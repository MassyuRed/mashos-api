#!/usr/bin/env python3
"""Official one-shot G4-B runtime preparation controller family V1.

Only ``main()`` is public and credit-bearing.  Import has no effects.  The CLI
owns the fixed P2>P3>P4>P6>P7 order, the private ledgers, cleanup and retention,
and the corrected post-cleanup single-build of the exact31 public result.
"""

from __future__ import annotations

import dataclasses
import hashlib
import json
import os
import selectors
import signal
import stat
import struct
import subprocess
import sys
import time
import zlib
from datetime import datetime, timezone
from typing import Any

from ai.tools.emlis_nls_v3_s11_g4b_runtime_preparation_contract_v1 import (
    PreparationContractV1,
    PreparationViolation,
    canonical_file_bytes,
    canonical_json_bytes,
    canonical_sha256,
    derive_requirements_bytes,
    strict_json_from_bytes,
    validate_execution_request,
    validate_lock_derivation,
    validate_public_result,
)
from ai.tools.emlis_nls_v3_s11_g4b_runtime_acquisition_v1 import (
    _abort_transport_binding,
    acquire_once,
    capture_transport_binding_at_start,
)
from ai.tools.emlis_nls_v3_s11_g4b_runtime_materialization_v1 import materialize_once
from ai.tools.emlis_nls_v3_s11_g4b_runtime_admission_bridge_v1 import run_admission_once

__all__ = ("main",)


DIRECT_CHILD_ORDER = (
    "P2_FOCUSED_UNITTEST",
    "P3_PIP_DOWNLOAD",
    "P4_CONTROL_PIP_OFFLINE_INSTALL",
    "P6_CHECKER_DEDICATED_TEST",
    "P7_OFFICIAL_CHECKER",
)
CONDITIONAL_EXPECTED_LAUNCH_EDGE_TOPOLOGY_EXACT11 = (
    "P1_CONTROLLER",
    "P2_FOCUSED_UNITTEST",
    "P3_PIP_DOWNLOAD",
    "P4_CONTROL_PIP_OFFLINE_INSTALL",
    "P5_TARGET_INTERPRETER_PIP_REEXEC",
    "P6_CHECKER_DEDICATED_TEST",
    "P7_CHECKER",
    "P8_OWNER",
    "P9_PYTEST_VERSION_PROBE",
    "P10_REQUIRED_ROLE_SMOKE",
    "P11_INDEPENDENT",
)
PUBLIC_RESULT_KEYS_EXACT31 = (
    "schema_version",
    "method_id",
    "candidate_id",
    "authority_context_binding_sha256",
    "session_context_binding_sha256",
    "status",
    "primary_terminal",
    "nested_checker_terminal",
    "technical_primary_outcome",
    "activated",
    "consumed",
    "checker_execution_attempt_count",
    "checker_component_status",
    "composite_technical_result",
    "current_session_runtime_readiness",
    "gate_b_technical_condition",
    "handoff_state",
    "gate_c_authorized",
    "cleanup_state",
    "retention_state",
    "technical_chain_complete",
    "publication_state",
    "durable_work_complete",
    "durable_current_owner_state",
    "durable_current_owner_runtime_ready",
    "durable_current_owner_gate_b_closed",
    "durable_current_owner_readiness_credit",
    "durable_current_owner_technical_credit",
    "durable_current_owner_product_credit",
    "durable_current_owner_primary_outcome",
    "automatic_progression",
)
PROCESS_LEDGER_KEYS_EXACT14 = (
    "sequence",
    "stage",
    "launch_owner",
    "executable_sha256",
    "argv_sha256",
    "environment_sha256",
    "cwd_binding_sha256",
    "pid_or_source_edge",
    "returncode",
    "stdout_sha256",
    "stdout_bytes",
    "stderr_sha256",
    "stderr_bytes",
    "termination_state",
)
PATH_LEDGER_KEYS_EXACT8 = (
    "sequence",
    "role",
    "locator_binding_sha256",
    "operation",
    "pre_state",
    "post_state",
    "result",
    "evidence_sha256",
)
_OFFICIAL_MODULE = "ai.tools.emlis_nls_v3_s11_g4b_runtime_preparation_controller_v1"
_FOCUSED_TEST_MODULE = (
    "ai.tests.test_emlis_nls_v3_s11_g4b_runtime_preparation_controller_v1"
)
_P1_ENVIRONMENT_EXACT7 = {
    "LANG": "C.UTF-8",
    "LC_ALL": "C.UTF-8",
    "PYTHONDONTWRITEBYTECODE": "1",
    "PYTHONHASHSEED": "0",
    "PYTHONNOUSERSITE": "1",
    "PYTHONUTF8": "1",
    "PYTEST_DISABLE_PLUGIN_AUTOLOAD": "1",
}
_P2_ENVIRONMENT_BASE = {"LANG": "C.UTF-8", "LC_ALL": "C.UTF-8"}
_MAX_INPUT_BYTES = 1_048_576
_MAX_STREAM_BYTES = 1_048_576
_DELETE_ON_STOP = (
    "controller_test_temp_root",
    "requirements_file_outside_runtime",
    "wheel_root",
    "process_temp_root",
    "runtime_root",
    "checker_test_pytest_ini",
    "checker_test_basetemp",
    "checker_probe_cwd",
    "private_handoff",
    "publication_staging",
)
_DELETE_ON_VALID = (
    "controller_test_temp_root",
    "requirements_file_outside_runtime",
    "wheel_root",
    "process_temp_root",
    "checker_test_pytest_ini",
    "checker_test_basetemp",
    "checker_probe_cwd",
)
_RETAIN_EVIDENCE = (
    "private_transport_binding_observation",
    "acquisition_observation",
    "materialization_attestation",
    "checker_request",
    "checker_result",
    "terminal_evidence",
    "cleanup_ledger",
)


@dataclasses.dataclass
class _Terminal:
    primary_terminal: str = "INTERNAL_FAIL_CLOSED"
    nested_checker_terminal: str = "NOT_APPLICABLE"
    consumed: bool = False
    checker_execution_attempt_count: int = 0
    checker_component_status: str = "NOT_RUN"
    composite_binding_sha256: str = "0" * 64
    success: bool = False
    retained_raw_sha256: dict[str, str] = dataclasses.field(default_factory=dict)
    runtime_full_root_manifest_sha256: str = ""
    materialization_event_id: str = ""


class _TerminalEvidenceSealFailure(RuntimeError):
    """Step 6 failed after the exact31 body was frozen; never build or emit another."""


@dataclasses.dataclass(frozen=True)
class _LifecycleDeadline:
    """Monotonic P1 wall deadline with the approved cleanup reserve."""

    started: float
    terminal: float
    cleanup_reserve_seconds: float

    @classmethod
    def start(cls) -> "_LifecycleDeadline":
        started = time.monotonic()
        return cls(
            started=started,
            terminal=started + PreparationContractV1.CONTROLLER_TOTAL_WALL_SECONDS,
            cleanup_reserve_seconds=PreparationContractV1.CLEANUP_RESERVE_SECONDS,
        )

    def require_phase_budget(self, phase: str, phase_seconds: float) -> None:
        now = time.monotonic()
        if (
            now < self.started
            or now + phase_seconds + self.cleanup_reserve_seconds > self.terminal
        ):
            raise PreparationViolation(
                "PATH_BUDGET_OR_SCOPE_EXCEEDED", f"{phase} would consume cleanup reserve"
            )

    def cleanup_expired(self) -> bool:
        now = time.monotonic()
        return now < self.started or now >= self.terminal


@dataclasses.dataclass(frozen=True)
class _ChildResult:
    pid: int
    returncode: int
    stdout: bytes
    stderr: bytes
    termination_state: str
    argv_sha256: str
    environment_sha256: str
    cwd_binding_sha256: str
    executable_sha256: str

    def ledger_row(self, sequence: int, stage: str) -> dict[str, Any]:
        return {
            "sequence": sequence,
            "stage": stage,
            "launch_owner": "OFFICIAL_CONTROLLER_V1",
            "executable_sha256": self.executable_sha256,
            "argv_sha256": self.argv_sha256,
            "environment_sha256": self.environment_sha256,
            "cwd_binding_sha256": self.cwd_binding_sha256,
            "pid_or_source_edge": str(self.pid),
            "returncode": self.returncode,
            "stdout_sha256": hashlib.sha256(self.stdout).hexdigest(),
            "stdout_bytes": len(self.stdout),
            "stderr_sha256": hashlib.sha256(self.stderr).hexdigest(),
            "stderr_bytes": len(self.stderr),
            "termination_state": self.termination_state,
        }


def _is_sha256(value: Any) -> bool:
    return (
        isinstance(value, str)
        and len(value) == 64
        and all(character in "0123456789abcdef" for character in value)
    )


def _validate_process_row(row: dict[str, Any]) -> None:
    if tuple(row) != PROCESS_LEDGER_KEYS_EXACT14:
        raise PreparationViolation("INTERNAL_FAIL_CLOSED", "process ledger schema drift")
    for key in (
        "executable_sha256", "argv_sha256", "environment_sha256",
        "cwd_binding_sha256", "stdout_sha256", "stderr_sha256",
    ):
        if not _is_sha256(row[key]):
            raise PreparationViolation(
                "INTERNAL_FAIL_CLOSED", f"process ledger {key} invalid"
            )
    if (
        type(row["sequence"]) is not int
        or row["sequence"] < 0
        or type(row["returncode"]) is not int
        or type(row["stdout_bytes"]) is not int
        or type(row["stderr_bytes"]) is not int
        or row["stdout_bytes"] < -1
        or row["stderr_bytes"] < -1
    ):
        raise PreparationViolation("INTERNAL_FAIL_CLOSED", "process ledger integer invalid")
    for key in ("stage", "launch_owner", "pid_or_source_edge", "termination_state"):
        if not isinstance(row[key], str) or not row[key] or "\x00" in row[key]:
            raise PreparationViolation(
                "INTERNAL_FAIL_CLOSED", f"process ledger {key} invalid"
            )


def _append_process_row(rows: list[dict[str, Any]], row: dict[str, Any]) -> None:
    candidate = dict(row)
    candidate["sequence"] = len(rows)
    ordered = {key: candidate[key] for key in PROCESS_LEDGER_KEYS_EXACT14}
    _validate_process_row(ordered)
    rows.append(ordered)


def _p1_process_row(request: dict[str, Any], repo_root: str) -> dict[str, Any]:
    executable = os.path.realpath(sys.executable)
    official_argv = (
        executable, "-E", "-s", "-S", "-B", "-m", _OFFICIAL_MODULE,
    )
    empty_sha = hashlib.sha256(b"").hexdigest()
    return {
        "sequence": 0,
        "stage": "P1_CONTROLLER",
        "launch_owner": "ULTRA_KAREN_APPROVED_LIVE_AUTHORITY",
        "executable_sha256": _sha256_file(executable, 67_108_864),
        "argv_sha256": canonical_sha256(list(official_argv)),
        "environment_sha256": canonical_sha256(_P1_ENVIRONMENT_EXACT7),
        "cwd_binding_sha256": canonical_sha256(
            {"schema_version": "g4b.cwd.binding.v1", "cwd": repo_root}
        ),
        "pid_or_source_edge": str(os.getpid()),
        # P1 seals this row before its own process can exit; -1 is explicitly
        # an unclaimed return code rather than a fabricated success.
        "returncode": -1,
        "stdout_sha256": empty_sha,
        "stdout_bytes": -1,
        "stderr_sha256": empty_sha,
        "stderr_bytes": -1,
        "termination_state": "TERMINAL_EMIT_PENDING_RETURN_CODE_UNOBSERVED",
    }


def _attempt_source_row(
    request: dict[str, Any], stage: str, terminal_state: str
) -> dict[str, Any]:
    """Describe a requested-but-unobserved OS edge without inventing a PID."""

    binding = canonical_sha256(
        {
            "schema_version": "g4b.requested.process.edge.v1",
            "stage": stage,
            "terminal_state": terminal_state,
            "candidate_id": PreparationContractV1.CANDIDATE_ID,
        }
    )
    empty_sha = hashlib.sha256(b"").hexdigest()
    return {
        "sequence": 0,
        "stage": stage,
        "launch_owner": (
            "ACQUISITION_V1" if stage == "P3_PIP_DOWNLOAD" else "ADMISSION_BRIDGE_V1"
        ),
        "executable_sha256": request["control_runtime"]["resolved_interpreter_sha256"],
        "argv_sha256": binding,
        "environment_sha256": binding,
        "cwd_binding_sha256": canonical_sha256(
            {
                "schema_version": "g4b.cwd.binding.v1",
                "cwd": request["path_plan"]["controller_test_cwd"],
            }
        ),
        "pid_or_source_edge": "OS_LAUNCH_REQUEST_EXACT1_PID_UNAVAILABLE",
        "returncode": -1,
        "stdout_sha256": empty_sha,
        "stdout_bytes": -1,
        "stderr_sha256": empty_sha,
        "stderr_bytes": -1,
        "termination_state": terminal_state,
    }


