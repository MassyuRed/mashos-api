# -*- coding: utf-8 -*-
"""P7-R53 R16/R17 tests for purge/disposal receipt and post-review summary."""

from __future__ import annotations

from copy import deepcopy
from pathlib import Path
import sys

import pytest

_R53_R15_READY_CACHE: dict[str, object] | None = None
_R53_R16_READY_CACHE: dict[str, object] | None = None
_R53_R17_READY_CACHE: dict[str, object] | None = None

sys.path.append(str(Path(__file__).resolve().parent))

import emlis_ai_p7_r51_p5_human_blind_qa_actual_local_manual_run as r51
import emlis_ai_p7_r53_r51_actual_local_review_execution_evidence_materialization as r53
from test_emlis_ai_p7_r53_r51_actual_local_review_execution_evidence_materialization_r12_r13_20260621 import (
    _r53_r11_ready,
    _r53_r12_ready,
)
from test_emlis_ai_p7_r53_r51_actual_local_review_execution_evidence_materialization_r14_r15_20260621 import (
    _assert_common_no_p8_release_or_runtime_change,
    _assert_no_body_payload_key_like_values,
    _r53_r13_ready,
    _r53_r14_ready,
)


def _assert_bodyfree_no_export_payload_flags(material: dict[str, object]) -> None:
    assert material["body_free"] is True
    for key in (
        "raw_input_included",
        "returned_surface_included",
        "comment_text_included",
        "reviewer_free_text_included",
        "question_text_included",
        "draft_question_text_included",
        "local_absolute_path_included",
        "body_content_hash_included",
        "deleted_body_preview_included",
        "terminal_output_included",
        "local_packet_exported",
        "content_hash_of_body_stored",
    ):
        if key in material:
            assert material[key] is False



def _r53_r15_completed_review_ready() -> dict[str, object]:
    global _R53_R15_READY_CACHE
    if _R53_R15_READY_CACHE is None:
        protocol = r53.build_p7_r53_pause_abort_expiration_protocol_bodyfree(
            rating_question_consistency_guard_bodyfree=_r53_r14_ready(),
            review_lifecycle_status="REVIEW_COMPLETED",
        )
        assert r53.assert_p7_r53_pause_abort_expiration_protocol_bodyfree_contract(protocol) is True
        _R53_R15_READY_CACHE = protocol
    return deepcopy(_R53_R15_READY_CACHE)


def _r53_r16_ready() -> dict[str, object]:
    global _R53_R16_READY_CACHE
    if _R53_R16_READY_CACHE is None:
        protocol = _r53_r15_completed_review_ready()
        purge_rows = r53.build_p7_r53_default_verified_purge_evidence_rows_bodyfree(
            review_session_id=protocol["review_session_id"],
        )
        material = r53.build_p7_r53_purge_disposal_receipt_bodyfree(
            pause_abort_expiration_protocol_bodyfree=protocol,
            purge_evidence_rows=purge_rows,
        )
        assert r53.assert_p7_r53_purge_disposal_receipt_bodyfree_contract(material) is True
        _R53_R16_READY_CACHE = material
    return deepcopy(_R53_R16_READY_CACHE)


def _r53_r17_ready() -> dict[str, object]:
    global _R53_R17_READY_CACHE
    if _R53_R17_READY_CACHE is None:
        summary = r53.build_p7_r53_body_free_post_review_summary_bodyfree(
            purge_disposal_receipt_bodyfree=_r53_r16_ready(),
            rating_row_normalization_bodyfree=_r53_r11_ready(),
            readfeel_blocker_execution_blocker_ingestion_bodyfree=_r53_r12_ready(),
            question_need_observation_row_normalization_bodyfree=_r53_r13_ready(),
            rating_question_consistency_guard_bodyfree=_r53_r14_ready(),
        )
        assert r53.assert_p7_r53_body_free_post_review_summary_bodyfree_contract(summary) is True
        _R53_R17_READY_CACHE = summary
    return deepcopy(_R53_R17_READY_CACHE)


