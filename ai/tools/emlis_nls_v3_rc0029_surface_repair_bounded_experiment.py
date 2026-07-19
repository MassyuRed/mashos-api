#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

"""Run bounded, private-only diagnostics for the rc0029 experiment.

The baseline command preserves the frozen rc0027 default-value projection.
The E3 and E4 commands consume only the disconnected rc0029 private runtime.
Body-bearing material and Product Read inputs are written only to an existing,
caller-owned 0700 directory outside the repository.  Companion receipts
contain only identifiers, dispositions, counts, hashes, and closed codes.
"""

import argparse
from contextlib import redirect_stderr, redirect_stdout
from dataclasses import fields, is_dataclass
import hashlib
import io
import json
import os
from pathlib import Path
import re
import stat as stat_module
import sys
from typing import Any, Mapping, Sequence


AI_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = AI_ROOT.parent.resolve()
SERVICES = AI_ROOT / "services" / "ai_inference"
HELPERS = AI_ROOT / "tests" / "helpers"
TOOLS = AI_ROOT / "tools"
for entry in (SERVICES, HELPERS, TOOLS):
    if str(entry) not in sys.path:
        sys.path.insert(0, str(entry))


_BATCH_PATH = (
    AI_ROOT / "tests" / "fixtures" / "emlis_nls_v3" / "generated"
    / "batch_001.jsonl"
)
_BATCH_MANIFEST_PATH = _BATCH_PATH.with_name("batch_001_manifest.json")
_COVERAGE_MATRIX_PATH = _BATCH_PATH.with_name("batch_001_coverage_matrix.json")
_DUPLICATE_REPORT_PATH = _BATCH_PATH.with_name("batch_001_duplicate_report.json")
_CYCLE_ROOT = AI_ROOT / "tests" / "fixtures" / "emlis_nls_v3" / "cycle_001"
_RC0026_DEPENDENCY_PATH = _CYCLE_ROOT / "cycle001_dependency_manifest_rc0026.json"
_RC0027_DEPENDENCY_PATH = _CYCLE_ROOT / "cycle001_dependency_manifest_rc0027.json"
_RC0028_DOWNSTREAM_DEPENDENCY_PATH = (
    _CYCLE_ROOT
    / "cycle001_dependency_manifest_rc0028_downstream_experiment.json"
)
_RC0029_SURFACE_REPAIR_DEPENDENCY_PATH = (
    _CYCLE_ROOT
    / "cycle001_dependency_manifest_rc0029_surface_repair_experiment.json"
)
_REPRESENTATIVE8_PATH = _CYCLE_ROOT / "rc0029_representative8_body_free.json"

_PRIVATE_FILENAME = "rc0027_default_baseline_private.json"
_BODY_FREE_FILENAME = "rc0027_default_baseline_body_free_receipt.json"
_PRIVATE_SCHEMA = (
    "cocolon.emlis.nls_v3.rc0029.rc0027_default_baseline.private.v1"
)
_BODY_FREE_SCHEMA = (
    "cocolon.emlis.nls_v3.rc0029.rc0027_default_baseline.body_free.v1"
)
_E3_PRIVATE_FILENAME = "rc0029_e3_representative8_private.json"
_E3_BODY_FREE_FILENAME = (
    "rc0029_e3_representative8_body_free_receipt.json"
)
_E4_PRIVATE_FILENAME = "rc0029_e4_frozen100_private.json"
_E4_BODY_FREE_FILENAME = "rc0029_e4_frozen100_body_free_receipt.json"
_E3_PRIVATE_SCHEMA = (
    "cocolon.emlis.nls_v3.rc0029.e3_representative8.private.v1"
)
_E3_BODY_FREE_SCHEMA = (
    "cocolon.emlis.nls_v3.rc0029.e3_representative8.body_free.v1"
)
_E4_PRIVATE_SCHEMA = (
    "cocolon.emlis.nls_v3.rc0029.e4_frozen100.private.v1"
)
_E4_BODY_FREE_SCHEMA = (
    "cocolon.emlis.nls_v3.rc0029.e4_frozen100.body_free.v1"
)
_REPRESENTATIVE8_SCHEMA = (
    "cocolon.emlis.nls_v3.rc0029.representative8.body_free.v1"
)
_E3_PRODUCT_READ_AUTHORIZATION_SCHEMA = (
    "cocolon.emlis.nls_v3.rc0029.e3_product_read_authorization."
    "body_free.v1"
)
_REPRESENTATIVE8_SHA256 = (
    "0c3fa4e078dcbb27c91989798426e8ee4c2bf7acc9424eee3488198e4f52d0fc"
)
_RC0027_FROZEN_DEPENDENCY_MANIFEST_SHA256 = (
    "ab87802b6a9019fccedd5bad3bd31e97dcc77f471a35a1136a8c717c308df69b"
)
_RC0027_FROZEN_SOURCE_CLOSURE_SHA256 = (
    "1214bb6c586a0aecbb3f7d6b251613c9b05e190057aa276d5c29a045be538dc7"
)
_REPRESENTATIVE8_CASE_IDS = (
    "nls3s_b001_0001",
    "nls3s_b001_0002",
    "nls3s_b001_0009",
    "nls3s_b001_0019",
    "nls3s_b001_0035",
    "nls3s_b001_0043",
    "nls3s_b001_0063",
    "nls3s_b001_0100",
)
_RC0027_SELECTED_CASE_IDS = frozenset(
    {
        "nls3s_b001_0001",
        "nls3s_b001_0002",
        "nls3s_b001_0003",
        "nls3s_b001_0004",
        "nls3s_b001_0005",
        "nls3s_b001_0006",
        "nls3s_b001_0007",
        "nls3s_b001_0009",
        "nls3s_b001_0010",
        "nls3s_b001_0011",
        "nls3s_b001_0012",
        "nls3s_b001_0013",
        "nls3s_b001_0014",
        "nls3s_b001_0016",
        "nls3s_b001_0017",
        "nls3s_b001_0019",
        "nls3s_b001_0020",
        "nls3s_b001_0023",
        "nls3s_b001_0025",
        "nls3s_b001_0026",
        "nls3s_b001_0027",
        "nls3s_b001_0028",
        "nls3s_b001_0029",
        "nls3s_b001_0030",
        "nls3s_b001_0033",
        "nls3s_b001_0035",
        "nls3s_b001_0036",
        "nls3s_b001_0037",
        "nls3s_b001_0040",
        "nls3s_b001_0043",
        "nls3s_b001_0044",
        "nls3s_b001_0045",
        "nls3s_b001_0046",
        "nls3s_b001_0047",
        "nls3s_b001_0048",
        "nls3s_b001_0049",
        "nls3s_b001_0050",
        "nls3s_b001_0053",
        "nls3s_b001_0055",
        "nls3s_b001_0056",
        "nls3s_b001_0063",
        "nls3s_b001_0067",
        "nls3s_b001_0071",
        "nls3s_b001_0075",
        "nls3s_b001_0078",
        "nls3s_b001_0079",
        "nls3s_b001_0085",
        "nls3s_b001_0087",
        "nls3s_b001_0089",
        "nls3s_b001_0090",
        "nls3s_b001_0094",
        "nls3s_b001_0095",
        "nls3s_b001_0096",
        "nls3s_b001_0098",
        "nls3s_b001_0099",
        "nls3s_b001_0100",
    }
)
_EXPECTED_CASE_COUNT = 100
_ALLOWED_DISPOSITIONS = frozenset(
    {"selected", "no_valid_candidate", "fail_close"}
)
_EXPECTED_DISPOSITION_COUNTS = {
    "selected": 56,
    "no_valid_candidate": 2,
    "fail_close": 42,
}
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_CASE_ID_RE = re.compile(r"^nls3s_b001_[0-9]{4}$")
_STOP_CODE_RE = re.compile(r"^[A-Z][A-Z0-9_]{2,95}$")


class BoundedExperimentStop(RuntimeError):
    """A body-free, path-free STOP result."""

    def __init__(self, code: str) -> None:
        if type(code) is not str or _STOP_CODE_RE.fullmatch(code) is None:
            code = "RC0029_BOUNDED_EXPERIMENT_STOP"
        self.code = code
        super().__init__(code)


class _ClosedArgumentParser(argparse.ArgumentParser):
    def error(self, message: str) -> None:
        del message
        raise BoundedExperimentStop("RC0029_CLI_ARGUMENT_REJECTED")


