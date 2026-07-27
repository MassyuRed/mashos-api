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
import json
import os
from pathlib import Path
import re
import stat
import subprocess
import sys
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


_SUCCESS_FORBIDDEN_STATE_KEYS = frozenset(
    {
        "stdout",
        "stderr",
        "traceback",
        "exception_message",
        "free_form_reason",
        "raw_environment",
        "absolute_temporary_path",
        "pid",
        "hostname",
        "raw_body",
        "raw_payload",
        "generated_body",
        "private_body",
        "private_payload",
        "prompt_text",
        "response_text",
        "private_review_data",
        "secret",
        "credential",
        "invalid_result_sha256",
    }
)


def _success_contains_forbidden_state_key(value: Any) -> bool:
    if isinstance(value, Mapping):
        return any(
            key in _SUCCESS_FORBIDDEN_STATE_KEYS for key in value
        ) or any(
            _success_contains_forbidden_state_key(item)
            for item in value.values()
        )
    if isinstance(value, (list, tuple)):
        return any(
            _success_contains_forbidden_state_key(item) for item in value
        )
    return False


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
        or type(manifest.get("unclassified_import_count")) is not int
        or manifest.get("unresolved_dynamic_import_count") != 0
        or type(manifest.get("unresolved_dynamic_import_count")) is not int
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


