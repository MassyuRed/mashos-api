# -*- coding: utf-8 -*-
from __future__ import annotations

import json
from copy import deepcopy
from functools import lru_cache

import pytest

import emlis_ai_p7_r51_p5_human_blind_qa_actual_local_manual_run as r51
import emlis_ai_p7_r52_r51_handoff_p6_p8_start_decision_gate as r52


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
    '"r52_actual_human_review_run_here": true',
    '"r52_actual_manual_review_run_here": true',
    '"r52_body_full_packet_generated_here": true',
    '"r52_actual_rating_rows_materialized_here": true',
    '"r52_actual_question_need_observation_rows_materialized_here": true',
    '"r52_actual_disposal_receipt_materialized_here": true',
    '"full_backend_suite_green_confirmed": true',
    '"backend_collect_only_claimed_as_full_backend_green": true',
    '"rn_contract_claimed_as_real_device_modal_readfeel": true',
)


def _assert_body_free_no_promotion(material: dict[str, object]) -> None:
    dumped = json.dumps(material, ensure_ascii=False, sort_keys=True).lower()
    for forbidden in FORBIDDEN_DUMP_TOKENS:
        assert forbidden not in dumped
    for forbidden in FORBIDDEN_TRUE_TOKENS:
        assert forbidden not in dumped


@lru_cache(maxsize=1)
def _cached_r52_r0() -> tuple[dict[str, object]]:
    refreeze = r52.build_p7_r52_current_received_snapshot_refreeze()
    assert r52.assert_p7_r52_current_received_snapshot_refreeze_contract(refreeze) is True
    return (refreeze,)


def _r52_r0() -> dict[str, object]:
    return deepcopy(_cached_r52_r0()[0])


def test_r52_r0_refreezes_current_received_snapshot_and_separates_r51_source_refs_without_git_or_allowance() -> None:
    refreeze = _r52_r0()

    assert refreeze["schema_version"] == r52.P7_R52_CURRENT_RECEIVED_SNAPSHOT_REFREEZE_SCHEMA_VERSION
    assert set(refreeze) == set(r52.P7_R52_CURRENT_RECEIVED_SNAPSHOT_REFREEZE_REQUIRED_FIELD_REFS)
    assert refreeze["phase"].startswith("P7_")
    assert refreeze["step"] == r52.P7_R52_STEP
    assert refreeze["scope"] == r52.P7_R52_SCOPE
    assert refreeze["policy_section"] == "R52-0_current_received_snapshot_r51_source_ref_separation"
    assert refreeze["source_mode"] == "local_snapshot"
    assert refreeze["git_check_required"] is False
    assert refreeze["git_check_performed"] is False
    assert refreeze["body_free"] is True

    current_refs = refreeze["current_received_snapshot_refs"]
    r51_refs = refreeze["r51_helper_source_snapshot_refs"]
    assert current_refs == r52.P7_R52_CURRENT_RECEIVED_SNAPSHOT_REFS
    assert r51_refs == r51.P7_R51_SOURCE_SNAPSHOT_REFS
    assert current_refs["backend_zip_ref"] == "mashos-api(160).zip"
    assert current_refs["rn_zip_ref"] == "Cocolon(247).zip"
    assert current_refs["premise_zip_ref"] == "Cocolon_前提資料(243).zip"
    assert r51_refs["backend_zip_ref"] == "mashos-api(159).zip"
    assert r51_refs["rn_zip_ref"] == "Cocolon(246).zip"
    assert r51_refs["premise_zip_ref"] == "Cocolon_前提資料(241).zip"
    assert refreeze["source_refs_are_separated"] is True
    assert refreeze["current_received_refs_reuse_r51_helper_refs"] is False
    assert refreeze["r51_actual_review_evidence_expected_from_r51_later"] is True
    assert refreeze["r51_actual_review_evidence_complete"] is False
    assert refreeze["r52_0_current_received_snapshot_refrozen"] is True
    assert refreeze["r52_1_validation_evidence_matrix_frozen"] is False
    assert tuple(refreeze["implemented_steps"]) == r52.P7_R52_R0_IMPLEMENTED_STEPS
    assert tuple(refreeze["not_yet_implemented_steps"]) == r52.P7_R52_R0_NOT_YET_IMPLEMENTED_STEPS
    assert refreeze["next_required_step"] == r52.P7_R52_R0_NEXT_REQUIRED_STEP_REF
    assert refreeze["p6_limited_human_readfeel_start_allowed"] is False
    assert refreeze["p8_start_allowed"] is False
    assert refreeze["p7_complete"] is False
    assert refreeze["release_allowed"] is False

    _assert_body_free_no_promotion(refreeze)


