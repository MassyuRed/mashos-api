# -*- coding: utf-8 -*-
from __future__ import annotations

"""Recovery Epoch 002 source/bootstrap closure contracts.

The public reconciliation API consumes body-free observations.  Strict
helpers in this module validate actual source and bootstrap manifests without
importing application modules or executing tests.
"""

import ast
from copy import deepcopy
import hashlib
import os
from pathlib import Path
import re
import stat
from typing import Any, Mapping

from emlis_ai_nls_v3_artifact_contract import artifact_sha256
from emlis_ai_recovery_epoch001_current_step_requirement_registry_v3 import (
    RECOVERY_EPOCH001_EXPECTED_FORMAL_NODE_REGISTRY_SHA256,
    RECOVERY_EPOCH001_EXPECTED_REGISTRY_SHA256,
    RECOVERY_EPOCH001_FORMAL_NODE_IDS_BY_STEP,
    fresh_recovery_epoch001_current_step_requirement_registry,
    validate_recovery_epoch001_current_step_requirement_registry_shape,
)


def _keys(value: str) -> frozenset[str]:
    return frozenset(value.split())


RECOVERY_EPOCH002_SOURCE_CLOSURE_KEYS = _keys(
    """
    repository_full_name source_ref source_commit_sha1 source_tree_sha1
    worktree_clean detailed_design_sha256
    source_dependency_closure_sha256 canonical_current_closure_sha256
    requirement_registry_sha256 formal_node_registry_sha256
    proof_source_closure_sha256 formal_test_manifest_sha256
    bootstrap_closure_sha256 d2_final_closure_sha256 source_closure_sha256
    """
)
RECOVERY_EPOCH002_D2_FINAL_CLOSURE_PREIMAGE_KEYS = (
    "source_commit_sha1",
    "source_tree_sha1",
    "canonical_current_closure_sha256",
    "source_dependency_closure_sha256",
    "proof_source_closure_sha256",
    "requirement_registry_sha256",
    "formal_node_registry_sha256",
    "formal_test_manifest_sha256",
    "bootstrap_closure_sha256",
    "detailed_design_sha256",
)
RECOVERY_EPOCH002_BOOTSTRAP_CLOSURE_KEYS = _keys(
    """
    schema_version source_commit_sha1 source_tree_sha1 formal_owner_artifacts
    formal_owner_artifacts_sha256 formal_test_node_ids formal_test_manifest
    formal_test_manifest_sha256 conftest_plugin_mode
    pytest_plugins_environment_variable_removed
    pytest_entrypoint_autoload_disabled explicit_plugin_allowlist
    loaded_plugin_manifest loaded_plugin_manifest_sha256 import_manifest
    import_manifest_sha256 dependency_lock_identity installed_distributions
    installed_distributions_sha256 python_runtime_identity
    pytest_distribution_identity environment_profile
    environment_profile_sha256 preflight_argv preflight_argv_sha256
    formal_worker_argv formal_worker_argv_sha256 unclassified_import_count
    unresolved_dynamic_import_count body_free bootstrap_closure_sha256
    """
)
RECOVERY_EPOCH002_IMPORT_MANIFEST_ROW_KEYS = _keys(
    "import_name classification owner_paths target_identity"
)
RECOVERY_EPOCH002_FIRST_PARTY_IMPORT_TARGET_KEYS = _keys(
    "path git_blob_sha1 raw_sha256"
)
RECOVERY_EPOCH002_STDLIB_IMPORT_TARGET_KEYS = _keys(
    "module_name python_runtime_identity_sha256"
)
RECOVERY_EPOCH002_THIRD_PARTY_IMPORT_TARGET_KEYS = _keys(
    """
    module_name normalized_distribution_name distribution_version
    wheel_sha256 installed_record_closure_sha256
    """
)
RECOVERY_EPOCH002_IMPORT_CLASSIFICATIONS = frozenset(
    {
        "FIRST_PARTY",
        "STDLIB_BOUND_TO_PYTHON_RUNTIME",
        "THIRD_PARTY_BOUND_TO_LOCKED_DISTRIBUTION",
    }
)
RECOVERY_EPOCH002_INSTALLER_IDENTITY_CLASS = (
    "PIP_REQUIRE_HASHES_WHEEL_LOCK_V1"
)
RECOVERY_EPOCH002_OPERATIONAL_OWNER_PATHS = {
    "bootstrap_closure_owner": (
        "ai/services/ai_inference/"
        "emlis_ai_recovery_epoch002_canonical_current_closure_v3.py"
    ),
    "canonical_current_closure_owner": (
        "ai/services/ai_inference/"
        "emlis_ai_recovery_epoch002_canonical_current_closure_v3.py"
    ),
    "checkpoint_owner": (
        "ai/tools/"
        "emlis_nls_v3_recovery_epoch002_formal_worker_evidence_v3.py"
    ),
    "formal_parent_owner": (
        "ai/tools/"
        "emlis_nls_v3_recovery_epoch002_formal_parent_orchestrator_v3.py"
    ),
    "formal_worker_owner": (
        "ai/tools/"
        "emlis_nls_v3_recovery_epoch002_current_step_proof_run.py"
    ),
    "independent_verifier": (
        "ai/tools/"
        "emlis_nls_v3_recovery_epoch002_closure_receipt_verify.py"
    ),
    "preflight_owner": (
        "ai/tools/"
        "emlis_nls_v3_recovery_epoch002_formal_worker_bootstrap_preflight.py"
    ),
    "publication_owner": (
        "ai/tools/"
        "emlis_nls_v3_recovery_epoch002_atomic_publication_bundle_v3.py"
    ),
    "readiness_owner": (
        "ai/tools/"
        "emlis_nls_v3_recovery_epoch002_formal_worker_bootstrap_preflight.py"
    ),
    "reproducible_dependency_lock": (
        "ai/configs/"
        "emlis_nls_v3_recovery_epoch002_formal_worker_bootstrap_lock_v1.json"
    ),
    "sequence_lineage_owner": (
        "ai/services/ai_inference/"
        "emlis_ai_recovery_epoch002_sequence_ledger_v3.py"
    ),
    "terminal_result_owner": (
        "ai/tools/"
        "emlis_nls_v3_recovery_epoch002_formal_worker_evidence_v3.py"
    ),
}
_OWNER_ARTIFACT_KEYS = _keys("role path git_blob_sha1 raw_sha256")
_SOURCE_FILE_IDENTITY_KEYS = _keys("path git_blob_sha1 raw_sha256")
_INSTALLED_DISTRIBUTION_IDENTITY_KEYS = _keys(
    """
    normalized_distribution_name distribution_version wheel_sha256
    installed_record_closure_sha256
    """
)

