# -*- coding: utf-8 -*-
from __future__ import annotations

import json
from copy import deepcopy
from functools import lru_cache

import pytest

import emlis_ai_p7_r48_p5_human_blind_qa_actual_review_packet as r48
import emlis_ai_p7_r50_p5_human_blind_qa_manual_run_decision as r50
import emlis_ai_p7_r51_p5_human_blind_qa_actual_local_manual_run as r51

FORBIDDEN_DUMP_TOKENS = (
    '"raw_input":', '"raw_answer":', '"comment_text":', '"comment_text_body":',
    '"returned_emlis_surface":', '"bounded_owned_history_review_surface":',
    '"current_input_review_surface":', '"reviewer_free_text":', '"reviewer_note":',
    '"reviewer_notes":', '"question_text":', '"draft_question_text":', '"question_body":',
    '"local_absolute_path": true', '"body_content_hash":', '"packet_content_hash":',
    '"terminal_output": "', '"stdout":', '"stderr":', '"traceback":',
)
FORBIDDEN_TRUE_TOKENS = (
    '"release_allowed": true', '"p7_complete": true', '"p8_start_allowed": true',
    '"question_api_implemented": true', '"question_db_schema_implemented": true',
    '"question_rn_ui_implemented": true', '"question_response_key_implemented": true',
    '"question_trigger_logic_implemented": true', '"actual_human_review_run_here": true',
    '"actual_manual_review_run_here": true', '"body_full_packet_generated_here": true',
    '"body_full_packets_created_local_only": true', '"packet_body_included_here": true',
    '"packet_body_copied_here": true', '"reviewer_instruction_materialized_for_actual_review_here": true',
    '"actual_rating_rows_materialized_here": true',
    '"actual_question_need_observation_rows_materialized_here": true',
    '"actual_disposal_receipt_materialized_here": true',
)


def _assert_body_free_no_promotion(material: dict[str, object]) -> None:
    dumped = json.dumps(material, ensure_ascii=False, sort_keys=True).lower()
    for forbidden in FORBIDDEN_DUMP_TOKENS:
        assert forbidden not in dumped
    for forbidden in FORBIDDEN_TRUE_TOKENS:
        assert forbidden not in dumped


@lru_cache(maxsize=1)
def _cached_request() -> tuple[dict[str, object]]:
    request = r51.build_p7_r51_r0_r5_packet_generation_request_chain(
        local_review_root="/tmp/cocolon_r51_actual_local_review_root",
        explicit_allow_token=r51.P7_R51_EXPLICIT_ACTUAL_LOCAL_MANUAL_RUN_ALLOW_TOKEN_REF,
        purge_plan=r51.build_p7_r51_default_local_only_purge_plan_bodyfree(),
    )
    assert request["generation_request_status"] == "READY_FOR_LOCAL_ONLY_BODY_FULL_PACKET_GENERATION"
    return (request,)


def _request() -> dict[str, object]:
    return deepcopy(_cached_request()[0])


@lru_cache(maxsize=1)
def _cached_scan() -> tuple[dict[str, object]]:
    scan = r51.build_p7_r51_body_full_packet_completeness_export_denylist_scan_bodyfree(
        local_only_body_full_packet_generation_request=_request()
    )
    assert r51.assert_p7_r51_body_full_packet_completeness_export_denylist_scan_bodyfree_contract(scan) is True
    return (scan,)


def _scan() -> dict[str, object]:
    return deepcopy(_cached_scan()[0])


@lru_cache(maxsize=1)
def _cached_freeze() -> tuple[dict[str, object]]:
    freeze = r51.build_p7_r51_reviewer_instruction_rating_form_freeze_bodyfree(
        body_full_packet_completeness_export_denylist_scan=_scan()
    )
    assert r51.assert_p7_r51_reviewer_instruction_rating_form_freeze_bodyfree_contract(freeze) is True
    return (freeze,)


