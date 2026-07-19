# -*- coding: utf-8 -*-
from __future__ import annotations

"""Exact, body-free dependency authority for the rc0028 downstream experiment.

The accepted E1b manifest is an immutable parent.  Filesystem discovery is
used only to reject unexpected rc0028 paths and forbidden reverse imports; it
can never admit a path into this closure.  The generated manifest fixture is
listed in the D0 allowlist but excluded from its own file-hash closure.
"""

import ast
import hashlib
from pathlib import Path
import re
from typing import Any, Mapping, Sequence

from emlis_ai_nls_v3_artifact_contract import artifact_sha256
from emlis_ai_rc0028_experiment_dependency_manifest_v3 import (
    RC0028_EXPERIMENT_ADDED_OR_CHANGED_PATHS,
    RC0028_EXPERIMENT_DEPENDENCY_MANIFEST_SCHEMA,
    RC0028_EXPERIMENT_SNAPSHOT_SUCCESSOR_PATH,
    validate_rc0028_experiment_dependency_manifest_shape,
)


RC0028_DOWNSTREAM_EXPERIMENT_DEPENDENCY_MANIFEST_SCHEMA = (
    "cocolon.emlis.nls_v3.rc0028_downstream_experiment_dependency_manifest.v1"
)
RC0028_DOWNSTREAM_EXPERIMENT_ID = (
    "nls_v3_rc0028_downstream_bounded_experiment"
)
RC0028_DOWNSTREAM_BASELINE_GIT_COMMIT = (
    "31d3cf183589b27481338277574f90500f3c5b11"
)
RC0028_DOWNSTREAM_BASELINE_GIT_TREE = (
    "c826c3ed5587356f313a90a5b67611e3972abd42"
)

RC0028_E1B_PARENT_MANIFEST_PATH = (
    "ai/tests/fixtures/emlis_nls_v3/cycle_001/"
    "cycle001_dependency_manifest_rc0028_experiment.json"
)
RC0028_E1B_PARENT_MANIFEST_ARTIFACT_SHA256 = (
    "e6a9b369afcc982f3413333bf91b3278cf64299462d25c037da19dc0013cd312"
)
RC0028_E1B_PARENT_SOURCE_CLOSURE_SHA256 = (
    "404d0338dd02e573aee0029be68ca72b1fb544d62bf0e34d655b73ce78227e1e"
)
RC0028_E1B_PARENT_FILE_HASHES_SHA256 = (
    "7cca57ae19853acdf30ff53fa76ff14185235bf32bff8cca18773684a5a89e88"
)
RC0028_E1B_PARENT_SOURCE_FILE_COUNT = 177

RC0028_DOWNSTREAM_LEXICALIZATION_PATH = (
    "ai/services/ai_inference/emlis_ai_step11_grounded_lexicalization_v3.py"
)
RC0028_DOWNSTREAM_SURFACE_PATH = (
    "ai/services/ai_inference/emlis_ai_step11_natural_surface_v3.py"
)
RC0028_DOWNSTREAM_MATCHER_PATH = (
    "ai/services/ai_inference/"
    "emlis_ai_step11_natural_surface_matcher_v3.py"
)
RC0028_DOWNSTREAM_HARD_GATE_PATH = (
    "ai/services/ai_inference/emlis_ai_step11_hard_gate_v3.py"
)

RC0028_DOWNSTREAM_MODIFIED_OWNER_HASHES = (
    {
        "path": RC0028_DOWNSTREAM_LEXICALIZATION_PATH,
        "predecessor_sha256": (
            "2207ce37b13dd98d13433721c259f9854c2e3e70d5dc579cf9661cab6c7a81aa"
        ),
        "current_sha256": (
            "cec416ee6f222aca6b63e0b355980adaadecc9abc03662272ce3ef745d7f5502"
        ),
    },
    {
        "path": RC0028_DOWNSTREAM_SURFACE_PATH,
        "predecessor_sha256": (
            "f397675a4cf88d94b40c5e4363f1ba182fe19c98becea546f06b564f43aa1ba9"
        ),
        "current_sha256": (
            "bb1d02f1e3eb20efb95cb9548798910ee7a9021c2ef174a50bec35029f4b1c4a"
        ),
    },
    {
        "path": RC0028_DOWNSTREAM_MATCHER_PATH,
        "predecessor_sha256": (
            "c9cacd3112f90f8f38fb7163a52ced248af78da2670459f7f418311a848f48b0"
        ),
        "current_sha256": (
            "88fbfb603bf8ae32ac1c4f049cfffe444744722c91a702ea56caacb79af90f6b"
        ),
    },
    {
        "path": RC0028_DOWNSTREAM_HARD_GATE_PATH,
        "predecessor_sha256": (
            "6e8000b58bb9679cec4c95519fec0154fa525649f1115e9f92fa4da74e26ebe9"
        ),
        "current_sha256": (
            "e73a9f148f115f17777cc12b6a21952990d5d7c481ff14b5033c89abba499f58"
        ),
    },
)
RC0028_DOWNSTREAM_MODIFIED_OWNER_PATHS = tuple(
    row["path"] for row in RC0028_DOWNSTREAM_MODIFIED_OWNER_HASHES
)

