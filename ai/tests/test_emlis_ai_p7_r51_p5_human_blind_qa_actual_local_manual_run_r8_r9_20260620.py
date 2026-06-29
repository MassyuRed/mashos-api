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
FORBIDDEN_TRUE_TOKENS = (
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
    '"actual_question_need_observation_rows_materialized_here": true',
    '"actual_disposal_receipt_materialized_here": true',
    '"p5_human_blind_qa_confirmed": true',
    '"p5_human_blind_qa_confirmed_candidate": true',
    '"p6_limited_human_readfeel_start_allowed": true',
    '"p8_question_design_material_candidate": true',
    '"full_backend_suite_green_confirmed": true',
)


def _assert_bodyfree_no_leak_or_promotion(material: dict[str, object]) -> None:
    dumped = json.dumps(material, ensure_ascii=False, sort_keys=True).lower()
    for forbidden in FORBIDDEN_DUMP_TOKENS:
        assert forbidden not in dumped
    for forbidden in FORBIDDEN_TRUE_TOKENS:
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


@lru_cache(maxsize=1)
def _cached_r8() -> tuple[dict[str, object]]:
    r8 = r51.build_p7_r51_actual_human_review_run_bodyfree(
        reviewer_instruction_rating_form_freeze=_freeze(),
        case_manifest_freeze=_manifest(),
        review_result_rows=_pass_review_rows(),
        reviewer_ref="pseudonymous_reviewer_r51_contract",
        reviewed_at="2026-06-20T00:00:00+09:00",
    )
    assert r51.assert_p7_r51_actual_human_review_run_bodyfree_contract(r8) is True
    return (r8,)


def _r8() -> dict[str, object]:
    return deepcopy(_cached_r8()[0])


@lru_cache(maxsize=1)
def _cached_r9() -> tuple[dict[str, object]]:
    r9 = r51.build_p7_r51_rating_row_normalizer_bodyfree(actual_human_review_run=_r8())
    assert r51.assert_p7_r51_rating_row_normalizer_bodyfree_contract(r9) is True
    return (r9,)


def _r9() -> dict[str, object]:
    return deepcopy(_cached_r9()[0])


def test_r51_r8_records_actual_review_run_from_24_sanitized_rows_without_storing_body_full_material() -> None:
    r8 = _r8()

    assert r8["schema_version"] == r51.P7_R51_ACTUAL_HUMAN_REVIEW_RUN_SCHEMA_VERSION
    assert set(r8) == set(r51.P7_R51_ACTUAL_HUMAN_REVIEW_RUN_REQUIRED_FIELD_REFS)
    assert r8["policy_section"] == "R51-8_actual_human_review_run"
    assert r8["review_session_status"] == "R51_ACTUAL_HUMAN_REVIEW_RUN_CAPTURED_BODYFREE"
    assert r8["actual_review_run_status"] == "READY_FOR_RATING_ROW_NORMALIZATION"
    assert r8["next_required_step"] == r51.P7_R51_R8_NEXT_REQUIRED_STEP_REF
    assert r8["required_case_count"] == 24
    assert r8["manifest_case_count"] == 24
    assert r8["review_result_capture_row_count"] == 24
    assert r8["reviewed_blind_case_id_count"] == 24
    assert r8["reviewed_case_ref_id_count"] == 24
    assert r8["reviewed_packet_ref_id_count"] == 24
    assert r8["all_24_cases_reviewed"] is True
    assert r8["rating_selections_captured_bodyfree"] is True
    assert r8["question_need_observation_selections_captured_bodyfree"] is True
    assert r8["actual_human_review_run_here"] is True
    assert r8["actual_manual_review_run_here"] is True
    assert r8["actual_review_result_rows_captured_here"] is True
    assert r8["actual_rating_rows_materialized_here"] is False
    assert r8["actual_question_need_observation_rows_materialized_here"] is False
    assert r8["body_full_packet_generated_here"] is False
    assert r8["body_full_packets_created_local_only"] is False
    assert r8["p5_actual_review_still_not_run"] is False
    assert tuple(r8["implemented_steps"]) == r51.P7_R51_R8_IMPLEMENTED_STEPS
    assert tuple(r8["not_yet_implemented_steps"]) == r51.P7_R51_R8_NOT_YET_IMPLEMENTED_STEPS
    _assert_bodyfree_no_leak_or_promotion(r8)


