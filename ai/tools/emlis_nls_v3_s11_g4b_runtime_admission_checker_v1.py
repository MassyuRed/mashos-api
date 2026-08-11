#!/usr/bin/env python3
"""Read-only orchestrator for G4-B runtime admission checker V1.

Acquisition and materialisation are deliberately out of scope.  The unmodified
CLI ``main`` is the only credit-bearing entrypoint.  It accepts the strict
Rule13/Rule16 external attestation for an externally prepared fresh runtime,
reads the current projection without mutation, launches each frozen role once
in fixed order, and returns a body-free terminal result.  Library invocation
is explicitly non-credit-bearing.
"""

from __future__ import annotations

import hashlib
import io
import os
import stat
import struct
import subprocess
import sys
import zlib
from typing import Any, Callable

sys.dont_write_bytecode = True

from ai.tools.emlis_nls_v3_s11_g4b_runtime_admission_contract_v1 import (  # noqa: E402
    ContractV1,
    ContractViolation,
    canonical_json_bytes,
    canonical_sha256,
    read_strict_json,
    runtime_executable_locator_sha256,
    runtime_root_locator_sha256,
    validate_public_result,
    validate_request,
    validate_role_result,
    write_strict_json,
)


_OWNER_MODULE = "ai.tools.emlis_nls_v3_s11_g4b_runtime_admission_owner_v1"
_INDEPENDENT_MODULE = (
    "ai.tools.emlis_nls_v3_s11_g4b_runtime_admission_independent_v1"
)
_PROCESS_TIMEOUT_SECONDS = 180
_MAX_PROCESS_OUTPUT_BYTES = ContractV1.MAX_INPUT_BYTES
_READINESS_SCHEMA = (
    "cocolon.emlis.nls_v3.step11.cycle001.g4.gate_b."
    "runtime_readiness_observation_preimage.v1"
)
_SMOKE_PREIMAGE_CLASS = "PATH_FREE_VERSIONED_INLINE_PROGRAM_V1"
_EXECUTION_ORDER = "OWNER>PYTEST_VERSION_PROBE>REQUIRED_ROLE_SMOKE>INDEPENDENT"
_ROLE_LAUNCH_PROGRAM = r'''import runpy
import sys
repo_root = sys.argv[1]
module_name = sys.argv[2]
sys.path.insert(0, repo_root)
runpy.run_module(module_name, run_name="__main__", alter_sys=True)
'''

_ROLE_SMOKE_PROGRAM = r'''from __future__ import annotations
import importlib.util
import inspect
import json
import os
import sys

repo_root = os.path.abspath(sys.argv[1])
sys.path.insert(0, repo_root)
effect_attempt_count = 0
blocked_events = {
    "os.chdir", "os.chflags", "os.chmod", "os.chown", "os.fchmod", "os.fchown",
    "os.fork", "os.forkpty", "os.ftruncate", "os.kill", "os.killpg", "os.lchown",
    "os.link", "os.mkfifo", "os.mkdir", "os.mknod",
    "os.putenv", "os.remove", "os.removexattr", "os.rename", "os.rmdir",
    "os.setxattr", "os.symlink", "os.system", "os.truncate", "os.unsetenv",
    "os.utime", "pty.spawn", "subprocess.Popen",
}
write_flags = (
    getattr(os, "O_APPEND", 0) | getattr(os, "O_CREAT", 0) |
    getattr(os, "O_EXCL", 0) | getattr(os, "O_RDWR", 0) |
    getattr(os, "O_TRUNC", 0) | getattr(os, "O_WRONLY", 0)
)
def deny_effect(event, arguments):
    global effect_attempt_count
    prohibited = event in blocked_events or event.startswith("socket.") or event.startswith("os.exec") or event.startswith("os.spawn") or event.startswith("os.posix_spawn")
    if event == "open":
        mode = arguments[1] if len(arguments) > 1 else None
        flags = arguments[2] if len(arguments) > 2 else 0
        prohibited = (
            (isinstance(mode, str) and any(character in mode for character in "wax+"))
            or (isinstance(flags, int) and bool(flags & write_flags))
        )
    if prohibited:
        effect_attempt_count += 1
        raise PermissionError("ROLE_SMOKE_EFFECT_DENIED")
sys.addaudithook(deny_effect)
specifications = (
    ("OWNER", "ai/services/ai_inference/emlis_ai_recovery_epoch002_sequence_ledger_v3.py", "validate_recovery_epoch004_sequence_event1_contract_state_v2"),
    ("INDEPENDENT", "ai/tools/emlis_nls_v3_recovery_epoch002_closure_receipt_verify.py", "verify_recovery_epoch004_sequence_event1_contract_state_v2"),
    ("PARENT", "ai/tools/emlis_nls_v3_recovery_epoch002_formal_parent_orchestrator_v3.py", "validate_recovery_epoch004_parent_phase3_event1_evidence_state_v2"),
)
loaded = 0
for index, (role, relative_path, callable_name) in enumerate(specifications):
    source_path = os.path.join(repo_root, *relative_path.split("/"))
    module_spec = importlib.util.spec_from_file_location(f"_g4b_role_smoke_{index}", source_path)
    if module_spec is None or module_spec.loader is None:
        raise RuntimeError("ROLE_SPEC_INVALID")
    module = importlib.util.module_from_spec(module_spec)
    module_spec.loader.exec_module(module)
    public_callable = getattr(module, callable_name, None)
    if not callable(public_callable):
        raise RuntimeError("ROLE_CALLABLE_ABSENT")
    parameters = tuple(inspect.signature(public_callable).parameters.values())
    if len(parameters) != 1:
        raise RuntimeError("ROLE_SIGNATURE_INVALID")
    loaded += 1
sys.stdout.write(json.dumps({"direct_role_load_count":loaded,"public_api_call_count":0,"effect_count":effect_attempt_count},sort_keys=True,separators=(",",":")))
'''


PopenFactory = Callable[..., Any]
_popen_factory: PopenFactory = subprocess.Popen
_CLI_ADMISSION_TOKEN = object()


def _raw_file(path: str) -> bytes:
    try:
        if os.path.realpath(path) != os.path.abspath(path) or not stat.S_ISREG(os.lstat(path).st_mode):
            raise ContractViolation("BASE_OR_PREIMAGE_DRIFT", "required source locator invalid")
        with open(path, "rb") as handle:
            return handle.read(_MAX_PROCESS_OUTPUT_BYTES + 1)
    except ContractViolation:
        raise
    except OSError as exc:
        raise ContractViolation("BASE_OR_PREIMAGE_DRIFT", "required source is unreadable") from exc


def _raw_sha256(path: str) -> str:
    body = _raw_file(path)
    if len(body) > _MAX_PROCESS_OUTPUT_BYTES:
        raise ContractViolation("BASE_OR_PREIMAGE_DRIFT", "required source exceeds V1 limit")
    return hashlib.sha256(body).hexdigest()


def _repo_root() -> str:
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))