def _stop(code: str) -> None:
    raise BoundedExperimentStop(code)


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _sha256_file(path: Path) -> str:
    try:
        return _sha256_bytes(path.read_bytes())
    except Exception:
        _stop("RC0029_FROZEN_SOURCE_UNAVAILABLE")


def _canonical_json_bytes(value: Any) -> bytes:
    try:
        return json.dumps(
            value,
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        ).encode("utf-8", errors="strict") + b"\n"
    except Exception:
        _stop("RC0029_PRIVATE_PROJECTION_NOT_CANONICAL")


def _exact_value_projection(
    value: Any,
    path: str = "$",
    *,
    allow_float: bool = False,
) -> Any:
    """Preserve private runtime values and their container/dataclass types."""

    if is_dataclass(value) and not isinstance(value, type):
        return {
            "kind": "dataclass",
            "type": f"{type(value).__module__}.{type(value).__qualname__}",
            "fields": {
                field.name: _exact_value_projection(
                    getattr(value, field.name),
                    f"{path}.{field.name}",
                    allow_float=allow_float,
                )
                for field in fields(value)
            },
        }
    if isinstance(value, tuple) and hasattr(type(value), "_fields"):
        names = getattr(type(value), "_fields", ())
        if (
            type(names) is not tuple
            or any(type(name) is not str for name in names)
        ):
            _stop("RC0029_PRIVATE_PROJECTION_TYPE_REJECTED")
        return {
            "kind": "named_tuple",
            "type": f"{type(value).__module__}.{type(value).__qualname__}",
            "fields": {
                name: _exact_value_projection(
                    getattr(value, name),
                    f"{path}.{name}",
                    allow_float=allow_float,
                )
                for name in names
            },
        }
    if isinstance(value, Mapping):
        projected: dict[str, Any] = {}
        for key, child in value.items():
            if type(key) is not str:
                _stop("RC0029_PRIVATE_PROJECTION_KEY_REJECTED")
            projected[key] = _exact_value_projection(
                child,
                f"{path}.{key}",
                allow_float=allow_float,
            )
        return projected
    if type(value) is list:
        return [
            _exact_value_projection(
                child,
                f"{path}[{index}]",
                allow_float=allow_float,
            )
            for index, child in enumerate(value)
        ]
    if type(value) is tuple:
        return {
            "kind": "tuple",
            "items": [
                _exact_value_projection(
                    child,
                    f"{path}[{index}]",
                    allow_float=allow_float,
                )
                for index, child in enumerate(value)
            ],
        }
    if type(value) in {set, frozenset} and allow_float:
        projected_items = [
            _exact_value_projection(
                child,
                f"{path}[]",
                allow_float=True,
            )
            for child in value
        ]
        projected_items.sort(
            key=lambda item: json.dumps(
                item,
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
            )
        )
        return {
            "kind": "frozenset" if type(value) is frozenset else "set",
            "items": projected_items,
        }
    if type(value) is bytes:
        return {"kind": "bytes", "hex": value.hex()}
    if type(value) is float and allow_float:
        if value != value or value in {float("inf"), float("-inf")}:
            _stop("RC0029_PRIVATE_PROJECTION_TYPE_REJECTED")
        return {"kind": "float", "hex": value.hex()}
    if value is None or type(value) in {bool, int, str}:
        return value
    _stop("RC0029_PRIVATE_PROJECTION_TYPE_REJECTED")


def _outside_repo(path: Path) -> bool:
    return path != REPO_ROOT and REPO_ROOT not in path.parents


def _open_private_directory(
    path: Path,
    *,
    output_names: tuple[str, str] = (
        _PRIVATE_FILENAME,
        _BODY_FREE_FILENAME,
    ),
) -> int:
    """Open an existing no-symlink 0700 directory and return its dirfd."""

    if (
        not path.is_absolute()
        or any(part in {"", ".", ".."} for part in path.parts[1:])
        or not hasattr(os, "O_DIRECTORY")
        or not hasattr(os, "O_NOFOLLOW")
        or not hasattr(os, "getuid")
    ):
        _stop("RC0029_PRIVATE_DIRECTORY_PREFLIGHT_REJECTED")
    lexical = Path(os.path.abspath(os.fspath(path)))
    try:
        resolved = path.resolve(strict=True)
    except Exception:
        _stop("RC0029_PRIVATE_DIRECTORY_PREFLIGHT_REJECTED")
    if lexical != path or resolved != lexical or not _outside_repo(resolved):
        _stop("RC0029_PRIVATE_DIRECTORY_PREFLIGHT_REJECTED")

    flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW
    if hasattr(os, "O_CLOEXEC"):
        flags |= os.O_CLOEXEC
    descriptor: int | None = None
    try:
        descriptor = os.open(lexical.anchor, flags)
        for component in lexical.parts[1:]:
            following = os.open(component, flags, dir_fd=descriptor)
            os.close(descriptor)
            descriptor = following
        status = os.fstat(descriptor)
        if (
            not stat_module.S_ISDIR(status.st_mode)
            or stat_module.S_IMODE(status.st_mode) != 0o700
            or status.st_uid != os.getuid()
        ):
            _stop("RC0029_PRIVATE_DIRECTORY_PREFLIGHT_REJECTED")
        if (
            len(output_names) != 2
            or len(set(output_names)) != 2
            or any(
                type(name) is not str
                or not name
                or name != Path(name).name
                for name in output_names
            )
        ):
            _stop("RC0029_PRIVATE_OUTPUT_NAME_REJECTED")
        for name in output_names:
            try:
                os.stat(name, dir_fd=descriptor, follow_symlinks=False)
            except FileNotFoundError:
                continue
            _stop("RC0029_PRIVATE_OUTPUT_ALREADY_EXISTS")
        return descriptor
    except BoundedExperimentStop:
        if descriptor is not None:
            os.close(descriptor)
        raise
    except Exception:
        if descriptor is not None:
            os.close(descriptor)
        _stop("RC0029_PRIVATE_DIRECTORY_PREFLIGHT_REJECTED")


def _open_exclusive_private_file(directory_fd: int, name: str) -> int:
    flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW
    if hasattr(os, "O_CLOEXEC"):
        flags |= os.O_CLOEXEC
    try:
        descriptor = os.open(name, flags, 0o600, dir_fd=directory_fd)
        os.fchmod(descriptor, 0o600)
        status = os.fstat(descriptor)
        if (
            not stat_module.S_ISREG(status.st_mode)
            or stat_module.S_IMODE(status.st_mode) != 0o600
            or status.st_uid != os.getuid()
            or status.st_nlink != 1
        ):
            os.close(descriptor)
            try:
                os.unlink(name, dir_fd=directory_fd)
            except OSError:
                pass
            _stop("RC0029_PRIVATE_OUTPUT_PREFLIGHT_REJECTED")
        return descriptor
    except BoundedExperimentStop:
        raise
    except FileExistsError:
        _stop("RC0029_PRIVATE_OUTPUT_ALREADY_EXISTS")
    except Exception:
        _stop("RC0029_PRIVATE_OUTPUT_PREFLIGHT_REJECTED")


def _write_private_pair(
    directory_fd: int,
    private_payload: bytes,
    body_free_payload: bytes,
    *,
    private_name: str = _PRIVATE_FILENAME,
    body_free_name: str = _BODY_FREE_FILENAME,
) -> None:
    descriptors: dict[str, int] = {}
    created: list[str] = []
    try:
        for name in (private_name, body_free_name):
            descriptors[name] = _open_exclusive_private_file(directory_fd, name)
            created.append(name)
        for name, payload in (
            (private_name, private_payload),
            (body_free_name, body_free_payload),
        ):
            descriptor = descriptors[name]
            view = memoryview(payload)
            while view:
                written = os.write(descriptor, view)
                if written < 1:
                    _stop("RC0029_PRIVATE_OUTPUT_WRITE_REJECTED")
                view = view[written:]
            os.fsync(descriptor)
        os.fsync(directory_fd)
    except BaseException:
        for descriptor in descriptors.values():
            try:
                os.close(descriptor)
            except OSError:
                pass
        descriptors.clear()
        for name in created:
            try:
                os.unlink(name, dir_fd=directory_fd)
            except OSError:
                pass
        raise
    finally:
        for descriptor in descriptors.values():
            os.close(descriptor)


