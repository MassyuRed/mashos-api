# -*- coding: utf-8 -*-
"""R54-AHR Post-DHR09 RSR-OP14/OP15 final validation and branch resolver tests."""

from __future__ import annotations

from pathlib import Path
import sys

import pytest

TEST_DIR = Path(__file__).resolve().parent
if str(TEST_DIR) not in sys.path:
    sys.path.insert(0, str(TEST_DIR))

import emlis_ai_p7_r54_ahr_post_dhr09_actual_local_review_retry_start_decision_20260704 as rsr
from test_r54_ahr_post_dhr09_actual_local_review_retry_start_decision_rsr_op02_op03_20260704 import (
    _assert_common_bodyfree_no_touch_no_promotion,
)
from test_r54_ahr_post_dhr09_actual_local_review_retry_start_decision_rsr_op04_op05_20260704 import (
    _rsr_op03_allow_accepted,
    _rsr_op04_ready,
)
from test_r54_ahr_post_dhr09_actual_local_review_retry_start_decision_rsr_op06_op07_20260704 import (
    _rsr_op05_ready,
    _rsr_op06_ready,
)
from test_r54_ahr_post_dhr09_actual_local_review_retry_start_decision_rsr_op08_op09_20260704 import (
    _rsr_op07_ready,
)
from test_r54_ahr_post_dhr09_actual_local_review_retry_start_decision_rsr_op10_op11_20260704 import (
    _rsr_op09_completed_receipt_required,
    _rsr_op10_accepted,
)
from test_r54_ahr_post_dhr09_actual_local_review_retry_start_decision_rsr_op12_op13_20260704 import (
    _rsr_op11_accepted,
    _rsr_op12_accepted,
    _valid_disposal_purge_receipt,
)


def _rsr_op13_accepted() -> dict[str, object]:
    op12 = _rsr_op12_accepted()
    material = rsr.build_p7_r54_ahr_post_dhr09_rsr_op13_disposal_purge_receipt_intake(
        question_need_observation_rows_intake=op12,
        disposal_purge_receipt=_valid_disposal_purge_receipt(op12),
    )
    assert rsr.assert_p7_r54_ahr_post_dhr09_rsr_op13_disposal_purge_receipt_intake_contract(material) is True
    assert material["rsr_op13_disposal_purge_receipt_accepted"] is True
    return material


def _rsr_op14_full_ready() -> dict[str, object]:
    material = rsr.build_p7_r54_ahr_post_dhr09_rsr_op14_final_no_leak_no_promotion_source_kind_validation(
        explicit_local_only_allow_gate=_rsr_op03_allow_accepted(),
        readiness_blocker_classifier=_rsr_op04_ready(),
        local_only_review_session_envelope=_rsr_op05_ready(),
        body_full_packet_transient_request_boundary=_rsr_op06_ready(),
        body_full_packet_generation_receipt_intake=_rsr_op07_ready(),
        actual_local_only_review_lifecycle_state_capture=_rsr_op09_completed_receipt_required(),
        actual_operation_receipt_intake=_rsr_op10_accepted(),
        review_rows_rating_rows_intake=_rsr_op11_accepted(),
        question_need_observation_rows_intake=_rsr_op12_accepted(),
        disposal_purge_receipt_intake=_rsr_op13_accepted(),
    )
    assert rsr.assert_p7_r54_ahr_post_dhr09_rsr_op14_final_no_leak_no_promotion_source_kind_validation_contract(material) is True
    assert material["rsr_op14_final_validation_passed"] is True
    return material


def _assert_op14_no_execution_or_promotion(material: dict[str, object]) -> None:
    assert material["actual_review_evidence_complete_here"] is False
    assert material["rsr_op14_does_not_create_or_modify_actual_evidence"] is True
    assert material["rsr_op14_does_not_execute_actual_review"] is True
    assert material["rsr_op14_does_not_execute_dhr_dmd_r52_or_release"] is True
    assert material["rsr_op14_does_not_start_p5_p6_p8_p7"] is True
    assert material["rsr_op14_does_not_change_api_db_rn_runtime_response_key"] is True
    assert material["dmd_execution_started_here"] is False
    assert material["r52_actual_execution_started_here"] is False
    assert material["p8_start_allowed"] is False
    assert material["p8_question_design_started"] is False
    assert material["p7_complete"] is False
    assert material["release_allowed"] is False


