#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Compare 11:35/11:36 Emlis observation diagnostic logs.

Usage examples:
  python tools/emlis_observation_compare_1135_1136.py backend.log rn.log
  python tools/emlis_observation_compare_1135_1136.py --format json all.log
  python tools/emlis_observation_compare_1135_1136.py \
      --left-trace-id emlisobs-... --right-trace-id emlisobs-... all.log

The script consumes only the one-line diagnostic JSON records. It does not need
raw input text or public comment_text.
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

from emlis_ai_observation_diagnostic_compare import (  # noqa: E402
    build_comparison_from_log_lines,
    dump_observation_diagnostic_comparison,
    format_observation_diagnostic_comparison_markdown,
)


def _read_lines(paths: list[str]) -> list[str]:
    if not paths:
        return sys.stdin.read().splitlines()
    lines: list[str] = []
    for path in paths:
        lines.extend(Path(path).read_text(encoding="utf-8", errors="replace").splitlines())
    return lines


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Compare Emlis observation diagnostic rows for the 11:35/11:36 workflow.")
    parser.add_argument("logs", nargs="*", help="Log files. If omitted, stdin is used.")
    parser.add_argument("--format", choices=("markdown", "json"), default="markdown")
    parser.add_argument("--left-label", default="11:35")
    parser.add_argument("--right-label", default="11:36")
    parser.add_argument("--left-trace-id", default="")
    parser.add_argument("--right-trace-id", default="")
    parser.add_argument("--left-emotion-log-id", default="")
    parser.add_argument("--right-emotion-log-id", default="")
    args = parser.parse_args(argv)

    report = build_comparison_from_log_lines(
        _read_lines(args.logs),
        left_label=args.left_label,
        right_label=args.right_label,
        left_trace_id=args.left_trace_id,
        right_trace_id=args.right_trace_id,
        left_emotion_log_id=args.left_emotion_log_id,
        right_emotion_log_id=args.right_emotion_log_id,
    )
    if args.format == "json":
        print(json.dumps(json.loads(dump_observation_diagnostic_comparison(report)), ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print(format_observation_diagnostic_comparison_markdown(report))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
