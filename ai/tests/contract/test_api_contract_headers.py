from __future__ import annotations

from api_contract_registry import API_CONTRACT_POLICY_VERSION


def test_app_bootstrap_returns_contract_headers(client):
    response = client.get(
        "/app/bootstrap",
        headers={
            "X-App-Version": "1.2.3",
            "X-App-Build": "123",
            "X-Platform": "ios",
        },
    )

    assert response.status_code == 200
    assert response.headers["X-Cocolon-Api-Policy-Version"] == API_CONTRACT_POLICY_VERSION
    assert response.headers["X-Cocolon-Contract-Id"] == "app.bootstrap.v1"
    assert response.headers["X-Cocolon-Deprecated"] == "false"
    assert response.headers["X-Cocolon-Request-Id"]

    body = response.json()
    assert body["client_meta"]["app_version"] == "1.2.3"
    assert body["client_meta"]["app_build"] == "123"
    assert body["client_meta"]["platform"] == "ios"



def test_legacy_emotion_submit_accepts_memo_without_category(client, monkeypatch):
    import api_emotion_submit as emotion_submit_module
    import emotion_submit_service as emotion_submit_service_module

    inserted_payload = {}
    background_payload = {}

    async def fake_resolve_user_id_from_token(_access_token: str) -> str:
        return "user-123"

    async def fake_persist_emotion_submission(**kwargs):
        payload = dict(kwargs)
        if payload.get("category") is None:
            payload["category"] = []
        inserted_payload.update(payload)
        background_payload.update({"memo": kwargs.get("memo")})
        return {
            "inserted": {"id": "emo-1"},
            "created_at": kwargs.get("created_at") or "2026-04-18T00:00:00Z",
            "input_feedback_comment": "compat comment",
            "input_feedback_meta": None,
        }

    monkeypatch.setattr(emotion_submit_module, "_resolve_user_id_from_token", fake_resolve_user_id_from_token)
    monkeypatch.setattr(emotion_submit_service_module, "persist_emotion_submission", fake_persist_emotion_submission)

    response = client.post(
        "/emotion/submit",
        headers={
            "Authorization": "Bearer test-token",
            "X-App-Version": "1.0.0",
            "X-App-Build": "100",
            "X-Platform": "android",
        },
        json={
            "emotions": ["Joy"],
            "memo": "old build memo payload",
        },
    )

    assert response.status_code == 200, response.text
    assert response.json()["status"] == "ok"
    assert inserted_payload["category"] == []
    assert background_payload["memo"] == "old build memo payload"
    assert response.headers["X-Cocolon-Contract-Id"] == "emotion.submit.v1"



def test_account_profile_me_keeps_tutorial_flags(client, monkeypatch):
    import api_account_lifecycle as account_lifecycle_module

    async def fake_require_user_id(_authorization):
        return "user-456"

    async def fake_fetch_profile_me(_user_id: str):
        return {
            "display_name": "Mash",
            "friend_code": "FRIEND-01",
            "myprofile_code": "MYPROFILE-01",
            "push_enabled": False,
            "tutorial_completed": True,
            "tutorial_skipped": False,
        }

    monkeypatch.setattr(account_lifecycle_module, "_require_user_id", fake_require_user_id)
    monkeypatch.setattr(account_lifecycle_module, "_fetch_profile_me", fake_fetch_profile_me)

    response = client.get("/account/profile/me", headers={"Authorization": "Bearer test-token"})

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["tutorial_completed"] is True
    assert body["tutorial_skipped"] is False
    assert body["push_enabled"] is False
    assert response.headers["X-Cocolon-Contract-Id"] == "account.profile.me.read.v1"


def test_account_display_name_availability_returns_contract_headers(client, monkeypatch):
    import api_account_lifecycle as account_lifecycle_module

    async def fake_require_user_id(_authorization):
        return "user-456"

    async def fake_is_display_name_available(candidate: str, *, exclude_user_id=None):
        assert candidate == "Mash"
        assert exclude_user_id == "user-456"
        return True

    monkeypatch.setattr(account_lifecycle_module, "_require_user_id", fake_require_user_id)
    monkeypatch.setattr(account_lifecycle_module, "_is_display_name_available", fake_is_display_name_available)

    response = client.get(
        "/account/display-name/availability?candidate=Mash",
        headers={"Authorization": "Bearer test-token"},
    )

    assert response.status_code == 200, response.text
    assert response.headers["X-Cocolon-Api-Policy-Version"] == API_CONTRACT_POLICY_VERSION
    assert response.headers["X-Cocolon-Contract-Id"] == "account.display_name.availability.v1"
    assert response.headers["X-Cocolon-Deprecated"] == "false"
    assert response.headers["X-Cocolon-Request-Id"]
    assert response.json()["available"] is True


