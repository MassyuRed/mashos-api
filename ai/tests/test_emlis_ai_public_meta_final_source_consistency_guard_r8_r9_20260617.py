from __future__ import annotations

from typing import Any

from emlis_ai_gate_recovery_public_constants import (
    CANDIDATE_SOURCE_KIND_COMPLETE_INITIAL_SURFACE_RECOMPOSITION_CANDIDATE,
    CANDIDATE_SOURCE_KIND_LABELLED_TWO_STAGE_SURFACE_RECOMPOSITION_CANDIDATE,
)
from emlis_ai_public_feedback_meta import build_public_emlis_input_feedback_meta

_COMPLETE_INITIAL = CANDIDATE_SOURCE_KIND_COMPLETE_INITIAL_SURFACE_RECOMPOSITION_CANDIDATE
_LABELLED_TWO_STAGE = CANDIDATE_SOURCE_KIND_LABELLED_TWO_STAGE_SURFACE_RECOMPOSITION_CANDIDATE

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


def _assert_public_surface_lineage_guarded(public_meta: dict[str, Any]) -> None:
    lineage = public_meta["public_surface_lineage"]
    assert lineage["lineage_consistency_passed"] is True
    assert lineage["candidate_source_kind"] == lineage["final_public_candidate_source_kind"]
    assert lineage["selected_public_candidate_source_kind"] == lineage["final_public_candidate_source_kind"]
    assert lineage["body_free"] is True
    assert lineage["raw_input_included"] is False
    assert lineage["comment_text_body_included"] is False
    assert lineage["original_comment_text_body_included"] is False
    assert lineage["candidate_body_included"] is False
    assert lineage["display_gate_relaxed"] is False
    assert lineage["runtime_surface_gate_relaxed"] is False
    assert lineage["visible_surface_gate_relaxed"] is False
    assert lineage["grounding_gate_relaxed"] is False
    assert lineage["template_gate_relaxed"] is False
    assert lineage["safety_gate_relaxed"] is False
    assert not (_keys(public_meta) & _FORBIDDEN_BODY_KEYS)


def test_r8_post_final_source_overrides_stale_public_lineage_without_body_leak() -> None:
    public_meta = build_public_emlis_input_feedback_meta(
        {
            "observation_status": "passed",
            # This is the stale pre-R8 public lineage shape: it presents the
            # pre-public complete-initial candidate as though it were final.
            "public_surface_lineage": {
                "schema_version": "cocolon.emlis.public_surface_lineage.v1",
                "source_phase": "PublicObservationRecovery_P8_PublicMetaBoundaryProductQualityMeta",
                "candidate_source_kind": _COMPLETE_INITIAL,
                "selected_public_candidate_source_kind": _COMPLETE_INITIAL,
                "pre_public_candidate_source_kind": _COMPLETE_INITIAL,
                "final_public_candidate_source_kind": _COMPLETE_INITIAL,
                "complete_initial_surface_recomposition_attempted": True,
                "complete_initial_surface_recomposition_final_used": True,
                "labelled_two_stage_surface_recomposition_final_used": False,
                "raw_input": "must not leak",
                "comment_text": "must not leak",
                "candidate_body": "must not leak",
            },
            # R8 must treat this as the source of truth for the actual returned
            # final public surface.
            "phase20_13_post_final_gate_recovery": {
                "source_phase": "Phase20-13_Post_Final_Gate_Recovery",
                "recovery_context": "post_final_pre_return_gate",
                "applied": True,
                "candidate_source_kind": _LABELLED_TWO_STAGE,
                "public_candidate_source_kind": _LABELLED_TWO_STAGE,
                "selected_public_candidate_source_kind": _LABELLED_TWO_STAGE,
                "pre_public_candidate_source_kind": _COMPLETE_INITIAL,
                "final_public_candidate_source_kind": _LABELLED_TWO_STAGE,
                "root_candidate_source_kind": "source_unavailable",
                "complete_initial_surface_recomposition_attempted": True,
                "complete_initial_surface_recomposition_final_used": False,
                "labelled_two_stage_surface_recomposition_final_used": True,
                "raw_input": "must not leak",
                "comment_text": "must not leak",
                "candidate_body": "must not leak",
            },
        },
        comment_text_present=True,
        subscription_tier="free",
    )

    lineage = public_meta["public_surface_lineage"]
    assert public_meta["observation_status"] == "passed"
    assert lineage["candidate_source_kind"] == _LABELLED_TWO_STAGE
    assert lineage["selected_public_candidate_source_kind"] == _LABELLED_TWO_STAGE
    assert lineage["final_public_candidate_source_kind"] == _LABELLED_TWO_STAGE
    assert lineage["pre_public_candidate_source_kind"] == _COMPLETE_INITIAL
    assert lineage["root_candidate_source_kind"] == "source_unavailable"
    assert lineage["complete_initial_surface_recomposition_attempted"] is True
    assert lineage["complete_initial_surface_recomposition_used"] is False
    assert lineage["complete_initial_surface_recomposition_final_used"] is False
    assert lineage["labelled_two_stage_surface_recomposition_used"] is True
    assert lineage["labelled_two_stage_surface_recomposition_final_used"] is True
    _assert_public_surface_lineage_guarded(public_meta)