@pytest.mark.parametrize(
    "key,value",
    [
        ("git_check_required", True),
        ("git_check_performed", True),
        ("source_refs_are_separated", False),
        ("current_received_refs_reuse_r51_helper_refs", True),
        ("r51_actual_review_evidence_complete", True),
        ("r52_1_validation_evidence_matrix_frozen", True),
        ("p6_limited_human_readfeel_start_allowed", True),
        ("p8_start_allowed", True),
        ("p7_complete", True),
        ("release_allowed", True),
        ("r52_actual_human_review_run_here", True),
        ("r52_body_full_packet_generated_here", True),
        ("api_db_rn_response_key_changed_here", True),
    ],
)
def test_r52_r0_rejects_git_claim_source_mix_or_p6_p8_release_promotion(key: str, value: object) -> None:
    material = _r52_r0()
    material[key] = value
    with pytest.raises(ValueError):
        r52.assert_p7_r52_current_received_snapshot_refreeze_contract(material)


def test_r52_r0_rejects_r51_source_refs_relabelled_as_current_snapshot() -> None:
    with pytest.raises(ValueError):
        r52.build_p7_r52_current_received_snapshot_refreeze(
            current_received_snapshot_refs=r51.P7_R51_SOURCE_SNAPSHOT_REFS,
        )