RC0028_DOWNSTREAM_RUNTIME_ADAPTER_PATH = (
    "ai/services/ai_inference/"
    "emlis_ai_step11_rc0028_experiment_runtime_adapter_v3.py"
)
RC0028_DOWNSTREAM_MANIFEST_OWNER_PATH = (
    "ai/services/ai_inference/"
    "emlis_ai_rc0028_downstream_experiment_dependency_manifest_v3.py"
)
RC0028_DOWNSTREAM_CATALOG_PATH = (
    "ai/services/ai_inference/"
    "emlis_ai_step11_rc0028_experiment_surface_catalog_v3.py"
)
RC0028_DOWNSTREAM_MANIFEST_TOOL_PATH = (
    "ai/tools/"
    "emlis_nls_v3_rc0028_downstream_experiment_dependency_manifest.py"
)
RC0028_DOWNSTREAM_BOUNDED_EXPERIMENT_TOOL_PATH = (
    "ai/tools/emlis_nls_v3_rc0028_bounded_experiment.py"
)
RC0028_DOWNSTREAM_REPRESENTATIVE_FIXTURE_PATH = (
    "ai/tests/fixtures/emlis_nls_v3/cycle_001/"
    "rc0028_representative8_body_free.json"
)
RC0028_DOWNSTREAM_GENERATED_MANIFEST_PATH = (
    "ai/tests/fixtures/emlis_nls_v3/cycle_001/"
    "cycle001_dependency_manifest_rc0028_downstream_experiment.json"
)

RC0028_DOWNSTREAM_E0B_RED_PATH = (
    "ai/tests/test_emlis_nls_v3_s11_rc0028_e0b_downstream_red.py"
)
RC0028_DOWNSTREAM_E0B_MUTATION_PATH = (
    "ai/tests/test_emlis_nls_v3_s11_rc0028_e0b_downstream_mutation.py"
)
RC0028_DOWNSTREAM_E0B_FROZEN_HASHES = (
    {
        "path": RC0028_DOWNSTREAM_E0B_RED_PATH,
        "sha256": (
            "df2f2ec7258f4a58d4e99b43fe412969c7d63503eb0a97100eb2790eaa82abb9"
        ),
    },
    {
        "path": RC0028_DOWNSTREAM_E0B_MUTATION_PATH,
        "sha256": (
            "39e7075ebe7cf3815f13c6e06639198d9702b98fa078546d0887f3d8856b9733"
        ),
    },
)

RC0028_DOWNSTREAM_NEW_PATH_ALLOWLIST = (
    RC0028_DOWNSTREAM_RUNTIME_ADAPTER_PATH,
    RC0028_DOWNSTREAM_MANIFEST_OWNER_PATH,
    RC0028_DOWNSTREAM_CATALOG_PATH,
    RC0028_DOWNSTREAM_MANIFEST_TOOL_PATH,
    RC0028_DOWNSTREAM_BOUNDED_EXPERIMENT_TOOL_PATH,
    RC0028_DOWNSTREAM_REPRESENTATIVE_FIXTURE_PATH,
    RC0028_DOWNSTREAM_GENERATED_MANIFEST_PATH,
    RC0028_DOWNSTREAM_E0B_RED_PATH,
    RC0028_DOWNSTREAM_E0B_MUTATION_PATH,
    "ai/tests/test_emlis_nls_v3_s11_rc0028_e2_downstream_integration.py",
    "ai/tests/"
    "test_emlis_nls_v3_s11_rc0028_e2_forward_inverse_independence.py",
    "ai/tests/test_emlis_nls_v3_s11_rc0028_e2_runtime_disconnect.py",
    "ai/tests/test_emlis_nls_v3_s11_rc0028_e3_representative8.py",
    "ai/tests/test_emlis_nls_v3_s11_rc0028_e4_frozen100_read_only.py",
    "ai/tests/"
    "test_emlis_nls_v3_s11_rc0028_downstream_dependency_closure.py",
    "ai/tests/"
    "test_emlis_nls_v3_s11_rc0028_rc0027_default_behavior_regression.py",
)
RC0028_DOWNSTREAM_HASHED_NEW_PATHS = tuple(
    path
    for path in RC0028_DOWNSTREAM_NEW_PATH_ALLOWLIST
    if path != RC0028_DOWNSTREAM_GENERATED_MANIFEST_PATH
)

RC0028_DOWNSTREAM_CATALOG_SHA256 = (
    "a8c64cc9955aec460238250d2d538e25e2bc44623d6cbf8118f6592a7d890af3"
)
RC0028_DOWNSTREAM_CATALOG_REQUIRED_ATOM_CODES = (
    "balanced_consideration",
    "choice_uncertainty",
    "comparative_assessment",
    "decision_timing",
    "explicit_coexistence",
    "explicit_contrast",
    "nonreduction_boundary",
    "ordered_sequence",
    "parallel_addition",
    "particle_object",
    "purpose_action",
    "reported_self_assessment",
    "withheld_action",
)

_AUTHORIZED_DYNAMIC_IMPORT_EDGES = (
    (
        RC0028_DOWNSTREAM_LEXICALIZATION_PATH,
        RC0028_EXPERIMENT_SNAPSHOT_SUCCESSOR_PATH,
    ),
    (
        RC0028_DOWNSTREAM_SURFACE_PATH,
        RC0028_EXPERIMENT_SNAPSHOT_SUCCESSOR_PATH,
    ),
    (
        RC0028_DOWNSTREAM_MATCHER_PATH,
        RC0028_EXPERIMENT_SNAPSHOT_SUCCESSOR_PATH,
    ),
    (
        RC0028_DOWNSTREAM_RUNTIME_ADAPTER_PATH,
        RC0028_EXPERIMENT_SNAPSHOT_SUCCESSOR_PATH,
    ),
)
_AUTHORIZED_SUPPORT_DYNAMIC_IMPORT_EDGES = (
    (
        "ai/tests/"
        "test_emlis_nls_v3_s11_rc0028_rc0027_default_behavior_regression.py",
        "ai/services/ai_inference/emlis_ai_step11_runtime_adapter_v3.py",
    ),
)

