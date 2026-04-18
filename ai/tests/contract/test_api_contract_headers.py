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