def _load_frozen_sources() -> tuple[
    list[dict[str, Any]], dict[str, Any], str, dict[str, str]
]:
    """Validate the exact rc0027 and frozen batch authorities."""

    try:
        from emlis_nls_v3_batch_run import load_validated_batch
        from emlis_nls_v3_s2_sample_registry import load_canonical_json
        from emlis_nls_v3_step11_dependency_manifest import (
            assert_current_step11_dependency_manifest,
        )

        samples, batch_manifest = load_validated_batch(
            _BATCH_PATH,
            _BATCH_MANIFEST_PATH,
        )
        before = load_canonical_json(_RC0026_DEPENDENCY_PATH)
        current = load_canonical_json(_RC0027_DEPENDENCY_PATH)
        source_closure = assert_current_step11_dependency_manifest(
            current,
            before_manifest=before,
        )
    except Exception:
        _stop("RC0029_FROZEN_SOURCE_VALIDATION_FAILED")

    if (
        type(samples) is not list
        or len(samples) != _EXPECTED_CASE_COUNT
        or type(batch_manifest) is not dict
        or batch_manifest.get("case_count") != _EXPECTED_CASE_COUNT
        or batch_manifest.get("candidate_version_id") is not None
        or current.get("candidate_version_id") != "nls_v3_rc_0027"
        or type(source_closure) is not str
        or _SHA256_RE.fullmatch(source_closure) is None
    ):
        _stop("RC0029_FROZEN_SOURCE_CONTRACT_MISMATCH")

    source_hashes = {
        "batch_manifest_sha256": _sha256_file(_BATCH_MANIFEST_PATH),
        "corpus_file_sha256": _sha256_file(_BATCH_PATH),
        "corpus_set_commitment": batch_manifest.get("corpus_set_commitment"),
        "coverage_matrix_sha256": _sha256_file(_COVERAGE_MATRIX_PATH),
        "duplicate_report_sha256": _sha256_file(_DUPLICATE_REPORT_PATH),
        "rc0027_dependency_manifest_sha256": _sha256_file(
            _RC0027_DEPENDENCY_PATH
        ),
    }
    if (
        any(
            type(value) is not str or _SHA256_RE.fullmatch(value) is None
            for value in source_hashes.values()
        )
        or source_hashes["corpus_file_sha256"]
        != batch_manifest.get("corpus_file_sha256")
        or source_hashes["coverage_matrix_sha256"]
        != batch_manifest.get("coverage_matrix_sha256")
        or source_hashes["duplicate_report_sha256"]
        != batch_manifest.get("duplicate_report_sha256")
    ):
        _stop("RC0029_FROZEN_SOURCE_HASH_MISMATCH")
    return samples, batch_manifest, source_closure, source_hashes


def _load_rc0029_frozen_sources() -> tuple[
    list[dict[str, Any]], dict[str, Any], str, dict[str, str]
]:
    """Validate E3/E4 inputs without treating append-only rc0029 as drift.

    The baseline capture command deliberately retains its rc0027 live-source
    assertion.  E3/E4 instead consume the exact frozen corpus authorities and
    the recorded rc0027 dependency closure as inputs to the disconnected
    successor experiment; current rc0029 experiment files are not rc0027.
    """

    try:
        from emlis_nls_v3_batch_run import load_validated_batch
        from emlis_nls_v3_s2_sample_registry import load_canonical_json
        from emlis_ai_rc0029_surface_repair_experiment_dependency_manifest_v3 import (
            validate_rc0029_surface_repair_dependency_manifest,
        )

        samples, batch_manifest = load_validated_batch(
            _BATCH_PATH,
            _BATCH_MANIFEST_PATH,
        )
        frozen_dependency = load_canonical_json(_RC0027_DEPENDENCY_PATH)
        parent_dependency = load_canonical_json(
            _RC0028_DOWNSTREAM_DEPENDENCY_PATH
        )
        repair_dependency = load_canonical_json(
            _RC0029_SURFACE_REPAIR_DEPENDENCY_PATH
        )
        repair_issues = (
            validate_rc0029_surface_repair_dependency_manifest(
                repair_dependency,
                parent_manifest=parent_dependency,
                repo_root=REPO_ROOT,
            )
        )
    except Exception:
        _stop("RC0029_FROZEN_SOURCE_VALIDATION_FAILED")

    predecessor_closure = frozen_dependency.get(
        "source_dependency_closure_sha256"
    )
    source_closure = repair_dependency.get(
        "source_dependency_closure_sha256"
    )
    if (
        type(samples) is not list
        or len(samples) != _EXPECTED_CASE_COUNT
        or type(batch_manifest) is not dict
        or batch_manifest.get("case_count") != _EXPECTED_CASE_COUNT
        or batch_manifest.get("candidate_version_id") is not None
        or type(frozen_dependency) is not dict
        or frozen_dependency.get("candidate_version_id") != "nls_v3_rc_0027"
        or predecessor_closure != _RC0027_FROZEN_SOURCE_CLOSURE_SHA256
        or _sha256_file(_RC0027_DEPENDENCY_PATH)
        != _RC0027_FROZEN_DEPENDENCY_MANIFEST_SHA256
        or type(parent_dependency) is not dict
        or type(repair_dependency) is not dict
        or repair_issues != ()
        or type(source_closure) is not str
        or _SHA256_RE.fullmatch(source_closure) is None
    ):
        _stop("RC0029_FROZEN_SOURCE_CONTRACT_MISMATCH")

    source_hashes = {
        "batch_manifest_sha256": _sha256_file(_BATCH_MANIFEST_PATH),
        "corpus_file_sha256": _sha256_file(_BATCH_PATH),
        "corpus_set_commitment": batch_manifest.get("corpus_set_commitment"),
        "coverage_matrix_sha256": _sha256_file(_COVERAGE_MATRIX_PATH),
        "duplicate_report_sha256": _sha256_file(_DUPLICATE_REPORT_PATH),
        "rc0027_dependency_manifest_sha256": _sha256_file(
            _RC0027_DEPENDENCY_PATH
        ),
    }
    if (
        any(
            type(value) is not str or _SHA256_RE.fullmatch(value) is None
            for value in source_hashes.values()
        )
        or source_hashes["corpus_file_sha256"]
        != batch_manifest.get("corpus_file_sha256")
        or source_hashes["coverage_matrix_sha256"]
        != batch_manifest.get("coverage_matrix_sha256")
        or source_hashes["duplicate_report_sha256"]
        != batch_manifest.get("duplicate_report_sha256")
    ):
        _stop("RC0029_FROZEN_SOURCE_HASH_MISMATCH")
    return samples, batch_manifest, source_closure, source_hashes


def _case_commitments(
    manifest: Mapping[str, Any],
    samples: Sequence[Mapping[str, Any]],
) -> dict[str, str]:
    rows = manifest.get("case_commitments")
    if type(rows) is not list or len(rows) != _EXPECTED_CASE_COUNT:
        _stop("RC0029_CASE_COMMITMENT_SET_INVALID")
    result: dict[str, str] = {}
    for row in rows:
        if type(row) is not dict or set(row) != {"case_id", "case_commitment"}:
            _stop("RC0029_CASE_COMMITMENT_SET_INVALID")
        case_id = row["case_id"]
        commitment = row["case_commitment"]
        if (
            type(case_id) is not str
            or _CASE_ID_RE.fullmatch(case_id) is None
            or case_id in result
            or type(commitment) is not str
            or _SHA256_RE.fullmatch(commitment) is None
        ):
            _stop("RC0029_CASE_COMMITMENT_SET_INVALID")
        result[case_id] = commitment
    sample_ids = [sample.get("case_id") for sample in samples]
    if (
        any(type(case_id) is not str for case_id in sample_ids)
        or sample_ids != sorted(result)
        or list(manifest.get("case_ids", ())) != sample_ids
    ):
        _stop("RC0029_CASE_COMMITMENT_SET_INVALID")
    return result


