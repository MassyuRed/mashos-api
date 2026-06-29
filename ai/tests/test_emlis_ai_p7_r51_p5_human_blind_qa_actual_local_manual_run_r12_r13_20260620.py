# -*- coding: utf-8 -*-
from __future__ import annotations

import json
from copy import deepcopy
from functools import lru_cache

import pytest

import emlis_ai_p7_r51_p5_human_blind_qa_actual_local_manual_run as r51


FORBIDDEN_DUMP_TOKENS = (
    '"raw_input":',
    '"raw_answer":',
    '"comment_text":',
    '"comment_text_body":',
    '"returned_emlis_surface":',
    '"bounded_owned_history_review_surface":',
    '"current_input_review_surface":',
    '"reviewer_free_text":',
    '"reviewer_note":',
    '"reviewer_notes":',
    '"question_text":',
    '"draft_question_text":',
    '"question_body":',
    '"local_absolute_path":',
    '"body_content_hash":',
    '"packet_content_hash":',
    '"terminal_output": "',
    '"stdout":',
    '"stderr":',
    '"traceback":',
)
FORBIDDEN_TRUE_TOKENS_BASE = (
    '"release_allowed": true',
    '"p7_complete": true',
    '"p8_start_allowed": true',
    '"hold004_close_allowed": true',
    '"question_api_implemented": true',
    '"question_db_schema_implemented": true',
    '"question_rn_ui_implemented": true',
    '"question_response_key_implemented": true',
    '"question_trigger_logic_implemented": true',
    '"question_trigger_logic_implemented_here": true',
    '"body_full_packet_generated_here": true',
    '"actual_body_full_packet_generated_here": true',
    '"actual_disposal_receipt_materialized_here": true',
    '"disposal_receipt_materialized_here": true',
    '"post_review_summary_materialized_here": true',
    '"p5_human_blind_qa_confirmed": true',
    '"p5_human_blind_qa_confirmed_candidate": true',
    '"p5_confirmed_candidate_allowed_after_protocol": true',
    '"p5_repair_return_candidate_allowed_after_protocol": true',
    '"p6_limited_human_readfeel_start_allowed": true',
    '"p8_question_design_material_candidate": true',
    '"full_backend_suite_green_confirmed": true',
)


def _assert_bodyfree_no_leak_or_promotion(material: dict[str, object]) -> None:
    dumped = json.dumps(material, ensure_ascii=False, sort_keys=True).lower()
    for forbidden in FORBIDDEN_DUMP_TOKENS:
        assert forbidden not in dumped
    for forbidden in FORBIDDEN_TRUE_TOKENS_BASE:
        assert forbidden not in dumped


@lru_cache(maxsize=1)
def _cached_purge_plan() -> tuple[dict[str, object]]:
    return (r51.build_p7_r51_default_local_only_purge_plan_bodyfree(),)


def _purge_plan() -> dict[str, object]:
    return deepcopy(_cached_purge_plan()[0])


@lru_cache(maxsize=1)
def _cached_envelope() -> tuple[dict[str, object]]:
    envelope = r51.build_p7_r51_r0_r3_preflight_session_envelope_chain(
        local_review_root="/tmp/cocolon_r51_local_review",
        explicit_allow_token=r51.P7_R51_EXPLICIT_ACTUAL_LOCAL_MANUAL_RUN_ALLOW_TOKEN_REF,
        purge_plan=_purge_plan(),
    )
    assert r51.assert_p7_r51_actual_review_session_envelope_bodyfree_contract(envelope) is True
    return (envelope,)


def _envelope() -> dict[str, object]:
    return deepcopy(_cached_envelope()[0])


@lru_cache(maxsize=1)
def _cached_manifest() -> tuple[dict[str, object]]:
    manifest = r51.build_p7_r51_24_case_manifest_freeze_bodyfree(actual_review_session_envelope=_envelope())
    assert r51.assert_p7_r51_24_case_manifest_freeze_bodyfree_contract(manifest) is True
    return (manifest,)


def _manifest() -> dict[str, object]:
    return deepcopy(_cached_manifest()[0])


