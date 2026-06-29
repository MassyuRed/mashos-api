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
    '"actual_question_need_observation_rows_materialized_here": true', '"actual_disposal_receipt_materialized_here": true',
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


@lru_cache(maxsize=1)
def _cached_op11_ready() -> tuple[dict[str, object]]:
    material = op.build_p7_r54_op11_sanitized_review_result_capture(
        actual_human_review_operation_state_capture=_op10_completed(), reviewer_selection_rows=_valid_selection_rows()
    )
    assert op.assert_p7_r54_op11_sanitized_review_result_capture_contract(material) is True
    return (material,)


def _op11_ready() -> dict[str, object]:
    return deepcopy(_cached_op11_ready()[0])


@lru_cache(maxsize=1)
def _cached_op12_ready() -> tuple[dict[str, object]]:
    material = op.build_p7_r54_op12_rating_row_normalization(sanitized_review_result_capture=_op11_ready())
    assert op.assert_p7_r54_op12_rating_row_normalization_contract(material) is True
    return (material,)


def _op12_ready() -> dict[str, object]:
    return deepcopy(_cached_op12_ready()[0])


def _op11_with_modified_first_row(**updates: object) -> dict[str, object]:
    rows = _valid_selection_rows()
    rows[0].update(updates)
    material = op.build_p7_r54_op11_sanitized_review_result_capture(
        actual_human_review_operation_state_capture=_op10_completed(), reviewer_selection_rows=rows
    )
    assert op.assert_p7_r54_op11_sanitized_review_result_capture_contract(material) is True
    return material


def test_r54_op12_default_rating_normalization_fails_closed_when_op11_is_not_ready() -> None:
    material = op.build_p7_r54_op12_rating_row_normalization()

    assert material["schema_version"] == op.P7_R54_OPERATION_RATING_ROW_NORMALIZATION_SCHEMA_VERSION
    assert set(material) == set(op.P7_R54_OPERATION_RATING_ROW_NORMALIZATION_REQUIRED_FIELD_REFS)
    assert material["policy_section"] == op.P7_R54_OP12_STEP_REF
    assert material["op11_rating_row_normalization_allowed_next"] is False
    assert material["rating_row_normalization_status"] == op.P7_R54_OP12_RATING_NORMALIZATION_BLOCKED_STATUS_REF
    assert material["rating_row_count"] == 0
    assert material["rating_rows_normalized_here"] is False
    assert material["actual_rating_rows_materialized_here"] is False
    assert material["readfeel_blocker_execution_blocker_ingestion_allowed_next"] is False
    assert material["next_required_step"] == op.P7_R54_OP12_BLOCKED_NEXT_REQUIRED_STEP_REF
    assert material["execution_blocker_ids"]
    _assert_body_free_no_promotion(material)


def test_r54_op12_rating_rows_normalize_twenty_four_bodyfree_rows() -> None:
    material = _op12_ready()

    assert material["schema_version"] == op.P7_R54_OPERATION_RATING_ROW_NORMALIZATION_SCHEMA_VERSION
    assert set(material) == set(op.P7_R54_OPERATION_RATING_ROW_NORMALIZATION_REQUIRED_FIELD_REFS)
    assert material["op11_schema_version"] == op.P7_R54_OPERATION_SANITIZED_REVIEW_RESULT_CAPTURE_SCHEMA_VERSION
    assert material["op11_next_required_step"] == op.P7_R54_OP12_STEP_REF
    assert material["op11_sanitized_review_result_capture_status"] == op.P7_R54_OP11_SANITIZED_CAPTURE_READY_STATUS_REF
    assert material["op11_rating_row_normalization_allowed_next"] is True
    assert material["rating_row_normalization_status"] == op.P7_R54_OP12_RATING_NORMALIZATION_READY_STATUS_REF
    assert material["rating_row_normalization_ref"] == op.P7_R54_OP12_RATING_ROW_NORMALIZATION_REF
    assert material["rating_row_normalization_reason_refs"] == [op.P7_R54_OP12_READY_REASON_REF]
    assert material["execution_blocker_ids"] == []
    assert material["rating_row_count"] == 24
    assert material["rating_row_refs_unique"] is True
    assert material["rating_case_ref_sets_match_review_capture"] is True
    assert material["verdict_counts"] == {"PASS": 24, "YELLOW": 0, "REPAIR_REQUIRED": 0, "RED": 0}
    assert material["axis_score_averages"] == {axis: 1.0 for axis in op.P7_R54_OP09_RATING_AXIS_REFS}
    assert material["rating_rows_are_bodyfree"] is True
    assert material["all_required_rating_rows_present"] is True
    assert material["rating_rows_normalized_here"] is True
    assert material["actual_rating_rows_materialized_here"] is True
    assert material["actual_blocker_rows_materialized_here"] is False
    assert material["question_observation_row_count"] == 0
    assert tuple(material["implemented_steps"]) == op.P7_R54_OP12_IMPLEMENTED_STEPS
    assert tuple(material["not_yet_implemented_steps"]) == op.P7_R54_OP12_NOT_YET_IMPLEMENTED_STEPS
    assert material["next_required_step"] == op.P7_R54_OP13_STEP_REF
    first_row = material["rating_rows"][0]
    assert set(first_row) == set(op.P7_R54_OPERATION_RATING_ROW_REQUIRED_FIELD_REFS)
    assert first_row["schema_version"] == op.P7_R54_OPERATION_RATING_ROW_SCHEMA_VERSION
    assert first_row["rating_row_is_bodyfree"] is True
    assert first_row["body_free"] is True
    assert first_row["axis_score_count"] == 6
    assert first_row["below_target_axis_count"] == 0
    _assert_body_free_no_promotion(material)


