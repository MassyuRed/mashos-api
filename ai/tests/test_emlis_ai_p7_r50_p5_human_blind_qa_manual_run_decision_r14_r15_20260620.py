# -*- coding: utf-8 -*-
"""R50-14/R50-15 tests for P5 human Blind QA manual-run decision.

These tests stop at body-free post-review summary building and P5 confirmed /
repair-return / inconclusive decision separation. They do not run human review,
do not generate body-full packets, do not write files, do not materialize actual
summary/decision artifacts, do not touch API/DB/RN contracts, do not start P6 or
P8, do not complete P7, and do not claim release readiness.
"""

from __future__ import annotations

import copy

import pytest

import emlis_ai_p7_r50_p5_human_blind_qa_manual_run_decision as r50


_VALID_LOCAL_ROOT_REF = "/tmp/cocolon_emlis_r50_local_review"
_SAFE_BODYFREE_EXPORT_CANDIDATE_REF = "summary.bodyfree/post_review_decision_summary.bodyfree.json"

_FALSE_ALWAYS_FLAGS = (
    "actual_human_review_run_here",
    "actual_manual_review_run_here",
    "body_full_packet_generated_here",
    "body_full_packets_created_local_only",
    "p6_limited_human_readfeel_start_allowed_candidate",
    "p8_question_design_material_candidate",
    "p7_complete",
    "p8_start_allowed",
    "release_allowed",
)

_BODY_LEAK_FIELD_REFS = (
    "raw_input",
    "raw_answer",
    "comment_text",
    "comment_text_body",
    "returned_emlis_surface",
    "bounded_owned_history_review_surface",
    "current_input_review_surface",
    "reviewer_free_text",
    "reviewer_note",
    "reviewer_notes",
    "question_text",
    "draft_question_text",
    "question_body",
    "local_absolute_path",
    "body_content_hash",
    "packet_content_hash",
    "terminal_output",
    "stdout",
    "stderr",
    "traceback",
)


def _walk_keys(value):
    if isinstance(value, dict):
        for key, child in value.items():
            yield str(key)
            yield from _walk_keys(child)
    elif isinstance(value, (list, tuple)):
        for child in value:
            yield from _walk_keys(child)


def _assert_body_free_no_leak(value):
    keys = set(_walk_keys(value))
    assert not (keys & set(_BODY_LEAK_FIELD_REFS))


def _assert_no_p6_p8_p7_release(material):
    for key in _FALSE_ALWAYS_FLAGS:
        if key in material:
            assert material[key] is False
    assert material["body_free"] is True
    _assert_body_free_no_leak(material)


def _r3_go():
    return r50.build_p7_r50_manual_run_decision_bodyfree(
        local_review_root_safe=True,
        explicit_allow_present=True,
        disposal_plan_ready=True,
        body_free_summary_path_ready=True,
    )


def _r4_passed():
    return r50.build_p7_r50_local_only_root_explicit_allow_export_denylist_preflight(
        manual_run_decision_bodyfree=_r3_go(),
        local_review_root=_VALID_LOCAL_ROOT_REF,
        explicit_allow_token=r50.P7_R50_EXPLICIT_BODY_FULL_ALLOW_TOKEN_REF,
        export_candidate_refs=[_SAFE_BODYFREE_EXPORT_CANDIDATE_REF],
    )


def _r5_ready():
    return r50.build_p7_r50_review_session_protocol_bodyfree(
        local_only_root_explicit_allow_export_preflight=_r4_passed()
    )


def _r6_ready():
    return r50.build_p7_r50_local_only_body_full_packet_generation_request(
        review_session_protocol_bodyfree=_r5_ready()
    )


def _r7_ready():
    return r50.build_p7_r50_reviewer_instruction_rating_form_freeze(
        local_only_body_full_packet_generation_request=_r6_ready()
    )


def _r8_ready():
    return r50.build_p7_r50_rating_row_normalizer_bodyfree(
        reviewer_instruction_rating_form_freeze=_r7_ready()
    )


def _r9_ready():
    return r50.build_p7_r50_readfeel_blocker_execution_blocker_ingestion_bodyfree(
        rating_row_normalizer_bodyfree=_r8_ready()
    )


def _r10_ready():
    return r50.build_p7_r50_question_need_observation_row_normalizer_bodyfree(
        readfeel_blocker_execution_blocker_ingestion_bodyfree=_r9_ready()
    )


def _r11_ready():
    return r50.build_p7_r50_rating_question_observation_consistency_guard_bodyfree(
        question_need_observation_row_normalizer_bodyfree=_r10_ready()
    )


def _r12_ready():
    return r50.build_p7_r50_pause_abort_expiration_protocol_bodyfree(
        rating_question_observation_consistency_guard_bodyfree=_r11_ready()
    )


