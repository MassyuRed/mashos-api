#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

"""Recovery Epoch 002 exact134 formal-worker boundary.

Import is inert.  The public runner requires explicit authorization, a
postverified reservation, a matching readiness receipt, and a pre-created
dependency lock.  The child persists monotonic body-free checkpoints and a
terminal result itself; the parent never invents collection or execution
facts when the child outcome is absent or ambiguous.
"""

import argparse
from copy import deepcopy
from datetime import datetime, timezone
import hashlib
from importlib import metadata
import json
import os
from pathlib import Path
import platform
import re
import stat
import subprocess
import sys
from typing import Any, Mapping, Sequence


_HERE = Path(__file__).resolve()
_REPO_ROOT = _HERE.parents[2]
_INFERENCE_ROOT = _REPO_ROOT / "ai" / "services" / "ai_inference"
_TOOLS_ROOT = _REPO_ROOT / "ai" / "tools"
for _import_root in (_INFERENCE_ROOT, _TOOLS_ROOT):
    if str(_import_root) not in sys.path:
        sys.path.insert(0, str(_import_root))

from emlis_ai_nls_v3_artifact_contract import artifact_sha256
from emlis_ai_recovery_epoch002_sequence_ledger_v3 import (
    validate_recovery_epoch002_reservation_artifact,
)
from emlis_ai_recovery_epoch002_canonical_current_closure_v3 import (
    validate_recovery_epoch002_bootstrap_manifest,
    validate_recovery_epoch002_formal_node_registry,
    validate_recovery_epoch002_operational_bootstrap_manifest,
    validate_recovery_epoch002_operational_source_manifest,
    validate_recovery_epoch002_source_closure,
)
from emlis_nls_v3_recovery_epoch002_closure_receipt_verify import (
    verify_recovery_epoch002_artifact_identity,
    verify_recovery_epoch002_published_artifact,
)
from emlis_nls_v3_recovery_epoch002_formal_worker_bootstrap_preflight import (
    RECOVERY_EPOCH002_FORMAL_PLUGIN_ALLOWLIST,
    RECOVERY_EPOCH002_FORMAL_PYTEST_OPTIONS,
    RECOVERY_EPOCH002_RUNTIME_MATERIALIZATION_KEYS,
    load_recovery_epoch002_dependency_lock_with_raw_sha256,
    validate_recovery_epoch002_dependency_lock,
    validate_recovery_epoch002_event1_publication_binding,
    validate_recovery_epoch002_operational_readiness_bindings,
    validate_recovery_epoch002_readiness_artifact,
)
from emlis_nls_v3_recovery_epoch002_formal_worker_evidence_v3 import (
    RECOVERY_EPOCH002_FORMAL_NODE_IDS,
    RECOVERY_EPOCH002_NEGATIVE_CLOSED_CODE_BY_NODE,
    validate_recovery_epoch002_attempt_state,
    validate_recovery_epoch002_checkpoint_chain,
    validate_recovery_epoch002_diagnostic,
    validate_recovery_epoch002_operational_terminal_result,
    validate_recovery_epoch002_success_terminal_state,
    validate_recovery_epoch002_unknown_disposition,
    write_recovery_epoch002_body_free_json_once,
)

RECOVERY_EPOCH002_REGISTERED_NEGATIVE_NODE_IDS = tuple(
    node_id
    for node_id in RECOVERY_EPOCH002_FORMAL_NODE_IDS
    if node_id in RECOVERY_EPOCH002_NEGATIVE_CLOSED_CODE_BY_NODE
)


RECOVERY_EPOCH002_CURRENT_STEP_PROOF_RUN_PROTOCOL = (
    "RECOVERY_EPOCH002_PYTEST_EXACT134_DURABLE_BODY_FREE_V1"
)
RECOVERY_EPOCH002_FORMAL_NODE_COUNT = 134
RECOVERY_EPOCH002_FORMAL_RUN_TIMEOUT_SECONDS = 3600
RECOVERY_EPOCH002_WORKER_ENVIRONMENT_FIXED = {
    "PYTEST_DISABLE_PLUGIN_AUTOLOAD": "1",
    "PYTHONDONTWRITEBYTECODE": "1",
    "PYTHONHASHSEED": "0",
    "PYTHONNOUSERSITE": "1",
    "PYTHONUTF8": "1",
}
RECOVERY_EPOCH002_WORKER_ENVIRONMENT_REMOVED = (
    "PYTHONHOME",
    "PYTHONPATH",
    "PYTEST_ADDOPTS",
    "PYTEST_PLUGINS",
)
RECOVERY_EPOCH002_RUN_CONTEXT_KEYS = frozenset(
    {
        "protocol",
        "repository_root",
        "source_commit_sha1",
        "source_tree_sha1",
        "logical_cycle_id",
        "recovery_epoch_id",
        "authority_token_id",
        "event1_challenge_id",
        "preflight_challenge_id",
        "formal_run_challenge_id",
        "formal_authority_challenge_id",
        "preflight_id",
        "attempt_id",
        "reservation_ordinal",
        "formal_test_run_reservation_sha256",
        "candidate_version_id",
        "source_baseline_event_sha256",
        "source_closure_sha256",
        "bootstrap_closure_sha256",
        "dependency_lock_relative_path",
        "dependency_lock_raw_sha256",
        "python_runtime_identity_sha256",
        "pytest_distribution_identity_sha256",
        "environment_profile",
        "environment_profile_sha256",
        "formal_test_node_ids",
        "authority_grant_sha256",
        "readiness_identity_sha256",
        "reservation_identity_sha256",
        "invocation_claim_sha256",
        "parent_checkpoint_sha256",
        "body_free",
        "run_context_sha256",
    }
)
RECOVERY_EPOCH002_FORMAL_AUTHORITY_GRANT_KEYS = frozenset(
    {
        "schema_version",
        "logical_cycle_id",
        "recovery_epoch_id",
        "candidate_version_id",
        "attempt_id",
        "formal_run_challenge_id",
        "readiness_identity_sha256",
        "reservation_identity_sha256",
        "formal_exact134_authorized",
        "automatic_progression",
        "body_free",
        "authority_grant_sha256",
    }
)
RECOVERY_EPOCH002_INVOCATION_CLAIM_KEYS = frozenset(
    {
        "schema_version",
        "attempt_id",
        "authority_grant_sha256",
        "readiness_identity_sha256",
        "reservation_identity_sha256",
        "source_commit_sha1",
        "source_tree_sha1",
        "created_at_utc",
        "automatic_retry",
        "body_free",
        "invocation_claim_sha256",
    }
)

_FORMAL_CHECKPOINT_SCHEMA = (
    "cocolon.emlis.nls_v3.recovery_epoch002.formal_worker_checkpoint.v1"
)
_TERMINAL_RESULT_SCHEMA = (
    "cocolon.emlis.nls_v3.recovery_epoch002."
    "formal_worker_terminal_result.v1"
)
_SHA1_RE = re.compile(r"^[0-9a-f]{40}$")
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_NODE_RE = re.compile(r"^ai/tests/[^:\n]+\.py::[^:\n]+(?:::[^:\n]+)*$")
_FORMAL_RUNNER_RELATIVE_PATH = (
    "ai/tools/"
    "emlis_nls_v3_recovery_epoch002_current_step_proof_run.py"
)
_PREFLIGHT_RELATIVE_PATH = (
    "ai/tools/"
    "emlis_nls_v3_recovery_epoch002_formal_worker_bootstrap_preflight.py"
)


def _utc_now_seconds() -> str:
    return (
        datetime.now(timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )


def _hash_without(value: Mapping[str, Any], key: str) -> str:
    material = deepcopy(dict(value))
    material.pop(key, None)
    return artifact_sha256(material)


def _read_regular_bytes(
    path: Path,
    *,
    maximum_bytes: int = 128 * 1024 * 1024,
) -> bytes:
    flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0)
    descriptor = os.open(path, flags)
    try:
        file_stat = os.fstat(descriptor)
        if not stat.S_ISREG(file_stat.st_mode):
            raise ValueError("expected a regular non-symlink file")
        chunks: list[bytes] = []
        total = 0
        while True:
            chunk = os.read(descriptor, 1024 * 1024)
            if not chunk:
                break
            total += len(chunk)
            if total > maximum_bytes:
                raise ValueError("regular file exceeds the closed size limit")
            chunks.append(chunk)
        return b"".join(chunks)
    finally:
        os.close(descriptor)


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    digest.update(_read_regular_bytes(path))
    return digest.hexdigest()


def _canonical_existing_child(root: Path, relative_text: Any) -> Path:
    if not isinstance(relative_text, str) or not relative_text:
        raise ValueError("FORMAL_RUNTIME_MATERIALIZATION_INVALID")
    relative = Path(relative_text)
    if (
        relative.is_absolute()
        or relative.as_posix() != relative_text
        or any(part in {"", ".", ".."} for part in relative.parts)
    ):
        raise ValueError("FORMAL_RUNTIME_MATERIALIZATION_INVALID")
    target = (root / relative).absolute()
    try:
        target.relative_to(root)
    except ValueError as exc:
        raise ValueError(
            "FORMAL_RUNTIME_MATERIALIZATION_INVALID"
        ) from exc
    current = root
    for component in relative.parts:
        current = current / component
        try:
            current_stat = current.lstat()
        except OSError as exc:
            raise ValueError(
                "FORMAL_RUNTIME_MATERIALIZATION_INVALID"
            ) from exc
        if stat.S_ISLNK(current_stat.st_mode):
            raise ValueError("FORMAL_RUNTIME_MATERIALIZATION_INVALID")
    return target


