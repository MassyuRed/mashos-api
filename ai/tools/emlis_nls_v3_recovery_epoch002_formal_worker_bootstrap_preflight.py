#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

"""Pre-reservation bootstrap validation for Recovery Epoch 002.

Importing this module performs no filesystem, package, pytest, subprocess, or
network action.  Callers must supply observed state explicitly.  In
particular, this preflight never imports a formal test module and never calls
``pytest.main``.
"""

import argparse
import base64
import csv
from copy import deepcopy
from datetime import datetime, timezone
from email.parser import BytesParser
from email.policy import compat32
import hashlib
import json
import os
from pathlib import Path, PurePosixPath
import re
import secrets
import shutil
import stat
import subprocess
import sys
from typing import Any, Mapping
import zipfile

_HERE = Path(__file__).resolve()
_REPO_ROOT = _HERE.parents[2]
_INFERENCE_ROOT = _REPO_ROOT / "ai" / "services" / "ai_inference"
_TOOLS_ROOT = _REPO_ROOT / "ai" / "tools"
for _import_root in (_INFERENCE_ROOT, _TOOLS_ROOT):
    if str(_import_root) not in sys.path:
        sys.path.insert(0, str(_import_root))

from emlis_ai_nls_v3_artifact_contract import (
    artifact_sha256,
    canonical_json_bytes,
)
from emlis_ai_recovery_epoch002_sequence_ledger_v3 import (
    validate_recovery_epoch002_event1_artifact,
    validate_recovery_epoch003_sequence_event1_contract_state,
)
from emlis_ai_recovery_epoch002_canonical_current_closure_v3 import (
    validate_recovery_epoch002_bootstrap_manifest,
    validate_recovery_epoch002_formal_node_registry,
    validate_recovery_epoch002_operational_bootstrap_manifest,
    validate_recovery_epoch002_operational_source_manifest,
    validate_recovery_epoch002_source_closure,
    validate_recovery_epoch003_source_bootstrap_contract_state,
)
from emlis_nls_v3_recovery_epoch002_closure_receipt_verify import (
    verify_recovery_epoch002_operational_artifact_identity,
    verify_recovery_epoch002_published_artifact,
    verify_recovery_epoch003_bootstrap_source_runtime_contract,
    verify_recovery_epoch003_bootstrap_source_runtime_contract_current,
)
from packaging.requirements import InvalidRequirement, Requirement
from packaging.tags import sys_tags
from packaging.utils import InvalidWheelFilename, parse_wheel_filename


def _keys(value: str) -> frozenset[str]:
    return frozenset(value.split())


RECOVERY_EPOCH002_READINESS_SCHEMA = (
    "cocolon.emlis.nls_v3.recovery_epoch002."
    "formal_worker_bootstrap_readiness.v1"
)
RECOVERY_EPOCH002_READINESS_KEYS = _keys(
    """
    schema_version authority_token event1_challenge_id preflight_challenge_id
    preflight_id candidate_version_id logical_cycle_id recovery_epoch_id
    source_baseline_event source_closure bootstrap_closure
    python_runtime_identity pytest_distribution_identity
    dependency_lock_identity environment_profile preflight_owner_identity
    preflight_argv_sha256 loaded_plugin_manifest_sha256 readiness_state
    formal_collection_state formal_execution_state pytest_main_called
    owner_validation_state independent_verification_state
    preflight_started_at_utc preflight_finished_at_utc readiness_receipt_path
    automatic_progression body_free bootstrap_readiness_receipt_sha256
    """
)
RECOVERY_EPOCH002_CONFTEST_PLUGIN_MODE = "DISABLED_BY_NOCONFTEST"
RECOVERY_EPOCH002_FORMAL_PYTEST_OPTIONS = (
    "-q",
    "--disable-warnings",
    "--noconftest",
    "-p",
    "no:cacheprovider",
)
RECOVERY_EPOCH002_FORMAL_PLUGIN_ALLOWLIST: tuple[str, ...] = ()

RECOVERY_EPOCH002_DEPENDENCY_LOCK_SCHEMA = (
    "cocolon.emlis.nls_v3.recovery_epoch002."
    "formal_worker_bootstrap_lock.v1"
)
RECOVERY_EPOCH002_DEPENDENCY_LOCK_KEYS = _keys(
    """
    schema_version identity_class target root_imports root_requirements
    module_distribution_map distribution_count distributions
    pip_require_hashes_lines resolution lock_sha256
    """
)
RECOVERY_EPOCH002_DEPENDENCY_LOCK_DISTRIBUTION_KEYS = _keys(
    """
    normalized_distribution_name distribution_version wheel_filename
    wheel_sha256 wheel_record_sha256 installed_record_closure_sha256
    requires_dist selected_dependency_names top_level_imports
    """
)
RECOVERY_EPOCH002_RUNTIME_MATERIALIZATION_KEYS = _keys(
    """
    schema_version runtime_root_identity_sha256
    python_executable_relative_path installed_directory_relative_path
    dependency_lock_raw_sha256 wheel_bundle_manifest_sha256
    distribution_count runtime_materialization_state body_free
    runtime_materialization_sha256
    """
)
RECOVERY_EPOCH002_OPERATIONAL_PREFLIGHT_ATTESTATION_KEYS = _keys(
    """
    schema_version logical_cycle_id recovery_epoch_id candidate_version_id
    preflight_id source_baseline_event_identity_sha256 source_commit_sha1
    source_tree_sha1 bootstrap_closure_sha256 dependency_lock_raw_sha256
    runtime_materialization_sha256 bootstrap_readiness_receipt_sha256
    readiness_receipt_path operational_issue_codes
    formal_exact134_invocation_count reservation_count_delta
    owner_validation_state independent_verification_state
    body_free operational_preflight_attestation_sha256
    """
)
_INSTALLER_IDENTITY_CLASS = "PIP_REQUIRE_HASHES_WHEEL_LOCK_V1"
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_ROOT_REQUIREMENT_RE = re.compile(
    r"^(?P<name>[A-Za-z0-9_.-]+)==(?P<version>[^\s]+)$"
)
_UTC_SECONDS_RE = re.compile(
    r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$"
)


def _hash_without(value: Mapping[str, Any], key: str) -> str:
    material = deepcopy(dict(value))
    material.pop(key, None)
    return artifact_sha256(material)


def _manifest_has_import(
    manifest: Mapping[str, Any],
    import_name: str,
) -> bool:
    rows = manifest.get("import_manifest")
    return type(rows) is list and any(
        type(row) is dict and row.get("import_name") == import_name
        for row in rows
    )


def _readiness_reconciliation_invalid(
    state: Mapping[str, Any],
) -> bool:
    manifest = state.get("bootstrap_manifest")
    if not isinstance(manifest, Mapping):
        return True
    argv = manifest.get("formal_worker_argv")
    return (
        state.get("pytest_main_called") is not False
        or state.get("collection_started") is not False
        or state.get("formal_test_module_imported") is not False
        or state.get("loaded_plugins") != []
        or manifest.get("conftest_plugin_mode")
        != RECOVERY_EPOCH002_CONFTEST_PLUGIN_MODE
        or manifest.get("pytest_plugins_environment_variable_removed")
        is not True
        or manifest.get("pytest_entrypoint_autoload_disabled") is not True
        or manifest.get("explicit_plugin_allowlist")
        != list(RECOVERY_EPOCH002_FORMAL_PLUGIN_ALLOWLIST)
        or manifest.get("loaded_plugin_manifest") != []
        or type(argv) is not list
        or "--noconftest" not in argv
        or not _manifest_has_import(manifest, "pytest")
        or state.get("runtime_materialization_matches_lock") is not True
        or state.get("static_import_manifest_complete") is not True
        or state.get("owner_issue_codes") != []
        or state.get("independent_issue_codes") != []
    )


def validate_recovery_epoch002_bootstrap_state(
    state: Mapping[str, Any],
) -> tuple[str, ...]:
    """Reconcile preflight observations without importing formal tests."""

    if type(state) is not dict:
        return ("READINESS_FORBIDDEN",)
    if _readiness_reconciliation_invalid(state):
        return ("READINESS_FORBIDDEN",)
    manifest = state.get("bootstrap_manifest")
    readiness = state.get("readiness_receipt")
    if (
        state.get("preflight_present") is not True
        or state.get("reservation_count_delta") != 0
        or state.get("formal_exact134_invocation_count") != 0
        or validate_recovery_epoch002_bootstrap_manifest(manifest)
        or validate_recovery_epoch002_readiness_artifact(readiness)
        or type(readiness) is not dict
        or readiness.get("bootstrap_closure") != manifest
        or readiness.get("dependency_lock_identity")
        != manifest.get("dependency_lock_identity")
    ):
        return ("READINESS_FORBIDDEN",)
    parity_pairs = (
        ("python_runtime_sha256", "child_python_runtime_sha256"),
        ("pytest_identity_sha256", "child_pytest_identity_sha256"),
        (
            "environment_profile_sha256",
            "child_environment_profile_sha256",
        ),
        ("preflight_argv_sha256", "child_preflight_argv_sha256"),
        (
            "formal_worker_argv_sha256",
            "child_formal_worker_argv_sha256",
        ),
        ("source_closure_sha256", "child_source_closure_sha256"),
        ("bootstrap_closure_sha256", "child_bootstrap_closure_sha256"),
    )
    if any(
        not isinstance(state.get(left), str)
        or _SHA256_RE.fullmatch(state[left]) is None
        or state.get(left) != state.get(right)
        for left, right in parity_pairs
    ):
        return ("READINESS_FORBIDDEN",)
    if (
        state.get("readiness_is_immediate_base") is not True
        or state.get("readiness_is_stale") is not False
        or state.get("readiness_reused") is not False
    ):
        return ("RESERVATION_FORBIDDEN",)
    return ()


def validate_recovery_epoch002_readiness_artifact(
    readiness: Mapping[str, Any],
) -> tuple[str, ...]:
    """Strictly validate an actual readiness receipt."""

    if type(readiness) is not dict:
        return ("READINESS_FORBIDDEN",)
    if set(readiness) != RECOVERY_EPOCH002_READINESS_KEYS:
        return ("READINESS_FORBIDDEN",)
    if (
        readiness.get("schema_version")
        != RECOVERY_EPOCH002_READINESS_SCHEMA
        or readiness.get("readiness_state")
        != "READY_FOR_EXACT_ONE_FORMAL_SPAWN"
        or readiness.get("formal_collection_state") != "NOT_STARTED"
        or readiness.get("formal_execution_state") != "NOT_STARTED"
        or readiness.get("pytest_main_called") is not False
        or readiness.get("owner_validation_state") != "VALID"
        or readiness.get("independent_verification_state") != "VALID"
        or readiness.get("automatic_progression") is not False
        or readiness.get("body_free") is not True
    ):
        return ("READINESS_FORBIDDEN",)
    if (
        readiness.get("bootstrap_readiness_receipt_sha256")
        != _hash_without(
            readiness,
            "bootstrap_readiness_receipt_sha256",
        )
    ):
        return ("READINESS_FORBIDDEN",)
    return ()


def _utc_seconds(value: Any) -> datetime | None:
    if not isinstance(value, str) or _UTC_SECONDS_RE.fullmatch(value) is None:
        return None
    try:
        parsed = datetime.strptime(
            value,
            "%Y-%m-%dT%H:%M:%SZ",
        ).replace(tzinfo=timezone.utc)
    except ValueError:
        return None
    return parsed


def _new_readiness_path_valid(value: Any) -> bool:
    if not isinstance(value, str) or not value:
        return False
    path = Path(value)
    return (
        not path.is_absolute()
        and path.as_posix() == value
        and ".." not in path.parts
        and path.parent.as_posix()
        == "EmlisAIの実装済み資料/documents"
        and path.suffix == ".json"
    )


def validate_recovery_epoch002_operational_readiness_bindings(
    readiness: Mapping[str, Any],
    manifest: Mapping[str, Any],
    *,
    expected_receipt_path: str | None = None,
) -> tuple[str, ...]:
    """Bind a readiness receipt to the observations that created it."""

    if (
        validate_recovery_epoch002_readiness_artifact(readiness)
        or validate_recovery_epoch002_bootstrap_manifest(manifest)
        or type(readiness) is not dict
        or type(manifest) is not dict
    ):
        return ("READINESS_FORBIDDEN",)
    source_identity = readiness.get("source_baseline_event")
    source_closure = readiness.get("source_closure")
    owner_rows = manifest.get("formal_owner_artifacts")
    owner_row = next(
        (
            row
            for row in owner_rows
            if type(row) is dict
            and row.get("role") == "preflight_owner"
        ),
        None,
    ) if type(owner_rows) is list else None
    started = _utc_seconds(readiness.get("preflight_started_at_utc"))
    finished = _utc_seconds(readiness.get("preflight_finished_at_utc"))
    receipt_path = readiness.get("readiness_receipt_path")
    if (
        readiness.get("logical_cycle_id") != "NLS_V3_CYCLE_001"
        or readiness.get("recovery_epoch_id")
        != "NLS_V3_CYCLE001_RECOVERY_EPOCH_002"
        or not isinstance(readiness.get("authority_token"), str)
        or not readiness.get("authority_token")
        or not isinstance(readiness.get("candidate_version_id"), str)
        or not readiness.get("candidate_version_id")
        or readiness.get("candidate_version_id") == "nls_v3_rc_0034"
        or any(
            _SHA256_RE.fullmatch(str(readiness.get(key, ""))) is None
            for key in (
                "event1_challenge_id",
                "preflight_challenge_id",
                "preflight_id",
                "preflight_argv_sha256",
                "loaded_plugin_manifest_sha256",
            )
        )
        or readiness.get("event1_challenge_id")
        == readiness.get("preflight_challenge_id")
        or verify_recovery_epoch002_operational_artifact_identity(
            source_identity
        )
        or source_identity.get("artifact_role")
        not in {"EVENT1", "SOURCE_BASELINE_EVENT"}
        or validate_recovery_epoch002_source_closure(source_closure)
        or readiness.get("bootstrap_closure") != manifest
        or readiness.get("python_runtime_identity")
        != manifest.get("python_runtime_identity")
        or readiness.get("pytest_distribution_identity")
        != manifest.get("pytest_distribution_identity")
        or readiness.get("dependency_lock_identity")
        != manifest.get("dependency_lock_identity")
        or readiness.get("environment_profile")
        != manifest.get("environment_profile")
        or readiness.get("preflight_argv_sha256")
        != manifest.get("preflight_argv_sha256")
        or readiness.get("loaded_plugin_manifest_sha256")
        != manifest.get("loaded_plugin_manifest_sha256")
        or owner_row is None
        or readiness.get("preflight_owner_identity")
        != {
            "path": owner_row["path"],
            "git_blob_sha1": owner_row["git_blob_sha1"],
            "raw_sha256": owner_row["raw_sha256"],
        }
        or started is None
        or finished is None
        or started > finished
        or not _new_readiness_path_valid(receipt_path)
        or (
            expected_receipt_path is not None
            and receipt_path != expected_receipt_path
        )
    ):
        return ("READINESS_FORBIDDEN",)
    preflight_preimage = {
        "logical_cycle_id": readiness["logical_cycle_id"],
        "recovery_epoch_id": readiness["recovery_epoch_id"],
        "candidate_version_id": readiness["candidate_version_id"],
        "authority_token": readiness["authority_token"],
        "event1_challenge_id": readiness["event1_challenge_id"],
        "preflight_challenge_id": readiness["preflight_challenge_id"],
        "source_baseline_event_identity_sha256": source_identity[
            "identity_sha256"
        ],
        "source_closure_sha256": source_closure[
            "source_closure_sha256"
        ],
        "bootstrap_closure_sha256": manifest[
            "bootstrap_closure_sha256"
        ],
    }
    if readiness.get("preflight_id") != artifact_sha256(
        preflight_preimage
    ):
        return ("READINESS_FORBIDDEN",)
    return ()


def build_recovery_epoch002_readiness_artifact(
    *,
    authority_token: str,
    event1_challenge_id: str,
    preflight_challenge_id: str,
    candidate_version_id: str,
    source_baseline_event: Mapping[str, Any],
    source_closure: Mapping[str, Any],
    bootstrap_manifest: Mapping[str, Any],
    preflight_started_at_utc: str,
    preflight_finished_at_utc: str,
    readiness_receipt_path: str,
) -> dict[str, Any]:
    """Build the body-free receipt from already-observed preflight facts."""

    manifest = deepcopy(dict(bootstrap_manifest))
    source = deepcopy(dict(source_closure))
    event_identity = deepcopy(dict(source_baseline_event))
    owner_rows = manifest.get("formal_owner_artifacts")
    owner_row = next(
        (
            row
            for row in owner_rows
            if type(row) is dict
            and row.get("role") == "preflight_owner"
        ),
        None,
    ) if type(owner_rows) is list else None
    if owner_row is None:
        raise ValueError("READINESS_FORBIDDEN")
    preflight_preimage = {
        "logical_cycle_id": "NLS_V3_CYCLE_001",
        "recovery_epoch_id": "NLS_V3_CYCLE001_RECOVERY_EPOCH_002",
        "candidate_version_id": candidate_version_id,
        "authority_token": authority_token,
        "event1_challenge_id": event1_challenge_id,
        "preflight_challenge_id": preflight_challenge_id,
        "source_baseline_event_identity_sha256": event_identity.get(
            "identity_sha256"
        ),
        "source_closure_sha256": source.get("source_closure_sha256"),
        "bootstrap_closure_sha256": manifest.get(
            "bootstrap_closure_sha256"
        ),
    }
    readiness: dict[str, Any] = {
        "schema_version": RECOVERY_EPOCH002_READINESS_SCHEMA,
        "authority_token": authority_token,
        "event1_challenge_id": event1_challenge_id,
        "preflight_challenge_id": preflight_challenge_id,
        "preflight_id": artifact_sha256(preflight_preimage),
        "candidate_version_id": candidate_version_id,
        "logical_cycle_id": "NLS_V3_CYCLE_001",
        "recovery_epoch_id": "NLS_V3_CYCLE001_RECOVERY_EPOCH_002",
        "source_baseline_event": event_identity,
        "source_closure": source,
        "bootstrap_closure": manifest,
        "python_runtime_identity": deepcopy(
            manifest.get("python_runtime_identity")
        ),
        "pytest_distribution_identity": deepcopy(
            manifest.get("pytest_distribution_identity")
        ),
        "dependency_lock_identity": deepcopy(
            manifest.get("dependency_lock_identity")
        ),
        "environment_profile": deepcopy(
            manifest.get("environment_profile")
        ),
        "preflight_owner_identity": {
            "path": owner_row["path"],
            "git_blob_sha1": owner_row["git_blob_sha1"],
            "raw_sha256": owner_row["raw_sha256"],
        },
        "preflight_argv_sha256": manifest.get("preflight_argv_sha256"),
        "loaded_plugin_manifest_sha256": manifest.get(
            "loaded_plugin_manifest_sha256"
        ),
        "readiness_state": "READY_FOR_EXACT_ONE_FORMAL_SPAWN",
        "formal_collection_state": "NOT_STARTED",
        "formal_execution_state": "NOT_STARTED",
        "pytest_main_called": False,
        "owner_validation_state": "VALID",
        "independent_verification_state": "VALID",
        "preflight_started_at_utc": preflight_started_at_utc,
        "preflight_finished_at_utc": preflight_finished_at_utc,
        "readiness_receipt_path": readiness_receipt_path,
        "automatic_progression": False,
        "body_free": True,
        "bootstrap_readiness_receipt_sha256": "",
    }
    readiness["bootstrap_readiness_receipt_sha256"] = _hash_without(
        readiness,
        "bootstrap_readiness_receipt_sha256",
    )
    if validate_recovery_epoch002_operational_readiness_bindings(
        readiness,
        manifest,
        expected_receipt_path=readiness_receipt_path,
    ):
        raise ValueError("READINESS_FORBIDDEN")
    return readiness


