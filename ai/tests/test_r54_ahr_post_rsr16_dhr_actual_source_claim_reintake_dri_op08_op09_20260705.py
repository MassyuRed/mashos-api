# -*- coding: utf-8 -*-
"""R54-AHR Post-RSR16 DRI-OP08/OP09 final rescan and DHR-OP04 adapter candidate tests."""

from __future__ import annotations

from copy import deepcopy
from pathlib import Path
import sys

import pytest

TEST_DIR = Path(__file__).resolve().parent
if str(TEST_DIR) not in sys.path:
    sys.path.insert(0, str(TEST_DIR))

import emlis_ai_p7_r54_ahr_post_dhr09_actual_local_review_retry_start_decision_20260704 as rsr
import emlis_ai_p7_r54_ahr_post_rsr16_dhr_actual_source_claim_reintake_20260705 as dri
from test_r54_ahr_post_rsr16_dhr_actual_source_claim_reintake_dri_op02_op03_20260705 import (
    _op01_ready,
    _op02_aligned,
)
from test_r54_ahr_post_rsr16_dhr_actual_source_claim_reintake_dri_op04_op05_20260705 import (
    _assert_common_bodyfree_no_touch_no_promotion,
    _op03_ready,
    _op04_ready,
    _op05_ready,
)
from test_r54_ahr_post_rsr16_dhr_actual_source_claim_reintake_dri_op06_op07_20260705 import (
    _op06_ready,
    _op07_ready,
    _op12_accepted,
    _op13_accepted,
)


def _ready_chain() -> dict[str, dict[str, object]]:
    """Build one coherent OP01〜OP07 body-free ready chain for OP08/OP09 tests."""

    op01 = _op01_ready()
    op02 = _op02_aligned()
    op03 = _op03_ready()
    op04 = _op04_ready()
    op05 = _op05_ready(op04=op04)
    op12 = _op12_accepted()
    op06 = _op06_ready(op05=op05, op12=op12)
    op13 = _op13_accepted(op12=op12)
    op07 = _op07_ready(op06=op06, op13=op13)
    return {
        "op01": op01,
        "op02": op02,
        "op03": op03,
        "op04": op04,
        "op05": op05,
        "op06": op06,
        "op07": op07,
    }


def _op08_ready(chain: dict[str, dict[str, object]] | None = None) -> dict[str, object]:
    selected = chain or _ready_chain()
    material = dri.build_p7_r54_ahr_post_rsr16_dri_op08_final_bodyfree_no_promotion_source_kind_rescan(
        dri_op01_rsr_op16_result_memo_intake=selected["op01"],
        dri_op02_rsr_op15_branch_next_step_alignment=selected["op02"],
        dri_op03_complete_candidate_supplied_material_inventory=selected["op03"],
        dri_op04_actual_operation_receipt_revalidation=selected["op04"],
        dri_op05_sanitized_rows_rating_rows_revalidation=selected["op05"],
        dri_op06_question_need_rows_bridge_only_revalidation=selected["op06"],
        dri_op07_disposal_purge_receipt_revalidation=selected["op07"],
    )
    assert dri.assert_p7_r54_ahr_post_rsr16_dri_op08_final_bodyfree_no_promotion_source_kind_rescan_contract(material) is True
    return material


