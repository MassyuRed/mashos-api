# -*- coding: utf-8 -*-
from __future__ import annotations

import json
from copy import deepcopy
from pathlib import Path
import sys

import pytest

sys.path.append(str(Path(__file__).resolve().parent))

import emlis_ai_p7_r54_actual_local_review_operation_reentry_20260625 as op
from test_emlis_ai_p7_r54_actual_local_review_operation_reentry_op14_op15_20260625 import (  # noqa: E402
    _op12_ready,
    _op14_ready,
)


FORBIDDEN_DUMP_TOKENS = (
    '"raw_input":', '"raw_answer":', '"comment_text":', '"comment_text_body":',
    '"returned_emlis_surface":', '"current_input_review_surface":', '"bounded_owned_history_review_surface":',
    '"reviewer_free_text":', '"reviewer_note":', '"reviewer_notes":', '"question_text": "',
    '"draft_question_text": "', '"question_body":', '"local_absolute_path":', '"local_directory_path":',
    '"body_content_hash":', '"packet_content_hash":', '"terminal_output": "', '"stdout":', '"stderr":', '"traceback":',
)
FORBIDDEN_PROMOTION_TRUE_TOKENS = (
    '"api_changed": true', '"db_changed": true', '"rn_changed": true', '"runtime_changed": true',
    '"api_route_changed": true', '"db_schema_changed": true', '"rn_visible_contract_changed": true',
    '"public_response_top_level_key_added": true', '"release_allowed": true', '"p7_complete": true',
    '"p8_start_allowed": true', '"p6_limited_human_readfeel_start_allowed": true',
    '"question_trigger_logic_implemented": true', '"p8_question_implementation_spec_finalized_here": true',
    '"actual_human_review_run_here": true', '"actual_manual_review_run_here": true',
    '"body_full_packet_generated_here": true', '"actual_body_full_packet_generated_here": true',
    '"body_full_packet_export_allowed": true', '"body_full_packet_zip_inclusion_allowed": true',
    '"reviewer_notes_export_allowed": true', '"local_path_included": true', '"question_text_included": true',
    '"draft_question_text_included": true', '"actual_disposal_run_here": true',
)


def _assert_body_free_no_promotion(material: dict[str, object]) -> None:
    dumped = json.dumps(material, ensure_ascii=False, sort_keys=True).lower()
    for forbidden in FORBIDDEN_DUMP_TOKENS:
        assert forbidden not in dumped
    for forbidden in FORBIDDEN_PROMOTION_TRUE_TOKENS:
        assert forbidden not in dumped


def _op15_ready() -> dict[str, object]:
    material = op.build_p7_r54_op15_rating_question_consistency_guard(
        question_need_observation_normalization=_op14_ready(),
        rating_row_normalization=_op12_ready(),
    )
    assert op.assert_p7_r54_op15_rating_question_consistency_guard_contract(material) is True
    assert material["rating_question_consistency_guard_status"] == op.P7_R54_OP15_CONSISTENCY_GUARD_READY_STATUS_REF
    return material


def _op16_ready() -> dict[str, object]:
    material = op.build_p7_r54_op16_pause_abort_expiration_protocol(
        rating_question_consistency_guard=_op15_ready(),
    )
    assert op.assert_p7_r54_op16_pause_abort_expiration_protocol_contract(material) is True
    assert material["pause_abort_expiration_protocol_status"] == op.P7_R54_OP16_PROTOCOL_READY_STATUS_REF
    return material


