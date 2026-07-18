# -*- coding: utf-8 -*-
from __future__ import annotations

"""Append-only rc0023 lineage and exact failed-rc0022 parent REDs."""

from copy import deepcopy
from typing import Any

import pytest

from emlis_ai_nls_v3_artifact_contract import artifact_sha256
from emlis_ai_step11_cycle_evidence_v3 import (
    FROZEN_RC0022_FORMAL_BATCH_SUMMARY_SHA256,
    FROZEN_RC0022_FORMAL_MANIFEST_ARTIFACT_SHA256,
    FROZEN_RC0022_FORMAL_PRIVATE_VERIFICATION_SHA256,
    FROZEN_RC0022_FORMAL_SOURCE_CLOSURE_SHA256,
    RC_CORRECTION_RERUN_LINEAGE_EVENT_V5_SCHEMA,
    RC_CORRECTION_RERUN_LINEAGE_V5_SCHEMA,
    STEP11_HISTORICAL_RC0022_CANDIDATE_VERSION_ID,
    STEP11_HISTORICAL_RC0023_CANDIDATE_VERSION_ID,
    STEP11_HISTORICAL_RC0022_RUNTIME_ADAPTER_VERSION,
    Step11CycleEvidenceError,
    build_rc0010_rc0023_correction_rerun_lineage,
    build_step11_dependency_manifest,
    validate_rc0010_rc0023_correction_rerun_lineage,
)
import emlis_ai_step11_cycle_evidence_v3 as cycle_evidence
import emlis_nls_v3_step11_dependency_manifest as dependency_tool
from test_emlis_nls_v3_s11_rc0021_append_only_lineage import (
    _commitment,
    _correction,
    _summary,
)
from test_emlis_nls_v3_s11_rc0022_append_only_lineage import (
    _rc0022_material,
)


def _failed_rc0022_summary(
    manifest: dict[str, Any],
) -> dict[str, Any]:
    closure = manifest["source_dependency_closure_sha256"]
    summary = deepcopy(_summary("nls_v3_rc_0022", closure))
    summary["dependency_manifest_sha256"] = artifact_sha256(manifest)
    summary["source_closure_start_sha256"] = closure
    summary["source_closure_end_sha256"] = closure
    summary["source_closure_stable"] = True
    summary["machine_status"] = "failed"
    summary["aggregate"]["selected_count"] = 0
    summary["aggregate"]["no_valid_candidate_count"] = 5
    summary["aggregate"]["exception_count"] = 95
    summary["aggregate"]["v1_fallback_count"] = 0
    for index, row in enumerate(summary["case_rows"]):
        row["status"] = (
            "exception" if index < 95 else "v3_no_valid_candidate"
        )
    return summary


