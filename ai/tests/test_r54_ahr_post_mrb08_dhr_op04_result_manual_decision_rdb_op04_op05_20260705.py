# -*- coding: utf-8 -*-
"""R54-AHR Post-MRB08 / DHR-OP04 result manual decision RDB-OP04/OP05 tests."""

from __future__ import annotations

from pathlib import Path
import sys

import pytest

TEST_DIR = Path(__file__).resolve().parent
if str(TEST_DIR) not in sys.path:
    sys.path.insert(0, str(TEST_DIR))

import emlis_ai_p7_r54_ahr_post_mrb08_dhr_op04_result_manual_decision_20260705 as rdb
import emlis_ai_p7_r54_ahr_post_dri_dhr_op04_manual_reintake_20260705 as mrb
import emlis_ai_p7_r54_ahr_post_elr19_downstream_manual_decision_handoff_or_retry_20260704 as dhr
from test_r54_ahr_post_dri_dhr_op04_manual_reintake_mrb_op06_op07_20260705 import (
    _op05_confirmed,
    _op05_invalid_result,
    _op05_not_confirmed,
    _op05_waiting_result,
)
from test_r54_ahr_post_dri_dhr_op04_manual_reintake_mrb_op08_result_20260705 import _op08_from_op05


def _assert_common_bodyfree_no_touch_no_promotion(material: dict[str, object]) -> None:
    assert material["source_mode"] == rdb.P7_R54_AHR_POST_MRB08_RDB_SOURCE_MODE
    assert material["git_connection_required"] is False
    assert material["git_checked"] is False
    assert material["body_free"] is True
    assert all(value is False for value in material["public_contract"].values())
    assert all(value is False for value in material["rdb_no_touch_contract"].values())
    assert all(value is False for value in material["body_free_markers"].values())
    assert all(value is False for value in material["not_claimed_boundary"].values())
    for key in rdb.P7_R54_AHR_POST_MRB08_RDB_REQUIRED_FALSE_FLAG_REFS:
        assert material[key] is False, key


def _op01_from_op05(op05: dict[str, object]) -> dict[str, object]:
    return rdb.build_p7_r54_ahr_post_mrb08_rdb_op01_mrb_op08_result_memo_closure_intake(
        mrb_op08_result_memo_closure=_op08_from_op05(op05),
    )


def _op02_from_op05(op05: dict[str, object]) -> dict[str, object]:
    return rdb.build_p7_r54_ahr_post_mrb08_rdb_op02_mrb_selected_branch_dhr_op04_result_status_consistency_check(
        mrb_op08_result_memo_closure_intake=_op01_from_op05(op05),
    )


def _op03_from_op05(op05: dict[str, object]) -> dict[str, object]:
    return rdb.build_p7_r54_ahr_post_mrb08_rdb_op03_dhr_op04_result_manual_decision_lane_resolver(
        mrb_branch_dhr_status_consistency_check=_op02_from_op05(op05),
    )


def _op04_from_op05(op05: dict[str, object]) -> dict[str, object]:
    return rdb.build_p7_r54_ahr_post_mrb08_rdb_op04_branch_specific_manual_decision_materialization(
        dhr_op04_result_manual_decision_lane_resolver=_op03_from_op05(op05),
    )


def _op05_from_op05(op05: dict[str, object]) -> dict[str, object]:
    return rdb.build_p7_r54_ahr_post_mrb08_rdb_op05_next_stage_candidate_envelope_without_execution(
        branch_specific_manual_decision_materialization=_op04_from_op05(op05),
    )


