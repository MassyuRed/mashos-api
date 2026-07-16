#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

"""Verify private/body-free separation and recompute every case commitment."""

import argparse
from pathlib import Path
import sys

AI_ROOT = Path(__file__).resolve().parents[1]
SERVICES = AI_ROOT / "services" / "ai_inference"
HELPERS = AI_ROOT / "tests" / "helpers"
for entry in (SERVICES, HELPERS):
    if str(entry) not in sys.path:
        sys.path.insert(0, str(entry))

from emlis_ai_step10_evidence_v3 import verify_batch_evidence  # noqa: E402
from emlis_nls_v3_s2_sample_registry import load_canonical_json  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Verify a Step 10 evidence pair.")
    parser.add_argument("--private-packet", type=Path, required=True)
    parser.add_argument("--body-free-summary", type=Path, required=True)
    args = parser.parse_args(argv)
    issues = verify_batch_evidence(
        load_canonical_json(args.private_packet),
        load_canonical_json(args.body_free_summary),
    )
    for issue in issues:
        print(issue)
    return 0 if not issues else 2


if __name__ == "__main__":
    raise SystemExit(main())