def _validate_process_ledger(rows: list[dict[str, Any]], *, success: bool) -> None:
    observed_stages: list[str] = []
    for sequence, row in enumerate(rows):
        row["sequence"] = sequence
        _validate_process_row(row)
        observed_stages.append(row["stage"])
    if len(observed_stages) != len(set(observed_stages)):
        raise PreparationViolation("INTERNAL_FAIL_CLOSED", "process stage duplicated")
    expected = CONDITIONAL_EXPECTED_LAUNCH_EDGE_TOPOLOGY_EXACT11
    positions = {stage: index for index, stage in enumerate(expected)}
    if any(stage not in positions for stage in observed_stages):
        raise PreparationViolation("INTERNAL_FAIL_CLOSED", "process stage unknown")
    if [positions[stage] for stage in observed_stages] != sorted(
        positions[stage] for stage in observed_stages
    ):
        raise PreparationViolation("INTERNAL_FAIL_CLOSED", "process stage order invalid")
    if success and tuple(observed_stages) != expected:
        raise PreparationViolation("INTERNAL_FAIL_CLOSED", "success process ledger not exact11")


def _effect_process_row(
    evidence: Any, *, stage: str, launch_owner: str
) -> dict[str, Any]:
    """Convert private effect metadata into one exact14 row without guessing."""

    if not isinstance(evidence, dict):
        raise PreparationViolation(
            "INTERNAL_FAIL_CLOSED", f"{stage} private process evidence absent"
        )
    required = {
        "pid", "returncode", "executable_sha256", "argv_sha256",
        "environment_sha256", "cwd_binding_sha256", "stdout_sha256",
        "stdout_bytes", "stderr_sha256", "stderr_bytes", "termination_state",
    }
    if set(evidence) != required or type(evidence["pid"]) is not int or evidence["pid"] <= 0:
        raise PreparationViolation(
            "INTERNAL_FAIL_CLOSED", f"{stage} private process evidence invalid"
        )
    row = {
        "sequence": 0,
        "stage": stage,
        "launch_owner": launch_owner,
        "executable_sha256": evidence["executable_sha256"],
        "argv_sha256": evidence["argv_sha256"],
        "environment_sha256": evidence["environment_sha256"],
        "cwd_binding_sha256": evidence["cwd_binding_sha256"],
        "pid_or_source_edge": str(evidence["pid"]),
        "returncode": evidence["returncode"],
        "stdout_sha256": evidence["stdout_sha256"],
        "stdout_bytes": evidence["stdout_bytes"],
        "stderr_sha256": evidence["stderr_sha256"],
        "stderr_bytes": evidence["stderr_bytes"],
        "termination_state": evidence["termination_state"],
    }
    _validate_process_row(row)
    return row


def _p5_source_edge_row(
    request: dict[str, Any], materialization: dict[str, Any], p4_row: dict[str, Any]
) -> dict[str, Any]:
    descriptor = {
        "schema_version": "g4b.p5.source_bound.argv.v1",
        "p4_argv_sha256": p4_row["argv_sha256"],
        "pip_runner_raw_sha256": PreparationContractV1.PIP_RUNNER_SHA256,
        "runtime_executable_locator_sha256": materialization[
            "runtime_executable_locator_sha256"
        ],
    }
    return {
        "sequence": 0,
        "stage": "P5_TARGET_INTERPRETER_PIP_REEXEC",
        "launch_owner": "PINNED_PIP_26_0_1_SOURCE_EDGE",
        "executable_sha256": materialization["resolved_interpreter_sha256"],
        "argv_sha256": canonical_sha256(descriptor),
        "environment_sha256": canonical_sha256(
            {
                "schema_version": "g4b.p5.source_bound.environment.v1",
                "p4_environment_sha256": p4_row["environment_sha256"],
                "pip_running_in_subprocess": "1",
            }
        ),
        "cwd_binding_sha256": p4_row["cwd_binding_sha256"],
        "pid_or_source_edge": PreparationContractV1.P5_STATIC_PROOF_STATE,
        "returncode": p4_row["returncode"],
        "stdout_sha256": p4_row["stdout_sha256"],
        "stdout_bytes": p4_row["stdout_bytes"],
        "stderr_sha256": p4_row["stderr_sha256"],
        "stderr_bytes": p4_row["stderr_bytes"],
        "termination_state": "EXITED_IN_P4_PROCESS_GROUP_PID_UNOBSERVED_SOURCE_BOUND",
    }


def _checker_internal_source_rows(
    request: dict[str, Any], checker_result: dict[str, Any]
) -> list[dict[str, Any]]:
    result_binding = canonical_sha256(checker_result)
    executable_sha = request["control_runtime"]["resolved_interpreter_sha256"]
    rows: list[dict[str, Any]] = []
    for stage in (
        "P8_OWNER", "P9_PYTEST_VERSION_PROBE", "P10_REQUIRED_ROLE_SMOKE", "P11_INDEPENDENT"
    ):
        stage_cwd = (
            request["path_plan"]["checker_probe_cwd"]
            if stage == "P9_PYTEST_VERSION_PROBE"
            else request["path_plan"]["checker_test_cwd"]
        )
        cwd_sha = canonical_sha256(
            {"schema_version": "g4b.cwd.binding.v1", "cwd": stage_cwd}
        )
        observation = canonical_sha256(
            {
                "schema_version": "g4b.checker.internal.validated.edge.v1",
                "stage": stage,
                "checker_public_result_sha256": result_binding,
            }
        )
        rows.append(
            {
                "sequence": 0,
                "stage": stage,
                "launch_owner": "UNCHANGED_CHECKER_V1_INTERNAL_OWNER",
                "executable_sha256": executable_sha,
                "argv_sha256": observation,
                "environment_sha256": canonical_sha256(_P1_ENVIRONMENT_EXACT7),
                "cwd_binding_sha256": cwd_sha,
                "pid_or_source_edge": "CHECKER_V1_INTERNAL_VALIDATED_CHILD_EXACT1_PID_UNPUBLISHED",
                "returncode": 0,
                "stdout_sha256": observation,
                "stdout_bytes": -1,
                "stderr_sha256": hashlib.sha256(b"").hexdigest(),
                "stderr_bytes": -1,
                "termination_state": "VALIDATED_BY_UNCHANGED_CHECKER_V1_PUBLIC_RESULT",
            }
        )
    return rows


def _sha256_file(path: str, limit: int = 536_870_912) -> str:
    digest = hashlib.sha256()
    count = 0
    try:
        observed = os.lstat(path)
        if not stat.S_ISREG(observed.st_mode) or observed.st_nlink != 1:
            raise PreparationViolation("BASE_OR_PREIMAGE_DRIFT", "file identity invalid")
        with open(path, "rb") as source:
            for block in iter(lambda: source.read(131_072), b""):
                count += len(block)
                if count > limit:
                    raise PreparationViolation("PATH_BUDGET_OR_SCOPE_EXCEEDED", "file too large")
                digest.update(block)
    except PreparationViolation:
        raise
    except OSError as exc:
        raise PreparationViolation("BASE_OR_PREIMAGE_DRIFT", "file observation failed") from exc
    return digest.hexdigest()


def _read_regular(path: str, limit: int) -> bytes:
    try:
        observed = os.lstat(path)
        if not stat.S_ISREG(observed.st_mode) or observed.st_nlink != 1:
            raise PreparationViolation("BASE_OR_PREIMAGE_DRIFT", "source is not regular")
        with open(path, "rb") as source:
            raw = source.read(limit + 1)
    except PreparationViolation:
        raise
    except OSError as exc:
        raise PreparationViolation("BASE_OR_PREIMAGE_DRIFT", "source read failed") from exc
    if len(raw) > limit:
        raise PreparationViolation("PATH_BUDGET_OR_SCOPE_EXCEEDED", "source too large")
    return raw


def _exclusive_file(path: str, payload: bytes, final_mode: int = 0o400) -> None:
    descriptor = -1
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0)
    try:
        descriptor = os.open(path, flags, 0o600)
        offset = 0
        while offset < len(payload):
            count = os.write(descriptor, payload[offset:])
            if count <= 0:
                raise OSError("short write")
            offset += count
        os.fsync(descriptor)
        os.fchmod(descriptor, final_mode)
        os.fsync(descriptor)
    except OSError as exc:
        raise PreparationViolation("PATH_BUDGET_OR_SCOPE_EXCEEDED", "private write failed") from exc
    finally:
        if descriptor >= 0:
            os.close(descriptor)
    _fsync_parent(path)


def _fsync_parent(path: str) -> None:
    descriptor = -1
    try:
        descriptor = os.open(os.path.dirname(path), os.O_RDONLY | os.O_DIRECTORY)
        os.fsync(descriptor)
    except OSError as exc:
        raise PreparationViolation("PATH_BUDGET_OR_SCOPE_EXCEEDED", "parent fsync failed") from exc
    finally:
        if descriptor >= 0:
            os.close(descriptor)


def _locator_binding(role: str, locator: str) -> str:
    return canonical_sha256(
        {"schema_version": "g4b.path.locator.binding.v1", "role": role, "locator": locator}
    )


def _path_row(
    rows: list[dict[str, Any]],
    role: str,
    locator: str,
    operation: str,
    pre_state: str,
    post_state: str,
    result: str,
) -> None:
    row = {
        "sequence": len(rows),
        "role": role,
        "locator_binding_sha256": _locator_binding(role, locator),
        "operation": operation,
        "pre_state": pre_state,
        "post_state": post_state,
        "result": result,
        "evidence_sha256": canonical_sha256(
            {
                "schema_version": "g4b.path.operation.evidence.v1",
                "role": role,
                "operation": operation,
                "pre_state": pre_state,
                "post_state": post_state,
                "result": result,
            }
        ),
    }
    if tuple(row) != PATH_LEDGER_KEYS_EXACT8:
        raise PreparationViolation("INTERNAL_FAIL_CLOSED", "path ledger schema drift")
    rows.append(row)


class _CleanupLedger:
    def __init__(self, path: str) -> None:
        self.path = path
        self._descriptor = -1
        self._raw_rows: list[bytes] = []
        flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0)
        try:
            self._descriptor = os.open(path, flags, 0o600)
        except OSError as exc:
            raise PreparationViolation("PATH_BUDGET_OR_SCOPE_EXCEEDED", "cleanup ledger create failed") from exc

    def append(
        self,
        phase: str,
        role: str,
        action: str,
        pre_state: str,
        result: str,
        post_state: str,
        evidence_sha256: str,
    ) -> None:
        if self._descriptor < 0:
            raise PreparationViolation("INTERNAL_FAIL_CLOSED", "cleanup ledger already sealed")
        if phase not in PreparationContractV1.CLEANUP_PHASES:
            raise PreparationViolation("INTERNAL_FAIL_CLOSED", "cleanup ledger phase invalid")
        if role not in PreparationContractV1.PATH_ROLE_NAMES:
            raise PreparationViolation("INTERNAL_FAIL_CLOSED", "cleanup ledger role invalid")
        if action not in PreparationContractV1.CLEANUP_ACTIONS:
            raise PreparationViolation("INTERNAL_FAIL_CLOSED", "cleanup ledger action invalid")
        for label, value in (
            ("pre_state", pre_state), ("result", result), ("post_state", post_state)
        ):
            if not isinstance(value, str) or not value or "\x00" in value:
                raise PreparationViolation(
                    "INTERNAL_FAIL_CLOSED", f"cleanup ledger {label} invalid"
                )
        if (
            not isinstance(evidence_sha256, str)
            or len(evidence_sha256) != 64
            or any(character not in "0123456789abcdef" for character in evidence_sha256)
        ):
            raise PreparationViolation(
                "INTERNAL_FAIL_CLOSED", "cleanup ledger evidence SHA invalid"
            )
        row = {
            "sequence": len(self._raw_rows),
            "phase": phase,
            "role": role,
            "action": action,
            "pre_state": pre_state,
            "result": result,
            "post_state": post_state,
            "evidence_sha256": evidence_sha256,
        }
        if tuple(row) != (
            "sequence", "phase", "role", "action", "pre_state", "result",
            "post_state", "evidence_sha256",
        ):
            raise PreparationViolation("INTERNAL_FAIL_CLOSED", "cleanup ledger schema drift")
        raw = canonical_json_bytes(row) + b"\n"
        offset = 0
        while offset < len(raw):
            written = os.write(self._descriptor, raw[offset:])
            if written <= 0:
                raise PreparationViolation("INTERNAL_FAIL_CLOSED", "cleanup ledger write failed")
            offset += written
        self._raw_rows.append(raw)

    def seal(self) -> tuple[str, bytes]:
        preimage_sha256 = hashlib.sha256(b"".join(self._raw_rows)).hexdigest()
        self.append(
            "TERMINAL_SEAL",
            "cleanup_ledger",
            "SEAL",
            "ACTIVE_0600",
            "COMPLETE",
            "SEALED_0400",
            preimage_sha256,
        )
        try:
            os.fsync(self._descriptor)
            os.fchmod(self._descriptor, 0o400)
            os.fsync(self._descriptor)
            os.close(self._descriptor)
            self._descriptor = -1
            _fsync_parent(self.path)
        except OSError as exc:
            raise PreparationViolation("INTERNAL_FAIL_CLOSED", "cleanup ledger seal failed") from exc
        raw = b"".join(self._raw_rows)
        return hashlib.sha256(raw).hexdigest(), raw


