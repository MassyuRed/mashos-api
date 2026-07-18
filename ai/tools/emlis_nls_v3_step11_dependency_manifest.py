#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

"""Build the exact rc0024-to-rc0025 Cycle 001 source closure."""

import argparse
import hashlib
import json
from pathlib import Path
import sys
from typing import Any, Mapping


AI_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = AI_ROOT.parent
SERVICES = AI_ROOT / "services" / "ai_inference"
TOOLS = AI_ROOT / "tools"
for entry in (SERVICES, TOOLS):
    if str(entry) not in sys.path:
        sys.path.insert(0, str(entry))

from emlis_ai_nls_v3_artifact_contract import artifact_sha256  # noqa: E402
from emlis_ai_step11_cycle_evidence_v3 import (  # noqa: E402
    FROZEN_RC0020_PREFLIGHT_MANIFEST_ARTIFACT_SHA256,
    FROZEN_RC0020_PREFLIGHT_SOURCE_CLOSURE_SHA256,
    FROZEN_RC0021_PREFLIGHT_MANIFEST_ARTIFACT_SHA256,
    FROZEN_RC0021_PREFLIGHT_SOURCE_CLOSURE_SHA256,
    FROZEN_RC0022_FORMAL_MANIFEST_ARTIFACT_SHA256,
    FROZEN_RC0022_FORMAL_SOURCE_CLOSURE_SHA256,
    FROZEN_RC0023_FORMAL_MANIFEST_ARTIFACT_SHA256,
    FROZEN_RC0023_FORMAL_SOURCE_CLOSURE_SHA256,
    FROZEN_RC0024_FORMAL_MANIFEST_ARTIFACT_SHA256,
    FROZEN_RC0024_FORMAL_SOURCE_CLOSURE_SHA256,
    STEP11_CURRENT_CANDIDATE_VERSION_ID,
    STEP11_HISTORICAL_RC0019_CANDIDATE_VERSION_ID,
    STEP11_HISTORICAL_RC0020_CANDIDATE_VERSION_ID,
    STEP11_HISTORICAL_RC0021_CANDIDATE_VERSION_ID,
    STEP11_HISTORICAL_RC0022_CANDIDATE_VERSION_ID,
    STEP11_HISTORICAL_RC0023_CANDIDATE_VERSION_ID,
    STEP11_HISTORICAL_RC0024_CANDIDATE_VERSION_ID,
    STEP11_SUCCESSOR_CANDIDATE_VERSION_ID,
    build_step11_dependency_manifest,
    validate_step11_dependency_manifest,
)
from emlis_ai_step11_natural_surface_v3 import (  # noqa: E402
    STEP11_CANDIDATE_VERSION_ID,
)
from emlis_nls_v3_batch_run import _write_json  # noqa: E402


FROZEN_RC0020_PREFLIGHT_FILE_COUNT = 136
FROZEN_RC0021_PREFLIGHT_FILE_COUNT = 138
FROZEN_RC0022_FORMAL_FILE_COUNT = 141
FROZEN_RC0023_FORMAL_FILE_COUNT = 145
FROZEN_RC0024_FORMAL_FILE_COUNT = 148
FROZEN_RC0019_PREFLIGHT_MANIFEST_ARTIFACT_SHA256 = (
    "78c8d1fc3271857ce2790bf2e166c51656af51c5f0fd455793ccc524bf68a695"
)
FROZEN_RC0019_PREFLIGHT_SOURCE_CLOSURE_SHA256 = (
    "cb98e9f32891cf42c31ab1719b4eb61f3450f75e6e52ad8262386d2e22adfdd8"
)
FROZEN_RC0019_PREFLIGHT_FILE_COUNT = 133

