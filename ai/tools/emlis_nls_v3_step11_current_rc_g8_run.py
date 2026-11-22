#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

"""Run exact-100 through the distinct Cycle001 Product recovery candidate.

This one-shot private runner rebuilds upstream typed sources request-locally.
It imports no prior Step11 runtime adapter, Gate, or selector and accepts only
the distinct rc0036 recovery identity after source-bound inverse validation.
Body-full rows are written only beside a body-free HMAC summary in an existing
caller-owned 0700 directory outside the repository.
"""

import argparse
import ast
from collections import Counter, defaultdict
from concurrent.futures import ProcessPoolExecutor
from contextlib import redirect_stderr, redirect_stdout
from dataclasses import dataclass
import hashlib
import hmac
import io
import json
import multiprocessing
import os
from pathlib import Path
import re
import stat as stat_module
import sys
from typing import Any, Mapping, Sequence


AI_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = AI_ROOT.parent.resolve()
SERVICES = AI_ROOT / "services" / "ai_inference"
TOOLS = AI_ROOT / "tools"
for entry in (SERVICES, TOOLS):
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
_MANIFEST_PATH = _BATCH_PATH.with_name("batch_001_manifest.json")
_FROZEN_BATCH_SHA256 = (
    "013dd2ad1c1f446f843f400b3eb16231e8f32649e30114e70039b4cb709e8414"
)
_FROZEN_MANIFEST_SHA256 = (
    "2b3308c4ada090539a2fc71c1cb235970aa0b90687b8d9633464ba61e94deba4"
)
_FROZEN_PRIVACY_REVIEW = {
    "status": "passed",
    "reviewer": "karen",
    "pii_absent": True,
    "real_user_text_copy_absent": True,
    "expected_response_absent": True,
}
_FROZEN_SAMPLE_KEYS = frozenset(
    {
        "batch_id",
        "case_id",
        "coverage",
        "input",
        "schema_version",
        "semantic_contract",
        "source",
    }
)
_FROZEN_MANIFEST_KEYS = frozenset(
    {
        "batch_id",
        "body_free",
        "case_commitments",
        "case_count",
        "case_ids",
        "corpus_file_ref",
        "corpus_file_sha256",
        "corpus_set_commitment",
        "counts_toward_karen_minimum",
        "coverage_matrix_ref",
        "coverage_matrix_sha256",
        "duplicate_counts",
        "duplicate_policy_sha256",
        "duplicate_report_ref",
        "duplicate_report_sha256",
        "frozen",
        "invalid_case_count",
        "invalid_case_history",
        "manifest_id",
        "near_review_decisions",
        "near_review_summary",
        "next_authority",
        "parent_registry_ref",
        "parent_registry_sha256",
        "privacy_review",
        "reference_case_count",
        "reference_corpus_set_commitment",
        "replacement_policy",
        "sample_schema_ref",
        "sample_schema_sha256",
        "schema_version",
        "source_partition",
        "state",
        "valid_case_count",
        "validator_policy_sha256",
    }
)
_PRIVATE_FILENAME = "current_rc_g8_exact100_private.json"
_BODY_FREE_FILENAME = "current_rc_g8_exact100_body_free.json"
_PRIVATE_SCHEMA = "cocolon.emlis.nls_v3.current_rc.g8.private_exact100.v4"
_BODY_FREE_SCHEMA = (
    "cocolon.emlis.nls_v3.current_rc.g8.body_free_exact100.v4"
)
_RECOVERY_CANDIDATE_VERSION = "nls_v3_rc_0036_cycle001_product_quality"
_RECOVERY_CANDIDATE_SCHEMA = (
    "cocolon.emlis.nls_v3.step11."
    "cycle001_product_quality_candidate.rc0036.v1"
)
_RECOVERY_OWNER_SCHEMA = (
    "cocolon.emlis.nls_v3.step11."
    "cycle001_product_recovery_owner.rc0036.v1"
)
_RECOVERY_SOURCE_SCHEMA = (
    "cocolon.emlis.nls_v3.step11."
    "cycle001_product_recovery_source.rc0036.v1"
)
_RECOVERY_PLAN_SCHEMA = (
    "cocolon.emlis.nls_v3.step11."
    "cycle001_product_recovery_plan.rc0036.v1"
)
_RECOVERY_RENDERED_SCHEMA = (
    "cocolon.emlis.nls_v3.step11."
    "cycle001_product_recovery_rendered.rc0036.v1"
)
_CASE_RE = re.compile(r"^nls3s_b001_[0-9]{4}$")
_RUN_ID_RE = re.compile(r"^[a-z0-9][a-z0-9._-]{2,63}$")
_CODE_RE = re.compile(r"^[A-Z][A-Z0-9_]{2,127}$")
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_ALLOWED_DISPOSITIONS = frozenset(
    {"selected", "no_valid_candidate", "fail_close"}
)
_CHECK_KEYS = (
    "input_projected",
    "source_context_built",
    "recovery_builder_called",
    "recovery_validator_passed",
    "recovery_identity_exact",
    "source_envelope_exact",
    "final_utf8_valid",
    "inverse_layout_exact",
    "semantic_atoms_exact",
    "construction_modifiers_exact",
    "reception_bindings_exact",
    "dimension_loci_exact",
)
_PRIVATE_ROW_KEYS = frozenset(
    {
        "case_id",
        "source_case_commitment",
        "source_input",
        "disposition",
        "candidate_version_id",
        "candidate_schema_version",
        "current_candidate_id",
        "candidate_output_utf8",
        "machine_checks",
        "failure_code",
        "exception_captured",
    }
)
_PUBLIC_FAILURE_CODES = frozenset(
    {
        "CURRENT_RC_G8_BASE_RUNTIME_INVALID",
        "CURRENT_RC_G8_BASE_STATUS_INVALID",
        "CURRENT_RC_G8_CASE_REJECTED",
        "CURRENT_RC_G8_CURRENT_BUILDER_UNAVAILABLE",
        "CURRENT_RC_G8_INVERSE_REJECTED",
        "CURRENT_RC_G8_PRIVATE_OUTPUT_INVALID",
        "STEP11_GROUNDED_PHRASE_AMBIGUOUS",
        "STEP11_INPUT_SPECIFIC_ANCHOR_UNRESOLVED",
        "STEP11_RC0031_OWNER_ROLE_TYPED_RECOMPOSITION_INVALID",
        "STEP11_RC0031_PRODUCT_OWNER_EXPRESSION_INVALID",
        "STEP11_RELATION_MULTI_EDGE_LOCAL_ANAPHORA_AMBIGUOUS",
        "STEP11_REQUIRED_OWNER_INPUT_SPECIFICITY_UNRESOLVED",
    }
)
_PAIR_KEYS = frozenset({"body_free_core_sha256", "run_hmac"})
_SOURCE_SEARCH_ROOTS = (SERVICES, TOOLS)


class CurrentRcG8RunError(RuntimeError):
    """Path-free runner failure containing one closed code."""

    def __init__(self, code: str) -> None:
        if type(code) is not str or _CODE_RE.fullmatch(code) is None:
            code = "CURRENT_RC_G8_RUN_FAILED"
        self.code = code
        super().__init__(code)


def _canonical_json_bytes(value: Any) -> bytes:
    try:
        return (
            json.dumps(
                value,
                ensure_ascii=False,
                sort_keys=True,
                separators=(",", ":"),
                allow_nan=False,
            ).encode("utf-8", errors="strict")
            + b"\n"
        )
    except Exception as exc:
        raise CurrentRcG8RunError(
            "CURRENT_RC_G8_RESULT_NOT_CANONICAL"
        ) from exc


def _closed_code(exc: BaseException) -> str:
    code = getattr(exc, "code", None)
    if type(code) is str and _CODE_RE.fullmatch(code) is not None:
        return code
    return "CURRENT_RC_G8_CASE_REJECTED"


def _empty_checks() -> dict[str, bool]:
    return {key: False for key in _CHECK_KEYS}


def _canonical_material_bytes(value: Any) -> bytes:
    payload = _canonical_json_bytes(value)
    if not payload.endswith(b"\n"):
        raise CurrentRcG8RunError("CURRENT_RC_G8_RESULT_NOT_CANONICAL")
    return payload[:-1]


def _frozen_repo_ref(value: Any) -> Path:
    if type(value) is not str or not value or "\\" in value:
        raise CurrentRcG8RunError("CURRENT_RC_G8_MANIFEST_INVALID")
    relative = Path(value)
    if (
        relative.is_absolute()
        or any(part in {"", ".", ".."} for part in relative.parts)
        or relative.as_posix() != value
    ):
        raise CurrentRcG8RunError("CURRENT_RC_G8_MANIFEST_INVALID")
    try:
        resolved = (REPO_ROOT / relative).resolve(strict=True)
        resolved.relative_to(REPO_ROOT)
    except Exception as exc:
        raise CurrentRcG8RunError("CURRENT_RC_G8_MANIFEST_INVALID") from exc
    if resolved != REPO_ROOT / relative:
        raise CurrentRcG8RunError("CURRENT_RC_G8_MANIFEST_INVALID")
    return resolved


def _exact100_sources(
    batch_path: Path,
    manifest_path: Path,
) -> tuple[list[dict[str, Any]], dict[str, Any], dict[str, str]]:
    from emlis_ai_step10_app_reachable_contract_v3 import (
        project_app_reachable_input,
    )

    try:
        resolved_batch = batch_path.resolve(strict=True)
        resolved_manifest = manifest_path.resolve(strict=True)
        batch_bytes = resolved_batch.read_bytes()
        manifest_bytes = resolved_manifest.read_bytes()
    except Exception as exc:
        raise CurrentRcG8RunError("CURRENT_RC_G8_SOURCE_UNAVAILABLE") from exc
    if (
        resolved_batch != _BATCH_PATH.resolve(strict=True)
        or resolved_manifest != _MANIFEST_PATH.resolve(strict=True)
        or hashlib.sha256(batch_bytes).hexdigest() != _FROZEN_BATCH_SHA256
        or hashlib.sha256(manifest_bytes).hexdigest()
        != _FROZEN_MANIFEST_SHA256
        or not batch_bytes
        or not batch_bytes.endswith(b"\n")
        or batch_bytes.startswith(b"\xef\xbb\xbf")
        or manifest_bytes.startswith(b"\xef\xbb\xbf")
    ):
        raise CurrentRcG8RunError("CURRENT_RC_G8_FROZEN_SOURCE_INVALID")
    try:
        manifest = json.loads(manifest_bytes.decode("utf-8", errors="strict"))
    except Exception as exc:
        raise CurrentRcG8RunError("CURRENT_RC_G8_MANIFEST_INVALID") from exc
    if (
        type(manifest) is not dict
        or set(manifest) != _FROZEN_MANIFEST_KEYS
        or _canonical_json_bytes(manifest) != manifest_bytes
    ):
        raise CurrentRcG8RunError("CURRENT_RC_G8_MANIFEST_INVALID")
    lines = tuple(batch_bytes.splitlines(keepends=True))
    samples: list[dict[str, Any]] = []
    for line in lines:
        if not line.endswith(b"\n") or line in {b"\n", b"\r\n"}:
            raise CurrentRcG8RunError("CURRENT_RC_G8_SAMPLE_INVALID")
        try:
            sample = json.loads(line.decode("utf-8", errors="strict"))
        except Exception as exc:
            raise CurrentRcG8RunError("CURRENT_RC_G8_SAMPLE_INVALID") from exc
        if (
            type(sample) is not dict
            or set(sample) != _FROZEN_SAMPLE_KEYS
            or _canonical_json_bytes(sample) != line
        ):
            raise CurrentRcG8RunError("CURRENT_RC_G8_SAMPLE_INVALID")
        samples.append(sample)
    expected_ids = tuple(f"nls3s_b001_{index:04d}" for index in range(1, 101))
    actual_ids = tuple(row.get("case_id") for row in samples)
    manifest_ids = tuple(manifest.get("case_ids", ()))
    commitments = manifest.get("case_commitments")
    if (
        len(lines) != 100
        or len(samples) != 100
        or manifest.get("schema_version")
        != "cocolon.emlis.nls_v3.sample_batch_manifest.v1"
        or manifest.get("batch_id") != "nls3_batch_001"
        or manifest.get("state") != "VALIDATED"
        or manifest.get("frozen") is not True
        or manifest.get("body_free") is not True
        or manifest.get("source_partition") != "karen_generated"
        or manifest.get("privacy_review") != _FROZEN_PRIVACY_REVIEW
        or manifest.get("case_count") != 100
        or manifest.get("valid_case_count") != 100
        or manifest.get("invalid_case_count") != 0
        or actual_ids != expected_ids
        or manifest_ids != expected_ids
        or type(commitments) is not list
        or len(commitments) != 100
    ):
        raise CurrentRcG8RunError("CURRENT_RC_G8_EXACT100_REQUIRED")
    commitment_by_case: dict[str, str] = {}
    expected_commitment_rows: list[dict[str, str]] = []
    for sample, row in zip(samples, commitments, strict=True):
        if type(row) is not dict:
            raise CurrentRcG8RunError("CURRENT_RC_G8_CASE_COMMITMENT_INVALID")
        case_id = row.get("case_id")
        commitment = row.get("case_commitment")
        calculated = hashlib.sha256(
            _canonical_material_bytes(sample)
        ).hexdigest()
        if (
            set(row) != {"case_id", "case_commitment"}
            or type(case_id) is not str
            or _CASE_RE.fullmatch(case_id) is None
            or type(commitment) is not str
            or re.fullmatch(r"[0-9a-f]{64}", commitment) is None
            or case_id in commitment_by_case
            or case_id != sample.get("case_id")
            or commitment != calculated
        ):
            raise CurrentRcG8RunError("CURRENT_RC_G8_CASE_COMMITMENT_INVALID")
        commitment_by_case[case_id] = commitment
        expected_commitment_rows.append(
            {"case_id": case_id, "case_commitment": calculated}
        )
    if tuple(commitment_by_case) != expected_ids:
        raise CurrentRcG8RunError("CURRENT_RC_G8_CASE_COMMITMENT_INVALID")
    corpus_set_commitment = hashlib.sha256(
        _canonical_material_bytes(sorted(commitment_by_case.values()))
    ).hexdigest()
    manifest_payload = dict(manifest)
    manifest_id = manifest_payload.pop("manifest_id", None)
    if (
        manifest.get("case_commitments") != expected_commitment_rows
        or manifest.get("corpus_file_sha256") != _FROZEN_BATCH_SHA256
        or manifest.get("corpus_set_commitment") != corpus_set_commitment
        or manifest_id
        != "nls3manifest_"
        + hashlib.sha256(_canonical_material_bytes(manifest_payload)).hexdigest()[
            :16
        ]
    ):
        raise CurrentRcG8RunError("CURRENT_RC_G8_MANIFEST_INVALID")
    referenced = (
        ("corpus_file_ref", "corpus_file_sha256"),
        ("coverage_matrix_ref", "coverage_matrix_sha256"),
        ("duplicate_report_ref", "duplicate_report_sha256"),
        ("parent_registry_ref", "parent_registry_sha256"),
        ("sample_schema_ref", "sample_schema_sha256"),
    )
    for ref_key, sha_key in referenced:
        path = _frozen_repo_ref(manifest.get(ref_key))
        try:
            actual_sha256 = hashlib.sha256(path.read_bytes()).hexdigest()
        except Exception as exc:
            raise CurrentRcG8RunError("CURRENT_RC_G8_MANIFEST_INVALID") from exc
        if (
            manifest.get(sha_key) != actual_sha256
            or (ref_key == "corpus_file_ref" and path != resolved_batch)
        ):
            raise CurrentRcG8RunError("CURRENT_RC_G8_MANIFEST_INVALID")
    for expected_id, sample in zip(expected_ids, samples, strict=True):
        if (
            sample.get("case_id") != expected_id
            or sample.get("batch_id") != "nls3_batch_001"
            or sample.get("schema_version")
            != "cocolon.emlis.nls_v3.sample_case.v1"
            or sample.get("source") != "karen_generated"
            or type(sample.get("coverage")) is not dict
            or type(sample.get("semantic_contract")) is not dict
            or type(sample.get("input")) is not dict
        ):
            raise CurrentRcG8RunError("CURRENT_RC_G8_SAMPLE_INVALID")
        try:
            project_app_reachable_input(sample["input"])
        except Exception as exc:
            raise CurrentRcG8RunError("CURRENT_RC_G8_SAMPLE_INVALID") from exc
    return samples, manifest, commitment_by_case


def _repo_relative(path: Path) -> tuple[Path, str]:
    try:
        resolved = path.resolve(strict=True)
        relative = resolved.relative_to(REPO_ROOT).as_posix()
    except Exception as exc:
        raise CurrentRcG8RunError("CURRENT_RC_G8_SOURCE_UNAVAILABLE") from exc
    if (
        not relative
        or relative.startswith("../")
        or "/../" in relative
        or resolved != REPO_ROOT / relative
    ):
        raise CurrentRcG8RunError("CURRENT_RC_G8_SOURCE_UNAVAILABLE")
    return resolved, relative


def _module_name(root: Path, path: Path) -> str:
    relative = path.relative_to(root)
    parts = list(relative.parts)
    if parts[-1] == "__init__.py":
        parts = parts[:-1]
    else:
        parts[-1] = Path(parts[-1]).stem
    return ".".join(parts)


def _local_module_index() -> tuple[dict[str, Path], dict[Path, str]]:
    by_name: dict[str, Path] = {}
    by_path: dict[Path, str] = {}
    for root in _SOURCE_SEARCH_ROOTS:
        for path in sorted(root.rglob("*.py")):
            resolved, _relative = _repo_relative(path)
            name = _module_name(root, resolved)
            if not name:
                continue
            prior = by_name.get(name)
            if prior is not None and prior != resolved:
                raise CurrentRcG8RunError(
                    "CURRENT_RC_G8_SOURCE_MODULE_AMBIGUOUS"
                )
            by_name[name] = resolved
            by_path[resolved] = name
    return by_name, by_path


def _import_candidates(
    tree: ast.AST,
    *,
    module_name: str,
    is_package: bool,
) -> tuple[str, ...]:
    names: set[str] = set()
    package = module_name.split(".") if is_package else module_name.split(".")[:-1]
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            names.update(alias.name for alias in node.names)
            continue
        if isinstance(node, ast.ImportFrom):
            if node.level:
                drop = node.level - 1
                if drop > len(package):
                    continue
                base_parts = package[: len(package) - drop]
                if node.module:
                    base_parts.extend(node.module.split("."))
                base = ".".join(base_parts)
            else:
                base = node.module or ""
            if base:
                names.add(base)
            for alias in node.names:
                if alias.name != "*":
                    names.add(".".join(row for row in (base, alias.name) if row))
            continue
        if (
            isinstance(node, ast.Call)
            and node.args
            and isinstance(node.args[0], ast.Constant)
            and type(node.args[0].value) is str
            and (
                isinstance(node.func, ast.Name)
                and node.func.id in {"import_module", "__import__"}
                or isinstance(node.func, ast.Attribute)
                and node.func.attr == "import_module"
            )
        ):
            names.add(node.args[0].value)
    return tuple(sorted(name for name in names if name))


def _transitive_local_python_sources(starts: Sequence[Path]) -> set[Path]:
    by_name, by_path = _local_module_index()
    pending = [path.resolve() for path in starts]
    sources: set[Path] = set()
    while pending:
        path = pending.pop()
        if path in sources:
            continue
        if path.suffix != ".py":
            continue
        _resolved, _relative = _repo_relative(path)
        try:
            tree = ast.parse(path.read_bytes(), filename=path.name)
        except Exception as exc:
            raise CurrentRcG8RunError("CURRENT_RC_G8_SOURCE_UNAVAILABLE") from exc
        sources.add(path)
        module_name = by_path.get(path, path.stem)
        for candidate in _import_candidates(
            tree,
            module_name=module_name,
            is_package=path.name == "__init__.py",
        ):
            name = candidate
            while name:
                imported = by_name.get(name)
                if imported is not None:
                    if imported not in sources:
                        pending.append(imported)
                    break
                name = name.rpartition(".")[0]
    return sources


def _closure_data_paths(batch_path: Path, manifest_path: Path) -> set[Path]:
    fixture_root = AI_ROOT / "tests" / "fixtures"
    schema_root = AI_ROOT / "tests" / "schemas"
    paths = {
        batch_path.resolve(),
        manifest_path.resolve(),
        batch_path.with_name("batch_001_coverage_matrix.json").resolve(),
        batch_path.with_name("batch_001_duplicate_report.json").resolve(),
    }
    paths.update(
        path.resolve()
        for path in (fixture_root / "emlis_nls_v3").rglob("*")
        if path.is_file()
    )
    paths.update(
        path.resolve()
        for path in fixture_root.glob("emlis_nls_v3_s*.json")
        if path.is_file()
    )
    paths.update(
        path.resolve()
        for path in schema_root.glob("emlis_nls_v3*.json")
        if path.is_file()
    )
    return paths


def _source_closure_paths(batch_path: Path, manifest_path: Path) -> tuple[Path, ...]:
    roots = (
        Path(__file__),
        SERVICES / "emlis_ai_step10_app_reachable_contract_v3.py",
        SERVICES / "emlis_ai_evidence_ledger_service.py",
        SERVICES
        / "emlis_ai_grounded_lexical_role_experiment_snapshot_successor_v3.py",
        SERVICES / "emlis_ai_step11_grounded_lexicalization_v3.py",
        SERVICES / "emlis_ai_step11_natural_surface_v3.py",
        SERVICES / "emlis_ai_step11_cycle001_product_recovery_v3.py",
        SERVICES / "emlis_ai_step11_rc0031_experiment_surface_catalog_v3.py",
        SERVICES / "emlis_ai_step11_rc0031_reception_focus_authority_v3.py",
    )
    for path in roots:
        _repo_relative(path)
    paths = _transitive_local_python_sources(roots)
    paths.update(_closure_data_paths(batch_path, manifest_path))
    return tuple(sorted(paths, key=lambda path: _repo_relative(path)[1]))


def _closure_digest(files: Sequence[Mapping[str, Any]]) -> str:
    return hashlib.sha256(
        b"cocolon.current-rc.g8.source-closure.v4\0"
        + _canonical_json_bytes(list(files))
    ).hexdigest()


def _source_closure_snapshot(
    batch_path: Path,
    manifest_path: Path,
) -> dict[str, Any]:
    rows: list[dict[str, str]] = []
    try:
        for path in _source_closure_paths(batch_path, manifest_path):
            resolved, relative = _repo_relative(path)
            rows.append(
                {
                    "path": relative,
                    "sha256": hashlib.sha256(resolved.read_bytes()).hexdigest(),
                }
            )
    except CurrentRcG8RunError:
        raise
    except Exception as exc:
        raise CurrentRcG8RunError("CURRENT_RC_G8_SOURCE_UNAVAILABLE") from exc
    return {
        "source_closure_sha256": _closure_digest(rows),
        "source_closure_file_count": len(rows),
        "source_closure_files": rows,
    }


def _source_closure(batch_path: Path, manifest_path: Path) -> str:
    """Compatibility projection of the recomputable v4 closure."""

    return str(
        _source_closure_snapshot(batch_path, manifest_path)[
            "source_closure_sha256"
        ]
    )


def _validated_source_snapshot(value: Any) -> dict[str, Any]:
    if type(value) is not dict or set(value) != {
        "source_closure_sha256",
        "source_closure_file_count",
        "source_closure_files",
    }:
        raise CurrentRcG8RunError("CURRENT_RC_G8_SOURCE_CLOSURE_INVALID")
    files = value.get("source_closure_files")
    if (
        type(value.get("source_closure_sha256")) is not str
        or _SHA256_RE.fullmatch(value["source_closure_sha256"]) is None
        or type(value.get("source_closure_file_count")) is not int
        or type(files) is not list
        or not files
    ):
        raise CurrentRcG8RunError("CURRENT_RC_G8_SOURCE_CLOSURE_INVALID")
    previous = ""
    for row in files:
        if type(row) is not dict or set(row) != {"path", "sha256"}:
            raise CurrentRcG8RunError("CURRENT_RC_G8_SOURCE_CLOSURE_INVALID")
        path = row.get("path")
        sha256 = row.get("sha256")
        if (
            type(path) is not str
            or not path
            or Path(path).is_absolute()
            or ".." in Path(path).parts
            or path <= previous
            or type(sha256) is not str
            or _SHA256_RE.fullmatch(sha256) is None
        ):
            raise CurrentRcG8RunError("CURRENT_RC_G8_SOURCE_CLOSURE_INVALID")
        previous = path
    if (
        value.get("source_closure_file_count") != len(files)
        or value.get("source_closure_sha256") != _closure_digest(files)
    ):
        raise CurrentRcG8RunError("CURRENT_RC_G8_SOURCE_CLOSURE_INVALID")
    return {
        "source_closure_sha256": value["source_closure_sha256"],
        "source_closure_file_count": len(files),
        "source_closure_files": [dict(row) for row in files],
    }


def _assert_source_unchanged(
    expected: Mapping[str, Any],
    batch_path: Path,
    manifest_path: Path,
    *,
    code: str,
) -> None:
    expected_snapshot = _validated_source_snapshot(expected)
    current = _source_closure_snapshot(batch_path, manifest_path)
    if _canonical_json_bytes(current) != _canonical_json_bytes(expected_snapshot):
        raise CurrentRcG8RunError(code)


def _bound_exact100_sources(
    batch_path: Path,
    manifest_path: Path,
) -> tuple[
    list[dict[str, Any]],
    dict[str, Any],
    dict[str, str],
    tuple[tuple[str, str, bytes], ...],
    dict[str, Any],
]:
    """Load exact100 only inside one stable, recomputable source closure."""

    source_snapshot = _source_closure_snapshot(batch_path, manifest_path)
    samples, manifest, commitment_by_case = _exact100_sources(
        batch_path, manifest_path
    )
    _assert_source_unchanged(
        source_snapshot,
        batch_path,
        manifest_path,
        code="CURRENT_RC_G8_SOURCE_CHANGED_DURING_PREFLIGHT",
    )
    case_sources = _exact100_source_bindings(samples, commitment_by_case)
    return (
        samples,
        manifest,
        commitment_by_case,
        case_sources,
        source_snapshot,
    )


def _exact100_source_bindings(
    samples: Sequence[Mapping[str, Any]],
    commitment_by_case: Mapping[str, str],
) -> tuple[tuple[str, str, bytes], ...]:
    """Bind each exact100 row to its validated frozen input and manifest row."""

    expected_ids = tuple(
        f"nls3s_b001_{index:04d}" for index in range(1, 101)
    )
    if len(samples) != 100 or tuple(commitment_by_case) != expected_ids:
        raise CurrentRcG8RunError(
            "CURRENT_RC_G8_CASE_SOURCE_BINDING_INVALID"
        )
    bindings: list[tuple[str, str, bytes]] = []
    for expected_id, sample in zip(expected_ids, samples, strict=True):
        commitment = commitment_by_case.get(expected_id)
        if (
            type(sample) is not dict
            or sample.get("case_id") != expected_id
            or type(sample.get("input")) is not dict
            or type(commitment) is not str
            or _SHA256_RE.fullmatch(commitment) is None
        ):
            raise CurrentRcG8RunError(
                "CURRENT_RC_G8_CASE_SOURCE_BINDING_INVALID"
            )
        bindings.append(
            (
                expected_id,
                commitment,
                _canonical_json_bytes(sample["input"]),
            )
        )
    return tuple(bindings)


