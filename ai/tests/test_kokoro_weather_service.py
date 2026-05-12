from __future__ import annotations

from datetime import datetime, timezone

from kokoro_weather_service import (
    build_current_kokoro_weather_from_rows,
    build_no_observation_current_weather,
    with_previous_available,
)


def test_current_kokoro_weather_no_observation_payload_is_past_observation_wording():
    now = datetime(2026, 5, 12, 5, 0, tzinfo=timezone.utc)

    payload = build_current_kokoro_weather_from_rows([], end_utc=now, previous_available=True)

    assert payload["status"] == "no_observation"
    assert payload["label"] == "今のこころ天気"
    assert payload["empty_title"] == "今日はまだ観測がありません"
    assert payload["empty_action_label"] == "前回のこころ天気を見る"
    assert payload["previous_available"] is True


def test_current_kokoro_weather_builds_temperature_and_dominant_emotion_without_good_bad_judgment():
    now = datetime(2026, 5, 12, 12, 0, tzinfo=timezone.utc)
    rows = [
        {"created_at": "2026-05-12T00:30:00Z", "emotion_details": [{"type": "平穏", "strength": "medium"}]},
        {"created_at": "2026-05-12T02:30:00Z", "emotion_details": [{"type": "不安", "strength": "medium"}]},
        {"created_at": "2026-05-12T04:30:00Z", "emotion_details": [{"type": "平穏", "strength": "strong"}]},
    ]

    payload = build_current_kokoro_weather_from_rows(rows, end_utc=now)

    assert payload["status"] == "ok"
    assert payload["period_mode"] == "today_jst"
    assert payload["temperature"]["unit"] == "kokoro_degree"
    assert payload["temperature"]["display"].endswith("°")
    assert payload["dominant_emotion"]["key"] == "calm"
    assert payload["dominant_emotion"]["label"] == "平穏"
    assert payload["weather"]["key"] in {"clear", "partly_cloudy", "cloudy", "soft_rain", "windy", "mixed", "unknown"}


def test_observation_memo_uses_movement_structure_not_specific_emotion_value():
    now = datetime(2026, 5, 12, 14, 0, tzinfo=timezone.utc)
    rows = [
        {"created_at": "2026-05-12T00:00:00Z", "emotion_details": [{"type": "喜び", "strength": "weak"}]},
        {"created_at": "2026-05-12T02:00:00Z", "emotion_details": [{"type": "不安", "strength": "strong"}]},
        {"created_at": "2026-05-12T04:00:00Z", "emotion_details": [{"type": "平穏", "strength": "weak"}]},
        {"created_at": "2026-05-12T06:00:00Z", "emotion_details": [{"type": "怒り", "strength": "strong"}]},
    ]

    payload = build_current_kokoro_weather_from_rows(rows, end_utc=now)

    assert payload["observation_memo"]["visible"] is True
    assert payload["observation_memo"]["label"] == "観測メモあり"
    assert payload["observation_memo"]["reasons"]


def test_with_previous_available_only_updates_no_observation_payload():
    no_observation = build_no_observation_current_weather(previous_available=False)
    ok_payload = {"status": "ok", "previous_available": False}

    assert with_previous_available(no_observation, True)["previous_available"] is True
    assert with_previous_available(ok_payload, True)["previous_available"] is False
