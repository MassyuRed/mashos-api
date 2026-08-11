#!/usr/bin/env python3
"""Filesystem-first independent derivation for the G4-B V1 checker.

This role starts from a no-follow physical inventory, discovers dist-info
metadata directly, and builds reverse ownership from RECORD bytes.  It does
not import ``importlib.metadata`` or any owner implementation.
"""

from __future__ import annotations

import base64
import configparser
import csv
from email.parser import BytesParser
import hashlib
import os
import platform
import posixpath
import re
import stat
import sys
from typing import Any

sys.dont_write_bytecode = True

from ai.tools.emlis_nls_v3_s11_g4b_runtime_admission_contract_v1 import (  # noqa: E402
    ContractV1,
    ContractViolation,
    canonical_json_bytes,
    canonical_sha256,
    read_strict_json,
    validate_request,
    write_strict_json,
)


_INDEPENDENT_EMPTY_ROWS_SHA256 = canonical_sha256([])


def _independent_name(value: str) -> str:
    return re.sub(r"[-_.]+", "-", value).lower()


def _independent_digest(path: str) -> tuple[str, int]:
    accumulator = hashlib.sha256()
    observed_size = 0
    with open(path, "rb") as source:
        while True:
            chunk = source.read(65_536)
            if not chunk:
                break
            accumulator.update(chunk)
            observed_size += len(chunk)
    return accumulator.hexdigest(), observed_size


def _independent_stat(path: str) -> list[int]:
    observed = os.lstat(path)
    return [
        observed.st_dev,
        observed.st_ino,
        stat.S_IMODE(observed.st_mode),
        observed.st_size,
        observed.st_mtime_ns,
    ]


def _independent_no_symlink(path: str) -> None:
    cursor = os.path.sep
    for component in os.path.abspath(path).split(os.path.sep)[1:]:
        cursor = os.path.join(cursor, component)
        try:
            observed_mode = os.lstat(cursor).st_mode
        except OSError as exc:
            raise ContractViolation("INDEPENDENT_INVALID", "locator component is absent") from exc
        if stat.S_ISLNK(observed_mode):
            raise ContractViolation("INDEPENDENT_INVALID", "symlink component is forbidden")


def _independent_locators(request: dict[str, Any]) -> tuple[str, str, str]:
    runtime_root = request["materialization"]["root"]
    site_root = os.path.join(
        runtime_root, *request["materialization"]["site_packages_relative"].split("/")
    )
    python_executable = request["runtime"]["executable"]
    for locator in (runtime_root, site_root, python_executable):
        _independent_no_symlink(locator)
    if not os.path.isdir(runtime_root) or not os.path.isdir(site_root):
        raise ContractViolation("INDEPENDENT_INVALID", "runtime roots are absent")
    try:
        executable_mode = os.lstat(python_executable).st_mode
        executable_sha256, _observed_size = _independent_digest(python_executable)
    except OSError as exc:
        raise ContractViolation("INDEPENDENT_INVALID", "runtime executable is unreadable") from exc
    if not stat.S_ISREG(executable_mode):
        raise ContractViolation("INDEPENDENT_INVALID", "runtime executable is not regular")
    if executable_sha256 != ContractV1.EXPECTED_INTERPRETER_SHA256:
        raise ContractViolation("BASE_OR_PREIMAGE_DRIFT", "interpreter digest mismatch")
    return runtime_root, site_root, python_executable


def _observe_independent_runtime_properties(
    request: dict[str, Any], executable: str
) -> dict[str, str]:
    """Independently observe actual target interpreter and platform values."""

    implementation_name = getattr(sys.implementation, "name", "")
    observed_version = ".".join(map(str, sys.version_info[:3]))
    observed_machine = platform.machine().casefold()
    observed_platform = f"{sys.platform}-{observed_machine}"
    observed_executable = os.path.abspath(sys.executable)
    try:
        identical_inode = os.path.samefile(observed_executable, executable)
    except OSError as exc:
        raise ContractViolation(
            "INDEPENDENT_INVALID", "independent executable identity unavailable"
        ) from exc
    if (
        implementation_name != "cpython"
        or observed_version != ContractV1.EXPECTED_PYTHON_VERSION
        or sys.platform != "linux"
        or observed_machine != "x86_64"
        or observed_platform != ContractV1.EXPECTED_PLATFORM_TAG
        or observed_executable != executable
        or not identical_inode
        or request["runtime"]["implementation"] != ContractV1.EXPECTED_IMPLEMENTATION
        or request["runtime"]["python_version"] != observed_version
        or request["runtime"]["platform_tag"] != observed_platform
    ):
        raise ContractViolation(
            "BASE_OR_PREIMAGE_DRIFT", "independent runtime properties mismatch"
        )
    return {
        "implementation": ContractV1.EXPECTED_IMPLEMENTATION,
        "python_version": observed_version,
        "platform_tag": observed_platform,
        "executable": observed_executable,
    }