@dataclass(frozen=True, slots=True, repr=False)
class _DirectRecoveryContext:
    """Request-local upstream authority; no surface Gate or selector state."""

    normalized_input: dict[str, Any]
    projected_current_input: dict[str, Any]
    resolver: Any
    grounded_plan: Any
    observation_stage_context: dict[str, Any]
    inventory_result: Any
    content_plan: dict[str, Any]
    discourse_plans: tuple[Any, ...]
    successor_snapshot: Any
    lexical_atom_specs: Any


@dataclass(frozen=True, slots=True, repr=False)
class _ExpectedFragment:
    source_fragment_id: str
    source_owner_id: str
    source_nucleus_id: str
    source_span_id: str
    source_field: str
    span_relative_start_index: int
    span_relative_end_index: int
    source_fragment_text: str
    source_fragment_text_sha256: str
    binding_basis: str


@dataclass(frozen=True, slots=True, repr=False)
class _ExpectedRoot:
    source_root_id: str
    source_owner_id: str
    source_nucleus_id: str
    source_obligation_ids: tuple[str, ...]
    source_fragments: tuple[_ExpectedFragment, ...]
    semantic_kind: str
    dimensions: tuple[str, str, str, str]
    required: bool


@dataclass(frozen=True, slots=True, repr=False)
class _ExpectedConstructionRole:
    construction_slot_id: str
    parent_nucleus_id: str
    source_span_id: str
    slot_start_index: int
    slot_end_index: int
    lexical_role_kind: str
    construction_position: str
    role_position_surface_token: str
    source_owner_ids: tuple[str, ...]
    source_owner_dimensions: tuple[tuple[str, str, str, str], ...]
    participation_ids: tuple[str, ...]


@dataclass(frozen=True, slots=True, repr=False)
class _ExpectedAtom:
    source_atom_id: str
    semantic_family: str
    semantic_key: str
    source_owner_ids: tuple[str, ...]
    direction: str
    dimensions: tuple[str, str, str, str]
    source_nucleus_owner_ids: tuple[str, ...]
    source_semantic_unit_owner_ids: tuple[str, ...]
    source_parent_nucleus_ids: tuple[str, ...]
    source_span_ids: tuple[str, ...]
    source_evidence_alias_ids: tuple[str, ...]
    source_marker_span_ids: tuple[str, ...]
    source_grounding_kind: str
    source_relation_ids: tuple[str, ...]
    authority_basis: str
    source_retention: str
    construction_roles: tuple[_ExpectedConstructionRole, ...]
    source_order: int
    surface_token: str
    forward_signature: tuple[Any, ...]


@dataclass(frozen=True, slots=True, repr=False)
class _ExpectedReception:
    source_reception_opportunity_id: str
    source_scope: str
    source_focus_owner_ids: tuple[str, ...]
    source_target_owner_ids: tuple[str, ...]
    supporting_source_owner_ids: tuple[str, ...]
    visible_support_owner_ids: tuple[str, ...]
    inventory_reception_act: str
    effective_reception_act: str
    act_refinement_basis: str
    sentence_group_ordinal: int


@dataclass(frozen=True, slots=True, repr=False)
class _ExpectedOwner:
    schema_version: str
    source_owner_id: str
    source_owner_kind: str
    source_owner_ordinal: int
    source_nucleus_id: str
    semantic_kind: str
    dimensions: tuple[str, str, str, str]
    typed_role_tokens: tuple[str, ...]
    referent_text: str
    referent_text_sha256: str
    referent_basis: str


@dataclass(frozen=True, slots=True, repr=False)
class _ExpectedRecovery:
    owner_registry: tuple[str, ...]
    owners: tuple[_ExpectedOwner, ...]
    roots: tuple[_ExpectedRoot, ...]
    atoms: tuple[_ExpectedAtom, ...]
    receptions: tuple[_ExpectedReception, ...]
    source_counts: tuple[tuple[str, int], ...]
    source_commitments: tuple[tuple[str, str], ...]
    current_input_binding: tuple[Any, ...]
    typed_payload_sha256: str
    candidate_boundary_sha256: str
    catalog: Mapping[str, Any]
    grammar: Mapping[str, Any]
    visible_authority: Any | None = None


@dataclass(frozen=True, slots=True, repr=False)
class _ExpectedVisibleMove:
    """One source-authorised visible move, without a completed sentence."""

    section_role: str
    family: str
    source_unit_id: str
    source_atom_ids: tuple[str, ...]
    source_owner_ids: tuple[str, ...]
    source_obligation_ids: tuple[str, ...]
    source_fragment_ids: tuple[str, ...]
    dimensions: tuple[str, str, str, str]
    semantic_key: str = ""
    direction: str = ""
    target_owner_ids: tuple[str, ...] = ()
    support_owner_ids: tuple[str, ...] = ()
    grounded_phrase_id: str = ""
    grounded_feature_sha256: str = ""
    action_lifecycle: str = ""
    open_unknown: bool = False


@dataclass(frozen=True, slots=True, repr=False)
class _ParsedVisibleNode:
    """Body-only typed clause signature without reconstructed prose."""

    section_role: str
    family: str
    visible_owner_ids: tuple[str, ...]
    semantic_key: str
    source_fragment_ids: tuple[str, ...] = ()
    target_owner_ids: tuple[str, ...] = ()
    support_owner_ids: tuple[str, ...] = ()
    open_unknown: bool = False
    intended_action: bool = False


@dataclass(frozen=True, slots=True, repr=False)
class _ExpectedVisibleAuthority:
    """Independent overlay/lexical authority used by the private runner."""

    active_discourse_plan: Mapping[str, Any]
    semantic_overlay: Any
    active_discourse_plan_sha256: str
    semantic_overlay_sha256: str
    source_to_owner: Mapping[str, str]
    owner_to_source: Mapping[str, str]
    ordered_owner_ids: tuple[str, ...]
    plain_phrase_by_owner: Mapping[str, str]
    first_phrase_by_owner: Mapping[str, str]
    phrase_id_by_owner: Mapping[str, str]
    feature_sha256_by_owner: Mapping[str, str]
    owner_reference_by_owner: Mapping[str, str]
    specificity_companion_phrase: str | None
    moves: tuple[_ExpectedVisibleMove, ...] = ()


@dataclass(frozen=True, slots=True, repr=False)
class _ExpectedAnchorFragment:
    source_slot: str
    source_start: int
    source_end: int
    source_anchor_id: str
    text: str
    source_nucleus_ids: tuple[str, ...]


def _build_direct_recovery_context(
    projected_input: Mapping[str, Any],
) -> _DirectRecoveryContext:
    """Rebuild typed upstream sources without importing an acceptance owner."""

    from emlis_ai_content_selection_v3 import build_content_selection_plan
    from emlis_ai_current_input_bundle import normalize_emlis_current_input
    from emlis_ai_discourse_graph_planner_v3 import (
        DiscourseGraphPlannerError,
        build_discourse_graph_plans,
    )
    from emlis_ai_evidence_ledger_service import (
        build_evidence_ledger,
        build_evidence_span_resolver,
    )
    from emlis_ai_grounded_lexical_role_experiment_snapshot_successor_v3 import (
        build_grounded_lexical_role_experiment_snapshot_successor,
    )
    from emlis_ai_grounded_observation_plan import (
        build_grounded_observation_plan,
    )
    from emlis_ai_observation_integrator_service import (
        integrate_perspective_board,
    )
    from emlis_ai_observation_stage_context_v3 import (
        build_observation_stage_context,
    )
    from emlis_ai_perspective_board import build_perspective_board
    from emlis_ai_perspective_observers import run_perspective_observers
    from emlis_ai_safety_triage import build_emlis_safety_triage_decision
    from emlis_ai_semantic_obligation_inventory_v3 import (
        build_grounded_source_snapshot,
        build_semantic_obligation_inventory,
    )
    from emlis_ai_step10_app_reachable_contract_v3 import (
        project_app_reachable_input,
    )
    from emlis_ai_step11_grounded_lexicalization_v3 import (
        build_step11_rc0028_experiment_lexical_atom_specs,
    )
    from emlis_ai_step11_planning_frontier_v3 import (
        build_step11_terminal_pair_discourse_plans,
    )

    projected = project_app_reachable_input(dict(projected_input))
    normalized = normalize_emlis_current_input(dict(projected))
    evidence_spans = tuple(build_evidence_ledger(normalized))
    resolver = build_evidence_span_resolver(
        evidence_spans,
        current_input=normalized,
    )
    reports = tuple(run_perspective_observers(evidence_spans))
    board = build_perspective_board(
        evidence_spans=evidence_spans,
        reports=reports,
    )
    graph = integrate_perspective_board(board=board)
    safety_decision = build_emlis_safety_triage_decision(
        current_input=normalized,
        graph=graph,
        evidence_spans=evidence_spans,
    )
    grounded_plan = build_grounded_observation_plan(
        normalized,
        evidence_spans=evidence_spans,
        reports=reports,
        board=board,
        graph=graph,
        safety_decision=safety_decision,
    )
    stage = build_observation_stage_context(
        stage="normal_observation",
        original_input_bundle=normalized,
    )
    snapshot = build_grounded_source_snapshot(
        grounded_plan,
        resolver,
        observation_stage_context=stage,
        original_input_bundle=normalized,
    )
    inventory = build_semantic_obligation_inventory(snapshot)
    content_plan = build_content_selection_plan(inventory)
    try:
        discourse = build_discourse_graph_plans(inventory, content_plan)
    except DiscourseGraphPlannerError as exc:
        if exc.code != "NO_SAFE_DISCOURSE_STRUCTURE":
            raise
        discourse = build_step11_terminal_pair_discourse_plans(
            inventory,
            content_plan,
        )
    discourse_plans = tuple(discourse.plans)
    if not discourse_plans:
        raise CurrentRcG8RunError(
            "CURRENT_RC_G8_DIRECT_SOURCE_CONTEXT_INVALID"
        )
    successor = build_grounded_lexical_role_experiment_snapshot_successor(
        grounded_plan,
        resolver,
        observation_stage_context=stage,
        original_input_bundle=normalized,
    )
    lexical_specs = build_step11_rc0028_experiment_lexical_atom_specs(successor)
    return _DirectRecoveryContext(
        normalized_input=normalized,
        projected_current_input=projected,
        resolver=resolver,
        grounded_plan=grounded_plan,
        observation_stage_context=stage,
        inventory_result=inventory,
        content_plan=content_plan,
        discourse_plans=discourse_plans,
        successor_snapshot=successor,
        lexical_atom_specs=lexical_specs,
    )


def _ordered_unique_strings(values: Sequence[Any]) -> tuple[str, ...]:
    return tuple(dict.fromkeys(str(value) for value in values))


def _source_dimensions(value: Any) -> tuple[str, str, str, str]:
    return (
        str(value.temporal_scope),
        str(value.modality),
        str(value.polarity),
        str(value.referent_scope),
    )


def _aggregate_source_dimensions(
    values: Sequence[tuple[str, str, str, str]],
) -> tuple[str, str, str, str]:
    rows = tuple(values)
    if not rows:
        raise CurrentRcG8RunError(
            "CURRENT_RC_G8_DIRECT_SOURCE_CONTEXT_INVALID"
        )
    return tuple(
        column[0] if len(set(column)) == 1 else "unknown"
        for column in zip(*rows, strict=True)
    )  # type: ignore[return-value]


def _relation_source_dimensions(
    atom_id: str,
    family: str,
    *,
    context: _DirectRecoveryContext,
) -> tuple[str, str, str, str]:
    snapshot = context.successor_snapshot.base_snapshot
    if family == "relation":
        authorities = tuple(
            row
            for row in context.successor_snapshot.relation_construction_authority.relation_authorities
            if str(row.experiment_relation_id) == atom_id
        )
        if len(authorities) != 1:
            raise CurrentRcG8RunError(
                "CURRENT_RC_G8_DIRECT_SOURCE_CONTEXT_INVALID"
            )
        authority = authorities[0]
        aliases = {str(authority.source_relation_id)}
        if authority.refines_source_relation_id is not None:
            aliases.add(str(authority.refines_source_relation_id))
        matches = tuple(
            row
            for row in snapshot.relations
            if aliases & {str(row.source_id), str(row.actual_source_id)}
        )
        if not matches:
            aliases.update(str(value) for value in authority.source_relation_ids)
            matches = tuple(
                row
                for row in snapshot.relations
                if aliases
                & {
                    str(row.source_id),
                    str(row.actual_source_id),
                    *(str(value) for value in row.source_relation_ids),
                }
            )
    elif family == "semantic_link":
        matches = tuple(
            row
            for row in snapshot.relations
            if atom_id in {str(row.source_id), str(row.actual_source_id)}
        )
    else:
        raise CurrentRcG8RunError(
            "CURRENT_RC_G8_DIRECT_SOURCE_CONTEXT_INVALID"
        )
    if len(matches) != 1:
        raise CurrentRcG8RunError(
            "CURRENT_RC_G8_DIRECT_SOURCE_CONTEXT_INVALID"
        )
    source = matches[0]
    return (
        str(source.temporal_scope),
        str(source.modality),
        str(source.polarity),
        "relation",
    )


