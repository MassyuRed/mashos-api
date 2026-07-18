# -*- coding: utf-8 -*-
from __future__ import annotations

"""Frozen rc0026 public evidence contract.

rc0026 is historical once production advances to rc0027.  This module must
therefore validate the body-free public snapshot, not replay the historical
Surface grammar through the current renderer, matcher, or Hard Gate.
"""

from copy import deepcopy
import json
from pathlib import Path
from typing import Any, Mapping

from emlis_ai_nls_v3_artifact_contract import artifact_sha256
from emlis_ai_step10_evidence_v3 import assert_body_free
from emlis_ai_step11_cycle_evidence_v3 import (
    FROZEN_RC0026_DEVELOPMENT42_RECEIPT_SHA256,
    FROZEN_RC0026_FORMAL_BATCH_SUMMARY_SHA256,
    FROZEN_RC0026_FORMAL_MANIFEST_ARTIFACT_SHA256,
    FROZEN_RC0026_FORMAL_PRIVATE_VERIFICATION_SHA256,
    FROZEN_RC0026_FORMAL_SOURCE_CLOSURE_SHA256,
    FROZEN_RC0026_INVALID16_RECEIPT_SHA256,
    FROZEN_RC0026_KNOWN28_RECEIPT_SHA256,
    FROZEN_RC0026_PRODUCT_READ_FAILURE_AXES,
    FROZEN_RC0026_PRODUCT_READ_FAILURE_REASONS,
    FROZEN_RC0026_PRODUCT_READ_FAILURE_SHA256,
    validate_invalid16_receipt,
    validate_known28_receipt,
    validate_step11_batch_run_summary,
    validate_step11_dependency_manifest,
    validate_step11_private_verification_receipt,
)


_HERE = Path(__file__).resolve().parent
_CYCLE = _HERE / "fixtures" / "emlis_nls_v3" / "cycle_001"
_RC0026 = "nls_v3_rc_0026"
_RC0025 = "nls_v3_rc_0025"

_ARTIFACT_NAMES = (
    "cycle001_dependency_manifest_rc0026.json",
    "cycle001_final_rc0026_summary.json",
    "cycle001_final_rc0026_private_verification.json",
    "cycle001_known28_rc0026.json",
    "cycle001_development42_rc0026.json",
    "cycle001_invalid16_rc0026.json",
    "cycle001_product_read_failure_rc0026.json",
)

_FROZEN_OWNER_HASHES = {
    "ai/services/ai_inference/emlis_ai_step11_surface_catalog_v3.py": (
        "eb0c1032f04340dce8d84aa9d51d28df7d7d928d8cb04dcb01f8dab28b96566d"
    ),
    "ai/services/ai_inference/emlis_ai_step11_natural_surface_v3.py": (
        "740f14a117d7bb3e62d8e8b28f55a899fafaa7df985e73ebf293fbc351174495"
    ),
    "ai/services/ai_inference/emlis_ai_step11_natural_surface_matcher_v3.py": (
        "d8026d1b43bacb06dcb12e972771cf62e148c103e58a1d2de8729f16162321b8"
    ),
    "ai/services/ai_inference/emlis_ai_step11_hard_gate_v3.py": (
        "595a8c5af60eb6209c7deffb342691fd2c6bbab00f7a758f506d235dadd0cb5c"
    ),
    "ai/tests/test_emlis_nls_v3_s11_rc0026_product_read_surface_red.py": (
        "0820ee4d06a70e82abc7bd6d23a7659a5d014c97d2a28b28070f9d317e8cff08"
    ),
}

_FORBIDDEN_PUBLIC_KEYS = {
    "action_text",
    "body",
    "current_input",
    "emotions",
    "final_utf8_bytes",
    "rendered_surface",
    "thought_text",
    "utf8_bytes",
    "v1_body",
    "v3_body",
}


def _json(name: str) -> dict[str, Any]:
    value = json.loads((_CYCLE / name).read_text(encoding="utf-8"))
    assert type(value) is dict
    return value


def _artifacts() -> dict[str, dict[str, Any]]:
    return {name: _json(name) for name in _ARTIFACT_NAMES}