def _verify_manifest_source_files(
    repository_root: Path,
    manifest: Mapping[str, Any],
    dependency_lock: Mapping[str, Any],
    stdlib_module_names: frozenset[str],
) -> None:
    if validate_recovery_epoch002_operational_source_manifest(
        repository_root,
        manifest,
        dependency_lock,
        stdlib_module_names,
    ):
        raise ValueError("FORMAL_SOURCE_IMPORT_CLOSURE_MISMATCH")


def _read_regular_json(path: Path) -> dict[str, Any]:
    flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0)
    try:
        descriptor = os.open(path, flags)
    except OSError as exc:
        raise ValueError(
            "formal worker input must be a regular non-symlink file"
        ) from exc
    try:
        file_stat = os.fstat(descriptor)
        if (
            not stat.S_ISREG(file_stat.st_mode)
            or file_stat.st_uid != os.getuid()
        ):
            raise ValueError("formal worker input owner/type is invalid")
        chunks: list[bytes] = []
        total = 0
        while True:
            chunk = os.read(descriptor, 1024 * 1024)
            if not chunk:
                break
            total += len(chunk)
            if total > 32 * 1024 * 1024:
                raise ValueError("formal worker input is too large")
            chunks.append(chunk)
    finally:
        os.close(descriptor)

    def reject_duplicates(
        pairs: list[tuple[str, Any]],
    ) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in pairs:
            if key in result:
                raise ValueError("duplicate formal worker JSON key")
            result[key] = value
        return result

    value = json.loads(
        b"".join(chunks).decode("utf-8"),
        object_pairs_hook=reject_duplicates,
        parse_constant=lambda value: (_ for _ in ()).throw(
            ValueError(f"non-finite JSON number: {value}")
        ),
    )
    if type(value) is not dict:
        raise ValueError("formal worker input root must be an object")
    return value


def _formal_nodes_valid(nodes: Any) -> bool:
    return (
        type(nodes) is list
        and len(nodes) == RECOVERY_EPOCH002_FORMAL_NODE_COUNT
        and len(nodes) == len(set(nodes))
        and all(
            isinstance(node, str) and _NODE_RE.fullmatch(node) is not None
            for node in nodes
        )
    )


def _worker_environment() -> dict[str, str]:
    return {
        "PATH": os.defpath,
        "LANG": "C.UTF-8",
        "LC_ALL": "C.UTF-8",
        **RECOVERY_EPOCH002_WORKER_ENVIRONMENT_FIXED,
    }


def _environment_profile(environment: Mapping[str, str]) -> dict[str, Any]:
    return {
        "fixed": dict(sorted(RECOVERY_EPOCH002_WORKER_ENVIRONMENT_FIXED.items())),
        "removed": list(RECOVERY_EPOCH002_WORKER_ENVIRONMENT_REMOVED),
        "inherited_path_sha256": hashlib.sha256(
            environment.get("PATH", "").encode("utf-8")
        ).hexdigest(),
        "lang": environment.get("LANG"),
        "lc_all": environment.get("LC_ALL"),
    }


def _python_runtime_identity() -> dict[str, Any]:
    executable = Path(sys.executable)
    build = {
        "python_build": list(platform.python_build()),
        "python_compiler": platform.python_compiler(),
        "platform": platform.platform(),
        "abi_flags": sys.abiflags,
    }
    return {
        "executable_sha256": _sha256_file(executable),
        "implementation": platform.python_implementation().upper(),
        "version": platform.python_version(),
        "build_sha256": artifact_sha256(build),
    }


def _python_runtime_identity_for(
    python_executable: Path,
) -> dict[str, Any]:
    probe = (
        "import json,platform,sys;"
        "print(json.dumps({"
        "'python_build':list(platform.python_build()),"
        "'python_compiler':platform.python_compiler(),"
        "'platform':platform.platform(),"
        "'abi_flags':sys.abiflags,"
        "'implementation':platform.python_implementation().upper(),"
        "'version':platform.python_version()"
        "},sort_keys=True))"
    )
    observed = json.loads(
        subprocess.run(
            [str(python_executable), "-I", "-B", "-c", probe],
            check=True,
            capture_output=True,
            text=True,
            timeout=30,
        ).stdout
    )
    build = {
        "python_build": observed["python_build"],
        "python_compiler": observed["python_compiler"],
        "platform": observed["platform"],
        "abi_flags": observed["abi_flags"],
    }
    return {
        "executable_sha256": _sha256_file(python_executable),
        "implementation": observed["implementation"],
        "version": observed["version"],
        "build_sha256": artifact_sha256(build),
    }


def _stdlib_module_names_for(
    python_executable: Path,
) -> frozenset[str]:
    output = subprocess.run(
        [
            str(python_executable),
            "-I",
            "-B",
            "-c",
            (
                "import json,sys;"
                "print(json.dumps(sorted(sys.stdlib_module_names)))"
            ),
        ],
        check=True,
        capture_output=True,
        text=True,
        timeout=30,
    ).stdout
    value = json.loads(output)
    if (
        type(value) is not list
        or any(not isinstance(item, str) or not item for item in value)
        or value != sorted(set(value))
    ):
        raise ValueError("PYTHON_STDLIB_IDENTITY_INVALID")
    return frozenset(value)


def _pytest_distribution_identity(
    lock: Mapping[str, Any],
) -> dict[str, Any]:
    row = next(
        (
            item
            for item in lock["distributions"]
            if item["normalized_distribution_name"] == "pytest"
        ),
        None,
    )
    if row is None:
        raise ValueError("DEPENDENCY_LOCK_INVALID")
    if metadata.version("pytest") != row["distribution_version"]:
        raise ValueError("PYTEST_RUNTIME_IDENTITY_MISMATCH")
    return {
        "normalized_distribution_name": "pytest",
        "distribution_version": row["distribution_version"],
        "wheel_sha256": row["wheel_sha256"],
        "installed_record_closure_sha256": row[
            "installed_record_closure_sha256"
        ],
    }


def _locked_pytest_identity(lock: Mapping[str, Any]) -> dict[str, Any]:
    row = next(
        (
            item
            for item in lock["distributions"]
            if item["normalized_distribution_name"] == "pytest"
        ),
        None,
    )
    if row is None:
        raise ValueError("DEPENDENCY_LOCK_INVALID")
    return {
        "normalized_distribution_name": "pytest",
        "distribution_version": row["distribution_version"],
        "wheel_sha256": row["wheel_sha256"],
        "installed_record_closure_sha256": row[
            "installed_record_closure_sha256"
        ],
    }


def build_recovery_epoch002_formal_worker_argv(
    *,
    python_executable: Path,
    runner_path: Path,
    context_path: Path,
    evidence_directory: Path,
) -> tuple[str, ...]:
    """Return the inert, isolated child argv."""

    return (
        str(python_executable),
        "-I",
        "-B",
        str(runner_path),
        "--internal-exact134-child",
        "--context",
        str(context_path),
        "--evidence-directory",
        str(evidence_directory),
        *RECOVERY_EPOCH002_FORMAL_PYTEST_OPTIONS,
    )


def _formal_worker_argv_template() -> list[str]:
    return [
        "python",
        "-I",
        "-B",
        _FORMAL_RUNNER_RELATIVE_PATH,
        "--internal-exact134-child",
        *RECOVERY_EPOCH002_FORMAL_PYTEST_OPTIONS,
    ]


def _preflight_argv_template() -> list[str]:
    return [
        "python",
        "-I",
        "-B",
        _PREFLIGHT_RELATIVE_PATH,
        "--preflight",
    ]


def _normalize_actual_formal_worker_argv(
    argv: Sequence[str],
    *,
    repository_root: Path,
    python_executable: Path,
    context_path: Path,
    evidence_directory: Path,
) -> list[str]:
    runner_path = repository_root / _FORMAL_RUNNER_RELATIVE_PATH
    expected = build_recovery_epoch002_formal_worker_argv(
        python_executable=python_executable,
        runner_path=runner_path,
        context_path=context_path,
        evidence_directory=evidence_directory,
    )
    if tuple(argv) != expected:
        raise ValueError("FORMAL_WORKER_ARGV_MISMATCH")
    return _formal_worker_argv_template()


def _checkpoint_base(context: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "schema_version": _FORMAL_CHECKPOINT_SCHEMA,
        "phase": "FORMAL_RUN",
        "logical_cycle_id": context["logical_cycle_id"],
        "recovery_epoch_id": context["recovery_epoch_id"],
        "authority_token_id": context["authority_token_id"],
        "event1_challenge_id": context["event1_challenge_id"],
        "preflight_challenge_id": context["preflight_challenge_id"],
        "formal_run_challenge_id": context["formal_run_challenge_id"],
        "formal_authority_challenge_id": context[
            "formal_authority_challenge_id"
        ],
        "preflight_id": context["preflight_id"],
        "attempt_id": context["attempt_id"],
        "reservation_ordinal": context["reservation_ordinal"],
        "formal_test_run_reservation_sha256": context[
            "formal_test_run_reservation_sha256"
        ],
        "candidate_version_id": context["candidate_version_id"],
        "source_baseline_event_sha256": context[
            "source_baseline_event_sha256"
        ],
        "source_closure_sha256": context["source_closure_sha256"],
        "bootstrap_closure_sha256": context["bootstrap_closure_sha256"],
    }


def _build_checkpoint(
    context: Mapping[str, Any],
    *,
    ordinal: int,
    stage: str,
    prior_checkpoint_sha256: str | None,
) -> dict[str, Any]:
    checkpoint = {
        **_checkpoint_base(context),
        "checkpoint_ordinal": ordinal,
        "stage_enum": stage,
        "observed_at_utc": _utc_now_seconds(),
        "prior_checkpoint_sha256": prior_checkpoint_sha256,
        "body_free": True,
        "checkpoint_sha256": "",
    }
    checkpoint["checkpoint_sha256"] = _hash_without(
        checkpoint,
        "checkpoint_sha256",
    )
    return checkpoint


