# -*- coding: utf-8 -*-
from __future__ import annotations

"""E3 machine gate for the frozen rc0030 representative eight.

The bounded runner may emit body-bearing Product Read inputs only into an
external caller-owned private directory.  This suite evaluates the machine
gate and its body-free receipt; it deliberately does not claim or automate the
human Product Read decision required before E4.
"""

from copy import deepcopy
import hashlib
import json
import os
from pathlib import Path
import stat
from typing import Any

import pytest

import emlis_ai_rc0030_surface_planning_experiment_dependency_manifest_v3 as dependency
import emlis_nls_v3_rc0030_surface_planning_bounded_experiment as bounded


_TEST_ROOT = Path(__file__).resolve().parent
_REPO_ROOT = _TEST_ROOT.parents[1]
_CYCLE_ROOT = _TEST_ROOT / "fixtures" / "emlis_nls_v3" / "cycle_001"
_GENERATED_ROOT = _TEST_ROOT / "fixtures" / "emlis_nls_v3" / "generated"
_REPRESENTATIVE = _CYCLE_ROOT / "rc0030_representative8_body_free.json"
_PHASE_MANIFEST = _CYCLE_ROOT / (
    "cycle001_dependency_manifest_rc0030_surface_planning_experiment.json"
)
_BATCH = _GENERATED_ROOT / "batch_001.jsonl"
_BATCH_MANIFEST = _GENERATED_ROOT / "batch_001_manifest.json"
_COVERAGE = _GENERATED_ROOT / "batch_001_coverage_matrix.json"
_DUPLICATES = _GENERATED_ROOT / "batch_001_duplicate_report.json"
_PRIVATE_FILENAME = "rc0030_e3_representative8_private.json"
_BODY_FREE_FILENAME = "rc0030_e3_representative8_body_free_receipt.json"
_REPRESENTATIVE_SHA256 = (
    "9cfbdafaf43a3caed8b5dc00e68b56cd2b24003a002f0a7cbd1c3ec06d598fa5"
)
_E3_PREDECESSOR = "38ca7fa779065998a363ce9bb581338d98b8f79d"
_EXPECTED_ROWS = (
    ("nls3s_b001_0001", "control", "PASS", ("PASS",)),
    ("nls3s_b001_0002", "control", "PASS", ("PASS",)),
    ("nls3s_b001_0009", "control", "MINOR", ("PASS", "MINOR")),
    ("nls3s_b001_0019", "improvement_target", "MAJOR", ("PASS", "MINOR")),
    ("nls3s_b001_0035", "improvement_target", "MAJOR", ("PASS", "MINOR")),
    ("nls3s_b001_0043", "improvement_target", "MAJOR", ("PASS", "MINOR")),
    ("nls3s_b001_0063", "improvement_target", "MAJOR", ("PASS", "MINOR")),
    ("nls3s_b001_0100", "improvement_target", "MAJOR", ("PASS", "MINOR")),
)
_CASE_IDS = tuple(row[0] for row in _EXPECTED_ROWS)
_CONTROL_IDS = frozenset(row[0] for row in _EXPECTED_ROWS if row[1] == "control")
_FORMER_MAJOR_IDS = frozenset(
    row[0] for row in _EXPECTED_ROWS if row[2] == "MAJOR"
)
_ALLOWED_DISPOSITIONS = frozenset(
    {"selected", "no_valid_candidate", "fail_close"}
)
_FORBIDDEN_BODY_KEYS = frozenset(
    {
        "action_text",
        "base_body",
        "body",
        "current_input",
        "final_utf8_bytes",
        "input",
        "normalized_input",
        "output",
        "owner_expressions",
        "parsed_witness",
        "product_read_input",
        "raw_text",
        "rendered_surface",
        "runtime_execution",
        "selected_final_utf8_bytes",
        "selected_final_utf8_text",
        "source_input",
        "source_fragment",
        "supporting_expression",
        "surface_text",
        "target_expression",
        "thought_text",
        "unsalted_body_digest",
        "utf8_bytes",
    }
)


def _load(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text(encoding="utf-8"))
    assert type(value) is dict
    return value


def _sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def _sha256(path: Path) -> str:
    return _sha256_bytes(path.read_bytes())


def _valid_nonzero_sha256(value: Any) -> bool:
    return (
        type(value) is str
        and len(value) == 64
        and value != "0" * 64
        and all(character in "0123456789abcdef" for character in value)
    )


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


