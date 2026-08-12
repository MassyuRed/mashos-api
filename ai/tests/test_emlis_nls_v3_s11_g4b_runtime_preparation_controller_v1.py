#!/usr/bin/env python3
"""Effect-free exact18 tests for the G4-B preparation controller family V1."""

from __future__ import annotations

import ast
import base64
import copy
import ctypes
import datetime as _datetime
import errno
import fcntl
import hashlib
import io
import json
import os
from pathlib import Path
import signal
import stat
import sys
import sysconfig
import tempfile
import time
import types
import unittest
from unittest import mock
import zipfile

from ai.tools import emlis_nls_v3_s11_g4b_runtime_acquisition_v1 as acquisition
from ai.tools import emlis_nls_v3_s11_g4b_runtime_admission_bridge_v1 as bridge
from ai.tools import emlis_nls_v3_s11_g4b_runtime_admission_contract_v1 as checker_contract
from ai.tools import emlis_nls_v3_s11_g4b_runtime_materialization_v1 as materialization
from ai.tools import emlis_nls_v3_s11_g4b_runtime_preparation_contract_v1 as contract
from ai.tools import emlis_nls_v3_s11_g4b_runtime_preparation_controller_v1 as controller


REPO_ROOT = Path(__file__).resolve().parents[2]
TOOLS = REPO_ROOT / "ai" / "tools"
CONFIGS = REPO_ROOT / "ai" / "configs"
DERIVED_LOCK = CONFIGS / "emlis_nls_v3_s11_g4b_runtime_preparation_exact5_lock_v1.json"
FORMAL_LOCK = CONFIGS / "emlis_nls_v3_recovery_epoch002_formal_worker_bootstrap_lock_v1.json"
SHA256_ZERO = "0" * 64
_PRIVILEGED_PARENT_FLAG = "--privileged-fd9-integration-parent-v2"
_PRIVILEGED_UID = 65534
_PRIVILEGED_GID = 65534
_PRIVILEGED_STDIN_LIMIT = 131_072
_PRIVILEGED_RECORD_LIMIT = 512
_PRIVILEGED_SENTINEL = b"G4B_V6_BODY_FREE:"
_PRIVILEGED_EVENT_SCHEMA = "g4b.v6.privileged_event.v1"
_PRIVILEGED_DIAGNOSTIC_SCHEMA = "g4b.v6.privileged_diagnostic.v1"
_PRIVILEGED_ENVELOPE_SCHEMA = "g4b.privileged_fd9.integration.v2"
_PRIVILEGED_RUNTIME_SOURCE_SIZE_LIMIT = 67_108_864
_PRIVILEGED_MANIFEST = (
    (
        "ai.tools.emlis_nls_v3_s11_g4b_runtime_preparation_contract_v1",
        "ai/tools/emlis_nls_v3_s11_g4b_runtime_preparation_contract_v1.py",
        73834,
        "966587a6457dc6376d53272e96019909d4c11ec98acc4c85d337f300ea462816",
    ),
    (
        "ai.tools.emlis_nls_v3_s11_g4b_runtime_acquisition_v1",
        "ai/tools/emlis_nls_v3_s11_g4b_runtime_acquisition_v1.py",
        43593,
        "de39e53edf88018c0c87179e0a5760986f995537867c588102679a704e5b007b",
    ),
)
_PRIVILEGED_SAFE_ERRNOS = frozenset(
    {1, 2, 5, 9, 13, 17, 20, 21, 22, 24, 32, 36, 38, 40, 75, 95, 110}
)
_PRIVILEGED_STAGES = frozenset(
    {
        "ROOT_PARENT_OR_FIXTURE",
        "PRE_DROP_CWD_AND_FD9_SETUP",
        "CREDENTIAL_AND_AUTHORITY_DROP",
        "EXECVE_REQUEST",
        "POSTEXEC_BOOTSTRAP_AND_LOADER",
        "POSTEXEC_PRODUCTION_CAPTURE",
        "POSTEXEC_PRE_P3_REREAD_AND_CLOSE",
        "PARENT_WAIT_OR_RESULT_TRANSPORT",
        "EVIDENCE_INSUFFICIENT",
    }
)
_PRIVILEGED_INTERNAL_REASONS = frozenset(
    {
        "OS_ERROR_OUTSIDE_SAFE_SET",
        "SCHEMA_OR_CANONICALITY_INVALID",
        "IDENTITY_OR_HASH_MISMATCH",
        "DESCRIPTOR_SET_OR_CLOSE_UNCERTAIN",
        "CREDENTIAL_CONTRACT_MISMATCH",
        "EVENT_OR_RESULT_TRANSPORT_INVALID",
    }
)
_PRIVILEGED_REASON_CLASSES = frozenset(
    {
        "IMPLEMENTATION_CONTRACT",
        "WORK_PRIVILEGE_OR_OS_SURFACE",
        "EXEC_BOOTSTRAP",
        "PRODUCTION_FD9_PROOF",
        "RESULT_TRANSPORT_INDETERMINATE",
    }
)

_PRIVILEGED_BOOTSTRAP_SOURCE = r'''import sys, os
_postexec_event = b'G4B_V6_BODY_FREE:{"event_class":"POSTEXEC_ENTERED","schema_version":"g4b.v6.privileged_event.v1","sequence_number":2}\n'
if os.write(2, _postexec_event) != len(_postexec_event):
    os._exit(71)
sys.path[:] = [entry for entry in sys.path if entry]
_stage = "POSTEXEC_BOOTSTRAP_AND_LOADER"
try:
    import errno as _errno
    import fcntl as _fcntl
    import hashlib as _hashlib
    import importlib.abc as _abc
    import importlib.machinery as _machinery
    import importlib.util as _util
    import json as _json
    import stat as _stat
    import types as _types

    _sentinel = b"G4B_V6_BODY_FREE:"
    _safe_errno = {1, 2, 5, 9, 13, 17, 20, 21, 22, 24, 32, 36, 38, 40, 75, 95, 110}
    _internal = {
        "OS_ERROR_OUTSIDE_SAFE_SET", "SCHEMA_OR_CANONICALITY_INVALID",
        "IDENTITY_OR_HASH_MISMATCH", "DESCRIPTOR_SET_OR_CLOSE_UNCERTAIN",
        "CREDENTIAL_CONTRACT_MISMATCH", "EVENT_OR_RESULT_TRANSPORT_INVALID",
    }

    def _canonical(value):
        return _json.dumps(
            value, ensure_ascii=False, sort_keys=True,
            separators=(",", ":"), allow_nan=False,
        ).encode("utf-8")

    def _pairs(pairs):
        result = {}
        for key, value in pairs:
            if key in result:
                raise ValueError("duplicate key")
            result[key] = value
        return result

    def _emit_diagnostic(stage, reason_class, error=None, internal=None):
        safe_number = None
        safe_internal = internal
        if isinstance(error, OSError) and error.errno in _safe_errno:
            safe_number = error.errno
            safe_internal = None
        elif safe_internal is None:
            safe_internal = "OS_ERROR_OUTSIDE_SAFE_SET" if isinstance(error, OSError) else "EVENT_OR_RESULT_TRANSPORT_INVALID"
        if safe_internal is not None and safe_internal not in _internal:
            safe_internal = "EVENT_OR_RESULT_TRANSPORT_INVALID"
        row = {
            "schema_version": "g4b.v6.privileged_diagnostic.v1",
            "terminal_class": "STOP",
            "stage": stage,
            "reason_class": reason_class,
            "safe_errno": safe_number,
            "safe_internal_reason": safe_internal,
            "execve_request_count": 1,
            "postexec_entry_count": 1,
            "child_exit_class": "CHILD_NONZERO",
        }
        payload = _sentinel + _canonical(row) + b"\n"
        if len(payload) <= 512:
            if os.write(2, payload) != len(payload):
                os._exit(71)

    def _read_stdin():
        chunks = []
        total = 0
        while True:
            block = os.read(0, 8192)
            if not block:
                break
            total += len(block)
            if total > 131072:
                raise ValueError("stdin limit")
            chunks.append(block)
        raw = b"".join(chunks)
        if not raw.endswith(b"\n") or raw.endswith(b"\n\n") or b"\r" in raw:
            raise ValueError("stdin framing")
        value = _json.loads(raw[:-1].decode("utf-8", "strict"), object_pairs_hook=_pairs)
        if _canonical(value) + b"\n" != raw:
            raise ValueError("stdin canonicality")
        return raw, value

    def _live_nonstdio():
        result = set()
        for name in os.listdir("/proc/self/fd"):
            if not name.isdigit():
                raise ValueError("fd name")
            fd = int(name)
            if fd < 3:
                continue
            try:
                _fcntl.fcntl(fd, _fcntl.F_GETFD)
            except OSError as error:
                if error.errno != _errno.EBADF:
                    raise
            else:
                result.add(fd)
        return result

    def _close_fd(fd):
        os.close(fd)
        try:
            _fcntl.fcntl(fd, _fcntl.F_GETFD)
        except OSError as error:
            if error.errno != _errno.EBADF:
                raise
        else:
            raise ValueError("descriptor remains open")

    def _sha_file(path, limit):
        digest = _hashlib.sha256()
        total = 0
        fd = os.open(path, os.O_RDONLY | getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_NOFOLLOW", 0))
        try:
            observed = os.fstat(fd)
            if not _stat.S_ISREG(observed.st_mode) or observed.st_nlink != 1:
                raise ValueError("runtime source type")
            while True:
                block = os.read(fd, 131072)
                if not block:
                    break
                total += len(block)
                if total > limit:
                    raise ValueError("runtime source budget")
                digest.update(block)
        finally:
            _close_fd(fd)
        return total, digest.hexdigest()

    _raw_envelope, _envelope = _read_stdin()
    if type(_envelope) is not dict or set(_envelope) != {
        "schema_version", "bootstrap_source_manifest", "repository_cwd_identity",
        "negative_dac_locator", "runtime_source_identity", "execution_request",
    }:
        raise ValueError("envelope schema")
    if _envelope["schema_version"] != "g4b.privileged_fd9.integration.v2":
        raise ValueError("envelope version")
    _manifest = _envelope["bootstrap_source_manifest"]
    if type(_manifest) is not list or len(_manifest) != 2:
        raise ValueError("manifest count")
    _expected = {
        "ai.tools.emlis_nls_v3_s11_g4b_runtime_preparation_contract_v1":
            "ai/tools/emlis_nls_v3_s11_g4b_runtime_preparation_contract_v1.py",
        "ai.tools.emlis_nls_v3_s11_g4b_runtime_acquisition_v1":
            "ai/tools/emlis_nls_v3_s11_g4b_runtime_acquisition_v1.py",
    }
    _rows = {}
    for _row in _manifest:
        if type(_row) is not dict or set(_row) != {"module", "relative_path", "byte_size", "raw_sha256"}:
            raise ValueError("manifest row schema")
        _module = _row["module"]
        if _module not in _expected or _row["relative_path"] != _expected[_module] or _module in _rows:
            raise ValueError("manifest identity")
        if type(_row["byte_size"]) is not int or not 0 < _row["byte_size"] <= 1048576:
            raise ValueError("manifest byte size")
        if type(_row["raw_sha256"]) is not str or len(_row["raw_sha256"]) != 64:
            raise ValueError("manifest hash")
        int(_row["raw_sha256"], 16)
        _rows[_module] = dict(_row)
    if set(_rows) != set(_expected):
        raise ValueError("manifest module set")

    _root_open = False
    _root_fd = os.open(
        ".", os.O_RDONLY | os.O_DIRECTORY | getattr(os, "O_CLOEXEC", 0) |
        getattr(os, "O_NOFOLLOW", 0),
    )
    _root_open = True
    _root_stat = os.fstat(_root_fd)
    _cwd_identity = _envelope["repository_cwd_identity"]
    if type(_cwd_identity) is not dict or set(_cwd_identity) != {"st_dev", "st_ino"}:
        raise ValueError("cwd identity schema")
    if (_root_stat.st_dev, _root_stat.st_ino) != (_cwd_identity["st_dev"], _cwd_identity["st_ino"]):
        raise ValueError("cwd identity mismatch")

    def _source_bytes(row):
        parts = row["relative_path"].split("/")
        if not parts or any(not part or part in (".", "..") for part in parts):
            raise ValueError("relative path")
        current = _root_fd
        current_owned = False
        source_fd = None
        pending_fd = None
        try:
            for component in parts[:-1]:
                pending_fd = os.open(
                    component,
                    os.O_RDONLY | os.O_DIRECTORY | getattr(os, "O_CLOEXEC", 0) |
                    getattr(os, "O_NOFOLLOW", 0), dir_fd=current,
                )
                if current_owned:
                    old = current
                    current_owned = False
                    _close_fd(old)
                current = pending_fd
                pending_fd = None
                current_owned = True
            source_fd = os.open(
                parts[-1], os.O_RDONLY | getattr(os, "O_CLOEXEC", 0) |
                getattr(os, "O_NOFOLLOW", 0), dir_fd=current,
            )
            observed = os.fstat(source_fd)
            if not _stat.S_ISREG(observed.st_mode) or observed.st_nlink != 1 or observed.st_size != row["byte_size"]:
                raise ValueError("source stat")
            chunks = []
            remaining = row["byte_size"]
            while remaining:
                block = os.read(source_fd, min(131072, remaining))
                if not block:
                    raise ValueError("source short read")
                chunks.append(block)
                remaining -= len(block)
            if os.read(source_fd, 1) != b"":
                raise ValueError("source extra byte")
            raw = b"".join(chunks)
            if _hashlib.sha256(raw).hexdigest() != row["raw_sha256"]:
                raise ValueError("source hash")
            return raw
        finally:
            try:
                try:
                    if source_fd is not None:
                        closing = source_fd
                        source_fd = None
                        _close_fd(closing)
                finally:
                    if pending_fd is not None:
                        closing = pending_fd
                        pending_fd = None
                        _close_fd(closing)
            finally:
                if current_owned:
                    closing = current
                    current_owned = False
                    _close_fd(closing)

    class _Finder(_abc.MetaPathFinder, _abc.Loader):
        def __init__(self, rows):
            self.rows = rows
            self.loaded = set()

        def find_spec(self, fullname, path=None, target=None):
            if fullname in self.rows:
                return _util.spec_from_loader(fullname, self, origin=self.rows[fullname]["relative_path"])
            if fullname.startswith("ai."):
                raise ImportError("unknown ai module")
            return None

        def create_module(self, spec):
            return None

        def exec_module(self, module):
            fullname = module.__spec__.name
            if fullname in self.loaded:
                raise ImportError("duplicate load")
            raw = _source_bytes(self.rows[fullname])
            module.__file__ = self.rows[fullname]["relative_path"]
            module.__package__ = fullname.rpartition(".")[0]
            self.loaded.add(fullname)
            exec(compile(raw.decode("utf-8", "strict"), module.__file__, "exec", dont_inherit=True), module.__dict__)

    for _package in ("ai", "ai.tools"):
        if _package in sys.modules:
            raise ImportError("unexpected ai namespace")
        _module_object = _types.ModuleType(_package)
        _module_object.__package__ = _package
        _module_object.__path__ = []
        _module_object.__spec__ = _machinery.ModuleSpec(_package, loader=None, is_package=True)
        _module_object.__spec__.submodule_search_locations = []
        sys.modules[_package] = _module_object

    _finder = _Finder(_rows)
    sys.meta_path.insert(0, _finder)
    _contract = __import__(
        "ai.tools.emlis_nls_v3_s11_g4b_runtime_preparation_contract_v1",
        fromlist=["*"],
    )
    _acquisition = __import__(
        "ai.tools.emlis_nls_v3_s11_g4b_runtime_acquisition_v1",
        fromlist=["*"],
    )
    if _finder.loaded != set(_expected):
        raise ImportError("exact2 load incomplete")
    _reparsed = _contract.strict_json_from_bytes(_raw_envelope, require_final_lf=True)
    if _reparsed != _envelope:
        raise ValueError("contract reparse mismatch")
    _locator = _envelope["negative_dac_locator"]
    _request_input = _envelope["execution_request"]
    _request = _contract.validate_execution_request(_request_input)
    _runtime_source = _envelope["runtime_source_identity"]
    if type(_runtime_source) is not dict or set(_runtime_source) != {"byte_size", "raw_sha256"}:
        raise ValueError("runtime source schema")
    _runtime_size, _runtime_sha = _sha_file(sys.executable, 67108864)
    if _runtime_size != _runtime_source["byte_size"] or _runtime_sha != _runtime_source["raw_sha256"]:
        raise ValueError("runtime source identity")
    _request["control_runtime"]["executable"] = sys.executable
    sys.meta_path.remove(_finder)
    _finder_removed = True
    for _loaded_module in (_contract, _acquisition):
        if (
            _loaded_module.__loader__ is not _finder
            or _loaded_module.__spec__ is None
            or _loaded_module.__spec__.loader is not _finder
        ):
            raise ImportError("loader ownership drift")
        _loaded_module.__loader__ = None
        _loaded_module.__spec__.loader = None
        _loaded_module.__spec__.loader_state = None
    _loaded_module = None
    _package = None
    _module_object = None
    _finder.rows.clear()
    _finder.loaded.clear()
    _row.clear()
    _row = None
    _module = None
    _rows.clear()
    _manifest.clear()
    _expected.clear()
    _request_input = None
    _runtime_source.clear()
    _runtime_source = None
    _raw_envelope = b""
    _reparsed.clear()
    _envelope.clear()
    _cwd_identity.clear()
    _rows = None
    _manifest = None
    _expected = None
    _reparsed = None
    _envelope = None
    _cwd_identity = None
    _finder = None
    _Finder = None
    _source_bytes = None
    _abc = None
    _util = None
    _machinery = None
    _closing_root = _root_fd
    _root_fd = -1
    _root_open = False
    _close_fd(_closing_root)
    if _live_nonstdio() != {9}:
        raise ValueError("post-loader descriptor set")

    if type(_locator) is not str:
        raise ValueError("negative locator")
    try:
        _unexpected = os.open(_locator, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0))
    except OSError as _open_error:
        if _open_error.errno != _errno.EACCES:
            raise
    else:
        _close_fd(_unexpected)
        raise ValueError("pathname authority widened")
    _locator = None

    _stage = "POSTEXEC_PRODUCTION_CAPTURE"
    _source_state = _acquisition._capture_descriptor_source(_request)
    if _source_state["source_rows"][0]["stage"] != "P1_ENTRY":
        raise ValueError("P1 source row")
    _owned_fd = _source_state["source_owned_fd"]
    _stage = "POSTEXEC_PRE_P3_REREAD_AND_CLOSE"
    _p3_row, _p3_sha = _acquisition._observe_and_close_descriptor_before_p3(_request, _source_state)
    if _p3_row["stage"] != "P3_PRELAUNCH" or _p3_sha != _request["egress_attestation_sha256"]:
        raise ValueError("P1/P3 mismatch")
    if _source_state.get("source_owned_fd") is not None:
        raise ValueError("owned source remains")
    try:
        os.setresuid(0, 0, 0)
    except PermissionError:
        pass
    else:
        raise ValueError("privilege regain")
    if os.getresuid() != (65534, 65534, 65534):
        raise ValueError("failed regain changed credentials")
    for _closed_fd in (9, _owned_fd):
        try:
            _fcntl.fcntl(_closed_fd, _fcntl.F_GETFD)
        except OSError as _closed_error:
            if _closed_error.errno != _errno.EBADF:
                raise
        else:
            raise ValueError("source descriptor remains open")
    if _live_nonstdio():
        raise ValueError("terminal descriptor set")
except BaseException as _error:
    try:
        if globals().get("_root_open", False):
            _closing_root = _root_fd
            _root_fd = -1
            _root_open = False
            _close_fd(_closing_root)
    except BaseException as _cleanup_error:
        _error = _cleanup_error
    try:
        if globals().get("_finder", None) in sys.meta_path:
            sys.meta_path.remove(_finder)
            _finder_removed = True
    except BaseException as _cleanup_error:
        _error = _cleanup_error
    try:
        _reason = "EXEC_BOOTSTRAP"
        if _stage == "POSTEXEC_PRODUCTION_CAPTURE" or _stage == "POSTEXEC_PRE_P3_REREAD_AND_CLOSE":
            _reason = "PRODUCTION_FD9_PROOF"
        _internal_reason = None
        if not isinstance(_error, OSError):
            _internal_reason = "IDENTITY_OR_HASH_MISMATCH" if _stage == "POSTEXEC_BOOTSTRAP_AND_LOADER" else "EVENT_OR_RESULT_TRANSPORT_INVALID"
        _emit_diagnostic(_stage, _reason, _error, _internal_reason)
    except BaseException:
        pass
    os._exit(71)
os._exit(0)
'''


