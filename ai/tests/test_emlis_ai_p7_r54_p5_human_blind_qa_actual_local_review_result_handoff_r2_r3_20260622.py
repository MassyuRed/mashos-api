# -*- coding: utf-8 -*-
from __future__ import annotations

import json
from copy import deepcopy
from functools import lru_cache

import pytest

import emlis_ai_p7_r54_p5_human_blind_qa_actual_local_review_result_handoff as r54


FORBIDDEN_DUMP_TOKENS = (
    '"raw_input":',
    '"raw_answer":',
    '"comment_text":',
    '"comment_text_body":',
    '"returned_emlis_surface":',
    '"current_input_review_surface":',
    '"bounded_owned_history_review_surface":',
    '"reviewer_free_text":',
    '"reviewer_note":',
    '"reviewer_notes":',
    '"question_text":',
    '"draft_question_text":',
    '"question_body":',
    '"local_absolute_path":',
    '"body_content_hash":',
    '"packet_content_hash":',
    '"terminal_output": "',
    '"stdout":',
    '"stderr":',
    '"traceback":',
)
FORBIDDEN_TRUE_TOKENS = (
    '"release_allowed": true',
    '"p7_complete": true',
    '"p8_start_allowed": true',
    '"hold004_close_allowed": true',
    '"p6_limited_human_readfeel_start_allowed": true',
    '"question_trigger_logic_implemented": true',
    '"p8_question_implementation_spec_finalized_here": true',
    '"api_db_rn_response_key_changed_here": true',
    '"runtime_changed_here": true',
    '"actual_human_review_run_here": true',
    '"actual_manual_review_run_here": true',
    '"body_full_packet_generated_here": true',
    '"body_full_packets_created_local_only": true',
    '"actual_rating_rows_materialized_here": true',
    '"actual_question_need_observation_rows_materialized_here": true',
    '"actual_disposal_receipt_materialized_here": true',
    '"full_backend_suite_green_confirmed": true',
    '"backend_collect_only_claimed_as_full_backend_green": true',
    '"r49_all_in_one_green_claimed": true',
    '"r53_all_in_one_green_claimed": true',
    '"actual_review_evidence_claimed": true',
    '"product_value_claimed": true',
    '"release_readiness_claimed": true',
)


def _assert_body_free_no_promotion(material: dict[str, object]) -> None:
    dumped = json.dumps(material, ensure_ascii=False, sort_keys=True).lower()
    for forbidden in FORBIDDEN_DUMP_TOKENS:
        assert forbidden not in dumped
    for forbidden in FORBIDDEN_TRUE_TOKENS:
        assert forbidden not in dumped


@lru_cache(maxsize=1)
def _cached_r54_r2() -> tuple[dict[str, object]]:
    intake = r54.build_p7_r54_validation_evidence_intake_bodyfree()
    assert r54.assert_p7_r54_validation_evidence_intake_bodyfree_contract(intake) is True
    return (intake,)


def _r54_r2() -> dict[str, object]:
    return deepcopy(_cached_r54_r2()[0])


def _ready_root(tmp_path) -> str:
    root = tmp_path / "r54_external_local_review_root"
    root.mkdir()
    return str(root)


def _ready_purge_plan() -> dict[str, object]:
    return r54.build_p7_r54_default_local_only_purge_plan_bodyfree()


