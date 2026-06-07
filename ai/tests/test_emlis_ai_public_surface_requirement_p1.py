# -*- coding: utf-8 -*-
from __future__ import annotations

"""P1 tests for public surface requirement decision.

P1 only adds a body-free decision before candidate adoption.  It must not change
RN/API/DB contracts, must not relax gates, and must not render public text.
"""

from collections.abc import Mapping, Sequence
from typing import Any

from emlis_ai_gate_recovery_public_candidate_builder import (
    build_public_candidate_after_gate_recovery,
)
from emlis_ai_public_surface_requirement import (
    LABELLED_TWO_STAGE_OBSERVATION_MARKER,
    LABELLED_TWO_STAGE_RECEPTION_BOUNDARY,
    PUBLIC_SURFACE_REQUIREMENT_SCHEMA_VERSION,
    SURFACE_REQUIREMENT_LABELLED_TWO_STAGE,
    SURFACE_REQUIREMENT_LOW_INFORMATION_OBSERVATION,
    SURFACE_REQUIREMENT_PLAIN_STATE_ANSWER,
    SURFACE_REQUIREMENT_SELF_DENIAL_SAFE_STATE_ANSWER,
    assert_public_surface_requirement_decision,
    public_surface_requirement_public_summary,
    resolve_public_surface_requirement,
)
from emlis_ai_types import ConversationComposerCandidate, DisplayDecision, SafetyBoundaryReport


_FORBIDDEN_META_KEYS = {
    "raw_input",
    "current_input",
    "memo",
    "memo_action",
    "comment_text",
    "commentText",
    "candidate_comment_text",
    "public_comment_text",
    "body",
    "text",
    "candidate_body",
    "surface_body",
}


def _assert_body_free(meta: Mapping[str, Any]) -> None:
    def walk(value: Any) -> None:
        if isinstance(value, Mapping):
            assert not (set(value.keys()) & _FORBIDDEN_META_KEYS)
            for child in value.values():
                walk(child)
        elif isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
            for child in value:
                walk(child)

    walk(meta)


def _rich_current_input() -> dict[str, Any]:
    return {
        "memo": (
            "仕事で相手の言い方に引っかかったあと、嬉しさもあるのに、境界線をどこに置けばいいのかが"
            "ずっと残っている。自分が悪いだけなのか、相手との距離を考え直す合図なのか、まだ判断できない。"
        ),
        "memo_action": "すぐに返事せず、明日は一度、自分が守りたい距離を書き出してから話す。",
        "emotions": ["喜び", "違和感", "不安"],
        "category": ["仕事", "人間関係"],
    }


def _eligible_material_route() -> dict[str, Any]:
    return {
        "material_quality": "eligible",
        "material_sufficient": True,
        "visible_material_slots": ["event", "emotion_direction", "action", "relationship"],
        "unknown_slots": ["cause"],
        "relation_material_ids": ["relationship_boundary_state_answer"],
    }


def _relationship_transition_current_input() -> dict[str, Any]:
    return {
        "memo": (
            "大切な人との関係が終わったあとも、そばにいてくれる友達の優しさを受け取れている。"
            "その優しさに安心するだけでなく、自分も別の形で返したい気持ちが強くなっている。"
            "関係の区切りと、次に向かう変化が同時に起きているように感じている。"
        ),
        "memo_action": "関係の終わりを受け止めつつ、支えてくれた友達に感謝を伝えようとしている。",
        "emotions": ["喜び", "悲しみ"],
        "category": ["人間関係", "価値観"],
    }


def _relationship_transition_material_route() -> dict[str, Any]:
    return {
        "safety_triage_kind": "safe_observation",
        "response_kind": "normal_observation",
        "public_observation_status": "passed",
        "comment_text_required": True,
        "public_input_feedback_allowed": True,
        "material_quality": "eligible",
        "material_sufficient": True,
        "visible_material_slots": [
            "event",
            "action",
            "emotion_direction",
            "relationship",
            "target",
            "change",
            "time",
            "value",
        ],
        "unknown_slots": ["cause"],
        "relation_material_ids": [
            "relationship_end",
            "support_from_other",
            "gratitude_or_return_intent",
            "relationship_material",
            "support_received_material",
        ],
        "generic_relation_material_ids": [
            "relationship_end",
            "support_from_other",
            "gratitude_or_return_intent",
            "relationship_material",
            "support_received_material",
        ],
    }


