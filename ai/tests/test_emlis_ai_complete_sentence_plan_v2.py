from __future__ import annotations

from typing import Any

from emlis_ai_complete_material_service import CompleteMaterialBundle, CompleteMaterialUnit
from emlis_ai_complete_relation_graph_service import build_complete_relation_graph
from emlis_ai_complete_sentence_planner import (
    COMPLETE_SENTENCE_PLAN_STAGE,
    COMPLETE_SENTENCE_PLANNER_VERSION,
    CompleteSentencePlanResult,
    build_complete_sentence_plan_v2,
    build_complete_sentence_plan_v2_meta,
    build_complete_sentence_planner_contract_meta,
)
from emlis_ai_complete_composer_types import CompleteSentencePlanV2
from emlis_ai_types import EvidenceSpan


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


def _unit(
    material_id: str,
    *,
    role: str,
    relation_type: str,
    must_keep: bool = False,
    evidence_span_id: str | None = None,
) -> CompleteMaterialUnit:
    span_id = evidence_span_id or f"s_{material_id}"
    return CompleteMaterialUnit(
        material_id=material_id,
        phrase_unit_id=f"pu_{material_id}",
        evidence_span_id=span_id,
        material_text=f"{role}の材料",
        role=role,
        relation_type=relation_type,
        polarity="mixed",
        must_keep=must_keep,
        source_anchor={
            "evidence_span_id": span_id,
            "source_field": "memo",
            "start_index": 0,
            "end_index": 8,
            "source_anchor_present": True,
        },
    )


def test_step6_contract_meta_is_additive_and_planner_only() -> None:
    meta = build_complete_sentence_planner_contract_meta()

    assert meta["version"] == COMPLETE_SENTENCE_PLANNER_VERSION
    assert meta["target_step"] == COMPLETE_SENTENCE_PLAN_STAGE
    assert meta["sentence_plan_2_0_added"] is True
    assert meta["sentence_planner_added"] is True
    assert meta["sentence_budget_range"] == "2..5"
    assert meta["must_include_repair_protected"] is True
    assert meta["optional_only_repair_can_trim"] is True
    assert meta["relation_line_forced_for_all_inputs"] is False
    assert meta["surface_realizer_must_follow_plan"] is True
    assert meta["comment_text_generated"] is False
    assert meta["comment_text_contract"] == "passed_only"
    assert meta["external_ai_used"] is False
    assert meta["local_llm_used"] is False
    assert meta["fixed_sentence_template_added"] is False
    assert meta["completion_sentence_templates_added"] is False
    assert meta["response_shape_changed"] is False
    assert meta["api_route_changed"] is False
    assert meta["db_physical_name_changed"] is False
    assert meta["rn_visible_title_changed"] is False
    assert meta["raw_input_included"] is False


def test_step6_builds_recovery_sentence_plan_from_relation_graph_seed() -> None:
    bundle = CompleteMaterialBundle(
        coverage_group="recovery",
        materials=(
            _unit("load", role="fatigue_accumulation", relation_type="pressure", must_keep=True),
            _unit("repair", role="small_repair", relation_type="recovery", must_keep=True),
        ),
    )
    graph = build_complete_relation_graph(material_bundle=bundle)
    plan = build_complete_sentence_plan_v2(observation_graph=graph)
    meta = build_complete_sentence_plan_v2_meta(observation_graph=graph)

    assert isinstance(plan, CompleteSentencePlanResult)
    assert isinstance(plan, CompleteSentencePlanV2)
    assert plan.usable is True
    assert meta["status"] == "ready"
    assert plan.coverage_group == "recovery"
    assert plan.sentence_budget == 3
    assert [line.line_role for line in plan.sentence_plans] == ["opening", "core", "relation"]
    assert set(plan.used_evidence_span_ids) == {"s_load", "s_repair"}
    assert set(plan.used_phrase_unit_ids) == {"pu_load", "pu_repair"}
    assert set(plan.relation_types) == {"pressure", "recovery"}
    assert meta["target_step"] == COMPLETE_SENTENCE_PLAN_STAGE
    assert meta["relation_line_present"] is True
    assert meta["sentence_binding_bundle"]["target_step"] == COMPLETE_SENTENCE_PLAN_STAGE
    assert meta["sentence_binding_bundle"]["next_step"] == "Step7_Surface_Realizer_2_0"
    assert meta["sentence_binding_bundle"]["source_step"] == COMPLETE_SENTENCE_PLAN_STAGE
    assert meta["must_include_repair_protected"] is True
    assert meta["optional_only_repair_can_trim"] is True
    assert meta["comment_text_generated"] is False
    assert meta["response_shape_changed"] is False
    assert _contains_forbidden_raw_key(meta) is False


