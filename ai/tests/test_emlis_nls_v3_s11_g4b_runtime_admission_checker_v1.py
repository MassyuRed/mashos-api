# -*- coding: utf-8 -*-
from __future__ import annotations

"""Contract tests for the G4-B read-only runtime admission checker V1.

The suite owns no tracked fixture, corpus, sample, or production artifact.  All
synthetic runtime data is private to ``tmp_path``; the source-boundary tests
inspect only the four checker-family source files.
"""

import ast
import base64
import csv
import hashlib
import io
import inspect
import json
import os
from pathlib import Path
import stat
import struct
from types import SimpleNamespace
from typing import Any
import zlib

import pytest

from ai.tools import emlis_nls_v3_s11_g4b_runtime_admission_checker_v1 as checker
from ai.tools import emlis_nls_v3_s11_g4b_runtime_admission_contract_v1 as contract
from ai.tools import emlis_nls_v3_s11_g4b_runtime_admission_independent_v1 as independent
from ai.tools import emlis_nls_v3_s11_g4b_runtime_admission_owner_v1 as owner


_TEST_ROOT = Path(__file__).resolve().parent
_REPO_ROOT = _TEST_ROOT.parents[1]
_TOOLS_ROOT = _REPO_ROOT / "ai" / "tools"

_CONTRACT_PATH = (
    _TOOLS_ROOT / "emlis_nls_v3_s11_g4b_runtime_admission_contract_v1.py"
)
_CHECKER_PATH = (
    _TOOLS_ROOT / "emlis_nls_v3_s11_g4b_runtime_admission_checker_v1.py"
)
_OWNER_PATH = _TOOLS_ROOT / "emlis_nls_v3_s11_g4b_runtime_admission_owner_v1.py"
_INDEPENDENT_PATH = (
    _TOOLS_ROOT / "emlis_nls_v3_s11_g4b_runtime_admission_independent_v1.py"
)
_FAMILY_PATHS = (
    _CONTRACT_PATH,
    _CHECKER_PATH,
    _OWNER_PATH,
    _INDEPENDENT_PATH,
)


