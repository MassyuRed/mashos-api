from __future__ import annotations

from types import SimpleNamespace
from typing import Any

import emlis_ai_limited_composer_client as limited_client


def _response(comment_text: str = "before repair") -> dict[str, Any]:
    return {
        "schema_version": "emlis.composer.response.v1",
        "composer_source": "ai_generated",
        "status": "generated",
        "comment_text": comment_text,
        "used_evidence_span_ids": [],
        "composer_model": "cocolon_emlis_observation_composer.limited.v1",
        "composer_meta": {"limited_reader_repair": {"attempted": True}},
    }


def _payload() -> dict[str, Any]:
    return {
        "schema_version": "emlis.composer.request.v1",
        "composition_contract": {"previous_rejection_reasons": ["relation_not_expressed"]},
    }


class _PassedEvaluation:
    passed = True
    result = SimpleNamespace(status="passed")

    def as_meta(self) -> dict[str, Any]:
        return {"adapter_name": "test_core", "passed": True}


class _RejectedEvaluation:
    passed = False
    result = SimpleNamespace(status="rejected")

    def as_meta(self) -> dict[str, Any]:
        return {"adapter_name": "test_core", "passed": False}


def test_core_checked_response_runs_limited_reader_repair_before_core_evaluation(monkeypatch) -> None:
    calls: list[str] = []

    def fake_repair(**kwargs: Any) -> dict[str, Any]:
        calls.append("repair")
        assert kwargs["coverage_scope"] == "partial_observation"
        assert kwargs["profile_key"] == "mixed_positive_anxiety"
        repaired = dict(kwargs["response"])
        repaired["comment_text"] = "after repair"
        repaired["composer_meta"] = {
            **dict(repaired.get("composer_meta") or {}),
            "limited_reader_repair": {"attempted": True, "applied": True},
        }
        return repaired

    def fake_evaluate(**kwargs: Any) -> _PassedEvaluation:
        calls.append("evaluate")
        assert calls == ["repair", "evaluate"]
        assert kwargs["comment_text"] == "after repair"
        assert dict(kwargs["response"])["comment_text"] == "after repair"
        assert dict(kwargs["composer_meta"])["limited_reader_repair"]["applied"] is True
        return _PassedEvaluation()

    monkeypatch.setattr(limited_client, "_apply_limited_reader_repair_if_needed", fake_repair)
    monkeypatch.setattr(limited_client, "evaluate_emlis_observation_candidate", fake_evaluate)

    out = limited_client._core_checked_response(
        response=_response(),
        payload=_payload(),
        evidence_items=[],
        phrase_units=[],
        sentence_plans=[],
        used_unit_ids=[],
        coverage_scope="partial_observation",
        profile_key="mixed_positive_anxiety",
    )

    assert calls == ["repair", "evaluate"]
    assert out["comment_text"] == "after repair"
    assert out["composer_meta"]["text_generation_core"]["passed"] is True


def test_core_checked_response_keeps_fail_closed_after_repair_when_core_rejects(monkeypatch) -> None:
    calls: list[str] = []

    def fake_repair(**kwargs: Any) -> dict[str, Any]:
        calls.append("repair")
        repaired = dict(kwargs["response"])
        repaired["comment_text"] = "after repair"
        return repaired

    def fake_evaluate(**kwargs: Any) -> _RejectedEvaluation:
        calls.append("evaluate")
        assert kwargs["comment_text"] == "after repair"
        return _RejectedEvaluation()

    monkeypatch.setattr(limited_client, "_apply_limited_reader_repair_if_needed", fake_repair)
    monkeypatch.setattr(limited_client, "evaluate_emlis_observation_candidate", fake_evaluate)

    out = limited_client._core_checked_response(
        response=_response(),
        payload=_payload(),
        evidence_items=[],
        phrase_units=[],
        sentence_plans=[],
        used_unit_ids=[],
        coverage_scope="current_input_core",
        profile_key="current_input_core",
    )

    assert calls == ["repair", "evaluate"]
    assert out["status"] == "unavailable"
    assert out["comment_text"] == ""
    assert "emlis_observation_core_rejected" in out["rejection_reasons"]
    assert out["composer_meta"]["text_generation_core"]["passed"] is False