def _physical_first(site_root: str) -> tuple[dict[str, str], dict[str, int]]:
    regular: dict[str, str] = {}
    counters = {
        "regular": 0,
        "directory": 0,
        "symlink": 0,
        "other": 0,
        "pyc": 0,
        "pycache": 0,
    }
    work = [site_root]
    while work:
        directory = work.pop()
        try:
            with os.scandir(directory) as scanner:
                children = sorted(scanner, key=lambda child: child.name, reverse=True)
        except OSError as exc:
            raise ContractViolation("INDEPENDENT_INVALID", "physical site scan failed") from exc
        for child in children:
            relative = os.path.relpath(child.path, site_root).replace(os.sep, "/")
            observed = child.stat(follow_symlinks=False)
            if stat.S_ISLNK(observed.st_mode):
                counters["symlink"] += 1
            elif stat.S_ISDIR(observed.st_mode):
                counters["directory"] += 1
                if child.name == "__pycache__":
                    counters["pycache"] += 1
                else:
                    work.append(child.path)
            elif stat.S_ISREG(observed.st_mode):
                counters["regular"] += 1
                if relative in regular:
                    raise ContractViolation("INDEPENDENT_INVALID", "duplicate physical path")
                regular[relative] = child.path
                if relative.endswith(".pyc"):
                    counters["pyc"] += 1
            else:
                counters["other"] += 1
    return regular, counters


def _direct_metadata_slots(physical: dict[str, str]) -> dict[str, tuple[str, str, str]]:
    slots: dict[str, tuple[str, str, str]] = {}
    for relative, path in sorted(physical.items()):
        if not relative.endswith(".dist-info/METADATA"):
            continue
        try:
            with open(path, "rb") as source:
                metadata = BytesParser().parse(source, headersonly=True)
        except (OSError, UnicodeError) as exc:
            raise ContractViolation("INDEPENDENT_INVALID", "METADATA parse failed") from exc
        raw_name = metadata.get("Name")
        version = metadata.get("Version")
        if not raw_name or not version:
            raise ContractViolation("INDEPENDENT_INVALID", "METADATA lacks Name or Version")
        normalized_name = _independent_name(raw_name)
        if normalized_name in slots:
            raise ContractViolation("INDEPENDENT_INVALID", "duplicate normalized distribution")
        dist_info = relative[: -len("/METADATA")]
        record_relative = f"{dist_info}/RECORD"
        record_path = physical.get(record_relative)
        if record_path is None:
            raise ContractViolation("INDEPENDENT_INVALID", "physical RECORD is absent")
        slots[normalized_name] = (version, record_relative, record_path)
    return slots


def _independent_record_hash(value: str) -> str:
    split = value.split("=", 1)
    if (
        len(split) != 2
        or split[0] != "sha256"
        or re.fullmatch(r"[A-Za-z0-9_-]+", split[1]) is None
    ):
        raise ContractViolation("INDEPENDENT_INVALID", "unsupported RECORD digest")
    try:
        decoded = base64.b64decode(
            split[1] + "=" * ((4 - len(split[1]) % 4) % 4),
            altchars=b"-_",
            validate=True,
        )
    except (ValueError, TypeError) as exc:
        raise ContractViolation("INDEPENDENT_INVALID", "RECORD digest encoding invalid") from exc
    if len(decoded) != 32:
        raise ContractViolation("INDEPENDENT_INVALID", "RECORD digest length invalid")
    normalized = base64.urlsafe_b64encode(decoded).rstrip(b"=").decode("ascii")
    if split[1] != normalized:
        raise ContractViolation(
            "INDEPENDENT_INVALID", "RECORD digest encoding is non-canonical"
        )
    return decoded.hex()