def _direct_expected_recovery_base(
    context: _DirectRecoveryContext,
) -> _ExpectedRecovery:
    """Derive the complete expected recovery signature from upstream only."""

    from emlis_ai_grounded_observation_semantic_restatement_v3 import (
        build_grounded_semantic_restatement_witness,
    )
    from emlis_ai_nls_v3_artifact_contract import artifact_sha256
    from emlis_ai_step11_natural_surface_v3 import (
        _step11_rc0031_product_surface_authorities,
        project_step11_current_input,
    )
    from emlis_ai_step11_rc0029_experiment_surface_catalog_v3 import (
        STEP11_RC0029_EXPERIMENT_SURFACE_CATALOG,
        STEP11_RC0029_EXPERIMENT_SURFACE_CATALOG_SHA256,
    )

    snapshot = context.successor_snapshot.base_snapshot
    lexical = context.lexical_atom_specs
    witness = build_grounded_semantic_restatement_witness(
        context.grounded_plan, context.resolver
    )
    if (
        witness.plan_binding_sha256
        != snapshot.semantic_restatement_plan_binding_sha256
        or witness.witness_sha256
        != snapshot.source_semantic_restatement_witness_sha256
    ):
        raise CurrentRcG8RunError(
            "CURRENT_RC_G8_DIRECT_SOURCE_CONTEXT_INVALID"
        )
    owner_registry = tuple(
        str(row.source_owner_id) for row in lexical.owner_bindings
    )
    owner_by_ordinal = {
        int(row.owner_ordinal): str(row.source_owner_id)
        for row in lexical.owner_bindings
    }
    owner_kind_by_id = {
        str(row.source_owner_id): str(row.source_owner_kind)
        for row in lexical.owner_bindings
    }
    nucleus_by_owner = {
        str(row.actual_source_id): row for row in snapshot.nuclei
    }
    source_to_owner = {
        str(row.source_id): str(row.actual_source_id) for row in snapshot.nuclei
    }
    dimensions_by_owner = {
        owner_id: _source_dimensions(row)
        for owner_id, row in nucleus_by_owner.items()
    }

    receptions: list[_ExpectedReception] = []
    opportunities = tuple(
        row
        for row in snapshot.reception_opportunities
        if row.retention == "required" or row.safety_required is True
    )
    for ordinal, opportunity in enumerate(opportunities, start=1):
        targets = _ordered_unique_strings(
            source_to_owner.get(str(value), str(value))
            for value in opportunity.target_nucleus_ids
        )
        supports = _ordered_unique_strings(
            source_to_owner.get(str(value), str(value))
            for value in opportunity.support_nucleus_ids
        )
        focus_owner_ids = _ordered_unique_strings((*targets, *supports))
        if (
            not targets
            or not focus_owner_ids
            or any(value not in nucleus_by_owner for value in targets)
            or any(value not in nucleus_by_owner for value in supports)
            or any(value not in nucleus_by_owner for value in focus_owner_ids)
        ):
            raise CurrentRcG8RunError(
                "CURRENT_RC_G8_DIRECT_SOURCE_CONTEXT_INVALID"
            )
        inventory_act = str(opportunity.reception_act)
        concrete_action = all(
            str(nucleus_by_owner[value].modality) in {"observed", "reported"}
            and str(nucleus_by_owner[value].temporal_scope)
            not in {"future", "present_to_future", "intended_future"}
            for value in targets
        )
        if inventory_act == "honor_concrete_action" and not concrete_action:
            effective = "do_not_dismiss"
            basis = "nonactual_action_nonpromotion"
        else:
            effective = inventory_act
            basis = "source_reception_act_projection"
        receptions.append(
            _ExpectedReception(
                source_reception_opportunity_id=str(opportunity.source_id),
                source_scope=str(opportunity.family),
                source_focus_owner_ids=focus_owner_ids,
                source_target_owner_ids=targets,
                supporting_source_owner_ids=supports,
                visible_support_owner_ids=tuple(
                    value for value in supports if value not in set(targets)
                ),
                inventory_reception_act=inventory_act,
                effective_reception_act=effective,
                act_refinement_basis=basis,
                sentence_group_ordinal=ordinal,
            )
        )

    focus_owner_ids = _ordered_unique_strings(
        value for row in receptions for value in row.source_focus_owner_ids
    )

    obligations = tuple(context.inventory_result.ledger["obligations"])
    grounded_nucleus_by_id = {
        str(row.nucleus_id): row for row in context.grounded_plan.nuclei
    }
    semantic_unit_by_id = {
        str(row.unit_id): row for row in witness.semantic_units
    }

    def fragment(
        *,
        owner_id: str,
        nucleus_id: str,
        span_id: str,
        start: int,
        end: int,
        basis: str,
        expected_artifact_sha256: str | None = None,
    ) -> _ExpectedFragment:
        span = context.resolver.resolve(span_id)
        raw_text = str(span.raw_text)
        text = raw_text[start:end]
        if (
            not text
            or start < 0
            or end <= start
            or end > len(raw_text)
            or (
                expected_artifact_sha256 is not None
                and artifact_sha256({"source_fragment": text})
                != expected_artifact_sha256
            )
        ):
            raise CurrentRcG8RunError(
                "CURRENT_RC_G8_DIRECT_SOURCE_CONTEXT_INVALID"
            )
        text_sha256 = hashlib.sha256(text.encode("utf-8")).hexdigest()
        material = {
            "source_owner_id": owner_id,
            "source_nucleus_id": nucleus_id,
            "source_span_id": span_id,
            "source_field": str(span.source_field),
            "span_relative_start_index": start,
            "span_relative_end_index": end,
            "source_fragment_text_sha256": text_sha256,
            "binding_basis": basis,
        }
        return _ExpectedFragment(
            source_fragment_id=(
                "nls3s11rc0036fragment_" + artifact_sha256(material)[:16]
            ),
            source_owner_id=owner_id,
            source_nucleus_id=nucleus_id,
            source_span_id=span_id,
            source_field=str(span.source_field),
            span_relative_start_index=start,
            span_relative_end_index=end,
            source_fragment_text=text,
            source_fragment_text_sha256=text_sha256,
            binding_basis=basis,
        )

    root_active_owner_ids = {
        *focus_owner_ids,
        *(
            value
            for row in receptions
            for value in (
                *row.source_target_owner_ids,
                *row.visible_support_owner_ids,
            )
        ),
        *(
            owner_by_ordinal[int(value)]
            for row in lexical.construction_atoms
            for value in row.target_owner_ordinals
        ),
        *(str(row.source_owner_id) for row in lexical.relation_endpoint_atoms),
        *(
            value
            for row in lexical.semantic_link_atoms
            for value in (
                str(row.from_semantic_unit_id),
                str(row.to_semantic_unit_id),
            )
        ),
        *(
            str(owner_id)
            for row in lexical.explicit_unknown_atoms
            for _kind, owner_id, _ordinal in row.affected_source_owners
        ),
    }
    roots: list[_ExpectedRoot] = []
    for nucleus in snapshot.nuclei:
        owner_id = str(nucleus.actual_source_id)
        if nucleus.required is not True and owner_id not in root_active_owner_ids:
            continue
        nucleus_id = str(nucleus.source_id)
        aliases = {owner_id, nucleus_id}
        obligation_ids = tuple(
            str(row["obligation_id"])
            for row in obligations
            if type(row) is dict
            and row.get("required") is True
            and aliases & {str(value) for value in row.get("nucleus_ids", ())}
        )
        semantic_unit = semantic_unit_by_id.get(owner_id)
        if semantic_unit is not None:
            fragments = (
                fragment(
                    owner_id=owner_id,
                    nucleus_id=nucleus_id,
                    span_id=str(semantic_unit.source_span_id),
                    start=int(semantic_unit.start_index),
                    end=int(semantic_unit.end_index),
                    basis="semantic_unit_exact_typed_range",
                    expected_artifact_sha256=str(
                        semantic_unit.source_fragment_sha256
                    ),
                ),
            )
        else:
            grounded = grounded_nucleus_by_id.get(owner_id)
            if grounded is None:
                raise CurrentRcG8RunError(
                    "CURRENT_RC_G8_DIRECT_SOURCE_CONTEXT_INVALID"
                )
            span_ids = _ordered_unique_strings(grounded.source_span_ids)
            fragments = tuple(
                fragment(
                    owner_id=owner_id,
                    nucleus_id=nucleus_id,
                    span_id=span_id,
                    start=0,
                    end=len(str(context.resolver.resolve(span_id).raw_text)),
                    basis="grounded_nucleus_exact_evidence_span",
                )
                for span_id in span_ids
            )
        dimensions = _source_dimensions(nucleus)
        root_material = {
            "source_owner_id": owner_id,
            "source_nucleus_id": nucleus_id,
            "source_obligation_ids": list(obligation_ids),
            "source_fragment_ids": [
                row.source_fragment_id for row in fragments
            ],
            "semantic_kind": str(nucleus.kind),
            "dimensions": list(dimensions),
            "required": bool(nucleus.required),
        }
        roots.append(
            _ExpectedRoot(
                source_root_id=(
                    "nls3s11rc0036root_"
                    + artifact_sha256(root_material)[:16]
                ),
                source_owner_id=owner_id,
                source_nucleus_id=nucleus_id,
                source_obligation_ids=obligation_ids,
                source_fragments=fragments,
                semantic_kind=str(nucleus.kind),
                dimensions=dimensions,
                required=bool(nucleus.required),
            )
        )

    atom_rows: list[_ExpectedAtom] = []
    construction_spec_by_slot = {
        str(row.construction_slot_id): row
        for row in lexical.construction_atoms
    }
    for ordinal, instance in enumerate(lexical.construction_instances, start=1):
        roles: list[_ExpectedConstructionRole] = []
        owner_ids: list[str] = []
        forward_roles: list[tuple[Any, ...]] = []
        for slot_id_value in instance.slot_ids:
            slot_id = str(slot_id_value)
            spec = construction_spec_by_slot[slot_id]
            role_owner_ids = tuple(
                owner_by_ordinal[int(value)]
                for value in spec.target_owner_ordinals
            )
            role_dimensions = tuple(
                dimensions_by_owner[value] for value in role_owner_ids
            )
            owner_ids.extend(role_owner_ids)
            roles.append(
                _ExpectedConstructionRole(
                    construction_slot_id=slot_id,
                    parent_nucleus_id=str(spec.parent_nucleus_id),
                    source_span_id=str(spec.source_span_id),
                    slot_start_index=int(spec.slot_start_index),
                    slot_end_index=int(spec.slot_end_index),
                    lexical_role_kind=str(spec.lexical_role_kind),
                    construction_position=str(spec.construction_position),
                    role_position_surface_token=str(
                        spec.role_position_surface_token
                    ),
                    source_owner_ids=role_owner_ids,
                    source_owner_dimensions=role_dimensions,
                    participation_ids=tuple(
                        str(value) for value in spec.participation_ids
                    ),
                )
            )
            forward_roles.append(
                (
                    slot_id,
                    str(spec.lexical_role_kind),
                    str(spec.construction_position),
                    str(spec.role_position_atom_code),
                    str(spec.role_position_surface_token),
                    tuple(int(value) for value in spec.target_owner_ordinals),
                    tuple(str(value) for value in spec.participation_ids),
                )
            )
        owners = _ordered_unique_strings(owner_ids)
        atom_rows.append(
            _ExpectedAtom(
                source_atom_id=str(instance.construction_instance_id),
                semantic_family="construction",
                semantic_key=str(instance.construction_code),
                source_owner_ids=owners,
                direction="",
                dimensions=_aggregate_source_dimensions(
                    tuple(dimensions_by_owner[value] for value in owners)
                ),
                source_nucleus_owner_ids=tuple(
                    value
                    for value in owners
                    if owner_kind_by_id[value] == "nucleus"
                ),
                source_semantic_unit_owner_ids=tuple(
                    value
                    for value in owners
                    if owner_kind_by_id[value] == "semantic_unit"
                ),
                source_parent_nucleus_ids=(str(instance.parent_nucleus_id),),
                source_span_ids=(str(instance.source_span_id),),
                source_evidence_alias_ids=tuple(
                    str(value) for value in instance.evidence_alias_ids
                ),
                source_marker_span_ids=(),
                source_grounding_kind="",
                source_relation_ids=(),
                authority_basis="",
                source_retention="",
                construction_roles=tuple(roles),
                source_order=len(atom_rows) + 1,
                surface_token=str(instance.construction_surface_token),
                forward_signature=(
                    "construction",
                    ordinal,
                    str(instance.construction_instance_id),
                    str(instance.construction_code),
                    str(instance.construction_atom_code),
                    str(instance.construction_surface_token),
                    tuple(str(value) for value in instance.slot_ids),
                    tuple(forward_roles),
                ),
            )
        )

    relation_specs: dict[str, list[Any]] = {}
    for spec in lexical.relation_endpoint_atoms:
        relation_specs.setdefault(str(spec.experiment_relation_id), []).append(
            spec
        )
    for ordinal, authority in enumerate(
        context.successor_snapshot.lexical_role_witness.relation_authorities,
        start=1,
    ):
        atom_id = str(authority.experiment_relation_id)
        owners = (
            str(authority.from_source_owner_id),
            str(authority.to_source_owner_id),
        )
        source_spans = _ordered_unique_strings(
            str(value)
            for spec in relation_specs.get(atom_id, ())
            for value in (
                *spec.evidence_alias_ids,
                *((spec.marker_source_span_id,)
                  if spec.marker_source_span_id is not None else ()),
            )
        )
        atom_rows.append(
            _ExpectedAtom(
                source_atom_id=atom_id,
                semantic_family="relation",
                semantic_key=str(authority.effective_relation_type),
                source_owner_ids=owners,
                direction=str(authority.direction),
                dimensions=_relation_source_dimensions(
                    atom_id, "relation", context=context
                ),
                source_nucleus_owner_ids=tuple(
                    value
                    for value in owners
                    if owner_kind_by_id[value] == "nucleus"
                ),
                source_semantic_unit_owner_ids=tuple(
                    value
                    for value in owners
                    if owner_kind_by_id[value] == "semantic_unit"
                ),
                source_parent_nucleus_ids=_ordered_unique_strings(
                    value
                    for spec in relation_specs.get(atom_id, ())
                    for value in (
                        spec.source_from_nucleus_id,
                        spec.source_to_nucleus_id,
                    )
                ),
                source_span_ids=(),
                source_evidence_alias_ids=_ordered_unique_strings(
                    value
                    for spec in relation_specs.get(atom_id, ())
                    for value in spec.evidence_alias_ids
                ),
                source_marker_span_ids=_ordered_unique_strings(
                    str(spec.marker_source_span_id)
                    for spec in relation_specs.get(atom_id, ())
                    if spec.marker_source_span_id is not None
                ),
                source_grounding_kind=str(authority.source_grounding_kind),
                source_relation_ids=tuple(
                    str(value) for value in authority.source_relation_ids
                ),
                authority_basis=str(authority.authority_basis),
                source_retention=str(authority.source_retention),
                construction_roles=(),
                source_order=len(atom_rows) + 1,
                surface_token="",
                forward_signature=(
                    "relation",
                    ordinal,
                    atom_id,
                    str(authority.source_relation_id),
                    str(authority.source_relation_type),
                    str(authority.effective_relation_type),
                    owner_registry.index(owners[0]) + 1,
                    owner_registry.index(owners[1]) + 1,
                    str(authority.direction),
                    str(authority.authority_basis),
                    str(authority.source_retention),
                    str(authority.experiment_retention),
                    None
                    if authority.refines_source_relation_id is None
                    else str(authority.refines_source_relation_id),
                ),
            )
        )

    link_spec_by_id = {
        str(row.source_semantic_link_id): row
        for row in lexical.semantic_link_atoms
    }
    for ordinal, link in enumerate(
        context.successor_snapshot.lexical_role_witness.semantic_link_bindings,
        start=1,
    ):
        atom_id = str(link.source_semantic_link_id)
        owners = (
            str(link.from_semantic_unit_id),
            str(link.to_semantic_unit_id),
        )
        spec = link_spec_by_id[atom_id]
        atom_rows.append(
            _ExpectedAtom(
                source_atom_id=atom_id,
                semantic_family="semantic_link",
                semantic_key=str(link.relation_type),
                source_owner_ids=owners,
                direction=str(link.direction),
                dimensions=_relation_source_dimensions(
                    atom_id, "semantic_link", context=context
                ),
                source_nucleus_owner_ids=tuple(
                    value
                    for value in owners
                    if owner_kind_by_id[value] == "nucleus"
                ),
                source_semantic_unit_owner_ids=tuple(
                    value
                    for value in owners
                    if owner_kind_by_id[value] == "semantic_unit"
                ),
                source_parent_nucleus_ids=(),
                source_span_ids=(str(spec.source_span_id),),
                source_evidence_alias_ids=(),
                source_marker_span_ids=(),
                source_grounding_kind="explicit_semantic_link",
                source_relation_ids=(atom_id,),
                authority_basis="semantic_link_binding",
                source_retention="required" if bool(link.required) else "optional",
                construction_roles=(),
                source_order=len(atom_rows) + 1,
                surface_token="",
                forward_signature=(
                    "semantic_link",
                    ordinal,
                    atom_id,
                    str(link.relation_type),
                    owner_registry.index(owners[0]) + 1,
                    owner_registry.index(owners[1]) + 1,
                    str(link.direction),
                    bool(link.required),
                ),
            )
        )

    unknown_spec_by_id = {
        str(row.source_unknown_id): row for row in lexical.explicit_unknown_atoms
    }
    for ordinal, unknown in enumerate(
        context.successor_snapshot.lexical_role_witness.explicit_unknown_bindings,
        start=1,
    ):
        atom_id = str(unknown.source_unknown_id)
        owners = tuple(
            str(value.owner_id) for value in unknown.affected_source_owners
        )
        spec = unknown_spec_by_id[atom_id]
        atom_rows.append(
            _ExpectedAtom(
                source_atom_id=atom_id,
                semantic_family="explicit_unknown",
                semantic_key=str(unknown.dimension),
                source_owner_ids=owners,
                direction="",
                dimensions=("unknown", "unknown", "unknown", "unknown"),
                source_nucleus_owner_ids=tuple(
                    value
                    for value in owners
                    if owner_kind_by_id[value] == "nucleus"
                ),
                source_semantic_unit_owner_ids=tuple(
                    value
                    for value in owners
                    if owner_kind_by_id[value] == "semantic_unit"
                ),
                source_parent_nucleus_ids=(),
                source_span_ids=(str(spec.source_span_id),),
                source_evidence_alias_ids=(),
                source_marker_span_ids=(),
                source_grounding_kind="",
                source_relation_ids=(),
                authority_basis="",
                source_retention="",
                construction_roles=(),
                source_order=len(atom_rows) + 1,
                surface_token="",
                forward_signature=(
                    "explicit_unknown",
                    ordinal,
                    atom_id,
                    str(unknown.dimension),
                    tuple(owner_registry.index(value) + 1 for value in owners),
                    bool(unknown.required),
                ),
            )
        )

    active_owner_ids = {
        *(row.source_owner_id for row in roots),
        *(owner for row in atom_rows for owner in row.source_owner_ids),
        *(
            owner
            for row in receptions
            for owner in row.source_target_owner_ids
        ),
    } | {
        owner
        for row in receptions
        for owner in (
            *row.source_focus_owner_ids,
            *row.visible_support_owner_ids,
        )
        if owner in set(owner_registry) and owner in nucleus_by_owner
    }
    role_catalog = STEP11_RC0029_EXPERIMENT_SURFACE_CATALOG[
        "owner_role_surface_tokens"
    ]
    role_tokens: dict[str, list[str]] = {}

    def add_role(owner_id: str, token: str) -> None:
        role_tokens.setdefault(owner_id, []).append(token)

    for spec in lexical.construction_atoms:
        for ordinal in spec.target_owner_ordinals:
            add_role(
                owner_by_ordinal[int(ordinal)],
                str(spec.role_position_surface_token),
            )
    for spec in lexical.relation_endpoint_atoms:
        add_role(
            str(spec.source_owner_id),
            str(spec.relation_surface_token)
            + str(role_catalog["relation_" + spec.relation_endpoint_role]),
        )
    for spec in lexical.semantic_link_atoms:
        add_role(
            str(spec.from_semantic_unit_id),
            str(spec.semantic_link_surface_token)
            + str(role_catalog["semantic_link_from"]),
        )
        add_role(
            str(spec.to_semantic_unit_id),
            str(spec.semantic_link_surface_token)
            + str(role_catalog["semantic_link_to"]),
        )
    for spec in lexical.explicit_unknown_atoms:
        for _kind, owner_id, _ordinal in spec.affected_source_owners:
            add_role(
                str(owner_id),
                str(spec.unknown_surface_token)
                + str(role_catalog["explicit_unknown"]),
            )
    for reception in receptions:
        for owner_id in reception.source_target_owner_ids:
            add_role(owner_id, str(role_catalog["reception_target"]))
        for owner_id in reception.visible_support_owner_ids:
            add_role(owner_id, str(role_catalog["reception_support"]))
        for owner_id in reception.source_focus_owner_ids:
            add_role(owner_id, str(role_catalog["reception_antecedent"]))
    unique_role_tokens = {
        owner_id: _ordered_unique_strings(values)
        for owner_id, values in role_tokens.items()
    }
    owner_specs = tuple(
        row
        for row in lexical.owner_bindings
        if str(row.source_owner_id) in active_owner_ids
    )
    head_catalog = STEP11_RC0029_EXPERIMENT_SURFACE_CATALOG[
        "owner_kind_surface_tokens"
    ]
    prepared = tuple(
        (
            row,
            nucleus_by_owner[str(row.source_owner_id)],
            str(head_catalog[str(nucleus_by_owner[str(row.source_owner_id)].kind)]),
            unique_role_tokens.get(str(row.source_owner_id), ()),
        )
        for row in owner_specs
    )
    referents = [row[2] for row in prepared]
    duplicate_heads = {
        head
        for head, count in Counter(referents).items()
        if count > 1
    }
    for head in duplicate_heads:
        indices = tuple(
            index
            for index, _row in enumerate(prepared)
            if prepared[index][2] == head
        )
        options_by_index = {index: prepared[index][3] for index in indices}
        assigned: dict[int, str] = {}
        for index in indices:
            for option in options_by_index[index]:
                if sum(
                    option in options_by_index[other] for other in indices
                ) == 1:
                    assigned[index] = option + "に関わる" + head
                    break
        for index in indices:
            if index in assigned:
                continue
            joined = "、".join(options_by_index[index])
            if joined:
                candidate = joined + "に関わる" + head
                other_candidates = tuple(
                    "、".join(options_by_index[other]) + "に関わる" + head
                    for other in indices
                    if other not in assigned and options_by_index[other]
                )
                if candidate not in other_candidates:
                    assigned[index] = candidate
        unresolved = tuple(index for index in indices if index not in assigned)
        if len(unresolved) > 1:
            raise CurrentRcG8RunError(
                "CURRENT_RC_G8_DIRECT_SOURCE_CONTEXT_INVALID"
            )
        for index, referent in assigned.items():
            referents[index] = referent
        if len({referents[index] for index in indices}) != len(indices):
            raise CurrentRcG8RunError(
                "CURRENT_RC_G8_DIRECT_SOURCE_CONTEXT_INVALID"
            )
    if len(set(referents)) != len(referents):
        raise CurrentRcG8RunError(
            "CURRENT_RC_G8_DIRECT_SOURCE_CONTEXT_INVALID"
        )
    owners = tuple(
        _ExpectedOwner(
            schema_version=_RECOVERY_OWNER_SCHEMA,
            source_owner_id=str(spec.source_owner_id),
            source_owner_kind=str(spec.source_owner_kind),
            source_owner_ordinal=int(spec.owner_ordinal),
            source_nucleus_id=str(nucleus.source_id),
            semantic_kind=str(nucleus.kind),
            dimensions=_source_dimensions(nucleus),
            typed_role_tokens=tuple(tokens),
            referent_text=referent,
            referent_text_sha256=hashlib.sha256(
                referent.encode("utf-8")
            ).hexdigest(),
            referent_basis=(
                "typed_kind"
                if referent == head
                else "typed_incident_role_disambiguation"
            ),
        )
        for (spec, nucleus, head, tokens), referent in zip(
            prepared, referents, strict=True
        )
    )

    projection = project_step11_current_input(context.projected_current_input)
    projection_material = {
        "thought_text": projection.thought_text,
        "action_text": projection.action_text,
        "emotions": list(projection.emotions),
        "categories": list(projection.categories),
    }
    normalized_sha256 = artifact_sha256(context.normalized_input)
    input_binding = (
        projection.thought_text,
        projection.action_text,
        tuple(projection.emotions),
        tuple(projection.categories),
        artifact_sha256(projection_material),
        normalized_sha256,
        str(
            snapshot.observation_stage_source_binding.original_input_bundle_sha256
        ),
    )
    _catalog_owner, catalog, grammar, catalog_sha256 = (
        _step11_rc0031_product_surface_authorities()
    )
    discourse_sha256 = artifact_sha256(
        {
            "ordered_discourse_plan_sha256s": [
                artifact_sha256(row) for row in context.discourse_plans
            ],
            "discourse_plan_count": len(context.discourse_plans),
        }
    )
    source_commitments = (
        ("source_observation_plan_sha256", str(snapshot.source_observation_plan_sha256)),
        ("source_successor_snapshot_sha256", str(context.successor_snapshot.experiment_snapshot_sha256)),
        ("source_lexical_atom_specs_sha256", str(lexical.specs_sha256)),
        ("source_semantic_restatement_witness_sha256", str(witness.witness_sha256)),
        ("source_inventory_ledger_sha256", artifact_sha256(context.inventory_result.ledger)),
        ("source_content_plan_sha256", artifact_sha256(context.content_plan)),
        ("source_discourse_plan_sha256", discourse_sha256),
        ("source_lexical_catalog_sha256", STEP11_RC0029_EXPERIMENT_SURFACE_CATALOG_SHA256),
        ("surface_catalog_sha256", str(catalog_sha256)),
    )
    family_counts = Counter(row.semantic_family for row in atom_rows)
    source_counts = (
        ("owners", len(owners)),
        ("roots", len(roots)),
        ("constructions", family_counts.get("construction", 0)),
        ("relations", family_counts.get("relation", 0)),
        ("semantic_links", family_counts.get("semantic_link", 0)),
        ("explicit_unknowns", family_counts.get("explicit_unknown", 0)),
        ("receptions", len(receptions)),
    )
    construction_material: list[dict[str, Any]] = []
    relation_material: list[dict[str, Any]] = []
    link_material: list[dict[str, Any]] = []
    unknown_material: list[dict[str, Any]] = []
    for atom in atom_rows:
        row = atom.forward_signature
        if atom.semantic_family == "construction":
            construction_material.append(
                {
                    "ordinal": row[1],
                    "construction_instance_id": row[2],
                    "construction_code": row[3],
                    "catalog_atom_code": row[4],
                    "surface_token": row[5],
                    "construction_slot_ids": list(row[6]),
                    "role_atoms": [
                        {
                            "construction_slot_id": role[0],
                            "lexical_role_kind": role[1],
                            "construction_position": role[2],
                            "role_position_atom_code": role[3],
                            "role_position_surface_token": role[4],
                            "target_owner_ordinals": list(role[5]),
                            "participation_ids": list(role[6]),
                        }
                        for role in row[7]
                    ],
                }
            )
        elif atom.semantic_family == "relation":
            relation_material.append(
                {
                    "ordinal": row[1],
                    "experiment_relation_id": row[2],
                    "source_relation_id": row[3],
                    "source_relation_type": row[4],
                    "effective_relation_type": row[5],
                    "from_owner_ordinal": row[6],
                    "to_owner_ordinal": row[7],
                    "direction": row[8],
                    "authority_basis": row[9],
                    "source_retention": row[10],
                    "experiment_retention": row[11],
                    "refines_source_relation_id": row[12],
                }
            )
        elif atom.semantic_family == "semantic_link":
            link_material.append(
                {
                    "ordinal": row[1],
                    "source_semantic_link_id": row[2],
                    "relation_type": row[3],
                    "from_owner_ordinal": row[4],
                    "to_owner_ordinal": row[5],
                    "direction": row[6],
                    "required": row[7],
                }
            )
        elif atom.semantic_family == "explicit_unknown":
            unknown_material.append(
                {
                    "ordinal": row[1],
                    "source_unknown_id": row[2],
                    "dimension": row[3],
                    "affected_owner_ordinals": list(row[4]),
                    "required": row[5],
                }
            )
    typed_payload_sha256 = artifact_sha256(
        {
            "owner_registry": list(owner_registry),
            "construction_atoms": construction_material,
            "relation_atoms": relation_material,
            "semantic_link_atoms": link_material,
            "explicit_unknown_atoms": unknown_material,
            "reception_bindings": [
                {
                    "source_reception_opportunity_id": (
                        row.source_reception_opportunity_id
                    ),
                    "source_scope": row.source_scope,
                    "source_focus_owner_ids": list(
                        row.source_focus_owner_ids
                    ),
                    "source_target_owner_ids": list(
                        row.source_target_owner_ids
                    ),
                    "supporting_source_owner_ids": list(
                        row.supporting_source_owner_ids
                    ),
                    "visible_support_owner_ids": list(
                        row.visible_support_owner_ids
                    ),
                    "inventory_reception_act": row.inventory_reception_act,
                    "effective_reception_act": row.effective_reception_act,
                    "act_refinement_basis": row.act_refinement_basis,
                    "sentence_group_ordinal": row.sentence_group_ordinal,
                }
                for row in receptions
            ],
        }
    )
    candidate_boundary_sha256 = artifact_sha256(
        {
            "semantic_coverage_authorized": True,
            "old_gate_consulted": False,
            "old_selector_consulted": False,
            "base_acceptance_claimed": False,
            "experimental_only": True,
            "private_body_full": True,
            "shareable": False,
            "runtime_connected": False,
        }
    )
    return _ExpectedRecovery(
        owner_registry=owner_registry,
        owners=owners,
        roots=tuple(roots),
        atoms=tuple(atom_rows),
        receptions=tuple(receptions),
        source_counts=source_counts,
        source_commitments=source_commitments,
        current_input_binding=input_binding,
        typed_payload_sha256=typed_payload_sha256,
        candidate_boundary_sha256=candidate_boundary_sha256,
        catalog=catalog,
        grammar=grammar,
    )


def _expected_active_discourse_plan(
    context: _DirectRecoveryContext,
) -> Mapping[str, Any]:
    """Select a source topology without consulting the production renderer."""

    obligations = tuple(context.inventory_result.ledger["obligations"])
    obligation_rank = {
        str(row["obligation_id"]): ordinal
        for ordinal, row in enumerate(obligations)
    }

    def topology_key(plan: Mapping[str, Any]) -> tuple[Any, ...]:
        nodes = tuple(plan.get("nodes", ()))
        groups = tuple(plan.get("sentence_groups", ()))
        edges = tuple(plan.get("edges", ()))
        node_obligation = {
            str(row["node_id"]): str(row["obligation_id"])
            for row in nodes
        }
        if (
            len(node_obligation) != len(nodes)
            or not set(node_obligation.values()) <= set(obligation_rank)
        ):
            raise CurrentRcG8RunError(
                "CURRENT_RC_G8_DIRECT_SOURCE_CONTEXT_INVALID"
            )
        group_topology = tuple(
            (
                0 if str(group["section_role"]) == "observation" else 1,
                tuple(
                    obligation_rank[node_obligation[str(node_id)]]
                    for node_id in group["node_ids"]
                ),
            )
            for group in groups
        )
        observation_widths = tuple(
            len(group["node_ids"])
            for group in groups
            if str(group["section_role"]) == "observation"
        )
        reception_widths = tuple(
            len(group["node_ids"])
            for group in groups
            if str(group["section_role"]) == "reception"
        )
        edge_topology = tuple(
            sorted(
                (
                    str(edge["type"]),
                    obligation_rank[node_obligation[str(edge["from"])]],
                    obligation_rank[node_obligation[str(edge["to"])]],
                )
                for edge in edges
            )
        )
        return (
            max(observation_widths, default=0),
            max(reception_widths, default=0),
            -len(observation_widths),
            -len(reception_widths),
            group_topology,
            edge_topology,
        )

    plans = tuple(context.discourse_plans)
    if not plans:
        raise CurrentRcG8RunError(
            "CURRENT_RC_G8_DIRECT_SOURCE_CONTEXT_INVALID"
        )
    return min(plans, key=topology_key)


def _expected_overlay_visible_features(overlay: Any) -> dict[str, dict[str, str]]:
    from emlis_ai_step11_surface_catalog_v3 import STEP11_SURFACE_CATALOG

    strength_by_anchor = {
        str(row.label_anchor_id): row.strength
        for row in overlay.label_anchors
    }
    allowed_lifecycles = frozenset(
        STEP11_SURFACE_CATALOG["grounded_lexicalization"]
        ["lifecycle_authority_policy"]["action_projection"]
    )
    result: dict[str, dict[str, str]] = {}
    for binding in overlay.nucleus_anchor_bindings:
        strengths = {
            strength_by_anchor[str(anchor_id)]
            for anchor_id in binding.source_label_anchor_ids
            if str(anchor_id) in strength_by_anchor
            and strength_by_anchor[str(anchor_id)] is not None
        }
        if len(strengths) > 1:
            raise CurrentRcG8RunError(
                "CURRENT_RC_G8_DIRECT_SOURCE_CONTEXT_INVALID"
            )
        if strengths:
            result.setdefault(str(binding.nucleus_id), {})[
                "label_strength"
            ] = str(next(iter(strengths)))
        if str(binding.realization_status) in allowed_lifecycles:
            result.setdefault(str(binding.nucleus_id), {})[
                "realization_lifecycle"
            ] = str(binding.realization_status)
    return result


def _build_expected_projection_authority(
    context: _DirectRecoveryContext,
) -> _ExpectedVisibleAuthority:
    """Rebuild active overlay and grounded owner phrases from source only."""

    from emlis_ai_nls_v3_artifact_contract import artifact_sha256
    from emlis_ai_step11_grounded_lexicalization_v3 import (
        Step11GroundedLexicalizationError,
        build_step11_grounded_phrase_specs,
        render_step11_grounded_phrase,
        select_step11_visible_source_anchor_use,
    )
    from emlis_ai_step11_semantic_overlay_v3 import (
        build_step11_semantic_overlay,
        step11_semantic_overlay_material,
    )

    active_plan = _expected_active_discourse_plan(context)
    overlay = build_step11_semantic_overlay(
        dict(context.projected_current_input),
        inventory_result=context.inventory_result,
        content_plan=context.content_plan,
        discourse_plan=active_plan,
    )
    snapshot = context.inventory_result.source_snapshot
    nuclei = tuple(snapshot.nuclei)
    nucleus_by_source = {str(row.source_id): row for row in nuclei}
    source_to_owner = {
        str(row.source_id): str(row.actual_source_id) for row in nuclei
    }
    owner_to_source = {
        str(row.actual_source_id): str(row.source_id) for row in nuclei
    }

    def canonical(value: Any) -> str:
        key = str(value)
        return key if key in nucleus_by_source else owner_to_source.get(key, key)

    obligations = tuple(context.inventory_result.ledger["obligations"])
    obligation_by_id = {
        str(row["obligation_id"]): row for row in obligations
    }
    node_by_id = {
        str(row["node_id"]): row for row in active_plan["nodes"]
    }
    discourse_nucleus_ids = tuple(
        canonical(nucleus_id)
        for group in active_plan["sentence_groups"]
        for node_id in group["node_ids"]
        for nucleus_id in obligation_by_id[
            str(node_by_id[str(node_id)]["obligation_id"])
        ].get("nucleus_ids", ())
    )
    authority_nucleus_ids = (
        *overlay.planning_frontier.active_nucleus_ids,
        *(
            nucleus_id
            for relation in overlay.relations
            for nucleus_id in (
                relation.from_nucleus_id,
                relation.to_nucleus_id,
            )
        ),
        *(
            nucleus_id
            for unknown in overlay.unknowns
            for nucleus_id in (
                *unknown.target_nucleus_ids,
                *unknown.context_nucleus_ids,
            )
        ),
        *(
            nucleus_id
            for binding in overlay.reception_antecedent_bindings
            for nucleus_id in (
                *binding.antecedent_nucleus_ids,
                *binding.supporting_nucleus_ids,
                *binding.source_target_nucleus_ids,
            )
        ),
    )
    source_order = {
        str(row.source_id): ordinal for ordinal, row in enumerate(nuclei)
    }
    ordered_source_ids = _ordered_unique_strings(
        (
            *discourse_nucleus_ids,
            *sorted(
                (canonical(value) for value in authority_nucleus_ids),
                key=lambda value: source_order.get(value, len(source_order)),
            ),
        )
    )
    if (
        not ordered_source_ids
        or any(value not in source_to_owner for value in ordered_source_ids)
    ):
        raise CurrentRcG8RunError(
            "CURRENT_RC_G8_DIRECT_SOURCE_CONTEXT_INVALID"
        )
    participating = set(
        str(value)
        for value in overlay.planning_frontier.participating_obligation_ids
    )

    def owner_obligations(nucleus_id: str) -> tuple[str, ...]:
        selected = tuple(
            str(row["obligation_id"])
            for row in obligations
            if str(row["obligation_id"]) in participating
            and nucleus_id in {canonical(value) for value in row["nucleus_ids"]}
        )
        fallback = tuple(
            str(row["obligation_id"])
            for row in obligations
            if nucleus_id in {canonical(value) for value in row["nucleus_ids"]}
        )
        result = selected or fallback
        if not result:
            raise CurrentRcG8RunError(
                "CURRENT_RC_G8_DIRECT_SOURCE_CONTEXT_INVALID"
            )
        return result

    extra_features = _expected_overlay_visible_features(overlay)
    spec_by_source: dict[str, Any] = {}
    for nucleus_id in ordered_source_ids:
        try:
            rows = build_step11_grounded_phrase_specs(
                snapshot,
                (),
                additional_owner_obligation_ids={
                    nucleus_id: owner_obligations(nucleus_id)
                },
                additional_visible_feature_values=(
                    {nucleus_id: extra_features[nucleus_id]}
                    if nucleus_id in extra_features
                    else None
                ),
            )
        except Step11GroundedLexicalizationError as exc:
            raise CurrentRcG8RunError(exc.code) from None
        if len(rows) != 1 or rows[0].owner_nucleus_ids != (nucleus_id,):
            raise CurrentRcG8RunError(
                "CURRENT_RC_G8_DIRECT_SOURCE_CONTEXT_INVALID"
            )
        spec_by_source[nucleus_id] = rows[0]

    nuclei_by_anchor: dict[str, list[str]] = defaultdict(list)
    for binding in overlay.nucleus_anchor_bindings:
        for anchor_id in binding.source_anchor_ids:
            nuclei_by_anchor[str(anchor_id)].append(str(binding.nucleus_id))
    anchor_fragments = tuple(
        _ExpectedAnchorFragment(
            source_slot=str(anchor.source_slot),
            source_start=int(anchor.start),
            source_end=int(anchor.end),
            source_anchor_id=str(anchor.anchor_id),
            text=str(anchor.text),
            source_nucleus_ids=tuple(
                sorted(nuclei_by_anchor.get(str(anchor.anchor_id), ()))
            ),
        )
        for anchor in overlay.anchors
        if str(anchor.role) == "nucleus"
    )
    selected_anchor = None
    selected_anchor_source_id: str | None = None
    for nucleus_id in ordered_source_ids:
        owner_fragments = tuple(
            row for row in anchor_fragments
            if nucleus_id in row.source_nucleus_ids
        )
        if not owner_fragments:
            continue
        try:
            selected_anchor = select_step11_visible_source_anchor_use(
                (spec_by_source[nucleus_id],),
                owner_fragments,
                preferred_owner_nucleus_ids=(nucleus_id,),
                require_input_specific_binding=True,
            )
        except Step11GroundedLexicalizationError as exc:
            if exc.code == "STEP11_INPUT_SPECIFIC_ANCHOR_UNRESOLVED":
                continue
            raise CurrentRcG8RunError(exc.code) from None
        selected_anchor_source_id = nucleus_id
        break

    companion_phrase: str | None = None
    if selected_anchor is None:
        evidence_alias_by_actual = {
            str(row.actual_source_id): str(row.alias_source_id)
            for row in snapshot.source_id_alias_bindings
            if str(row.source_kind) == "evidence"
        }
        label_candidates = sorted(
            overlay.label_anchors,
            key=lambda row: (
                0 if str(row.source_field) == "category" else 1,
                int(row.source_ordinal),
            ),
        )
        for label_anchor in label_candidates:
            evidence_alias = evidence_alias_by_actual.get(
                str(label_anchor.evidence_span_id)
            )
            matches = tuple(
                row for row in nuclei
                if evidence_alias is not None
                and evidence_alias in row.evidence_ids
                and str(label_anchor.source_field) in row.source_fields
            )
            if len(matches) != 1:
                continue
            nucleus_id = str(matches[0].source_id)
            features = (
                {nucleus_id: {"label_strength": str(label_anchor.strength)}}
                if label_anchor.strength is not None
                else None
            )
            try:
                rows = build_step11_grounded_phrase_specs(
                    snapshot,
                    (),
                    additional_owner_obligation_ids={
                        nucleus_id: owner_obligations(nucleus_id)
                    },
                    additional_visible_feature_values=features,
                )
                if len(rows) != 1:
                    continue
                fragment = _ExpectedAnchorFragment(
                    source_slot=str(label_anchor.source_slot),
                    source_start=0,
                    source_end=len(str(label_anchor.label)),
                    source_anchor_id=str(label_anchor.label_anchor_id),
                    text=str(label_anchor.label),
                    source_nucleus_ids=(nucleus_id,),
                )
                anchor_use = select_step11_visible_source_anchor_use(
                    rows,
                    (fragment,),
                    preferred_owner_nucleus_ids=(nucleus_id,),
                    require_input_specific_binding=True,
                )
                companion_phrase = render_step11_grounded_phrase(
                    rows[0], anchor_use
                )
            except Step11GroundedLexicalizationError as exc:
                if exc.code == "STEP11_INPUT_SPECIFIC_ANCHOR_UNRESOLVED":
                    continue
                raise CurrentRcG8RunError(exc.code) from None
            break
        if companion_phrase is None:
            raise CurrentRcG8RunError(
                "CURRENT_RC_G8_DIRECT_SOURCE_CONTEXT_INVALID"
            )

    plain_phrase_by_owner = {
        source_to_owner[source_id]: render_step11_grounded_phrase(spec)
        for source_id, spec in spec_by_source.items()
    }
    first_phrase_by_owner = dict(plain_phrase_by_owner)
    if selected_anchor is not None and selected_anchor_source_id is not None:
        owner_id = source_to_owner[selected_anchor_source_id]
        first_phrase_by_owner[owner_id] = render_step11_grounded_phrase(
            spec_by_source[selected_anchor_source_id], selected_anchor
        )

    owner_ids = tuple(source_to_owner[value] for value in ordered_source_ids)
    owners_by_phrase: dict[str, list[str]] = defaultdict(list)
    for owner_id in owner_ids:
        owners_by_phrase[plain_phrase_by_owner[owner_id]].append(owner_id)
    references: dict[str, str] = {}
    for phrase, rows in owners_by_phrase.items():
        if len(rows) == 1:
            references[rows[0]] = "その" + phrase
        elif len(rows) == 2:
            references[rows[0]] = "先に示した" + phrase
            references[rows[1]] = "後に示した" + phrase
        else:
            for ordinal, owner_id in enumerate(rows, start=1):
                references[owner_id] = str(ordinal) + "番目に示した" + phrase
    if len(references) != len(owner_ids) or len(set(references.values())) != len(
        references
    ):
        raise CurrentRcG8RunError(
            "CURRENT_RC_G8_DIRECT_SOURCE_CONTEXT_INVALID"
        )
    return _ExpectedVisibleAuthority(
        active_discourse_plan=active_plan,
        semantic_overlay=overlay,
        active_discourse_plan_sha256=artifact_sha256(active_plan),
        semantic_overlay_sha256=artifact_sha256(
            step11_semantic_overlay_material(overlay, include_id=False)
        ),
        source_to_owner=source_to_owner,
        owner_to_source=owner_to_source,
        ordered_owner_ids=owner_ids,
        plain_phrase_by_owner=plain_phrase_by_owner,
        first_phrase_by_owner=first_phrase_by_owner,
        phrase_id_by_owner={
            source_to_owner[source_id]: str(spec.grounded_phrase_id)
            for source_id, spec in spec_by_source.items()
        },
        feature_sha256_by_owner={
            source_to_owner[source_id]: str(
                spec.visible_feature_fingerprint_sha256
            )
            for source_id, spec in spec_by_source.items()
        },
        owner_reference_by_owner=references,
        specificity_companion_phrase=companion_phrase,
    )


