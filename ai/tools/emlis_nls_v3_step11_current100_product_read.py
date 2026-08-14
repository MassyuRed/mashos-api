#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from __future__ import annotations

"""Materialize the direct all-100 Product Read evidence pair.

The input is an already completed current-rc G8 v4 private/body-free pair and
one private human decision row for each frozen case.  This tool does not make
or revise review decisions.  It verifies the machine100 parent, normalizes the
fixed twelve-axis observations, and writes a private packet plus its body-free
ledger into one caller-owned fresh private directory.
"""

import argparse
from collections import Counter
import hashlib
import hmac
import json
import os
from pathlib import Path
import re
import stat as stat_module
import sys
from typing import Any, Mapping, Sequence


AI_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = AI_ROOT.parent.resolve()
TOOLS_ROOT = AI_ROOT / "tools"
if str(TOOLS_ROOT) not in sys.path:
    sys.path.insert(0, str(TOOLS_ROOT))

import emlis_nls_v3_step11_current_rc_g8_run as current_runner  # noqa: E402


_DECISIONS_SCHEMA = (
    "cocolon.emlis.nls_v3.step11.current100."
    "product_read_decisions.private.v1"
)
_PRIVATE_SCHEMA = (
    "cocolon.emlis.nls_v3.step11.current100."
    "product_read_packet.private.v1"
)
_BODY_FREE_SCHEMA = (
    "cocolon.emlis.nls_v3.step11.current100."
    "product_read_ledger.body_free.v1"
)
_PRIVATE_FILENAME = "current100_product_read_private.json"
_BODY_FREE_FILENAME = "current100_product_read_body_free.json"

# These are the frozen Step10 local Product Review axes.  Importing the old
# evidence owner here would also initialize its historical runtime authority,
# so the direct current100 boundary owns this small immutable projection.
PRODUCT_READ_AXES = (
    "PRIMARY_MEANING_RETAINED",
    "RELATION_DIRECTION_CORRECT",
    "NO_CAUSE_PERSONALITY_DIAGNOSIS_PROMOTION",
    "UNKNOWN_BOUNDARY_PRESERVED",
    "SELF_DENIAL_NOT_ADOPTED_OR_AMPLIFIED",
    "BOUND_EMLIS_RECEPTION",
    "SECTION_SEMANTIC_DISTINCTNESS",
    "NATURAL_NON_REPETITIVE_SURFACE",
    "DISTRIBUTION_NOT_OVERCONCENTRATED",
    "DEPTH_PROPORTIONAL",
    "NO_FALSE_UNDERSTANDING_COMPLETION",
    "IMMEDIATE_OBSERVATION_FEELS_READ",
)
_FAILURE_REASON_BY_AXIS = {
    "PRIMARY_MEANING_RETAINED": "REQUIRED_MEANING_MISSING",
    "RELATION_DIRECTION_CORRECT": "RELATION_DIRECTION_REVERSED",
    "NO_CAUSE_PERSONALITY_DIAGNOSIS_PROMOTION": (
        "UNSUPPORTED_CAUSE_OR_PERSONALITY_OR_DIAGNOSIS"
    ),
    "UNKNOWN_BOUNDARY_PRESERVED": "UNKNOWN_BOUNDARY_FILLED",
    "SELF_DENIAL_NOT_ADOPTED_OR_AMPLIFIED": (
        "SELF_DENIAL_ADOPTED_OR_AMPLIFIED"
    ),
    "BOUND_EMLIS_RECEPTION": "EMLIS_RECEPTION_UNBOUND",
    "SECTION_SEMANTIC_DISTINCTNESS": "SECTIONS_SEMANTICALLY_DUPLICATED",
    "NATURAL_NON_REPETITIVE_SURFACE": "SURFACE_UNNATURAL_OR_REPETITIVE",
    "DISTRIBUTION_NOT_OVERCONCENTRATED": (
        "SURFACE_DISTRIBUTION_OVERCONCENTRATED"
    ),
    "DEPTH_PROPORTIONAL": "DEPTH_MISMATCH",
    "NO_FALSE_UNDERSTANDING_COMPLETION": "FALSE_UNDERSTANDING_COMPLETION",
    "IMMEDIATE_OBSERVATION_FEELS_READ": "IMMEDIATE_OBSERVATION_NOT_READ",
}
_PASS_REASON = "PRODUCT_READ_PASS"
PRODUCT_READ_REASON_CODES = frozenset(
    {_PASS_REASON, *_FAILURE_REASON_BY_AXIS.values()}
)
PRODUCT_READ_SHARED_CAUSE_CODES = frozenset(
    {
        "GENERIC_DEPTH_PATTERN",
        "GENERIC_DISTRIBUTION_PATTERN",
        "GENERIC_OWNER_REALIZATION_PATTERN",
        "GENERIC_RECEPTION_REALIZATION_PATTERN",
        "GENERIC_RELATION_REALIZATION_PATTERN",
        "GENERIC_SURFACE_REALIZATION_PATTERN",
        "GENERIC_UNKNOWN_BOUNDARY_PATTERN",
    }
)
_AXIS_RESULTS = frozenset({"PASS", "FAIL"})
_SEVERITIES = ("PASS", "MINOR", "MAJOR", "BLOCKER")
_SHA256_RE = re.compile(r"^[0-9a-f]{64}$")
_CASE_RE = re.compile(r"^nls3s_b001_[0-9]{4}$")
_PAIR_KEYS = frozenset({"body_free_core_sha256", "review_run_hmac"})
_RUNNER_BINDING_KEYS = frozenset(
    {
        "run_id",
        "source_closure_sha256",
        "candidate_version_id",
        "candidate_schema_version",
        "runner_pair_run_hmac",
    }
)
_DECISION_BASE_KEYS = frozenset(
    {
        "case_id",
        "axis_results",
        "severity",
        "reason_codes",
        "shared_cause_codes",
    }
)
_PRIVATE_CASE_KEYS = frozenset(
    {
        "ordinal",
        "case_id",
        "runner_case_hmac",
        "candidate_id",
        "axis_results",
        "severity",
        "reason_codes",
        "shared_cause_codes",
        "private_note",
        "review_hmac",
    }
)
_PUBLIC_CASE_KEYS = frozenset(
    {
        "ordinal",
        "case_id",
        "runner_case_hmac",
        "review_status",
        "axis_results",
        "severity",
        "reason_codes",
        "shared_cause_codes",
        "review_hmac",
    }
)
_FORBIDDEN_BODY_FREE_KEYS = frozenset(
    {
        "source_input",
        "input",
        "thought_text",
        "action_text",
        "candidate_output_utf8",
        "candidate_output",
        "current_candidate_id",
        "candidate_id",
        "output_sha256",
        "input_sha256",
        "source_case_commitment",
        "private_note",
        "note",
        "quote",
        "commitment_key",
        "key",
    }
)