def _op08_waiting_for_op07(chain: dict[str, dict[str, object]] | None = None) -> dict[str, object]:
    selected = chain or _ready_chain()
    op07_wait = deepcopy(selected["op07"])
    op07_wait["dri_op07_status_ref"] = dri.P7_R54_AHR_POST_RSR16_DRI_OP07_STATUS_WAIT_FOR_PURGE_RECEIPT_REF
    op07_wait["disposal_purge_receipt_revalidation_status_ref"] = dri.P7_R54_AHR_POST_RSR16_DRI_OP07_STATUS_WAIT_FOR_PURGE_RECEIPT_REF
    op07_wait["dri_op07_disposal_purge_receipt_revalidated_bodyfree"] = False
    op07_wait["dri_op07_wait_for_disposal_purge_receipt"] = True
    op07_wait["dri_op07_ready_for_final_bodyfree_no_promotion_source_kind_rescan"] = False
    op07_wait["next_required_step"] = dri.P7_R54_AHR_POST_RSR16_DRI_NEXT_STEP_WAIT_FOR_PURGE_RECEIPT_REF
    material = dri.build_p7_r54_ahr_post_rsr16_dri_op08_final_bodyfree_no_promotion_source_kind_rescan(
        dri_op01_rsr_op16_result_memo_intake=selected["op01"],
        dri_op02_rsr_op15_branch_next_step_alignment=selected["op02"],
        dri_op03_complete_candidate_supplied_material_inventory=selected["op03"],
        dri_op04_actual_operation_receipt_revalidation=selected["op04"],
        dri_op05_sanitized_rows_rating_rows_revalidation=selected["op05"],
        dri_op06_question_need_rows_bridge_only_revalidation=selected["op06"],
        dri_op07_disposal_purge_receipt_revalidation=op07_wait,
    )
    assert dri.assert_p7_r54_ahr_post_rsr16_dri_op08_final_bodyfree_no_promotion_source_kind_rescan_contract(material) is True
    return material


def _op09_ready(chain: dict[str, dict[str, object]] | None = None, op08: dict[str, object] | None = None) -> dict[str, object]:
    selected = chain or _ready_chain()
    selected_op08 = op08 or _op08_ready(selected)
    material = dri.build_p7_r54_ahr_post_rsr16_dri_op09_dhr_op04_external_actual_source_claim_adapter_candidate(
        dri_op08_final_bodyfree_no_promotion_source_kind_rescan=selected_op08,
        dri_op04_actual_operation_receipt_revalidation=selected["op04"],
        dri_op05_sanitized_rows_rating_rows_revalidation=selected["op05"],
        dri_op06_question_need_rows_bridge_only_revalidation=selected["op06"],
        dri_op07_disposal_purge_receipt_revalidation=selected["op07"],
    )
    assert dri.assert_p7_r54_ahr_post_rsr16_dri_op09_dhr_op04_external_actual_source_claim_adapter_candidate_contract(material) is True
    return material


def test_dri_op08_final_scan_clear_bodyfree_without_adapter_or_downstream_execution() -> None:
    material = _op08_ready()

    assert set(material) == set(dri.P7_R54_AHR_POST_RSR16_DRI_OP08_REQUIRED_FIELD_REFS)
    assert material["schema_version"] == dri.P7_R54_AHR_POST_RSR16_DRI_OP08_SCHEMA_VERSION
    assert material["operation_step_ref"] == dri.P7_R54_AHR_POST_RSR16_DRI_OP08_STEP_REF
    assert material["op01_contract_valid"] is True
    assert material["op02_contract_valid"] is True
    assert material["op03_contract_valid"] is True
    assert material["op04_contract_valid"] is True
    assert material["op05_contract_valid"] is True
    assert material["op06_contract_valid"] is True
    assert material["op07_contract_valid"] is True
    assert material["op07_disposal_purge_receipt_revalidated_bodyfree"] is True
    assert material["final_scan_target_material_ref_count"] == 7
    assert material["final_scan_target_step_ref_count"] == 7
    assert material["final_scan_required_source_kind_ref"] == rsr.P7_R54_AHR_POST_DHR09_RSR_ACTUAL_REVIEW_SOURCE_KIND_REF
    assert material["final_scan_source_kind_ref_values"] == [rsr.P7_R54_AHR_POST_DHR09_RSR_ACTUAL_REVIEW_SOURCE_KIND_REF]
    assert material["final_scan_forbidden_payload_key_path_refs"] == []
    assert material["final_scan_body_like_value_path_refs"] == []
    assert material["final_scan_promotion_claim_refs"] == []
    assert material["final_scan_invalid_source_kind_refs"] == []
    assert material["final_scan_contract_or_readiness_blocker_refs"] == []
    assert material["dri_op08_status_ref"] == dri.P7_R54_AHR_POST_RSR16_DRI_OP08_STATUS_FINAL_SCAN_CLEAR_BODYFREE_REF
    assert material["final_bodyfree_no_promotion_source_kind_rescan_status_ref"] == material["dri_op08_status_ref"]
    assert material["dri_op08_final_scan_clear_bodyfree"] is True
    assert material["dri_op08_ready_for_dhr_op04_adapter_candidate_materialization"] is True
    assert material["dri_op08_blocker_refs"] == []
    assert material["dhr_op04_adapter_candidate_materialized_by_dri_op08"] is False
    assert material["dhr_op04_called_by_dri_op08"] is False
    assert material["dhr_actual_source_claim_reintake_executed_by_dri_op08"] is False
    assert material["actual_review_evidence_complete_here"] is False
    assert material["p8_question_design_started"] is False
    assert material["release_allowed"] is False
    assert material["next_required_step"] == dri.P7_R54_AHR_POST_RSR16_DRI_OP09_STEP_REF
    _assert_common_bodyfree_no_touch_no_promotion(material)