def test_r52_r1_freezes_validation_matrix_without_reclassifying_split_timeout_collect_only_or_rn_contract() -> None:
    freeze = r52.build_p7_r52_validation_evidence_matrix_freeze(current_received_snapshot_refreeze=_r52_r0())
    assert r52.assert_p7_r52_validation_evidence_matrix_freeze_contract(freeze) is True

    assert freeze["schema_version"] == r52.P7_R52_VALIDATION_EVIDENCE_MATRIX_FREEZE_SCHEMA_VERSION
    assert set(freeze) == set(r52.P7_R52_VALIDATION_EVIDENCE_MATRIX_FREEZE_REQUIRED_FIELD_REFS)
    assert freeze["step"] == r52.P7_R52_STEP
    assert freeze["scope"] == r52.P7_R52_SCOPE
    assert freeze["policy_section"] == "R52-1_validation_evidence_matrix_freeze"
    assert freeze["r0_refreeze_schema_version"] == r52.P7_R52_CURRENT_RECEIVED_SNAPSHOT_REFREEZE_SCHEMA_VERSION
    assert freeze["source_refs_are_separated"] is True
    assert freeze["validation_evidence_group_refs"] == list(r52.P7_R52_VALIDATION_EVIDENCE_GROUP_REFS)
    assert freeze["validation_evidence_required_group_refs"] == list(r52.P7_R52_VALIDATION_EVIDENCE_REQUIRED_GROUP_REFS)
    assert freeze["validation_evidence_row_count"] == len(r52.P7_R52_VALIDATION_EVIDENCE_GROUP_REFS)
    assert freeze["validation_evidence_required_groups_present"] is True
    assert freeze["validation_evidence_ready_for_r52_2_intake"] is True
    assert freeze["execution_blocker_ids"] == []

    rows = {row["evidence_group_ref"]: row for row in freeze["validation_evidence_rows"]}
    assert list(rows) == list(r52.P7_R52_VALIDATION_EVIDENCE_GROUP_REFS)
    assert rows["rn_contract"]["evidence_status_ref"] == "PASSED"
    assert rows["rn_contract"]["passed_count"] == 36
    assert rows["r51_target"]["evidence_status_ref"] == "PASSED"
    assert rows["r51_target"]["passed_count"] == 125
    assert rows["r50_target_regression"]["passed_count"] == 99
    assert rows["r49_split_matrix"]["evidence_status_ref"] == "PASSED_BY_SPLIT_EXECUTION"
    assert rows["r49_split_matrix"]["split_only"] is True
    assert rows["r49_split_matrix"]["passed_count"] == 76
    assert rows["r49_split_matrix"]["combined_green_claimed"] is False
    assert rows["r49_combined_command"]["evidence_status_ref"] == "TIMEOUT_UNCLASSIFIED"
    assert rows["r49_combined_command"]["timeout_unclassified"] is True
    assert rows["r49_combined_command"]["required_for_r52_2_intake"] is False
    assert rows["r49_combined_command"]["combined_green_claimed"] is False
    assert rows["r48_regression"]["passed_count"] == 82
    assert rows["r47_regression"]["passed_count"] == 275
    assert rows["r46_display_p5_core_subset"]["evidence_status_ref"] == "PASSED_WITH_KNOWN_WARNING"
    assert rows["r46_display_p5_core_subset"]["passed_count"] == 94
    assert rows["r46_display_p5_core_subset"]["warning_count"] == 1
    assert rows["backend_collect_only"]["evidence_status_ref"] == "COLLECT_ONLY_PASSED_WITH_KNOWN_WARNING"
    assert rows["backend_collect_only"]["collected_count"] == 3591
    assert rows["backend_collect_only"]["warning_count"] == 1

    assert freeze["rn_contract_green_evidence_present"] is True
    assert freeze["r51_target_green_evidence_present"] is True
    assert freeze["r50_target_green_evidence_present"] is True
    assert freeze["r49_split_matrix_green_evidence_present"] is True
    assert freeze["r49_split_matrix_green_required_for_r52_2_intake"] is True
    assert freeze["r49_combined_timeout_unclassified"] is True
    assert freeze["r49_combined_green_claim_allowed"] is False
    assert freeze["r49_combined_green_claimed"] is False
    assert freeze["r49_combined_required_for_r52_2_intake"] is False
    assert freeze["r49_split_evidence_claimed_as_combined_green"] is False
    assert freeze["r48_regression_green_evidence_present"] is True
    assert freeze["r47_regression_green_evidence_present"] is True
    assert freeze["r46_display_p5_core_green_evidence_present"] is True
    assert freeze["backend_collect_only_evidence_present"] is True
    assert freeze["full_backend_suite_green_confirmed"] is False
    assert freeze["backend_collect_only_claimed_as_full_backend_green"] is False
    assert freeze["rn_contract_claimed_as_real_device_modal_readfeel"] is False
    assert freeze["validation_commands_executed_here"] is False
    assert freeze["command_result_body_stored_here"] is False
    assert freeze["terminal_output_stored_here"] is False
    assert freeze["actual_manual_review_run_here"] is False
    assert freeze["body_full_packet_generated_here"] is False
    assert freeze["p6_limited_human_readfeel_start_allowed"] is False
    assert freeze["p8_start_allowed"] is False
    assert freeze["p7_complete"] is False
    assert freeze["release_allowed"] is False
    assert tuple(freeze["implemented_steps"]) == r52.P7_R52_IMPLEMENTED_STEPS
    assert tuple(freeze["not_yet_implemented_steps"]) == r52.P7_R52_NOT_YET_IMPLEMENTED_STEPS
    assert freeze["next_required_step"] == r52.P7_R52_R1_NEXT_REQUIRED_STEP_REF

    _assert_body_free_no_promotion(freeze)