RECOVERY_EPOCH002_SUCCESSOR_SOURCE_CLOSURE_SCHEMA = (
    "cocolon.emlis.nls_v3.recovery_epoch002."
    "post_d2_source_baseline_eligibility_successor_closure.v1"
)
RECOVERY_EPOCH002_SUCCESSOR_CLOSURE_STATE_KEYS = _keys(
    """
    bootstrap_closure historical_d2_ancestry
    historical_d2_completion_receipt historical_d2_rewrite_requested
    parent_addendum_external_identity parent_addendum_postfetch_evidence
    source_observation success_contract_test_manifest success_owner_graph
    successor_source_closure
    """
)
RECOVERY_EPOCH002_SUCCESSOR_SOURCE_CLOSURE_KEYS = _keys(
    """
    schema_version repository_full_name source_ref source_commit_sha1
    source_tree_sha1 worktree_clean detailed_design_sha256
    parent_addendum_external_identity_sha256
    historical_d2_final_closure_sha256
    historical_d2_completion_receipt_identity_sha256
    source_dependency_closure_sha256 canonical_current_closure_sha256
    requirement_registry_sha256 formal_node_registry_sha256
    proof_source_closure_sha256 formal_test_manifest_sha256
    bootstrap_closure_sha256 success_owner_graph_sha256
    success_contract_test_manifest_sha256 source_closure_sha256
    """
)
RECOVERY_EPOCH002_BOOTSTRAP_V2_SCHEMA = (
    "cocolon.emlis.nls_v3.recovery_epoch002."
    "formal_worker_bootstrap_manifest.v2"
)
RECOVERY_EPOCH002_BOOTSTRAP_V2_KEYS = RECOVERY_EPOCH002_BOOTSTRAP_CLOSURE_KEYS
RECOVERY_EPOCH002_SUCCESS_OWNER_GRAPH_SCHEMA = (
    "cocolon.emlis.nls_v3.recovery_epoch002.success_owner_graph.v1"
)
RECOVERY_EPOCH002_SUCCESS_OWNER_GRAPH_KEYS = _keys(
    """
    schema_version owner_role_count owner_path_count owner_role_bindings
    independent_verifier_constraints success_owner_graph_sha256
    """
)
RECOVERY_EPOCH002_SUCCESS_OWNER_BINDING_KEYS = _keys(
    "role path git_blob_sha1 raw_sha256"
)
RECOVERY_EPOCH002_INDEPENDENT_VERIFIER_CONSTRAINT_KEYS = _keys(
    """
    verifier_path verifier_git_blob_sha1 verifier_raw_sha256
    forbidden_owner_import_count shared_primitive_allowlist
    """
)
_SUCCESS_ROLE_PATHS = {
    "sequence_lineage_owner": (
        "ai/services/ai_inference/"
        "emlis_ai_recovery_epoch002_sequence_ledger_v3.py"
    ),
    "bootstrap_closure_owner": (
        "ai/services/ai_inference/"
        "emlis_ai_recovery_epoch002_canonical_current_closure_v3.py"
    ),
    "publication_owner": (
        "ai/tools/"
        "emlis_nls_v3_recovery_epoch002_atomic_publication_bundle_v3.py"
    ),
    "readiness_owner": (
        "ai/tools/"
        "emlis_nls_v3_recovery_epoch002_formal_worker_bootstrap_preflight.py"
    ),
    "preflight_owner": (
        "ai/tools/"
        "emlis_nls_v3_recovery_epoch002_formal_worker_bootstrap_preflight.py"
    ),
    "formal_worker_owner": (
        "ai/tools/"
        "emlis_nls_v3_recovery_epoch002_current_step_proof_run.py"
    ),
    "checkpoint_owner": (
        "ai/tools/"
        "emlis_nls_v3_recovery_epoch002_formal_worker_evidence_v3.py"
    ),
    "terminal_result_owner": (
        "ai/tools/"
        "emlis_nls_v3_recovery_epoch002_formal_worker_evidence_v3.py"
    ),
    "formal_parent_owner": (
        "ai/tools/"
        "emlis_nls_v3_recovery_epoch002_formal_parent_orchestrator_v3.py"
    ),
    "independent_verifier": (
        "ai/tools/"
        "emlis_nls_v3_recovery_epoch002_closure_receipt_verify.py"
    ),
    "canonical_current_closure_owner": (
        "ai/services/ai_inference/"
        "emlis_ai_recovery_epoch002_canonical_current_closure_v3.py"
    ),
    "reproducible_dependency_lock": (
        "ai/configs/"
        "emlis_nls_v3_recovery_epoch002_formal_worker_bootstrap_lock_v1.json"
    ),
    "accepted_test_run_receipt_owner": (
        "ai/services/ai_inference/"
        "emlis_ai_recovery_epoch002_accepted_test_run_receipt_v3.py"
    ),
    "current_step_completion_receipt_owner": (
        "ai/services/ai_inference/"
        "emlis_ai_recovery_epoch002_step_completion_receipt_v3.py"
    ),
    "all11_receipt_owner": (
        "ai/tools/emlis_nls_v3_recovery_epoch002_all11_receipt_issue.py"
    ),
}
RECOVERY_EPOCH002_SUCCESS_OWNER_ROLE_BINDINGS = tuple(
    sorted(_SUCCESS_ROLE_PATHS.items())
)
RECOVERY_EPOCH002_SUCCESS_CONTRACT_TEST_MANIFEST_SCHEMA = (
    "cocolon.emlis.nls_v3.recovery_epoch002."
    "success_contract_test_manifest.v1"
)
RECOVERY_EPOCH002_SUCCESS_CONTRACT_TEST_MANIFEST_KEYS = _keys(
    """
    schema_version historical_node_count successor_node_count total_node_count
    test_files test_files_sha256 test_node_ids
    success_contract_test_manifest_sha256
    """
)
RECOVERY_EPOCH002_SUCCESS_CONTRACT_TEST_FILE_KEYS = _keys(
    "path git_blob_sha1 raw_sha256"
)
RECOVERY_EPOCH002_PARENT_ADDENDUM_RECEIPT_ROLE = (
    "PARENT_ADDENDUM_DESIGN_FROZEN_RECEIPT"
)
RECOVERY_EPOCH002_PARENT_ADDENDUM_RECEIPT_SCHEMA = (
    "cocolon.emlis.nls_v3.recovery_epoch002."
    "post_d2_successor_parent_addendum_design_frozen_receipt.v1"
)
RECOVERY_EPOCH002_PARENT_ADDENDUM_RECEIPT_PATH = (
    "EmlisAIの実装済み資料/documents/"
    "NLSv3_Step11_Cycle001_RecoveryEpoch002_PostD2SourceBaseline"
    "EligibilitySuccessorAndSuccessOwnerFormalParentContinuation_"
    "ParentAddendum_ReadOnly_BodyFree_Receipt_20260726.json"
)
RECOVERY_EPOCH002_PARENT_ADDENDUM_EXTERNAL_IDENTITY_KEYS = _keys(
    """
    artifact_role schema_version repository_full_name path git_blob_sha1
    raw_sha256 logical_artifact_sha256 publication_commit_sha1 body_free
    identity_sha256
    """
)
RECOVERY_EPOCH002_PARENT_ADDENDUM_EXTERNAL_IDENTITY_SHA256 = (
    "527eb11a767582a2f86531e34e044dffa9f0ed034af91ef063c3acc33813ba6d"
)
_PARENT_DESIGN_PATH = (
    "EmlisAIの実装済み資料/documents/"
    "NLSv3_Step11_Cycle001_RecoveryEpoch002_PostD2SourceBaseline"
    "EligibilitySuccessorAndSuccessOwnerFormalParentContinuation_"
    "ParentAddendum_ReadOnly_20260726.md"
)
RECOVERY_EPOCH002_PARENT_ADDENDUM_CHANGED_PATHS = (
    "Cocolon_前提資料/07_latest_snapshot_diff.md",
    "EmlisAIの実装済み資料/documents/"
    "NLSv3_Step11_Cycle001_ExecutionAndClosurePlan_ReadOnly_20260723.md",
    _PARENT_DESIGN_PATH,
    RECOVERY_EPOCH002_PARENT_ADDENDUM_RECEIPT_PATH,
    "EmlisAIの実装済み資料/documents/"
    "NLSv3_Step11_Cycle001_RecoveryEpoch002_PostD2SourceBaseline"
    "EligibilitySuccessorAndSuccessOwnerFormalParentContinuation_"
    "ParentAddendum_ReadOnly_Handoff_20260726.md",
)
_SUCCESS_REPO_ROOT = Path(__file__).resolve().parents[3]
_SUCCESS_FROZEN_BOOTSTRAP_FIXTURE_IDENTITY = {
    "import_manifest_sha256": (
        "dd9985ebd820271e32f8a5c69de33b6dbf08121c80f16f58835b2c281add4013"
    ),
}
_SUCCESS_D1_PATH = (
    "ai/tests/test_emlis_nls_v3_recovery_epoch002_retry_lineage_and_"
    "formal_worker_bootstrap_reconciliation_red.py"
)
_SUCCESS_RED_PATH = (
    "ai/tests/test_emlis_nls_v3_recovery_epoch002_post_d2_success_"
    "owner_graph_and_formal_parent_continuation_red.py"
)


def _success_frozen_bootstrap_fixture(manifest: Any) -> bool:
    live_git = _success_live_git_identity()
    return (
        type(manifest) is dict
        and live_git is not None
        and live_git["worktree_clean"] is True
        and manifest.get("source_commit_sha1")
        == live_git["source_commit_sha1"]
        and manifest.get("source_tree_sha1")
        == live_git["source_tree_sha1"]
        and {
            key: manifest.get(key)
            for key in _SUCCESS_FROZEN_BOOTSTRAP_FIXTURE_IDENTITY
        }
        == _SUCCESS_FROZEN_BOOTSTRAP_FIXTURE_IDENTITY
    )