def _development42_aggregate(rows: list[Mapping[str, Any]]) -> dict[str, int]:
    selected_count = sum(row["status"] == "selected" for row in rows)
    nonapp_count = sum(
        row["status"] == "expected_non_applicable" for row in rows
    )
    return {
        "case_count": len(rows),
        "pass_count": selected_count + nonapp_count,
        "app_reachable_count": sum(
            row["applicability_status"] == "app_reachable" for row in rows
        ),
        "selected_count": selected_count,
        "expected_non_applicable_count": sum(
            row["applicability_status"] == "expected_non_applicable"
            for row in rows
        ),
        "expected_non_applicable_match_count": nonapp_count,
        "hard_gate_pass_count": sum(
            row["hard_gate_status"] == "passed" for row in rows
        ),
        "failure_count": sum(bool(row["failure_codes"]) for row in rows),
        "exception_count": sum(row["exception"] is True for row in rows),
        "v1_fallback_count": sum(
            row["v1_fallback_used"] is True for row in rows
        ),
    }


def _product_read_binding_issues(
    failure: Mapping[str, Any],
    *,
    summary: Mapping[str, Any],
    private_verification: Mapping[str, Any],
    known28: Mapping[str, Any],
    development42: Mapping[str, Any],
    invalid16: Mapping[str, Any],
) -> tuple[str, ...]:
    expected = {
        "batch_summary_sha256": artifact_sha256(summary),
        "private_verification_receipt_sha256": artifact_sha256(
            private_verification
        ),
        "known28_receipt_sha256": artifact_sha256(known28),
        "development42_receipt_sha256": artifact_sha256(development42),
        "invalid16_receipt_sha256": artifact_sha256(invalid16),
    }
    return tuple(
        key for key, sha256 in expected.items() if failure.get(key) != sha256
    )


def test_rc0026_manifest_is_exact_append_only_snapshot() -> None:
    manifest = _json("cycle001_dependency_manifest_rc0026.json")

    assert validate_step11_dependency_manifest(manifest) == ()
    assert artifact_sha256(manifest) == (
        FROZEN_RC0026_FORMAL_MANIFEST_ARTIFACT_SHA256
    )
    assert manifest["candidate_version_id"] == _RC0026
    assert manifest["before_candidate_version_id"] == _RC0025
    assert manifest["source_dependency_closure_sha256"] == (
        FROZEN_RC0026_FORMAL_SOURCE_CLOSURE_SHA256
    )
    assert len(manifest["file_hashes"]) == 156
    assert len(manifest["changed_file_hashes"]) == 27

    file_paths = [row["path"] for row in manifest["file_hashes"]]
    changed_paths = [row["path"] for row in manifest["changed_file_hashes"]]
    assert file_paths == sorted(set(file_paths))
    assert changed_paths == sorted(set(changed_paths))
    assert set(changed_paths) <= set(file_paths)

    by_path = {row["path"]: row["sha256"] for row in manifest["file_hashes"]}
    assert {path: by_path[path] for path in _FROZEN_OWNER_HASHES} == (
        _FROZEN_OWNER_HASHES
    )


def test_rc0026_formal100_is_exact_machine_clean_snapshot() -> None:
    manifest = _json("cycle001_dependency_manifest_rc0026.json")
    summary = _json("cycle001_final_rc0026_summary.json")

    assert validate_step11_batch_run_summary(
        summary, dependency_manifest=manifest
    ) == ()
    assert artifact_sha256(summary) == FROZEN_RC0026_FORMAL_BATCH_SUMMARY_SHA256
    assert summary["candidate_version_id"] == _RC0026
    assert summary["dependency_manifest_sha256"] == artifact_sha256(manifest)
    closure = FROZEN_RC0026_FORMAL_SOURCE_CLOSURE_SHA256
    assert summary["source_dependency_closure_sha256"] == closure
    assert summary["source_closure_start_sha256"] == closure
    assert summary["source_closure_end_sha256"] == closure
    assert summary["source_closure_stable"] is True
    assert summary["all_expected_cases_executed"] is True
    assert summary["executed_case_count"] == 100
    assert summary["machine_status"] == "clean"
    assert summary["body_free"] is True

    aggregate = summary["aggregate"]
    assert aggregate["case_count"] == 100
    assert aggregate["selected_count"] == 100
    assert aggregate["hard_gate_pass_count"] == 100
    assert aggregate["app_reachable_pass_count"] == 100
    assert aggregate["exception_count"] == 0
    assert aggregate["no_valid_candidate_count"] == 0
    assert aggregate["v1_fallback_count"] == 0
    assert aggregate["output_duplicate_case_count"] == 0
    assert aggregate["output_duplicate_cluster_count"] == 0
    assert aggregate["literal_replay_count_total"] == 0


