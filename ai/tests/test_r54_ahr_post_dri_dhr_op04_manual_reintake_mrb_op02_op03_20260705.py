# -*- coding: utf-8 -*-
"""R54-AHR Post-DRI / DHR-OP04 manual re-intake MRB-OP02/OP03 tests."""

from __future__ import annotations

from copy import deepcopy
from pathlib import Path
import sys

import pytest

TEST_DIR = Path(__file__).resolve().parent
if str(TEST_DIR) not in sys.path:
    sys.path.insert(0, str(TEST_DIR))

import emlis_ai_p7_r54_ahr_post_dri_dhr_op04_manual_reintake_20260705 as mrb
import emlis_ai_p7_r54_ahr_post_elr19_downstream_manual_decision_handoff_or_retry_20260704 as dhr
import emlis_ai_p7_r54_ahr_post_rsr16_dhr_actual_source_claim_reintake_20260705 as dri
from test_r54_ahr_post_alr12_explicit_local_only_review_start_retry_operation_elr_op16_op17_20260703 import (
    _op17_ready,
)
from test_r54_ahr_post_alr12_explicit_local_only_review_start_retry_operation_elr_op18_op19_20260703 import (
    _op17_waiting,
)
from test_r54_ahr_post_elr19_downstream_manual_decision_handoff_or_retry_dhr_op02_op03_20260704 import (
    _op02_accepted_intake,
)
from test_r54_ahr_post_rsr16_dhr_actual_source_claim_reintake_dri_op08_op09_20260705 import (
    _op09_ready,
)
from test_r54_ahr_post_rsr16_dhr_actual_source_claim_reintake_dri_op10_op11_20260705 import (
    _op09_waiting_for_final_scan,
    _op10_ready,
)
from test_r54_ahr_post_rsr16_dhr_actual_source_claim_reintake_dri_op12_result_20260705 import (
    _op12_closed,
)


def _assert_common_bodyfree_no_touch_no_promotion(material: dict[str, object]) -> None:
    assert material["source_mode"] == mrb.P7_R54_AHR_POST_DRI_MRB_SOURCE_MODE
    assert material["git_connection_required"] is False
    assert material["git_checked"] is False
    assert material["body_free"] is True
    assert all(value is False for value in material["public_contract"].values())
    assert all(value is False for value in material["mrb_no_touch_contract"].values())
    assert all(value is False for value in material["body_free_markers"].values())
    assert all(value is False for value in material["not_claimed_boundary"].values())
    for key in mrb.P7_R54_AHR_POST_DRI_MRB_REQUIRED_FALSE_FLAG_REFS:
        assert material[key] is False, key


def _mrb_op01_ready() -> dict[str, object]:
    material = mrb.build_p7_r54_ahr_post_dri_mrb_op01_dri_result_memo_op10_branch_intake(
        dri_op12_result_memo_closure=_op12_closed(),
        dri_op10_deterministic_branch_resolver=_op10_ready(),
    )
    assert material["mrb_op01_ready_for_mrb_op02"] is True
    assert mrb.assert_p7_r54_ahr_post_dri_mrb_op01_dri_result_memo_op10_branch_intake_contract(material) is True
    return material


def _mrb_op02_ready() -> dict[str, object]:
    material = mrb.build_p7_r54_ahr_post_dri_mrb_op02_dri_op09_adapter_candidate_extraction_and_scan(
        mrb_op01_dri_result_memo_op10_branch_intake=_mrb_op01_ready(),
        dri_op09_dhr_op04_external_actual_source_claim_adapter_candidate=_op09_ready(),
    )
    assert material["mrb_op02_ready_for_mrb_op03"] is True
    assert mrb.assert_p7_r54_ahr_post_dri_mrb_op02_dri_op09_adapter_candidate_extraction_and_scan_contract(material) is True
    return material


def _dhr_op03_ready() -> dict[str, object]:
    material = dhr.build_p7_r54_ahr_post_elr19_dhr_op03_elr_op17_dmd_compatible_receipt_candidate_extraction(
        elr_op18_downstream_manual_decision_hold_intake=_op02_accepted_intake(),
        elr_op17_dmd_compatible_receipt_candidate=_op17_ready(),
    )
    assert material["dhr_op03_ready_for_actual_source_claim_separation"] is True
    assert dhr.assert_p7_r54_ahr_post_elr19_dhr_op03_elr_op17_dmd_compatible_receipt_candidate_extraction_contract(material) is True
    return material


