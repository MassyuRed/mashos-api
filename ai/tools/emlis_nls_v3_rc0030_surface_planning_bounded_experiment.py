#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

"""Run the disconnected rc0030 E3 representative eight privately.

The command writes body-bearing Product Read material only to an existing,
caller-owned 0700 directory outside the repository.  Its companion receipt is
strictly body-free and carries only closed identifiers, roles, dispositions,
resource counts, hashes, and phase commitments.  This tool has no E4 command,
does not connect the experiment to a shared/public runtime, and never performs
or records a Product Read judgement.
"""

import argparse
from contextlib import redirect_stderr, redirect_stdout
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
    AI_ROOT
    / "tests"
    / "fixtures"
    / "emlis_nls_v3"
    / "generated"
    / "batch_001.jsonl"
)
_BATCH_MANIFEST_PATH = _BATCH_PATH.with_name("batch_001_manifest.json")
_COVERAGE_MATRIX_PATH = _BATCH_PATH.with_name("batch_001_coverage_matrix.json")
_DUPLICATE_REPORT_PATH = _BATCH_PATH.with_name("batch_001_duplicate_report.json")
_CYCLE_ROOT = AI_ROOT / "tests" / "fixtures" / "emlis_nls_v3" / "cycle_001"
_RC0029_DEPENDENCY_PATH = (
    _CYCLE_ROOT
    / "cycle001_dependency_manifest_rc0029_surface_repair_experiment.json"
)
_RC0030_DEPENDENCY_PATH = (
    _CYCLE_ROOT
    / "cycle001_dependency_manifest_rc0030_surface_planning_experiment.json"
)
_REPRESENTATIVE8_PATH = _CYCLE_ROOT / "rc0030_representative8_body_free.json"

RC0030_E3_PRIVATE_FILENAME = "rc0030_e3_representative8_private.json"
RC0030_E3_BODY_FREE_FILENAME = (
    "rc0030_e3_representative8_body_free_receipt.json"
)
RC0030_E3_PRIVATE_SCHEMA = (
    "cocolon.emlis.nls_v3.rc0030.e3_representative8.private.v1"
)
RC0030_E3_BODY_FREE_RECEIPT_SCHEMA = (
    "cocolon.emlis.nls_v3.rc0030.e3_representative8.body_free.v1"
)
RC0030_E3_EVALUATION_STAGE = "E3_representative8"
RC0030_E3_MANIFEST_PHASE = "E3_MACHINE_AND_PRODUCT_READ"
RC0030_E3_PHASE_PREDECESSOR_GIT_COMMIT = (
    "38ca7fa779065998a363ce9bb581338d98b8f79d"
)
RC0030_REPRESENTATIVE8_SHA256 = (
    "9cfbdafaf43a3caed8b5dc00e68b56cd2b24003a002f0a7cbd1c3ec06d598fa5"
)
RC0030_REPRESENTATIVE8_CASE_IDS = (
    "nls3s_b001_0001",
    "nls3s_b001_0002",
    "nls3s_b001_0009",
    "nls3s_b001_0019",
    "nls3s_b001_0035",
    "nls3s_b001_0043",
    "nls3s_b001_0063",
    "nls3s_b001_0100",
)

_EXPECTED_CASE_COUNT = 100
_REPRESENTATIVE_COUNT = 8
_ALLOWED_DISPOSITIONS = frozenset(
    {"selected", "no_valid_candidate", "fail_close"}
)
_RESOURCE_BOUNDS = {
    "candidate_limit_max": 12,
    "replan_limit_max": 1,
    "parser_invocations_max": 24,
    "matcher_invocations_max": 24,
    "body_byte_inspections_max": 48_000_000,
}
_BODY_FREE_COUNT_KEYS = (
    "base_body_parse_count",
    "base_candidate_count",
    "base_inverse_prepass_count",
    "base_inverse_rejected_candidate_count",
    "base_reuse_match_count",
    "body_byte_inspection_count",
    "construction_atom_count",
    "evaluated_candidate_count",
    "experiment_candidate_count",
    "explicit_unknown_atom_count",
    "final_body_parse_count",
    "final_surface_match_count",
    "forward_rejected_base_candidate_count",
    "hard_gate_pass_count",
    "owner_binding_count",
    "rejected_candidate_count",
    "relation_endpoint_atom_count",
    "replan_count",
    "semantic_link_atom_count",
    "verified_base_reuse_binding_count",
)
_BODY_FREE_HASH_KEYS = (
    "base_inverse_contexts_sha256",
    "lexical_atom_specs_sha256",
    "result_sha256",
    "selected_final_utf8_sha256",
    "source_case_commitment",
    "successor_authority_sha256",
    "successor_snapshot_sha256",
    "successor_witness_sha256",
    "surface_catalog_sha256",
)
_BODY_FREE_ROW_KEYS = {
    "body_free",
    "case_id",
    "closed_codes",
    "counts",
    "disposition",
    "experimental_only",
    "experiment_role",
    "hashes",
    "runtime_connected",
    "selected_candidate_present",
    "semantic_coverage_authority",
}
_RECEIPT_TOP_KEYS = {
    "body_free",
    "case_count",
    "case_ids",
    "cases",
    "disposition_counts",
    "evaluation_stage",
    "experimental_only",
    "formal_acceptance",
    "machine_status",
    "phase_predecessor_git_commit",
    "product_read_status",
    "representative_fixture_sha256",
    "resource_bounds",
    "runtime_connected",
    "schema_version",
    "source_dependency_closure_sha256",
    "source_dependency_manifest_sha256",
    "source_fixture_hashes",
}
_EXPECTED_ROLES = {
    "nls3s_b001_0001": "control",
    "nls3s_b001_0002": "control",
    "nls3s_b001_0009": "control",
    "nls3s_b001_0019": "improvement_target",
    "nls3s_b001_0035": "improvement_target",
    "nls3s_b001_0043": "improvement_target",
    "nls3s_b001_0063": "improvement_target",
    "nls3s_b001_0100": "improvement_target",
}
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_CASE_ID_RE = re.compile(r"^nls3s_b001_[0-9]{4}$")
_CLOSED_CODE_RE = re.compile(r"^[A-Z][A-Z0-9_]{2,159}$")
_MAX_PRIVATE_PAYLOAD_BYTES = 16_000_000
_MAX_RECEIPT_PAYLOAD_BYTES = 1_000_000


