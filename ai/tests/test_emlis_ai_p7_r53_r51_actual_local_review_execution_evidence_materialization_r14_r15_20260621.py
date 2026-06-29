# -*- coding: utf-8 -*-
"""P7-R53 R14/R15 tests for consistency guard and review lifecycle protocol."""

from __future__ import annotations

from copy import deepcopy
from pathlib import Path
import sys

import pytest

_R53_R14_READY_CACHE: dict[str, object] | None = None

sys.path.append(str(Path(__file__).resolve().parent))

import emlis_ai_p7_r51_p5_human_blind_qa_actual_local_manual_run as r51
import emlis_ai_p7_r53_r51_actual_local_review_execution_evidence_materialization as r53
from test_emlis_ai_p7_r53_r51_actual_local_review_execution_evidence_materialization_r12_r13_20260621 import (
    _question_candidate_rows,
    _r53_r10_from_rows,
    _r53_r10_ready,
    _r53_r11_from_r10,
    _r53_r11_ready,
    _r53_r12_ready,
)


def _assert_no_body_payload_key_like_values(material: dict[str, object]) -> None:
    serialized = repr(material)
    for forbidden_key_repr in (
        "'raw_input':",
        "'raw_answer':",
        "'comment_text':",
        "'body':",
        "'returned_emlis_surface':",
        "'current_input_review_surface':",
        "'bounded_owned_history_surface':",
        "'reviewer_free_text':",
        "'reviewer_notes':",
        "'question_text':",
        "'draft_question_text':",
        "'local_absolute_path':",
        "'body_content_hash':",
        "'packet_content_hash':",
    ):
        assert forbidden_key_repr not in serialized


def _assert_common_no_p8_release_or_runtime_change(material: dict[str, object]) -> None:
    assert material["body_free"] is True
    assert material["git_connection_required"] is False
    assert material["git_checked"] is False
    assert material["p8_start_allowed"] is False
    assert material["p7_complete"] is False
    assert material["release_allowed"] is False
    assert material["api_db_rn_response_key_changed_here"] is False
    assert material["runtime_changed_here"] is False
    assert material["body_full_packet_generated_here"] is False
    assert material["body_full_packets_created_local_only"] is False
    assert material["actual_reviewer_notes_materialized_here"] is False


def _r53_r13_ready() -> dict[str, object]:
    normalizer = r53.build_p7_r53_question_need_observation_row_normalization_bodyfree(
        readfeel_blocker_execution_blocker_ingestion_bodyfree=_r53_r12_ready(),
        actual_human_review_result_capture=_r53_r10_ready(),
    )
    assert r53.assert_p7_r53_question_need_observation_row_normalization_bodyfree_contract(normalizer) is True
    return normalizer


def _r53_r14_ready() -> dict[str, object]:
    global _R53_R14_READY_CACHE
    if _R53_R14_READY_CACHE is None:
        guard = r53.build_p7_r53_rating_question_consistency_guard_bodyfree(
            rating_row_normalization_bodyfree=_r53_r11_ready(),
            readfeel_blocker_execution_blocker_ingestion_bodyfree=_r53_r12_ready(),
            question_need_observation_row_normalization_bodyfree=_r53_r13_ready(),
        )
        assert r53.assert_p7_r53_rating_question_consistency_guard_bodyfree_contract(guard) is True
        _R53_R14_READY_CACHE = guard
    return deepcopy(_R53_R14_READY_CACHE)


def _red_routed_to_question_candidate_r14() -> dict[str, object]:
    rows = deepcopy(_question_candidate_rows())
    rows[0]["verdict"] = "RED"
    rows[0]["axis_scores"] = {
        "history_connection_naturalness": 0.2,
        "creepy_absence": 0.1,
        "overclaim_absence": 0.2,
        "self_blame_non_amplification": 0.2,
        "wants_more_input_or_accumulation": 0.2,
        "non_shallow_repeat": 0.2,
    }
    rows[0]["sanitized_reason_ids"] = ["p5_history_creepy_or_surveillance_feeling"]
    rows[0]["blocker_ids"] = ["p5_history_creepy_or_surveillance_feeling"]
    capture = _r53_r10_from_rows(rows)
    rating_rows = _r53_r11_from_r10(capture)
    ingestion = r53.build_p7_r53_readfeel_blocker_execution_blocker_ingestion_bodyfree(
        rating_row_normalization_bodyfree=rating_rows,
    )
    normalizer = r53.build_p7_r53_question_need_observation_row_normalization_bodyfree(
        readfeel_blocker_execution_blocker_ingestion_bodyfree=ingestion,
        actual_human_review_result_capture=capture,
    )
    guard = r53.build_p7_r53_rating_question_consistency_guard_bodyfree(
        rating_row_normalization_bodyfree=rating_rows,
        readfeel_blocker_execution_blocker_ingestion_bodyfree=ingestion,
        question_need_observation_row_normalization_bodyfree=normalizer,
    )
    assert r53.assert_p7_r53_rating_question_consistency_guard_bodyfree_contract(guard) is True
    return guard


