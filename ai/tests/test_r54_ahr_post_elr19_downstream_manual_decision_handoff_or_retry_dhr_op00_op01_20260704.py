# -*- coding: utf-8 -*-
"""R54-AHR Post-ELR19 downstream manual decision handoff-or-retry DHR-OP00/OP01 tests."""

from __future__ import annotations

from pathlib import Path
import sys

import pytest

TEST_DIR = Path(__file__).resolve().parent
if str(TEST_DIR) not in sys.path:
    sys.path.insert(0, str(TEST_DIR))

import emlis_ai_p7_r54_ahr_post_alr12_explicit_local_only_review_start_retry_operation_20260703 as elr
import emlis_ai_p7_r54_ahr_post_elr19_downstream_manual_decision_handoff_or_retry_20260704 as dhr
from test_r54_ahr_post_alr12_explicit_local_only_review_start_retry_operation_elr_op18_op19_20260703 import (
    _op17_waiting,
    _op19_closed,
)


def _assert_common_bodyfree_no_touch_no_promotion(material: dict[str, object]) -> None:
    assert material["body_free"] is True
    assert material["source_mode"] == dhr.P7_R54_AHR_POST_ELR19_DHR_SOURCE_MODE
    assert material["git_connection_required"] is False
    assert material["git_checked"] is False
    for field in dhr.P7_R54_AHR_POST_ELR19_DHR_REQUIRED_FALSE_FLAG_REFS:
        assert material[field] is False, field
    for marker_map_key in ("public_contract", "post_elr19_no_touch_contract", "body_free_markers"):
        assert material[marker_map_key]
        assert all(value is False for value in material[marker_map_key].values()), marker_map_key
    assert all(value is False for value in material["not_claimed_boundary"].values())


def test_dhr_op00_refreezes_scope_no_touch_no_promotion_after_elr_op19() -> None:
    material = dhr.build_p7_r54_ahr_post_elr19_dhr_op00_scope_no_touch_no_promotion_refreeze_after_elr_op19()

    assert set(material) == set(dhr.P7_R54_AHR_POST_ELR19_DHR_OP00_REQUIRED_FIELD_REFS)
    assert material["schema_version"] == dhr.P7_R54_AHR_POST_ELR19_DHR_OP00_SCHEMA_VERSION
    assert material["phase"] == dhr.P7_R54_AHR_POST_ELR19_DHR_PHASE
    assert material["selected_stage_ref"] == dhr.P7_R54_AHR_POST_ELR19_DHR_SELECTED_STAGE_REF
    assert material["current_hold_after_elr_op19_ref"] == dhr.P7_R54_AHR_POST_ELR19_DHR_CURRENT_HOLD_AFTER_ELR_OP19_REF
    assert material["current_default_next_required_step_ref"] == dhr.P7_R54_AHR_POST_ELR19_DHR_DEFAULT_NEXT_REQUIRED_STEP_REF
    assert material["dhr_op00_scope_confirmed"] is True
    assert material["dhr_op00_no_touch_boundary_confirmed"] is True
    assert material["dhr_op00_no_promotion_boundary_confirmed"] is True
    assert material["dhr_op00_does_not_intake_elr_op19_result_memo"] is True
    assert material["dhr_op00_does_not_execute_dmd_or_r52"] is True
    assert material["manual_decision_required_without_auto_execution"] is True
    assert tuple(material["implemented_steps"]) == dhr.P7_R54_AHR_POST_ELR19_DHR_OP00_IMPLEMENTED_STEPS
    assert tuple(material["not_yet_implemented_steps"]) == dhr.P7_R54_AHR_POST_ELR19_DHR_OP00_NOT_YET_IMPLEMENTED_STEPS
    assert material["next_required_step"] == dhr.P7_R54_AHR_POST_ELR19_DHR_OP01_STEP_REF
    assert tuple(material["not_stage_refs"]) == dhr.P7_R54_AHR_POST_ELR19_DHR_NOT_STAGE_REFS
    assert tuple(material["claim_boundary_refs"]) == dhr.P7_R54_AHR_POST_ELR19_DHR_CLAIM_BOUNDARY_REFS
    assert tuple(material["not_claimed_boundary_refs"]) == dhr.P7_R54_AHR_POST_ELR19_DHR_NOT_CLAIMED_BOUNDARY_REFS
    assert dhr.assert_p7_r54_ahr_post_elr19_dhr_op00_scope_no_touch_no_promotion_refreeze_after_elr_op19_contract(material) is True
    _assert_common_bodyfree_no_touch_no_promotion(material)