def _dhr_op03_waiting() -> dict[str, object]:
    material = dhr.build_p7_r54_ahr_post_elr19_dhr_op03_elr_op17_dmd_compatible_receipt_candidate_extraction(
        elr_op18_downstream_manual_decision_hold_intake=_op02_accepted_intake(),
        elr_op17_dmd_compatible_receipt_candidate=_op17_waiting(),
    )
    assert material["dhr_op03_waiting_for_complete_evidence"] is True
    assert dhr.assert_p7_r54_ahr_post_elr19_dhr_op03_elr_op17_dmd_compatible_receipt_candidate_extraction_contract(material) is True
    return material


def test_mrb_op02_extracts_dri_op09_candidate_bodyfree_without_dhr_op04_call() -> None:
    material = _mrb_op02_ready()
    candidate = material["external_actual_operation_evidence_claim_bodyfree_optional"]

    assert set(material) == set(mrb.P7_R54_AHR_POST_DRI_MRB_OP02_REQUIRED_FIELD_REFS)
    assert material["schema_version"] == mrb.P7_R54_AHR_POST_DRI_MRB_OP02_SCHEMA_VERSION
    assert material["operation_step_ref"] == mrb.P7_R54_AHR_POST_DRI_MRB_OP02_STEP_REF
    assert material["op01_contract_valid"] is True
    assert material["op01_ready_for_mrb_op02"] is True
    assert material["dri_op09_contract_valid"] is True
    assert material["dri_op09_status_ref"] == dri.P7_R54_AHR_POST_RSR16_DRI_OP09_STATUS_ADAPTER_CANDIDATE_MATERIALIZED_REF
    assert material["external_actual_operation_evidence_claim_bodyfree_optional_present"] is True
    assert material["external_actual_operation_evidence_claim_bodyfree_optional_key_refs"] == list(dri.P7_R54_AHR_POST_RSR16_DRI_OP09_DHR_OP04_READABLE_KEY_REFS)
    assert candidate["schema_version"] == dri.P7_R54_AHR_POST_RSR16_DRI_OP09_ADAPTER_SCHEMA_VERSION
    assert candidate["actual_source_claim_bodyfree"] is True
    assert material["adapter_candidate_key_set_valid"] is True
    assert material["adapter_candidate_source_kind_valid"] is True
    assert material["adapter_candidate_origin_valid"] is True
    assert material["adapter_candidate_required_true_flags_valid"] is True
    assert material["adapter_candidate_required_false_flags_valid"] is True
    assert material["adapter_candidate_row_counts_valid"] is True
    assert material["adapter_candidate_bodyfree_scan_clear"] is True
    assert material["adapter_candidate_promotion_scan_clear"] is True
    assert material["mrb_op02_status_ref"] == mrb.P7_R54_AHR_POST_DRI_MRB_OP02_STATUS_READY_FOR_OP03_REF
    assert material["mrb_op02_ready_for_mrb_op03"] is True
    assert material["mrb_op02_blocker_refs"] == []
    assert material["next_required_step"] == mrb.P7_R54_AHR_POST_DRI_MRB_OP03_STEP_REF
    assert material["mrb_op02_does_not_call_dhr_op04"] is True
    assert material["dhr_op04_called_here"] is False
    assert material["dhr_actual_source_claim_confirmed_here"] is False
    assert material["release_allowed"] is False
    _assert_common_bodyfree_no_touch_no_promotion(material)


def test_mrb_op02_requires_dhr_op04_readable_candidate_keys_before_op03() -> None:
    op09 = _op09_ready()
    candidate = dict(op09["external_actual_operation_evidence_claim_bodyfree_optional"])
    candidate.pop("rsr_op16_status_ref")
    op09["external_actual_operation_evidence_claim_bodyfree_optional"] = candidate
    op09["external_actual_operation_evidence_claim_bodyfree_optional_key_refs"] = list(candidate.keys())
    op09["external_actual_operation_evidence_claim_bodyfree_optional_key_ref_count"] = len(candidate)

    material = mrb.build_p7_r54_ahr_post_dri_mrb_op02_dri_op09_adapter_candidate_extraction_and_scan(
        mrb_op01_dri_result_memo_op10_branch_intake=_mrb_op01_ready(),
        dri_op09_dhr_op04_external_actual_source_claim_adapter_candidate=op09,
    )

    assert material["adapter_candidate_key_set_valid"] is False
    assert material["dri_op09_contract_valid"] is False
    assert material["mrb_op02_status_ref"] == mrb.P7_R54_AHR_POST_DRI_MRB_OP02_STATUS_REPAIR_DRI_OP09_REF
    assert material["mrb_op02_repair_required"] is True
    assert material["external_actual_operation_evidence_claim_bodyfree_optional"] == {}
    assert "dri_op09_adapter_candidate_contract_invalid" in material["mrb_op02_blocker_refs"]
    assert material["dhr_op04_called_here"] is False
    assert mrb.assert_p7_r54_ahr_post_dri_mrb_op02_dri_op09_adapter_candidate_extraction_and_scan_contract(material) is True
    _assert_common_bodyfree_no_touch_no_promotion(material)