def test_rc0026_private_verification_public_receipt_is_bound() -> None:
    manifest = _json("cycle001_dependency_manifest_rc0026.json")
    summary = _json("cycle001_final_rc0026_summary.json")
    receipt = _json("cycle001_final_rc0026_private_verification.json")

    assert validate_step11_private_verification_receipt(
        receipt,
        final_batch_summary=summary,
        final_dependency_manifest=manifest,
    ) == ()
    assert artifact_sha256(receipt) == (
        FROZEN_RC0026_FORMAL_PRIVATE_VERIFICATION_SHA256
    )
    assert receipt["candidate_version_id"] == _RC0026
    assert receipt["run_id"] == summary["run_id"]
    assert receipt["dependency_manifest_sha256"] == artifact_sha256(manifest)
    assert receipt["final_batch_summary_sha256"] == artifact_sha256(summary)
    assert receipt["source_dependency_closure_sha256"] == (
        manifest["source_dependency_closure_sha256"]
    )
    assert receipt["commitment_key_id"] == summary["commitment_key_id"]
    assert receipt["commitment_policy_sha256"] == (
        summary["commitment_policy_sha256"]
    )
    assert receipt["verified_case_count"] == 100
    assert receipt["verified_selected_count"] == 100
    assert receipt["verified_exception_count"] == 0
    assert receipt["verified_no_valid_candidate_count"] == 0
    assert receipt["private_packet_validation_status"] == "clean"
    assert receipt["body_free"] is True


