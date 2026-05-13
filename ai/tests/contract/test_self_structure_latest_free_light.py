from __future__ import annotations

from typing import Any

import subscription as subscription_module
import subscription_store as subscription_store_module


class _FakeResponse:
    def __init__(self, status_code: int, payload: Any):
        self.status_code = status_code
        self._payload = payload
        self.text = ""

    def json(self) -> Any:
        return self._payload


async def _fake_resolve_user_id_from_token(_access_token: str) -> str:
    return "free-user-1"


async def _fake_tier_free(_user_id: str, *, default=subscription_module.SubscriptionTier.FREE):
    return subscription_module.SubscriptionTier.FREE


def _saved_standard_latest_row() -> dict[str, Any]:
    summary = "仕事の場面では、整える役割が立ち上がりやすく見えます。"
    return {
        "id": "latest-row-standard",
        "report_type": "latest",
        "title": "自己分析レポート（最新版）",
        "content_text": "【自己分析レポート】\n\n【最近のあなたに見えている役割】\n"
        + summary
        + "\n\n1. 役割内容\n詳しい役割本文です。",
        "generated_at": "2026-05-12T00:00:00Z",
        "period_start": "1970-01-01T00:00:00.000Z",
        "period_end": "1970-01-01T00:00:00.000Z",
        "content_json": {
            "engine": "astor_myprofile_report",
            "version": "myprofile.report.v5",
            "report_mode": "standard",
            "report_type": "latest",
            "distribution": {
                "period_start": "2026-04-14T00:00:00Z",
                "period_end": "2026-05-12T00:00:00Z",
            },
            "analysis_refs": {
                "self_structure": {
                    "standard": {"source_hash": "analysis-hash-free-light"},
                }
            },
            "summaryText": summary,
            "sections": {
                "current_structure": [summary],
                "role_content": ["詳しい役割本文です。"],
            },
            "standardReport": {"detail": "Freeには直接返さない詳細"},
            "visibility": {"has_visible_content": True},
            "history": {"history_fingerprint": "history-free-light-1", "skip_reason": None},
        },
    }


def test_self_structure_latest_free_returns_light_summary_from_saved_standard_row(client, monkeypatch):
    import api_self_structure as self_structure_module

    async def fake_fetch_latest_self_structure_analysis_row(_user_id: str, _stage: str):
        return {
            "source_hash": "analysis-hash-free-light",
            "updated_at": "2026-05-12T00:00:00Z",
            "created_at": "2026-05-12T00:00:00Z",
        }

    async def fake_sb_get(path: str, *, params=None):
        assert path == "/rest/v1/self_structure_reports"
        return _FakeResponse(200, [_saved_standard_latest_row()])

    monkeypatch.setattr(self_structure_module, "_resolve_user_id_from_token", _fake_resolve_user_id_from_token)
    monkeypatch.setattr(self_structure_module, "_fetch_latest_self_structure_analysis_row", fake_fetch_latest_self_structure_analysis_row)
    monkeypatch.setattr(self_structure_module, "_sb_get", fake_sb_get)
    monkeypatch.setattr(subscription_store_module, "get_subscription_tier_for_user", _fake_tier_free)

    response = client.get(
        "/self-structure/latest?ensure=false",
        headers={"Authorization": "Bearer test-token"},
    )

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["status"] == "ok"
    assert body["reason"] == "up_to_date"
    assert body["refreshed"] is False
    assert body["report_mode"] == "light"
    assert body["title"] == "今のわたしマップ"
    assert "仕事の場面では" in body["content_text"]
    assert "詳しい自己分析レポートは Plus プラン以上" in body["content_text"]
    assert "詳しい役割本文です" not in body["content_text"]

    meta = body["meta"]
    assert meta["report_mode"] == "light"
    assert meta["visibility"]["viewer_tier"] == "free"
    assert meta["visibility"]["summary_visible"] is True
    assert meta["visibility"]["detail_report_visible"] is False
    assert "standardReport" not in meta
    assert meta["watashiMap"]["report_mode"] == "light"
    assert meta["watashiMap"]["visibility"]["viewer_tier"] == "free"
    assert meta["watashiMap"]["detail_report"]["visible"] is False
    assert meta["watashiMap"]["routes"] == []
    assert meta["sections"] == {
        "current_structure": ["仕事の場面では、整える役割が立ち上がりやすく見えます。"]
    }
    assert meta["watashiMap"]["version"] == "watashi.map.v1"
    assert meta["watashiMap"]["report_mode"] == "light"
    assert meta["watashiMap"]["visibility"]["viewer_tier"] == "free"
    assert meta["watashiMap"]["visibility"]["detail_report_visible"] is False
    assert meta["watashiMap"]["detail_report"]["lock_label"] == "詳しい自己分析レポートは Plus プラン以上で読めます。"

    watashi_map = meta["watashiMap"]
    assert watashi_map["version"] == "watashi.map.v1"
    assert watashi_map["label"] == "わたしマップ"
    assert watashi_map["report_mode"] == "light"
    assert watashi_map["visibility"]["viewer_tier"] == "free"
    assert watashi_map["visibility"]["summary_visible"] is True
    assert watashi_map["visibility"]["detail_report_visible"] is False
    assert watashi_map["routes"] == []
    assert watashi_map["crossroads"] == []
    assert "仕事の場面では" in watashi_map["overview"]["summary"]
