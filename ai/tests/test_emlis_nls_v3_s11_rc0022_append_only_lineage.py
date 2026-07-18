# -*- coding: utf-8 -*-
from __future__ import annotations

"""Append-only rc0022 lineage and exact rc0021-parent REDs."""

from typing import Any

import pytest

from emlis_ai_nls_v3_artifact_contract import artifact_sha256
from emlis_ai_step11_cycle_evidence_v3 import (
    FROZEN_RC0021_PREFLIGHT_BATCH_SUMMARY_SHA256,
    FROZEN_RC0021_PREFLIGHT_MANIFEST_ARTIFACT_SHA256,
    FROZEN_RC0021_PREFLIGHT_PRIVATE_VERIFICATION_SHA256,
    FROZEN_RC0021_PREFLIGHT_SOURCE_CLOSURE_SHA256,
    RC_CORRECTION_RERUN_LINEAGE_EVENT_V4_SCHEMA,
    RC_CORRECTION_RERUN_LINEAGE_V4_SCHEMA,
    STEP11_HISTORICAL_RC0021_CANDIDATE_VERSION_ID,
    STEP11_HISTORICAL_RC0022_CANDIDATE_VERSION_ID,
    Step11CycleEvidenceError,
    build_rc0010_rc0022_correction_rerun_lineage,
    validate_rc0010_rc0022_correction_rerun_lineage,
)
import emlis_ai_step11_cycle_evidence_v3 as cycle_evidence
import emlis_nls_v3_step11_dependency_manifest as dependency_tool
from test_emlis_nls_v3_s11_rc0021_append_only_lineage import (
    _bind_frozen_history,
    _commitment,
    _correction,
    _manifest,
    _material,
    _summary,
)


def _rc0022_material(
    monkeypatch: pytest.MonkeyPatch,
) -> tuple[
    list[dict[str, Any]],
    list[dict[str, Any]],
    list[dict[str, Any]],
    dict[str, Any],
    dict[str, Any],
]:
    events, manifests, summaries, rc20, rc20_summary = _material()
    _bind_frozen_history(
        monkeypatch,
        manifests,
        summaries,
        rc20,
        rc20_summary,
    )
    rc21 = next(
        row
        for row in manifests
        if row["candidate_version_id"] == "nls_v3_rc_0021"
    )
    rc21_summary = _summary(
        "nls_v3_rc_0021",
        rc21["source_dependency_closure_sha256"],
    )
    rc22 = _manifest(
        "nls_v3_rc_0022",
        before_candidate="nls_v3_rc_0021",
        before_closure=rc21["source_dependency_closure_sha256"],
    )
    manifests.append(rc22)
    summaries.append(rc21_summary)
    monkeypatch.setattr(
        cycle_evidence,
        "FROZEN_RC0021_PREFLIGHT_MANIFEST_ARTIFACT_SHA256",
        artifact_sha256(rc21),
    )
    monkeypatch.setattr(
        cycle_evidence,
        "FROZEN_RC0021_PREFLIGHT_SOURCE_CLOSURE_SHA256",
        rc21["source_dependency_closure_sha256"],
    )
    monkeypatch.setattr(
        cycle_evidence,
        "FROZEN_RC0021_PREFLIGHT_BATCH_SUMMARY_SHA256",
        artifact_sha256(rc21_summary),
    )

    rc21_disposition_index = next(
        index
        for index, row in enumerate(events)
        if row["event_type"] == "revision_disposition"
        and row["candidate_version_id"] == "nls_v3_rc_0021"
    )
    events[rc21_disposition_index:rc21_disposition_index] = [
        {
            "event_type": "execution_observed",
            "candidate_version_id": "nls_v3_rc_0021",
            "execution_scope": "preflight",
            "batch_summary_sha256": artifact_sha256(rc21_summary),
        },
        {
            "event_type": "product_read_observed",
            "candidate_version_id": "nls_v3_rc_0021",
            "batch_summary_sha256": artifact_sha256(rc21_summary),
            "review_outcome": "failed",
            "maximum_severity": "MAJOR",
            "failure_axis_codes": [
                "BOUND_EMLIS_RECEPTION",
                "IMMEDIATE_OBSERVATION_FEELS_READ",
                "NATURAL_NON_REPETITIVE_SURFACE",
            ],
            "failure_reason_codes": [
                "EMLIS_RECEPTION_UNBOUND",
                "IMMEDIATE_OBSERVATION_NOT_READ",
                "SURFACE_UNNATURAL_OR_REPETITIVE",
            ],
            "failure_case_ids": ["nls3s_b001_0035"],
            "review_receipt_commitment": _commitment(
                "rc21:product-read-major:0035"
            ),
        },
    ]
    events[rc21_disposition_index + 2] = {
        "event_type": "revision_disposition",
        "candidate_version_id": "nls_v3_rc_0021",
        "disposition": "superseded_after_observed_result",
        "decision_receipt_commitment": _commitment("rc21:superseded"),
    }
    events.extend(
        [
            _correction("nls_v3_rc_0022", rc22),
            {
                "event_type": "revision_disposition",
                "candidate_version_id": "nls_v3_rc_0022",
                "disposition": "current_pending_rerun",
                "decision_receipt_commitment": _commitment("rc22:pending"),
            },
        ]
    )
    return events, manifests, summaries, rc21, rc21_summary


