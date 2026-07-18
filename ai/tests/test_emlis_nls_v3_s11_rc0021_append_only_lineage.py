# -*- coding: utf-8 -*-
from __future__ import annotations

"""Append-only rc0021 lineage and exact rc0020-parent REDs."""

from copy import deepcopy
import hashlib
import json
from pathlib import Path
from typing import Any

import pytest

from emlis_ai_nls_v3_artifact_contract import artifact_sha256
from emlis_ai_step11_cycle_evidence_v3 import (
    RC_CORRECTION_RERUN_LINEAGE_EVENT_V3_SCHEMA,
    RC_CORRECTION_RERUN_LINEAGE_V3_SCHEMA,
    STEP11_HISTORICAL_RC0020_CANDIDATE_VERSION_ID,
    STEP11_HISTORICAL_RC0021_CANDIDATE_VERSION_ID,
    STEP11_HISTORICAL_RC0021_RUNTIME_ADAPTER_VERSION,
    Step11CycleEvidenceError,
    build_rc0010_rc0021_correction_rerun_lineage,
    build_step11_dependency_manifest,
    validate_rc0010_rc0021_correction_rerun_lineage,
)
import emlis_ai_step11_cycle_evidence_v3 as cycle_evidence
import emlis_nls_v3_step11_dependency_manifest as dependency_tool


_CYCLE = Path(__file__).resolve().parent / "fixtures" / "emlis_nls_v3" / "cycle_001"


def _json(name: str) -> dict[str, Any]:
    return json.loads((_CYCLE / name).read_text(encoding="utf-8"))


def _commitment(label: str) -> str:
    return hashlib.sha256(label.encode("utf-8")).hexdigest()


def _manifest(
    candidate: str,
    *,
    before_candidate: str,
    before_closure: str,
) -> dict[str, Any]:
    changed = [
        {
            "path": f"ai/tests/{candidate}_common_owner.py",
            "sha256": _commitment(f"{candidate}:owner"),
        }
    ]
    return build_step11_dependency_manifest(
        before_candidate_version_id=before_candidate,
        before_source_closure_sha256=before_closure,
        candidate_version_id=candidate,
        file_hashes=changed,
        changed_file_hashes=changed,
    )


def _summary(candidate: str, closure: str) -> dict[str, Any]:
    value = deepcopy(_json("cycle001_final_rc0016_summary.json"))
    value["candidate_version_id"] = candidate
    value["run_id"] = f"nls3run_{candidate[-4:]}c001{candidate[-1] * 8}"
    value["source_dependency_closure_sha256"] = closure
    value["machine_status"] = "clean"
    value["all_expected_cases_executed"] = True
    value["executed_case_count"] = 100
    value["aggregate"]["selected_count"] = 100
    value["aggregate"]["no_valid_candidate_count"] = 0
    value["aggregate"]["exception_count"] = 0
    value["aggregate"]["v1_fallback_count"] = 0
    for row in value["case_rows"]:
        row["status"] = "selected"
    return value


def _correction(
    candidate: str,
    manifest: dict[str, Any] | None,
) -> dict[str, Any]:
    source_kind = (
        "dependency_manifest"
        if manifest is not None
        else "historical_unfrozen_no_receipt"
    )
    return {
        "event_type": "correction_recorded",
        "candidate_version_id": candidate,
        "source_state_kind": source_kind,
        "source_state_artifact_sha256": (
            artifact_sha256(manifest)
            if manifest is not None
            else _commitment(f"{candidate}:source")
        ),
        "failure_evidence_commitment": _commitment(f"{candidate}:failure"),
        "structural_hypothesis_commitment": _commitment(
            f"{candidate}:hypothesis"
        ),
        "changed_file_set_commitment": (
            artifact_sha256(manifest["changed_file_hashes"])
            if manifest is not None
            else _commitment(f"{candidate}:changed")
        ),
        "negative_suite_commitment": _commitment(f"{candidate}:red"),
        "correction_decision_commitment": _commitment(
            f"{candidate}:decision"
        ),
    }