def _freeze() -> dict[str, object]:
    return deepcopy(_cached_freeze()[0])


def test_r51_r6_verifies_bodyfull_packet_completeness_scan_without_exporting_body_paths_or_hashes() -> None:
    scan = _scan()
    assert scan["schema_version"] == r51.P7_R51_BODY_FULL_PACKET_COMPLETENESS_EXPORT_DENYLIST_SCAN_SCHEMA_VERSION
    assert set(scan) == set(r51.P7_R51_BODY_FULL_PACKET_COMPLETENESS_EXPORT_DENYLIST_SCAN_REQUIRED_FIELD_REFS)
    assert scan["policy_section"] == "R51-6_body_full_packet_completeness_export_denylist_scan"
    assert scan["review_session_status"] == "R51_BODY_FULL_PACKET_COMPLETENESS_SCAN_READY"
    assert scan["packet_completeness_scan_status"] == "READY_FOR_REVIEWER_INSTRUCTION_RATING_FORM_FREEZE"
    assert scan["next_required_step"] == r51.P7_R51_R6_NEXT_REQUIRED_STEP_REF
    assert scan["required_case_count"] == 24
    assert scan["request_row_count"] == 24
    assert scan["packet_scan_row_count"] == 24
    assert len(scan["packet_scan_rows"]) == 24
    assert scan["expected_packet_ref_count"] == 24
    assert scan["present_packet_ref_count"] == 24
    assert scan["missing_packet_ref_count"] == 0
    assert scan["incomplete_packet_ref_count"] == 0
    assert scan["all_required_packets_present"] is True
    assert scan["all_required_fields_present"] is True
    assert scan["all_local_only_markers_present"] is True
    assert scan["all_must_not_export_markers_present"] is True
    assert scan["all_disposal_required_markers_present"] is True
    assert scan["body_full_packet_completeness_verified"] is True
    assert scan["body_full_packet_export_violation_detected"] is False
    assert scan["root_path_exposed"] is False
    assert scan["local_absolute_path_included"] is False
    assert scan["body_content_hash_stored_here"] is False
    assert scan["packet_body_included_here"] is False
    assert scan["packet_body_copied_here"] is False
    assert scan["body_full_packet_generated_here"] is False
    assert scan["body_full_packets_created_local_only"] is False
    assert scan["actual_human_review_run_here"] is False
    assert scan["p5_actual_review_still_not_run"] is True
    assert tuple(scan["implemented_steps"]) == r51.P7_R51_R6_IMPLEMENTED_STEPS
    assert tuple(scan["not_yet_implemented_steps"]) == r51.P7_R51_R6_NOT_YET_IMPLEMENTED_STEPS
    _assert_body_free_no_promotion(scan)


def test_r51_r6_scan_rows_are_bodyfree_evidence_not_packet_files() -> None:
    row = _scan()["packet_scan_rows"][0]
    assert set(row) == set(r51.P7_R51_PACKET_COMPLETENESS_SCAN_ROW_FIELD_REFS)
    assert row["completion_status_ref"] == "PACKET_PRESENT_LOCAL_ONLY"
    assert row["packet_kind"] == r51.P7_R51_PACKET_KIND
    assert row["review_kind"] == r51.P7_R51_REVIEW_KIND
    assert row["packet_present_local_only"] is True
    assert row["required_field_refs_present"] is True
    assert row["local_only_marker_present"] is True
    assert row["must_not_export_marker_present"] is True
    assert row["disposal_required_marker_present"] is True
    assert row["body_full_packet_materialized_here"] is False
    assert row["body_full_packet_body_copied_here"] is False
    assert row["local_absolute_path_included"] is False
    assert row["body_content_hash_stored_here"] is False
    assert row["export_candidate_detected"] is False
    assert row["export_denylist_violation_detected"] is False
    assert row["body_free"] is True


