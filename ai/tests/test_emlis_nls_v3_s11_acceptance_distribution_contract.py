# -*- coding: utf-8 -*-
from __future__ import annotations

"""Cycle001 expanded-parent and distribution-bypass RED tests."""

from copy import deepcopy
import hashlib
import inspect
from typing import Any

import pytest

import emlis_ai_step11_cycle_evidence_v3 as evidence
from emlis_ai_nls_v3_artifact_contract import artifact_sha256


def _sha(label: str) -> str:
    return hashlib.sha256(label.encode("utf-8")).hexdigest()


def _balanced_rows() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for index, case_id in enumerate(evidence._CASE_IDS):
        semantic_family = f"semantic_family_{index % 6}"
        opening = f"{semantic_family}_variant_{(index // 6) % 2}"
        rows.append(
            {
                "case_id": case_id,
                "status": "selected",
                "receipt": {
                    "selected_candidate_body_commitment": _sha(
                        f"body:{index}"
                    )
                },
                "surface_profile": {
                    "opening_family": opening,
                    "opening_semantic_family": semantic_family,
                    "opening_variant_id": opening,
                    "ending_family": f"ending_variant_{index % 4}",
                    "predicate_families": ["observed_nucleus"],
                    "reception_act_families": ["hold_in_attention"],
                    "reception_content_kind": "anaphoric",
                    "observation_literal_count": 1,
                    "unique_literal_owner_count": 1,
                    "literal_replay_count": 0,
                    "reception_literal_count": 0,
                    "near_duplicate_skeleton_commitment": _sha(
                        f"skeleton:{index % 5}"
                    ),
                },
            }
        )
    return rows


def _assessment(rows: list[dict[str, Any]]) -> dict[str, Any]:
    return evidence._surface_distribution_assessment(
        rows,
        candidate_version_id=evidence.STEP11_CURRENT_CANDIDATE_VERSION_ID,
    )


def test_balanced_full100_distribution_passes_all_frozen_dimensions() -> None:
    assessment = _assessment(_balanced_rows())

    assert evidence.STEP11_SURFACE_DISTRIBUTION_POLICY_SHA256 == (
        evidence.FROZEN_STEP11_SURFACE_DISTRIBUTION_POLICY_SHA256
    )
    assert assessment["selected_profile_count"] == 100
    assert assessment["global_evaluated_dimension_count"] == 3
    assert assessment["global_failed_dimension_count"] == 0
    assert assessment["semantic_evaluated_family_count"] == 6
    assert assessment["semantic_failed_family_count"] == 0
    assert assessment["semantic_family_accounted_case_count"] == 100
    assert assessment["semantic_family_coverage_complete"] is True
    assert assessment["exact_output_evaluated_case_count"] == 100
    assert assessment["exact_output_duplicate_case_count"] == 0
    assert assessment["acceptance_passed"] is True


def test_all_same_terminal_fails_even_with_balanced_openings() -> None:
    rows = _balanced_rows()
    for row in rows:
        row["surface_profile"]["ending_family"] = "ending_same"

    assessment = _assessment(rows)
    ending = next(
        row for row in assessment["global_rows"]
        if row["dimension"] == "ending_variant"
    )
    assert ending["evaluated_case_count"] == 100
    assert ending["dominant_variant_count"] == 100
    assert ending["policy_passed"] is False
    assert assessment["acceptance_passed"] is False


def test_all_same_skeleton_fails_even_with_balanced_openings_and_endings() -> None:
    rows = _balanced_rows()
    skeleton = _sha("same-skeleton")
    for row in rows:
        row["surface_profile"]["near_duplicate_skeleton_commitment"] = skeleton

    assessment = _assessment(rows)
    skeleton_row = next(
        row for row in assessment["global_rows"]
        if row["dimension"] == "surface_skeleton"
    )
    assert skeleton_row["dominant_variant_count"] == 100
    assert skeleton_row["policy_passed"] is False
    assert assessment["acceptance_passed"] is False