_FLAGS = {
    "experimental_only": True,
    "runtime_connected": False,
    "public_owner_unchanged": True,
    "rc0027_default_behavior_equivalent": True,
    "eligible_for_formal": False,
    "eligible_for_production": False,
}
_CANONICAL_REBUILD = {
    "algorithm": "artifact_sha256_without_source_dependency_closure_sha256",
    "file_order": "path_ascending",
    "filesystem_discovery_admission": False,
    "deterministic": True,
}
_GENERATED_MANIFEST_POLICY = {
    "path": RC0028_DOWNSTREAM_GENERATED_MANIFEST_PATH,
    "included_in_file_hashes": False,
    "included_in_new_file_hashes": False,
    "artifact_hash_authority": "external_body_free_receipt",
}
_OPTIONAL_CATALOG_DISPOSITION = {
    "path": RC0028_DOWNSTREAM_CATALOG_PATH,
    "present": True,
    "disposition": "CATALOG_REQUIRED",
    "sha256": RC0028_DOWNSTREAM_CATALOG_SHA256,
    "required_atom_codes": list(
        RC0028_DOWNSTREAM_CATALOG_REQUIRED_ATOM_CODES
    ),
}

_SHA_RE = re.compile(r"^[0-9a-f]{64}$")
_SAFE_PATH_RE = re.compile(r"^ai/[A-Za-z0-9_./-]+$")
_PROJECT_MODULE_PREFIXES = ("emlis_ai_", "emlis_nls_", "test_emlis_")


class Rc0028DownstreamExperimentDependencyError(ValueError):
    """Fail closed without exposing a source path or source body."""

    def __init__(self, code: str) -> None:
        if (
            type(code) is not str
            or re.fullmatch(r"RC0028_DOWNSTREAM_[A-Z0-9_]{2,95}", code)
            is None
        ):
            code = "RC0028_DOWNSTREAM_DEPENDENCY_REJECTED"
        self.code = code
        super().__init__(code)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _safe_file_rows(value: Any) -> list[dict[str, str]]:
    if type(value) is not list or not value:
        raise Rc0028DownstreamExperimentDependencyError(
            "RC0028_DOWNSTREAM_FILE_ROWS_REQUIRED"
        )
    rows: list[dict[str, str]] = []
    seen: set[str] = set()
    for item in value:
        if type(item) is not dict or set(item) != {"path", "sha256"}:
            raise Rc0028DownstreamExperimentDependencyError(
                "RC0028_DOWNSTREAM_FILE_ROW_SHAPE_INVALID"
            )
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
            raise Rc0028DownstreamExperimentDependencyError(
                "RC0028_DOWNSTREAM_FILE_ROW_INVALID"
            )
        seen.add(path)
        rows.append({"path": path, "sha256": sha256})
    if rows != sorted(rows, key=lambda row: row["path"]):
        raise Rc0028DownstreamExperimentDependencyError(
            "RC0028_DOWNSTREAM_FILE_ROWS_NOT_SORTED"
        )
    return rows


def _validated_parent_manifest(value: Any) -> dict[str, Any]:
    if type(value) is not dict:
        raise Rc0028DownstreamExperimentDependencyError(
            "RC0028_DOWNSTREAM_PARENT_MAPPING_REQUIRED"
        )
    if validate_rc0028_experiment_dependency_manifest_shape(value):
        raise Rc0028DownstreamExperimentDependencyError(
            "RC0028_DOWNSTREAM_PARENT_SHAPE_INVALID"
        )
    try:
        files = _safe_file_rows(value["file_hashes"])
    except (KeyError, TypeError) as error:
        raise Rc0028DownstreamExperimentDependencyError(
            "RC0028_DOWNSTREAM_PARENT_FILE_ROWS_INVALID"
        ) from error
    if (
        value.get("schema_version")
        != RC0028_EXPERIMENT_DEPENDENCY_MANIFEST_SCHEMA
        or artifact_sha256(value)
        != RC0028_E1B_PARENT_MANIFEST_ARTIFACT_SHA256
        or value.get("source_dependency_closure_sha256")
        != RC0028_E1B_PARENT_SOURCE_CLOSURE_SHA256
        or len(files) != RC0028_E1B_PARENT_SOURCE_FILE_COUNT
        or artifact_sha256(files)
        != RC0028_E1B_PARENT_FILE_HASHES_SHA256
        or value.get("baseline_git_commit")
        != RC0028_DOWNSTREAM_BASELINE_GIT_COMMIT
        or value.get("baseline_git_tree")
        != RC0028_DOWNSTREAM_BASELINE_GIT_TREE
    ):
        raise Rc0028DownstreamExperimentDependencyError(
            "RC0028_DOWNSTREAM_PARENT_BINDING_INVALID"
        )
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
            raise Rc0028DownstreamExperimentDependencyError(
                "RC0028_DOWNSTREAM_LOCAL_MODULE_NAME_COLLISION"
            )
        result[module] = path
    return result


