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
    '"actual_review_evidence_complete": true',
    '"historical_helper_refs_used_as_actual_review_basis": true',
    '"old_helper_refs_allowed_as_actual_review_basis": true',
    '"r55_current_refs_used_as_actual_review_basis": true',
    '"existing_op18_reused_as_actual_summary_basis": true',
    '"existing_op18_reused_as_actual_post_review_summary_basis": true',
    '"existing_op19_reused_as_actual_decision_basis": true',
    '"existing_op19_reused_as_actual_decision_candidate_basis": true',
    '"p5_human_blind_qa_confirmed_final": true',
)


def _assert_ev16_ev17_body_free_no_promotion(
    material: dict[str, object],
    *,
    allow_disposal_receipt: bool = True,
    allow_p5_candidate: bool = False,
) -> None:
    dumped = json.dumps(material, ensure_ascii=False, sort_keys=True).lower()
    for forbidden in FORBIDDEN_DUMP_TOKENS:
        assert forbidden not in dumped
    for forbidden in FORBIDDEN_TRUE_TOKENS:
        assert forbidden not in dumped
    if not allow_disposal_receipt:
        assert '"actual_disposal_receipt_materialized_here": true' not in dumped
        assert '"disposal_verified": true' not in dumped
    if not allow_p5_candidate:
        assert '"p5_human_blind_qa_confirmed_candidate": true' not in dumped


def _chain_from_rows(rows: list[dict[str, object]] | None = None) -> tuple[dict[str, object], dict[str, object], dict[str, object], dict[str, object], dict[str, object], dict[str, object]]:
    _, ev10, ev11, ev12 = prev._ev12_ready(rows)
    ev13 = ev.build_p7_r54_ev13_rating_question_consistency_guard(
        question_need_observation_row_normalization=ev12,
        rating_row_normalization=ev10,
    )
    assert ev.assert_p7_r54_ev13_rating_question_consistency_guard_contract(ev13) is True
    ev14 = ev.build_p7_r54_ev14_pause_abort_expiration_protocol(rating_question_consistency_guard=ev13)
    assert ev.assert_p7_r54_ev14_pause_abort_expiration_protocol_contract(ev14) is True
    ev15 = ev.build_p7_r54_ev15_purge_disposal_receipt(
        pause_abort_expiration_protocol=ev14,
        body_removed=True,
        reviewer_notes_removed=True,
        temporary_form_removed=True,
        disposal_receipt_ref=ev.P7_R54_EV15_DISPOSAL_RECEIPT_REF,
    )
    assert ev.assert_p7_r54_ev15_purge_disposal_receipt_contract(ev15) is True
    return ev10, ev11, ev12, ev13, ev14, ev15


def _ev16_ready(rows: list[dict[str, object]] | None = None) -> tuple[dict[str, object], dict[str, object], dict[str, object], dict[str, object], dict[str, object], dict[str, object]]:
    ev10, ev11, ev12, ev13, _, ev15 = _chain_from_rows(rows)
    material = ev.build_p7_r54_ev16_bodyfree_post_review_summary(
        purge_disposal_receipt=ev15,
        rating_question_consistency_guard=ev13,
        question_need_observation_row_normalization=ev12,
        blocker_ingestion=ev11,
        rating_row_normalization=ev10,
    )
    assert ev.assert_p7_r54_ev16_bodyfree_post_review_summary_contract(material) is True
    return ev10, ev11, ev12, ev13, ev15, material


def _ev17_ready(rows: list[dict[str, object]] | None = None, *, p4_current_only_surface_issue_refs: list[str] | None = None) -> tuple[dict[str, object], dict[str, object]]:
    *_, ev16 = _ev16_ready(rows)
    material = ev.build_p7_r54_ev17_p5_decision_candidate_separation(
        bodyfree_post_review_summary=ev16,
        p4_current_only_surface_issue_refs=p4_current_only_surface_issue_refs,
    )
    assert ev.assert_p7_r54_ev17_p5_decision_candidate_separation_contract(material) is True
    return ev16, material


def _rows_with_first_row(**updates: object) -> list[dict[str, object]]:
    rows = prev._selection_rows()
    rows[0] = dict(rows[0])
    rows[0].update(updates)
    return rows