def test_r53_r16_default_purge_disposal_receipt_is_blocked_without_completed_r15_protocol() -> None:
    material = r53.build_p7_r53_purge_disposal_receipt_bodyfree()

    assert material["schema_version"] == r53.P7_R53_PURGE_DISPOSAL_RECEIPT_SCHEMA_VERSION
    assert set(material) == set(r53.P7_R53_PURGE_DISPOSAL_RECEIPT_REQUIRED_FIELD_REFS)
    assert material["policy_section"] == "R53-16_purge_disposal_receipt"
    assert material["purge_disposal_receipt_status"] == "BLOCKED_BY_R53_15_PAUSE_OR_BLOCKED_PROTOCOL"
    assert material["r15_ready_for_purge_disposal_receipt"] is False
    assert material["body_removed"] is False
    assert material["reviewer_forms_removed"] is False
    assert material["reviewer_notes_removed"] is False
    assert material["body_full_packets_removed"] is False
    assert material["disposal_verified"] is False
    assert material["actual_disposal_run_here"] is False
    assert material["disposal_receipt_materialized_here"] is False
    assert material["actual_disposal_receipt_materialized_here"] is False
    assert material["local_file_delete_ops_executed_by_helper"] is False
    assert material["execution_blocker_ids"]
    assert material["open_execution_blocker_ids"] == material["execution_blocker_ids"]
    assert material["next_required_step"] == r53.P7_R53_R16_BLOCKED_NEXT_REQUIRED_STEP_REF

    _assert_common_no_p8_release_or_runtime_change(material)
    _assert_bodyfree_no_export_payload_flags(material)


def test_r53_r16_ready_materializes_bodyfree_disposal_receipt_from_verified_purge_rows() -> None:
    material = _r53_r16_ready()

    assert material["purge_disposal_receipt_status"] == "READY_FOR_BODY_FREE_POST_REVIEW_SUMMARY"
    assert material["review_session_status"] == "R53_PURGE_DISPOSAL_RECEIPT_VERIFIED_BODYFREE"
    assert material["r15_ready_for_purge_disposal_receipt"] is True
    assert material["r51_r14_purge_status"] == "READY_FOR_DISPOSAL_RECEIPT_BUILDER_VERIFIER"
    assert material["r51_r15_disposal_receipt_verifier_status"] == "READY_FOR_BODY_FREE_POST_REVIEW_SUMMARY_BUILDER"
    assert material["purge_evidence_row_count"] == len(r53.P7_R51_PURGE_PLAN_REQUIRED_DELETE_TARGET_REFS)
    assert material["purge_target_count"] == len(r53.P7_R51_PURGE_PLAN_REQUIRED_DELETE_TARGET_REFS)
    assert material["verified_purge_target_count"] == len(r53.P7_R51_PURGE_PLAN_REQUIRED_DELETE_TARGET_REFS)
    assert material["deleted_file_count"] == len(r53.P7_R51_PURGE_PLAN_REQUIRED_DELETE_TARGET_REFS) * r53.P7_R51_REQUIRED_CASE_COUNT
    assert material["missing_purge_target_refs"] == []
    assert material["failed_purge_target_refs"] == []
    assert material["not_verified_purge_target_refs"] == []
    assert material["body_removed"] is True
    assert material["reviewer_forms_removed"] is True
    assert material["reviewer_notes_removed"] is True
    assert material["body_full_packets_removed"] is True
    assert material["disposal_verified"] is True
    assert material["disposal_failed"] is False
    assert material["summary_finalize_allowed"] is True
    assert material["local_packet_exported"] is False
    assert material["content_hash_of_body_stored"] is False
    assert material["receipt_contains_body_full_material"] is False
    assert material["local_absolute_path_included"] is False
    assert material["body_content_hash_included"] is False
    assert material["deleted_body_preview_included"] is False
    assert material["terminal_output_included"] is False
    assert material["local_file_delete_ops_executed_by_helper"] is False
    assert material["actual_disposal_run_here"] is True
    assert material["disposal_receipt_materialized_here"] is True
    assert material["actual_disposal_receipt_materialized_here"] is True
    assert material["post_review_summary_materialized_here"] is False
    assert material["p5_actual_review_still_not_run"] is False
    assert material["r53_16_purge_disposal_receipt_built"] is True
    assert material["next_required_step"] == r53.P7_R53_R16_NEXT_REQUIRED_STEP_REF
    assert tuple(material["implemented_steps"]) == r53.P7_R53_R16_IMPLEMENTED_STEPS
    assert tuple(material["not_yet_implemented_steps"]) == r53.P7_R53_R16_NOT_YET_IMPLEMENTED_STEPS
    assert r51.assert_p7_r51_disposal_receipt_builder_verifier_bodyfree_contract(
        material["r51_r15_disposal_receipt_builder_verifier_bodyfree"],
        allowed_true_false_key_refs=r53.P7_R53_R16_ALLOWED_TRUE_FALSE_KEY_REFS,
    ) is True

    _assert_common_no_p8_release_or_runtime_change(material)
    _assert_bodyfree_no_export_payload_flags(material)


