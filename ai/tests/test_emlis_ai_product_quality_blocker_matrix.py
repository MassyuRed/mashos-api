# -*- coding: utf-8 -*-
from __future__ import annotations

import pytest

from emlis_ai_product_quality_blocker_matrix import (
    PRODUCT_QUALITY_BLOCKER_MATRIX_ROW_SCHEMA_VERSION,
    PRODUCT_QUALITY_BLOCKER_MATRIX_SCHEMA_VERSION,
    assert_product_quality_blocker_matrix_meta_only,
    build_product_quality_blocker_matrix,
    classify_product_quality_blocker,
    dump_product_quality_blocker_matrix,
)
from emlis_ai_product_quality_measurement_runner import run_product_quality_measurement
from emlis_ai_types import ReplyEnvelope

SECRET_COMMENT = "Phase4 secret comment_text body must never be serialized"
SECRET_INPUT = "Phase4 secret raw input must never be serialized"


def _blocked_display_event() -> dict[str, object]:
    return {
        "schema_version": "cocolon.emlis.product_quality.measurement_event.v1",
        "run_id": "pq_phase4_matrix",
        "row_id": "row_low_001",
        "family": "low_information_short",
        "public_display_reached": False,
        "comment_text_present": False,
        "comment_text_length": 0,
        "binding": {
            "binding_required_count": 1,
            "binding_supported_count": 0,
            "unsupported_binding_count": 1,
            "binding_passed": False,
        },
        "reason_coverage": {
            "reason_required_count": 1,
            "reason_covered_count": 0,
            "reason_coverage_passed": False,
        },
        "surface_quality": {
            "surface_signature_key": "phase4_low_info_signature",
            "template_major_count": 1,
            "mirror_only_detected": True,
            "unsafe_insight_surface_detected": False,
        },
        "safety": {"safety_major_count": 0},
        "blockers": [
            "public_display_not_reached",
            "comment_text_missing",
            "binding_not_passed",
            "reason_coverage_not_passed",
            "template_major_detected",
        ],
    }


def test_phase4_blocker_matrix_routes_release_blockers_to_owner_and_repair_policy_without_contract_change() -> None:
    matrix = build_product_quality_blocker_matrix(
        run_id="pq_phase4_matrix",
        events=[_blocked_display_event()],
        blockers=[
            "product_readfeel_display_reach_rate_below_target",
            "product_readfeel_binding_pass_rate_below_target",
            "product_readfeel_reason_coverage_below_target",
            "blind_qa_review_required",
        ],
        summary_metrics={
            "display_reach_rate": 0.0,
            "binding_pass_rate": 0.0,
            "reason_coverage_rate": 0.0,
            "runtime_surface_blind_qa_coverage_rate": 0.0,
            "user_label_connection_qa_coverage_rate": 0.0,
            "template_major_count": 1,
        },
        family_counts={"low_information_short": 1},
        missing_required_families=["daily_unpleasant"],
        runtime_summary={"release_blockers": ["blind_qa_missing"]},
        user_label_summary={"release_blockers": ["history_connection_creepiness_risk"]},
        phase11_gate={"v1_product_pass_blockers": ["five_consecutive_v1_product_pass_not_observed"]},
    )

    assert matrix["schema_version"] == PRODUCT_QUALITY_BLOCKER_MATRIX_SCHEMA_VERSION
    assert matrix["product_gate_ready"] is False
    assert matrix["public_release_applied"] is False
    assert matrix["all_release_blockers_have_owner_area"] is True
    assert matrix["all_release_blockers_have_repair_policy"] is True
    assert matrix["release_blocking_row_count"] == len(matrix["rows"])
    assert matrix["repair_work_queue"] == matrix["rows"]

    display_rows = [
        row for row in matrix["rows"] if row["blocker_id"] == "product_readfeel_display_reach_rate_below_target"
    ]
    assert display_rows
    display_row = display_rows[0]
    assert display_row["schema_version"] == PRODUCT_QUALITY_BLOCKER_MATRIX_ROW_SCHEMA_VERSION
    assert display_row["family"] == "low_information_short"
    assert display_row["blocker_group"] == "low_information"
    assert display_row["likely_owner_area"] == "display_repair_low_information"
    assert "emlis_ai_low_information_observation_composer.py" in display_row["candidate_modules"]
    assert display_row["contract_change_allowed"] is False
    assert display_row["gate_relaxation_allowed"] is False
    assert display_row["release_blocking"] is True
    assert display_row["target_metric"] == "display_reach_rate"
    assert display_row["target_metric_value"] == 0.9
    assert "row_low_001" in display_row["sample_row_ids"]

    assert matrix["blocker_group_counts"]["binding"] >= 1
    assert matrix["blocker_group_counts"]["blind_qa"] >= 1
    assert matrix["blocker_group_counts"]["user_label_connection"] >= 1
    assert matrix["blocker_group_counts"]["phase11_long_run"] >= 1

    dumped = dump_product_quality_blocker_matrix(matrix)
    assert SECRET_COMMENT not in dumped
    assert SECRET_INPUT not in dumped
    assert '"comment_text":' not in dumped
    assert '"raw_input":' not in dumped
    assert '"candidate_body":' not in dumped
    assert_product_quality_blocker_matrix_meta_only(matrix)


