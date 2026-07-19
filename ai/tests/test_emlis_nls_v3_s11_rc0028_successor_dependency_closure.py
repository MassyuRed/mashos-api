# -*- coding: utf-8 -*-
from __future__ import annotations

"""A0/A6: exact, body-free rc0028 experiment dependency closure."""

from copy import deepcopy
import json
from pathlib import Path

import pytest

from emlis_ai_nls_v3_artifact_contract import (
    artifact_sha256,
    load_canonical_json_bytes,
)
from emlis_ai_rc0028_experiment_dependency_manifest_v3 import (
    RC0027_PARENT_CANDIDATE_VERSION_ID,
    RC0027_PARENT_DISPOSITION,
    RC0027_PARENT_MANIFEST_ARTIFACT_SHA256,
    RC0027_PARENT_SOURCE_CLOSURE_SHA256,
    RC0027_PARENT_SOURCE_FILE_COUNT,
    RC0028_BASELINE_GIT_COMMIT,
    RC0028_BASELINE_GIT_TREE,
    RC0028_E1B_PREDECESSOR_SHA256,
    RC0028_EXPERIMENT_ADDED_OR_CHANGED_PATHS,
    RC0028_EXPERIMENT_DEPENDENCY_MANIFEST_SCHEMA,
    RC0028_GENERATED_MANIFEST_PATH,
    RC0028_SUCCESSOR_SOURCE_PATHS,
    Rc0028ExperimentDependencyError,
    build_rc0028_experiment_dependency_manifest,
    validate_rc0028_experiment_dependency_manifest,
    validate_rc0028_experiment_dependency_manifest_shape,
)


REPO_ROOT = Path(__file__).resolve().parents[2]
PARENT_PATH = (
    REPO_ROOT
    / "ai/tests/fixtures/emlis_nls_v3/cycle_001/"
    "cycle001_dependency_manifest_rc0027.json"
)
CURRENT_PATH = (
    REPO_ROOT
    / "ai/tests/fixtures/emlis_nls_v3/cycle_001/"
    "cycle001_dependency_manifest_rc0028_experiment.json"
)


def _read(path: Path) -> dict[str, object]:
    value = json.loads(path.read_text(encoding="utf-8"))
    assert type(value) is dict
    return value


def test_rc0028_experiment_parent_and_baseline_are_exact() -> None:
    parent = _read(PARENT_PATH)

    assert RC0027_PARENT_CANDIDATE_VERSION_ID == "nls_v3_rc_0027"
    assert RC0027_PARENT_SOURCE_FILE_COUNT == 161
    assert RC0027_PARENT_SOURCE_CLOSURE_SHA256 == (
        "1214bb6c586a0aecbb3f7d6b251613c9b05e190057aa276d5c29a045be538dc7"
    )
    assert RC0027_PARENT_MANIFEST_ARTIFACT_SHA256 == (
        "d7a3fc26fd3778f4c08c51e453cebaedd5e0f9674960d403090000b7cccfd450"
    )
    assert RC0027_PARENT_DISPOSITION == (
        "SOURCE_PREDECESSOR_ONLY_NOT_A_FORMAL_RC0027_FREEZE_CLAIM"
    )
    assert RC0028_BASELINE_GIT_COMMIT == (
        "31d3cf183589b27481338277574f90500f3c5b11"
    )
    assert RC0028_BASELINE_GIT_TREE == (
        "c826c3ed5587356f313a90a5b67611e3972abd42"
    )
    assert RC0028_E1B_PREDECESSOR_SHA256 == (
        "f449b44ef4bc007fb783a81b1e3884dcdcba017633b09fda3a4771bfd3149d50"
    )
    assert len(parent["file_hashes"]) == 161
    assert parent["source_dependency_closure_sha256"] == (
        RC0027_PARENT_SOURCE_CLOSURE_SHA256
    )
    assert artifact_sha256(parent) == RC0027_PARENT_MANIFEST_ARTIFACT_SHA256


def test_rc0028_experiment_manifest_is_exact_and_not_formal() -> None:
    parent = _read(PARENT_PATH)
    current = _read(CURRENT_PATH)

    assert current == build_rc0028_experiment_dependency_manifest(
        parent,
        repo_root=REPO_ROOT,
    )
    assert validate_rc0028_experiment_dependency_manifest(
        current,
        parent_manifest=parent,
        repo_root=REPO_ROOT,
    ) == ()
    assert current["schema_version"] == (
        RC0028_EXPERIMENT_DEPENDENCY_MANIFEST_SCHEMA
    )
    assert current["flags"] == {
        "experimental_only": True,
        "runtime_connected": False,
        "eligible_for_e0b": False,
        "eligible_for_e2": False,
        "eligible_for_formal": False,
        "eligible_for_production": False,
    }
    assert current["runtime_reverse_imports"] == []
    assert current["body_free"] is True


