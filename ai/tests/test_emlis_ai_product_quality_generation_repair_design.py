# -*- coding: utf-8 -*-
from __future__ import annotations

import pytest

from emlis_ai_product_quality_blocker_matrix import build_product_quality_blocker_matrix
from emlis_ai_product_quality_generation_repair_design import (
    PRODUCT_QUALITY_GENERATION_REPAIR_DESIGN_ROW_SCHEMA_VERSION,
    PRODUCT_QUALITY_GENERATION_REPAIR_DESIGN_SCHEMA_VERSION,
    assert_product_quality_generation_repair_design_meta_only,
    build_product_quality_generation_repair_design,
    dump_product_quality_generation_repair_design,
)
from emlis_ai_product_quality_measurement_runner import run_product_quality_measurement
from emlis_ai_types import ReplyEnvelope

SECRET_COMMENT = "Phase5 secret comment_text body must never be serialized"
SECRET_INPUT = "Phase5 secret raw input must never be serialized"


def _phase5_events() -> list[dict[str, object]]:
    return [
        {
            "run_id": "pq_phase5_design",
            "row_id": "row_low_001",
            "family": "low_information_short",
            "public_display_reached": False,
            "binding": {"binding_passed": False},
            "reason_coverage": {"reason_coverage_passed": False},
            "surface_quality": {"template_major_count": 0, "mirror_only_detected": False},
            "safety": {"safety_major_count": 0},
            "blockers": ["comment_text_missing", "binding_not_passed"],
        },
        {
            "run_id": "pq_phase5_design",
            "row_id": "row_daily_001",
            "family": "daily_unpleasant",
            "public_display_reached": True,
            "binding": {"binding_passed": True},
            "reason_coverage": {"reason_coverage_passed": False},
            "surface_quality": {"template_major_count": 0, "mirror_only_detected": False},
            "safety": {"safety_major_count": 0},
            "blockers": ["reason_coverage_not_passed"],
        },
        {
            "run_id": "pq_phase5_design",
            "row_id": "row_self_001",
            "family": "self_denial",
            "public_display_reached": False,
            "binding": {"binding_passed": True},
            "reason_coverage": {"reason_coverage_passed": True},
            "surface_quality": {"template_major_count": 0, "mirror_only_detected": False, "unsafe_insight_surface_detected": True},
            "safety": {"safety_major_count": 1},
            "blockers": ["unsafe_insight_surface_detected"],
        },
        {
            "run_id": "pq_phase5_design",
            "row_id": "row_long_001",
            "family": "long_meaning_arc",
            "public_display_reached": True,
            "binding": {"binding_passed": True},
            "reason_coverage": {"reason_coverage_passed": False},
            "surface_quality": {"template_major_count": 0, "mirror_only_detected": False},
            "safety": {"safety_major_count": 0},
            "blockers": ["history_connection_creepiness_risk", "overclaim_or_deciding_risk"],
        },
        {
            "run_id": "pq_phase5_design",
            "row_id": "row_surface_001",
            "family": "mixed_emotion",
            "public_display_reached": True,
            "binding": {"binding_passed": True},
            "reason_coverage": {"reason_coverage_passed": True},
            "surface_quality": {"template_major_count": 1, "mirror_only_detected": True},
            "safety": {"safety_major_count": 0},
            "blockers": ["template_major_detected", "mirror_only_detected"],
        },
    ]