@pytest.mark.parametrize(
    "missing_group,expected_blocker",
    [
        ("rn_contract", "r52_missing_rn_contract_green_evidence"),
        ("r51_target", "r52_missing_r51_target_green_evidence"),
        ("r50_target_regression", "r52_missing_r50_target_green_evidence"),
        ("r49_split_matrix", "r52_missing_r49_split_green_evidence"),
        ("r48_regression", "r52_missing_r48_regression_green_evidence"),
        ("r47_regression", "r52_missing_r47_regression_green_evidence"),
        ("r46_display_p5_core_subset", "r52_missing_r46_display_p5_core_green_evidence"),
        ("backend_collect_only", "r52_missing_backend_collect_only_evidence"),
    ],
)
def test_r52_r1_missing_required_evidence_blocks_r52_2_intake_without_starting_review(
    missing_group: str,
    expected_blocker: str,
) -> None:
    freeze = r52.build_p7_r52_validation_evidence_matrix_freeze(
        current_received_snapshot_refreeze=_r52_r0(),
        validation_evidence_overrides={
            missing_group: {
                "evidence_status_ref": "MISSING",
                "evidence_present": False,
                "passed_count": 0,
                "collected_count": 0,
                "warning_count": 0,
            }
        },
    )

    assert freeze["validation_evidence_ready_for_r52_2_intake"] is False
    assert expected_blocker in freeze["execution_blocker_ids"]
    assert freeze["next_required_step"] == r52.P7_R52_R1_BLOCKED_NEXT_REQUIRED_STEP_REF
    assert freeze["actual_manual_review_run_here"] is False
    assert freeze["body_full_packet_generated_here"] is False
    assert freeze["p6_limited_human_readfeel_start_allowed"] is False
    assert freeze["p8_start_allowed"] is False
    assert freeze["p7_complete"] is False
    assert freeze["release_allowed"] is False
    _assert_body_free_no_promotion(freeze)


def test_r52_r1_rejects_r49_combined_timeout_reclassified_as_green_or_required_intake() -> None:
    with pytest.raises(ValueError):
        r52.build_p7_r52_validation_evidence_matrix_freeze(
            current_received_snapshot_refreeze=_r52_r0(),
            validation_evidence_overrides={
                "r49_combined_command": {
                    "evidence_status_ref": "PASSED",
                    "timeout_unclassified": False,
                    "required_for_r52_2_intake": True,
                    "combined_green_claimed": True,
                }
            },
        )


def test_r52_r1_rejects_backend_collect_only_reclassified_as_full_backend_green() -> None:
    with pytest.raises(ValueError):
        r52.build_p7_r52_validation_evidence_matrix_freeze(
            current_received_snapshot_refreeze=_r52_r0(),
            validation_evidence_overrides={
                "backend_collect_only": {
                    "evidence_status_ref": "PASSED",
                    "evidence_present": True,
                }
            },
        )


def test_r52_r1_rejects_top_level_collect_only_or_rn_contract_promotion_claims() -> None:
    freeze = r52.build_p7_r52_validation_evidence_matrix_freeze(current_received_snapshot_refreeze=_r52_r0())

    for key in (
        "full_backend_suite_green_confirmed",
        "backend_collect_only_claimed_as_full_backend_green",
        "rn_contract_claimed_as_real_device_modal_readfeel",
        "validation_commands_executed_here",
        "actual_manual_review_run_here",
        "body_full_packet_generated_here",
        "p8_start_allowed",
        "release_allowed",
    ):
        broken = deepcopy(freeze)
        broken[key] = True
        with pytest.raises(ValueError):
            r52.assert_p7_r52_validation_evidence_matrix_freeze_contract(broken)


def test_r52_r0_r1_chain_builder_returns_valid_r1_material_bound_to_r0() -> None:
    r0 = _r52_r0()
    r1 = r52.build_p7_r52_r0_r1_current_snapshot_validation_evidence_freeze(
        current_received_snapshot_refreeze=r0,
    )

    assert r1["r0_refreeze_material_ref"] == r0["material_id"]
    assert r1["r52_0_current_received_snapshot_refrozen"] is True
    assert r1["r52_1_validation_evidence_matrix_frozen"] is True
    assert r1["next_required_step"] == r52.P7_R52_R1_NEXT_REQUIRED_STEP_REF
    _assert_body_free_no_promotion(r1)
