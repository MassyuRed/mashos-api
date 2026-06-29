"""R54-OP-18/OP-19 actual local-only review operation re-entry tests.

These tests keep OP18/OP19 as body-free operation-layer materialization:
OP18 summarizes already-sanitized review evidence as counts only, and OP19
separates the P5 decision candidate without final-confirming P5 or starting
P6/P8/release.
"""

from __future__ import annotations

import emlis_ai_p7_r54_actual_local_review_operation_reentry_20260625 as op

from test_emlis_ai_p7_r54_actual_local_review_operation_reentry_op14_op15_20260625 import (  # noqa: E501
    _op12_ready,
    _op13_ready,
    _op14_ready,
)
from test_emlis_ai_p7_r54_actual_local_review_operation_reentry_op16_op17_20260625 import (  # noqa: E501
    _op15_ready,
    _op16_ready,
)


def _op17_ready() -> dict[str, object]:
    return op.build_p7_r54_op17_purge_disposal_receipt(
        pause_abort_expiration_protocol=_op16_ready(),
        disposal_receipt_ref=op.P7_R54_OP17_DISPOSAL_RECEIPT_REF,
        body_removed=True,
        reviewer_notes_removed=True,
        temporary_form_removed=True,
        local_packet_exported=False,
        content_hash_of_body_stored=False,
    )


def _op18_ready() -> dict[str, object]:
    return op.build_p7_r54_op18_bodyfree_post_review_summary(
        purge_disposal_receipt=_op17_ready(),
        rating_row_normalization=_op12_ready(),
        blocker_ingestion=_op13_ready(),
        question_need_observation_normalization=_op14_ready(),
        rating_question_consistency_guard=_op15_ready(),
    )


def test_op18_op19_symbols_are_exported() -> None:
    expected = {
        "P7_R54_OPERATION_BODYFREE_POST_REVIEW_SUMMARY_SCHEMA_VERSION",
        "P7_R54_OPERATION_P5_DECISION_CANDIDATE_SEPARATION_SCHEMA_VERSION",
        "P7_R54_OP18_SUMMARY_READY_STATUS_REF",
        "P7_R54_OP19_DECISION_SEPARATION_READY_STATUS_REF",
        "build_p7_r54_op18_bodyfree_post_review_summary",
        "assert_p7_r54_op18_bodyfree_post_review_summary_contract",
        "build_p7_r54_op19_p5_decision_candidate_separation",
        "assert_p7_r54_op19_p5_decision_candidate_separation_contract",
        "build_p7_r54_operation_bodyfree_post_review_summary_bodyfree",
        "build_p7_r54_operation_p5_decision_candidate_separation_bodyfree",
    }
    assert expected.issubset(set(op.__all__))


def test_op18_default_is_fail_closed_and_bodyfree() -> None:
    material = op.build_p7_r54_op18_bodyfree_post_review_summary()

    assert op.assert_p7_r54_op18_bodyfree_post_review_summary_contract(material) is True
    assert material["bodyfree_post_review_summary_status"] == op.P7_R54_OP18_SUMMARY_BLOCKED_STATUS_REF
    assert material["bodyfree_post_review_summary_ref"] == "bodyfree_post_review_summary_not_ready"
    assert material["p5_decision_candidate_separation_allowed_next"] is False
    assert material["next_required_step"] == op.P7_R54_OP18_BLOCKED_NEXT_REQUIRED_STEP_REF
    assert material["actual_review_evidence_complete"] is False
    assert material["p5_human_blind_qa_confirmed_candidate"] is False
    assert material["p6_limited_human_readfeel_start_allowed"] is False
    assert material["p8_start_allowed"] is False
    assert material["release_allowed"] is False
    assert material["body_free"] is True
    assert material["question_text_included"] is False
    assert material["draft_question_text_included"] is False
    assert material["local_path_included"] is False
    assert material["open_execution_blocker_ids"]


def test_op18_ready_summarizes_only_bodyfree_counts() -> None:
    material = _op18_ready()

    assert op.assert_p7_r54_op18_bodyfree_post_review_summary_contract(material) is True
    assert material["bodyfree_post_review_summary_status"] == op.P7_R54_OP18_SUMMARY_READY_STATUS_REF
    assert material["bodyfree_post_review_summary_ref"] == op.P7_R54_OP18_SUMMARY_REF
    assert material["required_case_count"] == 24
    assert material["reviewed_case_count"] == 24
    assert material["rating_row_count"] == 24
    assert material["question_observation_row_count"] == 24
    assert material["verdict_counts"] == {"PASS": 24, "YELLOW": 0, "REPAIR_REQUIRED": 0, "RED": 0}
    assert material["primary_class_counts"] == {"no_question_needed_emlis_can_observe": 24}
    assert material["ambiguity_kind_counts"] == {"no_material_ambiguity": 24}
    assert material["one_question_fit_counts"] == {"not_needed": 24}
    assert material["repair_required_counts"] == {"no_repair_required": 24}
    assert material["disposal_verified"] is True
    assert material["no_body_leak_validation_passed"] is True
    assert material["no_question_text_validation_passed"] is True
    assert material["no_touch_validation_passed"] is True
    assert material["p5_decision_candidate_separation_allowed_next"] is True
    assert material["next_required_step"] == op.P7_R54_OP19_STEP_REF
    assert material["p5_human_blind_qa_confirmed_candidate"] is False
    assert material["actual_review_evidence_complete"] is False
    assert material["p6_limited_human_readfeel_start_allowed"] is False
    assert material["p8_start_allowed"] is False
    assert material["release_allowed"] is False
    assert material["open_execution_blocker_ids"] == []