def test_phase5_generation_repair_design_routes_blocker_matrix_to_ordered_tracks_without_contract_or_gate_relaxation() -> None:
    matrix = build_product_quality_blocker_matrix(
        run_id="pq_phase5_design",
        events=_phase5_events(),
        blockers=["blind_qa_review_required"],
    )
    design = build_product_quality_generation_repair_design(
        run_id="pq_phase5_design",
        blocker_matrix=matrix,
    )

    assert design["schema_version"] == PRODUCT_QUALITY_GENERATION_REPAIR_DESIGN_SCHEMA_VERSION
    assert design["product_gate_ready"] is False
    assert design["public_release_applied"] is False
    assert design["contract_change_allowed"] is False
    assert design["gate_relaxation_allowed"] is False
    assert design["fixed_template_allowed"] is False
    assert design["runtime_fixture_branch_allowed"] is False
    assert design["generation_logic_change_required"] is True
    assert design["source_blocker_matrix_row_count"] == matrix["row_count"]
    assert design["generation_repair_work_queue"] == design["rows"]

    tracks = design["repair_execution_order"]
    assert tracks.index("low_information_repair") < tracks.index("daily_mixed_state_answer")
    assert "self_denial_safe_state_answer" in tracks
    assert "surface_repetition_template_smell_repair" in tracks
    assert "user_label_connection_soft_connection_repair" in tracks
    assert "blind_qa_followup_required" in tracks

    low_rows = [row for row in design["rows"] if row["repair_track"] == "low_information_repair"]
    assert low_rows
    assert low_rows[0]["schema_version"] == PRODUCT_QUALITY_GENERATION_REPAIR_DESIGN_ROW_SCHEMA_VERSION
    assert low_rows[0]["target_owner_area"] == "display_repair_low_information"
    assert "emlis_ai_low_information_observation_composer.py" in low_rows[0]["candidate_modules"]
    assert "fixed_sentence_template" in low_rows[0]["forbidden_operation_ids"]
    assert low_rows[0]["contract_change_allowed"] is False
    assert low_rows[0]["gate_relaxation_allowed"] is False
    assert low_rows[0]["runtime_fixture_branch_allowed"] is False

    daily_rows = [row for row in design["rows"] if row["repair_track"] == "daily_mixed_state_answer"]
    assert daily_rows
    assert daily_rows[0]["target_owner_area"] == "state_answer_surface_planner"
    assert "state_answer_ratio_apply" in daily_rows[0]["repair_operation_ids"]

    dumped = dump_product_quality_generation_repair_design(design)
    assert SECRET_COMMENT not in dumped
    assert SECRET_INPUT not in dumped
    assert '"comment_text":' not in dumped
    assert '"raw_input":' not in dumped
    assert '"candidate_body":' not in dumped
    assert_product_quality_generation_repair_design_meta_only(design)


def test_phase5_generation_repair_design_assertion_rejects_body_payload_or_release_flag() -> None:
    matrix = build_product_quality_blocker_matrix(
        run_id="pq_phase5_assertion",
        blockers=["product_readfeel_display_reach_rate_below_target"],
    )
    design = build_product_quality_generation_repair_design(
        run_id="pq_phase5_assertion",
        blocker_matrix=matrix,
    )

    unsafe_body = dict(design)
    unsafe_body["comment_text"] = SECRET_COMMENT
    with pytest.raises(ValueError):
        assert_product_quality_generation_repair_design_meta_only(unsafe_body)

    unsafe_release = dict(design)
    unsafe_release["product_gate_ready"] = True
    with pytest.raises(ValueError):
        assert_product_quality_generation_repair_design_meta_only(unsafe_release)


def test_phase5_measurement_runner_connects_generation_repair_design_without_serializing_comment_or_input_body() -> None:
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
                "case_id": "phase5_runner_empty_comment",
                "family": "daily_unpleasant",
                "current_input": {"memo": SECRET_INPUT},
            }
        ],
        renderer=renderer,
        run_id="pq_phase5_runner_design",
        created_at="2026-06-04T00:00:00Z",
        env={},
        enable_composer=True,
    )

    design = run["generation_repair_design"]
    assert design["schema_version"] == PRODUCT_QUALITY_GENERATION_REPAIR_DESIGN_SCHEMA_VERSION
    assert run["generation_repair_design_row_count"] == design["summary"]["row_count"]
    assert run["generation_repair_design_summary"] == design["summary"]
    assert run["generation_repair_design_rows"] == design["rows"]
    assert run["generation_repair_work_queue"] == design["generation_repair_work_queue"]
    assert "daily_mixed_state_answer" in run["phase5_repair_execution_order"]
    assert design["product_gate_ready"] is False
    assert design["public_release_applied"] is False

    dumped = dump_product_quality_generation_repair_design(design)
    assert SECRET_INPUT not in dumped
    assert '"comment_text":' not in dumped
    assert '"raw_input":' not in dumped