def test_r54_ev16_ready_builds_bodyfree_summary_counts_after_disposal() -> None:
    ev10, ev11, ev12, ev13, ev15, material = _ev16_ready()

    assert material["schema_version"] == ev.P7_R54_EV16_BODYFREE_POST_REVIEW_SUMMARY_SCHEMA_VERSION
    assert set(material) == set(ev.P7_R54_EV16_REQUIRED_FIELD_REFS)
    assert material["policy_section"] == ev.P7_R54_EV16_STEP_REF
    assert material["operation_step_ref"] == ev.P7_R54_EV16_STEP_REF
    assert material["bodyfree_post_review_summary_status"] == ev.P7_R54_EV16_SUMMARY_READY_STATUS_REF
    assert material["bodyfree_post_review_summary_ref"] == ev.P7_R54_EV16_SUMMARY_REF
    assert material["bodyfree_post_review_summary_policy_ref"] == ev.P7_R54_EV16_SUMMARY_POLICY_REF
    assert material["bodyfree_post_review_summary_reason_refs"] == [ev.P7_R54_EV16_READY_REASON_REF]
    assert material["ev15_purge_disposal_receipt_status"] == ev.P7_R54_EV15_DISPOSAL_VERIFIED_STATUS_REF
    assert material["ev13_consistency_guard_status"] == ev.P7_R54_EV13_CONSISTENCY_GUARD_READY_STATUS_REF
    assert material["ev12_question_observation_normalization_status"] == ev.P7_R54_EV12_QUESTION_OBSERVATION_NORMALIZATION_READY_STATUS_REF
    assert material["ev11_blocker_ingestion_status"] == ev.P7_R54_EV11_BLOCKER_INGESTION_READY_STATUS_REF
    assert material["ev10_rating_row_normalization_status"] == ev.P7_R54_EV10_RATING_NORMALIZATION_READY_STATUS_REF
    assert material["operation_current_refs"] == ev.P7_R54_EV_OPERATION_CURRENT_REFS_20260626
    assert material["existing_op18_operation_current_refs"] == r54op.P7_R54_OPERATION_CURRENT_REFS
    assert material["existing_op18_current_refs_are_historical_here"] is True
    assert material["existing_op18_reused_as_actual_summary_basis"] is False
    assert material["existing_op18_reused_as_actual_post_review_summary_basis"] is False
    assert material["existing_op18_structural_contract_reused"] is True
    assert material["required_case_count"] == 24
    assert material["reviewed_case_count"] == 24
    assert material["rating_row_count"] == 24
    assert material["question_observation_row_count"] == 24
    assert material["verdict_counts"] == ev10["verdict_counts"]
    assert material["axis_score_averages"] == ev10["axis_score_averages"]
    assert material["readfeel_blocker_counts"] == ev11["readfeel_blocker_counts"]
    assert material["primary_class_counts"] == ev12["question_need_primary_class_counts"]
    assert material["consistency_issue_count"] == ev13["consistency_issue_count"]
    assert material["disposal_verified"] is True
    assert material["body_removed"] is True
    assert material["reviewer_notes_removed"] is True
    assert material["temporary_form_removed"] is True
    assert material["all_required_review_counts_present"] is True
    assert material["all_required_summary_inputs_ready"] is True
    assert material["no_body_leak_validation_passed"] is True
    assert material["no_question_text_validation_passed"] is True
    assert material["no_touch_validation_passed"] is True
    assert material["p5_decision_candidate_separation_allowed_next"] is True
    assert material["actual_review_evidence_complete"] is False
    assert material["next_required_step"] == ev.P7_R54_EV17_STEP_REF
    assert tuple(material["implemented_steps"]) == ev.P7_R54_EV16_IMPLEMENTED_STEPS
    assert tuple(material["not_yet_implemented_steps"]) == ev.P7_R54_EV16_NOT_YET_IMPLEMENTED_STEPS
    _assert_ev16_ev17_body_free_no_promotion(material)