def _sha(payload: bytes) -> str:
    return hashlib.sha256(payload).hexdigest()


def _path_plan(authority_root: str = "/private/g4b-authority", repo: str = "/repo") -> dict[str, str]:
    plan = {
        "authority_root": authority_root,
        "controller_test_cwd": repo,
        "checker_test_cwd": repo,
    }
    for role, leaf in contract.PreparationContractV1.PATH_ROLE_LEAVES:
        plan[role] = authority_root + "/" + leaf
    return plan


def _credential_contract(
    uid: int = 1000, gid: int = 1000, supplementary_gids: list[int] | None = None
) -> dict[str, object]:
    c = contract.PreparationContractV1
    return {
        "schema_version": c.P1_CREDENTIAL_CONTRACT_SCHEMA,
        "ruid": uid,
        "euid": uid,
        "suid": uid,
        "fsuid": uid,
        "rgid": gid,
        "egid": gid,
        "sgid": gid,
        "fsgid": gid,
        "supplementary_gids": list(supplementary_gids or []),
        "cap_effective": 0,
        "cap_permitted": 0,
        "cap_inheritable": 0,
        "cap_ambient": 0,
        "no_new_privs": 1,
    }


def _source_object_identity(observed: object) -> dict[str, object]:
    c = contract.PreparationContractV1
    return {
        "schema_version": c.PLATFORM_SOURCE_OBJECT_IDENTITY_SCHEMA,
        "st_dev": observed.st_dev,
        "st_ino": observed.st_ino,
        "st_uid": observed.st_uid,
        "st_gid": observed.st_gid,
        "st_mode": observed.st_mode,
        "st_nlink": observed.st_nlink,
    }


def _source_fixed_identity(observed: object) -> dict[str, object]:
    c = contract.PreparationContractV1
    return {
        "schema_version": c.P1_SOURCE_FIXED_TUPLE_SCHEMA,
        "st_dev": observed.st_dev,
        "st_ino": observed.st_ino,
        "st_uid": observed.st_uid,
        "st_gid": observed.st_gid,
        "st_mode": observed.st_mode,
        "st_nlink": observed.st_nlink,
        "st_size": observed.st_size,
        "st_mtime_ns": observed.st_mtime_ns,
        "st_ctime_ns": observed.st_ctime_ns,
    }


def _mapping_provenance(
    source_object_identity: dict[str, object],
    credential: dict[str, object],
    trusted_root_binding_sha256: str = "7" * 64,
) -> dict[str, object]:
    c = contract.PreparationContractV1
    platform_open_contract = {
        "schema_version": c.PLATFORM_OPEN_CONTRACT_SCHEMA,
        "trusted_root_binding_sha256": trusted_root_binding_sha256,
        "open_access_mode": "O_RDONLY",
        "parent_fd_cloexec_before_mapping": True,
        "resolve_beneath": True,
        "resolve_no_symlinks": True,
        "resolve_no_magiclinks": True,
        "p1_writable_resolved_ancestor_count": 0,
        "p1_writable_source": False,
        "retained_writable_source_fd_count": 0,
        "same_authority_mutation_count": 0,
        "same_authority_replacement_count": 0,
        "same_authority_relink_count": 0,
        "same_authority_reissue_count": 0,
    }
    return {
        "schema_version": c.PLATFORM_MAPPING_PROVENANCE_SCHEMA,
        "platform_control_state_instance_id": "PLATFORM_STATE_001",
        "platform_mapping_event_id": "PLATFORM_MAPPING_EVENT_001",
        "authority_id": "AUTHORITY_001",
        "observation_session_id": "OBSERVATION_001",
        "stable_authority_approval_binding_sha256": "1" * 64,
        "approved_candidate_body_sha256": c.APPROVED_CANDIDATE_BODY_SHA256,
        "issuer_policy_id": c.EGRESS_ISSUER_POLICY_ID,
        "transfer_mechanism_id": c.TRANSFER_MECHANISM_ID,
        "transfer_class": c.TRANSFER_CLASS,
        "descriptor_number": c.SOURCE_DESCRIPTOR_NUMBER,
        "p1_credential_contract": credential,
        "p1_credential_contract_binding_sha256": contract.canonical_sha256(credential),
        "platform_open_contract": platform_open_contract,
        "platform_open_contract_binding_sha256": contract.canonical_sha256(
            platform_open_contract
        ),
        "platform_source_object_identity": source_object_identity,
        "platform_source_object_identity_binding_sha256": contract.canonical_sha256(
            source_object_identity
        ),
        "source_issue_count": 1,
        "source_open_count": 1,
        "mapping_count": 1,
        "p1_launch_count": 1,
        "inherited_nonstdio_platform_descriptor_count": 1,
        "stdin_writer_count": 1,
        "stdin_writer_duplicate_count_after_final_byte": 0,
        "stdin_canonical_exact_bytes": True,
        "stdin_bounded_eof": True,
        "parent_source_copy_closed_after_launch_acceptance": True,
    }


def _egress_attestation(
    mapping: dict[str, object],
    issued_at: str = "2026-08-12T00:00:00Z",
    expires_at: str = "2026-08-12T00:15:00Z",
) -> dict[str, object]:
    c = contract.PreparationContractV1
    mapping_binding = contract.canonical_sha256(mapping)
    authority_id = "AUTHORITY_001"
    observation_session_id = "OBSERVATION_001"
    stable_binding = "1" * 64
    attestation = {
        "schema_version": c.EGRESS_ATTESTATION_SCHEMA,
        "source_class": c.EGRESS_ISSUER_CLASS,
        "issuer_policy_id": c.EGRESS_ISSUER_POLICY_ID,
        "platform_control_state_instance_id": "PLATFORM_STATE_001",
        "issuer_provenance_binding_sha256": "",
        "platform_mapping_provenance_binding_sha256": mapping_binding,
        "stable_authority_approval_binding_sha256": stable_binding,
        "approved_candidate_body_sha256": c.APPROVED_CANDIDATE_BODY_SHA256,
        "policy_id": c.ACQUISITION_POLICY_ID,
        "allowed_scheme": c.ALLOWED_SCHEME,
        "allowed_hosts": list(c.ALLOWED_HOSTS),
        "enforcement_scope": "CURRENT_G4B_ONE_SHOT_ACQUISITION_EXACT1",
        "authority_id": authority_id,
        "observation_session_id": observation_session_id,
        "acquisition_process_count": 1,
        "active": True,
        "issued_at": issued_at,
        "expires_at": expires_at,
    }
    provenance = {key: attestation[key] for key in c.ISSUER_PROVENANCE_KEYS}
    provenance["schema_version"] = c.ISSUER_PROVENANCE_SCHEMA
    attestation["issuer_provenance_binding_sha256"] = contract.canonical_sha256(provenance)
    return attestation


def _execution_request_from_source(
    mapping: dict[str, object],
    attestation: dict[str, object],
    source_identity: dict[str, object],
) -> dict[str, object]:
    c = contract.PreparationContractV1
    authority_id = "AUTHORITY_001"
    observation_session_id = "OBSERVATION_001"
    stable_binding = "1" * 64
    attestation_sha = contract.canonical_sha256(attestation)
    return {
        "schema_version": c.EXECUTION_REQUEST_SCHEMA,
        "candidate_id": c.CANDIDATE_ID,
        "approved_candidate_body_sha256": c.APPROVED_CANDIDATE_BODY_SHA256,
        "stable_authority_approval_binding_sha256": stable_binding,
        "authority_id": authority_id,
        "observation_session_id": observation_session_id,
        "receiver_session_id": observation_session_id,
        "receiver_nonce": "NONCE_001",
        "expected_git": {
            "cocolon_commit": "a" * 40,
            "cocolon_tree": "b" * 40,
            "mashos_api_commit": "c" * 40,
            "mashos_api_tree": "d" * 40,
        },
        "control_runtime": {
            "executable": "/control/python",
            "implementation": c.EXPECTED_IMPLEMENTATION,
            "python_version": c.EXPECTED_PYTHON_VERSION,
            "platform_tag": c.EXPECTED_PLATFORM_TAG,
            "resolved_interpreter_sha256": c.EXPECTED_INTERPRETER_SHA256,
            "pip_version": c.EXPECTED_PIP_VERSION,
            "pip_installed_source_manifest_sha256": "e" * 64,
            "pip_main_parser_sha256": c.PIP_MAIN_PARSER_SHA256,
            "pip_build_env_sha256": c.PIP_BUILD_ENV_SHA256,
            "pip_runner_sha256": c.PIP_RUNNER_SHA256,
            "p5_static_launch_edge_proof_state": c.P5_STATIC_PROOF_STATE,
        },
        "path_plan": _path_plan(),
        "private_transport": {
            "schema_version": c.PRIVATE_TRANSPORT_SCHEMA,
            "https_proxy": "https://proxy.private:8443",
            "custom_ca_locator": "/private/work-ca.pem",
            "expected_proxy_class": "WORK_TRANSPORT_PROXY_V1",
            "expected_ca_raw_sha256": "f" * 64,
            "expected_stable_projection_sha256": "0" * 64,
        },
        "egress_attestation_source": {
            "schema_version": c.EGRESS_ATTESTATION_SOURCE_SCHEMA,
            "transfer_mechanism_id": c.TRANSFER_MECHANISM_ID,
            "transfer_class": c.TRANSFER_CLASS,
            "descriptor_number": c.SOURCE_DESCRIPTOR_NUMBER,
            "platform_mapping_provenance": mapping,
            "platform_mapping_provenance_binding_sha256": contract.canonical_sha256(
                mapping
            ),
            "expected_owner_uid": 0,
            "expected_mode": "0400",
            "expected_regular_file": True,
            "expected_nlink": 1,
            "expected_source_identity": source_identity,
            "expected_source_identity_binding_sha256": contract.canonical_sha256(
                source_identity
            ),
            "expected_raw_sha256": attestation_sha,
            "expected_expiry": attestation["expires_at"],
        },
        "egress_attestation": attestation,
        "egress_attestation_sha256": attestation_sha,
        "publication_contract": {
            "schema_version": c.PUBLICATION_CONTRACT_SCHEMA,
            "cocolon_pre_head": "9" * 40,
            "receipt_path": "documents/receipt.json",
            "current_state_path": "Cocolon_前提資料/08_cycle001_current_state.md",
            "conditional_closure_route_path": "documents/closure.md",
            "conditional_milestone_path": "",
            "approved_public_path_set_sha256": "8" * 64,
            "result_unknown_policy": c.RESULT_UNKNOWN_POLICY,
        },
    }