_BOOTSTRAP_SCHEMA = (
    "cocolon.emlis.nls_v3.recovery_epoch002."
    "formal_worker_bootstrap_manifest.v1"
)
_SHA1_RE = re.compile(r"^[0-9a-f]{40}$")
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")


def _hash_without(value: Mapping[str, Any], key: str) -> str:
    material = deepcopy(dict(value))
    material.pop(key, None)
    return artifact_sha256(material)


def _import_target_valid(row: Mapping[str, Any]) -> bool:
    classification = row.get("classification")
    target = row.get("target_identity")
    if type(target) is not dict:
        return False
    if classification == "FIRST_PARTY":
        return set(target) == RECOVERY_EPOCH002_FIRST_PARTY_IMPORT_TARGET_KEYS
    if classification == "STDLIB_BOUND_TO_PYTHON_RUNTIME":
        return set(target) == RECOVERY_EPOCH002_STDLIB_IMPORT_TARGET_KEYS
    if classification == "THIRD_PARTY_BOUND_TO_LOCKED_DISTRIBUTION":
        return (
            set(target)
            == RECOVERY_EPOCH002_THIRD_PARTY_IMPORT_TARGET_KEYS
        )
    return False


def validate_recovery_epoch002_bootstrap_manifest(
    manifest: Mapping[str, Any],
) -> tuple[str, ...]:
    """Strictly validate a materialized bootstrap-closure manifest."""

    if type(manifest) is not dict:
        return ("READINESS_FORBIDDEN",)
    if set(manifest) != RECOVERY_EPOCH002_BOOTSTRAP_CLOSURE_KEYS:
        return ("READINESS_FORBIDDEN",)
    if manifest.get("schema_version") != _BOOTSTRAP_SCHEMA:
        return ("READINESS_FORBIDDEN",)
    owner_artifacts = manifest.get("formal_owner_artifacts")
    formal_nodes = manifest.get("formal_test_node_ids")
    formal_manifest = manifest.get("formal_test_manifest")
    installed = manifest.get("installed_distributions")
    python_identity = manifest.get("python_runtime_identity")
    pytest_identity = manifest.get("pytest_distribution_identity")
    environment = manifest.get("environment_profile")
    preflight_argv = manifest.get("preflight_argv")
    formal_argv = manifest.get("formal_worker_argv")
    if (
        _SHA1_RE.fullmatch(str(manifest.get("source_commit_sha1", "")))
        is None
        or _SHA1_RE.fullmatch(str(manifest.get("source_tree_sha1", "")))
        is None
        or type(owner_artifacts) is not list
        or not owner_artifacts
        or manifest.get("formal_owner_artifacts_sha256")
        != artifact_sha256(owner_artifacts)
        or type(formal_nodes) is not list
        or len(formal_nodes) != 134
        or any(not isinstance(node, str) or not node for node in formal_nodes)
        or len(formal_nodes) != len(set(formal_nodes))
        or type(formal_manifest) is not list
        or not formal_manifest
        or manifest.get("formal_test_manifest_sha256")
        != artifact_sha256(formal_manifest)
        or manifest.get("conftest_plugin_mode")
        != "DISABLED_BY_NOCONFTEST"
        or manifest.get("pytest_plugins_environment_variable_removed")
        is not True
        or manifest.get("pytest_entrypoint_autoload_disabled") is not True
        or manifest.get("explicit_plugin_allowlist") != []
        or manifest.get("loaded_plugin_manifest") != []
        or manifest.get("loaded_plugin_manifest_sha256")
        != artifact_sha256([])
        or type(installed) is not list
        or not installed
        or manifest.get("installed_distributions_sha256")
        != artifact_sha256(installed)
        or type(python_identity) is not dict
        or type(pytest_identity) is not dict
        or type(environment) is not dict
        or manifest.get("environment_profile_sha256")
        != artifact_sha256(environment)
        or type(preflight_argv) is not list
        or not preflight_argv
        or manifest.get("preflight_argv_sha256")
        != artifact_sha256(preflight_argv)
        or type(formal_argv) is not list
        or "--noconftest" not in formal_argv
        or manifest.get("formal_worker_argv_sha256")
        != artifact_sha256(formal_argv)
        or manifest.get("unclassified_import_count") != 0
        or manifest.get("unresolved_dynamic_import_count") != 0
        or manifest.get("body_free") is not True
    ):
        return ("READINESS_FORBIDDEN",)
    rows = manifest.get("import_manifest")
    if type(rows) is not list or not rows:
        return ("READINESS_FORBIDDEN",)
    for row in rows:
        if type(row) is not dict:
            return ("READINESS_FORBIDDEN",)
        if set(row) != RECOVERY_EPOCH002_IMPORT_MANIFEST_ROW_KEYS:
            return ("READINESS_FORBIDDEN",)
        if row.get("classification") not in (
            RECOVERY_EPOCH002_IMPORT_CLASSIFICATIONS
        ):
            return ("READINESS_FORBIDDEN",)
        if type(row.get("owner_paths")) is not list:
            return ("READINESS_FORBIDDEN",)
        if not _import_target_valid(row):
            return ("READINESS_FORBIDDEN",)
    if manifest.get("import_manifest_sha256") != artifact_sha256(rows):
        return ("READINESS_FORBIDDEN",)
    if (
        manifest.get("bootstrap_closure_sha256")
        != _hash_without(manifest, "bootstrap_closure_sha256")
    ):
        return ("READINESS_FORBIDDEN",)
    lock_identity = manifest.get("dependency_lock_identity")
    if (
        type(lock_identity) is not dict
        or set(lock_identity)
        != {"identity_class", "path", "raw_sha256"}
        or lock_identity.get("identity_class")
        != RECOVERY_EPOCH002_INSTALLER_IDENTITY_CLASS
        or _SHA256_RE.fullmatch(
            str(lock_identity.get("raw_sha256", ""))
        )
        is None
    ):
        return ("READINESS_FORBIDDEN",)
    return ()


