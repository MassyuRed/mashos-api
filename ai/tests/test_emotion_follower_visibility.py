"""Server emotion visibility through the API and prior queued deliveries."""
from __future__ import annotations

import asyncio
from pathlib import Path
import sys
from unittest.mock import AsyncMock

import httpx
import pytest
from fastapi import FastAPI

AI_ROOT = Path(__file__).resolve().parents[1]
for path in (AI_ROOT, AI_ROOT / "services", AI_ROOT / "services" / "ai_inference"):
    sys.path.insert(0, str(path))

import api_emotion_log as log
import api_emotion_submit as submit
import api_follow as follow
import api_nexus as nexus
import astor_worker as worker
import emotion_follower_visibility as visibility
import startup_snapshot_store as startup
from api_relationship_compat import register_relationship_compat_routes
from middleware_api_contract import install_api_contract_middleware

AUTHOR = "20b0483e-5729-4f8e-94ad-f43ae9d6e638"
VIEWER = "6edd38b6-0f3f-40ee-9d44-42df9a0206b1"
SECOND_VIEWER = "460edee1-0636-44de-8abe-3fedc2bf3741"
HEAD = "2026-11-21T03:45:56+00:00"
FEED_ITEM = {
    "id": 9,
    "viewer_user_id": VIEWER,
    "owner_user_id": AUTHOR,
    "owner_name": "感情を入力した人",
    "items": [{"type": "喜び", "strength": "strong"}],
    "created_at": HEAD,
}


def test_feed_unread_and_nexus_compat_recheck_current_owner_choices(monkeypatch):
    monkeypatch.delenv("FOLLOWER_SHARING_ENABLED", raising=False)
    state = {"allowed": True, "unavailable": False}

    async def post_rpc(function, args, **_):
        assert function == "emotion_log_feed_for_viewer"
        assert args["p_viewer_user_id"] == VIEWER and args["p_limit"] in (1, 20)
        if state["unavailable"]:
            return httpx.Response(500, text="PRIVATE DATABASE DIAGNOSTIC")
        return httpx.Response(200, json=[FEED_ITEM] if state["allowed"] else [])

    monkeypatch.setattr(visibility, "sb_post_rpc", post_rpc)
    monkeypatch.setattr(log, "_resolve_user_id_from_token", AsyncMock(return_value=VIEWER))
    monkeypatch.setattr(follow, "_fetch_last_read_at", AsyncMock(return_value=None))
    monkeypatch.setattr(follow, "_fetch_latest_pending_request_head_and_count", AsyncMock(return_value=(None, 0)))
    app = FastAPI()
    install_api_contract_middleware(app)
    log.register_emotion_log_routes(app)
    nexus.register_nexus_routes(app)
    register_relationship_compat_routes(app)

    async def flow():
        headers = {"Authorization": "Bearer viewer"}
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app),
                                     base_url="https://test.invalid", headers=headers) as http:
            response = await http.get("/emotion-log/feed")
            assert response.status_code == 200 and response.json()["items"][0]["id"] == 9
            assert response.headers["cache-control"] == "private, no-store"
            assert (await http.get("/emotion-log/unread-status")).json()["feed_unread"]
            state["allowed"] = False
            assert (await http.get("/emotion-log/feed")).json()["items"] == []
            for alias in ("/nexus/emotion-log", "/friends/feed"):
                forwarded = await http.get(alias)
                assert forwarded.status_code == 200 and forwarded.json()["items"] == []
                assert forwarded.headers["cache-control"] == "private, no-store"
            assert (await http.get("/nexus")).headers["cache-control"] == "private, no-store"
            assert not (await http.get("/emotion-log/unread-status")).json()["feed_unread"]
            state["unavailable"] = True
            denied = await http.get("/emotion-log/feed")
            assert denied.status_code == 503 and "PRIVATE DATABASE DIAGNOSTIC" not in denied.text

    asyncio.run(flow())


