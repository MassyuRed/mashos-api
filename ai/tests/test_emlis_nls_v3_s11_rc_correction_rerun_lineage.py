# -*- coding: utf-8 -*-
from __future__ import annotations

"""Append-only rc0010--rc0019 correction/rerun lineage RED tests."""

from copy import deepcopy
import hashlib
import json
from pathlib import Path
from typing import Any

import pytest

from emlis_ai_nls_v3_artifact_contract import artifact_sha256
from emlis_ai_step11_cycle_evidence_v3 import (
    RC_CORRECTION_RERUN_LINEAGE_EVENT_V1_SCHEMA,
    RC_CORRECTION_RERUN_LINEAGE_V1_SCHEMA,
    Step11CycleEvidenceError,
    build_rc0010_rc0019_correction_rerun_lineage,
    validate_rc0010_rc0019_correction_rerun_lineage,
)


_CYCLE = Path(__file__).resolve().parent / "fixtures" / "emlis_nls_v3" / "cycle_001"


def _json(name: str) -> dict[str, Any]:
    with (_CYCLE / name).open("r", encoding="utf-8") as handle:
        return json.load(handle)


def _commitment(label: str) -> str:
    return hashlib.sha256(label.encode("utf-8")).hexdigest()


def _parents() -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    manifests = [
        _json("cycle001_dependency_manifest.json"),
        _json("cycle001_dependency_manifest_rc0014.json"),
        _json("cycle001_dependency_manifest_rc0015.json"),
        _json("cycle001_dependency_manifest_rc0016.json"),
    ]
    summaries = [
        _json("cycle001_initial_rc0010_summary.json"),
        _json("cycle001_final_rc0014_summary.json"),
        _json("cycle001_final_rc0015_summary.json"),
        _json("cycle001_final_rc0016_summary.json"),
    ]
    return manifests, summaries


def _correction_event(
    candidate: str,
    *,
    manifest: dict[str, Any] | None,
    source_kind: str,
) -> dict[str, Any]:
    suffix = candidate.rsplit("_", 1)[-1]
    if manifest is None:
        source_commitment = _commitment(f"{candidate}:source-state")
        changed_commitment = _commitment(f"{candidate}:changed-files")
    else:
        source_commitment = artifact_sha256(manifest)
        changed_commitment = artifact_sha256(manifest["changed_file_hashes"])
    return {
        "event_type": "correction_recorded",
        "candidate_version_id": candidate,
        "source_state_kind": source_kind,
        "source_state_artifact_sha256": source_commitment,
        "failure_evidence_commitment": _commitment(f"{suffix}:failure"),
        "structural_hypothesis_commitment": _commitment(
            f"{suffix}:structural-hypothesis"
        ),
        "changed_file_set_commitment": changed_commitment,
        "negative_suite_commitment": _commitment(f"{suffix}:negative-suite"),
        "correction_decision_commitment": _commitment(
            f"{suffix}:correction-decision"
        ),
    }


