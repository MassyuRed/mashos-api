# -*- coding: utf-8 -*-
from __future__ import annotations

import json
from copy import deepcopy
from functools import lru_cache

import pytest

import emlis_ai_p7_r54_actual_local_review_operation_reentry_20260625 as op
from emlis_ai_p7_r51_p5_human_blind_qa_actual_local_manual_run import P7_R51_REQUIRED_CASE_COUNT


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
    '"question_text": "',
    '"draft_question_text": "',
    '"question_body":',
    '"local_absolute_path":',
    '"local_directory_path":',
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
    '"actual_body_full_packet_generated_here": true',
    '"actual_rating_rows_materialized_here": true',
    '"actual_question_need_observation_rows_materialized_here": true',
    '"actual_disposal_receipt_materialized_here": true',
    '"body_full_packet_export_allowed": true',
    '"body_full_packet_zip_inclusion_allowed": true',
    '"reviewer_notes_export_allowed": true',
    '"local_path_included": true',
    '"question_text_included": true',
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
    material = op.build_p7_r54_op08_packet_completeness_export_denylist_scan(
        packet_generation_local_operation=_op07_ready()
    )
    assert op.assert_p7_r54_op08_packet_completeness_export_denylist_scan_contract(material) is True
    return (material,)


def _op08_ready() -> dict[str, object]:
    return deepcopy(_cached_op08_ready()[0])


@lru_cache(maxsize=1)
def _cached_op09_ready() -> tuple[dict[str, object]]:
    material = op.build_p7_r54_op09_reviewer_instruction_rating_form_freeze(
        packet_completeness_export_denylist_scan=_op08_ready()
    )
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
        rows.append(
            {
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
            }
        )
    return rows


@lru_cache(maxsize=1)
def _cached_op11_ready() -> tuple[dict[str, object]]:
    material = op.build_p7_r54_op11_sanitized_review_result_capture(
        actual_human_review_operation_state_capture=_op10_completed(),
        reviewer_selection_rows=_valid_selection_rows(),
    )
    assert op.assert_p7_r54_op11_sanitized_review_result_capture_contract(material) is True
    return (material,)


def _op11_ready() -> dict[str, object]:
    return deepcopy(_cached_op11_ready()[0])


def test_r54_op10_default_state_capture_fails_closed_when_op09_form_not_ready() -> None:
    material = op.build_p7_r54_op10_actual_human_review_operation_state_capture()

    assert material["schema_version"] == op.P7_R54_OPERATION_ACTUAL_HUMAN_REVIEW_OPERATION_STATE_CAPTURE_SCHEMA_VERSION
    assert set(material) == set(op.P7_R54_OPERATION_ACTUAL_HUMAN_REVIEW_OPERATION_STATE_CAPTURE_REQUIRED_FIELD_REFS)
    assert material["policy_section"] == op.P7_R54_OP10_STEP_REF
    assert material["operation_step_ref"] == op.P7_R54_OP10_STEP_REF
    assert material["op09_form_ready"] is False
    assert material["state_capture_status"] == op.P7_R54_OP10_REVIEW_STATE_CAPTURE_BLOCKED_STATUS_REF
    assert material["review_operation_status"] == op.P7_R54_OP10_REVIEW_NOT_STARTED_STATUS_REF
    assert material["reviewer_ref_ids"] == []
    assert material["reviewer_ref_count"] == 0
    assert material["sanitized_review_result_capture_allowed_next"] is False
    assert material["next_required_step"] == op.P7_R54_OP10_BLOCKED_NEXT_REQUIRED_STEP_REF
    assert material["execution_blocker_ids"]
    assert material["actual_human_review_run_here"] is False
    assert material["actual_review_evidence_complete"] is False
    _assert_body_free_no_promotion(material)


