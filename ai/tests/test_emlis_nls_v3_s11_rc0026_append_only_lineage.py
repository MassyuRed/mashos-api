# -*- coding: utf-8 -*-
from __future__ import annotations

"""Append-only rc0026 lineage over clean rc0025 plus Product Read BLOCKER."""

from copy import deepcopy
from typing import Any

import pytest

from emlis_ai_nls_v3_artifact_contract import artifact_sha256
from emlis_ai_step11_cycle_evidence_v3 import (
    FROZEN_RC0025_FORMAL_BATCH_SUMMARY_SHA256,
    FROZEN_RC0025_FORMAL_MANIFEST_ARTIFACT_SHA256,
    FROZEN_RC0025_FORMAL_PRIVATE_VERIFICATION_SHA256,
    FROZEN_RC0025_FORMAL_SOURCE_CLOSURE_SHA256,
    FROZEN_RC0025_PRODUCT_READ_FAILURE_AXES,
    FROZEN_RC0025_PRODUCT_READ_FAILURE_REASONS,
    FROZEN_RC0025_PRODUCT_READ_FAILURE_SHA256,
    RC_CORRECTION_RERUN_LINEAGE_EVENT_V8_SCHEMA,
    RC_CORRECTION_RERUN_LINEAGE_V8_SCHEMA,
    STEP11_CURRENT_CANDIDATE_VERSION_ID,
    STEP11_HISTORICAL_RC0025_CANDIDATE_VERSION_ID,
    STEP11_HISTORICAL_RC0026_CANDIDATE_VERSION_ID,
    Step11CycleEvidenceError,
    build_rc0010_rc0026_correction_rerun_lineage,
    build_step11_dependency_manifest,
    validate_rc0010_rc0026_correction_rerun_lineage,
)
import emlis_ai_step11_cycle_evidence_v3 as cycle_evidence
import emlis_nls_v3_step11_dependency_manifest as dependency_tool
from test_emlis_nls_v3_s11_rc0021_append_only_lineage import (
    _commitment,
    _correction,
)
from test_emlis_nls_v3_s11_rc0024_append_only_lineage import _clean_summary
from test_emlis_nls_v3_s11_rc0025_append_only_lineage import _rc0025_material


_RC0026_ADDED_PATHS = (
    "ai/tests/test_emlis_nls_v3_s11_rc0026_append_only_lineage.py",
    "ai/tests/test_emlis_nls_v3_s11_rc0026_cycle_finalize.py",
    "ai/tests/test_emlis_nls_v3_s11_rc0026_product_read_surface_red.py",
    "ai/tests/test_emlis_nls_v3_s11_rc0026_semantic_matcher_contract.py",
    "ai/tests/test_emlis_nls_v3_s11_rc0026_semantic_source_contract_red.py",
)


