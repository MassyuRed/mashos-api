# -*- coding: utf-8 -*-
from __future__ import annotations

"""P4-2 fixture connector for body-free material audit.

The fixture may read local synthetic P3 baseline case material in order to build
material slots, but all exported audit packets and summaries are body-free.
"""

from collections.abc import Mapping, Sequence
import json
from typing import Any

from emlis_ai_product_readfeel_p4_material_audit import (
    PRODUCT_READFEEL_P4_MATERIAL_AUDIT_PROFILE_20260610,
    PRODUCT_READFEEL_P4_MATERIAL_AUDIT_STEP_20260610,
    PRODUCT_READFEEL_P4_MATERIAL_AUDIT_SUMMARY_VERSION_20260610,
    PRODUCT_READFEEL_P4_MATERIAL_AUDIT_VERSION_20260610,
    assert_product_readfeel_p4_material_audit_meta_only_20260610,
    build_product_readfeel_p4_material_audit_20260610,
    build_product_readfeel_p4_material_audit_public_summary_20260610,
)
from fixtures.emlis_ai_product_readfeel_baseline_cases_20260609 import (
    build_product_readfeel_baseline_cases_20260609,
)
from fixtures.emlis_ai_product_readfeel_p4_target_cases_20260610 import (
    build_product_readfeel_p4_target_case_selection_from_p3_9_20260610,
)


def build_product_readfeel_p4_material_audit_from_p4_1_20260610(
    *,
    target_case_selection_payload: Mapping[str, Any] | None = None,
    local_baseline_cases: Sequence[Mapping[str, Any]] | None = None,
    run_id: str | None = None,
    audit_route_overrides_by_case_ref_id: Mapping[str, Mapping[str, Any]] | None = None,
    surface_observations_by_case_ref_id: Mapping[str, Mapping[str, Any]] | None = None,
) -> dict[str, Any]:
    selection = target_case_selection_payload or build_product_readfeel_p4_target_case_selection_from_p3_9_20260610(
        run_id=run_id or "p4_2_source_target_case_selection"
    )
    local_cases = local_baseline_cases or build_product_readfeel_baseline_cases_20260609()
    audit = build_product_readfeel_p4_material_audit_20260610(
        target_case_selection_payload=selection,
        local_baseline_cases=local_cases,
        run_id=run_id or "p4_2_material_audit_fixture",
        audit_route_overrides_by_case_ref_id=audit_route_overrides_by_case_ref_id,
        surface_observations_by_case_ref_id=surface_observations_by_case_ref_id,
    )
    assert_product_readfeel_p4_material_audit_meta_only_20260610(audit)
    return audit


def build_product_readfeel_p4_material_audit_summary_from_p4_1_20260610(
    *,
    target_case_selection_payload: Mapping[str, Any] | None = None,
    local_baseline_cases: Sequence[Mapping[str, Any]] | None = None,
    run_id: str | None = None,
    audit_route_overrides_by_case_ref_id: Mapping[str, Mapping[str, Any]] | None = None,
    surface_observations_by_case_ref_id: Mapping[str, Mapping[str, Any]] | None = None,
) -> dict[str, Any]:
    audit = build_product_readfeel_p4_material_audit_from_p4_1_20260610(
        target_case_selection_payload=target_case_selection_payload,
        local_baseline_cases=local_baseline_cases,
        run_id=run_id,
        audit_route_overrides_by_case_ref_id=audit_route_overrides_by_case_ref_id,
        surface_observations_by_case_ref_id=surface_observations_by_case_ref_id,
    )
    return build_product_readfeel_p4_material_audit_public_summary_20260610(audit)


def dump_product_readfeel_p4_material_audit_summary_from_p4_1_20260610(
    *,
    target_case_selection_payload: Mapping[str, Any] | None = None,
    local_baseline_cases: Sequence[Mapping[str, Any]] | None = None,
    run_id: str | None = None,
    audit_route_overrides_by_case_ref_id: Mapping[str, Mapping[str, Any]] | None = None,
    surface_observations_by_case_ref_id: Mapping[str, Mapping[str, Any]] | None = None,
) -> str:
    summary = build_product_readfeel_p4_material_audit_summary_from_p4_1_20260610(
        target_case_selection_payload=target_case_selection_payload,
        local_baseline_cases=local_baseline_cases,
        run_id=run_id,
        audit_route_overrides_by_case_ref_id=audit_route_overrides_by_case_ref_id,
        surface_observations_by_case_ref_id=surface_observations_by_case_ref_id,
    )
    return json.dumps(summary, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


__all__ = [
    "PRODUCT_READFEEL_P4_MATERIAL_AUDIT_VERSION_20260610",
    "PRODUCT_READFEEL_P4_MATERIAL_AUDIT_SUMMARY_VERSION_20260610",
    "PRODUCT_READFEEL_P4_MATERIAL_AUDIT_STEP_20260610",
    "PRODUCT_READFEEL_P4_MATERIAL_AUDIT_PROFILE_20260610",
    "assert_product_readfeel_p4_material_audit_meta_only_20260610",
    "build_product_readfeel_p4_material_audit_from_p4_1_20260610",
    "build_product_readfeel_p4_material_audit_summary_from_p4_1_20260610",
    "dump_product_readfeel_p4_material_audit_summary_from_p4_1_20260610",
]