def _assert_official_cli_context() -> None:
    """Require the tracked ``-E -s -S -B -m`` admission startup boundary."""

    flags = sys.flags
    startup_flags_valid = all(
        getattr(flags, field, 0) == 1
        for field in (
            "ignore_environment",
            "no_user_site",
            "no_site",
            "dont_write_bytecode",
        )
    )
    module_name = getattr(__spec__, "name", None)
    try:
        cwd = os.getcwd()
    except OSError as exc:
        raise ContractViolation(
            "CURRENT_AUTHORITY_STOP", "official CLI cwd is unavailable"
        ) from exc
    if (
        not startup_flags_valid
        or module_name != ContractV1.OFFICIAL_ADMISSION_MODULE
        or __name__ != "__main__"
        or cwd != _repo_root()
    ):
        raise ContractViolation(
            "CURRENT_AUTHORITY_STOP", "official CLI startup context is absent"
        )


def _read_git_file(path: str, limit: int = 33_554_432) -> bytes:
    try:
        if os.path.realpath(path) != os.path.abspath(path):
            raise ContractViolation(
                "BASE_OR_PREIMAGE_DRIFT", "Git metadata has a symlink component"
            )
        observed = os.lstat(path)
        if not stat.S_ISREG(observed.st_mode):
            raise ContractViolation("BASE_OR_PREIMAGE_DRIFT", "Git metadata is not regular")
        if observed.st_size > limit:
            raise ContractViolation("BASE_OR_PREIMAGE_DRIFT", "Git metadata exceeds limit")
        with open(path, "rb") as handle:
            body = handle.read(limit + 1)
    except ContractViolation:
        raise
    except OSError as exc:
        raise ContractViolation("BASE_OR_PREIMAGE_DRIFT", "Git metadata is unreadable") from exc
    if len(body) > limit:
        raise ContractViolation("BASE_OR_PREIMAGE_DRIFT", "Git metadata exceeds limit")
    return body


def _git_directory(repo_root: str) -> str:
    dot_git = os.path.join(repo_root, ".git")
    try:
        observed = os.lstat(dot_git)
    except OSError as exc:
        raise ContractViolation("BASE_OR_PREIMAGE_DRIFT", "Git directory is absent") from exc
    if stat.S_ISLNK(observed.st_mode):
        raise ContractViolation("BASE_OR_PREIMAGE_DRIFT", "Git directory is a symlink")
    if stat.S_ISDIR(observed.st_mode):
        return dot_git
    if not stat.S_ISREG(observed.st_mode):
        raise ContractViolation("BASE_OR_PREIMAGE_DRIFT", "unsupported .git locator")
    try:
        locator = _read_git_file(dot_git, 4096).decode("utf-8", "strict").strip()
    except UnicodeDecodeError as exc:
        raise ContractViolation("BASE_OR_PREIMAGE_DRIFT", "Git locator is not UTF-8") from exc
    prefix = "gitdir: "
    if not locator.startswith(prefix) or "\n" in locator or "\r" in locator:
        raise ContractViolation("BASE_OR_PREIMAGE_DRIFT", "Git locator format invalid")
    git_dir = locator[len(prefix) :]
    if not os.path.isabs(git_dir):
        git_dir = os.path.abspath(os.path.join(repo_root, git_dir))
    if os.path.realpath(git_dir) != git_dir or not os.path.isdir(git_dir):
        raise ContractViolation("BASE_OR_PREIMAGE_DRIFT", "resolved Git directory invalid")
    return git_dir


def _git_common_directory(git_dir: str) -> str:
    commondir_path = os.path.join(git_dir, "commondir")
    if not os.path.lexists(commondir_path):
        return git_dir
    try:
        locator = _read_git_file(commondir_path, 4096).decode("utf-8", "strict").strip()
    except UnicodeDecodeError as exc:
        raise ContractViolation("BASE_OR_PREIMAGE_DRIFT", "Git commondir is not UTF-8") from exc
    if not locator or "\n" in locator or "\r" in locator:
        raise ContractViolation("BASE_OR_PREIMAGE_DRIFT", "Git commondir locator invalid")
    common_dir = locator if os.path.isabs(locator) else os.path.abspath(os.path.join(git_dir, locator))
    if os.path.realpath(common_dir) != common_dir or not os.path.isdir(common_dir):
        raise ContractViolation("BASE_OR_PREIMAGE_DRIFT", "Git common directory invalid")
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
            raise ContractViolation("BASE_OR_PREIMAGE_DRIFT", "packed-refs is not ASCII") from exc
        for line in lines:
            if not line or line.startswith("#") or line.startswith("^"):
                continue
            pieces = line.split(" ", 1)
            if len(pieces) != 2:
                raise ContractViolation("BASE_OR_PREIMAGE_DRIFT", "packed-refs row invalid")
            oid, name = pieces
            if name == reference:
                matches.append(oid)
    if len(matches) != 1 or ContractV1.GIT_OID_RE.fullmatch(matches[0]) is None:
        raise ContractViolation("BASE_OR_PREIMAGE_DRIFT", "packed Git reference unresolved")
    return matches[0]


def _resolve_git_reference(git_dir: str, common_dir: str, value: str) -> str:
    current = value
    seen: set[str] = set()
    for _depth in range(5):
        if ContractV1.GIT_OID_RE.fullmatch(current) is not None:
            return current
        prefix = "ref: "
        if not current.startswith(prefix):
            raise ContractViolation("BASE_OR_PREIMAGE_DRIFT", "Git reference value invalid")
        reference = current[len(prefix) :]
        if (
            not reference.startswith("refs/")
            or reference in seen
            or "\\" in reference
            or any(part in ("", ".", "..") for part in reference.split("/"))
        ):
            raise ContractViolation("BASE_OR_PREIMAGE_DRIFT", "Git reference path invalid")
        seen.add(reference)
        ref_paths = [
            os.path.join(directory, *reference.split("/"))
            for directory in dict.fromkeys((git_dir, common_dir))
        ]
        loose_refs = [path for path in ref_paths if os.path.lexists(path)]
        if len(loose_refs) > 1:
            raise ContractViolation("BASE_OR_PREIMAGE_DRIFT", "duplicate loose Git reference")
        if loose_refs:
            try:
                current = _read_git_file(loose_refs[0], 4096).decode("ascii", "strict").strip()
            except UnicodeDecodeError as exc:
                raise ContractViolation("BASE_OR_PREIMAGE_DRIFT", "Git ref is not ASCII") from exc
        else:
            current = _packed_ref((git_dir, common_dir), reference)
    raise ContractViolation("BASE_OR_PREIMAGE_DRIFT", "Git reference recursion exceeded")


def _commit_body_tree(body: bytes) -> str:
    first_line = body.split(b"\n", 1)[0]
    if not first_line.startswith(b"tree "):
        raise ContractViolation("BASE_OR_PREIMAGE_DRIFT", "commit tree line absent")
    try:
        tree_oid = first_line[5:].decode("ascii", "strict")
    except UnicodeDecodeError as exc:
        raise ContractViolation("BASE_OR_PREIMAGE_DRIFT", "commit tree is not ASCII") from exc
    if ContractV1.GIT_OID_RE.fullmatch(tree_oid) is None:
        raise ContractViolation("BASE_OR_PREIMAGE_DRIFT", "commit tree identity invalid")
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
        raise ContractViolation("BASE_OR_PREIMAGE_DRIFT", "loose commit object invalid") from exc
    if (
        len(decompressed) > 1_048_576
        or not decoder.eof
        or decoder.unconsumed_tail
        or decoder.unused_data
        or hashlib.sha1(decompressed).hexdigest() != commit_oid
    ):
        raise ContractViolation("BASE_OR_PREIMAGE_DRIFT", "loose commit identity mismatch")
    separator = decompressed.find(b"\0")
    if separator < 0:
        raise ContractViolation("BASE_OR_PREIMAGE_DRIFT", "loose commit header absent")
    header, body = decompressed[:separator], decompressed[separator + 1 :]
    pieces = header.split(b" ", 1)
    if len(pieces) != 2 or pieces[0] != b"commit":
        raise ContractViolation("BASE_OR_PREIMAGE_DRIFT", "loose object is not a commit")
    try:
        declared_size = int(pieces[1], 10)
    except ValueError as exc:
        raise ContractViolation("BASE_OR_PREIMAGE_DRIFT", "commit size is invalid") from exc
    if declared_size != len(body):
        raise ContractViolation("BASE_OR_PREIMAGE_DRIFT", "commit size mismatch")
    return _commit_body_tree(body)


