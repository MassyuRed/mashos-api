# -*- coding: utf-8 -*-
from __future__ import annotations

import pytest

from emlis_ai_product_release_decision import (
    PRODUCT_RELEASE_DECISION_PHASE,
    PRODUCT_RELEASE_DECISION_SCHEMA_VERSION,
    RELEASE_STAGE_RELEASE_CANDIDATE,
    assert_product_release_decision_meta_only,
    build_product_release_decision,
    dump_product_release_decision,
)
from emlis_ai_product_quality_measurement_runner import (
    dump_product_quality_measurement_run,
    run_product_quality_measurement,
)
from emlis_ai_reply_service import ReplyEnvelope

SECRET_INPUT = "PHASE7_SECRET_INPUT_SHOULD_NOT_SURVIVE"
SECRET_COMMENT = "PHASE7_SECRET_COMMENT_SHOULD_NOT_SURVIVE"


def _green_summary_metrics() -> dict[str, object]:
    return {
        "display_reach_rate": 1.0,
        "binding_pass_rate": 1.0,
        "reason_coverage_rate": 1.0,
        "runtime_surface_blind_qa_coverage_rate": 1.0,
        "runtime_surface_blind_qa_read_feeling_score": 1.0,
        "user_label_connection_qa_coverage_rate": 1.0,
        "user_label_connection_quality_score": 1.0,
        "five_consecutive_product_pass": True,
        "ten_consecutive_product_pass": True,
        "red_review_count": 0,
        "repair_required_row_count": 0,
        "template_major_count": 0,
        "safety_major_count": 0,
        "surface_signature_repeat_rate": 0.0,
    }


def _green_blind_integration() -> dict[str, object]:
    return {
        "blind_qa_integration_ready": True,
        "release_blockers": [],
        "runtime_surface": {
            "review_coverage_rate": 1.0,
            "read_feeling_score": 1.0,
            "red_review_count": 0,
        },
        "user_label_connection": {
            "review_coverage_rate": 1.0,
            "quality_score": 1.0,
            "red_review_count": 0,
            "dimension_scores": {
                "read_feeling": 1.0,
                "history_connection_naturalness": 1.0,
                "creepy_absence": 1.0,
                "overclaim_absence": 1.0,
                "self_blame_non_amplification": 1.0,
                "non_shallow_repeat": 1.0,
            },
        },
        "product_gate_ready": False,
        "public_release_applied": False,
    }


def _green_phase11() -> dict[str, object]:
    return {
        "v1_product_pass_candidate": True,
        "v1_product_pass_blockers": [],
        "sequence_report": {
            "v1_product_pass": {
                "consecutive_5_ready": True,
                "consecutive_10_ready": True,
            }
        },
        "surface_repetition_report": {"family_cross_surface_repetition_detected": False},
        "product_gate_ready": False,
        "public_release_applied": False,
    }


