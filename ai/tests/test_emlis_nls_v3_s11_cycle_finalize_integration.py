# -*- coding: utf-8 -*-
from __future__ import annotations

"""Focused REDs for the rc0020 Cycle001 finalizer integration."""

import hashlib
from pathlib import Path
import subprocess
import sys
from typing import Any

import pytest

from emlis_ai_nls_v3_artifact_contract import artifact_sha256
from emlis_nls_v3_s0_s1_baseline import load_baseline_cases
from emlis_nls_v3_s2_sample_registry import load_canonical_jsonl
import emlis_nls_v3_step11_cycle_finalize as finalize


_REPO = Path(__file__).resolve().parents[2]
_BATCH = (
    Path(__file__).resolve().parent
    / "fixtures"
    / "emlis_nls_v3"
    / "generated"
    / "batch_001.jsonl"
)


def _manifest(candidate: str, *, current: bool = False) -> dict[str, Any]:
    changed = [{"path": f"owner/{candidate}.py", "sha256": "a" * 64}]
    file_hashes = list(changed)
    if current:
        file_hashes.append(
            {"path": finalize._SECURITY_TEST_PATH, "sha256": "b" * 64}
        )
    return {
        "candidate_version_id": candidate,
        "source_dependency_closure_sha256": "c" * 64,
        "changed_file_hashes": changed,
        "file_hashes": file_hashes,
    }


def _summary(candidate: str) -> dict[str, Any]:
    return {
        "candidate_version_id": candidate,
        "run_id": f"nls3run_{candidate[-4:]}c001aaaaaaaa",
        "body_free": True,
    }