def test_rc0028_experiment_closure_inherits_all_161_parent_rows() -> None:
    parent = _read(PARENT_PATH)
    current = _read(CURRENT_PATH)
    parent_rows = {
        row["path"]: row["sha256"] for row in parent["file_hashes"]
    }
    current_rows = {
        row["path"]: row["sha256"] for row in current["file_hashes"]
    }
    changed_rows = {
        row["path"]: row["sha256"]
        for row in current["added_or_changed_file_hashes"]
    }

    assert len(parent_rows) == 161
    assert all(current_rows[path] == sha for path, sha in parent_rows.items())
    assert set(changed_rows) == set(RC0028_EXPERIMENT_ADDED_OR_CHANGED_PATHS)
    assert len(current_rows) == 161 + len(RC0028_EXPERIMENT_ADDED_OR_CHANGED_PATHS)
    assert RC0028_GENERATED_MANIFEST_PATH not in current_rows
    assert current["generated_manifest"] == {
        "path": RC0028_GENERATED_MANIFEST_PATH,
        "included_in_file_hashes": False,
        "artifact_hash_authority": "external_body_free_receipt",
    }


@pytest.mark.parametrize(
    ("field", "value", "issue"),
    (
        (
            "flags",
            {
                "experimental_only": True,
                "runtime_connected": True,
                "eligible_for_e0b": False,
                "eligible_for_e2": False,
                "eligible_for_formal": False,
                "eligible_for_production": False,
            },
            "RC0028_EXPERIMENT_ELIGIBILITY_FLAGS_INVALID",
        ),
        (
            "runtime_reverse_imports",
            ["ai/services/ai_inference/emlis_ai_reply_service.py"],
            "RC0028_EXPERIMENT_RUNTIME_CONNECTED",
        ),
        (
            "added_or_changed_paths",
            ["ai/services/ai_inference/unbound.py"],
            "RC0028_EXPERIMENT_PATH_ALLOWLIST_INVALID",
        ),
    ),
)
def test_rc0028_experiment_shape_rejects_authority_widening(
    field: str,
    value: object,
    issue: str,
) -> None:
    current = _read(CURRENT_PATH)
    mutated = deepcopy(current)
    mutated[field] = value

    assert issue in validate_rc0028_experiment_dependency_manifest_shape(
        mutated
    )


def test_rc0028_experiment_rejects_hash_and_path_mutations() -> None:
    current = _read(CURRENT_PATH)
    mutated_hash = deepcopy(current)
    mutated_hash["file_hashes"][0]["sha256"] = "1" * 64
    assert "RC0028_EXPERIMENT_CLOSURE_HASH_MISMATCH" in (
        validate_rc0028_experiment_dependency_manifest_shape(mutated_hash)
    )

    injected = deepcopy(current)
    injected["added_or_changed_file_hashes"].append(
        {
            "path": "ai/services/ai_inference/unbound.py",
            "sha256": "1" * 64,
        }
    )
    assert "RC0028_EXPERIMENT_FILE_ROWS_INVALID" in (
        validate_rc0028_experiment_dependency_manifest_shape(injected)
    )

    authority_path, witness_path, _snapshot_path = RC0028_SUCCESSOR_SOURCE_PATHS
    reversed_graph = deepcopy(current)
    reversed_graph["experiment_import_edges"].append(
        {
            "importer_path": authority_path,
            "imported_path": witness_path,
        }
    )
    reversed_graph["experiment_import_edges"].sort(
        key=lambda row: (row["importer_path"], row["imported_path"])
    )
    assert "RC0028_EXPERIMENT_IMPORT_DIRECTION_INVALID" in (
        validate_rc0028_experiment_dependency_manifest_shape(reversed_graph)
    )


def test_rc0028_experiment_rejects_non_exact_parent() -> None:
    parent = _read(PARENT_PATH)
    mutated = deepcopy(parent)
    mutated["file_hashes"][0]["sha256"] = "1" * 64

    with pytest.raises(
        Rc0028ExperimentDependencyError,
        match="RC0028_PARENT_INVALID",
    ):
        build_rc0028_experiment_dependency_manifest(
            mutated,
            repo_root=REPO_ROOT,
        )


def test_rc0028_experiment_manifest_contains_no_body_fields() -> None:
    current = _read(CURRENT_PATH)
    encoded = json.dumps(current, ensure_ascii=False, sort_keys=True)
    forbidden = (
        "thought_text",
        "action_text",
        "question_text",
        "raw_text",
        "source_text",
        "body_text",
        "private_corpus",
    )

    assert all(field not in encoded for field in forbidden)
    assert load_canonical_json_bytes(CURRENT_PATH.read_bytes()) == current
