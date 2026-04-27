from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, Optional


FIXTURE_DIR = Path(__file__).resolve().parent / "fixtures"


class _FakeResponse:
    def __init__(self, status_code: int, payload: Any):
        self.status_code = status_code
        self._payload = payload
        self.text = ""

    def json(self) -> Any:
        return self._payload


def _load_fixture(name: str) -> Any:
    return json.loads((FIXTURE_DIR / name).read_text(encoding="utf-8"))


def _assert_shape_subset(expected: Any, actual: Any, path: str = "$") -> None:
    if expected == "<any>":
        return
    if expected == "<str>":
        assert isinstance(actual, str), f"{path}: expected str, got {type(actual).__name__}"
        return
    if expected == "<int>":
        assert isinstance(actual, int) and not isinstance(actual, bool), f"{path}: expected int, got {type(actual).__name__}"
        return
    if expected == "<bool>":
        assert isinstance(actual, bool), f"{path}: expected bool, got {type(actual).__name__}"
        return
    if expected == "<dict>":
        assert isinstance(actual, dict), f"{path}: expected dict, got {type(actual).__name__}"
        return
    if expected == "<list>":
        assert isinstance(actual, list), f"{path}: expected list, got {type(actual).__name__}"
        return
    if expected == "<str_or_null>":
        assert actual is None or isinstance(actual, str), f"{path}: expected str|null, got {type(actual).__name__}"
        return
    if expected == "<dict_or_null>":
        assert actual is None or isinstance(actual, dict), f"{path}: expected dict|null, got {type(actual).__name__}"
        return

    if isinstance(expected, dict):
        assert isinstance(actual, dict), f"{path}: expected dict, got {type(actual).__name__}"
        for key, subshape in expected.items():
            assert key in actual, f"{path}: missing key '{key}'"
            _assert_shape_subset(subshape, actual[key], f"{path}.{key}")
        return

    if isinstance(expected, list):
        assert isinstance(actual, list), f"{path}: expected list, got {type(actual).__name__}"
        if expected:
            assert actual, f"{path}: expected non-empty list"
            _assert_shape_subset(expected[0], actual[0], f"{path}[0]")
        return

    assert actual == expected, f"{path}: expected {expected!r}, got {actual!r}"


def test_app_bootstrap_matches_legacy_fixture(client):
    fixture = _load_fixture("app_bootstrap_request_client_meta_v1.json")
    expected_shape = _load_fixture("app_bootstrap_response_shape_v1.json")

    response = client.get("/app/bootstrap", headers=fixture["headers"])

    assert response.status_code == 200, response.text
    body = response.json()
    _assert_shape_subset(expected_shape, body)
    assert body["client_meta"]["app_version"] == fixture["headers"]["X-App-Version"]
    assert body["client_meta"]["app_build"] == fixture["headers"]["X-App-Build"]
    assert body["client_meta"]["platform"] == fixture["headers"]["X-Platform"]


def test_legacy_emotion_submit_fixture_still_works(client, monkeypatch):
    import api_emotion_submit as emotion_submit_module
    import emotion_submit_service as emotion_submit_service_module

    fixture = _load_fixture("legacy_emotion_submit_request_v1.json")
    expected_shape = _load_fixture("legacy_emotion_submit_response_shape_v1.json")
    inserted_payload: Dict[str, Any] = {}
    background_payload: Dict[str, Any] = {}

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
        headers=fixture["headers"],
        json=fixture["json"],
    )

    assert response.status_code == 200, response.text
    _assert_shape_subset(expected_shape, response.json())
    assert inserted_payload["category"] == []
    assert background_payload["memo"] == fixture["json"]["memo"]


def test_account_profile_me_response_matches_legacy_shape_fixture(client, monkeypatch):
    import api_account_lifecycle as account_lifecycle_module

    expected_shape = _load_fixture("account_profile_me_response_shape_v1.json")

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
    _assert_shape_subset(expected_shape, response.json())


def test_account_display_name_availability_matches_snapshot_shape(client, monkeypatch):
    import api_account_lifecycle as account_lifecycle_module

    expected_shape = _load_fixture("account_display_name_availability_response_shape_v1.json")

    async def fake_require_user_id(_authorization):
        return "user-456"

    async def fake_is_display_name_available(candidate: str, *, exclude_user_id: Optional[str] = None) -> bool:
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
    _assert_shape_subset(expected_shape, response.json())