def _assert_official_cli_context() -> str:
    flags = sys.flags
    if not all(
        getattr(flags, name, 0) == 1
        for name in ("ignore_environment", "no_user_site", "no_site", "dont_write_bytecode")
    ):
        raise PreparationViolation("BASE_OR_PREIMAGE_DRIFT", "official Python flags absent")
    if getattr(__spec__, "name", None) != _OFFICIAL_MODULE or __name__ != "__main__":
        raise PreparationViolation("BASE_OR_PREIMAGE_DRIFT", "official module context absent")
    if dict(os.environ) != _P1_ENVIRONMENT_EXACT7:
        raise PreparationViolation("BASE_OR_PREIMAGE_DRIFT", "P1 environment not exact7")
    try:
        cwd = os.getcwd()
    except OSError as exc:
        raise PreparationViolation("BASE_OR_PREIMAGE_DRIFT", "cwd unavailable") from exc
    expected = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    if cwd != expected:
        raise PreparationViolation("BASE_OR_PREIMAGE_DRIFT", "official cwd mismatch")
    expected_argv = (
        os.path.realpath(sys.executable),
        "-E",
        "-s",
        "-S",
        "-B",
        "-m",
        _OFFICIAL_MODULE,
    )
    actual_argv = tuple(getattr(sys, "orig_argv", ()))
    if not actual_argv or os.path.realpath(actual_argv[0]) != expected_argv[0]:
        raise PreparationViolation("BASE_OR_PREIMAGE_DRIFT", "P1 executable argv drift")
    if (expected_argv[0], *actual_argv[1:]) != expected_argv:
        raise PreparationViolation("BASE_OR_PREIMAGE_DRIFT", "P1 official argv drift")
    return expected


def _verify_control_runtime(request: dict[str, Any]) -> None:
    """Bind the running P1 interpreter to the approved control-runtime bytes."""

    runtime = request["control_runtime"]
    executable = runtime["executable"]
    if (
        not os.path.isabs(executable)
        or os.path.normpath(executable) != executable
        or os.path.realpath(executable) != executable
    ):
        raise PreparationViolation("BASE_OR_PREIMAGE_DRIFT", "control executable not canonical")
    try:
        observed = os.lstat(executable)
    except OSError as exc:
        raise PreparationViolation("BASE_OR_PREIMAGE_DRIFT", "control executable absent") from exc
    if not stat.S_ISREG(observed.st_mode) or observed.st_nlink != 1:
        raise PreparationViolation("BASE_OR_PREIMAGE_DRIFT", "control executable identity invalid")
    if _sha256_file(executable, 67_108_864) != runtime["resolved_interpreter_sha256"]:
        raise PreparationViolation("BASE_OR_PREIMAGE_DRIFT", "control executable SHA mismatch")
    if os.path.realpath(sys.executable) != executable:
        raise PreparationViolation("BASE_OR_PREIMAGE_DRIFT", "P1 executable binding mismatch")
    if (
        getattr(sys.implementation, "name", "") != "cpython"
        or tuple(sys.version_info[:3]) != (3, 12, 13)
        or sys.platform != "linux"
        or os.uname().machine != "x86_64"
        or runtime["implementation"] != "CPython"
        or runtime["python_version"] != "3.12.13"
        or runtime["platform_tag"] != "linux-x86_64"
    ):
        raise PreparationViolation("BASE_OR_PREIMAGE_DRIFT", "control runtime actual drift")


def _read_git_file(path: str, limit: int = 33_554_432) -> bytes:
    """Read bounded, canonical, no-symlink Git metadata without invoking Git."""

    try:
        if os.path.realpath(path) != os.path.abspath(path):
            raise PreparationViolation(
                "BASE_OR_PREIMAGE_DRIFT", "Git metadata has a symlink component"
            )
        observed = os.lstat(path)
        if not stat.S_ISREG(observed.st_mode):
            raise PreparationViolation("BASE_OR_PREIMAGE_DRIFT", "Git metadata is not regular")
        if observed.st_size > limit:
            raise PreparationViolation("BASE_OR_PREIMAGE_DRIFT", "Git metadata exceeds limit")
        with open(path, "rb") as handle:
            body = handle.read(limit + 1)
    except PreparationViolation:
        raise
    except OSError as exc:
        raise PreparationViolation("BASE_OR_PREIMAGE_DRIFT", "Git metadata is unreadable") from exc
    if len(body) > limit:
        raise PreparationViolation("BASE_OR_PREIMAGE_DRIFT", "Git metadata exceeds limit")
    return body


def _is_git_oid(value: str) -> bool:
    return len(value) == 40 and all(character in "0123456789abcdef" for character in value)


def _git_directory(repo_root: str) -> str:
    dot_git = os.path.join(repo_root, ".git")
    try:
        observed = os.lstat(dot_git)
    except OSError as exc:
        raise PreparationViolation("BASE_OR_PREIMAGE_DRIFT", "Git directory is absent") from exc
    if stat.S_ISLNK(observed.st_mode):
        raise PreparationViolation("BASE_OR_PREIMAGE_DRIFT", "Git directory is a symlink")
    if stat.S_ISDIR(observed.st_mode):
        return dot_git
    if not stat.S_ISREG(observed.st_mode):
        raise PreparationViolation("BASE_OR_PREIMAGE_DRIFT", "unsupported .git locator")
    try:
        locator = _read_git_file(dot_git, 4096).decode("utf-8", "strict").strip()
    except UnicodeDecodeError as exc:
        raise PreparationViolation("BASE_OR_PREIMAGE_DRIFT", "Git locator is not UTF-8") from exc
    prefix = "gitdir: "
    if not locator.startswith(prefix) or "\n" in locator or "\r" in locator:
        raise PreparationViolation("BASE_OR_PREIMAGE_DRIFT", "Git locator format invalid")
    git_dir = locator[len(prefix) :]
    if not os.path.isabs(git_dir):
        git_dir = os.path.abspath(os.path.join(repo_root, git_dir))
    if os.path.realpath(git_dir) != git_dir or not os.path.isdir(git_dir):
        raise PreparationViolation("BASE_OR_PREIMAGE_DRIFT", "resolved Git directory invalid")
    return git_dir


def _git_common_directory(git_dir: str) -> str:
    commondir_path = os.path.join(git_dir, "commondir")
    if not os.path.lexists(commondir_path):
        return git_dir
    try:
        locator = _read_git_file(commondir_path, 4096).decode("utf-8", "strict").strip()
    except UnicodeDecodeError as exc:
        raise PreparationViolation("BASE_OR_PREIMAGE_DRIFT", "Git commondir is not UTF-8") from exc
    if not locator or "\n" in locator or "\r" in locator:
        raise PreparationViolation("BASE_OR_PREIMAGE_DRIFT", "Git commondir locator invalid")
    common_dir = locator if os.path.isabs(locator) else os.path.abspath(os.path.join(git_dir, locator))
    if os.path.realpath(common_dir) != common_dir or not os.path.isdir(common_dir):
        raise PreparationViolation("BASE_OR_PREIMAGE_DRIFT", "Git common directory invalid")
    return common_dir


def _packed_ref(git_dirs: tuple[str, ...], reference: str) -> str:
    matches: list[str] = []
    for directory in dict.fromkeys(git_dirs):
        packed_path = os.path.join(directory, "packed-refs")
        if not os.path.lexists(packed_path):
            continue
        try:
            lines = _read_git_file(packed_path, 8_388_608).decode("ascii", "strict").splitlines()
        except UnicodeDecodeError as exc:
            raise PreparationViolation("BASE_OR_PREIMAGE_DRIFT", "packed-refs is not ASCII") from exc
        for line in lines:
            if not line or line.startswith("#") or line.startswith("^"):
                continue
            pieces = line.split(" ", 1)
            if len(pieces) != 2:
                raise PreparationViolation("BASE_OR_PREIMAGE_DRIFT", "packed-refs row invalid")
            oid, name = pieces
            if name == reference:
                matches.append(oid)
    if len(matches) != 1 or not _is_git_oid(matches[0]):
        raise PreparationViolation("BASE_OR_PREIMAGE_DRIFT", "packed Git reference unresolved")
    return matches[0]


def _resolve_git_reference(git_dir: str, common_dir: str, value: str) -> str:
    current = value
    seen: set[str] = set()
    for _depth in range(5):
        if _is_git_oid(current):
            return current
        prefix = "ref: "
        if not current.startswith(prefix):
            raise PreparationViolation("BASE_OR_PREIMAGE_DRIFT", "Git reference value invalid")
        reference = current[len(prefix) :]
        if (
            not reference.startswith("refs/")
            or reference in seen
            or "\\" in reference
            or any(part in ("", ".", "..") for part in reference.split("/"))
        ):
            raise PreparationViolation("BASE_OR_PREIMAGE_DRIFT", "Git reference path invalid")
        seen.add(reference)
        ref_paths = [
            os.path.join(directory, *reference.split("/"))
            for directory in dict.fromkeys((git_dir, common_dir))
        ]
        loose_refs = [path for path in ref_paths if os.path.lexists(path)]
        if len(loose_refs) > 1:
            raise PreparationViolation("BASE_OR_PREIMAGE_DRIFT", "duplicate loose Git reference")
        if loose_refs:
            try:
                current = _read_git_file(loose_refs[0], 4096).decode("ascii", "strict").strip()
            except UnicodeDecodeError as exc:
                raise PreparationViolation("BASE_OR_PREIMAGE_DRIFT", "Git ref is not ASCII") from exc
        else:
            current = _packed_ref((git_dir, common_dir), reference)
    raise PreparationViolation("BASE_OR_PREIMAGE_DRIFT", "Git reference recursion exceeded")


def _commit_body_tree(body: bytes) -> str:
    first_line = body.split(b"\n", 1)[0]
    if not first_line.startswith(b"tree "):
        raise PreparationViolation("BASE_OR_PREIMAGE_DRIFT", "commit tree line absent")
    try:
        tree_oid = first_line[5:].decode("ascii", "strict")
    except UnicodeDecodeError as exc:
        raise PreparationViolation("BASE_OR_PREIMAGE_DRIFT", "commit tree is not ASCII") from exc
    if not _is_git_oid(tree_oid):
        raise PreparationViolation("BASE_OR_PREIMAGE_DRIFT", "commit tree identity invalid")
    return tree_oid


def _loose_commit_tree(common_dir: str, commit_oid: str) -> str | None:
    object_path = os.path.join(common_dir, "objects", commit_oid[:2], commit_oid[2:])
    if not os.path.lexists(object_path):
        return None
    compressed = _read_git_file(object_path, 1_048_576)
    try:
        decoder = zlib.decompressobj()
        decompressed = decoder.decompress(compressed, 1_048_577)
    except zlib.error as exc:
        raise PreparationViolation("BASE_OR_PREIMAGE_DRIFT", "loose commit object invalid") from exc
    if (
        len(decompressed) > 1_048_576
        or not decoder.eof
        or decoder.unconsumed_tail
        or decoder.unused_data
        or hashlib.sha1(decompressed).hexdigest() != commit_oid
    ):
        raise PreparationViolation("BASE_OR_PREIMAGE_DRIFT", "loose commit identity mismatch")
    separator = decompressed.find(b"\0")
    if separator < 0:
        raise PreparationViolation("BASE_OR_PREIMAGE_DRIFT", "loose commit header absent")
    header, body = decompressed[:separator], decompressed[separator + 1 :]
    pieces = header.split(b" ", 1)
    if len(pieces) != 2 or pieces[0] != b"commit":
        raise PreparationViolation("BASE_OR_PREIMAGE_DRIFT", "loose object is not a commit")
    try:
        declared_size = int(pieces[1], 10)
    except ValueError as exc:
        raise PreparationViolation("BASE_OR_PREIMAGE_DRIFT", "commit size is invalid") from exc
    if declared_size != len(body):
        raise PreparationViolation("BASE_OR_PREIMAGE_DRIFT", "commit size mismatch")
    return _commit_body_tree(body)


def _pack_index_offset(index_path: str, commit_oid: str) -> tuple[int, bytes, int]:
    index = _read_git_file(index_path, 67_108_864)
    if len(index) < 8 + 1024 + 40 or index[:4] != b"\xfftOc":
        raise PreparationViolation("BASE_OR_PREIMAGE_DRIFT", "pack index v2 header invalid")
    if struct.unpack(">I", index[4:8])[0] != 2:
        raise PreparationViolation("BASE_OR_PREIMAGE_DRIFT", "pack index version unsupported")
    if hashlib.sha1(index[:-20]).digest() != index[-20:]:
        raise PreparationViolation("BASE_OR_PREIMAGE_DRIFT", "pack index checksum invalid")
    fanout = struct.unpack(">256I", index[8:1032])
    if any(left > right for left, right in zip(fanout, fanout[1:])):
        raise PreparationViolation("BASE_OR_PREIMAGE_DRIFT", "pack index fanout invalid")
    count = fanout[-1]
    names_start = 1032
    crc_start = names_start + 20 * count
    offsets_start = crc_start + 4 * count
    offsets_end = offsets_start + 4 * count
    if offsets_end + 40 > len(index):
        raise PreparationViolation("BASE_OR_PREIMAGE_DRIFT", "pack index table truncated")
    large_bytes = len(index) - 40 - offsets_end
    if large_bytes < 0 or large_bytes % 8:
        raise PreparationViolation("BASE_OR_PREIMAGE_DRIFT", "pack index large offsets invalid")
    large_count = large_bytes // 8
    names = index[names_start:crc_start]
    target = bytes.fromhex(commit_oid)
    low, high = 0, count
    while low < high:
        middle = (low + high) // 2
        candidate = names[middle * 20 : (middle + 1) * 20]
        if candidate < target:
            low = middle + 1
        else:
            high = middle
    if low >= count or names[low * 20 : (low + 1) * 20] != target:
        raise KeyError(commit_oid)
    raw_offset = struct.unpack(">I", index[offsets_start + 4 * low : offsets_start + 4 * (low + 1)])[0]
    if raw_offset & 0x80000000:
        large_slot = raw_offset & 0x7FFFFFFF
        if large_slot >= large_count:
            raise PreparationViolation("BASE_OR_PREIMAGE_DRIFT", "pack large offset slot invalid")
        large_start = offsets_end + 8 * large_slot
        offset = struct.unpack(">Q", index[large_start : large_start + 8])[0]
    else:
        offset = raw_offset
    return offset, index[-40:-20], count