def _execution_request() -> dict[str, object]:
    synthetic = types.SimpleNamespace(
        st_dev=11,
        st_ino=12,
        st_uid=0,
        st_gid=0,
        st_mode=stat.S_IFREG | 0o400,
        st_nlink=1,
    )
    mapping = _mapping_provenance(
        _source_object_identity(synthetic), _credential_contract()
    )
    attestation = _egress_attestation(mapping)
    observed = types.SimpleNamespace(
        **vars(synthetic),
        st_size=len(contract.canonical_json_bytes(attestation)),
        st_mtime_ns=13,
        st_ctime_ns=14,
    )
    return _execution_request_from_source(
        mapping, attestation, _source_fixed_identity(observed)
    )


def _validated_lock() -> dict[str, object]:
    return contract.validate_lock_derivation(FORMAL_LOCK.read_bytes(), DERIVED_LOCK.read_bytes())


class RuntimePreparationControllerV1Tests(unittest.TestCase):
    maxDiff = None

    def test_01_exact7_inventory_and_checker_exact5_unchanged(self) -> None:
        exact7 = (
            "ai/configs/emlis_nls_v3_s11_g4b_runtime_preparation_exact5_lock_v1.json",
            "ai/tools/emlis_nls_v3_s11_g4b_runtime_preparation_contract_v1.py",
            "ai/tools/emlis_nls_v3_s11_g4b_runtime_acquisition_v1.py",
            "ai/tools/emlis_nls_v3_s11_g4b_runtime_materialization_v1.py",
            "ai/tools/emlis_nls_v3_s11_g4b_runtime_admission_bridge_v1.py",
            "ai/tools/emlis_nls_v3_s11_g4b_runtime_preparation_controller_v1.py",
            "ai/tests/test_emlis_nls_v3_s11_g4b_runtime_preparation_controller_v1.py",
        )
        self.assertEqual(len(exact7), 7)
        self.assertTrue(all((REPO_ROOT / item).is_file() for item in exact7))
        protected = {
            "ai/tools/emlis_nls_v3_s11_g4b_runtime_admission_contract_v1.py": "cb2fb32912baee32a6d40f2791f68c61eeaa39c4e351d5a7cfbd52319dd01ea4",
            "ai/tools/emlis_nls_v3_s11_g4b_runtime_admission_checker_v1.py": "2fc106423c3aaae3ef26c4a4592d7a377efd2e214f03924f47a6055eabaf8c2a",
            "ai/tools/emlis_nls_v3_s11_g4b_runtime_admission_owner_v1.py": "065a8f6d76391a0499a6caf7a2a8e1e4b57ab22a30b2274de293722e901b33a4",
            "ai/tools/emlis_nls_v3_s11_g4b_runtime_admission_independent_v1.py": "0996a185160c03a8cedde7aa43e45310d40964ae30669e057030a31969e2435a",
            "ai/tests/test_emlis_nls_v3_s11_g4b_runtime_admission_checker_v1.py": "051d027e47a1ea734026a4e4f8456605be248efedb126e4a72d1bf76ced78e55",
        }
        self.assertEqual({name: _sha((REPO_ROOT / name).read_bytes()) for name in protected}, protected)

    def test_02_import_dag_allowlist_forbidden_imports_and_exact18_ast(self) -> None:
        modules = {
            "emlis_nls_v3_s11_g4b_runtime_preparation_contract_v1.py": set(),
            "emlis_nls_v3_s11_g4b_runtime_acquisition_v1.py": {
                "ai.tools.emlis_nls_v3_s11_g4b_runtime_preparation_contract_v1"
            },
            "emlis_nls_v3_s11_g4b_runtime_materialization_v1.py": {
                "ai.tools.emlis_nls_v3_s11_g4b_runtime_preparation_contract_v1"
            },
            "emlis_nls_v3_s11_g4b_runtime_admission_bridge_v1.py": {
                "ai.tools.emlis_nls_v3_s11_g4b_runtime_preparation_contract_v1",
                "ai.tools.emlis_nls_v3_s11_g4b_runtime_admission_contract_v1",
            },
            "emlis_nls_v3_s11_g4b_runtime_preparation_controller_v1.py": {
                "ai.tools.emlis_nls_v3_s11_g4b_runtime_preparation_contract_v1",
                "ai.tools.emlis_nls_v3_s11_g4b_runtime_acquisition_v1",
                "ai.tools.emlis_nls_v3_s11_g4b_runtime_materialization_v1",
                "ai.tools.emlis_nls_v3_s11_g4b_runtime_admission_bridge_v1",
            },
        }
        forbidden_roots = {"pip", "requests", "socket", "http", "urllib.request"}
        for name, expected_project in modules.items():
            tree = ast.parse((TOOLS / name).read_text(encoding="utf-8"))
            imported = {
                node.module
                for node in ast.walk(tree)
                if isinstance(node, ast.ImportFrom) and node.module is not None
            }
            imported.update(
                alias.name for node in ast.walk(tree) if isinstance(node, ast.Import) for alias in node.names
            )
            self.assertEqual({item for item in imported if item.startswith("ai.")}, expected_project)
            self.assertFalse(any(item in forbidden_roots for item in imported))
        own_tree = ast.parse(Path(__file__).read_text(encoding="utf-8"))
        methods = sorted(
            node.name for node in ast.walk(own_tree)
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name.startswith("test_")
        )
        self.assertEqual(methods, [f"test_{index:02d}_{suffix}" for index, suffix in (
            (1, "exact7_inventory_and_checker_exact5_unchanged"),
            (2, "import_dag_allowlist_forbidden_imports_and_exact18_ast"),
            (3, "full46_to_exact5_canonical_derivation"),
            (4, "strict_json_rejects_duplicate_bom_cr_non_nfc_and_noncanonical"),
            (5, "requirements_bytes_and_fixed_identities"),
            (6, "official_pypi_exact2_host_policy"),
            (7, "path20_distinct19_private18"),
            (8, "preactivation_head_identity_and_effect_zero_validation"),
            (9, "descriptor_v2_fd9_capture_p3_close_and_transport_redaction"),
            (10, "acquisition_argv_exact12_environment_and_single_success_child"),
            (11, "acquisition_rejection_timeout_hash_failure_consumed_no_retry"),
            (12, "wheel_metadata_record_and_zip_safety"),
            (13, "in_process_venv_and_offline_install_network_zero"),
            (14, "installed_closure_full_root_and_partial_cleanup"),
            (15, "checker_request_preserves_full46_and_composite_exact25"),
            (16, "conditional_exact11_ledger_schema_and_pinned_p5_edge"),
            (17, "option_b_lifecycle_cleanup_seal_and_post_cleanup_exact31"),
            (18, "official_cli_exact31_durable_exact17_and_body_free_result"),
        )])
        self.assertEqual(contract.__all__, (
            "PreparationViolation", "PreparationContractV1", "canonical_json_bytes",
            "canonical_file_bytes", "canonical_sha256", "strict_json_from_bytes",
            "validate_lock_derivation", "derive_requirements_bytes",
            "validate_stable_authority_approval", "validate_execution_request",
            "validate_path_plan", "validate_public_result",
            "validate_durable_publication_transition",
        ))
        self.assertEqual(acquisition.__all__, ("capture_transport_binding_at_start", "acquire_once"))
        self.assertEqual(materialization.__all__, ("materialize_once",))
        self.assertEqual(bridge.__all__, ("run_admission_once",))
        self.assertEqual(controller.__all__, ("main",))

    def test_03_full46_to_exact5_canonical_derivation(self) -> None:
        lock = _validated_lock()
        self.assertEqual(_sha(FORMAL_LOCK.read_bytes()), contract.PreparationContractV1.FORMAL_LOCK_RAW_SHA256)
        self.assertEqual(_sha(DERIVED_LOCK.read_bytes()), contract.PreparationContractV1.DERIVED_LOCK_RAW_SHA256)
        self.assertEqual(lock["root_requirements"], ["pytest==8.4.1"])
        self.assertEqual(lock["root_imports"], ["pytest"])
        rows = lock["distributions"]
        self.assertEqual([row["normalized_distribution_name"] for row in rows], list(contract.PreparationContractV1.EXACT5_NAMES))
        self.assertEqual(rows[-1]["selected_dependency_names"], ["iniconfig", "packaging", "pluggy", "pygments"])
        self.assertTrue(all(not row["selected_dependency_names"] for row in rows[:-1]))

    def test_04_strict_json_rejects_duplicate_bom_cr_non_nfc_and_noncanonical(self) -> None:
        invalid = (
            b'{"a":1,"a":2}', b'\xef\xbb\xbf{"a":1}', b'{"a":1}\r',
            '{"x":"e\u0301"}'.encode("utf-8"), b'{"b":1, "a":2}', b'{"a":1.0}',
        )
        for payload in invalid:
            with self.subTest(payload=payload), self.assertRaises(contract.PreparationViolation):
                contract.strict_json_from_bytes(payload)
        with self.assertRaises(contract.PreparationViolation):
            contract.strict_json_from_bytes(b'{"a":1}\n\n', require_final_lf=True)
        self.assertEqual(contract.strict_json_from_bytes(b'{"a":1}\n', require_final_lf=True), {"a": 1})
        with mock.patch.object(bridge, "_read_regular", return_value=b'{"a":1}'):
            with self.assertRaises(contract.PreparationViolation):
                bridge._load_private_json("/private/evidence.json")
        with mock.patch.object(bridge, "_read_regular", return_value=b'{"a":1}\n'):
            self.assertEqual(bridge._load_private_json("/private/evidence.json")[0], {"a": 1})

    def test_05_requirements_bytes_and_fixed_identities(self) -> None:
        lock = _validated_lock()
        requirements = contract.derive_requirements_bytes(lock)
        self.assertEqual(len(requirements), 473)
        self.assertEqual(requirements.count(b"\n"), 5)
        self.assertTrue(requirements.endswith(b"\n"))
        self.assertEqual(_sha(requirements), contract.PreparationContractV1.REQUIREMENTS_SHA256)
        self.assertEqual(_sha(DERIVED_LOCK.read_bytes()[:-1]), contract.PreparationContractV1.DERIVED_LOCK_BODY_SHA256)
        self.assertEqual(bridge._git_blob_oid(DERIVED_LOCK.read_bytes()), contract.PreparationContractV1.DERIVED_LOCK_GIT_BLOB)

    def test_06_official_pypi_exact2_host_policy(self) -> None:
        c = contract.PreparationContractV1
        self.assertEqual(c.PRIMARY_INDEX_URL, "https://pypi.org/simple/")
        self.assertEqual(c.ALLOWED_HOSTS, ("files.pythonhosted.org", "pypi.org"))
        argv = acquisition._acquisition_argv(_execution_request())
        self.assertEqual(argv.count("--index-url"), 1)
        self.assertEqual(argv[argv.index("--index-url") + 1], c.PRIMARY_INDEX_URL)
        for forbidden in ("--extra-index-url", "--find-links", "--trusted-host", "--no-binary"):
            self.assertNotIn(forbidden, argv)
        for required in ("--require-hashes", "--only-binary=:all:", "--no-deps", "--no-cache-dir"):
            self.assertIn(required, argv)

    def test_07_path20_distinct19_private18(self) -> None:
        plan = contract.validate_path_plan(_path_plan())
        self.assertEqual(len(plan), 20)
        self.assertEqual(len(set(plan.values())), 19)
        self.assertEqual(plan["controller_test_cwd"], plan["checker_test_cwd"])
        private = [value for role, value in plan.items() if role not in ("controller_test_cwd", "checker_test_cwd")]
        self.assertEqual(len(private), 18)
        self.assertTrue(all(value == plan["authority_root"] or value.startswith(plan["authority_root"] + "/") for value in private))
        bad = dict(plan)
        bad["wheel_root"] = bad["runtime_root"]
        with self.assertRaises(contract.PreparationViolation):
            contract.validate_path_plan(bad)

    def test_08_preactivation_head_identity_and_effect_zero_validation(self) -> None:
        request = _execution_request()
        with mock.patch("builtins.open", side_effect=AssertionError("filesystem effect")), mock.patch(
            "subprocess.Popen", side_effect=AssertionError("process effect")
        ):
            self.assertEqual(contract.validate_execution_request(request), request)
        for path, replacement in (
            (("expected_git", "mashos_api_commit"), "x" * 40),
            (("control_runtime", "python_version"), "3.12.12"),
            (("control_runtime", "pip_runner_sha256"), "0" * 64),
        ):
            bad = copy.deepcopy(request)
            bad[path[0]][path[1]] = replacement
            with self.assertRaises(contract.PreparationViolation):
                contract.validate_execution_request(bad)
        unknown = copy.deepcopy(request)
        unknown["unapproved_extension"] = False
        with self.assertRaises(contract.PreparationViolation):
            contract.validate_execution_request(unknown)
        self.assertEqual(
            contract.PreparationContractV1.COMPOSITE_BINDING_SCHEMA,
            "emlis.nls_v3.s11.g4b.runtime_preparation.composite_binding.v1",
        )
        self.assertEqual(
            contract.PreparationContractV1.PRIVATE_HANDOFF_SCHEMA,
            "emlis.nls_v3.s11.g4b.runtime_preparation.private_handoff.v1",
        )

        with tempfile.TemporaryDirectory() as temporary:
            repo = Path(temporary).resolve() / "packed-clean-repo"
            git_dir = repo / ".git"
            pack_dir = git_dir / "objects" / "pack"
            pack_dir.mkdir(parents=True)
            tracked = repo / "tracked.txt"
            tracked_payload = b"tracked synthetic body\n"
            tracked.write_bytes(tracked_payload)

            blob_object = f"blob {len(tracked_payload)}\0".encode("ascii") + tracked_payload
            blob_oid = hashlib.sha1(blob_object).digest()
            path_bytes = b"tracked.txt"
            tree_body = b"100644 " + path_bytes + b"\0" + blob_oid
            tree_object = f"tree {len(tree_body)}\0".encode("ascii") + tree_body
            tree_oid = hashlib.sha1(tree_object).hexdigest()
            commit_body = f"tree {tree_oid}\n\nsynthetic packed commit\n".encode("ascii")
            commit_object = f"commit {len(commit_body)}\0".encode("ascii") + commit_body
            commit_oid = hashlib.sha1(commit_object).hexdigest()

            (git_dir / "HEAD").write_bytes(b"ref: refs/heads/main\n")
            (git_dir / "packed-refs").write_bytes(
                f"# pack-refs with: sorted\n{commit_oid} refs/heads/main\n".encode("ascii")
            )
            index_entry = (
                controller.struct.pack(">10I", 0, 0, 0, 0, 0, 0, 0o100644, 0, 0, len(tracked_payload))
                + blob_oid
                + controller.struct.pack(">H", len(path_bytes))
                + path_bytes
                + b"\0"
            )
            index_entry += b"\0" * ((-len(index_entry)) % 8)
            index_body = b"DIRC" + controller.struct.pack(">II", 2, 1) + index_entry
            (git_dir / "index").write_bytes(index_body + hashlib.sha1(index_body).digest())

            remaining = len(commit_body) >> 4
            first = (1 << 4) | (len(commit_body) & 0x0F)
            if remaining:
                first |= 0x80
            object_header = bytearray((first,))
            while remaining:
                current = remaining & 0x7F
                remaining >>= 7
                if remaining:
                    current |= 0x80
                object_header.append(current)
            packed_entry = bytes(object_header) + controller.zlib.compress(commit_body)
            pack_without_checksum = b"PACK" + controller.struct.pack(">II", 2, 1) + packed_entry
            pack_checksum = hashlib.sha1(pack_without_checksum).digest()
            oid_bytes = bytes.fromhex(commit_oid)
            fanout = [0 if slot < oid_bytes[0] else 1 for slot in range(256)]
            index_without_checksum = (
                b"\xfftOc"
                + controller.struct.pack(">I", 2)
                + controller.struct.pack(">256I", *fanout)
                + oid_bytes
                + controller.struct.pack(">I", controller.zlib.crc32(packed_entry) & 0xFFFFFFFF)
                + controller.struct.pack(">I", 12)
                + pack_checksum
            )
            (pack_dir / "pack-synthetic.pack").write_bytes(pack_without_checksum + pack_checksum)
            (pack_dir / "pack-synthetic.idx").write_bytes(
                index_without_checksum + hashlib.sha1(index_without_checksum).digest()
            )

            self.assertEqual(controller._actual_git_head_tree(repo.as_posix()), (commit_oid, tree_oid))
            tracked.write_bytes(b"tracked content drift\n")
            with self.assertRaises(contract.PreparationViolation):
                controller._actual_git_head_tree(repo.as_posix())
            tracked.write_bytes(tracked_payload)
            (repo / "untracked.txt").write_bytes(b"untracked\n")
            with self.assertRaises(contract.PreparationViolation):
                controller._actual_git_head_tree(repo.as_posix())

    def test_09_descriptor_v2_fd9_capture_p3_close_and_transport_redaction(self) -> None:
        request = _execution_request()
        ca_raw = b"PRIVATE CA BYTES"
        observed = types.SimpleNamespace(
            st_dev=1, st_ino=2, st_mode=stat.S_IFREG | 0o400, st_nlink=1,
            st_uid=1, st_gid=1, st_size=len(ca_raw), st_mtime_ns=3,
        )
        request["private_transport"]["expected_ca_raw_sha256"] = _sha(ca_raw)
        online, _offline = acquisition._literal_environments(request)
        stable = {
            "schema_version": contract.PreparationContractV1.TRANSPORT_BINDING_SCHEMA,
            "proxy_url": "https://proxy.private:8443", "proxy_scheme": "https",
            "proxy_host": "proxy.private", "proxy_port": 8443,
            "proxy_userinfo_present": False, "ca_locator": "/private/work-ca.pem",
            "ca_stat_tuple": {key: getattr(observed, key) for key in (
                "st_dev", "st_ino", "st_mode", "st_nlink", "st_uid", "st_gid", "st_size", "st_mtime_ns"
            )},
            "ca_raw_sha256": _sha(ca_raw), "tls_verification": True,
            "normalized_child_environment_sha256": contract.canonical_sha256(online),
            "locator_published": False,
        }
        stable["ca_stat_tuple"]["st_mode"] = 0o400
        request["private_transport"]["expected_stable_projection_sha256"] = contract.canonical_sha256(stable)
        with mock.patch.object(acquisition, "_read_regular_nofollow", return_value=(ca_raw, observed)), mock.patch.object(
            acquisition.os, "geteuid", return_value=2
        ), mock.patch.object(acquisition.time, "monotonic_ns", side_effect=(10, 20, 30)):
            records = [acquisition._transport_record(request, stage) for stage in ("B0", "B1", "B2")]
        self.assertEqual([row["stage"] for row in records], ["B0", "B1", "B2"])
        self.assertEqual(len({row["binding_sha256"] for row in records}), 1)
        state = {"fd": 7, "path": "/private/binding.jsonl", "records": records, "record_lines": [b"x\n"] * 3}
        with mock.patch.object(acquisition, "_append_record"), mock.patch.object(acquisition.os, "fchmod") as chmod, mock.patch.object(
            acquisition.os, "fsync"
        ), mock.patch.object(acquisition.os, "close"), mock.patch.object(acquisition.os, "open", return_value=8), mock.patch.object(
            acquisition, "_read_regular_nofollow", return_value=(b"sealed", observed)
        ):
            acquisition._seal_transport(state, full_match=True)
        chmod.assert_called_once_with(7, 0o400)
        self.assertEqual(state["fd"], -1)

        # Portable P2 freezes the descriptor contract and lifecycle with OS
        # surfaces mocked.  It deliberately makes no actual-DAC claim; that
        # proof is owned by the separate non-discovered privileged entry.
        attestation_raw = contract.canonical_json_bytes(request["egress_attestation"])
        expected_identity = request["egress_attestation_source"][
            "expected_source_identity"
        ]
        platform_source = types.SimpleNamespace(
            **{key: value for key, value in expected_identity.items() if key != "schema_version"}
        )
        expected_credential = request["egress_attestation_source"][
            "platform_mapping_provenance"
        ]["p1_credential_contract"]

        class FrozenDateTime(acquisition._datetime.datetime):
            @classmethod
            def now(cls, tz: object = None) -> object:
                return cls(
                    2026, 8, 12, 0, 5, 0,
                    tzinfo=acquisition._datetime.timezone.utc,
                )

        closed: set[int] = set()

        def portable_fcntl(fd: int, command: int, argument: int | None = None) -> int:
            if command == fcntl.F_DUPFD_CLOEXEC:
                self.assertEqual((fd, argument), (9, 10))
                return 11
            if command == fcntl.F_GETFD:
                if fd in closed:
                    raise OSError(errno.EBADF, "closed")
                return fcntl.FD_CLOEXEC if fd == 11 else 0
            if command == fcntl.F_GETFL:
                return os.O_RDONLY
            raise AssertionError("unapproved fcntl command")

        def portable_close(fd: int) -> None:
            self.assertNotIn(fd, closed)
            closed.add(fd)

        def portable_pread(_fd: int, count: int, offset: int) -> bytes:
            return attestation_raw[offset : offset + count]

        with mock.patch.object(
            acquisition.fcntl, "fcntl", side_effect=portable_fcntl
        ), mock.patch.object(
            acquisition.os, "fstat", return_value=platform_source
        ), mock.patch.object(
            acquisition.os, "pread", side_effect=portable_pread
        ), mock.patch.object(
            acquisition.os, "close", side_effect=portable_close
        ), mock.patch.object(
            acquisition.os, "get_inheritable", return_value=False
        ), mock.patch.object(
            acquisition, "_credential_observation", return_value=expected_credential
        ), mock.patch.object(
            acquisition._datetime, "datetime", FrozenDateTime
        ):
            source_state = acquisition._capture_descriptor_source(request)
            self.assertIn(9, closed)
            self.assertEqual(source_state["source_owned_fd"], 11)
            self.assertEqual(source_state["source_rows"][0]["stage"], "P1_ENTRY")
            p3_row, p3_sha = acquisition._observe_and_close_descriptor_before_p3(
                request, source_state
            )
        self.assertEqual(p3_row["stage"], "P3_PRELAUNCH")
        self.assertEqual(p3_sha, request["egress_attestation_sha256"])
        self.assertEqual(source_state["source_descriptor_state"], "CLOSED_BEFORE_P3")
        self.assertNotIn("source_owned_fd", source_state)
        self.assertIn(11, closed)
        self.assertNotIn("private_locator", request["egress_attestation_source"])
        self.assertNotIn(b"/platform/", contract.canonical_json_bytes(p3_row))
        self.assertIn(
            "_validate_control_runtime_actual(request)",
            (TOOLS / "emlis_nls_v3_s11_g4b_runtime_acquisition_v1.py").read_text(
                encoding="utf-8"
            ),
        )

        # A failure after B0 but before acquire_once must seal one failure
        # summary, relinquish the descriptor, and be idempotent in finally.
        with tempfile.TemporaryDirectory() as temporary:
            abort_request = _execution_request()
            binding_path = Path(temporary) / "binding.jsonl"
            abort_request["path_plan"][
                "private_transport_binding_observation"
            ] = binding_path.as_posix()
            b0 = {"binding_sha256": "a" * 64}
            b0_raw = contract.canonical_json_bytes(b0) + b"\n"
            fd = os.open(binding_path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
            acquisition._write_all(fd, b0_raw)
            os.fsync(fd)
            key = acquisition._state_key(abort_request)
            acquisition._ACTIVE_TRANSPORT[key] = {
                "fd": fd,
                "path": binding_path.as_posix(),
                "records": [b0],
                "record_lines": [b0_raw],
                "source_rows": [],
            }
            sealed_sha256 = acquisition._abort_transport_binding(abort_request)
            self.assertNotIn(key, acquisition._ACTIVE_TRANSPORT)
            self.assertIsNone(acquisition._abort_transport_binding(abort_request))
            sealed_raw = binding_path.read_bytes()
            self.assertEqual(sealed_sha256, _sha(sealed_raw))
            self.assertEqual(stat.S_IMODE(binding_path.stat().st_mode), 0o400)
            lines = sealed_raw.splitlines()
            self.assertEqual(len(lines), 2)
            summary = contract.strict_json_from_bytes(lines[1], require_final_lf=False)
            self.assertEqual(summary["record_count"], 1)
            self.assertFalse(summary["stable_projection_full_match"])

        # The portable suite freezes the separate privileged-entry contract
        # without claiming to execute its root boundary.  In particular, the
        # focused test is not part of its own loader manifest.
        self.assertEqual(len(_PRIVILEGED_MANIFEST), 2)
        self.assertEqual(
            [row[0] for row in _PRIVILEGED_MANIFEST],
            [
                "ai.tools.emlis_nls_v3_s11_g4b_runtime_preparation_contract_v1",
                "ai.tools.emlis_nls_v3_s11_g4b_runtime_acquisition_v1",
            ],
        )
        self.assertNotIn(
            "test_emlis_nls_v3_s11_g4b_runtime_preparation_controller_v1",
            _PRIVILEGED_BOOTSTRAP_SOURCE,
        )
        self.assertNotIn("resolve(", _PRIVILEGED_BOOTSTRAP_SOURCE)
        self.assertNotIn("realpath", _PRIVILEGED_BOOTSTRAP_SOURCE)
        self.assertNotIn("abspath", _PRIVILEGED_BOOTSTRAP_SOURCE)
        self.assertNotIn("getcwd", _PRIVILEGED_BOOTSTRAP_SOURCE)
        self.assertIsInstance(ast.parse(_PRIVILEGED_BOOTSTRAP_SOURCE), ast.Module)
        self.assertEqual(len(_PRIVILEGED_SAFE_ERRNOS), 17)
        self.assertEqual(len(_PRIVILEGED_STAGES), 9)
        self.assertEqual(len(_PRIVILEGED_INTERNAL_REASONS), 6)
        self.assertEqual(len(_PRIVILEGED_REASON_CLASSES), 5)

        repo_fd = os.open(
            REPO_ROOT,
            os.O_RDONLY | os.O_DIRECTORY | getattr(os, "O_CLOEXEC", 0)
            | getattr(os, "O_NOFOLLOW", 0),
        )
        try:
            rows = _privileged_manifest_rows(repo_fd)
        finally:
            closing = repo_fd
            repo_fd = -1
            _privileged_close_once(closing)
        self.assertEqual(
            [(row["module"], row["relative_path"]) for row in rows],
            [(row[0], row[1]) for row in _PRIVILEGED_MANIFEST],
        )

        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "one" / "two").mkdir(parents=True)
            payload = b"bounded manifest source\n"
            (root / "one" / "two" / "module.py").write_bytes(payload)
            root_fd = os.open(
                root,
                os.O_RDONLY | os.O_DIRECTORY | getattr(os, "O_CLOEXEC", 0)
                | getattr(os, "O_NOFOLLOW", 0),
            )
            try:
                self.assertEqual(
                    _privileged_read_relative(
                        root_fd,
                        "one/two/module.py",
                        len(payload),
                        _sha(payload),
                    ),
                    payload,
                )
                with self.assertRaises(RuntimeError):
                    _privileged_read_relative(
                        root_fd,
                        "one/two/module.py",
                        len(payload),
                        "0" * 64,
                    )
                os.symlink("two", root / "one" / "linked")
                with self.assertRaises(OSError):
                    _privileged_read_relative(
                        root_fd,
                        "one/linked/module.py",
                        len(payload),
                        _sha(payload),
                    )
            finally:
                closing = root_fd
                root_fd = -1
                _privileged_close_once(closing)

        captured_records: list[bytes] = []

        def capture_record(fd: int, payload: bytes) -> int:
            self.assertEqual(fd, 2)
            captured_records.append(payload)
            return len(payload)

        with mock.patch.object(os, "write", side_effect=capture_record):
            _privileged_emit_event("EXECVE_REQUESTED", 1)
            _privileged_emit_diagnostic(
                stage="PRE_DROP_CWD_AND_FD9_SETUP",
                reason_class="WORK_PRIVILEGE_OR_OS_SURFACE",
                error=OSError(errno.EACCES, "private locator must not escape"),
                internal_reason=None,
                execve_request_count=0,
                postexec_entry_count=0,
                child_exit_class="CHILD_NONZERO",
            )
        self.assertEqual(len(captured_records), 2)
        for payload in captured_records:
            self.assertLessEqual(len(payload), _PRIVILEGED_RECORD_LIMIT)
            self.assertTrue(payload.startswith(_PRIVILEGED_SENTINEL))
            self.assertNotIn(b"private locator", payload)
            parsed = contract.strict_json_from_bytes(
                payload[len(_PRIVILEGED_SENTINEL):], require_final_lf=True
            )
            self.assertIn(parsed["schema_version"], {
                _PRIVILEGED_EVENT_SCHEMA,
                _PRIVILEGED_DIAGNOSTIC_SCHEMA,
            })

    def _invoke_acquire(
        self,
        process: object,
        *,
        wheel_error: Exception | None = None,
        capture_error: Exception | None = None,
    ) -> tuple[object, mock.Mock]:
        request = _execution_request()
        lock = _validated_lock()
        b0 = {"binding_sha256": "4" * 64}
        key = (request["authority_id"], request["observation_session_id"], request["path_plan"]["private_transport_binding_observation"])
        acquisition._ACTIVE_TRANSPORT[key] = {"fd": 7, "path": key[2], "records": [b0], "record_lines": [], "source_rows": []}
        popen = mock.Mock(return_value=process)
        accepted = [{"wheel_filename": row["wheel_filename"], "wheel_sha256": row["wheel_sha256"]} for row in lock["distributions"]]
        wheel_side_effect = wheel_error if wheel_error is not None else None
        with mock.patch.object(acquisition, "validate_execution_request", side_effect=lambda value: value), mock.patch.object(
            acquisition, "_transport_record", side_effect=({"binding_sha256": "4" * 64}, {"binding_sha256": "4" * 64})
        ), mock.patch.object(acquisition, "_append_record"), mock.patch.object(
            acquisition,
            "_observe_and_close_descriptor_before_p3",
            return_value=({"stage": "P3_PRELAUNCH"}, "5" * 64),
        ), mock.patch.object(acquisition, "_exclusive_file"), mock.patch.object(acquisition.os, "mkdir"), mock.patch.object(
            acquisition, "_seal_transport", return_value="6" * 64
        ), mock.patch.object(acquisition.subprocess, "Popen", popen), mock.patch.object(
            acquisition, "_capture_child", side_effect=capture_error,
            return_value=(b"ok", b"")
        ), mock.patch.object(
            acquisition, "_validate_wheels", side_effect=wheel_side_effect, return_value=accepted
        ):
            return acquisition.acquire_once(request, lock, b0), popen

    def test_10_acquisition_argv_exact12_environment_and_single_success_child(self) -> None:
        process = mock.Mock(returncode=0)
        process.communicate.return_value = (b"ok", b"")
        observation, popen = self._invoke_acquire(process)
        self.assertEqual(popen.call_count, 1)
        kwargs = popen.call_args.kwargs
        self.assertFalse(kwargs["shell"])
        self.assertFalse(kwargs["text"])
        self.assertTrue(kwargs["close_fds"])
        self.assertEqual(kwargs["pass_fds"], ())
        self.assertTrue(kwargs["start_new_session"])
        self.assertEqual(len(kwargs["env"]), 12)
        self.assertEqual(set(kwargs["env"]), {
            "HTTPS_PROXY", "LANG", "LC_ALL", "NETRC", "PIP_CONFIG_FILE",
            "PYTHONDONTWRITEBYTECODE", "PYTHONNOUSERSITE", "REQUESTS_CA_BUNDLE",
            "SSL_CERT_FILE", "TEMP", "TMP", "TMPDIR",
        })
        self.assertTrue(observation["consumed"])
        self.assertEqual(len({key: value for key, value in observation.items() if not key.startswith("_")}), 18)
        self.assertEqual(
            set(observation["_process_evidence"]),
            {
                "pid", "returncode", "executable_sha256", "argv_sha256",
                "environment_sha256", "cwd_binding_sha256", "stdout_sha256",
                "stdout_bytes", "stderr_sha256", "stderr_bytes",
                "termination_state",
            },
        )

        # Regression: the stream-reader default is 1 MiB, while a locked wheel
        # is explicitly allowed through the contract's 16 MiB raw limit.
        with tempfile.TemporaryDirectory() as temporary:
            wheel_root = Path(temporary)
            payloads = {
                "package0-1-py3-none-any.whl": b"L" * (1_048_576 + 1),
                "package1-1-py3-none-any.whl": b"1",
                "package2-1-py3-none-any.whl": b"2",
                "package3-1-py3-none-any.whl": b"3",
                "package4-1-py3-none-any.whl": b"4",
            }
            for filename, payload in payloads.items():
                (wheel_root / filename).write_bytes(payload)
            expected_rows = [
                {"wheel_filename": filename, "wheel_sha256": _sha(payloads[filename])}
                for filename in sorted(payloads)
            ]
            synthetic_lock = {"distributions": expected_rows}
            with mock.patch.object(
                contract.PreparationContractV1,
                "ACCEPTED_WHEEL_MANIFEST_SHA256",
                contract.canonical_sha256(expected_rows),
            ):
                self.assertEqual(
                    acquisition._validate_wheels(wheel_root.as_posix(), synthetic_lock),
                    expected_rows,
                )

    def test_11_acquisition_rejection_timeout_hash_failure_consumed_no_retry(self) -> None:
        failures: list[tuple[object, Exception | None, Exception | None]] = []
        rejected = mock.Mock(side_effect=OSError("reject"))
        process_timeout = mock.Mock(returncode=None)
        timeout_error = contract.PreparationViolation(
            "ACQUISITION_PROCESS_INVALID", "timeout"
        )
        timeout_error.consumed = True
        failures.append((rejected, None, None))
        failures.append((mock.Mock(return_value=process_timeout), timeout_error, None))
        hash_process = mock.Mock(returncode=0)
        failures.append((
            mock.Mock(return_value=hash_process),
            None,
            contract.PreparationViolation("ACQUIRED_WHEEL_SET_INVALID", "hash"),
        ))
        for popen_behavior, capture_error, wheel_error in failures:
            request = _execution_request()
            lock = _validated_lock()
            b0 = {"binding_sha256": "4" * 64}
            key = (request["authority_id"], request["observation_session_id"], request["path_plan"]["private_transport_binding_observation"])
            acquisition._ACTIVE_TRANSPORT[key] = {"fd": 7, "path": key[2], "records": [b0], "record_lines": [], "source_rows": []}
            accepted = [{"wheel_filename": row["wheel_filename"], "wheel_sha256": row["wheel_sha256"]} for row in lock["distributions"]]
            with mock.patch.object(acquisition, "validate_execution_request", side_effect=lambda value: value), mock.patch.object(
                acquisition, "_transport_record", side_effect=({"binding_sha256": "4" * 64}, {"binding_sha256": "4" * 64})
            ), mock.patch.object(acquisition, "_append_record"), mock.patch.object(
                acquisition,
                "_observe_and_close_descriptor_before_p3",
                return_value=({"stage": "P3_PRELAUNCH"}, "5" * 64),
            ), mock.patch.object(acquisition, "_exclusive_file"), mock.patch.object(acquisition.os, "mkdir"), mock.patch.object(
                acquisition, "_seal_transport", return_value="6" * 64
            ), mock.patch.object(acquisition, "_terminate"), mock.patch.object(
                acquisition.subprocess, "Popen", popen_behavior
            ) as popen, mock.patch.object(
                acquisition, "_capture_child", side_effect=capture_error,
                return_value=(b"", b"")
            ), mock.patch.object(
                acquisition, "_validate_wheels", side_effect=wheel_error,
                return_value=accepted
            ):
                with self.assertRaises(contract.PreparationViolation) as caught:
                    acquisition.acquire_once(request, lock, b0)
            self.assertTrue(getattr(caught.exception, "consumed", False))
            self.assertEqual(popen.call_count, 1)

    def test_12_wheel_metadata_record_and_zip_safety(self) -> None:
        metadata_raw = b"Metadata-Version: 2.1\nName: demo\nVersion: 1.0\n\n"
        module_raw = b"VALUE = 1\n"
        def record_line(name: str, payload: bytes) -> str:
            digest = base64.urlsafe_b64encode(hashlib.sha256(payload).digest()).rstrip(b"=").decode()
            return f"{name},sha256={digest},{len(payload)}\n"
        record_raw = (
            record_line("demo.py", module_raw)
            + record_line("demo-1.0.dist-info/METADATA", metadata_raw)
            + "demo-1.0.dist-info/RECORD,,\n"
        ).encode()
        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as archive:
            archive.writestr("demo.py", module_raw)
            archive.writestr("demo-1.0.dist-info/METADATA", metadata_raw)
            archive.writestr("demo-1.0.dist-info/RECORD", record_raw)
        raw = buffer.getvalue()
        row = {
            "normalized_distribution_name": "demo", "distribution_version": "1.0",
            "wheel_filename": "demo-1.0-py3-none-any.whl", "wheel_sha256": _sha(raw),
            "wheel_record_sha256": _sha(record_raw), "requires_dist": [],
            "top_level_imports": ["demo"],
        }
        observed = types.SimpleNamespace(st_mode=stat.S_IFREG | 0o400, st_nlink=1)
        with mock.patch.object(materialization, "_read_regular", return_value=(raw, observed)):
            self.assertEqual(materialization._wheel_record(row, "/private/demo.whl")["wheel_record_sha256"], _sha(record_raw))
        for unsafe in ("../escape", "/absolute", "a\\b", "a/../b"):
            with self.assertRaises(contract.PreparationViolation):
                materialization._safe_zip_name(unsafe)
        with mock.patch.object(materialization.time, "monotonic_ns", return_value=2):
            with self.assertRaises(contract.PreparationViolation):
                materialization._check_deadline(1)
        source = (
            TOOLS / "emlis_nls_v3_s11_g4b_runtime_materialization_v1.py"
        ).read_text(encoding="utf-8")
        self.assertIn('with archive.open(info, "r") as member', source)
        self.assertIn("wheel member expands beyond declared size", source)

    def test_13_in_process_venv_and_offline_install_network_zero(self) -> None:
        request = _execution_request()
        argv = materialization._offline_argv(request)
        environment = materialization._offline_environment(request)
        self.assertIn("--no-index", argv)
        self.assertEqual(argv.count("--find-links"), 1)
        self.assertEqual(argv[argv.index("--find-links") + 1], request["path_plan"]["wheel_root"])
        self.assertFalse(any("http://" in item or "https://" in item for item in argv))
        self.assertEqual(len(environment), 9)
        self.assertFalse({"HTTPS_PROXY", "HTTP_PROXY", "REQUESTS_CA_BUNDLE", "SSL_CERT_FILE"} & set(environment))
        tree = ast.parse((TOOLS / "emlis_nls_v3_s11_g4b_runtime_materialization_v1.py").read_text(encoding="utf-8"))
        builders = [node for node in ast.walk(tree) if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute) and node.func.attr == "EnvBuilder"]
        self.assertEqual(len(builders), 1)
        keywords = {item.arg: ast.literal_eval(item.value) for item in builders[0].keywords}
        self.assertEqual(keywords["with_pip"], False)
        self.assertEqual(keywords["symlinks"], False)
        source = (
            TOOLS / "emlis_nls_v3_s11_g4b_runtime_materialization_v1.py"
        ).read_text(encoding="utf-8")
        self.assertNotIn("process.communicate(", source)
        self.assertIn("selectors.DefaultSelector()", source)
        self.assertIn("signal.setitimer", source)
        self.assertIn("pass_fds=()", source)
        with tempfile.TemporaryDirectory() as temporary:
            runtime = Path(temporary) / "runtime"
            (runtime / "lib").mkdir(parents=True)
            os.symlink("lib", runtime / "lib64")
            materialization._normalize_cpython_linux_venv_lib64(str(runtime))
            self.assertFalse((runtime / "lib64").exists())
            os.symlink("wrong", runtime / "lib64")
            with self.assertRaises(contract.PreparationViolation):
                materialization._normalize_cpython_linux_venv_lib64(str(runtime))

    def test_14_installed_closure_full_root_and_partial_cleanup(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary) / "runtime"
            root.mkdir()
            (root / "file.txt").write_bytes(b"one")
            first = materialization._full_root_manifest(str(root))
            self.assertEqual(first, materialization._full_root_manifest(str(root)))
            (root / "file.txt").write_bytes(b"two")
            self.assertNotEqual(first, materialization._full_root_manifest(str(root)))
            (root / "bin").mkdir()
            baseline = materialization._fresh_venv_baseline(str(root))
            (root / "bin" / "outside-site-unclaimed").write_bytes(b"injected")
            with self.assertRaisesRegex(
                contract.PreparationViolation, "unclaimed regular file"
            ):
                materialization._verify_runtime_ownership(
                    str(root), baseline, set()
                )
            with self.assertRaises(contract.PreparationViolation):
                materialization._claim_path(str(root), str(root / "site"), "../../escape")
            authority = str(Path(temporary) / "authority")
            Path(authority).mkdir(mode=0o700)
            os.chmod(authority, 0o700)
            plan = _path_plan(authority, "/repo")
            Path(plan["runtime_root"]).mkdir()
            (Path(plan["runtime_root"]) / "partial").write_bytes(b"x")
            rows: list[dict[str, object]] = []
            ledger = mock.Mock()
            state, retention = controller._cleanup({"path_plan": plan}, False, rows, ledger)
            self.assertEqual((state, retention), ("COMPLETE", "EVIDENCE_RETAINED"))
            self.assertFalse(Path(plan["runtime_root"]).exists())
            # A success claim without its runtime and private handoff must not
            # be promoted to CURRENT_SESSION_RETAINED.
            success_state, success_retention = controller._cleanup(
                {"path_plan": plan}, True, rows, ledger
            )
            self.assertEqual(
                (success_state, success_retention),
                ("FAILED", "PARTIAL_PRIVATE_STATE_RETAINED"),
            )
        source = (TOOLS / "emlis_nls_v3_s11_g4b_runtime_materialization_v1.py").read_text(encoding="utf-8")
        self.assertIn("installed_record_closure_sha256", source)
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "one").write_bytes(b"1")
            with mock.patch.object(materialization, "_RUNTIME_FILES", 0):
                with self.assertRaises(contract.PreparationViolation):
                    materialization._full_root_manifest(str(root))
            self.assertEqual(bridge._full_root_manifest(str(root)), materialization._full_root_manifest(str(root)))
            with mock.patch.object(bridge, "_RUNTIME_FILES", 0):
                with self.assertRaises(contract.PreparationViolation):
                    bridge._full_root_manifest(str(root))
            with mock.patch.object(bridge.time, "monotonic_ns", return_value=2):
                with self.assertRaises(contract.PreparationViolation):
                    bridge._full_root_manifest(str(root), 1)

        request = _execution_request()
        lock = _validated_lock()
        accepted = [
            {"wheel_filename": row["wheel_filename"], "wheel_sha256": row["wheel_sha256"]}
            for row in lock["distributions"]
        ]
        online, _offline = acquisition._literal_environments(request)
        observation = {
            "schema_version": contract.PreparationContractV1.ACQUISITION_OBSERVATION_SCHEMA,
            "authority_id": request["authority_id"],
            "observation_session_id": request["observation_session_id"],
            "consumed": True,
            "process_launch_count": 1,
            "argv_sha256": contract.canonical_sha256(acquisition._acquisition_argv(request)),
            "environment_sha256": contract.canonical_sha256(online),
            "egress_attestation_sha256": request["egress_attestation_sha256"],
            "egress_attestation_source_observation_sha256": "1" * 64,
            "transport_b0_sha256": "2" * 64,
            "transport_b1_sha256": "2" * 64,
            "transport_b2_sha256": "2" * 64,
            "returncode": 0,
            "stdout_sha256": "3" * 64,
            "stderr_sha256": "4" * 64,
            "requirements_sha256": contract.PreparationContractV1.REQUIREMENTS_SHA256,
            "accepted_wheel_rows": accepted,
            "accepted_wheel_manifest_sha256": (
                contract.PreparationContractV1.ACCEPTED_WHEEL_MANIFEST_SHA256
            ),
        }
        materialization._validate_acquisition_boundary(request, lock, observation)
        extended = dict(observation)
        extended["unknown"] = True
        with self.assertRaises(contract.PreparationViolation):
            materialization._validate_acquisition_boundary(request, lock, extended)
        self.assertIn("physical - record_self != owned", source)

    def test_15_checker_request_preserves_full46_and_composite_exact25(self) -> None:
        request = _execution_request()
        c = contract.PreparationContractV1
        lock = _validated_lock()
        root = request["path_plan"]["runtime_root"]
        root_sha = checker_contract.runtime_root_locator_sha256(root)
        full_root_sha = "7" * 64
        event_preimage = {
            "schema_version": checker_contract.ContractV1.MATERIALIZATION_ATTESTATION_SCHEMA,
            "authority_id": request["authority_id"], "observation_session_id": request["observation_session_id"],
            "procedure_ids": list(c.PROCEDURE_IDS),
            "fresh_root_nonexistent_before": True, "prior_artifact_reuse_count": 0,
            "root_locator_sha256": root_sha, "expected_full_root_manifest_sha256": full_root_sha,
            "site_packages_relative": c.SITE_PACKAGES_RELATIVE,
            "admitted_executable_relative_path": "bin/python",
        }
        accepted_rows = [
            {"wheel_filename": row["wheel_filename"], "wheel_sha256": row["wheel_sha256"]}
            for row in lock["distributions"]
        ]
        acquisition_observation = {
            "schema_version": c.ACQUISITION_OBSERVATION_SCHEMA,
            "authority_id": request["authority_id"],
            "observation_session_id": request["observation_session_id"],
            "consumed": True,
            "process_launch_count": 1,
            "argv_sha256": "1" * 64,
            "environment_sha256": "2" * 64,
            "egress_attestation_sha256": request["egress_attestation_sha256"],
            "egress_attestation_source_observation_sha256": "3" * 64,
            "transport_b0_sha256": "4" * 64,
            "transport_b1_sha256": "4" * 64,
            "transport_b2_sha256": "4" * 64,
            "returncode": 0,
            "stdout_sha256": "5" * 64,
            "stderr_sha256": "6" * 64,
            "requirements_sha256": c.REQUIREMENTS_SHA256,
            "accepted_wheel_rows": accepted_rows,
            "accepted_wheel_manifest_sha256": c.ACCEPTED_WHEEL_MANIFEST_SHA256,
        }
        self.assertEqual(
            contract._validate_acquisition_observation(request, acquisition_observation),
            acquisition_observation,
        )
        for mutation in ("unknown", "transport", "manifest"):
            bad_acquisition = copy.deepcopy(acquisition_observation)
            if mutation == "unknown":
                bad_acquisition["unapproved_extension"] = False
            elif mutation == "transport":
                bad_acquisition["transport_b2_sha256"] = "9" * 64
            else:
                bad_acquisition["accepted_wheel_rows"].reverse()
            with self.subTest(acquisition_mutation=mutation), self.assertRaises(
                contract.PreparationViolation
            ):
                contract._validate_acquisition_observation(request, bad_acquisition)

        wheel_record_rows = [
            {
                "wheel_filename": row["wheel_filename"],
                "wheel_sha256": row["wheel_sha256"],
                "wheel_record_sha256": row["wheel_record_sha256"],
            }
            for row in lock["distributions"]
        ]
        attestation = {
            "schema_version": c.MATERIALIZATION_ATTESTATION_SCHEMA,
            "authority_id": request["authority_id"],
            "observation_session_id": request["observation_session_id"],
            "event_id": checker_contract.canonical_sha256(event_preimage),
            "procedure_ids": list(c.PROCEDURE_IDS),
            "fresh_root_nonexistent_before": True, "prior_artifact_reuse_count": 0,
            "runtime_root_locator_sha256": root_sha,
            "site_packages_relative": c.SITE_PACKAGES_RELATIVE,
            "derived_lock_raw_sha256": c.DERIVED_LOCK_RAW_SHA256,
            "derived_lock_logical_sha256": c.DERIVED_LOCK_LOGICAL_SHA256,
            "accepted_wheel_manifest_sha256": c.ACCEPTED_WHEEL_MANIFEST_SHA256,
            "wheel_record_rows": wheel_record_rows,
            "wheel_record_manifest_sha256": c.WHEEL_RECORD_MANIFEST_SHA256,
            "distribution_closure_sha256": c.DISTRIBUTION_CLOSURE_SHA256,
            "runtime_executable_locator_sha256": checker_contract.runtime_executable_locator_sha256(
                root + "/bin/python"
            ),
            "resolved_interpreter_sha256": c.EXPECTED_INTERPRETER_SHA256,
            "installed_file_manifest_sha256": checker_contract.ContractV1.INSTALLED_MANIFEST_COMPARATOR_SHA256,
            "full_runtime_root_manifest_sha256": full_root_sha,
            "materialization_process_ledger_sha256": "8" * 64,
            "environment_policy_sha256": c.ENVIRONMENT_POLICY_SHA256,
            "status": "MATERIALIZED_VERIFIED",
        }
        self.assertEqual(
            contract._validate_materialization_attestation(request, attestation), attestation
        )
        for mutation in ("unknown", "event", "wheel_record"):
            bad_materialization = copy.deepcopy(attestation)
            if mutation == "unknown":
                bad_materialization["unapproved_extension"] = False
            elif mutation == "event":
                bad_materialization["event_id"] = "0" * 64
            else:
                bad_materialization["wheel_record_rows"].reverse()
            with self.subTest(materialization_mutation=mutation), self.assertRaises(
                contract.PreparationViolation
            ):
                contract._validate_materialization_attestation(request, bad_materialization)

        checker_request = bridge._checker_request(request, attestation)
        self.assertEqual(checker_request["frozen"]["lock_raw_sha256"], checker_contract.ContractV1.LOCK_RAW_SHA256)
        self.assertEqual(checker_request["frozen"]["lock_logical_sha256"], checker_contract.ContractV1.LOCK_LOGICAL_SHA256)
        self.assertNotEqual(checker_request["frozen"]["lock_logical_sha256"], c.DERIVED_LOCK_LOGICAL_SHA256)
        self.assertEqual(len(c.COMPOSITE_BINDING_KEYS), 25)
        source = (TOOLS / "emlis_nls_v3_s11_g4b_runtime_admission_bridge_v1.py").read_text(encoding="utf-8")
        for field in c.COMPOSITE_BINDING_KEYS:
            self.assertIn(f'"{field}"', source)
        checker_result = {
            "runtime_instance_observation_id": "a" * 64,
            "runtime_readiness_observation_id": "b" * 64,
            "handoff_binding_sha256": "0" * 64,
        }
        observed = types.SimpleNamespace(
            st_dev=11, st_ino=12, st_mode=stat.S_IFREG | 0o500,
            st_nlink=1, st_size=13, st_mtime_ns=14,
        )
        with mock.patch.object(bridge.os, "lstat", return_value=observed), mock.patch.object(
            bridge, "_file_sha256", return_value="c" * 64
        ):
            handoff_preimage = bridge._checker_handoff_preimage(
                request, attestation, checker_result
            )
            self.assertEqual(len(handoff_preimage), 18)
            self.assertEqual(frozenset(handoff_preimage), c.HANDOFF_BINDING_KEYS)
            checker_result["handoff_binding_sha256"] = contract.canonical_sha256(
                handoff_preimage
            )
            bridge._validate_checker_handoff_binding(request, attestation, checker_result)
            checker_result["handoff_binding_sha256"] = "d" * 64
            with self.assertRaises(contract.PreparationViolation):
                bridge._validate_checker_handoff_binding(
                    request, attestation, checker_result
                )

    def test_16_conditional_exact11_ledger_schema_and_pinned_p5_edge(self) -> None:
        self.assertEqual(controller.CONDITIONAL_EXPECTED_LAUNCH_EDGE_TOPOLOGY_EXACT11, contract.PreparationContractV1.CONDITIONAL_LAUNCH_EDGE_TOPOLOGY)
        self.assertEqual(len(controller.CONDITIONAL_EXPECTED_LAUNCH_EDGE_TOPOLOGY_EXACT11), 11)
        self.assertEqual(controller.DIRECT_CHILD_ORDER, (
            "P2_FOCUSED_UNITTEST", "P3_PIP_DOWNLOAD", "P4_CONTROL_PIP_OFFLINE_INSTALL",
            "P6_CHECKER_DEDICATED_TEST", "P7_OFFICIAL_CHECKER",
        ))
        rows: list[dict[str, object]] = []
        controller._append_observation_rows(rows, {
            "argv_sha256": "1" * 64, "environment_sha256": "2" * 64, "returncode": 0,
            "stdout_sha256": "3" * 64, "stderr_sha256": "4" * 64,
        }, {
            "materialization_process_ledger_sha256": "5" * 64,
            "environment_policy_sha256": "6" * 64,
            "resolved_interpreter_sha256": contract.PreparationContractV1.EXPECTED_INTERPRETER_SHA256,
            "runtime_executable_locator_sha256": "7" * 64,
        })
        self.assertEqual(len(rows), 3)
        self.assertTrue(all(tuple(row) == controller.PROCESS_LEDGER_KEYS_EXACT14 for row in rows))
        self.assertEqual(rows[-1]["stage"], "P5_TARGET_INTERPRETER_PIP_REEXEC")
        self.assertEqual(rows[-1]["pid_or_source_edge"], contract.PreparationContractV1.P5_STATIC_PROOF_STATE)
        child_fields = {
            "pid": 123,
            "returncode": 0,
            "stdout": b"",
            "stderr": b"",
            "termination_state": "EXITED",
            "argv_sha256": "1" * 64,
            "environment_sha256": "2" * 64,
            "cwd_binding_sha256": "3" * 64,
            "executable_sha256": "4" * 64,
        }
        p6 = bridge._ChildResult(stage="P6_CHECKER_DEDICATED_TEST", **child_fields)
        p7 = bridge._ChildResult(stage="P7_OFFICIAL_CHECKER", **child_fields)
        failure = contract.PreparationViolation("CHECKER_PROCESS_INVALID", "synthetic")
        self.assertIs(
            bridge._bind_p7_attempt_failure(
                failure, p6, p7, nested_terminal="INTERNAL_FAIL_CLOSED"
            ),
            failure,
        )
        self.assertEqual(failure.checker_execution_attempt_count, 1)
        self.assertEqual(failure.checker_component_status, "STOP")
        self.assertEqual(failure.nested_checker_terminal, "INTERNAL_FAIL_CLOSED")
        self.assertEqual([row["stage"] for row in failure.process_rows], [
            "P6_CHECKER_DEDICATED_TEST", "P7_OFFICIAL_CHECKER",
        ])
        request = _execution_request()
        evidence = {
            "pid": 456, "returncode": 0,
            "executable_sha256": request["control_runtime"]["resolved_interpreter_sha256"],
            "argv_sha256": "1" * 64, "environment_sha256": "2" * 64,
            "cwd_binding_sha256": contract.canonical_sha256({
                "schema_version": "g4b.cwd.binding.v1",
                "cwd": request["path_plan"]["controller_test_cwd"],
            }),
            "stdout_sha256": "3" * 64, "stdout_bytes": 0,
            "stderr_sha256": "4" * 64, "stderr_bytes": 0,
            "termination_state": "EXITED_WITH_PINNED_P5_SOURCE_EDGE",
        }
        projection = materialization._materialization_process_projection(
            request,
            runtime_executable_locator_sha256="5" * 64,
            resolved_interpreter_sha256=contract.PreparationContractV1.EXPECTED_INTERPRETER_SHA256,
            process_evidence=evidence,
        )
        self.assertEqual([row["stage"] for row in projection], [
            "P4_CONTROL_PIP_OFFLINE_INSTALL", "P5_TARGET_INTERPRETER_PIP_REEXEC",
        ])
        self.assertEqual(projection[1], controller._p5_source_edge_row({}, {
            "runtime_executable_locator_sha256": "5" * 64,
            "resolved_interpreter_sha256": contract.PreparationContractV1.EXPECTED_INTERPRETER_SHA256,
        }, projection[0]) | {"sequence": 1})
        self.assertEqual(contract.canonical_sha256(projection), contract.canonical_sha256(copy.deepcopy(projection)))
        bridge_source = (
            TOOLS / "emlis_nls_v3_s11_g4b_runtime_admission_bridge_v1.py"
        ).read_text(encoding="utf-8")
        direct_child = bridge_source[
            bridge_source.index("def _run_direct_child(") :
            bridge_source.index("def _full_root_manifest(")
        ]
        self.assertIn('selector.register(process.stdin, selectors.EVENT_WRITE, "stdin")', direct_child)
        self.assertIn("os.set_blocking(process.stdin.fileno(), False)", direct_child)
        self.assertLess(direct_child.index("deadline = time.monotonic()"), direct_child.index("os.write("))

    def test_17_option_b_lifecycle_cleanup_seal_and_post_cleanup_exact31(self) -> None:
        c = contract.PreparationContractV1
        approval = {
            "schema_version": c.STABLE_AUTHORITY_APPROVAL_SCHEMA, "candidate_id": c.CANDIDATE_ID,
            "approved_candidate_body_sha256": c.APPROVED_CANDIDATE_BODY_SHA256,
            "authority_id": "AUTHORITY_001", "authority_policy_id": c.AUTHORITY_POLICY_ID,
            "acquisition_policy_id": c.ACQUISITION_POLICY_ID, "egress_issuer_class": c.EGRESS_ISSUER_CLASS,
            "egress_issuer_policy_id": c.EGRESS_ISSUER_POLICY_ID, "allowed_scheme": c.ALLOWED_SCHEME,
            "allowed_hosts": list(c.ALLOWED_HOSTS), "acquisition_process_count": 1,
            "attestation_issue_phase": c.ATTESTATION_ISSUE_PHASE,
            "attestation_max_lifetime_seconds": 900,
            "minimum_remaining_lifetime_at_p3_seconds": 330,
            "same_authority_reissue_allowed": False,
        }
        self.assertEqual(contract.validate_stable_authority_approval(approval), approval)
        with tempfile.TemporaryDirectory() as temporary:
            path = str(Path(temporary) / "cleanup-ledger.jsonl")
            ledger = controller._CleanupLedger(path)
            ledger.append("TERMINAL_CLEANUP", "runtime_root", "NOT_CREATED", "NOT_CREATED", "COMPLETE", "ABSENT", SHA256_ZERO)
            digest, raw = ledger.seal()
            self.assertEqual(_sha(raw), digest)
            self.assertEqual(stat.S_IMODE(os.stat(path).st_mode), 0o400)
            with self.assertRaises(contract.PreparationViolation):
                ledger.append("TERMINAL_CLEANUP", "runtime_root", "RETAIN", "PRESENT", "COMPLETE", "RETAINED", SHA256_ZERO)
        main_source = (TOOLS / "emlis_nls_v3_s11_g4b_runtime_preparation_controller_v1.py").read_text(encoding="utf-8")
        start = main_source.index("def _terminalize_started(")
        ordered = [main_source.index(token, start) for token in (
            "_cleanup(", "cleanup_ledger.seal()", "_build_public_result_once(",
            "_seal_terminal_evidence(", "return (",
        )]
        self.assertEqual(ordered, sorted(ordered))
        cleanup_failed_terminal = controller._Terminal(
            primary_terminal=c.PRIMARY_SUCCESS_TERMINAL,
            nested_checker_terminal="RUNTIME_READY_CURRENT_SESSION_STOP",
            consumed=True,
            checker_execution_attempt_count=1,
            checker_component_status="VALID",
            composite_binding_sha256="7" * 64,
            success=True,
        )
        cleanup_failed, _raw, _digest = controller._build_public_result_once(
            _execution_request(), cleanup_failed_terminal, "FAILED",
            "PARTIAL_PRIVATE_STATE_RETAINED",
        )
        self.assertEqual(cleanup_failed["status"], "STOP")
        self.assertEqual(cleanup_failed["primary_terminal"], "INTERNAL_FAIL_CLOSED")
        self.assertEqual(cleanup_failed["checker_component_status"], "VALID")
        self.assertEqual(cleanup_failed["composite_technical_result"], "STOP_CLEANUP_INCOMPLETE")
        self.assertFalse(cleanup_failed["technical_chain_complete"])
        fallback = controller._sanitized_started_fallback("PRIVACY_VIOLATION")
        fallback_value = contract.strict_json_from_bytes(fallback)
        self.assertEqual(len(fallback_value), 31)
        self.assertEqual(fallback_value["status"], "STOP")
        self.assertEqual(fallback_value["primary_terminal"], "PRIVACY_VIOLATION")
        self.assertEqual(fallback_value["cleanup_state"], "UNKNOWN")
        self.assertFalse(fallback_value["technical_chain_complete"])

        with tempfile.TemporaryDirectory() as temporary:
            authority = Path(temporary) / "authority"
            authority.mkdir(mode=0o700)
            os.chmod(authority, 0o700)
            request = _execution_request()
            request["path_plan"] = _path_plan(str(authority), str(REPO_ROOT))
            invalid_role = "private_transport_binding_observation"
            invalid_evidence = Path(request["path_plan"][invalid_role])
            invalid_evidence.write_bytes(b"unsealed")
            os.chmod(invalid_evidence, 0o600)
            invalid_terminal = controller._Terminal(primary_terminal="INTERNAL_FAIL_CLOSED")
            invalid_rows: list[dict[str, object]] = []
            invalid_ledger = mock.Mock()
            cleanup_state, retention_state = controller._cleanup(
                request,
                False,
                invalid_rows,
                invalid_ledger,
                terminal=invalid_terminal,
            )
            self.assertEqual(
                (cleanup_state, retention_state),
                ("FAILED", "PARTIAL_PRIVATE_STATE_RETAINED"),
            )
            ledger_row = next(
                call.args for call in invalid_ledger.append.call_args_list
                if call.args[1] == invalid_role
            )
            self.assertEqual(
                ledger_row[2:6], ("RETAIN", "PRESENT", "FAILED", "RETAINED")
            )
            path_row = next(row for row in invalid_rows if row["role"] == invalid_role)
            self.assertEqual(path_row["result"], "FAILED")
            self.assertEqual(path_row["pre_state"], "PRESENT")
            invalid_result, _invalid_raw, _invalid_sha = controller._build_public_result_once(
                request, invalid_terminal, cleanup_state, retention_state
            )
            self.assertEqual(invalid_result["status"], "STOP")
            self.assertEqual(invalid_result["current_session_runtime_readiness"], "NOT_READY")
            self.assertFalse(invalid_result["technical_chain_complete"])

        with tempfile.TemporaryDirectory() as temporary:
            authority = Path(temporary) / "authority"
            authority.mkdir(mode=0o700)
            request = _execution_request()
            request["path_plan"] = _path_plan(str(authority), str(REPO_ROOT))
            missing_role = "acquisition_observation"
            missing_terminal = controller._Terminal(primary_terminal="INTERNAL_FAIL_CLOSED")
            missing_terminal.retained_raw_sha256[missing_role] = "a" * 64
            missing_rows: list[dict[str, object]] = []
            controller._path_row(
                missing_rows,
                missing_role,
                request["path_plan"][missing_role],
                "CREATE",
                "ABSENT",
                "SEALED_0400",
                "COMPLETE",
            )
            missing_ledger = mock.Mock()
            missing_state, missing_retention = controller._cleanup(
                request,
                False,
                missing_rows,
                missing_ledger,
                terminal=missing_terminal,
            )
            self.assertEqual(
                (missing_state, missing_retention),
                ("FAILED", "PARTIAL_PRIVATE_STATE_RETAINED"),
            )
            missing_row = next(
                call.args for call in missing_ledger.append.call_args_list
                if call.args[1] == missing_role
            )
            self.assertEqual(
                missing_row[2:6],
                ("RETAIN", "EXPECTED_PRESENT", "FAILED", "ABSENT_AFTER_CREATION"),
            )

        with tempfile.TemporaryDirectory() as temporary:
            invalid_authority = Path(temporary) / "invalid-authority"
            invalid_authority.mkdir(mode=0o700)
            os.chmod(invalid_authority, 0o755)
            invalid_request = _execution_request()
            invalid_request["path_plan"] = _path_plan(
                str(invalid_authority), str(REPO_ROOT)
            )
            invalid_state, invalid_retention = controller._cleanup(
                invalid_request,
                False,
                [],
                mock.Mock(),
                terminal=controller._Terminal(primary_terminal="INTERNAL_FAIL_CLOSED"),
            )
            self.assertEqual(
                (invalid_state, invalid_retention),
                ("FAILED", "PARTIAL_PRIVATE_STATE_RETAINED"),
            )

            missing_request = _execution_request()
            missing_request["path_plan"] = _path_plan(
                str(Path(temporary) / "missing-authority"), str(REPO_ROOT)
            )
            missing_state, missing_retention = controller._cleanup(
                missing_request,
                False,
                [],
                mock.Mock(),
                terminal=controller._Terminal(primary_terminal="INTERNAL_FAIL_CLOSED"),
            )
            self.assertEqual(
                (missing_state, missing_retention),
                ("FAILED", "PARTIAL_PRIVATE_STATE_RETAINED"),
            )

    def test_18_official_cli_exact31_durable_exact17_and_body_free_result(self) -> None:
        request = _execution_request()
        terminal = controller._Terminal(
            primary_terminal=contract.PreparationContractV1.PRIMARY_SUCCESS_TERMINAL,
            nested_checker_terminal="HANDOFF_BOUND_CURRENT_SESSION", consumed=True,
            checker_execution_attempt_count=1, checker_component_status="VALID",
            composite_binding_sha256="7" * 64, success=True,
        )
        result, raw, digest = controller._build_public_result_once(
            request, terminal, "COMPLETE", "CURRENT_SESSION_RETAINED"
        )
        self.assertEqual(len(result), 31)
        self.assertEqual(tuple(result), controller.PUBLIC_RESULT_KEYS_EXACT31)
        self.assertEqual(_sha(raw), digest)
        self.assertTrue(result["technical_chain_complete"])
        self.assertFalse(result["gate_c_authorized"])
        self.assertFalse(result["automatic_progression"])
        for private in (
            request["authority_id"], request["observation_session_id"], request["receiver_session_id"],
            request["receiver_nonce"], request["private_transport"]["https_proxy"],
            request["private_transport"]["custom_ca_locator"], request["path_plan"]["runtime_root"],
        ):
            self.assertNotIn(str(private).encode(), raw)
        transition = {
            "schema_version": contract.PreparationContractV1.DURABLE_TRANSITION_SCHEMA,
            "candidate_id": contract.PreparationContractV1.CANDIDATE_ID,
            "authority_context_binding_sha256": result["authority_context_binding_sha256"],
            "session_context_binding_sha256": result["session_context_binding_sha256"],
            "controller_public_result_sha256": digest,
            "terminal_evidence_envelope_sha256": "6" * 64,
            "publication_state": "VERIFIED", "remote_postverify_state": "EXACT_MATCH",
            "durable_work_complete": True, "current_owner_runtime_ready": True,
            "current_owner_gate_b_closed": True, "current_owner_readiness_credit": 1,
            "current_owner_technical_credit": 1, "current_owner_product_credit": 0,
            "current_owner_primary_outcome": "TECHNICAL_CREDIT",
            "publication_staging_cleanup_state": "ABSENT_VERIFIED", "automatic_progression": False,
        }
        self.assertEqual(contract.validate_durable_publication_transition(transition), transition)
        self.assertEqual(controller.__all__, ("main",))
        source = (TOOLS / "emlis_nls_v3_s11_g4b_runtime_preparation_controller_v1.py").read_text(encoding="utf-8")
        self.assertIn('if __name__ == "__main__":', source)
        self.assertIn("_assert_official_cli_context()", source)
        p1_row = {
            "sequence": 0,
            "stage": "P1_CONTROLLER",
            "launch_owner": "ULTRA_KAREN_APPROVED_LIVE_AUTHORITY",
            "executable_sha256": "1" * 64,
            "argv_sha256": "2" * 64,
            "environment_sha256": "3" * 64,
            "cwd_binding_sha256": "4" * 64,
            "pid_or_source_edge": "123",
            "returncode": -1,
            "stdout_sha256": SHA256_ZERO,
            "stdout_bytes": -1,
            "stderr_sha256": SHA256_ZERO,
            "stderr_bytes": -1,
            "termination_state": "TERMINAL_EMIT_PENDING_RETURN_CODE_UNOBSERVED",
        }
        lifecycle_terminal = controller._Terminal(primary_terminal="INTERNAL_FAIL_CLOSED")
        fake_ledger = object()
        with mock.patch.object(
            controller, "_assert_official_cli_context", return_value=str(REPO_ROOT)
        ), mock.patch.object(
            controller, "_read_request", return_value=request
        ), mock.patch.object(
            controller, "_p1_process_row", return_value=p1_row
        ), mock.patch.object(
            controller, "_run_lifecycle", return_value=(lifecycle_terminal, fake_ledger)
        ) as run_lifecycle, mock.patch.object(
            controller, "_terminalize_started", return_value=(2, b"body-free")
        ) as terminalize, mock.patch.object(controller, "_emit_once") as emit:
            self.assertEqual(controller.main(), 2)
            self.assertEqual(run_lifecycle.call_count, 1)
            self.assertEqual(terminalize.call_count, 1)
            emit.assert_called_once_with(b"body-free")

        failed_ledger = mock.Mock()
        failed_ledger.seal.side_effect = OSError("seal failed")
        fatal_terminal = controller._Terminal(primary_terminal="INTERNAL_FAIL_CLOSED")
        with mock.patch.object(
            controller, "_assert_official_cli_context", return_value=str(REPO_ROOT)
        ), mock.patch.object(
            controller, "_read_request", return_value=request
        ), mock.patch.object(
            controller, "_p1_process_row", return_value=p1_row
        ), mock.patch.object(
            controller, "_run_lifecycle", return_value=(fatal_terminal, failed_ledger)
        ), mock.patch.object(
            controller, "_cleanup", return_value=("UNKNOWN", "PARTIAL_PRIVATE_STATE_RETAINED")
        ), mock.patch.object(
            controller, "_build_public_result_once"
        ) as build_result, mock.patch.object(
            controller, "_seal_terminal_evidence"
        ) as seal_evidence, mock.patch.object(controller, "_emit_once") as emit:
            self.assertEqual(controller.main(), 3)
            build_result.assert_not_called()
            seal_evidence.assert_not_called()
            emit.assert_not_called()


