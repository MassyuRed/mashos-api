# -*- coding: utf-8 -*-
"""R54-AHR Post-DMH18 downstream manual decision triage DMD-OP00/OP01 tests."""

from __future__ import annotations

from copy import deepcopy
from pathlib import Path
import sys

import pytest

TEST_DIR = Path(__file__).resolve().parent
if str(TEST_DIR) not in sys.path:
    sys.path.insert(0, str(TEST_DIR))

import emlis_ai_p7_r54_ahr_post_dmh18_downstream_manual_decision_triage_20260703 as dmd
import emlis_ai_p7_r54_ahr_post_pmn23_downstream_manual_decision_hold_evidence_intake_20260701 as dmh
_READY_OP18_CACHE: dict[str, object] | None = None


def _ready_op18() -> dict[str, object]:
    """Return a contract-valid OP18 ready material without rebuilding OP00-OP17.

    DMH-OP18's contract checks the finalizer fields, not the original OP17
    object.  Mutating the lightweight blocked builder output keeps this target
    focused on DMD-OP00/OP01 and avoids re-running the whole DMH evidence chain.
    The full DMH-OP18 regression is still run separately.
    """

    global _READY_OP18_CACHE
    if _READY_OP18_CACHE is None:
        material = _blocked_op18()
        material.update(
            {
                "op17_schema_version": "op17_schema_contract_valid_fixture",
                "op17_material_ref": "op17_contract_valid_ready_fixture",
                "op17_next_required_step": dmh.P7_R54_AHR_POST_PMN23_DMH_OP18_STEP_REF,
                "op17_dmh_ready": True,
                "op17_postcr22_ex07_ex18_reentry_envelope_ready": True,
                "op17_actual_review_evidence_complete_from_real_review": True,
                "op17_actual_review_evidence_complete_predicate_carried_into_reentry_envelope": True,
                "dmh_op18_status_ref": dmh.P7_R54_AHR_POST_PMN23_DMH_OP18_READY_STATUS_REF,
                "dmh_op18_ready": True,
                "dmh_op18_reason_refs": list(dmh.P7_R54_AHR_POST_PMN23_DMH_OP18_READY_REASON_REFS),
                "dmh_op18_reason_ref_count": len(dmh.P7_R54_AHR_POST_PMN23_DMH_OP18_READY_REASON_REFS),
                "dmh_op18_blocker_refs": [],
                "dmh_op18_blocker_ref_count": 0,
                "result_memo_bodyfree_closed": True,
                "downstream_manual_decision_hold_state_ref": dmh.P7_R54_AHR_POST_PMN23_DMH_OP18_DOWNSTREAM_MANUAL_DECISION_HOLD_STATE_REF,
                "downstream_manual_decision_hold_finalized": True,
                "manual_downstream_decision_required": True,
                "actual_review_evidence_complete_candidate_from_real_review": True,
                "actual_review_evidence_complete_from_real_review": True,
                "actual_review_evidence_complete_predicate_carried_into_reentry_envelope": True,
                "evidence_completion_state_ref": dmh.P7_R54_AHR_POST_PMN23_DMH_OP18_EVIDENCE_COMPLETE_STATE_REF,
                "evidence_incomplete_continue_or_retry_required": False,
                "bodyfree_evidence_boundary_repair_required": False,
                "postcr22_ex07_ex18_reentry_ready_candidate": True,
                "implemented_steps": list(dmh.P7_R54_AHR_POST_PMN23_DMH_OP18_IMPLEMENTED_STEPS),
                "not_yet_implemented_steps": list(dmh.P7_R54_AHR_POST_PMN23_DMH_OP18_NOT_YET_IMPLEMENTED_STEPS),
                "next_required_step": dmh.P7_R54_AHR_POST_PMN23_DMH_OP18_NEXT_REQUIRED_STEP_EVIDENCE_COMPLETE_REF,
            }
        )
        assert dmh.assert_p7_r54_ahr_post_pmn23_dmh_op18_result_memo_downstream_manual_decision_hold_finalizer_contract(material) is True
        _READY_OP18_CACHE = material
    return deepcopy(_READY_OP18_CACHE)