def test_dri_op08_waits_when_op07_ready_flag_is_not_clear_without_candidate_materialization() -> None:
    material = _op08_waiting_for_op07()

    assert material["op07_contract_valid"] is True
    assert material["op07_disposal_purge_receipt_revalidated_bodyfree"] is False
    assert material["op07_ready_for_final_bodyfree_no_promotion_source_kind_rescan"] is False
    assert material["dri_op08_status_ref"] == dri.P7_R54_AHR_POST_RSR16_DRI_OP08_STATUS_WAIT_FOR_OP07_READY_REF
    assert material["dri_op08_wait_for_op07_ready"] is True
    assert material["dri_op08_ready_for_dhr_op04_adapter_candidate_materialization"] is False
    assert "dri_op07_not_ready_for_final_rescan" in material["dri_op08_blocker_refs"]
    assert material["dhr_op04_adapter_candidate_materialized_by_dri_op08"] is False
    assert material["dhr_op04_called_here"] is False
    assert material["dhr_actual_source_claim_reintake_executed_here"] is False
    assert material["next_required_step"] == dri.P7_R54_AHR_POST_RSR16_DRI_NEXT_STEP_WAIT_FOR_OP07_READY_BEFORE_FINAL_SCAN_REF
    _assert_common_bodyfree_no_touch_no_promotion(material)


def test_dri_op08_waits_when_op07_material_is_missing_without_promoting_to_blocked() -> None:
    chain = _ready_chain()
    material = dri.build_p7_r54_ahr_post_rsr16_dri_op08_final_bodyfree_no_promotion_source_kind_rescan(
        dri_op01_rsr_op16_result_memo_intake=chain["op01"],
        dri_op02_rsr_op15_branch_next_step_alignment=chain["op02"],
        dri_op03_complete_candidate_supplied_material_inventory=chain["op03"],
        dri_op04_actual_operation_receipt_revalidation=chain["op04"],
        dri_op05_sanitized_rows_rating_rows_revalidation=chain["op05"],
        dri_op06_question_need_rows_bridge_only_revalidation=chain["op06"],
    )

    assert material["op07_contract_valid"] is False
    assert material["dri_op08_status_ref"] == dri.P7_R54_AHR_POST_RSR16_DRI_OP08_STATUS_WAIT_FOR_OP07_READY_REF
    assert material["dri_op08_wait_for_op07_ready"] is True
    assert "dri_op07_not_ready_for_final_rescan" in material["dri_op08_blocker_refs"]
    assert material["dri_op08_final_scan_body_leak_or_promotion_blocked"] is False
    assert material["dhr_op04_called_here"] is False
    assert material["release_allowed"] is False
    assert dri.assert_p7_r54_ahr_post_rsr16_dri_op08_final_bodyfree_no_promotion_source_kind_rescan_contract(material) is True
    _assert_common_bodyfree_no_touch_no_promotion(material)