def _pack_index_offset(index_path: str, commit_oid: str) -> tuple[int, bytes, int]:
    index = _read_git_file(index_path, 67_108_864)
    if len(index) < 8 + 1024 + 40 or index[:4] != b"\xfftOc":
        raise ContractViolation("BASE_OR_PREIMAGE_DRIFT", "pack index v2 header invalid")
    if struct.unpack(">I", index[4:8])[0] != 2:
        raise ContractViolation("BASE_OR_PREIMAGE_DRIFT", "pack index version unsupported")
    if hashlib.sha1(index[:-20]).digest() != index[-20:]:
        raise ContractViolation("BASE_OR_PREIMAGE_DRIFT", "pack index checksum invalid")
    fanout = struct.unpack(">256I", index[8:1032])
    if any(left > right for left, right in zip(fanout, fanout[1:])):
        raise ContractViolation("BASE_OR_PREIMAGE_DRIFT", "pack index fanout invalid")
    count = fanout[-1]
    names_start = 1032
    crc_start = names_start + 20 * count
    offsets_start = crc_start + 4 * count
    offsets_end = offsets_start + 4 * count
    if offsets_end + 40 > len(index):
        raise ContractViolation("BASE_OR_PREIMAGE_DRIFT", "pack index table truncated")
    large_bytes = len(index) - 40 - offsets_end
    if large_bytes < 0 or large_bytes % 8:
        raise ContractViolation("BASE_OR_PREIMAGE_DRIFT", "pack index large offsets invalid")
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
            raise ContractViolation("BASE_OR_PREIMAGE_DRIFT", "pack large offset slot invalid")
        large_start = offsets_end + 8 * large_slot
        offset = struct.unpack(">Q", index[large_start : large_start + 8])[0]
    else:
        offset = raw_offset
    return offset, index[-40:-20], count


def _verify_pack_checksum(pack_path: str, expected_checksum: bytes) -> tuple[int, int]:
    try:
        if os.path.realpath(pack_path) != os.path.abspath(pack_path):
            raise ContractViolation(
                "BASE_OR_PREIMAGE_DRIFT", "pack file has a symlink component"
            )
        observed = os.lstat(pack_path)
        if not stat.S_ISREG(observed.st_mode) or observed.st_size < 12 + 20:
            raise ContractViolation("BASE_OR_PREIMAGE_DRIFT", "pack file invalid")
        digest = hashlib.sha1()
        with open(pack_path, "rb") as handle:
            header = handle.read(12)
            if len(header) != 12 or header[:4] != b"PACK":
                raise ContractViolation("BASE_OR_PREIMAGE_DRIFT", "pack header invalid")
            version, count = struct.unpack(">II", header[4:12])
            if version not in (2, 3):
                raise ContractViolation("BASE_OR_PREIMAGE_DRIFT", "pack version unsupported")
            handle.seek(0)
            remaining = observed.st_size - 20
            while remaining:
                block = handle.read(min(131_072, remaining))
                if not block:
                    raise ContractViolation("BASE_OR_PREIMAGE_DRIFT", "pack truncated")
                digest.update(block)
                remaining -= len(block)
            trailer = handle.read(20)
    except ContractViolation:
        raise
    except OSError as exc:
        raise ContractViolation("BASE_OR_PREIMAGE_DRIFT", "pack file unreadable") from exc
    if trailer != expected_checksum or digest.digest() != trailer:
        raise ContractViolation("BASE_OR_PREIMAGE_DRIFT", "pack checksum mismatch")
    return observed.st_size, count


def _packed_commit_tree(common_dir: str, commit_oid: str) -> str:
    pack_dir = os.path.join(common_dir, "objects", "pack")
    try:
        if os.path.realpath(pack_dir) != os.path.abspath(pack_dir):
            raise ContractViolation(
                "BASE_OR_PREIMAGE_DRIFT", "pack directory has a symlink component"
            )
        with os.scandir(pack_dir) as scanner:
            indexes = sorted(
                entry.path
                for entry in scanner
                if entry.name.endswith(".idx") and entry.is_file(follow_symlinks=False)
            )
    except ContractViolation:
        raise
    except OSError as exc:
        raise ContractViolation("BASE_OR_PREIMAGE_DRIFT", "pack directory unavailable") from exc
    matches: list[tuple[str, int, bytes, int]] = []
    for index_path in indexes:
        try:
            offset, checksum, count = _pack_index_offset(index_path, commit_oid)
        except KeyError:
            continue
        matches.append((index_path[:-4] + ".pack", offset, checksum, count))
    if len(matches) != 1:
        raise ContractViolation("BASE_OR_PREIMAGE_DRIFT", "packed commit cardinality invalid")
    pack_path, offset, checksum, index_count = matches[0]
    pack_size, pack_count = _verify_pack_checksum(pack_path, checksum)
    if pack_count != index_count or offset < 12 or offset >= pack_size - 20:
        raise ContractViolation("BASE_OR_PREIMAGE_DRIFT", "packed commit offset invalid")
    try:
        with open(pack_path, "rb") as handle:
            handle.seek(offset)
            first = handle.read(1)
            if not first:
                raise ContractViolation("BASE_OR_PREIMAGE_DRIFT", "packed object header absent")
            byte = first[0]
            object_type = (byte >> 4) & 0x7
            declared_size = byte & 0x0F
            shift = 4
            while byte & 0x80:
                next_byte = handle.read(1)
                if not next_byte or shift > 60:
                    raise ContractViolation("BASE_OR_PREIMAGE_DRIFT", "packed object header invalid")
                byte = next_byte[0]
                declared_size |= (byte & 0x7F) << shift
                shift += 7
            if object_type != 1:
                raise ContractViolation("BASE_OR_PREIMAGE_DRIFT", "packed commit is delta/unsupported")
            if declared_size > 1_048_576:
                raise ContractViolation("BASE_OR_PREIMAGE_DRIFT", "packed commit exceeds limit")
            decoder = zlib.decompressobj()
            chunks: list[bytes] = []
            total = 0
            while not decoder.eof:
                block = handle.read(65_536)
                if not block:
                    raise ContractViolation("BASE_OR_PREIMAGE_DRIFT", "packed commit truncated")
                output = decoder.decompress(block, 1_048_577 - total)
                chunks.append(output)
                total += len(output)
                if total > 1_048_576:
                    raise ContractViolation("BASE_OR_PREIMAGE_DRIFT", "packed commit expands over limit")
            body = b"".join(chunks)
    except ContractViolation:
        raise
    except (OSError, zlib.error) as exc:
        raise ContractViolation("BASE_OR_PREIMAGE_DRIFT", "packed commit read invalid") from exc
    if len(body) != declared_size:
        raise ContractViolation("BASE_OR_PREIMAGE_DRIFT", "packed commit size mismatch")
    object_bytes = f"commit {len(body)}\0".encode("ascii") + body
    if hashlib.sha1(object_bytes).hexdigest() != commit_oid:
        raise ContractViolation("BASE_OR_PREIMAGE_DRIFT", "packed commit identity mismatch")
    return _commit_body_tree(body)


