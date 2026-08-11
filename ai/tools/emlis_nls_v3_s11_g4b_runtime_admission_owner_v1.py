#!/usr/bin/env python3
"""Distribution-first owner derivation for the G4-B V1 checker.

The owner starts from ``importlib.metadata`` distributions and their RECORD
claims.  It independently verifies every claimed byte, then reconciles those
claims against a no-follow physical inventory.  It never imports the
independent role, creates a file, repairs a runtime, or performs network I/O.
"""

from __future__ import annotations

import base64
import configparser
import csv
import hashlib
import importlib.metadata
import io
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


_EMPTY_ROWS_SHA256 = canonical_sha256([])


def _normalized_name(value: str) -> str:
    return re.sub(r"[-_.]+", "-", value).lower()


def _file_digest(path: str) -> tuple[str, int]:
    digest = hashlib.sha256()
    size = 0
    with open(path, "rb") as handle:
        for block in iter(lambda: handle.read(131_072), b""):
            digest.update(block)
            size += len(block)
    return digest.hexdigest(), size


def _stat_vector(path: str) -> list[int]:
    item = os.lstat(path)
    return [
        item.st_dev,
        item.st_ino,
        stat.S_IMODE(item.st_mode),
        item.st_size,
        item.st_mtime_ns,
    ]


def _assert_no_symlink_components(path: str, code: str) -> None:
    absolute = os.path.abspath(path)
    current = os.path.sep
    for component in absolute.split(os.path.sep)[1:]:
        current = os.path.join(current, component)
        try:
            mode = os.lstat(current).st_mode
        except OSError as exc:
            raise ContractViolation(code, "required locator component is absent") from exc
        if stat.S_ISLNK(mode):
            raise ContractViolation(code, "symlink component is forbidden")


def _validate_locator(request: dict[str, Any]) -> tuple[str, str, str]:
    root = request["materialization"]["root"]
    site = os.path.join(root, *request["materialization"]["site_packages_relative"].split("/"))
    executable = request["runtime"]["executable"]
    for path in (root, site, executable):
        _assert_no_symlink_components(path, "OWNER_INVALID")
    if not os.path.isdir(root) or not os.path.isdir(site):
        raise ContractViolation("OWNER_INVALID", "runtime root or site-packages is absent")
    try:
        executable_mode = os.lstat(executable).st_mode
        executable_sha256, _size = _file_digest(executable)
    except OSError as exc:
        raise ContractViolation("OWNER_INVALID", "admitted executable is unreadable") from exc
    if not stat.S_ISREG(executable_mode):
        raise ContractViolation("OWNER_INVALID", "admitted executable is not a regular file")
    if executable_sha256 != ContractV1.EXPECTED_INTERPRETER_SHA256:
        raise ContractViolation("BASE_OR_PREIMAGE_DRIFT", "interpreter digest mismatch")
    return root, site, executable


def _observe_owner_runtime_properties(
    request: dict[str, Any], executable: str
) -> dict[str, str]:
    """Observe target-process properties without trusting request labels."""

    implementation = getattr(sys.implementation, "name", "")
    version = ".".join(str(part) for part in sys.version_info[:3])
    machine = platform.machine().lower()
    platform_tag = f"{sys.platform}-{machine}"
    observed_executable = os.path.abspath(sys.executable)
    try:
        same_file = os.path.samefile(observed_executable, executable)
    except OSError as exc:
        raise ContractViolation("OWNER_INVALID", "target executable identity is unavailable") from exc
    if (
        implementation != "cpython"
        or version != ContractV1.EXPECTED_PYTHON_VERSION
        or sys.platform != "linux"
        or machine != "x86_64"
        or platform_tag != ContractV1.EXPECTED_PLATFORM_TAG
        or observed_executable != executable
        or not same_file
        or request["runtime"]["implementation"] != ContractV1.EXPECTED_IMPLEMENTATION
        or request["runtime"]["python_version"] != version
        or request["runtime"]["platform_tag"] != platform_tag
    ):
        raise ContractViolation("BASE_OR_PREIMAGE_DRIFT", "owner runtime properties mismatch")
    return {
        "implementation": ContractV1.EXPECTED_IMPLEMENTATION,
        "python_version": version,
        "platform_tag": platform_tag,
        "executable": observed_executable,
    }