class _ImportVisitor(ast.NodeVisitor):
    def __init__(self) -> None:
        self.static_modules: set[str] = set()
        self.dynamic_modules: list[tuple[str, bool, str]] = []
        self.function_depth = 0

    def visit_Import(self, node: ast.Import) -> None:
        self.static_modules.update(
            alias.name.split(".", 1)[0] for alias in node.names
        )

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        if node.module:
            self.static_modules.add(node.module.split(".", 1)[0])
        elif node.level:
            self.static_modules.update(
                alias.name.split(".", 1)[0] for alias in node.names
            )

    def _visit_function(self, node: ast.AST) -> None:
        self.function_depth += 1
        self.generic_visit(node)
        self.function_depth -= 1

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        self._visit_function(node)

    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        self._visit_function(node)

    def visit_Call(self, node: ast.Call) -> None:
        kind: str | None = None
        if isinstance(node.func, ast.Name) and node.func.id == "__import__":
            kind = "function_local_literal___import__"
        elif (
            isinstance(node.func, ast.Attribute)
            and node.func.attr == "import_module"
            and isinstance(node.func.value, ast.Name)
            and node.func.value.id == "importlib"
        ) or (
            isinstance(node.func, ast.Name)
            and node.func.id == "import_module"
        ):
            kind = "function_local_literal_import_module"
        if kind is not None:
            if (
                not node.args
                or not isinstance(node.args[0], ast.Constant)
                or type(node.args[0].value) is not str
            ):
                self.generic_visit(node)
                return
            module = node.args[0].value.split(".", 1)[0]
            self.dynamic_modules.append(
                (module, self.function_depth > 0, kind)
            )
        self.generic_visit(node)


def _source_imports(
    source: bytes,
) -> tuple[tuple[str, ...], tuple[tuple[str, bool, str], ...]]:
    try:
        tree = ast.parse(source)
    except (SyntaxError, UnicodeError) as error:
        raise Rc0028DownstreamExperimentDependencyError(
            "RC0028_DOWNSTREAM_SOURCE_AST_INVALID"
        ) from error
    visitor = _ImportVisitor()
    visitor.visit(tree)
    return (
        tuple(sorted(visitor.static_modules)),
        tuple(sorted(set(visitor.dynamic_modules))),
    )


def _is_project_module(module: str) -> bool:
    return module.startswith(_PROJECT_MODULE_PREFIXES)


def _downstream_import_edges(
    repo_root: Path,
    *,
    closure_paths: Sequence[str],
) -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    index = _module_index(closure_paths)
    static_edges: set[tuple[str, str]] = set()
    dynamic_edges: set[tuple[str, str, str]] = set()
    importer_paths = tuple(
        path
        for path in (
            *RC0028_DOWNSTREAM_MODIFIED_OWNER_PATHS,
            *RC0028_DOWNSTREAM_HASHED_NEW_PATHS,
        )
        if path.endswith(".py")
    )
    for importer_path in importer_paths:
        try:
            static_modules, dynamic_modules = _source_imports(
                (repo_root / importer_path).read_bytes()
            )
        except OSError as error:
            raise Rc0028DownstreamExperimentDependencyError(
                "RC0028_DOWNSTREAM_IMPORT_SOURCE_UNAVAILABLE"
            ) from error
        for module in static_modules:
            imported_path = index.get(module)
            if imported_path is not None:
                static_edges.add((importer_path, imported_path))
            elif _is_project_module(module):
                raise Rc0028DownstreamExperimentDependencyError(
                    "RC0028_DOWNSTREAM_UNBOUND_PROJECT_IMPORT"
                )
        for module, function_local, kind in dynamic_modules:
            imported_path = index.get(module)
            if imported_path is None:
                if _is_project_module(module):
                    raise Rc0028DownstreamExperimentDependencyError(
                        "RC0028_DOWNSTREAM_UNBOUND_DYNAMIC_PROJECT_IMPORT"
                    )
                continue
            edge = (importer_path, imported_path)
            if edge in _AUTHORIZED_SUPPORT_DYNAMIC_IMPORT_EDGES:
                continue
            if (
                not function_local
                or edge not in _AUTHORIZED_DYNAMIC_IMPORT_EDGES
            ):
                raise Rc0028DownstreamExperimentDependencyError(
                    "RC0028_DOWNSTREAM_DYNAMIC_IMPORT_EDGE_FORBIDDEN"
                )
            dynamic_edges.add((importer_path, imported_path, kind))
    if {
        (importer, imported)
        for importer, imported, _kind in dynamic_edges
    } != set(_AUTHORIZED_DYNAMIC_IMPORT_EDGES):
        raise Rc0028DownstreamExperimentDependencyError(
            "RC0028_DOWNSTREAM_DYNAMIC_IMPORT_EDGE_SET_INVALID"
        )
    return (
        [
            {"importer_path": importer, "imported_path": imported}
            for importer, imported in sorted(static_edges)
        ],
        [
            {
                "importer_path": importer,
                "imported_path": imported,
                "import_kind": kind,
            }
            for importer, imported, kind in sorted(dynamic_edges)
        ],
    )


def find_rc0028_downstream_unexpected_paths(
    repo_root: Path,
    *,
    parent_manifest: Mapping[str, Any],
) -> tuple[str, ...]:
    """Discover only to reject; never add a discovered path to the closure."""

    parent = _validated_parent_manifest(parent_manifest)
    known = {
        row["path"] for row in _safe_file_rows(parent["file_hashes"])
    }
    parent_generated = parent.get("generated_manifest")
    if type(parent_generated) is dict:
        path = parent_generated.get("path")
        if type(path) is str:
            known.add(path)
    known.update(RC0028_DOWNSTREAM_NEW_PATH_ALLOWLIST)
    found: list[str] = []
    roots_and_suffixes = (
        (repo_root / "ai/services", frozenset({".py"})),
        (repo_root / "ai/tools", frozenset({".py"})),
        (repo_root / "ai/tests", frozenset({".py", ".json"})),
    )
    for root, suffixes in roots_and_suffixes:
        for path in sorted(root.rglob("*")):
            if (
                not path.is_file()
                or path.suffix not in suffixes
                or "rc0028" not in path.name.lower()
            ):
                continue
            relative = path.relative_to(repo_root).as_posix()
            if relative not in known:
                found.append(relative)
    return tuple(sorted(set(found)))


