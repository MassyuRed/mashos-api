# -*- coding: utf-8 -*-
"""R50-20 tests for P5 human Blind QA manual-run decision.

These tests stop at body-free touch-candidate/no-touch boundary freeze. They do
not inspect git, do not write files, do not generate body-full packets, do not
run human review, do not start P6/P8, and do not touch API/DB/RN/release
contracts.
"""

from __future__ import annotations

import copy

import pytest

import emlis_ai_p7_r50_p5_human_blind_qa_manual_run_decision as r50


_BODY_LEAK_FIELD_REFS = (
    "raw_input",
    "raw_answer",
    "comment_text",
    "comment_text_body",
    "returned_emlis_surface",
    "bounded_owned_history_review_surface",
    "current_input_review_surface",
    "reviewer_free_text",
    "reviewer_note",
    "reviewer_notes",
    "question_text",
    "draft_question_text",
    "question_body",
    "local_absolute_path",
    "body_content_hash",
    "packet_content_hash",
    "terminal_output",
    "stdout",
    "stderr",
    "traceback",
)

_ALWAYS_FALSE_REFS = (
    "production_runtime_spread_allowed",
    "rn_runtime_spread_allowed",
    "api_db_release_spread_allowed",
    "rn_contract_changed_here",
    "rn_production_files_touched_here",
    "api_route_changed_here",
    "db_schema_changed_here",
    "db_migration_changed_here",
    "emlis_reply_runtime_changed_here",
    "user_label_connection_runtime_changed_here",
    "p5_gate_relaxed_here",
    "question_trigger_logic_implemented_here",
    "question_api_implemented",
    "question_db_schema_implemented",
    "question_rn_ui_implemented",
    "question_response_key_added",
    "question_text_implemented_here",
    "draft_question_text_implemented_here",
    "p6_limited_human_readfeel_start_allowed",
    "p8_detail_design_allowed_here",
    "p8_implementation_spec_finalized_here",
    "p7_complete",
    "p8_start_allowed",
    "release_allowed",
    "actual_human_review_run_here",
    "actual_manual_review_run_here",
    "body_full_packet_generated_here",
    "body_full_packets_created_local_only",
    "actual_disposal_run_here",
    "actual_disposal_receipt_materialized_here",
)


def _walk_keys(value):
    if isinstance(value, dict):
        for key, child in value.items():
            yield str(key)
            yield from _walk_keys(child)
    elif isinstance(value, (list, tuple)):
        for child in value:
            yield from _walk_keys(child)


def _assert_no_body_or_question_text_keys(value):
    keys = set(_walk_keys(value))
    assert not (keys & set(_BODY_LEAK_FIELD_REFS))


def _assert_no_runtime_or_release_spread(material):
    for key in _ALWAYS_FALSE_REFS:
        if key in material:
            assert material[key] is False
    assert material["body_free"] is True
    _assert_no_body_or_question_text_keys(material)


def _blocked_r18_r19_freeze():
    source = r50.build_p7_r50_r16_r17_p6_p8_candidate_handoff_freeze()
    leaky_source = copy.deepcopy(source)
    leaky_source["question_text"] = "body-freeへ残してはいけない質問本文"
    guard = r50.build_p7_r50_no_body_leak_no_question_text_guard_bodyfree(
        source_material_bodyfree=leaky_source
    )
    matrix = r50.build_p7_r50_validation_command_matrix_bodyfree(
        no_body_leak_no_question_text_guard_bodyfree=guard
    )
    return r50.build_p7_r50_r18_r19_no_leak_validation_matrix_freeze(
        no_body_leak_no_question_text_guard_bodyfree=guard,
        validation_command_matrix_bodyfree=matrix,
    )


