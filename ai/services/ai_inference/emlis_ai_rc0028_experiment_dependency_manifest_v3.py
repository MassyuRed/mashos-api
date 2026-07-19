# -*- coding: utf-8 -*-
from __future__ import annotations

"""Closed, body-free dependency authority for the rc0028 E1b experiment.

This owner is deliberately independent from the frozen Step 9/Step 10 and
shared Step 11 manifests.  It can account for an experiment; it cannot make
that experiment formal, runtime-connected, product-eligible, or production
eligible.
"""

import ast
import hashlib
from pathlib import Path
import re
from typing import Any, Mapping, Sequence

from emlis_ai_nls_v3_artifact_contract import artifact_sha256
from emlis_ai_step9_dependency_manifest_v3 import (
    validate_step9_dependency_manifest,
)


RC0028_EXPERIMENT_DEPENDENCY_MANIFEST_SCHEMA = (
    "cocolon.emlis.nls_v3.rc0028_experiment_dependency_manifest.v1"
)
RC0028_EXPERIMENT_ID = "nls_v3_rc0028_e1b_successor_experiment"
RC0028_BASELINE_GIT_COMMIT = (
    "31d3cf183589b27481338277574f90500f3c5b11"
)
RC0028_BASELINE_GIT_TREE = "c826c3ed5587356f313a90a5b67611e3972abd42"

RC0027_PARENT_CANDIDATE_VERSION_ID = "nls_v3_rc_0027"
RC0027_PARENT_SOURCE_FILE_COUNT = 161
RC0027_PARENT_SOURCE_CLOSURE_SHA256 = (
    "1214bb6c586a0aecbb3f7d6b251613c9b05e190057aa276d5c29a045be538dc7"
)
RC0027_PARENT_MANIFEST_ARTIFACT_SHA256 = (
    "d7a3fc26fd3778f4c08c51e453cebaedd5e0f9674960d403090000b7cccfd450"
)
RC0027_PARENT_DISPOSITION = (
    "SOURCE_PREDECESSOR_ONLY_NOT_A_FORMAL_RC0027_FREEZE_CLAIM"
)

RC0028_E1B_PREDECESSOR_PATH = (
    "ai/tests/test_emlis_nls_v3_s11_rc0028_e1b_information_sufficiency_red.py"
)
RC0028_E1B_PREDECESSOR_SHA256 = (
    "f449b44ef4bc007fb783a81b1e3884dcdcba017633b09fda3a4771bfd3149d50"
)
RC0028_V1_LEXICAL_WITNESS_PATH = (
    "ai/services/ai_inference/emlis_ai_grounded_lexical_role_witness_v3.py"
)
RC0028_V1_LEXICAL_WITNESS_SHA256 = (
    "1523690453647bee2a6e61fb91d7b14823baee4e383c006bc2814006a4beb94b"
)
RC0028_V1_EXPERIMENT_SNAPSHOT_PATH = (
    "ai/services/ai_inference/"
    "emlis_ai_grounded_lexical_role_experiment_snapshot_v3.py"
)
RC0028_V1_EXPERIMENT_SNAPSHOT_SHA256 = (
    "4671aa22c4e432f907780f0becf900fead57044c53ea3bbc1bf501eb5abc1a27"
)

STEP9_MANIFEST_SOURCE_PATH = (
    "ai/services/ai_inference/emlis_ai_step9_dependency_manifest_v3.py"
)
STEP9_MANIFEST_SOURCE_SHA256 = (
    "19a21d5853c44130c2c874e8b9c6bbbc0a1fc79591c529fb060e7c1e3cd7742e"
)
STEP9_MANIFEST_ARTIFACT_SHA256 = (
    "9ac49f3ee8978f48ff402afdd9fb15f16063595546898e514b09b9bdaf58e880"
)
STEP9_DIRECT_OWNER_PATHS = (
    "ai/services/ai_inference/emlis_ai_grounded_observation_plan.py",
    "ai/services/ai_inference/"
    "emlis_ai_grounded_observation_semantic_restatement_v3.py",
    "ai/services/ai_inference/emlis_ai_semantic_obligation_inventory_v3.py",
)
STEP9_DIRECT_OWNER_SHA256 = (
    "b422093f907f3a825ec30f687f2f8b1d2688bf89950d9bc7436bfe0b5a67d177",
    "a014e942b34c2c8f2a424dda0b0ecd30cb34ff99112e813d2182ad84d34b65fc",
    "1dadb411fad46abb617da9ef9fcb48b18d8be987318966616d804c6ec69adbcb",
)