def _assert_op15_no_auto_execution(material: dict[str, object]) -> None:
    assert material["dhr_actual_source_claim_reintake_executed_here"] is False
    assert material["actual_source_claim_for_dhr_reintake_materialized_here_by_helper"] is False
    assert material["downstream_auto_execution_allowed"] is False
    assert material["actual_review_evidence_complete_here"] is False
    assert material["dmd_execution_started_here"] is False
    assert material["r52_actual_execution_started_here"] is False
    assert material["p5_final_allowed"] is False
    assert material["p6_start_allowed"] is False
    assert material["p8_start_allowed"] is False
    assert material["p8_question_design_started"] is False
    assert material["p8_question_implementation_started"] is False
    assert material["p7_complete"] is False
    assert material["release_allowed"] is False
    assert material["rsr_op15_does_not_execute_dhr_reintake"] is True
    assert material["rsr_op15_does_not_execute_dmd_or_r52"] is True
    assert material["rsr_op15_does_not_start_p5_p6_p8_p7_or_release"] is True
    assert material["rsr_op15_does_not_materialize_p8_question_spec"] is True


def test_rsr_op14_waits_for_accepted_disposal_purge_receipt_before_final_validation() -> None:
    material = rsr.build_p7_r54_ahr_post_dhr09_rsr_op14_final_no_leak_no_promotion_source_kind_validation()

    assert set(material) == set(rsr.P7_R54_AHR_POST_DHR09_RSR_OP14_REQUIRED_FIELD_REFS)
    assert material["schema_version"] == rsr.P7_R54_AHR_POST_DHR09_RSR_OP14_SCHEMA_VERSION
    assert material["operation_step_ref"] == rsr.P7_R54_AHR_POST_DHR09_RSR_OP14_STEP_REF
    assert material["rsr_op14_status_ref"] == rsr.P7_R54_AHR_POST_DHR09_RSR_OP14_STATUS_WAITING_FOR_ACCEPTED_OP13_REF
    assert material["rsr_op14_waiting_for_accepted_disposal_purge_receipt"] is True
    assert material["rsr_op14_final_validation_passed"] is False
    assert material["next_required_step"] == rsr.P7_R54_AHR_POST_DHR09_RSR_NEXT_STEP_WAIT_FOR_ACCEPTED_DISPOSAL_PURGE_RECEIPT_BEFORE_FINAL_VALIDATION_REF
    assert rsr.assert_p7_r54_ahr_post_dhr09_rsr_op14_final_no_leak_no_promotion_source_kind_validation_contract(material) is True
    _assert_common_bodyfree_no_touch_no_promotion(material)
    _assert_op14_no_execution_or_promotion(material)


def test_rsr_op14_passes_final_no_leak_no_promotion_source_kind_validation_with_full_bodyfree_chain() -> None:
    material = _rsr_op14_full_ready()

    assert material["rsr_op14_status_ref"] == rsr.P7_R54_AHR_POST_DHR09_RSR_OP14_STATUS_PASSED_BODYFREE_REF
    assert material["final_validation_forbidden_payload_key_path_refs"] == []
    assert material["final_validation_body_like_value_path_refs"] == []
    assert material["final_validation_promotion_claim_refs"] == []
    assert material["final_validation_invalid_source_kind_refs"] == []
    assert material["final_validation_question_text_materialization_refs"] == []
    assert material["final_validation_helper_generated_actual_claim_refs"] == []
    assert material["complete_candidate_prerequisite_missing_refs"] == []
    assert material["actual_evidence_complete_candidate_ready_for_op15"] is True
    assert material["actual_review_evidence_complete_here"] is False
    assert material["next_required_step"] == rsr.P7_R54_AHR_POST_DHR09_RSR_OP15_STEP_REF
    _assert_common_bodyfree_no_touch_no_promotion(material)
    _assert_op14_no_execution_or_promotion(material)