@pytest.mark.parametrize(
    ("op05", "expected_status", "expected_material_ref", "expected_candidate_ref", "expected_candidate_kind", "candidate_key"),
    [
        (
            _op05_confirmed(),
            rdb.P7_R54_AHR_POST_MRB08_RDB_STATUS_CONFIRMED_DHR_OP05_MANUAL_HANDOFF_CANDIDATE_STOPPED_REF,
            rdb.P7_R54_AHR_POST_MRB08_RDB_OP04_MATERIAL_CONFIRMED_REF,
            rdb.P7_R54_AHR_POST_MRB08_RDB_NEXT_STEP_PREPARE_DHR_OP05_MANUAL_HANDOFF_DECISION_REF,
            rdb.P7_R54_AHR_POST_MRB08_RDB_CANDIDATE_KIND_DHR_OP05_HANDOFF_REF,
            "dhr_op05_manual_handoff_candidate_present",
        ),
        (
            _op05_not_confirmed(),
            rdb.P7_R54_AHR_POST_MRB08_RDB_STATUS_NOT_CONFIRMED_RETRY_OR_START_DECISION_REQUIRED_STOPPED_REF,
            rdb.P7_R54_AHR_POST_MRB08_RDB_OP04_MATERIAL_RETRY_OR_START_REF,
            rdb.P7_R54_AHR_POST_MRB08_RDB_NEXT_STEP_PREPARE_RETRY_OR_START_DECISION_REF,
            rdb.P7_R54_AHR_POST_MRB08_RDB_CANDIDATE_KIND_RETRY_OR_START_REF,
            "retry_or_start_candidate_present",
        ),
        (
            _op05_waiting_result(),
            rdb.P7_R54_AHR_POST_MRB08_RDB_STATUS_WAITING_EXTERNAL_CLAIM_REQUIRED_STOPPED_REF,
            rdb.P7_R54_AHR_POST_MRB08_RDB_OP04_MATERIAL_WAIT_EXTERNAL_CLAIM_REF,
            rdb.P7_R54_AHR_POST_MRB08_RDB_NEXT_STEP_WAIT_EXTERNAL_BODYFREE_CLAIM_REF,
            rdb.P7_R54_AHR_POST_MRB08_RDB_CANDIDATE_KIND_WAIT_EXTERNAL_CLAIM_REF,
            "external_claim_wait_candidate_present",
        ),
        (
            _op05_invalid_result(),
            rdb.P7_R54_AHR_POST_MRB08_RDB_STATUS_REPAIR_REQUIRED_AFTER_DHR_OP04_RESULT_STOPPED_REF,
            rdb.P7_R54_AHR_POST_MRB08_RDB_OP04_MATERIAL_REPAIR_REF,
            rdb.P7_R54_AHR_POST_MRB08_RDB_NEXT_STEP_REPAIR_RESULT_OR_MRB08_REF,
            rdb.P7_R54_AHR_POST_MRB08_RDB_CANDIDATE_KIND_REPAIR_REF,
            "repair_candidate_present",
        ),
    ],
)
def test_rdb_op04_materializes_branch_specific_manual_decision_for_all_consistent_result_lanes(
    op05: dict[str, object],
    expected_status: str,
    expected_material_ref: str,
    expected_candidate_ref: str,
    expected_candidate_kind: str,
    candidate_key: str,
) -> None:
    material = _op04_from_op05(op05)

    assert set(material) == set(rdb.P7_R54_AHR_POST_MRB08_RDB_OP04_REQUIRED_FIELD_REFS)
    assert material["schema_version"] == rdb.P7_R54_AHR_POST_MRB08_RDB_OP04_SCHEMA_VERSION
    assert material["operation_step_ref"] == rdb.P7_R54_AHR_POST_MRB08_RDB_OP04_STEP_REF
    assert material["op03_contract_valid"] is True
    assert material["op03_manual_decision_lane_resolved"] is True
    assert material["rdb_status_ref"] == expected_status
    assert material["branch_specific_manual_decision_material_ref"] == expected_material_ref
    assert material["selected_next_stage_candidate_ref"] == expected_candidate_ref
    assert material["selected_next_stage_candidate_kind_ref"] == expected_candidate_kind
    assert material[candidate_key] is True
    assert sum(
        1
        for key in (
            "dhr_op05_manual_handoff_candidate_present",
            "retry_or_start_candidate_present",
            "external_claim_wait_candidate_present",
            "repair_candidate_present",
            "unresolved_manual_hold_candidate_present",
            "blocked_candidate_present",
        )
        if material[key] is True
    ) == 1
    assert material["manual_decision_materialized"] is True
    assert material["manual_decision_materialized_bodyfree"] is True
    assert material["manual_decision_auto_executes_downstream"] is False
    assert material["selected_next_stage_candidate_not_executed"] is True
    assert material["rdb_op04_does_not_materialize_next_stage_candidate_envelope"] is True
    assert material["dhr_op05_called_here"] is False
    assert material["dhr_op06_called_here"] is False
    assert material["dmd_execution_started_here"] is False
    assert material["r52_actual_execution_started_here"] is False
    assert material["actual_review_operation_started_here"] is False
    assert material["p8_question_substitution_allowed"] is False
    assert material["question_text_materialized"] is False
    assert material["p8_start_allowed"] is False
    assert material["release_allowed"] is False
    assert material["next_required_step"] == rdb.P7_R54_AHR_POST_MRB08_RDB_OP05_STEP_REF
    assert rdb.assert_p7_r54_ahr_post_mrb08_rdb_op04_branch_specific_manual_decision_materialization_contract(material) is True
    _assert_common_bodyfree_no_touch_no_promotion(material)


