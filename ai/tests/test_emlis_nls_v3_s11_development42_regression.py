# -*- coding: utf-8 -*-
from __future__ import annotations

"""Development42 applicability and regression evidence contracts for rc0022."""

import hashlib
from pathlib import Path
from types import SimpleNamespace

import pytest

import emlis_nls_v3_step11_regression as regression


_TOOL_PATH = Path(regression.__file__).resolve()
_CLOSURE = "a" * 64
_VALIDATOR_SHA = "b" * 64
_KEY = b"d" * 32


def _parents() -> tuple[dict[str, object], dict[str, object]]:
    summary = {
        "candidate_version_id": regression.STEP11_CANDIDATE_VERSION_ID,
        "source_dependency_closure_sha256": _CLOSURE,
        "source_closure_start_sha256": _CLOSURE,
        "source_closure_end_sha256": _CLOSURE,
        "source_closure_stable": True,
        "machine_status": "clean",
        "executed_case_count": 100,
        "all_expected_cases_executed": True,
        "commitment_policy_sha256": "c" * 64,
        "commitment_key_id": regression.commitment_key_id(_KEY),
        "case_rows": [
            {"status": "selected", "v1_fallback_used": False}
            for _ in range(100)
        ],
        "body_free": True,
    }
    dependency = {
        "candidate_version_id": regression.STEP11_CANDIDATE_VERSION_ID,
        "source_dependency_closure_sha256": _CLOSURE,
        "file_hashes": [
            {
                "path": "ai/tools/emlis_nls_v3_step11_regression.py",
                "sha256": hashlib.sha256(_TOOL_PATH.read_bytes()).hexdigest(),
            },
            {
                "path": (
                    "ai/services/ai_inference/"
                    "emlis_ai_step10_app_reachable_contract_v3.py"
                ),
                "sha256": _VALIDATOR_SHA,
            },
        ],
        "body_free": True,
    }
    return summary, dependency


@pytest.fixture
def development42_parents(monkeypatch):
    summary, dependency = _parents()
    monkeypatch.setattr(
        regression,
        "assert_current_step11_dependency_manifest",
        lambda value, *, before_manifest: _CLOSURE,
    )
    monkeypatch.setattr(
        regression,
        "validate_step11_batch_run_summary",
        lambda value, *, dependency_manifest: (),
    )
    monkeypatch.setattr(
        regression,
        "validate_step11_dependency_manifest",
        lambda value: (),
    )
    return summary, dependency


def test_development42_source_and_applicability_inventory_are_frozen() -> None:
    inventory = regression.build_development42_expected_applicability()

    assert regression.validate_development42_applicability_contract() == ()
    assert inventory["counts"] == {
        "app_reachable": 24,
        "expected_non_applicable": 18,
    }
    assert len(inventory["cases"]) == 42
    assert inventory["candidate_generation_control_allowed"] is False
    assert regression.artifact_sha256(inventory) == (
        regression.FROZEN_DEVELOPMENT42_EXPECTED_APPLICABILITY_SHA256
    )
    assert hashlib.sha256(
        regression.DEVELOPMENT_FIXTURE_PATH.read_bytes()
    ).hexdigest() == regression.FROZEN_DEVELOPMENT42_SOURCE_FILE_SHA256
    assert all(
        row["applicability_status"] == "app_reachable"
        or row["expected_issue_codes"]
        for row in inventory["cases"]
    )


def test_development42_uses_the_cohort_independent_legacy_adapter() -> None:
    valid = {
        "memo": "今日は少し進めた。",
        "memo_action": "",
        "emotions": ["喜び"],
        "category": ["生活"],
    }
    invalid = {**valid, "memo": "", "memo_action": ""}

    projected, issues = regression.project_legacy_regression_input(valid)
    invalid_projected, invalid_issues = (
        regression.project_legacy_regression_input(invalid)
    )

    assert issues == ()
    assert projected == {
        "thought_text": valid["memo"],
        "action_text": "",
        "emotions": [{"type": "喜び", "strength": "medium"}],
        "categories": ["生活"],
    }
    assert invalid_projected is not None
    assert invalid_issues == (
        "input:thought_action_both_empty_after_js_trim",
    )


