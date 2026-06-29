# -*- coding: utf-8 -*-
from __future__ import annotations

import json
from copy import deepcopy
from functools import lru_cache

import pytest

import emlis_ai_p7_r48_p5_human_blind_qa_actual_review_packet as r48
import emlis_ai_p7_r49_p5_human_blind_qa_actual_review_execution as r49

SECRET_INPUT = "R49 secret raw input must not enter body-free R2/R3 material"
SECRET_SURFACE = "R49 returned Emlis surface must not enter body-free R2/R3 material"
SECRET_REVIEWER = "R49 reviewer free text must not enter body-free R2/R3 material"
SECRET_QUESTION = "R49 draft question text must not enter body-free R2/R3 material"


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
    ):
        assert forbidden_true not in dumped.lower()


@lru_cache(maxsize=1)
def _cached_r49_r2() -> tuple[dict[str, object]]:
    r2 = r49.build_p7_r49_r48_case_matrix_handoff_validation()
    assert r49.assert_p7_r49_r48_case_matrix_handoff_validation_contract(r2) is True
    return (r2,)


def _r49_r2() -> dict[str, object]:
    return deepcopy(_cached_r49_r2()[0])


def test_r49_r2_validates_r48_24_case_matrix_handoff_without_bodyfull_or_reviewer_hidden_refs() -> None:
    r2 = _r49_r2()

    assert r2["schema_version"] == r49.P7_R49_R48_CASE_MATRIX_HANDOFF_VALIDATION_SCHEMA_VERSION
    assert set(r2) == set(r49.P7_R49_R48_CASE_MATRIX_HANDOFF_VALIDATION_REQUIRED_FIELD_REFS)
    assert r2["policy_section"] == "R49-2_r48_case_matrix_handoff_validation"
    assert r2["review_kind"] == r49.P7_R49_REVIEW_KIND == r48.P7_R48_REVIEW_KIND
    assert r2["packet_kind"] == r49.P7_R49_PACKET_KIND == r48.P7_R48_PACKET_KIND
    assert r2["r48_case_matrix_handoff_required"] is True
    assert r2["r48_case_matrix_handoff_validated"] is True
    assert r2["r48_case_matrix_schema_version"] == r48.P7_R48_P5_CASE_MATRIX_SCHEMA_VERSION
    assert r2["r48_r2_r3_case_matrix_freeze_schema_version"] == r48.P7_R48_R2_R3_LOCAL_STORAGE_CASE_MATRIX_FREEZE_SCHEMA_VERSION

    assert r2["required_total_cases"] == 24
    assert r2["case_count"] == 24
    assert r2["case_manifest_row_count"] == 24
    assert r2["family_coverage_satisfied"] is True
    assert r2["minimums_satisfied"] is True
    assert r2["owned_history_positive_case_count"] == 20
    assert r2["case_ref_id_count"] == 24
    assert r2["blind_case_id_count"] == 24
    assert r2["packet_ref_id_count"] == 24
    assert r2["blind_case_id_case_ref_separated"] is True
    assert r2["packet_ref_id_present_for_all_cases"] is True

    expected_family_counts = {
        "history_line_eligible_input": 4,
        "standard_state_answer_owned_history": 4,
        "self_understanding_owned_history": 3,
        "uncertainty_support_owned_history": 3,
        "change_future_intention_owned_history": 3,
        "relationship_gratitude_recovery_owned_history": 3,
        "low_information_history_not_eligible": 2,
        "free_tier_history_present_not_allowed": 2,
    }
    assert r2["family_case_counts"] == expected_family_counts
    assert r2["case_role_counts"] == {
        "positive_history_line": 4,
        "positive_owned_history": 16,
        "boundary_no_history_line": 4,
    }

    for row in r2["case_manifest_rows"]:
        assert set(row) == set(r49.P7_R49_R48_CASE_MATRIX_HANDOFF_ROW_FIELD_REFS)
        assert row["case_ref_id"] != row["blind_case_id"]
        assert row["packet_ref_id"]
        assert row["controller_only"] is True
        assert row["reviewer_facing_identifier_policy"] == "blind_case_id_only"
        assert row["reviewer_receives_blind_case_id"] is True
        assert row["reviewer_receives_case_ref_id"] is False
        assert row["reviewer_receives_family"] is False
        assert row["reviewer_receives_subscription_tier"] is False
        assert row["reviewer_receives_expected_result"] is False
        assert row["reviewer_receives_gate_result"] is False
        assert row["body_full_packet_materialized_here"] is False
        assert row["local_reviewer_payload_materialized_here"] is False
        assert row["body_free"] is True

    assert tuple(r2["implemented_steps"]) == r49.P7_R49_R2_IMPLEMENTED_STEPS
    assert tuple(r2["not_yet_implemented_steps"]) == r49.P7_R49_R2_NOT_YET_IMPLEMENTED_STEPS
    assert r2["next_required_step"] == r49.P7_R49_R2_NEXT_REQUIRED_STEP_REF
    assert r2["actual_case_matrix_materialized_here"] is False
    assert r2["body_full_packet_materialized_here"] is False
    assert r2["actual_body_full_packet_generated_here"] is False
    assert r2["actual_human_review_run_here"] is False
    assert r2["question_need_observation_required"] is True
    assert r2["question_need_observation_rows_required_later"] is True

    _assert_no_body_question_or_release_promotion(r2)