class _CapHeader(ctypes.Structure):
    _fields_ = (("version", ctypes.c_uint32), ("pid", ctypes.c_int))


class _CapData(ctypes.Structure):
    _fields_ = (
        ("effective", ctypes.c_uint32),
        ("permitted", ctypes.c_uint32),
        ("inheritable", ctypes.c_uint32),
    )


def _privileged_canonical_bytes(value: object) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8")


def _privileged_emit_event(event_class: str, sequence_number: int) -> None:
    if (event_class, sequence_number) not in {
        ("EXECVE_REQUESTED", 1),
        ("POSTEXEC_ENTERED", 2),
    }:
        raise RuntimeError("event contract")
    row = {
        "schema_version": _PRIVILEGED_EVENT_SCHEMA,
        "event_class": event_class,
        "sequence_number": sequence_number,
    }
    payload = _PRIVILEGED_SENTINEL + _privileged_canonical_bytes(row) + b"\n"
    if len(payload) > _PRIVILEGED_RECORD_LIMIT:
        raise RuntimeError("event bound")
    written = os.write(2, payload)
    if written != len(payload):
        raise RuntimeError("event atomic write")


def _privileged_emit_diagnostic(
    *,
    stage: str,
    reason_class: str,
    error: BaseException | None,
    internal_reason: str | None,
    execve_request_count: int,
    postexec_entry_count: int,
    child_exit_class: str,
) -> None:
    if stage not in _PRIVILEGED_STAGES:
        stage = "EVIDENCE_INSUFFICIENT"
    if reason_class not in _PRIVILEGED_REASON_CLASSES:
        reason_class = "RESULT_TRANSPORT_INDETERMINATE"
    safe_errno: int | None = None
    safe_internal = internal_reason
    if isinstance(error, OSError) and error.errno in _PRIVILEGED_SAFE_ERRNOS:
        safe_errno = error.errno
        safe_internal = None
    elif safe_internal is None:
        safe_internal = (
            "OS_ERROR_OUTSIDE_SAFE_SET"
            if isinstance(error, OSError)
            else "EVENT_OR_RESULT_TRANSPORT_INVALID"
        )
    if safe_internal is not None and safe_internal not in _PRIVILEGED_INTERNAL_REASONS:
        safe_internal = "EVENT_OR_RESULT_TRANSPORT_INVALID"
    row = {
        "schema_version": _PRIVILEGED_DIAGNOSTIC_SCHEMA,
        "terminal_class": "STOP",
        "stage": stage,
        "reason_class": reason_class,
        "safe_errno": safe_errno,
        "safe_internal_reason": safe_internal,
        "execve_request_count": execve_request_count,
        "postexec_entry_count": postexec_entry_count,
        "child_exit_class": child_exit_class,
    }
    if (safe_errno is None) == (safe_internal is None):
        raise RuntimeError("diagnostic reason cardinality")
    payload = _PRIVILEGED_SENTINEL + _privileged_canonical_bytes(row) + b"\n"
    if len(payload) > _PRIVILEGED_RECORD_LIMIT:
        raise RuntimeError("diagnostic bound")
    written = os.write(2, payload)
    if written != len(payload):
        raise RuntimeError("diagnostic atomic write")