def _independent_claim(
    runtime_root: str, site_root: str, raw_path: str
) -> tuple[str, str, str]:
    if (
        not raw_path
        or raw_path.startswith("/")
        or "\\" in raw_path
        or "\x00" in raw_path
        or any(ord(character) < 32 or ord(character) == 127 for character in raw_path)
    ):
        raise ContractViolation("INDEPENDENT_INVALID", "invalid RECORD path text")
    normalized = posixpath.normpath(raw_path)
    if normalized != raw_path or normalized in ("", "."):
        raise ContractViolation("INDEPENDENT_INVALID", "RECORD path normalization drift")
    candidate = os.path.abspath(os.path.join(site_root, *normalized.split("/")))
    try:
        if os.path.commonpath((runtime_root, candidate)) != runtime_root:
            raise ContractViolation("INDEPENDENT_INVALID", "RECORD path escapes runtime")
    except ValueError as exc:
        raise ContractViolation("INDEPENDENT_INVALID", "RECORD path escapes runtime") from exc
    _independent_no_symlink(candidate)
    try:
        within_site = os.path.commonpath((site_root, candidate)) == site_root
    except ValueError:
        within_site = False
    if within_site and candidate != site_root:
        return "SITE", os.path.relpath(candidate, site_root).replace(os.sep, "/"), candidate
    runtime_bin = os.path.join(runtime_root, "bin")
    if os.path.dirname(candidate) != runtime_bin or not os.path.basename(candidate):
        raise ContractViolation("INDEPENDENT_INVALID", "external claim is not a bin direct child")
    return "EXTERNAL", os.path.relpath(candidate, runtime_root).replace(os.sep, "/"), candidate


def _independent_console_scripts(path: str | None) -> set[str]:
    if path is None:
        return set()
    try:
        with open(path, "r", encoding="utf-8", errors="strict", newline="") as source:
            body = source.read()
        parsed = configparser.ConfigParser(interpolation=None, strict=True)
        parsed.optionxform = str
        parsed.read_string(body)
    except (OSError, UnicodeError, configparser.Error) as exc:
        raise ContractViolation("INDEPENDENT_INVALID", "entry_points.txt parse failed") from exc
    if not parsed.has_section("console_scripts"):
        return set()
    names = set(parsed.options("console_scripts"))
    if any(not name or "/" in name or "\\" in name for name in names):
        raise ContractViolation("INDEPENDENT_INVALID", "console-script name invalid")
    return names


def _reverse_claims(
    runtime_root: str,
    site_root: str,
    name: str,
    version: str,
    record_relative: str,
    record_path: str,
) -> tuple[list[dict[str, Any]], dict[str, Any], list[str]]:
    try:
        with open(record_path, "r", encoding="utf-8", errors="strict", newline="") as source:
            record_rows = list(csv.reader(source))
    except (OSError, UnicodeError, csv.Error) as exc:
        raise ContractViolation("INDEPENDENT_INVALID", "RECORD parse failed") from exc
    ownership_rows: list[dict[str, Any]] = []
    closure_rows: list[dict[str, Any]] = []
    external_rows: list[tuple[str, str]] = []
    entry_points_path: str | None = None
    self_count = 0
    seen: set[str] = set()
    for record_row in record_rows:
        if len(record_row) != 3:
            raise ContractViolation("INDEPENDENT_INVALID", "malformed RECORD row")
        raw_path, record_hash, record_size = record_row
        domain, relative, actual_path = _independent_claim(runtime_root, site_root, raw_path)
        claim_key = f"{domain}:{relative}"
        if claim_key in seen:
            raise ContractViolation("INDEPENDENT_INVALID", "duplicate RECORD claim")
        seen.add(claim_key)
        try:
            actual_mode = os.lstat(actual_path).st_mode
            actual_hash, actual_size = _independent_digest(actual_path)
        except OSError as exc:
            raise ContractViolation("INDEPENDENT_INVALID", "RECORD claim is unreadable") from exc
        if not stat.S_ISREG(actual_mode):
            raise ContractViolation("INDEPENDENT_INVALID", "RECORD claim is not regular")
        record_self = domain == "SITE" and relative == record_relative
        if record_self:
            self_count += 1
            if record_hash or record_size:
                raise ContractViolation("INDEPENDENT_INVALID", "RECORD self fields are not empty")
        else:
            if not record_hash or not record_size:
                raise ContractViolation("INDEPENDENT_INVALID", "non-self RECORD fields are empty")
            if _independent_record_hash(record_hash) != actual_hash:
                raise ContractViolation("INDEPENDENT_INVALID", "RECORD digest mismatch")
            try:
                expected_size = int(record_size, 10)
            except ValueError as exc:
                raise ContractViolation("INDEPENDENT_INVALID", "RECORD size invalid") from exc
            if record_size != str(expected_size) or expected_size != actual_size:
                raise ContractViolation("INDEPENDENT_INVALID", "RECORD size mismatch")
        if record_self:
            continue
        if domain == "EXTERNAL":
            external_rows.append((relative, os.path.basename(actual_path)))
            continue
        if relative.endswith(".pyc") or "__pycache__" in relative.split("/"):
            raise ContractViolation("INDEPENDENT_INVALID", "bytecode/cache claim present")
        closure_rows.append(
            {"path": relative, "sha256": actual_hash, "size": actual_size}
        )
        if relative.endswith(".dist-info/entry_points.txt"):
            entry_points_path = actual_path
        ownership_rows.append(
            {
                "normalized_distribution_name": name,
                "relative_path": relative,
                "byte_count": actual_size,
                "raw_sha256": actual_hash,
            }
        )
    if self_count != 1:
        raise ContractViolation("INDEPENDENT_INVALID", "RECORD self cardinality invalid")
    if {basename for _relative, basename in external_rows} != _independent_console_scripts(
        entry_points_path
    ):
        raise ContractViolation("INDEPENDENT_INVALID", "external entrypoint set mismatch")
    closure_rows.sort(key=lambda row: row["path"])
    closure_sha256 = canonical_sha256({"record_entries": closure_rows})
    expected_sha256 = {
        slot_name: slot_sha256
        for slot_name, _slot_version, slot_sha256 in ContractV1.EXPECTED_RECORD_CLOSURES
    }[name]
    if closure_sha256 != expected_sha256:
        raise ContractViolation("INDEPENDENT_INVALID", "installed RECORD closure mismatch")
    return (
        ownership_rows,
        {
            "normalized_distribution_name": name,
            "distribution_version": version,
            "installed_record_closure_sha256": closure_sha256,
        },
        [relative for relative, _basename in external_rows],
    )