def test_r54_ev16_blocks_when_disposal_receipt_is_not_verified() -> None:
    ev10, ev11, ev12, ev13, ev14, _ = _chain_from_rows()
    ev15 = ev.build_p7_r54_ev15_purge_disposal_receipt(
        pause_abort_expiration_protocol=ev14,
        body_removed=True,
        reviewer_notes_removed=False,
        temporary_form_removed=True,
        disposal_receipt_ref=ev.P7_R54_EV15_DISPOSAL_RECEIPT_REF,
    )
    assert ev.assert_p7_r54_ev15_purge_disposal_receipt_contract(ev15) is True

    material = ev.build_p7_r54_ev16_bodyfree_post_review_summary(
        purge_disposal_receipt=ev15,
        rating_question_consistency_guard=ev13,
        question_need_observation_row_normalization=ev12,
        blocker_ingestion=ev11,
        rating_row_normalization=ev10,
    )

    assert material["bodyfree_post_review_summary_status"] == ev.P7_R54_EV16_SUMMARY_BLOCKED_STATUS_REF
    assert material["p5_decision_candidate_separation_allowed_next"] is False
    assert "ev15_disposal_receipt_not_verified_for_bodyfree_summary" in material["open_execution_blocker_ids"]
    assert material["disposal_verified"] is False
    assert material["next_required_step"] == ev.P7_R54_EV16_BLOCKED_NEXT_REQUIRED_STEP_REF
    _assert_ev16_ev17_body_free_no_promotion(material, allow_disposal_receipt=False)


def test_r54_ev17_separates_p5_confirmed_candidate_only_without_starting_p6_p8_or_release() -> None:
    ev16, material = _ev17_ready()

    assert material["schema_version"] == ev.P7_R54_EV17_P5_DECISION_CANDIDATE_SEPARATION_SCHEMA_VERSION
    assert set(material) == set(ev.P7_R54_EV17_REQUIRED_FIELD_REFS)
    assert material["policy_section"] == ev.P7_R54_EV17_STEP_REF
    assert material["operation_step_ref"] == ev.P7_R54_EV17_STEP_REF
    assert material["decision_candidate_separation_status"] == ev.P7_R54_EV17_DECISION_SEPARATION_READY_STATUS_REF
    assert material["decision_candidate_separation_ref"] == ev.P7_R54_EV17_DECISION_SEPARATION_REF
    assert material["decision_candidate_separation_policy_ref"] == ev.P7_R54_EV17_DECISION_SEPARATION_POLICY_REF
    assert material["p5_decision_candidate_ref"] == ev.P7_R54_EV17_P5_CONFIRMED_CANDIDATE_REF
    assert material["p5_decision_candidate_materialized_here"] is True
    assert material["p5_confirmed_candidate_conditions_met"] is True
    assert material["p5_human_blind_qa_confirmed_candidate"] is True
    assert material["p5_human_blind_qa_confirmed_final"] is False
    assert material["p6_limited_human_readfeel_start_allowed"] is False
    assert material["p8_start_allowed"] is False
    assert material["release_allowed"] is False
    assert material["p5_final_confirmation_blocked_here"] is True
    assert material["p6_start_blocked_here"] is True
    assert material["p8_start_blocked_here"] is True
    assert material["release_blocked_here"] is True
    assert material["actual_review_evidence_complete"] is False
    assert material["next_required_step"] == ev.P7_R54_EV18_NEXT_REQUIRED_STEP_REF
    assert material["existing_op19_current_refs_are_historical_here"] is True
    assert material["existing_op19_reused_as_actual_decision_basis"] is False
    assert material["existing_op19_reused_as_actual_decision_candidate_basis"] is False
    assert material["verdict_counts"] == ev16["verdict_counts"]
    assert tuple(material["implemented_steps"]) == ev.P7_R54_EV17_IMPLEMENTED_STEPS
    assert tuple(material["not_yet_implemented_steps"]) == ev.P7_R54_EV17_NOT_YET_IMPLEMENTED_STEPS
    _assert_ev16_ev17_body_free_no_promotion(material, allow_p5_candidate=True)