def find_rc0028_downstream_unexpected_reverse_imports(
    repo_root: Path,
) -> tuple[str, ...]:
    """Reject shared/public owners that load downstream experiment modules."""

    forbidden_modules = frozenset(
        {
            Path(RC0028_EXPERIMENT_SNAPSHOT_SUCCESSOR_PATH).stem,
            "emlis_ai_grounded_lexical_role_witness_successor_v3",
            "emlis_ai_grounded_relation_construction_authority_successor_v3",
            Path(RC0028_DOWNSTREAM_RUNTIME_ADAPTER_PATH).stem,
            Path(RC0028_DOWNSTREAM_CATALOG_PATH).stem,
            Path(RC0028_DOWNSTREAM_MANIFEST_OWNER_PATH).stem,
        }
    )
    excluded_paths = set(RC0028_EXPERIMENT_ADDED_OR_CHANGED_PATHS) | set(
        RC0028_DOWNSTREAM_MODIFIED_OWNER_PATHS
    ) | set(RC0028_DOWNSTREAM_HASHED_NEW_PATHS)
    found: list[str] = []
    for root in (repo_root / "ai/services", repo_root / "ai/tools"):
        for path in sorted(root.rglob("*.py")):
            relative = path.relative_to(repo_root).as_posix()
            if relative in excluded_paths:
                continue
            try:
                static_modules, dynamic_modules = _source_imports(
                    path.read_bytes()
                )
            except OSError as error:
                raise Rc0028DownstreamExperimentDependencyError(
                    "RC0028_DOWNSTREAM_REVERSE_IMPORT_SCAN_UNAVAILABLE"
                ) from error
            imported = set(static_modules) | {
                module for module, _local, _kind in dynamic_modules
            }
            if imported & forbidden_modules:
                found.append(relative)
    return tuple(found)


def _parent_binding(parent: Mapping[str, Any]) -> dict[str, Any]:
    files = _safe_file_rows(parent["file_hashes"])
    return {
        "schema_version": RC0028_EXPERIMENT_DEPENDENCY_MANIFEST_SCHEMA,
        "manifest_path": RC0028_E1B_PARENT_MANIFEST_PATH,
        "manifest_artifact_sha256": (
            RC0028_E1B_PARENT_MANIFEST_ARTIFACT_SHA256
        ),
        "source_dependency_closure_sha256": (
            RC0028_E1B_PARENT_SOURCE_CLOSURE_SHA256
        ),
        "source_file_count": RC0028_E1B_PARENT_SOURCE_FILE_COUNT,
        "file_hashes_sha256": RC0028_E1B_PARENT_FILE_HASHES_SHA256,
        "file_hashes": files,
        "immutable": True,
    }