def test_r50_20_touch_candidate_no_touch_boundary_freezes_only_r50_helper_and_target_tests():
    freeze = r50.build_p7_r50_touch_candidate_no_touch_boundary_freeze()

    assert freeze["schema_version"] == r50.P7_R50_TOUCH_CANDIDATE_NO_TOUCH_BOUNDARY_FREEZE_SCHEMA_VERSION
    assert freeze["policy_section"] == "R50-20_touch_candidate_no_touch_boundary_freeze"
    assert freeze["touch_boundary_status"] == "TOUCH_CANDIDATE_NO_TOUCH_BOUNDARY_FROZEN"
    assert freeze["touch_boundary_freeze_required"] is True
    assert freeze["touch_boundary_freeze_ready"] is True
    assert freeze["validation_matrix_status"] == "VALIDATION_COMMAND_MATRIX_READY"
    assert freeze["production_touch_candidate_file_refs"] == list(r50.P7_R50_PRODUCTION_TOUCH_CANDIDATE_FILE_REFS)
    assert freeze["optional_touch_candidate_file_refs"] == list(r50.P7_R50_OPTIONAL_TOUCH_CANDIDATE_FILE_REFS)
    assert freeze["test_touch_candidate_file_refs"] == list(r50.P7_R50_ALLOWED_TEST_TOUCH_FILE_REFS)
    assert freeze["allowed_actual_touched_file_refs"] == list(r50.P7_R50_ALLOWED_ACTUAL_TOUCHED_FILE_REFS)
    assert freeze["current_patch_expected_touched_file_refs"] == list(r50.P7_R50_R20_CURRENT_PATCH_EXPECTED_TOUCHED_FILE_REFS)
    assert "services/ai_inference/emlis_ai_p7_r50_p5_human_blind_qa_manual_run_decision.py" in freeze["allowed_actual_touched_file_refs"]
    assert "tests/test_emlis_ai_p7_r50_p5_human_blind_qa_manual_run_decision_r20_20260620.py" in freeze["allowed_actual_touched_file_refs"]
    assert set(freeze["allowed_actual_touched_file_refs"]).isdisjoint(freeze["explicit_no_touch_file_refs"])
    assert set(freeze["current_patch_expected_touched_file_refs"]).issubset(freeze["allowed_actual_touched_file_refs"])
    assert set(freeze["current_patch_expected_touched_file_refs"]).isdisjoint(freeze["explicit_no_touch_file_refs"])
    assert freeze["next_required_step"] == r50.P7_R50_R20_NEXT_REQUIRED_STEP_REF
    assert freeze["post_r20_next_work_ref"] == r50.P7_R50_R20_POST_FREEZE_NEXT_WORK_REF
    assert tuple(freeze["implemented_steps"]) == r50.P7_R50_R20_IMPLEMENTED_STEPS
    assert tuple(freeze["not_yet_implemented_steps"]) == r50.P7_R50_R20_NOT_YET_IMPLEMENTED_STEPS
    _assert_no_runtime_or_release_spread(freeze)


def test_r50_20_explicit_no_touch_refs_include_runtime_rn_api_db_p8_and_release_boundaries():
    freeze = r50.build_p7_r50_touch_candidate_no_touch_boundary_freeze()
    no_touch = set(freeze["explicit_no_touch_file_refs"])
    no_touch_areas = set(freeze["explicit_no_touch_area_refs"])

    assert "Cocolon/screens/InputScreen.js" in no_touch
    assert "Cocolon/screens/input/InputFeedbackReplyModal.js" in no_touch
    assert "Cocolon/tests/rn-screen-contracts.test.js" in no_touch
    assert "services/ai_inference/api_emotion_submit.py" in no_touch
    assert "services/ai_inference/emotion_submit_service.py" in no_touch
    assert "services/ai_inference/emlis_ai_reply_service.py" in no_touch
    assert "services/ai_inference/emlis_ai_user_label_connection_gate.py" in no_touch
    assert "services/ai_inference/emlis_ai_p7_r49_p5_human_blind_qa_actual_review_execution.py" in no_touch
    assert "rn_production_files" in no_touch_areas
    assert "api_route_files" in no_touch_areas
    assert "db_schema_migration_files" in no_touch_areas
    assert "p8_question_api_db_rn_response_key" in no_touch_areas
    assert "release_material_files" in no_touch_areas
    assert "body_full_packet_artifact_files" in no_touch_areas
    _assert_no_runtime_or_release_spread(freeze)


