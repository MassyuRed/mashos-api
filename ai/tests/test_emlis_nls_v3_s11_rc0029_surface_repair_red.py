# -*- coding: utf-8 -*-
from __future__ import annotations

"""R1 semantic RED for the rc0029 common-Surface repair.

The predecessor is executed through its private, request-local adapter so the
four Product Read failures are proved against final bytes rather than against
the presence of a future API.  Once the versioned rc0029 private adapter is
present, the exact same contract is applied to that successor.  Diagnostics
are closed body-free codes; neither source nor rendered text is emitted.
"""

from functools import lru_cache
import hashlib
import importlib
import json
from pathlib import Path
import re
from typing import Any, Callable

import pytest


_FIXTURE_ROOT = Path(__file__).resolve().parent / "fixtures" / "emlis_nls_v3"
_CYCLE_ROOT = _FIXTURE_ROOT / "cycle_001"
_BATCH = _FIXTURE_ROOT / "generated" / "batch_001.jsonl"
_REPRESENTATIVE = _CYCLE_ROOT / "rc0028_representative8_body_free.json"
_DOWNSTREAM_MANIFEST = (
    _CYCLE_ROOT
    / "cycle001_dependency_manifest_rc0028_downstream_experiment.json"
)

_REPRESENTATIVE_SHA256 = (
    "6703815684c878b6d00554ad393f23964aa69d7110888e8786fc074faa2d6efd"
)
_RC0028_ADAPTER = "emlis_ai_step11_rc0028_experiment_runtime_adapter_v3"
_RC0029_ADAPTER = "emlis_ai_step11_rc0029_experiment_runtime_adapter_v3"
_RC0028_PRIVATE_API = "execute_step11_rc0028_experiment_private"
_RC0029_PRIVATE_API = "execute_step11_rc0029_experiment_private"

_SCHEMA_CASE = "nls3s_b001_0019"
_OPAQUE_REFERENT_CASE = "nls3s_b001_0035"
_DEPTH_CASE = "nls3s_b001_0063"
_RECEPTION_CASE = _SCHEMA_CASE
_R1_CASE_IDS = frozenset(
    {
        _SCHEMA_CASE,
        _OPAQUE_REFERENT_CASE,
        _DEPTH_CASE,
        _RECEPTION_CASE,
    }
)

_FAILURE_FAMILIES = (
    "SCHEMA_EXPOSITION",
    "OPAQUE_ORDINAL_REFERENT",
    "DEPTH_COMPACTION_FAILURE",
    "RECEPTION_BINDING_FAILURE",
)
_FAMILY_ATTACKS = {
    "SCHEMA_EXPOSITION": (
        "machine-taxonomy-marker",
        "record-per-visible-line",
    ),
    "OPAQUE_ORDINAL_REFERENT": (
        "source-order-only-owner-handle",
        "same-kind-owner-collision",
        "owner-count-over-four",
        "endpoint-swap",
    ),
    "DEPTH_COMPACTION_FAILURE": (
        "construction-relation-link-unknown-row-growth",
        "content-depth-budget-overshoot",
        "required-atom-drop-to-shorten",
    ),
    "RECEPTION_BINDING_FAILURE": (
        "generic-reception",
        "antecedent-drop",
        "antecedent-swap",
        "different-owner-binding",
    ),
}

# rc0028's visible owner registry is an ordinal machine registry, not a
# source-authorized semantic head.  It is frozen here rather than read from a
# mutable catalog so changing the predecessor catalog cannot make the RED
# disappear.
_OPAQUE_OWNER_RE = re.compile(
    r"(?:その|もう一方の|さらに別の|[4-9][0-9]*つ目の)内容"
)
_SCHEMA_MARKERS = (
    "構造を見ると、",
    "まだ定まらない点として、",
)


def _closed_fail(code: str) -> None:
    pytest.fail(code, pytrace=False)


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