def _record_digest(value: str, code: str) -> str:
    pieces = value.split("=", 1)
    if (
        len(pieces) != 2
        or pieces[0] != "sha256"
        or re.fullmatch(r"[A-Za-z0-9_-]+", pieces[1]) is None
    ):
        raise ContractViolation(code, "RECORD digest is not sha256")
    try:
        decoded = base64.b64decode(
            pieces[1] + "=" * ((4 - len(pieces[1]) % 4) % 4),
            altchars=b"-_",
            validate=True,
        )
    except (ValueError, TypeError) as exc:
        raise ContractViolation(code, "RECORD digest encoding is invalid") from exc
    if len(decoded) != 32:
        raise ContractViolation(code, "RECORD digest length is invalid")
    canonical = base64.urlsafe_b64encode(decoded).rstrip(b"=").decode("ascii")
    if pieces[1] != canonical:
        raise ContractViolation(code, "RECORD digest encoding is non-canonical")
    return decoded.hex()


def _claim_locator(root: str, site: str, raw_path: str) -> tuple[str, str, str]:
    if (
        not raw_path
        or raw_path.startswith("/")
        or "\\" in raw_path
        or "\x00" in raw_path
        or any(ord(character) < 32 or ord(character) == 127 for character in raw_path)
    ):
        raise ContractViolation("OWNER_INVALID", "RECORD path is not canonical POSIX text")
    normalized = posixpath.normpath(raw_path)
    if normalized in ("", ".") or normalized != raw_path:
        raise ContractViolation("OWNER_INVALID", "RECORD path normalization changed the path")
    candidate = os.path.abspath(os.path.join(site, *normalized.split("/")))
    try:
        if os.path.commonpath((root, candidate)) != root:
            raise ContractViolation("OWNER_INVALID", "RECORD path escapes runtime root")
    except ValueError as exc:
        raise ContractViolation("OWNER_INVALID", "RECORD path escapes runtime root") from exc
    _assert_no_symlink_components(candidate, "OWNER_INVALID")
    try:
        site_common = os.path.commonpath((site, candidate))
    except ValueError:
        site_common = ""
    if site_common == site and candidate != site:
        relative = os.path.relpath(candidate, site).replace(os.sep, "/")
        return "SITE", relative, candidate
    expected_bin = os.path.join(root, "bin")
    if os.path.dirname(candidate) != expected_bin or not os.path.basename(candidate):
        raise ContractViolation("OWNER_INVALID", "external RECORD row is not a bin direct child")
    relative = os.path.relpath(candidate, root).replace(os.sep, "/")
    return "EXTERNAL", relative, candidate


def _console_scripts(path: str | None) -> set[str]:
    if path is None:
        return set()
    try:
        with open(path, "r", encoding="utf-8", errors="strict", newline="") as handle:
            text = handle.read()
        parser = configparser.ConfigParser(interpolation=None, strict=True)
        parser.optionxform = str
        parser.read_string(text)
    except (OSError, UnicodeError, configparser.Error) as exc:
        raise ContractViolation("OWNER_INVALID", "entry_points.txt is invalid") from exc
    if not parser.has_section("console_scripts"):
        return set()
    names = set(parser.options("console_scripts"))
    if any(not name or "/" in name or "\\" in name for name in names):
        raise ContractViolation("OWNER_INVALID", "console-script key is invalid")
    return names


