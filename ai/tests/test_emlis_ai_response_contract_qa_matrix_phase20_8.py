# -*- coding: utf-8 -*-
from __future__ import annotations

import json
from collections.abc import Mapping
from typing import Any

import pytest

from emlis_ai_response_contract import ResponseKind
from emlis_ai_response_contract_qa_matrix import (
    FAMILY_LOW_INFORMATION_AMBIGUOUS,
    FAMILY_LOW_INFORMATION_SHORT,
    FAMILY_SAFETY_EMERGENCY,
    MUST_NOT_EMPTY_COMMENT_TEXT,
    MUST_NOT_FIXED_TEMPLATE,
    MUST_NOT_UNSUPPORTED_ASSERTION,
    PHASE20_8_CASE_ID_RUNTIME_CONDITION_ALLOWED,
    PHASE20_8_EXACT_FIXTURE_REGRESSION_IDS,
    PHASE20_8_EXACT_FIXTURE_TEXT_MATCHING_ALLOWED,
    PHASE20_8_INPUT_FAMILIES,
    PHASE20_8_RESPONSE_CONTRACT_QA_MATRIX_SCHEMA_VERSION,
    PHASE20_8_RESPONSE_CONTRACT_QA_REPORT_SCHEMA_VERSION,
    assert_phase20_8_response_contract_qa_case_payload,
    assert_phase20_8_response_contract_qa_evaluation_payload,
    assert_phase20_8_response_contract_qa_report_payload,
    build_phase20_8_response_contract_qa_cases,
    build_phase20_8_response_contract_qa_report,
    evaluate_phase20_8_response_contract_qa_case,
)

RAW_FIXTURE_FRAGMENTS = (
    "今日は職場で上司に急に予定変更",
    "なんか今日は全部だるい",
    "もやもやする",
    "もう死にたい",
    "友達に優しくしてもらって",
    "嬉しいはずなのに",
    "朝、部屋を片付けて",
    "自分が何を大事にしたい",
)


def _dump(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True)


def test_phase20_8_qa_cases_cover_all_families_without_exact_text_targets() -> None:
    cases = build_phase20_8_response_contract_qa_cases()
    rows = [case.schema_payload() for case in cases]
    meta_rows = [case.meta_payload() for case in cases]

    assert PHASE20_8_RESPONSE_CONTRACT_QA_MATRIX_SCHEMA_VERSION == "cocolon.emlis.response_contract_qa_matrix.v1"
    assert [case.input_family for case in cases] == list(PHASE20_8_INPUT_FAMILIES)
    assert len(cases) == 10
    assert len({case.case_id for case in cases}) == 10
    assert len({case.input_family for case in cases}) == 10
    assert PHASE20_8_EXACT_FIXTURE_TEXT_MATCHING_ALLOWED is False
    assert PHASE20_8_CASE_ID_RUNTIME_CONDITION_ALLOWED is False
    assert set(PHASE20_8_EXACT_FIXTURE_REGRESSION_IDS) == {
        "phase19_real_device_A_low_information_fatigue",
        "phase19_real_device_B_safety_boundary_self_harm_adjacent",
        "phase19_real_device_C_generic_self_understanding_regression",
        "phase19_real_device_D_generic_relationship_boundary_regression",
    }

    for row, meta in zip(rows, meta_rows, strict=True):
        assert set(row.keys()) == {
            "case_id",
            "input_family",
            "expected_response_kind",
            "expected_public_feedback",
            "must_not",
            "quality_assertions",
        }
        assert_phase20_8_response_contract_qa_case_payload(meta)
        assert meta["schema_version"] == PHASE20_8_RESPONSE_CONTRACT_QA_MATRIX_SCHEMA_VERSION
        assert meta["exact_comment_text_expected"] is False
        assert meta["case_id_runtime_condition_allowed"] is False
        assert meta["rn_production_change_required"] is False
        assert meta["raw_input_included"] is False
        assert meta["comment_text_included"] is False
        assert MUST_NOT_UNSUPPORTED_ASSERTION in row["must_not"]
        assert MUST_NOT_FIXED_TEMPLATE in row["must_not"]
        assert "case_specific_route" in row["must_not"]
        assert row["quality_assertions"]

    dumped = _dump(meta_rows)
    for raw in RAW_FIXTURE_FRAGMENTS:
        assert raw not in dumped