class BoundedExperimentStop(RuntimeError):
    """A path-free and body-free STOP result."""

    def __init__(self, code: str) -> None:
        if type(code) is not str or _CLOSED_CODE_RE.fullmatch(code) is None:
            code = "RC0030_BOUNDED_EXPERIMENT_STOP"
        self.code = code
        super().__init__(code)


class _ClosedArgumentParser(argparse.ArgumentParser):
    def error(self, message: str) -> None:
        del message
        raise BoundedExperimentStop("RC0030_CLI_ARGUMENT_REJECTED")


def _stop(code: str) -> None:
    raise BoundedExperimentStop(code)


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _sha256_file(path: Path) -> str:
    try:
        return _sha256_bytes(path.read_bytes())
    except Exception:
        _stop("RC0030_FROZEN_SOURCE_UNAVAILABLE")


def _valid_sha256(value: Any) -> bool:
    return (
        type(value) is str
        and _SHA256_RE.fullmatch(value) is not None
        and value != "0" * 64
    )


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
        _stop("RC0030_PRIVATE_PROJECTION_NOT_CANONICAL")


def _canonical_json_clone(value: Any) -> Any:
    try:
        return json.loads(
            _canonical_json_bytes(value).decode("utf-8", errors="strict")
        )
    except BoundedExperimentStop:
        raise
    except Exception:
        _stop("RC0030_PRIVATE_PROJECTION_NOT_CANONICAL")


def _load_strict_json_object(path: Path, *, code: str) -> dict[str, Any]:
    try:
        raw = path.read_bytes()
        value = json.loads(raw.decode("utf-8", errors="strict"))
    except Exception:
        _stop(code)
    if type(value) is not dict:
        _stop(code)
    return value


def _outside_repo(path: Path) -> bool:
    return path != REPO_ROOT and REPO_ROOT not in path.parents


def _open_private_directory(path: Path) -> int:
    """Open an existing no-symlink 0700 directory and return its dirfd."""

    if (
        not path.is_absolute()
        or any(part in {"", ".", ".."} for part in path.parts[1:])
        or not hasattr(os, "O_DIRECTORY")
        or not hasattr(os, "O_NOFOLLOW")
        or not hasattr(os, "getuid")
    ):
        _stop("RC0030_PRIVATE_DIRECTORY_PREFLIGHT_REJECTED")
    lexical = Path(os.path.abspath(os.fspath(path)))
    try:
        resolved = path.resolve(strict=True)
    except Exception:
        _stop("RC0030_PRIVATE_DIRECTORY_PREFLIGHT_REJECTED")
    if lexical != path or resolved != lexical or not _outside_repo(resolved):
        _stop("RC0030_PRIVATE_DIRECTORY_PREFLIGHT_REJECTED")

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
            _stop("RC0030_PRIVATE_DIRECTORY_PREFLIGHT_REJECTED")
        for name in (
            RC0030_E3_PRIVATE_FILENAME,
            RC0030_E3_BODY_FREE_FILENAME,
        ):
            try:
                os.stat(name, dir_fd=descriptor, follow_symlinks=False)
            except FileNotFoundError:
                continue
            _stop("RC0030_PRIVATE_OUTPUT_ALREADY_EXISTS")
        return descriptor
    except BoundedExperimentStop:
        if descriptor is not None:
            os.close(descriptor)
        raise
    except Exception:
        if descriptor is not None:
            os.close(descriptor)
        _stop("RC0030_PRIVATE_DIRECTORY_PREFLIGHT_REJECTED")


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
            _stop("RC0030_PRIVATE_OUTPUT_PREFLIGHT_REJECTED")
        return descriptor
    except BoundedExperimentStop:
        raise
    except FileExistsError:
        _stop("RC0030_PRIVATE_OUTPUT_ALREADY_EXISTS")
    except Exception:
        _stop("RC0030_PRIVATE_OUTPUT_PREFLIGHT_REJECTED")