class _CheckpointWriter:
    def __init__(
        self,
        *,
        context: Mapping[str, Any],
        directory: Path,
        ordinal: int,
        prior_hash: str | None,
    ) -> None:
        self._context = context
        self._directory = directory
        self._ordinal = ordinal
        self._prior_hash = prior_hash
        self.last_stage: str | None = None

    def persist(self, stage: str) -> dict[str, Any]:
        checkpoint = _build_checkpoint(
            self._context,
            ordinal=self._ordinal,
            stage=stage,
            prior_checkpoint_sha256=self._prior_hash,
        )
        filename = (
            f"checkpoint-{self._ordinal:03d}-"
            f"{stage.lower().replace('_', '-')}.json"
        )
        write_recovery_epoch002_body_free_json_once(
            self._directory,
            filename,
            checkpoint,
        )
        self._ordinal += 1
        self._prior_hash = checkpoint["checkpoint_sha256"]
        self.last_stage = stage
        return checkpoint


class _BodyFreePytestCapture:
    """First-party recorder; third-party plugin autoload remains disabled."""

    _ALLOWED_STATES = {
        "PASSED",
        "FAILED",
        "SKIPPED",
        "XFAILED",
        "XPASSED",
    }

    def __init__(
        self,
        checkpoints: _CheckpointWriter,
        *,
        expected_nodes: Sequence[str],
    ) -> None:
        self.checkpoints = checkpoints
        self.expected_nodes = list(expected_nodes)
        self.collected: list[str] = []
        self.executed: list[str] = []
        self.states: dict[str, str] = {}
        self.collection_errors = 0
        self._execution_started = False

    def pytest_collection(self, session: Any) -> None:
        self.checkpoints.persist("COLLECTION_STARTED")

    def pytest_collectreport(self, report: Any) -> None:
        if getattr(report, "failed", False):
            self.collection_errors += 1

    def pytest_collection_finish(self, session: Any) -> None:
        self.collected = [item.nodeid for item in session.items]
        stage = "COLLECTION_FINISHED"
        if (
            self.collection_errors
            or self.collected != self.expected_nodes
        ):
            stage = "COLLECTION_FAILED"
            if self.collected != self.expected_nodes:
                self.collection_errors += 1
            session.items[:] = []
        self.checkpoints.persist(stage)

    def pytest_runtest_logstart(self, nodeid: str, location: Any) -> None:
        if not self._execution_started:
            self.checkpoints.persist("EXECUTION_STARTED")
            self._execution_started = True
        if nodeid not in self.executed:
            self.executed.append(nodeid)

    def pytest_runtest_logreport(self, report: Any) -> None:
        nodeid = report.nodeid
        if report.failed:
            self.states[nodeid] = "FAILED"
            return
        if report.skipped:
            self.states[nodeid] = (
                "XFAILED" if hasattr(report, "wasxfail") else "SKIPPED"
            )
            return
        if report.when == "call":
            if report.passed:
                state = "XPASSED" if hasattr(report, "wasxfail") else "PASSED"
            else:
                state = "SKIPPED"
            self.states[nodeid] = state

    def close_execution(self) -> bool:
        if self.checkpoints.last_stage == "COLLECTION_FAILED":
            return True
        if not self._execution_started:
            return False
        self.checkpoints.persist("EXECUTION_FINISHED")
        return True


def _validate_run_context(context: Mapping[str, Any]) -> None:
    if type(context) is not dict or set(context) != RECOVERY_EPOCH002_RUN_CONTEXT_KEYS:
        raise ValueError("FORMAL_WORKER_CONTEXT_INVALID")
    if (
        context.get("protocol")
        != RECOVERY_EPOCH002_CURRENT_STEP_PROOF_RUN_PROTOCOL
        or context.get("body_free") is not True
        or context.get("run_context_sha256")
        != _hash_without(context, "run_context_sha256")
        or type(context.get("environment_profile")) is not dict
        or artifact_sha256(context["environment_profile"])
        != context.get("environment_profile_sha256")
        or not _formal_nodes_valid(context.get("formal_test_node_ids"))
        or type(context.get("reservation_ordinal")) is not int
        or type(context.get("reservation_ordinal")) is bool
        or context.get("reservation_ordinal", 0) <= 0
    ):
        raise ValueError("FORMAL_WORKER_CONTEXT_INVALID")
    for key in (
        "source_commit_sha1",
        "source_tree_sha1",
    ):
        if _SHA1_RE.fullmatch(str(context.get(key, ""))) is None:
            raise ValueError("FORMAL_WORKER_CONTEXT_INVALID")
    for key in (
        "event1_challenge_id",
        "preflight_challenge_id",
        "formal_run_challenge_id",
        "formal_authority_challenge_id",
        "authority_token_id",
        "preflight_id",
        "attempt_id",
        "formal_test_run_reservation_sha256",
        "source_baseline_event_sha256",
        "source_closure_sha256",
        "bootstrap_closure_sha256",
        "dependency_lock_raw_sha256",
        "python_runtime_identity_sha256",
        "pytest_distribution_identity_sha256",
        "environment_profile_sha256",
        "authority_grant_sha256",
        "readiness_identity_sha256",
        "reservation_identity_sha256",
        "invocation_claim_sha256",
        "parent_checkpoint_sha256",
    ):
        if _SHA256_RE.fullmatch(str(context.get(key, ""))) is None:
            raise ValueError("FORMAL_WORKER_CONTEXT_INVALID")


def _git_identity(repo_root: Path) -> tuple[str, str, bool]:
    def run(*args: str) -> str:
        return subprocess.run(
            ["git", *args],
            cwd=repo_root,
            check=True,
            capture_output=True,
            text=True,
            timeout=10,
        ).stdout.strip()

    commit = run("rev-parse", "HEAD")
    tree = run("rev-parse", "HEAD^{tree}")
    clean = run("status", "--porcelain", "--untracked-files=all") == ""
    return commit, tree, clean


def _validate_authority_grant(
    grant: Mapping[str, Any],
    *,
    reservation: Mapping[str, Any],
    readiness_identity: Mapping[str, Any],
    reservation_identity: Mapping[str, Any],
) -> None:
    if (
        type(grant) is not dict
        or set(grant) != RECOVERY_EPOCH002_FORMAL_AUTHORITY_GRANT_KEYS
        or grant.get("schema_version")
        != (
            "cocolon.emlis.nls_v3.recovery_epoch002."
            "formal_exact134_authority_grant.v1"
        )
        or grant.get("logical_cycle_id")
        != reservation.get("logical_cycle_id")
        or grant.get("recovery_epoch_id")
        != reservation.get("recovery_epoch_id")
        or grant.get("candidate_version_id")
        != reservation.get("candidate_version_id")
        or grant.get("attempt_id") != reservation.get("attempt_id")
        or grant.get("formal_run_challenge_id")
        != reservation.get("challenge_id")
        or grant.get("readiness_identity_sha256")
        != readiness_identity.get("identity_sha256")
        or grant.get("reservation_identity_sha256")
        != reservation_identity.get("identity_sha256")
        or grant.get("formal_exact134_authorized") is not True
        or grant.get("automatic_progression") is not False
        or grant.get("body_free") is not True
        or grant.get("authority_grant_sha256")
        != _hash_without(grant, "authority_grant_sha256")
    ):
        raise PermissionError("FORMAL_EXACT134_NOT_AUTHORIZED")