def _load_representative8_fixture(
    *,
    source_hashes: Mapping[str, str],
    commitments: Mapping[str, str],
) -> dict[str, Any]:
    if _sha256_file(_REPRESENTATIVE8_PATH) != _REPRESENTATIVE8_SHA256:
        _stop("RC0029_REPRESENTATIVE8_FIXTURE_HASH_MISMATCH")
    try:
        raw = _REPRESENTATIVE8_PATH.read_bytes()
        value = json.loads(raw.decode("utf-8", errors="strict"))
    except Exception:
        _stop("RC0029_REPRESENTATIVE8_FIXTURE_INVALID")
    if type(value) is not dict or raw != _canonical_json_bytes(value):
        _stop("RC0029_REPRESENTATIVE8_FIXTURE_INVALID")
    expected_top = {
        "body_free",
        "predecessor",
        "representative_count",
        "rows",
        "schema_version",
        "source_fixture_commitments",
    }
    fixture_hashes = value.get("source_fixture_commitments")
    predecessor = value.get("predecessor")
    rows = value.get("rows")
    expected_fixture_hashes = {
        key: source_hashes[key]
        for key in (
            "batch_manifest_sha256",
            "corpus_file_sha256",
            "corpus_set_commitment",
            "coverage_matrix_sha256",
            "duplicate_report_sha256",
        )
    }
    if (
        set(value) != expected_top
        or value.get("body_free") is not True
        or value.get("representative_count") != 8
        or value.get("schema_version") != _REPRESENTATIVE8_SCHEMA
        or predecessor != {
            "rc0028_e3_machine_receipt_sha256": (
                "1a473850fc0e13bcb9288713cbe547635a065ec63f28aab0ff407ba9c7565de4"
            ),
            "rc0028_e3_product_read_stop_receipt_sha256": (
                "923b368124b3f40b62488d2b48749b17c56c4aa2a2f0d6853f8e9aa0d84ca767"
            ),
            "rc0028_representative_fixture_sha256": (
                "6703815684c878b6d00554ad393f23964aa69d7110888e8786fc074faa2d6efd"
            ),
        }
        or fixture_hashes != expected_fixture_hashes
        or type(rows) is not list
        or len(rows) != 8
    ):
        _stop("RC0029_REPRESENTATIVE8_FIXTURE_INVALID")
    expected_metadata = {
        "nls3s_b001_0001": ("control", "PASS"),
        "nls3s_b001_0002": ("control", "PASS"),
        "nls3s_b001_0009": ("control", "MINOR"),
        "nls3s_b001_0019": ("improvement_target", "MAJOR"),
        "nls3s_b001_0035": ("improvement_target", "MAJOR"),
        "nls3s_b001_0043": ("improvement_target", "MAJOR"),
        "nls3s_b001_0063": ("improvement_target", "MAJOR"),
        "nls3s_b001_0100": ("improvement_target", "MAJOR"),
    }
    seen: list[str] = []
    for row in rows:
        if type(row) is not dict or set(row) != {
            "baseline_product_read_severity",
            "case_id",
            "experiment_role",
            "source_case_commitment",
        }:
            _stop("RC0029_REPRESENTATIVE8_FIXTURE_INVALID")
        case_id = row.get("case_id")
        if (
            case_id not in expected_metadata
            or case_id in seen
            or (
                row.get("experiment_role"),
                row.get("baseline_product_read_severity"),
            )
            != expected_metadata[case_id]
            or row.get("source_case_commitment")
            != commitments.get(case_id)
        ):
            _stop("RC0029_REPRESENTATIVE8_FIXTURE_INVALID")
        seen.append(case_id)
    if tuple(seen) != _REPRESENTATIVE8_CASE_IDS:
        _stop("RC0029_REPRESENTATIVE8_FIXTURE_INVALID")
    return value


def _read_private_authorization(path: Path) -> tuple[dict[str, Any], str]:
    if (
        not path.is_absolute()
        or any(part in {"", ".", ".."} for part in path.parts[1:])
        or not hasattr(os, "O_NOFOLLOW")
        or not hasattr(os, "getuid")
    ):
        _stop("RC0029_E3_PRODUCT_READ_AUTHORIZATION_REJECTED")
    lexical = Path(os.path.abspath(os.fspath(path)))
    try:
        resolved = path.resolve(strict=True)
    except Exception:
        _stop("RC0029_E3_PRODUCT_READ_AUTHORIZATION_REJECTED")
    if lexical != path or resolved != lexical or not _outside_repo(resolved):
        _stop("RC0029_E3_PRODUCT_READ_AUTHORIZATION_REJECTED")
    flags = os.O_RDONLY | os.O_NOFOLLOW
    if hasattr(os, "O_CLOEXEC"):
        flags |= os.O_CLOEXEC
    descriptor: int | None = None
    try:
        descriptor = os.open(path, flags)
        status = os.fstat(descriptor)
        if (
            not stat_module.S_ISREG(status.st_mode)
            or stat_module.S_IMODE(status.st_mode) != 0o600
            or status.st_uid != os.getuid()
            or status.st_nlink != 1
            or not 1 <= status.st_size <= 65536
        ):
            _stop("RC0029_E3_PRODUCT_READ_AUTHORIZATION_REJECTED")
        chunks: list[bytes] = []
        remaining = status.st_size
        while remaining:
            chunk = os.read(descriptor, min(remaining, 65536))
            if not chunk:
                _stop("RC0029_E3_PRODUCT_READ_AUTHORIZATION_REJECTED")
            chunks.append(chunk)
            remaining -= len(chunk)
        raw = b"".join(chunks)
    except BoundedExperimentStop:
        raise
    except Exception:
        _stop("RC0029_E3_PRODUCT_READ_AUTHORIZATION_REJECTED")
    finally:
        if descriptor is not None:
            os.close(descriptor)
    try:
        value = json.loads(raw.decode("utf-8", errors="strict"))
    except Exception:
        _stop("RC0029_E3_PRODUCT_READ_AUTHORIZATION_REJECTED")
    if type(value) is not dict or raw != _canonical_json_bytes(value):
        _stop("RC0029_E3_PRODUCT_READ_AUTHORIZATION_REJECTED")
    expected_keys = {
        "body_free",
        "decision",
        "e3_body_free_receipt_sha256",
        "formal_acceptance",
        "product_read_completed",
        "representative_fixture_sha256",
        "reviewed_case_ids",
        "schema_version",
    }
    if (
        set(value) != expected_keys
        or value.get("schema_version")
        != _E3_PRODUCT_READ_AUTHORIZATION_SCHEMA
        or value.get("body_free") is not True
        or not _valid_nonzero_sha256(
            value.get("e3_body_free_receipt_sha256")
        )
        or value.get("representative_fixture_sha256")
        != _REPRESENTATIVE8_SHA256
        or value.get("reviewed_case_ids")
        != list(_REPRESENTATIVE8_CASE_IDS)
        or value.get("product_read_completed") is not True
        or value.get("decision") != "proceed_to_frozen100"
        or value.get("formal_acceptance") != "not_claimed"
    ):
        _stop("RC0029_E3_PRODUCT_READ_AUTHORIZATION_REJECTED")
    return value, _sha256_bytes(raw)


def _valid_nonzero_sha256(value: Any) -> bool:
    return (
        type(value) is str
        and _SHA256_RE.fullmatch(value) is not None
        and value != "0" * 64
    )


