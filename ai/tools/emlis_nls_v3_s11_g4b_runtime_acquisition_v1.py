#!/usr/bin/env python3
"""One-shot, hash-locked acquisition for the G4-B preparation family.

The module deliberately exposes only the two effect surfaces approved by the
V3 design.  It does not use pip as a library and it has no direct network API;
the single ``pip download`` child is the only possible network edge.
"""

from __future__ import annotations

import hashlib
import datetime as _datetime
import os
import selectors
import signal
import stat
import subprocess
import sys
import sysconfig
import time
from typing import Any
from urllib.parse import urlsplit

from ai.tools.emlis_nls_v3_s11_g4b_runtime_preparation_contract_v1 import (
    PreparationContractV1,
    PreparationViolation,
    canonical_file_bytes,
    canonical_json_bytes,
    canonical_sha256,
    derive_requirements_bytes,
    strict_json_from_bytes,
    validate_execution_request,
)

__all__ = ("capture_transport_binding_at_start", "acquire_once")

_ACTIVE_TRANSPORT: dict[tuple[str, str, str], dict[str, Any]] = {}
_MAX_OUTPUT = 1_048_576
_ACQUISITION_TIMEOUT = 300
_PIP_SOURCE_EXACT3 = (
    ("pip/_internal/cli/main_parser.py", PreparationContractV1.PIP_MAIN_PARSER_SHA256),
    ("pip/_internal/build_env.py", PreparationContractV1.PIP_BUILD_ENV_SHA256),
    ("pip/__pip-runner__.py", PreparationContractV1.PIP_RUNNER_SHA256),
)


def _fail(code: str, detail: str, *, consumed: bool = False) -> None:
    error = PreparationViolation(code, detail)
    error.consumed = consumed
    raise error


