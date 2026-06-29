# -*- coding: utf-8 -*-
from __future__ import annotations

import json
from copy import deepcopy
from functools import lru_cache

import pytest

import emlis_ai_p7_r54_actual_local_review_operation_reentry_20260625 as op
from emlis_ai_p7_r51_p5_human_blind_qa_actual_local_manual_run import P7_R51_REQUIRED_CASE_COUNT


FORBIDDEN_DUMP_TOKENS = (
    '"raw_input":', '"raw_answer":', '"comment_text":', '"comment_text_body":',
    '"returned_emlis_surface":', '"current_input_review_surface":', '"bounded_owned_history_review_surface":',
    '"reviewer_free_text":', '"reviewer_note":', '"reviewer_notes":', '"question_text": "',
    '"draft_question_text": "', '"question_body":', '"local_absolute_path":', '"local_directory_path":',
    '"body_content_hash":', '"packet_content_hash":', '"terminal_output": "', '"stdout":', '"stderr":', '"traceback":',
)
FORBIDDEN_TRUE_TOKENS = (
    '"api_changed": true', '"db_changed": true', '"rn_changed": true', '"runtime_changed": true',
    '"api_route_changed": true', '"db_schema_changed": true', '"rn_visible_contract_changed": true',
    '"public_response_top_level_key_added": true', '"release_allowed": true', '"p7_complete": true',
    '"p8_start_allowed": true', '"p6_limited_human_readfeel_start_allowed": true',
    '"question_trigger_logic_implemented": true', '"p8_question_implementation_spec_finalized_here": true',
    '"actual_human_review_run_here": true', '"actual_manual_review_run_here": true',
    '"body_full_packet_generated_here": true', '"actual_body_full_packet_generated_here": true',
    '"actual_disposal_receipt_materialized_here": true',
    '"body_full_packet_export_allowed": true', '"body_full_packet_zip_inclusion_allowed": true',
    '"reviewer_notes_export_allowed": true', '"local_path_included": true', '"question_text_included": true',
    '"draft_question_text_included": true',
)


def _assert_body_free_no_promotion(material: dict[str, object]) -> None:
    dumped = json.dumps(material, ensure_ascii=False, sort_keys=True).lower()
    for forbidden in FORBIDDEN_DUMP_TOKENS:
        assert forbidden not in dumped
    for forbidden in FORBIDDEN_TRUE_TOKENS:
        assert forbidden not in dumped


@lru_cache(maxsize=1)
def _cached_op04_ready() -> tuple[dict[str, object]]:
    material = op.build_p7_r54_op04_local_only_preflight(
        local_review_root_presence_ref=op.P7_R54_OP04_LOCAL_REVIEW_ROOT_READY_REF,
        explicit_allow_token_ref=op.P7_R54_OP04_EXPLICIT_ALLOW_TOKEN_REF,
        purge_plan_ref=op.P7_R54_OP04_PURGE_PLAN_READY_REF,
        retention_policy_ref=op.P7_R54_OP04_RETENTION_POLICY_READY_REF,
        export_denylist_policy_ref=op.P7_R54_OP04_EXPORT_DENYLIST_POLICY_READY_REF,
    )
    assert op.assert_p7_r54_op04_local_only_preflight_contract(material) is True
    return (material,)


def _op04_ready() -> dict[str, object]:
    return deepcopy(_cached_op04_ready()[0])


@lru_cache(maxsize=1)
def _cached_op05_ready() -> tuple[dict[str, object]]:
    material = op.build_p7_r54_op05_24_case_manifest_freeze(local_only_preflight=_op04_ready())
    assert op.assert_p7_r54_op05_24_case_manifest_freeze_contract(material) is True
    return (material,)


def _op05_ready() -> dict[str, object]:
    return deepcopy(_cached_op05_ready()[0])


@lru_cache(maxsize=1)
def _cached_op06_ready() -> tuple[dict[str, object]]:
    material = op.build_p7_r54_op06_local_only_body_full_packet_generation_request(case_manifest_freeze=_op05_ready())
    assert op.assert_p7_r54_op06_local_only_body_full_packet_generation_request_contract(material) is True
    return (material,)


