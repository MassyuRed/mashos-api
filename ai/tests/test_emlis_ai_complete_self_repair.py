from __future__ import annotations

from copy import deepcopy
from typing import Any

from emlis_ai_complete_self_repair_service import (
    COMPLETE_SELF_REPAIR_STAGE,
    COMPLETE_SELF_REPAIR_VERSION,
    CompleteSelfRepairResult,
    build_complete_self_repair_contract_meta,
    build_complete_self_repair_meta,
    run_complete_self_repair_loop,
)
from emlis_ai_complete_surface_realizer import (
    CompleteSurfaceRealizationV2,
    build_complete_surface_realization_v2,
    build_complete_surface_signature,
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


def _contains_forbidden_raw_key(value: Any) -> bool:
    if isinstance(value, dict):
        return any(key in _FORBIDDEN_RAW_KEYS or _contains_forbidden_raw_key(item) for key, item in value.items())
    if isinstance(value, (list, tuple, set)):
        return any(_contains_forbidden_raw_key(item) for item in value)
    return False


def _relationship_seed() -> dict[str, Any]:
    return {
        "coverage_group": "relationship",
        "sentence_budget": 3,
        "graph_nodes": [
            {
                "node_id": "n1",
                "material_id": "m1",
                "phrase_unit_id": "pu1",
                "evidence_span_id": "s1",
                "role": "wish_to_rely",
                "relation_type": "approach_avoidance",
                "must_keep": True,
                "source_anchor_present": True,
            },
            {
                "node_id": "n2",
                "material_id": "m2",
                "phrase_unit_id": "pu2",
                "evidence_span_id": "s2",
                "role": "burden_fear",
                "relation_type": "approach_avoidance",
                "must_keep": True,
                "source_anchor_present": True,
            },
        ],
    }


def _long_seed() -> dict[str, Any]:
    return {
        "coverage_group": "long_meaning_arc",
        "sentence_budget": 4,
        "graph_nodes": [
            {"node_id": "n1", "material_id": "m1", "phrase_unit_id": "pu1", "evidence_span_id": "s1", "role": "fatigue_accumulation", "relation_type": "pressure", "must_keep": True, "source_anchor_present": True},
            {"node_id": "n2", "material_id": "m2", "phrase_unit_id": "pu2", "evidence_span_id": "s2", "role": "value_wish", "relation_type": "contrast", "source_anchor_present": True},
            {"node_id": "n3", "material_id": "m3", "phrase_unit_id": "pu3", "evidence_span_id": "s3", "role": "small_repair", "relation_type": "recovery", "source_anchor_present": True},
            {"node_id": "n4", "material_id": "m4", "phrase_unit_id": "pu4", "evidence_span_id": "s4", "role": "hurt_core", "relation_type": "residue", "source_anchor_present": True},
        ],
    }


def _long_realization() -> CompleteSurfaceRealizationV2:
    realization = build_complete_surface_realization_v2(sentence_plan_seed=_long_seed())
    assert realization.ready is True
    assert len(realization.surface_lines) == 4
    return realization


def test_step9_contract_meta_is_additive_and_gate_safe() -> None:
    meta = build_complete_self_repair_contract_meta()

    assert meta["version"] == COMPLETE_SELF_REPAIR_VERSION
    assert meta["target_step"] == COMPLETE_SELF_REPAIR_STAGE
    assert meta["self_repair_loop_added"] is True
    assert meta["max_repair_attempts"] == 2
    assert "unsupported_sentence" in meta["allowed_repair_reasons"]
    assert "relation_not_expressed" in meta["allowed_repair_reasons"]
    assert "raw_echo" in meta["allowed_repair_reasons"]
    assert "too_long" in meta["allowed_repair_reasons"]
    assert "overclaim" in meta["allowed_repair_reasons"]
    assert meta["gate_relaxation_allowed"] is False
    assert meta["grounding_gate_relaxed"] is False
    assert meta["display_gate_relaxed"] is False
    assert meta["new_meaning_addition_allowed"] is False
    assert meta["must_include_deletion_allowed"] is False
    assert meta["comment_text_key_written"] is False
    assert meta["comment_text_contract"] == "passed_only"
    assert meta["response_shape_changed"] is False
    assert meta["public_response_key_change"] is False
    assert meta["api_route_changed"] is False
    assert meta["db_physical_name_changed"] is False
    assert meta["rn_visible_title_changed"] is False
    assert meta["external_ai_used"] is False
    assert meta["local_llm_used"] is False
    assert meta["fixed_sentence_template_used"] is False
    assert meta["raw_input_included"] is False


def test_step9_relation_not_expressed_adds_relation_marker_without_changing_binding_ids() -> None:
    realization = build_complete_surface_realization_v2(sentence_plan_seed=_relationship_seed())
    before_text = realization.realized_text
    result = run_complete_self_repair_loop(surface_realization=realization, gate_reasons=["relation_not_expressed"])
    meta = result.as_meta()

    assert isinstance(result, CompleteSelfRepairResult)
    assert result.repaired is True
    assert result.ready is True
    assert meta["status"] == "repaired"
    assert meta["attempt_count"] == 1
    assert meta["repair_trace"][0]["reason_code"] == "relation_not_expressed"
    assert meta["repair_trace"][0]["applied_operation"] == "make_declared_relation_surface_explicit"
    assert meta["repair_trace"][0]["evidence_ids_unchanged"] is True
    assert meta["repair_trace"][0]["relation_ids_unchanged"] is True
    assert result.repaired_surface_realization.realized_text != before_text
    assert "両方" in result.repaired_surface_realization.realized_text
    assert set(result.used_evidence_span_ids) == set(realization.used_evidence_span_ids)
    assert set(result.used_phrase_unit_ids) == set(realization.used_phrase_unit_ids)
    assert set(result.relation_types) == set(realization.relation_types)
    assert meta["comment_text_key_written"] is False
    assert meta["response_shape_changed"] is False
    assert _contains_forbidden_raw_key(meta) is False


def test_step9_too_long_removes_optional_closing_without_deleting_must_include_lines() -> None:
    realization = _long_realization()
    result = run_complete_self_repair_loop(surface_realization=realization, gate_reasons=["too_long"])
    meta = result.as_meta()

    assert result.repaired is True
    assert result.ready is True
    assert meta["attempt_count"] == 1
    assert meta["repair_trace"][0]["applied_operation"] == "remove_optional_line_for_length"
    assert meta["before_surface_line_count"] == 4
    assert meta["after_surface_line_count"] == 3
    assert [line.line_role for line in result.repaired_surface_realization.surface_lines] == ["opening", "core", "relation"]
    assert {"s1", "s2"}.issubset(set(result.used_evidence_span_ids))
    assert meta["new_meaning_added"] is False
    assert meta["comment_text_key_written"] is False
    assert meta["response_shape_changed"] is False


def test_step9_unsupported_sentence_drops_optional_unbound_line_but_preserves_required_lines() -> None:
    realization = _long_realization()
    rows = [line.as_meta() for line in realization.surface_lines]
    rows[-1]["used_evidence_span_ids"] = []
    rows[-1]["evidence_span_ids"] = []
    damaged = CompleteSurfaceRealizationV2(
        plan_id=realization.plan_id,
        coverage_group=realization.coverage_group,
        surface_lines=rows,
        source_sentence_plan=realization.source_sentence_plan,
        status="ready",
    )

    assert damaged.ready is False
    result = run_complete_self_repair_loop(surface_realization=damaged, gate_reasons=["unsupported_sentence"])
    meta = result.as_meta()

    assert result.repaired is True
    assert result.ready is True
    assert meta["repair_trace"][0]["reason_code"] == "unsupported_sentence"
    assert meta["repair_trace"][0]["applied_operation"] == "remove_optional_line"
    assert meta["after_surface_line_count"] == 3
    assert all(line.evidence_span_ids for line in result.repaired_surface_realization.surface_lines)
    assert all(line.phrase_unit_ids for line in result.repaired_surface_realization.surface_lines)
    assert meta["comment_text_key_written"] is False
    assert meta["response_shape_changed"] is False


def test_step9_template_like_varies_surface_signature_without_fixed_completed_sentence() -> None:
    realization = _long_realization()
    before = build_complete_surface_signature(realization)
    result = run_complete_self_repair_loop(surface_realization=realization, gate_reasons=["template_like"])
    after = build_complete_surface_signature(result.repaired_surface_realization)
    meta = result.as_meta()

    assert result.repaired is True
    assert result.ready is True
    assert meta["repair_trace"][0]["applied_operation"] == "vary_surface_signature_tail_connector_order"
    assert before["surface_signatures"] != after["surface_signatures"]
    assert meta["surface_signature_changed"] is True
    assert meta["fixed_sentence_template_used"] is False
    assert meta["external_ai_used"] is False
    assert meta["local_llm_used"] is False
    assert meta["comment_text_key_written"] is False
    assert set(result.used_evidence_span_ids) == set(realization.used_evidence_span_ids)


def test_step9_raw_echo_rephrases_from_role_and_keeps_binding_scope() -> None:
    realization = build_complete_surface_realization_v2(sentence_plan_seed=_relationship_seed())
    rows = [line.as_meta() for line in realization.surface_lines]
    rows[0]["surface_text"] = "今日は会議と資料修正が続いて、本当に疲れて、今日は会議と資料修正が続いた。"
    echo = CompleteSurfaceRealizationV2(
        plan_id=realization.plan_id,
        coverage_group=realization.coverage_group,
        surface_lines=rows,
        source_sentence_plan=realization.source_sentence_plan,
        status="ready",
    )

    result = run_complete_self_repair_loop(surface_realization=echo, gate_reasons=["raw_echo"])
    meta = result.as_meta()

    assert result.repaired is True
    assert result.ready is True
    assert meta["repair_trace"][0]["applied_operation"] == "reduce_raw_echo_by_role_phrase_rephrase"
    assert "会議と資料修正" not in result.repaired_surface_realization.realized_text
    assert "根拠のある範囲" in result.repaired_surface_realization.realized_text
    assert set(result.used_evidence_span_ids) == set(echo.used_evidence_span_ids)
    assert set(result.used_phrase_unit_ids) == set(echo.used_phrase_unit_ids)
    assert meta["new_meaning_added"] is False
    assert meta["comment_text_key_written"] is False
    assert _contains_forbidden_raw_key(meta) is False


def test_step9_overclaim_rejects_must_include_overclaim_without_weakening_gate() -> None:
    realization = build_complete_surface_realization_v2(sentence_plan_seed=_relationship_seed())
    rows = [line.as_meta() for line in realization.surface_lines]
    rows[0]["surface_text"] = "本当は愛されたい気持ちが中心にあります。"
    overclaim = CompleteSurfaceRealizationV2(
        plan_id=realization.plan_id,
        coverage_group=realization.coverage_group,
        surface_lines=rows,
        source_sentence_plan=realization.source_sentence_plan,
        status="ready",
    )

    result = run_complete_self_repair_loop(surface_realization=overclaim, gate_reasons=["overclaim"])
    meta = result.as_meta()

    assert result.aborted is True
    assert meta["status"] == "aborted"
    assert meta["repair_trace"][0]["result"] == "aborted"
    assert meta["repair_trace"][0]["reason_code"] == "overclaim"
    assert meta["repair_trace"][0]["applied_operation"] == "overclaim_reject_preferred"
    assert meta["gate_relaxation_allowed"] is False
    assert meta["grounding_gate_relaxed"] is False
    assert meta["display_gate_relaxed"] is False
    assert meta["new_meaning_added"] is False
    assert meta["comment_text_key_written"] is False
    assert meta["response_shape_changed"] is False


def test_step9_meta_helper_accepts_grounding_report_repair_targets() -> None:
    class _Report:
        rejection_reasons = ["unsupported_sentence"]
        binding_rejection_reasons: list[str] = []
        allowed_evidence_span_ids = ["s1", "s2"]
        binding_diagnostics = {"repair_targets": ["relation_not_expressed"]}

    realization = build_complete_surface_realization_v2(sentence_plan_seed=_relationship_seed())
    meta = build_complete_self_repair_meta(surface_realization=realization, grounding_report=_Report())

    assert meta["status"] == "repaired"
    assert meta["attempt_count"] <= 2
    assert "unsupported_sentence" in meta["gate_reasons"]
    assert "relation_not_expressed" in meta["gate_reasons"]
    assert meta["max_repair_attempts"] == 2
    assert meta["repaired_surface_meta"]["comment_text_key_written"] is False
    assert meta["response_shape_changed"] is False
    assert _contains_forbidden_raw_key(meta) is False