@pytest.mark.parametrize(
    ("field", "bad_value"),
    [
        ("body_free", False),
        ("git_checked", True),
        ("dhr_op00_no_touch_boundary_confirmed", False),
        ("dhr_op00_no_promotion_boundary_confirmed", False),
        ("dhr_op00_does_not_start_p5_p6_p8_p7_or_release", False),
        ("p8_start_allowed", True),
        ("release_allowed", True),
        ("manual_decision_auto_executes_downstream", True),
        ("next_required_step", dhr.P7_R54_AHR_POST_ELR19_DHR_OP02_STEP_REF),
    ],
)
def test_dhr_op00_contract_rejects_scope_or_promotion_mutations(field: str, bad_value: object) -> None:
    material = dhr.build_p7_r54_ahr_post_elr19_dhr_op00_scope_no_touch_no_promotion_refreeze_after_elr_op19()
    material[field] = bad_value

    with pytest.raises(ValueError):
        dhr.assert_p7_r54_ahr_post_elr19_dhr_op00_scope_no_touch_no_promotion_refreeze_after_elr_op19_contract(material)


def test_dhr_op00_contract_rejects_public_contract_marker_mutation() -> None:
    material = dhr.build_p7_r54_ahr_post_elr19_dhr_op00_scope_no_touch_no_promotion_refreeze_after_elr_op19()
    material["public_contract"]["api_response_key_added"] = True

    with pytest.raises(ValueError):
        dhr.assert_p7_r54_ahr_post_elr19_dhr_op00_scope_no_touch_no_promotion_refreeze_after_elr_op19_contract(material)


def test_dhr_op00_contract_rejects_forbidden_top_level_payload_key() -> None:
    material = dhr.build_p7_r54_ahr_post_elr19_dhr_op00_scope_no_touch_no_promotion_refreeze_after_elr_op19()
    material["raw_input"] = "must never pass"

    with pytest.raises(ValueError):
        dhr.assert_p7_r54_ahr_post_elr19_dhr_op00_scope_no_touch_no_promotion_refreeze_after_elr_op19_contract(material)


def test_dhr_op01_accepts_elr_op19_closed_bodyfree_without_dmd_or_promotion_execution() -> None:
    op00 = dhr.build_p7_r54_ahr_post_elr19_dhr_op00_scope_no_touch_no_promotion_refreeze_after_elr_op19()
    material = dhr.build_p7_r54_ahr_post_elr19_dhr_op01_elr_op19_result_memo_validation_closure_intake(
        scope_no_touch_no_promotion_refreeze=op00,
        elr_op19_result_memo_validation_closure=_op19_closed(),
    )

    assert set(material) == set(dhr.P7_R54_AHR_POST_ELR19_DHR_OP01_REQUIRED_FIELD_REFS)
    assert material["schema_version"] == dhr.P7_R54_AHR_POST_ELR19_DHR_OP01_SCHEMA_VERSION
    assert material["op00_contract_valid"] is True
    assert material["elr_op19_result_memo_present"] is True
    assert material["elr_op19_contract_valid"] is True
    assert material["elr_op19_result_memo_validation_closure_status_ref"] == elr.P7_R54_AHR_POST_ALR12_ELR_OP19_STATUS_CLOSED_BODYFREE_REF
    assert material["elr_op19_intake_status_ref"] == dhr.P7_R54_AHR_POST_ELR19_DHR_ELR_OP19_INTAKE_CLOSED_BODYFREE_REF
    assert material["elr_op19_closed_bodyfree"] is True
    assert material["elr_op19_op18_downstream_manual_decision_hold_ready"] is True
    assert material["elr_op19_op18_downstream_manual_decision_required_without_auto_execution"] is True
    assert material["elr_op19_target_tests_passed_count"] == 31
    assert material["elr_op19_selected_regression_passed_count"] == 390
    assert material["elr_op19_compileall_passed"] is True
    assert material["elr_op19_forbidden_payload_key_path_refs"] == []
    assert material["elr_op19_body_like_value_path_refs"] == []
    assert material["elr_op19_promotion_claim_refs"] == []
    assert material["actual_review_execution_claimed_by_dhr_op01"] is False
    assert material["dmd_execution_started_here"] is False
    assert material["dhr_op01_ready_for_elr_op18_manual_hold_intake"] is True
    assert material["next_required_step"] == dhr.P7_R54_AHR_POST_ELR19_DHR_OP02_STEP_REF
    assert dhr.assert_p7_r54_ahr_post_elr19_dhr_op01_elr_op19_result_memo_validation_closure_intake_contract(material) is True
    _assert_common_bodyfree_no_touch_no_promotion(material)


