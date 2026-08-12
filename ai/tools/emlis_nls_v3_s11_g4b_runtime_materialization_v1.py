#!/usr/bin/env python3
"""Fail-closed offline materialization for the G4-B preparation family."""

from __future__ import annotations

import base64
import csv
import email.policy
import hashlib
import io
import os
import posixpath
import selectors
import signal
import stat
import subprocess
import threading
import time
import venv
import zipfile
from email.parser import BytesParser
from typing import Any

from ai.tools.emlis_nls_v3_s11_g4b_runtime_preparation_contract_v1 import (
    PreparationContractV1,
    PreparationViolation,
    canonical_file_bytes,
    canonical_json_bytes,
    canonical_sha256,
    validate_execution_request,
)

__all__ = ("materialize_once",)

_MAX_OUTPUT = 1_048_576
_PROCESS_TIMEOUT = 300
_RUNTIME_FILES = 4096
_RUNTIME_DIRECTORIES = 1024
_RUNTIME_BYTES = 536_870_912
_PROCESS_PROJECTION_KEYS_EXACT14 = (
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


def _check_deadline(deadline_ns: int | None) -> None:
    if deadline_ns is not None and time.monotonic_ns() >= deadline_ns:
        _process_fail("in-process materialization deadline exceeded")


def _alarm_handler(_signum: int, _frame: object) -> None:
    _process_fail("in-process materialization hard deadline exceeded")


def _set_phase_alarm(seconds: float) -> None:
    if threading.current_thread() is threading.main_thread() and hasattr(signal, "setitimer"):
        signal.setitimer(signal.ITIMER_REAL, seconds)


def _fail(detail: str) -> None:
    raise PreparationViolation("MATERIALIZATION_IDENTITY_INVALID", detail)


def _process_fail(detail: str) -> None:
    raise PreparationViolation("MATERIALIZATION_PROCESS_INVALID", detail)


def _sha(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _canonical_file(path: str, value: Any) -> None:
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0)
    try:
        fd = os.open(path, flags, 0o600)
        try:
            payload = canonical_file_bytes(value)
            view = memoryview(payload)
            while view:
                count = os.write(fd, view)
                if count <= 0:
                    _process_fail("private evidence write made no progress")
                view = view[count:]
            os.fsync(fd)
            os.fchmod(fd, 0o400)
            os.fsync(fd)
        finally:
            os.close(fd)
    except PreparationViolation:
        raise
    except OSError:
        _process_fail("exclusive private evidence creation failed")


def _read_regular(
    path: str, limit: int = 16_777_216, deadline_ns: int | None = None
) -> tuple[bytes, os.stat_result]:
    flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_CLOEXEC", 0)
    try:
        fd = os.open(path, flags)
        try:
            observed = os.fstat(fd)
            if not stat.S_ISREG(observed.st_mode) or observed.st_nlink != 1:
                _fail("required object is not a single regular file")
            chunks: list[bytes] = []
            total = 0
            while True:
                _check_deadline(deadline_ns)
                block = os.read(fd, 131_072)
                if not block:
                    break
                total += len(block)
                if total > limit:
                    _fail("regular-file byte budget exceeded")
                chunks.append(block)
            return b"".join(chunks), observed
        finally:
            os.close(fd)
    except PreparationViolation:
        raise
    except OSError:
        _fail("required regular file is unreadable")
    raise AssertionError


def _normalized_name(value: str) -> str:
    import re

    return re.sub(r"[-_.]+", "-", value).lower()


def _record_digest(value: str) -> str:
    pieces = value.split("=", 1)
    if len(pieces) != 2 or pieces[0] != "sha256":
        _fail("RECORD digest algorithm is not sha256")
    encoded = pieces[1]
    try:
        decoded = base64.b64decode(
            encoded + "=" * ((4 - len(encoded) % 4) % 4),
            altchars=b"-_",
            validate=True,
        )
    except (ValueError, TypeError):
        _fail("RECORD digest is malformed")
    if len(decoded) != 32 or base64.urlsafe_b64encode(decoded).rstrip(b"=").decode() != encoded:
        _fail("RECORD digest is noncanonical")
    return decoded.hex()


def _safe_zip_name(name: str) -> str:
    if (
        not name
        or name.startswith("/")
        or "\\" in name
        or "\x00" in name
        or any(ord(character) < 32 or ord(character) == 127 for character in name)
    ):
        _fail("wheel member path is unsafe")
    stripped = name[:-1] if name.endswith("/") else name
    if not stripped or posixpath.normpath(stripped) != stripped or stripped.startswith("../"):
        _fail("wheel member path changes under normalization")
    return stripped


def _wheel_record(
    lock_row: dict[str, Any], path: str, deadline_ns: int | None = None
) -> dict[str, str]:
    raw, _observed = _read_regular(path, deadline_ns=deadline_ns)
    if _sha(raw) != lock_row["wheel_sha256"]:
        _fail("wheel raw hash mismatches lock")
    try:
        archive = zipfile.ZipFile(io.BytesIO(raw), "r")
    except (OSError, zipfile.BadZipFile):
        _fail("wheel ZIP is invalid")
    with archive:
        infos = archive.infolist()
        if not infos or len(infos) > 4096:
            _fail("wheel ZIP member cardinality is invalid")
        if sum(item.file_size for item in infos) > 134_217_728:
            _fail("wheel uncompressed budget exceeded")
        seen: set[str] = set()
        payloads: dict[str, bytes] = {}
        for info in infos:
            _check_deadline(deadline_ns)
            name = _safe_zip_name(info.filename)
            if name in seen:
                _fail("duplicate wheel member")
            seen.add(name)
            unix_mode = info.external_attr >> 16
            file_type = stat.S_IFMT(unix_mode)
            if file_type not in (0, stat.S_IFREG, stat.S_IFDIR) or stat.S_ISLNK(unix_mode):
                _fail("wheel symlink or special member is forbidden")
            if info.flag_bits & 0x1 or info.compress_size > 16_777_216:
                _fail("encrypted or oversized wheel member is forbidden")
            if not info.is_dir():
                try:
                    chunks: list[bytes] = []
                    observed_size = 0
                    with archive.open(info, "r") as member:
                        while True:
                            _check_deadline(deadline_ns)
                            block = member.read(131_072)
                            if not block:
                                break
                            observed_size += len(block)
                            if observed_size > info.file_size:
                                _fail("wheel member expands beyond declared size")
                            chunks.append(block)
                    if observed_size != info.file_size:
                        _fail("wheel member size mismatches ZIP directory")
                    payloads[name] = b"".join(chunks)
                except (OSError, RuntimeError, zipfile.BadZipFile):
                    _fail("wheel member read failed")

        dist_info = [
            name.rsplit("/", 1)[0]
            for name in payloads
            if name.endswith(".dist-info/METADATA")
        ]
        if len(dist_info) != 1:
            _fail("wheel METADATA cardinality is not exact1")
        prefix = dist_info[0]
        metadata_name = prefix + "/METADATA"
        record_name = prefix + "/RECORD"
        if record_name not in payloads:
            _fail("wheel RECORD is absent")
        metadata = BytesParser(policy=email.policy.compat32).parsebytes(payloads[metadata_name])
        if (
            _normalized_name(str(metadata.get("Name", "")))
            != lock_row["normalized_distribution_name"]
            or str(metadata.get("Version", "")) != lock_row["distribution_version"]
            or list(metadata.get_all("Requires-Dist", [])) != lock_row["requires_dist"]
        ):
            _fail("wheel METADATA mismatches the derived lock")
        record_raw = payloads[record_name]
        if _sha(record_raw) != lock_row["wheel_record_sha256"]:
            _fail("wheel RECORD raw identity mismatches lock")
        try:
            rows = list(csv.reader(io.StringIO(record_raw.decode("utf-8", "strict"), newline="")))
        except (UnicodeError, csv.Error):
            _fail("wheel RECORD is malformed")
        claims: set[str] = set()
        self_count = 0
        for row in rows:
            _check_deadline(deadline_ns)
            if len(row) != 3:
                _fail("wheel RECORD row is malformed")
            name, digest, size = row
            name = _safe_zip_name(name)
            if name in claims:
                _fail("wheel RECORD has a duplicate claim")
            claims.add(name)
            if name == record_name:
                self_count += 1
                if digest or size:
                    _fail("wheel RECORD self row must have empty hash and size")
                continue
            if name not in payloads or not digest or not size:
                _fail("wheel RECORD claim is missing payload/hash/size")
            try:
                expected_size = int(size, 10)
            except ValueError:
                _fail("wheel RECORD size is invalid")
            if size != str(expected_size) or expected_size != len(payloads[name]):
                _fail("wheel RECORD size mismatches")
            if _record_digest(digest) != _sha(payloads[name]):
                _fail("wheel RECORD digest mismatches")
        if self_count != 1 or claims != set(payloads):
            _fail("wheel RECORD closure does not equal ZIP regular members")

        top_levels: set[str] = set()
        for name in payloads:
            first = name.split("/", 1)[0]
            if first.endswith(".dist-info") or first.endswith(".data"):
                continue
            if "/" in name:
                top_levels.add(first)
            elif first.endswith(".py"):
                top_levels.add(first[:-3])
        expected_top = set(lock_row["top_level_imports"])
        if top_levels != expected_top:
            _fail("wheel top-level import set mismatches lock")
    return {
        "wheel_filename": lock_row["wheel_filename"],
        "wheel_sha256": lock_row["wheel_sha256"],
        "wheel_record_sha256": lock_row["wheel_record_sha256"],
    }


def _offline_argv(request: dict[str, Any]) -> list[str]:
    plan = request["path_plan"]
    return [
        request["control_runtime"]["executable"], "-I", "-B", "-m", "pip",
        "--isolated", "--disable-pip-version-check", "--no-input", "--no-color",
        "--no-python-version-warning", "--timeout", "15", "--retries", "0",
        "--resume-retries", "0", "--keyring-provider", "disabled", "--python",
        os.path.join(plan["runtime_root"], "bin", "python"), "install", "--no-index",
        "--find-links", plan["wheel_root"], "--no-cache-dir", "--progress-bar", "off",
        "--only-binary=:all:", "--no-deps", "--require-hashes", "--no-compile",
        "--requirement", plan["requirements_file_outside_runtime"],
    ]


def _offline_environment(request: dict[str, Any]) -> dict[str, str]:
    temporary = request["path_plan"]["process_temp_root"]
    return {
        "LANG": "C.UTF-8", "LC_ALL": "C.UTF-8", "NETRC": "/dev/null",
        "PIP_CONFIG_FILE": "/dev/null", "PYTHONDONTWRITEBYTECODE": "1",
        "PYTHONNOUSERSITE": "1", "TEMP": temporary, "TMP": temporary, "TMPDIR": temporary,
    }


def _normalize_cpython_linux_venv_lib64(
    runtime_root: str, deadline_ns: int | None = None
) -> None:
    """Remove only CPython/Linux's exact ``lib64 -> lib`` venv alias.

    The admitted root manifest forbids symlinks.  CPython creates this one
    platform alias even when ``EnvBuilder(symlinks=False)`` is selected, so it
    is normalized once before P4.  An absent, changed, or non-symlink alias is
    structural drift and is never silently accepted.
    """

    library = os.path.join(runtime_root, "lib")
    alias = os.path.join(runtime_root, "lib64")
    try:
        root_observed = os.lstat(runtime_root)
        library_observed = os.lstat(library)
        alias_observed = os.lstat(alias)
        target = os.readlink(alias)
    except OSError:
        _fail("CPython Linux venv lib64 alias is absent or unreadable")
    if (
        not stat.S_ISDIR(root_observed.st_mode)
        or stat.S_ISLNK(root_observed.st_mode)
        or not stat.S_ISDIR(library_observed.st_mode)
        or stat.S_ISLNK(library_observed.st_mode)
        or not stat.S_ISLNK(alias_observed.st_mode)
        or target != "lib"
    ):
        _fail("CPython Linux venv lib64 alias is not exact lib64 -> lib")
    for directory, dirs, files in os.walk(runtime_root, topdown=True, followlinks=False):
        _check_deadline(deadline_ns)
        dirs.sort()
        files.sort()
        for name in dirs + files:
            path = os.path.join(directory, name)
            try:
                observed = os.lstat(path)
            except OSError:
                _fail("CPython Linux venv entry changed during lib64 normalization")
            if stat.S_ISLNK(observed.st_mode) and path != alias:
                _fail("CPython Linux venv contains a non-lib64 symlink")
            if not (
                stat.S_ISDIR(observed.st_mode)
                or stat.S_ISREG(observed.st_mode)
                or stat.S_ISLNK(observed.st_mode)
            ):
                _fail("CPython Linux venv contains a special entry before P4")
    try:
        os.unlink(alias)
    except OSError:
        _process_fail("CPython Linux venv lib64 alias normalization failed")
    if os.path.lexists(alias):
        _process_fail("CPython Linux venv lib64 alias remained after normalization")


def _materialization_process_projection(
    request: dict[str, Any],
    *,
    runtime_executable_locator_sha256: str,
    resolved_interpreter_sha256: str,
    process_evidence: dict[str, Any],
) -> list[dict[str, Any]]:
    """Build the canonical exact2 P4/P5 exact14 controller projection."""

    required_evidence = {
        "pid",
        "returncode",
        "executable_sha256",
        "argv_sha256",
        "environment_sha256",
        "cwd_binding_sha256",
        "stdout_sha256",
        "stdout_bytes",
        "stderr_sha256",
        "stderr_bytes",
        "termination_state",
    }
    if set(process_evidence) != required_evidence:
        _process_fail("P4 private process evidence schema is not exact11")
    digest_fields = (
        "executable_sha256",
        "argv_sha256",
        "environment_sha256",
        "cwd_binding_sha256",
        "stdout_sha256",
        "stderr_sha256",
    )
    expected_cwd_binding = canonical_sha256(
        {
            "schema_version": "g4b.cwd.binding.v1",
            "cwd": request["path_plan"]["controller_test_cwd"],
        }
    )
    if (
        type(process_evidence["pid"]) is not int
        or process_evidence["pid"] <= 0
        or process_evidence["returncode"] != 0
        or process_evidence["stdout_bytes"] < 0
        or process_evidence["stderr_bytes"] < 0
        or process_evidence["executable_sha256"]
        != request["control_runtime"]["resolved_interpreter_sha256"]
        or process_evidence["cwd_binding_sha256"] != expected_cwd_binding
        or process_evidence["termination_state"] != "EXITED_WITH_PINNED_P5_SOURCE_EDGE"
        or any(
            type(process_evidence[key]) is not str
            or len(process_evidence[key]) != 64
            or any(character not in "0123456789abcdef" for character in process_evidence[key])
            for key in digest_fields
        )
    ):
        _process_fail("P4 private process evidence identity is invalid")
    p4 = {
        "sequence": 0,
        "stage": "P4_CONTROL_PIP_OFFLINE_INSTALL",
        "launch_owner": "MATERIALIZATION_V1",
        "executable_sha256": process_evidence["executable_sha256"],
        "argv_sha256": process_evidence["argv_sha256"],
        "environment_sha256": process_evidence["environment_sha256"],
        "cwd_binding_sha256": process_evidence["cwd_binding_sha256"],
        "pid_or_source_edge": str(process_evidence["pid"]),
        "returncode": process_evidence["returncode"],
        "stdout_sha256": process_evidence["stdout_sha256"],
        "stdout_bytes": process_evidence["stdout_bytes"],
        "stderr_sha256": process_evidence["stderr_sha256"],
        "stderr_bytes": process_evidence["stderr_bytes"],
        "termination_state": process_evidence["termination_state"],
    }
    p5_descriptor = {
        "schema_version": "g4b.p5.source_bound.argv.v1",
        "p4_argv_sha256": p4["argv_sha256"],
        "pip_runner_raw_sha256": PreparationContractV1.PIP_RUNNER_SHA256,
        "runtime_executable_locator_sha256": runtime_executable_locator_sha256,
    }
    p5 = {
        "sequence": 1,
        "stage": "P5_TARGET_INTERPRETER_PIP_REEXEC",
        "launch_owner": "PINNED_PIP_26_0_1_SOURCE_EDGE",
        "executable_sha256": resolved_interpreter_sha256,
        "argv_sha256": canonical_sha256(p5_descriptor),
        "environment_sha256": canonical_sha256(
            {
                "schema_version": "g4b.p5.source_bound.environment.v1",
                "p4_environment_sha256": p4["environment_sha256"],
                "pip_running_in_subprocess": "1",
            }
        ),
        "cwd_binding_sha256": p4["cwd_binding_sha256"],
        "pid_or_source_edge": PreparationContractV1.P5_STATIC_PROOF_STATE,
        "returncode": p4["returncode"],
        "stdout_sha256": p4["stdout_sha256"],
        "stdout_bytes": p4["stdout_bytes"],
        "stderr_sha256": p4["stderr_sha256"],
        "stderr_bytes": p4["stderr_bytes"],
        "termination_state": "EXITED_IN_P4_PROCESS_GROUP_PID_UNOBSERVED_SOURCE_BOUND",
    }
    projection = [p4, p5]
    if any(tuple(row) != _PROCESS_PROJECTION_KEYS_EXACT14 for row in projection):
        _process_fail("P4/P5 process projection schema is not exact14")
    return projection


def _terminate(process: subprocess.Popen[bytes]) -> None:
    try:
        os.killpg(process.pid, signal.SIGTERM)
        process.wait(timeout=5)
    except (OSError, subprocess.TimeoutExpired):
        try:
            os.killpg(process.pid, signal.SIGKILL)
        except OSError:
            pass
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            pass


def _file_digest(
    path: str, deadline_ns: int | None = None, limit: int = _RUNTIME_BYTES
) -> tuple[str, int]:
    digest = hashlib.sha256()
    size = 0
    flags = os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_CLOEXEC", 0)
    try:
        descriptor = os.open(path, flags)
        observed = os.fstat(descriptor)
        if not stat.S_ISREG(observed.st_mode) or observed.st_nlink != 1:
            os.close(descriptor)
            _fail("runtime payload is not a single regular file")
        with os.fdopen(descriptor, "rb", closefd=True) as handle:
            while True:
                _check_deadline(deadline_ns)
                block = handle.read(131_072)
                if not block:
                    break
                size += len(block)
                if size > limit:
                    _fail("runtime regular-file byte budget exceeded")
                digest.update(block)
    except PreparationViolation:
        raise
    except OSError:
        _fail("runtime regular file cannot be read without following links")
    return digest.hexdigest(), size


def _claim_path(root: str, site: str, raw_path: str) -> tuple[str, str]:
    if (
        not raw_path
        or raw_path.startswith("/")
        or "\\" in raw_path
        or "\x00" in raw_path
        or posixpath.normpath(raw_path) != raw_path
    ):
        _fail("installed RECORD path is unsafe or noncanonical")
    name = raw_path
    candidate = os.path.abspath(os.path.join(site, *name.split("/")))
    if os.path.commonpath((root, candidate)) != root:
        _fail("installed RECORD claim escapes runtime")
    return name, candidate


def _runtime_inventory(
    root: str, deadline_ns: int | None = None
) -> tuple[list[dict[str, Any]], dict[str, dict[str, Any]]]:
    """Return one bounded, no-follow inventory for every runtime descendant."""

    try:
        root_observed = os.lstat(root)
    except OSError:
        _fail("runtime root is unavailable")
    if (
        os.path.realpath(root) != os.path.abspath(root)
        or not stat.S_ISDIR(root_observed.st_mode)
        or stat.S_ISLNK(root_observed.st_mode)
    ):
        _fail("runtime root identity is invalid")
    rows: list[dict[str, Any]] = []
    by_path: dict[str, dict[str, Any]] = {}
    regular_count = 0
    directory_count = 0
    aggregate_bytes = 0
    for directory, dirs, files in os.walk(root, topdown=True, followlinks=False):
        _check_deadline(deadline_ns)
        dirs.sort()
        files.sort()
        for name in dirs + files:
            path = os.path.join(directory, name)
            relative = os.path.relpath(path, root).replace(os.sep, "/")
            try:
                observed = os.lstat(path)
            except OSError:
                _fail("runtime inventory entry changed during observation")
            mode = stat.S_IMODE(observed.st_mode)
            if stat.S_ISLNK(observed.st_mode):
                _fail("runtime symlink is forbidden")
            if stat.S_ISDIR(observed.st_mode):
                directory_count += 1
                if directory_count > _RUNTIME_DIRECTORIES:
                    _fail("runtime directory cardinality budget exceeded")
                row: dict[str, Any] = {
                    "kind": "directory", "mode": mode, "relative_path": relative,
                }
            elif stat.S_ISREG(observed.st_mode):
                regular_count += 1
                if regular_count > _RUNTIME_FILES:
                    _fail("runtime regular-file cardinality budget exceeded")
                raw_sha, size = _file_digest(path, deadline_ns)
                aggregate_bytes += size
                if aggregate_bytes > _RUNTIME_BYTES:
                    _fail("runtime aggregate byte budget exceeded")
                row = {
                    "kind": "regular", "mode": mode, "relative_path": relative,
                    "size": size, "raw_sha256": raw_sha,
                }
            else:
                _fail("runtime special file is forbidden")
            if relative in by_path:
                _fail("runtime inventory path is duplicated")
            rows.append(row)
            by_path[relative] = row
    rows.sort(key=lambda item: item["relative_path"])
    return rows, by_path


def _fresh_venv_baseline(
    root: str, deadline_ns: int | None = None
) -> dict[str, dict[str, Any]]:
    """Freeze the normalized fresh-venv inventory before the only P4 launch."""

    _rows, by_path = _runtime_inventory(root, deadline_ns)
    return {relative: dict(row) for relative, row in by_path.items()}


def _verify_runtime_ownership(
    root: str,
    baseline: dict[str, dict[str, Any]],
    record_claims: set[str],
    deadline_ns: int | None = None,
) -> str:
    """Admit only unchanged venv baseline plus exact5 RECORD-owned additions."""

    rows, current = _runtime_inventory(root, deadline_ns)
    if set(baseline) & record_claims:
        _fail("installed RECORD claim overlaps fresh venv baseline")
    for relative, baseline_row in baseline.items():
        if current.get(relative) != baseline_row:
            _fail("fresh venv baseline identity changed during installation")
    for relative, row in current.items():
        if relative in baseline:
            continue
        if row["kind"] == "regular":
            if relative not in record_claims:
                _fail("full runtime contains an unclaimed regular file")
            continue
        prefix = relative + "/"
        if not any(claim.startswith(prefix) for claim in record_claims):
            _fail("full runtime contains an unclaimed directory")
    current_regular = {
        relative for relative, row in current.items() if row["kind"] == "regular"
    }
    if not record_claims <= current_regular:
        _fail("installed RECORD claim is absent from full runtime")
    return canonical_sha256(rows)


def _installed_manifests(
    root: str,
    site: str,
    lock: dict[str, Any],
    baseline: dict[str, dict[str, Any]],
    deadline_ns: int | None = None,
) -> tuple[str, str, str]:
    all_rows: list[dict[str, Any]] = []
    closures: list[dict[str, str]] = []
    owned: set[str] = set()
    record_self: set[str] = set()
    record_claims: set[str] = set()
    for lock_row in lock["distributions"]:
        _check_deadline(deadline_ns)
        candidates = [
            name for name in os.listdir(site)
            if name.endswith(".dist-info")
            and os.path.isfile(os.path.join(site, name, "RECORD"))
        ]
        matching: list[str] = []
        for directory in candidates:
            _check_deadline(deadline_ns)
            metadata_path = os.path.join(site, directory, "METADATA")
            try:
                metadata = BytesParser(policy=email.policy.compat32).parsebytes(
                    _read_regular(metadata_path, 1_048_576)[0]
                )
            except PreparationViolation:
                continue
            if (
                _normalized_name(str(metadata.get("Name", "")))
                == lock_row["normalized_distribution_name"]
                and str(metadata.get("Version", "")) == lock_row["distribution_version"]
            ):
                matching.append(directory)
        if len(matching) != 1:
            _fail("installed distribution metadata cardinality is not exact1")
        record_relative = matching[0] + "/RECORD"
        record_path = os.path.join(site, matching[0], "RECORD")
        record_bytes, _ = _read_regular(record_path, 4_194_304)
        try:
            rows = list(csv.reader(io.StringIO(record_bytes.decode("utf-8", "strict"), newline="")))
        except (UnicodeError, csv.Error):
            _fail("installed RECORD is malformed")
        closure_entries: list[dict[str, Any]] = []
        for row in rows:
            _check_deadline(deadline_ns)
            if len(row) != 3:
                _fail("installed RECORD row is malformed")
            raw_path, claimed, size = row
            relative, path = _claim_path(root, site, raw_path)
            root_relative = os.path.relpath(path, root).replace(os.sep, "/")
            if root_relative in record_claims:
                _fail("installed RECORD ownership overlaps")
            record_claims.add(root_relative)
            if relative in owned:
                _fail("installed RECORD ownership overlaps")
            actual, actual_size = _file_digest(path, deadline_ns)
            if relative == record_relative:
                if claimed or size:
                    _fail("installed RECORD self row is not empty")
                record_self.add(relative)
                continue
            if not claimed or not size or _record_digest(claimed) != actual:
                _fail("installed RECORD digest mismatches")
            try:
                expected_size = int(size, 10)
            except ValueError:
                _fail("installed RECORD size is invalid")
            if size != str(expected_size) or expected_size != actual_size:
                _fail("installed RECORD size mismatches")
            if os.path.commonpath((site, path)) != site:
                # Console-script claims are verified but are outside the
                # importable installed-closure and site inventory domains.
                continue
            if relative.endswith(".pyc") or "__pycache__" in relative.split("/"):
                _fail("installed bytecode/cache payload is forbidden")
            owned.add(relative)
            closure_entries.append({"path": relative, "sha256": actual, "size": actual_size})
            all_rows.append(
                {
                    "normalized_distribution_name": lock_row["normalized_distribution_name"],
                    "relative_path": relative,
                    "byte_count": actual_size,
                    "raw_sha256": actual,
                }
            )
        closure_entries.sort(key=lambda item: item["path"])
        closure_sha = canonical_sha256({"record_entries": closure_entries})
        if closure_sha != lock_row["installed_record_closure_sha256"]:
            _fail("installed distribution closure mismatches lock")
        closures.append(
            {
                "normalized_distribution_name": lock_row["normalized_distribution_name"],
                "distribution_version": lock_row["distribution_version"],
                "installed_record_closure_sha256": closure_sha,
            }
        )
    all_rows.sort(
        key=lambda item: (
            [row["normalized_distribution_name"] for row in lock["distributions"]].index(
                item["normalized_distribution_name"]
            ),
            item["relative_path"],
        )
    )
    physical: set[str] = set()
    for directory, dirs, files in os.walk(site, topdown=True, followlinks=False):
        _check_deadline(deadline_ns)
        dirs.sort()
        files.sort()
        if "__pycache__" in dirs:
            _fail("installed __pycache__ is forbidden")
        for name in dirs + files:
            path = os.path.join(directory, name)
            if stat.S_ISLNK(os.lstat(path).st_mode):
                _fail("installed symlink is forbidden")
        for name in files:
            physical.add(os.path.relpath(os.path.join(directory, name), site).replace(os.sep, "/"))
    if physical - record_self != owned:
        _fail("installed physical inventory does not match RECORD ownership")
    installed_sha = canonical_sha256(all_rows)
    expected_installed = getattr(PreparationContractV1, "INSTALLED_FILE_MANIFEST_SHA256", None)
    if expected_installed is not None and installed_sha != expected_installed:
        _fail("installed file manifest identity mismatches")
    distribution_sha = canonical_sha256(closures)
    expected_distribution = getattr(
        PreparationContractV1,
        "DISTRIBUTION_CLOSURE_SHA256",
        "4d3d6afdac2b9a606d4797ff5fbe65010faddf0de9788202798ddb8d95e6556c",
    )
    if distribution_sha != expected_distribution:
        _fail("aggregate installed closure mismatches")
    full_root_sha = _verify_runtime_ownership(
        root, baseline, record_claims, deadline_ns
    )
    return installed_sha, distribution_sha, full_root_sha


def _full_root_manifest(root: str, deadline_ns: int | None = None) -> str:
    rows, _by_path = _runtime_inventory(root, deadline_ns)
    return canonical_sha256(rows)


def _capture_child(process: subprocess.Popen[bytes], timeout_seconds: float) -> tuple[bytes, bytes]:
    if process.stdout is None or process.stderr is None:
        _terminate(process)
        _process_fail("P4/P5 pipes are unavailable")
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
                _process_fail("P4/P5 process group timeout")
            for key, _events in selector.select(min(remaining, 0.25)):
                block = os.read(key.fileobj.fileno(), 65_536)
                if not block:
                    selector.unregister(key.fileobj)
                    continue
                target = captured[key.data]
                if len(target) + len(block) > _MAX_OUTPUT:
                    _terminate(process)
                    _process_fail("P4/P5 output overflow")
                target.extend(block)
        try:
            process.wait(timeout=max(0.0, deadline - time.monotonic()))
        except subprocess.TimeoutExpired:
            _terminate(process)
            _process_fail("P4/P5 wait timeout")
    except PreparationViolation:
        _terminate(process)
        raise
    except OSError:
        _terminate(process)
        _process_fail("P4/P5 bounded capture failed")
    finally:
        selector.close()
    return bytes(captured["stdout"]), bytes(captured["stderr"])


def _validate_acquisition_boundary(
    request: dict[str, Any], lock: dict[str, Any], observation: dict[str, Any]
) -> None:
    c = PreparationContractV1
    if type(observation) is not dict or frozenset(observation) != c.ACQUISITION_OBSERVATION_KEYS:
        _fail("acquisition observation exact18 schema mismatches")
    expected_rows = [
        {
            "wheel_filename": row["wheel_filename"],
            "wheel_sha256": row["wheel_sha256"],
        }
        for row in lock["distributions"]
    ]
    fixed = {
        "schema_version": c.ACQUISITION_OBSERVATION_SCHEMA,
        "authority_id": request["authority_id"],
        "observation_session_id": request["observation_session_id"],
        "consumed": True,
        "process_launch_count": 1,
        "egress_attestation_sha256": request["egress_attestation_sha256"],
        "returncode": 0,
        "requirements_sha256": c.REQUIREMENTS_SHA256,
        "accepted_wheel_rows": expected_rows,
        "accepted_wheel_manifest_sha256": c.ACCEPTED_WHEEL_MANIFEST_SHA256,
    }
    if any(observation.get(key) != value for key, value in fixed.items()):
        _fail("acquisition observation fixed identity mismatches")
    online = {
        "LANG": "C.UTF-8", "LC_ALL": "C.UTF-8", "NETRC": "/dev/null",
        "PIP_CONFIG_FILE": "/dev/null", "PYTHONDONTWRITEBYTECODE": "1",
        "PYTHONNOUSERSITE": "1", "TEMP": request["path_plan"]["process_temp_root"],
        "TMP": request["path_plan"]["process_temp_root"],
        "TMPDIR": request["path_plan"]["process_temp_root"],
        "HTTPS_PROXY": request["private_transport"]["https_proxy"],
        "REQUESTS_CA_BUNDLE": request["private_transport"]["custom_ca_locator"],
        "SSL_CERT_FILE": request["private_transport"]["custom_ca_locator"],
    }
    if observation["argv_sha256"] != canonical_sha256(
        _online_acquisition_argv(request)
    ) or observation["environment_sha256"] != canonical_sha256(online):
        _fail("acquisition process identity mismatches")
    for key in (
        "egress_attestation_source_observation_sha256", "transport_b0_sha256",
        "transport_b1_sha256", "transport_b2_sha256", "stdout_sha256", "stderr_sha256",
    ):
        value = observation[key]
        if type(value) is not str or len(value) != 64 or any(ch not in "0123456789abcdef" for ch in value):
            _fail("acquisition observation digest is invalid")


def _online_acquisition_argv(request: dict[str, Any]) -> list[str]:
    plan = request["path_plan"]
    return [
        request["control_runtime"]["executable"], "-I", "-B", "-m", "pip",
        "--isolated", "--disable-pip-version-check", "--no-input", "--no-color",
        "--no-python-version-warning", "--timeout", "15", "--retries", "0",
        "--resume-retries", "0", "--keyring-provider", "disabled", "download",
        "--no-cache-dir", "--progress-bar", "off", "--only-binary=:all:",
        "--no-deps", "--require-hashes", "--index-url", PreparationContractV1.PRIMARY_INDEX_URL,
        "--requirement", plan["requirements_file_outside_runtime"], "--dest", plan["wheel_root"],
    ]


def _materialize_once(
    request: dict[str, Any], validated_lock: dict[str, Any], acquisition_observation: dict[str, Any]
) -> dict[str, Any]:
    """Validate exact5 wheels, create one fresh venv, and install offline once."""

    request = validate_execution_request(request)
    _validate_acquisition_boundary(request, validated_lock, acquisition_observation)
    in_process_budget_ns = (
        PreparationContractV1.IN_PROCESS_MATERIALIZATION_WALL_SECONDS * 1_000_000_000
    )
    deadline_ns = time.monotonic_ns() + in_process_budget_ns
    _set_phase_alarm(PreparationContractV1.IN_PROCESS_MATERIALIZATION_WALL_SECONDS)
    plan = request["path_plan"]
    wheel_rows: list[dict[str, str]] = []
    for lock_row in validated_lock["distributions"]:
        wheel_rows.append(
            _wheel_record(
                lock_row, os.path.join(plan["wheel_root"], lock_row["wheel_filename"]), deadline_ns
            )
        )
    wheel_manifest = canonical_sha256(wheel_rows)
    expected_wheel_records = getattr(
        PreparationContractV1,
        "WHEEL_RECORD_MANIFEST_SHA256",
        "61006261c4aebbb68d941153cdb5be4feb753f1bd638a500dc389b6f4e506fae",
    )
    if wheel_manifest != expected_wheel_records:
        _fail("wheel RECORD manifest identity mismatches")

    runtime_root = plan["runtime_root"]
    if os.path.lexists(runtime_root):
        _fail("runtime root existed before materialization")
    try:
        os.mkdir(runtime_root, 0o700)
        venv.EnvBuilder(
            system_site_packages=False,
            clear=False,
            symlinks=False,
            upgrade=False,
            with_pip=False,
            prompt=None,
            upgrade_deps=False,
        ).create(runtime_root)
    except (OSError, ValueError):
        _process_fail("in-process venv creation failed")
    executable = os.path.join(runtime_root, "bin", "python")
    executable_raw, executable_stat = _read_regular(
        executable, 64 * 1024 * 1024, deadline_ns
    )
    expected_interpreter = getattr(
        PreparationContractV1,
        "EXPECTED_INTERPRETER_SHA256",
        "9ed008e5a8685235361f0c53771b520ab082dd99a877ad2fd796a93fa4c0b488",
    )
    if _sha(executable_raw) != expected_interpreter or not stat.S_ISREG(executable_stat.st_mode):
        _fail("runtime interpreter identity mismatches")

    remaining_in_process_ns = deadline_ns - time.monotonic_ns()
    if remaining_in_process_ns <= 0:
        _process_fail("in-process materialization deadline exceeded")
    _set_phase_alarm(0.0)
    argv = _offline_argv(request)
    environment = _offline_environment(request)
    # CPython/Linux creates exactly this compatibility alias.  Normalize it
    # immediately before P4 so neither P4 nor the admitted full-root manifest
    # can inherit a symlink.
    _normalize_cpython_linux_venv_lib64(runtime_root, deadline_ns)
    baseline = _fresh_venv_baseline(runtime_root, deadline_ns)
    try:
        process = subprocess.Popen(
            argv,
            stdin=subprocess.DEVNULL,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            cwd=request["path_plan"]["controller_test_cwd"],
            env=environment,
            shell=False,
            text=False,
            close_fds=True,
            pass_fds=(),
            start_new_session=True,
        )
    except OSError:
        _process_fail("P4 OS launch rejected")
    stdout, stderr = _capture_child(process, _PROCESS_TIMEOUT)
    if process.returncode != 0:
        _terminate(process)
        _process_fail("P4/P5 returned nonzero")

    deadline_ns = time.monotonic_ns() + remaining_in_process_ns
    _set_phase_alarm(remaining_in_process_ns / 1_000_000_000)

    site_relative = getattr(
        PreparationContractV1, "SITE_PACKAGES_RELATIVE", "lib/python3.12/site-packages"
    )
    site = os.path.join(runtime_root, *site_relative.split("/"))
    if not os.path.isdir(site):
        _fail("fixed site-packages path is absent")
    installed_sha, distribution_sha, full_root_sha = _installed_manifests(
        runtime_root, site, validated_lock, baseline, deadline_ns
    )
    root_locator_sha = canonical_sha256(
        {
            "schema_version": "emlis.nls_v3.s11.g4b.runtime_root_locator.v1",
            "runtime_root": runtime_root,
        }
    )
    executable_locator_sha = canonical_sha256(
        {
            "schema_version": "emlis.nls_v3.s11.g4b.runtime_executable_locator.v1",
            "runtime_executable": executable,
        }
    )
    process_evidence = {
        "pid": process.pid,
        "returncode": process.returncode,
        "executable_sha256": request["control_runtime"]["resolved_interpreter_sha256"],
        "argv_sha256": canonical_sha256(argv),
        "environment_sha256": canonical_sha256(environment),
        "cwd_binding_sha256": canonical_sha256(
            {
                "schema_version": "g4b.cwd.binding.v1",
                "cwd": request["path_plan"]["controller_test_cwd"],
            }
        ),
        "stdout_sha256": _sha(stdout),
        "stdout_bytes": len(stdout),
        "stderr_sha256": _sha(stderr),
        "stderr_bytes": len(stderr),
        "termination_state": "EXITED_WITH_PINNED_P5_SOURCE_EDGE",
    }
    process_projection = _materialization_process_projection(
        request,
        runtime_executable_locator_sha256=executable_locator_sha,
        resolved_interpreter_sha256=_sha(executable_raw),
        process_evidence=process_evidence,
    )
    process_ledger_sha = canonical_sha256(process_projection)
    procedures = list(
        getattr(
            PreparationContractV1,
            "PROCEDURE_IDS",
            (
                "COCOLON_RULE13_RUNTIME_CONTINUITY_V20260811",
                "COCOLON_RULE16_ONE_SHOT_PRELAUNCH_V20260811",
            ),
        )
    )
    event_preimage = {
        "schema_version": "emlis.nls_v3.s11.g4b.runtime_materialization.external_attestation.v1",
        "authority_id": request["authority_id"],
        "observation_session_id": request["observation_session_id"],
        "procedure_ids": procedures,
        "fresh_root_nonexistent_before": True,
        "prior_artifact_reuse_count": 0,
        "root_locator_sha256": root_locator_sha,
        "expected_full_root_manifest_sha256": full_root_sha,
        "site_packages_relative": site_relative,
        "admitted_executable_relative_path": "bin/python",
    }
    attestation = {
        "schema_version": getattr(
            PreparationContractV1,
            "MATERIALIZATION_ATTESTATION_SCHEMA",
            "emlis.nls_v3.s11.g4b.runtime_materialization.attestation.v1",
        ),
        "authority_id": request["authority_id"],
        "observation_session_id": request["observation_session_id"],
        "event_id": canonical_sha256(event_preimage),
        "procedure_ids": procedures,
        "fresh_root_nonexistent_before": True,
        "prior_artifact_reuse_count": 0,
        "runtime_root_locator_sha256": root_locator_sha,
        "site_packages_relative": site_relative,
        "derived_lock_raw_sha256": getattr(
            PreparationContractV1,
            "DERIVED_LOCK_RAW_SHA256",
            "8c0e3482089e6420f624e93ba974897e01ee777740e8b7af133e1a6c293767c8",
        ),
        "derived_lock_logical_sha256": getattr(
            PreparationContractV1,
            "DERIVED_LOCK_LOGICAL_SHA256",
            "1e5b243a9d610f9d4d469a6b3424a88ea8022557c8fffe79d676326840f1004d",
        ),
        "accepted_wheel_manifest_sha256": acquisition_observation[
            "accepted_wheel_manifest_sha256"
        ],
        "wheel_record_rows": wheel_rows,
        "wheel_record_manifest_sha256": wheel_manifest,
        "distribution_closure_sha256": distribution_sha,
        "runtime_executable_locator_sha256": executable_locator_sha,
        "resolved_interpreter_sha256": _sha(executable_raw),
        "installed_file_manifest_sha256": installed_sha,
        "full_runtime_root_manifest_sha256": full_root_sha,
        "materialization_process_ledger_sha256": process_ledger_sha,
        "environment_policy_sha256": getattr(
            PreparationContractV1,
            "ENVIRONMENT_POLICY_SHA256",
            "8a43751b49a8db1d024063608405f9b169e829f3c0be3488433b31800d44b1a4",
        ),
        "status": "MATERIALIZED_VERIFIED",
    }
    _canonical_file(plan["materialization_attestation"], attestation)
    # Preserve the exact22 persisted schema and expose the directly observed
    # P4 evidence and canonical P4/P5 exact14 projection only in memory.
    returned = dict(attestation)
    returned["_process_evidence"] = process_evidence
    returned["_process_ledger_projection"] = process_projection
    return returned


def materialize_once(
    request: dict[str, Any], validated_lock: dict[str, Any], acquisition_observation: dict[str, Any]
) -> dict[str, Any]:
    """Apply the V3 hard guard around the single in-process materialization."""

    use_alarm = threading.current_thread() is threading.main_thread() and hasattr(signal, "setitimer")
    previous_handler: Any = None
    previous_timer: tuple[float, float] | None = None
    if use_alarm:
        previous_handler = signal.getsignal(signal.SIGALRM)
        previous_timer = signal.getitimer(signal.ITIMER_REAL)
        signal.signal(signal.SIGALRM, _alarm_handler)
    try:
        return _materialize_once(request, validated_lock, acquisition_observation)
    finally:
        if use_alarm:
            signal.setitimer(signal.ITIMER_REAL, 0.0)
            signal.signal(signal.SIGALRM, previous_handler)
            if previous_timer is not None and previous_timer[0] > 0.0:
                signal.setitimer(signal.ITIMER_REAL, *previous_timer)