def test_dri_op08_repairs_when_op07_contract_is_malformed_but_not_leaking() -> None:
    chain = _ready_chain()
    op07_bad = deepcopy(chain["op07"])
    op07_bad["schema_version"] = "wrong.schema"
    material = dri.build_p7_r54_ahr_post_rsr16_dri_op08_final_bodyfree_no_promotion_source_kind_rescan(
        dri_op01_rsr_op16_result_memo_intake=chain["op01"],
        dri_op02_rsr_op15_branch_next_step_alignment=chain["op02"],
        dri_op03_complete_candidate_supplied_material_inventory=chain["op03"],
        dri_op04_actual_operation_receipt_revalidation=chain["op04"],
        dri_op05_sanitized_rows_rating_rows_revalidation=chain["op05"],
        dri_op06_question_need_rows_bridge_only_revalidation=chain["op06"],
        dri_op07_disposal_purge_receipt_revalidation=op07_bad,
    )

    assert material["op07_contract_valid"] is False
    assert material["dri_op08_status_ref"] == dri.P7_R54_AHR_POST_RSR16_DRI_OP08_STATUS_FINAL_SCAN_REPAIR_REQUIRED_REF
    assert material["dri_op08_final_scan_repair_required"] is True
    assert "dri_op07_contract_invalid_or_missing" in material["dri_op08_blocker_refs"]
    assert material["dri_op08_final_scan_body_leak_or_promotion_blocked"] is False
    assert material["dhr_op04_called_here"] is False
    assert material["release_allowed"] is False
    assert dri.assert_p7_r54_ahr_post_rsr16_dri_op08_final_bodyfree_no_promotion_source_kind_rescan_contract(material) is True
    _assert_common_bodyfree_no_touch_no_promotion(material)


@pytest.mark.parametrize(
    ("additional_materials", "expected_blocker", "expected_path_field", "leaked_value"),
    [
        ({"leak": {"raw_input": "do not leak DRI OP08 raw body"}}, "dri_op08_forbidden_payload_key_detected", "final_scan_forbidden_payload_key_path_refs", "do not leak DRI OP08 raw body"),
        ({"promo": {"release_allowed": True}}, "dri_op08_promotion_claim_detected", "final_scan_promotion_claim_refs", None),
        ({"source": {"source_kind_ref": "unit_test_fixture"}}, "dri_op08_invalid_source_kind_detected", "final_scan_invalid_source_kind_refs", None),
    ],
)
def test_dri_op08_blocks_body_leak_promotion_or_invalid_source_kind_before_adapter(additional_materials, expected_blocker: str, expected_path_field: str, leaked_value: str | None) -> None:
    chain = _ready_chain()
    material = dri.build_p7_r54_ahr_post_rsr16_dri_op08_final_bodyfree_no_promotion_source_kind_rescan(
        dri_op01_rsr_op16_result_memo_intake=chain["op01"],
        dri_op02_rsr_op15_branch_next_step_alignment=chain["op02"],
        dri_op03_complete_candidate_supplied_material_inventory=chain["op03"],
        dri_op04_actual_operation_receipt_revalidation=chain["op04"],
        dri_op05_sanitized_rows_rating_rows_revalidation=chain["op05"],
        dri_op06_question_need_rows_bridge_only_revalidation=chain["op06"],
        dri_op07_disposal_purge_receipt_revalidation=chain["op07"],
        additional_bodyfree_materials=additional_materials,
    )

    assert material["dri_op08_status_ref"] == dri.P7_R54_AHR_POST_RSR16_DRI_OP08_STATUS_FINAL_SCAN_BODY_LEAK_OR_PROMOTION_BLOCKED_REF
    assert material["dri_op08_final_scan_body_leak_or_promotion_blocked"] is True
    assert expected_blocker in material["dri_op08_blocker_refs"]
    assert material[expected_path_field]
    assert material["dri_op08_ready_for_dhr_op04_adapter_candidate_materialization"] is False
    assert material["dhr_op04_adapter_candidate_materialized_by_dri_op08"] is False
    assert material["dhr_op04_called_here"] is False
    assert material["p8_question_design_started"] is False
    if leaked_value is not None:
        assert leaked_value not in repr(material)
    assert dri.assert_p7_r54_ahr_post_rsr16_dri_op08_final_bodyfree_no_promotion_source_kind_rescan_contract(material) is True
    _assert_common_bodyfree_no_touch_no_promotion(material)


