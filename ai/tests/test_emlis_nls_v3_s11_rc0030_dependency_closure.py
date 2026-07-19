# -*- coding: utf-8 -*-
from __future__ import annotations

"""Phase-qualified P5 successor closure for the disconnected rc0030 lane."""

import hashlib
import json
from pathlib import Path
import subprocess
import sys
from typing import Any

import emlis_ai_rc0030_surface_planning_experiment_dependency_manifest_v3 as dependency


_REPO_ROOT = Path(__file__).resolve().parents[2]
_CYCLE_ROOT = (
    Path(__file__).resolve().parent
    / "fixtures"
    / "emlis_nls_v3"
    / "cycle_001"
)
_PARENT = (
    _CYCLE_ROOT
    / "cycle001_dependency_manifest_rc0029_surface_repair_experiment.json"
)
_CURRENT = (
    _CYCLE_ROOT
    / "cycle001_dependency_manifest_rc0030_surface_planning_experiment.json"
)
_TOOL = (
    _REPO_ROOT
    / "ai"
    / "tools"
    / "emlis_nls_v3_rc0030_surface_planning_dependency_manifest.py"
)


def _load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    assert type(value) is dict
    return value


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def test_rc0030_p5_manifest_rebuilds_from_immutable_predecessors() -> None:
    parent = _load(_PARENT)
    current = _load(_CURRENT)
    assert (
        dependency.validate_rc0030_surface_planning_dependency_manifest_shape(
            current
        )
        == ()
    )
    assert dependency.validate_rc0030_surface_planning_dependency_manifest(
        current,
        parent_manifest=parent,
        repo_root=_REPO_ROOT,
    ) == ()
    assert (
        dependency.build_rc0030_surface_planning_dependency_manifest(
            parent,
            repo_root=_REPO_ROOT,
        )
        == current
    )


def test_rc0030_p5_manifest_binds_exact_four_plus_active_paths() -> None:
    current = _load(_CURRENT)
    modified = current["modified_owner_file_hashes"]
    added = current["new_file_hashes"]
    delta_by_path = {
        row["path"]: row.get("current_sha256", row.get("sha256"))
        for row in modified + added
    }
    expected = set(dependency.RC0030_MODIFIED_OWNER_PATHS) | set(
        dependency.RC0030_P5_HASHED_NEW_PATHS
    )
    assert set(delta_by_path) == expected
    assert all(
        delta_by_path[path] == _sha256(_REPO_ROOT / path)
        for path in delta_by_path
    )
    assert dependency.RC0030_GENERATED_MANIFEST_PATH not in {
        row["path"] for row in current["file_hashes"]
    }
    assert current["new_path_allowlist"] == sorted(
        dependency.RC0030_NEW_PATH_ALLOWLIST
    )
    assert len(current["new_path_allowlist"]) == 18
    assert current["activation_policy"] == {
        "phase": dependency.RC0030_MANIFEST_PHASE,
        "exact18_is_closed_maximum": True,
        "active_new_paths": sorted(dependency.RC0030_P5_ACTIVE_NEW_PATHS),
        "newly_active_paths": sorted(
            dependency.RC0030_P5_NEWLY_ACTIVE_PATHS
        ),
        "reserved_absent_paths": sorted(
            dependency.RC0030_P5_RESERVED_ABSENT_PATHS
        ),
        "later_phase_activation": {
            phase: sorted(paths)
            for phase, paths in sorted(
                dependency.RC0030_LATER_PHASE_ACTIVATION.items()
            )
        },
        "later_phase_order": list(dependency.RC0030_LATER_PHASE_ORDER),
        "activation_is_monotonic": True,
    }
    assert set(dependency.RC0030_P5_ACTIVE_NEW_PATHS).isdisjoint(
        dependency.RC0030_P5_RESERVED_ABSENT_PATHS
    )
    assert set(dependency.RC0030_P5_ACTIVE_NEW_PATHS) | set(
        dependency.RC0030_P5_RESERVED_ABSENT_PATHS
    ) == set(dependency.RC0030_NEW_PATH_ALLOWLIST)
    assert set(dependency.RC0030_P5_NEWLY_ACTIVE_PATHS) == set(
        dependency.RC0030_P5_ACTIVE_NEW_PATHS
    ) - set(dependency.RC0030_P4_ACTIVE_NEW_PATHS)
    assert len(dependency.RC0030_P5_ACTIVE_NEW_PATHS) == 14
    assert len(dependency.RC0030_P5_HASHED_NEW_PATHS) == 13
    assert len(dependency.RC0030_P5_RESERVED_ABSENT_PATHS) == 4
    assert dependency.find_rc0030_surface_planning_reserved_paths(
        _REPO_ROOT
    ) == ()
    assert current["unexpected_paths"] == []
    assert current["unbound_project_imports"] == []
    assert current["forbidden_reverse_imports"] == []
    assert current["reserved_paths_present"] == []
    assert current["source_file_count"] == 222