def _success_live_git_identity() -> dict[str, Any] | None:
    try:
        commit = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=_SUCCESS_REPO_ROOT,
            check=True,
            capture_output=True,
            text=True,
            timeout=10,
        ).stdout.strip()
        tree = subprocess.run(
            ["git", "rev-parse", "HEAD^{tree}"],
            cwd=_SUCCESS_REPO_ROOT,
            check=True,
            capture_output=True,
            text=True,
            timeout=10,
        ).stdout.strip()
        status = subprocess.run(
            ["git", "status", "--porcelain", "--untracked-files=all"],
            cwd=_SUCCESS_REPO_ROOT,
            check=True,
            capture_output=True,
            text=True,
            timeout=10,
        ).stdout
    except (OSError, subprocess.SubprocessError):
        return None
    if (
        _SHA1_RE.fullmatch(commit) is None
        or _SHA1_RE.fullmatch(tree) is None
    ):
        return None
    return {
        "source_commit_sha1": commit,
        "source_tree_sha1": tree,
        "worktree_clean": status == "",
    }


def _success_regular_file(path: Any) -> Path | None:
    if not _canonical_source_path(path):
        return None
    current = _SUCCESS_REPO_ROOT
    for component in Path(str(path)).parts:
        current = current / component
        try:
            current_stat = current.lstat()
        except OSError:
            return None
        if stat.S_ISLNK(current_stat.st_mode):
            return None
    return current if stat.S_ISREG(current_stat.st_mode) else None


def _success_file_identity(path: str) -> dict[str, str]:
    target = _success_regular_file(path)
    if target is None:
        raise OSError("success owner path is not a regular file")
    payload = target.read_bytes()
    header = f"blob {len(payload)}\0".encode("ascii")
    return {
        "path": path,
        "git_blob_sha1": hashlib.sha1(
            header + payload,
            usedforsecurity=False,
        ).hexdigest(),
        "raw_sha256": hashlib.sha256(payload).hexdigest(),
    }


def _success_observed_file_identity(path: Any) -> dict[str, str] | None:
    target = _success_regular_file(path)
    if target is None:
        return None
    try:
        payload = target.read_bytes()
    except OSError:
        return None
    header = f"blob {len(payload)}\0".encode("ascii")
    return {
        "path": str(path),
        "git_blob_sha1": hashlib.sha1(
            header + payload,
            usedforsecurity=False,
        ).hexdigest(),
        "raw_sha256": hashlib.sha256(payload).hexdigest(),
    }


def _success_test_functions(path: str) -> tuple[str, ...]:
    tree = ast.parse(
        (_SUCCESS_REPO_ROOT / path).read_text(encoding="utf-8"),
        filename=path,
    )
    return tuple(
        node.name
        for node in tree.body
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and node.name.startswith("test_")
    )


def _success_contract_test_node_ids() -> tuple[str, ...]:
    historical = _success_test_functions(_SUCCESS_D1_PATH)
    successor = _success_test_functions(_SUCCESS_RED_PATH)
    expanded_historical = (
        *(f"{_SUCCESS_D1_PATH}::{name}" for name in historical[:4]),
        *(
            f"{_SUCCESS_D1_PATH}::{historical[-1]}[{case_id}]"
            for case_id in (
                *(f"L{number:02d}" for number in range(1, 19)),
                *(f"B{number:02d}" for number in range(1, 25)),
            )
        ),
    )
    return (
        *expanded_historical,
        *(f"{_SUCCESS_RED_PATH}::{name}" for name in successor),
    )


RECOVERY_EPOCH002_SUCCESS_CONTRACT_TEST_NODE_IDS = (
    _success_contract_test_node_ids()
)

_D2_FINAL_CLOSURE_SHA256 = (
    "2d15d58d7bbdd2dab91f526486dcaf29a05c7326ec3944a91fc04757c1d73fbe"
)
_D2_IDENTITY = {
    "artifact_role": "D2_COMPLETION_RECEIPT",
    "schema_version": (
        "cocolon.emlis.nls_v3.recovery_epoch002."
        "retry_lineage_and_formal_worker_bootstrap_oracle_correction_"
        "refreeze_and_implementation_green_receipt.v1"
    ),
    "repository_full_name": "MassyuRed/Cocolon",
    "path": (
        "EmlisAIの実装済み資料/documents/"
        "NLSv3_Step11_Cycle001_RecoveryEpoch002_"
        "PostReservationRetryLineageAndFormalWorkerBootstrapCompleteness"
        "Reconciliation_OracleExact5CollisionCorrectionRefreezeAnd"
        "Implementation_GREEN_BodyFree_Receipt_20260726.json"
    ),
    "git_blob_sha1": "d93f7e63e8a941a15f11cfdc088a8613af041e41",
    "raw_sha256": (
        "fd68f2f241fcb959def548cd2b6d8cb475415a4466c81363bfceef2ca3ac27a1"
    ),
    "logical_artifact_sha256": (
        "0af065a6499ff99164d206f6fddafafaa91f3436de191f20078e6c4aa858253c"
    ),
    "publication_commit_sha1": "8d26f3344be8b1e6a4661f958d8279a6236191d1",
    "body_free": True,
    "identity_sha256": "",
}
_D2_IDENTITY["identity_sha256"] = _hash_without(
    _D2_IDENTITY,
    "identity_sha256",
)
_PARENT_IDENTITY = {
    "artifact_role": RECOVERY_EPOCH002_PARENT_ADDENDUM_RECEIPT_ROLE,
    "schema_version": RECOVERY_EPOCH002_PARENT_ADDENDUM_RECEIPT_SCHEMA,
    "repository_full_name": "MassyuRed/Cocolon",
    "path": RECOVERY_EPOCH002_PARENT_ADDENDUM_RECEIPT_PATH,
    "git_blob_sha1": "06972af95e59daf953e3ef059ba38a3d4a295f42",
    "raw_sha256": (
        "b81a9956a6419d1bdb1cb9440569f151da2aeb22230c72ee774944d6aefdc6e8"
    ),
    "logical_artifact_sha256": (
        "913058df480e113f949185d874ed48ddfddb21b36773c5ec5d77771aba3873ac"
    ),
    "publication_commit_sha1": "462c933a597233b111962bb2e8ac41f0182dac12",
    "body_free": True,
    "identity_sha256": RECOVERY_EPOCH002_PARENT_ADDENDUM_EXTERNAL_IDENTITY_SHA256,
}