def _verified_receipt(status="DISPOSAL_VERIFIED"):
    return r50.build_p7_r50_disposal_receipt_bodyfree(
        review_session_id="p7_r50_review_session_001",
        case_count=24,
        deleted_file_count=48,
        disposal_status=status,
        body_removed=True,
        reviewer_notes_removed=True,
        purge_started_at="2026-06-20T10:00:00+09:00",
        purge_completed_at="2026-06-20T10:01:00+09:00",
    )


def _r13_verified(status="DISPOSAL_VERIFIED"):
    return r50.build_p7_r50_disposal_receipt_builder_verifier_bodyfree(
        pause_abort_expiration_protocol_bodyfree=_r12_ready(),
        disposal_receipt_bodyfree=_verified_receipt(status=status),
    )


def _pending_receipt():
    return r50.build_p7_r50_disposal_receipt_bodyfree(
        review_session_id="p7_r50_review_session_001",
        case_count=24,
        deleted_file_count=0,
        disposal_status="NOT_GENERATED",
        body_removed=False,
        reviewer_notes_removed=False,
    )


def _case_row(index: int, **overrides):
    row = {
        "review_session_id": "p7_r50_review_session_001",
        "packet_ref_id": f"packet_blind_{index:02d}",
        "blind_case_id": f"blind_case_{index:02d}",
        "case_ref_id": f"case_history_line_eligible_{index:02d}",
        "family": "history_line_eligible_input",
        "case_role": "positive_history_line",
        "body_free": True,
    }
    row.update(overrides)
    return row


def _pass_result(**overrides):
    result = {
        "axis_scores": {axis: 1.0 for axis in r50.P5_HUMAN_BLIND_QA_RATING_AXES},
        "verdict": "PASS",
        "sanitized_reason_ids": [],
        "blocker_ids": [],
        "reviewer_free_text_included": False,
        "body_free": True,
    }
    result.update(overrides)
    return result


def _repair_result(**overrides):
    scores = {axis: 1.0 for axis in r50.P5_HUMAN_BLIND_QA_RATING_AXES}
    scores["history_connection_naturalness"] = 0.5
    result = {
        "axis_scores": scores,
        "verdict": "REPAIR_REQUIRED",
        "sanitized_reason_ids": ["p5_history_connection_too_generic"],
        "blocker_ids": ["p5_history_connection_too_generic"],
        "reviewer_free_text_included": False,
        "body_free": True,
    }
    result.update(overrides)
    return result


def _question_result(primary="no_question_needed_emlis_can_observe", **overrides):
    result = {
        "question_need_primary_class": primary,
        "ambiguity_kind_refs": ["no_material_ambiguity"] if primary == "no_question_needed_emlis_can_observe" else [],
        "sanitized_reason_ids": [primary],
        "question_text_included": False,
        "draft_question_text_included": False,
        "reviewer_free_text_included": False,
        "body_free": True,
    }
    result.update(overrides)
    return result


def _rating_rows(count=24, *, repair_index=None):
    rows = []
    for index in range(count):
        result = _repair_result() if index == repair_index else _pass_result()
        rows.append(
            r50.normalize_p7_r50_rating_capture_row_bodyfree(
                review_result=result,
                case_row=_case_row(index),
                reviewer_ref="reviewer_bodyfree_001",
                reviewed_at="2026-06-20T12:00:00+09:00",
            )
        )
    return rows


def _question_rows(count=24, *, repair_index=None):
    rows = []
    for index in range(count):
        primary = "not_question_p5_surface_repair_required" if index == repair_index else "no_question_needed_emlis_can_observe"
        rows.append(
            r50.normalize_p7_r50_question_need_observation_row_bodyfree(
                question_observation_result=_question_result(primary),
                case_row=_case_row(index),
            )
        )
    return rows


def _readfeel_blocker_rows(*, repair_index=None):
    if repair_index is None:
        return []
    return [
        r50.build_p7_r50_readfeel_blocker_row_bodyfree(
            case_row=_case_row(repair_index),
            blocker_id="p5_history_connection_too_generic",
            sanitized_reason_ids=["p5_history_connection_too_generic"],
        )
    ]


def _execution_blocker_rows(*, index=0):
    return [
        r50.build_p7_r50_execution_blocker_row_bodyfree(
            case_row=_case_row(index),
            execution_blocker_id="r50_review_aborted_before_rating",
            execution_blocker_status="OPEN",
        )
    ]