def test_rc0022_versions_and_frozen_rc0021_constants_are_explicit() -> None:
    assert STEP11_HISTORICAL_RC0021_CANDIDATE_VERSION_ID == "nls_v3_rc_0021"
    assert STEP11_HISTORICAL_RC0022_CANDIDATE_VERSION_ID == "nls_v3_rc_0022"
    assert RC_CORRECTION_RERUN_LINEAGE_V4_SCHEMA.endswith(".v4")
    assert RC_CORRECTION_RERUN_LINEAGE_EVENT_V4_SCHEMA.endswith(".v4")
    assert FROZEN_RC0021_PREFLIGHT_MANIFEST_ARTIFACT_SHA256 == (
        "b4b2e0b743f3bc5750818bcc352474a303721bb90ee75eebeb13796fe2ce18e4"
    )
    assert FROZEN_RC0021_PREFLIGHT_SOURCE_CLOSURE_SHA256 == (
        "612939ef04f90e82e67ae015715d3a5e508aa217effd4a988dee542ba3428cee"
    )
    assert FROZEN_RC0021_PREFLIGHT_BATCH_SUMMARY_SHA256 == (
        "e30c1d6adb83a0428a1ebae0e4373edb44ab5122edba77aca4bdadcb11907e4b"
    )
    assert FROZEN_RC0021_PREFLIGHT_PRIVATE_VERIFICATION_SHA256 == (
        "111c9212cd67ba191b5f3116d92fcd5c2a3b70c4a28de5eb85e827954b2b96ff"
    )


