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
from pathlib import Path, PurePosixPath
import re
import stat
import subprocess
import sys
from typing import Any, Mapping

from emlis_ai_nls_v3_artifact_contract import (
    artifact_sha256,
    canonical_json_bytes,
)
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


# Recovery Epoch003 is additive.  These constants and the validator below
# deliberately leave every Epoch002 schema and validation branch untouched.
RECOVERY_EPOCH003_SOURCE_CLOSURE_SCHEMA = (
    "cocolon.emlis.nls_v3.recovery_epoch003."
    "source_baseline_eligibility_closure.v1"
)
RECOVERY_EPOCH003_BOOTSTRAP_MANIFEST_SCHEMA = (
    "cocolon.emlis.nls_v3.recovery_epoch003."
    "formal_worker_bootstrap_manifest.v1"
)
RECOVERY_EPOCH003_SOURCE_CLOSURE_KEYS = _keys(
    """
    schema_version repository_full_name source_ref source_commit_sha1
    source_tree_sha1 worktree_clean detailed_design_sha256
    epoch003_p0_external_identity_sha256 epoch002_predecessor_set_sha256
    d1_red_receipt_external_identity_sha256
    d2_green_receipt_external_identity_sha256
    source_dependency_closure_sha256 canonical_current_closure_sha256
    requirement_registry_sha256 formal_node_registry_sha256
    proof_source_closure_sha256 formal_test_manifest_sha256
    bootstrap_closure_sha256
    reference_runtime_observation_external_identity_sha256
    source_closure_sha256
    """
)
RECOVERY_EPOCH003_BOOTSTRAP_MANIFEST_KEYS = _keys(
    """
    schema_version source_commit_sha1 source_tree_sha1
    formal_owner_artifacts formal_owner_artifacts_sha256
    formal_test_node_ids formal_test_manifest formal_test_manifest_sha256
    conftest_plugin_mode pytest_plugins_environment_variable_removed
    pytest_entrypoint_autoload_disabled explicit_plugin_allowlist
    loaded_plugin_manifest loaded_plugin_manifest_sha256 import_manifest
    import_manifest_sha256 dependency_lock_identity
    wheel_bundle_manifest_sha256 expected_installed_distributions
    expected_installed_distributions_sha256 expected_python_runtime_identity
    expected_pytest_distribution_identity
    reference_runtime_observation_external_identity environment_policy
    environment_policy_sha256 preflight_argv preflight_argv_sha256
    formal_worker_argv formal_worker_argv_sha256 unclassified_import_count
    unresolved_dynamic_import_count body_free bootstrap_closure_sha256
    """
)
RECOVERY_EPOCH003_KNOWN_SCHEMA_PAIRS = (
    (
        RECOVERY_EPOCH002_SUCCESSOR_SOURCE_CLOSURE_SCHEMA,
        RECOVERY_EPOCH002_BOOTSTRAP_V2_SCHEMA,
    ),
    (
        RECOVERY_EPOCH003_SOURCE_CLOSURE_SCHEMA,
        RECOVERY_EPOCH003_BOOTSTRAP_MANIFEST_SCHEMA,
    ),
)

_RECOVERY_EPOCH003_EXTERNAL_IDENTITY_KEYS = _keys(
    """
    artifact_role body_free git_blob_sha1 identity_sha256
    logical_artifact_sha256 path publication_commit_sha1 raw_sha256
    repository_full_name schema_version
    """
)
_RECOVERY_EPOCH003_RUNTIME_IDENTITY_KEYS = _keys(
    "executable_sha256 implementation version build_sha256"
)
_RECOVERY_EPOCH003_DISTRIBUTION_KEYS = _keys(
    """
    normalized_distribution_name distribution_version wheel_sha256
    installed_record_closure_sha256
    """
)
_RECOVERY_EPOCH003_DEPENDENCY_LOCK_KEYS = _keys(
    "identity_class path raw_sha256"
)
_RECOVERY_EPOCH003_ENVIRONMENT_POLICY_KEYS = _keys(
    "fixed removed inherited_path_sha256 lang lc_all"
)
_RECOVERY_EPOCH003_ENVIRONMENT_FIXED_KEYS = _keys(
    "PYTEST_DISABLE_PLUGIN_AUTOLOAD PYTHONDONTWRITEBYTECODE"
)
_RECOVERY_EPOCH003_OWNER_ROW_KEYS = _keys(
    "role path git_blob_sha1 raw_sha256"
)
_RECOVERY_EPOCH003_TEST_ROW_KEYS = _keys(
    "path git_blob_sha1 raw_sha256"
)
_RECOVERY_EPOCH003_IMPORT_ROW_KEYS = _keys(
    "import_name classification owner_paths target_identity"
)
_RECOVERY_EPOCH003_FIRST_PARTY_TARGET_KEYS = _keys(
    "path git_blob_sha1 raw_sha256"
)
_RECOVERY_EPOCH003_STDLIB_TARGET_KEYS = _keys(
    "module_name python_runtime_identity_sha256"
)
_RECOVERY_EPOCH003_THIRD_PARTY_TARGET_KEYS = _keys(
    """
    module_name normalized_distribution_name distribution_version
    wheel_sha256 installed_record_closure_sha256
    """
)
_RECOVERY_EPOCH003_SHA1_RE = re.compile(r"^[0-9a-f]{40}$")
_RECOVERY_EPOCH003_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_RECOVERY_EPOCH003_REFERENCE_ROLE = (
    "RECOVERY_EPOCH003_REFERENCE_RUNTIME_OBSERVATION"
)
_RECOVERY_EPOCH003_REFERENCE_SCHEMA = (
    "cocolon.emlis.nls_v3.recovery_epoch003."
    "reference_runtime_observation.v1"
)
_RECOVERY_EPOCH003_REFERENCE_PATH = (
    "EmlisAIの実装済み資料/documents/"
    "NLSv3_Step11_Cycle001_RecoveryEpoch003_"
    "PreEvent1_ReferenceRuntimeObservation_BodyFree_Receipt.json"
)
_RECOVERY_EPOCH003_FINAL_ISSUANCE_AUTHORITY = (
    "NLS_V3_STEP11_CYCLE001_RECOVERY_EPOCH003_FINAL_PRE_EVENT1_REFERENCE_"
    "RUNTIME_OBSERVATION_AND_SOURCE_BOOTSTRAP_OPERATIONAL_ADMISSION_"
    "CARRIER_ISSUANCE_INDEPENDENT_VERIFICATION_AND_POSTVERIFICATION_ONLY"
)
_RECOVERY_EPOCH003_REFERENCE_KEYS = _keys(
    """
    schema_version logical_cycle_id recovery_epoch_id authority_token
    source_commit_sha1 source_tree_sha1 dependency_lock_identity
    wheel_bundle_manifest_sha256 runtime_materialization
    python_runtime_identity pytest_distribution_identity
    installed_distributions installed_distributions_sha256
    environment_policy environment_policy_sha256 reservation_count_delta
    formal_exact134_invocation_count collection_state test_execution_state
    body_free reference_runtime_observation_sha256
    """
)
_RECOVERY_EPOCH003_RUNTIME_MATERIALIZATION_KEYS = _keys(
    """
    schema_version runtime_root_identity_sha256
    python_executable_relative_path installed_directory_relative_path
    dependency_lock_raw_sha256 wheel_bundle_manifest_sha256
    distribution_count runtime_materialization_state body_free
    runtime_materialization_sha256
    """
)
_RECOVERY_EPOCH003_RUNTIME_MATERIALIZATION_SCHEMA = (
    "cocolon.emlis.nls_v3.recovery_epoch003.runtime_materialization.v1"
)
_RECOVERY_EPOCH003_DETAILED_DESIGN_SHA256 = (
    "6aa3fb799919ac30b0eb84571ac4009d62a2bd799c84322272a59bba533f13bc"
)
_RECOVERY_EPOCH003_D1_RECEIPT_IDENTITY_SHA256 = (
    "d9164d82715abb519b549a7581737a37ebd3bf153b53284697cbe4573a8edb9e"
)
_RECOVERY_EPOCH003_D2_RECEIPT_IDENTITY_SHA256 = (
    "cbd665b12b3af16b251a66073222d12823fb8776207922616718290e4bddc738"
)
_RECOVERY_EPOCH003_P0_EXTERNAL_IDENTITY_SHA256 = (
    "74286b862eeee1663d2758ee18d1e848316da6fc27b12fef38c149c5a2b52f36"
)
_RECOVERY_EPOCH003_EPOCH002_PREDECESSOR_SET_SHA256 = (
    "44ef0cf922e8fb6503ae4a96f458a60abc8fbae2e48aa11863269ff783d7343d"
)
_RECOVERY_EPOCH003_LOCK_PATH = (
    "ai/configs/"
    "emlis_nls_v3_recovery_epoch002_formal_worker_bootstrap_lock_v1.json"
)
_RECOVERY_EPOCH003_LOCK_BLOB_SHA1 = (
    "0822fcb010985cd0d384f250a9e8a1fe16dc8fd4"
)
_RECOVERY_EPOCH003_LOCK_RAW_SHA256 = (
    "9bb2875541a6d959c1dca47cb5b96de5b0041ccf5288e849c469c15a8b310787"
)
_RECOVERY_EPOCH003_LOCK_LOGICAL_SHA256 = (
    "801ba54efc0f6655238d14e7c153fb70b555801489aa8ba028515fc64d9c05f4"
)
_RECOVERY_EPOCH003_WHEEL_BUNDLE_SHA256 = (
    "63f3915ccf57845dc0c4b5d14762207d23d1cb7a435a9de8411add8491ba6fc8"
)
_RECOVERY_EPOCH003_INSTALLED_DISTRIBUTIONS_SHA256 = (
    "0e2e4b5ec3f3b1aef7fad4474af28d8eeea8fa7bec1a57a9cb7180fc81b80e42"
)
_RECOVERY_EPOCH003_REQUIREMENT_REGISTRY_PATH = (
    "ai/services/ai_inference/"
    "emlis_ai_recovery_epoch001_current_step_requirement_registry_v3.py"
)
_RECOVERY_EPOCH003_OWNER_ROLE_PATHS = tuple(
    sorted(
        (
            (
                "atomic_publication_bundle",
                "ai/tools/"
                "emlis_nls_v3_recovery_epoch002_"
                "atomic_publication_bundle_v3.py",
            ),
            (
                "canonical_current_closure",
                "ai/services/ai_inference/"
                "emlis_ai_recovery_epoch002_"
                "canonical_current_closure_v3.py",
            ),
            (
                "current_step_proof_gate",
                "ai/tools/"
                "emlis_nls_v3_recovery_epoch002_current_step_proof_run.py",
            ),
            (
                "formal_parent_orchestrator",
                "ai/tools/"
                "emlis_nls_v3_recovery_epoch002_"
                "formal_parent_orchestrator_v3.py",
            ),
            (
                "formal_worker_bootstrap_preflight",
                "ai/tools/"
                "emlis_nls_v3_recovery_epoch002_"
                "formal_worker_bootstrap_preflight.py",
            ),
            (
                "independent_closure_verifier",
                "ai/tools/"
                "emlis_nls_v3_recovery_epoch002_closure_receipt_verify.py",
            ),
            (
                "sequence_ledger",
                "ai/services/ai_inference/"
                "emlis_ai_recovery_epoch002_sequence_ledger_v3.py",
            ),
        ),
        key=lambda row: (row[0], row[1]),
    )
)
_RECOVERY_EPOCH003_FORMAL_NODE_IDS = tuple(
    node_id
    for step in range(11)
    for node_id in RECOVERY_EPOCH001_FORMAL_NODE_IDS_BY_STEP[step]
)
_RECOVERY_EPOCH003_FORMAL_TEST_PATHS = tuple(
    sorted(
        {
            node_id.split("::", 1)[0]
            for node_id in _RECOVERY_EPOCH003_FORMAL_NODE_IDS
        }
    )
)
_RECOVERY_EPOCH003_PREFLIGHT_ARGV = [
    "python",
    "-m",
    "ai.tools.emlis_nls_v3_recovery_epoch002_"
    "formal_worker_bootstrap_preflight",
]
_RECOVERY_EPOCH003_FORMAL_WORKER_ARGV_PREFIX = [
    "python",
    "-m",
    "pytest",
    "--noconftest",
    "-p",
    "no:cacheprovider",
]


