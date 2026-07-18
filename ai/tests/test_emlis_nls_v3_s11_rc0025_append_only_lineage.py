# -*- coding: utf-8 -*-
from __future__ import annotations

"""Append-only rc0025 lineage and exact clean-rc0024 parent contracts."""

from copy import deepcopy
from typing import Any

import pytest

from emlis_ai_nls_v3_artifact_contract import artifact_sha256
from emlis_ai_step11_cycle_evidence_v3 import (
    FROZEN_RC0024_FORMAL_BATCH_SUMMARY_SHA256,
    FROZEN_RC0024_FORMAL_MANIFEST_ARTIFACT_SHA256,
    FROZEN_RC0024_FORMAL_PRIVATE_VERIFICATION_SHA256,
    FROZEN_RC0024_FORMAL_SOURCE_CLOSURE_SHA256,
    RC_CORRECTION_RERUN_LINEAGE_EVENT_V7_SCHEMA,
    RC_CORRECTION_RERUN_LINEAGE_V7_SCHEMA,
    STEP11_CURRENT_CANDIDATE_VERSION_ID,
    STEP11_HISTORICAL_RC0024_CANDIDATE_VERSION_ID,
    STEP11_HISTORICAL_RC0024_RUNTIME_ADAPTER_VERSION,
    Step11CycleEvidenceError,
    build_rc0010_rc0025_correction_rerun_lineage,
    build_step11_dependency_manifest,
    validate_rc0010_rc0025_correction_rerun_lineage,
)
import emlis_ai_step11_cycle_evidence_v3 as cycle_evidence
import emlis_nls_v3_step11_dependency_manifest as dependency_tool
from test_emlis_nls_v3_s11_rc0021_append_only_lineage import (
    _commitment,
    _correction,
)
from test_emlis_nls_v3_s11_rc0024_append_only_lineage import (
    _clean_summary,
    _rc0024_material,
)


_RC0025_ADDED_PATHS = (
    "ai/tests/test_emlis_ai_nls_v3_rc0025_v1_surface_regression.py",
    "ai/tests/test_emlis_nls_v3_s11_rc0025_append_only_lineage.py",
    "ai/tests/test_emlis_nls_v3_s11_rc0025_cycle_finalize.py",
)


def _rc0025_material(
    monkeypatch: pytest.MonkeyPatch,
) -> tuple[
    list[dict[str, Any]],
    list[dict[str, Any]],
    list[dict[str, Any]],
    dict[str, Any],
    dict[str, Any],
]:
    events, manifests, summaries, _, rc23, _ = _rc0024_material(monkeypatch)
    rc24_rows = [
        {
            "path": f"ai/tests/frozen_rc0024/path_{index:03d}.py",
            "sha256": _commitment(f"rc24:{index}"),
        }
        for index in range(148)
    ]
    rc24 = build_step11_dependency_manifest(
        before_candidate_version_id="nls_v3_rc_0023",
        before_source_closure_sha256=rc23[
            "source_dependency_closure_sha256"
        ],
        candidate_version_id="nls_v3_rc_0024",
        file_hashes=rc24_rows,
        changed_file_hashes=rc24_rows[:1],
    )
    manifests[-1] = rc24
    rc24_correction = next(
        row
        for row in events
        if row["event_type"] == "correction_recorded"
        and row["candidate_version_id"] == "nls_v3_rc_0024"
    )
    rc24_correction["source_state_artifact_sha256"] = artifact_sha256(rc24)
    rc24_correction["changed_file_set_commitment"] = artifact_sha256(
        rc24["changed_file_hashes"]
    )
    rc24_summary = _clean_summary("nls_v3_rc_0024", rc24)
    summaries.append(rc24_summary)
    monkeypatch.setattr(
        cycle_evidence,
        "FROZEN_RC0024_FORMAL_MANIFEST_ARTIFACT_SHA256",
        artifact_sha256(rc24),
    )
    monkeypatch.setattr(
        cycle_evidence,
        "FROZEN_RC0024_FORMAL_SOURCE_CLOSURE_SHA256",
        rc24["source_dependency_closure_sha256"],
    )
    monkeypatch.setattr(
        cycle_evidence,
        "FROZEN_RC0024_FORMAL_BATCH_SUMMARY_SHA256",
        artifact_sha256(rc24_summary),
    )

    rc24_pending_index = next(
        index
        for index, row in enumerate(events)
        if row["event_type"] == "revision_disposition"
        and row["candidate_version_id"] == "nls_v3_rc_0024"
    )
    events[rc24_pending_index : rc24_pending_index + 1] = [
        {
            "event_type": "execution_observed",
            "candidate_version_id": "nls_v3_rc_0024",
            "execution_scope": "formal_cumulative_rerun",
            "batch_summary_sha256": artifact_sha256(rc24_summary),
        },
        {
            "event_type": "revision_disposition",
            "candidate_version_id": "nls_v3_rc_0024",
            "disposition": "superseded_after_observed_result",
            "decision_receipt_commitment": _commitment("rc24:superseded"),
        },
    ]

    rc25_row = {
        "path": "ai/tests/rc0025_common_owner.py",
        "sha256": _commitment("rc25:owner"),
    }
    rc25 = build_step11_dependency_manifest(
        before_candidate_version_id="nls_v3_rc_0024",
        before_source_closure_sha256=rc24[
            "source_dependency_closure_sha256"
        ],
        candidate_version_id="nls_v3_rc_0025",
        file_hashes=[rc25_row],
        changed_file_hashes=[rc25_row],
    )
    manifests.append(rc25)
    events.extend(
        [
            _correction("nls_v3_rc_0025", rc25),
            {
                "event_type": "revision_disposition",
                "candidate_version_id": "nls_v3_rc_0025",
                "disposition": "current_pending_rerun",
                "decision_receipt_commitment": _commitment("rc25:pending"),
            },
        ]
    )
    return events, manifests, summaries, rc24, rc24_summary