def _write_private_pair(
    directory_fd: int,
    private_payload: bytes,
    body_free_payload: bytes,
) -> None:
    if (
        not 1 <= len(private_payload) <= _MAX_PRIVATE_PAYLOAD_BYTES
        or not 1 <= len(body_free_payload) <= _MAX_RECEIPT_PAYLOAD_BYTES
    ):
        _stop("RC0030_PRIVATE_OUTPUT_RESOURCE_BOUND_EXCEEDED")
    descriptors: dict[str, int] = {}
    created: list[str] = []
    try:
        for name in (
            RC0030_E3_PRIVATE_FILENAME,
            RC0030_E3_BODY_FREE_FILENAME,
        ):
            descriptors[name] = _open_exclusive_private_file(directory_fd, name)
            created.append(name)
        for name, payload in (
            (RC0030_E3_PRIVATE_FILENAME, private_payload),
            (RC0030_E3_BODY_FREE_FILENAME, body_free_payload),
        ):
            view = memoryview(payload)
            while view:
                written = os.write(descriptors[name], view)
                if written < 1:
                    _stop("RC0030_PRIVATE_OUTPUT_WRITE_REJECTED")
                view = view[written:]
            os.fsync(descriptors[name])
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


def _case_commitments(
    manifest: Mapping[str, Any],
    samples: Sequence[Mapping[str, Any]],
) -> dict[str, str]:
    rows = manifest.get("case_commitments")
    if type(rows) is not list or len(rows) != _EXPECTED_CASE_COUNT:
        _stop("RC0030_CASE_COMMITMENT_SET_INVALID")
    result: dict[str, str] = {}
    for row in rows:
        if type(row) is not dict or set(row) != {"case_id", "case_commitment"}:
            _stop("RC0030_CASE_COMMITMENT_SET_INVALID")
        case_id = row.get("case_id")
        commitment = row.get("case_commitment")
        if (
            type(case_id) is not str
            or _CASE_ID_RE.fullmatch(case_id) is None
            or case_id in result
            or not _valid_sha256(commitment)
        ):
            _stop("RC0030_CASE_COMMITMENT_SET_INVALID")
        result[case_id] = commitment
    sample_ids = [sample.get("case_id") for sample in samples]
    if (
        any(type(case_id) is not str for case_id in sample_ids)
        or sample_ids != sorted(result)
        or list(manifest.get("case_ids", ())) != sample_ids
    ):
        _stop("RC0030_CASE_COMMITMENT_SET_INVALID")
    return result


