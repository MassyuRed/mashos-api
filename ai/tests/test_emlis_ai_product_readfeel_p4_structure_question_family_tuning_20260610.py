# -*- coding: utf-8 -*-
from __future__ import annotations

import json
from typing import Any

from emlis_ai_complete_sentence_planner import build_complete_sentence_plan_v2
from emlis_ai_complete_surface_realizer import build_complete_surface_realization_v2
from emlis_ai_reception_mode_resolver import (
    MODE_STRUCTURE,
    resolve_emlis_reception_mode_meta,
)
from emlis_ai_shared_reception_evidence import build_emlis_shared_reception_evidence_meta
from emlis_ai_state_answer_ratio_policy import build_emlis_ai_state_answer_ratio_policy
from emlis_ai_two_stage_section_surface_plan import build_two_stage_section_surface_plan
from test_emlis_ai_complete_sentence_plan_two_stage_section_meta import _contains_forbidden_raw_key


def _structure_question_current_input() -> dict[str, Any]:
    return {
        "id": "p4-7-structure-question-current",
        "created_at": "2026-06-10T10:00:00+09:00",
        "memo": "なぜ同じ場面で意見を言おうとすると止まって、あとから引っかかるのか知りたい",
        "memo_action": "会議で話そうとしたけれど途中で詰まってしまい、帰ってからも考え続けた",
        "emotion_details": [{"type": "不安", "strength": "medium"}],
        "emotions": ["不安"],
        "category": ["仕事", "人間関係"],
        "is_secret": False,
    }


def _structure_question_two_stage_plan() -> dict[str, Any]:
    role_plan = {
        "two_stage_display_required": True,
        "section_labels_required": True,
        "expected_comment_text_shape": "labelled_two_stage_text",
        "resolved_ratio": {"reason": "structure_question_observation_thickened"},
        "sections": [
            {
                "section_id": "observation",
                "section_role": "structure_question_observation",
                "sentence_plan_unit_count": 4,
                "claim_strength": "single_input_soft",
            },
            {
                "section_id": "reception",
                "section_role": "human_follow",
                "reception_section_role": "structure_question_soft_reception",
                "sentence_plan_unit_count": 2,
                "allowed_tone_family": "calm_observation_with_soft_reception",
            },
        ],
    }
    return build_two_stage_section_surface_plan(
        role_plan,
        composition_contract={
            "two_stage_reception_surface_required": True,
            "reception_mode_id": MODE_STRUCTURE,
        },
    )


def _structure_question_seed() -> dict[str, Any]:
    return {
        "coverage_group": "structure_question",
        "sentence_budget": 3,
        "required_line_roles": ["opening", "core", "relation"],
        "graph_nodes": [
            {
                "node_id": "question_core",
                "material_id": "structure_question_material",
                "phrase_unit_id": "pu_structure_question",
                "evidence_span_id": "ev_structure_question",
                "role": "structure_question_anchor",
                "relation_type": "center",
                "focus_rank": 1,
                "must_keep": True,
                "source_anchor_present": True,
            },
            {
                "node_id": "visible_state",
                "material_id": "visible_relation_or_state_material",
                "phrase_unit_id": "pu_visible_state",
                "evidence_span_id": "ev_visible_state",
                "role": "visible_relation_or_state_anchor",
                "relation_type": "approach_avoidance",
                "focus_rank": 2,
                "source_anchor_present": True,
            },
            {
                "node_id": "unresolved_conflict",
                "material_id": "unresolved_or_conflict_material",
                "phrase_unit_id": "pu_unresolved_conflict",
                "evidence_span_id": "ev_unresolved_conflict",
                "role": "unresolved_or_conflict_anchor",
                "relation_type": "approach_avoidance",
                "focus_rank": 3,
                "source_anchor_present": True,
            },
        ],
    }


def _structure_question_surface_realization() -> Any:
    sentence_plan = build_complete_sentence_plan_v2(
        sentence_plan_seed=_structure_question_seed(),
        two_stage_section_surface_plan=_structure_question_two_stage_plan(),
    )
    return build_complete_surface_realization_v2(sentence_plan=sentence_plan)


def test_p4_7_structure_question_material_routes_to_structure_without_low_information_or_comfort_escape() -> None:
    current_input = _structure_question_current_input()

    evidence = build_emlis_shared_reception_evidence_meta(current_input)
    resolver = resolve_emlis_reception_mode_meta(current_input)

    assert evidence["event_fact_present"] is True
    assert evidence["reaction_present"] is True
    assert evidence["structure_question_requested"] is True
    assert evidence["structure_question_anchor_ready"] is True
    assert evidence["structure_question_visible_relation_or_state_anchor_ready"] is True
    assert evidence["structure_question_unresolved_or_conflict_anchor_ready"] is True
    assert "structure_question_observation" in evidence["reception_candidate_mode_ids"]

    assert resolver["reception_mode"] == MODE_STRUCTURE
    assert resolver["low_information_question_required"] is False
    assert resolver["question_required"] is False
    assert resolver["structure_question_anchor_ready"] is True
    assert resolver["structure_question_current_only_surface_required"] is True
    assert resolver["structure_question_question_only_surface_allowed"] is False
    assert resolver["structure_question_comfort_only_allowed"] is False
    assert resolver["structure_question_cause_overclaim_allowed"] is False
    assert resolver["structure_question_personality_claim_allowed"] is False
    assert resolver["structure_question_other_person_intent_claim_allowed"] is False
    assert resolver["structure_question_p6_deep_insight_applied"] is False
    assert resolver["structure_question_p6_backlog_marker_only"] is True
    assert resolver["mode_selection_contract"]["structure_question_p6_deep_insight_not_applied_in_p4"] is True
    assert resolver["comment_text_generated"] is False
    assert resolver["public_response_key_added"] is False

    encoded = json.dumps(resolver, ensure_ascii=False, sort_keys=True)
    assert current_input["memo"] not in encoded
    assert current_input["memo_action"] not in encoded
    assert current_input["id"] not in encoded
    assert _contains_forbidden_raw_key(resolver) is False