def _verify_pack_checksum(pack_path: str, expected_checksum: bytes) -> tuple[int, int]:
    try:
        if os.path.realpath(pack_path) != os.path.abspath(pack_path):
            raise PreparationViolation("BASE_OR_PREIMAGE_DRIFT", "pack file has a symlink component")
        observed = os.lstat(pack_path)
        if not stat.S_ISREG(observed.st_mode) or observed.st_size < 12 + 20:
            raise PreparationViolation("BASE_OR_PREIMAGE_DRIFT", "pack file invalid")
        digest = hashlib.sha1()
        with open(pack_path, "rb") as handle:
            header = handle.read(12)
            if len(header) != 12 or header[:4] != b"PACK":
                raise PreparationViolation("BASE_OR_PREIMAGE_DRIFT", "pack header invalid")
            version, count = struct.unpack(">II", header[4:12])
            if version not in (2, 3):
                raise PreparationViolation("BASE_OR_PREIMAGE_DRIFT", "pack version unsupported")
            handle.seek(0)
            remaining = observed.st_size - 20
            while remaining:
                block = handle.read(min(131_072, remaining))
                if not block:
                    raise PreparationViolation("BASE_OR_PREIMAGE_DRIFT", "pack truncated")
                digest.update(block)
                remaining -= len(block)
            trailer = handle.read(20)
    except PreparationViolation:
        raise
    except OSError as exc:
        raise PreparationViolation("BASE_OR_PREIMAGE_DRIFT", "pack file unreadable") from exc
    if trailer != expected_checksum or digest.digest() != trailer:
        raise PreparationViolation("BASE_OR_PREIMAGE_DRIFT", "pack checksum mismatch")
    return observed.st_size, count


def _packed_commit_tree(common_dir: str, commit_oid: str) -> str:
    pack_dir = os.path.join(common_dir, "objects", "pack")
    try:
        if os.path.realpath(pack_dir) != os.path.abspath(pack_dir):
            raise PreparationViolation("BASE_OR_PREIMAGE_DRIFT", "pack directory has a symlink component")
        with os.scandir(pack_dir) as scanner:
            indexes = sorted(
                entry.path
                for entry in scanner
                if entry.name.endswith(".idx") and entry.is_file(follow_symlinks=False)
            )
    except PreparationViolation:
        raise
    except OSError as exc:
        raise PreparationViolation("BASE_OR_PREIMAGE_DRIFT", "pack directory unavailable") from exc
    matches: list[tuple[str, int, bytes, int]] = []
    for index_path in indexes:
        try:
            offset, checksum, count = _pack_index_offset(index_path, commit_oid)
        except KeyError:
            continue
        matches.append((index_path[:-4] + ".pack", offset, checksum, count))
    if len(matches) != 1:
        raise PreparationViolation("BASE_OR_PREIMAGE_DRIFT", "packed commit cardinality invalid")
    pack_path, offset, checksum, index_count = matches[0]
    pack_size, pack_count = _verify_pack_checksum(pack_path, checksum)
    if pack_count != index_count or offset < 12 or offset >= pack_size - 20:
        raise PreparationViolation("BASE_OR_PREIMAGE_DRIFT", "packed commit offset invalid")
    try:
        with open(pack_path, "rb") as handle:
            handle.seek(offset)
            first = handle.read(1)
            if not first:
                raise PreparationViolation("BASE_OR_PREIMAGE_DRIFT", "packed object header absent")
            byte = first[0]
            object_type = (byte >> 4) & 0x7
            declared_size = byte & 0x0F
            shift = 4
            while byte & 0x80:
                next_byte = handle.read(1)
                if not next_byte or shift > 60:
                    raise PreparationViolation("BASE_OR_PREIMAGE_DRIFT", "packed object header invalid")
                byte = next_byte[0]
                declared_size |= (byte & 0x7F) << shift
                shift += 7
            if object_type != 1:
                raise PreparationViolation("BASE_OR_PREIMAGE_DRIFT", "packed commit is delta/unsupported")
            if declared_size > 1_048_576:
                raise PreparationViolation("BASE_OR_PREIMAGE_DRIFT", "packed commit exceeds limit")
            decoder = zlib.decompressobj()
            chunks: list[bytes] = []
            total = 0
            while not decoder.eof:
                block = handle.read(65_536)
                if not block:
                    raise PreparationViolation("BASE_OR_PREIMAGE_DRIFT", "packed commit truncated")
                output = decoder.decompress(block, 1_048_577 - total)
                chunks.append(output)
                total += len(output)
                if total > 1_048_576:
                    raise PreparationViolation("BASE_OR_PREIMAGE_DRIFT", "packed commit expands over limit")
            body = b"".join(chunks)
    except PreparationViolation:
        raise
    except (OSError, zlib.error) as exc:
        raise PreparationViolation("BASE_OR_PREIMAGE_DRIFT", "packed commit read invalid") from exc
    if len(body) != declared_size:
        raise PreparationViolation("BASE_OR_PREIMAGE_DRIFT", "packed commit size mismatch")
    object_bytes = f"commit {len(body)}\0".encode("ascii") + body
    if hashlib.sha1(object_bytes).hexdigest() != commit_oid:
        raise PreparationViolation("BASE_OR_PREIMAGE_DRIFT", "packed commit identity mismatch")
    return _commit_body_tree(body)


def _git_blob_oid(path: bytes, mode: int) -> bytes:
    try:
        observed = os.lstat(path)
    except OSError as exc:
        raise PreparationViolation("BASE_OR_PREIMAGE_DRIFT", "tracked worktree leaf is unavailable") from exc
    if mode in (0o100644, 0o100755):
        if not stat.S_ISREG(observed.st_mode):
            raise PreparationViolation("BASE_OR_PREIMAGE_DRIFT", "tracked file type mismatch")
        worktree_mode = 0o100755 if stat.S_IMODE(observed.st_mode) & 0o111 else 0o100644
        if worktree_mode != mode:
            raise PreparationViolation("BASE_OR_PREIMAGE_DRIFT", "tracked executable mode mismatch")
        length = observed.st_size
        digest = hashlib.sha1(f"blob {length}\0".encode("ascii"))
        try:
            with open(path, "rb") as handle:
                observed_length = 0
                for block in iter(lambda: handle.read(131_072), b""):
                    digest.update(block)
                    observed_length += len(block)
        except OSError as exc:
            raise PreparationViolation("BASE_OR_PREIMAGE_DRIFT", "tracked file unreadable") from exc
        if observed_length != length:
            raise PreparationViolation("BASE_OR_PREIMAGE_DRIFT", "tracked file changed while read")
        return digest.digest()
    if mode == 0o120000:
        if not stat.S_ISLNK(observed.st_mode):
            raise PreparationViolation("BASE_OR_PREIMAGE_DRIFT", "tracked symlink type mismatch")
        try:
            target = os.readlink(path)
        except OSError as exc:
            raise PreparationViolation("BASE_OR_PREIMAGE_DRIFT", "tracked symlink is unreadable") from exc
        target_bytes = os.fsencode(target) if isinstance(target, str) else target
        return hashlib.sha1(f"blob {len(target_bytes)}\0".encode("ascii") + target_bytes).digest()
    if mode in (0o160000, 0o040000):
        raise PreparationViolation("BASE_OR_PREIMAGE_DRIFT", "gitlink or sparse index unsupported")
    raise PreparationViolation("BASE_OR_PREIMAGE_DRIFT", "tracked mode unsupported")


def _tree_oid_from_entries(entries: list[tuple[bytes, int, bytes]]) -> str:
    root: dict[bytes, Any] = {}
    for path, mode, oid in entries:
        parts = path.split(b"/")
        if any(part in (b"", b".", b"..") for part in parts):
            raise PreparationViolation("BASE_OR_PREIMAGE_DRIFT", "tracked path invalid")
        cursor = root
        for component in parts[:-1]:
            current = cursor.get(component)
            if current is None:
                current = {}
                cursor[component] = current
            if not isinstance(current, dict):
                raise PreparationViolation("BASE_OR_PREIMAGE_DRIFT", "tracked path prefix conflict")
            cursor = current
        if parts[-1] in cursor:
            raise PreparationViolation("BASE_OR_PREIMAGE_DRIFT", "duplicate tracked path")
        cursor[parts[-1]] = (mode, oid)

    def build(node: dict[bytes, Any]) -> bytes:
        material: list[tuple[bytes, bytes]] = []
        for name, value in node.items():
            if isinstance(value, dict):
                child_oid = build(value)
                material.append((name + b"/", b"40000 " + name + b"\0" + child_oid))
            else:
                mode, child_oid = value
                material.append((name, f"{mode:o}".encode("ascii") + b" " + name + b"\0" + child_oid))
        body = b"".join(entry for _key, entry in sorted(material, key=lambda item: item[0]))
        return hashlib.sha1(f"tree {len(body)}\0".encode("ascii") + body).digest()

    return build(root).hex()


def _worktree_leaf_paths(repo_root: str) -> set[bytes]:
    """Return the no-follow worktree leaf set, excluding only root .git."""

    leaves: set[bytes] = set()
    pending = [repo_root]
    while pending:
        directory = pending.pop()
        try:
            with os.scandir(directory) as scanner:
                entries = sorted(scanner, key=lambda item: item.name, reverse=True)
        except OSError as exc:
            raise PreparationViolation("BASE_OR_PREIMAGE_DRIFT", "worktree scan failed") from exc
        for entry in entries:
            relative = os.path.relpath(entry.path, repo_root).replace(os.sep, "/")
            if relative == ".git":
                continue
            try:
                observed = entry.stat(follow_symlinks=False)
            except OSError as exc:
                raise PreparationViolation("BASE_OR_PREIMAGE_DRIFT", "worktree leaf observation failed") from exc
            if stat.S_ISDIR(observed.st_mode):
                pending.append(entry.path)
            elif stat.S_ISREG(observed.st_mode) or stat.S_ISLNK(observed.st_mode):
                encoded = os.fsencode(relative)
                if encoded in leaves:
                    raise PreparationViolation("BASE_OR_PREIMAGE_DRIFT", "duplicate worktree leaf")
                leaves.add(encoded)
            else:
                raise PreparationViolation("BASE_OR_PREIMAGE_DRIFT", "untracked special leaf present")
    return leaves


def _index_worktree_tree(repo_root: str, git_dir: str) -> str:
    index = _read_git_file(os.path.join(git_dir, "index"))
    if len(index) < 12 + 20 or hashlib.sha1(index[:-20]).digest() != index[-20:]:
        raise PreparationViolation("BASE_OR_PREIMAGE_DRIFT", "Git index checksum invalid")
    if index[:4] != b"DIRC":
        raise PreparationViolation("BASE_OR_PREIMAGE_DRIFT", "Git index signature invalid")
    version, count = struct.unpack(">II", index[4:12])
    if version not in (2, 3):
        raise PreparationViolation("BASE_OR_PREIMAGE_DRIFT", "Git index version unsupported")
    limit = len(index) - 20
    offset = 12
    previous_path: bytes | None = None
    parsed: list[tuple[bytes, int, bytes]] = []
    root_bytes = os.fsencode(repo_root)
    for _slot in range(count):
        entry_start = offset
        if offset + 62 > limit:
            raise PreparationViolation("BASE_OR_PREIMAGE_DRIFT", "Git index entry truncated")
        mode = struct.unpack(">I", index[offset + 24 : offset + 28])[0]
        expected_oid = index[offset + 40 : offset + 60]
        flags = struct.unpack(">H", index[offset + 60 : offset + 62])[0]
        if flags & 0x4000 or ((flags >> 12) & 0x3) != 0:
            raise PreparationViolation("BASE_OR_PREIMAGE_DRIFT", "extended or non-stage0 index entry")
        path_start = offset + 62
        path_end = index.find(b"\0", path_start, limit)
        if path_end < 0:
            raise PreparationViolation("BASE_OR_PREIMAGE_DRIFT", "Git index path terminator absent")
        path = index[path_start:path_end]
        declared_length = flags & 0x0FFF
        if declared_length != 0x0FFF and declared_length != len(path):
            raise PreparationViolation("BASE_OR_PREIMAGE_DRIFT", "Git index path length mismatch")
        if previous_path is not None and path <= previous_path:
            raise PreparationViolation("BASE_OR_PREIMAGE_DRIFT", "Git index path order invalid")
        previous_path = path
        raw_entry_size = path_end + 1 - entry_start
        padded_size = (raw_entry_size + 7) & ~7
        offset = entry_start + padded_size
        if offset > limit or any(index[path_end + 1 : offset]):
            raise PreparationViolation("BASE_OR_PREIMAGE_DRIFT", "Git index padding invalid")
        components = path.split(b"/")
        if any(component in (b"", b".", b"..") for component in components):
            raise PreparationViolation("BASE_OR_PREIMAGE_DRIFT", "Git index path invalid")
        worktree_path = os.path.join(root_bytes, *components)
        actual_oid = _git_blob_oid(worktree_path, mode)
        if actual_oid != expected_oid:
            raise PreparationViolation("BASE_OR_PREIMAGE_DRIFT", "tracked worktree blob mismatch")
        parsed.append((path, mode, expected_oid))
    while offset < limit:
        if offset + 8 > limit:
            raise PreparationViolation("BASE_OR_PREIMAGE_DRIFT", "Git index extension truncated")
        signature = index[offset : offset + 4]
        size = struct.unpack(">I", index[offset + 4 : offset + 8])[0]
        offset += 8
        if offset + size > limit:
            raise PreparationViolation("BASE_OR_PREIMAGE_DRIFT", "Git index extension size invalid")
        if not signature or 97 <= signature[0] <= 122:
            raise PreparationViolation("BASE_OR_PREIMAGE_DRIFT", "mandatory Git index extension unsupported")
        offset += size
    if offset != limit:
        raise PreparationViolation("BASE_OR_PREIMAGE_DRIFT", "Git index parse did not close")
    if _worktree_leaf_paths(repo_root) != {path for path, _mode, _oid in parsed}:
        raise PreparationViolation("BASE_OR_PREIMAGE_DRIFT", "tracked/untracked leaf set mismatch")
    return _tree_oid_from_entries(parsed)


