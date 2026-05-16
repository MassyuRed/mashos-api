from __future__ import annotations

from typing import Any

from emlis_ai_complete_sentence_planner import build_complete_sentence_plan_v2
from emlis_ai_complete_surface_realizer import (
    COMPLETE_SURFACE_REALIZER_STAGE,
    COMPLETE_SURFACE_REALIZER_VERSION,
    CompleteSurfaceRealizationV2,
    build_complete_surface_realization_v2,
    build_complete_surface_realizer_contract_meta,
    build_complete_surface_realizer_v2_meta,
    build_complete_surface_signature,
)


def _contains_forbidden_raw_key(value: Any) -> bool:
    forbidden = {
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
    if isinstance(value, dict):
        return any(key in forbidden or _contains_forbidden_raw_key(item) for key, item in value.items())
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


def test_step7_contract_meta_is_additive_and_grammar_parts_only() -> None:
    meta = build_complete_surface_realizer_contract_meta()

    assert meta["version"] == COMPLETE_SURFACE_REALIZER_VERSION
    assert meta["target_step"] == COMPLETE_SURFACE_REALIZER_STAGE
    assert meta["surface_realizer_2_0_added"] is True
    assert meta["accepts_complete_sentence_plan_v2"] is True
    assert meta["sentence_plan_must_be_followed"] is True
    assert meta["subject_policy_added"] is True
    assert meta["predicate_bank_added"] is True
    assert meta["connector_policy_added"] is True
    assert meta["ending_policy_added"] is True
    assert meta["distance_policy_added"] is True
    assert meta["variation_policy_added"] is True
    assert meta["surface_signature_added"] is True
    assert meta["surface_signature_to_template_guard"] is True
    assert meta["surface_text_internal_only"] is True
    assert meta["comment_text_generated"] is False
    assert meta["comment_text_key_written"] is False
    assert meta["comment_text_contract"] == "passed_only"
    assert meta["completion_sentence_template_used"] is False
    assert meta["role_completed_sentence_template_used"] is False
    assert meta["input_specific_template_used"] is False
    assert meta["external_ai_used"] is False
    assert meta["local_llm_used"] is False
    assert meta["response_shape_changed"] is False
    assert meta["api_route_changed"] is False
    assert meta["db_physical_name_changed"] is False
    assert meta["rn_visible_title_changed"] is False
    assert meta["raw_input_included"] is False


def test_step7_realizes_relationship_plan_with_relation_surface_signature() -> None:
    realization = build_complete_surface_realization_v2(sentence_plan_seed=_relationship_seed())
    meta = build_complete_surface_realizer_v2_meta(sentence_plan_seed=_relationship_seed())

    assert isinstance(realization, CompleteSurfaceRealizationV2)
    assert realization.ready is True
    assert meta["status"] == "ready"
    assert meta["ready"] is True
    assert meta["surface_realizer_2_0_added"] is True
    assert meta["surface_text_generated"] is True
    assert meta["comment_text_generated"] is False
    assert meta["comment_text_key_written"] is False
    assert meta["sentence_plan_followed"] is True
    assert meta["surface_line_count"] == 3
    assert meta["surface_line_count"] == meta["sentence_plan_line_count"]
    assert "近づきたい" in meta["realized_text"]
    assert "止まる" in meta["realized_text"] or "止まりたい" in meta["realized_text"]
    assert "あなた" not in meta["realized_text"]
    assert "かもしれません" not in meta["realized_text"]
    assert set(meta["used_evidence_span_ids"]) == {"s1", "s2"}
    assert set(meta["used_phrase_unit_ids"]) == {"pu1", "pu2"}
    assert set(meta["relation_types"]) == {"approach_avoidance"}
    assert meta["surface_signature"]["signature_count"] == 3
    assert meta["surface_signature"]["same_ending_guard_passed"] is True
    assert meta["surface_signature"]["completion_sentence_template_used"] is False
    assert all(line["subject_policy_key"] == "omit_second_person_subject" for line in meta["surface_lines"])
    assert all(line["completion_sentence_template_used"] is False for line in meta["surface_lines"])
    assert all(line["raw_input_included"] is False for line in meta["surface_lines"])
    assert _contains_forbidden_raw_key(meta) is False


def test_step7_surface_lines_keep_sentence_plan_binding_ids() -> None:
    plan = build_complete_sentence_plan_v2(sentence_plan_seed=_relationship_seed())
    realization = build_complete_surface_realization_v2(sentence_plan=plan)

    assert realization.ready is True
    assert [line.sentence_id for line in realization.surface_lines] == [line.sentence_id for line in plan.sentence_plans]
    assert [line.line_role for line in realization.surface_lines] == [line.line_role for line in plan.sentence_plans]
    assert set(realization.used_evidence_span_ids) == set(plan.used_evidence_span_ids)
    assert set(realization.used_phrase_unit_ids) == set(plan.used_phrase_unit_ids)
    assert set(realization.relation_types) == set(plan.relation_types)
    grounding = realization.as_grounding_input()
    assert grounding["target_step"] == "Step8_Binding_aware_Grounding"
    assert grounding["raw_input_included"] is False
    assert len(grounding["surface_lines"]) == len(plan.sentence_plans)


def test_step7_unavailable_when_sentence_plan_is_not_source_bound() -> None:
    meta = build_complete_surface_realizer_v2_meta(
        sentence_plan_seed={
            "coverage_group": "conflict",
            "sentence_budget": 3,
            "graph_nodes": [
                {
                    "node_id": "rootless",
                    "material_id": "m-rootless",
                    "phrase_unit_id": "pu-rootless",
                    "role": "value_wish",
                    "relation_type": "contrast",
                    "source_anchor_present": False,
                }
            ],
        }
    )

    assert meta["status"] == "unavailable"
    assert meta["ready"] is False
    assert meta["surface_text_generated"] is False
    assert meta["comment_text_generated"] is False
    assert meta["comment_text_key_written"] is False
    assert meta["surface_line_count"] == 0
    assert "surface_lines_missing" in meta["validation_errors"]
    assert meta["response_shape_changed"] is False
    assert meta["raw_input_included"] is False
    assert _contains_forbidden_raw_key(meta) is False


def test_step7_long_meaning_arc_varies_endings_without_fixed_templates() -> None:
    meta = build_complete_surface_realizer_v2_meta(
        sentence_plan_seed={
            "coverage_group": "long_meaning_arc",
            "sentence_budget": 4,
            "graph_nodes": [
                {"node_id": "n1", "material_id": "m1", "phrase_unit_id": "pu1", "evidence_span_id": "s1", "role": "fatigue_accumulation", "relation_type": "pressure", "must_keep": True, "source_anchor_present": True},
                {"node_id": "n2", "material_id": "m2", "phrase_unit_id": "pu2", "evidence_span_id": "s2", "role": "value_wish", "relation_type": "contrast", "source_anchor_present": True},
                {"node_id": "n3", "material_id": "m3", "phrase_unit_id": "pu3", "evidence_span_id": "s3", "role": "small_repair", "relation_type": "recovery", "source_anchor_present": True},
                {"node_id": "n4", "material_id": "m4", "phrase_unit_id": "pu4", "evidence_span_id": "s4", "role": "hurt_core", "relation_type": "residue", "source_anchor_present": True},
            ],
        }
    )

    assert meta["status"] == "ready"
    assert meta["surface_line_count"] in {3, 4}
    assert meta["same_ending_major_count"] == 0
    assert meta["same_ending_guard_passed"] is True
    assert meta["connector_policy_applied"] is True
    assert meta["predicate_bank_applied"] is True
    assert meta["ending_policy_applied"] is True
    assert meta["distance_policy_applied"] is True
    assert meta["variation_policy_applied"] is True
    assert meta["completion_sentence_template_used"] is False
    assert meta["role_completed_sentence_template_used"] is False
    assert meta["input_specific_template_used"] is False
    assert meta["response_shape_changed"] is False
    assert _contains_forbidden_raw_key(meta) is False


def test_step7_surface_signature_helper_returns_template_guard_material() -> None:
    realization = build_complete_surface_realization_v2(sentence_plan_seed=_relationship_seed())
    signature = build_complete_surface_signature(realization)

    assert signature["version"] == "emlis.complete_surface_signature.v2"
    assert signature["signature_count"] == len(realization.surface_lines)
    assert signature["surface_signatures"]
    assert signature["same_ending_guard_passed"] is True
    assert signature["completion_sentence_template_used"] is False
    assert signature["raw_input_included"] is False