def test_r54_op16_default_protocol_fails_closed_when_op15_is_not_ready() -> None:
    material = op.build_p7_r54_op16_pause_abort_expiration_protocol()

    assert material["schema_version"] == op.P7_R54_OPERATION_PAUSE_ABORT_EXPIRATION_PROTOCOL_SCHEMA_VERSION
    assert set(material) == set(op.P7_R54_OPERATION_PAUSE_ABORT_EXPIRATION_PROTOCOL_REQUIRED_FIELD_REFS)
    assert material["policy_section"] == op.P7_R54_OP16_STEP_REF
    assert material["op15_ready_for_pause_abort_expiration_protocol"] is False
    assert material["pause_abort_expiration_protocol_status"] == op.P7_R54_OP16_PROTOCOL_BLOCKED_STATUS_REF
    assert material["ready_for_purge_disposal_receipt"] is False
    assert material["disposal_receipt_allowed_next"] is False
    assert material["handoff_allowed_before_purge"] is False
    assert material["r52_reintake_handoff_allowed_before_purge"] is False
    assert material["actual_review_evidence_complete"] is False
    assert material["disposal_verified"] is False
    assert material["actual_disposal_receipt_materialized_here"] is False
    assert material["next_required_step"] == op.P7_R54_OP16_BLOCKED_NEXT_REQUIRED_STEP_REF
    assert material["open_execution_blocker_ids"]
    _assert_body_free_no_promotion(material)


def test_r54_op16_ready_protocol_routes_to_purge_without_promoting_review_or_release() -> None:
    material = _op16_ready()

    assert set(material) == set(op.P7_R54_OPERATION_PAUSE_ABORT_EXPIRATION_PROTOCOL_REQUIRED_FIELD_REFS)
    assert material["op15_ready_for_pause_abort_expiration_protocol"] is True
    assert material["pause_abort_expiration_protocol_ref"] == op.P7_R54_OP16_PROTOCOL_REF
    assert material["review_session_cancelled_is_purge_trigger"] is True
    assert material["retention_deadline_reached_is_purge_trigger"] is True
    assert tuple(material["purge_trigger_refs"]) == tuple(op.P7_R47_BODY_FULL_PACKET_DELETE_TRIGGER_REFS)
    assert tuple(material["required_local_delete_target_refs"]) == tuple(op.P7_R54_OP16_REQUIRED_LOCAL_DELETE_TARGET_REFS)
    assert material["rating_row_count"] == 24
    assert material["question_observation_row_count"] == 24
    assert material["actual_rating_rows_materialized_here"] is True
    assert material["actual_question_need_observation_rows_materialized_here"] is True
    assert material["actual_review_evidence_complete"] is False
    assert material["disposal_verified"] is False
    assert material["ready_for_purge_disposal_receipt"] is True
    assert material["disposal_receipt_allowed_next"] is True
    assert material["handoff_allowed_before_purge"] is False
    assert tuple(material["implemented_steps"]) == op.P7_R54_OP16_IMPLEMENTED_STEPS
    assert tuple(material["not_yet_implemented_steps"]) == op.P7_R54_OP16_NOT_YET_IMPLEMENTED_STEPS
    assert material["next_required_step"] == op.P7_R54_OP17_STEP_REF
    _assert_body_free_no_promotion(material)


@pytest.mark.parametrize(
    ("review_status", "expected_status"),
    [
        (op.P7_R54_OP10_REVIEW_ABORTED_STATUS_REF, op.P7_R54_OP16_PROTOCOL_ABORTED_STATUS_REF),
        (op.P7_R54_OP10_REVIEW_EXPIRED_STATUS_REF, op.P7_R54_OP16_PROTOCOL_EXPIRED_STATUS_REF),
    ],
)
def test_r54_op16_abort_or_expiration_routes_to_purge_as_inconclusive_direction(
    review_status: str,
    expected_status: str,
) -> None:
    material = op.build_p7_r54_op16_pause_abort_expiration_protocol(
        rating_question_consistency_guard=_op15_ready(),
        session_event_status_ref=review_status,
    )

    assert material["pause_abort_expiration_protocol_status"] == expected_status
    assert material["review_aborted_or_expired"] is True
    assert material["p5_decision_direction_ref"] == "p5_inconclusive_due_to_abort_or_expiration"
    assert material["p5_decision_materialized_here"] is False
    assert material["ready_for_purge_disposal_receipt"] is True
    assert material["next_required_step"] == op.P7_R54_OP17_STEP_REF
    _assert_body_free_no_promotion(material)