def test_step6_short_daily_keeps_two_sentence_budget_and_avoids_relation_overinterpretation() -> None:
    seed = {
        "coverage_group": "short_daily",
        "sentence_budget": 4,
        "required_line_roles": ["opening", "core", "relation", "closing"],
        "graph_nodes": [
            {
                "node_id": "n1",
                "material_id": "m1",
                "phrase_unit_id": "pu1",
                "evidence_span_id": "s1",
                "role": "current_expression",
                "relation_type": "center",
                "focus_rank": 1,
                "must_keep": True,
                "source_anchor_present": True,
            },
            {
                "node_id": "n2",
                "material_id": "m2",
                "phrase_unit_id": "pu2",
                "evidence_span_id": "s2",
                "role": "small_wobble",
                "relation_type": "coexistence",
                "focus_rank": 2,
                "source_anchor_present": True,
            },
        ],
    }
    plan = build_complete_sentence_plan_v2(sentence_plan_seed=seed)
    meta = build_complete_sentence_plan_v2_meta(sentence_plan_seed=seed)

    assert plan.usable is True
    assert plan.coverage_group == "short_daily"
    assert plan.sentence_budget == 2
    assert [line.line_role for line in plan.sentence_plans] == ["opening", "core"]
    assert "relation" not in [line.line_role for line in plan.sentence_plans]
    assert meta["short_input_overinterpretation_guard_enabled"] is True
    assert meta["relation_line_forced_for_all_inputs"] is False
    assert meta["comment_text_generated"] is False
    assert _contains_forbidden_raw_key(meta) is False


def test_step6_long_meaning_arc_is_not_full_summary_and_uses_three_or_four_lines() -> None:
    graph = build_complete_relation_graph(
        coverage_group="long_meaning_arc",
        focus_selector_input={
            "materials": [
                {"material_id": "m1", "phrase_unit_id": "pu1", "evidence_span_id": "s1", "role": "fatigue_accumulation", "relation_type": "pressure", "must_keep": True, "source_anchor_present": True},
                {"material_id": "m2", "phrase_unit_id": "pu2", "evidence_span_id": "s2", "role": "value_wish", "relation_type": "contrast", "source_anchor_present": True},
                {"material_id": "m3", "phrase_unit_id": "pu3", "evidence_span_id": "s3", "role": "small_repair", "relation_type": "recovery", "source_anchor_present": True},
                {"material_id": "m4", "phrase_unit_id": "pu4", "evidence_span_id": "s4", "role": "hurt_core", "relation_type": "residue", "source_anchor_present": True},
                {"material_id": "m5", "phrase_unit_id": "pu5", "evidence_span_id": "s5", "role": "anticipation_loop", "relation_type": "pressure", "source_anchor_present": True},
            ]
        },
    )
    meta = build_complete_sentence_plan_v2_meta(observation_graph=graph)

    assert meta["status"] == "ready"
    assert meta["coverage_group"] == "long_meaning_arc"
    assert meta["sentence_budget"] in {3, 4}
    assert meta["sentence_budget"] >= 3
    assert meta["long_input_full_summary_blocked"] is True
    assert len(meta["sentence_plans"]) == meta["sentence_budget"]
    assert len(meta["used_evidence_span_ids"]) < 5
    assert meta["relation_line_present"] is True
    assert meta["surface_realizer_must_follow_plan"] is True
    assert meta["surface_realizer_free_invention_blocked"] is True
    assert _contains_forbidden_raw_key(meta) is False


