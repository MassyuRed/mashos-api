# -*- coding: utf-8 -*-
from __future__ import annotations

"""Append-only rc0024 lineage and exact clean-rc0023 parent REDs."""

from copy import deepcopy
from typing import Any

import pytest

from emlis_ai_nls_v3_artifact_contract import artifact_sha256
from emlis_ai_step11_cycle_evidence_v3 import (
    FROZEN_RC0023_FORMAL_BATCH_SUMMARY_SHA256,
    FROZEN_RC0023_FORMAL_MANIFEST_ARTIFACT_SHA256,
    FROZEN_RC0023_FORMAL_PRIVATE_VERIFICATION_SHA256,
    FROZEN_RC0023_FORMAL_SOURCE_CLOSURE_SHA256,
    RC_CORRECTION_RERUN_LINEAGE_EVENT_V6_SCHEMA,
    RC_CORRECTION_RERUN_LINEAGE_V6_SCHEMA,
    STEP11_CURRENT_CANDIDATE_VERSION_ID,
    STEP11_HISTORICAL_RC0023_CANDIDATE_VERSION_ID,
    STEP11_HISTORICAL_RC0023_RUNTIME_ADAPTER_VERSION,
    Step11CycleEvidenceError,
    build_rc0010_rc0024_correction_rerun_lineage,
    build_step11_dependency_manifest,
    validate_rc0010_rc0024_correction_rerun_lineage,
)
import emlis_ai_step11_cycle_evidence_v3 as cycle_evidence
import emlis_nls_v3_step11_dependency_manifest as dependency_tool
from test_emlis_nls_v3_s11_rc0021_append_only_lineage import (
    _commitment,
    _correction,
    _summary,
)
from test_emlis_nls_v3_s11_rc0023_append_only_lineage import (
    _rc0023_material,
)


_RC0024_ADDED_PATHS = (
    "ai/tests/test_emlis_nls_v3_s11_rc0024_append_only_lineage.py",
    "ai/tests/test_emlis_nls_v3_s11_rc0024_cycle_finalize.py",
    "ai/tests/test_emlis_nls_v3_s11_rc0024_source_slot_ownership.py",
)


def _clean_summary(
    candidate: str,
    manifest: dict[str, Any],
) -> dict[str, Any]:
    closure = manifest["source_dependency_closure_sha256"]
    summary = deepcopy(_summary(candidate, closure))
    summary["dependency_manifest_sha256"] = artifact_sha256(manifest)
    summary["source_closure_start_sha256"] = closure
    summary["source_closure_end_sha256"] = closure
    summary["source_closure_stable"] = True
    summary["machine_status"] = "clean"
    summary["all_expected_cases_executed"] = True
    summary["executed_case_count"] = 100
    summary["aggregate"]["selected_count"] = 100
    summary["aggregate"]["no_valid_candidate_count"] = 0
    summary["aggregate"]["exception_count"] = 0
    summary["aggregate"]["v1_fallback_count"] = 0
    for row in summary["case_rows"]:
        row["status"] = "selected"
    return summary