def build_rc0028_downstream_experiment_dependency_manifest(
    parent_manifest: Mapping[str, Any],
    *,
    repo_root: Path,
) -> dict[str, Any]:
    """Build only the exact D0 allowlist over the immutable E1b parent."""

    parent = _validated_parent_manifest(parent_manifest)
    parent_files = _safe_file_rows(parent["file_hashes"])
    parent_by_path = {row["path"]: row["sha256"] for row in parent_files}
    modified_by_path = {
        row["path"]: row for row in RC0028_DOWNSTREAM_MODIFIED_OWNER_HASHES
    }
    if set(modified_by_path) != set(RC0028_DOWNSTREAM_MODIFIED_OWNER_PATHS):
        raise Rc0028DownstreamExperimentDependencyError(
            "RC0028_DOWNSTREAM_MODIFIED_OWNER_LEDGER_INVALID"
        )
    if any(path not in parent_by_path for path in modified_by_path):
        raise Rc0028DownstreamExperimentDependencyError(
            "RC0028_DOWNSTREAM_MODIFIED_OWNER_NOT_IN_PARENT"
        )
    if any(path in parent_by_path for path in RC0028_DOWNSTREAM_HASHED_NEW_PATHS):
        raise Rc0028DownstreamExperimentDependencyError(
            "RC0028_DOWNSTREAM_NEW_PATH_ALREADY_IN_PARENT"
        )
    if RC0028_DOWNSTREAM_GENERATED_MANIFEST_PATH in parent_by_path:
        raise Rc0028DownstreamExperimentDependencyError(
            "RC0028_DOWNSTREAM_GENERATED_SELF_HASH_IN_PARENT"
        )

    current_parent_rows: list[dict[str, str]] = []
    modified_rows: list[dict[str, str]] = []
    for row in parent_files:
        path = row["path"]
        modified = modified_by_path.get(path)
        if modified is None:
            try:
                current_sha256 = _sha256(repo_root / path)
            except OSError as error:
                raise Rc0028DownstreamExperimentDependencyError(
                    "RC0028_DOWNSTREAM_PARENT_SOURCE_UNAVAILABLE"
                ) from error
            if current_sha256 != row["sha256"]:
                raise Rc0028DownstreamExperimentDependencyError(
                    "RC0028_DOWNSTREAM_IMMUTABLE_PARENT_SOURCE_DRIFT"
                )
        else:
            if row["sha256"] != modified["predecessor_sha256"]:
                raise Rc0028DownstreamExperimentDependencyError(
                    "RC0028_DOWNSTREAM_MODIFIED_PREDECESSOR_MISMATCH"
                )
            try:
                current_sha256 = _sha256(repo_root / path)
            except OSError as error:
                raise Rc0028DownstreamExperimentDependencyError(
                    "RC0028_DOWNSTREAM_MODIFIED_OWNER_UNAVAILABLE"
                ) from error
            if current_sha256 != modified["current_sha256"]:
                raise Rc0028DownstreamExperimentDependencyError(
                    "RC0028_DOWNSTREAM_MODIFIED_OWNER_DRIFT"
                )
            modified_rows.append(dict(modified))
        current_parent_rows.append({"path": path, "sha256": current_sha256})

    new_rows: list[dict[str, str]] = []
    for path in RC0028_DOWNSTREAM_HASHED_NEW_PATHS:
        try:
            sha256 = _sha256(repo_root / path)
        except OSError as error:
            raise Rc0028DownstreamExperimentDependencyError(
                "RC0028_DOWNSTREAM_ALLOWLIST_PATH_MISSING"
            ) from error
        new_rows.append({"path": path, "sha256": sha256})
    new_rows.sort(key=lambda row: row["path"])
    new_by_path = {row["path"]: row["sha256"] for row in new_rows}
    if new_by_path.get(RC0028_DOWNSTREAM_CATALOG_PATH) != (
        RC0028_DOWNSTREAM_CATALOG_SHA256
    ):
        raise Rc0028DownstreamExperimentDependencyError(
            "RC0028_DOWNSTREAM_CATALOG_DRIFT"
        )
    for frozen in RC0028_DOWNSTREAM_E0B_FROZEN_HASHES:
        if new_by_path.get(frozen["path"]) != frozen["sha256"]:
            raise Rc0028DownstreamExperimentDependencyError(
                "RC0028_DOWNSTREAM_E0B_PREDECESSOR_DRIFT"
            )

    unexpected = find_rc0028_downstream_unexpected_paths(
        repo_root,
        parent_manifest=parent,
    )
    if unexpected:
        raise Rc0028DownstreamExperimentDependencyError(
            "RC0028_DOWNSTREAM_UNEXPECTED_PATH"
        )
    reverse_imports = find_rc0028_downstream_unexpected_reverse_imports(
        repo_root
    )
    if reverse_imports:
        raise Rc0028DownstreamExperimentDependencyError(
            "RC0028_DOWNSTREAM_FORBIDDEN_REVERSE_IMPORT"
        )

    files = sorted(
        current_parent_rows + new_rows,
        key=lambda row: row["path"],
    )
    static_edges, dynamic_edges = _downstream_import_edges(
        repo_root,
        closure_paths=[row["path"] for row in files],
    )
    material: dict[str, Any] = {
        "schema_version": (
            RC0028_DOWNSTREAM_EXPERIMENT_DEPENDENCY_MANIFEST_SCHEMA
        ),
        "experiment_id": RC0028_DOWNSTREAM_EXPERIMENT_ID,
        "baseline_git_commit": RC0028_DOWNSTREAM_BASELINE_GIT_COMMIT,
        "baseline_git_tree": RC0028_DOWNSTREAM_BASELINE_GIT_TREE,
        "parent": _parent_binding(parent),
        "modified_owner_file_hashes": sorted(
            modified_rows,
            key=lambda row: row["path"],
        ),
        "new_path_allowlist": list(
            sorted(RC0028_DOWNSTREAM_NEW_PATH_ALLOWLIST)
        ),
        "new_file_hashes": new_rows,
        "e0b_red_predecessors": [
            dict(row)
            for row in sorted(
                RC0028_DOWNSTREAM_E0B_FROZEN_HASHES,
                key=lambda row: row["path"],
            )
        ],
        "optional_catalog": dict(_OPTIONAL_CATALOG_DISPOSITION),
        "generated_manifest": dict(_GENERATED_MANIFEST_POLICY),
        "flags": dict(_FLAGS),
        "canonical_rebuild": dict(_CANONICAL_REBUILD),
        "source_file_count": len(files),
        "file_hashes": files,
        "static_project_import_edges": static_edges,
        "dynamic_project_import_edges": dynamic_edges,
        "unexpected_paths": [],
        "unbound_project_imports": [],
        "forbidden_reverse_imports": [],
        "body_free": True,
    }
    return {
        **material,
        "source_dependency_closure_sha256": artifact_sha256(material),
    }


def _normalized_edges(
    value: Any,
    *,
    dynamic: bool,
) -> tuple[tuple[str, ...], ...] | None:
    if type(value) is not list:
        return None
    expected_keys = (
        {"importer_path", "imported_path", "import_kind"}
        if dynamic
        else {"importer_path", "imported_path"}
    )
    rows: list[tuple[str, ...]] = []
    for item in value:
        if type(item) is not dict or set(item) != expected_keys:
            return None
        values = (
            item.get("importer_path"),
            item.get("imported_path"),
            *([item.get("import_kind")] if dynamic else []),
        )
        if any(type(part) is not str or not part for part in values):
            return None
        rows.append(values)
    normalized = tuple(rows)
    if normalized != tuple(sorted(set(normalized))):
        return None
    return normalized