def _capture_case_projection(
    sample: Mapping[str, Any],
    *,
    source_case_commitment: str,
    source_closure: str,
) -> tuple[dict[str, Any], dict[str, Any]]:
    try:
        from emlis_ai_step11_natural_surface_matcher_v3 import (
            match_step11_natural_surface,
            parse_step11_natural_surface,
        )
        from emlis_ai_step11_natural_surface_v3 import (
            STEP11_CANDIDATE_VERSION_ID,
        )
        from emlis_ai_step11_runtime_adapter_v3 import (
            Step11RuntimeAdapterError,
            execute_step11_offline_v3,
            validate_step11_runtime_execution,
        )
    except Exception:
        _stop("RC0029_RC0027_ADAPTER_UNAVAILABLE")

    case_id = sample.get("case_id")
    current_input = sample.get("input")
    if (
        type(case_id) is not str
        or _CASE_ID_RE.fullmatch(case_id) is None
        or type(current_input) is not dict
        or STEP11_CANDIDATE_VERSION_ID != "nls_v3_rc_0027"
    ):
        _stop("RC0029_SAMPLE_PROJECTION_REJECTED")
    try:
        execution = execute_step11_offline_v3(
            dict(current_input),
            candidate_version_id=STEP11_CANDIDATE_VERSION_ID,
            source_dependency_closure_sha256=source_closure,
        )
        validation_issues = validate_step11_runtime_execution(execution)
    except Step11RuntimeAdapterError as exc:
        failure_code = getattr(exc, "code", None)
        if (
            type(failure_code) is not str
            or _STOP_CODE_RE.fullmatch(failure_code) is None
        ):
            _stop("RC0029_RC0027_PIPELINE_EXCEPTION")
        private_row = {
            "candidates": [],
            "case_id": case_id,
            "disposition": {
                "bounded_candidate_limit": 12,
                "evaluated_candidate_ids": [],
                "failure_code": failure_code,
                "recovery_attempted": False,
                "selected_candidate_id": None,
                "status": "fail_close",
                "v1_fallback_used": False,
            },
            "source_case_commitment": source_case_commitment,
        }
        body_free_row = {
            "candidate_count": 0,
            "case_id": case_id,
            "disposition": "fail_close",
            "source_case_commitment": source_case_commitment,
        }
        return private_row, body_free_row
    except Exception:
        _stop("RC0029_RC0027_PIPELINE_EXCEPTION")
    if validation_issues:
        _stop("RC0029_RC0027_EXECUTION_VALIDATION_FAILED")

    selection = execution.selection_result
    runtime_status = execution.status
    if runtime_status == "selected":
        disposition = "selected"
    elif runtime_status == "v3_no_valid_candidate":
        disposition = "no_valid_candidate"
    else:
        _stop("RC0029_RC0027_STATUS_UNKNOWN")
    if selection.status != runtime_status:
        _stop("RC0029_RC0027_STATUS_UNKNOWN")
    if (
        disposition == "selected"
        and type(selection.selected_candidate_id) is not str
    ) or (
        disposition == "no_valid_candidate"
        and selection.selected_candidate_id is not None
    ):
        _stop("RC0029_RC0027_DISPOSITION_INVALID")

    candidates = execution.natural_candidates
    candidate_ids = tuple(candidate.candidate_id for candidate in candidates)
    gate_by_id = {gate.candidate_id: gate for gate in selection.gate_results}
    if (
        len(candidates) > 12
        or candidate_ids != selection.evaluated_candidate_ids
        or len(gate_by_id) != len(candidates)
        or set(gate_by_id) != set(candidate_ids)
    ):
        _stop("RC0029_RC0027_BOUNDED_CANDIDATE_SET_INVALID")

    private_candidates: list[dict[str, Any]] = []
    for candidate in candidates:
        try:
            witness = parse_step11_natural_surface(
                candidate.rendered_surface.utf8_bytes
            )
            binding = match_step11_natural_surface(
                witness,
                inventory_result=execution.inventory_result,
                content_plan=execution.content_plan,
                discourse_plan=candidate.discourse_plan,
                current_input=execution.projected_current_input,
            )
        except Exception:
            _stop("RC0029_RC0027_PROJECTION_EXCEPTION")
        private_candidates.append(
            {
                "candidate_id": candidate.candidate_id,
                "hard_gate": _exact_value_projection(
                    gate_by_id[candidate.candidate_id]
                ),
                "parsed_witness": _exact_value_projection(witness),
                "rendered_utf8_bytes": _exact_value_projection(
                    candidate.rendered_surface.utf8_bytes
                ),
                "surface_ast": _exact_value_projection(candidate.surface_ast),
                "verified_binding": _exact_value_projection(binding),
            }
        )

    private_row = {
        "candidates": private_candidates,
        "case_id": case_id,
        "disposition": {
            "bounded_candidate_limit": selection.bounded_candidate_limit,
            "evaluated_candidate_ids": list(selection.evaluated_candidate_ids),
            "recovery_attempted": selection.recovery_attempted,
            "selected_candidate_id": selection.selected_candidate_id,
            "status": disposition,
            "runtime_status": runtime_status,
            "v1_fallback_used": selection.v1_fallback_used,
        },
        "source_case_commitment": source_case_commitment,
    }
    body_free_row = {
        "candidate_count": len(candidates),
        "case_id": case_id,
        "disposition": disposition,
        "source_case_commitment": source_case_commitment,
    }
    return private_row, body_free_row


_RC0029_BODY_FREE_COUNT_KEYS = (
    "base_candidate_count",
    "construction_atom_count",
    "evaluated_candidate_count",
    "experiment_candidate_count",
    "explicit_unknown_atom_count",
    "hard_gate_pass_count",
    "owner_binding_count",
    "rejected_candidate_count",
    "relation_endpoint_atom_count",
    "replan_count",
    "semantic_link_atom_count",
)
_RC0029_BODY_FREE_HASH_KEYS = (
    "lexical_atom_specs_sha256",
    "result_sha256",
    "source_case_commitment",
    "successor_authority_sha256",
    "successor_snapshot_sha256",
    "successor_witness_sha256",
    "surface_catalog_sha256",
)


def _rc0029_fail_close_projection(
    *,
    case_id: str,
    source_case_commitment: str,
    failure_code: str,
) -> tuple[dict[str, Any], dict[str, Any]]:
    if (
        type(failure_code) is not str
        or _STOP_CODE_RE.fullmatch(failure_code) is None
    ):
        _stop("RC0029_RC0029_RUNTIME_UNKNOWN_EXCEPTION")
    counts = {key: 0 for key in _RC0029_BODY_FREE_COUNT_KEYS}
    hashes = {key: None for key in _RC0029_BODY_FREE_HASH_KEYS}
    hashes["source_case_commitment"] = source_case_commitment
    private_row = {
        "case_id": case_id,
        "product_read_input": {
            "selected_final_utf8_bytes": None,
            "status": "not_selected",
        },
        "runtime_error_code": failure_code,
        "runtime_execution": None,
        "source_case_commitment": source_case_commitment,
    }
    body_free_row = {
        "case_id": case_id,
        "closed_codes": [failure_code],
        "counts": counts,
        "disposition": "fail_close",
        "hashes": hashes,
    }
    return private_row, body_free_row


def _run_rc0029_case_projection(
    sample: Mapping[str, Any],
    *,
    source_case_commitment: str,
    source_closure: str,
) -> tuple[dict[str, Any], dict[str, Any]]:
    try:
        from emlis_ai_step11_rc0029_experiment_runtime_adapter_v3 import (
            Step11Rc0029ExperimentRuntimeError,
            execute_step11_rc0029_experiment_private,
            step11_rc0029_experiment_result_material,
            validate_step11_rc0029_experiment_private_execution,
            validate_step11_rc0029_experiment_result,
        )
    except Exception:
        _stop("RC0029_RC0029_PRIVATE_RUNTIME_UNAVAILABLE")

    case_id = sample.get("case_id")
    current_input = sample.get("input")
    if (
        type(case_id) is not str
        or _CASE_ID_RE.fullmatch(case_id) is None
        or type(current_input) is not dict
        or not _valid_nonzero_sha256(source_case_commitment)
        or not _valid_nonzero_sha256(source_closure)
    ):
        _stop("RC0029_SAMPLE_PROJECTION_REJECTED")
    try:
        execution = execute_step11_rc0029_experiment_private(
            dict(current_input),
            case_id=case_id,
            source_case_commitment=source_case_commitment,
            source_dependency_closure_sha256=source_closure,
            candidate_limit=12,
            replan_limit=1,
        )
    except Step11Rc0029ExperimentRuntimeError as exc:
        return _rc0029_fail_close_projection(
            case_id=case_id,
            source_case_commitment=source_case_commitment,
            failure_code=exc.code,
        )
    except Exception:
        _stop("RC0029_RC0029_RUNTIME_UNKNOWN_EXCEPTION")

    if validate_step11_rc0029_experiment_private_execution(execution):
        _stop("RC0029_RC0029_PRIVATE_EXECUTION_INVALID")
    result = execution.body_free_result
    if validate_step11_rc0029_experiment_result(result):
        _stop("RC0029_RC0029_BODY_FREE_RESULT_INVALID")
    material = step11_rc0029_experiment_result_material(result)
    if (
        result.case_id != case_id
        or result.source_case_commitment != source_case_commitment
        or result.source_dependency_closure_sha256 != source_closure
        or result.disposition not in _ALLOWED_DISPOSITIONS
        or material.get("body_free") is not True
    ):
        _stop("RC0029_RC0029_SOURCE_COMMITMENT_MISMATCH")

    counts = {
        key: getattr(result, key) for key in _RC0029_BODY_FREE_COUNT_KEYS
    }
    hashes = {
        key: getattr(result, key) for key in _RC0029_BODY_FREE_HASH_KEYS
    }
    closed_codes = list(result.closed_failure_codes)
    selected_bytes = execution.selected_final_utf8_bytes
    if result.disposition == "selected":
        if type(selected_bytes) is not bytes or not selected_bytes:
            _stop("RC0029_PRODUCT_READ_INPUT_MISSING")
        product_read_input = {
            "selected_final_utf8_bytes": _exact_value_projection(
                selected_bytes,
                allow_float=True,
            ),
            "status": "ready",
        }
    else:
        if selected_bytes is not None:
            _stop("RC0029_PRODUCT_READ_INPUT_DISPOSITION_MISMATCH")
        product_read_input = {
            "selected_final_utf8_bytes": None,
            "status": "not_selected",
        }
    private_row = {
        "case_id": case_id,
        "product_read_input": product_read_input,
        "runtime_error_code": None,
        "runtime_execution": _exact_value_projection(
            execution,
            allow_float=True,
        ),
        "source_case_commitment": source_case_commitment,
    }
    body_free_row = {
        "case_id": case_id,
        "closed_codes": closed_codes,
        "counts": counts,
        "disposition": result.disposition,
        "hashes": hashes,
    }
    return private_row, body_free_row