def test_r54_op12_blocks_pass_verdict_with_readfeel_blocker_before_op13() -> None:
    op11 = _op11_with_modified_first_row(blocker_ids=["p5_history_connection_too_generic"])
    material = op.build_p7_r54_op12_rating_row_normalization(sanitized_review_result_capture=op11)

    assert material["rating_row_normalization_status"] == op.P7_R54_OP12_RATING_NORMALIZATION_BLOCKED_STATUS_REF
    assert material["rating_rows"] == []
    assert material["rating_row_count"] == 0
    assert "rating_row_verdict_blocker_consistency_failed" in material["execution_blocker_ids"]
    assert material["pass_with_any_blocker_detected"] is True
    assert material["rating_consistency_issue_rows"][0]["issue_id"] == "r54_op12_pass_with_any_blocker_detected"
    assert material["readfeel_blocker_execution_blocker_ingestion_allowed_next"] is False
    _assert_body_free_no_promotion(material)


def test_r54_op13_default_blocker_ingestion_fails_closed_when_op12_is_not_ready() -> None:
    material = op.build_p7_r54_op13_readfeel_blocker_execution_blocker_ingestion()

    assert material["schema_version"] == op.P7_R54_OPERATION_READFEEL_BLOCKER_EXECUTION_BLOCKER_INGESTION_SCHEMA_VERSION
    assert set(material) == set(op.P7_R54_OPERATION_READFEEL_BLOCKER_EXECUTION_BLOCKER_INGESTION_REQUIRED_FIELD_REFS)
    assert material["policy_section"] == op.P7_R54_OP13_STEP_REF
    assert material["op12_blocker_ingestion_allowed_next"] is False
    assert material["blocker_ingestion_status"] == op.P7_R54_OP13_BLOCKER_INGESTION_BLOCKED_STATUS_REF
    assert material["readfeel_blocker_rows"] == []
    assert material["execution_blocker_rows"]
    assert material["readfeel_blocker_row_builder_ready"] is False
    assert material["execution_blocker_row_builder_ready"] is False
    assert material["actual_blocker_rows_materialized_here"] is False
    assert material["next_required_step"] == op.P7_R54_OP13_BLOCKED_NEXT_REQUIRED_STEP_REF
    _assert_body_free_no_promotion(material)


def test_r54_op13_ingests_zero_blockers_from_all_pass_rating_rows_and_points_to_op14() -> None:
    material = op.build_p7_r54_op13_readfeel_blocker_execution_blocker_ingestion(rating_row_normalization=_op12_ready())

    assert material["schema_version"] == op.P7_R54_OPERATION_READFEEL_BLOCKER_EXECUTION_BLOCKER_INGESTION_SCHEMA_VERSION
    assert set(material) == set(op.P7_R54_OPERATION_READFEEL_BLOCKER_EXECUTION_BLOCKER_INGESTION_REQUIRED_FIELD_REFS)
    assert material["op12_schema_version"] == op.P7_R54_OPERATION_RATING_ROW_NORMALIZATION_SCHEMA_VERSION
    assert material["op12_next_required_step"] == op.P7_R54_OP13_STEP_REF
    assert material["blocker_ingestion_status"] == op.P7_R54_OP13_BLOCKER_INGESTION_READY_STATUS_REF
    assert material["blocker_ingestion_reason_refs"] == [op.P7_R54_OP13_READY_REASON_REF]
    assert material["execution_blocker_ids"] == []
    assert material["rating_row_count"] == 24
    assert material["readfeel_blocker_rows"] == []
    assert material["open_readfeel_blocker_count"] == 0
    assert material["execution_blocker_rows"] == []
    assert material["readfeel_and_execution_blockers_separated"] is True
    assert material["execution_blockers_do_not_assign_readfeel_verdict"] is True
    assert material["rating_rows_preserved_from_op12"] is True
    assert material["actual_blocker_rows_materialized_here"] is True
    assert material["question_observation_row_count"] == 0
    assert tuple(material["implemented_steps"]) == op.P7_R54_OP13_IMPLEMENTED_STEPS
    assert tuple(material["not_yet_implemented_steps"]) == op.P7_R54_OP13_NOT_YET_IMPLEMENTED_STEPS
    assert material["next_required_step"] == "R54-OP-14_question_need_observation_normalization"
    _assert_body_free_no_promotion(material)