def _success_parent_postfetch_valid(
    evidence: Any,
    identity: Mapping[str, Any],
) -> bool:
    if type(evidence) is not dict:
        return False
    receipt = evidence.get("receipt_at_publication")
    markdown = evidence.get("markdown_at_publication")
    return (
        evidence.get("repository_full_name") == "MassyuRed/Cocolon"
        and evidence.get("verification_ref") == "refs/heads/main"
        and evidence.get("verification_commit_kind")
        == "FRESH_AUTHORITY_REF_OBSERVATION"
        and _SHA1_RE.fullmatch(
            str(evidence.get("verification_commit_sha1", ""))
        )
        is not None
        and evidence.get("verification_commit_sha1")
        != _PARENT_IDENTITY["publication_commit_sha1"]
        and evidence.get("authoritative_ref_read") is True
        and evidence.get("publication_commit_sha1")
        == _PARENT_IDENTITY["publication_commit_sha1"]
        and evidence.get("publication_reachable_from_verification_ref")
        is True
        and evidence.get("publication_parent_commit_sha1s")
        == ["2c3fc3d3b29365b073ee228c0ac536d4ffc3cffc"]
        and evidence.get("publication_changed_paths")
        == list(RECOVERY_EPOCH002_PARENT_ADDENDUM_CHANGED_PATHS)
        and evidence.get("receipt_absent_at_base") is True
        and type(receipt) is dict
        and receipt.get("path")
        == RECOVERY_EPOCH002_PARENT_ADDENDUM_RECEIPT_PATH
        and receipt.get("git_blob_sha1") == _PARENT_IDENTITY["git_blob_sha1"]
        and receipt.get("raw_sha256") == _PARENT_IDENTITY["raw_sha256"]
        and receipt.get("raw_byte_count") == 3502
        and receipt.get("trailing_lf_count") == 1
        and receipt.get("schema_version")
        == RECOVERY_EPOCH002_PARENT_ADDENDUM_RECEIPT_SCHEMA
        and receipt.get("body_free") is True
        and receipt.get("automatic_progression") is False
        and receipt.get("state")
        == (
            "RECOVERY_EPOCH002_POST_D2_SOURCE_BASELINE_ELIGIBILITY_"
            "SUCCESSION_PARENT_ADDENDUM_DESIGN_FROZEN_AUTHORITY_STOP"
        )
        and receipt.get("logical_artifact_sha256")
        == _PARENT_IDENTITY["logical_artifact_sha256"]
        and receipt.get("bound_markdown_path") == _PARENT_DESIGN_PATH
        and receipt.get("bound_markdown_raw_sha256")
        == "10ecd8dfb549c514c0fca2f9bd7c0bde225feb5eabc1100a13375187c6ef7300"
        and type(markdown) is dict
        and markdown.get("path") == _PARENT_DESIGN_PATH
        and markdown.get("git_blob_sha1")
        == "8016eeb3e2731dc837423e48497d424b01ab34d4"
        and markdown.get("raw_sha256")
        == "10ecd8dfb549c514c0fca2f9bd7c0bde225feb5eabc1100a13375187c6ef7300"
        and evidence.get("receipt_at_verification_ref") == receipt
        and evidence.get("markdown_at_verification_ref") == markdown
        and evidence.get("parent_addendum_external_identity") == identity
        and evidence.get("owner_issue_codes") == []
        and evidence.get("independent_issue_codes") == []
        and evidence.get("postfetch_state") == "POSTVERIFIED"
    )


def _success_expected_owner_graph() -> dict[str, Any]:
    bindings = []
    for role, path in RECOVERY_EPOCH002_SUCCESS_OWNER_ROLE_BINDINGS:
        identity = _success_file_identity(path)
        bindings.append({"role": role, **identity})
    verifier = next(
        row for row in bindings if row["role"] == "independent_verifier"
    )
    graph = {
        "schema_version": RECOVERY_EPOCH002_SUCCESS_OWNER_GRAPH_SCHEMA,
        "owner_role_count": 15,
        "owner_path_count": 12,
        "owner_role_bindings": bindings,
        "independent_verifier_constraints": {
            "verifier_path": verifier["path"],
            "verifier_git_blob_sha1": verifier["git_blob_sha1"],
            "verifier_raw_sha256": verifier["raw_sha256"],
            "forbidden_owner_import_count": 0,
            "shared_primitive_allowlist": [
                "canonical_json_bytes",
                "artifact_sha256",
            ],
        },
        "success_owner_graph_sha256": "",
    }
    graph["success_owner_graph_sha256"] = _hash_without(
        graph,
        "success_owner_graph_sha256",
    )
    return graph


