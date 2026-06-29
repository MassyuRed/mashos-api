# -*- coding: utf-8 -*-
from __future__ import annotations

import json
from collections.abc import Mapping, Sequence
from typing import Any

from emlis_ai_complete_initial_surface_availability import (
    COMPLETE_INITIAL_SURFACE_AVAILABILITY_PUBLIC_META_KEY,
    NORMAL_REBUILD_BLOCKER_SOURCE_UNAVAILABLE_NOT_REBUILDABLE,
    RECOVERY_LANE_BLOCKED_BEFORE_RECOMPOSITION,
    RECOVERY_LANE_COMPLETE_INITIAL_SURFACE_RECOMPOSITION,
    RECOVERY_LANE_SOURCE_AVAILABILITY_INVESTIGATION,
    assert_complete_initial_surface_availability_summary,
    build_complete_initial_surface_availability_summary,
    complete_initial_surface_availability_public_summary,
)
from emlis_ai_public_feedback_meta import build_public_emlis_input_feedback_meta
from emlis_ai_public_surface_requirement import (
    SURFACE_REQUIREMENT_INFRASTRUCTURE_FAIL_CLOSED,
    SURFACE_REQUIREMENT_LABELLED_TWO_STAGE,
    resolve_public_surface_requirement,
)

SECRET_RAW_INPUT = "p4 raw input must not leak"
SECRET_COMMENT_TEXT = "p4 comment text must not leak"

_FORBIDDEN_BODY_KEYS = {
    "raw_input",
    "current_input",
    "memo",
    "memo_action",
    "comment_text",
    "commentText",
    "candidate_comment_text",
    "public_comment_text",
    "observation_text",
    "reception_text",
    "body",
    "text",
    "surface_text",
}


def _assert_body_free(value: Mapping[str, Any]) -> None:
    serialized = json.dumps(value, ensure_ascii=False, sort_keys=True)
    assert SECRET_RAW_INPUT not in serialized
    assert SECRET_COMMENT_TEXT not in serialized

    def walk(node: Any) -> None:
        if isinstance(node, Mapping):
            assert not (set(node.keys()) & _FORBIDDEN_BODY_KEYS)
            for child in node.values():
                walk(child)
        elif isinstance(node, Sequence) and not isinstance(node, (str, bytes, bytearray)):
            for child in node:
                walk(child)

    walk(value)


def _labelled_requirement() -> dict[str, Any]:
    return resolve_public_surface_requirement(
        current_input={
            "memo": "人との関係や自分の境界線について長く考えている入力" * 4,
            "memo_action": "一度距離を置いて、次の返し方を整理する",
            "emotions": ["joy", "anxiety"],
            "categories": ["relationship"],
        },
        material_route={
            "material_quality": "sufficient_input_material",
            "material_sufficient": True,
        },
        composer_meta={
            "state_answer_two_stage_display_required": True,
            "state_answer_joined_comment_text_required": True,
            "state_answer_section_labels_required": True,
            "state_answer_expected_comment_text_shape": "labelled_two_stage_text",
            "raw_input_included": False,
            "comment_text_body_included": False,
        },
        diagnostic_summary={"reason_codes": ["two_stage_required", "relationship_boundary"]},
    )


def _c_source_unavailable_step5_meta() -> dict[str, Any]:
    return {
        "complete_initial_client_resolved": True,
        "candidate_generation_attempted": True,
        "candidate_generated_before_display_gate": False,
        "candidate_status": "unavailable",
        "composer_source": "unavailable",
        "first_blocker_code": "complete_initial_surface_unavailable",
        "material_quality": "sufficient_input_material",
        "material_sufficient": True,
        "reader_gate_evaluated": True,
        "grounding_gate_evaluated": True,
        "template_gate_evaluated": True,
        "display_gate_evaluated": True,
        "reason_codes": ["complete_initial_surface_unavailable"],
        "raw_input_included": False,
        "comment_text_body_included": False,
    }