def test_r51_r8_capture_rows_are_bodyfree_and_keep_reviewer_free_text_question_text_and_machine_score_out() -> None:
    row = _r8()["review_result_capture_rows"][0]
    assert set(row) == set(r51.P7_R51_ACTUAL_REVIEW_RESULT_CAPTURE_ROW_FIELD_REFS)
    assert row["review_kind"] == r51.P7_R51_REVIEW_KIND
    assert set(row["axis_scores"]) == set(r51.P5_HUMAN_BLIND_QA_RATING_AXES)
    assert row["verdict"] == "PASS"
    assert row["reviewer_free_text_included"] is False
    assert row["question_text_included"] is False
    assert row["draft_question_text_included"] is False
    assert row["machine_auto_score_used"] is False
    assert row["machine_metrics_used_for_readfeel"] is False
    assert row["body_free"] is True
    _assert_bodyfree_no_leak_or_promotion(row)


def test_r51_r8_blocks_without_24_review_result_rows_and_does_not_claim_actual_review() -> None:
    rows = _pass_review_rows()[:-1]
    r8 = r51.build_p7_r51_actual_human_review_run_bodyfree(
        reviewer_instruction_rating_form_freeze=_freeze(),
        case_manifest_freeze=_manifest(),
        review_result_rows=rows,
    )
    assert r8["actual_review_run_status"] == "BLOCKED_BY_ACTUAL_REVIEW_RESULT_ROWS"
    assert r8["actual_human_review_run_here"] is False
    assert r8["actual_manual_review_run_here"] is False
    assert r8["actual_review_result_rows_captured_here"] is False
    assert r8["review_result_capture_row_count"] == 0
    assert "r51_rating_rows_incomplete" in r8["execution_blocker_ids"]
    assert r8["p5_actual_review_still_not_run"] is True
    assert tuple(r8["implemented_steps"]) == r51.P7_R51_R7_IMPLEMENTED_STEPS
    assert r8["next_required_step"] == r51.P7_R51_R8_BLOCKED_NEXT_REQUIRED_STEP_REF
    _assert_bodyfree_no_leak_or_promotion(r8)


@pytest.mark.parametrize(
    "key,value",
    [
        ("reviewer_free_text_included", True),
        ("question_text_included", True),
        ("draft_question_text_included", True),
        ("machine_auto_score_used", True),
        ("machine_metrics_used_for_readfeel", True),
    ],
)
def test_r51_r8_rejects_forbidden_review_result_claims(key: str, value: object) -> None:
    rows = _pass_review_rows()
    rows[0][key] = value
    with pytest.raises(ValueError):
        r51.build_p7_r51_actual_human_review_run_bodyfree(
            reviewer_instruction_rating_form_freeze=_freeze(),
            case_manifest_freeze=_manifest(),
            review_result_rows=rows,
        )


def test_r51_r8_rejects_body_payload_and_local_path_in_sanitized_review_rows() -> None:
    rows = _pass_review_rows()
    rows[0]["returned_emlis_surface"] = "body must stay local-only"
    with pytest.raises(ValueError):
        r51.build_p7_r51_actual_human_review_run_bodyfree(
            reviewer_instruction_rating_form_freeze=_freeze(),
            case_manifest_freeze=_manifest(),
            review_result_rows=rows,
        )

    rows = _pass_review_rows()
    rows[0]["local_absolute_path"] = "/tmp/local-only/body-full.json"
    with pytest.raises(ValueError):
        r51.build_p7_r51_actual_human_review_run_bodyfree(
            reviewer_instruction_rating_form_freeze=_freeze(),
            case_manifest_freeze=_manifest(),
            review_result_rows=rows,
        )


def test_r51_r8_rejects_missing_extra_or_out_of_range_axis_scores() -> None:
    rows = _pass_review_rows()
    rows[0]["axis_scores"] = {axis: 1.0 for axis in r51.P5_HUMAN_BLIND_QA_RATING_AXES[:-1]}
    with pytest.raises(ValueError):
        r51.build_p7_r51_actual_human_review_run_bodyfree(
            reviewer_instruction_rating_form_freeze=_freeze(),
            case_manifest_freeze=_manifest(),
            review_result_rows=rows,
        )

    rows = _pass_review_rows()
    scores = dict(rows[0]["axis_scores"])
    scores["extra_axis"] = 1.0
    rows[0]["axis_scores"] = scores
    with pytest.raises(ValueError):
        r51.build_p7_r51_actual_human_review_run_bodyfree(
            reviewer_instruction_rating_form_freeze=_freeze(),
            case_manifest_freeze=_manifest(),
            review_result_rows=rows,
        )

    rows = _pass_review_rows()
    scores = dict(rows[0]["axis_scores"])
    scores[r51.P5_HUMAN_BLIND_QA_RATING_AXES[0]] = 1.1
    rows[0]["axis_scores"] = scores
    with pytest.raises(ValueError):
        r51.build_p7_r51_actual_human_review_run_bodyfree(
            reviewer_instruction_rating_form_freeze=_freeze(),
            case_manifest_freeze=_manifest(),
            review_result_rows=rows,
        )


