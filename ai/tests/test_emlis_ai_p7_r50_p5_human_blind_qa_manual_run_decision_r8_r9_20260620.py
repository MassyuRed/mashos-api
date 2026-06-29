# -*- coding: utf-8 -*-
"""R50-8/R50-9 tests for P5 human Blind QA manual-run decision.

These tests stop at body-free rating row normalization and blocker ingestion.
They do not run human review, do not materialize actual 24-case rows, do not
write body-full packets, do not touch API/DB/RN contracts, do not start P8,
do not complete P7, and do not claim release readiness.
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
    "api_db_rn_response_key_changed_here",
    "question_api_implemented",
    "question_db_schema_implemented",
    "question_rn_ui_implemented",
    "question_response_key_implemented",
    "question_trigger_logic_implemented",
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


def test_r50_received_source_contains_r0_to_r7_before_r8_r9_progression():
    assert r50.P7_R50_R7_IMPLEMENTED_STEPS[-1] == "R50-7_reviewer_instruction_rating_form_freeze"
    assert r50.P7_R50_R7_NOT_YET_IMPLEMENTED_STEPS[0] == "R50-8_rating_row_normalizer"
    assert r50.P7_R50_R7_NEXT_REQUIRED_STEP_REF == "R50-8_rating_row_normalizer"
    assert r50.P7_R50_R8_NEXT_REQUIRED_STEP_REF == "R50-9_readfeel_blocker_execution_blocker_ingestion"
    assert r50.P7_R50_R9_NEXT_REQUIRED_STEP_REF == "R50-10_question_need_observation_row_normalizer"


def test_r50_r8_builds_rating_row_normalizer_policy_without_materializing_actual_rows():
    normalizer = _r8_ready()

    assert r50.assert_p7_r50_rating_row_normalizer_bodyfree_contract(normalizer) is True
    assert normalizer["schema_version"] == r50.P7_R50_RATING_ROW_NORMALIZER_BODYFREE_SCHEMA_VERSION
    assert normalizer["policy_section"] == "R50-8_rating_row_normalizer"
    assert normalizer["instruction_form_status"] == "READY_FOR_REVIEWER_INSTRUCTION_AND_RATING_FORM"
    assert normalizer["normalizer_status"] == "READY_FOR_RATING_ROW_NORMALIZATION"
    assert normalizer["normalizer_ready"] is True
    assert normalizer["required_case_count"] == 24
    assert normalizer["rating_row_schema_version"] == r50.P7_R50_RATING_CAPTURE_ROW_BODYFREE_SCHEMA_VERSION
    assert normalizer["r48_rating_row_schema_version_ref"] == r50.P7_R48_P5_RATING_ROW_BODYFREE_SCHEMA_VERSION
    assert normalizer["rating_row_required_field_refs"] == list(r50.P7_R50_RATING_CAPTURE_ROW_BODYFREE_REQUIRED_FIELD_REFS)
    assert normalizer["rating_axis_refs"] == list(r50.P5_HUMAN_BLIND_QA_RATING_AXES)
    assert normalizer["rating_axis_target_refs"] == dict(r50.P5_HUMAN_BLIND_QA_TARGETS)
    assert normalizer["rating_score_min"] == 0.0
    assert normalizer["rating_score_max"] == 1.0
    assert normalizer["missing_axis_scores_pass_allowed"] is False
    assert normalizer["extra_rating_axis_allowed"] is False
    assert normalizer["machine_auto_score_allowed"] is False
    assert normalizer["readfeel_auto_estimation_allowed"] is False
    assert normalizer["machine_metrics_used_for_readfeel_allowed"] is False
    assert normalizer["reviewer_free_text_bodyfree_allowed"] is False
    assert normalizer["allowed_verdict_refs"] == ["PASS", "YELLOW", "REPAIR_REQUIRED", "RED"]
    assert normalizer["blocked_or_not_reviewable_must_use_execution_blocker_row"] is True
    assert normalizer["red_or_repair_requires_blocker"] is True
    assert normalizer["pass_requires_targets_and_no_blockers"] is True
    assert normalizer["rating_rows_are_bodyfree"] is True
    assert normalizer["actual_rating_rows_materialized_here"] is False
    assert normalizer["actual_blocker_rows_materialized_here"] is False
    assert normalizer["actual_execution_blocker_rows_materialized_here"] is False
    assert normalizer["next_required_step"] == r50.P7_R50_R8_NEXT_REQUIRED_STEP_REF
    assert normalizer["implemented_steps"] == list(r50.P7_R50_R8_IMPLEMENTED_STEPS)
    assert normalizer["not_yet_implemented_steps"] == list(r50.P7_R50_R8_NOT_YET_IMPLEMENTED_STEPS)
    _assert_no_runtime_or_product_completion(normalizer)


def test_r50_r8_normalizes_pass_rating_row_as_r48_compatible_bodyfree_row():
    row = r50.normalize_p7_r50_rating_capture_row_bodyfree(
        review_result=_pass_result(),
        case_row=_case_row(),
        reviewer_ref="reviewer_bodyfree_001",
        reviewed_at="2026-06-20T12:00:00+09:00",
    )

    assert r50.assert_p7_r50_rating_capture_row_bodyfree_contract(row) is True
    assert row["schema_version"] == r50.P7_R50_RATING_CAPTURE_ROW_BODYFREE_SCHEMA_VERSION
    assert row["review_session_id"] == "p7_r50_review_session_001"
    assert row["packet_ref_id"] == "packet_blind_001"
    assert row["blind_case_id"] == "blind_case_001"
    assert row["case_ref_id"] == "case_history_line_eligible_001"
    assert row["family"] == "history_line_eligible_input"
    assert row["case_role"] == "positive_history_line"
    assert row["axis_scores"] == {axis: 1.0 for axis in r50.P5_HUMAN_BLIND_QA_RATING_AXES}
    assert row["verdict"] == "PASS"
    assert row["sanitized_reason_ids"] == []
    assert row["blocker_ids"] == []
    assert row["reviewer_free_text_included"] is False
    assert row["body_removed"] is False
    assert row["body_free"] is True
    _assert_body_free_no_leak(row)


def test_r50_r8_rejects_missing_extra_axes_machine_score_reviewer_text_and_body_leak():
    missing_axis = _pass_result()
    missing_axis["axis_scores"].pop("non_shallow_repeat")
    with pytest.raises(ValueError):
        r50.normalize_p7_r50_rating_capture_row_bodyfree(
            review_result=missing_axis,
            case_row=_case_row(),
        )

    extra_axis = _pass_result()
    extra_axis["axis_scores"]["extra_axis"] = 1.0
    with pytest.raises(ValueError):
        r50.normalize_p7_r50_rating_capture_row_bodyfree(
            review_result=extra_axis,
            case_row=_case_row(),
        )

    machine_score = _pass_result(machine_auto_score_used=True)
    with pytest.raises(ValueError):
        r50.normalize_p7_r50_rating_capture_row_bodyfree(
            review_result=machine_score,
            case_row=_case_row(),
        )

    reviewer_text = _pass_result(reviewer_free_text_included=True)
    with pytest.raises(ValueError):
        r50.normalize_p7_r50_rating_capture_row_bodyfree(
            review_result=reviewer_text,
            case_row=_case_row(),
        )

    body_leak = _pass_result(raw_input="body text must not enter body-free rating input")
    with pytest.raises(ValueError):
        r50.normalize_p7_r50_rating_capture_row_bodyfree(
            review_result=body_leak,
            case_row=_case_row(),
        )


def test_r50_r8_rejects_pass_below_target_or_pass_with_blocker_or_repair_without_blocker():
    below_target_pass = _pass_result()
    below_target_pass["axis_scores"]["history_connection_naturalness"] = 0.89
    with pytest.raises(ValueError):
        r50.normalize_p7_r50_rating_capture_row_bodyfree(
            review_result=below_target_pass,
            case_row=_case_row(),
        )

    pass_with_blocker = _pass_result(
        sanitized_reason_ids=["p5_history_connection_too_generic"],
        blocker_ids=["p5_history_connection_too_generic"],
    )
    with pytest.raises(ValueError):
        r50.normalize_p7_r50_rating_capture_row_bodyfree(
            review_result=pass_with_blocker,
            case_row=_case_row(),
        )

    repair_without_blocker = _repair_required_result(blocker_ids=[])
    with pytest.raises(ValueError):
        r50.normalize_p7_r50_rating_capture_row_bodyfree(
            review_result=repair_without_blocker,
            case_row=_case_row(),
        )


def test_r50_r8_blocks_when_r7_instruction_form_is_not_ready():
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
    normalizer = r50.build_p7_r50_rating_row_normalizer_bodyfree(
        reviewer_instruction_rating_form_freeze=blocked_r7
    )

    assert normalizer["instruction_form_status"] == "BLOCKED_BY_R50_6_PACKET_GENERATION_REQUEST"
    assert normalizer["normalizer_status"] == "BLOCKED_BY_R50_7_REVIEWER_INSTRUCTION_RATING_FORM"
    assert normalizer["normalizer_ready"] is False
    assert normalizer["local_only_body_full_generation_allowed"] is False
    assert "r50_explicit_allow_missing" in normalizer["execution_blocker_ids"]
    assert normalizer["next_required_step"] == r50.P7_R50_R8_BLOCKED_NEXT_REQUIRED_STEP_REF
    _assert_no_runtime_or_product_completion(normalizer)


def test_r50_r9_builds_readfeel_blocker_row_from_repair_rating_without_execution_blocker_mix():
    rating_row = r50.normalize_p7_r50_rating_capture_row_bodyfree(
        review_result=_repair_required_result(),
        case_row=_case_row(),
    )
    blocker_row = r50.build_p7_r50_readfeel_blocker_row_bodyfree(
        case_row=rating_row,
        blocker_id=rating_row["blocker_ids"][0],
        blocker_kind="REPAIR_REQUIRED",
        sanitized_reason_ids=rating_row["sanitized_reason_ids"],
    )

    assert r50.assert_p7_r50_readfeel_blocker_row_bodyfree_contract(blocker_row) is True
    assert blocker_row["schema_version"] == r50.P7_R50_READFEEL_BLOCKER_ROW_BODYFREE_SCHEMA_VERSION
    assert blocker_row["blocker_id"] == "p5_history_connection_too_generic"
    assert blocker_row["blocker_kind"] == "REPAIR_REQUIRED"
    assert blocker_row["blocker_kind"] != "EXECUTION_BLOCKER"
    assert blocker_row["blocker_status"] == "OPEN"
    assert blocker_row["sanitized_reason_ids"] == ["p5_history_connection_too_generic"]
    assert blocker_row["reviewer_free_text_included"] is False
    assert blocker_row["body_free"] is True
    _assert_body_free_no_leak(blocker_row)


def test_r50_r9_builds_execution_blocker_row_without_assigning_readfeel_verdict():
    execution_row = r50.build_p7_r50_execution_blocker_row_bodyfree(
        case_row=_case_row(case_role="boundary_no_history_line"),
        execution_blocker_id="r50_rating_rows_incomplete",
    )

    assert r50.assert_p7_r50_execution_blocker_row_bodyfree_contract(execution_row) is True
    assert execution_row["schema_version"] == r50.P7_R50_EXECUTION_BLOCKER_ROW_BODYFREE_SCHEMA_VERSION
    assert execution_row["execution_blocker_id"] == "r50_rating_rows_incomplete"
    assert execution_row["execution_blocker_kind"] == "RATING"
    assert execution_row["execution_blocker_status"] == "OPEN"
    assert execution_row["readfeel_verdict_not_assigned"] is True
    assert "verdict" not in execution_row
    assert "blocker_id" not in execution_row
    assert execution_row["body_free"] is True
    _assert_body_free_no_leak(execution_row)


def test_r50_r9_builds_ingestion_policy_and_separates_readfeel_from_execution_blockers():
    ingestion = r50.build_p7_r50_readfeel_blocker_execution_blocker_ingestion_bodyfree(
        rating_row_normalizer_bodyfree=_r8_ready()
    )

    assert r50.assert_p7_r50_readfeel_blocker_execution_blocker_ingestion_bodyfree_contract(ingestion) is True
    assert ingestion["schema_version"] == r50.P7_R50_READFEEL_EXECUTION_BLOCKER_INGESTION_BODYFREE_SCHEMA_VERSION
    assert ingestion["policy_section"] == "R50-9_readfeel_blocker_execution_blocker_ingestion"
    assert ingestion["normalizer_status"] == "READY_FOR_RATING_ROW_NORMALIZATION"
    assert ingestion["blocker_ingestion_status"] == "READY_FOR_READFEEL_AND_EXECUTION_BLOCKER_INGESTION"
    assert ingestion["readfeel_blocker_row_schema_version"] == r50.P7_R50_READFEEL_BLOCKER_ROW_BODYFREE_SCHEMA_VERSION
    assert ingestion["execution_blocker_row_schema_version"] == r50.P7_R50_EXECUTION_BLOCKER_ROW_BODYFREE_SCHEMA_VERSION
    assert ingestion["readfeel_blocker_row_required_field_refs"] == list(r50.P7_R50_READFEEL_BLOCKER_ROW_BODYFREE_REQUIRED_FIELD_REFS)
    assert ingestion["execution_blocker_row_required_field_refs"] == list(r50.P7_R50_EXECUTION_BLOCKER_ROW_BODYFREE_REQUIRED_FIELD_REFS)
    assert ingestion["readfeel_blocker_id_refs"] == list(r50.P7_R48_READFEEL_BLOCKER_ID_REFS)
    assert ingestion["execution_blocker_id_refs"] == list(r50.P7_R50_EXECUTION_BLOCKER_ID_REFS)
    assert ingestion["readfeel_blocker_kind_refs"] == list(r50.P7_R48_P5_BLOCKER_KINDS)
    assert ingestion["execution_blocker_kind_refs"] == list(r50.P7_R50_EXECUTION_BLOCKER_KIND_REFS)
    assert ingestion["readfeel_and_execution_blockers_separated"] is True
    assert ingestion["execution_blockers_do_not_assign_readfeel_verdict"] is True
    assert ingestion["execution_blocker_cases_do_not_create_rating_rows"] is True
    assert ingestion["rating_missing_maps_to_execution_blocker_not_red"] is True
    assert ingestion["local_root_missing_maps_to_execution_blocker_not_red"] is True
    assert ingestion["disposal_failed_maps_to_execution_blocker_not_red"] is True
    assert ingestion["body_free_leak_maps_to_execution_blocker_not_red"] is True
    assert ingestion["readfeel_blocker_row_builder_ready"] is True
    assert ingestion["execution_blocker_row_builder_ready"] is True
    assert ingestion["actual_blocker_rows_materialized_here"] is False
    assert ingestion["actual_execution_blocker_rows_materialized_here"] is False
    assert ingestion["next_required_step"] == r50.P7_R50_R9_NEXT_REQUIRED_STEP_REF
    assert ingestion["implemented_steps"] == list(r50.P7_R50_R9_IMPLEMENTED_STEPS)
    assert ingestion["not_yet_implemented_steps"] == list(r50.P7_R50_R9_NOT_YET_IMPLEMENTED_STEPS)
    _assert_no_runtime_or_product_completion(ingestion)


def test_r50_r9_blocks_when_r8_normalizer_is_not_ready():
    blocked_r8 = r50.build_p7_r50_rating_row_normalizer_bodyfree(
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
    ingestion = r50.build_p7_r50_readfeel_blocker_execution_blocker_ingestion_bodyfree(
        rating_row_normalizer_bodyfree=blocked_r8
    )

    assert ingestion["normalizer_status"] == "BLOCKED_BY_R50_7_REVIEWER_INSTRUCTION_RATING_FORM"
    assert ingestion["blocker_ingestion_status"] == "BLOCKED_BY_R50_8_RATING_ROW_NORMALIZER"
    assert ingestion["readfeel_blocker_row_builder_ready"] is False
    assert ingestion["execution_blocker_row_builder_ready"] is False
    assert ingestion["local_only_body_full_generation_allowed"] is False
    assert "r50_explicit_allow_missing" in ingestion["execution_blocker_ids"]
    assert ingestion["next_required_step"] == r50.P7_R50_R9_BLOCKED_NEXT_REQUIRED_STEP_REF
    _assert_no_runtime_or_product_completion(ingestion)


def test_r50_r8_r9_combined_freeze_matches_nested_materials_and_does_not_claim_review_completion():
    combined = r50.build_p7_r50_r8_r9_rating_blocker_ingestion_freeze(
        reviewer_instruction_rating_form_freeze=_r7_ready()
    )

    assert r50.assert_p7_r50_r8_r9_rating_blocker_ingestion_freeze_contract(combined) is True
    assert combined["schema_version"] == r50.P7_R50_R8_R9_RATING_BLOCKER_INGESTION_FREEZE_SCHEMA_VERSION
    assert combined["policy_section"] == "R50-8_R50-9_rating_blocker_ingestion_freeze"
    assert combined["normalizer_status"] == combined["r8_rating_row_normalizer"]["normalizer_status"]
    assert combined["blocker_ingestion_status"] == combined["r9_readfeel_blocker_execution_blocker_ingestion"]["blocker_ingestion_status"]
    assert combined["local_only_body_full_generation_allowed"] is True
    assert combined["actual_manual_review_run_here"] is False
    assert combined["body_full_packet_generated_here"] is False
    assert combined["actual_rating_rows_materialized_here"] is False
    assert combined["actual_blocker_rows_materialized_here"] is False
    assert combined["actual_execution_blocker_rows_materialized_here"] is False
    assert combined["p7_complete"] is False
    assert combined["p8_start_allowed"] is False
    assert combined["release_allowed"] is False
    assert combined["implemented_steps"] == list(r50.P7_R50_R9_IMPLEMENTED_STEPS)
    assert combined["not_yet_implemented_steps"] == list(r50.P7_R50_R9_NOT_YET_IMPLEMENTED_STEPS)
    assert combined["next_required_step"] == r50.P7_R50_R9_NEXT_REQUIRED_STEP_REF
    _assert_body_free_no_leak(combined)


def test_r50_r8_r9_contracts_reject_body_free_forbidden_keys_and_drift():
    normalizer = _r8_ready()
    leaked_normalizer = copy.deepcopy(normalizer)
    leaked_normalizer["reviewer_free_text"] = "free text must remain local-only"
    with pytest.raises(ValueError):
        r50.assert_p7_r50_rating_row_normalizer_bodyfree_contract(leaked_normalizer)

    ingestion = r50.build_p7_r50_readfeel_blocker_execution_blocker_ingestion_bodyfree(
        rating_row_normalizer_bodyfree=normalizer
    )
    drifted_ingestion = copy.deepcopy(ingestion)
    drifted_ingestion["execution_blockers_do_not_assign_readfeel_verdict"] = False
    with pytest.raises(ValueError):
        r50.assert_p7_r50_readfeel_blocker_execution_blocker_ingestion_bodyfree_contract(drifted_ingestion)

    execution_row = r50.build_p7_r50_execution_blocker_row_bodyfree(
        case_row=_case_row(),
        execution_blocker_id="r50_local_review_root_missing",
    )
    leaked_execution_row = copy.deepcopy(execution_row)
    leaked_execution_row["local_absolute_path"] = _VALID_LOCAL_ROOT_REF
    with pytest.raises(ValueError):
        r50.assert_p7_r50_execution_blocker_row_bodyfree_contract(leaked_execution_row)
