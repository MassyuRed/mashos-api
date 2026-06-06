# -*- coding: utf-8 -*-
from __future__ import annotations

"""P6: labelled two-stage recomposition must recover two-stage required surfaces."""

from collections.abc import Mapping, Sequence
from typing import Any

from emlis_ai_gate_recovery_public_candidate_builder import build_public_candidate_after_gate_recovery
from emlis_ai_gate_recovery_public_constants import (
    CANDIDATE_SOURCE_KIND_LABELLED_TWO_STAGE_SURFACE_RECOMPOSITION_CANDIDATE,
    PUBLIC_SURFACE_ROLE_PUBLIC_OBSERVATION,
)
from emlis_ai_labelled_two_stage_surface_recomposition import (
    assert_labelled_two_stage_surface_recomposition_meta,
    build_labelled_two_stage_surface_recomposition_candidate,
    labelled_two_stage_surface_recomposition_public_summary,
    should_attempt_labelled_two_stage_surface_recomposition,
)
from emlis_ai_public_surface_requirement import (
    SURFACE_REQUIREMENT_LABELLED_TWO_STAGE,
    is_labelled_two_stage_comment_text_shape,
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


def _current_input() -> dict[str, Any]:
    return {
        "memo": "仕事で相手の言い方に引っかかったあと、嬉しさもあるのに距離の置き方で迷っている。",
        "memo_action": "すぐ返事せず、一度、自分が守りたい距離を書き出してから話す。",
        "emotions": ["喜び", "違和感", "不安"],
        "category": ["仕事", "人間関係"],
    }


def _material_route() -> dict[str, Any]:
    return {
        "material_quality": "eligible",
        "material_sufficient": True,
        "visible_material_slots": ["event", "emotion_direction", "action", "relationship"],
        "unknown_slots": ["cause"],
        "relation_material_ids": ["relationship_boundary_state_answer"],
        "generic_relation_material_ids": ["relationship_boundary_state_answer"],
    }


def _surface_requirement() -> dict[str, Any]:
    return public_surface_requirement_public_summary(
        {
            "surface_requirement_family": SURFACE_REQUIREMENT_LABELLED_TWO_STAGE,
            "two_stage_required": True,
            "plain_state_answer_allowed": False,
            "low_information_allowed": False,
            "required_comment_text_shape": {
                "kind": "labelled_two_stage",
                "starts_with": "見えたこと：\\n",
                "contains_boundary": "\\n\\nEmlisから：\\n",
                "observation_section_required": True,
                "reception_section_required": True,
                "comment_text_body_included": False,
            },
            "decision_sources": ["p6_test_two_stage_required"],
            "material_quality_family": "sufficient_input_material",
            "raw_input_included": False,
            "comment_text_body_included": False,
        }
    )


def _plain_original_candidate() -> ConversationComposerCandidate:
    return ConversationComposerCandidate(
        comment_text=(
            "この記録では、人とのやり取りについて、喜びの動きがまだ落ち着ききっていない状態として見えます。"
            "次にどう動くかを探しているところもEmlisは受け取りました。"
        ),
        composer_source="ai_generated",
        status="generated",
        ai_generated=True,
        trace_id="p6-original",
        attempt_count=1,
        confidence=0.82,
        rejection_reasons=[],
        request_schema_version="emlis.composer.request.v1",
        response_schema_version="cocolon.emlis.complete_composer.response.v1",
        fixed_string_renderer_used=False,
        composer_model="complete_initial_composer_v1",
        generation_method="complete_initial_composer",
        coverage_scope="current_input_only",
        generation_scope="current_input_only",
        composer_meta={
            "candidate_source_kind": "complete_initial_composer",
            "public_surface_role": PUBLIC_SURFACE_ROLE_PUBLIC_OBSERVATION,
            "state_answer_two_stage_display_required": True,
            "state_answer_joined_comment_text_required": True,
            "state_answer_section_labels_required": True,
            "state_answer_expected_comment_text_shape": "labelled_two_stage_text",
            "raw_input_included": False,
            "comment_text_body_included": False,
        },
        used_claim_ids=["claim_relationship_boundary"],
        used_relation_ids=["relationship_boundary_state_answer"],
    )


def _surface_failed_display_decision() -> DisplayDecision:
    return DisplayDecision(
        observation_status="rejected",
        comment_text="",
        rejection_reasons=[
            "visible_surface_acceptance_gate_failed",
            "product_surface_invalid_plain_used_for_two_stage_required",
        ],
        trace_id="p6-two-stage-required",
    )


def test_p6_builds_labelled_two_stage_candidate_from_plain_original_without_body_meta() -> None:
    original = _plain_original_candidate()
    assert should_attempt_labelled_two_stage_surface_recomposition(
        current_input=_current_input(),
        material_route=_material_route(),
        surface_requirement=_surface_requirement(),
        original_composer_candidate=original,
        original_display_decision=_surface_failed_display_decision(),
    )

    candidate, reasons = build_labelled_two_stage_surface_recomposition_candidate(
        current_input=_current_input(),
        material_route=_material_route(),
        surface_requirement=_surface_requirement(),
        original_composer_candidate=original,
        original_display_decision=_surface_failed_display_decision(),
        trace_id="p6-direct",
        recovery_context="pre_public_display_gate",
    )

    assert candidate is not None
    assert "labelled_two_stage_surface_recomposition_candidate_built" in reasons
    assert candidate.composer_model == "labelled_two_stage_surface_recomposition_v1"
    assert is_labelled_two_stage_comment_text_shape(candidate.comment_text)
    assert candidate.comment_text.startswith("見えたこと：\n")
    assert "\n\nEmlisから：\n" in candidate.comment_text
    meta = candidate.composer_meta
    assert_labelled_two_stage_surface_recomposition_meta(meta)
    assert meta["candidate_source_kind"] == CANDIDATE_SOURCE_KIND_LABELLED_TWO_STAGE_SURFACE_RECOMPOSITION_CANDIDATE
    assert meta["labelled_two_stage_surface_recomposition_used"] is True
    assert meta["normal_observation_rebuild_used"] is False
    assert meta["complete_initial_surface_recomposition_used"] is False
    assert meta["gate_recovery_material_surface_used"] is False
    assert meta["implementation_boundary"]["fixed_fallback_used"] is False
    _assert_body_free(meta)

    public_summary = labelled_two_stage_surface_recomposition_public_summary(meta)
    assert public_summary["candidate_source_kind"] == CANDIDATE_SOURCE_KIND_LABELLED_TWO_STAGE_SURFACE_RECOMPOSITION_CANDIDATE
    assert public_summary["labels_present"] is True
    assert public_summary["section_budget_valid"] is True
    _assert_body_free(public_summary)


def test_public_candidate_builder_prefers_p6_for_two_stage_required_before_plain_rebuild() -> None:
    result = build_public_candidate_after_gate_recovery(
        current_input=_current_input(),
        material_route=_material_route(),
        original_composer_candidate=_plain_original_candidate(),
        original_display_decision=_surface_failed_display_decision(),
        safety_triage_kind="safe_observation",
        safety_report=SafetyBoundaryReport(requires_block=False),
        recovery_plan=None,
        trace_id="p6-builder",
    )

    assert result.candidate_available is True
    assert result.source_kind == CANDIDATE_SOURCE_KIND_LABELLED_TWO_STAGE_SURFACE_RECOMPOSITION_CANDIDATE
    assert result.public_display_allowed is True
    assert result.candidate is not None
    assert is_labelled_two_stage_comment_text_shape(result.candidate.comment_text)
    meta = result.as_meta()
    assert meta["recovery_plan"]["target_public_candidate_source"] == CANDIDATE_SOURCE_KIND_LABELLED_TWO_STAGE_SURFACE_RECOMPOSITION_CANDIDATE
    assert meta["candidate_lineage"]["public_candidate_rebuilt_after_recovery"] is True
    _assert_body_free(meta)


def test_p6_can_recompose_already_labelled_but_failed_surface_and_blocks_low_information() -> None:
    labelled = _plain_original_candidate()
    labelled = ConversationComposerCandidate(
        **{
            **labelled.__dict__,
            "comment_text": "見えたこと：\n状態が見えます。\n\nEmlisから：\nそのまま受け取りました。",
        }
    )
    assert should_attempt_labelled_two_stage_surface_recomposition(
        current_input=_current_input(),
        material_route=_material_route(),
        surface_requirement=_surface_requirement(),
        original_composer_candidate=labelled,
        original_display_decision=_surface_failed_display_decision(),
    )
    candidate, reasons = build_labelled_two_stage_surface_recomposition_candidate(
        current_input=_current_input(),
        material_route=_material_route(),
        surface_requirement=_surface_requirement(),
        original_composer_candidate=labelled,
        original_display_decision=_surface_failed_display_decision(),
        trace_id="p6-labelled-failed",
        recovery_context="pre_public_display_gate",
    )
    assert candidate is not None
    assert "labelled_two_stage_surface_recomposition_candidate_built" in reasons
    assert candidate.composer_meta["original_surface_plain_or_unlabelled"] is False
    assert candidate.composer_meta["original_surface_labelled_two_stage"] is True

    low_material = dict(_material_route(), material_quality="low_information")
    assert not should_attempt_labelled_two_stage_surface_recomposition(
        current_input=_current_input(),
        material_route=low_material,
        surface_requirement=_surface_requirement(),
        original_composer_candidate=_plain_original_candidate(),
        original_display_decision=_surface_failed_display_decision(),
    )