@pytest.mark.parametrize(
    ("field", "bad_value"),
    [
        ("schema_version", "wrong.schema"),
        ("dri_op08_status_ref", dri.P7_R54_AHR_POST_RSR16_DRI_OP08_STATUS_WAIT_FOR_OP07_READY_REF),
        ("next_required_step", dri.P7_R54_AHR_POST_RSR16_DRI_NEXT_STEP_PROVIDE_ADAPTER_TO_DHR_OP04_MANUALLY_REF),
        ("dhr_op04_adapter_candidate_materialized_by_dri_op08", True),
        ("dhr_op04_called_by_dri_op08", True),
        ("dhr_actual_source_claim_reintake_executed_by_dri_op08", True),
        ("p8_question_design_started", True),
        ("release_allowed", True),
        ("body_free", False),
    ],
)
def test_dri_op08_contract_rejects_boundary_or_status_mutations(field: str, bad_value: object) -> None:
    material = _op08_ready()
    material[field] = bad_value

    with pytest.raises(ValueError):
        dri.assert_p7_r54_ahr_post_rsr16_dri_op08_final_bodyfree_no_promotion_source_kind_rescan_contract(material)


def test_dri_op08_full_title_aliases_match_short_builder_and_assert_contract() -> None:
    chain = _ready_chain()
    material = dri.build_p7_r54_ahr_post_rsr16_dhr_actual_source_claim_reintake_dri_op08_final_bodyfree_no_promotion_source_kind_rescan(
        dri_op01_rsr_op16_result_memo_intake=chain["op01"],
        dri_op02_rsr_op15_branch_next_step_alignment=chain["op02"],
        dri_op03_complete_candidate_supplied_material_inventory=chain["op03"],
        dri_op04_actual_operation_receipt_revalidation=chain["op04"],
        dri_op05_sanitized_rows_rating_rows_revalidation=chain["op05"],
        dri_op06_question_need_rows_bridge_only_revalidation=chain["op06"],
        dri_op07_disposal_purge_receipt_revalidation=chain["op07"],
    )

    assert material["dri_op08_final_scan_clear_bodyfree"] is True
    assert dri.assert_p7_r54_ahr_post_rsr16_dhr_actual_source_claim_reintake_dri_op08_final_bodyfree_no_promotion_source_kind_rescan_contract(material) is True


