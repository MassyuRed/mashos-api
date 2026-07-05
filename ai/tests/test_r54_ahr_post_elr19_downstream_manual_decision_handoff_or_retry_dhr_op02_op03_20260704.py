# -*- coding: utf-8 -*-
"""R54-AHR Post-ELR19 downstream manual decision handoff-or-retry DHR-OP02/OP03 tests."""

from __future__ import annotations

from pathlib import Path
import sys

import pytest

TEST_DIR = Path(__file__).resolve().parent
if str(TEST_DIR) not in sys.path:
    sys.path.insert(0, str(TEST_DIR))

import emlis_ai_p7_r54_ahr_post_alr12_explicit_local_only_review_start_retry_operation_20260703 as elr
import emlis_ai_p7_r54_ahr_post_dmh18_downstream_manual_decision_triage_20260703 as dmd
import emlis_ai_p7_r54_ahr_post_elr19_downstream_manual_decision_handoff_or_retry_20260704 as dhr
from test_r54_ahr_post_alr12_explicit_local_only_review_start_retry_operation_elr_op16_op17_20260703 import (
    _op17_ready,
)
from test_r54_ahr_post_alr12_explicit_local_only_review_start_retry_operation_elr_op18_op19_20260703 import (
    _op17_waiting,
    _op18_hold,
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


def _op01_closed_intake() -> dict[str, object]:
    material = dhr.build_p7_r54_ahr_post_elr19_dhr_op01_elr_op19_result_memo_validation_closure_intake(
        elr_op19_result_memo_validation_closure=_op19_closed(),
    )
    assert material["dhr_op01_ready_for_elr_op18_manual_hold_intake"] is True
    assert dhr.assert_p7_r54_ahr_post_elr19_dhr_op01_elr_op19_result_memo_validation_closure_intake_contract(material) is True
    return material


def _op02_accepted_intake() -> dict[str, object]:
    material = dhr.build_p7_r54_ahr_post_elr19_dhr_op02_elr_op18_downstream_manual_decision_hold_intake(
        elr_op19_result_memo_validation_closure_intake=_op01_closed_intake(),
        elr_op18_downstream_manual_decision_hold=_op18_hold(),
    )
    assert material["dhr_op02_status_ref"] == dhr.P7_R54_AHR_POST_ELR19_DHR_ELR_OP18_MANUAL_HOLD_ACCEPTED_BODYFREE_REF
    assert dhr.assert_p7_r54_ahr_post_elr19_dhr_op02_elr_op18_downstream_manual_decision_hold_intake_contract(material) is True
    return material


def test_dhr_op02_accepts_elr_op18_manual_hold_without_downstream_execution() -> None:
    material = _op02_accepted_intake()

    assert set(material) == set(dhr.P7_R54_AHR_POST_ELR19_DHR_OP02_REQUIRED_FIELD_REFS)
    assert material["schema_version"] == dhr.P7_R54_AHR_POST_ELR19_DHR_OP02_SCHEMA_VERSION
    assert material["op01_contract_valid"] is True
    assert material["op01_ready_for_elr_op18_manual_hold_intake"] is True
    assert material["elr_op18_manual_hold_present"] is True
    assert material["elr_op18_contract_valid"] is True
    assert material["elr_op18_downstream_manual_decision_hold_status_ref"] == elr.P7_R54_AHR_POST_ALR12_ELR_OP18_STATUS_HELD_BODYFREE_REF
    assert material["elr_op18_downstream_manual_decision_hold_ready"] is True
    assert material["elr_op18_downstream_manual_decision_required_without_auto_execution"] is True
    assert material["elr_op18_complete_candidate_held_without_downstream_execution"] is True
    assert material["elr_op18_manual_decision_auto_executes_downstream"] is False
    assert material["elr_op18_dmd_reexecution_started_here"] is False
    assert material["elr_op18_r52_actual_execution_started_here"] is False
    assert material["dhr_op02_ready_for_elr_op17_receipt_candidate_extraction"] is True
    assert material["dhr_op02_does_not_confirm_actual_source_claim"] is True
    assert material["dhr_op02_does_not_intake_elr_op17"] is True
    assert material["next_required_step"] == dhr.P7_R54_AHR_POST_ELR19_DHR_OP03_STEP_REF
    _assert_common_bodyfree_no_touch_no_promotion(material)


def test_dhr_op02_waits_when_elr_op18_waits_for_handoff_candidate() -> None:
    op18_waiting = elr.build_p7_r54_ahr_post_alr12_elr_op18_downstream_non_promotion_manual_decision_hold(
        op17_dmd_compatible_actual_operation_evidence_receipt_adapter_handoff_candidate=_op17_waiting(),
    )
    material = dhr.build_p7_r54_ahr_post_elr19_dhr_op02_elr_op18_downstream_manual_decision_hold_intake(
        elr_op19_result_memo_validation_closure_intake=_op01_closed_intake(),
        elr_op18_downstream_manual_decision_hold=op18_waiting,
    )

    assert material["dhr_op02_status_ref"] == dhr.P7_R54_AHR_POST_ELR19_DHR_ELR_OP18_MANUAL_HOLD_WAITING_FOR_HANDOFF_REF
    assert material["elr_op18_contract_valid"] is True
    assert material["elr_op18_downstream_manual_decision_hold_waiting_for_handoff"] is True
    assert material["dhr_op02_ready"] is False
    assert material["dhr_op02_waiting_for_elr_handoff_candidate"] is True
    assert material["dhr_op02_blocker_refs"] == []
    assert material["next_required_step"] == dhr.P7_R54_AHR_POST_ELR19_DHR_NEXT_STEP_WAIT_FOR_ELR_HANDOFF_CANDIDATE_REF
    assert dhr.assert_p7_r54_ahr_post_elr19_dhr_op02_elr_op18_downstream_manual_decision_hold_intake_contract(material) is True
    _assert_common_bodyfree_no_touch_no_promotion(material)


def test_dhr_op02_repairs_when_elr_op18_carries_promotion_claim() -> None:
    op18 = _op18_hold()
    op18["release_allowed"] = True
    material = dhr.build_p7_r54_ahr_post_elr19_dhr_op02_elr_op18_downstream_manual_decision_hold_intake(
        elr_op19_result_memo_validation_closure_intake=_op01_closed_intake(),
        elr_op18_downstream_manual_decision_hold=op18,
    )

    assert material["dhr_op02_status_ref"] == dhr.P7_R54_AHR_POST_ELR19_DHR_ELR_OP18_MANUAL_HOLD_REPAIR_REQUIRED_REF
    assert material["elr_op18_contract_valid"] is False
    assert material["elr_op18_promotion_claim_ref_count"] > 0
    assert "elr_op18_manual_hold_promotion_claim_detected" in material["dhr_op02_blocker_refs"]
    assert material["dhr_op02_repair_required"] is True
    assert material["next_required_step"] == dhr.P7_R54_AHR_POST_ELR19_DHR_NEXT_STEP_REPAIR_ELR_OP18_MANUAL_HOLD_REF
    assert dhr.assert_p7_r54_ahr_post_elr19_dhr_op02_elr_op18_downstream_manual_decision_hold_intake_contract(material) is True
    _assert_common_bodyfree_no_touch_no_promotion(material)


def test_dhr_op02_repairs_forbidden_elr_op18_payload_key_without_leaking_value() -> None:
    op18 = _op18_hold()
    op18["question_text"] = "must not leak from op18"
    material = dhr.build_p7_r54_ahr_post_elr19_dhr_op02_elr_op18_downstream_manual_decision_hold_intake(
        elr_op19_result_memo_validation_closure_intake=_op01_closed_intake(),
        elr_op18_downstream_manual_decision_hold=op18,
    )

    assert material["dhr_op02_status_ref"] == dhr.P7_R54_AHR_POST_ELR19_DHR_ELR_OP18_MANUAL_HOLD_REPAIR_REQUIRED_REF
    assert material["elr_op18_forbidden_payload_key_path_count"] > 0
    assert "elr_op18_manual_hold_forbidden_payload_key_detected" in material["dhr_op02_blocker_refs"]
    assert "must not leak from op18" not in repr(material)
    assert dhr.assert_p7_r54_ahr_post_elr19_dhr_op02_elr_op18_downstream_manual_decision_hold_intake_contract(material) is True


def test_dhr_op02_missing_elr_op18_material_stops_before_op03() -> None:
    material = dhr.build_p7_r54_ahr_post_elr19_dhr_op02_elr_op18_downstream_manual_decision_hold_intake(
        elr_op19_result_memo_validation_closure_intake=_op01_closed_intake(),
    )

    assert material["dhr_op02_status_ref"] == dhr.P7_R54_AHR_POST_ELR19_DHR_ELR_OP18_MANUAL_HOLD_MISSING_OR_INVALID_REF
    assert material["elr_op18_manual_hold_present"] is False
    assert material["elr_op18_contract_valid"] is False
    assert material["dhr_op02_repair_required"] is True
    assert material["next_required_step"] == dhr.P7_R54_AHR_POST_ELR19_DHR_NEXT_STEP_REPAIR_ELR_OP18_MANUAL_HOLD_REF
    assert dhr.assert_p7_r54_ahr_post_elr19_dhr_op02_elr_op18_downstream_manual_decision_hold_intake_contract(material) is True
    _assert_common_bodyfree_no_touch_no_promotion(material)


@pytest.mark.parametrize(
    ("field", "bad_value"),
    [
        ("elr_op18_manual_hold_intake_status_ref", dhr.P7_R54_AHR_POST_ELR19_DHR_ELR_OP18_MANUAL_HOLD_WAITING_FOR_HANDOFF_REF),
        ("dhr_op02_ready_for_elr_op17_receipt_candidate_extraction", False),
        ("elr_op18_dmd_reexecution_started_here", True),
        ("elr_op18_r52_actual_execution_started_here", True),
        ("p8_start_allowed", True),
        ("release_allowed", True),
        ("manual_decision_auto_executes_downstream", True),
        ("next_required_step", "P8_START"),
    ],
)
def test_dhr_op02_contract_rejects_manual_hold_or_promotion_mutations(field: str, bad_value: object) -> None:
    material = _op02_accepted_intake()
    material[field] = bad_value

    with pytest.raises(ValueError):
        dhr.assert_p7_r54_ahr_post_elr19_dhr_op02_elr_op18_downstream_manual_decision_hold_intake_contract(material)


def test_dhr_op03_extracts_elr_op17_receipt_candidate_shape_without_actual_source_confirmation() -> None:
    material = dhr.build_p7_r54_ahr_post_elr19_dhr_op03_elr_op17_dmd_compatible_receipt_candidate_extraction(
        elr_op18_downstream_manual_decision_hold_intake=_op02_accepted_intake(),
        elr_op17_dmd_compatible_receipt_candidate=_op17_ready(),
    )

    assert set(material) == set(dhr.P7_R54_AHR_POST_ELR19_DHR_OP03_REQUIRED_FIELD_REFS)
    assert material["schema_version"] == dhr.P7_R54_AHR_POST_ELR19_DHR_OP03_SCHEMA_VERSION
    assert material["dhr_op03_status_ref"] == dhr.P7_R54_AHR_POST_ELR19_DHR_ELR_OP17_RECEIPT_CANDIDATE_SHAPE_VALID_BODYFREE_REF
    assert material["op02_contract_valid"] is True
    assert material["op02_ready_for_elr_op17_receipt_candidate_extraction"] is True
    assert material["elr_op17_contract_valid"] is True
    assert material["receipt_shape_valid"] is True
    assert material["receipt_schema_version_matches_dmd"] is True
    assert material["receipt_schema_version"] == dmd.P7_R54_AHR_POST_DMH18_DMD_ACTUAL_OPERATION_EVIDENCE_RECEIPT_SCHEMA_VERSION
    assert material["receipt_source_kind_ref"] == dmd.P7_R54_AHR_POST_DMH18_DMD_ACTUAL_OPERATION_SOURCE_KIND_REF
    assert material["receipt_count_fields_are_24"] is True
    assert material["receipt_required_true_fields_passed"] is True
    assert material["receipt_body_free"] is True
    assert material["receipt_forbidden_payload_key_path_refs"] == []
    assert material["receipt_body_like_value_path_refs"] == []
    assert material["receipt_promotion_claim_refs"] == []
    assert material["receipt_claimed_as_actual_execution_by_dhr_op03"] is False
    assert material["actual_source_claim_confirmed_for_downstream_handoff"] is False
    assert material["dhr_op03_ready_for_actual_source_claim_separation"] is True
    assert material["next_required_step"] == dhr.P7_R54_AHR_POST_ELR19_DHR_OP04_STEP_REF
    receipt = material["dmd_compatible_actual_operation_evidence_receipt_bodyfree"]
    assert receipt["schema_version"] == dmd.P7_R54_AHR_POST_DMH18_DMD_ACTUAL_OPERATION_EVIDENCE_RECEIPT_SCHEMA_VERSION
    for count_field in dmd.P7_R54_AHR_POST_DMH18_DMD_RECEIPT_COUNT_FIELD_REFS:
        assert receipt[count_field] == dmd.P7_R54_AHR_POST_DMH18_DMD_REQUIRED_EVIDENCE_COUNT
    assert dhr.assert_p7_r54_ahr_post_elr19_dhr_op03_elr_op17_dmd_compatible_receipt_candidate_extraction_contract(material) is True
    _assert_common_bodyfree_no_touch_no_promotion(material)


def test_dhr_op03_waits_when_elr_op17_receipt_candidate_is_waiting() -> None:
    material = dhr.build_p7_r54_ahr_post_elr19_dhr_op03_elr_op17_dmd_compatible_receipt_candidate_extraction(
        elr_op18_downstream_manual_decision_hold_intake=_op02_accepted_intake(),
        elr_op17_dmd_compatible_receipt_candidate=_op17_waiting(),
    )

    assert material["dhr_op03_status_ref"] == dhr.P7_R54_AHR_POST_ELR19_DHR_ELR_OP17_RECEIPT_CANDIDATE_WAITING_FOR_COMPLETE_EVIDENCE_REF
    assert material["elr_op17_contract_valid"] is True
    assert material["dhr_op03_waiting_for_complete_evidence"] is True
    assert material["dmd_compatible_actual_operation_evidence_receipt_bodyfree"] == {}
    assert material["dhr_op03_blocker_refs"] == []
    assert material["next_required_step"] == dhr.P7_R54_AHR_POST_ELR19_DHR_NEXT_STEP_WAIT_FOR_ELR_OP17_RECEIPT_CANDIDATE_REF
    assert dhr.assert_p7_r54_ahr_post_elr19_dhr_op03_elr_op17_dmd_compatible_receipt_candidate_extraction_contract(material) is True
    _assert_common_bodyfree_no_touch_no_promotion(material)


def test_dhr_op03_repairs_invalid_receipt_source_kind_without_confirming_actual_source() -> None:
    op17 = _op17_ready()
    receipt = dict(op17["dmd_compatible_actual_operation_evidence_receipt_bodyfree"])
    receipt["source_kind_ref"] = "synthetic"
    op17["dmd_compatible_actual_operation_evidence_receipt_bodyfree"] = receipt
    material = dhr.build_p7_r54_ahr_post_elr19_dhr_op03_elr_op17_dmd_compatible_receipt_candidate_extraction(
        elr_op18_downstream_manual_decision_hold_intake=_op02_accepted_intake(),
        elr_op17_dmd_compatible_receipt_candidate=op17,
    )

    assert material["dhr_op03_status_ref"] == dhr.P7_R54_AHR_POST_ELR19_DHR_ELR_OP17_RECEIPT_CANDIDATE_REPAIR_REQUIRED_REF
    assert material["elr_op17_contract_valid"] is False
    assert material["receipt_source_kind_valid"] is False
    assert "elr_op17_receipt_source_kind_invalid" in material["dhr_op03_blocker_refs"]
    assert material["actual_source_claim_confirmed_for_downstream_handoff"] is False
    assert material["dmd_compatible_actual_operation_evidence_receipt_bodyfree"] == {}
    assert material["next_required_step"] == dhr.P7_R54_AHR_POST_ELR19_DHR_NEXT_STEP_REPAIR_ELR_OP17_RECEIPT_CANDIDATE_REF
    assert dhr.assert_p7_r54_ahr_post_elr19_dhr_op03_elr_op17_dmd_compatible_receipt_candidate_extraction_contract(material) is True
    _assert_common_bodyfree_no_touch_no_promotion(material)


def test_dhr_op03_repairs_forbidden_receipt_body_key_without_leaking_value() -> None:
    op17 = _op17_ready()
    receipt = dict(op17["dmd_compatible_actual_operation_evidence_receipt_bodyfree"])
    receipt["question_text"] = "must not leak from receipt"
    op17["dmd_compatible_actual_operation_evidence_receipt_bodyfree"] = receipt
    material = dhr.build_p7_r54_ahr_post_elr19_dhr_op03_elr_op17_dmd_compatible_receipt_candidate_extraction(
        elr_op18_downstream_manual_decision_hold_intake=_op02_accepted_intake(),
        elr_op17_dmd_compatible_receipt_candidate=op17,
    )

    assert material["dhr_op03_status_ref"] == dhr.P7_R54_AHR_POST_ELR19_DHR_ELR_OP17_RECEIPT_CANDIDATE_REPAIR_REQUIRED_REF
    assert material["receipt_forbidden_payload_key_path_count"] > 0
    assert "elr_op17_receipt_candidate_forbidden_payload_key_detected" in material["dhr_op03_blocker_refs"]
    assert material["dmd_compatible_actual_operation_evidence_receipt_bodyfree"] == {}
    assert "must not leak from receipt" not in repr(material)
    assert dhr.assert_p7_r54_ahr_post_elr19_dhr_op03_elr_op17_dmd_compatible_receipt_candidate_extraction_contract(material) is True


def test_dhr_op03_missing_elr_op17_material_stops_before_actual_source_separation() -> None:
    material = dhr.build_p7_r54_ahr_post_elr19_dhr_op03_elr_op17_dmd_compatible_receipt_candidate_extraction(
        elr_op18_downstream_manual_decision_hold_intake=_op02_accepted_intake(),
    )

    assert material["dhr_op03_status_ref"] == dhr.P7_R54_AHR_POST_ELR19_DHR_ELR_OP17_RECEIPT_CANDIDATE_MISSING_OR_INVALID_REF
    assert material["elr_op17_receipt_candidate_present"] is False
    assert material["elr_op17_contract_valid"] is False
    assert material["dhr_op03_repair_required"] is True
    assert material["actual_source_claim_confirmed_for_downstream_handoff"] is False
    assert material["next_required_step"] == dhr.P7_R54_AHR_POST_ELR19_DHR_NEXT_STEP_REPAIR_ELR_OP17_RECEIPT_CANDIDATE_REF
    assert dhr.assert_p7_r54_ahr_post_elr19_dhr_op03_elr_op17_dmd_compatible_receipt_candidate_extraction_contract(material) is True
    _assert_common_bodyfree_no_touch_no_promotion(material)


@pytest.mark.parametrize(
    ("field", "bad_value"),
    [
        ("receipt_claimed_as_actual_execution_by_dhr_op03", True),
        ("actual_source_claim_confirmed_for_downstream_handoff", True),
        ("dmd_execution_started_here", True),
        ("r52_actual_execution_started_here", True),
        ("p8_start_allowed", True),
        ("release_allowed", True),
        ("manual_decision_auto_executes_downstream", True),
        ("next_required_step", "DMD_EXECUTION_ALLOWED"),
    ],
)
def test_dhr_op03_contract_rejects_actual_source_or_promotion_mutations(field: str, bad_value: object) -> None:
    material = dhr.build_p7_r54_ahr_post_elr19_dhr_op03_elr_op17_dmd_compatible_receipt_candidate_extraction(
        elr_op18_downstream_manual_decision_hold_intake=_op02_accepted_intake(),
        elr_op17_dmd_compatible_receipt_candidate=_op17_ready(),
    )
    material[field] = bad_value

    with pytest.raises(ValueError):
        dhr.assert_p7_r54_ahr_post_elr19_dhr_op03_elr_op17_dmd_compatible_receipt_candidate_extraction_contract(material)


def test_dhr_op02_op03_full_title_aliases_match_canonical_builders() -> None:
    op01 = _op01_closed_intake()
    op18 = _op18_hold()
    op17 = _op17_ready()
    canonical_op02 = dhr.build_p7_r54_ahr_post_elr19_dhr_op02_elr_op18_downstream_manual_decision_hold_intake(
        elr_op19_result_memo_validation_closure_intake=op01,
        elr_op18_downstream_manual_decision_hold=op18,
    )
    alias_op02 = dhr.build_p7_r54_ahr_post_elr19_downstream_manual_decision_handoff_or_retry_dhr_op02_elr_op18_downstream_manual_decision_hold_intake(
        elr_op19_result_memo_validation_closure_intake=op01,
        elr_op18_downstream_manual_decision_hold=op18,
    )
    canonical_op03 = dhr.build_p7_r54_ahr_post_elr19_dhr_op03_elr_op17_dmd_compatible_receipt_candidate_extraction(
        elr_op18_downstream_manual_decision_hold_intake=canonical_op02,
        elr_op17_dmd_compatible_receipt_candidate=op17,
    )
    alias_op03 = dhr.build_p7_r54_ahr_post_elr19_downstream_manual_decision_handoff_or_retry_dhr_op03_elr_op17_dmd_compatible_receipt_candidate_extraction(
        elr_op18_downstream_manual_decision_hold_intake=canonical_op02,
        elr_op17_dmd_compatible_receipt_candidate=op17,
    )

    assert canonical_op02 == alias_op02
    assert canonical_op03 == alias_op03
    assert dhr.assert_p7_r54_ahr_post_elr19_downstream_manual_decision_handoff_or_retry_dhr_op02_elr_op18_downstream_manual_decision_hold_intake_contract(alias_op02) is True
    assert dhr.assert_p7_r54_ahr_post_elr19_downstream_manual_decision_handoff_or_retry_dhr_op03_elr_op17_dmd_compatible_receipt_candidate_extraction_contract(alias_op03) is True
