# -*- coding: utf-8 -*-
from __future__ import annotations

import json
from copy import deepcopy
from functools import lru_cache

import pytest

import emlis_ai_p7_r49_p5_human_blind_qa_actual_review_execution as r49

SECRET_INPUT = "R49 secret raw input must not enter body-free R12/R13 material"
SECRET_SURFACE = "R49 returned Emlis surface must not enter body-free R12/R13 material"
SECRET_REVIEWER = "R49 reviewer free text must not enter body-free R12/R13 material"
SECRET_QUESTION = "R49 draft question text must not enter body-free R12/R13 material"


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
        '"actual_disposal_run_here": true',
        '"actual_disposal_receipt_materialized_here": true',
    ):
        assert forbidden_true not in dumped.lower()


@lru_cache(maxsize=1)
def _cached_base() -> tuple[dict[str, object], dict[str, object]]:
    r2 = r49.build_p7_r49_r48_case_matrix_handoff_validation()
    assert r49.assert_p7_r49_r48_case_matrix_handoff_validation_contract(r2) is True
    r3 = r49.build_p7_r49_local_only_actual_packet_generation_preflight(
        r49_r48_case_matrix_handoff_validation=r2,
        local_review_root="/tmp/cocolon_r49_r12_r13_valid_external_local_review_root",
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
    return deepcopy(_cached_base()[0])


def _r9_guard() -> dict[str, object]:
    return deepcopy(_cached_base()[1])


def _case_rows() -> list[dict[str, object]]:
    return deepcopy(_r2()["case_manifest_rows"])


def _pass_rating_rows_for_all_cases() -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for case_row in _case_rows():
        rows.append(
            r49.normalize_p7_r49_p5_rating_row_via_r48_bodyfree(
                case_manifest_row=case_row,
                review_session_id=r49.P7_R49_DEFAULT_REVIEW_SESSION_ID,
                review_result={
                    "axis_scores": {axis: 1.0 for axis in r49.P5_HUMAN_BLIND_QA_RATING_AXES},
                    "verdict": "PASS",
                    "sanitized_reason_ids": [],
                    "blocker_ids": [],
                },
                body_removed=True,
            )
        )
    return rows


def _question_rows_for_all_cases(*, with_repair_required: bool = False) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for index, case_row in enumerate(_case_rows()):
        if with_repair_required and index == 0:
            result = {
                "question_need_primary_class": "not_question_p5_surface_repair_required",
                "ambiguity_kind_refs": ["history_connection_basis_unclear"],
                "sanitized_reason_ids": ["not_question_p5_surface_repair_required"],
            }
        elif index == 0:
            result = {
                "question_need_primary_class": "question_may_reduce_overread_risk",
                "ambiguity_kind_refs": ["missing_target"],
                "sanitized_reason_ids": ["question_may_reduce_overread_risk"],
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


def _complete_question_summary(*, with_repair_required: bool = False) -> dict[str, object]:
    return r49.build_p7_r49_question_need_observation_summary_bodyfree(
        r49_rating_question_observation_consistency_guard=_r9_guard(),
        question_need_observation_rows=_question_rows_for_all_cases(with_repair_required=with_repair_required),
    )


def _verified_disposal_connection(summary: dict[str, object]) -> dict[str, object]:
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
    return r49.build_p7_r49_disposal_receipt_connection(
        r49_question_need_observation_summary=summary,
        disposal_result=r48_receipt,
    )


def _r10_r11_freeze(*, with_repair_required: bool = False, verified_disposal: bool = True) -> dict[str, object]:
    summary = _complete_question_summary(with_repair_required=with_repair_required)
    connection = _verified_disposal_connection(summary) if verified_disposal else r49.build_p7_r49_disposal_receipt_connection(
        r49_question_need_observation_summary=summary,
    )
    return r49.build_p7_r49_r10_r11_question_summary_disposal_connection_freeze(
        r49_question_need_observation_summary=summary,
        r49_disposal_receipt_connection=connection,
    )


def test_r49_r12_builds_review_handoff_summary_from_r48_summary_without_confirming_p5() -> None:
    handoff = r49.build_p7_r49_review_handoff_summary_bodyfree(
        r10_r11_question_summary_disposal_connection_freeze=_r10_r11_freeze(),
        rating_rows=_pass_rating_rows_for_all_cases(),
    )
    assert r49.assert_p7_r49_review_handoff_summary_bodyfree_contract(handoff) is True

    assert handoff["schema_version"] == r49.P7_R49_REVIEW_HANDOFF_SUMMARY_BODYFREE_SCHEMA_VERSION
    assert set(handoff) == set(r49.P7_R49_REVIEW_HANDOFF_SUMMARY_BODYFREE_REQUIRED_FIELD_REFS)
    assert handoff["policy_section"] == "R49-12_review_handoff_summary_builder"
    assert handoff["r48_review_handoff_summary_function_ref"] == "build_p7_r48_p5_review_handoff_summary_bodyfree"
    assert tuple(handoff["r48_review_handoff_summary_required_field_refs"]) == r49.P7_R48_P5_REVIEW_HANDOFF_SUMMARY_REQUIRED_FIELD_REFS
    assert handoff["review_session_status"] == "SUMMARY_FINALIZED"
    assert handoff["r48_review_session_status"] == "FINALIZED"
    assert handoff["rating_row_count"] == r49.P7_R49_REQUIRED_TOTAL_CASES
    assert handoff["rating_rows_complete"] is True
    assert handoff["question_observation_row_count"] == r49.P7_R49_REQUIRED_TOTAL_CASES
    assert handoff["question_observation_rows_complete"] is True
    assert handoff["question_observation_repair_required_count"] == 0
    assert handoff["question_observation_execution_blocker_count"] == 0
    assert handoff["disposal_verified_for_candidate"] is True
    assert handoff["r48_handoff_summary_candidate_claim"] is True
    assert handoff["p5_human_blind_qa_confirmed_candidate"] is False
    assert handoff["p6_limited_human_readfeel_start_allowed_candidate"] is False
    assert handoff["p8_start_allowed"] is False
    assert handoff["release_allowed"] is False
    assert tuple(handoff["implemented_steps"]) == r49.P7_R49_R12_IMPLEMENTED_STEPS
    assert tuple(handoff["not_yet_implemented_steps"]) == r49.P7_R49_R12_NOT_YET_IMPLEMENTED_STEPS
    assert handoff["next_required_step"] == r49.P7_R49_R12_NEXT_REQUIRED_STEP_REF
    _assert_no_body_question_or_release_promotion(handoff)


def test_r49_r13_connects_p5_candidate_gate_but_defers_p6_and_release() -> None:
    handoff = r49.build_p7_r49_review_handoff_summary_bodyfree(
        r10_r11_question_summary_disposal_connection_freeze=_r10_r11_freeze(),
        rating_rows=_pass_rating_rows_for_all_cases(),
    )
    gate = r49.build_p7_r49_p5_confirmed_candidate_gate_connection(r49_review_handoff_summary=handoff)
    assert r49.assert_p7_r49_p5_confirmed_candidate_gate_connection_contract(gate) is True

    assert gate["schema_version"] == r49.P7_R49_P5_CONFIRMED_CANDIDATE_GATE_CONNECTION_SCHEMA_VERSION
    assert set(gate) == set(r49.P7_R49_P5_CONFIRMED_CANDIDATE_GATE_CONNECTION_REQUIRED_FIELD_REFS)
    assert gate["policy_section"] == "R49-13_p5_confirmed_candidate_gate_connection"
    assert gate["r48_p5_confirmed_candidate_gate_function_ref"] == "build_p7_r48_p5_confirmed_candidate_gate_bodyfree"
    assert tuple(gate["r48_p5_confirmed_candidate_gate_required_field_refs"]) == r49.P7_R48_P5_CONFIRMED_CANDIDATE_GATE_REQUIRED_FIELD_REFS
    assert set(gate["required_condition_refs"]) == set(r49.P7_R49_P5_CONFIRMED_CANDIDATE_REQUIRED_CONDITION_REFS)
    assert gate["missing_requirement_refs"] == []
    assert gate["failed_requirement_count"] == 0
    assert gate["r48_p5_confirmed_candidate_gate_passed"] is True
    assert gate["question_observation_completeness_connected_to_gate"] is True
    assert gate["p5_confirmed_candidate_gate_passed"] is True
    assert gate["p5_human_blind_qa_confirmed_candidate"] is True
    assert gate["p6_limited_human_readfeel_start_allowed_candidate"] is False
    assert gate["p6_candidate_handoff_deferred_to_r14"] is True
    assert gate["p5_human_blind_qa_confirmed"] is False
    assert gate["p6_limited_human_readfeel_start_allowed"] is False
    assert gate["p8_start_allowed"] is False
    assert gate["release_allowed"] is False
    assert tuple(gate["implemented_steps"]) == r49.P7_R49_R13_IMPLEMENTED_STEPS
    assert tuple(gate["not_yet_implemented_steps"]) == r49.P7_R49_R13_NOT_YET_IMPLEMENTED_STEPS
    assert gate["next_required_step"] == r49.P7_R49_R13_NEXT_REQUIRED_STEP_REF
    _assert_no_body_question_or_release_promotion(gate)


def test_r49_r13_blocks_candidate_when_question_observation_marks_p5_repair_required() -> None:
    handoff = r49.build_p7_r49_review_handoff_summary_bodyfree(
        r10_r11_question_summary_disposal_connection_freeze=_r10_r11_freeze(with_repair_required=True),
        rating_rows=_pass_rating_rows_for_all_cases(),
    )
    assert handoff["r48_handoff_summary_candidate_claim"] is True
    assert handoff["question_observation_repair_required_count"] == 1
    gate = r49.build_p7_r49_p5_confirmed_candidate_gate_connection(r49_review_handoff_summary=handoff)
    assert r49.assert_p7_r49_p5_confirmed_candidate_gate_connection_contract(gate) is True
    assert gate["r48_p5_confirmed_candidate_gate_passed"] is True
    assert gate["p5_confirmed_candidate_gate_passed"] is False
    assert gate["p5_human_blind_qa_confirmed_candidate"] is False
    assert "question_observation_repair_required_zero" in gate["missing_requirement_refs"]
    assert gate["p8_start_allowed"] is False
    assert gate["release_allowed"] is False
    _assert_no_body_question_or_release_promotion(gate)


def test_r49_r13_blocks_candidate_until_disposal_is_verified() -> None:
    handoff = r49.build_p7_r49_review_handoff_summary_bodyfree(
        r10_r11_question_summary_disposal_connection_freeze=_r10_r11_freeze(verified_disposal=False),
        rating_rows=_pass_rating_rows_for_all_cases(),
    )
    assert handoff["review_session_status"] == "DISPOSAL_PENDING"
    assert handoff["disposal_verified_for_candidate"] is False
    gate = r49.build_p7_r49_p5_confirmed_candidate_gate_connection(r49_review_handoff_summary=handoff)
    assert r49.assert_p7_r49_p5_confirmed_candidate_gate_connection_contract(gate) is True
    assert gate["p5_confirmed_candidate_gate_passed"] is False
    assert gate["p5_human_blind_qa_confirmed_candidate"] is False
    assert "r49_review_handoff_summary_finalized" in gate["missing_requirement_refs"]
    assert "disposal_verified_for_candidate" in gate["missing_requirement_refs"]
    assert gate["p8_start_allowed"] is False
    assert gate["release_allowed"] is False
    _assert_no_body_question_or_release_promotion(gate)


def test_r49_r12_r13_freeze_combines_handoff_and_gate_without_advancing_to_r14_or_p8() -> None:
    handoff = r49.build_p7_r49_review_handoff_summary_bodyfree(
        r10_r11_question_summary_disposal_connection_freeze=_r10_r11_freeze(),
        rating_rows=_pass_rating_rows_for_all_cases(),
    )
    gate = r49.build_p7_r49_p5_confirmed_candidate_gate_connection(r49_review_handoff_summary=handoff)
    freeze = r49.build_p7_r49_r12_r13_review_handoff_p5_gate_connection_freeze(
        r49_review_handoff_summary=handoff,
        r49_p5_confirmed_candidate_gate_connection=gate,
    )
    assert r49.assert_p7_r49_r12_r13_review_handoff_p5_gate_connection_freeze_contract(freeze) is True

    assert freeze["schema_version"] == r49.P7_R49_R12_R13_REVIEW_HANDOFF_P5_GATE_CONNECTION_FREEZE_SCHEMA_VERSION
    assert set(freeze) == set(r49.P7_R49_R12_R13_REVIEW_HANDOFF_P5_GATE_CONNECTION_FREEZE_REQUIRED_FIELD_REFS)
    assert freeze["policy_section"] == "R49-12_R49-13_review_handoff_p5_gate_connection_freeze"
    assert freeze["review_handoff_summary_ready"] is True
    assert freeze["p5_confirmed_candidate_gate_connected"] is True
    assert freeze["question_observation_completeness_connected_to_gate"] is True
    assert freeze["p5_human_blind_qa_confirmed_candidate"] is True
    assert freeze["p6_limited_human_readfeel_start_allowed_candidate"] is False
    assert freeze["p6_candidate_handoff_deferred_to_r14"] is True
    assert freeze["p8_start_allowed"] is False
    assert freeze["release_allowed"] is False
    assert tuple(freeze["implemented_steps"]) == r49.P7_R49_R13_IMPLEMENTED_STEPS
    assert tuple(freeze["not_yet_implemented_steps"]) == r49.P7_R49_R13_NOT_YET_IMPLEMENTED_STEPS
    assert freeze["next_required_step"] == r49.P7_R49_R13_NEXT_REQUIRED_STEP_REF
    _assert_no_body_question_or_release_promotion(freeze)


@pytest.mark.parametrize(
    "leaky_key,secret",
    [
        ("raw_input", SECRET_INPUT),
        ("returned_emlis_surface", SECRET_SURFACE),
        ("reviewer_free_text", SECRET_REVIEWER),
        ("question_text", SECRET_QUESTION),
    ],
)
def test_r49_r12_rejects_body_or_question_text_leaks(leaky_key: str, secret: str) -> None:
    rating_rows = _pass_rating_rows_for_all_cases()
    rating_rows[0] = deepcopy(rating_rows[0])
    rating_rows[0][leaky_key] = secret
    with pytest.raises(ValueError):
        r49.build_p7_r49_review_handoff_summary_bodyfree(
            r10_r11_question_summary_disposal_connection_freeze=_r10_r11_freeze(),
            rating_rows=rating_rows,
        )
