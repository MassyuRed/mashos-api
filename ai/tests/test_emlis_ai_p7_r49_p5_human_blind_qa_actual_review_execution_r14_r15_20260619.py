# -*- coding: utf-8 -*-
from __future__ import annotations

import json
from copy import deepcopy
from functools import lru_cache

import pytest

import emlis_ai_p7_r49_p5_human_blind_qa_actual_review_execution as r49

SECRET_INPUT = "R49 secret raw input must not enter body-free R14/R15 material"
SECRET_SURFACE = "R49 returned Emlis surface must not enter body-free R14/R15 material"
SECRET_REVIEWER = "R49 reviewer free text must not enter body-free R14/R15 material"
SECRET_QUESTION = "R49 draft question text must not enter body-free R14/R15 material"


def _dumped(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def _assert_no_body_question_or_permission_promotion(value: dict[str, object]) -> None:
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
        '"p6_limited_human_readfeel_start_allowed": true',
        '"p6_limited_human_readfeel_confirmed": true',
        '"p8_detail_design_allowed_here": true',
        '"p8_implementation_spec_finalized_here": true',
        '"question_api_implemented": true',
        '"question_db_schema_implemented": true',
        '"question_rn_ui_implemented": true',
        '"question_response_key_implemented": true',
        '"question_trigger_logic_implemented": true',
        '"question_trigger_logic_implemented_here": true',
        '"api_db_rn_response_key_changed_here": true',
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
        local_review_root="/tmp/cocolon_r49_r14_r15_valid_external_local_review_root",
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


@lru_cache(maxsize=1)
def _cached_pass_rating_rows_for_all_cases() -> tuple[dict[str, object], ...]:
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
    return tuple(rows)


def _pass_rating_rows_for_all_cases() -> list[dict[str, object]]:
    return deepcopy(_cached_pass_rating_rows_for_all_cases())


@lru_cache(maxsize=4)
def _cached_question_rows_for_all_cases(
    with_repair_required: bool = False,
    with_no_p8_candidate: bool = False,
) -> tuple[dict[str, object], ...]:
    rows: list[dict[str, object]] = []
    for index, case_row in enumerate(_case_rows()):
        if with_repair_required and index == 0:
            result = {
                "question_need_primary_class": "not_question_p5_surface_repair_required",
                "ambiguity_kind_refs": ["history_connection_basis_unclear"],
                "sanitized_reason_ids": ["not_question_p5_surface_repair_required"],
            }
        elif with_no_p8_candidate or index > 0:
            result = {
                "question_need_primary_class": "no_question_needed_emlis_can_observe",
                "sanitized_reason_ids": ["no_question_needed_emlis_can_observe"],
            }
        else:
            result = {
                "question_need_primary_class": "question_may_reduce_overread_risk",
                "ambiguity_kind_refs": ["missing_target"],
                "sanitized_reason_ids": ["question_may_reduce_overread_risk"],
            }
        rows.append(
            r49.normalize_p7_r49_question_need_observation_row_bodyfree(
                question_observation_result=result,
                case_manifest_row=case_row,
            )
        )
    return tuple(rows)


def _question_rows_for_all_cases(
    *,
    with_repair_required: bool = False,
    with_no_p8_candidate: bool = False,
) -> list[dict[str, object]]:
    return deepcopy(_cached_question_rows_for_all_cases(with_repair_required, with_no_p8_candidate))


@lru_cache(maxsize=4)
def _cached_complete_question_summary(
    with_repair_required: bool = False,
    with_no_p8_candidate: bool = False,
) -> dict[str, object]:
    return r49.build_p7_r49_question_need_observation_summary_bodyfree(
        r49_rating_question_observation_consistency_guard=_r9_guard(),
        question_need_observation_rows=_question_rows_for_all_cases(
            with_repair_required=with_repair_required,
            with_no_p8_candidate=with_no_p8_candidate,
        ),
    )


def _complete_question_summary(
    *,
    with_repair_required: bool = False,
    with_no_p8_candidate: bool = False,
) -> dict[str, object]:
    return deepcopy(_cached_complete_question_summary(with_repair_required, with_no_p8_candidate))


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


def _r10_r11_freeze(
    *,
    with_repair_required: bool = False,
    with_no_p8_candidate: bool = False,
    verified_disposal: bool = True,
) -> dict[str, object]:
    summary = _complete_question_summary(
        with_repair_required=with_repair_required,
        with_no_p8_candidate=with_no_p8_candidate,
    )
    connection = (
        _verified_disposal_connection(summary)
        if verified_disposal
        else r49.build_p7_r49_disposal_receipt_connection(r49_question_need_observation_summary=summary)
    )
    return r49.build_p7_r49_r10_r11_question_summary_disposal_connection_freeze(
        r49_question_need_observation_summary=summary,
        r49_disposal_receipt_connection=connection,
    )


@lru_cache(maxsize=8)
def _cached_review_handoff(
    with_repair_required: bool = False,
    with_no_p8_candidate: bool = False,
    verified_disposal: bool = True,
) -> dict[str, object]:
    return r49.build_p7_r49_review_handoff_summary_bodyfree(
        r10_r11_question_summary_disposal_connection_freeze=_r10_r11_freeze(
            with_repair_required=with_repair_required,
            with_no_p8_candidate=with_no_p8_candidate,
            verified_disposal=verified_disposal,
        ),
        rating_rows=_pass_rating_rows_for_all_cases(),
    )


def _review_handoff(
    *,
    with_repair_required: bool = False,
    with_no_p8_candidate: bool = False,
    verified_disposal: bool = True,
) -> dict[str, object]:
    return deepcopy(_cached_review_handoff(with_repair_required, with_no_p8_candidate, verified_disposal))


@lru_cache(maxsize=2)
def _cached_valid_gate(with_no_p8_candidate: bool = False) -> dict[str, object]:
    handoff = _review_handoff(with_no_p8_candidate=with_no_p8_candidate)
    gate = r49.build_p7_r49_p5_confirmed_candidate_gate_connection(r49_review_handoff_summary=handoff)
    assert r49.assert_p7_r49_p5_confirmed_candidate_gate_connection_contract(gate) is True
    return gate


def _valid_gate(*, with_no_p8_candidate: bool = False) -> dict[str, object]:
    return deepcopy(_cached_valid_gate(with_no_p8_candidate))


@lru_cache(maxsize=1)
def _cached_repair_required_gate() -> dict[str, object]:
    handoff = _review_handoff(with_repair_required=True)
    gate = r49.build_p7_r49_p5_confirmed_candidate_gate_connection(r49_review_handoff_summary=handoff)
    assert r49.assert_p7_r49_p5_confirmed_candidate_gate_connection_contract(gate) is True
    return gate


def _repair_required_gate() -> dict[str, object]:
    return deepcopy(_cached_repair_required_gate())


@lru_cache(maxsize=1)
def _cached_undisposed_gate() -> dict[str, object]:
    handoff = _review_handoff(verified_disposal=False)
    gate = r49.build_p7_r49_p5_confirmed_candidate_gate_connection(r49_review_handoff_summary=handoff)
    assert r49.assert_p7_r49_p5_confirmed_candidate_gate_connection_contract(gate) is True
    return gate


def _undisposed_gate() -> dict[str, object]:
    return deepcopy(_cached_undisposed_gate())


def test_r49_r14_builds_p6_start_candidate_handoff_without_starting_p6() -> None:
    gate = _valid_gate()
    handoff = r49.build_p7_r49_p6_limited_human_readfeel_start_candidate_handoff(
        r49_p5_confirmed_candidate_gate_connection=gate,
    )
    assert r49.assert_p7_r49_p6_limited_human_readfeel_start_candidate_handoff_contract(handoff) is True

    assert handoff["schema_version"] == r49.P7_R49_P6_LIMITED_HUMAN_READFEEL_START_CANDIDATE_HANDOFF_SCHEMA_VERSION
    assert set(handoff) == set(r49.P7_R49_P6_LIMITED_HUMAN_READFEEL_START_CANDIDATE_HANDOFF_REQUIRED_FIELD_REFS)
    assert handoff["policy_section"] == "R49-14_p6_limited_human_readfeel_start_candidate_handoff"
    assert handoff["r46_p6_limited_human_readfeel_handoff_function_ref"] == "build_p6_limited_human_readfeel_handoff_material"
    assert handoff["r46_p6_limited_human_readfeel_handoff_contract_ref"] == "assert_p6_limited_human_readfeel_handoff_material_contract"
    assert handoff["r46_p6_limited_human_readfeel_handoff_schema_version"] == r49.P7_R46_P6_LIMITED_HUMAN_READFEEL_HANDOFF_SCHEMA_VERSION
    assert tuple(handoff["p6_review_families"]) == r49.P6_LIMITED_READFEEL_REVIEW_FAMILIES
    assert tuple(handoff["p6_no_connect_families"]) == r49.P6_NO_CONNECT_FAMILIES
    assert tuple(handoff["p6_rating_axes"]) == r49.P6_LIMITED_READFEEL_RATING_AXES
    assert handoff["p6_target_thresholds"] == dict(r49.P6_LIMITED_READFEEL_TARGETS)
    assert set(handoff["required_condition_refs"]) == set(r49.P7_R49_P6_START_CANDIDATE_REQUIRED_CONDITION_REFS)
    assert handoff["missing_requirement_refs"] == []
    assert handoff["failed_requirement_count"] == 0
    assert handoff["p5_human_blind_qa_confirmed_candidate"] is True
    assert handoff["p6_limited_human_readfeel_start_allowed_candidate"] is True
    assert handoff["p6_limited_human_readfeel_start_allowed"] is False
    assert handoff["p6_limited_human_readfeel_confirmed"] is False
    assert handoff["full_backend_suite_green_claim_used_for_p6_start_allowed"] is False
    assert handoff["p6_start_permission_granted_here"] is False
    assert handoff["p7_complete"] is False
    assert handoff["p8_start_allowed"] is False
    assert handoff["release_allowed"] is False
    assert tuple(handoff["implemented_steps"]) == r49.P7_R49_R14_IMPLEMENTED_STEPS
    assert tuple(handoff["not_yet_implemented_steps"]) == r49.P7_R49_R14_NOT_YET_IMPLEMENTED_STEPS
    assert handoff["next_required_step"] == r49.P7_R49_R14_NEXT_REQUIRED_STEP_REF
    _assert_no_body_question_or_permission_promotion(handoff)


def test_r49_r14_blocks_p6_start_candidate_when_p5_gate_is_not_candidate() -> None:
    gate = _repair_required_gate()
    handoff = r49.build_p7_r49_p6_limited_human_readfeel_start_candidate_handoff(
        r49_p5_confirmed_candidate_gate_connection=gate,
    )
    assert r49.assert_p7_r49_p6_limited_human_readfeel_start_candidate_handoff_contract(handoff) is True

    assert gate["p5_human_blind_qa_confirmed_candidate"] is False
    assert handoff["p6_limited_human_readfeel_start_allowed_candidate"] is False
    assert "p5_human_blind_qa_confirmed_candidate" in handoff["missing_requirement_refs"]
    assert "question_observation_repair_required_zero" in handoff["missing_requirement_refs"]
    assert handoff["p6_limited_human_readfeel_start_allowed"] is False
    assert handoff["release_allowed"] is False
    _assert_no_body_question_or_permission_promotion(handoff)


def test_r49_r14_keeps_p6_candidate_blocked_until_disposal_verified() -> None:
    gate = _undisposed_gate()
    handoff = r49.build_p7_r49_p6_limited_human_readfeel_start_candidate_handoff(
        r49_p5_confirmed_candidate_gate_connection=gate,
    )
    assert r49.assert_p7_r49_p6_limited_human_readfeel_start_candidate_handoff_contract(handoff) is True

    assert gate["p5_human_blind_qa_confirmed_candidate"] is False
    assert handoff["p6_limited_human_readfeel_start_allowed_candidate"] is False
    assert "disposal_verified_for_candidate" in handoff["missing_requirement_refs"]
    assert handoff["p6_limited_human_readfeel_start_allowed"] is False
    assert handoff["p8_start_allowed"] is False
    _assert_no_body_question_or_permission_promotion(handoff)


def test_r49_r15_builds_p8_question_design_material_candidate_handoff_without_starting_p8() -> None:
    r14 = r49.build_p7_r49_p6_limited_human_readfeel_start_candidate_handoff(
        r49_p5_confirmed_candidate_gate_connection=_valid_gate(),
    )
    handoff = r49.build_p7_r49_p8_question_design_material_candidate_handoff(
        r49_p6_limited_human_readfeel_start_candidate_handoff=r14,
    )
    assert r49.assert_p7_r49_p8_question_design_material_candidate_handoff_contract(handoff) is True

    assert handoff["schema_version"] == r49.P7_R49_P8_QUESTION_DESIGN_MATERIAL_CANDIDATE_HANDOFF_SCHEMA_VERSION
    assert set(handoff) == set(r49.P7_R49_P8_QUESTION_DESIGN_MATERIAL_CANDIDATE_HANDOFF_REQUIRED_FIELD_REFS)
    assert handoff["policy_section"] == "R49-15_p8_question_design_material_candidate_handoff"
    assert handoff["p8_question_design_material_candidate_handoff_ready"] is True
    assert handoff["p8_question_design_material_candidate"] is True
    assert handoff["p8_design_material_candidate_missing_requirement_refs"] == []
    assert handoff["p8_design_material_candidate_failed_requirement_count"] == 0
    assert handoff["question_observation_row_count"] == r49.P7_R49_REQUIRED_TOTAL_CASES
    assert handoff["question_observation_rows_complete"] is True
    assert handoff["question_may_reduce_overread_risk_count"] == 1
    assert handoff["no_question_needed_count"] == r49.P7_R49_REQUIRED_TOTAL_CASES - 1
    assert handoff["p8_design_material_candidate_row_count"] == r49.P7_R49_REQUIRED_TOTAL_CASES
    assert "p8_start_not_allowed_in_r49" in handoff["p8_start_blocker_refs"]
    assert handoff["question_text_included"] is False
    assert handoff["draft_question_text_included"] is False
    assert handoff["reviewer_free_text_included"] is False
    assert handoff["raw_input_or_comment_text_included"] is False
    assert handoff["returned_surface_included"] is False
    assert handoff["local_path_or_body_hash_included"] is False
    assert handoff["question_trigger_logic_implemented_here"] is False
    assert handoff["api_db_rn_response_key_changed_here"] is False
    assert handoff["p8_detail_design_allowed_here"] is False
    assert handoff["p8_implementation_spec_finalized_here"] is False
    assert handoff["p8_start_allowed"] is False
    assert handoff["release_allowed"] is False
    assert tuple(handoff["implemented_steps"]) == r49.P7_R49_R15_IMPLEMENTED_STEPS
    assert tuple(handoff["not_yet_implemented_steps"]) == r49.P7_R49_R15_NOT_YET_IMPLEMENTED_STEPS
    assert handoff["next_required_step"] == r49.P7_R49_R15_NEXT_REQUIRED_STEP_REF
    _assert_no_body_question_or_permission_promotion(handoff)


def _incomplete_question_summary_gate() -> dict[str, object]:
    summary = r49.build_p7_r49_question_need_observation_summary_bodyfree(
        r49_rating_question_observation_consistency_guard=_r9_guard(),
        question_need_observation_rows=_question_rows_for_all_cases()[:-1],
    )
    connection = r49.build_p7_r49_disposal_receipt_connection(
        r49_question_need_observation_summary=summary,
    )
    freeze = r49.build_p7_r49_r10_r11_question_summary_disposal_connection_freeze(
        r49_question_need_observation_summary=summary,
        r49_disposal_receipt_connection=connection,
    )
    handoff = r49.build_p7_r49_review_handoff_summary_bodyfree(
        r10_r11_question_summary_disposal_connection_freeze=freeze,
        rating_rows=_pass_rating_rows_for_all_cases(),
    )
    gate = r49.build_p7_r49_p5_confirmed_candidate_gate_connection(r49_review_handoff_summary=handoff)
    assert r49.assert_p7_r49_p5_confirmed_candidate_gate_connection_contract(gate) is True
    return gate


def test_r49_r15_keeps_material_non_candidate_when_question_summary_is_incomplete() -> None:
    r14 = r49.build_p7_r49_p6_limited_human_readfeel_start_candidate_handoff(
        r49_p5_confirmed_candidate_gate_connection=_incomplete_question_summary_gate(),
    )
    handoff = r49.build_p7_r49_p8_question_design_material_candidate_handoff(
        r49_p6_limited_human_readfeel_start_candidate_handoff=r14,
    )
    assert r49.assert_p7_r49_p8_question_design_material_candidate_handoff_contract(handoff) is True

    assert handoff["p8_question_design_material_candidate"] is False
    assert handoff["question_observation_rows_complete"] is False
    assert handoff["p8_design_material_candidate_row_count"] == r49.P7_R49_REQUIRED_TOTAL_CASES - 1
    assert "question_observation_rows_complete" in handoff["p8_design_material_candidate_missing_requirement_refs"]
    assert "p8_question_design_material_candidate" in handoff["p8_design_material_candidate_missing_requirement_refs"]
    assert "question_observation_rows_incomplete" in handoff["p8_start_blocker_refs"]
    assert handoff["p8_start_allowed"] is False
    assert handoff["release_allowed"] is False
    _assert_no_body_question_or_permission_promotion(handoff)


def test_r49_r14_r15_freeze_combines_candidates_without_promoting_permissions() -> None:
    r14 = r49.build_p7_r49_p6_limited_human_readfeel_start_candidate_handoff(
        r49_p5_confirmed_candidate_gate_connection=_valid_gate(),
    )
    r15 = r49.build_p7_r49_p8_question_design_material_candidate_handoff(
        r49_p6_limited_human_readfeel_start_candidate_handoff=r14,
    )
    freeze = r49.build_p7_r49_r14_r15_p6_p8_candidate_handoff_freeze(
        r49_p6_limited_human_readfeel_start_candidate_handoff=r14,
        r49_p8_question_design_material_candidate_handoff=r15,
    )
    assert r49.assert_p7_r49_r14_r15_p6_p8_candidate_handoff_freeze_contract(freeze) is True

    assert freeze["schema_version"] == r49.P7_R49_R14_R15_P6_P8_CANDIDATE_HANDOFF_FREEZE_SCHEMA_VERSION
    assert set(freeze) == set(r49.P7_R49_R14_R15_P6_P8_CANDIDATE_HANDOFF_FREEZE_REQUIRED_FIELD_REFS)
    assert freeze["policy_section"] == "R49-14_R49-15_p6_p8_candidate_handoff_freeze"
    assert freeze["p5_human_blind_qa_confirmed_candidate"] is True
    assert freeze["p6_limited_human_readfeel_start_allowed_candidate"] is True
    assert freeze["p6_limited_human_readfeel_start_allowed"] is False
    assert freeze["p6_limited_human_readfeel_confirmed"] is False
    assert freeze["p8_question_design_material_candidate"] is True
    assert freeze["p8_detail_design_allowed_here"] is False
    assert freeze["p8_implementation_spec_finalized_here"] is False
    assert freeze["question_trigger_logic_implemented_here"] is False
    assert freeze["api_db_rn_response_key_changed_here"] is False
    assert freeze["p7_complete"] is False
    assert freeze["p8_start_allowed"] is False
    assert freeze["release_allowed"] is False
    assert tuple(freeze["implemented_steps"]) == r49.P7_R49_R15_IMPLEMENTED_STEPS
    assert tuple(freeze["not_yet_implemented_steps"]) == r49.P7_R49_R15_NOT_YET_IMPLEMENTED_STEPS
    assert freeze["next_required_step"] == r49.P7_R49_R15_NEXT_REQUIRED_STEP_REF
    _assert_no_body_question_or_permission_promotion(freeze)


@pytest.mark.parametrize(
    "leaky_key,secret",
    [
        ("raw_input", SECRET_INPUT),
        ("returned_emlis_surface", SECRET_SURFACE),
        ("reviewer_free_text", SECRET_REVIEWER),
        ("question_text", SECRET_QUESTION),
    ],
)
def test_r49_r14_rejects_body_or_question_text_leaks(leaky_key: str, secret: str) -> None:
    gate = _valid_gate()
    gate[leaky_key] = secret
    with pytest.raises(ValueError):
        r49.build_p7_r49_p6_limited_human_readfeel_start_candidate_handoff(
            r49_p5_confirmed_candidate_gate_connection=gate,
        )
