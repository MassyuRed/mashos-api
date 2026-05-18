from __future__ import annotations

import json

import pytest

from emlis_ai_complete_product_quality_measurement_connection import (
    COMPLETE_PRODUCT_QUALITY_MEASUREMENT_EXIT_GATE_REQUIRED_FIXTURE_CLASSES,
    COMPLETE_PRODUCT_QUALITY_MEASUREMENT_EXIT_GATE_STEP,
    ProductQualityMeasurementConnectionError,
    build_complete_product_quality_measurement_connection,
    dump_complete_product_quality_measurement_connection,
)


def _row(
    trace_id: str,
    *,
    backend_status: str = "passed",
    backend_len: int = 120,
    frontend_joined: bool = True,
    modal_opened: bool | None = True,
    display_confirmed: bool = True,
    classification: str = "passed_displayed",
    measurement_classification: str | None = None,
    primary_reason: str = "passed",
    display_blockers: list[str] | None = None,
    coverage_group: str = "short_daily",
) -> dict:
    return {
        "trace_id": trace_id,
        "emotion_log_id": trace_id,
        "coverage_group": coverage_group,
        "backend_status": backend_status,
        "backend_len": backend_len,
        "backend_comment_text_present": backend_len > 0,
        "backend_public_passed": backend_status == "passed" and backend_len > 0,
        "frontend_joined": frontend_joined,
        "frontend_join_status": "joined" if frontend_joined else "missing",
        "modal_opened": modal_opened,
        "display_confirmed": display_confirmed,
        "diagnostic_capture_status": "captured" if frontend_joined else "frontend_diagnostic_missing_or_not_captured",
        "backend_diagnostic_capture_status": "captured",
        "frontend_diagnostic_capture_status": "captured" if frontend_joined else "frontend_diagnostic_missing_or_not_captured",
        "classification": classification,
        "measurement_classification": measurement_classification or classification,
        "primary_reason": primary_reason,
        "candidate_generated": True,
        "display_count_blockers": list(display_blockers or []),
        "binding_supported_sentence_count": 1 if display_confirmed else 0,
        "expected_binding_count": 1 if backend_status == "passed" else 0,
        "raw_input_included": False,
        "comment_text_included": False,
    }


def _diagnostic_missing_row() -> dict:
    return {
        "trace_id": "step10-diagnostic-missing",
        "emotion_log_id": "step10-diagnostic-missing",
        "diagnostic_capture_status": "backend_diagnostic_missing_or_not_captured",
        "backend_diagnostic_capture_status": "backend_diagnostic_missing_or_not_captured",
        "classification": "unknown_diagnostic_missing",
        "measurement_classification": "unknown_diagnostic_missing",
        "display_confirmed": False,
        "raw_input_included": False,
        "comment_text_included": False,
    }


def _four_fixture_rows() -> list[dict]:
    return [
        _diagnostic_missing_row(),
        _row(
            "step10-backend-rejected",
            backend_status="rejected",
            backend_len=0,
            modal_opened=False,
            display_confirmed=False,
            classification="candidate_generated_but_grounding_rejected",
            primary_reason="unsupported_sentence",
            coverage_group="conflict",
        ),
        _row(
            "step10-passed-hidden",
            modal_opened=False,
            display_confirmed=False,
            classification="passed_backend_frontend_hidden",
            primary_reason="frontend_modal_not_opened",
            display_blockers=["frontend_modal_not_opened"],
            coverage_group="relationship",
        ),
        _row("step10-display-confirmed", coverage_group="pressure"),
    ]


def test_step10_exit_gate_completes_measurement_connection_without_product_gate_release() -> None:
    report = build_complete_product_quality_measurement_connection(
        rows=_four_fixture_rows(),
        run_id="step10-four-fixture-run",
    )
    summary = report["exit_gate_summary"]

    assert report["measurement_latest_step"] == COMPLETE_PRODUCT_QUALITY_MEASUREMENT_EXIT_GATE_STEP
    assert report["exit_gate_summary_ready"] is True
    assert report["measurement_exit_gate_completed"] is True
    assert report["measurement_connection_complete"] is True
    assert report["product_gate_measurement_connection_complete"] is True
    assert report["minimum_exit_gate_fixture_coverage_complete"] is True
    assert summary["observed_fixture_classes"] == list(COMPLETE_PRODUCT_QUALITY_MEASUREMENT_EXIT_GATE_REQUIRED_FIXTURE_CLASSES)
    assert summary["missing_fixture_classes"] == []
    assert report["scorecard_event_count"] == 4
    assert report["display_confirmed_count"] == 1
    assert report["passed_display_count"] == 1
    assert report["scorecard_passed_display_count"] == 1
    assert report["product_gate_ready"] is False
    assert report["product_gate_reached"] is False
    assert report["product_gate_achieved"] is False
    assert report["product_gate_public_release_applied"] is False
    assert report["public_release_applied"] is False
    assert report["release_judgment"]["release_allowed"] is False
    assert report["release_judgment"]["reason"] == "step10_exit_gate_measurement_connection_only_public_release_not_applied"
    assert summary["next_action_reason_source_order"] == [
        "diagnostic_capture_gap",
        "classification_counter",
        "release_blockers",
        "top_rejection_reasons",
    ]
    assert "unknown_diagnostic_missing" in summary["classification_counter"]
    assert "unsupported_sentence" in summary["top_rejection_reasons"]
    assert summary["public_contract_unchanged"] is True
    assert summary["product_release_closed"] is True
    assert summary["raw_input_included"] is False
    assert summary["comment_text_included"] is False

    dumped = json.loads(dump_complete_product_quality_measurement_connection(report))
    assert dumped["measurement_connection_complete"] is True
    assert dumped["exit_gate_summary"]["product_gate_achieved"] is False
    assert "comment_text" not in dumped


def test_step10_single_display_run_is_connected_but_fixture_coverage_remains_visible() -> None:
    report = build_complete_product_quality_measurement_connection(
        rows=[_row("step10-single-display")],
        run_id="step10-single-display-run",
    )
    summary = report["exit_gate_summary"]

    assert report["measurement_connection_complete"] is True
    assert report["display_confirmed_count"] == 1
    assert report["passed_display_count"] == 1
    assert report["minimum_exit_gate_fixture_coverage_complete"] is False
    assert summary["observed_fixture_classes"] == ["display_confirmed"]
    assert "diagnostic_missing" in summary["missing_fixture_classes"]
    assert "backend_rejected" in summary["missing_fixture_classes"]
    assert "passed_backend_frontend_hidden" in summary["missing_fixture_classes"]
    assert report["product_gate_ready"] is False
    assert report["public_release_applied"] is False


def test_step10_exit_gate_rejects_raw_or_public_comment_payload() -> None:
    unsafe = _row("step10-unsafe")
    unsafe["commentText"] = "これはExit Gateでも出してはいけない観測本文です"

    with pytest.raises(ProductQualityMeasurementConnectionError):
        build_complete_product_quality_measurement_connection(rows=[unsafe], run_id="step10-unsafe")