def _expected_overlay_receptions(
    context: _DirectRecoveryContext,
    authority: _ExpectedVisibleAuthority,
) -> tuple[_ExpectedReception, ...]:
    snapshot = context.successor_snapshot.base_snapshot
    nuclei_by_owner = {
        str(row.actual_source_id): row for row in snapshot.nuclei
    }
    opportunities: dict[str, Any] = {}
    for row in snapshot.reception_opportunities:
        opportunities[str(row.source_id)] = row
        opportunities[str(row.actual_source_id)] = row
    result: list[_ExpectedReception] = []
    for ordinal, binding in enumerate(
        authority.semantic_overlay.reception_antecedent_bindings, start=1
    ):
        matches: list[Any] = []
        seen: set[str] = set()
        for value in binding.source_reception_opportunity_ids:
            row = opportunities.get(str(value))
            if row is None or str(row.source_id) in seen:
                continue
            matches.append(row)
            seen.add(str(row.source_id))
        if len(matches) != 1:
            raise CurrentRcG8RunError(
                "CURRENT_RC_G8_DIRECT_SOURCE_CONTEXT_INVALID"
            )
        opportunity = matches[0]
        antecedents = (
            tuple(binding.antecedent_nucleus_ids)
            or tuple(binding.source_target_nucleus_ids)
        )
        targets = _ordered_unique_strings(
            authority.source_to_owner.get(str(value), str(value))
            for value in antecedents
        )
        supports = _ordered_unique_strings(
            authority.source_to_owner.get(str(value), str(value))
            for value in binding.supporting_nucleus_ids
        )
        focus = _ordered_unique_strings((*targets, *supports))
        if (
            not targets
            or not focus
            or any(value not in nuclei_by_owner for value in focus)
        ):
            raise CurrentRcG8RunError(
                "CURRENT_RC_G8_DIRECT_SOURCE_CONTEXT_INVALID"
            )
        inventory_act = str(opportunity.reception_act)
        if inventory_act not in set(str(value) for value in binding.allowed_response_acts):
            raise CurrentRcG8RunError(
                "CURRENT_RC_G8_DIRECT_SOURCE_CONTEXT_INVALID"
            )
        concrete = str(binding.action_lifecycle) in {
            "reported_completed",
            "reported_ongoing",
        }
        if inventory_act == "honor_concrete_action" and not concrete:
            effective = "do_not_dismiss"
            basis = "nonactual_action_nonpromotion"
        else:
            effective = inventory_act
            basis = "source_reception_act_projection"
        result.append(
            _ExpectedReception(
                source_reception_opportunity_id=str(opportunity.source_id),
                source_scope=str(opportunity.family),
                source_focus_owner_ids=focus,
                source_target_owner_ids=targets,
                supporting_source_owner_ids=supports,
                visible_support_owner_ids=tuple(
                    value for value in supports if value not in set(targets)
                ),
                inventory_reception_act=inventory_act,
                effective_reception_act=effective,
                act_refinement_basis=basis,
                sentence_group_ordinal=ordinal,
            )
        )
    if not result:
        raise CurrentRcG8RunError(
            "CURRENT_RC_G8_DIRECT_SOURCE_CONTEXT_INVALID"
        )
    return tuple(result)


def _expected_alias_identities(
    context: _DirectRecoveryContext,
) -> Mapping[str, frozenset[str]]:
    peers: dict[str, set[str]] = defaultdict(set)
    for binding in context.successor_snapshot.base_snapshot.source_id_alias_bindings:
        if str(binding.source_kind) not in {"relation", "unknown_boundary"}:
            continue
        actual = str(binding.actual_source_id)
        alias = str(binding.alias_source_id)
        peers[actual].update((actual, alias))
        peers[alias].update((actual, alias))
    return {key: frozenset(values) for key, values in peers.items()}


def _identity_closure(
    values: Sequence[Any], aliases: Mapping[str, frozenset[str]]
) -> frozenset[str]:
    result: set[str] = set()
    for value in values:
        key = str(value)
        result.add(key)
        result.update(aliases.get(key, ()))
    return frozenset(result)


def _expected_active_atoms(
    context: _DirectRecoveryContext,
    base: _ExpectedRecovery,
    authority: _ExpectedVisibleAuthority,
) -> tuple[_ExpectedAtom, ...]:
    active_owners = set(authority.ordered_owner_ids)
    aliases = _expected_alias_identities(context)
    selected: list[_ExpectedAtom] = []
    selected_ids: set[str] = set()
    for atom in base.atoms:
        if (
            atom.semantic_family == "construction"
            and set(atom.source_owner_ids) <= active_owners
        ):
            selected.append(atom)
            selected_ids.add(atom.source_atom_id)
    for relation in authority.semantic_overlay.relations:
        if not relation.required and not relation.explicit:
            continue
        owners = (
            authority.source_to_owner[str(relation.from_nucleus_id)],
            authority.source_to_owner[str(relation.to_nucleus_id)],
        )
        matches = tuple(
            atom for atom in base.atoms
            if atom.semantic_family in {"relation", "semantic_link"}
            and atom.source_atom_id not in selected_ids
            and tuple(atom.source_owner_ids[:2]) == owners
        )
        if len(matches) != 1:
            raise CurrentRcG8RunError(
                "CURRENT_RC_G8_DIRECT_SOURCE_CONTEXT_INVALID"
            )
        selected.append(matches[0])
        selected_ids.add(matches[0].source_atom_id)
    for unknown in authority.semantic_overlay.unknowns:
        unknown_ids = _identity_closure(unknown.source_unknown_ids, aliases)
        owners = {
            authority.source_to_owner[str(value)]
            for value in (
                *unknown.target_nucleus_ids,
                *unknown.context_nucleus_ids,
            )
            if str(value) in authority.source_to_owner
        }
        matches = tuple(
            atom for atom in base.atoms
            if atom.semantic_family == "explicit_unknown"
            and atom.source_atom_id not in selected_ids
            and _identity_closure((atom.source_atom_id,), aliases) & unknown_ids
            and bool(set(atom.source_owner_ids) & owners)
        )
        if not matches:
            raise CurrentRcG8RunError(
                "CURRENT_RC_G8_DIRECT_SOURCE_CONTEXT_INVALID"
            )
        selected.extend(matches)
        selected_ids.update(row.source_atom_id for row in matches)
    return tuple(sorted(selected, key=lambda row: row.source_order))


def _expected_role_tokens(
    context: _DirectRecoveryContext,
    receptions: Sequence[_ExpectedReception],
) -> Mapping[str, tuple[str, ...]]:
    from emlis_ai_step11_rc0029_experiment_surface_catalog_v3 import (
        STEP11_RC0029_EXPERIMENT_SURFACE_CATALOG,
    )

    lexical = context.lexical_atom_specs
    rows: dict[str, list[str]] = defaultdict(list)
    catalog = STEP11_RC0029_EXPERIMENT_SURFACE_CATALOG[
        "owner_role_surface_tokens"
    ]
    owner_by_ordinal = {
        int(row.owner_ordinal): str(row.source_owner_id)
        for row in lexical.owner_bindings
    }
    for atom in lexical.construction_atoms:
        for ordinal in atom.target_owner_ordinals:
            rows[owner_by_ordinal[int(ordinal)]].append(
                str(atom.role_position_surface_token)
            )
    for atom in lexical.relation_endpoint_atoms:
        rows[str(atom.source_owner_id)].append(
            str(atom.relation_surface_token)
            + str(catalog["relation_" + str(atom.relation_endpoint_role)])
        )
    for atom in lexical.semantic_link_atoms:
        rows[str(atom.from_semantic_unit_id)].append(
            str(atom.semantic_link_surface_token)
            + str(catalog["semantic_link_from"])
        )
        rows[str(atom.to_semantic_unit_id)].append(
            str(atom.semantic_link_surface_token)
            + str(catalog["semantic_link_to"])
        )
    for atom in lexical.explicit_unknown_atoms:
        for _kind, owner_id, _ordinal in atom.affected_source_owners:
            rows[str(owner_id)].append(
                str(atom.unknown_surface_token)
                + str(catalog["explicit_unknown"])
            )
    for binding in receptions:
        for owner_id in binding.source_target_owner_ids:
            rows[owner_id].append(str(catalog["reception_target"]))
        for owner_id in binding.visible_support_owner_ids:
            rows[owner_id].append(str(catalog["reception_support"]))
        for owner_id in binding.source_focus_owner_ids:
            rows[owner_id].append(str(catalog["reception_antecedent"]))
    return {
        owner_id: _ordered_unique_strings(values)
        for owner_id, values in rows.items()
    }


def _expected_typed_payload_sha256(
    owner_registry: Sequence[str],
    atoms: Sequence[_ExpectedAtom],
    receptions: Sequence[_ExpectedReception],
) -> str:
    from emlis_ai_nls_v3_artifact_contract import artifact_sha256

    constructions: list[dict[str, Any]] = []
    relations: list[dict[str, Any]] = []
    links: list[dict[str, Any]] = []
    unknowns: list[dict[str, Any]] = []
    for atom in atoms:
        row = atom.forward_signature
        if atom.semantic_family == "construction":
            constructions.append(
                {
                    "ordinal": row[1],
                    "construction_instance_id": row[2],
                    "construction_code": row[3],
                    "catalog_atom_code": row[4],
                    "surface_token": row[5],
                    "construction_slot_ids": list(row[6]),
                    "role_atoms": [
                        {
                            "construction_slot_id": role[0],
                            "lexical_role_kind": role[1],
                            "construction_position": role[2],
                            "role_position_atom_code": role[3],
                            "role_position_surface_token": role[4],
                            "target_owner_ordinals": list(role[5]),
                            "participation_ids": list(role[6]),
                        }
                        for role in row[7]
                    ],
                }
            )
        elif atom.semantic_family == "relation":
            relations.append(
                {
                    "ordinal": row[1],
                    "experiment_relation_id": row[2],
                    "source_relation_id": row[3],
                    "source_relation_type": row[4],
                    "effective_relation_type": row[5],
                    "from_owner_ordinal": row[6],
                    "to_owner_ordinal": row[7],
                    "direction": row[8],
                    "authority_basis": row[9],
                    "source_retention": row[10],
                    "experiment_retention": row[11],
                    "refines_source_relation_id": row[12],
                }
            )
        elif atom.semantic_family == "semantic_link":
            links.append(
                {
                    "ordinal": row[1],
                    "source_semantic_link_id": row[2],
                    "relation_type": row[3],
                    "from_owner_ordinal": row[4],
                    "to_owner_ordinal": row[5],
                    "direction": row[6],
                    "required": row[7],
                }
            )
        elif atom.semantic_family == "explicit_unknown":
            unknowns.append(
                {
                    "ordinal": row[1],
                    "source_unknown_id": row[2],
                    "dimension": row[3],
                    "affected_owner_ordinals": list(row[4]),
                    "required": row[5],
                }
            )
    return artifact_sha256(
        {
            "owner_registry": list(owner_registry),
            "construction_atoms": constructions,
            "relation_atoms": relations,
            "semantic_link_atoms": links,
            "explicit_unknown_atoms": unknowns,
            "reception_bindings": [
                {
                    "source_reception_opportunity_id": (
                        row.source_reception_opportunity_id
                    ),
                    "source_scope": row.source_scope,
                    "source_focus_owner_ids": list(row.source_focus_owner_ids),
                    "source_target_owner_ids": list(
                        row.source_target_owner_ids
                    ),
                    "supporting_source_owner_ids": list(
                        row.supporting_source_owner_ids
                    ),
                    "visible_support_owner_ids": list(
                        row.visible_support_owner_ids
                    ),
                    "inventory_reception_act": row.inventory_reception_act,
                    "effective_reception_act": row.effective_reception_act,
                    "act_refinement_basis": row.act_refinement_basis,
                    "sentence_group_ordinal": row.sentence_group_ordinal,
                }
                for row in receptions
            ],
        }
    )


def _expected_unknown_dimension_key(value: str) -> str:
    mapping = {
        "cause": "cause",
        "future_outcome": "outcome",
        "omitted_referent": "referent",
        "unresolved_intention": "future",
        "decision_state": "decision_state",
        "post_decision_comparative_merit": (
            "post_decision_comparative_merit"
        ),
        "other_person": "other_person_awareness",
        "relation": "relation",
        "unspecified": "generic",
    }
    try:
        return mapping[value]
    except KeyError as exc:
        raise CurrentRcG8RunError(
            "CURRENT_RC_G8_DIRECT_SOURCE_CONTEXT_INVALID"
        ) from exc


def _expected_observation_owner_groups(
    context: _DirectRecoveryContext,
    authority: _ExpectedVisibleAuthority,
) -> tuple[tuple[str, ...], ...]:
    """Project discourse groups from typed obligations, never case identity."""

    obligations = {
        str(row["obligation_id"]): row
        for row in context.inventory_result.ledger["obligations"]
    }
    nodes = {
        str(row["node_id"]): row
        for row in authority.active_discourse_plan["nodes"]
    }
    primary_kinds = frozenset(
        {
            "grounded_nucleus_notice",
            "significance_or_shift",
            "intention_or_next_action",
        }
    )

    def source_id(value: Any) -> str:
        key = str(value)
        return (
            key
            if key in authority.source_to_owner
            else authority.owner_to_source.get(key, key)
        )

    active_owner_ids = set(authority.ordered_owner_ids)
    covered: set[str] = set()
    result: list[tuple[str, ...]] = []
    for group in authority.active_discourse_plan["sentence_groups"]:
        if str(group["section_role"]) != "observation":
            continue
        owner_ids = _ordered_unique_strings(
            authority.source_to_owner[nucleus_id]
            for node_id in group["node_ids"]
            for node in (nodes[str(node_id)],)
            for obligation in (obligations[str(node["obligation_id"])],)
            if str(obligation["kind"]) in primary_kinds
            for value in obligation.get("nucleus_ids", ())
            for nucleus_id in (source_id(value),)
            if nucleus_id in authority.source_to_owner
            and authority.source_to_owner[nucleus_id] in active_owner_ids
            and authority.source_to_owner[nucleus_id] not in covered
        )
        if owner_ids:
            result.append(owner_ids)
            covered.update(owner_ids)
    result.extend(
        (owner_id,)
        for owner_id in authority.ordered_owner_ids
        if owner_id not in covered
    )
    if (
        not result
        or set(value for row in result for value in row) != active_owner_ids
        or sum(len(row) for row in result) != len(active_owner_ids)
    ):
        raise CurrentRcG8RunError(
            "CURRENT_RC_G8_DIRECT_SOURCE_CONTEXT_INVALID"
        )
    return tuple(result)


def _expected_source_range_groups(
    context: _DirectRecoveryContext,
    expected: _ExpectedRecovery,
    authority: _ExpectedVisibleAuthority,
) -> tuple[
    tuple[str, tuple[_ExpectedRoot, ...], tuple[_ExpectedFragment, ...]], ...
]:
    """Group typed source ranges without constructing any visible wording."""

    roots_by_owner = {row.source_owner_id: row for row in expected.roots}
    discourse_owner_order = _ordered_unique_strings(
        owner_id
        for group in _expected_observation_owner_groups(context, authority)
        for owner_id in group
        if owner_id in roots_by_owner
    )
    source_owner_order = _ordered_unique_strings(
        (*discourse_owner_order, *authority.ordered_owner_ids)
    )
    owner_rank = {
        owner_id: ordinal for ordinal, owner_id in enumerate(source_owner_order)
    }
    nucleus_by_owner = {
        str(row.actual_source_id): row
        for row in context.successor_snapshot.base_snapshot.nuclei
    }
    label_owner_ids = {
        owner_id
        for owner_id in source_owner_order
        if str(nucleus_by_owner[owner_id].allowed_claim_scope)
        == "selected_label_only"
    }
    range_rows: dict[tuple[str, int, int, str], dict[str, Any]] = {}
    for owner_id in source_owner_order:
        root = roots_by_owner[owner_id]
        if not root.source_fragments:
            raise CurrentRcG8RunError(
                "CURRENT_RC_G8_DIRECT_SOURCE_CONTEXT_INVALID"
            )
        for fragment in root.source_fragments:
            key = (
                fragment.source_span_id,
                fragment.span_relative_start_index,
                fragment.span_relative_end_index,
                fragment.source_fragment_text_sha256,
            )
            row = range_rows.setdefault(
                key,
                {
                    "source_span_id": fragment.source_span_id,
                    "source_field": fragment.source_field,
                    "start": fragment.span_relative_start_index,
                    "end": fragment.span_relative_end_index,
                    "text_sha256": fragment.source_fragment_text_sha256,
                    "owners": [],
                    "roots": [],
                    "fragments": [],
                },
            )
            if (
                row["source_field"] != fragment.source_field
                or row["text_sha256"]
                != fragment.source_fragment_text_sha256
            ):
                raise CurrentRcG8RunError(
                    "CURRENT_RC_G8_DIRECT_SOURCE_CONTEXT_INVALID"
                )
            row["owners"].append(owner_id)
            row["roots"].append(root)
            row["fragments"].append(fragment)
    rows_by_span: dict[tuple[str, str], list[dict[str, Any]]] = defaultdict(
        list
    )
    for row in range_rows.values():
        rows_by_span[(row["source_span_id"], row["source_field"])].append(row)
    for rows in rows_by_span.values():
        ordered = sorted(rows, key=lambda row: (row["start"], row["end"]))
        if any(
            left["end"] > right["start"]
            for left, right in zip(ordered, ordered[1:])
        ):
            raise CurrentRcG8RunError(
                "CURRENT_RC_G8_DIRECT_SOURCE_CONTEXT_INVALID"
            )

    def rank(rows: Sequence[Mapping[str, Any]]) -> tuple[int, int]:
        return (
            min(
                owner_rank[owner_id]
                for row in rows
                for owner_id in row["owners"]
            ),
            min(int(row["start"]) for row in rows),
        )

    grouped_rows: list[tuple[str, tuple[Mapping[str, Any], ...]]] = []
    main_groups: list[tuple[Mapping[str, Any], ...]] = []
    for span_rows in rows_by_span.values():
        normal_rows = tuple(
            sorted(
                (
                    row
                    for row in span_rows
                    if not set(row["owners"]) <= label_owner_ids
                ),
                key=lambda row: (row["start"], row["end"]),
            )
        )
        if not normal_rows:
            continue
        decomposition_owned = all(
            "adapter:semantic_decomposition_v3"
            in {
                str(code)
                for owner_id in row["owners"]
                for code in nucleus_by_owner[owner_id].source_attribute_codes
            }
            for row in normal_rows
        )
        if decomposition_owned:
            main_groups.append(normal_rows)
        else:
            main_groups.extend((row,) for row in normal_rows)
    main_groups.sort(key=rank)
    grouped_rows.extend(("meaning", rows) for rows in main_groups)
    label_rows: dict[str, list[Mapping[str, Any]]] = defaultdict(list)
    for row in range_rows.values():
        if not set(row["owners"]) <= label_owner_ids:
            continue
        source_field = str(row["source_field"])
        if source_field in {"emotion_details", "emotions"}:
            label_rows["emotion"].append(row)
        elif source_field in {"category", "categories"}:
            label_rows["category"].append(row)
        else:
            raise CurrentRcG8RunError(
                "CURRENT_RC_G8_DIRECT_SOURCE_CONTEXT_INVALID"
            )
    for label_kind in ("emotion", "category"):
        rows = tuple(
            sorted(label_rows.get(label_kind, ()), key=lambda row: rank((row,)))
        )
        if rows:
            grouped_rows.append(("labelcompanion", rows))
    result: list[
        tuple[str, tuple[_ExpectedRoot, ...], tuple[_ExpectedFragment, ...]]
    ] = []
    for family, rows in grouped_rows:
        result.append(
            (
                family,
                tuple(
                    {
                        root.source_root_id: root
                        for row in rows
                        for root in row["roots"]
                    }.values()
                ),
                tuple(
                    fragment
                    for row in rows
                    for fragment in row["fragments"]
                ),
            )
        )
    return tuple(result)