def _canonical_source_path(value: Any) -> bool:
    if not isinstance(value, str) or not value:
        return False
    if value.startswith("/") or "\\" in value:
        return False
    parts = value.split("/")
    return all(part not in {"", ".", ".."} for part in parts)


def validate_recovery_epoch002_operational_bootstrap_manifest(
    manifest: Mapping[str, Any],
    dependency_lock: Mapping[str, Any],
) -> tuple[str, ...]:
    """Bind the exact operational owners, nodes, imports, and exact46 lock."""

    issues = validate_recovery_epoch002_bootstrap_manifest(manifest)
    if issues:
        return issues
    if type(dependency_lock) is not dict:
        return ("READINESS_FORBIDDEN",)

    owner_rows = manifest["formal_owner_artifacts"]
    owner_roles = [row.get("role") for row in owner_rows]
    if (
        any(
            type(row) is not dict
            or set(row) != _OWNER_ARTIFACT_KEYS
            or not _canonical_source_path(row.get("path"))
            or _SHA1_RE.fullmatch(str(row.get("git_blob_sha1", "")))
            is None
            or _SHA256_RE.fullmatch(str(row.get("raw_sha256", "")))
            is None
            for row in owner_rows
        )
        or owner_roles != sorted(RECOVERY_EPOCH002_OPERATIONAL_OWNER_PATHS)
        or any(
            row["path"]
            != RECOVERY_EPOCH002_OPERATIONAL_OWNER_PATHS[row["role"]]
            for row in owner_rows
        )
    ):
        return ("READINESS_FORBIDDEN",)

    formal_rows = manifest["formal_test_manifest"]
    formal_paths = [row.get("path") for row in formal_rows]
    if (
        any(
            type(row) is not dict
            or set(row) != _SOURCE_FILE_IDENTITY_KEYS
            or not _canonical_source_path(row.get("path"))
            or _SHA1_RE.fullmatch(str(row.get("git_blob_sha1", "")))
            is None
            or _SHA256_RE.fullmatch(str(row.get("raw_sha256", "")))
            is None
            for row in formal_rows
        )
        or formal_paths != sorted(set(formal_paths))
        or any(
            node.split("::", 1)[0] not in formal_paths
            for node in manifest["formal_test_node_ids"]
        )
    ):
        return ("READINESS_FORBIDDEN",)

    lock_rows = dependency_lock.get("distributions")
    installed_rows = manifest["installed_distributions"]
    if type(lock_rows) is not list or type(installed_rows) is not list:
        return ("READINESS_FORBIDDEN",)
    expected_installed = [
        {
            "normalized_distribution_name": row.get(
                "normalized_distribution_name"
            ),
            "distribution_version": row.get("distribution_version"),
            "wheel_sha256": row.get("wheel_sha256"),
            "installed_record_closure_sha256": row.get(
                "installed_record_closure_sha256"
            ),
        }
        for row in lock_rows
    ]
    if (
        any(
            type(row) is not dict
            or set(row) != _INSTALLED_DISTRIBUTION_IDENTITY_KEYS
            for row in installed_rows
        )
        or installed_rows != expected_installed
        or dependency_lock.get("distribution_count") != len(installed_rows)
    ):
        return ("READINESS_FORBIDDEN",)
    installed_by_name = {
        row["normalized_distribution_name"]: row
        for row in installed_rows
    }
    if manifest["pytest_distribution_identity"] != installed_by_name.get(
        "pytest"
    ):
        return ("READINESS_FORBIDDEN",)

    python_identity = manifest["python_runtime_identity"]
    if (
        set(python_identity)
        != {"executable_sha256", "implementation", "version", "build_sha256"}
        or python_identity.get("implementation") != "CPYTHON"
        or not isinstance(python_identity.get("version"), str)
        or not python_identity.get("version")
        or _SHA256_RE.fullmatch(
            str(python_identity.get("executable_sha256", ""))
        )
        is None
        or _SHA256_RE.fullmatch(str(python_identity.get("build_sha256", "")))
        is None
    ):
        return ("READINESS_FORBIDDEN",)

    first_party_paths = {
        row["target_identity"]["path"]
        for row in manifest["import_manifest"]
        if row["classification"] == "FIRST_PARTY"
    }
    allowed_owner_paths = (
        set(RECOVERY_EPOCH002_OPERATIONAL_OWNER_PATHS.values())
        | set(formal_paths)
        | first_party_paths
    )
    module_mapping = dependency_lock.get("module_distribution_map")
    namespace_mapping = dependency_lock.get("resolution", {}).get(
        "namespace_module_distribution_map",
        {},
    )
    if type(module_mapping) is not dict or type(namespace_mapping) is not dict:
        return ("READINESS_FORBIDDEN",)
    import_names: list[str] = []
    runtime_identity_sha256 = artifact_sha256(python_identity)
    for row in manifest["import_manifest"]:
        import_name = row["import_name"]
        owner_paths = row["owner_paths"]
        target = row["target_identity"]
        import_names.append(import_name)
        if (
            not isinstance(import_name, str)
            or not import_name
            or owner_paths != sorted(set(owner_paths))
            or not owner_paths
            or any(path not in allowed_owner_paths for path in owner_paths)
        ):
            return ("READINESS_FORBIDDEN",)
        if row["classification"] == "FIRST_PARTY":
            if (
                not _canonical_source_path(target.get("path"))
                or _SHA1_RE.fullmatch(
                    str(target.get("git_blob_sha1", ""))
                )
                is None
                or _SHA256_RE.fullmatch(str(target.get("raw_sha256", "")))
                is None
            ):
                return ("READINESS_FORBIDDEN",)
        elif row["classification"] == "STDLIB_BOUND_TO_PYTHON_RUNTIME":
            if (
                not isinstance(target.get("module_name"), str)
                or not target.get("module_name")
                or target.get("python_runtime_identity_sha256")
                != runtime_identity_sha256
            ):
                return ("READINESS_FORBIDDEN",)
        else:
            matching_prefixes = [
                prefix
                for prefix in module_mapping
                if (
                    import_name == prefix
                    or import_name.startswith(f"{prefix}.")
                )
            ]
            if not matching_prefixes:
                return ("READINESS_FORBIDDEN",)
            longest = max(matching_prefixes, key=len)
            if (
                import_name == longest
                and len(namespace_mapping.get(longest, ())) > 1
            ):
                return ("READINESS_FORBIDDEN",)
            expected_distribution = module_mapping[longest]
            if target != {
                "module_name": target.get("module_name"),
                **installed_by_name.get(expected_distribution, {}),
            } or target.get("module_name") != import_name:
                return ("READINESS_FORBIDDEN",)
    if import_names != sorted(set(import_names)):
        return ("READINESS_FORBIDDEN",)
    return ()


