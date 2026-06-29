# -*- coding: utf-8 -*-
from __future__ import annotations

import json
from copy import deepcopy
from functools import lru_cache

import pytest

import emlis_ai_p7_r48_p5_human_blind_qa_actual_review_packet as r48
import emlis_ai_p7_r49_p5_human_blind_qa_actual_review_execution as r49

SECRET_INPUT = "R49 secret raw input must not enter body-free R6/R7 material"
SECRET_SURFACE = "R49 returned Emlis surface must not enter body-free R6/R7 material"
SECRET_REVIEWER = "R49 reviewer free text must not enter body-free R6/R7 material"
SECRET_QUESTION = "R49 draft question text must not enter body-free R6/R7 material"


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
def _cached_r5_connection() -> tuple[dict[str, object], dict[str, object], dict[str, object]]:
    r2 = r49.build_p7_r49_r48_case_matrix_handoff_validation()
    assert r49.assert_p7_r49_r48_case_matrix_handoff_validation_contract(r2) is True
    r3 = r49.build_p7_r49_local_only_actual_packet_generation_preflight(
        r49_r48_case_matrix_handoff_validation=r2,
        local_review_root="/tmp/cocolon_r49_r6_r7_valid_external_local_review_root",
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
    return (r2, protocol, connection)


def _r2() -> dict[str, object]:
    return deepcopy(_cached_r5_connection()[0])


def _r5() -> dict[str, object]:
    return deepcopy(_cached_r5_connection()[2])


def test_r49_r6_freezes_blocker_execution_blocker_ingestion_to_r48_bodyfree_builders() -> None:
    ingestion = r49.build_p7_r49_blocker_execution_blocker_ingestion(
        r49_rating_row_ingestion_r48_normalizer_connection=_r5(),
    )
    assert r49.assert_p7_r49_blocker_execution_blocker_ingestion_contract(ingestion) is True

    assert ingestion["schema_version"] == r49.P7_R49_BLOCKER_EXECUTION_BLOCKER_INGESTION_SCHEMA_VERSION
    assert set(ingestion) == set(r49.P7_R49_BLOCKER_EXECUTION_BLOCKER_INGESTION_REQUIRED_FIELD_REFS)
    assert ingestion["policy_section"] == "R49-6_blocker_execution_blocker_ingestion"
    assert ingestion["r5_rating_ingestion_schema_version"] == r49.P7_R49_RATING_ROW_INGESTION_R48_NORMALIZER_CONNECTION_SCHEMA_VERSION
    assert ingestion["r48_blocker_execution_blocker_row_builder_schema_version"] == r48.P7_R48_BLOCKER_EXECUTION_BLOCKER_ROW_BUILDER_SCHEMA_VERSION
    assert ingestion["r48_blocker_row_bodyfree_schema_version"] == r48.P7_R48_P5_BLOCKER_ROW_BODYFREE_SCHEMA_VERSION
    assert ingestion["r48_execution_blocker_row_bodyfree_schema_version"] == r48.P7_R48_P5_EXECUTION_BLOCKER_ROW_BODYFREE_SCHEMA_VERSION
    assert ingestion["r48_blocker_row_builder_function_ref"] == "build_p7_r48_p5_blocker_row_bodyfree"
    assert ingestion["r48_execution_blocker_row_builder_function_ref"] == "build_p7_r48_p5_execution_blocker_row_bodyfree"
    assert ingestion["r48_blocker_row_contract_ref"] == "assert_p7_r48_p5_blocker_row_bodyfree_contract"
    assert ingestion["r48_execution_blocker_row_contract_ref"] == "assert_p7_r48_p5_execution_blocker_row_bodyfree_contract"
    assert tuple(ingestion["r48_blocker_row_required_field_refs"]) == r48.P7_R48_P5_BLOCKER_ROW_REQUIRED_FIELD_REFS
    assert tuple(ingestion["r48_execution_blocker_row_required_field_refs"]) == r48.P7_R48_P5_EXECUTION_BLOCKER_ROW_REQUIRED_FIELD_REFS
    assert tuple(ingestion["readfeel_blocker_id_refs"]) == r48.P7_R48_READFEEL_BLOCKER_ID_REFS
    assert tuple(ingestion["r49_execution_blocker_id_refs"]) == r49.P7_R49_EXECUTION_BLOCKER_ID_REFS
    assert set(r48.P7_R48_EXECUTION_BLOCKER_ID_REFS) <= set(ingestion["r48_execution_blocker_id_refs"])
    assert ingestion["r49_to_r48_execution_blocker_id_map"] == r49.P7_R49_TO_R48_EXECUTION_BLOCKER_ID_MAP
    assert set(ingestion["r49_to_r48_execution_blocker_id_map"]) == set(r49.P7_R49_EXECUTION_BLOCKER_ID_REFS)
    assert set(ingestion["r49_to_r48_execution_blocker_id_map"].values()) <= set(r48.P7_R48_EXECUTION_BLOCKER_ID_REFS)

    assert ingestion["blocker_execution_ingestion_ready"] is True
    assert ingestion["blocker_rows_must_be_r48_bodyfree"] is True
    assert ingestion["execution_blocker_rows_must_be_r48_bodyfree"] is True
    assert ingestion["r48_builder_connection_fixed"] is True
    assert ingestion["readfeel_and_execution_blockers_separated"] is True
    assert ingestion["execution_blockers_do_not_assign_readfeel_verdict"] is True
    assert ingestion["review_execution_blockers_do_not_create_p5_readfeel_red"] is True
    assert ingestion["question_observation_ingestion_done_here"] is False
    assert ingestion["actual_blocker_rows_materialized_here"] is False
    assert ingestion["actual_execution_blocker_rows_materialized_here"] is False
    assert tuple(ingestion["implemented_steps"]) == r49.P7_R49_R6_IMPLEMENTED_STEPS
    assert tuple(ingestion["not_yet_implemented_steps"]) == r49.P7_R49_R6_NOT_YET_IMPLEMENTED_STEPS
    assert ingestion["next_required_step"] == r49.P7_R49_R6_NEXT_REQUIRED_STEP_REF
    _assert_no_body_question_or_release_promotion(ingestion)


def test_r49_r6_normalizes_readfeel_blocker_and_execution_blocker_rows_without_mixing_classes() -> None:
    case_row = _r2()["case_manifest_rows"][0]
    readfeel_row = r49.normalize_p7_r49_p5_readfeel_blocker_row_via_r48_bodyfree(
        case_manifest_row=case_row,
        blocker_id="p5_history_connection_too_generic",
        review_session_id="p7_r49_review_session_for_blocker_ingestion",
        blocker_kind="REPAIR_REQUIRED",
        sanitized_reason_ids=["p5_history_connection_too_generic"],
        body_removed=True,
    )
    assert r48.assert_p7_r48_p5_blocker_row_bodyfree_contract(readfeel_row) is True
    assert readfeel_row["schema_version"] == r48.P7_R48_P5_BLOCKER_ROW_BODYFREE_SCHEMA_VERSION
    assert set(readfeel_row) == set(r48.P7_R48_P5_BLOCKER_ROW_REQUIRED_FIELD_REFS)
    assert readfeel_row["blocker_id"] == "p5_history_connection_too_generic"
    assert readfeel_row["blocker_kind"] != "EXECUTION_BLOCKER"
    assert readfeel_row["reviewer_free_text_included"] is False
    assert readfeel_row["body_removed"] is True
    assert readfeel_row["body_free"] is True
    _assert_no_body_question_or_release_promotion(readfeel_row)

    execution_row = r49.normalize_p7_r49_execution_blocker_row_via_r48_bodyfree(
        case_manifest_row=case_row,
        execution_blocker_id="r49_review_session_blocked_missing_local_root",
        review_session_id="p7_r49_review_session_for_blocker_ingestion",
    )
    assert r48.assert_p7_r48_p5_execution_blocker_row_bodyfree_contract(execution_row) is True
    assert execution_row["schema_version"] == r48.P7_R48_P5_EXECUTION_BLOCKER_ROW_BODYFREE_SCHEMA_VERSION
    assert set(execution_row) == set(r48.P7_R48_P5_EXECUTION_BLOCKER_ROW_REQUIRED_FIELD_REFS)
    assert execution_row["execution_blocker_id"] == "review_packet_generation_blocked_missing_local_root"
    assert execution_row["execution_blocker_kind"] == "GENERATION"
    assert execution_row["readfeel_verdict_not_assigned"] is True
    assert execution_row["body_free"] is True
    _assert_no_body_question_or_release_promotion(execution_row)

    with pytest.raises(ValueError):
        r49.normalize_p7_r49_p5_readfeel_blocker_row_via_r48_bodyfree(
            case_manifest_row=case_row,
            blocker_id="r49_review_session_blocked_missing_local_root",
        )
    with pytest.raises(ValueError):
        r49.normalize_p7_r49_execution_blocker_row_via_r48_bodyfree(
            case_manifest_row=case_row,
            execution_blocker_id="p5_history_connection_too_generic",
        )


def test_r49_r7_freezes_question_need_observation_row_schema_and_enums_without_question_implementation() -> None:
    ingestion = r49.build_p7_r49_blocker_execution_blocker_ingestion(r49_rating_row_ingestion_r48_normalizer_connection=_r5())
    freeze = r49.build_p7_r49_question_need_observation_row_schema_enum_freeze(
        r49_blocker_execution_blocker_ingestion=ingestion,
    )
    assert r49.assert_p7_r49_question_need_observation_row_schema_enum_freeze_contract(freeze) is True

    assert freeze["schema_version"] == r49.P7_R49_QUESTION_NEED_OBSERVATION_ROW_SCHEMA_ENUM_FREEZE_SCHEMA_VERSION
    assert set(freeze) == set(r49.P7_R49_QUESTION_NEED_OBSERVATION_ROW_SCHEMA_ENUM_FREEZE_REQUIRED_FIELD_REFS)
    assert freeze["policy_section"] == "R49-7_question_need_observation_row_schema_enum_freeze"
    assert freeze["question_need_observation_row_schema_version"] == r49.P7_R49_QUESTION_NEED_OBSERVATION_ROW_BODYFREE_SCHEMA_VERSION
    assert freeze["question_need_observation_summary_schema_version"] == r49.P7_R49_QUESTION_NEED_OBSERVATION_SUMMARY_BODYFREE_SCHEMA_VERSION
    assert freeze["observation_stage_ref"] == r49.P7_R49_QUESTION_NEED_OBSERVATION_STAGE_REF
    assert tuple(freeze["question_need_observation_row_required_field_refs"]) == r49.P7_R49_QUESTION_NEED_OBSERVATION_ROW_REQUIRED_FIELD_REFS
    assert tuple(freeze["question_need_observation_row_forbidden_field_refs"]) == r49.P7_R49_QUESTION_NEED_OBSERVATION_ROW_FORBIDDEN_FIELD_REFS
    assert tuple(freeze["question_need_primary_class_refs"]) == r49.P7_R49_QUESTION_NEED_PRIMARY_CLASS_REFS
    assert tuple(freeze["ambiguity_kind_refs"]) == r49.P7_R49_AMBIGUITY_KIND_REFS
    assert tuple(freeze["one_question_fit_refs"]) == r49.P7_R49_ONE_QUESTION_FIT_REFS
    assert tuple(freeze["repair_required_ref_refs"]) == r49.P7_R49_REPAIR_REQUIRED_REF_REFS
    assert tuple(freeze["plan_candidate_flag_refs"]) == r49.P7_R49_PLAN_CANDIDATE_FLAG_REFS

    assert freeze["enum_refs_unique"] is True
    assert freeze["primary_class_refs_cover_repair_and_execution_boundaries"] is True
    assert freeze["plan_candidate_flags_are_overlay_not_primary_required"] is True
    assert "not_question_emlis_readfeel_repair_required" in freeze["question_need_primary_class_refs"]
    assert "not_question_p5_surface_repair_required" in freeze["question_need_primary_class_refs"]
    assert "not_question_gate_boundary_required" in freeze["question_need_primary_class_refs"]
    assert "insufficient_material_execution_blocker" in freeze["question_need_primary_class_refs"]
    assert "plus_single_question_candidate_later" in freeze["plan_candidate_flag_refs"]
    assert "premium_deep_dive_candidate_later" in freeze["plan_candidate_flag_refs"]

    assert freeze["question_text_allowed"] is False
    assert freeze["draft_question_text_allowed"] is False
    assert freeze["reviewer_free_text_allowed"] is False
    assert freeze["raw_input_allowed"] is False
    assert freeze["raw_answer_allowed"] is False
    assert freeze["comment_text_body_allowed"] is False
    assert freeze["returned_surface_allowed"] is False
    assert freeze["local_path_allowed"] is False
    assert freeze["body_hash_allowed"] is False
    assert freeze["question_need_observation_row_schema_enum_fixed"] is True
    assert freeze["question_need_observation_row_bodyfree_contract_ready"] is True
    assert freeze["question_need_observation_row_normalizer_implemented_here"] is False
    assert freeze["question_need_observation_row_instances_materialized_here"] is False
    assert freeze["p8_question_implementation_spec_finalized_here"] is False
    assert freeze["p8_start_allowed"] is False
    assert freeze["release_allowed"] is False
    assert freeze["actual_question_need_observation_rows_materialized_here"] is False
    assert tuple(freeze["implemented_steps"]) == r49.P7_R49_R7_IMPLEMENTED_STEPS
    assert tuple(freeze["not_yet_implemented_steps"]) == r49.P7_R49_R7_NOT_YET_IMPLEMENTED_STEPS
    assert freeze["next_required_step"] == r49.P7_R49_R7_NEXT_REQUIRED_STEP_REF
    _assert_no_body_question_or_release_promotion(freeze)


def test_r49_r6_r7_combined_freeze_keeps_next_step_at_r8_and_does_not_claim_actual_rows() -> None:
    ingestion = r49.build_p7_r49_blocker_execution_blocker_ingestion(r49_rating_row_ingestion_r48_normalizer_connection=_r5())
    freeze = r49.build_p7_r49_question_need_observation_row_schema_enum_freeze(
        r49_blocker_execution_blocker_ingestion=ingestion,
    )
    combined = r49.build_p7_r49_r6_r7_blocker_question_schema_freeze(
        r49_blocker_execution_blocker_ingestion=ingestion,
        r49_question_need_observation_row_schema_enum_freeze=freeze,
    )
    assert r49.assert_p7_r49_r6_r7_blocker_question_schema_freeze_contract(combined) is True

    assert combined["schema_version"] == r49.P7_R49_R6_R7_BLOCKER_QUESTION_SCHEMA_FREEZE_SCHEMA_VERSION
    assert set(combined) == set(r49.P7_R49_R6_R7_BLOCKER_QUESTION_SCHEMA_FREEZE_REQUIRED_FIELD_REFS)
    assert combined["policy_section"] == "R49-6_R49-7_blocker_question_schema_freeze"
    assert combined["blocker_execution_ingestion_ready"] is True
    assert combined["readfeel_and_execution_blockers_separated"] is True
    assert combined["question_need_observation_row_schema_enum_fixed"] is True
    assert combined["question_need_observation_required"] is True
    assert combined["question_need_observation_rows_required_later"] is True
    assert combined["actual_human_review_run_here"] is False
    assert combined["actual_rating_rows_materialized_here"] is False
    assert combined["actual_blocker_rows_materialized_here"] is False
    assert combined["actual_execution_blocker_rows_materialized_here"] is False
    assert combined["actual_question_need_observation_rows_materialized_here"] is False
    assert combined["question_need_observation_row_normalizer_implemented_here"] is False
    assert tuple(combined["implemented_steps"]) == r49.P7_R49_R7_IMPLEMENTED_STEPS
    assert tuple(combined["not_yet_implemented_steps"]) == r49.P7_R49_R7_NOT_YET_IMPLEMENTED_STEPS
    assert combined["next_required_step"] == r49.P7_R49_R7_NEXT_REQUIRED_STEP_REF
    _assert_no_body_question_or_release_promotion(combined)
