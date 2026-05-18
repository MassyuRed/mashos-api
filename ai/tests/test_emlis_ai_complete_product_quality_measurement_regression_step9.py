from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

import pytest

TOOLS = Path(__file__).resolve().parents[1] / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

from emlis_ai_complete_product_quality_measurement_connection import (  # noqa: E402
    ProductQualityMeasurementConnectionError,
    build_complete_product_quality_measurement_connection,
    dump_complete_product_quality_measurement_connection,
)
from emlis_ai_complete_product_quality_measurement_contract_inventory import (  # noqa: E402
    build_product_gate_measurement_contract_inventory,
)
from emlis_observation_product_quality_measurement import (  # noqa: E402
    build_complete_product_quality_measurement_report_from_log_lines,
    format_complete_product_quality_measurement_report_markdown,
)


def _joined_row(
    *,
    trace_id: str,
    classification: str = "passed_displayed",
    measurement_classification: str | None = None,
    backend_status: str = "passed",
    backend_len: int = 120,
    frontend_joined: bool = True,
    modal_opened: bool | None = True,
    display_confirmed: bool = True,
    primary_reason: str = "passed",
    coverage_group: str = "short_daily",
    display_blockers: list[str] | None = None,
) -> dict[str, Any]:
    backend_public_passed = backend_status == "passed" and backend_len > 0
    return {
        "trace_id": trace_id,
        "emotion_log_id": f"emotion-{trace_id}",
        "coverage_group": coverage_group,
        "backend_status": backend_status,
        "backend_len": backend_len,
        "backend_comment_text_present": backend_len > 0,
        "backend_public_passed": backend_public_passed,
        "rn_status": "passed" if frontend_joined and backend_public_passed else backend_status,
        "rn_len": backend_len if frontend_joined and backend_public_passed else None,
        "frontend_joined": frontend_joined,
        "frontend_join_status": "joined" if frontend_joined else "missing",
        "modal_opened": modal_opened,
        "display_confirmed": display_confirmed,
        "product_gate_display_counted": display_confirmed,
        "scorecard_passed_display_count": 1 if display_confirmed else 0,
        "diagnostic_capture_status": "captured" if frontend_joined else "frontend_diagnostic_missing_or_not_captured",
        "backend_diagnostic_capture_status": "captured",
        "frontend_diagnostic_capture_status": "captured" if frontend_joined else "frontend_diagnostic_missing_or_not_captured",
        "classification": classification,
        "measurement_classification": measurement_classification or classification,
        "primary_reason": primary_reason,
        "stage": "display" if backend_public_passed else "grounding",
        "candidate_generated": True,
        "reader": "pass",
        "grounding": "fail" if classification == "candidate_generated_but_grounding_rejected" else "pass",
        "template": "pass",
        "display": "pass" if backend_public_passed else "fail",
        "reader_reason": "passed",
        "grounding_reason": primary_reason,
        "template_reason": "passed",
        "display_reason": primary_reason,
        "display_count_blockers": list(display_blockers or []),
        "binding_supported_sentence_count": 1 if display_confirmed else 0,
        "expected_binding_count": 1 if backend_public_passed or backend_status == "rejected" else 0,
        "raw_input_included": False,
        "comment_text_included": False,
    }


def _backend_line(record: dict[str, Any]) -> str:
    return "emlis_observation_diagnostic_lockdown " + json.dumps(record, ensure_ascii=False, sort_keys=True)


def _frontend_line(record: dict[str, Any]) -> str:
    return "emlis_observation_frontend_result " + json.dumps(record, ensure_ascii=False, sort_keys=True)


def _backend_record(
    *,
    trace_id: str = "step9-log",
    emotion_log_id: str = "emotion-step9-log",
    status: str = "passed",
    comment_len: int = 120,
    classification: str = "passed_displayed",
    primary_reason: str = "passed",
    coverage_group: str = "short_daily",
) -> dict[str, Any]:
    return {
        "version": "emlis.observation_diagnostic_lockdown.v1",
        "source": "backend",
        "trace_id": trace_id,
        "emotion_log_id": emotion_log_id,
        "coverage_group": coverage_group,
        "observation_status": status,
        "comment_text_length": comment_len,
        "comment_text_present": comment_len > 0,
        "classification": classification,
        "stage": "display" if status == "passed" else "grounding",
        "primary_reason": primary_reason,
        "candidate_generated": True,
        "reader": "passed",
        "grounding": "passed" if status == "passed" else "failed",
        "template_echo": "passed",
        "display": "passed" if status == "passed" else "failed",
        "binding_supported_sentence_count": 1 if status == "passed" else 0,
        "expected_binding_count": 1,
        "raw_input_included": False,
        "comment_text_included": False,
    }