_RC0029_RECEIPT_TOP_KEYS = {
    "body_free",
    "case_count",
    "cases",
    "disposition_counts",
    "e3_body_free_receipt_sha256",
    "evaluation_stage",
    "formal_acceptance",
    "product_read_authorization_sha256",
    "product_read_status",
    "representative_fixture_sha256",
    "schema_version",
    "source_dependency_closure_sha256",
    "source_fixture_hashes",
}


def validate_rc0029_experiment_body_free_receipt(
    value: Any,
    *,
    expected_stage: str,
) -> tuple[str, ...]:
    """Validate exact E3/E4 accounting without inspecting any body."""

    if expected_stage == "E3_representative8":
        expected_schema = _E3_BODY_FREE_SCHEMA
        expected_case_ids = _REPRESENTATIVE8_CASE_IDS
        expected_product_status = "input_ready_not_reviewed"
        expected_count = 8
    elif expected_stage == "E4_frozen100":
        expected_schema = _E4_BODY_FREE_SCHEMA
        expected_case_ids = tuple(
            f"nls3s_b001_{index:04d}"
            for index in range(1, _EXPECTED_CASE_COUNT + 1)
        )
        expected_product_status = "external_authorization_validated"
        expected_count = _EXPECTED_CASE_COUNT
    else:
        return ("RC0029_RECEIPT_STAGE_INVALID",)
    issues: set[str] = set()
    if type(value) is not dict or set(value) != _RC0029_RECEIPT_TOP_KEYS:
        return ("RC0029_RECEIPT_SHAPE_INVALID",)
    cases = value.get("cases")
    counts = value.get("disposition_counts")
    source_hashes = value.get("source_fixture_hashes")
    if (
        value.get("schema_version") != expected_schema
        or value.get("body_free") is not True
        or value.get("evaluation_stage") != expected_stage
        or value.get("case_count") != expected_count
        or value.get("representative_fixture_sha256")
        != _REPRESENTATIVE8_SHA256
        or value.get("product_read_status") != expected_product_status
        or value.get("formal_acceptance") != "not_claimed"
        or not _valid_nonzero_sha256(
            value.get("source_dependency_closure_sha256")
        )
        or type(source_hashes) is not dict
        or not source_hashes
        or any(not _valid_nonzero_sha256(item) for item in source_hashes.values())
    ):
        issues.add("RC0029_RECEIPT_CONTRACT_INVALID")
    if (
        type(counts) is not dict
        or set(counts) != _ALLOWED_DISPOSITIONS
        or any(
            type(count) is not int or type(count) is bool or count < 0
            for count in counts.values()
        )
        or sum(counts.values()) != expected_count
    ):
        issues.add("RC0029_RECEIPT_ACCOUNTING_INVALID")
    if type(cases) is not list or len(cases) != expected_count:
        issues.add("RC0029_RECEIPT_CASE_SET_INVALID")
        return tuple(sorted(issues))

    recomputed = {key: 0 for key in sorted(_ALLOWED_DISPOSITIONS)}
    seen: list[str] = []
    for row in cases:
        if type(row) is not dict or set(row) != {
            "case_id",
            "closed_codes",
            "counts",
            "disposition",
            "hashes",
        }:
            issues.add("RC0029_RECEIPT_CASE_SHAPE_INVALID")
            continue
        case_id = row.get("case_id")
        disposition = row.get("disposition")
        closed_codes = row.get("closed_codes")
        row_counts = row.get("counts")
        row_hashes = row.get("hashes")
        if (
            type(case_id) is not str
            or _CASE_ID_RE.fullmatch(case_id) is None
            or case_id in seen
            or disposition not in _ALLOWED_DISPOSITIONS
        ):
            issues.add("RC0029_RECEIPT_CASE_ID_INVALID")
            continue
        seen.append(case_id)
        recomputed[disposition] += 1
        if (
            type(closed_codes) is not list
            or closed_codes != sorted(set(closed_codes))
            or any(
                type(code) is not str
                or _STOP_CODE_RE.fullmatch(code) is None
                for code in closed_codes
            )
            or (disposition == "selected" and closed_codes)
            or (disposition != "selected" and not closed_codes)
        ):
            issues.add("RC0029_RECEIPT_CLOSED_CODE_INVALID")
        if (
            type(row_counts) is not dict
            or tuple(sorted(row_counts)) != _RC0029_BODY_FREE_COUNT_KEYS
            or any(
                type(count) is not int or type(count) is bool or count < 0
                for count in row_counts.values()
            )
            or row_counts.get("base_candidate_count", 13) > 12
            or row_counts.get("experiment_candidate_count", 13) > 12
            or row_counts.get("evaluated_candidate_count", 13) > 12
            or row_counts.get("hard_gate_pass_count", 0)
            + row_counts.get("rejected_candidate_count", 0)
            != row_counts.get("evaluated_candidate_count", -1)
            or row_counts.get("replan_count", 2) > 1
        ):
            issues.add("RC0029_RECEIPT_COUNT_INVALID")
        if (
            type(row_hashes) is not dict
            or tuple(sorted(row_hashes)) != _RC0029_BODY_FREE_HASH_KEYS
            or not _valid_nonzero_sha256(
                row_hashes.get("source_case_commitment")
            )
            or any(
                item is not None and not _valid_nonzero_sha256(item)
                for key, item in row_hashes.items()
                if key != "source_case_commitment"
            )
            or (
                disposition != "fail_close"
                and any(
                    not _valid_nonzero_sha256(item)
                    for item in row_hashes.values()
                )
            )
        ):
            issues.add("RC0029_RECEIPT_HASH_INVALID")
    if tuple(seen) != expected_case_ids:
        issues.add("RC0029_RECEIPT_CASE_SET_INVALID")
    if type(counts) is dict and counts != recomputed:
        issues.add("RC0029_RECEIPT_ACCOUNTING_INVALID")

    if expected_stage == "E3_representative8":
        if (
            value.get("product_read_authorization_sha256") is not None
            or value.get("e3_body_free_receipt_sha256") is not None
        ):
            issues.add("RC0029_E3_PREMATURE_AUTHORIZATION_FORBIDDEN")
    elif (
        not _valid_nonzero_sha256(
            value.get("product_read_authorization_sha256")
        )
        or not _valid_nonzero_sha256(
            value.get("e3_body_free_receipt_sha256")
        )
    ):
        issues.add("RC0029_E3_PRODUCT_READ_AUTHORIZATION_REJECTED")
    return tuple(sorted(issues))


def validate_rc0029_e4_viability(value: Any) -> tuple[str, ...]:
    """Lock exact 100-case accounting and the external E3 authorization."""

    receipt_issues = validate_rc0029_experiment_body_free_receipt(
        value,
        expected_stage="E4_frozen100",
    )
    if receipt_issues:
        return receipt_issues

    selected_case_ids = frozenset(
        row["case_id"]
        for row in value["cases"]
        if row["disposition"] == "selected"
    )
    issues: set[str] = set()
    if len(selected_case_ids) <= len(_RC0027_SELECTED_CASE_IDS):
        issues.add("RC0029_E4_SELECTED_COUNT_NOT_IMPROVED")
    if not _RC0027_SELECTED_CASE_IDS <= selected_case_ids:
        issues.add("RC0029_E4_FROZEN_SELECTION_REGRESSION")
    new_selected = selected_case_ids - _RC0027_SELECTED_CASE_IDS
    if not new_selected - frozenset(_REPRESENTATIVE8_CASE_IDS):
        issues.add("RC0029_E4_NON_REPRESENTATIVE_GAIN_MISSING")
    return tuple(sorted(issues))