def _rc0023_material(
    monkeypatch: pytest.MonkeyPatch,
) -> tuple[
    list[dict[str, Any]],
    list[dict[str, Any]],
    list[dict[str, Any]],
    dict[str, Any],
    dict[str, Any],
]:
    events, manifests, summaries, rc21, _ = _rc0022_material(monkeypatch)
    rc22_rows = [
        {
            "path": f"ai/tests/frozen_rc0022/path_{index:03d}.py",
            "sha256": _commitment(f"rc22:{index}"),
        }
        for index in range(141)
    ]
    rc22 = build_step11_dependency_manifest(
        before_candidate_version_id="nls_v3_rc_0021",
        before_source_closure_sha256=rc21[
            "source_dependency_closure_sha256"
        ],
        candidate_version_id="nls_v3_rc_0022",
        file_hashes=rc22_rows,
        changed_file_hashes=rc22_rows[:1],
    )
    manifests[-1] = rc22
    rc22_correction = next(
        row
        for row in events
        if row["event_type"] == "correction_recorded"
        and row["candidate_version_id"] == "nls_v3_rc_0022"
    )
    rc22_correction["source_state_artifact_sha256"] = artifact_sha256(rc22)
    rc22_correction["changed_file_set_commitment"] = artifact_sha256(
        rc22["changed_file_hashes"]
    )

    rc22_summary = _failed_rc0022_summary(rc22)
    summaries.append(rc22_summary)
    monkeypatch.setattr(
        cycle_evidence,
        "FROZEN_RC0022_FORMAL_MANIFEST_ARTIFACT_SHA256",
        artifact_sha256(rc22),
    )
    monkeypatch.setattr(
        cycle_evidence,
        "FROZEN_RC0022_FORMAL_SOURCE_CLOSURE_SHA256",
        rc22["source_dependency_closure_sha256"],
    )
    monkeypatch.setattr(
        cycle_evidence,
        "FROZEN_RC0022_FORMAL_BATCH_SUMMARY_SHA256",
        artifact_sha256(rc22_summary),
    )

    rc22_pending_index = next(
        index
        for index, row in enumerate(events)
        if row["event_type"] == "revision_disposition"
        and row["candidate_version_id"] == "nls_v3_rc_0022"
    )
    events[rc22_pending_index : rc22_pending_index + 1] = [
        {
            "event_type": "execution_observed",
            "candidate_version_id": "nls_v3_rc_0022",
            "execution_scope": "formal_cumulative_rerun",
            "batch_summary_sha256": artifact_sha256(rc22_summary),
        },
        {
            "event_type": "revision_disposition",
            "candidate_version_id": "nls_v3_rc_0022",
            "disposition": "superseded_after_observed_result",
            "decision_receipt_commitment": _commitment("rc22:superseded"),
        },
    ]

    rc23 = build_step11_dependency_manifest(
        before_candidate_version_id="nls_v3_rc_0022",
        before_source_closure_sha256=rc22[
            "source_dependency_closure_sha256"
        ],
        candidate_version_id="nls_v3_rc_0023",
        file_hashes=[
            {
                "path": "ai/tests/rc0023_common_owner.py",
                "sha256": _commitment("rc23:owner"),
            }
        ],
        changed_file_hashes=[
            {
                "path": "ai/tests/rc0023_common_owner.py",
                "sha256": _commitment("rc23:owner"),
            }
        ],
    )
    manifests.append(rc23)
    events.extend(
        [
            _correction("nls_v3_rc_0023", rc23),
            {
                "event_type": "revision_disposition",
                "candidate_version_id": "nls_v3_rc_0023",
                "disposition": "current_pending_rerun",
                "decision_receipt_commitment": _commitment("rc23:pending"),
            },
        ]
    )
    return events, manifests, summaries, rc22, rc22_summary


def test_rc0023_versions_and_frozen_rc0022_constants_are_explicit() -> None:
    assert STEP11_HISTORICAL_RC0022_CANDIDATE_VERSION_ID == "nls_v3_rc_0022"
    assert STEP11_HISTORICAL_RC0023_CANDIDATE_VERSION_ID == "nls_v3_rc_0023"
    assert STEP11_HISTORICAL_RC0022_RUNTIME_ADAPTER_VERSION.endswith(
        ".rc0022.v1"
    )
    assert RC_CORRECTION_RERUN_LINEAGE_V5_SCHEMA.endswith(".v5")
    assert RC_CORRECTION_RERUN_LINEAGE_EVENT_V5_SCHEMA.endswith(".v5")
    assert FROZEN_RC0022_FORMAL_MANIFEST_ARTIFACT_SHA256 == (
        "a6f691e09b20c31302a30b239b255fa302dd1d94892fedc894d6c45fd36274df"
    )
    assert FROZEN_RC0022_FORMAL_SOURCE_CLOSURE_SHA256 == (
        "252b83e41b9f77e3ffb38041471f00a22946443119dff3c26524230ac60b1783"
    )
    assert FROZEN_RC0022_FORMAL_BATCH_SUMMARY_SHA256 == (
        "7db9feeb6b7d6a41f54ce0d7a27bb3fbafade2cd60f0c5f89745172d8f5f5c06"
    )
    assert FROZEN_RC0022_FORMAL_PRIVATE_VERIFICATION_SHA256 == (
        "ab12f6e1d437f7ab3d04093c08873c5d65141061a45d7836284a90ff79095a87"
    )