def _frontend_record(
    *,
    trace_id: str = "step9-log",
    emotion_log_id: str = "emotion-step9-log",
    status: str = "passed",
    comment_len: int = 120,
    modal_opened: bool = True,
) -> dict[str, Any]:
    return {
        "version": "emlis.observation_frontend_result.v1",
        "source": "frontend",
        "trace_id": trace_id,
        "emotion_log_id": emotion_log_id,
        "observation_status": status,
        "comment_text_length": comment_len,
        "comment_text_present": comment_len > 0,
        "modal_opened": modal_opened,
        "raw_input_included": False,
        "comment_text_included": False,
    }


def _contains_forbidden_payload_key(value: Any) -> bool:
    forbidden = {
        "raw_input",
        "rawInput",
        "raw_text",
        "rawText",
        "input_text",
        "inputText",
        "memo_text",
        "memoText",
        "current_input",
        "currentInput",
        "comment_text",
        "commentText",
        "input_feedback_comment",
        "inputFeedbackComment",
        "public_comment_text",
        "candidate_comment_text",
        "reply_text",
        "replyText",
        "text",
    }
    if isinstance(value, dict):
        return any(str(key) in forbidden or _contains_forbidden_payload_key(nested) for key, nested in value.items())
    if isinstance(value, list):
        return any(_contains_forbidden_payload_key(item) for item in value)
    return False


@pytest.mark.parametrize(
    ("row", "expected"),
    [
        (
            _joined_row(trace_id="step9-display-confirmed"),
            {
                "passed_display_count": 1,
                "display_confirmed_count": 1,
                "next_action_classification": "passed_displayed",
                "next_action_layer": "scorecard",
            },
        ),
        (
            _joined_row(
                trace_id="step9-backend-only",
                frontend_joined=False,
                modal_opened=None,
                display_confirmed=False,
                measurement_classification="backend_public_passed_frontend_unconfirmed",
                display_blockers=["frontend_diagnostic_missing_or_not_captured"],
            ),
            {
                "passed_display_count": 0,
                "display_confirmed_count": 0,
                "next_action_classification": "unknown_diagnostic_missing",
                "next_action_layer": "diagnostic",
            },
        ),
        (
            _joined_row(
                trace_id="step9-hidden",
                classification="passed_backend_frontend_hidden",
                modal_opened=False,
                display_confirmed=False,
                primary_reason="frontend_modal_not_opened",
                display_blockers=["frontend_modal_not_opened"],
            ),
            {
                "passed_display_count": 0,
                "display_confirmed_count": 0,
                "next_action_classification": "passed_backend_frontend_hidden",
                "next_action_layer": "frontend",
            },
        ),
        (
            _joined_row(
                trace_id="step9-grounding",
                classification="candidate_generated_but_grounding_rejected",
                backend_status="rejected",
                backend_len=0,
                modal_opened=False,
                display_confirmed=False,
                primary_reason="unsupported_sentence",
                display_blockers=["unsupported_sentence"],
            ),
            {
                "passed_display_count": 0,
                "display_confirmed_count": 0,
                "next_action_classification": "candidate_generated_but_grounding_rejected",
                "next_action_layer": "grounding",
            },
        ),
    ],
)
def test_step9_regression_core_classifications_keep_display_counting_and_routing_semantics(
    row: dict[str, Any],
    expected: dict[str, Any],
) -> None:
    report = build_complete_product_quality_measurement_connection(rows=[row], run_id="step9-regression")

    assert report["measurement_report_ready"] is True
    assert report["passed_display_count"] == expected["passed_display_count"]
    assert report["scorecard_passed_display_count"] == expected["passed_display_count"]
    assert report["display_confirmed_count"] == expected["display_confirmed_count"]
    assert report["next_action_classification"] == expected["next_action_classification"]
    assert report["next_action_layer"] == expected["next_action_layer"]
    assert report["public_release_applied"] is False
    assert report["product_gate_public_release_applied"] is False
    assert report["raw_input_included"] is False
    assert report["comment_text_included"] is False
    assert not _contains_forbidden_payload_key(report)