def _privileged_close_once(fd: int) -> None:
    os.close(fd)
    try:
        fcntl.fcntl(fd, fcntl.F_GETFD)
    except OSError as error:
        if error.errno != errno.EBADF:
            raise
    else:
        raise RuntimeError("descriptor remains open")


def _privileged_live_nonstdio() -> set[int]:
    result: set[int] = set()
    for name in os.listdir("/proc/self/fd"):
        if not name.isdigit():
            raise RuntimeError("non-numeric descriptor entry")
        fd = int(name)
        if fd < 3:
            continue
        try:
            fcntl.fcntl(fd, fcntl.F_GETFD)
        except OSError as error:
            if error.errno != errno.EBADF:
                raise
        else:
            result.add(fd)
    return result


def _privileged_close_other_nonstdio(keep: set[int]) -> None:
    for fd in sorted(_privileged_live_nonstdio() - keep):
        _privileged_close_once(fd)
    if _privileged_live_nonstdio() != keep:
        raise RuntimeError("nonstdio descriptor set")


def _privileged_read_status() -> dict[str, str]:
    values: dict[str, str] = {}
    with open("/proc/self/status", "r", encoding="ascii") as status_file:
        for line in status_file:
            key, separator, value = line.partition(":")
            if separator and key in {
                "Uid", "Gid", "Groups", "CapInh", "CapPrm", "CapEff", "CapAmb",
                "NoNewPrivs",
            }:
                if key in values:
                    raise RuntimeError("duplicate credential status key")
                values[key] = value.strip()
    return values


