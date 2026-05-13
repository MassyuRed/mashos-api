from __future__ import annotations

from datetime import datetime, timezone

import pytest
from fastapi import HTTPException, FastAPI
from fastapi.testclient import TestClient

import api_analysis_reads as reads
import api_analysis_reports as reports
import api_report_reads as report_reads
from kokoro_weather_service import build_report_kokoro_weather


def test_build_report_kokoro_weather_weekly_has_day_items_and_time_buckets():
    start = datetime(2026, 5, 11, 15, 0, tzinfo=timezone.utc)
    end = datetime(2026, 5, 18, 14, 59, tzinfo=timezone.utc)
    rows = [
        {"created_at": "2026-05-11T16:30:00Z", "emotion_details": [{"type": "平穏", "strength": "medium"}]},
        {"created_at": "2026-05-12T02:30:00Z", "emotion_details": [{"type": "不安", "strength": "strong"}]},
        {"created_at": "2026-05-12T09:30:00Z", "emotion_details": [{"type": "喜び", "strength": "weak"}]},
    ]

    payload = build_report_kokoro_weather(
        report_type="weekly",
        rows=rows,
        period_start_utc=start,
        period_end_utc=end,
        existing_metrics={"totals": {"calm": 2, "anxiety": 3, "joy": 1}, "totalAll": 6},
    )

    assert payload["version"] == "kokoro.weather.v1"
    assert payload["report_type"] == "weekly"
    assert len(payload["items"]) == 7
    assert payload["items"][0]["kind"] == "day"
    assert payload["items"][0]["time_buckets"]
    assert payload["summary"]["temperature_display"].endswith("°")
    assert payload["summary"]["observation_memo"]["label"] in ("", "観測メモあり")


def test_build_report_kokoro_weather_from_snapshot_days_without_rows_is_fail_closed():
    start = datetime(2026, 5, 11, 15, 0, tzinfo=timezone.utc)
    end = datetime(2026, 5, 18, 14, 59, tzinfo=timezone.utc)
    days = [
        {"dateKey": "2026-05-12", "label": "5/12", "calm": 3, "anxiety": 1, "dominantKey": "calm"},
        {"dateKey": "2026-05-13", "label": "5/13", "sadness": 2, "calm": 1, "dominantKey": "sadness"},
    ]

    payload = build_report_kokoro_weather(
        report_type="weekly",
        rows=[],
        period_start_utc=start,
        period_end_utc=end,
        existing_metrics={"totals": {"calm": 4, "sadness": 2, "anxiety": 1}, "totalAll": 7},
        existing_days=days,
    )

    assert payload["report_type"] == "weekly"
    assert len(payload["items"]) == 2
    assert payload["items"][0]["weather_key"] in {"clear", "partly_cloudy", "cloudy", "soft_rain", "windy", "mixed", "unknown"}
    assert payload["items"][0]["temperature_display"].endswith("°")


def test_kokoro_weather_report_row_helper_accepts_full_and_projection_rows():
    full_row = {
        "report_type": "weekly",
        "content_json": {
            "kokoroWeather": {
                "version": "kokoro.weather.v1",
                "summary": {"weather_label": "うすぐもり"},
                "items": [],
            }
        },
    }
    projection_row = {
        "report_type": "weekly",
        "kokoro_weather_version": "kokoro.weather.v1",
    }
    old_row = {
        "report_type": "weekly",
        "content_json": {"standardReport": {"contentText": "旧感情分析本文"}},
    }

    assert reports._is_kokoro_weather_report_row(full_row) is True
    assert reports._is_kokoro_weather_report_row(projection_row) is True
    assert reports._is_kokoro_weather_report_row(old_row) is False


@pytest.mark.asyncio
async def test_ready_projection_filters_old_emotion_reports(monkeypatch):
    class DummyViewContext:
        subscription_tier = "premium"
        history_retention = {}

    rows = [
        {
            "id": "old-report",
            "report_type": "weekly",
            "period_start": "2026-05-04T15:00:00Z",
            "period_end": "2026-05-11T14:59:59Z",
            "title": "旧感情分析",
            "generated_at": "2026-05-11T15:00:00Z",
            "updated_at": "2026-05-11T15:00:00Z",
        },
        {
            "id": "kokoro-report",
            "report_type": "weekly",
            "period_start": "2026-05-11T15:00:00Z",
            "period_end": "2026-05-18T14:59:59Z",
            "title": "こころ天気（週）",
            "kokoro_weather_version": "kokoro.weather.v1",
            "generated_at": "2026-05-18T15:00:00Z",
            "updated_at": "2026-05-18T15:00:00Z",
        },
    ]

    async def fake_resolve_report_view_context(*_args, **_kwargs):
        return DummyViewContext()

    async def fake_fetch_candidate_chunk(*_args, **_kwargs):
        return rows

    monkeypatch.setattr(reports, "resolve_report_view_context", fake_resolve_report_view_context)
    monkeypatch.setattr(reports, "_fetch_myweb_ready_candidate_chunk", fake_fetch_candidate_chunk)
    monkeypatch.setattr(reports, "apply_myweb_report_access_for_viewer", lambda row, **_kwargs: row)

    payload = await reports._build_myweb_ready_payload_projection_first(
        user_id="user-1",
        report_type="weekly",
        lim=10,
        off=0,
        include_body=False,
    )

    assert [item["id"] for item in payload["items"]] == ["kokoro-report"]