def test_r54_r2_intakes_r49_to_r53_validation_evidence_with_claim_boundaries() -> None:
    intake = _r54_r2()

    assert intake["schema_version"] == r54.P7_R54_VALIDATION_EVIDENCE_INTAKE_SCHEMA_VERSION
    assert set(intake) == set(r54.P7_R54_VALIDATION_EVIDENCE_INTAKE_REQUIRED_FIELD_REFS)
    assert intake["phase"].startswith("P7_")
    assert intake["step"] == r54.P7_R54_STEP
    assert intake["scope"] == r54.P7_R54_SCOPE
    assert intake["policy_section"] == "R54-2_r49_to_r53_validation_evidence_intake"
    assert intake["source_mode"] == "local_snapshot"
    assert intake["git_connection_required"] is False
    assert intake["git_checked"] is False
    assert intake["body_free"] is True

    assert intake["current_received_snapshot_refs"] == r54.P7_R54_CURRENT_RECEIVED_SNAPSHOT_REFS
    assert intake["actual_review_basis_ref"] == "r54_current_received_snapshot_refs"
    assert intake["actual_review_basis_allowed"] == "current_ref_only"
    assert intake["validation_evidence_group_refs"] == list(r54.P7_R54_VALIDATION_EVIDENCE_GROUP_REFS)
    assert intake["validation_evidence_required_group_refs"] == list(r54.P7_R54_VALIDATION_EVIDENCE_REQUIRED_GROUP_REFS)
    assert intake["validation_evidence_optional_group_refs"] == list(r54.P7_R54_VALIDATION_EVIDENCE_OPTIONAL_GROUP_REFS)
    assert intake["validation_evidence_row_count"] == 10
    assert intake["validation_evidence_required_groups_present"] is True
    assert intake["validation_evidence_intake_status"] == "VALIDATION_INTAKE_READY"
    assert intake["validation_evidence_ready_for_r54_3_preflight"] is True
    assert intake["local_only_actual_review_preflight_allowed_after_r54_2"] is True
    assert intake["next_required_step"] == r54.P7_R54_R2_NEXT_REQUIRED_STEP_REF

    expected_counts = {
        "rn_contract_36_passed": ("individual", 36, 0, 0),
        "r49_individual_split_76_passed": ("individual", 76, 0, 0),
        "r50_target_99_passed": ("split", 99, 0, 0),
        "r51_target_125_passed": ("split", 125, 0, 0),
        "r52_target_219_passed": ("split", 219, 0, 0),
        "r53_py_compile_passed": ("individual", 0, 0, 0),
        "r53_target_split_291_passed": ("split", 291, 0, 0),
        "backend_collect_only_4101_collected_1_warning": ("collect_only", 0, 4101, 1),
        "r49_all_in_one_timeout_unclaimed": ("all_in_one", 0, 0, 0),
        "r53_all_in_one_timeout_unclaimed": ("all_in_one", 0, 0, 0),
    }
    rows = intake["validation_evidence_rows"]
    assert [row["evidence_group_ref"] for row in rows] == list(expected_counts)
    for row in rows:
        assert r54.assert_p7_r54_validation_evidence_row_contract(row) is True
        mode, passed, collected, warnings = expected_counts[row["evidence_group_ref"]]
        assert row["execution_mode"] == mode
        assert row["passed_count"] == passed
        assert row["collected_count"] == collected
        assert row["warning_count"] == warnings
        assert row["failed_count"] == 0
        assert row["full_suite_green_claimed"] is False
        assert row["product_value_claimed"] is False
        assert row["release_readiness_claimed"] is False
        assert row["actual_review_evidence_claimed"] is False
        assert row["body_free"] is True

    by_group = {row["evidence_group_ref"]: row for row in rows}
    assert by_group["backend_collect_only_4101_collected_1_warning"]["collect_only"] is True
    assert by_group["backend_collect_only_4101_collected_1_warning"]["required_for_r54_3_preflight"] is False
    assert by_group["r49_all_in_one_timeout_unclaimed"]["timeout_observed"] is True
    assert by_group["r53_all_in_one_timeout_unclaimed"]["timeout_observed"] is True
    assert intake["backend_collect_only_claimed_as_full_backend_green"] is False
    assert intake["full_backend_suite_green_confirmed"] is False
    assert intake["r49_all_in_one_green_claimed"] is False
    assert intake["r53_all_in_one_green_claimed"] is False
    assert intake["actual_review_evidence_claimed"] is False
    assert intake["product_value_claimed"] is False
    assert intake["release_readiness_claimed"] is False
    assert intake["body_full_packet_generation_allowed_after_r54_2"] is False
    assert intake["actual_review_generation_allowed_after_r54_2"] is False
    assert tuple(intake["implemented_steps"]) == r54.P7_R54_R2_IMPLEMENTED_STEPS
    assert tuple(intake["not_yet_implemented_steps"]) == r54.P7_R54_R2_NOT_YET_IMPLEMENTED_STEPS

    _assert_body_free_no_promotion(intake)


