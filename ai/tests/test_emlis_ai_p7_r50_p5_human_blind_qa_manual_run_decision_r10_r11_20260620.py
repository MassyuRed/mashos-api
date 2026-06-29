# -*- coding: utf-8 -*-
"""R50-10/R50-11 tests for P5 human Blind QA manual-run decision.

These tests stop at body-free question-need row normalization and the rating vs
question-observation consistency guard.  They do not run human review, do not
materialize actual 24-case rows, do not write body-full packets, do not touch
API/DB/RN contracts, do not start P8, do not complete P7, and do not claim
release readiness.
"""

from __future__ import annotations

import copy

import pytest

import emlis_ai_p7_r50_p5_human_blind_qa_manual_run_decision as r50


_VALID_LOCAL_ROOT_REF = "/tmp/cocolon_emlis_r50_local_review"
_SAFE_BODYFREE_EXPORT_CANDIDATE_REF = "summary.bodyfree/post_review_decision_summary.bodyfree.json"

_FALSE_RUNTIME_AND_PRODUCT_FLAGS = (
    "actual_human_review_run_here",
    "actual_manual_review_run_here",
    "body_full_packet_generated_here",
    "body_full_packets_created_local_only",
    "actual_question_need_observation_rows_materialized_here",
    "actual_question_need_observation_summary_materialized_here",
    "api_db_rn_response_key_changed_here",
    "question_api_implemented",
    "question_db_schema_implemented",
    "question_rn_ui_implemented",
    "question_response_key_implemented",
    "question_trigger_logic_implemented",
    "question_storage_schema_implemented",
    "question_answer_persistence_implemented",
    "question_plan_guard_implemented",
    "p8_implementation_spec_finalized_here",
    "p5_human_blind_qa_confirmed",
    "p5_human_blind_qa_confirmed_candidate",
    "p6_limited_human_readfeel_start_allowed",
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


def _assert_no_runtime_or_product_completion(material):
    for key in _FALSE_RUNTIME_AND_PRODUCT_FLAGS:
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


def _case_row(**overrides):
    row = {
        "review_session_id": "p7_r50_review_session_001",
        "packet_ref_id": "packet_blind_001",
        "blind_case_id": "blind_case_001",
        "case_ref_id": "case_history_line_eligible_001",
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


def _repair_required_result(**overrides):
    scores = {axis: 1.0 for axis in r50.P5_HUMAN_BLIND_QA_RATING_AXES}
    scores["history_connection_naturalness"] = 0.50
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


def test_r50_received_source_contains_r0_to_r9_before_r10_r11_progression():
    assert r50.P7_R50_R9_IMPLEMENTED_STEPS[-1] == "R50-9_readfeel_blocker_execution_blocker_ingestion"
    assert r50.P7_R50_R9_NOT_YET_IMPLEMENTED_STEPS[0] == "R50-10_question_need_observation_row_normalizer"
    assert r50.P7_R50_R9_NEXT_REQUIRED_STEP_REF == "R50-10_question_need_observation_row_normalizer"
    assert r50.P7_R50_R10_NEXT_REQUIRED_STEP_REF == "R50-11_rating_question_observation_consistency_guard"
    assert r50.P7_R50_R11_NEXT_REQUIRED_STEP_REF == "R50-12_pause_abort_expiration_protocol"


def test_r50_r10_builds_question_need_observation_row_normalizer_without_materializing_actual_rows():
    normalizer = _r10_ready()

    assert r50.assert_p7_r50_question_need_observation_row_normalizer_bodyfree_contract(normalizer) is True
    assert normalizer["schema_version"] == r50.P7_R50_QUESTION_NEED_OBSERVATION_ROW_NORMALIZER_BODYFREE_SCHEMA_VERSION
    assert normalizer["policy_section"] == "R50-10_question_need_observation_row_normalizer"
    assert normalizer["blocker_ingestion_status"] == "READY_FOR_READFEEL_AND_EXECUTION_BLOCKER_INGESTION"
    assert normalizer["question_observation_normalizer_status"] == "READY_FOR_QUESTION_NEED_OBSERVATION_ROW_NORMALIZATION"
    assert normalizer["normalizer_ready"] is True
    assert normalizer["required_case_count"] == 24
    assert normalizer["question_need_observation_row_schema_version"] == r50.P7_R50_QUESTION_NEED_OBSERVATION_ROW_BODYFREE_SCHEMA_VERSION
    assert normalizer["r49_question_need_observation_row_schema_version_ref"] == r50.P7_R49_QUESTION_NEED_OBSERVATION_ROW_BODYFREE_SCHEMA_VERSION
    assert normalizer["question_need_observation_row_required_field_refs"] == list(r50.P7_R50_QUESTION_NEED_OBSERVATION_ROW_BODYFREE_REQUIRED_FIELD_REFS)
    assert normalizer["question_need_primary_class_refs"] == list(r50.P7_R50_QUESTION_NEED_PRIMARY_CLASS_REFS)
    assert normalizer["ambiguity_kind_refs"] == list(r50.P7_R50_AMBIGUITY_KIND_REFS)
    assert normalizer["one_question_fit_refs"] == list(r50.P7_R50_ONE_QUESTION_FIT_REFS)
    assert normalizer["plan_candidate_flag_refs"] == list(r50.P7_R50_PLAN_CANDIDATE_FLAG_REFS)
    assert normalizer["question_text_included_allowed"] is False
    assert normalizer["draft_question_text_included_allowed"] is False
    assert normalizer["reviewer_free_text_included_allowed"] is False
    assert normalizer["question_trigger_logic_implemented_here"] is False
    assert normalizer["p8_question_implementation_spec_finalized_here"] is False
    assert normalizer["actual_question_need_observation_rows_materialized_here"] is False
    assert normalizer["next_required_step"] == r50.P7_R50_R10_NEXT_REQUIRED_STEP_REF
    assert normalizer["implemented_steps"] == list(r50.P7_R50_R10_IMPLEMENTED_STEPS)
    assert normalizer["not_yet_implemented_steps"] == list(r50.P7_R50_R10_NOT_YET_IMPLEMENTED_STEPS)
    _assert_no_runtime_or_product_completion(normalizer)


def test_r50_r10_normalizes_no_question_needed_row_as_bodyfree_without_question_text():
    row = r50.normalize_p7_r50_question_need_observation_row_bodyfree(
        question_observation_result=_question_result(),
        case_row=_case_row(),
    )

    assert r50.assert_p7_r50_question_need_observation_row_bodyfree_contract(row) is True
    assert row["schema_version"] == r50.P7_R50_QUESTION_NEED_OBSERVATION_ROW_BODYFREE_SCHEMA_VERSION
    assert row["review_session_id"] == "p7_r50_review_session_001"
    assert row["packet_ref_id"] == "packet_blind_001"
    assert row["blind_case_id"] == "blind_case_001"
    assert row["case_ref_id"] == "case_history_line_eligible_001"
    assert row["family"] == "history_line_eligible_input"
    assert row["case_role"] == "positive_history_line"
    assert row["review_kind"] == r50.P7_R50_REVIEW_KIND
    assert row["observation_stage"] == r50.P7_R50_QUESTION_NEED_OBSERVATION_STAGE_REF
    assert row["question_need_primary_class"] == "no_question_needed_emlis_can_observe"
    assert row["ambiguity_kind_refs"] == ["no_material_ambiguity"]
    assert row["one_question_fit_ref"] == "not_needed"
    assert row["repair_required_refs"] == ["no_repair_required"]
    assert row["plan_candidate_flags"] == ["p8_design_material_candidate"]
    assert row["question_text_included"] is False
    assert row["draft_question_text_included"] is False
    assert row["reviewer_free_text_included"] is False
    assert row["body_removed"] is False
    assert row["body_free"] is True
    _assert_body_free_no_leak(row)


def test_r50_r10_normalizes_question_candidate_and_repair_required_rows_with_canonical_enums():
    candidate_row = r50.normalize_p7_r50_question_need_observation_row_bodyfree(
        question_observation_result=_question_result(
            primary="question_may_reduce_overread_risk",
            ambiguity_kind_refs=["missing_target"],
        ),
        case_row=_case_row(),
    )
    assert candidate_row["one_question_fit_ref"] == "fits_one_question"
    assert candidate_row["ambiguity_kind_refs"] == ["missing_target"]
    assert candidate_row["repair_required_refs"] == ["no_repair_required"]
    assert candidate_row["plan_candidate_flags"] == ["p8_design_material_candidate"]

    repair_row = r50.normalize_p7_r50_question_need_observation_row_bodyfree(
        question_observation_result=_question_result(
            primary="not_question_p5_surface_repair_required",
        ),
        case_row=_case_row(),
    )
    assert repair_row["one_question_fit_ref"] == "repair_required_not_question"
    assert repair_row["repair_required_refs"] == ["p5_surface_repair_required"]
    assert repair_row["plan_candidate_flags"] == []
    _assert_body_free_no_leak(candidate_row)
    _assert_body_free_no_leak(repair_row)


def test_r50_r10_rejects_question_text_reviewer_text_body_leak_and_semantic_drift():
    with pytest.raises(ValueError):
        r50.normalize_p7_r50_question_need_observation_row_bodyfree(
            question_observation_result=_question_result(question_text_included=True),
            case_row=_case_row(),
        )

    with pytest.raises(ValueError):
        r50.normalize_p7_r50_question_need_observation_row_bodyfree(
            question_observation_result=_question_result(reviewer_free_text="local-only reviewer note must not leak"),
            case_row=_case_row(),
        )

    with pytest.raises(ValueError):
        r50.normalize_p7_r50_question_need_observation_row_bodyfree(
            question_observation_result=_question_result(
                primary="question_may_reduce_overread_risk",
                ambiguity_kind_refs=["missing_target"],
                one_question_fit_ref="not_needed",
            ),
            case_row=_case_row(),
        )

    with pytest.raises(ValueError):
        r50.normalize_p7_r50_question_need_observation_row_bodyfree(
            question_observation_result=_question_result(
                primary="not_question_emlis_readfeel_repair_required",
                plan_candidate_flags=["p8_design_material_candidate"],
            ),
            case_row=_case_row(),
        )

    with pytest.raises(ValueError):
        r50.normalize_p7_r50_question_need_observation_row_bodyfree(
            question_observation_result=_question_result(
                primary="question_may_reduce_overread_risk",
                ambiguity_kind_refs=[],
            ),
            case_row=_case_row(),
        )


def test_r50_r10_blocks_when_r9_blocker_ingestion_is_not_ready():
    blocked_r4 = r50.build_p7_r50_local_only_root_explicit_allow_export_denylist_preflight(
        manual_run_decision_bodyfree=_r3_go(),
        local_review_root=_VALID_LOCAL_ROOT_REF,
        explicit_allow_token="WRONG_TOKEN",
    )
    blocked_r5 = r50.build_p7_r50_review_session_protocol_bodyfree(
        local_only_root_explicit_allow_export_preflight=blocked_r4
    )
    blocked_r6 = r50.build_p7_r50_local_only_body_full_packet_generation_request(
        review_session_protocol_bodyfree=blocked_r5
    )
    blocked_r7 = r50.build_p7_r50_reviewer_instruction_rating_form_freeze(
        local_only_body_full_packet_generation_request=blocked_r6
    )
    blocked_r8 = r50.build_p7_r50_rating_row_normalizer_bodyfree(
        reviewer_instruction_rating_form_freeze=blocked_r7
    )
    blocked_r9 = r50.build_p7_r50_readfeel_blocker_execution_blocker_ingestion_bodyfree(
        rating_row_normalizer_bodyfree=blocked_r8
    )
    normalizer = r50.build_p7_r50_question_need_observation_row_normalizer_bodyfree(
        readfeel_blocker_execution_blocker_ingestion_bodyfree=blocked_r9
    )

    assert normalizer["blocker_ingestion_status"] == "BLOCKED_BY_R50_8_RATING_ROW_NORMALIZER"
    assert normalizer["question_observation_normalizer_status"] == "BLOCKED_BY_R50_9_BLOCKER_INGESTION"
    assert normalizer["normalizer_ready"] is False
    assert normalizer["local_only_body_full_generation_allowed"] is False
    assert "r50_explicit_allow_missing" in normalizer["execution_blocker_ids"]
    assert normalizer["next_required_step"] == r50.P7_R50_R10_BLOCKED_NEXT_REQUIRED_STEP_REF
    _assert_no_runtime_or_product_completion(normalizer)


def test_r50_r11_builds_consistency_guard_without_running_review_or_p8_design():
    guard = r50.build_p7_r50_rating_question_observation_consistency_guard_bodyfree(
        question_need_observation_row_normalizer_bodyfree=_r10_ready()
    )

    assert r50.assert_p7_r50_rating_question_observation_consistency_guard_bodyfree_contract(guard) is True
    assert guard["schema_version"] == r50.P7_R50_RATING_QUESTION_OBSERVATION_CONSISTENCY_GUARD_BODYFREE_SCHEMA_VERSION
    assert guard["policy_section"] == "R50-11_rating_question_observation_consistency_guard"
    assert guard["question_observation_normalizer_status"] == "READY_FOR_QUESTION_NEED_OBSERVATION_ROW_NORMALIZATION"
    assert guard["consistency_guard_status"] == "READY_FOR_RATING_QUESTION_OBSERVATION_CONSISTENCY_GUARD"
    assert guard["rating_question_consistency_guard_ready"] is True
    assert guard["p5_weakness_must_not_be_hidden_by_questions"] is True
    assert guard["rating_and_question_observation_ids_must_match"] is True
    assert guard["pass_rating_forbids_not_question_repair_primary_class"] is True
    assert guard["repair_or_red_rating_forbids_question_candidate_primary_only"] is True
    assert guard["insufficient_material_requires_execution_blocker_row"] is True
    assert guard["question_candidate_cannot_clear_readfeel_blocker"] is True
    assert guard["consistency_guard_function_ref"] == "assert_p7_r50_rating_vs_question_observation_consistency"
    assert guard["next_required_step"] == r50.P7_R50_R11_NEXT_REQUIRED_STEP_REF
    assert guard["implemented_steps"] == list(r50.P7_R50_R11_IMPLEMENTED_STEPS)
    assert guard["not_yet_implemented_steps"] == list(r50.P7_R50_R11_NOT_YET_IMPLEMENTED_STEPS)
    _assert_no_runtime_or_product_completion(guard)


def test_r50_r11_allows_pass_rating_with_no_question_needed_observation_for_same_case():
    rating_row = r50.normalize_p7_r50_rating_capture_row_bodyfree(
        review_result=_pass_result(),
        case_row=_case_row(),
    )
    question_row = r50.normalize_p7_r50_question_need_observation_row_bodyfree(
        question_observation_result=_question_result(),
        case_row=_case_row(),
    )

    assert r50.assert_p7_r50_rating_vs_question_observation_consistency(
        rating_row=rating_row,
        question_need_observation_row=question_row,
    ) is True


def test_r50_r11_rejects_question_observation_that_hides_p5_readfeel_repair():
    pass_rating = r50.normalize_p7_r50_rating_capture_row_bodyfree(
        review_result=_pass_result(),
        case_row=_case_row(),
    )
    repair_question = r50.normalize_p7_r50_question_need_observation_row_bodyfree(
        question_observation_result=_question_result(primary="not_question_p5_surface_repair_required"),
        case_row=_case_row(),
    )
    with pytest.raises(ValueError):
        r50.assert_p7_r50_rating_vs_question_observation_consistency(
            rating_row=pass_rating,
            question_need_observation_row=repair_question,
        )

    repair_rating = r50.normalize_p7_r50_rating_capture_row_bodyfree(
        review_result=_repair_required_result(),
        case_row=_case_row(),
    )
    question_candidate = r50.normalize_p7_r50_question_need_observation_row_bodyfree(
        question_observation_result=_question_result(
            primary="question_may_reduce_overread_risk",
            ambiguity_kind_refs=["missing_target"],
        ),
        case_row=_case_row(),
    )
    with pytest.raises(ValueError):
        r50.assert_p7_r50_rating_vs_question_observation_consistency(
            rating_row=repair_rating,
            question_need_observation_row=question_candidate,
        )


def test_r50_r11_requires_execution_blocker_row_for_insufficient_material_observation():
    question_row = r50.normalize_p7_r50_question_need_observation_row_bodyfree(
        question_observation_result=_question_result(primary="insufficient_material_execution_blocker"),
        case_row=_case_row(case_role="boundary_no_history_line"),
    )

    with pytest.raises(ValueError):
        r50.assert_p7_r50_rating_vs_question_observation_consistency(
            question_need_observation_row=question_row,
            execution_blocker_rows=[],
        )

    execution_row = r50.build_p7_r50_execution_blocker_row_bodyfree(
        case_row=_case_row(case_role="boundary_no_history_line"),
        execution_blocker_id="r50_question_need_observation_rows_incomplete",
    )
    assert r50.assert_p7_r50_rating_vs_question_observation_consistency(
        question_need_observation_row=question_row,
        execution_blocker_rows=[execution_row],
    ) is True

    rating_row = r50.normalize_p7_r50_rating_capture_row_bodyfree(
        review_result=_pass_result(),
        case_row=_case_row(case_role="boundary_no_history_line"),
    )
    with pytest.raises(ValueError):
        r50.assert_p7_r50_rating_vs_question_observation_consistency(
            rating_row=rating_row,
            question_need_observation_row=question_row,
            execution_blocker_rows=[execution_row],
        )


def test_r50_r11_blocks_when_r10_question_normalizer_is_not_ready():
    blocked_r10 = r50.build_p7_r50_question_need_observation_row_normalizer_bodyfree(
        readfeel_blocker_execution_blocker_ingestion_bodyfree=r50.build_p7_r50_readfeel_blocker_execution_blocker_ingestion_bodyfree(
            rating_row_normalizer_bodyfree=r50.build_p7_r50_rating_row_normalizer_bodyfree(
                reviewer_instruction_rating_form_freeze=r50.build_p7_r50_reviewer_instruction_rating_form_freeze(
                    local_only_body_full_packet_generation_request=r50.build_p7_r50_local_only_body_full_packet_generation_request(
                        review_session_protocol_bodyfree=r50.build_p7_r50_review_session_protocol_bodyfree(
                            local_only_root_explicit_allow_export_preflight=r50.build_p7_r50_local_only_root_explicit_allow_export_denylist_preflight(
                                manual_run_decision_bodyfree=_r3_go(),
                                local_review_root=_VALID_LOCAL_ROOT_REF,
                                explicit_allow_token="WRONG_TOKEN",
                            )
                        )
                    )
                )
            )
        )
    )
    guard = r50.build_p7_r50_rating_question_observation_consistency_guard_bodyfree(
        question_need_observation_row_normalizer_bodyfree=blocked_r10
    )

    assert guard["question_observation_normalizer_status"] == "BLOCKED_BY_R50_9_BLOCKER_INGESTION"
    assert guard["consistency_guard_status"] == "BLOCKED_BY_R50_10_QUESTION_OBSERVATION_NORMALIZER"
    assert guard["rating_question_consistency_guard_ready"] is False
    assert guard["local_only_body_full_generation_allowed"] is False
    assert "r50_explicit_allow_missing" in guard["execution_blocker_ids"]
    assert guard["next_required_step"] == r50.P7_R50_R11_BLOCKED_NEXT_REQUIRED_STEP_REF
    _assert_no_runtime_or_product_completion(guard)


def test_r50_r10_r11_combined_freeze_matches_nested_materials_and_does_not_claim_review_completion():
    combined = r50.build_p7_r50_r10_r11_question_normalizer_consistency_guard_freeze(
        readfeel_blocker_execution_blocker_ingestion_bodyfree=_r9_ready()
    )

    assert r50.assert_p7_r50_r10_r11_question_normalizer_consistency_guard_freeze_contract(combined) is True
    assert combined["schema_version"] == r50.P7_R50_R10_R11_QUESTION_NORMALIZER_CONSISTENCY_GUARD_FREEZE_SCHEMA_VERSION
    assert combined["policy_section"] == "R50-10_R50-11_question_normalizer_consistency_guard_freeze"
    assert combined["question_observation_normalizer_status"] == combined["r10_question_need_observation_row_normalizer"]["question_observation_normalizer_status"]
    assert combined["consistency_guard_status"] == combined["r11_rating_question_observation_consistency_guard"]["consistency_guard_status"]
    assert combined["local_only_body_full_generation_allowed"] is True
    assert combined["actual_manual_review_run_here"] is False
    assert combined["body_full_packet_generated_here"] is False
    assert combined["actual_rating_rows_materialized_here"] is False
    assert combined["actual_blocker_rows_materialized_here"] is False
    assert combined["actual_execution_blocker_rows_materialized_here"] is False
    assert combined["actual_question_need_observation_rows_materialized_here"] is False
    assert combined["p7_complete"] is False
    assert combined["p8_start_allowed"] is False
    assert combined["release_allowed"] is False
    assert combined["implemented_steps"] == list(r50.P7_R50_R11_IMPLEMENTED_STEPS)
    assert combined["not_yet_implemented_steps"] == list(r50.P7_R50_R11_NOT_YET_IMPLEMENTED_STEPS)
    assert combined["next_required_step"] == r50.P7_R50_R11_NEXT_REQUIRED_STEP_REF
    _assert_body_free_no_leak(combined)


def test_r50_r10_r11_contracts_reject_body_free_forbidden_keys_and_drift():
    normalizer = _r10_ready()
    leaked_normalizer = copy.deepcopy(normalizer)
    leaked_normalizer["question_text"] = "Draft question must not appear in R50 body-free material"
    with pytest.raises(ValueError):
        r50.assert_p7_r50_question_need_observation_row_normalizer_bodyfree_contract(leaked_normalizer)

    guard = r50.build_p7_r50_rating_question_observation_consistency_guard_bodyfree(
        question_need_observation_row_normalizer_bodyfree=normalizer
    )
    drifted_guard = copy.deepcopy(guard)
    drifted_guard["p5_weakness_must_not_be_hidden_by_questions"] = False
    with pytest.raises(ValueError):
        r50.assert_p7_r50_rating_question_observation_consistency_guard_bodyfree_contract(drifted_guard)

    question_row = r50.normalize_p7_r50_question_need_observation_row_bodyfree(
        question_observation_result=_question_result(),
        case_row=_case_row(),
    )
    leaked_question_row = copy.deepcopy(question_row)
    leaked_question_row["reviewer_free_text"] = "local-only note must not leave local review"
    with pytest.raises(ValueError):
        r50.assert_p7_r50_question_need_observation_row_bodyfree_contract(leaked_question_row)