def test_rdb_op04_confirmed_creates_dhr_op05_candidate_without_calling_dhr_op05() -> None:
    material = _op04_from_op05(_op05_confirmed())

    assert material["dhr_op05_manual_handoff_candidate_present"] is True
    assert material["confirmed_dhr_op05_manual_handoff_material_present"] is True
    assert material["dhr_op05_candidate_operation_ref"] == dhr.P7_R54_AHR_POST_ELR19_DHR_OP05_STEP_REF
    assert material["actual_source_claim_confirmed_for_downstream_handoff"] is True
    assert material["dhr_op05_called_here"] is False
    assert material["dhr_op06_called_here"] is False
    assert material["dmd_execution_started_here"] is False
    assert rdb.assert_p7_r54_ahr_post_mrb08_rdb_op04_branch_specific_manual_decision_materialization_contract(material) is True
    _assert_common_bodyfree_no_touch_no_promotion(material)


def test_rdb_op04_not_confirmed_stays_retry_or_start_without_p8_question() -> None:
    material = _op04_from_op05(_op05_not_confirmed())

    assert material["retry_or_start_candidate_present"] is True
    assert material["retry_or_start_decision_material_present"] is True
    assert material["retry_or_start_candidate_operation_ref"] == "actual_local_only_human_review_operation_retry_or_start_decision"
    assert material["p8_question_substitution_allowed"] is False
    assert material["question_text_materialized"] is False
    assert material["actual_review_operation_started_here"] is False
    assert rdb.assert_p7_r54_ahr_post_mrb08_rdb_op04_branch_specific_manual_decision_materialization_contract(material) is True
    _assert_common_bodyfree_no_touch_no_promotion(material)


def test_rdb_op04_waiting_external_claim_does_not_request_raw_evidence_or_body_full_packet() -> None:
    material = _op04_from_op05(_op05_waiting_result())

    assert material["external_claim_wait_candidate_present"] is True
    assert material["external_claim_wait_material_present"] is True
    assert material["raw_evidence_request_materialized_here"] is False
    assert material["body_full_packet_requested_here"] is False
    assert material["actual_review_operation_started_here"] is False
    assert rdb.assert_p7_r54_ahr_post_mrb08_rdb_op04_branch_specific_manual_decision_materialization_contract(material) is True
    _assert_common_bodyfree_no_touch_no_promotion(material)


def test_rdb_op04_invalid_result_creates_repair_dimensions_without_executing_repair() -> None:
    material = _op04_from_op05(_op05_invalid_result())

    assert material["repair_candidate_present"] is True
    assert material["repair_decision_material_present"] is True
    assert material["repair_dimension_refs"] == list(rdb.P7_R54_AHR_POST_MRB08_RDB_REPAIR_DIMENSION_REFS)
    assert "promotion_claim" in material["repair_dimension_refs"]
    assert "mrb_op08_validation_or_result_memo" in material["repair_dimension_refs"]
    assert material["repair_execution_started_here"] is False
    assert rdb.assert_p7_r54_ahr_post_mrb08_rdb_op04_branch_specific_manual_decision_materialization_contract(material) is True
    _assert_common_bodyfree_no_touch_no_promotion(material)