def _recovery_epoch003_hash_without(
    value: Mapping[str, Any],
    key: str,
) -> str:
    payload = dict(value)
    payload.pop(key, None)
    return artifact_sha256(payload)


def _recovery_epoch003_sha1(value: Any) -> bool:
    return (
        isinstance(value, str)
        and _RECOVERY_EPOCH003_SHA1_RE.fullmatch(value) is not None
    )


def _recovery_epoch003_sha256(value: Any) -> bool:
    return (
        isinstance(value, str)
        and _RECOVERY_EPOCH003_SHA256_RE.fullmatch(value) is not None
    )


def _recovery_epoch003_external_identity_valid(
    value: Any,
    *,
    role: str,
    schema: str,
    path: str,
) -> bool:
    return bool(
        type(value) is dict
        and set(value) == _RECOVERY_EPOCH003_EXTERNAL_IDENTITY_KEYS
        and value.get("artifact_role") == role
        and value.get("schema_version") == schema
        and value.get("path") == path
        and value.get("repository_full_name") == "MassyuRed/Cocolon"
        and value.get("body_free") is True
        and _recovery_epoch003_sha1(value.get("git_blob_sha1"))
        and _recovery_epoch003_sha1(value.get("publication_commit_sha1"))
        and _recovery_epoch003_sha256(value.get("raw_sha256"))
        and _recovery_epoch003_sha256(
            value.get("logical_artifact_sha256")
        )
        and value.get("identity_sha256")
        == _recovery_epoch003_hash_without(value, "identity_sha256")
    )


def _recovery_epoch003_runtime_identity_valid(value: Any) -> bool:
    return bool(
        type(value) is dict
        and set(value) == _RECOVERY_EPOCH003_RUNTIME_IDENTITY_KEYS
        and isinstance(value.get("implementation"), str)
        and bool(value.get("implementation"))
        and isinstance(value.get("version"), str)
        and bool(value.get("version"))
        and _recovery_epoch003_sha256(value.get("executable_sha256"))
        and _recovery_epoch003_sha256(value.get("build_sha256"))
        and value.get("executable_sha256") != "0" * 64
        and value.get("build_sha256") != "0" * 64
    )


def _recovery_epoch003_distribution_valid(value: Any) -> bool:
    return bool(
        type(value) is dict
        and set(value) == _RECOVERY_EPOCH003_DISTRIBUTION_KEYS
        and isinstance(value.get("normalized_distribution_name"), str)
        and bool(value.get("normalized_distribution_name"))
        and isinstance(value.get("distribution_version"), str)
        and bool(value.get("distribution_version"))
        and _recovery_epoch003_sha256(value.get("wheel_sha256"))
        and _recovery_epoch003_sha256(
            value.get("installed_record_closure_sha256")
        )
    )


def _recovery_epoch003_environment_valid(value: Any) -> bool:
    if (
        type(value) is not dict
        or set(value) != _RECOVERY_EPOCH003_ENVIRONMENT_POLICY_KEYS
        or type(value.get("fixed")) is not dict
        or set(value["fixed"]) != _RECOVERY_EPOCH003_ENVIRONMENT_FIXED_KEYS
        or value["fixed"].get("PYTEST_DISABLE_PLUGIN_AUTOLOAD") != "1"
        or value["fixed"].get("PYTHONDONTWRITEBYTECODE") != "1"
        or value.get("removed")
        != ["PYTEST_ADDOPTS", "PYTEST_PLUGINS", "PYTHONPATH"]
        or value.get("inherited_path_sha256") == "0" * 64
        or not _recovery_epoch003_sha256(
            value.get("inherited_path_sha256")
        )
    ):
        return False
    return all(
        isinstance(value.get(key), str) and bool(value.get(key))
        for key in ("lang", "lc_all")
    )


def _recovery_epoch003_materialization_valid(
    value: Any,
    *,
    lock_raw_sha256: str,
    wheel_bundle_manifest_sha256: str,
    distribution_count: int,
) -> bool:
    if (
        type(value) is not dict
        or set(value) != _RECOVERY_EPOCH003_RUNTIME_MATERIALIZATION_KEYS
        or value.get("schema_version")
        != _RECOVERY_EPOCH003_RUNTIME_MATERIALIZATION_SCHEMA
        or not _recovery_epoch003_sha256(
            value.get("runtime_root_identity_sha256")
        )
        or value.get("dependency_lock_raw_sha256") != lock_raw_sha256
        or value.get("wheel_bundle_manifest_sha256")
        != wheel_bundle_manifest_sha256
        or value.get("distribution_count") != distribution_count
        or value.get("runtime_materialization_state")
        != "VERIFIED_LOCKED_REFERENCE_RUNTIME"
        or value.get("body_free") is not True
        or value.get("runtime_materialization_sha256")
        != _recovery_epoch003_hash_without(
            value,
            "runtime_materialization_sha256",
        )
    ):
        return False
    for key in (
        "python_executable_relative_path",
        "installed_directory_relative_path",
    ):
        path = value.get(key)
        if (
            not isinstance(path, str)
            or not path
            or PurePosixPath(path).is_absolute()
            or ".." in PurePosixPath(path).parts
        ):
            return False
    return True


def _recovery_epoch003_reference_valid(value: Any) -> bool:
    if (
        type(value) is not dict
        or set(value) != _RECOVERY_EPOCH003_REFERENCE_KEYS
        or value.get("schema_version") != _RECOVERY_EPOCH003_REFERENCE_SCHEMA
        or value.get("logical_cycle_id") != "NLS_V3_CYCLE_001"
        or value.get("recovery_epoch_id")
        != "NLS_V3_CYCLE001_RECOVERY_EPOCH_003"
        or value.get("authority_token")
        != _RECOVERY_EPOCH003_FINAL_ISSUANCE_AUTHORITY
        or not _recovery_epoch003_sha1(value.get("source_commit_sha1"))
        or not _recovery_epoch003_sha1(value.get("source_tree_sha1"))
        or value.get("reservation_count_delta") != 0
        or value.get("formal_exact134_invocation_count") != 0
        or value.get("collection_state") != "NOT_STARTED"
        or value.get("test_execution_state") != "NOT_STARTED"
        or value.get("body_free") is not True
        or value.get("reference_runtime_observation_sha256")
        != _recovery_epoch003_hash_without(
            value,
            "reference_runtime_observation_sha256",
        )
    ):
        return False
    lock = value.get("dependency_lock_identity")
    installed = value.get("installed_distributions")
    environment = value.get("environment_policy")
    return bool(
        type(lock) is dict
        and set(lock) == _RECOVERY_EPOCH003_DEPENDENCY_LOCK_KEYS
        and lock.get("identity_class") == "EXACT_HASH_LOCK"
        and lock.get("path") == _RECOVERY_EPOCH003_LOCK_PATH
        and lock.get("raw_sha256")
        == _RECOVERY_EPOCH003_LOCK_RAW_SHA256
        and value.get("wheel_bundle_manifest_sha256")
        == _RECOVERY_EPOCH003_WHEEL_BUNDLE_SHA256
        and type(installed) is list
        and len(installed) == 46
        and all(
            _recovery_epoch003_distribution_valid(row)
            for row in installed
        )
        and [row["normalized_distribution_name"] for row in installed]
        == sorted(
            {
                row["normalized_distribution_name"]
                for row in installed
            }
        )
        and value.get("installed_distributions_sha256")
        == artifact_sha256(installed)
        == _RECOVERY_EPOCH003_INSTALLED_DISTRIBUTIONS_SHA256
        and _recovery_epoch003_runtime_identity_valid(
            value.get("python_runtime_identity")
        )
        and value["python_runtime_identity"].get("implementation")
        == "CPYTHON"
        and value["python_runtime_identity"].get("version") == "3.12.13"
        and _recovery_epoch003_distribution_valid(
            value.get("pytest_distribution_identity")
        )
        and value.get("pytest_distribution_identity") in installed
        and value["pytest_distribution_identity"].get(
            "normalized_distribution_name"
        )
        == "pytest"
        and _recovery_epoch003_environment_valid(environment)
        and value.get("environment_policy_sha256")
        == artifact_sha256(environment)
        and _recovery_epoch003_materialization_valid(
            value.get("runtime_materialization"),
            lock_raw_sha256=_RECOVERY_EPOCH003_LOCK_RAW_SHA256,
            wheel_bundle_manifest_sha256=(
                _RECOVERY_EPOCH003_WHEEL_BUNDLE_SHA256
            ),
            distribution_count=46,
        )
    )


