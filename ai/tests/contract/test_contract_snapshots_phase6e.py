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

    fixture = _load_fixture("legacy_emotion_submit_request_v1.json")
    expected_shape = _load_fixture("legacy_emotion_submit_response_shape_v1.json")
    inserted_payload: Dict[str, Any] = {}
    background_payload: Dict[str, Any] = {}

    async def fake_resolve_user_id_from_token(_access_token: str) -> str:
        return "user-123"

    async def fake_insert_emotion_row(**kwargs):
        inserted_payload.update(kwargs)
        return {"id": "emo-1", "created_at": kwargs["created_at"]}

    def fake_start_background_tasks(**kwargs):
        background_payload.update(kwargs)

    monkeypatch.setattr(emotion_submit_module, "_resolve_user_id_from_token", fake_resolve_user_id_from_token)
    monkeypatch.setattr(emotion_submit_module, "_insert_emotion_row", fake_insert_emotion_row)
    monkeypatch.setattr(emotion_submit_module, "_start_post_submit_background_tasks", fake_start_background_tasks)

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


def test_mymodel_create_questions_keeps_legacy_editable_shape(client, monkeypatch):
    import api_mymodel_create as create_module

    expected_shape = _load_fixture("mymodel_create_questions_response_shape_v1.json")

    async def fake_resolve_user_id_from_token(_access_token: str) -> str:
        return "user-789"

    async def fake_touch_active_user(_user_id: str, activity: Optional[str] = None):
        return None

    async def fake_get_subscription_tier_for_user(_user_id: str):
        return create_module.SubscriptionTier.FREE

    async def fake_fetch_questions_all_active():
        return [
            {"id": 1, "question_text": "Question 1", "sort_order": 1, "tier": "light", "is_active": True},
            {"id": 2, "question_text": "Question 2", "sort_order": 2, "tier": "light", "is_active": True},
        ]

    async def fake_fetch_answers(*, user_id: str, question_ids=None):
        return {
            1: {"question_id": 1, "answer_text": "Saved answer", "updated_at": "2026-03-11T00:00:00Z", "is_secret": True},
        }

    monkeypatch.setattr(create_module, "_resolve_user_id_from_token", fake_resolve_user_id_from_token)
    monkeypatch.setattr(create_module, "touch_active_user", fake_touch_active_user)
    monkeypatch.setattr(create_module, "get_subscription_tier_for_user", fake_get_subscription_tier_for_user)
    monkeypatch.setattr(create_module, "_fetch_questions_all_active", fake_fetch_questions_all_active)
    monkeypatch.setattr(create_module, "_fetch_answers", fake_fetch_answers)

    response = client.get("/mymodel/create/questions?build_tier=light", headers={"Authorization": "Bearer test-token"})

    assert response.status_code == 200, response.text
    body = response.json()
    _assert_shape_subset(expected_shape, body)
    assert body["questions"][0]["editable"] is False
    assert body["questions"][0]["can_edit"] is False
    assert body["questions"][0]["edit_block_reason"] == create_module.EDIT_LOCKED_MESSAGE
    assert body["meta"]["can_edit_existing"] is False
    assert body["meta"]["can_toggle_secret_without_edit"] is True


def test_mymodel_create_answers_accepts_missing_is_secret_fixture(client, monkeypatch):
    import api_mymodel_create as create_module

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
        "/mymodel/create/answers",
        headers=fixture["headers"],
        json=fixture["json"],
    )

    assert response.status_code == 200, response.text
    assert saved_batches, "expected at least one upsert payload"
    assert saved_batches[0]["is_secret"] is True
    _assert_shape_subset(expected_shape, response.json())