def test_rc0022_lineage_orders_rc20_and_case0035_rc21_product_failures(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    events, manifests, summaries, _, _ = _rc0022_material(monkeypatch)

    lineage = build_rc0010_rc0022_correction_rerun_lineage(
        events,
        dependency_manifests=manifests,
        batch_run_summaries=summaries,
    )

    assert lineage["schema_version"] == RC_CORRECTION_RERUN_LINEAGE_V4_SCHEMA
    assert lineage["current_candidate_version_id"] == "nls_v3_rc_0022"
    assert lineage["acceptance_lineage_ready"] is False
    assert lineage["failed_product_read_candidate_sequence"] == [
        "nls_v3_rc_0020",
        "nls_v3_rc_0021",
    ]
    product_reads = [
        row
        for row in lineage["events"]
        if row["event_type"] == "product_read_observed"
    ]
    assert [row["candidate_version_id"] for row in product_reads] == [
        "nls_v3_rc_0020",
        "nls_v3_rc_0021",
    ]
    assert product_reads[1]["failure_case_ids"] == ["nls3s_b001_0035"]
    assert product_reads[1]["maximum_severity"] == "MAJOR"
    rc21_disposition = next(
        row
        for row in lineage["events"]
        if row["event_type"] == "revision_disposition"
        and row["candidate_version_id"] == "nls_v3_rc_0021"
    )
    assert rc21_disposition["disposition"] == (
        "superseded_after_observed_result"
    )
    assert rc21_disposition["failed_product_read_observed"] is True
    assert lineage["aggregate"]["failed_product_read_count"] == 2
    assert validate_rc0010_rc0022_correction_rerun_lineage(
        lineage,
        dependency_manifests=manifests,
        batch_run_summaries=summaries,
    ) == ()


@pytest.mark.parametrize(
    "mutation",
    ("remove_rc21_review", "wrong_case", "accept_rc21"),
)
def test_rc0022_rejects_erased_or_relabelled_rc0021_product_failure(
    monkeypatch: pytest.MonkeyPatch,
    mutation: str,
) -> None:
    events, manifests, summaries, _, _ = _rc0022_material(monkeypatch)
    rc21_product = next(
        row
        for row in events
        if row["event_type"] == "product_read_observed"
        and row["candidate_version_id"] == "nls_v3_rc_0021"
    )
    if mutation == "remove_rc21_review":
        events.remove(rc21_product)
    elif mutation == "wrong_case":
        rc21_product["failure_case_ids"] = ["nls3s_b001_0068"]
    else:
        disposition = next(
            row
            for row in events
            if row["event_type"] == "revision_disposition"
            and row["candidate_version_id"] == "nls_v3_rc_0021"
        )
        disposition["disposition"] = "cycle_final_candidate"

    with pytest.raises(Step11CycleEvidenceError):
        build_rc0010_rc0022_correction_rerun_lineage(
            events,
            dependency_manifests=manifests,
            batch_run_summaries=summaries,
        )


def test_rc0022_requires_immediate_exact_rc0021_parent(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    events, manifests, summaries, rc21, _ = _rc0022_material(monkeypatch)
    forged = _manifest(
        "nls_v3_rc_0022",
        before_candidate="nls_v3_rc_0020",
        before_closure=rc21["before_source_closure_sha256"],
    )
    manifests[-1] = forged
    correction = next(
        row
        for row in events
        if row["event_type"] == "correction_recorded"
        and row["candidate_version_id"] == "nls_v3_rc_0022"
    )
    correction["source_state_artifact_sha256"] = artifact_sha256(forged)
    correction["changed_file_set_commitment"] = artifact_sha256(
        forged["changed_file_hashes"]
    )

    with pytest.raises(
        Step11CycleEvidenceError,
        match="RC_LINEAGE_FINAL_DEPENDENCY_BASE_INVALID",
    ):
        build_rc0010_rc0022_correction_rerun_lineage(
            events,
            dependency_manifests=manifests,
            batch_run_summaries=summaries,
        )


def test_rc0022_dependency_manifest_is_exact_diff_from_frozen_rc0021(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    rows = [
        {
            "path": f"ai/tests/frozen_rc0021/path_{index:03d}.py",
            "sha256": _commitment(f"rc21:{index}"),
        }
        for index in range(138)
    ]
    rc21 = cycle_evidence.build_step11_dependency_manifest(
        before_candidate_version_id="nls_v3_rc_0020",
        before_source_closure_sha256=_commitment("rc20"),
        candidate_version_id="nls_v3_rc_0021",
        file_hashes=rows,
        changed_file_hashes=rows[:1],
    )
    changed_path = rows[35]["path"]
    current = {row["path"]: row["sha256"] for row in rows}
    current[changed_path] = _commitment("rc22:changed")
    for path in dependency_tool.RC0022_ADDED_SOURCE_PATHS:
        current[path] = _commitment(f"rc22:{path}")
    monkeypatch.setattr(
        dependency_tool,
        "FROZEN_RC0021_PREFLIGHT_MANIFEST_ARTIFACT_SHA256",
        artifact_sha256(rc21),
    )
    monkeypatch.setattr(
        dependency_tool,
        "FROZEN_RC0021_PREFLIGHT_SOURCE_CLOSURE_SHA256",
        rc21["source_dependency_closure_sha256"],
    )
    monkeypatch.setattr(
        dependency_tool,
        "FROZEN_RC0020_PREFLIGHT_SOURCE_CLOSURE_SHA256",
        rc21["before_source_closure_sha256"],
    )
    monkeypatch.setattr(dependency_tool, "_sha256", lambda path: current[path])

    result = dependency_tool.build_current_step11_dependency_manifest(rc21)

    assert result["before_candidate_version_id"] == "nls_v3_rc_0021"
    assert result["before_source_closure_sha256"] == rc21[
        "source_dependency_closure_sha256"
    ]
    assert result["candidate_version_id"] == "nls_v3_rc_0022"
    assert len(result["file_hashes"]) == 141
    assert {row["path"] for row in result["changed_file_hashes"]} == {
        changed_path,
        *dependency_tool.RC0022_ADDED_SOURCE_PATHS,
    }
