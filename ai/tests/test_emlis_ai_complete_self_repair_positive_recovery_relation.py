from __future__ import annotations

from typing import Any

from emlis_ai_complete_self_repair_service import run_complete_self_repair_loop
from emlis_ai_complete_surface_realizer import CompleteSurfaceRealizationV2
from emlis_ai_listener_reader_judge import judge_listener_readability
from emlis_ai_relation_surface_contract import RELATION_SURFACE_CONTRACT_VERSION

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


def _contains_forbidden_raw_key(value: Any) -> bool:
    if isinstance(value, dict):
        return any(key in _FORBIDDEN_RAW_KEYS or _contains_forbidden_raw_key(item) for key, item in value.items())
    if isinstance(value, (list, tuple, set)):
        return any(_contains_forbidden_raw_key(item) for item in value)
    return False


def _positive_recovery_realization(*, prior_load_present: bool = True) -> CompleteSurfaceRealizationV2:
    relation_text = "小さな回復として形を取り直しています。"
    relation_meta = {
        "source": "positive_recovery_step3_fixture",
        "raw_input_included": False,
    }
    if prior_load_present:
        relation_text = "前段の負荷のあとに、小さな回復として形を取り直しています。"
        relation_meta["prior_load_hint"] = "負荷"
    return CompleteSurfaceRealizationV2(
        plan_id="positive_recovery_step3_plan",
        coverage_group="positive_recovery",
        surface_lines=(
            {
                "sentence_id": "s1",
                "line_role": "opening",
                "relation_type": "recovery",
                "surface_text": "Emlisです。",
                "used_evidence_span_ids": ["span_1"],
                "used_phrase_unit_ids": ["pu_1"],
                "predicate_key": "opening_receive",
                "source_sentence_plan_line": {
                    "sentence_id": "s1",
                    "line_role": "opening",
                    "relation_type": "recovery",
                    "used_evidence_span_ids": ["span_1"],
                    "used_phrase_unit_ids": ["pu_1"],
                    "must_include_roles": ["small_repair"],
                },
            },
            {
                "sentence_id": "s2",
                "line_role": "core",
                "relation_type": "recovery",
                "surface_text": "小さな回復が少し戻ってきています。",
                "used_evidence_span_ids": ["span_2"],
                "used_phrase_unit_ids": ["pu_2"],
                "predicate_key": "recovery_return",
                "source_sentence_plan_line": {
                    "sentence_id": "s2",
                    "line_role": "core",
                    "relation_type": "recovery",
                    "used_evidence_span_ids": ["span_2"],
                    "used_phrase_unit_ids": ["pu_2"],
                    "must_include_roles": ["small_repair"],
                },
            },
            {
                "sentence_id": "s3",
                "line_role": "relation",
                "relation_type": "recovery",
                "surface_text": relation_text,
                "used_evidence_span_ids": ["span_3"],
                "used_phrase_unit_ids": ["pu_3"],
                "predicate_key": "recovery_reshape",
                "meta": relation_meta,
                "source_sentence_plan_line": {
                    "sentence_id": "s3",
                    "line_role": "relation",
                    "relation_type": "recovery",
                    "used_evidence_span_ids": ["span_3"],
                    "used_phrase_unit_ids": ["pu_3"],
                    "must_include_roles": ["small_repair"],
                },
            },
        ),
        source_sentence_plan=None,
        status="ready",
        meta={"fixture": "positive_recovery_step3", "raw_input_included": False},
    )


def test_self_repair_positive_recovery_marker_uses_relation_surface_contract() -> None:
    realization = _positive_recovery_realization(prior_load_present=True)
    before_text = realization.realized_text

    result = run_complete_self_repair_loop(
        surface_realization=realization,
        gate_reasons=["relation_not_expressed"],
    )
    meta = result.as_meta()
    trace = meta["repair_trace"][0]
    repaired_text = result.repaired_surface_realization.realized_text

    assert result.repaired is True
    assert result.ready is True
    assert repaired_text != before_text
    assert "戻ってくる動きとその前の重さが同じ流れの中でつながっています。" in repaired_text
    assert "戻ってくる動きと前段の負荷の関係も残しています。" not in repaired_text
    assert trace["reason_code"] == "relation_not_expressed"
    assert trace["applied_operation"] == "make_declared_relation_surface_explicit"
    assert trace["meaning_added"] is False
    assert trace["new_meaning_added"] is False
    assert trace["relation_ids_preserved"] is True
    assert trace["gate_relaxed"] is False
    assert trace["relation_surface_contract_version"] == RELATION_SURFACE_CONTRACT_VERSION
    assert trace["self_repair_relation_marker_applied"] is True
    assert trace["self_repair_relation_marker_key"] == "recovery_load_bridge_v1"
    assert trace["self_repair_relation_signal"]["reader_relation_signal_detected"] is True
    assert "recovery" in trace["self_repair_relation_signal"]["reader_relation_signal_relation_types"]
    assert set(result.used_evidence_span_ids) == set(realization.used_evidence_span_ids)
    assert set(result.used_phrase_unit_ids) == set(realization.used_phrase_unit_ids)
    assert set(result.relation_types) == set(realization.relation_types)
    assert _contains_forbidden_raw_key(meta) is False


def test_self_repair_positive_recovery_marker_without_prior_load_does_not_invent_load() -> None:
    realization = _positive_recovery_realization(prior_load_present=False)

    result = run_complete_self_repair_loop(
        surface_realization=realization,
        gate_reasons=["relation_not_expressed"],
    )
    trace = result.as_meta()["repair_trace"][0]
    repaired_text = result.repaired_surface_realization.realized_text

    assert result.repaired is True
    assert "戻る流れが、前の流れと切り離されずにつながっています。" in repaired_text
    assert "その前の重さ" not in repaired_text
    assert "前段の負荷" not in repaired_text
    assert trace["self_repair_relation_marker_key"] == "recovery_connected_flow_v1"
    assert trace["self_repair_relation_signal"]["reader_relation_signal_detected"] is True
    assert trace["meaning_added"] is False
    assert trace["relation_ids_preserved"] is True


def test_self_repair_repaired_positive_recovery_text_is_reader_detectable() -> None:
    realization = _positive_recovery_realization(prior_load_present=True)

    result = run_complete_self_repair_loop(
        surface_realization=realization,
        gate_reasons=["relation_not_expressed"],
    )
    reader_report = judge_listener_readability(
        result.repaired_surface_realization.realized_text,
        expected_relation_types=("positive_recovery",),
    )

    assert "relation_not_expressed" not in reader_report.rejection_reasons
