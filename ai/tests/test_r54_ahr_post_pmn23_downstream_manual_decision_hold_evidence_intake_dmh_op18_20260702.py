# -*- coding: utf-8 -*-
"""R54-AHR Post-PMN23 downstream manual decision hold DMH-OP18 tests."""

from __future__ import annotations

from copy import deepcopy
from pathlib import Path
import sys

import pytest

TEST_DIR = Path(__file__).resolve().parent
if str(TEST_DIR) not in sys.path:
    sys.path.insert(0, str(TEST_DIR))

import emlis_ai_p7_r54_ahr_post_pmn23_downstream_manual_decision_hold_evidence_intake_20260701 as dmh
import test_r54_ahr_post_pmn23_downstream_manual_decision_hold_evidence_intake_dmh_op16_op17_20260702 as dmh_op16_op17_prev

_READY_OP17_CACHE: dict[str, object] | None = None
_READY_OP18_CACHE: dict[str, object] | None = None


def _ready_op17() -> dict[str, object]:
    global _READY_OP17_CACHE
    if _READY_OP17_CACHE is None:
        material = dmh_op16_op17_prev._ready_op17()
        assert dmh.assert_p7_r54_ahr_post_pmn23_dmh_op17_postcr22_ex07_ex18_actual_evidence_reentry_envelope_contract(material) is True
        _READY_OP17_CACHE = material
    return deepcopy(_READY_OP17_CACHE)


def _build_op18(**overrides: dict[str, object]) -> dict[str, object]:
    kwargs: dict[str, object] = {
        "postcr22_ex07_ex18_actual_evidence_reentry_envelope": _ready_op17(),
    }
    kwargs.update(overrides)
    return dmh.build_p7_r54_ahr_post_pmn23_dmh_op18_result_memo_downstream_manual_decision_hold_finalizer(**kwargs)


def _ready_op18() -> dict[str, object]:
    global _READY_OP18_CACHE
    if _READY_OP18_CACHE is None:
        material = _build_op18()
        assert dmh.assert_p7_r54_ahr_post_pmn23_dmh_op18_result_memo_downstream_manual_decision_hold_finalizer_contract(material) is True
        _READY_OP18_CACHE = material
    return deepcopy(_READY_OP18_CACHE)


def _assert_bodyfree_no_touch_no_downstream(material: dict[str, object], *, complete_allowed: bool) -> None:
    assert material["body_free"] is True
    for key in dmh.P7_R54_AHR_POST_PMN23_DMH_REQUIRED_FALSE_FLAG_REFS:
        expected = complete_allowed if key == "actual_review_evidence_complete_from_real_review" else False
        assert material[key] is expected, key
    for marker_map_key in ("public_contract", "post_pmn23_no_touch_contract", "body_free_markers"):
        assert material[marker_map_key]
        assert all(value is False for value in material[marker_map_key].values()), marker_map_key
    for forbidden_key in dmh.P7_R54_AHR_POST_PMN23_DMH_FORBIDDEN_PAYLOAD_KEY_REFS:
        assert forbidden_key not in material, forbidden_key
    assert material["postcr22_ex07_ex18_reentry_executed_here"] is False
    assert material["r52_actual_execution_started_here"] is False
    assert material["r52_actual_execution_confirmed"] is False
    assert material["p5_final_allowed"] is False
    assert material["p6_start_allowed"] is False
    assert material["p8_start_allowed"] is False
    assert material["p7_complete"] is False
    assert material["release_allowed"] is False
    assert material["manual_decision_auto_executes_downstream"] is False


