# -*- coding: utf-8 -*-
from __future__ import annotations

import json
from copy import deepcopy
from functools import lru_cache

import pytest

import emlis_ai_p7_r50_p5_human_blind_qa_manual_run_decision as r50
import emlis_ai_p7_r51_p5_human_blind_qa_actual_local_manual_run as r51


FORBIDDEN_DUMP_TOKENS = (
    '"raw_input":',
    '"raw_answer":',
    '"comment_text":',
    '"comment_text_body":',
    '"returned_emlis_surface":',
    '"bounded_owned_history_review_surface":',
    '"current_input_review_surface":',
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
    '"question_api_implemented": true',
    '"question_db_schema_implemented": true',
    '"question_rn_ui_implemented": true',
    '"question_response_key_implemented": true',
    '"question_trigger_logic_implemented": true',
    '"actual_human_review_run_here": true',
    '"actual_manual_review_run_here": true',
    '"body_full_packet_generated_here": true',
    '"actual_body_full_packet_generated_here": true',
    '"actual_rating_rows_materialized_here": true',
    '"actual_question_need_observation_rows_materialized_here": true',
    '"actual_disposal_receipt_materialized_here": true',
    '"full_backend_suite_green_confirmed": true',
)


def _assert_body_free_no_promotion(material: dict[str, object]) -> None:
    dumped = json.dumps(material, ensure_ascii=False, sort_keys=True).lower()
    for forbidden in FORBIDDEN_DUMP_TOKENS:
        assert forbidden not in dumped
    for forbidden in FORBIDDEN_TRUE_TOKENS:
        assert forbidden not in dumped


@lru_cache(maxsize=1)
def _cached_r50_boundary() -> tuple[dict[str, object]]:
    boundary = r50.build_p7_r50_touch_candidate_no_touch_boundary_freeze()
    assert r50.assert_p7_r50_touch_candidate_no_touch_boundary_freeze_contract(boundary) is True
    return (boundary,)


def _r50_boundary() -> dict[str, object]:
    return deepcopy(_cached_r50_boundary()[0])


@lru_cache(maxsize=1)
def _cached_r51_r0() -> tuple[dict[str, object]]:
    refreeze = r51.build_p7_r51_current_source_r50_handoff_refreeze(r50_handoff_boundary=_r50_boundary())
    assert r51.assert_p7_r51_current_source_r50_handoff_refreeze_contract(refreeze) is True
    return (refreeze,)


def _r51_r0() -> dict[str, object]:
    return deepcopy(_cached_r51_r0()[0])