def _two_stage_composer_meta() -> dict[str, Any]:
    return {
        "composer_source": "ai_generated",
        "candidate_status": "generated",
        "state_answer_two_stage_display_required": True,
        "state_answer_two_stage_reception_surface_required": True,
        "state_answer_joined_comment_text_required": True,
        "state_answer_section_labels_required": True,
        "state_answer_expected_comment_text_shape": "labelled_two_stage_text",
        "state_answer_surface_contract": {
            "surface_requirement_family": "labelled_two_stage",
            "raw_input_included": False,
            "comment_text_body_included": False,
        },
        "raw_input_included": False,
        "comment_text_body_included": False,
    }


def _surface_failed_display_decision() -> DisplayDecision:
    return DisplayDecision(
        observation_status="rejected",
        comment_text="",
        rejection_reasons=[
            "visible_surface_acceptance_gate_failed",
            "surface_relation_skeleton_major",
        ],
        trace_id="p1-public-surface-requirement",
    )


def _original_candidate_with_two_stage_meta() -> ConversationComposerCandidate:
    return ConversationComposerCandidate(
        comment_text="この入力では、境界線と嬉しさが同時に残っています。",
        composer_source="ai_generated",
        status="generated",
        ai_generated=True,
        trace_id="p1-original-candidate",
        attempt_count=1,
        confidence=0.83,
        rejection_reasons=[],
        request_schema_version="emlis.composer.request.v1",
        response_schema_version="cocolon.emlis.complete_composer.response.v1",
        fixed_string_renderer_used=False,
        composer_model="complete_initial_composer_v1",
        generation_method="complete_initial_composer",
        coverage_scope="current_input_only",
        generation_scope="current_input_only",
        composer_meta=_two_stage_composer_meta(),
        used_claim_ids=["claim_relationship_boundary"],
        used_relation_ids=["relationship_boundary_state_answer"],
    )


def test_p1_two_stage_meta_requires_labelled_surface_body_free() -> None:
    decision = resolve_public_surface_requirement(
        current_input=_rich_current_input(),
        material_route=_eligible_material_route(),
        composer_meta=_two_stage_composer_meta(),
        diagnostic_summary={"reason_codes": ["relationship_boundary", "two_stage_required"]},
    )

    assert_public_surface_requirement_decision(decision)
    assert decision["schema_version"] == PUBLIC_SURFACE_REQUIREMENT_SCHEMA_VERSION
    assert decision["surface_requirement_family"] == SURFACE_REQUIREMENT_LABELLED_TWO_STAGE
    assert decision["two_stage_required"] is True
    assert decision["plain_state_answer_allowed"] is False
    assert decision["low_information_allowed"] is False
    assert decision["required_comment_text_shape"]["starts_with"] == LABELLED_TWO_STAGE_OBSERVATION_MARKER
    assert decision["required_comment_text_shape"]["contains_boundary"] == LABELLED_TWO_STAGE_RECEPTION_BOUNDARY
    assert decision["public_contract"]["rn_visible_contract_changed"] is False
    assert decision["gate_policy"]["display_gate_relaxed"] is False
    assert decision["raw_input_included"] is False
    assert decision["comment_text_body_included"] is False
    _assert_body_free(decision)


def test_p1_relationship_transition_material_requires_labelled_two_stage_without_case_route() -> None:
    decision = resolve_public_surface_requirement(
        current_input=_relationship_transition_current_input(),
        material_route=_relationship_transition_material_route(),
        composer_meta={
            "composer_source": "unavailable",
            "candidate_status": "unavailable",
            "primary_reason": "limited_composer_shallow_empty_candidate",
            "raw_input_included": False,
            "comment_text_body_included": False,
        },
        diagnostic_summary={"primary_reason": "limited_composer_shallow_empty_candidate"},
    )

    assert_public_surface_requirement_decision(decision)
    assert decision["surface_requirement_family"] == SURFACE_REQUIREMENT_LABELLED_TWO_STAGE
    assert decision["two_stage_required"] is True
    assert decision["plain_state_answer_allowed"] is False
    assert decision["low_information_allowed"] is False
    assert "material_relationship_transition_two_stage" in decision["decision_sources"]
    assert "fixture_family_meta" not in decision["decision_sources"]
    assert decision["input_material_classification"]["high_information_input"] is True
    assert decision["required_comment_text_shape"]["starts_with"] == LABELLED_TWO_STAGE_OBSERVATION_MARKER
    assert decision["required_comment_text_shape"]["contains_boundary"] == LABELLED_TWO_STAGE_RECEPTION_BOUNDARY
    assert decision["public_contract"]["rn_visible_contract_changed"] is False
    assert decision["gate_policy"]["display_gate_relaxed"] is False
    _assert_body_free(decision)


