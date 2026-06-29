# -*- coding: utf-8 -*-
from __future__ import annotations

import json
from copy import deepcopy
from functools import lru_cache

import pytest

import emlis_ai_p7_r48_p5_human_blind_qa_actual_review_packet as r48
import emlis_ai_p7_r49_p5_human_blind_qa_actual_review_execution as r49

SECRET_INPUT = "R49 secret raw input must not enter body-free R4/R5 material"
SECRET_SURFACE = "R49 returned Emlis surface must not enter body-free R4/R5 material"
SECRET_REVIEWER = "R49 reviewer free text must not enter body-free R4/R5 material"
SECRET_QUESTION = "R49 draft question text must not enter body-free R4/R5 material"


def _dumped(value: object) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def _assert_no_body_question_or_release_promotion(value: dict[str, object]) -> None:
    dumped = _dumped(value)
    assert SECRET_INPUT not in dumped
    assert SECRET_SURFACE not in dumped
    assert SECRET_REVIEWER not in dumped
    assert SECRET_QUESTION not in dumped
    for forbidden_key in (
        '"raw_input":',
        '"raw_answer":',
        '"comment_text":',
        '"comment_text_body":',
        '"current_input_review_surface":',
        '"returned_emlis_surface":',
        '"bounded_owned_history_review_surface":',
        '"reviewer_free_text":',
        '"reviewer_note":',
        '"question_text":',
        '"draft_question_text":',
        '"question_body":',
        '"terminal_output":',
        '"body_content_hash":',
        '"packet_content_hash":',
        '"local_absolute_path":',
    ):
        assert forbidden_key not in dumped
    for forbidden_true in (
        '"release_allowed": true',
        '"p7_complete": true',
        '"p8_start_allowed": true',
        '"hold004_close_allowed": true',
        '"question_api_implemented": true',
        '"question_db_schema_implemented": true',
        '"question_rn_ui_implemented": true',
        '"question_response_key_implemented": true',
        '"question_trigger_logic_implemented": true',
        '"p8_implementation_spec_finalized_here": true',
        '"actual_body_full_packet_generated_here": true',
        '"body_full_writer_created_here": true',
        '"actual_human_review_run_here": true',
        '"actual_rating_rows_materialized_here": true',
    ):
        assert forbidden_true not in dumped.lower()


@lru_cache(maxsize=1)
def _cached_r2_r3_ready() -> tuple[dict[str, object], dict[str, object]]:
    r2 = r49.build_p7_r49_r48_case_matrix_handoff_validation()
    assert r49.assert_p7_r49_r48_case_matrix_handoff_validation_contract(r2) is True
    r3 = r49.build_p7_r49_local_only_actual_packet_generation_preflight(
        r49_r48_case_matrix_handoff_validation=r2,
        local_review_root="/tmp/cocolon_r49_r4_r5_valid_external_local_review_root",
        explicit_body_full_generation_allow=True,
    )
    assert r49.assert_p7_r49_local_only_actual_packet_generation_preflight_contract(r3) is True
    assert r3["preflight_status"] == "READY_FOR_LOCAL_ONLY_PACKET_GENERATION"
    return (r2, r3)


def _r2() -> dict[str, object]:
    return deepcopy(_cached_r2_r3_ready()[0])


def _ready_r3() -> dict[str, object]:
    return deepcopy(_cached_r2_r3_ready()[1])


def _passing_review_result() -> dict[str, object]:
    return {
        "axis_scores": {axis: 1.0 for axis in r49.P5_HUMAN_BLIND_QA_RATING_AXES},
        "verdict": "PASS",
        "sanitized_reason_ids": [],
        "blocker_ids": [],
    }