@lru_cache(maxsize=1)
def _cached_freeze() -> tuple[dict[str, object]]:
    freeze = r51.build_p7_r51_r0_r7_reviewer_instruction_rating_form_chain(
        local_review_root="/tmp/cocolon_r51_local_review",
        explicit_allow_token=r51.P7_R51_EXPLICIT_ACTUAL_LOCAL_MANUAL_RUN_ALLOW_TOKEN_REF,
        purge_plan=_purge_plan(),
    )
    assert r51.assert_p7_r51_reviewer_instruction_rating_form_freeze_bodyfree_contract(freeze) is True
    return (freeze,)


def _freeze() -> dict[str, object]:
    return deepcopy(_cached_freeze()[0])


def _base_pass_review_rows() -> list[dict[str, object]]:
    axis_scores = {axis: 1.0 for axis in r51.P5_HUMAN_BLIND_QA_RATING_AXES}
    rows: list[dict[str, object]] = []
    for case in _manifest()["case_rows"]:
        case_row = dict(case)
        rows.append(
            {
                "blind_case_id": case_row["blind_case_id"],
                "axis_scores": dict(axis_scores),
                "verdict": "PASS",
                "sanitized_reason_ids": [],
                "blocker_ids": [],
                "question_need_primary_class": "no_question_needed_emlis_can_observe",
                "ambiguity_kind_refs": ["no_material_ambiguity"],
                "one_question_fit_ref": "not_needed",
                "repair_required_refs": ["no_repair_required"],
                "reviewer_free_text_included": False,
                "question_text_included": False,
                "draft_question_text_included": False,
                "machine_auto_score_used": False,
                "machine_metrics_used_for_readfeel": False,
            }
        )
    return rows


def _question_candidate_review_rows() -> list[dict[str, object]]:
    rows = _base_pass_review_rows()
    rows[0].update(
        {
            "question_need_primary_class": "question_may_reduce_overread_risk",
            "ambiguity_kind_refs": ["missing_target"],
            "one_question_fit_ref": "fits_one_question",
            "repair_required_refs": ["no_repair_required"],
        }
    )
    return rows


def _consistent_repair_review_rows() -> list[dict[str, object]]:
    rows = _base_pass_review_rows()
    rows[0].update(
        {
            "axis_scores": {axis: 0.75 for axis in r51.P5_HUMAN_BLIND_QA_RATING_AXES},
            "verdict": "REPAIR_REQUIRED",
            "sanitized_reason_ids": ["p5_history_connection_too_generic"],
            "blocker_ids": ["p5_history_connection_too_generic"],
            "question_need_primary_class": "not_question_p5_surface_repair_required",
            "ambiguity_kind_refs": ["history_connection_basis_unclear"],
            "one_question_fit_ref": "repair_required_not_question",
            "repair_required_refs": ["p5_surface_repair_required"],
        }
    )
    return rows


def _repair_hidden_by_question_review_rows() -> list[dict[str, object]]:
    rows = _base_pass_review_rows()
    rows[0].update(
        {
            "axis_scores": {axis: 0.75 for axis in r51.P5_HUMAN_BLIND_QA_RATING_AXES},
            "verdict": "REPAIR_REQUIRED",
            "sanitized_reason_ids": ["p5_history_connection_too_generic"],
            "blocker_ids": ["p5_history_connection_too_generic"],
            "question_need_primary_class": "question_may_reduce_overread_risk",
            "ambiguity_kind_refs": ["missing_target"],
            "one_question_fit_ref": "fits_one_question",
            "repair_required_refs": ["no_repair_required"],
        }
    )
    return rows


def _creepy_hidden_by_question_review_rows() -> list[dict[str, object]]:
    rows = _base_pass_review_rows()
    rows[0].update(
        {
            "axis_scores": {
                "history_connection_naturalness": 0.75,
                "creepy_absence": 0.0,
                "overclaim_absence": 0.75,
                "self_blame_non_amplification": 0.75,
                "wants_more_input_or_accumulation": 0.75,
                "non_shallow_repeat": 0.75,
            },
            "verdict": "RED",
            "sanitized_reason_ids": ["p5_history_creepy_or_surveillance_feeling"],
            "blocker_ids": ["p5_history_creepy_or_surveillance_feeling"],
            "question_need_primary_class": "question_may_reduce_overread_risk",
            "ambiguity_kind_refs": ["history_connection_basis_unclear"],
            "one_question_fit_ref": "fits_one_question",
            "repair_required_refs": ["no_repair_required"],
        }
    )
    return rows