def _blocked_op18() -> dict[str, object]:
    material = dmh.build_p7_r54_ahr_post_pmn23_dmh_op18_result_memo_downstream_manual_decision_hold_finalizer()
    assert material["dmh_op18_status_ref"] == dmh.P7_R54_AHR_POST_PMN23_DMH_OP18_BLOCKED_STATUS_REF
    assert dmh.assert_p7_r54_ahr_post_pmn23_dmh_op18_result_memo_downstream_manual_decision_hold_finalizer_contract(material) is True
    return material


def _assert_common_bodyfree_no_touch_no_promotion(material: dict[str, object]) -> None:
    assert material["body_free"] is True
    assert material["git_connection_required"] is False
    assert material["git_checked"] is False
    for field in dmd.P7_R54_AHR_POST_DMH18_DMD_REQUIRED_FALSE_FLAG_REFS:
        assert material[field] is False, field
    for marker_map_key in ("public_contract", "post_dmh18_no_touch_contract", "body_free_markers"):
        assert material[marker_map_key]
        assert all(value is False for value in material[marker_map_key].values()), marker_map_key
    assert all(value is False for value in material["not_claimed_boundary"].values())


def test_dmd_op00_refreezes_scope_no_touch_no_promotion_after_dmh_op18() -> None:
    material = dmd.build_p7_r54_ahr_post_dmh18_dmd_op00_scope_no_touch_no_promotion_refreeze()

    assert set(material) == set(dmd.P7_R54_AHR_POST_DMH18_DMD_OP00_REQUIRED_FIELD_REFS)
    assert material["schema_version"] == dmd.P7_R54_AHR_POST_DMH18_DMD_OP00_SCHEMA_VERSION
    assert material["phase"] == dmd.P7_R54_AHR_POST_DMH18_DMD_PHASE
    assert material["source_mode"] == dmd.P7_R54_AHR_POST_DMH18_DMD_SOURCE_MODE
    assert material["selected_stage_ref"] == dmd.P7_R54_AHR_POST_DMH18_DMD_SELECTED_STAGE_REF
    assert material["dmd_op00_scope_confirmed"] is True
    assert material["dmd_op00_no_touch_boundary_confirmed"] is True
    assert material["dmd_op00_no_promotion_boundary_confirmed"] is True
    assert material["dmd_op00_does_not_intake_op18_finalizer"] is True
    assert material["dmd_op00_does_not_generate_body_full_packet"] is True
    assert material["dmd_op00_does_not_run_actual_local_human_review"] is True
    assert material["dmd_op00_does_not_create_receipts_rows_or_disposal"] is True
    assert tuple(material["implemented_steps"]) == dmd.P7_R54_AHR_POST_DMH18_DMD_OP00_IMPLEMENTED_STEPS
    assert tuple(material["not_yet_implemented_steps"]) == dmd.P7_R54_AHR_POST_DMH18_DMD_OP00_NOT_YET_IMPLEMENTED_STEPS
    assert material["next_required_step"] == dmd.P7_R54_AHR_POST_DMH18_DMD_OP01_STEP_REF
    assert tuple(material["fixed_non_promotion_refs"]) == dmd.P7_R54_AHR_POST_DMH18_DMD_FIXED_NON_PROMOTION_REFS
    assert tuple(material["not_stage_refs"]) == dmd.P7_R54_AHR_POST_DMH18_DMD_NOT_STAGE_REFS
    assert dmd.assert_p7_r54_ahr_post_dmh18_dmd_op00_scope_no_touch_no_promotion_refreeze_contract(material) is True
    _assert_common_bodyfree_no_touch_no_promotion(material)