def _git_blob_oid(path: bytes, mode: int) -> bytes:
    try:
        observed = os.lstat(path)
    except OSError as exc:
        raise ContractViolation(
            "BASE_OR_PREIMAGE_DRIFT", "tracked worktree leaf is unavailable"
        ) from exc
    if mode in (0o100644, 0o100755):
        if not stat.S_ISREG(observed.st_mode):
            raise ContractViolation("BASE_OR_PREIMAGE_DRIFT", "tracked file type mismatch")
        worktree_mode = 0o100755 if stat.S_IMODE(observed.st_mode) & 0o111 else 0o100644
        if worktree_mode != mode:
            raise ContractViolation("BASE_OR_PREIMAGE_DRIFT", "tracked executable mode mismatch")
        length = observed.st_size
        digest = hashlib.sha1(f"blob {length}\0".encode("ascii"))
        try:
            with open(path, "rb") as handle:
                observed_length = 0
                for block in iter(lambda: handle.read(131_072), b""):
                    digest.update(block)
                    observed_length += len(block)
        except OSError as exc:
            raise ContractViolation("BASE_OR_PREIMAGE_DRIFT", "tracked file unreadable") from exc
        if observed_length != length:
            raise ContractViolation("BASE_OR_PREIMAGE_DRIFT", "tracked file changed while read")
        return digest.digest()
    if mode == 0o120000:
        if not stat.S_ISLNK(observed.st_mode):
            raise ContractViolation("BASE_OR_PREIMAGE_DRIFT", "tracked symlink type mismatch")
        try:
            target = os.readlink(path)
        except OSError as exc:
            raise ContractViolation(
                "BASE_OR_PREIMAGE_DRIFT", "tracked symlink is unreadable"
            ) from exc
        if isinstance(target, str):
            target_bytes = os.fsencode(target)
        else:
            target_bytes = target
        return hashlib.sha1(
            f"blob {len(target_bytes)}\0".encode("ascii") + target_bytes
        ).digest()
    if mode in (0o160000, 0o040000):
        raise ContractViolation("BASE_OR_PREIMAGE_DRIFT", "gitlink or sparse index unsupported")
    raise ContractViolation("BASE_OR_PREIMAGE_DRIFT", "tracked mode unsupported")


def _tree_oid_from_entries(entries: list[tuple[bytes, int, bytes]]) -> str:
    root: dict[bytes, Any] = {}
    for path, mode, oid in entries:
        parts = path.split(b"/")
        if any(part in (b"", b".", b"..") for part in parts):
            raise ContractViolation("BASE_OR_PREIMAGE_DRIFT", "tracked path invalid")
        cursor = root
        for component in parts[:-1]:
            current = cursor.get(component)
            if current is None:
                current = {}
                cursor[component] = current
            if not isinstance(current, dict):
                raise ContractViolation("BASE_OR_PREIMAGE_DRIFT", "tracked path prefix conflict")
            cursor = current
        if parts[-1] in cursor:
            raise ContractViolation("BASE_OR_PREIMAGE_DRIFT", "duplicate tracked path")
        cursor[parts[-1]] = (mode, oid)

    def build(node: dict[bytes, Any]) -> bytes:
        material: list[tuple[bytes, bytes]] = []
        for name, value in node.items():
            if isinstance(value, dict):
                child_oid = build(value)
                material.append((name + b"/", b"40000 " + name + b"\0" + child_oid))
            else:
                mode, child_oid = value
                material.append(
                    (name, f"{mode:o}".encode("ascii") + b" " + name + b"\0" + child_oid)
                )
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
            raise ContractViolation("BASE_OR_PREIMAGE_DRIFT", "worktree scan failed") from exc
        for entry in entries:
            relative = os.path.relpath(entry.path, repo_root).replace(os.sep, "/")
            if relative == ".git":
                continue
            try:
                observed = entry.stat(follow_symlinks=False)
            except OSError as exc:
                raise ContractViolation(
                    "BASE_OR_PREIMAGE_DRIFT", "worktree leaf observation failed"
                ) from exc
            if stat.S_ISDIR(observed.st_mode):
                pending.append(entry.path)
            elif stat.S_ISREG(observed.st_mode) or stat.S_ISLNK(observed.st_mode):
                encoded = os.fsencode(relative)
                if encoded in leaves:
                    raise ContractViolation("BASE_OR_PREIMAGE_DRIFT", "duplicate worktree leaf")
                leaves.add(encoded)
            else:
                raise ContractViolation("BASE_OR_PREIMAGE_DRIFT", "untracked special leaf present")
    return leaves


def _index_worktree_tree(repo_root: str, git_dir: str) -> str:
    index = _read_git_file(os.path.join(git_dir, "index"))
    if len(index) < 12 + 20 or hashlib.sha1(index[:-20]).digest() != index[-20:]:
        raise ContractViolation("BASE_OR_PREIMAGE_DRIFT", "Git index checksum invalid")
    if index[:4] != b"DIRC":
        raise ContractViolation("BASE_OR_PREIMAGE_DRIFT", "Git index signature invalid")
    version, count = struct.unpack(">II", index[4:12])
    if version not in (2, 3):
        raise ContractViolation("BASE_OR_PREIMAGE_DRIFT", "Git index version unsupported")
    limit = len(index) - 20
    offset = 12
    previous_path: bytes | None = None
    parsed: list[tuple[bytes, int, bytes]] = []
    root_bytes = os.fsencode(repo_root)
    for _slot in range(count):
        entry_start = offset
        if offset + 62 > limit:
            raise ContractViolation("BASE_OR_PREIMAGE_DRIFT", "Git index entry truncated")
        mode = struct.unpack(">I", index[offset + 24 : offset + 28])[0]
        expected_oid = index[offset + 40 : offset + 60]
        flags = struct.unpack(">H", index[offset + 60 : offset + 62])[0]
        if flags & 0x4000 or ((flags >> 12) & 0x3) != 0:
            raise ContractViolation("BASE_OR_PREIMAGE_DRIFT", "extended or non-stage0 index entry")
        path_start = offset + 62
        path_end = index.find(b"\0", path_start, limit)
        if path_end < 0:
            raise ContractViolation("BASE_OR_PREIMAGE_DRIFT", "Git index path terminator absent")
        path = index[path_start:path_end]
        declared_length = flags & 0x0FFF
        if declared_length != 0x0FFF and declared_length != len(path):
            raise ContractViolation("BASE_OR_PREIMAGE_DRIFT", "Git index path length mismatch")
        if previous_path is not None and path <= previous_path:
            raise ContractViolation("BASE_OR_PREIMAGE_DRIFT", "Git index path order invalid")
        previous_path = path
        raw_entry_size = path_end + 1 - entry_start
        padded_size = (raw_entry_size + 7) & ~7
        offset = entry_start + padded_size
        if offset > limit or any(index[path_end + 1 : offset]):
            raise ContractViolation("BASE_OR_PREIMAGE_DRIFT", "Git index padding invalid")
        components = path.split(b"/")
        if any(component in (b"", b".", b"..") for component in components):
            raise ContractViolation("BASE_OR_PREIMAGE_DRIFT", "Git index path invalid")
        worktree_path = os.path.join(root_bytes, *components)
        actual_oid = _git_blob_oid(worktree_path, mode)
        if actual_oid != expected_oid:
            raise ContractViolation("BASE_OR_PREIMAGE_DRIFT", "tracked worktree blob mismatch")
        parsed.append((path, mode, expected_oid))
    while offset < limit:
        if offset + 8 > limit:
            raise ContractViolation("BASE_OR_PREIMAGE_DRIFT", "Git index extension truncated")
        signature = index[offset : offset + 4]
        size = struct.unpack(">I", index[offset + 4 : offset + 8])[0]
        offset += 8
        if offset + size > limit:
            raise ContractViolation("BASE_OR_PREIMAGE_DRIFT", "Git index extension size invalid")
        if not signature or 97 <= signature[0] <= 122:
            raise ContractViolation("BASE_OR_PREIMAGE_DRIFT", "mandatory Git index extension unsupported")
        offset += size
    if offset != limit:
        raise ContractViolation("BASE_OR_PREIMAGE_DRIFT", "Git index parse did not close")
    if _worktree_leaf_paths(repo_root) != {path for path, _mode, _oid in parsed}:
        raise ContractViolation("BASE_OR_PREIMAGE_DRIFT", "tracked/untracked leaf set mismatch")
    return _tree_oid_from_entries(parsed)