def test_phase4_blocker_classifier_never_returns_empty_owner_or_policy_for_unknown_blocker() -> None:
    classified = classify_product_quality_blocker("new_unmapped_blocker", family="daily_unpleasant")

    assert classified["blocker_group"] == "unmapped_product_quality_blocker"
    assert classified["likely_owner_area"] == "product_quality_measurement_triage"
    assert classified["repair_policy"]
    assert classified["contract_change_allowed"] is False
    assert classified["release_blocking"] is True


def test_phase4_blocker_matrix_assertion_rejects_body_payload_or_release_flag() -> None:
    matrix = build_product_quality_blocker_matrix(
        run_id="pq_phase4_assertion",
        blockers=["blind_qa_review_required"],
        summary_metrics={"runtime_surface_blind_qa_coverage_rate": 0.0},
    )

    unsafe_body = dict(matrix)
    unsafe_body["comment_text"] = SECRET_COMMENT
    with pytest.raises(ValueError):
        assert_product_quality_blocker_matrix_meta_only(unsafe_body)

    unsafe_release = dict(matrix)
    unsafe_release["product_gate_ready"] = True
    with pytest.raises(ValueError):
        assert_product_quality_blocker_matrix_meta_only(unsafe_release)


def test_phase4_measurement_runner_connects_blocker_matrix_without_body_payloads() -> None:
    def renderer(**_: object) -> ReplyEnvelope:
        return ReplyEnvelope(
            comment_text=" ",
            meta={
                "version": "emlis_ai_v3",
                "kernel_version": "multi_perspective_observation.v1",
                "tier": "free",
                "observation_status": "passed",
            },
        )

    run = run_product_quality_measurement(
        input_cases=[
            {
                "case_id": "phase4_runner_empty_comment",
                "family": "daily_unpleasant",
                "current_input": {"memo": SECRET_INPUT},
            }
        ],
        renderer=renderer,
        run_id="pq_phase4_runner_matrix",
        created_at="2026-06-04T00:00:00Z",
        env={},
        enable_composer=True,
    )

    matrix = run["blocker_matrix"]
    assert matrix["schema_version"] == PRODUCT_QUALITY_BLOCKER_MATRIX_SCHEMA_VERSION
    assert run["blocker_matrix_summary"]["row_count"] == matrix["row_count"]
    assert run["blocker_matrix_summary"]["release_blocking_row_count"] == matrix["release_blocking_row_count"]
    assert run["blocker_matrix_summary"]["blocker_group_counts"] == matrix["blocker_group_counts"]
    assert run["blocker_matrix_summary"]["owner_area_counts"] == matrix["owner_area_counts"]
    assert run["blocker_matrix_summary"]["all_release_blockers_have_owner_area_and_repair_policy"] is True
    assert run["blocker_matrix_rows"] == matrix["rows"]
    assert run["repair_work_queue"] == matrix["repair_work_queue"]
    assert any(row["blocker_id"] == "product_readfeel_display_reach_rate_below_target" for row in matrix["rows"])
    assert any(row["blocker_id"] == "comment_text_missing" for row in matrix["rows"])
    dumped = dump_product_quality_blocker_matrix(matrix)
    assert SECRET_INPUT not in dumped
    assert '"comment_text":' not in dumped
    assert matrix["product_gate_ready"] is False
    assert matrix["public_release_applied"] is False