def test_rc0025_versions_and_frozen_rc0024_constants_are_explicit() -> None:
    assert STEP11_HISTORICAL_RC0024_CANDIDATE_VERSION_ID == "nls_v3_rc_0024"
    assert STEP11_CURRENT_CANDIDATE_VERSION_ID == "nls_v3_rc_0025"
    assert STEP11_HISTORICAL_RC0024_RUNTIME_ADAPTER_VERSION.endswith(
        ".rc0024.v1"
    )
    assert RC_CORRECTION_RERUN_LINEAGE_V7_SCHEMA.endswith(".v7")
    assert RC_CORRECTION_RERUN_LINEAGE_EVENT_V7_SCHEMA.endswith(".v7")
    assert FROZEN_RC0024_FORMAL_MANIFEST_ARTIFACT_SHA256 == (
        "bbe785c144ac0e721aa8887b0f49848b104f65e6c2820a2f62b7f7d4ed3ac811"
    )
    assert FROZEN_RC0024_FORMAL_SOURCE_CLOSURE_SHA256 == (
        "fa52aa55627dbeada60c5fe2187a7551cd4ab0c72fde289157a82945c0c6467d"
    )
    assert FROZEN_RC0024_FORMAL_BATCH_SUMMARY_SHA256 == (
        "de09a19ef35b1fbbab78ae6417b0e23f7b0e3701b71fbf58d07bed79aa449534"
    )
    assert FROZEN_RC0024_FORMAL_PRIVATE_VERIFICATION_SHA256 == (
        "355c412df6e1e21c07ffad37aef077db7fd80bd096b3905e64e1fde9ca4c58e8"
    )


