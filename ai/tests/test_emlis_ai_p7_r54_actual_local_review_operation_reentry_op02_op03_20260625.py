# -*- coding: utf-8 -*-
from __future__ import annotations

import json
from copy import deepcopy
from functools import lru_cache

import pytest

import emlis_ai_p7_r54_actual_local_review_operation_reentry_20260625 as op
import emlis_ai_p7_r54_p5_human_blind_qa_actual_local_review_result_handoff as r54
import emlis_ai_p7_r55_r54_evidence_reconcile_r52_reintake_decision_materialization as r55


FORBIDDEN_DUMP_TOKENS = (
    '"raw_input":',
    '"raw_answer":',
    '"comment_text":',
    '"comment_text_body":',
    '"returned_emlis_surface":',
    '"current_input_review_surface":',
    '"bounded_owned_history_review_surface":',
    '"reviewer_free_text":',
    '"reviewer_note":',
    '"reviewer_notes":',
    '"question_text":',
    '"draft_question_text":',
    '"question_body":',
    '"local_absolute_path":',
    '"body_content_hash":',
    '"packet_content_hash":',
    '"terminal_output": "',
    '"stdout":',
    '"stderr":',
    '"traceback":',
)
FORBIDDEN_TRUE_TOKENS = (
    '"api_changed": true',
    '"db_changed": true',
    '"rn_changed": true',
    '"runtime_changed": true',
    '"api_route_changed": true',
    '"db_schema_changed": true',
    '"rn_visible_contract_changed": true',
    '"public_response_top_level_key_added": true',
    '"release_allowed": true',
    '"p7_complete": true',
    '"p8_start_allowed": true',
    '"p6_limited_human_readfeel_start_allowed": true',
    '"question_trigger_logic_implemented": true',
    '"p8_question_implementation_spec_finalized_here": true',
    '"actual_human_review_run_here": true',
    '"actual_manual_review_run_here": true',
    '"body_full_packet_generated_here": true',
    '"actual_rating_rows_materialized_here": true',
    '"actual_question_need_observation_rows_materialized_here": true',
    '"actual_disposal_receipt_materialized_here": true',
    '"old_helper_refs_allowed_as_actual_review_basis": true',
    '"historical_helper_refs_can_be_used_for_actual_review_basis": true',
    '"historical_helper_refs_used_as_actual_review_basis": true',
)


def _assert_body_free_no_promotion(material: dict[str, object]) -> None:
    dumped = json.dumps(material, ensure_ascii=False, sort_keys=True).lower()
    for forbidden in FORBIDDEN_DUMP_TOKENS:
        assert forbidden not in dumped
    for forbidden in FORBIDDEN_TRUE_TOKENS:
        assert forbidden not in dumped


@lru_cache(maxsize=1)
def _cached_op01() -> tuple[dict[str, object]]:
    material = op.build_p7_r54_op01_operation_current_snapshot_refs_refreeze()
    assert op.assert_p7_r54_op01_operation_current_snapshot_refs_refreeze_contract(material) is True
    return (material,)


def _op01() -> dict[str, object]:
    return deepcopy(_cached_op01()[0])


@lru_cache(maxsize=1)
def _cached_op02() -> tuple[dict[str, object]]:
    material = op.build_p7_r54_op02_historical_helper_source_delta_reconcile(
        operation_current_snapshot_refreeze=_op01(),
    )
    assert op.assert_p7_r54_op02_historical_helper_source_delta_reconcile_contract(material) is True
    return (material,)


def _op02() -> dict[str, object]:
    return deepcopy(_cached_op02()[0])


@lru_cache(maxsize=1)
def _cached_op03() -> tuple[dict[str, object]]:
    material = op.build_p7_r54_op03_r55_hold_intake(
        historical_helper_source_delta_reconcile=_op02(),
    )
    assert op.assert_p7_r54_op03_r55_hold_intake_contract(material) is True
    return (material,)


def _op03() -> dict[str, object]:
    return deepcopy(_cached_op03()[0])