def _privileged_verify_credentials() -> None:
    expected_uid = (_PRIVILEGED_UID,) * 3
    expected_gid = (_PRIVILEGED_GID,) * 3
    if os.getresuid() != expected_uid or os.getresgid() != expected_gid:
        raise RuntimeError("res credential contract")
    values = _privileged_read_status()
    if set(values) != {
        "Uid", "Gid", "Groups", "CapInh", "CapPrm", "CapEff", "CapAmb", "NoNewPrivs"
    }:
        raise RuntimeError("credential status keyset")
    if tuple(int(item) for item in values["Uid"].split()) != (_PRIVILEGED_UID,) * 4:
        raise RuntimeError("uid quartet")
    if tuple(int(item) for item in values["Gid"].split()) != (_PRIVILEGED_GID,) * 4:
        raise RuntimeError("gid quartet")
    if values["Groups"]:
        raise RuntimeError("supplementary group contract")
    if any(int(values[key], 16) != 0 for key in ("CapInh", "CapPrm", "CapEff", "CapAmb")):
        raise RuntimeError("capability contract")
    if values["NoNewPrivs"] != "1":
        raise RuntimeError("no_new_privs contract")


def _privileged_clear_authority() -> None:
    libc = ctypes.CDLL(None, use_errno=True)
    header = _CapHeader(0x20080522, 0)
    data = (_CapData * 2)()
    if libc.capset(ctypes.byref(header), ctypes.byref(data)) != 0:
        raise OSError(ctypes.get_errno(), "capset")
    pr_cap_ambient = 47
    pr_cap_ambient_clear_all = 4
    if libc.prctl(pr_cap_ambient, pr_cap_ambient_clear_all, 0, 0, 0) != 0:
        raise OSError(ctypes.get_errno(), "PR_CAP_AMBIENT_CLEAR_ALL")
    if libc.prctl(38, 1, 0, 0, 0) != 0:
        raise OSError(ctypes.get_errno(), "PR_SET_NO_NEW_PRIVS")