def test_dmh_op18_finalizes_bodyfree_result_memo_and_downstream_manual_decision_hold_without_auto_execution() -> None:
    material = _ready_op18()

    assert set(material) == set(dmh.P7_R54_AHR_POST_PMN23_DMH_OP18_REQUIRED_FIELD_REFS)
    assert material["schema_version"] == dmh.P7_R54_AHR_POST_PMN23_DMH_OP18_RESULT_MEMO_DOWNSTREAM_MANUAL_DECISION_HOLD_FINALIZER_SCHEMA_VERSION
    assert material["operation_step_ref"] == dmh.P7_R54_AHR_POST_PMN23_DMH_OP18_STEP_REF
    assert material["dmh_op18_status_ref"] == dmh.P7_R54_AHR_POST_PMN23_DMH_OP18_READY_STATUS_REF
    assert tuple(material["dmh_op18_allowed_status_refs"]) == dmh.P7_R54_AHR_POST_PMN23_DMH_OP18_ALLOWED_STATUS_REFS
    assert material["dmh_op18_ready"] is True
    assert tuple(material["dmh_op18_reason_refs"]) == dmh.P7_R54_AHR_POST_PMN23_DMH_OP18_READY_REASON_REFS
    assert material["dmh_op18_blocker_refs"] == []
    assert material["result_memo_finalizer_ref"] == dmh.P7_R54_AHR_POST_PMN23_DMH_OP18_FINALIZER_REF
    assert material["result_memo_ref"] == dmh.P7_R54_AHR_POST_PMN23_DMH_OP18_RESULT_MEMO_REF
    assert material["result_memo_bodyfree_closed"] is True
    assert tuple(material["result_memo_required_section_refs"]) == dmh.P7_R54_AHR_POST_PMN23_DMH_OP18_RESULT_MEMO_REQUIRED_SECTION_REFS
    assert material["result_memo_required_section_ref_count"] == len(dmh.P7_R54_AHR_POST_PMN23_DMH_OP18_RESULT_MEMO_REQUIRED_SECTION_REFS)
    assert material["result_memo_contains_no_body_question_path_hash_or_terminal_output"] is True
    assert material["downstream_manual_decision_hold_ref"] == dmh.P7_R54_AHR_POST_PMN23_DMH_DOWNSTREAM_MANUAL_DECISION_HOLD_REF
    assert material["downstream_manual_decision_hold_state_ref"] == dmh.P7_R54_AHR_POST_PMN23_DMH_OP18_DOWNSTREAM_MANUAL_DECISION_HOLD_STATE_REF
    assert material["downstream_manual_decision_hold_finalized"] is True
    assert material["manual_downstream_decision_required"] is True
    assert material["actual_review_evidence_complete_candidate_from_real_review"] is True
    assert material["actual_review_evidence_complete_from_real_review"] is True
    assert material["actual_review_evidence_complete_from_real_operation_claimed_here"] is False
    assert material["evidence_completion_state_ref"] == dmh.P7_R54_AHR_POST_PMN23_DMH_OP18_EVIDENCE_COMPLETE_STATE_REF
    assert material["postcr22_ex07_ex18_reentry_ready_candidate"] is True
    assert tuple(material["fixed_non_promotion_refs"]) == dmh.P7_R54_AHR_POST_PMN23_DMH_OP18_FIXED_NON_PROMOTION_REFS
    assert tuple(material["implemented_steps"]) == dmh.P7_R54_AHR_POST_PMN23_DMH_OP18_IMPLEMENTED_STEPS
    assert tuple(material["not_yet_implemented_steps"]) == dmh.P7_R54_AHR_POST_PMN23_DMH_OP18_NOT_YET_IMPLEMENTED_STEPS
    assert material["next_required_step"] == dmh.P7_R54_AHR_POST_PMN23_DMH_OP18_NEXT_REQUIRED_STEP_EVIDENCE_COMPLETE_REF
    _assert_bodyfree_no_touch_no_downstream(material, complete_allowed=True)


def test_dmh_op18_alias_builder_and_contract_match_canonical_functions() -> None:
    material = dmh.build_p7_r54_ahr_post_pmn23_downstream_manual_decision_hold_result_memo_downstream_manual_decision_hold_finalizer_bodyfree(
        postcr22_ex07_ex18_actual_evidence_reentry_envelope=_ready_op17()
    )

    assert material["dmh_op18_ready"] is True
    assert dmh.assert_p7_r54_ahr_post_pmn23_downstream_manual_decision_hold_result_memo_downstream_manual_decision_hold_finalizer_bodyfree_contract(material) is True


def test_dmh_op18_blocks_with_continue_or_retry_step_when_op17_envelope_is_missing() -> None:
    material = dmh.build_p7_r54_ahr_post_pmn23_dmh_op18_result_memo_downstream_manual_decision_hold_finalizer()

    assert material["dmh_op18_ready"] is False
    assert material["dmh_op18_status_ref"] == dmh.P7_R54_AHR_POST_PMN23_DMH_OP18_BLOCKED_STATUS_REF
    assert "dmh_op18_op17_postcr22_ex07_ex18_reentry_envelope_missing" in material["dmh_op18_blocker_refs"]
    assert material["next_required_step"] == dmh.P7_R54_AHR_POST_PMN23_DMH_OP18_NEXT_REQUIRED_STEP_EVIDENCE_INCOMPLETE_REF
    assert material["evidence_completion_state_ref"] == dmh.P7_R54_AHR_POST_PMN23_DMH_OP18_EVIDENCE_INCOMPLETE_STATE_REF
    assert material["evidence_incomplete_continue_or_retry_required"] is True
    assert material["bodyfree_evidence_boundary_repair_required"] is False
    assert material["actual_review_evidence_complete_from_real_review"] is False
    assert tuple(material["implemented_steps"]) == dmh.P7_R54_AHR_POST_PMN23_DMH_OP17_IMPLEMENTED_STEPS
    assert tuple(material["not_yet_implemented_steps"]) == dmh.P7_R54_AHR_POST_PMN23_DMH_OP17_NOT_YET_IMPLEMENTED_STEPS
    assert dmh.assert_p7_r54_ahr_post_pmn23_dmh_op18_result_memo_downstream_manual_decision_hold_finalizer_contract(material) is True
    _assert_bodyfree_no_touch_no_downstream(material, complete_allowed=False)