def _op06_ready() -> dict[str, object]:
    return deepcopy(_cached_op06_ready()[0])


@lru_cache(maxsize=1)
def _cached_op07_ready() -> tuple[dict[str, object]]:
    op06 = _op06_ready()
    material = op.build_p7_r54_op07_packet_generation_local_operation(
        body_full_packet_generation_request=op06,
        local_operation_receipt_ref=op.P7_R54_OP07_LOCAL_OPERATION_RECEIPT_REF,
        declared_generated_packet_ref_ids=op06["requested_packet_ref_ids"],
    )
    assert op.assert_p7_r54_op07_packet_generation_local_operation_contract(material) is True
    return (material,)


def _op07_ready() -> dict[str, object]:
    return deepcopy(_cached_op07_ready()[0])


@lru_cache(maxsize=1)
def _cached_op08_ready() -> tuple[dict[str, object]]:
    material = op.build_p7_r54_op08_packet_completeness_export_denylist_scan(packet_generation_local_operation=_op07_ready())
    assert op.assert_p7_r54_op08_packet_completeness_export_denylist_scan_contract(material) is True
    return (material,)


def _op08_ready() -> dict[str, object]:
    return deepcopy(_cached_op08_ready()[0])


@lru_cache(maxsize=1)
def _cached_op09_ready() -> tuple[dict[str, object]]:
    material = op.build_p7_r54_op09_reviewer_instruction_rating_form_freeze(packet_completeness_export_denylist_scan=_op08_ready())
    assert op.assert_p7_r54_op09_reviewer_instruction_rating_form_freeze_contract(material) is True
    return (material,)


def _op09_ready() -> dict[str, object]:
    return deepcopy(_cached_op09_ready()[0])


def _selection_row_refs() -> list[str]:
    return [f"r54op11-sanitized-review-row-{index:03d}" for index in range(1, P7_R51_REQUIRED_CASE_COUNT + 1)]


@lru_cache(maxsize=1)
def _cached_op10_completed() -> tuple[dict[str, object]]:
    op08 = _op08_ready()
    material = op.build_p7_r54_op10_actual_human_review_operation_state_capture(
        reviewer_instruction_rating_form_freeze=_op09_ready(),
        review_operation_status_ref=op.P7_R54_OP10_REVIEW_COMPLETED_SELECTIONS_CAPTURED_STATUS_REF,
        reviewer_assignment_ref="r54_local_only_human_reviewer_assigned_bodyfree",
        reviewer_ref_ids=["reviewer-pseudonymous-r54-a"],
        review_completion_receipt_ref="r54_local_only_human_review_completed_receipt_bodyfree",
        completed_packet_ref_ids=op08["declared_packet_ref_ids"],
        completed_selection_row_refs=_selection_row_refs(),
    )
    assert op.assert_p7_r54_op10_actual_human_review_operation_state_capture_contract(material) is True
    return (material,)


def _op10_completed() -> dict[str, object]:
    return deepcopy(_cached_op10_completed()[0])


def _valid_selection_rows() -> list[dict[str, object]]:
    op06 = _op06_ready()
    rows: list[dict[str, object]] = []
    flags = {flag: False for flag in op.P7_R54_OP09_PLAN_CANDIDATE_FLAG_REFS}
    for source, row_ref in zip(op06["packet_generation_request_rows"], _selection_row_refs(), strict=True):
        rows.append({
            "review_result_row_ref": row_ref,
            "packet_ref_id": source["packet_ref_id"],
            "blind_case_id": source["blind_case_id"],
            "case_ref_id": source["case_ref_id"],
            "family": source["family"],
            "case_role": source["case_role"],
            "reviewer_ref": "reviewer-pseudonymous-r54-a",
            "reviewed_at_ref": "coarse_reviewed_at_ref_20260625",
            "axis_scores": {axis: 1.0 for axis in op.P7_R54_OP09_RATING_AXIS_REFS},
            "verdict": "PASS",
            "sanitized_reason_ids": ["p5_history_line_read_naturally_bodyfree"],
            "blocker_ids": [],
            "question_need_primary_class": "no_question_needed_emlis_can_observe",
            "ambiguity_kind_refs": ["no_material_ambiguity"],
            "one_question_fit_ref": "not_needed",
            "repair_required_refs": ["no_repair_required"],
            "plan_candidate_flags": dict(flags),
        })
    return rows