def test_rc0025_lineage_preserves_rc0024_clean_execution(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    events, manifests, summaries, _, _ = _rc0025_material(monkeypatch)

    lineage = build_rc0010_rc0025_correction_rerun_lineage(
        events,
        dependency_manifests=manifests,
        batch_run_summaries=summaries,
    )

    assert lineage["schema_version"] == RC_CORRECTION_RERUN_LINEAGE_V7_SCHEMA
    assert lineage["current_candidate_version_id"] == "nls_v3_rc_0025"
    assert lineage["acceptance_lineage_ready"] is False
    assert lineage["failed_machine_execution_candidate_sequence"] == [
        "nls_v3_rc_0022"
    ]
    rc24_execution = next(
        row
        for row in lineage["events"]
        if row["event_type"] == "execution_observed"
        and row["candidate_version_id"] == "nls_v3_rc_0024"
    )
    assert rc24_execution["execution_scope"] == "formal_cumulative_rerun"
    assert rc24_execution["machine_status"] == "clean"
    assert rc24_execution["executed_case_count"] == 100
    assert rc24_execution["selected_count"] == 100
    assert rc24_execution["no_valid_candidate_count"] == 0
    assert rc24_execution["exception_count"] == 0
    rc24_disposition = next(
        row
        for row in lineage["events"]
        if row["event_type"] == "revision_disposition"
        and row["candidate_version_id"] == "nls_v3_rc_0024"
    )
    assert rc24_disposition["disposition"] == (
        "superseded_after_observed_result"
    )
    rc25_correction = next(
        row
        for row in lineage["events"]
        if row["event_type"] == "correction_recorded"
        and row["candidate_version_id"] == "nls_v3_rc_0025"
    )
    assert rc25_correction["dependency_diff_base_candidate_version_id"] == (
        "nls_v3_rc_0024"
    )
    assert validate_rc0010_rc0025_correction_rerun_lineage(
        lineage,
        dependency_manifests=manifests,
        batch_run_summaries=summaries,
    ) == ()


def test_rc0025_lineage_rejects_relabelled_rc0024_parent(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    events, manifests, summaries, _, rc24_summary = _rc0025_material(
        monkeypatch
    )
    rc24_summary["machine_status"] = "failed"
    rc24_summary["aggregate"]["selected_count"] = 0
    rc24_summary["aggregate"]["exception_count"] = 100
    for row in rc24_summary["case_rows"]:
        row["status"] = "exception"

    with pytest.raises(Step11CycleEvidenceError):
        build_rc0010_rc0025_correction_rerun_lineage(
            events,
            dependency_manifests=manifests,
            batch_run_summaries=summaries,
        )


def test_rc0025_manifest_is_exact_148_plus_3_successor(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    rows = [
        {
            "path": f"ai/tests/frozen_rc0024/path_{index:03d}.py",
            "sha256": _commitment(f"rc24:{index}"),
        }
        for index in range(148)
    ]
    rc24 = build_step11_dependency_manifest(
        before_candidate_version_id="nls_v3_rc_0023",
        before_source_closure_sha256=_commitment("rc23"),
        candidate_version_id="nls_v3_rc_0024",
        file_hashes=rows,
        changed_file_hashes=rows[:1],
    )
    frozen_rc24 = deepcopy(rc24)
    changed_path = rows[35]["path"]
    current = {row["path"]: row["sha256"] for row in rows}
    current[changed_path] = _commitment("rc25:changed")
    for path in _RC0025_ADDED_PATHS:
        current[path] = _commitment(f"rc25:{path}")
    monkeypatch.setattr(
        dependency_tool,
        "FROZEN_RC0024_FORMAL_MANIFEST_ARTIFACT_SHA256",
        artifact_sha256(rc24),
    )
    monkeypatch.setattr(
        dependency_tool,
        "FROZEN_RC0024_FORMAL_SOURCE_CLOSURE_SHA256",
        rc24["source_dependency_closure_sha256"],
    )
    monkeypatch.setattr(
        dependency_tool,
        "FROZEN_RC0023_FORMAL_SOURCE_CLOSURE_SHA256",
        rc24["before_source_closure_sha256"],
    )
    monkeypatch.setattr(
        dependency_tool,
        "STEP11_CANDIDATE_VERSION_ID",
        STEP11_CURRENT_CANDIDATE_VERSION_ID,
    )
    monkeypatch.setattr(dependency_tool, "_sha256", lambda path: current[path])

    assert dependency_tool.RC0025_ADDED_SOURCE_PATHS == _RC0025_ADDED_PATHS
    result = dependency_tool.build_current_step11_dependency_manifest(rc24)

    assert rc24 == frozen_rc24
    assert result["before_candidate_version_id"] == "nls_v3_rc_0024"
    assert result["before_source_closure_sha256"] == rc24[
        "source_dependency_closure_sha256"
    ]
    assert result["candidate_version_id"] == "nls_v3_rc_0025"
    assert len(rc24["file_hashes"]) == 148
    assert len(result["file_hashes"]) == 151
    assert {row["path"] for row in result["changed_file_hashes"]} == {
        changed_path,
        *_RC0025_ADDED_PATHS,
    }
