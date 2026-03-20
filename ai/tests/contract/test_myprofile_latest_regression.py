from __future__ import annotations

import json

from astor_myprofile_report import MYPROFILE_REPORT_SCHEMA_VERSION
from subscription import SubscriptionTier


class _FakeResponse:
    def __init__(self, status_code: int, payload):
        self.status_code = status_code
        self._payload = payload
        self.text = json.dumps(payload, ensure_ascii=False)

    def json(self):
        return self._payload



def test_myprofile_latest_does_not_500_on_current_schema_row(client, monkeypatch):
    import api_myprofile as myprofile_module
    import subscription_store

    async def fake_resolve_user_id_from_token(_access_token: str) -> str:
        return "user-123"

    async def fake_get_subscription_tier_for_user(_user_id: str, *, default=SubscriptionTier.FREE):
        return SubscriptionTier.PLUS

    async def fake_fetch_latest_self_structure_analysis_row(_user_id: str, _stage: str):
        return {
            "source_hash": "analysis-hash-1",
            "updated_at": "2026-03-20T00:00:00Z",
            "created_at": "2026-03-20T00:00:00Z",
        }

    async def fake_sb_get(path: str, *, params=None):
        assert path == "/rest/v1/myprofile_reports"
        assert params is not None
        return _FakeResponse(
            200,
            [
                {
                    "id": "latest-row-1",
                    "title": "現在の自己構造",
                    "content_text": "現在の自己構造レポート本文",
                    "generated_at": "2026-03-20T00:00:02Z",
                    "period_start": "2026-02-21T00:00:00Z",
                    "period_end": "2026-03-20T00:00:00Z",
                    "content_json": {
                        "version": MYPROFILE_REPORT_SCHEMA_VERSION,
                        "report_mode": "standard",
                        "visibility": {"has_visible_content": True},
                        "analysis_refs": {
                            "self_structure": {
                                "standard": {"source_hash": "analysis-hash-1"}
                            }
                        },
                    },
                }
            ],
        )

    monkeypatch.setattr(myprofile_module, "_resolve_user_id_from_token", fake_resolve_user_id_from_token)
    monkeypatch.setattr(subscription_store, "get_subscription_tier_for_user", fake_get_subscription_tier_for_user)
    monkeypatch.setattr(
        myprofile_module,
        "_fetch_latest_self_structure_analysis_row",
        fake_fetch_latest_self_structure_analysis_row,
    )
    monkeypatch.setattr(myprofile_module, "_sb_get", fake_sb_get)

    response = client.get(
        "/myprofile/latest?ensure=true&report_mode=standard",
        headers={"Authorization": "Bearer test-token"},
    )

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["status"] == "ok"
    assert body["reason"] == "up_to_date"
    assert body["refreshed"] is False
    assert body["report_mode"] == "standard"
    assert body["content_text"] == "現在の自己構造レポート本文"
