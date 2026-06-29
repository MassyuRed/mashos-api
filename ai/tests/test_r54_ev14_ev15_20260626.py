# -*- coding: utf-8 -*-
from __future__ import annotations

import json
from copy import deepcopy

import pytest

import emlis_ai_p7_r54_actual_local_review_operation_reentry_20260625 as r54op
import emlis_ai_p7_r54_actual_review_execution_evidence_materialization_20260626 as ev
import test_r54_ev12_ev13_20260626 as prev


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
    '"question_text": "',
    '"draft_question_text": "',
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
    '"api_changed": true',
    '"db_changed": true',
    '"rn_changed": true',
    '"runtime_changed": true',
    '"api_route_changed": true',
    '"db_schema_changed": true',
    '"rn_visible_contract_changed": true',
    '"public_response_top_level_key_added": true',
    '"release_allowed": true',
    '"p7_complete": true',
    '"p8_start_allowed": true',
    '"p6_limited_human_readfeel_start_allowed": true',
    '"question_trigger_logic_implemented": true',
    '"p8_question_implementation_spec_finalized_here": true',
    '"actual_human_review_run_here": true',
    '"actual_manual_review_run_here": true',
    '"body_full_packet_generated_here": true',
    '"historical_helper_refs_used_as_actual_review_basis": true',
    '"old_helper_refs_allowed_as_actual_review_basis": true',
    '"r55_current_refs_used_as_actual_review_basis": true',
    '"actual_review_evidence_complete": true',
    '"existing_op16_reused_as_actual_pause_abort_basis": true',
    '"existing_op16_reused_as_actual_protocol_basis": true',
    '"existing_op17_reused_as_actual_disposal_basis": true',
)


def _assert_ev14_ev15_body_free_no_promotion(
    material: dict[str, object],
    *,
    allow_rating_rows: bool = True,
    allow_blocker_rows: bool = True,
    allow_question_rows: bool = True,
    allow_disposal_receipt: bool = False,
) -> None:
    dumped = json.dumps(material, ensure_ascii=False, sort_keys=True).lower()
    for forbidden in FORBIDDEN_DUMP_TOKENS:
        assert forbidden not in dumped
    for forbidden in FORBIDDEN_TRUE_TOKENS:
        assert forbidden not in dumped
    if not allow_rating_rows:
        assert '"actual_rating_rows_materialized_here": true' not in dumped
    if not allow_blocker_rows:
        assert '"actual_blocker_rows_materialized_here": true' not in dumped
    if not allow_question_rows:
        assert '"actual_question_need_observation_rows_materialized_here": true' not in dumped
    if not allow_disposal_receipt:
        assert '"actual_disposal_receipt_materialized_here": true' not in dumped
        assert '"disposal_verified": true' not in dumped


def _ev13_ready() -> dict[str, object]:
    _, ev10, _, ev12 = prev._ev12_ready()
    material = ev.build_p7_r54_ev13_rating_question_consistency_guard(
        question_need_observation_row_normalization=ev12,
        rating_row_normalization=ev10,
    )
    assert ev.assert_p7_r54_ev13_rating_question_consistency_guard_contract(material) is True
    assert material["rating_question_consistency_guard_status"] == ev.P7_R54_EV13_CONSISTENCY_GUARD_READY_STATUS_REF
    return material


def _ev13_blocked_by_not_question_repair() -> dict[str, object]:
    rows = prev._selection_rows()
    rows[0] = dict(rows[0])
    rows[0]["question_need_primary_class"] = "not_question_p5_surface_repair_required"
    rows[0]["one_question_fit_ref"] = "repair_required_not_question"
    _, ev10, _, ev12 = prev._ev12_ready(rows)
    material = ev.build_p7_r54_ev13_rating_question_consistency_guard(
        question_need_observation_row_normalization=ev12,
        rating_row_normalization=ev10,
    )
    assert ev.assert_p7_r54_ev13_rating_question_consistency_guard_contract(material) is True
    assert material["rating_question_consistency_guard_status"] == ev.P7_R54_EV13_CONSISTENCY_GUARD_BLOCKED_STATUS_REF
    return material


def _ev14_ready() -> dict[str, object]:
    material = ev.build_p7_r54_ev14_pause_abort_expiration_protocol(
        rating_question_consistency_guard=_ev13_ready(),
    )
    assert ev.assert_p7_r54_ev14_pause_abort_expiration_protocol_contract(material) is True
    assert material["pause_abort_expiration_protocol_status"] == ev.P7_R54_EV14_PROTOCOL_READY_STATUS_REF
    return material


