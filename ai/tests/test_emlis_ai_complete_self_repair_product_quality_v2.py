from __future__ import annotations

from typing import Any

from emlis_ai_complete_reply_diagnostics_service import build_complete_scorecard_event
from emlis_ai_complete_scorecard_service import normalize_complete_scorecard_event
from emlis_ai_complete_self_repair_service import (
    COMPLETE_PRODUCT_QUALITY_SELF_REPAIR_STAGE,
    COMPLETE_SELF_REPAIR_POLICY_VERSION,
    build_complete_self_repair_contract_meta,
    build_complete_self_repair_policy_table_v2,
    run_complete_self_repair_loop,
)
from emlis_ai_complete_surface_realizer import (
    CompleteSurfaceRealizationV2,
    build_complete_surface_realization_v2,
)


class _DisplayDecision:
    observation_status = "passed"
    rejection_reasons: list[str] = []


class _Candidate:
    def __init__(self, self_repair_meta: dict[str, Any]) -> None:
        self.status = "generated"
        self.composer_source = "ai_generated"
        self.composer_model = "cocolon_emlis_observation_composer.a1.v1"
        self.generation_method = "complete_initial_binding_first_composer"
        self.generation_scope = "scoped_graph_evidence_composer"
        self.coverage_scope = "conflict"
        self.used_evidence_span_ids = ["s1", "s2"]
        self.used_relation_ids = ["approach_avoidance"]
        self.composer_meta = {
            "coverage_group": "conflict",
            "used_evidence_span_ids": ["s1", "s2"],
            "used_phrase_unit_ids": ["pu1", "pu2"],
            "used_relation_ids": ["approach_avoidance"],
            "binding_count": 2,
            "final_grounding_report": {
                "binding_used": True,
                "binding_supported_sentence_count": 2,
                "expected_binding_count": 2,
                "product_quality_grounding_report": {
                    "binding_supported_sentence_count": 2,
                    "expected_binding_count": 2,
                    "binding_support_source": "declared_relation_binding",
                },
            },
            "self_repair": self_repair_meta,
            "repair_trace": self_repair_meta.get("repair_trace_v2", []),
        }

    def as_meta(self, *, include_comment_text: bool = False) -> dict[str, Any]:
        return {
            "status": self.status,
            "composer_source": self.composer_source,
            "composer_meta": self.composer_meta,
            "coverage_scope": self.coverage_scope,
            "used_evidence_span_ids": self.used_evidence_span_ids,
            "used_relation_ids": self.used_relation_ids,
        }


def _relationship_seed() -> dict[str, Any]:
    return {
        "coverage_group": "conflict",
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


def test_step4_product_quality_self_repair_policy_table_is_gate_safe() -> None:
    contract = build_complete_self_repair_contract_meta()
    policy_table = build_complete_self_repair_policy_table_v2()

    assert contract["product_quality_step"] == COMPLETE_PRODUCT_QUALITY_SELF_REPAIR_STAGE
    assert contract["repair_policy_version"] == COMPLETE_SELF_REPAIR_POLICY_VERSION
    assert contract["gate_relaxation_allowed"] is False
    assert contract["new_meaning_addition_allowed"] is False
    assert contract["must_include_deletion_allowed"] is False
    assert policy_table["unsupported_sentence"]["source_gate"] == "grounding"
    assert "add_rootless_material" in policy_table["unsupported_sentence"]["forbidden_operations"]
    assert "delete_must_include" in policy_table["too_long"]["forbidden_operations"]
    assert policy_table["overclaim"]["reject_preferred"] is True


def test_step4_relation_repair_trace_v2_records_required_fields_without_meaning_addition() -> None:
    realization = build_complete_surface_realization_v2(sentence_plan_seed=_relationship_seed())
    result = run_complete_self_repair_loop(surface_realization=realization, gate_reasons=["relation_not_expressed"])
    trace = result.as_meta()["repair_trace_v2"][0]

    assert result.repaired is True
    assert trace["repair_trace_contract_version"] == "emlis.complete_repair_trace.v2"
    assert trace["repair_policy_version"] == COMPLETE_SELF_REPAIR_POLICY_VERSION
    assert trace["source_gate"] == "grounding"
    assert trace["reason_code"] == "relation_not_expressed"
    assert trace["operation"] == "make_declared_relation_surface_explicit"
    assert trace["meaning_added"] is False
    assert trace["evidence_ids_preserved"] is True
    assert trace["relation_ids_preserved"] is True
    assert trace["before_sentence_ids"] == trace["after_sentence_ids"]
    assert trace["relation_type"] == "approach_avoidance"
    assert trace["release_blocker"] is False


def test_step4_template_and_echo_repairs_record_surface_signature_and_echo_ratios() -> None:
    realization = build_complete_surface_realization_v2(sentence_plan_seed=_relationship_seed())
    template_result = run_complete_self_repair_loop(surface_realization=realization, gate_reasons=["template_like"])
    template_trace = template_result.as_meta()["repair_trace_v2"][0]

    assert template_trace["source_gate"] == "template"
    assert template_trace["surface_signature_before"]["surface_signatures"] != template_trace["surface_signature_after"]["surface_signatures"]
    assert template_trace["surface_signature_changed"] is True
    assert template_trace["meaning_added"] is False

    rows = [line.as_meta() for line in realization.surface_lines]
    rows[0]["surface_text"] = "会議が続いた。会議が続いた。会議が続いた。会議が続いた。会議が続いた。"
    echo = CompleteSurfaceRealizationV2(
        plan_id=realization.plan_id,
        coverage_group=realization.coverage_group,
        surface_lines=rows,
        source_sentence_plan=realization.source_sentence_plan,
        status="ready",
    )
    echo_result = run_complete_self_repair_loop(surface_realization=echo, gate_reasons=["raw_echo"])
    echo_trace = echo_result.as_meta()["repair_trace_v2"][0]

    assert echo_trace["source_gate"] == "template"
    assert echo_trace["operation"] == "reduce_raw_echo_by_role_phrase_rephrase"
    assert echo_trace["echo_ratio_after"] <= echo_trace["echo_ratio_before"]
    assert echo_trace["meaning_added"] is False


def test_step4_overclaim_abort_is_visible_as_release_blocker_not_gate_relaxation() -> None:
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
    trace = result.as_meta()["repair_trace_v2"][0]

    assert result.aborted is True
    assert trace["source_gate"] == "overclaim"
    assert trace["result"] == "aborted"
    assert trace["abort_reason"] == "overclaim_reject_preferred"
    assert trace["release_blocker"] is True
    assert trace["meaning_added"] is False
    assert trace["gate_relaxed"] is False


def test_step4_repair_trace_v2_feeds_scorecard_without_raw_text() -> None:
    realization = build_complete_surface_realization_v2(sentence_plan_seed=_relationship_seed())
    repair = run_complete_self_repair_loop(surface_realization=realization, gate_reasons=["relation_not_expressed"])
    self_repair_meta = repair.as_meta(include_realized_text=False)
    event = build_complete_scorecard_event(composer_candidate=_Candidate(self_repair_meta), display_decision=_DisplayDecision())
    normalized = normalize_complete_scorecard_event(event)

    assert event["repair_trace_v2_count"] == 1
    assert event["repair_passed_count"] == 1
    assert event["repair_meaning_added_count"] == 0
    assert event["repair_policy_violation_count"] == 0
    assert event["repair_success"] is True
    assert normalized["repair_success_count"] == 1
    assert normalized["repair_trace_v2_count"] == 1
    assert normalized["repair_meaning_added_count"] == 0
    assert normalized["raw_input_included"] is False