def _sha256_bytes(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _read_regular_nofollow(
    path: str, code: str, limit: int = _MAX_OUTPUT
) -> tuple[bytes, os.stat_result]:
    flags = os.O_RDONLY | getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_NOFOLLOW", 0)
    try:
        fd = os.open(path, flags)
        try:
            observed = os.fstat(fd)
            if not stat.S_ISREG(observed.st_mode) or observed.st_nlink != 1:
                _fail(code, "private source is not a single regular file")
            chunks: list[bytes] = []
            total = 0
            while True:
                block = os.read(fd, 131_072)
                if not block:
                    break
                total += len(block)
                if total > limit:
                    _fail(code, "private source exceeds its byte limit")
                chunks.append(block)
            return b"".join(chunks), observed
        finally:
            os.close(fd)
    except PreparationViolation:
        raise
    except OSError as exc:
        _fail(code, "private source cannot be read without following links")
        raise AssertionError from exc


def _validate_control_runtime_actual(request: dict[str, Any]) -> None:
    """Fresh-read the P1 interpreter and pinned pip source without a child process."""

    runtime = request["control_runtime"]
    executable = runtime["executable"]
    if not os.path.isabs(executable) or os.path.realpath(executable) != os.path.realpath(
        sys.executable
    ):
        _fail("BASE_OR_PREIMAGE_DRIFT", "control executable is not the running interpreter")
    resolved = os.path.realpath(executable)
    raw, _observed = _read_regular_nofollow(
        resolved, "BASE_OR_PREIMAGE_DRIFT", 67_108_864
    )
    if _sha256_bytes(raw) != runtime["resolved_interpreter_sha256"]:
        _fail("BASE_OR_PREIMAGE_DRIFT", "control interpreter raw identity mismatches")
    implementation = "CPython" if sys.implementation.name == "cpython" else sys.implementation.name
    version = ".".join(str(item) for item in sys.version_info[:3])
    platform_tag = sysconfig.get_platform()
    if (
        implementation != runtime["implementation"]
        or version != runtime["python_version"]
        or platform_tag != runtime["platform_tag"]
    ):
        _fail("BASE_OR_PREIMAGE_DRIFT", "control runtime facts mismatch")

    purelib = sysconfig.get_path("purelib")
    if not purelib or not os.path.isabs(purelib):
        _fail("BASE_OR_PREIMAGE_DRIFT", "control pip source root is unavailable")
    for relative, expected_sha256 in _PIP_SOURCE_EXACT3:
        source_raw, _source_stat = _read_regular_nofollow(
            os.path.join(purelib, *relative.split("/")), "BASE_OR_PREIMAGE_DRIFT"
        )
        if _sha256_bytes(source_raw) != expected_sha256:
            _fail("BASE_OR_PREIMAGE_DRIFT", f"pinned pip source drift: {relative}")

    pip_root = os.path.join(purelib, "pip")
    try:
        dist_info = sorted(
            name
            for name in os.listdir(purelib)
            if name == f"pip-{runtime['pip_version']}.dist-info"
        )
    except OSError:
        _fail("BASE_OR_PREIMAGE_DRIFT", "pip installed-source inventory failed")
    if len(dist_info) != 1:
        _fail("BASE_OR_PREIMAGE_DRIFT", "pinned pip dist-info cardinality is not exact1")
    metadata_raw, _metadata_stat = _read_regular_nofollow(
        os.path.join(purelib, dist_info[0], "METADATA"), "BASE_OR_PREIMAGE_DRIFT"
    )
    try:
        metadata_lines = metadata_raw.decode("utf-8", "strict").splitlines()
    except UnicodeDecodeError:
        _fail("BASE_OR_PREIMAGE_DRIFT", "pinned pip metadata is not strict UTF-8")
    if "Name: pip" not in metadata_lines or f"Version: {runtime['pip_version']}" not in metadata_lines:
        _fail("BASE_OR_PREIMAGE_DRIFT", "pinned pip metadata mismatches")
    rows: list[dict[str, Any]] = []
    total = 0
    for root in (pip_root, os.path.join(purelib, dist_info[0])):
        for directory, directories, files in os.walk(root, topdown=True, followlinks=False):
            directories.sort()
            files.sort()
            for name in directories:
                if stat.S_ISLNK(os.lstat(os.path.join(directory, name)).st_mode):
                    _fail("BASE_OR_PREIMAGE_DRIFT", "pip installed source contains symlink")
            for name in files:
                path = os.path.join(directory, name)
                source_raw, observed = _read_regular_nofollow(path, "BASE_OR_PREIMAGE_DRIFT")
                total += len(source_raw)
                if total > 67_108_864 or len(rows) >= 8192:
                    _fail("BASE_OR_PREIMAGE_DRIFT", "pip installed-source budget exceeded")
                rows.append(
                    {
                        "relative_path": os.path.relpath(path, purelib).replace(os.sep, "/"),
                        "byte_count": observed.st_size,
                        "raw_sha256": _sha256_bytes(source_raw),
                    }
                )
    rows.sort(key=lambda row: row["relative_path"])
    if canonical_sha256(rows) != runtime["pip_installed_source_manifest_sha256"]:
        _fail("BASE_OR_PREIMAGE_DRIFT", "pip installed-source manifest mismatches")


def _literal_environments(request: dict[str, Any]) -> tuple[dict[str, str], dict[str, str]]:
    plan = request["path_plan"]
    transport = request["private_transport"]
    ca = transport["custom_ca_locator"]
    common = {
        "LANG": "C.UTF-8",
        "LC_ALL": "C.UTF-8",
        "NETRC": "/dev/null",
        "PIP_CONFIG_FILE": "/dev/null",
        "PYTHONDONTWRITEBYTECODE": "1",
        "PYTHONNOUSERSITE": "1",
        "TEMP": plan["process_temp_root"],
        "TMP": plan["process_temp_root"],
        "TMPDIR": plan["process_temp_root"],
    }
    online = dict(common)
    online.update(
        {
            "HTTPS_PROXY": transport["https_proxy"],
            "REQUESTS_CA_BUNDLE": ca,
            "SSL_CERT_FILE": ca,
        }
    )
    return online, common


def _transport_record(request: dict[str, Any], stage: str) -> dict[str, Any]:
    transport = request["private_transport"]
    raw_url = transport["https_proxy"]
    parsed = urlsplit(raw_url)
    if os.geteuid() == 0:
        _fail("PRIVATE_TRANSPORT_BINDING_INVALID", "authority root can modify the CA")
    if (
        parsed.scheme not in ("http", "https")
        or not parsed.hostname
        or parsed.username is not None
        or parsed.password is not None
        or parsed.path not in ("", "/")
        or parsed.query
        or parsed.fragment
    ):
        _fail("PRIVATE_TRANSPORT_BINDING_INVALID", "proxy URL is ambiguous or contains userinfo")
    try:
        port = parsed.port
    except ValueError:
        _fail("PRIVATE_TRANSPORT_BINDING_INVALID", "proxy port is invalid")
    if port is None:
        port = 443 if parsed.scheme == "https" else 80

    ca_raw, observed = _read_regular_nofollow(
        transport["custom_ca_locator"], "PRIVATE_TRANSPORT_BINDING_INVALID"
    )
    mode = stat.S_IMODE(observed.st_mode)
    if mode & 0o022:
        _fail("PRIVATE_TRANSPORT_BINDING_INVALID", "CA is group/world writable")
    if observed.st_uid == os.geteuid() and mode & 0o200:
        _fail("PRIVATE_TRANSPORT_BINDING_INVALID", "authority user can modify the CA")
    expected_ca = transport["expected_ca_raw_sha256"]
    actual_ca = _sha256_bytes(ca_raw)
    if actual_ca != expected_ca:
        _fail("PRIVATE_TRANSPORT_BINDING_INVALID", "CA raw identity mismatches request")

    online, _offline = _literal_environments(request)
    stable = {
        "schema_version": getattr(
            PreparationContractV1,
            "TRANSPORT_BINDING_SCHEMA",
            "emlis.nls_v3.s11.g4b.private_transport_binding.v1",
        ),
        "proxy_url": raw_url,
        "proxy_scheme": parsed.scheme,
        "proxy_host": parsed.hostname.lower(),
        "proxy_port": port,
        "proxy_userinfo_present": False,
        "ca_locator": transport["custom_ca_locator"],
        "ca_stat_tuple": {
            "st_dev": observed.st_dev,
            "st_ino": observed.st_ino,
            "st_mode": mode,
            "st_nlink": observed.st_nlink,
            "st_uid": observed.st_uid,
            "st_gid": observed.st_gid,
            "st_size": observed.st_size,
            "st_mtime_ns": observed.st_mtime_ns,
        },
        "ca_raw_sha256": actual_ca,
        "tls_verification": True,
        "normalized_child_environment_sha256": canonical_sha256(online),
        "locator_published": False,
    }
    stable_sha = canonical_sha256(stable)
    if stable_sha != transport["expected_stable_projection_sha256"]:
        _fail("PRIVATE_TRANSPORT_BINDING_INVALID", "transport stable projection mismatches")
    return {
        "schema_version": stable["schema_version"],
        "stage": stage,
        "proxy_url": stable["proxy_url"],
        "proxy_scheme": stable["proxy_scheme"],
        "proxy_host": stable["proxy_host"],
        "proxy_port": stable["proxy_port"],
        "proxy_userinfo_present": False,
        "ca_locator": stable["ca_locator"],
        "ca_stat_tuple": stable["ca_stat_tuple"],
        "ca_raw_sha256": stable["ca_raw_sha256"],
        "tls_verification": True,
        "normalized_child_environment_sha256": stable["normalized_child_environment_sha256"],
        "observed_monotonic_ns": time.monotonic_ns(),
        "binding_sha256": stable_sha,
        "locator_published": False,
    }


def _write_all(fd: int, payload: bytes) -> None:
    view = memoryview(payload)
    while view:
        count = os.write(fd, view)
        if count <= 0:
            _fail("PRIVATE_TRANSPORT_BINDING_INVALID", "private evidence write made no progress")
        view = view[count:]


def _append_record(state: dict[str, Any], record: dict[str, Any]) -> None:
    raw = canonical_json_bytes(record) + b"\n"
    _write_all(state["fd"], raw)
    os.fsync(state["fd"])
    state["record_lines"].append(raw)


def _seal_transport(state: dict[str, Any], *, full_match: bool) -> str:
    records = state["records"]
    summary = {
        "schema_version": getattr(
            PreparationContractV1,
            "TRANSPORT_SUMMARY_SCHEMA",
            "emlis.nls_v3.s11.g4b.private_transport_binding.summary.v1",
        ),
        "record_count": len(records),
        "ordered_binding_sha256": [item["binding_sha256"] for item in records],
        "stable_projection_full_match": full_match,
        "records_preimage_sha256": _sha256_bytes(b"".join(state["record_lines"])),
    }
    _append_record(state, summary)
    fd = state["fd"]
    os.fchmod(fd, 0o400)
    os.fsync(fd)
    os.close(fd)
    state["fd"] = -1
    directory_fd = os.open(os.path.dirname(state["path"]), os.O_RDONLY | os.O_DIRECTORY)
    try:
        os.fsync(directory_fd)
    finally:
        os.close(directory_fd)
    raw, _observed = _read_regular_nofollow(
        state["path"], "PRIVATE_TRANSPORT_BINDING_INVALID"
    )
    return _sha256_bytes(raw)


def _source_observation(request: dict[str, Any], stage: str) -> tuple[dict[str, Any], str]:
    source = request["egress_attestation_source"]
    raw, observed = _read_regular_nofollow(
        source["private_locator"], "HOST_EXCEPTION_NOT_ENFORCED"
    )
    mode = stat.S_IMODE(observed.st_mode)
    raw_sha = _sha256_bytes(raw)
    expected_mode = int(source["expected_mode"], 8)
    effective_uid = os.geteuid()
    effective_groups = set(os.getgroups()) | {os.getegid()}
    authority_writable = effective_uid == 0 or bool(
        (observed.st_uid == effective_uid and mode & stat.S_IWUSR)
        or (observed.st_gid in effective_groups and mode & stat.S_IWGRP)
        or mode & stat.S_IWOTH
    )
    owner_class_valid = (
        source["expected_owner_class"] == "PLATFORM_ROOT"
        and observed.st_uid == 0
        and effective_uid != 0
    ) or (
        source["expected_owner_class"] == "APPROVED_DISTINCT_NON_AUTHORITY_OWNER"
        and observed.st_uid != 0
        and observed.st_uid != effective_uid
    )
    if (
        mode != expected_mode
        or not source["expected_regular_file"]
        or observed.st_nlink != source["expected_nlink"]
        or raw_sha != source["expected_raw_sha256"]
        or mode & 0o222
        or not owner_class_valid
        or authority_writable
    ):
        _fail("HOST_EXCEPTION_NOT_ENFORCED", "egress trust-root source identity mismatches")
    try:
        body = strict_json_from_bytes(raw, require_final_lf=False)
    except PreparationViolation:
        raise
    if body != request["egress_attestation"] or raw_sha != request["egress_attestation_sha256"]:
        _fail("HOST_EXCEPTION_NOT_ENFORCED", "egress attestation raw body mismatches")
    if source["expected_expiry"] != body["expires_at"]:
        _fail("HOST_EXCEPTION_NOT_ENFORCED", "egress source expiry mismatches")
    try:
        issued = _datetime.datetime.strptime(body["issued_at"], "%Y-%m-%dT%H:%M:%SZ").replace(
            tzinfo=_datetime.timezone.utc
        )
        expires = _datetime.datetime.strptime(body["expires_at"], "%Y-%m-%dT%H:%M:%SZ").replace(
            tzinfo=_datetime.timezone.utc
        )
    except (KeyError, TypeError, ValueError):
        _fail("HOST_EXCEPTION_NOT_ENFORCED", "egress attestation time is invalid")
    now = _datetime.datetime.now(_datetime.timezone.utc)
    expiry_valid = issued - _datetime.timedelta(seconds=30) <= now < expires
    if stage == "P3_PRELAUNCH":
        expiry_valid = expiry_valid and (expires - now).total_seconds() >= (
            PreparationContractV1.MINIMUM_REMAINING_LIFETIME_AT_P3_SECONDS
        )
    if not expiry_valid:
        _fail("HOST_EXCEPTION_NOT_ENFORCED", "egress attestation validity window is not admissible")
    row = {
        "stage": stage,
        "owner_class": source["expected_owner_class"],
        "mode": mode,
        "regular_file": True,
        "nlink": observed.st_nlink,
        "authority_writable": authority_writable,
        "raw_sha256": raw_sha,
        "expiry_valid": expiry_valid,
        "stable_approval_match": (
            body["stable_authority_approval_binding_sha256"]
            == request["stable_authority_approval_binding_sha256"]
        ),
    }
    if not row["stable_approval_match"]:
        _fail("HOST_EXCEPTION_NOT_ENFORCED", "stable approval binding mismatches")
    return row, raw_sha


def _state_key(request: dict[str, Any]) -> tuple[str, str, str]:
    return (
        request["authority_id"],
        request["observation_session_id"],
        request["path_plan"]["private_transport_binding_observation"],
    )


def capture_transport_binding_at_start(request: dict[str, Any]) -> dict[str, Any]:
    """Capture B0 and begin the single-writer append-only private observation."""

    request = validate_execution_request(request)
    _validate_control_runtime_actual(request)
    key = _state_key(request)
    if key in _ACTIVE_TRANSPORT:
        _fail("PRIVATE_TRANSPORT_BINDING_INVALID", "B0 already exists for this session")
    path = key[2]
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0)
    try:
        fd = os.open(path, flags, 0o600)
    except OSError:
        _fail("PRIVATE_TRANSPORT_BINDING_INVALID", "transport evidence exclusive create failed")
    state = {"fd": fd, "path": path, "records": [], "record_lines": []}
    try:
        b0 = _transport_record(request, "B0")
        _append_record(state, b0)
        state["records"].append(b0)
        source_row, _source_sha = _source_observation(request, "P1_ENTRY")
        state["source_rows"] = [source_row]
        _ACTIVE_TRANSPORT[key] = state
        return b0
    except Exception:
        try:
            if state["fd"] >= 0:
                _seal_transport(state, full_match=False)
        finally:
            _ACTIVE_TRANSPORT.pop(key, None)
        raise