@pytest.mark.parametrize(
    "group_ref,patch,expected_blocker",
    [
        ("rn_contract_36_passed", {"evidence_present": False}, "r54_rn_contract_36_passed_missing"),
        ("r49_individual_split_76_passed", {"evidence_present": False}, "r54_r49_individual_split_76_passed_missing"),
        ("r53_target_split_291_passed", {"evidence_present": False}, "r54_r53_target_split_291_passed_missing"),
    ],
)
def test_r54_r2_blocks_when_required_validation_evidence_is_missing(group_ref: str, patch: dict[str, object], expected_blocker: str) -> None:
    intake = r54.build_p7_r54_validation_evidence_intake_bodyfree(
        validation_evidence_overrides={group_ref: patch},
    )
    assert intake["validation_evidence_intake_status"] == "VALIDATION_INTAKE_BLOCKED"
    assert intake["validation_evidence_ready_for_r54_3_preflight"] is False
    assert "r54_validation_evidence_required_groups_missing" in intake["execution_blocker_ids"]
    assert expected_blocker in intake["execution_blocker_ids"]
    assert intake["local_only_actual_review_preflight_allowed_after_r54_2"] is False
    assert intake["next_required_step"] == r54.P7_R54_R2_BLOCKED_NEXT_REQUIRED_STEP_REF
    assert r54.assert_p7_r54_validation_evidence_intake_bodyfree_contract(intake) is True
    _assert_body_free_no_promotion(intake)


@pytest.mark.parametrize(
    "group_ref,patch",
    [
        ("backend_collect_only_4101_collected_1_warning", {"full_suite_green_claimed": True}),
        ("r49_all_in_one_timeout_unclaimed", {"claim_level": "all_in_one_green"}),
        ("r53_all_in_one_timeout_unclaimed", {"full_suite_green_claimed": True}),
        ("r50_target_99_passed", {"actual_review_evidence_claimed": True}),
        ("r51_target_125_passed", {"product_value_claimed": True}),
        ("r52_target_219_passed", {"release_readiness_claimed": True}),
    ],
)
def test_r54_r2_rejects_collect_only_timeout_actual_review_product_or_release_claim_inflation(group_ref: str, patch: dict[str, object]) -> None:
    with pytest.raises(ValueError):
        r54.build_p7_r54_validation_evidence_intake_bodyfree(
            validation_evidence_overrides={group_ref: patch},
        )


@pytest.mark.parametrize(
    "key,value",
    [
        ("backend_collect_only_claimed_as_full_backend_green", True),
        ("full_backend_suite_green_confirmed", True),
        ("r49_all_in_one_green_claimed", True),
        ("r53_all_in_one_green_claimed", True),
        ("actual_review_evidence_claimed", True),
        ("product_value_claimed", True),
        ("release_readiness_claimed", True),
        ("actual_human_review_run_here", True),
        ("body_full_packet_generated_here", True),
        ("p5_human_blind_qa_confirmed_candidate", True),
        ("p6_limited_human_readfeel_start_allowed", True),
        ("p8_start_allowed", True),
        ("release_allowed", True),
        ("api_db_rn_response_key_changed_here", True),
        ("validation_evidence_intake_done_here", False),
    ],
)
def test_r54_r2_rejects_top_level_validation_inflation_or_promotion_mutation(key: str, value: object) -> None:
    material = _r54_r2()
    material[key] = value
    with pytest.raises(ValueError):
        r54.assert_p7_r54_validation_evidence_intake_bodyfree_contract(material)