@pytest.mark.parametrize(
    ("field", "bad_value", "expected_blocker"),
    [
        ("dmh_op17_ready", False, "dmh_op18_op17_postcr22_ex07_ex18_reentry_envelope_invalid"),
        ("postcr22_ex07_ex18_reentry_envelope_ready", False, "dmh_op18_op17_postcr22_ex07_ex18_reentry_envelope_invalid"),
        ("actual_review_evidence_complete_from_real_review", False, "dmh_op18_op17_postcr22_ex07_ex18_reentry_envelope_invalid"),
        ("actual_review_evidence_complete_predicate_carried_into_reentry_envelope", False, "dmh_op18_op17_postcr22_ex07_ex18_reentry_envelope_invalid"),
        ("next_required_step", dmh.P7_R54_AHR_POST_PMN23_DMH_OP17_BLOCKED_NEXT_REQUIRED_STEP_REF, "dmh_op18_op17_postcr22_ex07_ex18_reentry_envelope_invalid"),
        ("postcr22_ex07_ex18_reentry_executed_here", True, "dmh_op18_op17_postcr22_ex07_ex18_reentry_envelope_invalid"),
        ("r52_actual_execution_started_here", True, "dmh_op18_op17_postcr22_ex07_ex18_reentry_envelope_invalid"),
        ("p8_start_allowed", True, "dmh_op18_op17_postcr22_ex07_ex18_reentry_envelope_invalid"),
        ("release_allowed", True, "dmh_op18_op17_postcr22_ex07_ex18_reentry_envelope_invalid"),
    ],
)
def test_dmh_op18_requires_op17_ready_envelope_and_routes_mutations_to_repair(field: str, bad_value: object, expected_blocker: str) -> None:
    op17 = _ready_op17()
    op17[field] = bad_value
    material = dmh.build_p7_r54_ahr_post_pmn23_dmh_op18_result_memo_downstream_manual_decision_hold_finalizer(
        postcr22_ex07_ex18_actual_evidence_reentry_envelope=op17
    )

    assert material["dmh_op18_ready"] is False
    assert material["dmh_op18_status_ref"] == dmh.P7_R54_AHR_POST_PMN23_DMH_OP18_REPAIR_REQUIRED_STATUS_REF
    assert expected_blocker in material["dmh_op18_blocker_refs"]
    assert material["next_required_step"] == dmh.P7_R54_AHR_POST_PMN23_DMH_OP18_NEXT_REQUIRED_STEP_REPAIR_REF
    assert material["evidence_completion_state_ref"] == dmh.P7_R54_AHR_POST_PMN23_DMH_OP18_REPAIR_REQUIRED_STATE_REF
    assert material["bodyfree_evidence_boundary_repair_required"] is True
    assert material["actual_review_evidence_complete_from_real_review"] is False
    assert dmh.assert_p7_r54_ahr_post_pmn23_dmh_op18_result_memo_downstream_manual_decision_hold_finalizer_contract(material) is True
    _assert_bodyfree_no_touch_no_downstream(material, complete_allowed=False)