def test_r51_r0_refreezes_current_source_and_complete_r50_handoff_without_starting_review_p8_or_release() -> None:
    refreeze = _r51_r0()

    assert refreeze["schema_version"] == r51.P7_R51_CURRENT_SOURCE_R50_HANDOFF_REFREEZE_SCHEMA_VERSION
    assert set(refreeze) == set(r51.P7_R51_CURRENT_SOURCE_R50_HANDOFF_REFREEZE_REQUIRED_FIELD_REFS)
    assert refreeze["phase"].startswith("P7_")
    assert refreeze["step"] == r51.P7_R51_STEP
    assert refreeze["scope"] == r51.P7_R51_SCOPE
    assert refreeze["policy_section"] == "R51-0_current_source_r50_handoff_refreeze"
    assert refreeze["source_mode"] == "local_snapshot"
    assert refreeze["git_connection_required"] is False
    assert refreeze["git_checked"] is False
    assert refreeze["body_free"] is True
    assert refreeze["source_snapshot_refs"]["backend_zip_ref"] == "mashos-api(159).zip"
    assert refreeze["source_snapshot_refs"]["premise_zip_ref"] == "Cocolon_前提資料(241).zip"

    handoff = refreeze["r50_handoff"]
    assert set(handoff) == set(r51.P7_R51_R50_HANDOFF_REQUIRED_FIELD_REFS)
    assert handoff["r50_handoff_required"] is True
    assert handoff["r50_step"] == r50.P7_R50_STEP
    assert handoff["r50_scope"] == r50.P7_R50_SCOPE
    assert handoff["r50_schema_version"] == r50.P7_R50_TOUCH_CANDIDATE_NO_TOUCH_BOUNDARY_FREEZE_SCHEMA_VERSION
    assert handoff["r50_review_kind"] == r51.P7_R51_REVIEW_KIND == r50.P7_R50_REVIEW_KIND
    assert handoff["r50_packet_kind"] == r51.P7_R51_PACKET_KIND == r50.P7_R50_PACKET_KIND
    assert handoff["r50_required_case_count"] == r51.P7_R51_REQUIRED_CASE_COUNT == 24
    assert tuple(handoff["r50_completed_steps"]) == r50.P7_R50_R20_IMPLEMENTED_STEPS
    assert tuple(handoff["r50_not_yet_implemented_steps"]) == r50.P7_R50_R20_NOT_YET_IMPLEMENTED_STEPS == ()
    assert handoff["r50_next_required_step"] == r50.P7_R50_R20_NEXT_REQUIRED_STEP_REF
    assert handoff["r50_touch_boundary_status"] == "TOUCH_CANDIDATE_NO_TOUCH_BOUNDARY_FROZEN"
    assert handoff["r50_validation_matrix_status"] == "VALIDATION_COMMAND_MATRIX_READY"
    assert handoff["r50_boundary_freeze_ready"] is True
    assert handoff["r50_manual_run_boundary_finished"] is True
    assert handoff["r50_actual_review_completed"] is False
    assert handoff["r50_actual_human_review_run"] is False
    assert handoff["r50_body_full_packet_generated"] is False
    assert handoff["r50_rating_rows_materialized"] is False
    assert handoff["r50_question_need_observation_rows_materialized"] is False
    assert handoff["r50_disposal_receipt_materialized"] is False
    assert handoff["r50_p5_human_blind_qa_confirmed"] is False
    assert handoff["r50_p5_human_blind_qa_confirmed_candidate"] is False
    assert handoff["r50_p6_limited_human_readfeel_start_allowed"] is False
    assert handoff["r50_p8_start_allowed"] is False
    assert handoff["r50_release_allowed"] is False

    bridge = refreeze["p7_p8_bridge_rule"]
    assert set(bridge) == set(r51.P7_R51_BRIDGE_RULE_REQUIRED_FIELD_REFS)
    assert bridge["p7_bridge_only"] is True
    assert bridge["r51_is_p5_actual_local_only_manual_run"] is True
    assert bridge["r51_r0_r1_are_pre_review_freezes_only"] is True
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

    assert tuple(refreeze["implemented_steps"]) == r51.P7_R51_R0_IMPLEMENTED_STEPS
    assert tuple(refreeze["not_yet_implemented_steps"]) == r51.P7_R51_R0_NOT_YET_IMPLEMENTED_STEPS
    assert refreeze["r0_current_source_r50_handoff_refrozen"] is True
    assert refreeze["r1_validation_evidence_r49_timeout_handling_frozen"] is False
    assert refreeze["p5_actual_review_still_not_run"] is True
    assert refreeze["local_root_preflight_required_later"] is True
    assert refreeze["actual_manual_review_run_here"] is False
    assert refreeze["body_full_packet_generated_here"] is False
    assert refreeze["next_required_step"] == r51.P7_R51_R0_NEXT_REQUIRED_STEP_REF

    _assert_body_free_no_promotion(refreeze)


@pytest.mark.parametrize(
    "key,value",
    [
        ("actual_human_review_run_here", True),
        ("actual_manual_review_run_here", True),
        ("actual_body_full_packet_generated_here", True),
        ("body_full_packet_generated_here", True),
        ("actual_rating_rows_materialized_here", True),
        ("actual_question_need_observation_rows_materialized_here", True),
        ("actual_disposal_receipt_materialized_here", True),
        ("p5_human_blind_qa_confirmed", True),
        ("p5_human_blind_qa_confirmed_candidate", True),
        ("p6_limited_human_readfeel_start_allowed", True),
        ("p8_start_allowed", True),
        ("release_allowed", True),
        ("p7_complete", True),
    ],
)
def test_r51_r0_rejects_r50_handoff_that_claims_review_p8_release_or_p5_confirmation(key: str, value: object) -> None:
    boundary = _r50_boundary()
    boundary[key] = value
    with pytest.raises(ValueError):
        r51.build_p7_r51_current_source_r50_handoff_refreeze(r50_handoff_boundary=boundary)


def test_r51_r0_rejects_incomplete_or_wrong_next_step_r50_handoff() -> None:
    boundary = _r50_boundary()
    boundary["implemented_steps"] = boundary["implemented_steps"][:-1]
    with pytest.raises(ValueError):
        r51.build_p7_r51_current_source_r50_handoff_refreeze(r50_handoff_boundary=boundary)

    boundary = _r50_boundary()
    boundary["not_yet_implemented_steps"] = ["R50-20_touch_candidate_no_touch_boundary_freeze"]
    with pytest.raises(ValueError):
        r51.build_p7_r51_current_source_r50_handoff_refreeze(r50_handoff_boundary=boundary)

    boundary = _r50_boundary()
    boundary["next_required_step"] = "P8_question_detail_design_start"
    with pytest.raises(ValueError):
        r51.build_p7_r51_current_source_r50_handoff_refreeze(r50_handoff_boundary=boundary)