def validate_recovery_epoch002_event1_publication_binding(
    *,
    event1_artifact: Mapping[str, Any],
    event1_external_identity: Mapping[str, Any],
    event1_publication_state: Mapping[str, Any],
    readiness: Mapping[str, Any],
) -> tuple[str, ...]:
    """Verify the published Event1 that authorizes bootstrap preflight."""

    if (
        validate_recovery_epoch002_event1_artifact(event1_artifact)
        or verify_recovery_epoch002_operational_artifact_identity(
            event1_external_identity
        )
        or type(event1_publication_state) is not dict
        or event1_publication_state.get("artifact_role")
        != "SOURCE_BASELINE_EVENT"
        or event1_publication_state.get("artifact") != event1_artifact
        or event1_publication_state.get("artifact_external_identity")
        != event1_external_identity
        or verify_recovery_epoch002_published_artifact(
            event1_publication_state
        )
        or event1_external_identity.get("artifact_role")
        not in {"EVENT1", "SOURCE_BASELINE_EVENT"}
        or event1_external_identity.get("logical_artifact_sha256")
        != event1_artifact.get("event_sha256")
        or readiness.get("source_baseline_event")
        != event1_external_identity
        or readiness.get("logical_cycle_id")
        != event1_artifact.get("logical_cycle_id")
        or readiness.get("recovery_epoch_id")
        != event1_artifact.get("recovery_epoch_id")
        or readiness.get("candidate_version_id")
        != event1_artifact.get("candidate_version_id")
        or readiness.get("event1_challenge_id")
        != event1_artifact.get("challenge_id")
        or readiness.get("source_closure")
        != event1_artifact.get("source_closure")
        or readiness.get("bootstrap_closure")
        != event1_artifact.get("bootstrap_closure")
    ):
        return ("READINESS_FORBIDDEN",)
    return ()


def _wheel_record_sha256(path: Path) -> str | None:
    try:
        with zipfile.ZipFile(path) as archive:
            names = [
                name
                for name in archive.namelist()
                if name.endswith(".dist-info/RECORD")
            ]
            if len(names) != 1:
                return None
            return hashlib.sha256(archive.read(names[0])).hexdigest()
    except (OSError, zipfile.BadZipFile, KeyError):
        return None


def _wheel_metadata_identity(
    path: Path,
) -> dict[str, Any] | None:
    try:
        with zipfile.ZipFile(path) as archive:
            names = archive.namelist()
            metadata_names = [
                name for name in names
                if name.endswith(".dist-info/METADATA")
            ]
            top_level_names = [
                name for name in names
                if name.endswith(".dist-info/top_level.txt")
            ]
            if len(metadata_names) != 1:
                return None
            message = BytesParser(policy=compat32).parsebytes(
                archive.read(metadata_names[0])
            )
            raw_name = message.get("Name")
            version = message.get("Version")
            if not isinstance(raw_name, str) or not isinstance(version, str):
                return None
            top_levels: set[str] = set()
            if len(top_level_names) == 1:
                top_levels.update(
                    line.strip()
                    for line in archive.read(top_level_names[0])
                    .decode("utf-8")
                    .splitlines()
                    if line.strip()
                )
            if not top_levels:
                for member in names:
                    parts = member.split("/")
                    if not parts:
                        continue
                    if parts[0].endswith(".dist-info"):
                        continue
                    if parts[0].endswith(".data"):
                        if (
                            len(parts) >= 3
                            and parts[1] in {"purelib", "platlib"}
                        ):
                            parts = parts[2:]
                        else:
                            continue
                    first = parts[0]
                    if first.endswith(".py"):
                        first = first[:-3]
                    elif "." in first and len(parts) == 1:
                        first = first.split(".", 1)[0]
                    if first.isidentifier() and first != "__pycache__":
                        top_levels.add(first)
            return {
                "normalized_distribution_name": (
                    _normalize_distribution_name(raw_name)
                ),
                "distribution_version": version,
                "requires_dist": sorted(
                    message.get_all("Requires-Dist") or []
                ),
                "top_level_imports": sorted(top_levels),
            }
    except (
        OSError,
        UnicodeError,
        zipfile.BadZipFile,
        KeyError,
    ):
        return None


def _normalize_distribution_name(value: str) -> str:
    return re.sub(r"[-_.]+", "-", value).lower()


def _installed_distribution_closure(
    directory: Path,
    *,
    runtime_root: Path | None = None,
) -> dict[str, tuple[str, str]] | None:
    """Return name -> (version, verified importable-file closure).

    Every non-pyc RECORD entry is checked against an actual owner-only
    runtime tree.  Entry-point scripts outside ``site-packages`` are verified
    but excluded from the import closure; RECORD itself is also excluded
    because it embeds path-dependent entry-point hashes.
    """

    if directory.is_symlink() or not directory.is_dir():
        return None
    root = directory if runtime_root is None else runtime_root
    if root.is_symlink() or not root.is_dir():
        return None
    directory = directory.absolute()
    root = root.absolute()
    try:
        directory.relative_to(root)
    except ValueError:
        return None

    def actual_file(path_text: str) -> tuple[Path, bool] | None:
        candidate = Path(
            os.path.normpath(str(directory / path_text))
        ).absolute()
        try:
            candidate.relative_to(root)
        except ValueError:
            return None
        current = root
        for component in candidate.relative_to(root).parts:
            current = current / component
            try:
                current_stat = current.lstat()
            except OSError:
                return None
            if stat.S_ISLNK(current_stat.st_mode):
                return None
        try:
            final_stat = candidate.lstat()
        except OSError:
            return None
        if not stat.S_ISREG(final_stat.st_mode):
            return None
        try:
            candidate.relative_to(directory)
            importable = True
        except ValueError:
            importable = False
        return candidate, importable

    def digest_matches(path: Path, encoded: str, size: str) -> bool:
        payload = path.read_bytes()
        if size and int(size) != len(payload):
            return False
        if not encoded:
            return True
        try:
            algorithm, expected = encoded.split("=", 1)
        except ValueError:
            return False
        if algorithm != "sha256":
            return False
        actual = base64.urlsafe_b64encode(
            hashlib.sha256(payload).digest()
        ).rstrip(b"=").decode("ascii")
        return actual == expected

    result: dict[str, tuple[str, str]] = {}
    try:
        metadata_paths = sorted(directory.glob("*.dist-info/METADATA"))
        for metadata_path in metadata_paths:
            record_path = metadata_path.parent / "RECORD"
            if (
                metadata_path.is_symlink()
                or record_path.is_symlink()
                or not metadata_path.is_file()
                or not record_path.is_file()
            ):
                return None
            message = BytesParser(policy=compat32).parsebytes(
                metadata_path.read_bytes()
            )
            raw_name = message.get("Name")
            version = message.get("Version")
            if not isinstance(raw_name, str) or not isinstance(version, str):
                return None
            name = _normalize_distribution_name(raw_name)
            if name in result:
                return None
            entries: list[dict[str, Any]] = []
            with record_path.open(
                encoding="utf-8",
                newline="",
            ) as handle:
                for path_text, digest, size in csv.reader(handle):
                    if (
                        path_text.endswith(".pyc")
                        or "/__pycache__/" in path_text
                    ):
                        continue
                    observed = actual_file(path_text)
                    if observed is None:
                        return None
                    actual_path, importable = observed
                    if not digest_matches(actual_path, digest, size):
                        return None
                    if (
                        not importable
                        or actual_path == record_path.absolute()
                    ):
                        continue
                    payload = actual_path.read_bytes()
                    entries.append(
                        {
                            "path": actual_path.relative_to(
                                directory
                            ).as_posix(),
                            "sha256": hashlib.sha256(payload).hexdigest(),
                            "size": len(payload),
                        }
                    )
            entries.sort(key=lambda row: row["path"])
            result[name] = (
                version,
                artifact_sha256({"record_entries": entries}),
            )
    except (OSError, UnicodeError, ValueError):
        return None
    return result


def validate_recovery_epoch002_dependency_lock(
    lock: Mapping[str, Any],
    *,
    wheel_directory: Path | None = None,
    installed_directory: Path | None = None,
    runtime_root: Path | None = None,
) -> tuple[str, ...]:
    """Validate the exact-version, exact-wheel bootstrap lock."""

    if type(lock) is not dict:
        return ("DEPENDENCY_LOCK_INVALID",)
    if set(lock) != RECOVERY_EPOCH002_DEPENDENCY_LOCK_KEYS:
        return ("DEPENDENCY_LOCK_INVALID",)
    if (
        lock.get("schema_version")
        != RECOVERY_EPOCH002_DEPENDENCY_LOCK_SCHEMA
        or lock.get("identity_class") != _INSTALLER_IDENTITY_CLASS
    ):
        return ("DEPENDENCY_LOCK_INVALID",)
    rows = lock.get("distributions")
    if type(rows) is not list or not rows:
        return ("DEPENDENCY_LOCK_INVALID",)
    if lock.get("distribution_count") != len(rows):
        return ("DEPENDENCY_LOCK_INVALID",)
    if any(type(row) is not dict for row in rows):
        return ("DEPENDENCY_LOCK_INVALID",)
    row_names = [
        row.get("normalized_distribution_name")
        for row in rows
    ]
    if (
        any(not isinstance(name, str) for name in row_names)
        or row_names != sorted(row_names)
    ):
        return ("DEPENDENCY_LOCK_INVALID",)
    names: set[str] = set()
    versions: dict[str, str] = {}
    dependency_graph: dict[str, list[str]] = {}
    expected_lines: list[str] = []
    parsed_requirements: dict[str, list[Requirement]] = {}
    compatible_tags = frozenset(sys_tags())
    for row in rows:
        if type(row) is not dict:
            return ("DEPENDENCY_LOCK_INVALID",)
        if (
            set(row)
            != RECOVERY_EPOCH002_DEPENDENCY_LOCK_DISTRIBUTION_KEYS
        ):
            return ("DEPENDENCY_LOCK_INVALID",)
        name = row.get("normalized_distribution_name")
        version = row.get("distribution_version")
        filename = row.get("wheel_filename")
        wheel_hash = row.get("wheel_sha256")
        record_hash = row.get("wheel_record_sha256")
        installed_hash = row.get("installed_record_closure_sha256")
        requires = row.get("requires_dist")
        selected = row.get("selected_dependency_names")
        top_levels = row.get("top_level_imports")
        if (
            not isinstance(name, str)
            or not name
            or name != _normalize_distribution_name(name)
            or name in names
            or not isinstance(version, str)
            or not version
            or not isinstance(filename, str)
            or not filename.endswith(".whl")
            or not isinstance(wheel_hash, str)
            or _SHA256_RE.fullmatch(wheel_hash) is None
            or not isinstance(record_hash, str)
            or _SHA256_RE.fullmatch(record_hash) is None
            or not isinstance(installed_hash, str)
            or _SHA256_RE.fullmatch(installed_hash) is None
            or type(requires) is not list
            or any(not isinstance(item, str) for item in requires)
            or requires != sorted(requires)
            or type(selected) is not list
            or any(
                not isinstance(item, str)
                or item != _normalize_distribution_name(item)
                for item in selected
            )
            or selected != sorted(set(selected))
            or type(top_levels) is not list
            or any(
                not isinstance(item, str) or not item
                for item in top_levels
            )
            or top_levels != sorted(set(top_levels))
        ):
            return ("DEPENDENCY_LOCK_INVALID",)
        names.add(name)
        versions[name] = version
        dependency_graph[name] = selected
        try:
            parsed_requirements[name] = [
                Requirement(requirement)
                for requirement in requires
            ]
            wheel_name, wheel_version, _, wheel_tags = (
                parse_wheel_filename(filename)
            )
        except (InvalidRequirement, InvalidWheelFilename):
            return ("DEPENDENCY_LOCK_INVALID",)
        if (
            _normalize_distribution_name(str(wheel_name)) != name
            or str(wheel_version) != version
            or not compatible_tags.intersection(wheel_tags)
        ):
            return ("DEPENDENCY_LOCK_INVALID",)
        expected_lines.append(
            f"{name}=={version} --hash=sha256:{wheel_hash}"
        )
        if wheel_directory is not None:
            wheel = wheel_directory / filename
            try:
                actual_hash = hashlib.sha256(wheel.read_bytes()).hexdigest()
            except OSError:
                return ("DEPENDENCY_LOCK_WHEEL_MISSING",)
            if actual_hash != wheel_hash:
                return ("DEPENDENCY_LOCK_WHEEL_HASH_MISMATCH",)
            if _wheel_record_sha256(wheel) != record_hash:
                return ("DEPENDENCY_LOCK_RECORD_HASH_MISMATCH",)
            metadata_identity = _wheel_metadata_identity(wheel)
            if (
                metadata_identity is None
                or metadata_identity["normalized_distribution_name"] != name
                or metadata_identity["distribution_version"] != version
                or metadata_identity["requires_dist"] != requires
                or metadata_identity["top_level_imports"] != top_levels
            ):
                return ("DEPENDENCY_LOCK_WHEEL_METADATA_MISMATCH",)
    if any(
        dependency not in names
        for selected in dependency_graph.values()
        for dependency in selected
    ):
        return ("DEPENDENCY_LOCK_INVALID",)
    if lock.get("pip_require_hashes_lines") != sorted(expected_lines):
        return ("DEPENDENCY_LOCK_INVALID",)

    root_requirements = lock.get("root_requirements")
    root_imports = lock.get("root_imports")
    if (
        type(root_requirements) is not list
        or not root_requirements
        or any(not isinstance(item, str) for item in root_requirements)
        or root_requirements != sorted(set(root_requirements))
        or type(root_imports) is not list
        or not root_imports
        or any(not isinstance(item, str) or not item for item in root_imports)
        or root_imports != sorted(set(root_imports))
    ):
        return ("DEPENDENCY_LOCK_INVALID",)
    root_names: set[str] = set()
    for requirement in root_requirements:
        if not isinstance(requirement, str):
            return ("DEPENDENCY_LOCK_INVALID",)
        match = _ROOT_REQUIREMENT_RE.fullmatch(requirement)
        if match is None:
            return ("DEPENDENCY_LOCK_INVALID",)
        name = _normalize_distribution_name(match.group("name"))
        if (
            name in root_names
            or versions.get(name) != match.group("version")
        ):
            return ("DEPENDENCY_LOCK_INVALID",)
        root_names.add(name)
    reachable = set(root_names)
    pending = list(sorted(root_names))
    while pending:
        current = pending.pop()
        for dependency in dependency_graph.get(current, ()):
            if dependency not in reachable:
                reachable.add(dependency)
                pending.append(dependency)
    if reachable != names:
        return ("DEPENDENCY_LOCK_INVALID",)

    resolution = lock.get("resolution")
    if (
        type(resolution) is not dict
        or resolution.get("allow_sdist") is not False
        or resolution.get("hashes_required") is not True
        or resolution.get("index_access_during_install") is not False
        or resolution.get("unresolved_dependency_count") != 0
        or resolution.get("root_requirement_count") != len(root_names)
        or resolution.get("reachable_distribution_count") != len(names)
    ):
        return ("DEPENDENCY_LOCK_INVALID",)
    marker_environment = resolution.get("marker_environment")
    activated_extras = resolution.get("activated_extras")
    if (
        type(marker_environment) is not dict
        or any(
            not isinstance(key, str)
            or not isinstance(value, str)
            for key, value in marker_environment.items()
        )
        or type(activated_extras) is not dict
        or any(
            name not in names
            or type(extras) is not list
            or extras != sorted(set(extras))
            or any(not isinstance(extra, str) or not extra for extra in extras)
            for name, extras in activated_extras.items()
        )
    ):
        return ("DEPENDENCY_LOCK_INVALID",)
    for name, requirements in parsed_requirements.items():
        expected_dependencies: set[str] = set()
        extras = activated_extras.get(name, [])
        marker_environments = [
            {**marker_environment, "extra": extra}
            for extra in ["", *extras]
        ]
        for requirement in requirements:
            if requirement.url is not None:
                return ("DEPENDENCY_LOCK_INVALID",)
            if (
                requirement.marker is not None
                and not any(
                    requirement.marker.evaluate(environment)
                    for environment in marker_environments
                )
            ):
                continue
            dependency = _normalize_distribution_name(requirement.name)
            dependency_version = versions.get(dependency)
            if (
                dependency_version is None
                or not requirement.specifier.contains(
                    dependency_version,
                    prereleases=True,
                )
            ):
                return ("DEPENDENCY_LOCK_INVALID",)
            expected_dependencies.add(dependency)
        if dependency_graph[name] != sorted(expected_dependencies):
            return ("DEPENDENCY_LOCK_INVALID",)
    target = lock.get("target")
    if (
        type(target) is not dict
        or target.get("wheel_only") is not True
        or target.get("implementation") != "CPYTHON"
        or not isinstance(target.get("python_version"), str)
        or not target.get("python_version")
    ):
        return ("DEPENDENCY_LOCK_INVALID",)
    mapping = lock.get("module_distribution_map")
    if (
        type(mapping) is not dict
        or any(
            not isinstance(key, str)
            or not key
            or not isinstance(value, str)
            or value not in names
            for key, value in mapping.items()
        )
        or any(import_name not in mapping for import_name in root_imports)
    ):
        return ("DEPENDENCY_LOCK_INVALID",)
    namespace_mapping = resolution.get(
        "namespace_module_distribution_map",
        {},
    )
    if type(namespace_mapping) is not dict or any(
        not isinstance(module, str)
        or type(owners) is not list
        or any(not isinstance(owner, str) for owner in owners)
        or any(owner not in names for owner in owners)
        or owners != sorted(set(owners))
        for module, owners in namespace_mapping.items()
    ):
        return ("DEPENDENCY_LOCK_INVALID",)

    if installed_directory is not None:
        installed = _installed_distribution_closure(
            installed_directory,
            runtime_root=runtime_root,
        )
        if installed is None or set(installed) != names:
            return ("DEPENDENCY_LOCK_INSTALLED_CLOSURE_MISMATCH",)
        for row in rows:
            name = row["normalized_distribution_name"]
            version, closure_hash = installed[name]
            if (
                version != row["distribution_version"]
                or closure_hash
                != row["installed_record_closure_sha256"]
            ):
                return ("DEPENDENCY_LOCK_INSTALLED_CLOSURE_MISMATCH",)
    if (
        lock.get("lock_sha256")
        != _hash_without(lock, "lock_sha256")
    ):
        return ("DEPENDENCY_LOCK_INVALID",)
    return ()