def test_dri_op09_materializes_bodyfree_dhr_op04_adapter_candidate_without_calling_dhr_or_confirming_claim() -> None:
    chain = _ready_chain()
    op08 = _op08_ready(chain)
    material = _op09_ready(chain, op08)
    candidate = material["external_actual_operation_evidence_claim_bodyfree_optional"]

    assert set(material) == set(dri.P7_R54_AHR_POST_RSR16_DRI_OP09_REQUIRED_FIELD_REFS)
    assert material["schema_version"] == dri.P7_R54_AHR_POST_RSR16_DRI_OP09_SCHEMA_VERSION
    assert material["operation_step_ref"] == dri.P7_R54_AHR_POST_RSR16_DRI_OP09_STEP_REF
    assert material["op08_contract_valid"] is True
    assert material["op08_final_scan_clear_bodyfree"] is True
    assert material["op08_ready_for_dhr_op04_adapter_candidate_materialization"] is True
    assert material["op04_contract_valid"] is True
    assert material["op05_contract_valid"] is True
    assert material["op06_contract_valid"] is True
    assert material["op07_contract_valid"] is True
    assert material["dri_op09_status_ref"] == dri.P7_R54_AHR_POST_RSR16_DRI_OP09_STATUS_ADAPTER_CANDIDATE_MATERIALIZED_REF
    assert material["dhr_op04_external_actual_source_claim_adapter_candidate_status_ref"] == material["dri_op09_status_ref"]
    assert material["adapter_candidate_materialized"] is True
    assert material["adapter_candidate_materialized_bodyfree"] is True
    assert material["adapter_candidate_for_manual_dhr_op04_input_only"] is True
    assert material["adapter_candidate_not_dhr_confirmed"] is True
    assert material["adapter_candidate_does_not_call_dhr_op04"] is True
    assert material["adapter_candidate_does_not_execute_dhr_reintake"] is True
    assert material["adapter_candidate_downstream_auto_execution_allowed"] is False
    assert material["external_actual_operation_evidence_claim_bodyfree_optional_present"] is True
    assert candidate["schema_version"] == dri.P7_R54_AHR_POST_RSR16_DRI_OP09_ADAPTER_SCHEMA_VERSION
    assert candidate["material_kind"] == dri.P7_R54_AHR_POST_RSR16_DRI_OP09_ADAPTER_MATERIAL_KIND
    assert candidate["source_kind_ref"] == rsr.P7_R54_AHR_POST_DHR09_RSR_ACTUAL_REVIEW_SOURCE_KIND_REF
    assert candidate["actual_source_claim_source_kind_ref"] == rsr.P7_R54_AHR_POST_DHR09_RSR_ACTUAL_REVIEW_SOURCE_KIND_REF
    assert candidate["actual_source_claim_bodyfree"] is True
    assert candidate["actual_local_only_human_review_by_person_confirmed"] is True
    assert candidate["actual_human_review_executed_by_person"] is True
    assert candidate["sanitized_review_result_row_count"] == rsr.P7_R54_AHR_POST_DHR09_RSR_EXPECTED_CASE_COUNT
    assert candidate["rating_row_count"] == rsr.P7_R54_AHR_POST_DHR09_RSR_EXPECTED_CASE_COUNT
    assert candidate["question_need_observation_row_count"] == rsr.P7_R54_AHR_POST_DHR09_RSR_EXPECTED_CASE_COUNT
    assert candidate["dhr_op04_called_here"] is False
    assert candidate["dhr_actual_source_claim_reintake_executed_here"] is False
    assert candidate["p8_question_design_started"] is False
    assert candidate["release_allowed"] is False
    assert tuple(candidate.keys()) == tuple(dri.P7_R54_AHR_POST_RSR16_DRI_OP09_DHR_OP04_READABLE_KEY_REFS)
    assert material["external_actual_operation_evidence_claim_bodyfree_optional_key_refs"] == list(dri.P7_R54_AHR_POST_RSR16_DRI_OP09_DHR_OP04_READABLE_KEY_REFS)
    assert material["adapter_candidate_forbidden_payload_key_path_refs"] == []
    assert material["adapter_candidate_body_like_value_path_refs"] == []
    assert material["adapter_candidate_promotion_claim_refs"] == []
    assert material["adapter_candidate_invalid_source_kind_refs"] == []
    assert material["dhr_op04_called_by_dri_op09"] is False
    assert material["dhr_actual_source_claim_confirmed_by_dri_op09"] is False
    assert material["dhr_actual_source_claim_reintake_executed_by_dri_op09"] is False
    assert material["dhr_op04_called_here"] is False
    assert material["dhr_actual_source_claim_reintake_executed_here"] is False
    assert material["p8_question_design_started"] is False
    assert material["release_allowed"] is False
    assert material["next_required_step"] == dri.P7_R54_AHR_POST_RSR16_DRI_NEXT_STEP_PROVIDE_ADAPTER_TO_DHR_OP04_MANUALLY_REF
    _assert_common_bodyfree_no_touch_no_promotion(material)


def test_dri_op09_waits_when_op08_final_scan_is_valid_but_not_clear_and_does_not_materialize_candidate() -> None:
    chain = _ready_chain()
    op08_wait = _op08_waiting_for_op07(chain)
    material = dri.build_p7_r54_ahr_post_rsr16_dri_op09_dhr_op04_external_actual_source_claim_adapter_candidate(
        dri_op08_final_bodyfree_no_promotion_source_kind_rescan=op08_wait,
        dri_op04_actual_operation_receipt_revalidation=chain["op04"],
        dri_op05_sanitized_rows_rating_rows_revalidation=chain["op05"],
        dri_op06_question_need_rows_bridge_only_revalidation=chain["op06"],
        dri_op07_disposal_purge_receipt_revalidation=chain["op07"],
    )

    assert material["op08_contract_valid"] is True
    assert material["op08_status_ref"] == dri.P7_R54_AHR_POST_RSR16_DRI_OP08_STATUS_WAIT_FOR_OP07_READY_REF
    assert material["op08_final_scan_clear_bodyfree"] is False
    assert material["dri_op09_status_ref"] == dri.P7_R54_AHR_POST_RSR16_DRI_OP09_STATUS_WAIT_FOR_FINAL_SCAN_CLEAR_REF
    assert material["dri_op09_wait_for_final_scan_clear"] is True
    assert material["external_actual_operation_evidence_claim_bodyfree_optional_present"] is False
    assert material["external_actual_operation_evidence_claim_bodyfree_optional"] == {}
    assert material["adapter_candidate_materialized"] is False
    assert material["dhr_op04_called_here"] is False
    assert material["dhr_actual_source_claim_reintake_executed_here"] is False
    assert material["next_required_step"] == dri.P7_R54_AHR_POST_RSR16_DRI_NEXT_STEP_WAIT_FOR_OP08_FINAL_SCAN_REF
    assert dri.assert_p7_r54_ahr_post_rsr16_dri_op09_dhr_op04_external_actual_source_claim_adapter_candidate_contract(material) is True
    _assert_common_bodyfree_no_touch_no_promotion(material)


