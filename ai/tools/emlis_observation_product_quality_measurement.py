#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Build a local EmlisAI ProductGate measurement report from diagnostic logs.

Usage examples:
  python ai/tools/emlis_observation_product_quality_measurement.py backend.log rn.log
  python ai/tools/emlis_observation_product_quality_measurement.py --format json all.log
  cat all.log | python ai/tools/emlis_observation_product_quality_measurement.py --run-id local-001

The tool consumes only the one-line backend/RN diagnostic JSON records:
``emlis_observation_diagnostic_lockdown {...}`` and
``emlis_observation_frontend_result {...}``. It never needs raw input text or
public ``comment_text`` bodies, and the imported parsers reject those payload
keys before the ProductQualityScorecard report is built.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Iterable, Mapping, Sequence
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
SERVICES = ROOT / "services" / "ai_inference"
if str(SERVICES) not in sys.path:
    sys.path.insert(0, str(SERVICES))

from emlis_ai_complete_product_quality_measurement_connection import (  # noqa: E402
    assert_product_quality_measurement_connection_meta_only,
    build_complete_product_quality_measurement_connection,
    dump_complete_product_quality_measurement_connection,
)
from emlis_ai_observation_diagnostic_compare import (  # noqa: E402
    join_backend_frontend_diagnostics,
    parse_observation_diagnostic_logs,
)


def _safe_mapping(value: Any) -> dict[str, Any]:
    return dict(value) if isinstance(value, Mapping) else {}



_SAFE_BACKEND_ROW_FORWARD_KEYS = (
    "binding_supported_sentence_count",
    "expected_binding_count",
    "binding_pass_count",
    "supported_sentence_count",
    "repair_attempted",
    "repair_success",
    "repair_applied",
    "self_repair_attempted",
    "self_repair_success",
    "template_major_count",
    "safety_major_count",
)


def _join_key(record: Mapping[str, Any]) -> tuple[str, str]:
    return str(record.get("trace_id") or "").strip(), str(record.get("emotion_log_id") or "").strip()


def _augment_rows_with_backend_measurement_fields(
    rows: Sequence[Mapping[str, Any]],
    backend_records: Sequence[Mapping[str, Any]],
) -> list[dict[str, Any]]:
    """Carry scorecard-safe numeric meta from backend diagnostics into rows."""

    by_trace: dict[str, Mapping[str, Any]] = {}
    by_emotion: dict[str, Mapping[str, Any]] = {}
    for record in backend_records:
        trace_id, emotion_log_id = _join_key(record)
        if trace_id and trace_id not in by_trace:
            by_trace[trace_id] = record
        if emotion_log_id and emotion_log_id not in by_emotion:
            by_emotion[emotion_log_id] = record

    augmented: list[dict[str, Any]] = []
    for source_row in rows:
        row = dict(source_row)
        trace_id, emotion_log_id = _join_key(row)
        backend = by_trace.get(trace_id) if trace_id else None
        if backend is None and emotion_log_id:
            backend = by_emotion.get(emotion_log_id)
        if backend is not None:
            for key in _SAFE_BACKEND_ROW_FORWARD_KEYS:
                if key in backend and key not in row:
                    row[key] = backend[key]
        augmented.append(row)
    return augmented

def _read_lines(paths: Sequence[str]) -> list[str]:
    """Read log lines from files, or stdin when no file path is given."""

    if not paths:
        return sys.stdin.read().splitlines()
    lines: list[str] = []
    for path in paths:
        lines.extend(Path(path).read_text(encoding="utf-8", errors="replace").splitlines())
    return lines