def test_r54_op16_pause_blocks_handoff_and_does_not_allow_disposal_receipt_yet() -> None:
    material = op.build_p7_r54_op16_pause_abort_expiration_protocol(
        rating_question_consistency_guard=_op15_ready(),
        session_event_status_ref=op.P7_R54_OP10_REVIEW_PAUSED_STATUS_REF,
    )

    assert material["pause_abort_expiration_protocol_status"] == op.P7_R54_OP16_PROTOCOL_PAUSED_STATUS_REF
    assert material["review_paused_without_handoff"] is True
    assert material["ready_for_purge_disposal_receipt"] is False
    assert material["disposal_receipt_allowed_next"] is False
    assert material["handoff_allowed_before_purge"] is False
    assert material["next_required_step"] == op.P7_R54_OP16_PAUSED_NEXT_REQUIRED_STEP_REF
    _assert_body_free_no_promotion(material)


def test_r54_op17_default_receipt_fails_closed_without_op16_and_removal_receipt() -> None:
    material = op.build_p7_r54_op17_purge_disposal_receipt()

    assert material["schema_version"] == op.P7_R54_OPERATION_PURGE_DISPOSAL_RECEIPT_SCHEMA_VERSION
    assert set(material) == set(op.P7_R54_OPERATION_PURGE_DISPOSAL_RECEIPT_REQUIRED_FIELD_REFS)
    assert material["policy_section"] == op.P7_R54_OP17_STEP_REF
    assert material["purge_disposal_receipt_status"] == op.P7_R54_OP17_DISPOSAL_BLOCKED_STATUS_REF
    assert material["disposal_verified"] is False
    assert material["actual_disposal_receipt_materialized_here"] is False
    assert material["body_free_post_review_summary_allowed_next"] is False
    assert material["next_required_step"] == op.P7_R54_OP17_BLOCKED_NEXT_REQUIRED_STEP_REF
    assert material["open_execution_blocker_ids"]
    _assert_body_free_no_promotion(material)


def test_r54_op17_verified_receipt_records_only_bodyfree_disposal_evidence() -> None:
    material = op.build_p7_r54_op17_purge_disposal_receipt(
        pause_abort_expiration_protocol=_op16_ready(),
        body_removed=True,
        reviewer_notes_removed=True,
        temporary_form_removed=True,
        local_packet_exported=False,
        content_hash_of_body_stored=False,
        disposal_receipt_ref=op.P7_R54_OP17_DISPOSAL_RECEIPT_REF,
    )

    assert set(material) == set(op.P7_R54_OPERATION_PURGE_DISPOSAL_RECEIPT_REQUIRED_FIELD_REFS)
    assert material["purge_disposal_receipt_status"] == op.P7_R54_OP17_DISPOSAL_VERIFIED_STATUS_REF
    assert material["purge_disposal_receipt_ref"] == op.P7_R54_OP17_DISPOSAL_RECEIPT_REF
    assert tuple(material["removal_target_refs"]) == tuple(op.P7_R54_OP17_REMOVAL_TARGET_REFS)
    assert material["body_removed"] is True
    assert material["reviewer_notes_removed"] is True
    assert material["temporary_form_removed"] is True
    assert material["body_removed"] is True and material["reviewer_notes_removed"] is True and material["temporary_form_removed"] is True
    assert material["local_packet_exported"] is False
    assert material["content_hash_of_body_stored"] is False
    assert material["body_full_packet_zip_inclusion_allowed"] is False
    assert material["reviewer_notes_export_allowed"] is False
    assert material["body_full_packet_export_allowed"] is False
    assert material["disposal_verified"] is True
    assert material["actual_disposal_receipt_materialized_here"] is True
    assert material["actual_disposal_run_here"] is False
    assert material["actual_review_evidence_complete"] is False
    assert material["body_free_post_review_summary_allowed_next"] is True
    assert tuple(material["implemented_steps"]) == op.P7_R54_OP17_IMPLEMENTED_STEPS
    assert tuple(material["not_yet_implemented_steps"]) == op.P7_R54_OP17_NOT_YET_IMPLEMENTED_STEPS
    assert material["next_required_step"] == op.P7_R54_OP18_STEP_REF
    _assert_body_free_no_promotion(material)