def _load_validated_sources() -> tuple[
    list[dict[str, Any]],
    dict[str, str],
    str,
    str,
    dict[str, Mapping[str, Any]],
]:
    """Load exact corpus, E3 manifest, and frozen representative authority."""

    try:
        from emlis_nls_v3_batch_run import load_validated_batch
        from emlis_nls_v3_s2_sample_registry import load_canonical_json
        from emlis_ai_rc0030_surface_planning_experiment_dependency_manifest_v3 import (
            RC0030_E3_PHASE_PREDECESSOR_GIT_COMMIT as manifest_predecessor,
            RC0030_MANIFEST_PHASE,
            RC0030_SURFACE_PLANNING_DEPENDENCY_MANIFEST_SCHEMA,
            validate_rc0030_surface_planning_dependency_manifest,
        )

        samples, batch_manifest = load_validated_batch(
            _BATCH_PATH,
            _BATCH_MANIFEST_PATH,
        )
        parent = load_canonical_json(_RC0029_DEPENDENCY_PATH)
        dependency = load_canonical_json(_RC0030_DEPENDENCY_PATH)
        dependency_issues = validate_rc0030_surface_planning_dependency_manifest(
            dependency,
            parent_manifest=parent,
            repo_root=REPO_ROOT,
        )
    except Exception:
        _stop("RC0030_FROZEN_SOURCE_VALIDATION_FAILED")

    source_closure = dependency.get("source_dependency_closure_sha256")
    flags = dependency.get("flags")
    if (
        type(samples) is not list
        or len(samples) != _EXPECTED_CASE_COUNT
        or type(batch_manifest) is not dict
        or batch_manifest.get("case_count") != _EXPECTED_CASE_COUNT
        or batch_manifest.get("candidate_version_id") is not None
        or dependency_issues != ()
        or dependency.get("schema_version")
        != RC0030_SURFACE_PLANNING_DEPENDENCY_MANIFEST_SCHEMA
        or dependency.get("manifest_phase") != RC0030_E3_MANIFEST_PHASE
        or RC0030_MANIFEST_PHASE != RC0030_E3_MANIFEST_PHASE
        or manifest_predecessor != RC0030_E3_PHASE_PREDECESSOR_GIT_COMMIT
        or dependency.get("phase_predecessor_git_commit")
        != RC0030_E3_PHASE_PREDECESSOR_GIT_COMMIT
        or not _valid_sha256(source_closure)
        or type(flags) is not dict
        or flags.get("experimental_only") is not True
        or flags.get("runtime_connected") is not False
        or flags.get("eligible_for_formal") is not False
        or flags.get("eligible_for_production") is not False
    ):
        _stop("RC0030_FROZEN_SOURCE_CONTRACT_MISMATCH")

    source_hashes = {
        "batch_manifest_sha256": _sha256_file(_BATCH_MANIFEST_PATH),
        "corpus_file_sha256": _sha256_file(_BATCH_PATH),
        "corpus_set_commitment": batch_manifest.get("corpus_set_commitment"),
        "coverage_matrix_sha256": _sha256_file(_COVERAGE_MATRIX_PATH),
        "duplicate_report_sha256": _sha256_file(_DUPLICATE_REPORT_PATH),
    }
    if (
        any(not _valid_sha256(value) for value in source_hashes.values())
        or source_hashes["corpus_file_sha256"]
        != batch_manifest.get("corpus_file_sha256")
        or source_hashes["coverage_matrix_sha256"]
        != batch_manifest.get("coverage_matrix_sha256")
        or source_hashes["duplicate_report_sha256"]
        != batch_manifest.get("duplicate_report_sha256")
    ):
        _stop("RC0030_FROZEN_SOURCE_HASH_MISMATCH")

    commitments = _case_commitments(batch_manifest, samples)
    representative = _load_strict_json_object(
        _REPRESENTATIVE8_PATH,
        code="RC0030_REPRESENTATIVE8_FIXTURE_INVALID",
    )
    if _sha256_file(_REPRESENTATIVE8_PATH) != RC0030_REPRESENTATIVE8_SHA256:
        _stop("RC0030_REPRESENTATIVE8_FIXTURE_HASH_MISMATCH")
    rows = representative.get("rows")
    if (
        representative.get("body_free") is not True
        or representative.get("representative_count") != _REPRESENTATIVE_COUNT
        or representative.get("source_fixture_commitments") != source_hashes
        or type(rows) is not list
        or len(rows) != _REPRESENTATIVE_COUNT
    ):
        _stop("RC0030_REPRESENTATIVE8_FIXTURE_INVALID")
    row_by_id: dict[str, Mapping[str, Any]] = {}
    for row in rows:
        if type(row) is not dict:
            _stop("RC0030_REPRESENTATIVE8_FIXTURE_INVALID")
        case_id = row.get("case_id")
        if (
            case_id not in _EXPECTED_ROLES
            or case_id in row_by_id
            or row.get("experiment_role") != _EXPECTED_ROLES[case_id]
            or row.get("source_case_commitment") != commitments.get(case_id)
            or type(row.get("rc0030_required_product_read_severity")) is not list
            or not row["rc0030_required_product_read_severity"]
        ):
            _stop("RC0030_REPRESENTATIVE8_FIXTURE_INVALID")
        row_by_id[case_id] = row
    if tuple(row_by_id) != RC0030_REPRESENTATIVE8_CASE_IDS:
        _stop("RC0030_REPRESENTATIVE8_FIXTURE_INVALID")

    sample_by_id = {sample.get("case_id"): sample for sample in samples}
    if len(sample_by_id) != _EXPECTED_CASE_COUNT or any(
        case_id not in sample_by_id for case_id in RC0030_REPRESENTATIVE8_CASE_IDS
    ):
        _stop("RC0030_FROZEN_SOURCE_CONTRACT_MISMATCH")
    selected_samples = [
        sample_by_id[case_id] for case_id in RC0030_REPRESENTATIVE8_CASE_IDS
    ]
    return (
        selected_samples,
        source_hashes,
        source_closure,
        _sha256_file(_RC0030_DEPENDENCY_PATH),
        row_by_id,
    )


def _fail_close_case(
    *,
    case_id: str,
    experiment_role: str,
    source_case_commitment: str,
    failure_code: str,
    source_input: Mapping[str, Any],
) -> tuple[dict[str, Any], dict[str, Any]]:
    if _CLOSED_CODE_RE.fullmatch(failure_code) is None:
        _stop("RC0030_RUNTIME_UNKNOWN_EXCEPTION")
    counts = {key: 0 for key in _BODY_FREE_COUNT_KEYS}
    hashes = {key: None for key in _BODY_FREE_HASH_KEYS}
    hashes["source_case_commitment"] = source_case_commitment
    private_row = {
        "case_id": case_id,
        "experiment_role": experiment_role,
        "product_read_input": {
            "selected_final_utf8_sha256": None,
            "selected_final_utf8_text": None,
            "source_input": dict(source_input),
            "status": "not_selected",
        },
        "runtime_body_free_result": None,
        "runtime_error_code": failure_code,
        "source_case_commitment": source_case_commitment,
    }
    body_free_row = {
        "body_free": True,
        "case_id": case_id,
        "closed_codes": [failure_code],
        "counts": counts,
        "disposition": "fail_close",
        "experimental_only": True,
        "experiment_role": experiment_role,
        "hashes": hashes,
        "runtime_connected": False,
        "selected_candidate_present": False,
        "semantic_coverage_authority": "none",
    }
    return private_row, body_free_row


