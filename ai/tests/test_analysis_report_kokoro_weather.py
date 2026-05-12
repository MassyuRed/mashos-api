from __future__ import annotations

from datetime import datetime, timezone

import pytest

import api_analysis_reports as reports
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