@pytest.mark.asyncio
async def test_ready_latest_body_filters_old_full_rows(monkeypatch):
    class DummyViewContext:
        subscription_tier = "premium"
        history_retention = {}

    old_content = {"standardReport": {"contentText": "旧感情分析本文"}}
    kokoro_content = {
        "kokoroWeather": {
            "version": "kokoro.weather.v1",
            "summary": {"weather_label": "風あり"},
            "items": [{"kind": "day", "label": "12(火)"}],
        }
    }
    rows = [
        {
            "id": "old-report",
            "report_type": "weekly",
            "period_start": "2026-05-04T15:00:00Z",
            "period_end": "2026-05-11T14:59:59Z",
            "title": "旧感情分析",
            "content_text": "旧本文",
            "content_json": old_content,
            "generated_at": "2026-05-11T15:00:00Z",
            "updated_at": "2026-05-11T15:00:00Z",
        },
        {
            "id": "kokoro-report",
            "report_type": "weekly",
            "period_start": "2026-05-11T15:00:00Z",
            "period_end": "2026-05-18T14:59:59Z",
            "title": "こころ天気（週）",
            "content_text": "こころ天気本文",
            "content_json": kokoro_content,
            "generated_at": "2026-05-18T15:00:00Z",
            "updated_at": "2026-05-18T15:00:00Z",
        },
    ]

    async def fake_resolve_report_view_context(*_args, **_kwargs):
        return DummyViewContext()

    async def fake_fetch_full_candidate_chunk(*_args, **_kwargs):
        return rows

    monkeypatch.setattr(reports, "resolve_report_view_context", fake_resolve_report_view_context)
    monkeypatch.setattr(reports, "_fetch_myweb_ready_full_candidate_chunk", fake_fetch_full_candidate_chunk)
    monkeypatch.setattr(reports, "apply_myweb_report_access_for_viewer", lambda row, **_kwargs: row)

    payload = await reports._build_myweb_ready_payload_projection_first(
        user_id="user-1",
        report_type="weekly",
        lim=1,
        off=0,
        include_body=True,
    )

    assert [item["id"] for item in payload["items"]] == ["kokoro-report"]
    assert payload["items"][0]["content_text"] == "こころ天気本文"


@pytest.mark.asyncio
async def test_generate_daily_report_attaches_kokoro_weather_without_changing_internal_type(monkeypatch):
    start = datetime(2026, 5, 12, 0, 0, tzinfo=timezone.utc)
    end = datetime(2026, 5, 12, 23, 59, tzinfo=timezone.utc)
    target = reports.TargetPeriod(
        report_type="daily",
        dist_utc=end,
        period_start_utc=start,
        period_end_utc=end,
        period_start_iso=start.isoformat().replace("+00:00", "Z"),
        period_end_iso=end.isoformat().replace("+00:00", "Z"),
        title="こころ天気（日）: test",
        title_meta={},
    )
    rows = [
        {"created_at": "2026-05-12T01:00:00Z", "is_secret": False, "emotion_details": [{"type": "平穏", "strength": "medium"}]},
        {"created_at": "2026-05-12T06:00:00Z", "is_secret": False, "emotion_details": [{"type": "不安", "strength": "strong"}]},
    ]

    async def fake_fetch_emotion_rows(_user_id, _start_iso, _end_iso):
        return rows

    async def fake_upsert(payload):
        assert payload["report_type"] == "daily"
        assert payload["content_json"]["kokoroWeather"]["report_type"] == "daily"
        assert payload["content_json"]["kokoroWeather"]["version"] == "kokoro.weather.v1"
        assert payload["content_json"]["kokoroWeather"]["time_buckets"]
        return "report-1"

    monkeypatch.setattr(reports, "_fetch_emotion_rows", fake_fetch_emotion_rows)
    monkeypatch.setattr(reports, "_upsert_report", fake_upsert)
    monkeypatch.setattr(reports, "_fetch_latest_snapshot_hash", lambda *args, **kwargs: None)
    monkeypatch.setattr(reports, "_attach_analysis_report_validity_meta_if_available", lambda content_json, **kwargs: content_json)
    monkeypatch.setattr(reports, "attach_emlis_context_anchors", lambda content_json, _anchors: content_json)
    monkeypatch.setattr(reports, "build_emotion_report_emlis_context_anchors", lambda **kwargs: {})

    text, content_json, _astor_text, meta = await reports._generate_and_save("user-1", target, include_astor=False)

    assert text
    assert meta["status"] == "generated"
    assert content_json["kokoroWeather"]["report_type"] == "daily"