def _actual_git_head_tree(repo_root: str) -> tuple[str, str]:
    """Resolve actual tracked HEAD/tree without git, network, or filesystem writes."""

    if os.path.realpath(repo_root) != repo_root or not os.path.isdir(repo_root):
        raise ContractViolation("BASE_OR_PREIMAGE_DRIFT", "repository root is not canonical")
    git_dir = _git_directory(repo_root)
    common_dir = _git_common_directory(git_dir)
    try:
        head_value = _read_git_file(os.path.join(git_dir, "HEAD"), 4096).decode(
            "ascii", "strict"
        ).strip()
    except UnicodeDecodeError as exc:
        raise ContractViolation("BASE_OR_PREIMAGE_DRIFT", "Git HEAD is not ASCII") from exc
    head_commit = _resolve_git_reference(git_dir, common_dir, head_value)
    index_tree = _index_worktree_tree(repo_root, git_dir)
    commit_tree = _loose_commit_tree(common_dir, head_commit)
    if commit_tree is None:
        commit_tree = _packed_commit_tree(common_dir, head_commit)
    if commit_tree != index_tree:
        raise ContractViolation("BASE_OR_PREIMAGE_DRIFT", "HEAD commit tree and index tree differ")
    return head_commit, index_tree


def _assert_disjoint_private_roots(repo_root: str, runtime_root: str, probe_cwd: str) -> None:
    paths = (repo_root, runtime_root, probe_cwd)
    if any(os.path.realpath(path) != path for path in paths):
        raise ContractViolation("INPUT_SCHEMA_INVALID", "private root locator is not realpath-canonical")
    for index, left in enumerate(paths):
        for right in paths[index + 1 :]:
            try:
                common = os.path.commonpath((left, right))
            except ValueError as exc:
                raise ContractViolation("INPUT_SCHEMA_INVALID", "private roots are incomparable") from exc
            if common in (left, right):
                raise ContractViolation("INPUT_SCHEMA_INVALID", "private roots overlap or contain")


def _source_bindings(repo_root: str) -> dict[str, str]:
    observed: dict[str, str] = {}
    expected_blob_sha1s = dict(ContractV1.REQUIRED_ROLE_BLOB_SHA1S)
    for role, relative_path, expected_sha256, _callable_name in ContractV1.REQUIRED_ROLE_SOURCES:
        source_path = os.path.join(repo_root, *relative_path.split("/"))
        body = _raw_file(source_path)
        if len(body) > _MAX_PROCESS_OUTPUT_BYTES:
            raise ContractViolation(
                "BASE_OR_PREIMAGE_DRIFT", f"{role} source exceeds V1 limit"
            )
        actual_sha256 = hashlib.sha256(body).hexdigest()
        actual_blob_sha1 = hashlib.sha1(
            f"blob {len(body)}\0".encode("ascii") + body
        ).hexdigest()
        if actual_sha256 != expected_sha256:
            raise ContractViolation("BASE_OR_PREIMAGE_DRIFT", f"{role} source identity mismatch")
        if actual_blob_sha1 != expected_blob_sha1s.get(role):
            raise ContractViolation(
                "BASE_OR_PREIMAGE_DRIFT", f"{role} Git blob identity mismatch"
            )
        observed[role] = actual_sha256
    lock_path = os.path.join(repo_root, *ContractV1.LOCK_SOURCE_RELATIVE.split("/"))
    lock_raw_sha256 = _raw_sha256(lock_path)
    if lock_raw_sha256 != ContractV1.LOCK_RAW_SHA256:
        raise ContractViolation("BASE_OR_PREIMAGE_DRIFT", "formal lock raw identity mismatch")
    observed["FORMAL_LOCK_RAW"] = lock_raw_sha256
    ordered_paths_sha256 = canonical_sha256(
        [relative_path for _role, relative_path, _sha256, _name in ContractV1.REQUIRED_ROLE_SOURCES]
    )
    if ordered_paths_sha256 != ContractV1.REQUIRED_ROLE_PATH_ORDERED_SHA256:
        raise ContractViolation("BASE_OR_PREIMAGE_DRIFT", "required role path order mismatch")
    return observed


def _full_root_manifest(root: str) -> str:
    rows: list[dict[str, Any]] = []
    pending = [root]
    while pending:
        directory = pending.pop()
        try:
            with os.scandir(directory) as scanner:
                entries = sorted(scanner, key=lambda item: item.name, reverse=True)
        except OSError as exc:
            raise ContractViolation("ROOT_DRIFT", "full-root inventory failed") from exc
        for entry in entries:
            relative = os.path.relpath(entry.path, root).replace(os.sep, "/")
            try:
                observed = entry.stat(follow_symlinks=False)
            except OSError as exc:
                raise ContractViolation("ROOT_DRIFT", "full-root entry observation failed") from exc
            mode = stat.S_IMODE(observed.st_mode)
            if stat.S_ISDIR(observed.st_mode):
                rows.append({"kind": "directory", "mode": mode, "relative_path": relative})
                pending.append(entry.path)
            elif stat.S_ISREG(observed.st_mode):
                digest = hashlib.sha256()
                size = 0
                try:
                    with open(entry.path, "rb") as source:
                        for block in iter(lambda: source.read(131_072), b""):
                            digest.update(block)
                            size += len(block)
                except OSError as exc:
                    raise ContractViolation("ROOT_DRIFT", "full-root file read failed") from exc
                rows.append(
                    {
                        "kind": "regular",
                        "mode": mode,
                        "relative_path": relative,
                        "size": size,
                        "raw_sha256": digest.hexdigest(),
                    }
                )
            elif stat.S_ISLNK(observed.st_mode):
                try:
                    target = os.readlink(entry.path).encode("utf-8", "surrogateescape")
                except OSError as exc:
                    raise ContractViolation("ROOT_DRIFT", "full-root symlink read failed") from exc
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