@pytest.mark.parametrize(
    ("bad_key", "bad_value", "expected_field", "expected_blocker"),
    [
        ("raw_input", "do not copy raw body from DRI OP09", "adapter_candidate_forbidden_payload_key_path_refs", "dri_op09_candidate_forbidden_payload_key_detected"),
        ("question_text", "do not copy question text from DRI OP09", "adapter_candidate_forbidden_payload_key_path_refs", "dri_op09_candidate_forbidden_payload_key_detected"),
        ("local_path", "/mnt/do-not-copy-local-path", "adapter_candidate_forbidden_payload_key_path_refs", "dri_op09_candidate_forbidden_payload_key_detected"),
    ],
)
def test_mrb_op02_blocks_candidate_body_payload_keys_without_copying_values(bad_key: str, bad_value: str, expected_field: str, expected_blocker: str) -> None:
    op09 = _op09_ready()
    candidate = dict(op09["external_actual_operation_evidence_claim_bodyfree_optional"])
    candidate[bad_key] = bad_value
    op09["external_actual_operation_evidence_claim_bodyfree_optional"] = candidate
    op09["external_actual_operation_evidence_claim_bodyfree_optional_key_refs"] = list(candidate.keys())
    op09["external_actual_operation_evidence_claim_bodyfree_optional_key_ref_count"] = len(candidate)

    material = mrb.build_p7_r54_ahr_post_dri_mrb_op02_dri_op09_adapter_candidate_extraction_and_scan(
        mrb_op01_dri_result_memo_op10_branch_intake=_mrb_op01_ready(),
        dri_op09_dhr_op04_external_actual_source_claim_adapter_candidate=op09,
    )

    assert material["mrb_op02_status_ref"] == mrb.P7_R54_AHR_POST_DRI_MRB_OP02_STATUS_BLOCKED_BODYFREE_PROMOTION_AUTORUN_REF
    assert material["mrb_op02_bodyfree_leak_promotion_or_autorun_blocked"] is True
    assert material[expected_field]
    assert expected_blocker in material["mrb_op02_blocker_refs"]
    assert material["external_actual_operation_evidence_claim_bodyfree_optional"] == {}
    assert bad_value not in repr(material)
    assert material["dhr_op04_called_here"] is False
    assert material["p8_question_design_started"] is False
    assert mrb.assert_p7_r54_ahr_post_dri_mrb_op02_dri_op09_adapter_candidate_extraction_and_scan_contract(material) is True
    _assert_common_bodyfree_no_touch_no_promotion(material)


def test_mrb_op02_blocks_candidate_with_downstream_promotion_claim() -> None:
    op09 = _op09_ready()
    candidate = dict(op09["external_actual_operation_evidence_claim_bodyfree_optional"])
    candidate["dhr_op04_called_here"] = True
    op09["external_actual_operation_evidence_claim_bodyfree_optional"] = candidate

    material = mrb.build_p7_r54_ahr_post_dri_mrb_op02_dri_op09_adapter_candidate_extraction_and_scan(
        mrb_op01_dri_result_memo_op10_branch_intake=_mrb_op01_ready(),
        dri_op09_dhr_op04_external_actual_source_claim_adapter_candidate=op09,
    )

    assert material["mrb_op02_status_ref"] == mrb.P7_R54_AHR_POST_DRI_MRB_OP02_STATUS_BLOCKED_BODYFREE_PROMOTION_AUTORUN_REF
    assert "external_actual_operation_evidence_claim_bodyfree_optional.dhr_op04_called_here" in material["adapter_candidate_promotion_claim_refs"]
    assert "dri_op09_candidate_promotion_or_autorun_claim_detected" in material["mrb_op02_blocker_refs"]
    assert material["external_actual_operation_evidence_claim_bodyfree_optional"] == {}
    assert material["dhr_op04_called_here"] is False
    assert material["release_allowed"] is False
    assert mrb.assert_p7_r54_ahr_post_dri_mrb_op02_dri_op09_adapter_candidate_extraction_and_scan_contract(material) is True
    _assert_common_bodyfree_no_touch_no_promotion(material)