def _independent_full_root(runtime_root: str) -> str:
    manifest: list[dict[str, Any]] = []
    queue = [runtime_root]
    while queue:
        directory = queue.pop()
        try:
            with os.scandir(directory) as scanner:
                entries = sorted(scanner, key=lambda child: child.name, reverse=True)
        except OSError as exc:
            raise ContractViolation("INDEPENDENT_INVALID", "full-root scan failed") from exc
        for entry in entries:
            relative = os.path.relpath(entry.path, runtime_root).replace(os.sep, "/")
            observed = entry.stat(follow_symlinks=False)
            permissions = stat.S_IMODE(observed.st_mode)
            if stat.S_ISDIR(observed.st_mode):
                manifest.append({"kind": "directory", "mode": permissions, "relative_path": relative})
                queue.append(entry.path)
            elif stat.S_ISREG(observed.st_mode):
                digest, length = _independent_digest(entry.path)
                manifest.append(
                    {
                        "kind": "regular",
                        "mode": permissions,
                        "relative_path": relative,
                        "size": length,
                        "raw_sha256": digest,
                    }
                )
            elif stat.S_ISLNK(observed.st_mode):
                target_bytes = os.readlink(entry.path).encode("utf-8", "surrogateescape")
                manifest.append(
                    {
                        "kind": "symlink",
                        "mode": permissions,
                        "relative_path": relative,
                        "target_sha256": hashlib.sha256(target_bytes).hexdigest(),
                    }
                )
            else:
                manifest.append({"kind": "other", "mode": permissions, "relative_path": relative})
    manifest.sort(key=lambda row: row["relative_path"])
    return canonical_sha256(manifest)


