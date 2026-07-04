# -*- coding: utf-8 -*-
"""R54-AHR Post-DMD08 actual local review operation ALR-OP02/OP03 tests."""

from __future__ import annotations

from copy import deepcopy
from pathlib import Path
import sys

import pytest

TEST_DIR = Path(__file__).resolve().parent
if str(TEST_DIR) not in sys.path:
    sys.path.insert(0, str(TEST_DIR))

import emlis_ai_p7_r54_ahr_post_dmd08_continue_retry_actual_local_review_operation_20260703 as alr
import emlis_ai_p7_r54_ahr_post_dmh18_downstream_manual_decision_triage_20260703 as dmd
from test_r54_ahr_post_dmd08_continue_retry_actual_local_review_operation_alr_op00_op01_20260703 import (  # noqa: E501
    _complete_manual_decision_dmd08,
    _complete_receipt,
    _evidence_incomplete_dmd08,
    _repair_dmd08,
)


def _op01_evidence_incomplete() -> dict[str, object]:
    material = alr.build_p7_r54_ahr_post_dmd08_alr_op01_dmd_op08_result_memo_branch_intake(
        dmd_op08_bodyfree_result_memo_target_tests_regression_closure=_evidence_incomplete_dmd08(),
    )
    assert alr.assert_p7_r54_ahr_post_dmd08_alr_op01_dmd_op08_result_memo_branch_intake_contract(material) is True
    return material


def _op01_repair() -> dict[str, object]:
    material = alr.build_p7_r54_ahr_post_dmd08_alr_op01_dmd_op08_result_memo_branch_intake(
        dmd_op08_bodyfree_result_memo_target_tests_regression_closure=_repair_dmd08(),
    )
    assert alr.assert_p7_r54_ahr_post_dmd08_alr_op01_dmd_op08_result_memo_branch_intake_contract(material) is True
    return material


def _op01_complete() -> dict[str, object]:
    material = alr.build_p7_r54_ahr_post_dmd08_alr_op01_dmd_op08_result_memo_branch_intake(
        dmd_op08_bodyfree_result_memo_target_tests_regression_closure=_complete_manual_decision_dmd08(),
    )
    assert alr.assert_p7_r54_ahr_post_dmd08_alr_op01_dmd_op08_result_memo_branch_intake_contract(material) is True
    return material


def _continuable_session(**overrides: object) -> dict[str, object]:
    session: dict[str, object] = {
        "review_session_id": alr.P7_R54_AHR_POST_DMD08_ALR_DEFAULT_REVIEW_SESSION_ID,
        "session_source_kind_ref": alr.P7_R54_AHR_POST_DMD08_ALR_ACTUAL_LOCAL_ONLY_SOURCE_KIND_REF,
        "session_state_ref": "ALR_STATE_REVIEW_PAUSED_CONTINUE_ALLOWED",
        "body_free": True,
        "disposal_purge_finalized": False,
        "actual_rows_fixture_only": False,
    }
    session.update(overrides)
    return session


def _complete_receipt_for_alr() -> dict[str, object]:
    receipt = _complete_receipt()
    receipt["review_session_id"] = alr.P7_R54_AHR_POST_DMD08_ALR_DEFAULT_REVIEW_SESSION_ID
    receipt["operation_receipt_ref"] = "actual_receipt_bodyfree_alr_session"
    return receipt


def _assert_common_bodyfree_no_touch_no_promotion(material: dict[str, object]) -> None:
    assert material["body_free"] is True
    assert material["git_connection_required"] is False
    assert material["git_checked"] is False
    for field in alr.P7_R54_AHR_POST_DMD08_ALR_REQUIRED_FALSE_FLAG_REFS:
        assert material[field] is False, field
    for marker_map_key in ("public_contract", "post_dmd08_no_touch_contract", "body_free_markers"):
        assert material[marker_map_key]
        assert all(value is False for value in material[marker_map_key].values()), marker_map_key
    assert all(value is False for value in material["not_claimed_boundary"].values())