def test_r54_ev14_ready_protocol_routes_to_ev15_bodyfree() -> None:
    material = _ev14_ready()

    assert material["schema_version"] == ev.P7_R54_EV14_PAUSE_ABORT_EXPIRATION_PROTOCOL_SCHEMA_VERSION
    assert set(material) == set(ev.P7_R54_EV14_REQUIRED_FIELD_REFS)
    assert material["policy_section"] == ev.P7_R54_EV14_STEP_REF
    assert material["operation_step_ref"] == ev.P7_R54_EV14_STEP_REF
    assert material["ev13_ready_for_pause_abort_expiration_protocol"] is True
    assert material["existing_op16_current_refs_are_historical_here"] is True
    assert material["existing_op16_reused_as_actual_protocol_basis"] is False
    assert material["existing_op16_structural_contract_reused"] is True
    assert material["operation_current_refs"] == ev.P7_R54_EV_OPERATION_CURRENT_REFS_20260626
    assert material["existing_op16_operation_current_refs"] == r54op.P7_R54_OPERATION_CURRENT_REFS
    assert material["rating_row_count"] == 24
    assert material["question_observation_row_count"] == 24
    assert material["purge_trigger_refs"] == list(ev.P7_R54_EV14_PURGE_TRIGGER_REFS)
    assert "question_observation_rows_finalized" in material["purge_trigger_refs"]
    assert tuple(material["required_local_delete_target_refs"]) == ev.P7_R54_EV14_REQUIRED_LOCAL_DELETE_TARGET_REFS
    assert material["ready_for_purge_disposal_receipt"] is True
    assert material["purge_disposal_receipt_allowed_next"] is True
    assert material["disposal_receipt_allowed_next"] is True
    assert material["disposal_verified"] is False
    assert material["actual_disposal_receipt_materialized_here"] is False
    assert material["next_required_step"] == ev.P7_R54_EV15_STEP_REF
    assert tuple(material["implemented_steps"]) == ev.P7_R54_EV14_IMPLEMENTED_STEPS
    assert tuple(material["not_yet_implemented_steps"]) == ev.P7_R54_EV14_NOT_YET_IMPLEMENTED_STEPS
    _assert_ev14_ev15_body_free_no_promotion(material)


@pytest.mark.parametrize(
    "status_ref,expected_status,expected_direction",
    [
        (r54op.P7_R54_OP10_REVIEW_PAUSED_STATUS_REF, ev.P7_R54_EV14_PROTOCOL_PAUSED_STATUS_REF, "pause_no_handoff_local_only"),
        (r54op.P7_R54_OP10_REVIEW_ABORTED_STATUS_REF, ev.P7_R54_EV14_PROTOCOL_ABORTED_STATUS_REF, "r54_operation_inconclusive_required_later"),
        (r54op.P7_R54_OP10_REVIEW_EXPIRED_STATUS_REF, ev.P7_R54_EV14_PROTOCOL_EXPIRED_STATUS_REF, "r54_operation_inconclusive_required_later"),
        ("rating_incomplete_purge_required", ev.P7_R54_EV14_PROTOCOL_RATING_INCOMPLETE_STATUS_REF, "r54_operation_inconclusive_required_later"),
    ],
)
def test_r54_ev14_pause_abort_expire_statuses_do_not_create_handoff(status_ref: str, expected_status: str, expected_direction: str) -> None:
    material = ev.build_p7_r54_ev14_pause_abort_expiration_protocol(
        rating_question_consistency_guard=_ev13_ready(),
        review_operation_status_ref=status_ref,
    )

    assert material["pause_abort_expiration_protocol_status"] == expected_status
    assert material["p5_decision_direction_ref"] == expected_direction
    assert material["p5_decision_materialized_here"] is False
    assert material["p5_inconclusive_direction_only_not_decision_materialized"] is True
    assert material["actual_review_evidence_complete"] is False
    assert material["p6_p8_release_promotion_blocked_here"] is True
    if expected_status == ev.P7_R54_EV14_PROTOCOL_PAUSED_STATUS_REF:
        assert material["review_paused_without_handoff"] is True
        assert material["ready_for_purge_disposal_receipt"] is False
        assert material["next_required_step"] == ev.P7_R54_EV14_PAUSED_NEXT_REQUIRED_STEP_REF
    else:
        assert material["ready_for_purge_disposal_receipt"] is True
        assert material["next_required_step"] == ev.P7_R54_EV15_STEP_REF
    _assert_ev14_ev15_body_free_no_promotion(material)


def test_r54_ev14_blocks_when_ev13_consistency_guard_is_blocked() -> None:
    material = ev.build_p7_r54_ev14_pause_abort_expiration_protocol(
        rating_question_consistency_guard=_ev13_blocked_by_not_question_repair(),
    )

    assert material["pause_abort_expiration_protocol_status"] == ev.P7_R54_EV14_PROTOCOL_BLOCKED_STATUS_REF
    assert material["ev13_ready_for_pause_abort_expiration_protocol"] is False
    assert material["ready_for_purge_disposal_receipt"] is False
    assert material["purge_disposal_receipt_allowed_next"] is False
    assert material["next_required_step"] == ev.P7_R54_EV14_BLOCKED_NEXT_REQUIRED_STEP_REF
    assert "ev13_consistency_guard_not_ready_for_pause_abort_expiration_protocol" in material["open_execution_blocker_ids"]
    assert material["actual_disposal_receipt_materialized_here"] is False
    _assert_ev14_ev15_body_free_no_promotion(material)


