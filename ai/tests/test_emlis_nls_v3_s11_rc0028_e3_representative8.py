# -*- coding: utf-8 -*-
from __future__ import annotations

"""E3 machine gate for the frozen rc0028 representative eight.

This suite deliberately does not perform Product Read.  Human review remains
an external, body-free authorization receipt and is tested as the prerequisite
to E4 in the companion frozen-100 contract.
"""

import hashlib
import json
from pathlib import Path
from typing import Any

import pytest

from emlis_ai_step11_rc0028_experiment_runtime_adapter_v3 import (
    STEP11_RC0028_EXPERIMENT_CANDIDATE_VERSION_ID,
    run_step11_rc0028_experiment,
    step11_rc0028_experiment_result_material,
    validate_step11_rc0028_experiment_result,
)


_FIXTURE_ROOT = (
    Path(__file__).resolve().parent / "fixtures" / "emlis_nls_v3"
)
_CYCLE_ROOT = _FIXTURE_ROOT / "cycle_001"
_GENERATED_ROOT = _FIXTURE_ROOT / "generated"
_REPRESENTATIVE = _CYCLE_ROOT / "rc0028_representative8_body_free.json"
_DOWNSTREAM_MANIFEST = (
    _CYCLE_ROOT
    / "cycle001_dependency_manifest_rc0028_downstream_experiment.json"
)
_BATCH = _GENERATED_ROOT / "batch_001.jsonl"
_BATCH_MANIFEST = _GENERATED_ROOT / "batch_001_manifest.json"
_COVERAGE = _GENERATED_ROOT / "batch_001_coverage_matrix.json"
_DUPLICATES = _GENERATED_ROOT / "batch_001_duplicate_report.json"

_REPRESENTATIVE_SHA256 = (
    "6703815684c878b6d00554ad393f23964aa69d7110888e8786fc074faa2d6efd"
)
_EXPECTED_ROWS = (
    ("nls3s_b001_0001", "control", "PASS"),
    ("nls3s_b001_0002", "control", "PASS"),
    ("nls3s_b001_0009", "control", "MINOR"),
    ("nls3s_b001_0019", "improvement_target", "MAJOR"),
    ("nls3s_b001_0035", "improvement_target", "MAJOR"),
    ("nls3s_b001_0043", "improvement_target", "MAJOR"),
    ("nls3s_b001_0063", "improvement_target", "MAJOR"),
    ("nls3s_b001_0100", "improvement_target", "MAJOR"),
)
_FORBIDDEN_BODY_KEYS = frozenset(
    {
        "action_text",
        "body",
        "current_input",
        "final_utf8_bytes",
        "normalized_input",
        "output",
        "parsed_witness",
        "rendered_surface",
        "source_fragment",
        "thought_text",
        "unsalted_body_digest",
        "utf8_bytes",
    }
)


def _load_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    assert type(value) is dict
    return value


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _all_mapping_keys(value: Any) -> frozenset[str]:
    keys: set[str] = set()
    if type(value) is dict:
        keys.update(value)
        for child in value.values():
            keys.update(_all_mapping_keys(child))
    elif type(value) is list:
        for child in value:
            keys.update(_all_mapping_keys(child))
    return frozenset(keys)