def _source(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _tree(path: Path) -> ast.Module:
    return ast.parse(_source(path), filename=path.as_posix())


def _imported_modules(path: Path) -> set[str]:
    names: set[str] = set()
    for node in ast.walk(_tree(path)):
        if isinstance(node, ast.Import):
            names.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            names.add(node.module)
    return names


def _call_name(node: ast.Call) -> str:
    parts: list[str] = []
    target: ast.expr = node.func
    while isinstance(target, ast.Attribute):
        parts.append(target.attr)
        target = target.value
    if isinstance(target, ast.Name):
        parts.append(target.id)
    return ".".join(reversed(parts))


def _json_clone(value: dict[str, Any]) -> dict[str, Any]:
    return json.loads(json.dumps(value, ensure_ascii=False))


def _refresh_materialization_attestation(request: dict[str, Any]) -> None:
    materialization = request["materialization"]
    materialization["root_locator_sha256"] = contract.runtime_root_locator_sha256(
        materialization["root"]
    )
    materialization["event_id"] = contract.materialization_event_id(request)


def _valid_request() -> dict[str, Any]:
    root = "/private/fresh-runtime"
    request = {
        "schema_version": contract.ContractV1.REQUEST_SCHEMA,
        "authority_id": "g4b-admission-authority-v1",
        "observation_session_id": "session-current-001",
        "materialization": {
            "event_id": "0" * 64,
            "procedure_ids": list(contract.ContractV1.EXPECTED_PROCEDURE_IDS),
            "fresh_root_nonexistent_before": True,
            "prior_artifact_reuse_count": 0,
            "root": root,
            "root_locator_sha256": contract.runtime_root_locator_sha256(root),
            "expected_full_root_manifest_sha256": "1" * 64,
            "site_packages_relative": "lib/python3.12/site-packages",
            "probe_cwd": "/private/empty-probe-cwd",
        },
        "runtime": {
            "executable": "/private/fresh-runtime/bin/python",
            "implementation": contract.ContractV1.EXPECTED_IMPLEMENTATION,
            "python_version": contract.ContractV1.EXPECTED_PYTHON_VERSION,
            "platform_tag": contract.ContractV1.EXPECTED_PLATFORM_TAG,
            "resolved_interpreter_sha256": (
                contract.ContractV1.EXPECTED_INTERPRETER_SHA256
            ),
        },
        "frozen": {
            "mashos_api_commit": "2" * 40,
            "mashos_api_tree": "3" * 40,
            "lock_raw_sha256": contract.ContractV1.LOCK_RAW_SHA256,
            "lock_logical_sha256": contract.ContractV1.LOCK_LOGICAL_SHA256,
            "projection_sha256": contract.ContractV1.PROJECTION_SHA256,
            "requirements_sha256": contract.ContractV1.REQUIREMENTS_SHA256,
            "wheel_manifest_sha256": contract.ContractV1.WHEEL_MANIFEST_SHA256,
            "distribution_closure_sha256": (
                contract.ContractV1.DISTRIBUTION_CLOSURE_SHA256
            ),
            "installed_manifest_comparator_sha256": (
                contract.ContractV1.INSTALLED_MANIFEST_COMPARATOR_SHA256
            ),
        },
        "handoff": {
            "receiver_session_id": "session-current-001",
            "receiver_nonce": "receiver-current-001",
        },
    }
    _refresh_materialization_attestation(request)
    return request


def _valid_role_result(role: str, *, process_id: int) -> dict[str, Any]:
    rows = [
        {
            "normalized_distribution_name": "iniconfig",
            "relative_path": "iniconfig-2.3.0.dist-info/METADATA",
            "byte_count": 101,
            "raw_sha256": "4" * 64,
        },
        {
            "normalized_distribution_name": "packaging",
            "relative_path": "packaging/__init__.py",
            "byte_count": 202,
            "raw_sha256": "5" * 64,
        },
        {
            "normalized_distribution_name": "pluggy",
            "relative_path": "pluggy/__init__.py",
            "byte_count": 303,
            "raw_sha256": "6" * 64,
        },
        {
            "normalized_distribution_name": "pytest",
            "relative_path": "pytest/__init__.py",
            "byte_count": 404,
            "raw_sha256": "7" * 64,
        },
    ]
    closures = [
        {
            "normalized_distribution_name": name,
            "distribution_version": version,
            "installed_record_closure_sha256": f"{index + 8:x}" * 64,
        }
        for index, (name, version) in enumerate(
            contract.ContractV1.EXPECTED_DISTRIBUTIONS
        )
    ]
    manifest_sha256 = contract.canonical_sha256(rows)
    closure_sha256 = contract.canonical_sha256(closures)
    runtime_identity_exact19 = {
        "logical_runtime_id": "d" * 64,
        "runtime_content_identity": "e" * 64,
        "runtime_root_identity_sha256": "f" * 64,
        "runtime_instance_observation_id": "1" * 64,
        "materialization_event_id": "0" * 64,
        "formal_lock_logical_sha256": contract.ContractV1.LOCK_LOGICAL_SHA256,
        "runner_projection_sha256": contract.ContractV1.PROJECTION_SHA256,
        "accepted_wheel_manifest_sha256": contract.ContractV1.WHEEL_MANIFEST_SHA256,
        "distribution_closure_sha256": closure_sha256,
        "installed_file_manifest_sha256": manifest_sha256,
        "full_runtime_root_manifest_sha256": "2" * 64,
        "entrypoint_control_identity_sha256": "3" * 64,
        "resolved_interpreter_executable_sha256": (
            contract.ContractV1.EXPECTED_INTERPRETER_SHA256
        ),
        "environment_policy_sha256": contract.ContractV1.ENVIRONMENT_POLICY_SHA256,
        "required_role_path_ordered_sha256": (
            contract.ContractV1.REQUIRED_ROLE_PATH_ORDERED_SHA256
        ),
        "admitted_executable_relative_path": (
            contract.ContractV1.EXPECTED_EXECUTABLE_RELATIVE
        ),
        "distribution_count": 5,
        "record_closure_match_count": 5,
        "unexpected_entry_count": 0,
    }
    canonical_diagnostic = {
        "canonical_row_count": len(rows),
        "canonical_preimage_bytes": len(contract.canonical_json_bytes(rows)),
        "canonical_preimage_lf": 0,
        "site_regular_file_count": len(rows) + 5,
        "site_directory_count": 7,
        "site_symlink_count": 0,
        "site_other_count": 0,
        "eligible_regular_payload_count": len(rows),
        "owned_file_count": len(rows),
        "unowned_file_count": 0,
        "duplicate_relative_path_count": 0,
        "missing_file_count": 0,
        "extra_file_count": 0,
        "pyc_file_count": 0,
        "pycache_directory_count": 0,
        "record_self_excluded_count": 5,
        "verified_external_entrypoint_count": 3,
        "external_entrypoint_pathset_sha256": "4" * 64,
        "canonical_pathset_sha256": "5" * 64,
        "mismatch_row_sha256": contract.canonical_sha256([]),
        "mismatch_row_count": 0,
        "nonzero_mismatch_family_count": 0,
    }
    return {
        "schema_version": contract.ContractV1.ROLE_RESULT_SCHEMA,
        "role": role,
        "status": "VALID",
        "process_id": process_id,
        "strategy": {
            "owner": "DISTRIBUTION_FIRST_RECORD_CLAIM_CONSTRUCTION",
            "independent": "FILESYSTEM_FIRST_REVERSE_OWNERSHIP_RECONCILIATION",
        }[role],
        "runtime_identity_exact19": runtime_identity_exact19,
        "manifest_sha256": manifest_sha256,
        "manifest_rows": rows,
        "distribution_closures": closures,
        "canonical_diagnostic": canonical_diagnostic,
    }


def _admit_synthetic_role_contract(
    monkeypatch: pytest.MonkeyPatch, result: dict[str, Any]
) -> None:
    diagnostic = result["canonical_diagnostic"]
    monkeypatch.setattr(
        contract.ContractV1,
        "EXPECTED_MANIFEST_ROW_COUNT",
        len(result["manifest_rows"]),
    )
    monkeypatch.setattr(
        contract.ContractV1,
        "EXPECTED_CANONICAL_PREIMAGE_BYTES",
        diagnostic["canonical_preimage_bytes"],
    )
    monkeypatch.setattr(
        contract.ContractV1,
        "EXPECTED_SITE_REGULAR_FILE_COUNT",
        diagnostic["site_regular_file_count"],
    )
    monkeypatch.setattr(
        contract.ContractV1,
        "EXPECTED_SITE_DIRECTORY_COUNT",
        diagnostic["site_directory_count"],
    )
    monkeypatch.setattr(
        contract.ContractV1,
        "EXPECTED_EXTERNAL_ENTRYPOINT_COUNT",
        diagnostic["verified_external_entrypoint_count"],
    )
    monkeypatch.setattr(
        contract.ContractV1,
        "EXPECTED_EXTERNAL_ENTRYPOINT_PATHSET_SHA256",
        diagnostic["external_entrypoint_pathset_sha256"],
    )
    monkeypatch.setattr(
        contract.ContractV1,
        "EXPECTED_CANONICAL_PATHSET_SHA256",
        diagnostic["canonical_pathset_sha256"],
    )
    monkeypatch.setattr(
        contract.ContractV1,
        "EXPECTED_EMPTY_MISMATCH_ROW_SHA256",
        diagnostic["mismatch_row_sha256"],
    )
    monkeypatch.setattr(
        contract.ContractV1,
        "INSTALLED_MANIFEST_COMPARATOR_SHA256",
        result["manifest_sha256"],
    )
    monkeypatch.setattr(
        contract.ContractV1,
        "EXPECTED_RECORD_CLOSURES",
        tuple(
            (
                item["normalized_distribution_name"],
                item["distribution_version"],
                item["installed_record_closure_sha256"],
            )
            for item in result["distribution_closures"]
        ),
    )
    distribution_closure_sha256 = contract.canonical_sha256(
        result["distribution_closures"]
    )
    monkeypatch.setattr(
        contract.ContractV1,
        "DISTRIBUTION_CLOSURE_SHA256",
        distribution_closure_sha256,
    )
    result["runtime_identity_exact19"][
        "installed_file_manifest_sha256"
    ] = result["manifest_sha256"]
    result["runtime_identity_exact19"][
        "distribution_closure_sha256"
    ] = distribution_closure_sha256


def _assert_violation(code: str, function: Any, *args: Any) -> None:
    with pytest.raises(contract.ContractViolation) as captured:
        function(*args)
    assert captured.value.code == code


def _synthetic_pid(slot: int) -> int:
    return os.getpid() + 100_000 + slot


def _record_digest(payload: bytes) -> str:
    return base64.urlsafe_b64encode(hashlib.sha256(payload).digest()).rstrip(b"=").decode(
        "ascii"
    )


def _write_bytes(path: Path, payload: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(payload)


def _mini_loose_git_repo(tmp_path: Path) -> tuple[Path, str, str, Path]:
    repo = tmp_path / "mini-git-repo"
    git_dir = repo / ".git"
    tracked = repo / "tracked.txt"
    tracked_payload = b"tracked synthetic body\n"
    _write_bytes(tracked, tracked_payload)

    blob_object = (
        f"blob {len(tracked_payload)}\0".encode("ascii") + tracked_payload
    )
    blob_oid = hashlib.sha1(blob_object).digest()
    path_bytes = b"tracked.txt"
    tree_body = b"100644 " + path_bytes + b"\0" + blob_oid
    tree_object = f"tree {len(tree_body)}\0".encode("ascii") + tree_body
    tree_oid = hashlib.sha1(tree_object).hexdigest()
    commit_body = f"tree {tree_oid}\n\nsynthetic commit\n".encode("ascii")
    commit_object = f"commit {len(commit_body)}\0".encode("ascii") + commit_body
    commit_oid = hashlib.sha1(commit_object).hexdigest()

    _write_bytes(git_dir / "HEAD", b"ref: refs/heads/main\n")
    _write_bytes(
        git_dir / "refs" / "heads" / "main",
        f"{commit_oid}\n".encode("ascii"),
    )
    _write_bytes(
        git_dir / "objects" / commit_oid[:2] / commit_oid[2:],
        zlib.compress(commit_object),
    )

    index_entry = (
        struct.pack(
            ">10I",
            0,
            0,
            0,
            0,
            0,
            0,
            0o100644,
            0,
            0,
            len(tracked_payload),
        )
        + blob_oid
        + struct.pack(">H", len(path_bytes))
        + path_bytes
        + b"\0"
    )
    index_entry += b"\0" * ((-len(index_entry)) % 8)
    index_body = b"DIRC" + struct.pack(">II", 2, 1) + index_entry
    _write_bytes(git_dir / "index", index_body + hashlib.sha1(index_body).digest())
    return repo, commit_oid, tree_oid, tracked


def _write_single_commit_pack(
    common_dir: Path, commit_body: bytes, *, object_type: int
) -> str:
    commit_object = f"commit {len(commit_body)}\0".encode("ascii") + commit_body
    commit_oid = hashlib.sha1(commit_object).hexdigest()
    remaining = len(commit_body) >> 4
    first = (object_type << 4) | (len(commit_body) & 0x0F)
    if remaining:
        first |= 0x80
    header = bytearray((first,))
    while remaining:
        current = remaining & 0x7F
        remaining >>= 7
        if remaining:
            current |= 0x80
        header.append(current)
    packed_entry = bytes(header) + zlib.compress(commit_body)
    pack_without_checksum = b"PACK" + struct.pack(">II", 2, 1) + packed_entry
    pack_checksum = hashlib.sha1(pack_without_checksum).digest()

    oid_bytes = bytes.fromhex(commit_oid)
    first_oid_byte = oid_bytes[0]
    fanout = [0 if slot < first_oid_byte else 1 for slot in range(256)]
    index_without_checksum = (
        b"\xfftOc"
        + struct.pack(">I", 2)
        + struct.pack(">256I", *fanout)
        + oid_bytes
        + struct.pack(">I", zlib.crc32(packed_entry) & 0xFFFFFFFF)
        + struct.pack(">I", 12)
        + pack_checksum
    )
    pack_dir = common_dir / "objects" / "pack"
    _write_bytes(
        pack_dir / "pack-synthetic.pack", pack_without_checksum + pack_checksum
    )
    _write_bytes(
        pack_dir / "pack-synthetic.idx",
        index_without_checksum + hashlib.sha1(index_without_checksum).digest(),
    )
    return commit_oid


def _snapshot_tree(root: Path) -> list[dict[str, Any]]:
    root_stat = root.lstat()
    rows: list[dict[str, Any]] = [
        {
            "kind": "root",
            "mode": stat.S_IMODE(root_stat.st_mode),
            "mtime_ns": root_stat.st_mtime_ns,
            "relative_path": ".",
        }
    ]
    for directory, names, files in os.walk(root, topdown=True, followlinks=False):
        names.sort()
        files.sort()
        directory_path = Path(directory)
        for name in names + files:
            path = directory_path / name
            observed = path.lstat()
            relative = path.relative_to(root).as_posix()
            if stat.S_ISREG(observed.st_mode):
                rows.append(
                    {
                        "kind": "regular",
                        "mode": stat.S_IMODE(observed.st_mode),
                        "mtime_ns": observed.st_mtime_ns,
                        "relative_path": relative,
                        "raw_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
                    }
                )
            elif stat.S_ISDIR(observed.st_mode):
                rows.append(
                    {
                        "kind": "directory",
                        "mode": stat.S_IMODE(observed.st_mode),
                        "mtime_ns": observed.st_mtime_ns,
                        "relative_path": relative,
                    }
                )
            elif stat.S_ISLNK(observed.st_mode):
                rows.append(
                    {
                        "kind": "symlink",
                        "mtime_ns": observed.st_mtime_ns,
                        "relative_path": relative,
                        "target": os.readlink(path),
                    }
                )
            else:
                rows.append(
                    {
                        "kind": "other",
                        "mtime_ns": observed.st_mtime_ns,
                        "relative_path": relative,
                    }
                )
    return rows


def _mini_runtime(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> tuple[dict[str, Any], Path, Path, Path]:
    root = tmp_path / "fresh-runtime"
    site = root / "lib" / "python3.12" / "site-packages"
    executable = root / "bin" / "python"
    probe_cwd = tmp_path / "empty-probe-cwd"
    site.mkdir(parents=True)
    executable.parent.mkdir(parents=True)
    probe_cwd.mkdir()
    executable_payload = b"synthetic interpreter identity\n"
    executable.write_bytes(executable_payload)
    executable.chmod(0o755)

    manifest_rows: list[dict[str, Any]] = []
    expected_record_closures: list[tuple[str, str, str]] = []
    output_closures: list[dict[str, str]] = []
    tamper_payload: Path | None = None
    console_script_slots = {0: "iniconfig-mini", 1: "packaging-mini", 2: "pluggy-mini"}

    for slot, (name, version) in enumerate(contract.ContractV1.EXPECTED_DISTRIBUTIONS):
        dist_info = site / f"{name.replace('-', '_')}-{version}.dist-info"
        payload_path = site / name / "payload.py"
        metadata_path = dist_info / "METADATA"
        record_path = dist_info / "RECORD"
        payload = f"VALUE = {slot!r}\n".encode("utf-8")
        metadata = (
            f"Metadata-Version: 2.1\nName: {name}\nVersion: {version}\n"
        ).encode("utf-8")
        _write_bytes(payload_path, payload)
        _write_bytes(metadata_path, metadata)
        if tamper_payload is None:
            tamper_payload = payload_path

        claimed_paths: list[tuple[str, Path]] = [
            (payload_path.relative_to(site).as_posix(), payload_path),
            (metadata_path.relative_to(site).as_posix(), metadata_path),
        ]
        script_name = console_script_slots.get(slot)
        if script_name is not None:
            entry_points_path = dist_info / "entry_points.txt"
            entry_points = (
                f"[console_scripts]\n{script_name} = {name}.payload:VALUE\n"
            ).encode("utf-8")
            script_path = root / "bin" / script_name
            script_payload = f"#!synthetic\n# {script_name}\n".encode("utf-8")
            _write_bytes(entry_points_path, entry_points)
            _write_bytes(script_path, script_payload)
            script_path.chmod(0o755)
            claimed_paths.append(
                (entry_points_path.relative_to(site).as_posix(), entry_points_path)
            )
            claimed_paths.append((f"../../../bin/{script_name}", script_path))

        record_rows: list[list[str]] = []
        for raw_path, physical_path in claimed_paths:
            body = physical_path.read_bytes()
            record_rows.append(
                [raw_path, f"sha256={_record_digest(body)}", str(len(body))]
            )
        record_relative = record_path.relative_to(site).as_posix()
        record_rows.append([record_relative, "", ""])
        stream = io.StringIO(newline="")
        writer = csv.writer(stream, lineterminator="\n")
        writer.writerows(record_rows)
        _write_bytes(record_path, stream.getvalue().encode("utf-8"))

        closure_entries: list[dict[str, Any]] = []
        for raw_path, physical_path in claimed_paths + [(record_relative, record_path)]:
            # The V1 closure contains only site payload.  RECORD self and the
            # separately verified external console-script controls are excluded.
            if physical_path == record_path or not physical_path.is_relative_to(site):
                continue
            body = physical_path.read_bytes()
            closure_entries.append(
                {
                    "path": physical_path.relative_to(site).as_posix(),
                    "sha256": hashlib.sha256(body).hexdigest(),
                    "size": len(body),
                }
            )
            manifest_rows.append(
                {
                    "normalized_distribution_name": name,
                    "relative_path": physical_path.relative_to(site).as_posix(),
                    "byte_count": len(body),
                    "raw_sha256": hashlib.sha256(body).hexdigest(),
                }
            )
        closure_entries.sort(key=lambda item: item["path"])
        closure_sha256 = contract.canonical_sha256(
            {"record_entries": closure_entries}
        )
        expected_record_closures.append((name, version, closure_sha256))
        output_closures.append(
            {
                "normalized_distribution_name": name,
                "distribution_version": version,
                "installed_record_closure_sha256": closure_sha256,
            }
        )

    rank = {
        name: index
        for index, (name, _version) in enumerate(
            contract.ContractV1.EXPECTED_DISTRIBUTIONS
        )
    }
    manifest_rows.sort(
        key=lambda item: (
            rank[item["normalized_distribution_name"]],
            item["relative_path"],
        )
    )
    monkeypatch.setattr(
        contract.ContractV1,
        "EXPECTED_INTERPRETER_SHA256",
        hashlib.sha256(executable_payload).hexdigest(),
    )
    monkeypatch.setattr(
        contract.ContractV1, "EXPECTED_MANIFEST_ROW_COUNT", len(manifest_rows)
    )
    monkeypatch.setattr(
        contract.ContractV1,
        "EXPECTED_RECORD_CLOSURES",
        tuple(expected_record_closures),
    )
    monkeypatch.setattr(
        contract.ContractV1,
        "INSTALLED_MANIFEST_COMPARATOR_SHA256",
        contract.canonical_sha256(manifest_rows),
    )
    monkeypatch.setattr(
        contract.ContractV1,
        "DISTRIBUTION_CLOSURE_SHA256",
        contract.canonical_sha256(output_closures),
    )
    external_entrypoint_paths = sorted(
        f"bin/{script_name}" for script_name in console_script_slots.values()
    )
    monkeypatch.setattr(
        contract.ContractV1,
        "EXPECTED_CANONICAL_PREIMAGE_BYTES",
        len(contract.canonical_json_bytes(manifest_rows)),
    )
    monkeypatch.setattr(
        contract.ContractV1,
        "EXPECTED_SITE_REGULAR_FILE_COUNT",
        len(manifest_rows) + len(contract.ContractV1.EXPECTED_DISTRIBUTIONS),
    )
    monkeypatch.setattr(
        contract.ContractV1,
        "EXPECTED_SITE_DIRECTORY_COUNT",
        len(contract.ContractV1.EXPECTED_DISTRIBUTIONS) * 2,
    )
    monkeypatch.setattr(
        contract.ContractV1,
        "EXPECTED_EXTERNAL_ENTRYPOINT_COUNT",
        len(external_entrypoint_paths),
    )
    monkeypatch.setattr(
        contract.ContractV1,
        "EXPECTED_EXTERNAL_ENTRYPOINT_PATHSET_SHA256",
        contract.canonical_sha256(
            sorted(
                hashlib.sha256(path.encode("utf-8")).hexdigest()
                for path in external_entrypoint_paths
            )
        ),
    )
    monkeypatch.setattr(
        contract.ContractV1,
        "EXPECTED_CANONICAL_PATHSET_SHA256",
        contract.canonical_sha256(
            sorted(row["relative_path"] for row in manifest_rows)
        ),
    )
    monkeypatch.setattr(
        contract.ContractV1,
        "EXPECTED_EMPTY_MISMATCH_ROW_SHA256",
        contract.canonical_sha256([]),
    )
    request = _valid_request()
    request["materialization"]["root"] = root.as_posix()
    request["materialization"]["expected_full_root_manifest_sha256"] = (
        checker._full_root_manifest(root.as_posix())
    )
    request["materialization"]["probe_cwd"] = probe_cwd.as_posix()
    request["runtime"]["executable"] = executable.as_posix()
    request["runtime"]["resolved_interpreter_sha256"] = (
        contract.ContractV1.EXPECTED_INTERPRETER_SHA256
    )
    request["frozen"]["distribution_closure_sha256"] = (
        contract.ContractV1.DISTRIBUTION_CLOSURE_SHA256
    )
    request["frozen"]["installed_manifest_comparator_sha256"] = (
        contract.ContractV1.INSTALLED_MANIFEST_COMPARATOR_SHA256
    )
    _refresh_materialization_attestation(request)

    def owner_runtime_observation(
        observed_request: dict[str, Any], observed_executable: str
    ) -> dict[str, str]:
        assert observed_request["runtime"]["executable"] == observed_executable
        return {
            "implementation": contract.ContractV1.EXPECTED_IMPLEMENTATION,
            "python_version": contract.ContractV1.EXPECTED_PYTHON_VERSION,
            "platform_tag": contract.ContractV1.EXPECTED_PLATFORM_TAG,
            "executable": observed_executable,
        }

    def independent_runtime_observation(
        observed_request: dict[str, Any], observed_executable: str
    ) -> dict[str, str]:
        assert observed_request["runtime"]["executable"] == observed_executable
        return {
            "implementation": contract.ContractV1.EXPECTED_IMPLEMENTATION,
            "python_version": contract.ContractV1.EXPECTED_PYTHON_VERSION,
            "platform_tag": contract.ContractV1.EXPECTED_PLATFORM_TAG,
            "executable": observed_executable,
        }

    monkeypatch.setattr(
        owner, "_observe_owner_runtime_properties", owner_runtime_observation
    )
    monkeypatch.setattr(
        independent,
        "_observe_independent_runtime_properties",
        independent_runtime_observation,
    )
    monkeypatch.setattr(
        checker,
        "_actual_git_head_tree",
        lambda _repo_root: (
            request["frozen"]["mashos_api_commit"],
            request["frozen"]["mashos_api_tree"],
        ),
    )
    monkeypatch.setattr(checker, "_assert_official_cli_context", lambda: None)
    assert tamper_payload is not None
    return request, root, site, tamper_payload


def _install_fake_popen(
    monkeypatch: pytest.MonkeyPatch,
    owner_result: dict[str, Any],
    independent_result: dict[str, Any],
    calls: list[dict[str, Any]],
    *,
    process_ids: list[int] | None = None,
) -> Any:
    responses = [
        SimpleNamespace(
            returncode=0,
            stdout=contract.canonical_json_bytes(owner_result),
            stderr=b"",
        ),
        SimpleNamespace(returncode=0, stdout=b"pytest 8.4.1\n", stderr=b""),
        SimpleNamespace(
            returncode=0,
            stdout=contract.canonical_json_bytes(
                {
                    "direct_role_load_count": 3,
                    "public_api_call_count": 0,
                    "effect_count": 0,
                }
            ),
            stderr=b"",
        ),
        SimpleNamespace(
            returncode=0,
            stdout=contract.canonical_json_bytes(independent_result),
            stderr=b"",
        ),
    ]
    pids = list(
        process_ids
        or (
            owner_result["process_id"],
            owner_result["process_id"] + 1,
            owner_result["process_id"] + 2,
            independent_result["process_id"],
        )
    )
    if len(pids) != 4:
        raise AssertionError("fake process ledger must contain exact4 PIDs")

    class FakePopen:
        def __init__(
            self,
            process_id: int,
            response: SimpleNamespace,
            call: dict[str, Any],
        ) -> None:
            self.pid = process_id
            self.returncode = response.returncode
            self._response = response
            self._call = call
            self.killed = False

        def communicate(
            self, input: bytes | None = None, timeout: int | None = None
        ) -> tuple[bytes, bytes]:
            self._call["input"] = input
            self._call["timeout"] = timeout
            return self._response.stdout, self._response.stderr

        def kill(self) -> None:
            self.killed = True

    def popen_factory(argv: list[str], **kwargs: Any) -> FakePopen:
        if not responses or not pids:
            raise AssertionError("unexpected retry or additional process")
        process_id = pids.pop(0)
        call = {"argv": list(argv), "process_id": process_id, **kwargs}
        calls.append(call)
        return FakePopen(process_id, responses.pop(0), call)

    popen_factory.responses = responses  # type: ignore[attr-defined]
    popen_factory.pids = pids  # type: ignore[attr-defined]
    monkeypatch.setattr(checker, "_popen_factory", popen_factory)
    return popen_factory


def _official_orchestrate(request: dict[str, Any]) -> dict[str, Any]:
    return checker._orchestrate_cli(request, checker._CLI_ADMISSION_TOKEN)


def _expected_handoff_binding(
    request: dict[str, Any],
    owner_result: dict[str, Any],
    public_result: dict[str, Any],
) -> str:
    identity = owner_result["runtime_identity_exact19"]
    return contract.canonical_sha256(
        {
            "schema_version": contract.ContractV1.HANDOFF_SCHEMA,
            "handoff_claim": contract.ContractV1.HANDOFF_CLAIM,
            "private_locator_holder": "CALLER_REQUEST_CONTEXT",
            "consumer_observed": False,
            "observation_session_id": request["observation_session_id"],
            "receiver_session_id": request["handoff"]["receiver_session_id"],
            "receiver_nonce": request["handoff"]["receiver_nonce"],
            "mashos_api_commit": request["frozen"]["mashos_api_commit"],
            "mashos_api_tree": request["frozen"]["mashos_api_tree"],
            "freshness_evidence_class": contract.ContractV1.FRESHNESS_EVIDENCE_CLASS,
            "freshness_claim_limit": contract.ContractV1.FRESHNESS_CLAIM_LIMIT,
            "materialization_event_id": request["materialization"]["event_id"],
            "runtime_root_locator_sha256": contract.runtime_root_locator_sha256(
                request["materialization"]["root"]
            ),
            "runtime_executable_locator_sha256": (
                contract.runtime_executable_locator_sha256(
                    request["runtime"]["executable"]
                )
            ),
            "expected_full_root_manifest_sha256": request["materialization"][
                "expected_full_root_manifest_sha256"
            ],
            "runtime_instance_observation_id": identity[
                "runtime_instance_observation_id"
            ],
            "runtime_readiness_observation_id": public_result[
                "runtime_readiness_observation_id"
            ],
            "entrypoint_control_identity_sha256": identity[
                "entrypoint_control_identity_sha256"
            ],
        }
    )


def _assert_body_free_public_result(result: dict[str, Any], request: dict[str, Any]) -> None:
    serialized = contract.canonical_json_bytes(result).decode("utf-8")
    private_values = (
        request["authority_id"],
        request["observation_session_id"],
        request["materialization"]["event_id"],
        request["materialization"]["root"],
        request["materialization"]["root_locator_sha256"],
        request["materialization"]["expected_full_root_manifest_sha256"],
        request["materialization"]["probe_cwd"],
        request["runtime"]["executable"],
        request["frozen"]["mashos_api_commit"],
        request["frozen"]["mashos_api_tree"],
        request["handoff"]["receiver_session_id"],
        request["handoff"]["receiver_nonce"],
    )
    assert not any(value in serialized for value in private_values)
    forbidden_keys = {
        "absolute_path",
        "manifest_rows",
        "private_handoff",
        "raw_output",
        "receiver_nonce",
        "runtime_root",
    }

    def walk(value: Any) -> None:
        if isinstance(value, dict):
            assert not (set(value) & forbidden_keys)
            for item in value.values():
                walk(item)
        elif isinstance(value, list):
            for item in value:
                walk(item)

    walk(result)


def test_canonical_json_is_compact_utf8_and_preserves_manifest_row_order() -> None:
    rows = [
        {"name": "zeta", "version": "1"},
        {"name": "alpha", "version": "2"},
        {"name": "華恋", "version": "3"},
        {"name": "omega", "version": "4"},
    ]
    value = {"z": "環境", "manifest_rows": rows, "a": 1}

    encoded = contract.canonical_json_bytes(value)

    assert encoded == (
        '{"a":1,"manifest_rows":['
        '{"name":"zeta","version":"1"},'
        '{"name":"alpha","version":"2"},'
        '{"name":"華恋","version":"3"},'
        '{"name":"omega","version":"4"}],'
        '"z":"環境"}'
    ).encode("utf-8")
    assert contract.canonical_sha256(value) == hashlib.sha256(encoded).hexdigest()


def test_v1_check_order_is_closed_exact9() -> None:
    assert tuple(contract.ContractV1.CHECK_ORDER) == (
        "INPUT_SCHEMA_AND_HEAD_BINDING",
        "FRESH_MATERIALIZATION_EVIDENCE",
        "PRE_ROOT_AND_FROZEN_IDENTITIES",
        "OWNER_DERIVATION",
        "PYTEST_VERSION_PROBE",
        "REQUIRED_ROLE_SMOKE",
        "INDEPENDENT_DERIVATION",
        "RECONCILIATION_AND_POST_ROOT",
        "SAME_INSTANCE_HANDOFF_BINDING",
    )


def test_v1_runtime_and_frozen_inputs_are_exact() -> None:
    assert contract.ContractV1.OFFICIAL_ADMISSION_MODULE == (
        "ai.tools.emlis_nls_v3_s11_g4b_runtime_admission_checker_v1"
    )
    assert contract.ContractV1.OFFICIAL_ADMISSION_ENTRYPOINT == (
        "ai.tools.emlis_nls_v3_s11_g4b_runtime_admission_checker_v1:main"
    )
    assert contract.ContractV1.OFFICIAL_PYTHON_FLAGS == (
        "-E",
        "-s",
        "-S",
        "-B",
        "-m",
    )
    assert contract.ContractV1.LIBRARY_INVOCATION_CREDIT is False
    assert contract.ContractV1.MATERIALIZATION_ATTESTATION_SCHEMA == (
        "emlis.nls_v3.s11.g4b.runtime_materialization.external_attestation.v1"
    )
    assert contract.ContractV1.ROOT_LOCATOR_SCHEMA == (
        "emlis.nls_v3.s11.g4b.runtime_root_locator.v1"
    )
    assert contract.ContractV1.EXECUTABLE_LOCATOR_SCHEMA == (
        "emlis.nls_v3.s11.g4b.runtime_executable_locator.v1"
    )
    assert contract.ContractV1.HANDOFF_CLAIM == (
        "CURRENT_SESSION_BINDING_ONLY_CONSUMER_NOT_OBSERVED_V1"
    )
    assert contract.ContractV1.EXPECTED_IMPLEMENTATION == "CPython"
    assert contract.ContractV1.EXPECTED_PYTHON_VERSION == "3.12.13"
    assert contract.ContractV1.EXPECTED_PLATFORM_TAG == "linux-x86_64"
    assert contract.ContractV1.EXPECTED_EXECUTABLE_RELATIVE == "bin/python"
    assert contract.ContractV1.EXPECTED_SITE_PACKAGES_RELATIVE == (
        "lib/python3.12/site-packages"
    )
    assert contract.ContractV1.EXPECTED_INTERPRETER_SHA256 == (
        "9ed008e5a8685235361f0c53771b520ab082dd99a877ad2fd796a93fa4c0b488"
    )
    assert contract.ContractV1.EXPECTED_DISTRIBUTIONS == (
        ("iniconfig", "2.3.0"),
        ("packaging", "26.2"),
        ("pluggy", "1.6.0"),
        ("pygments", "2.20.0"),
        ("pytest", "8.4.1"),
    )
    assert contract.ContractV1.EXPECTED_MANIFEST_ROW_COUNT == 482
    assert contract.ContractV1.EXPECTED_CANONICAL_PREIMAGE_BYTES == 89_653
    assert contract.ContractV1.EXPECTED_SITE_REGULAR_FILE_COUNT == 487
    assert contract.ContractV1.EXPECTED_SITE_DIRECTORY_COUNT == 27
    assert contract.ContractV1.EXPECTED_EXTERNAL_ENTRYPOINT_COUNT == 3
    assert contract.ContractV1.EXPECTED_EXTERNAL_ENTRYPOINT_PATHSET_SHA256 == (
        "e68059e3cc382b66728dfa6fe0a2b0bad4685d105e12f037fd09649e0f4b9b61"
    )
    assert contract.ContractV1.EXPECTED_CANONICAL_PATHSET_SHA256 == (
        "6fb972b20c2c5c776886c53c905bf08e8577fa74284d760c39065b9ba65328f2"
    )
    assert contract.ContractV1.EXPECTED_EMPTY_MISMATCH_ROW_SHA256 == (
        "4f53cda18c2baa0c0354bb5f9a3ecbe5ed12ab4d8e11ba873c2f11161202b945"
    )
    assert contract.ContractV1.EXPECTED_RECORD_CLOSURES == (
        (
            "iniconfig",
            "2.3.0",
            "390ff70b72d7d6be5bf03dae9ff546d6a13584704d3078ce0000eded74092e05",
        ),
        (
            "packaging",
            "26.2",
            "851cdb430628cce99eb887f87405c6c2bfb24e642a972cdf843267018c82c3a1",
        ),
        (
            "pluggy",
            "1.6.0",
            "b072098f6cace7afdf1d4759f13b91f805836743a0af3c4f38f40343c60ee942",
        ),
        (
            "pygments",
            "2.20.0",
            "ce2debc2a42c4274ea75b03e9c0f4dc5bd01c6f25e86da4fac5d76296e3b1a05",
        ),
        (
            "pytest",
            "8.4.1",
            "5cefca6d1f84bef673818f562c6b63b100d32b51dc26405c5bed8cbd91b11874",
        ),
    )
    assert len(contract.ContractV1.RUNTIME_IDENTITY_EXACT19_KEYS) == 19
    assert len(contract.ContractV1.READINESS_PREIMAGE_FIELDS) == 40
    assert contract.ContractV1.EXPECTED_PROCEDURE_IDS == (
        "COCOLON_RULE13_RUNTIME_CONTINUITY_V20260811",
        "COCOLON_RULE16_ONE_SHOT_PRELAUNCH_V20260811",
    )
    assert contract.ContractV1.ENVIRONMENT_POLICY_SHA256 == (
        "8a43751b49a8db1d024063608405f9b169e829f3c0be3488433b31800d44b1a4"
    )
    assert contract.ContractV1.REQUIRED_ROLE_PATH_ORDERED_SHA256 == (
        "e01f5e587ba1884b988075eee1c162454d3a6a1d4b10febc3b7111c2b5c1b248"
    )
    assert contract.ContractV1.REQUIRED_ROLE_SOURCES == (
        (
            "OWNER",
            "ai/services/ai_inference/"
            "emlis_ai_recovery_epoch002_sequence_ledger_v3.py",
            "13aa675be1356ab524a69066f861c2d27a8d8e32f0d690811b2b3308f199057d",
            "validate_recovery_epoch004_sequence_event1_contract_state_v2",
        ),
        (
            "INDEPENDENT",
            "ai/tools/"
            "emlis_nls_v3_recovery_epoch002_closure_receipt_verify.py",
            "634ddb104e0b7630c695e032bb54726912fcfc9ad4351ab0eb6da7901671fc2b",
            "verify_recovery_epoch004_sequence_event1_contract_state_v2",
        ),
        (
            "PARENT",
            "ai/tools/"
            "emlis_nls_v3_recovery_epoch002_formal_parent_orchestrator_v3.py",
            "14fedde39823d90253a6adec6fc05ccde29f05a659edbac7edc007b28eab5793",
            "validate_recovery_epoch004_parent_phase3_event1_evidence_state_v2",
        ),
    )
    assert contract.ContractV1.REQUIRED_ROLE_BLOB_SHA1S == (
        ("OWNER", "044287009b1fd155689bded46628b8fc91b73c06"),
        ("INDEPENDENT", "0fae71a29f8fe44d31c18af42aaf53cc34beac6c"),
        ("PARENT", "fdea3dc18d81ca9ce1e3a842e802d21d0019a8c5"),
    )
    assert contract.ContractV1.LOCK_RAW_SHA256 == (
        "9bb2875541a6d959c1dca47cb5b96de5b0041ccf5288e849c469c15a8b310787"
    )
    assert contract.ContractV1.LOCK_SOURCE_RELATIVE == (
        "ai/configs/"
        "emlis_nls_v3_recovery_epoch002_formal_worker_bootstrap_lock_v1.json"
    )
    assert contract.ContractV1.LOCK_LOGICAL_SHA256 == (
        "801ba54efc0f6655238d14e7c153fb70b555801489aa8ba028515fc64d9c05f4"
    )
    assert contract.ContractV1.PROJECTION_SHA256 == (
        "f501025c1dccef68c47c0a3e52f3ef74d01233f371b16f2b1a0bdfb21089e57e"
    )
    assert contract.ContractV1.REQUIREMENTS_SHA256 == (
        "4f7218509a20e42850afe75597f2abfdf447035001847621d4637faa246065f1"
    )
    assert contract.ContractV1.WHEEL_MANIFEST_SHA256 == (
        "00d2df98c8cda7f1473794892bafe7ccd18cc816c79ccb346f3e21ff629b136d"
    )
    assert contract.ContractV1.DISTRIBUTION_CLOSURE_SHA256 == (
        "4d3d6afdac2b9a606d4797ff5fbe65010faddf0de9788202798ddb8d95e6556c"
    )
    assert contract.ContractV1.INSTALLED_MANIFEST_COMPARATOR_SHA256 == (
        "0eba095e4c173b4b69f68532fd66cf2c871ab9edef64d91754b52ed7daee15c5"
    )


def test_request_schema_accepts_only_exact_v1_shape() -> None:
    value = _valid_request()
    assert contract.validate_request(value) is value

    unknown = _json_clone(value)
    unknown["future"] = "not-v1"
    _assert_violation("INPUT_SCHEMA_INVALID", contract.validate_request, unknown)

    missing = _json_clone(value)
    del missing["authority_id"]
    _assert_violation("INPUT_SCHEMA_INVALID", contract.validate_request, missing)

    nested_unknown = _json_clone(value)
    nested_unknown["runtime"]["fallback_executable"] = "/usr/bin/python3"
    _assert_violation(
        "INPUT_SCHEMA_INVALID", contract.validate_request, nested_unknown
    )

    future_version = _json_clone(value)
    future_version["schema_version"] = "emlis.nls_v3.s11.g4b.runtime_admission.request.v2"
    _assert_violation(
        "SCHEMA_OR_VERSION_INVALID", contract.validate_request, future_version
    )


def test_runtime_root_and_probe_cwd_must_be_disjoint() -> None:
    probe_inside_root = _valid_request()
    probe_inside_root["materialization"]["probe_cwd"] = (
        "/private/fresh-runtime/empty-probe-cwd"
    )
    _assert_violation(
        "INPUT_SCHEMA_INVALID", contract.validate_request, probe_inside_root
    )

    root_inside_probe = _valid_request()
    root_inside_probe["materialization"]["probe_cwd"] = "/private"
    _assert_violation(
        "INPUT_SCHEMA_INVALID", contract.validate_request, root_inside_probe
    )


def test_repo_runtime_and_probe_roots_are_pairwise_disjoint(
    tmp_path: Path,
) -> None:
    repo = tmp_path / "repo"
    runtime = tmp_path / "runtime"
    probe = tmp_path / "probe"
    for path in (repo, runtime, probe):
        path.mkdir()
    assert (
        checker._assert_disjoint_private_roots(
            repo.as_posix(), runtime.as_posix(), probe.as_posix()
        )
        is None
    )

    for overlapping_runtime, overlapping_probe in (
        (repo / "runtime", probe),
        (runtime, repo / "probe"),
        (runtime, runtime / "probe"),
        (probe / "runtime", probe),
    ):
        _assert_violation(
            "INPUT_SCHEMA_INVALID",
            checker._assert_disjoint_private_roots,
            repo.as_posix(),
            overlapping_runtime.as_posix(),
            overlapping_probe.as_posix(),
        )


@pytest.mark.parametrize(
    "mismatch", ("flags", "spec", "module_name", "cwd")
)
def test_official_cli_context_requires_exact_flags_module_and_cwd(
    monkeypatch: pytest.MonkeyPatch, mismatch: str
) -> None:
    flag_values = {
        "ignore_environment": 1,
        "no_user_site": 1,
        "no_site": 1,
        "dont_write_bytecode": 1,
    }
    spec_name = contract.ContractV1.OFFICIAL_ADMISSION_MODULE
    module_name = "__main__"
    cwd = "/private/canonical-repository"
    if mismatch == "flags":
        flag_values["no_site"] = 0
    elif mismatch == "spec":
        spec_name += ".wrong"
    elif mismatch == "module_name":
        module_name = contract.ContractV1.OFFICIAL_ADMISSION_MODULE
    else:
        cwd += "-wrong"

    monkeypatch.setattr(
        checker, "sys", SimpleNamespace(flags=SimpleNamespace(**flag_values))
    )
    monkeypatch.setattr(checker, "__spec__", SimpleNamespace(name=spec_name))
    monkeypatch.setattr(checker, "__name__", module_name)
    monkeypatch.setattr(checker, "os", SimpleNamespace(getcwd=lambda: cwd))
    monkeypatch.setattr(
        checker, "_repo_root", lambda: "/private/canonical-repository"
    )

    _assert_violation(
        "CURRENT_AUTHORITY_STOP", checker._assert_official_cli_context
    )


def test_official_cli_context_accepts_only_the_exact_startup_shape(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    flags = SimpleNamespace(
        ignore_environment=1,
        no_user_site=1,
        no_site=1,
        dont_write_bytecode=1,
    )
    repo_root = "/private/canonical-repository"
    monkeypatch.setattr(checker, "sys", SimpleNamespace(flags=flags))
    monkeypatch.setattr(
        checker,
        "__spec__",
        SimpleNamespace(name=contract.ContractV1.OFFICIAL_ADMISSION_MODULE),
    )
    monkeypatch.setattr(checker, "__name__", "__main__")
    monkeypatch.setattr(checker, "os", SimpleNamespace(getcwd=lambda: repo_root))
    monkeypatch.setattr(checker, "_repo_root", lambda: repo_root)

    assert checker._assert_official_cli_context() is None


@pytest.mark.parametrize(
    "control_name", (".git", "pytest.ini", "pyproject.toml", "tox.ini", "setup.cfg")
)
def test_probe_cwd_rejects_repository_or_test_config_in_any_ancestor(
    tmp_path: Path, control_name: str
) -> None:
    controlled_parent = tmp_path / "controlled-parent"
    probe_cwd = controlled_parent / "empty-probe-cwd"
    probe_cwd.mkdir(parents=True)
    control = controlled_parent / control_name
    if control_name == ".git":
        control.mkdir()
    else:
        _write_bytes(control, b"[synthetic-control]\n")

    _assert_violation(
        "PROBE_OR_SMOKE_INVALID",
        checker._assert_probe_ancestors_config_free,
        probe_cwd.as_posix(),
    )


def test_actual_git_head_tree_is_read_only_bound_and_fails_closed(
    tmp_path: Path,
) -> None:
    repo, expected_commit, expected_tree, tracked = _mini_loose_git_repo(tmp_path)
    before = _snapshot_tree(repo)

    assert checker._actual_git_head_tree(repo.as_posix()) == (
        expected_commit,
        expected_tree,
    )
    assert _snapshot_tree(repo) == before

    tracked.write_bytes(b"tracked content drift\n")
    _assert_violation(
        "BASE_OR_PREIMAGE_DRIFT",
        checker._actual_git_head_tree,
        repo.as_posix(),
    )

    no_git = tmp_path / "not-a-repository"
    no_git.mkdir()
    _assert_violation(
        "BASE_OR_PREIMAGE_DRIFT",
        checker._actual_git_head_tree,
        no_git.as_posix(),
    )


def test_packed_direct_commit_is_read_and_delta_commit_fails_closed(
    tmp_path: Path,
) -> None:
    expected_tree = "a" * 40
    commit_body = f"tree {expected_tree}\n\npacked synthetic commit\n".encode(
        "ascii"
    )
    direct_common = tmp_path / "direct-common"
    direct_oid = _write_single_commit_pack(
        direct_common, commit_body, object_type=1
    )
    assert checker._packed_commit_tree(
        direct_common.as_posix(), direct_oid
    ) == expected_tree

    delta_common = tmp_path / "delta-common"
    delta_oid = _write_single_commit_pack(delta_common, commit_body, object_type=6)
    _assert_violation(
        "BASE_OR_PREIMAGE_DRIFT",
        checker._packed_commit_tree,
        delta_common.as_posix(),
        delta_oid,
    )


def test_strict_json_rejects_duplicates_nonfinite_and_invalid_utf8() -> None:
    _assert_violation(
        "INPUT_SCHEMA_INVALID",
        contract.read_strict_json,
        io.BytesIO(b'{"schema_version":"v1","schema_version":"v2"}'),
    )
    _assert_violation(
        "INPUT_SCHEMA_INVALID",
        contract.read_strict_json,
        io.BytesIO(b'{"value":NaN}'),
    )
    _assert_violation(
        "INPUT_SCHEMA_INVALID",
        contract.read_strict_json,
        io.BytesIO(b'{"value":"\xff"}'),
    )

    stream = io.BytesIO()
    contract.write_strict_json({"message": "華恋", "a": 1}, stream)
    assert stream.getvalue() == '{"a":1,"message":"華恋"}'.encode("utf-8")


def test_freshness_reuse_frozen_and_handoff_drift_fail_closed() -> None:
    valid = _valid_request()
    preimage = contract.materialization_attestation_preimage(valid)
    assert contract.ContractV1.FRESHNESS_EVIDENCE_CLASS == (
        "EXTERNAL_RULE13_RULE16_ATTESTATION_ACCEPTED_V1"
    )
    assert contract.ContractV1.FRESHNESS_CLAIM_LIMIT == (
        "CHECKER_DOES_NOT_RECONSTRUCT_PREMATERIALIZATION_NONEXISTENCE"
    )
    assert preimage["schema_version"] == (
        contract.ContractV1.MATERIALIZATION_ATTESTATION_SCHEMA
    )
    assert set(preimage) == {
        "schema_version",
        "authority_id",
        "observation_session_id",
        "procedure_ids",
        "fresh_root_nonexistent_before",
        "prior_artifact_reuse_count",
        "root_locator_sha256",
        "expected_full_root_manifest_sha256",
        "site_packages_relative",
        "admitted_executable_relative_path",
    }
    assert "root" not in preimage
    assert "probe_cwd" not in preimage
    assert contract.materialization_event_id(valid) == valid["materialization"][
        "event_id"
    ]

    not_fresh = _valid_request()
    not_fresh["materialization"]["fresh_root_nonexistent_before"] = False
    _assert_violation("FRESHNESS_UNPROVED", contract.validate_request, not_fresh)

    reused = _valid_request()
    reused["materialization"]["prior_artifact_reuse_count"] = 1
    _assert_violation(
        "PAST_ARTIFACT_REUSE_DETECTED", contract.validate_request, reused
    )

    old_procedure = _valid_request()
    old_procedure["materialization"]["procedure_ids"] = [
        "historical-rule13",
        "historical-rule16",
    ]
    _assert_violation(
        "FRESHNESS_UNPROVED", contract.validate_request, old_procedure
    )

    event_drift = _valid_request()
    event_drift["materialization"]["event_id"] = "f" * 64
    _assert_violation(
        "FRESHNESS_UNPROVED", contract.validate_request, event_drift
    )

    locator_drift = _valid_request()
    locator_drift["materialization"]["root_locator_sha256"] = "e" * 64
    _assert_violation(
        "FRESHNESS_UNPROVED", contract.validate_request, locator_drift
    )

    expected_root_attestation_drift = _valid_request()
    expected_root_attestation_drift["materialization"][
        "expected_full_root_manifest_sha256"
    ] = "d" * 64
    _assert_violation(
        "FRESHNESS_UNPROVED",
        contract.validate_request,
        expected_root_attestation_drift,
    )

    frozen_drift = _valid_request()
    frozen_drift["frozen"]["lock_raw_sha256"] = "e" * 64
    _assert_violation(
        "BASE_OR_PREIMAGE_DRIFT", contract.validate_request, frozen_drift
    )

    session_drift = _valid_request()
    session_drift["handoff"]["receiver_session_id"] = "session-stale-001"
    _assert_violation("HANDOFF_INVALID", contract.validate_request, session_drift)


def test_role_result_schema_and_manifest_tamper_fail_closed(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    owner_result = _valid_role_result("owner", process_id=101)
    _admit_synthetic_role_contract(monkeypatch, owner_result)
    assert contract.validate_role_result(owner_result, "owner") is owner_result

    unknown = _json_clone(owner_result)
    unknown["absolute_runtime_root"] = "/private/fresh-runtime"
    _assert_violation(
        "INPUT_SCHEMA_INVALID", contract.validate_role_result, unknown, "owner"
    )

    future_version = _json_clone(owner_result)
    future_version["schema_version"] = (
        "emlis.nls_v3.s11.g4b.runtime_admission.role_result.v2"
    )
    _assert_violation(
        "SCHEMA_OR_VERSION_INVALID",
        contract.validate_role_result,
        future_version,
        "owner",
    )

    digest_tamper = _json_clone(owner_result)
    digest_tamper["manifest_rows"][0]["byte_count"] += 1
    _assert_violation(
        "OWNER_INVALID", contract.validate_role_result, digest_tamper, "owner"
    )

    order_tamper = _json_clone(owner_result)
    order_tamper["manifest_rows"][0], order_tamper["manifest_rows"][1] = (
        order_tamper["manifest_rows"][1],
        order_tamper["manifest_rows"][0],
    )
    order_tamper["manifest_sha256"] = contract.canonical_sha256(
        order_tamper["manifest_rows"]
    )
    _assert_violation(
        "OWNER_INVALID", contract.validate_role_result, order_tamper, "owner"
    )

    closure_tamper = _json_clone(owner_result)
    closure_tamper["distribution_closures"][0][
        "installed_record_closure_sha256"
    ] = "a" * 64
    _assert_violation(
        "OWNER_INVALID", contract.validate_role_result, closure_tamper, "owner"
    )

    diagnostic_tamper = _json_clone(owner_result)
    diagnostic_tamper["canonical_diagnostic"]["unowned_file_count"] = 1
    _assert_violation(
        "OWNER_INVALID", contract.validate_role_result, diagnostic_tamper, "owner"
    )

    wrong_role = _valid_role_result("owner", process_id=102)
    _assert_violation(
        "INDEPENDENT_INVALID",
        contract.validate_role_result,
        wrong_role,
        "independent",
    )


def test_current_comparator_is_not_satisfied_by_consistent_arbitrary_rows(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    arbitrary = _valid_role_result("owner", process_id=103)
    _admit_synthetic_role_contract(monkeypatch, arbitrary)
    assert contract.validate_role_result(arbitrary, "owner") is arbitrary

    comparator_drift = "a" * 64
    assert comparator_drift != arbitrary["manifest_sha256"]
    monkeypatch.setattr(
        contract.ContractV1,
        "INSTALLED_MANIFEST_COMPARATOR_SHA256",
        comparator_drift,
    )
    arbitrary["runtime_identity_exact19"][
        "installed_file_manifest_sha256"
    ] = comparator_drift
    with pytest.raises(contract.ContractViolation) as captured:
        contract.validate_role_result(arbitrary, "owner")
    assert captured.value.code == "OWNER_INVALID"
    assert captured.value.detail == "current comparator mismatch"


def test_separate_derivations_full_match_and_leave_runtime_unchanged(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    request, root, _site, _tamper_payload = _mini_runtime(tmp_path, monkeypatch)
    before = _snapshot_tree(root)

    owner_result = owner.derive_owner(_json_clone(request))
    independent_result = independent.derive_independent(_json_clone(request))

    assert contract.validate_role_result(owner_result, "owner") is owner_result
    assert (
        contract.validate_role_result(independent_result, "independent")
        is independent_result
    )
    assert owner_result["runtime_identity_exact19"] == independent_result[
        "runtime_identity_exact19"
    ]
    assert owner_result["manifest_rows"] == independent_result["manifest_rows"]
    assert owner_result["distribution_closures"] == independent_result[
        "distribution_closures"
    ]
    assert owner_result["canonical_diagnostic"] == independent_result[
        "canonical_diagnostic"
    ]
    assert _snapshot_tree(root) == before


def test_owner_and_independent_observe_actual_target_runtime_separately(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    owner_observer = owner._observe_owner_runtime_properties
    independent_observer = independent._observe_independent_runtime_properties
    request, _root, _site, _tamper_payload = _mini_runtime(tmp_path, monkeypatch)
    executable = request["runtime"]["executable"]

    assert owner_observer is not independent_observer
    _assert_violation(
        "BASE_OR_PREIMAGE_DRIFT", owner_observer, request, executable
    )
    _assert_violation(
        "BASE_OR_PREIMAGE_DRIFT", independent_observer, request, executable
    )

    for path, function_name in (
        (_OWNER_PATH, "_observe_owner_runtime_properties"),
        (_INDEPENDENT_PATH, "_observe_independent_runtime_properties"),
    ):
        function = next(
            node
            for node in _tree(path).body
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
            and node.name == function_name
        )
        source = ast.get_source_segment(_source(path), function)
        assert source is not None
        for required_observation in (
            "sys.implementation",
            "sys.version_info",
            "sys.platform",
            "platform.machine",
            "sys.executable",
            "os.path.samefile",
        ):
            assert required_observation in source


@pytest.mark.parametrize(
    "tamper",
    ("hash", "missing", "extra", "symlink", "pyc", "pycache", "nonregular"),
)
def test_both_derivations_reject_runtime_tamper(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch, tamper: str
) -> None:
    request, _root, site, tamper_payload = _mini_runtime(tmp_path, monkeypatch)
    if tamper == "hash":
        tamper_payload.write_bytes(b"tampered bytes\n")
    elif tamper == "missing":
        tamper_payload.unlink()
    elif tamper == "extra":
        _write_bytes(site / "unowned-extra.txt", b"extra\n")
    elif tamper == "symlink":
        (site / "unowned-link").symlink_to(tamper_payload)
    elif tamper == "pyc":
        _write_bytes(site / "unexpected.pyc", b"bytecode\n")
    elif tamper == "pycache":
        (site / "__pycache__").mkdir()
    else:
        os.mkfifo(site / "unexpected-fifo")

    _assert_violation("OWNER_INVALID", owner.derive_owner, _json_clone(request))
    _assert_violation(
        "INDEPENDENT_INVALID",
        independent.derive_independent,
        _json_clone(request),
    )


def test_expected_full_root_attestation_and_outside_site_drift_fail_closed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    request, root, _site, _tamper_payload = _mini_runtime(tmp_path, monkeypatch)

    wrong_expected = _json_clone(request)
    wrong_expected["materialization"]["expected_full_root_manifest_sha256"] = (
        "f" * 64
    )
    assert (
        wrong_expected["materialization"]["expected_full_root_manifest_sha256"]
        != request["materialization"]["expected_full_root_manifest_sha256"]
    )
    _refresh_materialization_attestation(wrong_expected)
    assert contract.validate_request(wrong_expected) is wrong_expected
    _assert_violation(
        "OWNER_INVALID", owner.derive_owner, _json_clone(wrong_expected)
    )
    _assert_violation(
        "INDEPENDENT_INVALID",
        independent.derive_independent,
        _json_clone(wrong_expected),
    )
    launch_attempts: list[list[str]] = []

    def forbidden_popen(argv: list[str], **_kwargs: Any) -> Any:
        launch_attempts.append(list(argv))
        raise AssertionError("pre-root mismatch must not launch a process")

    monkeypatch.setattr(
        checker,
        "_source_bindings",
        lambda _repo_root: {"STABLE": "a" * 64},
    )
    monkeypatch.setattr(checker, "_popen_factory", forbidden_popen)
    _assert_violation(
        "BASE_OR_PREIMAGE_DRIFT",
        _official_orchestrate,
        _json_clone(wrong_expected),
    )
    assert launch_attempts == []

    _write_bytes(root / "outside-site-drift.txt", b"unexpected root payload\n")
    _assert_violation("OWNER_INVALID", owner.derive_owner, _json_clone(request))
    _assert_violation(
        "INDEPENDENT_INVALID",
        independent.derive_independent,
        _json_clone(request),
    )


@pytest.mark.parametrize("drift_slot", ("commit", "tree"))
def test_official_checker_rejects_actual_git_head_or_tree_drift_before_launch(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    drift_slot: str,
) -> None:
    request, _root, _site, _tamper_payload = _mini_runtime(tmp_path, monkeypatch)
    observed_commit = request["frozen"]["mashos_api_commit"]
    observed_tree = request["frozen"]["mashos_api_tree"]
    if drift_slot == "commit":
        observed_commit = "f" * 40
    else:
        observed_tree = "f" * 40
    monkeypatch.setattr(
        checker,
        "_actual_git_head_tree",
        lambda _repo_root: (observed_commit, observed_tree),
    )
    launch_attempts: list[list[str]] = []

    def forbidden_popen(argv: list[str], **_kwargs: Any) -> Any:
        launch_attempts.append(list(argv))
        raise AssertionError("HEAD/tree drift must stop before process launch")

    monkeypatch.setattr(checker, "_popen_factory", forbidden_popen)
    _assert_violation(
        "BASE_OR_PREIMAGE_DRIFT",
        _official_orchestrate,
        _json_clone(request),
    )
    assert launch_attempts == []


def test_orchestrator_uses_fixed_exact4_process_order_and_public_body_free_handoff(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    request, root, _site, _tamper_payload = _mini_runtime(tmp_path, monkeypatch)
    owner_result = owner.derive_owner(_json_clone(request))
    independent_result = independent.derive_independent(_json_clone(request))
    owner_result["process_id"] = _synthetic_pid(7001)
    independent_result["process_id"] = _synthetic_pid(7004)
    before = _snapshot_tree(root)
    calls: list[dict[str, Any]] = []
    popen_factory = _install_fake_popen(
        monkeypatch, owner_result, independent_result, calls
    )

    result = _official_orchestrate(_json_clone(request))

    executable = request["runtime"]["executable"]
    assert len(calls) == 4
    assert calls[0]["argv"] == [
        executable,
        "-I",
        "-B",
        "-c",
        checker._ROLE_LAUNCH_PROGRAM,
        _REPO_ROOT.as_posix(),
        "ai.tools.emlis_nls_v3_s11_g4b_runtime_admission_owner_v1",
    ]
    assert calls[1]["argv"] == [
        executable,
        "-I",
        "-B",
        "-m",
        "pytest",
        "--version",
    ]
    assert calls[2]["argv"] == [
        executable,
        "-I",
        "-B",
        "-c",
        checker._ROLE_SMOKE_PROGRAM,
        _REPO_ROOT.as_posix(),
    ]
    assert calls[3]["argv"] == [
        executable,
        "-I",
        "-B",
        "-c",
        checker._ROLE_LAUNCH_PROGRAM,
        _REPO_ROOT.as_posix(),
        "ai.tools.emlis_nls_v3_s11_g4b_runtime_admission_independent_v1",
    ]
    assert [call["process_id"] for call in calls] == [
        _synthetic_pid(7001),
        _synthetic_pid(7002),
        _synthetic_pid(7003),
        _synthetic_pid(7004),
    ]
    assert calls[0]["input"] == contract.canonical_json_bytes(request)
    assert calls[3]["input"] == contract.canonical_json_bytes(request)
    assert calls[1]["input"] is None
    assert calls[2]["input"] is None
    assert calls[0]["cwd"] == _REPO_ROOT.as_posix()
    assert calls[1]["cwd"] == request["materialization"]["probe_cwd"]
    assert calls[2]["cwd"] == _REPO_ROOT.as_posix()
    assert calls[3]["cwd"] == _REPO_ROOT.as_posix()
    for call in calls:
        assert "shell" not in call
        assert call["stdin"] == checker.subprocess.PIPE
        assert call["stdout"] == checker.subprocess.PIPE
        assert call["stderr"] == checker.subprocess.PIPE
        assert call["close_fds"] is True
        assert call["timeout"] == checker._PROCESS_TIMEOUT_SECONDS
        assert call["env"] == {
            "LANG": "C.UTF-8",
            "LC_ALL": "C.UTF-8",
            "PYTHONDONTWRITEBYTECODE": "1",
            "PYTHONHASHSEED": "0",
            "PYTHONNOUSERSITE": "1",
            "PYTHONUTF8": "1",
            "PYTEST_DISABLE_PLUGIN_AUTOLOAD": "1",
        }
    assert getattr(popen_factory, "responses") == []
    assert getattr(popen_factory, "pids") == []
    assert result["status"] == "VALID"
    assert result["runtime_ready"] is True
    assert result["gate_b_closed"] is True
    assert result["checks_completed"] == list(contract.ContractV1.CHECK_ORDER)
    assert result["handoff_state"] == "HANDOFF_BOUND_CURRENT_SESSION"
    assert result["handoff_consumed"] is False
    assert result["gate_c_authorized"] is False
    assert result["target_execution_count"] == 0
    assert result["automatic_progression"] is False
    assert set(result) == contract.ContractV1.PUBLIC_SUCCESS_KEYS
    assert contract.validate_public_result(result) is result
    assert result["handoff_binding_sha256"] == _expected_handoff_binding(
        request, owner_result, result
    )
    _assert_body_free_public_result(result, request)
    assert _snapshot_tree(root) == before


def test_public_result_schema_rejects_private_extensions_and_invalid_versions(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    request, _root, _site, _tamper_payload = _mini_runtime(tmp_path, monkeypatch)
    owner_result = owner.derive_owner(_json_clone(request))
    independent_result = independent.derive_independent(_json_clone(request))
    owner_result["process_id"] = _synthetic_pid(7101)
    independent_result["process_id"] = _synthetic_pid(7104)
    calls: list[dict[str, Any]] = []
    _install_fake_popen(
        monkeypatch, owner_result, independent_result, calls
    )
    public_success = _official_orchestrate(_json_clone(request))

    leaked_manifest = _json_clone(public_success)
    leaked_manifest["manifest_rows"] = owner_result["manifest_rows"]
    _assert_violation(
        "PRIVACY_VIOLATION",
        contract.validate_public_result,
        leaked_manifest,
    )

    leaked_path = _json_clone(public_success)
    leaked_path["absolute_runtime_root"] = request["materialization"]["root"]
    _assert_violation(
        "PRIVACY_VIOLATION", contract.validate_public_result, leaked_path
    )

    future_version = _json_clone(public_success)
    future_version["schema_version"] = (
        "emlis.nls_v3.s11.g4b.runtime_admission.public_result.v2"
    )
    _assert_violation(
        "PRIVACY_VIOLATION", contract.validate_public_result, future_version
    )

    wrong_type = _json_clone(public_success)
    wrong_type["target_execution_count"] = False
    _assert_violation(
        "PRIVACY_VIOLATION", contract.validate_public_result, wrong_type
    )


def test_handoff_binding_is_current_session_private_and_not_consumed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    request, _root, _site, _tamper_payload = _mini_runtime(tmp_path, monkeypatch)
    owner_result = owner.derive_owner(_json_clone(request))
    independent_result = independent.derive_independent(_json_clone(request))
    owner_result["process_id"] = _synthetic_pid(7201)
    independent_result["process_id"] = _synthetic_pid(7204)
    first_calls: list[dict[str, Any]] = []
    _install_fake_popen(
        monkeypatch, owner_result, independent_result, first_calls
    )
    first = _official_orchestrate(_json_clone(request))

    rebound_request = _json_clone(request)
    rebound_request["handoff"]["receiver_nonce"] = "receiver-current-002"
    second_calls: list[dict[str, Any]] = []
    _install_fake_popen(
        monkeypatch, owner_result, independent_result, second_calls
    )
    second = _official_orchestrate(rebound_request)

    assert first["runtime_instance_observation_id"] == second[
        "runtime_instance_observation_id"
    ]
    assert first["runtime_readiness_observation_id"] == second[
        "runtime_readiness_observation_id"
    ]
    assert first["handoff_binding_sha256"] != second["handoff_binding_sha256"]
    assert first["handoff_binding_sha256"] == _expected_handoff_binding(
        request, owner_result, first
    )
    assert second["handoff_binding_sha256"] == _expected_handoff_binding(
        rebound_request, owner_result, second
    )
    locator_tamper = _json_clone(request)
    locator_tamper["materialization"]["root"] += "-different"
    locator_tamper["runtime"]["executable"] = (
        locator_tamper["materialization"]["root"] + "/bin/python"
    )
    assert _expected_handoff_binding(locator_tamper, owner_result, first) != first[
        "handoff_binding_sha256"
    ]
    for result, source_request in (
        (first, request),
        (second, rebound_request),
    ):
        assert result["handoff_state"] == "HANDOFF_BOUND_CURRENT_SESSION"
        assert result["handoff_consumed"] is False
        assert result["gate_c_authorized"] is False
        assert result["automatic_progression"] is False
        _assert_body_free_public_result(result, source_request)


def test_public_stop_is_typed_body_free_and_unknown_codes_fail_internal() -> None:
    for code in sorted(contract.ContractV1.STOP_CODES):
        typed_stop = checker._public_stop(code)
        assert set(typed_stop) == contract.ContractV1.PUBLIC_STOP_KEYS
        assert typed_stop["status"] == "STOP"
        assert typed_stop["terminal"] == code
        assert contract.validate_public_result(typed_stop) is typed_stop
        _assert_body_free_public_result(typed_stop, _valid_request())

    internal_stop = checker._public_stop("NOT_A_V1_STOP_CODE")
    assert internal_stop["terminal"] == "INTERNAL_FAIL_CLOSED"
    assert contract.validate_public_result(internal_stop) is internal_stop

    handoff_stop = checker._public_stop("HANDOFF_INVALID")
    invalid_terminal = _json_clone(handoff_stop)
    invalid_terminal["terminal"] = "FUTURE_UNTYPED_STOP"
    _assert_violation(
        "PRIVACY_VIOLATION", contract.validate_public_result, invalid_terminal
    )

    missing = _json_clone(handoff_stop)
    del missing["handoff_state"]
    _assert_violation(
        "PRIVACY_VIOLATION", contract.validate_public_result, missing
    )

    wrong_type = _json_clone(handoff_stop)
    wrong_type["target_execution_count"] = False
    _assert_violation(
        "PRIVACY_VIOLATION", contract.validate_public_result, wrong_type
    )


@pytest.mark.parametrize(
    ("raised", "expected_terminal", "expected_exit"),
    (
        (
            contract.ContractViolation("HANDOFF_INVALID", "synthetic rejection"),
            "HANDOFF_INVALID",
            2,
        ),
        (RuntimeError("synthetic internal failure"), "INTERNAL_FAIL_CLOSED", 3),
    ),
)
def test_checker_main_maps_failures_to_typed_stop_and_exit_status(
    monkeypatch: pytest.MonkeyPatch,
    raised: Exception,
    expected_terminal: str,
    expected_exit: int,
) -> None:
    stdin = SimpleNamespace(buffer=io.BytesIO(contract.canonical_json_bytes(_valid_request())))
    stdout_bytes = io.BytesIO()
    stdout = SimpleNamespace(buffer=stdout_bytes)

    def reject(_request: dict[str, Any], admission_token: object) -> dict[str, Any]:
        assert admission_token is checker._CLI_ADMISSION_TOKEN
        raise raised

    monkeypatch.setattr(checker, "sys", SimpleNamespace(stdin=stdin, stdout=stdout))
    monkeypatch.setattr(checker, "_assert_official_cli_context", lambda: None)
    monkeypatch.setattr(checker, "_orchestrate_cli", reject)

    assert checker.main() == expected_exit
    public_stop = contract.read_strict_json(io.BytesIO(stdout_bytes.getvalue()))
    assert public_stop["terminal"] == expected_terminal
    assert contract.validate_public_result(public_stop) is public_stop
    _assert_body_free_public_result(public_stop, _valid_request())


def test_orchestrator_rejects_pid_overlap_and_independent_divergence_without_retry(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    request, _root, _site, _tamper_payload = _mini_runtime(tmp_path, monkeypatch)
    owner_result = owner.derive_owner(_json_clone(request))
    independent_result = independent.derive_independent(_json_clone(request))
    owner_result["process_id"] = _synthetic_pid(8001)
    independent_result["process_id"] = _synthetic_pid(8004)
    calls: list[dict[str, Any]] = []
    _install_fake_popen(
        monkeypatch,
        owner_result,
        independent_result,
        calls,
        process_ids=[
            _synthetic_pid(8002),
            _synthetic_pid(8003),
            _synthetic_pid(8004),
            _synthetic_pid(8005),
        ],
    )
    _assert_violation(
        "PROCESS_CARDINALITY_OR_LAUNCH_INVALID",
        _official_orchestrate,
        _json_clone(request),
    )
    assert len(calls) == 1

    owner_result["process_id"] = _synthetic_pid(8101)
    independent_result["process_id"] = _synthetic_pid(8101)
    calls = []
    _install_fake_popen(
        monkeypatch,
        owner_result,
        independent_result,
        calls,
        process_ids=[
            _synthetic_pid(8101),
            _synthetic_pid(8102),
            _synthetic_pid(8103),
            _synthetic_pid(8101),
        ],
    )
    _assert_violation(
        "PROCESS_CARDINALITY_OR_LAUNCH_INVALID",
        _official_orchestrate,
        _json_clone(request),
    )
    assert len(calls) == 4

    owner_result["process_id"] = _synthetic_pid(8201)
    independent_result["process_id"] = _synthetic_pid(8204)
    independent_result["runtime_identity_exact19"][
        "runtime_root_identity_sha256"
    ] = "9" * 64
    calls = []
    _install_fake_popen(
        monkeypatch,
        owner_result,
        independent_result,
        calls,
        process_ids=[
            _synthetic_pid(8201),
            _synthetic_pid(8202),
            _synthetic_pid(8203),
            _synthetic_pid(8204),
        ],
    )
    _assert_violation(
        "DERIVATION_DIVERGENCE",
        _official_orchestrate,
        _json_clone(request),
    )
    assert len(calls) == 4


def test_orchestrator_detects_runtime_mutation_before_handoff(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    request, _root, site, _tamper_payload = _mini_runtime(tmp_path, monkeypatch)
    owner_result = owner.derive_owner(_json_clone(request))
    independent_result = independent.derive_independent(_json_clone(request))
    owner_result["process_id"] = _synthetic_pid(9001)
    independent_result["process_id"] = _synthetic_pid(9004)
    calls: list[dict[str, Any]] = []
    base_factory = _install_fake_popen(
        monkeypatch, owner_result, independent_result, calls
    )

    def mutating_factory(argv: list[str], **kwargs: Any) -> Any:
        process = base_factory(argv, **kwargs)
        if len(calls) == 4:
            _write_bytes(site / "post-observation-drift.txt", b"drift\n")
        return process

    monkeypatch.setattr(checker, "_popen_factory", mutating_factory)

    _assert_violation(
        "ROOT_DRIFT",
        _official_orchestrate,
        _json_clone(request),
    )
    assert len(calls) == 4


@pytest.mark.parametrize(
    ("drift_kind", "expected_process_count"),
    (("source", 3), ("head", 4)),
)
def test_official_checker_detects_repo_control_drift_without_writing_sources(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    drift_kind: str,
    expected_process_count: int,
) -> None:
    request, _root, _site, _tamper_payload = _mini_runtime(tmp_path, monkeypatch)
    owner_result = owner.derive_owner(_json_clone(request))
    independent_result = independent.derive_independent(_json_clone(request))
    owner_result["process_id"] = _synthetic_pid(9101)
    independent_result["process_id"] = _synthetic_pid(9104)
    calls: list[dict[str, Any]] = []
    _install_fake_popen(monkeypatch, owner_result, independent_result, calls)

    expected_head = (
        request["frozen"]["mashos_api_commit"],
        request["frozen"]["mashos_api_tree"],
    )
    stable_sources = {"OWNER": "1" * 64, "INDEPENDENT": "2" * 64}
    if drift_kind == "source":
        source_observations = [stable_sources, {"OWNER": "3" * 64}]

        def source_bindings(_repo_root: str) -> dict[str, str]:
            return source_observations.pop(0)

        monkeypatch.setattr(checker, "_source_bindings", source_bindings)
    else:
        head_observations = [expected_head, ("f" * 40, expected_head[1])]

        def actual_head_tree(_repo_root: str) -> tuple[str, str]:
            return head_observations.pop(0)

        monkeypatch.setattr(checker, "_actual_git_head_tree", actual_head_tree)
        monkeypatch.setattr(
            checker, "_source_bindings", lambda _repo_root: stable_sources
        )

    _assert_violation(
        "ROOT_DRIFT",
        _official_orchestrate,
        _json_clone(request),
    )
    assert len(calls) == expected_process_count


def test_public_callable_boundaries_are_explicit() -> None:
    assert list(inspect.signature(owner.derive_owner).parameters) == ["request"]
    assert list(inspect.signature(independent.derive_independent).parameters) == [
        "request"
    ]
    assert list(inspect.signature(checker.orchestrate).parameters) == ["request"]
    assert list(inspect.signature(checker._orchestrate_cli).parameters) == [
        "request",
        "admission_token",
    ]
    _assert_violation(
        "CURRENT_AUTHORITY_STOP", checker.orchestrate, _valid_request()
    )
    _assert_violation(
        "CURRENT_AUTHORITY_STOP",
        checker._orchestrate_cli,
        _valid_request(),
        object(),
    )
    assert checker._CLI_ADMISSION_TOKEN is not None
    assert callable(owner.main)
    assert callable(independent.main)
    assert callable(checker.main)


def test_owner_and_independent_are_separate_files_and_no_cross_import() -> None:
    assert _OWNER_PATH != _INDEPENDENT_PATH
    owner_imports = _imported_modules(_OWNER_PATH)
    independent_imports = _imported_modules(_INDEPENDENT_PATH)

    shared_contract = (
        "ai.tools.emlis_nls_v3_s11_g4b_runtime_admission_contract_v1"
    )
    owner_family_imports = {
        name
        for name in owner_imports
        if "emlis_nls_v3_s11_g4b_runtime_admission_" in name
    }
    independent_family_imports = {
        name
        for name in independent_imports
        if "emlis_nls_v3_s11_g4b_runtime_admission_" in name
    }
    assert owner_family_imports == {shared_contract}
    assert independent_family_imports == {shared_contract}

    assert not any("runtime_admission_independent" in name for name in owner_imports)
    assert not any("runtime_admission_owner" in name for name in independent_imports)
    assert "importlib.metadata" in owner_imports
    assert "importlib.metadata" not in independent_imports

    owner_calls = {
        _call_name(node)
        for node in ast.walk(_tree(_OWNER_PATH))
        if isinstance(node, ast.Call)
    }
    independent_calls = {
        _call_name(node)
        for node in ast.walk(_tree(_INDEPENDENT_PATH))
        if isinstance(node, ast.Call)
    }
    assert "importlib.metadata.distributions" in owner_calls
    assert "os.scandir" in independent_calls


def test_orchestrator_constructs_two_explicit_module_role_processes() -> None:
    source = _source(_CHECKER_PATH)
    assert "emlis_nls_v3_s11_g4b_runtime_admission_owner_v1" in source
    assert "emlis_nls_v3_s11_g4b_runtime_admission_independent_v1" in source
    imported = _imported_modules(_CHECKER_PATH)
    assert "subprocess" in imported
    assert "subprocess.run" not in source
    assert "_popen_factory: PopenFactory = subprocess.Popen" in source
    assert "_orchestrate_cli(" in source
    assert "_CLI_ADMISSION_TOKEN" in source


def test_required_role_smoke_installs_read_only_audit_guard_before_imports() -> None:
    program = checker._ROLE_SMOKE_PROGRAM
    tree = ast.parse(program, filename="<g4b-role-smoke>")
    calls = {
        _call_name(node) for node in ast.walk(tree) if isinstance(node, ast.Call)
    }
    assert "sys.addaudithook" in calls
    assert program.index("sys.addaudithook(deny_effect)") < program.index(
        "module_spec.loader.exec_module(module)"
    )
    for blocked_event in (
        '"open"',
        '"os.chmod"',
        '"os.mkdir"',
        '"os.remove"',
        '"os.rename"',
        '"os.symlink"',
        '"os.system"',
        '"subprocess.Popen"',
        'event.startswith("socket.")',
        'event.startswith("os.spawn")',
        'event.startswith("os.posix_spawn")',
        '"wax+"',
        '"O_CREAT"',
        '"O_TRUNC"',
        '"O_WRONLY"',
    ):
        assert blocked_event in program
    assert "effect_attempt_count" in program


def test_checker_family_has_no_filesystem_mutator_or_network_import() -> None:
    forbidden_import_roots = {
        "aiohttp",
        "ftplib",
        "http",
        "requests",
        "socket",
        "urllib",
    }
    forbidden_calls = {
        "os.chmod",
        "os.chown",
        "os.makedirs",
        "os.mkdir",
        "os.link",
        "os.remove",
        "os.rename",
        "os.replace",
        "os.rmdir",
        "os.symlink",
        "os.truncate",
        "os.unlink",
        "shutil.copy",
        "shutil.copy2",
        "shutil.copyfile",
        "shutil.copytree",
        "shutil.move",
        "shutil.rmtree",
    }
    forbidden_methods = {
        "chmod",
        "hardlink_to",
        "mkdir",
        "rename",
        "replace",
        "rmdir",
        "symlink_to",
        "touch",
        "unlink",
        "write_bytes",
        "write_text",
    }

    for path in _FAMILY_PATHS:
        imports = _imported_modules(path)
        assert not ({name.split(".", 1)[0] for name in imports} & forbidden_import_roots)
        for node in ast.walk(_tree(path)):
            if not isinstance(node, ast.Call):
                continue
            name = _call_name(node)
            assert name not in forbidden_calls, f"{path.name}: {name}"
            assert name.rsplit(".", 1)[-1] not in forbidden_methods, (
                f"{path.name}: {name}"
            )
            if name in {"open", "Path.open"} or name.endswith(".open"):
                mode: str | None = None
                mode_supplied = False
                if len(node.args) >= 2 and isinstance(node.args[1], ast.Constant):
                    mode = node.args[1].value
                    mode_supplied = True
                elif len(node.args) >= 2:
                    mode_supplied = True
                for keyword in node.keywords:
                    if keyword.arg == "mode":
                        mode_supplied = True
                        if isinstance(keyword.value, ast.Constant):
                            mode = keyword.value.value
                if mode_supplied:
                    assert isinstance(mode, str), f"{path.name}: dynamic open mode"
                if isinstance(mode, str):
                    assert not set(mode) & set("wax+"), f"{path.name}: open {mode}"
            if name == "os.open" and len(node.args) >= 2:
                forbidden_flags = {
                    "O_APPEND",
                    "O_CREAT",
                    "O_EXCL",
                    "O_RDWR",
                    "O_TRUNC",
                    "O_WRONLY",
                }
                used_flags = {
                    item.attr
                    for item in ast.walk(node.args[1])
                    if isinstance(item, ast.Attribute)
                }
                assert not used_flags & forbidden_flags, (
                    f"{path.name}: os.open flags {sorted(used_flags & forbidden_flags)}"
                )


def test_checker_family_uses_only_stdlib_and_existing_project_modules() -> None:
    allowed_project_prefixes = (
        "ai.tools.emlis_nls_v3_s11_g4b_runtime_admission_",
    )
    stdlib = __import__("sys").stdlib_module_names

    for path in _FAMILY_PATHS:
        for name in _imported_modules(path):
            root = name.split(".", 1)[0]
            assert (
                root in stdlib
                or root == "__future__"
                or name.startswith(allowed_project_prefixes)
            ), (
                path.name,
                name,
            )


def test_checker_family_does_not_reference_product_or_hundred_case_runner() -> None:
    forbidden_fragments = (
        "ai.services.ai_inference",
        "emlis_ai_step11_",
        "emlis_nls_v3_step11_batch_run",
    )
    for path in _FAMILY_PATHS:
        values = (
            node.value
            for node in ast.walk(_tree(path))
            if isinstance(node, ast.Constant) and isinstance(node.value, str)
        )
        for value in values:
            assert not any(fragment in value for fragment in forbidden_fragments), (
                path.name,
                value,
            )