def test_r49_r4_builds_actual_review_session_protocol_from_ready_preflight_without_generating_packets() -> None:
    protocol = r49.build_p7_r49_actual_review_session_protocol(
        r49_local_only_actual_packet_generation_preflight=_ready_r3(),
    )
    assert r49.assert_p7_r49_actual_review_session_protocol_contract(protocol) is True

    assert protocol["schema_version"] == r49.P7_R49_ACTUAL_REVIEW_SESSION_PROTOCOL_SCHEMA_VERSION
    assert set(protocol) == set(r49.P7_R49_ACTUAL_REVIEW_SESSION_PROTOCOL_REQUIRED_FIELD_REFS)
    assert protocol["policy_section"] == "R49-4_actual_review_session_protocol_builder"
    assert protocol["review_prompt_version"] == r48.P7_R48_REVIEW_PROMPT_VERSION
    assert protocol["required_case_count"] == 24
    assert protocol["protocol_case_count"] == 24
    assert protocol["protocol_ready_for_later_local_only_review"] is True
    assert protocol["protocol_blocked_by_preflight"] is False
    assert protocol["review_session_status"] == "NOT_STARTED"

    assert tuple(protocol["reviewer_visible_field_refs"]) == r48.P7_R48_P5_REVIEWER_PACKET_REVIEWER_VISIBLE_FIELD_REFS
    assert tuple(protocol["local_only_packet_required_field_refs"]) == r48.P7_R48_P5_REVIEWER_PACKET_LOCAL_ONLY_REQUIRED_FIELD_REFS
    assert tuple(protocol["local_only_packet_forbidden_field_refs"]) == r48.P7_R48_P5_REVIEWER_PACKET_LOCAL_ONLY_FORBIDDEN_FIELD_REFS
    assert tuple(protocol["review_question_refs"]) == r48.P7_R48_P5_REVIEW_QUESTION_REFS
    assert tuple(protocol["rating_axes"]) == r49.P5_HUMAN_BLIND_QA_RATING_AXES
    assert protocol["rating_axis_target_thresholds"] == dict(r49.P5_HUMAN_BLIND_QA_TARGETS)

    assert protocol["reviewer_reads_blind_case_id_units"] is True
    assert protocol["reviewer_receives_case_ref_id"] is False
    assert protocol["reviewer_receives_family"] is False
    assert protocol["reviewer_receives_subscription_tier"] is False
    assert protocol["question_need_observation_required"] is True
    assert protocol["question_need_observation_row_required_per_case"] is True
    assert protocol["question_text_required"] is False
    assert protocol["question_text_allowed"] is False
    assert protocol["draft_question_text_allowed"] is False
    assert protocol["reviewer_free_text_local_only_allowed"] is True
    assert protocol["reviewer_free_text_bodyfree_export_allowed"] is False
    assert protocol["machine_metric_rating_allowed"] is False
    assert protocol["readfeel_auto_rating_allowed"] is False

    for row in protocol["protocol_case_rows"]:
        assert set(row) == set(r49.P7_R49_ACTUAL_REVIEW_SESSION_PROTOCOL_CASE_ROW_FIELD_REFS)
        assert row["blind_case_id"]
        assert row["packet_ref_id"]
        assert row["reviewer_receives_blind_case_id"] is True
        assert row["reviewer_receives_case_ref_id"] is False
        assert row["reviewer_receives_family"] is False
        assert row["reviewer_receives_subscription_tier"] is False
        assert row["packet_ref_id_visible_to_reviewer"] is False
        assert row["question_text_required"] is False
        assert row["reviewer_free_text_bodyfree_export_allowed"] is False
        assert row["body_full_packet_materialized_here"] is False
        assert row["actual_human_review_run_here"] is False
        assert row["body_free"] is True

    assert tuple(protocol["implemented_steps"]) == r49.P7_R49_R4_IMPLEMENTED_STEPS
    assert tuple(protocol["not_yet_implemented_steps"]) == r49.P7_R49_R4_NOT_YET_IMPLEMENTED_STEPS
    assert protocol["next_required_step"] == r49.P7_R49_R4_NEXT_REQUIRED_STEP_REF
    assert protocol["body_full_packet_materialized_here"] is False
    assert protocol["local_reviewer_payload_materialized_here"] is False
    assert protocol["actual_body_full_packet_generated_here"] is False
    assert protocol["actual_human_review_run_here"] is False
    assert protocol["actual_rating_rows_materialized_here"] is False
    assert protocol["actual_question_need_observation_rows_materialized_here"] is False
    _assert_no_body_question_or_release_promotion(protocol)


def test_r49_r4_blocked_preflight_protocol_stays_precheck_blocked_and_does_not_claim_packets_ready() -> None:
    blocked_r3 = r49.build_p7_r49_local_only_actual_packet_generation_preflight(
        r49_r48_case_matrix_handoff_validation=_r2(),
    )
    assert blocked_r3["preflight_status"] == "BLOCKED"
    protocol = r49.build_p7_r49_actual_review_session_protocol(
        r49_local_only_actual_packet_generation_preflight=blocked_r3,
    )

    assert r49.assert_p7_r49_actual_review_session_protocol_contract(protocol) is True
    assert protocol["protocol_case_count"] == 24
    assert protocol["protocol_ready_for_later_local_only_review"] is False
    assert protocol["protocol_blocked_by_preflight"] is True
    assert protocol["review_session_status"] == "PRECHECK_BLOCKED"
    assert protocol["body_full_packet_materialized_here"] is False
    assert protocol["actual_body_full_packet_generated_here"] is False
    assert protocol["actual_human_review_run_here"] is False
    _assert_no_body_question_or_release_promotion(protocol)


