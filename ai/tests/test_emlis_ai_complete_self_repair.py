from __future__ import annotations

from copy import deepcopy
from typing import Any

from emlis_ai_complete_self_repair_service import (
    COMPLETE_SELF_REPAIR_STAGE,
    COMPLETE_SELF_REPAIR_VERSION,
    PHASE17_SELF_REPAIR_UNAVAILABLE_REASON_SCHEMA_VERSION,
    PHASE17_SELF_REPAIR_UNAVAILABLE_REASON_SOURCE_PHASE,
    REPAIR_REASON_PHASE17_GROUNDING_RELATION_BINDING_MISSING,
    REPAIR_REASON_PHASE17_INTERNAL_ROLE_LABEL_LEAK,
    REPAIR_REASON_PHASE17_PRODUCT_VISIBLE_FIXTURE_NOT_REACHED,
    REPAIR_REASON_PHASE17_RELATION_SKELETON_LEAK,
    REPAIR_REASON_PHASE17_SECTION_BUDGET_MISMATCH,
    REPAIR_REASON_PHASE17_SURFACE_MODE_POLICY_MISSING,
    REPAIR_REASON_TEMPLATE_LIKE,
    CompleteSelfRepairResult,
    build_complete_self_repair_contract_meta,
    build_complete_self_repair_meta,
    build_phase17_self_repair_unavailable_reason_summary,
    normalize_complete_self_repair_reason,
    run_complete_self_repair_loop,
)
from emlis_ai_complete_surface_realizer import (
    CompleteSurfaceRealizationV2,
    build_complete_surface_realizer_contract_meta,
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




def test_phase17_7_contract_meta_lists_product_visible_repair_reasons_without_relaxation() -> None:
    meta = build_complete_self_repair_contract_meta()

    assert meta["phase17_7_self_repair_unavailable_reason_supported"] is True
    assert meta["phase17_7_self_repair_unavailable_reason_schema_version"] == PHASE17_SELF_REPAIR_UNAVAILABLE_REASON_SCHEMA_VERSION
    assert meta["phase17_7_self_repair_unavailable_reason_source_phase"] == PHASE17_SELF_REPAIR_UNAVAILABLE_REASON_SOURCE_PHASE
    assert REPAIR_REASON_PHASE17_INTERNAL_ROLE_LABEL_LEAK in meta["allowed_repair_reasons"]
    assert REPAIR_REASON_PHASE17_RELATION_SKELETON_LEAK in meta["allowed_repair_reasons"]
    assert meta["repair_policy_table"][REPAIR_REASON_PHASE17_INTERNAL_ROLE_LABEL_LEAK]["allowed_operations"] == [
        "rerender_surface_from_existing_role_phrases"
    ]
    assert meta["phase17_7_repair_targets_fixed_text_allowed"] is False
    assert meta["phase17_7_gate_relaxation_allowed"] is False
    assert meta["comment_text_key_written"] is False
    assert meta["response_shape_changed"] is False
    assert _contains_forbidden_raw_key(meta) is False


def test_phase17_7_surface_realizer_meta_exposes_repair_reason_codes_without_body() -> None:
    contract = build_complete_surface_realizer_contract_meta()

    assert contract["phase17_7_surface_repair_reason_supported"] is True
    assert contract["phase17_7_surface_repair_reason_summary_only"] is True
    assert contract["phase17_7_surface_repair_comment_text_body_included"] is False
    assert contract["phase17_7_surface_repair_raw_input_included"] is False

    realization = build_complete_surface_realization_v2(sentence_plan_seed=_long_seed())
    rows = [line.as_meta() for line in realization.surface_lines]
    rows[0]["surface_text"] = "positive state が本文に残っています。"
    damaged = CompleteSurfaceRealizationV2(
        plan_id=realization.plan_id,
        coverage_group=realization.coverage_group,
        surface_lines=rows,
        source_sentence_plan=realization.source_sentence_plan,
        status="ready",
    )
    meta = damaged.as_meta(include_realized_text=False)

    assert REPAIR_REASON_PHASE17_INTERNAL_ROLE_LABEL_LEAK in meta["phase17_7_surface_repair_reason_codes"]
    assert meta["phase17_7_surface_repair_reason_summary_only"] is True
    assert meta["phase17_7_surface_repair_comment_text_body_included"] is False
    assert meta["phase17_7_surface_repair_raw_input_included"] is False
    assert "realized_text" not in meta
    assert _contains_forbidden_raw_key(meta) is False


def test_phase17_7_reason_summary_is_meta_only_and_maps_unavailable_sources() -> None:
    summary = build_phase17_self_repair_unavailable_reason_summary(
        primary_reason="complete_initial_surface_unavailable",
        candidate_status="unavailable",
        extra_meta={
            "two_stage_unavailable_reason_codes": [
                "same_predicate_family_stack",
                "two_stage_internal_role_label_leak",
            ],
            "comment_text_body_included": False,
            "raw_input_included": False,
        },
    )

    assert summary["schema_version"] == PHASE17_SELF_REPAIR_UNAVAILABLE_REASON_SCHEMA_VERSION
    assert summary["source_phase"] == PHASE17_SELF_REPAIR_UNAVAILABLE_REASON_SOURCE_PHASE
    assert summary["product_visible_fixture_not_reached"] is True
    assert REPAIR_REASON_PHASE17_SURFACE_MODE_POLICY_MISSING in summary["phase17_reason_codes"]
    assert REPAIR_REASON_PHASE17_INTERNAL_ROLE_LABEL_LEAK in summary["phase17_reason_codes"]
    assert REPAIR_REASON_PHASE17_PRODUCT_VISIBLE_FIXTURE_NOT_REACHED in summary["phase17_reason_codes"]
    assert REPAIR_REASON_PHASE17_PRODUCT_VISIBLE_FIXTURE_NOT_REACHED in summary["diagnostic_only_reason_codes"]
    assert "template_like" in summary["self_repair_handoff_reason_codes"]
    assert summary["release_blocker"] is False
    assert summary["reason_summary_only"] is True
    assert summary["comment_text_body_included"] is False
    assert summary["raw_input_included"] is False
    assert summary["display_gate_relaxed"] is False
    assert summary["grounding_gate_relaxed"] is False
    assert _contains_forbidden_raw_key(summary) is False


def test_phase17_7_normalizes_product_visible_gate_reasons_before_self_repair_handoff() -> None:
    assert normalize_complete_self_repair_reason("same_predicate_family_stack") == REPAIR_REASON_TEMPLATE_LIKE
    assert normalize_complete_self_repair_reason("two_stage_internal_role_label_leak") == REPAIR_REASON_PHASE17_INTERNAL_ROLE_LABEL_LEAK
    assert normalize_complete_self_repair_reason("two_stage_relation_skeleton_leak_surface") == REPAIR_REASON_PHASE17_RELATION_SKELETON_LEAK
    assert normalize_complete_self_repair_reason("complete_initial_grounding_failed") == REPAIR_REASON_PHASE17_GROUNDING_RELATION_BINDING_MISSING
    assert normalize_complete_self_repair_reason("product_visible_fixture_not_reached") == REPAIR_REASON_PHASE17_PRODUCT_VISIBLE_FIXTURE_NOT_REACHED


def test_phase17_7_internal_role_label_leak_rerenders_from_existing_role_phrase_without_fixed_text() -> None:
    realization = build_complete_surface_realization_v2(sentence_plan_seed=_long_seed())
    rows = [line.as_meta() for line in realization.surface_lines]
    rows[0]["surface_text"] = "achievement がそのまま表面に出ています。"
    rows[0]["role_phrase_key"] = "achievement"
    damaged = CompleteSurfaceRealizationV2(
        plan_id=realization.plan_id,
        coverage_group=realization.coverage_group,
        surface_lines=rows,
        source_sentence_plan=realization.source_sentence_plan,
        status="ready",
    )

    result = run_complete_self_repair_loop(
        surface_realization=damaged,
        gate_reasons=["two_stage_internal_role_label_leak"],
    )
    meta = result.as_meta(include_realized_text=False)

    assert result.repaired is True
    assert result.ready is True
    assert "achievement" not in result.repaired_surface_realization.realized_text
    assert "気持ちが動いた変化" in result.repaired_surface_realization.realized_text
    assert meta["repair_trace"][0]["reason_code"] == REPAIR_REASON_PHASE17_INTERNAL_ROLE_LABEL_LEAK
    assert meta["repair_trace"][0]["applied_operation"] == "rerender_surface_from_existing_role_phrases"
    assert meta["phase17_7_self_repair_unavailable_reason"]["reason_summary_only"] is True
    assert meta["fixed_sentence_template_used"] is False
    assert meta["comment_text_key_written"] is False
    assert meta["display_gate_relaxed"] is False
    assert _contains_forbidden_raw_key(meta) is False


def test_phase17_7_relation_skeleton_leak_rerenders_without_inventing_relation() -> None:
    realization = build_complete_surface_realization_v2(sentence_plan_seed=_relationship_seed())
    rows = [line.as_meta() for line in realization.surface_lines]
    rows[0]["surface_text"] = "同じ流れが同じ場所に残っています。"
    rows[0]["relation_type"] = "approach_avoidance"
    damaged = CompleteSurfaceRealizationV2(
        plan_id=realization.plan_id,
        coverage_group=realization.coverage_group,
        surface_lines=rows,
        source_sentence_plan=realization.source_sentence_plan,
        status="ready",
    )

    result = run_complete_self_repair_loop(
        surface_realization=damaged,
        gate_reasons=["two_stage_relation_skeleton_leak"],
    )
    text = result.repaired_surface_realization.realized_text
    meta = result.as_meta(include_realized_text=False)

    assert result.repaired is True
    assert "同じ流れ" not in text
    assert "同じ場所" not in text
    assert set(result.relation_types) == set(damaged.relation_types)
    assert meta["repair_trace"][0]["reason_code"] == REPAIR_REASON_PHASE17_RELATION_SKELETON_LEAK
    assert meta["repair_trace"][0]["relation_ids_unchanged"] is True
    assert meta["new_meaning_added"] is False
    assert meta["fixed_sentence_template_used"] is False
    assert meta["grounding_gate_relaxed"] is False


def test_phase17_7_section_budget_mismatch_trims_only_optional_excess_rows() -> None:
    realization = build_complete_surface_realization_v2(sentence_plan_seed=_long_seed())
    rows = [line.as_meta() for line in realization.surface_lines]
    for index, row in enumerate(rows):
        section_id = "observation" if index < 2 else "reception"
        row["two_stage_section_id"] = section_id
        row["two_stage_display_label"] = "見えたこと：" if section_id == "observation" else "Emlisから："
        source_line = {
            **row.get("source_sentence_plan_line", {}),
            "must_include_roles": [] if index == 1 else row.get("source_sentence_plan_line", {}).get("must_include_roles", []),
            "optional_roles": ["optional_phase17_budget_row"] if index == 1 else row.get("source_sentence_plan_line", {}).get("optional_roles", []),
        }
        source_line["meta"] = {
            **source_line.get("meta", {}),
            "two_stage_section_id": section_id,
            "two_stage_display_label": row["two_stage_display_label"],
            "two_stage_section_order": 1 if section_id == "observation" else 2,
            "two_stage_required": True,
        }
        row["source_sentence_plan_line"] = source_line
        row["meta"] = {
            **row.get("meta", {}),
            "two_stage_section_id": section_id,
            "two_stage_display_label": row["two_stage_display_label"],
            "two_stage_section_order": 1 if section_id == "observation" else 2,
            "two_stage_required": True,
        }
    damaged = CompleteSurfaceRealizationV2(
        plan_id=realization.plan_id,
        coverage_group=realization.coverage_group,
        surface_lines=rows,
        status="ready",
        meta={"two_stage_required": True},
    )

    result = run_complete_self_repair_loop(
        surface_realization=damaged,
        gate_reasons=["two_stage_section_budget_mismatch"],
    )
    meta = result.as_meta(include_realized_text=False)
    section_ids = [line.meta.get("two_stage_section_id") for line in result.repaired_surface_realization.surface_lines]

    assert result.repaired is True
    assert result.ready is True
    assert section_ids.count("observation") == 1
    assert section_ids.count("reception") == 2
    assert meta["repair_trace"][0]["reason_code"] == REPAIR_REASON_PHASE17_SECTION_BUDGET_MISMATCH
    assert meta["repair_trace"][0]["applied_operation"] == "normalize_two_stage_section_budget"
    assert meta["fixed_sentence_template_used"] is False
    assert meta["display_gate_relaxed"] is False
    assert meta["grounding_gate_relaxed"] is False


def test_phase17_7_product_visible_not_reached_is_diagnostic_only_not_repair_handoff() -> None:
    realization = build_complete_surface_realization_v2(sentence_plan_seed=_relationship_seed())

    result = run_complete_self_repair_loop(
        surface_realization=realization,
        gate_reasons=["product_visible_fixture_not_reached"],
    )
    meta = result.as_meta(include_realized_text=False)

    assert result.aborted is False
    assert result.repaired is False
    assert meta["repair_trace"] == []
    assert REPAIR_REASON_PHASE17_PRODUCT_VISIBLE_FIXTURE_NOT_REACHED in meta["phase17_diagnostic_only_reason_codes"]
    assert meta["blocked_reasons"] == []
    assert meta["fixed_sentence_template_used"] is False
    assert meta["display_gate_relaxed"] is False
    assert meta["grounding_gate_relaxed"] is False

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