def _summary(count=24, *, disposal_status="DISPOSAL_VERIFIED", repair_index=None, execution_blocker=False):
    return r50.build_p7_r50_body_free_post_review_summary_bodyfree(
        disposal_receipt_builder_verifier_bodyfree=_r13_verified(status=disposal_status),
        rating_rows_bodyfree=_rating_rows(count=count, repair_index=repair_index),
        question_need_observation_rows_bodyfree=_question_rows(count=count, repair_index=repair_index),
        readfeel_blocker_rows_bodyfree=_readfeel_blocker_rows(repair_index=repair_index),
        execution_blocker_rows_bodyfree=_execution_blocker_rows() if execution_blocker else [],
    )


def test_r50_received_source_contains_r0_to_r13_before_r14_r15_progression():
    assert r50.P7_R50_R13_IMPLEMENTED_STEPS[-1] == "R50-13_disposal_receipt_builder_verifier"
    assert r50.P7_R50_R13_NOT_YET_IMPLEMENTED_STEPS[0] == "R50-14_body_free_post_review_summary_builder"
    assert r50.P7_R50_R13_NEXT_REQUIRED_STEP_REF == "R50-14_body_free_post_review_summary_builder"
    assert r50.P7_R50_R14_NEXT_REQUIRED_STEP_REF == "R50-15_p5_confirmed_repair_return_inconclusive_decision"
    assert r50.P7_R50_R15_NEXT_REQUIRED_STEP_REF == "R50-16_p6_limited_human_readfeel_candidate_handoff"


def test_r50_r14_builds_bodyfree_post_review_summary_counts_without_materializing_summary_file():
    summary = _summary()

    assert r50.assert_p7_r50_body_free_post_review_summary_bodyfree_contract(summary) is True
    assert summary["schema_version"] == r50.P7_R50_BODY_FREE_POST_REVIEW_SUMMARY_BODYFREE_SCHEMA_VERSION
    assert summary["policy_section"] == "R50-14_body_free_post_review_summary_builder"
    assert summary["post_review_summary_builder_status"] == "BODYFREE_POST_REVIEW_SUMMARY_READY"
    assert summary["rating_row_count"] == 24
    assert summary["question_observation_row_count"] == 24
    assert summary["rating_and_question_case_ref_sets_match"] is True
    assert summary["verdict_counts"]["PASS"] == 24
    assert summary["verdict_counts"]["RED"] == 0
    assert summary["execution_blocker_open_count"] == 0
    assert summary["readfeel_blocker_open_count"] == 0
    assert summary["question_need_primary_class_counts"]["no_question_needed_emlis_can_observe"] == 24
    assert summary["ambiguity_kind_counts"]["no_material_ambiguity"] == 24
    assert summary["one_question_fit_counts"]["not_needed"] == 24
    assert summary["repair_required_counts"]["no_repair_required"] == 24
    assert summary["disposal_status"] == "DISPOSAL_VERIFIED"
    assert summary["body_free_summary_ready"] is True
    assert summary["post_review_summary_materialized_here"] is False
    assert summary["next_required_step"] == r50.P7_R50_R14_NEXT_REQUIRED_STEP_REF
    assert summary["implemented_steps"] == list(r50.P7_R50_R14_IMPLEMENTED_STEPS)
    assert summary["not_yet_implemented_steps"] == list(r50.P7_R50_R14_NOT_YET_IMPLEMENTED_STEPS)
    _assert_no_p6_p8_p7_release(summary)


def test_r50_r14_blocks_summary_when_disposal_receipt_is_not_verified():
    verifier = r50.build_p7_r50_disposal_receipt_builder_verifier_bodyfree(
        pause_abort_expiration_protocol_bodyfree=_r12_ready(),
        disposal_receipt_bodyfree=_pending_receipt(),
    )
    summary = r50.build_p7_r50_body_free_post_review_summary_bodyfree(
        disposal_receipt_builder_verifier_bodyfree=verifier,
        rating_rows_bodyfree=_rating_rows(),
        question_need_observation_rows_bodyfree=_question_rows(),
    )

    assert summary["post_review_summary_builder_status"] == "BLOCKED_BY_R50_13_DISPOSAL_RECEIPT"
    assert summary["body_free_summary_ready"] is False
    assert summary["p5_decision_required_next"] is False
    assert summary["next_required_step"] == r50.P7_R50_R14_BLOCKED_NEXT_REQUIRED_STEP_REF
    _assert_no_p6_p8_p7_release(summary)


