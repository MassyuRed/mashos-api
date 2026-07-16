#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

"""Recompute a body-free cumulative manifest from complete batch case rows."""

import argparse
import hashlib
from pathlib import Path
import sys
from typing import Any

AI_ROOT = Path(__file__).resolve().parents[1]
SERVICES = AI_ROOT / "services" / "ai_inference"
HELPERS = AI_ROOT / "tests" / "helpers"
for entry in (SERVICES, HELPERS):
    if str(entry) not in sys.path:
        sys.path.insert(0, str(entry))

from emlis_ai_nls_v3_artifact_contract import canonical_json_bytes  # noqa: E402
from emlis_ai_step10_evidence_v3 import build_cumulative_run_manifest  # noqa: E402
from emlis_nls_v3_batch_run import (  # noqa: E402
    _write_json,
    _resolve_repo_ref,
    load_validated_batch,
)
from emlis_nls_v3_s2_sample_registry import load_canonical_json  # noqa: E402


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Build the Step 10 cumulative receipt.")
    parser.add_argument("--summary", type=Path, action="append", required=True)
    parser.add_argument("--manifest", type=Path, action="append", required=True)
    parser.add_argument("--cumulative-run-id", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    summaries = [load_canonical_json(path) for path in args.summary]
    manifests = [load_canonical_json(path) for path in args.manifest]
    if len(summaries) != len(manifests):
        raise ValueError("cumulative_summary_manifest_count_mismatch")
    expected: dict[str, list[str]] = {}
    manifest_hashes: dict[str, str] = {}
    for manifest_path, manifest in zip(args.manifest, manifests):
        if type(manifest) is not dict:
            raise ValueError("batch_manifest_mapping_required")
        batch_id = str(manifest["batch_id"])
        if batch_id in expected:
            raise ValueError("cumulative_manifest_batch_duplicate")
        load_validated_batch(
            _resolve_repo_ref(manifest["corpus_file_ref"]),
            manifest_path.resolve(),
        )
        expected[batch_id] = list(manifest["case_ids"])
        manifest_hashes[batch_id] = hashlib.sha256(
            canonical_json_bytes(manifest) + b"\n"
        ).hexdigest()
    result = build_cumulative_run_manifest(
        summaries,
        expected_case_ids_by_batch=expected,
        expected_batch_manifest_sha256_by_batch=manifest_hashes,
        cumulative_run_id=args.cumulative_run_id,
    )
    _write_json(args.output, result, private=False)
    return 0 if result["formal_status"] == "step10_ready_for_step11" else 2


if __name__ == "__main__":
    raise SystemExit(main())
