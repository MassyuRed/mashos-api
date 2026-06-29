# -*- coding: utf-8 -*-
from __future__ import annotations

import json
from copy import deepcopy
from functools import lru_cache

import pytest

import emlis_ai_p7_r48_p5_human_blind_qa_actual_review_packet as r48
import emlis_ai_p7_r49_p5_human_blind_qa_actual_review_execution as r49

SECRET_INPUT = "R49 secret raw input must not enter body-free material"
SECRET_SURFACE = "R49 returned Emlis surface must not enter body-free material"
SECRET_REVIEWER = "R49 reviewer free text must not enter body-free material"
SECRET_QUESTION = "R49 draft question text must not enter body-free material"


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
    ):
        assert forbidden_true not in dumped.lower()


@lru_cache(maxsize=1)
def _cached_r48_boundary() -> tuple[dict[str, object]]:
    boundary = r48.build_p7_r48_touch_candidate_no_touch_boundary_freeze()
    assert r48.assert_p7_r48_touch_candidate_no_touch_boundary_freeze_contract(boundary) is True
    return (boundary,)


def _r48_boundary() -> dict[str, object]:
    return deepcopy(_cached_r48_boundary()[0])


@lru_cache(maxsize=1)
def _cached_r49_r0() -> tuple[dict[str, object]]:
    refreeze = r49.build_p7_r49_current_source_r48_handoff_bridge_refreeze(r48_handoff_boundary=_r48_boundary())
    assert r49.assert_p7_r49_current_source_r48_handoff_bridge_refreeze_contract(refreeze) is True
    return (refreeze,)


def _r49_r0() -> dict[str, object]:
    return deepcopy(_cached_r49_r0()[0])


