# -*- coding: utf-8 -*-
from __future__ import annotations

from typing import Any, Mapping

from emlis_ai_complete_sentence_planner import (
    build_complete_sentence_binding_bundle_meta,
    build_complete_sentence_plan_v2,
    build_complete_sentence_plan_v2_meta,
)
from emlis_ai_two_stage_section_surface_plan import (
    EMLIS_TWO_STAGE_SECTION_SURFACE_PLAN_MATERIAL_ID,
    EMLIS_TWO_STAGE_SECTION_SURFACE_PLAN_SCHEMA_VERSION,
    build_two_stage_section_surface_plan,
)


def _contains_forbidden_raw_key(value: Any) -> bool:
    forbidden = {
        "raw_text",
        "raw_input",
        "input_text",
        "user_input",
        "current_input",
        "memo",
        "memo_action",
        "memo_text",
        "raw_user_text",
        "original_text",
        "source_text",
    }
    if isinstance(value, Mapping):
        return any(str(key) in forbidden or _contains_forbidden_raw_key(item) for key, item in value.items())
    if isinstance(value, (list, tuple, set)):
        return any(_contains_forbidden_raw_key(item) for item in value)
    return False


def _two_stage_plan() -> dict[str, Any]:
    role_plan = {
        "two_stage_display_required": True,
        "section_labels_required": True,
        "expected_comment_text_shape": "labelled_two_stage_text",
        "resolved_ratio": {"reason": "daily_unpleasant_reception_light"},
        "sections": [
            {
                "section_id": "observation",
                "section_role": "state_answer_observation",
                "sentence_plan_unit_count": 1,
            },
            {
                "section_id": "reception",
                "section_role": "human_follow",
                "reception_section_role": "emlis_reception",
                "sentence_plan_unit_count": 3,
                "allowed_tone_family": "natural_short_reception",
            },
        ],
    }
    return build_two_stage_section_surface_plan(
        role_plan,
        composition_contract={"two_stage_reception_surface_required": True},
    )


def _seed() -> dict[str, Any]:
    return {
        "coverage_group": "short_daily",
        "sentence_budget": 2,
        "required_line_roles": ["opening", "core"],
        "graph_nodes": [
            {
                "node_id": "reaction",
                "material_id": "reaction_material",
                "phrase_unit_id": "pu_reaction",
                "evidence_span_id": "ev_reaction",
                "role": "explicit_negative_reaction",
                "relation_type": "center",
                "focus_rank": 1,
                "must_keep": True,
                "source_anchor_present": True,
            },
            {
                "node_id": "event",
                "material_id": "event_material",
                "phrase_unit_id": "pu_event",
                "evidence_span_id": "ev_event",
                "role": "daily_event_fact",
                "relation_type": "coexistence",
                "focus_rank": 2,
                "source_anchor_present": True,
            },
        ],
    }


def test_phase16_3_complete_sentence_plan_lines_carry_two_stage_section_meta() -> None:
    plan = build_complete_sentence_plan_v2(
        sentence_plan_seed=_seed(),
        two_stage_section_surface_plan=_two_stage_plan(),
    )

    assert plan.usable is True
    assert plan.used_evidence_span_ids == ("ev_reaction", "ev_event")
    assert [line.meta["two_stage_section_id"] for line in plan.sentence_plans] == ["observation", "reception"]

    observation, reception = plan.sentence_plans
    assert observation.meta["two_stage_section_role"] == "state_answer_observation"
    assert observation.meta["two_stage_display_label"] == "見えたこと"
    assert observation.meta["two_stage_section_label_required"] is True
    assert observation.meta["two_stage_section_order_index"] == 0
    assert observation.meta["two_stage_expected_comment_text_shape"] == "labelled_two_stage_text"
    assert observation.meta["must_not_include_human_follow"] is True

    assert reception.meta["two_stage_section_role"] == "emlis_reception"
    assert reception.meta["two_stage_display_label"] == "Emlisから"
    assert reception.meta["two_stage_section_label_required"] is True
    assert reception.meta["two_stage_section_order_index"] == 1
    assert reception.meta["two_stage_expected_comment_text_shape"] == "labelled_two_stage_text"
    assert reception.meta["must_not_include_new_observation_claim"] is True
    assert reception.meta["allowed_tone_family"] == "natural_short_reception"


def test_phase16_3_complete_sentence_plan_meta_exposes_section_summary_without_raw_input() -> None:
    meta = build_complete_sentence_plan_v2_meta(
        sentence_plan_seed=_seed(),
        two_stage_section_surface_plan=_two_stage_plan(),
        meta={"memo": "raw memo must be stripped", "safe_trace": "kept"},
    )

    assert meta["status"] == "ready"
    assert meta["two_stage_section_surface_plan_connected"] is True
    assert meta["two_stage_section_meta_propagated"] is True
    assert meta["two_stage_section_surface_plan_material_id"] == EMLIS_TWO_STAGE_SECTION_SURFACE_PLAN_MATERIAL_ID
    assert meta["two_stage_section_surface_plan_schema_version"] == EMLIS_TWO_STAGE_SECTION_SURFACE_PLAN_SCHEMA_VERSION
    assert meta["two_stage_section_order"] == ["observation", "reception"]
    assert meta["two_stage_section_line_counts"] == {"observation": 1, "reception": 1}
    assert meta["two_stage_observation_section_present"] is True
    assert meta["two_stage_reception_section_present"] is True
    assert meta["comment_text_generated"] is False
    assert meta["raw_input_included"] is False
    assert _contains_forbidden_raw_key(meta) is False

    line_meta = [line["meta"] for line in meta["sentence_plans"]]
    assert [item["two_stage_section_id"] for item in line_meta] == ["observation", "reception"]
    assert all(item["comment_text_generated"] is False for item in line_meta)


def test_phase16_3_sentence_binding_bundle_keeps_section_meta_and_evidence_ids() -> None:
    plan = build_complete_sentence_plan_v2(
        sentence_plan_seed=_seed(),
        two_stage_section_surface_plan=_two_stage_plan(),
    )
    bundle = build_complete_sentence_binding_bundle_meta(plan)

    assert bundle["two_stage_section_meta_propagated"] is True
    assert bundle["two_stage_section_line_counts"] == {"observation": 1, "reception": 1}
    assert bundle["used_evidence_span_ids"] == ["ev_reaction", "ev_event"]
    assert bundle["used_phrase_unit_ids"] == ["pu_reaction", "pu_event"]
    assert [row["meta"]["two_stage_section_id"] for row in bundle["sentence_bindings"]] == [
        "observation",
        "reception",
    ]
    assert bundle["response_shape_changed"] is False
    assert bundle["raw_input_included"] is False
    assert _contains_forbidden_raw_key(bundle) is False