@pytest.mark.parametrize(
    "updates,expected_reason",
    [
        ({"verdict": "YELLOW"}, "yellow_verdict_present"),
        ({"verdict": "REPAIR_REQUIRED", "readfeel_blocker_ids": ["p5_history_connection_too_generic"], "question_need_primary_class": "question_may_reduce_overread_risk"}, "repair_required_verdict_present"),
        ({"verdict": "RED", "readfeel_blocker_ids": ["p5_history_creepy_or_surveillance_feeling"], "question_need_primary_class": "question_may_reduce_overread_risk"}, "red_verdict_present"),
        ({"question_need_primary_class": "not_question_p5_surface_repair_required", "one_question_fit_ref": "repair_required_not_question", "repair_required_refs": ["p5_surface_repair_required"], "verdict": "YELLOW"}, "not_question_repair_required_row_present"),
    ],
)
def test_r54_ev17_routes_p5_readfeel_or_surface_weakness_to_p5_repair_return(updates: dict[str, object], expected_reason: str) -> None:
    rows = _rows_with_first_row(**updates)
    _, material = _ev17_ready(rows)

    assert material["p5_decision_candidate_ref"] == ev.P7_R54_EV17_P5_REPAIR_RETURN_REF
    assert material["p5_repair_return_required"] is True
    assert material["p5_human_blind_qa_confirmed_candidate"] is False
    assert material["next_required_step"] == ev.P7_R54_EV17_P5_REPAIR_NEXT_REQUIRED_STEP_REF
    assert expected_reason in material["p5_decision_repair_reason_refs"]
    assert material["p8_start_allowed"] is False
    _assert_ev16_ev17_body_free_no_promotion(material)


def test_r54_ev17_routes_below_target_axes_to_p5_repair_return() -> None:
    rows = prev._selection_rows()
    for index, row in enumerate(rows):
        rows[index] = dict(row)
        rows[index]["axis_scores"] = {axis: 0.25 for axis in ev.P7_R54_EV08_RATING_AXIS_REFS}
        rows[index]["verdict"] = "YELLOW"
    _, material = _ev17_ready(rows)

    assert material["p5_decision_candidate_ref"] == ev.P7_R54_EV17_P5_REPAIR_RETURN_REF
    assert material["p5_repair_return_required"] is True
    assert "axis_below_target:history_connection_naturalness" in material["p5_decision_repair_reason_refs"]
    assert material["next_required_step"] == ev.P7_R54_EV17_P5_REPAIR_NEXT_REQUIRED_STEP_REF
    _assert_ev16_ev17_body_free_no_promotion(material)


def test_r54_ev17_routes_current_only_surface_issue_to_p4_r12() -> None:
    _, material = _ev17_ready(p4_current_only_surface_issue_refs=["current_surface_generic_family_hij"])

    assert material["p5_decision_candidate_ref"] == ev.P7_R54_EV17_P4_R12_TARGETED_REPAIR_REF
    assert material["p4_r12_targeted_current_only_surface_repair_required"] is True
    assert material["p4_current_only_surface_issue_refs"] == ["current_surface_generic_family_hij"]
    assert material["p5_human_blind_qa_confirmed_candidate"] is False
    assert material["next_required_step"] == ev.P7_R54_EV17_P4_R12_REPAIR_NEXT_REQUIRED_STEP_REF
    _assert_ev16_ev17_body_free_no_promotion(material)


def test_r54_ev17_blocks_when_ev16_summary_is_not_ready() -> None:
    ev16 = ev.build_p7_r54_ev16_bodyfree_post_review_summary()
    assert ev16["bodyfree_post_review_summary_status"] == ev.P7_R54_EV16_SUMMARY_BLOCKED_STATUS_REF

    material = ev.build_p7_r54_ev17_p5_decision_candidate_separation(bodyfree_post_review_summary=ev16)

    assert material["decision_candidate_separation_status"] == ev.P7_R54_EV17_DECISION_SEPARATION_BLOCKED_STATUS_REF
    assert material["p5_decision_candidate_ref"] == ev.P7_R54_EV17_INCONCLUSIVE_REF
    assert material["p5_decision_candidate_materialized_here"] is False
    assert material["p5_decision_inconclusive_reason_refs"] == ["ev16_bodyfree_post_review_summary_not_ready"]
    assert material["next_required_step"] == ev.P7_R54_EV17_BLOCKED_NEXT_REQUIRED_STEP_REF
    assert material["p8_start_allowed"] is False
    _assert_ev16_ev17_body_free_no_promotion(material, allow_disposal_receipt=False)