def _canonical_json_bytes(value: Any) -> bytes:
    return json.dumps(
        value,
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
        allow_nan=False,
    ).encode("utf-8", errors="strict") + b"\n"


@pytest.fixture(scope="module")
def authority() -> tuple[dict[str, Any], dict[str, Any]]:
    representative = _load(_REPRESENTATIVE)
    phase_manifest = _load(_PHASE_MANIFEST)
    assert _sha256(_REPRESENTATIVE) == _REPRESENTATIVE_SHA256
    assert representative["body_free"] is True
    assert representative["representative_count"] == 8
    assert tuple(
        (
            row["case_id"],
            row["experiment_role"],
            row["baseline_product_read_severity"],
            tuple(row["rc0030_required_product_read_severity"]),
        )
        for row in representative["rows"]
    ) == _EXPECTED_ROWS
    return representative, phase_manifest


@pytest.fixture(scope="module")
def machine_artifacts(
    tmp_path_factory: pytest.TempPathFactory,
) -> tuple[Path, bytes, dict[str, Any], bytes, dict[str, Any]]:
    output_directory = tmp_path_factory.mktemp("rc0030-e3-private")
    output_directory.chmod(0o700)
    assert output_directory.is_absolute()
    assert output_directory != _REPO_ROOT
    assert _REPO_ROOT not in output_directory.parents

    bounded.run_rc0030_representative8(output_directory)
    private_path = output_directory / _PRIVATE_FILENAME
    body_free_path = output_directory / _BODY_FREE_FILENAME
    private_bytes = private_path.read_bytes()
    body_free_bytes = body_free_path.read_bytes()
    private = json.loads(private_bytes)
    body_free = json.loads(body_free_bytes)
    assert type(private) is dict and type(body_free) is dict
    return output_directory, private_bytes, private, body_free_bytes, body_free


def test_rc0030_e3_authority_is_exact_controls_plus_former_major_five(
    authority: tuple[dict[str, Any], dict[str, Any]],
) -> None:
    representative, phase_manifest = authority
    assert _CONTROL_IDS == {
        "nls3s_b001_0001",
        "nls3s_b001_0002",
        "nls3s_b001_0009",
    }
    assert _FORMER_MAJOR_IDS == {
        "nls3s_b001_0019",
        "nls3s_b001_0035",
        "nls3s_b001_0043",
        "nls3s_b001_0063",
        "nls3s_b001_0100",
    }
    assert tuple(row["case_id"] for row in representative["rows"]) == _CASE_IDS
    assert dependency.RC0030_MANIFEST_PHASE == "E3_MACHINE_AND_PRODUCT_READ"
    assert dependency.RC0030_E3_PHASE_PREDECESSOR_GIT_COMMIT == _E3_PREDECESSOR
    assert phase_manifest["phase_predecessor_git_commit"] == _E3_PREDECESSOR
    assert phase_manifest["manifest_phase"] == "E3_MACHINE_AND_PRODUCT_READ"
    assert phase_manifest["activation_policy"]["newly_active_paths"] == sorted(
        dependency.RC0030_E3_NEWLY_ACTIVE_PATHS
    )
    assert phase_manifest["activation_policy"]["reserved_absent_paths"] == [
        "ai/tests/test_emlis_nls_v3_s11_rc0030_e4_frozen100_read_only.py"
    ]


def test_rc0030_e3_runner_emits_one_external_private_pair(
    machine_artifacts: tuple[
        Path, bytes, dict[str, Any], bytes, dict[str, Any]
    ],
) -> None:
    output_directory, private_bytes, private, body_free_bytes, body_free = (
        machine_artifacts
    )
    assert {path.name for path in output_directory.iterdir()} == {
        _PRIVATE_FILENAME,
        _BODY_FREE_FILENAME,
    }
    assert stat.S_IMODE(output_directory.stat().st_mode) == 0o700
    assert all(
        stat.S_IMODE((output_directory / name).stat().st_mode) == 0o600
        for name in (_PRIVATE_FILENAME, _BODY_FREE_FILENAME)
    )
    assert private_bytes == _canonical_json_bytes(private)
    assert body_free_bytes == _canonical_json_bytes(body_free)
    assert private["body_free_receipt_sha256"] == _sha256_bytes(body_free_bytes)
    assert private["private_body_full"] is True
    assert private["experimental_only"] is True
    assert private["runtime_connected"] is False
    assert private["shareable"] is False
    assert private["product_read_judgement"] == "not_performed_by_tool"
    assert body_free["body_free"] is True
    assert body_free["experimental_only"] is True
    assert body_free["runtime_connected"] is False
    assert body_free["formal_acceptance"] == "not_claimed"
    assert body_free["product_read_status"] == "input_ready_not_reviewed"
    assert bounded.validate_rc0030_experiment_body_free_receipt(body_free) == ()