def test_op18_summary_contains_no_body_or_question_text_material() -> None:
    material = _op18_ready()
    forbidden_keys = {
        "body_full_packet_content",
        "packet_content",
        "raw_input",
        "returned_emlis_body",
        "bounded_history_surface_body",
        "reviewer_free_text",
        "reviewer_notes_body",
        "local_path",
        "body_hash",
        "question_text",
        "draft_question_text",
    }
    assert forbidden_keys.isdisjoint(material.keys())


def test_op19_default_is_blocked_inconclusive_without_promotion() -> None:
    material = op.build_p7_r54_op19_p5_decision_candidate_separation()

    assert op.assert_p7_r54_op19_p5_decision_candidate_separation_contract(material) is True
    assert material["decision_candidate_separation_status"] == op.P7_R54_OP19_DECISION_SEPARATION_BLOCKED_STATUS_REF
    assert material["p5_decision_candidate_ref"] == op.P7_R54_OP19_INCONCLUSIVE_REF
    assert material["p5_decision_candidate_materialized_here"] is False
    assert material["p5_human_blind_qa_confirmed_candidate"] is False
    assert material["p5_human_blind_qa_confirmed_final"] is False
    assert material["p6_limited_human_readfeel_candidate"] is False
    assert material["p6_limited_human_readfeel_start_allowed"] is False
    assert material["p8_question_design_material_candidate"] is False
    assert material["p8_start_allowed"] is False
    assert material["release_allowed"] is False
    assert material["actual_review_evidence_complete"] is False
    assert material["next_required_step"] == op.P7_R54_OP19_BLOCKED_NEXT_REQUIRED_STEP_REF


def test_op19_confirmed_candidate_is_candidate_only_not_final_or_promotion() -> None:
    material = op.build_p7_r54_op19_p5_decision_candidate_separation(
        bodyfree_post_review_summary=_op18_ready(),
    )

    assert op.assert_p7_r54_op19_p5_decision_candidate_separation_contract(material) is True
    assert material["decision_candidate_separation_status"] == op.P7_R54_OP19_DECISION_SEPARATION_READY_STATUS_REF
    assert material["p5_decision_candidate_ref"] == op.P7_R54_OP19_P5_CONFIRMED_CANDIDATE_REF
    assert material["p5_decision_candidate_materialized_here"] is True
    assert material["p5_confirmed_candidate_conditions_met"] is True
    assert material["p5_human_blind_qa_confirmed_candidate"] is True
    assert material["p5_human_blind_qa_confirmed_final"] is False
    assert material["p6_limited_human_readfeel_candidate"] is False
    assert material["p6_limited_human_readfeel_start_allowed"] is False
    assert material["p8_question_design_material_candidate"] is False
    assert material["p8_start_allowed"] is False
    assert material["release_allowed"] is False
    assert material["actual_review_evidence_complete"] is False
    assert material["next_required_step"] == op.P7_R54_OP20_STEP_REF


def test_op19_red_or_repair_required_verdict_returns_p5_repair() -> None:
    summary = dict(_op18_ready())
    summary["verdict_counts"] = {"PASS": 23, "YELLOW": 0, "REPAIR_REQUIRED": 1, "RED": 0}
    assert op.assert_p7_r54_op18_bodyfree_post_review_summary_contract(summary) is True

    material = op.build_p7_r54_op19_p5_decision_candidate_separation(bodyfree_post_review_summary=summary)

    assert material["p5_decision_candidate_ref"] == op.P7_R54_OP19_P5_REPAIR_RETURN_REF
    assert material["p5_repair_return_required"] is True
    assert "repair_required_verdict_present" in material["p5_decision_repair_reason_refs"]
    assert material["next_required_step"] == op.P7_R54_OP19_P5_REPAIR_NEXT_REQUIRED_STEP_REF
    assert material["p6_limited_human_readfeel_start_allowed"] is False
    assert material["p8_start_allowed"] is False
    assert material["release_allowed"] is False


def test_op19_yellow_verdict_stays_inconclusive_not_p5_confirmed() -> None:
    summary = dict(_op18_ready())
    summary["verdict_counts"] = {"PASS": 23, "YELLOW": 1, "REPAIR_REQUIRED": 0, "RED": 0}
    assert op.assert_p7_r54_op18_bodyfree_post_review_summary_contract(summary) is True

    material = op.build_p7_r54_op19_p5_decision_candidate_separation(bodyfree_post_review_summary=summary)

    assert material["p5_decision_candidate_ref"] == op.P7_R54_OP19_INCONCLUSIVE_REF
    assert material["r54_operation_inconclusive_required"] is True
    assert "yellow_verdict_present" in material["p5_decision_inconclusive_reason_refs"]
    assert material["p5_human_blind_qa_confirmed_candidate"] is False
    assert material["next_required_step"] == op.P7_R54_OP19_INCONCLUSIVE_NEXT_REQUIRED_STEP_REF