def test_r53_r14_default_consistency_guard_is_blocked_without_ready_rating_and_question_rows() -> None:
    guard = r53.build_p7_r53_rating_question_consistency_guard_bodyfree()

    assert guard["schema_version"] == r53.P7_R53_RATING_QUESTION_CONSISTENCY_GUARD_SCHEMA_VERSION
    assert set(guard) == set(r53.P7_R53_RATING_QUESTION_CONSISTENCY_GUARD_REQUIRED_FIELD_REFS)
    assert guard["policy_section"] == "R53-14_rating_question_consistency_guard"
    assert guard["rating_question_consistency_guard_status"] == "BLOCKED_BY_RATING_QUESTION_OBSERVATION_INCONSISTENCY"
    assert guard["r11_ready_for_consistency_guard"] is False
    assert guard["r12_ready_for_consistency_guard"] is False
    assert guard["r13_ready_for_consistency_guard"] is False
    assert guard["p5_weakness_not_hidden_by_question_candidates"] is False
    assert guard["actual_question_need_observation_rows_materialized_here"] is False
    assert guard["p5_actual_review_still_not_run"] is True
    assert guard["r53_14_rating_question_consistency_guard_built"] is False
    assert guard["execution_blocker_ids"]
    assert guard["open_execution_blocker_ids"] == guard["execution_blocker_ids"]
    assert guard["next_required_step"] == r53.P7_R53_R14_BLOCKED_NEXT_REQUIRED_STEP_REF

    _assert_common_no_p8_release_or_runtime_change(guard)
    _assert_no_body_payload_key_like_values(guard)


def test_r53_r14_ready_passes_when_rating_rows_and_question_rows_are_consistent() -> None:
    guard = _r53_r14_ready()

    assert guard["rating_question_consistency_guard_status"] == "READY_FOR_PAUSE_ABORT_EXPIRATION_PROTOCOL"
    assert guard["review_session_status"] == "R53_RATING_QUESTION_CONSISTENCY_GUARD_READY"
    assert guard["r11_ready_for_consistency_guard"] is True
    assert guard["r12_ready_for_consistency_guard"] is True
    assert guard["r13_ready_for_consistency_guard"] is True
    assert guard["r51_r12_next_required_step"] == r51.P7_R51_R12_NEXT_REQUIRED_STEP_REF
    assert guard["rating_row_count"] == 24
    assert guard["question_observation_row_count"] == 24
    assert guard["rating_question_case_ref_sets_match"] is True
    assert guard["all_required_rows_present"] is True
    assert guard["consistency_issue_count"] == 0
    assert guard["consistency_issue_rows"] == []
    assert guard["p5_weakness_not_hidden_by_question_candidates"] is True
    assert guard["actual_human_review_run_here"] is True
    assert guard["actual_manual_review_run_here"] is True
    assert guard["actual_rating_rows_materialized_here"] is True
    assert guard["actual_blocker_rows_materialized_here"] is True
    assert guard["actual_execution_blocker_rows_materialized_here"] is True
    assert guard["actual_question_need_observation_rows_materialized_here"] is True
    assert guard["actual_question_need_observation_summary_materialized_here"] is False
    assert guard["p5_actual_review_still_not_run"] is False
    assert guard["p8_question_design_material_candidate"] is False
    assert guard["p8_start_allowed"] is False
    assert guard["execution_blocker_ids"] == []
    assert guard["r53_14_rating_question_consistency_guard_built"] is True
    assert guard["next_required_step"] == r53.P7_R53_R14_NEXT_REQUIRED_STEP_REF
    assert tuple(guard["implemented_steps"]) == r53.P7_R53_R14_IMPLEMENTED_STEPS
    assert tuple(guard["not_yet_implemented_steps"]) == r53.P7_R53_R14_NOT_YET_IMPLEMENTED_STEPS
    assert r51.assert_p7_r51_rating_question_observation_consistency_guard_bodyfree_contract(
        guard["r51_r12_rating_question_observation_consistency_guard_bodyfree"],
        allowed_true_false_key_refs=r53.P7_R53_R14_ALLOWED_TRUE_FALSE_KEY_REFS,
    ) is True

    _assert_common_no_p8_release_or_runtime_change(guard)
    _assert_no_body_payload_key_like_values(guard)


