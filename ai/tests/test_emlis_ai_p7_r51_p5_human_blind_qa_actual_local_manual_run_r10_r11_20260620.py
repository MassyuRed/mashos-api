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
    '"body_full_packet_generated_here": true',
    '"actual_body_full_packet_generated_here": true',
    '"actual_disposal_receipt_materialized_here": true',
    '"p5_human_blind_qa_confirmed": true',
    '"p5_human_blind_qa_confirmed_candidate": true',
    '"p6_limited_human_readfeel_start_allowed": true',
    '"p8_question_design_material_candidate": true',
    '"full_backend_suite_green_confirmed": true',
)


def _assert_bodyfree_no_leak_or_promotion(material: dict[str, object], *, allow_question_rows: bool = False) -> None:
    dumped = json.dumps(material, ensure_ascii=False, sort_keys=True).lower()
    for forbidden in FORBIDDEN_DUMP_TOKENS:
        assert forbidden not in dumped
    for forbidden in FORBIDDEN_TRUE_TOKENS_BASE:
        assert forbidden not in dumped
    if not allow_question_rows:
        assert '"actual_question_need_observation_rows_materialized_here": true' not in dumped


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


def _pass_review_rows() -> list[dict[str, object]]:
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


def _repair_review_rows() -> list[dict[str, object]]:
    rows = _pass_review_rows()
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