def test_r49_r2_rejects_case_count_mismatch_and_blind_case_id_controller_case_ref_collapse() -> None:
    r48_freeze = r48.build_p7_r48_r2_r3_local_storage_case_matrix_freeze()
    mutated = deepcopy(r48_freeze)
    mutated["p5_case_matrix"]["case_rows"] = mutated["p5_case_matrix"]["case_rows"][:-1]
    mutated["p5_case_matrix"]["case_count"] = 23
    mutated["case_count"] = 23
    with pytest.raises(ValueError):
        r49.build_p7_r49_r48_case_matrix_handoff_validation(r48_case_matrix_handoff=mutated)

    collapsed = r49.build_p7_r49_r48_case_matrix_handoff_validation()
    collapsed["case_manifest_rows"][0]["blind_case_id"] = collapsed["case_manifest_rows"][0]["case_ref_id"]
    with pytest.raises(ValueError):
        r49.assert_p7_r49_r48_case_matrix_handoff_validation_contract(collapsed)


@pytest.mark.parametrize(
    ("kwargs", "expected_blocker"),
    [
        ({}, "r49_review_session_blocked_missing_local_root"),
        (
            {"local_review_root": "/tmp/cocolon_r49_review_root_missing_allow"},
            "r49_review_session_blocked_missing_explicit_allow",
        ),
        (
            {"local_review_root": "/mnt/data/cocolon_r49_review_root", "explicit_body_full_generation_allow": True},
            "r49_review_session_blocked_invalid_local_root",
        ),
        (
            {
                "local_review_root": "/tmp/cocolon_r49_review_root_export_violation",
                "explicit_body_full_generation_allow": True,
                "candidate_export_refs": ["body_full_packets.local_only/example.local_only.json"],
            },
            "r49_review_session_blocked_body_full_packet_export_violation",
        ),
    ],
)
def test_r49_r3_blocks_local_only_packet_generation_preflight_with_bodyfree_execution_blocker_ids(
    kwargs: dict[str, object],
    expected_blocker: str,
) -> None:
    r3 = r49.build_p7_r49_local_only_actual_packet_generation_preflight(
        r49_r48_case_matrix_handoff_validation=_r49_r2(),
        **kwargs,
    )
    assert r49.assert_p7_r49_local_only_actual_packet_generation_preflight_contract(r3) is True

    assert r3["schema_version"] == r49.P7_R49_LOCAL_ONLY_ACTUAL_PACKET_GENERATION_PREFLIGHT_SCHEMA_VERSION
    assert set(r3) == set(r49.P7_R49_LOCAL_ONLY_ACTUAL_PACKET_GENERATION_PREFLIGHT_REQUIRED_FIELD_REFS)
    assert r3["policy_section"] == "R49-3_local_only_actual_packet_generation_preflight"
    assert r3["preflight_status"] == "BLOCKED"
    assert r3["review_session_status"] == "PRECHECK_BLOCKED"
    assert expected_blocker in r3["execution_blocker_ids"]
    assert r3["execution_blocker_count"] == len(r3["execution_blocker_ids"])
    assert r3["local_only_packet_generation_preflight_passed"] is False
    assert r3["local_only_packet_generation_allowed_by_preflight"] is False
    assert r3["body_full_packet_materialization_allowed_by_preflight"] is False
    assert r3["root_path_exposed"] is False
    assert r3["local_absolute_path_included"] is False
    assert r3["local_packet_export_allowed"] is False
    assert r3["body_full_packet_export_allowed"] is False
    assert r3["body_full_packet_git_tracking_allowed"] is False
    assert r3["body_full_packet_zip_inclusion_allowed"] is False
    assert r3["body_content_hash_storage_allowed"] is False
    assert r3["body_free_material_can_include_local_packet_payload"] is False
    assert r3["preflight_does_not_generate_packet"] is True
    assert r3["body_full_packet_materialized_here"] is False
    assert r3["actual_body_full_packet_generated_here"] is False
    assert r3["body_full_writer_created_here"] is False
    assert r3["actual_human_review_run_here"] is False
    assert r3["actual_question_need_observation_rows_materialized_here"] is False
    assert tuple(r3["implemented_steps"]) == r49.P7_R49_R2_R3_IMPLEMENTED_STEPS
    assert tuple(r3["not_yet_implemented_steps"]) == r49.P7_R49_R2_R3_NOT_YET_IMPLEMENTED_STEPS
    assert r3["next_required_step"] == r49.P7_R49_R3_NEXT_REQUIRED_STEP_REF

    _assert_no_body_question_or_release_promotion(r3)