def test_report_distribution_settings_matches_snapshot_shape(client, monkeypatch):
    import api_report_distribution_settings as report_distribution_settings_module

    expected_shape = _load_fixture("report_distribution_settings_response_shape_v1.json")

    async def fake_require_user_id(_authorization):
        return "user-456"

    async def fake_get_or_create_user_settings(_user_id: str, *, timezone_name: Optional[str] = None):
        return {
            "notification_enabled": True,
            "delivery_time_local": "00:00",
            "timezone_name": timezone_name or "Asia/Tokyo",
        }

    monkeypatch.setattr(report_distribution_settings_module, "_require_user_id", fake_require_user_id)
    monkeypatch.setattr(
        report_distribution_settings_module.store,
        "get_or_create_user_settings",
        fake_get_or_create_user_settings,
    )

    response = client.get(
        "/report-distribution/settings?timezone_name=Asia%2FTokyo",
        headers={"Authorization": "Bearer test-token"},
    )

    assert response.status_code == 200, response.text
    _assert_shape_subset(expected_shape, response.json())



def test_mymodel_create_answers_accepts_missing_is_secret_fixture(client, monkeypatch):
    import api_profile_create as create_module

    fixture = _load_fixture("legacy_mymodel_create_answers_request_v1.json")
    expected_shape = _load_fixture("mymodel_create_answers_response_shape_v1.json")
    saved_batches = []

    async def fake_resolve_user_id_from_token(_access_token: str) -> str:
        return "user-789"

    async def fake_touch_active_user(_user_id: str, activity: Optional[str] = None):
        return None

    async def fake_get_subscription_tier_for_user(_user_id: str):
        return create_module.SubscriptionTier.PLUS

    async def fake_fetch_questions(*, build_tier: str):
        return [
            {"id": 1, "question_text": "Question 1", "sort_order": 1, "tier": build_tier, "is_active": True},
        ]

    async def fake_fetch_questions_all_active():
        return [
            {"id": 1, "question_text": "Question 1", "sort_order": 1, "tier": "light", "is_active": True},
        ]

    async def fake_fetch_answers(*, user_id: str, question_ids=None):
        return {
            1: {"question_id": 1, "answer_text": "Existing answer", "updated_at": "2026-03-10T00:00:00Z", "is_secret": True},
        }

    async def fake_sb_post(path, *, params=None, json=None, prefer=None):
        saved_batches.extend(list(json or []))
        return _FakeResponse(201, [])

    async def fake_sb_delete(path, *, params=None):
        return _FakeResponse(204, [])

    async def fake_enqueue_global_snapshot_refresh(*args, **kwargs):
        return None

    async def fake_enqueue_account_status_refresh(*args, **kwargs):
        return None

    monkeypatch.setattr(create_module, "_resolve_user_id_from_token", fake_resolve_user_id_from_token)
    monkeypatch.setattr(create_module, "touch_active_user", fake_touch_active_user)
    monkeypatch.setattr(create_module, "get_subscription_tier_for_user", fake_get_subscription_tier_for_user)
    monkeypatch.setattr(create_module, "_fetch_questions", fake_fetch_questions)
    monkeypatch.setattr(create_module, "_fetch_questions_all_active", fake_fetch_questions_all_active)
    monkeypatch.setattr(create_module, "_fetch_answers", fake_fetch_answers)
    monkeypatch.setattr(create_module, "_sb_post", fake_sb_post)
    monkeypatch.setattr(create_module, "_sb_delete", fake_sb_delete)
    monkeypatch.setattr(create_module, "enqueue_global_snapshot_refresh", fake_enqueue_global_snapshot_refresh)
    monkeypatch.setattr(create_module, "enqueue_account_status_refresh", fake_enqueue_account_status_refresh)

    response = client.post(
        "/profile-create/answers",
        headers=fixture["headers"],
        json=fixture["json"],
    )

    assert response.status_code == 200, response.text
    assert saved_batches, "expected at least one upsert payload"
    assert saved_batches[0]["is_secret"] is True
    _assert_shape_subset(expected_shape, response.json())



