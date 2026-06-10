# -*- coding: utf-8 -*-
from __future__ import annotations

"""P4-4 fixture connector for body-free family tuning policy.

The fixture connects P4-1 target cases and P4-2 material audit outputs to the
P4-4 family policy packet.  It never keeps synthetic input bodies, rendered
Emlis ``comment_text`` bodies, raw history text, or raw test logs.
"""

from collections.abc import Mapping
import json
from typing import Any

from emlis_ai_product_readfeel_p4_family_tuning_policy import (
    PRODUCT_READFEEL_P4_FAMILY_TUNING_POLICY_PROFILE_20260610,
    PRODUCT_READFEEL_P4_FAMILY_TUNING_POLICY_STEP_20260610,
    PRODUCT_READFEEL_P4_FAMILY_TUNING_POLICY_SUMMARY_VERSION_20260610,
    PRODUCT_READFEEL_P4_FAMILY_TUNING_POLICY_VERSION_20260610,
    assert_product_readfeel_p4_family_tuning_policy_meta_only_20260610,
    build_product_readfeel_p4_family_tuning_policy_20260610,
    build_product_readfeel_p4_family_tuning_policy_public_summary_20260610,
)
from fixtures.emlis_ai_product_readfeel_p4_material_audit_20260610 import (
    build_product_readfeel_p4_material_audit_from_p4_1_20260610,
)
from fixtures.emlis_ai_product_readfeel_p4_target_cases_20260610 import (
    build_product_readfeel_p4_target_case_selection_from_p3_9_20260610,
)


def build_product_readfeel_p4_family_tuning_policy_from_p4_1_p4_2_20260610(
    *,
    target_case_selection_payload: Mapping[str, Any] | None = None,
    material_audit_payload: Mapping[str, Any] | None = None,
    run_id: str | None = None,
) -> dict[str, Any]:
    target_selection = target_case_selection_payload or build_product_readfeel_p4_target_case_selection_from_p3_9_20260610(
        run_id=run_id or "p4_4_source_p4_1_target_selection"
    )
    material_audit = material_audit_payload or build_product_readfeel_p4_material_audit_from_p4_1_20260610(
        target_case_selection_payload=target_selection,
        run_id=run_id or "p4_4_source_p4_2_material_audit",
    )
    policy = build_product_readfeel_p4_family_tuning_policy_20260610(
        target_case_selection_payload=target_selection,
        material_audit_payload=material_audit,
        run_id=run_id or "p4_4_family_tuning_policy_fixture",
    )
    assert_product_readfeel_p4_family_tuning_policy_meta_only_20260610(policy)
    return policy


def build_product_readfeel_p4_family_tuning_policy_summary_from_p4_1_p4_2_20260610(
    *,
    target_case_selection_payload: Mapping[str, Any] | None = None,
    material_audit_payload: Mapping[str, Any] | None = None,
    run_id: str | None = None,
) -> dict[str, Any]:
    policy = build_product_readfeel_p4_family_tuning_policy_from_p4_1_p4_2_20260610(
        target_case_selection_payload=target_case_selection_payload,
        material_audit_payload=material_audit_payload,
        run_id=run_id,
    )
    return build_product_readfeel_p4_family_tuning_policy_public_summary_20260610(policy)


def dump_product_readfeel_p4_family_tuning_policy_summary_from_p4_1_p4_2_20260610(
    *,
    target_case_selection_payload: Mapping[str, Any] | None = None,
    material_audit_payload: Mapping[str, Any] | None = None,
    run_id: str | None = None,
) -> str:
    summary = build_product_readfeel_p4_family_tuning_policy_summary_from_p4_1_p4_2_20260610(
        target_case_selection_payload=target_case_selection_payload,
        material_audit_payload=material_audit_payload,
        run_id=run_id,
    )
    return json.dumps(summary, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


__all__ = [
    "PRODUCT_READFEEL_P4_FAMILY_TUNING_POLICY_VERSION_20260610",
    "PRODUCT_READFEEL_P4_FAMILY_TUNING_POLICY_SUMMARY_VERSION_20260610",
    "PRODUCT_READFEEL_P4_FAMILY_TUNING_POLICY_STEP_20260610",
    "PRODUCT_READFEEL_P4_FAMILY_TUNING_POLICY_PROFILE_20260610",
    "assert_product_readfeel_p4_family_tuning_policy_meta_only_20260610",
    "build_product_readfeel_p4_family_tuning_policy_from_p4_1_p4_2_20260610",
    "build_product_readfeel_p4_family_tuning_policy_summary_from_p4_1_p4_2_20260610",
    "dump_product_readfeel_p4_family_tuning_policy_summary_from_p4_1_p4_2_20260610",
]