def test_six_family_single_variant_sparse_bypass_is_closed() -> None:
    rows = _balanced_rows()
    for index, row in enumerate(rows):
        family = f"semantic_family_{index % 6}"
        row["surface_profile"]["opening_semantic_family"] = family
        row["surface_profile"]["opening_family"] = f"{family}_only"
        row["surface_profile"]["opening_variant_id"] = f"{family}_only"

    assessment = _assessment(rows)
    opening = next(
        row for row in assessment["global_rows"]
        if row["dimension"] == "opening_variant"
    )
    assert opening["distinct_variant_count"] == 6
    assert opening["policy_passed"] is True
    assert assessment["semantic_evaluated_family_count"] == 6
    assert assessment["semantic_failed_family_count"] == 6
    assert all(
        row["policy_passed"] is False
        for row in assessment["semantic_family_rows"]
    )
    assert assessment["acceptance_passed"] is False


def test_singleton_semantic_family_is_recorded_without_false_failure() -> None:
    rows = _balanced_rows()
    rows[0]["surface_profile"]["opening_semantic_family"] = "singleton_family"
    rows[0]["surface_profile"]["opening_family"] = "singleton_only"
    rows[0]["surface_profile"]["opening_variant_id"] = "singleton_only"

    assessment = _assessment(rows)
    singleton = next(
        row for row in assessment["semantic_family_rows"]
        if row["opening_semantic_family"] == "singleton_family"
    )
    assert singleton["case_count"] == 1
    assert singleton["policy_evaluated"] is False
    assert singleton["policy_passed"] is None
    assert singleton["singleton_disposition"] == "recorded_not_failed"
    assert assessment["semantic_family_coverage_complete"] is True
    assert assessment["acceptance_passed"] is True


def test_exact_output_duplicate_bypass_is_closed() -> None:
    rows = _balanced_rows()
    duplicate = _sha("same-output")
    for row in rows:
        row["receipt"]["selected_candidate_body_commitment"] = duplicate

    assessment = _assessment(rows)
    assert assessment["exact_output_coverage_complete"] is True
    assert assessment["exact_output_duplicate_cluster_count"] == 1
    assert assessment["exact_output_duplicate_case_count"] == 100
    assert assessment["acceptance_passed"] is False


def _auxiliary_parents() -> dict[str, Any]:
    return {
        "final_run_id": "nls3run_0019c00100000001",
        "known": {
            "run_id": "nls3run_0019c00100000002",
            "aggregate": {"case_count": 28, "contract_pass_count": 28},
        },
        "development": {
            "run_id": "nls3run_0019c00100000003",
            "aggregate": {
                "case_count": 42,
                "pass_count": 42,
                "app_reachable_count": 24,
                "selected_count": 24,
                "hard_gate_pass_count": 24,
                "expected_non_applicable_count": 18,
                "expected_non_applicable_match_count": 18,
            },
        },
        "available_scope": {
            "scope_aggregate": {
                "known_machine_execution_case_count": 70,
                "legacy_registered_case_count": 3,
                "legacy_app_reachable_to_execute_count": 0,
                "legacy_expected_non_applicable_count": 3,
                "available_real_user_current_valid_count": 0,
            }
        },
        "invalid": {
            "run_id": "nls3run_0019c00100000004",
            "aggregate": {
                "case_count": 16,
                "expected_rejection_match_count": 16,
                "under_rejected_count": 0,
            },
        },
        "correction_lineage": {
            "historical_sequence_complete": True,
            "acceptance_lineage_ready": True,
            "aggregate": {"unreceipted_execution_claim_count": 0},
        },
        "lineage_final_binding": {
            "candidate_version_id": (
                evidence.STEP11_CURRENT_CANDIDATE_VERSION_ID
            ),
            "run_id": "nls3run_0019c00100000001",
        },
    }


