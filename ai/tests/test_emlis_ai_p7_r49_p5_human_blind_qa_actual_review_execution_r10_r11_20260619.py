# -*- coding: utf-8 -*-
from __future__ import annotations

import json
from copy import deepcopy
from functools import lru_cache

import pytest

import emlis_ai_p7_r49_p5_human_blind_qa_actual_review_execution as r49

SECRET_INPUT = "R49 secret raw input must not enter body-free R10/R11 material"
SECRET_SURFACE = "R49 returned Emlis surface must not enter body-free R10/R11 material"
SECRET_REVIEWER = "R49 reviewer free text must not enter body-free R10/R11 material"
SECRET_QUESTION = "R49 draft question text must not enter body-free R10/R11 material"


def _dumped(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def _assert_no_body_question_or_release_promotion(value: dict[str, object]) -> None:
    dumped = _dumped(value)
    assert SECRET_INPUT not in dumped
    assert SECRET_SURFACE not in dumped
    assert SECRET_REVIEWER not in dumped
    assert SECRET_QUESTION not in dumped
    for forbidden_key in (
        '"raw_input":',
        '"raw_answer":',
        '"comment_text":',
        '"comment_text_body":',
        '"current_input_review_surface":',
        '"returned_emlis_surface":',
        '"bounded_owned_history_review_surface":',
        '"reviewer_free_text":',
        '"reviewer_note":',
        '"question_text":',
        '"draft_question_text":',
        '"question_body":',
        '"terminal_output":',
        '"body_content_hash":',
        '"packet_content_hash":',
        '"local_absolute_path":',
    ):
        assert forbidden_key not in dumped
    for forbidden_true in (
        '"release_allowed": true',
        '"p7_complete": true',
        '"p8_start_allowed": true',
        '"hold004_close_allowed": true',
        '"question_api_implemented": true',
        '"question_db_schema_implemented": true',
        '"question_rn_ui_implemented": true',
        '"question_response_key_implemented": true',
        '"question_trigger_logic_implemented": true',
        '"p8_implementation_spec_finalized_here": true',
        '"actual_body_full_packet_generated_here": true',
        '"body_full_writer_created_here": true',
        '"actual_human_review_run_here": true',
        '"actual_rating_rows_materialized_here": true',
        '"actual_blocker_rows_materialized_here": true',
        '"actual_execution_blocker_rows_materialized_here": true',
        '"actual_question_need_observation_rows_materialized_here": true',
        '"actual_question_need_observation_summary_materialized_here": true',
        '"actual_disposal_run_here": true',
        '"actual_disposal_receipt_materialized_here": true',
        '"actual_cleanup_run_here": true',
    ):
        assert forbidden_true not in dumped.lower()


@lru_cache(maxsize=1)
def _cached_r9_guard() -> tuple[dict[str, object], dict[str, object]]:
    r2 = r49.build_p7_r49_r48_case_matrix_handoff_validation()
    assert r49.assert_p7_r49_r48_case_matrix_handoff_validation_contract(r2) is True
    r3 = r49.build_p7_r49_local_only_actual_packet_generation_preflight(
        r49_r48_case_matrix_handoff_validation=r2,
        local_review_root="/tmp/cocolon_r49_r10_r11_valid_external_local_review_root",
        explicit_body_full_generation_allow=True,
    )
    assert r49.assert_p7_r49_local_only_actual_packet_generation_preflight_contract(r3) is True
    protocol = r49.build_p7_r49_actual_review_session_protocol(
        r49_local_only_actual_packet_generation_preflight=r3,
    )
    assert r49.assert_p7_r49_actual_review_session_protocol_contract(protocol) is True
    connection = r49.build_p7_r49_rating_row_ingestion_r48_normalizer_connection(
        r49_actual_review_session_protocol=protocol,
    )
    assert r49.assert_p7_r49_rating_row_ingestion_r48_normalizer_connection_contract(connection) is True
    ingestion = r49.build_p7_r49_blocker_execution_blocker_ingestion(
        r49_rating_row_ingestion_r48_normalizer_connection=connection,
    )
    assert r49.assert_p7_r49_blocker_execution_blocker_ingestion_contract(ingestion) is True
    schema_freeze = r49.build_p7_r49_question_need_observation_row_schema_enum_freeze(
        r49_blocker_execution_blocker_ingestion=ingestion,
    )
    assert r49.assert_p7_r49_question_need_observation_row_schema_enum_freeze_contract(schema_freeze) is True
    normalizer = r49.build_p7_r49_question_need_observation_row_normalizer(
        r49_question_need_observation_row_schema_enum_freeze=schema_freeze,
    )
    assert r49.assert_p7_r49_question_need_observation_row_normalizer_contract(normalizer) is True
    guard = r49.build_p7_r49_rating_question_observation_consistency_guard(
        r49_question_need_observation_row_normalizer=normalizer,
    )
    assert r49.assert_p7_r49_rating_question_observation_consistency_guard_contract(guard) is True
    return (r2, guard)


def _r2() -> dict[str, object]:
    return deepcopy(_cached_r9_guard()[0])


def _r9_guard() -> dict[str, object]:
    return deepcopy(_cached_r9_guard()[1])


def _question_rows_for_all_cases() -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    case_rows = deepcopy(_r2()["case_manifest_rows"])
    for index, case_row in enumerate(case_rows):
        if index == 0:
            result = {
                "question_need_primary_class": "question_may_reduce_overread_risk",
                "ambiguity_kind_refs": ["missing_target"],
                "sanitized_reason_ids": ["question_may_reduce_overread_risk"],
            }
        elif index == 1:
            result = {
                "question_need_primary_class": "plus_single_question_candidate_later",
                "ambiguity_kind_refs": ["missing_time_scope"],
                "sanitized_reason_ids": ["plus_single_question_candidate_later"],
            }
        elif index == 2:
            result = {
                "question_need_primary_class": "premium_deep_dive_candidate_later",
                "ambiguity_kind_refs": ["missing_relation_context"],
                "sanitized_reason_ids": ["premium_deep_dive_candidate_later"],
            }
        else:
            result = {
                "question_need_primary_class": "no_question_needed_emlis_can_observe",
                "sanitized_reason_ids": ["no_question_needed_emlis_can_observe"],
            }
        rows.append(
            r49.normalize_p7_r49_question_need_observation_row_bodyfree(
                question_observation_result=result,
                case_manifest_row=case_row,
            )
        )
    return rows


def _complete_summary() -> dict[str, object]:
    return r49.build_p7_r49_question_need_observation_summary_bodyfree(
        r49_rating_question_observation_consistency_guard=_r9_guard(),
        question_need_observation_rows=_question_rows_for_all_cases(),
    )


def test_r49_r10_builds_bodyfree_question_need_observation_summary_without_starting_p8() -> None:
    summary = _complete_summary()
    assert r49.assert_p7_r49_question_need_observation_summary_bodyfree_contract(summary) is True

    assert summary["schema_version"] == r49.P7_R49_QUESTION_NEED_OBSERVATION_SUMMARY_BODYFREE_SCHEMA_VERSION
    assert set(summary) == set(r49.P7_R49_QUESTION_NEED_OBSERVATION_SUMMARY_BODYFREE_REQUIRED_FIELD_REFS)
    assert summary["policy_section"] == "R49-10_question_need_observation_summary_builder"
    assert summary["question_observation_summary_builder_ready"] is True
    assert summary["question_observation_rows_must_be_bodyfree"] is True
    assert summary["total_case_count"] == r49.P7_R49_REQUIRED_TOTAL_CASES
    assert summary["question_observation_row_count"] == r49.P7_R49_REQUIRED_TOTAL_CASES
    assert summary["question_observation_rows_complete"] is True
    assert summary["unique_case_ref_id_count"] == r49.P7_R49_REQUIRED_TOTAL_CASES
    assert summary["unique_blind_case_id_count"] == r49.P7_R49_REQUIRED_TOTAL_CASES
    assert summary["unique_packet_ref_id_count"] == r49.P7_R49_REQUIRED_TOTAL_CASES
    assert set(summary["primary_class_counts"]) == set(r49.P7_R49_QUESTION_NEED_PRIMARY_CLASS_REFS)
    assert sum(summary["primary_class_counts"].values()) == r49.P7_R49_REQUIRED_TOTAL_CASES
    assert set(summary["ambiguity_kind_counts"]) == set(r49.P7_R49_AMBIGUITY_KIND_REFS)
    assert set(summary["one_question_fit_counts"]) == set(r49.P7_R49_ONE_QUESTION_FIT_REFS)
    assert set(summary["repair_required_counts"]) == set(r49.P7_R49_REPAIR_REQUIRED_REF_REFS)
    assert set(summary["plan_candidate_flag_counts"]) == set(r49.P7_R49_PLAN_CANDIDATE_FLAG_REFS)
    assert summary["p8_design_material_candidate_row_count"] > 0
    assert summary["p8_question_design_material_candidate"] is True
    assert summary["p8_start_allowed"] is False
    assert summary["p8_implementation_spec_finalized_here"] is False
    assert summary["question_trigger_logic_implemented_here"] is False
    assert summary["api_db_rn_response_key_changed_here"] is False
    assert summary["actual_human_review_run_here"] is False
    assert summary["actual_question_need_observation_rows_materialized_here"] is False
    assert summary["actual_question_need_observation_summary_materialized_here"] is False
    assert tuple(summary["implemented_steps"]) == r49.P7_R49_R10_IMPLEMENTED_STEPS
    assert tuple(summary["not_yet_implemented_steps"]) == r49.P7_R49_R10_NOT_YET_IMPLEMENTED_STEPS
    assert summary["next_required_step"] == r49.P7_R49_R10_NEXT_REQUIRED_STEP_REF
    _assert_no_body_question_or_release_promotion(summary)


def test_r49_r10_incomplete_summary_stays_non_candidate_and_rejects_body_leaks() -> None:
    summary = r49.build_p7_r49_question_need_observation_summary_bodyfree(
        r49_rating_question_observation_consistency_guard=_r9_guard(),
    )
    assert r49.assert_p7_r49_question_need_observation_summary_bodyfree_contract(summary) is True
    assert summary["question_observation_row_count"] == 0
    assert summary["question_observation_rows_complete"] is False
    assert summary["p8_question_design_material_candidate"] is False
    assert summary["next_required_step"] == r49.P7_R49_R10_NEXT_REQUIRED_STEP_REF
    _assert_no_body_question_or_release_promotion(summary)

    leaky_row = deepcopy(_question_rows_for_all_cases()[0])
    leaky_row["question_text"] = SECRET_QUESTION
    with pytest.raises(ValueError):
        r49.build_p7_r49_question_need_observation_summary_bodyfree(
            r49_rating_question_observation_consistency_guard=_r9_guard(),
            question_need_observation_rows=[leaky_row],
        )

    duplicate_rows = _question_rows_for_all_cases()
    duplicate_rows[1] = deepcopy(duplicate_rows[0])
    with pytest.raises(ValueError):
        r49.build_p7_r49_question_need_observation_summary_bodyfree(
            r49_rating_question_observation_consistency_guard=_r9_guard(),
            question_need_observation_rows=duplicate_rows,
        )


def test_r49_r11_connects_r48_disposal_receipt_schema_without_running_disposal() -> None:
    summary = _complete_summary()
    connection = r49.build_p7_r49_disposal_receipt_connection(
        r49_question_need_observation_summary=summary,
    )
    assert r49.assert_p7_r49_disposal_receipt_connection_contract(connection) is True

    assert connection["schema_version"] == r49.P7_R49_DISPOSAL_RECEIPT_CONNECTION_SCHEMA_VERSION
    assert set(connection) == set(r49.P7_R49_DISPOSAL_RECEIPT_CONNECTION_REQUIRED_FIELD_REFS)
    assert connection["policy_section"] == "R49-11_disposal_receipt_connection"
    assert connection["r48_disposal_receipt_builder_function_ref"] == "build_p7_r48_p5_disposal_receipt_bodyfree"
    assert connection["r48_disposal_receipt_contract_ref"] == "assert_p7_r48_p5_disposal_receipt_bodyfree_contract"
    assert tuple(connection["r48_disposal_receipt_required_field_refs"]) == r49.P7_R48_P5_DISPOSAL_RECEIPT_REQUIRED_FIELD_REFS
    assert tuple(connection["r48_disposal_receipt_forbidden_field_refs"]) == r49.P7_R48_P5_DISPOSAL_RECEIPT_FORBIDDEN_FIELD_REFS
    assert set(connection["r47_disposal_status_refs"]) == set(r49.P7_R47_DISPOSAL_STATUSES)
    assert connection["question_observation_rows_complete_required_before_disposal_pending"] is True
    assert connection["question_observation_rows_complete"] is True
    assert connection["disposal_pending_allowed_by_question_observation_summary"] is True
    assert connection["disposal_status"] == "PURGE_REQUIRED"
    assert connection["review_session_status"] == "DISPOSAL_PENDING"
    assert connection["disposal_verified_for_candidate"] is False
    assert connection["disposal_receipt_bodyfree"] is True
    assert connection["disposal_receipt"]["schema_version"] == r49.P7_R48_P5_DISPOSAL_RECEIPT_BODYFREE_SCHEMA_VERSION
    assert connection["local_packet_exported"] is False
    assert connection["content_hash_of_body_stored"] is False
    assert connection["body_path_hash_forbidden"] is True
    assert connection["receipt_does_not_delete_files_here"] is True
    assert connection["actual_disposal_run_here"] is False
    assert connection["actual_cleanup_run_here"] is False
    assert connection["actual_disposal_receipt_materialized_here"] is False
    assert connection["p8_start_allowed"] is False
    assert connection["release_allowed"] is False
    assert tuple(connection["implemented_steps"]) == r49.P7_R49_R11_IMPLEMENTED_STEPS
    assert tuple(connection["not_yet_implemented_steps"]) == r49.P7_R49_R11_NOT_YET_IMPLEMENTED_STEPS
    assert connection["next_required_step"] == r49.P7_R49_R11_NEXT_REQUIRED_STEP_REF
    _assert_no_body_question_or_release_promotion(connection)


def test_r49_r11_accepts_bodyfree_verified_r48_receipt_but_still_does_not_claim_disposal_execution() -> None:
    summary = _complete_summary()
    r48_receipt = r49.build_p7_r48_p5_disposal_receipt_bodyfree(
        review_session_id=r49.P7_R49_DEFAULT_REVIEW_SESSION_ID,
        case_count=r49.P7_R49_REQUIRED_TOTAL_CASES,
        deleted_file_count=48,
        disposal_status="DISPOSAL_VERIFIED",
        body_removed=True,
        reviewer_notes_removed=True,
        purge_started_at="20260619T000000JST",
        purge_completed_at="20260619T000001JST",
    )
    connection = r49.build_p7_r49_disposal_receipt_connection(
        r49_question_need_observation_summary=summary,
        disposal_result=r48_receipt,
    )
    assert r49.assert_p7_r49_disposal_receipt_connection_contract(connection) is True
    assert connection["disposal_status"] == "DISPOSAL_VERIFIED"
    assert connection["review_session_status"] == "DISPOSAL_VERIFIED"
    assert connection["disposal_verified_for_candidate"] is True
    assert connection["body_removed"] is True
    assert connection["reviewer_notes_removed"] is True
    assert connection["execution_blocker_ids"] == []
    assert connection["actual_disposal_run_here"] is False
    assert connection["actual_disposal_receipt_materialized_here"] is False
    assert connection["p8_start_allowed"] is False
    assert connection["release_allowed"] is False
    _assert_no_body_question_or_release_promotion(connection)


def test_r49_r11_blocks_disposal_pending_when_question_observation_summary_is_incomplete() -> None:
    incomplete_summary = r49.build_p7_r49_question_need_observation_summary_bodyfree(
        r49_rating_question_observation_consistency_guard=_r9_guard(),
    )
    blocked = r49.build_p7_r49_disposal_receipt_connection(
        r49_question_need_observation_summary=incomplete_summary,
    )
    assert r49.assert_p7_r49_disposal_receipt_connection_contract(blocked) is True
    assert blocked["question_observation_rows_complete"] is False
    assert blocked["disposal_pending_allowed_by_question_observation_summary"] is False
    assert blocked["disposal_status"] == "GENERATION_BLOCKED"
    assert blocked["review_session_status"] == "BLOCKED"
    assert "r49_question_need_observation_rows_missing" in blocked["execution_blocker_ids"]
    assert blocked["p8_start_allowed"] is False
    assert blocked["release_allowed"] is False

    with pytest.raises(ValueError):
        r49.build_p7_r49_disposal_receipt_connection(
            r49_question_need_observation_summary=incomplete_summary,
            disposal_status="PURGE_REQUIRED",
        )
    with pytest.raises(ValueError):
        r49.build_p7_r49_disposal_receipt_connection(
            r49_question_need_observation_summary=incomplete_summary,
            disposal_result={
                "schema_version": r49.P7_R48_P5_DISPOSAL_RECEIPT_BODYFREE_SCHEMA_VERSION,
                "review_session_id": r49.P7_R49_DEFAULT_REVIEW_SESSION_ID,
                "packet_kind": r49.P7_R49_PACKET_KIND,
                "case_count": r49.P7_R49_REQUIRED_TOTAL_CASES,
                "deleted_file_count": 24,
                "purge_started_at": "20260619T000000JST",
                "purge_completed_at": "20260619T000001JST",
                "disposal_status": "DISPOSAL_VERIFIED",
                "body_removed": True,
                "reviewer_notes_removed": True,
                "local_packet_exported": False,
                "content_hash_of_body_stored": False,
                "p7_material_body_free": True,
                "body_free": True,
                "release_allowed": False,
                "p7_complete": False,
                "p8_start_allowed": False,
                "hold004_close_allowed": False,
            },
        )


def test_r49_r10_r11_freeze_combines_summary_and_disposal_connection_without_advancing_to_r12_or_release() -> None:
    summary = _complete_summary()
    connection = r49.build_p7_r49_disposal_receipt_connection(
        r49_question_need_observation_summary=summary,
    )
    freeze = r49.build_p7_r49_r10_r11_question_summary_disposal_connection_freeze(
        r49_question_need_observation_summary=summary,
        r49_disposal_receipt_connection=connection,
    )
    assert r49.assert_p7_r49_r10_r11_question_summary_disposal_connection_freeze_contract(freeze) is True

    assert freeze["schema_version"] == r49.P7_R49_R10_R11_QUESTION_SUMMARY_DISPOSAL_CONNECTION_FREEZE_SCHEMA_VERSION
    assert set(freeze) == set(r49.P7_R49_R10_R11_QUESTION_SUMMARY_DISPOSAL_CONNECTION_FREEZE_REQUIRED_FIELD_REFS)
    assert freeze["policy_section"] == "R49-10_R49-11_question_summary_disposal_connection_freeze"
    assert freeze["question_observation_summary_builder_ready"] is True
    assert freeze["question_observation_rows_complete"] is True
    assert freeze["disposal_receipt_connection_ready"] is True
    assert freeze["disposal_receipt_bodyfree"] is True
    assert freeze["disposal_pending_allowed_by_question_observation_summary"] is True
    assert freeze["p8_question_design_material_candidate"] is True
    assert freeze["p8_start_allowed"] is False
    assert freeze["release_allowed"] is False
    assert freeze["actual_disposal_run_here"] is False
    assert freeze["actual_disposal_receipt_materialized_here"] is False
    assert freeze["actual_human_review_run_here"] is False
    assert tuple(freeze["implemented_steps"]) == r49.P7_R49_R11_IMPLEMENTED_STEPS
    assert tuple(freeze["not_yet_implemented_steps"]) == r49.P7_R49_R11_NOT_YET_IMPLEMENTED_STEPS
    assert freeze["next_required_step"] == r49.P7_R49_R11_NEXT_REQUIRED_STEP_REF
    _assert_no_body_question_or_release_promotion(freeze)
