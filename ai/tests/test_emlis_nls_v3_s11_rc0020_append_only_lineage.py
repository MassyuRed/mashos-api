# -*- coding: utf-8 -*-
from __future__ import annotations

"""Append-only rc0020 lineage and immediate dependency-boundary REDs."""

from copy import deepcopy
import hashlib
import json
from pathlib import Path
from typing import Any

import pytest

from emlis_ai_nls_v3_artifact_contract import artifact_sha256
from emlis_ai_step11_cycle_evidence_v3 import (
    CYCLE_CHANGE_LEDGER_SCHEMA,
    CYCLE_CHANGE_ROW_SCHEMA,
    RC_CORRECTION_RERUN_LINEAGE_EVENT_SCHEMA,
    RC_CORRECTION_RERUN_LINEAGE_SCHEMA,
    Step11CycleEvidenceError,
    build_rc0010_rc0020_correction_rerun_lineage,
    build_cycle_change_ledger,
    build_step11_dependency_manifest,
    validate_rc0010_rc0020_correction_rerun_lineage,
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
    suffix = candidate.rsplit("_", 1)[-1]
    changed = [
        {
            "path": f"ai/tests/rc{suffix}_structural_owner.py",
            "sha256": _commitment(f"{candidate}:owner-bytes"),
        }
    ]
    return build_step11_dependency_manifest(
        before_candidate_version_id=before_candidate,
        before_source_closure_sha256=before_closure,
        candidate_version_id=candidate,
        file_hashes=changed,
        changed_file_hashes=changed,
    )


def _summary(
    candidate: str,
    closure: str,
    *,
    failed_counts: tuple[int, int, int] | None = None,
) -> dict[str, Any]:
    value = deepcopy(_json("cycle001_final_rc0016_summary.json"))
    value["candidate_version_id"] = candidate
    value["run_id"] = f"nls3run_{candidate[-4:]}c001{candidate[-1] * 8}"
    value["source_dependency_closure_sha256"] = closure
    if failed_counts is None:
        return value

    selected, no_valid, exception = failed_counts
    assert selected + no_valid + exception == 100
    for index, row in enumerate(value["case_rows"]):
        row["status"] = (
            "selected"
            if index < selected
            else "v3_no_valid_candidate"
            if index < selected + no_valid
            else "exception"
        )
    value["aggregate"]["selected_count"] = selected
    value["aggregate"]["no_valid_candidate_count"] = no_valid
    value["aggregate"]["exception_count"] = exception
    value["aggregate"]["v1_fallback_count"] = 0
    value["machine_status"] = "failed"
    value["all_expected_cases_executed"] = True
    value["executed_case_count"] = 100
    return value


def _correction_event(
    candidate: str,
    manifest: dict[str, Any] | None,
) -> dict[str, Any]:
    source_kind = (
        "dependency_manifest"
        if manifest is not None
        else "historical_unfrozen_no_receipt"
    )
    source_sha = (
        artifact_sha256(manifest)
        if manifest is not None
        else _commitment(f"{candidate}:unfrozen-source")
    )
    changed_sha = (
        artifact_sha256(manifest["changed_file_hashes"])
        if manifest is not None
        else _commitment(f"{candidate}:unfrozen-changed")
    )
    return {
        "event_type": "correction_recorded",
        "candidate_version_id": candidate,
        "source_state_kind": source_kind,
        "source_state_artifact_sha256": source_sha,
        "failure_evidence_commitment": _commitment(f"{candidate}:failure"),
        "structural_hypothesis_commitment": _commitment(
            f"{candidate}:hypothesis"
        ),
        "changed_file_set_commitment": changed_sha,
        "negative_suite_commitment": _commitment(f"{candidate}:negative"),
        "correction_decision_commitment": _commitment(
            f"{candidate}:decision"
        ),
    }


def _material() -> tuple[
    list[dict[str, Any]],
    list[dict[str, Any]],
    list[dict[str, Any]],
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
    initial_closure = initial["source_dependency_closure_sha256"]
    rc18 = _manifest(
        "nls_v3_rc_0018",
        before_candidate="nls_v3_rc_0010",
        before_closure=initial_closure,
    )
    rc19 = _manifest(
        "nls_v3_rc_0019",
        before_candidate="nls_v3_rc_0010",
        before_closure=initial_closure,
    )
    rc20 = _manifest(
        "nls_v3_rc_0020",
        before_candidate="nls_v3_rc_0019",
        before_closure=rc19["source_dependency_closure_sha256"],
    )
    manifests.extend((rc18, rc19, rc20))
    summaries.extend(
        (
            _summary(
                "nls_v3_rc_0018",
                rc18["source_dependency_closure_sha256"],
                failed_counts=(80, 20, 0),
            ),
            _summary(
                "nls_v3_rc_0019",
                rc19["source_dependency_closure_sha256"],
                failed_counts=(93, 6, 1),
            ),
            _summary(
                "nls_v3_rc_0020",
                rc20["source_dependency_closure_sha256"],
            ),
        )
    )
    manifest_by_candidate = {
        row["candidate_version_id"]: row for row in manifests
    }
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
            "decision_receipt_commitment": _commitment("rc0010:superseded"),
        },
    ]
    for number in range(11, 21):
        candidate = f"nls_v3_rc_{number:04d}"
        manifest = manifest_by_candidate.get(candidate)
        events.append(_correction_event(candidate, manifest))
        if candidate in summary_by_candidate:
            events.append(
                {
                    "event_type": "execution_observed",
                    "candidate_version_id": candidate,
                    "execution_scope": (
                        "preflight"
                        if candidate in {"nls_v3_rc_0018", "nls_v3_rc_0019"}
                        else "formal_cumulative_rerun"
                    ),
                    "batch_summary_sha256": artifact_sha256(
                        summary_by_candidate[candidate]
                    ),
                }
            )
        disposition = (
            "superseded_unexecuted"
            if number == 11
            else "historical_unfrozen_no_receipt"
            if number in {12, 13, 17}
            else "cycle_final_candidate"
            if number == 20
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
    return events, manifests, summaries


def _bind_material_history(
    monkeypatch: pytest.MonkeyPatch,
    summaries: list[dict[str, Any]],
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


def test_rc0020_lineage_keeps_failed_rc0019_preflight_observed_and_superseded(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    events, manifests, summaries = _material()
    _bind_material_history(monkeypatch, summaries)
    lineage = build_rc0010_rc0020_correction_rerun_lineage(
        events,
        dependency_manifests=manifests,
        batch_run_summaries=summaries,
    )

    assert lineage["schema_version"] == RC_CORRECTION_RERUN_LINEAGE_SCHEMA
    assert lineage["current_candidate_version_id"] == "nls_v3_rc_0020"
    assert lineage["expected_candidate_sequence"][-2:] == [
        "nls_v3_rc_0019",
        "nls_v3_rc_0020",
    ]
    rc19_execution = next(
        row
        for row in lineage["events"]
        if row["event_type"] == "execution_observed"
        and row["candidate_version_id"] == "nls_v3_rc_0019"
    )
    assert rc19_execution["execution_scope"] == "preflight"
    assert rc19_execution["machine_status"] == "failed"
    assert rc19_execution["selected_count"] == 93
    assert rc19_execution["no_valid_candidate_count"] == 6
    assert rc19_execution["exception_count"] == 1
    assert rc19_execution["counts_as_clean_formal_rerun"] is False
    rc19_disposition = next(
        row
        for row in lineage["events"]
        if row["event_type"] == "revision_disposition"
        and row["candidate_version_id"] == "nls_v3_rc_0019"
    )
    assert rc19_disposition["disposition"] == "superseded_after_observed_result"
    assert rc19_disposition["counts_as_passed_rerun"] is False
    assert all(
        row["schema_version"] == RC_CORRECTION_RERUN_LINEAGE_EVENT_SCHEMA
        for row in lineage["events"]
    )
    assert validate_rc0010_rc0020_correction_rerun_lineage(
        lineage,
        dependency_manifests=manifests,
        batch_run_summaries=summaries,
    ) == ()


def test_rc0020_lineage_rejects_non_immediate_final_dependency_base(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    events, manifests, summaries = _material()
    _bind_material_history(monkeypatch, summaries)
    rc19 = next(
        row for row in manifests if row["candidate_version_id"] == "nls_v3_rc_0019"
    )
    forged = _manifest(
        "nls_v3_rc_0020",
        before_candidate="nls_v3_rc_0010",
        before_closure=summaries[0]["source_dependency_closure_sha256"],
    )
    manifests = [
        forged if row["candidate_version_id"] == "nls_v3_rc_0020" else row
        for row in manifests
    ]
    correction = next(
        row
        for row in events
        if row["event_type"] == "correction_recorded"
        and row["candidate_version_id"] == "nls_v3_rc_0020"
    )
    correction["source_state_artifact_sha256"] = artifact_sha256(forged)
    correction["changed_file_set_commitment"] = artifact_sha256(
        forged["changed_file_hashes"]
    )
    final_summary = next(
        row for row in summaries if row["candidate_version_id"] == "nls_v3_rc_0020"
    )
    final_summary["source_dependency_closure_sha256"] = forged[
        "source_dependency_closure_sha256"
    ]
    execution = next(
        row
        for row in events
        if row["event_type"] == "execution_observed"
        and row["candidate_version_id"] == "nls_v3_rc_0020"
    )
    execution["batch_summary_sha256"] = artifact_sha256(final_summary)

    with pytest.raises(
        Step11CycleEvidenceError,
        match="RC_LINEAGE_FINAL_DEPENDENCY_BASE_INVALID",
    ):
        build_rc0010_rc0020_correction_rerun_lineage(
            events,
            dependency_manifests=manifests,
            batch_run_summaries=summaries,
        )
    assert rc19["source_dependency_closure_sha256"] != forged[
        "before_source_closure_sha256"
    ]


@pytest.mark.parametrize("tamper", ("run_id", "aggregate", "case_row"))
def test_rc0020_lineage_rejects_historical_summary_substitution(
    monkeypatch: pytest.MonkeyPatch,
    tamper: str,
) -> None:
    events, manifests, summaries = _material()
    _bind_material_history(monkeypatch, summaries)
    rc19_index = next(
        index
        for index, row in enumerate(summaries)
        if row["candidate_version_id"] == "nls_v3_rc_0019"
    )
    forged = deepcopy(summaries[rc19_index])
    if tamper == "run_id":
        forged["run_id"] = "nls3run_0019c001dddddddd"
    elif tamper == "aggregate":
        forged["aggregate"]["substitution_marker"] = 0
    else:
        forged["case_rows"][0]["substitution_marker"] = 0
    summaries[rc19_index] = forged
    execution = next(
        row
        for row in events
        if row["event_type"] == "execution_observed"
        and row["candidate_version_id"] == "nls_v3_rc_0019"
    )
    execution["batch_summary_sha256"] = artifact_sha256(forged)

    with pytest.raises(
        Step11CycleEvidenceError,
        match="RC_LINEAGE_HISTORICAL_SUMMARY_COMMITMENT_MISMATCH",
    ):
        build_rc0010_rc0020_correction_rerun_lineage(
            events,
            dependency_manifests=manifests,
            batch_run_summaries=summaries,
        )


def test_rc0020_change_ledger_separates_cycle_and_immediate_delta(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    initial_summary = {"body_free": True, "role": "initial-summary"}
    final_summary = {"body_free": True, "role": "final-summary"}
    initial_closure = _commitment("cycle-initial-closure")
    rc19_closure = _commitment("frozen-rc0019-closure")
    owner_path = (
        "ai/services/ai_inference/emlis_ai_step11_cycle_evidence_v3.py"
    )
    file_hashes = [
        {"path": owner_path, "sha256": _commitment("owner")},
        {
            "path": cycle_evidence._STEP11_SECURITY_TEST_PATH,
            "sha256": _commitment("security"),
        },
        {
            "path": cycle_evidence._WORKAROUND_SCANNER_PATH,
            "sha256": _commitment("scanner"),
        },
    ]
    dependency = build_step11_dependency_manifest(
        before_candidate_version_id="nls_v3_rc_0019",
        before_source_closure_sha256=rc19_closure,
        candidate_version_id="nls_v3_rc_0020",
        file_hashes=file_hashes,
        changed_file_hashes=[file_hashes[0]],
    )
    lock = {
        "source_dependency_closure_sha256": initial_closure,
        "initial_batch_summary_sha256": artifact_sha256(initial_summary),
        "body_free": True,
    }
    commitment = _commitment("blocking-case")
    initial_review = {
        "rows": [
            {
                "review": {
                    "case_identity_commitment": commitment,
                    "severity": "BLOCKER",
                    "reason_codes": ["REQUIRED_MEANING_MISSING"],
                }
            }
        ],
        "body_free": True,
    }
    final_projection = {
        "candidate_version_id": "nls_v3_rc_0020",
        "source_dependency_closure_sha256": dependency[
            "source_dependency_closure_sha256"
        ],
        "summary_sha256": artifact_sha256(final_summary),
    }
    cumulative = {
        "schema_version": cycle_evidence.CUMULATIVE100_RECEIPT_SCHEMA,
        "candidate_version_id": "nls_v3_rc_0020",
        "source_dependency_closure_sha256": dependency[
            "source_dependency_closure_sha256"
        ],
        "final_batch_summary_sha256": artifact_sha256(final_summary),
        "initial_lock_sha256": artifact_sha256(lock),
        "body_free": True,
    }
    workaround = {"body_free": True, "status": "passed"}
    hypothesis = {
        "schema_version": "cocolon.emlis.nls_v3.shared_failure_hypothesis.v2",
        "owner_scope": "step11_common_structural_owner",
        "failure_layer": "matcher",
        "severity": "BLOCKER",
        "failure_codes": ["REQUIRED_MEANING_MISSING"],
        "common_cause_codes": ["required_obligation_not_realised"],
        "correction_strategy_codes": ["realise_required_obligations"],
        "affected_owner_paths": [owner_path],
        "applies_to_case_count": 1,
    }
    input_rows = [
        {
            "failure_case_commitments": [commitment],
            "failure_layer": "matcher",
            "severity": "BLOCKER",
            "failure_codes": ["REQUIRED_MEANING_MISSING"],
            "shared_structural_hypothesis": hypothesis,
            "shared_structural_hypothesis_commitment": artifact_sha256(
                hypothesis
            ),
            "correction_owner_paths": [owner_path],
            "regression_risk_codes": ["SEMANTIC_COVERAGE_REGRESSION"],
            "negative_test_ids": sorted(
                cycle_evidence._CHANGE_NEGATIVE_TEST_IDS
            ),
        }
    ]
    monkeypatch.setattr(
        cycle_evidence,
        "_validated_initial_lock",
        lambda *_args, **_kwargs: lock,
    )
    monkeypatch.setattr(
        cycle_evidence,
        "_validated_review_set",
        lambda *_args, **_kwargs: initial_review,
    )
    monkeypatch.setattr(
        cycle_evidence,
        "_project_final",
        lambda *_args, **_kwargs: final_projection,
    )
    monkeypatch.setattr(
        cycle_evidence,
        "validate_case_specific_workaround_scan_receipt",
        lambda *_args, **_kwargs: (),
    )

    ledger = build_cycle_change_ledger(
        lock,
        initial_summary,
        {},
        initial_review,
        final_summary,
        cumulative,
        input_rows,
        final_dependency_manifest=dependency,
        workaround_scan_receipt=workaround,
    )

    assert ledger["schema_version"] == CYCLE_CHANGE_LEDGER_SCHEMA
    assert ledger["cycle_initial_candidate_version_id"] == "nls_v3_rc_0010"
    assert ledger["cycle_final_candidate_version_id"] == "nls_v3_rc_0020"
    assert ledger["cycle_initial_source_closure_sha256"] == initial_closure
    delta = ledger["final_correction_delta"]
    assert delta["before_candidate_version_id"] == "nls_v3_rc_0019"
    assert delta["after_candidate_version_id"] == "nls_v3_rc_0020"
    assert delta["before_source_closure_sha256"] == rc19_closure
    assert delta["after_source_closure_sha256"] == dependency[
        "source_dependency_closure_sha256"
    ]
    row = ledger["rows"][0]
    assert row["schema_version"] == CYCLE_CHANGE_ROW_SCHEMA
    assert row["failure_evidence_origin"] == "cycle_initial_review"
    assert row["final_correction_delta_sha256"] == artifact_sha256(delta)
    assert "changed_file_hashes" not in row


def test_rc0020_change_ledger_rejects_non_immediate_final_delta(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    dependency = _manifest(
        "nls_v3_rc_0020",
        before_candidate="nls_v3_rc_0010",
        before_closure=_commitment("cycle-initial"),
    )
    with pytest.raises(
        Step11CycleEvidenceError,
        match="FINAL_CORRECTION_DEPENDENCY_BOUNDARY_INVALID",
    ):
        cycle_evidence._final_correction_delta(
            dependency,
            final_candidate_version_id="nls_v3_rc_0020",
            final_source_closure_sha256=dependency[
                "source_dependency_closure_sha256"
            ],
        )


def test_rc0020_dependency_manifest_is_exact_diff_from_all_133_rc0019_paths(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    predecessor_rows = [
        {
            "path": f"ai/tests/frozen_rc0019/path_{index:03d}.py",
            "sha256": _commitment(f"rc0019:{index}"),
        }
        for index in range(133)
    ]
    predecessor = build_step11_dependency_manifest(
        before_candidate_version_id="nls_v3_rc_0010",
        before_source_closure_sha256=_commitment("rc0010-closure"),
        candidate_version_id="nls_v3_rc_0019",
        file_hashes=predecessor_rows,
        changed_file_hashes=predecessor_rows[:1],
    )
    new_path = "ai/tests/test_rc0020_new_red.py"
    current_hashes = {row["path"]: row["sha256"] for row in predecessor_rows}
    changed_existing_path = predecessor_rows[57]["path"]
    current_hashes[changed_existing_path] = _commitment("rc0020:changed-57")
    current_hashes[new_path] = _commitment("rc0020:new-red")
    visited: list[str] = []

    def fake_sha256(path: str) -> str:
        visited.append(path)
        return current_hashes[path]

    monkeypatch.setattr(
        dependency_tool,
        "FROZEN_RC0019_PREFLIGHT_MANIFEST_ARTIFACT_SHA256",
        artifact_sha256(predecessor),
    )
    monkeypatch.setattr(
        dependency_tool,
        "FROZEN_RC0019_PREFLIGHT_SOURCE_CLOSURE_SHA256",
        predecessor["source_dependency_closure_sha256"],
    )
    monkeypatch.setattr(
        dependency_tool,
        "RC0020_ADDED_SOURCE_PATHS",
        (new_path,),
    )
    monkeypatch.setattr(
        dependency_tool,
        "STEP11_CANDIDATE_VERSION_ID",
        "nls_v3_rc_0020",
    )
    monkeypatch.setattr(dependency_tool, "_sha256", fake_sha256)

    current = dependency_tool.build_current_step11_dependency_manifest(
        predecessor
    )

    assert current["before_candidate_version_id"] == "nls_v3_rc_0019"
    assert current["before_source_closure_sha256"] == predecessor[
        "source_dependency_closure_sha256"
    ]
    assert current["candidate_version_id"] == "nls_v3_rc_0020"
    assert len(current["file_hashes"]) == 134
    assert current["changed_file_hashes"] == sorted(
        [
            {
                "path": changed_existing_path,
                "sha256": current_hashes[changed_existing_path],
            },
            {"path": new_path, "sha256": current_hashes[new_path]},
        ],
        key=lambda row: row["path"],
    )
    assert len(visited) == 134
    assert set(visited) == set(current_hashes)