def test_p4_names_c_complete_initial_surface_unavailable_without_normal_rebuild() -> None:
    summary = build_complete_initial_surface_availability_summary(
        candidate_generation_summary=_c_source_unavailable_step5_meta(),
        surface_requirement=_labelled_requirement(),
    )

    assert_complete_initial_surface_availability_summary(summary)
    assert summary["complete_initial_client_resolved"] is True
    assert summary["candidate_generation_attempted"] is True
    assert summary["candidate_generated_before_display_gate"] is False
    assert summary["candidate_status"] == "unavailable"
    assert summary["composer_source"] == "unavailable"
    assert summary["first_blocker_family"] == "source_unavailable"
    assert summary["first_blocker_code"] == "complete_initial_surface_unavailable"
    assert summary["material_sufficient"] is True
    assert summary["surface_requirement_family"] == SURFACE_REQUIREMENT_LABELLED_TWO_STAGE
    assert summary["recovery_lane"] == RECOVERY_LANE_COMPLETE_INITIAL_SURFACE_RECOMPOSITION
    assert summary["normal_observation_rebuild_allowed"] is False
    assert summary["normal_observation_rebuild_blocker"] == (
        NORMAL_REBUILD_BLOCKER_SOURCE_UNAVAILABLE_NOT_REBUILDABLE
    )
    assert summary["existing_gates_evaluated"]["reader_gate_evaluated"] is True
    assert summary["existing_gates_evaluated"]["grounding_gate_evaluated"] is True
    assert summary["existing_gates_evaluated"]["template_gate_evaluated"] is True
    assert summary["existing_gates_evaluated"]["display_gate_evaluated"] is True
    assert summary["body_free"] is True
    _assert_body_free(summary)


def test_p4_d_source_unavailable_material_route_meta_keeps_availability_eligible() -> None:
    summary = build_complete_initial_surface_availability_summary(
        candidate_generation_summary={
            "complete_initial_client_resolved": False,
            "candidate_generation_attempted": False,
            "candidate_generated_before_display_gate": False,
            "candidate_status": "unavailable",
            "composer_source": "unavailable",
            "primary_reason": "limited_composer_shallow_empty_candidate",
            "reason_codes": ["limited_composer_shallow_empty_candidate"],
            "reader_gate_evaluated": True,
            "grounding_gate_evaluated": True,
            "template_gate_evaluated": True,
            "display_gate_evaluated": True,
            "raw_input_included": False,
            "comment_text_body_included": False,
        },
        surface_requirement={
            "surface_requirement_family": SURFACE_REQUIREMENT_LABELLED_TWO_STAGE,
            "two_stage_required": True,
            "plain_state_answer_allowed": False,
            "low_information_allowed": False,
            "body_free": True,
            "raw_input_included": False,
            "comment_text_body_included": False,
        },
        material_route={
            "material_quality": "eligible",
            "response_kind": "normal_observation",
            "safety_triage_kind": "safe_observation",
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
            "relation_material_ids": [
                "relationship_end",
                "support_from_other",
                "gratitude_or_return_intent",
            ],
            "raw_input_included": False,
            "comment_text_body_included": False,
        },
    )

    assert_complete_initial_surface_availability_summary(summary)
    assert summary["first_blocker_family"] == "source_unavailable"
    assert summary["first_blocker_code"] == "limited_composer_shallow_empty_candidate"
    assert summary["material_sufficient"] is True
    assert summary["material_quality_family"] == "eligible"
    assert summary["surface_requirement_family"] == SURFACE_REQUIREMENT_LABELLED_TWO_STAGE
    assert summary["recovery_lane"] == RECOVERY_LANE_COMPLETE_INITIAL_SURFACE_RECOMPOSITION
    assert summary["normal_observation_rebuild_allowed"] is False
    assert summary["normal_observation_rebuild_blocker"] == (
        NORMAL_REBUILD_BLOCKER_SOURCE_UNAVAILABLE_NOT_REBUILDABLE
    )
    assert summary["body_free"] is True
    _assert_body_free(summary)


