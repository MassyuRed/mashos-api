# -*- coding: utf-8 -*-
from __future__ import annotations

import pytest

from helpers.emlis_ai_phase18_product_quality_matrix import (
    CHECK_COMPLETE_INITIAL_CANDIDATE_GENERATION_PATH,
    CHECK_DAILY_UNPLEASANT_MODE_CONTEXT,
    CHECK_DIAGNOSTIC_CLASSIFICATION_TAXONOMY,
    CHECK_LOW_INFORMATION_PUBLIC_REPAIR,
    CHECK_OBSERVATION_STRUCTURE_META_ONLY_BOUNDARY,
    CHECK_PHASE17_PRODUCT_VISIBLE_FIVE_FIXTURES,
    CHECK_RN_PASSED_COMMENT_TEXT_CONTRACT,
    CHECK_VISIBLE_READABILITY_QUALITY,
    PHASE18_PRODUCT_QUALITY_BASELINE_SCHEMA_VERSION,
    PHASE18_PRODUCT_QUALITY_MATRIX_ID,
    PHASE18_PRODUCT_QUALITY_MATRIX_SCHEMA_VERSION,
    PHASE18_PRODUCT_QUALITY_REQUIRED_CHECK_IDS,
    PHASE18_PRODUCT_QUALITY_SOURCE_PHASE,
    STATUS_GREEN,
    STATUS_NOT_RUN,
    STATUS_RED,
    assert_phase18_product_quality_matrix_meta_only,
    build_phase18_0_local_baseline_observations,
    build_phase18_product_quality_matrix_with_observations,
    build_phase18_product_quality_regression_matrix,
)


def test_phase18_1_product_quality_regression_matrix_schema_and_release_blockers_are_fixed() -> None:
    matrix = build_phase18_product_quality_regression_matrix()

    assert matrix["schema_version"] == PHASE18_PRODUCT_QUALITY_MATRIX_SCHEMA_VERSION
    assert matrix["source_phase"] == PHASE18_PRODUCT_QUALITY_SOURCE_PHASE
    assert matrix["matrix_id"] == PHASE18_PRODUCT_QUALITY_MATRIX_ID
    assert [check["check_id"] for check in matrix["checks"]] == list(PHASE18_PRODUCT_QUALITY_REQUIRED_CHECK_IDS)
    assert all(check["required_status"] == STATUS_GREEN for check in matrix["checks"])
    assert all(check["blocks_release"] is True for check in matrix["checks"])
    assert matrix["public_contract"] == {
        "public_response_key_added": False,
        "observation_text_key_added": False,
        "reception_text_key_added": False,
        "rn_visible_contract_changed": False,
        "db_physical_name_changed": False,
        "api_route_changed": False,
        "raw_input_included": False,
        "raw_text_included": False,
        "comment_text_body_included": False,
        "generated_candidate_text_included": False,
        "surface_policy_included": False,
    }
    assert matrix["implementation_contract"]["external_ai_added"] is False
    assert matrix["implementation_contract"]["local_llm_added"] is False
    assert matrix["implementation_contract"]["runtime_completed_reply_templates_added"] is False
    assert_phase18_product_quality_matrix_meta_only(matrix)


def test_phase18_0_local_baseline_records_current_green_and_red_without_public_body_leak() -> None:
    baseline = build_phase18_0_local_baseline_observations()
    observations = baseline["observations"]

    assert baseline["schema_version"] == PHASE18_PRODUCT_QUALITY_BASELINE_SCHEMA_VERSION
    assert baseline["source_phase"] == PHASE18_PRODUCT_QUALITY_SOURCE_PHASE
    assert set(observations) == set(PHASE18_PRODUCT_QUALITY_REQUIRED_CHECK_IDS)
    assert observations[CHECK_PHASE17_PRODUCT_VISIBLE_FIVE_FIXTURES]["observed_status"] == STATUS_GREEN
    assert observations[CHECK_PHASE17_PRODUCT_VISIBLE_FIVE_FIXTURES]["passed"] == 33
    assert observations[CHECK_RN_PASSED_COMMENT_TEXT_CONTRACT]["observed_status"] == STATUS_GREEN
    assert observations[CHECK_RN_PASSED_COMMENT_TEXT_CONTRACT]["passed"] == 32
    assert observations[CHECK_COMPLETE_INITIAL_CANDIDATE_GENERATION_PATH]["observed_status"] == STATUS_RED
    assert observations[CHECK_LOW_INFORMATION_PUBLIC_REPAIR]["observed_status"] == STATUS_RED
    assert observations[CHECK_DAILY_UNPLEASANT_MODE_CONTEXT]["observed_status"] == STATUS_RED
    assert observations[CHECK_OBSERVATION_STRUCTURE_META_ONLY_BOUNDARY]["observed_status"] == STATUS_RED
    assert observations[CHECK_DIAGNOSTIC_CLASSIFICATION_TAXONOMY]["observed_status"] == STATUS_RED
    assert observations[CHECK_VISIBLE_READABILITY_QUALITY]["observed_status"] == STATUS_NOT_RUN
    assert baseline["public_contract"]["public_response_key_added"] is False
    assert baseline["public_contract"]["comment_text_body_included"] is False
    assert baseline["gate_policy"]["display_gate_relaxed"] is False
    assert baseline["gate_policy"]["grounding_gate_relaxed"] is False
    assert_phase18_product_quality_matrix_meta_only(baseline)