def test_r53_r16_blocks_ready_protocol_when_purge_evidence_rows_are_missing() -> None:
    material = r53.build_p7_r53_purge_disposal_receipt_bodyfree(
        pause_abort_expiration_protocol_bodyfree=_r53_r15_completed_review_ready(),
    )

    assert material["purge_disposal_receipt_status"] == "BLOCKED_BY_BODY_FULL_PACKET_REVIEWER_NOTES_PURGE"
    assert material["r15_ready_for_purge_disposal_receipt"] is True
    assert material["purge_evidence_row_count"] == 0
    assert material["missing_purge_target_refs"] == list(r53.P7_R51_PURGE_PLAN_REQUIRED_DELETE_TARGET_REFS)
    assert "r53_disposal_not_verified" in material["execution_blocker_ids"]
    assert material["body_removed"] is False
    assert material["disposal_verified"] is False
    assert material["actual_disposal_run_here"] is False
    assert material["next_required_step"] == r53.P7_R53_R16_BLOCKED_NEXT_REQUIRED_STEP_REF

    _assert_common_no_p8_release_or_runtime_change(material)
    _assert_bodyfree_no_export_payload_flags(material)


def test_r53_r16_blocks_failed_or_unverified_purge_rows_without_exposing_paths_or_hashes() -> None:
    protocol = _r53_r15_completed_review_ready()
    rows = r53.build_p7_r53_default_verified_purge_evidence_rows_bodyfree(
        review_session_id=protocol["review_session_id"],
    )
    rows[0] = dict(rows[0])
    rows[0]["removed"] = False
    rows[0]["verification_status_ref"] = "PURGE_FAILED"
    material = r53.build_p7_r53_purge_disposal_receipt_bodyfree(
        pause_abort_expiration_protocol_bodyfree=protocol,
        purge_evidence_rows=rows,
    )

    assert material["purge_disposal_receipt_status"] == "BLOCKED_BY_BODY_FULL_PACKET_REVIEWER_NOTES_PURGE"
    assert material["failed_purge_target_refs"] == [rows[0]["purge_target_ref"]]
    assert "r53_disposal_failed" in material["execution_blocker_ids"]
    assert material["body_removed"] is False
    assert material["disposal_verified"] is False
    assert material["local_absolute_path_included"] is False
    assert material["body_content_hash_included"] is False
    assert material["deleted_body_preview_included"] is False
    assert material["terminal_output_included"] is False

    _assert_common_no_p8_release_or_runtime_change(material)
    _assert_bodyfree_no_export_payload_flags(material)


def test_r53_r16_rejects_export_body_hash_path_or_promotion_mutations() -> None:
    base = _r53_r16_ready()
    forbidden_pairs = [
        ("local_packet_exported", True),
        ("content_hash_of_body_stored", True),
        ("receipt_contains_body_full_material", True),
        ("local_absolute_path_included", True),
        ("body_content_hash_included", True),
        ("deleted_body_preview_included", True),
        ("terminal_output_included", True),
        ("local_file_delete_ops_executed_by_helper", True),
        ("post_review_summary_materialized_here", True),
        ("p5_human_blind_qa_confirmed_candidate", True),
        ("p8_question_design_material_candidate", True),
        ("p8_start_allowed", True),
        ("release_allowed", True),
        ("runtime_changed_here", True),
        ("body_full_packet_generated_here", True),
    ]
    for key, value in forbidden_pairs:
        material = deepcopy(base)
        material[key] = value
        with pytest.raises(ValueError):
            r53.assert_p7_r53_purge_disposal_receipt_bodyfree_contract(material)