def test_r54_op10_not_started_after_form_freeze_captures_state_without_claiming_review_completion() -> None:
    material = op.build_p7_r54_op10_actual_human_review_operation_state_capture(
        reviewer_instruction_rating_form_freeze=_op09_ready()
    )

    assert material["op09_form_ready"] is True
    assert material["state_capture_status"] == op.P7_R54_OP10_REVIEW_STATE_CAPTURE_READY_STATUS_REF
    assert material["review_operation_status"] == op.P7_R54_OP10_REVIEW_NOT_STARTED_STATUS_REF
    assert material["reviewer_assignment_ref"] == "reviewer_assignment_not_started_bodyfree"
    assert material["sanitized_review_result_capture_allowed_next"] is False
    assert material["review_completed_packet_ref_count"] == 0
    assert material["review_completed_selection_row_count"] == 0
    assert material["next_required_step"] == op.P7_R54_OP10_NOT_COMPLETED_NEXT_REQUIRED_STEP_REF
    assert tuple(material["implemented_steps"]) == op.P7_R54_OP10_IMPLEMENTED_STEPS
    assert tuple(material["not_yet_implemented_steps"]) == op.P7_R54_OP10_NOT_YET_IMPLEMENTED_STEPS
    assert material["actual_human_review_run_here"] is False
    assert material["actual_manual_review_run_here"] is False
    assert material["rating_row_count"] == 0
    assert material["question_observation_row_count"] == 0
    _assert_body_free_no_promotion(material)


def test_r54_op10_completed_state_requires_24_packet_refs_and_selection_row_refs_before_op11() -> None:
    material = _op10_completed()
    op08 = _op08_ready()

    assert material["state_capture_status"] == op.P7_R54_OP10_REVIEW_STATE_CAPTURE_READY_STATUS_REF
    assert material["review_operation_status"] == op.P7_R54_OP10_REVIEW_COMPLETED_SELECTIONS_CAPTURED_STATUS_REF
    assert material["reviewer_ref_ids"] == ["reviewer-pseudonymous-r54-a"]
    assert material["reviewer_ref_count"] == 1
    assert material["review_completed_packet_ref_ids"] == op08["declared_packet_ref_ids"]
    assert material["review_completed_packet_ref_count"] == 24
    assert material["review_completed_packet_ref_ids_unique"] is True
    assert material["review_completed_selection_row_refs"] == _selection_row_refs()
    assert material["review_completed_selection_row_count"] == 24
    assert material["review_completed_selection_row_refs_unique"] is True
    assert material["review_completed_selections_captured_by_external_human_ref"] == "external_human_review_selection_receipt_bodyfree"
    assert material["sanitized_review_result_capture_allowed_next"] is True
    assert material["next_required_step"] == op.P7_R54_OP11_STEP_REF
    assert material["actual_human_review_run_here"] is False
    assert material["actual_review_evidence_complete"] is False
    _assert_body_free_no_promotion(material)


def test_r54_op10_blocks_completed_state_when_receipt_or_refs_are_missing() -> None:
    material = op.build_p7_r54_op10_actual_human_review_operation_state_capture(
        reviewer_instruction_rating_form_freeze=_op09_ready(),
        review_operation_status_ref=op.P7_R54_OP10_REVIEW_COMPLETED_SELECTIONS_CAPTURED_STATUS_REF,
        reviewer_ref_ids=["reviewer-pseudonymous-r54-a"],
        completed_packet_ref_ids=_op08_ready()["declared_packet_ref_ids"][:23],
        completed_selection_row_refs=_selection_row_refs(),
    )

    assert material["state_capture_status"] == op.P7_R54_OP10_REVIEW_STATE_CAPTURE_BLOCKED_STATUS_REF
    assert material["sanitized_review_result_capture_allowed_next"] is False
    assert material["next_required_step"] == op.P7_R54_OP10_NOT_COMPLETED_NEXT_REQUIRED_STEP_REF
    assert "review_completion_receipt_ref_required" in material["execution_blocker_ids"]
    assert "review_completed_packet_ref_count_must_be_24" in material["execution_blocker_ids"]
    _assert_body_free_no_promotion(material)