def validate_recovery_epoch002_formal_node_registry(
    repository_root: Path,
    manifest: Mapping[str, Any],
    source_closure: Mapping[str, Any],
) -> tuple[str, ...]:
    """Bind exact134 to the existing authoritative Step 0--10 registry."""

    try:
        registry = (
            fresh_recovery_epoch001_current_step_requirement_registry()
        )
        registry_issues = (
            validate_recovery_epoch001_current_step_requirement_registry_shape(
                registry,
                repo_root=repository_root,
            )
        )
        ordered_nodes = [
            node
            for step in range(11)
            for node in RECOVERY_EPOCH001_FORMAL_NODE_IDS_BY_STEP[step]
        ]
        formal_root = artifact_sha256(
            {
                "step_nodes": {
                    str(step): list(
                        RECOVERY_EPOCH001_FORMAL_NODE_IDS_BY_STEP[step]
                    )
                    for step in range(11)
                }
            }
        )
    except (KeyError, OSError, TypeError, ValueError):
        return ("READINESS_FORBIDDEN",)
    if (
        registry_issues
        or registry.get("registry_sha256")
        != RECOVERY_EPOCH001_EXPECTED_REGISTRY_SHA256
        or source_closure.get("requirement_registry_sha256")
        != RECOVERY_EPOCH001_EXPECTED_REGISTRY_SHA256
        or formal_root
        != RECOVERY_EPOCH001_EXPECTED_FORMAL_NODE_REGISTRY_SHA256
        or source_closure.get("formal_node_registry_sha256")
        != RECOVERY_EPOCH001_EXPECTED_FORMAL_NODE_REGISTRY_SHA256
        or manifest.get("formal_test_node_ids") != ordered_nodes
    ):
        return ("READINESS_FORBIDDEN",)
    return ()