def _recovery_epoch003_git(root: Path, *args: str) -> str:
    return subprocess.run(
        ["git", *args],
        cwd=root,
        check=True,
        capture_output=True,
        text=True,
        timeout=20,
    ).stdout.strip()


def _recovery_epoch003_git_file_bytes(
    root: Path,
    path: str,
) -> bytes:
    return subprocess.run(
        ["git", "show", f"HEAD:{path}"],
        cwd=root,
        check=True,
        capture_output=True,
        timeout=20,
    ).stdout


def _recovery_epoch003_expected_source_repository(root: Path) -> bool:
    try:
        head = _recovery_epoch003_git(root, "rev-parse", "HEAD")
        main = _recovery_epoch003_git(
            root,
            "rev-parse",
            "refs/heads/main",
        )
        top_level = Path(
            _recovery_epoch003_git(
                root,
                "rev-parse",
                "--show-toplevel",
            )
        ).resolve()
        origin = _recovery_epoch003_git(
            root,
            "config",
            "--get",
            "remote.origin.url",
        ).rstrip("/")
    except (OSError, subprocess.SubprocessError):
        return False
    normalized = origin.removesuffix(".git")
    return bool(
        top_level == root
        and head == main
        and (
            normalized.endswith("/MassyuRed/mashos-api")
            or normalized.endswith(":MassyuRed/mashos-api")
        )
    )


def _recovery_epoch003_path_has_symlink_component(path: Path) -> bool:
    absolute = path.absolute()
    current = Path(absolute.anchor)
    for part in absolute.parts[1:]:
        current /= part
        if current.is_symlink():
            return True
    return False


def _recovery_epoch003_git_file_identity(
    root: Path,
    path: str,
) -> dict[str, str]:
    payload = _recovery_epoch003_git_file_bytes(root, path)
    return {
        "path": path,
        "git_blob_sha1": _recovery_epoch003_git(
            root,
            "rev-parse",
            f"HEAD:{path}",
        ),
        "raw_sha256": hashlib.sha256(payload).hexdigest(),
    }


def _recovery_epoch003_owner_artifacts(
    root: Path,
) -> list[dict[str, str]]:
    return [
        {
            "role": role,
            **_recovery_epoch003_git_file_identity(root, path),
        }
        for role, path in _RECOVERY_EPOCH003_OWNER_ROLE_PATHS
    ]


def _recovery_epoch003_formal_test_manifest(
    root: Path,
    paths: tuple[str, ...] | None = None,
) -> list[dict[str, str]]:
    return [
        _recovery_epoch003_git_file_identity(root, path)
        for path in (
            _RECOVERY_EPOCH003_FORMAL_TEST_PATHS
            if paths is None
            else paths
        )
    ]


def _recovery_epoch003_literal_assignment(
    root: Path,
    path: str,
    name: str,
) -> Any:
    tree = ast.parse(
        _recovery_epoch003_git_file_bytes(root, path).decode("utf-8")
    )
    for node in tree.body:
        targets: list[ast.expr] = []
        value: ast.expr | None = None
        if isinstance(node, ast.Assign):
            targets = list(node.targets)
            value = node.value
        elif isinstance(node, ast.AnnAssign):
            targets = [node.target]
            value = node.value
        if (
            value is not None
            and any(
                isinstance(target, ast.Name) and target.id == name
                for target in targets
            )
        ):
            return ast.literal_eval(value)
    raise ValueError("literal assignment missing")


def _recovery_epoch003_top_level_symbols(
    root: Path,
    path: str,
) -> frozenset[str]:
    tree = ast.parse(
        _recovery_epoch003_git_file_bytes(root, path).decode("utf-8")
    )
    result: set[str] = set()
    for node in tree.body:
        if isinstance(
            node,
            (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef),
        ):
            result.add(node.name)
        elif isinstance(node, ast.Import):
            result.update(
                alias.asname or alias.name.partition(".")[0]
                for alias in node.names
            )
        elif isinstance(node, ast.ImportFrom):
            result.update(
                alias.asname or alias.name
                for alias in node.names
                if alias.name != "*"
            )
        elif isinstance(node, (ast.Assign, ast.AnnAssign)):
            targets = (
                node.targets
                if isinstance(node, ast.Assign)
                else [node.target]
            )
            result.update(
                target.id
                for target in targets
                if isinstance(target, ast.Name)
            )
    return frozenset(result)