def test_r49_r3_ready_preflight_allows_later_local_only_generation_but_does_not_materialize_packets() -> None:
    r3 = r49.build_p7_r49_local_only_actual_packet_generation_preflight(
        r49_r48_case_matrix_handoff_validation=_r49_r2(),
        local_review_root="/tmp/cocolon_r49_valid_external_local_review_root",
        explicit_body_full_generation_allow=True,
    )
    assert r49.assert_p7_r49_local_only_actual_packet_generation_preflight_contract(r3) is True

    assert r3["preflight_status"] == "READY_FOR_LOCAL_ONLY_PACKET_GENERATION"
    assert r3["review_session_status"] == "NOT_STARTED"
    assert r3["execution_blocker_ids"] == []
    assert r3["execution_blocker_count"] == 0
    assert r3["local_review_root_status"] == "valid"
    assert r3["local_review_root_valid"] is True
    assert r3["explicit_body_full_generation_allow"] is True
    assert r3["local_only_packet_generation_preflight_passed"] is True
    assert r3["local_only_packet_generation_allowed_by_preflight"] is True
    assert r3["body_full_packet_materialization_allowed_by_preflight"] is True
    assert r3["body_full_packet_materialization_block_reason_ids"] == []
    assert r3["export_violation_reason_ids"] == []
    assert r3["preflight_does_not_generate_packet"] is True
    assert r3["body_full_packet_materialized_here"] is False
    assert r3["actual_body_full_packet_generated_here"] is False
    assert r3["body_full_writer_created_here"] is False
    assert r3["actual_human_review_run_here"] is False
    assert r3["actual_rating_rows_materialized_here"] is False
    assert r3["actual_disposal_run_here"] is False
    assert r3["generated_local_packet_schema_version"] == r48.P7_R48_P5_REVIEWER_PACKET_LOCAL_ONLY_SCHEMA_VERSION

    _assert_no_body_question_or_release_promotion(r3)


def test_r49_r2_r3_combined_freeze_preserves_closed_p7_p8_release_state() -> None:
    freeze = r49.build_p7_r49_r2_r3_case_matrix_preflight_freeze()
    assert r49.assert_p7_r49_r2_r3_case_matrix_preflight_freeze_contract(freeze) is True

    assert freeze["schema_version"] == r49.P7_R49_R2_R3_CASE_MATRIX_PREFLIGHT_FREEZE_SCHEMA_VERSION
    assert set(freeze) == set(r49.P7_R49_R2_R3_CASE_MATRIX_PREFLIGHT_FREEZE_REQUIRED_FIELD_REFS)
    assert tuple(freeze["implemented_steps"]) == r49.P7_R49_R2_R3_IMPLEMENTED_STEPS
    assert tuple(freeze["not_yet_implemented_steps"]) == r49.P7_R49_R2_R3_NOT_YET_IMPLEMENTED_STEPS
    assert freeze["preflight_status"] == "BLOCKED"
    assert freeze["execution_blocker_ids"] == ["r49_review_session_blocked_missing_local_root"]
    assert freeze["local_only_packet_generation_allowed_by_preflight"] is False
    assert freeze["body_full_packet_materialized_here"] is False
    assert freeze["actual_body_full_packet_generated_here"] is False
    assert freeze["actual_human_review_run_here"] is False
    assert freeze["question_need_observation_required"] is True
    assert freeze["question_need_observation_rows_required_later"] is True
    assert freeze["next_required_step"] == r49.P7_R49_R3_NEXT_REQUIRED_STEP_REF
    assert freeze["p5_human_blind_qa_confirmed"] is False
    assert freeze["p6_limited_human_readfeel_start_allowed"] is False
    assert freeze["p7_complete"] is False
    assert freeze["p8_start_allowed"] is False
    assert freeze["release_allowed"] is False

    _assert_no_body_question_or_release_promotion(freeze)