def test_r54_op02_materializes_source_delta_rows_without_mixing_historical_refs_into_current_basis() -> None:
    material = _op02()

    assert material["schema_version"] == op.P7_R54_OPERATION_HISTORICAL_HELPER_SOURCE_DELTA_RECONCILE_SCHEMA_VERSION
    assert set(material) == set(op.P7_R54_OPERATION_HISTORICAL_HELPER_SOURCE_DELTA_RECONCILE_REQUIRED_FIELD_REFS)
    assert material["policy_section"] == op.P7_R54_OP02_STEP_REF
    assert material["operation_step_ref"] == op.P7_R54_OP02_STEP_REF
    assert material["op01_schema_version"] == op.P7_R54_OPERATION_CURRENT_SNAPSHOT_REFREEZE_SCHEMA_VERSION
    assert material["op01_next_required_step"] == op.P7_R54_OP02_STEP_REF
    assert material["operation_current_refs"] == op.P7_R54_OPERATION_CURRENT_REFS
    assert material["operation_current_refs"]["backend_zip_ref"] == "mashos-api(166).zip"
    assert material["historical_helper_ref_groups"] == list(op.P7_R54_OPERATION_HISTORICAL_HELPER_REF_GROUP_REFS)
    assert material["historical_helper_refs"] == op.P7_R54_OPERATION_HISTORICAL_HELPER_REFS
    assert material["source_delta_row_refs"] == list(op.P7_R54_SOURCE_DELTA_ROW_REFS)
    assert material["source_delta_row_count"] == 2
    assert material["source_delta_rows_required_next"] is False
    assert material["source_delta_rows_materialized_here"] is True
    assert material["all_historical_helper_refs_reconciled"] is True
    assert material["historical_helper_refs_can_be_used_for_helper_regression_only"] is True
    assert material["historical_helper_refs_can_be_used_for_actual_review_basis"] is False
    assert material["old_helper_refs_allowed_as_actual_review_basis"] is False
    assert material["historical_helper_refs_used_as_actual_review_basis"] is False
    assert material["operation_current_refs_used_as_actual_review_basis"] is True
    assert material["operation_current_refs_are_actual_review_basis"] is True

    rows = {row["source_delta_row_ref"]: row for row in material["source_delta_rows"]}
    assert set(rows) == set(op.P7_R54_SOURCE_DELTA_ROW_REFS)
    r54_row = rows["r54_helper_refs_vs_operation_current_refs"]
    r55_row = rows["r55_helper_refs_vs_operation_current_refs"]

    assert r54_row["helper_ref_group"] == "r54_helper_current_received_snapshot_refs"
    assert r54_row["helper_snapshot_refs"] == r54.P7_R54_CURRENT_RECEIVED_SNAPSHOT_REFS
    assert r54_row["helper_snapshot_refs"]["backend_zip_ref"] == "mashos-api(162).zip"
    assert r54_row["operation_current_refs"] == op.P7_R54_OPERATION_CURRENT_REFS
    assert "backend_zip_ref" in r54_row["changed_ref_keys"]
    assert r54_row["historical_helper_refs_used_as_actual_review_basis"] is False
    assert r54_row["operation_current_refs_used_as_actual_review_basis"] is True

    assert r55_row["helper_ref_group"] == "r55_helper_current_received_snapshot_refs"
    assert r55_row["helper_snapshot_refs"] == r55.P7_R55_CURRENT_RECEIVED_SNAPSHOT_REFS
    assert r55_row["helper_snapshot_refs"]["backend_zip_ref"] == "mashos-api(163).zip"
    assert r55_row["operation_current_refs"] == op.P7_R54_OPERATION_CURRENT_REFS
    assert "backend_zip_ref" in r55_row["changed_ref_keys"]
    assert r55_row["historical_helper_refs_used_as_actual_review_basis"] is False
    assert r55_row["operation_current_refs_used_as_actual_review_basis"] is True

    assert tuple(material["implemented_steps"]) == op.P7_R54_OP02_IMPLEMENTED_STEPS
    assert tuple(material["not_yet_implemented_steps"]) == op.P7_R54_OP02_NOT_YET_IMPLEMENTED_STEPS
    assert material["next_required_step"] == op.P7_R54_OP03_STEP_REF
    assert material["body_full_generation_blocked_until_preflight"] is True
    assert material["actual_human_review_run_here"] is False
    assert material["body_full_packet_generated_here"] is False
    assert material["p6_limited_human_readfeel_start_allowed"] is False
    assert material["p8_start_allowed"] is False
    assert material["release_allowed"] is False
    assert material["question_text_included"] is False
    assert material["draft_question_text_included"] is False
    assert material["local_path_included"] is False

    _assert_body_free_no_promotion(material)