def test_mrb_op02_preserves_dri_candidate_not_dhr_confirmed_boundary() -> None:
    material = _mrb_op02_ready()

    assert material["dri_op09_candidate_is_only_dhr_op04_input_material"] is True
    assert material["dri_op09_candidate_is_not_dhr_op04_call"] is True
    assert material["dri_op09_candidate_is_not_dhr_actual_source_claim_confirmed"] is True
    assert material["dri_op09_candidate_is_not_dhr_reintake_execution"] is True
    assert material["dri_op09_candidate_is_not_dhr_op05_ready"] is True
    assert material["mrb_op02_does_not_intake_dhr_op03_material"] is True
    assert material["dhr_op04_called_here"] is False
    assert material["dhr_actual_source_claim_confirmed_here"] is False
    assert material["dhr_op05_called_here"] is False
    assert material["p8_start_allowed"] is False
    assert material["release_allowed"] is False


def test_mrb_op02_waits_when_dri_op09_candidate_is_waiting() -> None:
    material = mrb.build_p7_r54_ahr_post_dri_mrb_op02_dri_op09_adapter_candidate_extraction_and_scan(
        mrb_op01_dri_result_memo_op10_branch_intake=_mrb_op01_ready(),
        dri_op09_dhr_op04_external_actual_source_claim_adapter_candidate=_op09_waiting_for_final_scan(),
    )

    assert material["dri_op09_contract_valid"] is True
    assert material["dri_op09_status_ref"] == dri.P7_R54_AHR_POST_RSR16_DRI_OP09_STATUS_WAIT_FOR_FINAL_SCAN_CLEAR_REF
    assert material["mrb_op02_status_ref"] == mrb.P7_R54_AHR_POST_DRI_MRB_OP02_STATUS_WAITING_FOR_DRI_OP09_REF
    assert material["mrb_op02_waiting_for_dri_op09_candidate"] is True
    assert material["external_actual_operation_evidence_claim_bodyfree_optional_present"] is False
    assert material["external_actual_operation_evidence_claim_bodyfree_optional"] == {}
    assert "dri_op09_adapter_candidate_not_materialized" in material["mrb_op02_blocker_refs"]
    assert material["dhr_op04_called_here"] is False
    assert mrb.assert_p7_r54_ahr_post_dri_mrb_op02_dri_op09_adapter_candidate_extraction_and_scan_contract(material) is True
    _assert_common_bodyfree_no_touch_no_promotion(material)


def test_mrb_op03_accepts_dhr_op03_ready_material_without_dhr_op04_call() -> None:
    material = mrb.build_p7_r54_ahr_post_dri_mrb_op03_dhr_op03_ready_material_intake(
        mrb_op02_dri_op09_adapter_candidate_extraction_and_scan=_mrb_op02_ready(),
        dhr_op03_elr_op17_dmd_compatible_receipt_candidate_extraction=_dhr_op03_ready(),
    )

    assert set(material) == set(mrb.P7_R54_AHR_POST_DRI_MRB_OP03_REQUIRED_FIELD_REFS)
    assert material["schema_version"] == mrb.P7_R54_AHR_POST_DRI_MRB_OP03_SCHEMA_VERSION
    assert material["operation_step_ref"] == mrb.P7_R54_AHR_POST_DRI_MRB_OP03_STEP_REF
    assert material["op02_contract_valid"] is True
    assert material["op02_ready_for_mrb_op03"] is True
    assert material["dhr_op03_contract_valid"] is True
    assert material["dhr_op03_status_ref"] == dhr.P7_R54_AHR_POST_ELR19_DHR_OP03_STATUS_SHAPE_VALID_BODYFREE_REF
    assert material["dhr_op03_ready"] is True
    assert material["dhr_op03_ready_for_actual_source_claim_separation"] is True
    assert material["dhr_op03_receipt_shape_valid"] is True
    assert material["dhr_op03_receipt_source_kind_valid"] is True
    assert material["dhr_op03_receipt_count_fields_are_24"] is True
    assert material["dhr_op03_receipt_required_true_fields_passed"] is True
    assert material["dhr_op03_receipt_body_free"] is True
    assert material["dhr_op03_receipt_claimed_as_actual_execution_by_dhr_op03"] is False
    assert material["dhr_op03_actual_source_claim_confirmed_for_downstream_handoff"] is False
    assert material["mrb_op03_status_ref"] == mrb.P7_R54_AHR_POST_DRI_MRB_OP03_STATUS_READY_FOR_OP04_ENVELOPE_REF
    assert material["mrb_op03_ready_for_mrb_op04"] is True
    assert material["mrb_op03_blocker_refs"] == []
    assert material["next_required_step"] == mrb.P7_R54_AHR_POST_DRI_MRB_OP04_STEP_REF
    assert material["mrb_op03_does_not_build_dhr_op04_envelope"] is True
    assert material["mrb_op03_does_not_call_dhr_op04"] is True
    assert material["dhr_op04_called_here"] is False
    assert material["dhr_op05_called_here"] is False
    assert material["release_allowed"] is False
    assert mrb.assert_p7_r54_ahr_post_dri_mrb_op03_dhr_op03_ready_material_intake_contract(material) is True
    _assert_common_bodyfree_no_touch_no_promotion(material)