RC0028_RELATION_AUTHORITY_SUCCESSOR_PATH = (
    "ai/services/ai_inference/"
    "emlis_ai_grounded_relation_construction_authority_successor_v3.py"
)
RC0028_LEXICAL_WITNESS_SUCCESSOR_PATH = (
    "ai/services/ai_inference/"
    "emlis_ai_grounded_lexical_role_witness_successor_v3.py"
)
RC0028_EXPERIMENT_SNAPSHOT_SUCCESSOR_PATH = (
    "ai/services/ai_inference/"
    "emlis_ai_grounded_lexical_role_experiment_snapshot_successor_v3.py"
)
RC0028_EXPERIMENT_MANIFEST_OWNER_PATH = (
    "ai/services/ai_inference/"
    "emlis_ai_rc0028_experiment_dependency_manifest_v3.py"
)
RC0028_EXPERIMENT_MANIFEST_TOOL_PATH = (
    "ai/tools/emlis_nls_v3_rc0028_experiment_dependency_manifest.py"
)
RC0027_PARENT_FIXTURE_PATH = (
    "ai/tests/fixtures/emlis_nls_v3/cycle_001/"
    "cycle001_dependency_manifest_rc0027.json"
)
RC0028_GENERATED_MANIFEST_PATH = (
    "ai/tests/fixtures/emlis_nls_v3/cycle_001/"
    "cycle001_dependency_manifest_rc0028_experiment.json"
)

# A0 exact change ledger.  No filesystem walk may add a path to this tuple.
# The generated manifest is deliberately excluded to avoid a self-hash cycle.
RC0028_EXPERIMENT_ADDED_OR_CHANGED_PATHS = (
    RC0028_V1_LEXICAL_WITNESS_PATH,
    RC0028_V1_EXPERIMENT_SNAPSHOT_PATH,
    "ai/tests/test_emlis_nls_v3_s11_rc0028_upstream_lexical_role_red.py",
    "ai/tests/test_emlis_nls_v3_s11_rc0028_lexical_role_snapshot_red.py",
    RC0028_E1B_PREDECESSOR_PATH,
    RC0028_RELATION_AUTHORITY_SUCCESSOR_PATH,
    RC0028_LEXICAL_WITNESS_SUCCESSOR_PATH,
    RC0028_EXPERIMENT_SNAPSHOT_SUCCESSOR_PATH,
    RC0028_EXPERIMENT_MANIFEST_OWNER_PATH,
    RC0028_EXPERIMENT_MANIFEST_TOOL_PATH,
    "ai/tests/test_emlis_nls_v3_s11_rc0028_successor_authority.py",
    "ai/tests/test_emlis_nls_v3_s11_rc0028_successor_lexical_role.py",
    "ai/tests/test_emlis_nls_v3_s11_rc0028_successor_snapshot.py",
    "ai/tests/test_emlis_nls_v3_s11_rc0028_successor_dependency_closure.py",
    "ai/tests/test_emlis_nls_v3_s11_rc0028_successor_runtime_disconnect.py",
    RC0027_PARENT_FIXTURE_PATH,
)

