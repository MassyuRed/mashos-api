"""Verify retirement at the old report entry points and keep the live graph reachable."""

import asyncio
from datetime import datetime, timezone

from fastapi import FastAPI
from fastapi.testclient import TestClient
import pytest

import api_analysis_reads as reads
import api_analysis_reports as reports
import api_cron_distribution as cron
from subscription_bootstrap_store import _merge_plan_catalog


@pytest.fixture
def client(monkeypatch):
    async def resolve_user(token):
        return "test-owner" if token == "owner" else None

    async def no_report_work(*args, **kwargs):
        pytest.fail("a retired report entry point attempted generation or selected users")

    monkeypatch.setattr(reports, "_resolve_user_id_from_token", resolve_user)
    monkeypatch.setattr(reports, "_generate_and_save_from_snapshot", no_report_work)
    monkeypatch.setattr(cron, "_fetch_user_ids_from_profiles", no_report_work)
    monkeypatch.setattr(cron, "CRON_TOKEN_VALUES", {"cron"})
    app = FastAPI()
    reports.register_analysis_report_routes(app)
    reads.register_analysis_read_routes(app)
    cron.register_cron_distribution_routes(app)
    return TestClient(app)


@pytest.mark.parametrize("period", ["daily", "weekly", "monthly"])
def test_on_demand_report_generation_is_retired(client, period):
    route = "/analysis/reports/ensure"
    body = {"types": [period], "force": True}
    assert client.post(route, json=body).status_code == 401

    response = client.post(route, headers={"Authorization": "Bearer owner"}, json=body)
    assert response.status_code == 410
    assert response.json()["detail"] == "kokoro_graph_reports_retired"


@pytest.mark.parametrize("period", ["daily", "weekly", "monthly"])
def test_legacy_cron_finishes_without_generating_reports(client, period):
    route = f"/cron/myweb/{period}"
    assert client.post(route, json={}).status_code == 401

    response = client.post(route, headers={"Authorization": "Bearer cron"}, json={"force": True})
    result = response.json()
    assert response.status_code == 200
    assert result["job"] == f"myweb_{period}"
    assert result["status"] == "retired"
    assert result["processed"] == result["generated"] == result["errors"] == 0
    assert result["done"] and result["next_offset"] is None


@pytest.mark.parametrize("period", ["today", "week", "month"])
def test_free_can_read_all_live_graph_periods(client, monkeypatch, period):
    async def require_user(authorization):
        assert authorization == "Bearer owner"
        return "test-owner"

    async def viewer_tier(user_id):
        assert user_id == "test-owner"
        return "free"

    async def live_graph(user_id, *, period, anchor, now_utc, history_start_utc):
        assert user_id == "test-owner"
        assert history_start_utc is not None
        return {"period": period}

    monkeypatch.setattr(reads, "_require_user_id", require_user)
    monkeypatch.setattr(reads, "_resolve_viewer_tier", viewer_tier)
    monkeypatch.setattr(reads, "_now_utc", lambda: datetime(2026, 11, 21, tzinfo=timezone.utc))
    monkeypatch.setattr(reads, "build_live_kokoro_weather", live_graph)
    response = client.get(
        "/analysis/kokoro-weather", params={"period": period}, headers={"Authorization": "Bearer owner"}
    )
    assert response.status_code == 200
    assert response.json() == {"period": period}
    assert response.headers["Cache-Control"] == "private, no-store"


def test_pending_graph_report_pushes_are_suppressed(monkeypatch):
    class CandidateStore:
        async def list_pending_candidates(self, *, limit):
            return [
                {
                    "user_id": "test-owner",
                    "distribution_key": "2026-11-21",
                    "report_family": f"emotion_{period}",
                }
                for period in ("daily", "weekly", "monthly")
            ]

        async def mark_bundle_delivered(self, **kwargs):
            assert kwargs["bundle_families"] == []
            assert kwargs["payload"]["send_status"] == "suppressed_policy"

    async def unexpected_push(*args, **kwargs):
        pytest.fail("attempted to send a retired report push")

    monkeypatch.setattr(cron, "ReportDistributionPushStore", CandidateStore)
    monkeypatch.setattr(cron, "ReportDistributionSettingsStore", None)
    monkeypatch.setattr(cron, "_send_report_distribution_bundle_push", unexpected_push)
    result = asyncio.run(cron.run_report_distribution_push_once(body=cron.ReportDistributionPushBatchRequest()))
    assert result.sent == result.errors == 0
    assert result.skipped == 1


def test_subscription_catalog_does_not_advertise_retired_reports():
    catalog = _merge_plan_catalog([
        {"plan_code": tier, "features_json": ["こころグラフ（日/週/月）の本文"]}
        for tier in ("plus", "premium")
    ])
    for tier in ("plus", "premium"):
        assert all("こころグラフ" not in feature for feature in catalog[tier]["features"])
        assert any("わたしマップ" in feature for feature in catalog[tier]["features"])
