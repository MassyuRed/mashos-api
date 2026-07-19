# -*- coding: utf-8 -*-
from __future__ import annotations

"""E4 read-only gate over body-free frozen-100 experiment receipts."""

from copy import deepcopy
import hashlib
import inspect
import json
from pathlib import Path
from typing import Any, Iterable

import pytest

from emlis_ai_nls_v3_artifact_contract import artifact_sha256
import emlis_nls_v3_rc0028_bounded_experiment as bounded


_FIXTURE_ROOT = (
    Path(__file__).resolve().parent / "fixtures" / "emlis_nls_v3"
)
_CYCLE_ROOT = _FIXTURE_ROOT / "cycle_001"
_GENERATED_ROOT = _FIXTURE_ROOT / "generated"
_BATCH_MANIFEST = _GENERATED_ROOT / "batch_001_manifest.json"
_BATCH = _GENERATED_ROOT / "batch_001.jsonl"
_COVERAGE = _GENERATED_ROOT / "batch_001_coverage_matrix.json"
_DUPLICATES = _GENERATED_ROOT / "batch_001_duplicate_report.json"
_RC0027_MANIFEST = _CYCLE_ROOT / "cycle001_dependency_manifest_rc0027.json"
_DOWNSTREAM_MANIFEST = (
    _CYCLE_ROOT
    / "cycle001_dependency_manifest_rc0028_downstream_experiment.json"
)