@lru_cache(maxsize=1)
def _authority() -> tuple[
    dict[str, dict[str, Any]],
    dict[str, str],
    str,
]:
    if _sha256(_REPRESENTATIVE) != _REPRESENTATIVE_SHA256:
        _closed_fail("STEP11_RC0029_R1_REPRESENTATIVE_COMMITMENT_MISMATCH")
    representative = json.loads(_REPRESENTATIVE.read_text(encoding="utf-8"))
    downstream = json.loads(_DOWNSTREAM_MANIFEST.read_text(encoding="utf-8"))
    if type(representative) is not dict or type(downstream) is not dict:
        _closed_fail("STEP11_RC0029_R1_AUTHORITY_TYPE_INVALID")
    closure = downstream.get("source_dependency_closure_sha256")
    if type(closure) is not str or re.fullmatch(r"[0-9a-f]{64}", closure) is None:
        _closed_fail("STEP11_RC0029_R1_SOURCE_CLOSURE_INVALID")

    representative_rows = representative.get("rows")
    if type(representative_rows) is not list:
        _closed_fail("STEP11_RC0029_R1_REPRESENTATIVE_ROWS_INVALID")
    commitments = {
        row.get("case_id"): row.get("source_case_commitment")
        for row in representative_rows
        if type(row) is dict
    }
    if not _R1_CASE_IDS <= set(commitments) or any(
        type(commitments[case_id]) is not str
        or re.fullmatch(r"[0-9a-f]{64}", commitments[case_id]) is None
        for case_id in _R1_CASE_IDS
    ):
        _closed_fail("STEP11_RC0029_R1_CASE_COMMITMENT_MISMATCH")

    samples: dict[str, dict[str, Any]] = {}
    for line in _BATCH.read_text(encoding="utf-8").splitlines():
        if not line:
            continue
        row = json.loads(line)
        if type(row) is dict and row.get("case_id") in _R1_CASE_IDS:
            samples[row["case_id"]] = row
    if set(samples) != set(_R1_CASE_IDS):
        _closed_fail("STEP11_RC0029_R1_SOURCE_CASE_SET_MISMATCH")
    return samples, commitments, closure


@lru_cache(maxsize=1)
def _private_runner() -> Callable[..., Any]:
    """Prefer the versioned successor without hiding an incomplete API."""

    try:
        module = importlib.import_module(_RC0029_ADAPTER)
    except ModuleNotFoundError as error:
        if error.name != _RC0029_ADAPTER:
            raise
        module = importlib.import_module(_RC0028_ADAPTER)
        api_name = _RC0028_PRIVATE_API
    else:
        api_name = _RC0029_PRIVATE_API
    runner = getattr(module, api_name, None)
    if not callable(runner):
        _closed_fail("STEP11_RC0029_R1_PRIVATE_RUNTIME_API_MISSING")
    return runner


@lru_cache(maxsize=None)
def _execution(case_id: str) -> Any:
    samples, commitments, closure = _authority()
    execution = _private_runner()(
        samples[case_id]["input"],
        case_id=case_id,
        source_case_commitment=commitments[case_id],
        source_dependency_closure_sha256=closure,
    )
    result = getattr(execution, "body_free_result", None)
    if (
        result is None
        or getattr(result, "disposition", None) != "selected"
        or getattr(result, "selected_candidate_present", None) is not True
    ):
        _closed_fail("STEP11_RC0029_R1_SUBJECT_NOT_SELECTED")
    if type(getattr(execution, "selected_final_utf8_bytes", None)) is not bytes:
        _closed_fail("STEP11_RC0029_R1_SELECTED_FINAL_BYTES_MISSING")
    return execution


def _selected_candidate(execution: Any) -> Any:
    selection = getattr(execution, "selection_result", None)
    candidate = getattr(selection, "selected_candidate", None)
    if candidate is None:
        _closed_fail("STEP11_RC0029_R1_SELECTED_CANDIDATE_MISSING")
    return candidate


def _surface_text(execution: Any) -> str:
    body = execution.selected_final_utf8_bytes
    try:
        text = body.decode("utf-8", errors="strict")
    except UnicodeDecodeError:
        _closed_fail("STEP11_RC0029_R1_SELECTED_UTF8_INVALID")
    if text.encode("utf-8", errors="strict") != body:
        _closed_fail("STEP11_RC0029_R1_SELECTED_UTF8_NONCANONICAL")
    return text


def _section_line_counts(execution: Any) -> tuple[int, int]:
    text = _surface_text(execution)
    prefix = "見えたこと：\n"
    separator = "\n\nEmlisから：\n"
    if not text.startswith(prefix) or text.count(separator) != 1:
        _closed_fail("STEP11_RC0029_R1_SURFACE_LAYOUT_INVALID")
    observation, reception = text[len(prefix) :].split(separator)
    observation_lines = observation.split("\n")
    reception_lines = reception.split("\n")
    if (
        not observation_lines
        or not reception_lines
        or any(not line for line in (*observation_lines, *reception_lines))
    ):
        _closed_fail("STEP11_RC0029_R1_SURFACE_LAYOUT_INVALID")
    return len(observation_lines), len(reception_lines)


def _structural_record_count(candidate: Any) -> int:
    names = (
        "construction_atoms",
        "relation_atoms",
        "semantic_link_atoms",
        "explicit_unknown_atoms",
    )
    values = tuple(getattr(candidate, name, None) for name in names)
    if any(type(value) is not tuple for value in values):
        _closed_fail("STEP11_RC0029_R1_STRUCTURAL_RECORD_SET_INVALID")
    return sum(len(value) for value in values)


