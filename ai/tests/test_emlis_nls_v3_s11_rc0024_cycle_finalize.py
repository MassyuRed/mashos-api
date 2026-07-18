# -*- coding: utf-8 -*-
from __future__ import annotations

"""rc0024 finalizer boundary and exact clean-rc0023 parent REDs."""

from copy import deepcopy
import inspect
import json
from pathlib import Path
from typing import Any

import pytest

from emlis_ai_nls_v3_artifact_contract import artifact_sha256
from emlis_ai_step11_cycle_evidence_v3 import build_step11_dependency_manifest
import emlis_ai_step11_cycle_evidence_v3 as cycle_evidence
import emlis_nls_v3_step11_cycle_finalize as finalizer
from test_emlis_nls_v3_s11_rc0021_append_only_lineage import (
    _commitment,
    _summary,
)
from test_emlis_nls_v3_s11_rc0022_cycle_finalize import (
    _rc0021_product_read_failure,
)
from test_emlis_nls_v3_s11_rc0023_cycle_finalize import (
    _bind_finalizer_frozen_parents,
    _private_rc0022,
    _rc0020_product_read_failure,
)
from test_emlis_nls_v3_s11_rc0024_append_only_lineage import (
    _clean_summary,
    _rc0024_material,
)


_CYCLE = (
    Path(__file__).resolve().parent
    / "fixtures"
    / "emlis_nls_v3"
    / "cycle_001"
)


def _private_rc0023(
    rc23_manifest: dict[str, Any],
    rc23_summary: dict[str, Any],
) -> dict[str, Any]:
    return {
        "schema_version": (
            "cocolon.emlis.nls_v3.private_verification_receipt.step11.v1"
        ),
        "candidate_version_id": "nls_v3_rc_0023",
        "run_id": rc23_summary["run_id"],
        "dependency_manifest_sha256": artifact_sha256(rc23_manifest),
        "source_dependency_closure_sha256": rc23_manifest[
            "source_dependency_closure_sha256"
        ],
        "final_batch_summary_sha256": artifact_sha256(rc23_summary),
        "verified_case_count": 100,
        "verified_selected_count": 100,
        "verified_no_valid_candidate_count": 0,
        "verified_exception_count": 0,
        "private_packet_validation_status": "clean",
        "commitment_key_id": _commitment("rc23:key-id"),
        "body_free": True,
    }


def _bind_rc0023_finalizer_parent(
    monkeypatch: pytest.MonkeyPatch,
    *,
    rc23_manifest: dict[str, Any],
    rc23_summary: dict[str, Any],
    rc23_private: dict[str, Any],
) -> None:
    monkeypatch.setattr(
        finalizer,
        "FROZEN_RC0023_FORMAL_MANIFEST_ARTIFACT_SHA256",
        artifact_sha256(rc23_manifest),
    )
    monkeypatch.setattr(
        finalizer,
        "FROZEN_RC0023_FORMAL_SOURCE_CLOSURE_SHA256",
        rc23_manifest["source_dependency_closure_sha256"],
    )
    monkeypatch.setattr(
        finalizer,
        "FROZEN_RC0023_FORMAL_BATCH_SUMMARY_SHA256",
        artifact_sha256(rc23_summary),
    )
    monkeypatch.setattr(
        finalizer,
        "FROZEN_RC0023_FORMAL_PRIVATE_VERIFICATION_SHA256",
        artifact_sha256(rc23_private),
    )