def _material() -> tuple[
    list[dict[str, Any]],
    list[dict[str, Any]],
    list[dict[str, Any]],
    dict[str, Any],
    dict[str, Any],
]:
    initial = _json("cycle001_initial_rc0010_summary.json")
    manifests = [
        _json("cycle001_dependency_manifest.json"),
        _json("cycle001_dependency_manifest_rc0014.json"),
        _json("cycle001_dependency_manifest_rc0015.json"),
        _json("cycle001_dependency_manifest_rc0016.json"),
    ]
    summaries = [
        initial,
        _json("cycle001_final_rc0014_summary.json"),
        _json("cycle001_final_rc0015_summary.json"),
        _json("cycle001_final_rc0016_summary.json"),
    ]
    manifest_by_candidate = {
        row["candidate_version_id"]: row for row in manifests
    }
    initial_closure = initial["source_dependency_closure_sha256"]
    for number in (18, 19):
        candidate = f"nls_v3_rc_{number:04d}"
        manifest = _manifest(
            candidate,
            before_candidate="nls_v3_rc_0010",
            before_closure=initial_closure,
        )
        manifests.append(manifest)
        manifest_by_candidate[candidate] = manifest
        summary = _summary(candidate, manifest["source_dependency_closure_sha256"])
        if number == 19:
            summary["case_rows"][-1]["status"] = "exception"
            summary["case_rows"][-2]["status"] = "v3_no_valid_candidate"
            summary["aggregate"]["selected_count"] = 98
            summary["aggregate"]["no_valid_candidate_count"] = 1
            summary["aggregate"]["exception_count"] = 1
            summary["machine_status"] = "failed"
        summaries.append(summary)

    rc19 = manifest_by_candidate["nls_v3_rc_0019"]
    rc20 = _manifest(
        "nls_v3_rc_0020",
        before_candidate="nls_v3_rc_0019",
        before_closure=rc19["source_dependency_closure_sha256"],
    )
    rc21 = _manifest(
        "nls_v3_rc_0021",
        before_candidate="nls_v3_rc_0020",
        before_closure=rc20["source_dependency_closure_sha256"],
    )
    manifests.extend((rc20, rc21))
    manifest_by_candidate.update(
        {"nls_v3_rc_0020": rc20, "nls_v3_rc_0021": rc21}
    )
    rc20_summary = _summary(
        "nls_v3_rc_0020", rc20["source_dependency_closure_sha256"]
    )
    summaries.append(rc20_summary)
    summary_by_candidate = {
        row["candidate_version_id"]: row for row in summaries
    }

    events: list[dict[str, Any]] = [
        {
            "event_type": "initial_run_observed",
            "candidate_version_id": "nls_v3_rc_0010",
            "batch_summary_sha256": artifact_sha256(initial),
        },
        {
            "event_type": "revision_disposition",
            "candidate_version_id": "nls_v3_rc_0010",
            "disposition": "superseded_after_observed_result",
            "decision_receipt_commitment": _commitment("rc10:superseded"),
        },
    ]
    for number in range(11, 22):
        candidate = f"nls_v3_rc_{number:04d}"
        manifest = manifest_by_candidate.get(candidate)
        events.append(_correction(candidate, manifest))
        summary = summary_by_candidate.get(candidate)
        if summary is not None:
            events.append(
                {
                    "event_type": "execution_observed",
                    "candidate_version_id": candidate,
                    "execution_scope": (
                        "preflight"
                        if number in {18, 19, 20}
                        else "formal_cumulative_rerun"
                    ),
                    "batch_summary_sha256": artifact_sha256(summary),
                }
            )
        if number == 20:
            events.append(
                {
                    "event_type": "product_read_observed",
                    "candidate_version_id": candidate,
                    "batch_summary_sha256": artifact_sha256(rc20_summary),
                    "review_outcome": "failed",
                    "maximum_severity": "MAJOR",
                    "failure_axis_codes": [
                        "NATURAL_NON_REPETITIVE_SURFACE"
                    ],
                    "failure_reason_codes": [
                        "SURFACE_UNNATURAL_OR_REPETITIVE"
                    ],
                    "review_receipt_commitment": _commitment(
                        "rc20:product-read-major"
                    ),
                }
            )
        disposition = (
            "current_pending_rerun"
            if number == 21
            else "superseded_unexecuted"
            if number == 11
            else "historical_unfrozen_no_receipt"
            if number in {12, 13, 17}
            else "superseded_after_observed_result"
        )
        events.append(
            {
                "event_type": "revision_disposition",
                "candidate_version_id": candidate,
                "disposition": disposition,
                "decision_receipt_commitment": _commitment(
                    f"{candidate}:{disposition}"
                ),
            }
        )
    return events, manifests, summaries, rc20, rc20_summary