def test_alr_op02_inventory_marks_missing_existing_operation_material_without_resolving_action() -> None:
    material = alr.build_p7_r54_ahr_post_dmd08_alr_op02_existing_operation_material_inventory(
        dmd_op08_result_memo_branch_intake=_op01_evidence_incomplete(),
    )

    assert set(material) == set(alr.P7_R54_AHR_POST_DMD08_ALR_OP02_REQUIRED_FIELD_REFS)
    assert material["schema_version"] == alr.P7_R54_AHR_POST_DMD08_ALR_OP02_SCHEMA_VERSION
    assert material["operation_material_inventory_status_ref"] == alr.P7_R54_AHR_POST_DMD08_ALR_OP02_STATUS_MISSING_REF
    assert material["retry_or_start_candidate"] is True
    assert material["continue_candidate"] is False
    assert material["repair_stop_candidate"] is False
    assert material["complete_receipt_manual_decision_candidate"] is False
    assert material["existing_local_only_review_session_material_present"] is False
    assert material["next_required_step"] == alr.P7_R54_AHR_POST_DMD08_ALR_OP03_STEP_REF
    assert "selected_action_ref" not in material
    assert alr.assert_p7_r54_ahr_post_dmd08_alr_op02_existing_operation_material_inventory_contract(material) is True
    _assert_common_bodyfree_no_touch_no_promotion(material)


def test_alr_op02_inventory_allows_only_actual_bodyfree_continuable_session() -> None:
    material = alr.build_p7_r54_ahr_post_dmd08_alr_op02_existing_operation_material_inventory(
        dmd_op08_result_memo_branch_intake=_op01_evidence_incomplete(),
        existing_local_only_review_session_material_bodyfree=_continuable_session(),
    )

    assert material["operation_material_inventory_status_ref"] == alr.P7_R54_AHR_POST_DMD08_ALR_OP02_STATUS_CONTINUABLE_BODYFREE_REF
    assert material["continue_candidate"] is True
    assert material["retry_or_start_candidate"] is False
    assert material["repair_stop_candidate"] is False
    assert material["session_source_kind_ref"] == alr.P7_R54_AHR_POST_DMD08_ALR_ACTUAL_LOCAL_ONLY_SOURCE_KIND_REF
    assert material["session_state_ref"] in alr.P7_R54_AHR_POST_DMD08_ALR_CONTINUABLE_SESSION_STATE_REFS
    assert material["session_body_free"] is True
    assert material["review_session_id_consistent"] is True
    assert alr.assert_p7_r54_ahr_post_dmd08_alr_op02_existing_operation_material_inventory_contract(material) is True
    _assert_common_bodyfree_no_touch_no_promotion(material)


def test_alr_op02_inventory_rejects_helper_green_source_before_operation() -> None:
    material = alr.build_p7_r54_ahr_post_dmd08_alr_op02_existing_operation_material_inventory(
        dmd_op08_result_memo_branch_intake=_op01_evidence_incomplete(),
        existing_local_only_review_session_material_bodyfree=_continuable_session(session_source_kind_ref="helper_green"),
    )

    assert material["operation_material_inventory_status_ref"] == alr.P7_R54_AHR_POST_DMD08_ALR_OP02_STATUS_REPAIR_REQUIRED_REF
    assert material["repair_stop_candidate"] is True
    assert "helper_green" in material["operation_material_invalid_source_kind_refs"]
    assert "alr_op02_invalid_source_kind_detected" in material["alr_op02_blocker_refs"]
    assert material["actual_local_human_review_executed_here"] is False
    assert alr.assert_p7_r54_ahr_post_dmd08_alr_op02_existing_operation_material_inventory_contract(material) is True
    _assert_common_bodyfree_no_touch_no_promotion(material)


def test_alr_op02_inventory_complete_receipt_becomes_complete_candidate_but_no_downstream_execution() -> None:
    material = alr.build_p7_r54_ahr_post_dmd08_alr_op02_existing_operation_material_inventory(
        dmd_op08_result_memo_branch_intake=_op01_complete(),
        existing_actual_operation_receipt_bodyfree=_complete_receipt_for_alr(),
    )

    assert material["operation_material_inventory_status_ref"] == alr.P7_R54_AHR_POST_DMD08_ALR_OP02_STATUS_COMPLETE_CANDIDATE_REF
    assert material["complete_receipt_manual_decision_candidate"] is True
    assert material["actual_evidence_receipt_complete"] is True
    assert material["actual_evidence_receipt_count_complete"] is True
    assert material["actual_evidence_receipt_guard_complete"] is True
    assert all(value is True for value in material["receipt_count_pass_refs"].values())
    assert material["manual_decision_auto_executes_downstream"] is False
    assert material["p8_start_allowed"] is False
    assert material["release_allowed"] is False
    assert alr.assert_p7_r54_ahr_post_dmd08_alr_op02_existing_operation_material_inventory_contract(material) is True
    _assert_common_bodyfree_no_touch_no_promotion(material)