def _actual_git_head_tree(repo_root: str) -> tuple[str, str]:
    """Resolve clean tracked HEAD/tree without Git, network, or filesystem writes."""

    if os.path.realpath(repo_root) != repo_root or not os.path.isdir(repo_root):
        raise PreparationViolation("BASE_OR_PREIMAGE_DRIFT", "repository root is not canonical")
    git_dir = _git_directory(repo_root)
    common_dir = _git_common_directory(git_dir)
    try:
        head_value = _read_git_file(os.path.join(git_dir, "HEAD"), 4096).decode(
            "ascii", "strict"
        ).strip()
    except UnicodeDecodeError as exc:
        raise PreparationViolation("BASE_OR_PREIMAGE_DRIFT", "Git HEAD is not ASCII") from exc
    head_commit = _resolve_git_reference(git_dir, common_dir, head_value)
    index_tree = _index_worktree_tree(repo_root, git_dir)
    commit_tree = _loose_commit_tree(common_dir, head_commit)
    if commit_tree is None:
        commit_tree = _packed_commit_tree(common_dir, head_commit)
    if commit_tree != index_tree:
        raise PreparationViolation("BASE_OR_PREIMAGE_DRIFT", "HEAD commit tree and index tree differ")
    return head_commit, index_tree


def _terminate(process: Any) -> None:
    try:
        os.killpg(process.pid, signal.SIGTERM)
    except (OSError, ProcessLookupError):
        pass
    try:
        process.wait(timeout=5.0)
        return
    except (subprocess.TimeoutExpired, OSError):
        pass
    try:
        os.killpg(process.pid, signal.SIGKILL)
    except (OSError, ProcessLookupError):
        pass
    try:
        process.wait(timeout=5.0)
    except (subprocess.TimeoutExpired, OSError):
        pass


def _run_child(
    argv: tuple[str, ...], cwd: str, environment: dict[str, str], timeout_seconds: float
) -> _ChildResult:
    try:
        process = subprocess.Popen(
            argv,
            cwd=cwd,
            env=dict(environment),
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            shell=False,
            text=False,
            close_fds=True,
            pass_fds=(),
            start_new_session=True,
        )
    except OSError as exc:
        raise PreparationViolation("CONTROLLER_FOCUSED_TEST_INVALID", "P2 launch failed") from exc
    assert process.stdout is not None and process.stderr is not None
    selector = selectors.DefaultSelector()
    selector.register(process.stdout, selectors.EVENT_READ, "stdout")
    selector.register(process.stderr, selectors.EVENT_READ, "stderr")
    captured = {"stdout": bytearray(), "stderr": bytearray()}
    deadline = time.monotonic() + timeout_seconds
    try:
        while selector.get_map():
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                _terminate(process)
                raise PreparationViolation("CONTROLLER_FOCUSED_TEST_INVALID", "P2 timeout")
            for key, _events in selector.select(min(remaining, 0.25)):
                block = os.read(key.fileobj.fileno(), 65_536)
                if not block:
                    selector.unregister(key.fileobj)
                    continue
                if len(captured[key.data]) + len(block) > _MAX_STREAM_BYTES:
                    _terminate(process)
                    raise PreparationViolation("CONTROLLER_FOCUSED_TEST_INVALID", "P2 output overflow")
                captured[key.data].extend(block)
        returncode = process.wait(timeout=max(0.0, deadline - time.monotonic()))
    except subprocess.TimeoutExpired as exc:
        _terminate(process)
        raise PreparationViolation("CONTROLLER_FOCUSED_TEST_INVALID", "P2 wait timeout") from exc
    finally:
        selector.close()
    return _ChildResult(
        pid=process.pid,
        returncode=returncode,
        stdout=bytes(captured["stdout"]),
        stderr=bytes(captured["stderr"]),
        termination_state="EXITED",
        argv_sha256=canonical_sha256(list(argv)),
        environment_sha256=canonical_sha256(environment),
        cwd_binding_sha256=canonical_sha256(
            {"schema_version": "g4b.cwd.binding.v1", "cwd": cwd}
        ),
        executable_sha256=_sha256_file(argv[0]),
    )


def _create_directory(path: str, rows: list[dict[str, Any]], role: str) -> None:
    try:
        os.mkdir(path, 0o700)
    except OSError as exc:
        raise PreparationViolation("PATH_BUDGET_OR_SCOPE_EXCEEDED", "directory create failed") from exc
    _path_row(rows, role, path, "CREATE", "ABSENT", "DIRECTORY_0700", "COMPLETE")


def _create_preparation_paths(
    request: dict[str, Any], rows: list[dict[str, Any]]
) -> _CleanupLedger:
    paths = request["path_plan"]
    authority_root = paths["authority_root"]
    parent = os.path.dirname(authority_root)
    parent_descriptor = -1
    try:
        if os.path.realpath(parent) != parent:
            raise PreparationViolation("PATH_BUDGET_OR_SCOPE_EXCEEDED", "authority parent invalid")
        parent_descriptor = os.open(
            parent,
            os.O_RDONLY
            | os.O_DIRECTORY
            | getattr(os, "O_CLOEXEC", 0)
            | getattr(os, "O_NOFOLLOW", 0),
        )
        parent_stat = os.fstat(parent_descriptor)
        if (
            not stat.S_ISDIR(parent_stat.st_mode)
            or parent_stat.st_uid != os.geteuid()
            or stat.S_IMODE(parent_stat.st_mode) != 0o700
        ):
            raise PreparationViolation(
                "PATH_BUDGET_OR_SCOPE_EXCEEDED", "authority parent ownership/mode invalid"
            )
        os.mkdir(authority_root, 0o700)
        child_stat = os.lstat(authority_root)
        if (
            not stat.S_ISDIR(child_stat.st_mode)
            or stat.S_ISLNK(child_stat.st_mode)
            or child_stat.st_uid != os.geteuid()
            or stat.S_IMODE(child_stat.st_mode) != 0o700
            or child_stat.st_dev != parent_stat.st_dev
        ):
            raise PreparationViolation(
                "PATH_BUDGET_OR_SCOPE_EXCEEDED",
                "authority root owner/mode/mount boundary invalid",
            )
    except PreparationViolation:
        raise
    except OSError as exc:
        raise PreparationViolation("PATH_BUDGET_OR_SCOPE_EXCEEDED", "authority root create failed") from exc
    finally:
        if parent_descriptor >= 0:
            os.close(parent_descriptor)
    _path_row(rows, "authority_root", authority_root, "CREATE", "ABSENT", "DIRECTORY_0700", "COMPLETE")
    try:
        ledger = _CleanupLedger(paths["cleanup_ledger"])
    except Exception:
        # No ledger exists yet, so remove the sole phase-created container.  A
        # caller may still emit a sanitized result, but must not claim retained
        # terminal evidence.
        try:
            _delete_tree_no_follow(authority_root)
        except Exception:
            pass
        raise
    try:
        ledger.append(
            "CONTROLLER_TEST", "authority_root", "CREATE", "ABSENT", "COMPLETE",
            "DIRECTORY_0700", canonical_sha256(
                {"schema_version": "g4b.lifecycle.event.v1", "role": "authority_root", "state": "DIRECTORY_0700"}
            ),
        )
        ledger.append(
            "CONTROLLER_TEST", "cleanup_ledger", "CREATE", "ABSENT", "COMPLETE",
            "ACTIVE_0600", canonical_sha256(
                {"schema_version": "g4b.lifecycle.event.v1", "role": "cleanup_ledger", "state": "ACTIVE_0600"}
            ),
        )
        for role in ("controller_test_temp_root", "process_temp_root"):
            _create_directory(paths[role], rows, role)
            ledger.append(
                "CONTROLLER_TEST", role, "CREATE", "ABSENT", "COMPLETE",
                "DIRECTORY_0700", canonical_sha256(
                    {"schema_version": "g4b.lifecycle.event.v1", "role": role, "state": "DIRECTORY_0700"}
                ),
            )
    except Exception as exc:
        setattr(exc, "cleanup_ledger", ledger)
        raise
    return ledger


def _run_focused_test(request: dict[str, Any]) -> _ChildResult:
    paths = request["path_plan"]
    environment = dict(_P2_ENVIRONMENT_BASE)
    for key in ("TEMP", "TMP", "TMPDIR"):
        environment[key] = paths["controller_test_temp_root"]
    result = _run_child(
        (
            request["control_runtime"]["executable"],
            "-E",
            "-s",
            "-S",
            "-B",
            "-m",
            "unittest",
            "-q",
            _FOCUSED_TEST_MODULE,
        ),
        paths["controller_test_cwd"],
        environment,
        PreparationContractV1.FOCUSED_TEST_WALL_SECONDS,
    )
    if result.returncode != 0:
        raise PreparationViolation("CONTROLLER_FOCUSED_TEST_INVALID", "P2 nonzero")
    return result


def _append_observation_rows(
    process_rows: list[dict[str, Any]],
    acquisition: dict[str, Any],
    materialization: dict[str, Any],
    *,
    require_private_evidence: bool = False,
) -> None:
    def effect_or_source(
        evidence: Any, *, stage: str, owner: str, projection: dict[str, Any]
    ) -> dict[str, Any]:
        if evidence is not None:
            return _effect_process_row(evidence, stage=stage, launch_owner=owner)
        if require_private_evidence:
            raise PreparationViolation(
                "INTERNAL_FAIL_CLOSED", f"{stage} private process evidence absent"
            )
        binding = canonical_sha256(
            {"schema_version": "g4b.process.observation.unexposed.v1", "stage": stage, **projection}
        )
        return {
            "sequence": 0,
            "stage": stage,
            "launch_owner": owner,
            "executable_sha256": binding,
            "argv_sha256": binding,
            "environment_sha256": binding,
            "cwd_binding_sha256": binding,
            "pid_or_source_edge": "PRIVATE_PROCESS_OBSERVATION_NOT_EXPOSED",
            "returncode": -1,
            "stdout_sha256": binding,
            "stdout_bytes": -1,
            "stderr_sha256": binding,
            "stderr_bytes": -1,
            "termination_state": "OBSERVATION_NOT_EXPOSED_NOT_CREDITABLE",
        }

    p3 = effect_or_source(
        acquisition.get("_process_evidence"),
        stage="P3_PIP_DOWNLOAD",
        owner="ACQUISITION_V1",
        projection={
            "argv_sha256": acquisition["argv_sha256"],
            "environment_sha256": acquisition["environment_sha256"],
            "returncode": acquisition["returncode"],
        },
    )
    p4 = effect_or_source(
        materialization.get("_process_evidence"),
        stage="P4_CONTROL_PIP_OFFLINE_INSTALL",
        owner="MATERIALIZATION_V1",
        projection={
            "process_projection_sha256": materialization["materialization_process_ledger_sha256"],
            "environment_policy_sha256": materialization["environment_policy_sha256"],
        },
    )
    _append_process_row(process_rows, p3)
    _append_process_row(process_rows, p4)
    _append_process_row(process_rows, _p5_source_edge_row({}, materialization, p4))