def _claim_published_reservation_attempt(
    *,
    authority_grant: Mapping[str, Any],
    reservation: Mapping[str, Any],
    readiness: Mapping[str, Any],
    readiness_external_identity: Mapping[str, Any],
    reservation_external_identity: Mapping[str, Any],
    readiness_publication_state: Mapping[str, Any],
    reservation_publication_state: Mapping[str, Any],
    attempt_registry_root: Path,
) -> tuple[Path, dict[str, Any]]:
    """Claim a postverified reservation before fallible local admission."""

    if validate_recovery_epoch002_reservation_artifact(reservation):
        raise ValueError("RUN_RESERVATION_INVALID")
    if validate_recovery_epoch002_readiness_artifact(readiness):
        raise ValueError("READINESS_FORBIDDEN")
    if verify_recovery_epoch002_artifact_identity(
        readiness_external_identity
    ) or verify_recovery_epoch002_artifact_identity(
        reservation_external_identity
    ):
        raise ValueError("FORMAL_PUBLICATION_IDENTITY_INVALID")
    if (
        readiness_publication_state.get("artifact") != readiness
        or readiness_publication_state.get("artifact_external_identity")
        != readiness_external_identity
        or reservation_publication_state.get("artifact") != reservation
        or reservation_publication_state.get("artifact_external_identity")
        != reservation_external_identity
        or verify_recovery_epoch002_published_artifact(
            readiness_publication_state
        )
        or verify_recovery_epoch002_published_artifact(
            reservation_publication_state
        )
    ):
        raise ValueError("FORMAL_PUBLICATION_POSTVERIFICATION_INVALID")
    _validate_authority_grant(
        authority_grant,
        reservation=reservation,
        readiness_identity=readiness_external_identity,
        reservation_identity=reservation_external_identity,
    )

    supplied_registry_root = attempt_registry_root.absolute()
    try:
        registry_root = attempt_registry_root.resolve(strict=True)
        registry_stat = registry_root.lstat()
    except OSError as exc:
        raise ValueError("FORMAL_ATTEMPT_REGISTRY_INVALID") from exc
    if (
        registry_root != supplied_registry_root
        or not stat.S_ISDIR(registry_stat.st_mode)
        or registry_root.is_symlink()
        or registry_stat.st_uid != os.getuid()
        or stat.S_IMODE(registry_stat.st_mode) != 0o700
    ):
        raise ValueError("FORMAL_ATTEMPT_REGISTRY_INVALID")

    attempt_id = reservation["attempt_id"]
    directory = registry_root / attempt_id
    try:
        os.mkdir(directory, mode=0o700)
    except FileExistsError as exc:
        raise PermissionError("FORMAL_ATTEMPT_ALREADY_CLAIMED") from exc

    source_closure = reservation["source_closure"]
    checkpoint_context = {
        "logical_cycle_id": reservation["logical_cycle_id"],
        "recovery_epoch_id": reservation["recovery_epoch_id"],
        "authority_token_id": artifact_sha256(
            {"authority_token": reservation["authority_token"]}
        ),
        "event1_challenge_id": reservation["event1_challenge_id"],
        "preflight_challenge_id": reservation["preflight_challenge_id"],
        "formal_run_challenge_id": reservation["challenge_id"],
        "formal_authority_challenge_id": reservation[
            "authority_challenge_id"
        ],
        "preflight_id": readiness["preflight_id"],
        "attempt_id": attempt_id,
        "reservation_ordinal": reservation["reservation_ordinal"],
        "formal_test_run_reservation_sha256": reservation[
            "formal_test_run_reservation_sha256"
        ],
        "candidate_version_id": reservation["candidate_version_id"],
        "source_baseline_event_sha256": reservation[
            "source_baseline_event"
        ]["logical_artifact_sha256"],
        "source_closure_sha256": source_closure[
            "source_closure_sha256"
        ],
        "bootstrap_closure_sha256": source_closure[
            "bootstrap_closure_sha256"
        ],
    }
    parent_checkpoint = _build_checkpoint(
        checkpoint_context,
        ordinal=1,
        stage="PARENT_SPAWN_INTENT_PERSISTED",
        prior_checkpoint_sha256=None,
    )
    write_recovery_epoch002_body_free_json_once(
        directory,
        "checkpoint-001-parent-spawn-intent-persisted.json",
        parent_checkpoint,
    )
    return directory, parent_checkpoint


def _validate_operational_admission(
    *,
    authority_grant: Mapping[str, Any],
    event1_artifact: Mapping[str, Any],
    event1_external_identity: Mapping[str, Any],
    event1_publication_state: Mapping[str, Any],
    reservation: Mapping[str, Any],
    readiness: Mapping[str, Any],
    readiness_external_identity: Mapping[str, Any],
    reservation_external_identity: Mapping[str, Any],
    readiness_publication_state: Mapping[str, Any],
    reservation_publication_state: Mapping[str, Any],
    formal_test_node_ids: Sequence[str],
    repository_root: Path,
    dependency_lock_path: Path,
    wheel_directory: Path,
    locked_runtime_root: Path,
    attempt_registry_root: Path,
) -> tuple[
    Path,
    Path,
    dict[str, Any],
    Path,
    Path,
    Path,
    list[str],
]:
    if validate_recovery_epoch002_reservation_artifact(reservation):
        raise ValueError("RUN_RESERVATION_INVALID")
    if validate_recovery_epoch002_readiness_artifact(readiness):
        raise ValueError("READINESS_FORBIDDEN")
    if verify_recovery_epoch002_artifact_identity(
        readiness_external_identity
    ) or verify_recovery_epoch002_artifact_identity(
        reservation_external_identity
    ):
        raise ValueError("FORMAL_PUBLICATION_IDENTITY_INVALID")
    if (
        readiness_publication_state.get("artifact") != readiness
        or readiness_publication_state.get("artifact_external_identity")
        != readiness_external_identity
        or reservation_publication_state.get("artifact") != reservation
        or reservation_publication_state.get("artifact_external_identity")
        != reservation_external_identity
        or verify_recovery_epoch002_published_artifact(
            readiness_publication_state
        )
        or verify_recovery_epoch002_published_artifact(
            reservation_publication_state
        )
    ):
        raise ValueError("FORMAL_PUBLICATION_POSTVERIFICATION_INVALID")
    _validate_authority_grant(
        authority_grant,
        reservation=reservation,
        readiness_identity=readiness_external_identity,
        reservation_identity=reservation_external_identity,
    )

    manifest = readiness.get("bootstrap_closure")
    source_closure = reservation.get("source_closure")
    nodes = list(formal_test_node_ids)
    if (
        validate_recovery_epoch002_bootstrap_manifest(manifest)
        or validate_recovery_epoch002_operational_readiness_bindings(
            readiness,
            manifest,
            expected_receipt_path=readiness_external_identity.get("path"),
        )
        or validate_recovery_epoch002_event1_publication_binding(
            event1_artifact=event1_artifact,
            event1_external_identity=event1_external_identity,
            event1_publication_state=event1_publication_state,
            readiness=readiness,
        )
        or validate_recovery_epoch002_source_closure(source_closure)
        or validate_recovery_epoch002_formal_node_registry(
            repository_root,
            manifest,
            source_closure,
        )
        or not _formal_nodes_valid(nodes)
        or nodes != manifest.get("formal_test_node_ids")
        or readiness.get("candidate_version_id")
        != reservation.get("candidate_version_id")
        or readiness.get("logical_cycle_id")
        != reservation.get("logical_cycle_id")
        or readiness.get("recovery_epoch_id")
        != reservation.get("recovery_epoch_id")
        or readiness.get("event1_challenge_id")
        != reservation.get("event1_challenge_id")
        or readiness.get("preflight_challenge_id")
        != reservation.get("preflight_challenge_id")
        or readiness.get("source_baseline_event")
        != reservation.get("source_baseline_event")
        or readiness.get("source_closure") != source_closure
        or readiness.get("authority_token")
        != reservation.get("authority_token")
        or readiness.get("bootstrap_readiness_receipt_sha256")
        is None
        or reservation.get("bootstrap_readiness_artifact")
        != readiness_external_identity
        or source_closure.get("bootstrap_closure_sha256")
        != manifest.get("bootstrap_closure_sha256")
        or source_closure.get("formal_test_manifest_sha256")
        != manifest.get("formal_test_manifest_sha256")
        or readiness.get("python_runtime_identity")
        != manifest.get("python_runtime_identity")
        or readiness.get("pytest_distribution_identity")
        != manifest.get("pytest_distribution_identity")
        or readiness.get("dependency_lock_identity")
        != manifest.get("dependency_lock_identity")
        or readiness.get("environment_profile")
        != manifest.get("environment_profile")
        or manifest.get("source_commit_sha1")
        != source_closure.get("source_commit_sha1")
        or manifest.get("source_tree_sha1")
        != source_closure.get("source_tree_sha1")
        or reservation.get("formal_node_registry_sha256")
        != source_closure.get("formal_node_registry_sha256")
    ):
        raise ValueError("FORMAL_ADMISSION_BINDING_INVALID")
    preflight_preimage = {
        "logical_cycle_id": readiness["logical_cycle_id"],
        "recovery_epoch_id": readiness["recovery_epoch_id"],
        "candidate_version_id": readiness["candidate_version_id"],
        "authority_token": readiness["authority_token"],
        "event1_challenge_id": readiness["event1_challenge_id"],
        "preflight_challenge_id": readiness["preflight_challenge_id"],
        "source_baseline_event_identity_sha256": readiness[
            "source_baseline_event"
        ]["identity_sha256"],
        "source_closure_sha256": source_closure["source_closure_sha256"],
        "bootstrap_closure_sha256": manifest["bootstrap_closure_sha256"],
    }
    if readiness.get("preflight_id") != artifact_sha256(preflight_preimage):
        raise ValueError("FORMAL_PREFLIGHT_IDENTITY_INVALID")

    if (
        reservation_publication_state.get(
            "ready_receipt_marked_consumed"
        )
        is not True
        or reservation_publication_state.get(
            "authoritative_reservation_presence"
        )
        != "PRESENT"
        or readiness_external_identity.get("path")
        == reservation_external_identity.get("path")
    ):
        raise ValueError("FORMAL_READINESS_IMMEDIATE_BASE_INVALID")

    root = repository_root.absolute()
    if repository_root.is_symlink() or not root.is_dir():
        raise ValueError("FORMAL_SOURCE_BINDING_INVALID")
    lock_path = dependency_lock_path.absolute()
    if dependency_lock_path.is_symlink() or not lock_path.is_file():
        raise ValueError("DEPENDENCY_LOCK_PATH_INVALID")
    try:
        lock_relative = lock_path.relative_to(root).as_posix()
    except ValueError as exc:
        raise ValueError("DEPENDENCY_LOCK_PATH_INVALID") from exc
    lock_identity = manifest["dependency_lock_identity"]
    if lock_relative != lock_identity.get("path"):
        raise ValueError("DEPENDENCY_LOCK_RAW_IDENTITY_MISMATCH")
    lock, lock_raw_sha256 = (
        load_recovery_epoch002_dependency_lock_with_raw_sha256(lock_path)
    )
    if lock_raw_sha256 != lock_identity.get("raw_sha256"):
        raise ValueError("DEPENDENCY_LOCK_RAW_IDENTITY_MISMATCH")
    if validate_recovery_epoch002_operational_bootstrap_manifest(
        manifest,
        lock,
    ):
        raise ValueError("FORMAL_BOOTSTRAP_MANIFEST_INVALID")
    if (
        manifest.get("preflight_argv") != _preflight_argv_template()
        or manifest.get("formal_worker_argv")
        != _formal_worker_argv_template()
    ):
        raise ValueError("FORMAL_WORKER_ARGV_MISMATCH")

    runtime_root = locked_runtime_root.absolute()
    registry_root = attempt_registry_root.absolute()
    for path in (runtime_root, registry_root, wheel_directory):
        path_stat = path.lstat()
        if (
            not stat.S_ISDIR(path_stat.st_mode)
            or path.is_symlink()
            or path_stat.st_uid != os.getuid()
        ):
            raise ValueError("FORMAL_RUNTIME_PATH_INVALID")
    registry_stat = registry_root.lstat()
    if stat.S_IMODE(registry_stat.st_mode) != 0o700:
        raise ValueError("FORMAL_ATTEMPT_REGISTRY_INVALID")

    environment_profile = manifest["environment_profile"]
    materialization = environment_profile.get(
        "locked_runtime_materialization"
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
        != lock_identity["raw_sha256"]
        or materialization.get("distribution_count")
        != lock.get("distribution_count")
        or materialization.get("wheel_bundle_manifest_sha256")
        != artifact_sha256(
            [
                {
                    "wheel_filename": row["wheel_filename"],
                    "wheel_sha256": row["wheel_sha256"],
                    "wheel_record_sha256": row["wheel_record_sha256"],
                }
                for row in lock["distributions"]
            ]
        )
        or environment_profile.get(
            "attempt_registry_root_identity_sha256"
        )
        != artifact_sha256({"attempt_registry_root": str(registry_root)})
    ):
        raise ValueError("FORMAL_RUNTIME_MATERIALIZATION_INVALID")
    python_executable = _canonical_existing_child(
        runtime_root,
        materialization["python_executable_relative_path"],
    )
    installed_directory = _canonical_existing_child(
        runtime_root,
        materialization["installed_directory_relative_path"],
    )
    if (
        python_executable.is_symlink()
        or not python_executable.is_file()
        or installed_directory.is_symlink()
        or not installed_directory.is_dir()
        or validate_recovery_epoch002_dependency_lock(
            lock,
            wheel_directory=wheel_directory,
            installed_directory=installed_directory,
            runtime_root=runtime_root,
        )
    ):
        raise ValueError("FORMAL_RUNTIME_MATERIALIZATION_INVALID")
    runtime_identity = _python_runtime_identity_for(python_executable)
    stdlib_module_names = _stdlib_module_names_for(python_executable)
    _verify_manifest_source_files(
        root,
        manifest,
        lock,
        stdlib_module_names,
    )
    pytest_identity = _locked_pytest_identity(lock)
    if (
        runtime_identity != manifest.get("python_runtime_identity")
        or pytest_identity != manifest.get("pytest_distribution_identity")
    ):
        raise ValueError("FORMAL_RUNTIME_IDENTITY_MISMATCH")
    expected_environment = manifest["environment_profile"]
    if any(
        expected_environment.get(key) != value
        for key, value in _environment_profile(
            _worker_environment()
        ).items()
    ):
        raise ValueError("FORMAL_ENVIRONMENT_PROFILE_MISMATCH")

    return (
        root,
        lock_path,
        lock,
        python_executable,
        installed_directory,
        registry_root,
        nodes,
    )