def test_r53_r14_allows_plus_question_material_counts_only_when_p5_rating_is_not_repair() -> None:
    capture = _r53_r10_from_rows(_question_candidate_rows())
    rating_rows = _r53_r11_from_r10(capture)
    ingestion = r53.build_p7_r53_readfeel_blocker_execution_blocker_ingestion_bodyfree(
        rating_row_normalization_bodyfree=rating_rows,
    )
    normalizer = r53.build_p7_r53_question_need_observation_row_normalization_bodyfree(
        readfeel_blocker_execution_blocker_ingestion_bodyfree=ingestion,
        actual_human_review_result_capture=capture,
    )
    guard = r53.build_p7_r53_rating_question_consistency_guard_bodyfree(
        rating_row_normalization_bodyfree=rating_rows,
        readfeel_blocker_execution_blocker_ingestion_bodyfree=ingestion,
        question_need_observation_row_normalization_bodyfree=normalizer,
    )

    assert guard["rating_question_consistency_guard_status"] == "READY_FOR_PAUSE_ABORT_EXPIRATION_PROTOCOL"
    assert guard["p8_question_material_candidate_allowed_by_consistency"] is True
    assert guard["p8_question_material_candidate_case_count"] >= 1
    assert guard["question_candidate_allowed_case_count"] >= 1
    assert guard["p8_question_design_material_candidate"] is False
    assert guard["p8_start_allowed"] is False
    assert guard["p8_question_implementation_spec_finalized_here"] is False
    assert guard["question_trigger_logic_implemented_here"] is False

    _assert_no_body_payload_key_like_values(guard)


def test_r53_r14_blocks_red_or_repair_rows_routed_to_question_candidate() -> None:
    guard = _red_routed_to_question_candidate_r14()

    assert guard["rating_question_consistency_guard_status"] == "BLOCKED_BY_RATING_QUESTION_OBSERVATION_INCONSISTENCY"
    assert guard["consistency_issue_count"] >= 1
    assert guard["consistency_issue_id_counts"]["r51_red_or_repair_required_routed_to_question_candidate"] == 1  # type: ignore[index]
    assert "r53_rating_question_observation_inconsistent" in guard["execution_blocker_ids"]
    assert guard["p5_weakness_not_hidden_by_question_candidates"] is False
    assert guard["p8_question_material_candidate_allowed_by_consistency"] is False
    assert guard["question_candidate_allowed_case_count"] == 0
    assert guard["actual_human_review_run_here"] is True
    assert guard["actual_question_need_observation_rows_materialized_here"] is True
    assert guard["p5_actual_review_still_not_run"] is False
    assert guard["r53_14_rating_question_consistency_guard_built"] is False
    assert guard["next_required_step"] == r53.P7_R53_R14_BLOCKED_NEXT_REQUIRED_STEP_REF

    _assert_common_no_p8_release_or_runtime_change(guard)
    _assert_no_body_payload_key_like_values(guard)


def test_r53_r14_rejects_question_text_p8_promotion_runtime_changes_or_bodyfull_generation() -> None:
    base_guard = _r53_r14_ready()
    forbidden_pairs = [
        ("question_text_included_allowed", True),
        ("draft_question_text_included_allowed", True),
        ("reviewer_free_text_included_allowed", True),
        ("raw_input_allowed", True),
        ("returned_surface_allowed", True),
        ("local_path_allowed", True),
        ("body_hash_allowed", True),
        ("p8_question_implementation_spec_finalized_here", True),
        ("question_trigger_logic_implemented_here", True),
        ("p8_question_design_material_candidate", True),
        ("p8_start_allowed", True),
        ("release_allowed", True),
        ("api_db_rn_response_key_changed_here", True),
        ("runtime_changed_here", True),
        ("body_full_packet_generated_here", True),
        ("body_full_packets_created_local_only", True),
    ]
    for key, value in forbidden_pairs:
        guard = deepcopy(base_guard)
        guard[key] = value
        with pytest.raises(ValueError):
            r53.assert_p7_r53_rating_question_consistency_guard_bodyfree_contract(guard)