def _expected_visible_moves(
    context: _DirectRecoveryContext,
    expected: _ExpectedRecovery,
    authority: _ExpectedVisibleAuthority,
) -> tuple[_ExpectedVisibleMove, ...]:
    from emlis_ai_nls_v3_artifact_contract import artifact_sha256

    roots_by_owner = {row.source_owner_id: row for row in expected.roots}
    atoms_by_id = {row.source_atom_id: row for row in expected.atoms}
    moves: list[_ExpectedVisibleMove] = []
    construction_by_owner: dict[str, list[str]] = defaultdict(list)
    for atom in expected.atoms:
        if atom.semantic_family != "construction":
            continue
        owner_id = next(
            (
                value for value in authority.ordered_owner_ids
                if value in atom.source_owner_ids
            ),
            None,
        )
        if owner_id is None:
            raise CurrentRcG8RunError(
                "CURRENT_RC_G8_DIRECT_SOURCE_CONTEXT_INVALID"
            )
        construction_by_owner[owner_id].append(atom.source_atom_id)
    rendered_owner_ids: set[str] = set()
    rendered_fragment_ids: set[str] = set()
    for unit_family, group_roots, fragments in _expected_source_range_groups(
        context, expected, authority
    ):
        owner_ids = _ordered_unique_strings(
            row.source_owner_id for row in group_roots
        )
        new_owner_ids = tuple(
            value for value in owner_ids if value not in rendered_owner_ids
        )
        atom_ids = _ordered_unique_strings(
            atom_id
            for owner_id in new_owner_ids
            for atom_id in construction_by_owner.get(owner_id, ())
        )
        obligation_ids = _ordered_unique_strings(
            obligation_id
            for row in group_roots
            if row.source_owner_id in new_owner_ids
            for obligation_id in row.source_obligation_ids
        )
        fragment_ids = tuple(row.source_fragment_id for row in fragments)
        if set(fragment_ids) & rendered_fragment_ids:
            raise CurrentRcG8RunError(
                "CURRENT_RC_G8_DIRECT_SOURCE_CONTEXT_INVALID"
            )
        moves.append(
            _ExpectedVisibleMove(
                section_role="observation",
                family="root_group",
                source_unit_id=(
                    "nls3s11rc0036"
                    + unit_family
                    + "_"
                    + artifact_sha256(
                        {
                            "source_root_ids": [
                                row.source_root_id for row in group_roots
                            ],
                            "source_fragment_ids": list(fragment_ids),
                        }
                    )[:16]
                ),
                source_atom_ids=atom_ids,
                source_owner_ids=owner_ids,
                source_obligation_ids=obligation_ids,
                source_fragment_ids=fragment_ids,
                dimensions=_aggregate_source_dimensions(
                    tuple(row.dimensions for row in group_roots)
                ),
                semantic_key="source_range_group",
            )
        )
        rendered_owner_ids.update(new_owner_ids)
        rendered_fragment_ids.update(fragment_ids)
    expected_fragment_ids = {
        fragment.source_fragment_id
        for root in expected.roots
        for fragment in root.source_fragments
    }
    if (
        rendered_owner_ids != set(authority.ordered_owner_ids)
        or rendered_fragment_ids != expected_fragment_ids
    ):
        raise CurrentRcG8RunError(
            "CURRENT_RC_G8_DIRECT_SOURCE_CONTEXT_INVALID"
        )
    active_source_ids = set(authority.owner_to_source.values()) & {
        authority.owner_to_source[value]
        for value in authority.ordered_owner_ids
    }
    for evaluation in authority.semantic_overlay.reported_self_evaluations:
        source_ids = _ordered_unique_strings(
            binding.nucleus_id
            for binding in authority.semantic_overlay.nucleus_anchor_bindings
            if evaluation.source_anchor_id in binding.source_anchor_ids
            and str(binding.nucleus_id) in active_source_ids
        )
        if len(source_ids) != 1:
            raise CurrentRcG8RunError(
                "CURRENT_RC_G8_DIRECT_SOURCE_CONTEXT_INVALID"
            )
        owner_id = authority.source_to_owner[source_ids[0]]
        root = roots_by_owner[owner_id]
        moves.append(
            _ExpectedVisibleMove(
                section_role="observation",
                family="self_denial",
                source_unit_id=str(evaluation.self_evaluation_id),
                source_atom_ids=(),
                source_owner_ids=(owner_id,),
                source_obligation_ids=(),
                source_fragment_ids=(),
                dimensions=root.dimensions,
                semantic_key=str(evaluation.evaluation_target),
            )
        )
    used_relation_ids: set[str] = set()
    for relation in authority.semantic_overlay.relations:
        if not relation.required and not relation.explicit:
            continue
        owners = (
            authority.source_to_owner[str(relation.from_nucleus_id)],
            authority.source_to_owner[str(relation.to_nucleus_id)],
        )
        matches = tuple(
            atom for atom in expected.atoms
            if atom.semantic_family in {"relation", "semantic_link"}
            and atom.source_atom_id not in used_relation_ids
            and tuple(atom.source_owner_ids[:2]) == owners
        )
        if len(matches) != 1:
            raise CurrentRcG8RunError(
                "CURRENT_RC_G8_DIRECT_SOURCE_CONTEXT_INVALID"
            )
        atom = matches[0]
        used_relation_ids.add(atom.source_atom_id)
        moves.append(
            _ExpectedVisibleMove(
                section_role="observation",
                family="relation",
                source_unit_id=atom.source_atom_id,
                source_atom_ids=(atom.source_atom_id,),
                source_owner_ids=owners,
                source_obligation_ids=(),
                source_fragment_ids=(),
                dimensions=atom.dimensions,
                semantic_key=str(relation.relation_type),
                direction=str(relation.relation_direction),
            )
        )
    aliases = _expected_alias_identities(context)
    used_unknown_ids: set[str] = set()
    for unknown in authority.semantic_overlay.unknowns:
        source_ids = _ordered_unique_strings(unknown.target_nucleus_ids)
        owner_ids = _ordered_unique_strings(
            authority.source_to_owner[str(value)]
            for value in source_ids
            if str(value) in authority.source_to_owner
        )
        source_unknown_ids = _identity_closure(
            unknown.source_unknown_ids, aliases
        )
        matches = tuple(
            atom for atom in expected.atoms
            if atom.semantic_family == "explicit_unknown"
            and atom.source_atom_id not in used_unknown_ids
            and _identity_closure((atom.source_atom_id,), aliases)
            & source_unknown_ids
            and bool(set(atom.source_owner_ids) & set(owner_ids))
        )
        if not owner_ids or not matches:
            raise CurrentRcG8RunError(
                "CURRENT_RC_G8_DIRECT_SOURCE_CONTEXT_INVALID"
            )
        atom_ids = tuple(row.source_atom_id for row in matches)
        used_unknown_ids.update(atom_ids)
        moves.append(
            _ExpectedVisibleMove(
                section_role="observation",
                family="unknown",
                source_unit_id=str(unknown.unknown_id),
                source_atom_ids=atom_ids,
                source_owner_ids=owner_ids,
                source_obligation_ids=(),
                source_fragment_ids=(),
                dimensions=("unknown", "unknown", "unknown", "unknown"),
                semantic_key=_expected_unknown_dimension_key(
                    str(unknown.unknown_type)
                ),
            )
        )
    assigned_ids = {
        atom_id for move in moves for atom_id in move.source_atom_ids
    }
    if assigned_ids != set(atoms_by_id):
        raise CurrentRcG8RunError(
            "CURRENT_RC_G8_DIRECT_SOURCE_CONTEXT_INVALID"
        )
    overlay_reception: dict[str, Any] = {}
    for binding in authority.semantic_overlay.reception_antecedent_bindings:
        for opportunity_id in binding.source_reception_opportunity_ids:
            key = str(opportunity_id)
            if key in overlay_reception:
                raise CurrentRcG8RunError(
                    "CURRENT_RC_G8_DIRECT_SOURCE_CONTEXT_INVALID"
                )
            overlay_reception[key] = binding
    unknown_owner_ids = {
        authority.source_to_owner[str(nucleus_id)]
        for unknown in authority.semantic_overlay.unknowns
        for nucleus_id in (
            *unknown.target_nucleus_ids,
            *unknown.context_nucleus_ids,
        )
        if str(nucleus_id) in authority.source_to_owner
    }
    for reception in expected.receptions:
        support_ids = tuple(
            value for value in reception.visible_support_owner_ids
            if value not in set(reception.source_target_owner_ids)
        )
        overlay_binding = overlay_reception.get(
            reception.source_reception_opportunity_id
        )
        if overlay_binding is None:
            matches = tuple(
                row
                for row in authority.semantic_overlay.reception_antecedent_bindings
                if reception.source_reception_opportunity_id
                in tuple(str(value) for value in row.source_reception_opportunity_ids)
            )
            if len(matches) != 1:
                raise CurrentRcG8RunError(
                    "CURRENT_RC_G8_DIRECT_SOURCE_CONTEXT_INVALID"
                )
            overlay_binding = matches[0]
        moves.append(
            _ExpectedVisibleMove(
                section_role="reception",
                family="reception",
                source_unit_id=reception.source_reception_opportunity_id,
                source_atom_ids=(),
                source_owner_ids=_ordered_unique_strings(
                    (*reception.source_target_owner_ids, *support_ids)
                ),
                source_obligation_ids=(),
                source_fragment_ids=(),
                dimensions=("unknown", "unknown", "unknown", "unknown"),
                semantic_key=reception.effective_reception_act,
                target_owner_ids=reception.source_target_owner_ids,
                support_owner_ids=support_ids,
                action_lifecycle=str(overlay_binding.action_lifecycle),
                open_unknown=bool(
                    set((*reception.source_target_owner_ids, *support_ids))
                    & unknown_owner_ids
                ),
            )
        )
    return tuple(moves)


def _authority_with_moves(
    authority: _ExpectedVisibleAuthority,
    moves: Sequence[_ExpectedVisibleMove],
) -> _ExpectedVisibleAuthority:
    return _ExpectedVisibleAuthority(
        active_discourse_plan=authority.active_discourse_plan,
        semantic_overlay=authority.semantic_overlay,
        active_discourse_plan_sha256=authority.active_discourse_plan_sha256,
        semantic_overlay_sha256=authority.semantic_overlay_sha256,
        source_to_owner=authority.source_to_owner,
        owner_to_source=authority.owner_to_source,
        ordered_owner_ids=authority.ordered_owner_ids,
        plain_phrase_by_owner=authority.plain_phrase_by_owner,
        first_phrase_by_owner=authority.first_phrase_by_owner,
        phrase_id_by_owner=authority.phrase_id_by_owner,
        feature_sha256_by_owner=authority.feature_sha256_by_owner,
        owner_reference_by_owner=authority.owner_reference_by_owner,
        specificity_companion_phrase=authority.specificity_companion_phrase,
        moves=tuple(moves),
    )


def _expected_active_roots(
    context: _DirectRecoveryContext,
    active_owner_ids: set[str],
) -> tuple[_ExpectedRoot, ...]:
    from emlis_ai_grounded_observation_semantic_restatement_v3 import (
        build_grounded_semantic_restatement_witness,
    )
    from emlis_ai_nls_v3_artifact_contract import artifact_sha256

    snapshot = context.successor_snapshot.base_snapshot
    witness = build_grounded_semantic_restatement_witness(
        context.grounded_plan, context.resolver
    )
    obligations = tuple(context.inventory_result.ledger["obligations"])
    grounded_by_owner = {
        str(row.nucleus_id): row for row in context.grounded_plan.nuclei
    }
    unit_by_owner = {
        str(row.unit_id): row for row in witness.semantic_units
    }

    def source_fragment(
        *,
        owner_id: str,
        nucleus_id: str,
        span_id: str,
        start: int,
        end: int,
        basis: str,
        expected_artifact_sha256: str | None = None,
    ) -> _ExpectedFragment:
        span = context.resolver.resolve(span_id)
        raw_text = str(span.raw_text)
        text = raw_text[start:end]
        if (
            not text
            or start < 0
            or end <= start
            or end > len(raw_text)
            or (
                expected_artifact_sha256 is not None
                and artifact_sha256({"source_fragment": text})
                != expected_artifact_sha256
            )
        ):
            raise CurrentRcG8RunError(
                "CURRENT_RC_G8_DIRECT_SOURCE_CONTEXT_INVALID"
            )
        text_sha256 = hashlib.sha256(text.encode("utf-8")).hexdigest()
        material = {
            "source_owner_id": owner_id,
            "source_nucleus_id": nucleus_id,
            "source_span_id": span_id,
            "source_field": str(span.source_field),
            "span_relative_start_index": start,
            "span_relative_end_index": end,
            "source_fragment_text_sha256": text_sha256,
            "binding_basis": basis,
        }
        return _ExpectedFragment(
            source_fragment_id=(
                "nls3s11rc0036fragment_" + artifact_sha256(material)[:16]
            ),
            source_owner_id=owner_id,
            source_nucleus_id=nucleus_id,
            source_span_id=span_id,
            source_field=str(span.source_field),
            span_relative_start_index=start,
            span_relative_end_index=end,
            source_fragment_text=text,
            source_fragment_text_sha256=text_sha256,
            binding_basis=basis,
        )

    roots: list[_ExpectedRoot] = []
    for nucleus in snapshot.nuclei:
        owner_id = str(nucleus.actual_source_id)
        if owner_id not in active_owner_ids:
            continue
        nucleus_id = str(nucleus.source_id)
        aliases = {owner_id, nucleus_id}
        obligation_ids = tuple(
            str(row["obligation_id"])
            for row in obligations
            if type(row) is dict
            and row.get("required") is True
            and aliases & {str(value) for value in row.get("nucleus_ids", ())}
        )
        semantic_unit = unit_by_owner.get(owner_id)
        if semantic_unit is not None:
            fragments = (
                source_fragment(
                    owner_id=owner_id,
                    nucleus_id=nucleus_id,
                    span_id=str(semantic_unit.source_span_id),
                    start=int(semantic_unit.start_index),
                    end=int(semantic_unit.end_index),
                    basis="semantic_unit_exact_typed_range",
                    expected_artifact_sha256=str(
                        semantic_unit.source_fragment_sha256
                    ),
                ),
            )
        else:
            grounded = grounded_by_owner.get(owner_id)
            if grounded is None:
                raise CurrentRcG8RunError(
                    "CURRENT_RC_G8_DIRECT_SOURCE_CONTEXT_INVALID"
                )
            span_ids = _ordered_unique_strings(grounded.source_span_ids)
            if not span_ids:
                raise CurrentRcG8RunError(
                    "CURRENT_RC_G8_DIRECT_SOURCE_CONTEXT_INVALID"
                )
            fragments = tuple(
                source_fragment(
                    owner_id=owner_id,
                    nucleus_id=nucleus_id,
                    span_id=span_id,
                    start=0,
                    end=len(str(context.resolver.resolve(span_id).raw_text)),
                    basis="grounded_nucleus_exact_evidence_span",
                )
                for span_id in span_ids
            )
        dimensions = _source_dimensions(nucleus)
        material = {
            "source_owner_id": owner_id,
            "source_nucleus_id": nucleus_id,
            "source_obligation_ids": list(obligation_ids),
            "source_fragment_ids": [
                row.source_fragment_id for row in fragments
            ],
            "semantic_kind": str(nucleus.kind),
            "dimensions": list(dimensions),
            "required": bool(nucleus.required),
        }
        roots.append(
            _ExpectedRoot(
                source_root_id=(
                    "nls3s11rc0036root_" + artifact_sha256(material)[:16]
                ),
                source_owner_id=owner_id,
                source_nucleus_id=nucleus_id,
                source_obligation_ids=obligation_ids,
                source_fragments=fragments,
                semantic_kind=str(nucleus.kind),
                dimensions=dimensions,
                required=bool(nucleus.required),
            )
        )
    if {row.source_owner_id for row in roots} != active_owner_ids:
        raise CurrentRcG8RunError(
            "CURRENT_RC_G8_DIRECT_SOURCE_CONTEXT_INVALID"
        )
    return tuple(roots)


def _direct_expected_recovery(
    context: _DirectRecoveryContext,
) -> _ExpectedRecovery:
    """Return only the source-active envelope and visible authority."""

    base = _direct_expected_recovery_base(context)
    authority = _build_expected_projection_authority(context)
    receptions = _expected_overlay_receptions(context, authority)
    atoms = _expected_active_atoms(context, base, authority)
    active_owners = set(authority.ordered_owner_ids)
    roots = _expected_active_roots(context, active_owners)
    roles = _expected_role_tokens(context, receptions)
    owners: list[_ExpectedOwner] = []
    nucleus_by_owner = {
        str(row.actual_source_id): row
        for row in context.successor_snapshot.base_snapshot.nuclei
    }
    for owner in context.lexical_atom_specs.owner_bindings:
        owner_id = str(owner.source_owner_id)
        if owner_id not in active_owners:
            continue
        nucleus = nucleus_by_owner.get(owner_id)
        referent = authority.plain_phrase_by_owner.get(owner_id)
        if nucleus is None:
            raise CurrentRcG8RunError(
                "CURRENT_RC_G8_DIRECT_SOURCE_CONTEXT_INVALID"
            )
        if type(referent) is not str or not referent:
            raise CurrentRcG8RunError(
                "CURRENT_RC_G8_DIRECT_SOURCE_CONTEXT_INVALID"
            )
        owners.append(
            _ExpectedOwner(
                schema_version=_RECOVERY_OWNER_SCHEMA,
                source_owner_id=owner_id,
                source_owner_kind=str(owner.source_owner_kind),
                source_owner_ordinal=int(owner.owner_ordinal),
                source_nucleus_id=str(nucleus.source_id),
                semantic_kind=str(nucleus.kind),
                dimensions=_source_dimensions(nucleus),
                typed_role_tokens=roles.get(owner_id, ()),
                referent_text=referent,
                referent_text_sha256=hashlib.sha256(
                    referent.encode("utf-8")
                ).hexdigest(),
                referent_basis="grounded_semantic_feature_phrase",
            )
        )
    if {row.source_owner_id for row in owners} != active_owners:
        raise CurrentRcG8RunError(
            "CURRENT_RC_G8_DIRECT_SOURCE_CONTEXT_INVALID"
        )
    family_counts = Counter(row.semantic_family for row in atoms)
    expected = _ExpectedRecovery(
        owner_registry=base.owner_registry,
        owners=tuple(owners),
        roots=roots,
        atoms=atoms,
        receptions=receptions,
        source_counts=(
            ("owners", len(owners)),
            ("roots", len(roots)),
            ("constructions", family_counts.get("construction", 0)),
            ("relations", family_counts.get("relation", 0)),
            ("semantic_links", family_counts.get("semantic_link", 0)),
            ("explicit_unknowns", family_counts.get("explicit_unknown", 0)),
            ("receptions", len(receptions)),
        ),
        source_commitments=base.source_commitments,
        current_input_binding=base.current_input_binding,
        typed_payload_sha256=_expected_typed_payload_sha256(
            base.owner_registry, atoms, receptions
        ),
        candidate_boundary_sha256=base.candidate_boundary_sha256,
        catalog=base.catalog,
        grammar=base.grammar,
    )
    authority = _authority_with_moves(
        authority, _expected_visible_moves(context, expected, authority)
    )
    return _ExpectedRecovery(
        owner_registry=expected.owner_registry,
        owners=expected.owners,
        roots=expected.roots,
        atoms=expected.atoms,
        receptions=expected.receptions,
        source_counts=expected.source_counts,
        source_commitments=expected.source_commitments,
        current_input_binding=expected.current_input_binding,
        typed_payload_sha256=expected.typed_payload_sha256,
        candidate_boundary_sha256=expected.candidate_boundary_sha256,
        catalog=expected.catalog,
        grammar=expected.grammar,
        visible_authority=authority,
    )


def _owner_term(
    value: str,
    owner_lexicon: Mapping[str, tuple[str, str, str, str]],
    catalog: Mapping[str, Any],
    grammar: Mapping[str, Any],
) -> tuple[str, tuple[str, ...]] | None:
    fragments = tuple(
        (str(code), str(fragment))
        for code, fragment in catalog[
            "construction_predicate_fragments"
        ].items()
    )
    matches: list[tuple[str, tuple[str, ...]]] = []
    for expression, owner in owner_lexicon.items():
        if value == expression:
            matches.append((owner[0], ()))
        for first_code, first_fragment in fragments:
            if value == expression + first_fragment:
                matches.append((owner[0], (first_code,)))
            for second_code, second_fragment in fragments:
                if value == expression + first_fragment + second_fragment:
                    matches.append((owner[0], (first_code, second_code)))
    unique = tuple(dict.fromkeys(matches))
    return unique[0] if len(unique) == 1 else None


def _owner_sequence(
    value: str,
    joiner: str,
    owner_lexicon: Mapping[str, tuple[str, str, str, str]],
    catalog: Mapping[str, Any],
    grammar: Mapping[str, Any],
) -> tuple[tuple[str, tuple[str, ...]], ...] | None:
    fragments = tuple(
        str(row)
        for row in catalog["construction_predicate_fragments"].values()
    )
    visible_terms = tuple(
        sorted(
            set(owner_lexicon)
            | {
                expression + first
                for expression in owner_lexicon
                for first in fragments
            }
            | {
                expression + first + second
                for expression in owner_lexicon
                for first in fragments
                for second in fragments
            },
            key=len,
            reverse=True,
        )
    )
    solutions: list[tuple[tuple[str, tuple[str, ...]], ...]] = []

    def walk(
        remaining: str,
        rows: tuple[tuple[str, tuple[str, ...]], ...],
    ) -> None:
        if not remaining:
            solutions.append(rows)
            return
        for visible in visible_terms:
            if remaining != visible and not remaining.startswith(visible + joiner):
                continue
            parsed = _owner_term(visible, owner_lexicon, catalog, grammar)
            if parsed is None:
                continue
            tail = "" if remaining == visible else remaining[len(visible + joiner) :]
            walk(tail, rows + (parsed,))

    walk(value, ())
    unique = tuple(dict.fromkeys(solutions))
    return unique[0] if len(unique) == 1 and unique[0] else None


def _template_captures(
    template: str,
    value: str,
) -> tuple[tuple[str, str], ...]:
    """Enumerate bounded literal-template captures before typed decoding."""

    parts = tuple(re.split(r"(\{source\}|\{target\})", template))
    if parts.count("{source}") != 1 or parts.count("{target}") != 1:
        return ()
    rows: list[tuple[str, str]] = []

    def walk(
        ordinal: int,
        offset: int,
        captures: tuple[tuple[str, str], ...],
    ) -> None:
        if ordinal == len(parts):
            if offset == len(value):
                material = dict(captures)
                rows.append((material["source"], material["target"]))
            return
        part = parts[ordinal]
        if part in {"{source}", "{target}"}:
            name = part[1:-1]
            for end in range(offset + 1, len(value) + 1):
                walk(ordinal + 1, end, captures + ((name, value[offset:end]),))
            return
        if value.startswith(part, offset):
            walk(ordinal + 1, offset + len(part), captures)

    walk(0, 0, ())
    return tuple(dict.fromkeys(rows))


def _template_owner_matches(
    template: str,
    value: str,
    owner_lexicon: Mapping[str, tuple[str, str, str, str]],
    catalog: Mapping[str, Any],
    grammar: Mapping[str, Any],
) -> tuple[
    tuple[
        tuple[str, tuple[str, ...]],
        tuple[str, tuple[str, ...]],
    ],
    ...,
]:
    decoded: list[
        tuple[
            tuple[str, tuple[str, ...]],
            tuple[str, tuple[str, ...]],
        ]
    ] = []
    for source_material, target_material in _template_captures(
        template, value
    ):
        source = _owner_term(
            source_material, owner_lexicon, catalog, grammar
        )
        target = _owner_term(
            target_material, owner_lexicon, catalog, grammar
        )
        if source is not None and target is not None:
            decoded.append((source, target))
    return tuple(dict.fromkeys(decoded))


def _strip_dimension_prefixes(
    value: str,
    grammar: Mapping[str, Any],
) -> tuple[str, tuple[tuple[str, str], ...]]:
    registries = (
        ("temporal", grammar["temporal_scope_cues"]),
        ("modality", grammar["modality_cues"]),
        ("polarity", grammar["polarity_cues"]),
        ("referent", grammar["referent_scope_cues"]),
    )
    tokens = tuple(
        sorted(
            (
                (str(token), family, str(code))
                for family, registry in registries
                for code, token in registry.items()
                if token
            ),
            key=lambda row: len(row[0]),
            reverse=True,
        )
    )
    remainder = value
    recovered: list[tuple[str, str]] = []
    for _bound in range(8):
        match = next(
            (row for row in tokens if remainder.startswith(row[0])), None
        )
        if match is None:
            break
        token, family, code = match
        remainder = remainder[len(token) :]
        recovered.append((family, code))
    return remainder, tuple(recovered)


def _plan_owned_regions(
    actual_body: bytes,
    catalog: Mapping[str, Any],
    grammar: Mapping[str, Any],
    *,
    observation_group_ordinals: Sequence[int],
) -> tuple[tuple[str, ...], tuple[str, ...]] | None:
    try:
        actual = actual_body.decode("utf-8", errors="strict")
    except (AttributeError, UnicodeDecodeError):
        return None
    separator = str(grammar["section_separator"])
    header = str(grammar["observation_header"])
    suffix = str(catalog["clause_morphology"]["sentence_suffix"])
    if (
        actual.count(separator) != 1
        or not actual.startswith(header)
        or not header.endswith("\n")
    ):
        return None
    actual_observation, actual_reception = actual.split(separator, 1)
    observation_material = actual_observation[len(header) :]
    actual_lines = observation_material.split("\n")
    if any(not line for line in actual_lines):
        return None
    expected_groups = tuple(sorted(set(observation_group_ordinals)))
    if expected_groups != tuple(range(1, len(actual_lines) + 1)):
        return None
    clusters: list[str] = []
    for group in expected_groups:
        actual_line = actual_lines[group - 1]
        if not actual_line.endswith(suffix):
            return None
        product = actual_line[: -len(suffix)]
        if not product:
            return None
        clusters.append(product)
    sentence_join = str(
        catalog["clause_morphology"]["grammatical_sentence_join"]
    )
    receptions: list[str] = []
    reception_lines = () if not actual_reception else actual_reception.split("\n")
    if any(not line for line in reception_lines):
        return None
    for line in reception_lines:
        if not line.endswith(suffix):
            return None
        receptions.extend(
            row for row in line[: -len(suffix)].split(sentence_join) if row
        )
    return tuple(clusters), tuple(receptions)


def _parse_observation(
    clusters: Sequence[str],
    owner_lexicon: Mapping[str, tuple[str, str, str, str]],
    catalog: Mapping[str, Any],
    grammar: Mapping[str, Any],
    *,
    strip_leading_dimensions: bool = True,
) -> dict[str, Any]:
    atoms: Counter[Any] = Counter()
    modifiers: Counter[Any] = Counter()
    unparsed = 0
    ambiguous = 0
    temporal_loci = 0
    separators = {
        str(grammar["clause_join"]),
        *(str(row) for row in grammar["atom_joiners"]),
        str(catalog["clause_morphology"]["within_sentence_clause_join"]),
        str(catalog["clause_morphology"]["grammatical_sentence_join"]),
    }
    split_pattern = "|".join(
        re.escape(row) for row in sorted(separators, key=len, reverse=True) if row
    )
    for cluster in clusters:
        pieces = tuple(row for row in re.split(split_pattern, cluster) if row)
        temporal_seen = False
        parsed_in_cluster = 0
        for raw_piece in pieces:
            piece, dimensions = (
                _strip_dimension_prefixes(raw_piece, grammar)
                if strip_leading_dimensions
                else (raw_piece, ())
            )
            temporal_seen = temporal_seen or any(
                row[0] == "temporal" for row in dimensions
            )
            matches: list[
                tuple[str, str, str, tuple[str, ...], tuple[Any, ...]]
            ] = []
            for family, registry in (
                ("relation", catalog["relation_predicate_fragments"]),
                ("semantic_link", catalog["semantic_link_predicate_fragments"]),
            ):
                for compound_key, template in registry.items():
                    semantic_key, direction = str(compound_key).rsplit(":", 1)
                    for source, target in _template_owner_matches(
                        str(template),
                        piece,
                        owner_lexicon,
                        catalog,
                        grammar,
                    ):
                        matches.append(
                            (
                                family,
                                semantic_key,
                                direction,
                                (source[0], target[0]),
                                (source, target),
                            )
                        )
            unknown_join = str(
                catalog["clause_morphology"]["unknown_owner_join"]
            )
            for semantic_key, fragment in catalog[
                "unknown_predicate_fragments"
            ].items():
                fragment = str(fragment)
                if not piece.endswith(fragment):
                    continue
                owners = _owner_sequence(
                    piece[: -len(fragment)],
                    unknown_join,
                    owner_lexicon,
                    catalog,
                    grammar,
                )
                if owners is not None:
                    matches.append(
                        (
                            "explicit_unknown",
                            str(semantic_key),
                            "",
                            tuple(row[0] for row in owners),
                            owners,
                        )
                    )
            standalone = str(
                catalog["clause_morphology"]["construction_standalone_predicate"]
            )
            for semantic_key, fragment in catalog[
                "construction_predicate_fragments"
            ].items():
                suffix = str(fragment) + standalone
                if not piece.endswith(suffix):
                    continue
                owner = _owner_term(
                    piece[: -len(suffix)], owner_lexicon, catalog, grammar
                )
                if owner is not None and not owner[1]:
                    matches.append(
                        (
                            "construction",
                            str(semantic_key),
                            "",
                            (owner[0],),
                            (owner,),
                        )
                    )
            unique = tuple(dict.fromkeys(matches))
            if len(unique) != 1:
                ambiguous += len(unique) > 1
                unparsed += len(unique) == 0
                continue
            family, semantic_key, direction, owners, owner_rows = unique[0]
            parsed_in_cluster += 1
            atoms[(family, semantic_key, direction, owners)] += 1
            for owner_id, construction_codes in owner_rows:
                for code in construction_codes:
                    atoms[("construction", code, "", (owner_id,))] += 1
                    modifiers[(code, owner_id)] += 1
        temporal_loci += temporal_seen and bool(parsed_in_cluster)
    return {
        "atoms": atoms,
        "modifiers": modifiers,
        "unparsed": unparsed,
        "ambiguous": ambiguous,
        "temporal_loci": temporal_loci,
    }


def _parse_reception(
    clauses: Sequence[str],
    owner_lexicon: Mapping[str, tuple[str, str, str, str]],
    catalog: Mapping[str, Any],
    grammar: Mapping[str, Any],
) -> tuple[Counter[Any], int]:
    actual: Counter[Any] = Counter()
    ambiguous = 0
    morphology = catalog["clause_morphology"]
    for clause in clauses:
        candidates: list[tuple[str, tuple[str, ...], tuple[str, ...]]] = []
        for act_code, act in catalog[
            "reception_act_predicate_fragments"
        ].items():
            suffix = str(morphology["reception_object_particle"]) + str(act)
            if not clause.endswith(suffix):
                continue
            owner_material = clause[: -len(suffix)]
            support_split = str(morphology["support_target_link"])
            variants: tuple[tuple[str, str], ...] = (("", owner_material),)
            if support_split in owner_material:
                variants += (tuple(owner_material.split(support_split, 1)),)
            for support_material, target_material in variants:
                targets = _owner_sequence(
                    target_material,
                    str(morphology["target_owner_join"]),
                    owner_lexicon,
                    catalog,
                    grammar,
                )
                supports = (
                    _owner_sequence(
                        support_material,
                        str(morphology["support_owner_join"]),
                        owner_lexicon,
                        catalog,
                        grammar,
                    )
                    if support_material
                    else ()
                )
                if (
                    targets is not None
                    and supports is not None
                    and all(not row[1] for row in (*supports, *targets))
                ):
                    candidates.append(
                        (
                            str(act_code),
                            tuple(row[0] for row in supports),
                            tuple(row[0] for row in targets),
                        )
                    )
        unique = tuple(dict.fromkeys(candidates))
        if len(unique) != 1:
            ambiguous += 1
            continue
        actual[unique[0]] += 1
    return actual, ambiguous