def _events(
    manifests: list[dict[str, Any]],
    summaries: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    manifest_by_candidate = {
        value["candidate_version_id"]: value for value in manifests
    }
    summary_by_candidate = {
        value["candidate_version_id"]: value for value in summaries
    }
    events: list[dict[str, Any]] = [
        {
            "event_type": "initial_run_observed",
            "candidate_version_id": "nls_v3_rc_0010",
            "batch_summary_sha256": artifact_sha256(
                summary_by_candidate["nls_v3_rc_0010"]
            ),
        },
        {
            "event_type": "revision_disposition",
            "candidate_version_id": "nls_v3_rc_0010",
            "disposition": "superseded_after_observed_result",
            "decision_receipt_commitment": _commitment("0010:superseded"),
        },
    ]
    formal_receipt_candidates = {
        "nls_v3_rc_0014",
        "nls_v3_rc_0015",
        "nls_v3_rc_0016",
    }
    historical_unfrozen = {
        "nls_v3_rc_0012",
        "nls_v3_rc_0013",
        "nls_v3_rc_0017",
        "nls_v3_rc_0018",
    }
    for number in range(11, 20):
        candidate = f"nls_v3_rc_{number:04d}"
        manifest = manifest_by_candidate.get(candidate)
        source_kind = (
            "dependency_manifest"
            if manifest is not None
            else "working_state_unfrozen"
            if number == 19
            else "historical_unfrozen_no_receipt"
        )
        events.append(
            _correction_event(
                candidate,
                manifest=manifest,
                source_kind=source_kind,
            )
        )
        if candidate in formal_receipt_candidates:
            events.append(
                {
                    "event_type": "execution_observed",
                    "candidate_version_id": candidate,
                    "execution_scope": "formal_cumulative_rerun",
                    "batch_summary_sha256": artifact_sha256(
                        summary_by_candidate[candidate]
                    ),
                }
            )
            disposition = "superseded_after_observed_result"
        elif number == 11:
            disposition = "superseded_unexecuted"
        elif candidate in historical_unfrozen:
            disposition = "historical_unfrozen_no_receipt"
        else:
            disposition = "current_pending_rerun"
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
    return events


def _material() -> tuple[
    dict[str, Any],
    list[dict[str, Any]],
    list[dict[str, Any]],
    list[dict[str, Any]],
]:
    manifests, summaries = _parents()
    events = _events(manifests, summaries)
    lineage = build_rc0010_rc0019_correction_rerun_lineage(
        events,
        dependency_manifests=manifests,
        batch_run_summaries=summaries,
    )
    return lineage, events, manifests, summaries


def test_rc_lineage_preserves_complete_honest_pending_history() -> None:
    lineage, _events_value, manifests, summaries = _material()

    assert lineage["schema_version"] == RC_CORRECTION_RERUN_LINEAGE_V1_SCHEMA
    assert lineage["historical_sequence_complete"] is True
    assert lineage["acceptance_lineage_ready"] is False
    assert lineage["expected_candidate_sequence"] == [
        f"nls_v3_rc_{number:04d}" for number in range(10, 20)
    ]
    assert lineage["aggregate"] == {
        "candidate_revision_count": 10,
        "correction_event_count": 9,
        "receipt_bound_execution_count": 4,
        "receipt_bound_clean_formal_rerun_count": 3,
        "historical_no_receipt_revision_count": 4,
        "unreceipted_execution_claim_count": 0,
    }
    assert validate_rc0010_rc0019_correction_rerun_lineage(
        lineage,
        dependency_manifests=manifests,
        batch_run_summaries=summaries,
    ) == ()

    previous = None
    for index, event in enumerate(lineage["events"]):
        assert event["schema_version"] == (
            RC_CORRECTION_RERUN_LINEAGE_EVENT_V1_SCHEMA
        )
        assert event["event_index"] == index
        assert event["previous_event_commitment"] == previous
        previous = event["event_commitment"]
    assert lineage["lineage_head_commitment"] == previous


def test_rc_lineage_no_receipt_revision_never_acquires_run_claim() -> None:
    _lineage, events, manifests, summaries = _material()
    correction_index = next(
        index
        for index, event in enumerate(events)
        if event.get("candidate_version_id") == "nls_v3_rc_0012"
        and event["event_type"] == "correction_recorded"
    )
    events.insert(
        correction_index + 1,
        {
            "event_type": "execution_observed",
            "candidate_version_id": "nls_v3_rc_0012",
            "execution_scope": "formal_cumulative_rerun",
            "batch_summary_sha256": _commitment("fabricated-run"),
        },
    )

    with pytest.raises(
        Step11CycleEvidenceError,
        match="RC_LINEAGE_EXECUTION_EVENT_INVALID",
    ):
        build_rc0010_rc0019_correction_rerun_lineage(
            events,
            dependency_manifests=manifests,
            batch_run_summaries=summaries,
        )


def test_rc_lineage_clean_old_rerun_cannot_become_final_acceptance() -> None:
    _lineage, events, manifests, summaries = _material()
    pending = next(
        event
        for event in events
        if event.get("candidate_version_id") == "nls_v3_rc_0019"
        and event["event_type"] == "revision_disposition"
    )
    pending["disposition"] = "cycle_final_candidate"

    with pytest.raises(
        Step11CycleEvidenceError,
        match="RC_LINEAGE_FINAL_DISPOSITION_INVALID",
    ):
        build_rc0010_rc0019_correction_rerun_lineage(
            events,
            dependency_manifests=manifests,
            batch_run_summaries=summaries,
        )


def test_rc_lineage_execution_is_bound_to_exact_candidate_receipt() -> None:
    _lineage, events, manifests, summaries = _material()
    rc14 = next(
        event
        for event in events
        if event.get("candidate_version_id") == "nls_v3_rc_0014"
        and event["event_type"] == "execution_observed"
    )
    rc15_summary = next(
        value
        for value in summaries
        if value["candidate_version_id"] == "nls_v3_rc_0015"
    )
    rc14["batch_summary_sha256"] = artifact_sha256(rc15_summary)

    with pytest.raises(
        Step11CycleEvidenceError,
        match="RC_LINEAGE_EXECUTION_EVENT_INVALID",
    ):
        build_rc0010_rc0019_correction_rerun_lineage(
            events,
            dependency_manifests=manifests,
            batch_run_summaries=summaries,
        )


def test_rc_lineage_recomputation_rejects_hash_chain_or_outcome_tamper() -> None:
    lineage, _events_value, manifests, summaries = _material()
    forged = deepcopy(lineage)
    execution = next(
        event
        for event in forged["events"]
        if event["event_type"] == "execution_observed"
    )
    execution["counts_as_clean_formal_rerun"] = False

    assert validate_rc0010_rc0019_correction_rerun_lineage(
        forged,
        dependency_manifests=manifests,
        batch_run_summaries=summaries,
    ) == ("RC_CORRECTION_RERUN_LINEAGE_RECOMPUTATION_MISMATCH",)


def test_rc_lineage_rejects_orphan_receipt_parent() -> None:
    _lineage, events, manifests, summaries = _material()
    summaries.append(deepcopy(summaries[-1]))
    summaries[-1]["run_id"] = "nls3run_0016c001ffffffff"

    with pytest.raises(
        Step11CycleEvidenceError,
        match="RC_LINEAGE_UNUSED_SUMMARY_PARENT",
    ):
        build_rc0010_rc0019_correction_rerun_lineage(
            events,
            dependency_manifests=manifests,
            batch_run_summaries=summaries,
        )
