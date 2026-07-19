# -*- coding: utf-8 -*-
from __future__ import annotations

"""Exact dependency authority for the disconnected rc0029 repair lane.

The rc0028 downstream manifest is an immutable logical parent.  This module
accounts only for the four append-only downstream owners and the exact rc0029
allowlist.  Filesystem discovery is rejection-only and cannot admit a path.
"""

import ast
import hashlib
from pathlib import Path
import re
from typing import Any, Mapping, Sequence

from emlis_ai_nls_v3_artifact_contract import artifact_sha256
from emlis_ai_rc0028_downstream_experiment_dependency_manifest_v3 import (
    RC0028_DOWNSTREAM_EXPERIMENT_DEPENDENCY_MANIFEST_SCHEMA,
    validate_rc0028_downstream_experiment_dependency_manifest_shape,
)


RC0029_SURFACE_REPAIR_DEPENDENCY_MANIFEST_SCHEMA = (
    "cocolon.emlis.nls_v3."
    "rc0029_surface_repair_experiment_dependency_manifest.v1"
)
RC0029_SURFACE_REPAIR_EXPERIMENT_ID = (
    "nls_v3_rc0029_e3_common_surface_repair_experiment"
)
RC0029_BASELINE_GIT_COMMIT = (
    "e069ffd782e4d2b960b2c1e770d9018ab78a8b1d"
)
RC0029_BASELINE_GIT_TREE = "f03ee376581c6611467690c296140a7ccdc9e23d"

RC0028_DOWNSTREAM_PARENT_MANIFEST_PATH = (
    "ai/tests/fixtures/emlis_nls_v3/cycle_001/"
    "cycle001_dependency_manifest_rc0028_downstream_experiment.json"
)
RC0028_DOWNSTREAM_PARENT_MANIFEST_FILE_SHA256 = (
    "ffe0ff52e7d875e430d0878dced96c7b8994b05e6366ed9b4ff70055e8f2e8d0"
)
RC0028_DOWNSTREAM_PARENT_MANIFEST_ARTIFACT_SHA256 = (
    "7b3adafdbe6c21348e9dd74d8cd5ef84a8139aa616e3f8ae5e1dcbfb1b788c11"
)
RC0028_DOWNSTREAM_PARENT_SOURCE_CLOSURE_SHA256 = (
    "08a83e30954055facdb711e1253a81145101e565afde4327567f239169f2d942"
)
RC0028_DOWNSTREAM_PARENT_FILE_HASHES_SHA256 = (
    "f2f89b85cb92d70408b9c80d26a4cad3fd3f13ab375d9bc77c164bac5ac61025"
)
RC0028_DOWNSTREAM_PARENT_SOURCE_FILE_COUNT = 192

RC0029_LEXICALIZATION_PATH = (
    "ai/services/ai_inference/emlis_ai_step11_grounded_lexicalization_v3.py"
)
RC0029_SURFACE_PATH = (
    "ai/services/ai_inference/emlis_ai_step11_natural_surface_v3.py"
)
RC0029_MATCHER_PATH = (
    "ai/services/ai_inference/"
    "emlis_ai_step11_natural_surface_matcher_v3.py"
)
RC0029_HARD_GATE_PATH = (
    "ai/services/ai_inference/emlis_ai_step11_hard_gate_v3.py"
)

# e069ffd bytes are a strict prefix of each rc0029 owner.  The size makes the
# prefix check independent from git and prevents a rewrite followed by append.
RC0029_MODIFIED_OWNER_PREDECESSORS = (
    {
        "path": RC0029_LEXICALIZATION_PATH,
        "predecessor_size": 83815,
        "predecessor_sha256": (
            "cec416ee6f222aca6b63e0b355980adaadecc9abc03662272ce3ef745d7f5502"
        ),
    },
    {
        "path": RC0029_SURFACE_PATH,
        "predecessor_size": 250254,
        "predecessor_sha256": (
            "bb1d02f1e3eb20efb95cb9548798910ee7a9021c2ef174a50bec35029f4b1c4a"
        ),
    },
    {
        "path": RC0029_MATCHER_PATH,
        "predecessor_size": 459458,
        "predecessor_sha256": (
            "88fbfb603bf8ae32ac1c4f049cfffe444744722c91a702ea56caacb79af90f6b"
        ),
    },
    {
        "path": RC0029_HARD_GATE_PATH,
        "predecessor_size": 103729,
        "predecessor_sha256": (
            "e73a9f148f115f17777cc12b6a21952990d5d7c481ff14b5033c89abba499f58"
        ),
    },
)
RC0029_MODIFIED_OWNER_PATHS = tuple(
    row["path"] for row in RC0029_MODIFIED_OWNER_PREDECESSORS
)