def validate_recovery_epoch002_operational_source_manifest(
    repository_root: Path,
    manifest: Mapping[str, Any],
    dependency_lock: Mapping[str, Any],
    stdlib_module_names: frozenset[str],
) -> tuple[str, ...]:
    """Verify source bytes and derive complete static/dynamic import coverage."""

    if type(manifest) is not dict:
        return ("READINESS_FORBIDDEN",)
    root = repository_root.absolute()
    try:
        root_stat = root.lstat()
    except OSError:
        return ("READINESS_FORBIDDEN",)
    if (
        not stat.S_ISDIR(root_stat.st_mode)
        or repository_root.is_symlink()
    ):
        return ("READINESS_FORBIDDEN",)

    def child(relative_text: Any) -> Path | None:
        if (
            not _canonical_source_path(relative_text)
            or Path(relative_text).is_absolute()
        ):
            return None
        relative = Path(relative_text)
        target = (root / relative).absolute()
        try:
            target.relative_to(root)
        except ValueError:
            return None
        current = root
        for component in relative.parts:
            current = current / component
            try:
                current_stat = current.lstat()
            except OSError:
                return None
            if stat.S_ISLNK(current_stat.st_mode):
                return None
        return target

    def read_payload(path: Path) -> bytes | None:
        flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0)
        try:
            descriptor = os.open(path, flags)
        except OSError:
            return None
        try:
            file_stat = os.fstat(descriptor)
            if not stat.S_ISREG(file_stat.st_mode):
                return None
            chunks: list[bytes] = []
            total = 0
            while True:
                block = os.read(descriptor, 1024 * 1024)
                if not block:
                    break
                total += len(block)
                if total > 128 * 1024 * 1024:
                    return None
                chunks.append(block)
            return b"".join(chunks)
        finally:
            os.close(descriptor)

    identities: dict[str, tuple[str, str]] = {}
    rows = [
        *manifest.get("formal_owner_artifacts", []),
        *manifest.get("formal_test_manifest", []),
        *[
            row["target_identity"]
            for row in manifest.get("import_manifest", [])
            if (
                type(row) is dict
                and row.get("classification") == "FIRST_PARTY"
                and type(row.get("target_identity")) is dict
            )
        ],
    ]
    for row in rows:
        if type(row) is not dict or "path" not in row:
            return ("READINESS_FORBIDDEN",)
        path_text = row["path"]
        expected = (row.get("git_blob_sha1"), row.get("raw_sha256"))
        if path_text in identities and identities[path_text] != expected:
            return ("READINESS_FORBIDDEN",)
        identities[path_text] = expected

    source_payloads: dict[str, bytes] = {}
    for path_text, (expected_blob, expected_raw) in identities.items():
        source_path = child(path_text)
        observed = None if source_path is None else read_payload(source_path)
        if observed is None:
            return ("READINESS_FORBIDDEN",)
        header = f"blob {len(observed)}\0".encode("ascii")
        if (
            hashlib.sha256(observed).hexdigest() != expected_raw
            or hashlib.sha1(
                header + observed,
                usedforsecurity=False,
            ).hexdigest()
            != expected_blob
        ):
            return ("READINESS_FORBIDDEN",)
        source_payloads[path_text] = observed

    observed_owners: dict[str, set[str]] = {}
    unresolved_dynamic_import_count = 0
    if type(dependency_lock) is not dict or type(stdlib_module_names) is not frozenset:
        return ("READINESS_FORBIDDEN",)
    module_mapping = dependency_lock.get("module_distribution_map")
    if type(module_mapping) is not dict:
        return ("READINESS_FORBIDDEN",)

    def observe(import_name: str, owner_path: str) -> None:
        if import_name:
            observed_owners.setdefault(import_name, set()).add(owner_path)

    def module_search_roots(owner_path: str) -> tuple[Path, ...]:
        if owner_path.startswith("ai/tests/"):
            return (
                Path("ai/tests"),
                Path("ai/tests/helpers"),
                Path("ai/tools"),
                Path("ai/services/ai_inference"),
                Path("ai/services"),
                Path(),
            )
        return (
            Path("ai/tests/helpers"),
            Path("ai/tools"),
            Path("ai/services/ai_inference"),
            Path("ai/services"),
            Path(),
        )

    def module_source_paths(
        import_name: str,
        owner_path: str,
    ) -> list[str]:
        if not import_name or import_name.startswith("file:"):
            return []
        module_relative = Path(*import_name.split("."))
        result: list[str] = []
        for search_root in module_search_roots(owner_path):
            for suffix in (
                module_relative / "__init__.py",
                Path(f"{module_relative}.py"),
            ):
                relative = search_root / suffix
                target = child(relative.as_posix())
                if target is None:
                    continue
                try:
                    target_stat = target.lstat()
                except OSError:
                    continue
                if stat.S_ISREG(target_stat.st_mode):
                    result.append(relative.as_posix())
        return result

    def owner_package_parts(owner_path: str) -> list[str] | None:
        path = Path(owner_path)
        for search_root in module_search_roots(owner_path):
            try:
                relative = path.relative_to(search_root)
            except ValueError:
                continue
            if relative.suffix != ".py":
                return None
            return list(relative.parts[:-1])
        return None

    for owner_path, observed in source_payloads.items():
        if not owner_path.endswith(".py"):
            continue
        try:
            tree = ast.parse(observed, filename=owner_path)
        except (SyntaxError, UnicodeError):
            return ("READINESS_FORBIDDEN",)
        package_parts = owner_package_parts(owner_path)
        if package_parts is None:
            return ("READINESS_FORBIDDEN",)
        importlib_aliases = {"importlib"}
        import_module_aliases: set[str] = set()
        pathlib_aliases = {"pathlib"}
        path_constructor_aliases: set[str] = set()
        pytest_aliases = {"pytest"}

        def import_name(import_node: ast.ImportFrom) -> str | None:
            if not import_node.level:
                return import_node.module or ""
            keep = len(package_parts) - (import_node.level - 1)
            if keep <= 0:
                return None
            parts = package_parts[:keep]
            if import_node.module:
                parts.extend(import_node.module.split("."))
            return ".".join(parts)

        source_exports: dict[str, frozenset[str]] = {}

        def exported_names(path_text: str) -> frozenset[str]:
            cached = source_exports.get(path_text)
            if cached is not None:
                return cached
            payload = source_payloads.get(path_text)
            if payload is None:
                return frozenset()
            try:
                source_tree = ast.parse(payload, filename=path_text)
            except (SyntaxError, UnicodeError):
                return frozenset()
            names: set[str] = set()

            def bind(target: ast.AST) -> None:
                if isinstance(target, ast.Name):
                    names.add(target.id)
                elif isinstance(target, (ast.Tuple, ast.List)):
                    for element in target.elts:
                        bind(element)

            for statement in source_tree.body:
                if isinstance(
                    statement,
                    (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef),
                ):
                    names.add(statement.name)
                elif isinstance(statement, ast.Assign):
                    for target in statement.targets:
                        bind(target)
                elif isinstance(statement, ast.AnnAssign):
                    bind(statement.target)
                elif isinstance(statement, ast.Import):
                    for alias in statement.names:
                        names.add(alias.asname or alias.name.split(".", 1)[0])
                elif isinstance(statement, ast.ImportFrom):
                    for alias in statement.names:
                        if alias.name != "*":
                            names.add(alias.asname or alias.name)
            result = frozenset(names)
            source_exports[path_text] = result
            return result

        def first_party_import_available(import_node: ast.AST) -> bool:
            if isinstance(import_node, ast.Import):
                return all(
                    len(module_source_paths(alias.name, owner_path)) == 1
                    for alias in import_node.names
                )
            if not isinstance(import_node, ast.ImportFrom):
                return False
            resolved = import_name(import_node)
            if not resolved:
                return False
            target_paths = module_source_paths(resolved, owner_path)
            if len(target_paths) != 1:
                return False
            target_exports = exported_names(target_paths[0])
            for alias in import_node.names:
                if alias.name == "*":
                    return False
                submodule = f"{resolved}.{alias.name}"
                if (
                    len(module_source_paths(submodule, owner_path)) == 1
                    or alias.name in target_exports
                ):
                    continue
                return False
            return True

        def runtime_reachable_nodes(node: ast.AST) -> list[ast.AST]:
            result = [node]
            if isinstance(node, ast.Try):
                primary_imports = [
                    statement
                    for statement in node.body
                    if isinstance(statement, (ast.Import, ast.ImportFrom))
                ]
                if primary_imports and all(
                    isinstance(statement, (ast.Import, ast.ImportFrom))
                    for statement in node.body
                ) and all(
                    first_party_import_available(item)
                    for item in primary_imports
                ):
                    children: list[ast.AST] = [
                        *node.body,
                        *node.orelse,
                        *node.finalbody,
                    ]
                else:
                    children = [
                        *node.body,
                        *node.handlers,
                        *node.orelse,
                        *node.finalbody,
                    ]
            else:
                children = list(ast.iter_child_nodes(node))
            for child_node in children:
                result.extend(runtime_reachable_nodes(child_node))
            return result

        runtime_nodes = runtime_reachable_nodes(tree)
        for node in runtime_nodes:
            if isinstance(node, ast.Import):
                for alias in node.names:
                    observe(alias.name, owner_path)
                    if alias.name == "importlib":
                        importlib_aliases.add(alias.asname or alias.name)
                    if alias.name == "pytest":
                        pytest_aliases.add(alias.asname or alias.name)
                    if alias.name == "pathlib":
                        pathlib_aliases.add(alias.asname or alias.name)
            elif isinstance(node, ast.ImportFrom):
                resolved_import_name = import_name(node)
                if resolved_import_name is None:
                    return ("READINESS_FORBIDDEN",)
                observe(resolved_import_name, owner_path)
                for alias in node.names:
                    if alias.name == "*" or not resolved_import_name:
                        continue
                    submodule = f"{resolved_import_name}.{alias.name}"
                    if module_source_paths(submodule, owner_path):
                        observe(submodule, owner_path)
                if node.level == 0 and node.module == "importlib":
                    for alias in node.names:
                        if alias.name == "import_module":
                            import_module_aliases.add(
                                alias.asname or alias.name
                            )
                if node.level == 0 and node.module == "pytest":
                    pytest_aliases.add("pytest")
                if node.level == 0 and node.module == "pathlib":
                    for alias in node.names:
                        if alias.name == "Path":
                            path_constructor_aliases.add(
                                alias.asname or alias.name
                            )

        path_values: dict[str, set[Path]] = {
            "__file__": {(root / owner_path).absolute()}
        }

        def evaluate_paths(node: ast.AST) -> set[Path]:
            if isinstance(node, ast.Name):
                return set(path_values.get(node.id, ()))
            if (
                isinstance(node, ast.Constant)
                and isinstance(node.value, str)
            ):
                return {Path(node.value)}
            if isinstance(node, (ast.Tuple, ast.List)):
                return {
                    value
                    for item in node.elts
                    for value in evaluate_paths(item)
                }
            if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Div):
                return {
                    left / right
                    for left in evaluate_paths(node.left)
                    for right in evaluate_paths(node.right)
                }
            if isinstance(node, ast.Attribute) and node.attr == "parent":
                return {value.parent for value in evaluate_paths(node.value)}
            if isinstance(node, ast.Call):
                function = node.func
                is_path_constructor = (
                    isinstance(function, ast.Name)
                    and function.id in path_constructor_aliases
                ) or (
                    isinstance(function, ast.Attribute)
                    and function.attr == "Path"
                    and isinstance(function.value, ast.Name)
                    and function.value.id in pathlib_aliases
                )
                if is_path_constructor and len(node.args) == 1:
                    return evaluate_paths(node.args[0])
                if isinstance(function, ast.Attribute):
                    base = evaluate_paths(function.value)
                    if function.attr in {"resolve", "absolute"}:
                        return {
                            (
                                value.absolute()
                                if value.is_absolute()
                                else (root / value).absolute()
                            )
                            for value in base
                        }
                    if function.attr == "joinpath":
                        values = base
                        for argument in node.args:
                            values = {
                                left / right
                                for left in values
                                for right in evaluate_paths(argument)
                            }
                        return values
            return set()

        assignments = [
            node
            for node in runtime_nodes
            if isinstance(node, (ast.Assign, ast.AnnAssign, ast.For))
        ]
        for _ in range(len(assignments) + 1):
            changed = False
            for assignment in assignments:
                targets: list[ast.AST] = []
                values: set[Path] = set()
                if isinstance(assignment, ast.Assign):
                    targets = list(assignment.targets)
                    values = evaluate_paths(assignment.value)
                elif isinstance(assignment, ast.AnnAssign):
                    targets = [assignment.target]
                    if assignment.value is not None:
                        values = evaluate_paths(assignment.value)
                elif isinstance(assignment, ast.For):
                    targets = [assignment.target]
                    values = evaluate_paths(assignment.iter)
                if not values:
                    continue
                for target in targets:
                    if not isinstance(target, ast.Name):
                        continue
                    previous = path_values.get(target.id, set())
                    merged = previous | values
                    if merged != previous:
                        path_values[target.id] = merged
                        changed = True
            if not changed:
                break

        resolved_spec_count = 0
        exec_module_count = 0
        for node in runtime_nodes:
            if not isinstance(node, ast.Call):
                continue
            function = node.func
            if (
                isinstance(function, ast.Attribute)
                and function.attr == "spec_from_file_location"
            ):
                if len(node.args) < 2:
                    unresolved_dynamic_import_count += 1
                    continue
                candidates = evaluate_paths(node.args[1])
                resolved_paths: set[str] = set()
                for candidate in candidates:
                    absolute = (
                        candidate
                        if candidate.is_absolute()
                        else (root / candidate).absolute()
                    )
                    try:
                        relative = absolute.relative_to(root).as_posix()
                    except ValueError:
                        continue
                    target = child(relative)
                    if target is None:
                        continue
                    try:
                        target_stat = target.lstat()
                    except OSError:
                        continue
                    if stat.S_ISREG(target_stat.st_mode):
                        resolved_paths.add(relative)
                if not resolved_paths:
                    unresolved_dynamic_import_count += 1
                else:
                    for relative in sorted(resolved_paths):
                        observe(f"file:{relative}", owner_path)
                    resolved_spec_count += 1
                continue
            if (
                isinstance(function, ast.Attribute)
                and function.attr == "exec_module"
            ):
                exec_module_count += 1
                continue
            dynamic = (
                isinstance(function, ast.Name)
                and (
                    function.id == "__import__"
                    or function.id in import_module_aliases
                )
            ) or (
                isinstance(function, ast.Attribute)
                and isinstance(function.value, ast.Name)
                and (
                    (
                        function.value.id in importlib_aliases
                        and function.attr == "import_module"
                    )
                    or (
                        function.value.id in pytest_aliases
                        and function.attr == "importorskip"
                    )
                )
            )
            if not dynamic:
                continue
            if (
                node.args
                and isinstance(node.args[0], ast.Constant)
                and isinstance(node.args[0].value, str)
                and node.args[0].value
            ):
                observe(node.args[0].value, owner_path)
            else:
                unresolved_dynamic_import_count += 1
        if exec_module_count > resolved_spec_count:
            unresolved_dynamic_import_count += (
                exec_module_count - resolved_spec_count
            )

    try:
        declared_rows = {
            row["import_name"]: row
            for row in manifest["import_manifest"]
        }
        declared = {
            row["import_name"]: set(row["owner_paths"])
            for row in manifest["import_manifest"]
        }
    except (KeyError, TypeError):
        return ("READINESS_FORBIDDEN",)
    for import_name, owner_paths in observed_owners.items():
        row = declared_rows.get(import_name)
        if row is None:
            return ("READINESS_FORBIDDEN",)
        target = row.get("target_identity")
        if import_name.startswith("file:"):
            expected_path = import_name.removeprefix("file:")
            if (
                row.get("classification") != "FIRST_PARTY"
                or type(target) is not dict
                or target.get("path") != expected_path
            ):
                return ("READINESS_FORBIDDEN",)
            continue
        resolutions = {
            paths[0]
            for owner_path in owner_paths
            if (
                paths := module_source_paths(import_name, owner_path)
            )
        }
        unresolved_owners = [
            owner_path
            for owner_path in owner_paths
            if not module_source_paths(import_name, owner_path)
        ]
        if resolutions:
            if (
                unresolved_owners
                or len(resolutions) != 1
                or row.get("classification") != "FIRST_PARTY"
                or type(target) is not dict
                or target.get("path") != next(iter(resolutions))
            ):
                return ("READINESS_FORBIDDEN",)
            continue
        root_module = import_name.split(".", 1)[0]
        if root_module in stdlib_module_names:
            if (
                row.get("classification")
                != "STDLIB_BOUND_TO_PYTHON_RUNTIME"
                or type(target) is not dict
                or target.get("module_name") != import_name
            ):
                return ("READINESS_FORBIDDEN",)
            continue
        matching_prefixes = [
            prefix
            for prefix in module_mapping
            if import_name == prefix or import_name.startswith(f"{prefix}.")
        ]
        if not matching_prefixes:
            return ("READINESS_FORBIDDEN",)
        expected_distribution = module_mapping[
            max(matching_prefixes, key=len)
        ]
        if (
            row.get("classification")
            != "THIRD_PARTY_BOUND_TO_LOCKED_DISTRIBUTION"
            or type(target) is not dict
            or target.get("module_name") != import_name
            or target.get("normalized_distribution_name")
            != expected_distribution
        ):
            return ("READINESS_FORBIDDEN",)
    if (
        declared != observed_owners
        or manifest.get("unclassified_import_count") != 0
        or manifest.get("unresolved_dynamic_import_count")
        != unresolved_dynamic_import_count
        or unresolved_dynamic_import_count != 0
    ):
        return ("READINESS_FORBIDDEN",)
    return ()