def test_r51_r8_requires_pass_rows_to_meet_targets_and_repair_rows_to_carry_blocker_and_reason() -> None:
    rows = _pass_review_rows()
    scores = dict(rows[0]["axis_scores"])
    scores["history_connection_naturalness"] = 0.50
    rows[0]["axis_scores"] = scores
    with pytest.raises(ValueError):
        r51.build_p7_r51_actual_human_review_run_bodyfree(
            reviewer_instruction_rating_form_freeze=_freeze(),
            case_manifest_freeze=_manifest(),
            review_result_rows=rows,
        )

    rows = _pass_review_rows()
    scores = {axis: 0.75 for axis in r51.P5_HUMAN_BLIND_QA_RATING_AXES}
    rows[0].update(
        {
            "axis_scores": scores,
            "verdict": "REPAIR_REQUIRED",
            "sanitized_reason_ids": ["p5_history_connection_too_generic"],
            "blocker_ids": ["p5_history_connection_too_generic"],
            "question_need_primary_class": "not_question_p5_surface_repair_required",
            "ambiguity_kind_refs": ["history_connection_basis_unclear"],
            "one_question_fit_ref": "repair_required_not_question",
            "repair_required_refs": ["p5_surface_repair_required"],
        }
    )
    r8 = r51.build_p7_r51_actual_human_review_run_bodyfree(
        reviewer_instruction_rating_form_freeze=_freeze(),
        case_manifest_freeze=_manifest(),
        review_result_rows=rows,
    )
    assert r8["actual_review_run_status"] == "READY_FOR_RATING_ROW_NORMALIZATION"

    rows = _pass_review_rows()
    rows[0].update({"axis_scores": scores, "verdict": "REPAIR_REQUIRED", "sanitized_reason_ids": [], "blocker_ids": []})
    with pytest.raises(ValueError):
        r51.build_p7_r51_actual_human_review_run_bodyfree(
            reviewer_instruction_rating_form_freeze=_freeze(),
            case_manifest_freeze=_manifest(),
            review_result_rows=rows,
        )


def test_r51_r9_normalizes_24_rating_rows_bodyfree_and_points_to_r51_10() -> None:
    r9 = _r9()

    assert r9["schema_version"] == r51.P7_R51_RATING_ROW_NORMALIZER_BODYFREE_SCHEMA_VERSION
    assert set(r9) == set(r51.P7_R51_RATING_ROW_NORMALIZER_BODYFREE_REQUIRED_FIELD_REFS)
    assert r9["policy_section"] == "R51-9_rating_row_normalization"
    assert r9["review_session_status"] == "R51_RATING_ROWS_NORMALIZED_BODYFREE"
    assert r9["rating_row_normalizer_status"] == "READY_FOR_READFEEL_BLOCKER_EXECUTION_BLOCKER_INGESTION"
    assert r9["next_required_step"] == r51.P7_R51_R9_NEXT_REQUIRED_STEP_REF
    assert r9["required_case_count"] == 24
    assert r9["review_result_capture_row_count"] == 24
    assert r9["rating_row_count"] == 24
    assert len(r9["rating_rows"]) == 24
    assert r9["rating_row_schema_version"] == r51.P7_R51_RATING_ROW_BODYFREE_SCHEMA_VERSION
    assert r9["r48_rating_row_schema_version_ref"] == r51.P7_R48_P5_RATING_ROW_BODYFREE_SCHEMA_VERSION
    assert tuple(r9["rating_axis_refs"]) == r51.P5_HUMAN_BLIND_QA_RATING_AXES
    assert r9["rating_axis_target_refs"] == dict(r51.P5_HUMAN_BLIND_QA_TARGETS)
    assert r9["all_required_rating_rows_present"] is True
    assert r9["rating_case_ref_sets_match_review_capture"] is True
    assert r9["verdict_counts"] == {"PASS": 24, "YELLOW": 0, "REPAIR_REQUIRED": 0, "RED": 0}
    assert r9["actual_human_review_run_here"] is True
    assert r9["actual_manual_review_run_here"] is True
    assert r9["actual_rating_rows_materialized_here"] is True
    assert r9["actual_question_need_observation_rows_materialized_here"] is False
    assert r9["p7_complete"] is False
    assert r9["p8_start_allowed"] is False
    assert r9["release_allowed"] is False
    assert tuple(r9["implemented_steps"]) == r51.P7_R51_R9_IMPLEMENTED_STEPS
    assert tuple(r9["not_yet_implemented_steps"]) == r51.P7_R51_R9_NOT_YET_IMPLEMENTED_STEPS
    _assert_bodyfree_no_leak_or_promotion(r9)