def test_rc0029_r1_failure_family_and_attack_denominator_is_exact() -> None:
    assert tuple(_FAMILY_ATTACKS) == _FAILURE_FAMILIES
    assert sum(len(rows) for rows in _FAMILY_ATTACKS.values()) == 13
    assert len(
        {attack for rows in _FAMILY_ATTACKS.values() for attack in rows}
    ) == 13


def test_rc0029_r1_schema_exposition_rejects_machine_taxonomy_markers() -> None:
    text = _surface_text(_execution(_SCHEMA_CASE))
    if any(marker in text for marker in _SCHEMA_MARKERS):
        _closed_fail("STEP11_RC0029_SCHEMA_EXPOSITION")


def test_rc0029_r1_schema_exposition_rejects_record_per_visible_line() -> None:
    execution = _execution(_SCHEMA_CASE)
    candidate = _selected_candidate(execution)
    base = getattr(candidate, "base_candidate", None)
    base_body = getattr(base, "final_utf8_bytes", None)
    if type(base_body) is not bytes:
        _closed_fail("STEP11_RC0029_R1_BASE_SURFACE_MISSING")
    final_observation_lines, _ = _section_line_counts(execution)
    base_proxy = type("_BaseProxy", (), {"selected_final_utf8_bytes": base_body})()
    base_observation_lines, _ = _section_line_counts(base_proxy)
    record_count = _structural_record_count(candidate)
    if record_count < 2:
        _closed_fail("STEP11_RC0029_R1_SCHEMA_DENOMINATOR_INVALID")
    if final_observation_lines - base_observation_lines >= record_count:
        _closed_fail("STEP11_RC0029_SCHEMA_RECORD_PER_LINE")


def test_rc0029_r1_opaque_ordinal_requires_source_authorized_head() -> None:
    text = _surface_text(_execution(_OPAQUE_REFERENT_CASE))
    if _OPAQUE_OWNER_RE.search(text) is not None:
        _closed_fail("STEP11_RC0029_OPAQUE_ORDINAL_REFERENT")


def test_rc0029_r1_depth_compaction_respects_frozen_content_budget() -> None:
    execution = _execution(_DEPTH_CASE)
    candidate = _selected_candidate(execution)
    if _structural_record_count(candidate) < 4:
        _closed_fail("STEP11_RC0029_R1_DEPTH_DENOMINATOR_INVALID")
    base_execution = getattr(execution, "base_execution", None)
    content_plan = getattr(base_execution, "content_plan", None)
    budget = (
        content_plan.get("section_budget")
        if type(content_plan) is dict
        else None
    )
    required_keys = {
        "observation_sentence_max",
        "reception_sentence_max",
        "total_sentence_max",
    }
    if (
        type(budget) is not dict
        or not required_keys <= set(budget)
        or any(type(budget[key]) is not int for key in required_keys)
    ):
        _closed_fail("STEP11_RC0029_R1_DEPTH_BUDGET_INVALID")
    observation_count, reception_count = _section_line_counts(execution)
    if (
        observation_count > budget["observation_sentence_max"]
        or reception_count > budget["reception_sentence_max"]
        or observation_count + reception_count > budget["total_sentence_max"]
    ):
        _closed_fail("STEP11_RC0029_DEPTH_COMPACTION_FAILURE")


def test_rc0029_r1_reception_requires_body_only_exact_antecedent() -> None:
    execution = _execution(_RECEPTION_CASE)
    parsed = getattr(execution, "selected_parsed_witness", None)
    base_witness = getattr(parsed, "base_witness", parsed)
    atoms = getattr(base_witness, "atoms", None)
    if type(atoms) is not tuple:
        _closed_fail("STEP11_RC0029_R1_RECEPTION_WITNESS_INVALID")
    reception_atoms = tuple(
        atom
        for atom in atoms
        if getattr(atom, "section_role", None) == "reception"
        and getattr(atom, "reception_act", None) is not None
    )
    if not reception_atoms:
        _closed_fail("STEP11_RC0029_R1_RECEPTION_DENOMINATOR_INVALID")
    antecedent_sets = tuple(
        getattr(atom, "reception_antecedent_references", None)
        for atom in reception_atoms
    )
    if any(type(rows) is not tuple for rows in antecedent_sets):
        _closed_fail("STEP11_RC0029_R1_RECEPTION_WITNESS_INVALID")
    if any(len(rows) != 1 for rows in antecedent_sets):
        _closed_fail("STEP11_RC0029_RECEPTION_BINDING_FAILURE")