def _r8_from_rows(rows: list[dict[str, object]]) -> dict[str, object]:
    r8 = r51.build_p7_r51_actual_human_review_run_bodyfree(
        reviewer_instruction_rating_form_freeze=_freeze(),
        case_manifest_freeze=_manifest(),
        review_result_rows=rows,
        reviewer_ref="pseudonymous_reviewer_r51_contract",
        reviewed_at="2026-06-20T00:00:00+09:00",
    )
    assert r51.assert_p7_r51_actual_human_review_run_bodyfree_contract(r8) is True
    return r8


def _r9_r10_r11_from_rows(rows: list[dict[str, object]]) -> tuple[dict[str, object], dict[str, object], dict[str, object]]:
    r8 = _r8_from_rows(rows)
    r9 = r51.build_p7_r51_rating_row_normalizer_bodyfree(actual_human_review_run=r8)
    assert r51.assert_p7_r51_rating_row_normalizer_bodyfree_contract(r9) is True
    r10 = r51.build_p7_r51_readfeel_blocker_execution_blocker_ingestion_bodyfree(
        rating_row_normalizer_bodyfree=r9
    )
    assert r51.assert_p7_r51_readfeel_blocker_execution_blocker_ingestion_bodyfree_contract(r10) is True
    r11 = r51.build_p7_r51_question_need_observation_row_normalizer_bodyfree(
        actual_human_review_run=r8,
        readfeel_blocker_execution_blocker_ingestion_bodyfree=r10,
    )
    assert r51.assert_p7_r51_question_need_observation_row_normalizer_bodyfree_contract(r11) is True
    return r9, r10, r11


def _r12_from_rows(rows: list[dict[str, object]]) -> dict[str, object]:
    r9, r10, r11 = _r9_r10_r11_from_rows(rows)
    r12 = r51.build_p7_r51_rating_question_observation_consistency_guard_bodyfree(
        r9_rating_row_normalizer_bodyfree=r9,
        r10_readfeel_blocker_execution_blocker_ingestion_bodyfree=r10,
        r11_question_need_observation_row_normalizer_bodyfree=r11,
    )
    assert r51.assert_p7_r51_rating_question_observation_consistency_guard_bodyfree_contract(r12) is True
    return r12


@lru_cache(maxsize=1)
def _cached_r12_pass() -> tuple[dict[str, object]]:
    return (_r12_from_rows(_base_pass_review_rows()),)


def _r12_pass() -> dict[str, object]:
    return deepcopy(_cached_r12_pass()[0])


def test_r51_r12_clean_rating_and_question_rows_pass_consistency_guard_without_starting_p8() -> None:
    r12 = _r12_pass()

    assert r12["schema_version"] == r51.P7_R51_RATING_QUESTION_OBSERVATION_CONSISTENCY_GUARD_SCHEMA_VERSION
    assert set(r12) == set(r51.P7_R51_RATING_QUESTION_OBSERVATION_CONSISTENCY_GUARD_BODYFREE_REQUIRED_FIELD_REFS)
    assert r12["policy_section"] == "R51-12_rating_question_observation_consistency_guard"
    assert r12["review_session_status"] == "R51_RATING_QUESTION_OBSERVATION_CONSISTENCY_GUARD_READY"
    assert r12["rating_question_consistency_guard_status"] == "READY_FOR_PAUSE_ABORT_EXPIRATION_PROTOCOL"
    assert r12["next_required_step"] == r51.P7_R51_R12_NEXT_REQUIRED_STEP_REF
    assert r12["required_case_count"] == 24
    assert r12["rating_row_count"] == 24
    assert r12["question_observation_row_count"] == 24
    assert r12["consistency_issue_count"] == 0
    assert r12["consistency_issue_rows"] == []
    assert r12["rating_question_case_ref_sets_match"] is True
    assert r12["all_required_rows_present"] is True
    assert r12["p5_weakness_not_hidden_by_question_candidate"] is True
    assert r12["actual_human_review_run_here"] is True
    assert r12["actual_rating_rows_materialized_here"] is True
    assert r12["actual_question_need_observation_rows_materialized_here"] is True
    assert r12["p8_question_design_material_candidate"] is False
    assert r12["p8_start_allowed"] is False
    assert r12["release_allowed"] is False
    assert tuple(r12["implemented_steps"]) == r51.P7_R51_R12_IMPLEMENTED_STEPS
    assert tuple(r12["not_yet_implemented_steps"]) == r51.P7_R51_R12_NOT_YET_IMPLEMENTED_STEPS
    _assert_bodyfree_no_leak_or_promotion(r12)