def test_rc0030_e3_machine_selects_and_exactly_accounts_for_all_eight(
    machine_artifacts: tuple[
        Path, bytes, dict[str, Any], bytes, dict[str, Any]
    ],
) -> None:
    _directory, _private_bytes, _private, _body_free_bytes, receipt = (
        machine_artifacts
    )
    rows = receipt["cases"]
    assert receipt["case_count"] == len(rows) == 8
    assert tuple(row["case_id"] for row in rows) == _CASE_IDS
    assert receipt["disposition_counts"] == {
        "fail_close": 0,
        "no_valid_candidate": 0,
        "selected": 8,
    }
    assert sum(receipt["disposition_counts"].values()) == 8
    assert all(
        row["disposition"] == "selected" and row["closed_codes"] == []
        for row in rows
    )
    assert {row["case_id"] for row in rows if row["disposition"] == "selected"} == (
        _CONTROL_IDS | _FORMER_MAJOR_IDS
    )


def test_rc0030_e3_parser_matcher_gate_and_resource_accounting_is_exact(
    machine_artifacts: tuple[
        Path, bytes, dict[str, Any], bytes, dict[str, Any]
    ],
) -> None:
    _directory, _private_bytes, _private, _body_free_bytes, receipt = (
        machine_artifacts
    )
    assert receipt["resource_bounds"] == {
        "body_byte_inspections_max": 48_000_000,
        "candidate_limit_max": 12,
        "matcher_invocations_max": 24,
        "parser_invocations_max": 24,
        "replan_limit_max": 1,
    }
    for row in receipt["cases"]:
        counts = row["counts"]
        assert counts["replan_count"] == 0
        assert counts["base_body_parse_count"] == counts["base_reuse_match_count"]
        assert counts["base_body_parse_count"] == counts["base_inverse_prepass_count"]
        assert counts["final_body_parse_count"] == counts["final_surface_match_count"]
        assert counts["final_body_parse_count"] == counts["evaluated_candidate_count"]
        assert counts["hard_gate_pass_count"] >= 1
        assert counts["hard_gate_pass_count"] + counts["rejected_candidate_count"] == (
            counts["evaluated_candidate_count"]
        )
        assert 1 <= counts["experiment_candidate_count"] <= 12
        assert 1 <= counts["evaluated_candidate_count"] <= 12
        assert counts["base_body_parse_count"] + counts["final_body_parse_count"] <= 24
        assert counts["base_reuse_match_count"] + counts["final_surface_match_count"] <= 24
        assert 0 < counts["body_byte_inspection_count"] <= 48_000_000
        assert row["selected_candidate_present"] is True
        assert row["body_free"] is True
        assert row["experimental_only"] is True
        assert row["runtime_connected"] is False
        assert row["semantic_coverage_authority"] == "none"
        assert all(
            _valid_nonzero_sha256(row["hashes"].get(key))
            for key in (
                "base_inverse_contexts_sha256",
                "lexical_atom_specs_sha256",
                "result_sha256",
                "source_case_commitment",
                "successor_authority_sha256",
                "successor_snapshot_sha256",
                "successor_witness_sha256",
                "surface_catalog_sha256",
            )
        )


