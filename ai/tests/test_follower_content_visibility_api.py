"""Author sharing is independent per follower and enforced without the UI flag."""
import asyncio

import httpx
import pytest
from fastapi import FastAPI

import api_account_visibility as account
import api_emotion_submit
import api_follow_graph as follow
import api_nexus
import api_piece_runtime
from middleware_api_contract import install_api_contract_middleware
import piece_generated_access as generated
import piece_public_read_service as pieces
import piece_public_read_store as piece_store
import supabase_client

AUTHOR = "10000000-0000-4000-8000-000000000001"
FOLLOWER = "20000000-0000-4000-8000-000000000002"
OTHER = "30000000-0000-4000-8000-000000000003"
FOLLOWERS = "/follow/followers/content-visibility"
CHOICE = "/follow/followers/" + FOLLOWER + "/content-visibility"
LEGACY = "/account/visibility/me"
POST_ID = "reflection:old-legacy"
BODY = "限定された旧ピースの本文"
ROW = {
    "id": "old-legacy", "public_id": "old-legacy", "owner_user_id": AUTHOR,
    "source_type": "emotion_generated", "status": "published", "is_active": True,
    "question": "過去の問い", "answer": BODY, "published_at": "2026-11-21T01:00:00+00:00",
}


@pytest.fixture
def service(monkeypatch):
    state = {"linked": True, "choices": {}, "calls": [], "invalidated": [], "read_failure": False}
    accounts = {"author": AUTHOR, "follower": FOLLOWER, "other": OTHER}

    async def resolve(token):
        return accounts.get(token, None)

    def row_for(follower):
        return {"follower_user_id": follower, "can_view_pieces": True,
                "can_receive_emotion_notifications": True} | state["choices"]

    async def rpc(name, args, **kwargs):
        state["calls"].append((name, args))
        if name == "follow_author_visibility_list_v1":
            rows = [row_for(FOLLOWER)] if state["linked"] and args["p_author_user_id"] == AUTHOR else []
            return httpx.Response(200, json=rows)
        if name == "follow_author_visibility_patch_v1":
            if not state["linked"] or (args["p_author_user_id"], args["p_follower_user_id"]) != (AUTHOR, FOLLOWER):
                return httpx.Response(400, json={"code": "P0001", "message": "FOLLOW_RELATION_NOT_FOUND"})
            for key in ("can_view_pieces", "can_receive_emotion_notifications"):
                if args["p_" + key] is not None:
                    state["choices"][key] = args["p_" + key]
            return httpx.Response(200, json=row_for(FOLLOWER))
        if name == "follow_piece_visible_owner_ids_v1":
            if state["read_failure"]:
                return httpx.Response(500, json={"message": "PRIVATE DATABASE DIAGNOSTIC"})
            valid = state["linked"] and args["p_viewer_user_id"] == FOLLOWER and row_for(FOLLOWER)["can_view_pieces"]
            return httpx.Response(200, json=[AUTHOR] if valid and AUTHOR in args["p_owner_user_ids"] else [])
        raise AssertionError(name)

    async def legacy_follows(path, *, params):
        assert path == "/rest/v1/myprofile_links"
        return [{"owner_user_id": AUTHOR}] if state["linked"] and params["viewer_user_id"] == f"eq.{FOLLOWER}" else []

    async def old_rows(owner_id, **kwargs):
        return [ROW] if owner_id == AUTHOR else []

    async def old_item(iid):
        return ROW if iid == POST_ID else None

    async def profile_rows(ids):
        return {AUTHOR: {"display_name": "ユーザー", "friend_code": "HIDDEN_LEGACY_CODE"}}

    async def hidden_codes(path, **kwargs):
        assert path == "/rest/v1/account_visibility_settings"
        return httpx.Response(200, json=[{"user_id": AUTHOR, "is_friend_code_public": False}])

    async def no_metrics(*args, **kwargs):
        return {}

    async def no_interaction(*args, **kwargs):
        return set()

    async def invalidate(ids):
        state["invalidated"].extend(ids)

    async def read_account_settings(uid):
        return {"user_id": uid, "is_private_account": True, "is_friend_code_public": False}

    async def no_global_write(*args, **kwargs):
        raise AssertionError("retired account settings reached stored data")

    state["get_row"] = row_for
    for module in (follow, api_nexus, api_piece_runtime, account):
        monkeypatch.setattr(module, "_resolve_user_id_from_token", resolve)
    monkeypatch.setattr(supabase_client, "sb_post_rpc", rpc)
    monkeypatch.setattr(supabase_client, "sb_get", hidden_codes)
    monkeypatch.setattr(piece_store, "sb_get_json", legacy_follows)
    monkeypatch.setattr(pieces, "fetch_active_emotion_generated_reflections_for_owner", old_rows)
    monkeypatch.setattr(generated, "fetch_emotion_generated_row_by_instance_id", old_item)
    monkeypatch.setattr(pieces, "fetch_profiles_by_ids", profile_rows)
    monkeypatch.setattr(pieces, "get_public_generated_reflection_text", lambda row: row["answer"])
    monkeypatch.setattr(generated, "get_public_generated_reflection_text", lambda row: row["answer"])
    monkeypatch.setattr(pieces, "fetch_instance_metrics", no_metrics)
    monkeypatch.setattr(pieces, "fetch_reads", no_interaction)
    monkeypatch.setattr(pieces, "fetch_resonated_instances", no_interaction)
    monkeypatch.setattr(api_emotion_submit, "_invalidate_emotion_log_receiver_caches", invalidate)
    monkeypatch.setattr(account, "_get_or_create_settings", read_account_settings)
    monkeypatch.setattr(account, "_sb_patch", no_global_write)

    app = FastAPI()
    install_api_contract_middleware(app)
    follow.register_follow_graph_routes(app)
    account.register_account_visibility_routes(app)
    api_nexus.register_nexus_routes(app)
    api_piece_runtime.register_piece_runtime_routes(app)

    def send(method, path, *, token="author", **kwargs):
        async def request():
            headers = {"Authorization": f"Bearer {token}"} if token is not None else {}
            async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app),
                                         base_url="http://follower-settings-test.invalid") as client:
                return await client.request(method, path, headers=headers, **kwargs)
        return asyncio.run(request())

    return send, state