def _distribution_claims(
    distribution: importlib.metadata.Distribution,
    name: str,
    root: str,
    site: str,
) -> tuple[list[dict[str, Any]], dict[str, Any], str, list[str]]:
    files = tuple(distribution.files or ())
    record_candidates = [
        item
        for item in files
        if item.name == "RECORD" and item.parent.name.endswith(".dist-info")
    ]
    if len(record_candidates) != 1:
        raise ContractViolation("OWNER_INVALID", "installed RECORD cardinality is not exact1")
    record_path = os.fspath(distribution.locate_file(record_candidates[0]))
    _assert_no_symlink_components(record_path, "OWNER_INVALID")
    record_relative = os.path.relpath(record_path, site).replace(os.sep, "/")
    try:
        with open(record_path, "r", encoding="utf-8", errors="strict", newline="") as handle:
            record_rows = list(csv.reader(handle))
    except (OSError, UnicodeError, csv.Error) as exc:
        raise ContractViolation("OWNER_INVALID", "installed RECORD is unreadable") from exc

    manifest_rows: list[dict[str, Any]] = []
    closure_entries: list[dict[str, Any]] = []
    external: list[tuple[str, str]] = []
    entry_points_path: str | None = None
    record_self_count = 0
    seen_claims: set[str] = set()
    for record_row in record_rows:
        if len(record_row) != 3:
            raise ContractViolation("OWNER_INVALID", "installed RECORD row is malformed")
        raw_path, claimed_digest, claimed_size = record_row
        domain, relative, path = _claim_locator(root, site, raw_path)
        claim_key = f"{domain}:{relative}"
        if claim_key in seen_claims:
            raise ContractViolation("OWNER_INVALID", "duplicate installed RECORD path")
        seen_claims.add(claim_key)
        try:
            mode = os.lstat(path).st_mode
            actual_sha256, actual_size = _file_digest(path)
        except OSError as exc:
            raise ContractViolation("OWNER_INVALID", "RECORD claim is unreadable") from exc
        if not stat.S_ISREG(mode):
            raise ContractViolation("OWNER_INVALID", "RECORD claim is not a regular file")
        is_record_self = domain == "SITE" and relative == record_relative
        if is_record_self:
            record_self_count += 1
            if claimed_digest or claimed_size:
                raise ContractViolation("OWNER_INVALID", "RECORD self row must have empty hash and size")
        else:
            if not claimed_digest or not claimed_size:
                raise ContractViolation("OWNER_INVALID", "non-self RECORD row lacks hash or size")
            if _record_digest(claimed_digest, "OWNER_INVALID") != actual_sha256:
                raise ContractViolation("OWNER_INVALID", "RECORD hash mismatch")
            try:
                expected_size = int(claimed_size, 10)
            except ValueError as exc:
                raise ContractViolation("OWNER_INVALID", "RECORD size is invalid") from exc
            if claimed_size != str(expected_size) or expected_size != actual_size:
                raise ContractViolation("OWNER_INVALID", "RECORD size mismatch")
        if is_record_self:
            continue
        if domain == "EXTERNAL":
            external.append((relative, os.path.basename(path)))
            continue
        if relative.endswith(".pyc") or "__pycache__" in relative.split("/"):
            raise ContractViolation("OWNER_INVALID", "bytecode/cache payload is prohibited")
        closure_entries.append(
            {"path": relative, "sha256": actual_sha256, "size": actual_size}
        )
        if relative.endswith(".dist-info/entry_points.txt"):
            entry_points_path = path
        manifest_rows.append(
            {
                "normalized_distribution_name": name,
                "relative_path": relative,
                "byte_count": actual_size,
                "raw_sha256": actual_sha256,
            }
        )
    if record_self_count != 1:
        raise ContractViolation("OWNER_INVALID", "RECORD self cardinality is not exact1")
    allowed_scripts = _console_scripts(entry_points_path)
    if {basename for _relative, basename in external} != allowed_scripts:
        raise ContractViolation("OWNER_INVALID", "external entrypoint set mismatch")
    closure_entries.sort(key=lambda item: item["path"])
    closure_sha256 = canonical_sha256({"record_entries": closure_entries})
    expected = {
        slot_name: slot_sha
        for slot_name, _slot_version, slot_sha in ContractV1.EXPECTED_RECORD_CLOSURES
    }[name]
    if closure_sha256 != expected:
        raise ContractViolation("OWNER_INVALID", "installed RECORD closure mismatch")
    return (
        manifest_rows,
        {
            "normalized_distribution_name": name,
            "distribution_version": distribution.version,
            "installed_record_closure_sha256": closure_sha256,
        },
        record_relative,
        [relative for relative, _basename in external],
    )


def _site_inventory(site: str) -> tuple[set[str], dict[str, int]]:
    regular: set[str] = set()
    counts = {"regular": 0, "directory": 0, "symlink": 0, "other": 0, "pyc": 0, "pycache": 0}
    pending = [site]
    while pending:
        directory = pending.pop()
        try:
            with os.scandir(directory) as iterator:
                entries = sorted(iterator, key=lambda item: item.name, reverse=True)
        except OSError as exc:
            raise ContractViolation("OWNER_INVALID", "site inventory failed") from exc
        for entry in entries:
            relative = os.path.relpath(entry.path, site).replace(os.sep, "/")
            mode = entry.stat(follow_symlinks=False).st_mode
            if stat.S_ISLNK(mode):
                counts["symlink"] += 1
            elif stat.S_ISDIR(mode):
                counts["directory"] += 1
                if entry.name == "__pycache__":
                    counts["pycache"] += 1
                else:
                    pending.append(entry.path)
            elif stat.S_ISREG(mode):
                counts["regular"] += 1
                regular.add(relative)
                if relative.endswith(".pyc"):
                    counts["pyc"] += 1
            else:
                counts["other"] += 1
    return regular, counts