def build_complete_product_quality_measurement_report_from_log_lines(
    lines: Iterable[str],
    *,
    run_id: str = "",
) -> dict[str, Any]:
    """Parse diagnostic lines and build the Step8 local measurement report.

    Non-diagnostic lines are ignored. Diagnostic lines containing raw input or
    public comment payload keys are rejected by the Step1 parser before rows are
    joined. Display counting keeps the Step2 contract: backend pass alone does
    not become ``passed_display_count`` unless RN display is confirmed.
    """

    source_lines = list(lines or [])
    parsed = parse_observation_diagnostic_logs(source_lines)
    joined_rows = join_backend_frontend_diagnostics(parsed["backend"], parsed["frontend"])
    rows = _augment_rows_with_backend_measurement_fields(joined_rows, parsed["backend"])
    report = build_complete_product_quality_measurement_connection(rows=rows, run_id=run_id)
    report["source"] = "emlis_product_gate_measurement_step8_local_tool_output"
    report["source_step"] = "Step8_local_tool_output"
    report["step"] = "Step8_local_tool_output"
    report["local_tool_output_ready"] = True
    report["diagnostic_backend_line_count"] = len(parsed["backend"])
    report["diagnostic_frontend_line_count"] = len(parsed["frontend"])
    report["non_diagnostic_lines_ignored"] = max(
        0,
        len(source_lines) - len(parsed["backend"]) - len(parsed["frontend"]),
    )
    report["raw_input_included"] = False
    report["raw_text_included"] = False
    report["comment_text_included"] = False
    assert_product_quality_measurement_connection_meta_only(report, source="step8_local_tool_report")
    return report


def _metric(scorecard: Mapping[str, Any], name: str, default: Any = "") -> Any:
    if name in scorecard:
        return scorecard.get(name, default)
    machine = _safe_mapping(scorecard.get("machine_metrics"))
    return machine.get(name, default)


def _cell(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, float):
        return f"{value:.4f}".rstrip("0").rstrip(".")
    if isinstance(value, (list, tuple, set)):
        return ", ".join(_cell(item) for item in value)
    if isinstance(value, Mapping):
        return json.dumps(value, ensure_ascii=False, sort_keys=True)
    return str(value).replace("|", "\\|").replace("\n", " ")