@pytest.mark.parametrize(
    "key,value",
    [
        ("source_delta_rows_materialized_here", False),
        ("all_historical_helper_refs_reconciled", False),
        ("historical_helper_refs_can_be_used_for_helper_regression_only", False),
        ("historical_helper_refs_can_be_used_for_actual_review_basis", True),
        ("old_helper_refs_allowed_as_actual_review_basis", True),
        ("historical_helper_refs_used_as_actual_review_basis", True),
        ("operation_current_refs_used_as_actual_review_basis", False),
        ("operation_current_refs_are_actual_review_basis", False),
        ("body_full_generation_blocked_until_preflight", False),
        ("human_review_completion_claim_blocked_here", False),
        ("p6_p8_release_promotion_blocked_here", False),
        ("actual_human_review_run_here", True),
        ("body_full_packet_generated_here", True),
        ("actual_rating_rows_materialized_here", True),
        ("actual_question_need_observation_rows_materialized_here", True),
        ("p6_limited_human_readfeel_start_allowed", True),
        ("p8_start_allowed", True),
        ("release_allowed", True),
        ("question_text_included", True),
        ("draft_question_text_included", True),
        ("local_path_included", True),
    ],
)
def test_r54_op02_rejects_current_basis_mixing_review_claims_promotion_or_body_boundary_mutation(
    key: str,
    value: object,
) -> None:
    material = _op02()
    material[key] = value
    with pytest.raises(ValueError):
        op.assert_p7_r54_op02_historical_helper_source_delta_reconcile_contract(material)


def test_r54_op02_rejects_source_delta_rows_relabelled_removed_or_rebased_to_old_helper_refs() -> None:
    material = _op02()
    material["source_delta_rows"][0]["operation_current_refs"] = dict(r54.P7_R54_CURRENT_RECEIVED_SNAPSHOT_REFS)
    with pytest.raises(ValueError):
        op.assert_p7_r54_op02_historical_helper_source_delta_reconcile_contract(material)

    material = _op02()
    material["source_delta_rows"][1]["helper_snapshot_refs"] = dict(op.P7_R54_OPERATION_CURRENT_REFS)
    with pytest.raises(ValueError):
        op.assert_p7_r54_op02_historical_helper_source_delta_reconcile_contract(material)

    material = _op02()
    material["source_delta_rows"] = material["source_delta_rows"][:1]
    material["source_delta_row_count"] = 1
    with pytest.raises(ValueError):
        op.assert_p7_r54_op02_historical_helper_source_delta_reconcile_contract(material)


