#!/usr/bin/env python3
"""One-shot bridge from G4-B preparation evidence to checker V1.

The bridge is deliberately not a checker library wrapper.  It constructs the
unchanged checker V1 request, runs the dedicated checker test and the official
checker CLI as separate child processes, validates the body-free checker
result, and returns private binding evidence to the controller.  Importing the
module has no filesystem, environment, clock, process, or network effect.
"""

from __future__ import annotations

import dataclasses
import hashlib
import os
import re
import selectors
import signal
import stat
import subprocess
import time
from typing import Any

from ai.tools.emlis_nls_v3_s11_g4b_runtime_preparation_contract_v1 import (
    PreparationContractV1,
    PreparationViolation,
    _validate_acquisition_observation,
    _validate_materialization_attestation,
    canonical_json_bytes,
    canonical_sha256,
    strict_json_from_bytes,
    validate_execution_request,
)
from ai.tools.emlis_nls_v3_s11_g4b_runtime_admission_contract_v1 import (
    ContractV1 as AdmissionContractV1,
    ContractViolation as AdmissionViolation,
    canonical_sha256 as admission_canonical_sha256,
    materialization_event_id,
    runtime_executable_locator_sha256,
    runtime_root_locator_sha256,
    validate_public_result as validate_checker_public_result,
    validate_request as validate_checker_request,
)

__all__ = ("run_admission_once",)


_CHECKER_MODULE = "ai.tools.emlis_nls_v3_s11_g4b_runtime_admission_checker_v1"
_CHECKER_TEST_MODULE = "ai.tests.test_emlis_nls_v3_s11_g4b_runtime_admission_checker_v1"
_CHECKER_TEST_RELATIVE = (
    "ai/tests/test_emlis_nls_v3_s11_g4b_runtime_admission_checker_v1.py"
)
_CHECKER_TEST_COUNT = 51
_PROCESS_TIMEOUT_P6 = 600.0
_PROCESS_TIMEOUT_P7 = 900.0
_MAX_STREAM_BYTES = 1_048_576
_RUNTIME_FILES = PreparationContractV1.RUNTIME_REGULAR_FILES
_RUNTIME_DIRECTORIES = PreparationContractV1.RUNTIME_DIRECTORIES
_RUNTIME_BYTES = PreparationContractV1.RUNTIME_AGGREGATE_BYTES
_SHA256_RE = re.compile(r"\A[0-9a-f]{64}\Z")
_CHILD_ENVIRONMENT_EXACT7 = {
    "LANG": "C.UTF-8",
    "LC_ALL": "C.UTF-8",
    "PYTHONDONTWRITEBYTECODE": "1",
    "PYTHONHASHSEED": "0",
    "PYTHONNOUSERSITE": "1",
    "PYTHONUTF8": "1",
    "PYTEST_DISABLE_PLUGIN_AUTOLOAD": "1",
}