def test_alr_op02_inventory_body_payload_key_is_recorded_as_path_without_body_value() -> None:
    material = alr.build_p7_r54_ahr_post_dmd08_alr_op02_existing_operation_material_inventory(
        dmd_op08_result_memo_branch_intake=_op01_evidence_incomplete(),
        existing_local_only_review_session_material_bodyfree=_continuable_session(raw_input="body-value-must-not-survive"),
    )

    assert material["operation_material_inventory_status_ref"] == alr.P7_R54_AHR_POST_DMD08_ALR_OP02_STATUS_REPAIR_REQUIRED_REF
    assert material["operation_material_forbidden_payload_key_paths"] == ["operation_material[1].raw_input"]
    assert "body-value-must-not-survive" not in repr(material)
    assert alr.assert_p7_r54_ahr_post_dmd08_alr_op02_existing_operation_material_inventory_contract(material) is True
    _assert_common_bodyfree_no_touch_no_promotion(material)


def test_alr_op02_inventory_dmd_repair_branch_stays_repair_and_does_not_run_operation() -> None:
    material = alr.build_p7_r54_ahr_post_dmd08_alr_op02_existing_operation_material_inventory(
        dmd_op08_result_memo_branch_intake=_op01_repair(),
    )

    assert material["operation_material_inventory_status_ref"] == alr.P7_R54_AHR_POST_DMD08_ALR_OP02_STATUS_REPAIR_REQUIRED_REF
    assert material["repair_stop_candidate"] is True
    assert material["alr_op02_ready"] is False
    assert material["actual_human_review_run_here"] is False
    assert alr.assert_p7_r54_ahr_post_dmd08_alr_op02_existing_operation_material_inventory_contract(material) is True
    _assert_common_bodyfree_no_touch_no_promotion(material)


def test_alr_op03_scan_passes_clean_missing_inventory_to_op04_without_implementing_op04() -> None:
    op02 = alr.build_p7_r54_ahr_post_dmd08_alr_op02_existing_operation_material_inventory(
        dmd_op08_result_memo_branch_intake=_op01_evidence_incomplete(),
    )
    material = alr.build_p7_r54_ahr_post_dmd08_alr_op03_bodyfree_leak_invalid_source_promotion_scan(
        alr_op02_existing_operation_material_inventory=op02,
    )

    assert set(material) == set(alr.P7_R54_AHR_POST_DMD08_ALR_OP03_REQUIRED_FIELD_REFS)
    assert material["schema_version"] == alr.P7_R54_AHR_POST_DMD08_ALR_OP03_SCHEMA_VERSION
    assert material["bodyfree_scan_status_ref"] == alr.P7_R54_AHR_POST_DMD08_ALR_OP03_BODYFREE_SCAN_PASSED_REF
    assert material["promotion_claim_scan_status_ref"] == alr.P7_R54_AHR_POST_DMD08_ALR_OP03_PROMOTION_SCAN_PASSED_REF
    assert material["repair_stop_required"] is False
    assert material["alr_op03_ready_for_op04"] is True
    assert material["next_required_step"] == alr.P7_R54_AHR_POST_DMD08_ALR_OP04_STEP_REF
    assert "selected_action_ref" not in material
    assert alr.assert_p7_r54_ahr_post_dmd08_alr_op03_bodyfree_leak_invalid_source_promotion_scan_contract(material) is True
    _assert_common_bodyfree_no_touch_no_promotion(material)


def test_alr_op03_scan_carries_op02_bodyfree_repair_without_body_value() -> None:
    op02 = alr.build_p7_r54_ahr_post_dmd08_alr_op02_existing_operation_material_inventory(
        dmd_op08_result_memo_branch_intake=_op01_evidence_incomplete(),
        existing_local_only_review_session_material_bodyfree=_continuable_session(raw_input="body-value-must-not-survive"),
    )
    material = alr.build_p7_r54_ahr_post_dmd08_alr_op03_bodyfree_leak_invalid_source_promotion_scan(
        alr_op02_existing_operation_material_inventory=op02,
    )

    assert material["bodyfree_scan_status_ref"] == alr.P7_R54_AHR_POST_DMD08_ALR_OP03_BODYFREE_SCAN_REPAIR_REQUIRED_REF
    assert material["repair_stop_required"] is True
    assert material["forbidden_payload_key_paths"] == ["operation_material[1].raw_input"]
    assert "body-value-must-not-survive" not in repr(material)
    assert material["next_required_step"] == alr.P7_R54_AHR_POST_DMD08_ALR_NEXT_STEP_STOP_AND_REPAIR_BEFORE_OPERATION_REF
    assert alr.assert_p7_r54_ahr_post_dmd08_alr_op03_bodyfree_leak_invalid_source_promotion_scan_contract(material) is True
    _assert_common_bodyfree_no_touch_no_promotion(material)