@pytest.mark.parametrize(
    ("additional_material", "expected_field", "expected_blocker"),
    [
        ({"raw_input": "do not leak this body"}, "final_validation_forbidden_payload_key_path_refs", "final_validation_body_leak_promotion_source_kind_or_helper_claim_detected"),
        ({"release_allowed": True}, "final_validation_promotion_claim_refs", "final_validation_body_leak_promotion_source_kind_or_helper_claim_detected"),
        ({"source_kind_ref": "unit_test_fixture_not_actual"}, "final_validation_invalid_source_kind_refs", "final_validation_body_leak_promotion_source_kind_or_helper_claim_detected"),
        ({"question_text_materialized": True}, "final_validation_question_text_materialization_refs", "final_validation_body_leak_promotion_source_kind_or_helper_claim_detected"),
        ({"row_created_by_helper": True}, "final_validation_helper_generated_actual_claim_refs", "final_validation_body_leak_promotion_source_kind_or_helper_claim_detected"),
    ],
)
def test_rsr_op14_blocks_body_leak_promotion_source_kind_question_materialization_or_helper_actual_claim(additional_material, expected_field: str, expected_blocker: str) -> None:
    op13 = _rsr_op13_accepted()
    material = rsr.build_p7_r54_ahr_post_dhr09_rsr_op14_final_no_leak_no_promotion_source_kind_validation(
        disposal_purge_receipt_intake=op13,
        additional_bodyfree_materials={"bad_material": additional_material},
    )

    assert material["rsr_op14_status_ref"] == rsr.P7_R54_AHR_POST_DHR09_RSR_OP14_STATUS_BODY_LEAK_OR_SOURCE_CLAIM_BLOCKED_REF
    assert material[expected_field]
    assert expected_blocker in material["op14_blocker_refs"]
    assert material["rsr_op14_final_validation_passed"] is False
    assert material["actual_evidence_complete_candidate_ready_for_op15"] is False
    assert "do not leak this body" not in repr(material)
    assert rsr.assert_p7_r54_ahr_post_dhr09_rsr_op14_final_no_leak_no_promotion_source_kind_validation_contract(material) is True
    _assert_common_bodyfree_no_touch_no_promotion(material)
    _assert_op14_no_execution_or_promotion(material)


@pytest.mark.parametrize(
    ("field", "bad_value"),
    [
        ("rsr_op14_final_validation_passed", False),
        ("rsr_op14_does_not_execute_actual_review", False),
        ("actual_review_evidence_complete_here", True),
        ("dmd_execution_started_here", True),
        ("r52_actual_execution_started_here", True),
        ("p8_start_allowed", True),
        ("p8_question_design_started", True),
        ("p7_complete", True),
        ("release_allowed", True),
        ("next_required_step", rsr.P7_R54_AHR_POST_DHR09_RSR_NEXT_STEP_RETURN_TO_DHR_ACTUAL_SOURCE_CLAIM_REINTAKE_NO_AUTO_EXECUTION_REF),
    ],
)
def test_rsr_op14_contract_rejects_final_validation_completion_or_downstream_promotion_mutations(field: str, bad_value: object) -> None:
    material = _rsr_op14_full_ready()
    material[field] = bad_value

    with pytest.raises(ValueError):
        rsr.assert_p7_r54_ahr_post_dhr09_rsr_op14_final_no_leak_no_promotion_source_kind_validation_contract(material)


