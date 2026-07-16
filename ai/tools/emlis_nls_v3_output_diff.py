#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

"""Create a body-free changed/unchanged diff from two batch receipts."""

import argparse
from pathlib import Path
import sys

AI_ROOT = Path(__file__).resolve().parents[1]
SERVICES = AI_ROOT / "services" / "ai_inference"
HELPERS = AI_ROOT / "tests" / "helpers"
for entry in (SERVICES, HELPERS):
    if str(entry) not in sys.path:
        sys.path.insert(0, str(entry))

from emlis_ai_step10_evidence_v3 import build_output_diff  # noqa: E402
from emlis_nls_v3_batch_run import _write_json  # noqa: E402
from emlis_nls_v3_s2_sample_registry import load_canonical_json  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Diff NLS v3 body commitments.")
    parser.add_argument("--previous", type=Path, required=True)
    parser.add_argument("--current", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    result = build_output_diff(
        load_canonical_json(args.previous),
        load_canonical_json(args.current),
    )
    _write_json(args.output, result, private=False)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
