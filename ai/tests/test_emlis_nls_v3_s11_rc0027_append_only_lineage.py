# -*- coding: utf-8 -*-
from __future__ import annotations

"""Append-only rc0027 lineage over exact clean rc0026 public parents."""

from copy import deepcopy
from typing import Any

import pytest

from emlis_ai_nls_v3_artifact_contract import artifact_sha256
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
    RC_CORRECTION_RERUN_LINEAGE_EVENT_V9_SCHEMA,
    RC_CORRECTION_RERUN_LINEAGE_V9_SCHEMA,
    STEP11_CURRENT_CANDIDATE_VERSION_ID,
    STEP11_HISTORICAL_RC0026_CANDIDATE_VERSION_ID,
    Step11CycleEvidenceError,
    build_rc0010_rc0027_correction_rerun_lineage,
    build_step11_dependency_manifest,
    validate_rc0010_rc0027_correction_rerun_lineage,
)
import emlis_ai_step11_cycle_evidence_v3 as cycle_evidence
from test_emlis_nls_v3_s11_rc0021_append_only_lineage import (
    _commitment,
    _correction,
)
from test_emlis_nls_v3_s11_rc0024_append_only_lineage import _clean_summary
from test_emlis_nls_v3_s11_rc0026_append_only_lineage import _rc0026_material


def _rc0027_material(
    monkeypatch: pytest.MonkeyPatch,
) -> tuple[
    list[dict[str, Any]],
    list[dict[str, Any]],
    list[dict[str, Any]],
    dict[str, Any],
    dict[str, Any],
]:
    events, manifests, summaries, _, _ = _rc0026_material(monkeypatch)
    rc26_rows = [
        {
            "path": f"ai/tests/frozen_rc0026/path_{index:03d}.py",
            "sha256": _commitment(f"rc26:{index}"),
        }
        for index in range(156)
    ]
    rc25 = next(
        row
        for row in manifests
        if row["candidate_version_id"] == "nls_v3_rc_0025"
    )
    rc26 = build_step11_dependency_manifest(
        before_candidate_version_id="nls_v3_rc_0025",
        before_source_closure_sha256=rc25[
            "source_dependency_closure_sha256"
        ],
        candidate_version_id="nls_v3_rc_0026",
        file_hashes=rc26_rows,
        changed_file_hashes=rc26_rows[:1],
    )
    manifests[-1] = rc26
    rc26_correction = next(
        row
        for row in events
        if row["event_type"] == "correction_recorded"
        and row["candidate_version_id"] == "nls_v3_rc_0026"
    )
    rc26_correction["source_state_artifact_sha256"] = artifact_sha256(rc26)
    rc26_correction["changed_file_set_commitment"] = artifact_sha256(
        rc26["changed_file_hashes"]
    )
    rc26_summary = _clean_summary("nls_v3_rc_0026", rc26)
    summaries.append(rc26_summary)
    monkeypatch.setattr(
        cycle_evidence,
        "FROZEN_RC0026_FORMAL_MANIFEST_ARTIFACT_SHA256",
        artifact_sha256(rc26),
    )
    monkeypatch.setattr(
        cycle_evidence,
        "FROZEN_RC0026_FORMAL_SOURCE_CLOSURE_SHA256",
        rc26["source_dependency_closure_sha256"],
    )
    monkeypatch.setattr(
        cycle_evidence,
        "FROZEN_RC0026_FORMAL_BATCH_SUMMARY_SHA256",
        artifact_sha256(rc26_summary),
    )

    pending_index = next(
        index
        for index, row in enumerate(events)
        if row["event_type"] == "revision_disposition"
        and row["candidate_version_id"] == "nls_v3_rc_0026"
    )
    summary_sha = artifact_sha256(rc26_summary)
    events[pending_index : pending_index + 1] = [
        {
            "event_type": "execution_observed",
            "candidate_version_id": "nls_v3_rc_0026",
            "execution_scope": "formal_cumulative_rerun",
            "batch_summary_sha256": summary_sha,
        },
        *[
            {
                "event_type": "regression_receipt_observed",
                "candidate_version_id": "nls_v3_rc_0026",
                "batch_summary_sha256": summary_sha,
                "regression_suite": suite,
                "receipt_commitment": commitment,
            }
            for suite, commitment in (
                ("known28", FROZEN_RC0026_KNOWN28_RECEIPT_SHA256),
                (
                    "development42",
                    FROZEN_RC0026_DEVELOPMENT42_RECEIPT_SHA256,
                ),
                ("invalid16", FROZEN_RC0026_INVALID16_RECEIPT_SHA256),
            )
        ],
        {
            "event_type": "product_read_observed",
            "candidate_version_id": "nls_v3_rc_0026",
            "batch_summary_sha256": summary_sha,
            "review_outcome": "failed",
            "maximum_severity": "MAJOR",
            "failure_axis_codes": list(
                FROZEN_RC0026_PRODUCT_READ_FAILURE_AXES
            ),
            "failure_reason_codes": list(
                FROZEN_RC0026_PRODUCT_READ_FAILURE_REASONS
            ),
            "review_receipt_commitment": (
                FROZEN_RC0026_PRODUCT_READ_FAILURE_SHA256
            ),
        },
        {
            "event_type": "revision_disposition",
            "candidate_version_id": "nls_v3_rc_0026",
            "disposition": "superseded_after_observed_result",
            "decision_receipt_commitment": _commitment("rc26:superseded"),
        },
    ]

    rc27_row = {
        "path": "ai/tests/rc0027_common_surface_owner.py",
        "sha256": _commitment("rc27:owner"),
    }
    rc27 = build_step11_dependency_manifest(
        before_candidate_version_id="nls_v3_rc_0026",
        before_source_closure_sha256=rc26[
            "source_dependency_closure_sha256"
        ],
        candidate_version_id="nls_v3_rc_0027",
        file_hashes=[rc27_row],
        changed_file_hashes=[rc27_row],
    )
    manifests.append(rc27)
    events.extend(
        [
            _correction("nls_v3_rc_0027", rc27),
            {
                "event_type": "revision_disposition",
                "candidate_version_id": "nls_v3_rc_0027",
                "disposition": "current_pending_rerun",
                "decision_receipt_commitment": _commitment("rc27:pending"),
            },
        ]
    )
    return events, manifests, summaries, rc26, rc26_summary