def _sanitized_environment() -> dict[str, str]:
    return {
        "LANG": "C.UTF-8",
        "LC_ALL": "C.UTF-8",
        "PYTHONDONTWRITEBYTECODE": "1",
        "PYTHONHASHSEED": "0",
        "PYTHONNOUSERSITE": "1",
        "PYTHONUTF8": "1",
        "PYTEST_DISABLE_PLUGIN_AUTOLOAD": "1",
    }


def _completed_process(
    argv: list[str],
    *,
    cwd: str,
    input_bytes: bytes | None,
) -> tuple[int, int, bytes, bytes]:
    process: Any | None = None
    try:
        process = _popen_factory(
            argv,
            cwd=cwd,
            env=_sanitized_environment(),
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            close_fds=True,
        )
        process_id = process.pid
        if type(process_id) is not int or process_id <= 0 or process_id == os.getpid():
            raise ContractViolation(
                "PROCESS_CARDINALITY_OR_LAUNCH_INVALID", "child PID is invalid"
            )
        stdout, stderr = process.communicate(
            input=input_bytes, timeout=_PROCESS_TIMEOUT_SECONDS
        )
    except subprocess.TimeoutExpired as exc:
        if process is not None:
            try:
                process.kill()
                process.communicate()
            except Exception:
                pass
        raise ContractViolation(
            "PROCESS_CARDINALITY_OR_LAUNCH_INVALID", "single process timed out"
        ) from exc
    except ContractViolation:
        raise
    except (OSError, subprocess.SubprocessError, AttributeError, TypeError) as exc:
        raise ContractViolation(
            "PROCESS_CARDINALITY_OR_LAUNCH_INVALID", "single process launch failed"
        ) from exc
    if not isinstance(stdout, bytes) or not isinstance(stderr, bytes):
        raise ContractViolation("PROCESS_CARDINALITY_OR_LAUNCH_INVALID", "process output is not bytes")
    if len(stdout) > _MAX_PROCESS_OUTPUT_BYTES or len(stderr) > _MAX_PROCESS_OUTPUT_BYTES:
        raise ContractViolation("PROCESS_CARDINALITY_OR_LAUNCH_INVALID", "process output exceeds limit")
    returncode = process.returncode
    if type(returncode) is not int:
        raise ContractViolation("PROCESS_CARDINALITY_OR_LAUNCH_INVALID", "return code is absent")
    return process_id, returncode, stdout, stderr


def _run_role(
    role: str,
    module_name: str,
    request_bytes: bytes,
    executable: str,
    repo_root: str,
) -> tuple[dict[str, Any], bytes, int]:
    process_id, returncode, stdout, stderr = _completed_process(
        [
            executable,
            "-I",
            "-B",
            "-c",
            _ROLE_LAUNCH_PROGRAM,
            repo_root,
            module_name,
        ],
        cwd=repo_root,
        input_bytes=request_bytes,
    )
    if returncode != 0 or stderr != b"":
        raise ContractViolation(f"{role.upper()}_INVALID", "role process did not close VALID")
    try:
        value = read_strict_json(io.BytesIO(stdout))
    except ContractViolation as exc:
        raise ContractViolation(f"{role.upper()}_INVALID", "role output schema invalid") from exc
    result = validate_role_result(value, role)
    if result["process_id"] != process_id:
        raise ContractViolation(
            "PROCESS_CARDINALITY_OR_LAUNCH_INVALID", "role-reported PID mismatch"
        )
    return result, stdout, process_id


def _assert_probe_ancestors_config_free(probe_cwd: str) -> None:
    forbidden = (".git", "pytest.ini", "pyproject.toml", "tox.ini", "setup.cfg")
    cursor = probe_cwd
    while True:
        for name in forbidden:
            candidate = os.path.join(cursor, name)
            try:
                os.lstat(candidate)
            except FileNotFoundError:
                continue
            except OSError as exc:
                raise ContractViolation(
                    "PROBE_OR_SMOKE_INVALID", "probe ancestor cannot prove config absence"
                ) from exc
            raise ContractViolation(
                "PROBE_OR_SMOKE_INVALID", "probe ancestor contains repository/config control"
            )
        parent = os.path.dirname(cursor)
        if parent == cursor:
            return
        cursor = parent


def _run_pytest_probe(executable: str, probe_cwd: str) -> tuple[str, bytes, bytes, int]:
    _assert_probe_ancestors_config_free(probe_cwd)
    try:
        if os.path.realpath(probe_cwd) != probe_cwd or not os.path.isdir(probe_cwd):
            raise ContractViolation("PROBE_OR_SMOKE_INVALID", "probe cwd is absent")
        with os.scandir(probe_cwd) as scanner:
            if next(scanner, None) is not None:
                raise ContractViolation("PROBE_OR_SMOKE_INVALID", "probe cwd is not empty")
    except OSError as exc:
        raise ContractViolation("PROBE_OR_SMOKE_INVALID", "probe cwd observation failed") from exc
    process_id, returncode, stdout, stderr = _completed_process(
        [executable, "-I", "-B", "-m", "pytest", "--version"],
        cwd=probe_cwd,
        input_bytes=None,
    )
    _assert_probe_ancestors_config_free(probe_cwd)
    try:
        if os.path.realpath(probe_cwd) != probe_cwd or not os.path.isdir(probe_cwd):
            raise ContractViolation(
                "PROBE_OR_SMOKE_INVALID", "pytest probe changed the cwd locator"
            )
        with os.scandir(probe_cwd) as scanner:
            if next(scanner, None) is not None:
                raise ContractViolation(
                    "PROBE_OR_SMOKE_INVALID", "pytest probe changed the empty cwd"
                )
    except OSError as exc:
        raise ContractViolation("PROBE_OR_SMOKE_INVALID", "probe cwd postcheck failed") from exc
    try:
        reported = stdout.decode("utf-8", "strict").strip()
    except UnicodeDecodeError as exc:
        raise ContractViolation("PROBE_OR_SMOKE_INVALID", "pytest output is not UTF-8") from exc
    if (
        returncode != 0
        or stderr != b""
        or reported != f"pytest {ContractV1.EXPECTED_PYTEST_VERSION}"
    ):
        raise ContractViolation("PROBE_OR_SMOKE_INVALID", "pytest version probe invalid")
    return ContractV1.EXPECTED_PYTEST_VERSION, stdout, stderr, process_id