def test_global_summary_returns_contract_headers(client, monkeypatch):
    import api_global_summary as global_summary_module

    monkeypatch.setattr(global_summary_module, "_today_jst_date_iso", lambda: "2026-03-12")

    async def fake_fetch_latest_ready_global_summary(activity_date: str, *, timezone_name: str):
        return {
            "activity_date": activity_date,
            "timezone": timezone_name,
            "published_at": "2026-03-12T00:00:00Z",
            "payload": {
                "version": "global_summary.v1",
                "activity_date": activity_date,
                "timezone": timezone_name,
                "generated_at": "2026-03-12T00:00:00Z",
                "totals": {
                    "emotion_users": 7,
                    "reflection_views": 11,
                    "echo_count": 13,
                    "discovery_count": 17,
                },
            },
        }

    async def fake_generate_global_summary_payload(*args, **kwargs):
        raise AssertionError("legacy fallback should not run when READY artifact exists")

    monkeypatch.setattr(global_summary_module, "fetch_latest_ready_global_summary", fake_fetch_latest_ready_global_summary)
    monkeypatch.setattr(global_summary_module, "generate_global_summary_payload", fake_generate_global_summary_payload)

    response = client.get("/global_summary?date=2026-03-11&tz=%2B09:00")

    assert response.status_code == 200, response.text
    assert response.headers["X-Cocolon-Api-Policy-Version"] == API_CONTRACT_POLICY_VERSION
    assert response.headers["X-Cocolon-Contract-Id"] == "global_summary.read.v1"
    assert response.headers["X-Cocolon-Deprecated"] == "false"
    assert response.headers["X-Cocolon-Request-Id"]
    body = response.json()
    assert body["date"] == "2026-03-11"
    assert body["tz"] == "+09:00"
    assert body["emotion_users"] == 7
    assert body["reflection_views"] == 11
    assert body["echo_count"] == 13
    assert body["discovery_count"] == 17



class _FakeResponse:
    def __init__(self, status_code, payload):
        self.status_code = status_code
        self._payload = payload
        self.text = ""

    def json(self):
        return self._payload


def test_myprofile_latest_status_returns_contract_headers(client, monkeypatch):
    import api_myprofile as myprofile_module

    async def fake_resolve_user_id_from_token(_access_token: str) -> str:
        return "user-123"

    async def fake_sb_get(path: str, *, params=None):
        assert path == "/rest/v1/myprofile_reports"
        return _FakeResponse(
            200,
            [
                {
                    "generated_at": "2026-03-20T00:00:00Z",
                    "content_text": "現在の自己構造です。",
                    "title": "自己構造レポート（最新版）",
                    "period_start": "2026-02-21T00:00:00Z",
                    "period_end": "2026-03-20T00:00:00Z",
                    "content_json": {
                        "version": "myprofile.report.v4",
                        "report_mode": "standard",
                        "visibility": {"has_visible_content": True},
                        "history": {
                            "history_fingerprint": "self-structure-version-key-1",
                            "skip_reason": None,
                        },
                    },
                }
            ],
        )

    monkeypatch.setattr(myprofile_module, "_resolve_user_id_from_token", fake_resolve_user_id_from_token)
    monkeypatch.setattr(myprofile_module, "_sb_get", fake_sb_get)

    response = client.get("/myprofile/latest/status", headers={"Authorization": "Bearer test-token"})

    assert response.status_code == 200, response.text
    assert response.headers["X-Cocolon-Api-Policy-Version"] == API_CONTRACT_POLICY_VERSION
    assert response.headers["X-Cocolon-Contract-Id"] == "myprofile.latest.status.v1"
    assert response.headers["X-Cocolon-Deprecated"] == "false"
    assert response.headers["X-Cocolon-Request-Id"]