def test_mrb_op03_does_not_treat_op03_receipt_shape_as_actual_source_confirmation() -> None:
    material = mrb.build_p7_r54_ahr_post_dri_mrb_op03_dhr_op03_ready_material_intake(
        mrb_op02_dri_op09_adapter_candidate_extraction_and_scan=_mrb_op02_ready(),
        dhr_op03_elr_op17_dmd_compatible_receipt_candidate_extraction=_dhr_op03_ready(),
    )

    assert material["dhr_op03_receipt_shape_is_not_actual_source_claim_confirmation"] is True
    assert material["dhr_op03_ready_material_is_not_dhr_op04_call"] is True
    assert material["dhr_op03_ready_material_is_not_dhr_actual_source_claim_confirmed"] is True
    assert material["dhr_op03_ready_material_is_not_dhr_reintake_execution"] is True
    assert material["dhr_op03_ready_material_is_not_dhr_op05_ready"] is True
    assert material["dhr_op03_actual_source_claim_confirmed_for_downstream_handoff"] is False
    assert material["dhr_actual_source_claim_confirmed_here"] is False
    assert material["dhr_actual_source_claim_reintake_executed_here"] is False
    assert material["p8_start_allowed"] is False


def test_mrb_op03_waits_when_dhr_op03_is_waiting_for_complete_evidence() -> None:
    material = mrb.build_p7_r54_ahr_post_dri_mrb_op03_dhr_op03_ready_material_intake(
        mrb_op02_dri_op09_adapter_candidate_extraction_and_scan=_mrb_op02_ready(),
        dhr_op03_elr_op17_dmd_compatible_receipt_candidate_extraction=_dhr_op03_waiting(),
    )

    assert material["dhr_op03_contract_valid"] is True
    assert material["dhr_op03_waiting_for_complete_evidence"] is True
    assert material["mrb_op03_status_ref"] == mrb.P7_R54_AHR_POST_DRI_MRB_OP03_STATUS_WAITING_FOR_DHR_OP03_REF
    assert material["mrb_op03_waiting_for_dhr_op03_ready_material"] is True
    assert material["dhr_op03_ready_material_bodyfree"] == {}
    assert "dhr_op03_ready_material_waiting_for_complete_evidence" in material["mrb_op03_blocker_refs"]
    assert material["dhr_op04_called_here"] is False
    assert mrb.assert_p7_r54_ahr_post_dri_mrb_op03_dhr_op03_ready_material_intake_contract(material) is True
    _assert_common_bodyfree_no_touch_no_promotion(material)