def test_r49_r5_freezes_rating_row_ingestion_to_r48_normalizer_without_materializing_rating_rows() -> None:
    protocol = r49.build_p7_r49_actual_review_session_protocol(
        r49_local_only_actual_packet_generation_preflight=_ready_r3(),
    )
    connection = r49.build_p7_r49_rating_row_ingestion_r48_normalizer_connection(
        r49_actual_review_session_protocol=protocol,
    )
    assert r49.assert_p7_r49_rating_row_ingestion_r48_normalizer_connection_contract(connection) is True

    assert connection["schema_version"] == r49.P7_R49_RATING_ROW_INGESTION_R48_NORMALIZER_CONNECTION_SCHEMA_VERSION
    assert set(connection) == set(r49.P7_R49_RATING_ROW_INGESTION_R48_NORMALIZER_CONNECTION_REQUIRED_FIELD_REFS)
    assert connection["policy_section"] == "R49-5_rating_row_ingestion_r48_normalizer_connection"
    assert connection["r4_protocol_schema_version"] == r49.P7_R49_ACTUAL_REVIEW_SESSION_PROTOCOL_SCHEMA_VERSION
    assert connection["r48_rating_row_normalizer_schema_version"] == r48.P7_R48_RATING_ROW_NORMALIZER_SCHEMA_VERSION
    assert connection["r48_rating_row_bodyfree_schema_version"] == r48.P7_R48_P5_RATING_ROW_BODYFREE_SCHEMA_VERSION
    assert connection["r48_rating_row_normalizer_function_ref"] == "normalize_p7_r48_p5_rating_row_bodyfree"
    assert connection["r48_rating_row_contract_ref"] == "assert_p7_r48_p5_rating_row_bodyfree_contract"
    assert tuple(connection["r48_rating_row_required_field_refs"]) == r48.P7_R48_P5_RATING_ROW_REQUIRED_FIELD_REFS
    assert tuple(connection["rating_axes"]) == r49.P5_HUMAN_BLIND_QA_RATING_AXES
    assert connection["axis_target_thresholds"] == dict(r49.P5_HUMAN_BLIND_QA_TARGETS)
    assert tuple(connection["allowed_verdict_refs"]) == r48.P7_R48_P5_REVIEWABLE_VERDICTS
    assert tuple(connection["sanitized_reason_id_refs"]) == r48.P7_R48_SANITIZED_REASON_ID_REFS
    assert tuple(connection["readfeel_blocker_id_refs"]) == r48.P7_R48_READFEEL_BLOCKER_ID_REFS

    assert connection["rating_row_ingestion_ready"] is True
    assert connection["rating_rows_must_be_r48_bodyfree"] is True
    assert connection["r48_normalizer_connection_fixed"] is True
    assert connection["r49_does_not_define_independent_rating_axes"] is True
    assert connection["machine_metrics_used_for_readfeel"] is False
    assert connection["readfeel_auto_estimation_allowed"] is False
    assert connection["reviewer_free_text_bodyfree_allowed"] is False
    assert connection["question_observation_ingestion_done_here"] is False
    assert connection["actual_human_review_run_here"] is False
    assert connection["actual_rating_rows_materialized_here"] is False
    assert tuple(connection["implemented_steps"]) == r49.P7_R49_R5_IMPLEMENTED_STEPS
    assert tuple(connection["not_yet_implemented_steps"]) == r49.P7_R49_R5_NOT_YET_IMPLEMENTED_STEPS
    assert connection["next_required_step"] == r49.P7_R49_R5_NEXT_REQUIRED_STEP_REF
    _assert_no_body_question_or_release_promotion(connection)


