# -*- coding: utf-8 -*-
from __future__ import annotations

"""Phase-qualified E2 successor closure for the disconnected rc0030 lane."""

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


def test_rc0030_e2_manifest_rebuilds_from_immutable_predecessors() -> None:
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


def test_rc0030_e2_manifest_binds_exact_four_plus_active_paths() -> None:
    current = _load(_CURRENT)
    modified = current["modified_owner_file_hashes"]
    added = current["new_file_hashes"]
    delta_by_path = {
        row["path"]: row.get("current_sha256", row.get("sha256"))
        for row in modified + added
    }
    expected = set(dependency.RC0030_MODIFIED_OWNER_PATHS) | set(
        dependency.RC0030_E2_HASHED_NEW_PATHS
    )
    assert set(delta_by_path) == expected
    assert all(
        delta_by_path[path] == _sha256(_REPO_ROOT / path)
        for path in delta_by_path
    )
    assert dependency.RC0030_E2_INTEGRATION_PHASE_PREDECESSOR_SHA256 == (
        "789008643a4d7ba388a26f35fbf2276eea5f1c3702f94ea6089377ce372d5eaa"
    )
    assert delta_by_path[dependency.RC0030_E2_NEWLY_ACTIVE_PATHS[0]] == (
        dependency.RC0030_E2_INTEGRATION_PHASE_PREDECESSOR_SHA256
    )
    assert dependency.RC0030_GENERATED_MANIFEST_PATH not in {
        row["path"] for row in current["file_hashes"]
    }
    assert current["new_path_allowlist"] == sorted(
        dependency.RC0030_NEW_PATH_ALLOWLIST
    )
    assert len(current["new_path_allowlist"]) == 18
    assert dependency.RC0030_NEW_PATH_ALLOWLIST[9] == (
        "ai/tests/test_emlis_nls_v3_s11_rc0030_e2_integration.py"
    )
    assert tuple(
        dependency.RC0030_NEW_PATH_ALLOWLIST[index]
        for index in (4, 15, 16)
    ) == dependency.RC0030_E2_RESERVED_ABSENT_PATHS
    assert current["activation_policy"] == {
        "phase": dependency.RC0030_MANIFEST_PHASE,
        "exact18_is_closed_maximum": True,
        "active_new_paths": sorted(dependency.RC0030_E2_ACTIVE_NEW_PATHS),
        "newly_active_paths": sorted(
            dependency.RC0030_E2_NEWLY_ACTIVE_PATHS
        ),
        "reserved_absent_paths": sorted(
            dependency.RC0030_E2_RESERVED_ABSENT_PATHS
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
    assert set(dependency.RC0030_E2_ACTIVE_NEW_PATHS).isdisjoint(
        dependency.RC0030_E2_RESERVED_ABSENT_PATHS
    )
    assert set(dependency.RC0030_E2_ACTIVE_NEW_PATHS) | set(
        dependency.RC0030_E2_RESERVED_ABSENT_PATHS
    ) == set(dependency.RC0030_NEW_PATH_ALLOWLIST)
    assert set(dependency.RC0030_E2_NEWLY_ACTIVE_PATHS) == set(
        dependency.RC0030_E2_ACTIVE_NEW_PATHS
    ) - set(dependency.RC0030_P5_ACTIVE_NEW_PATHS)
    assert dependency.RC0030_E2_NEWLY_ACTIVE_PATHS == (
        "ai/tests/test_emlis_nls_v3_s11_rc0030_e2_integration.py",
    )
    assert len(dependency.RC0030_E2_ACTIVE_NEW_PATHS) == 15
    assert len(dependency.RC0030_E2_HASHED_NEW_PATHS) == 14
    assert len(dependency.RC0030_E2_RESERVED_ABSENT_PATHS) == 3
    assert set(dependency.RC0030_E2_RESERVED_ABSENT_PATHS) == {
        dependency.RC0030_BOUNDED_EXPERIMENT_TOOL_PATH,
        "ai/tests/test_emlis_nls_v3_s11_rc0030_e3_representative8.py",
        "ai/tests/test_emlis_nls_v3_s11_rc0030_e4_frozen100_read_only.py",
    }
    assert dependency.RC0030_LATER_PHASE_ORDER == (
        "E3_MACHINE_AND_PRODUCT_READ",
        "E4_FROZEN100",
    )
    assert dependency.find_rc0030_surface_planning_reserved_paths(
        _REPO_ROOT
    ) == ()
    assert current["unexpected_paths"] == []
    assert current["unbound_project_imports"] == []
    assert current["forbidden_reverse_imports"] == []
    assert current["reserved_paths_present"] == []
    assert current["source_file_count"] == 223


def test_rc0030_e2_manifest_closes_phase_flags_and_predecessors() -> None:
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
        "45b178cfc0e7d94ab8385682ab3c7bbf0ab9aa25"
    )
    assert dependency.RC0030_E2_PHASE_PREDECESSOR_GIT_COMMIT == (
        "45b178cfc0e7d94ab8385682ab3c7bbf0ab9aa25"
    )
    assert current["manifest_phase"] == "E2_INTEGRATED_SYNCHRONIZATION"
    assert dependency.RC0030_P5_MANIFEST_SCHEMA == (
        "cocolon.emlis.nls_v3."
        "rc0030_surface_planning_experiment_dependency_manifest.v2"
    )
    assert dependency.RC0030_P5_MANIFEST_PHASE == (
        "P5_CARDINALITY_REGRESSION"
    )
    assert dependency.RC0030_P5_MANIFEST_GIT_COMMIT == (
        "924bd458255f226db54c17d84dd4aafc5db2b1e2"
    )
    assert dependency.RC0030_P5_MANIFEST_GIT_COMMIT != (
        dependency.RC0030_E2_PHASE_PREDECESSOR_GIT_COMMIT
    )
    assert dependency.RC0030_P5_MANIFEST_FILE_SHA256 == (
        "4ceb33aa6bb6f15d6ad9b7212bbdcee901edb352707f3f19a90e91ff6d91f62c"
    )
    assert dependency.RC0030_P5_MANIFEST_ARTIFACT_SHA256 == (
        "265418796ec720112ea046014b7dd3c612d392382647a64db5fe7396b4a976b7"
    )
    assert dependency.RC0030_P5_SOURCE_DEPENDENCY_CLOSURE_SHA256 == (
        "7c905f06c88ed4a19f8ece102cafbb1333dcce1b3e840081952682703ec038e5"
    )
    assert dependency.RC0030_P5_FILE_HASHES_SHA256 == (
        "75663d3799c8da7e196d4a30fcc29b1358ab4fc3a56b2461f7eb3b9ec2ecbf70"
    )
    assert dependency.RC0030_P5_SOURCE_FILE_COUNT == 222
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
        "schema_version": dependency.RC0030_P5_MANIFEST_SCHEMA,
        "git_commit": dependency.RC0030_P5_MANIFEST_GIT_COMMIT,
        "manifest_phase": dependency.RC0030_P5_MANIFEST_PHASE,
        "phase_predecessor_git_commit": (
            dependency.RC0030_P5_PHASE_PREDECESSOR_GIT_COMMIT
        ),
        "manifest_path": dependency.RC0030_GENERATED_MANIFEST_PATH,
        "manifest_file_sha256": dependency.RC0030_P5_MANIFEST_FILE_SHA256,
        "manifest_artifact_sha256": (
            dependency.RC0030_P5_MANIFEST_ARTIFACT_SHA256
        ),
        "source_dependency_closure_sha256": (
            dependency.RC0030_P5_SOURCE_DEPENDENCY_CLOSURE_SHA256
        ),
        "file_hashes_sha256": dependency.RC0030_P5_FILE_HASHES_SHA256,
        "source_file_count": dependency.RC0030_P5_SOURCE_FILE_COUNT,
        "immutable": True,
    }
    by_path = {
        row["path"]: row
        for row in current["modified_owner_file_hashes"]
    }
    expected_owner_lineage = {
        dependency.RC0030_LEXICALIZATION_PATH: (
            "592f3ab7c90831c3191f51e9e7dd9a1f8c3fe4add1fd31bba9fdc65dccaecc28",
            "592f3ab7c90831c3191f51e9e7dd9a1f8c3fe4add1fd31bba9fdc65dccaecc28",
            "592f3ab7c90831c3191f51e9e7dd9a1f8c3fe4add1fd31bba9fdc65dccaecc28",
        ),
        dependency.RC0030_SURFACE_PATH: (
            "8f8ea6f197bac02edc8ee3594165625e1e8f06e5a6a7bb44e41445d880ae9c37",
            "8f8ea6f197bac02edc8ee3594165625e1e8f06e5a6a7bb44e41445d880ae9c37",
            "5f548499e05e5a982f375dde5f059d7eba08f06fbc59bd0a76d9ed788a1e8eaf",
        ),
        dependency.RC0030_MATCHER_PATH: (
            "629305364ac50530265d7d87a6ca28678eb3e1be6ac7289ae770b3b5f871d8c9",
            "7665406076bdbae621a713df9fdf40ac6bf7cf2bfbbbc6659bcc2829908ddb5a",
            "648a3a6690f8df860053c811a5416fcfc9983524e5ff880a0e6921a122a52e30",
        ),
        dependency.RC0030_HARD_GATE_PATH: (
            "1926ef12e74f1a9f53015f2d913cbb4b6881606e57e5078c6f8192e2894af4c7",
            "2a70d294a8457d7f9328789ae6cba118d71bef477e2cc9a2ccb4facf24df68ca",
            "88514bb2a179e8d726f36e1666d2618330d95979107403ededc93aa35655943b",
        ),
    }
    assert set(by_path) == set(expected_owner_lineage)
    for path, (p4_sha256, p5_sha256, e2_sha256) in (
        expected_owner_lineage.items()
    ):
        assert by_path[path]["p4_phase_predecessor_sha256"] == p4_sha256
        assert by_path[path]["p5_phase_predecessor_sha256"] == p5_sha256
        assert by_path[path]["phase_predecessor_sha256"] == e2_sha256
        assert by_path[path]["current_sha256"] == e2_sha256