@pytest.mark.parametrize(
    "key,value",
    [
        ("op09_form_ready", False),
        ("op09_reviewer_instruction_status", op.P7_R54_OP09_FORM_BLOCKED_STATUS_REF),
        ("state_capture_is_bodyfree_only", False),
        ("state_capture_contains_reviewer_free_text", True),
        ("state_capture_contains_packet_content", True),
        ("state_capture_contains_local_path", True),
        ("state_capture_contains_question_text", True),
        ("state_capture_contains_body_hash", True),
        ("actual_human_review_started_here", True),
        ("actual_human_review_run_here", True),
        ("actual_manual_review_run_here", True),
        ("actual_review_evidence_complete", True),
        ("rating_row_count", 1),
        ("question_observation_row_count", 1),
        ("disposal_verified", True),
        ("human_review_completion_claim_blocked_here", False),
        ("p6_p8_release_promotion_blocked_here", False),
        ("p6_limited_human_readfeel_start_allowed", True),
        ("p8_start_allowed", True),
        ("release_allowed", True),
        ("question_text_included", True),
        ("draft_question_text_included", True),
        ("local_path_included", True),
    ],
)
def test_r54_op10_rejects_state_body_leak_review_claim_or_promotion_mutation(
    key: str,
    value: object,
) -> None:
    material = _op10_completed()
    material[key] = value
    with pytest.raises(ValueError):
        op.assert_p7_r54_op10_actual_human_review_operation_state_capture_contract(material)


def test_r54_op11_default_capture_blocks_until_op10_completed_state_is_ready() -> None:
    material = op.build_p7_r54_op11_sanitized_review_result_capture()

    assert material["schema_version"] == op.P7_R54_OPERATION_SANITIZED_REVIEW_RESULT_CAPTURE_SCHEMA_VERSION
    assert set(material) == set(op.P7_R54_OPERATION_SANITIZED_REVIEW_RESULT_CAPTURE_REQUIRED_FIELD_REFS)
    assert material["policy_section"] == op.P7_R54_OP11_STEP_REF
    assert material["operation_step_ref"] == op.P7_R54_OP11_STEP_REF
    assert material["op10_sanitized_capture_allowed_next"] is False
    assert material["sanitized_review_result_capture_status"] == op.P7_R54_OP11_SANITIZED_CAPTURE_BLOCKED_STATUS_REF
    assert material["sanitized_review_result_rows"] == []
    assert material["sanitized_review_result_row_count"] == 0
    assert material["selection_rows_are_bodyfree_only"] is False
    assert material["rating_row_normalization_allowed_next"] is False
    assert material["sanitized_review_result_rows_materialized_here"] is False
    assert material["next_required_step"] == op.P7_R54_OP11_BLOCKED_NEXT_REQUIRED_STEP_REF
    assert material["execution_blocker_ids"]
    _assert_body_free_no_promotion(material)


def test_r54_op11_captures_24_sanitized_selection_rows_without_rating_or_question_normalization() -> None:
    material = _op11_ready()
    op10 = _op10_completed()

    assert material["sanitized_review_result_capture_status"] == op.P7_R54_OP11_SANITIZED_CAPTURE_READY_STATUS_REF
    assert material["sanitized_review_result_capture_ref"] == op.P7_R54_OP11_SANITIZED_REVIEW_RESULT_CAPTURE_REF
    assert material["sanitized_review_result_reason_refs"] == [op.P7_R54_OP11_READY_REASON_REF]
    assert material["execution_blocker_ids"] == []
    assert material["open_execution_blocker_ids"] == []
    assert material["expected_packet_ref_ids"] == op10["review_completed_packet_ref_ids"]
    assert material["expected_selection_row_refs"] == op10["review_completed_selection_row_refs"]
    assert material["sanitized_review_result_row_count"] == 24
    assert material["reviewed_case_count"] == 24
    assert len(material["sanitized_review_result_rows"]) == 24
    assert material["packet_ref_ids"] == op10["review_completed_packet_ref_ids"]
    assert material["packet_ref_ids_unique"] is True
    assert material["case_ref_ids_unique"] is True
    assert material["blind_case_ids_unique"] is True
    assert material["reviewer_ref_ids"] == ["reviewer-pseudonymous-r54-a"]
    assert material["selection_rows_are_bodyfree_only"] is True
    assert material["rating_row_normalization_allowed_next"] is True
    assert material["sanitized_review_result_rows_materialized_here"] is True
    assert material["actual_rating_rows_materialized_here"] is False
    assert material["actual_question_need_observation_rows_materialized_here"] is False
    assert material["rating_row_count"] == 0
    assert material["question_observation_row_count"] == 0
    assert material["actual_review_evidence_complete"] is False
    assert material["disposal_verified"] is False
    assert tuple(material["implemented_steps"]) == op.P7_R54_OP11_IMPLEMENTED_STEPS
    assert tuple(material["not_yet_implemented_steps"]) == op.P7_R54_OP11_NOT_YET_IMPLEMENTED_STEPS
    assert material["next_required_step"] == op.P7_R54_OP12_STEP_REF
    row = material["sanitized_review_result_rows"][0]
    assert row["schema_version"] == op.P7_R54_OPERATION_SANITIZED_REVIEW_RESULT_ROW_SCHEMA_VERSION
    assert set(row) == set(op.P7_R54_OPERATION_SANITIZED_REVIEW_RESULT_ROW_REQUIRED_FIELD_REFS)
    assert row["selection_only_row"] is True
    assert row["body_removed"] is True
    assert row["body_free"] is True
    assert row["reviewer_free_text_included"] is False
    assert row["raw_body_included"] is False
    assert row["question_text_included"] is False
    assert row["local_path_included"] is False
    assert row["body_hash_included"] is False
    _assert_body_free_no_promotion(material)


