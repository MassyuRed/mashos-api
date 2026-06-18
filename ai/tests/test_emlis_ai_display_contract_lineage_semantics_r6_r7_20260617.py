from __future__ import annotations

from typing import Any

from emlis_ai_body_free_public_source_lineage import (
    assert_body_free_public_source_lineage_record,
    sanitize_body_free_public_source_lineage_record,
)
from emlis_ai_gate_recovery_public_constants import (
    CANDIDATE_SOURCE_KIND_COMPLETE_INITIAL_SURFACE_RECOMPOSITION_CANDIDATE,
    CANDIDATE_SOURCE_KIND_GATE_RECOVERY_MATERIAL_SURFACE,
    CANDIDATE_SOURCE_KIND_LABELLED_TWO_STAGE_SURFACE_RECOMPOSITION_CANDIDATE,
    PUBLIC_SURFACE_ROLE_DIAGNOSTIC_RECOVERY,
)
from emlis_ai_public_feedback_meta import build_public_emlis_input_feedback_meta


_COMPLETE_INITIAL = CANDIDATE_SOURCE_KIND_COMPLETE_INITIAL_SURFACE_RECOMPOSITION_CANDIDATE
_LABELLED_TWO_STAGE = CANDIDATE_SOURCE_KIND_LABELLED_TWO_STAGE_SURFACE_RECOMPOSITION_CANDIDATE
_GATE_RECOVERY_MATERIAL = CANDIDATE_SOURCE_KIND_GATE_RECOVERY_MATERIAL_SURFACE

_FORBIDDEN_BODY_KEYS = {
    "raw_input",
    "memo",
    "memo_action",
    "emotion_details",
    "comment_text",
    "candidate_comment_text",
    "public_comment_text",
    "surface_text",
    "surface_body",
    "candidate_body",
    "generated_text",
    "realized_text",
    "text",
    "body",
    "source_text",
    "input_text",
    "evidence_text",
    "reviewer_free_text",
    "traceback",
    "terminal_output",
}


def _keys(value: Any) -> set[str]:
    if isinstance(value, dict):
        found: set[str] = set()
        for key, nested in value.items():
            found.add(str(key))
            found.update(_keys(nested))
        return found
    if isinstance(value, list):
        found: set[str] = set()
        for item in value:
            found.update(_keys(item))
        return found
    return set()


def _assert_public_lineage_body_free(public_meta: dict[str, Any]) -> None:
    lineage = public_meta["public_surface_lineage"]
    assert lineage["body_free"] is True
    assert lineage["raw_input_included"] is False
    assert lineage["comment_text_body_included"] is False
    assert lineage["candidate_body_included"] is False
    assert lineage["display_gate_relaxed"] is False
    assert lineage["runtime_surface_gate_relaxed"] is False
    assert lineage["visible_surface_gate_relaxed"] is False
    assert lineage["grounding_gate_relaxed"] is False
    assert lineage["template_gate_relaxed"] is False
    assert lineage["safety_gate_relaxed"] is False
    assert not (_keys(public_meta) & _FORBIDDEN_BODY_KEYS)


def test_r6_pre_connection_complete_initial_attempt_does_not_override_labelled_final() -> None:
    public_meta = build_public_emlis_input_feedback_meta(
        {
            "observation_status": "passed",
            "body_free_public_source_lineage": {
                "candidate_source_kind": _LABELLED_TWO_STAGE,
                "root_candidate_source_kind": "unavailable",
                "recovery_input_candidate_source_kind": _COMPLETE_INITIAL,
                "selected_public_candidate_source_kind": _LABELLED_TWO_STAGE,
                "pre_public_candidate_source_kind": _COMPLETE_INITIAL,
                "final_public_candidate_source_kind": _LABELLED_TWO_STAGE,
                "public_surface_role": "public_observation_candidate",
                "surface_requirement_family": "labelled_two_stage",
                "two_stage_required": True,
                "plain_surface_allowed": False,
                "low_information_allowed": False,
                "complete_initial_surface_recomposition_attempted": True,
                "complete_initial_surface_recomposition_used": False,
                "complete_initial_surface_recomposition_final_used": False,
                "labelled_two_stage_surface_recomposition_used": True,
                "labelled_two_stage_surface_recomposition_final_used": True,
                "body_free": True,
                "raw_input_included": False,
                "comment_text_body_included": False,
                "candidate_body_included": False,
            },
        },
        comment_text_present=True,
        subscription_tier="free",
    )

    lineage = public_meta["public_surface_lineage"]
    assert public_meta["observation_status"] == "passed"
    assert lineage["candidate_source_kind"] == _LABELLED_TWO_STAGE
    assert lineage["final_public_candidate_source_kind"] == _LABELLED_TWO_STAGE
    assert lineage["selected_public_candidate_source_kind"] == _LABELLED_TWO_STAGE
    assert lineage["pre_public_candidate_source_kind"] == _COMPLETE_INITIAL
    assert lineage["recovery_input_candidate_source_kind"] == _COMPLETE_INITIAL
    assert lineage["root_candidate_source_kind"] == "unavailable"
    assert lineage["lineage_consistency_passed"] is True
    assert lineage["complete_initial_surface_recomposition_attempted"] is True
    assert lineage["complete_initial_surface_recomposition_used"] is False
    assert lineage["complete_initial_surface_recomposition_final_used"] is False
    assert lineage["labelled_two_stage_surface_recomposition_used"] is True
    assert lineage["labelled_two_stage_surface_recomposition_final_used"] is True
    _assert_public_lineage_body_free(public_meta)