def test_r51_r9_rating_rows_keep_r51_schema_review_kind_and_bodyfree_boundaries() -> None:
    row = _r9()["rating_rows"][0]
    assert set(row) == set(r51.P7_R51_RATING_ROW_BODYFREE_REQUIRED_FIELD_REFS)
    assert row["schema_version"] == r51.P7_R51_RATING_ROW_BODYFREE_SCHEMA_VERSION
    assert row["review_kind"] == r51.P7_R51_REVIEW_KIND
    assert set(row["axis_scores"]) == set(r51.P5_HUMAN_BLIND_QA_RATING_AXES)
    assert row["verdict"] == "PASS"
    assert row["sanitized_reason_ids"] == []
    assert row["blocker_ids"] == []
    assert row["reviewer_free_text_included"] is False
    assert row["body_free"] is True
    assert r51.assert_p7_r51_rating_row_bodyfree_contract(row) is True
    _assert_bodyfree_no_leak_or_promotion(row)


def test_r51_r9_blocks_when_r8_review_run_is_not_ready() -> None:
    r8 = r51.build_p7_r51_actual_human_review_run_bodyfree(
        reviewer_instruction_rating_form_freeze=_freeze(),
        case_manifest_freeze=_manifest(),
        review_result_rows=_pass_review_rows()[:-1],
    )
    r9 = r51.build_p7_r51_rating_row_normalizer_bodyfree(actual_human_review_run=r8)
    assert r9["rating_row_normalizer_status"] == "BLOCKED_BY_R51_8_ACTUAL_HUMAN_REVIEW_RUN"
    assert r9["rating_row_count"] == 0
    assert r9["actual_rating_rows_materialized_here"] is False
    assert "r51_rating_rows_incomplete" in r9["execution_blocker_ids"]
    assert r9["p5_actual_review_still_not_run"] is True
    assert r9["next_required_step"] == r51.P7_R51_R9_BLOCKED_NEXT_REQUIRED_STEP_REF
    _assert_bodyfree_no_leak_or_promotion(r9)


def test_r51_r9_rating_row_contract_rejects_schema_free_text_and_release_promotion_mutation() -> None:
    row = deepcopy(_r9()["rating_rows"][0])
    row["reviewer_free_text_included"] = True
    with pytest.raises(ValueError):
        r51.assert_p7_r51_rating_row_bodyfree_contract(row)

    row = deepcopy(_r9()["rating_rows"][0])
    row["schema_version"] = "wrong.schema"
    with pytest.raises(ValueError):
        r51.assert_p7_r51_rating_row_bodyfree_contract(row)

    normalizer = _r9()
    normalizer["release_allowed"] = True
    with pytest.raises(ValueError):
        r51.assert_p7_r51_rating_row_normalizer_bodyfree_contract(normalizer)


def test_r51_r9_does_not_start_p8_question_design_or_materialize_question_rows() -> None:
    r9 = _r9()
    assert r9["question_api_implemented"] is False
    assert r9["question_db_schema_implemented"] is False
    assert r9["question_rn_ui_implemented"] is False
    assert r9["question_response_key_implemented"] is False
    assert r9["question_trigger_logic_implemented"] is False
    assert r9["p8_implementation_spec_finalized_here"] is False
    assert r9["actual_question_need_observation_rows_materialized_here"] is False
    assert r9["p8_start_allowed"] is False
    assert r9["release_allowed"] is False
    _assert_bodyfree_no_leak_or_promotion(r9)
