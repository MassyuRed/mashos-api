from __future__ import annotations


def test_notices_current_contract_headers_and_shape(client, monkeypatch):
    import api_notice as notice_module

    async def fake_require_user_id(_authorization):
        return "user-123"

    async def fake_fetch_current_notice_bundle(_user_id: str, _client_meta):
        return {
            "feature_enabled": True,
            "unread_count": 2,
            "has_unread": True,
            "badge": {
                "show": True,
                "count": 2,
            },
            "popup_notice": {
                "notice_id": "notice-1",
                "notice_key": "update_2026_03_19_ios",
                "version": 1,
                "title": "アップデート版を配布しました",
                "body": "不具合修正を含む最新版を配布しました。",
                "body_format": "plain_text",
                "category": "update",
                "priority": "high",
                "published_at": "2026-03-19T09:00:00Z",
                "is_read": False,
                "read_at": None,
                "popup_seen_at": None,
                "cta": {
                    "kind": "none",
                    "label": None,
                    "route": None,
                    "params": {},
                    "url": None,
                },
            },
        }

    monkeypatch.setattr(notice_module, "_require_user_id", fake_require_user_id)
    monkeypatch.setattr(notice_module.store, "fetch_current_notice_bundle", fake_fetch_current_notice_bundle)

    response = client.get(
        "/notices/current",
        headers={
            "Authorization": "Bearer test-token",
            "X-App-Version": "1.2.3",
            "X-App-Build": "123",
            "X-Platform": "ios",
        },
    )

    assert response.status_code == 200, response.text
    assert response.headers["X-Cocolon-Contract-Id"] == "notice.current.v1"
    body = response.json()
    assert body["feature_enabled"] is True
    assert body["unread_count"] == 2
    assert body["has_unread"] is True
    assert body["badge"]["show"] is True
    assert body["popup_notice"]["notice_id"] == "notice-1"
    assert body["popup_notice"]["cta"]["kind"] == "none"



def test_notices_history_contract_shape(client, monkeypatch):
    import api_notice as notice_module

    async def fake_require_user_id(_authorization):
        return "user-123"

    async def fake_list_notice_history(_user_id: str, _client_meta, *, limit: int, offset: int):
        assert limit == 30
        assert offset == 0
        return {
            "feature_enabled": True,
            "items": [
                {
                    "notice_id": "notice-1",
                    "notice_key": "update_2026_03_19_ios",
                    "version": 1,
                    "title": "アップデート版を配布しました",
                    "body": "不具合修正を含む最新版を配布しました。",
                    "body_format": "plain_text",
                    "category": "update",
                    "priority": "high",
                    "published_at": "2026-03-19T09:00:00Z",
                    "is_read": False,
                    "read_at": None,
                    "popup_seen_at": "2026-03-19T10:00:00Z",
                    "cta": {
                        "kind": "url",
                        "label": "App Storeを開く",
                        "route": None,
                        "params": {},
                        "url": "https://example.com/app",
                    },
                }
            ],
            "limit": 30,
            "offset": 0,
            "has_more": False,
            "next_offset": None,
            "unread_count": 1,
        }

    monkeypatch.setattr(notice_module, "_require_user_id", fake_require_user_id)
    monkeypatch.setattr(notice_module.store, "list_notice_history", fake_list_notice_history)

    response = client.get(
        "/notices/history",
        headers={
            "Authorization": "Bearer test-token",
            "X-App-Version": "1.2.3",
            "X-App-Build": "123",
            "X-Platform": "ios",
        },
    )

    assert response.status_code == 200, response.text
    assert response.headers["X-Cocolon-Contract-Id"] == "notice.history.list.v1"
    body = response.json()
    assert body["feature_enabled"] is True
    assert body["unread_count"] == 1
    assert len(body["items"]) == 1
    assert body["items"][0]["title"] == "アップデート版を配布しました"
    assert body["items"][0]["cta"]["kind"] == "url"



def test_notices_read_is_idempotent(client, monkeypatch):
    import api_notice as notice_module

    state = {"calls": 0}

    async def fake_require_user_id(_authorization):
        return "user-123"

    async def fake_mark_notices_read(_user_id: str, notice_ids):
        assert notice_ids == ["notice-1"]
        state["calls"] += 1
        return 1 if state["calls"] == 1 else 0

    async def fake_fetch_current_notice_bundle(_user_id: str, _client_meta):
        return {
            "feature_enabled": True,
            "unread_count": 0,
            "has_unread": False,
            "badge": {"show": False, "count": 0},
            "popup_notice": None,
        }

    monkeypatch.setattr(notice_module, "_require_user_id", fake_require_user_id)
    monkeypatch.setattr(notice_module.store, "mark_notices_read", fake_mark_notices_read)
    monkeypatch.setattr(notice_module.store, "fetch_current_notice_bundle", fake_fetch_current_notice_bundle)

    headers = {
        "Authorization": "Bearer test-token",
        "X-App-Version": "1.2.3",
        "X-App-Build": "123",
        "X-Platform": "ios",
    }
    payload = {"notice_ids": ["notice-1"]}

    response1 = client.post("/notices/read", headers=headers, json=payload)
    response2 = client.post("/notices/read", headers=headers, json=payload)

    assert response1.status_code == 200, response1.text
    assert response2.status_code == 200, response2.text
    assert response1.headers["X-Cocolon-Contract-Id"] == "notice.read.mark.v1"
    assert response2.headers["X-Cocolon-Contract-Id"] == "notice.read.mark.v1"
    assert response1.json()["updated_count"] == 1
    assert response2.json()["updated_count"] == 0
    assert response2.json()["unread_count"] == 0



def test_notices_popup_seen_is_idempotent(client, monkeypatch):
    import api_notice as notice_module

    async def fake_require_user_id(_authorization):
        return "user-123"

    async def fake_mark_notice_popup_seen(_user_id: str, notice_id: str):
        assert notice_id == "notice-1"
        return True

    monkeypatch.setattr(notice_module, "_require_user_id", fake_require_user_id)
    monkeypatch.setattr(notice_module.store, "mark_notice_popup_seen", fake_mark_notice_popup_seen)

    headers = {"Authorization": "Bearer test-token"}
    payload = {"notice_id": "notice-1"}

    response1 = client.post("/notices/popup-seen", headers=headers, json=payload)
    response2 = client.post("/notices/popup-seen", headers=headers, json=payload)

    assert response1.status_code == 200, response1.text
    assert response2.status_code == 200, response2.text
    assert response1.headers["X-Cocolon-Contract-Id"] == "notice.popup_seen.mark.v1"
    assert response2.headers["X-Cocolon-Contract-Id"] == "notice.popup_seen.mark.v1"
    assert response1.json()["popup_seen"] is True
    assert response2.json()["popup_seen"] is True