def test_p4_public_meta_exposes_body_free_availability_summary() -> None:
    summary = build_complete_initial_surface_availability_summary(
        candidate_generation_summary=_c_source_unavailable_step5_meta(),
        surface_requirement=_labelled_requirement(),
    )
    internal_meta = {
        "observation_status": "unavailable",
        "rejection_reasons": ["complete_initial_surface_unavailable"],
        "diagnostic_summary": {
            COMPLETE_INITIAL_SURFACE_AVAILABILITY_PUBLIC_META_KEY: summary,
            "step5_candidate_generation_path": _c_source_unavailable_step5_meta(),
            "raw_input": SECRET_RAW_INPUT,
            "comment_text": SECRET_COMMENT_TEXT,
        },
    }

    public_meta = build_public_emlis_input_feedback_meta(
        internal_meta,
        comment_text_present=False,
    )

    public_summary = public_meta[COMPLETE_INITIAL_SURFACE_AVAILABILITY_PUBLIC_META_KEY]
    assert public_summary["first_blocker_family"] == "source_unavailable"
    assert public_summary["recovery_lane"] == RECOVERY_LANE_COMPLETE_INITIAL_SURFACE_RECOMPOSITION
    assert public_summary["normal_observation_rebuild_allowed"] is False
    assert public_summary["normal_observation_rebuild_blocker"] == (
        NORMAL_REBUILD_BLOCKER_SOURCE_UNAVAILABLE_NOT_REBUILDABLE
    )
    assert public_summary["body_free"] is True
    _assert_body_free(public_summary)
    _assert_body_free(public_meta)


def test_p4_rollout_block_is_named_separately_from_source_unavailable() -> None:
    summary = build_complete_initial_surface_availability_summary(
        candidate_generation_summary={
            "complete_initial_client_resolved": True,
            "candidate_generation_attempted": True,
            "candidate_generated_before_display_gate": False,
            "candidate_status": "not_generated",
            "composer_source": "unavailable",
            "material_quality": "sufficient_input_material",
            "material_sufficient": True,
            "reason_codes": ["rollout_stage_off"],
            "raw_input_included": False,
            "comment_text_body_included": False,
        },
        surface_requirement=_labelled_requirement(),
    )

    assert_complete_initial_surface_availability_summary(summary)
    assert summary["first_blocker_family"] == "ap0_rollout"
    assert summary["first_blocker_code"] == "rollout_stage_off"
    assert summary["availability_diagnostics"]["ap0_or_rollout_blocked"] is True
    assert summary["recovery_lane"] == RECOVERY_LANE_BLOCKED_BEFORE_RECOMPOSITION
    assert summary["normal_observation_rebuild_allowed"] is False
    _assert_body_free(summary)


def test_p4_can_build_public_summary_from_step5_without_body_payload() -> None:
    summary = build_complete_initial_surface_availability_summary(
        diagnostic_summary={
            "step5_candidate_generation_path": _c_source_unavailable_step5_meta(),
            "complete_initial_runtime": {
                "candidate_generation_attempted": True,
                "candidate_generated_before_display_gate": False,
                "candidate_status": "unavailable",
                "composer_source": "unavailable",
            },
            "surface_requirement": _labelled_requirement(),
        },
    )
    public_summary = complete_initial_surface_availability_public_summary(summary)

    assert public_summary["candidate_generated_before_display_gate"] is False
    assert public_summary["first_blocker_family"] == "source_unavailable"
    assert public_summary["material_sufficient"] is True
    assert public_summary["surface_requirement_family"] == SURFACE_REQUIREMENT_LABELLED_TWO_STAGE
    assert public_summary["body_free"] is True
    _assert_body_free(public_summary)