def _fragment_signature(value: Any) -> tuple[Any, ...]:
    return (
        str(value.source_fragment_id),
        str(value.source_owner_id),
        str(value.source_nucleus_id),
        str(value.source_span_id),
        str(value.source_field),
        int(value.span_relative_start_index),
        int(value.span_relative_end_index),
        str(value.source_fragment_text),
        str(value.source_fragment_text_sha256),
        str(value.binding_basis),
    )


def _root_signature(value: Any) -> tuple[Any, ...]:
    return (
        str(value.source_root_id),
        str(value.source_owner_id),
        str(value.source_nucleus_id),
        tuple(str(row) for row in value.source_obligation_ids),
        tuple(_fragment_signature(row) for row in value.source_fragments),
        str(value.semantic_kind),
        tuple(str(row) for row in value.dimensions),
        value.required,
    )


def _construction_role_signature(value: Any) -> tuple[Any, ...]:
    return (
        str(value.construction_slot_id),
        str(value.parent_nucleus_id),
        str(value.source_span_id),
        int(value.slot_start_index),
        int(value.slot_end_index),
        str(value.lexical_role_kind),
        str(value.construction_position),
        str(value.role_position_surface_token),
        tuple(str(row) for row in value.source_owner_ids),
        tuple(
            tuple(str(child) for child in row)
            for row in value.source_owner_dimensions
        ),
        tuple(str(row) for row in value.participation_ids),
    )


def _atom_signature(value: Any) -> tuple[Any, ...]:
    return (
        str(value.source_atom_id),
        str(value.semantic_family),
        str(value.semantic_key),
        tuple(str(row) for row in value.source_owner_ids),
        str(value.direction),
        tuple(str(row) for row in value.dimensions),
        tuple(str(row) for row in value.source_nucleus_owner_ids),
        tuple(str(row) for row in value.source_semantic_unit_owner_ids),
        tuple(str(row) for row in value.source_parent_nucleus_ids),
        tuple(str(row) for row in value.source_span_ids),
        tuple(str(row) for row in value.source_evidence_alias_ids),
        tuple(str(row) for row in value.source_marker_span_ids),
        str(value.source_grounding_kind),
        tuple(str(row) for row in value.source_relation_ids),
        str(value.authority_basis),
        str(value.source_retention),
        tuple(
            _construction_role_signature(row)
            for row in value.construction_roles
        ),
        int(value.source_order),
    )


def _reception_signature(value: Any) -> tuple[Any, ...]:
    return (
        str(value.source_reception_opportunity_id),
        str(value.source_scope),
        tuple(str(row) for row in value.source_focus_owner_ids),
        tuple(str(row) for row in value.source_target_owner_ids),
        tuple(str(row) for row in value.supporting_source_owner_ids),
        tuple(str(row) for row in value.visible_support_owner_ids),
        str(value.inventory_reception_act),
        str(value.effective_reception_act),
        str(value.act_refinement_basis),
        int(value.sentence_group_ordinal),
    )


def _owner_signature(value: Any) -> tuple[Any, ...]:
    return (
        str(value.schema_version),
        str(value.source_owner_id),
        str(value.source_owner_kind),
        int(value.source_owner_ordinal),
        str(value.source_nucleus_id),
        str(value.semantic_kind),
        tuple(str(row) for row in value.dimensions),
        tuple(str(row) for row in value.typed_role_tokens),
        str(value.referent_text),
        str(value.referent_text_sha256),
        str(value.referent_basis),
    )


def _current_input_binding_signature(value: Any) -> tuple[Any, ...]:
    return (
        str(value.thought_text),
        str(value.action_text),
        tuple(str(row) for row in value.emotions),
        tuple(str(row) for row in value.categories),
        str(value.projected_material_sha256),
        str(value.normalized_bundle_sha256),
        str(value.snapshot_original_input_bundle_sha256),
    )


def _forward_atom_signatures(candidate: Any) -> tuple[tuple[Any, ...], ...]:
    rows: list[tuple[Any, ...]] = []
    for atom in candidate.construction_atoms:
        rows.append(
            (
                "construction",
                int(atom.ordinal),
                str(atom.construction_instance_id),
                str(atom.construction_code),
                str(atom.catalog_atom_code),
                str(atom.surface_token),
                tuple(str(value) for value in atom.construction_slot_ids),
                tuple(
                    (
                        str(role.construction_slot_id),
                        str(role.lexical_role_kind),
                        str(role.construction_position),
                        str(role.role_position_atom_code),
                        str(role.role_position_surface_token),
                        tuple(
                            int(value) for value in role.target_owner_ordinals
                        ),
                        tuple(str(value) for value in role.participation_ids),
                    )
                    for role in atom.role_atoms
                ),
            )
        )
    for atom in candidate.relation_atoms:
        rows.append(
            (
                "relation",
                int(atom.ordinal),
                str(atom.experiment_relation_id),
                str(atom.source_relation_id),
                str(atom.source_relation_type),
                str(atom.effective_relation_type),
                int(atom.from_owner_ordinal),
                int(atom.to_owner_ordinal),
                str(atom.direction),
                str(atom.authority_basis),
                str(atom.source_retention),
                str(atom.experiment_retention),
                None
                if atom.refines_source_relation_id is None
                else str(atom.refines_source_relation_id),
            )
        )
    for atom in candidate.semantic_link_atoms:
        rows.append(
            (
                "semantic_link",
                int(atom.ordinal),
                str(atom.source_semantic_link_id),
                str(atom.relation_type),
                int(atom.from_owner_ordinal),
                int(atom.to_owner_ordinal),
                str(atom.direction),
                atom.required,
            )
        )
    for atom in candidate.explicit_unknown_atoms:
        rows.append(
            (
                "explicit_unknown",
                int(atom.ordinal),
                str(atom.source_unknown_id),
                str(atom.dimension),
                tuple(int(value) for value in atom.affected_owner_ordinals),
                atom.required,
            )
        )
    return tuple(rows)


def _plan_unit_signature(value: Any) -> tuple[Any, ...]:
    return (
        int(value.line_ordinal),
        str(value.section_role),
        str(value.source_unit_id),
        tuple(str(row) for row in value.source_atom_ids),
        tuple(str(row) for row in value.source_owner_ids),
        tuple(
            (str(owner_id), tuple(str(child) for child in dimensions))
            for owner_id, dimensions in value.source_owner_dimensions
        ),
        tuple(str(row) for row in value.source_obligation_ids),
        tuple(str(row) for row in value.source_fragment_ids),
        tuple(str(row) for row in value.dimensions),
        int(value.visible_clause_count),
    )


def _expected_plan_unit_signatures(
    expected: _ExpectedRecovery,
) -> tuple[tuple[Any, ...], ...]:
    authority = expected.visible_authority
    if type(authority) is not _ExpectedVisibleAuthority:
        raise CurrentRcG8RunError(
            "CURRENT_RC_G8_DIRECT_SOURCE_CONTEXT_INVALID"
        )
    dimensions_by_owner = {
        row.source_owner_id: row.dimensions for row in expected.owners
    }
    return tuple(
        (
            ordinal,
            move.section_role,
            move.source_unit_id,
            move.source_atom_ids,
            move.source_owner_ids,
            tuple(
                (owner_id, dimensions_by_owner[owner_id])
                for owner_id in move.source_owner_ids
            ),
            move.source_obligation_ids,
            move.source_fragment_ids,
            move.dimensions,
            1,
        )
        for ordinal, move in enumerate(authority.moves, start=1)
    )


def _visible_owner_mentions(
    line: str,
    authority: _ExpectedVisibleAuthority,
    expected: _ExpectedRecovery | None = None,
    phrase_occurrence: Counter[str] | None = None,
) -> tuple[tuple[str, int, int], ...]:
    """Decode grounded owner lexemes without comparing source fragments."""

    owners_by_phrase: dict[str, list[str]] = defaultdict(list)
    if expected is None:
        for owner_id in authority.ordered_owner_ids:
            phrase = authority.plain_phrase_by_owner.get(owner_id)
            if type(phrase) is not str or not phrase:
                return ()
            owners_by_phrase[phrase].append(owner_id)
    else:
        references = _expected_owner_reference_tokens(expected, authority)
        if set(references) != set(authority.ordered_owner_ids):
            return ()
        for owner_id, phrase in references.items():
            owners_by_phrase[phrase].append(owner_id)
    candidates: list[tuple[int, int, str, tuple[str, ...]]] = []
    for phrase, owner_ids in owners_by_phrase.items():
        start = line.find(phrase)
        while start >= 0:
            candidates.append(
                (start, start + len(phrase), phrase, tuple(owner_ids))
            )
            start = line.find(phrase, start + 1)
    selected: list[tuple[int, int, str, tuple[str, ...]]] = []
    for row in sorted(candidates, key=lambda value: (value[0], -value[1])):
        if any(row[0] < old[1] and old[0] < row[1] for old in selected):
            continue
        selected.append(row)
    selected.sort(key=lambda value: value[0])
    occurrence = phrase_occurrence if phrase_occurrence is not None else Counter()
    result: list[tuple[str, int, int]] = []
    collision_prefixes = {
        "先に触れた": 0,
        "続いて触れた": 1,
        "次に触れた": 1,
        "あとに触れた": 2,
    }
    for start, end, phrase, owner_ids in selected:
        if len(owner_ids) == 1:
            owner_id = owner_ids[0]
        else:
            prefix = line[max(0, start - 12) : start]
            rank = next(
                (
                    value
                    for token, value in collision_prefixes.items()
                    if prefix.endswith(token)
                ),
                occurrence[phrase],
            )
            if rank >= len(owner_ids):
                return ()
            owner_id = owner_ids[rank]
        occurrence[phrase] += 1
        result.append((owner_id, start, end))
    return tuple(result)


def _line_without_owner_lexemes(
    line: str, mentions: Sequence[tuple[str, int, int]]
) -> str:
    chars = list(line)
    for _owner_id, start, end in mentions:
        chars[start:end] = " " * (end - start)
    return "".join(chars)


def _expected_owner_reference_tokens(
    expected: _ExpectedRecovery,
    authority: _ExpectedVisibleAuthority,
) -> Mapping[str, str]:
    """Rebuild the public typed-anaphor grammar from source owner roles."""

    from emlis_ai_step11_surface_catalog_v3 import STEP11_SURFACE_CATALOG

    endpoint_roles: dict[str, set[str]] = defaultdict(set)
    for relation in authority.semantic_overlay.relations:
        from_owner = authority.source_to_owner.get(
            str(relation.from_nucleus_id)
        )
        to_owner = authority.source_to_owner.get(str(relation.to_nucleus_id))
        if from_owner is not None:
            endpoint_roles[from_owner].add(str(relation.from_endpoint_role))
        if to_owner is not None:
            endpoint_roles[to_owner].add(str(relation.to_endpoint_role))
    kind_by_owner = {
        row.source_owner_id: row.semantic_kind for row in expected.roots
    }
    source_slots_by_owner: dict[str, set[str]] = defaultdict(set)
    for binding in authority.semantic_overlay.nucleus_anchor_bindings:
        owner_id = authority.source_to_owner.get(str(binding.nucleus_id))
        if owner_id is not None:
            source_slots_by_owner[owner_id].update(
                str(value) for value in binding.source_slots
            )
    role_by_owner: dict[str, str] = {}
    for owner_id in authority.ordered_owner_ids:
        explicit = endpoint_roles.get(owner_id, set())
        if len(explicit) > 1:
            return {}
        if explicit:
            role = next(iter(explicit))
        elif (
            kind_by_owner.get(owner_id) == "action"
            or "memo_action" in source_slots_by_owner.get(owner_id, set())
        ):
            role = "action"
        elif (
            kind_by_owner.get(owner_id) == "reaction"
            or bool(
                {"emotion_details", "emotions"}
                & source_slots_by_owner.get(owner_id, set())
            )
        ):
            role = "affect"
        else:
            role = "proposition"
        if role not in {"action", "affect", "proposition"}:
            return {}
        role_by_owner[owner_id] = role
    lexical = STEP11_SURFACE_CATALOG["grounded_lexicalization"]
    local_anaphors = lexical["local_anaphors"]
    template = str(
        STEP11_SURFACE_CATALOG["endpoint_reference_grammar"][
            "reference_token_template"
        ]
    )
    owners_by_role: dict[str, list[str]] = defaultdict(list)
    for owner_id in authority.ordered_owner_ids:
        owners_by_role[role_by_owner[owner_id]].append(owner_id)
    result: dict[str, str] = {}
    for role, owner_ids in owners_by_role.items():
        local = str(local_anaphors[role])
        if len(owner_ids) == 1:
            result[owner_ids[0]] = local
            continue
        role_label = local.removeprefix("その")
        for ordinal, owner_id in enumerate(owner_ids, start=1):
            result[owner_id] = template.format(
                ordinal=ordinal, role_label=role_label
            )
    if len(set(result.values())) != len(result):
        return {}
    return result


def _relation_surface_forms() -> tuple[tuple[str, str, str, str], ...]:
    from emlis_ai_step11_surface_catalog_v3 import STEP11_SURFACE_CATALOG

    rows: list[tuple[str, str, str, str]] = []
    relation_atoms = STEP11_SURFACE_CATALOG["grounded_lexicalization"][
        "relation_atoms"
    ]
    for relation_type, directions in relation_atoms.items():
        for direction, form in directions.items():
            rows.append(
                (
                    str(relation_type),
                    str(direction),
                    str(form["left"]),
                    str(form["right"]),
                )
            )
    return tuple(rows)


def _visible_source_range_tokens(
    line: str,
    expected: _ExpectedRecovery,
    authority: _ExpectedVisibleAuthority,
    token_occurrence: Counter[str],
) -> tuple[tuple[str, ...], tuple[str, ...]]:
    """Decode exact source-range tokens, not a completed rendered line."""

    fragment_by_id = {
        fragment.source_fragment_id: fragment
        for root in expected.roots
        for fragment in root.source_fragments
    }
    ordered_fragment_ids = tuple(
        fragment_id
        for move in authority.moves
        if move.family == "root_group"
        for fragment_id in move.source_fragment_ids
    )
    range_rows: dict[tuple[str, int, int, str], list[_ExpectedFragment]] = {}
    range_order: list[tuple[str, int, int, str]] = []
    for fragment_id in ordered_fragment_ids:
        fragment = fragment_by_id.get(fragment_id)
        if fragment is None:
            return (), ()
        key = (
            fragment.source_span_id,
            fragment.span_relative_start_index,
            fragment.span_relative_end_index,
            fragment.source_fragment_text_sha256,
        )
        if key not in range_rows:
            range_rows[key] = []
            range_order.append(key)
        range_rows[key].append(fragment)
    rows_by_text: dict[str, list[tuple[_ExpectedFragment, ...]]] = defaultdict(
        list
    )
    for key in range_order:
        fragments = tuple(range_rows[key])
        text = fragments[0].source_fragment_text
        if not text or any(row.source_fragment_text != text for row in fragments):
            return (), ()
        rows_by_text[text].append(fragments)
    candidates: list[tuple[int, int, str]] = []
    for token in rows_by_text:
        start = line.find(token)
        while start >= 0:
            candidates.append((start, start + len(token), token))
            start = line.find(token, start + 1)
    selected: list[tuple[int, int, str]] = []
    for row in sorted(candidates, key=lambda value: (value[0], -value[1])):
        if any(row[0] < old[1] and old[0] < row[1] for old in selected):
            continue
        selected.append(row)
    selected.sort(key=lambda value: value[0])
    fragment_ids: list[str] = []
    owner_ids: list[str] = []
    for _start, _end, token in selected:
        ordinal = token_occurrence[token]
        rows = rows_by_text[token]
        if ordinal >= len(rows):
            return (), ()
        fragments = rows[ordinal]
        token_occurrence[token] += 1
        fragment_ids.extend(row.source_fragment_id for row in fragments)
        owner_ids.extend(row.source_owner_id for row in fragments)
    return tuple(fragment_ids), _ordered_unique_strings(owner_ids)


def _parse_visible_node(
    line: str,
    *,
    section_role: str,
    expected: _ExpectedRecovery,
    authority: _ExpectedVisibleAuthority,
    phrase_occurrence: Counter[str] | None = None,
    token_occurrence: Counter[str] | None = None,
) -> _ParsedVisibleNode | None:
    """Parse typed owner/move atoms; no completed sentence is rebuilt."""

    if section_role == "observation":
        fragment_ids, fragment_owner_ids = _visible_source_range_tokens(
            line,
            expected,
            authority,
            token_occurrence if token_occurrence is not None else Counter(),
        )
        if fragment_ids and fragment_owner_ids:
            return _ParsedVisibleNode(
                section_role="observation",
                family="root_group",
                visible_owner_ids=fragment_owner_ids,
                semantic_key="source_range_group",
                source_fragment_ids=fragment_ids,
            )
    mentions = _visible_owner_mentions(
        line,
        authority,
        expected=expected,
        phrase_occurrence=phrase_occurrence,
    )
    visible_owner_ids = _ordered_unique_strings(
        owner_id for owner_id, _start, _end in mentions
    )
    residual = _line_without_owner_lexemes(line, mentions)
    if section_role == "reception":
        if not visible_owner_ids:
            return None
        acts = expected.catalog["reception_act_predicate_fragments"]
        matching_acts = tuple(
            str(act)
            for act, fragment in acts.items()
            if type(fragment) is str and fragment and fragment in residual
        )
        if len(matching_acts) != 1:
            return None
        support_marker = str(
            expected.catalog["clause_morphology"]["support_target_link"]
        )
        support_boundary = line.find(support_marker)
        if support_marker and support_boundary >= 0:
            support_ids = _ordered_unique_strings(
                owner_id
                for owner_id, _start, end in mentions
                if end <= support_boundary
            )
            target_ids = _ordered_unique_strings(
                owner_id
                for owner_id, start, _end in mentions
                if start > support_boundary
            )
        else:
            support_ids = ()
            target_ids = visible_owner_ids
        if not target_ids or set(target_ids) & set(support_ids):
            return None
        return _ParsedVisibleNode(
            section_role="reception",
            family="reception",
            visible_owner_ids=(*support_ids, *target_ids),
            semantic_key=matching_acts[0],
            target_owner_ids=target_ids,
            support_owner_ids=support_ids,
            open_unknown="開いている部分" in residual,
            intended_action="これから行う" in residual,
        )
    if section_role != "observation":
        return None
    if visible_owner_ids and all(
        marker in residual
        for marker in ("あなた自身", "事実", "決めません")
    ):
        if len(visible_owner_ids) != 1:
            return None
        return _ParsedVisibleNode(
            section_role="observation",
            family="self_denial",
            visible_owner_ids=visible_owner_ids,
            semantic_key="self_denial_not_fact",
        )
    relation_matches: list[tuple[str, str]] = []
    for relation_type, direction, left, right in _relation_surface_forms():
        left_at = residual.find(left)
        right_at = residual.find(right, max(0, left_at + len(left)))
        if left_at >= 0 and right_at >= 0:
            relation_matches.append((relation_type, direction))
    relation_types = _ordered_unique_strings(
        value[0] for value in relation_matches
    )
    if relation_types and visible_owner_ids:
        if len(relation_types) != 1 or len(visible_owner_ids) != 2:
            return None
        return _ParsedVisibleNode(
            section_role="observation",
            family="relation",
            visible_owner_ids=visible_owner_ids,
            semantic_key=relation_types[0],
        )
    unknown_atoms = {
        "decision_state": ("選ぶ先",),
        "post_decision_comparative_merit": ("比べ方",),
        "other_person_awareness": ("相手からどう見えるか",),
        "cause": ("理由", "背景"),
        "referent": ("何を指すか", "指すもの"),
        "future": ("先の展開",),
        "outcome": ("結果",),
        "relation": ("間の関係", "二つの関係"),
        "generic": ("不明な部分", "その範囲"),
    }
    unknown_matches = tuple(
        key
        for key, tokens in unknown_atoms.items()
        if any(token in residual for token in tokens)
    )
    boundary_markers = (
        "まだ",
        "補いません",
        "決めつけません",
        "決めません",
        "開いて",
    )
    if (
        visible_owner_ids
        and unknown_matches
        and any(value in residual for value in boundary_markers)
    ):
        if len(unknown_matches) != 1:
            return None
        return _ParsedVisibleNode(
            section_role="observation",
            family="unknown",
            visible_owner_ids=visible_owner_ids,
            semantic_key=unknown_matches[0],
        )
    return None


def _independent_visible_decode(
    candidate: Any,
    expected: _ExpectedRecovery,
) -> dict[str, Any]:
    """Decode typed moves from visible clauses; never replay a full body."""

    result = {
        "layout": False,
        "roots": False,
        "atoms": False,
        "construction_roles": False,
        "receptions": False,
        "dimensions": False,
        "moves": (),
    }
    authority = expected.visible_authority
    if type(authority) is not _ExpectedVisibleAuthority:
        return result
    try:
        text = candidate.rendered_surface.utf8_bytes.decode(
            "utf-8", errors="strict"
        )
        header = str(expected.grammar["observation_header"])
        separator = str(expected.grammar["section_separator"])
        suffix = str(
            expected.catalog["clause_morphology"]["sentence_suffix"]
        )
        if not text.startswith(header) or text.count(separator) != 1:
            return result
        observation, reception = text[len(header) :].split(separator, 1)

        def section_lines(value: str) -> tuple[str, ...]:
            if not value:
                return ()
            rows = tuple(value.split("\n"))
            if any(
                not row or not suffix or not row.endswith(suffix)
                for row in rows
            ):
                raise ValueError("invalid visible line")
            return tuple(row[: -len(suffix)] for row in rows)

        observation_lines = section_lines(observation)
        reception_lines = section_lines(reception)
        visible_rows = (
            *(("observation", row) for row in observation_lines),
            *(("reception", row) for row in reception_lines),
        )
        if len(visible_rows) != len(authority.moves):
            return result
        decoded: list[_ParsedVisibleNode] = []
        phrase_occurrence: Counter[str] = Counter()
        token_occurrence: Counter[str] = Counter()
        for section_role, line in visible_rows:
            node = _parse_visible_node(
                line,
                section_role=section_role,
                expected=expected,
                authority=authority,
                phrase_occurrence=phrase_occurrence,
                token_occurrence=token_occurrence,
            )
            if node is None:
                return result
            decoded.append(node)
        decoded_moves = tuple(decoded)
        result["moves"] = decoded_moves
        root_owner_ids = tuple(
            owner_id
            for row in decoded_moves
            if row.family == "root_group"
            for owner_id in row.visible_owner_ids
        )
        visible_fragment_ids = tuple(
            fragment_id
            for row in decoded_moves
            if row.family == "root_group"
            for fragment_id in row.source_fragment_ids
        )
        expected_fragment_ids = tuple(
            fragment.source_fragment_id
            for root in expected.roots
            for fragment in root.source_fragments
        )
        result["roots"] = bool(
            set(root_owner_ids) == set(authority.ordered_owner_ids)
            and len(visible_fragment_ids) == len(expected_fragment_ids)
            and set(visible_fragment_ids) == set(expected_fragment_ids)
            and any(row.family == "root_group" for row in decoded_moves)
        )
        expected_family_counts = Counter(row.family for row in authority.moves)
        decoded_family_counts = Counter(row.family for row in decoded_moves)
        result["atoms"] = bool(
            result["roots"]
            and all(
                decoded_family_counts[family]
                == expected_family_counts[family]
                for family in ("relation", "unknown", "self_denial")
            )
        )
        root_owner_set = set(root_owner_ids)
        result["construction_roles"] = bool(
            result["roots"]
            and all(
                bool(set(row.source_owner_ids) & root_owner_set)
                for row in candidate.source_envelope.atom_bindings
                if row.semantic_family == "construction"
            )
        )
        result["receptions"] = bool(
            decoded_family_counts["reception"]
            == len(candidate.reception_bindings)
            and decoded_family_counts["reception"] > 0
        )
        result["dimensions"] = bool(
            all(
                owner_id in set(candidate.owner_registry)
                for row in decoded_moves
                for owner_id in row.visible_owner_ids
            )
        )
        result["layout"] = bool(
            result["roots"]
            and result["atoms"]
            and result["receptions"]
            and len(observation_lines)
            == sum(
                row.section_role == "observation" for row in authority.moves
            )
            and len(reception_lines)
            == sum(row.section_role == "reception" for row in authority.moves)
        )
    except Exception:
        return result
    return result


def _relation_display_owner_ids(
    owner_ids: tuple[str, ...], relation_type: str, direction: str
) -> tuple[str, ...]:
    from emlis_ai_step11_surface_catalog_v3 import STEP11_SURFACE_CATALOG

    if len(owner_ids) != 2:
        return ()
    try:
        form = STEP11_SURFACE_CATALOG["grounded_lexicalization"][
            "relation_atoms"
        ][relation_type][direction]
        endpoint = {"from": owner_ids[0], "to": owner_ids[1]}
        first, second = tuple(form["endpoint_order"])
        return (endpoint[str(first)], endpoint[str(second)])
    except (KeyError, TypeError, ValueError):
        return ()


def _visible_move_signature(value: _ExpectedVisibleMove) -> tuple[Any, ...]:
    if value.family == "root_group":
        visible_owner_ids = value.source_owner_ids
        semantic_key = "source_range_group"
    elif value.family == "self_denial":
        visible_owner_ids = value.source_owner_ids
        semantic_key = "self_denial_not_fact"
    elif value.family == "relation":
        visible_owner_ids = _relation_display_owner_ids(
            value.source_owner_ids, value.semantic_key, value.direction
        )
        semantic_key = value.semantic_key
    elif value.family == "unknown":
        visible_owner_ids = value.source_owner_ids
        semantic_key = value.semantic_key
    elif value.family == "reception":
        visible_owner_ids = (*value.support_owner_ids, *value.target_owner_ids)
        semantic_key = value.semantic_key
    else:
        return ()
    return (
        value.section_role,
        value.family,
        visible_owner_ids,
        semantic_key,
        value.target_owner_ids,
        value.support_owner_ids,
        value.open_unknown,
        value.action_lifecycle == "intended",
        value.source_fragment_ids if value.family == "root_group" else (),
    )


def _parsed_visible_signature(value: _ParsedVisibleNode) -> tuple[Any, ...]:
    return (
        value.section_role,
        value.family,
        value.visible_owner_ids,
        value.semantic_key,
        value.target_owner_ids,
        value.support_owner_ids,
        value.open_unknown,
        value.intended_action,
        value.source_fragment_ids,
    )