def test_r49_r5_normalizes_sanitized_rating_row_via_r48_bodyfree_contract() -> None:
    case_row = _r2()["case_manifest_rows"][0]
    rating = r49.normalize_p7_r49_p5_rating_row_via_r48_bodyfree(
        review_result=_passing_review_result(),
        case_manifest_row=case_row,
        review_session_id="p7_r49_review_session_for_rating_ingestion",
        reviewer_ref="reviewer_bodyfree_ref",
        reviewed_at="2026-06-19T00:00:00+09:00",
        body_removed=True,
    )

    assert r48.assert_p7_r48_p5_rating_row_bodyfree_contract(rating) is True
    assert rating["schema_version"] == r48.P7_R48_P5_RATING_ROW_BODYFREE_SCHEMA_VERSION
    assert set(rating) == set(r48.P7_R48_P5_RATING_ROW_REQUIRED_FIELD_REFS)
    assert rating["review_session_id"] == "p7_r49_review_session_for_rating_ingestion"
    assert rating["packet_ref_id"] == case_row["packet_ref_id"]
    assert rating["blind_case_id"] == case_row["blind_case_id"]
    assert rating["case_ref_id"] == case_row["case_ref_id"]
    assert rating["family"] == case_row["family"]
    assert rating["case_role"] == case_row["case_role"]
    assert rating["verdict"] == "PASS"
    assert rating["blocker_ids"] == []
    assert rating["reviewer_free_text_included"] is False
    assert rating["body_removed"] is True
    assert rating["body_free"] is True
    _assert_no_body_question_or_release_promotion(rating)


@pytest.mark.parametrize(
    "forbidden_patch",
    [
        {"reviewer_free_text": SECRET_REVIEWER},
        {"machine_metrics_used_for_readfeel": True},
        {"question_need_primary_class": "question_may_reduce_overread_risk"},
    ],
)
def test_r49_r5_rejects_reviewer_text_machine_metric_and_question_observation_mixed_into_rating_ingestion(
    forbidden_patch: dict[str, object],
) -> None:
    review_result = _passing_review_result()
    review_result.update(forbidden_patch)
    with pytest.raises(ValueError):
        r49.normalize_p7_r49_p5_rating_row_via_r48_bodyfree(
            review_result=review_result,
            case_manifest_row=_r2()["case_manifest_rows"][0],
        )


def test_r49_r5_keeps_r48_verdict_score_blocker_consistency_guard() -> None:
    bad_pass = _passing_review_result()
    bad_pass["axis_scores"] = {axis: 1.0 for axis in r49.P5_HUMAN_BLIND_QA_RATING_AXES}
    bad_pass["axis_scores"]["history_connection_naturalness"] = 0.1

    with pytest.raises(ValueError):
        r49.normalize_p7_r49_p5_rating_row_via_r48_bodyfree(
            review_result=bad_pass,
            case_manifest_row=_r2()["case_manifest_rows"][0],
        )


def test_r49_r4_r5_freeze_keeps_p8_release_and_actual_review_closed() -> None:
    freeze = r49.build_p7_r49_r4_r5_protocol_rating_connection_freeze(
        r49_local_only_actual_packet_generation_preflight=_ready_r3(),
    )
    assert r49.assert_p7_r49_r4_r5_protocol_rating_connection_freeze_contract(freeze) is True

    assert freeze["schema_version"] == r49.P7_R49_R4_R5_PROTOCOL_RATING_CONNECTION_FREEZE_SCHEMA_VERSION
    assert set(freeze) == set(r49.P7_R49_R4_R5_PROTOCOL_RATING_CONNECTION_FREEZE_REQUIRED_FIELD_REFS)
    assert freeze["policy_section"] == "R49-4_R49-5_protocol_rating_connection_freeze"
    assert freeze["protocol_ready_for_later_local_only_review"] is True
    assert freeze["rating_row_ingestion_ready"] is True
    assert freeze["r48_normalizer_connection_fixed"] is True
    assert freeze["body_full_packet_materialized_here"] is False
    assert freeze["actual_body_full_packet_generated_here"] is False
    assert freeze["actual_human_review_run_here"] is False
    assert freeze["actual_rating_rows_materialized_here"] is False
    assert freeze["actual_question_need_observation_rows_materialized_here"] is False
    assert freeze["question_need_observation_required"] is True
    assert freeze["question_need_observation_rows_required_later"] is True
    assert tuple(freeze["implemented_steps"]) == r49.P7_R49_R5_IMPLEMENTED_STEPS
    assert tuple(freeze["not_yet_implemented_steps"]) == r49.P7_R49_R5_NOT_YET_IMPLEMENTED_STEPS
    assert freeze["next_required_step"] == r49.P7_R49_R5_NEXT_REQUIRED_STEP_REF
    _assert_no_body_question_or_release_promotion(freeze)