@pytest.mark.parametrize(
    ("field", "bad_value"),
    [
        ("body_free", False),
        ("git_checked", True),
        ("dmd_op00_no_touch_boundary_confirmed", False),
        ("dmd_op00_no_promotion_boundary_confirmed", False),
        ("dmd_op00_does_not_start_p8_p6_r52_or_release", False),
        ("p8_start_allowed", True),
        ("release_allowed", True),
        ("manual_decision_auto_executes_downstream", True),
        ("next_required_step", dmd.P7_R54_AHR_POST_DMH18_DMD_OP02_STEP_REF),
    ],
)
def test_dmd_op00_contract_rejects_scope_or_promotion_mutations(field: str, bad_value: object) -> None:
    material = dmd.build_p7_r54_ahr_post_dmh18_dmd_op00_scope_no_touch_no_promotion_refreeze()
    material[field] = bad_value

    with pytest.raises(ValueError):
        dmd.assert_p7_r54_ahr_post_dmh18_dmd_op00_scope_no_touch_no_promotion_refreeze_contract(material)


def test_dmd_op00_contract_rejects_public_contract_marker_mutation() -> None:
    material = dmd.build_p7_r54_ahr_post_dmh18_dmd_op00_scope_no_touch_no_promotion_refreeze()
    material["public_contract"]["api_response_key_added"] = True

    with pytest.raises(ValueError):
        dmd.assert_p7_r54_ahr_post_dmh18_dmd_op00_scope_no_touch_no_promotion_refreeze_contract(material)


def test_dmd_op00_contract_rejects_forbidden_top_level_payload_key() -> None:
    material = dmd.build_p7_r54_ahr_post_dmh18_dmd_op00_scope_no_touch_no_promotion_refreeze()
    material["raw_input"] = "must never pass"

    with pytest.raises(ValueError):
        dmd.assert_p7_r54_ahr_post_dmh18_dmd_op00_scope_no_touch_no_promotion_refreeze_contract(material)


def test_dmd_op01_accepts_ready_op18_finalizer_but_keeps_candidate_only_and_passes_to_op02() -> None:
    op00 = dmd.build_p7_r54_ahr_post_dmh18_dmd_op00_scope_no_touch_no_promotion_refreeze()
    material = dmd.build_p7_r54_ahr_post_dmh18_dmd_op01_op18_finalizer_bodyfree_intake(
        scope_no_touch_no_promotion_refreeze=op00,
        op18_result_memo_downstream_manual_decision_hold_finalizer=_ready_op18(),
    )

    assert set(material) == set(dmd.P7_R54_AHR_POST_DMH18_DMD_OP01_REQUIRED_FIELD_REFS)
    assert material["schema_version"] == dmd.P7_R54_AHR_POST_DMH18_DMD_OP01_SCHEMA_VERSION
    assert material["dmd_op01_status_ref"] == dmd.P7_R54_AHR_POST_DMH18_DMD_OP01_STATUS_ACCEPTED_REF
    assert material["dmd_op01_ready"] is True
    assert material["op18_finalizer_present"] is True
    assert material["op18_contract_valid"] is True
    assert material["op18_dmh_op18_ready"] is True
    assert material["op18_candidate_supported"] is True
    assert material["op18_actual_review_evidence_complete_from_real_review"] is True
    assert material["op18_real_operation_claim_detected"] is False
    assert material["op18_ready_path_not_promoted_to_real_operation_claim"] is True
    assert material["candidate_supported_not_promoted_to_claimed_from_real_operation"] is True
    assert material["actual_review_evidence_complete_from_real_operation_claimed_by_dmd_op01"] is False
    assert material["op18_intake_branch_candidate_ref"] == dmd.P7_R54_AHR_POST_DMH18_DMD_BRANCH_CANDIDATE_OP18_ACCEPTED_REF
    assert material["next_required_step"] == dmd.P7_R54_AHR_POST_DMH18_DMD_NEXT_STEP_DMD_OP02_REF
    assert tuple(material["implemented_steps"]) == dmd.P7_R54_AHR_POST_DMH18_DMD_OP01_IMPLEMENTED_STEPS
    assert dmd.assert_p7_r54_ahr_post_dmh18_dmd_op01_op18_finalizer_bodyfree_intake_contract(material) is True
    _assert_common_bodyfree_no_touch_no_promotion(material)


