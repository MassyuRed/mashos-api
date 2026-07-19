# -*- coding: utf-8 -*-
from __future__ import annotations

"""A6: successor dependency graph remains experiment-only and one-way."""

import json
from pathlib import Path

from emlis_ai_rc0028_experiment_dependency_manifest_v3 import (
    RC0028_EXPERIMENT_MANIFEST_OWNER_PATH,
    RC0028_EXPERIMENT_MANIFEST_TOOL_PATH,
    RC0028_SUCCESSOR_SOURCE_PATHS,
    find_rc0028_unexpected_reverse_imports,
)


REPO_ROOT = Path(__file__).resolve().parents[2]
CURRENT_PATH = (
    REPO_ROOT
    / "ai/tests/fixtures/emlis_nls_v3/cycle_001/"
    "cycle001_dependency_manifest_rc0028_experiment.json"
)


def _manifest() -> dict[str, object]:
    value = json.loads(CURRENT_PATH.read_text(encoding="utf-8"))
    assert type(value) is dict
    return value


def test_rc0028_successor_has_no_runtime_or_production_reverse_import() -> None:
    assert find_rc0028_unexpected_reverse_imports(REPO_ROOT) == ()
    manifest = _manifest()
    assert manifest["runtime_reverse_imports"] == []
    assert manifest["flags"]["runtime_connected"] is False
    assert manifest["flags"]["eligible_for_production"] is False


def test_rc0028_successor_import_graph_is_strictly_upstream_to_downstream() -> None:
    manifest = _manifest()
    edges = {
        (row["importer_path"], row["imported_path"])
        for row in manifest["experiment_import_edges"]
    }
    authority_path, witness_path, snapshot_path = RC0028_SUCCESSOR_SOURCE_PATHS

    assert (witness_path, authority_path) in edges
    assert (snapshot_path, authority_path) in edges
    assert (snapshot_path, witness_path) in edges
    assert (authority_path, witness_path) not in edges
    assert (authority_path, snapshot_path) not in edges
    assert (witness_path, snapshot_path) not in edges


def test_rc0028_successor_entrypoints_are_tests_and_manifest_tool_only() -> None:
    manifest = _manifest()
    entrypoints = manifest["allowed_experiment_entrypoint_paths"]
    assert RC0028_EXPERIMENT_MANIFEST_TOOL_PATH in entrypoints
    assert RC0028_EXPERIMENT_MANIFEST_OWNER_PATH not in entrypoints
    assert all(
        path == RC0028_EXPERIMENT_MANIFEST_TOOL_PATH
        or path.startswith("ai/tests/test_emlis_nls_v3_s11_rc0028_")
        for path in entrypoints
    )
    assert all(
        not path.startswith(
            (
                "ai/services/api/",
                "ai/services/runtime/",
                "ai/services/worker/",
            )
        )
        for path in entrypoints
    )
