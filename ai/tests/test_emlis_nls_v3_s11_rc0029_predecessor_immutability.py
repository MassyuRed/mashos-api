# -*- coding: utf-8 -*-
from __future__ import annotations

"""Byte freeze for the rc0028 logical parent of the rc0029 repair."""

import hashlib
import json
from pathlib import Path

import emlis_ai_rc0029_surface_repair_experiment_dependency_manifest_v3 as dependency


_REPO_ROOT = Path(__file__).resolve().parents[2]
_PARENT = (
    Path(__file__).resolve().parent
    / "fixtures"
    / "emlis_nls_v3"
    / "cycle_001"
    / "cycle001_dependency_manifest_rc0028_downstream_experiment.json"
)


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _sha256(path: Path) -> str:
    return _sha256_bytes(path.read_bytes())


def _parent() -> dict[str, object]:
    value = json.loads(_PARENT.read_text(encoding="utf-8"))
    assert type(value) is dict
    return value


def test_rc0028_generated_manifest_is_the_exact_immutable_parent() -> None:
    assert _sha256(_PARENT) == (
        dependency.RC0028_DOWNSTREAM_PARENT_MANIFEST_FILE_SHA256
    )
    parent = _parent()
    assert parent["source_dependency_closure_sha256"] == (
        "08a83e30954055facdb711e1253a81145101e565afde4327567f239169f2d942"
    )
    assert parent["source_file_count"] == 192


def test_rc0029_exact_four_preserve_the_complete_e069ffd_prefix() -> None:
    parent = _parent()
    parent_hashes = {
        row["path"]: row["sha256"]
        for row in parent["file_hashes"]  # type: ignore[index]
    }
    for row in dependency.RC0029_MODIFIED_OWNER_PREDECESSORS:
        path = row["path"]
        size = row["predecessor_size"]
        predecessor_sha256 = row["predecessor_sha256"]
        source = (_REPO_ROOT / path).read_bytes()
        assert parent_hashes[path] == predecessor_sha256
        assert len(source) >= size
        assert _sha256_bytes(source[:size]) == predecessor_sha256


def test_rc0029_does_not_drift_any_other_rc0028_parent_source() -> None:
    parent = _parent()
    modified = set(dependency.RC0029_MODIFIED_OWNER_PATHS)
    for row in parent["file_hashes"]:  # type: ignore[index]
        if row["path"] in modified:
            continue
        assert _sha256(_REPO_ROOT / row["path"]) == row["sha256"]