def _declared_plan_move_signatures(
    candidate: Any,
    expected: _ExpectedRecovery,
) -> tuple[tuple[Any, ...], ...]:
    """Normalize the candidate's public AST; never copy expected moves."""

    from emlis_ai_nls_v3_artifact_contract import artifact_sha256

    authority = expected.visible_authority
    if type(authority) is not _ExpectedVisibleAuthority:
        return ()
    try:
        envelope = candidate.source_envelope
        roots = tuple(envelope.root_bindings)
        atoms = tuple(envelope.atom_bindings)
        receptions = tuple(candidate.reception_bindings)
        root_by_fragment = {
            fragment.source_fragment_id: root
            for root in roots
            for fragment in root.source_fragments
        }
        atom_by_id = {row.source_atom_id: row for row in atoms}
        reception_by_id = {
            row.source_reception_opportunity_id: row for row in receptions
        }
        evaluation_by_id = {
            str(row.self_evaluation_id): row
            for row in authority.semantic_overlay.reported_self_evaluations
        }
        unknown_by_id = {
            str(row.unknown_id): row
            for row in authority.semantic_overlay.unknowns
        }
        overlay_reception: dict[str, Any] = {}
        for row in authority.semantic_overlay.reception_antecedent_bindings:
            for opportunity_id in row.source_reception_opportunity_ids:
                key = str(opportunity_id)
                if key in overlay_reception:
                    return ()
                overlay_reception[key] = row
        unknown_owner_ids = {
            authority.source_to_owner[str(nucleus_id)]
            for unknown in authority.semantic_overlay.unknowns
            for nucleus_id in (
                *unknown.target_nucleus_ids,
                *unknown.context_nucleus_ids,
            )
            if str(nucleus_id) in authority.source_to_owner
        }
        signatures: list[tuple[Any, ...]] = []
        declared_root_owner_ids: set[str] = set()
        construction_by_owner: dict[str, list[str]] = defaultdict(list)
        for atom in atoms:
            if atom.semantic_family != "construction":
                continue
            owner_id = next(
                (
                    value
                    for value in candidate.owner_registry
                    if value in atom.source_owner_ids
                ),
                None,
            )
            if owner_id is None:
                return ()
            construction_by_owner[str(owner_id)].append(atom.source_atom_id)
        for unit in candidate.realization_plan.units:
            owner_ids = tuple(str(value) for value in unit.source_owner_ids)
            atom_ids = tuple(str(value) for value in unit.source_atom_ids)
            fragment_ids = tuple(
                str(value) for value in unit.source_fragment_ids
            )
            if unit.section_role == "reception":
                if atom_ids or fragment_ids:
                    return ()
                reception = reception_by_id.get(str(unit.source_unit_id))
                overlay_binding = overlay_reception.get(
                    str(unit.source_unit_id)
                )
                if reception is None or overlay_binding is None:
                    return ()
                target_ids = tuple(reception.source_target_owner_ids)
                support_ids = tuple(
                    value
                    for value in reception.visible_support_owner_ids
                    if value not in set(target_ids)
                )
                if owner_ids != _ordered_unique_strings(
                    (*target_ids, *support_ids)
                ):
                    return ()
                signatures.append(
                    (
                        "reception",
                        "reception",
                        (*support_ids, *target_ids),
                        str(reception.effective_reception_act),
                        target_ids,
                        support_ids,
                        bool(set((*target_ids, *support_ids)) & unknown_owner_ids),
                        str(overlay_binding.action_lifecycle) == "intended",
                        (),
                    )
                )
                continue
            if unit.section_role != "observation":
                return ()
            if fragment_ids:
                try:
                    grouped_root_rows = tuple(
                        root_by_fragment[value] for value in fragment_ids
                    )
                    group_atoms = tuple(atom_by_id[value] for value in atom_ids)
                except KeyError:
                    return ()
                group_roots = tuple(
                    {
                        row.source_root_id: row for row in grouped_root_rows
                    }.values()
                )
                root_owner_ids = _ordered_unique_strings(
                    row.source_owner_id for row in group_roots
                )
                new_owner_ids = tuple(
                    value
                    for value in root_owner_ids
                    if value not in declared_root_owner_ids
                )
                construction_ids = _ordered_unique_strings(
                    atom_id
                    for owner_id in new_owner_ids
                    for atom_id in construction_by_owner.get(owner_id, ())
                )
                unit_id = str(unit.source_unit_id)
                family = next(
                    (
                        value
                        for value in ("meaning", "labelcompanion")
                        if unit_id.startswith("nls3s11rc0036" + value + "_")
                    ),
                    None,
                )
                if family is None:
                    return ()
                source_unit_id = (
                    "nls3s11rc0036"
                    + family
                    + "_"
                    + artifact_sha256(
                        {
                            "source_root_ids": [
                                row.source_root_id for row in group_roots
                            ],
                            "source_fragment_ids": list(fragment_ids),
                        }
                    )[:16]
                )
                if (
                    root_owner_ids != owner_ids
                    or any(
                        row.semantic_family != "construction"
                        for row in group_atoms
                    )
                    or atom_ids != construction_ids
                    or str(unit.source_unit_id) != source_unit_id
                ):
                    return ()
                signatures.append(
                    (
                        "observation",
                        "root_group",
                        owner_ids,
                        "source_range_group",
                        (),
                        (),
                        False,
                        False,
                        fragment_ids,
                    )
                )
                declared_root_owner_ids.update(new_owner_ids)
                continue
            evaluation = evaluation_by_id.get(str(unit.source_unit_id))
            if evaluation is not None:
                if atom_ids or len(owner_ids) != 1:
                    return ()
                signatures.append(
                    (
                        "observation",
                        "self_denial",
                        owner_ids,
                        "self_denial_not_fact",
                        (),
                        (),
                        False,
                        False,
                        (),
                    )
                )
                continue
            unknown = unknown_by_id.get(str(unit.source_unit_id))
            if unknown is not None:
                try:
                    group_atoms = tuple(atom_by_id[value] for value in atom_ids)
                    target_ids = _ordered_unique_strings(
                        authority.source_to_owner[str(value)]
                        for value in unknown.target_nucleus_ids
                    )
                except KeyError:
                    return ()
                if (
                    not atom_ids
                    or any(
                        row.semantic_family != "explicit_unknown"
                        for row in group_atoms
                    )
                    or owner_ids != target_ids
                ):
                    return ()
                signatures.append(
                    (
                        "observation",
                        "unknown",
                        owner_ids,
                        _expected_unknown_dimension_key(
                            str(unknown.unknown_type)
                        ),
                        (),
                        (),
                        False,
                        False,
                        (),
                    )
                )
                continue
            if len(atom_ids) != 1:
                return ()
            atom = atom_by_id.get(atom_ids[0])
            if (
                atom is None
                or atom.semantic_family not in {"relation", "semantic_link"}
                or str(unit.source_unit_id) != atom.source_atom_id
                or tuple(atom.source_owner_ids[:2]) != owner_ids
            ):
                return ()
            relation_matches = tuple(
                row
                for row in authority.semantic_overlay.relations
                if (row.required or row.explicit)
                and (
                    authority.source_to_owner[str(row.from_nucleus_id)],
                    authority.source_to_owner[str(row.to_nucleus_id)],
                )
                == owner_ids
            )
            if len(relation_matches) != 1:
                return ()
            relation = relation_matches[0]
            visible_ids = _relation_display_owner_ids(
                owner_ids,
                str(relation.relation_type),
                str(relation.relation_direction),
            )
            if not visible_ids:
                return ()
            signatures.append(
                (
                    "observation",
                    "relation",
                    visible_ids,
                    str(relation.relation_type),
                    (),
                    (),
                    False,
                    False,
                    (),
                )
            )
        return tuple(signatures)
    except Exception:
        return ()


def _recovery_source_envelope_exact(
    candidate: Any,
    *,
    context: _DirectRecoveryContext,
) -> bool:
    """Bind the recovery envelope to independently rebuilt upstream hashes."""

    try:
        from emlis_ai_step11_cycle001_product_recovery_v3 import (
            step11_cycle001_product_recovery_source_envelope_material,
        )
        from emlis_ai_nls_v3_artifact_contract import artifact_sha256

        expected = _direct_expected_recovery(context)
        envelope = candidate.source_envelope
        owner_bindings = tuple(envelope.owner_bindings)
        root_bindings = tuple(envelope.root_bindings)
        atom_bindings = tuple(envelope.atom_bindings)
        reception_bindings = tuple(envelope.reception_bindings)
        envelope_fields = set(getattr(type(envelope), "__dataclass_fields__", {}))
        forbidden = {
            "body",
            "current_input",
            "final_utf8_bytes",
            "raw_input",
            "raw_output",
            "rendered_surface",
            "utf8_bytes",
        }
        expected_commitments = dict(expected.source_commitments)
        return bool(
            envelope.schema_version == _RECOVERY_SOURCE_SCHEMA
            and envelope.candidate_version_id == _RECOVERY_CANDIDATE_VERSION
            and type(envelope.source_candidate_id) is str
            and bool(envelope.source_candidate_id)
            and type(envelope.source_envelope_sha256) is str
            and _SHA256_RE.fullmatch(envelope.source_envelope_sha256)
            is not None
            and envelope.source_envelope_sha256 != "0" * 64
            and envelope.source_envelope_sha256
            == artifact_sha256(
                step11_cycle001_product_recovery_source_envelope_material(
                    envelope, include_id=False
                )
            )
            and envelope.source_candidate_id
            == "nls3s11rc0036source_"
            + envelope.source_envelope_sha256[:16]
            and all(
                getattr(envelope, name, None) == value
                for name, value in expected_commitments.items()
            )
            and _current_input_binding_signature(
                envelope.current_input_binding
            )
            == expected.current_input_binding
            and envelope.duplicated_typed_payload_sha256
            == expected.typed_payload_sha256
            and tuple(envelope.source_counts) == expected.source_counts
            and tuple(_owner_signature(row) for row in owner_bindings)
            == tuple(_owner_signature(row) for row in expected.owners)
            and tuple(_root_signature(row) for row in root_bindings)
            == tuple(_root_signature(row) for row in expected.roots)
            and tuple(_atom_signature(row) for row in atom_bindings)
            == tuple(_atom_signature(row) for row in expected.atoms)
            and tuple(
                _reception_signature(row) for row in reception_bindings
            )
            == tuple(
                _reception_signature(row) for row in expected.receptions
            )
            and not (envelope_fields & forbidden)
            and owner_bindings
            and type(candidate.owner_registry) is tuple
            and tuple(candidate.owner_registry) == expected.owner_registry
            and envelope.old_gate_consulted is False
            and envelope.old_selector_consulted is False
            and envelope.base_acceptance_claimed is False
            and envelope.semantic_coverage_authorized is True
            and envelope.semantic_coverage_authority
            == "rc0036_source_envelope_visible_inverse_replay"
            and envelope.experimental_only is True
            and envelope.private_body_full is True
            and envelope.shareable is False
            and envelope.runtime_connected is False
        )
    except Exception:
        return False


def _recovery_inverse_checks(
    candidate: Any,
    *,
    context: _DirectRecoveryContext,
) -> dict[str, bool]:
    """Independently inverse-check final material against upstream sources."""

    result = {
        "final_utf8_valid": False,
        "inverse_layout_exact": False,
        "semantic_atoms_exact": False,
        "construction_modifiers_exact": False,
        "reception_bindings_exact": False,
        "dimension_loci_exact": False,
    }
    try:
        expected = _direct_expected_recovery(context)
        authority = expected.visible_authority
        if type(authority) is not _ExpectedVisibleAuthority:
            return result
        body = candidate.rendered_surface.utf8_bytes
        result["final_utf8_valid"] = bool(
            type(body) is bytes
            and bool(body)
            and body.decode("utf-8", errors="strict").encode(
                "utf-8", errors="strict"
            )
            == body
            and hashlib.sha256(body).hexdigest()
            == candidate.rendered_surface.sha256
            and candidate.final_utf8_bytes == body
            and candidate.rendered_surface.schema_version
            == _RECOVERY_RENDERED_SCHEMA
            and candidate.rendered_surface.source_envelope_sha256
            == candidate.source_envelope.source_envelope_sha256
            and candidate.rendered_surface.source_realization_plan_id
            == candidate.realization_plan.realization_plan_id
        )
        envelope = candidate.source_envelope
        atom_bindings = tuple(envelope.atom_bindings)
        expected_atom_signatures = tuple(
            _atom_signature(row) for row in expected.atoms
        )
        actual_atom_signatures = tuple(
            _atom_signature(row) for row in atom_bindings
        )
        expected_forward = tuple(
            row.forward_signature for row in expected.atoms
        )
        actual_forward = _forward_atom_signatures(candidate)
        decoded = _independent_visible_decode(candidate, expected)
        expected_move_signatures = tuple(
            _visible_move_signature(row) for row in authority.moves
        )
        declared_move_signatures = _declared_plan_move_signatures(
            candidate, expected
        )
        decoded_move_signatures = tuple(
            _parsed_visible_signature(row) for row in decoded["moves"]
        )
        three_way_moves_exact = bool(
            expected_move_signatures
            and expected_move_signatures == declared_move_signatures
            and expected_move_signatures == decoded_move_signatures
        )
        result["semantic_atoms_exact"] = bool(
            actual_atom_signatures == expected_atom_signatures
            and actual_forward == expected_forward
            and decoded["atoms"]
            and three_way_moves_exact
        )
        result["construction_modifiers_exact"] = bool(
            tuple(
                tuple(
                    _construction_role_signature(role)
                    for role in row.construction_roles
                )
                for row in atom_bindings
                if row.semantic_family == "construction"
            )
            == tuple(
                tuple(
                    _construction_role_signature(role)
                    for role in row.construction_roles
                )
                for row in expected.atoms
                if row.semantic_family == "construction"
            )
            and decoded["construction_roles"]
            and three_way_moves_exact
        )
        result["reception_bindings_exact"] = bool(
            tuple(
                _reception_signature(row)
                for row in candidate.reception_bindings
            )
            == tuple(
                _reception_signature(row) for row in expected.receptions
            )
            and tuple(
                _reception_signature(row)
                for row in envelope.reception_bindings
            )
            == tuple(
                _reception_signature(row) for row in expected.receptions
            )
            and decoded["receptions"]
            and three_way_moves_exact
        )
        expected_plan_units = _expected_plan_unit_signatures(expected)
        actual_plan_units = tuple(
            _plan_unit_signature(row) for row in candidate.realization_plan.units
        )
        expected_dimension_rows = tuple(row[8] for row in expected_plan_units)
        actual_dimension_rows = tuple(row[8] for row in actual_plan_units)
        result["dimension_loci_exact"] = bool(
            actual_dimension_rows == expected_dimension_rows
            and actual_plan_units == expected_plan_units
            and decoded["dimensions"]
            and three_way_moves_exact
        )
        observation_count = sum(
            row.section_role == "observation" for row in authority.moves
        )
        reception_count = sum(
            row.section_role == "reception" for row in authority.moves
        )
        result["inverse_layout_exact"] = bool(
            candidate.realization_plan.schema_version == _RECOVERY_PLAN_SCHEMA
            and candidate.realization_plan.candidate_version_id
            == _RECOVERY_CANDIDATE_VERSION
            and candidate.realization_plan.source_envelope_sha256
            == candidate.source_envelope.source_envelope_sha256
            and candidate.realization_plan.duplicated_typed_payload_sha256
            == expected.typed_payload_sha256
            and candidate.realization_plan.candidate_boundary_sha256
            == expected.candidate_boundary_sha256
            and actual_plan_units == expected_plan_units
            and decoded["layout"]
            and three_way_moves_exact
            and candidate.realization_plan.observation_line_count
            == observation_count
            and candidate.realization_plan.reception_line_count
            == reception_count
            and candidate.realization_plan.maximum_visible_clauses_per_line
            == 1
            and candidate.realization_plan.body_free is True
            and candidate.rendered_surface.observation_line_count
            == observation_count
            and candidate.rendered_surface.reception_line_count
            == reception_count
        )
    except Exception:
        pass
    return result


def _current_candidate(
    projected_input: Mapping[str, Any],
    *,
    source_closure: str,
) -> tuple[str, Any | None, dict[str, bool], str | None]:
    from emlis_ai_step11_cycle001_product_recovery_v3 import (
        build_step11_cycle001_product_recovery_candidate,
        validate_step11_cycle001_product_recovery_candidate,
    )
    from emlis_ai_nls_v3_artifact_contract import artifact_sha256

    checks = _empty_checks()
    checks["input_projected"] = True
    if type(source_closure) is not str or _SHA256_RE.fullmatch(source_closure) is None:
        return (
            "fail_close",
            None,
            checks,
            "CURRENT_RC_G8_SOURCE_CLOSURE_INVALID",
        )
    context = _build_direct_recovery_context(projected_input)
    checks["source_context_built"] = True
    source_arguments = {
        "plan": context.grounded_plan,
        "resolver": context.resolver,
        "successor_snapshot": context.successor_snapshot,
        "lexical_atom_specs": context.lexical_atom_specs,
        "inventory_result": context.inventory_result,
        "content_plan": context.content_plan,
        "discourse_plans": context.discourse_plans,
        "current_input": context.projected_current_input,
    }
    candidate = build_step11_cycle001_product_recovery_candidate(
        **source_arguments
    )
    checks["recovery_builder_called"] = True
    issues = validate_step11_cycle001_product_recovery_candidate(
        candidate,
        **source_arguments,
    )
    checks["recovery_validator_passed"] = not issues
    expected_candidate_id = "nls3s11rc0036cand_" + artifact_sha256(
        {
            "candidate_version_id": _RECOVERY_CANDIDATE_VERSION,
            "candidate_schema": _RECOVERY_CANDIDATE_SCHEMA,
            "source_envelope_sha256": (
                candidate.source_envelope.source_envelope_sha256
            ),
            "source_candidate_id": candidate.source_envelope.source_candidate_id,
            "final_bytes_sha256": candidate.rendered_surface.sha256,
            "realization_plan_id": (
                candidate.realization_plan.realization_plan_id
            ),
            "ast_id": candidate.realization_plan.ast_id,
        }
    )[:20]
    checks["recovery_identity_exact"] = bool(
        getattr(candidate, "candidate_version_id", None)
        == _RECOVERY_CANDIDATE_VERSION
        and getattr(candidate, "schema_version", None)
        == _RECOVERY_CANDIDATE_SCHEMA
        and getattr(candidate, "candidate_id", None) == expected_candidate_id
        and getattr(candidate, "old_gate_consulted", None) is False
        and getattr(candidate, "old_selector_consulted", None) is False
        and getattr(candidate, "base_acceptance_claimed", None) is False
        and getattr(candidate, "semantic_coverage_authorized", None) is True
        and getattr(candidate, "experimental_only", None) is True
        and getattr(candidate, "private_body_full", None) is True
        and getattr(candidate, "shareable", None) is False
        and getattr(candidate, "runtime_connected", None) is False
    )
    checks["source_envelope_exact"] = _recovery_source_envelope_exact(
        candidate,
        context=context,
    )
    checks.update(
        _recovery_inverse_checks(
            candidate,
            context=context,
        )
    )
    if not all(checks.values()):
        return "fail_close", candidate, checks, "CURRENT_RC_G8_INVERSE_REJECTED"
    return "selected", candidate, checks, None


def _case_row(
    sample: Mapping[str, Any],
    source_case_commitment: str,
    source_snapshot: Mapping[str, Any],
    batch_path: Path = _BATCH_PATH,
    manifest_path: Path = _MANIFEST_PATH,
) -> dict[str, Any]:
    source = _validated_source_snapshot(source_snapshot)
    _assert_source_unchanged(
        source,
        batch_path,
        manifest_path,
        code="CURRENT_RC_G8_WORKER_SOURCE_STALE",
    )
    from emlis_ai_step10_app_reachable_contract_v3 import (
        project_app_reachable_input,
    )

    case_id = sample.get("case_id")
    checks = _empty_checks()
    exception_captured = False
    if type(case_id) is not str or _CASE_RE.fullmatch(case_id) is None:
        raise CurrentRcG8RunError("CURRENT_RC_G8_SAMPLE_INVALID")
    try:
        projected = project_app_reachable_input(sample["input"])
        checks["input_projected"] = True
        with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
            disposition, candidate, checks, failure_code = _current_candidate(
                projected,
                source_closure=str(source["source_closure_sha256"]),
            )
    except Exception as exc:
        disposition = "fail_close"
        candidate = None
        failure_code = _closed_code(exc)
        exception_captured = True
    output = None
    candidate_id = None
    if candidate is not None:
        candidate_id = str(candidate.candidate_id)
        try:
            output = candidate.rendered_surface.utf8_bytes.decode(
                "utf-8", errors="strict"
            )
        except Exception:
            disposition = "fail_close"
            failure_code = "CURRENT_RC_G8_PRIVATE_OUTPUT_INVALID"
            checks["final_utf8_valid"] = False
            exception_captured = True
    _assert_source_unchanged(
        source,
        batch_path,
        manifest_path,
        code="CURRENT_RC_G8_WORKER_SOURCE_CHANGED",
    )
    return {
        "case_id": case_id,
        "source_case_commitment": source_case_commitment,
        "source_input": dict(sample["input"]),
        "disposition": disposition,
        "candidate_version_id": _RECOVERY_CANDIDATE_VERSION,
        "candidate_schema_version": _RECOVERY_CANDIDATE_SCHEMA,
        "current_candidate_id": candidate_id,
        "candidate_output_utf8": output,
        "machine_checks": checks,
        "failure_code": failure_code,
        "exception_captured": exception_captured,
    }


def _case_row_job(
    args: tuple[dict[str, Any], str, dict[str, Any], Path, Path],
) -> dict[str, Any]:
    return _case_row(*args)


def _run_cases(
    samples: Sequence[dict[str, Any]],
    commitment_by_case: Mapping[str, str],
    source_snapshot: Mapping[str, Any],
    *,
    workers: int,
    batch_path: Path = _BATCH_PATH,
    manifest_path: Path = _MANIFEST_PATH,
) -> list[dict[str, Any]]:
    source = _validated_source_snapshot(source_snapshot)
    jobs = tuple(
        (
            sample,
            commitment_by_case[str(sample["case_id"])],
            source,
            batch_path,
            manifest_path,
        )
        for sample in samples
    )
    if workers == 1:
        return [_case_row_job(job) for job in jobs]
    with ProcessPoolExecutor(
        max_workers=workers,
        mp_context=multiprocessing.get_context("spawn"),
    ) as executor:
        return list(executor.map(_case_row_job, jobs, chunksize=1))


def _assert_machine100(rows: Any) -> None:
    """Admit an evidence pair only for exact recovery output 100/100."""

    if type(rows) is not list or len(rows) != 100:
        raise CurrentRcG8RunError("CURRENT_RC_G8_MACHINE100_REQUIRED")
    for row in rows:
        if (
            type(row) is not dict
            or row.get("disposition") != "selected"
            or row.get("candidate_version_id")
            != _RECOVERY_CANDIDATE_VERSION
            or row.get("candidate_schema_version")
            != _RECOVERY_CANDIDATE_SCHEMA
            or type(row.get("current_candidate_id")) is not str
            or not row["current_candidate_id"]
            or type(row.get("candidate_output_utf8")) is not str
            or not row["candidate_output_utf8"]
            or row.get("failure_code") is not None
            or row.get("exception_captured") is not False
            or type(row.get("machine_checks")) is not dict
            or set(row["machine_checks"]) != set(_CHECK_KEYS)
            or not all(row["machine_checks"].values())
        ):
            raise CurrentRcG8RunError(
                "CURRENT_RC_G8_MACHINE100_REQUIRED"
            )


def _validate_private_rows(
    rows: Any,
    *,
    expected_case_sources: Sequence[tuple[str, str, bytes]],
) -> list[dict[str, Any]]:
    if type(rows) is not list or len(rows) != 100:
        raise CurrentRcG8RunError("CURRENT_RC_G8_EXACT100_REQUIRED")
    expected_ids = tuple(f"nls3s_b001_{index:04d}" for index in range(1, 101))
    if (
        type(expected_case_sources) not in {list, tuple}
        or len(expected_case_sources) != 100
    ):
        raise CurrentRcG8RunError(
            "CURRENT_RC_G8_CASE_SOURCE_BINDING_INVALID"
        )
    actual: list[dict[str, Any]] = []
    for expected_id, raw, source_binding in zip(
        expected_ids, rows, expected_case_sources, strict=True
    ):
        if (
            type(source_binding) is not tuple
            or len(source_binding) != 3
            or source_binding[0] != expected_id
            or type(source_binding[1]) is not str
            or _SHA256_RE.fullmatch(source_binding[1]) is None
            or type(source_binding[2]) is not bytes
            or not source_binding[2]
        ):
            raise CurrentRcG8RunError(
                "CURRENT_RC_G8_CASE_SOURCE_BINDING_INVALID"
            )
        if type(raw) is not dict or set(raw) != _PRIVATE_ROW_KEYS:
            raise CurrentRcG8RunError("CURRENT_RC_G8_PRIVATE_ROW_INVALID")
        row = dict(raw)
        checks = row.get("machine_checks")
        candidate_id = row.get("current_candidate_id")
        candidate_version = row.get("candidate_version_id")
        candidate_schema = row.get("candidate_schema_version")
        output = row.get("candidate_output_utf8")
        failure = row.get("failure_code")
        disposition = row.get("disposition")
        exception_captured = row.get("exception_captured")
        if (
            row.get("case_id") != expected_id
            or type(row.get("source_case_commitment")) is not str
            or _SHA256_RE.fullmatch(row["source_case_commitment"]) is None
            or type(row.get("source_input")) is not dict
            or disposition not in _ALLOWED_DISPOSITIONS
            or candidate_version != _RECOVERY_CANDIDATE_VERSION
            or candidate_schema != _RECOVERY_CANDIDATE_SCHEMA
            or type(exception_captured) is not bool
            or type(checks) is not dict
            # Canonical JSON sorts object keys, so validate the exact key set
            # rather than relying on the producer's insertion order.
            or set(checks) != set(_CHECK_KEYS)
            or any(type(value) is not bool for value in checks.values())
            or (
                candidate_id is not None
                and (type(candidate_id) is not str or not candidate_id)
            )
            or (output is not None and (type(output) is not str or not output))
            or (
                failure is not None
                and (
                    type(failure) is not str
                    or _CODE_RE.fullmatch(failure) is None
                )
            )
        ):
            raise CurrentRcG8RunError("CURRENT_RC_G8_PRIVATE_ROW_INVALID")
        if disposition == "selected":
            valid_state = (
                type(candidate_id) is str
                and type(output) is str
                and failure is None
                and exception_captured is False
                and all(checks.values())
            )
        elif disposition == "no_valid_candidate":
            valid_state = (
                candidate_id is None
                and output is None
                and failure is None
                and exception_captured is False
                and checks["input_projected"]
                and checks["source_context_built"]
                and not checks["recovery_builder_called"]
                and not any(
                    checks[key]
                    for key in _CHECK_KEYS
                    if key
                    not in {"input_projected", "source_context_built"}
                )
            )
        else:
            candidate_absent = (
                candidate_id is None
                and output is None
                and checks["recovery_builder_called"] is False
            )
            inverse_rejected = (
                type(candidate_id) is str
                and type(output) is str
                and failure == "CURRENT_RC_G8_INVERSE_REJECTED"
                and exception_captured is False
                and checks["input_projected"]
                and checks["source_context_built"]
                and checks["recovery_builder_called"]
            )
            output_rejected = (
                type(candidate_id) is str
                and output is None
                and failure == "CURRENT_RC_G8_PRIVATE_OUTPUT_INVALID"
                and exception_captured is True
                and checks["input_projected"]
                and checks["source_context_built"]
                and checks["recovery_builder_called"]
                and checks["final_utf8_valid"] is False
            )
            check_progression_exact = bool(
                (
                    checks["input_projected"]
                    or not any(
                        checks[key]
                        for key in _CHECK_KEYS
                        if key != "input_projected"
                    )
                )
                and (
                    checks["source_context_built"]
                    or not any(
                        checks[key]
                        for key in _CHECK_KEYS
                        if key
                        not in {"input_projected", "source_context_built"}
                    )
                )
                and (
                    checks["recovery_builder_called"]
                    or not any(
                        checks[key]
                        for key in _CHECK_KEYS
                        if key
                        not in {
                            "input_projected",
                            "source_context_built",
                            "recovery_builder_called",
                        }
                    )
                )
            )
            valid_state = bool(
                type(failure) is str
                and not all(checks.values())
                and check_progression_exact
                and (candidate_absent or inverse_rejected or output_rejected)
            )
        if not valid_state:
            raise CurrentRcG8RunError("CURRENT_RC_G8_PRIVATE_STATE_INVALID")
        if (
            not hmac.compare_digest(
                row["source_case_commitment"], source_binding[1]
            )
            or _canonical_json_bytes(row["source_input"])
            != source_binding[2]
        ):
            raise CurrentRcG8RunError(
                "CURRENT_RC_G8_CASE_SOURCE_BINDING_INVALID"
            )
        actual.append(row)
    return actual