def test_r53_r15_default_protocol_is_blocked_without_ready_consistency_guard() -> None:
    protocol = r53.build_p7_r53_pause_abort_expiration_protocol_bodyfree()

    assert protocol["schema_version"] == r53.P7_R53_PAUSE_ABORT_EXPIRATION_PROTOCOL_SCHEMA_VERSION
    assert set(protocol) == set(r53.P7_R53_PAUSE_ABORT_EXPIRATION_PROTOCOL_REQUIRED_FIELD_REFS)
    assert protocol["policy_section"] == "R53-15_pause_abort_expiration_protocol"
    assert protocol["pause_abort_expiration_protocol_status"] == "BLOCKED_BY_R53_14_CONSISTENCY_GUARD"
    assert protocol["r14_ready_for_pause_abort_expiration_protocol"] is False
    assert protocol["r53_15_pause_abort_expiration_protocol_built"] is False
    assert protocol["body_full_packet_purge_required"] is False
    assert protocol["reviewer_notes_purge_required"] is False
    assert protocol["actual_disposal_run_here"] is False
    assert protocol["disposal_receipt_materialized_here"] is False
    assert protocol["execution_blocker_ids"]
    assert protocol["open_execution_blocker_ids"] == protocol["execution_blocker_ids"]
    assert protocol["next_required_step"] == r53.P7_R53_R15_BLOCKED_NEXT_REQUIRED_STEP_REF

    _assert_common_no_p8_release_or_runtime_change(protocol)
    _assert_no_body_payload_key_like_values(protocol)


def test_r53_r15_completed_review_continues_to_purge_without_creating_disposal_receipt_here() -> None:
    protocol = r53.build_p7_r53_pause_abort_expiration_protocol_bodyfree(
        rating_question_consistency_guard_bodyfree=_r53_r14_ready(),
        review_lifecycle_status="REVIEW_COMPLETED",
    )

    assert protocol["pause_abort_expiration_protocol_status"] == "READY_FOR_BODY_FULL_PACKET_REVIEWER_NOTES_PURGE"
    assert protocol["review_session_status"] == "R53_PAUSE_ABORT_EXPIRATION_PROTOCOL_READY"
    assert protocol["pause_abort_expiration_action_ref"] == "CONTINUE_TO_R51_14_PURGE"
    assert protocol["r14_ready_for_pause_abort_expiration_protocol"] is True
    assert protocol["r51_r13_next_required_step"] == r51.P7_R51_R13_NEXT_REQUIRED_STEP_REF
    assert protocol["body_full_packet_purge_required"] is True
    assert protocol["reviewer_forms_purge_required"] is True
    assert protocol["reviewer_notes_purge_required"] is True
    assert protocol["purge_required_before_summary"] is True
    assert protocol["body_removed"] is False
    assert protocol["reviewer_notes_removed"] is False
    assert protocol["actual_disposal_run_here"] is False
    assert protocol["disposal_receipt_materialized_here"] is False
    assert protocol["actual_disposal_receipt_materialized_here"] is False
    assert protocol["post_review_summary_materialized_here"] is False
    assert protocol["actual_human_review_run_here"] is True
    assert protocol["actual_question_need_observation_rows_materialized_here"] is True
    assert protocol["p5_actual_review_still_not_run"] is False
    assert protocol["r53_15_pause_abort_expiration_protocol_built"] is True
    assert protocol["next_required_step"] == r53.P7_R53_R15_NEXT_REQUIRED_STEP_REF
    assert tuple(protocol["implemented_steps"]) == r53.P7_R53_R15_IMPLEMENTED_STEPS
    assert tuple(protocol["not_yet_implemented_steps"]) == r53.P7_R53_R15_NOT_YET_IMPLEMENTED_STEPS
    assert r51.assert_p7_r51_pause_abort_expiration_protocol_bodyfree_contract(
        protocol["r51_r13_pause_abort_expiration_protocol_bodyfree"],
        allowed_true_false_key_refs=r53.P7_R53_R15_ALLOWED_TRUE_FALSE_KEY_REFS,
    ) is True

    _assert_common_no_p8_release_or_runtime_change(protocol)
    _assert_no_body_payload_key_like_values(protocol)


def test_r53_r15_paused_review_keeps_retention_clock_running_and_does_not_purge_yet() -> None:
    protocol = r53.build_p7_r53_pause_abort_expiration_protocol_bodyfree(
        rating_question_consistency_guard_bodyfree=_r53_r14_ready(),
        review_lifecycle_status="REVIEW_PAUSED",
        body_full_packet_age_hours=1,
    )

    assert protocol["pause_abort_expiration_protocol_status"] == "PAUSED_RETENTION_CLOCK_STILL_RUNNING"
    assert protocol["pause_abort_expiration_action_ref"] == "PAUSE_LOCAL_ONLY_REVIEW"
    assert protocol["retention_clock_stops_on_pause"] is False
    assert protocol["review_pause_does_not_stop_retention_deadline"] is True
    assert protocol["body_full_packet_purge_required"] is False
    assert protocol["purge_required_before_summary"] is False
    assert protocol["reviewer_notes_purge_required"] is True
    assert protocol["next_required_step"] == r53.P7_R53_R15_PAUSED_NEXT_REQUIRED_STEP_REF
    assert protocol["r53_15_pause_abort_expiration_protocol_built"] is True

    _assert_common_no_p8_release_or_runtime_change(protocol)
    _assert_no_body_payload_key_like_values(protocol)