def _full_root_manifest(root: str) -> str:
    rows: list[dict[str, Any]] = []
    pending = [root]
    while pending:
        directory = pending.pop()
        try:
            with os.scandir(directory) as iterator:
                entries = sorted(iterator, key=lambda item: item.name, reverse=True)
        except OSError as exc:
            raise ContractViolation("OWNER_INVALID", "full-root inventory failed") from exc
        for entry in entries:
            relative = os.path.relpath(entry.path, root).replace(os.sep, "/")
            observed = entry.stat(follow_symlinks=False)
            mode = stat.S_IMODE(observed.st_mode)
            if stat.S_ISDIR(observed.st_mode):
                rows.append({"kind": "directory", "mode": mode, "relative_path": relative})
                pending.append(entry.path)
            elif stat.S_ISREG(observed.st_mode):
                raw_sha256, size = _file_digest(entry.path)
                rows.append(
                    {
                        "kind": "regular",
                        "mode": mode,
                        "relative_path": relative,
                        "size": size,
                        "raw_sha256": raw_sha256,
                    }
                )
            elif stat.S_ISLNK(observed.st_mode):
                target = os.readlink(entry.path).encode("utf-8", "surrogateescape")
                rows.append(
                    {
                        "kind": "symlink",
                        "mode": mode,
                        "relative_path": relative,
                        "target_sha256": hashlib.sha256(target).hexdigest(),
                    }
                )
            else:
                rows.append({"kind": "other", "mode": mode, "relative_path": relative})
    rows.sort(key=lambda item: item["relative_path"])
    return canonical_sha256(rows)