def test_rdb_op04_branch_status_mismatch_creates_repair_material_without_downstream_promotion() -> None:
    op01 = _op01_from_op05(_op05_not_confirmed())
    op01["dhr_op04_result_status_ref"] = dhr.P7_R54_AHR_POST_ELR19_DHR_OP04_STATUS_CONFIRMED_BODYFREE_REF
    op02 = rdb.build_p7_r54_ahr_post_mrb08_rdb_op02_mrb_selected_branch_dhr_op04_result_status_consistency_check(
        mrb_op08_result_memo_closure_intake=op01,
    )
    op03 = rdb.build_p7_r54_ahr_post_mrb08_rdb_op03_dhr_op04_result_manual_decision_lane_resolver(
        mrb_branch_dhr_status_consistency_check=op02,
    )
    material = rdb.build_p7_r54_ahr_post_mrb08_rdb_op04_branch_specific_manual_decision_materialization(
        dhr_op04_result_manual_decision_lane_resolver=op03,
    )

    assert material["rdb_status_ref"] == rdb.P7_R54_AHR_POST_MRB08_RDB_STATUS_REPAIR_REQUIRED_FOR_MRB08_BRANCH_STATUS_MISMATCH_REF
    assert material["repair_candidate_present"] is True
    assert "mrb08_branch_status_mapping_ref" in material["repair_dimension_refs"]
    assert "dhr_op04_result_status_ref_does_not_map_to_mrb_selected_branch_ref" in material["branch_material_blocker_refs"]
    assert material["dhr_op05_called_here"] is False
    assert material["p8_question_design_started"] is False
    assert rdb.assert_p7_r54_ahr_post_mrb08_rdb_op04_branch_specific_manual_decision_materialization_contract(material) is True
    _assert_common_bodyfree_no_touch_no_promotion(material)


def test_rdb_op04_missing_mrb08_closure_materializes_unresolved_manual_hold() -> None:
    material = rdb.build_p7_r54_ahr_post_mrb08_rdb_op04_branch_specific_manual_decision_materialization()

    assert material["rdb_status_ref"] == rdb.P7_R54_AHR_POST_MRB08_RDB_STATUS_WAITING_FOR_MRB08_RESULT_CLOSURE_REF
    assert material["unresolved_manual_hold_candidate_present"] is True
    assert material["unresolved_manual_hold_material_present"] is True
    assert material["unresolved_dimension_refs"] == list(rdb.P7_R54_AHR_POST_MRB08_RDB_UNRESOLVED_DIMENSION_REFS)
    assert material["dhr_op05_called_here"] is False
    assert material["release_allowed"] is False
    assert rdb.assert_p7_r54_ahr_post_mrb08_rdb_op04_branch_specific_manual_decision_materialization_contract(material) is True
    _assert_common_bodyfree_no_touch_no_promotion(material)


def test_rdb_op04_blocks_body_like_or_question_text_in_op03_without_copying_value() -> None:
    op03 = _op03_from_op05(_op05_confirmed())
    op03["question_text"] = "must not be copied into RDB material"
    material = rdb.build_p7_r54_ahr_post_mrb08_rdb_op04_branch_specific_manual_decision_materialization(
        dhr_op04_result_manual_decision_lane_resolver=op03,
    )

    assert material["rdb_status_ref"] == rdb.P7_R54_AHR_POST_MRB08_RDB_STATUS_BLOCKED_BODYFREE_LEAK_PROMOTION_OR_AUTORUN_REF
    assert material["blocked_candidate_present"] is True
    assert "op03.question_text" in material["op03_input_forbidden_payload_key_path_refs"]
    assert "must not be copied" not in repr(material)
    assert material["dhr_op05_called_here"] is False
    assert rdb.assert_p7_r54_ahr_post_mrb08_rdb_op04_branch_specific_manual_decision_materialization_contract(material) is True
    _assert_common_bodyfree_no_touch_no_promotion(material)