def _validate_materialization_process_projection(
    materialization: dict[str, Any], process_rows: list[dict[str, Any]]
) -> None:
    """Bind exact22's process digest to the terminal envelope P4/P5 rows."""

    projection = materialization.get("_process_ledger_projection")
    if not isinstance(projection, list) or len(projection) != 2:
        raise PreparationViolation(
            "INTERNAL_FAIL_CLOSED", "materialization process projection absent"
        )
    for sequence, row in enumerate(projection):
        if not isinstance(row, dict) or tuple(row) != PROCESS_LEDGER_KEYS_EXACT14:
            raise PreparationViolation(
                "INTERNAL_FAIL_CLOSED", "materialization process projection schema drift"
            )
        candidate = dict(row)
        candidate["sequence"] = sequence
        _validate_process_row(candidate)
    if canonical_sha256(projection) != materialization[
        "materialization_process_ledger_sha256"
    ]:
        raise PreparationViolation(
            "INTERNAL_FAIL_CLOSED", "materialization process projection SHA mismatch"
        )
    embedded = [
        dict(row)
        for row in process_rows
        if row["stage"] in (
            "P4_CONTROL_PIP_OFFLINE_INSTALL",
            "P5_TARGET_INTERPRETER_PIP_REEXEC",
        )
    ]
    for sequence, row in enumerate(embedded):
        row["sequence"] = sequence
    if embedded != projection:
        raise PreparationViolation(
            "INTERNAL_FAIL_CLOSED", "embedded P4/P5 projection mismatch"
        )


def _delete_tree_no_follow(path: str) -> None:
    try:
        observed = os.lstat(path)
    except FileNotFoundError:
        return
    if stat.S_ISLNK(observed.st_mode):
        raise PreparationViolation("INTERNAL_FAIL_CLOSED", "cleanup symlink refused")
    if stat.S_ISDIR(observed.st_mode):
        with os.scandir(path) as scanner:
            for entry in scanner:
                _delete_tree_no_follow(entry.path)
        os.rmdir(path)
    elif stat.S_ISREG(observed.st_mode):
        os.unlink(path)
    else:
        raise PreparationViolation("INTERNAL_FAIL_CLOSED", "cleanup special entry refused")


def _append_lifecycle_event(
    ledger: _CleanupLedger,
    phase: str,
    role: str,
    action: str,
    pre_state: str,
    result: str,
    post_state: str,
) -> None:
    ledger.append(
        phase,
        role,
        action,
        pre_state,
        result,
        post_state,
        canonical_sha256(
            {
                "schema_version": "g4b.lifecycle.event.v1",
                "phase": phase,
                "role": role,
                "action": action,
                "pre_state": pre_state,
                "result": result,
                "post_state": post_state,
            }
        ),
    )


def _sealed_regular_raw(path: str, limit: int = 33_554_432) -> tuple[bytes, str]:
    flags = os.O_RDONLY | getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_NOFOLLOW", 0)
    descriptor = -1
    try:
        descriptor = os.open(path, flags)
        observed = os.fstat(descriptor)
        if (
            not stat.S_ISREG(observed.st_mode)
            or observed.st_nlink != 1
            or stat.S_IMODE(observed.st_mode) != 0o400
        ):
            raise PreparationViolation(
                "INTERNAL_FAIL_CLOSED", "retained evidence is not sealed regular0400 nlink1"
            )
        chunks: list[bytes] = []
        total = 0
        while True:
            block = os.read(descriptor, 131_072)
            if not block:
                break
            total += len(block)
            if total > limit:
                raise PreparationViolation(
                    "PATH_BUDGET_OR_SCOPE_EXCEEDED", "retained evidence exceeds limit"
                )
            chunks.append(block)
    except PreparationViolation:
        raise
    except OSError as exc:
        raise PreparationViolation(
            "INTERNAL_FAIL_CLOSED", "retained evidence observation failed"
        ) from exc
    finally:
        if descriptor >= 0:
            os.close(descriptor)
    raw = b"".join(chunks)
    return raw, hashlib.sha256(raw).hexdigest()


def _runtime_full_root_manifest(root: str) -> str:
    try:
        root_stat = os.lstat(root)
    except OSError as exc:
        raise PreparationViolation("INTERNAL_FAIL_CLOSED", "retained runtime absent") from exc
    if (
        not stat.S_ISDIR(root_stat.st_mode)
        or stat.S_ISLNK(root_stat.st_mode)
        or stat.S_IMODE(root_stat.st_mode) != 0o700
    ):
        raise PreparationViolation("INTERNAL_FAIL_CLOSED", "retained runtime root invalid")
    rows: list[dict[str, Any]] = []
    regular_count = 0
    directory_count = 0
    total_bytes = 0
    for directory, directories, files in os.walk(root, topdown=True, followlinks=False):
        directories.sort()
        files.sort()
        for name in directories + files:
            path = os.path.join(directory, name)
            relative = os.path.relpath(path, root).replace(os.sep, "/")
            try:
                observed = os.lstat(path)
            except OSError as exc:
                raise PreparationViolation(
                    "INTERNAL_FAIL_CLOSED", "retained runtime inventory failed"
                ) from exc
            mode = stat.S_IMODE(observed.st_mode)
            if stat.S_ISLNK(observed.st_mode):
                raise PreparationViolation("INTERNAL_FAIL_CLOSED", "retained runtime symlink")
            if stat.S_ISDIR(observed.st_mode):
                directory_count += 1
                if directory_count > PreparationContractV1.RUNTIME_DIRECTORIES:
                    raise PreparationViolation(
                        "PATH_BUDGET_OR_SCOPE_EXCEEDED",
                        "retained runtime directory count exceeded",
                    )
                rows.append({"kind": "directory", "mode": mode, "relative_path": relative})
            elif stat.S_ISREG(observed.st_mode):
                regular_count += 1
                if regular_count > PreparationContractV1.RUNTIME_REGULAR_FILES:
                    raise PreparationViolation(
                        "PATH_BUDGET_OR_SCOPE_EXCEEDED",
                        "retained runtime regular-file count exceeded",
                    )
                raw_sha = _sha256_file(path, PreparationContractV1.RUNTIME_AGGREGATE_BYTES)
                total_bytes += observed.st_size
                if total_bytes > PreparationContractV1.RUNTIME_AGGREGATE_BYTES:
                    raise PreparationViolation(
                        "PATH_BUDGET_OR_SCOPE_EXCEEDED", "retained runtime bytes exceeded"
                    )
                rows.append(
                    {
                        "kind": "regular",
                        "mode": mode,
                        "relative_path": relative,
                        "size": observed.st_size,
                        "raw_sha256": raw_sha,
                    }
                )
            else:
                raise PreparationViolation("INTERNAL_FAIL_CLOSED", "retained runtime special file")
    rows.sort(key=lambda item: item["relative_path"])
    return canonical_sha256(rows)


def _validate_success_handoff(
    request: dict[str, Any], terminal: _Terminal, raw: bytes
) -> None:
    handoff = strict_json_from_bytes(raw)
    if (
        not isinstance(handoff, dict)
        or frozenset(handoff) != PreparationContractV1.PRIVATE_HANDOFF_KEYS
        or handoff["schema_version"] != PreparationContractV1.PRIVATE_HANDOFF_SCHEMA
        or handoff["authority_id"] != request["authority_id"]
        or handoff["observation_session_id"] != request["observation_session_id"]
        or handoff["receiver_session_id"] != request["receiver_session_id"]
        or handoff["receiver_nonce"] != request["receiver_nonce"]
        or handoff["materialization_event_id"] != terminal.materialization_event_id
        or handoff["expected_full_root_manifest_sha256"]
        != terminal.runtime_full_root_manifest_sha256
        or handoff["consumed"] is not False
    ):
        raise PreparationViolation("INTERNAL_FAIL_CLOSED", "retained handoff identity mismatch")
    root_binding = canonical_sha256(
        {
            "schema_version": "emlis.nls_v3.s11.g4b.runtime_root_locator.v1",
            "runtime_root": request["path_plan"]["runtime_root"],
        }
    )
    executable_binding = canonical_sha256(
        {
            "schema_version": "emlis.nls_v3.s11.g4b.runtime_executable_locator.v1",
            "runtime_executable": os.path.join(
                request["path_plan"]["runtime_root"], "bin", "python"
            ),
        }
    )
    if (
        handoff["runtime_root_locator_sha256"] != root_binding
        or handoff["runtime_executable_locator_sha256"] != executable_binding
        or not _is_sha256(handoff["runtime_readiness_observation_id"])
        or not _is_sha256(handoff["handoff_binding_sha256"])
    ):
        raise PreparationViolation("INTERNAL_FAIL_CLOSED", "retained handoff binding mismatch")


def _persisted_projection(
    value: dict[str, Any], expected_keys: frozenset[str], label: str
) -> dict[str, Any]:
    projection = {key: item for key, item in value.items() if not key.startswith("_")}
    if frozenset(projection) != expected_keys:
        raise PreparationViolation("INTERNAL_FAIL_CLOSED", f"{label} persisted schema drift")
    return projection


def _capture_retained_identity(
    terminal: _Terminal, paths: dict[str, str], role: str
) -> None:
    _raw, raw_sha256 = _sealed_regular_raw(paths[role])
    terminal.retained_raw_sha256[role] = raw_sha256


def _apply_terminal_exception(
    terminal: _Terminal,
    error: BaseException,
    request: dict[str, Any],
    process_rows: list[dict[str, Any]],
) -> None:
    terminal.primary_terminal = (
        error.code
        if isinstance(error, PreparationViolation)
        and error.code in PreparationContractV1.PRIMARY_STOP_TERMINALS
        else "INTERNAL_FAIL_CLOSED"
    )
    terminal.consumed = terminal.consumed or bool(getattr(error, "consumed", False))
    terminal.nested_checker_terminal = getattr(
        error, "nested_checker_terminal", terminal.nested_checker_terminal
    )
    terminal.checker_execution_attempt_count = int(
        getattr(error, "checker_execution_attempt_count", terminal.checker_execution_attempt_count)
    )
    terminal.checker_component_status = getattr(
        error, "checker_component_status", terminal.checker_component_status
    )
    observed = {row["stage"] for row in process_rows}
    if terminal.consumed and "P3_PIP_DOWNLOAD" not in observed:
        _append_process_row(
            process_rows,
            _attempt_source_row(
                request, "P3_PIP_DOWNLOAD", "CONSUMED_PROCESS_OBSERVATION_UNAVAILABLE"
            ),
        )
        observed.add("P3_PIP_DOWNLOAD")
    for raw_row in getattr(error, "process_rows", []):
        row = dict(raw_row)
        if row.get("stage") == "P7_OFFICIAL_CHECKER":
            row["stage"] = "P7_CHECKER"
        if row.get("stage") not in {item["stage"] for item in process_rows}:
            _append_process_row(process_rows, row)
    observed = {row["stage"] for row in process_rows}
    if terminal.checker_execution_attempt_count == 1 and "P7_CHECKER" not in observed:
        _append_process_row(
            process_rows,
            _attempt_source_row(
                request, "P7_CHECKER", "OS_LAUNCH_REQUEST_REJECTED_OR_UNOBSERVED"
            ),
        )
    terminal.success = False