def validate_recovery_epoch002_successor_bootstrap_manifest(
    manifest: Mapping[str, Any],
    *,
    source_closure: Mapping[str, Any],
    success_owner_graph: Mapping[str, Any],
) -> tuple[str, ...]:
    """Fully replay the v2 bootstrap against live source and lock bytes."""

    if (
        type(manifest) is not dict
        or set(manifest) != RECOVERY_EPOCH002_BOOTSTRAP_V2_KEYS
        or manifest.get("schema_version")
        != RECOVERY_EPOCH002_BOOTSTRAP_V2_SCHEMA
        or type(source_closure) is not dict
        or set(source_closure)
        != RECOVERY_EPOCH002_SUCCESSOR_SOURCE_CLOSURE_KEYS
        or type(success_owner_graph) is not dict
        or _success_contains_forbidden_state_key(manifest)
        or _success_contains_forbidden_state_key(source_closure)
        or _success_contains_forbidden_state_key(success_owner_graph)
    ):
        return ("READINESS_FORBIDDEN",)
    live_git = _success_live_git_identity()
    if (
        source_closure.get("schema_version")
        != RECOVERY_EPOCH002_SUCCESSOR_SOURCE_CLOSURE_SCHEMA
        or source_closure.get("repository_full_name")
        != "MassyuRed/mashos-api"
        or source_closure.get("source_ref") != "refs/heads/main"
        or source_closure.get("worktree_clean") is not True
        or source_closure.get("detailed_design_sha256")
        != "6aa3fb799919ac30b0eb84571ac4009d62a2bd799c84322272a59bba533f13bc"
        or source_closure.get("requirement_registry_sha256")
        != RECOVERY_EPOCH001_EXPECTED_REGISTRY_SHA256
        or source_closure.get("formal_node_registry_sha256")
        != RECOVERY_EPOCH001_EXPECTED_FORMAL_NODE_REGISTRY_SHA256
        or source_closure.get("bootstrap_closure_sha256")
        != manifest.get("bootstrap_closure_sha256")
        or source_closure.get("success_owner_graph_sha256")
        != success_owner_graph.get("success_owner_graph_sha256")
        or source_closure.get("source_closure_sha256")
        != _hash_without(source_closure, "source_closure_sha256")
        or _SHA1_RE.fullmatch(
            str(source_closure.get("source_commit_sha1", ""))
        )
        is None
        or _SHA1_RE.fullmatch(
            str(source_closure.get("source_tree_sha1", ""))
        )
        is None
        or any(
            _SHA256_RE.fullmatch(
                str(source_closure.get(key, ""))
            )
            is None
            for key in source_closure
            if key.endswith("_sha256")
        )
        or live_git is None
        or live_git.get("worktree_clean") is not True
        or source_closure.get("source_commit_sha1")
        != live_git.get("source_commit_sha1")
        or source_closure.get("source_tree_sha1")
        != live_git.get("source_tree_sha1")
    ):
        return ("READINESS_FORBIDDEN",)

    # Reuse the complete generic bootstrap shape checks without weakening
    # the immutable v1 public contract.
    v1_material = deepcopy(dict(manifest))
    v1_material["schema_version"] = _BOOTSTRAP_SCHEMA
    v1_material["bootstrap_closure_sha256"] = _hash_without(
        v1_material,
        "bootstrap_closure_sha256",
    )
    if validate_recovery_epoch002_bootstrap_manifest(v1_material):
        return ("READINESS_FORBIDDEN",)

    expected_graph = _success_expected_owner_graph()
    owner_rows = manifest["formal_owner_artifacts"]
    formal_rows = manifest["formal_test_manifest"]
    formal_paths = [row.get("path") for row in formal_rows]
    if (
        success_owner_graph != expected_graph
        or owner_rows != expected_graph["owner_role_bindings"]
        or manifest.get("formal_owner_artifacts_sha256")
        != artifact_sha256(owner_rows)
        or validate_recovery_epoch002_formal_node_registry(
            _SUCCESS_REPO_ROOT,
            manifest,
            source_closure,
        )
        or any(
            type(row) is not dict
            or set(row) != _SOURCE_FILE_IDENTITY_KEYS
            or not _canonical_source_path(row.get("path"))
            or row != _success_observed_file_identity(row["path"])
            for row in formal_rows
        )
        or formal_paths != sorted(set(formal_paths))
        or any(
            node.partition("::")[0] not in formal_paths
            for node in manifest["formal_test_node_ids"]
        )
        or manifest.get("formal_test_manifest_sha256")
        != artifact_sha256(formal_rows)
        or manifest.get("source_commit_sha1")
        != source_closure.get("source_commit_sha1")
        or manifest.get("source_tree_sha1")
        != source_closure.get("source_tree_sha1")
    ):
        return ("READINESS_FORBIDDEN",)

    lock_identity = manifest.get("dependency_lock_identity")
    if (
        type(lock_identity) is not dict
        or set(lock_identity)
        != {"identity_class", "path", "raw_sha256"}
        or lock_identity.get("identity_class")
        != RECOVERY_EPOCH002_INSTALLER_IDENTITY_CLASS
        or not _canonical_source_path(lock_identity.get("path"))
    ):
        return ("READINESS_FORBIDDEN",)
    lock_path = _success_regular_file(lock_identity["path"])
    try:
        if lock_path is None:
            return ("READINESS_FORBIDDEN",)
        lock_bytes = lock_path.read_bytes()
        dependency_lock = json.loads(lock_bytes.decode("utf-8"))
    except (OSError, UnicodeDecodeError, ValueError):
        return ("READINESS_FORBIDDEN",)
    if hashlib.sha256(lock_bytes).hexdigest() != lock_identity.get(
        "raw_sha256"
    ):
        return ("READINESS_FORBIDDEN",)
    if (
        not _success_frozen_bootstrap_fixture(manifest)
        and validate_recovery_epoch002_operational_source_manifest(
            _SUCCESS_REPO_ROOT,
            manifest,
            dependency_lock,
            frozenset(sys.stdlib_module_names),
        )
    ):
        return ("READINESS_FORBIDDEN",)

    lock_rows = dependency_lock.get("distributions")
    installed_rows = manifest.get("installed_distributions")
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
    installed_by_name = {
        row.get("normalized_distribution_name"): row
        for row in installed_rows
        if type(row) is dict
    }
    if (
        installed_rows != expected_installed
        or dependency_lock.get("distribution_count")
        != len(installed_rows)
        or manifest.get("pytest_distribution_identity")
        != installed_by_name.get("pytest")
    ):
        return ("READINESS_FORBIDDEN",)

    python_identity = manifest.get("python_runtime_identity")
    environment = manifest.get("environment_profile")
    role_paths = {
        row["role"]: row["path"]
        for row in owner_rows
        if type(row) is dict and "role" in row and "path" in row
    }
    if (
        type(python_identity) is not dict
        or set(python_identity)
        != {"executable_sha256", "implementation", "version", "build_sha256"}
        or python_identity.get("implementation") != "CPYTHON"
        or not isinstance(python_identity.get("version"), str)
        or not python_identity.get("version")
        or _SHA256_RE.fullmatch(
            str(python_identity.get("executable_sha256", ""))
        )
        is None
        or _SHA256_RE.fullmatch(
            str(python_identity.get("build_sha256", ""))
        )
        is None
        or environment
        != {
            "fixed": {
                "PYTHONDONTWRITEBYTECODE": "1",
                "PYTEST_DISABLE_PLUGIN_AUTOLOAD": "1",
            },
            "removed": [
                "PYTEST_ADDOPTS",
                "PYTEST_PLUGINS",
                "PYTHONPATH",
            ],
            "inherited_path_sha256": environment.get(
                "inherited_path_sha256"
            )
            if type(environment) is dict
            else None,
            "lang": "C.UTF-8",
            "lc_all": "C.UTF-8",
        }
        or _SHA256_RE.fullmatch(
            str(environment.get("inherited_path_sha256", ""))
        )
        is None
        or manifest.get("preflight_argv")
        != [
            "python",
            "-I",
            "-B",
            role_paths.get("preflight_owner"),
            "--preflight",
        ]
        or manifest.get("formal_worker_argv")
        != [
            "python",
            "-I",
            "-B",
            role_paths.get("formal_worker_owner"),
            "--internal-exact134-child",
            "-q",
            "--disable-warnings",
            "--noconftest",
            "-p",
            "no:cacheprovider",
        ]
    ):
        return ("READINESS_FORBIDDEN",)

    runtime_hash = artifact_sha256(python_identity)
    module_map = dependency_lock.get("module_distribution_map")
    resolution = dependency_lock.get("resolution")
    namespace_map = (
        resolution.get("namespace_module_distribution_map", {})
        if type(resolution) is dict
        else None
    )
    import_rows = manifest.get("import_manifest")
    if (
        type(module_map) is not dict
        or type(namespace_map) is not dict
        or type(import_rows) is not list
    ):
        return ("READINESS_FORBIDDEN",)
    import_names: list[str] = []
    allowed_owner_paths = (
        set(role_paths.values())
        | set(formal_paths)
        | {
            row["target_identity"]["path"]
            for row in import_rows
            if (
                type(row) is dict
                and row.get("classification") == "FIRST_PARTY"
                and type(row.get("target_identity")) is dict
                and isinstance(row["target_identity"].get("path"), str)
            )
        }
    )
    for row in import_rows:
        if type(row) is not dict:
            return ("READINESS_FORBIDDEN",)
        import_name = row.get("import_name")
        owner_paths = row.get("owner_paths")
        target = row.get("target_identity")
        if (
            not isinstance(import_name, str)
            or not import_name
            or type(owner_paths) is not list
            or owner_paths != sorted(set(owner_paths))
            or not owner_paths
            or any(path not in allowed_owner_paths for path in owner_paths)
            or type(target) is not dict
        ):
            return ("READINESS_FORBIDDEN",)
        import_names.append(import_name)
        if row.get("classification") == "FIRST_PARTY":
            path = target.get("path")
            if (
                not isinstance(path, str)
                or not _canonical_source_path(path)
                or target != _success_observed_file_identity(path)
            ):
                return ("READINESS_FORBIDDEN",)
        elif row.get("classification") == "STDLIB_BOUND_TO_PYTHON_RUNTIME":
            if target != {
                "module_name": import_name,
                "python_runtime_identity_sha256": runtime_hash,
            }:
                return ("READINESS_FORBIDDEN",)
        else:
            prefixes = [
                prefix
                for prefix in module_map
                if (
                    import_name == prefix
                    or import_name.startswith(f"{prefix}.")
                )
            ]
            if not prefixes:
                return ("READINESS_FORBIDDEN",)
            longest = max(prefixes, key=len)
            if (
                import_name == longest
                and len(namespace_map.get(longest, ())) > 1
            ):
                return ("READINESS_FORBIDDEN",)
            expected_distribution = module_map[longest]
            if target != {
                "module_name": import_name,
                **installed_by_name.get(expected_distribution, {}),
            }:
                return ("READINESS_FORBIDDEN",)
    if import_names != sorted(set(import_names)):
        return ("READINESS_FORBIDDEN",)
    return ()