def validate_rc0028_downstream_experiment_dependency_manifest_shape(
    value: Any,
) -> tuple[str, ...]:
    """Validate exact fields and canonical commitments without filesystem I/O."""

    if type(value) is not dict:
        return ("RC0028_DOWNSTREAM_MANIFEST_MAPPING_REQUIRED",)
    expected_keys = {
        "schema_version",
        "experiment_id",
        "baseline_git_commit",
        "baseline_git_tree",
        "parent",
        "modified_owner_file_hashes",
        "new_path_allowlist",
        "new_file_hashes",
        "e0b_red_predecessors",
        "optional_catalog",
        "generated_manifest",
        "flags",
        "canonical_rebuild",
        "source_file_count",
        "file_hashes",
        "static_project_import_edges",
        "dynamic_project_import_edges",
        "unexpected_paths",
        "unbound_project_imports",
        "forbidden_reverse_imports",
        "body_free",
        "source_dependency_closure_sha256",
    }
    issues: set[str] = set()
    if set(value) != expected_keys:
        issues.add("RC0028_DOWNSTREAM_MANIFEST_SHAPE_INVALID")
    if (
        value.get("schema_version")
        != RC0028_DOWNSTREAM_EXPERIMENT_DEPENDENCY_MANIFEST_SCHEMA
        or value.get("experiment_id") != RC0028_DOWNSTREAM_EXPERIMENT_ID
        or value.get("baseline_git_commit")
        != RC0028_DOWNSTREAM_BASELINE_GIT_COMMIT
        or value.get("baseline_git_tree")
        != RC0028_DOWNSTREAM_BASELINE_GIT_TREE
        or value.get("body_free") is not True
    ):
        issues.add("RC0028_DOWNSTREAM_MANIFEST_IDENTITY_INVALID")
    if value.get("flags") != _FLAGS:
        issues.add("RC0028_DOWNSTREAM_FLAGS_INVALID")
    if value.get("canonical_rebuild") != _CANONICAL_REBUILD:
        issues.add("RC0028_DOWNSTREAM_CANONICAL_REBUILD_INVALID")
    if value.get("generated_manifest") != _GENERATED_MANIFEST_POLICY:
        issues.add("RC0028_DOWNSTREAM_SELF_HASH_POLICY_INVALID")
    if value.get("optional_catalog") != _OPTIONAL_CATALOG_DISPOSITION:
        issues.add("RC0028_DOWNSTREAM_CATALOG_DISPOSITION_INVALID")
    if value.get("new_path_allowlist") != list(
        sorted(RC0028_DOWNSTREAM_NEW_PATH_ALLOWLIST)
    ):
        issues.add("RC0028_DOWNSTREAM_PATH_ALLOWLIST_INVALID")
    expected_modified = sorted(
        (dict(row) for row in RC0028_DOWNSTREAM_MODIFIED_OWNER_HASHES),
        key=lambda row: row["path"],
    )
    if value.get("modified_owner_file_hashes") != expected_modified:
        issues.add("RC0028_DOWNSTREAM_MODIFIED_OWNER_HASHES_INVALID")
    expected_e0b = [
        dict(row)
        for row in sorted(
            RC0028_DOWNSTREAM_E0B_FROZEN_HASHES,
            key=lambda row: row["path"],
        )
    ]
    if value.get("e0b_red_predecessors") != expected_e0b:
        issues.add("RC0028_DOWNSTREAM_E0B_BINDING_INVALID")

    parent = value.get("parent")
    parent_files: list[dict[str, str]] = []
    if type(parent) is not dict:
        issues.add("RC0028_DOWNSTREAM_PARENT_BINDING_INVALID")
    else:
        try:
            parent_files = _safe_file_rows(parent.get("file_hashes"))
        except Rc0028DownstreamExperimentDependencyError:
            issues.add("RC0028_DOWNSTREAM_PARENT_FILE_ROWS_INVALID")
        expected_parent_keys = {
            "schema_version",
            "manifest_path",
            "manifest_artifact_sha256",
            "source_dependency_closure_sha256",
            "source_file_count",
            "file_hashes_sha256",
            "file_hashes",
            "immutable",
        }
        if (
            set(parent) != expected_parent_keys
            or parent.get("schema_version")
            != RC0028_EXPERIMENT_DEPENDENCY_MANIFEST_SCHEMA
            or parent.get("manifest_path")
            != RC0028_E1B_PARENT_MANIFEST_PATH
            or parent.get("manifest_artifact_sha256")
            != RC0028_E1B_PARENT_MANIFEST_ARTIFACT_SHA256
            or parent.get("source_dependency_closure_sha256")
            != RC0028_E1B_PARENT_SOURCE_CLOSURE_SHA256
            or parent.get("source_file_count")
            != RC0028_E1B_PARENT_SOURCE_FILE_COUNT
            or parent.get("file_hashes_sha256")
            != RC0028_E1B_PARENT_FILE_HASHES_SHA256
            or parent.get("immutable") is not True
            or len(parent_files) != RC0028_E1B_PARENT_SOURCE_FILE_COUNT
            or (
                parent_files
                and artifact_sha256(parent_files)
                != RC0028_E1B_PARENT_FILE_HASHES_SHA256
            )
        ):
            issues.add("RC0028_DOWNSTREAM_PARENT_BINDING_INVALID")

    try:
        files = _safe_file_rows(value.get("file_hashes"))
        new_files = _safe_file_rows(value.get("new_file_hashes"))
    except Rc0028DownstreamExperimentDependencyError:
        issues.add("RC0028_DOWNSTREAM_FILE_ROWS_INVALID")
        files = []
        new_files = []
    by_path = {row["path"]: row["sha256"] for row in files}
    new_by_path = {row["path"]: row["sha256"] for row in new_files}
    parent_by_path = {
        row["path"]: row["sha256"] for row in parent_files
    }
    current_modified = {
        row["path"]: row["current_sha256"]
        for row in RC0028_DOWNSTREAM_MODIFIED_OWNER_HASHES
    }
    expected_file_count = (
        RC0028_E1B_PARENT_SOURCE_FILE_COUNT
        + len(RC0028_DOWNSTREAM_HASHED_NEW_PATHS)
    )
    if (
        value.get("source_file_count") != expected_file_count
        or len(files) != expected_file_count
        or set(new_by_path) != set(RC0028_DOWNSTREAM_HASHED_NEW_PATHS)
        or any(by_path.get(path) != sha for path, sha in new_by_path.items())
        or any(
            by_path.get(path)
            != current_modified.get(path, predecessor_sha)
            for path, predecessor_sha in parent_by_path.items()
        )
        or RC0028_DOWNSTREAM_GENERATED_MANIFEST_PATH in by_path
        or RC0028_DOWNSTREAM_GENERATED_MANIFEST_PATH in new_by_path
    ):
        issues.add("RC0028_DOWNSTREAM_FILE_CLOSURE_INVALID")
    if (
        new_by_path.get(RC0028_DOWNSTREAM_CATALOG_PATH)
        != RC0028_DOWNSTREAM_CATALOG_SHA256
        or any(
            new_by_path.get(row["path"]) != row["sha256"]
            for row in RC0028_DOWNSTREAM_E0B_FROZEN_HASHES
        )
    ):
        issues.add("RC0028_DOWNSTREAM_FROZEN_NEW_HASH_INVALID")

    static_edges = _normalized_edges(
        value.get("static_project_import_edges"),
        dynamic=False,
    )
    dynamic_edges = _normalized_edges(
        value.get("dynamic_project_import_edges"),
        dynamic=True,
    )
    if static_edges is None:
        issues.add("RC0028_DOWNSTREAM_STATIC_IMPORT_GRAPH_INVALID")
    elif any(
        importer not in by_path or imported not in by_path
        for importer, imported in static_edges
    ):
        issues.add("RC0028_DOWNSTREAM_STATIC_IMPORT_GRAPH_INVALID")
    expected_dynamic = tuple(
        sorted(
            (
                importer,
                imported,
                "function_local_literal___import__",
            )
            for importer, imported in _AUTHORIZED_DYNAMIC_IMPORT_EDGES
        )
    )
    if dynamic_edges != expected_dynamic:
        issues.add("RC0028_DOWNSTREAM_DYNAMIC_IMPORT_GRAPH_INVALID")
    if (
        value.get("unexpected_paths") != []
        or value.get("unbound_project_imports") != []
        or value.get("forbidden_reverse_imports") != []
    ):
        issues.add("RC0028_DOWNSTREAM_ZERO_AUDIT_INVALID")

    closure = value.get("source_dependency_closure_sha256")
    if type(closure) is not str or _SHA_RE.fullmatch(closure) is None:
        issues.add("RC0028_DOWNSTREAM_CLOSURE_HASH_INVALID")
    else:
        material = {
            key: item
            for key, item in value.items()
            if key != "source_dependency_closure_sha256"
        }
        try:
            recomputed = artifact_sha256(material)
        except (RecursionError, TypeError, UnicodeError, ValueError):
            recomputed = None
        if recomputed != closure:
            issues.add("RC0028_DOWNSTREAM_CLOSURE_HASH_MISMATCH")
    return tuple(sorted(issues))