def test_cycle_finalize_standalone_help_resolves_test_helpers() -> None:
    result = subprocess.run(
        [
            sys.executable,
            str(_REPO / "ai/tools/emlis_nls_v3_step11_cycle_finalize.py"),
            "--help",
        ],
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
    assert "--development42-receipt" in result.stdout
    assert "--lineage-dependency-manifest" in result.stdout
    assert "--lineage-batch-summary" in result.stdout


@pytest.mark.parametrize(
    ("tool_name", "required_flag"),
    (
        ("emlis_nls_v3_step11_dependency_manifest.py", "--before-manifest"),
        ("emlis_nls_v3_step11_batch_run.py", "--before-dependency-manifest"),
        ("emlis_nls_v3_step11_regression.py", "--before-dependency-manifest"),
    ),
)
def test_rc0020_execution_tools_require_explicit_rc0019_parent(
    tool_name: str,
    required_flag: str,
) -> None:
    result = subprocess.run(
        [sys.executable, str(_REPO / "ai/tools" / tool_name), "--help"],
        check=False,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr
    assert required_flag in result.stdout


def test_workaround_scan_covers_every_available_input_cohort() -> None:
    samples = load_canonical_jsonl(_BATCH)
    generation_root = _REPO / "ai/services/ai_inference"
    dependency = {
        "file_hashes": [
            {
                "path": path.relative_to(_REPO).as_posix(),
                "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            }
            for path in sorted(generation_root.glob("*.py"))
            if path.name in finalize._GENERATION_OWNER_NAMES
        ]
    }
    counts, _policy, attacks, scope = finalize.scan_case_specific_workarounds(
        dependency,
        samples,
    )

    assert counts == {dimension: 0 for dimension in finalize._DIMENSIONS}
    assert all(attacks.values())
    assert scope["aggregate"] == {
        "cohort_count": 4,
        "case_count": 173,
        "input_literal_count": 1042,
        "scanned_literal_count": 266,
        "unique_scanned_literal_count": 266,
    }
    assert {
        row["cohort"]: row["case_count"] for row in scope["cohorts"]
    } == {
        "karen_batch001": 100,
        "known28": 28,
        "development42": 42,
        "legacy3": 3,
    }
    assert scope["raw_input_included"] is False
    assert scope["body_free"] is True

    texts, recomputed_scope = finalize._workaround_scan_input_material(samples)
    assert recomputed_scope == scope
    karen_normalized = {
        finalize._normalise(text)
        for sample in samples
        for text in finalize._input_string_leaves(sample["input"])
    }
    known_only = next(
        text
        for case in load_baseline_cases()
        for text in finalize._input_string_leaves(dict(case.current_input))
        if len(finalize._normalise(text)) >= 12
        and finalize._normalise(text) not in karen_normalized
    )
    assert finalize._scan_one_source(
        f"VALUE = {known_only!r}\n", input_texts=texts
    )["input_specific_literal"] > 0
    assert known_only not in repr(scope)


def test_lineage_builder_constructs_only_receipt_backed_execution_events(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    historical_manifests = [
        _manifest(f"nls_v3_rc_{number:04d}")
        for number in (11, 14, 15, 16, 18, 19)
    ]
    historical_summaries = [
        _summary(f"nls_v3_rc_{number:04d}")
        for number in (14, 15, 16, 18, 19)
    ]
    initial = _summary("nls_v3_rc_0010")
    final = _summary("nls_v3_rc_0020")
    current = _manifest("nls_v3_rc_0020", current=True)
    scan_scope = {
        "schema_version": finalize._WORKAROUND_SCAN_INPUT_SCOPE_SCHEMA,
        "aggregate": {"case_count": 173},
        "raw_input_included": False,
        "body_free": True,
    }
    captured: dict[str, Any] = {}

    def fake_lineage_builder(
        events: list[dict[str, Any]],
        *,
        dependency_manifests: list[dict[str, Any]],
        batch_run_summaries: list[dict[str, Any]],
    ) -> dict[str, Any]:
        captured["events"] = events
        captured["manifests"] = dependency_manifests
        captured["summaries"] = batch_run_summaries
        return {"events": events, "body_free": True}

    monkeypatch.setattr(
        finalize,
        "build_rc0010_rc0020_correction_rerun_lineage",
        fake_lineage_builder,
    )
    lineage, support, manifests, summaries = (
        finalize._build_rc0010_rc0020_lineage(
            initial_summary=initial,
            initial_review={"body_free": True},
            final_summary=final,
            dependency_manifest=current,
            historical_dependency_manifests=historical_manifests,
            historical_batch_run_summaries=historical_summaries,
            workaround_scan_input_scope=scan_scope,
        )
    )

    assert lineage == {"events": captured["events"], "body_free": True}
    assert [row["candidate_version_id"] for row in manifests] == [
        "nls_v3_rc_0011",
        "nls_v3_rc_0014",
        "nls_v3_rc_0015",
        "nls_v3_rc_0016",
        "nls_v3_rc_0018",
        "nls_v3_rc_0019",
        "nls_v3_rc_0020",
    ]
    assert [row["candidate_version_id"] for row in summaries] == [
        "nls_v3_rc_0010",
        "nls_v3_rc_0014",
        "nls_v3_rc_0015",
        "nls_v3_rc_0016",
        "nls_v3_rc_0018",
        "nls_v3_rc_0019",
        "nls_v3_rc_0020",
    ]
    events = captured["events"]
    executions = {
        row["candidate_version_id"]: row["execution_scope"]
        for row in events
        if row["event_type"] == "execution_observed"
    }
    assert executions == {
        "nls_v3_rc_0014": "formal_cumulative_rerun",
        "nls_v3_rc_0015": "formal_cumulative_rerun",
        "nls_v3_rc_0016": "formal_cumulative_rerun",
        "nls_v3_rc_0018": "preflight",
        "nls_v3_rc_0019": "preflight",
        "nls_v3_rc_0020": "formal_cumulative_rerun",
    }
    corrections = {
        row["candidate_version_id"]: row
        for row in events
        if row["event_type"] == "correction_recorded"
    }
    assert {
        candidate: corrections[candidate]["source_state_kind"]
        for candidate in (
            "nls_v3_rc_0012",
            "nls_v3_rc_0013",
            "nls_v3_rc_0017",
        )
    } == {
        "nls_v3_rc_0012": "historical_unfrozen_no_receipt",
        "nls_v3_rc_0013": "historical_unfrozen_no_receipt",
        "nls_v3_rc_0017": "historical_unfrozen_no_receipt",
    }
    dispositions = {
        row["candidate_version_id"]: row["disposition"]
        for row in events
        if row["event_type"] == "revision_disposition"
    }
    assert dispositions["nls_v3_rc_0011"] == "superseded_unexecuted"
    assert dispositions["nls_v3_rc_0018"] == (
        "superseded_after_observed_result"
    )
    assert dispositions["nls_v3_rc_0019"] == (
        "superseded_after_observed_result"
    )
    assert dispositions["nls_v3_rc_0020"] == "cycle_final_candidate"
    assert support["aggregate"] == {
        "correction_count": 10,
        "retained_dependency_manifest_count": 7,
        "retained_batch_summary_count": 7,
        "historical_no_receipt_correction_count": 3,
        "unreceipted_execution_claim_count": 0,
    }
    current_support = support["rows"][-1]
    assert current_support["negative_suite"][
        "workaround_scan_input_scope_sha256"
    ] == artifact_sha256(scan_scope)


def test_finalizer_rejects_invalid_dev_receipt_or_reused_run_id(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    parents = {
        "final_summary": {"run_id": "nls3run_0020c001aaaaaaaa"},
        "dependency_manifest": {},
        "known28_receipt": {"run_id": "nls3run_0020c001bbbbbbbb"},
        "development42_receipt": {"run_id": "nls3run_0020c001cccccccc"},
        "invalid16_receipt": {"run_id": "nls3run_0020c001dddddddd"},
    }
    monkeypatch.setattr(
        finalize,
        "validate_development42_receipt",
        lambda *_args, **_kwargs: (),
    )
    finalize._validate_finalizer_regression_parents(**parents)

    parents["invalid16_receipt"] = {
        "run_id": parents["development42_receipt"]["run_id"]
    }
    with pytest.raises(ValueError, match="step11_finalize_run_ids_not_distinct"):
        finalize._validate_finalizer_regression_parents(**parents)

    monkeypatch.setattr(
        finalize,
        "validate_development42_receipt",
        lambda *_args, **_kwargs: ("DEV42_TAMPER",),
    )
    with pytest.raises(ValueError, match="step11_finalize_development42_invalid"):
        finalize._validate_finalizer_regression_parents(**parents)