def test_r50_r15_confirms_p5_candidate_only_when_all_bodyfree_requirements_are_met():
    summary = _summary()
    decision = r50.build_p7_r50_p5_confirmed_repair_return_inconclusive_decision_bodyfree(
        post_review_summary_bodyfree=summary
    )

    assert r50.assert_p7_r50_p5_confirmed_repair_return_inconclusive_decision_bodyfree_contract(decision) is True
    assert decision["schema_version"] == r50.P7_R50_P5_CONFIRMED_REPAIR_INCONCLUSIVE_DECISION_BODYFREE_SCHEMA_VERSION
    assert decision["p5_decision_status"] == "P5_CONFIRMED_CANDIDATE"
    assert decision["p5_human_blind_qa_confirmed_candidate"] is True
    assert decision["p5_human_blind_qa_confirmed"] is False
    assert decision["p5_repair_return_candidate"] is False
    assert decision["p5_review_inconclusive"] is False
    assert decision["p5_confirmed_candidate_reason_refs"] == list(r50.P7_R50_P5_CONFIRMED_REQUIREMENT_REFS)
    assert decision["next_required_step"] == r50.P7_R50_R15_NEXT_REQUIRED_STEP_REF
    assert decision["implemented_steps"] == list(r50.P7_R50_R15_IMPLEMENTED_STEPS)
    assert decision["not_yet_implemented_steps"] == list(r50.P7_R50_R15_NOT_YET_IMPLEMENTED_STEPS)
    _assert_no_p6_p8_p7_release(decision)


def test_r50_r15_returns_p5_repair_when_readfeel_or_p5_surface_repair_is_present():
    summary = _summary(repair_index=0)
    decision = r50.build_p7_r50_p5_confirmed_repair_return_inconclusive_decision_bodyfree(
        post_review_summary_bodyfree=summary
    )

    assert decision["p5_decision_status"] == "P5_REPAIR_RETURN"
    assert decision["p5_human_blind_qa_confirmed_candidate"] is False
    assert decision["p5_repair_return_candidate"] is True
    assert decision["p5_review_inconclusive"] is False
    assert any(ref.startswith("readfeel_blocker:p5_history_connection_too_generic") for ref in decision["p5_decision_reason_refs"])
    assert any(ref.startswith("question_primary_repair:not_question_p5_surface_repair_required") for ref in decision["p5_decision_reason_refs"])
    assert decision["next_required_step"] == r50.P7_R50_R15_REPAIR_RETURN_NEXT_REQUIRED_STEP_REF
    _assert_no_p6_p8_p7_release(decision)


def test_r50_r15_marks_inconclusive_for_incomplete_rows_open_execution_blocker_or_expired_purge():
    incomplete = r50.build_p7_r50_p5_confirmed_repair_return_inconclusive_decision_bodyfree(
        post_review_summary_bodyfree=_summary(count=23)
    )
    assert incomplete["p5_decision_status"] == "P5_REVIEW_INCONCLUSIVE"
    assert incomplete["p5_review_inconclusive"] is True
    assert "r50_24_case_rows_incomplete" in incomplete["p5_inconclusive_reason_refs"]

    blocked = r50.build_p7_r50_p5_confirmed_repair_return_inconclusive_decision_bodyfree(
        post_review_summary_bodyfree=_summary(execution_blocker=True)
    )
    assert blocked["p5_decision_status"] == "P5_REVIEW_INCONCLUSIVE"
    assert "r50_open_execution_blockers" in blocked["p5_inconclusive_reason_refs"]

    expired = r50.build_p7_r50_p5_confirmed_repair_return_inconclusive_decision_bodyfree(
        post_review_summary_bodyfree=_summary(disposal_status="EXPIRED_PURGED")
    )
    assert expired["p5_decision_status"] == "P5_REVIEW_INCONCLUSIVE"
    assert expired["disposal_status"] == "EXPIRED_PURGED"
    assert "r50_disposal_not_verified_for_candidate" in expired["p5_inconclusive_reason_refs"]


def test_r50_r14_r15_freeze_composes_summary_and_decision_without_promoting_p6_p8_release():
    summary = _summary()
    freeze = r50.build_p7_r50_r14_r15_post_review_decision_freeze(
        body_free_post_review_summary_bodyfree=summary
    )

    assert r50.assert_p7_r50_r14_r15_post_review_decision_freeze_contract(freeze) is True
    assert freeze["schema_version"] == r50.P7_R50_R14_R15_POST_REVIEW_DECISION_FREEZE_SCHEMA_VERSION
    assert freeze["policy_section"] == "R50-14_R50-15_post_review_decision_freeze"
    assert freeze["post_review_summary_builder_status"] == "BODYFREE_POST_REVIEW_SUMMARY_READY"
    assert freeze["p5_decision_status"] == "P5_CONFIRMED_CANDIDATE"
    assert freeze["p5_human_blind_qa_confirmed_candidate"] is True
    assert freeze["p6_limited_human_readfeel_start_allowed_candidate"] is False
    assert freeze["p8_question_design_material_candidate"] is False
    assert freeze["p7_complete"] is False
    assert freeze["p8_start_allowed"] is False
    assert freeze["release_allowed"] is False
    assert freeze["next_required_step"] == r50.P7_R50_R15_NEXT_REQUIRED_STEP_REF
    _assert_no_p6_p8_p7_release(freeze)