def test_dmh_op18_detects_forbidden_payload_key_in_op17_and_routes_to_repair() -> None:
    op17 = _ready_op17()
    op17["raw_input"] = "must never pass"
    material = dmh.build_p7_r54_ahr_post_pmn23_dmh_op18_result_memo_downstream_manual_decision_hold_finalizer(
        postcr22_ex07_ex18_actual_evidence_reentry_envelope=op17
    )

    assert material["dmh_op18_ready"] is False
    assert material["dmh_op18_status_ref"] == dmh.P7_R54_AHR_POST_PMN23_DMH_OP18_REPAIR_REQUIRED_STATUS_REF
    assert "dmh_op18_op17_postcr22_ex07_ex18_reentry_envelope_invalid" in material["dmh_op18_blocker_refs"]
    assert "dmh_op18_op17_forbidden_payload_key_detected" in material["dmh_op18_blocker_refs"]
    assert material["op17_forbidden_payload_key_detected"] is True
    assert material["next_required_step"] == dmh.P7_R54_AHR_POST_PMN23_DMH_OP18_NEXT_REQUIRED_STEP_REPAIR_REF
    assert dmh.assert_p7_r54_ahr_post_pmn23_dmh_op18_result_memo_downstream_manual_decision_hold_finalizer_contract(material) is True


@pytest.mark.parametrize(
    ("field", "bad_value"),
    [
        ("dmh_op18_ready", False),
        ("dmh_op18_status_ref", dmh.P7_R54_AHR_POST_PMN23_DMH_OP18_BLOCKED_STATUS_REF),
        ("op17_dmh_ready", False),
        ("op17_postcr22_ex07_ex18_reentry_envelope_ready", False),
        ("op17_actual_review_evidence_complete_from_real_review", False),
        ("result_memo_bodyfree_closed", False),
        ("result_memo_includes_body_text", True),
        ("result_memo_includes_question_text", True),
        ("result_memo_includes_local_path", True),
        ("result_memo_includes_body_hash", True),
        ("result_memo_includes_terminal_output_body", True),
        ("result_memo_contains_no_body_question_path_hash_or_terminal_output", False),
        ("downstream_manual_decision_hold_finalized", False),
        ("manual_downstream_decision_required", False),
        ("manual_decision_auto_executes_downstream", True),
        ("actual_review_evidence_complete_from_real_review", False),
        ("actual_review_evidence_complete_from_real_operation_claimed_here", True),
        ("postcr22_ex07_ex18_reentry_executed_here", True),
        ("r52_actual_execution_started_here", True),
        ("r52_actual_execution_confirmed", True),
        ("p5_final_allowed", True),
        ("p6_start_allowed", True),
        ("p8_start_allowed", True),
        ("p7_complete", True),
        ("release_allowed", True),
        ("next_required_step", dmh.P7_R54_AHR_POST_PMN23_DMH_OP18_NEXT_REQUIRED_STEP_REPAIR_REF),
    ],
)
def test_dmh_op18_contract_rejects_ready_material_mutations(field: str, bad_value: object) -> None:
    material = _ready_op18()
    material[field] = bad_value

    with pytest.raises(ValueError):
        dmh.assert_p7_r54_ahr_post_pmn23_dmh_op18_result_memo_downstream_manual_decision_hold_finalizer_contract(material)


def test_dmh_op18_contract_rejects_result_memo_required_section_tampering() -> None:
    material = _ready_op18()
    material["result_memo_required_section_refs"] = list(material["result_memo_required_section_refs"][:-1])

    with pytest.raises(ValueError):
        dmh.assert_p7_r54_ahr_post_pmn23_dmh_op18_result_memo_downstream_manual_decision_hold_finalizer_contract(material)


def test_dmh_op18_contract_rejects_fixed_non_promotion_ref_tampering() -> None:
    material = _ready_op18()
    material["fixed_non_promotion_refs"] = list(material["fixed_non_promotion_refs"][:-1])

    with pytest.raises(ValueError):
        dmh.assert_p7_r54_ahr_post_pmn23_dmh_op18_result_memo_downstream_manual_decision_hold_finalizer_contract(material)


def test_dmh_op18_keeps_candidates_candidate_only_and_does_not_claim_release_or_full_backend_or_rn_green() -> None:
    material = _ready_op18()

    assert material["p5_confirmed_candidate_not_p5_final"] is True
    assert material["p6_candidate_only_not_p6_start"] is True
    assert material["p8_material_candidate_only_not_p8_start"] is True
    assert material["r52_handoff_candidate_not_r52_actual_execution"] is True
    assert material["op18_does_not_claim_full_backend_or_rn_green"] is True
    assert material["full_backend_suite_green"] is False
    assert material["full_backend_suite_green_confirmed"] is False
    assert material["full_backend_suite_green_claimed_here"] is False
    assert material["rn_contract_green"] is False
    assert material["rn_contract_green_confirmed"] is False
    assert material["rn_contract_green_claimed_here"] is False
    assert material["rn_real_device_modal_verified"] is False
    assert material["rn_real_device_modal_verified_claimed_here"] is False
    _assert_bodyfree_no_touch_no_downstream(material, complete_allowed=True)