def test_r54_ev15_ready_materializes_bodyfree_disposal_receipt_only() -> None:
    ev14 = _ev14_ready()
    material = ev.build_p7_r54_ev15_purge_disposal_receipt(
        pause_abort_expiration_protocol=ev14,
        body_removed=True,
        reviewer_notes_removed=True,
        temporary_form_removed=True,
        disposal_receipt_ref=ev.P7_R54_EV15_DISPOSAL_RECEIPT_REF,
    )

    assert material["schema_version"] == ev.P7_R54_EV15_PURGE_DISPOSAL_RECEIPT_SCHEMA_VERSION
    assert set(material) == set(ev.P7_R54_EV15_REQUIRED_FIELD_REFS)
    assert material["policy_section"] == ev.P7_R54_EV15_STEP_REF
    assert material["operation_step_ref"] == ev.P7_R54_EV15_STEP_REF
    assert material["purge_disposal_receipt_status"] == ev.P7_R54_EV15_DISPOSAL_VERIFIED_STATUS_REF
    assert material["purge_disposal_receipt_ref"] == ev.P7_R54_EV15_DISPOSAL_RECEIPT_REF
    assert material["existing_op17_current_refs_are_historical_here"] is True
    assert material["existing_op17_reused_as_actual_disposal_basis"] is False
    assert material["existing_op17_structural_contract_reused"] is True
    assert material["body_removed"] is True
    assert material["reviewer_notes_removed"] is True
    assert material["temporary_form_removed"] is True
    assert material["all_required_local_targets_removed"] is True
    assert material["local_packet_exported"] is False
    assert material["content_hash_of_body_stored"] is False
    assert material["actual_disposal_run_here"] is False
    assert material["disposal_verified"] is True
    assert material["actual_disposal_receipt_materialized_here"] is True
    assert material["actual_review_evidence_complete"] is False
    assert material["body_free_post_review_summary_allowed_next"] is True
    assert material["next_required_step"] == ev.P7_R54_EV16_NEXT_REQUIRED_STEP_REF
    assert tuple(material["implemented_steps"]) == ev.P7_R54_EV15_IMPLEMENTED_STEPS
    assert tuple(material["not_yet_implemented_steps"]) == ev.P7_R54_EV15_NOT_YET_IMPLEMENTED_STEPS
    _assert_ev14_ev15_body_free_no_promotion(material, allow_disposal_receipt=True)


def test_r54_ev15_blocks_until_all_local_disposal_refs_are_verified() -> None:
    material = ev.build_p7_r54_ev15_purge_disposal_receipt(
        pause_abort_expiration_protocol=_ev14_ready(),
        body_removed=True,
        reviewer_notes_removed=False,
        temporary_form_removed=True,
        disposal_receipt_ref=ev.P7_R54_EV15_DISPOSAL_RECEIPT_REF,
    )

    assert material["purge_disposal_receipt_status"] == ev.P7_R54_EV15_DISPOSAL_BLOCKED_STATUS_REF
    assert material["disposal_verified"] is False
    assert material["actual_disposal_receipt_materialized_here"] is False
    assert "reviewer_notes_not_removed" in material["open_execution_blocker_ids"]
    assert material["body_free_post_review_summary_allowed_next"] is False
    assert material["next_required_step"] == ev.P7_R54_EV15_BLOCKED_NEXT_REQUIRED_STEP_REF
    _assert_ev14_ev15_body_free_no_promotion(material)


def test_r54_ev15_requires_explicit_bodyfree_receipt_ref() -> None:
    material = ev.build_p7_r54_ev15_purge_disposal_receipt(
        pause_abort_expiration_protocol=_ev14_ready(),
        body_removed=True,
        reviewer_notes_removed=True,
        temporary_form_removed=True,
    )

    assert material["purge_disposal_receipt_status"] == ev.P7_R54_EV15_DISPOSAL_BLOCKED_STATUS_REF
    assert "bodyfree_disposal_receipt_ref_missing_or_unexpected" in material["open_execution_blocker_ids"]
    assert material["disposal_verified"] is False
    assert material["actual_disposal_receipt_materialized_here"] is False
    _assert_ev14_ev15_body_free_no_promotion(material)