def _cleanup(
    request: dict[str, Any],
    success: bool,
    path_rows: list[dict[str, Any]],
    ledger: _CleanupLedger,
    *,
    terminal: _Terminal | None = None,
    deadline: _LifecycleDeadline | None = None,
) -> tuple[str, str]:
    paths = request["path_plan"]
    complete = True
    unknown = False
    phase_created_roles = {
        row["role"]
        for row in tuple(path_rows)
        if row.get("operation") in ("CREATE", "WRITE", "SEAL")
        and row.get("result") == "COMPLETE"
        and row.get("post_state") not in ("ABSENT", "ABSENT_VERIFIED", "NOT_CREATED")
    }
    # Delete-role state table: absent-at-entry is NOT_CREATED/COMPLETE;
    # present-and-removed is DELETE/COMPLETE; any remaining or unobservable
    # object is DELETE/FAILED (or UNKNOWN after the reserved cleanup deadline).
    roles = _DELETE_ON_VALID if success else _DELETE_ON_STOP
    for role in roles:
        path = paths[role]
        existed = os.path.lexists(path)
        if deadline is not None and deadline.cleanup_expired():
            absent = False
            unknown = True
        else:
            try:
                _delete_tree_no_follow(path)
                absent = not os.path.lexists(path)
            except (OSError, PreparationViolation):
                absent = False
        result = "COMPLETE" if absent else ("UNKNOWN" if unknown else "FAILED")
        complete = complete and absent
        action = "DELETE" if existed else "NOT_CREATED"
        ledger.append(
            "TERMINAL_CLEANUP",
            role,
            action,
            "PRESENT" if existed else "NOT_CREATED",
            result,
            "ABSENT" if absent else "PRESENT_OR_UNKNOWN",
            canonical_sha256(
                {"schema_version": "g4b.cleanup.evidence.v1", "role": role, "absent": absent}
            ),
        )
        _path_row(
            path_rows,
            role,
            path,
            action,
            "PRESENT" if existed else "NOT_CREATED",
            "ABSENT" if absent else "PRESENT_OR_UNKNOWN",
            result,
        )
    required_retained = set(_RETAIN_EVIDENCE)
    required_retained.add("authority_root")
    if success:
        required_retained.update(("runtime_root", "private_handoff"))
    for role in sorted(required_retained):
        if role in ("terminal_evidence", "cleanup_ledger"):
            continue
        path = paths[role]
        retained = os.path.lexists(path)
        identity_match = False
        expected_sha256 = (
            terminal.retained_raw_sha256.get(role) if terminal is not None else None
        )
        expected_known = expected_sha256 is not None
        required = (
            success
            or role == "authority_root"
            or expected_known
            or role in phase_created_roles
        )
        if retained and role in ("authority_root", "runtime_root"):
            try:
                observed = os.lstat(path)
                structurally_valid = (
                    stat.S_ISDIR(observed.st_mode)
                    and not stat.S_ISLNK(observed.st_mode)
                    and observed.st_uid == os.geteuid()
                    and stat.S_IMODE(observed.st_mode) == 0o700
                )
                if role == "authority_root":
                    parent_observed = os.lstat(os.path.dirname(path))
                    structurally_valid = structurally_valid and (
                        stat.S_ISDIR(parent_observed.st_mode)
                        and not stat.S_ISLNK(parent_observed.st_mode)
                        and parent_observed.st_uid == os.geteuid()
                        and stat.S_IMODE(parent_observed.st_mode) == 0o700
                        and observed.st_dev == parent_observed.st_dev
                    )
                else:
                    authority_observed = os.lstat(paths["authority_root"])
                    structurally_valid = structurally_valid and (
                        stat.S_ISDIR(authority_observed.st_mode)
                        and not stat.S_ISLNK(authority_observed.st_mode)
                        and authority_observed.st_uid == os.geteuid()
                        and stat.S_IMODE(authority_observed.st_mode) == 0o700
                        and observed.st_dev == authority_observed.st_dev
                    )
                if not structurally_valid:
                    raise PreparationViolation("INTERNAL_FAIL_CLOSED", "retained directory invalid")
                if role == "runtime_root":
                    actual_manifest = _runtime_full_root_manifest(path)
                    identity_match = bool(
                        terminal is not None
                        and terminal.runtime_full_root_manifest_sha256
                        and actual_manifest == terminal.runtime_full_root_manifest_sha256
                    )
                else:
                    identity_match = True
            except (OSError, PreparationViolation):
                identity_match = False
        elif retained:
            # Only a true, phase-uncreated absence may become NOT_CREATED.
            # Every present object must be a sealed exact-byte match.
            try:
                raw, raw_sha256 = _sealed_regular_raw(path)
                identity_match = expected_known and expected_sha256 == raw_sha256
                if role == "private_handoff" and success and terminal is not None:
                    _validate_success_handoff(request, terminal, raw)
            except PreparationViolation:
                identity_match = False
        required_match = retained and identity_match
        retain_result = (
            "COMPLETE"
            if required_match or (not retained and not required)
            else "FAILED"
        )
        complete = complete and retain_result == "COMPLETE"
        action = "RETAIN" if retained or required else "NOT_CREATED"
        pre_state = (
            "PRESENT"
            if retained
            else ("EXPECTED_PRESENT" if required else "NOT_CREATED")
        )
        post_state = (
            "RETAINED"
            if retained
            else ("ABSENT_AFTER_CREATION" if required else "NOT_CREATED")
        )
        ledger.append(
            "TERMINAL_CLEANUP",
            role,
            action,
            pre_state,
            retain_result,
            post_state,
            canonical_sha256(
                {"schema_version": "g4b.retention.evidence.v1", "role": role, "retained": retained}
            ),
        )
        _path_row(
            path_rows,
            role,
            path,
            action,
            pre_state,
            post_state,
            retain_result,
        )
    if unknown:
        return "UNKNOWN", "PARTIAL_PRIVATE_STATE_RETAINED"
    if not complete:
        return "FAILED", "PARTIAL_PRIVATE_STATE_RETAINED"
    return "COMPLETE", "CURRENT_SESSION_RETAINED" if success else "EVIDENCE_RETAINED"


def _context_bindings(request: dict[str, Any]) -> tuple[str, str]:
    authority = canonical_sha256(
        {
            "schema_version": "g4b.authority.context.binding.v1",
            "authority_id": request["authority_id"],
            "approved_candidate_body_sha256": request["approved_candidate_body_sha256"],
        }
    )
    session = canonical_sha256(
        {
            "schema_version": "g4b.session.context.binding.v1",
            "observation_session_id": request["observation_session_id"],
            "receiver_session_id": request["receiver_session_id"],
            "receiver_nonce": request["receiver_nonce"],
        }
    )
    return authority, session


def _build_public_result_once(
    request: dict[str, Any], terminal: _Terminal, cleanup_state: str, retention_state: str
) -> tuple[dict[str, Any], bytes, str]:
    authority_binding, session_binding = _context_bindings(request)
    valid = terminal.success and cleanup_state == "COMPLETE"
    # Cleanup is a separate state and never erases the primary technical fact.
    # The public exact31 STOP vocabulary nevertheless requires a STOP terminal,
    # so a checker-VALID/cleanup-incomplete chain is fail-closed under the
    # generic internal terminal while preserving the nested checker component.
    public_terminal = (
        PreparationContractV1.PRIMARY_SUCCESS_TERMINAL
        if valid
        else (
            "INTERNAL_FAIL_CLOSED"
            if terminal.success and cleanup_state != "COMPLETE"
            else terminal.primary_terminal
        )
    )
    result: dict[str, Any] = {}
    values = {
        "schema_version": PreparationContractV1.PUBLIC_RESULT_SCHEMA,
        "method_id": PreparationContractV1.METHOD_ID,
        "candidate_id": PreparationContractV1.CANDIDATE_ID,
        "authority_context_binding_sha256": authority_binding,
        "session_context_binding_sha256": session_binding,
        "status": "VALID" if valid else "STOP",
        "primary_terminal": public_terminal,
        "nested_checker_terminal": terminal.nested_checker_terminal,
        "technical_primary_outcome": "TECHNICAL_CREDIT" if valid else "BLOCKER_NARROWED",
        "activated": True,
        "consumed": terminal.consumed,
        "checker_execution_attempt_count": terminal.checker_execution_attempt_count,
        "checker_component_status": terminal.checker_component_status,
        "composite_technical_result": (
            "VALID" if valid else (
                "STOP_CLEANUP_INCOMPLETE"
                if terminal.success and cleanup_state != "COMPLETE"
                else "STOP"
            )
        ),
        "current_session_runtime_readiness": "READY_CURRENT_SESSION" if valid else "NOT_READY",
        "gate_b_technical_condition": (
            "SATISFIED_CURRENT_SESSION" if valid else "NOT_SATISFIED"
        ),
        "handoff_state": "HANDOFF_BOUND_CURRENT_SESSION" if valid else "NOT_BOUND",
        "gate_c_authorized": False,
        "cleanup_state": cleanup_state,
        "retention_state": retention_state,
        "technical_chain_complete": valid,
        "publication_state": "NOT_ATTEMPTED",
        "durable_work_complete": False,
        "durable_current_owner_state": "UNCHANGED_PENDING_PUBLICATION" if valid else "UNCHANGED",
        "durable_current_owner_runtime_ready": False,
        "durable_current_owner_gate_b_closed": False,
        "durable_current_owner_readiness_credit": 0,
        "durable_current_owner_technical_credit": 0,
        "durable_current_owner_product_credit": 0,
        "durable_current_owner_primary_outcome": "BLOCKER_NARROWED",
        "automatic_progression": False,
    }
    for key in PUBLIC_RESULT_KEYS_EXACT31:
        result[key] = values[key]
    validate_public_result(result)
    frozen_bytes = canonical_json_bytes(result)
    return result, frozen_bytes, hashlib.sha256(frozen_bytes).hexdigest()


def _seal_terminal_evidence(
    request: dict[str, Any],
    terminal: _Terminal,
    cleanup_state: str,
    retention_state: str,
    cleanup_sha256: str,
    public_result_sha256: str,
    process_rows: list[dict[str, Any]],
    path_rows: list[dict[str, Any]],
) -> None:
    for sequence, row in enumerate(process_rows):
        row["sequence"] = sequence
        if tuple(row) != PROCESS_LEDGER_KEYS_EXACT14:
            raise PreparationViolation("INTERNAL_FAIL_CLOSED", "process ledger schema drift")
    for sequence, row in enumerate(path_rows):
        row["sequence"] = sequence
    terminal_evidence = {
        "schema_version": PreparationContractV1.TERMINAL_EVIDENCE_SCHEMA,
        "candidate_id": PreparationContractV1.CANDIDATE_ID,
        "authority_id": request["authority_id"],
        "observation_session_id": request["observation_session_id"],
        "activated": True,
        "consumed": terminal.consumed,
        "primary_terminal": (
            PreparationContractV1.PRIMARY_SUCCESS_TERMINAL
            if terminal.success and cleanup_state == "COMPLETE"
            else (
                "INTERNAL_FAIL_CLOSED"
                if terminal.success and cleanup_state != "COMPLETE"
                else terminal.primary_terminal
            )
        ),
        "nested_checker_terminal": terminal.nested_checker_terminal,
        "checker_component_status": terminal.checker_component_status,
        "cleanup_state": cleanup_state,
        "retention_state": retention_state,
        "publication_state": "NOT_ATTEMPTED",
        "process_ledger_sha256": canonical_sha256(process_rows),
        "path_ledger_sha256": canonical_sha256(path_rows),
        "composite_binding_sha256": terminal.composite_binding_sha256,
        "public_result_sha256": public_result_sha256,
        "cleanup_ledger_sha256": cleanup_sha256,
        "created_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "automatic_progression": False,
    }
    if frozenset(terminal_evidence) != PreparationContractV1.TERMINAL_EVIDENCE_KEYS:
        raise PreparationViolation("INTERNAL_FAIL_CLOSED", "terminal evidence schema drift")
    envelope = {
        "schema_version": "emlis.nls_v3.s11.g4b.runtime_preparation.terminal_envelope.v1",
        "terminal_evidence": terminal_evidence,
        "process_ledger": process_rows,
        "path_ledger": path_rows,
    }
    _exclusive_file(
        request["path_plan"]["terminal_evidence"], canonical_json_bytes(envelope), 0o400
    )


def _load_and_validate_lock(repo_root: str) -> dict[str, Any]:
    formal = _read_regular(
        os.path.join(
            repo_root,
            "ai/configs/emlis_nls_v3_recovery_epoch002_formal_worker_bootstrap_lock_v1.json",
        ),
        131_072,
    )
    derived = _read_regular(
        os.path.join(
            repo_root,
            "ai/configs/emlis_nls_v3_s11_g4b_runtime_preparation_exact5_lock_v1.json",
        ),
        16_384,
    )
    return validate_lock_derivation(formal, derived)