def test_step9_regression_local_tool_output_stays_meta_only_and_release_closed() -> None:
    lines = [
        "ordinary server line ignored by Step8/Step9 regression",
        _backend_line(_backend_record()),
        _frontend_line(_frontend_record()),
    ]

    report = build_complete_product_quality_measurement_report_from_log_lines(lines, run_id="step9-log-run")
    dumped = json.loads(dump_complete_product_quality_measurement_connection(report))
    markdown = format_complete_product_quality_measurement_report_markdown(report)

    assert report["local_tool_output_ready"] is True
    assert report["diagnostic_backend_line_count"] == 1
    assert report["diagnostic_frontend_line_count"] == 1
    assert report["non_diagnostic_lines_ignored"] == 1
    assert dumped["passed_display_count"] == 1
    assert dumped["display_confirmed_count"] == 1
    assert dumped["public_release_applied"] is False
    assert dumped["product_gate_public_release_applied"] is False
    assert dumped["scorecard"]["read_feeling_score"] is None
    assert dumped["scorecard"]["machine_metrics_used_for_read_feeling"] is False
    assert "## Scorecard metrics" in markdown
    assert "## Next action branch" in markdown
    assert "raw_input_included: false" in markdown
    assert "comment_text_included: false" in markdown
    assert not _contains_forbidden_payload_key(dumped)


def test_step9_regression_rejects_raw_or_public_comment_payload_before_report_output() -> None:
    unsafe_row = _joined_row(trace_id="step9-unsafe")
    unsafe_row["commentText"] = "これは回帰テストでも出してはいけない観測本文です"

    with pytest.raises(ProductQualityMeasurementConnectionError):
        build_complete_product_quality_measurement_connection(rows=[unsafe_row], run_id="step9-unsafe")

    unsafe_backend = _backend_record()
    unsafe_backend["rawInput"] = "これは回帰テストでも出してはいけない入力本文です"
    with pytest.raises(ValueError):
        build_complete_product_quality_measurement_report_from_log_lines([_backend_line(unsafe_backend)])


def test_step9_regression_inventory_keeps_public_contract_and_non_target_locks() -> None:
    inventory = build_product_gate_measurement_contract_inventory()
    lock_ids = {item["contract_id"] for item in inventory["contract_locks"]}
    allowed = set(inventory["allowed_touch_files"])

    assert inventory["scope"] == "Complete Composer ProductGate Measurement Step0-10"
    assert "Step9: regression tests" in inventory["steps_in_scope"]
    assert "Step10: Exit Gate" in inventory["steps_in_scope"]
    assert inventory["step9_regression_tests_required"] is True
    assert inventory["step10_exit_gate_required"] is True
    assert inventory["step10_exit_gate_is_product_gate_achievement"] is False
    assert inventory["step10_exit_gate_public_release_applied"] is False
    assert inventory["step9_regression_tests_are_public_release"] is False
    assert inventory["regression_tests_ready"] is True
    assert inventory["regression_public_contract_checks_required"] is True
    assert inventory["regression_meta_only_checks_required"] is True
    assert inventory["regression_display_counting_checks_required"] is True
    assert inventory["regression_rn_contract_checks_required"] is True
    assert inventory["rn_runtime_files_modified_by_measurement"] is False
    assert inventory["product_gate_achieved"] is False
    assert inventory["public_release_applied"] is False
    assert inventory["rn_visible_contract_change_allowed"] is False
    assert inventory["api_response_key_change_allowed"] is False
    assert inventory["db_physical_rename_allowed"] is False
    assert inventory["gate_relaxation_allowed"] is False
    assert "step9_regression_public_contract_boundary" in lock_ids
    assert "step10_exit_gate_measurement_only_boundary" in lock_ids
    assert "step10_exit_gate_fact_based_next_action_boundary" in lock_ids
    assert "rn_passed_only_modal_contract" in lock_ids
    assert "meta_only_diagnostic_boundary" in lock_ids
    assert "ai/tests/test_emlis_ai_complete_product_quality_measurement_regression_step9.py" in allowed
    assert "ai/tests/test_emlis_ai_complete_product_quality_measurement_exit_gate_step10.py" in allowed
    assert not any(path.startswith("screens/") or path.startswith("Cocolon/screens/") for path in allowed)


def test_step9_regression_backend_public_route_and_response_keys_remain_stable() -> None:
    ai_root = Path(__file__).resolve().parents[1]
    api_submit = (ai_root / "services" / "ai_inference" / "api_emotion_submit.py").read_text(encoding="utf-8")
    submit_service = (ai_root / "services" / "ai_inference" / "emotion_submit_service.py").read_text(encoding="utf-8")

    assert '@app.post("/emotion/submit", response_model=EmotionSubmitResponse)' in api_submit
    assert "comment_text" in api_submit
    assert "emlis_ai" in api_submit
    assert "observation_status" in submit_service
    assert "input_feedback" in api_submit
    assert "Gate relaxed" not in submit_service