def test_expanded_auxiliary_counts_and_four_run_ids_are_exact() -> None:
    parents = _auxiliary_parents()
    conditions = evidence._auxiliary_acceptance_conditions(**parents)
    assert all(conditions.values())

    duplicate_run = deepcopy(parents)
    duplicate_run["development"]["run_id"] = duplicate_run["known"]["run_id"]
    conditions = evidence._auxiliary_acceptance_conditions(**duplicate_run)
    assert conditions[
        "final_known_development_invalid_run_ids_pairwise_distinct"
    ] is False

    wrong_scope = deepcopy(parents)
    wrong_scope["available_scope"]["scope_aggregate"][
        "known_machine_execution_case_count"
    ] = 69
    conditions = evidence._auxiliary_acceptance_conditions(**wrong_scope)
    assert conditions["known_regression_registered_case_count_70"] is False


def test_lineage_final_binding_uses_exact_summary_and_manifest_parents(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    final_run_id = "nls3run_0019c00100000001"
    closure = _sha("closure")
    final_summary = {"artifact": "final-summary", "body_free": True}
    final_manifest = {"artifact": "final-manifest", "body_free": True}
    summary_sha = artifact_sha256(final_summary)
    manifest_sha = artifact_sha256(final_manifest)
    monkeypatch.setattr(
        evidence,
        "_project_final",
        lambda summary, manifest: {
            "candidate_version_id": (
                evidence.STEP11_CURRENT_CANDIDATE_VERSION_ID
            ),
            "run_id": final_run_id,
            "source_dependency_closure_sha256": closure,
        },
    )
    monkeypatch.setattr(
        evidence,
        "_validated_dependency_manifest",
        lambda manifest: dict(manifest),
    )
    final_event_commitment = _sha("final-event")
    lineage = {
        "lineage_head_commitment": final_event_commitment,
        "events": [
            {
                "event_type": "correction_recorded",
                "candidate_version_id": (
                    evidence.STEP11_CURRENT_CANDIDATE_VERSION_ID
                ),
                "source_state_kind": "dependency_manifest",
                "dependency_manifest_sha256": manifest_sha,
                "source_state_artifact_sha256": manifest_sha,
                "source_dependency_closure_sha256": closure,
            },
            {
                "event_type": "execution_observed",
                "candidate_version_id": (
                    evidence.STEP11_CURRENT_CANDIDATE_VERSION_ID
                ),
                "execution_scope": "formal_cumulative_rerun",
                "batch_summary_sha256": summary_sha,
                "outcome_receipt_commitment": summary_sha,
                "run_id": final_run_id,
                "source_dependency_closure_sha256": closure,
                "machine_status": "clean",
                "counts_as_clean_formal_rerun": True,
            },
            {
                "event_type": "revision_disposition",
                "candidate_version_id": (
                    evidence.STEP11_CURRENT_CANDIDATE_VERSION_ID
                ),
                "disposition": "cycle_final_candidate",
                "counts_as_passed_rerun": True,
                "event_commitment": final_event_commitment,
            },
        ],
    }

    binding = evidence._require_lineage_final_parent_binding(
        lineage,
        final_batch_summary=final_summary,
        final_dependency_manifest=final_manifest,
    )
    assert binding["final_batch_summary_sha256"] == summary_sha
    assert binding["final_dependency_manifest_sha256"] == manifest_sha

    forged_summary = {**final_summary, "artifact": "different-summary"}
    with pytest.raises(
        evidence.Step11CycleEvidenceError,
        match="LINEAGE_FINAL_PARENT_BINDING_INVALID",
    ):
        evidence._require_lineage_final_parent_binding(
            lineage,
            final_batch_summary=forged_summary,
            final_dependency_manifest=final_manifest,
        )


def test_cumulative_and_acceptance_require_expanded_parent_set() -> None:
    required = {
        "development42_receipt",
        "available_input_scope_receipt",
        "correction_rerun_lineage",
        "lineage_dependency_manifests",
        "lineage_batch_run_summaries",
    }
    assert required <= set(
        inspect.signature(evidence.build_cumulative100_receipt).parameters
    )
    assert required <= set(
        inspect.signature(evidence.build_cycle001_acceptance).parameters
    )