def validate_rc0028_downstream_experiment_dependency_manifest(
    value: Any,
    *,
    parent_manifest: Mapping[str, Any],
    repo_root: Path,
) -> tuple[str, ...]:
    shape_issues = (
        validate_rc0028_downstream_experiment_dependency_manifest_shape(
            value
        )
    )
    if shape_issues:
        return shape_issues
    try:
        expected = build_rc0028_downstream_experiment_dependency_manifest(
            parent_manifest,
            repo_root=repo_root,
        )
    except (
        KeyError,
        OSError,
        TypeError,
        Rc0028DownstreamExperimentDependencyError,
    ):
        return ("RC0028_DOWNSTREAM_DEPENDENCY_UNAVAILABLE_OR_DRIFTED",)
    if value != expected:
        return ("RC0028_DOWNSTREAM_DEPENDENCY_RECOMPUTATION_MISMATCH",)
    return ()


__all__ = [
    "RC0028_DOWNSTREAM_BASELINE_GIT_COMMIT",
    "RC0028_DOWNSTREAM_BASELINE_GIT_TREE",
    "RC0028_DOWNSTREAM_CATALOG_PATH",
    "RC0028_DOWNSTREAM_CATALOG_REQUIRED_ATOM_CODES",
    "RC0028_DOWNSTREAM_E0B_FROZEN_HASHES",
    "RC0028_DOWNSTREAM_EXPERIMENT_DEPENDENCY_MANIFEST_SCHEMA",
    "RC0028_DOWNSTREAM_EXPERIMENT_ID",
    "RC0028_DOWNSTREAM_GENERATED_MANIFEST_PATH",
    "RC0028_DOWNSTREAM_HASHED_NEW_PATHS",
    "RC0028_DOWNSTREAM_MANIFEST_OWNER_PATH",
    "RC0028_DOWNSTREAM_MANIFEST_TOOL_PATH",
    "RC0028_DOWNSTREAM_MODIFIED_OWNER_HASHES",
    "RC0028_DOWNSTREAM_MODIFIED_OWNER_PATHS",
    "RC0028_DOWNSTREAM_NEW_PATH_ALLOWLIST",
    "RC0028_E1B_PARENT_MANIFEST_ARTIFACT_SHA256",
    "RC0028_E1B_PARENT_MANIFEST_PATH",
    "RC0028_E1B_PARENT_SOURCE_CLOSURE_SHA256",
    "Rc0028DownstreamExperimentDependencyError",
    "build_rc0028_downstream_experiment_dependency_manifest",
    "find_rc0028_downstream_unexpected_paths",
    "find_rc0028_downstream_unexpected_reverse_imports",
    "validate_rc0028_downstream_experiment_dependency_manifest",
    "validate_rc0028_downstream_experiment_dependency_manifest_shape",
]