def _run_role_smoke(
    executable: str, repo_root: str
) -> tuple[dict[str, int], bytes, int]:
    process_id, returncode, stdout, stderr = _completed_process(
        [executable, "-I", "-B", "-c", _ROLE_SMOKE_PROGRAM, repo_root],
        cwd=repo_root,
        input_bytes=None,
    )
    if returncode != 0 or stderr != b"":
        raise ContractViolation("PROBE_OR_SMOKE_INVALID", "required-role smoke failed")
    try:
        value = read_strict_json(io.BytesIO(stdout))
    except ContractViolation as exc:
        raise ContractViolation("PROBE_OR_SMOKE_INVALID", "role smoke output invalid") from exc
    expected = {
        "direct_role_load_count": 3,
        "public_api_call_count": 0,
        "effect_count": 0,
    }
    if value != expected:
        raise ContractViolation("PROBE_OR_SMOKE_INVALID", "role smoke counters invalid")
    return value, stdout, process_id


def _readiness_preimage_bytes(fields: dict[str, Any]) -> bytes:
    if tuple(fields) != ContractV1.READINESS_PREIMAGE_FIELDS:
        raise ContractViolation("INTERNAL_FAIL_CLOSED", "readiness field order is not exact40")
    rendered: list[str] = []
    for key in ContractV1.READINESS_PREIMAGE_FIELDS:
        value = fields[key]
        if isinstance(value, bool):
            scalar = "true" if value else "false"
        elif type(value) is int:
            scalar = str(value)
        elif isinstance(value, str):
            scalar = value
        else:
            raise ContractViolation("INTERNAL_FAIL_CLOSED", "readiness value is not scalar")
        if not scalar or "\n" in scalar or "\r" in scalar:
            raise ContractViolation("INTERNAL_FAIL_CLOSED", "readiness scalar is invalid")
        rendered.append(f"{key}={scalar}")
    return "\n".join(rendered).encode("utf-8")


def orchestrate(request: dict[str, Any]) -> dict[str, Any]:
    """Reject library-mode admission; only the unmodified CLI may grant credit."""

    del request
    raise ContractViolation(
        "CURRENT_AUTHORITY_STOP", "library invocation is not a credit-bearing admission"
    )