def test_r51_r12_question_candidate_is_only_bodyfree_material_candidate_and_not_p8_start() -> None:
    r12 = _r12_from_rows(_question_candidate_review_rows())

    assert r12["rating_question_consistency_guard_status"] == "READY_FOR_PAUSE_ABORT_EXPIRATION_PROTOCOL"
    assert r12["consistency_issue_count"] == 0
    assert r12["question_candidate_allowed_case_count"] >= 1
    assert r12["p8_question_material_candidate_allowed_by_consistency"] is True
    assert r12["p8_question_design_material_candidate"] is False
    assert r12["p8_question_implementation_spec_finalized_here"] is False
    assert r12["question_trigger_logic_implemented_here"] is False
    assert r12["p8_start_allowed"] is False
    _assert_bodyfree_no_leak_or_promotion(r12)


def test_r51_r12_consistent_repair_observation_marks_p5_repair_need_without_hiding_it_as_question() -> None:
    r12 = _r12_from_rows(_consistent_repair_review_rows())

    assert r12["rating_question_consistency_guard_status"] == "READY_FOR_PAUSE_ABORT_EXPIRATION_PROTOCOL"
    assert r12["consistency_issue_count"] == 0
    assert r12["p5_repair_return_required_by_consistency"] is True
    assert r12["p5_weakness_not_hidden_by_question_candidate"] is True
    assert r12["p5_repair_return_candidate"] is False
    assert r12["p8_question_design_material_candidate"] is False
    assert r12["p8_start_allowed"] is False
    _assert_bodyfree_no_leak_or_promotion(r12)


def test_r51_r12_blocks_repair_or_creepy_cases_escaping_to_question_candidate() -> None:
    repair_hidden = _r12_from_rows(_repair_hidden_by_question_review_rows())
    assert repair_hidden["rating_question_consistency_guard_status"] == "BLOCKED_BY_RATING_QUESTION_OBSERVATION_INCONSISTENCY"
    assert repair_hidden["consistency_issue_count"] >= 1
    assert repair_hidden["consistency_issue_id_counts"]["r51_red_or_repair_required_routed_to_question_candidate"] >= 1
    assert repair_hidden["p5_weakness_not_hidden_by_question_candidate"] is False
    assert repair_hidden["execution_blocker_ids"] == ["r51_rating_question_observation_inconsistent"]
    assert repair_hidden["next_required_step"] == r51.P7_R51_R12_BLOCKED_NEXT_REQUIRED_STEP_REF
    _assert_bodyfree_no_leak_or_promotion(repair_hidden)

    creepy_hidden = _r12_from_rows(_creepy_hidden_by_question_review_rows())
    assert creepy_hidden["rating_question_consistency_guard_status"] == "BLOCKED_BY_RATING_QUESTION_OBSERVATION_INCONSISTENCY"
    assert creepy_hidden["consistency_issue_id_counts"]["r51_creepy_or_boundary_blocker_routed_to_question_candidate"] >= 1
    assert creepy_hidden["consistency_issue_id_counts"]["r51_red_or_repair_required_routed_to_question_candidate"] >= 1
    assert creepy_hidden["p5_weakness_not_hidden_by_question_candidate"] is False
    _assert_bodyfree_no_leak_or_promotion(creepy_hidden)


