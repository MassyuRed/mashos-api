from __future__ import annotations

from typing import Any

from emlis_ai_complete_self_repair_service import (
    COMPLETE_PRODUCT_QUALITY_SELF_REPAIR_STAGE,
    COMPLETE_SELF_REPAIR_POLICY_VERSION,
    build_complete_self_repair_contract_meta,
    build_complete_self_repair_policy_table_v2,
    run_complete_self_repair_loop,
)
from emlis_ai_complete_surface_realizer import CompleteSurfaceRealizationV2, build_complete_surface_realization_v2
from emlis_ai_complete_reply_diagnostics_service import build_complete_scorecard_event
from emlis_ai_complete_scorecard_service import aggregate_complete_scorecard_events, normalize_complete_scorecard_event


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


def _conflict_seed(sentence_budget: int = 3) -> dict[str, Any]:
    return {
        "coverage_group": "conflict",
        "sentence_budget": sentence_budget,
        "graph_nodes": [
            {
                "node_id": "n1",
                "material_id": "m1",
                "phrase_unit_id": "pu1",
                "evidence_span_id": "s1",
                "role": "wish_to_move",
                "relation_type": "contrast",
                "must_keep": True,
                "source_anchor_present": True,
            },
            {
                "node_id": "n2",
                "material_id": "m2",
                "phrase_unit_id": "pu2",
                "evidence_span_id": "s2",
                "role": "fear_to_stop",
                "relation_type": "contrast",
                "must_keep": True,
                "source_anchor_present": True,
            },
            {
                "node_id": "n3",
                "material_id": "m3",
                "phrase_unit_id": "pu3",
                "evidence_span_id": "s3",
                "role": "small_residue",
                "relation_type": "residue",
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


def test_step4_self_repair_policy_table_v2_keeps_gate_fail_closed_contract() -> None:
    contract = build_complete_self_repair_contract_meta()
    policy = build_complete_self_repair_policy_table_v2()

    assert contract["product_quality_step"] == COMPLETE_PRODUCT_QUALITY_SELF_REPAIR_STAGE
    assert contract["repair_policy_version"] == COMPLETE_SELF_REPAIR_POLICY_VERSION
    assert contract["repair_trace_contract_version"] == "emlis.complete_repair_trace.v2"
    assert contract["gate_relaxation_allowed"] is False
    assert contract["new_meaning_addition_allowed"] is False
    assert policy["unsupported_sentence"]["allowed_operations"] == ["remove_optional_line", "rebind_to_existing_evidence"]
    assert "add_rootless_material" in policy["unsupported_sentence"]["forbidden_operations"]
    assert "surface_signature_before" in policy["template_like"]["required_trace_fields"]
    assert policy["overclaim"]["reject_preferred"] is True
    assert contract["comment_text_key_written"] is False
    assert contract["response_shape_changed"] is False
    assert contract["external_ai_used"] is False


def test_step4_relation_repair_trace_v2_records_operation_and_preserves_binding() -> None:
    realization = build_complete_surface_realization_v2(sentence_plan_seed=_conflict_seed())
    result = run_complete_self_repair_loop(surface_realization=realization, gate_reasons=["relation_not_expressed"])
    trace = result.as_meta()["repair_trace_v2"][0]

    assert result.repaired is True
    assert trace["source_gate"] == "grounding"
    assert trace["reason_code"] == "relation_not_expressed"
    assert trace["operation"] == "make_declared_relation_surface_explicit"
    assert trace["meaning_added"] is False
    assert trace["evidence_ids_preserved"] is True
    assert trace["relation_ids_preserved"] is True
    assert trace["relation_type"] == "contrast"
    assert trace["before_sentence_ids"] == trace["after_sentence_ids"]
    assert trace["surface_signature_before"]["signature_count"] == trace["surface_signature_after"]["signature_count"]
    assert result.as_meta()["repair_policy_table"]["relation_not_expressed"]["meaning_added"] is False
    assert _contains_forbidden_raw_key(result.as_meta()) is False


def test_step4_too_long_trace_records_optional_sentence_removal_without_deleting_must_include() -> None:
    realization = build_complete_surface_realization_v2(sentence_plan_seed=_long_seed())
    assert len(realization.surface_lines) == 4

    result = run_complete_self_repair_loop(surface_realization=realization, gate_reasons=["too_long"])
    trace = result.as_meta()["repair_trace_v2"][0]

    assert result.repaired is True
    assert trace["source_gate"] == "reader"
    assert trace["operation"] == "remove_optional_line_for_length"
    assert trace["meaning_added"] is False
    assert trace["removed_optional_sentence_ids"]
    assert len(trace["after_sentence_ids"]) == len(trace["before_sentence_ids"]) - 1
    assert {"s1", "s2"}.issubset(set(result.used_evidence_span_ids))
    assert result.as_meta()["comment_text_key_written"] is False


def test_step4_raw_echo_trace_records_echo_ratio_movement() -> None:
    realization = build_complete_surface_realization_v2(sentence_plan_seed=_conflict_seed())
    rows = [line.as_meta() for line in realization.surface_lines]
    rows[0]["surface_text"] = "今日は会議と資料修正が続いて、今日は会議と資料修正が続いた。"
    echo = CompleteSurfaceRealizationV2(
        plan_id=realization.plan_id,
        coverage_group=realization.coverage_group,
        surface_lines=rows,
        source_sentence_plan=realization.source_sentence_plan,
        status="ready",
    )

    result = run_complete_self_repair_loop(surface_realization=echo, gate_reasons=["raw_echo"])
    trace = result.as_meta()["repair_trace_v2"][0]

    assert result.repaired is True
    assert trace["source_gate"] == "template"
    assert trace["operation"] == "reduce_raw_echo_by_role_phrase_rephrase"
    assert trace["echo_ratio_before"] >= trace["echo_ratio_after"]
    assert trace["echo_ratio_reduced"] is True
    assert trace["meaning_added"] is False
    assert "会議と資料修正" not in result.repaired_surface_realization.realized_text


def test_step4_overclaim_trace_aborts_instead_of_weakening_gate() -> None:
    realization = build_complete_surface_realization_v2(sentence_plan_seed=_conflict_seed())
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
    trace = meta["repair_trace_v2"][0]

    assert result.aborted is True
    assert trace["source_gate"] == "overclaim"
    assert trace["result"] == "aborted"
    assert trace["abort_reason"] == "overclaim_reject_preferred"
    assert trace["meaning_added"] is False
    assert meta["gate_relaxation_allowed"] is False
    assert meta["display_gate_relaxed"] is False


def test_step4_repair_trace_v2_flows_to_scorecard_event_and_aggregate() -> None:
    realization = build_complete_surface_realization_v2(sentence_plan_seed=_conflict_seed())
    repair = run_complete_self_repair_loop(surface_realization=realization, gate_reasons=["relation_not_expressed"])
    repair_meta = repair.as_meta(include_realized_text=False)
    candidate = {
        "status": "generated",
        "composer_source": "ai_generated",
        "composer_model": "cocolon_emlis_observation_composer.a1.v1",
        "generation_method": "complete_initial_binding_first_composer",
        "coverage_scope": "conflict",
        "used_evidence_span_ids": list(repair.used_evidence_span_ids),
        "used_relation_ids": list(repair.relation_types),
        "composer_meta": {
            "complete_composer_client_added": True,
            "coverage_group": "conflict",
            "used_phrase_unit_ids": list(repair.used_phrase_unit_ids),
            "self_repair": repair_meta,
            "repair_trace": repair_meta["repair_trace_v2"],
            "binding_meta": {"binding_count": len(repair.repaired_surface_realization.surface_lines)},
        },
    }
    display = {"observation_status": "passed", "rejection_reasons": []}

    event = build_complete_scorecard_event(composer_candidate=candidate, display_decision=display)
    normalized = normalize_complete_scorecard_event(event)
    aggregate = aggregate_complete_scorecard_events([event])

    assert event["repair_trace_v2_count"] == 1
    assert event["repair_meaning_added_count"] == 0
    assert event["repair_policy_violation_count"] == 0
    assert normalized["repair_passed_count"] == 1
    assert aggregate["totals"]["repair_passed_count"] == 1
    assert "repair_meaning_added_detected" not in aggregate["release_blockers"]
    assert "repair_policy_violation_detected" not in aggregate["release_blockers"]