def _run_case(
    sample: Mapping[str, Any],
    *,
    fixture_row: Mapping[str, Any],
    source_closure: str,
) -> tuple[dict[str, Any], dict[str, Any]]:
    try:
        runtime_owner = __import__(
            "emlis_ai_step11_rc0030_experiment_runtime_adapter_v3",
            fromlist=(
                "STEP11_RC0030_MAX_BODY_BYTE_INSPECTIONS",
                "STEP11_RC0030_MAX_CANDIDATES",
                "STEP11_RC0030_MAX_MATCHER_INVOCATIONS",
                "STEP11_RC0030_MAX_PARSER_INVOCATIONS",
                "STEP11_RC0030_MAX_REPLANS",
                "Step11Rc0030ExperimentRuntimeError",
                "execute_step11_rc0030_experiment_private",
                "step11_rc0030_experiment_result_material",
                "validate_step11_rc0030_experiment_private_execution",
                "validate_step11_rc0030_experiment_result",
            ),
        )
        STEP11_RC0030_MAX_BODY_BYTE_INSPECTIONS = (
            runtime_owner.STEP11_RC0030_MAX_BODY_BYTE_INSPECTIONS
        )
        STEP11_RC0030_MAX_CANDIDATES = (
            runtime_owner.STEP11_RC0030_MAX_CANDIDATES
        )
        STEP11_RC0030_MAX_MATCHER_INVOCATIONS = (
            runtime_owner.STEP11_RC0030_MAX_MATCHER_INVOCATIONS
        )
        STEP11_RC0030_MAX_PARSER_INVOCATIONS = (
            runtime_owner.STEP11_RC0030_MAX_PARSER_INVOCATIONS
        )
        STEP11_RC0030_MAX_REPLANS = runtime_owner.STEP11_RC0030_MAX_REPLANS
        Step11Rc0030ExperimentRuntimeError = (
            runtime_owner.Step11Rc0030ExperimentRuntimeError
        )
        execute_step11_rc0030_experiment_private = (
            runtime_owner.execute_step11_rc0030_experiment_private
        )
        step11_rc0030_experiment_result_material = (
            runtime_owner.step11_rc0030_experiment_result_material
        )
        validate_step11_rc0030_experiment_private_execution = (
            runtime_owner.validate_step11_rc0030_experiment_private_execution
        )
        validate_step11_rc0030_experiment_result = (
            runtime_owner.validate_step11_rc0030_experiment_result
        )
    except Exception:
        _stop("RC0030_PRIVATE_RUNTIME_UNAVAILABLE")

    if (
        STEP11_RC0030_MAX_CANDIDATES != _RESOURCE_BOUNDS["candidate_limit_max"]
        or STEP11_RC0030_MAX_REPLANS != _RESOURCE_BOUNDS["replan_limit_max"]
        or STEP11_RC0030_MAX_PARSER_INVOCATIONS
        != _RESOURCE_BOUNDS["parser_invocations_max"]
        or STEP11_RC0030_MAX_MATCHER_INVOCATIONS
        != _RESOURCE_BOUNDS["matcher_invocations_max"]
        or STEP11_RC0030_MAX_BODY_BYTE_INSPECTIONS
        != _RESOURCE_BOUNDS["body_byte_inspections_max"]
    ):
        _stop("RC0030_RUNTIME_RESOURCE_CONTRACT_DRIFTED")

    case_id = sample.get("case_id")
    current_input = sample.get("input")
    source_case_commitment = fixture_row.get("source_case_commitment")
    experiment_role = fixture_row.get("experiment_role")
    if (
        case_id != fixture_row.get("case_id")
        or type(case_id) is not str
        or _CASE_ID_RE.fullmatch(case_id) is None
        or type(current_input) is not dict
        or not _valid_sha256(source_case_commitment)
        or experiment_role != _EXPECTED_ROLES.get(case_id)
    ):
        _stop("RC0030_SAMPLE_PROJECTION_REJECTED")
    source_input = _canonical_json_clone(current_input)
    runtime_input = _canonical_json_clone(current_input)
    if type(source_input) is not dict or type(runtime_input) is not dict:
        _stop("RC0030_SAMPLE_PROJECTION_REJECTED")

    try:
        execution = execute_step11_rc0030_experiment_private(
            runtime_input,
            case_id=case_id,
            source_case_commitment=source_case_commitment,
            source_dependency_closure_sha256=source_closure,
            candidate_limit=_RESOURCE_BOUNDS["candidate_limit_max"],
            replan_limit=_RESOURCE_BOUNDS["replan_limit_max"],
        )
    except Step11Rc0030ExperimentRuntimeError as exc:
        return _fail_close_case(
            case_id=case_id,
            experiment_role=experiment_role,
            source_case_commitment=source_case_commitment,
            failure_code=exc.code,
            source_input=source_input,
        )
    except Exception:
        _stop("RC0030_RUNTIME_UNKNOWN_EXCEPTION")

    if validate_step11_rc0030_experiment_private_execution(execution):
        _stop("RC0030_PRIVATE_EXECUTION_INVALID")
    result = execution.body_free_result
    if validate_step11_rc0030_experiment_result(result):
        _stop("RC0030_BODY_FREE_RESULT_INVALID")
    material = step11_rc0030_experiment_result_material(result)
    if (
        result.case_id != case_id
        or result.source_case_commitment != source_case_commitment
        or result.source_dependency_closure_sha256 != source_closure
        or result.disposition not in _ALLOWED_DISPOSITIONS
        or result.experimental_only is not True
        or result.body_free is not True
        or result.runtime_connected is not False
        or result.semantic_coverage_authority != "none"
        or material.get("body_free") is not True
        or material.get("runtime_connected") is not False
    ):
        _stop("RC0030_RUNTIME_SOURCE_COMMITMENT_MISMATCH")

    counts = {key: getattr(result, key) for key in _BODY_FREE_COUNT_KEYS}
    hashes = {
        key: getattr(result, key)
        for key in _BODY_FREE_HASH_KEYS
        if key != "selected_final_utf8_sha256"
    }
    selected_bytes = execution.selected_final_utf8_bytes
    selected_text: str | None = None
    if result.disposition == "selected":
        if (
            result.selected_candidate_present is not True
            or type(selected_bytes) is not bytes
            or not selected_bytes
            or len(selected_bytes) > 1_000_000
        ):
            _stop("RC0030_PRODUCT_READ_INPUT_MISSING")
        try:
            selected_text = selected_bytes.decode("utf-8", errors="strict")
        except UnicodeError:
            _stop("RC0030_PRODUCT_READ_INPUT_INVALID")
        selected_sha256 = _sha256_bytes(selected_bytes)
        product_read_status = "ready"
    else:
        if result.selected_candidate_present is not False or selected_bytes is not None:
            _stop("RC0030_PRODUCT_READ_INPUT_DISPOSITION_MISMATCH")
        selected_sha256 = None
        product_read_status = "not_selected"
    hashes["selected_final_utf8_sha256"] = selected_sha256

    private_row = {
        "case_id": case_id,
        "experiment_role": experiment_role,
        "product_read_input": {
            "baseline_product_read_severity": fixture_row.get(
                "baseline_product_read_severity"
            ),
            "rc0029_product_read_severity": fixture_row.get(
                "rc0029_product_read_severity"
            ),
            "rc0030_required_product_read_severity": list(
                fixture_row["rc0030_required_product_read_severity"]
            ),
            "selected_final_utf8_sha256": selected_sha256,
            "selected_final_utf8_text": selected_text,
            "source_input": source_input,
            "status": product_read_status,
        },
        "runtime_body_free_result": material,
        "runtime_error_code": None,
        "source_case_commitment": source_case_commitment,
    }
    body_free_row = {
        "body_free": True,
        "case_id": case_id,
        "closed_codes": list(result.closed_failure_codes),
        "counts": counts,
        "disposition": result.disposition,
        "experimental_only": True,
        "experiment_role": experiment_role,
        "hashes": hashes,
        "runtime_connected": False,
        "selected_candidate_present": result.selected_candidate_present,
        "semantic_coverage_authority": result.semantic_coverage_authority,
    }
    return private_row, body_free_row