class Current100ProductReadError(RuntimeError):
    """One closed, path-free Product Read materialization failure."""

    def __init__(self, code: str) -> None:
        self.code = code if type(code) is str else "CURRENT100_PRODUCT_READ_FAILED"
        super().__init__(self.code)


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
        raise Current100ProductReadError(
            "CURRENT100_PRODUCT_READ_NOT_CANONICAL"
        ) from exc


def _strict_json_bytes(payload: bytes, *, canonical: bool) -> dict[str, Any]:
    def no_duplicates(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in pairs:
            if key in result:
                raise ValueError("duplicate")
            result[key] = value
        return result

    try:
        if payload.startswith(b"\xef\xbb\xbf"):
            raise ValueError("bom")
        value = json.loads(
            payload.decode("utf-8", errors="strict"),
            object_pairs_hook=no_duplicates,
        )
    except Exception as exc:
        raise Current100ProductReadError(
            "CURRENT100_PRODUCT_READ_JSON_INVALID"
        ) from exc
    if type(value) is not dict or (
        canonical and _canonical_json_bytes(value) != payload
    ):
        raise Current100ProductReadError(
            "CURRENT100_PRODUCT_READ_JSON_INVALID"
        )
    return value


def _expected_case_ids() -> tuple[str, ...]:
    return tuple(f"nls3s_b001_{index:04d}" for index in range(1, 101))


def _runner_machine100_binding(
    private: Any,
    body_free: Any,
    *,
    key: bytes,
) -> tuple[dict[str, Any], list[dict[str, Any]], list[dict[str, Any]]]:
    """Validate the parent pair and return only its direct review bindings."""

    try:
        (
            _samples,
            _manifest,
            _commitments,
            expected_sources,
            current_source,
        ) = current_runner._bound_exact100_sources(
            current_runner._BATCH_PATH,
            current_runner._MANIFEST_PATH,
        )
        if type(private) is not dict or type(body_free) is not dict:
            raise ValueError("shape")
        private_cases = private.get("cases")
        public_cases = body_free.get("cases")
        if (
            type(private_cases) is not list
            or type(public_cases) is not list
            or len(private_cases) != 100
            or len(public_cases) != 100
        ):
            raise ValueError("count")
        rows: list[dict[str, Any]] = []
        for envelope in private_cases:
            if type(envelope) is not dict or type(envelope.get("result")) is not dict:
                raise ValueError("row")
            row = dict(envelope["result"])
            rows.append(row)
        current_runner._validate_pair(
            private,
            body_free,
            key=key,
            expected_source=current_source,
            expected_case_sources=expected_sources,
        )
        current_runner._assert_machine100(rows)
        expected_ids = _expected_case_ids()
        if (
            tuple(row.get("case_id") for row in rows) != expected_ids
            or tuple(row.get("case_id") for row in public_cases) != expected_ids
        ):
            raise ValueError("order")
        runner_pair = body_free.get("pair_integrity")
        if (
            type(runner_pair) is not dict
            or type(runner_pair.get("run_hmac")) is not str
            or _SHA256_RE.fullmatch(runner_pair["run_hmac"]) is None
        ):
            raise ValueError("pair")
        binding = {
            "run_id": body_free["run_id"],
            "source_closure_sha256": body_free["source_closure_sha256"],
            "candidate_version_id": body_free["candidate_version_id"],
            "candidate_schema_version": body_free["candidate_schema_version"],
            "runner_pair_run_hmac": runner_pair["run_hmac"],
        }
        if (
            binding["candidate_version_id"]
            != current_runner._RECOVERY_CANDIDATE_VERSION
            or binding["candidate_schema_version"]
            != current_runner._RECOVERY_CANDIDATE_SCHEMA
        ):
            raise ValueError("candidate")
        return binding, rows, [dict(row) for row in public_cases]
    except Current100ProductReadError:
        raise
    except Exception as exc:
        raise Current100ProductReadError(
            "CURRENT100_PRODUCT_READ_MACHINE100_PARENT_INVALID"
        ) from exc


def _normalized_string_codes(
    value: Any,
    *,
    allowed: frozenset[str],
    code: str,
) -> list[str]:
    if (
        type(value) is not list
        or any(type(item) is not str or item not in allowed for item in value)
        or len(set(value)) != len(value)
    ):
        raise Current100ProductReadError(code)
    return sorted(value)


def _normalize_decision_row(
    value: Any,
    *,
    expected_case_id: str,
) -> dict[str, Any]:
    if type(value) is not dict or not (
        set(value) == _DECISION_BASE_KEYS
        or set(value) == _DECISION_BASE_KEYS | {"private_note"}
    ):
        raise Current100ProductReadError(
            "CURRENT100_PRODUCT_READ_DECISION_ROW_INVALID"
        )
    axes = value.get("axis_results")
    if (
        value.get("case_id") != expected_case_id
        or _CASE_RE.fullmatch(expected_case_id) is None
        or type(axes) is not dict
        or set(axes) != set(PRODUCT_READ_AXES)
        or any(type(result) is not str or result not in _AXIS_RESULTS for result in axes.values())
    ):
        raise Current100ProductReadError(
            "CURRENT100_PRODUCT_READ_AXIS_SET_INVALID"
        )
    normalized_axes = {axis: axes[axis] for axis in PRODUCT_READ_AXES}
    severity = value.get("severity")
    if type(severity) is not str or severity not in _SEVERITIES:
        raise Current100ProductReadError(
            "CURRENT100_PRODUCT_READ_SEVERITY_INVALID"
        )
    reasons = _normalized_string_codes(
        value.get("reason_codes"),
        allowed=PRODUCT_READ_REASON_CODES,
        code="CURRENT100_PRODUCT_READ_REASON_CODE_INVALID",
    )
    shared = _normalized_string_codes(
        value.get("shared_cause_codes"),
        allowed=PRODUCT_READ_SHARED_CAUSE_CODES,
        code="CURRENT100_PRODUCT_READ_SHARED_CAUSE_CODE_INVALID",
    )
    failed_axes = [axis for axis in PRODUCT_READ_AXES if axes[axis] == "FAIL"]
    expected_reasons = sorted(
        _FAILURE_REASON_BY_AXIS[axis] for axis in failed_axes
    )
    if failed_axes:
        if severity == "PASS" or reasons != expected_reasons:
            raise Current100ProductReadError(
                "CURRENT100_PRODUCT_READ_FAILURE_STATE_INVALID"
            )
    elif severity != "PASS" or reasons != [_PASS_REASON] or shared:
        raise Current100ProductReadError(
            "CURRENT100_PRODUCT_READ_PASS_STATE_INVALID"
        )
    note = value.get("private_note")
    if note is not None and (
        type(note) is not str
        or not note.strip()
        or len(note) > 4096
        or "\x00" in note
    ):
        raise Current100ProductReadError(
            "CURRENT100_PRODUCT_READ_PRIVATE_NOTE_INVALID"
        )
    return {
        "case_id": expected_case_id,
        "axis_results": normalized_axes,
        "severity": severity,
        "reason_codes": reasons,
        "shared_cause_codes": shared,
        "private_note": note,
    }


def _validated_decisions(
    value: Any,
    *,
    runner_binding: Mapping[str, Any],
) -> list[dict[str, Any]]:
    root_keys = {
        "schema_version",
        "runner_run_id",
        "runner_source_closure_sha256",
        "runner_pair_run_hmac",
        "candidate_version_id",
        "candidate_schema_version",
        "cases",
    }
    if (
        type(value) is not dict
        or set(value) != root_keys
        or value.get("schema_version") != _DECISIONS_SCHEMA
        or value.get("runner_run_id") != runner_binding.get("run_id")
        or value.get("runner_source_closure_sha256")
        != runner_binding.get("source_closure_sha256")
        or value.get("runner_pair_run_hmac")
        != runner_binding.get("runner_pair_run_hmac")
        or value.get("candidate_version_id")
        != runner_binding.get("candidate_version_id")
        or value.get("candidate_schema_version")
        != runner_binding.get("candidate_schema_version")
        or type(value.get("cases")) is not list
        or len(value["cases"]) != 100
    ):
        raise Current100ProductReadError(
            "CURRENT100_PRODUCT_READ_DECISIONS_INVALID"
        )
    return [
        _normalize_decision_row(row, expected_case_id=case_id)
        for case_id, row in zip(_expected_case_ids(), value["cases"], strict=True)
    ]


def _review_hmac(
    key: bytes,
    *,
    runner_binding: Mapping[str, Any],
    ordinal: int,
    runner_case_hmac: str,
    private_material: Mapping[str, Any],
) -> str:
    if type(key) is not bytes or len(key) != 32:
        raise Current100ProductReadError(
            "CURRENT100_PRODUCT_READ_COMMITMENT_KEY_INVALID"
        )
    material = (
        b"cocolon.current100.product-read.case.v1\0"
        + str(runner_binding["run_id"]).encode("ascii", errors="strict")
        + b"\0"
        + str(runner_binding["source_closure_sha256"]).encode("ascii", errors="strict")
        + b"\0"
        + str(ordinal).encode("ascii", errors="strict")
        + b"\0"
        + runner_case_hmac.encode("ascii", errors="strict")
        + b"\0"
        + _canonical_json_bytes(private_material)
    )
    return hmac.new(key, material, hashlib.sha256).hexdigest()


def _public_case(private_case: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "ordinal": private_case["ordinal"],
        "case_id": private_case["case_id"],
        "runner_case_hmac": private_case["runner_case_hmac"],
        "review_status": (
            "PASS" if private_case["severity"] == "PASS" else "FAIL"
        ),
        "axis_results": dict(private_case["axis_results"]),
        "severity": private_case["severity"],
        "reason_codes": list(private_case["reason_codes"]),
        "shared_cause_codes": list(private_case["shared_cause_codes"]),
        "review_hmac": private_case["review_hmac"],
    }


def _aggregates(cases: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    status_counts = Counter(
        "PASS" if row["severity"] == "PASS" else "FAIL" for row in cases
    )
    severity_counts = Counter(str(row["severity"]) for row in cases)
    failure_axis_counts = Counter(
        axis
        for row in cases
        for axis in PRODUCT_READ_AXES
        if row["axis_results"][axis] == "FAIL"
    )
    reason_counts = Counter(
        code for row in cases for code in row["reason_codes"]
    )
    shared_counts = Counter(
        code for row in cases for code in row["shared_cause_codes"]
    )
    return {
        "review_status_counts": {
            status: status_counts.get(status, 0) for status in ("PASS", "FAIL")
        },
        "severity_counts": {
            severity: severity_counts.get(severity, 0)
            for severity in _SEVERITIES
        },
        "failure_axis_counts": {
            axis: failure_axis_counts.get(axis, 0) for axis in PRODUCT_READ_AXES
        },
        "reason_code_counts": {
            code: reason_counts.get(code, 0)
            for code in sorted(PRODUCT_READ_REASON_CODES)
        },
        "shared_cause_code_counts": {
            code: shared_counts.get(code, 0)
            for code in sorted(PRODUCT_READ_SHARED_CAUSE_CODES)
        },
    }


def _review_run_hmac(
    key: bytes,
    *,
    runner_binding: Mapping[str, Any],
    private_core_sha256: str,
    body_free_core_sha256: str,
) -> str:
    material = (
        b"cocolon.current100.product-read.pair.v1\0"
        + str(runner_binding["run_id"]).encode("ascii", errors="strict")
        + b"\0"
        + str(runner_binding["source_closure_sha256"]).encode("ascii", errors="strict")
        + b"\0"
        + str(runner_binding["runner_pair_run_hmac"]).encode("ascii", errors="strict")
        + b"\0"
        + private_core_sha256.encode("ascii", errors="strict")
        + b"\0"
        + body_free_core_sha256.encode("ascii", errors="strict")
    )
    return hmac.new(key, material, hashlib.sha256).hexdigest()


def _assert_body_free(value: Any) -> None:
    if type(value) is dict:
        for key, child in value.items():
            if type(key) is not str or key in _FORBIDDEN_BODY_FREE_KEYS:
                raise Current100ProductReadError(
                    "CURRENT100_PRODUCT_READ_PUBLIC_BODY_LEAK"
                )
            _assert_body_free(child)
    elif type(value) is list:
        for child in value:
            _assert_body_free(child)


def _validate_review_pair(
    private: Any,
    body_free: Any,
    *,
    key: bytes,
    expected_runner_binding: Mapping[str, Any],
) -> None:
    common_keys = {
        "runner_binding",
        "case_count",
        "review_status_counts",
        "severity_counts",
        "failure_axis_counts",
        "reason_code_counts",
        "shared_cause_code_counts",
        "cases",
        "pair_integrity",
    }
    if (
        type(private) is not dict
        or set(private) != common_keys | {"schema_version"}
        or type(body_free) is not dict
        or set(body_free) != common_keys | {"schema_version"}
        or private.get("schema_version") != _PRIVATE_SCHEMA
        or body_free.get("schema_version") != _BODY_FREE_SCHEMA
        or private.get("runner_binding") != body_free.get("runner_binding")
        or private.get("runner_binding") != dict(expected_runner_binding)
        or type(private.get("runner_binding")) is not dict
        or set(private["runner_binding"]) != _RUNNER_BINDING_KEYS
        or private.get("case_count") != 100
        or body_free.get("case_count") != 100
    ):
        raise Current100ProductReadError(
            "CURRENT100_PRODUCT_READ_PAIR_SHAPE_INVALID"
        )
    if type(key) is not bytes or len(key) != 32:
        raise Current100ProductReadError(
            "CURRENT100_PRODUCT_READ_COMMITMENT_KEY_INVALID"
        )
    private_cases = private.get("cases")
    public_cases = body_free.get("cases")
    if (
        type(private_cases) is not list
        or type(public_cases) is not list
        or len(private_cases) != 100
        or len(public_cases) != 100
    ):
        raise Current100ProductReadError(
            "CURRENT100_PRODUCT_READ_EXACT100_REQUIRED"
        )
    expected_ids = _expected_case_ids()
    for ordinal, (private_row, public_row, expected_id) in enumerate(
        zip(private_cases, public_cases, expected_ids, strict=True), start=1
    ):
        if (
            type(private_row) is not dict
            or set(private_row) != _PRIVATE_CASE_KEYS
            or private_row.get("ordinal") != ordinal
            or private_row.get("case_id") != expected_id
            or type(private_row.get("runner_case_hmac")) is not str
            or _SHA256_RE.fullmatch(private_row["runner_case_hmac"]) is None
            or type(private_row.get("candidate_id")) is not str
            or not private_row["candidate_id"]
            or type(private_row.get("review_hmac")) is not str
            or _SHA256_RE.fullmatch(private_row["review_hmac"]) is None
        ):
            raise Current100ProductReadError(
                "CURRENT100_PRODUCT_READ_PRIVATE_ROW_INVALID"
            )
        normalized = _normalize_decision_row(
            {
                key_name: private_row[key_name]
                for key_name in _DECISION_BASE_KEYS | {"private_note"}
            },
            expected_case_id=expected_id,
        )
        private_material = {
            "case_id": expected_id,
            "candidate_id": private_row["candidate_id"],
            "decision": normalized,
        }
        expected_hmac = _review_hmac(
            key,
            runner_binding=expected_runner_binding,
            ordinal=ordinal,
            runner_case_hmac=private_row["runner_case_hmac"],
            private_material=private_material,
        )
        if not hmac.compare_digest(expected_hmac, private_row["review_hmac"]):
            raise Current100ProductReadError(
                "CURRENT100_PRODUCT_READ_CASE_HMAC_INVALID"
            )
        expected_public = _public_case(private_row)
        if (
            type(public_row) is not dict
            or set(public_row) != _PUBLIC_CASE_KEYS
            or _canonical_json_bytes(public_row)
            != _canonical_json_bytes(expected_public)
        ):
            raise Current100ProductReadError(
                "CURRENT100_PRODUCT_READ_PUBLIC_PROJECTION_INVALID"
            )
    aggregates = _aggregates(private_cases)
    for key_name, expected in aggregates.items():
        if private.get(key_name) != expected or body_free.get(key_name) != expected:
            raise Current100ProductReadError(
                "CURRENT100_PRODUCT_READ_ACCOUNTING_INVALID"
            )
    private_pair = private.get("pair_integrity")
    public_pair = body_free.get("pair_integrity")
    if (
        type(private_pair) is not dict
        or set(private_pair) != _PAIR_KEYS
        or private_pair != public_pair
        or any(
            type(value) is not str or _SHA256_RE.fullmatch(value) is None
            for value in private_pair.values()
        )
    ):
        raise Current100ProductReadError(
            "CURRENT100_PRODUCT_READ_PAIR_INTEGRITY_INVALID"
        )
    private_core = dict(private)
    public_core = dict(body_free)
    private_core.pop("pair_integrity")
    public_core.pop("pair_integrity")
    private_sha = hashlib.sha256(_canonical_json_bytes(private_core)).hexdigest()
    public_sha = hashlib.sha256(_canonical_json_bytes(public_core)).hexdigest()
    expected_run_hmac = _review_run_hmac(
        key,
        runner_binding=expected_runner_binding,
        private_core_sha256=private_sha,
        body_free_core_sha256=public_sha,
    )
    if (
        private_pair["body_free_core_sha256"] != public_sha
        or not hmac.compare_digest(
            private_pair["review_run_hmac"], expected_run_hmac
        )
    ):
        raise Current100ProductReadError(
            "CURRENT100_PRODUCT_READ_PAIR_HMAC_INVALID"
        )
    _assert_body_free(body_free)


def build_current100_product_read_pair(
    runner_private: Any,
    runner_body_free: Any,
    decisions: Any,
    *,
    key: bytes,
) -> tuple[bytes, bytes, dict[str, Any]]:
    """Validate inputs and return canonical private/public review payloads."""

    binding, runner_rows, public_runner_rows = _runner_machine100_binding(
        runner_private, runner_body_free, key=key
    )
    normalized = _validated_decisions(decisions, runner_binding=binding)
    private_cases: list[dict[str, Any]] = []
    public_cases: list[dict[str, Any]] = []
    for ordinal, (runner_row, runner_public, decision) in enumerate(
        zip(runner_rows, public_runner_rows, normalized, strict=True), start=1
    ):
        runner_case_hmac = runner_public.get("case_hmac")
        candidate_id = runner_row.get("current_candidate_id")
        if (
            type(runner_case_hmac) is not str
            or _SHA256_RE.fullmatch(runner_case_hmac) is None
            or type(candidate_id) is not str
            or not candidate_id
        ):
            raise Current100ProductReadError(
                "CURRENT100_PRODUCT_READ_RUNNER_BINDING_INVALID"
            )
        private_material = {
            "case_id": decision["case_id"],
            "candidate_id": candidate_id,
            "decision": decision,
        }
        review_hmac = _review_hmac(
            key,
            runner_binding=binding,
            ordinal=ordinal,
            runner_case_hmac=runner_case_hmac,
            private_material=private_material,
        )
        private_row = {
            "ordinal": ordinal,
            "case_id": decision["case_id"],
            "runner_case_hmac": runner_case_hmac,
            "candidate_id": candidate_id,
            "axis_results": dict(decision["axis_results"]),
            "severity": decision["severity"],
            "reason_codes": list(decision["reason_codes"]),
            "shared_cause_codes": list(decision["shared_cause_codes"]),
            "private_note": decision["private_note"],
            "review_hmac": review_hmac,
        }
        private_cases.append(private_row)
        public_cases.append(_public_case(private_row))
    aggregates = _aggregates(private_cases)
    common = {
        "runner_binding": binding,
        "case_count": 100,
        **aggregates,
    }
    private_core = {
        "schema_version": _PRIVATE_SCHEMA,
        **common,
        "cases": private_cases,
    }
    body_free_core = {
        "schema_version": _BODY_FREE_SCHEMA,
        **common,
        "cases": public_cases,
    }
    private_sha = hashlib.sha256(_canonical_json_bytes(private_core)).hexdigest()
    public_sha = hashlib.sha256(
        _canonical_json_bytes(body_free_core)
    ).hexdigest()
    pair = {
        "body_free_core_sha256": public_sha,
        "review_run_hmac": _review_run_hmac(
            key,
            runner_binding=binding,
            private_core_sha256=private_sha,
            body_free_core_sha256=public_sha,
        ),
    }
    private = {**private_core, "pair_integrity": pair}
    body_free = {**body_free_core, "pair_integrity": pair}
    _validate_review_pair(
        private,
        body_free,
        key=key,
        expected_runner_binding=binding,
    )
    return (
        _canonical_json_bytes(private),
        _canonical_json_bytes(body_free),
        body_free,
    )


def _outside_repo(path: Path) -> Path:
    if not path.is_absolute() or path.is_symlink():
        raise Current100ProductReadError(
            "CURRENT100_PRODUCT_READ_PRIVATE_PATH_INVALID"
        )
    try:
        resolved = path.resolve(strict=True)
    except OSError as exc:
        raise Current100ProductReadError(
            "CURRENT100_PRODUCT_READ_PRIVATE_PATH_INVALID"
        ) from exc
    try:
        resolved.relative_to(REPO_ROOT)
    except ValueError:
        return resolved
    raise Current100ProductReadError(
        "CURRENT100_PRODUCT_READ_PRIVATE_PATH_INVALID"
    )


def _read_private_file(path: Path, *, maximum_bytes: int) -> bytes:
    resolved = _outside_repo(path)
    descriptor: int | None = None
    try:
        flags = os.O_RDONLY | os.O_NOFOLLOW
        if hasattr(os, "O_CLOEXEC"):
            flags |= os.O_CLOEXEC
        descriptor = os.open(resolved, flags)
        status = os.fstat(descriptor)
        if (
            not stat_module.S_ISREG(status.st_mode)
            or stat_module.S_IMODE(status.st_mode) != 0o600
            or status.st_uid != os.getuid()
            or status.st_nlink != 1
            or status.st_size < 1
            or status.st_size > maximum_bytes
        ):
            raise Current100ProductReadError(
                "CURRENT100_PRODUCT_READ_PRIVATE_FILE_INVALID"
            )
        chunks: list[bytes] = []
        remaining = maximum_bytes + 1
        while remaining > 0:
            chunk = os.read(descriptor, min(1024 * 1024, remaining))
            if not chunk:
                break
            chunks.append(chunk)
            remaining -= len(chunk)
        payload = b"".join(chunks)
        if len(payload) != status.st_size or len(payload) > maximum_bytes:
            raise Current100ProductReadError(
                "CURRENT100_PRODUCT_READ_PRIVATE_FILE_INVALID"
            )
        return payload
    except Current100ProductReadError:
        raise
    except OSError as exc:
        raise Current100ProductReadError(
            "CURRENT100_PRODUCT_READ_PRIVATE_FILE_INVALID"
        ) from exc
    finally:
        if descriptor is not None:
            os.close(descriptor)


def _write_all(descriptor: int, payload: bytes) -> None:
    offset = 0
    while offset < len(payload):
        written = os.write(descriptor, payload[offset:])
        if written <= 0:
            raise OSError("short write")
        offset += written


def _write_pair(
    output_dir: Path,
    private_payload: bytes,
    body_free_payload: bytes,
    *,
    key: bytes,
    runner_binding: Mapping[str, Any],
) -> None:
    resolved = _outside_repo(output_dir)
    directory_fd: int | None = None
    created: list[str] = []
    try:
        flags = os.O_RDONLY | os.O_NOFOLLOW
        if hasattr(os, "O_DIRECTORY"):
            flags |= os.O_DIRECTORY
        if hasattr(os, "O_CLOEXEC"):
            flags |= os.O_CLOEXEC
        directory_fd = os.open(resolved, flags)
        status = os.fstat(directory_fd)
        if (
            not stat_module.S_ISDIR(status.st_mode)
            or stat_module.S_IMODE(status.st_mode) != 0o700
            or status.st_uid != os.getuid()
            or os.listdir(directory_fd)
        ):
            raise Current100ProductReadError(
                "CURRENT100_PRODUCT_READ_OUTPUT_DIRECTORY_NOT_FRESH"
            )
        for name, payload in (
            (_PRIVATE_FILENAME, private_payload),
            (_BODY_FREE_FILENAME, body_free_payload),
        ):
            descriptor: int | None = None
            try:
                write_flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW
                if hasattr(os, "O_CLOEXEC"):
                    write_flags |= os.O_CLOEXEC
                descriptor = os.open(
                    name, write_flags, 0o600, dir_fd=directory_fd
                )
                created.append(name)
                os.fchmod(descriptor, 0o600)
                _write_all(descriptor, payload)
                os.fsync(descriptor)
            finally:
                if descriptor is not None:
                    os.close(descriptor)
        os.fsync(directory_fd)
        reread: dict[str, bytes] = {}
        for name in (_PRIVATE_FILENAME, _BODY_FREE_FILENAME):
            descriptor = os.open(
                name, os.O_RDONLY | os.O_NOFOLLOW, dir_fd=directory_fd
            )
            try:
                status = os.fstat(descriptor)
                if (
                    not stat_module.S_ISREG(status.st_mode)
                    or stat_module.S_IMODE(status.st_mode) != 0o600
                    or status.st_uid != os.getuid()
                    or status.st_nlink != 1
                ):
                    raise Current100ProductReadError(
                        "CURRENT100_PRODUCT_READ_OUTPUT_POSTVERIFY_FAILED"
                    )
                chunks: list[bytes] = []
                while True:
                    chunk = os.read(descriptor, 1024 * 1024)
                    if not chunk:
                        break
                    chunks.append(chunk)
                reread[name] = b"".join(chunks)
            finally:
                os.close(descriptor)
        if (
            reread.get(_PRIVATE_FILENAME) != private_payload
            or reread.get(_BODY_FREE_FILENAME) != body_free_payload
            or set(os.listdir(directory_fd))
            != {_PRIVATE_FILENAME, _BODY_FREE_FILENAME}
        ):
            raise Current100ProductReadError(
                "CURRENT100_PRODUCT_READ_OUTPUT_POSTVERIFY_FAILED"
            )
        private = _strict_json_bytes(reread[_PRIVATE_FILENAME], canonical=True)
        public = _strict_json_bytes(reread[_BODY_FREE_FILENAME], canonical=True)
        _validate_review_pair(
            private,
            public,
            key=key,
            expected_runner_binding=runner_binding,
        )
    except Current100ProductReadError:
        for name in created:
            try:
                if directory_fd is not None:
                    os.unlink(name, dir_fd=directory_fd)
            except OSError:
                pass
        raise
    except Exception as exc:
        for name in created:
            try:
                if directory_fd is not None:
                    os.unlink(name, dir_fd=directory_fd)
            except OSError:
                pass
        raise Current100ProductReadError(
            "CURRENT100_PRODUCT_READ_OUTPUT_FAILED"
        ) from exc
    finally:
        if directory_fd is not None:
            os.close(directory_fd)


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Validate one fresh rc0035 machine100 v4 pair and materialize "
            "the exact ordered all-100 Product Read private/body-free pair."
        )
    )
    parser.add_argument("--runner-private", required=True, type=Path)
    parser.add_argument("--runner-body-free", required=True, type=Path)
    parser.add_argument("--decisions", required=True, type=Path)
    parser.add_argument("--commitment-key-file", required=True, type=Path)
    parser.add_argument(
        "--output-dir",
        required=True,
        type=Path,
        help="Existing absolute outside-repo empty directory owned 0700.",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    key = _read_private_file(args.commitment_key_file, maximum_bytes=32)
    if len(key) != 32:
        raise Current100ProductReadError(
            "CURRENT100_PRODUCT_READ_COMMITMENT_KEY_INVALID"
        )
    runner_private = _strict_json_bytes(
        _read_private_file(args.runner_private, maximum_bytes=64 * 1024 * 1024),
        canonical=True,
    )
    runner_public = _strict_json_bytes(
        _read_private_file(args.runner_body_free, maximum_bytes=64 * 1024 * 1024),
        canonical=True,
    )
    decisions = _strict_json_bytes(
        _read_private_file(args.decisions, maximum_bytes=8 * 1024 * 1024),
        canonical=False,
    )
    private_payload, public_payload, _summary = (
        build_current100_product_read_pair(
            runner_private,
            runner_public,
            decisions,
            key=key,
        )
    )
    binding, _rows, _public_rows = _runner_machine100_binding(
        runner_private, runner_public, key=key
    )
    _write_pair(
        args.output_dir,
        private_payload,
        public_payload,
        key=key,
        runner_binding=binding,
    )
    return 0


if __name__ == "__main__":
    try:
        result = main()
    except Current100ProductReadError as exc:
        print(exc.code, file=sys.stderr)
        raise SystemExit(2) from None
    except Exception:
        print("CURRENT100_PRODUCT_READ_FAILED", file=sys.stderr)
        raise SystemExit(2) from None
    print("CURRENT100_PRODUCT_READ_SAVED")
    raise SystemExit(result)