def test_r51_r6_blocks_when_a_required_packet_is_missing_or_incomplete() -> None:
    rows = deepcopy(_scan()["packet_scan_rows"])
    rows[0]["packet_present_local_only"] = False
    scan = r51.build_p7_r51_body_full_packet_completeness_export_denylist_scan_bodyfree(
        local_only_body_full_packet_generation_request=_request(),
        packet_completion_rows=rows,
    )
    assert scan["packet_completeness_scan_status"] == "BLOCKED_BY_PACKET_COMPLETENESS_OR_EXPORT_DENYLIST"
    assert scan["body_full_packet_completeness_verified"] is False
    assert scan["r6_body_full_packet_completeness_export_denylist_scan_built"] is False
    assert scan["missing_packet_ref_count"] == 1
    assert "r51_case_material_missing" in scan["execution_blocker_ids"]
    assert scan["next_required_step"] == r51.P7_R51_R6_BLOCKED_NEXT_REQUIRED_STEP_REF

    rows = deepcopy(_scan()["packet_scan_rows"])
    rows[0]["required_field_refs_present"] = False
    scan = r51.build_p7_r51_body_full_packet_completeness_export_denylist_scan_bodyfree(
        local_only_body_full_packet_generation_request=_request(),
        packet_completion_rows=rows,
    )
    assert scan["packet_completeness_scan_status"] == "BLOCKED_BY_PACKET_COMPLETENESS_OR_EXPORT_DENYLIST"
    assert scan["incomplete_packet_ref_count"] == 1
    assert "r51_body_full_packet_generation_failed" in scan["execution_blocker_ids"]


def test_r51_r6_blocks_export_denylist_hits_without_storing_export_candidates() -> None:
    scan = r51.build_p7_r51_body_full_packet_completeness_export_denylist_scan_bodyfree(
        local_only_body_full_packet_generation_request=_request(),
        export_candidate_refs=["body_full_packets.local_only/packet_hidden.json"],
    )
    assert scan["packet_completeness_scan_status"] == "BLOCKED_BY_PACKET_COMPLETENESS_OR_EXPORT_DENYLIST"
    assert scan["export_candidate_refs_checked_count"] == 1
    assert scan["denied_export_candidate_count"] == 1
    assert scan["body_full_packet_export_violation_detected"] is True
    assert "r51_body_full_packet_export_violation" in scan["execution_blocker_ids"]
    assert scan["export_candidate_refs_stored_here"] is False
    assert scan["export_candidate_body_stored_here"] is False
    assert scan["next_required_step"] == r51.P7_R51_R6_BLOCKED_NEXT_REQUIRED_STEP_REF


def test_r51_r6_contract_rejects_path_hash_body_or_review_claims() -> None:
    for key in (
        "local_absolute_path_included",
        "body_content_hash_stored_here",
        "packet_body_included_here",
        "packet_body_copied_here",
        "body_full_packet_generated_here",
        "body_full_packets_created_local_only",
        "actual_human_review_run_here",
        "release_allowed",
    ):
        scan = _scan()
        scan[key] = True
        with pytest.raises(ValueError):
            r51.assert_p7_r51_body_full_packet_completeness_export_denylist_scan_bodyfree_contract(scan)