def _rc0024_material(
    monkeypatch: pytest.MonkeyPatch,
) -> tuple[
    list[dict[str, Any]],
    list[dict[str, Any]],
    list[dict[str, Any]],
    dict[str, Any],
    dict[str, Any],
    dict[str, Any],
]:
    events, manifests, summaries, rc22, _ = _rc0023_material(monkeypatch)

    rc23_rows = [
        {
            "path": f"ai/tests/frozen_rc0023/path_{index:03d}.py",
            "sha256": _commitment(f"rc23:{index}"),
        }
        for index in range(145)
    ]
    rc23 = build_step11_dependency_manifest(
        before_candidate_version_id="nls_v3_rc_0022",
        before_source_closure_sha256=rc22[
            "source_dependency_closure_sha256"
        ],
        candidate_version_id="nls_v3_rc_0023",
        file_hashes=rc23_rows,
        changed_file_hashes=rc23_rows[:1],
    )
    manifests[-1] = rc23
    rc23_correction = next(
        row
        for row in events
        if row["event_type"] == "correction_recorded"
        and row["candidate_version_id"] == "nls_v3_rc_0023"
    )
    rc23_correction["source_state_artifact_sha256"] = artifact_sha256(rc23)
    rc23_correction["changed_file_set_commitment"] = artifact_sha256(
        rc23["changed_file_hashes"]
    )

    rc23_summary = _clean_summary("nls_v3_rc_0023", rc23)
    summaries.append(rc23_summary)
    monkeypatch.setattr(
        cycle_evidence,
        "FROZEN_RC0023_FORMAL_MANIFEST_ARTIFACT_SHA256",
        artifact_sha256(rc23),
    )
    monkeypatch.setattr(
        cycle_evidence,
        "FROZEN_RC0023_FORMAL_SOURCE_CLOSURE_SHA256",
        rc23["source_dependency_closure_sha256"],
    )
    monkeypatch.setattr(
        cycle_evidence,
        "FROZEN_RC0023_FORMAL_BATCH_SUMMARY_SHA256",
        artifact_sha256(rc23_summary),
    )

    rc23_pending_index = next(
        index
        for index, row in enumerate(events)
        if row["event_type"] == "revision_disposition"
        and row["candidate_version_id"] == "nls_v3_rc_0023"
    )
    events[rc23_pending_index : rc23_pending_index + 1] = [
        {
            "event_type": "execution_observed",
            "candidate_version_id": "nls_v3_rc_0023",
            "execution_scope": "formal_cumulative_rerun",
            "batch_summary_sha256": artifact_sha256(rc23_summary),
        },
        {
            "event_type": "revision_disposition",
            "candidate_version_id": "nls_v3_rc_0023",
            "disposition": "superseded_after_observed_result",
            "decision_receipt_commitment": _commitment("rc23:superseded"),
        },
    ]

    rc24_row = {
        "path": "ai/tests/rc0024_common_owner.py",
        "sha256": _commitment("rc24:owner"),
    }
    rc24 = build_step11_dependency_manifest(
        before_candidate_version_id="nls_v3_rc_0023",
        before_source_closure_sha256=rc23[
            "source_dependency_closure_sha256"
        ],
        candidate_version_id="nls_v3_rc_0024",
        file_hashes=[rc24_row],
        changed_file_hashes=[rc24_row],
    )
    manifests.append(rc24)
    events.extend(
        [
            _correction("nls_v3_rc_0024", rc24),
            {
                "event_type": "revision_disposition",
                "candidate_version_id": "nls_v3_rc_0024",
                "disposition": "current_pending_rerun",
                "decision_receipt_commitment": _commitment("rc24:pending"),
            },
        ]
    )
    return events, manifests, summaries, rc22, rc23, rc23_summary


def test_rc0024_versions_and_frozen_rc0023_constants_are_explicit() -> None:
    assert STEP11_HISTORICAL_RC0023_CANDIDATE_VERSION_ID == "nls_v3_rc_0023"
    assert STEP11_CURRENT_CANDIDATE_VERSION_ID == "nls_v3_rc_0024"
    assert STEP11_HISTORICAL_RC0023_RUNTIME_ADAPTER_VERSION.endswith(
        ".rc0023.v1"
    )
    assert RC_CORRECTION_RERUN_LINEAGE_V6_SCHEMA.endswith(".v6")
    assert RC_CORRECTION_RERUN_LINEAGE_EVENT_V6_SCHEMA.endswith(".v6")
    assert FROZEN_RC0023_FORMAL_MANIFEST_ARTIFACT_SHA256 == (
        "c98ffd8fd6da6e74d7811d5ee272bc469321e36f03d3c48b711a15095218b57e"
    )
    assert FROZEN_RC0023_FORMAL_SOURCE_CLOSURE_SHA256 == (
        "83c220fa71f4d22549e94b9733918892a3c532367aa4075f268e1bb3eca48e92"
    )
    assert FROZEN_RC0023_FORMAL_BATCH_SUMMARY_SHA256 == (
        "d5edd618b53a488de53ad2ffb4ca5f6c4e0b4eff634d7639dc023fc7dbec9c57"
    )
    assert FROZEN_RC0023_FORMAL_PRIVATE_VERIFICATION_SHA256 == (
        "26747b6166babceadc23c51ef67f8b53abdb60b7af4a4c565aaa6052d63c051e"
    )


