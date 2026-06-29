# -*- coding: utf-8 -*-
from __future__ import annotations

import json
from copy import deepcopy
from functools import lru_cache

import pytest

import emlis_ai_p7_r47_local_review_packet_policy as r47
import emlis_ai_p7_r48_p5_human_blind_qa_actual_review_packet as r48
import emlis_ai_p7_r49_p5_human_blind_qa_actual_review_execution as r49
import emlis_ai_p7_r50_p5_human_blind_qa_manual_run_decision as r50

SECRET_INPUT = "R50 secret raw input must not enter body-free material"
SECRET_SURFACE = "R50 returned Emlis surface must not enter body-free material"
SECRET_REVIEWER = "R50 reviewer free text must not enter body-free material"
SECRET_QUESTION = "R50 draft question text must not enter body-free material"
SECRET_PATH = "/tmp/r50/local/body_full_packet.json"


def _dumped(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def _assert_no_body_question_or_release_promotion(value: dict[str, object]) -> None:
    dumped = _dumped(value)
    assert SECRET_INPUT not in dumped
    assert SECRET_SURFACE not in dumped
    assert SECRET_REVIEWER not in dumped
    assert SECRET_QUESTION not in dumped
    assert SECRET_PATH not in dumped
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
        '"reviewer_notes":',
        '"question_text":',
        '"draft_question_text":',
        '"question_body":',
        '"terminal_output":',
        '"body_content_hash":',
        '"packet_content_hash":',
        '"local_absolute_path":',
        '"stdout":',
        '"stderr":',
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
        '"manual_run_decision_made_here": true',
        '"local_only_body_full_generation_allowed": true',
        '"body_full_packet_generated_here": true',
        '"actual_human_review_run_here": true',
    ):
        assert forbidden_true not in dumped.lower()


@lru_cache(maxsize=1)
def _cached_r49_boundary() -> tuple[dict[str, object]]:
    boundary = r49.build_p7_r49_touch_candidate_no_touch_boundary_freeze()
    assert r49.assert_p7_r49_touch_candidate_no_touch_boundary_freeze_contract(boundary) is True
    return (boundary,)


def _r49_boundary() -> dict[str, object]:
    return deepcopy(_cached_r49_boundary()[0])


@lru_cache(maxsize=1)
def _cached_r50_r0() -> tuple[dict[str, object]]:
    refreeze = r50.build_p7_r50_current_source_r49_handoff_bridge_refreeze(r49_handoff_boundary=_r49_boundary())
    assert r50.assert_p7_r50_current_source_r49_handoff_bridge_refreeze_contract(refreeze) is True
    return (refreeze,)


def _r50_r0() -> dict[str, object]:
    return deepcopy(_cached_r50_r0()[0])