def test_dmd_op01_accepts_valid_blocked_op18_finalizer_as_bodyfree_incomplete_candidate_for_later_separation() -> None:
    material = dmd.build_p7_r54_ahr_post_dmh18_dmd_op01_op18_finalizer_bodyfree_intake(
        op18_result_memo_downstream_manual_decision_hold_finalizer=_blocked_op18(),
    )

    assert material["dmd_op01_status_ref"] == dmd.P7_R54_AHR_POST_DMH18_DMD_OP01_STATUS_ACCEPTED_REF
    assert material["dmd_op01_ready"] is True
    assert material["op18_contract_valid"] is True
    assert material["op18_dmh_op18_ready"] is False
    assert material["op18_evidence_incomplete_continue_or_retry_required"] is True
    assert material["op18_intake_branch_candidate_ref"] == dmd.P7_R54_AHR_POST_DMH18_DMD_BRANCH_EVIDENCE_INCOMPLETE_REF
    assert material["next_required_step"] == dmd.P7_R54_AHR_POST_DMH18_DMD_NEXT_STEP_DMD_OP02_REF
    assert dmd.assert_p7_r54_ahr_post_dmh18_dmd_op01_op18_finalizer_bodyfree_intake_contract(material) is True
    _assert_common_bodyfree_no_touch_no_promotion(material)


def test_dmd_op01_missing_op18_finalizer_goes_to_evidence_incomplete_without_op02_pass() -> None:
    material = dmd.build_p7_r54_ahr_post_dmh18_dmd_op01_op18_finalizer_bodyfree_intake()

    assert material["dmd_op01_status_ref"] == dmd.P7_R54_AHR_POST_DMH18_DMD_OP01_STATUS_MISSING_REF
    assert material["dmd_op01_ready"] is False
    assert material["op18_finalizer_present"] is False
    assert material["op18_contract_valid"] is False
    assert material["op18_intake_branch_candidate_ref"] == dmd.P7_R54_AHR_POST_DMH18_DMD_BRANCH_EVIDENCE_INCOMPLETE_REF
    assert "dmd_op01_op18_finalizer_missing" in material["dmd_op01_blocker_refs"]
    assert material["next_required_step"] == dmd.P7_R54_AHR_POST_DMH18_DMD_NEXT_STEP_CONTINUE_OR_RETRY_ACTUAL_REVIEW_REF
    assert dmd.assert_p7_r54_ahr_post_dmh18_dmd_op01_op18_finalizer_bodyfree_intake_contract(material) is True
    _assert_common_bodyfree_no_touch_no_promotion(material)


def test_dmd_op01_forbidden_payload_in_op18_goes_to_repair_without_leaking_body_value() -> None:
    op18 = _ready_op18()
    op18["raw_input"] = "this body must not appear in DMD output"
    material = dmd.build_p7_r54_ahr_post_dmh18_dmd_op01_op18_finalizer_bodyfree_intake(
        op18_result_memo_downstream_manual_decision_hold_finalizer=op18,
    )

    assert material["dmd_op01_status_ref"] == dmd.P7_R54_AHR_POST_DMH18_DMD_OP01_STATUS_INVALID_OR_REPAIR_REQUIRED_REF
    assert material["op18_intake_branch_candidate_ref"] == dmd.P7_R54_AHR_POST_DMH18_DMD_BRANCH_REPAIR_REQUIRED_REF
    assert material["next_required_step"] == dmd.P7_R54_AHR_POST_DMH18_DMD_NEXT_STEP_STOP_AND_REPAIR_BODYFREE_REF
    assert material["op18_forbidden_payload_key_path_count"] == 1
    assert material["op18_forbidden_payload_key_paths"] == ["op18_finalizer.raw_input"]
    assert "this body must not appear" not in repr(material)
    assert dmd.assert_p7_r54_ahr_post_dmh18_dmd_op01_op18_finalizer_bodyfree_intake_contract(material) is True
    _assert_common_bodyfree_no_touch_no_promotion(material)


