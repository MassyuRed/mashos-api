from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

from kokoro_weather_service import (
    build_current_kokoro_weather_from_rows,
    build_report_kokoro_weather,
)
from publish_governance import history_retention_window_utc


FORBIDDEN_JUDGMENT_OR_FUTURE_WARNING_WORDS = (
    "注意報",
    "警報",
    "予報",
    "良い感情",
    "悪い感情",
)


def _walk_strings(value: Any):
    if isinstance(value, str):
        yield value
        return
    if isinstance(value, dict):
        for item in value.values():
            yield from _walk_strings(item)
        return
    if isinstance(value, (list, tuple, set)):
        for item in value:
            yield from _walk_strings(item)


def _assert_no_warning_or_judgment_words(payload: Any) -> None:
    joined = "\n".join(_walk_strings(payload))
    for word in FORBIDDEN_JUDGMENT_OR_FUTURE_WARNING_WORDS:
        assert word not in joined


def test_phase6_current_weather_copy_stays_observation_not_future_warning_or_judgment():
    now = datetime(2026, 5, 12, 12, 0, tzinfo=timezone.utc)
    rows = [
        {"created_at": "2026-05-12T00:00:00Z", "emotion_details": [{"type": "喜び", "strength": "weak"}]},
        {"created_at": "2026-05-12T02:00:00Z", "emotion_details": [{"type": "不安", "strength": "strong"}]},
        {"created_at": "2026-05-12T04:00:00Z", "emotion_details": [{"type": "平穏", "strength": "weak"}]},
        {"created_at": "2026-05-12T06:00:00Z", "emotion_details": [{"type": "怒り", "strength": "strong"}]},
    ]

    payload = build_current_kokoro_weather_from_rows(rows, end_utc=now)

    assert payload["status"] == "ok"
    assert payload["temperature"]["display"].endswith("°")
    assert payload["temperature"]["unit"] == "kokoro_degree"
    assert payload["observation_memo"]["label"] in ("", "観測メモあり")
    _assert_no_warning_or_judgment_words(payload)


def test_phase6_report_kokoro_weather_keeps_internal_type_and_old_data_fail_closed():
    start = datetime(2026, 5, 1, 0, 0, tzinfo=timezone.utc)
    end = start + timedelta(days=7)

    no_observation = build_report_kokoro_weather(
        report_type="weekly",
        rows=[],
        period_start_utc=start,
        period_end_utc=end,
        existing_metrics={},
    )
    assert no_observation["report_type"] == "weekly"
    assert no_observation["status"] == "no_observation"
    assert no_observation["items"]
    _assert_no_warning_or_judgment_words(no_observation)

    with_old_snapshot_days = build_report_kokoro_weather(
        report_type="weekly",
        rows=[],
        period_start_utc=start,
        period_end_utc=end,
        existing_metrics={"totals": {"calm": 4, "anxiety": 2}, "totalAll": 6},
        existing_days=[
            {"dateKey": "2026-05-01", "label": "5/1", "calm": 3, "anxiety": 1, "dominantKey": "calm"},
        ],
    )
    assert with_old_snapshot_days["report_type"] == "weekly"
    assert with_old_snapshot_days["status"] == "ok"
    assert with_old_snapshot_days["items"][0]["temperature_display"].endswith("°")
    _assert_no_warning_or_judgment_words(with_old_snapshot_days)


def test_phase6_access_retention_policy_is_unchanged_for_free_plus_premium():
    now = datetime(2026, 5, 12, 12, 0, tzinfo=timezone.utc)

    free_window = history_retention_window_utc("free", now_utc=now)
    plus_window = history_retention_window_utc("plus", now_utc=now)
    premium_window = history_retention_window_utc("premium", now_utc=now)

    assert free_window["mode"] == "current_and_previous_month_jst"
    assert free_window["start_utc"] is not None
    assert free_window["end_utc_exclusive"] is not None

    assert plus_window["mode"] == "rolling_365d"
    assert plus_window["start_utc"] is not None
    assert plus_window["end_utc_exclusive"] is not None

    assert premium_window["mode"] == "unlimited"
    assert premium_window["start_utc"] is None
    assert premium_window["end_utc_exclusive"] is None
