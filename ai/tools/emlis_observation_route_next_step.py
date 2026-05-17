#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Route a Step 7 Emlis observation comparison into the Step 8 next branch.

Examples:
  python tools/emlis_observation_route_next_step.py --comparison-json comparison.json
  python tools/emlis_observation_route_next_step.py --format json backend.log rn.log
  python tools/emlis_observation_route_next_step.py --left-trace-id emlisobs-... --right-trace-id emlisobs-... all.log

The tool consumes only diagnostic JSON. It does not need raw input text or
public comment_text.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SERVICES = ROOT / "services" / "ai_inference"
if str(SERVICES) not in sys.path:
    sys.path.insert(0, str(SERVICES))

from emlis_ai_observation_diagnostic_branching import (  # noqa: E402
    build_observation_diagnostic_branch_plan,
    dump_observation_diagnostic_branch_plan,
    format_observation_diagnostic_branch_markdown,
)
from emlis_ai_observation_diagnostic_compare import build_comparison_from_log_lines  # noqa: E402


def _read_lines(paths: list[str]) -> list[str]:
    if not paths:
        return sys.stdin.read().splitlines()
    lines: list[str] = []
    for path in paths:
        lines.extend(Path(path).read_text(encoding="utf-8", errors="replace").splitlines())
    return lines


def _read_comparison_json(path: str) -> dict:
    if path == "-":
        payload = sys.stdin.read()
    else:
        payload = Path(path).read_text(encoding="utf-8", errors="replace")
    parsed = json.loads(payload)
    if not isinstance(parsed, dict):
        raise ValueError("comparison JSON must be an object")
    return parsed


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Route Emlis observation diagnostics to the Step 8 next branch.")
    parser.add_argument("logs", nargs="*", help="Diagnostic log files. If omitted and --comparison-json is not set, stdin is used.")
    parser.add_argument("--comparison-json", default="", help="Step 7 comparison JSON file. Use '-' for stdin.")
    parser.add_argument("--format", choices=("markdown", "json"), default="markdown")
    parser.add_argument("--left-label", default="11:35")
    parser.add_argument("--right-label", default="11:36")
    parser.add_argument("--left-trace-id", default="")
    parser.add_argument("--right-trace-id", default="")
    parser.add_argument("--left-emotion-log-id", default="")
    parser.add_argument("--right-emotion-log-id", default="")
    args = parser.parse_args(argv)

    if args.comparison_json:
        source = _read_comparison_json(args.comparison_json)
    else:
        source = build_comparison_from_log_lines(
            _read_lines(args.logs),
            left_label=args.left_label,
            right_label=args.right_label,
            left_trace_id=args.left_trace_id,
            right_trace_id=args.right_trace_id,
            left_emotion_log_id=args.left_emotion_log_id,
            right_emotion_log_id=args.right_emotion_log_id,
        )
    plan = build_observation_diagnostic_branch_plan(source)
    if args.format == "json":
        print(json.dumps(json.loads(dump_observation_diagnostic_branch_plan(plan)), ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print(format_observation_diagnostic_branch_markdown(plan))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
