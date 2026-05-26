from __future__ import annotations

import json
from typing import Any, Mapping

import pytest

from emlis_ai_complete_composer_initial_meta import COMPLETE_COMPOSER_INITIAL_MODEL
from emlis_ai_complete_composer_types import COMPLETE_COMPOSER_GENERATION_METHOD
from emlis_ai_relation_surface_contract import RELATION_SURFACE_CONTRACT_VERSION

_POSITIVE_RECOVERY_MEMO = (
    "疲れが残っていたけれど、少し戻ってくる感覚もある。"
    "重さが全部消えたわけではないけれど、整え直したい気持ちがある。"
)
_RELATION_MISSING_TEXT = "\n".join(
    [
        "Emlisです。",
        "小さな回復が少し戻ってきています。",
        "中心にある感覚として形を取り直しています。",
        "締めでは、静かにあります。",
    ]
)
_RELATION_REPAIRED_TEXT = "\n".join(
    [
        "Emlisです。",
        "今回の入力では、疲れのあとにも、小さな回復が少し戻ってきています。",
        "戻ってくる動きとその前の重さが同じ流れの中でつながっています。",
    ]
)
_RELATION_REPAIRED_PUBLIC_TEXT = "\n".join(
    [
        "Emlisです。",
        "今回の入力では、疲れのあとにも、小さな回復が少し戻ってきています。",
        "戻ってくる動きとその前の重さが同じ流れの中でつながっています。",
    ]
)
_FORBIDDEN_RAW_KEYS = {
    "raw_text",
    "raw_input",
    "input_text",
    "user_input",
    "current_input",
    "memo_text",
    "raw_user_text",
    "original_text",
    "source_text",
}


def _clear_flags(monkeypatch: pytest.MonkeyPatch) -> None:
    for name in (
        "COCOLON_EMLIS_LIMITED_COMPOSER_ENABLED",
        "COCOLON_EMLIS_AI_LIMITED_COMPOSER_ENABLED",
        "EMLIS_AI_LIMITED_COMPOSER_ENABLED",
        "COCOLON_LIMITED_COMPOSER_ENABLED",
        "COCOLON_EMLIS_AI_DEFAULT_LIMITED_COMPOSER_ENABLED",
        "EMLIS_AI_DEFAULT_LIMITED_COMPOSER_ENABLED",
        "COCOLON_EMLIS_DEFAULT_COMPOSER",
        "COCOLON_EMLIS_AI_DEFAULT_COMPOSER",
        "EMLIS_AI_DEFAULT_COMPOSER",
        "COCOLON_EMLIS_LIMITED_COMPOSER_ROLLOUT_STAGE",
        "COCOLON_EMLIS_AI_LIMITED_COMPOSER_ROLLOUT_STAGE",
        "EMLIS_AI_LIMITED_COMPOSER_ROLLOUT_STAGE",
        "COCOLON_EMLIS_LIMITED_COMPOSER_ROLLOUT",
        "EMLIS_AI_LIMITED_COMPOSER_ROLLOUT",
    ):
        monkeypatch.delenv(name, raising=False)


def _contains_forbidden_raw_key(value: Any) -> bool:
    if isinstance(value, Mapping):
        return any(str(key) in _FORBIDDEN_RAW_KEYS or _contains_forbidden_raw_key(item) for key, item in value.items())
    if isinstance(value, (list, tuple, set)):
        return any(_contains_forbidden_raw_key(item) for item in value)
    return False


def _positive_recovery_input(input_id: str) -> dict[str, object]:
    return {
        "id": input_id,
        "created_at": "2026-05-16T00:00:00Z",
        "memo": _POSITIVE_RECOVERY_MEMO,
        "memo_action": "",
        "emotion_details": [{"type": "自己理解", "strength": "medium"}],
        "emotions": ["自己理解"],
        "category": ["生活"],
    }


def _first_evidence_span_id(payload: Mapping[str, Any]) -> str:
    spans = payload.get("evidence_spans") or []
    if isinstance(spans, list) and spans and isinstance(spans[0], Mapping):
        return str(spans[0].get("span_id") or "span-positive-recovery")
    return "span-positive-recovery"


def _body_lines(text: str) -> list[str]:
    return [line for line in str(text or "").splitlines() if line.strip() and "Emlisです" not in line]