RC0028_SUCCESSOR_SOURCE_PATHS = (
    RC0028_RELATION_AUTHORITY_SUCCESSOR_PATH,
    RC0028_LEXICAL_WITNESS_SUCCESSOR_PATH,
    RC0028_EXPERIMENT_SNAPSHOT_SUCCESSOR_PATH,
)
RC0028_ALLOWED_EXPERIMENT_ENTRYPOINT_PATHS = (
    RC0028_EXPERIMENT_MANIFEST_TOOL_PATH,
    "ai/tests/test_emlis_nls_v3_s11_rc0028_upstream_lexical_role_red.py",
    "ai/tests/test_emlis_nls_v3_s11_rc0028_lexical_role_snapshot_red.py",
    RC0028_E1B_PREDECESSOR_PATH,
    "ai/tests/test_emlis_nls_v3_s11_rc0028_successor_authority.py",
    "ai/tests/test_emlis_nls_v3_s11_rc0028_successor_lexical_role.py",
    "ai/tests/test_emlis_nls_v3_s11_rc0028_successor_snapshot.py",
    "ai/tests/test_emlis_nls_v3_s11_rc0028_successor_dependency_closure.py",
    "ai/tests/test_emlis_nls_v3_s11_rc0028_successor_runtime_disconnect.py",
)

_SHA_RE = re.compile(r"^[0-9a-f]{64}$")
_SAFE_PATH_RE = re.compile(r"^ai/[A-Za-z0-9_./-]+$")
_SUCCESSOR_MODULE_RANK = {
    Path(RC0028_RELATION_AUTHORITY_SUCCESSOR_PATH).stem: 0,
    Path(RC0028_LEXICAL_WITNESS_SUCCESSOR_PATH).stem: 1,
    Path(RC0028_EXPERIMENT_SNAPSHOT_SUCCESSOR_PATH).stem: 2,
}


class Rc0028ExperimentDependencyError(ValueError):
    """The experiment closure cannot be built without widening authority."""


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _safe_file_rows(value: Any) -> list[dict[str, str]]:
    if type(value) is not list or not value:
        raise Rc0028ExperimentDependencyError("RC0028_FILE_ROWS_REQUIRED")
    rows: list[dict[str, str]] = []
    seen: set[str] = set()
    for item in value:
        if type(item) is not dict or set(item) != {"path", "sha256"}:
            raise Rc0028ExperimentDependencyError("RC0028_FILE_ROW_SHAPE_INVALID")
        path = item.get("path")
        sha256 = item.get("sha256")
        if (
            type(path) is not str
            or _SAFE_PATH_RE.fullmatch(path) is None
            or ".." in Path(path).parts
            or type(sha256) is not str
            or _SHA_RE.fullmatch(sha256) is None
            or sha256 == "0" * 64
            or path in seen
        ):
            raise Rc0028ExperimentDependencyError("RC0028_FILE_ROW_INVALID")
        seen.add(path)
        rows.append({"path": path, "sha256": sha256})
    if rows != sorted(rows, key=lambda row: row["path"]):
        raise Rc0028ExperimentDependencyError("RC0028_FILE_ROWS_NOT_SORTED")
    return rows


def _validated_parent_manifest(value: Any) -> dict[str, Any]:
    if type(value) is not dict:
        raise Rc0028ExperimentDependencyError("RC0028_PARENT_MAPPING_REQUIRED")
    try:
        files = _safe_file_rows(value["file_hashes"])
    except (KeyError, TypeError) as exc:
        raise Rc0028ExperimentDependencyError("RC0028_PARENT_INVALID") from exc
    if (
        value.get("candidate_version_id") != RC0027_PARENT_CANDIDATE_VERSION_ID
        or value.get("source_dependency_closure_sha256")
        != RC0027_PARENT_SOURCE_CLOSURE_SHA256
        or len(files) != RC0027_PARENT_SOURCE_FILE_COUNT
        or artifact_sha256(value) != RC0027_PARENT_MANIFEST_ARTIFACT_SHA256
    ):
        raise Rc0028ExperimentDependencyError("RC0028_PARENT_INVALID")
    return dict(value)


def _module_index(paths: Sequence[str]) -> dict[str, str]:
    result: dict[str, str] = {}
    for path in paths:
        if not path.endswith(".py"):
            continue
        module = Path(path).stem
        if module == "__init__":
            continue
        previous = result.get(module)
        if previous is not None and previous != path:
            raise Rc0028ExperimentDependencyError(
                "RC0028_LOCAL_MODULE_NAME_COLLISION"
            )
        result[module] = path
    return result