def test_r49_r0_refreezes_current_source_r48_handoff_and_p7_p8_bridge_without_starting_p8() -> None:
    refreeze = _r49_r0()

    assert refreeze["schema_version"] == r49.P7_R49_CURRENT_SOURCE_R48_HANDOFF_BRIDGE_REFREEZE_SCHEMA_VERSION
    assert set(refreeze) == set(r49.P7_R49_CURRENT_SOURCE_R48_HANDOFF_BRIDGE_REFREEZE_REQUIRED_FIELD_REFS)
    assert refreeze["phase"].startswith("P7_")
    assert refreeze["step"] == r49.P7_R49_STEP
    assert refreeze["scope"] == r49.P7_R49_SCOPE
    assert refreeze["policy_section"] == "R49-0_current_source_r48_handoff_bridge_rule_refreeze"
    assert refreeze["source_mode"] == "local_snapshot"
    assert refreeze["git_connection_required"] is False
    assert refreeze["git_checked"] is False
    assert refreeze["body_free"] is True

    handoff = refreeze["r48_handoff"]
    assert set(handoff) == set(r49.P7_R49_R48_HANDOFF_REQUIRED_FIELD_REFS)
    assert handoff["r48_handoff_required"] is True
    assert handoff["r48_step"] == r48.P7_R48_STEP
    assert handoff["r48_scope"] == r48.P7_R48_SCOPE
    assert handoff["r48_packet_kind"] == r49.P7_R49_PACKET_KIND == r48.P7_R48_PACKET_KIND
    assert handoff["r48_review_kind"] == r49.P7_R49_REVIEW_KIND == r48.P7_R48_REVIEW_KIND
    assert tuple(handoff["r48_implemented_steps"]) == r48.P7_R48_R18_IMPLEMENTED_STEPS
    assert tuple(handoff["r48_not_yet_implemented_steps"]) == r48.P7_R48_R18_NOT_YET_IMPLEMENTED_STEPS
    assert handoff["r48_next_required_step"] == r48.P7_R48_R18_NEXT_REQUIRED_STEP_REF
    assert handoff["r48_actual_review_packet_preparation_finished"] is True
    assert handoff["r48_actual_human_review_run"] is False
    assert handoff["r48_body_full_packet_generated"] is False
    assert handoff["r48_disposal_run"] is False
    assert handoff["r48_disposal_receipt_materialized"] is False
    assert handoff["r48_p5_human_blind_qa_confirmed"] is False
    assert handoff["r48_p6_limited_human_readfeel_start_allowed"] is False
    assert handoff["r48_p7_complete"] is False
    assert handoff["r48_p8_start_allowed"] is False
    assert handoff["r48_release_allowed"] is False

    bridge = refreeze["p7_p8_bridge_rule"]
    assert set(bridge) == set(r49.P7_R49_BRIDGE_RULE_REQUIRED_FIELD_REFS)
    assert bridge["bridge_rule_ref"] == "p7_p8_bridge_question_need_observation_20260619"
    assert bridge["p7_bridge_only"] is True
    assert bridge["question_need_observation_memo_only"] is True
    assert bridge["question_need_observation_bodyfree_required"] is True
    assert bridge["p8_design_material_candidate_allowed_later"] is True
    assert bridge["p8_detail_design_allowed_here"] is False
    assert bridge["question_api_implemented"] is False
    assert bridge["question_db_schema_implemented"] is False
    assert bridge["question_rn_ui_implemented"] is False
    assert bridge["question_response_key_implemented"] is False
    assert bridge["question_trigger_logic_implemented"] is False
    assert bridge["raw_input_or_comment_text_allowed_in_bridge_material"] is False
    assert bridge["returned_surface_allowed_in_bridge_material"] is False
    assert bridge["reviewer_free_text_allowed_in_bridge_material"] is False
    assert bridge["question_text_allowed_in_bridge_material"] is False
    assert bridge["p7_completion_condition_relaxed"] is False
    assert bridge["p8_start_allowed"] is False
    assert bridge["release_allowed"] is False

    assert refreeze["r0_current_source_r48_handoff_bridge_refrozen"] is True
    assert refreeze["r1_scope_schema_status_enum_fixed"] is False
    assert refreeze["first_next_work_ref"] == r49.P7_R49_FIRST_NEXT_WORK_REF
    assert refreeze["next_required_step"] == r49.P7_R49_R0_NEXT_REQUIRED_STEP_REF
    for key in r49.P7_R49_R0_R1_FALSE_KEY_REFS:
        assert refreeze[key] is False

    _assert_no_body_question_or_release_promotion(refreeze)


def test_r49_r0_rejects_r48_boundary_that_claims_review_done_p8_open_or_release() -> None:
    for key in (
        "actual_human_review_run_here",
        "actual_body_full_packet_generated_here",
        "p5_human_blind_qa_confirmed",
        "p6_limited_human_readfeel_start_allowed",
        "p8_start_allowed",
        "release_allowed",
    ):
        boundary = _r48_boundary()
        boundary[key] = True
        with pytest.raises(ValueError):
            r49.build_p7_r49_current_source_r48_handoff_bridge_refreeze(r48_handoff_boundary=boundary)