def _privileged_read_relative(
    root_fd: int,
    relative_path: str,
    expected_size: int,
    expected_sha256: str,
) -> bytes:
    parts = relative_path.split("/")
    if not parts or any(not part or part in {".", ".."} for part in parts):
        raise RuntimeError("manifest relative path")
    current_fd = root_fd
    current_owned = False
    source_fd = -1
    pending_fd = -1
    try:
        for component in parts[:-1]:
            pending_fd = os.open(
                component,
                os.O_RDONLY | os.O_DIRECTORY | getattr(os, "O_CLOEXEC", 0)
                | getattr(os, "O_NOFOLLOW", 0),
                dir_fd=current_fd,
            )
            observed = os.fstat(pending_fd)
            if not stat.S_ISDIR(observed.st_mode):
                closing = pending_fd
                pending_fd = -1
                _privileged_close_once(closing)
                raise RuntimeError("manifest ancestor type")
            if current_owned:
                closing = current_fd
                current_owned = False
                _privileged_close_once(closing)
            current_fd = pending_fd
            pending_fd = -1
            current_owned = True
        source_fd = os.open(
            parts[-1],
            os.O_RDONLY | getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_NOFOLLOW", 0),
            dir_fd=current_fd,
        )
        observed = os.fstat(source_fd)
        if (
            not stat.S_ISREG(observed.st_mode)
            or observed.st_nlink != 1
            or observed.st_size != expected_size
        ):
            raise RuntimeError("manifest source stat")
        chunks: list[bytes] = []
        remaining = expected_size
        while remaining:
            block = os.read(source_fd, min(131_072, remaining))
            if not block:
                raise RuntimeError("manifest source short read")
            chunks.append(block)
            remaining -= len(block)
        if os.read(source_fd, 1) != b"":
            raise RuntimeError("manifest source extra byte")
        raw = b"".join(chunks)
        if hashlib.sha256(raw).hexdigest() != expected_sha256:
            raise RuntimeError("manifest source hash")
        return raw
    finally:
        try:
            try:
                if source_fd >= 0:
                    closing = source_fd
                    source_fd = -1
                    _privileged_close_once(closing)
            finally:
                if pending_fd >= 0:
                    closing = pending_fd
                    pending_fd = -1
                    _privileged_close_once(closing)
        finally:
            if current_owned:
                closing = current_fd
                current_owned = False
                _privileged_close_once(closing)