RC0029_CATALOG_PATH = (
    "ai/services/ai_inference/"
    "emlis_ai_step11_rc0029_experiment_surface_catalog_v3.py"
)
RC0029_RUNTIME_ADAPTER_PATH = (
    "ai/services/ai_inference/"
    "emlis_ai_step11_rc0029_experiment_runtime_adapter_v3.py"
)
RC0029_MANIFEST_OWNER_PATH = (
    "ai/services/ai_inference/"
    "emlis_ai_rc0029_surface_repair_experiment_dependency_manifest_v3.py"
)
RC0029_MANIFEST_TOOL_PATH = (
    "ai/tools/emlis_nls_v3_rc0029_surface_repair_dependency_manifest.py"
)
RC0029_BOUNDED_EXPERIMENT_TOOL_PATH = (
    "ai/tools/emlis_nls_v3_rc0029_surface_repair_bounded_experiment.py"
)
RC0029_GENERATED_MANIFEST_PATH = (
    "ai/tests/fixtures/emlis_nls_v3/cycle_001/"
    "cycle001_dependency_manifest_rc0029_surface_repair_experiment.json"
)
RC0029_REPRESENTATIVE_FIXTURE_PATH = (
    "ai/tests/fixtures/emlis_nls_v3/cycle_001/"
    "rc0029_representative8_body_free.json"
)

RC0029_NEW_PATH_ALLOWLIST = (
    RC0029_CATALOG_PATH,
    RC0029_RUNTIME_ADAPTER_PATH,
    RC0029_MANIFEST_OWNER_PATH,
    RC0029_MANIFEST_TOOL_PATH,
    RC0029_BOUNDED_EXPERIMENT_TOOL_PATH,
    RC0029_GENERATED_MANIFEST_PATH,
    RC0029_REPRESENTATIVE_FIXTURE_PATH,
    "ai/tests/test_emlis_nls_v3_s11_rc0029_surface_repair_red.py",
    "ai/tests/test_emlis_nls_v3_s11_rc0029_surface_repair_mutation.py",
    "ai/tests/test_emlis_nls_v3_s11_rc0029_e2_integration.py",
    "ai/tests/test_emlis_nls_v3_s11_rc0029_forward_inverse_independence.py",
    "ai/tests/test_emlis_nls_v3_s11_rc0029_runtime_disconnect.py",
    "ai/tests/test_emlis_nls_v3_s11_rc0029_predecessor_immutability.py",
    "ai/tests/test_emlis_nls_v3_s11_rc0029_e3_representative8.py",
    "ai/tests/test_emlis_nls_v3_s11_rc0029_e4_frozen100_read_only.py",
    "ai/tests/test_emlis_nls_v3_s11_rc0029_dependency_closure.py",
    "ai/tests/"
    "test_emlis_nls_v3_s11_rc0029_rc0027_default_behavior_regression.py",
    "ai/tests/"
    "test_emlis_nls_v3_s11_rc0029_rc0028_experiment_regression.py",
)
RC0029_HASHED_NEW_PATHS = tuple(
    path
    for path in RC0029_NEW_PATH_ALLOWLIST
    if path != RC0029_GENERATED_MANIFEST_PATH
)

_FLAGS = {
    "experimental_only": True,
    "runtime_connected": False,
    "public_owner_unchanged": True,
    "rc0027_default_behavior_equivalent": True,
    "rc0028_experiment_behavior_equivalent": True,
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
    "path": RC0029_GENERATED_MANIFEST_PATH,
    "included_in_file_hashes": False,
    "included_in_new_file_hashes": False,
    "artifact_hash_authority": "external_body_free_receipt",
}

