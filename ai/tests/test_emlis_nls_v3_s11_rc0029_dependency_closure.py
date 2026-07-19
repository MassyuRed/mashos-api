# -*- coding: utf-8 -*-
from __future__ import annotations

"""Exact closure for the disconnected rc0029 surface-repair lane."""

import hashlib
import json
from pathlib import Path
import subprocess
import sys
from typing import Any

import emlis_ai_rc0029_surface_repair_experiment_dependency_manifest_v3 as dependency


_REPO_ROOT = Path(__file__).resolve().parents[2]
_CYCLE_ROOT = (
    Path(__file__).resolve().parent
    / "fixtures"
    / "emlis_nls_v3"
    / "cycle_001"
)
_PARENT = (
    _CYCLE_ROOT
    / "cycle001_dependency_manifest_rc0028_downstream_experiment.json"
)
_CURRENT = (
    _CYCLE_ROOT
    / "cycle001_dependency_manifest_rc0029_surface_repair_experiment.json"
)
_TOOL = (
    _REPO_ROOT
    / "ai"
    / "tools"
    / "emlis_nls_v3_rc0029_surface_repair_dependency_manifest.py"
)


def _load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    assert type(value) is dict
    return value


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_rc0029_manifest_rebuilds_exactly_from_immutable_rc0028() -> None:
    parent = _load(_PARENT)
    current = _load(_CURRENT)
    assert (
        dependency.validate_rc0029_surface_repair_dependency_manifest_shape(
            current
        )
        == ()
    )
    assert dependency.validate_rc0029_surface_repair_dependency_manifest(
        current,
        parent_manifest=parent,
        repo_root=_REPO_ROOT,
    ) == ()
    assert (
        dependency.build_rc0029_surface_repair_dependency_manifest(
            parent,
            repo_root=_REPO_ROOT,
        )
        == current
    )


def test_rc0029_manifest_binds_exact_four_plus_exact_new_allowlist() -> None:
    current = _load(_CURRENT)
    modified = current["modified_owner_file_hashes"]
    added = current["new_file_hashes"]
    delta_by_path = {
        row["path"]: row.get("current_sha256", row.get("sha256"))
        for row in modified + added
    }
    expected = set(dependency.RC0029_MODIFIED_OWNER_PATHS) | set(
        dependency.RC0029_HASHED_NEW_PATHS
    )
    assert set(delta_by_path) == expected
    assert all(
        delta_by_path[path] == _sha256(_REPO_ROOT / path)
        for path in delta_by_path
    )
    assert dependency.RC0029_GENERATED_MANIFEST_PATH not in {
        row["path"] for row in current["file_hashes"]
    }
    assert current["new_path_allowlist"] == sorted(
        dependency.RC0029_NEW_PATH_ALLOWLIST
    )
    assert current["unexpected_paths"] == []
    assert current["unbound_project_imports"] == []
    assert current["forbidden_reverse_imports"] == []


def test_rc0029_manifest_closes_disposition_and_parent_commitment() -> None:
    current = _load(_CURRENT)
    flags = current["flags"]
    assert flags == {
        "experimental_only": True,
        "runtime_connected": False,
        "public_owner_unchanged": True,
        "rc0027_default_behavior_equivalent": True,
        "rc0028_experiment_behavior_equivalent": True,
        "eligible_for_formal": False,
        "eligible_for_production": False,
    }
    assert current["parent"] == {
        "schema_version": (
            "cocolon.emlis.nls_v3."
            "rc0028_downstream_experiment_dependency_manifest.v1"
        ),
        "manifest_path": dependency.RC0028_DOWNSTREAM_PARENT_MANIFEST_PATH,
        "manifest_file_sha256": (
            dependency.RC0028_DOWNSTREAM_PARENT_MANIFEST_FILE_SHA256
        ),
        "manifest_artifact_sha256": (
            "7b3adafdbe6c21348e9dd74d8cd5ef84a8139aa616e3f8ae5e1dcbfb1b788c11"
        ),
        "source_dependency_closure_sha256": (
            "08a83e30954055facdb711e1253a81145101e565afde4327567f239169f2d942"
        ),
        "source_file_count": 192,
        "file_hashes_sha256": (
            "f2f89b85cb92d70408b9c80d26a4cad3fd3f13ab375d9bc77c164bac5ac61025"
        ),
        "immutable": True,
    }


def test_rc0029_manifest_tool_verifies_generated_fixture() -> None:
    current = _load(_CURRENT)
    completed = subprocess.run(
        (
            sys.executable,
            str(_TOOL),
            "--parent-manifest",
            str(_PARENT),
            "--repo-root",
            str(_REPO_ROOT),
            "--check",
            str(_CURRENT),
        ),
        cwd=_REPO_ROOT,
        check=False,
        capture_output=True,
        text=True,
        timeout=30,
    )
    assert completed.returncode == 0, completed.stderr
    assert completed.stderr == ""
    assert completed.stdout.strip() == current[
        "source_dependency_closure_sha256"
    ]