def test_mymodel_create_answers_free_blocks_text_edit_but_allows_secret_toggle(client, monkeypatch):
    import api_mymodel_create as create_module

    saved_batches = []

    async def fake_resolve_user_id_from_token(_access_token: str) -> str:
        return "user-999"

    async def fake_touch_active_user(_user_id: str, activity: Optional[str] = None):
        return None

    async def fake_get_subscription_tier_for_user(_user_id: str):
        return create_module.SubscriptionTier.FREE

    async def fake_fetch_questions_all_active():
        return [
            {"id": 1, "question_text": "Question 1", "sort_order": 1, "tier": "light", "is_active": True},
        ]

    async def fake_fetch_answers(*, user_id: str, question_ids=None):
        return {
            1: {
                "question_id": 1,
                "answer_text": "Existing answer",
                "updated_at": "2026-03-10T00:00:00Z",
                "is_secret": False,
            },
        }

    async def fake_sb_post(path, *, params=None, json=None, prefer=None):
        saved_batches.extend(list(json or []))
        return _FakeResponse(201, [])

    async def fake_sb_delete(path, *, params=None):
        raise AssertionError("free user should not be able to clear an existing answer")

    async def fake_enqueue_global_snapshot_refresh(*args, **kwargs):
        return None

    async def fake_enqueue_account_status_refresh(*args, **kwargs):
        return None

    monkeypatch.setattr(create_module, "_resolve_user_id_from_token", fake_resolve_user_id_from_token)
    monkeypatch.setattr(create_module, "touch_active_user", fake_touch_active_user)
    monkeypatch.setattr(create_module, "get_subscription_tier_for_user", fake_get_subscription_tier_for_user)
    monkeypatch.setattr(create_module, "_fetch_questions_all_active", fake_fetch_questions_all_active)
    monkeypatch.setattr(create_module, "_fetch_answers", fake_fetch_answers)
    monkeypatch.setattr(create_module, "_sb_post", fake_sb_post)
    monkeypatch.setattr(create_module, "_sb_delete", fake_sb_delete)
    monkeypatch.setattr(create_module, "enqueue_global_snapshot_refresh", fake_enqueue_global_snapshot_refresh)
    monkeypatch.setattr(create_module, "enqueue_account_status_refresh", fake_enqueue_account_status_refresh)

    response = client.post(
        "/mymodel/create/answers",
        headers={"Authorization": "Bearer test-token"},
        json={
            "answers": [
                {
                    "question_id": 1,
                    "answer_text": "Edited text should be blocked",
                    "is_secret": True,
                }
            ]
        },
    )

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["status"] == "partial"
    assert body["saved"] == 0
    assert body["skipped_locked"] == 1
    assert saved_batches == []

    response_toggle = client.post(
        "/mymodel/create/answers",
        headers={"Authorization": "Bearer test-token"},
        json={
            "answers": [
                {
                    "question_id": 1,
                    "is_secret": True,
                }
            ]
        },
    )

    assert response_toggle.status_code == 200, response_toggle.text
    toggle_body = response_toggle.json()
    assert toggle_body["status"] == "ok"
    assert toggle_body["saved"] == 1
    assert saved_batches == [
        {
            "user_id": "user-999",
            "question_id": 1,
            "answer_text": "Existing answer",
            "is_secret": True,
        }
    ]


def test_myweb_unread_status_matches_snapshot_shape(client, monkeypatch):
    import api_report_reads as report_reads_module

    expected_shape = _load_fixture("report_reads_myweb_unread_status_response_shape_v1.json")

    async def fake_require_user_id(_authorization):
        return "user-123"

    async def fake_resolve_viewer_tier(_user_id: str) -> str:
        return "free"

    async def fake_sb_get(path, *, params=None, timeout=8.0):
        if path == "/rest/v1/myweb_reports":
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
    import api_myprofile_reports_read as myprofile_reports_module

    expected_shape = _load_fixture("myprofile_reports_history_response_shape_v1.json")

    async def fake_require_user_id(_authorization):
        return "user-789"

    async def fake_sb_get(path, *, params=None, timeout=8.0):
        assert path == "/rest/v1/myprofile_reports"
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

    monkeypatch.setattr(myprofile_reports_module, "_require_user_id", fake_require_user_id)
    monkeypatch.setattr(myprofile_reports_module, "sb_get", fake_sb_get)

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