def test_r50_r0_refreezes_current_source_r49_handoff_and_p7_p8_bridge_without_review_p8_or_release() -> None:
    refreeze = _r50_r0()

    assert refreeze["schema_version"] == r50.P7_R50_CURRENT_SOURCE_R49_HANDOFF_BRIDGE_REFREEZE_SCHEMA_VERSION
    assert set(refreeze) == set(r50.P7_R50_CURRENT_SOURCE_R49_HANDOFF_BRIDGE_REFREEZE_REQUIRED_FIELD_REFS)
    assert refreeze["phase"].startswith("P7_")
    assert refreeze["step"] == r50.P7_R50_STEP
    assert refreeze["scope"] == r50.P7_R50_SCOPE
    assert refreeze["policy_section"] == "R50-0_current_source_r49_handoff_p7_p8_bridge_refreeze"
    assert refreeze["source_mode"] == "local_snapshot"
    assert refreeze["git_connection_required"] is False
    assert refreeze["git_checked"] is False
    assert refreeze["body_free"] is True
    assert refreeze["source_snapshot_refs"]["backend_zip_ref"] == "mashos-api(158).zip"

    handoff = refreeze["r49_handoff"]
    assert set(handoff) == set(r50.P7_R50_R49_HANDOFF_REQUIRED_FIELD_REFS)
    assert handoff["r49_handoff_required"] is True
    assert handoff["r49_step"] == r49.P7_R49_STEP
    assert handoff["r49_scope"] == r49.P7_R49_SCOPE
    assert handoff["r49_packet_kind"] == r50.P7_R50_PACKET_KIND == r48.P7_R48_PACKET_KIND
    assert handoff["r49_review_kind"] == r50.P7_R50_REVIEW_KIND == r48.P7_R48_REVIEW_KIND
    assert tuple(handoff["r49_completed_steps"]) == r49.P7_R49_R18_IMPLEMENTED_STEPS
    assert tuple(handoff["r49_not_yet_implemented_steps"]) == r49.P7_R49_R18_NOT_YET_IMPLEMENTED_STEPS == ()
    assert handoff["r49_next_required_step"] == "P5_human_blind_qa_actual_review_manual_run_decision"
    assert handoff["r49_actual_review_execution_scaffold_finished"] is True
    assert handoff["r49_question_need_observation_capture_footing_ready"] is True
    assert handoff["r49_touch_no_touch_boundary_frozen"] is True
    assert handoff["r49_actual_review_completed"] is False
    assert handoff["r49_actual_human_review_run"] is False
    assert handoff["r49_body_full_packet_generated"] is False
    assert handoff["r49_rating_rows_materialized"] is False
    assert handoff["r49_question_need_observation_rows_materialized"] is False
    assert handoff["r49_disposal_receipt_materialized"] is False
    assert handoff["r49_p5_human_blind_qa_confirmed"] is False
    assert handoff["r49_p6_limited_human_readfeel_start_allowed"] is False
    assert handoff["r49_p8_start_allowed"] is False
    assert handoff["r49_release_allowed"] is False

    bridge = refreeze["p7_p8_bridge_rule"]
    assert set(bridge) == set(r50.P7_R50_BRIDGE_RULE_REQUIRED_FIELD_REFS)
    assert bridge["p7_bridge_only"] is True
    assert bridge["r50_is_manual_run_decision_preparation"] is True
    assert bridge["question_need_observation_memo_only"] is True
    assert bridge["question_need_observation_body_free_required"] is True
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

    assert refreeze["r0_current_source_r49_handoff_bridge_refrozen"] is True
    assert refreeze["r1_scope_schema_status_enum_fixed"] is False
    assert refreeze["manual_run_decision_required_later"] is True
    assert refreeze["actual_manual_review_run_here"] is False
    assert refreeze["body_full_packet_generated_here"] is False
    assert tuple(refreeze["implemented_steps"]) == r50.P7_R50_R0_IMPLEMENTED_STEPS
    assert tuple(refreeze["not_yet_implemented_steps"]) == r50.P7_R50_R0_NOT_YET_IMPLEMENTED_STEPS
    assert refreeze["next_required_step"] == r50.P7_R50_R0_NEXT_REQUIRED_STEP_REF
    for key in r50.P7_R50_R0_R1_FALSE_KEY_REFS:
        assert refreeze[key] is False

    _assert_no_body_question_or_release_promotion(refreeze)


def test_r50_r0_rejects_r49_boundary_that_claims_review_done_p8_open_or_release() -> None:
    for key in (
        "actual_human_review_run_here",
        "actual_body_full_packet_generated_here",
        "actual_rating_rows_materialized_here",
        "actual_question_need_observation_rows_materialized_here",
        "actual_disposal_receipt_materialized_here",
        "p5_human_blind_qa_confirmed",
        "p5_human_blind_qa_confirmed_candidate",
        "p6_limited_human_readfeel_start_allowed",
        "p8_question_design_material_candidate",
        "p8_start_allowed",
        "release_allowed",
    ):
        boundary = _r49_boundary()
        boundary[key] = True
        with pytest.raises(ValueError):
            r50.build_p7_r50_current_source_r49_handoff_bridge_refreeze(r49_handoff_boundary=boundary)