def _build_op11_from_rows(rows: list[dict[str, object]]) -> dict[str, object]:
    material = op.build_p7_r54_op11_sanitized_review_result_capture(
        actual_human_review_operation_state_capture=_op10_completed(), reviewer_selection_rows=rows
    )
    assert op.assert_p7_r54_op11_sanitized_review_result_capture_contract(material) is True
    return material


@lru_cache(maxsize=1)
def _cached_op11_ready() -> tuple[dict[str, object]]:
    return (_build_op11_from_rows(_valid_selection_rows()),)


def _op11_ready() -> dict[str, object]:
    return deepcopy(_cached_op11_ready()[0])


def _op11_with_modified_first_row(**updates: object) -> dict[str, object]:
    rows = _valid_selection_rows()
    rows[0].update(updates)
    return _build_op11_from_rows(rows)


@lru_cache(maxsize=1)
def _cached_op12_ready() -> tuple[dict[str, object]]:
    material = op.build_p7_r54_op12_rating_row_normalization(sanitized_review_result_capture=_op11_ready())
    assert op.assert_p7_r54_op12_rating_row_normalization_contract(material) is True
    return (material,)


def _op12_ready() -> dict[str, object]:
    return deepcopy(_cached_op12_ready()[0])


@lru_cache(maxsize=1)
def _cached_op13_ready() -> tuple[dict[str, object]]:
    material = op.build_p7_r54_op13_readfeel_blocker_execution_blocker_ingestion(rating_row_normalization=_op12_ready())
    assert op.assert_p7_r54_op13_readfeel_blocker_execution_blocker_ingestion_contract(material) is True
    return (material,)


def _op13_ready() -> dict[str, object]:
    return deepcopy(_cached_op13_ready()[0])


@lru_cache(maxsize=1)
def _cached_op14_ready() -> tuple[dict[str, object]]:
    material = op.build_p7_r54_op14_question_need_observation_normalization(
        blocker_ingestion=_op13_ready(),
        rating_row_normalization=_op12_ready(),
        sanitized_review_result_capture=_op11_ready(),
    )
    assert op.assert_p7_r54_op14_question_need_observation_normalization_contract(material) is True
    return (material,)


def _op14_ready() -> dict[str, object]:
    return deepcopy(_cached_op14_ready()[0])


def test_r54_op14_default_question_observation_normalization_fails_closed_when_prereqs_are_not_ready() -> None:
    material = op.build_p7_r54_op14_question_need_observation_normalization()

    assert material["schema_version"] == op.P7_R54_OPERATION_QUESTION_NEED_OBSERVATION_NORMALIZATION_SCHEMA_VERSION
    assert set(material) == set(op.P7_R54_OPERATION_QUESTION_NEED_OBSERVATION_NORMALIZATION_REQUIRED_FIELD_REFS)
    assert material["policy_section"] == op.P7_R54_OP14_STEP_REF
    assert material["op13_question_observation_normalization_allowed_next"] is False
    assert material["question_observation_normalization_status"] == op.P7_R54_OP14_QUESTION_OBSERVATION_NORMALIZATION_BLOCKED_STATUS_REF
    assert material["question_observation_rows"] == []
    assert material["question_observation_row_count"] == 0
    assert material["actual_question_need_observation_rows_materialized_here"] is False
    assert material["rating_question_consistency_guard_allowed_next"] is False
    assert material["next_required_step"] == op.P7_R54_OP14_BLOCKED_NEXT_REQUIRED_STEP_REF
    assert material["execution_blocker_ids"]
    _assert_body_free_no_promotion(material)