def test_r54_op13_separates_readfeel_blockers_from_execution_blockers() -> None:
    op11 = _op11_with_modified_first_row(
        verdict="REPAIR_REQUIRED",
        sanitized_reason_ids=["p5_history_scope_overclaim_detected_bodyfree"],
        blocker_ids=["p5_history_scope_overclaim"],
        repair_required_refs=["p5_surface_repair_required"],
    )
    op12 = op.build_p7_r54_op12_rating_row_normalization(sanitized_review_result_capture=op11)
    assert op12["rating_row_normalization_status"] == op.P7_R54_OP12_RATING_NORMALIZATION_READY_STATUS_REF
    material = op.build_p7_r54_op13_readfeel_blocker_execution_blocker_ingestion(rating_row_normalization=op12)

    assert material["blocker_ingestion_status"] == op.P7_R54_OP13_BLOCKER_INGESTION_READY_STATUS_REF
    assert material["readfeel_blocker_row_count"] == 1
    assert material["readfeel_blocker_counts"] == {"p5_history_scope_overclaim": 1}
    assert material["open_readfeel_blocker_count"] == 1
    assert material["execution_blocker_ids"] == []
    row = material["readfeel_blocker_rows"][0]
    assert set(row) == set(op.P7_R54_OPERATION_READFEEL_BLOCKER_ROW_REQUIRED_FIELD_REFS)
    assert row["schema_version"] == op.P7_R54_OPERATION_READFEEL_BLOCKER_ROW_SCHEMA_VERSION
    assert row["blocker_kind_ref"] == op.P7_R54_OP13_READFEEL_BLOCKER_KIND_REF
    assert row["readfeel_blocker_id"] == "p5_history_scope_overclaim"
    assert row["blocker_status_ref"] == "open"
    _assert_body_free_no_promotion(material)


def test_r54_op12_op13_bodyfree_aliases_match_primary_builders() -> None:
    op12 = op.build_p7_r54_operation_rating_row_normalization_bodyfree(sanitized_review_result_capture=_op11_ready())
    op13 = op.build_p7_r54_operation_readfeel_blocker_execution_blocker_ingestion_bodyfree(rating_row_normalization=op12)

    assert op.assert_p7_r54_operation_rating_row_normalization_bodyfree_contract(op12) is True
    assert op.assert_p7_r54_operation_readfeel_blocker_execution_blocker_ingestion_bodyfree_contract(op13) is True
    assert op12["rating_row_normalization_status"] == op.P7_R54_OP12_RATING_NORMALIZATION_READY_STATUS_REF
    assert op13["blocker_ingestion_status"] == op.P7_R54_OP13_BLOCKER_INGESTION_READY_STATUS_REF
    _assert_body_free_no_promotion(op12)
    _assert_body_free_no_promotion(op13)


@pytest.mark.parametrize(
    "builder,asserter",
    [
        (op.build_p7_r54_op12_rating_row_normalization, op.assert_p7_r54_op12_rating_row_normalization_contract),
        (op.build_p7_r54_op13_readfeel_blocker_execution_blocker_ingestion, op.assert_p7_r54_op13_readfeel_blocker_execution_blocker_ingestion_contract),
    ],
)
def test_r54_op12_op13_contracts_reject_api_db_rn_runtime_mutation_flags(builder, asserter) -> None:
    material = builder()
    for key in ("api_changed", "db_changed", "rn_changed", "runtime_changed", "release_allowed", "p8_start_allowed"):
        broken = deepcopy(material)
        broken[key] = True
        with pytest.raises(ValueError):
            asserter(broken)