def _sentence_bindings(text: str, span_id: str) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for index, line in enumerate(_body_lines(text), start=1):
        rows.append(
            {
                "sentence_id": f"positive-recovery-s{index}",
                "text": line,
                "line_role": "relation" if "つなが" in line else "core",
                "relation_type": "recovery" if "つなが" in line else "context",
                "used_evidence_span_ids": [span_id],
                "used_phrase_unit_ids": [f"pu-positive-recovery-{index}"],
                "phrase_unit_roles": ["recovery_load_bridge" if "つなが" in line else "small_recovery"],
                "phrase_unit_polarities": ["positive_recovery"],
                "material_quality_flags": ["bodyable"],
            }
        )
    return rows


def _candidate_payload(*, text: str, payload: Mapping[str, Any], repaired: bool) -> dict[str, Any]:
    span_id = _first_evidence_span_id(payload)
    bindings = _sentence_bindings(text, span_id)
    relation_signal_keys = ["recovery_load_bridge"] if repaired else []
    relation_marker_key = "recovery_load_bridge_v1" if repaired else ""
    relation_surface_report = {
        "relation_surface_contract_version": RELATION_SURFACE_CONTRACT_VERSION,
        "surface_recovery_relation_line_aligned": repaired,
        "surface_relation_marker_key": relation_marker_key,
        "surface_relation_marker_keys": [relation_marker_key] if relation_marker_key else [],
        "expected_relation_types": ["recovery"],
        "reader_relation_signal_detected": repaired,
        "reader_relation_signal_count": len(relation_signal_keys),
        "reader_relation_signal_keys": relation_signal_keys,
        "reader_relation_signal_relation_types": ["recovery"] if repaired else [],
        "raw_input_included": False,
    }
    self_repair = {
        "self_repair_relation_marker_applied": repaired,
        "self_repair_relation_marker_key": relation_marker_key,
        "self_repair_relation_marker_keys": [relation_marker_key] if relation_marker_key else [],
        "self_repair_relation_marker_count": 1 if repaired else 0,
        "self_repair_relation_marker_signal_detected": repaired,
        "self_repair_relation_marker_signal_count": len(relation_signal_keys),
        "self_repair_relation_marker_signal_keys": relation_signal_keys,
        "self_repair_relation_marker_signal_relation_types": ["recovery"] if repaired else [],
        "self_repair_relation_marker_meaning_added": False,
        "self_repair_relation_marker_gate_relaxed": False,
        "meaning_added": False,
        "gate_relaxed": False,
        "raw_input_included": False,
    }
    repair_trace_v2 = []
    if repaired:
        repair_trace_v2.append(
            {
                "attempt": 1,
                "source_gate": "reader",
                "reason_code": "relation_not_expressed",
                "operation": "make_declared_relation_surface_explicit",
                "meaning_added": False,
                "relation_ids_preserved": True,
                "gate_relaxed": False,
                "self_repair_relation_marker_applied": True,
                "self_repair_relation_marker_key": relation_marker_key,
                "self_repair_relation_marker_signal_keys": relation_signal_keys,
                "raw_input_included": False,
            }
        )
    return {
        "schema_version": "emlis.complete_composer.response.v1",
        "response_schema_version": "emlis.complete_composer.response.v1",
        "composer_source": "ai_generated",
        "composer_model": COMPLETE_COMPOSER_INITIAL_MODEL,
        "generation_method": COMPLETE_COMPOSER_GENERATION_METHOD,
        "generation_scope": "scoped_graph_evidence_composer",
        "coverage_scope": "positive_recovery",
        "comment_text": text,
        "used_evidence_span_ids": [span_id],
        "used_claim_ids": ["claim-positive-recovery"],
        "used_relation_ids": ["recovery"],
        "confidence": 0.91,
        "fixed_string_renderer_used": False,
        "composer_meta": {
            "complete_composer_client_added": True,
            "complete_composer_initial": True,
            "complete_binding_aware_grounding": True,
            "complete_sentence_plan_v2": True,
            "product_quality_grounding": True,
            "coverage_group": "positive_recovery",
            "coverage_scope": "positive_recovery",
            "relation_types": ["recovery"],
            "used_evidence_span_ids": [span_id],
            "used_phrase_unit_ids": [row["used_phrase_unit_ids"][0] for row in bindings],
            "used_relation_ids": ["recovery"],
            "sentence_bindings": bindings,
            "grounding_input": {
                "version": "emlis.complete_binding_aware_grounding.v1",
                "complete_binding_aware_grounding": True,
                "product_quality_grounding": True,
                "binding_required": True,
                "binding_count": len(bindings),
                "expected_binding_count": len(bindings),
                "sentence_bindings": bindings,
                "used_evidence_span_ids": [span_id],
                "relation_surface_contract_version": RELATION_SURFACE_CONTRACT_VERSION,
                "raw_input_included": False,
            },
            "relation_surface_contract_version": RELATION_SURFACE_CONTRACT_VERSION,
            "surface_realizer": {
                "relation_surface_contract_version": RELATION_SURFACE_CONTRACT_VERSION,
                "relation_surface_report": relation_surface_report,
                "raw_input_included": False,
            },
            "surface_signature": relation_surface_report,
            "self_repair": self_repair,
            "self_repair_report_v2": self_repair,
            "repair_trace": repair_trace_v2,
            "repair_trace_v2": repair_trace_v2,
            "external_ai_used": False,
            "local_llm_used": False,
            "fixed_sentence_template_used": False,
            "fallback_observation_sentence_added": False,
            "raw_input_included": False,
        },
    }