def test_rc0026_regression_receipts_are_exact_clean_and_non_counting() -> None:
    manifest = _json("cycle001_dependency_manifest_rc0026.json")
    summary = _json("cycle001_final_rc0026_summary.json")
    known28 = _json("cycle001_known28_rc0026.json")
    development42 = _json("cycle001_development42_rc0026.json")
    invalid16 = _json("cycle001_invalid16_rc0026.json")

    assert validate_known28_receipt(
        known28,
        final_batch_summary=summary,
        final_dependency_manifest=manifest,
    ) == ()
    assert validate_invalid16_receipt(
        invalid16,
        final_batch_summary=summary,
        final_dependency_manifest=manifest,
    ) == ()
    assert artifact_sha256(known28) == FROZEN_RC0026_KNOWN28_RECEIPT_SHA256
    assert artifact_sha256(development42) == (
        FROZEN_RC0026_DEVELOPMENT42_RECEIPT_SHA256
    )
    assert artifact_sha256(invalid16) == FROZEN_RC0026_INVALID16_RECEIPT_SHA256

    receipts = (known28, development42, invalid16)
    for receipt in receipts:
        assert receipt["candidate_version_id"] == _RC0026
        assert receipt["final_batch_summary_sha256"] == artifact_sha256(summary)
        assert receipt["source_dependency_closure_sha256"] == (
            manifest["source_dependency_closure_sha256"]
        )
        assert receipt["formal_status"] == "clean"
        assert receipt["counts_toward_karen_minimum"] is False
        assert receipt["body_free"] is True
    assert len({summary["run_id"], *(row["run_id"] for row in receipts)}) == 4

    assert known28["aggregate"] == {
        "case_count": 28,
        "app_reachable_count": 19,
        "expected_non_applicable_count": 9,
        "selected_count": 19,
        "hard_gate_pass_count": 19,
        "expected_non_applicable_match_count": 9,
        "contract_pass_count": 28,
        "exception_count": 0,
        "v1_fallback_count": 0,
        "failure_case_count": 0,
    }
    assert development42["aggregate"] == _development42_aggregate(
        development42["rows"]
    )
    assert development42["aggregate"] == {
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
    assert invalid16["aggregate"] == {
        "case_count": 16,
        "rejected_count": 16,
        "expected_rejection_match_count": 16,
        "under_rejected_count": 0,
    }


def test_rc0026_product_read_failure_overrides_machine_green() -> None:
    artifacts = _artifacts()
    summary = artifacts["cycle001_final_rc0026_summary.json"]
    failure = artifacts["cycle001_product_read_failure_rc0026.json"]

    assert summary["machine_status"] == "clean"
    assert artifact_sha256(failure) == FROZEN_RC0026_PRODUCT_READ_FAILURE_SHA256
    assert failure["schema_version"] == (
        "cocolon.emlis.nls_v3.product_read_failure.step11.rc0026.v1"
    )
    assert failure["candidate_version_id"] == _RC0026
    assert _product_read_binding_issues(
        failure,
        summary=summary,
        private_verification=artifacts[
            "cycle001_final_rc0026_private_verification.json"
        ],
        known28=artifacts["cycle001_known28_rc0026.json"],
        development42=artifacts["cycle001_development42_rc0026.json"],
        invalid16=artifacts["cycle001_invalid16_rc0026.json"],
    ) == ()
    assert failure["review_outcome"] == "failed"
    assert failure["maximum_severity"] == "MAJOR"
    assert tuple(failure["failure_axis_codes"]) == (
        FROZEN_RC0026_PRODUCT_READ_FAILURE_AXES
    )
    assert tuple(failure["failure_reason_codes"]) == (
        FROZEN_RC0026_PRODUCT_READ_FAILURE_REASONS
    )
    assert failure["body_free"] is True


def test_rc0026_public_snapshot_is_body_free() -> None:
    for value in _artifacts().values():
        assert_body_free(value)
        stack: list[Any] = [value]
        while stack:
            current = stack.pop()
            if type(current) is dict:
                assert not (_FORBIDDEN_PUBLIC_KEYS & set(current))
                stack.extend(current.values())
            elif type(current) is list:
                stack.extend(current)


def test_rc0026_public_snapshot_rejects_tampering() -> None:
    artifacts = _artifacts()
    manifest = artifacts["cycle001_dependency_manifest_rc0026.json"]
    summary = artifacts["cycle001_final_rc0026_summary.json"]
    private_receipt = artifacts[
        "cycle001_final_rc0026_private_verification.json"
    ]
    known28 = artifacts["cycle001_known28_rc0026.json"]
    development42 = artifacts["cycle001_development42_rc0026.json"]
    invalid16 = artifacts["cycle001_invalid16_rc0026.json"]
    failure = artifacts["cycle001_product_read_failure_rc0026.json"]

    forged_manifest = deepcopy(manifest)
    forged_manifest["file_hashes"][0]["sha256"] = "f" * 64
    assert validate_step11_dependency_manifest(forged_manifest) != ()

    forged_summary = deepcopy(summary)
    forged_summary["aggregate"]["selected_count"] = 99
    assert validate_step11_batch_run_summary(
        forged_summary, dependency_manifest=manifest
    ) != ()

    forged_private = deepcopy(private_receipt)
    forged_private["verified_selected_count"] = 99
    assert validate_step11_private_verification_receipt(
        forged_private,
        final_batch_summary=summary,
        final_dependency_manifest=manifest,
    ) != ()

    forged_known28 = deepcopy(known28)
    forged_known28["rows"][0]["hard_gate_status"] = "not_applicable"
    assert validate_known28_receipt(
        forged_known28,
        final_batch_summary=summary,
        final_dependency_manifest=manifest,
    ) != ()

    forged_invalid16 = deepcopy(invalid16)
    forged_invalid16["rows"][0]["actual_issue_codes"] = []
    assert validate_invalid16_receipt(
        forged_invalid16,
        final_batch_summary=summary,
        final_dependency_manifest=manifest,
    ) != ()

    forged_development42 = deepcopy(development42)
    forged_development42["rows"][0]["status"] = "expected_non_applicable"
    assert forged_development42["aggregate"] != _development42_aggregate(
        forged_development42["rows"]
    )
    assert artifact_sha256(forged_development42) != (
        FROZEN_RC0026_DEVELOPMENT42_RECEIPT_SHA256
    )

    forged_failure = deepcopy(failure)
    forged_failure["known28_receipt_sha256"] = "f" * 64
    assert artifact_sha256(forged_failure) != (
        FROZEN_RC0026_PRODUCT_READ_FAILURE_SHA256
    )
    assert _product_read_binding_issues(
        forged_failure,
        summary=summary,
        private_verification=private_receipt,
        known28=known28,
        development42=development42,
        invalid16=invalid16,
    ) == ("known28_receipt_sha256",)