def _privileged_manifest_rows(repo_fd: int) -> list[dict[str, object]]:
    rows: list[dict[str, object]] = []
    for module, relative_path, byte_size, raw_sha256 in _PRIVILEGED_MANIFEST:
        _privileged_read_relative(repo_fd, relative_path, byte_size, raw_sha256)
        rows.append(
            {
                "module": module,
                "relative_path": relative_path,
                "byte_size": byte_size,
                "raw_sha256": raw_sha256,
            }
        )
    return rows


def _privileged_id_is_mapped(path: str, identity: int) -> bool:
    """Return whether an inside user-namespace identity has an active mapping."""

    try:
        rows = Path(path).read_text(encoding="ascii").splitlines()
    except (OSError, UnicodeError):
        return False
    for row in rows:
        fields = row.split()
        if len(fields) != 3:
            return False
        try:
            inside, _outside, length = (int(field, 10) for field in fields)
        except ValueError:
            return False
        if length > 0 and inside <= identity < inside + length:
            return True
    return False


def _privileged_runner_admission() -> None:
    """Fail before fixture/fork when the current namespace cannot prove UID 65534."""

    if os.geteuid() != 0 or os.getegid() != 0:
        raise PermissionError(errno.EPERM, "root integration required")
    try:
        setgroups_policy = Path("/proc/self/setgroups").read_text(
            encoding="ascii"
        ).strip()
    except (OSError, UnicodeError) as error:
        raise PermissionError(errno.EPERM, "setgroups policy unavailable") from error
    if setgroups_policy != "allow":
        raise PermissionError(errno.EPERM, "setgroups policy denies transition")
    if not _privileged_id_is_mapped("/proc/self/uid_map", _PRIVILEGED_UID):
        raise PermissionError(errno.EPERM, "privileged uid is not mapped")
    if not _privileged_id_is_mapped("/proc/self/gid_map", _PRIVILEGED_GID):
        raise PermissionError(errno.EPERM, "privileged gid is not mapped")
    status = _privileged_read_status()
    try:
        effective = int(status["CapEff"], 16)
    except (KeyError, ValueError) as error:
        raise PermissionError(errno.EPERM, "effective capabilities unavailable") from error
    required = (1 << 6) | (1 << 7) | (1 << 8)
    if effective & required != required:
        raise PermissionError(errno.EPERM, "credential transition capabilities unavailable")


def _privileged_runtime_manifest_sha256() -> str:
    """Bind the exact installed pip source used by this admitted interpreter."""

    purelib = sysconfig.get_path("purelib")
    if not purelib or not os.path.isabs(purelib):
        raise RuntimeError("control pip source root")
    version = contract.PreparationContractV1.EXPECTED_PIP_VERSION
    roots = (
        os.path.join(purelib, "pip"),
        os.path.join(purelib, f"pip-{version}.dist-info"),
    )
    rows: list[dict[str, object]] = []
    total = 0
    for root in roots:
        if not os.path.isdir(root):
            raise RuntimeError("control pip source missing")
        for directory, directories, files in os.walk(
            root, topdown=True, followlinks=False
        ):
            directories.sort()
            files.sort()
            for name in directories:
                if stat.S_ISLNK(os.lstat(os.path.join(directory, name)).st_mode):
                    raise RuntimeError("control pip source symlink")
            for name in files:
                path = os.path.join(directory, name)
                observed = os.lstat(path)
                if not stat.S_ISREG(observed.st_mode):
                    raise RuntimeError("control pip source type")
                raw = Path(path).read_bytes()
                if len(raw) != observed.st_size:
                    raise RuntimeError("control pip source size")
                total += len(raw)
                if total > 67_108_864 or len(rows) >= 8192:
                    raise RuntimeError("control pip source budget")
                rows.append(
                    {
                        "relative_path": os.path.relpath(path, purelib).replace(
                            os.sep, "/"
                        ),
                        "byte_count": len(raw),
                        "raw_sha256": hashlib.sha256(raw).hexdigest(),
                    }
                )
    rows.sort(key=lambda row: str(row["relative_path"]))
    return contract.canonical_sha256(rows)


def _privileged_runtime_source_identity() -> dict[str, object]:
    """Bind the pre-exec interpreter bytes without binding its transient locator."""

    raw = Path(sys.executable).read_bytes()
    if not raw or len(raw) > _PRIVILEGED_RUNTIME_SOURCE_SIZE_LIMIT:
        raise RuntimeError("control interpreter source budget")
    if hashlib.sha256(raw).hexdigest() != contract.PreparationContractV1.EXPECTED_INTERPRETER_SHA256:
        raise RuntimeError("control interpreter source identity")
    return {"byte_size": len(raw), "raw_sha256": hashlib.sha256(raw).hexdigest()}


def _privileged_exec_child(
    source_fd: int,
    stdin_fd: int,
    repo_fd: int,
    repo_identity: tuple[int, int],
) -> None:
    stage = "PRE_DROP_CWD_AND_FD9_SETUP"
    reason_class = "WORK_PRIVILEGE_OR_OS_SURFACE"
    execve_request_count = 0
    try:
        if len({source_fd, stdin_fd, repo_fd}) != 3 or min(source_fd, stdin_fd, repo_fd) < 3:
            raise RuntimeError("inherited descriptor contract")
        source_copy = fcntl.fcntl(source_fd, fcntl.F_DUPFD_CLOEXEC, 10)
        stdin_copy = fcntl.fcntl(stdin_fd, fcntl.F_DUPFD_CLOEXEC, 10)
        repo_copy = fcntl.fcntl(repo_fd, fcntl.F_DUPFD_CLOEXEC, 10)
        os.fchdir(repo_copy)
        observed_cwd = os.stat(".", follow_symlinks=False)
        if (observed_cwd.st_dev, observed_cwd.st_ino) != repo_identity:
            raise RuntimeError("pre-drop cwd identity")
        closing = repo_copy
        repo_copy = -1
        _privileged_close_once(closing)
        closing = repo_fd
        repo_fd = -1
        _privileged_close_once(closing)

        os.dup2(source_copy, 9, inheritable=True)
        os.dup2(stdin_copy, 0, inheritable=True)
        for original in (source_copy, stdin_copy, source_fd, stdin_fd):
            if original not in {0, 2, 9}:
                _privileged_close_once(original)
        _privileged_close_other_nonstdio({9})

        stage = "CREDENTIAL_AND_AUTHORITY_DROP"
        os.setgroups([])
        os.setresgid(_PRIVILEGED_GID, _PRIVILEGED_GID, _PRIVILEGED_GID)
        os.setresuid(_PRIVILEGED_UID, _PRIVILEGED_UID, _PRIVILEGED_UID)
        _privileged_clear_authority()
        _privileged_verify_credentials()
        observed_cwd = os.stat(".", follow_symlinks=False)
        if (observed_cwd.st_dev, observed_cwd.st_ino) != repo_identity:
            raise RuntimeError("post-drop cwd identity")
        if _privileged_live_nonstdio() != {9}:
            raise RuntimeError("pre-exec descriptor set")

        stage = "EXECVE_REQUEST"
        reason_class = "EXEC_BOOTSTRAP"
        _privileged_emit_event("EXECVE_REQUESTED", 1)
        execve_request_count = 1
        argv = [sys.executable, "-E", "-s", "-S", "-B", "-c", _PRIVILEGED_BOOTSTRAP_SOURCE]
        os.execve(sys.executable, argv, {})
    except BaseException as error:
        try:
            internal = None
            diagnostic_reason = reason_class
            if not isinstance(error, OSError):
                if stage == "CREDENTIAL_AND_AUTHORITY_DROP":
                    internal = "CREDENTIAL_CONTRACT_MISMATCH"
                elif stage == "PRE_DROP_CWD_AND_FD9_SETUP":
                    internal = "DESCRIPTOR_SET_OR_CLOSE_UNCERTAIN"
                else:
                    internal = "EVENT_OR_RESULT_TRANSPORT_INVALID"
                diagnostic_reason = (
                    "EXEC_BOOTSTRAP" if stage == "EXECVE_REQUEST" else "IMPLEMENTATION_CONTRACT"
                )
            _privileged_emit_diagnostic(
                stage=stage,
                reason_class=diagnostic_reason,
                error=error,
                internal_reason=internal,
                execve_request_count=execve_request_count,
                postexec_entry_count=0,
                child_exit_class="CHILD_NONZERO",
            )
        except BaseException:
            pass
        os._exit(71)


def _write_pipe_exact(fd: int, payload: bytes) -> None:
    view = memoryview(payload)
    while view:
        written = os.write(fd, view)
        if written <= 0:
            raise RuntimeError("stdin writer made no progress")
        view = view[written:]


def _privileged_parent() -> int:
    temporary = ""
    source_path = ""
    temporary_exists = False
    source_exists = False
    repo_fd = -1
    source_write_fd = -1
    source_read_fd = -1
    read_fd = -1
    write_fd = -1
    child_pid = -1
    fork_succeeded = False
    waited = False
    try:
        _privileged_runner_admission()
        temporary = tempfile.mkdtemp(prefix="g4b-fd9-dac-")
        temporary_exists = True
        source_path = os.path.join(temporary, "source")
        repo_fd = os.open(
            REPO_ROOT,
            os.O_RDONLY | os.O_DIRECTORY | getattr(os, "O_CLOEXEC", 0)
            | getattr(os, "O_NOFOLLOW", 0),
        )
        repo_observed = os.fstat(repo_fd)
        repo_identity = (repo_observed.st_dev, repo_observed.st_ino)
        manifest_rows = _privileged_manifest_rows(repo_fd)
        os.chmod(temporary, 0o755)
        source_write_fd = os.open(
            source_path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600
        )
        source_exists = True
        initial = os.fstat(source_write_fd)
        source_object = _source_object_identity(
            types.SimpleNamespace(
                st_dev=initial.st_dev,
                st_ino=initial.st_ino,
                st_uid=0,
                st_gid=initial.st_gid,
                st_mode=stat.S_IFREG | 0o400,
                st_nlink=1,
            )
        )
        credential = _credential_contract(_PRIVILEGED_UID, _PRIVILEGED_GID, [])
        mapping = _mapping_provenance(source_object, credential)
        now = _datetime.datetime.now(_datetime.timezone.utc).replace(microsecond=0)
        issued_at = now.strftime("%Y-%m-%dT%H:%M:%SZ")
        expires_at = (now + _datetime.timedelta(minutes=15)).strftime(
            "%Y-%m-%dT%H:%M:%SZ"
        )
        attestation = _egress_attestation(mapping, issued_at, expires_at)
        attestation_raw = contract.canonical_json_bytes(attestation)
        _write_pipe_exact(source_write_fd, attestation_raw)
        os.fsync(source_write_fd)
        os.fchmod(source_write_fd, 0o400)
        closing = source_write_fd
        source_write_fd = -1
        _privileged_close_once(closing)
        source_observed = os.stat(source_path, follow_symlinks=False)
        source_identity = _source_fixed_identity(source_observed)
        request = _execution_request_from_source(mapping, attestation, source_identity)
        request["control_runtime"][
            "pip_installed_source_manifest_sha256"
        ] = _privileged_runtime_manifest_sha256()
        contract.validate_execution_request(request)
        source_read_fd = os.open(
            source_path,
            os.O_RDONLY | getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_NOFOLLOW", 0),
        )
        read_fd, write_fd = os.pipe()
        child_pid = os.fork()
        if child_pid == 0:
            _privileged_exec_child(source_read_fd, read_fd, repo_fd, repo_identity)
            os._exit(74)
        fork_succeeded = True
        closing = repo_fd
        repo_fd = -1
        _privileged_close_once(closing)
        closing = source_read_fd
        source_read_fd = -1
        _privileged_close_once(closing)
        closing = read_fd
        read_fd = -1
        _privileged_close_once(closing)
        envelope = {
            "schema_version": _PRIVILEGED_ENVELOPE_SCHEMA,
            "bootstrap_source_manifest": manifest_rows,
            "repository_cwd_identity": {
                "st_dev": repo_identity[0],
                "st_ino": repo_identity[1],
            },
            "negative_dac_locator": source_path,
            "runtime_source_identity": _privileged_runtime_source_identity(),
            "execution_request": request,
        }
        payload = contract.canonical_file_bytes(envelope)
        if len(payload) > _PRIVILEGED_STDIN_LIMIT:
            raise RuntimeError("integration envelope bound")
        _write_pipe_exact(write_fd, payload)
        closing = write_fd
        write_fd = -1
        _privileged_close_once(closing)
        waited_pid, status_value = os.waitpid(child_pid, 0)
        waited = True
        child_pid = -1
        if waited_pid <= 0:
            return 73
        if os.WIFSIGNALED(status_value):
            return 72
        if not os.WIFEXITED(status_value) or os.WEXITSTATUS(status_value) != 0:
            return 71
        source_exists = False
        os.unlink(source_path)
        temporary_exists = False
        os.rmdir(temporary)
        pass_record = b"PRIVILEGED_ACTUAL_DAC_INTEGRATION_EXACT1_PASS\n"
        if os.write(1, pass_record) != len(pass_record):
            return 73
        return 0
    except BaseException as error:
        if not fork_succeeded:
            try:
                _privileged_emit_diagnostic(
                    stage="ROOT_PARENT_OR_FIXTURE",
                    reason_class=(
                        "WORK_PRIVILEGE_OR_OS_SURFACE"
                        if isinstance(error, OSError)
                        else "IMPLEMENTATION_CONTRACT"
                    ),
                    error=error,
                    internal_reason=(
                        None if isinstance(error, OSError) else "EVENT_OR_RESULT_TRANSPORT_INVALID"
                    ),
                    execve_request_count=0,
                    postexec_entry_count=0,
                    child_exit_class=(
                        "PRE_FORK_ROOT_FAILURE" if isinstance(error, OSError) else "INTERNAL_ROOT_FAILURE"
                    ),
                )
            except BaseException:
                pass
            return 70 if isinstance(error, OSError) else 74
        if child_pid > 0 and not waited:
            try:
                os.kill(child_pid, signal.SIGKILL)
            except OSError:
                pass
            try:
                os.waitpid(child_pid, 0)
            except OSError:
                pass
            waited = True
            child_pid = -1
        return 73
    finally:
        for fd in (repo_fd, source_write_fd, source_read_fd, read_fd, write_fd):
            if fd >= 0:
                try:
                    os.close(fd)
                except OSError:
                    pass
        if source_exists:
            try:
                os.unlink(source_path)
            except OSError:
                pass
        if temporary_exists:
            try:
                os.rmdir(temporary)
            except OSError:
                pass


if __name__ == "__main__":
    if sys.argv[1:] == [_PRIVILEGED_PARENT_FLAG]:
        raise SystemExit(_privileged_parent())
    unittest.main()