def test_r51_r7_freezes_reviewer_instruction_and_rating_form_without_running_review() -> None:
    freeze = _freeze()
    assert freeze["schema_version"] == r51.P7_R51_REVIEWER_INSTRUCTION_RATING_FORM_FREEZE_SCHEMA_VERSION
    assert set(freeze) == set(r51.P7_R51_REVIEWER_INSTRUCTION_RATING_FORM_FREEZE_REQUIRED_FIELD_REFS)
    assert freeze["policy_section"] == "R51-7_reviewer_instruction_rating_form_freeze"
    assert freeze["review_session_status"] == "R51_REVIEWER_INSTRUCTION_RATING_FORM_READY"
    assert freeze["instruction_form_status"] == "READY_FOR_ACTUAL_HUMAN_REVIEW_RUN"
    assert freeze["next_required_step"] == r51.P7_R51_R7_NEXT_REQUIRED_STEP_REF
    assert freeze["required_case_count"] == 24
    assert freeze["packet_scan_row_count"] == 24
    assert freeze["review_prompt_version"] == r51.P7_R51_REVIEW_PROMPT_VERSION
    assert freeze["reviewer_instruction_version"] == r50.P7_R50_REVIEWER_INSTRUCTION_VERSION
    assert freeze["rating_form_version"] == r50.P7_R50_RATING_FORM_VERSION
    assert tuple(freeze["reviewer_check_item_refs"]) == r50.P7_R50_REVIEWER_CHECK_ITEM_REFS
    assert tuple(freeze["required_reviewer_check_label_refs"]) == r50.P7_R50_REQUIRED_REVIEWER_CHECK_LABEL_REFS
    assert tuple(freeze["rating_axis_refs"]) == r50.P5_HUMAN_BLIND_QA_RATING_AXES
    assert freeze["rating_axis_target_refs"] == dict(r50.P5_HUMAN_BLIND_QA_TARGETS)
    assert freeze["rating_axis_count"] == 6
    assert freeze["rating_score_min"] == 0.0
    assert freeze["rating_score_max"] == 1.0
    assert tuple(freeze["verdict_refs"]) == r50.P7_R50_RATING_VERDICT_REFS
    assert tuple(freeze["readfeel_blocker_id_refs"]) == r48.P7_R48_READFEEL_BLOCKER_ID_REFS
    assert freeze["body_full_packet_completeness_verified"] is True
    assert freeze["local_only_body_full_generation_allowed"] is True
    assert freeze["reviewer_instruction_materialized_for_actual_review_here"] is False
    assert freeze["actual_rating_rows_materialized_here"] is False
    assert freeze["actual_question_need_observation_rows_materialized_here"] is False
    assert freeze["actual_human_review_run_here"] is False
    assert freeze["actual_manual_review_run_here"] is False
    assert freeze["p7_complete"] is False
    assert freeze["p8_start_allowed"] is False
    assert freeze["release_allowed"] is False
    assert tuple(freeze["implemented_steps"]) == r51.P7_R51_R7_IMPLEMENTED_STEPS
    assert tuple(freeze["not_yet_implemented_steps"]) == r51.P7_R51_R7_NOT_YET_IMPLEMENTED_STEPS
    _assert_body_free_no_promotion(freeze)


def test_r51_r7_keeps_blind_policy_question_text_and_reviewer_free_text_boundaries() -> None:
    freeze = _freeze()
    assert tuple(freeze["reviewer_visible_field_refs"]) == r51.P7_R50_REVIEWER_VISIBLE_FIELD_REFS
    assert tuple(freeze["reviewer_hidden_field_refs"]) == r51.P7_R50_REVIEWER_HIDDEN_FIELD_REFS
    assert freeze["blind_case_id_required"] is True
    assert freeze["case_ref_hidden_from_reviewer"] is True
    assert freeze["family_hidden_from_reviewer"] is True
    assert freeze["subscription_tier_hidden_from_reviewer"] is True
    assert freeze["controller_expected_result_hidden_from_reviewer"] is True
    assert freeze["gate_expected_result_hidden_from_reviewer"] is True
    assert freeze["p5_confirmed_conditions_hidden_from_reviewer"] is True
    assert freeze["p8_material_candidate_conditions_hidden_from_reviewer"] is True
    assert freeze["question_need_observation_selection_required"] is True
    assert tuple(freeze["question_need_primary_class_refs"]) == r50.P7_R50_QUESTION_NEED_PRIMARY_CLASS_REFS
    assert tuple(freeze["ambiguity_kind_refs"]) == r50.P7_R50_AMBIGUITY_KIND_REFS
    assert tuple(freeze["one_question_fit_refs"]) == r50.P7_R50_ONE_QUESTION_FIT_REFS
    assert tuple(freeze["repair_required_ref_refs"]) == r50.P7_R50_REPAIR_REQUIRED_REF_REFS
    assert freeze["question_text_required"] is False
    assert freeze["draft_question_text_allowed"] is False
    assert freeze["reviewer_free_text_local_only"] is True
    assert freeze["reviewer_free_text_bodyfree_export_allowed"] is False
    assert freeze["reviewer_free_text_to_sanitized_reason_ids_required"] is True
    assert freeze["p5_weakness_must_not_be_hidden_by_question_candidate"] is True