@pytest.mark.asyncio
async def test_detail_rejects_old_emotion_report_without_kokoro_weather(monkeypatch):
    class DummyViewContext:
        subscription_tier = "premium"

    old_row = {
        "id": "old-report",
        "report_type": "weekly",
        "period_start": "2026-05-04T15:00:00Z",
        "period_end": "2026-05-11T14:59:59Z",
        "title": "旧感情分析",
        "content_text": "旧本文",
        "content_json": {"standardReport": {"contentText": "旧感情分析本文"}},
    }

    async def fake_resolve_report_view_context(*_args, **_kwargs):
        return DummyViewContext()

    async def fake_fetch_full_rows_by_ids(*_args, **_kwargs):
        return [old_row]

    monkeypatch.setattr(reports, "resolve_report_view_context", fake_resolve_report_view_context)
    monkeypatch.setattr(reports, "_fetch_myweb_full_rows_by_ids", fake_fetch_full_rows_by_ids)
    monkeypatch.setattr(reports, "apply_myweb_report_access_for_viewer", lambda row, **_kwargs: row)

    with pytest.raises(HTTPException) as excinfo:
        await reports._build_myweb_detail_payload(user_id="user-1", report_id="old-report")

    assert excinfo.value.status_code == 404
    assert "Kokoro weather" in str(excinfo.value.detail)


def test_weekly_days_rejects_old_weekly_report_without_kokoro_weather(monkeypatch):
    app = FastAPI()
    reads.register_analysis_read_routes(app)
    client = TestClient(app)

    async def fake_require_user_id(_authorization):
        return "user-1"

    async def fake_resolve_viewer_tier(_user_id):
        return "premium"

    async def fake_fetch_report_row(_user_id, _report_id, *, tier_str):
        return {
            "id": "old-weekly",
            "report_type": "weekly",
            "period_start": "2026-05-04T15:00:00Z",
            "period_end": "2026-05-11T14:59:59Z",
            "content_json": {
                "days": [
                    {"dateKey": "2026-05-05", "label": "5/5", "calm": 3, "dominantKey": "calm"}
                ]
            },
        }

    monkeypatch.setattr(reads, "_require_user_id", fake_require_user_id)
    monkeypatch.setattr(reads, "_resolve_viewer_tier", fake_resolve_viewer_tier)
    monkeypatch.setattr(reads, "_fetch_myweb_report_row", fake_fetch_report_row)

    response = client.get(
        "/analysis/reports/old-weekly/weekly-days",
        headers={"Authorization": "Bearer test-token"},
    )

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_unread_status_uses_only_kokoro_weather_reports(monkeypatch):
    class FakeResponse:
        def __init__(self, payload):
            self.status_code = 200
            self._payload = payload
            self.text = ""

        def json(self):
            return self._payload

    async def fake_sb_get(path, *, params=None, timeout=8.0):
        assert path == "/rest/v1/analysis_reports"
        return FakeResponse(
            [
                {
                    "id": "old-weekly",
                    "report_type": "weekly",
                    "period_start": "2026-05-11T15:00:00Z",
                    "period_end": "2026-05-18T14:59:59Z",
                    "publish_status": "READY",
                    "metrics_total_all": "3",
                },
                {
                    "id": "kokoro-weekly",
                    "report_type": "weekly",
                    "period_start": "2026-05-04T15:00:00Z",
                    "period_end": "2026-05-11T14:59:59Z",
                    "publish_status": "READY",
                    "kokoro_weather_version": "kokoro.weather.v1",
                    "metrics_total_all": "3",
                },
            ]
        )

    monkeypatch.setattr(report_reads, "sb_get", fake_sb_get)

    ids = await report_reads._fetch_latest_ready_myweb_ids(
        "user-1",
        "weekly",
        tier_str="premium",
        limit=1,
    )

    assert ids == ["kokoro-weekly"]