def test_dmd_op01_promotion_claim_in_op18_goes_to_repair_without_downstream_execution() -> None:
    op18 = _ready_op18()
    op18["p8_start_allowed"] = True
    material = dmd.build_p7_r54_ahr_post_dmh18_dmd_op01_op18_finalizer_bodyfree_intake(
        op18_result_memo_downstream_manual_decision_hold_finalizer=op18,
    )

    assert material["dmd_op01_status_ref"] == dmd.P7_R54_AHR_POST_DMH18_DMD_OP01_STATUS_INVALID_OR_REPAIR_REQUIRED_REF
    assert material["op18_intake_branch_candidate_ref"] == dmd.P7_R54_AHR_POST_DMH18_DMD_BRANCH_REPAIR_REQUIRED_REF
    assert "p8_start_allowed" in material["op18_promotion_claim_refs"]
    assert material["p8_start_allowed"] is False
    assert material["manual_decision_auto_executes_downstream"] is False
    assert material["next_required_step"] == dmd.P7_R54_AHR_POST_DMH18_DMD_NEXT_STEP_STOP_AND_REPAIR_BODYFREE_REF
    assert dmd.assert_p7_r54_ahr_post_dmh18_dmd_op01_op18_finalizer_bodyfree_intake_contract(material) is True
    _assert_common_bodyfree_no_touch_no_promotion(material)


def test_dmd_op01_contract_rejects_candidate_to_real_operation_promotion_mutation() -> None:
    material = dmd.build_p7_r54_ahr_post_dmh18_dmd_op01_op18_finalizer_bodyfree_intake(
        op18_result_memo_downstream_manual_decision_hold_finalizer=_ready_op18(),
    )
    material["actual_review_evidence_complete_from_real_operation_claimed_by_dmd_op01"] = True

    with pytest.raises(ValueError):
        dmd.assert_p7_r54_ahr_post_dmh18_dmd_op01_op18_finalizer_bodyfree_intake_contract(material)


def test_dmd_op01_alias_builder_and_contract_match_canonical_functions() -> None:
    material = dmd.build_p7_r54_ahr_post_dmh18_downstream_manual_decision_op18_finalizer_bodyfree_intake(
        op18_result_memo_downstream_manual_decision_hold_finalizer=_ready_op18(),
    )

    assert material["dmd_op01_status_ref"] == dmd.P7_R54_AHR_POST_DMH18_DMD_OP01_STATUS_ACCEPTED_REF
    assert dmd.assert_p7_r54_ahr_post_dmh18_downstream_manual_decision_op18_finalizer_bodyfree_intake_contract(material) is True


def test_dmd_op00_op01_result_memo_is_bodyfree_and_limited_to_current_scope() -> None:
    result_memo = TEST_DIR / "R54_AHR_PostDMH18_DownstreamManualDecision_ActualEvidenceStatusTriage_DMD_OP00_OP01_Result_20260703.md"
    text = result_memo.read_text(encoding="utf-8")

    for heading in (
        "## 1. Implementation scope",
        "## 2. Changed files",
        "## 3. DMD-OP00",
        "## 4. DMD-OP01",
        "## 5. Test results",
        "## 6. Not claimed",
    ):
        assert heading in text
    assert "DMD-OP02" in text
    assert "not implemented" in text
    forbidden_literals = (
        "raw_input:",
        "comment_text:",
        "question_text:",
        "draft_question_text:",
        "terminal output body",
    )
    for literal in forbidden_literals:
        assert literal not in text