def test_r50_r1_fixes_scope_schema_versions_status_enum_manual_decision_enum_and_execution_blockers() -> None:
    freeze = r50.build_p7_r50_scope_schema_status_enum_freeze(current_source_r49_handoff_bridge_refreeze=_r50_r0())
    assert r50.assert_p7_r50_scope_schema_status_enum_freeze_contract(freeze) is True

    assert freeze["schema_version"] == r50.P7_R50_SCOPE_SCHEMA_STATUS_ENUM_FREEZE_SCHEMA_VERSION
    assert set(freeze) == set(r50.P7_R50_SCOPE_SCHEMA_STATUS_ENUM_FREEZE_REQUIRED_FIELD_REFS)
    assert freeze["step"] == r50.P7_R50_STEP
    assert freeze["scope"] == r50.P7_R50_SCOPE
    assert freeze["policy_section"] == "R50-1_scope_schema_version_status_enum_freeze"
    assert freeze["r0_schema_version"] == r50.P7_R50_CURRENT_SOURCE_R49_HANDOFF_BRIDGE_REFREEZE_SCHEMA_VERSION
    assert freeze["review_kind"] == r50.P7_R50_REVIEW_KIND == r48.P7_R48_REVIEW_KIND
    assert freeze["packet_kind"] == r50.P7_R50_PACKET_KIND == r48.P7_R48_PACKET_KIND
    assert freeze["r49_handoff_required"] is True
    assert freeze["required_case_count"] == 24
    assert freeze["review_session_status"] == "NOT_STARTED"
    assert tuple(freeze["review_session_status_refs"]) == r50.P7_R50_REVIEW_SESSION_STATUS_REFS
    assert tuple(freeze["manual_run_decision_refs"]) == r50.P7_R50_MANUAL_RUN_DECISION_REFS
    assert "GO_FOR_LOCAL_MANUAL_REVIEW" in freeze["manual_run_decision_refs"]
    assert "NO_GO_EXPLICIT_ALLOW_MISSING" in freeze["manual_run_decision_refs"]
    assert tuple(freeze["execution_blocker_id_refs"]) == r50.P7_R50_EXECUTION_BLOCKER_ID_REFS
    assert "r50_missing_r49_handoff" in freeze["execution_blocker_id_refs"]
    assert "r50_body_free_leak_detected" in freeze["execution_blocker_id_refs"]
    assert tuple(freeze["execution_blocker_status_refs"]) == r50.P7_R50_EXECUTION_BLOCKER_STATUS_REFS
    assert tuple(freeze["question_need_primary_class_refs"]) == r49.P7_R49_QUESTION_NEED_PRIMARY_CLASS_REFS
    assert tuple(freeze["ambiguity_kind_refs"]) == r49.P7_R49_AMBIGUITY_KIND_REFS
    assert tuple(freeze["one_question_fit_refs"]) == r49.P7_R49_ONE_QUESTION_FIT_REFS
    assert tuple(freeze["repair_required_ref_refs"]) == r49.P7_R49_REPAIR_REQUIRED_REF_REFS

    assert freeze["r49_touch_boundary_schema_version"] == r49.P7_R49_TOUCH_CANDIDATE_NO_TOUCH_BOUNDARY_FREEZE_SCHEMA_VERSION
    assert freeze["r49_question_need_observation_row_bodyfree_schema_version"] == r49.P7_R49_QUESTION_NEED_OBSERVATION_ROW_BODYFREE_SCHEMA_VERSION
    assert freeze["r49_question_need_observation_summary_bodyfree_schema_version"] == r49.P7_R49_QUESTION_NEED_OBSERVATION_SUMMARY_BODYFREE_SCHEMA_VERSION
    assert freeze["r49_review_handoff_summary_bodyfree_schema_version"] == r49.P7_R49_REVIEW_HANDOFF_SUMMARY_BODYFREE_SCHEMA_VERSION
    assert freeze["r48_reviewer_packet_local_only_schema_version"] == r48.P7_R48_P5_REVIEWER_PACKET_LOCAL_ONLY_SCHEMA_VERSION
    assert freeze["r48_rating_row_bodyfree_schema_version"] == r48.P7_R48_P5_RATING_ROW_BODYFREE_SCHEMA_VERSION
    assert freeze["r48_blocker_row_bodyfree_schema_version"] == r48.P7_R48_P5_BLOCKER_ROW_BODYFREE_SCHEMA_VERSION
    assert freeze["r48_execution_blocker_row_bodyfree_schema_version"] == r48.P7_R48_P5_EXECUTION_BLOCKER_ROW_BODYFREE_SCHEMA_VERSION
    assert freeze["r48_disposal_receipt_bodyfree_schema_version"] == r48.P7_R48_P5_DISPOSAL_RECEIPT_BODYFREE_SCHEMA_VERSION
    assert freeze["r47_local_review_root_env_var"] == r47.P7_R47_LOCAL_REVIEW_ROOT_ENV_VAR
    assert tuple(tuple(row) for row in freeze["r48_p5_first_formal_case_distribution"]) == r48.P7_R48_P5_FIRST_FORMAL_CASE_DISTRIBUTION

    assert freeze["scope_fixed"] is True
    assert freeze["schema_versions_fixed"] is True
    assert freeze["status_enum_fixed"] is True
    assert freeze["manual_run_decision_enum_fixed"] is True
    assert freeze["execution_blocker_enum_fixed"] is True
    assert freeze["question_need_observation_enum_inherited_from_r49"] is True
    assert freeze["manual_run_decision_made_here"] is False
    assert freeze["actual_manual_review_run_here"] is False
    assert freeze["body_full_packet_generated_here"] is False
    assert freeze["p8_question_detail_design_in_scope"] is False
    assert freeze["api_db_rn_response_key_changed_here"] is False
    assert tuple(freeze["implemented_steps"]) == r50.P7_R50_IMPLEMENTED_STEPS
    assert tuple(freeze["not_yet_implemented_steps"]) == r50.P7_R50_NOT_YET_IMPLEMENTED_STEPS
    assert freeze["next_required_step"] == r50.P7_R50_R1_NEXT_REQUIRED_STEP_REF
    for key in r50.P7_R50_R0_R1_FALSE_KEY_REFS:
        assert freeze[key] is False

    _assert_no_body_question_or_release_promotion(freeze)