def test_myweb_unread_status_matches_snapshot_shape(client, monkeypatch):
    import api_report_reads as report_reads_module

    expected_shape = _load_fixture("report_reads_myweb_unread_status_response_shape_v1.json")

    async def fake_require_user_id(_authorization):
        return "user-123"

    async def fake_resolve_viewer_tier(_user_id: str) -> str:
        return "free"

    async def fake_sb_get(path, *, params=None, timeout=8.0):
        if path == "/rest/v1/analysis_reports":
            report_type = params.get("report_type", "").replace("eq.", "")
            rows = [
                {
                    "id": f"{report_type}-draft",
                    "report_type": report_type,
                    "period_start": "2026-03-01T00:00:00Z",
                    "period_end": "2026-03-01T23:59:59Z",
                    "content_json": {"publish": {"status": "DRAFT"}, "metrics": {"totalAll": 3}},
                },
                {
                    "id": f"{report_type}-ready",
                    "report_type": report_type,
                    "period_start": "2026-03-02T00:00:00Z",
                    "period_end": "2026-03-02T23:59:59Z",
                    "content_json": {"publish": {"status": "READY"}, "metrics": {"totalAll": 3}},
                },
            ]
            return _FakeResponse(200, rows)
        if path == "/rest/v1/report_reads":
            return _FakeResponse(200, [])
        raise AssertionError(f"unexpected path: {path}")

    monkeypatch.setattr(report_reads_module, "_require_user_id", fake_require_user_id)
    monkeypatch.setattr(report_reads_module, "_resolve_viewer_tier", fake_resolve_viewer_tier)
    monkeypatch.setattr(report_reads_module, "sb_get", fake_sb_get)

    response = client.get(
        "/report-reads/myweb-unread-status?limit=1&include_self_structure=false",
        headers={"Authorization": "Bearer test-token"},
    )

    assert response.status_code == 200, response.text
    _assert_shape_subset(expected_shape, response.json())


def test_myprofile_history_matches_snapshot_shape(client, monkeypatch):
    import api_self_structure_reports as self_structure_reports_module
    import report_artifact_read_service as report_read_service

    expected_shape = _load_fixture("myprofile_reports_history_response_shape_v1.json")

    async def fake_require_user_id(_authorization):
        return "user-789"

    async def fake_sb_get(path, *, params=None, timeout=8.0):
        assert path == "/rest/v1/self_structure_reports"
        return _FakeResponse(
            200,
            [
                {
                    "id": "monthly-hidden",
                    "report_type": "monthly",
                    "title": "hidden",
                    "period_start": "2026-02-01T00:00:00Z",
                    "period_end": "2026-02-28T23:59:59Z",
                    "generated_at": "2026-03-01T00:00:00Z",
                    "updated_at": "2026-03-01T00:00:00Z",
                    "content_text": "",
                    "content_json": {},
                },
                {
                    "id": "monthly-visible",
                    "report_type": "monthly",
                    "title": "visible",
                    "period_start": "2026-02-01T00:00:00Z",
                    "period_end": "2026-02-28T23:59:59Z",
                    "generated_at": "2026-03-01T00:00:00Z",
                    "updated_at": "2026-03-01T00:00:00Z",
                    "content_text": "published body",
                    "content_json": {"report_mode": "standard"},
                },
            ],
        )

    async def fake_resolve_subscription_tier(_user_id: str) -> str:
        return "premium"

    class FakeReportViewContext:
        subscription_tier = "premium"

    async def fake_resolve_report_view_context(_user_id: str, *, now_utc=None):
        return FakeReportViewContext()

    monkeypatch.setattr(self_structure_reports_module, "_require_user_id", fake_require_user_id)
    monkeypatch.setattr(report_read_service, "_resolve_subscription_tier", fake_resolve_subscription_tier)
    monkeypatch.setattr(report_read_service, "resolve_report_view_context", fake_resolve_report_view_context)
    monkeypatch.setattr(report_read_service, "sb_get", fake_sb_get)

    response = client.get(
        "/myprofile/reports/history?report_type=monthly&limit=60",
        headers={"Authorization": "Bearer test-token"},
    )

    assert response.status_code == 200, response.text
    _assert_shape_subset(expected_shape, response.json())



def test_global_summary_matches_response_shape_fixture(client, monkeypatch):
    import api_global_summary as global_summary_module

    monkeypatch.setattr(global_summary_module, "_today_jst_date_iso", lambda: "2026-03-12")

    expected_shape = _load_fixture("global_summary_response_shape_v1.json")

    async def fake_fetch_latest_ready_global_summary(activity_date: str, *, timezone_name: str):
        return {
            "activity_date": activity_date,
            "timezone": timezone_name,
            "published_at": "2026-03-12T03:00:00Z",
            "payload": {
                "version": "global_summary.v1",
                "activity_date": activity_date,
                "timezone": timezone_name,
                "generated_at": "2026-03-12T02:59:59Z",
                "totals": {
                    "emotion_users": 12,
                    "reflection_views": 24,
                    "echo_count": 36,
                    "discovery_count": 48,
                },
            },
        }

    async def fake_generate_global_summary_payload(*args, **kwargs):
        raise AssertionError("legacy fallback should not run when READY artifact exists")

    monkeypatch.setattr(global_summary_module, "fetch_latest_ready_global_summary", fake_fetch_latest_ready_global_summary)
    monkeypatch.setattr(global_summary_module, "generate_global_summary_payload", fake_generate_global_summary_payload)

    response = client.get("/global_summary?date=2026-03-11")

    assert response.status_code == 200, response.text
    _assert_shape_subset(expected_shape, response.json())