def test_app_startup_returns_contract_headers_and_fixed_boundary(client, monkeypatch):
    import api_app_bootstrap as app_bootstrap_module
    import startup_snapshot_store as startup_snapshot_store_module

    async def fake_require_user_id(_authorization):
        return "user-123"

    async def fake_get_startup_snapshot(_user_id: str, *, client_meta=None, timezone_name=None, force_refresh=False):
        assert _user_id == "user-123"
        assert bool(force_refresh) is True
        return {
            "schema_version": "startup_snapshot.v1",
            "user_id": "user-123",
            "generated_at": "2026-04-19T00:00:00Z",
            "source_versions": {
                "schema": "startup_snapshot.v1",
                "emotion_log_unread": "emotion_log.unread.v1",
                "friends_unread": "friends.unread.v1",
                "myweb_unread": "report_reads.myweb_unread.v1",
                "notices_current": "notice.current.v1",
                "today_question_light": "today_question.current.light.v1",
            },
            "flags": {
                "has_any_emotion_log_unread": True,
                "has_any_friends_unread": True,
                "has_any_myweb_unread": False,
                "has_popup_notice": True,
                "today_question_answered": False,
            },
            "sections": {
                "emotion_log_unread": {
                    "status": "ok",
                    "feed_unread": True,
                    "requests_unread": False,
                    "incoming_pending_count": 1,
                    "feed_last_read_at": None,
                    "requests_last_read_at": None,
                },
                "friends_unread": {
                    "status": "ok",
                    "feed_unread": True,
                    "requests_unread": False,
                    "incoming_pending_count": 1,
                    "feed_last_read_at": None,
                    "requests_last_read_at": None,
                },
                "myweb_unread": {
                    "status": "ok",
                    "viewer_tier": "free",
                    "ids_by_type": {"daily": [], "weekly": [], "monthly": [], "selfStructure": []},
                    "read_ids": [],
                    "unread_by_type": {"daily": False, "weekly": False, "monthly": False, "selfStructure": False},
                },
                "notices_current": {
                    "feature_enabled": True,
                    "unread_count": 1,
                    "has_unread": True,
                    "badge": {"show": True, "count": 1},
                    "popup_notice": {"notice_id": "notice-1", "title": "hello", "body": "notice body"},
                },
                "today_question_light": {
                    "service_day_key": "2026-04-19",
                    "answer_status": "unanswered",
                    "answer_summary": None,
                    "question": {
                        "question_id": "q-1",
                        "question_key": "qkey",
                        "version": 1,
                        "text": "今日の問い",
                        "choice_count": 3,
                        "free_text_enabled": True,
                    },
                    "delivery": {},
                    "progress": {},
                },
                "today_question": {
                    "service_day_key": "2026-04-19",
                    "answer_status": "unanswered",
                    "answer_summary": None,
                    "question": {
                        "question_id": "q-1",
                        "question_key": "qkey",
                        "version": 1,
                        "text": "今日の問い",
                        "choice_count": 3,
                        "free_text_enabled": True,
                    },
                    "delivery": {},
                    "progress": {},
                },
            },
            "errors": {},
            "timezone_name": timezone_name,
        }

    monkeypatch.setattr(app_bootstrap_module, "_require_user_id", fake_require_user_id)
    monkeypatch.setattr(startup_snapshot_store_module, "get_startup_snapshot", fake_get_startup_snapshot)

    response = client.get(
        "/app/startup?force_refresh=true&timezone_name=Asia%2FTokyo",
        headers={
            "Authorization": "Bearer test-token",
            "X-App-Version": "1.2.3",
            "X-App-Build": "123",
            "X-Platform": "ios",
        },
    )

    assert response.status_code == 200, response.text
    assert response.headers["X-Cocolon-Api-Policy-Version"] == API_CONTRACT_POLICY_VERSION
    assert response.headers["X-Cocolon-Contract-Id"] == "app.startup.v1"
    body = response.json()
    assert body["client_meta"]["app_version"] == "1.2.3"
    assert body["startup"]["sections"].get("today_question_light") is not None
    assert "input_summary" not in body["startup"]["sections"]
    assert "global_summary" not in body["startup"]["sections"]