def test_dhr_op01_waits_when_elr_op19_is_waiting_for_manual_hold() -> None:
    op18_waiting = elr.build_p7_r54_ahr_post_alr12_elr_op18_downstream_non_promotion_manual_decision_hold(
        op17_dmd_compatible_actual_operation_evidence_receipt_adapter_handoff_candidate=_op17_waiting(),
    )
    op19_waiting = elr.build_p7_r54_ahr_post_alr12_elr_op19_result_memo_validation_closure(
        op18_downstream_non_promotion_manual_decision_hold=op18_waiting,
    )
    material = dhr.build_p7_r54_ahr_post_elr19_dhr_op01_elr_op19_result_memo_validation_closure_intake(
        elr_op19_result_memo_validation_closure=op19_waiting,
    )

    assert material["elr_op19_intake_status_ref"] == dhr.P7_R54_AHR_POST_ELR19_DHR_ELR_OP19_INTAKE_WAITING_FOR_MANUAL_HOLD_REF
    assert material["elr_op19_waiting_for_manual_hold"] is True
    assert material["elr_op19_closed_bodyfree"] is False
    assert material["dhr_op01_waiting_for_elr_op19_closure"] is True
    assert material["next_required_step"] == dhr.P7_R54_AHR_POST_ELR19_DHR_NEXT_STEP_WAIT_FOR_ELR_OP19_CLOSURE_REF
    assert dhr.assert_p7_r54_ahr_post_elr19_dhr_op01_elr_op19_result_memo_validation_closure_intake_contract(material) is True
    _assert_common_bodyfree_no_touch_no_promotion(material)


def test_dhr_op01_repairs_when_elr_op19_carries_promotion_claim() -> None:
    op19 = _op19_closed()
    op19["release_allowed"] = True
    material = dhr.build_p7_r54_ahr_post_elr19_dhr_op01_elr_op19_result_memo_validation_closure_intake(
        elr_op19_result_memo_validation_closure=op19,
    )

    assert material["elr_op19_intake_status_ref"] == dhr.P7_R54_AHR_POST_ELR19_DHR_ELR_OP19_INTAKE_REPAIR_REQUIRED_REF
    assert material["elr_op19_contract_valid"] is False
    assert material["elr_op19_promotion_claim_ref_count"] > 0
    assert "elr_op19_promotion_claim_detected" in material["dhr_op01_blocker_refs"]
    assert "elr_op19_result_memo_contract_invalid" in material["dhr_op01_blocker_refs"]
    assert material["dhr_op01_repair_required"] is True
    assert material["next_required_step"] == dhr.P7_R54_AHR_POST_ELR19_DHR_NEXT_STEP_REPAIR_ELR_OP19_RESULT_MEMO_BOUNDARY_REF
    assert dhr.assert_p7_r54_ahr_post_elr19_dhr_op01_elr_op19_result_memo_validation_closure_intake_contract(material) is True
    _assert_common_bodyfree_no_touch_no_promotion(material)