def test_r54_r3_blocks_by_default_before_local_root_allow_and_purge_plan() -> None:
    preflight = r54.build_p7_r54_local_only_actual_review_preflight_bodyfree(
        validation_evidence_intake=_r54_r2(),
    )

    assert preflight["schema_version"] == r54.P7_R54_LOCAL_ONLY_ACTUAL_REVIEW_PREFLIGHT_SCHEMA_VERSION
    assert set(preflight) == set(r54.P7_R54_LOCAL_ONLY_ACTUAL_REVIEW_PREFLIGHT_REQUIRED_FIELD_REFS)
    assert preflight["policy_section"] == "R54-3_local_only_root_explicit_allow_purge_plan_preflight"
    assert preflight["preflight_status"] == "R54_LOCAL_REVIEW_PREFLIGHT_BLOCKED"
    assert preflight["r2_validation_evidence_ready_for_r54_3_preflight"] is True
    assert preflight["local_review_root_env_var"] == "COCOLON_EMLIS_LOCAL_REVIEW_ROOT"
    assert preflight["local_review_root_configured"] is False
    assert preflight["local_review_root_valid"] is False
    assert preflight["explicit_allow_env_var"] == r54.P7_R54_EXPLICIT_LOCAL_REVIEW_ALLOW_ENV_VAR
    assert preflight["explicit_allow_present"] is False
    assert preflight["purge_plan_present"] is False
    assert preflight["purge_plan_ready"] is False
    assert preflight["retention_policy_present"] is False
    assert preflight["export_denylist_present"] is True
    assert preflight["body_full_packet_retention_max_hours"] == 72
    assert preflight["reviewer_notes_retention_after_rating_finalized_max_hours"] == 24
    assert preflight["body_full_packet_export_allowed"] is False
    assert preflight["reviewer_notes_export_allowed"] is False
    assert preflight["body_full_packet_zip_inclusion_allowed"] is False
    assert preflight["local_only_body_full_generation_allowed_before_preflight"] is False
    assert preflight["local_only_body_full_generation_allowed_after_preflight"] is False
    assert preflight["body_full_generation_allowed"] is False
    assert preflight["actual_review_session_envelope_allowed_after_r54_3"] is False
    assert preflight["actual_human_review_run_here"] is False
    assert preflight["body_full_packet_generated_here"] is False
    assert preflight["local_root_preflight_passed_here"] is False
    assert preflight["explicit_allow_present_here"] is False
    assert preflight["purge_plan_verified_here"] is False
    assert preflight["next_required_step"] == r54.P7_R54_R3_BLOCKED_NEXT_REQUIRED_STEP_REF
    assert "r54_local_review_root_missing" in preflight["execution_blocker_ids"]
    assert "r54_explicit_allow_missing" in preflight["execution_blocker_ids"]
    assert "r54_purge_plan_missing" in preflight["execution_blocker_ids"]
    assert "r54_retention_policy_missing" in preflight["execution_blocker_ids"]

    assert r54.assert_p7_r54_local_only_actual_review_preflight_bodyfree_contract(preflight) is True
    _assert_body_free_no_promotion(preflight)