# These files did not exist in the frozen rc0020 closure.  They are explicit
# rc0021 RED owners and are therefore included as additions, never discovered
# by a permissive filesystem walk.
RC0021_ADDED_SOURCE_PATHS = (
    "ai/tests/test_emlis_nls_v3_s11_rc0021_append_only_lineage.py",
    "ai/tests/test_emlis_nls_v3_s11_rc0021_compound_balanced_surface.py",
)
RC0022_ADDED_SOURCE_PATHS = (
    "ai/tests/test_emlis_nls_v3_s11_rc0022_append_only_lineage.py",
    "ai/tests/test_emlis_nls_v3_s11_rc0022_cycle_finalize.py",
    "ai/tests/test_emlis_nls_v3_s11_rc0022_grammatical_chunk_surface.py",
)
RC0023_ADDED_SOURCE_PATHS = (
    "ai/tests/test_emlis_nls_v3_s11_rc0023_append_only_lineage.py",
    "ai/tests/test_emlis_nls_v3_s11_rc0023_batch_evidence.py",
    "ai/tests/test_emlis_nls_v3_s11_rc0023_cycle_finalize.py",
    "ai/tests/test_emlis_nls_v3_s11_rc0023_matcher.py",
)
RC0024_ADDED_SOURCE_PATHS = (
    "ai/tests/test_emlis_nls_v3_s11_rc0024_append_only_lineage.py",
    "ai/tests/test_emlis_nls_v3_s11_rc0024_cycle_finalize.py",
    "ai/tests/test_emlis_nls_v3_s11_rc0024_source_slot_ownership.py",
)
RC0025_ADDED_SOURCE_PATHS = (
    "ai/tests/test_emlis_ai_nls_v3_rc0025_v1_surface_regression.py",
    "ai/tests/test_emlis_nls_v3_s11_rc0025_append_only_lineage.py",
    "ai/tests/test_emlis_nls_v3_s11_rc0025_cycle_finalize.py",
)
RC0020_ADDED_SOURCE_PATHS = (
    "ai/tests/test_emlis_nls_v3_s11_rc0020_append_only_lineage.py",
    "ai/tests/test_emlis_nls_v3_s11_rc0020_matcher.py",
    "ai/tests/test_emlis_nls_v3_s11_rc0020_required_unknown.py",
)


def _sha256(relative_path: str) -> str:
    return hashlib.sha256((REPO_ROOT / relative_path).read_bytes()).hexdigest()


def _validated_rc0020_preflight_manifest(
    value: Mapping[str, Any],
) -> dict[str, Any]:
    if (
        type(value) is not dict
        or validate_step11_dependency_manifest(value)
        or artifact_sha256(value)
        != FROZEN_RC0020_PREFLIGHT_MANIFEST_ARTIFACT_SHA256
        or value.get("candidate_version_id")
        != STEP11_HISTORICAL_RC0020_CANDIDATE_VERSION_ID
        or value.get("source_dependency_closure_sha256")
        != FROZEN_RC0020_PREFLIGHT_SOURCE_CLOSURE_SHA256
        or type(value.get("file_hashes")) is not list
        or len(value["file_hashes"])
        != FROZEN_RC0020_PREFLIGHT_FILE_COUNT
    ):
        raise ValueError("step11_rc0020_preflight_manifest_invalid")
    return dict(value)


def _validated_rc0021_preflight_manifest(
    value: Mapping[str, Any],
) -> dict[str, Any]:
    if (
        type(value) is not dict
        or validate_step11_dependency_manifest(value)
        or artifact_sha256(value)
        != FROZEN_RC0021_PREFLIGHT_MANIFEST_ARTIFACT_SHA256
        or value.get("candidate_version_id")
        != STEP11_HISTORICAL_RC0021_CANDIDATE_VERSION_ID
        or value.get("source_dependency_closure_sha256")
        != FROZEN_RC0021_PREFLIGHT_SOURCE_CLOSURE_SHA256
        or value.get("before_candidate_version_id")
        != STEP11_HISTORICAL_RC0020_CANDIDATE_VERSION_ID
        or value.get("before_source_closure_sha256")
        != FROZEN_RC0020_PREFLIGHT_SOURCE_CLOSURE_SHA256
        or type(value.get("file_hashes")) is not list
        or len(value["file_hashes"])
        != FROZEN_RC0021_PREFLIGHT_FILE_COUNT
    ):
        raise ValueError("step11_rc0021_preflight_manifest_invalid")
    return dict(value)


def _validated_rc0022_formal_manifest(
    value: Mapping[str, Any],
) -> dict[str, Any]:
    if (
        type(value) is not dict
        or validate_step11_dependency_manifest(value)
        or artifact_sha256(value)
        != FROZEN_RC0022_FORMAL_MANIFEST_ARTIFACT_SHA256
        or value.get("candidate_version_id")
        != STEP11_HISTORICAL_RC0022_CANDIDATE_VERSION_ID
        or value.get("source_dependency_closure_sha256")
        != FROZEN_RC0022_FORMAL_SOURCE_CLOSURE_SHA256
        or value.get("before_candidate_version_id")
        != STEP11_HISTORICAL_RC0021_CANDIDATE_VERSION_ID
        or value.get("before_source_closure_sha256")
        != FROZEN_RC0021_PREFLIGHT_SOURCE_CLOSURE_SHA256
        or type(value.get("file_hashes")) is not list
        or len(value["file_hashes"]) != FROZEN_RC0022_FORMAL_FILE_COUNT
    ):
        raise ValueError("step11_rc0022_formal_manifest_invalid")
    return dict(value)