def test_dhr_op01_repairs_forbidden_elr_op19_payload_key_without_leaking_body_value() -> None:
    op19 = _op19_closed()
    op19["question_text"] = "this question body must not leak"
    material = dhr.build_p7_r54_ahr_post_elr19_dhr_op01_elr_op19_result_memo_validation_closure_intake(
        elr_op19_result_memo_validation_closure=op19,
    )

    assert material["elr_op19_intake_status_ref"] == dhr.P7_R54_AHR_POST_ELR19_DHR_ELR_OP19_INTAKE_REPAIR_REQUIRED_REF
    assert material["elr_op19_forbidden_payload_key_path_count"] > 0
    assert "elr_op19_forbidden_payload_key_detected" in material["dhr_op01_blocker_refs"]
    assert "this question body must not leak" not in repr(material)
    assert dhr.assert_p7_r54_ahr_post_elr19_dhr_op01_elr_op19_result_memo_validation_closure_intake_contract(material) is True


def test_dhr_op01_missing_elr_op19_material_stops_before_op02() -> None:
    material = dhr.build_p7_r54_ahr_post_elr19_dhr_op01_elr_op19_result_memo_validation_closure_intake()

    assert material["elr_op19_intake_status_ref"] == dhr.P7_R54_AHR_POST_ELR19_DHR_ELR_OP19_INTAKE_MISSING_OR_INVALID_REF
    assert material["elr_op19_result_memo_present"] is False
    assert material["elr_op19_contract_valid"] is False
    assert material["elr_op19_missing_or_invalid"] is True
    assert material["dhr_op01_repair_required"] is True
    assert material["next_required_step"] == dhr.P7_R54_AHR_POST_ELR19_DHR_NEXT_STEP_REPAIR_ELR_OP19_RESULT_MEMO_BOUNDARY_REF
    assert dhr.assert_p7_r54_ahr_post_elr19_dhr_op01_elr_op19_result_memo_validation_closure_intake_contract(material) is True
    _assert_common_bodyfree_no_touch_no_promotion(material)


@pytest.mark.parametrize(
    ("field", "bad_value"),
    [
        ("elr_op19_intake_status_ref", dhr.P7_R54_AHR_POST_ELR19_DHR_ELR_OP19_INTAKE_WAITING_FOR_MANUAL_HOLD_REF),
        ("dhr_op01_ready_for_elr_op18_manual_hold_intake", False),
        ("dmd_execution_started_here", True),
        ("r52_actual_execution_started_here", True),
        ("p8_start_allowed", True),
        ("release_allowed", True),
        ("manual_decision_auto_executes_downstream", True),
        ("next_required_step", "P8_START"),
    ],
)
def test_dhr_op01_contract_rejects_closed_intake_mutations(field: str, bad_value: object) -> None:
    material = dhr.build_p7_r54_ahr_post_elr19_dhr_op01_elr_op19_result_memo_validation_closure_intake(
        elr_op19_result_memo_validation_closure=_op19_closed(),
    )
    material[field] = bad_value

    with pytest.raises(ValueError):
        dhr.assert_p7_r54_ahr_post_elr19_dhr_op01_elr_op19_result_memo_validation_closure_intake_contract(material)


def test_dhr_op00_op01_full_title_aliases_match_canonical_builders() -> None:
    canonical_op00 = dhr.build_p7_r54_ahr_post_elr19_dhr_op00_scope_no_touch_no_promotion_refreeze_after_elr_op19()
    alias_op00 = dhr.build_p7_r54_ahr_post_elr19_downstream_manual_decision_handoff_or_retry_dhr_op00_scope_no_touch_no_promotion_refreeze_after_elr_op19()
    canonical_op01 = dhr.build_p7_r54_ahr_post_elr19_dhr_op01_elr_op19_result_memo_validation_closure_intake(
        elr_op19_result_memo_validation_closure=_op19_closed(),
    )
    alias_op01 = dhr.build_p7_r54_ahr_post_elr19_downstream_manual_decision_handoff_or_retry_dhr_op01_elr_op19_result_memo_validation_closure_intake(
        elr_op19_result_memo_validation_closure=_op19_closed(),
    )

    assert canonical_op00 == alias_op00
    assert canonical_op01 == alias_op01
    assert dhr.assert_p7_r54_ahr_post_elr19_downstream_manual_decision_handoff_or_retry_dhr_op00_scope_no_touch_no_promotion_refreeze_after_elr_op19_contract(alias_op00) is True
    assert dhr.assert_p7_r54_ahr_post_elr19_downstream_manual_decision_handoff_or_retry_dhr_op01_elr_op19_result_memo_validation_closure_intake_contract(alias_op01) is True