def test_author_controls_which_current_follower_receives_each_kind(service, monkeypatch):
    send, state = service
    monkeypatch.setenv("FOLLOWER_SHARING_ENABLED", "true")
    first = send("GET", FOLLOWERS)
    assert first.status_code == 200 and first.json() == {"items": [state["get_row"](FOLLOWER)]}
    assert first.headers["cache-control"] == "private, no-store"
    assert send("GET", FOLLOWERS, token=None).status_code == 401
    assert send("GET", FOLLOWERS, token="other").json() == {"items": []}
    assert send("PATCH", CHOICE, token="other", json={"can_view_pieces": False}).status_code == 404
    assert state["choices"] == {}

    piece = send("PATCH", CHOICE, json={"can_view_pieces": False})
    assert piece.status_code == 200 and piece.json() == {
        "follower_user_id": FOLLOWER, "can_view_pieces": False, "can_receive_emotion_notifications": True}
    assert state["calls"][-1] == ("follow_author_visibility_patch_v1", {
        "p_author_user_id": AUTHOR, "p_follower_user_id": FOLLOWER,
        "p_can_view_pieces": False, "p_can_receive_emotion_notifications": None})
    assert state["invalidated"] == []
    emotion = send("PATCH", CHOICE, json={"can_receive_emotion_notifications": False})
    assert emotion.json() == {
        "follower_user_id": FOLLOWER, "can_view_pieces": False, "can_receive_emotion_notifications": False}
    assert state["invalidated"] == [FOLLOWER]

    state["linked"] = False
    assert send("GET", FOLLOWERS).json() == {"items": []}
    assert send("PATCH", CHOICE, json={"can_view_pieces": True}).status_code == 404
    state["linked"] = True
    assert send("GET", FOLLOWERS).json() == {"items": [emotion.json()]}


@pytest.mark.parametrize("body", [
    {}, {"can_view_pieces": "true"}, {"can_view_pieces": None}, {"can_view_pieces": 0},
    {"owner_user_id": OTHER, "can_view_pieces": True}, [],
])
def test_malformed_changes_never_reach_storage(service, monkeypatch, body):
    send, state = service
    monkeypatch.setenv("FOLLOWER_SHARING_ENABLED", "true")
    assert send("PATCH", CHOICE, json=body).status_code == 400
    assert state["calls"] == []


def test_existing_privacy_settings_are_readable_but_not_mutable_after_cutover(service, monkeypatch):
    send, _ = service
    monkeypatch.setenv("FOLLOWER_SHARING_ENABLED", "true")
    old = send("GET", LEGACY).json()
    assert old["is_private_account"] is True and old["is_friend_code_public"] is False
    result = send("PATCH", LEGACY, json={"is_private_account": False, "is_share_code_public": True})
    assert result.status_code == 410 and result.json()["code"] == "ACCOUNT_VISIBILITY_RETIRED"
    assert send("GET", LEGACY).json() == old


def test_existing_piece_content_and_unread_follow_live_permission_even_with_management_off(service, monkeypatch):
    send, state = service
    monkeypatch.delenv("FOLLOWER_SHARING_ENABLED", raising=False)
    assert send("GET", FOLLOWERS).status_code == 503
    feed = send("GET", "/nexus/pieces", token="follower")
    assert feed.status_code == 200 and feed.json()["items"][0]["body"] == BODY
    assert "HIDDEN_LEGACY_CODE" not in feed.text
    assert feed.headers["cache-control"] == "private, no-store"
    state["choices"]["can_view_pieces"] = False
    denied = send("GET", "/nexus/pieces", token="follower")
    assert denied.status_code == 200 and denied.json()["items"] == []
    detail = send("GET", "/nexus/pieces/" + POST_ID, token="follower")
    assert detail.status_code == 403 and BODY not in detail.text
    resonance = send("POST", "/piece/resonances/submit", token="follower",
                     json={"q_instance_id": POST_ID, "strength": "medium"})
    assert resonance.status_code == 403 and BODY not in resonance.text
    body = send("GET", "/nexus/pieces/unread-status", token="follower").json()
    assert body["following_has_unread"] is False
    own = send("GET", "/nexus/pieces?following_only=false", token="author")
    assert own.status_code == 200 and own.json()["items"][0]["body"] == BODY
    state["read_failure"] = True
    failure = send("GET", "/nexus/pieces", token="follower")
    assert failure.status_code == 503
    assert BODY not in failure.text and "PRIVATE DATABASE DIAGNOSTIC" not in failure.text