def _orchestrate_cli(request: dict[str, Any], admission_token: object) -> dict[str, Any]:
    """Perform the official one-shot CLI admission in the fixed exact4 process order."""

    if admission_token is not _CLI_ADMISSION_TOKEN:
        raise ContractViolation("CURRENT_AUTHORITY_STOP", "official CLI token is absent")
    _assert_official_cli_context()
    request = validate_request(request)
    repo_root = _repo_root()
    root = request["materialization"]["root"]
    probe_cwd = request["materialization"]["probe_cwd"]
    executable = request["runtime"]["executable"]
    _assert_disjoint_private_roots(repo_root, root, probe_cwd)
    expected_head_tree = (
        request["frozen"]["mashos_api_commit"],
        request["frozen"]["mashos_api_tree"],
    )
    pre_head_tree = _actual_git_head_tree(repo_root)
    if pre_head_tree != expected_head_tree:
        raise ContractViolation("BASE_OR_PREIMAGE_DRIFT", "actual Git HEAD/tree mismatch")
    source_bindings_pre = _source_bindings(repo_root)
    pre_root_sha256 = _full_root_manifest(root)
    expected_root_sha256 = request["materialization"][
        "expected_full_root_manifest_sha256"
    ]
    if pre_root_sha256 != expected_root_sha256:
        raise ContractViolation("BASE_OR_PREIMAGE_DRIFT", "expected runtime root mismatch")
    request_bytes = canonical_json_bytes(request)
    stage_ledger: list[dict[str, Any]] = []

    owner, owner_output, owner_pid = _run_role(
        "owner", _OWNER_MODULE, request_bytes, executable, repo_root
    )
    stage_ledger.append({"stage": "OWNER", "process_id": owner_pid})
    pytest_version, pytest_stdout, pytest_stderr, pytest_pid = _run_pytest_probe(
        executable, probe_cwd
    )
    stage_ledger.append({"stage": "PYTEST_VERSION_PROBE", "process_id": pytest_pid})
    smoke, smoke_output, smoke_pid = _run_role_smoke(executable, repo_root)
    stage_ledger.append({"stage": "REQUIRED_ROLE_SMOKE", "process_id": smoke_pid})
    if _source_bindings(repo_root) != source_bindings_pre:
        raise ContractViolation("ROOT_DRIFT", "required role sources changed during smoke")
    independent, independent_output, independent_pid = _run_role(
        "independent", _INDEPENDENT_MODULE, request_bytes, executable, repo_root
    )
    stage_ledger.append({"stage": "INDEPENDENT", "process_id": independent_pid})

    expected_stages = (
        "OWNER",
        "PYTEST_VERSION_PROBE",
        "REQUIRED_ROLE_SMOKE",
        "INDEPENDENT",
    )
    if (
        tuple(item["stage"] for item in stage_ledger) != expected_stages
        or len(stage_ledger) != 4
        or len({item["process_id"] for item in stage_ledger}) != 4
        or any(item["process_id"] == os.getpid() for item in stage_ledger)
    ):
        raise ContractViolation(
            "PROCESS_CARDINALITY_OR_LAUNCH_INVALID", "process stage ledger is not exact4"
        )
    if ">".join(item["stage"] for item in stage_ledger) != _EXECUTION_ORDER:
        raise ContractViolation("INTERNAL_FAIL_CLOSED", "process execution order drift")
    owner_identity = owner["runtime_identity_exact19"]
    independent_identity = independent["runtime_identity_exact19"]
    if owner_identity != independent_identity:
        raise ContractViolation("DERIVATION_DIVERGENCE", "runtime exact19 does not fully match")
    if owner["manifest_rows"] != independent["manifest_rows"]:
        raise ContractViolation("DERIVATION_DIVERGENCE", "canonical manifest rows diverged")
    if owner["distribution_closures"] != independent["distribution_closures"]:
        raise ContractViolation("DERIVATION_DIVERGENCE", "distribution closures diverged")
    if owner["canonical_diagnostic"] != independent["canonical_diagnostic"]:
        raise ContractViolation("DERIVATION_DIVERGENCE", "canonical diagnostics diverged")
    if owner_identity["materialization_event_id"] != request["materialization"]["event_id"]:
        raise ContractViolation("FRESHNESS_UNPROVED", "materialization event binding diverged")
    post_root_sha256 = _full_root_manifest(root)
    post_head_tree = _actual_git_head_tree(repo_root)
    if (
        pre_root_sha256 != post_root_sha256
        or post_root_sha256 != expected_root_sha256
        or owner_identity["full_runtime_root_manifest_sha256"] != pre_root_sha256
        or independent_identity["full_runtime_root_manifest_sha256"] != pre_root_sha256
    ):
        raise ContractViolation("ROOT_DRIFT", "runtime root changed during admission")
    if post_head_tree != pre_head_tree or post_head_tree != expected_head_tree:
        raise ContractViolation("ROOT_DRIFT", "Git HEAD/tree changed during admission")
    if _source_bindings(repo_root) != source_bindings_pre:
        raise ContractViolation("ROOT_DRIFT", "required role sources changed during admission")

    tools_root = os.path.dirname(__file__)
    contract_path = os.path.join(
        tools_root, "emlis_nls_v3_s11_g4b_runtime_admission_contract_v1.py"
    )
    owner_path = os.path.join(
        tools_root, "emlis_nls_v3_s11_g4b_runtime_admission_owner_v1.py"
    )
    independent_path = os.path.join(
        tools_root, "emlis_nls_v3_s11_g4b_runtime_admission_independent_v1.py"
    )
    exact19_sha256 = canonical_sha256(owner_identity)
    diagnostic_sha256 = canonical_sha256(owner["canonical_diagnostic"])
    readiness_fields: dict[str, Any] = {}
    for key, value in (
        ("schema_version", _READINESS_SCHEMA),
        ("authority_id", request["authority_id"]),
        ("technical_contract_raw_sha256", _raw_sha256(contract_path)),
        ("owner_process_body_raw_sha256", _raw_sha256(owner_path)),
        ("independent_process_body_raw_sha256", _raw_sha256(independent_path)),
        ("comparator_schema", "NLS_V3_INSTALLED_FILE_MANIFEST_CANONICAL_V1"),
        ("comparator_expected_sha256", ContractV1.INSTALLED_MANIFEST_COMPARATOR_SHA256),
        ("accepted_wheel_count", 5),
        ("accepted_wheel_manifest_sha256", ContractV1.WHEEL_MANIFEST_SHA256),
        ("materialization_event_id", request["materialization"]["event_id"]),
        ("logical_runtime_id", owner_identity["logical_runtime_id"]),
        ("runtime_content_identity", owner_identity["runtime_content_identity"]),
        ("runtime_root_identity_sha256", owner_identity["runtime_root_identity_sha256"]),
        ("runtime_instance_observation_id", owner_identity["runtime_instance_observation_id"]),
        ("execution_order", _EXECUTION_ORDER),
        ("owner_process_count", sum(item["stage"] == "OWNER" for item in stage_ledger)),
        ("owner_result", "VALID"),
        ("owner_output_sha256", hashlib.sha256(owner_output).hexdigest()),
        (
            "pytest_version_probe_count",
            sum(item["stage"] == "PYTEST_VERSION_PROBE" for item in stage_ledger),
        ),
        ("pytest_version", pytest_version),
        ("pytest_version_stdout_sha256", hashlib.sha256(pytest_stdout).hexdigest()),
        ("pytest_version_stderr_bytes", len(pytest_stderr)),
        (
            "required_role_smoke_process_count",
            sum(item["stage"] == "REQUIRED_ROLE_SMOKE" for item in stage_ledger),
        ),
        (
            "required_role_smoke_inline_program_observed_sha256",
            hashlib.sha256(_ROLE_SMOKE_PROGRAM.encode("utf-8")).hexdigest(),
        ),
        ("required_role_smoke_program_preimage_class", _SMOKE_PREIMAGE_CLASS),
        ("required_role_smoke_output_sha256", hashlib.sha256(smoke_output).hexdigest()),
        ("required_role_direct_load_count", smoke["direct_role_load_count"]),
        ("required_role_public_api_call_count", smoke["public_api_call_count"]),
        ("required_role_effect_count", smoke["effect_count"]),
        (
            "independent_process_count",
            sum(item["stage"] == "INDEPENDENT" for item in stage_ledger),
        ),
        ("independent_result", "VALID"),
        ("independent_output_sha256", hashlib.sha256(independent_output).hexdigest()),
        ("runtime_identity_exact19_full_match", True),
        ("runtime_identity_exact19_sha256", exact19_sha256),
        ("canonical_diagnostic_full_match", True),
        ("canonical_diagnostic_sha256", diagnostic_sha256),
        ("current_comparator_match", True),
        ("installed_file_manifest_sha256", owner["manifest_sha256"]),
        ("full_runtime_root_manifest_sha256", pre_root_sha256),
        ("full_runtime_root_pre_post_match", True),
    ):
        readiness_fields[key] = value
    readiness_id = hashlib.sha256(_readiness_preimage_bytes(readiness_fields)).hexdigest()
    handoff_binding = canonical_sha256(
        {
            "schema_version": ContractV1.HANDOFF_SCHEMA,
            "handoff_claim": ContractV1.HANDOFF_CLAIM,
            "private_locator_holder": "CALLER_REQUEST_CONTEXT",
            "consumer_observed": False,
            "observation_session_id": request["observation_session_id"],
            "receiver_session_id": request["handoff"]["receiver_session_id"],
            "receiver_nonce": request["handoff"]["receiver_nonce"],
            "mashos_api_commit": request["frozen"]["mashos_api_commit"],
            "mashos_api_tree": request["frozen"]["mashos_api_tree"],
            "freshness_evidence_class": ContractV1.FRESHNESS_EVIDENCE_CLASS,
            "freshness_claim_limit": ContractV1.FRESHNESS_CLAIM_LIMIT,
            "materialization_event_id": request["materialization"]["event_id"],
            "runtime_root_locator_sha256": runtime_root_locator_sha256(root),
            "runtime_executable_locator_sha256": runtime_executable_locator_sha256(
                executable
            ),
            "expected_full_root_manifest_sha256": expected_root_sha256,
            "runtime_instance_observation_id": owner_identity["runtime_instance_observation_id"],
            "runtime_readiness_observation_id": readiness_id,
            "entrypoint_control_identity_sha256": owner_identity[
                "entrypoint_control_identity_sha256"
            ],
        }
    )
    return validate_public_result({
        "schema_version": ContractV1.PUBLIC_RESULT_SCHEMA,
        "method_id": ContractV1.METHOD_ID,
        "status": "VALID",
        "terminal": "RUNTIME_READY_CURRENT_SESSION_STOP",
        "checks_completed": list(ContractV1.CHECK_ORDER),
        "primary_outcome": "TECHNICAL_CREDIT",
        "runtime_ready": True,
        "gate_b_closed": True,
        "runtime_readiness_observation_id": readiness_id,
        "runtime_instance_observation_id": owner_identity["runtime_instance_observation_id"],
        "installed_file_manifest_sha256": owner["manifest_sha256"],
        "runtime_identity_exact19_sha256": exact19_sha256,
        "canonical_diagnostic_sha256": diagnostic_sha256,
        "handoff_state": "HANDOFF_BOUND_CURRENT_SESSION",
        "handoff_binding_sha256": handoff_binding,
        "handoff_consumed": False,
        "gate_c_authorized": False,
        "target_execution_count": 0,
        "automatic_progression": False,
    })


def _public_stop(code: str) -> dict[str, Any]:
    terminal = code if code in ContractV1.STOP_CODES else "INTERNAL_FAIL_CLOSED"
    return validate_public_result({
        "schema_version": ContractV1.PUBLIC_RESULT_SCHEMA,
        "method_id": ContractV1.METHOD_ID,
        "status": "STOP",
        "terminal": terminal,
        "primary_outcome": "BLOCKER_NARROWED",
        "runtime_ready": False,
        "gate_b_closed": False,
        "handoff_state": "NOT_BOUND",
        "handoff_consumed": False,
        "gate_c_authorized": False,
        "target_execution_count": 0,
        "automatic_progression": False,
    })


def main() -> int:
    try:
        _assert_official_cli_context()
        result = _orchestrate_cli(
            read_strict_json(sys.stdin.buffer), _CLI_ADMISSION_TOKEN
        )
    except ContractViolation as exc:
        write_strict_json(_public_stop(exc.code), sys.stdout.buffer)
        return 2
    except Exception:
        write_strict_json(_public_stop("INTERNAL_FAIL_CLOSED"), sys.stdout.buffer)
        return 3
    write_strict_json(result, sys.stdout.buffer)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