def test_r54_op14_normalizes_twenty_four_question_need_observation_rows_without_question_text() -> None:
    material = _op14_ready()

    assert material["schema_version"] == op.P7_R54_OPERATION_QUESTION_NEED_OBSERVATION_NORMALIZATION_SCHEMA_VERSION
    assert set(material) == set(op.P7_R54_OPERATION_QUESTION_NEED_OBSERVATION_NORMALIZATION_REQUIRED_FIELD_REFS)
    assert material["op13_schema_version"] == op.P7_R54_OPERATION_READFEEL_BLOCKER_EXECUTION_BLOCKER_INGESTION_SCHEMA_VERSION
    assert material["op13_next_required_step"] == op.P7_R54_OP14_STEP_REF
    assert material["op13_question_observation_normalization_allowed_next"] is True
    assert material["question_observation_normalization_status"] == op.P7_R54_OP14_QUESTION_OBSERVATION_NORMALIZATION_READY_STATUS_REF
    assert material["question_observation_normalization_ref"] == op.P7_R54_OP14_QUESTION_OBSERVATION_NORMALIZATION_REF
    assert material["question_observation_row_count"] == 24
    assert material["question_observation_row_refs_unique"] is True
    assert material["row_case_ref_sets_match_review_capture"] is True
    assert material["row_case_ref_sets_match_rating_rows"] is True
    assert material["all_required_question_need_observation_rows_present"] is True
    assert material["primary_class_ambiguity_one_question_fit_are_canonical_refs"] is True
    assert material["question_text_absent_for_all_rows"] is True
    assert material["draft_question_text_absent_for_all_rows"] is True
    assert material["question_text_or_draft_text_saved_here"] is False
    assert material["p8_question_implementation_spec_finalized_here"] is False
    assert material["question_trigger_logic_implemented_here"] is False
    assert material["api_db_rn_response_key_changed_here"] is False
    assert material["actual_rating_rows_materialized_here"] is True
    assert material["actual_blocker_rows_materialized_here"] is True
    assert material["actual_question_need_observation_rows_materialized_here"] is True
    assert material["actual_review_evidence_complete"] is False
    assert tuple(material["implemented_steps"]) == op.P7_R54_OP14_IMPLEMENTED_STEPS
    assert tuple(material["not_yet_implemented_steps"]) == op.P7_R54_OP14_NOT_YET_IMPLEMENTED_STEPS
    assert material["next_required_step"] == op.P7_R54_OP15_STEP_REF
    first_row = material["question_observation_rows"][0]
    assert set(first_row) == set(op.P7_R54_OPERATION_QUESTION_NEED_OBSERVATION_ROW_REQUIRED_FIELD_REFS)
    assert first_row["schema_version"] == op.P7_R54_OPERATION_QUESTION_NEED_OBSERVATION_ROW_SCHEMA_VERSION
    assert first_row["question_observation_row_is_bodyfree"] is True
    assert first_row["question_text_included"] is False
    assert first_row["draft_question_text_included"] is False
    assert first_row["p8_material_candidate_allowed"] is False
    _assert_body_free_no_promotion(material)


def test_r54_op14_keeps_plus_question_candidate_as_p8_material_candidate_without_implementing_p8() -> None:
    op11 = _op11_with_modified_first_row(
        question_need_primary_class="plus_single_question_candidate_later",
        ambiguity_kind_refs=["missing_target"],
        one_question_fit_ref="fits_one_question",
        repair_required_refs=["no_repair_required"],
    )
    op12 = op.build_p7_r54_op12_rating_row_normalization(sanitized_review_result_capture=op11)
    op13 = op.build_p7_r54_op13_readfeel_blocker_execution_blocker_ingestion(rating_row_normalization=op12)
    material = op.build_p7_r54_op14_question_need_observation_normalization(
        blocker_ingestion=op13, rating_row_normalization=op12, sanitized_review_result_capture=op11
    )

    assert material["question_observation_normalization_status"] == op.P7_R54_OP14_QUESTION_OBSERVATION_NORMALIZATION_READY_STATUS_REF
    assert material["p8_material_candidate_row_count"] == 1
    row = material["question_observation_rows"][0]
    assert row["question_need_primary_class"] == "plus_single_question_candidate_later"
    assert row["p8_material_candidate_allowed"] is True
    assert row["plan_candidate_flags"]["plus_single_question_candidate_later"] is True
    assert row["plan_candidate_flags"]["p8_design_material_candidate"] is True
    assert row["plan_candidate_flags"]["p8_implementation_spec_finalized_here"] is False
    assert material["p8_start_allowed"] is False
    _assert_body_free_no_promotion(material)