def _build_terminal_result(
    *,
    context: Mapping[str, Any],
    capture: _BodyFreePytestCapture,
    terminal_checkpoint_sha256: str,
    exit_code: int,
    started_at_utc: str,
    finished_at_utc: str,
) -> dict[str, Any]:
    result: dict[str, Any] = {
        "schema_version": _TERMINAL_RESULT_SCHEMA,
        "logical_cycle_id": context["logical_cycle_id"],
        "recovery_epoch_id": context["recovery_epoch_id"],
        "authority_token_id": context["authority_token_id"],
        "event1_challenge_id": context["event1_challenge_id"],
        "formal_run_challenge_id": context["formal_run_challenge_id"],
        "formal_authority_challenge_id": context[
            "formal_authority_challenge_id"
        ],
        "attempt_id": context["attempt_id"],
        "candidate_version_id": context["candidate_version_id"],
        "source_baseline_event_sha256": context[
            "source_baseline_event_sha256"
        ],
        "source_closure_sha256": context["source_closure_sha256"],
        "bootstrap_closure_sha256": context["bootstrap_closure_sha256"],
        "formal_test_run_reservation_sha256": context[
            "formal_test_run_reservation_sha256"
        ],
        "terminal_checkpoint_sha256": terminal_checkpoint_sha256,
        "collection_node_ids": list(capture.collected),
        "executed_node_ids": list(capture.executed),
        "states": dict(capture.states),
        "collection_errors": capture.collection_errors,
        "exit_class": "EXITED",
        "exit_code": exit_code,
        "signal_number": None,
        "timed_out": False,
        "python_runtime_identity_sha256": context[
            "python_runtime_identity_sha256"
        ],
        "pytest_distribution_identity_sha256": context[
            "pytest_distribution_identity_sha256"
        ],
        "started_at_utc": started_at_utc,
        "finished_at_utc": finished_at_utc,
        "body_free": True,
        "formal_worker_result_sha256": "",
    }
    result["formal_worker_result_sha256"] = _hash_without(
        result,
        "formal_worker_result_sha256",
    )
    return result


def _internal_exact134_child(
    *,
    context_path: Path,
    evidence_directory: Path,
    forwarded_pytest_options: Sequence[str],
) -> int:
    context = _read_regular_json(context_path)
    _validate_run_context(context)
    directory_stat = evidence_directory.lstat()
    if (
        not stat.S_ISDIR(directory_stat.st_mode)
        or evidence_directory.is_symlink()
        or stat.S_IMODE(directory_stat.st_mode) != 0o700
        or directory_stat.st_uid != os.getuid()
    ):
        raise ValueError("FORMAL_EVIDENCE_DIRECTORY_INVALID")
    claim = _read_regular_json(
        evidence_directory / "invocation-claim.json"
    )
    if (
        set(claim) != RECOVERY_EPOCH002_INVOCATION_CLAIM_KEYS
        or claim.get("schema_version")
        != (
            "cocolon.emlis.nls_v3.recovery_epoch002."
            "formal_exact134_invocation_claim.v1"
        )
        or claim.get("attempt_id") != context.get("attempt_id")
        or claim.get("authority_grant_sha256")
        != context.get("authority_grant_sha256")
        or claim.get("readiness_identity_sha256")
        != context.get("readiness_identity_sha256")
        or claim.get("reservation_identity_sha256")
        != context.get("reservation_identity_sha256")
        or claim.get("source_commit_sha1")
        != context.get("source_commit_sha1")
        or claim.get("source_tree_sha1")
        != context.get("source_tree_sha1")
        or claim.get("automatic_retry") is not False
        or claim.get("body_free") is not True
        or claim.get("invocation_claim_sha256")
        != _hash_without(claim, "invocation_claim_sha256")
        or claim.get("invocation_claim_sha256")
        != context.get("invocation_claim_sha256")
    ):
        raise ValueError("FORMAL_INVOCATION_CLAIM_INVALID")
    if tuple(forwarded_pytest_options) != RECOVERY_EPOCH002_FORMAL_PYTEST_OPTIONS:
        raise ValueError("FORMAL_PYTEST_OPTIONS_INVALID")
    if RECOVERY_EPOCH002_FORMAL_PLUGIN_ALLOWLIST:
        raise ValueError("FORMAL_PLUGIN_ALLOWLIST_INVALID")

    checkpoints = _CheckpointWriter(
        context=context,
        directory=evidence_directory,
        ordinal=2,
        prior_hash=context["parent_checkpoint_sha256"],
    )
    checkpoints.persist("CHILD_PROCESS_ENTRY")

    repo_root = Path(context["repository_root"]).resolve()
    commit, tree, clean = _git_identity(repo_root)
    if (
        commit != context["source_commit_sha1"]
        or tree != context["source_tree_sha1"]
        or clean is not True
    ):
        raise ValueError("FORMAL_SOURCE_BINDING_INVALID")
    checkpoints.persist("SOURCE_BINDING_VALIDATED")

    lock_path = repo_root / context["dependency_lock_relative_path"]
    lock, lock_raw_sha256 = (
        load_recovery_epoch002_dependency_lock_with_raw_sha256(lock_path)
    )
    if lock_raw_sha256 != context["dependency_lock_raw_sha256"]:
        raise ValueError("DEPENDENCY_LOCK_RAW_IDENTITY_MISMATCH")
    installed_root = Path(
        metadata.distribution("pytest").locate_file("")
    ).resolve()
    if validate_recovery_epoch002_dependency_lock(
        lock,
        installed_directory=installed_root,
        runtime_root=Path(sys.prefix),
    ):
        raise ValueError("DEPENDENCY_LOCK_INSTALLED_CLOSURE_MISMATCH")
    runtime_identity = _python_runtime_identity()
    if artifact_sha256(runtime_identity) != context[
        "python_runtime_identity_sha256"
    ]:
        raise ValueError("PYTHON_RUNTIME_IDENTITY_MISMATCH")
    checkpoints.persist("RUNTIME_PROFILE_VALIDATED")

    import pytest

    pytest_identity = _pytest_distribution_identity(lock)
    if artifact_sha256(pytest_identity) != context[
        "pytest_distribution_identity_sha256"
    ]:
        raise ValueError("PYTEST_RUNTIME_IDENTITY_MISMATCH")
    checkpoints.persist("PYTEST_IMPORT_VALIDATED")

    environment = _worker_environment()
    observed_environment = _environment_profile(environment)
    expected_environment = context["environment_profile"]
    if (
        any(
            expected_environment.get(key) != value
            for key, value in observed_environment.items()
        )
        or artifact_sha256(expected_environment)
        != context["environment_profile_sha256"]
    ):
        raise ValueError("FORMAL_ENVIRONMENT_PROFILE_MISMATCH")

    capture = _BodyFreePytestCapture(
        checkpoints,
        expected_nodes=context["formal_test_node_ids"],
    )
    checkpoints.persist("FORMAL_PLUGIN_BOOTSTRAP_VALIDATED")
    checkpoints.persist("PYTEST_MAIN_ENTERING")

    started_at_utc = _utc_now_seconds()
    exit_code = int(
        pytest.main(
            [
                *context["formal_test_node_ids"],
                *RECOVERY_EPOCH002_FORMAL_PYTEST_OPTIONS,
            ],
            plugins=[capture],
        )
    )
    if capture.close_execution() is not True:
        return 2
    finished_at_utc = _utc_now_seconds()

    terminal_checkpoint = _build_checkpoint(
        context,
        ordinal=checkpoints._ordinal,
        stage="TERMINAL_RESULT_PERSISTED",
        prior_checkpoint_sha256=checkpoints._prior_hash,
    )
    terminal_result = _build_terminal_result(
        context=context,
        capture=capture,
        terminal_checkpoint_sha256=terminal_checkpoint["checkpoint_sha256"],
        exit_code=exit_code,
        started_at_utc=started_at_utc,
        finished_at_utc=finished_at_utc,
    )
    if validate_recovery_epoch002_operational_terminal_result(
        terminal_result
    ):
        raise ValueError("FORMAL_TERMINAL_RESULT_INVALID")
    write_recovery_epoch002_body_free_json_once(
        evidence_directory,
        "formal-worker-terminal-result.json",
        terminal_result,
    )
    write_recovery_epoch002_body_free_json_once(
        evidence_directory,
        (
            f"checkpoint-{checkpoints._ordinal:03d}-"
            "terminal-result-persisted.json"
        ),
        terminal_checkpoint,
    )
    return 0