def test_r51_r1_freezes_validation_evidence_and_r49_timeout_without_wildcard_green_claim() -> None:
    freeze = r51.build_p7_r51_validation_evidence_r49_timeout_handling_freeze(
        current_source_r50_handoff_refreeze=_r51_r0(),
    )
    assert r51.assert_p7_r51_validation_evidence_r49_timeout_handling_freeze_contract(freeze) is True

    assert freeze["schema_version"] == r51.P7_R51_VALIDATION_EVIDENCE_R49_TIMEOUT_HANDLING_FREEZE_SCHEMA_VERSION
    assert set(freeze) == set(r51.P7_R51_VALIDATION_EVIDENCE_R49_TIMEOUT_HANDLING_FREEZE_REQUIRED_FIELD_REFS)
    assert freeze["step"] == r51.P7_R51_STEP
    assert freeze["scope"] == r51.P7_R51_SCOPE
    assert freeze["policy_section"] == "R51-1_validation_evidence_r49_timeout_handling_freeze"
    assert freeze["required_case_count"] == 24
    assert freeze["r0_refreeze_schema_version"] == r51.P7_R51_CURRENT_SOURCE_R50_HANDOFF_REFREEZE_SCHEMA_VERSION
    assert freeze["validation_evidence_group_refs"] == list(r51.P7_R51_VALIDATION_EVIDENCE_GROUP_REFS)
    assert freeze["validation_evidence_required_group_refs"] == list(r51.P7_R51_VALIDATION_EVIDENCE_REQUIRED_GROUP_REFS)
    assert freeze["validation_evidence_row_count"] == len(r51.P7_R51_VALIDATION_EVIDENCE_GROUP_REFS)
    assert freeze["validation_evidence_required_groups_present"] is True
    assert freeze["validation_evidence_ready_for_r51_2_preflight"] is True
    assert freeze["execution_blocker_ids"] == []

    rows = {row["evidence_group_ref"]: row for row in freeze["validation_evidence_rows"]}
    assert list(rows) == list(r51.P7_R51_VALIDATION_EVIDENCE_GROUP_REFS)
    assert rows["r50_target"]["evidence_status_ref"] == "PASSED"
    assert rows["r50_target"]["passed_count"] == 99
    assert rows["r49_split_matrix"]["evidence_status_ref"] == "PASSED_BY_SPLIT_EXECUTION"
    assert rows["r49_split_matrix"]["passed_count"] == 76
    assert rows["r49_split_matrix"]["required_for_r51_2_preflight"] is True
    assert rows["r49_wildcard_bulk"]["evidence_status_ref"] == "TIMEOUT_UNCLASSIFIED"
    assert rows["r49_wildcard_bulk"]["timeout_unclassified"] is True
    assert rows["r49_wildcard_bulk"]["required_for_r51_2_preflight"] is False
    assert rows["r48_regression"]["passed_count"] == 82
    assert rows["r47_regression"]["passed_count"] == 275
    assert rows["r46_display_p5_core_subset"]["passed_count"] == 94
    assert rows["r46_display_p5_core_subset"]["warning_count"] == 1
    assert rows["backend_collect_only"]["collected_count"] == 3466
    assert rows["backend_collect_only"]["warning_count"] == 1
    assert rows["rn_no_touch_optional"]["passed_count"] == 36
    assert rows["rn_no_touch_optional"]["optional"] is True

    assert freeze["r50_target_green_evidence_present"] is True
    assert freeze["r49_split_matrix_green_evidence_present"] is True
    assert freeze["r49_split_matrix_green_required_for_r51"] is True
    assert freeze["r49_split_matrix_green_required_for_r51_2_preflight"] is True
    assert freeze["r49_wildcard_bulk_timeout_unclassified"] is True
    assert freeze["r49_wildcard_green_claim_allowed"] is False
    assert freeze["r49_wildcard_green_claimed"] is False
    assert freeze["r49_wildcard_bulk_required_for_r51_2_preflight"] is False
    assert freeze["r49_timeout_handling_claim_boundary_ref"] == "split_matrix_green_required_wildcard_bulk_timeout_visible_not_green_claim"
    assert freeze["r48_regression_green_evidence_present"] is True
    assert freeze["r47_regression_green_evidence_present"] is True
    assert freeze["r46_display_p5_core_green_evidence_present"] is True
    assert freeze["rn_contract_green_evidence_present"] is True
    assert freeze["backend_collect_only_evidence_present"] is True
    assert freeze["full_backend_suite_green_confirmed"] is False
    assert freeze["collect_only_claimed_as_full_backend_green"] is False
    assert freeze["rn_contract_claimed_as_real_device_modal_readfeel"] is False
    assert freeze["validation_commands_executed_here"] is False
    assert freeze["command_result_body_stored_here"] is False
    assert freeze["terminal_output_stored_here"] is False
    assert freeze["actual_manual_review_run_here"] is False
    assert freeze["body_full_packet_generated_here"] is False
    assert freeze["r0_current_source_r50_handoff_refrozen"] is True
    assert freeze["r1_validation_evidence_r49_timeout_handling_frozen"] is True
    assert tuple(freeze["implemented_steps"]) == r51.P7_R51_IMPLEMENTED_STEPS
    assert tuple(freeze["not_yet_implemented_steps"]) == r51.P7_R51_NOT_YET_IMPLEMENTED_STEPS
    assert freeze["next_required_step"] == r51.P7_R51_R1_NEXT_REQUIRED_STEP_REF

    _assert_body_free_no_promotion(freeze)