def test_r51_r7_blocks_when_r6_scan_is_blocked() -> None:
    rows = deepcopy(_scan()["packet_scan_rows"])
    rows[0]["packet_present_local_only"] = False
    blocked_scan = r51.build_p7_r51_body_full_packet_completeness_export_denylist_scan_bodyfree(
        local_only_body_full_packet_generation_request=_request(),
        packet_completion_rows=rows,
    )
    freeze = r51.build_p7_r51_reviewer_instruction_rating_form_freeze_bodyfree(
        body_full_packet_completeness_export_denylist_scan=blocked_scan,
    )
    assert freeze["instruction_form_status"] == "BLOCKED_BY_R51_6_PACKET_COMPLETENESS_SCAN"
    assert freeze["review_session_status"] == "PRECHECK_BLOCKED"
    assert freeze["local_only_body_full_generation_allowed"] is False
    assert freeze["r7_reviewer_instruction_rating_form_freeze_built"] is False
    assert "r51_case_material_missing" in freeze["execution_blocker_ids"]
    assert freeze["next_required_step"] == r51.P7_R51_R7_BLOCKED_NEXT_REQUIRED_STEP_REF


@pytest.mark.parametrize(
    "key,value",
    [
        ("extra_rating_axis_allowed", True),
        ("machine_auto_score_allowed", True),
        ("question_text_required", True),
        ("draft_question_text_allowed", True),
        ("reviewer_free_text_bodyfree_export_allowed", True),
        ("actual_rating_rows_materialized_here", True),
        ("actual_human_review_run_here", True),
        ("p8_start_allowed", True),
        ("release_allowed", True),
    ],
)
def test_r51_r7_contract_rejects_extra_axis_question_text_rating_review_or_release_claims(key: str, value: object) -> None:
    freeze = _freeze()
    freeze[key] = value
    with pytest.raises(ValueError):
        r51.assert_p7_r51_reviewer_instruction_rating_form_freeze_bodyfree_contract(freeze)


def test_r51_r0_to_r7_chain_returns_ready_instruction_freeze_without_review_or_p8_start() -> None:
    freeze = r51.build_p7_r51_r0_r7_reviewer_instruction_rating_form_chain(
        local_review_root="/tmp/cocolon_r51_actual_local_review_root",
        explicit_allow_token=r51.P7_R51_EXPLICIT_ACTUAL_LOCAL_MANUAL_RUN_ALLOW_TOKEN_REF,
        purge_plan=r51.build_p7_r51_default_local_only_purge_plan_bodyfree(),
    )
    assert freeze["instruction_form_status"] == "READY_FOR_ACTUAL_HUMAN_REVIEW_RUN"
    assert freeze["next_required_step"] == r51.P7_R51_R7_NEXT_REQUIRED_STEP_REF
    assert freeze["r6_body_full_packet_completeness_export_denylist_scan_built"] is True
    assert freeze["r7_reviewer_instruction_rating_form_freeze_built"] is True
    assert freeze["actual_manual_review_run_here"] is False
    assert freeze["actual_rating_rows_materialized_here"] is False
    assert freeze["p7_complete"] is False
    assert freeze["p8_start_allowed"] is False
    assert freeze["release_allowed"] is False