def _abort_transport_binding(request: dict[str, Any]) -> str | None:
    """Failure-seal an active B0 once and relinquish its in-process ownership.

    This is deliberately private so the approved acquisition public API remains
    exact2.  The controller may call it after B0 succeeds but before
    :func:`acquire_once` takes ownership.  Popping the state before sealing
    makes repeated/finally calls idempotent and prevents a second summary line.
    """

    try:
        key = _state_key(request)
    except (KeyError, TypeError):
        return None
    state = _ACTIVE_TRANSPORT.pop(key, None)
    if state is None or state.get("fd", -1) < 0:
        return None
    try:
        return _seal_transport(state, full_match=False)
    except Exception:
        # A failed seal must not leak the controller-owned descriptor.  Keep
        # the artifact non-writable whenever the descriptor still permits it;
        # the caller still receives the original seal failure and fails closed.
        fd = state.get("fd", -1)
        if fd >= 0:
            try:
                os.fchmod(fd, 0o400)
                os.fsync(fd)
            except OSError:
                pass
            finally:
                try:
                    os.close(fd)
                finally:
                    state["fd"] = -1
        raise


def _acquisition_argv(request: dict[str, Any]) -> list[str]:
    plan = request["path_plan"]
    return [
        request["control_runtime"]["executable"], "-I", "-B", "-m", "pip",
        "--isolated", "--disable-pip-version-check", "--no-input", "--no-color",
        "--no-python-version-warning", "--timeout", "15", "--retries", "0",
        "--resume-retries", "0", "--keyring-provider", "disabled", "download",
        "--no-cache-dir", "--progress-bar", "off", "--only-binary=:all:",
        "--no-deps", "--require-hashes", "--index-url", "https://pypi.org/simple/",
        "--requirement", plan["requirements_file_outside_runtime"],
        "--dest", plan["wheel_root"],
    ]