def _public_failure_reason(row: Mapping[str, Any]) -> str:
    disposition = row["disposition"]
    if disposition == "selected":
        return "CURRENT_RC_G8_SELECTED"
    if disposition == "no_valid_candidate":
        return "CURRENT_RC_G8_NO_VALID_CANDIDATE"
    code = row.get("failure_code")
    return (
        str(code)
        if code in _PUBLIC_FAILURE_CODES
        else "CURRENT_RC_G8_CASE_REJECTED"
    )


def _case_commitment(
    key: bytes,
    run_id: str,
    source_closure: str,
    ordinal: int,
    row: Mapping[str, Any],
) -> str:
    if type(key) is not bytes or len(key) != 32:
        raise CurrentRcG8RunError("CURRENT_RC_G8_COMMITMENT_KEY_INVALID")
    material = (
        b"cocolon.current-rc.g8.case-result.v4\0"
        + run_id.encode("ascii", errors="strict")
        + b"\0"
        + source_closure.encode("ascii", errors="strict")
        + b"\0"
        + str(ordinal).encode("ascii", errors="strict")
        + b"\0"
        + _canonical_json_bytes(row)
    )
    return hmac.new(key, material, hashlib.sha256).hexdigest()


def _public_case_row(
    row: Mapping[str, Any],
    *,
    ordinal: int,
    case_hmac: str,
) -> dict[str, Any]:
    return {
        "ordinal": ordinal,
        "case_id": row["case_id"],
        "source_case_commitment": row["source_case_commitment"],
        "disposition": row["disposition"],
        "candidate_version_id": row["candidate_version_id"],
        "candidate_schema_version": row["candidate_schema_version"],
        "candidate_present": row["current_candidate_id"] is not None,
        "output_present": row["candidate_output_utf8"] is not None,
        "exception_present": row["exception_captured"],
        "failure_reason_code": _public_failure_reason(row),
        "machine_checks": dict(row["machine_checks"]),
        "case_hmac": case_hmac,
    }


def _run_commitment(
    key: bytes,
    *,
    run_id: str,
    source_closure: str,
    private_core_sha256: str,
    body_free_core_sha256: str,
) -> str:
    material = (
        b"cocolon.current-rc.g8.run-pair.v4\0"
        + run_id.encode("ascii", errors="strict")
        + b"\0"
        + source_closure.encode("ascii", errors="strict")
        + b"\0"
        + private_core_sha256.encode("ascii", errors="strict")
        + b"\0"
        + body_free_core_sha256.encode("ascii", errors="strict")
    )
    return hmac.new(key, material, hashlib.sha256).hexdigest()


def _artifact_source_snapshot(value: Mapping[str, Any]) -> dict[str, Any]:
    return _validated_source_snapshot(
        {
            "source_closure_sha256": value.get("source_closure_sha256"),
            "source_closure_file_count": value.get(
                "source_closure_file_count"
            ),
            "source_closure_files": value.get("source_closure_files"),
        }
    )


def _validate_pair(
    private: Any,
    body_free: Any,
    *,
    key: bytes,
    expected_source: Mapping[str, Any],
    expected_case_sources: Sequence[tuple[str, str, bytes]],
) -> None:
    private_keys = {
        "schema_version",
        "candidate_version_id",
        "candidate_schema_version",
        "run_id",
        "source_closure_sha256",
        "source_closure_file_count",
        "source_closure_files",
        "case_count",
        "cases",
        "pair_integrity",
    }
    body_free_keys = private_keys | {"disposition_counts"}
    body_free_keys.add("exception_count")
    if (
        type(private) is not dict
        or set(private) != private_keys
        or type(body_free) is not dict
        or set(body_free) != body_free_keys
        or private.get("schema_version") != _PRIVATE_SCHEMA
        or body_free.get("schema_version") != _BODY_FREE_SCHEMA
        or private.get("candidate_version_id") != _RECOVERY_CANDIDATE_VERSION
        or body_free.get("candidate_version_id")
        != _RECOVERY_CANDIDATE_VERSION
        or private.get("candidate_schema_version")
        != _RECOVERY_CANDIDATE_SCHEMA
        or body_free.get("candidate_schema_version")
        != _RECOVERY_CANDIDATE_SCHEMA
        or private.get("run_id") != body_free.get("run_id")
        or type(private.get("run_id")) is not str
        or _RUN_ID_RE.fullmatch(private["run_id"]) is None
        or private.get("case_count") != 100
        or body_free.get("case_count") != 100
    ):
        raise CurrentRcG8RunError("CURRENT_RC_G8_PAIR_SHAPE_INVALID")
    expected = _validated_source_snapshot(expected_source)
    private_source = _artifact_source_snapshot(private)
    body_free_source = _artifact_source_snapshot(body_free)
    if not (
        _canonical_json_bytes(private_source)
        == _canonical_json_bytes(body_free_source)
        == _canonical_json_bytes(expected)
    ):
        raise CurrentRcG8RunError("CURRENT_RC_G8_SOURCE_CLOSURE_INVALID")
    private_cases = private.get("cases")
    public_cases = body_free.get("cases")
    if (
        type(private_cases) is not list
        or len(private_cases) != 100
        or type(public_cases) is not list
        or len(public_cases) != 100
    ):
        raise CurrentRcG8RunError("CURRENT_RC_G8_EXACT100_REQUIRED")
    rows: list[dict[str, Any]] = []
    for ordinal, envelope in enumerate(private_cases, start=1):
        if (
            type(envelope) is not dict
            or set(envelope) != {"ordinal", "result", "case_hmac"}
            or envelope.get("ordinal") != ordinal
            or type(envelope.get("result")) is not dict
            or type(envelope.get("case_hmac")) is not str
            or _SHA256_RE.fullmatch(envelope["case_hmac"]) is None
        ):
            raise CurrentRcG8RunError("CURRENT_RC_G8_PRIVATE_ROW_INVALID")
        rows.append(dict(envelope["result"]))
    rows = _validate_private_rows(
        rows, expected_case_sources=expected_case_sources
    )
    source_closure = expected["source_closure_sha256"]
    for ordinal, (row, private_envelope, public_row) in enumerate(
        zip(rows, private_cases, public_cases, strict=True), start=1
    ):
        expected_hmac = _case_commitment(
            key,
            private["run_id"],
            source_closure,
            ordinal,
            row,
        )
        if not hmac.compare_digest(
            expected_hmac, private_envelope["case_hmac"]
        ):
            raise CurrentRcG8RunError(
                "CURRENT_RC_G8_HMAC_VERIFICATION_FAILED"
            )
        expected_public = _public_case_row(
            row, ordinal=ordinal, case_hmac=expected_hmac
        )
        if (
            type(public_row) is not dict
            or _canonical_json_bytes(public_row)
            != _canonical_json_bytes(expected_public)
        ):
            raise CurrentRcG8RunError(
                "CURRENT_RC_G8_BODY_FREE_PROJECTION_INVALID"
            )
    counts = Counter(row["disposition"] for row in rows)
    expected_counts = {
        disposition: counts.get(disposition, 0)
        for disposition in sorted(_ALLOWED_DISPOSITIONS)
    }
    if body_free.get("disposition_counts") != expected_counts:
        raise CurrentRcG8RunError("CURRENT_RC_G8_ACCOUNTING_INVALID")
    if body_free.get("exception_count") != sum(
        row["exception_captured"] for row in rows
    ):
        raise CurrentRcG8RunError("CURRENT_RC_G8_ACCOUNTING_INVALID")
    private_pair = private.get("pair_integrity")
    body_free_pair = body_free.get("pair_integrity")
    if (
        type(private_pair) is not dict
        or set(private_pair) != _PAIR_KEYS
        or type(body_free_pair) is not dict
        or set(body_free_pair) != _PAIR_KEYS
        or private_pair != body_free_pair
        or any(
            type(value) is not str or _SHA256_RE.fullmatch(value) is None
            for value in private_pair.values()
        )
    ):
        raise CurrentRcG8RunError("CURRENT_RC_G8_PAIR_INTEGRITY_INVALID")
    private_core = dict(private)
    body_free_core = dict(body_free)
    private_core.pop("pair_integrity")
    body_free_core.pop("pair_integrity")
    private_sha = hashlib.sha256(
        _canonical_json_bytes(private_core)
    ).hexdigest()
    body_free_sha = hashlib.sha256(
        _canonical_json_bytes(body_free_core)
    ).hexdigest()
    expected_run_hmac = _run_commitment(
        key,
        run_id=private["run_id"],
        source_closure=source_closure,
        private_core_sha256=private_sha,
        body_free_core_sha256=body_free_sha,
    )
    if (
        private_pair["body_free_core_sha256"] != body_free_sha
        or not hmac.compare_digest(
            private_pair["run_hmac"], expected_run_hmac
        )
    ):
        raise CurrentRcG8RunError(
            "CURRENT_RC_G8_HMAC_VERIFICATION_FAILED"
        )


def _decode_canonical_payload(payload: bytes) -> dict[str, Any]:
    try:
        if payload.startswith(b"\xef\xbb\xbf"):
            raise ValueError("bom")
        value = json.loads(payload.decode("utf-8", errors="strict"))
    except Exception as exc:
        raise CurrentRcG8RunError(
            "CURRENT_RC_G8_RESULT_NOT_CANONICAL"
        ) from exc
    if type(value) is not dict or _canonical_json_bytes(value) != payload:
        raise CurrentRcG8RunError("CURRENT_RC_G8_RESULT_NOT_CANONICAL")
    return value


def _result_payloads(
    rows: Sequence[dict[str, Any]],
    *,
    key: bytes,
    run_id: str,
    source_snapshot: Mapping[str, Any],
    expected_case_sources: Sequence[tuple[str, str, bytes]],
) -> tuple[bytes, bytes, dict[str, Any]]:
    if type(run_id) is not str or _RUN_ID_RE.fullmatch(run_id) is None:
        raise CurrentRcG8RunError("CURRENT_RC_G8_ARGUMENT_INVALID")
    source = _validated_source_snapshot(source_snapshot)
    private_rows = _validate_private_rows(
        list(rows), expected_case_sources=expected_case_sources
    )
    source_closure = source["source_closure_sha256"]
    private_cases: list[dict[str, Any]] = []
    body_free_cases: list[dict[str, Any]] = []
    for ordinal, row in enumerate(private_rows, start=1):
        commitment = _case_commitment(
            key, run_id, source_closure, ordinal, row
        )
        private_cases.append(
            {"ordinal": ordinal, "result": row, "case_hmac": commitment}
        )
        body_free_cases.append(
            _public_case_row(row, ordinal=ordinal, case_hmac=commitment)
        )
    disposition_counts = Counter(
        row["disposition"] for row in body_free_cases
    )
    common = {
        "candidate_version_id": _RECOVERY_CANDIDATE_VERSION,
        "candidate_schema_version": _RECOVERY_CANDIDATE_SCHEMA,
        "run_id": run_id,
        "source_closure_sha256": source_closure,
        "source_closure_file_count": source["source_closure_file_count"],
        "source_closure_files": source["source_closure_files"],
        "case_count": 100,
    }
    private_core = {
        "schema_version": _PRIVATE_SCHEMA,
        **common,
        "cases": private_cases,
    }
    body_free_core = {
        "schema_version": _BODY_FREE_SCHEMA,
        **common,
        "disposition_counts": {
            disposition: disposition_counts.get(disposition, 0)
            for disposition in sorted(_ALLOWED_DISPOSITIONS)
        },
        "exception_count": sum(
            row["exception_captured"] for row in private_rows
        ),
        "cases": body_free_cases,
    }
    private_core_sha256 = hashlib.sha256(
        _canonical_json_bytes(private_core)
    ).hexdigest()
    body_free_core_sha256 = hashlib.sha256(
        _canonical_json_bytes(body_free_core)
    ).hexdigest()
    pair = {
        "body_free_core_sha256": body_free_core_sha256,
        "run_hmac": _run_commitment(
            key,
            run_id=run_id,
            source_closure=source_closure,
            private_core_sha256=private_core_sha256,
            body_free_core_sha256=body_free_core_sha256,
        ),
    }
    private = {**private_core, "pair_integrity": pair}
    body_free = {**body_free_core, "pair_integrity": pair}
    _validate_pair(
        private,
        body_free,
        key=key,
        expected_source=source,
        expected_case_sources=expected_case_sources,
    )
    return (
        _canonical_json_bytes(private),
        _canonical_json_bytes(body_free),
        body_free,
    )


def _outside_repo(path: Path) -> bool:
    return path != REPO_ROOT and REPO_ROOT not in path.parents


def _read_commitment_key(path: Path) -> bytes:
    """Read one outside-repo caller key without importing batch/runtime code."""

    if (
        not path.is_absolute()
        or any(part in {"", ".", ".."} for part in path.parts[1:])
        or not hasattr(os, "O_DIRECTORY")
        or not hasattr(os, "O_NOFOLLOW")
        or not hasattr(os, "getuid")
    ):
        raise CurrentRcG8RunError("CURRENT_RC_G8_COMMITMENT_KEY_INVALID")
    lexical = Path(os.path.abspath(os.fspath(path)))
    try:
        resolved = path.resolve(strict=True)
    except Exception as exc:
        raise CurrentRcG8RunError(
            "CURRENT_RC_G8_COMMITMENT_KEY_INVALID"
        ) from exc
    if lexical != path or resolved != lexical or not _outside_repo(resolved):
        raise CurrentRcG8RunError("CURRENT_RC_G8_COMMITMENT_KEY_INVALID")
    directory_flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW
    file_flags = os.O_RDONLY | os.O_NOFOLLOW
    if hasattr(os, "O_CLOEXEC"):
        directory_flags |= os.O_CLOEXEC
        file_flags |= os.O_CLOEXEC
    directory_fd: int | None = None
    descriptor: int | None = None
    try:
        directory_fd = os.open(lexical.anchor, directory_flags)
        for component in lexical.parts[1:-1]:
            following = os.open(
                component,
                directory_flags,
                dir_fd=directory_fd,
            )
            os.close(directory_fd)
            directory_fd = following
        descriptor = os.open(
            lexical.name,
            file_flags,
            dir_fd=directory_fd,
        )
        status = os.fstat(descriptor)
        if (
            not stat_module.S_ISREG(status.st_mode)
            or stat_module.S_IMODE(status.st_mode) != 0o600
            or status.st_uid != os.getuid()
            or status.st_nlink != 1
        ):
            raise CurrentRcG8RunError(
                "CURRENT_RC_G8_COMMITMENT_KEY_INVALID"
            )
        chunks: list[bytes] = []
        remaining = 257
        while remaining:
            chunk = os.read(descriptor, remaining)
            if not chunk:
                break
            chunks.append(chunk)
            remaining -= len(chunk)
        raw = b"".join(chunks)
        if len(raw) == 257:
            raise CurrentRcG8RunError(
                "CURRENT_RC_G8_COMMITMENT_KEY_INVALID"
            )
    except CurrentRcG8RunError:
        raise
    except Exception as exc:
        raise CurrentRcG8RunError(
            "CURRENT_RC_G8_COMMITMENT_KEY_INVALID"
        ) from exc
    finally:
        if descriptor is not None:
            os.close(descriptor)
        if directory_fd is not None:
            os.close(directory_fd)
    if len(raw) == 32:
        return raw
    try:
        key = bytes.fromhex(raw.decode("ascii", errors="strict").strip())
    except (UnicodeError, ValueError) as exc:
        raise CurrentRcG8RunError(
            "CURRENT_RC_G8_COMMITMENT_KEY_INVALID"
        ) from exc
    if len(key) != 32:
        raise CurrentRcG8RunError("CURRENT_RC_G8_COMMITMENT_KEY_INVALID")
    return key


def _open_private_directory(
    path: Path,
    *,
    output_names: tuple[str, str],
) -> int:
    """Open one caller-owned, outside-repo, no-symlink 0700 directory."""

    if (
        not path.is_absolute()
        or any(part in {"", ".", ".."} for part in path.parts[1:])
        or not hasattr(os, "O_DIRECTORY")
        or not hasattr(os, "O_NOFOLLOW")
        or not hasattr(os, "getuid")
        or len(output_names) != 2
        or len(set(output_names)) != 2
        or any(
            type(name) is not str
            or not name
            or name != Path(name).name
            for name in output_names
        )
    ):
        raise CurrentRcG8RunError(
            "CURRENT_RC_G8_PRIVATE_DIRECTORY_PREFLIGHT_REJECTED"
        )
    lexical = Path(os.path.abspath(os.fspath(path)))
    try:
        resolved = path.resolve(strict=True)
    except Exception as exc:
        raise CurrentRcG8RunError(
            "CURRENT_RC_G8_PRIVATE_DIRECTORY_PREFLIGHT_REJECTED"
        ) from exc
    if lexical != path or resolved != lexical or not _outside_repo(resolved):
        raise CurrentRcG8RunError(
            "CURRENT_RC_G8_PRIVATE_DIRECTORY_PREFLIGHT_REJECTED"
        )
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
            raise CurrentRcG8RunError(
                "CURRENT_RC_G8_PRIVATE_DIRECTORY_PREFLIGHT_REJECTED"
            )
        for name in output_names:
            try:
                os.stat(name, dir_fd=descriptor, follow_symlinks=False)
            except FileNotFoundError:
                continue
            raise CurrentRcG8RunError(
                "CURRENT_RC_G8_PRIVATE_OUTPUT_ALREADY_EXISTS"
            )
        return descriptor
    except CurrentRcG8RunError:
        if descriptor is not None:
            os.close(descriptor)
        raise
    except Exception as exc:
        if descriptor is not None:
            os.close(descriptor)
        raise CurrentRcG8RunError(
            "CURRENT_RC_G8_PRIVATE_DIRECTORY_PREFLIGHT_REJECTED"
        ) from exc


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
            raise CurrentRcG8RunError(
                "CURRENT_RC_G8_PRIVATE_OUTPUT_PREFLIGHT_REJECTED"
            )
        return descriptor
    except CurrentRcG8RunError:
        raise
    except FileExistsError as exc:
        raise CurrentRcG8RunError(
            "CURRENT_RC_G8_PRIVATE_OUTPUT_ALREADY_EXISTS"
        ) from exc
    except Exception as exc:
        raise CurrentRcG8RunError(
            "CURRENT_RC_G8_PRIVATE_OUTPUT_PREFLIGHT_REJECTED"
        ) from exc


def _write_private_pair(
    directory_fd: int,
    private_payload: bytes,
    body_free_payload: bytes,
    *,
    private_name: str,
    body_free_name: str,
) -> None:
    """Exclusively create, sync, and retain exactly the two private files."""

    descriptors: dict[str, int] = {}
    created: list[str] = []
    try:
        for name in (private_name, body_free_name):
            descriptors[name] = _open_exclusive_private_file(
                directory_fd, name
            )
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
                    raise CurrentRcG8RunError(
                        "CURRENT_RC_G8_PRIVATE_OUTPUT_WRITE_REJECTED"
                    )
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


def _write_outputs(
    output_dir: Path,
    private_payload: bytes,
    body_free_payload: bytes,
    *,
    key: bytes,
    source_snapshot: Mapping[str, Any],
    expected_case_sources: Sequence[tuple[str, str, bytes]],
    batch_path: Path,
    manifest_path: Path,
) -> tuple[dict[str, Any], dict[str, Any]]:
    _assert_source_unchanged(
        source_snapshot,
        batch_path,
        manifest_path,
        code="CURRENT_RC_G8_SOURCE_CHANGED_BEFORE_WRITE",
    )
    private = _decode_canonical_payload(private_payload)
    body_free = _decode_canonical_payload(body_free_payload)
    _validate_pair(
        private,
        body_free,
        key=key,
        expected_source=source_snapshot,
        expected_case_sources=expected_case_sources,
    )
    directory_fd: int | None = None
    pair_written = False

    def discard_written_pair() -> None:
        if directory_fd is None or not pair_written:
            return
        for name in (_PRIVATE_FILENAME, _BODY_FREE_FILENAME):
            try:
                os.unlink(name, dir_fd=directory_fd)
            except FileNotFoundError:
                pass
            except OSError:
                pass
        try:
            os.fsync(directory_fd)
        except OSError:
            pass

    try:
        directory_fd = _open_private_directory(
            output_dir,
            output_names=(_PRIVATE_FILENAME, _BODY_FREE_FILENAME),
        )
        if os.listdir(directory_fd):
            raise CurrentRcG8RunError(
                "CURRENT_RC_G8_PRIVATE_DIRECTORY_NOT_FRESH"
            )
        _write_private_pair(
            directory_fd,
            private_payload,
            body_free_payload,
            private_name=_PRIVATE_FILENAME,
            body_free_name=_BODY_FREE_FILENAME,
        )
        pair_written = True
        reread: dict[str, bytes] = {}
        flags = os.O_RDONLY | os.O_NOFOLLOW
        if hasattr(os, "O_CLOEXEC"):
            flags |= os.O_CLOEXEC
        for name in (_PRIVATE_FILENAME, _BODY_FREE_FILENAME):
            descriptor: int | None = None
            try:
                descriptor = os.open(name, flags, dir_fd=directory_fd)
                status = os.fstat(descriptor)
                if (
                    not stat_module.S_ISREG(status.st_mode)
                    or stat_module.S_IMODE(status.st_mode) != 0o600
                    or status.st_uid != os.getuid()
                    or status.st_nlink != 1
                ):
                    raise CurrentRcG8RunError(
                        "CURRENT_RC_G8_PRIVATE_OUTPUT_POSTVERIFY_FAILED"
                    )
                chunks: list[bytes] = []
                while True:
                    chunk = os.read(descriptor, 1024 * 1024)
                    if not chunk:
                        break
                    chunks.append(chunk)
                reread[name] = b"".join(chunks)
            finally:
                if descriptor is not None:
                    os.close(descriptor)
        if (
            reread[_PRIVATE_FILENAME] != private_payload
            or reread[_BODY_FREE_FILENAME] != body_free_payload
        ):
            raise CurrentRcG8RunError(
                "CURRENT_RC_G8_PRIVATE_OUTPUT_POSTVERIFY_FAILED"
            )
        private = _decode_canonical_payload(reread[_PRIVATE_FILENAME])
        body_free = _decode_canonical_payload(reread[_BODY_FREE_FILENAME])
        _validate_pair(
            private,
            body_free,
            key=key,
            expected_source=source_snapshot,
            expected_case_sources=expected_case_sources,
        )
        _assert_source_unchanged(
            source_snapshot,
            batch_path,
            manifest_path,
            code="CURRENT_RC_G8_SOURCE_CHANGED_DURING_WRITE",
        )
        if set(os.listdir(directory_fd)) != {
            _PRIVATE_FILENAME,
            _BODY_FREE_FILENAME,
        }:
            raise CurrentRcG8RunError(
                "CURRENT_RC_G8_PRIVATE_DIRECTORY_POSTVERIFY_FAILED"
            )
        return private, body_free
    except CurrentRcG8RunError:
        discard_written_pair()
        raise
    except Exception as exc:
        discard_written_pair()
        raise CurrentRcG8RunError(
            "CURRENT_RC_G8_PRIVATE_OUTPUT_REJECTED"
        ) from exc
    finally:
        if directory_fd is not None:
            os.close(directory_fd)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Build one source-bound rc0036 recovery output for every case in "
            "the frozen exact-100 corpus and save a private body-full/HMAC "
            "body-free v4 pair only when machine100 is exact."
        )
    )
    parser.add_argument("--run-id", required=True)
    parser.add_argument(
        "--commitment-key-file",
        required=True,
        type=Path,
        help="Existing outside-repo 0600 file containing exactly 32 key bytes.",
    )
    parser.add_argument(
        "--output-dir",
        required=True,
        type=Path,
        help="Existing absolute outside-repo directory owned by the caller (0700).",
    )
    parser.add_argument(
        "--workers",
        type=int,
        default=min(8, max(1, os.cpu_count() or 1)),
        help="Parallel case workers (1-32; default: min(CPU count, 8)).",
    )
    parser.add_argument("--batch", type=Path, default=_BATCH_PATH)
    parser.add_argument("--manifest", type=Path, default=_MANIFEST_PATH)
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    if (
        type(args.run_id) is not str
        or _RUN_ID_RE.fullmatch(args.run_id) is None
        or type(args.workers) is not int
        or not 1 <= args.workers <= 32
    ):
        raise CurrentRcG8RunError("CURRENT_RC_G8_ARGUMENT_INVALID")
    batch_path = args.batch.resolve()
    manifest_path = args.manifest.resolve()
    (
        samples,
        _manifest,
        commitment_by_case,
        expected_case_sources,
        source_snapshot,
    ) = _bound_exact100_sources(batch_path, manifest_path)
    key = _read_commitment_key(args.commitment_key_file)
    rows = _run_cases(
        samples,
        commitment_by_case,
        source_snapshot,
        workers=args.workers,
        batch_path=batch_path,
        manifest_path=manifest_path,
    )
    _assert_machine100(rows)
    _assert_source_unchanged(
        source_snapshot,
        batch_path,
        manifest_path,
        code="CURRENT_RC_G8_SOURCE_CHANGED_DURING_EXECUTION",
    )
    private_payload, body_free_payload, _summary = _result_payloads(
        rows,
        key=key,
        run_id=args.run_id,
        source_snapshot=source_snapshot,
        expected_case_sources=expected_case_sources,
    )
    _write_outputs(
        args.output_dir,
        private_payload,
        body_free_payload,
        key=key,
        source_snapshot=source_snapshot,
        expected_case_sources=expected_case_sources,
        batch_path=batch_path,
        manifest_path=manifest_path,
    )
    return 0


if __name__ == "__main__":
    try:
        exit_code = main()
    except CurrentRcG8RunError as exc:
        print(exc.code, file=sys.stderr)
        raise SystemExit(2) from None
    except Exception:
        print("CURRENT_RC_G8_RUN_FAILED", file=sys.stderr)
        raise SystemExit(2) from None
    print("CURRENT_RC_G8_RESULTS_SAVED")
    raise SystemExit(exit_code)