def _finalizer_material_rc0024(
    monkeypatch: pytest.MonkeyPatch,
) -> dict[str, Any]:
    _, manifests, summaries, rc22, rc23, rc23_summary = _rc0024_material(
        monkeypatch
    )
    rc22_summary = next(
        row
        for row in summaries
        if row["candidate_version_id"] == "nls_v3_rc_0022"
    )
    rc22_private = _private_rc0022(rc22, rc22_summary)
    rc23_private = _private_rc0023(rc23, rc23_summary)

    historical_manifests = [
        row
        for row in manifests
        if row["candidate_version_id"] != "nls_v3_rc_0024"
    ]
    historical_summaries = [
        row
        for row in summaries
        if row["candidate_version_id"] != "nls_v3_rc_0010"
    ]
    _bind_finalizer_frozen_parents(
        monkeypatch,
        historical_manifests,
        historical_summaries,
        rc22_private,
    )
    _bind_rc0023_finalizer_parent(
        monkeypatch,
        rc23_manifest=rc23,
        rc23_summary=rc23_summary,
        rc23_private=rc23_private,
    )

    security_row = {
        "path": finalizer._SECURITY_TEST_PATH,
        "sha256": _commitment("rc24:security"),
    }
    rc24 = build_step11_dependency_manifest(
        before_candidate_version_id="nls_v3_rc_0023",
        before_source_closure_sha256=rc23[
            "source_dependency_closure_sha256"
        ],
        candidate_version_id="nls_v3_rc_0024",
        file_hashes=[security_row],
        changed_file_hashes=[security_row],
    )
    rc24_summary = _clean_summary("nls_v3_rc_0024", rc24)
    return {
        "initial_summary": next(
            row
            for row in summaries
            if row["candidate_version_id"] == "nls_v3_rc_0010"
        ),
        "initial_review": {"body_free": True},
        "final_summary": rc24_summary,
        "dependency_manifest": rc24,
        "historical_dependency_manifests": historical_manifests,
        "historical_batch_run_summaries": historical_summaries,
        "workaround_scan_input_scope": {"body_free": True},
        "rc0020_product_read_failure": _rc0020_product_read_failure(),
        "rc0021_product_read_failure": _rc0021_product_read_failure(),
        "rc0022_private_verification_receipt": rc22_private,
        "rc0023_private_verification_receipt": rc23_private,
    }


