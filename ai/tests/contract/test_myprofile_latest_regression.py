from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import subscription as subscription_module
import subscription_store as subscription_store_module


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


def _saved_latest_row() -> dict[str, Any]:
    return {
        "id": "latest-row-1",
        "title": "自己構造レポート（最新版）",
        "content_text": "現在の自己構造です。",
        "generated_at": "2026-03-20T00:00:00Z",
        "period_start": "2026-02-21T00:00:00Z",
        "period_end": "2026-03-20T00:00:00Z",
        "content_json": {
            "version": "myprofile.report.v4",
            "report_mode": "standard",
            "visibility": {"has_visible_content": True},
            "history": {
                "history_fingerprint": "self-structure-version-key-1",
                "skip_reason": None,
            },
            "distribution": {
                "period_start": "2026-02-21T00:00:00Z",
                "period_end": "2026-03-20T00:00:00Z",
            },
            "analysis_refs": {
                "self_structure": {
                    "standard": {"source_hash": "analysis-hash-1"}
                }
            },
        },
    }


async def _fake_resolve_user_id_from_token(_access_token: str) -> str:
    return "user-123"


async def _fake_get_subscription_tier_for_user(_user_id: str, *, default=subscription_module.SubscriptionTier.FREE):
    return subscription_module.SubscriptionTier.PLUS


def test_myprofile_latest_current_schema_row_does_not_500(client, monkeypatch):
    import api_myprofile as myprofile_module

    async def fake_fetch_latest_self_structure_analysis_row(_user_id: str, _stage: str):
        return {
            "source_hash": "analysis-hash-1",
            "updated_at": "2026-03-20T00:00:00Z",
            "created_at": "2026-03-20T00:00:00Z",
        }

    async def fake_sb_get(path: str, *, params=None):
        assert path == "/rest/v1/myprofile_reports"
        return _FakeResponse(200, [_saved_latest_row()])

    monkeypatch.setattr(myprofile_module, "_resolve_user_id_from_token", _fake_resolve_user_id_from_token)
    monkeypatch.setattr(myprofile_module, "_fetch_latest_self_structure_analysis_row", fake_fetch_latest_self_structure_analysis_row)
    monkeypatch.setattr(myprofile_module, "_sb_get", fake_sb_get)
    monkeypatch.setattr(
        subscription_store_module,
        "get_subscription_tier_for_user",
        _fake_get_subscription_tier_for_user,
    )

    response = client.get(
        "/myprofile/latest?ensure=false&report_mode=standard",
        headers={"Authorization": "Bearer test-token"},
    )

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["status"] == "ok"
    assert body["reason"] == "up_to_date"
    assert body["refreshed"] is False
    assert body["report_mode"] == "standard"
    assert body["content_text"] == "現在の自己構造です。"
    assert body["meta"]["version"] == "myprofile.report.v4"
    assert body["has_visible_content"] is True
    assert body["period_start"] == "2026-02-21T00:00:00Z"
    assert body["period_end"] == "2026-03-20T00:00:00Z"


def test_myprofile_latest_status_matches_fixture_shape(client, monkeypatch):
    import api_myprofile as myprofile_module

    expected_shape = _load_fixture("myprofile_latest_status_response_shape_v1.json")

    async def fake_sb_get(path: str, *, params=None):
        assert path == "/rest/v1/myprofile_reports"
        return _FakeResponse(200, [_saved_latest_row()])

    monkeypatch.setattr(myprofile_module, "_resolve_user_id_from_token", _fake_resolve_user_id_from_token)
    monkeypatch.setattr(myprofile_module, "_sb_get", fake_sb_get)

    response = client.get(
        "/myprofile/latest/status",
        headers={"Authorization": "Bearer test-token"},
    )

    assert response.status_code == 200, response.text
    body = response.json()
    _assert_shape_subset(expected_shape, body)
    assert body["version_key"] == "self-structure-version-key-1"
    assert body["saved_report_mode"] == "standard"
    assert body["has_visible_content"] is True
    assert body["skip_reason"] is None
