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
    assert_complete_initial_surface_availability_summary,
    build_complete_initial_surface_availability_summary,
    complete_initial_surface_availability_public_summary,
)
from emlis_ai_public_feedback_meta import build_public_emlis_input_feedback_meta
from emlis_ai_public_surface_requirement import (
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