class _PositiveRecoveryRepairComposer:
    composer_model = COMPLETE_COMPOSER_INITIAL_MODEL

    def __init__(self, *, never_repair: bool = False) -> None:
        self.never_repair = never_repair
        self.payloads: list[Mapping[str, Any]] = []

    def generate(self, payload: Mapping[str, Any]) -> dict[str, Any]:
        self.payloads.append(dict(payload))
        previous_reasons = list((payload.get("composition_contract") or {}).get("previous_rejection_reasons") or [])
        repaired = bool("relation_not_expressed" in previous_reasons and not self.never_repair)
        return _candidate_payload(
            text=_RELATION_REPAIRED_TEXT if repaired else _RELATION_MISSING_TEXT,
            payload=payload,
            repaired=repaired,
        )


def _previous_rejection_reasons(call: Mapping[str, Any]) -> list[str]:
    return list((call.get("composition_contract") or {}).get("previous_rejection_reasons") or [])


def _reader_gate(diagnostic: Mapping[str, Any]) -> Mapping[str, Any]:
    return dict((diagnostic.get("gate_results") or {}).get("reader") or {})


def _display_gate(reply_meta: Mapping[str, Any]) -> Mapping[str, Any]:
    return dict(((reply_meta.get("multi_perspective") or {}).get("gate_trace") or {}).get("display_gate") or {})