def test_r51_r12_rejects_question_logic_promotion_and_body_payload_mutations() -> None:
    r12 = _r12_pass()

    promoted = deepcopy(r12)
    promoted["question_trigger_logic_implemented_here"] = True
    with pytest.raises(ValueError):
        r51.assert_p7_r51_rating_question_observation_consistency_guard_bodyfree_contract(promoted)

    with_body = deepcopy(r12)
    with_body["raw_input"] = "body must not enter R51-12"
    with pytest.raises(ValueError):
        r51.assert_p7_r51_rating_question_observation_consistency_guard_bodyfree_contract(with_body)

    p8_started = deepcopy(r12)
    p8_started["p8_question_design_material_candidate"] = True
    with pytest.raises(ValueError):
        r51.assert_p7_r51_rating_question_observation_consistency_guard_bodyfree_contract(p8_started)


def test_r51_r13_completed_review_requires_purge_path_without_running_disposal_or_summary() -> None:
    protocol = r51.build_p7_r51_pause_abort_expiration_protocol_bodyfree(
        rating_question_observation_consistency_guard_bodyfree=_r12_pass(),
        review_lifecycle_status="REVIEW_COMPLETED",
        body_full_packet_age_hours=1,
        reviewer_notes_age_hours=1,
    )

    assert protocol["schema_version"] == r51.P7_R51_PAUSE_ABORT_EXPIRATION_PROTOCOL_SCHEMA_VERSION
    assert set(protocol) == set(r51.P7_R51_PAUSE_ABORT_EXPIRATION_PROTOCOL_BODYFREE_REQUIRED_FIELD_REFS)
    assert protocol["policy_section"] == "R51-13_pause_abort_expiration_protocol"
    assert protocol["review_session_status"] == "R51_PAUSE_ABORT_EXPIRATION_PROTOCOL_READY"
    assert protocol["pause_abort_expiration_protocol_status"] == "READY_FOR_BODY_FULL_PACKET_REVIEWER_NOTES_PURGE"
    assert protocol["review_lifecycle_status"] == "REVIEW_COMPLETED"
    assert protocol["next_required_step"] == r51.P7_R51_R13_NEXT_REQUIRED_STEP_REF
    assert protocol["body_full_packet_purge_required"] is True
    assert protocol["reviewer_forms_purge_required"] is True
    assert protocol["reviewer_notes_purge_required"] is True
    assert protocol["purge_required_before_summary"] is True
    assert protocol["actual_disposal_run_here"] is False
    assert protocol["actual_disposal_receipt_materialized_here"] is False
    assert protocol["post_review_summary_materialized_here"] is False
    assert tuple(protocol["implemented_steps"]) == r51.P7_R51_R13_IMPLEMENTED_STEPS
    assert tuple(protocol["not_yet_implemented_steps"]) == r51.P7_R51_R13_NOT_YET_IMPLEMENTED_STEPS
    _assert_bodyfree_no_leak_or_promotion(protocol)


def test_r51_r13_pause_keeps_retention_clock_running_without_purge_yet_when_not_expired() -> None:
    protocol = r51.build_p7_r51_pause_abort_expiration_protocol_bodyfree(
        rating_question_observation_consistency_guard_bodyfree=_r12_pass(),
        review_lifecycle_status="REVIEW_PAUSED",
        body_full_packet_age_hours=1,
        reviewer_notes_age_hours=1,
    )

    assert protocol["pause_abort_expiration_protocol_status"] == "PAUSED_RETENTION_CLOCK_STILL_RUNNING"
    assert protocol["review_lifecycle_status"] == "REVIEW_PAUSED"
    assert protocol["retention_clock_stops_on_pause"] is False
    assert protocol["review_pause_does_not_stop_retention_deadline"] is True
    assert protocol["body_full_packet_retention_expired"] is False
    assert protocol["body_full_packet_purge_required"] is False
    assert protocol["purge_required_before_summary"] is False
    assert protocol["next_required_step"] == r51.P7_R51_R13_PAUSED_NEXT_REQUIRED_STEP_REF
    assert protocol["p5_confirmed_candidate_allowed_after_protocol"] is False
    assert protocol["p8_start_allowed"] is False
    _assert_bodyfree_no_leak_or_promotion(protocol)