def load_recovery_epoch002_dependency_lock_with_raw_sha256(
    path: Path,
) -> tuple[dict[str, Any], str]:
    """Load and hash a lock through one no-follow file descriptor."""

    def reject_duplicates(
        pairs: list[tuple[str, Any]],
    ) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in pairs:
            if key in result:
                raise ValueError("duplicate JSON key")
            result[key] = value
        return result

    flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0)
    try:
        descriptor = os.open(path, flags)
    except OSError as exc:
        raise ValueError(
            "dependency lock must be a regular non-symlink file"
        ) from exc
    try:
        file_stat = os.fstat(descriptor)
        if not stat.S_ISREG(file_stat.st_mode):
            raise ValueError("dependency lock must be a regular file")
        chunks: list[bytes] = []
        total = 0
        while True:
            chunk = os.read(descriptor, 1024 * 1024)
            if not chunk:
                break
            total += len(chunk)
            if total > 16 * 1024 * 1024:
                raise ValueError("dependency lock is too large")
            chunks.append(chunk)
    finally:
        os.close(descriptor)
    payload = b"".join(chunks)
    try:
        value = json.loads(
            payload.decode("utf-8"),
            object_pairs_hook=reject_duplicates,
            parse_constant=lambda value: (_ for _ in ()).throw(
                ValueError(f"non-finite JSON number: {value}")
            ),
        )
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise ValueError("dependency lock must be canonical JSON") from exc
    if type(value) is not dict:
        raise ValueError("dependency lock root must be an object")
    issues = validate_recovery_epoch002_dependency_lock(value)
    if issues:
        raise ValueError(issues[0])
    return value, hashlib.sha256(payload).hexdigest()


def load_recovery_epoch002_dependency_lock(
    path: Path,
) -> dict[str, Any]:
    """Load a lock through one no-follow file descriptor."""

    return load_recovery_epoch002_dependency_lock_with_raw_sha256(path)[0]


def materialize_recovery_epoch002_locked_runtime(
    *,
    lock_path: Path,
    wheel_directory: Path,
    runtime_root: Path,
) -> dict[str, Any]:
    """Create a fresh locked venv without importing or running formal tests."""

    lock, lock_raw_sha256 = (
        load_recovery_epoch002_dependency_lock_with_raw_sha256(lock_path)
    )
    issues = validate_recovery_epoch002_dependency_lock(
        lock,
        wheel_directory=wheel_directory,
    )
    if issues:
        raise ValueError(issues[0])
    if (
        wheel_directory.is_symlink()
        or not wheel_directory.is_dir()
        or runtime_root.exists()
        or runtime_root.is_symlink()
    ):
        raise ValueError("RUNTIME_MATERIALIZATION_TARGET_INVALID")

    subprocess.run(
        [
            sys.executable,
            "-I",
            "-B",
            "-m",
            "venv",
            "--without-pip",
            "--copies",
            str(runtime_root),
        ],
        check=True,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        timeout=120,
    )
    python_relative = (
        Path("Scripts/python.exe")
        if os.name == "nt"
        else Path("bin/python")
    )
    python_executable = runtime_root / python_relative
    requirements_path = runtime_root / "locked-requirements.txt"
    requirements_payload = (
        "\n".join(lock["pip_require_hashes_lines"]) + "\n"
    ).encode("utf-8")
    descriptor = os.open(
        requirements_path,
        os.O_WRONLY | os.O_CREAT | os.O_EXCL
        | getattr(os, "O_NOFOLLOW", 0),
        0o600,
    )
    try:
        os.write(descriptor, requirements_payload)
        os.fsync(descriptor)
    finally:
        os.close(descriptor)

    subprocess.run(
        [
            sys.executable,
            "-I",
            "-B",
            "-m",
            "pip",
            "--python",
            str(python_executable),
            "install",
            "--require-hashes",
            "--no-index",
            "--only-binary=:all:",
            "--no-compile",
            f"--find-links={wheel_directory}",
            "--requirement",
            str(requirements_path),
        ],
        check=True,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        timeout=600,
    )
    site_output = subprocess.run(
        [
            str(python_executable),
            "-I",
            "-B",
            "-c",
            (
                "import json,sysconfig;"
                "print(json.dumps(sysconfig.get_path('purelib')))"
            ),
        ],
        check=True,
        capture_output=True,
        text=True,
        timeout=30,
    ).stdout
    installed_directory = Path(json.loads(site_output)).absolute()
    runtime_absolute = runtime_root.absolute()
    try:
        installed_relative = installed_directory.relative_to(
            runtime_absolute
        )
    except ValueError as exc:
        raise ValueError(
            "RUNTIME_MATERIALIZATION_TARGET_INVALID"
        ) from exc
    issues = validate_recovery_epoch002_dependency_lock(
        lock,
        wheel_directory=wheel_directory,
        installed_directory=installed_directory,
        runtime_root=runtime_absolute,
    )
    if issues:
        raise ValueError(issues[0])

    wheel_manifest = [
        {
            "wheel_filename": row["wheel_filename"],
            "wheel_sha256": row["wheel_sha256"],
            "wheel_record_sha256": row["wheel_record_sha256"],
        }
        for row in lock["distributions"]
    ]
    result: dict[str, Any] = {
        "schema_version": (
            "cocolon.emlis.nls_v3.recovery_epoch002."
            "locked_runtime_materialization.v1"
        ),
        "runtime_root_identity_sha256": artifact_sha256(
            {"runtime_root": str(runtime_absolute)}
        ),
        "python_executable_relative_path": python_relative.as_posix(),
        "installed_directory_relative_path": installed_relative.as_posix(),
        "dependency_lock_raw_sha256": lock_raw_sha256,
        "wheel_bundle_manifest_sha256": artifact_sha256(wheel_manifest),
        "distribution_count": lock["distribution_count"],
        "runtime_materialization_state": "VERIFIED_LOCKED_RUNTIME",
        "body_free": True,
        "runtime_materialization_sha256": "",
    }
    result["runtime_materialization_sha256"] = _hash_without(
        result,
        "runtime_materialization_sha256",
    )
    return result


def validate_recovery_epoch002_operational_bootstrap_state(
    state: Mapping[str, Any],
    *,
    event1_artifact: Mapping[str, Any],
    event1_external_identity: Mapping[str, Any],
    event1_publication_state: Mapping[str, Any],
    repository_root: Path,
    dependency_lock_path: Path,
    wheel_directory: Path,
    locked_runtime_root: Path,
    attempt_registry_root: Path,
) -> tuple[str, ...]:
    """Execute the read-only, pre-reservation operational reconciliation."""

    if validate_recovery_epoch002_bootstrap_state(state):
        return ("READINESS_FORBIDDEN",)
    manifest = state.get("bootstrap_manifest")
    readiness = state.get("readiness_receipt")
    source_closure = (
        readiness.get("source_closure")
        if type(readiness) is dict
        else None
    )
    if (
        type(manifest) is not dict
        or type(readiness) is not dict
        or validate_recovery_epoch002_operational_readiness_bindings(
            readiness,
            manifest,
            expected_receipt_path=state.get("readiness_target_path"),
        )
        or validate_recovery_epoch002_event1_publication_binding(
            event1_artifact=event1_artifact,
            event1_external_identity=event1_external_identity,
            event1_publication_state=event1_publication_state,
            readiness=readiness,
        )
        or state.get("readiness_target_path_preexisted") is not False
    ):
        return ("READINESS_FORBIDDEN",)
    root = repository_root.absolute()
    lock_path = dependency_lock_path.absolute()
    runtime_root = locked_runtime_root.absolute()
    registry_root = attempt_registry_root.absolute()
    try:
        root_stat = root.lstat()
        runtime_stat = runtime_root.lstat()
        registry_stat = registry_root.lstat()
        wheel_stat = wheel_directory.lstat()
    except OSError:
        return ("READINESS_FORBIDDEN",)
    if (
        repository_root.is_symlink()
        or locked_runtime_root.is_symlink()
        or attempt_registry_root.is_symlink()
        or wheel_directory.is_symlink()
        or any(
            not stat.S_ISDIR(item.st_mode)
            for item in (
                root_stat,
                runtime_stat,
                registry_stat,
                wheel_stat,
            )
        )
        or stat.S_IMODE(registry_stat.st_mode) != 0o700
        or registry_stat.st_uid != os.getuid()
    ):
        return ("READINESS_FORBIDDEN",)

    lock_identity = manifest.get("dependency_lock_identity")
    try:
        lock_relative = lock_path.relative_to(root).as_posix()
        lock, lock_raw_sha256 = (
            load_recovery_epoch002_dependency_lock_with_raw_sha256(
                lock_path
            )
        )
    except (OSError, ValueError):
        return ("READINESS_FORBIDDEN",)
    if (
        type(lock_identity) is not dict
        or lock_relative != lock_identity.get("path")
        or lock_raw_sha256 != lock_identity.get("raw_sha256")
        or validate_recovery_epoch002_dependency_lock(
            lock,
            wheel_directory=wheel_directory,
        )
        or validate_recovery_epoch002_operational_bootstrap_manifest(
            manifest,
            lock,
        )
        or validate_recovery_epoch002_formal_node_registry(
            root,
            manifest,
            source_closure,
        )
    ):
        return ("READINESS_FORBIDDEN",)

    environment_profile = manifest.get("environment_profile")
    materialization = (
        environment_profile.get("locked_runtime_materialization")
        if type(environment_profile) is dict
        else None
    )
    if (
        type(materialization) is not dict
        or set(materialization)
        != RECOVERY_EPOCH002_RUNTIME_MATERIALIZATION_KEYS
        or materialization.get("runtime_materialization_state")
        != "VERIFIED_LOCKED_RUNTIME"
        or materialization.get("body_free") is not True
        or materialization.get("runtime_materialization_sha256")
        != _hash_without(
            materialization,
            "runtime_materialization_sha256",
        )
        or materialization.get("runtime_root_identity_sha256")
        != artifact_sha256({"runtime_root": str(runtime_root)})
        or materialization.get("dependency_lock_raw_sha256")
        != lock_raw_sha256
        or materialization.get("distribution_count")
        != lock.get("distribution_count")
        or environment_profile.get(
            "attempt_registry_root_identity_sha256"
        )
        != artifact_sha256({"attempt_registry_root": str(registry_root)})
    ):
        return ("READINESS_FORBIDDEN",)

    def runtime_child(relative_text: Any) -> Path | None:
        if not isinstance(relative_text, str) or not relative_text:
            return None
        relative = Path(relative_text)
        if (
            relative.is_absolute()
            or relative.as_posix() != relative_text
            or any(part in {"", ".", ".."} for part in relative.parts)
        ):
            return None
        target = (runtime_root / relative).absolute()
        try:
            target.relative_to(runtime_root)
        except ValueError:
            return None
        current = runtime_root
        for component in relative.parts:
            current = current / component
            try:
                current_stat = current.lstat()
            except OSError:
                return None
            if stat.S_ISLNK(current_stat.st_mode):
                return None
        return target

    python_executable = runtime_child(
        materialization.get("python_executable_relative_path")
    )
    installed_directory = runtime_child(
        materialization.get("installed_directory_relative_path")
    )
    if (
        python_executable is None
        or installed_directory is None
        or not python_executable.is_file()
        or not installed_directory.is_dir()
        or validate_recovery_epoch002_dependency_lock(
            lock,
            wheel_directory=wheel_directory,
            installed_directory=installed_directory,
            runtime_root=runtime_root,
        )
    ):
        return ("READINESS_FORBIDDEN",)

    probe = (
        "import json,platform,sys;"
        "print(json.dumps({"
        "'python_build':list(platform.python_build()),"
        "'python_compiler':platform.python_compiler(),"
        "'platform':platform.platform(),"
        "'abi_flags':sys.abiflags,"
        "'implementation':platform.python_implementation().upper(),"
        "'version':platform.python_version(),"
        "'stdlib_module_names':sorted(sys.stdlib_module_names)"
        "},sort_keys=True))"
    )
    try:
        observed = json.loads(
            subprocess.run(
                [str(python_executable), "-I", "-B", "-c", probe],
                check=True,
                capture_output=True,
                text=True,
                timeout=30,
            ).stdout
        )
        executable_sha256 = hashlib.sha256(
            python_executable.read_bytes()
        ).hexdigest()
    except (
        OSError,
        subprocess.SubprocessError,
        json.JSONDecodeError,
        KeyError,
    ):
        return ("READINESS_FORBIDDEN",)
    stdlib_values = observed.get("stdlib_module_names")
    if (
        type(stdlib_values) is not list
        or stdlib_values != sorted(set(stdlib_values))
        or any(
            not isinstance(value, str) or not value
            for value in stdlib_values
        )
    ):
        return ("READINESS_FORBIDDEN",)
    runtime_identity = {
        "executable_sha256": executable_sha256,
        "implementation": observed["implementation"],
        "version": observed["version"],
        "build_sha256": artifact_sha256(
            {
                "python_build": observed["python_build"],
                "python_compiler": observed["python_compiler"],
                "platform": observed["platform"],
                "abi_flags": observed["abi_flags"],
            }
        ),
    }
    pytest_row = next(
        (
            row
            for row in lock["distributions"]
            if row["normalized_distribution_name"] == "pytest"
        ),
        None,
    )
    pytest_identity = (
        None
        if pytest_row is None
        else {
            "normalized_distribution_name": "pytest",
            "distribution_version": pytest_row["distribution_version"],
            "wheel_sha256": pytest_row["wheel_sha256"],
            "installed_record_closure_sha256": pytest_row[
                "installed_record_closure_sha256"
            ],
        }
    )
    if (
        runtime_identity != manifest.get("python_runtime_identity")
        or pytest_identity != manifest.get("pytest_distribution_identity")
        or validate_recovery_epoch002_operational_source_manifest(
            root,
            manifest,
            lock,
            frozenset(stdlib_values),
        )
    ):
        return ("READINESS_FORBIDDEN",)

    def git(*args: str) -> str:
        return subprocess.run(
            ["git", *args],
            cwd=root,
            check=True,
            capture_output=True,
            text=True,
            timeout=10,
        ).stdout.strip()

    try:
        commit = git("rev-parse", "HEAD")
        tree = git("rev-parse", "HEAD^{tree}")
        clean = git("status", "--porcelain", "--untracked-files=all") == ""
    except (OSError, subprocess.SubprocessError):
        return ("READINESS_FORBIDDEN",)
    if (
        clean is not True
        or commit != source_closure.get("source_commit_sha1")
        or tree != source_closure.get("source_tree_sha1")
        or commit != manifest.get("source_commit_sha1")
        or tree != manifest.get("source_tree_sha1")
    ):
        return ("READINESS_FORBIDDEN",)

    if (
        state.get("formal_exact134_invocation_count") != 0
        or state.get("reservation_count_delta") != 0
    ):
        return ("READINESS_FORBIDDEN",)
    return ()


def build_recovery_epoch002_operational_preflight_attestation(
    state: Mapping[str, Any],
    *,
    event1_artifact: Mapping[str, Any],
    event1_external_identity: Mapping[str, Any],
    event1_publication_state: Mapping[str, Any],
    repository_root: Path,
    dependency_lock_path: Path,
    wheel_directory: Path,
    locked_runtime_root: Path,
    attempt_registry_root: Path,
) -> dict[str, Any]:
    """Run the full gate and attest only a genuinely valid observation."""

    issues = validate_recovery_epoch002_operational_bootstrap_state(
        state,
        event1_artifact=event1_artifact,
        event1_external_identity=event1_external_identity,
        event1_publication_state=event1_publication_state,
        repository_root=repository_root,
        dependency_lock_path=dependency_lock_path,
        wheel_directory=wheel_directory,
        locked_runtime_root=locked_runtime_root,
        attempt_registry_root=attempt_registry_root,
    )
    if issues:
        raise ValueError(issues[0])
    readiness = state["readiness_receipt"]
    manifest = state["bootstrap_manifest"]
    source_closure = readiness["source_closure"]
    materialization = manifest["environment_profile"][
        "locked_runtime_materialization"
    ]
    attestation: dict[str, Any] = {
        "schema_version": (
            "cocolon.emlis.nls_v3.recovery_epoch002."
            "operational_bootstrap_preflight_attestation.v1"
        ),
        "logical_cycle_id": readiness["logical_cycle_id"],
        "recovery_epoch_id": readiness["recovery_epoch_id"],
        "candidate_version_id": readiness["candidate_version_id"],
        "preflight_id": readiness["preflight_id"],
        "source_baseline_event_identity_sha256": (
            event1_external_identity["identity_sha256"]
        ),
        "source_commit_sha1": source_closure["source_commit_sha1"],
        "source_tree_sha1": source_closure["source_tree_sha1"],
        "bootstrap_closure_sha256": manifest[
            "bootstrap_closure_sha256"
        ],
        "dependency_lock_raw_sha256": manifest[
            "dependency_lock_identity"
        ]["raw_sha256"],
        "runtime_materialization_sha256": materialization[
            "runtime_materialization_sha256"
        ],
        "bootstrap_readiness_receipt_sha256": readiness[
            "bootstrap_readiness_receipt_sha256"
        ],
        "readiness_receipt_path": readiness["readiness_receipt_path"],
        "operational_issue_codes": [],
        "formal_exact134_invocation_count": 0,
        "reservation_count_delta": 0,
        "owner_validation_state": "VALID",
        "independent_verification_state": "VALID",
        "body_free": True,
        "operational_preflight_attestation_sha256": "",
    }
    attestation[
        "operational_preflight_attestation_sha256"
    ] = _hash_without(
        attestation,
        "operational_preflight_attestation_sha256",
    )
    return attestation