@pytest.mark.asyncio
async def test_step6_positive_recovery_e2e_repairs_reader_relation_not_expressed_without_relaxing_gates(monkeypatch: pytest.MonkeyPatch) -> None:
    _clear_flags(monkeypatch)
    from emlis_ai_reply_service import render_emlis_ai_reply

    composer = _PositiveRecoveryRepairComposer()
    reply = await render_emlis_ai_reply(
        user_id="step6-positive-recovery-repair-user",
        subscription_tier="free",
        current_input=_positive_recovery_input("step6-positive-recovery-repair-input"),
        display_name="Mash",
        timezone_name="Asia/Tokyo",
        composer_client=composer,
    )

    assert len(composer.payloads) == 2
    assert _previous_rejection_reasons(composer.payloads[0]) == []
    assert "relation_not_expressed" in _previous_rejection_reasons(composer.payloads[1])

    diagnostic = reply.meta["diagnostic_summary"]
    gate_results = diagnostic["gate_results"]
    reader_gate = gate_results["reader"]
    grounding_gate = gate_results["grounding"]
    template_gate = gate_results["template_echo"]
    display_gate = _display_gate(reply.meta)
    relation_diagnostic = diagnostic["step5_relation_diagnostic"]

    assert reader_gate["passed"] is True
    assert template_gate["passed"] is True
    assert "relation_not_expressed" not in reader_gate.get("rejection_reasons", [])
    assert "relation_not_expressed" not in diagnostic.get("secondary_reasons", [])
    assert diagnostic["primary_reason"] != "relation_not_expressed"
    assert reader_gate["reader_relation_signal_detected"] is True
    assert "recovery_load_bridge" in reader_gate["reader_relation_signal_keys"]

    if reply.meta["observation_status"] == "passed":
        assert reply.comment_text == _RELATION_REPAIRED_PUBLIC_TEXT
        assert diagnostic["primary_reason"] == "passed"
        assert grounding_gate["passed"] is True
        assert display_gate["passed"] is True
        assert display_gate["comment_text_allowed"] is True
    else:
        assert reply.comment_text == ""
        assert diagnostic["primary_reason"] != "relation_not_expressed"
        assert display_gate["passed"] is False
        assert display_gate["comment_text_allowed"] is False
        assert "relation_not_expressed" not in display_gate.get("rejection_reasons", [])

    assert relation_diagnostic["reader_gate_relation_not_expressed"] is False
    assert relation_diagnostic["reader_relation_signal_detected"] is True
    assert relation_diagnostic["self_repair_relation_marker_applied"] is True
    assert relation_diagnostic["self_repair_relation_marker_key"] == "recovery_load_bridge_v1"
    assert relation_diagnostic["self_repair_relation_marker_meaning_added"] is False
    assert relation_diagnostic["self_repair_relation_marker_gate_relaxed"] is False
    assert relation_diagnostic["reader_gate_relaxed"] is False
    assert relation_diagnostic["display_gate_relaxed"] is False
    assert relation_diagnostic["grounding_gate_relaxed"] is False
    assert relation_diagnostic["template_gate_relaxed"] is False
    assert relation_diagnostic["raw_input_included"] is False
    assert relation_diagnostic["comment_text_included"] is False
    assert _contains_forbidden_raw_key(relation_diagnostic) is False

    serialized_relation_diag = json.dumps(relation_diagnostic, ensure_ascii=False, sort_keys=True)
    assert _POSITIVE_RECOVERY_MEMO not in serialized_relation_diag
    assert _RELATION_REPAIRED_TEXT not in serialized_relation_diag
    assert _RELATION_REPAIRED_PUBLIC_TEXT not in serialized_relation_diag
    assert "\"comment_text\":" not in serialized_relation_diag


@pytest.mark.asyncio
async def test_step6_positive_recovery_e2e_keeps_fail_closed_when_relation_surface_is_still_missing(monkeypatch: pytest.MonkeyPatch) -> None:
    _clear_flags(monkeypatch)
    from emlis_ai_reply_service import render_emlis_ai_reply

    composer = _PositiveRecoveryRepairComposer(never_repair=True)
    reply = await render_emlis_ai_reply(
        user_id="step6-positive-recovery-still-missing-user",
        subscription_tier="free",
        current_input=_positive_recovery_input("step6-positive-recovery-still-missing-input"),
        display_name="Mash",
        timezone_name="Asia/Tokyo",
        composer_client=composer,
    )

    diagnostic = reply.meta["diagnostic_summary"]
    reader_gate = _reader_gate(diagnostic)
    display_gate = _display_gate(reply.meta)
    relation_diagnostic = diagnostic["step5_relation_diagnostic"]

    assert len(composer.payloads) == 2
    assert "relation_not_expressed" in _previous_rejection_reasons(composer.payloads[1])
    assert reply.meta["observation_status"] == "rejected"
    assert reply.comment_text == ""
    assert diagnostic["stage"] == "reader"
    assert diagnostic["primary_reason"] == "relation_not_expressed"
    assert reader_gate["passed"] is False
    assert reader_gate["reader_relation_signal_detected"] is False
    assert "relation_not_expressed" in reader_gate.get("rejection_reasons", [])
    assert display_gate["passed"] is False
    assert display_gate["comment_text_allowed"] is False
    assert display_gate["comment_text_present"] is False
    assert "relation_not_expressed" in display_gate.get("rejection_reasons", [])
    assert relation_diagnostic["reader_gate_relation_not_expressed"] is True
    assert relation_diagnostic["self_repair_relation_marker_applied"] is False
    assert relation_diagnostic["display_gate_relaxed"] is False
    assert relation_diagnostic["raw_input_included"] is False
    assert relation_diagnostic["comment_text_included"] is False

    serialized_relation_diag = json.dumps(relation_diagnostic, ensure_ascii=False, sort_keys=True)
    assert _POSITIVE_RECOVERY_MEMO not in serialized_relation_diag
    assert _RELATION_MISSING_TEXT not in serialized_relation_diag
    assert "\"comment_text\":" not in serialized_relation_diag