def test_r49_r1_fixes_scope_schema_versions_status_enum_and_question_observation_enums() -> None:
    envelope = r49.build_p7_r49_review_session_envelope(current_source_r48_handoff_bridge_refreeze=_r49_r0())
    assert r49.assert_p7_r49_review_session_envelope_contract(envelope) is True

    assert envelope["schema_version"] == r49.P7_R49_REVIEW_SESSION_ENVELOPE_BODYFREE_SCHEMA_VERSION
    assert set(envelope) == set(r49.P7_R49_REVIEW_SESSION_ENVELOPE_REQUIRED_FIELD_REFS)
    assert envelope["step"] == r49.P7_R49_STEP
    assert envelope["scope"] == r49.P7_R49_SCOPE
    assert envelope["policy_section"] == "R49-1_scope_schema_version_status_enum_freeze"
    assert envelope["r0_bridge_refreeze_schema_version"] == r49.P7_R49_CURRENT_SOURCE_R48_HANDOFF_BRIDGE_REFREEZE_SCHEMA_VERSION
    assert envelope["review_kind"] == r49.P7_R49_REVIEW_KIND == r48.P7_R48_REVIEW_KIND
    assert envelope["packet_kind"] == r49.P7_R49_PACKET_KIND == r48.P7_R48_PACKET_KIND
    assert envelope["r48_handoff_required"] is True
    assert envelope["r48_case_matrix_required"] is True
    assert envelope["required_total_cases"] == 24
    assert envelope["review_session_status"] == "NOT_STARTED"
    assert tuple(envelope["review_session_status_refs"]) == r49.P7_R49_REVIEW_SESSION_STATUS_REFS
    assert tuple(envelope["question_need_primary_class_refs"]) == r49.P7_R49_QUESTION_NEED_PRIMARY_CLASS_REFS
    assert tuple(envelope["ambiguity_kind_refs"]) == r49.P7_R49_AMBIGUITY_KIND_REFS
    assert tuple(envelope["one_question_fit_refs"]) == r49.P7_R49_ONE_QUESTION_FIT_REFS
    assert tuple(envelope["repair_required_ref_refs"]) == r49.P7_R49_REPAIR_REQUIRED_REF_REFS
    assert tuple(envelope["plan_candidate_flag_refs"]) == r49.P7_R49_PLAN_CANDIDATE_FLAG_REFS

    assert envelope["r49_review_session_envelope_schema_version"] == r49.P7_R49_REVIEW_SESSION_ENVELOPE_BODYFREE_SCHEMA_VERSION
    assert envelope["question_need_observation_row_bodyfree_schema_version"] == r49.P7_R49_QUESTION_NEED_OBSERVATION_ROW_BODYFREE_SCHEMA_VERSION
    assert envelope["question_need_observation_summary_bodyfree_schema_version"] == r49.P7_R49_QUESTION_NEED_OBSERVATION_SUMMARY_BODYFREE_SCHEMA_VERSION
    assert envelope["review_handoff_summary_bodyfree_schema_version"] == r49.P7_R49_REVIEW_HANDOFF_SUMMARY_BODYFREE_SCHEMA_VERSION
    assert envelope["r48_case_matrix_schema_version"] == r48.P7_R48_P5_CASE_MATRIX_SCHEMA_VERSION
    assert envelope["r48_rating_row_bodyfree_schema_version"] == r48.P7_R48_P5_RATING_ROW_BODYFREE_SCHEMA_VERSION
    assert envelope["r48_blocker_row_bodyfree_schema_version"] == r48.P7_R48_P5_BLOCKER_ROW_BODYFREE_SCHEMA_VERSION
    assert envelope["r48_execution_blocker_row_bodyfree_schema_version"] == r48.P7_R48_P5_EXECUTION_BLOCKER_ROW_BODYFREE_SCHEMA_VERSION
    assert envelope["r48_disposal_receipt_bodyfree_schema_version"] == r48.P7_R48_P5_DISPOSAL_RECEIPT_BODYFREE_SCHEMA_VERSION
    assert envelope["r48_review_handoff_summary_bodyfree_schema_version"] == r48.P7_R48_P5_REVIEW_HANDOFF_SUMMARY_BODYFREE_SCHEMA_VERSION
    assert tuple(envelope["r48_p5_confirmed_candidate_required_condition_refs"]) == r48.P7_R48_P5_CONFIRMED_CANDIDATE_REQUIRED_CONDITION_REFS
    assert tuple(tuple(row) for row in envelope["r48_p5_first_formal_case_distribution"]) == r48.P7_R48_P5_FIRST_FORMAL_CASE_DISTRIBUTION
    assert tuple(envelope["r48_readfeel_blocker_id_refs"]) == r48.P7_R48_READFEEL_BLOCKER_ID_REFS

    assert envelope["scope_fixed"] is True
    assert envelope["schema_versions_fixed"] is True
    assert envelope["status_enum_fixed"] is True
    assert envelope["question_need_enum_refs_fixed"] is True
    assert envelope["r49_is_p8_question_detail_design"] is False
    assert envelope["body_full_packet_materialized_here"] is False
    assert envelope["actual_human_review_run_here"] is False
    assert envelope["question_need_observation_required"] is True
    assert envelope["question_need_observation_rows_required"] is True
    assert envelope["question_text_required"] is False
    assert envelope["reviewer_free_text_bodyfree_export_allowed"] is False
    assert tuple(envelope["implemented_steps"]) == r49.P7_R49_IMPLEMENTED_STEPS
    assert tuple(envelope["not_yet_implemented_steps"]) == r49.P7_R49_NOT_YET_IMPLEMENTED_STEPS
    assert envelope["first_next_work_ref"] == r49.P7_R49_FIRST_NEXT_WORK_REF
    assert envelope["next_required_step"] == r49.P7_R49_R1_NEXT_REQUIRED_STEP_REF
    for key in r49.P7_R49_R0_R1_FALSE_KEY_REFS:
        assert envelope[key] is False

    _assert_no_body_question_or_release_promotion(envelope)