def validate_recovery_epoch002_operational_preflight_attestation(
    attestation: Mapping[str, Any],
    *,
    readiness: Mapping[str, Any],
    event1_external_identity: Mapping[str, Any],
) -> tuple[str, ...]:
    """Validate the full-gate attestation before readiness publication."""

    manifest = (
        readiness.get("bootstrap_closure")
        if type(readiness) is dict
        else None
    )
    source_closure = (
        readiness.get("source_closure")
        if type(readiness) is dict
        else None
    )
    materialization = (
        manifest.get("environment_profile", {}).get(
            "locked_runtime_materialization"
        )
        if type(manifest) is dict
        else None
    )
    if (
        type(attestation) is not dict
        or set(attestation)
        != RECOVERY_EPOCH002_OPERATIONAL_PREFLIGHT_ATTESTATION_KEYS
        or attestation.get("schema_version")
        != (
            "cocolon.emlis.nls_v3.recovery_epoch002."
            "operational_bootstrap_preflight_attestation.v1"
        )
        or type(source_closure) is not dict
        or type(materialization) is not dict
        or attestation.get("logical_cycle_id")
        != readiness.get("logical_cycle_id")
        or attestation.get("recovery_epoch_id")
        != readiness.get("recovery_epoch_id")
        or attestation.get("candidate_version_id")
        != readiness.get("candidate_version_id")
        or attestation.get("preflight_id")
        != readiness.get("preflight_id")
        or attestation.get("source_baseline_event_identity_sha256")
        != event1_external_identity.get("identity_sha256")
        or attestation.get("source_commit_sha1")
        != source_closure.get("source_commit_sha1")
        or attestation.get("source_tree_sha1")
        != source_closure.get("source_tree_sha1")
        or attestation.get("bootstrap_closure_sha256")
        != manifest.get("bootstrap_closure_sha256")
        or attestation.get("dependency_lock_raw_sha256")
        != manifest.get("dependency_lock_identity", {}).get("raw_sha256")
        or attestation.get("runtime_materialization_sha256")
        != materialization.get("runtime_materialization_sha256")
        or attestation.get("bootstrap_readiness_receipt_sha256")
        != readiness.get("bootstrap_readiness_receipt_sha256")
        or attestation.get("readiness_receipt_path")
        != readiness.get("readiness_receipt_path")
        or attestation.get("operational_issue_codes") != []
        or attestation.get("formal_exact134_invocation_count") != 0
        or attestation.get("reservation_count_delta") != 0
        or attestation.get("owner_validation_state") != "VALID"
        or attestation.get("independent_verification_state") != "VALID"
        or attestation.get("body_free") is not True
        or attestation.get("operational_preflight_attestation_sha256")
        != _hash_without(
            attestation,
            "operational_preflight_attestation_sha256",
        )
    ):
        return ("READINESS_FORBIDDEN",)
    return ()


_PREFLIGHT_CLI_REQUEST_KEYS = frozenset(
    {
        "state",
        "event1_artifact",
        "event1_external_identity",
        "event1_publication_state",
        "repository_root",
        "dependency_lock_path",
        "wheel_directory",
        "locked_runtime_root",
        "attempt_registry_root",
    }
)


def _read_preflight_cli_request() -> dict[str, Any]:
    payload = sys.stdin.buffer.read(32 * 1024 * 1024 + 1)
    if len(payload) > 32 * 1024 * 1024:
        raise ValueError("PREFLIGHT_REQUEST_TOO_LARGE")

    def reject_duplicates(
        pairs: list[tuple[str, Any]],
    ) -> dict[str, Any]:
        value: dict[str, Any] = {}
        for key, item in pairs:
            if key in value:
                raise ValueError("PREFLIGHT_REQUEST_DUPLICATE_KEY")
            value[key] = item
        return value

    value = json.loads(
        payload.decode("utf-8"),
        object_pairs_hook=reject_duplicates,
        parse_constant=lambda item: (_ for _ in ()).throw(
            ValueError(f"PREFLIGHT_REQUEST_NONFINITE_NUMBER:{item}")
        ),
    )
    if type(value) is not dict or set(value) != _PREFLIGHT_CLI_REQUEST_KEYS:
        raise ValueError("PREFLIGHT_REQUEST_INVALID")
    return value


def _preflight_cli_result(
    *,
    issues: tuple[str, ...],
    readiness: Any,
    attestation: Mapping[str, Any] | None,
) -> dict[str, Any]:
    result: dict[str, Any] = {
        "schema_version": (
            "cocolon.emlis.nls_v3.recovery_epoch002."
            "bootstrap_preflight_result.v1"
        ),
        "preflight_state": "VALID" if not issues else "REJECTED",
        "issue_codes": list(issues),
        "bootstrap_readiness_receipt_sha256": (
            readiness.get("bootstrap_readiness_receipt_sha256")
            if type(readiness) is dict and not issues
            else None
        ),
        "operational_preflight_attestation": (
            deepcopy(dict(attestation))
            if type(attestation) is dict and not issues
            else None
        ),
        "formal_exact134_invocation_count": 0,
        "reservation_count_delta": 0,
        "body_free": True,
        "preflight_result_sha256": "",
    }
    result["preflight_result_sha256"] = _hash_without(
        result,
        "preflight_result_sha256",
    )
    return result