def _load_checkpoint_prefix(
    directory: Path,
) -> tuple[list[dict[str, Any]], str]:
    paths = sorted(directory.glob("checkpoint-*.json"))
    if not paths:
        return [], "ABSENT"
    prefix: list[dict[str, Any]] = []
    for path in paths:
        try:
            row = _read_regular_json(path)
        except (OSError, UnicodeError, ValueError, json.JSONDecodeError):
            return prefix, "INVALID"
        candidate = [*prefix, row]
        if validate_recovery_epoch002_checkpoint_chain(
            candidate,
            allow_prefix=True,
        ):
            return prefix, "INVALID"
        prefix.append(row)
    if prefix[-1].get("stage_enum") == "TERMINAL_RESULT_PERSISTED":
        return prefix, "VALID"
    return prefix, "VALID_PREFIX"


def _reconcile_terminal_evidence(
    *,
    directory: Path,
) -> tuple[
    dict[str, Any] | None,
    list[dict[str, Any]],
    str,
    str,
]:
    checkpoints, checkpoint_status = _load_checkpoint_prefix(directory)
    terminal_path = directory / "formal-worker-terminal-result.json"
    terminal_present = os.path.lexists(terminal_path)
    if checkpoint_status == "INVALID":
        return (
            None,
            checkpoints,
            checkpoint_status,
            "INVALID" if terminal_present else "ABSENT",
        )
    if not terminal_present:
        if checkpoint_status == "VALID":
            checkpoint_status = "INVALID"
        return None, checkpoints, checkpoint_status, "ABSENT"
    try:
        result = _read_regular_json(terminal_path)
    except (OSError, UnicodeError, ValueError, json.JSONDecodeError):
        return None, checkpoints, checkpoint_status, "INVALID"
    if (
        checkpoint_status != "VALID"
        or validate_recovery_epoch002_checkpoint_chain(
            checkpoints,
            allow_prefix=False,
        )
        or validate_recovery_epoch002_operational_terminal_result(result)
        or result.get("terminal_checkpoint_sha256")
        != checkpoints[-1].get("checkpoint_sha256")
        or any(
            result.get(name) != checkpoints[-1].get(name)
            for name in (
                "logical_cycle_id",
                "recovery_epoch_id",
                "authority_token_id",
                "event1_challenge_id",
                "formal_run_challenge_id",
                "formal_authority_challenge_id",
                "attempt_id",
                "candidate_version_id",
                "source_baseline_event_sha256",
                "source_closure_sha256",
                "bootstrap_closure_sha256",
                "formal_test_run_reservation_sha256",
            )
        )
    ):
        return None, checkpoints, "INVALID", "INVALID"
    return result, checkpoints, "VALID", "VALID"