def _validate_body_free_receipt(value: Any) -> None:
    expected_top = {
        "body_free",
        "case_count",
        "cases",
        "disposition_counts",
        "schema_version",
        "source_dependency_closure_sha256",
        "source_fixture_hashes",
    }
    if type(value) is not dict or set(value) != expected_top:
        _stop("RC0029_BODY_FREE_RECEIPT_INVALID")
    cases = value.get("cases")
    counts = value.get("disposition_counts")
    source_hashes = value.get("source_fixture_hashes")
    if (
        value.get("body_free") is not True
        or value.get("schema_version") != _BODY_FREE_SCHEMA
        or value.get("case_count") != _EXPECTED_CASE_COUNT
        or type(cases) is not list
        or len(cases) != _EXPECTED_CASE_COUNT
        or type(counts) is not dict
        or set(counts) != _ALLOWED_DISPOSITIONS
        or sum(counts.values()) != _EXPECTED_CASE_COUNT
        or any(
            type(count) is not int or type(count) is bool or count < 0
            for count in counts.values()
        )
        or type(source_hashes) is not dict
        or not source_hashes
        or any(
            type(item) is not str or _SHA256_RE.fullmatch(item) is None
            for item in source_hashes.values()
        )
        or type(value.get("source_dependency_closure_sha256")) is not str
        or _SHA256_RE.fullmatch(value["source_dependency_closure_sha256"])
        is None
    ):
        _stop("RC0029_BODY_FREE_RECEIPT_INVALID")
    seen: set[str] = set()
    recomputed = {status: 0 for status in sorted(_ALLOWED_DISPOSITIONS)}
    for row in cases:
        if type(row) is not dict or set(row) != {
            "candidate_count",
            "case_id",
            "disposition",
            "source_case_commitment",
        }:
            _stop("RC0029_BODY_FREE_RECEIPT_INVALID")
        case_id = row["case_id"]
        disposition = row["disposition"]
        if (
            type(case_id) is not str
            or _CASE_ID_RE.fullmatch(case_id) is None
            or case_id in seen
            or disposition not in _ALLOWED_DISPOSITIONS
            or type(row["candidate_count"]) is not int
            or type(row["candidate_count"]) is bool
            or not 0 <= row["candidate_count"] <= 12
            or type(row["source_case_commitment"]) is not str
            or _SHA256_RE.fullmatch(row["source_case_commitment"]) is None
        ):
            _stop("RC0029_BODY_FREE_RECEIPT_INVALID")
        seen.add(case_id)
        recomputed[disposition] += 1
    if cases != sorted(cases, key=lambda row: row["case_id"]) or counts != recomputed:
        _stop("RC0029_BODY_FREE_RECEIPT_INVALID")


def capture_rc0027_baseline(output_directory: Path) -> None:
    directory_fd = _open_private_directory(output_directory)
    try:
        samples, manifest, source_closure, source_hashes = (
            _load_frozen_sources()
        )
        commitments = _case_commitments(manifest, samples)
        private_rows: list[dict[str, Any]] = []
        body_free_rows: list[dict[str, Any]] = []
        for sample in samples:
            case_id = sample["case_id"]
            private_row, body_free_row = _capture_case_projection(
                sample,
                source_case_commitment=commitments[case_id],
                source_closure=source_closure,
            )
            private_rows.append(private_row)
            body_free_rows.append(body_free_row)

        # Re-load all authorities after the long run.  A change during capture
        # invalidates the in-memory projection and produces no output files.
        end_samples, end_manifest, end_closure, end_hashes = (
            _load_frozen_sources()
        )
        if (
            end_samples != samples
            or end_manifest != manifest
            or end_closure != source_closure
            or end_hashes != source_hashes
        ):
            _stop("RC0029_FROZEN_SOURCE_CHANGED_DURING_CAPTURE")

        disposition_counts = {
            status: sum(row["disposition"] == status for row in body_free_rows)
            for status in sorted(_ALLOWED_DISPOSITIONS)
        }
        if disposition_counts != _EXPECTED_DISPOSITION_COUNTS:
            _stop("RC0029_RC0027_BASELINE_AGGREGATE_MISMATCH")
        private_artifact = {
            "adapter_version": "cocolon.emlis.nls_v3.runtime_adapter.step11.rc0027.v1",
            "body_full_private": True,
            "candidate_version_id": "nls_v3_rc_0027",
            "case_count": _EXPECTED_CASE_COUNT,
            "cases": private_rows,
            "schema_version": _PRIVATE_SCHEMA,
            "source_dependency_closure_sha256": source_closure,
            "source_fixture_hashes": source_hashes,
        }
        body_free_receipt = {
            "body_free": True,
            "case_count": _EXPECTED_CASE_COUNT,
            "cases": body_free_rows,
            "disposition_counts": disposition_counts,
            "schema_version": _BODY_FREE_SCHEMA,
            "source_dependency_closure_sha256": source_closure,
            "source_fixture_hashes": source_hashes,
        }
        _validate_body_free_receipt(body_free_receipt)
        private_payload = _canonical_json_bytes(private_artifact)
        body_free_payload = _canonical_json_bytes(body_free_receipt)
        _write_private_pair(directory_fd, private_payload, body_free_payload)
    finally:
        os.close(directory_fd)


def _assert_rc0029_receipt_sources(
    receipt: Mapping[str, Any],
    *,
    expected_stage: str,
    source_closure: str,
    source_hashes: Mapping[str, str],
    commitments: Mapping[str, str],
) -> None:
    issues = validate_rc0029_experiment_body_free_receipt(
        receipt,
        expected_stage=expected_stage,
    )
    if issues:
        _stop(
            "RC0029_E3_BODY_FREE_RECEIPT_INVALID"
            if expected_stage == "E3_representative8"
            else "RC0029_E4_BODY_FREE_RECEIPT_INVALID"
        )
    if (
        receipt.get("source_dependency_closure_sha256") != source_closure
        or receipt.get("source_fixture_hashes") != dict(source_hashes)
        or any(
            row["hashes"]["source_case_commitment"]
            != commitments.get(row["case_id"])
            for row in receipt["cases"]
        )
    ):
        _stop("RC0029_RC0029_SOURCE_COMMITMENT_MISMATCH")


