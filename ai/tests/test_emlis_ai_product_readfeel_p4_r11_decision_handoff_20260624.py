# -*- coding: utf-8 -*-
from __future__ import annotations

from copy import deepcopy
from functools import lru_cache

import emlis_ai_product_readfeel_p4_r11_residual_family_surface_audit as r11
import emlis_ai_product_readfeel_p4_r11_surface_specificity_role_verdict_audit as r11_r6r7
import emlis_ai_product_readfeel_p4_r11_summary_decision_handoff as r11_r8
from fixtures.emlis_ai_product_readfeel_baseline_cases_20260609 import (
    build_product_readfeel_baseline_cases_20260609,
    build_product_readfeel_baseline_public_safe_index_20260609,
)


@lru_cache(maxsize=1)
def _cached_sources() -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    return (
        build_product_readfeel_baseline_public_safe_index_20260609(),
        build_product_readfeel_baseline_cases_20260609(),
    )


def _baseline() -> list[dict[str, object]]:
    return deepcopy(_cached_sources()[0])


def _local_cases() -> list[dict[str, object]]:
    return deepcopy(_cached_sources()[1])


def _passing_probe_for_row(row: dict[str, object]) -> str:
    return " ".join(str(role) for role in row.get("required_surface_role_ids") or ())


def test_r11_8_decision_handoff_returns_r54_candidate_when_no_current_only_blocker() -> None:
    baseline = _baseline()
    scope = r11.build_product_readfeel_p4_r11_residual_family_scope_matrix_20260624(
        baseline_public_safe_index=baseline,
        run_id="p4_r11_decision_handoff_scope",
    )
    selection = r11.build_product_readfeel_p4_r11_case_ref_selection_coverage_audit_20260624(
        scope_matrix=scope,
        baseline_public_safe_index=baseline,
        run_id="p4_r11_decision_handoff_selection",
    )
    material = r11.build_product_readfeel_p4_r11_material_route_audit_20260624(
        case_ref_selection_payload=selection,
        local_baseline_cases=_local_cases(),
        run_id="p4_r11_decision_handoff_material",
    )
    surface = r11.build_product_readfeel_p4_r11_surface_path_audit_20260624(
        material_route_audit_payload=material,
        local_baseline_cases=_local_cases(),
        run_id="p4_r11_decision_handoff_surface",
    )
    probes = [
        {"case_ref_id": row["case_ref_id"], "local_visible_surface": _passing_probe_for_row(row)}
        for row in surface["audit_rows"]
        if isinstance(row, dict)
    ]
    specificity = r11_r6r7.build_product_readfeel_p4_r11_surface_specificity_role_audit_20260624(
        surface_path_audit_payload=surface,
        local_surface_probes=probes,
        run_id="p4_r11_decision_handoff_specificity",
    )
    verdict = r11_r6r7.build_product_readfeel_p4_r11_verdict_repair_candidate_classification_20260624(
        surface_specificity_role_audit_payload=specificity,
        run_id="p4_r11_decision_handoff_verdict",
    )
    handoff = r11_r8.build_product_readfeel_p4_r11_summary_decision_handoff_20260624(
        verdict_repair_classification_payload=verdict,
        run_id="p4_r11_decision_handoff",
    )

    assert handoff["decision_handoff"]["decision_ref"] == r11_r8.P4_R11_DECISION_RETURN_TO_R54_ACTUAL_REVIEW_CANDIDATE_20260624
    assert handoff["decision_handoff"]["r55_decision_preserved"] is True
    assert handoff["decision_handoff"]["p5_human_review_evidence_created_here"] is False
    assert handoff["decision_handoff"]["question_observation_rows_created_here"] is False
    assert handoff["decision_handoff"]["p8_start_allowed"] is False
    assert handoff["decision_handoff"]["release_allowed"] is False
    r11.assert_product_readfeel_p4_r11_residual_surface_audit_meta_only_20260624(handoff)
