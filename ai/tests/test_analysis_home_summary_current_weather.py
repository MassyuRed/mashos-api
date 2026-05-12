from __future__ import annotations

import pytest

import api_analysis_reads as reads


@pytest.mark.asyncio
async def test_home_summary_adds_current_weather_without_removing_existing_fields(monkeypatch):
    async def fake_get_or_compute(_key, _ttl, builder):
        return await builder()

    async def fake_summary(_uid):
        return {"weekly": {"count": 2, "top": [["平穏", 2]]}, "monthly": {"count": 5}}

    async def fake_input_status(_uid):
        return {
            "today_count": 0,
            "week_count": 2,
            "month_count": 5,
            "last_input_at": "2026-05-11T10:00:00Z",
        }

    async def fake_current_weather(_uid):
        return {
            "status": "no_observation",
            "period_mode": "today_jst",
            "label": "今のこころ天気",
            "empty_title": "今日はまだ観測がありません",
            "empty_action_label": "前回のこころ天気を見る",
            "previous_available": False,
        }

    monkeypatch.setattr(reads, "get_or_compute", fake_get_or_compute)
    monkeypatch.setattr(reads, "get_myweb_home_summary_from_artifacts", fake_summary)
    monkeypatch.setattr(reads, "get_input_summary_snapshot", fake_input_status)
    monkeypatch.setattr(reads, "build_current_kokoro_weather", fake_current_weather)

    payload = await reads.get_myweb_home_summary_payload_for_user("user-1")

    assert payload["weekly"]["count"] == 2
    assert payload["monthly"]["count"] == 5
    assert payload["input_status"]["today_count"] == 0
    assert payload["current_weather"]["status"] == "no_observation"
    assert payload["current_weather"]["previous_available"] is True