def test_rc0027_exact_frozen_rc0026_parent_constants_are_explicit() -> None:
    assert STEP11_HISTORICAL_RC0026_CANDIDATE_VERSION_ID == "nls_v3_rc_0026"
    assert STEP11_CURRENT_CANDIDATE_VERSION_ID == "nls_v3_rc_0027"
    assert RC_CORRECTION_RERUN_LINEAGE_V9_SCHEMA.endswith(".v9")
    assert RC_CORRECTION_RERUN_LINEAGE_EVENT_V9_SCHEMA.endswith(".v9")
    assert FROZEN_RC0026_FORMAL_MANIFEST_ARTIFACT_SHA256 == (
        "79d4b7b2bf2c926f914c4da6fc3c108dd1e539c5cf44b315c5625e48a3ac62af"
    )
    assert FROZEN_RC0026_FORMAL_SOURCE_CLOSURE_SHA256 == (
        "9c21d9eaac57e342e4097757b6500a73eb278e786f77db04ca0525e00290c1a4"
    )
    assert FROZEN_RC0026_FORMAL_BATCH_SUMMARY_SHA256 == (
        "10abda72ad1607460dac1ec2cddcb90c477d566dffe16d2b24d822b2fe1a6ebd"
    )
    assert FROZEN_RC0026_FORMAL_PRIVATE_VERIFICATION_SHA256 == (
        "fa89570f7ea356c0240628326b42977ea0dd955a989b100e160ada75af2849ba"
    )


def test_rc0027_lineage_binds_rc0026_execution_regressions_and_major_read(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    events, manifests, summaries, _, _ = _rc0027_material(monkeypatch)

    lineage = build_rc0010_rc0027_correction_rerun_lineage(
        events,
        dependency_manifests=manifests,
        batch_run_summaries=summaries,
    )

    assert lineage["schema_version"] == RC_CORRECTION_RERUN_LINEAGE_V9_SCHEMA
    assert lineage["current_candidate_version_id"] == "nls_v3_rc_0027"
    assert lineage["acceptance_lineage_ready"] is False
    rc26_events = [
        row
        for row in lineage["events"]
        if row["candidate_version_id"] == "nls_v3_rc_0026"
    ]
    assert [
        row["regression_suite"]
        for row in rc26_events
        if row["event_type"] == "regression_receipt_observed"
    ] == ["known28", "development42", "invalid16"]
    review = next(
        row
        for row in rc26_events
        if row["event_type"] == "product_read_observed"
    )
    assert review["maximum_severity"] == "MAJOR"
    assert lineage["aggregate"]["regression_receipt_observation_count"] == 3
    assert validate_rc0010_rc0027_correction_rerun_lineage(
        lineage,
        dependency_manifests=manifests,
        batch_run_summaries=summaries,
    ) == ()


@pytest.mark.parametrize("mutation", ["drop", "reorder", "wrong_hash"])
def test_rc0027_lineage_rejects_inexact_rc0026_regression_sequence(
    monkeypatch: pytest.MonkeyPatch,
    mutation: str,
) -> None:
    events, manifests, summaries, _, _ = _rc0027_material(monkeypatch)
    indices = [
        index
        for index, row in enumerate(events)
        if row["event_type"] == "regression_receipt_observed"
        and row["candidate_version_id"] == "nls_v3_rc_0026"
    ]
    if mutation == "drop":
        events.pop(indices[1])
    elif mutation == "reorder":
        events[indices[0]], events[indices[1]] = (
            events[indices[1]],
            events[indices[0]],
        )
    else:
        events[indices[0]]["receipt_commitment"] = _commitment("wrong")

    with pytest.raises(Step11CycleEvidenceError):
        build_rc0010_rc0027_correction_rerun_lineage(
            events,
            dependency_manifests=manifests,
            batch_run_summaries=summaries,
        )


def test_rc0027_lineage_does_not_mutate_parent_artifacts(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    events, manifests, summaries, _, _ = _rc0027_material(monkeypatch)
    frozen = deepcopy((events, manifests, summaries))

    build_rc0010_rc0027_correction_rerun_lineage(
        events,
        dependency_manifests=manifests,
        batch_run_summaries=summaries,
    )

    assert (events, manifests, summaries) == frozen