def test_r54_op15_default_consistency_guard_fails_closed_when_op14_is_not_ready() -> None:
    material = op.build_p7_r54_op15_rating_question_consistency_guard()

    assert material["schema_version"] == op.P7_R54_OPERATION_RATING_QUESTION_CONSISTENCY_GUARD_SCHEMA_VERSION
    assert set(material) == set(op.P7_R54_OPERATION_RATING_QUESTION_CONSISTENCY_GUARD_REQUIRED_FIELD_REFS)
    assert material["policy_section"] == op.P7_R54_OP15_STEP_REF
    assert material["op14_consistency_guard_allowed_next"] is False
    assert material["rating_question_consistency_guard_status"] == op.P7_R54_OP15_CONSISTENCY_GUARD_BLOCKED_STATUS_REF
    assert material["rating_question_consistency_issue_rows"] == []
    assert material["ready_for_pause_abort_expiration_protocol"] is False
    assert material["next_required_step"] == op.P7_R54_OP15_BLOCKED_NEXT_REQUIRED_STEP_REF
    assert material["execution_blocker_ids"]
    _assert_body_free_no_promotion(material)


def test_r54_op15_passes_all_pass_no_question_needed_consistency_and_points_to_op16() -> None:
    material = op.build_p7_r54_op15_rating_question_consistency_guard(
        question_need_observation_normalization=_op14_ready(), rating_row_normalization=_op12_ready()
    )

    assert material["schema_version"] == op.P7_R54_OPERATION_RATING_QUESTION_CONSISTENCY_GUARD_SCHEMA_VERSION
    assert set(material) == set(op.P7_R54_OPERATION_RATING_QUESTION_CONSISTENCY_GUARD_REQUIRED_FIELD_REFS)
    assert material["op14_schema_version"] == op.P7_R54_OPERATION_QUESTION_NEED_OBSERVATION_NORMALIZATION_SCHEMA_VERSION
    assert material["op14_next_required_step"] == op.P7_R54_OP15_STEP_REF
    assert material["op14_consistency_guard_allowed_next"] is True
    assert material["rating_question_consistency_guard_status"] == op.P7_R54_OP15_CONSISTENCY_GUARD_READY_STATUS_REF
    assert material["rating_question_consistency_guard_ref"] == op.P7_R54_OP15_CONSISTENCY_GUARD_REF
    assert material["execution_blocker_ids"] == []
    assert material["rating_row_count"] == 24
    assert material["question_observation_row_count"] == 24
    assert material["rating_question_case_ref_sets_match"] is True
    assert material["all_required_rating_and_question_rows_present"] is True
    assert material["consistency_issue_count"] == 0
    assert material["ready_for_pause_abort_expiration_protocol"] is True
    assert material["actual_question_need_observation_rows_materialized_here"] is True
    assert material["actual_review_evidence_complete"] is False
    assert tuple(material["implemented_steps"]) == op.P7_R54_OP15_IMPLEMENTED_STEPS
    assert tuple(material["not_yet_implemented_steps"]) == op.P7_R54_OP15_NOT_YET_IMPLEMENTED_STEPS
    assert material["next_required_step"] == "R54-OP-16_pause_abort_expiration_protocol"
    _assert_body_free_no_promotion(material)


def test_r54_op15_blocks_repair_required_with_no_question_needed_observation() -> None:
    op11 = _op11_with_modified_first_row(
        verdict="REPAIR_REQUIRED",
        sanitized_reason_ids=["p5_history_line_repair_required_bodyfree"],
        blocker_ids=["p5_history_connection_too_generic"],
        question_need_primary_class="no_question_needed_emlis_can_observe",
        repair_required_refs=["no_repair_required"],
    )
    op12 = op.build_p7_r54_op12_rating_row_normalization(sanitized_review_result_capture=op11)
    op13 = op.build_p7_r54_op13_readfeel_blocker_execution_blocker_ingestion(rating_row_normalization=op12)
    op14 = op.build_p7_r54_op14_question_need_observation_normalization(
        blocker_ingestion=op13, rating_row_normalization=op12, sanitized_review_result_capture=op11
    )
    material = op.build_p7_r54_op15_rating_question_consistency_guard(
        question_need_observation_normalization=op14, rating_row_normalization=op12
    )

    assert material["rating_question_consistency_guard_status"] == op.P7_R54_OP15_CONSISTENCY_GUARD_BLOCKED_STATUS_REF
    assert material["consistency_issue_count"] >= 1
    assert material["red_or_repair_with_no_question_needed_count"] == 1
    assert material["p5_confirmed_candidate_blocked_by_consistency_issues"] is True
    assert material["ready_for_pause_abort_expiration_protocol"] is False
    assert material["next_required_step"] == op.P7_R54_OP15_BLOCKED_NEXT_REQUIRED_STEP_REF
    assert material["rating_question_consistency_issue_rows"][0]["issue_id"] == "r54_op15_red_or_repair_with_no_question_needed_observation"
    _assert_body_free_no_promotion(material)