def test_rc0030_p5_manifest_closes_phase_flags_and_predecessors() -> None:
    current = _load(_CURRENT)
    flags = current["flags"]
    assert flags == {
        "experimental_only": True,
        "runtime_connected": False,
        "public_owner_unchanged": True,
        "rc0027_default_behavior_equivalent": True,
        "rc0028_experiment_behavior_equivalent": True,
        "rc0029_experiment_behavior_equivalent": True,
        "eligible_for_formal": False,
        "eligible_for_production": False,
    }
    assert current["baseline_git_commit"] == (
        "e1e2ec5c17fa165f9972373304899802832ecd5b"
    )
    assert current["phase_predecessor_git_commit"] == (
        "3897331a5f605762e09f9953e47801d45d3c5da2"
    )
    assert current["manifest_phase"] == "P5_CARDINALITY_REGRESSION"
    assert current["parent"] == {
        "schema_version": (
            "cocolon.emlis.nls_v3."
            "rc0029_surface_repair_experiment_dependency_manifest.v1"
        ),
        "manifest_path": (
            dependency.RC0029_SURFACE_REPAIR_PARENT_MANIFEST_PATH
        ),
        "manifest_file_sha256": (
            dependency.RC0029_SURFACE_REPAIR_PARENT_MANIFEST_FILE_SHA256
        ),
        "manifest_artifact_sha256": (
            "05365d90ffec011868a6c7b9926505ca71fc675b9285ee6b8c3f4d15f714af8b"
        ),
        "source_dependency_closure_sha256": (
            "cd46925c6db478ac07e501acb64c45cae3a122ab0c1d834d06a83f1190cfb082"
        ),
        "source_file_count": 209,
        "file_hashes_sha256": (
            "55acda0e6971aefd6ab5c04cd214cb0668c3e0e9e05a1741981b63ba60872835"
        ),
        "immutable": True,
    }
    assert current["phase_predecessor"] == {
        "schema_version": dependency.RC0030_P4_MANIFEST_SCHEMA,
        "git_commit": dependency.RC0030_P5_PHASE_PREDECESSOR_GIT_COMMIT,
        "manifest_phase": dependency.RC0030_P4_MANIFEST_PHASE,
        "phase_predecessor_git_commit": (
            dependency.RC0030_P4_PHASE_PREDECESSOR_GIT_COMMIT
        ),
        "manifest_path": dependency.RC0030_GENERATED_MANIFEST_PATH,
        "manifest_file_sha256": dependency.RC0030_P4_MANIFEST_FILE_SHA256,
        "manifest_artifact_sha256": (
            dependency.RC0030_P4_MANIFEST_ARTIFACT_SHA256
        ),
        "source_dependency_closure_sha256": (
            dependency.RC0030_P4_SOURCE_DEPENDENCY_CLOSURE_SHA256
        ),
        "source_file_count": dependency.RC0030_P4_SOURCE_FILE_COUNT,
        "immutable": True,
    }
    by_path = {
        row["path"]: row
        for row in current["modified_owner_file_hashes"]
    }
    assert by_path[dependency.RC0030_MATCHER_PATH][
        "phase_predecessor_sha256"
    ] == "629305364ac50530265d7d87a6ca28678eb3e1be6ac7289ae770b3b5f871d8c9"
    assert by_path[dependency.RC0030_HARD_GATE_PATH][
        "phase_predecessor_sha256"
    ] == "1926ef12e74f1a9f53015f2d913cbb4b6881606e57e5078c6f8192e2894af4c7"
    assert by_path[dependency.RC0030_MATCHER_PATH]["current_sha256"] != (
        by_path[dependency.RC0030_MATCHER_PATH][
            "phase_predecessor_sha256"
        ]
    )
    assert by_path[dependency.RC0030_HARD_GATE_PATH]["current_sha256"] != (
        by_path[dependency.RC0030_HARD_GATE_PATH][
            "phase_predecessor_sha256"
        ]
    )


def test_rc0030_p5_manifest_rejects_phase_or_activation_mutation() -> None:
    current = _load(_CURRENT)
    stale_phase = {**current, "manifest_phase": "P4_GATE_RUNTIME_CLOSURE"}
    assert "RC0030_MANIFEST_IDENTITY_INVALID" in (
        dependency.validate_rc0030_surface_planning_dependency_manifest_shape(
            stale_phase
        )
    )
    altered = json.loads(json.dumps(current))
    altered["activation_policy"]["reserved_absent_paths"].pop()
    assert "RC0030_ACTIVATION_POLICY_INVALID" in (
        dependency.validate_rc0030_surface_planning_dependency_manifest_shape(
            altered
        )
    )


def test_rc0030_p5_manifest_tool_verifies_generated_fixture() -> None:
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