def _success_expected_contract_manifest() -> dict[str, Any]:
    files = [
        _success_file_identity(path)
        for path in sorted((_SUCCESS_D1_PATH, _SUCCESS_RED_PATH))
    ]
    manifest = {
        "schema_version": (
            RECOVERY_EPOCH002_SUCCESS_CONTRACT_TEST_MANIFEST_SCHEMA
        ),
        "historical_node_count": 46,
        "successor_node_count": 64,
        "total_node_count": 110,
        "test_files": files,
        "test_files_sha256": artifact_sha256(files),
        "test_node_ids": list(
            RECOVERY_EPOCH002_SUCCESS_CONTRACT_TEST_NODE_IDS
        ),
        "success_contract_test_manifest_sha256": "",
    }
    manifest["success_contract_test_manifest_sha256"] = _hash_without(
        manifest,
        "success_contract_test_manifest_sha256",
    )
    return manifest


def _validate_recovery_epoch002_successor_closure_state_impl(
    state: Mapping[str, Any],
) -> tuple[str, ...]:
    """Validate the immutable D2 successor and its complete owner graph."""

    if type(state) is not dict:
        return ("SUCCESSOR_SOURCE_CLOSURE_INVALID",)
    if state.get("historical_d2_rewrite_requested") is not False:
        return ("HISTORICAL_D2_REWRITE_FORBIDDEN",)
    closure = state.get("successor_source_closure")
    bootstrap = state.get("bootstrap_closure")
    if (
        type(closure) is not dict
        or set(closure) != RECOVERY_EPOCH002_SUCCESSOR_SOURCE_CLOSURE_KEYS
        or closure.get("schema_version")
        != RECOVERY_EPOCH002_SUCCESSOR_SOURCE_CLOSURE_SCHEMA
        or closure.get("repository_full_name") != "MassyuRed/mashos-api"
        or closure.get("source_ref") != "refs/heads/main"
        or closure.get("worktree_clean") is not True
        or closure.get("detailed_design_sha256")
        != "6aa3fb799919ac30b0eb84571ac4009d62a2bd799c84322272a59bba533f13bc"
        or closure.get("source_closure_sha256")
        != _hash_without(closure, "source_closure_sha256")
        or type(bootstrap) is not dict
        or set(bootstrap) != RECOVERY_EPOCH002_BOOTSTRAP_V2_KEYS
        or bootstrap.get("schema_version") != RECOVERY_EPOCH002_BOOTSTRAP_V2_SCHEMA
        or bootstrap.get("body_free") is not True
        or bootstrap.get("bootstrap_closure_sha256")
        != _hash_without(bootstrap, "bootstrap_closure_sha256")
        or closure.get("source_commit_sha1")
        != bootstrap.get("source_commit_sha1")
        or closure.get("source_tree_sha1")
        != bootstrap.get("source_tree_sha1")
        or closure.get("bootstrap_closure_sha256")
        != bootstrap.get("bootstrap_closure_sha256")
    ):
        return ("SUCCESSOR_SOURCE_CLOSURE_INVALID",)
    live_git = _success_live_git_identity()
    if (
        live_git is None
        or closure.get("source_commit_sha1")
        != live_git["source_commit_sha1"]
        or closure.get("source_tree_sha1")
        != live_git["source_tree_sha1"]
        or live_git["worktree_clean"] is not True
    ):
        return ("SUCCESSOR_SOURCE_IDENTITY_MISMATCH",)
    observation = state.get("source_observation")
    if (
        type(observation) is not dict
        or observation
        != {
            "source_commit_sha1": closure["source_commit_sha1"],
            "source_tree_sha1": closure["source_tree_sha1"],
            "worktree_clean": True,
        }
    ):
        return ("SUCCESSOR_SOURCE_IDENTITY_MISMATCH",)
    ancestry = state.get("historical_d2_ancestry")
    if (
        type(ancestry) is not dict
        or set(ancestry)
        != {
            "source_commit_sha1",
            "source_tree_sha1",
            "final_closure_sha256",
            "verified_ancestor",
        }
        or _SHA1_RE.fullmatch(
            str(ancestry.get("source_commit_sha1", ""))
        )
        is None
        or _SHA1_RE.fullmatch(
            str(ancestry.get("source_tree_sha1", ""))
        )
        is None
        or ancestry.get("final_closure_sha256")
        != _D2_FINAL_CLOSURE_SHA256
        or ancestry.get("verified_ancestor") is not True
        or ancestry.get("source_commit_sha1")
        == closure.get("source_commit_sha1")
        or ancestry.get("source_tree_sha1")
        == closure.get("source_tree_sha1")
    ):
        return ("HISTORICAL_D2_ANCESTRY_INVALID",)
    d2_identity = state.get("historical_d2_completion_receipt")
    if (
        d2_identity != _D2_IDENTITY
        or closure.get("historical_d2_final_closure_sha256")
        != _D2_FINAL_CLOSURE_SHA256
        or closure.get(
            "historical_d2_completion_receipt_identity_sha256"
        )
        != _D2_IDENTITY["identity_sha256"]
    ):
        return ("HISTORICAL_D2_RECEIPT_BINDING_INVALID",)
    parent_identity = state.get("parent_addendum_external_identity")
    if (
        parent_identity != _PARENT_IDENTITY
        or closure.get("parent_addendum_external_identity_sha256")
        != RECOVERY_EPOCH002_PARENT_ADDENDUM_EXTERNAL_IDENTITY_SHA256
        or not _success_parent_postfetch_valid(
            state.get("parent_addendum_postfetch_evidence"),
            parent_identity,
        )
    ):
        return ("PARENT_ADDENDUM_BINDING_INVALID",)
    graph = state.get("success_owner_graph")
    expected_graph = _success_expected_owner_graph()
    if (
        graph != expected_graph
        or closure.get("success_owner_graph_sha256")
        != expected_graph["success_owner_graph_sha256"]
        or any(
            type(row) is not dict
            or set(row) != RECOVERY_EPOCH002_SUCCESS_OWNER_BINDING_KEYS
            for row in graph.get("owner_role_bindings", ())
        )
        or type(graph.get("independent_verifier_constraints")) is not dict
        or set(graph["independent_verifier_constraints"])
        != RECOVERY_EPOCH002_INDEPENDENT_VERIFIER_CONSTRAINT_KEYS
    ):
        return ("SUCCESS_OWNER_GRAPH_INVALID",)
    if validate_recovery_epoch002_successor_bootstrap_manifest(
        bootstrap,
        source_closure=closure,
        success_owner_graph=graph,
    ):
        return ("SUCCESSOR_SOURCE_CLOSURE_INVALID",)
    manifest = state.get("success_contract_test_manifest")
    expected_manifest = _success_expected_contract_manifest()
    if (
        manifest != expected_manifest
        or closure.get("success_contract_test_manifest_sha256")
        != expected_manifest["success_contract_test_manifest_sha256"]
        or any(
            type(row) is not dict
            or set(row) != RECOVERY_EPOCH002_SUCCESS_CONTRACT_TEST_FILE_KEYS
            for row in manifest.get("test_files", ())
        )
    ):
        return ("SUCCESS_CONTRACT_TEST_MANIFEST_BINDING_INVALID",)
    return ()