@pytest.mark.parametrize(
    ("op05", "expected_candidate_ref", "candidate_key"),
    [
        (_op05_confirmed(), rdb.P7_R54_AHR_POST_MRB08_RDB_NEXT_STEP_PREPARE_DHR_OP05_MANUAL_HANDOFF_DECISION_REF, "dhr_op05_manual_handoff_candidate_present"),
        (_op05_not_confirmed(), rdb.P7_R54_AHR_POST_MRB08_RDB_NEXT_STEP_PREPARE_RETRY_OR_START_DECISION_REF, "retry_or_start_candidate_present"),
        (_op05_waiting_result(), rdb.P7_R54_AHR_POST_MRB08_RDB_NEXT_STEP_WAIT_EXTERNAL_BODYFREE_CLAIM_REF, "external_claim_wait_candidate_present"),
        (_op05_invalid_result(), rdb.P7_R54_AHR_POST_MRB08_RDB_NEXT_STEP_REPAIR_RESULT_OR_MRB08_REF, "repair_candidate_present"),
    ],
)
def test_rdb_op05_wraps_next_stage_candidate_envelope_without_execution_for_all_materialized_lanes(
    op05: dict[str, object],
    expected_candidate_ref: str,
    candidate_key: str,
) -> None:
    envelope = _op05_from_op05(op05)

    assert set(envelope) == set(rdb.P7_R54_AHR_POST_MRB08_RDB_OP05_REQUIRED_FIELD_REFS)
    assert envelope["schema_version"] == rdb.P7_R54_AHR_POST_MRB08_RDB_OP05_SCHEMA_VERSION
    assert envelope["operation_step_ref"] == rdb.P7_R54_AHR_POST_MRB08_RDB_OP05_STEP_REF
    assert envelope["op04_contract_valid"] is True
    assert envelope["op04_manual_decision_materialized"] is True
    assert envelope["selected_next_stage_candidate_ref"] == expected_candidate_ref
    assert envelope[candidate_key] is True
    assert sum(
        1
        for key in (
            "dhr_op05_manual_handoff_candidate_present",
            "retry_or_start_candidate_present",
            "external_claim_wait_candidate_present",
            "repair_candidate_present",
            "unresolved_manual_hold_candidate_present",
            "blocked_candidate_present",
        )
        if envelope[key] is True
    ) == 1
    assert envelope["candidate_envelope_bodyfree"] is True
    assert envelope["next_stage_candidate_enveloped_without_execution"] is True
    assert envelope["selected_next_stage_candidate_not_executed"] is True
    assert envelope["downstream_auto_execution_allowed"] is False
    assert envelope["dhr_op05_builder_called_here"] is False
    assert envelope["dhr_op06_builder_called_here"] is False
    assert envelope["dmd_builder_called_here"] is False
    assert envelope["r52_actual_execution_called_here"] is False
    assert envelope["actual_local_human_review_operation_started_here"] is False
    assert envelope["p8_question_candidate_created"] is False
    assert envelope["p8_question_design_started_here"] is False
    assert envelope["release_decision_created_here"] is False
    assert envelope["next_required_step"] == rdb.P7_R54_AHR_POST_MRB08_RDB_OP06_STEP_REF
    assert rdb.assert_p7_r54_ahr_post_mrb08_rdb_op05_next_stage_candidate_envelope_without_execution_contract(envelope) is True
    _assert_common_bodyfree_no_touch_no_promotion(envelope)


def test_rdb_op05_confirmed_candidate_does_not_call_dhr_op05_builder_or_dmd() -> None:
    envelope = _op05_from_op05(_op05_confirmed())

    assert envelope["dhr_op05_manual_handoff_candidate_present"] is True
    assert envelope["dhr_op05_candidate_but_builder_not_called"] is True
    assert envelope["selected_next_stage_operation_candidate_ref"] == dhr.P7_R54_AHR_POST_ELR19_DHR_OP05_STEP_REF
    assert envelope["dhr_op05_builder_called_here"] is False
    assert envelope["dhr_op05_called_here"] is False
    assert envelope["dmd_execution_started_here"] is False
    assert envelope["dmd_builder_called_here"] is False
    assert envelope["release_allowed"] is False
    assert rdb.assert_p7_r54_ahr_post_mrb08_rdb_op05_next_stage_candidate_envelope_without_execution_contract(envelope) is True
    _assert_common_bodyfree_no_touch_no_promotion(envelope)