def _exclusive_file(path: str, payload: bytes, mode: int = 0o400) -> None:
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | getattr(os, "O_NOFOLLOW", 0)
    try:
        fd = os.open(path, flags, 0o600)
        try:
            _write_all(fd, payload)
            os.fsync(fd)
            os.fchmod(fd, mode)
            os.fsync(fd)
        finally:
            os.close(fd)
    except OSError:
        _fail("ACQUISITION_PROCESS_INVALID", "exclusive private file creation failed")


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


def _capture_child(process: subprocess.Popen[bytes], timeout_seconds: float) -> tuple[bytes, bytes]:
    """Bound both child streams while preserving one process launch."""

    if process.stdout is None or process.stderr is None:
        _terminate(process)
        _fail("ACQUISITION_PROCESS_INVALID", "P3 pipes are unavailable", consumed=True)
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
                _fail("ACQUISITION_PROCESS_INVALID", "P3 timeout", consumed=True)
            for key, _events in selector.select(min(remaining, 0.25)):
                block = os.read(key.fileobj.fileno(), 65_536)
                if not block:
                    selector.unregister(key.fileobj)
                    continue
                target = captured[key.data]
                if len(target) + len(block) > _MAX_OUTPUT:
                    _terminate(process)
                    _fail("ACQUISITION_PROCESS_INVALID", "P3 output overflow", consumed=True)
                target.extend(block)
        try:
            process.wait(timeout=max(0.0, deadline - time.monotonic()))
        except subprocess.TimeoutExpired:
            _terminate(process)
            _fail("ACQUISITION_PROCESS_INVALID", "P3 wait timeout", consumed=True)
    except PreparationViolation:
        _terminate(process)
        raise
    except OSError:
        _terminate(process)
        _fail("ACQUISITION_PROCESS_INVALID", "P3 bounded capture failed", consumed=True)
    finally:
        selector.close()
    return bytes(captured["stdout"]), bytes(captured["stderr"])