_SHA_RE = re.compile(r"^[0-9a-f]{64}$")
_SAFE_PATH_RE = re.compile(r"^ai/[A-Za-z0-9_./-]+$")
_PROJECT_MODULE_PREFIXES = ("emlis_ai_", "emlis_nls_", "test_emlis_")


class Rc0029SurfaceRepairDependencyError(ValueError):
    """Fail closed without including source paths or bodies in the code."""

    def __init__(self, code: str) -> None:
        if (
            type(code) is not str
            or re.fullmatch(r"RC0029_[A-Z0-9_]{2,110}", code) is None
        ):
            code = "RC0029_SURFACE_REPAIR_DEPENDENCY_REJECTED"
        self.code = code
        super().__init__(code)


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _sha256(path: Path) -> str:
    return _sha256_bytes(path.read_bytes())


def _safe_file_rows(value: Any) -> list[dict[str, str]]:
    if type(value) is not list or not value:
        raise Rc0029SurfaceRepairDependencyError(
            "RC0029_FILE_ROWS_REQUIRED"
        )
    rows: list[dict[str, str]] = []
    seen: set[str] = set()
    for item in value:
        if type(item) is not dict or set(item) != {"path", "sha256"}:
            raise Rc0029SurfaceRepairDependencyError(
                "RC0029_FILE_ROW_SHAPE_INVALID"
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
            raise Rc0029SurfaceRepairDependencyError(
                "RC0029_FILE_ROW_INVALID"
            )
        seen.add(path)
        rows.append({"path": path, "sha256": sha256})
    if rows != sorted(rows, key=lambda row: row["path"]):
        raise Rc0029SurfaceRepairDependencyError(
            "RC0029_FILE_ROWS_NOT_SORTED"
        )
    return rows


def _validated_parent_manifest(value: Any) -> dict[str, Any]:
    if type(value) is not dict:
        raise Rc0029SurfaceRepairDependencyError(
            "RC0029_PARENT_MAPPING_REQUIRED"
        )
    if validate_rc0028_downstream_experiment_dependency_manifest_shape(value):
        raise Rc0029SurfaceRepairDependencyError(
            "RC0029_PARENT_SHAPE_INVALID"
        )
    try:
        files = _safe_file_rows(value["file_hashes"])
    except (KeyError, TypeError) as error:
        raise Rc0029SurfaceRepairDependencyError(
            "RC0029_PARENT_FILE_ROWS_INVALID"
        ) from error
    if (
        value.get("schema_version")
        != RC0028_DOWNSTREAM_EXPERIMENT_DEPENDENCY_MANIFEST_SCHEMA
        or artifact_sha256(value)
        != RC0028_DOWNSTREAM_PARENT_MANIFEST_ARTIFACT_SHA256
        or value.get("source_dependency_closure_sha256")
        != RC0028_DOWNSTREAM_PARENT_SOURCE_CLOSURE_SHA256
        or len(files) != RC0028_DOWNSTREAM_PARENT_SOURCE_FILE_COUNT
        or artifact_sha256(files)
        != RC0028_DOWNSTREAM_PARENT_FILE_HASHES_SHA256
    ):
        raise Rc0029SurfaceRepairDependencyError(
            "RC0029_PARENT_BINDING_INVALID"
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
            raise Rc0029SurfaceRepairDependencyError(
                "RC0029_LOCAL_MODULE_NAME_COLLISION"
            )
        result[module] = path
    return result


class _ImportVisitor(ast.NodeVisitor):
    def __init__(self, literal_strings: Mapping[str, str]) -> None:
        self.static_modules: set[str] = set()
        self.module_scope_static_modules: set[str] = set()
        self.dynamic_modules: list[tuple[str, bool, str]] = []
        self.function_depth = 0
        self.literal_strings = dict(literal_strings)

    def visit_Import(self, node: ast.Import) -> None:
        modules = {alias.name.split(".", 1)[0] for alias in node.names}
        self.static_modules.update(modules)
        if self.function_depth == 0:
            self.module_scope_static_modules.update(modules)

    def visit_ImportFrom(self, node: ast.ImportFrom) -> None:
        modules: set[str] = set()
        if node.module:
            modules.add(node.module.split(".", 1)[0])
        elif node.level:
            modules.update(
                alias.name.split(".", 1)[0] for alias in node.names
            )
        self.static_modules.update(modules)
        if self.function_depth == 0:
            self.module_scope_static_modules.update(modules)

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
        if kind is not None and node.args:
            first = node.args[0]
            value: str | None = None
            if isinstance(first, ast.Constant) and type(first.value) is str:
                value = first.value
            elif isinstance(first, ast.Name):
                value = self.literal_strings.get(first.id)
            if value is not None:
                module = value.split(".", 1)[0]
                self.dynamic_modules.append(
                    (module, self.function_depth > 0, kind)
                )
        self.generic_visit(node)


def _source_imports(
    source: bytes,
) -> tuple[
    tuple[str, ...],
    tuple[str, ...],
    tuple[tuple[str, bool, str], ...],
]:
    try:
        tree = ast.parse(source)
    except (SyntaxError, UnicodeError) as error:
        raise Rc0029SurfaceRepairDependencyError(
            "RC0029_SOURCE_AST_INVALID"
        ) from error
    literal_strings: dict[str, str] = {}
    assigned_names: set[str] = set()
    for node in tree.body:
        names: tuple[str, ...] = ()
        value: ast.expr | None = None
        if isinstance(node, ast.Assign):
            names = tuple(
                target.id
                for target in node.targets
                if isinstance(target, ast.Name)
            )
            value = node.value
        elif isinstance(node, ast.AnnAssign) and isinstance(
            node.target, ast.Name
        ):
            names = (node.target.id,)
            value = node.value
        for name in names:
            if name in assigned_names:
                literal_strings.pop(name, None)
                continue
            assigned_names.add(name)
            if isinstance(value, ast.Constant) and type(value.value) is str:
                literal_strings[name] = value.value
    visitor = _ImportVisitor(literal_strings)
    visitor.visit(tree)
    return (
        tuple(sorted(visitor.static_modules)),
        tuple(sorted(visitor.module_scope_static_modules)),
        tuple(sorted(set(visitor.dynamic_modules))),
    )


def _is_project_module(module: str) -> bool:
    return module.startswith(_PROJECT_MODULE_PREFIXES)


def _delta_import_edges(
    repo_root: Path,
    *,
    closure_paths: Sequence[str],
) -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    index = _module_index(closure_paths)
    static_edges: set[tuple[str, str]] = set()
    dynamic_edges: set[tuple[str, str, str]] = set()
    importer_paths = tuple(
        path
        for path in (*RC0029_MODIFIED_OWNER_PATHS, *RC0029_HASHED_NEW_PATHS)
        if path.endswith(".py")
    )
    experiment_modules = {
        Path(RC0029_CATALOG_PATH).stem,
        Path(RC0029_RUNTIME_ADAPTER_PATH).stem,
        Path(RC0029_MANIFEST_OWNER_PATH).stem,
    }
    for importer_path in importer_paths:
        try:
            (
                static_modules,
                module_scope_static_modules,
                dynamic_modules,
            ) = _source_imports(
                (repo_root / importer_path).read_bytes()
            )
        except OSError as error:
            raise Rc0029SurfaceRepairDependencyError(
                "RC0029_IMPORT_SOURCE_UNAVAILABLE"
            ) from error
        for module in static_modules:
            imported_path = index.get(module)
            if imported_path is None:
                if _is_project_module(module):
                    raise Rc0029SurfaceRepairDependencyError(
                        "RC0029_UNBOUND_PROJECT_IMPORT"
                    )
                continue
            if (
                importer_path in RC0029_MODIFIED_OWNER_PATHS
                and module in experiment_modules
                and module in module_scope_static_modules
            ):
                raise Rc0029SurfaceRepairDependencyError(
                    "RC0029_EXACT_OWNER_STATIC_EXPERIMENT_IMPORT_FORBIDDEN"
                )
            static_edges.add((importer_path, imported_path))
        for module, function_local, kind in dynamic_modules:
            imported_path = index.get(module)
            if imported_path is None:
                if _is_project_module(module):
                    raise Rc0029SurfaceRepairDependencyError(
                        "RC0029_UNBOUND_DYNAMIC_PROJECT_IMPORT"
                    )
                continue
            if not function_local:
                raise Rc0029SurfaceRepairDependencyError(
                    "RC0029_NONLOCAL_DYNAMIC_IMPORT_FORBIDDEN"
                )
            dynamic_edges.add((importer_path, imported_path, kind))
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


def find_rc0029_surface_repair_unexpected_paths(
    repo_root: Path,
) -> tuple[str, ...]:
    """Discover rc0029-named paths only to reject unapproved additions."""

    known = set(RC0029_NEW_PATH_ALLOWLIST)
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
                or "rc0029" not in path.name.lower()
            ):
                continue
            relative = path.relative_to(repo_root).as_posix()
            if relative not in known:
                found.append(relative)
    return tuple(sorted(set(found)))


def find_rc0029_surface_repair_forbidden_reverse_imports(
    repo_root: Path,
) -> tuple[str, ...]:
    """Reject any shared/public service or tool loading rc0029 modules."""

    forbidden_modules = frozenset(
        {
            Path(RC0029_CATALOG_PATH).stem,
            Path(RC0029_RUNTIME_ADAPTER_PATH).stem,
            Path(RC0029_MANIFEST_OWNER_PATH).stem,
        }
    )
    excluded = set(RC0029_MODIFIED_OWNER_PATHS) | set(
        RC0029_HASHED_NEW_PATHS
    )
    found: list[str] = []
    for root in (repo_root / "ai/services", repo_root / "ai/tools"):
        for path in sorted(root.rglob("*.py")):
            relative = path.relative_to(repo_root).as_posix()
            if relative in excluded:
                continue
            try:
                (
                    static_modules,
                    _module_scope,
                    dynamic_modules,
                ) = _source_imports(
                    path.read_bytes()
                )
            except OSError as error:
                raise Rc0029SurfaceRepairDependencyError(
                    "RC0029_REVERSE_IMPORT_SCAN_UNAVAILABLE"
                ) from error
            imported = set(static_modules) | {
                module for module, _local, _kind in dynamic_modules
            }
            if imported & forbidden_modules:
                found.append(relative)
    return tuple(found)


def _parent_binding(parent: Mapping[str, Any]) -> dict[str, Any]:
    _safe_file_rows(parent["file_hashes"])
    return {
        "schema_version": (
            RC0028_DOWNSTREAM_EXPERIMENT_DEPENDENCY_MANIFEST_SCHEMA
        ),
        "manifest_path": RC0028_DOWNSTREAM_PARENT_MANIFEST_PATH,
        "manifest_file_sha256": (
            RC0028_DOWNSTREAM_PARENT_MANIFEST_FILE_SHA256
        ),
        "manifest_artifact_sha256": (
            RC0028_DOWNSTREAM_PARENT_MANIFEST_ARTIFACT_SHA256
        ),
        "source_dependency_closure_sha256": (
            RC0028_DOWNSTREAM_PARENT_SOURCE_CLOSURE_SHA256
        ),
        "source_file_count": RC0028_DOWNSTREAM_PARENT_SOURCE_FILE_COUNT,
        "file_hashes_sha256": RC0028_DOWNSTREAM_PARENT_FILE_HASHES_SHA256,
        "immutable": True,
    }


def _modified_owner_rows(
    repo_root: Path,
    *,
    parent_by_path: Mapping[str, str],
) -> tuple[list[dict[str, Any]], dict[str, str]]:
    rows: list[dict[str, Any]] = []
    current_by_path: dict[str, str] = {}
    for predecessor in RC0029_MODIFIED_OWNER_PREDECESSORS:
        path = predecessor["path"]
        expected = predecessor["predecessor_sha256"]
        if parent_by_path.get(path) != expected:
            raise Rc0029SurfaceRepairDependencyError(
                "RC0029_MODIFIED_OWNER_PARENT_MISMATCH"
            )
        try:
            source = (repo_root / path).read_bytes()
        except OSError as error:
            raise Rc0029SurfaceRepairDependencyError(
                "RC0029_MODIFIED_OWNER_UNAVAILABLE"
            ) from error
        size = predecessor["predecessor_size"]
        if (
            type(size) is not int
            or size <= 0
            or len(source) <= size
            or _sha256_bytes(source[:size]) != expected
        ):
            raise Rc0029SurfaceRepairDependencyError(
                "RC0029_MODIFIED_OWNER_PREFIX_DRIFT"
            )
        current = _sha256_bytes(source)
        current_by_path[path] = current
        rows.append(
            {
                "path": path,
                "predecessor_size": size,
                "predecessor_sha256": expected,
                "current_sha256": current,
                "append_only_prefix_verified": True,
            }
        )
    rows.sort(key=lambda row: row["path"])
    return rows, current_by_path


def build_rc0029_surface_repair_dependency_manifest(
    parent_manifest: Mapping[str, Any],
    *,
    repo_root: Path,
) -> dict[str, Any]:
    """Build the exact rc0029 delta over immutable rc0028 evidence."""

    parent = _validated_parent_manifest(parent_manifest)
    parent_files = _safe_file_rows(parent["file_hashes"])
    parent_by_path = {row["path"]: row["sha256"] for row in parent_files}
    if any(path in parent_by_path for path in RC0029_HASHED_NEW_PATHS):
        raise Rc0029SurfaceRepairDependencyError(
            "RC0029_NEW_PATH_ALREADY_IN_PARENT"
        )
    if RC0029_GENERATED_MANIFEST_PATH in parent_by_path:
        raise Rc0029SurfaceRepairDependencyError(
            "RC0029_GENERATED_SELF_HASH_IN_PARENT"
        )

    modified_rows, current_by_path = _modified_owner_rows(
        repo_root,
        parent_by_path=parent_by_path,
    )
    current_parent_rows: list[dict[str, str]] = []
    for row in parent_files:
        path = row["path"]
        current = current_by_path.get(path)
        if current is None:
            try:
                current = _sha256(repo_root / path)
            except OSError as error:
                raise Rc0029SurfaceRepairDependencyError(
                    "RC0029_IMMUTABLE_PARENT_SOURCE_UNAVAILABLE"
                ) from error
            if current != row["sha256"]:
                raise Rc0029SurfaceRepairDependencyError(
                    "RC0029_IMMUTABLE_PARENT_SOURCE_DRIFT"
                )
        current_parent_rows.append({"path": path, "sha256": current})

    new_rows: list[dict[str, str]] = []
    for path in RC0029_HASHED_NEW_PATHS:
        try:
            sha256 = _sha256(repo_root / path)
        except OSError as error:
            raise Rc0029SurfaceRepairDependencyError(
                "RC0029_ALLOWLIST_PATH_MISSING"
            ) from error
        new_rows.append({"path": path, "sha256": sha256})
    new_rows.sort(key=lambda row: row["path"])

    unexpected = find_rc0029_surface_repair_unexpected_paths(repo_root)
    if unexpected:
        raise Rc0029SurfaceRepairDependencyError(
            "RC0029_UNEXPECTED_PATH"
        )
    reverse_imports = find_rc0029_surface_repair_forbidden_reverse_imports(
        repo_root
    )
    if reverse_imports:
        raise Rc0029SurfaceRepairDependencyError(
            "RC0029_FORBIDDEN_REVERSE_IMPORT"
        )

    files = sorted(
        current_parent_rows + new_rows,
        key=lambda row: row["path"],
    )
    static_edges, dynamic_edges = _delta_import_edges(
        repo_root,
        closure_paths=[row["path"] for row in files],
    )
    material: dict[str, Any] = {
        "schema_version": RC0029_SURFACE_REPAIR_DEPENDENCY_MANIFEST_SCHEMA,
        "experiment_id": RC0029_SURFACE_REPAIR_EXPERIMENT_ID,
        "baseline_git_commit": RC0029_BASELINE_GIT_COMMIT,
        "baseline_git_tree": RC0029_BASELINE_GIT_TREE,
        "parent": _parent_binding(parent),
        "modified_owner_file_hashes": modified_rows,
        "new_path_allowlist": list(sorted(RC0029_NEW_PATH_ALLOWLIST)),
        "new_file_hashes": new_rows,
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


def validate_rc0029_surface_repair_dependency_manifest_shape(
    value: Any,
) -> tuple[str, ...]:
    """Validate exact fields and canonical commitments without filesystem."""

    if type(value) is not dict:
        return ("RC0029_MANIFEST_MAPPING_REQUIRED",)
    expected_keys = {
        "schema_version",
        "experiment_id",
        "baseline_git_commit",
        "baseline_git_tree",
        "parent",
        "modified_owner_file_hashes",
        "new_path_allowlist",
        "new_file_hashes",
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
        issues.add("RC0029_MANIFEST_SHAPE_INVALID")
    if (
        value.get("schema_version")
        != RC0029_SURFACE_REPAIR_DEPENDENCY_MANIFEST_SCHEMA
        or value.get("experiment_id") != RC0029_SURFACE_REPAIR_EXPERIMENT_ID
        or value.get("baseline_git_commit") != RC0029_BASELINE_GIT_COMMIT
        or value.get("baseline_git_tree") != RC0029_BASELINE_GIT_TREE
        or value.get("body_free") is not True
    ):
        issues.add("RC0029_MANIFEST_IDENTITY_INVALID")
    if value.get("flags") != _FLAGS:
        issues.add("RC0029_FLAGS_INVALID")
    if value.get("canonical_rebuild") != _CANONICAL_REBUILD:
        issues.add("RC0029_CANONICAL_REBUILD_INVALID")
    if value.get("generated_manifest") != _GENERATED_MANIFEST_POLICY:
        issues.add("RC0029_SELF_HASH_POLICY_INVALID")
    if value.get("new_path_allowlist") != list(
        sorted(RC0029_NEW_PATH_ALLOWLIST)
    ):
        issues.add("RC0029_PATH_ALLOWLIST_INVALID")
    expected_parent = {
        "schema_version": (
            RC0028_DOWNSTREAM_EXPERIMENT_DEPENDENCY_MANIFEST_SCHEMA
        ),
        "manifest_path": RC0028_DOWNSTREAM_PARENT_MANIFEST_PATH,
        "manifest_file_sha256": (
            RC0028_DOWNSTREAM_PARENT_MANIFEST_FILE_SHA256
        ),
        "manifest_artifact_sha256": (
            RC0028_DOWNSTREAM_PARENT_MANIFEST_ARTIFACT_SHA256
        ),
        "source_dependency_closure_sha256": (
            RC0028_DOWNSTREAM_PARENT_SOURCE_CLOSURE_SHA256
        ),
        "source_file_count": RC0028_DOWNSTREAM_PARENT_SOURCE_FILE_COUNT,
        "file_hashes_sha256": RC0028_DOWNSTREAM_PARENT_FILE_HASHES_SHA256,
        "immutable": True,
    }
    if value.get("parent") != expected_parent:
        issues.add("RC0029_PARENT_BINDING_INVALID")
    if any(
        value.get(key) != []
        for key in (
            "unexpected_paths",
            "unbound_project_imports",
            "forbidden_reverse_imports",
        )
    ):
        issues.add("RC0029_OPEN_DEPENDENCY_SET")

    try:
        files = _safe_file_rows(value.get("file_hashes"))
        new_rows = _safe_file_rows(value.get("new_file_hashes"))
    except Rc0029SurfaceRepairDependencyError:
        issues.add("RC0029_FILE_ROWS_INVALID")
        files = []
        new_rows = []
    by_path = {row["path"]: row["sha256"] for row in files}
    new_by_path = {row["path"]: row["sha256"] for row in new_rows}
    if (
        set(new_by_path) != set(RC0029_HASHED_NEW_PATHS)
        or any(by_path.get(path) != sha for path, sha in new_by_path.items())
        or RC0029_GENERATED_MANIFEST_PATH in by_path
        or value.get("source_file_count") != len(files)
        or len(files)
        != RC0028_DOWNSTREAM_PARENT_SOURCE_FILE_COUNT
        + len(RC0029_HASHED_NEW_PATHS)
    ):
        issues.add("RC0029_FILE_CLOSURE_INVALID")

    modified = value.get("modified_owner_file_hashes")
    expected_predecessors = {
        row["path"]: row for row in RC0029_MODIFIED_OWNER_PREDECESSORS
    }
    if type(modified) is not list:
        issues.add("RC0029_MODIFIED_OWNER_LEDGER_INVALID")
    else:
        seen: set[str] = set()
        normalized: list[str] = []
        for row in modified:
            if (
                type(row) is not dict
                or set(row)
                != {
                    "path",
                    "predecessor_size",
                    "predecessor_sha256",
                    "current_sha256",
                    "append_only_prefix_verified",
                }
            ):
                issues.add("RC0029_MODIFIED_OWNER_LEDGER_INVALID")
                continue
            path = row.get("path")
            predecessor = expected_predecessors.get(path)
            if (
                predecessor is None
                or row.get("predecessor_size")
                != predecessor["predecessor_size"]
                or row.get("predecessor_sha256")
                != predecessor["predecessor_sha256"]
                or type(row.get("current_sha256")) is not str
                or _SHA_RE.fullmatch(row["current_sha256"]) is None
                or row.get("current_sha256")
                == predecessor["predecessor_sha256"]
                or row.get("append_only_prefix_verified") is not True
                or by_path.get(path) != row.get("current_sha256")
                or path in seen
            ):
                issues.add("RC0029_MODIFIED_OWNER_LEDGER_INVALID")
            if type(path) is str:
                seen.add(path)
                normalized.append(path)
        if (
            set(seen) != set(RC0029_MODIFIED_OWNER_PATHS)
            or normalized != sorted(normalized)
        ):
            issues.add("RC0029_MODIFIED_OWNER_LEDGER_INVALID")

    static_edges = _normalized_edges(
        value.get("static_project_import_edges"),
        dynamic=False,
    )
    dynamic_edges = _normalized_edges(
        value.get("dynamic_project_import_edges"),
        dynamic=True,
    )
    if static_edges is None or dynamic_edges is None:
        issues.add("RC0029_IMPORT_GRAPH_INVALID")
    else:
        if any(
            importer not in by_path or imported not in by_path
            for importer, imported in static_edges
        ) or any(
            importer not in by_path or imported not in by_path
            for importer, imported, _kind in dynamic_edges
        ):
            issues.add("RC0029_IMPORT_GRAPH_INVALID")

    closure = value.get("source_dependency_closure_sha256")
    if type(closure) is not str or _SHA_RE.fullmatch(closure) is None:
        issues.add("RC0029_CLOSURE_HASH_INVALID")
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
            issues.add("RC0029_CLOSURE_HASH_MISMATCH")
    return tuple(sorted(issues))


def validate_rc0029_surface_repair_dependency_manifest(
    value: Any,
    *,
    parent_manifest: Mapping[str, Any],
    repo_root: Path,
) -> tuple[str, ...]:
    shape_issues = validate_rc0029_surface_repair_dependency_manifest_shape(
        value
    )
    if shape_issues:
        return shape_issues
    try:
        expected = build_rc0029_surface_repair_dependency_manifest(
            parent_manifest,
            repo_root=repo_root,
        )
    except (
        KeyError,
        OSError,
        TypeError,
        Rc0029SurfaceRepairDependencyError,
    ):
        return ("RC0029_DEPENDENCY_UNAVAILABLE_OR_DRIFTED",)
    if value != expected:
        return ("RC0029_DEPENDENCY_RECOMPUTATION_MISMATCH",)
    return ()


__all__ = [
    "RC0028_DOWNSTREAM_PARENT_MANIFEST_FILE_SHA256",
    "RC0028_DOWNSTREAM_PARENT_MANIFEST_PATH",
    "RC0029_BASELINE_GIT_COMMIT",
    "RC0029_BASELINE_GIT_TREE",
    "RC0029_GENERATED_MANIFEST_PATH",
    "RC0029_HASHED_NEW_PATHS",
    "RC0029_MODIFIED_OWNER_PATHS",
    "RC0029_MODIFIED_OWNER_PREDECESSORS",
    "RC0029_NEW_PATH_ALLOWLIST",
    "RC0029_SURFACE_REPAIR_DEPENDENCY_MANIFEST_SCHEMA",
    "RC0029_SURFACE_REPAIR_EXPERIMENT_ID",
    "Rc0029SurfaceRepairDependencyError",
    "build_rc0029_surface_repair_dependency_manifest",
    "find_rc0029_surface_repair_forbidden_reverse_imports",
    "find_rc0029_surface_repair_unexpected_paths",
    "validate_rc0029_surface_repair_dependency_manifest",
    "validate_rc0029_surface_repair_dependency_manifest_shape",
]