def test_rsr_op15_resolves_actual_evidence_complete_candidate_for_dhr_reintake_without_auto_execution() -> None:
    material = rsr.build_p7_r54_ahr_post_dhr09_rsr_op15_actual_evidence_complete_candidate_next_branch_resolver(
        final_validation=_rsr_op14_full_ready(),
    )

    assert set(material) == set(rsr.P7_R54_AHR_POST_DHR09_RSR_OP15_REQUIRED_FIELD_REFS)
    assert material["schema_version"] == rsr.P7_R54_AHR_POST_DHR09_RSR_OP15_SCHEMA_VERSION
    assert material["operation_step_ref"] == rsr.P7_R54_AHR_POST_DHR09_RSR_OP15_STEP_REF
    assert material["rsr_op15_branch_ref"] == rsr.P7_R54_AHR_POST_DHR09_RSR_OP15_BRANCH_ACTUAL_REVIEW_EVIDENCE_READY_FOR_DHR_REINTAKE_NO_AUTO_EXECUTION_REF
    assert material["actual_evidence_complete_candidate"] is True
    assert material["actual_evidence_complete_candidate_ready_for_dhr_reintake_no_auto_execution"] is True
    assert material["dhr_actual_source_claim_reintake_required_next"] is True
    assert material["source_claim_bundle_candidate_source_kind_ref"] == rsr.P7_R54_AHR_POST_DHR09_RSR_ACTUAL_REVIEW_SOURCE_KIND_REF
    assert material["source_claim_bundle_candidate_reviewed_case_count"] == rsr.P7_R54_AHR_POST_DHR09_RSR_EXPECTED_CASE_COUNT
    assert material["source_claim_bundle_candidate_selection_row_count"] == rsr.P7_R54_AHR_POST_DHR09_RSR_EXPECTED_CASE_COUNT
    assert material["next_required_step"] == rsr.P7_R54_AHR_POST_DHR09_RSR_NEXT_STEP_RETURN_TO_DHR_ACTUAL_SOURCE_CLAIM_REINTAKE_NO_AUTO_EXECUTION_REF
    assert rsr.assert_p7_r54_ahr_post_dhr09_rsr_op15_actual_evidence_complete_candidate_next_branch_resolver_contract(material) is True
    _assert_common_bodyfree_no_touch_no_promotion(material)
    _assert_op15_no_auto_execution(material)


def test_rsr_op15_waits_for_explicit_allow_when_final_validation_passed_but_chain_prerequisites_are_missing() -> None:
    op13 = _rsr_op13_accepted()
    op14 = rsr.build_p7_r54_ahr_post_dhr09_rsr_op14_final_no_leak_no_promotion_source_kind_validation(
        disposal_purge_receipt_intake=op13,
    )
    assert op14["rsr_op14_final_validation_passed"] is True
    assert "explicit_allow_accepted" in op14["complete_candidate_prerequisite_missing_refs"]
    material = rsr.build_p7_r54_ahr_post_dhr09_rsr_op15_actual_evidence_complete_candidate_next_branch_resolver(
        final_validation=op14,
    )

    assert material["rsr_op15_branch_ref"] == rsr.P7_R54_AHR_POST_DHR09_RSR_OP15_BRANCH_WAIT_FOR_EXPLICIT_LOCAL_ONLY_ALLOW_REF
    assert material["rsr_op15_wait_for_explicit_allow"] is True
    assert material["actual_evidence_complete_candidate"] is False
    assert material["dhr_actual_source_claim_reintake_required_next"] is False
    assert material["next_required_step"] == rsr.P7_R54_AHR_POST_DHR09_RSR_NEXT_STEP_RETURN_TO_RSR_OP03_EXPLICIT_ALLOW_GATE_REF
    assert rsr.assert_p7_r54_ahr_post_dhr09_rsr_op15_actual_evidence_complete_candidate_next_branch_resolver_contract(material) is True
    _assert_common_bodyfree_no_touch_no_promotion(material)
    _assert_op15_no_auto_execution(material)