def test_dri_op09_repairs_when_required_source_material_is_not_revalidated() -> None:
    chain = _ready_chain()
    op08 = _op08_ready(chain)
    op04_not_ready = deepcopy(chain["op04"])
    op04_not_ready["dri_op04_revalidated_bodyfree"] = False
    material = dri.build_p7_r54_ahr_post_rsr16_dri_op09_dhr_op04_external_actual_source_claim_adapter_candidate(
        dri_op08_final_bodyfree_no_promotion_source_kind_rescan=op08,
        dri_op04_actual_operation_receipt_revalidation=op04_not_ready,
        dri_op05_sanitized_rows_rating_rows_revalidation=chain["op05"],
        dri_op06_question_need_rows_bridge_only_revalidation=chain["op06"],
        dri_op07_disposal_purge_receipt_revalidation=chain["op07"],
    )

    assert material["op08_contract_valid"] is True
    assert material["op04_contract_valid"] is False
    assert material["dri_op09_status_ref"] == dri.P7_R54_AHR_POST_RSR16_DRI_OP09_STATUS_REPAIR_FINAL_SCAN_OR_MATERIAL_REF
    assert material["dri_op09_repair_required"] is True
    assert "op08_or_source_material_contract_invalid" in material["dri_op09_blocker_refs"]
    assert material["external_actual_operation_evidence_claim_bodyfree_optional_present"] is False
    assert material["dhr_op04_called_here"] is False
    assert material["release_allowed"] is False
    assert dri.assert_p7_r54_ahr_post_rsr16_dri_op09_dhr_op04_external_actual_source_claim_adapter_candidate_contract(material) is True
    _assert_common_bodyfree_no_touch_no_promotion(material)


def test_dri_op09_blocks_when_op08_final_scan_is_blocked_before_adapter_materialization() -> None:
    chain = _ready_chain()
    op08_blocked = dri.build_p7_r54_ahr_post_rsr16_dri_op08_final_bodyfree_no_promotion_source_kind_rescan(
        dri_op01_rsr_op16_result_memo_intake=chain["op01"],
        dri_op02_rsr_op15_branch_next_step_alignment=chain["op02"],
        dri_op03_complete_candidate_supplied_material_inventory=chain["op03"],
        dri_op04_actual_operation_receipt_revalidation=chain["op04"],
        dri_op05_sanitized_rows_rating_rows_revalidation=chain["op05"],
        dri_op06_question_need_rows_bridge_only_revalidation=chain["op06"],
        dri_op07_disposal_purge_receipt_revalidation=chain["op07"],
        additional_bodyfree_materials={"leak": {"question_text": "do not leak DRI OP09 question text"}},
    )
    assert op08_blocked["dri_op08_final_scan_body_leak_or_promotion_blocked"] is True

    material = dri.build_p7_r54_ahr_post_rsr16_dri_op09_dhr_op04_external_actual_source_claim_adapter_candidate(
        dri_op08_final_bodyfree_no_promotion_source_kind_rescan=op08_blocked,
        dri_op04_actual_operation_receipt_revalidation=chain["op04"],
        dri_op05_sanitized_rows_rating_rows_revalidation=chain["op05"],
        dri_op06_question_need_rows_bridge_only_revalidation=chain["op06"],
        dri_op07_disposal_purge_receipt_revalidation=chain["op07"],
    )

    assert material["dri_op09_status_ref"] == dri.P7_R54_AHR_POST_RSR16_DRI_OP09_STATUS_BLOCKED_FINAL_SCAN_REF
    assert material["dri_op09_blocked_before_adapter_candidate"] is True
    assert "dri_op08_final_scan_blocked" in material["dri_op09_blocker_refs"]
    assert material["external_actual_operation_evidence_claim_bodyfree_optional_present"] is False
    assert material["adapter_candidate_materialized"] is False
    assert material["dhr_op04_called_here"] is False
    assert material["p8_question_design_started"] is False
    assert "do not leak DRI OP09 question text" not in repr(material)
    assert dri.assert_p7_r54_ahr_post_rsr16_dri_op09_dhr_op04_external_actual_source_claim_adapter_candidate_contract(material) is True
    _assert_common_bodyfree_no_touch_no_promotion(material)


