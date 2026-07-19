#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

"""Build or verify the independent rc0028 experiment dependency closure."""

import argparse
import json
import os
from pathlib import Path
import sys


AI_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = AI_ROOT.parent
SERVICES = AI_ROOT / "services" / "ai_inference"
if str(SERVICES) not in sys.path:
    sys.path.insert(0, str(SERVICES))

from emlis_ai_nls_v3_artifact_contract import canonical_json_bytes  # noqa: E402
from emlis_ai_rc0028_experiment_dependency_manifest_v3 import (  # noqa: E402
    build_rc0028_experiment_dependency_manifest,
    validate_rc0028_experiment_dependency_manifest,
)


def _load_json(path: Path) -> object:
    return json.loads(path.read_text(encoding="utf-8"))


def _write_body_free_json(path: Path, value: object) -> None:
    if path.exists():
        raise ValueError("rc0028_experiment_dependency_output_already_exists")
    path.parent.mkdir(parents=True, exist_ok=True)
    descriptor = os.open(
        path,
        os.O_WRONLY | os.O_CREAT | os.O_EXCL,
        0o644,
    )
    try:
        with os.fdopen(descriptor, "wb") as handle:
            handle.write(canonical_json_bytes(value) + b"\n")
    except BaseException:
        path.unlink(missing_ok=True)
        raise


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--before-manifest", type=Path, required=True)
    parser.add_argument("--repo-root", type=Path, default=REPO_ROOT)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--output", type=Path)
    mode.add_argument("--check", type=Path)
    args = parser.parse_args(argv)

    parent = _load_json(args.before_manifest)
    repo_root = args.repo_root.resolve()
    if args.output is not None:
        manifest = build_rc0028_experiment_dependency_manifest(
            parent,
            repo_root=repo_root,
        )
        _write_body_free_json(args.output, manifest)
        return 0

    current = _load_json(args.check)
    issues = validate_rc0028_experiment_dependency_manifest(
        current,
        parent_manifest=parent,
        repo_root=repo_root,
    )
    if issues:
        for issue in issues:
            print(issue, file=sys.stderr)
        return 1
    print(current["source_dependency_closure_sha256"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