def validate_rc0030_experiment_body_free_receipt(value: Any) -> tuple[str, ...]:
    """Validate E3 machine evidence without reading any input or body."""

    if type(value) is not dict or set(value) != _RECEIPT_TOP_KEYS:
        return ("RC0030_RECEIPT_SHAPE_INVALID",)
    issues: set[str] = set()
    cases = value.get("cases")
    counts = value.get("disposition_counts")
    source_hashes = value.get("source_fixture_hashes")
    if (
        value.get("schema_version") != RC0030_E3_BODY_FREE_RECEIPT_SCHEMA
        or value.get("body_free") is not True
        or value.get("experimental_only") is not True
        or value.get("runtime_connected") is not False
        or value.get("evaluation_stage") != RC0030_E3_EVALUATION_STAGE
        or value.get("case_count") != _REPRESENTATIVE_COUNT
        or value.get("case_ids") != list(RC0030_REPRESENTATIVE8_CASE_IDS)
        or value.get("phase_predecessor_git_commit")
        != RC0030_E3_PHASE_PREDECESSOR_GIT_COMMIT
        or value.get("representative_fixture_sha256")
        != RC0030_REPRESENTATIVE8_SHA256
        or value.get("resource_bounds") != _RESOURCE_BOUNDS
        or value.get("formal_acceptance") != "not_claimed"
        or not _valid_sha256(value.get("source_dependency_closure_sha256"))
        or not _valid_sha256(value.get("source_dependency_manifest_sha256"))
        or type(source_hashes) is not dict
        or set(source_hashes) != {
            "batch_manifest_sha256",
            "corpus_file_sha256",
            "corpus_set_commitment",
            "coverage_matrix_sha256",
            "duplicate_report_sha256",
        }
        or any(not _valid_sha256(item) for item in source_hashes.values())
    ):
        issues.add("RC0030_RECEIPT_CONTRACT_INVALID")
    if (
        type(counts) is not dict
        or set(counts) != _ALLOWED_DISPOSITIONS
        or any(
            type(count) is not int or type(count) is bool or count < 0
            for count in counts.values()
        )
        or sum(counts.values()) != _REPRESENTATIVE_COUNT
    ):
        issues.add("RC0030_RECEIPT_ACCOUNTING_INVALID")
    if type(cases) is not list or len(cases) != _REPRESENTATIVE_COUNT:
        issues.add("RC0030_RECEIPT_CASE_SET_INVALID")
        return tuple(sorted(issues))

    recomputed = {key: 0 for key in sorted(_ALLOWED_DISPOSITIONS)}
    seen: list[str] = []
    for row in cases:
        if type(row) is not dict or set(row) != _BODY_FREE_ROW_KEYS:
            issues.add("RC0030_RECEIPT_CASE_SHAPE_INVALID")
            continue
        case_id = row.get("case_id")
        disposition = row.get("disposition")
        closed_codes = row.get("closed_codes")
        row_counts = row.get("counts")
        row_hashes = row.get("hashes")
        if (
            type(case_id) is not str
            or case_id not in _EXPECTED_ROLES
            or case_id in seen
            or row.get("experiment_role") != _EXPECTED_ROLES.get(case_id)
            or disposition not in _ALLOWED_DISPOSITIONS
            or row.get("body_free") is not True
            or row.get("experimental_only") is not True
            or row.get("runtime_connected") is not False
            or row.get("semantic_coverage_authority") != "none"
            or type(row.get("selected_candidate_present")) is not bool
        ):
            issues.add("RC0030_RECEIPT_CASE_ID_OR_CONTRACT_INVALID")
            continue
        seen.append(case_id)
        recomputed[disposition] += 1
        if (
            type(closed_codes) is not list
            or closed_codes != sorted(set(closed_codes))
            or any(
                type(code) is not str or _CLOSED_CODE_RE.fullmatch(code) is None
                for code in closed_codes
            )
            or (disposition == "selected" and closed_codes)
            or (disposition != "selected" and not closed_codes)
            or row["selected_candidate_present"] != (disposition == "selected")
        ):
            issues.add("RC0030_RECEIPT_DISPOSITION_INVALID")
        if (
            type(row_counts) is not dict
            or tuple(sorted(row_counts)) != _BODY_FREE_COUNT_KEYS
            or any(
                type(count) is not int or type(count) is bool or count < 0
                for count in row_counts.values()
            )
            or row_counts.get("base_candidate_count", 13) > 12
            or row_counts.get("experiment_candidate_count", 13) > 12
            or row_counts.get("evaluated_candidate_count", 13) > 12
            or row_counts.get("base_body_parse_count", 25)
            + row_counts.get("final_body_parse_count", 25)
            > 24
            or row_counts.get("base_reuse_match_count", 25)
            + row_counts.get("final_surface_match_count", 25)
            > 24
            or row_counts.get("body_byte_inspection_count", 48_000_001)
            > 48_000_000
            or row_counts.get("hard_gate_pass_count", 0)
            + row_counts.get("rejected_candidate_count", 0)
            != row_counts.get("evaluated_candidate_count", -1)
            or row_counts.get("replan_count", 2) > 1
        ):
            issues.add("RC0030_RECEIPT_RESOURCE_COUNT_INVALID")
        if (
            type(row_hashes) is not dict
            or tuple(sorted(row_hashes)) != _BODY_FREE_HASH_KEYS
            or not _valid_sha256(row_hashes.get("source_case_commitment"))
            or any(
                item is not None and not _valid_sha256(item)
                for key, item in row_hashes.items()
                if key != "source_case_commitment"
            )
            or (
                disposition == "selected"
                and any(not _valid_sha256(item) for item in row_hashes.values())
            )
            or (
                disposition != "selected"
                and row_hashes.get("selected_final_utf8_sha256") is not None
            )
        ):
            issues.add("RC0030_RECEIPT_HASH_INVALID")
    if tuple(seen) != RC0030_REPRESENTATIVE8_CASE_IDS:
        issues.add("RC0030_RECEIPT_CASE_SET_INVALID")
    if type(counts) is dict and counts != recomputed:
        issues.add("RC0030_RECEIPT_ACCOUNTING_INVALID")

    selected_exact = recomputed.get("selected") == _REPRESENTATIVE_COUNT
    expected_machine = (
        "ready_for_product_read" if selected_exact else "stopped_before_product_read"
    )
    expected_product = (
        "input_ready_not_reviewed" if selected_exact else "blocked_machine_not_green"
    )
    if (
        value.get("machine_status") != expected_machine
        or value.get("product_read_status") != expected_product
    ):
        issues.add("RC0030_RECEIPT_MACHINE_STATUS_INVALID")
    return tuple(sorted(issues))