@pytest.mark.parametrize(
    "key,value",
    [
        ("operation_current_refs_used_as_actual_review_basis", False),
        ("existing_op16_current_refs_are_historical_here", False),
        ("existing_op16_reused_as_actual_protocol_basis", True),
        ("existing_op16_structural_contract_reused", False),
        ("required_case_count", 23),
        ("pause_abort_expiration_protocol_status", ev.P7_R54_EV14_PROTOCOL_BLOCKED_STATUS_REF),
        ("ready_for_purge_disposal_receipt", False),
        ("purge_disposal_receipt_allowed_next", False),
        ("handoff_allowed_before_purge", True),
        ("r52_reintake_handoff_allowed_before_purge", True),
        ("p5_decision_materialized_here", True),
        ("actual_review_evidence_complete", True),
        ("disposal_verified", True),
        ("actual_disposal_receipt_materialized_here", True),
        ("human_review_completion_claim_blocked_here", False),
        ("actual_human_review_completion_claim_blocked_here", False),
        ("p6_p8_release_promotion_blocked_here", False),
        ("api_changed", True),
        ("db_changed", True),
        ("rn_changed", True),
        ("runtime_changed", True),
        ("question_trigger_logic_implemented", True),
        ("p8_start_allowed", True),
        ("release_allowed", True),
        ("question_text_included", True),
        ("draft_question_text_included", True),
        ("local_path_included", True),
    ],
)
def test_r54_ev14_rejects_pause_abort_boundary_mutations(key: str, value: object) -> None:
    material = _ev14_ready()
    material[key] = value
    with pytest.raises(ValueError):
        ev.assert_p7_r54_ev14_pause_abort_expiration_protocol_contract(material)


@pytest.mark.parametrize(
    "key,value",
    [
        ("operation_current_refs_used_as_actual_review_basis", False),
        ("existing_op17_current_refs_are_historical_here", False),
        ("existing_op17_reused_as_actual_disposal_basis", True),
        ("existing_op17_structural_contract_reused", False),
        ("required_case_count", 23),
        ("purge_disposal_receipt_status", ev.P7_R54_EV15_DISPOSAL_BLOCKED_STATUS_REF),
        ("body_removed", False),
        ("reviewer_notes_removed", False),
        ("temporary_form_removed", False),
        ("all_required_local_targets_removed", False),
        ("local_packet_exported", True),
        ("content_hash_of_body_stored", True),
        ("body_full_packet_zip_inclusion_allowed", True),
        ("reviewer_notes_export_allowed", True),
        ("body_full_packet_export_allowed", True),
        ("actual_disposal_run_here", True),
        ("actual_review_evidence_complete", True),
        ("human_review_completion_claim_blocked_here", False),
        ("actual_human_review_completion_claim_blocked_here", False),
        ("p6_p8_release_promotion_blocked_here", False),
        ("api_changed", True),
        ("db_changed", True),
        ("rn_changed", True),
        ("runtime_changed", True),
        ("question_trigger_logic_implemented", True),
        ("p8_start_allowed", True),
        ("release_allowed", True),
        ("question_text_included", True),
        ("draft_question_text_included", True),
        ("local_path_included", True),
    ],
)
def test_r54_ev15_rejects_disposal_receipt_boundary_mutations(key: str, value: object) -> None:
    material = ev.build_p7_r54_ev15_purge_disposal_receipt(
        pause_abort_expiration_protocol=_ev14_ready(),
        body_removed=True,
        reviewer_notes_removed=True,
        temporary_form_removed=True,
        disposal_receipt_ref=ev.P7_R54_EV15_DISPOSAL_RECEIPT_REF,
    )
    material[key] = value
    with pytest.raises(ValueError):
        ev.assert_p7_r54_ev15_purge_disposal_receipt_contract(material)


def test_r54_ev14_ev15_reject_body_leak_and_old_current_refs() -> None:
    ev14 = _ev14_ready()
    ev14["operation_current_refs"] = dict(r54op.P7_R54_OPERATION_CURRENT_REFS)
    with pytest.raises(ValueError):
        ev.assert_p7_r54_ev14_pause_abort_expiration_protocol_contract(ev14)

    ev14 = _ev14_ready()
    ev14["question_text"] = "question text must not be present"
    with pytest.raises(ValueError):
        ev.assert_p7_r54_ev14_pause_abort_expiration_protocol_contract(ev14)

    ev15 = ev.build_p7_r54_ev15_purge_disposal_receipt(
        pause_abort_expiration_protocol=_ev14_ready(),
        body_removed=True,
        reviewer_notes_removed=True,
        temporary_form_removed=True,
        disposal_receipt_ref=ev.P7_R54_EV15_DISPOSAL_RECEIPT_REF,
    )
    ev15["local_absolute_path"] = "/tmp/body-full-packet"
    with pytest.raises(ValueError):
        ev.assert_p7_r54_ev15_purge_disposal_receipt_contract(ev15)