def test_rsr_op15_blocks_when_op14_final_validation_is_blocked() -> None:
    op14 = rsr.build_p7_r54_ahr_post_dhr09_rsr_op14_final_no_leak_no_promotion_source_kind_validation(
        disposal_purge_receipt_intake=_rsr_op13_accepted(),
        additional_bodyfree_materials={"bad_source": {"source_kind_ref": "synthetic_fixture"}},
    )
    assert op14["rsr_op14_body_leak_promotion_or_source_kind_blocked"] is True
    material = rsr.build_p7_r54_ahr_post_dhr09_rsr_op15_actual_evidence_complete_candidate_next_branch_resolver(final_validation=op14)

    assert material["rsr_op15_branch_ref"] == rsr.P7_R54_AHR_POST_DHR09_RSR_OP15_BRANCH_BODYFREE_LEAK_OR_SOURCE_CLAIM_BLOCKED_REF
    assert material["rsr_op15_bodyfree_leak_or_source_claim_blocked"] is True
    assert material["actual_evidence_complete_candidate"] is False
    assert material["next_required_step"] == rsr.P7_R54_AHR_POST_DHR09_RSR_NEXT_STEP_BLOCKED_BODYFREE_LEAK_OR_SOURCE_CLAIM_BEFORE_DHR_REINTAKE_REF
    assert rsr.assert_p7_r54_ahr_post_dhr09_rsr_op15_actual_evidence_complete_candidate_next_branch_resolver_contract(material) is True
    _assert_common_bodyfree_no_touch_no_promotion(material)
    _assert_op15_no_auto_execution(material)


@pytest.mark.parametrize(
    ("field", "bad_value"),
    [
        ("actual_evidence_complete_candidate", False),
        ("dhr_actual_source_claim_reintake_required_next", False),
        ("dhr_actual_source_claim_reintake_executed_here", True),
        ("downstream_auto_execution_allowed", True),
        ("actual_review_evidence_complete_here", True),
        ("dmd_execution_started_here", True),
        ("r52_actual_execution_started_here", True),
        ("p8_start_allowed", True),
        ("p8_question_design_started", True),
        ("p7_complete", True),
        ("release_allowed", True),
        ("next_required_step", rsr.P7_R54_AHR_POST_DHR09_RSR_OP16_STEP_REF),
    ],
)
def test_rsr_op15_contract_rejects_dhr_execution_downstream_promotion_or_candidate_mutations(field: str, bad_value: object) -> None:
    material = rsr.build_p7_r54_ahr_post_dhr09_rsr_op15_actual_evidence_complete_candidate_next_branch_resolver(
        final_validation=_rsr_op14_full_ready(),
    )
    material[field] = bad_value

    with pytest.raises(ValueError):
        rsr.assert_p7_r54_ahr_post_dhr09_rsr_op15_actual_evidence_complete_candidate_next_branch_resolver_contract(material)


def test_rsr_op14_op15_full_title_aliases_match_canonical_builders() -> None:
    op14 = _rsr_op14_full_ready()
    alias_op14 = rsr.build_p7_r54_ahr_post_dhr09_actual_local_review_retry_start_decision_rsr_op14_final_no_leak_no_promotion_source_kind_validation(
        explicit_local_only_allow_gate=_rsr_op03_allow_accepted(),
        readiness_blocker_classifier=_rsr_op04_ready(),
        local_only_review_session_envelope=_rsr_op05_ready(),
        body_full_packet_transient_request_boundary=_rsr_op06_ready(),
        body_full_packet_generation_receipt_intake=_rsr_op07_ready(),
        actual_local_only_review_lifecycle_state_capture=_rsr_op09_completed_receipt_required(),
        actual_operation_receipt_intake=_rsr_op10_accepted(),
        review_rows_rating_rows_intake=_rsr_op11_accepted(),
        question_need_observation_rows_intake=_rsr_op12_accepted(),
        disposal_purge_receipt_intake=_rsr_op13_accepted(),
    )
    assert alias_op14 == op14
    assert rsr.assert_p7_r54_ahr_post_dhr09_actual_local_review_retry_start_decision_rsr_op14_final_no_leak_no_promotion_source_kind_validation_contract(alias_op14) is True

    canonical_op15 = rsr.build_p7_r54_ahr_post_dhr09_rsr_op15_actual_evidence_complete_candidate_next_branch_resolver(final_validation=op14)
    alias_op15 = rsr.build_p7_r54_ahr_post_dhr09_actual_local_review_retry_start_decision_rsr_op15_actual_evidence_complete_candidate_next_branch_resolver(final_validation=op14)
    assert alias_op15 == canonical_op15
    assert rsr.assert_p7_r54_ahr_post_dhr09_actual_local_review_retry_start_decision_rsr_op15_actual_evidence_complete_candidate_next_branch_resolver_contract(alias_op15) is True