def _assert_sources_unchanged(
    expected: tuple[
        list[dict[str, Any]],
        dict[str, str],
        str,
        str,
        dict[str, Mapping[str, Any]],
    ],
) -> None:
    if _load_validated_sources() != expected:
        _stop("RC0030_FROZEN_SOURCE_CHANGED_DURING_RUN")


def run_rc0030_representative8(output_directory: Path) -> None:
    """Run exactly the frozen eight and emit private Product Read inputs."""

    directory_fd = _open_private_directory(output_directory)
    try:
        sources = _load_validated_sources()
        samples, source_hashes, source_closure, dependency_sha256, rows = sources
        private_rows: list[dict[str, Any]] = []
        body_free_rows: list[dict[str, Any]] = []
        for sample in samples:
            case_id = sample.get("case_id")
            if type(case_id) is not str or case_id not in rows:
                _stop("RC0030_REPRESENTATIVE8_CASE_SET_INVALID")
            private_row, body_free_row = _run_case(
                sample,
                fixture_row=rows[case_id],
                source_closure=source_closure,
            )
            private_rows.append(private_row)
            body_free_rows.append(body_free_row)

        _assert_sources_unchanged(sources)
        disposition_counts = {
            status: sum(row["disposition"] == status for row in body_free_rows)
            for status in sorted(_ALLOWED_DISPOSITIONS)
        }
        if sum(disposition_counts.values()) != _REPRESENTATIVE_COUNT:
            _stop("RC0030_E3_ACCOUNTING_MISMATCH")
        selected_exact = disposition_counts["selected"] == _REPRESENTATIVE_COUNT
        body_free_receipt = {
            "body_free": True,
            "case_count": _REPRESENTATIVE_COUNT,
            "case_ids": list(RC0030_REPRESENTATIVE8_CASE_IDS),
            "cases": body_free_rows,
            "disposition_counts": disposition_counts,
            "evaluation_stage": RC0030_E3_EVALUATION_STAGE,
            "experimental_only": True,
            "formal_acceptance": "not_claimed",
            "machine_status": (
                "ready_for_product_read"
                if selected_exact
                else "stopped_before_product_read"
            ),
            "phase_predecessor_git_commit": (
                RC0030_E3_PHASE_PREDECESSOR_GIT_COMMIT
            ),
            "product_read_status": (
                "input_ready_not_reviewed"
                if selected_exact
                else "blocked_machine_not_green"
            ),
            "representative_fixture_sha256": RC0030_REPRESENTATIVE8_SHA256,
            "resource_bounds": dict(_RESOURCE_BOUNDS),
            "runtime_connected": False,
            "schema_version": RC0030_E3_BODY_FREE_RECEIPT_SCHEMA,
            "source_dependency_closure_sha256": source_closure,
            "source_dependency_manifest_sha256": dependency_sha256,
            "source_fixture_hashes": source_hashes,
        }
        receipt_issues = validate_rc0030_experiment_body_free_receipt(
            body_free_receipt
        )
        if receipt_issues:
            _stop("RC0030_E3_BODY_FREE_RECEIPT_INVALID")
        body_free_payload = _canonical_json_bytes(body_free_receipt)
        private_artifact = {
            "body_free_receipt_sha256": _sha256_bytes(body_free_payload),
            "case_count": _REPRESENTATIVE_COUNT,
            "cases": private_rows,
            "evaluation_stage": RC0030_E3_EVALUATION_STAGE,
            "experimental_only": True,
            "formal_acceptance": "not_claimed",
            "phase_predecessor_git_commit": (
                RC0030_E3_PHASE_PREDECESSOR_GIT_COMMIT
            ),
            "private_body_full": True,
            "product_read_judgement": "not_performed_by_tool",
            "representative_fixture_sha256": RC0030_REPRESENTATIVE8_SHA256,
            "runtime_connected": False,
            "schema_version": RC0030_E3_PRIVATE_SCHEMA,
            "shareable": False,
            "source_dependency_closure_sha256": source_closure,
            "source_dependency_manifest_sha256": dependency_sha256,
            "source_fixture_hashes": source_hashes,
        }
        private_payload = _canonical_json_bytes(private_artifact)
        _write_private_pair(directory_fd, private_payload, body_free_payload)
    finally:
        os.close(directory_fd)