def test_phase7_release_decision_collects_blockers_and_followup_fixes_without_release_flags() -> None:
    decision = build_product_release_decision(
        run_id="pq_phase7_blocked",
        run_status="completed_with_blockers",
        event_count=1,
        family_counts={"low_information_short": 1},
        missing_required_families=["daily_unpleasant"],
        summary_metrics={
            "display_reach_rate": 0.0,
            "binding_pass_rate": 0.0,
            "reason_coverage_rate": 0.0,
            "runtime_surface_blind_qa_coverage_rate": 0.0,
            "user_label_connection_qa_coverage_rate": 0.0,
        },
        composer_bootstrap={"measurement_can_continue": True, "composer_generation_path_open": True, "blockers": []},
        blocker_matrix={
            "row_count": 1,
            "release_blocking_row_count": 1,
            "rows": [
                {
                    "blocker_id": "product_readfeel_display_reach_rate_below_target",
                    "likely_owner_area": "display_reach_repair",
                    "repair_policy": "Gateを緩めず表示可能な観測文へ戻す",
                    "candidate_modules": ["emlis_ai_observation_display_repair_integration.py"],
                    "release_blocking": True,
                    "product_gate_ready": False,
                    "public_release_applied": False,
                }
            ],
            "product_gate_ready": False,
            "public_release_applied": False,
        },
        blind_qa_integration={"blind_qa_integration_ready": False, "release_blockers": ["blind_qa_review_required"]},
        phase11_long_run_product_gate={"v1_product_pass_candidate": False, "v1_product_pass_blockers": ["phase11_events_missing"]},
        runtime_surface_blind_qa_long_run_summary={"runtime_surface_blind_qa_long_run_ready": False, "release_blockers": ["blind_qa_missing"]},
        user_label_connection_qa_summary={"user_label_connection_product_quality_qa_ready": False, "release_blockers": ["history_connection_creepiness_risk"]},
    )

    assert decision["schema_version"] == PRODUCT_RELEASE_DECISION_SCHEMA_VERSION
    assert decision["phase"] == PRODUCT_RELEASE_DECISION_PHASE
    assert decision["release_allowed"] is False
    assert "product_readfeel_display_reach_rate_below_target" in decision["release_blockers"]
    assert "blind_qa_review_required" in decision["release_blockers"]
    assert "phase11_events_missing" in decision["release_blockers"]
    display_fix = [fix for fix in decision["required_followup_fixes"] if fix["blocker_id"] == "product_readfeel_display_reach_rate_below_target"][0]
    assert display_fix["owner_area"] == "display_reach_repair"
    assert display_fix["contract_change_allowed"] is False
    assert display_fix["gate_relaxation_allowed"] is False
    assert decision["product_gate_ready"] is False
    assert decision["public_release_applied"] is False
    assert decision["contract_assertions"]["public_response_key_added"] is False
    assert_product_release_decision_meta_only(decision)


def test_phase7_release_decision_requires_explicit_release_candidate_evidence_even_when_targets_green() -> None:
    decision = build_product_release_decision(
        run_id="pq_phase7_green_without_shadow",
        run_status="completed",
        event_count=12,
        family_counts={"daily_unpleasant": 1, "self_denial": 1},
        missing_required_families=[],
        summary_metrics=_green_summary_metrics(),
        composer_bootstrap={"measurement_can_continue": True, "composer_generation_path_open": True, "blockers": []},
        blocker_matrix={"row_count": 0, "release_blocking_row_count": 0, "rows": [], "product_gate_ready": False, "public_release_applied": False},
        blind_qa_integration=_green_blind_integration(),
        runtime_surface_blind_qa_long_run_summary={"runtime_surface_blind_qa_long_run_ready": True, "release_blockers": []},
        user_label_connection_qa_summary={"user_label_connection_product_quality_qa_ready": True, "release_blockers": []},
        phase11_long_run_product_gate=_green_phase11(),
    )

    assert decision["release_allowed"] is False
    assert "release_candidate_shadow_evidence_missing" in decision["release_blockers"]
    assert decision["readiness_flags"]["all_score_targets_met"] is True
    assert decision["readiness_flags"]["release_candidate_evidence_confirmed"] is False


def test_phase7_release_decision_can_allow_release_candidate_only_with_no_blockers_and_explicit_evidence() -> None:
    decision = build_product_release_decision(
        run_id="pq_phase7_release_candidate",
        run_status="completed",
        event_count=12,
        family_counts={"daily_unpleasant": 1, "self_denial": 1},
        missing_required_families=[],
        summary_metrics=_green_summary_metrics(),
        composer_bootstrap={"measurement_can_continue": True, "composer_generation_path_open": True, "blockers": []},
        blocker_matrix={"row_count": 0, "release_blocking_row_count": 0, "rows": [], "product_gate_ready": False, "public_release_applied": False},
        blind_qa_integration=_green_blind_integration(),
        runtime_surface_blind_qa_long_run_summary={"runtime_surface_blind_qa_long_run_ready": True, "release_blockers": []},
        user_label_connection_qa_summary={"user_label_connection_product_quality_qa_ready": True, "release_blockers": []},
        phase11_long_run_product_gate=_green_phase11(),
        release_candidate_evidence_confirmed=True,
    )

    assert decision["release_allowed"] is True
    assert decision["release_stage"] == RELEASE_STAGE_RELEASE_CANDIDATE
    assert decision["release_blockers"] == []
    assert decision["product_gate_ready"] is False
    assert decision["public_release_applied"] is False
    assert_product_release_decision_meta_only(decision)


