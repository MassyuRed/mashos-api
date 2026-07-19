#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

"""Build or verify the phase-qualified rc0030 P4 delta closure."""

import argparse
import hashlib
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
from emlis_ai_rc0030_surface_planning_experiment_dependency_manifest_v3 import (  # noqa: E402
    RC0029_SURFACE_REPAIR_PARENT_MANIFEST_FILE_SHA256,
    Rc0030SurfacePlanningDependencyError,
    build_rc0030_surface_planning_dependency_manifest,
    validate_rc0030_surface_planning_dependency_manifest,
)


def _load_json(path: Path) -> object:
    return json.loads(path.read_text(encoding="utf-8"))


def _load_exact_parent(path: Path) -> object:
    if hashlib.sha256(path.read_bytes()).hexdigest() != (
        RC0029_SURFACE_REPAIR_PARENT_MANIFEST_FILE_SHA256
    ):
        raise Rc0030SurfacePlanningDependencyError(
            "RC0030_PARENT_MANIFEST_FILE_DRIFT"
        )
    return _load_json(path)


def _write_body_free_json(path: Path, value: object) -> None:
    if path.exists():
        raise Rc0030SurfacePlanningDependencyError(
            "RC0030_OUTPUT_ALREADY_EXISTS"
        )
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
    parser.add_argument("--parent-manifest", type=Path, required=True)
    parser.add_argument("--repo-root", type=Path, default=REPO_ROOT)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--output", type=Path)
    mode.add_argument("--check", type=Path)
    args = parser.parse_args(argv)

    try:
        parent = _load_exact_parent(args.parent_manifest)
        repo_root = args.repo_root.resolve()
        if args.output is not None:
            manifest = build_rc0030_surface_planning_dependency_manifest(
                parent,
                repo_root=repo_root,
            )
            _write_body_free_json(args.output, manifest)
            return 0

        current = _load_json(args.check)
        issues = validate_rc0030_surface_planning_dependency_manifest(
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
    except Rc0030SurfacePlanningDependencyError as error:
        print(error.code, file=sys.stderr)
        return 1
    except (OSError, TypeError, ValueError):
        print("RC0030_TOOL_INPUT_INVALID", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