def _build_parser() -> argparse.ArgumentParser:
    parser = _ClosedArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
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
    return parser


def main(argv: list[str] | None = None) -> int:
    try:
        args = _build_parser().parse_args(argv)
        with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
            if args.command != "run-representative8":
                _stop("RC0030_CLI_COMMAND_REJECTED")
            run_rc0030_representative8(args.output_dir)
        os.write(1, b"RC0030_E3_REPRESENTATIVE8_COMPLETED\n")
        return 0
    except SystemExit as exc:
        if exc.code == 0:
            return 0
        os.write(
            2,
            b"RC0030_BOUNDED_EXPERIMENT_STOP:RC0030_CLI_ARGUMENT_REJECTED\n",
        )
        return 2
    except BoundedExperimentStop as exc:
        os.write(
            2,
            f"RC0030_BOUNDED_EXPERIMENT_STOP:{exc.code}\n".encode("ascii"),
        )
        return 2
    except BaseException:
        os.write(
            2,
            b"RC0030_BOUNDED_EXPERIMENT_STOP:RC0030_BOUNDED_EXPERIMENT_STOP\n",
        )
        return 2


__all__ = [
    "BoundedExperimentStop",
    "RC0030_E3_BODY_FREE_FILENAME",
    "RC0030_E3_BODY_FREE_RECEIPT_SCHEMA",
    "RC0030_E3_EVALUATION_STAGE",
    "RC0030_E3_PHASE_PREDECESSOR_GIT_COMMIT",
    "RC0030_E3_PRIVATE_FILENAME",
    "RC0030_E3_PRIVATE_SCHEMA",
    "RC0030_REPRESENTATIVE8_CASE_IDS",
    "RC0030_REPRESENTATIVE8_SHA256",
    "main",
    "run_rc0030_representative8",
    "validate_rc0030_experiment_body_free_receipt",
]


if __name__ == "__main__":
    raise SystemExit(main())