def test_rc0030_e3_receipt_is_body_free_disconnected_and_source_bound(
    authority: tuple[dict[str, Any], dict[str, Any]],
    machine_artifacts: tuple[
        Path, bytes, dict[str, Any], bytes, dict[str, Any]
    ],
) -> None:
    _representative, phase_manifest = authority
    _directory, _private_bytes, _private, body_free_bytes, receipt = (
        machine_artifacts
    )
    assert not (_all_mapping_keys(receipt) & _FORBIDDEN_BODY_KEYS)
    assert receipt["source_dependency_closure_sha256"] == (
        phase_manifest["source_dependency_closure_sha256"]
    )
    source_hashes = receipt["source_fixture_hashes"]
    assert receipt["representative_fixture_sha256"] == _sha256(_REPRESENTATIVE)
    assert receipt["source_dependency_manifest_sha256"] == _sha256(
        _PHASE_MANIFEST
    )
    assert source_hashes["batch_manifest_sha256"] == _sha256(_BATCH_MANIFEST)
    assert source_hashes["corpus_file_sha256"] == _sha256(_BATCH)
    assert source_hashes["coverage_matrix_sha256"] == _sha256(_COVERAGE)
    assert source_hashes["duplicate_report_sha256"] == _sha256(_DUPLICATES)
    serialized = body_free_bytes.decode("utf-8")
    samples = {
        row["case_id"]: row["input"]
        for line in _BATCH.read_text(encoding="utf-8").splitlines()
        if line
        for row in (json.loads(line),)
        if row.get("case_id") in _CASE_IDS
    }
    assert set(samples) == set(_CASE_IDS)
    assert all(
        json.dumps(value, ensure_ascii=False, sort_keys=True) not in serialized
        for value in samples.values()
    )


def test_rc0030_e3_private_inputs_are_complete_but_do_not_claim_review(
    machine_artifacts: tuple[
        Path, bytes, dict[str, Any], bytes, dict[str, Any]
    ],
) -> None:
    _directory, _private_bytes, private, _body_free_bytes, receipt = (
        machine_artifacts
    )
    assert private["case_count"] == 8
    assert tuple(row["case_id"] for row in private["cases"]) == _CASE_IDS
    assert private["formal_acceptance"] == "not_claimed"
    assert private["product_read_judgement"] == "not_performed_by_tool"
    assert all(
        row["product_read_input"]["status"] == "ready"
        and row["runtime_error_code"] is None
        and row["runtime_body_free_result"] is not None
        and row["product_read_input"]["source_input"]
        and row["product_read_input"]["selected_final_utf8_text"]
        and _valid_nonzero_sha256(
            row["product_read_input"]["selected_final_utf8_sha256"]
        )
        for row in private["cases"]
    )
    assert not (_all_mapping_keys(receipt) & {"product_read_judgement", "hex"})


@pytest.mark.parametrize(
    "mutation",
    (
        "duplicate_case",
        "false_accounting",
        "resource_overrun",
        "runtime_connected",
        "body_injection",
        "premature_acceptance",
    ),
)
def test_rc0030_e3_receipt_mutations_fail_closed(
    mutation: str,
    machine_artifacts: tuple[
        Path, bytes, dict[str, Any], bytes, dict[str, Any]
    ],
) -> None:
    _directory, _private_bytes, _private, _body_free_bytes, receipt = (
        machine_artifacts
    )
    forged = deepcopy(receipt)
    if mutation == "duplicate_case":
        forged["cases"][1]["case_id"] = forged["cases"][0]["case_id"]
    elif mutation == "false_accounting":
        forged["disposition_counts"]["selected"] = 7
        forged["disposition_counts"]["fail_close"] = 1
    elif mutation == "resource_overrun":
        forged["cases"][0]["counts"]["body_byte_inspection_count"] = 48_000_001
    elif mutation == "runtime_connected":
        forged["cases"][0]["runtime_connected"] = True
    elif mutation == "body_injection":
        forged["cases"][0]["body"] = "forbidden"
    elif mutation == "premature_acceptance":
        forged["formal_acceptance"] = "accepted"
    assert bounded.validate_rc0030_experiment_body_free_receipt(forged) != ()


def test_rc0030_e3_runner_filesystem_misuse_fails_before_execution(
    tmp_path: Path,
) -> None:
    with pytest.raises(bounded.BoundedExperimentStop) as repository:
        bounded.run_rc0030_representative8(_REPO_ROOT)
    assert repository.value.code == "RC0030_PRIVATE_DIRECTORY_PREFLIGHT_REJECTED"

    output_directory = tmp_path / "private"
    output_directory.mkdir(mode=0o700)
    (output_directory / _PRIVATE_FILENAME).write_text("occupied", encoding="utf-8")
    os.chmod(output_directory / _PRIVATE_FILENAME, 0o600)
    with pytest.raises(bounded.BoundedExperimentStop) as occupied:
        bounded.run_rc0030_representative8(output_directory)
    assert occupied.value.code == "RC0030_PRIVATE_OUTPUT_ALREADY_EXISTS"
    assert tuple(path.name for path in output_directory.iterdir()) == (
        _PRIVATE_FILENAME,
    )