def test_r51_r13_abort_and_expiration_require_purge_and_block_p5_confirmed_candidate() -> None:
    aborted = r51.build_p7_r51_pause_abort_expiration_protocol_bodyfree(
        rating_question_observation_consistency_guard_bodyfree=_r12_pass(),
        review_lifecycle_status="REVIEW_ABORTED",
        body_full_packet_age_hours=1,
        reviewer_notes_age_hours=1,
    )
    assert aborted["pause_abort_expiration_protocol_status"] == "ABORTED_PURGE_REQUIRED"
    assert aborted["body_full_packet_purge_required"] is True
    assert aborted["aborted_or_expired_blocks_p5_confirmed_candidate"] is True
    assert aborted["p5_review_inconclusive_candidate_after_protocol"] is True
    assert aborted["next_required_step"] == r51.P7_R51_R13_NEXT_REQUIRED_STEP_REF
    _assert_bodyfree_no_leak_or_promotion(aborted)

    expired = r51.build_p7_r51_pause_abort_expiration_protocol_bodyfree(
        rating_question_observation_consistency_guard_bodyfree=_r12_pass(),
        review_lifecycle_status="REVIEW_EXPIRED",
        body_full_packet_age_hours=72,
        reviewer_notes_age_hours=24,
    )
    assert expired["pause_abort_expiration_protocol_status"] == "EXPIRED_PURGE_REQUIRED"
    assert expired["body_full_packet_retention_expired"] is True
    assert expired["reviewer_notes_retention_expired"] is True
    assert expired["body_full_packet_purge_required"] is True
    assert expired["body_removed_priority_over_rating_completion_when_expired"] is True
    assert expired["aborted_or_expired_blocks_p5_confirmed_candidate"] is True
    assert expired["next_required_step"] == r51.P7_R51_R13_NEXT_REQUIRED_STEP_REF
    _assert_bodyfree_no_leak_or_promotion(expired)


def test_r51_r13_blocks_when_r12_consistency_guard_is_blocked() -> None:
    blocked_r12 = _r12_from_rows(_repair_hidden_by_question_review_rows())
    protocol = r51.build_p7_r51_pause_abort_expiration_protocol_bodyfree(
        rating_question_observation_consistency_guard_bodyfree=blocked_r12,
        review_lifecycle_status="REVIEW_COMPLETED",
        body_full_packet_age_hours=1,
        reviewer_notes_age_hours=1,
    )

    assert protocol["pause_abort_expiration_protocol_status"] == "BLOCKED_BY_R51_12_CONSISTENCY_GUARD"
    assert protocol["r13_pause_abort_expiration_protocol_built"] is False
    assert protocol["body_full_packet_purge_required"] is False
    assert protocol["purge_required_before_summary"] is False
    assert protocol["execution_blocker_ids"] == ["r51_rating_question_observation_inconsistent"]
    assert protocol["next_required_step"] == r51.P7_R51_R13_BLOCKED_NEXT_REQUIRED_STEP_REF
    assert protocol["actual_disposal_receipt_materialized_here"] is False
    assert protocol["post_review_summary_materialized_here"] is False
    _assert_bodyfree_no_leak_or_promotion(protocol)


def test_r51_r13_rejects_disposal_release_and_body_payload_mutations() -> None:
    protocol = r51.build_p7_r51_pause_abort_expiration_protocol_bodyfree(
        rating_question_observation_consistency_guard_bodyfree=_r12_pass(),
        review_lifecycle_status="REVIEW_COMPLETED",
        body_full_packet_age_hours=1,
        reviewer_notes_age_hours=1,
    )

    disposal_claim = deepcopy(protocol)
    disposal_claim["actual_disposal_receipt_materialized_here"] = True
    with pytest.raises(ValueError):
        r51.assert_p7_r51_pause_abort_expiration_protocol_bodyfree_contract(disposal_claim)

    release_claim = deepcopy(protocol)
    release_claim["p7_complete"] = True
    with pytest.raises(ValueError):
        r51.assert_p7_r51_pause_abort_expiration_protocol_bodyfree_contract(release_claim)

    with_body = deepcopy(protocol)
    with_body["raw_input"] = "body must not enter R51-13"
    with pytest.raises(ValueError):
        r51.assert_p7_r51_pause_abort_expiration_protocol_bodyfree_contract(with_body)