@pytest.mark.parametrize(
    "missing_group,expected_blocker",
    [
        ("r50_target", "r51_missing_r50_target_green_evidence"),
        ("r49_split_matrix", "r51_missing_r49_split_green_evidence"),
        ("r48_regression", "r51_missing_r48_regression_green_evidence"),
        ("r47_regression", "r51_missing_r47_regression_green_evidence"),
        ("r46_display_p5_core_subset", "r51_missing_r46_display_p5_core_green_evidence"),
        ("backend_collect_only", "r51_missing_backend_collect_only_evidence"),
        ("rn_no_touch_optional", "r51_missing_rn_contract_green_evidence"),
    ],
)
def test_r51_r1_missing_required_evidence_blocks_r51_2_preflight_without_starting_review(
    missing_group: str,
    expected_blocker: str,
) -> None:
    freeze = r51.build_p7_r51_validation_evidence_r49_timeout_handling_freeze(
        current_source_r50_handoff_refreeze=_r51_r0(),
        validation_evidence_overrides={
            missing_group: {
                "evidence_status_ref": "MISSING",
                "evidence_present": False,
                "passed_count": 0,
                "collected_count": 0,
            }
        },
    )

    assert freeze["validation_evidence_ready_for_r51_2_preflight"] is False
    assert expected_blocker in freeze["execution_blocker_ids"]
    assert freeze["next_required_step"] == r51.P7_R51_R1_BLOCKED_NEXT_REQUIRED_STEP_REF
    assert freeze["actual_manual_review_run_here"] is False
    assert freeze["body_full_packet_generated_here"] is False
    assert freeze["p7_complete"] is False
    assert freeze["p8_start_allowed"] is False
    assert freeze["release_allowed"] is False
    _assert_body_free_no_promotion(freeze)


def test_r51_r1_keeps_r49_wildcard_timeout_visible_even_when_evidence_is_ready() -> None:
    freeze = r51.build_p7_r51_validation_evidence_r49_timeout_handling_freeze(
        current_source_r50_handoff_refreeze=_r51_r0(),
    )
    wildcard_row = [row for row in freeze["validation_evidence_rows"] if row["evidence_group_ref"] == "r49_wildcard_bulk"][0]

    assert freeze["validation_evidence_ready_for_r51_2_preflight"] is True
    assert freeze["r49_split_matrix_green_evidence_present"] is True
    assert freeze["r49_wildcard_bulk_timeout_unclassified"] is True
    assert wildcard_row["evidence_present"] is True
    assert wildcard_row["timeout_unclassified"] is True
    assert wildcard_row["required_for_r51_2_preflight"] is False
    assert freeze["r49_wildcard_green_claim_allowed"] is False
    assert freeze["r49_wildcard_green_claimed"] is False
    assert "r51_r49_wildcard_timeout_unclassified" not in freeze["execution_blocker_ids"]


def test_r51_r1_rejects_wildcard_timeout_reclassified_as_green_or_required_preflight() -> None:
    with pytest.raises(ValueError):
        r51.build_p7_r51_validation_evidence_r49_timeout_handling_freeze(
            current_source_r50_handoff_refreeze=_r51_r0(),
            validation_evidence_overrides={
                "r49_wildcard_bulk": {
                    "evidence_status_ref": "PASSED",
                    "timeout_unclassified": False,
                    "required_for_r51_2_preflight": True,
                }
            },
        )


def test_r51_r0_r1_chain_builder_returns_valid_r1_material_bound_to_r0() -> None:
    r0 = _r51_r0()
    r1 = r51.build_p7_r51_r0_r1_current_source_validation_evidence_freeze(
        current_source_r50_handoff_refreeze=r0,
    )

    assert r1["r0_refreeze_material_ref"] == r0["material_id"]
    assert r1["r0_current_source_r50_handoff_refrozen"] is True
    assert r1["r1_validation_evidence_r49_timeout_handling_frozen"] is True
    assert r1["next_required_step"] == r51.P7_R51_R1_NEXT_REQUIRED_STEP_REF
    _assert_body_free_no_promotion(r1)