def _persist_unknown_disposition(
    *,
    directory: Path,
    reservation_identity: Mapping[str, Any],
    reservation: Mapping[str, Any],
    preflight_id: str,
    checkpoints: Sequence[Mapping[str, Any]],
    checkpoint_status: str,
    terminal_status: str,
    exit_class: str,
    exit_code: int | None,
    signal_number: int | None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    last_stage = (
        checkpoints[-1].get("stage_enum") if checkpoints else None
    )
    diagnostic: dict[str, Any] = {
        "schema_version": (
            "cocolon.emlis.nls_v3.recovery_epoch002."
            "formal_worker_diagnostic.v1"
        ),
        "logical_cycle_id": reservation["logical_cycle_id"],
        "recovery_epoch_id": reservation["recovery_epoch_id"],
        "authority_token_id": artifact_sha256(
            {"authority_token": reservation["authority_token"]}
        ),
        "event1_challenge_id": reservation["event1_challenge_id"],
        "preflight_challenge_id": reservation["preflight_challenge_id"],
        "formal_run_challenge_id": reservation["challenge_id"],
        "formal_authority_challenge_id": reservation[
            "authority_challenge_id"
        ],
        "preflight_id": preflight_id,
        "attempt_id": reservation["attempt_id"],
        "reservation_ordinal": reservation["reservation_ordinal"],
        "process_start_observed": exit_class != "SPAWN_FAILED",
        "exit_class": exit_class,
        "exit_code": exit_code,
        "signal_number": signal_number,
        "checkpoint_status": checkpoint_status,
        "last_valid_stage": last_stage,
        "terminal_result_status": terminal_status,
        "valid_result_identity_sha256": None,
        "stop_code": "ATTEMPT_CONSUMPTION_UNKNOWN_STOP",
        "body_free": True,
        "diagnostic_sha256": "",
    }
    diagnostic["diagnostic_sha256"] = _hash_without(
        diagnostic,
        "diagnostic_sha256",
    )
    disposition: dict[str, Any] = {
        "schema_version": (
            "cocolon.emlis.nls_v3.recovery_epoch002."
            "attempt_consumption_unknown_disposition.v1"
        ),
        "reservation_artifact": dict(reservation_identity),
        "attempt_id": reservation["attempt_id"],
        "checkpoint_status": checkpoint_status,
        "last_valid_stage": last_stage,
        "terminal_result_status": terminal_status,
        "exit_class": exit_class,
        "exit_code": exit_code,
        "signal_number": signal_number,
        "stop_code": "ATTEMPT_CONSUMPTION_UNKNOWN_STOP",
        "automatic_retry": False,
        "body_free": True,
        "attempt_consumption_unknown_disposition_sha256": "",
    }
    disposition[
        "attempt_consumption_unknown_disposition_sha256"
    ] = _hash_without(
        disposition,
        "attempt_consumption_unknown_disposition_sha256",
    )
    if validate_recovery_epoch002_diagnostic(diagnostic):
        raise ValueError("DIAGNOSTIC_INVALID")
    if validate_recovery_epoch002_unknown_disposition(disposition):
        raise ValueError("UNKNOWN_DISPOSITION_INVALID")
    write_recovery_epoch002_body_free_json_once(
        directory,
        "formal-worker-diagnostic.json",
        diagnostic,
    )
    write_recovery_epoch002_body_free_json_once(
        directory,
        "attempt-consumption-unknown-disposition.json",
        disposition,
    )
    return diagnostic, disposition


def _persist_valid_terminal_diagnostic(
    *,
    directory: Path,
    reservation: Mapping[str, Any],
    readiness: Mapping[str, Any],
    terminal: Mapping[str, Any],
    checkpoints: Sequence[Mapping[str, Any]],
) -> dict[str, Any]:
    diagnostic: dict[str, Any] = {
        "schema_version": (
            "cocolon.emlis.nls_v3.recovery_epoch002."
            "formal_worker_diagnostic.v1"
        ),
        "logical_cycle_id": reservation["logical_cycle_id"],
        "recovery_epoch_id": reservation["recovery_epoch_id"],
        "authority_token_id": artifact_sha256(
            {"authority_token": reservation["authority_token"]}
        ),
        "event1_challenge_id": reservation["event1_challenge_id"],
        "preflight_challenge_id": reservation["preflight_challenge_id"],
        "formal_run_challenge_id": reservation["challenge_id"],
        "formal_authority_challenge_id": reservation[
            "authority_challenge_id"
        ],
        "preflight_id": readiness["preflight_id"],
        "attempt_id": reservation["attempt_id"],
        "reservation_ordinal": reservation["reservation_ordinal"],
        "process_start_observed": True,
        "exit_class": terminal["exit_class"],
        "exit_code": terminal["exit_code"],
        "signal_number": terminal["signal_number"],
        "checkpoint_status": "VALID",
        "last_valid_stage": checkpoints[-1]["stage_enum"],
        "terminal_result_status": "VALID",
        "valid_result_identity_sha256": terminal[
            "formal_worker_result_sha256"
        ],
        "stop_code": (
            "RESULT_DURABLY_PRESENT_TERMINAL_PUBLICATION_PENDING_STOP"
        ),
        "body_free": True,
        "diagnostic_sha256": "",
    }
    diagnostic["diagnostic_sha256"] = _hash_without(
        diagnostic,
        "diagnostic_sha256",
    )
    if validate_recovery_epoch002_diagnostic(diagnostic):
        raise ValueError("DIAGNOSTIC_INVALID")
    write_recovery_epoch002_body_free_json_once(
        directory,
        "formal-worker-diagnostic.json",
        diagnostic,
    )
    return diagnostic


def _attempt_state(
    *,
    exit_class: str,
    exit_code: int | None,
    signal_number: int | None,
    checkpoints: list[dict[str, Any]],
    checkpoint_status: str,
    terminal_status: str,
    terminal: dict[str, Any] | None,
    diagnostic: dict[str, Any],
    unknown_disposition: dict[str, Any] | None,
) -> dict[str, Any]:
    return {
        "reservation_published_and_postverified": True,
        "parent_spawn_intent_persisted": bool(checkpoints),
        "child_process_created": exit_class != "SPAWN_FAILED",
        "exit_class": exit_class,
        "exit_code": exit_code,
        "signal_number": signal_number,
        "timed_out": exit_class == "TIMED_OUT",
        "checkpoint_status": checkpoint_status,
        "checkpoint_chain": checkpoints,
        "terminal_result_status": terminal_status,
        "terminal_result": terminal,
        "terminal_result_publication_succeeded": False,
        "same_attempt_rerun_requested": False,
        "synthetic_collection_observation": False,
        "multiple_run_results_ranked": False,
        "earlier_consumed_lineage_dropped": False,
        "diagnostics": diagnostic,
        "unknown_disposition": unknown_disposition,
    }


def _close_claimed_attempt_unknown(
    *,
    directory: Path,
    reservation_identity: Mapping[str, Any],
    reservation: Mapping[str, Any],
    readiness: Mapping[str, Any],
    exit_class: str,
    exit_code: int | None = None,
    signal_number: int | None = None,
) -> dict[str, Any]:
    (
        terminal,
        checkpoints,
        checkpoint_status,
        terminal_status,
    ) = _reconcile_terminal_evidence(directory=directory)
    if terminal_status == "VALID" and terminal is not None:
        diagnostic = _persist_valid_terminal_diagnostic(
            directory=directory,
            reservation=reservation,
            readiness=readiness,
            terminal=terminal,
            checkpoints=checkpoints,
        )
        state = _attempt_state(
            exit_class=terminal["exit_class"],
            exit_code=terminal["exit_code"],
            signal_number=terminal["signal_number"],
            checkpoints=checkpoints,
            checkpoint_status="VALID",
            terminal_status="VALID",
            terminal=terminal,
            diagnostic=diagnostic,
            unknown_disposition=None,
        )
    else:
        diagnostic, disposition = _persist_unknown_disposition(
            directory=directory,
            reservation_identity=reservation_identity,
            reservation=reservation,
            preflight_id=readiness["preflight_id"],
            checkpoints=checkpoints,
            checkpoint_status=checkpoint_status,
            terminal_status=terminal_status,
            exit_class=exit_class,
            exit_code=exit_code,
            signal_number=signal_number,
        )
        state = _attempt_state(
            exit_class=exit_class,
            exit_code=exit_code,
            signal_number=signal_number,
            checkpoints=checkpoints,
            checkpoint_status=checkpoint_status,
            terminal_status=terminal_status,
            terminal=None,
            diagnostic=diagnostic,
            unknown_disposition=disposition,
        )
    issues = validate_recovery_epoch002_attempt_state(state)
    if issues not in {
        (),
        ("ATTEMPT_CONSUMPTION_UNKNOWN_STOP",),
        (
            "RESULT_DURABLY_PRESENT_TERMINAL_PUBLICATION_PENDING_STOP",
        ),
    }:
        raise ValueError(issues[0])
    return state


def _run_recovery_epoch002_current_step_proof_impl(
    *,
    authority_grant: Mapping[str, Any],
    event1_artifact: Mapping[str, Any],
    event1_external_identity: Mapping[str, Any],
    event1_publication_state: Mapping[str, Any],
    reservation: Mapping[str, Any],
    readiness: Mapping[str, Any],
    readiness_external_identity: Mapping[str, Any],
    reservation_external_identity: Mapping[str, Any],
    readiness_publication_state: Mapping[str, Any],
    reservation_publication_state: Mapping[str, Any],
    formal_test_node_ids: Sequence[str],
    repository_root: Path,
    dependency_lock_path: Path,
    wheel_directory: Path,
    locked_runtime_root: Path,
    attempt_registry_root: Path,
    claimed_directory: Path,
    parent_checkpoint: Mapping[str, Any],
    timeout_seconds: int = RECOVERY_EPOCH002_FORMAL_RUN_TIMEOUT_SECONDS,
) -> dict[str, Any]:
    """Validate and spawn one already-claimed published attempt."""

    if type(timeout_seconds) is not int or timeout_seconds <= 0:
        raise ValueError("FORMAL_TIMEOUT_INVALID")
    (
        root,
        lock_path,
        lock,
        python_executable,
        _installed_directory,
        registry_root,
        nodes,
    ) = _validate_operational_admission(
        authority_grant=authority_grant,
        event1_artifact=event1_artifact,
        event1_external_identity=event1_external_identity,
        event1_publication_state=event1_publication_state,
        reservation=reservation,
        readiness=readiness,
        readiness_external_identity=readiness_external_identity,
        reservation_external_identity=reservation_external_identity,
        readiness_publication_state=readiness_publication_state,
        reservation_publication_state=reservation_publication_state,
        formal_test_node_ids=formal_test_node_ids,
        repository_root=repository_root,
        dependency_lock_path=dependency_lock_path,
        wheel_directory=wheel_directory,
        locked_runtime_root=locked_runtime_root,
        attempt_registry_root=attempt_registry_root,
    )
    manifest = readiness["bootstrap_closure"]
    commit, tree, clean = _git_identity(root)
    source_closure = reservation["source_closure"]
    if (
        clean is not True
        or source_closure["source_commit_sha1"] != commit
        or source_closure["source_tree_sha1"] != tree
    ):
        raise ValueError("FORMAL_SOURCE_BINDING_INVALID")

    attempt_id = reservation["attempt_id"]
    if _SHA256_RE.fullmatch(attempt_id) is None:
        raise ValueError("FORMAL_ATTEMPT_ID_INVALID")
    directory = claimed_directory
    if (
        directory != registry_root / attempt_id
        or directory.is_symlink()
        or not directory.is_dir()
        or validate_recovery_epoch002_checkpoint_chain(
            [dict(parent_checkpoint)]
        )
        or _read_regular_json(
            directory
            / "checkpoint-001-parent-spawn-intent-persisted.json"
        )
        != parent_checkpoint
    ):
        raise ValueError("FORMAL_ATTEMPT_CLAIM_INVALID")
    predicted_context_path = directory / "formal-worker-context.json"
    predicted_runner_path = root / _FORMAL_RUNNER_RELATIVE_PATH
    predicted_argv = build_recovery_epoch002_formal_worker_argv(
        python_executable=python_executable,
        runner_path=predicted_runner_path,
        context_path=predicted_context_path,
        evidence_directory=directory,
    )
    if (
        _normalize_actual_formal_worker_argv(
            predicted_argv,
            repository_root=root,
            python_executable=python_executable,
            context_path=predicted_context_path,
            evidence_directory=directory,
        )
        != manifest["formal_worker_argv"]
    ):
        raise ValueError("FORMAL_WORKER_ARGV_MISMATCH")
    claim: dict[str, Any] = {
        "schema_version": (
            "cocolon.emlis.nls_v3.recovery_epoch002."
            "formal_exact134_invocation_claim.v1"
        ),
        "attempt_id": attempt_id,
        "authority_grant_sha256": authority_grant[
            "authority_grant_sha256"
        ],
        "readiness_identity_sha256": readiness_external_identity[
            "identity_sha256"
        ],
        "reservation_identity_sha256": reservation_external_identity[
            "identity_sha256"
        ],
        "source_commit_sha1": commit,
        "source_tree_sha1": tree,
        "created_at_utc": _utc_now_seconds(),
        "automatic_retry": False,
        "body_free": True,
        "invocation_claim_sha256": "",
    }
    claim["invocation_claim_sha256"] = _hash_without(
        claim,
        "invocation_claim_sha256",
    )
    write_recovery_epoch002_body_free_json_once(
        directory,
        "invocation-claim.json",
        claim,
    )

    runtime_identity = _python_runtime_identity_for(python_executable)
    pytest_identity = _locked_pytest_identity(lock)
    environment = _worker_environment()
    environment_profile = manifest["environment_profile"]
    observed_environment = _environment_profile(environment)
    if any(
        environment_profile.get(key) != value
        for key, value in observed_environment.items()
    ):
        raise ValueError("FORMAL_ENVIRONMENT_PROFILE_MISMATCH")
    context: dict[str, Any] = {
        "protocol": RECOVERY_EPOCH002_CURRENT_STEP_PROOF_RUN_PROTOCOL,
        "repository_root": str(root),
        "source_commit_sha1": commit,
        "source_tree_sha1": tree,
        "logical_cycle_id": reservation["logical_cycle_id"],
        "recovery_epoch_id": reservation["recovery_epoch_id"],
        "authority_token_id": artifact_sha256(
            {"authority_token": reservation["authority_token"]}
        ),
        "event1_challenge_id": reservation["event1_challenge_id"],
        "preflight_challenge_id": reservation["preflight_challenge_id"],
        "formal_run_challenge_id": reservation["challenge_id"],
        "formal_authority_challenge_id": reservation[
            "authority_challenge_id"
        ],
        "preflight_id": readiness["preflight_id"],
        "attempt_id": attempt_id,
        "reservation_ordinal": reservation["reservation_ordinal"],
        "formal_test_run_reservation_sha256": reservation[
            "formal_test_run_reservation_sha256"
        ],
        "candidate_version_id": reservation["candidate_version_id"],
        "source_baseline_event_sha256": reservation[
            "source_baseline_event"
        ]["logical_artifact_sha256"],
        "source_closure_sha256": source_closure["source_closure_sha256"],
        "bootstrap_closure_sha256": source_closure[
            "bootstrap_closure_sha256"
        ],
        "dependency_lock_relative_path": lock_path.relative_to(root).as_posix(),
        "dependency_lock_raw_sha256": manifest[
            "dependency_lock_identity"
        ]["raw_sha256"],
        "python_runtime_identity_sha256": artifact_sha256(runtime_identity),
        "pytest_distribution_identity_sha256": artifact_sha256(
            pytest_identity
        ),
        "environment_profile": deepcopy(environment_profile),
        "environment_profile_sha256": artifact_sha256(
            environment_profile
        ),
        "formal_test_node_ids": nodes,
        "authority_grant_sha256": authority_grant[
            "authority_grant_sha256"
        ],
        "readiness_identity_sha256": readiness_external_identity[
            "identity_sha256"
        ],
        "reservation_identity_sha256": reservation_external_identity[
            "identity_sha256"
        ],
        "invocation_claim_sha256": claim["invocation_claim_sha256"],
        "parent_checkpoint_sha256": "",
        "body_free": True,
        "run_context_sha256": "",
    }
    if (
        runtime_identity != manifest["python_runtime_identity"]
        or pytest_identity != manifest["pytest_distribution_identity"]
    ):
        raise ValueError("FORMAL_RUNTIME_IDENTITY_MISMATCH")
    context["parent_checkpoint_sha256"] = parent_checkpoint[
        "checkpoint_sha256"
    ]
    context["run_context_sha256"] = _hash_without(
        context,
        "run_context_sha256",
    )
    _validate_run_context(context)
    context_path = write_recovery_epoch002_body_free_json_once(
        directory,
        "formal-worker-context.json",
        context,
    )
    runner_path = root / _FORMAL_RUNNER_RELATIVE_PATH
    argv = build_recovery_epoch002_formal_worker_argv(
        python_executable=python_executable,
        runner_path=runner_path,
        context_path=context_path,
        evidence_directory=directory,
    )
    if (
        _normalize_actual_formal_worker_argv(
            argv,
            repository_root=root,
            python_executable=python_executable,
            context_path=context_path,
            evidence_directory=directory,
        )
        != manifest["formal_worker_argv"]
    ):
        raise ValueError("FORMAL_WORKER_ARGV_MISMATCH")
    exit_class = "SPAWN_FAILED"
    exit_code: int | None = None
    signal_number: int | None = None
    try:
        completed = subprocess.run(
            argv,
            cwd=root,
            env=environment,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False,
            timeout=timeout_seconds,
        )
        if completed.returncode < 0:
            exit_class = "SIGNALED"
            signal_number = -completed.returncode
        else:
            exit_class = "EXITED"
            exit_code = completed.returncode
    except subprocess.TimeoutExpired:
        exit_class = "TIMED_OUT"
    except OSError:
        exit_class = "SPAWN_FAILED"

    return _close_claimed_attempt_unknown(
        directory=directory,
        reservation_identity=reservation_external_identity,
        reservation=reservation,
        readiness=readiness,
        exit_class=exit_class,
        exit_code=exit_code,
        signal_number=signal_number,
    )


def run_recovery_epoch002_current_step_proof(
    *,
    authority_grant: Mapping[str, Any],
    event1_artifact: Mapping[str, Any],
    event1_external_identity: Mapping[str, Any],
    event1_publication_state: Mapping[str, Any],
    reservation: Mapping[str, Any],
    readiness: Mapping[str, Any],
    readiness_external_identity: Mapping[str, Any],
    reservation_external_identity: Mapping[str, Any],
    readiness_publication_state: Mapping[str, Any],
    reservation_publication_state: Mapping[str, Any],
    formal_test_node_ids: Sequence[str],
    repository_root: Path,
    dependency_lock_path: Path,
    wheel_directory: Path,
    locked_runtime_root: Path,
    attempt_registry_root: Path,
    timeout_seconds: int = RECOVERY_EPOCH002_FORMAL_RUN_TIMEOUT_SECONDS,
) -> dict[str, Any]:
    """Run once and close every post-claim exception as unknown evidence."""

    attempt_id = reservation.get("attempt_id")
    directory = (
        attempt_registry_root.absolute() / attempt_id
        if isinstance(attempt_id, str)
        and _SHA256_RE.fullmatch(attempt_id) is not None
        else None
    )
    claimed_attempt = False
    try:
        directory, parent_checkpoint = _claim_published_reservation_attempt(
            authority_grant=authority_grant,
            reservation=reservation,
            readiness=readiness,
            readiness_external_identity=readiness_external_identity,
            reservation_external_identity=reservation_external_identity,
            readiness_publication_state=readiness_publication_state,
            reservation_publication_state=reservation_publication_state,
            attempt_registry_root=attempt_registry_root,
        )
        claimed_attempt = True
        return _run_recovery_epoch002_current_step_proof_impl(
            authority_grant=authority_grant,
            event1_artifact=event1_artifact,
            event1_external_identity=event1_external_identity,
            event1_publication_state=event1_publication_state,
            reservation=reservation,
            readiness=readiness,
            readiness_external_identity=readiness_external_identity,
            reservation_external_identity=reservation_external_identity,
            readiness_publication_state=readiness_publication_state,
            reservation_publication_state=reservation_publication_state,
            formal_test_node_ids=formal_test_node_ids,
            repository_root=repository_root,
            dependency_lock_path=dependency_lock_path,
            wheel_directory=wheel_directory,
            locked_runtime_root=locked_runtime_root,
            attempt_registry_root=attempt_registry_root,
            claimed_directory=directory,
            parent_checkpoint=parent_checkpoint,
            timeout_seconds=timeout_seconds,
        )
    except PermissionError as exc:
        if str(exc) == "FORMAL_ATTEMPT_ALREADY_CLAIMED":
            raise
        failure = exc
    except Exception as exc:
        failure = exc
    if (
        claimed_attempt is not True
        or directory is None
        or not directory.is_dir()
        or directory.is_symlink()
    ):
        raise failure
    try:
        return _close_claimed_attempt_unknown(
            directory=directory,
            reservation_identity=reservation_external_identity,
            reservation=reservation,
            readiness=readiness,
            exit_class="SPAWN_FAILED",
        )
    except Exception as closure_failure:
        raise failure from closure_failure


def validate_recovery_epoch002_closed_code_capture_state(
    state: Mapping[str, Any],
) -> tuple[str, ...]:
    """Require the eleven registered negative codes to be observed."""

    if (
        type(state) is not dict
        or validate_recovery_epoch002_success_terminal_state(state) != ()
    ):
        return ("TERMINAL_ACTUAL_CLOSED_CODE_NOT_OBSERVED",)
    observations = state.get("runner_closed_code_observations")
    terminal = state.get("terminal_result")
    outcomes = (
        terminal.get("outcomes")
        if type(terminal) is dict
        else None
    )
    if (
        type(observations) is not dict
        or observations != RECOVERY_EPOCH002_NEGATIVE_CLOSED_CODE_BY_NODE
        or type(outcomes) is not list
    ):
        return ("TERMINAL_ACTUAL_CLOSED_CODE_NOT_OBSERVED",)
    actual_by_node = {
        row.get("test_node_id"): row.get("actual_closed_code")
        for row in outcomes
        if type(row) is dict
    }
    if any(
        actual_by_node.get(node_id) != expected_code
        for node_id, expected_code in (
            RECOVERY_EPOCH002_NEGATIVE_CLOSED_CODE_BY_NODE.items()
        )
    ):
        return ("TERMINAL_ACTUAL_CLOSED_CODE_NOT_OBSERVED",)
    return ()


def _main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--internal-exact134-child", action="store_true")
    parser.add_argument("--context")
    parser.add_argument("--evidence-directory")
    known, forwarded = parser.parse_known_args(argv)
    if (
        known.internal_exact134_child is not True
        or known.context is None
        or known.evidence_directory is None
    ):
        return 2
    try:
        return _internal_exact134_child(
            context_path=Path(known.context),
            evidence_directory=Path(known.evidence_directory),
            forwarded_pytest_options=forwarded,
        )
    except (
        ImportError,
        KeyError,
        OSError,
        subprocess.SubprocessError,
        ValueError,
    ):
        return 2


if __name__ == "__main__":
    raise SystemExit(_main())


__all__ = [
    "RECOVERY_EPOCH002_CURRENT_STEP_PROOF_RUN_PROTOCOL",
    "RECOVERY_EPOCH002_FORMAL_NODE_COUNT",
    "RECOVERY_EPOCH002_FORMAL_RUN_TIMEOUT_SECONDS",
    "RECOVERY_EPOCH002_WORKER_ENVIRONMENT_FIXED",
    "RECOVERY_EPOCH002_WORKER_ENVIRONMENT_REMOVED",
    "RECOVERY_EPOCH002_RUN_CONTEXT_KEYS",
    "RECOVERY_EPOCH002_REGISTERED_NEGATIVE_NODE_IDS",
    "RECOVERY_EPOCH002_FORMAL_NODE_IDS",
    "RECOVERY_EPOCH002_NEGATIVE_CLOSED_CODE_BY_NODE",
    "build_recovery_epoch002_formal_worker_argv",
    "run_recovery_epoch002_current_step_proof",
    "validate_recovery_epoch002_closed_code_capture_state",
]