def _question_candidate_review_rows() -> list[dict[str, object]]:
    rows = _pass_review_rows()
    rows[0].update(
        {
            "question_need_primary_class": "question_may_reduce_overread_risk",
            "ambiguity_kind_refs": ["missing_target"],
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


@lru_cache(maxsize=1)
def _cached_r8_pass() -> tuple[dict[str, object]]:
    return (_r8_from_rows(_pass_review_rows()),)


def _r8_pass() -> dict[str, object]:
    return deepcopy(_cached_r8_pass()[0])


@lru_cache(maxsize=1)
def _cached_r9_pass() -> tuple[dict[str, object]]:
    r9 = r51.build_p7_r51_rating_row_normalizer_bodyfree(actual_human_review_run=_r8_pass())
    assert r51.assert_p7_r51_rating_row_normalizer_bodyfree_contract(r9) is True
    return (r9,)


def _r9_pass() -> dict[str, object]:
    return deepcopy(_cached_r9_pass()[0])


@lru_cache(maxsize=1)
def _cached_r10_pass() -> tuple[dict[str, object]]:
    r10 = r51.build_p7_r51_readfeel_blocker_execution_blocker_ingestion_bodyfree(
        rating_row_normalizer_bodyfree=_r9_pass()
    )
    assert r51.assert_p7_r51_readfeel_blocker_execution_blocker_ingestion_bodyfree_contract(r10) is True
    return (r10,)


def _r10_pass() -> dict[str, object]:
    return deepcopy(_cached_r10_pass()[0])


def _r9_from_rows(rows: list[dict[str, object]]) -> dict[str, object]:
    r9 = r51.build_p7_r51_rating_row_normalizer_bodyfree(actual_human_review_run=_r8_from_rows(rows))
    assert r51.assert_p7_r51_rating_row_normalizer_bodyfree_contract(r9) is True
    return r9


def _r10_from_rows(rows: list[dict[str, object]]) -> dict[str, object]:
    r10 = r51.build_p7_r51_readfeel_blocker_execution_blocker_ingestion_bodyfree(
        rating_row_normalizer_bodyfree=_r9_from_rows(rows)
    )
    assert r51.assert_p7_r51_readfeel_blocker_execution_blocker_ingestion_bodyfree_contract(r10) is True
    return r10


def _r11_from_rows(rows: list[dict[str, object]]) -> dict[str, object]:
    r8 = _r8_from_rows(rows)
    r10 = r51.build_p7_r51_readfeel_blocker_execution_blocker_ingestion_bodyfree(
        rating_row_normalizer_bodyfree=r51.build_p7_r51_rating_row_normalizer_bodyfree(actual_human_review_run=r8)
    )
    r11 = r51.build_p7_r51_question_need_observation_row_normalizer_bodyfree(
        actual_human_review_run=r8,
        readfeel_blocker_execution_blocker_ingestion_bodyfree=r10,
    )
    assert r51.assert_p7_r51_question_need_observation_row_normalizer_bodyfree_contract(r11) is True
    return r11


def test_r51_r10_ingests_empty_blocker_sets_after_pass_rating_rows_and_points_to_r51_11() -> None:
    r10 = _r10_pass()

    assert r10["schema_version"] == r51.P7_R51_READFEEL_EXECUTION_BLOCKER_INGESTION_BODYFREE_SCHEMA_VERSION
    assert set(r10) == set(r51.P7_R51_READFEEL_EXECUTION_BLOCKER_INGESTION_BODYFREE_REQUIRED_FIELD_REFS)
    assert r10["policy_section"] == "R51-10_readfeel_blocker_execution_blocker_ingestion"
    assert r10["review_session_status"] == "R51_READFEEL_EXECUTION_BLOCKERS_INGESTED_BODYFREE"
    assert r10["blocker_ingestion_status"] == "READY_FOR_QUESTION_NEED_OBSERVATION_ROW_NORMALIZATION"
    assert r10["next_required_step"] == r51.P7_R51_R10_NEXT_REQUIRED_STEP_REF
    assert r10["rating_row_count"] == 24
    assert r10["readfeel_blocker_row_count"] == 0
    assert r10["execution_blocker_row_count"] == 0
    assert r10["readfeel_and_execution_blockers_separated"] is True
    assert r10["execution_blockers_do_not_assign_readfeel_verdict"] is True
    assert r10["actual_blocker_rows_materialized_here"] is True
    assert r10["actual_execution_blocker_rows_materialized_here"] is True
    assert r10["actual_question_need_observation_rows_materialized_here"] is False
    assert tuple(r10["implemented_steps"]) == r51.P7_R51_R10_IMPLEMENTED_STEPS
    assert tuple(r10["not_yet_implemented_steps"]) == r51.P7_R51_R10_NOT_YET_IMPLEMENTED_STEPS
    _assert_bodyfree_no_leak_or_promotion(r10)


def test_r51_r10_materializes_readfeel_blocker_row_without_turning_it_into_execution_blocker() -> None:
    r10 = _r10_from_rows(_repair_review_rows())

    assert r10["blocker_ingestion_status"] == "READY_FOR_QUESTION_NEED_OBSERVATION_ROW_NORMALIZATION"
    assert r10["readfeel_blocker_row_count"] == 1
    assert r10["execution_blocker_row_count"] == 0
    assert r10["open_readfeel_blocker_count"] == 1
    assert r10["open_execution_blocker_count"] == 0
    row = r10["readfeel_blocker_rows"][0]
    assert set(row) == set(r51.P7_R51_READFEEL_BLOCKER_ROW_BODYFREE_REQUIRED_FIELD_REFS)
    assert row["blocker_id"] == "p5_history_connection_too_generic"
    assert row["blocker_kind"] == "REPAIR_REQUIRED"
    assert row["blocker_status"] == "OPEN"
    assert "p5_history_connection_too_generic" in row["sanitized_reason_ids"]
    assert row["reviewer_free_text_included"] is False
    assert row["body_free"] is True
    assert r51.assert_p7_r51_readfeel_blocker_row_bodyfree_contract(row) is True
    _assert_bodyfree_no_leak_or_promotion(r10)


def test_r51_r10_maps_blocked_rating_normalizer_to_execution_blocker_without_readfeel_verdict() -> None:
    r8_blocked = r51.build_p7_r51_actual_human_review_run_bodyfree(
        reviewer_instruction_rating_form_freeze=_freeze(),
        case_manifest_freeze=_manifest(),
        review_result_rows=_pass_review_rows()[:-1],
    )
    r9_blocked = r51.build_p7_r51_rating_row_normalizer_bodyfree(actual_human_review_run=r8_blocked)
    r10 = r51.build_p7_r51_readfeel_blocker_execution_blocker_ingestion_bodyfree(
        rating_row_normalizer_bodyfree=r9_blocked
    )

    assert r10["blocker_ingestion_status"] == "BLOCKED_BY_R51_9_RATING_ROW_NORMALIZER"
    assert r10["readfeel_blocker_row_count"] == 0
    assert r10["execution_blocker_row_count"] >= 1
    assert r10["actual_blocker_rows_materialized_here"] is False
    assert r10["actual_execution_blocker_rows_materialized_here"] is False
    assert r10["r10_readfeel_blocker_execution_blocker_ingestion_built"] is False
    erow = r10["execution_blocker_rows"][0]
    assert set(erow) == set(r51.P7_R51_EXECUTION_BLOCKER_ROW_BODYFREE_REQUIRED_FIELD_REFS)
    assert erow["execution_blocker_id"] == "r51_rating_rows_incomplete"
    assert erow["execution_blocker_kind"] == "RATING"
    assert erow["readfeel_verdict_not_assigned"] is True
    assert r51.assert_p7_r51_execution_blocker_row_bodyfree_contract(erow) is True
    _assert_bodyfree_no_leak_or_promotion(r10)


def test_r51_r11_normalizes_24_question_need_rows_bodyfree_and_points_to_r51_12() -> None:
    r11 = _r11_from_rows(_pass_review_rows())

    assert r11["schema_version"] == r51.P7_R51_QUESTION_NEED_OBSERVATION_ROW_NORMALIZER_BODYFREE_SCHEMA_VERSION
    assert set(r11) == set(r51.P7_R51_QUESTION_NEED_OBSERVATION_ROW_NORMALIZER_BODYFREE_REQUIRED_FIELD_REFS)
    assert r11["policy_section"] == "R51-11_question_need_observation_row_normalization"
    assert r11["review_session_status"] == "R51_QUESTION_NEED_OBSERVATION_ROWS_NORMALIZED_BODYFREE"
    assert r11["question_observation_normalizer_status"] == "READY_FOR_RATING_QUESTION_OBSERVATION_CONSISTENCY_GUARD"
    assert r11["next_required_step"] == r51.P7_R51_R11_NEXT_REQUIRED_STEP_REF
    assert r11["question_observation_row_count"] == 24
    assert len(r11["question_need_observation_rows"]) == 24
    assert r11["all_required_question_need_observation_rows_present"] is True
    assert r11["row_case_ref_sets_match_review_capture"] is True
    assert r11["row_case_ref_sets_match_rating_rows"] is True
    assert r11["question_need_primary_class_counts"] == {"no_question_needed_emlis_can_observe": 24}
    assert r11["ambiguity_kind_counts"] == {"no_material_ambiguity": 24}
    assert r11["one_question_fit_counts"] == {"not_needed": 24}
    assert r11["repair_required_counts"] == {"no_repair_required": 24}
    assert r11["actual_question_need_observation_rows_materialized_here"] is True
    assert r11["actual_question_need_observation_summary_materialized_here"] is False
    assert r11["p8_question_implementation_spec_finalized_here"] is False
    assert r11["p8_start_allowed"] is False
    assert r11["release_allowed"] is False
    assert tuple(r11["implemented_steps"]) == r51.P7_R51_R11_IMPLEMENTED_STEPS
    assert tuple(r11["not_yet_implemented_steps"]) == r51.P7_R51_R11_NOT_YET_IMPLEMENTED_STEPS
    _assert_bodyfree_no_leak_or_promotion(r11, allow_question_rows=True)


def test_r51_r11_question_rows_keep_schema_stage_enums_and_no_text_boundary() -> None:
    r11 = _r11_from_rows(_pass_review_rows())
    row = r11["question_need_observation_rows"][0]

    assert set(row) == set(r51.P7_R51_QUESTION_NEED_OBSERVATION_ROW_BODYFREE_REQUIRED_FIELD_REFS)
    assert row["schema_version"] == r51.P7_R51_QUESTION_NEED_OBSERVATION_ROW_BODYFREE_SCHEMA_VERSION
    assert row["observation_stage"] == r51.P7_R50_QUESTION_NEED_OBSERVATION_STAGE_REF
    assert row["question_need_primary_class"] == "no_question_needed_emlis_can_observe"
    assert row["ambiguity_kind_refs"] == ["no_material_ambiguity"]
    assert row["one_question_fit_ref"] == "not_needed"
    assert row["repair_required_refs"] == ["no_repair_required"]
    assert row["question_text_included"] is False
    assert row["draft_question_text_included"] is False
    assert row["reviewer_free_text_included"] is False
    assert row["body_free"] is True
    assert r51.assert_p7_r51_question_need_observation_row_bodyfree_contract(row) is True
    _assert_bodyfree_no_leak_or_promotion(row, allow_question_rows=True)


def test_r51_r11_carries_question_candidate_as_bodyfree_p8_material_flag_without_starting_p8() -> None:
    r11 = _r11_from_rows(_question_candidate_review_rows())

    assert r11["question_observation_normalizer_status"] == "READY_FOR_RATING_QUESTION_OBSERVATION_CONSISTENCY_GUARD"
    assert r11["question_need_primary_class_counts"]["question_may_reduce_overread_risk"] == 1
    assert r11["plan_candidate_flag_counts"]["p8_design_material_candidate"] >= 1
    row = [
        item
        for item in r11["question_need_observation_rows"]
        if item["question_need_primary_class"] == "question_may_reduce_overread_risk"
    ][0]
    assert row["ambiguity_kind_refs"] == ["missing_target"]
    assert row["one_question_fit_ref"] == "fits_one_question"
    assert row["plan_candidate_flags"] == ["p8_design_material_candidate"]
    assert row["repair_required_refs"] == ["no_repair_required"]
    assert r11["question_trigger_logic_implemented_here"] is False
    assert r11["api_db_rn_response_key_changed_here"] is False
    assert r11["p8_question_implementation_spec_finalized_here"] is False
    assert r11["p8_start_allowed"] is False
    assert r11["release_allowed"] is False
    _assert_bodyfree_no_leak_or_promotion(r11, allow_question_rows=True)


def test_r51_r11_rejects_question_text_reviewer_text_and_body_payload_mutations() -> None:
    r11 = _r11_from_rows(_pass_review_rows())

    row = deepcopy(r11["question_need_observation_rows"][0])
    row["question_text_included"] = True
    with pytest.raises(ValueError):
        r51.assert_p7_r51_question_need_observation_row_bodyfree_contract(row)

    row = deepcopy(r11["question_need_observation_rows"][0])
    row["reviewer_free_text_included"] = True
    with pytest.raises(ValueError):
        r51.assert_p7_r51_question_need_observation_row_bodyfree_contract(row)

    row = deepcopy(r11["question_need_observation_rows"][0])
    row["raw_input"] = "body must not enter R51-11 body-free row"
    with pytest.raises(ValueError):
        r51.assert_p7_r51_question_need_observation_row_bodyfree_contract(row)

    normalizer = r11
    normalizer["question_trigger_logic_implemented_here"] = True
    with pytest.raises(ValueError):
        r51.assert_p7_r51_question_need_observation_row_normalizer_bodyfree_contract(normalizer)


def test_r51_r11_rejects_inconsistent_question_observation_semantics() -> None:
    row = deepcopy(_r11_from_rows(_pass_review_rows())["question_need_observation_rows"][0])
    row["ambiguity_kind_refs"] = ["missing_target"]
    with pytest.raises(ValueError):
        r51.assert_p7_r51_question_need_observation_row_bodyfree_contract(row)

    row = deepcopy(_r11_from_rows(_question_candidate_review_rows())["question_need_observation_rows"][0])
    row["plan_candidate_flags"] = []
    with pytest.raises(ValueError):
        r51.assert_p7_r51_question_need_observation_row_bodyfree_contract(row)

    rows = _pass_review_rows()
    rows[0].update(
        {
            "question_need_primary_class": "not_question_p5_surface_repair_required",
            "ambiguity_kind_refs": ["history_connection_basis_unclear"],
            "one_question_fit_ref": "repair_required_not_question",
            "repair_required_refs": ["no_repair_required"],
        }
    )
    r8 = _r8_from_rows(rows)
    r10 = r51.build_p7_r51_readfeel_blocker_execution_blocker_ingestion_bodyfree(
        rating_row_normalizer_bodyfree=r51.build_p7_r51_rating_row_normalizer_bodyfree(actual_human_review_run=r8)
    )
    r11 = r51.build_p7_r51_question_need_observation_row_normalizer_bodyfree(
        actual_human_review_run=r8,
        readfeel_blocker_execution_blocker_ingestion_bodyfree=r10,
    )
    assert r11["question_observation_normalizer_status"] == "BLOCKED_BY_QUESTION_OBSERVATION_ROW_VALIDATION"
    assert "r51_question_need_observation_rows_incomplete" in r11["execution_blocker_ids"]
    assert r11["actual_question_need_observation_rows_materialized_here"] is False
    _assert_bodyfree_no_leak_or_promotion(r11)