def test_phase20_8_matrix_evaluates_response_kind_by_family_not_exact_comment_text() -> None:
    cases = build_phase20_8_response_contract_qa_cases()
    evaluations = [evaluate_phase20_8_response_contract_qa_case(case) for case in cases]
    by_family = {evaluation.input_family: evaluation for evaluation in evaluations}

    assert all(evaluation.response_kind_matches for evaluation in evaluations)
    assert all(not evaluation.fatal_failures for evaluation in evaluations)
    assert by_family[FAMILY_LOW_INFORMATION_SHORT].actual_response_kind == ResponseKind.LOW_INFORMATION_OBSERVATION.value
    assert by_family[FAMILY_LOW_INFORMATION_AMBIGUOUS].actual_response_kind == ResponseKind.LOW_INFORMATION_OBSERVATION.value
    assert by_family[FAMILY_SAFETY_EMERGENCY].actual_response_kind == ResponseKind.SAFETY_BLOCKED_EMERGENCY.value
    assert by_family[FAMILY_SAFETY_EMERGENCY].public_observation_status == "safety_blocked"
    assert by_family[FAMILY_SAFETY_EMERGENCY].actual_public_feedback is False
    assert by_family[FAMILY_SAFETY_EMERGENCY].comment_text_non_empty is False

    for case, evaluation in zip(cases, evaluations, strict=True):
        meta = evaluation.as_meta()
        assert_phase20_8_response_contract_qa_evaluation_payload(meta)
        assert meta["raw_input_included"] is False
        assert meta["comment_text_included"] is False
        if case.expected_public_feedback:
            assert evaluation.public_observation_status == "passed"
            assert evaluation.actual_public_feedback is True
            assert evaluation.comment_text_required is True
            assert evaluation.comment_text_non_empty is True
            assert MUST_NOT_EMPTY_COMMENT_TEXT in case.must_not
        else:
            assert evaluation.actual_response_kind in {
                ResponseKind.SAFETY_SUPPORT_REQUIRED.value,
                ResponseKind.SAFETY_BLOCKED_EMERGENCY.value,
                ResponseKind.INFRASTRUCTURE_ERROR.value,
            }
            assert MUST_NOT_EMPTY_COMMENT_TEXT not in case.must_not

    dumped = _dump([evaluation.as_meta() for evaluation in evaluations])
    for raw in RAW_FIXTURE_FRAGMENTS:
        assert raw not in dumped


def test_phase20_8_report_tracks_new_metrics_and_targets() -> None:
    report = build_phase20_8_response_contract_qa_report()
    meta = report.as_meta()

    assert meta["schema_version"] == PHASE20_8_RESPONSE_CONTRACT_QA_REPORT_SCHEMA_VERSION
    assert meta["case_count"] == 10
    assert meta["family_count"] == 10
    assert meta["always_display_rate"] == 1.0
    assert meta["always_display_rate_target_ready"] is True
    assert meta["low_info_observation_rate"] == 1.0
    assert meta["low_info_observation_rate_target_ready"] is True
    assert meta["unsupported_assertion_count"] == 0
    assert meta["unsupported_assertion_count_target_ready"] is True
    assert meta["template_repeat_rate"] == 0.0
    assert meta["template_repeat_rate_not_increased"] is True
    assert meta["blind_qa_fatal_count"] == 0
    assert meta["blind_qa_fatal_count_target_ready"] is True
    assert meta["self_denial_safe_response_rate"] == 1.0
    assert meta["emergency_safety_not_overridden_count"] == 1
    assert meta["safety_overwrite_count"] == 0
    assert meta["safety_emergency_not_overridden_target_ready"] is True
    assert meta["exact_comment_text_matching_used"] is False
    assert meta["a_c_d_exact_green_is_primary_metric"] is False
    assert meta["raw_input_included"] is False
    assert meta["comment_text_included"] is False
    assert_phase20_8_response_contract_qa_report_payload(meta)


def test_phase20_8_quality_failures_are_fatal_without_changing_runtime_gates() -> None:
    cases = build_phase20_8_response_contract_qa_cases()
    target = next(case for case in cases if case.input_family == "normal_eligible")
    evaluation = evaluate_phase20_8_response_contract_qa_case(
        target,
        rendered_comment_text="まず今すぐ連絡してください。原因はあなたが弱い人だからです。",
        quality_flags={MUST_NOT_FIXED_TEMPLATE: True},
    )

    assert evaluation.response_kind_matches is True
    assert set(evaluation.fatal_failures) >= {
        MUST_NOT_UNSUPPORTED_ASSERTION,
        "personality_label",
        "advice_first",
        MUST_NOT_FIXED_TEMPLATE,
    }
    meta = evaluation.as_meta()
    assert meta["raw_input_included"] is False
    assert meta["comment_text_included"] is False
    assert_phase20_8_response_contract_qa_evaluation_payload(meta)