def _run_rc0029_exact_scope(
    output_directory: Path,
    *,
    evaluation_stage: str,
    private_name: str,
    body_free_name: str,
    private_schema: str,
    body_free_schema: str,
    product_read_authorization: Mapping[str, Any] | None,
    product_read_authorization_sha256: str | None,
    product_read_authorization_path: Path | None,
) -> None:
    output_names = (private_name, body_free_name)
    directory_fd = _open_private_directory(
        output_directory,
        output_names=output_names,
    )
    try:
        samples, manifest, source_closure, source_hashes = (
            _load_rc0029_frozen_sources()
        )
        commitments = _case_commitments(manifest, samples)
        representative = _load_representative8_fixture(
            source_hashes=source_hashes,
            commitments=commitments,
        )
        sample_by_id = {sample["case_id"]: sample for sample in samples}
        if len(sample_by_id) != _EXPECTED_CASE_COUNT:
            _stop("RC0029_FROZEN_SOURCE_CONTRACT_MISMATCH")
        if evaluation_stage == "E3_representative8":
            selected_samples = tuple(
                sample_by_id[case_id]
                for case_id in _REPRESENTATIVE8_CASE_IDS
            )
            expected_count = 8
            product_read_status = "input_ready_not_reviewed"
            e3_receipt_sha256 = None
        elif evaluation_stage == "E4_frozen100":
            selected_samples = tuple(samples)
            expected_count = _EXPECTED_CASE_COUNT
            product_read_status = "external_authorization_validated"
            if product_read_authorization is None:
                _stop("RC0029_E3_PRODUCT_READ_AUTHORIZATION_REJECTED")
            e3_receipt_sha256 = product_read_authorization.get(
                "e3_body_free_receipt_sha256"
            )
        else:
            _stop("RC0029_CLI_COMMAND_REJECTED")
        if len(selected_samples) != expected_count:
            _stop("RC0029_RC0029_CASE_SET_INVALID")

        private_rows: list[dict[str, Any]] = []
        body_free_rows: list[dict[str, Any]] = []
        for sample in selected_samples:
            case_id = sample["case_id"]
            private_row, body_free_row = _run_rc0029_case_projection(
                sample,
                source_case_commitment=commitments[case_id],
                source_closure=source_closure,
            )
            private_rows.append(private_row)
            body_free_rows.append(body_free_row)

        end_samples, end_manifest, end_closure, end_hashes = (
            _load_rc0029_frozen_sources()
        )
        end_commitments = _case_commitments(end_manifest, end_samples)
        end_representative = _load_representative8_fixture(
            source_hashes=end_hashes,
            commitments=end_commitments,
        )
        if (
            end_samples != samples
            or end_manifest != manifest
            or end_closure != source_closure
            or end_hashes != source_hashes
            or end_commitments != commitments
            or end_representative != representative
        ):
            _stop("RC0029_FROZEN_SOURCE_CHANGED_DURING_RUN")
        if evaluation_stage == "E4_frozen100":
            if product_read_authorization_path is None:
                _stop("RC0029_E3_PRODUCT_READ_AUTHORIZATION_REJECTED")
            end_authorization, end_authorization_sha256 = (
                _read_private_authorization(product_read_authorization_path)
            )
            if (
                end_authorization != product_read_authorization
                or end_authorization_sha256
                != product_read_authorization_sha256
            ):
                _stop("RC0029_E3_PRODUCT_READ_AUTHORIZATION_CHANGED")

        disposition_counts = {
            status: sum(
                row["disposition"] == status for row in body_free_rows
            )
            for status in sorted(_ALLOWED_DISPOSITIONS)
        }
        if sum(disposition_counts.values()) != expected_count:
            _stop(
                "RC0029_E3_ACCOUNTING_MISMATCH"
                if evaluation_stage == "E3_representative8"
                else "RC0029_E4_ACCOUNTING_MISMATCH"
            )
        body_free_receipt = {
            "body_free": True,
            "case_count": expected_count,
            "cases": body_free_rows,
            "disposition_counts": disposition_counts,
            "e3_body_free_receipt_sha256": e3_receipt_sha256,
            "evaluation_stage": evaluation_stage,
            "formal_acceptance": "not_claimed",
            "product_read_authorization_sha256": (
                product_read_authorization_sha256
            ),
            "product_read_status": product_read_status,
            "representative_fixture_sha256": _REPRESENTATIVE8_SHA256,
            "schema_version": body_free_schema,
            "source_dependency_closure_sha256": source_closure,
            "source_fixture_hashes": source_hashes,
        }
        _assert_rc0029_receipt_sources(
            body_free_receipt,
            expected_stage=evaluation_stage,
            source_closure=source_closure,
            source_hashes=source_hashes,
            commitments=commitments,
        )
        body_free_payload = _canonical_json_bytes(body_free_receipt)
        private_artifact = {
            "body_free_receipt_sha256": _sha256_bytes(body_free_payload),
            "body_full_private": True,
            "case_count": expected_count,
            "cases": private_rows,
            "evaluation_stage": evaluation_stage,
            "formal_acceptance": "not_claimed",
            "product_read_authorization": (
                None
                if product_read_authorization is None
                else dict(product_read_authorization)
            ),
            "product_read_judgement": "not_performed_by_tool",
            "representative_fixture_sha256": _REPRESENTATIVE8_SHA256,
            "schema_version": private_schema,
            "source_dependency_closure_sha256": source_closure,
            "source_fixture_hashes": source_hashes,
        }
        private_payload = _canonical_json_bytes(private_artifact)
        _write_private_pair(
            directory_fd,
            private_payload,
            body_free_payload,
            private_name=private_name,
            body_free_name=body_free_name,
        )
    finally:
        os.close(directory_fd)


def run_rc0029_representative8(output_directory: Path) -> None:
    """Run exactly the frozen E3 eight and emit private Product Read inputs."""

    _run_rc0029_exact_scope(
        output_directory,
        evaluation_stage="E3_representative8",
        private_name=_E3_PRIVATE_FILENAME,
        body_free_name=_E3_BODY_FREE_FILENAME,
        private_schema=_E3_PRIVATE_SCHEMA,
        body_free_schema=_E3_BODY_FREE_SCHEMA,
        product_read_authorization=None,
        product_read_authorization_sha256=None,
        product_read_authorization_path=None,
    )


def run_rc0029_frozen100(
    output_directory: Path,
    *,
    product_read_receipt_path: Path,
) -> None:
    """Run exact E4 only after external E3 Product Read authorization."""

    authorization, authorization_sha256 = _read_private_authorization(
        product_read_receipt_path
    )
    _run_rc0029_exact_scope(
        output_directory,
        evaluation_stage="E4_frozen100",
        private_name=_E4_PRIVATE_FILENAME,
        body_free_name=_E4_BODY_FREE_FILENAME,
        private_schema=_E4_PRIVATE_SCHEMA,
        body_free_schema=_E4_BODY_FREE_SCHEMA,
        product_read_authorization=authorization,
        product_read_authorization_sha256=authorization_sha256,
        product_read_authorization_path=product_read_receipt_path,
    )


def _build_parser() -> argparse.ArgumentParser:
    parser = _ClosedArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    capture = commands.add_parser(
        "capture-rc0027-baseline",
        help="capture the exact private rc0027 default projection",
    )
    capture.add_argument(
        "--output-dir",
        type=Path,
        required=True,
        help="existing absolute 0700 directory outside the repository",
    )
    representative = commands.add_parser(
        "run-representative8",
        help="run the exact E3 representative eight privately",
    )
    representative.add_argument(
        "--output-dir",
        type=Path,
        required=True,
        help="existing absolute 0700 directory outside the repository",
    )
    frozen = commands.add_parser(
        "run-frozen100",
        help="run exact E4 after external E3 Product Read authorization",
    )
    frozen.add_argument(
        "--output-dir",
        type=Path,
        required=True,
        help="existing absolute 0700 directory outside the repository",
    )
    frozen.add_argument(
        "--product-read-receipt",
        type=Path,
        required=True,
        help="absolute 0600 external E3 Product Read authorization receipt",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    success_code = b""
    try:
        args = _build_parser().parse_args(argv)
        # Silence every dependency call.  Only the two fixed path-free result
        # codes below may reach the process streams.
        with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
            if args.command == "capture-rc0027-baseline":
                capture_rc0027_baseline(args.output_dir)
                success_code = b"RC0029_RC0027_BASELINE_CAPTURED\n"
            elif args.command == "run-representative8":
                run_rc0029_representative8(args.output_dir)
                success_code = b"RC0029_E3_REPRESENTATIVE8_COMPLETED\n"
            elif args.command == "run-frozen100":
                run_rc0029_frozen100(
                    args.output_dir,
                    product_read_receipt_path=(
                        args.product_read_receipt
                    ),
                )
                success_code = b"RC0029_E4_FROZEN100_COMPLETED\n"
            else:
                _stop("RC0029_CLI_COMMAND_REJECTED")
    except SystemExit as exc:
        # ``argparse`` uses SystemExit(0) only for its path-free help output.
        # Any other parser exit is a closed STOP without echoing arguments.
        if exc.code == 0:
            return 0
        os.write(
            2,
            b"RC0029_BOUNDED_EXPERIMENT_STOP:RC0029_CLI_ARGUMENT_REJECTED\n",
        )
        return 2
    except BoundedExperimentStop as exc:
        os.write(2, f"RC0029_BOUNDED_EXPERIMENT_STOP:{exc.code}\n".encode("ascii"))
        return 2
    except BaseException:
        os.write(2, b"RC0029_BOUNDED_EXPERIMENT_STOP:RC0029_UNHANDLED_EXCEPTION\n")
        return 2
    if not success_code:
        os.write(
            2,
            b"RC0029_BOUNDED_EXPERIMENT_STOP:RC0029_CLI_COMMAND_REJECTED\n",
        )
        return 2
    os.write(1, success_code)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