def _rc0026_material(
    monkeypatch: pytest.MonkeyPatch,
) -> tuple[
    list[dict[str, Any]],
    list[dict[str, Any]],
    list[dict[str, Any]],
    dict[str, Any],
    dict[str, Any],
]:
    events, manifests, summaries, _, _ = _rc0025_material(monkeypatch)
    rc25_rows = [
        {
            "path": f"ai/tests/frozen_rc0025/path_{index:03d}.py",
            "sha256": _commitment(f"rc25:{index}"),
        }
        for index in range(151)
    ]
    rc24 = next(
        row for row in manifests if row["candidate_version_id"] == "nls_v3_rc_0024"
    )
    rc25 = build_step11_dependency_manifest(
        before_candidate_version_id="nls_v3_rc_0024",
        before_source_closure_sha256=rc24["source_dependency_closure_sha256"],
        candidate_version_id="nls_v3_rc_0025",
        file_hashes=rc25_rows,
        changed_file_hashes=rc25_rows[:1],
    )
    manifests[-1] = rc25
    rc25_correction = next(
        row
        for row in events
        if row["event_type"] == "correction_recorded"
        and row["candidate_version_id"] == "nls_v3_rc_0025"
    )
    rc25_correction["source_state_artifact_sha256"] = artifact_sha256(rc25)
    rc25_correction["changed_file_set_commitment"] = artifact_sha256(
        rc25["changed_file_hashes"]
    )
    rc25_summary = _clean_summary("nls_v3_rc_0025", rc25)
    summaries.append(rc25_summary)
    monkeypatch.setattr(
        cycle_evidence,
        "FROZEN_RC0025_FORMAL_MANIFEST_ARTIFACT_SHA256",
        artifact_sha256(rc25),
    )
    monkeypatch.setattr(
        cycle_evidence,
        "FROZEN_RC0025_FORMAL_SOURCE_CLOSURE_SHA256",
        rc25["source_dependency_closure_sha256"],
    )
    monkeypatch.setattr(
        cycle_evidence,
        "FROZEN_RC0025_FORMAL_BATCH_SUMMARY_SHA256",
        artifact_sha256(rc25_summary),
    )

    pending_index = next(
        index
        for index, row in enumerate(events)
        if row["event_type"] == "revision_disposition"
        and row["candidate_version_id"] == "nls_v3_rc_0025"
    )
    events[pending_index : pending_index + 1] = [
        {
            "event_type": "execution_observed",
            "candidate_version_id": "nls_v3_rc_0025",
            "execution_scope": "formal_cumulative_rerun",
            "batch_summary_sha256": artifact_sha256(rc25_summary),
        },
        {
            "event_type": "product_read_observed",
            "candidate_version_id": "nls_v3_rc_0025",
            "batch_summary_sha256": artifact_sha256(rc25_summary),
            "review_outcome": "failed",
            "maximum_severity": "BLOCKER",
            "failure_axis_codes": list(FROZEN_RC0025_PRODUCT_READ_FAILURE_AXES),
            "failure_reason_codes": list(
                FROZEN_RC0025_PRODUCT_READ_FAILURE_REASONS
            ),
            "review_receipt_commitment": (
                FROZEN_RC0025_PRODUCT_READ_FAILURE_SHA256
            ),
        },
        {
            "event_type": "revision_disposition",
            "candidate_version_id": "nls_v3_rc_0025",
            "disposition": "superseded_after_observed_result",
            "decision_receipt_commitment": _commitment("rc25:superseded"),
        },
    ]

    rc26_row = {
        "path": "ai/tests/rc0026_common_owner.py",
        "sha256": _commitment("rc26:owner"),
    }
    rc26 = build_step11_dependency_manifest(
        before_candidate_version_id="nls_v3_rc_0025",
        before_source_closure_sha256=rc25["source_dependency_closure_sha256"],
        candidate_version_id="nls_v3_rc_0026",
        file_hashes=[rc26_row],
        changed_file_hashes=[rc26_row],
    )
    manifests.append(rc26)
    events.extend(
        [
            _correction("nls_v3_rc_0026", rc26),
            {
                "event_type": "revision_disposition",
                "candidate_version_id": "nls_v3_rc_0026",
                "disposition": "current_pending_rerun",
                "decision_receipt_commitment": _commitment("rc26:pending"),
            },
        ]
    )
    return events, manifests, summaries, rc25, rc25_summary


def test_rc0026_exact_frozen_rc0025_parent_constants_are_explicit() -> None:
    assert STEP11_HISTORICAL_RC0025_CANDIDATE_VERSION_ID == "nls_v3_rc_0025"
    assert STEP11_CURRENT_CANDIDATE_VERSION_ID == "nls_v3_rc_0027"
    assert STEP11_HISTORICAL_RC0026_CANDIDATE_VERSION_ID == "nls_v3_rc_0026"
    assert RC_CORRECTION_RERUN_LINEAGE_V8_SCHEMA.endswith(".v8")
    assert RC_CORRECTION_RERUN_LINEAGE_EVENT_V8_SCHEMA.endswith(".v8")
    assert FROZEN_RC0025_FORMAL_MANIFEST_ARTIFACT_SHA256 == (
        "222007643aeb46337ebe31e4a46c6a88b96c75134e6ddf881944f52b6723cb47"
    )
    assert FROZEN_RC0025_FORMAL_SOURCE_CLOSURE_SHA256 == (
        "983a85aab08b217fd3b09e965c52f789d332f72cac2c03bdb06c9452983e728d"
    )
    assert FROZEN_RC0025_FORMAL_BATCH_SUMMARY_SHA256 == (
        "1aaf8b8818eec31ad637a27d9414a7ec801e28675b8b88bd6d281718a7d0c19a"
    )
    assert FROZEN_RC0025_FORMAL_PRIVATE_VERIFICATION_SHA256 == (
        "4ca6eedf954455325b74a306dfb32c37c2e4d16ed59cea18de38eb2606b568b5"
    )


