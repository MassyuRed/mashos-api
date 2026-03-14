from __future__ import annotations


def test_myweb_unread_status_ignores_non_publishable_reports(client, monkeypatch):
    import api_report_reads as report_reads_module

    async def fake_require_user_id(_authorization):
        return "user-123"

    async def fake_resolve_viewer_tier(_user_id: str) -> str:
        return "free"

    class FakeResponse:
        def __init__(self, status_code, payload):
            self.status_code = status_code
            self._payload = payload
            self.text = ""

        def json(self):
            return self._payload

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
            return FakeResponse(200, rows)
        if path == "/rest/v1/report_reads":
            return FakeResponse(200, [])
        raise AssertionError(f"unexpected path: {path}")

    monkeypatch.setattr(report_reads_module, "_require_user_id", fake_require_user_id)
    monkeypatch.setattr(report_reads_module, "_resolve_viewer_tier", fake_resolve_viewer_tier)
    monkeypatch.setattr(report_reads_module, "sb_get", fake_sb_get)

    response = client.get(
        "/report-reads/myweb-unread-status?limit=1&include_self_structure=false",
        headers={"Authorization": "Bearer test-token"},
    )

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["ids_by_type"]["daily"] == ["daily-ready"]
    assert body["ids_by_type"]["weekly"] == ["weekly-ready"]
    assert body["ids_by_type"]["monthly"] == ["monthly-ready"]


def test_myweb_weekly_days_rejects_non_publishable_reports(client, monkeypatch):
    import api_myweb_reads as myweb_reads_module

    async def fake_require_user_id(_authorization):
        return "user-456"

    async def fake_resolve_viewer_tier(_user_id: str) -> str:
        return "premium"

    class FakeResponse:
        status_code = 200
        text = ""

        def json(self):
            return [
                {
                    "id": "weekly-1",
                    "report_type": "weekly",
                    "period_start": "2026-03-01T00:00:00Z",
                    "period_end": "2026-03-07T23:59:59Z",
                    "content_json": {"publish": {"status": "DRAFT"}},
                }
            ]

    async def fake_sb_get(path, *, params=None, timeout=8.0):
        assert path == "/rest/v1/myweb_reports"
        return FakeResponse()

    monkeypatch.setattr(myweb_reads_module, "_require_user_id", fake_require_user_id)
    monkeypatch.setattr(myweb_reads_module, "_resolve_viewer_tier", fake_resolve_viewer_tier)
    monkeypatch.setattr(myweb_reads_module, "sb_get", fake_sb_get)

    response = client.get("/myweb/reports/weekly-1/weekly-days", headers={"Authorization": "Bearer test-token"})
    assert response.status_code == 404


def test_myprofile_history_filters_non_publishable_rows(client, monkeypatch):
    import api_myprofile_reports_read as myprofile_reports_module

    async def fake_require_user_id(_authorization):
        return "user-789"

    class FakeResponse:
        status_code = 200
        text = ""

        def json(self):
            return [
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
            ]

    async def fake_sb_get(path, *, params=None, timeout=8.0):
        assert path == "/rest/v1/myprofile_reports"
        return FakeResponse()

    monkeypatch.setattr(myprofile_reports_module, "_require_user_id", fake_require_user_id)
    monkeypatch.setattr(myprofile_reports_module, "sb_get", fake_sb_get)

    response = client.get("/myprofile/reports/history?report_type=monthly&limit=60", headers={"Authorization": "Bearer test-token"})
    assert response.status_code == 200, response.text
    body = response.json()
    assert [item["id"] for item in body["items"]] == ["monthly-visible"]


def test_myprofile_detail_rejects_non_publishable_row(client, monkeypatch):
    import api_myprofile_reports_read as myprofile_reports_module

    async def fake_require_user_id(_authorization):
        return "user-789"

    class FakeResponse:
        status_code = 200
        text = ""

        def json(self):
            return [
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
                }
            ]

    async def fake_sb_get(path, *, params=None, timeout=8.0):
        assert path == "/rest/v1/myprofile_reports"
        return FakeResponse()

    monkeypatch.setattr(myprofile_reports_module, "_require_user_id", fake_require_user_id)
    monkeypatch.setattr(myprofile_reports_module, "sb_get", fake_sb_get)

    response = client.get("/myprofile/reports/monthly-hidden", headers={"Authorization": "Bearer test-token"})
    assert response.status_code == 404



def test_global_summary_prefers_ready_artifact_over_legacy_fallback(client, monkeypatch):
    import api_global_summary as global_summary_module

    async def fake_fetch_latest_ready_global_summary(activity_date: str, *, timezone_name: str):
        return {
            "activity_date": activity_date,
            "timezone": timezone_name,
            "published_at": "2026-03-12T01:23:45Z",
            "payload": {
                "version": "global_summary.v1",
                "activity_date": activity_date,
                "timezone": timezone_name,
                "generated_at": "2026-03-12T01:23:40Z",
                "totals": {
                    "emotion_users": 21,
                    "reflection_views": 34,
                    "echo_count": 55,
                    "discovery_count": 89,
                },
            },
        }

    async def fake_generate_global_summary_payload(*args, **kwargs):
        raise AssertionError("legacy fallback should not run when READY artifact exists")

    monkeypatch.setattr(global_summary_module, "fetch_latest_ready_global_summary", fake_fetch_latest_ready_global_summary)
    monkeypatch.setattr(global_summary_module, "generate_global_summary_payload", fake_generate_global_summary_payload)

    response = client.get("/global_summary?date=2026-03-11&tz=%2B09:00")

    assert response.status_code == 200, response.text
    body = response.json()
    assert body == {
        "date": "2026-03-11",
        "tz": "+09:00",
        "emotion_users": 21,
        "reflection_views": 34,
        "echo_count": 55,
        "discovery_count": 89,
        "updated_at": "2026-03-12T01:23:45Z",
    }


def test_global_summary_uses_migration_fallback_when_ready_missing(client, monkeypatch):
    import api_global_summary as global_summary_module

    async def fake_fetch_latest_ready_global_summary(activity_date: str, *, timezone_name: str):
        return None

    async def fake_generate_global_summary_payload(
        activity_date: str,
        *,
        timezone_name: str,
        prefer_refresh: bool,
        fallback_to_table: bool,
        allow_empty: bool,
    ):
        assert activity_date == "2026-03-11"
        assert timezone_name == "Asia/Tokyo"
        assert prefer_refresh is False
        assert fallback_to_table is True
        assert allow_empty is False
        return {
            "version": "global_summary.v1",
            "activity_date": activity_date,
            "timezone": timezone_name,
            "generated_at": "2026-03-12T02:00:00Z",
            "totals": {
                "emotion_users": 3,
                "reflection_views": 5,
                "echo_count": 8,
                "discovery_count": 13,
            },
        }

    monkeypatch.setattr(global_summary_module, "fetch_latest_ready_global_summary", fake_fetch_latest_ready_global_summary)
    monkeypatch.setattr(global_summary_module, "generate_global_summary_payload", fake_generate_global_summary_payload)

    response = client.get("/global_summary?date=2026-03-11&tz=Asia%2FTokyo")

    assert response.status_code == 200, response.text
    body = response.json()
    assert body == {
        "date": "2026-03-11",
        "tz": "+09:00",
        "emotion_users": 3,
        "reflection_views": 5,
        "echo_count": 8,
        "discovery_count": 13,
        "updated_at": "2026-03-12T02:00:00Z",
    }