def _bind_frozen_history(
    monkeypatch: pytest.MonkeyPatch,
    manifests: list[dict[str, Any]],
    summaries: list[dict[str, Any]],
    rc20: dict[str, Any],
    rc20_summary: dict[str, Any],
) -> None:
    frozen_candidates = {
        "nls_v3_rc_0014",
        "nls_v3_rc_0015",
        "nls_v3_rc_0016",
        "nls_v3_rc_0018",
        "nls_v3_rc_0019",
    }
    monkeypatch.setattr(
        cycle_evidence,
        "_RC0020_FROZEN_HISTORICAL_BATCH_SUMMARY_SHA256",
        tuple(
            sorted(
                (
                    row["candidate_version_id"],
                    artifact_sha256(row),
                )
                for row in summaries
                if row["candidate_version_id"] in frozen_candidates
            )
        ),
    )
    monkeypatch.setattr(
        cycle_evidence,
        "FROZEN_RC0020_PREFLIGHT_MANIFEST_ARTIFACT_SHA256",
        artifact_sha256(rc20),
    )
    monkeypatch.setattr(
        cycle_evidence,
        "FROZEN_RC0020_PREFLIGHT_SOURCE_CLOSURE_SHA256",
        rc20["source_dependency_closure_sha256"],
    )
    monkeypatch.setattr(
        cycle_evidence,
        "FROZEN_RC0020_PREFLIGHT_BATCH_SUMMARY_SHA256",
        artifact_sha256(rc20_summary),
    )


def test_rc0021_versions_are_explicit_without_relabelling_rc0020() -> None:
    assert STEP11_HISTORICAL_RC0020_CANDIDATE_VERSION_ID == "nls_v3_rc_0020"
    assert STEP11_HISTORICAL_RC0021_CANDIDATE_VERSION_ID == "nls_v3_rc_0021"
    assert STEP11_HISTORICAL_RC0021_RUNTIME_ADAPTER_VERSION.endswith(
        ".rc0021.v1"
    )
    assert RC_CORRECTION_RERUN_LINEAGE_V3_SCHEMA.endswith(".v3")
    assert RC_CORRECTION_RERUN_LINEAGE_EVENT_V3_SCHEMA.endswith(".v3")