def build_recovery_epoch002_d2_final_closure_preimage(
    source_closure: Mapping[str, Any],
) -> dict[str, Any] | None:
    """Extract the ordered D2 final-closure preimage."""

    try:
        result = {
            key: source_closure[key]
            for key in RECOVERY_EPOCH002_D2_FINAL_CLOSURE_PREIMAGE_KEYS
        }
    except (KeyError, TypeError):
        return None
    return result


def compute_recovery_epoch002_d2_final_closure_sha256(
    source_closure: Mapping[str, Any],
) -> str | None:
    preimage = build_recovery_epoch002_d2_final_closure_preimage(
        source_closure
    )
    return None if preimage is None else artifact_sha256(preimage)


def validate_recovery_epoch002_source_closure(
    source_closure: Mapping[str, Any],
) -> tuple[str, ...]:
    """Validate an actual exact15 source-closure artifact."""

    if type(source_closure) is not dict:
        return ("SOURCE_CLOSURE_INVALID",)
    if set(source_closure) != RECOVERY_EPOCH002_SOURCE_CLOSURE_KEYS:
        return ("SOURCE_CLOSURE_INVALID",)
    sha256_fields = (
        "detailed_design_sha256",
        "source_dependency_closure_sha256",
        "canonical_current_closure_sha256",
        "requirement_registry_sha256",
        "formal_node_registry_sha256",
        "proof_source_closure_sha256",
        "formal_test_manifest_sha256",
        "bootstrap_closure_sha256",
        "d2_final_closure_sha256",
        "source_closure_sha256",
    )
    if (
        source_closure.get("worktree_clean") is not True
        or source_closure.get("repository_full_name")
        != "MassyuRed/mashos-api"
        or source_closure.get("source_ref") != "refs/heads/main"
        or _SHA1_RE.fullmatch(
            str(source_closure.get("source_commit_sha1", ""))
        )
        is None
        or _SHA1_RE.fullmatch(
            str(source_closure.get("source_tree_sha1", ""))
        )
        is None
        or any(
            _SHA256_RE.fullmatch(str(source_closure.get(field, "")))
            is None
            for field in sha256_fields
        )
    ):
        return ("SOURCE_CLOSURE_INVALID",)
    expected_final = compute_recovery_epoch002_d2_final_closure_sha256(
        source_closure
    )
    if source_closure.get("d2_final_closure_sha256") != expected_final:
        return ("SOURCE_CLOSURE_INVALID",)
    if (
        source_closure.get("source_closure_sha256")
        != _hash_without(source_closure, "source_closure_sha256")
    ):
        return ("SOURCE_CLOSURE_INVALID",)
    return ()