def test_r53_r17_ready_aggregates_only_bodyfree_counts_refs_and_booleans() -> None:
    summary = _r53_r17_ready()

    assert summary["post_review_summary_status"] == "READY_FOR_P5_DECISION_CANDIDATE_SEPARATION"
    assert summary["review_session_status"] == "R53_BODY_FREE_POST_REVIEW_SUMMARY_READY"
    assert summary["r16_ready_for_post_review_summary"] is True
    assert summary["r51_r16_post_review_summary_status"] == "READY_FOR_P5_CONFIRMED_REPAIR_RETURN_INCONCLUSIVE_DECISION"
    assert summary["all_24_cases_reviewed"] is True
    assert summary["rating_row_count"] == 24
    assert summary["question_observation_row_count"] == 24
    assert summary["pass_count"] == 24
    assert summary["red_count"] == 0
    assert summary["repair_required_count"] == 0
    assert summary["yellow_count"] == 0
    assert summary["open_execution_blocker_count"] == 0
    assert summary["execution_blocker_ids"] == []
    assert summary["all_axis_targets_met"] is True
    assert set(summary["axis_score_averages"]) == set(r51.P5_HUMAN_BLIND_QA_RATING_AXES)
    assert set(summary["axis_target_refs"]) == set(r51.P5_HUMAN_BLIND_QA_RATING_AXES)
    assert summary["disposal_verified"] is True
    assert summary["body_removed"] is True
    assert summary["reviewer_forms_removed"] is True
    assert summary["reviewer_notes_removed"] is True
    assert summary["body_free_summary_contains_only_counts_and_refs"] is True
    assert summary["raw_input_included"] is False
    assert summary["returned_surface_included"] is False
    assert summary["comment_text_included"] is False
    assert summary["reviewer_free_text_included"] is False
    assert summary["question_text_included"] is False
    assert summary["draft_question_text_included"] is False
    assert summary["local_absolute_path_included"] is False
    assert summary["body_content_hash_included"] is False
    assert summary["local_packet_exported"] is False
    assert summary["content_hash_of_body_stored"] is False
    assert summary["actual_disposal_run_here"] is True
    assert summary["disposal_receipt_materialized_here"] is True
    assert summary["actual_disposal_receipt_materialized_here"] is True
    assert summary["post_review_summary_materialized_here"] is True
    assert summary["actual_question_need_observation_summary_materialized_here"] is True
    assert summary["p5_human_blind_qa_confirmed_candidate"] is False
    assert summary["p5_repair_return_candidate"] is False
    assert summary["p5_review_inconclusive"] is False
    assert summary["p6_limited_human_readfeel_start_allowed_candidate"] is False
    assert summary["p8_question_design_material_candidate"] is False
    assert summary["p8_start_allowed"] is False
    assert summary["release_allowed"] is False
    assert summary["r53_17_body_free_post_review_summary_built"] is True
    assert summary["next_required_step"] == r53.P7_R53_R17_NEXT_REQUIRED_STEP_REF
    assert tuple(summary["implemented_steps"]) == r53.P7_R53_R17_IMPLEMENTED_STEPS
    assert tuple(summary["not_yet_implemented_steps"]) == r53.P7_R53_R17_NOT_YET_IMPLEMENTED_STEPS
    assert r51.assert_p7_r51_body_free_post_review_summary_builder_bodyfree_contract(
        summary["r51_r16_body_free_post_review_summary_builder_bodyfree"],
        allowed_true_false_key_refs=r53.P7_R53_R17_ALLOWED_TRUE_FALSE_KEY_REFS,
    ) is True

    _assert_common_no_p8_release_or_runtime_change(summary)
    _assert_bodyfree_no_export_payload_flags(summary)


def test_r53_r17_rejects_body_text_path_hash_or_candidate_promotion_mutations() -> None:
    base = _r53_r17_ready()
    forbidden_pairs = [
        ("raw_input_included", True),
        ("returned_surface_included", True),
        ("comment_text_included", True),
        ("reviewer_free_text_included", True),
        ("question_text_included", True),
        ("draft_question_text_included", True),
        ("local_absolute_path_included", True),
        ("body_content_hash_included", True),
        ("local_packet_exported", True),
        ("content_hash_of_body_stored", True),
        ("p5_human_blind_qa_confirmed_candidate", True),
        ("p5_repair_return_candidate", True),
        ("p5_review_inconclusive", True),
        ("p6_limited_human_readfeel_start_allowed_candidate", True),
        ("p8_question_design_material_candidate", True),
        ("p8_start_allowed", True),
        ("p7_complete", True),
        ("release_allowed", True),
        ("api_db_rn_response_key_changed_here", True),
        ("runtime_changed_here", True),
        ("body_full_packet_generated_here", True),
        ("body_full_packets_created_local_only", True),
    ]
    for key, value in forbidden_pairs:
        summary = deepcopy(base)
        summary[key] = value
        with pytest.raises(ValueError):
            r53.assert_p7_r53_body_free_post_review_summary_bodyfree_contract(summary)