def test_rdb_op05_blocks_promotion_mutation_in_op04_before_envelope_execution() -> None:
    op04 = _op04_from_op05(_op05_confirmed())
    op04["dhr_op05_called_here"] = True
    envelope = rdb.build_p7_r54_ahr_post_mrb08_rdb_op05_next_stage_candidate_envelope_without_execution(
        branch_specific_manual_decision_materialization=op04,
    )

    assert envelope["rdb_status_ref"] == rdb.P7_R54_AHR_POST_MRB08_RDB_STATUS_BLOCKED_BODYFREE_LEAK_PROMOTION_OR_AUTORUN_REF
    assert envelope["blocked_candidate_present"] is True
    assert "op04.dhr_op05_called_here" in envelope["op04_input_promotion_claim_refs"]
    assert envelope["dhr_op05_called_here"] is False
    assert envelope["dhr_op05_builder_called_here"] is False
    assert envelope["p8_start_allowed"] is False
    assert rdb.assert_p7_r54_ahr_post_mrb08_rdb_op05_next_stage_candidate_envelope_without_execution_contract(envelope) is True
    _assert_common_bodyfree_no_touch_no_promotion(envelope)


def test_rdb_op04_op05_contracts_reject_execution_or_candidate_promotion_mutations() -> None:
    op04 = _op04_from_op05(_op05_confirmed())
    op04["selected_next_stage_candidate_not_executed"] = False
    with pytest.raises(ValueError):
        rdb.assert_p7_r54_ahr_post_mrb08_rdb_op04_branch_specific_manual_decision_materialization_contract(op04)

    op04 = _op04_from_op05(_op05_not_confirmed())
    op04["p8_question_substitution_allowed"] = True
    with pytest.raises(ValueError):
        rdb.assert_p7_r54_ahr_post_mrb08_rdb_op04_branch_specific_manual_decision_materialization_contract(op04)

    envelope = _op05_from_op05(_op05_confirmed())
    envelope["dhr_op05_builder_called_here"] = True
    with pytest.raises(ValueError):
        rdb.assert_p7_r54_ahr_post_mrb08_rdb_op05_next_stage_candidate_envelope_without_execution_contract(envelope)

    envelope = _op05_from_op05(_op05_confirmed())
    envelope["downstream_auto_execution_allowed"] = True
    with pytest.raises(ValueError):
        rdb.assert_p7_r54_ahr_post_mrb08_rdb_op05_next_stage_candidate_envelope_without_execution_contract(envelope)


def test_rdb_op04_op05_full_title_aliases_match_short_builders_and_asserts() -> None:
    assert (
        rdb.build_p7_r54_ahr_post_mrb08_dhr_op04_result_manual_decision_rdb_op04_branch_specific_manual_decision_materialization
        is rdb.build_p7_r54_ahr_post_mrb08_rdb_op04_branch_specific_manual_decision_materialization
    )
    assert (
        rdb.assert_p7_r54_ahr_post_mrb08_dhr_op04_result_manual_decision_rdb_op04_branch_specific_manual_decision_materialization_contract
        is rdb.assert_p7_r54_ahr_post_mrb08_rdb_op04_branch_specific_manual_decision_materialization_contract
    )
    assert (
        rdb.build_p7_r54_ahr_post_mrb08_dhr_op04_result_manual_decision_rdb_op05_next_stage_candidate_envelope_without_execution
        is rdb.build_p7_r54_ahr_post_mrb08_rdb_op05_next_stage_candidate_envelope_without_execution
    )
    assert (
        rdb.assert_p7_r54_ahr_post_mrb08_dhr_op04_result_manual_decision_rdb_op05_next_stage_candidate_envelope_without_execution_contract
        is rdb.assert_p7_r54_ahr_post_mrb08_rdb_op05_next_stage_candidate_envelope_without_execution_contract
    )