def test_mrb_op03_repairs_when_dhr_op03_contract_is_invalid_without_body_leak() -> None:
    dhr_op03 = _dhr_op03_ready()
    dhr_op03["schema_version"] = "bad_dhr_op03_schema"

    material = mrb.build_p7_r54_ahr_post_dri_mrb_op03_dhr_op03_ready_material_intake(
        mrb_op02_dri_op09_adapter_candidate_extraction_and_scan=_mrb_op02_ready(),
        dhr_op03_elr_op17_dmd_compatible_receipt_candidate_extraction=dhr_op03,
    )

    assert material["dhr_op03_contract_valid"] is False
    assert material["mrb_op03_status_ref"] == mrb.P7_R54_AHR_POST_DRI_MRB_OP03_STATUS_REPAIR_DHR_OP03_REF
    assert material["mrb_op03_repair_required"] is True
    assert material["dhr_op03_ready_material_bodyfree"] == {}
    assert "dhr_op03_ready_material_contract_invalid" in material["mrb_op03_blocker_refs"]
    assert material["dhr_op04_called_here"] is False
    assert mrb.assert_p7_r54_ahr_post_dri_mrb_op03_dhr_op03_ready_material_intake_contract(material) is True
    _assert_common_bodyfree_no_touch_no_promotion(material)


def test_mrb_op03_blocks_dhr_op03_material_promotion_claim_without_copying_ready_material() -> None:
    dhr_op03 = deepcopy(_dhr_op03_ready())
    dhr_op03["actual_source_claim_confirmed_for_downstream_handoff"] = True

    material = mrb.build_p7_r54_ahr_post_dri_mrb_op03_dhr_op03_ready_material_intake(
        mrb_op02_dri_op09_adapter_candidate_extraction_and_scan=_mrb_op02_ready(),
        dhr_op03_elr_op17_dmd_compatible_receipt_candidate_extraction=dhr_op03,
    )

    assert material["mrb_op03_status_ref"] == mrb.P7_R54_AHR_POST_DRI_MRB_OP03_STATUS_BLOCKED_BODYFREE_PROMOTION_AUTORUN_REF
    assert material["mrb_op03_bodyfree_leak_promotion_or_autorun_blocked"] is True
    assert "dhr_op03_material.actual_source_claim_confirmed_for_downstream_handoff" in material["dhr_op03_material_promotion_claim_refs"]
    assert "dhr_op03_material_promotion_or_autorun_claim_detected" in material["mrb_op03_blocker_refs"]
    assert material["dhr_op03_ready_material_bodyfree"] == {}
    assert material["dhr_op03_actual_source_claim_confirmed_for_downstream_handoff"] is False
    assert material["dhr_actual_source_claim_confirmed_here"] is False
    assert material["dhr_op04_called_here"] is False
    assert material["release_allowed"] is False
    assert mrb.assert_p7_r54_ahr_post_dri_mrb_op03_dhr_op03_ready_material_intake_contract(material) is True


def test_mrb_op02_op03_full_title_aliases_match_canonical_builders() -> None:
    op01 = _mrb_op01_ready()
    op09 = _op09_ready()
    canonical_op02 = mrb.build_p7_r54_ahr_post_dri_mrb_op02_dri_op09_adapter_candidate_extraction_and_scan(
        mrb_op01_dri_result_memo_op10_branch_intake=op01,
        dri_op09_dhr_op04_external_actual_source_claim_adapter_candidate=op09,
    )
    alias_op02 = mrb.build_p7_r54_ahr_post_dri_dhr_op04_manual_reintake_mrb_op02_dri_op09_adapter_candidate_extraction_and_scan(
        mrb_op01_dri_result_memo_op10_branch_intake=op01,
        dri_op09_dhr_op04_external_actual_source_claim_adapter_candidate=op09,
    )
    dhr_op03 = _dhr_op03_ready()
    canonical_op03 = mrb.build_p7_r54_ahr_post_dri_mrb_op03_dhr_op03_ready_material_intake(
        mrb_op02_dri_op09_adapter_candidate_extraction_and_scan=canonical_op02,
        dhr_op03_elr_op17_dmd_compatible_receipt_candidate_extraction=dhr_op03,
    )
    alias_op03 = mrb.build_p7_r54_ahr_post_dri_dhr_op04_manual_reintake_mrb_op03_dhr_op03_ready_material_intake(
        mrb_op02_dri_op09_adapter_candidate_extraction_and_scan=canonical_op02,
        dhr_op03_elr_op17_dmd_compatible_receipt_candidate_extraction=dhr_op03,
    )

    assert canonical_op02 == alias_op02
    assert canonical_op03 == alias_op03
    assert mrb.assert_p7_r54_ahr_post_dri_dhr_op04_manual_reintake_mrb_op02_dri_op09_adapter_candidate_extraction_and_scan_contract(alias_op02) is True
    assert mrb.assert_p7_r54_ahr_post_dri_dhr_op04_manual_reintake_mrb_op03_dhr_op03_ready_material_intake_contract(alias_op03) is True