def test_p4_explicit_phase20_3_material_route_overrides_prior_unknown_availability_summary() -> None:
    prior_unknown_summary = {
        "schema_version": "cocolon.emlis.complete_initial_surface_availability.v1",
        "source_phase": "PublicObservationRecovery_P4_CompleteInitialSurfaceAvailability",
        "candidate_status": "unavailable",
        "composer_source": "unavailable",
        "first_blocker_family": "source_unavailable",
        "first_blocker_code": "limited_composer_shallow_empty_candidate",
        "material_sufficient": False,
        "material_quality_family": "unknown",
        "surface_requirement_family": "unknown",
        "recovery_lane": "source_availability_investigation",
        "body_free": True,
        "raw_input_included": False,
        "comment_text_body_included": False,
    }
    summary = build_complete_initial_surface_availability_summary(
        diagnostic_summary={
            COMPLETE_INITIAL_SURFACE_AVAILABILITY_PUBLIC_META_KEY: prior_unknown_summary,
            "primary_reason": "limited_composer_shallow_empty_candidate",
            "display_rejection_reasons": [
                "surface_signature_unavailable",
                "empty_comment_text_without_candidate",
            ],
            "composer_status": "unavailable",
            "composer_source": "unavailable",
        },
        candidate_generation_summary={
            "candidate_generation_attempted": False,
            "candidate_generated_before_display_gate": False,
            "candidate_status": "unavailable",
            "composer_source": "unavailable",
        },
        surface_requirement=_labelled_requirement(),
        material_route={
            "response_kind": "normal_observation",
            "material_quality": "eligible",
            "eligible_for_full_observation": True,
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
            "relation_material_ids": [
                "relationship_end",
                "support_from_other",
                "gratitude_or_return_intent",
            ],
            "raw_input_included": False,
            "comment_text_body_included": False,
        },
    )

    assert_complete_initial_surface_availability_summary(summary)
    assert summary["first_blocker_family"] == "source_unavailable"
    assert summary["first_blocker_code"] == "limited_composer_shallow_empty_candidate"
    assert summary["material_sufficient"] is True
    assert summary["material_quality_family"] == "eligible"
    assert summary["surface_requirement_family"] == SURFACE_REQUIREMENT_LABELLED_TWO_STAGE
    assert summary["recovery_lane"] == RECOVERY_LANE_COMPLETE_INITIAL_SURFACE_RECOMPOSITION
    assert summary["normal_observation_rebuild_allowed"] is False
    assert summary["normal_observation_rebuild_blocker"] == (
        NORMAL_REBUILD_BLOCKER_SOURCE_UNAVAILABLE_NOT_REBUILDABLE
    )
    assert summary["body_free"] is True
    _assert_body_free(summary)


def test_p5_true_infrastructure_blocker_overrides_source_unavailable_recomposition_lane() -> None:
    summary = build_complete_initial_surface_availability_summary(
        candidate_generation_summary={
            "complete_initial_client_resolved": False,
            "candidate_generation_attempted": False,
            "candidate_generated_before_display_gate": False,
            "candidate_status": "unavailable",
            "composer_source": "unavailable",
            "primary_reason": "limited_composer_shallow_empty_candidate",
            "reason_codes": [
                "limited_composer_shallow_empty_candidate",
                "reply_timeout_or_error",
            ],
            "material_quality": "eligible",
            "material_sufficient": True,
            "raw_input_included": False,
            "comment_text_body_included": False,
        },
        surface_requirement={
            "surface_requirement_family": SURFACE_REQUIREMENT_LABELLED_TWO_STAGE,
            "two_stage_required": True,
            "body_free": True,
            "raw_input_included": False,
            "comment_text_body_included": False,
        },
    )

    assert_complete_initial_surface_availability_summary(summary)
    assert summary["first_blocker_family"] == "infrastructure"
    assert summary["first_blocker_code"] == "reply_timeout_or_error"
    assert summary["material_sufficient"] is True
    assert summary["surface_requirement_family"] == SURFACE_REQUIREMENT_LABELLED_TWO_STAGE
    assert summary["recovery_lane"] == RECOVERY_LANE_BLOCKED_BEFORE_RECOMPOSITION
    assert summary["normal_observation_rebuild_allowed"] is False
    assert summary["body_free"] is True
    _assert_body_free(summary)


def test_p5_material_quality_blocker_does_not_open_source_unavailable_recomposition_lane() -> None:
    summary = build_complete_initial_surface_availability_summary(
        candidate_generation_summary={
            "complete_initial_client_resolved": False,
            "candidate_generation_attempted": False,
            "candidate_generated_before_display_gate": False,
            "candidate_status": "unavailable",
            "composer_source": "unavailable",
            "primary_reason": "limited_composer_shallow_empty_candidate",
            "reason_codes": [
                "limited_composer_shallow_empty_candidate",
                "material_insufficient",
            ],
            "material_quality": "low_information",
            "material_sufficient": False,
            "raw_input_included": False,
            "comment_text_body_included": False,
        },
        surface_requirement={
            "surface_requirement_family": SURFACE_REQUIREMENT_LABELLED_TWO_STAGE,
            "two_stage_required": True,
            "body_free": True,
            "raw_input_included": False,
            "comment_text_body_included": False,
        },
    )

    assert_complete_initial_surface_availability_summary(summary)
    assert summary["first_blocker_family"] == "material_quality"
    assert summary["first_blocker_code"] == "material_insufficient"
    assert summary["material_sufficient"] is False
    assert summary["recovery_lane"] == RECOVERY_LANE_BLOCKED_BEFORE_RECOMPOSITION
    assert summary["normal_observation_rebuild_allowed"] is False
    assert summary["body_free"] is True
    _assert_body_free(summary)


