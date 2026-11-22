"""Input -> live read -> period projection; synthetic rows and authenticated API transport."""
from datetime import datetime, timedelta, timezone
from unittest.mock import AsyncMock

import httpx
import pytest
from fastapi import FastAPI, HTTPException

import api_analysis_reads as reads
import kokoro_weather_service as weather
from publish_governance import history_retention_window_utc

NOW = datetime.fromisoformat("2026-11-08T21:40:00+09:00")


def row(at, *emotions, secret=False, uid="owner", id="1"):
    return dict(id=id, user_id=uid, created_at=at, is_secret=secret,
                emotions=[key for key, _ in emotions],
                emotion_details=[dict(type=key, strength=level) for key, level in emotions])


def example_rows():
    return [
        row("2026-11-08T08:10:00+09:00", ("喜び", "medium"), ("不安", "weak")),
        row("2026-11-08T09:45:00+09:00", ("不安", "medium")),
        row("2026-11-08T12:30:00+09:00", ("怒り", "weak"), ("不安", "medium")),
        row("2026-11-08T15:20:00+09:00", ("平穏", "medium")),
        row("2026-11-08T18:40:00+09:00", ("喜び", "medium"), ("平穏", "strong")),
        row("2026-11-08T21:10:00+09:00", ("平穏", "medium")),
    ]


def build(rows, **kwargs):
    return weather.build_live_kokoro_weather_from_rows(rows, now_utc=NOW, **kwargs)


def test_actual_input_shape_counts_records_once_and_strength_weights_sum_to_100():
    rows = example_rows() + [
        row("2026-11-08T13:00:00+09:00", ("自己理解", "strong")),
        row("2026-11-08T13:00:00+09:00", ("喜び", "strong"), secret=True),
        row("invalid", ("喜び", "strong")),
        row("2026-11-08T22:00:00+09:00", ("喜び", "strong")),
        row("2026-11-07T23:59:59+09:00", ("喜び", "strong")),
    ]
    result = build(rows)
    summary = result["summary"]
    assert summary["input_count"] == 6
    assert summary["recorded_days"] == 1
    assert summary["emotion_weights"] == dict(joy=4, sadness=0, anger=1, anxiety=5, calm=7)
    assert summary["emotion_share_pct"] == dict(joy=24, sadness=0, anger=6, anxiety=29, calm=41)
    assert [x["input_count"] for x in result["time_buckets"]] == [0, 2, 2, 2]
    assert result["time_buckets"][0]["status"] == "no_observation"
    assert result["time_buckets"][1]["records"][0]["created_at"][11:16] == "08:10"
    assert "memo" not in str(result)


def test_today_bands_are_JST_and_future_slots_are_separate_from_missing():
    result = weather.build_live_kokoro_weather_from_rows([
        row("2026-11-07T14:59:59Z", ("喜び", "strong")),
        row("2026-11-07T15:00:00Z", ("平穏", "weak")),
        row("2026-11-07T21:00:00Z", ("不安", "strong")),
    ], now_utc=datetime.fromisoformat("2026-11-08T10:00:00+09:00"))
    assert result["summary"]["input_count"] == 2
    assert [x["status"] for x in result["time_buckets"]] == ["ok", "ok", "future", "future"]
    assert result["next_anchor"] is None


@pytest.mark.parametrize("period,anchor,start,end,size", [
    ("week", None, "2026-11-02", "2026-11-08", 7),
    ("month", None, "2026-11-01", "2026-11-08", 8),
    ("month", "2026-10-31", "2026-10-01", "2026-10-31", 31),
    ("month", "2024-02-20", "2024-02-01", "2024-02-29", 29),
    ("week", "2026-01-01", "2025-12-29", "2026-01-04", 7),
])
def test_calendar_ranges_and_month_days_are_not_four_week_buckets(period, anchor, start, end, size):
    result = build([], period=period, anchor=anchor)
    assert (result["start_date"], result["end_date"]) == (start, end)
    assert len(result["items"]) == size
    assert all(x["input_count"] == 0 and not any(x["emotion_weights"].values()) for x in result["items"])


def test_week_keeps_unrecorded_gap_and_never_imputes_calm_or_future():
    result = weather.build_live_kokoro_weather_from_rows([
        row("2026-11-02T12:00:00+09:00", ("喜び", "strong")),
        row("2026-11-04T12:00:00+09:00", ("不安", "strong")),
    ], period="week", now_utc=datetime.fromisoformat("2026-11-04T13:00:00+09:00"))
    assert result["summary"]["recorded_days"] == 2
    assert [x["status"] for x in result["items"]] == ["ok", "no_observation", "ok", "future", "future", "future", "future"]