def test_startup_replaces_stale_emotion_flags_without_mutating_cached_snapshot(monkeypatch):
    old_unread = {"feed_unread": True, "requests_unread": False}
    old_snapshot = {"sections": {"emotion_log_unread": old_unread, "friends_unread": old_unread},
                    "flags": {"has_any_emotion_log_unread": True, "has_any_friends_unread": True,
                              "has_popup_notice": True}}
    monkeypatch.setattr(startup, "STARTUP_SNAPSHOT_ENABLED", True)
    monkeypatch.setattr(startup, "get_or_compute", AsyncMock(return_value=old_snapshot))
    current = AsyncMock(return_value={"feed_unread": False, "feed_last_read_at": HEAD})
    monkeypatch.setattr(follow, "get_current_emotion_log_unread_for_user", current)

    actual = asyncio.run(startup.get_startup_snapshot(VIEWER))
    current.assert_awaited_once_with(VIEWER)
    assert actual["sections"]["emotion_log_unread"] == {
        "feed_unread": False, "requests_unread": False, "feed_last_read_at": HEAD}
    assert actual["sections"]["friends_unread"] == actual["sections"]["emotion_log_unread"]
    assert actual["flags"] == {"has_any_emotion_log_unread": False, "has_any_friends_unread": False,
                               "has_popup_notice": True}
    assert old_snapshot["flags"]["has_any_emotion_log_unread"] and old_unread["feed_unread"]


def test_submit_needs_sender_grant_as_well_as_receiver_opt_in(monkeypatch):
    monkeypatch.setattr(submit, "_fetch_follow_viewer_ids", AsyncMock(return_value=[VIEWER, SECOND_VIEWER]))
    not_permitted = AsyncMock(return_value=[VIEWER])
    monkeypatch.setattr(submit, "permitted_emotion_recipients", not_permitted)
    observed = []

    async def receiver_preferences(*, viewer_user_ids, owner_user_id, require_read):
        observed.append((viewer_user_ids, owner_user_id, require_read))
        return []

    monkeypatch.setattr(submit, "_filter_viewer_ids_by_emotion_notification_settings", receiver_preferences)
    insert = AsyncMock()
    push = AsyncMock()
    monkeypatch.setattr(submit, "_insert_emotion_log_feed_rows", insert)
    monkeypatch.setattr(submit, "_push_notify_followers_about_emotion", push)
    asyncio.run(submit._notify_follow_viewers_about_emotion(
        owner_user_id=AUTHOR, emotion_details=FEED_ITEM["items"], created_at=HEAD))
    not_permitted.assert_awaited_once_with(AUTHOR, [VIEWER, SECOND_VIEWER])
    assert observed == [([VIEWER], AUTHOR, True)]
    insert.assert_not_awaited()
    push.assert_not_awaited()


def test_queue_rechecks_actor_and_filters_tokens_before_push(monkeypatch):
    packet = {"body": "通知本文", "event_type": "emotion_log", "recipient_mode": "user_ids",
              "actor_user_id": AUTHOR, "recipient_user_ids": [VIEWER, SECOND_VIEWER]}
    monkeypatch.setattr(worker, "_fetch_push_tokens_for_users", AsyncMock(
        return_value={VIEWER: "revoked-token", SECOND_VIEWER: "permitted-token"}))
    permission = AsyncMock(return_value=[SECOND_VIEWER])
    monkeypatch.setattr(worker, "_filter_current_emotion_recipients", permission)
    sent = AsyncMock(return_value={"status": "sent"})
    monkeypatch.setattr(worker, "_send_fcm_push", sent)

    result = asyncio.run(worker._handle_send_fcm_push_v1(user_id=AUTHOR, payload=packet))
    assert result["status"] == "sent" and result["recipient_count"] == 1
    permission.assert_awaited_once_with(viewer_user_ids=[VIEWER, SECOND_VIEWER], owner_user_id=AUTHOR)
    assert sent.await_args.kwargs["tokens"] == ["permitted-token"]

    sent.reset_mock()
    skipped = asyncio.run(worker._handle_send_fcm_push_v1(user_id=VIEWER, payload=packet))
    assert skipped["status"] == "skipped_invalid_emotion_notification"
    sent.assert_not_awaited()

    permission.side_effect = RuntimeError("EmotionLog visibility unavailable")
    with pytest.raises(RuntimeError, match="visibility unavailable"):
        asyncio.run(worker._handle_send_fcm_push_v1(user_id=AUTHOR, payload=packet))
    sent.assert_not_awaited()


def test_recipient_rpc_must_only_return_the_checked_uuids(monkeypatch):
    monkeypatch.setattr(visibility, "sb_post_rpc", AsyncMock(return_value=httpx.Response(
        200, json=[VIEWER, SECOND_VIEWER])))
    with pytest.raises(RuntimeError, match="visibility unavailable"):
        asyncio.run(visibility.permitted_emotion_recipients(AUTHOR, [VIEWER]))