def _identity_exact19(
    request: dict[str, Any],
    root: str,
    executable: str,
    manifest_sha256: str,
    full_root_sha256: str,
) -> dict[str, Any]:
    executable_sha256, _size = _file_digest(executable)
    control = canonical_sha256(
        {
            "relative_path": ContractV1.EXPECTED_EXECUTABLE_RELATIVE,
            "stat": _stat_vector(executable),
            "raw_sha256": executable_sha256,
        }
    )
    logical = canonical_sha256(
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
    content = canonical_sha256(
        {
            "logical_runtime_id": logical,
            "full_runtime_root_manifest_sha256": full_root_sha256,
        }
    )
    root_identity = canonical_sha256(
        {"root_stat": _stat_vector(root), "full_runtime_root_manifest_sha256": full_root_sha256}
    )
    instance = canonical_sha256(
        {
            "observation_session_id": request["observation_session_id"],
            "materialization_event_id": request["materialization"]["event_id"],
            "logical_runtime_id": logical,
            "runtime_content_identity": content,
            "runtime_root_identity_sha256": root_identity,
            "entrypoint_control_identity_sha256": control,
        }
    )
    return {
        "logical_runtime_id": logical,
        "runtime_content_identity": content,
        "runtime_root_identity_sha256": root_identity,
        "runtime_instance_observation_id": instance,
        "materialization_event_id": request["materialization"]["event_id"],
        "formal_lock_logical_sha256": ContractV1.LOCK_LOGICAL_SHA256,
        "runner_projection_sha256": ContractV1.PROJECTION_SHA256,
        "accepted_wheel_manifest_sha256": ContractV1.WHEEL_MANIFEST_SHA256,
        "distribution_closure_sha256": ContractV1.DISTRIBUTION_CLOSURE_SHA256,
        "installed_file_manifest_sha256": manifest_sha256,
        "full_runtime_root_manifest_sha256": full_root_sha256,
        "entrypoint_control_identity_sha256": control,
        "resolved_interpreter_executable_sha256": executable_sha256,
        "environment_policy_sha256": ContractV1.ENVIRONMENT_POLICY_SHA256,
        "required_role_path_ordered_sha256": ContractV1.REQUIRED_ROLE_PATH_ORDERED_SHA256,
        "admitted_executable_relative_path": ContractV1.EXPECTED_EXECUTABLE_RELATIVE,
        "distribution_count": 5,
        "record_closure_match_count": 5,
        "unexpected_entry_count": 0,
    }


def _derive_owner_impl(request: dict[str, Any]) -> dict[str, Any]:
    request = validate_request(request)
    root, site, executable = _validate_locator(request)
    _observe_owner_runtime_properties(request, executable)
    distributions: dict[str, importlib.metadata.Distribution] = {}
    for distribution in importlib.metadata.distributions(path=[site]):
        raw_name = distribution.metadata.get("Name")
        if not raw_name:
            raise ContractViolation("OWNER_INVALID", "distribution Name is absent")
        name = _normalized_name(raw_name)
        if name in distributions:
            raise ContractViolation("OWNER_INVALID", "duplicate normalized distribution")
        distributions[name] = distribution
    if set(distributions) != {name for name, _version in ContractV1.EXPECTED_DISTRIBUTIONS}:
        raise ContractViolation("OWNER_INVALID", "installed distribution set is not exact5")

    rows: list[dict[str, Any]] = []
    closures: list[dict[str, Any]] = []
    record_self_paths: set[str] = set()
    external_paths: set[str] = set()
    external_claim_count = 0
    owned: dict[str, str] = {}
    duplicate_count = 0
    for name, expected_version in ContractV1.EXPECTED_DISTRIBUTIONS:
        distribution = distributions[name]
        if distribution.version != expected_version:
            raise ContractViolation("OWNER_INVALID", "distribution version mismatch")
        dist_rows, closure, record_self, external = _distribution_claims(
            distribution, name, root, site
        )
        for row in dist_rows:
            relative = row["relative_path"]
            if relative in owned:
                duplicate_count += 1
            owned[relative] = name
            rows.append(row)
        closures.append(closure)
        record_self_paths.add(record_self)
        external_paths.update(external)
        external_claim_count += len(external)

    if external_claim_count != len(external_paths):
        raise ContractViolation("OWNER_INVALID", "duplicate cross-distribution external claim")

    rank = {name: index for index, (name, _version) in enumerate(ContractV1.EXPECTED_DISTRIBUTIONS)}
    rows.sort(key=lambda item: (rank[item["normalized_distribution_name"]], item["relative_path"]))
    manifest_sha256 = canonical_sha256(rows)
    if manifest_sha256 != ContractV1.INSTALLED_MANIFEST_COMPARATOR_SHA256:
        raise ContractViolation("OWNER_INVALID", "installed manifest comparator mismatch")
    if canonical_sha256(closures) != ContractV1.DISTRIBUTION_CLOSURE_SHA256:
        raise ContractViolation("OWNER_INVALID", "aggregate distribution closure mismatch")

    physical, counts = _site_inventory(site)
    eligible = physical - record_self_paths
    claimed = set(owned)
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
        raise ContractViolation("OWNER_INVALID", "physical inventory does not match RECORD ownership")
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
        "mismatch_row_sha256": _EMPTY_ROWS_SHA256,
        "mismatch_row_count": 0,
        "nonzero_mismatch_family_count": 0,
    }
    full_root_sha256 = _full_root_manifest(root)
    if (
        full_root_sha256
        != request["materialization"]["expected_full_root_manifest_sha256"]
    ):
        raise ContractViolation("OWNER_INVALID", "full runtime root manifest mismatch")
    return {
        "schema_version": ContractV1.ROLE_RESULT_SCHEMA,
        "role": "owner",
        "status": "VALID",
        "process_id": os.getpid(),
        "strategy": "DISTRIBUTION_FIRST_RECORD_CLAIM_CONSTRUCTION",
        "runtime_identity_exact19": _identity_exact19(
            request, root, executable, manifest_sha256, full_root_sha256
        ),
        "manifest_sha256": manifest_sha256,
        "manifest_rows": rows,
        "distribution_closures": closures,
        "canonical_diagnostic": diagnostic,
    }


def derive_owner(request: dict[str, Any]) -> dict[str, Any]:
    """Return a private VALID role result or raise a typed fail-closed fault."""

    try:
        return _derive_owner_impl(request)
    except ContractViolation:
        raise
    except (OSError, UnicodeError, ValueError, csv.Error, configparser.Error) as exc:
        raise ContractViolation("OWNER_INVALID", "owner derivation failed closed") from exc


def _invalid_result(code: str) -> dict[str, Any]:
    return {
        "schema_version": "emlis.nls_v3.s11.g4b.runtime_admission.role_failure.v1",
        "role": "owner",
        "status": "INVALID",
        "code": code,
    }


def main() -> int:
    try:
        result = derive_owner(read_strict_json(sys.stdin.buffer))
    except ContractViolation as exc:
        write_strict_json(_invalid_result(exc.code), sys.stdout.buffer)
        return 2
    except Exception:
        write_strict_json(_invalid_result("INTERNAL_FAIL_CLOSED"), sys.stdout.buffer)
        return 3
    write_strict_json(result, sys.stdout.buffer)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