def test_development42_full_run_builds_42_bound_results(
    monkeypatch,
    development42_parents,
) -> None:
    summary, dependency = development42_parents

    async def fake_v1(current_input, case_ref):
        return f"v1:{case_ref}"

    def fake_v3(current_input, **kwargs):
        body = (
            f"v3:{current_input['thought_text']}:{current_input['action_text']}"
        ).encode("utf-8")
        candidate = SimpleNamespace(candidate_id="candidate_1")
        gate = SimpleNamespace(
            candidate_id="candidate_1",
            hard_pass=True,
            failure_codes=(),
        )
        return SimpleNamespace(
            status="selected",
            final_utf8_bytes=body,
            selected_candidate=candidate,
            selection_result=SimpleNamespace(gate_results=(gate,)),
        )

    monkeypatch.setattr(regression, "_v1_body", fake_v1)
    monkeypatch.setattr(regression, "execute_step11_offline_v3", fake_v3)
    monkeypatch.setattr(
        regression,
        "validate_step11_runtime_execution",
        lambda execution: (),
    )

    private, receipt = regression.run_development42(
        final_batch_summary=summary,
        before_dependency_manifest={"candidate_version_id": "nls_v3_rc_0021"},
        dependency_manifest=dependency,
        commitment_key=_KEY,
        run_id="nls3run_0022c001dddddddd",
    )

    assert len(private["cases"]) == 42
    assert receipt["schema_version"] == (
        regression.STEP11_DEVELOPMENT42_RECEIPT_SCHEMA
    )
    assert receipt["regression_set"] == "V2_DEVELOPMENT_42"
    assert receipt["aggregate"] == {
        "case_count": 42,
        "pass_count": 42,
        "app_reachable_count": 24,
        "selected_count": 24,
        "expected_non_applicable_count": 18,
        "expected_non_applicable_match_count": 18,
        "hard_gate_pass_count": 24,
        "failure_count": 0,
        "exception_count": 0,
        "v1_fallback_count": 0,
    }
    assert receipt["formal_status"] == "clean"
    assert receipt["counts_toward_karen_minimum"] is False
    assert regression.validate_development42_receipt(
        receipt,
        final_batch_summary=summary,
        dependency_manifest=dependency,
    ) == ()
    assert regression.validate_development42_private_packet(
        private,
        receipt,
        commitment_key=_KEY,
    ) == ()


def test_development42_receipt_rejects_false_green_status(
    monkeypatch,
    development42_parents,
) -> None:
    summary, dependency = development42_parents
    inventory = regression.build_development42_expected_applicability()
    cases = {
        case.case_id: case for case in regression._load_frozen_development42_cases()
    }
    rows = []
    for expected in inventory["cases"]:
        applicable = expected["applicability_status"] == "app_reachable"
        rows.append(
            {
                "case_ref": expected["case_ref"],
                "family": cases[expected["case_ref"]].family,
                "legacy_input_commitment": "1" * 64,
                "projected_input_commitment": "2" * 64 if applicable else None,
                "applicability_binding_commitment": "3" * 64,
                "applicability_status": expected["applicability_status"],
                "applicability_issue_codes": expected["expected_issue_codes"],
                "v1_baseline_body_commitment": "4" * 64,
                "selected_candidate_body_commitment": (
                    "5" * 64 if applicable else None
                ),
                "status": "selected" if applicable else "expected_non_applicable",
                "hard_gate_status": "passed" if applicable else "not_applicable",
                "failure_codes": [],
                "exception": False,
                "v1_fallback_used": False,
            }
        )

    nonapp = next(
        row for row in rows if row["status"] == "expected_non_applicable"
    )
    nonapp["status"] = "selected"
    nonapp["hard_gate_status"] = "passed"
    nonapp["projected_input_commitment"] = "2" * 64
    nonapp["selected_candidate_body_commitment"] = "5" * 64

    with pytest.raises(ValueError, match="nonapp_row_invalid"):
        regression.build_development42_receipt(
            rows,
            final_batch_summary=summary,
            dependency_manifest=dependency,
            run_id="nls3run_0022c001dddddddd",
            private_packet_commitment="6" * 64,
            verifier_sha256=hashlib.sha256(_TOOL_PATH.read_bytes()).hexdigest(),
            verified_case_count=42,
        )