def test_p1_relationship_transition_rule_does_not_promote_without_relationship_slot() -> None:
    material_route = _relationship_transition_material_route()
    material_route["visible_material_slots"] = ["event", "action", "target", "change", "value"]

    decision = resolve_public_surface_requirement(
        current_input=_relationship_transition_current_input(),
        material_route=material_route,
        composer_meta={"composer_source": "unavailable", "candidate_status": "unavailable"},
        diagnostic_summary={},
    )

    assert decision["surface_requirement_family"] == SURFACE_REQUIREMENT_PLAIN_STATE_ANSWER
    assert decision["two_stage_required"] is False
    assert decision["plain_state_answer_allowed"] is True
    assert "material_relationship_transition_two_stage" not in decision["decision_sources"]
    _assert_body_free(decision)


def test_p1_relationship_transition_rule_does_not_override_self_denial_safe_state_answer() -> None:
    material_route = _relationship_transition_material_route()
    material_route["surface_requirement_family"] = SURFACE_REQUIREMENT_SELF_DENIAL_SAFE_STATE_ANSWER

    decision = resolve_public_surface_requirement(
        current_input=_relationship_transition_current_input(),
        material_route=material_route,
        composer_meta={},
        diagnostic_summary={},
    )

    assert decision["surface_requirement_family"] == SURFACE_REQUIREMENT_SELF_DENIAL_SAFE_STATE_ANSWER
    assert decision["two_stage_required"] is False
    assert decision["plain_state_answer_allowed"] is False
    assert "material_relationship_transition_two_stage" not in decision["decision_sources"]
    _assert_body_free(decision)


def test_p1_low_information_material_does_not_become_plain_or_two_stage() -> None:
    decision = resolve_public_surface_requirement(
        current_input={"memo": "少し疲れた", "emotions": ["疲れ"], "category": ["体調"]},
        material_route={"material_quality": "low_information", "visible_material_slots": ["emotion"]},
        composer_meta={},
        diagnostic_summary={},
    )

    assert decision["surface_requirement_family"] == SURFACE_REQUIREMENT_LOW_INFORMATION_OBSERVATION
    assert decision["two_stage_required"] is False
    assert decision["plain_state_answer_allowed"] is False
    assert decision["low_information_allowed"] is True
    _assert_body_free(decision)


def test_p1_plain_state_answer_allowed_for_non_two_stage_normal_material() -> None:
    decision = resolve_public_surface_requirement(
        current_input={
            "memo": "今日は少し落ち着いていた。",
            "memo_action": "夜は早く寝る。",
            "emotions": ["安心"],
            "category": ["生活"],
        },
        material_route={"material_quality": "eligible", "visible_material_slots": ["event", "action"]},
        composer_meta={"composer_source": "ai_generated", "candidate_status": "generated"},
        diagnostic_summary={},
    )

    assert decision["surface_requirement_family"] == SURFACE_REQUIREMENT_PLAIN_STATE_ANSWER
    assert decision["two_stage_required"] is False
    assert decision["plain_state_answer_allowed"] is True
    assert decision["low_information_allowed"] is False
    _assert_body_free(decision)


def test_p1_builder_embeds_sanitized_surface_requirement_in_recovery_plan() -> None:
    result = build_public_candidate_after_gate_recovery(
        current_input=_rich_current_input(),
        material_route=_eligible_material_route(),
        original_composer_candidate=_original_candidate_with_two_stage_meta(),
        original_display_decision=_surface_failed_display_decision(),
        safety_triage_kind="safe_observation",
        safety_report=SafetyBoundaryReport(requires_block=False),
        recovery_plan={},
        trace_id="p1-builder-surface-requirement",
    )

    plan = result.as_meta()["recovery_plan"]
    requirement = plan["surface_requirement"]
    assert requirement == public_surface_requirement_public_summary(requirement)
    assert requirement["surface_requirement_family"] == SURFACE_REQUIREMENT_LABELLED_TWO_STAGE
    assert requirement["two_stage_required"] is True
    assert requirement["plain_state_answer_allowed"] is False
    assert requirement["public_contract"]["rn_visible_contract_changed"] is False
    assert requirement["gate_policy"]["display_gate_relaxed"] is False
    _assert_body_free(plan)
