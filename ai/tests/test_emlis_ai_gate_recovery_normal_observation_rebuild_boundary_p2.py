# -*- coding: utf-8 -*-
from __future__ import annotations

"""P2: normal_observation_rebuild must not satisfy labelled two-stage surfaces."""

from collections.abc import Mapping, Sequence
from typing import Any

from emlis_ai_gate_recovery_public_candidate_builder import (
    NORMAL_OBSERVATION_REBUILD_COMPOSER_MODEL,
    NORMAL_OBSERVATION_REBUILD_GENERATION_METHOD,
    build_public_candidate_after_gate_recovery,
)
from emlis_ai_gate_recovery_public_constants import (
    BLOCKER_NORMAL_OBSERVATION_REBUILD_BLOCKED_TWO_STAGE_REQUIRED,
    CANDIDATE_SOURCE_KIND_BOUNDED_REPAIRED_ORIGINAL_CANDIDATE,
    CANDIDATE_SOURCE_KIND_LABELLED_TWO_STAGE_SURFACE_RECOMPOSITION_CANDIDATE,
    CANDIDATE_SOURCE_KIND_NORMAL_OBSERVATION_REBUILD_CANDIDATE,
    PUBLIC_SURFACE_ROLE_PUBLIC_OBSERVATION,
)
from emlis_ai_public_surface_requirement import (
    SURFACE_REQUIREMENT_LABELLED_TWO_STAGE,
    SURFACE_REQUIREMENT_PLAIN_STATE_ANSWER,
    public_surface_requirement_public_summary,
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


def _rich_two_stage_input() -> dict[str, Any]:
    return {
        "memo": (
            "仕事で相手の言い方に引っかかったあと、嬉しさもあるのに、境界線をどこに置けばいいのかが"
            "ずっと残っている。自分が悪いだけなのか、相手との距離を考え直す合図なのか、まだ判断できない。"
        ),
        "memo_action": "すぐに返事せず、明日は一度、自分が守りたい距離を書き出してから話す。",
        "emotions": ["喜び", "違和感", "不安"],
        "category": ["仕事", "人間関係"],
    }


def _plain_input() -> dict[str, Any]:
    return {
        "memo": "今日は仕事の話を受けたあと、納得したい気持ちと引っかかりが残っている。",
        "memo_action": "明日は一度、事実だけを書き出してから返事を考える。",
        "emotions": ["不安", "違和感"],
        "category": ["仕事"],
    }


def _eligible_material_route(*, relation_required: bool = True) -> dict[str, Any]:
    return {
        "material_quality": "eligible",
        "material_sufficient": True,
        "visible_material_slots": ["event", "emotion_direction", "action", "relationship"],
        "unknown_slots": ["cause"],
        "relation_material_ids": (
            ["relationship_boundary_state_answer"] if relation_required else ["work_state_answer"]
        ),
    }


def _surface_failed_display_decision() -> DisplayDecision:
    return DisplayDecision(
        observation_status="rejected",
        comment_text="",
        rejection_reasons=[
            "visible_surface_acceptance_gate_failed",
            "surface_relation_skeleton_major",
            "surface_grammar_warning",
        ],
        trace_id="p2-normal-observation-rebuild-boundary",
    )


def _two_stage_composer_meta() -> dict[str, Any]:
    return {
        "candidate_source_kind": "complete_initial_composer",
        "public_surface_role": PUBLIC_SURFACE_ROLE_PUBLIC_OBSERVATION,
        "composer_source": "ai_generated",
        "candidate_status": "generated",
        "state_answer_two_stage_display_required": True,
        "state_answer_two_stage_reception_surface_required": True,
        "state_answer_joined_comment_text_required": True,
        "state_answer_section_labels_required": True,
        "state_answer_expected_comment_text_shape": "labelled_two_stage_text",
        "state_answer_surface_contract": {
            "surface_requirement_family": SURFACE_REQUIREMENT_LABELLED_TWO_STAGE,
            "raw_input_included": False,
            "comment_text_body_included": False,
        },
        "raw_input_included": False,
        "comment_text_body_included": False,
    }


def _plain_composer_meta() -> dict[str, Any]:
    return {
        "candidate_source_kind": "complete_initial_composer",
        "public_surface_role": PUBLIC_SURFACE_ROLE_PUBLIC_OBSERVATION,
        "composer_source": "ai_generated",
        "candidate_status": "generated",
        "raw_input_included": False,
        "comment_text_body_included": False,
    }


def _original_candidate(*, two_stage_required: bool) -> ConversationComposerCandidate:
    return ConversationComposerCandidate(
        comment_text=(
            "この入力では、仕事の話に対して同じ流れの中で、納得したい気持ちと"
            "引っかかりが同じ場所に残っています。片方だけに減らさず、状態が一色ではありません。"
        ),
        composer_source="ai_generated",
        status="generated",
        ai_generated=True,
        trace_id="p2-original-candidate",
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
        composer_meta=_two_stage_composer_meta() if two_stage_required else _plain_composer_meta(),
        used_claim_ids=["claim_work_aftertalk_state", "claim_reply_action"],
        used_relation_ids=["relationship_boundary_state_answer"],
    )


def _normal_rebuild_candidate() -> ConversationComposerCandidate:
    return ConversationComposerCandidate(
        comment_text=(
            "この記録では、仕事の話を受け取ったあとも、納得したい気持ちと引っかかりが"
            "まだ落ち着ききっていない状態として見えます。返事を急がず、事実を分けて"
            "見ようとしているところもEmlisは受け取りました。"
        ),
        composer_source="ai_generated",
        status="generated",
        ai_generated=True,
        trace_id="p2-normal-rebuild-candidate",
        attempt_count=1,
        confidence=0.78,
        rejection_reasons=[],
        request_schema_version="emlis.composer.request.v1",
        response_schema_version="cocolon.emlis.phase20_8.normal_observation_rebuild.response.v1",
        fixed_string_renderer_used=False,
        composer_model=NORMAL_OBSERVATION_REBUILD_COMPOSER_MODEL,
        generation_method=NORMAL_OBSERVATION_REBUILD_GENERATION_METHOD,
        coverage_scope="current_input_normal_observation_rebuild",
        generation_scope="current_input_only",
        composer_meta={
            "candidate_source_kind": CANDIDATE_SOURCE_KIND_NORMAL_OBSERVATION_REBUILD_CANDIDATE,
            "public_surface_role": PUBLIC_SURFACE_ROLE_PUBLIC_OBSERVATION,
            "surface_requirement_family": SURFACE_REQUIREMENT_PLAIN_STATE_ANSWER,
            "two_stage_required": False,
            "plain_state_answer_allowed": True,
            "raw_input_included": False,
            "comment_text_body_included": False,
        },
        used_claim_ids=["claim_work_aftertalk_state", "claim_reply_action"],
        used_relation_ids=["relationship_boundary_state_answer"],
    )


def _labelled_surface_requirement_summary() -> dict[str, Any]:
    return public_surface_requirement_public_summary(
        {
            "surface_requirement_family": SURFACE_REQUIREMENT_LABELLED_TWO_STAGE,
            "two_stage_required": True,
            "plain_state_answer_allowed": False,
            "low_information_allowed": False,
            "decision_sources": ["p2_test_two_stage_required"],
            "material_quality_family": "eligible",
            "raw_input_included": False,
            "comment_text_body_included": False,
        }
    )


def test_p2_default_plan_blocks_normal_rebuild_when_two_stage_required() -> None:
    result = build_public_candidate_after_gate_recovery(
        current_input=_rich_two_stage_input(),
        material_route=_eligible_material_route(relation_required=True),
        original_composer_candidate=_original_candidate(two_stage_required=True),
        original_display_decision=_surface_failed_display_decision(),
        safety_triage_kind="safe_observation",
        safety_report=SafetyBoundaryReport(requires_block=False),
        recovery_plan={},
        trace_id="p2-default-two-stage-blocks-normal-rebuild",
    )

    meta = result.as_meta()
    plan = meta["recovery_plan"]
    assert plan["surface_requirement"]["surface_requirement_family"] == SURFACE_REQUIREMENT_LABELLED_TWO_STAGE
    assert plan["surface_requirement"]["two_stage_required"] is True
    assert plan["target_public_candidate_source"] == CANDIDATE_SOURCE_KIND_LABELLED_TWO_STAGE_SURFACE_RECOMPOSITION_CANDIDATE
    assert CANDIDATE_SOURCE_KIND_NORMAL_OBSERVATION_REBUILD_CANDIDATE not in plan[
        "fallback_public_candidate_source_order"
    ]
    assert BLOCKER_NORMAL_OBSERVATION_REBUILD_BLOCKED_TWO_STAGE_REQUIRED in plan[
        "blockers_if_no_public_candidate"
    ]
    assert result.source_kind == CANDIDATE_SOURCE_KIND_LABELLED_TWO_STAGE_SURFACE_RECOMPOSITION_CANDIDATE
    _assert_body_free(meta)


def test_p2_explicit_normal_rebuild_candidate_is_not_selected_for_labelled_two_stage() -> None:
    result = build_public_candidate_after_gate_recovery(
        current_input=_rich_two_stage_input(),
        material_route=_eligible_material_route(relation_required=True),
        original_composer_candidate=_original_candidate(two_stage_required=True),
        original_display_decision=_surface_failed_display_decision(),
        safety_triage_kind="safe_observation",
        safety_report=SafetyBoundaryReport(requires_block=False),
        recovery_plan={
            "surface_requirement": _labelled_surface_requirement_summary(),
            "target_public_candidate_source": CANDIDATE_SOURCE_KIND_NORMAL_OBSERVATION_REBUILD_CANDIDATE,
            "fallback_public_candidate_source_order": [
                CANDIDATE_SOURCE_KIND_NORMAL_OBSERVATION_REBUILD_CANDIDATE,
                CANDIDATE_SOURCE_KIND_BOUNDED_REPAIRED_ORIGINAL_CANDIDATE,
            ],
        },
        normal_observation_rebuild_candidate=_normal_rebuild_candidate(),
        trace_id="p2-explicit-two-stage-does-not-select-normal-rebuild",
    )

    meta = result.as_meta()
    plan = meta["recovery_plan"]
    assert plan["surface_requirement"]["two_stage_required"] is True
    assert plan["target_public_candidate_source"] != CANDIDATE_SOURCE_KIND_NORMAL_OBSERVATION_REBUILD_CANDIDATE
    assert CANDIDATE_SOURCE_KIND_NORMAL_OBSERVATION_REBUILD_CANDIDATE not in plan[
        "fallback_public_candidate_source_order"
    ]
    assert BLOCKER_NORMAL_OBSERVATION_REBUILD_BLOCKED_TWO_STAGE_REQUIRED in plan[
        "blockers_if_no_public_candidate"
    ]
    assert result.source_kind == CANDIDATE_SOURCE_KIND_LABELLED_TWO_STAGE_SURFACE_RECOMPOSITION_CANDIDATE
    if result.candidate is not None:
        assert result.candidate.composer_model != NORMAL_OBSERVATION_REBUILD_COMPOSER_MODEL
        assert result.candidate.generation_method != NORMAL_OBSERVATION_REBUILD_GENERATION_METHOD
    _assert_body_free(meta)


def test_p2_plain_surface_requirement_still_allows_normal_rebuild_and_marks_plain_meta() -> None:
    result = build_public_candidate_after_gate_recovery(
        current_input=_plain_input(),
        material_route=_eligible_material_route(relation_required=False),
        original_composer_candidate=_original_candidate(two_stage_required=False),
        original_display_decision=_surface_failed_display_decision(),
        safety_triage_kind="safe_observation",
        safety_report=SafetyBoundaryReport(requires_block=False),
        recovery_plan={},
        trace_id="p2-plain-still-allows-normal-rebuild",
    )

    assert result.candidate is not None
    assert result.source_kind == CANDIDATE_SOURCE_KIND_NORMAL_OBSERVATION_REBUILD_CANDIDATE
    candidate_meta = result.candidate.composer_meta
    assert candidate_meta["surface_requirement_family"] == SURFACE_REQUIREMENT_PLAIN_STATE_ANSWER
    assert candidate_meta["two_stage_required"] is False
    assert candidate_meta["plain_state_answer_allowed"] is True
    assert candidate_meta["low_information_allowed"] is False
    assert candidate_meta["surface_requirement"]["surface_requirement_family"] == SURFACE_REQUIREMENT_PLAIN_STATE_ANSWER
    assert candidate_meta["surface_requirement"]["two_stage_required"] is False
    assert candidate_meta["two_stage_section_surface_plan"]["required"] is False
    assert candidate_meta["two_stage_section_surface_plan"]["surface_requirement_family"] == SURFACE_REQUIREMENT_PLAIN_STATE_ANSWER
    _assert_body_free(result.as_meta())
    _assert_body_free(candidate_meta)