def _validated_rc0023_formal_manifest(
    value: Mapping[str, Any],
) -> dict[str, Any]:
    if (
        type(value) is not dict
        or validate_step11_dependency_manifest(value)
        or artifact_sha256(value)
        != FROZEN_RC0023_FORMAL_MANIFEST_ARTIFACT_SHA256
        or value.get("candidate_version_id")
        != STEP11_HISTORICAL_RC0023_CANDIDATE_VERSION_ID
        or value.get("source_dependency_closure_sha256")
        != FROZEN_RC0023_FORMAL_SOURCE_CLOSURE_SHA256
        or value.get("before_candidate_version_id")
        != STEP11_HISTORICAL_RC0022_CANDIDATE_VERSION_ID
        or value.get("before_source_closure_sha256")
        != FROZEN_RC0022_FORMAL_SOURCE_CLOSURE_SHA256
        or type(value.get("file_hashes")) is not list
        or len(value["file_hashes"]) != FROZEN_RC0023_FORMAL_FILE_COUNT
    ):
        raise ValueError("step11_rc0023_formal_manifest_invalid")
    return dict(value)


def _validated_rc0024_formal_manifest(
    value: Mapping[str, Any],
) -> dict[str, Any]:
    if (
        type(value) is not dict
        or validate_step11_dependency_manifest(value)
        or artifact_sha256(value)
        != FROZEN_RC0024_FORMAL_MANIFEST_ARTIFACT_SHA256
        or value.get("candidate_version_id")
        != STEP11_HISTORICAL_RC0024_CANDIDATE_VERSION_ID
        or value.get("source_dependency_closure_sha256")
        != FROZEN_RC0024_FORMAL_SOURCE_CLOSURE_SHA256
        or value.get("before_candidate_version_id")
        != STEP11_HISTORICAL_RC0023_CANDIDATE_VERSION_ID
        or value.get("before_source_closure_sha256")
        != FROZEN_RC0023_FORMAL_SOURCE_CLOSURE_SHA256
        or type(value.get("file_hashes")) is not list
        or len(value["file_hashes"]) != FROZEN_RC0024_FORMAL_FILE_COUNT
    ):
        raise ValueError("step11_rc0024_formal_manifest_invalid")
    return dict(value)


def _validated_rc0019_preflight_manifest(
    value: Mapping[str, Any],
) -> dict[str, Any]:
    if (
        type(value) is not dict
        or validate_step11_dependency_manifest(value)
        or artifact_sha256(value)
        != FROZEN_RC0019_PREFLIGHT_MANIFEST_ARTIFACT_SHA256
        or value.get("candidate_version_id")
        != STEP11_HISTORICAL_RC0019_CANDIDATE_VERSION_ID
        or value.get("source_dependency_closure_sha256")
        != FROZEN_RC0019_PREFLIGHT_SOURCE_CLOSURE_SHA256
        or type(value.get("file_hashes")) is not list
        or len(value["file_hashes"]) != FROZEN_RC0019_PREFLIGHT_FILE_COUNT
    ):
        raise ValueError("step11_rc0019_preflight_manifest_invalid")
    return dict(value)


def _build_dependency_successor(
    predecessor: Mapping[str, Any],
    *,
    predecessor_file_count: int,
    added_source_paths: tuple[str, ...],
    candidate_version_id: str,
) -> dict[str, Any]:
    predecessor_hashes = {
        row["path"]: row["sha256"] for row in predecessor["file_hashes"]
    }
    if len(predecessor_hashes) != predecessor_file_count:
        raise ValueError("step11_predecessor_path_set_invalid")
    if any(path in predecessor_hashes for path in added_source_paths):
        raise ValueError("step11_added_path_already_in_predecessor")

    current_hashes: dict[str, str] = {}
    changed_paths: list[str] = []
    for relative_path, predecessor_sha256 in sorted(predecessor_hashes.items()):
        current_sha256 = _sha256(relative_path)
        current_hashes[relative_path] = current_sha256
        if current_sha256 != predecessor_sha256:
            changed_paths.append(relative_path)
    for relative_path in added_source_paths:
        current_hashes[relative_path] = _sha256(relative_path)
        changed_paths.append(relative_path)
    if not changed_paths:
        raise ValueError("step11_source_delta_required")

    files = [
        {"path": path, "sha256": sha256}
        for path, sha256 in sorted(current_hashes.items())
    ]
    changed = [
        {"path": path, "sha256": current_hashes[path]}
        for path in sorted(changed_paths)
    ]
    return build_step11_dependency_manifest(
        before_candidate_version_id=predecessor["candidate_version_id"],
        before_source_closure_sha256=predecessor[
            "source_dependency_closure_sha256"
        ],
        candidate_version_id=candidate_version_id,
        file_hashes=files,
        changed_file_hashes=changed,
    )