def test_rc0030_e2_manifest_rejects_phase_or_activation_mutation() -> None:
    current = _load(_CURRENT)
    stale_phase = {**current, "manifest_phase": "P5_CARDINALITY_REGRESSION"}
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
    collapsed_predecessor = json.loads(json.dumps(current))
    collapsed_predecessor["phase_predecessor"]["git_commit"] = (
        dependency.RC0030_E2_PHASE_PREDECESSOR_GIT_COMMIT
    )
    assert "RC0030_PHASE_PREDECESSOR_BINDING_INVALID" in (
        dependency.validate_rc0030_surface_planning_dependency_manifest_shape(
            collapsed_predecessor
        )
    )
    altered_owner = json.loads(json.dumps(current))
    surface_row = next(
        row
        for row in altered_owner["modified_owner_file_hashes"]
        if row["path"] == dependency.RC0030_SURFACE_PATH
    )
    surface_row["phase_predecessor_sha256"] = surface_row[
        "p5_phase_predecessor_sha256"
    ]
    assert "RC0030_MODIFIED_OWNER_LEDGER_INVALID" in (
        dependency.validate_rc0030_surface_planning_dependency_manifest_shape(
            altered_owner
        )
    )


def test_rc0030_e2_manifest_tool_verifies_generated_fixture() -> None:
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