@pytest.mark.parametrize(
    ("field", "bad_value"),
    [
        ("schema_version", "wrong.schema"),
        ("dri_op09_status_ref", dri.P7_R54_AHR_POST_RSR16_DRI_OP09_STATUS_WAIT_FOR_FINAL_SCAN_CLEAR_REF),
        ("next_required_step", dri.P7_R54_AHR_POST_RSR16_DRI_OP12_STEP_REF),
        ("adapter_candidate_downstream_auto_execution_allowed", True),
        ("dhr_actual_source_claim_confirmed_by_dri_op09", True),
        ("dhr_op04_called_by_dri_op09", True),
        ("dhr_actual_source_claim_reintake_executed_by_dri_op09", True),
        ("p8_question_design_started", True),
        ("release_allowed", True),
        ("body_free", False),
    ],
)
def test_dri_op09_contract_rejects_downstream_confirmation_or_boundary_mutations(field: str, bad_value: object) -> None:
    material = _op09_ready()
    material[field] = bad_value

    with pytest.raises(ValueError):
        dri.assert_p7_r54_ahr_post_rsr16_dri_op09_dhr_op04_external_actual_source_claim_adapter_candidate_contract(material)


def test_dri_op09_contract_rejects_candidate_that_claims_dhr_call_or_release() -> None:
    material = _op09_ready()
    candidate = dict(material["external_actual_operation_evidence_claim_bodyfree_optional"])
    candidate["dhr_op04_called_here"] = True
    material["external_actual_operation_evidence_claim_bodyfree_optional"] = candidate
    material["external_actual_operation_evidence_claim_bodyfree_optional_key_refs"] = list(candidate.keys())
    material["external_actual_operation_evidence_claim_bodyfree_optional_key_ref_count"] = len(candidate)

    with pytest.raises(ValueError):
        dri.assert_p7_r54_ahr_post_rsr16_dri_op09_dhr_op04_external_actual_source_claim_adapter_candidate_contract(material)


def test_dri_op09_full_title_aliases_match_short_builder_and_assert_contract() -> None:
    chain = _ready_chain()
    op08 = _op08_ready(chain)
    material = dri.build_p7_r54_ahr_post_rsr16_dhr_actual_source_claim_reintake_dri_op09_dhr_op04_external_actual_source_claim_adapter_candidate(
        dri_op08_final_bodyfree_no_promotion_source_kind_rescan=op08,
        dri_op04_actual_operation_receipt_revalidation=chain["op04"],
        dri_op05_sanitized_rows_rating_rows_revalidation=chain["op05"],
        dri_op06_question_need_rows_bridge_only_revalidation=chain["op06"],
        dri_op07_disposal_purge_receipt_revalidation=chain["op07"],
    )

    assert material["dri_op09_adapter_candidate_materialized_bodyfree"] is True
    assert dri.assert_p7_r54_ahr_post_rsr16_dhr_actual_source_claim_reintake_dri_op09_dhr_op04_external_actual_source_claim_adapter_candidate_contract(material) is True