def test_p4_7_structure_question_ratio_and_section_policy_are_60_70_observation_30_40_reception() -> None:
    meta = build_emlis_ai_state_answer_ratio_policy(_structure_question_current_input()).as_meta()
    ratio = meta["resolved_ratio"]
    unit_plan = meta["ratio_basis"]["section_role_unit_plan"]
    context = meta["resolver_context"]
    section_plan = _structure_question_two_stage_plan()

    assert ratio["reason"] == "structure_question_observation_thickened"
    assert ratio["range_key"] == "structure_question"
    assert ratio["observation"] == 0.70
    assert ratio["human_follow"] == 0.30
    assert 0.60 <= ratio["observation"] <= 0.70
    assert 0.30 <= ratio["human_follow"] <= 0.40
    assert ratio["observation"] > ratio["human_follow"]
    assert unit_plan["observation_section_role"] == "structure_question_observation"
    assert unit_plan["human_follow_section_role"] == "structure_question_soft_reception"
    assert context["p4_7_structure_question_ratio_policy_aligned"] is True
    assert context["p4_7_structure_question_observation_ratio_range"] == "60_70"
    assert context["p4_7_structure_question_reception_ratio_range"] == "30_40"
    assert context["p4_7_structure_question_comfort_only_forbidden"] is True
    assert context["p4_7_structure_question_p6_deep_insight_blocked"] is True

    assert section_plan["reception_mode_id"] == MODE_STRUCTURE
    assert section_plan["mode_section_budget"] == {
        "observation_min": 2,
        "observation_max": 2,
        "reception_min": 1,
        "reception_max": 1,
    }
    assert section_plan["p4_7_structure_question_family_tuning_ready"] is True
    assert section_plan["p4_7_structure_question_observation_ratio_section_aligned"] is True
    assert "structure_question_anchor_required" in section_plan["sections"][0]["allowed_surface_intents"]
    assert "visible_relation_or_state_anchor_required" in section_plan["sections"][0]["allowed_surface_intents"]
    assert "unresolved_or_conflict_anchor_required" in section_plan["sections"][0]["allowed_surface_intents"]
    assert "structure_question_soft_reception" in section_plan["sections"][1]["allowed_surface_intents"]
    assert "question_only_forbidden" in section_plan["sections"][1]["allowed_surface_intents"]
    assert section_plan["public_response_key_added"] is False
    assert section_plan["rn_visible_contract_changed"] is False


def test_p4_7_structure_question_surface_observes_relation_without_question_only_comfort_or_p6_over_insight() -> None:
    realization = _structure_question_surface_realization()

    assert realization.ready is True
    comment_text = realization.comment_text
    assert comment_text.startswith("見えたこと：\n")
    assert "\n\nEmlisから：\n" in comment_text
    assert "同じ入力" in comment_text or "関係" in comment_text
    assert "受け取れます" in comment_text
    assert "?" not in comment_text
    assert "？" not in comment_text
    assert "大丈夫です" not in comment_text
    assert "原因は" not in comment_text
    assert "性格" not in comment_text
    assert "相手の意図" not in comment_text
    assert "してください" not in comment_text
    assert "診断" not in comment_text
    assert "トラウマ" not in comment_text
    assert "価値線" not in comment_text

    two_stage = realization.two_stage_surface_realization
    assert two_stage["section_line_counts"] == {"observation": 2, "reception": 1}
    summary = two_stage["structure_question_surface_quality"]
    assert summary["p4_7_structure_question_family_tuning_applied"] is True
    assert summary["p4_7_structure_question_observation_ratio_policy_aligned"] is True
    assert summary["p4_7_structure_question_structure_question_anchor_retained"] is True
    assert summary["p4_7_structure_question_visible_relation_or_state_anchor_retained"] is True
    assert summary["p4_7_structure_question_unresolved_or_conflict_anchor_retained"] is True
    assert summary["p4_7_structure_question_emlis_reception_anchor_retained"] is True
    assert summary["p4_7_structure_question_question_only_surface_blocked"] is True
    assert summary["p4_7_structure_question_comfort_only_blocked"] is True
    assert summary["p4_7_structure_question_overclaim_blocked"] is True
    assert summary["p4_7_structure_question_p6_over_insight_blocked"] is True
    assert summary["p4_7_structure_question_p6_backlog_marker_only"] is True
    assert summary["forbidden_surface_hits"] == []
    assert summary["comment_text_body_included"] is False
    assert summary["surface_text_body_included"] is False
    assert summary["raw_input_included"] is False
    assert summary["public_response_key_added"] is False
    assert summary["rn_visible_contract_changed"] is False

    meta = realization.as_meta(include_realized_text=False)
    assert meta["p4_7_structure_question_family_tuning_applied"] is True
    assert meta["structure_question_surface_quality_applied"] is True
    assert meta["structure_question_surface_quality_passed"] is True
    assert meta["structure_question_surface_quality_forbidden_hits"] == []
    assert _contains_forbidden_raw_key(meta) is False
    assert meta["comment_text_body_included"] is False
    assert meta.get("public_response_key_added", False) is False