def _recovery_epoch003_import_manifest(
    root: Path,
    *,
    lock: Mapping[str, Any],
    runtime_identity: Mapping[str, Any],
) -> list[dict[str, Any]]:
    mapping = lock.get("module_distribution_map")
    distributions = {
        row.get("normalized_distribution_name"): row
        for row in lock.get("distributions", [])
        if type(row) is dict
    }
    if type(mapping) is not dict:
        raise ValueError("module distribution map invalid")
    tracked_modes = {
        path: metadata.split()[0]
        for line in _recovery_epoch003_git(
            root,
            "ls-files",
            "-s",
            "*.py",
        ).splitlines()
        if line and "\t" in line
        for metadata, path in [line.split("\t", 1)]
    }
    tracked_paths = tuple(
        sorted(
            path
            for path, mode in tracked_modes.items()
            if mode in {"100644", "100755"}
        )
    )
    tracked_set = frozenset(tracked_paths)

    def module_search_roots(importer_path: str) -> tuple[PurePosixPath, ...]:
        if importer_path.startswith("ai/tests/"):
            return (
                PurePosixPath("ai/tests"),
                PurePosixPath("ai/tests/helpers"),
                PurePosixPath("ai/tools"),
                PurePosixPath("ai/services/ai_inference"),
                PurePosixPath("ai/services"),
                PurePosixPath(),
            )
        return (
            PurePosixPath("ai/tests/helpers"),
            PurePosixPath("ai/tools"),
            PurePosixPath("ai/services/ai_inference"),
            PurePosixPath("ai/services"),
            PurePosixPath(),
        )

    def resolve_first_party_binding(
        module_name: str,
        importer_path: str,
    ) -> tuple[str, PurePosixPath] | None:
        module_relative = PurePosixPath(*module_name.split("."))
        for search_root in module_search_roots(importer_path):
            for suffix in (
                module_relative / "__init__.py",
                PurePosixPath(f"{module_relative}.py"),
            ):
                candidate = (search_root / suffix).as_posix()
                if candidate in tracked_set:
                    return candidate, search_root
        return None

    def resolve_first_party(
        module_name: str,
        importer_path: str,
    ) -> str | None:
        binding = resolve_first_party_binding(module_name, importer_path)
        return binding[0] if binding is not None else None

    def relative_module(
        runtime_module_name: str | None,
        importer_is_package: bool,
        module_name: str | None,
        level: int,
    ) -> str:
        if level == 0:
            if module_name is None:
                raise ValueError("empty absolute import")
            return module_name
        if runtime_module_name is None:
            raise ValueError("relative file import has no runtime package")
        package = runtime_module_name.split(".")
        if not importer_is_package:
            package = package[:-1]
        if not package or level > len(package):
            raise ValueError("relative import above runtime package")
        base = package[: len(package) - level + 1]
        if module_name:
            base.extend(module_name.split("."))
        return ".".join(base)

    exported_name_cache: dict[str, frozenset[str]] = {}

    def exported_names(path: str) -> frozenset[str]:
        cached = exported_name_cache.get(path)
        if cached is not None:
            return cached
        tree = ast.parse(
            _recovery_epoch003_git_file_bytes(root, path).decode("utf-8")
        )
        names: set[str] = set()

        def bind(target: ast.AST) -> None:
            if isinstance(target, ast.Name):
                names.add(target.id)
            elif isinstance(target, (ast.Tuple, ast.List)):
                for child in target.elts:
                    bind(child)

        for statement in tree.body:
            if isinstance(
                statement,
                (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef),
            ):
                names.add(statement.name)
            elif isinstance(statement, ast.Assign):
                for target in statement.targets:
                    bind(target)
            elif isinstance(statement, ast.AnnAssign):
                if statement.value is not None:
                    bind(statement.target)
            elif isinstance(statement, ast.Import):
                for alias in statement.names:
                    names.add(
                        alias.asname or alias.name.split(".", 1)[0]
                    )
            elif isinstance(statement, ast.ImportFrom):
                for alias in statement.names:
                    if alias.name != "*":
                        names.add(alias.asname or alias.name)
        result = frozenset(names)
        exported_name_cache[path] = result
        return result

    def first_party_import_available(
        node: ast.AST,
        importer_path: str,
        runtime_module_name: str | None,
        importer_is_package: bool,
    ) -> bool:
        if isinstance(node, ast.Import):
            return all(
                resolve_first_party(alias.name, importer_path) is not None
                for alias in node.names
            )
        if not isinstance(node, ast.ImportFrom):
            return False
        base = relative_module(
            runtime_module_name,
            importer_is_package,
            node.module,
            node.level,
        )
        base_path = resolve_first_party(base, importer_path)
        exports = (
            exported_names(base_path)
            if base_path is not None
            else frozenset()
        )
        for alias in node.names:
            if alias.name == "*":
                return False
            if (
                resolve_first_party(
                    f"{base}.{alias.name}",
                    importer_path,
                )
                is not None
                or alias.name in exports
            ):
                continue
            return False
        return base_path is not None or bool(node.names)

    def import_error_only_handler(node: ast.ExceptHandler) -> bool:
        expected = {"ImportError", "ModuleNotFoundError"}
        if isinstance(node.type, ast.Name):
            return node.type.id in expected
        return bool(
            isinstance(node.type, ast.Tuple)
            and node.type.elts
            and all(
                isinstance(item, ast.Name) and item.id in expected
                for item in node.type.elts
            )
        )

    def runtime_reachable_nodes(
        node: ast.AST,
        importer_path: str,
        runtime_module_name: str | None,
        importer_is_package: bool,
    ) -> list[ast.AST]:
        result = [node]
        if isinstance(node, ast.Try):
            primary_imports = [
                statement
                for statement in node.body
                if isinstance(statement, (ast.Import, ast.ImportFrom))
            ]
            if (
                primary_imports
                and len(primary_imports) == len(node.body)
                and all(
                    first_party_import_available(
                        statement,
                        importer_path,
                        runtime_module_name,
                        importer_is_package,
                    )
                    for statement in primary_imports
                )
                and all(
                    import_error_only_handler(handler)
                    for handler in node.handlers
                )
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
        for child in children:
            result.extend(
                runtime_reachable_nodes(
                    child,
                    importer_path,
                    runtime_module_name,
                    importer_is_package,
                )
            )
        return result

    importers: dict[str, set[str]] = {}
    first_party_targets: dict[str, str] = {}
    seeds = {
        path for _role, path in _RECOVERY_EPOCH003_OWNER_ROLE_PATHS
    } | set(_RECOVERY_EPOCH003_FORMAL_TEST_PATHS)
    pending: list[tuple[str, str | None]] = [
        (path, None) for path in sorted(seeds)
    ]
    visited: set[tuple[str, str | None]] = set()

    def record(module_name: str, importer_path: str) -> None:
        if not module_name:
            raise ValueError("empty import")
        importers.setdefault(module_name, set()).add(importer_path)
        target_binding = resolve_first_party_binding(
            module_name,
            importer_path,
        )
        if target_binding is not None:
            target_path, selected_root = target_binding
            existing = first_party_targets.setdefault(
                module_name,
                target_path,
            )
            if existing != target_path:
                raise ValueError("ambiguous first-party import")
            parts = module_name.split(".")
            for index in range(1, len(parts)):
                package_name = ".".join(parts[:index])
                package_path = (
                    selected_root
                    / PurePosixPath(*parts[:index])
                    / "__init__.py"
                ).as_posix()
                if package_path not in tracked_set:
                    continue
                importers.setdefault(package_name, set()).add(importer_path)
                prior = first_party_targets.setdefault(
                    package_name,
                    package_path,
                )
                if prior != package_path:
                    raise ValueError("ambiguous first-party package")
                package_item = (package_path, package_name)
                if package_item not in visited:
                    pending.append(package_item)
            target_item = (target_path, module_name)
            if target_item not in visited:
                pending.append(target_item)

    def record_file(
        target_path: str,
        importer_path: str,
        runtime_context: str | None,
    ) -> None:
        import_name = f"file:{target_path}"
        importers.setdefault(import_name, set()).add(importer_path)
        previous = first_party_targets.setdefault(import_name, target_path)
        if previous != target_path:
            raise ValueError("ambiguous first-party file import")
        target_item = (target_path, runtime_context)
        if target_item not in visited:
            pending.append(target_item)

    while pending:
        path, runtime_module_name = pending.pop(0)
        visit_key = (path, runtime_module_name)
        if visit_key in visited:
            continue
        if path not in tracked_paths:
            raise ValueError("untracked import owner")
        visited.add(visit_key)
        tree = ast.parse(
            _recovery_epoch003_git_file_bytes(root, path).decode("utf-8")
        )
        importer_is_package = path.endswith("/__init__.py")
        runtime_nodes = runtime_reachable_nodes(
            tree,
            path,
            runtime_module_name,
            importer_is_package,
        )
        reachable_ids = {id(node) for node in runtime_nodes}
        parent_by_id = {
            id(child): parent
            for parent in ast.walk(tree)
            for child in ast.iter_child_nodes(parent)
        }
        scope_types = (
            ast.FunctionDef,
            ast.AsyncFunctionDef,
            ast.Lambda,
            ast.ClassDef,
        )

        def evaluate_paths(
            node: ast.AST,
            path_values: Mapping[str, set[Path]],
            collection_names: set[str],
        ) -> set[Path]:
            if isinstance(node, ast.Name):
                return set(path_values.get(node.id, ()))
            if (
                isinstance(node, ast.Constant)
                and isinstance(node.value, str)
            ):
                return {Path(node.value)}
            if isinstance(node, (ast.Tuple, ast.List, ast.Set)):
                groups = [
                    evaluate_paths(item, path_values, collection_names)
                    for item in node.elts
                ]
                if any(not group for group in groups):
                    return set()
                return {value for group in groups for value in group}
            if isinstance(node, ast.Dict):
                groups = [
                    evaluate_paths(item, path_values, collection_names)
                    for item in node.values
                ]
                if any(not group for group in groups):
                    return set()
                return {value for group in groups for value in group}
            if isinstance(node, ast.BinOp) and isinstance(node.op, ast.Div):
                left_values = evaluate_paths(
                    node.left,
                    path_values,
                    collection_names,
                )
                right_values = evaluate_paths(
                    node.right,
                    path_values,
                    collection_names,
                )
                if not left_values or not right_values:
                    return set()
                return {
                    left / right
                    for left in left_values
                    for right in right_values
                }
            if isinstance(node, ast.Attribute):
                if node.attr != "parent":
                    return set()
                return {
                    value.parent
                    for value in evaluate_paths(
                        node.value,
                        path_values,
                        collection_names,
                    )
                }
            if isinstance(node, ast.Subscript):
                if (
                    isinstance(node.value, ast.Attribute)
                    and node.value.attr == "parents"
                    and isinstance(node.slice, ast.Constant)
                    and type(node.slice.value) is int
                ):
                    return {
                        value.parents[node.slice.value]
                        for value in evaluate_paths(
                            node.value.value,
                            path_values,
                            collection_names,
                        )
                        if 0 <= node.slice.value < len(value.parents)
                    }
                if (
                    isinstance(node.value, ast.Name)
                    and node.value.id in collection_names
                ):
                    return set(path_values.get(node.value.id, ()))
                return set()
            if isinstance(node, ast.Call):
                function = node.func
                if (
                    (
                        isinstance(function, ast.Name)
                        and function.id == "Path"
                    )
                    or (
                        isinstance(function, ast.Attribute)
                        and function.attr == "Path"
                    )
                ) and len(node.args) == 1 and not node.keywords:
                    return evaluate_paths(
                        node.args[0],
                        path_values,
                        collection_names,
                    )
                if isinstance(function, ast.Attribute):
                    base = evaluate_paths(
                        function.value,
                        path_values,
                        collection_names,
                    )
                    if (
                        function.attr in {"resolve", "absolute"}
                        and not node.args
                        and not node.keywords
                    ):
                        return {
                            (
                                value.absolute()
                                if value.is_absolute()
                                else (root / value).absolute()
                            )
                            for value in base
                        }
                    if function.attr == "joinpath":
                        if not node.args or node.keywords:
                            return set()
                        values = base
                        for argument in node.args:
                            argument_values = evaluate_paths(
                                argument,
                                path_values,
                                collection_names,
                            )
                            if not values or not argument_values:
                                return set()
                            values = {
                                left / right
                                for left in values
                                for right in argument_values
                            }
                        return values
            return set()

        def target_names(target: ast.AST) -> set[str]:
            if isinstance(target, ast.Name):
                return {target.id}
            if isinstance(target, (ast.Tuple, ast.List)):
                return {
                    name
                    for item in target.elts
                    for name in target_names(item)
                }
            return set()

        def scope_assignments(
            scope: ast.AST,
            *,
            before_line: int | None,
        ) -> list[ast.Assign | ast.AnnAssign | ast.For]:
            result: list[ast.Assign | ast.AnnAssign | ast.For] = []

            def visit(node: ast.AST) -> None:
                if node is not scope and isinstance(node, scope_types):
                    return
                if id(node) not in reachable_ids:
                    return
                if isinstance(node, (ast.Assign, ast.AnnAssign, ast.For)):
                    if (
                        before_line is None
                        or getattr(node, "lineno", before_line) < before_line
                    ):
                        result.append(node)
                for child in ast.iter_child_nodes(node):
                    visit(child)

            for child in ast.iter_child_nodes(scope):
                visit(child)
            return sorted(
                result,
                key=lambda item: (
                    getattr(item, "lineno", 0),
                    getattr(item, "col_offset", 0),
                ),
            )

        def apply_assignments(
            assignments: list[ast.Assign | ast.AnnAssign | ast.For],
            path_values: dict[str, set[Path]],
            collection_names: set[str],
        ) -> None:
            for _ in range(len(assignments) + 1):
                changed = False
                for assignment in assignments:
                    if isinstance(assignment, ast.Assign):
                        targets = list(assignment.targets)
                        value_node = assignment.value
                    elif isinstance(assignment, ast.AnnAssign):
                        targets = [assignment.target]
                        value_node = assignment.value
                    else:
                        targets = [assignment.target]
                        value_node = assignment.iter
                    if value_node is None:
                        continue
                    values = evaluate_paths(
                        value_node,
                        path_values,
                        collection_names,
                    )
                    is_collection = bool(
                        isinstance(
                            value_node,
                            (ast.Dict, ast.List, ast.Tuple, ast.Set),
                        )
                        or (
                            isinstance(value_node, ast.Name)
                            and value_node.id in collection_names
                        )
                    )
                    for target in targets:
                        for name in target_names(target):
                            if is_collection and name not in collection_names:
                                collection_names.add(name)
                                changed = True
                            if not values:
                                continue
                            previous = path_values.get(name, set())
                            merged = previous | values
                            if merged != previous:
                                path_values[name] = merged
                                changed = True
                if not changed:
                    break

        module_assignments = scope_assignments(
            tree,
            before_line=None,
        )

        def lexical_scope(node: ast.AST) -> ast.AST:
            current = parent_by_id.get(id(node))
            while current is not None:
                if isinstance(current, scope_types):
                    return current
                current = parent_by_id.get(id(current))
            return tree

        def environment_for(
            node: ast.AST,
        ) -> tuple[dict[str, set[Path]], set[str]]:
            path_values: dict[str, set[Path]] = {
                "__file__": {(root / path).absolute()}
            }
            collections: set[str] = set()
            apply_assignments(
                module_assignments,
                path_values,
                collections,
            )
            scope = lexical_scope(node)
            if scope is not tree:
                local_assignments = scope_assignments(
                    scope,
                    before_line=getattr(node, "lineno", 0),
                )
                local_bound = {
                    name
                    for assignment in scope_assignments(
                        scope,
                        before_line=None,
                    )
                    for target in (
                        list(assignment.targets)
                        if isinstance(assignment, ast.Assign)
                        else [assignment.target]
                    )
                    for name in target_names(target)
                }
                if isinstance(
                    scope,
                    (ast.FunctionDef, ast.AsyncFunctionDef, ast.Lambda),
                ):
                    local_bound.update(
                        argument.arg
                        for argument in (
                            *scope.args.posonlyargs,
                            *scope.args.args,
                            *scope.args.kwonlyargs,
                        )
                    )
                    if scope.args.vararg is not None:
                        local_bound.add(scope.args.vararg.arg)
                    if scope.args.kwarg is not None:
                        local_bound.add(scope.args.kwarg.arg)
                for name in local_bound:
                    path_values.pop(name, None)
                    collections.discard(name)
                apply_assignments(
                    local_assignments,
                    path_values,
                    collections,
                )
            return path_values, collections

        resolved_file_targets: set[tuple[str, str | None]] = set()
        spec_bindings: dict[tuple[int, str], int] = {}
        exec_bindings: dict[tuple[int, str], int] = {}
        for node in runtime_nodes:
            if isinstance(node, ast.Import):
                for alias in node.names:
                    record(alias.name, path)
            elif isinstance(node, ast.ImportFrom):
                base = relative_module(
                    runtime_module_name,
                    importer_is_package,
                    node.module,
                    node.level,
                )
                resolved_any = False
                if resolve_first_party(base, path) is not None:
                    record(base, path)
                    resolved_any = True
                for alias in node.names:
                    if alias.name == "*":
                        continue
                    candidate = f"{base}.{alias.name}"
                    if resolve_first_party(candidate, path) is not None:
                        record(candidate, path)
                        resolved_any = True
                if not resolved_any:
                    record(base, path)
            elif isinstance(node, ast.Call):
                function = node.func
                function_name = (
                    function.id
                    if isinstance(function, ast.Name)
                    else (
                        function.attr
                        if isinstance(function, ast.Attribute)
                        else ""
                    )
                )
                if function_name in {"__import__", "import_module"}:
                    if (
                        not node.args
                        or not isinstance(node.args[0], ast.Constant)
                        or not isinstance(node.args[0].value, str)
                    ):
                        raise ValueError("unresolved dynamic import")
                    record(node.args[0].value, path)
                elif function_name == "spec_from_file_location":
                    if len(node.args) < 2:
                        raise ValueError("unresolved file import")
                    assignment = parent_by_id.get(id(node))
                    if (
                        isinstance(assignment, ast.Assign)
                        and assignment.value is node
                        and len(assignment.targets) == 1
                        and isinstance(assignment.targets[0], ast.Name)
                    ):
                        spec_name = assignment.targets[0].id
                    elif (
                        isinstance(assignment, ast.AnnAssign)
                        and assignment.value is node
                        and isinstance(assignment.target, ast.Name)
                    ):
                        spec_name = assignment.target.id
                    else:
                        raise ValueError("unbound file import spec")
                    scope_key = id(lexical_scope(node))
                    binding_key = (scope_key, spec_name)
                    spec_bindings[binding_key] = (
                        spec_bindings.get(binding_key, 0) + 1
                    )
                    path_values, collections = environment_for(node)
                    resolved: set[str] = set()
                    path_candidates = evaluate_paths(
                        node.args[1],
                        path_values,
                        collections,
                    )
                    if not path_candidates:
                        raise ValueError("unresolved file import")
                    for candidate in path_candidates:
                        absolute = (
                            candidate
                            if candidate.is_absolute()
                            else (root / candidate).absolute()
                        )
                        try:
                            relative = absolute.relative_to(root).as_posix()
                        except ValueError as exc:
                            raise ValueError(
                                "file import outside repository"
                            ) from exc
                        if relative not in tracked_set:
                            raise ValueError("untracked file import")
                        resolved.add(relative)
                    candidates = sorted(resolved)
                    if not candidates:
                        raise ValueError("unresolved file import")
                    alias_values = evaluate_paths(
                        node.args[0],
                        path_values,
                        collections,
                    )
                    runtime_context: str | None = None
                    if len(alias_values) == 1:
                        alias = str(next(iter(alias_values)))
                        if (
                            alias
                            and all(
                                part.isidentifier()
                                for part in alias.split(".")
                            )
                        ):
                            runtime_context = alias
                    resolved_file_targets.update(
                        (candidate, runtime_context)
                        for candidate in candidates
                    )
                elif function_name == "exec_module":
                    owner = (
                        function.value
                        if isinstance(function, ast.Attribute)
                        else None
                    )
                    if (
                        not isinstance(owner, ast.Attribute)
                        or owner.attr != "loader"
                        or not isinstance(owner.value, ast.Name)
                    ):
                        raise ValueError("unbound file import execution")
                    binding_key = (
                        id(lexical_scope(node)),
                        owner.value.id,
                    )
                    exec_bindings[binding_key] = (
                        exec_bindings.get(binding_key, 0) + 1
                    )
        if (
            set(spec_bindings) != set(exec_bindings)
            or any(count != 1 for count in spec_bindings.values())
            or any(count != 1 for count in exec_bindings.values())
        ):
            raise ValueError("unmatched file import execution")
        for target_path, runtime_context in sorted(
            resolved_file_targets,
            key=lambda item: (item[0], item[1] or ""),
        ):
            record_file(target_path, path, runtime_context)

    runtime_hash = artifact_sha256(runtime_identity)
    rows: list[dict[str, Any]] = []
    for import_name in sorted(importers):
        owner_paths = sorted(importers[import_name])
        first_party_path = first_party_targets.get(import_name)
        root_name = import_name.split(".", 1)[0]
        if first_party_path is not None:
            rows.append(
                {
                    "import_name": import_name,
                    "classification": "FIRST_PARTY",
                    "owner_paths": owner_paths,
                    "target_identity": (
                        _recovery_epoch003_git_file_identity(
                            root,
                            first_party_path,
                        )
                    ),
                }
            )
        elif root_name in sys.stdlib_module_names or import_name == (
            "__future__"
        ):
            rows.append(
                {
                    "import_name": import_name,
                    "classification": (
                        "STDLIB_BOUND_TO_PYTHON_RUNTIME"
                    ),
                    "owner_paths": owner_paths,
                    "target_identity": {
                        "module_name": import_name,
                        "python_runtime_identity_sha256": runtime_hash,
                    },
                }
            )
        else:
            matching_prefixes = [
                prefix
                for prefix in mapping
                if (
                    import_name == prefix
                    or import_name.startswith(f"{prefix}.")
                )
            ]
            distribution_name = (
                mapping[max(matching_prefixes, key=len)]
                if matching_prefixes
                else None
            )
            distribution = distributions.get(distribution_name)
            if type(distribution) is not dict:
                raise ValueError(f"unclassified import: {import_name}")
            target = {
                key: distribution[key]
                for key in _RECOVERY_EPOCH003_DISTRIBUTION_KEYS
            }
            rows.append(
                {
                    "import_name": import_name,
                    "classification": (
                        "THIRD_PARTY_BOUND_TO_LOCKED_DISTRIBUTION"
                    ),
                    "owner_paths": owner_paths,
                    "target_identity": {
                        "module_name": import_name,
                        **target,
                    },
                }
            )
    if not rows:
        raise ValueError("empty import manifest")
    return rows


def build_recovery_epoch003_source_bootstrap_closure(
    state: Mapping[str, Any],
) -> dict[str, Any] | tuple[str, ...]:
    """Derive the nested exact20/exact33 carrier from actual source bytes."""

    failure = ("RECOVERY_EPOCH003_SOURCE_BOOTSTRAP_BUILD_INVALID",)
    try:
        required = _keys(
            """
            source_repository_root source_commit_sha1 source_tree_sha1
            reference_runtime_observation
            reference_runtime_observation_external_identity
            """
        )
        if type(state) is not dict or set(state) != required:
            return failure
        if (
            not isinstance(state.get("source_repository_root"), str)
            or not state.get("source_repository_root")
        ):
            return failure
        raw_root = Path(state["source_repository_root"]).absolute()
        if _recovery_epoch003_path_has_symlink_component(raw_root):
            return failure
        root = raw_root.resolve()
        commit = _recovery_epoch003_git(root, "rev-parse", "HEAD")
        tree = _recovery_epoch003_git(root, "rev-parse", "HEAD^{tree}")
        clean = (
            _recovery_epoch003_git(
                root,
                "status",
                "--porcelain",
                "--untracked-files=all",
            )
            == ""
        )
        reference = state.get("reference_runtime_observation")
        reference_identity = state.get(
            "reference_runtime_observation_external_identity"
        )
        reference_bytes = (
            canonical_json_bytes(reference) + b"\n"
            if type(reference) is dict
            else b""
        )
        reference_blob_sha1 = hashlib.sha1(
            b"blob "
            + str(len(reference_bytes)).encode("ascii")
            + b"\0"
            + reference_bytes
        ).hexdigest()
        if (
            not clean
            or not _recovery_epoch003_expected_source_repository(root)
            or state.get("source_commit_sha1") != commit
            or state.get("source_tree_sha1") != tree
            or not _recovery_epoch003_reference_valid(reference)
            or reference.get("source_commit_sha1") != commit
            or reference.get("source_tree_sha1") != tree
            or not _recovery_epoch003_external_identity_valid(
                reference_identity,
                role=_RECOVERY_EPOCH003_REFERENCE_ROLE,
                schema=_RECOVERY_EPOCH003_REFERENCE_SCHEMA,
                path=_RECOVERY_EPOCH003_REFERENCE_PATH,
            )
            or reference_identity.get("logical_artifact_sha256")
            != reference.get("reference_runtime_observation_sha256")
            or reference_identity.get("raw_sha256")
            != hashlib.sha256(reference_bytes).hexdigest()
            or reference_identity.get("git_blob_sha1")
            != reference_blob_sha1
        ):
            return failure
        lock_identity = reference["dependency_lock_identity"]
        lock_payload = _recovery_epoch003_git_file_bytes(
            root,
            _RECOVERY_EPOCH003_LOCK_PATH,
        )
        lock = json.loads(lock_payload)
        if (
            hashlib.sha256(lock_payload).hexdigest()
            != _RECOVERY_EPOCH003_LOCK_RAW_SHA256
            or lock_identity
            != {
                "identity_class": "EXACT_HASH_LOCK",
                "path": _RECOVERY_EPOCH003_LOCK_PATH,
                "raw_sha256": _RECOVERY_EPOCH003_LOCK_RAW_SHA256,
            }
            or _recovery_epoch003_git(
                root,
                "rev-parse",
                f"HEAD:{_RECOVERY_EPOCH003_LOCK_PATH}",
            )
            != _RECOVERY_EPOCH003_LOCK_BLOB_SHA1
            or lock.get("lock_sha256")
            != _RECOVERY_EPOCH003_LOCK_LOGICAL_SHA256
            or lock.get("lock_sha256")
            != _recovery_epoch003_hash_without(lock, "lock_sha256")
            or lock.get("distribution_count") != 46
            or type(lock.get("distributions")) is not list
            or len(lock["distributions"]) != 46
            or lock.get("target", {}).get("implementation") != "CPYTHON"
            or lock.get("target", {}).get("python_version") != "3.12.13"
            or lock.get("target", {}).get("platform") != "linux-x86_64"
            or lock.get("target", {}).get("machine") != "x86_64"
            or lock.get("resolution", {}).get("pip_version") != "26.0.1"
        ):
            return failure
        expected_installed = [
            {
                key: row[key]
                for key in _RECOVERY_EPOCH003_DISTRIBUTION_KEYS
            }
            for row in lock["distributions"]
        ]
        expected_installed.sort(
            key=lambda row: row["normalized_distribution_name"]
        )
        wheel_manifest = [
            {
                "wheel_filename": row["wheel_filename"],
                "wheel_sha256": row["wheel_sha256"],
                "wheel_record_sha256": row["wheel_record_sha256"],
            }
            for row in lock["distributions"]
        ]
        if (
            expected_installed != reference["installed_distributions"]
            or artifact_sha256(expected_installed)
            != _RECOVERY_EPOCH003_INSTALLED_DISTRIBUTIONS_SHA256
            or artifact_sha256(wheel_manifest)
            != _RECOVERY_EPOCH003_WHEEL_BUNDLE_SHA256
        ):
            return failure
        actual_nodes_by_step = _recovery_epoch003_literal_assignment(
            root,
            _RECOVERY_EPOCH003_REQUIREMENT_REGISTRY_PATH,
            "RECOVERY_EPOCH001_FORMAL_NODE_IDS_BY_STEP",
        )
        actual_rows = _recovery_epoch003_literal_assignment(
            root,
            _RECOVERY_EPOCH003_REQUIREMENT_REGISTRY_PATH,
            "_RECOVERY_EPOCH001_CURRENT_STEP_REQUIREMENT_ROWS",
        )
        actual_registry_hash = _recovery_epoch003_literal_assignment(
            root,
            _RECOVERY_EPOCH003_REQUIREMENT_REGISTRY_PATH,
            "RECOVERY_EPOCH001_EXPECTED_REGISTRY_SHA256",
        )
        actual_formal_registry_hash = (
            _recovery_epoch003_literal_assignment(
                root,
                _RECOVERY_EPOCH003_REQUIREMENT_REGISTRY_PATH,
                "RECOVERY_EPOCH001_EXPECTED_FORMAL_NODE_REGISTRY_SHA256",
            )
        )
        actual_registry_material = {
            "schema_version": _recovery_epoch003_literal_assignment(
                root,
                _RECOVERY_EPOCH003_REQUIREMENT_REGISTRY_PATH,
                (
                    "RECOVERY_EPOCH001_CURRENT_STEP_"
                    "REQUIREMENT_REGISTRY_SCHEMA"
                ),
            ),
            "candidate_version_id": _recovery_epoch003_literal_assignment(
                root,
                _RECOVERY_EPOCH003_REQUIREMENT_REGISTRY_PATH,
                "RECOVERY_EPOCH001_CANDIDATE_VERSION_ID",
            ),
            "recovery_epoch": 1,
            "red_freeze_authority": _recovery_epoch003_literal_assignment(
                root,
                _RECOVERY_EPOCH003_REQUIREMENT_REGISTRY_PATH,
                "RECOVERY_EPOCH001_REGISTRY_RED_FREEZE_AUTHORITY",
            ),
            "detailed_design_sha256": _recovery_epoch003_literal_assignment(
                root,
                _RECOVERY_EPOCH003_REQUIREMENT_REGISTRY_PATH,
                "RECOVERY_EPOCH001_DETAILED_DESIGN_SHA256",
            ),
            "required_sequence_event_1": (
                _recovery_epoch003_literal_assignment(
                    root,
                    _RECOVERY_EPOCH003_REQUIREMENT_REGISTRY_PATH,
                    "RECOVERY_EPOCH001_REQUIRED_SEQUENCE_EVENT_1",
                )
            ),
            "completion_sequence_event_2": (
                _recovery_epoch003_literal_assignment(
                    root,
                    _RECOVERY_EPOCH003_REQUIREMENT_REGISTRY_PATH,
                    "RECOVERY_EPOCH001_COMPLETION_SEQUENCE_EVENT_2",
                )
            ),
            "steps": actual_rows,
            "automatic_progression": False,
            "body_free": True,
        }
        actual_nodes = tuple(
            node
            for step in range(11)
            for node in actual_nodes_by_step[step]
        )
        actual_test_paths = tuple(
            sorted(
                {
                    node_id.split("::", 1)[0]
                    for node_id in actual_nodes
                }
            )
        )
        actual_test_functions = {
            path: frozenset(
                node.name
                for node in ast.parse(
                    _recovery_epoch003_git_file_bytes(
                        root,
                        path,
                    ).decode("utf-8")
                ).body
                if isinstance(
                    node,
                    (ast.FunctionDef, ast.AsyncFunctionDef),
                )
            )
            for path in actual_test_paths
        }
        if (
            type(actual_nodes_by_step) is not dict
            or set(actual_nodes_by_step) != set(range(11))
            or type(actual_rows) is not list
            or len(actual_rows) != 11
            or [row.get("step_number") for row in actual_rows]
            != list(range(11))
            or any(
                type(row) is not dict
                or row.get("formal_completion_node_ids")
                != actual_nodes_by_step[step]
                for step, row in enumerate(actual_rows)
            )
            or actual_nodes_by_step
            != RECOVERY_EPOCH001_FORMAL_NODE_IDS_BY_STEP
            or actual_nodes != _RECOVERY_EPOCH003_FORMAL_NODE_IDS
            or len(actual_nodes) != 134
            or len(set(actual_nodes)) != 134
            or actual_test_paths
            != _RECOVERY_EPOCH003_FORMAL_TEST_PATHS
            or len(actual_test_paths) != 21
            or actual_registry_hash
            != RECOVERY_EPOCH001_EXPECTED_REGISTRY_SHA256
            or artifact_sha256(actual_registry_material)
            != actual_registry_hash
            or actual_formal_registry_hash
            != RECOVERY_EPOCH001_EXPECTED_FORMAL_NODE_REGISTRY_SHA256
            or artifact_sha256(
                {
                    "step_nodes": {
                        str(step): list(actual_nodes_by_step[step])
                        for step in range(11)
                    }
                }
            )
            != actual_formal_registry_hash
            or any(
                not function_name.startswith("test_")
                or function_name
                not in actual_test_functions.get(path, frozenset())
                for path, function_name in (
                    node_id.split("::", 1)
                    for node_id in actual_nodes
                )
            )
        ):
            return failure
        owners = _recovery_epoch003_owner_artifacts(root)
        tests = _recovery_epoch003_formal_test_manifest(
            root,
            actual_test_paths,
        )
        imports = _recovery_epoch003_import_manifest(
            root,
            lock=lock,
            runtime_identity=reference["python_runtime_identity"],
        )
        preflight_argv = deepcopy(_RECOVERY_EPOCH003_PREFLIGHT_ARGV)
        formal_argv = [
            *_RECOVERY_EPOCH003_FORMAL_WORKER_ARGV_PREFIX,
            *actual_nodes,
        ]
        bootstrap = {
            "schema_version": RECOVERY_EPOCH003_BOOTSTRAP_MANIFEST_SCHEMA,
            "source_commit_sha1": commit,
            "source_tree_sha1": tree,
            "formal_owner_artifacts": owners,
            "formal_owner_artifacts_sha256": artifact_sha256(owners),
            "formal_test_node_ids": list(
                actual_nodes
            ),
            "formal_test_manifest": tests,
            "formal_test_manifest_sha256": artifact_sha256(tests),
            "conftest_plugin_mode": "NOCONFTEST",
            "pytest_plugins_environment_variable_removed": True,
            "pytest_entrypoint_autoload_disabled": True,
            "explicit_plugin_allowlist": [],
            "loaded_plugin_manifest": [],
            "loaded_plugin_manifest_sha256": artifact_sha256([]),
            "import_manifest": imports,
            "import_manifest_sha256": artifact_sha256(imports),
            "dependency_lock_identity": deepcopy(lock_identity),
            "wheel_bundle_manifest_sha256": reference[
                "wheel_bundle_manifest_sha256"
            ],
            "expected_installed_distributions": deepcopy(
                reference["installed_distributions"]
            ),
            "expected_installed_distributions_sha256": reference[
                "installed_distributions_sha256"
            ],
            "expected_python_runtime_identity": deepcopy(
                reference["python_runtime_identity"]
            ),
            "expected_pytest_distribution_identity": deepcopy(
                reference["pytest_distribution_identity"]
            ),
            "reference_runtime_observation_external_identity": deepcopy(
                reference_identity
            ),
            "environment_policy": deepcopy(
                reference["environment_policy"]
            ),
            "environment_policy_sha256": reference[
                "environment_policy_sha256"
            ],
            "preflight_argv": preflight_argv,
            "preflight_argv_sha256": artifact_sha256(preflight_argv),
            "formal_worker_argv": formal_argv,
            "formal_worker_argv_sha256": artifact_sha256(formal_argv),
            "unclassified_import_count": 0,
            "unresolved_dynamic_import_count": 0,
            "body_free": True,
            "bootstrap_closure_sha256": "",
        }
        bootstrap["bootstrap_closure_sha256"] = (
            _recovery_epoch003_hash_without(
                bootstrap,
                "bootstrap_closure_sha256",
            )
        )
        proof_owner = next(
            row
            for row in owners
            if row["role"] == "current_step_proof_gate"
        )
        source = {
            "schema_version": RECOVERY_EPOCH003_SOURCE_CLOSURE_SCHEMA,
            "repository_full_name": "MassyuRed/mashos-api",
            "source_ref": "refs/heads/main",
            "source_commit_sha1": commit,
            "source_tree_sha1": tree,
            "worktree_clean": True,
            "detailed_design_sha256": (
                _RECOVERY_EPOCH003_DETAILED_DESIGN_SHA256
            ),
            "epoch003_p0_external_identity_sha256": (
                _RECOVERY_EPOCH003_P0_EXTERNAL_IDENTITY_SHA256
            ),
            "epoch002_predecessor_set_sha256": (
                _RECOVERY_EPOCH003_EPOCH002_PREDECESSOR_SET_SHA256
            ),
            "d1_red_receipt_external_identity_sha256": (
                _RECOVERY_EPOCH003_D1_RECEIPT_IDENTITY_SHA256
            ),
            "d2_green_receipt_external_identity_sha256": (
                _RECOVERY_EPOCH003_D2_RECEIPT_IDENTITY_SHA256
            ),
            "source_dependency_closure_sha256": artifact_sha256(imports),
            "canonical_current_closure_sha256": artifact_sha256(owners),
            "requirement_registry_sha256": (
                actual_registry_hash
            ),
            "formal_node_registry_sha256": (
                actual_formal_registry_hash
            ),
            "proof_source_closure_sha256": artifact_sha256(proof_owner),
            "formal_test_manifest_sha256": bootstrap[
                "formal_test_manifest_sha256"
            ],
            "bootstrap_closure_sha256": bootstrap[
                "bootstrap_closure_sha256"
            ],
            "reference_runtime_observation_external_identity_sha256": (
                reference_identity["identity_sha256"]
            ),
            "source_closure_sha256": "",
        }
        source["source_closure_sha256"] = (
            _recovery_epoch003_hash_without(
                source,
                "source_closure_sha256",
            )
        )
        if (
            not _recovery_epoch003_bootstrap_valid(bootstrap)
            or not _recovery_epoch003_source_valid(source, bootstrap)
            or validate_recovery_epoch002_formal_node_registry(
                root,
                bootstrap,
                source,
            )
            or _recovery_epoch003_git(root, "rev-parse", "HEAD")
            != commit
            or _recovery_epoch003_git(root, "rev-parse", "HEAD^{tree}")
            != tree
            or _recovery_epoch003_git(
                root,
                "status",
                "--porcelain",
                "--untracked-files=all",
            )
            != ""
            or not _recovery_epoch003_expected_source_repository(root)
        ):
            return failure
        return {
            "source_closure": source,
            "bootstrap_closure": bootstrap,
        }
    except (
        AttributeError,
        IndexError,
        json.JSONDecodeError,
        KeyError,
        OSError,
        RecursionError,
        StopIteration,
        subprocess.SubprocessError,
        SyntaxError,
        TypeError,
        UnicodeError,
        ValueError,
    ):
        return failure


def _recovery_epoch003_placeholder_present(
    bootstrap: Mapping[str, Any],
) -> bool:
    runtime = bootstrap.get("expected_python_runtime_identity")
    environment = bootstrap.get("environment_policy")
    return bool(
        type(runtime) is dict
        and (
            runtime.get("executable_sha256") == "0" * 64
            or runtime.get("build_sha256") == "0" * 64
        )
    ) or bool(
        type(environment) is dict
        and environment.get("inherited_path_sha256") == "0" * 64
    )


def _recovery_epoch003_bootstrap_valid(value: Any) -> bool:
    if (
        type(value) is not dict
        or set(value) != RECOVERY_EPOCH003_BOOTSTRAP_MANIFEST_KEYS
        or value.get("schema_version")
        != RECOVERY_EPOCH003_BOOTSTRAP_MANIFEST_SCHEMA
        or not _recovery_epoch003_sha1(value.get("source_commit_sha1"))
        or not _recovery_epoch003_sha1(value.get("source_tree_sha1"))
        or value.get("body_free") is not True
        or value.get("bootstrap_closure_sha256")
        != _recovery_epoch003_hash_without(
            value,
            "bootstrap_closure_sha256",
        )
        or value.get("conftest_plugin_mode") != "NOCONFTEST"
        or value.get("pytest_plugins_environment_variable_removed")
        is not True
        or value.get("pytest_entrypoint_autoload_disabled") is not True
        or value.get("explicit_plugin_allowlist") != []
        or value.get("loaded_plugin_manifest") != []
        or value.get("loaded_plugin_manifest_sha256")
        != artifact_sha256(value["loaded_plugin_manifest"])
        or value.get("unclassified_import_count") != 0
        or value.get("unresolved_dynamic_import_count") != 0
    ):
        return False

    owners = value.get("formal_owner_artifacts")
    if (
        type(owners) is not list
        or not owners
        or any(
            type(row) is not dict
            or set(row) != _RECOVERY_EPOCH003_OWNER_ROW_KEYS
            or not isinstance(row.get("role"), str)
            or not row.get("role")
            or not isinstance(row.get("path"), str)
            or not row.get("path")
            or not _recovery_epoch003_sha1(row.get("git_blob_sha1"))
            or not _recovery_epoch003_sha256(row.get("raw_sha256"))
            for row in owners
        )
        or len({(row["role"], row["path"]) for row in owners})
        != len(owners)
        or [
            (row["role"], row["path"])
            for row in owners
        ]
        != list(_RECOVERY_EPOCH003_OWNER_ROLE_PATHS)
        or value.get("formal_owner_artifacts_sha256")
        != artifact_sha256(owners)
    ):
        return False

    nodes = value.get("formal_test_node_ids")
    tests = value.get("formal_test_manifest")
    if (
        type(nodes) is not list
        or nodes != list(_RECOVERY_EPOCH003_FORMAL_NODE_IDS)
        or len(nodes) != len(set(nodes))
        or len(nodes) != 134
        or type(tests) is not list
        or len(tests) != 21
        or any(
            type(row) is not dict
            or set(row) != _RECOVERY_EPOCH003_TEST_ROW_KEYS
            or not isinstance(row.get("path"), str)
            or not row.get("path")
            or not _recovery_epoch003_sha1(row.get("git_blob_sha1"))
            or not _recovery_epoch003_sha256(row.get("raw_sha256"))
            for row in tests
        )
        or [row["path"] for row in tests]
        != list(_RECOVERY_EPOCH003_FORMAL_TEST_PATHS)
        or value.get("formal_test_manifest_sha256")
        != artifact_sha256(tests)
    ):
        return False

    imports = value.get("import_manifest")
    if (
        type(imports) is not list
        or not imports
        or any(
            type(row) is not dict
            or set(row) != _RECOVERY_EPOCH003_IMPORT_ROW_KEYS
            or not isinstance(row.get("import_name"), str)
            or not row.get("import_name")
            or row.get("classification")
            not in {
                "FIRST_PARTY",
                "STDLIB_BOUND_TO_PYTHON_RUNTIME",
                "THIRD_PARTY_BOUND_TO_LOCKED_DISTRIBUTION",
            }
            or type(row.get("owner_paths")) is not list
            or type(row.get("target_identity")) is not dict
            for row in imports
        )
        or [row["import_name"] for row in imports]
        != sorted({row["import_name"] for row in imports})
        or value.get("import_manifest_sha256") != artifact_sha256(imports)
    ):
        return False

    lock = value.get("dependency_lock_identity")
    installed = value.get("expected_installed_distributions")
    pytest_identity = value.get("expected_pytest_distribution_identity")
    if (
        type(lock) is not dict
        or set(lock) != _RECOVERY_EPOCH003_DEPENDENCY_LOCK_KEYS
        or lock.get("identity_class") != "EXACT_HASH_LOCK"
        or not isinstance(lock.get("path"), str)
        or not lock.get("path")
        or not _recovery_epoch003_sha256(lock.get("raw_sha256"))
        or not _recovery_epoch003_sha256(
            value.get("wheel_bundle_manifest_sha256")
        )
        or type(installed) is not list
        or not installed
        or any(
            not _recovery_epoch003_distribution_valid(row)
            for row in installed
        )
        or [row["normalized_distribution_name"] for row in installed]
        != sorted(
            {
                row["normalized_distribution_name"]
                for row in installed
            }
        )
        or value.get("expected_installed_distributions_sha256")
        != artifact_sha256(installed)
        or not _recovery_epoch003_distribution_valid(pytest_identity)
        or pytest_identity.get("normalized_distribution_name") != "pytest"
        or pytest_identity not in installed
        or not _recovery_epoch003_runtime_identity_valid(
            value.get("expected_python_runtime_identity")
        )
    ):
        return False
    runtime_identity_hash = artifact_sha256(
        value["expected_python_runtime_identity"]
    )
    distribution_by_name = {
        row["normalized_distribution_name"]: row for row in installed
    }
    for row in imports:
        classification = row["classification"]
        owner_paths = row["owner_paths"]
        target = row["target_identity"]
        if (
            owner_paths != sorted(set(owner_paths))
            or any(
                not isinstance(path, str) or not path
                for path in owner_paths
            )
        ):
            return False
        if classification == "FIRST_PARTY":
            if (
                set(target) != _RECOVERY_EPOCH003_FIRST_PARTY_TARGET_KEYS
                or owner_paths == []
                or not _recovery_epoch003_sha1(
                    target.get("git_blob_sha1")
                )
                or not _recovery_epoch003_sha256(
                    target.get("raw_sha256")
                )
            ):
                return False
        elif classification == "STDLIB_BOUND_TO_PYTHON_RUNTIME":
            if (
                set(target) != _RECOVERY_EPOCH003_STDLIB_TARGET_KEYS
                or target.get("module_name") != row["import_name"]
                or target.get("python_runtime_identity_sha256")
                != runtime_identity_hash
            ):
                return False
        else:
            distribution = distribution_by_name.get(
                target.get("normalized_distribution_name")
            )
            if (
                set(target)
                != _RECOVERY_EPOCH003_THIRD_PARTY_TARGET_KEYS
                or target.get("module_name") != row["import_name"]
                or distribution is None
                or {
                    key: target.get(key)
                    for key in _RECOVERY_EPOCH003_DISTRIBUTION_KEYS
                }
                != distribution
            ):
                return False

    reference = value.get(
        "reference_runtime_observation_external_identity"
    )
    environment = value.get("environment_policy")
    preflight_argv = value.get("preflight_argv")
    formal_argv = value.get("formal_worker_argv")
    return bool(
        _recovery_epoch003_external_identity_valid(
            reference,
            role=_RECOVERY_EPOCH003_REFERENCE_ROLE,
            schema=_RECOVERY_EPOCH003_REFERENCE_SCHEMA,
            path=_RECOVERY_EPOCH003_REFERENCE_PATH,
        )
        and _recovery_epoch003_environment_valid(environment)
        and value.get("environment_policy_sha256")
        == artifact_sha256(environment)
        and type(preflight_argv) is list
        and preflight_argv == _RECOVERY_EPOCH003_PREFLIGHT_ARGV
        and value.get("preflight_argv_sha256")
        == artifact_sha256(preflight_argv)
        and type(formal_argv) is list
        and formal_argv
        == [
            *_RECOVERY_EPOCH003_FORMAL_WORKER_ARGV_PREFIX,
            *_RECOVERY_EPOCH003_FORMAL_NODE_IDS,
        ]
        and value.get("formal_worker_argv_sha256")
        == artifact_sha256(formal_argv)
    )


def _recovery_epoch003_source_valid(
    value: Any,
    bootstrap: Mapping[str, Any],
) -> bool:
    if (
        type(value) is not dict
        or set(value) != RECOVERY_EPOCH003_SOURCE_CLOSURE_KEYS
        or value.get("schema_version")
        != RECOVERY_EPOCH003_SOURCE_CLOSURE_SCHEMA
        or value.get("repository_full_name") != "MassyuRed/mashos-api"
        or value.get("source_ref") != "refs/heads/main"
        or value.get("worktree_clean") is not True
        or value.get("epoch003_p0_external_identity_sha256")
        != _RECOVERY_EPOCH003_P0_EXTERNAL_IDENTITY_SHA256
    ):
        return False
    if (
        not _recovery_epoch003_sha1(value.get("source_commit_sha1"))
        or not _recovery_epoch003_sha1(value.get("source_tree_sha1"))
        or value.get("source_commit_sha1")
        != bootstrap.get("source_commit_sha1")
        or value.get("source_tree_sha1")
        != bootstrap.get("source_tree_sha1")
        or value.get("formal_test_manifest_sha256")
        != bootstrap.get("formal_test_manifest_sha256")
        or value.get("bootstrap_closure_sha256")
        != bootstrap.get("bootstrap_closure_sha256")
        or value.get(
            "reference_runtime_observation_external_identity_sha256"
        )
        != bootstrap[
            "reference_runtime_observation_external_identity"
        ].get("identity_sha256")
        or value.get("source_closure_sha256")
        != _recovery_epoch003_hash_without(
            value,
            "source_closure_sha256",
        )
    ):
        return False
    sha256_fields = RECOVERY_EPOCH003_SOURCE_CLOSURE_KEYS - {
        "schema_version",
        "repository_full_name",
        "source_ref",
        "source_commit_sha1",
        "source_tree_sha1",
        "worktree_clean",
    }
    return all(
        _recovery_epoch003_sha256(value.get(key))
        for key in sha256_fields
    )


def validate_recovery_epoch003_source_bootstrap_contract_state(
    state: Mapping[str, Any],
) -> tuple[str, ...]:
    """Validate the versioned Epoch003 source/bootstrap pair without effects."""

    try:
        if type(state) is not dict:
            return ("SOURCE_BOOTSTRAP_BASELINE_MISMATCH",)
        source = state.get("source_closure")
        bootstrap = state.get("bootstrap_closure")
        if type(source) is not dict or type(bootstrap) is not dict:
            return ("SOURCE_BOOTSTRAP_BASELINE_MISMATCH",)
        pair = (
            source.get("schema_version"),
            bootstrap.get("schema_version"),
        )
        if pair not in RECOVERY_EPOCH003_KNOWN_SCHEMA_PAIRS:
            return ("BOOTSTRAP_SCHEMA_PAIR_UNSUPPORTED",)
        if pair == RECOVERY_EPOCH003_KNOWN_SCHEMA_PAIRS[0]:
            # The historical pair keeps its already-accepted meaning.  This
            # additive dispatch does not reinterpret its inner schema.
            return ()
        if _recovery_epoch003_placeholder_present(bootstrap):
            return (
                "RECOVERY_EPOCH003_RUNTIME_IDENTITY_PLACEHOLDER_FORBIDDEN",
            )
        if (
            not _recovery_epoch003_bootstrap_valid(bootstrap)
            or not _recovery_epoch003_source_valid(source, bootstrap)
        ):
            return ("SOURCE_BOOTSTRAP_BASELINE_MISMATCH",)
        return ()
    except (
        AttributeError,
        KeyError,
        RecursionError,
        TypeError,
        UnicodeError,
        ValueError,
    ):
        return ("SOURCE_BOOTSTRAP_BASELINE_MISMATCH",)


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
    "RECOVERY_EPOCH003_SOURCE_CLOSURE_SCHEMA",
    "RECOVERY_EPOCH003_BOOTSTRAP_MANIFEST_SCHEMA",
    "RECOVERY_EPOCH003_SOURCE_CLOSURE_KEYS",
    "RECOVERY_EPOCH003_BOOTSTRAP_MANIFEST_KEYS",
    "RECOVERY_EPOCH003_KNOWN_SCHEMA_PAIRS",
    "build_recovery_epoch003_source_bootstrap_closure",
    "validate_recovery_epoch003_source_bootstrap_contract_state",
]