def test_r54_op15_blocks_pass_with_not_question_p5_surface_repair_observation() -> None:
    op11 = _op11_with_modified_first_row(
        question_need_primary_class="not_question_p5_surface_repair_required",
        ambiguity_kind_refs=["history_connection_basis_unclear"],
        one_question_fit_ref="repair_required_not_question",
        repair_required_refs=["p5_surface_repair_required"],
    )
    op12 = op.build_p7_r54_op12_rating_row_normalization(sanitized_review_result_capture=op11)
    op13 = op.build_p7_r54_op13_readfeel_blocker_execution_blocker_ingestion(rating_row_normalization=op12)
    op14 = op.build_p7_r54_op14_question_need_observation_normalization(
        blocker_ingestion=op13, rating_row_normalization=op12, sanitized_review_result_capture=op11
    )
    material = op.build_p7_r54_op15_rating_question_consistency_guard(
        question_need_observation_normalization=op14, rating_row_normalization=op12
    )

    assert op14["not_question_repair_required_count"] == 1
    assert op14["p8_material_candidate_row_count"] == 0
    assert material["rating_question_consistency_guard_status"] == op.P7_R54_OP15_CONSISTENCY_GUARD_BLOCKED_STATUS_REF
    assert material["pass_with_not_question_repair_required_count"] == 1
    assert material["rating_question_consistency_issue_rows"][0]["issue_id"] == "r54_op15_pass_with_not_question_repair_required"
    assert material["p8_material_candidates_do_not_hide_p5_repair_here"] is True
    _assert_body_free_no_promotion(material)


def test_r54_op14_op15_bodyfree_aliases_match_primary_builders() -> None:
    op14 = op.build_p7_r54_operation_question_need_observation_normalization_bodyfree(
        blocker_ingestion=_op13_ready(), rating_row_normalization=_op12_ready(), sanitized_review_result_capture=_op11_ready()
    )
    op15 = op.build_p7_r54_operation_rating_question_consistency_guard_bodyfree(
        question_need_observation_normalization=op14, rating_row_normalization=_op12_ready()
    )

    assert op.assert_p7_r54_operation_question_need_observation_normalization_bodyfree_contract(op14) is True
    assert op.assert_p7_r54_operation_rating_question_consistency_guard_bodyfree_contract(op15) is True
    assert op14["question_observation_normalization_status"] == op.P7_R54_OP14_QUESTION_OBSERVATION_NORMALIZATION_READY_STATUS_REF
    assert op15["rating_question_consistency_guard_status"] == op.P7_R54_OP15_CONSISTENCY_GUARD_READY_STATUS_REF
    _assert_body_free_no_promotion(op14)
    _assert_body_free_no_promotion(op15)


@pytest.mark.parametrize(
    "builder,asserter",
    [
        (op.build_p7_r54_op14_question_need_observation_normalization, op.assert_p7_r54_op14_question_need_observation_normalization_contract),
        (op.build_p7_r54_op15_rating_question_consistency_guard, op.assert_p7_r54_op15_rating_question_consistency_guard_contract),
    ],
)
def test_r54_op14_op15_contracts_reject_api_db_rn_runtime_mutation_flags(builder, asserter) -> None:
    material = builder()
    for key in ("api_changed", "db_changed", "rn_changed", "runtime_changed", "release_allowed", "p8_start_allowed"):
        broken = deepcopy(material)
        broken[key] = True
        with pytest.raises(ValueError):
            asserter(broken)
