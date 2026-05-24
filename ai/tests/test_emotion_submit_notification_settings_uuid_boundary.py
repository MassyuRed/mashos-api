from __future__ import annotations

from types import SimpleNamespace

import pytest

import api_emotion_submit as api

OWNER_UUID = "00000000-0000-4000-8000-000000000001"
VIEWER_ONE_UUID = "00000000-0000-4000-8000-000000000101"
VIEWER_TWO_UUID = "00000000-0000-4000-8000-000000000102"
GLOBAL_SENTINELS = (
    api.EMOTION_NOTIFICATION_GLOBAL_OWNER_ID,
    api.FRIEND_NOTIFICATION_GLOBAL_OWNER_ID,
)


def _configure_supabase(monkeypatch) -> None:
    monkeypatch.setattr(api, "SUPABASE_URL", "https://example.supabase.co")
    monkeypatch.setattr(api, "SUPABASE_SERVICE_ROLE_KEY", "service-role-key")
    monkeypatch.setattr(api, "EMOTION_NOTIFICATION_SETTINGS_READ_TABLE", "emotion_notification_settings")


def test_emotion_notification_owner_filter_uses_only_uuid_owner() -> None:
    assert api._emotion_notification_owner_filter_ids(OWNER_UUID) == [OWNER_UUID]
    assert api._emotion_notification_owner_filter_ids(api.EMOTION_NOTIFICATION_GLOBAL_OWNER_ID) == []
    assert api._emotion_notification_owner_filter_ids("not-a-uuid") == []


@pytest.mark.asyncio
async def test_notification_settings_filter_does_not_put_global_sentinel_in_uuid_owner_filter(monkeypatch) -> None:
    _configure_supabase(monkeypatch)
    calls: list[dict] = []

    async def fake_sb_get(path, *, params, timeout):
        calls.append({"path": path, "params": dict(params), "timeout": timeout})
        return SimpleNamespace(status_code=200, text="[]", json=lambda: [])

    monkeypatch.setattr(api, "_sb_get_shared", fake_sb_get)

    result = await api._filter_viewer_ids_by_emotion_notification_settings(
        viewer_user_ids=[VIEWER_ONE_UUID, VIEWER_TWO_UUID],
        owner_user_id=OWNER_UUID,
    )

    assert result == [VIEWER_ONE_UUID, VIEWER_TWO_UUID]
    assert len(calls) == 1
    params = calls[0]["params"]
    assert params["owner_user_id"] == f'in.("{OWNER_UUID}")'
    assert VIEWER_ONE_UUID in params["viewer_user_id"]
    assert VIEWER_TWO_UUID in params["viewer_user_id"]
    assert params["is_enabled"] == "eq.false"
    for sentinel in GLOBAL_SENTINELS:
        assert sentinel not in params["owner_user_id"]


@pytest.mark.asyncio
async def test_notification_settings_filter_excludes_disabled_viewer_from_owner_uuid_query(monkeypatch) -> None:
    _configure_supabase(monkeypatch)

    async def fake_sb_get(path, *, params, timeout):
        assert path == "/rest/v1/emotion_notification_settings"
        assert params["owner_user_id"] == f'in.("{OWNER_UUID}")'
        return SimpleNamespace(
            status_code=200,
            text="[]",
            json=lambda: [{"viewer_user_id": VIEWER_TWO_UUID}],
        )

    monkeypatch.setattr(api, "_sb_get_shared", fake_sb_get)

    result = await api._filter_viewer_ids_by_emotion_notification_settings(
        viewer_user_ids=[VIEWER_ONE_UUID, VIEWER_TWO_UUID],
        owner_user_id=OWNER_UUID,
    )

    assert result == [VIEWER_ONE_UUID]


@pytest.mark.asyncio
async def test_notification_settings_filter_skips_query_when_owner_id_is_not_uuid_safe(monkeypatch) -> None:
    _configure_supabase(monkeypatch)
    called = False

    async def fake_sb_get(*_args, **_kwargs):
        nonlocal called
        called = True
        raise AssertionError("uuid-unsafe owner must not be sent to Supabase notification filter")

    monkeypatch.setattr(api, "_sb_get_shared", fake_sb_get)

    result = await api._filter_viewer_ids_by_emotion_notification_settings(
        viewer_user_ids=[VIEWER_ONE_UUID, VIEWER_TWO_UUID],
        owner_user_id=api.EMOTION_NOTIFICATION_GLOBAL_OWNER_ID,
    )

    assert result == [VIEWER_ONE_UUID, VIEWER_TWO_UUID]
    assert called is False