def test_r8_unapplied_post_final_attempt_does_not_override_existing_final_source() -> None:
    public_meta = build_public_emlis_input_feedback_meta(
        {
            "observation_status": "passed",
            "public_surface_lineage": {
                "schema_version": "cocolon.emlis.public_surface_lineage.v1",
                "source_phase": "PublicObservationRecovery_P8_PublicMetaBoundaryProductQualityMeta",
                "candidate_source_kind": _COMPLETE_INITIAL,
                "selected_public_candidate_source_kind": _COMPLETE_INITIAL,
                "pre_public_candidate_source_kind": _COMPLETE_INITIAL,
                "final_public_candidate_source_kind": _COMPLETE_INITIAL,
                "complete_initial_surface_recomposition_final_used": True,
                "labelled_two_stage_surface_recomposition_final_used": False,
            },
            # Candidate source is present for diagnostics, but final_public is
            # intentionally empty because the post-final recovery was not applied.
            "phase20_13_post_final_gate_recovery": {
                "source_phase": "Phase20-13_Post_Final_Gate_Recovery",
                "recovery_context": "post_final_pre_return_gate",
                "applied": False,
                "candidate_source_kind": _LABELLED_TWO_STAGE,
                "public_candidate_source_kind": _LABELLED_TWO_STAGE,
                "selected_public_candidate_source_kind": _LABELLED_TWO_STAGE,
                "pre_public_candidate_source_kind": _COMPLETE_INITIAL,
                "final_public_candidate_source_kind": "",
                "complete_initial_surface_recomposition_attempted": True,
                "complete_initial_surface_recomposition_final_used": False,
                "labelled_two_stage_surface_recomposition_final_used": False,
            },
        },
        comment_text_present=True,
        subscription_tier="free",
    )

    lineage = public_meta["public_surface_lineage"]
    assert lineage["candidate_source_kind"] == _COMPLETE_INITIAL
    assert lineage["selected_public_candidate_source_kind"] == _COMPLETE_INITIAL
    assert lineage["final_public_candidate_source_kind"] == _COMPLETE_INITIAL
    assert lineage["pre_public_candidate_source_kind"] == _COMPLETE_INITIAL
    assert lineage["complete_initial_surface_recomposition_used"] is True
    assert lineage["complete_initial_surface_recomposition_final_used"] is True
    assert lineage["labelled_two_stage_surface_recomposition_used"] is False
    assert lineage["labelled_two_stage_surface_recomposition_final_used"] is False
    _assert_public_surface_lineage_guarded(public_meta)