def test_rc0024_finalizer_preserves_rc22_failure_and_rc23_clean_execution(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    parents = _finalizer_material_rc0024(monkeypatch)

    lineage, support, manifests, summaries = (
        finalizer._build_rc0010_rc0024_lineage(**parents)
    )

    assert lineage["current_candidate_version_id"] == "nls_v3_rc_0024"
    assert lineage["failed_machine_execution_candidate_sequence"] == [
        "nls_v3_rc_0022"
    ]
    rc22_execution = next(
        row
        for row in lineage["events"]
        if row["event_type"] == "execution_observed"
        and row["candidate_version_id"] == "nls_v3_rc_0022"
    )
    assert rc22_execution["machine_status"] == "failed"
    assert rc22_execution["selected_count"] == 0
    assert rc22_execution["exception_count"] == 95

    rc23_execution = next(
        row
        for row in lineage["events"]
        if row["event_type"] == "execution_observed"
        and row["candidate_version_id"] == "nls_v3_rc_0023"
    )
    assert rc23_execution["execution_scope"] == "formal_cumulative_rerun"
    assert rc23_execution["machine_status"] == "clean"
    assert rc23_execution["selected_count"] == 100
    assert rc23_execution["no_valid_candidate_count"] == 0
    assert rc23_execution["exception_count"] == 0
    rc23_disposition = next(
        row
        for row in lineage["events"]
        if row["event_type"] == "revision_disposition"
        and row["candidate_version_id"] == "nls_v3_rc_0023"
    )
    assert rc23_disposition["disposition"] == (
        "superseded_after_observed_result"
    )

    rc24_correction = next(
        row
        for row in lineage["events"]
        if row["event_type"] == "correction_recorded"
        and row["candidate_version_id"] == "nls_v3_rc_0024"
    )
    assert rc24_correction["dependency_diff_base_candidate_version_id"] == (
        "nls_v3_rc_0023"
    )
    assert support["rc0022_private_verification_receipt_sha256"] == (
        artifact_sha256(parents["rc0022_private_verification_receipt"])
    )
    assert support["rc0023_private_verification_receipt_sha256"] == (
        artifact_sha256(parents["rc0023_private_verification_receipt"])
    )
    assert any(
        row["candidate_version_id"] == "nls_v3_rc_0023"
        for row in manifests
    )
    assert any(
        row["candidate_version_id"] == "nls_v3_rc_0023"
        for row in summaries
    )


@pytest.mark.parametrize(
    "mutation",
    ("omit_manifest", "omit_summary", "relabel_summary", "forge_private"),
)
def test_rc0024_finalizer_rejects_missing_or_relabelled_rc0023_parent(
    monkeypatch: pytest.MonkeyPatch,
    mutation: str,
) -> None:
    parents = _finalizer_material_rc0024(monkeypatch)
    if mutation == "omit_manifest":
        parents["historical_dependency_manifests"] = [
            row
            for row in parents["historical_dependency_manifests"]
            if row["candidate_version_id"] != "nls_v3_rc_0023"
        ]
    elif mutation == "omit_summary":
        parents["historical_batch_run_summaries"] = [
            row
            for row in parents["historical_batch_run_summaries"]
            if row["candidate_version_id"] != "nls_v3_rc_0023"
        ]
    elif mutation == "relabel_summary":
        rc23_summary = next(
            row
            for row in parents["historical_batch_run_summaries"]
            if row["candidate_version_id"] == "nls_v3_rc_0023"
        )
        rc23_summary["machine_status"] = "failed"
        rc23_summary["aggregate"]["selected_count"] = 0
        rc23_summary["aggregate"]["exception_count"] = 100
        for row in rc23_summary["case_rows"]:
            row["status"] = "exception"
    else:
        parents["rc0023_private_verification_receipt"] = {
            **parents["rc0023_private_verification_receipt"],
            "verified_selected_count": 0,
            "verified_exception_count": 100,
        }

    with pytest.raises(ValueError):
        finalizer._build_rc0010_rc0024_lineage(**parents)


def test_rc0024_finalizer_rejects_non_immediate_dependency_parent(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    parents = _finalizer_material_rc0024(monkeypatch)
    security_row = {
        "path": finalizer._SECURITY_TEST_PATH,
        "sha256": _commitment("rc24:security"),
    }
    parents["dependency_manifest"] = build_step11_dependency_manifest(
        before_candidate_version_id="nls_v3_rc_0022",
        before_source_closure_sha256=_commitment("not-rc23"),
        candidate_version_id="nls_v3_rc_0024",
        file_hashes=[security_row],
        changed_file_hashes=[security_row],
    )

    with pytest.raises(
        cycle_evidence.Step11CycleEvidenceError,
        match="RC_LINEAGE_FINAL_DEPENDENCY_BASE_INVALID",
    ):
        finalizer._build_rc0010_rc0024_lineage(**parents)


def test_rc0024_private_verification_exact_frozen_rc0023_is_accepted() -> None:
    receipt = json.loads(
        (_CYCLE / "cycle001_final_rc0023_private_verification.json").read_text(
            encoding="utf-8"
        )
    )

    finalizer._validate_frozen_rc0023_private_verification(receipt)

    with pytest.raises(ValueError):
        finalizer._validate_frozen_rc0023_private_verification(
            {**receipt, "verified_selected_count": 0}
        )


def test_rc0024_scope_is_current_while_rc0023_alias_stays_historical(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    historical_rc22 = {
        "schema_version": "historical.rc22",
        "candidate_version_id": "nls_v3_rc_0022",
        "body_free": True,
    }
    monkeypatch.setattr(
        finalizer,
        "build_historical_rc0022_available_input_scope_receipt",
        lambda **_: deepcopy(historical_rc22),
    )
    parents = {
        "step1_baseline_receipt": {},
        "step1_input_contract": {},
        "step2_corpus_registry": {},
    }

    historical_rc23 = (
        finalizer.build_historical_rc0023_available_input_scope_receipt(
            **parents
        )
    )
    compatibility_rc23 = (
        finalizer._build_rc0023_available_input_scope_receipt(**parents)
    )
    current_rc24 = finalizer.build_available_input_scope_receipt(**parents)

    assert historical_rc23 == compatibility_rc23
    assert historical_rc23["candidate_version_id"] == "nls_v3_rc_0023"
    assert historical_rc23["schema_version"].endswith(".rc0023.v1")
    assert current_rc24["candidate_version_id"] == "nls_v3_rc_0024"
    assert current_rc24["schema_version"].endswith(".rc0024.v1")


def test_rc0024_finalizer_requires_all_exact_rc0023_parent_inputs() -> None:
    parameters = inspect.signature(finalizer.build_cycle_artifacts).parameters
    assert "historical_lineage_dependency_manifests" in parameters
    assert "historical_lineage_batch_run_summaries" in parameters
    assert "rc0022_private_verification_receipt" in parameters
    assert "rc0023_private_verification_receipt" in parameters