_REPRESENTATIVE_FIXTURE_SHA256 = (
    "6703815684c878b6d00554ad393f23964aa69d7110888e8786fc074faa2d6efd"
)
_REPRESENTATIVE_IDS = (
    "nls3s_b001_0001",
    "nls3s_b001_0002",
    "nls3s_b001_0009",
    "nls3s_b001_0019",
    "nls3s_b001_0035",
    "nls3s_b001_0043",
    "nls3s_b001_0063",
    "nls3s_b001_0100",
)
_RC0027_SELECTED_56 = frozenset(
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
_NEW_NON_REPRESENTATIVE_CASE = "nls3s_b001_0008"


def _load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    assert type(value) is dict
    return value


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _commitment(label: str) -> str:
    return hashlib.sha256(label.encode("ascii")).hexdigest()


def _case_row(
    case_id: str,
    source_case_commitment: str,
    *,
    selected: bool,
) -> dict[str, Any]:
    if selected:
        counts = {
            "base_candidate_count": 1,
            "construction_atom_count": 0,
            "evaluated_candidate_count": 1,
            "experiment_candidate_count": 1,
            "explicit_unknown_atom_count": 0,
            "hard_gate_pass_count": 1,
            "owner_binding_count": 1,
            "rejected_candidate_count": 0,
            "relation_endpoint_atom_count": 0,
            "replan_count": 0,
            "semantic_link_atom_count": 0,
        }
        hashes: dict[str, str | None] = {
            "lexical_atom_specs_sha256": _commitment(case_id + ":lexical"),
            "result_sha256": _commitment(case_id + ":result"),
            "source_case_commitment": source_case_commitment,
            "successor_authority_sha256": _commitment(case_id + ":authority"),
            "successor_snapshot_sha256": _commitment(case_id + ":snapshot"),
            "successor_witness_sha256": _commitment(case_id + ":witness"),
            "surface_catalog_sha256": _commitment(case_id + ":catalog"),
        }
        disposition = "selected"
        closed_codes: list[str] = []
    else:
        counts = {
            "base_candidate_count": 0,
            "construction_atom_count": 0,
            "evaluated_candidate_count": 0,
            "experiment_candidate_count": 0,
            "explicit_unknown_atom_count": 0,
            "hard_gate_pass_count": 0,
            "owner_binding_count": 0,
            "rejected_candidate_count": 0,
            "relation_endpoint_atom_count": 0,
            "replan_count": 0,
            "semantic_link_atom_count": 0,
        }
        hashes = {
            "lexical_atom_specs_sha256": None,
            "result_sha256": _commitment(case_id + ":result"),
            "source_case_commitment": source_case_commitment,
            "successor_authority_sha256": None,
            "successor_snapshot_sha256": None,
            "successor_witness_sha256": None,
            "surface_catalog_sha256": None,
        }
        disposition = "fail_close"
        closed_codes = ["STEP11_RC0028_PIPELINE_FAIL_CLOSE"]
    return {
        "case_id": case_id,
        "disposition": disposition,
        "counts": counts,
        "hashes": hashes,
        "closed_codes": closed_codes,
    }


def _e4_receipt(selected_ids: Iterable[str]) -> dict[str, Any]:
    selected = frozenset(selected_ids)
    batch_manifest = _load(_BATCH_MANIFEST)
    downstream = _load(_DOWNSTREAM_MANIFEST)
    commitment_by_id = {
        row["case_id"]: row["case_commitment"]
        for row in batch_manifest["case_commitments"]
    }
    cases = [
        _case_row(
            case_id,
            commitment_by_id[case_id],
            selected=case_id in selected,
        )
        for case_id in batch_manifest["case_ids"]
    ]
    counts = {
        status: sum(row["disposition"] == status for row in cases)
        for status in ("fail_close", "no_valid_candidate", "selected")
    }
    e3_receipt_sha256 = _commitment("e3-machine-receipt")
    product_read_authorization = {
        "schema_version": (
            "cocolon.emlis.nls_v3.rc0028."
            "e3_product_read_authorization.body_free.v1"
        ),
        "body_free": True,
        "e3_body_free_receipt_sha256": e3_receipt_sha256,
        "representative_fixture_sha256": _REPRESENTATIVE_FIXTURE_SHA256,
        "reviewed_case_ids": list(_REPRESENTATIVE_IDS),
        "product_read_completed": True,
        "decision": "proceed_to_frozen100",
        "formal_acceptance": "not_claimed",
    }
    return {
        "schema_version": (
            "cocolon.emlis.nls_v3.rc0028.e4_frozen100.body_free.v1"
        ),
        "body_free": True,
        "evaluation_stage": "E4_frozen100",
        "case_count": 100,
        "cases": cases,
        "disposition_counts": counts,
        "source_dependency_closure_sha256": downstream[
            "source_dependency_closure_sha256"
        ],
        "source_fixture_hashes": {
            "batch_manifest_sha256": _sha256(_BATCH_MANIFEST),
            "corpus_file_sha256": _sha256(_BATCH),
            "corpus_set_commitment": batch_manifest["corpus_set_commitment"],
            "coverage_matrix_sha256": _sha256(_COVERAGE),
            "duplicate_report_sha256": _sha256(_DUPLICATES),
            "rc0027_dependency_manifest_sha256": _sha256(_RC0027_MANIFEST),
        },
        "representative_fixture_sha256": _REPRESENTATIVE_FIXTURE_SHA256,
        "product_read_authorization_sha256": artifact_sha256(
            product_read_authorization
        ),
        "e3_body_free_receipt_sha256": e3_receipt_sha256,
        "product_read_status": "external_authorization_validated",
        "formal_acceptance": "not_claimed",
    }


def test_rc0028_e4_runner_requires_external_product_read_authorization(
    tmp_path: Path,
) -> None:
    runner = getattr(bounded, "run_rc0028_frozen100", None)
    assert callable(runner), "RC0028_E4_RUNNER_REQUIRED"
    parameters = inspect.signature(runner).parameters
    assert tuple(parameters) == (
        "output_directory",
        "product_read_receipt_path",
    )
    product_parameter = parameters["product_read_receipt_path"]
    assert product_parameter.kind is inspect.Parameter.KEYWORD_ONLY
    assert product_parameter.default is inspect.Parameter.empty

    output_directory = tmp_path / "private"
    output_directory.mkdir(mode=0o700)
    missing_receipt = tmp_path / "missing-product-read-receipt.json"
    with pytest.raises(bounded.BoundedExperimentStop) as captured:
        runner(
            output_directory,
            product_read_receipt_path=missing_receipt,
        )
    assert captured.value.code == (
        "RC0028_E3_PRODUCT_READ_AUTHORIZATION_REJECTED"
    )
    assert tuple(output_directory.iterdir()) == ()


def test_rc0028_e4_viability_requires_100_accounted_and_selected_above_56() -> None:
    validate_receipt = getattr(
        bounded,
        "validate_rc0028_experiment_body_free_receipt",
        None,
    )
    validate_viability = getattr(
        bounded,
        "validate_rc0028_e4_viability",
        None,
    )
    assert callable(validate_receipt), "RC0028_BODY_FREE_VALIDATOR_REQUIRED"
    assert callable(validate_viability), "RC0028_E4_VIABILITY_VALIDATOR_REQUIRED"

    selected = {*_RC0027_SELECTED_56, _NEW_NON_REPRESENTATIVE_CASE}
    receipt = _e4_receipt(selected)
    assert receipt["disposition_counts"] == {
        "fail_close": 43,
        "no_valid_candidate": 0,
        "selected": 57,
    }
    assert validate_receipt(receipt, expected_stage="E4_frozen100") == ()
    assert validate_viability(receipt) == ()


@pytest.mark.parametrize(
    "selected_ids",
    (
        _RC0027_SELECTED_56 - {"nls3s_b001_0001"},
        _RC0027_SELECTED_56,
    ),
)
def test_rc0028_e4_rejects_old56_regression_or_no_net_new_selection(
    selected_ids: frozenset[str],
) -> None:
    validate_viability = getattr(
        bounded,
        "validate_rc0028_e4_viability",
        None,
    )
    assert callable(validate_viability), "RC0028_E4_VIABILITY_VALIDATOR_REQUIRED"
    assert validate_viability(_e4_receipt(selected_ids)) != ()


def test_rc0028_e4_new_selection_is_outside_representative_eight() -> None:
    selected = {*_RC0027_SELECTED_56, _NEW_NON_REPRESENTATIVE_CASE}
    new_selected = selected - _RC0027_SELECTED_56
    assert new_selected == {_NEW_NON_REPRESENTATIVE_CASE}
    assert not (new_selected & frozenset(_REPRESENTATIVE_IDS))
    validate_viability = getattr(
        bounded,
        "validate_rc0028_e4_viability",
        None,
    )
    assert callable(validate_viability), "RC0028_E4_VIABILITY_VALIDATOR_REQUIRED"
    assert validate_viability(_e4_receipt(selected)) == ()


def test_rc0028_e4_receipt_cannot_claim_formal_acceptance() -> None:
    validate_receipt = getattr(
        bounded,
        "validate_rc0028_experiment_body_free_receipt",
        None,
    )
    receipt = _e4_receipt({*_RC0027_SELECTED_56, _NEW_NON_REPRESENTATIVE_CASE})
    forged = deepcopy(receipt)
    forged["formal_acceptance"] = "accepted"
    assert callable(validate_receipt), "RC0028_BODY_FREE_VALIDATOR_REQUIRED"
    assert validate_receipt(forged, expected_stage="E4_frozen100") != ()