@pytest.fixture(scope="module")
def representative_authority() -> tuple[
    dict[str, Any], dict[str, dict[str, Any]], str
]:
    fixture = _load_json(_REPRESENTATIVE)
    batch_manifest = _load_json(_BATCH_MANIFEST)
    samples = {
        row["case_id"]: row
        for row in (
            json.loads(line)
            for line in _BATCH.read_text(encoding="utf-8").splitlines()
            if line
        )
    }
    downstream_manifest = _load_json(_DOWNSTREAM_MANIFEST)
    closure = downstream_manifest.get("source_dependency_closure_sha256")
    assert type(closure) is str and len(closure) == 64

    assert _sha256(_REPRESENTATIVE) == _REPRESENTATIVE_SHA256
    assert fixture == {
        "body_free": True,
        "representative_count": 8,
        "rows": fixture["rows"],
        "schema_version": (
            "cocolon.emlis.nls_v3.rc0028.representative8.body_free.v1"
        ),
        "source_fixture_commitments": fixture["source_fixture_commitments"],
    }
    expected_sources = {
        "batch_manifest_sha256": _sha256(_BATCH_MANIFEST),
        "corpus_file_sha256": _sha256(_BATCH),
        "corpus_set_commitment": batch_manifest["corpus_set_commitment"],
        "coverage_matrix_sha256": _sha256(_COVERAGE),
        "duplicate_report_sha256": _sha256(_DUPLICATES),
    }
    assert fixture["source_fixture_commitments"] == expected_sources

    commitment_by_id = {
        row["case_id"]: row["case_commitment"]
        for row in batch_manifest["case_commitments"]
    }
    assert tuple(
        (
            row["case_id"],
            row["experiment_role"],
            row["baseline_product_read_severity"],
        )
        for row in fixture["rows"]
    ) == _EXPECTED_ROWS
    assert all(
        row["source_case_commitment"]
        == commitment_by_id[row["case_id"]]
        and row["case_id"] in samples
        for row in fixture["rows"]
    )
    return fixture, samples, closure


@pytest.fixture(scope="module")
def representative_machine_results(
    representative_authority: tuple[
        dict[str, Any], dict[str, dict[str, Any]], str
    ],
) -> tuple[Any, ...]:
    fixture, samples, closure = representative_authority
    return tuple(
        run_step11_rc0028_experiment(
            samples[row["case_id"]]["input"],
            case_id=row["case_id"],
            source_case_commitment=row["source_case_commitment"],
            source_dependency_closure_sha256=closure,
        )
        for row in fixture["rows"]
    )


def test_rc0028_e3_fixture_is_exact_body_free_authority(
    representative_authority: tuple[
        dict[str, Any], dict[str, dict[str, Any]], str
    ],
) -> None:
    fixture, _samples, _closure = representative_authority
    assert fixture["representative_count"] == 8
    assert [row[0] for row in _EXPECTED_ROWS] == [
        row["case_id"] for row in fixture["rows"]
    ]


def test_rc0028_e3_public_runtime_accounts_for_eight_selected_results(
    representative_machine_results: tuple[Any, ...],
) -> None:
    assert len(representative_machine_results) == 8
    disposition_counts = {
        status: sum(row.disposition == status for row in representative_machine_results)
        for status in ("selected", "no_valid_candidate", "fail_close")
    }
    assert disposition_counts == {
        "selected": 8,
        "no_valid_candidate": 0,
        "fail_close": 0,
    }
    for row in representative_machine_results:
        assert validate_step11_rc0028_experiment_result(row) == ()
        assert row.experiment_candidate_version_id == (
            STEP11_RC0028_EXPERIMENT_CANDIDATE_VERSION_ID
        )
        assert row.selected_candidate_present is True
        assert row.closed_failure_codes == ()
        assert row.evaluated_candidate_count >= 1
        assert row.hard_gate_pass_count >= 1
        assert row.hard_gate_pass_count + row.rejected_candidate_count == (
            row.evaluated_candidate_count
        )


def test_rc0028_e3_machine_receipts_are_body_free_and_not_product_read(
    representative_machine_results: tuple[Any, ...],
) -> None:
    materials = tuple(
        step11_rc0028_experiment_result_material(row)
        for row in representative_machine_results
    )
    assert all(
        not (_all_mapping_keys(row) & _FORBIDDEN_BODY_KEYS)
        for row in materials
    )
    assert all(
        not any(
            "product_read" in key or "review" in key
            for key in _all_mapping_keys(row)
        )
        for row in materials
    )
    assert all(
        row["experimental_only"] is True
        and row["runtime_connected"] is False
        and row["semantic_coverage_authority"] == "none"
        for row in materials
    )
