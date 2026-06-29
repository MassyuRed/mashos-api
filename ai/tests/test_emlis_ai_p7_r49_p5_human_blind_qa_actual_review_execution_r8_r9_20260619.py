# -*- coding: utf-8 -*-
from __future__ import annotations

import json
from copy import deepcopy
from functools import lru_cache

import pytest

import emlis_ai_p7_r48_p5_human_blind_qa_actual_review_packet as r48
import emlis_ai_p7_r49_p5_human_blind_qa_actual_review_execution as r49

SECRET_INPUT = "R49 secret raw input must not enter body-free R8/R9 material"
SECRET_SURFACE = "R49 returned Emlis surface must not enter body-free R8/R9 material"
SECRET_REVIEWER = "R49 reviewer free text must not enter body-free R8/R9 material"
SECRET_QUESTION = "R49 draft question text must not enter body-free R8/R9 material"


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
    ):
        assert forbidden_true not in dumped.lower()


@lru_cache(maxsize=1)
def _cached_r7_freeze() -> tuple[dict[str, object], dict[str, object], dict[str, object]]:
    r2 = r49.build_p7_r49_r48_case_matrix_handoff_validation()
    assert r49.assert_p7_r49_r48_case_matrix_handoff_validation_contract(r2) is True
    r3 = r49.build_p7_r49_local_only_actual_packet_generation_preflight(
        r49_r48_case_matrix_handoff_validation=r2,
        local_review_root="/tmp/cocolon_r49_r8_r9_valid_external_local_review_root",
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
    freeze = r49.build_p7_r49_question_need_observation_row_schema_enum_freeze(
        r49_blocker_execution_blocker_ingestion=ingestion,
    )
    assert r49.assert_p7_r49_question_need_observation_row_schema_enum_freeze_contract(freeze) is True
    return (r2, connection, freeze)


def _r2() -> dict[str, object]:
    return deepcopy(_cached_r7_freeze()[0])


def _r7() -> dict[str, object]:
    return deepcopy(_cached_r7_freeze()[2])


def _first_case() -> dict[str, object]:
    return deepcopy(_r2()["case_manifest_rows"][0])


def _pass_rating_row(case_row: dict[str, object]) -> dict[str, object]:
    return r49.normalize_p7_r49_p5_rating_row_via_r48_bodyfree(
        case_manifest_row=case_row,
        review_session_id=r49.P7_R49_DEFAULT_REVIEW_SESSION_ID,
        review_result={
            "axis_scores": {axis: 1.0 for axis in r48.P5_HUMAN_BLIND_QA_RATING_AXES},
            "verdict": "PASS",
            "sanitized_reason_ids": [],
            "blocker_ids": [],
        },
        body_removed=True,
    )


def _repair_rating_row(case_row: dict[str, object]) -> dict[str, object]:
    axis_scores = {axis: 1.0 for axis in r48.P5_HUMAN_BLIND_QA_RATING_AXES}
    axis_scores["history_connection_naturalness"] = 0.1
    return r49.normalize_p7_r49_p5_rating_row_via_r48_bodyfree(
        case_manifest_row=case_row,
        review_session_id=r49.P7_R49_DEFAULT_REVIEW_SESSION_ID,
        review_result={
            "axis_scores": axis_scores,
            "verdict": "REPAIR_REQUIRED",
            "sanitized_reason_ids": ["p5_history_connection_too_generic"],
            "blocker_ids": ["p5_history_connection_too_generic"],
        },
        body_removed=True,
    )


def test_r49_r8_freezes_question_need_observation_row_normalizer_without_claiming_actual_rows() -> None:
    normalizer = r49.build_p7_r49_question_need_observation_row_normalizer(
        r49_question_need_observation_row_schema_enum_freeze=_r7(),
    )
    assert r49.assert_p7_r49_question_need_observation_row_normalizer_contract(normalizer) is True

    assert normalizer["schema_version"] == r49.P7_R49_QUESTION_NEED_OBSERVATION_ROW_NORMALIZER_SCHEMA_VERSION
    assert set(normalizer) == set(r49.P7_R49_QUESTION_NEED_OBSERVATION_ROW_NORMALIZER_REQUIRED_FIELD_REFS)
    assert normalizer["policy_section"] == "R49-8_question_need_observation_row_normalizer"
    assert normalizer["question_need_observation_row_schema_version"] == r49.P7_R49_QUESTION_NEED_OBSERVATION_ROW_BODYFREE_SCHEMA_VERSION
    assert normalizer["question_need_observation_row_normalizer_function_ref"] == "normalize_p7_r49_question_need_observation_row_bodyfree"
    assert tuple(normalizer["question_need_observation_row_required_field_refs"]) == r49.P7_R49_QUESTION_NEED_OBSERVATION_ROW_REQUIRED_FIELD_REFS
    assert tuple(normalizer["question_need_observation_row_forbidden_field_refs"]) == r49.P7_R49_QUESTION_NEED_OBSERVATION_ROW_FORBIDDEN_FIELD_REFS
    assert tuple(normalizer["question_need_primary_class_refs"]) == r49.P7_R49_QUESTION_NEED_PRIMARY_CLASS_REFS
    assert normalizer["normalizer_ready"] is True
    assert normalizer["question_need_observation_rows_must_be_bodyfree"] is True
    assert normalizer["body_removed_required_for_question_observation_row"] is True
    assert normalizer["question_text_included_allowed"] is False
    assert normalizer["draft_question_text_included_allowed"] is False
    assert normalizer["reviewer_free_text_included_allowed"] is False
    assert normalizer["p8_question_implementation_spec_finalized_here"] is False
    assert normalizer["question_trigger_logic_implemented_here"] is False
    assert normalizer["api_db_rn_response_key_changed_here"] is False
    assert normalizer["question_need_observation_row_normalizer_implemented_here"] is True
    assert normalizer["question_need_observation_row_instances_materialized_here"] is False
    assert normalizer["actual_question_need_observation_rows_materialized_here"] is False
    assert tuple(normalizer["implemented_steps"]) == r49.P7_R49_R8_IMPLEMENTED_STEPS
    assert tuple(normalizer["not_yet_implemented_steps"]) == r49.P7_R49_R8_NOT_YET_IMPLEMENTED_STEPS
    assert normalizer["next_required_step"] == r49.P7_R49_R8_NEXT_REQUIRED_STEP_REF
    _assert_no_body_question_or_release_promotion(normalizer)


def test_r49_r8_normalizes_bodyfree_question_need_observation_rows_and_rejects_question_text() -> None:
    case_row = _first_case()
    row = r49.normalize_p7_r49_question_need_observation_row_bodyfree(
        case_manifest_row=case_row,
        question_observation_result={
            "question_need_primary_class": "question_may_reduce_overread_risk",
            "ambiguity_kind_refs": ["missing_target"],
            "sanitized_reason_ids": ["question_may_reduce_overread_risk"],
        },
    )
    assert r49.assert_p7_r49_question_need_observation_row_bodyfree_contract(row) is True
    assert row["schema_version"] == r49.P7_R49_QUESTION_NEED_OBSERVATION_ROW_BODYFREE_SCHEMA_VERSION
    assert set(row) == set(r49.P7_R49_QUESTION_NEED_OBSERVATION_ROW_REQUIRED_FIELD_REFS)
    assert row["packet_ref_id"] == case_row["packet_ref_id"]
    assert row["blind_case_id"] == case_row["blind_case_id"]
    assert row["case_ref_id"] == case_row["case_ref_id"]
    assert row["family"] == case_row["family"]
    assert row["case_role"] == case_row["case_role"]
    assert row["observation_stage"] == r49.P7_R49_QUESTION_NEED_OBSERVATION_STAGE_REF
    assert row["question_need_primary_class"] == "question_may_reduce_overread_risk"
    assert row["ambiguity_kind_refs"] == ["missing_target"]
    assert row["one_question_fit_ref"] == "fits_one_question"
    assert row["plan_candidate_flags"]["p8_design_material_candidate"] is True
    assert row["plan_candidate_flags"]["p8_implementation_spec_finalized_here"] is False
    assert row["repair_required_refs"] == ["no_repair_required"]
    assert row["question_text_included"] is False
    assert row["draft_question_text_included"] is False
    assert row["reviewer_free_text_included"] is False
    assert row["body_removed"] is True
    assert row["body_free"] is True
    _assert_no_body_question_or_release_promotion(row)

    no_question = r49.normalize_p7_r49_question_need_observation_row_bodyfree(
        case_manifest_row=case_row,
        question_observation_result={
            "question_need_primary_class": "no_question_needed_emlis_can_observe",
            "sanitized_reason_ids": ["no_question_needed_emlis_can_observe"],
        },
    )
    assert no_question["ambiguity_kind_refs"] == ["no_material_ambiguity"]
    assert no_question["one_question_fit_ref"] == "not_needed"
    assert no_question["repair_required_refs"] == ["no_repair_required"]
    assert no_question["plan_candidate_flags"]["p8_design_material_candidate"] is True

    with pytest.raises(ValueError):
        r49.normalize_p7_r49_question_need_observation_row_bodyfree(
            case_manifest_row=case_row,
            question_observation_result={
                "question_need_primary_class": "question_may_reduce_overread_risk",
                "ambiguity_kind_refs": ["missing_target"],
                "question_text": SECRET_QUESTION,
            },
        )
    with pytest.raises(ValueError):
        r49.normalize_p7_r49_question_need_observation_row_bodyfree(
            case_manifest_row=case_row,
            question_observation_result={
                "question_need_primary_class": "question_may_reduce_overread_risk",
                "ambiguity_kind_refs": ["missing_target"],
            },
            body_removed=False,
        )


def test_r49_r8_rejects_inconsistent_question_observation_class_fit_and_repair_refs() -> None:
    case_row = _first_case()
    with pytest.raises(ValueError):
        r49.normalize_p7_r49_question_need_observation_row_bodyfree(
            case_manifest_row=case_row,
            question_observation_result={
                "question_need_primary_class": "question_may_reduce_overread_risk",
                "ambiguity_kind_refs": ["missing_target"],
                "one_question_fit_ref": "repair_required_not_question",
            },
        )
    with pytest.raises(ValueError):
        r49.normalize_p7_r49_question_need_observation_row_bodyfree(
            case_manifest_row=case_row,
            question_observation_result={
                "question_need_primary_class": "not_question_p5_surface_repair_required",
                "one_question_fit_ref": "repair_required_not_question",
                "repair_required_refs": ["no_repair_required"],
            },
        )
    with pytest.raises(ValueError):
        r49.normalize_p7_r49_question_need_observation_row_bodyfree(
            case_manifest_row=case_row,
            question_observation_result={
                "question_need_primary_class": "not_question_gate_boundary_required",
                "one_question_fit_ref": "repair_required_not_question",
                "repair_required_refs": ["gate_boundary_repair_required"],
                "plan_candidate_flags": {"p8_design_material_candidate": True},
            },
        )


def test_r49_r9_freezes_rating_question_observation_consistency_guard_without_advancing_to_summary() -> None:
    normalizer = r49.build_p7_r49_question_need_observation_row_normalizer(
        r49_question_need_observation_row_schema_enum_freeze=_r7(),
    )
    guard = r49.build_p7_r49_rating_question_observation_consistency_guard(
        r49_question_need_observation_row_normalizer=normalizer,
    )
    assert r49.assert_p7_r49_rating_question_observation_consistency_guard_contract(guard) is True

    assert guard["schema_version"] == r49.P7_R49_RATING_QUESTION_OBSERVATION_CONSISTENCY_GUARD_SCHEMA_VERSION
    assert set(guard) == set(r49.P7_R49_RATING_QUESTION_OBSERVATION_CONSISTENCY_GUARD_REQUIRED_FIELD_REFS)
    assert guard["policy_section"] == "R49-9_rating_vs_question_observation_consistency_guard"
    assert guard["rating_question_consistency_guard_ready"] is True
    assert guard["p5_weakness_must_not_be_hidden_by_questions"] is True
    assert guard["rating_and_question_observation_ids_must_match"] is True
    assert guard["pass_rating_forbids_not_question_repair_primary_class"] is True
    assert guard["repair_or_red_rating_forbids_question_candidate_primary_only"] is True
    assert guard["repair_required_not_question_requires_repair_ref"] is True
    assert guard["insufficient_material_requires_execution_blocker_row"] is True
    assert guard["question_candidate_cannot_clear_readfeel_blocker"] is True
    assert guard["consistency_guard_function_ref"] == "assert_p7_r49_rating_vs_question_observation_consistency"
    assert guard["actual_rating_rows_materialized_here"] is False
    assert guard["actual_question_need_observation_rows_materialized_here"] is False
    assert guard["p8_start_allowed"] is False
    assert guard["release_allowed"] is False
    assert tuple(guard["implemented_steps"]) == r49.P7_R49_R9_IMPLEMENTED_STEPS
    assert tuple(guard["not_yet_implemented_steps"]) == r49.P7_R49_R9_NOT_YET_IMPLEMENTED_STEPS
    assert guard["next_required_step"] == r49.P7_R49_R9_NEXT_REQUIRED_STEP_REF
    _assert_no_body_question_or_release_promotion(guard)


def test_r49_r9_rating_and_question_observation_consistency_guard_rejects_hiding_p5_weakness_with_questions() -> None:
    case_row = _first_case()
    pass_rating = _pass_rating_row(case_row)
    no_question = r49.normalize_p7_r49_question_need_observation_row_bodyfree(
        case_manifest_row=case_row,
        question_observation_result={
            "question_need_primary_class": "no_question_needed_emlis_can_observe",
            "sanitized_reason_ids": ["no_question_needed_emlis_can_observe"],
        },
    )
    assert r49.assert_p7_r49_rating_vs_question_observation_consistency(
        rating_row=pass_rating,
        question_need_observation_row=no_question,
    ) is True

    not_question_repair = r49.normalize_p7_r49_question_need_observation_row_bodyfree(
        case_manifest_row=case_row,
        question_observation_result={
            "question_need_primary_class": "not_question_p5_surface_repair_required",
            "repair_required_refs": ["p5_surface_repair_required"],
            "sanitized_reason_ids": ["not_question_p5_surface_repair_required"],
        },
    )
    with pytest.raises(ValueError):
        r49.assert_p7_r49_rating_vs_question_observation_consistency(
            rating_row=pass_rating,
            question_need_observation_row=not_question_repair,
        )

    repair_rating = _repair_rating_row(case_row)
    question_candidate = r49.normalize_p7_r49_question_need_observation_row_bodyfree(
        case_manifest_row=case_row,
        question_observation_result={
            "question_need_primary_class": "question_may_reduce_overread_risk",
            "ambiguity_kind_refs": ["missing_target"],
            "sanitized_reason_ids": ["question_may_reduce_overread_risk"],
        },
    )
    with pytest.raises(ValueError):
        r49.assert_p7_r49_rating_vs_question_observation_consistency(
            rating_row=repair_rating,
            question_need_observation_row=question_candidate,
        )

    shifted_case = dict(case_row)
    shifted_case["blind_case_id"] = "p7r49-r8r9-different-blind-case"
    shifted_question = r49.normalize_p7_r49_question_need_observation_row_bodyfree(
        case_manifest_row=shifted_case,
        question_observation_result={
            "question_need_primary_class": "no_question_needed_emlis_can_observe",
            "sanitized_reason_ids": ["no_question_needed_emlis_can_observe"],
        },
    )
    with pytest.raises(ValueError):
        r49.assert_p7_r49_rating_vs_question_observation_consistency(
            rating_row=pass_rating,
            question_need_observation_row=shifted_question,
        )


def test_r49_r9_insufficient_material_question_observation_requires_execution_blocker_row() -> None:
    case_row = _first_case()
    insufficient = r49.normalize_p7_r49_question_need_observation_row_bodyfree(
        case_manifest_row=case_row,
        question_observation_result={
            "question_need_primary_class": "insufficient_material_execution_blocker",
            "sanitized_reason_ids": ["insufficient_material_execution_blocker"],
        },
    )
    with pytest.raises(ValueError):
        r49.assert_p7_r49_rating_vs_question_observation_consistency(
            question_need_observation_row=insufficient,
            execution_blocker_rows=[],
        )

    execution_row = r49.normalize_p7_r49_execution_blocker_row_via_r48_bodyfree(
        case_manifest_row=case_row,
        execution_blocker_id="r49_question_need_observation_rows_missing",
        review_session_id=r49.P7_R49_DEFAULT_REVIEW_SESSION_ID,
    )
    assert r49.assert_p7_r49_rating_vs_question_observation_consistency(
        question_need_observation_row=insufficient,
        execution_blocker_rows=[execution_row],
    ) is True
    with pytest.raises(ValueError):
        r49.assert_p7_r49_rating_vs_question_observation_consistency(
            rating_row=_pass_rating_row(case_row),
            question_need_observation_row=insufficient,
            execution_blocker_rows=[execution_row],
        )


def test_r49_r8_r9_combined_freeze_keeps_next_step_at_r10_and_does_not_claim_actual_review_rows() -> None:
    normalizer = r49.build_p7_r49_question_need_observation_row_normalizer(
        r49_question_need_observation_row_schema_enum_freeze=_r7(),
    )
    guard = r49.build_p7_r49_rating_question_observation_consistency_guard(
        r49_question_need_observation_row_normalizer=normalizer,
    )
    combined = r49.build_p7_r49_r8_r9_question_normalizer_consistency_guard_freeze(
        r49_question_need_observation_row_normalizer=normalizer,
        r49_rating_question_observation_consistency_guard=guard,
    )
    assert r49.assert_p7_r49_r8_r9_question_normalizer_consistency_guard_freeze_contract(combined) is True

    assert combined["schema_version"] == r49.P7_R49_R8_R9_QUESTION_NORMALIZER_CONSISTENCY_GUARD_FREEZE_SCHEMA_VERSION
    assert set(combined) == set(r49.P7_R49_R8_R9_QUESTION_NORMALIZER_CONSISTENCY_GUARD_FREEZE_REQUIRED_FIELD_REFS)
    assert combined["policy_section"] == "R49-8_R49-9_question_normalizer_consistency_guard_freeze"
    assert combined["question_need_observation_row_normalizer_implemented_here"] is True
    assert combined["rating_question_consistency_guard_ready"] is True
    assert combined["p5_weakness_must_not_be_hidden_by_questions"] is True
    assert combined["actual_human_review_run_here"] is False
    assert combined["actual_rating_rows_materialized_here"] is False
    assert combined["actual_blocker_rows_materialized_here"] is False
    assert combined["actual_execution_blocker_rows_materialized_here"] is False
    assert combined["actual_question_need_observation_rows_materialized_here"] is False
    assert combined["actual_question_need_observation_summary_materialized_here"] is False
    assert tuple(combined["implemented_steps"]) == r49.P7_R49_R9_IMPLEMENTED_STEPS
    assert tuple(combined["not_yet_implemented_steps"]) == r49.P7_R49_R9_NOT_YET_IMPLEMENTED_STEPS
    assert combined["next_required_step"] == r49.P7_R49_R9_NEXT_REQUIRED_STEP_REF
    _assert_no_body_question_or_release_promotion(combined)