def test_app_startup_matches_response_shape_fixture(client, monkeypatch):
    import api_app_bootstrap as app_bootstrap_module
    import startup_snapshot_store as startup_snapshot_store_module

    expected_shape = _load_fixture("app_startup_response_shape_v1.json")

    async def fake_require_user_id(_authorization):
        return "user-123"

    async def fake_get_startup_snapshot(_user_id: str, *, client_meta=None, timezone_name=None, force_refresh=False):
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
                "today_question_light": "today_question.current.light.v1"
            },
            "flags": {
                "has_any_emotion_log_unread": True,
                "has_any_friends_unread": True,
                "has_any_myweb_unread": False,
                "has_popup_notice": True,
                "today_question_answered": False
            },
            "sections": {
                "emotion_log_unread": {
                    "status": "ok",
                    "feed_unread": True,
                    "requests_unread": False,
                    "incoming_pending_count": 0,
                    "feed_last_read_at": None,
                    "requests_last_read_at": None
                },
                "friends_unread": {
                    "status": "ok",
                    "feed_unread": True,
                    "requests_unread": False,
                    "incoming_pending_count": 0,
                    "feed_last_read_at": None,
                    "requests_last_read_at": None
                },
                "myweb_unread": {
                    "status": "ok",
                    "viewer_tier": "free",
                    "ids_by_type": {"daily": [], "weekly": [], "monthly": [], "selfStructure": []},
                    "read_ids": [],
                    "unread_by_type": {"daily": False, "weekly": False, "monthly": False, "selfStructure": False}
                },
                "notices_current": {
                    "feature_enabled": True,
                    "unread_count": 1,
                    "has_unread": True,
                    "badge": {"show": True, "count": 1},
                    "popup_notice": {"notice_id": "notice-1", "title": "hello", "body": "notice body"}
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
                        "free_text_enabled": True
                    },
                    "delivery": {},
                    "progress": {}
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
                        "free_text_enabled": True
                    },
                    "delivery": {},
                    "progress": {}
                }
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
    body = response.json()
    _assert_shape_subset(expected_shape, body)
    assert "input_summary" not in body["startup"]["sections"]
    assert "global_summary" not in body["startup"]["sections"]



def test_home_state_matches_response_shape_fixture(client, monkeypatch):
    import api_home_state as home_state_module

    expected_shape = _load_fixture("home_state_response_shape_v1.json")

    async def fake_resolve_authenticated_user_id(*, authorization=None, legacy_user_id=None):
        return "user-123"

    async def fake_get_home_state(_user_id: str, *, client_meta=None, timezone_name=None, force_refresh=False):
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
                    "last_input_at": "2026-04-19T00:00:00Z"
                },
                "global_summary": {
                    "date": "2026-04-19",
                    "tz": "+09:00",
                    "emotion_users": 5,
                    "reflection_views": 6,
                    "echo_count": 7,
                    "discovery_count": 8,
                    "updated_at": "2026-04-19T00:00:00Z"
                },
                "notices_current": {
                    "feature_enabled": True,
                    "unread_count": 1,
                    "has_unread": True,
                    "badge": {"show": True, "count": 1},
                    "popup_notice": {"notice_id": "notice-1", "title": "hello", "body": "notice body"}
                },
                "today_question_current": {
                    "service_day_key": "2026-04-19",
                    "question": {
                        "question_id": "q-1",
                        "question_key": "qkey",
                        "version": 1,
                        "text": "今日の問い",
                        "choice_count": 3,
                        "choices": [{"choice_id": "c-1", "choice_key": "one", "label": "はい"}],
                        "free_text_enabled": True
                    },
                    "answer_status": "unanswered",
                    "answer_summary": None,
                    "delivery": {},
                    "progress": {}
                },
                "emotion_reflection_quota": {
                    "status": "ok",
                    "subscription_tier": "free",
                    "month_key": "2026-04",
                    "publish_limit": 0,
                    "published_count": 0,
                    "remaining_count": 0,
                    "can_publish": False
                }
            },
            "errors": {}
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
    body = response.json()
    _assert_shape_subset(expected_shape, body)