def _validate_wheels(wheel_root: str, lock: dict[str, Any]) -> list[dict[str, str]]:
    expected = {
        row["wheel_filename"]: row["wheel_sha256"] for row in lock["distributions"]
    }
    try:
        entries = sorted(os.scandir(wheel_root), key=lambda item: item.name)
    except OSError:
        _fail("ACQUIRED_WHEEL_SET_INVALID", "wheel root cannot be enumerated", consumed=True)
    if [item.name for item in entries] != sorted(expected):
        _fail("ACQUIRED_WHEEL_SET_INVALID", "wheel filename set is not exact5", consumed=True)
    rows: list[dict[str, str]] = []
    total = 0
    for entry in entries:
        observed = entry.stat(follow_symlinks=False)
        if not stat.S_ISREG(observed.st_mode) or observed.st_nlink != 1:
            _fail("ACQUIRED_WHEEL_SET_INVALID", "wheel is not a single regular file", consumed=True)
        total += observed.st_size
        if (
            observed.st_size > PreparationContractV1.WHEEL_RAW_BYTES
            or total > PreparationContractV1.WHEEL_AGGREGATE_BYTES
        ):
            _fail("ACQUIRED_WHEEL_SET_INVALID", "wheel byte budget exceeded", consumed=True)
        raw, _ = _read_regular_nofollow(
            entry.path,
            "ACQUIRED_WHEEL_SET_INVALID",
            limit=PreparationContractV1.WHEEL_RAW_BYTES,
        )
        actual = _sha256_bytes(raw)
        if actual != expected[entry.name]:
            _fail("ACQUIRED_WHEEL_SET_INVALID", "wheel hash mismatches lock", consumed=True)
        rows.append({"wheel_filename": entry.name, "wheel_sha256": actual})
    expected_manifest = getattr(
        PreparationContractV1,
        "ACCEPTED_WHEEL_MANIFEST_SHA256",
        "00d2df98c8cda7f1473794892bafe7ccd18cc816c79ccb346f3e21ff629b136d",
    )
    if canonical_sha256(rows) != expected_manifest:
        _fail("ACQUIRED_WHEEL_SET_INVALID", "wheel manifest identity mismatches", consumed=True)
    return rows