def test_r54_op03_intakes_r55_hold_without_starting_review_p6_p8_or_release() -> None:
    material = _op03()

    assert material["schema_version"] == op.P7_R54_OPERATION_R55_HOLD_INTAKE_SCHEMA_VERSION
    assert set(material) == set(op.P7_R54_OPERATION_R55_HOLD_INTAKE_REQUIRED_FIELD_REFS)
    assert material["policy_section"] == op.P7_R54_OP03_STEP_REF
    assert material["operation_step_ref"] == op.P7_R54_OP03_STEP_REF
    assert material["op02_schema_version"] == op.P7_R54_OPERATION_HISTORICAL_HELPER_SOURCE_DELTA_RECONCILE_SCHEMA_VERSION
    assert material["op02_next_required_step"] == op.P7_R54_OP03_STEP_REF
    assert material["operation_current_refs"] == op.P7_R54_OPERATION_CURRENT_REFS
    assert material["source_delta_row_refs"] == list(op.P7_R54_SOURCE_DELTA_ROW_REFS)
    assert material["source_delta_row_count"] == 2
    assert material["op02_source_delta_rows_materialized"] is True

    assert material["r55_decision_material_schema_version"] == r55.P7_R55_R52_REINTAKE_DECISION_MATERIALIZATION_SCHEMA_VERSION
    assert material["r55_decision_ref"] == "R55_R52_RETURN_TO_R54_ACTUAL_REVIEW_REQUIRED"
    assert material["r55_decision_ref"] == r55.P7_R55_DEFAULT_R52_REINTAKE_DECISION_REF
    assert material["r55_decision_status"] == r55.P7_R55_DEFAULT_DECISION_STATUS_REF
    assert material["r55_next_required_step"] == "R54_actual_local_only_human_review_operation_required_before_R52_reintake"
    assert material["r55_existing_r52_decision_equivalent"] == r55.P7_R55_DEFAULT_R52_EXISTING_DECISION_EQUIVALENT_REF
    assert material["r55_hold_intake_status_ref"] == op.P7_R54_R55_HOLD_INTAKE_STATUS_REF
    assert material["r55_actual_review_evidence_gap_status_ref"] == r55.P7_R55_ACTUAL_REVIEW_EVIDENCE_MISSING_GAP_STATUS_REF
    assert material["r55_actual_review_evidence_complete"] is False
    assert material["required_case_count"] == 24
    assert material["rating_row_count"] == 0
    assert material["question_observation_row_count"] == 0
    assert material["disposal_verified"] is False
    assert material["missing_evidence_refs"] == list(r55.P7_R55_DEFAULT_MISSING_EVIDENCE_REFS)
    assert material["missing_evidence_ref_count"] == len(r55.P7_R55_DEFAULT_MISSING_EVIDENCE_REFS)
    assert material["r54_review_operation_state_ref"] == r55.P7_R55_R54_DEFAULT_REVIEW_OPERATION_STATE_REF
    assert material["p5_decision_status_ref"] == r55.P7_R55_P5_DECISION_STATUS_NOT_REVIEWED_REF
    assert material["p5_decision_candidate_ref"] == r55.P7_R55_R54_DEFAULT_P5_DECISION_CANDIDATE_REF
    assert material["p6_hold"] is True
    assert material["p8_hold"] is True
    assert material["release_hold"] is True
    assert material["r54_actual_local_only_human_review_operation_required_before_r52_reintake"] is True
    assert material["actual_review_evidence_complete"] is False
    assert material["source_delta_rows_materialized_here"] is False

    assert tuple(material["implemented_steps"]) == op.P7_R54_OP03_IMPLEMENTED_STEPS
    assert tuple(material["not_yet_implemented_steps"]) == op.P7_R54_OP03_NOT_YET_IMPLEMENTED_STEPS
    assert material["next_required_step"] == op.P7_R54_OP04_NEXT_REQUIRED_STEP_REF
    assert material["body_full_generation_blocked_until_preflight"] is True
    assert material["human_review_completion_claim_blocked_here"] is True
    assert material["p6_p8_release_promotion_blocked_here"] is True
    assert material["actual_human_review_run_here"] is False
    assert material["body_full_packet_generated_here"] is False
    assert material["actual_rating_rows_materialized_here"] is False
    assert material["actual_question_need_observation_rows_materialized_here"] is False
    assert material["p6_limited_human_readfeel_start_allowed"] is False
    assert material["p8_start_allowed"] is False
    assert material["release_allowed"] is False
    assert material["question_text_included"] is False
    assert material["draft_question_text_included"] is False
    assert material["local_path_included"] is False

    _assert_body_free_no_promotion(material)


@pytest.mark.parametrize(
    "key,value",
    [
        ("op02_source_delta_rows_materialized", False),
        ("r55_decision_ref", "R55_R52_P5_CONFIRMED_CANDIDATE_ONLY"),
        ("r55_decision_status", "GO"),
        ("r55_next_required_step", "p8_start"),
        ("r55_actual_review_evidence_complete", True),
        ("required_case_count", 0),
        ("rating_row_count", 1),
        ("question_observation_row_count", 1),
        ("disposal_verified", True),
        ("p6_hold", False),
        ("p8_hold", False),
        ("release_hold", False),
        ("r54_actual_local_only_human_review_operation_required_before_r52_reintake", False),
        ("actual_review_evidence_complete", True),
        ("source_delta_rows_materialized_here", True),
        ("body_full_generation_blocked_until_preflight", False),
        ("human_review_completion_claim_blocked_here", False),
        ("p6_p8_release_promotion_blocked_here", False),
        ("actual_human_review_run_here", True),
        ("body_full_packet_generated_here", True),
        ("actual_rating_rows_materialized_here", True),
        ("actual_question_need_observation_rows_materialized_here", True),
        ("p6_limited_human_readfeel_start_allowed", True),
        ("p8_start_allowed", True),
        ("release_allowed", True),
        ("question_text_included", True),
        ("draft_question_text_included", True),
        ("local_path_included", True),
    ],
)
def test_r54_op03_rejects_r55_hold_mutation_review_claim_promotion_or_body_boundary_mutation(
    key: str,
    value: object,
) -> None:
    material = _op03()
    material[key] = value
    with pytest.raises(ValueError):
        op.assert_p7_r54_op03_r55_hold_intake_contract(material)
