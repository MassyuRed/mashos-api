# -*- coding: utf-8 -*-
from __future__ import annotations

import pytest

from emlis_ai_product_quality_measurement_runner import (
    COMPOSER_GENERATION_PATH_NOT_OPEN_BLOCKER,
    LOCAL_PRODUCT_QA_PROFILE,
    PRODUCT_QUALITY_MEASUREMENT_REQUIRED_FAMILIES,
    PRODUCT_QUALITY_MEASUREMENT_RUN_SCHEMA_VERSION,
    assert_product_quality_measurement_run_meta_only,
    build_product_quality_minimum_fixture_family_cases,
    dump_product_quality_measurement_run,
    run_product_quality_measurement,
)
from emlis_ai_types import ReplyEnvelope

VISIBLE_COMMENT = "Phase3の表示用comment_textです。run materialへ本文を残してはいけない。"
SECRET_INPUT = "Phase3 secret raw input must never be serialized"


def _passed_reply() -> ReplyEnvelope:
    return ReplyEnvelope(
        comment_text=VISIBLE_COMMENT,
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
                "surface_signature_key": "phase3_unique_signature",
            },
        },
    )


def test_phase3_runner_builds_measurement_run_and_connected_material_without_text_or_contract_changes() -> None:
    def renderer(**_: object) -> ReplyEnvelope:
        return _passed_reply()

    run = run_product_quality_measurement(
        input_cases=build_product_quality_minimum_fixture_family_cases(),
        renderer=renderer,
        run_id="pq_phase3_runner",
        created_at="2026-06-04T00:00:00Z",
        env={},
        enable_composer=True,
    )

    assert run["schema_version"] == PRODUCT_QUALITY_MEASUREMENT_RUN_SCHEMA_VERSION
    assert run["run_profile"] == LOCAL_PRODUCT_QA_PROFILE
    assert run["run_status"] == "completed_with_blockers"
    assert run["event_count"] == len(PRODUCT_QUALITY_MEASUREMENT_REQUIRED_FAMILIES)
    assert run["summary_metrics"]["display_reach_rate"] == 1.0
    assert run["summary_metrics"]["binding_pass_rate"] == 1.0
    assert run["summary_metrics"]["reason_coverage_rate"] == 1.0
    assert run["summary_metrics"]["runtime_surface_blind_qa_coverage_rate"] == 0.0
    assert set(run["family_counts"]) == set(PRODUCT_QUALITY_MEASUREMENT_REQUIRED_FAMILIES)
    assert run["missing_required_families"] == []

    assert len(run["measurement_events"]) == run["event_count"]
    assert len(run["scorecard_rows"]) == run["event_count"]
    assert len(run["runtime_surface_blind_qa_candidates"]) == run["event_count"]
    assert run["product_readfeel_scorecard"]["product_gate_ready"] is False
    assert run["runtime_surface_blind_qa_long_run_summary"]["product_gate_ready"] is False
    assert run["user_label_connection_qa_summary"]["product_gate_ready"] is False
    assert run["phase11_long_run_product_gate"]["product_gate_ready"] is False
    assert run["public_release_applied"] is False
    assert run["contract_assertions"] == {
        "api_route_changed": False,
        "response_shape_changed": False,
        "public_response_key_added": False,
        "db_physical_name_changed": False,
        "rn_visible_contract_changed": False,
        "rn_visible_title_changed": False,
        "comment_text_body_included_in_release_material": False,
        "raw_input_included_in_release_material": False,
        "candidate_body_included_in_release_material": False,
        "display_gate_relaxed": False,
        "grounding_gate_relaxed": False,
        "template_gate_relaxed": False,
    }
    assert "blind_qa_missing" in run["blockers"] or "blind_qa_review_required" in run["blockers"]

    dumped = dump_product_quality_measurement_run(run)
    assert VISIBLE_COMMENT not in dumped
    assert "疲れた" not in dumped
    assert '"comment_text":' not in dumped
    assert '"raw_input":' not in dumped
    assert '"candidate_body":' not in dumped
    assert_product_quality_measurement_run_meta_only(run)


def test_phase3_runner_skips_renderer_when_local_composer_bootstrap_is_blocked() -> None:
    def renderer(**_: object) -> ReplyEnvelope:
        raise AssertionError("renderer must not be called when composer path is closed")

    run = run_product_quality_measurement(
        input_cases=[{"case_id": "blocked_case", "family": "daily_unpleasant", "current_input": {"memo": SECRET_INPUT}}],
        renderer=renderer,
        run_id="pq_phase3_blocked",
        created_at="2026-06-04T00:00:00Z",
        env={},
        enable_composer=False,
    )

    assert run["run_status"] == "blocked"
    assert run["measurement_can_continue"] is False
    assert run["event_count"] == 0
    assert COMPOSER_GENERATION_PATH_NOT_OPEN_BLOCKER in run["blockers"]
    assert "phase3_events_missing" in run["blockers"]
    dumped = dump_product_quality_measurement_run(run)
    assert SECRET_INPUT not in dumped
    assert '"current_input":' not in dumped
    assert run["product_gate_ready"] is False
    assert run["public_release_applied"] is False


def test_phase3_runner_records_display_not_reached_as_event_and_run_blocker() -> None:
    def renderer(**_: object) -> ReplyEnvelope:
        return ReplyEnvelope(
            comment_text="   ",
            meta={
                "version": "emlis_ai_v3",
                "kernel_version": "multi_perspective_observation.v1",
                "tier": "free",
                "observation_status": "passed",
            },
        )

    run = run_product_quality_measurement(
        input_cases=[{"case_id": "empty_comment", "family": "daily_unpleasant", "current_input": {"memo": SECRET_INPUT}}],
        renderer=renderer,
        run_id="pq_phase3_display_not_reached",
        created_at="2026-06-04T00:00:00Z",
        env={},
        enable_composer=True,
    )

    event = run["measurement_events"][0]
    assert event["public_display_reached"] is False
    assert "comment_text_missing" in event["blockers"]
    assert "public_display_not_reached" in event["blockers"]
    assert "product_readfeel_display_reach_rate_below_target" in run["blockers"]
    dumped = dump_product_quality_measurement_run(run)
    assert SECRET_INPUT not in dumped


def test_phase3_measurement_run_assertion_rejects_body_payload_or_release_flag() -> None:
    def renderer(**_: object) -> ReplyEnvelope:
        return _passed_reply()

    run = run_product_quality_measurement(
        input_cases=[{"case_id": "valid", "family": "daily_unpleasant", "current_input": {"memo": SECRET_INPUT}}],
        renderer=renderer,
        run_id="pq_phase3_assertion",
        created_at="2026-06-04T00:00:00Z",
        env={},
        enable_composer=True,
    )

    unsafe_body = dict(run)
    unsafe_body["comment_text"] = VISIBLE_COMMENT
    with pytest.raises(ValueError):
        assert_product_quality_measurement_run_meta_only(unsafe_body)

    unsafe_release = dict(run)
    unsafe_release["product_gate_ready"] = True
    with pytest.raises(ValueError):
        assert_product_quality_measurement_run_meta_only(unsafe_release)