def test_r54_r3_ready_when_local_root_allow_purge_retention_and_export_denylist_are_clear(tmp_path) -> None:
    preflight = r54.build_p7_r54_local_only_actual_review_preflight_bodyfree(
        validation_evidence_intake=_r54_r2(),
        local_review_root=_ready_root(tmp_path),
        explicit_allow_token=r54.P7_R54_EXPLICIT_LOCAL_REVIEW_ALLOW_TOKEN_REF,
        purge_plan=_ready_purge_plan(),
        export_candidate_refs=("bodyfree/result_handoff.json",),
    )

    assert preflight["preflight_status"] == "R54_LOCAL_REVIEW_PREFLIGHT_READY"
    assert preflight["execution_blocker_ids"] == []
    assert preflight["open_execution_blocker_ids"] == []
    assert preflight["local_review_root_configured"] is True
    assert preflight["local_review_root_valid"] is True
    assert preflight["storage_root_ref"] == "external_local_review_root"
    assert preflight["root_path_exposed"] is False
    assert preflight["local_absolute_path_included"] is False
    assert preflight["explicit_allow_present"] is True
    assert preflight["explicit_allow_token_body_stored_here"] is False
    assert preflight["purge_plan_present"] is True
    assert preflight["purge_plan_status"] == "READY"
    assert preflight["purge_plan_ready"] is True
    assert preflight["purge_plan_required_before_body_full_generation"] is True
    assert tuple(preflight["purge_plan_required_delete_target_refs"]) == r54.P7_R51_PURGE_PLAN_REQUIRED_DELETE_TARGET_REFS
    assert preflight["retention_policy_present"] is True
    assert preflight["export_denylist_present"] is True
    assert preflight["export_candidate_refs_checked_count"] == 1
    assert preflight["denied_export_candidate_count"] == 0
    assert preflight["export_denylist_violation_refs"] == []
    assert preflight["export_candidate_refs_stored_here"] is False
    assert preflight["export_candidate_body_stored_here"] is False
    assert preflight["body_full_packet_export_allowed"] is False
    assert preflight["body_full_packet_zip_inclusion_allowed"] is False
    assert preflight["body_full_generation_allowed"] is True
    assert preflight["local_only_body_full_generation_allowed_after_preflight"] is True
    assert preflight["actual_review_session_envelope_allowed_after_r54_3"] is True
    assert preflight["actual_human_review_run_here"] is False
    assert preflight["actual_manual_review_run_here"] is False
    assert preflight["body_full_packet_generated_here"] is False
    assert preflight["body_full_packets_created_local_only"] is False
    assert preflight["validation_evidence_intake_done_here"] is True
    assert preflight["local_root_preflight_passed_here"] is True
    assert preflight["explicit_allow_present_here"] is True
    assert preflight["purge_plan_verified_here"] is True
    assert preflight["next_required_step"] == r54.P7_R54_R3_NEXT_REQUIRED_STEP_REF
    assert tuple(preflight["implemented_steps"]) == r54.P7_R54_R3_IMPLEMENTED_STEPS
    assert tuple(preflight["not_yet_implemented_steps"]) == r54.P7_R54_R3_NOT_YET_IMPLEMENTED_STEPS

    assert r54.assert_p7_r54_local_only_actual_review_preflight_bodyfree_contract(preflight) is True
    _assert_body_free_no_promotion(preflight)


def test_r54_r3_blocks_repo_or_artifact_root_without_exposing_path(tmp_path) -> None:
    preflight = r54.build_p7_r54_local_only_actual_review_preflight_bodyfree(
        validation_evidence_intake=_r54_r2(),
        local_review_root="/mnt/data/r54_body_full_packets",
        explicit_allow_token=r54.P7_R54_EXPLICIT_LOCAL_REVIEW_ALLOW_TOKEN_REF,
        purge_plan=_ready_purge_plan(),
    )
    assert preflight["preflight_status"] == "R54_LOCAL_REVIEW_PREFLIGHT_BLOCKED"
    assert preflight["local_review_root_configured"] is True
    assert preflight["local_review_root_valid"] is False
    assert "r54_local_review_root_invalid" in preflight["execution_blocker_ids"]
    assert preflight["local_absolute_path_included"] is False
    assert preflight["root_path_exposed"] is False
    assert preflight["body_full_generation_allowed"] is False
    assert r54.assert_p7_r54_local_only_actual_review_preflight_bodyfree_contract(preflight) is True
    _assert_body_free_no_promotion(preflight)


def test_r54_r3_blocks_export_denylist_candidate_before_packet_generation(tmp_path) -> None:
    preflight = r54.build_p7_r54_local_only_actual_review_preflight_bodyfree(
        validation_evidence_intake=_r54_r2(),
        local_review_root=_ready_root(tmp_path),
        explicit_allow_token=r54.P7_R54_EXPLICIT_LOCAL_REVIEW_ALLOW_TOKEN_REF,
        purge_plan=_ready_purge_plan(),
        export_candidate_refs=("review/body_full_local_review_packet.zip",),
    )
    assert preflight["preflight_status"] == "R54_LOCAL_REVIEW_PREFLIGHT_BLOCKED"
    assert preflight["local_review_root_valid"] is True
    assert preflight["explicit_allow_present"] is True
    assert preflight["purge_plan_ready"] is True
    assert "r54_packet_export_denylist_violation" in preflight["execution_blocker_ids"]
    assert preflight["denied_export_candidate_count"] == 1
    assert preflight["export_denylist_violation_refs"]
    assert preflight["body_full_generation_allowed"] is False
    assert r54.assert_p7_r54_local_only_actual_review_preflight_bodyfree_contract(preflight) is True
    _assert_body_free_no_promotion(preflight)