@pytest.mark.parametrize(
    "review_lifecycle_status,expected_status,expected_action",
    [
        ("REVIEW_ABORTED", "ABORTED_PURGE_REQUIRED", "ABORT_LOCAL_ONLY_REVIEW"),
        ("REVIEW_EXPIRED", "EXPIRED_PURGE_REQUIRED", "EXPIRE_LOCAL_ONLY_REVIEW"),
    ],
)
def test_r53_r15_aborted_or_expired_review_requires_purge_and_blocks_p5_candidates(
    review_lifecycle_status: str,
    expected_status: str,
    expected_action: str,
) -> None:
    protocol = r53.build_p7_r53_pause_abort_expiration_protocol_bodyfree(
        rating_question_consistency_guard_bodyfree=_r53_r14_ready(),
        review_lifecycle_status=review_lifecycle_status,
    )

    assert protocol["pause_abort_expiration_protocol_status"] == expected_status
    assert protocol["pause_abort_expiration_action_ref"] == expected_action
    assert protocol["body_full_packet_purge_required"] is True
    assert protocol["reviewer_forms_purge_required"] is True
    assert protocol["reviewer_notes_purge_required"] is True
    assert protocol["purge_required_before_summary"] is True
    assert protocol["aborted_or_expired_blocks_p5_confirmed_candidate"] is True
    assert protocol["p5_confirmed_candidate_allowed_after_protocol"] is False
    assert protocol["p5_human_blind_qa_confirmed_candidate"] is False
    assert protocol["p6_limited_human_readfeel_start_allowed_candidate"] is False
    assert protocol["p8_question_design_material_candidate"] is False
    assert protocol["next_required_step"] == r53.P7_R53_R15_NEXT_REQUIRED_STEP_REF

    _assert_common_no_p8_release_or_runtime_change(protocol)
    _assert_no_body_payload_key_like_values(protocol)


def test_r53_r15_expired_by_packet_age_prioritizes_body_removal_even_if_lifecycle_says_paused() -> None:
    protocol = r53.build_p7_r53_pause_abort_expiration_protocol_bodyfree(
        rating_question_consistency_guard_bodyfree=_r53_r14_ready(),
        review_lifecycle_status="REVIEW_PAUSED",
        body_full_packet_age_hours=999,
    )

    assert protocol["pause_abort_expiration_protocol_status"] == "EXPIRED_PURGE_REQUIRED"
    assert protocol["body_full_packet_retention_expired"] is True
    assert protocol["body_removed_priority_over_rating_completion_when_expired"] is True
    assert protocol["body_full_packet_purge_required"] is True
    assert protocol["next_required_step"] == r53.P7_R53_R15_NEXT_REQUIRED_STEP_REF

    _assert_no_body_payload_key_like_values(protocol)


def test_r53_r15_rejects_purge_claims_disposal_receipt_p5_candidate_p8_release_or_runtime_change() -> None:
    base_protocol = r53.build_p7_r53_pause_abort_expiration_protocol_bodyfree(
        rating_question_consistency_guard_bodyfree=_r53_r14_ready(),
    )
    forbidden_pairs = [
        ("retention_clock_stops_on_pause", True),
        ("body_removed", True),
        ("reviewer_notes_removed", True),
        ("local_packet_exported", True),
        ("content_hash_of_body_stored", True),
        ("p5_confirmed_candidate_allowed_after_protocol", True),
        ("p5_repair_return_candidate_allowed_after_protocol", True),
        ("disposal_receipt_materialized_here", True),
        ("actual_disposal_run_here", True),
        ("actual_disposal_receipt_materialized_here", True),
        ("post_review_summary_materialized_here", True),
        ("p8_question_implementation_spec_finalized_here", True),
        ("question_trigger_logic_implemented_here", True),
        ("api_db_rn_response_key_changed_here", True),
        ("body_full_packet_generated_here", True),
        ("body_full_packets_created_local_only", True),
        ("p8_start_allowed", True),
        ("release_allowed", True),
        ("runtime_changed_here", True),
    ]
    for key, value in forbidden_pairs:
        protocol = deepcopy(base_protocol)
        protocol[key] = value
        with pytest.raises(ValueError):
            r53.assert_p7_r53_pause_abort_expiration_protocol_bodyfree_contract(protocol)
