# -*- coding: utf-8 -*-
from __future__ import annotations

import pytest

import emlis_ai_p7_r49_p5_human_blind_qa_actual_review_execution as r49


def test_r49_r18_builds_touch_candidate_no_touch_boundary_without_runtime_spread() -> None:
    boundary = r49.build_p7_r49_touch_candidate_no_touch_boundary_freeze()
    assert r49.assert_p7_r49_touch_candidate_no_touch_boundary_freeze_contract(boundary) is True

    assert boundary["schema_version"] == r49.P7_R49_TOUCH_CANDIDATE_NO_TOUCH_BOUNDARY_FREEZE_SCHEMA_VERSION
    assert set(boundary) == set(r49.P7_R49_TOUCH_CANDIDATE_NO_TOUCH_BOUNDARY_REQUIRED_FIELD_REFS)
    assert boundary["policy_section"] == "R49-18_touch_candidate_no_touch_boundary_freeze"
    assert boundary["touch_boundary_freeze_required"] is True
    assert boundary["touch_candidate_boundary_frozen"] is True
    assert boundary["no_touch_boundary_frozen"] is True
    assert boundary["forbidden_actual_touched_refs_rejected"] is True
    assert boundary["no_touch_refs_must_remain_untouched"] is True
    assert boundary["allowed_refs_do_not_include_no_touch_refs"] is True
    assert boundary["production_touch_candidate_is_r49_helper_only"] is True
    assert boundary["optional_touch_candidate_is_local_file_ops_only"] is True
    assert boundary["test_touch_candidate_is_r49_target_only"] is True

    assert tuple(boundary["production_touch_candidate_file_refs"]) == r49.P7_R49_PRODUCTION_TOUCH_CANDIDATE_FILE_REFS
    assert tuple(boundary["optional_touch_candidate_file_refs"]) == r49.P7_R49_OPTIONAL_TOUCH_CANDIDATE_FILE_REFS
    assert tuple(boundary["test_touch_candidate_file_refs"]) == r49.P7_R49_VALIDATION_R49_TARGET_TEST_FILE_REFS
    assert tuple(boundary["allowed_production_file_refs"]) == r49.P7_R49_ALLOWED_PRODUCTION_TOUCH_FILE_REFS
    assert tuple(boundary["allowed_test_file_refs"]) == r49.P7_R49_ALLOWED_TEST_TOUCH_FILE_REFS
    assert tuple(boundary["allowed_actual_touched_file_refs"]) == r49.P7_R49_ALLOWED_ACTUAL_TOUCHED_FILE_REFS
    assert tuple(boundary["explicit_no_touch_file_refs"]) == r49.P7_R49_EXPLICIT_NO_TOUCH_FILE_REFS
    assert tuple(boundary["explicit_no_touch_area_refs"]) == r49.P7_R49_EXPLICIT_NO_TOUCH_AREA_REFS
    assert tuple(boundary["forbidden_actual_touched_file_refs"]) == r49.P7_R49_EXPLICIT_NO_TOUCH_FILE_REFS
    assert tuple(boundary["current_patch_expected_touched_file_refs"]) == r49.P7_R49_R18_CURRENT_PATCH_EXPECTED_TOUCHED_FILE_REFS
    assert "tests/test_emlis_ai_p7_r49_p5_human_blind_qa_actual_review_execution_r18_20260619.py" in boundary[
        "test_touch_candidate_file_refs"
    ]

    assert boundary["actual_touched_file_refs_checked_here"] is False
    assert boundary["actual_touched_file_refs_verified_here"] is False
    assert boundary["actual_touched_file_refs_materialized_here"] is False
    assert boundary["forbidden_actual_touched_refs_detected_here"] is False
    assert boundary["production_runtime_spread_allowed"] is False
    assert boundary["rn_runtime_spread_allowed"] is False
    assert boundary["api_db_release_spread_allowed"] is False
    assert boundary["validation_commands_executed_here"] is False
    assert boundary["command_output_stored_here"] is False
    assert boundary["terminal_output_stored_here"] is False