def test_r54_op11_blocks_when_rows_are_missing_or_refs_do_not_match_op10() -> None:
    material = op.build_p7_r54_op11_sanitized_review_result_capture(
        actual_human_review_operation_state_capture=_op10_completed(),
        reviewer_selection_rows=_valid_selection_rows()[:23],
    )

    assert material["sanitized_review_result_capture_status"] == op.P7_R54_OP11_SANITIZED_CAPTURE_BLOCKED_STATUS_REF
    assert material["sanitized_review_result_rows"] == []
    assert "sanitized_review_result_row_count_must_be_24" in material["execution_blocker_ids"]
    assert material["rating_row_normalization_allowed_next"] is False
    assert material["next_required_step"] == op.P7_R54_OP11_BLOCKED_NEXT_REQUIRED_STEP_REF
    _assert_body_free_no_promotion(material)

    rows = _valid_selection_rows()
    rows[0]["packet_ref_id"] = "different-packet-ref"
    material = op.build_p7_r54_op11_sanitized_review_result_capture(
        actual_human_review_operation_state_capture=_op10_completed(),
        reviewer_selection_rows=rows,
    )
    assert material["sanitized_review_result_capture_status"] == op.P7_R54_OP11_SANITIZED_CAPTURE_BLOCKED_STATUS_REF
    assert "sanitized_review_packet_refs_must_match_op10_completion_refs" in material["execution_blocker_ids"]


def test_r54_op11_rejects_raw_body_or_reviewer_free_text_in_input_rows() -> None:
    rows = _valid_selection_rows()
    rows[0]["raw_input"] = "body must not be accepted"
    with pytest.raises(ValueError):
        op.build_p7_r54_op11_sanitized_review_result_capture(
            actual_human_review_operation_state_capture=_op10_completed(),
            reviewer_selection_rows=rows,
        )

    rows = _valid_selection_rows()
    rows[0]["reviewer_free_text"] = "notes must not be accepted"
    with pytest.raises(ValueError):
        op.build_p7_r54_op11_sanitized_review_result_capture(
            actual_human_review_operation_state_capture=_op10_completed(),
            reviewer_selection_rows=rows,
        )