def test_rc0024_lineage_preserves_rc22_failure_and_rc23_clean_execution(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    events, manifests, summaries, _, _, _ = _rc0024_material(monkeypatch)

    lineage = build_rc0010_rc0024_correction_rerun_lineage(
        events,
        dependency_manifests=manifests,
        batch_run_summaries=summaries,
    )

    assert lineage["schema_version"] == RC_CORRECTION_RERUN_LINEAGE_V6_SCHEMA
    assert lineage["current_candidate_version_id"] == "nls_v3_rc_0024"
    assert lineage["acceptance_lineage_ready"] is False
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
    assert rc22_execution["no_valid_candidate_count"] == 5
    assert rc22_execution["exception_count"] == 95

    rc23_execution = next(
        row
        for row in lineage["events"]
        if row["event_type"] == "execution_observed"
        and row["candidate_version_id"] == "nls_v3_rc_0023"
    )
    assert rc23_execution["execution_scope"] == "formal_cumulative_rerun"
    assert rc23_execution["machine_status"] == "clean"
    assert rc23_execution["executed_case_count"] == 100
    assert rc23_execution["selected_count"] == 100
    assert rc23_execution["no_valid_candidate_count"] == 0
    assert rc23_execution["exception_count"] == 0
    assert rc23_execution["counts_as_clean_formal_rerun"] is True
    rc23_disposition = next(
        row
        for row in lineage["events"]
        if row["event_type"] == "revision_disposition"
        and row["candidate_version_id"] == "nls_v3_rc_0023"
    )
    assert rc23_disposition["disposition"] == (
        "superseded_after_observed_result"
    )
    assert rc23_disposition["counts_as_passed_rerun"] is False

    rc24_correction = next(
        row
        for row in lineage["events"]
        if row["event_type"] == "correction_recorded"
        and row["candidate_version_id"] == "nls_v3_rc_0024"
    )
    assert rc24_correction["dependency_diff_base_candidate_version_id"] == (
        "nls_v3_rc_0023"
    )
    assert validate_rc0010_rc0024_correction_rerun_lineage(
        lineage,
        dependency_manifests=manifests,
        batch_run_summaries=summaries,
    ) == ()


@pytest.mark.parametrize(
    "mutation",
    ("remove_execution", "relabel_failed", "claim_unexecuted"),
)
def test_rc0024_rejects_erased_or_relabelled_rc0023_clean_execution(
    monkeypatch: pytest.MonkeyPatch,
    mutation: str,
) -> None:
    events, manifests, summaries, _, _, rc23_summary = _rc0024_material(
        monkeypatch
    )
    if mutation == "remove_execution":
        events[:] = [
            row
            for row in events
            if not (
                row["event_type"] == "execution_observed"
                and row["candidate_version_id"] == "nls_v3_rc_0023"
            )
        ]
    elif mutation == "relabel_failed":
        rc23_summary["machine_status"] = "failed"
        rc23_summary["aggregate"]["selected_count"] = 0
        rc23_summary["aggregate"]["exception_count"] = 100
        for row in rc23_summary["case_rows"]:
            row["status"] = "exception"
    else:
        disposition = next(
            row
            for row in events
            if row["event_type"] == "revision_disposition"
            and row["candidate_version_id"] == "nls_v3_rc_0023"
        )
        disposition["disposition"] = "superseded_unexecuted"

    with pytest.raises(Step11CycleEvidenceError):
        build_rc0010_rc0024_correction_rerun_lineage(
            events,
            dependency_manifests=manifests,
            batch_run_summaries=summaries,
        )


def test_rc0024_requires_immediate_exact_rc0023_parent(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    events, manifests, summaries, _, rc23, _ = _rc0024_material(monkeypatch)
    forged_row = {
        "path": "ai/tests/forged_rc0024_owner.py",
        "sha256": _commitment("forged:rc24-owner"),
    }
    forged = build_step11_dependency_manifest(
        before_candidate_version_id="nls_v3_rc_0022",
        before_source_closure_sha256=rc23["before_source_closure_sha256"],
        candidate_version_id="nls_v3_rc_0024",
        file_hashes=[forged_row],
        changed_file_hashes=[forged_row],
    )
    manifests[-1] = forged
    correction = next(
        row
        for row in events
        if row["event_type"] == "correction_recorded"
        and row["candidate_version_id"] == "nls_v3_rc_0024"
    )
    correction["source_state_artifact_sha256"] = artifact_sha256(forged)
    correction["changed_file_set_commitment"] = artifact_sha256(
        forged["changed_file_hashes"]
    )

    with pytest.raises(
        Step11CycleEvidenceError,
        match="RC_LINEAGE_FINAL_DEPENDENCY_BASE_INVALID",
    ):
        build_rc0010_rc0024_correction_rerun_lineage(
            events,
            dependency_manifests=manifests,
            batch_run_summaries=summaries,
        )


def test_rc0024_dependency_manifest_is_exact_diff_from_frozen_rc0023(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    rows = [
        {
            "path": f"ai/tests/frozen_rc0023/path_{index:03d}.py",
            "sha256": _commitment(f"rc23:{index}"),
        }
        for index in range(145)
    ]
    rc23 = build_step11_dependency_manifest(
        before_candidate_version_id="nls_v3_rc_0022",
        before_source_closure_sha256=_commitment("rc22"),
        candidate_version_id="nls_v3_rc_0023",
        file_hashes=rows,
        changed_file_hashes=rows[:1],
    )
    changed_path = rows[35]["path"]
    current = {row["path"]: row["sha256"] for row in rows}
    current[changed_path] = _commitment("rc24:changed")
    for path in _RC0024_ADDED_PATHS:
        current[path] = _commitment(f"rc24:{path}")
    monkeypatch.setattr(
        dependency_tool,
        "FROZEN_RC0023_FORMAL_MANIFEST_ARTIFACT_SHA256",
        artifact_sha256(rc23),
    )
    monkeypatch.setattr(
        dependency_tool,
        "FROZEN_RC0023_FORMAL_SOURCE_CLOSURE_SHA256",
        rc23["source_dependency_closure_sha256"],
    )
    monkeypatch.setattr(
        dependency_tool,
        "FROZEN_RC0022_FORMAL_SOURCE_CLOSURE_SHA256",
        rc23["before_source_closure_sha256"],
    )
    monkeypatch.setattr(
        dependency_tool,
        "STEP11_CANDIDATE_VERSION_ID",
        STEP11_CURRENT_CANDIDATE_VERSION_ID,
    )
    monkeypatch.setattr(dependency_tool, "_sha256", lambda path: current[path])

    assert dependency_tool.RC0024_ADDED_SOURCE_PATHS == _RC0024_ADDED_PATHS
    result = dependency_tool.build_current_step11_dependency_manifest(rc23)

    assert result["before_candidate_version_id"] == "nls_v3_rc_0023"
    assert result["before_source_closure_sha256"] == rc23[
        "source_dependency_closure_sha256"
    ]
    assert result["candidate_version_id"] == "nls_v3_rc_0024"
    assert len(result["file_hashes"]) == 148
    assert {row["path"] for row in result["changed_file_hashes"]} == {
        changed_path,
        *_RC0024_ADDED_PATHS,
    }