def _independent_identity(
    request: dict[str, Any],
    runtime_root: str,
    executable: str,
    manifest_sha256: str,
    full_root_sha256: str,
) -> dict[str, Any]:
    executable_sha256, _size = _independent_digest(executable)
    control_identity = canonical_sha256(
        {
            "relative_path": ContractV1.EXPECTED_EXECUTABLE_RELATIVE,
            "stat": _independent_stat(executable),
            "raw_sha256": executable_sha256,
        }
    )
    logical_identity = canonical_sha256(
        {
            "formal_lock_logical_sha256": ContractV1.LOCK_LOGICAL_SHA256,
            "runner_projection_sha256": ContractV1.PROJECTION_SHA256,
            "accepted_wheel_manifest_sha256": ContractV1.WHEEL_MANIFEST_SHA256,
            "distribution_closure_sha256": ContractV1.DISTRIBUTION_CLOSURE_SHA256,
            "installed_file_manifest_sha256": manifest_sha256,
            "resolved_interpreter_executable_sha256": executable_sha256,
            "environment_policy_sha256": ContractV1.ENVIRONMENT_POLICY_SHA256,
            "required_role_path_ordered_sha256": ContractV1.REQUIRED_ROLE_PATH_ORDERED_SHA256,
            "admitted_executable_relative_path": ContractV1.EXPECTED_EXECUTABLE_RELATIVE,
        }
    )
    content_identity = canonical_sha256(
        {
            "logical_runtime_id": logical_identity,
            "full_runtime_root_manifest_sha256": full_root_sha256,
        }
    )
    root_identity = canonical_sha256(
        {
            "root_stat": _independent_stat(runtime_root),
            "full_runtime_root_manifest_sha256": full_root_sha256,
        }
    )
    observation_identity = canonical_sha256(
        {
            "observation_session_id": request["observation_session_id"],
            "materialization_event_id": request["materialization"]["event_id"],
            "logical_runtime_id": logical_identity,
            "runtime_content_identity": content_identity,
            "runtime_root_identity_sha256": root_identity,
            "entrypoint_control_identity_sha256": control_identity,
        }
    )
    return {
        "logical_runtime_id": logical_identity,
        "runtime_content_identity": content_identity,
        "runtime_root_identity_sha256": root_identity,
        "runtime_instance_observation_id": observation_identity,
        "materialization_event_id": request["materialization"]["event_id"],
        "formal_lock_logical_sha256": ContractV1.LOCK_LOGICAL_SHA256,
        "runner_projection_sha256": ContractV1.PROJECTION_SHA256,
        "accepted_wheel_manifest_sha256": ContractV1.WHEEL_MANIFEST_SHA256,
        "distribution_closure_sha256": ContractV1.DISTRIBUTION_CLOSURE_SHA256,
        "installed_file_manifest_sha256": manifest_sha256,
        "full_runtime_root_manifest_sha256": full_root_sha256,
        "entrypoint_control_identity_sha256": control_identity,
        "resolved_interpreter_executable_sha256": executable_sha256,
        "environment_policy_sha256": ContractV1.ENVIRONMENT_POLICY_SHA256,
        "required_role_path_ordered_sha256": ContractV1.REQUIRED_ROLE_PATH_ORDERED_SHA256,
        "admitted_executable_relative_path": ContractV1.EXPECTED_EXECUTABLE_RELATIVE,
        "distribution_count": 5,
        "record_closure_match_count": 5,
        "unexpected_entry_count": 0,
    }