def test_existing_history_retention_clamps_partial_period_and_navigation():
    cutoff = NOW - timedelta(days=365)
    result = build([
        row("2025-11-08T21:39:59+09:00", ("喜び", "strong")),
        row("2025-11-08T21:40:00+09:00", ("不安", "medium")),
    ], period="month", anchor="2025-11-01", history_start_utc=cutoff)
    assert result["partial_history"] is True
    assert result["summary"]["input_count"] == 1
    assert result["items"][0]["status"] == "outside_history"
    assert result["items"][7]["partial_history"] is True
    assert result["previous_anchor"] is None
    free = history_retention_window_utc("free", now_utc=NOW)
    with pytest.raises(PermissionError):
        build([], period="month", anchor="2026-09-01", history_start_utc=free["start_utc"])


@pytest.mark.asyncio
async def test_paginated_owner_only_read_handles_short_server_pages_and_more_than_1000(monkeypatch):
    source = [row(f"2026-11-08T12:00:00+09:00", ("喜び", "weak"), id=f"{i:06}") for i in range(1101)]
    calls = []
    async def get(path, *, params, timeout):
        calls.append(params)
        assert path == "/rest/v1/emotions" and params["user_id"] == "eq.owner"
        assert "memo" not in params["select"]
        if len(calls) > 1:
            cursor = min((len(calls) - 1) * 400, len(source)) - 1
            assert f"id.gt.{cursor:06}" in params["and"]
        index = (len(calls) - 1) * 400
        return httpx.Response(200, json=source[index:index+400])
    monkeypatch.setattr(weather, "sb_get", get)
    result = await weather.build_live_kokoro_weather("owner", now_utc=NOW)
    assert result["summary"]["input_count"] == 1101
    assert len(calls) == 4


@pytest.mark.asyncio
@pytest.mark.parametrize("bad", ["json", "status", "owner", "cursor"])
async def test_bad_or_failed_later_page_never_returns_partial_success(monkeypatch, bad):
    first = row("2026-11-08T12:00:00+09:00", ("平穏", "medium"))
    responses = [httpx.Response(200, json=[first])]
    responses.append({
        "json": httpx.Response(200, text="not-json"),
        "status": httpx.Response(503),
        "owner": httpx.Response(200, json=[dict(first, user_id="other")]),
        "cursor": httpx.Response(200, json=[first]),
    }[bad])
    monkeypatch.setattr(weather, "sb_get", AsyncMock(side_effect=responses))
    with pytest.raises(RuntimeError):
        await weather.build_live_kokoro_weather("owner", now_utc=NOW)


@pytest.mark.asyncio
async def test_authenticated_route_reuses_tier_bounds_and_rereads_new_save_or_deletion(monkeypatch):
    source, calls = [], []
    async def require(authorization):
        if authorization != "Bearer valid":
            raise HTTPException(status_code=401)
        return "owner"
    async def get(path, *, params, timeout):
        calls.append(params)
        return httpx.Response(200, json=[] if "id.gt." in params["and"] else source.copy())
    monkeypatch.setattr(reads, "_require_user_id", require)
    monkeypatch.setattr(reads, "_resolve_viewer_tier", AsyncMock(return_value="free"))
    monkeypatch.setattr(reads, "_now_utc", lambda: NOW)
    monkeypatch.setattr(weather, "sb_get", get)
    app = FastAPI()
    reads.register_analysis_read_routes(app)
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://synthetic") as client:
        assert (await client.get("/analysis/kokoro-weather")).status_code == 401
        async def get_weather(query=""):
            return await client.get("/analysis/kokoro-weather" + query, headers={"Authorization": "Bearer valid"})
        assert (await get_weather()).json()["summary"]["input_count"] == 0
        source.extend(example_rows())
        for period in ("today", "week", "month"):
            result = await get_weather(f"?period={period}&user_id=other")
            assert result.status_code == 200
            assert result.headers["cache-control"] == "private, no-store"
            assert result.json()["summary"]["input_count"] == 6
        source.clear()
        assert (await get_weather()).json()["summary"]["input_count"] == 0
        assert (await get_weather("?period=month&anchor=2026-09-01")).status_code == 403
        for query in ("?period=year", "?anchor=2026-11-09", "?anchor=2026-02-30", "?anchor=0001-01-01"):
            assert (await get_weather(query)).status_code == 422
        monkeypatch.setattr(weather, "sb_get", AsyncMock(return_value=httpx.Response(200, text="bad-json")))
        assert (await get_weather()).status_code == 503
    assert all(params["user_id"] == "eq.owner" for params in calls)