def build_current_step11_dependency_manifest(
    before_manifest: Mapping[str, Any],
) -> dict[str, Any]:
    if (
        type(before_manifest) is dict
        and before_manifest.get("candidate_version_id")
        == STEP11_HISTORICAL_RC0019_CANDIDATE_VERSION_ID
    ):
        predecessor = _validated_rc0019_preflight_manifest(before_manifest)
        return _build_dependency_successor(
            predecessor,
            predecessor_file_count=FROZEN_RC0019_PREFLIGHT_FILE_COUNT,
            added_source_paths=RC0020_ADDED_SOURCE_PATHS,
            candidate_version_id=STEP11_SUCCESSOR_CANDIDATE_VERSION_ID,
        )
    if (
        type(before_manifest) is dict
        and before_manifest.get("candidate_version_id")
        == STEP11_HISTORICAL_RC0020_CANDIDATE_VERSION_ID
    ):
        predecessor = _validated_rc0020_preflight_manifest(before_manifest)
        return _build_dependency_successor(
            predecessor,
            predecessor_file_count=FROZEN_RC0020_PREFLIGHT_FILE_COUNT,
            added_source_paths=RC0021_ADDED_SOURCE_PATHS,
            candidate_version_id=(
                STEP11_HISTORICAL_RC0021_CANDIDATE_VERSION_ID
            ),
        )
    if (
        type(before_manifest) is dict
        and before_manifest.get("candidate_version_id")
        == STEP11_HISTORICAL_RC0021_CANDIDATE_VERSION_ID
    ):
        predecessor = _validated_rc0021_preflight_manifest(before_manifest)
        return _build_dependency_successor(
            predecessor,
            predecessor_file_count=FROZEN_RC0021_PREFLIGHT_FILE_COUNT,
            added_source_paths=RC0022_ADDED_SOURCE_PATHS,
            candidate_version_id=(
                STEP11_HISTORICAL_RC0022_CANDIDATE_VERSION_ID
            ),
        )

    if (
        type(before_manifest) is dict
        and before_manifest.get("candidate_version_id")
        == STEP11_HISTORICAL_RC0022_CANDIDATE_VERSION_ID
    ):
        predecessor = _validated_rc0022_formal_manifest(before_manifest)
        return _build_dependency_successor(
            predecessor,
            predecessor_file_count=FROZEN_RC0022_FORMAL_FILE_COUNT,
            added_source_paths=RC0023_ADDED_SOURCE_PATHS,
            candidate_version_id=(
                STEP11_HISTORICAL_RC0023_CANDIDATE_VERSION_ID
            ),
        )

    if (
        type(before_manifest) is dict
        and before_manifest.get("candidate_version_id")
        == STEP11_HISTORICAL_RC0023_CANDIDATE_VERSION_ID
    ):
        predecessor = _validated_rc0023_formal_manifest(before_manifest)
        return _build_dependency_successor(
            predecessor,
            predecessor_file_count=FROZEN_RC0023_FORMAL_FILE_COUNT,
            added_source_paths=RC0024_ADDED_SOURCE_PATHS,
            candidate_version_id=(
                STEP11_HISTORICAL_RC0024_CANDIDATE_VERSION_ID
            ),
        )

    predecessor = _validated_rc0024_formal_manifest(before_manifest)
    if STEP11_CANDIDATE_VERSION_ID != STEP11_CURRENT_CANDIDATE_VERSION_ID:
        raise ValueError("step11_rc0025_candidate_owner_mismatch")
    return _build_dependency_successor(
        predecessor,
        predecessor_file_count=FROZEN_RC0024_FORMAL_FILE_COUNT,
        added_source_paths=RC0025_ADDED_SOURCE_PATHS,
        candidate_version_id=STEP11_CURRENT_CANDIDATE_VERSION_ID,
    )


def validate_current_step11_dependency_manifest(
    value: Any,
    *,
    before_manifest: Mapping[str, Any],
) -> tuple[str, ...]:
    try:
        expected = build_current_step11_dependency_manifest(before_manifest)
    except (KeyError, OSError, TypeError, ValueError):
        return ("STEP11_DEPENDENCY_FILES_UNAVAILABLE_OR_DRIFTED",)
    return () if value == expected else ("STEP11_DEPENDENCY_FILES_OR_MANIFEST_MISMATCH",)


def assert_current_step11_dependency_manifest(
    value: Any,
    *,
    before_manifest: Mapping[str, Any],
) -> str:
    issues = validate_current_step11_dependency_manifest(
        value,
        before_manifest=before_manifest,
    )
    if issues:
        raise ValueError(issues[0])
    return value["source_dependency_closure_sha256"]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--before-manifest", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    if args.output.exists():
        raise ValueError("step11_dependency_output_already_exists")
    before_manifest = json.loads(args.before_manifest.read_text(encoding="utf-8"))
    _write_json(
        args.output,
        build_current_step11_dependency_manifest(before_manifest),
        private=False,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