def test_rc0026_lineage_preserves_clean_rc0025_and_blocker_review(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    events, manifests, summaries, _, _ = _rc0026_material(monkeypatch)

    lineage = build_rc0010_rc0026_correction_rerun_lineage(
        events,
        dependency_manifests=manifests,
        batch_run_summaries=summaries,
    )

    assert lineage["schema_version"] == RC_CORRECTION_RERUN_LINEAGE_V8_SCHEMA
    assert lineage["current_candidate_version_id"] == "nls_v3_rc_0026"
    assert lineage["acceptance_lineage_ready"] is False
    rc25_execution = next(
        row
        for row in lineage["events"]
        if row["event_type"] == "execution_observed"
        and row["candidate_version_id"] == "nls_v3_rc_0025"
    )
    assert rc25_execution["machine_status"] == "clean"
    assert rc25_execution["executed_case_count"] == 100
    assert rc25_execution["selected_count"] == 100
    rc25_review = next(
        row
        for row in lineage["events"]
        if row["event_type"] == "product_read_observed"
        and row["candidate_version_id"] == "nls_v3_rc_0025"
    )
    assert rc25_review["maximum_severity"] == "BLOCKER"
    assert rc25_review["failure_axis_codes"] == list(
        FROZEN_RC0025_PRODUCT_READ_FAILURE_AXES
    )
    assert validate_rc0010_rc0026_correction_rerun_lineage(
        lineage,
        dependency_manifests=manifests,
        batch_run_summaries=summaries,
    ) == ()


@pytest.mark.parametrize(
    "field,replacement",
    [
        ("maximum_severity", "MAJOR"),
        ("execution_scope", "preflight"),
        ("review_receipt_commitment", _commitment("rc25:wrong-review")),
    ],
)
def test_rc0026_lineage_rejects_relabelled_rc0025_product_read(
    monkeypatch: pytest.MonkeyPatch,
    field: str,
    replacement: str,
) -> None:
    events, manifests, summaries, _, _ = _rc0026_material(monkeypatch)
    event_type = "execution_observed" if field == "execution_scope" else "product_read_observed"
    target = next(
        row
        for row in events
        if row["event_type"] == event_type
        and row["candidate_version_id"] == "nls_v3_rc_0025"
    )
    target[field] = replacement

    with pytest.raises(Step11CycleEvidenceError):
        build_rc0010_rc0026_correction_rerun_lineage(
            events,
            dependency_manifests=manifests,
            batch_run_summaries=summaries,
        )


def test_rc0026_manifest_is_exact_151_plus_structural_red_owners(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    rows = [
        {
            "path": f"ai/tests/frozen_rc0025/path_{index:03d}.py",
            "sha256": _commitment(f"rc25:{index}"),
        }
        for index in range(151)
    ]
    rc25 = build_step11_dependency_manifest(
        before_candidate_version_id="nls_v3_rc_0024",
        before_source_closure_sha256=_commitment("rc24"),
        candidate_version_id="nls_v3_rc_0025",
        file_hashes=rows,
        changed_file_hashes=rows[:1],
    )
    frozen_rc25 = deepcopy(rc25)
    changed_path = rows[40]["path"]
    current = {row["path"]: row["sha256"] for row in rows}
    current[changed_path] = _commitment("rc26:changed")
    for path in _RC0026_ADDED_PATHS:
        current[path] = _commitment(f"rc26:{path}")
    monkeypatch.setattr(
        dependency_tool,
        "FROZEN_RC0025_FORMAL_MANIFEST_ARTIFACT_SHA256",
        artifact_sha256(rc25),
    )
    monkeypatch.setattr(
        dependency_tool,
        "FROZEN_RC0025_FORMAL_SOURCE_CLOSURE_SHA256",
        rc25["source_dependency_closure_sha256"],
    )
    monkeypatch.setattr(
        dependency_tool,
        "FROZEN_RC0024_FORMAL_SOURCE_CLOSURE_SHA256",
        rc25["before_source_closure_sha256"],
    )
    monkeypatch.setattr(
        dependency_tool,
        "STEP11_CANDIDATE_VERSION_ID",
        STEP11_CURRENT_CANDIDATE_VERSION_ID,
    )
    monkeypatch.setattr(dependency_tool, "_sha256", lambda path: current[path])

    assert dependency_tool.RC0026_ADDED_SOURCE_PATHS == _RC0026_ADDED_PATHS
    result = dependency_tool.build_current_step11_dependency_manifest(rc25)

    assert rc25 == frozen_rc25
    assert result["before_candidate_version_id"] == "nls_v3_rc_0025"
    assert result["before_source_closure_sha256"] == rc25[
        "source_dependency_closure_sha256"
    ]
    assert result["candidate_version_id"] == "nls_v3_rc_0026"
    assert len(result["file_hashes"]) == 156
    assert {row["path"] for row in result["changed_file_hashes"]} == {
        changed_path,
        *_RC0026_ADDED_PATHS,
    }