def test_r54_r3_blocks_when_r2_validation_intake_is_not_ready(tmp_path) -> None:
    blocked_r2 = r54.build_p7_r54_validation_evidence_intake_bodyfree(
        validation_evidence_overrides={"r53_target_split_291_passed": {"evidence_present": False}},
    )
    preflight = r54.build_p7_r54_local_only_actual_review_preflight_bodyfree(
        validation_evidence_intake=blocked_r2,
        local_review_root=_ready_root(tmp_path),
        explicit_allow_token=r54.P7_R54_EXPLICIT_LOCAL_REVIEW_ALLOW_TOKEN_REF,
        purge_plan=_ready_purge_plan(),
    )
    assert preflight["preflight_status"] == "R54_LOCAL_REVIEW_PREFLIGHT_BLOCKED"
    assert preflight["r2_validation_evidence_ready_for_r54_3_preflight"] is False
    assert "r54_validation_evidence_not_ready" in preflight["execution_blocker_ids"]
    assert "r54_r53_target_split_291_passed_missing" in preflight["execution_blocker_ids"]
    assert preflight["body_full_generation_allowed"] is False
    assert preflight["next_required_step"] == r54.P7_R54_R3_BLOCKED_NEXT_REQUIRED_STEP_REF
    assert r54.assert_p7_r54_local_only_actual_review_preflight_bodyfree_contract(preflight) is True
    _assert_body_free_no_promotion(preflight)


def test_r54_r3_blocks_incomplete_purge_plan_and_changed_retention(tmp_path) -> None:
    bad_plan = _ready_purge_plan()
    bad_plan["reviewer_notes_retention_after_rating_finalized_max_hours"] = 72
    preflight = r54.build_p7_r54_local_only_actual_review_preflight_bodyfree(
        validation_evidence_intake=_r54_r2(),
        local_review_root=_ready_root(tmp_path),
        explicit_allow_token=r54.P7_R54_EXPLICIT_LOCAL_REVIEW_ALLOW_TOKEN_REF,
        purge_plan=bad_plan,
    )
    assert preflight["preflight_status"] == "R54_LOCAL_REVIEW_PREFLIGHT_BLOCKED"
    assert preflight["purge_plan_present"] is True
    assert preflight["purge_plan_ready"] is False
    assert preflight["retention_policy_present"] is False
    assert "reviewer_notes_retention_window_changed" in preflight["purge_plan_reason_refs"]
    assert "r54_purge_plan_missing" in preflight["execution_blocker_ids"]
    assert "r54_retention_policy_missing" in preflight["execution_blocker_ids"]
    assert preflight["body_full_generation_allowed"] is False
    assert r54.assert_p7_r54_local_only_actual_review_preflight_bodyfree_contract(preflight) is True
    _assert_body_free_no_promotion(preflight)


@pytest.mark.parametrize(
    "key,value",
    [
        ("git_connection_required", True),
        ("git_checked", True),
        ("root_path_exposed", True),
        ("local_absolute_path_included", True),
        ("explicit_allow_token_body_stored_here", True),
        ("body_full_packet_export_allowed", True),
        ("body_full_packet_zip_inclusion_allowed", True),
        ("actual_human_review_run_here", True),
        ("body_full_packet_generated_here", True),
        ("body_full_packets_created_local_only", True),
        ("p6_limited_human_readfeel_start_allowed", True),
        ("p8_start_allowed", True),
        ("release_allowed", True),
        ("api_db_rn_response_key_changed_here", True),
        ("validation_evidence_intake_done_here", False),
    ],
)
def test_r54_r3_rejects_body_path_export_review_runtime_or_release_mutation(tmp_path, key: str, value: object) -> None:
    material = r54.build_p7_r54_local_only_actual_review_preflight_bodyfree(
        validation_evidence_intake=_r54_r2(),
        local_review_root=_ready_root(tmp_path),
        explicit_allow_token=r54.P7_R54_EXPLICIT_LOCAL_REVIEW_ALLOW_TOKEN_REF,
        purge_plan=_ready_purge_plan(),
    )
    material[key] = value
    with pytest.raises(ValueError):
        r54.assert_p7_r54_local_only_actual_review_preflight_bodyfree_contract(material)