def test_r7_phase20_5_pre_public_source_is_kept_separate_from_post_final_source() -> None:
    public_meta = build_public_emlis_input_feedback_meta(
        {
            "observation_status": "passed",
            "phase20_13_post_final_gate_recovery": {
                "source_phase": "Phase20-13_Post_Final_Gate_Recovery",
                "recovery_context": "post_final_pre_return_gate",
                "public_candidate_source_kind": _LABELLED_TWO_STAGE,
                "selected_public_candidate_source_kind": _LABELLED_TWO_STAGE,
                "final_public_candidate_source_kind": _LABELLED_TWO_STAGE,
                "recovery_input_candidate_source_kind": _COMPLETE_INITIAL,
                "pre_public_candidate_source_kind": _COMPLETE_INITIAL,
                "root_candidate_source_kind": "unavailable",
                "public_surface_role": "public_observation_candidate",
                "complete_initial_surface_recomposition_attempted": True,
                "complete_initial_surface_recomposition_final_used": False,
                "labelled_two_stage_surface_recomposition_final_used": True,
                "raw_input_included": False,
                "comment_text_body_included": False,
                "candidate_body_included": False,
            },
            "phase20_5_gate_recovery_public_boundary": {
                "source_phase": "phase20_5_gate_recovery_public_boundary",
                "recovery_context": "pre_public_display_gate",
                "adopted_candidate_source_kind": _COMPLETE_INITIAL,
                "candidate_source_kind": _COMPLETE_INITIAL,
                "public_surface_role": "public_observation_candidate",
                "raw_input_included": False,
                "comment_text_body_included": False,
                "candidate_body_included": False,
            },
            "complete_initial_surface_recomposition_summary": {
                "attempted": True,
                "candidate_generated": True,
                "applied": False,
                "existing_gate_chain": {
                    "blocked_reasons": ["visible_surface_acceptance_gate_failed"],
                    "candidate_adopted_after_existing_gates": False,
                },
                "raw_input_included": False,
                "comment_text_body_included": False,
                "candidate_body_included": False,
            },
        },
        comment_text_present=True,
        subscription_tier="free",
    )

    lineage = public_meta["public_surface_lineage"]
    assert lineage["candidate_source_kind"] == _LABELLED_TWO_STAGE
    assert lineage["final_public_candidate_source_kind"] == _LABELLED_TWO_STAGE
    assert lineage["pre_public_candidate_source_kind"] == _COMPLETE_INITIAL
    assert lineage["complete_initial_surface_recomposition_attempted"] is True
    assert lineage["complete_initial_surface_recomposition_used"] is False
    assert lineage["labelled_two_stage_surface_recomposition_used"] is True
    assert lineage["lineage_consistency_passed"] is True
    _assert_public_lineage_body_free(public_meta)


def test_r7_gate_recovery_material_surface_stays_forbidden_and_body_free() -> None:
    lineage = sanitize_body_free_public_source_lineage_record(
        {
            "candidate_source_kind": _GATE_RECOVERY_MATERIAL,
            "selected_public_candidate_source_kind": _GATE_RECOVERY_MATERIAL,
            "final_public_candidate_source_kind": _GATE_RECOVERY_MATERIAL,
            "raw_input": "must be stripped",
            "comment_text": "must be stripped",
            "candidate_body": "must be stripped",
            "raw_input_included": True,
            "comment_text_body_included": True,
            "candidate_body_included": True,
            "display_gate_relaxed": True,
            "runtime_surface_gate_relaxed": True,
        }
    )

    assert lineage["candidate_source_kind"] == _GATE_RECOVERY_MATERIAL
    assert lineage["final_public_candidate_source_kind"] == _GATE_RECOVERY_MATERIAL
    assert lineage["public_candidate_source_allowed"] is False
    assert lineage["public_candidate_source_forbidden"] is True
    assert lineage["public_surface_role"] == PUBLIC_SURFACE_ROLE_DIAGNOSTIC_RECOVERY
    assert lineage["public_display_allowed_by_boundary"] is False
    assert lineage["gate_recovery_material_surface_used_as_public_body"] is True
    assert lineage["diagnostic_recovery_surface_used_as_public_body"] is False
    assert lineage["body_free"] is True
    assert lineage["raw_input_included"] is False
    assert lineage["comment_text_body_included"] is False
    assert lineage["candidate_body_included"] is False
    assert lineage["display_gate_relaxed"] is False
    assert lineage["runtime_surface_gate_relaxed"] is False
    assert "raw_input" not in lineage
    assert "comment_text" not in lineage
    assert "candidate_body" not in lineage
    assert_body_free_public_source_lineage_record(lineage)