RECOVERY_EPOCH003_REFERENCE_OBSERVATION_SCHEMA = (
    "cocolon.emlis.nls_v3.recovery_epoch003."
    "reference_runtime_observation.v1"
)
RECOVERY_EPOCH003_OPERATIONAL_OBSERVATION_SCHEMA = (
    "cocolon.emlis.nls_v3.recovery_epoch003."
    "operational_runtime_observation.v1"
)
RECOVERY_EPOCH003_READINESS_SCHEMA = (
    "cocolon.emlis.nls_v3.recovery_epoch003."
    "bootstrap_readiness_receipt.v1"
)
RECOVERY_EPOCH003_FAILURE_SCHEMA = (
    "cocolon.emlis.nls_v3.recovery_epoch003."
    "formal_worker_bootstrap_preflight_failure_receipt.v1"
)
RECOVERY_EPOCH003_FAILURE_CLASSES = (
    "BOOTSTRAP_SCHEMA_PAIR_UNSUPPORTED",
    "SOURCE_BOOTSTRAP_BASELINE_MISMATCH",
    "OPERATIONAL_RUNTIME_IDENTITY_MISMATCH",
    "OPERATIONAL_MATERIALIZATION_BINDING_MISSING",
    "INDEPENDENT_OPERATIONAL_PROJECTION_DISAGREEMENT",
)
RECOVERY_EPOCH003_PREFLIGHT_STOP_CODE = (
    "PRE_RESERVATION_FORMAL_WORKER_BOOTSTRAP_STOP"
)
_RECOVERY_EPOCH003_SOURCE_SCHEMA = (
    "cocolon.emlis.nls_v3.recovery_epoch003."
    "source_baseline_eligibility_closure.v1"
)
_RECOVERY_EPOCH003_BOOTSTRAP_SCHEMA = (
    "cocolon.emlis.nls_v3.recovery_epoch003."
    "formal_worker_bootstrap_manifest.v1"
)
_RECOVERY_EPOCH003_KNOWN_SCHEMA_PAIRS = (
    (
        "cocolon.emlis.nls_v3.recovery_epoch002."
        "post_d2_source_baseline_eligibility_successor_closure.v1",
        "cocolon.emlis.nls_v3.recovery_epoch002."
        "formal_worker_bootstrap_manifest.v2",
    ),
    (
        _RECOVERY_EPOCH003_SOURCE_SCHEMA,
        _RECOVERY_EPOCH003_BOOTSTRAP_SCHEMA,
    ),
)
_RECOVERY_EPOCH003_SOURCE_KEYS = _keys(
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
_RECOVERY_EPOCH003_BOOTSTRAP_KEYS = _keys(
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
_RECOVERY_EPOCH003_OPERATIONAL_KEYS = _keys(
    """
    schema_version logical_cycle_id recovery_epoch_id candidate_version_id
    authority_token preflight_challenge_id preflight_id
    source_baseline_event_external_identity_sha256 source_closure_sha256
    bootstrap_closure_sha256 source_commit_sha1 source_tree_sha1
    worktree_clean formal_owner_artifacts_sha256
    formal_test_manifest_sha256 import_manifest_sha256
    dependency_lock_raw_sha256 wheel_bundle_manifest_sha256
    installed_distributions_sha256 pytest_distribution_identity
    python_runtime_identity loaded_plugin_manifest_sha256
    preflight_argv_sha256 formal_worker_argv_sha256 environment_policy
    environment_policy_sha256 runtime_materialization
    runtime_root_identity_sha256 reference_runtime_root_identity_sha256
    attempt_registry_root_identity_sha256
    owner_operational_projection_sha256
    independent_operational_projection_sha256 owner_validation_state
    independent_verification_state reservation_count_delta
    formal_exact134_invocation_count collection_state test_execution_state
    pytest_main_called body_free operational_runtime_observation_sha256
    """
)
_RECOVERY_EPOCH003_PROJECTION_KEYS = _keys(
    """
    source_commit_sha1 source_tree_sha1 formal_owner_artifacts_sha256
    formal_test_manifest_sha256 import_manifest_sha256
    dependency_lock_raw_sha256 wheel_bundle_manifest_sha256
    installed_distributions_sha256 pytest_distribution_identity
    python_runtime_identity loaded_plugin_manifest_sha256
    preflight_argv_sha256 formal_worker_argv_sha256
    environment_policy_sha256
    """
)
_RECOVERY_EPOCH003_READINESS_KEYS = _keys(
    """
    schema_version logical_cycle_id recovery_epoch_id candidate_version_id
    authority_token event1_external_identity_sha256
    event1_bootstrap_closure event1_bootstrap_closure_sha256
    operational_runtime_observation_external_identity
    operational_runtime_observation_sha256
    expected_observed_projection_sha256 readiness_receipt_path
    preflight_started_at_utc preflight_finished_at_utc
    owner_validation_state independent_verification_state
    reservation_count_delta formal_exact134_invocation_count
    collection_state test_execution_state pytest_main_called
    automatic_progression body_free bootstrap_readiness_receipt_sha256
    """
)
_RECOVERY_EPOCH003_FAILURE_KEYS = _keys(
    """
    schema_version logical_cycle_id recovery_epoch_id candidate_version_id
    authority_token preflight_challenge_id preflight_id
    event1_external_identity_sha256 source_closure_sha256
    bootstrap_closure_sha256 operational_runtime_observation_state
    operational_runtime_observation_external_identity
    operational_runtime_observation_sha256
    owner_operational_projection_sha256
    independent_operational_projection_sha256
    expected_observed_projection_sha256 failure_stage failure_class
    failure_issue_codes stop_code reservation_count_delta attempt_id
    formal_exact134_invocation_count owner_validation_state
    independent_verification_state automatic_retry automatic_progression
    body_free receipt_sha256
    """
)
_RECOVERY_EPOCH003_EXTERNAL_IDENTITY_KEYS = _keys(
    """
    artifact_role body_free git_blob_sha1 identity_sha256
    logical_artifact_sha256 path publication_commit_sha1 raw_sha256
    repository_full_name schema_version
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
_RECOVERY_EPOCH003_ENVIRONMENT_KEYS = _keys(
    "fixed removed inherited_path_sha256 lang lc_all"
)
_RECOVERY_EPOCH003_ENVIRONMENT_FIXED_KEYS = _keys(
    "PYTEST_DISABLE_PLUGIN_AUTOLOAD PYTHONDONTWRITEBYTECODE"
)
_RECOVERY_EPOCH003_REFERENCE_PATH = (
    "EmlisAIの実装済み資料/documents/"
    "NLSv3_Step11_Cycle001_RecoveryEpoch003_"
    "PreEvent1_ReferenceRuntimeObservation_BodyFree_Receipt.json"
)
_RECOVERY_EPOCH003_EVENT1_PATH = (
    "EmlisAIの実装済み資料/documents/"
    "NLSv3_Step11_Cycle001_RecoveryEpoch003_"
    "SequenceEvent01_SourceBaselineLocked_BodyFree_Event.json"
)
_RECOVERY_EPOCH003_OPERATIONAL_PATH = (
    "EmlisAIの実装済み資料/documents/"
    "NLSv3_Step11_Cycle001_RecoveryEpoch003_"
    "PostEvent1_OperationalRuntimeObservation_BodyFree_Receipt.json"
)
_RECOVERY_EPOCH003_READINESS_PATH = (
    "EmlisAIの実装済み資料/documents/"
    "NLSv3_Step11_Cycle001_RecoveryEpoch003_"
    "PostEvent1_BootstrapReadiness_BodyFree_Receipt.json"
)
_RECOVERY_EPOCH003_EVENT_SCHEMA = (
    "cocolon.emlis.nls_v3.recovery_epoch003.sequence_event.v1"
)
_RECOVERY_EPOCH003_SHA1_RE = re.compile(r"^[0-9a-f]{40}$")
_RECOVERY_EPOCH003_UTC_RE = re.compile(
    r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z$"
)
_RECOVERY_EPOCH003_FINAL_ISSUANCE_AUTHORITY = (
    "NLS_V3_STEP11_CYCLE001_RECOVERY_EPOCH003_FINAL_PRE_EVENT1_REFERENCE_"
    "RUNTIME_OBSERVATION_AND_SOURCE_BOOTSTRAP_OPERATIONAL_ADMISSION_"
    "CARRIER_ISSUANCE_INDEPENDENT_VERIFICATION_AND_POSTVERIFICATION_ONLY"
)
_RECOVERY_EPOCH003_MATERIALIZATION_REQUEST_KEYS = _keys(
    """
    authority_token artifact_repository_root source_repository_root
    expected_source_commit_sha1 expected_source_tree_sha1
    dependency_lock_path wheelhouse_path destination_root environment
    """
)
_RECOVERY_EPOCH003_MATERIALIZATION_RESULT_KEYS = _keys(
    """
    runtime_root wheel_snapshot_root runtime_materialization
    effective_environment_policy
    """
)
_RECOVERY_EPOCH003_REFERENCE_BUILD_KEYS = _keys(
    "materialization_request materialization_result"
)
_RECOVERY_EPOCH003_ROOT_IDENTITY_PREIMAGE_KEYS = _keys(
    """
    schema_version materialization_kind root_nonce_sha256
    source_commit_sha1 source_tree_sha1 dependency_lock_raw_sha256
    wheel_bundle_manifest_sha256 installed_distributions_sha256
    python_runtime_identity_sha256 pytest_distribution_identity_sha256
    environment_policy_sha256
    """
)
_RECOVERY_EPOCH003_LOCK_PATH = (
    "ai/configs/"
    "emlis_nls_v3_recovery_epoch002_formal_worker_bootstrap_lock_v1.json"
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
_RECOVERY_EPOCH003_ROOT_NONCE_FILE = ".cocolon-root-nonce"


def _recovery_epoch003_external_identity_valid(
    value: Any,
    *,
    roles: frozenset[str],
    schema: str,
    path: str,
    logical_hash: str,
) -> bool:
    return bool(
        type(value) is dict
        and set(value) == _RECOVERY_EPOCH003_EXTERNAL_IDENTITY_KEYS
        and value.get("artifact_role") in roles
        and value.get("schema_version") == schema
        and value.get("path") == path
        and value.get("repository_full_name") == "MassyuRed/Cocolon"
        and value.get("body_free") is True
        and _RECOVERY_EPOCH003_SHA1_RE.fullmatch(
            str(value.get("git_blob_sha1", ""))
        )
        is not None
        and _RECOVERY_EPOCH003_SHA1_RE.fullmatch(
            str(value.get("publication_commit_sha1", ""))
        )
        is not None
        and _SHA256_RE.fullmatch(str(value.get("raw_sha256", "")))
        is not None
        and _SHA256_RE.fullmatch(str(logical_hash)) is not None
        and value.get("logical_artifact_sha256") == logical_hash
        and value.get("identity_sha256")
        == _hash_without(value, "identity_sha256")
    )


def _recovery_epoch003_runtime_identity_valid(value: Any) -> bool:
    return bool(
        type(value) is dict
        and set(value) == _RECOVERY_EPOCH003_RUNTIME_IDENTITY_KEYS
        and isinstance(value.get("implementation"), str)
        and bool(value.get("implementation"))
        and isinstance(value.get("version"), str)
        and bool(value.get("version"))
        and _SHA256_RE.fullmatch(
            str(value.get("executable_sha256", ""))
        )
        is not None
        and _SHA256_RE.fullmatch(str(value.get("build_sha256", "")))
        is not None
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
        and _SHA256_RE.fullmatch(str(value.get("wheel_sha256", "")))
        is not None
        and _SHA256_RE.fullmatch(
            str(value.get("installed_record_closure_sha256", ""))
        )
        is not None
    )


def _recovery_epoch003_environment_valid(value: Any) -> bool:
    return bool(
        type(value) is dict
        and set(value) == _RECOVERY_EPOCH003_ENVIRONMENT_KEYS
        and type(value.get("fixed")) is dict
        and set(value["fixed"])
        == _RECOVERY_EPOCH003_ENVIRONMENT_FIXED_KEYS
        and value["fixed"].get("PYTEST_DISABLE_PLUGIN_AUTOLOAD") == "1"
        and value["fixed"].get("PYTHONDONTWRITEBYTECODE") == "1"
        and value.get("removed")
        == ["PYTEST_ADDOPTS", "PYTEST_PLUGINS", "PYTHONPATH"]
        and _SHA256_RE.fullmatch(
            str(value.get("inherited_path_sha256", ""))
        )
        is not None
        and value.get("inherited_path_sha256") != "0" * 64
        and isinstance(value.get("lang"), str)
        and bool(value.get("lang"))
        and isinstance(value.get("lc_all"), str)
        and bool(value.get("lc_all"))
    )


def _recovery_epoch003_materialization_valid(
    value: Any,
    *,
    dependency_lock_raw_sha256: str,
    wheel_bundle_manifest_sha256: str,
    distribution_count: int,
) -> bool:
    if (
        type(value) is not dict
        or set(value)
        != _RECOVERY_EPOCH003_RUNTIME_MATERIALIZATION_KEYS
        or value.get("schema_version")
        != (
            "cocolon.emlis.nls_v3.recovery_epoch003."
            "runtime_materialization.v1"
        )
        or _SHA256_RE.fullmatch(
            str(value.get("runtime_root_identity_sha256", ""))
        )
        is None
        or value.get("dependency_lock_raw_sha256")
        != dependency_lock_raw_sha256
        or value.get("wheel_bundle_manifest_sha256")
        != wheel_bundle_manifest_sha256
        or value.get("distribution_count") != distribution_count
        or not isinstance(value.get("runtime_materialization_state"), str)
        or not value.get("runtime_materialization_state")
        or value.get("body_free") is not True
        or value.get("runtime_materialization_sha256")
        != _hash_without(value, "runtime_materialization_sha256")
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


def _recovery_epoch003_input_zero_effects_valid(
    state: Mapping[str, Any],
) -> bool:
    return bool(
        state.get("reservation_count_delta") == 0
        and state.get("attempt_id") is None
        and state.get("formal_exact134_invocation_count") == 0
        and state.get("collection_state") == "NOT_STARTED"
        and state.get("test_execution_state") == "NOT_STARTED"
        and state.get("pytest_main_called") is False
        and state.get("automatic_progression") is False
        and state.get("body_free") is True
    )


def _recovery_epoch003_receipt_context_valid(
    state: Mapping[str, Any],
) -> bool:
    source = state.get("source_closure")
    bootstrap = state.get("bootstrap_closure")
    event_identity = state.get("event1_external_identity")
    return bool(
        state.get("logical_cycle_id") == "NLS_V3_CYCLE_001"
        and state.get("recovery_epoch_id")
        == "NLS_V3_CYCLE001_RECOVERY_EPOCH_003"
        and isinstance(state.get("candidate_version_id"), str)
        and bool(state.get("candidate_version_id"))
        and _SHA256_RE.fullmatch(
            str(state.get("preflight_challenge_id", ""))
        )
        is not None
        and _SHA256_RE.fullmatch(str(state.get("preflight_id", "")))
        is not None
        and _recovery_epoch003_input_zero_effects_valid(state)
        and type(source) is dict
        and _SHA256_RE.fullmatch(
            str(source.get("source_closure_sha256", ""))
        )
        is not None
        and source.get("source_closure_sha256")
        == _hash_without(source, "source_closure_sha256")
        and type(bootstrap) is dict
        and _SHA256_RE.fullmatch(
            str(bootstrap.get("bootstrap_closure_sha256", ""))
        )
        is not None
        and bootstrap.get("bootstrap_closure_sha256")
        == _hash_without(bootstrap, "bootstrap_closure_sha256")
        and _recovery_epoch003_external_identity_valid(
            event_identity,
            roles=frozenset(
                {"RECOVERY_EPOCH003_SOURCE_BASELINE_EVENT"}
            ),
            schema=_RECOVERY_EPOCH003_EVENT_SCHEMA,
            path=_RECOVERY_EPOCH003_EVENT1_PATH,
            logical_hash=(
                event_identity.get("logical_artifact_sha256")
                if type(event_identity) is dict
                else ""
            ),
        )
    )


def _recovery_epoch003_projection_from_event(
    event: Mapping[str, Any],
) -> dict[str, Any]:
    source = event["source_closure"]
    bootstrap = event["bootstrap_closure"]
    return {
        "source_commit_sha1": source["source_commit_sha1"],
        "source_tree_sha1": source["source_tree_sha1"],
        "formal_owner_artifacts_sha256": bootstrap[
            "formal_owner_artifacts_sha256"
        ],
        "formal_test_manifest_sha256": bootstrap[
            "formal_test_manifest_sha256"
        ],
        "import_manifest_sha256": bootstrap["import_manifest_sha256"],
        "dependency_lock_raw_sha256": bootstrap[
            "dependency_lock_identity"
        ]["raw_sha256"],
        "wheel_bundle_manifest_sha256": bootstrap[
            "wheel_bundle_manifest_sha256"
        ],
        "installed_distributions_sha256": bootstrap[
            "expected_installed_distributions_sha256"
        ],
        "pytest_distribution_identity": deepcopy(
            bootstrap["expected_pytest_distribution_identity"]
        ),
        "python_runtime_identity": deepcopy(
            bootstrap["expected_python_runtime_identity"]
        ),
        "loaded_plugin_manifest_sha256": bootstrap[
            "loaded_plugin_manifest_sha256"
        ],
        "preflight_argv_sha256": bootstrap["preflight_argv_sha256"],
        "formal_worker_argv_sha256": bootstrap[
            "formal_worker_argv_sha256"
        ],
        "environment_policy_sha256": bootstrap[
            "environment_policy_sha256"
        ],
    }


def _recovery_epoch003_projection_from_observation(
    observation: Mapping[str, Any],
) -> dict[str, Any]:
    return {
        key: deepcopy(observation[key])
        for key in _RECOVERY_EPOCH003_PROJECTION_KEYS
    }


def _recovery_epoch003_baseline_valid(
    state: Mapping[str, Any],
) -> bool:
    source = state.get("source_closure")
    bootstrap = state.get("bootstrap_closure")
    reference = state.get("reference_runtime_observation")
    reference_identity = state.get(
        "reference_runtime_observation_external_identity"
    )
    event = state.get("event1_at_publication")
    event_identity = state.get("event1_external_identity")
    if (
        state.get("logical_cycle_id") != "NLS_V3_CYCLE_001"
        or state.get("recovery_epoch_id")
        != "NLS_V3_CYCLE001_RECOVERY_EPOCH_003"
        or not isinstance(state.get("candidate_version_id"), str)
        or not state.get("candidate_version_id")
        or _SHA256_RE.fullmatch(
            str(state.get("preflight_challenge_id", ""))
        )
        is None
        or _SHA256_RE.fullmatch(str(state.get("preflight_id", "")))
        is None
        or state.get("reference_materialization_performed") is not True
        or not _recovery_epoch003_input_zero_effects_valid(state)
        or type(source) is not dict
        or set(source) != _RECOVERY_EPOCH003_SOURCE_KEYS
        or source.get("schema_version") != _RECOVERY_EPOCH003_SOURCE_SCHEMA
        or source.get("source_closure_sha256")
        != _hash_without(source, "source_closure_sha256")
        or type(bootstrap) is not dict
        or set(bootstrap) != _RECOVERY_EPOCH003_BOOTSTRAP_KEYS
        or bootstrap.get("schema_version")
        != _RECOVERY_EPOCH003_BOOTSTRAP_SCHEMA
        or bootstrap.get("bootstrap_closure_sha256")
        != _hash_without(bootstrap, "bootstrap_closure_sha256")
        or source.get("source_commit_sha1")
        != bootstrap.get("source_commit_sha1")
        or source.get("source_tree_sha1")
        != bootstrap.get("source_tree_sha1")
        or source.get("formal_test_manifest_sha256")
        != bootstrap.get("formal_test_manifest_sha256")
        or source.get("bootstrap_closure_sha256")
        != bootstrap.get("bootstrap_closure_sha256")
        or source.get("worktree_clean") is not True
        or bootstrap.get("body_free") is not True
        or validate_recovery_epoch003_source_bootstrap_contract_state(
            {
                "source_closure": source,
                "bootstrap_closure": bootstrap,
            }
        )
        != ()
    ):
        return False
    if type(reference) is not dict:
        return False
    installed = reference.get("installed_distributions")
    lock = reference.get("dependency_lock_identity")
    runtime = reference.get("runtime_materialization")
    environment = reference.get("environment_policy")
    if (
        type(reference) is not dict
        or set(reference) != _RECOVERY_EPOCH003_REFERENCE_KEYS
        or reference.get("schema_version")
        != RECOVERY_EPOCH003_REFERENCE_OBSERVATION_SCHEMA
        or reference.get("logical_cycle_id")
        != state.get("logical_cycle_id")
        or reference.get("recovery_epoch_id")
        != state.get("recovery_epoch_id")
        or not isinstance(reference.get("authority_token"), str)
        or not reference.get("authority_token")
        or reference.get("reference_runtime_observation_sha256")
        != _hash_without(
            reference,
            "reference_runtime_observation_sha256",
        )
        or reference.get("source_commit_sha1")
        != bootstrap.get("source_commit_sha1")
        or reference.get("source_tree_sha1")
        != bootstrap.get("source_tree_sha1")
        or reference.get("dependency_lock_identity")
        != bootstrap.get("dependency_lock_identity")
        or reference.get("wheel_bundle_manifest_sha256")
        != bootstrap.get("wheel_bundle_manifest_sha256")
        or reference.get("python_runtime_identity")
        != bootstrap.get("expected_python_runtime_identity")
        or reference.get("pytest_distribution_identity")
        != bootstrap.get("expected_pytest_distribution_identity")
        or reference.get("installed_distributions_sha256")
        != bootstrap.get("expected_installed_distributions_sha256")
        or reference.get("environment_policy")
        != bootstrap.get("environment_policy")
        or reference.get("environment_policy_sha256")
        != bootstrap.get("environment_policy_sha256")
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
        or reference.get("installed_distributions_sha256")
        != artifact_sha256(installed)
        or reference.get("pytest_distribution_identity")
        not in installed
        or reference["pytest_distribution_identity"].get(
            "normalized_distribution_name"
        )
        != "pytest"
        or not _recovery_epoch003_runtime_identity_valid(
            reference.get("python_runtime_identity")
        )
        or type(lock) is not dict
        or set(lock) != _RECOVERY_EPOCH003_DEPENDENCY_LOCK_KEYS
        or lock.get("identity_class") != "EXACT_HASH_LOCK"
        or not isinstance(lock.get("path"), str)
        or not lock.get("path")
        or _SHA256_RE.fullmatch(str(lock.get("raw_sha256", "")))
        is None
        or not _recovery_epoch003_environment_valid(environment)
        or reference.get("environment_policy_sha256")
        != artifact_sha256(environment)
        or not _recovery_epoch003_materialization_valid(
            runtime,
            dependency_lock_raw_sha256=lock.get("raw_sha256"),
            wheel_bundle_manifest_sha256=reference.get(
                "wheel_bundle_manifest_sha256"
            ),
            distribution_count=len(installed),
        )
        or reference.get("reservation_count_delta") != 0
        or reference.get("formal_exact134_invocation_count") != 0
        or reference.get("collection_state") != "NOT_STARTED"
        or reference.get("test_execution_state") != "NOT_STARTED"
        or reference.get("body_free") is not True
        or not _recovery_epoch003_external_identity_valid(
            reference_identity,
            roles=frozenset(
                {"RECOVERY_EPOCH003_REFERENCE_RUNTIME_OBSERVATION"}
            ),
            schema=RECOVERY_EPOCH003_REFERENCE_OBSERVATION_SCHEMA,
            path=_RECOVERY_EPOCH003_REFERENCE_PATH,
            logical_hash=reference.get(
                "reference_runtime_observation_sha256"
            ),
        )
        or source.get(
            "reference_runtime_observation_external_identity_sha256"
        )
        != reference_identity.get("identity_sha256")
        or bootstrap.get(
            "reference_runtime_observation_external_identity"
        )
        != reference_identity
    ):
        return False
    if (
        type(event) is not dict
        or event.get("schema_version") != _RECOVERY_EPOCH003_EVENT_SCHEMA
        or event.get("source_closure") != source
        or event.get("bootstrap_closure") != bootstrap
        or event.get("body_free") is not True
        or event.get("automatic_progression") is not False
        or event.get("event_sha256")
        != _hash_without(event, "event_sha256")
        or validate_recovery_epoch003_sequence_event1_contract_state(
            state
        )
        != ()
        or not _recovery_epoch003_external_identity_valid(
            event_identity,
            roles=frozenset(
                {"RECOVERY_EPOCH003_SOURCE_BASELINE_EVENT"}
            ),
            schema=_RECOVERY_EPOCH003_EVENT_SCHEMA,
            path=_RECOVERY_EPOCH003_EVENT1_PATH,
            logical_hash=event.get("event_sha256"),
        )
    ):
        return False
    return True


def _recovery_epoch003_operational_owner_valid(
    state: Mapping[str, Any],
    *,
    expected: Mapping[str, Any],
    owner: Mapping[str, Any],
) -> bool:
    observation = state.get("operational_runtime_observation")
    identity = state.get(
        "operational_runtime_observation_external_identity"
    )
    event = state.get("event1_at_publication")
    event_identity = state.get("event1_external_identity")
    reference = state.get("reference_runtime_observation")
    bootstrap = state.get("bootstrap_closure")
    runtime = (
        observation.get("runtime_materialization")
        if type(observation) is dict
        else None
    )
    reference_runtime = (
        reference.get("runtime_materialization")
        if type(reference) is dict
        else None
    )
    owner_hash = artifact_sha256(owner)
    if (
        type(observation) is not dict
        or set(observation) != _RECOVERY_EPOCH003_OPERATIONAL_KEYS
        or observation.get("schema_version")
        != RECOVERY_EPOCH003_OPERATIONAL_OBSERVATION_SCHEMA
        or observation.get("logical_cycle_id")
        != state.get("logical_cycle_id")
        or observation.get("recovery_epoch_id")
        != state.get("recovery_epoch_id")
        or observation.get("candidate_version_id")
        != state.get("candidate_version_id")
        or not isinstance(observation.get("authority_token"), str)
        or not observation.get("authority_token")
        or observation.get("preflight_challenge_id")
        != state.get("preflight_challenge_id")
        or observation.get("preflight_id") != state.get("preflight_id")
        or observation.get(
            "source_baseline_event_external_identity_sha256"
        )
        != event_identity.get("identity_sha256")
        or observation.get("source_closure_sha256")
        != event["source_closure"].get("source_closure_sha256")
        or observation.get("bootstrap_closure_sha256")
        != event["bootstrap_closure"].get("bootstrap_closure_sha256")
        or state.get("expected_operational_projection") != expected
        or state.get("owner_operational_projection") != owner
        or expected != owner
        or observation.get("owner_operational_projection_sha256")
        != owner_hash
        or observation.get("owner_validation_state") != "VALID"
        or observation.get("independent_verification_state") != "VALID"
        or observation.get("worktree_clean") is not True
        or observation.get("reservation_count_delta") != 0
        or observation.get("formal_exact134_invocation_count") != 0
        or observation.get("collection_state") != "NOT_STARTED"
        or observation.get("test_execution_state") != "NOT_STARTED"
        or observation.get("pytest_main_called") is not False
        or observation.get("body_free") is not True
        or observation.get("environment_policy")
        != event["bootstrap_closure"].get("environment_policy")
        or observation.get("environment_policy_sha256")
        != artifact_sha256(observation.get("environment_policy"))
        or observation.get("operational_runtime_observation_sha256")
        != _hash_without(
            observation,
            "operational_runtime_observation_sha256",
        )
        or type(runtime) is not dict
        or type(bootstrap) is not dict
        or not _recovery_epoch003_materialization_valid(
            runtime,
            dependency_lock_raw_sha256=observation.get(
                "dependency_lock_raw_sha256"
            ),
            wheel_bundle_manifest_sha256=observation.get(
                "wheel_bundle_manifest_sha256"
            ),
            distribution_count=len(
                bootstrap.get("expected_installed_distributions", [])
            ),
        )
        or observation.get("runtime_root_identity_sha256")
        != runtime.get("runtime_root_identity_sha256")
        or type(reference_runtime) is not dict
        or observation.get("reference_runtime_root_identity_sha256")
        != reference_runtime.get("runtime_root_identity_sha256")
        or observation.get("runtime_root_identity_sha256")
        == observation.get("reference_runtime_root_identity_sha256")
        or not _recovery_epoch003_external_identity_valid(
            identity,
            roles=frozenset(
                {
                    "RECOVERY_EPOCH003_OPERATIONAL_RUNTIME_OBSERVATION",
                    (
                        "RECOVERY_EPOCH003_OPERATIONAL_RUNTIME_"
                        "OBSERVATION_FAILURE_EVIDENCE"
                    ),
                }
            ),
            schema=RECOVERY_EPOCH003_OPERATIONAL_OBSERVATION_SCHEMA,
            path=_RECOVERY_EPOCH003_OPERATIONAL_PATH,
            logical_hash=observation.get(
                "operational_runtime_observation_sha256"
            ),
        )
    ):
        return False
    roots = (
        observation.get("runtime_root_identity_sha256"),
        observation.get("reference_runtime_root_identity_sha256"),
        observation.get("attempt_registry_root_identity_sha256"),
    )
    return all(
        isinstance(value, str)
        and _SHA256_RE.fullmatch(value) is not None
        for value in roots
    ) and _recovery_epoch003_input_zero_effects_valid(state)


def _recovery_epoch003_failure_evidence_identity(
    state: Mapping[str, Any],
) -> dict[str, Any] | None:
    observation = state.get("operational_runtime_observation")
    identity = state.get(
        "operational_runtime_observation_external_identity"
    )
    logical_hash = (
        observation.get("operational_runtime_observation_sha256")
        if type(observation) is dict
        else None
    )
    if not _recovery_epoch003_external_identity_valid(
        identity,
        roles=frozenset(
            {
                "RECOVERY_EPOCH003_OPERATIONAL_RUNTIME_OBSERVATION",
                (
                    "RECOVERY_EPOCH003_OPERATIONAL_RUNTIME_"
                    "OBSERVATION_FAILURE_EVIDENCE"
                ),
            }
        ),
        schema=RECOVERY_EPOCH003_OPERATIONAL_OBSERVATION_SCHEMA,
        path=_RECOVERY_EPOCH003_OPERATIONAL_PATH,
        logical_hash=logical_hash,
    ):
        return None
    result = deepcopy(identity)
    result["artifact_role"] = (
        "RECOVERY_EPOCH003_OPERATIONAL_RUNTIME_"
        "OBSERVATION_FAILURE_EVIDENCE"
    )
    result["identity_sha256"] = _hash_without(
        result,
        "identity_sha256",
    )
    return result


def _recovery_epoch003_failure_receipt(
    state: Mapping[str, Any],
    failure_class: str,
    *,
    include_observation: bool,
    expected_hash: str | None = None,
    owner_hash: str | None = None,
    independent_hash: str | None = None,
) -> dict[str, Any]:
    observation = state.get("operational_runtime_observation")
    observation_identity = state.get(
        "operational_runtime_observation_external_identity"
    )
    event_identity = state.get("event1_external_identity")
    source = state.get("source_closure")
    bootstrap = state.get("bootstrap_closure")
    if not include_observation:
        observation_identity = None
        observation_hash = None
        owner_hash = None
        independent_hash = None
        combined_hash = None
    else:
        observation_identity = (
            _recovery_epoch003_failure_evidence_identity(state)
        )
        observation_hash = (
            observation.get("operational_runtime_observation_sha256")
            if type(observation) is dict
            else None
        )
        if failure_class == "OPERATIONAL_RUNTIME_IDENTITY_MISMATCH":
            independent_hash = owner_hash
            combined_hash = (
                artifact_sha256(
                    {"expected": expected_hash, "observed": owner_hash}
                )
                if expected_hash is not None and owner_hash is not None
                else None
            )
        else:
            combined_hash = (
                artifact_sha256(
                    {
                        "owner": owner_hash,
                        "independent": independent_hash,
                    }
                )
                if owner_hash is not None and independent_hash is not None
                else None
            )
    failure_stage = {
        "BOOTSTRAP_SCHEMA_PAIR_UNSUPPORTED": "BEFORE_MATERIALIZATION",
        "SOURCE_BOOTSTRAP_BASELINE_MISMATCH": "BEFORE_MATERIALIZATION",
        (
            "OPERATIONAL_MATERIALIZATION_BINDING_MISSING"
        ): "MATERIALIZATION_BINDING",
        (
            "OPERATIONAL_RUNTIME_IDENTITY_MISMATCH"
        ): "EXPECTED_OBSERVED_COMPARISON",
        (
            "INDEPENDENT_OPERATIONAL_PROJECTION_DISAGREEMENT"
        ): "INDEPENDENT_PROJECTION",
    }[failure_class]
    authority_token = (
        observation.get("authority_token")
        if (
            include_observation
            and type(observation) is dict
            and isinstance(observation.get("authority_token"), str)
            and observation.get("authority_token")
        )
        else "UNISSUED_RECOVERY_EPOCH003_PREFLIGHT_AUTHORITY"
    )
    receipt = {
        "schema_version": RECOVERY_EPOCH003_FAILURE_SCHEMA,
        "logical_cycle_id": state.get("logical_cycle_id"),
        "recovery_epoch_id": state.get("recovery_epoch_id"),
        "candidate_version_id": state.get("candidate_version_id"),
        "authority_token": authority_token,
        "preflight_challenge_id": state.get("preflight_challenge_id"),
        "preflight_id": state.get("preflight_id"),
        "event1_external_identity_sha256": (
            event_identity.get("identity_sha256")
            if type(event_identity) is dict
            else None
        ),
        "source_closure_sha256": (
            source.get("source_closure_sha256")
            if type(source) is dict
            else None
        ),
        "bootstrap_closure_sha256": (
            bootstrap.get("bootstrap_closure_sha256")
            if type(bootstrap) is dict
            else None
        ),
        "operational_runtime_observation_state": (
            "OBSERVED" if include_observation else "NOT_AVAILABLE"
        ),
        "operational_runtime_observation_external_identity": (
            deepcopy(observation_identity)
            if type(observation_identity) is dict
            else None
        ),
        "operational_runtime_observation_sha256": observation_hash,
        "owner_operational_projection_sha256": owner_hash,
        "independent_operational_projection_sha256": independent_hash,
        "expected_observed_projection_sha256": combined_hash,
        "failure_stage": failure_stage,
        "failure_class": failure_class,
        "failure_issue_codes": [failure_class],
        "stop_code": RECOVERY_EPOCH003_PREFLIGHT_STOP_CODE,
        "reservation_count_delta": 0,
        "attempt_id": None,
        "formal_exact134_invocation_count": 0,
        "owner_validation_state": (
            "INVALID"
            if failure_class
            == "OPERATIONAL_RUNTIME_IDENTITY_MISMATCH"
            else "NOT_STARTED"
            if not include_observation
            else "VALID"
        ),
        "independent_verification_state": (
            "INVALID"
            if failure_class
            == "INDEPENDENT_OPERATIONAL_PROJECTION_DISAGREEMENT"
            else "NOT_STARTED"
            if not include_observation
            else "VALID"
        ),
        "automatic_retry": False,
        "automatic_progression": False,
        "body_free": True,
        "receipt_sha256": "",
    }
    receipt["receipt_sha256"] = _hash_without(receipt, "receipt_sha256")
    return receipt


def _recovery_epoch003_readiness_receipt(
    state: Mapping[str, Any],
    *,
    expected_hash: str,
    observed_hash: str,
) -> dict[str, Any]:
    event = state["event1_at_publication"]
    event_identity = state["event1_external_identity"]
    observation = state["operational_runtime_observation"]
    observation_identity = state[
        "operational_runtime_observation_external_identity"
    ]
    receipt = {
        "schema_version": RECOVERY_EPOCH003_READINESS_SCHEMA,
        "logical_cycle_id": state.get("logical_cycle_id"),
        "recovery_epoch_id": state.get("recovery_epoch_id"),
        "candidate_version_id": state.get("candidate_version_id"),
        "authority_token": observation.get("authority_token"),
        "event1_external_identity_sha256": event_identity.get(
            "identity_sha256"
        ),
        "event1_bootstrap_closure": deepcopy(event["bootstrap_closure"]),
        "event1_bootstrap_closure_sha256": event[
            "bootstrap_closure"
        ].get("bootstrap_closure_sha256"),
        "operational_runtime_observation_external_identity": deepcopy(
            observation_identity
        ),
        "operational_runtime_observation_sha256": observation.get(
            "operational_runtime_observation_sha256"
        ),
        "expected_observed_projection_sha256": artifact_sha256(
            {"expected": expected_hash, "observed": observed_hash}
        ),
        "readiness_receipt_path": _RECOVERY_EPOCH003_READINESS_PATH,
        "preflight_started_at_utc": state.get(
            "preflight_started_at_utc"
        ),
        "preflight_finished_at_utc": state.get(
            "preflight_finished_at_utc"
        ),
        "owner_validation_state": "VALID",
        "independent_verification_state": "VALID",
        "reservation_count_delta": 0,
        "formal_exact134_invocation_count": 0,
        "collection_state": "NOT_STARTED",
        "test_execution_state": "NOT_STARTED",
        "pytest_main_called": False,
        "automatic_progression": False,
        "body_free": True,
        "bootstrap_readiness_receipt_sha256": "",
    }
    receipt["bootstrap_readiness_receipt_sha256"] = _hash_without(
        receipt,
        "bootstrap_readiness_receipt_sha256",
    )
    return receipt


def evaluate_recovery_epoch003_preflight_contract(
    state: Mapping[str, Any],
) -> dict[str, Any] | tuple[str, ...]:
    """Evaluate supplied Epoch003 state without materializing or reserving."""

    try:
        if (
            type(state) is not dict
            or not _recovery_epoch003_receipt_context_valid(state)
        ):
            return (RECOVERY_EPOCH003_PREFLIGHT_STOP_CODE,)
        source = state.get("source_closure")
        bootstrap = state.get("bootstrap_closure")
        pair = (
            source.get("schema_version")
            if type(source) is dict
            else None,
            bootstrap.get("schema_version")
            if type(bootstrap) is dict
            else None,
        )
        if pair not in _RECOVERY_EPOCH003_KNOWN_SCHEMA_PAIRS:
            return _recovery_epoch003_failure_receipt(
                state,
                "BOOTSTRAP_SCHEMA_PAIR_UNSUPPORTED",
                include_observation=False,
            )
        if (
            pair != _RECOVERY_EPOCH003_KNOWN_SCHEMA_PAIRS[1]
            or not _recovery_epoch003_baseline_valid(state)
        ):
            return _recovery_epoch003_failure_receipt(
                state,
                "SOURCE_BOOTSTRAP_BASELINE_MISMATCH",
                include_observation=False,
            )
        observation = state.get("operational_runtime_observation")
        observation_identity = state.get(
            "operational_runtime_observation_external_identity"
        )
        owner_state = state.get("owner_operational_projection")
        if (
            state.get("operational_materialization_performed") is not True
            or type(observation) is not dict
            or set(observation) != _RECOVERY_EPOCH003_OPERATIONAL_KEYS
            or type(observation_identity) is not dict
            or type(owner_state) is not dict
        ):
            return _recovery_epoch003_failure_receipt(
                state,
                "OPERATIONAL_MATERIALIZATION_BINDING_MISSING",
                include_observation=False,
            )
        if not _recovery_epoch003_external_identity_valid(
            observation_identity,
            roles=frozenset(
                {
                    "RECOVERY_EPOCH003_OPERATIONAL_RUNTIME_OBSERVATION",
                    (
                        "RECOVERY_EPOCH003_OPERATIONAL_RUNTIME_"
                        "OBSERVATION_FAILURE_EVIDENCE"
                    ),
                }
            ),
            schema=RECOVERY_EPOCH003_OPERATIONAL_OBSERVATION_SCHEMA,
            path=_RECOVERY_EPOCH003_OPERATIONAL_PATH,
            logical_hash=observation.get(
                "operational_runtime_observation_sha256"
            ),
        ):
            return _recovery_epoch003_failure_receipt(
                state,
                "OPERATIONAL_MATERIALIZATION_BINDING_MISSING",
                include_observation=False,
            )
        if (
            not isinstance(observation.get("authority_token"), str)
            or not observation.get("authority_token")
        ):
            return _recovery_epoch003_failure_receipt(
                state,
                "OPERATIONAL_MATERIALIZATION_BINDING_MISSING",
                include_observation=False,
            )
        started = state.get("preflight_started_at_utc")
        finished = state.get("preflight_finished_at_utc")
        if (
            _RECOVERY_EPOCH003_UTC_RE.fullmatch(str(started)) is None
            or _RECOVERY_EPOCH003_UTC_RE.fullmatch(str(finished)) is None
            or started > finished
        ):
            return _recovery_epoch003_failure_receipt(
                state,
                "OPERATIONAL_MATERIALIZATION_BINDING_MISSING",
                include_observation=False,
            )
        expected = _recovery_epoch003_projection_from_event(
            state["event1_at_publication"]
        )
        owner = _recovery_epoch003_projection_from_observation(observation)
        expected_hash = artifact_sha256(expected)
        owner_hash = artifact_sha256(owner)
        if not _recovery_epoch003_operational_owner_valid(
            state,
            expected=expected,
            owner=owner,
        ):
            return _recovery_epoch003_failure_receipt(
                state,
                "OPERATIONAL_RUNTIME_IDENTITY_MISMATCH",
                include_observation=True,
                expected_hash=expected_hash,
                owner_hash=owner_hash,
            )
        independent_hash = observation.get(
            "independent_operational_projection_sha256"
        )
        independent_issues = (
            verify_recovery_epoch003_bootstrap_source_runtime_contract(
                state
            )
        )
        if independent_issues == (
            "INDEPENDENT_OPERATIONAL_PROJECTION_DISAGREEMENT",
        ):
            return _recovery_epoch003_failure_receipt(
                state,
                "INDEPENDENT_OPERATIONAL_PROJECTION_DISAGREEMENT",
                include_observation=True,
                owner_hash=owner_hash,
                independent_hash=independent_hash,
            )
        if (
            independent_issues != ()
            or _SHA256_RE.fullmatch(str(independent_hash)) is None
            or independent_hash != owner_hash
        ):
            return _recovery_epoch003_failure_receipt(
                state,
                "OPERATIONAL_RUNTIME_IDENTITY_MISMATCH",
                include_observation=True,
                expected_hash=expected_hash,
                owner_hash=owner_hash,
            )
        if (
            observation_identity.get("artifact_role")
            != "RECOVERY_EPOCH003_OPERATIONAL_RUNTIME_OBSERVATION"
        ):
            return _recovery_epoch003_failure_receipt(
                state,
                "OPERATIONAL_RUNTIME_IDENTITY_MISMATCH",
                include_observation=True,
                expected_hash=expected_hash,
                owner_hash=owner_hash,
            )
        return _recovery_epoch003_readiness_receipt(
            state,
            expected_hash=expected_hash,
            observed_hash=owner_hash,
        )
    except (
        AttributeError,
        KeyError,
        RecursionError,
        TypeError,
        UnicodeError,
        ValueError,
    ):
        safe_state = state if type(state) is dict else {}
        if not _recovery_epoch003_receipt_context_valid(safe_state):
            return (RECOVERY_EPOCH003_PREFLIGHT_STOP_CODE,)
        return _recovery_epoch003_failure_receipt(
            safe_state,
            "SOURCE_BOOTSTRAP_BASELINE_MISMATCH",
            include_observation=False,
        )


_RECOVERY_EPOCH003_CURRENT_STRICT_ZERO_EFFECTS = {
    "reference_runtime_materialization_count": 0,
    "operational_runtime_materialization_count": 0,
    "reference_observation_publication_count": 0,
    "operational_admission_publication_count": 0,
    "runtime_publication_count": 0,
    "candidate_publication_count": 0,
    "event1_publication_count": 0,
    "readiness_publication_count": 0,
    "failure_publication_count": 0,
    "reservation_count": 0,
    "attempt_count": 0,
    "formal_exact134_invocation_count": 0,
    "formal_collection_count": 0,
    "formal_execution_count": 0,
}
_RECOVERY_EPOCH003_CURRENT_STRICT_OVERRIDE_KEYS = frozenset(
    {
        "profile",
        "verification_mode",
        "allow_historical_fallback",
    }
)


def _recovery_epoch003_current_strict_preflight_result(
    failure_code: str | None,
) -> dict[str, Any]:
    return {
        "schema_version": (
            "cocolon.emlis.nls_v3.recovery_epoch003."
            "current_strict_preflight_result.v1"
        ),
        "current_strict_preflight_state": (
            "VALID" if failure_code is None else "INVALID"
        ),
        "failure_code": failure_code,
        "source_baseline_state": "UNLOCKED",
        "body_free": True,
        "automatic_progression": False,
        "pytest_main_called": False,
        **_RECOVERY_EPOCH003_CURRENT_STRICT_ZERO_EFFECTS,
    }


def execute_recovery_epoch003_current_strict_preflight_v1(
    state: Mapping[str, Any],
) -> dict[str, Any]:
    """Verify current supplied state without materializing or publishing."""

    try:
        if type(state) is not dict:
            return _recovery_epoch003_current_strict_preflight_result(
                "SOURCE_BOOTSTRAP_BASELINE_MISMATCH"
            )
        if any(
            key in state
            for key in _RECOVERY_EPOCH003_CURRENT_STRICT_OVERRIDE_KEYS
        ):
            return _recovery_epoch003_current_strict_preflight_result(
                (
                    "RECOVERY_EPOCH003_CURRENT_STRICT_"
                    "PROFILE_OVERRIDE_FORBIDDEN"
                )
            )
        issues = (
            verify_recovery_epoch003_bootstrap_source_runtime_contract_current(
                state
            )
        )
        if (
            type(issues) is not tuple
            or len(issues) > 1
            or any(
                not isinstance(issue, str) or not issue
                for issue in issues
            )
        ):
            return _recovery_epoch003_current_strict_preflight_result(
                "SOURCE_BOOTSTRAP_BASELINE_MISMATCH"
            )
        return _recovery_epoch003_current_strict_preflight_result(
            issues[0] if issues else None
        )
    except (
        AttributeError,
        KeyError,
        OSError,
        RecursionError,
        subprocess.SubprocessError,
        SyntaxError,
        TypeError,
        UnicodeError,
        ValueError,
    ):
        return _recovery_epoch003_current_strict_preflight_result(
            "SOURCE_BOOTSTRAP_BASELINE_MISMATCH"
        )


def _recovery_epoch003_effective_environment_policy(
    environment: Any,
) -> dict[str, Any] | None:
    if (
        type(environment) is not dict
        or any(
            not isinstance(key, str)
            or not isinstance(value, str)
            for key, value in environment.items()
        )
        or any(
            key.startswith("PIP_")
            or key in {
                "PYTHONPATH",
                "PYTHONHOME",
                "PYTEST_ADDOPTS",
                "PYTEST_PLUGINS",
            }
            for key in environment
        )
    ):
        return None
    path = environment.get("PATH")
    lang = environment.get("LANG")
    lc_all = environment.get("LC_ALL")
    if not all(
        isinstance(value, str) and bool(value)
        for value in (path, lang, lc_all)
    ):
        return None
    return {
        "fixed": {
            "PYTEST_DISABLE_PLUGIN_AUTOLOAD": "1",
            "PYTHONDONTWRITEBYTECODE": "1",
        },
        "removed": ["PYTEST_ADDOPTS", "PYTEST_PLUGINS", "PYTHONPATH"],
        "inherited_path_sha256": hashlib.sha256(
            path.encode("utf-8")
        ).hexdigest(),
        "lang": lang,
        "lc_all": lc_all,
    }


def _recovery_epoch003_sanitized_environment(
    environment: Mapping[str, str],
) -> dict[str, str]:
    return {
        "PATH": environment["PATH"],
        "LANG": environment["LANG"],
        "LC_ALL": environment["LC_ALL"],
        "PYTEST_DISABLE_PLUGIN_AUTOLOAD": "1",
        "PYTHONDONTWRITEBYTECODE": "1",
    }


def _recovery_epoch003_is_outside(
    candidate: Path,
    protected: Path,
) -> bool:
    if candidate == protected:
        return False
    try:
        candidate.relative_to(protected)
    except ValueError:
        return True
    return False


def _recovery_epoch003_paths_disjoint(left: Path, right: Path) -> bool:
    return bool(
        _recovery_epoch003_is_outside(left, right)
        and _recovery_epoch003_is_outside(right, left)
    )


def _recovery_epoch003_path_has_symlink_component(path: Path) -> bool:
    absolute = path.absolute()
    current = Path(absolute.anchor)
    for part in absolute.parts[1:]:
        current /= part
        if current.is_symlink():
            return True
    return False


def _recovery_epoch003_git(root: Path, *args: str) -> str:
    return subprocess.run(
        ["git", *args],
        cwd=root,
        check=True,
        capture_output=True,
        text=True,
        timeout=20,
    ).stdout.strip()


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


def _recovery_epoch003_expected_artifact_repository(root: Path) -> bool:
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
            normalized.endswith("/MassyuRed/Cocolon")
            or normalized.endswith(":MassyuRed/Cocolon")
        )
    )


def _recovery_epoch003_load_materialization_inputs(
    state: Mapping[str, Any],
    *,
    allow_existing_destination: bool = False,
) -> tuple[
    Path,
    Path,
    Path,
    Path,
    dict[str, Any],
    str,
    dict[str, Any],
]:
    if (
        type(state) is not dict
        or set(state) != _RECOVERY_EPOCH003_MATERIALIZATION_REQUEST_KEYS
        or state.get("authority_token")
        != _RECOVERY_EPOCH003_FINAL_ISSUANCE_AUTHORITY
    ):
        raise ValueError("request shape")
    path_keys = (
        "artifact_repository_root",
        "source_repository_root",
        "dependency_lock_path",
        "wheelhouse_path",
        "destination_root",
    )
    if any(
        not isinstance(state.get(key), str) or not state.get(key)
        for key in path_keys
    ):
        raise ValueError("request path")
    raw_artifact_root = Path(state["artifact_repository_root"]).absolute()
    raw_source_root = Path(state["source_repository_root"]).absolute()
    raw_lock_path = Path(state["dependency_lock_path"]).absolute()
    raw_wheelhouse = Path(state["wheelhouse_path"]).absolute()
    raw_destination = Path(state["destination_root"]).absolute()
    if any(
        _recovery_epoch003_path_has_symlink_component(path)
        for path in (
            raw_artifact_root,
            raw_source_root,
            raw_lock_path,
            raw_wheelhouse,
            raw_destination,
            raw_destination.parent,
        )
    ):
        raise ValueError("symlink boundary")
    artifact_root = raw_artifact_root.resolve()
    source_root = raw_source_root.resolve()
    lock_path = raw_lock_path.resolve()
    wheelhouse = raw_wheelhouse.resolve()
    destination = raw_destination.resolve()
    policy = _recovery_epoch003_effective_environment_policy(
        state.get("environment")
    )
    if policy is None:
        raise ValueError("environment")
    if (
        not artifact_root.is_dir()
        or not source_root.is_dir()
        or not wheelhouse.is_dir()
        or (
            (destination.exists() or destination.is_symlink())
            if not allow_existing_destination
            else not destination.is_dir()
        )
        or any(
            not _recovery_epoch003_paths_disjoint(destination, protected)
            for protected in (artifact_root, source_root, wheelhouse)
        )
        or not _recovery_epoch003_paths_disjoint(
            artifact_root,
            source_root,
        )
        or not _recovery_epoch003_expected_source_repository(source_root)
        or not _recovery_epoch003_expected_artifact_repository(
            artifact_root
        )
    ):
        raise ValueError("root boundary")
    commit = _recovery_epoch003_git(source_root, "rev-parse", "HEAD")
    tree = _recovery_epoch003_git(
        source_root,
        "rev-parse",
        "HEAD^{tree}",
    )
    clean = (
        _recovery_epoch003_git(
            source_root,
            "status",
            "--porcelain",
            "--untracked-files=all",
        )
        == ""
    )
    if (
        not clean
        or state.get("expected_source_commit_sha1") != commit
        or state.get("expected_source_tree_sha1") != tree
        or lock_path
        != (source_root / _RECOVERY_EPOCH003_LOCK_PATH).resolve()
        or not lock_path.is_file()
    ):
        raise ValueError("source identity")
    lock, raw_sha256 = (
        load_recovery_epoch002_dependency_lock_with_raw_sha256(lock_path)
    )
    if (
        raw_sha256 != _RECOVERY_EPOCH003_LOCK_RAW_SHA256
        or lock.get("lock_sha256")
        != _RECOVERY_EPOCH003_LOCK_LOGICAL_SHA256
        or lock.get("distribution_count") != 46
        or lock.get("resolution", {}).get("pip_version") != "26.0.1"
        or lock.get("target", {}).get("python_version") != "3.12.13"
        or lock.get("target", {}).get("implementation") != "CPYTHON"
        or lock.get("target", {}).get("machine") != "x86_64"
        or validate_recovery_epoch002_dependency_lock(
            lock,
            wheel_directory=wheelhouse,
        )
    ):
        raise ValueError("lock")
    expected_names = {
        row["wheel_filename"] for row in lock["distributions"]
    }
    entries = list(os.scandir(wheelhouse))
    if (
        len(entries) != 46
        or {entry.name for entry in entries} != expected_names
        or any(
            entry.is_symlink()
            or not entry.is_file(follow_symlinks=False)
            for entry in entries
        )
    ):
        raise ValueError("wheelhouse")
    environment = _recovery_epoch003_sanitized_environment(
        state["environment"]
    )
    installer_identity, _stdlib, installer_target = (
        _recovery_epoch003_runtime_probe(
            Path(sys.executable).resolve(),
            environment=environment,
        )
    )
    if (
        installer_identity["implementation"] != "CPYTHON"
        or installer_identity["version"] != "3.12.13"
        or installer_target.get("system") != "Linux"
        or installer_target.get("machine") != "x86_64"
    ):
        raise ValueError("installer runtime")
    pip_output = subprocess.run(
        [sys.executable, "-I", "-B", "-m", "pip", "--version"],
        check=True,
        capture_output=True,
        text=True,
        timeout=30,
        env=environment,
    ).stdout.split()
    if len(pip_output) < 2 or pip_output[1] != "26.0.1":
        raise ValueError("installer pip")
    return (
        artifact_root,
        source_root,
        wheelhouse,
        destination,
        lock,
        raw_sha256,
        policy,
    )


def _recovery_epoch003_copy_wheel_nofollow(
    source: Path,
    target: Path,
) -> None:
    source_fd = os.open(
        source,
        os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0),
    )
    target_fd: int | None = None
    try:
        source_stat = os.fstat(source_fd)
        if not stat.S_ISREG(source_stat.st_mode):
            raise ValueError("wheel is not regular")
        target_fd = os.open(
            target,
            os.O_WRONLY
            | os.O_CREAT
            | os.O_EXCL
            | getattr(os, "O_NOFOLLOW", 0),
            0o400,
        )
        while True:
            chunk = os.read(source_fd, 1024 * 1024)
            if not chunk:
                break
            offset = 0
            while offset < len(chunk):
                offset += os.write(target_fd, chunk[offset:])
        os.fsync(target_fd)
    finally:
        os.close(source_fd)
        if target_fd is not None:
            os.close(target_fd)


def _recovery_epoch003_runtime_probe(
    python_executable: Path,
    *,
    environment: Mapping[str, str],
) -> tuple[dict[str, Any], frozenset[str], dict[str, str]]:
    probe = (
        "import json,platform,sys;"
        "print(json.dumps({"
        "'python_build':list(platform.python_build()),"
        "'python_compiler':platform.python_compiler(),"
        "'platform':platform.platform(),"
        "'system':platform.system(),"
        "'machine':platform.machine(),"
        "'abi_flags':sys.abiflags,"
        "'byte_order':sys.byteorder,"
        "'python_cache_tag':sys.implementation.cache_tag,"
        "'sys_platform':sys.platform,"
        "'implementation':platform.python_implementation().upper(),"
        "'version':platform.python_version(),"
        "'stdlib_module_names':sorted(sys.stdlib_module_names)"
        "},sort_keys=True))"
    )
    observed = json.loads(
        subprocess.run(
            [str(python_executable), "-I", "-B", "-c", probe],
            check=True,
            capture_output=True,
            text=True,
            timeout=30,
            env=dict(environment),
        ).stdout
    )
    stdlib = observed.get("stdlib_module_names")
    if (
        type(stdlib) is not list
        or stdlib != sorted(set(stdlib))
        or any(not isinstance(name, str) or not name for name in stdlib)
    ):
        raise ValueError("stdlib probe")
    identity = {
        "executable_sha256": hashlib.sha256(
            python_executable.read_bytes()
        ).hexdigest(),
        "implementation": observed["implementation"],
        "version": observed["version"],
        "build_sha256": artifact_sha256(
            {
                "python_build": observed["python_build"],
                "python_compiler": observed["python_compiler"],
                "platform": observed["platform"],
                "abi_flags": observed["abi_flags"],
            }
        ),
    }
    target = {
        "system": observed["system"],
        "machine": observed["machine"],
        "abi_flags": observed["abi_flags"],
        "byte_order": observed["byte_order"],
        "python_cache_tag": observed["python_cache_tag"],
        "sys_platform": observed["sys_platform"],
    }
    return identity, frozenset(stdlib), target


def _recovery_epoch003_installed_identities(
    lock: Mapping[str, Any],
) -> list[dict[str, Any]]:
    rows = [
        {
            key: row[key]
            for key in _RECOVERY_EPOCH003_DISTRIBUTION_KEYS
        }
        for row in lock["distributions"]
    ]
    rows.sort(key=lambda row: row["normalized_distribution_name"])
    return rows


def _recovery_epoch003_root_identity(
    *,
    root: Path,
    materialization_kind: str,
    source_commit_sha1: str,
    source_tree_sha1: str,
    lock_raw_sha256: str,
    wheel_bundle_manifest_sha256: str,
    installed_distributions: list[dict[str, Any]],
    python_runtime_identity: Mapping[str, Any],
    pytest_distribution_identity: Mapping[str, Any],
    environment_policy: Mapping[str, Any],
) -> str:
    nonce_path = root / _RECOVERY_EPOCH003_ROOT_NONCE_FILE
    descriptor = os.open(
        nonce_path,
        os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0),
    )
    try:
        nonce_stat = os.fstat(descriptor)
        nonce = os.read(descriptor, 33)
    finally:
        os.close(descriptor)
    if (
        not stat.S_ISREG(nonce_stat.st_mode)
        or len(nonce) != 32
        or nonce_stat.st_nlink != 1
        or nonce_stat.st_uid != os.geteuid()
        or nonce_stat.st_mode
        & (stat.S_IWUSR | stat.S_IWGRP | stat.S_IWOTH)
        or materialization_kind not in {"REFERENCE", "OPERATIONAL"}
    ):
        raise ValueError("root nonce")
    preimage = {
        "schema_version": (
            "cocolon.emlis.nls_v3.recovery_epoch003."
            "runtime_root_identity_preimage.v1"
        ),
        "materialization_kind": materialization_kind,
        "root_nonce_sha256": hashlib.sha256(nonce).hexdigest(),
        "source_commit_sha1": source_commit_sha1,
        "source_tree_sha1": source_tree_sha1,
        "dependency_lock_raw_sha256": lock_raw_sha256,
        "wheel_bundle_manifest_sha256": wheel_bundle_manifest_sha256,
        "installed_distributions_sha256": artifact_sha256(
            installed_distributions
        ),
        "python_runtime_identity_sha256": artifact_sha256(
            python_runtime_identity
        ),
        "pytest_distribution_identity_sha256": artifact_sha256(
            pytest_distribution_identity
        ),
        "environment_policy_sha256": artifact_sha256(
            environment_policy
        ),
    }
    if set(preimage) != _RECOVERY_EPOCH003_ROOT_IDENTITY_PREIMAGE_KEYS:
        raise ValueError("root identity")
    return artifact_sha256(preimage)


def materialize_recovery_epoch003_reference_runtime(
    state: Mapping[str, Any],
) -> dict[str, Any] | tuple[str, ...]:
    """Materialize one fresh exact46 reference runtime without tests."""

    failure = (
        "RECOVERY_EPOCH003_REFERENCE_RUNTIME_MATERIALIZATION_INVALID",
    )
    destination: Path | None = None
    snapshot: Path | None = None
    destination_created = False
    snapshot_created = False
    try:
        (
            artifact_root,
            source_root,
            wheelhouse,
            destination,
            lock,
            lock_raw_sha256,
            policy,
        ) = _recovery_epoch003_load_materialization_inputs(state)
        snapshot = destination.parent / (
            destination.name
            + ".wheel-snapshot-"
            + secrets.token_hex(16)
        )
        if (
            snapshot.exists()
            or snapshot.is_symlink()
            or snapshot == destination
            or any(
                not _recovery_epoch003_paths_disjoint(
                    snapshot,
                    protected,
                )
                for protected in (
                    artifact_root,
                    source_root,
                    wheelhouse,
                )
            )
            or not _recovery_epoch003_paths_disjoint(
                snapshot,
                destination,
            )
        ):
            return failure
        os.mkdir(snapshot, 0o700)
        snapshot_created = True
        for row in lock["distributions"]:
            _recovery_epoch003_copy_wheel_nofollow(
                wheelhouse / row["wheel_filename"],
                snapshot / row["wheel_filename"],
            )
        if validate_recovery_epoch002_dependency_lock(
            lock,
            wheel_directory=snapshot,
        ):
            raise ValueError("snapshot")
        snapshot_entries = list(os.scandir(snapshot))
        if (
            len(snapshot_entries) != 46
            or {
                entry.name for entry in snapshot_entries
            }
            != {
                row["wheel_filename"] for row in lock["distributions"]
            }
            or any(
                entry.is_symlink()
                or not entry.is_file(follow_symlinks=False)
                or entry.stat(follow_symlinks=False).st_uid
                != os.geteuid()
                or entry.stat(follow_symlinks=False).st_nlink != 1
                or entry.stat(follow_symlinks=False).st_mode
                & (stat.S_IWUSR | stat.S_IWGRP | stat.S_IWOTH)
                for entry in snapshot_entries
            )
        ):
            raise ValueError("snapshot entries")
        os.chmod(snapshot, 0o500)
        os.mkdir(destination, 0o700)
        destination_created = True
        nonce = secrets.token_bytes(32)
        nonce_fd = os.open(
            destination / _RECOVERY_EPOCH003_ROOT_NONCE_FILE,
            os.O_WRONLY
            | os.O_CREAT
            | os.O_EXCL
            | getattr(os, "O_NOFOLLOW", 0),
            0o400,
        )
        try:
            os.write(nonce_fd, nonce)
            os.fsync(nonce_fd)
        finally:
            os.close(nonce_fd)
        environment = _recovery_epoch003_sanitized_environment(
            state["environment"]
        )
        subprocess.run(
            [
                sys.executable,
                "-I",
                "-B",
                "-m",
                "venv",
                "--without-pip",
                "--copies",
                str(destination),
            ],
            check=True,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=120,
            env=environment,
        )
        python_relative = (
            Path("Scripts/python.exe")
            if os.name == "nt"
            else Path("bin/python")
        )
        python_executable = destination / python_relative
        if (
            not python_executable.is_file()
            or python_executable.is_symlink()
            or not stat.S_ISREG(python_executable.lstat().st_mode)
        ):
            raise ValueError("runtime executable")
        requirements = destination / "locked-requirements.txt"
        requirements_payload = (
            "\n".join(lock["pip_require_hashes_lines"]) + "\n"
        ).encode("utf-8")
        requirements_fd = os.open(
            requirements,
            os.O_WRONLY
            | os.O_CREAT
            | os.O_EXCL
            | getattr(os, "O_NOFOLLOW", 0),
            0o400,
        )
        try:
            os.write(requirements_fd, requirements_payload)
            os.fsync(requirements_fd)
        finally:
            os.close(requirements_fd)
        subprocess.run(
            [
                sys.executable,
                "-I",
                "-B",
                "-m",
                "pip",
                "--python",
                str(python_executable),
                "install",
                "--isolated",
                "--no-index",
                "--no-cache-dir",
                "--require-hashes",
                "--only-binary=:all:",
                "--no-compile",
                f"--find-links={snapshot}",
                "--requirement",
                str(requirements),
            ],
            check=True,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            timeout=600,
            env=environment,
        )
        site_output = subprocess.run(
            [
                str(python_executable),
                "-I",
                "-B",
                "-c",
                (
                    "import json,sysconfig;"
                    "print(json.dumps(sysconfig.get_path('purelib')))"
                ),
            ],
            check=True,
            capture_output=True,
            text=True,
            timeout=30,
            env=environment,
        ).stdout
        installed_directory = Path(json.loads(site_output)).resolve()
        installed_relative = installed_directory.relative_to(destination)
        if validate_recovery_epoch002_dependency_lock(
            lock,
            wheel_directory=snapshot,
            installed_directory=installed_directory,
            runtime_root=destination,
        ):
            raise ValueError("installed closure")
        post_install_snapshot_entries = list(os.scandir(snapshot))
        if (
            len(post_install_snapshot_entries) != 46
            or {
                entry.name for entry in post_install_snapshot_entries
            }
            != {
                row["wheel_filename"] for row in lock["distributions"]
            }
            or any(
                entry.is_symlink()
                or not entry.is_file(follow_symlinks=False)
                or entry.stat(follow_symlinks=False).st_uid
                != os.geteuid()
                or entry.stat(follow_symlinks=False).st_nlink != 1
                or entry.stat(follow_symlinks=False).st_mode
                & (stat.S_IWUSR | stat.S_IWGRP | stat.S_IWOTH)
                for entry in post_install_snapshot_entries
            )
            or snapshot.stat().st_mode
            & (stat.S_IWUSR | stat.S_IWGRP | stat.S_IWOTH)
            or validate_recovery_epoch002_dependency_lock(
                lock,
                wheel_directory=snapshot,
            )
        ):
            raise ValueError("snapshot changed")
        runtime_identity, _stdlib, runtime_target = (
            _recovery_epoch003_runtime_probe(
                python_executable,
                environment=environment,
            )
        )
        target = lock["target"]
        if (
            runtime_identity["implementation"] != target["implementation"]
            or runtime_identity["version"] != target["python_version"]
            or runtime_target.get("system") != "Linux"
            or runtime_target.get("machine") != target["machine"]
            or runtime_target.get("abi_flags") != target["abi_flags"]
            or runtime_target.get("byte_order") != target["byte_order"]
            or runtime_target.get("python_cache_tag")
            != target["python_cache_tag"]
            or runtime_target.get("sys_platform") != "linux"
        ):
            raise ValueError("runtime target")
        installed = _recovery_epoch003_installed_identities(lock)
        pytest_identity = next(
            row
            for row in installed
            if row["normalized_distribution_name"] == "pytest"
        )
        installer_pip = subprocess.run(
            [
                sys.executable,
                "-I",
                "-B",
                "-m",
                "pip",
                "--version",
            ],
            check=True,
            capture_output=True,
            text=True,
            timeout=30,
            env=environment,
        ).stdout.split()
        runtime_pytest_version = subprocess.run(
            [
                str(python_executable),
                "-I",
                "-B",
                "-c",
                (
                    "import importlib.metadata as m;"
                    "print(m.version('pytest'))"
                ),
            ],
            check=True,
            capture_output=True,
            text=True,
            timeout=30,
            env=environment,
        ).stdout.strip()
        if (
            len(installer_pip) < 2
            or installer_pip[1] != "26.0.1"
            or runtime_pytest_version
            != pytest_identity["distribution_version"]
        ):
            raise ValueError("runtime distributions")
        wheel_manifest = [
            {
                "wheel_filename": row["wheel_filename"],
                "wheel_sha256": row["wheel_sha256"],
                "wheel_record_sha256": row["wheel_record_sha256"],
            }
            for row in lock["distributions"]
        ]
        wheel_bundle_hash = artifact_sha256(wheel_manifest)
        if (
            wheel_bundle_hash != _RECOVERY_EPOCH003_WHEEL_BUNDLE_SHA256
            or artifact_sha256(installed)
            != _RECOVERY_EPOCH003_INSTALLED_DISTRIBUTIONS_SHA256
        ):
            raise ValueError("frozen identity")
        root_identity = _recovery_epoch003_root_identity(
            root=destination,
            materialization_kind="REFERENCE",
            source_commit_sha1=state["expected_source_commit_sha1"],
            source_tree_sha1=state["expected_source_tree_sha1"],
            lock_raw_sha256=lock_raw_sha256,
            wheel_bundle_manifest_sha256=wheel_bundle_hash,
            installed_distributions=installed,
            python_runtime_identity=runtime_identity,
            pytest_distribution_identity=pytest_identity,
            environment_policy=policy,
        )
        materialization = {
            "schema_version": (
                "cocolon.emlis.nls_v3.recovery_epoch003."
                "runtime_materialization.v1"
            ),
            "runtime_root_identity_sha256": root_identity,
            "python_executable_relative_path": python_relative.as_posix(),
            "installed_directory_relative_path": (
                installed_relative.as_posix()
            ),
            "dependency_lock_raw_sha256": lock_raw_sha256,
            "wheel_bundle_manifest_sha256": wheel_bundle_hash,
            "distribution_count": 46,
            "runtime_materialization_state": (
                "VERIFIED_LOCKED_REFERENCE_RUNTIME"
            ),
            "body_free": True,
            "runtime_materialization_sha256": "",
        }
        materialization["runtime_materialization_sha256"] = _hash_without(
            materialization,
            "runtime_materialization_sha256",
        )
        return {
            "runtime_root": str(destination),
            "wheel_snapshot_root": str(snapshot),
            "runtime_materialization": materialization,
            "effective_environment_policy": policy,
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
        TypeError,
        UnicodeError,
        ValueError,
    ):
        if destination_created and destination is not None:
            shutil.rmtree(destination, ignore_errors=True)
        if snapshot_created and snapshot is not None:
            try:
                os.chmod(snapshot, 0o700)
                for entry in os.scandir(snapshot):
                    if entry.is_file(follow_symlinks=False):
                        os.chmod(entry.path, 0o600)
            except OSError:
                pass
            shutil.rmtree(snapshot, ignore_errors=True)
        return failure


def _recovery_epoch003_probe_materialization(
    request: Mapping[str, Any],
    result: Mapping[str, Any],
) -> tuple[
    dict[str, Any],
    list[dict[str, Any]],
    dict[str, Any],
    dict[str, Any],
] | None:
    try:
        (
            artifact_root,
            source_root,
            wheelhouse,
            destination,
            lock,
            lock_raw_sha256,
            policy,
        ) = _recovery_epoch003_load_materialization_inputs(
            request,
            allow_existing_destination=True,
        )
        if (
            type(result) is not dict
            or set(result) != _RECOVERY_EPOCH003_MATERIALIZATION_RESULT_KEYS
            or Path(result.get("runtime_root", "")).resolve()
            != destination
            or type(result.get("wheel_snapshot_root")) is not str
            or not result.get("wheel_snapshot_root")
            or result.get("effective_environment_policy") != policy
        ):
            return None
        raw_snapshot = Path(
            result["wheel_snapshot_root"]
        ).absolute()
        if _recovery_epoch003_path_has_symlink_component(raw_snapshot):
            return None
        snapshot = raw_snapshot.resolve()
        expected_wheel_names = {
            row["wheel_filename"] for row in lock["distributions"]
        }
        snapshot_entries = list(os.scandir(snapshot))
        if (
            not destination.is_dir()
            or not snapshot.is_dir()
            or not _recovery_epoch003_paths_disjoint(
                snapshot,
                destination,
            )
            or any(
                not _recovery_epoch003_paths_disjoint(
                    snapshot,
                    protected,
                )
                for protected in (
                    artifact_root,
                    source_root,
                    wheelhouse,
                )
            )
            or len(snapshot_entries) != 46
            or {
                entry.name for entry in snapshot_entries
            }
            != expected_wheel_names
            or any(
                entry.is_symlink()
                or not entry.is_file(follow_symlinks=False)
                or entry.stat(follow_symlinks=False).st_uid
                != os.geteuid()
                or entry.stat(follow_symlinks=False).st_nlink != 1
                or entry.stat(follow_symlinks=False).st_mode
                & (stat.S_IWUSR | stat.S_IWGRP | stat.S_IWOTH)
                for entry in snapshot_entries
            )
            or snapshot.stat().st_mode
            & (stat.S_IWUSR | stat.S_IWGRP | stat.S_IWOTH)
            or validate_recovery_epoch002_dependency_lock(
                lock,
                wheel_directory=snapshot,
            )
        ):
            return None
        materialization = result.get("runtime_materialization")
        if (
            not _recovery_epoch003_materialization_valid(
                materialization,
                dependency_lock_raw_sha256=lock_raw_sha256,
                wheel_bundle_manifest_sha256=(
                    _RECOVERY_EPOCH003_WHEEL_BUNDLE_SHA256
                ),
                distribution_count=46,
            )
            or materialization.get("runtime_materialization_state")
            != "VERIFIED_LOCKED_REFERENCE_RUNTIME"
        ):
            return None
        python_relative = Path(
            materialization["python_executable_relative_path"]
        )
        installed_relative = Path(
            materialization["installed_directory_relative_path"]
        )
        if (
            python_relative.is_absolute()
            or installed_relative.is_absolute()
            or ".." in python_relative.parts
            or ".." in installed_relative.parts
        ):
            return None
        python_executable = destination / python_relative
        installed_directory = destination / installed_relative
        if (
            not python_executable.is_file()
            or python_executable.is_symlink()
            or not stat.S_ISREG(python_executable.lstat().st_mode)
            or not installed_directory.is_dir()
            or installed_directory.is_symlink()
        ):
            return None
        if validate_recovery_epoch002_dependency_lock(
            lock,
            wheel_directory=snapshot,
            installed_directory=installed_directory,
            runtime_root=destination,
        ):
            return None
        environment = _recovery_epoch003_sanitized_environment(
            request["environment"]
        )
        runtime_identity, _stdlib, runtime_target = (
            _recovery_epoch003_runtime_probe(
                python_executable,
                environment=environment,
            )
        )
        installed = _recovery_epoch003_installed_identities(lock)
        pytest_identity = next(
            row
            for row in installed
            if row["normalized_distribution_name"] == "pytest"
        )
        installer_pip = subprocess.run(
            [
                sys.executable,
                "-I",
                "-B",
                "-m",
                "pip",
                "--version",
            ],
            check=True,
            capture_output=True,
            text=True,
            timeout=30,
            env=environment,
        ).stdout.split()
        runtime_pytest_version = subprocess.run(
            [
                str(python_executable),
                "-I",
                "-B",
                "-c",
                (
                    "import importlib.metadata as m;"
                    "print(m.version('pytest'))"
                ),
            ],
            check=True,
            capture_output=True,
            text=True,
            timeout=30,
            env=environment,
        ).stdout.strip()
        root_identity = _recovery_epoch003_root_identity(
            root=destination,
            materialization_kind="REFERENCE",
            source_commit_sha1=request["expected_source_commit_sha1"],
            source_tree_sha1=request["expected_source_tree_sha1"],
            lock_raw_sha256=lock_raw_sha256,
            wheel_bundle_manifest_sha256=(
                _RECOVERY_EPOCH003_WHEEL_BUNDLE_SHA256
            ),
            installed_distributions=installed,
            python_runtime_identity=runtime_identity,
            pytest_distribution_identity=pytest_identity,
            environment_policy=policy,
        )
        if (
            root_identity
            != materialization.get("runtime_root_identity_sha256")
            or artifact_sha256(installed)
            != _RECOVERY_EPOCH003_INSTALLED_DISTRIBUTIONS_SHA256
            or runtime_identity.get("implementation") != "CPYTHON"
            or runtime_identity.get("version") != "3.12.13"
            or runtime_target.get("system") != "Linux"
            or runtime_target.get("machine") != "x86_64"
            or runtime_target.get("abi_flags")
            != lock["target"]["abi_flags"]
            or runtime_target.get("byte_order")
            != lock["target"]["byte_order"]
            or runtime_target.get("python_cache_tag")
            != lock["target"]["python_cache_tag"]
            or runtime_target.get("sys_platform") != "linux"
            or len(installer_pip) < 2
            or installer_pip[1] != "26.0.1"
            or runtime_pytest_version
            != pytest_identity["distribution_version"]
        ):
            return None
        return runtime_identity, installed, pytest_identity, policy
    except (
        AttributeError,
        IndexError,
        KeyError,
        OSError,
        StopIteration,
        subprocess.SubprocessError,
        TypeError,
        UnicodeError,
        ValueError,
    ):
        return None


def build_recovery_epoch003_reference_runtime_observation(
    state: Mapping[str, Any],
) -> dict[str, Any] | tuple[str, ...]:
    """Freshly probe one materialized reference runtime into exact21."""

    failure = (
        "RECOVERY_EPOCH003_REFERENCE_RUNTIME_OBSERVATION_INVALID",
    )
    try:
        if (
            type(state) is not dict
            or set(state) != _RECOVERY_EPOCH003_REFERENCE_BUILD_KEYS
        ):
            return failure
        request = state.get("materialization_request")
        result = state.get("materialization_result")
        if (
            type(request) is not dict
            or request.get("authority_token")
            != _RECOVERY_EPOCH003_FINAL_ISSUANCE_AUTHORITY
        ):
            return failure
        probed = _recovery_epoch003_probe_materialization(request, result)
        if probed is None:
            return failure
        runtime_identity, installed, pytest_identity, policy = probed
        materialization = deepcopy(result["runtime_materialization"])
        reference = {
            "schema_version": RECOVERY_EPOCH003_REFERENCE_OBSERVATION_SCHEMA,
            "logical_cycle_id": "NLS_V3_CYCLE_001",
            "recovery_epoch_id": "NLS_V3_CYCLE001_RECOVERY_EPOCH_003",
            "authority_token": (
                _RECOVERY_EPOCH003_FINAL_ISSUANCE_AUTHORITY
            ),
            "source_commit_sha1": request[
                "expected_source_commit_sha1"
            ],
            "source_tree_sha1": request["expected_source_tree_sha1"],
            "dependency_lock_identity": {
                "identity_class": "EXACT_HASH_LOCK",
                "path": _RECOVERY_EPOCH003_LOCK_PATH,
                "raw_sha256": _RECOVERY_EPOCH003_LOCK_RAW_SHA256,
            },
            "wheel_bundle_manifest_sha256": (
                _RECOVERY_EPOCH003_WHEEL_BUNDLE_SHA256
            ),
            "runtime_materialization": materialization,
            "python_runtime_identity": runtime_identity,
            "pytest_distribution_identity": pytest_identity,
            "installed_distributions": installed,
            "installed_distributions_sha256": artifact_sha256(installed),
            "environment_policy": policy,
            "environment_policy_sha256": artifact_sha256(policy),
            "reservation_count_delta": 0,
            "formal_exact134_invocation_count": 0,
            "collection_state": "NOT_STARTED",
            "test_execution_state": "NOT_STARTED",
            "body_free": True,
            "reference_runtime_observation_sha256": "",
        }
        reference["reference_runtime_observation_sha256"] = _hash_without(
            reference,
            "reference_runtime_observation_sha256",
        )
        return reference
    except (
        AttributeError,
        KeyError,
        OSError,
        RecursionError,
        subprocess.SubprocessError,
        TypeError,
        UnicodeError,
        ValueError,
    ):
        return failure


def _main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Recovery Epoch002 read-only bootstrap preflight",
    )
    parser.add_argument("--preflight", action="store_true")
    args = parser.parse_args(argv)
    if args.preflight is not True:
        parser.error("--preflight is required")
    try:
        request = _read_preflight_cli_request()
        path_keys = (
            "repository_root",
            "dependency_lock_path",
            "wheel_directory",
            "locked_runtime_root",
            "attempt_registry_root",
        )
        if any(
            not isinstance(request.get(key), str) or not request.get(key)
            for key in path_keys
        ):
            raise ValueError("PREFLIGHT_REQUEST_PATH_INVALID")
        state = request["state"]
        attestation = (
            build_recovery_epoch002_operational_preflight_attestation(
                state,
                event1_artifact=request["event1_artifact"],
                event1_external_identity=request[
                    "event1_external_identity"
                ],
                event1_publication_state=request[
                    "event1_publication_state"
                ],
                repository_root=Path(request["repository_root"]),
                dependency_lock_path=Path(
                    request["dependency_lock_path"]
                ),
                wheel_directory=Path(request["wheel_directory"]),
                locked_runtime_root=Path(
                    request["locked_runtime_root"]
                ),
                attempt_registry_root=Path(
                    request["attempt_registry_root"]
                ),
            )
        )
        issues = ()
        readiness = (
            state.get("readiness_receipt")
            if type(state) is dict
            else None
        )
    except (
        json.JSONDecodeError,
        OSError,
        TypeError,
        UnicodeError,
        ValueError,
    ):
        issues = ("READINESS_FORBIDDEN",)
        readiness = None
        attestation = None
    result = _preflight_cli_result(
        issues=issues,
        readiness=readiness,
        attestation=attestation,
    )
    sys.stdout.buffer.write(canonical_json_bytes(result) + b"\n")
    return 0 if not issues else 2


__all__ = [
    "RECOVERY_EPOCH002_READINESS_SCHEMA",
    "RECOVERY_EPOCH002_READINESS_KEYS",
    "RECOVERY_EPOCH002_CONFTEST_PLUGIN_MODE",
    "RECOVERY_EPOCH002_FORMAL_PYTEST_OPTIONS",
    "RECOVERY_EPOCH002_FORMAL_PLUGIN_ALLOWLIST",
    "RECOVERY_EPOCH002_DEPENDENCY_LOCK_SCHEMA",
    "RECOVERY_EPOCH002_DEPENDENCY_LOCK_KEYS",
    "RECOVERY_EPOCH002_DEPENDENCY_LOCK_DISTRIBUTION_KEYS",
    "RECOVERY_EPOCH002_RUNTIME_MATERIALIZATION_KEYS",
    "RECOVERY_EPOCH002_OPERATIONAL_PREFLIGHT_ATTESTATION_KEYS",
    "validate_recovery_epoch002_bootstrap_state",
    "validate_recovery_epoch002_readiness_artifact",
    "validate_recovery_epoch002_operational_readiness_bindings",
    "build_recovery_epoch002_readiness_artifact",
    "validate_recovery_epoch002_event1_publication_binding",
    "validate_recovery_epoch002_dependency_lock",
    "load_recovery_epoch002_dependency_lock",
    "load_recovery_epoch002_dependency_lock_with_raw_sha256",
    "materialize_recovery_epoch002_locked_runtime",
    "validate_recovery_epoch002_operational_bootstrap_state",
    "build_recovery_epoch002_operational_preflight_attestation",
    "validate_recovery_epoch002_operational_preflight_attestation",
    "RECOVERY_EPOCH003_REFERENCE_OBSERVATION_SCHEMA",
    "RECOVERY_EPOCH003_OPERATIONAL_OBSERVATION_SCHEMA",
    "RECOVERY_EPOCH003_READINESS_SCHEMA",
    "RECOVERY_EPOCH003_FAILURE_SCHEMA",
    "RECOVERY_EPOCH003_FAILURE_CLASSES",
    "RECOVERY_EPOCH003_PREFLIGHT_STOP_CODE",
    "materialize_recovery_epoch003_reference_runtime",
    "build_recovery_epoch003_reference_runtime_observation",
    "evaluate_recovery_epoch003_preflight_contract",
    "execute_recovery_epoch003_current_strict_preflight_v1",
]


if __name__ == "__main__":
    raise SystemExit(_main())