def test_rc0023_lineage_preserves_failed_rc0022_execution(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    events, manifests, summaries, _, _ = _rc0023_material(monkeypatch)

    lineage = build_rc0010_rc0023_correction_rerun_lineage(
        events,
        dependency_manifests=manifests,
        batch_run_summaries=summaries,
    )

    assert lineage["schema_version"] == RC_CORRECTION_RERUN_LINEAGE_V5_SCHEMA
    assert lineage["current_candidate_version_id"] == "nls_v3_rc_0023"
    assert lineage["acceptance_lineage_ready"] is False
    assert lineage["failed_product_read_candidate_sequence"] == [
        "nls_v3_rc_0020",
        "nls_v3_rc_0021",
    ]
    assert lineage["failed_machine_execution_candidate_sequence"] == [
        "nls_v3_rc_0022"
    ]
    rc22_execution = next(
        row
        for row in lineage["events"]
        if row["event_type"] == "execution_observed"
        and row["candidate_version_id"] == "nls_v3_rc_0022"
    )
    assert rc22_execution["execution_scope"] == "formal_cumulative_rerun"
    assert rc22_execution["machine_status"] == "failed"
    assert rc22_execution["executed_case_count"] == 100
    assert rc22_execution["selected_count"] == 0
    assert rc22_execution["no_valid_candidate_count"] == 5
    assert rc22_execution["exception_count"] == 95
    assert rc22_execution["counts_as_clean_formal_rerun"] is False
    rc22_disposition = next(
        row
        for row in lineage["events"]
        if row["event_type"] == "revision_disposition"
        and row["candidate_version_id"] == "nls_v3_rc_0022"
    )
    assert rc22_disposition["disposition"] == (
        "superseded_after_observed_result"
    )
    assert rc22_disposition["failed_machine_execution_observed"] is True
    assert rc22_disposition["counts_as_passed_rerun"] is False
    assert lineage["aggregate"]["failed_machine_execution_count"] == 1
    assert validate_rc0010_rc0023_correction_rerun_lineage(
        lineage,
        dependency_manifests=manifests,
        batch_run_summaries=summaries,
    ) == ()


@pytest.mark.parametrize(
    "mutation",
    ("remove_execution", "relabel_clean", "claim_unexecuted"),
)
def test_rc0023_rejects_erased_or_relabelled_rc0022_machine_failure(
    monkeypatch: pytest.MonkeyPatch,
    mutation: str,
) -> None:
    events, manifests, summaries, _, rc22_summary = _rc0023_material(
        monkeypatch
    )
    if mutation == "remove_execution":
        events[:] = [
            row
            for row in events
            if not (
                row["event_type"] == "execution_observed"
                and row["candidate_version_id"] == "nls_v3_rc_0022"
            )
        ]
    elif mutation == "relabel_clean":
        rc22_summary["machine_status"] = "clean"
        rc22_summary["aggregate"]["selected_count"] = 100
        rc22_summary["aggregate"]["no_valid_candidate_count"] = 0
        rc22_summary["aggregate"]["exception_count"] = 0
        for row in rc22_summary["case_rows"]:
            row["status"] = "selected"
    else:
        disposition = next(
            row
            for row in events
            if row["event_type"] == "revision_disposition"
            and row["candidate_version_id"] == "nls_v3_rc_0022"
        )
        disposition["disposition"] = "superseded_unexecuted"

    with pytest.raises(Step11CycleEvidenceError):
        build_rc0010_rc0023_correction_rerun_lineage(
            events,
            dependency_manifests=manifests,
            batch_run_summaries=summaries,
        )


def test_rc0023_requires_immediate_exact_rc0022_parent(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    events, manifests, summaries, rc22, _ = _rc0023_material(monkeypatch)
    forged = build_step11_dependency_manifest(
        before_candidate_version_id="nls_v3_rc_0021",
        before_source_closure_sha256=rc22["before_source_closure_sha256"],
        candidate_version_id="nls_v3_rc_0023",
        file_hashes=[
            {
                "path": "ai/tests/forged_rc0023_owner.py",
                "sha256": _commitment("forged:owner"),
            }
        ],
        changed_file_hashes=[
            {
                "path": "ai/tests/forged_rc0023_owner.py",
                "sha256": _commitment("forged:owner"),
            }
        ],
    )
    manifests[-1] = forged
    correction = next(
        row
        for row in events
        if row["event_type"] == "correction_recorded"
        and row["candidate_version_id"] == "nls_v3_rc_0023"
    )
    correction["source_state_artifact_sha256"] = artifact_sha256(forged)
    correction["changed_file_set_commitment"] = artifact_sha256(
        forged["changed_file_hashes"]
    )

    with pytest.raises(
        Step11CycleEvidenceError,
        match="RC_LINEAGE_FINAL_DEPENDENCY_BASE_INVALID",
    ):
        build_rc0010_rc0023_correction_rerun_lineage(
            events,
            dependency_manifests=manifests,
            batch_run_summaries=summaries,
        )


def test_rc0023_dependency_manifest_is_exact_diff_from_frozen_rc0022(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    rows = [
        {
            "path": f"ai/tests/frozen_rc0022/path_{index:03d}.py",
            "sha256": _commitment(f"rc22:{index}"),
        }
        for index in range(141)
    ]
    rc22 = build_step11_dependency_manifest(
        before_candidate_version_id="nls_v3_rc_0021",
        before_source_closure_sha256=_commitment("rc21"),
        candidate_version_id="nls_v3_rc_0022",
        file_hashes=rows,
        changed_file_hashes=rows[:1],
    )
    changed_path = rows[35]["path"]
    current = {row["path"]: row["sha256"] for row in rows}
    current[changed_path] = _commitment("rc23:changed")
    for path in dependency_tool.RC0023_ADDED_SOURCE_PATHS:
        current[path] = _commitment(f"rc23:{path}")
    monkeypatch.setattr(
        dependency_tool,
        "FROZEN_RC0022_FORMAL_MANIFEST_ARTIFACT_SHA256",
        artifact_sha256(rc22),
    )
    monkeypatch.setattr(
        dependency_tool,
        "FROZEN_RC0022_FORMAL_SOURCE_CLOSURE_SHA256",
        rc22["source_dependency_closure_sha256"],
    )
    monkeypatch.setattr(
        dependency_tool,
        "FROZEN_RC0021_PREFLIGHT_SOURCE_CLOSURE_SHA256",
        rc22["before_source_closure_sha256"],
    )
    monkeypatch.setattr(
        dependency_tool,
        "STEP11_CANDIDATE_VERSION_ID",
        STEP11_HISTORICAL_RC0023_CANDIDATE_VERSION_ID,
    )
    monkeypatch.setattr(dependency_tool, "_sha256", lambda path: current[path])

    result = dependency_tool.build_current_step11_dependency_manifest(rc22)

    assert result["before_candidate_version_id"] == "nls_v3_rc_0022"
    assert result["before_source_closure_sha256"] == rc22[
        "source_dependency_closure_sha256"
    ]
    assert result["candidate_version_id"] == "nls_v3_rc_0023"
    assert len(result["file_hashes"]) == 145
    assert {row["path"] for row in result["changed_file_hashes"]} == {
        changed_path,
        *dependency_tool.RC0023_ADDED_SOURCE_PATHS,
    }