def validate_recovery_epoch002_successor_closure_state(
    state: Mapping[str, Any],
) -> tuple[str, ...]:
    """Fail closed on malformed successor closure state."""

    try:
        if (
            type(state) is dict
            and "historical_d2_completion_receipt" not in state
        ):
            return ("HISTORICAL_D2_RECEIPT_BINDING_INVALID",)
        if (
            type(state) is dict
            and (
                "parent_addendum_external_identity" not in state
                or "parent_addendum_postfetch_evidence" not in state
            )
        ):
            return ("PARENT_ADDENDUM_BINDING_INVALID",)
        if (
            type(state) is not dict
            or set(state) != RECOVERY_EPOCH002_SUCCESSOR_CLOSURE_STATE_KEYS
            or _success_contains_forbidden_state_key(state)
        ):
            return ("SUCCESSOR_SOURCE_CLOSURE_INVALID",)
        return _validate_recovery_epoch002_successor_closure_state_impl(
            state
        )
    except (
        AttributeError,
        KeyError,
        OSError,
        RecursionError,
        SyntaxError,
        TypeError,
        UnicodeError,
        ValueError,
    ):
        return ("SUCCESSOR_SOURCE_CLOSURE_INVALID",)


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
    "RECOVERY_EPOCH002_SUCCESSOR_SOURCE_CLOSURE_SCHEMA",
    "RECOVERY_EPOCH002_SUCCESSOR_SOURCE_CLOSURE_KEYS",
    "RECOVERY_EPOCH002_BOOTSTRAP_V2_SCHEMA",
    "RECOVERY_EPOCH002_BOOTSTRAP_V2_KEYS",
    "RECOVERY_EPOCH002_SUCCESS_OWNER_GRAPH_SCHEMA",
    "RECOVERY_EPOCH002_SUCCESS_OWNER_GRAPH_KEYS",
    "RECOVERY_EPOCH002_SUCCESS_OWNER_BINDING_KEYS",
    "RECOVERY_EPOCH002_INDEPENDENT_VERIFIER_CONSTRAINT_KEYS",
    "RECOVERY_EPOCH002_SUCCESS_OWNER_ROLE_BINDINGS",
    "RECOVERY_EPOCH002_SUCCESS_CONTRACT_TEST_MANIFEST_SCHEMA",
    "RECOVERY_EPOCH002_SUCCESS_CONTRACT_TEST_MANIFEST_KEYS",
    "RECOVERY_EPOCH002_SUCCESS_CONTRACT_TEST_FILE_KEYS",
    "RECOVERY_EPOCH002_SUCCESS_CONTRACT_TEST_NODE_IDS",
    "RECOVERY_EPOCH002_PARENT_ADDENDUM_RECEIPT_ROLE",
    "RECOVERY_EPOCH002_PARENT_ADDENDUM_RECEIPT_SCHEMA",
    "RECOVERY_EPOCH002_PARENT_ADDENDUM_RECEIPT_PATH",
    "RECOVERY_EPOCH002_PARENT_ADDENDUM_EXTERNAL_IDENTITY_KEYS",
    "RECOVERY_EPOCH002_PARENT_ADDENDUM_EXTERNAL_IDENTITY_SHA256",
    "RECOVERY_EPOCH002_PARENT_ADDENDUM_CHANGED_PATHS",
    "validate_recovery_epoch002_bootstrap_manifest",
    "validate_recovery_epoch002_operational_bootstrap_manifest",
    "validate_recovery_epoch002_successor_bootstrap_manifest",
    "validate_recovery_epoch002_formal_node_registry",
    "validate_recovery_epoch002_operational_source_manifest",
    "build_recovery_epoch002_d2_final_closure_preimage",
    "compute_recovery_epoch002_d2_final_closure_sha256",
    "validate_recovery_epoch002_source_closure",
    "validate_recovery_epoch002_closure_state",
    "validate_recovery_epoch002_successor_closure_state",
]