def _derive_independent_impl(request: dict[str, Any]) -> dict[str, Any]:
    request = validate_request(request)
    runtime_root, site_root, executable = _independent_locators(request)
    _observe_independent_runtime_properties(request, executable)
    physical, counts = _physical_first(site_root)
    slots = _direct_metadata_slots(physical)
    if set(slots) != {name for name, _version in ContractV1.EXPECTED_DISTRIBUTIONS}:
        raise ContractViolation("INDEPENDENT_INVALID", "physical distribution set is not exact5")

    rows: list[dict[str, Any]] = []
    closures: list[dict[str, Any]] = []
    record_self_paths: set[str] = set()
    external_paths: set[str] = set()
    external_claim_count = 0
    reverse_owner: dict[str, str] = {}
    duplicate_count = 0
    for name, expected_version in ContractV1.EXPECTED_DISTRIBUTIONS:
        version, record_relative, record_path = slots[name]
        if version != expected_version:
            raise ContractViolation("INDEPENDENT_INVALID", "physical distribution version mismatch")
        dist_rows, closure, external = _reverse_claims(
            runtime_root, site_root, name, version, record_relative, record_path
        )
        for row in dist_rows:
            relative = row["relative_path"]
            if relative in reverse_owner:
                duplicate_count += 1
            reverse_owner[relative] = name
            rows.append(row)
        closures.append(closure)
        record_self_paths.add(record_relative)
        external_paths.update(external)
        external_claim_count += len(external)

    if external_claim_count != len(external_paths):
        raise ContractViolation(
            "INDEPENDENT_INVALID", "duplicate cross-distribution external claim"
        )

    rank = {name: index for index, (name, _version) in enumerate(ContractV1.EXPECTED_DISTRIBUTIONS)}
    rows.sort(key=lambda row: (rank[row["normalized_distribution_name"]], row["relative_path"]))
    manifest_sha256 = canonical_sha256(rows)
    if manifest_sha256 != ContractV1.INSTALLED_MANIFEST_COMPARATOR_SHA256:
        raise ContractViolation("INDEPENDENT_INVALID", "installed manifest comparator mismatch")
    if canonical_sha256(closures) != ContractV1.DISTRIBUTION_CLOSURE_SHA256:
        raise ContractViolation("INDEPENDENT_INVALID", "aggregate closure mismatch")

    eligible = set(physical) - record_self_paths
    claimed = set(reverse_owner)
    unowned = eligible - claimed
    missing = claimed - eligible
    if (
        duplicate_count
        or unowned
        or missing
        or counts["symlink"]
        or counts["other"]
        or counts["pyc"]
        or counts["pycache"]
    ):
        raise ContractViolation("INDEPENDENT_INVALID", "reverse ownership is not a full match")
    manifest_bytes = canonical_json_bytes(rows)
    diagnostic = {
        "canonical_row_count": len(rows),
        "canonical_preimage_bytes": len(manifest_bytes),
        "canonical_preimage_lf": manifest_bytes.count(b"\n"),
        "site_regular_file_count": counts["regular"],
        "site_directory_count": counts["directory"],
        "site_symlink_count": counts["symlink"],
        "site_other_count": counts["other"],
        "eligible_regular_payload_count": len(eligible),
        "owned_file_count": len(claimed & eligible),
        "unowned_file_count": len(unowned),
        "duplicate_relative_path_count": duplicate_count,
        "missing_file_count": len(missing),
        "extra_file_count": len(unowned),
        "pyc_file_count": counts["pyc"],
        "pycache_directory_count": counts["pycache"],
        "record_self_excluded_count": len(record_self_paths),
        "verified_external_entrypoint_count": len(external_paths),
        "external_entrypoint_pathset_sha256": canonical_sha256(
            sorted(hashlib.sha256(path.encode("utf-8")).hexdigest() for path in external_paths)
        ),
        "canonical_pathset_sha256": canonical_sha256(sorted(claimed)),
        "mismatch_row_sha256": _INDEPENDENT_EMPTY_ROWS_SHA256,
        "mismatch_row_count": 0,
        "nonzero_mismatch_family_count": 0,
    }
    full_root_sha256 = _independent_full_root(runtime_root)
    if (
        full_root_sha256
        != request["materialization"]["expected_full_root_manifest_sha256"]
    ):
        raise ContractViolation(
            "INDEPENDENT_INVALID", "full runtime root manifest mismatch"
        )
    return {
        "schema_version": ContractV1.ROLE_RESULT_SCHEMA,
        "role": "independent",
        "status": "VALID",
        "process_id": os.getpid(),
        "strategy": "FILESYSTEM_FIRST_REVERSE_OWNERSHIP_RECONCILIATION",
        "runtime_identity_exact19": _independent_identity(
            request, runtime_root, executable, manifest_sha256, full_root_sha256
        ),
        "manifest_sha256": manifest_sha256,
        "manifest_rows": rows,
        "distribution_closures": closures,
        "canonical_diagnostic": diagnostic,
    }


def derive_independent(request: dict[str, Any]) -> dict[str, Any]:
    """Return a private VALID reverse-ownership result or fail closed."""

    try:
        return _derive_independent_impl(request)
    except ContractViolation:
        raise
    except (OSError, UnicodeError, ValueError, csv.Error, configparser.Error) as exc:
        raise ContractViolation(
            "INDEPENDENT_INVALID", "independent derivation failed closed"
        ) from exc


def _independent_invalid(code: str) -> dict[str, Any]:
    return {
        "schema_version": "emlis.nls_v3.s11.g4b.runtime_admission.role_failure.v1",
        "role": "independent",
        "status": "INVALID",
        "code": code,
    }


def main() -> int:
    try:
        result = derive_independent(read_strict_json(sys.stdin.buffer))
    except ContractViolation as exc:
        write_strict_json(_independent_invalid(exc.code), sys.stdout.buffer)
        return 2
    except Exception:
        write_strict_json(_independent_invalid("INTERNAL_FAIL_CLOSED"), sys.stdout.buffer)
        return 3
    write_strict_json(result, sys.stdout.buffer)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