def test_phase20_8_report_detects_template_repetition_without_using_exact_fixture_success() -> None:
    cases = build_phase20_8_response_contract_qa_cases()
    repeated = {
        case.case_id: "Phase20-8 repeated QA sample." for case in cases if case.expected_public_feedback
    }
    report = build_phase20_8_response_contract_qa_report(rendered_comment_text_by_case_id=repeated)
    meta = report.as_meta()

    assert meta["template_repeat_rate"] > 0.0
    assert meta["template_repeat_count"] > 0
    assert meta["template_repeat_rate_not_increased"] is False
    assert meta["exact_comment_text_matching_used"] is False


def test_phase20_8_keeps_phase19_exact_fixtures_as_regression_not_text_targets() -> None:
    from test_emotion_submit_phase19_real_device_abcd_public_feedback_e2e import (  # noqa: WPS433
        PHASE19_REAL_DEVICE_ABCD_CASES,
    )

    assert [case.case_id for case in PHASE19_REAL_DEVICE_ABCD_CASES] == list(PHASE20_8_EXACT_FIXTURE_REGRESSION_IDS)
    assert not any(hasattr(case, "expected_comment_text") for case in PHASE19_REAL_DEVICE_ABCD_CASES)
    assert not any(hasattr(case, "expected_exact_comment_text") for case in PHASE19_REAL_DEVICE_ABCD_CASES)
    assert all(case.expected_comment_text_non_empty for case in PHASE19_REAL_DEVICE_ABCD_CASES)

    report_meta = build_phase20_8_response_contract_qa_report().as_meta()
    assert report_meta["exact_comment_text_matching_used"] is False
    assert report_meta["a_c_d_exact_green_is_primary_metric"] is False


@pytest.mark.parametrize(
    "bad_payload",
    [
        {
            "schema_version": PHASE20_8_RESPONSE_CONTRACT_QA_MATRIX_SCHEMA_VERSION,
            "source_phase": "Phase20-8_QA_Matrix",
            "case_id": "phase20_8_bad_raw",
            "input_family": "normal_eligible",
            "expected_response_kind": "normal_observation",
            "expected_public_feedback": True,
            "must_not": ["empty_comment_text", "unsupported_assertion", "fixed_template"],
            "quality_assertions": ["response_kind_matches_input_family"],
            "memo": "raw text must not be kept",
            "exact_comment_text_expected": False,
            "case_id_runtime_condition_allowed": False,
            "rn_production_change_required": False,
            "raw_input_included": False,
            "comment_text_included": False,
        },
        {
            "schema_version": PHASE20_8_RESPONSE_CONTRACT_QA_MATRIX_SCHEMA_VERSION,
            "source_phase": "Phase20-8_QA_Matrix",
            "case_id": "phase20_8_bad_exact_text",
            "input_family": "normal_eligible",
            "expected_response_kind": "normal_observation",
            "expected_public_feedback": True,
            "must_not": ["empty_comment_text", "unsupported_assertion", "fixed_template"],
            "quality_assertions": ["response_kind_matches_input_family"],
            "exact_comment_text_expected": True,
            "case_id_runtime_condition_allowed": False,
            "rn_production_change_required": False,
            "raw_input_included": False,
            "comment_text_included": False,
        },
        {
            "schema_version": PHASE20_8_RESPONSE_CONTRACT_QA_MATRIX_SCHEMA_VERSION,
            "source_phase": "Phase20-8_QA_Matrix",
            "case_id": "phase20_8_bad_case_runtime",
            "input_family": "normal_eligible",
            "expected_response_kind": "normal_observation",
            "expected_public_feedback": True,
            "must_not": ["empty_comment_text", "unsupported_assertion", "fixed_template"],
            "quality_assertions": ["response_kind_matches_input_family"],
            "exact_comment_text_expected": False,
            "case_id_runtime_condition_allowed": True,
            "rn_production_change_required": False,
            "raw_input_included": False,
            "comment_text_included": False,
        },
    ],
)
def test_phase20_8_matrix_rejects_schema_drift_exact_text_and_case_runtime_conditions(
    bad_payload: Mapping[str, Any],
) -> None:
    with pytest.raises(ValueError):
        assert_phase20_8_response_contract_qa_case_payload(bad_payload)