def test_step6_marks_must_include_and_optional_repair_boundary() -> None:
    seed = {
        "coverage_group": "history_cross_core",
        "sentence_budget": 3,
        "required_line_roles": ["opening", "core", "closing"],
        "graph_nodes": [
            {
                "node_id": "n1",
                "material_id": "m1",
                "phrase_unit_id": "pu1",
                "evidence_span_id": "s1",
                "role": "known_action",
                "relation_type": "context",
                "focus_rank": 1,
                "must_keep": True,
                "source_anchor_present": True,
            },
            {
                "node_id": "n2",
                "material_id": "m2",
                "phrase_unit_id": "pu2",
                "evidence_span_id": "s2",
                "role": "safe_home",
                "relation_type": "coexistence",
                "focus_rank": 2,
                "source_anchor_present": True,
            },
        ],
        "optional_graph_nodes": [
            {
                "node_id": "n3",
                "material_id": "m3",
                "phrase_unit_id": "pu3",
                "evidence_span_id": "s3",
                "role": "small_repair",
                "relation_type": "recovery",
                "focus_rank": 3,
                "source_anchor_present": True,
            }
        ],
    }
    meta = build_complete_sentence_plan_v2_meta(sentence_plan_seed=seed)

    assert meta["status"] == "ready"
    assert "known_action" in meta["must_include_roles"]
    assert meta["must_include_repair_protected"] is True
    assert meta["optional_only_repair_can_trim"] is True
    closing = [line for line in meta["sentence_plans"] if line["line_role"] == "closing"]
    assert closing
    assert "trim_optional_only" in closing[0]["repair_policy"]
    assert closing[0]["meta"]["optional_line"] is True
    assert meta["closing_optional"] is True
    assert _contains_forbidden_raw_key(meta) is False


def test_step6_unavailable_when_source_bound_graph_nodes_are_missing() -> None:
    meta = build_complete_sentence_plan_v2_meta(
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
    assert "usable_sentence_plans_missing" in meta["validation_errors"]
    assert "evidence_span_id_missing" in meta["validation_errors"]
    assert "source_anchor_missing" in meta["validation_errors"]
    assert meta["comment_text_generated"] is False
    assert meta["response_shape_changed"] is False
    assert _contains_forbidden_raw_key(meta) is False


def test_step6_can_build_from_evidence_spans_through_prior_steps() -> None:
    meta = build_complete_sentence_plan_v2_meta(
        coverage_group="energy_recovery",
        evidence_spans=[
            EvidenceSpan(span_id="s1", raw_text="今日は仕事で疲れて、集中も切れている。", start_index=0, end_index=22, detected_type="event", source_field="memo"),
            EvidenceSpan(span_id="s2", raw_text="お茶を飲んで少し落ち着いた。", start_index=23, end_index=39, detected_type="value", source_field="memo"),
        ],
    )

    assert meta["status"] == "ready"
    assert meta["coverage_group"] == "recovery"
    assert meta["sentence_budget"] in {2, 3}
    assert meta["used_evidence_span_ids"]
    assert meta["used_phrase_unit_ids"]
    assert set(meta["relation_types"]).intersection({"pressure", "recovery"})
    assert meta["sentence_binding_bundle"]["bundle_version"] == "emlis.sentence_binding_bundle.v1"
    assert meta["sentence_binding_bundle"]["source_step"] == COMPLETE_SENTENCE_PLAN_STAGE
    assert meta["sentence_binding_bundle"]["response_shape_changed"] is False
    assert meta["sentence_binding_bundle"]["raw_input_included"] is False


def test_step6_line_meta_contains_binding_and_no_public_comment_text() -> None:
    seed = {
        "coverage_group": "relationship",
        "sentence_budget": 3,
        "graph_nodes": [
            {"node_id": "n1", "material_id": "m1", "phrase_unit_id": "pu1", "evidence_span_id": "s1", "role": "wish_to_rely", "relation_type": "approach_avoidance", "must_keep": True, "source_anchor_present": True},
            {"node_id": "n2", "material_id": "m2", "phrase_unit_id": "pu2", "evidence_span_id": "s2", "role": "burden_fear", "relation_type": "approach_avoidance", "must_keep": True, "source_anchor_present": True},
        ],
    }
    meta = build_complete_sentence_plan_v2_meta(sentence_plan_seed=seed)
    relation_lines = [line for line in meta["sentence_plans"] if line["line_role"] == "relation"]

    assert meta["status"] == "ready"
    assert relation_lines
    assert relation_lines[0]["relation_type"] == "approach_avoidance"
    assert "action_instruction" in relation_lines[0]["forbidden_surface_keys"]
    assert "relation_not_expressed" in relation_lines[0]["repair_policy"]
    assert relation_lines[0]["meta"]["relation_surface_policy"]["relation_type"] == "approach_avoidance"
    assert meta["comment_text_generated"] is False
    assert "comment_text" not in meta
    assert all("comment_text" not in line for line in meta["sentence_plans"])
    assert _contains_forbidden_raw_key(meta) is False