def test_phase18_1_baseline_summary_blocks_release_until_all_required_checks_are_green() -> None:
    matrix = build_phase18_product_quality_matrix_with_observations()
    summary = matrix["summary"]

    assert summary["release_ready"] is False
    assert summary["green_check_ids"] == [
        CHECK_PHASE17_PRODUCT_VISIBLE_FIVE_FIXTURES,
        CHECK_RN_PASSED_COMMENT_TEXT_CONTRACT,
    ]
    assert summary["red_check_ids"] == [
        CHECK_COMPLETE_INITIAL_CANDIDATE_GENERATION_PATH,
        CHECK_LOW_INFORMATION_PUBLIC_REPAIR,
        CHECK_DAILY_UNPLEASANT_MODE_CONTEXT,
        CHECK_OBSERVATION_STRUCTURE_META_ONLY_BOUNDARY,
        CHECK_DIAGNOSTIC_CLASSIFICATION_TAXONOMY,
    ]
    assert summary["not_run_check_ids"] == [CHECK_VISIBLE_READABILITY_QUALITY]
    assert summary["blocking_not_green_check_ids"] == [
        CHECK_COMPLETE_INITIAL_CANDIDATE_GENERATION_PATH,
        CHECK_LOW_INFORMATION_PUBLIC_REPAIR,
        CHECK_DAILY_UNPLEASANT_MODE_CONTEXT,
        CHECK_OBSERVATION_STRUCTURE_META_ONLY_BOUNDARY,
        CHECK_DIAGNOSTIC_CLASSIFICATION_TAXONOMY,
        CHECK_VISIBLE_READABILITY_QUALITY,
    ]
    assert_phase18_product_quality_matrix_meta_only(matrix)


def test_phase18_1_matrix_accepts_future_green_observations_without_contract_change() -> None:
    observed_statuses = {check_id: STATUS_GREEN for check_id in PHASE18_PRODUCT_QUALITY_REQUIRED_CHECK_IDS}
    matrix = build_phase18_product_quality_matrix_with_observations(observed_statuses)

    assert matrix["summary"]["release_ready"] is True
    assert matrix["summary"]["blocking_not_green_check_ids"] == []
    assert matrix["summary"]["green_check_count"] == len(PHASE18_PRODUCT_QUALITY_REQUIRED_CHECK_IDS)
    assert matrix["summary"]["red_check_count"] == 0
    assert matrix["public_contract"]["public_response_key_added"] is False
    assert matrix["public_contract"]["rn_visible_contract_changed"] is False
    assert matrix["gate_policy"]["display_gate_relaxed"] is False
    assert matrix["gate_policy"]["grounding_gate_relaxed"] is False
    assert_phase18_product_quality_matrix_meta_only(matrix)


def test_phase18_1_matrix_rejects_missing_unknown_or_unsupported_statuses() -> None:
    with pytest.raises(ValueError, match="missing"):
        build_phase18_product_quality_matrix_with_observations({})

    with pytest.raises(ValueError, match="unknown"):
        build_phase18_product_quality_matrix_with_observations(
            {**{check_id: STATUS_GREEN for check_id in PHASE18_PRODUCT_QUALITY_REQUIRED_CHECK_IDS}, "extra": STATUS_GREEN}
        )

    with pytest.raises(ValueError, match="Unsupported"):
        build_phase18_product_quality_matrix_with_observations(
            {
                **{check_id: STATUS_GREEN for check_id in PHASE18_PRODUCT_QUALITY_REQUIRED_CHECK_IDS},
                CHECK_LOW_INFORMATION_PUBLIC_REPAIR: "yellow",
            }
        )