def validate_recovery_epoch002_closure_state(
    state: Mapping[str, Any],
) -> tuple[str, ...]:
    """Reconcile event1/current closure roots and bootstrap completeness."""

    if type(state) is not dict:
        return ("EVENT1_REUSE_FORBIDDEN",)
    pairs = (
        ("event1_closure_sha256", "current_source_closure_sha256"),
        ("event1_proof_closure_sha256", "current_proof_closure_sha256"),
        (
            "event1_registry_closure_sha256",
            "current_registry_closure_sha256",
        ),
        (
            "event1_bootstrap_closure_sha256",
            "current_bootstrap_closure_sha256",
        ),
    )
    if any(
        _SHA256_RE.fullmatch(str(state.get(left, ""))) is None
        or _SHA256_RE.fullmatch(str(state.get(right, ""))) is None
        or state.get(left) != state.get(right)
        for left, right in pairs
    ):
        return ("EVENT1_REUSE_FORBIDDEN",)
    if (
        state.get("static_import_manifest_complete") is not True
        or state.get("third_party_distribution_mapping_complete") is not True
        or state.get("unclassified_import_count") != 0
        or state.get("unresolved_dynamic_import_count") != 0
    ):
        return ("READINESS_FORBIDDEN",)
    return ()


__all__ = [
    "RECOVERY_EPOCH002_SOURCE_CLOSURE_KEYS",
    "RECOVERY_EPOCH002_D2_FINAL_CLOSURE_PREIMAGE_KEYS",
    "RECOVERY_EPOCH002_BOOTSTRAP_CLOSURE_KEYS",
    "RECOVERY_EPOCH002_IMPORT_MANIFEST_ROW_KEYS",
    "RECOVERY_EPOCH002_FIRST_PARTY_IMPORT_TARGET_KEYS",
    "RECOVERY_EPOCH002_STDLIB_IMPORT_TARGET_KEYS",
    "RECOVERY_EPOCH002_THIRD_PARTY_IMPORT_TARGET_KEYS",
    "RECOVERY_EPOCH002_IMPORT_CLASSIFICATIONS",
    "RECOVERY_EPOCH002_INSTALLER_IDENTITY_CLASS",
    "RECOVERY_EPOCH002_OPERATIONAL_OWNER_PATHS",
    "validate_recovery_epoch002_bootstrap_manifest",
    "validate_recovery_epoch002_operational_bootstrap_manifest",
    "validate_recovery_epoch002_formal_node_registry",
    "validate_recovery_epoch002_operational_source_manifest",
    "build_recovery_epoch002_d2_final_closure_preimage",
    "compute_recovery_epoch002_d2_final_closure_sha256",
    "validate_recovery_epoch002_source_closure",
    "validate_recovery_epoch002_closure_state",
]