def test_home_state_returns_contract_headers_and_shape(client, monkeypatch):
    import api_home_state as home_state_module

    async def fake_resolve_authenticated_user_id(*, authorization=None, legacy_user_id=None):
        return "user-123"

    async def fake_get_home_state(_user_id: str, *, client_meta=None, timezone_name=None, force_refresh=False):
        assert _user_id == "user-123"
        return {
            "status": "ok",
            "user_id": "user-123",
            "generated_at": "2026-04-19T00:00:00Z",
            "service_day_key": "2026-04-19",
            "source_versions": {"schema": "home_state.v1"},
            "popup_candidates": [
                {"kind": "notice", "notice_id": "notice-1", "service_day_key": None, "question_id": None}
            ],
            "notice_popup_notice_id": "notice-1",
            "sections": {
                "input_summary": {
                    "status": "ok",
                    "user_id": "user-123",
                    "today_count": 1,
                    "week_count": 2,
                    "month_count": 3,
                    "streak_days": 4,
                    "last_input_at": "2026-04-19T00:00:00Z",
                },
                "global_summary": {
                    "date": "2026-04-19",
                    "tz": "+09:00",
                    "emotion_users": 5,
                    "reflection_views": 6,
                    "echo_count": 7,
                    "discovery_count": 8,
                    "updated_at": "2026-04-19T00:00:00Z",
                },
                "notices_current": {
                    "feature_enabled": True,
                    "unread_count": 1,
                    "has_unread": True,
                    "badge": {"show": True, "count": 1},
                    "popup_notice": {"notice_id": "notice-1", "title": "hello", "body": "notice body"},
                },
                "today_question_current": {
                    "service_day_key": "2026-04-19",
                    "question": {
                        "question_id": "q-1",
                        "question_key": "qkey",
                        "version": 1,
                        "text": "今日の問い",
                        "choice_count": 3,
                        "choices": [
                            {"choice_id": "c-1", "choice_key": "one", "label": "はい"}
                        ],
                        "free_text_enabled": True,
                    },
                    "answer_status": "unanswered",
                    "answer_summary": None,
                    "delivery": {},
                    "progress": {},
                },
                "emotion_reflection_quota": {
                    "status": "ok",
                    "subscription_tier": "free",
                    "month_key": "2026-04",
                    "publish_limit": 0,
                    "published_count": 0,
                    "remaining_count": 0,
                    "can_publish": False,
                },
            },
            "errors": {},
        }

    monkeypatch.setattr(home_state_module, "resolve_authenticated_user_id", fake_resolve_authenticated_user_id)
    monkeypatch.setattr(home_state_module, "get_home_state", fake_get_home_state)

    response = client.get(
        "/home/state?timezone_name=Asia%2FTokyo&force_refresh=true",
        headers={
            "Authorization": "Bearer test-token",
            "X-App-Version": "1.2.3",
            "X-App-Build": "123",
            "X-Platform": "ios",
        },
    )

    assert response.status_code == 200, response.text
    assert response.headers["X-Cocolon-Api-Policy-Version"] == API_CONTRACT_POLICY_VERSION
    assert response.headers["X-Cocolon-Contract-Id"] == "home.state.v1"
    body = response.json()
    assert body["sections"]["input_summary"]["today_count"] == 1
    assert body["sections"]["emotion_reflection_quota"]["subscription_tier"] == "free"



def test_emotion_reflection_cancel_returns_contract_headers(client, monkeypatch):
    import api_emotion_reflection as reflection_module

    async def fake_resolve_authenticated_user_id(*, authorization=None, legacy_user_id=None):
        return "user-123"

    async def fake_fetch_preview_draft(*, preview_id: str, user_id: str):
        return {"id": preview_id, "user_id": user_id}

    async def fake_cancel_preview_draft(*, preview_id: str, user_id: str):
        return {"status": "cancelled", "preview_id": preview_id, "user_id": user_id}

    monkeypatch.setattr(reflection_module, "resolve_authenticated_user_id", fake_resolve_authenticated_user_id)
    monkeypatch.setattr(reflection_module, "fetch_preview_draft", fake_fetch_preview_draft)
    monkeypatch.setattr(reflection_module, "cancel_preview_draft", fake_cancel_preview_draft)

    response = client.post(
        "/emotion/reflection/cancel",
        headers={"Authorization": "Bearer test-token"},
        json={"preview_id": "preview-1"},
    )

    assert response.status_code == 200, response.text
    assert response.headers["X-Cocolon-Contract-Id"] == "emotion.reflection.cancel.v1"
    assert response.json()["result"] == "cancelled"