def test_r50_20_boundary_blocks_when_r19_validation_matrix_is_blocked_without_opening_runtime_touch():
    blocked_r19 = _blocked_r18_r19_freeze()
    freeze = r50.build_p7_r50_touch_candidate_no_touch_boundary_freeze(
        r18_r19_no_leak_validation_matrix_freeze=blocked_r19
    )

    assert blocked_r19["validation_matrix_status"] == "BLOCKED_BY_R50_18_NO_BODY_LEAK_GUARD"
    assert freeze["touch_boundary_status"] == "BLOCKED_BY_R50_19_VALIDATION_MATRIX"
    assert freeze["touch_boundary_freeze_ready"] is False
    assert freeze["next_required_step"] == r50.P7_R50_R20_BLOCKED_NEXT_REQUIRED_STEP_REF
    assert freeze["touch_candidate_boundary_frozen"] is True
    assert freeze["no_touch_boundary_frozen"] is True
    assert freeze["actual_touched_file_refs_checked_here"] is False
    assert freeze["actual_touched_file_refs_materialized_here"] is False
    _assert_no_runtime_or_release_spread(freeze)


def test_r50_20_actual_touched_refs_contract_accepts_current_patch_refs_and_rejects_no_touch_refs():
    freeze = r50.build_p7_r50_touch_candidate_no_touch_boundary_freeze()

    assert r50.assert_p7_r50_touch_candidate_no_touch_actual_touched_file_refs_contract(
        r50.P7_R50_R20_CURRENT_PATCH_EXPECTED_TOUCHED_FILE_REFS,
        touch_boundary_freeze=freeze,
    )

    with pytest.raises(ValueError):
        r50.assert_p7_r50_touch_candidate_no_touch_actual_touched_file_refs_contract(
            ["Cocolon/screens/InputScreen.js"],
            touch_boundary_freeze=freeze,
        )
    with pytest.raises(ValueError):
        r50.assert_p7_r50_touch_candidate_no_touch_actual_touched_file_refs_contract(
            ["services/ai_inference/emlis_ai_reply_service.py"],
            touch_boundary_freeze=freeze,
        )
    with pytest.raises(ValueError):
        r50.assert_p7_r50_touch_candidate_no_touch_actual_touched_file_refs_contract(
            ["services/ai_inference/unlisted_runtime_file.py"],
            touch_boundary_freeze=freeze,
        )


def test_r50_20_contract_rejects_runtime_p8_release_spread_or_no_touch_drift():
    freeze = r50.build_p7_r50_touch_candidate_no_touch_boundary_freeze()

    for key in (
        "rn_production_files_touched_here",
        "api_route_changed_here",
        "db_schema_changed_here",
        "emlis_reply_runtime_changed_here",
        "question_api_implemented",
        "p8_start_allowed",
        "release_allowed",
    ):
        drift = copy.deepcopy(freeze)
        drift[key] = True
        with pytest.raises(ValueError):
            r50.assert_p7_r50_touch_candidate_no_touch_boundary_freeze_contract(drift)

    drift = copy.deepcopy(freeze)
    drift["current_patch_expected_touched_file_refs"].append("Cocolon/screens/InputScreen.js")
    with pytest.raises(ValueError):
        r50.assert_p7_r50_touch_candidate_no_touch_boundary_freeze_contract(drift)

    drift = copy.deepcopy(freeze)
    drift["allowed_actual_touched_file_refs"].append("Cocolon/screens/InputScreen.js")
    with pytest.raises(ValueError):
        r50.assert_p7_r50_touch_candidate_no_touch_boundary_freeze_contract(drift)


def test_r50_20_new_exports_are_available_via_star_import():
    namespace: dict[str, object] = {}
    exec("from emlis_ai_p7_r50_p5_human_blind_qa_manual_run_decision import *", namespace)

    assert "P7_R50_TOUCH_CANDIDATE_NO_TOUCH_BOUNDARY_FREEZE_SCHEMA_VERSION" in namespace
    assert "build_p7_r50_touch_candidate_no_touch_boundary_freeze" in namespace
    assert "assert_p7_r50_touch_candidate_no_touch_boundary_freeze_contract" in namespace
    assert "assert_p7_r50_touch_candidate_no_touch_actual_touched_file_refs_contract" in namespace
