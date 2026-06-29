# -*- coding: utf-8 -*-
"""R50-16/R50-17 tests for P5 human Blind QA manual-run decision.

These tests stop at body-free P6/P8 candidate handoffs. They do not start P6,
do not start P8, do not design question text, do not generate body-full packets,
do not run human review, do not write files, and do not touch API/DB/RN/release
contracts.
"""

from __future__ import annotations

import copy

import pytest

import emlis_ai_p7_r50_p5_human_blind_qa_manual_run_decision as r50


_VALID_LOCAL_ROOT_REF = "/tmp/cocolon_emlis_r50_local_review"
_SAFE_BODYFREE_EXPORT_CANDIDATE_REF = "summary.bodyfree/post_review_decision_summary.bodyfree.json"

_FALSE_ALWAYS_FLAGS = (
    "p6_limited_human_readfeel_start_allowed",
    "p6_limited_human_readfeel_confirmed",
    "p7_complete",
    "p8_start_allowed",
    "release_allowed",
    "actual_human_review_run_here",
    "actual_manual_review_run_here",
    "body_full_packet_generated_here",
    "body_full_packets_created_local_only",
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


def _assert_no_start_or_release(material):
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
        "ambiguity_kind_refs": ["no_material_ambiguity"] if primary == "no_question_needed_emlis_can_observe" else ["missing_target"],
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


def _question_rows(count=24, *, repair_index=None, plus_index=None):
    rows = []
    for index in range(count):
        if repair_index == index:
            primary = "not_question_p5_surface_repair_required"
        elif plus_index == index:
            primary = "plus_single_question_candidate_later"
        else:
            primary = "no_question_needed_emlis_can_observe"
        rows.append(
            r50.normalize_p7_r50_question_need_observation_row_bodyfree(
                question_observation_result=_question_result(primary),
                case_row=_case_row(index),
            )
        )
    return rows


def _summary(*, repair_index=None, status="DISPOSAL_VERIFIED", count=24, plus_index=None):
    return r50.build_p7_r50_body_free_post_review_summary_bodyfree(
        disposal_receipt_builder_verifier_bodyfree=_r13_verified(status=status),
        rating_rows_bodyfree=_rating_rows(count=count, repair_index=repair_index),
        question_need_observation_rows_bodyfree=_question_rows(count=count, repair_index=repair_index, plus_index=plus_index),
    )


def _decision(*, repair_index=None, status="DISPOSAL_VERIFIED", count=24, plus_index=None):
    summary = _summary(repair_index=repair_index, status=status, count=count, plus_index=plus_index)
    return r50.build_p7_r50_p5_confirmed_repair_return_inconclusive_decision_bodyfree(
        post_review_summary_bodyfree=summary
    ), summary


def _freeze(*, repair_index=None, status="DISPOSAL_VERIFIED", count=24, plus_index=None):
    decision, summary = _decision(repair_index=repair_index, status=status, count=count, plus_index=plus_index)
    return r50.build_p7_r50_r14_r15_post_review_decision_freeze(
        body_free_post_review_summary_bodyfree=summary,
        p5_confirmed_repair_inconclusive_decision_bodyfree=decision,
    )


# ---------------------------------------------------------------------------
# R50-16 / R50-17: P6 and P8 candidate handoffs
# ---------------------------------------------------------------------------


def test_r50_16_p6_candidate_handoff_requires_p5_confirmed_but_does_not_start_p6():
    p6 = r50.build_p7_r50_p6_limited_human_readfeel_candidate_handoff_bodyfree(
        r14_r15_post_review_decision_freeze=_freeze()
    )

    assert p6["schema_version"] == r50.P7_R50_P6_LIMITED_HUMAN_READFEEL_CANDIDATE_HANDOFF_BODYFREE_SCHEMA_VERSION
    assert p6["p6_candidate_handoff_status"] == "P6_LIMITED_HUMAN_READFEEL_CANDIDATE_HANDOFF_READY"
    assert p6["p6_limited_human_readfeel_start_allowed_candidate"] is True
    assert p6["p6_limited_human_readfeel_start_allowed"] is False
    assert p6["p5_human_blind_qa_confirmed_candidate"] is True
    assert p6["next_required_step"] == r50.P7_R50_R16_NEXT_REQUIRED_STEP_REF
    assert tuple(p6["implemented_steps"]) == r50.P7_R50_R16_IMPLEMENTED_STEPS
    assert tuple(p6["not_yet_implemented_steps"]) == r50.P7_R50_R16_NOT_YET_IMPLEMENTED_STEPS
    assert p6["r16_p6_limited_human_readfeel_candidate_handoff_built"] is True
    _assert_no_start_or_release(p6)


def test_r50_16_blocks_p6_candidate_when_p5_repair_return_is_needed():
    p6 = r50.build_p7_r50_p6_limited_human_readfeel_candidate_handoff_bodyfree(
        r14_r15_post_review_decision_freeze=_freeze(repair_index=0)
    )

    assert p6["p5_repair_return_candidate"] is True
    assert p6["p6_limited_human_readfeel_start_allowed_candidate"] is False
    assert p6["p6_candidate_handoff_status"] == "BLOCKED_BY_R50_15_P5_DECISION"
    assert "p5_confirmed_candidate_true" in p6["p6_candidate_missing_requirement_refs"]
    assert "p5_unresolved_material_not_hidden_by_p6" in p6["p6_candidate_missing_requirement_refs"]
    assert p6["next_required_step"] == r50.P7_R50_R16_BLOCKED_NEXT_REQUIRED_STEP_REF
    _assert_no_start_or_release(p6)


def test_r50_17_p8_material_candidate_uses_only_bodyfree_question_counts_and_does_not_start_p8():
    p6 = r50.build_p7_r50_p6_limited_human_readfeel_candidate_handoff_bodyfree(
        r14_r15_post_review_decision_freeze=_freeze(plus_index=2)
    )
    p8 = r50.build_p7_r50_p8_question_design_material_candidate_handoff_bodyfree(
        p6_limited_human_readfeel_candidate_handoff_bodyfree=p6
    )

    assert p8["schema_version"] == r50.P7_R50_P8_QUESTION_DESIGN_MATERIAL_CANDIDATE_HANDOFF_BODYFREE_SCHEMA_VERSION
    assert p8["p8_candidate_handoff_status"] == "P8_QUESTION_DESIGN_MATERIAL_CANDIDATE_READY"
    assert p8["p8_question_design_material_candidate"] is True
    assert p8["p8_start_allowed"] is False
    assert p8["question_text_included"] is False
    assert p8["draft_question_text_included"] is False
    assert p8["reviewer_free_text_included"] is False
    assert p8["raw_input_or_comment_text_included"] is False
    assert p8["returned_surface_included"] is False
    assert p8["local_path_or_body_hash_included"] is False
    assert p8["question_trigger_logic_implemented_here"] is False
    assert p8["p8_detail_design_allowed_here"] is False
    assert p8["p8_implementation_spec_finalized_here"] is False
    assert p8["question_observation_row_count"] == 24
    assert p8["plus_single_question_candidate_later_count"] == 1
    assert set(p8["primary_class_counts"]) == set(r50.P7_R50_QUESTION_NEED_PRIMARY_CLASS_REFS)
    assert set(p8["ambiguity_kind_counts"]) == set(r50.P7_R50_AMBIGUITY_KIND_REFS)
    assert set(p8["one_question_fit_counts"]) == set(r50.P7_R50_ONE_QUESTION_FIT_REFS)
    assert set(p8["repair_required_counts"]) == set(r50.P7_R50_REPAIR_REQUIRED_REF_REFS)
    assert tuple(p8["implemented_steps"]) == r50.P7_R50_R17_IMPLEMENTED_STEPS
    assert p8["next_required_step"] == r50.P7_R50_R17_NEXT_REQUIRED_STEP_REF
    _assert_no_start_or_release(p8)


def test_r50_17_blocks_p8_material_when_p5_repair_return_would_be_mixed_into_questions():
    p6 = r50.build_p7_r50_p6_limited_human_readfeel_candidate_handoff_bodyfree(
        r14_r15_post_review_decision_freeze=_freeze(repair_index=0)
    )
    p8 = r50.build_p7_r50_p8_question_design_material_candidate_handoff_bodyfree(
        p6_limited_human_readfeel_candidate_handoff_bodyfree=p6
    )

    assert p8["p8_question_design_material_candidate"] is False
    assert p8["p8_candidate_handoff_status"] == "BLOCKED_BY_R50_16_P6_HANDOFF"
    assert "repair_required_not_question_not_misclassified_as_p8" in p8["p8_design_material_candidate_missing_requirement_refs"]
    assert "p5_repair_return_not_mixed_into_p8_material" in p8["p8_design_material_candidate_missing_requirement_refs"]
    assert p8["not_question_repair_required_count"] == 1
    assert p8["next_required_step"] == r50.P7_R50_R17_BLOCKED_NEXT_REQUIRED_STEP_REF
    _assert_no_start_or_release(p8)


def test_r50_17_blocks_p8_material_when_question_rows_are_incomplete():
    p6 = r50.build_p7_r50_p6_limited_human_readfeel_candidate_handoff_bodyfree(
        r14_r15_post_review_decision_freeze=_freeze(count=23)
    )
    p8 = r50.build_p7_r50_p8_question_design_material_candidate_handoff_bodyfree(
        p6_limited_human_readfeel_candidate_handoff_bodyfree=p6
    )

    assert p8["question_observation_rows_complete"] is False
    assert p8["p8_question_design_material_candidate"] is False
    assert "question_observation_rows_24_complete" in p8["p8_design_material_candidate_missing_requirement_refs"]
    assert p8["p8_start_allowed"] is False
    _assert_no_start_or_release(p8)


def test_r50_17_contract_rejects_question_text_or_p8_start_drift():
    p6 = r50.build_p7_r50_p6_limited_human_readfeel_candidate_handoff_bodyfree(
        r14_r15_post_review_decision_freeze=_freeze()
    )
    p8 = r50.build_p7_r50_p8_question_design_material_candidate_handoff_bodyfree(
        p6_limited_human_readfeel_candidate_handoff_bodyfree=p6
    )

    drift = copy.deepcopy(p8)
    drift["question_text_included"] = True
    with pytest.raises(ValueError):
        r50.assert_p7_r50_p8_question_design_material_candidate_handoff_bodyfree_contract(drift)

    drift = copy.deepcopy(p8)
    drift["p8_start_allowed"] = True
    with pytest.raises(ValueError):
        r50.assert_p7_r50_p8_question_design_material_candidate_handoff_bodyfree_contract(drift)


def test_r50_r16_r17_freeze_keeps_candidate_handoffs_separate_from_start_permissions():
    p6 = r50.build_p7_r50_p6_limited_human_readfeel_candidate_handoff_bodyfree(
        r14_r15_post_review_decision_freeze=_freeze(plus_index=1)
    )
    p8 = r50.build_p7_r50_p8_question_design_material_candidate_handoff_bodyfree(
        p6_limited_human_readfeel_candidate_handoff_bodyfree=p6
    )
    freeze = r50.build_p7_r50_r16_r17_p6_p8_candidate_handoff_freeze(
        p6_limited_human_readfeel_candidate_handoff_bodyfree=p6,
        p8_question_design_material_candidate_handoff_bodyfree=p8,
    )

    assert freeze["schema_version"] == r50.P7_R50_R16_R17_P6_P8_CANDIDATE_HANDOFF_FREEZE_SCHEMA_VERSION
    assert freeze["p6_limited_human_readfeel_start_allowed_candidate"] is True
    assert freeze["p6_limited_human_readfeel_start_allowed"] is False
    assert freeze["p8_question_design_material_candidate"] is True
    assert freeze["p8_start_allowed"] is False
    assert freeze["p7_complete"] is False
    assert freeze["release_allowed"] is False
    assert tuple(freeze["implemented_steps"]) == r50.P7_R50_R17_IMPLEMENTED_STEPS
    assert tuple(freeze["not_yet_implemented_steps"]) == r50.P7_R50_R17_NOT_YET_IMPLEMENTED_STEPS
    _assert_no_start_or_release(freeze)