def test_r50_r1_rejects_unknown_review_session_status() -> None:
    with pytest.raises(ValueError):
        r50.build_p7_r50_scope_schema_status_enum_freeze(review_session_status="READY_FOR_P8")


def test_r50_r1_contract_rejects_p8_question_design_review_run_bodyfull_and_contract_mutation_claims() -> None:
    freeze = r50.build_p7_r50_scope_schema_status_enum_freeze(current_source_r49_handoff_bridge_refreeze=_r50_r0())

    for key in (
        "manual_run_decision_made_here",
        "actual_manual_review_run_here",
        "body_full_packet_generated_here",
        "p8_question_detail_design_in_scope",
        "api_db_rn_response_key_changed_here",
        "p8_start_allowed",
        "release_allowed",
    ):
        mutated = deepcopy(freeze)
        mutated[key] = True
        with pytest.raises(ValueError):
            r50.assert_p7_r50_scope_schema_status_enum_freeze_contract(mutated)


def test_r50_r0_r1_combined_freeze_is_body_free_and_points_to_r50_2_without_running_review() -> None:
    combined = r50.build_p7_r50_r0_r1_scope_status_freeze(r49_handoff_boundary=_r49_boundary())
    assert r50.assert_p7_r50_r0_r1_scope_status_freeze_contract(combined) is True

    assert combined["schema_version"] == r50.P7_R50_R0_R1_SCOPE_STATUS_FREEZE_SCHEMA_VERSION
    assert set(combined) == set(r50.P7_R50_R0_R1_SCOPE_STATUS_FREEZE_REQUIRED_FIELD_REFS)
    assert tuple(combined["implemented_steps"]) == r50.P7_R50_IMPLEMENTED_STEPS
    assert tuple(combined["not_yet_implemented_steps"]) == r50.P7_R50_NOT_YET_IMPLEMENTED_STEPS
    assert tuple(combined["review_session_status_refs"]) == r50.P7_R50_REVIEW_SESSION_STATUS_REFS
    assert tuple(combined["manual_run_decision_refs"]) == r50.P7_R50_MANUAL_RUN_DECISION_REFS
    assert tuple(combined["execution_blocker_id_refs"]) == r50.P7_R50_EXECUTION_BLOCKER_ID_REFS
    assert combined["required_case_count"] == 24
    assert combined["r0_current_source_r49_handoff_bridge_refrozen"] is True
    assert combined["r1_scope_schema_status_enum_fixed"] is True
    assert combined["manual_run_decision_required_later"] is True
    assert combined["actual_manual_review_run_here"] is False
    assert combined["body_full_packet_generated_here"] is False
    assert combined["p5_human_blind_qa_confirmed"] is False
    assert combined["p6_limited_human_readfeel_start_allowed"] is False
    assert combined["p7_complete"] is False
    assert combined["p8_start_allowed"] is False
    assert combined["release_allowed"] is False
    assert combined["next_required_step"] == r50.P7_R50_R1_NEXT_REQUIRED_STEP_REF

    _assert_no_body_question_or_release_promotion(combined)