def test_p5_source_unavailable_lane_requires_supported_surface_requirement() -> None:
    summary = build_complete_initial_surface_availability_summary(
        candidate_generation_summary={
            "complete_initial_client_resolved": False,
            "candidate_generation_attempted": False,
            "candidate_generated_before_display_gate": False,
            "candidate_status": "unavailable",
            "composer_source": "unavailable",
            "primary_reason": "limited_composer_shallow_empty_candidate",
            "reason_codes": ["limited_composer_shallow_empty_candidate"],
            "raw_input_included": False,
            "comment_text_body_included": False,
        },
        material_route={
            "material_quality": "eligible",
            "eligible_for_full_observation": True,
            "response_kind": "normal_observation",
            "raw_input_included": False,
            "comment_text_body_included": False,
        },
    )

    assert_complete_initial_surface_availability_summary(summary)
    assert summary["first_blocker_family"] == "source_unavailable"
    assert summary["material_sufficient"] is True
    assert summary["surface_requirement_family"] == "unknown"
    assert summary["recovery_lane"] == RECOVERY_LANE_SOURCE_AVAILABILITY_INVESTIGATION
    assert summary["normal_observation_rebuild_allowed"] is False
    _assert_body_free(summary)


def test_p5_d_source_unavailable_lane_remains_recomposition_when_surface_is_labelled() -> None:
    summary = build_complete_initial_surface_availability_summary(
        candidate_generation_summary={
            "complete_initial_client_resolved": False,
            "candidate_generation_attempted": False,
            "candidate_generated_before_display_gate": False,
            "candidate_status": "unavailable",
            "composer_source": "unavailable",
            "primary_reason": "limited_composer_shallow_empty_candidate",
            "reason_codes": [
                "limited_composer_shallow_empty_candidate",
                "surface_signature_unavailable",
                "runtime_surface_pre_return_gate_failed",
            ],
            "raw_input_included": False,
            "comment_text_body_included": False,
        },
        surface_requirement={
            "surface_requirement_family": SURFACE_REQUIREMENT_LABELLED_TWO_STAGE,
            "two_stage_required": True,
            "plain_state_answer_allowed": False,
            "low_information_allowed": False,
            "body_free": True,
            "raw_input_included": False,
            "comment_text_body_included": False,
        },
        material_route={
            "material_quality": "eligible",
            "eligible_for_full_observation": True,
            "response_kind": "normal_observation",
            "raw_input_included": False,
            "comment_text_body_included": False,
        },
    )

    assert_complete_initial_surface_availability_summary(summary)
    assert summary["first_blocker_family"] == "source_unavailable"
    assert summary["first_blocker_code"] == "limited_composer_shallow_empty_candidate"
    assert summary["material_sufficient"] is True
    assert summary["material_quality_family"] == "eligible"
    assert summary["surface_requirement_family"] == SURFACE_REQUIREMENT_LABELLED_TWO_STAGE
    assert summary["recovery_lane"] == RECOVERY_LANE_COMPLETE_INITIAL_SURFACE_RECOMPOSITION
    assert summary["normal_observation_rebuild_allowed"] is False
    assert summary["normal_observation_rebuild_blocker"] == (
        NORMAL_REBUILD_BLOCKER_SOURCE_UNAVAILABLE_NOT_REBUILDABLE
    )
    _assert_body_free(summary)