def test_rc0021_lineage_records_machine_clean_product_read_major_as_superseded(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    events, manifests, summaries, rc20, rc20_summary = _material()
    _bind_frozen_history(monkeypatch, manifests, summaries, rc20, rc20_summary)

    lineage = build_rc0010_rc0021_correction_rerun_lineage(
        events,
        dependency_manifests=manifests,
        batch_run_summaries=summaries,
    )

    assert lineage["schema_version"] == RC_CORRECTION_RERUN_LINEAGE_V3_SCHEMA
    assert lineage["current_candidate_version_id"] == "nls_v3_rc_0021"
    assert lineage["acceptance_lineage_ready"] is False
    rc20_run = next(
        row
        for row in lineage["events"]
        if row["event_type"] == "execution_observed"
        and row["candidate_version_id"] == "nls_v3_rc_0020"
    )
    assert rc20_run["execution_scope"] == "preflight"
    assert rc20_run["machine_status"] == "clean"
    assert rc20_run["selected_count"] == 100
    assert rc20_run["counts_as_clean_formal_rerun"] is False
    product_read = next(
        row
        for row in lineage["events"]
        if row["event_type"] == "product_read_observed"
    )
    assert product_read["candidate_version_id"] == "nls_v3_rc_0020"
    assert product_read["review_outcome"] == "failed"
    assert product_read["maximum_severity"] == "MAJOR"
    assert product_read["acceptance_eligible"] is False
    assert product_read["counts_as_passed_rerun"] is False
    rc20_disposition = next(
        row
        for row in lineage["events"]
        if row["event_type"] == "revision_disposition"
        and row["candidate_version_id"] == "nls_v3_rc_0020"
    )
    assert rc20_disposition["disposition"] == "superseded_after_observed_result"
    assert rc20_disposition["counts_as_passed_rerun"] is False
    assert lineage["aggregate"]["failed_product_read_count"] == 1
    assert validate_rc0010_rc0021_correction_rerun_lineage(
        lineage,
        dependency_manifests=manifests,
        batch_run_summaries=summaries,
    ) == ()


@pytest.mark.parametrize("mutation", ("remove", "accept_rc20", "wrong_summary"))
def test_rc0021_lineage_rejects_erased_or_relabelled_rc0020_product_failure(
    monkeypatch: pytest.MonkeyPatch,
    mutation: str,
) -> None:
    events, manifests, summaries, rc20, rc20_summary = _material()
    _bind_frozen_history(monkeypatch, manifests, summaries, rc20, rc20_summary)
    if mutation == "remove":
        events = [row for row in events if row["event_type"] != "product_read_observed"]
    elif mutation == "accept_rc20":
        disposition = next(
            row
            for row in events
            if row["event_type"] == "revision_disposition"
            and row["candidate_version_id"] == "nls_v3_rc_0020"
        )
        disposition["disposition"] = "cycle_final_candidate"
    else:
        product = next(
            row for row in events if row["event_type"] == "product_read_observed"
        )
        product["batch_summary_sha256"] = _commitment("substituted-summary")

    with pytest.raises(Step11CycleEvidenceError):
        build_rc0010_rc0021_correction_rerun_lineage(
            events,
            dependency_manifests=manifests,
            batch_run_summaries=summaries,
        )


def test_rc0021_lineage_requires_exact_immediate_rc0020_parent(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    events, manifests, summaries, rc20, rc20_summary = _material()
    _bind_frozen_history(monkeypatch, manifests, summaries, rc20, rc20_summary)
    forged = _manifest(
        "nls_v3_rc_0021",
        before_candidate="nls_v3_rc_0019",
        before_closure=_commitment("not-rc0020-closure"),
    )
    manifests[-1] = forged
    correction = next(
        row
        for row in events
        if row["event_type"] == "correction_recorded"
        and row["candidate_version_id"] == "nls_v3_rc_0021"
    )
    correction["source_state_artifact_sha256"] = artifact_sha256(forged)
    correction["changed_file_set_commitment"] = artifact_sha256(
        forged["changed_file_hashes"]
    )
    with pytest.raises(
        Step11CycleEvidenceError,
        match="RC_LINEAGE_FINAL_DEPENDENCY_BASE_INVALID",
    ):
        build_rc0010_rc0021_correction_rerun_lineage(
            events,
            dependency_manifests=manifests,
            batch_run_summaries=summaries,
        )


def test_rc0021_dependency_manifest_is_exact_diff_from_frozen_rc0020(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    rows = [
        {
            "path": f"ai/tests/frozen_rc0020/path_{index:03d}.py",
            "sha256": _commitment(f"rc20:{index}"),
        }
        for index in range(136)
    ]
    rc20 = build_step11_dependency_manifest(
        before_candidate_version_id="nls_v3_rc_0019",
        before_source_closure_sha256=_commitment("rc19"),
        candidate_version_id="nls_v3_rc_0020",
        file_hashes=rows,
        changed_file_hashes=rows[:1],
    )
    changed_path = rows[35]["path"]
    current = {row["path"]: row["sha256"] for row in rows}
    current[changed_path] = _commitment("rc21:changed")
    for path in dependency_tool.RC0021_ADDED_SOURCE_PATHS:
        current[path] = _commitment(f"rc21:{path}")
    monkeypatch.setattr(
        dependency_tool,
        "FROZEN_RC0020_PREFLIGHT_MANIFEST_ARTIFACT_SHA256",
        artifact_sha256(rc20),
    )
    monkeypatch.setattr(
        dependency_tool,
        "FROZEN_RC0020_PREFLIGHT_SOURCE_CLOSURE_SHA256",
        rc20["source_dependency_closure_sha256"],
    )
    monkeypatch.setattr(dependency_tool, "_sha256", lambda path: current[path])

    result = dependency_tool.build_current_step11_dependency_manifest(rc20)

    assert result["before_candidate_version_id"] == "nls_v3_rc_0020"
    assert result["before_source_closure_sha256"] == rc20[
        "source_dependency_closure_sha256"
    ]
    assert result["candidate_version_id"] == "nls_v3_rc_0021"
    assert len(result["file_hashes"]) == 138
    assert {row["path"] for row in result["changed_file_hashes"]} == {
        changed_path,
        *dependency_tool.RC0021_ADDED_SOURCE_PATHS,
    }