def test_r49_r1_rejects_unknown_review_session_status() -> None:
    with pytest.raises(ValueError):
        r49.build_p7_r49_review_session_envelope(review_session_status="READY_FOR_P8")


def test_r49_r1_contract_rejects_p8_question_detail_design_review_run_and_bodyfull_claims() -> None:
    envelope = r49.build_p7_r49_review_session_envelope(current_source_r48_handoff_bridge_refreeze=_r49_r0())

    for key in (
        "r49_is_p8_question_detail_design",
        "body_full_packet_materialized_here",
        "actual_human_review_run_here",
        "question_text_required",
        "reviewer_free_text_bodyfree_export_allowed",
        "p8_start_allowed",
        "release_allowed",
    ):
        mutated = deepcopy(envelope)
        mutated[key] = True
        with pytest.raises(ValueError):
            r49.assert_p7_r49_review_session_envelope_contract(mutated)


def test_r49_r0_r1_combined_freeze_is_body_free_and_points_to_r2_without_running_review() -> None:
    combined = r49.build_p7_r49_r0_r1_scope_status_freeze(r48_handoff_boundary=_r48_boundary())
    assert r49.assert_p7_r49_r0_r1_scope_status_freeze_contract(combined) is True

    assert combined["schema_version"] == r49.P7_R49_R0_R1_SCOPE_STATUS_FREEZE_SCHEMA_VERSION
    assert set(combined) == set(r49.P7_R49_R0_R1_SCOPE_STATUS_FREEZE_REQUIRED_FIELD_REFS)
    assert tuple(combined["implemented_steps"]) == r49.P7_R49_IMPLEMENTED_STEPS
    assert tuple(combined["not_yet_implemented_steps"]) == r49.P7_R49_NOT_YET_IMPLEMENTED_STEPS
    assert tuple(combined["review_session_status_refs"]) == r49.P7_R49_REVIEW_SESSION_STATUS_REFS
    assert tuple(combined["question_need_primary_class_refs"]) == r49.P7_R49_QUESTION_NEED_PRIMARY_CLASS_REFS
    assert combined["first_next_work_ref"] == r49.P7_R49_FIRST_NEXT_WORK_REF
    assert combined["next_required_step"] == r49.P7_R49_R1_NEXT_REQUIRED_STEP_REF
    assert combined["r0_current_source_r48_handoff_bridge_refrozen"] is True
    assert combined["r1_scope_schema_status_enum_fixed"] is True
    assert combined["actual_human_review_run_here"] is False
    assert combined["actual_body_full_packet_generated_here"] is False
    assert combined["actual_question_need_observation_rows_materialized_here"] is False
    assert combined["p5_human_blind_qa_confirmed"] is False
    assert combined["p6_limited_human_readfeel_start_allowed"] is False
    assert combined["p7_complete"] is False
    assert combined["p8_start_allowed"] is False
    assert combined["release_allowed"] is False

    _assert_no_body_question_or_release_promotion(combined)