@pytest.mark.parametrize(
    "key,value",
    [
        ("operation_current_refs_used_as_actual_review_basis", False),
        ("existing_op18_current_refs_are_historical_here", False),
        ("existing_op18_reused_as_actual_summary_basis", True),
        ("existing_op18_reused_as_actual_post_review_summary_basis", True),
        ("existing_op18_structural_contract_reused", False),
        ("required_case_count", 23),
        ("bodyfree_post_review_summary_status", ev.P7_R54_EV16_SUMMARY_BLOCKED_STATUS_REF),
        ("reviewed_case_count", 23),
        ("rating_row_count", 23),
        ("question_observation_row_count", 23),
        ("all_required_review_counts_present", False),
        ("all_required_summary_inputs_ready", False),
        ("no_body_leak_validation_passed", False),
        ("no_question_text_validation_passed", False),
        ("no_touch_validation_passed", False),
        ("p5_decision_candidate_separation_allowed_next", False),
        ("local_packet_exported", True),
        ("content_hash_of_body_stored", True),
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
def test_r54_ev16_rejects_summary_boundary_mutations(key: str, value: object) -> None:
    *_, material = _ev16_ready()
    material[key] = value
    with pytest.raises(ValueError):
        ev.assert_p7_r54_ev16_bodyfree_post_review_summary_contract(material)


@pytest.mark.parametrize(
    "key,value",
    [
        ("operation_current_refs_used_as_actual_review_basis", False),
        ("existing_op19_current_refs_are_historical_here", False),
        ("existing_op19_reused_as_actual_decision_basis", True),
        ("existing_op19_reused_as_actual_decision_candidate_basis", True),
        ("existing_op19_structural_contract_reused", False),
        ("required_case_count", 23),
        ("decision_candidate_separation_status", ev.P7_R54_EV17_DECISION_SEPARATION_BLOCKED_STATUS_REF),
        ("p5_decision_candidate_ref", "unknown_decision_candidate"),
        ("p5_decision_candidate_materialized_here", False),
        ("p5_human_blind_qa_confirmed_final", True),
        ("p6_limited_human_readfeel_start_allowed", True),
        ("p8_start_allowed", True),
        ("release_allowed", True),
        ("p5_final_confirmation_blocked_here", False),
        ("p6_start_blocked_here", False),
        ("p8_start_blocked_here", False),
        ("release_blocked_here", False),
        ("local_packet_exported", True),
        ("content_hash_of_body_stored", True),
        ("actual_review_evidence_complete", True),
        ("api_changed", True),
        ("db_changed", True),
        ("rn_changed", True),
        ("runtime_changed", True),
        ("question_trigger_logic_implemented", True),
        ("question_text_included", True),
        ("draft_question_text_included", True),
        ("local_path_included", True),
    ],
)
def test_r54_ev17_rejects_decision_boundary_mutations(key: str, value: object) -> None:
    _, material = _ev17_ready()
    material[key] = value
    with pytest.raises(ValueError):
        ev.assert_p7_r54_ev17_p5_decision_candidate_separation_contract(material)


def test_r54_ev16_ev17_reject_body_leak_and_old_current_refs() -> None:
    *_, ev16 = _ev16_ready()
    ev16["operation_current_refs"] = dict(r54op.P7_R54_OPERATION_CURRENT_REFS)
    with pytest.raises(ValueError):
        ev.assert_p7_r54_ev16_bodyfree_post_review_summary_contract(ev16)

    *_, ev16 = _ev16_ready()
    ev16["question_text"] = "question text must not be present"
    with pytest.raises(ValueError):
        ev.assert_p7_r54_ev16_bodyfree_post_review_summary_contract(ev16)

    _, ev17 = _ev17_ready()
    ev17["local_absolute_path"] = "/tmp/body-full-packet"
    with pytest.raises(ValueError):
        ev.assert_p7_r54_ev17_p5_decision_candidate_separation_contract(ev17)