def test_r49_r18_keeps_rn_api_db_runtime_p8_and_release_closed() -> None:
    boundary = r49.build_p7_r49_touch_candidate_no_touch_boundary_freeze()

    for false_key in (
        "rn_contract_changed_here",
        "rn_production_files_touched_here",
        "rn_contract_test_files_touched_here",
        "rn_visible_contract_changed_here",
        "public_response_shape_changed_here",
        "api_response_shape_changed_here",
        "public_response_top_level_key_added_here",
        "request_key_changed_here",
        "api_route_changed_here",
        "db_schema_changed_here",
        "db_migration_changed_here",
        "emlis_reply_runtime_changed_here",
        "user_label_connection_runtime_changed_here",
        "p5_runtime_changed_here",
        "p5_gate_relaxed_here",
        "release_material_changed_here",
        "question_trigger_logic_implemented_here",
        "question_api_implemented",
        "question_db_schema_implemented",
        "question_rn_ui_implemented",
        "question_response_key_added",
        "question_response_key_implemented",
        "question_text_implemented_here",
        "draft_question_text_implemented_here",
        "p5_human_blind_qa_confirmed",
        "p6_limited_human_readfeel_start_allowed",
        "p6_limited_human_readfeel_confirmed",
        "p8_detail_design_allowed_here",
        "p8_implementation_spec_finalized_here",
        "p7_complete",
        "p8_start_allowed",
        "release_allowed",
        "actual_human_review_run_here",
        "actual_body_full_packet_generated_here",
        "body_full_writer_created_here",
        "local_reviewer_payload_materialized_here",
        "actual_rating_rows_materialized_here",
        "actual_blocker_rows_materialized_here",
        "actual_execution_blocker_rows_materialized_here",
        "actual_question_need_observation_rows_materialized_here",
        "actual_question_need_observation_summary_materialized_here",
        "actual_disposal_run_here",
        "actual_disposal_receipt_materialized_here",
    ):
        assert boundary[false_key] is False

    assert "Cocolon/screens/InputScreen.js" in boundary["explicit_no_touch_file_refs"]
    assert "services/ai_inference/api_emotion_submit.py" in boundary["explicit_no_touch_file_refs"]
    assert "services/ai_inference/emlis_ai_reply_service.py" in boundary["explicit_no_touch_file_refs"]
    assert "rn_production_files" in boundary["explicit_no_touch_area_refs"]
    assert "api_route_files" in boundary["explicit_no_touch_area_refs"]
    assert "db_schema_migration_files" in boundary["explicit_no_touch_area_refs"]
    assert "p8_question_trigger_logic" in boundary["explicit_no_touch_area_refs"]
    assert "release_material_files" in boundary["explicit_no_touch_area_refs"]


def test_r49_r18_finalizes_r49_implemented_steps_without_p7_or_p8_promotion() -> None:
    boundary = r49.build_p7_r49_touch_candidate_no_touch_boundary_freeze()

    assert tuple(boundary["implemented_steps"]) == r49.P7_R49_R18_IMPLEMENTED_STEPS
    assert tuple(boundary["not_yet_implemented_steps"]) == r49.P7_R49_R18_NOT_YET_IMPLEMENTED_STEPS
    assert boundary["implemented_steps"][-1] == "R18_touch_candidate_no_touch_boundary_freeze"
    assert boundary["not_yet_implemented_steps"] == []
    assert boundary["next_required_step"] == r49.P7_R49_R18_NEXT_REQUIRED_STEP_REF
    assert boundary["post_r18_next_work_ref"] == r49.P7_R49_R18_POST_FREEZE_NEXT_WORK_REF
    assert boundary["next_required_step"] == "P5_human_blind_qa_actual_review_manual_run_decision"
    assert boundary["p7_complete"] is False
    assert boundary["p8_start_allowed"] is False
    assert boundary["release_allowed"] is False


def test_r49_r18_actual_touched_refs_contract_allows_only_declared_current_patch_refs() -> None:
    boundary = r49.build_p7_r49_touch_candidate_no_touch_boundary_freeze()

    assert r49.assert_p7_r49_touch_candidate_no_touch_actual_touched_file_refs_contract(
        r49.P7_R49_R18_CURRENT_PATCH_EXPECTED_TOUCHED_FILE_REFS,
        touch_boundary_freeze=boundary,
    ) is True

    assert r49.assert_p7_r49_touch_candidate_no_touch_actual_touched_file_refs_contract(
        (
            "services/ai_inference/emlis_ai_p7_r49_p5_human_blind_qa_actual_review_execution.py",
            "tests/test_emlis_ai_p7_r49_p5_human_blind_qa_actual_review_execution_r18_20260619.py",
        ),
        touch_boundary_freeze=boundary,
    ) is True


@pytest.mark.parametrize(
    "forbidden_ref",
    [
        "Cocolon/screens/InputScreen.js",
        "services/ai_inference/api_emotion_submit.py",
        "services/ai_inference/emlis_ai_reply_service.py",
        "services/ai_inference/emlis_ai_user_label_connection_gate.py",
    ],
)
def test_r49_r18_actual_touched_refs_contract_rejects_no_touch_refs(forbidden_ref: str) -> None:
    boundary = r49.build_p7_r49_touch_candidate_no_touch_boundary_freeze()

    with pytest.raises(ValueError):
        r49.assert_p7_r49_touch_candidate_no_touch_actual_touched_file_refs_contract(
            (
                "services/ai_inference/emlis_ai_p7_r49_p5_human_blind_qa_actual_review_execution.py",
                forbidden_ref,
            ),
            touch_boundary_freeze=boundary,
        )


def test_r49_r18_contract_rejects_allowed_no_touch_overlap() -> None:
    boundary = r49.build_p7_r49_touch_candidate_no_touch_boundary_freeze()
    boundary["allowed_actual_touched_file_refs"] = list(boundary["allowed_actual_touched_file_refs"]) + [
        "services/ai_inference/api_emotion_submit.py"
    ]

    with pytest.raises(ValueError):
        r49.assert_p7_r49_touch_candidate_no_touch_boundary_freeze_contract(boundary)