def test_r54_op17_blocks_when_required_local_target_or_receipt_is_missing() -> None:
    material = op.build_p7_r54_op17_purge_disposal_receipt(
        pause_abort_expiration_protocol=_op16_ready(),
        body_removed=True,
        reviewer_notes_removed=True,
        temporary_form_removed=False,
        disposal_receipt_ref=op.P7_R54_OP17_DISPOSAL_RECEIPT_REF,
    )

    assert material["purge_disposal_receipt_status"] == op.P7_R54_OP17_DISPOSAL_BLOCKED_STATUS_REF
    assert material["temporary_form_removed"] is False
    assert "temporary_form_not_removed" in material["open_execution_blocker_ids"]
    assert material["disposal_verified"] is False
    assert material["actual_disposal_receipt_materialized_here"] is False
    assert material["next_required_step"] == op.P7_R54_OP17_BLOCKED_NEXT_REQUIRED_STEP_REF
    _assert_body_free_no_promotion(material)


def test_r54_op16_op17_bodyfree_aliases_match_primary_builders() -> None:
    op16 = op.build_p7_r54_operation_pause_abort_expiration_protocol_bodyfree(
        rating_question_consistency_guard=_op15_ready(),
    )
    op17 = op.build_p7_r54_operation_purge_disposal_receipt_bodyfree(
        pause_abort_expiration_protocol=op16,
        body_removed=True,
        reviewer_notes_removed=True,
        temporary_form_removed=True,
        disposal_receipt_ref=op.P7_R54_OP17_DISPOSAL_RECEIPT_REF,
    )

    assert op.assert_p7_r54_operation_pause_abort_expiration_protocol_bodyfree_contract(op16) is True
    assert op.assert_p7_r54_operation_purge_disposal_receipt_bodyfree_contract(op17) is True
    assert op16["pause_abort_expiration_protocol_status"] == op.P7_R54_OP16_PROTOCOL_READY_STATUS_REF
    assert op17["purge_disposal_receipt_status"] == op.P7_R54_OP17_DISPOSAL_VERIFIED_STATUS_REF
    _assert_body_free_no_promotion(op16)
    _assert_body_free_no_promotion(op17)


@pytest.mark.parametrize(
    "builder,asserter",
    [
        (op.build_p7_r54_op16_pause_abort_expiration_protocol, op.assert_p7_r54_op16_pause_abort_expiration_protocol_contract),
        (op.build_p7_r54_op17_purge_disposal_receipt, op.assert_p7_r54_op17_purge_disposal_receipt_contract),
    ],
)
def test_r54_op16_op17_contracts_reject_api_db_rn_runtime_mutation_flags(builder, asserter) -> None:
    material = builder()
    for key in ("api_changed", "db_changed", "rn_changed", "runtime_changed", "release_allowed", "p8_start_allowed"):
        broken = deepcopy(material)
        broken[key] = True
        with pytest.raises(ValueError):
            asserter(broken)


@pytest.mark.parametrize(
    ("updates", "expected_blocker"),
    [
        ({"local_packet_exported": True}, "local_packet_exported_during_disposal"),
        ({"content_hash_of_body_stored": True}, "content_hash_of_body_stored_during_disposal"),
    ],
)
def test_r54_op17_blocks_packet_export_or_body_hash_storage(updates: dict[str, object], expected_blocker: str) -> None:
    kwargs = {
        "pause_abort_expiration_protocol": _op16_ready(),
        "body_removed": True,
        "reviewer_notes_removed": True,
        "temporary_form_removed": True,
        "disposal_receipt_ref": op.P7_R54_OP17_DISPOSAL_RECEIPT_REF,
    }
    kwargs.update(updates)
    with pytest.raises(ValueError):
        op.build_p7_r54_op17_purge_disposal_receipt(**kwargs)
    assert expected_blocker