def test_p5_true_infrastructure_reason_blocks_source_unavailable_recomposition() -> None:
    summary = build_complete_initial_surface_availability_summary(
        candidate_generation_summary={
            "complete_initial_client_resolved": False,
            "candidate_generation_attempted": False,
            "candidate_generated_before_display_gate": False,
            "candidate_status": "unavailable",
            "composer_source": "unavailable",
            "primary_reason": "limited_composer_shallow_empty_candidate",
            "reason_codes": [
                "limited_composer_shallow_empty_candidate",
                "reply_timeout_or_error",
            ],
            "raw_input_included": False,
            "comment_text_body_included": False,
        },
        surface_requirement=_labelled_requirement(),
        material_route={
            "material_quality": "eligible",
            "eligible_for_full_observation": True,
            "raw_input_included": False,
            "comment_text_body_included": False,
        },
    )

    assert_complete_initial_surface_availability_summary(summary)
    assert summary["first_blocker_family"] == "infrastructure"
    assert summary["first_blocker_code"] == "reply_timeout_or_error"
    assert summary["availability_diagnostics"]["ap0_or_rollout_blocked"] is False
    assert summary["recovery_lane"] == RECOVERY_LANE_BLOCKED_BEFORE_RECOMPOSITION
    assert summary["normal_observation_rebuild_allowed"] is False
    _assert_body_free(summary)


def test_p5_infrastructure_surface_requirement_blocks_recomposition_even_with_eligible_material() -> None:
    summary = build_complete_initial_surface_availability_summary(
        candidate_generation_summary={
            "complete_initial_client_resolved": False,
            "candidate_generation_attempted": False,
            "candidate_generated_before_display_gate": False,
            "candidate_status": "unavailable",
            "composer_source": "unavailable",
            "primary_reason": "limited_composer_shallow_empty_candidate",
            "reason_codes": ["limited_composer_shallow_empty_candidate"],
            "raw_input_included": False,
            "comment_text_body_included": False,
        },
        surface_requirement={
            "surface_requirement_family": SURFACE_REQUIREMENT_INFRASTRUCTURE_FAIL_CLOSED,
            "two_stage_required": False,
            "plain_state_answer_allowed": False,
            "low_information_allowed": False,
            "body_free": True,
            "raw_input_included": False,
            "comment_text_body_included": False,
        },
        material_route={
            "material_quality": "eligible",
            "eligible_for_full_observation": True,
            "response_kind": "normal_observation",
            "raw_input_included": False,
            "comment_text_body_included": False,
        },
    )

    assert_complete_initial_surface_availability_summary(summary)
    assert summary["first_blocker_family"] == "infrastructure"
    assert summary["first_blocker_code"] == "limited_composer_shallow_empty_candidate"
    assert summary["material_sufficient"] is True
    assert summary["surface_requirement_family"] == SURFACE_REQUIREMENT_INFRASTRUCTURE_FAIL_CLOSED
    assert summary["recovery_lane"] == RECOVERY_LANE_BLOCKED_BEFORE_RECOMPOSITION
    assert summary["normal_observation_rebuild_allowed"] is False
    _assert_body_free(summary)


def test_p5_unsupported_material_quality_blocks_source_unavailable_recomposition() -> None:
    summary = build_complete_initial_surface_availability_summary(
        candidate_generation_summary={
            "complete_initial_client_resolved": False,
            "candidate_generation_attempted": False,
            "candidate_generated_before_display_gate": False,
            "candidate_status": "unavailable",
            "composer_source": "unavailable",
            "primary_reason": "limited_composer_shallow_empty_candidate",
            "reason_codes": ["limited_composer_shallow_empty_candidate"],
            "raw_input_included": False,
            "comment_text_body_included": False,
        },
        surface_requirement=_labelled_requirement(),
        material_route={
            "material_quality": "unsupported",
            "response_kind": "normal_observation",
            "raw_input_included": False,
            "comment_text_body_included": False,
        },
    )

    assert_complete_initial_surface_availability_summary(summary)
    assert summary["first_blocker_family"] == "material_quality"
    assert summary["material_sufficient"] is False
    assert summary["material_quality_family"] == "unsupported"
    assert summary["surface_requirement_family"] == SURFACE_REQUIREMENT_LABELLED_TWO_STAGE
    assert summary["availability_diagnostics"]["material_quality_blocked"] is True
    assert summary["recovery_lane"] == RECOVERY_LANE_BLOCKED_BEFORE_RECOMPOSITION
    assert summary["normal_observation_rebuild_allowed"] is False
    _assert_body_free(summary)
