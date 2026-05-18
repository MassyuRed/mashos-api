from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

TOOLS = Path(__file__).resolve().parents[1] / "tools"
if str(TOOLS) not in sys.path:
    sys.path.insert(0, str(TOOLS))

from emlis_observation_product_quality_measurement import (  # noqa: E402
    build_complete_product_quality_measurement_report_from_log_lines,
    dump_complete_product_quality_measurement_report_pretty_json,
    format_complete_product_quality_measurement_report_markdown,
    main,
)


def _backend_record(
    *,
    trace_id: str = "emlisobs-tool-1",
    emotion_log_id: str = "emotion-tool-1",
    status: str = "passed",
    comment_len: int = 64,
    coverage_group: str = "short_daily",
) -> dict:
    gate_passed = status == "passed"
    return {
        "version": "emlis.observation_diagnostic_lockdown.v1",
        "source": "backend_emotion_submit",
        "trace_id": trace_id,
        "emotion_log_id": emotion_log_id,
        "created_at": "2026-05-18T12:00:00+09:00",
        "observation_status": status,
        "comment_text_length": comment_len,
        "comment_text_present": comment_len > 0,
        "stage": "display" if gate_passed else "grounding",
        "primary_reason": "passed" if gate_passed else "unsupported_sentence",
        "coverage_group": coverage_group,
        "composer_client_resolution": {"connection_status": "connected"},
        "candidate": {"generated": True, "status": "generated"},
        "gate_results": {
            "reader": {"passed": True, "primary_reason": "passed"},
            "grounding": {"passed": gate_passed, "primary_reason": "passed" if gate_passed else "unsupported_sentence"},
            "template_echo": {"passed": True, "primary_reason": "passed"},
            "display": {"passed": gate_passed, "primary_reason": "passed" if gate_passed else "rejected"},
        },
        "self_repair": {"status": "not_attempted", "attempted": False},
        "binding_supported_sentence_count": 1 if gate_passed else 0,
        "expected_binding_count": 1,
        "raw_input_included": False,
        "comment_text_included": False,
    }


def _frontend_record(
    *,
    trace_id: str = "emlisobs-tool-1",
    emotion_log_id: str = "emotion-tool-1",
    status: str = "passed",
    comment_len: int = 64,
    modal_opened: bool = True,
) -> dict:
    return {
        "version": "emlis.observation_frontend_result.v1",
        "source": "rn_input_feedback_modal",
        "trace_id": trace_id,
        "emotion_log_id": emotion_log_id,
        "observation_status": status,
        "comment_text_length": comment_len,
        "comment_text_present": comment_len > 0,
        "modal_opened": modal_opened,
        "raw_input_included": False,
        "comment_text_included": False,
    }


def _backend_line(record: dict) -> str:
    return "emlis_observation_diagnostic_lockdown " + json.dumps(record, ensure_ascii=False, sort_keys=True)


def _frontend_line(record: dict) -> str:
    return "emlis_observation_frontend_result " + json.dumps(record, ensure_ascii=False, sort_keys=True)


def _has_forbidden_payload_key(value: object) -> bool:
    forbidden = {
        "raw_input",
        "rawInput",
        "input",
        "input_text",
        "inputText",
        "memo",
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
        return any(str(key) in forbidden or _has_forbidden_payload_key(nested) for key, nested in value.items())
    if isinstance(value, list):
        return any(_has_forbidden_payload_key(item) for item in value)
    return False


def test_step8_local_tool_builds_json_report_from_backend_and_frontend_diagnostics() -> None:
    lines = [
        "ordinary server line is ignored",
        _backend_line(_backend_record()),
        _frontend_line(_frontend_record()),
    ]

    report = build_complete_product_quality_measurement_report_from_log_lines(lines, run_id="local-tool-run")

    assert report["source_step"] == "Step8_local_tool_output"
    assert report["local_tool_output_ready"] is True
    assert report["diagnostic_backend_line_count"] == 1
    assert report["diagnostic_frontend_line_count"] == 1
    assert report["non_diagnostic_lines_ignored"] == 1
    assert report["display_confirmed_count"] == 1
    assert report["scorecard_passed_display_count"] == 1
    assert report["passed_display_count"] == 1
    assert report["display_reach_rate"] == 1.0
    assert report["scorecard"]["binding_pass_rate"] == 1.0
    assert report["public_release_applied"] is False
    assert report["raw_input_included"] is False
    assert report["comment_text_included"] is False
    assert not _has_forbidden_payload_key(report)

    dumped = dump_complete_product_quality_measurement_report_pretty_json(report)
    parsed = json.loads(dumped)
    assert parsed["local_tool_output_ready"] is True
    assert parsed["scorecard"]["passed_display_count"] == 1
    assert "これは出してはいけない本文" not in dumped


def test_step8_markdown_output_contains_scorecard_metrics_and_next_action_branch() -> None:
    report = build_complete_product_quality_measurement_report_from_log_lines(
        [_backend_line(_backend_record()), _frontend_line(_frontend_record())],
        run_id="markdown-run",
    )

    markdown = format_complete_product_quality_measurement_report_markdown(report)

    assert "# EmlisAI Product Gate Measurement" in markdown
    assert "## Scorecard metrics" in markdown
    assert "display_reach_rate" in markdown
    assert "## Next action branch" in markdown
    assert "classification:" in markdown
    assert "## Coverage groups" in markdown
    assert "raw_input_included: false" in markdown
    assert "comment_text_included: false" in markdown
    assert "これは出してはいけない本文" not in markdown


def test_step8_backend_pass_without_frontend_is_not_display_counted() -> None:
    report = build_complete_product_quality_measurement_report_from_log_lines(
        [_backend_line(_backend_record(trace_id="backend-only", emotion_log_id="emotion-backend-only"))],
        run_id="backend-only-run",
    )

    assert report["diagnostic_backend_line_count"] == 1
    assert report["diagnostic_frontend_line_count"] == 0
    assert report["display_confirmed_count"] == 0
    assert report["scorecard_passed_display_count"] == 0
    assert report["passed_display_count"] == 0
    assert "frontend_diagnostic_missing_or_not_captured" in report["release_blockers"]
    assert report["next_action_branch"]["classification"] == "unknown_diagnostic_missing"
    assert report["next_action_branch"]["repair_allowed"] is False


def test_step8_local_tool_rejects_forbidden_payload_key_before_output() -> None:
    unsafe = _backend_record()
    unsafe["commentText"] = "これは出してはいけない本文です"

    with pytest.raises(ValueError):
        build_complete_product_quality_measurement_report_from_log_lines([_backend_line(unsafe)])


def test_step8_cli_json_smoke_outputs_report(tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
    log_file = tmp_path / "emlis.log"
    log_file.write_text(
        "\n".join([_backend_line(_backend_record()), _frontend_line(_frontend_record())]),
        encoding="utf-8",
    )

    assert main(["--format", "json", "--run-id", "cli-run", str(log_file)]) == 0
    stdout = capsys.readouterr().out
    parsed = json.loads(stdout)

    assert parsed["run_id"] == "cli-run"
    assert parsed["local_tool_output_ready"] is True
    assert parsed["source_step"] == "Step8_local_tool_output"
    assert parsed["scorecard"]["display_reach_rate"] == 1.0
    assert parsed["product_gate_public_release_applied"] is False
    assert not _has_forbidden_payload_key(parsed)