def _imported_modules(
    source: bytes,
    *,
    allow_relative: bool = False,
) -> tuple[str, ...]:
    try:
        tree = ast.parse(source)
    except (SyntaxError, UnicodeError) as exc:
        raise Rc0028ExperimentDependencyError("RC0028_SOURCE_AST_INVALID") from exc
    modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules.update(alias.name.split(".", 1)[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom):
            if node.level and not allow_relative:
                raise Rc0028ExperimentDependencyError(
                    "RC0028_RELATIVE_IMPORT_FORBIDDEN"
                )
            if node.module:
                modules.add(node.module.split(".", 1)[0])
    return tuple(sorted(modules))


def _experiment_import_edges(
    repo_root: Path,
    *,
    closure_paths: Sequence[str],
) -> list[dict[str, str]]:
    index = _module_index(closure_paths)
    edges: set[tuple[str, str]] = set()
    for importer_path in RC0028_EXPERIMENT_ADDED_OR_CHANGED_PATHS:
        if not importer_path.endswith(".py"):
            continue
        source = (repo_root / importer_path).read_bytes()
        for imported_module in _imported_modules(source):
            imported_path = index.get(imported_module)
            if imported_path is not None:
                edges.add((importer_path, imported_path))
                continue
            if imported_module.startswith(("emlis_ai_", "test_emlis_")):
                raise Rc0028ExperimentDependencyError(
                    "RC0028_UNBOUND_LOCAL_IMPORT"
                )

    for importer_path, imported_path in edges:
        importer = Path(importer_path).stem
        imported = Path(imported_path).stem
        importer_rank = _SUCCESSOR_MODULE_RANK.get(importer)
        imported_rank = _SUCCESSOR_MODULE_RANK.get(imported)
        if (
            importer_rank is not None
            and imported_rank is not None
            and imported_rank >= importer_rank
        ):
            raise Rc0028ExperimentDependencyError(
                "RC0028_SUCCESSOR_IMPORT_DIRECTION_INVALID"
            )
    return [
        {"importer_path": importer, "imported_path": imported}
        for importer, imported in sorted(edges)
    ]


def find_rc0028_unexpected_reverse_imports(repo_root: Path) -> tuple[str, ...]:
    """Return production/tool files that import a successor runtime owner.

    Discovery is used only as a rejection audit.  It never admits files into
    the source closure; admission remains the exact A0 tuple above.
    """

    successor_modules = frozenset(_SUCCESSOR_MODULE_RANK)
    excluded_paths = set(RC0028_SUCCESSOR_SOURCE_PATHS) | {
        RC0028_EXPERIMENT_MANIFEST_OWNER_PATH,
        RC0028_EXPERIMENT_MANIFEST_TOOL_PATH,
    }
    roots = (repo_root / "ai" / "services", repo_root / "ai" / "tools")
    found: list[str] = []
    for root in roots:
        for path in sorted(root.rglob("*.py")):
            relative = path.relative_to(repo_root).as_posix()
            if relative in excluded_paths:
                continue
            try:
                imported = set(
                    _imported_modules(path.read_bytes(), allow_relative=True)
                )
            except OSError as exc:
                raise Rc0028ExperimentDependencyError(
                    "RC0028_REVERSE_IMPORT_SCAN_UNAVAILABLE"
                ) from exc
            if imported & successor_modules:
                found.append(relative)
    return tuple(found)


def _step9_baseline(parent_by_path: Mapping[str, str]) -> dict[str, Any]:
    try:
        source_hash = parent_by_path[STEP9_MANIFEST_SOURCE_PATH]
        direct = [
            {"path": path, "sha256": parent_by_path[path]}
            for path in STEP9_DIRECT_OWNER_PATHS
        ]
    except KeyError as exc:
        raise Rc0028ExperimentDependencyError(
            "RC0028_STEP9_PARENT_BINDING_MISSING"
        ) from exc
    if source_hash != STEP9_MANIFEST_SOURCE_SHA256 or tuple(
        row["sha256"] for row in direct
    ) != STEP9_DIRECT_OWNER_SHA256:
        raise Rc0028ExperimentDependencyError("RC0028_STEP9_BASELINE_DRIFT")
    return {
        "validation_status": "passed",
        "manifest_source_path": STEP9_MANIFEST_SOURCE_PATH,
        "manifest_source_sha256": source_hash,
        "manifest_artifact_sha256": STEP9_MANIFEST_ARTIFACT_SHA256,
        "direct_owner_file_hashes": direct,
    }


def build_rc0028_experiment_dependency_manifest(
    parent_manifest: Mapping[str, Any],
    *,
    repo_root: Path,
) -> dict[str, Any]:
    """Build the exact rc0027 + explicitly admitted rc0028 experiment closure."""

    parent = _validated_parent_manifest(parent_manifest)
    if validate_step9_dependency_manifest():
        raise Rc0028ExperimentDependencyError("RC0028_STEP9_VALIDATION_FAILED")
    parent_files = _safe_file_rows(parent["file_hashes"])
    parent_by_path = {row["path"]: row["sha256"] for row in parent_files}
    if any(path in parent_by_path for path in RC0028_EXPERIMENT_ADDED_OR_CHANGED_PATHS):
        raise Rc0028ExperimentDependencyError("RC0028_ADDED_PATH_IN_PARENT")
    if RC0028_GENERATED_MANIFEST_PATH in parent_by_path:
        raise Rc0028ExperimentDependencyError("RC0028_SELF_HASH_PATH_IN_PARENT")

    for path, expected in parent_by_path.items():
        try:
            actual = _sha256(repo_root / path)
        except OSError as exc:
            raise Rc0028ExperimentDependencyError(
                "RC0028_PARENT_SOURCE_UNAVAILABLE"
            ) from exc
        if actual != expected:
            raise Rc0028ExperimentDependencyError("RC0028_PARENT_SOURCE_DRIFT")

    added: list[dict[str, str]] = []
    for path in RC0028_EXPERIMENT_ADDED_OR_CHANGED_PATHS:
        try:
            sha256 = _sha256(repo_root / path)
        except OSError as exc:
            raise Rc0028ExperimentDependencyError(
                "RC0028_ALLOWLIST_SOURCE_UNAVAILABLE"
            ) from exc
        added.append({"path": path, "sha256": sha256})
    added.sort(key=lambda row: row["path"])

    added_by_path = {row["path"]: row["sha256"] for row in added}
    if (
        added_by_path.get(RC0028_V1_LEXICAL_WITNESS_PATH)
        != RC0028_V1_LEXICAL_WITNESS_SHA256
        or added_by_path.get(RC0028_V1_EXPERIMENT_SNAPSHOT_PATH)
        != RC0028_V1_EXPERIMENT_SNAPSHOT_SHA256
    ):
        raise Rc0028ExperimentDependencyError("RC0028_V1_CHECKPOINT_DRIFT")

    reverse_imports = find_rc0028_unexpected_reverse_imports(repo_root)
    if reverse_imports:
        raise Rc0028ExperimentDependencyError(
            "RC0028_UNEXPECTED_RUNTIME_REVERSE_IMPORT"
        )
    files = sorted(parent_files + added, key=lambda row: row["path"])
    edges = _experiment_import_edges(
        repo_root,
        closure_paths=[row["path"] for row in files],
    )
    material: dict[str, Any] = {
        "schema_version": RC0028_EXPERIMENT_DEPENDENCY_MANIFEST_SCHEMA,
        "experiment_id": RC0028_EXPERIMENT_ID,
        "baseline_git_commit": RC0028_BASELINE_GIT_COMMIT,
        "baseline_git_tree": RC0028_BASELINE_GIT_TREE,
        "parent": {
            "candidate_version_id": RC0027_PARENT_CANDIDATE_VERSION_ID,
            "source_file_count": RC0027_PARENT_SOURCE_FILE_COUNT,
            "source_dependency_closure_sha256": (
                RC0027_PARENT_SOURCE_CLOSURE_SHA256
            ),
            "manifest_artifact_sha256": (
                RC0027_PARENT_MANIFEST_ARTIFACT_SHA256
            ),
            "disposition": RC0027_PARENT_DISPOSITION,
        },
        "flags": {
            "experimental_only": True,
            "runtime_connected": False,
            "eligible_for_e0b": False,
            "eligible_for_e2": False,
            "eligible_for_formal": False,
            "eligible_for_production": False,
        },
        "step9_baseline": _step9_baseline(parent_by_path),
        "predecessors": {
            "e1b_red_path": RC0028_E1B_PREDECESSOR_PATH,
            "e1b_red_sha256": RC0028_E1B_PREDECESSOR_SHA256,
            "v1_lexical_witness_path": RC0028_V1_LEXICAL_WITNESS_PATH,
            "v1_lexical_witness_sha256": RC0028_V1_LEXICAL_WITNESS_SHA256,
            "v1_experiment_snapshot_path": (
                RC0028_V1_EXPERIMENT_SNAPSHOT_PATH
            ),
            "v1_experiment_snapshot_sha256": (
                RC0028_V1_EXPERIMENT_SNAPSHOT_SHA256
            ),
        },
        "generated_manifest": {
            "path": RC0028_GENERATED_MANIFEST_PATH,
            "included_in_file_hashes": False,
            "artifact_hash_authority": "external_body_free_receipt",
        },
        "added_or_changed_paths": list(
            sorted(RC0028_EXPERIMENT_ADDED_OR_CHANGED_PATHS)
        ),
        "allowed_experiment_entrypoint_paths": list(
            sorted(RC0028_ALLOWED_EXPERIMENT_ENTRYPOINT_PATHS)
        ),
        "file_hashes": files,
        "added_or_changed_file_hashes": added,
        "experiment_import_edges": edges,
        "runtime_reverse_imports": [],
        "body_free": True,
    }
    closure = artifact_sha256(material)
    return {**material, "source_dependency_closure_sha256": closure}


def validate_rc0028_experiment_dependency_manifest_shape(
    value: Any,
) -> tuple[str, ...]:
    """Validate closed shape and internal commitments without filesystem I/O."""

    if type(value) is not dict:
        return ("RC0028_EXPERIMENT_MANIFEST_MAPPING_REQUIRED",)
    expected_keys = {
        "schema_version",
        "experiment_id",
        "baseline_git_commit",
        "baseline_git_tree",
        "parent",
        "flags",
        "step9_baseline",
        "predecessors",
        "generated_manifest",
        "added_or_changed_paths",
        "allowed_experiment_entrypoint_paths",
        "file_hashes",
        "added_or_changed_file_hashes",
        "experiment_import_edges",
        "runtime_reverse_imports",
        "body_free",
        "source_dependency_closure_sha256",
    }
    issues: set[str] = set()
    if set(value) != expected_keys:
        issues.add("RC0028_EXPERIMENT_MANIFEST_SHAPE_INVALID")
    if (
        value.get("schema_version")
        != RC0028_EXPERIMENT_DEPENDENCY_MANIFEST_SCHEMA
        or value.get("experiment_id") != RC0028_EXPERIMENT_ID
        or value.get("baseline_git_commit") != RC0028_BASELINE_GIT_COMMIT
        or value.get("baseline_git_tree") != RC0028_BASELINE_GIT_TREE
        or value.get("body_free") is not True
    ):
        issues.add("RC0028_EXPERIMENT_MANIFEST_IDENTITY_INVALID")
    expected_parent = {
        "candidate_version_id": RC0027_PARENT_CANDIDATE_VERSION_ID,
        "source_file_count": RC0027_PARENT_SOURCE_FILE_COUNT,
        "source_dependency_closure_sha256": (
            RC0027_PARENT_SOURCE_CLOSURE_SHA256
        ),
        "manifest_artifact_sha256": RC0027_PARENT_MANIFEST_ARTIFACT_SHA256,
        "disposition": RC0027_PARENT_DISPOSITION,
    }
    expected_flags = {
        "experimental_only": True,
        "runtime_connected": False,
        "eligible_for_e0b": False,
        "eligible_for_e2": False,
        "eligible_for_formal": False,
        "eligible_for_production": False,
    }
    if value.get("parent") != expected_parent:
        issues.add("RC0028_EXPERIMENT_PARENT_BINDING_INVALID")
    if value.get("flags") != expected_flags:
        issues.add("RC0028_EXPERIMENT_ELIGIBILITY_FLAGS_INVALID")
    if value.get("runtime_reverse_imports") != []:
        issues.add("RC0028_EXPERIMENT_RUNTIME_CONNECTED")
    if value.get("generated_manifest") != {
        "path": RC0028_GENERATED_MANIFEST_PATH,
        "included_in_file_hashes": False,
        "artifact_hash_authority": "external_body_free_receipt",
    }:
        issues.add("RC0028_EXPERIMENT_SELF_HASH_POLICY_INVALID")
    if value.get("added_or_changed_paths") != list(
        sorted(RC0028_EXPERIMENT_ADDED_OR_CHANGED_PATHS)
    ):
        issues.add("RC0028_EXPERIMENT_PATH_ALLOWLIST_INVALID")
    if value.get("allowed_experiment_entrypoint_paths") != list(
        sorted(RC0028_ALLOWED_EXPERIMENT_ENTRYPOINT_PATHS)
    ):
        issues.add("RC0028_EXPERIMENT_ENTRYPOINT_ALLOWLIST_INVALID")

    edges = value.get("experiment_import_edges")
    if type(edges) is not list:
        issues.add("RC0028_EXPERIMENT_IMPORT_GRAPH_INVALID")
    else:
        normalized_edges: list[tuple[str, str]] = []
        for edge in edges:
            if (
                type(edge) is not dict
                or set(edge) != {"importer_path", "imported_path"}
                or type(edge.get("importer_path")) is not str
                or type(edge.get("imported_path")) is not str
            ):
                issues.add("RC0028_EXPERIMENT_IMPORT_GRAPH_INVALID")
                continue
            importer_path = edge["importer_path"]
            imported_path = edge["imported_path"]
            normalized_edges.append((importer_path, imported_path))
            importer_rank = _SUCCESSOR_MODULE_RANK.get(
                Path(importer_path).stem
            )
            imported_rank = _SUCCESSOR_MODULE_RANK.get(
                Path(imported_path).stem
            )
            if (
                importer_rank is not None
                and imported_rank is not None
                and imported_rank >= importer_rank
            ):
                issues.add("RC0028_EXPERIMENT_IMPORT_DIRECTION_INVALID")
        if normalized_edges != sorted(set(normalized_edges)):
            issues.add("RC0028_EXPERIMENT_IMPORT_GRAPH_INVALID")

    try:
        files = _safe_file_rows(value.get("file_hashes"))
        changed = _safe_file_rows(value.get("added_or_changed_file_hashes"))
    except Rc0028ExperimentDependencyError:
        issues.add("RC0028_EXPERIMENT_FILE_ROWS_INVALID")
        files = []
        changed = []
    by_path = {row["path"]: row["sha256"] for row in files}
    changed_by_path = {row["path"]: row["sha256"] for row in changed}
    if (
        len(files)
        != RC0027_PARENT_SOURCE_FILE_COUNT
        + len(RC0028_EXPERIMENT_ADDED_OR_CHANGED_PATHS)
        or set(changed_by_path) != set(RC0028_EXPERIMENT_ADDED_OR_CHANGED_PATHS)
        or any(by_path.get(path) != sha for path, sha in changed_by_path.items())
        or RC0028_GENERATED_MANIFEST_PATH in by_path
    ):
        issues.add("RC0028_EXPERIMENT_FILE_CLOSURE_INVALID")
    if type(edges) is list and any(
        importer not in by_path or imported not in by_path
        for importer, imported in normalized_edges
    ):
        issues.add("RC0028_EXPERIMENT_IMPORT_GRAPH_INVALID")
    expected_predecessors = {
        "e1b_red_path": RC0028_E1B_PREDECESSOR_PATH,
        "e1b_red_sha256": RC0028_E1B_PREDECESSOR_SHA256,
        "v1_lexical_witness_path": RC0028_V1_LEXICAL_WITNESS_PATH,
        "v1_lexical_witness_sha256": RC0028_V1_LEXICAL_WITNESS_SHA256,
        "v1_experiment_snapshot_path": RC0028_V1_EXPERIMENT_SNAPSHOT_PATH,
        "v1_experiment_snapshot_sha256": (
            RC0028_V1_EXPERIMENT_SNAPSHOT_SHA256
        ),
    }
    if value.get("predecessors") != expected_predecessors:
        issues.add("RC0028_EXPERIMENT_PREDECESSOR_BINDING_INVALID")
    step9 = value.get("step9_baseline")
    expected_step9 = {
        "validation_status": "passed",
        "manifest_source_path": STEP9_MANIFEST_SOURCE_PATH,
        "manifest_source_sha256": STEP9_MANIFEST_SOURCE_SHA256,
        "manifest_artifact_sha256": STEP9_MANIFEST_ARTIFACT_SHA256,
        "direct_owner_file_hashes": [
            {"path": path, "sha256": sha256}
            for path, sha256 in zip(
                STEP9_DIRECT_OWNER_PATHS,
                STEP9_DIRECT_OWNER_SHA256,
                strict=True,
            )
        ],
    }
    if step9 != expected_step9:
        issues.add("RC0028_EXPERIMENT_STEP9_BINDING_INVALID")
    closure = value.get("source_dependency_closure_sha256")
    if type(closure) is not str or _SHA_RE.fullmatch(closure) is None:
        issues.add("RC0028_EXPERIMENT_CLOSURE_HASH_INVALID")
    else:
        material = {
            key: item
            for key, item in value.items()
            if key != "source_dependency_closure_sha256"
        }
        try:
            recomputed = artifact_sha256(material)
        except (RecursionError, TypeError, ValueError, UnicodeError):
            recomputed = None
        if recomputed != closure:
            issues.add("RC0028_EXPERIMENT_CLOSURE_HASH_MISMATCH")
    return tuple(sorted(issues))


def validate_rc0028_experiment_dependency_manifest(
    value: Any,
    *,
    parent_manifest: Mapping[str, Any],
    repo_root: Path,
) -> tuple[str, ...]:
    shape_issues = validate_rc0028_experiment_dependency_manifest_shape(value)
    if shape_issues:
        return shape_issues
    try:
        expected = build_rc0028_experiment_dependency_manifest(
            parent_manifest,
            repo_root=repo_root,
        )
    except (KeyError, OSError, TypeError, Rc0028ExperimentDependencyError):
        return ("RC0028_EXPERIMENT_DEPENDENCY_UNAVAILABLE_OR_DRIFTED",)
    if value != expected:
        return ("RC0028_EXPERIMENT_DEPENDENCY_RECOMPUTATION_MISMATCH",)
    return ()


__all__ = [
    "RC0027_PARENT_CANDIDATE_VERSION_ID",
    "RC0027_PARENT_DISPOSITION",
    "RC0027_PARENT_FIXTURE_PATH",
    "RC0027_PARENT_MANIFEST_ARTIFACT_SHA256",
    "RC0027_PARENT_SOURCE_CLOSURE_SHA256",
    "RC0027_PARENT_SOURCE_FILE_COUNT",
    "RC0028_ALLOWED_EXPERIMENT_ENTRYPOINT_PATHS",
    "RC0028_BASELINE_GIT_COMMIT",
    "RC0028_BASELINE_GIT_TREE",
    "RC0028_E1B_PREDECESSOR_PATH",
    "RC0028_E1B_PREDECESSOR_SHA256",
    "RC0028_EXPERIMENT_ADDED_OR_CHANGED_PATHS",
    "RC0028_EXPERIMENT_DEPENDENCY_MANIFEST_SCHEMA",
    "RC0028_EXPERIMENT_ID",
    "RC0028_EXPERIMENT_MANIFEST_OWNER_PATH",
    "RC0028_EXPERIMENT_MANIFEST_TOOL_PATH",
    "RC0028_GENERATED_MANIFEST_PATH",
    "RC0028_SUCCESSOR_SOURCE_PATHS",
    "Rc0028ExperimentDependencyError",
    "build_rc0028_experiment_dependency_manifest",
    "find_rc0028_unexpected_reverse_imports",
    "validate_rc0028_experiment_dependency_manifest",
    "validate_rc0028_experiment_dependency_manifest_shape",
]