@pytest.mark.parametrize(
    "key,value",
    [
        ("op10_sanitized_capture_allowed_next", False),
        ("op10_review_operation_status", op.P7_R54_OP10_REVIEW_IN_PROGRESS_STATUS_REF),
        ("sanitized_review_result_capture_ref", "different_capture_ref"),
        ("sanitized_review_result_row_count", 23),
        ("reviewed_case_count", 23),
        ("packet_ref_count", 23),
        ("case_ref_count", 23),
        ("blind_case_id_count", 23),
        ("packet_ref_ids_unique", False),
        ("case_ref_ids_unique", False),
        ("blind_case_ids_unique", False),
        ("selection_rows_are_bodyfree_only", False),
        ("sanitized_rows_contain_reviewer_free_text", True),
        ("sanitized_rows_contain_raw_body", True),
        ("sanitized_rows_contain_comment_text", True),
        ("sanitized_rows_contain_question_text", True),
        ("sanitized_rows_contain_local_path", True),
        ("sanitized_rows_contain_body_hash", True),
        ("sanitized_rows_contain_packet_content", True),
        ("rating_row_normalization_allowed_next", False),
        ("sanitized_review_result_rows_materialized_here", False),
        ("actual_rating_rows_materialized_here", True),
        ("actual_question_need_observation_rows_materialized_here", True),
        ("actual_review_evidence_complete", True),
        ("rating_row_count", 24),
        ("question_observation_row_count", 24),
        ("disposal_verified", True),
        ("human_review_completion_claim_blocked_here", False),
        ("p6_p8_release_promotion_blocked_here", False),
        ("p6_limited_human_readfeel_start_allowed", True),
        ("p8_start_allowed", True),
        ("release_allowed", True),
        ("question_text_included", True),
        ("draft_question_text_included", True),
        ("local_path_included", True),
    ],
)
def test_r54_op11_rejects_sanitized_capture_boundary_row_materialization_or_promotion_mutation(
    key: str,
    value: object,
) -> None:
    material = _op11_ready()
    material[key] = value
    with pytest.raises(ValueError):
        op.assert_p7_r54_op11_sanitized_review_result_capture_contract(material)


def test_r54_op11_rejects_row_level_body_or_option_mutations() -> None:
    material = _op11_ready()
    material["sanitized_review_result_rows"][0]["question_text_included"] = True
    with pytest.raises(ValueError):
        op.assert_p7_r54_op11_sanitized_review_result_capture_contract(material)

    material = _op11_ready()
    material["sanitized_review_result_rows"][0]["axis_scores"]["history_connection_naturalness"] = 1.25
    with pytest.raises(ValueError):
        op.assert_p7_r54_op11_sanitized_review_result_capture_contract(material)

    material = _op11_ready()
    material["sanitized_review_result_rows"][0]["verdict"] = "MAYBE"
    with pytest.raises(ValueError):
        op.assert_p7_r54_op11_sanitized_review_result_capture_contract(material)

    material = _op11_ready()
    material["sanitized_review_result_rows"][0]["plan_candidate_flags"]["p8_implementation_spec_finalized_here"] = True
    with pytest.raises(ValueError):
        op.assert_p7_r54_op11_sanitized_review_result_capture_contract(material)


def test_r54_op10_op11_bodyfree_aliases_match_primary_builders() -> None:
    op10 = op.build_p7_r54_operation_actual_human_review_operation_state_capture_bodyfree(
        reviewer_instruction_rating_form_freeze=_op09_ready(),
        review_operation_status_ref=op.P7_R54_OP10_REVIEW_COMPLETED_SELECTIONS_CAPTURED_STATUS_REF,
        reviewer_assignment_ref="r54_local_only_human_reviewer_assigned_bodyfree",
        reviewer_ref_ids=["reviewer-pseudonymous-r54-a"],
        review_completion_receipt_ref="r54_local_only_human_review_completed_receipt_bodyfree",
        completed_packet_ref_ids=_op08_ready()["declared_packet_ref_ids"],
        completed_selection_row_refs=_selection_row_refs(),
    )
    assert op.assert_p7_r54_operation_actual_human_review_operation_state_capture_bodyfree_contract(op10) is True
    assert op10["next_required_step"] == op.P7_R54_OP11_STEP_REF

    op11 = op.build_p7_r54_operation_sanitized_review_result_capture_bodyfree(
        actual_human_review_operation_state_capture=op10,
        reviewer_selection_rows=_valid_selection_rows(),
    )
    assert op.assert_p7_r54_operation_sanitized_review_result_capture_bodyfree_contract(op11) is True
    assert op11["next_required_step"] == op.P7_R54_OP12_STEP_REF
    _assert_body_free_no_promotion(op11)