def test_alr_op03_scan_detects_promotion_claim_from_operation_material() -> None:
    session = _continuable_session(p8_start_allowed=True)
    op02 = alr.build_p7_r54_ahr_post_dmd08_alr_op02_existing_operation_material_inventory(
        dmd_op08_result_memo_branch_intake=_op01_evidence_incomplete(),
        existing_local_only_review_session_material_bodyfree=session,
    )
    material = alr.build_p7_r54_ahr_post_dmd08_alr_op03_bodyfree_leak_invalid_source_promotion_scan(
        alr_op02_existing_operation_material_inventory=op02,
    )

    assert op02["operation_material_promotion_claim_paths"] == ["operation_material[1].p8_start_allowed"]
    assert material["promotion_claim_scan_status_ref"] == alr.P7_R54_AHR_POST_DMD08_ALR_OP03_PROMOTION_SCAN_REPAIR_REQUIRED_REF
    assert material["promotion_claim_paths"] == ["operation_material[1].p8_start_allowed"]
    assert "p8_start_allowed" in material["promotion_claim_refs"]
    assert material["repair_stop_required"] is True
    assert material["p8_start_allowed"] is False
    assert material["release_allowed"] is False
    assert alr.assert_p7_r54_ahr_post_dmd08_alr_op03_bodyfree_leak_invalid_source_promotion_scan_contract(material) is True
    _assert_common_bodyfree_no_touch_no_promotion(material)


def test_alr_op03_contract_rejects_promotion_pass_status_when_claim_paths_exist() -> None:
    session = _continuable_session(p8_start_allowed=True)
    op02 = alr.build_p7_r54_ahr_post_dmd08_alr_op02_existing_operation_material_inventory(
        dmd_op08_result_memo_branch_intake=_op01_evidence_incomplete(),
        existing_local_only_review_session_material_bodyfree=session,
    )
    material = alr.build_p7_r54_ahr_post_dmd08_alr_op03_bodyfree_leak_invalid_source_promotion_scan(
        alr_op02_existing_operation_material_inventory=op02,
    )
    material["promotion_claim_scan_status_ref"] = alr.P7_R54_AHR_POST_DMD08_ALR_OP03_PROMOTION_SCAN_PASSED_REF

    with pytest.raises(ValueError):
        alr.assert_p7_r54_ahr_post_dmd08_alr_op03_bodyfree_leak_invalid_source_promotion_scan_contract(material)


def test_alr_op02_op03_aliases_match_full_design_title_names() -> None:
    op01 = _op01_evidence_incomplete()
    op02 = alr.build_p7_r54_ahr_post_dmd08_continue_retry_actual_local_review_operation_alr_op02_existing_operation_material_inventory(
        dmd_op08_result_memo_branch_intake=op01,
    )
    op03 = alr.build_p7_r54_ahr_post_dmd08_continue_retry_actual_local_review_operation_alr_op03_bodyfree_leak_invalid_source_promotion_scan(
        alr_op02_existing_operation_material_inventory=op02,
    )

    assert alr.assert_p7_r54_ahr_post_dmd08_continue_retry_actual_local_review_operation_alr_op02_existing_operation_material_inventory_contract(op02) is True
    assert alr.assert_p7_r54_ahr_post_dmd08_continue_retry_actual_local_review_operation_alr_op03_bodyfree_leak_invalid_source_promotion_scan_contract(op03) is True


def test_alr_op02_op03_result_memo_exists_and_remains_bodyfree() -> None:
    result_path = TEST_DIR / "R54_AHR_PostDMD08_ContinueRetryActualLocalOnlyHumanReviewOperation_ALR_OP00_OP03_Result_20260703.md"
    text = result_path.read_text(encoding="utf-8")

    assert "ALR-OP02" in text
    assert "ALR-OP03" in text
    assert "actual_local_human_review_execution: false" in text
    assert "actual_body_full_packet_generation: false" in text
    assert "p8_start: false" in text
    assert "release_decision: false" in text
    assert "body-value-must-not-survive" not in text