def format_complete_product_quality_measurement_report_markdown(report: Mapping[str, Any]) -> str:
    """Render a compact meta-only Markdown report for local Step8 runs."""

    data = dict(report or {})
    data["raw_input_included"] = False
    data["raw_text_included"] = False
    data["comment_text_included"] = False
    assert_product_quality_measurement_connection_meta_only(data, source="step8_markdown_report")

    capture = _safe_mapping(data.get("capture_summary"))
    scorecard = _safe_mapping(data.get("scorecard") or data.get("product_quality_scorecard"))
    next_branch = _safe_mapping(data.get("next_action_branch") or data.get("next_branch"))
    exit_gate = _safe_mapping(data.get("exit_gate_summary") or data.get("measurement_exit_gate_summary"))
    coverage = _safe_mapping(data.get("coverage_group_summary"))
    by_group = _safe_mapping(data.get("by_coverage_group") or coverage.get("by_coverage_group"))
    release_blockers = data.get("release_blockers") or []

    lines = [
        "# EmlisAI Product Gate Measurement",
        "",
        f"run_id: {_cell(data.get('run_id'))}",
        f"source_step: {_cell(data.get('source_step'))}",
        f"local_tool_output_ready: {_cell(data.get('local_tool_output_ready'))}",
        f"diagnostic_capture_status: {_cell(capture.get('diagnostic_capture_status'))}",
        f"backend_diagnostic_lines: {_cell(data.get('diagnostic_backend_line_count'))}",
        f"frontend_diagnostic_lines: {_cell(data.get('diagnostic_frontend_line_count'))}",
        f"display_confirmed_count: {_cell(data.get('display_confirmed_count'))}",
        f"scorecard_passed_display_count: {_cell(data.get('scorecard_passed_display_count'))}",
        "",
        "## Scorecard metrics",
        "",
        "| metric | value |",
        "| --- | --- |",
    ]
    for metric_name in (
        "eligible_count",
        "passed_display_count",
        "display_reach_rate",
        "binding_pass_rate",
        "repair_success_rate",
        "reason_coverage_rate",
        "template_major_count",
        "safety_major_count",
        "read_feeling_score",
        "blind_qa_missing",
    ):
        lines.append(f"| {metric_name} | {_cell(_metric(scorecard, metric_name))} |")

    lines.extend(
        [
            "",
            "## Next action branch",
            "",
            f"classification: {_cell(next_branch.get('classification'))}",
            f"target_layer: {_cell(next_branch.get('target_layer'))}",
            f"next_work_unit: {_cell(next_branch.get('next_work_unit') or data.get('next_step'))}",
            f"repair_allowed: {_cell(next_branch.get('repair_allowed'))}",
            f"routing_basis: {_cell(next_branch.get('routing_basis') or data.get('next_action_routing_basis'))}",
            f"touch_files: {_cell(next_branch.get('touch_files'))}",
            f"do_not_touch: {_cell(next_branch.get('do_not_touch'))}",
            "",
            "## Exit Gate",
            "",
            f"measurement_exit_gate_ready: {_cell(data.get('measurement_exit_gate_ready') if 'measurement_exit_gate_ready' in data else exit_gate.get('measurement_exit_gate_ready'))}",
            f"measurement_connection_complete: {_cell(data.get('measurement_connection_complete') if 'measurement_connection_complete' in data else exit_gate.get('measurement_connection_complete'))}",
            f"scorecard_event_connection_ready: {_cell(data.get('scorecard_event_connection_ready') if 'scorecard_event_connection_ready' in data else exit_gate.get('scorecard_event_connection_ready'))}",
            f"product_gate_ready: {_cell(data.get('product_gate_ready'))}",
            f"product_gate_achieved: {_cell(exit_gate.get('product_gate_achieved') if 'product_gate_achieved' in exit_gate else data.get('product_gate_achieved'))}",
            f"product_gate_public_release_applied: {_cell(data.get('product_gate_public_release_applied'))}",
            f"exit_gate_decision: {_cell(data.get('exit_gate_decision') or exit_gate.get('exit_gate_decision'))}",
            f"exit_gate_blockers: {_cell(data.get('exit_gate_blockers') or exit_gate.get('exit_gate_blockers'))}",
            "",
            "## Release blockers",
            "",
        ]
    )
    if release_blockers:
        lines.extend(f"- {_cell(blocker)}" for blocker in release_blockers)
    else:
        lines.append("- none")

    lines.extend(
        [
            "",
            "## Coverage groups",
            "",
            "| group | eligible_count | passed_display_count | display_reach_rate | top_rejection_reasons |",
            "| --- | ---: | ---: | ---: | --- |",
        ]
    )
    if by_group:
        for group, row in by_group.items():
            item = _safe_mapping(row)
            lines.append(
                "| "
                + " | ".join(
                    [
                        _cell(group),
                        _cell(item.get("eligible_count")),
                        _cell(item.get("passed_display_count")),
                        _cell(item.get("display_reach_rate")),
                        _cell(item.get("top_rejection_reasons") or item.get("reason_counter")),
                    ]
                )
                + " |"
            )
    else:
        lines.append("| none | 0 | 0 | 0 |  |")

    lines.extend(
        [
            "",
            "## Meta-only contract",
            "",
            f"raw_input_included: {_cell(data.get('raw_input_included'))}",
            f"comment_text_included: {_cell(data.get('comment_text_included'))}",
            f"public_release_applied: {_cell(data.get('public_release_applied'))}",
        ]
    )
    return "\n".join(lines)


def dump_complete_product_quality_measurement_report_pretty_json(report: Mapping[str, Any]) -> str:
    """Return pretty JSON while preserving the existing meta-only dump guard."""

    compact = dump_complete_product_quality_measurement_connection(report)
    return json.dumps(json.loads(compact), ensure_ascii=False, indent=2, sort_keys=True)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Build a local EmlisAI ProductGate measurement report from backend/RN diagnostic log lines."
    )
    parser.add_argument("logs", nargs="*", help="Log files. If omitted, stdin is used.")
    parser.add_argument("--format", choices=("markdown", "json"), default="markdown")
    parser.add_argument("--run-id", default="", help="Optional local run id included in the report.")
    args = parser.parse_args(argv)

    lines = _read_lines(args.logs)
    report = build_complete_product_quality_measurement_report_from_log_lines(lines, run_id=args.run_id)
    if args.format == "json":
        print(dump_complete_product_quality_measurement_report_pretty_json(report))
    else:
        print(format_complete_product_quality_measurement_report_markdown(report))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