def _run_lifecycle(
    request: dict[str, Any],
    repo_root: str,
    process_rows: list[dict[str, Any]],
    path_rows: list[dict[str, Any]],
    deadline: _LifecycleDeadline | None = None,
) -> tuple[_Terminal, _CleanupLedger]:
    paths = request["path_plan"]
    deadline = deadline or _LifecycleDeadline.start()
    terminal = _Terminal()
    b0_active = False
    try:
        ledger = _create_preparation_paths(request, path_rows)
    except Exception as exc:
        partial_ledger = getattr(exc, "cleanup_ledger", None)
        if not isinstance(partial_ledger, _CleanupLedger):
            raise
        _apply_terminal_exception(terminal, exc, request, process_rows)
        return terminal, partial_ledger
    try:
        _verify_control_runtime(request)
        expected_head_tree = (
            request["expected_git"]["mashos_api_commit"],
            request["expected_git"]["mashos_api_tree"],
        )
        if _actual_git_head_tree(repo_root) != expected_head_tree:
            raise PreparationViolation("BASE_OR_PREIMAGE_DRIFT", "Git HEAD/tree mismatch")
        validated_lock = _load_and_validate_lock(repo_root)
        b0 = capture_transport_binding_at_start(request)
        b0_active = True
        _path_row(
            path_rows,
            "private_transport_binding_observation",
            paths["private_transport_binding_observation"],
            "CREATE",
            "ABSENT",
            "ACTIVE_0600",
            "COMPLETE",
        )
        _append_lifecycle_event(
            ledger,
            "ACQUISITION",
            "private_transport_binding_observation",
            "CREATE",
            "ABSENT",
            "COMPLETE",
            "ACTIVE_0600",
        )
        deadline.require_phase_budget(
            "P2_FOCUSED_UNITTEST", PreparationContractV1.FOCUSED_TEST_WALL_SECONDS
        )
        p2 = _run_focused_test(request)
        _append_process_row(
            process_rows, p2.ledger_row(len(process_rows), "P2_FOCUSED_UNITTEST")
        )
        _append_lifecycle_event(
            ledger,
            "CONTROLLER_TEST",
            "controller_test_temp_root",
            "WRITE",
            "DIRECTORY_0700",
            "COMPLETE",
            "P2_EXACT18_PASS",
        )
        _delete_tree_no_follow(paths["controller_test_temp_root"])
        _path_row(
            path_rows,
            "controller_test_temp_root",
            paths["controller_test_temp_root"],
            "DELETE",
            "DIRECTORY_0700",
            "ABSENT",
            "COMPLETE",
        )
        _append_lifecycle_event(
            ledger,
            "CONTROLLER_TEST",
            "controller_test_temp_root",
            "DELETE",
            "DIRECTORY_0700",
            "COMPLETE",
            "ABSENT",
        )
        _append_lifecycle_event(
            ledger,
            "CONTROLLER_TEST",
            "controller_test_temp_root",
            "VERIFY_ABSENT",
            "ABSENT",
            "COMPLETE",
            "ABSENT_VERIFIED",
        )
        deadline.require_phase_budget(
            "P3_PIP_DOWNLOAD", PreparationContractV1.ACQUISITION_WALL_SECONDS
        )
        acquisition = acquire_once(request, validated_lock, b0)
        b0_active = False
        terminal.consumed = bool(acquisition.get("consumed"))
        acquisition_persisted = _persisted_projection(
            acquisition,
            PreparationContractV1.ACQUISITION_OBSERVATION_KEYS,
            "acquisition observation",
        )
        for role, operation, pre_state, post_state in (
            ("requirements_file_outside_runtime", "CREATE", "ABSENT", "SEALED_0400"),
            ("wheel_root", "CREATE", "ABSENT", "DIRECTORY_0700_WITH_EXACT5"),
            ("acquisition_observation", "CREATE", "ABSENT", "SEALED_0400"),
            (
                "private_transport_binding_observation",
                "SEAL",
                "ACTIVE_0600",
                "SEALED_0400",
            ),
        ):
            _path_row(
                path_rows,
                role,
                paths[role],
                operation,
                pre_state,
                post_state,
                "COMPLETE",
            )
            _append_lifecycle_event(
                ledger,
                "ACQUISITION",
                role,
                "SEAL" if post_state == "SEALED_0400" else "CREATE",
                pre_state,
                "COMPLETE",
                post_state,
            )
        for role in (
            "private_transport_binding_observation", "acquisition_observation"
        ):
            _capture_retained_identity(terminal, paths, role)
        deadline.require_phase_budget(
            "P4_P5_MATERIALIZATION",
            PreparationContractV1.IN_PROCESS_MATERIALIZATION_WALL_SECONDS
            + PreparationContractV1.OFFLINE_INSTALL_WALL_SECONDS,
        )
        materialization = materialize_once(
            request, validated_lock, acquisition_persisted
        )
        materialization_persisted = _persisted_projection(
            materialization,
            PreparationContractV1.MATERIALIZATION_ATTESTATION_KEYS,
            "materialization attestation",
        )
        terminal.runtime_full_root_manifest_sha256 = materialization_persisted[
            "full_runtime_root_manifest_sha256"
        ]
        terminal.materialization_event_id = materialization_persisted["event_id"]
        for role, post_state in (
            ("runtime_root", "MATERIALIZED_VERIFIED"),
            ("materialization_attestation", "SEALED_0400"),
        ):
            _path_row(
                path_rows,
                role,
                paths[role],
                "CREATE",
                "ABSENT",
                post_state,
                "COMPLETE",
            )
            _append_lifecycle_event(
                ledger,
                "MATERIALIZATION",
                role,
                "SEAL" if post_state == "SEALED_0400" else "CREATE",
                "ABSENT",
                "COMPLETE",
                post_state,
            )
        _capture_retained_identity(terminal, paths, "materialization_attestation")
        _append_observation_rows(
            process_rows,
            acquisition,
            materialization,
            require_private_evidence=True,
        )
        _validate_materialization_process_projection(materialization, process_rows)
        _create_directory(paths["checker_probe_cwd"], path_rows, "checker_probe_cwd")
        _append_lifecycle_event(
            ledger,
            "ADMISSION",
            "checker_probe_cwd",
            "CREATE",
            "ABSENT",
            "COMPLETE",
            "DIRECTORY_0700",
        )
        _exclusive_file(paths["checker_test_pytest_ini"], b"", 0o400)
        _path_row(
            path_rows,
            "checker_test_pytest_ini",
            paths["checker_test_pytest_ini"],
            "CREATE",
            "ABSENT",
            "SEALED_0400",
            "COMPLETE",
        )
        _append_lifecycle_event(
            ledger,
            "CHECKER_TEST",
            "checker_test_pytest_ini",
            "SEAL",
            "ABSENT",
            "COMPLETE",
            "SEALED_0400",
        )
        deadline.require_phase_budget(
            "P6_P7_CHECKER_ADMISSION",
            PreparationContractV1.CHECKER_TEST_WALL_SECONDS
            + PreparationContractV1.CHECKER_WALL_SECONDS,
        )
        bridge = run_admission_once(request, materialization_persisted)
        for row in bridge["process_rows"]:
            row = dict(row)
            if row.get("stage") == "P7_OFFICIAL_CHECKER":
                row["stage"] = "P7_CHECKER"
            _append_process_row(process_rows, row)
        terminal.primary_terminal = PreparationContractV1.PRIMARY_SUCCESS_TERMINAL
        terminal.nested_checker_terminal = bridge["nested_checker_terminal"]
        terminal.checker_execution_attempt_count = bridge["checker_execution_attempt_count"]
        terminal.checker_component_status = bridge["checker_component_status"]
        terminal.composite_binding_sha256 = bridge["composite_binding_sha256"]
        for role, post_state in (
            ("checker_test_basetemp", "DIRECTORY_CREATED_BY_P6"),
            ("checker_request", "SEALED_0400"),
            ("checker_result", "SEALED_0400"),
            ("private_handoff", "SEALED_0400"),
        ):
            if os.path.lexists(paths[role]):
                _path_row(
                    path_rows,
                    role,
                    paths[role],
                    "CREATE",
                    "ABSENT",
                    post_state,
                    "COMPLETE",
                )
                _append_lifecycle_event(
                    ledger,
                    "CHECKER_TEST" if role == "checker_test_basetemp" else "ADMISSION",
                    role,
                    "CREATE" if role == "checker_test_basetemp" else "SEAL",
                    "ABSENT",
                    "COMPLETE",
                    post_state,
                )
        for role in ("checker_request", "checker_result", "private_handoff"):
            _capture_retained_identity(terminal, paths, role)
        for row in _checker_internal_source_rows(request, bridge["checker_result"]):
            _append_process_row(process_rows, row)
        _validate_process_ledger(process_rows, success=True)
        terminal.success = True
    except Exception as exc:
        if b0_active:
            try:
                _abort_transport_binding(request)
                if os.path.lexists(paths["private_transport_binding_observation"]):
                    _capture_retained_identity(
                        terminal, paths, "private_transport_binding_observation"
                    )
                    _path_row(
                        path_rows,
                        "private_transport_binding_observation",
                        paths["private_transport_binding_observation"],
                        "SEAL",
                        "ACTIVE_0600",
                        "SEALED_0400_FAILURE_SUMMARY",
                        "COMPLETE",
                    )
                    _append_lifecycle_event(
                        ledger,
                        "ACQUISITION",
                        "private_transport_binding_observation",
                        "SEAL",
                        "ACTIVE_0600",
                        "COMPLETE",
                        "SEALED_0400_FAILURE_SUMMARY",
                    )
            except Exception:
                exc = PreparationViolation(
                    "PRIVATE_TRANSPORT_BINDING_INVALID",
                    "B0 failure summary seal failed",
                )
        _apply_terminal_exception(terminal, exc, request, process_rows)
        try:
            _validate_process_ledger(process_rows, success=False)
        except PreparationViolation:
            terminal.primary_terminal = "INTERNAL_FAIL_CLOSED"
    return terminal, ledger


def _sanitized_started_fallback(primary_terminal: str) -> bytes:
    """Return one body-free exact31 when no private path can be trusted.

    This is used only after P1 has started but before a canonical request/path
    plan is available.  It deliberately contains no request-derived body or
    locator; the external invocation owner retains the Receipt/reconciliation
    obligation for this defensive terminal.
    """

    terminal = (
        primary_terminal
        if primary_terminal in PreparationContractV1.PRIMARY_STOP_TERMINALS
        else "INTERNAL_FAIL_CLOSED"
    )
    zero_context = canonical_sha256(
        {
            "schema_version": "g4b.untrusted.started.context.v1",
            "candidate_id": PreparationContractV1.CANDIDATE_ID,
        }
    )
    values = {
        "schema_version": PreparationContractV1.PUBLIC_RESULT_SCHEMA,
        "method_id": PreparationContractV1.METHOD_ID,
        "candidate_id": PreparationContractV1.CANDIDATE_ID,
        "authority_context_binding_sha256": zero_context,
        "session_context_binding_sha256": zero_context,
        "status": "STOP",
        "primary_terminal": terminal,
        "nested_checker_terminal": "NOT_APPLICABLE",
        "technical_primary_outcome": "BLOCKER_NARROWED",
        "activated": True,
        "consumed": False,
        "checker_execution_attempt_count": 0,
        "checker_component_status": "NOT_RUN",
        "composite_technical_result": "STOP",
        "current_session_runtime_readiness": "NOT_READY",
        "gate_b_technical_condition": "NOT_SATISFIED",
        "handoff_state": "NOT_BOUND",
        "gate_c_authorized": False,
        "cleanup_state": "UNKNOWN",
        "retention_state": "NONE",
        "technical_chain_complete": False,
        "publication_state": "NOT_ATTEMPTED",
        "durable_work_complete": False,
        "durable_current_owner_state": "UNCHANGED",
        "durable_current_owner_runtime_ready": False,
        "durable_current_owner_gate_b_closed": False,
        "durable_current_owner_readiness_credit": 0,
        "durable_current_owner_technical_credit": 0,
        "durable_current_owner_product_credit": 0,
        "durable_current_owner_primary_outcome": "BLOCKER_NARROWED",
        "automatic_progression": False,
    }
    result = {key: values[key] for key in PUBLIC_RESULT_KEYS_EXACT31}
    validate_public_result(result)
    return canonical_json_bytes(result)


def _emit_once(payload: bytes) -> None:
    if len(payload) > 65_536:
        raise PreparationViolation("PRIVACY_VIOLATION", "public result exceeds cap")
    sys.stdout.buffer.write(payload)
    sys.stdout.buffer.flush()


def _terminalize_started(
    request: dict[str, Any],
    terminal: _Terminal,
    cleanup_ledger: _CleanupLedger,
    process_rows: list[dict[str, Any]],
    path_rows: list[dict[str, Any]],
    deadline: _LifecycleDeadline,
) -> tuple[int, bytes]:
    """Run the residual-exact1 order and build the public body exactly once."""

    try:
        cleanup_state, retention_state = _cleanup(
            request,
            terminal.success,
            path_rows,
            cleanup_ledger,
            terminal=terminal,
            deadline=deadline,
        )
    except Exception:
        cleanup_state, retention_state = (
            "UNKNOWN",
            "PARTIAL_PRIVATE_STATE_RETAINED",
        )
        terminal.primary_terminal = "INTERNAL_FAIL_CLOSED"

    try:
        cleanup_sha256, _cleanup_raw = cleanup_ledger.seal()
    except Exception as exc:
        terminal.primary_terminal = "INTERNAL_FAIL_CLOSED"
        # No terminal envelope can bind final cleanup without this seal.
        # Stop before exact31 build/freeze so stdout remains empty and the
        # external owner can reconcile the fatal private-evidence failure.
        raise _TerminalEvidenceSealFailure from exc
    if not _is_sha256(cleanup_sha256):
        terminal.primary_terminal = "INTERNAL_FAIL_CLOSED"
        raise _TerminalEvidenceSealFailure

    # No exact31 bytes or hash exist before the cleanup attempt and seal above.
    _result, frozen_result, public_result_sha256 = _build_public_result_once(
        request, terminal, cleanup_state, retention_state
    )
    try:
        _seal_terminal_evidence(
            request,
            terminal,
            cleanup_state,
            retention_state,
            cleanup_sha256,
            public_result_sha256,
            process_rows,
            path_rows,
        )
        _sealed_regular_raw(request["path_plan"]["terminal_evidence"])
    except Exception as exc:
        # The exact31 bytes are already frozen and therefore must not be
        # mutated, rebuilt, or emitted out of the approved step6→step7
        # order.  The external owner reconciles the missing envelope
        # without a technical rerun.
        raise _TerminalEvidenceSealFailure from exc
    return (
        0 if terminal.success and cleanup_state == "COMPLETE" else 2,
        frozen_result,
    )


def _read_request() -> dict[str, Any]:
    raw = sys.stdin.buffer.read(_MAX_INPUT_BYTES + 1)
    if len(raw) > _MAX_INPUT_BYTES:
        raise PreparationViolation("PRIVACY_VIOLATION", "stdin exceeds limit")
    value = strict_json_from_bytes(raw)
    if not isinstance(value, dict):
        raise PreparationViolation("PRIVACY_VIOLATION", "request is not object")
    return validate_execution_request(value)


def main() -> int:
    """Execute one activated authority and emit one post-cleanup exact31 JSON."""

    process_rows: list[dict[str, Any]] = []
    path_rows: list[dict[str, Any]] = []
    deadline = _LifecycleDeadline.start()
    previous_umask = os.umask(0o077)
    try:
        repo_root = _assert_official_cli_context()
        request = _read_request()
        _append_process_row(process_rows, _p1_process_row(request, repo_root))
        terminal, cleanup_ledger = _run_lifecycle(
            request, repo_root, process_rows, path_rows, deadline
        )
        returncode, frozen_result = _terminalize_started(
            request,
            terminal,
            cleanup_ledger,
            process_rows,
            path_rows,
            deadline,
        )
        _emit_once(frozen_result)
        return returncode
    except _TerminalEvidenceSealFailure:
        return 3
    except Exception as exc:
        code = exc.code if isinstance(exc, PreparationViolation) else "INTERNAL_FAIL_CLOSED"
        try:
            _emit_once(_sanitized_started_fallback(code))
        except Exception:
            return 3
        return 2
    finally:
        os.umask(previous_umask)


if __name__ == "__main__":
    raise SystemExit(main())