def test_phase7_release_decision_assertion_rejects_body_payload_release_flag_or_invalid_allowed_state() -> None:
    base = build_product_release_decision(run_id="pq_phase7_assertion")

    unsafe_body = dict(base)
    unsafe_body["comment_text"] = SECRET_COMMENT
    with pytest.raises(ValueError):
        assert_product_release_decision_meta_only(unsafe_body)

    unsafe_release = dict(base)
    unsafe_release["product_gate_ready"] = True
    with pytest.raises(ValueError):
        assert_product_release_decision_meta_only(unsafe_release)

    unsafe_allowed = dict(base)
    unsafe_allowed["release_allowed"] = True
    unsafe_allowed["release_stage"] = "internal_qa"
    unsafe_allowed["release_blockers"] = []
    with pytest.raises(ValueError):
        assert_product_release_decision_meta_only(unsafe_allowed)


def test_phase7_detects_source_text_payload_without_serializing_it() -> None:
    decision = build_product_release_decision(
        run_id="pq_phase7_text_payload",
        measurement_run={
            "run_id": "pq_phase7_text_payload",
            "event_count": 1,
            "family_counts": {"daily_unpleasant": 1},
            "summary_metrics": {"display_reach_rate": 1.0},
            "blockers": [],
            "product_gate_ready": False,
            "public_release_applied": False,
        },
        product_readfeel_scorecard={"comment_text": SECRET_COMMENT, "product_gate_ready": False, "public_release_applied": False},
        composer_resolution_summary={"measurement_can_continue": True, "composer_generation_path_open": True},
    )

    assert decision["release_allowed"] is False
    assert "release_decision_text_payload_detected" in decision["release_blockers"]
    dumped = dump_product_release_decision(decision)
    assert SECRET_COMMENT not in dumped
    assert '"comment_text":' not in dumped


def test_phase7_measurement_runner_connects_release_decision_without_serializing_bodies() -> None:
    def renderer(**_: object) -> ReplyEnvelope:
        return ReplyEnvelope(
            comment_text=SECRET_COMMENT,
            meta={
                "version": "emlis_ai_v3",
                "kernel_version": "multi_perspective_observation.v1",
                "tier": "free",
                "observation_status": "passed",
                "runtime_surface_pre_return_gate": {"passed": True, "action": "allow"},
                "visible_surface_acceptance_gate": {"classification": "pass", "action": "allow"},
                "state_answer_gate_boundary": {"passed": True},
                "diagnostic_summary": {
                    "binding_required_count": 1,
                    "binding_supported_count": 1,
                    "reason_required_count": 0,
                    "reason_covered_count": 0,
                    "surface_signature_key": "phase7_runner_signature",
                },
            },
        )

    run = run_product_quality_measurement(
        input_cases=[{"case_id": "phase7_runner", "family": "daily_unpleasant", "current_input": {"memo": SECRET_INPUT}}],
        renderer=renderer,
        run_id="pq_phase7_runner",
        created_at="2026-06-04T00:00:00Z",
        env={},
        enable_composer=True,
    )

    decision = run["release_decision"]
    assert decision["schema_version"] == PRODUCT_RELEASE_DECISION_SCHEMA_VERSION
    assert run["release_decision_summary"]["release_allowed"] is False
    assert run["release_decision_summary"]["release_stage"] == decision["release_stage"]
    assert run["release_decision_release_blockers"] == decision["release_blockers"]
    assert run["release_decision_required_followup_fixes"] == decision["required_followup_fixes"]
    assert run["phase7_release_decision_internal_only"] is True
    assert decision["product_gate_ready"] is False
    assert decision["public_release_applied"] is False
    dumped_decision = dump_product_release_decision(decision)
    dumped_run = dump_product_quality_measurement_run(run)
    assert SECRET_INPUT not in dumped_decision
    assert SECRET_INPUT not in dumped_run
    assert '"comment_text":' not in dumped_decision
    assert '"comment_text":' not in dumped_run
    assert_product_release_decision_meta_only(decision)