@dataclasses.dataclass(frozen=True)
class _ChildResult:
    stage: str
    pid: int
    returncode: int
    stdout: bytes
    stderr: bytes
    termination_state: str
    argv_sha256: str
    environment_sha256: str
    cwd_binding_sha256: str
    executable_sha256: str

    def ledger_row(self, sequence: int) -> dict[str, Any]:
        return {
            "sequence": sequence,
            "stage": self.stage,
            "launch_owner": "ADMISSION_BRIDGE_V1",
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


def _check_manifest_deadline(deadline_ns: int | None) -> None:
    if deadline_ns is not None and time.monotonic_ns() >= deadline_ns:
        raise PreparationViolation(
            "ADMISSION_BRIDGE_INVALID", "runtime inventory deadline exceeded"
        )


def _file_sha256(
    path: str, limit: int = 33_554_432, deadline_ns: int | None = None
) -> str:
    digest = hashlib.sha256()
    total = 0
    descriptor = -1
    try:
        before = os.lstat(path)
        flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_CLOEXEC", 0)
        descriptor = os.open(path, flags)
        observed = os.fstat(descriptor)
        if (
            not stat.S_ISREG(before.st_mode)
            or before.st_nlink != 1
            or not stat.S_ISREG(observed.st_mode)
            or observed.st_nlink != 1
            or (before.st_dev, before.st_ino) != (observed.st_dev, observed.st_ino)
            or observed.st_size > limit
        ):
            raise PreparationViolation("ADMISSION_BRIDGE_INVALID", "source is not regular")
        initial_identity = (
            observed.st_dev,
            observed.st_ino,
            observed.st_mode,
            observed.st_nlink,
            observed.st_size,
            observed.st_mtime_ns,
        )
        while True:
            _check_manifest_deadline(deadline_ns)
            block = os.read(descriptor, 131_072)
            if not block:
                break
            total += len(block)
            if total > limit:
                raise PreparationViolation(
                    "ADMISSION_BRIDGE_INVALID", "source exceeds bridge limit"
                )
            digest.update(block)
        after = os.fstat(descriptor)
        final_identity = (
            after.st_dev,
            after.st_ino,
            after.st_mode,
            after.st_nlink,
            after.st_size,
            after.st_mtime_ns,
        )
        if final_identity != initial_identity or total != observed.st_size:
            raise PreparationViolation(
                "ADMISSION_BRIDGE_INVALID", "source changed during bounded read"
            )
    except PreparationViolation:
        raise
    except OSError as exc:
        raise PreparationViolation(
            "ADMISSION_BRIDGE_INVALID", "source observation failed"
        ) from exc
    finally:
        if descriptor >= 0:
            os.close(descriptor)
    return digest.hexdigest()


def _read_regular(path: str, limit: int = 33_554_432) -> bytes:
    try:
        observed = os.lstat(path)
        if not stat.S_ISREG(observed.st_mode) or observed.st_nlink != 1:
            raise PreparationViolation("ADMISSION_BRIDGE_INVALID", "evidence is not regular")
        with open(path, "rb") as source:
            raw = source.read(limit + 1)
    except PreparationViolation:
        raise
    except OSError as exc:
        raise PreparationViolation(
            "ADMISSION_BRIDGE_INVALID", "private evidence read failed"
        ) from exc
    if len(raw) > limit:
        raise PreparationViolation("ADMISSION_BRIDGE_INVALID", "private evidence too large")
    return raw


def _write_private_sealed(path: str, payload: bytes) -> None:
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL
    flags |= getattr(os, "O_NOFOLLOW", 0)
    descriptor = -1
    try:
        descriptor = os.open(path, flags, 0o600)
        offset = 0
        while offset < len(payload):
            written = os.write(descriptor, payload[offset:])
            if written <= 0:
                raise OSError("short private evidence write")
            offset += written
        os.fsync(descriptor)
        os.fchmod(descriptor, 0o400)
        os.fsync(descriptor)
    except OSError as exc:
        raise PreparationViolation(
            "ADMISSION_BRIDGE_INVALID", "private evidence seal failed"
        ) from exc
    finally:
        if descriptor >= 0:
            os.close(descriptor)
    parent_descriptor = -1
    try:
        parent_descriptor = os.open(os.path.dirname(path), os.O_RDONLY | os.O_DIRECTORY)
        os.fsync(parent_descriptor)
    except OSError as exc:
        raise PreparationViolation(
            "ADMISSION_BRIDGE_INVALID", "private evidence parent seal failed"
        ) from exc
    finally:
        if parent_descriptor >= 0:
            os.close(parent_descriptor)


def _terminate_process_group(process: Any) -> None:
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


def _run_direct_child(
    stage: str,
    argv: tuple[str, ...],
    *,
    cwd: str,
    environment: dict[str, str],
    stdin_payload: bytes | None,
    timeout_seconds: float,
) -> _ChildResult:
    """Run one fixed child with bounded binary capture; tests replace this helper."""

    if not argv or any(not item or "\x00" in item for item in argv):
        raise PreparationViolation("CHECKER_PROCESS_INVALID", "invalid child argv")
    try:
        process = subprocess.Popen(
            argv,
            cwd=cwd,
            env=dict(environment),
            stdin=subprocess.PIPE if stdin_payload is not None else subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            shell=False,
            text=False,
            close_fds=True,
            pass_fds=(),
            start_new_session=True,
        )
    except OSError as exc:
        terminal = (
            "CHECKER_DEDICATED_TEST_INVALID"
            if stage == "P6_CHECKER_DEDICATED_TEST"
            else "CHECKER_PROCESS_INVALID"
        )
        raise PreparationViolation(terminal, "child launch rejected") from exc
    assert process.stdout is not None and process.stderr is not None
    selector = selectors.DefaultSelector()
    stdin_offset = 0
    if stdin_payload is not None:
        assert process.stdin is not None
        try:
            os.set_blocking(process.stdin.fileno(), False)
        except OSError as exc:
            _terminate_process_group(process)
            raise PreparationViolation(
                "CHECKER_PROCESS_INVALID", "checker stdin setup failed"
            ) from exc
        selector.register(process.stdin, selectors.EVENT_WRITE, "stdin")
    selector.register(process.stdout, selectors.EVENT_READ, "stdout")
    selector.register(process.stderr, selectors.EVENT_READ, "stderr")
    captured = {"stdout": bytearray(), "stderr": bytearray()}
    deadline = time.monotonic() + timeout_seconds
    termination_state = "EXITED"
    try:
        while selector.get_map():
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                termination_state = "TIMEOUT_TERMINATED"
                _terminate_process_group(process)
                raise PreparationViolation(
                    "CHECKER_DEDICATED_TEST_INVALID"
                    if stage == "P6_CHECKER_DEDICATED_TEST"
                    else "CHECKER_PROCESS_INVALID",
                    "child timeout",
                )
            for key, _events in selector.select(min(remaining, 0.25)):
                if key.data == "stdin":
                    try:
                        count = os.write(
                            key.fileobj.fileno(),
                            stdin_payload[stdin_offset : stdin_offset + 65_536],
                        )
                    except BlockingIOError:
                        continue
                    except (BrokenPipeError, OSError) as exc:
                        _terminate_process_group(process)
                        raise PreparationViolation(
                            "CHECKER_PROCESS_INVALID", "checker stdin failed"
                        ) from exc
                    if count <= 0:
                        _terminate_process_group(process)
                        raise PreparationViolation(
                            "CHECKER_PROCESS_INVALID", "checker stdin made no progress"
                        )
                    stdin_offset += count
                    if stdin_offset == len(stdin_payload):
                        selector.unregister(key.fileobj)
                        try:
                            key.fileobj.close()
                        except OSError as exc:
                            _terminate_process_group(process)
                            raise PreparationViolation(
                                "CHECKER_PROCESS_INVALID", "checker stdin close failed"
                            ) from exc
                    continue
                block = os.read(key.fileobj.fileno(), 65_536)
                if not block:
                    selector.unregister(key.fileobj)
                    continue
                target = captured[key.data]
                if len(target) + len(block) > _MAX_STREAM_BYTES:
                    termination_state = "OUTPUT_OVERFLOW_TERMINATED"
                    _terminate_process_group(process)
                    raise PreparationViolation(
                        "CHECKER_DEDICATED_TEST_INVALID"
                        if stage == "P6_CHECKER_DEDICATED_TEST"
                        else "CHECKER_PROCESS_INVALID",
                        "child output overflow",
                    )
                target.extend(block)
        returncode = process.wait(timeout=max(0.0, deadline - time.monotonic()))
    except subprocess.TimeoutExpired as exc:
        termination_state = "TIMEOUT_TERMINATED"
        _terminate_process_group(process)
        raise PreparationViolation(
            "CHECKER_DEDICATED_TEST_INVALID"
            if stage == "P6_CHECKER_DEDICATED_TEST"
            else "CHECKER_PROCESS_INVALID",
            "child wait timeout",
        ) from exc
    finally:
        selector.close()
    return _ChildResult(
        stage=stage,
        pid=process.pid,
        returncode=returncode,
        stdout=bytes(captured["stdout"]),
        stderr=bytes(captured["stderr"]),
        termination_state=termination_state,
        argv_sha256=canonical_sha256(list(argv)),
        environment_sha256=canonical_sha256(environment),
        cwd_binding_sha256=canonical_sha256(
            {"schema_version": "g4b.cwd.binding.v1", "cwd": cwd}
        ),
        executable_sha256=_file_sha256(argv[0]),
    )


def _full_root_manifest(root: str, deadline_ns: int | None = None) -> str:
    """Hash one exact bounded regular/directory runtime inventory."""

    _check_manifest_deadline(deadline_ns)
    try:
        root_observed = os.lstat(root)
    except OSError as exc:
        raise PreparationViolation(
            "ADMISSION_BRIDGE_INVALID", "runtime root observation failed"
        ) from exc
    if not stat.S_ISDIR(root_observed.st_mode) or stat.S_ISLNK(root_observed.st_mode):
        raise PreparationViolation("ADMISSION_BRIDGE_INVALID", "runtime root is not exact directory")
    rows: list[dict[str, Any]] = []
    pending = [root]
    regular_count = 0
    directory_count = 0
    aggregate_bytes = 0
    while pending:
        _check_manifest_deadline(deadline_ns)
        directory = pending.pop()
        try:
            with os.scandir(directory) as scanner:
                entries = sorted(scanner, key=lambda item: item.name, reverse=True)
        except OSError as exc:
            raise PreparationViolation(
                "ADMISSION_BRIDGE_INVALID", "runtime inventory failed"
            ) from exc
        for entry in entries:
            _check_manifest_deadline(deadline_ns)
            relative = os.path.relpath(entry.path, root).replace(os.sep, "/")
            try:
                observed = entry.stat(follow_symlinks=False)
            except OSError as exc:
                raise PreparationViolation(
                    "ADMISSION_BRIDGE_INVALID", "runtime entry observation failed"
                ) from exc
            mode = stat.S_IMODE(observed.st_mode)
            if stat.S_ISDIR(observed.st_mode):
                directory_count += 1
                if directory_count > _RUNTIME_DIRECTORIES:
                    raise PreparationViolation(
                        "ADMISSION_BRIDGE_INVALID",
                        "runtime directory cardinality budget exceeded",
                    )
                rows.append({"kind": "directory", "mode": mode, "relative_path": relative})
                pending.append(entry.path)
            elif stat.S_ISREG(observed.st_mode):
                regular_count += 1
                if regular_count > _RUNTIME_FILES:
                    raise PreparationViolation(
                        "ADMISSION_BRIDGE_INVALID",
                        "runtime regular-file cardinality budget exceeded",
                    )
                if observed.st_size < 0 or aggregate_bytes + observed.st_size > _RUNTIME_BYTES:
                    raise PreparationViolation(
                        "ADMISSION_BRIDGE_INVALID", "runtime aggregate byte budget exceeded"
                    )
                remaining = _RUNTIME_BYTES - aggregate_bytes
                rows.append(
                    {
                        "kind": "regular",
                        "mode": mode,
                        "relative_path": relative,
                        "size": observed.st_size,
                        "raw_sha256": _file_sha256(entry.path, remaining, deadline_ns),
                    }
                )
                aggregate_bytes += observed.st_size
            else:
                raise PreparationViolation(
                    "ADMISSION_BRIDGE_INVALID", "runtime symlink or special file is forbidden"
                )
    rows.sort(key=lambda item: item["relative_path"])
    return admission_canonical_sha256(rows)


def _checker_request(
    request: dict[str, Any], materialization: dict[str, Any]
) -> dict[str, Any]:
    paths = request["path_plan"]
    runtime_root = paths["runtime_root"]
    executable = os.path.join(runtime_root, AdmissionContractV1.EXPECTED_EXECUTABLE_RELATIVE)
    checker_request = {
        "schema_version": AdmissionContractV1.REQUEST_SCHEMA,
        "authority_id": request["authority_id"],
        "observation_session_id": request["observation_session_id"],
        "materialization": {
            "event_id": materialization["event_id"],
            "procedure_ids": list(materialization["procedure_ids"]),
            "fresh_root_nonexistent_before": materialization[
                "fresh_root_nonexistent_before"
            ],
            "prior_artifact_reuse_count": materialization[
                "prior_artifact_reuse_count"
            ],
            "root": runtime_root,
            "root_locator_sha256": materialization["runtime_root_locator_sha256"],
            "expected_full_root_manifest_sha256": materialization[
                "full_runtime_root_manifest_sha256"
            ],
            "site_packages_relative": materialization["site_packages_relative"],
            "probe_cwd": paths["checker_probe_cwd"],
        },
        "runtime": {
            "executable": executable,
            "implementation": AdmissionContractV1.EXPECTED_IMPLEMENTATION,
            "python_version": AdmissionContractV1.EXPECTED_PYTHON_VERSION,
            "platform_tag": AdmissionContractV1.EXPECTED_PLATFORM_TAG,
            "resolved_interpreter_sha256": materialization[
                "resolved_interpreter_sha256"
            ],
        },
        "frozen": {
            "mashos_api_commit": request["expected_git"]["mashos_api_commit"],
            "mashos_api_tree": request["expected_git"]["mashos_api_tree"],
            "lock_raw_sha256": AdmissionContractV1.LOCK_RAW_SHA256,
            "lock_logical_sha256": AdmissionContractV1.LOCK_LOGICAL_SHA256,
            "projection_sha256": AdmissionContractV1.PROJECTION_SHA256,
            "requirements_sha256": AdmissionContractV1.REQUIREMENTS_SHA256,
            "wheel_manifest_sha256": AdmissionContractV1.WHEEL_MANIFEST_SHA256,
            "distribution_closure_sha256": AdmissionContractV1.DISTRIBUTION_CLOSURE_SHA256,
            "installed_manifest_comparator_sha256": (
                AdmissionContractV1.INSTALLED_MANIFEST_COMPARATOR_SHA256
            ),
        },
        "handoff": {
            "receiver_session_id": request["receiver_session_id"],
            "receiver_nonce": request["receiver_nonce"],
        },
    }
    try:
        validate_checker_request(checker_request)
    except AdmissionViolation as exc:
        raise PreparationViolation("ADMISSION_BRIDGE_INVALID", "checker request invalid") from exc
    if materialization_event_id(checker_request) != materialization["event_id"]:
        raise PreparationViolation("ADMISSION_BRIDGE_INVALID", "event identity mismatch")
    return checker_request


def _run_checker_test(request: dict[str, Any], checker_request: dict[str, Any]) -> _ChildResult:
    paths = request["path_plan"]
    executable = checker_request["runtime"]["executable"]
    argv = (
        executable,
        "-E",
        "-s",
        "-B",
        "-m",
        "pytest",
        "--disable-plugin-autoload",
        "-p",
        "no:cacheprovider",
        "--noconftest",
        "-c",
        paths["checker_test_pytest_ini"],
        "--basetemp=" + paths["checker_test_basetemp"],
        "--maxfail=1",
        "--tb=short",
        "--color=no",
        "-q",
        os.path.join(paths["checker_test_cwd"], _CHECKER_TEST_RELATIVE),
    )
    result = _run_direct_child(
        "P6_CHECKER_DEDICATED_TEST",
        argv,
        cwd=paths["checker_test_cwd"],
        environment=_CHILD_ENVIRONMENT_EXACT7,
        stdin_payload=None,
        timeout_seconds=_PROCESS_TIMEOUT_P6,
    )
    combined = result.stdout + b"\n" + result.stderr
    if result.returncode != 0 or re.search(rb"\b51 passed\b", combined) is None:
        raise PreparationViolation(
            "CHECKER_DEDICATED_TEST_INVALID", "dedicated test did not pass exact51"
        )
    return result


def _run_checker(request: dict[str, Any], checker_request: dict[str, Any]) -> _ChildResult:
    paths = request["path_plan"]
    executable = checker_request["runtime"]["executable"]
    return _run_direct_child(
        "P7_OFFICIAL_CHECKER",
        (
            executable,
            "-E",
            "-s",
            "-S",
            "-B",
            "-m",
            _CHECKER_MODULE,
        ),
        cwd=paths["checker_test_cwd"],
        environment=_CHILD_ENVIRONMENT_EXACT7,
        stdin_payload=canonical_json_bytes(checker_request),
        timeout_seconds=_PROCESS_TIMEOUT_P7,
    )


def _git_blob_oid(raw: bytes) -> str:
    prefix = f"blob {len(raw)}\0".encode("ascii")
    return hashlib.sha1(prefix + raw, usedforsecurity=False).hexdigest()


def _load_private_json(path: str) -> tuple[dict[str, Any], bytes]:
    raw = _read_regular(path)
    value = strict_json_from_bytes(raw, require_final_lf=True)
    if not isinstance(value, dict):
        raise PreparationViolation("ADMISSION_BRIDGE_INVALID", "private evidence not object")
    return value, raw


def _composite_binding(
    request: dict[str, Any],
    materialization: dict[str, Any],
    checker_request: dict[str, Any],
    checker_result: dict[str, Any],
    handoff: dict[str, Any],
) -> dict[str, Any]:
    paths = request["path_plan"]
    acquisition, acquisition_raw = _load_private_json(paths["acquisition_observation"])
    acquisition = _validate_acquisition_observation(request, acquisition)
    transport_raw = _read_regular(paths["private_transport_binding_observation"])
    repo_root = paths["controller_test_cwd"]
    lock_path = os.path.join(
        repo_root,
        "ai/configs/emlis_nls_v3_s11_g4b_runtime_preparation_exact5_lock_v1.json",
    )
    lock_raw = _read_regular(lock_path, 16_384)
    if hashlib.sha256(lock_raw).hexdigest() != getattr(
        PreparationContractV1, "DERIVED_LOCK_RAW_SHA256", ""
    ):
        raise PreparationViolation("ADMISSION_BRIDGE_INVALID", "derived lock drift")
    preparation_source = canonical_json_bytes.__code__.co_filename
    attestation = request["egress_attestation"]
    source_observation_sha256 = acquisition.get(
        "egress_attestation_source_observation_sha256"
    )
    if not isinstance(source_observation_sha256, str) or _SHA256_RE.fullmatch(
        source_observation_sha256
    ) is None:
        raise PreparationViolation(
            "ADMISSION_BRIDGE_INVALID", "egress source observation binding absent"
        )
    composite = {
        "schema_version": PreparationContractV1.COMPOSITE_BINDING_SCHEMA,
        "authority_id": request["authority_id"],
        "observation_session_id": request["observation_session_id"],
        "formal_lock_raw_sha256": AdmissionContractV1.LOCK_RAW_SHA256,
        "formal_lock_logical_sha256": AdmissionContractV1.LOCK_LOGICAL_SHA256,
        "derived_lock_git_blob": _git_blob_oid(lock_raw),
        "derived_lock_raw_sha256": hashlib.sha256(lock_raw).hexdigest(),
        "derived_lock_logical_sha256": getattr(
            PreparationContractV1, "DERIVED_LOCK_LOGICAL_SHA256"
        ),
        "preparation_contract_raw_sha256": _file_sha256(preparation_source),
        "stable_authority_approval_binding_sha256": request[
            "stable_authority_approval_binding_sha256"
        ],
        "execution_request_sha256": canonical_sha256(request),
        "projection_sha256": PreparationContractV1.PROJECTION_SHA256,
        "requirements_sha256": PreparationContractV1.REQUIREMENTS_SHA256,
        "accepted_wheel_manifest_sha256": materialization[
            "accepted_wheel_manifest_sha256"
        ],
        "wheel_record_manifest_sha256": materialization[
            "wheel_record_manifest_sha256"
        ],
        "distribution_closure_sha256": materialization[
            "distribution_closure_sha256"
        ],
        "issuer_provenance_binding_sha256": attestation[
            "issuer_provenance_binding_sha256"
        ],
        "egress_attestation_source_observation_sha256": source_observation_sha256,
        "egress_attestation_sha256": request["egress_attestation_sha256"],
        "transport_binding_observation_sha256": hashlib.sha256(transport_raw).hexdigest(),
        "acquisition_observation_sha256": hashlib.sha256(acquisition_raw).hexdigest(),
        "materialization_attestation_sha256": canonical_sha256(materialization),
        "checker_request_sha256": canonical_sha256(checker_request),
        "checker_result_sha256": canonical_sha256(checker_result),
        "handoff_binding_sha256": handoff["handoff_binding_sha256"],
    }
    if frozenset(composite) != PreparationContractV1.COMPOSITE_BINDING_KEYS:
        raise PreparationViolation("ADMISSION_BRIDGE_INVALID", "composite keyset drift")
    return composite


def _checker_handoff_preimage(
    request: dict[str, Any],
    materialization: dict[str, Any],
    checker_result: dict[str, Any],
) -> dict[str, Any]:
    """Reconstruct the unchanged checker V1 exact18 handoff preimage."""

    paths = request["path_plan"]
    executable = os.path.join(
        paths["runtime_root"], AdmissionContractV1.EXPECTED_EXECUTABLE_RELATIVE
    )
    try:
        observed = os.lstat(executable)
    except OSError as exc:
        raise PreparationViolation(
            "HANDOFF_BINDING_INVALID", "runtime entrypoint stat failed"
        ) from exc
    if not stat.S_ISREG(observed.st_mode) or observed.st_nlink != 1:
        raise PreparationViolation(
            "HANDOFF_BINDING_INVALID", "runtime entrypoint is not a single regular file"
        )
    entrypoint_control_identity_sha256 = canonical_sha256(
        {
            "relative_path": AdmissionContractV1.EXPECTED_EXECUTABLE_RELATIVE,
            "stat": [
                observed.st_dev,
                observed.st_ino,
                stat.S_IMODE(observed.st_mode),
                observed.st_size,
                observed.st_mtime_ns,
            ],
            "raw_sha256": _file_sha256(executable),
        }
    )
    preimage = {
        "schema_version": AdmissionContractV1.HANDOFF_SCHEMA,
        "handoff_claim": AdmissionContractV1.HANDOFF_CLAIM,
        "private_locator_holder": "CALLER_REQUEST_CONTEXT",
        "consumer_observed": False,
        "observation_session_id": request["observation_session_id"],
        "receiver_session_id": request["receiver_session_id"],
        "receiver_nonce": request["receiver_nonce"],
        "mashos_api_commit": request["expected_git"]["mashos_api_commit"],
        "mashos_api_tree": request["expected_git"]["mashos_api_tree"],
        "freshness_evidence_class": AdmissionContractV1.FRESHNESS_EVIDENCE_CLASS,
        "freshness_claim_limit": AdmissionContractV1.FRESHNESS_CLAIM_LIMIT,
        "materialization_event_id": materialization["event_id"],
        "runtime_root_locator_sha256": materialization["runtime_root_locator_sha256"],
        "runtime_executable_locator_sha256": runtime_executable_locator_sha256(executable),
        "expected_full_root_manifest_sha256": materialization[
            "full_runtime_root_manifest_sha256"
        ],
        "runtime_instance_observation_id": checker_result[
            "runtime_instance_observation_id"
        ],
        "runtime_readiness_observation_id": checker_result[
            "runtime_readiness_observation_id"
        ],
        "entrypoint_control_identity_sha256": entrypoint_control_identity_sha256,
    }
    if frozenset(preimage) != PreparationContractV1.HANDOFF_BINDING_KEYS:
        raise PreparationViolation("HANDOFF_BINDING_INVALID", "handoff preimage keyset drift")
    return preimage


def _validate_checker_handoff_binding(
    request: dict[str, Any],
    materialization: dict[str, Any],
    checker_result: dict[str, Any],
) -> None:
    expected = canonical_sha256(
        _checker_handoff_preimage(request, materialization, checker_result)
    )
    if checker_result.get("handoff_binding_sha256") != expected:
        raise PreparationViolation(
            "HANDOFF_BINDING_INVALID", "checker handoff exact18 digest mismatch"
        )


def _bind_p7_attempt_failure(
    error: PreparationViolation,
    p6: _ChildResult,
    p7: _ChildResult | None = None,
    *,
    nested_terminal: str = "NOT_AVAILABLE",
) -> PreparationViolation:
    """Preserve the P7 attempt and every available process row on failure."""

    error.checker_execution_attempt_count = 1
    error.checker_component_status = "STOP"
    error.nested_checker_terminal = nested_terminal
    rows = [p6.ledger_row(0)]
    if p7 is not None:
        rows.append(p7.ledger_row(1))
    error.process_rows = rows
    return error


def run_admission_once(
    request: dict[str, Any], materialization_attestation: dict[str, Any]
) -> dict[str, Any]:
    """Run P6 then P7 once and return private controller evidence.

    The returned dictionary is intentionally private and is not a public
    result schema.  It gives the controller the exact process rows, unchanged
    checker result, current-session handoff, and composite exact25 digest.
    """

    request = validate_execution_request(request)
    materialization_attestation = _validate_materialization_attestation(
        request, materialization_attestation
    )
    persisted_materialization, _persisted_raw = _load_private_json(
        request["path_plan"]["materialization_attestation"]
    )
    if persisted_materialization != materialization_attestation:
        raise PreparationViolation(
            "MATERIALIZATION_IDENTITY_INVALID",
            "persisted materialization attestation mismatches admitted object",
        )
    if (
        materialization_attestation["installed_file_manifest_sha256"]
        != AdmissionContractV1.INSTALLED_MANIFEST_COMPARATOR_SHA256
    ):
        raise PreparationViolation(
            "MATERIALIZATION_IDENTITY_INVALID", "installed manifest comparator mismatch"
        )
    checker_request = _checker_request(request, materialization_attestation)
    expected_manifest = materialization_attestation["full_runtime_root_manifest_sha256"]
    runtime_root = request["path_plan"]["runtime_root"]
    admission_deadline_ns = time.monotonic_ns() + int(
        (_PROCESS_TIMEOUT_P6 + _PROCESS_TIMEOUT_P7) * 1_000_000_000
    )
    if _full_root_manifest(runtime_root, admission_deadline_ns) != expected_manifest:
        raise PreparationViolation("ADMISSION_BRIDGE_INVALID", "pre-P6 root drift")

    request_payload = canonical_json_bytes(checker_request)
    _write_private_sealed(request["path_plan"]["checker_request"], request_payload)
    p6 = _run_checker_test(request, checker_request)
    if _full_root_manifest(runtime_root, admission_deadline_ns) != expected_manifest:
        raise PreparationViolation("ADMISSION_BRIDGE_INVALID", "P6 changed runtime root")
    try:
        p7 = _run_checker(request, checker_request)
    except PreparationViolation as exc:
        _bind_p7_attempt_failure(exc, p6)
        raise
    try:
        post_p7_manifest = _full_root_manifest(runtime_root, admission_deadline_ns)
    except PreparationViolation as exc:
        _bind_p7_attempt_failure(exc, p6, p7)
        raise
    if post_p7_manifest != expected_manifest:
        raise _bind_p7_attempt_failure(
            PreparationViolation("ADMISSION_BRIDGE_INVALID", "P7 changed runtime root"),
            p6,
            p7,
        )
    try:
        if p7.returncode not in (0, 2, 3):
            raise PreparationViolation(
                "CHECKER_PROCESS_INVALID", "checker return code invalid"
            )
        checker_result = strict_json_from_bytes(p7.stdout)
        validate_checker_public_result(checker_result)
    except (PreparationViolation, AdmissionViolation) as exc:
        failure = PreparationViolation("CHECKER_PROCESS_INVALID", "checker result invalid")
        raise _bind_p7_attempt_failure(failure, p6, p7) from exc
    if not isinstance(checker_result, dict):
        raise _bind_p7_attempt_failure(
            PreparationViolation("CHECKER_PROCESS_INVALID", "checker result not object"),
            p6,
            p7,
        )
    try:
        if (
            checker_result.get("status") == "VALID" and p7.returncode != 0
        ) or (
            checker_result.get("status") == "STOP" and p7.returncode not in (2, 3)
        ):
            raise PreparationViolation(
                "CHECKER_PROCESS_INVALID", "checker status and return code diverge"
            )
        _write_private_sealed(
            request["path_plan"]["checker_result"], canonical_json_bytes(checker_result)
        )
        if checker_result.get("status") != "VALID":
            failure = PreparationViolation(
                "CHECKER_RETURNED_TYPED_STOP", "existing checker returned typed STOP"
            )
            raise _bind_p7_attempt_failure(
                failure,
                p6,
                p7,
                nested_terminal=checker_result.get("terminal", "UNKNOWN"),
            )

        _validate_checker_handoff_binding(
            request, materialization_attestation, checker_result
        )
        handoff = {
            "schema_version": PreparationContractV1.PRIVATE_HANDOFF_SCHEMA,
            "authority_id": request["authority_id"],
            "observation_session_id": request["observation_session_id"],
            "receiver_session_id": request["receiver_session_id"],
            "receiver_nonce": request["receiver_nonce"],
            "materialization_event_id": materialization_attestation["event_id"],
            "runtime_root_locator_sha256": materialization_attestation[
                "runtime_root_locator_sha256"
            ],
            "runtime_executable_locator_sha256": runtime_executable_locator_sha256(
                checker_request["runtime"]["executable"]
            ),
            "expected_full_root_manifest_sha256": expected_manifest,
            "runtime_readiness_observation_id": checker_result[
                "runtime_readiness_observation_id"
            ],
            "handoff_binding_sha256": checker_result["handoff_binding_sha256"],
            "consumed": False,
        }
        if (
            frozenset(handoff) != PreparationContractV1.PRIVATE_HANDOFF_KEYS
            or handoff["runtime_root_locator_sha256"]
            != runtime_root_locator_sha256(runtime_root)
        ):
            raise PreparationViolation("HANDOFF_BINDING_INVALID", "handoff binding invalid")
        composite = _composite_binding(
            request,
            materialization_attestation,
            checker_request,
            checker_result,
            handoff,
        )
        _write_private_sealed(
            request["path_plan"]["private_handoff"], canonical_json_bytes(handoff)
        )
    except PreparationViolation as exc:
        if not hasattr(exc, "checker_execution_attempt_count"):
            _bind_p7_attempt_failure(exc, p6, p7)
        raise
    return {
        "checker_request": checker_request,
        "checker_result": checker_result,
        "private_handoff": handoff,
        "composite_binding": composite,
        "composite_binding_sha256": canonical_sha256(composite),
        "checker_execution_attempt_count": 1,
        "nested_checker_terminal": checker_result["terminal"],
        "checker_component_status": "VALID",
        "process_rows": [p6.ledger_row(0), p7.ledger_row(1)],
    }