def acquire_once(
    request: dict[str, Any], validated_lock: dict[str, Any], transport_binding_b0: dict[str, Any]
) -> dict[str, Any]:
    """Consume the one-shot authority at P3 and return/persist exact18 evidence."""

    request = validate_execution_request(request)
    key = _state_key(request)
    state = _ACTIVE_TRANSPORT.get(key)
    if state is None or state["records"] != [transport_binding_b0]:
        _fail("PRIVATE_TRANSPORT_BINDING_INVALID", "active B0 ownership is absent")
    consumed = False
    transport_sha = ""
    try:
        requirements = derive_requirements_bytes(validated_lock)
        expected_requirements = getattr(
            PreparationContractV1,
            "REQUIREMENTS_SHA256",
            "4f7218509a20e42850afe75597f2abfdf447035001847621d4637faa246065f1",
        )
        if _sha256_bytes(requirements) != expected_requirements:
            _fail("BASE_OR_PREIMAGE_DRIFT", "requirements identity mismatches")
        _exclusive_file(request["path_plan"]["requirements_file_outside_runtime"], requirements)
        try:
            os.mkdir(request["path_plan"]["wheel_root"], 0o700)
        except OSError:
            _fail("ACQUISITION_PROCESS_INVALID", "fresh wheel root creation failed")

        b1 = _transport_record(request, "B1")
        _append_record(state, b1)
        state["records"].append(b1)
        if b1["binding_sha256"] != transport_binding_b0["binding_sha256"]:
            _fail("PRIVATE_TRANSPORT_DRIFT", "B0/B1 transport binding drift")
        source_row, source_sha = _source_observation(request, "P3_PRELAUNCH")
        state["source_rows"].append(source_row)

        argv = _acquisition_argv(request)
        online, _offline = _literal_environments(request)
        consumed = True
        try:
            process = subprocess.Popen(
                argv,
                stdin=subprocess.DEVNULL,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                cwd=request["path_plan"]["controller_test_cwd"],
                env=online,
                shell=False,
                text=False,
                close_fds=True,
                pass_fds=(),
                start_new_session=True,
            )
        except OSError:
            _fail("ACQUISITION_PROCESS_INVALID", "P3 OS launch rejected", consumed=True)
        stdout, stderr = _capture_child(process, _ACQUISITION_TIMEOUT)

        b2 = _transport_record(request, "B2")
        _append_record(state, b2)
        state["records"].append(b2)
        match = len({item["binding_sha256"] for item in state["records"]}) == 1
        _seal_transport(state, full_match=match)
        if not match:
            _fail("PRIVATE_TRANSPORT_DRIFT", "B0/B1/B2 transport drift", consumed=True)
        if process.returncode != 0:
            _terminate(process)
            _fail("ACQUISITION_PROCESS_INVALID", "P3 returned nonzero", consumed=True)
        accepted = _validate_wheels(request["path_plan"]["wheel_root"], validated_lock)
        observation = {
            "schema_version": getattr(
                PreparationContractV1,
                "ACQUISITION_OBSERVATION_SCHEMA",
                "emlis.nls_v3.s11.g4b.runtime_acquisition.observation.v1",
            ),
            "authority_id": request["authority_id"],
            "observation_session_id": request["observation_session_id"],
            "consumed": True,
            "process_launch_count": 1,
            "argv_sha256": canonical_sha256(argv),
            "environment_sha256": canonical_sha256(online),
            "egress_attestation_sha256": source_sha,
            "egress_attestation_source_observation_sha256": canonical_sha256(state["source_rows"]),
            "transport_b0_sha256": transport_binding_b0["binding_sha256"],
            "transport_b1_sha256": b1["binding_sha256"],
            "transport_b2_sha256": b2["binding_sha256"],
            "returncode": process.returncode,
            "stdout_sha256": _sha256_bytes(stdout),
            "stderr_sha256": _sha256_bytes(stderr),
            "requirements_sha256": _sha256_bytes(requirements),
            "accepted_wheel_rows": accepted,
            "accepted_wheel_manifest_sha256": canonical_sha256(accepted),
        }
        if frozenset(observation) != PreparationContractV1.ACQUISITION_OBSERVATION_KEYS:
            _fail("ACQUISITION_PROCESS_INVALID", "acquisition observation schema drift", consumed=True)
        _exclusive_file(
            request["path_plan"]["acquisition_observation"],
            canonical_file_bytes(observation),
        )
        # Private controller-only process evidence is deliberately added only
        # after the exact18 body has been validated and persisted.  Callers
        # must strip this underscore key before passing the observation across
        # the materialization schema boundary.
        returned = dict(observation)
        returned["_process_evidence"] = {
            "pid": process.pid,
            "returncode": process.returncode,
            "executable_sha256": request["control_runtime"]["resolved_interpreter_sha256"],
            "argv_sha256": canonical_sha256(argv),
            "environment_sha256": canonical_sha256(online),
            "cwd_binding_sha256": canonical_sha256(
                {
                    "schema_version": "g4b.cwd.binding.v1",
                    "cwd": request["path_plan"]["controller_test_cwd"],
                }
            ),
            "stdout_sha256": _sha256_bytes(stdout),
            "stdout_bytes": len(stdout),
            "stderr_sha256": _sha256_bytes(stderr),
            "stderr_bytes": len(stderr),
            "termination_state": "EXITED",
        }
        return returned
    except PreparationViolation as error:
        error.consumed = bool(getattr(error, "consumed", False) or consumed)
        if state.get("fd", -1) >= 0:
            try:
                _seal_transport(state, full_match=False)
            except Exception:
                pass
        raise
    finally:
        _ACTIVE_TRANSPORT.pop(key, None)
