# -*- coding: utf-8 -*-
from __future__ import annotations

"""P4-1 fixture connector for body-free target case selection.

The fixture uses the P3-9 connection decision and the P3-1 public-safe baseline
index.  It never keeps synthetic input bodies, rendered Emlis ``comment_text``
bodies, raw history text, or raw test logs.
"""

from collections.abc import Mapping, Sequence
import json
from typing import Any

from emlis_ai_product_readfeel_p4_target_case_selection import (
    PRODUCT_READFEEL_P4_TARGET_CASE_SELECTION_PROFILE_20260610,
    PRODUCT_READFEEL_P4_TARGET_CASE_SELECTION_STEP_20260610,
    PRODUCT_READFEEL_P4_TARGET_CASE_SELECTION_SUMMARY_VERSION_20260610,
    PRODUCT_READFEEL_P4_TARGET_CASE_SELECTION_VERSION_20260610,
    assert_product_readfeel_p4_target_case_selection_meta_only_20260610,
    build_product_readfeel_p4_target_case_selection_20260610,
    build_product_readfeel_p4_target_case_selection_public_summary_20260610,
)
from fixtures.emlis_ai_product_readfeel_baseline_cases_20260609 import (
    build_product_readfeel_baseline_public_safe_index_20260609,
)
from fixtures.emlis_ai_product_readfeel_p3_p4_p5_connection_decision_20260609 import (
    build_product_readfeel_p3_p4_p5_connection_decision_from_regression_20260609,
)


def build_product_readfeel_p4_target_case_selection_from_p3_9_20260610(
    *,
    p3_connection_decision: Mapping[str, Any] | None = None,
    baseline_public_safe_index: Sequence[Mapping[str, Any]] | None = None,
    run_id: str | None = None,
) -> dict[str, Any]:
    decision = p3_connection_decision or build_product_readfeel_p3_p4_p5_connection_decision_from_regression_20260609(
        run_id=run_id or "p4_1_source_p3_9_connection_decision"
    )
    baseline_index = baseline_public_safe_index or build_product_readfeel_baseline_public_safe_index_20260609()
    selection = build_product_readfeel_p4_target_case_selection_20260610(
        p3_connection_decision=decision,
        baseline_public_safe_index=baseline_index,
        run_id=run_id or "p4_1_target_case_selection_fixture",
    )
    assert_product_readfeel_p4_target_case_selection_meta_only_20260610(selection)
    return selection


def build_product_readfeel_p4_target_case_selection_summary_from_p3_9_20260610(
    *,
    p3_connection_decision: Mapping[str, Any] | None = None,
    baseline_public_safe_index: Sequence[Mapping[str, Any]] | None = None,
    run_id: str | None = None,
) -> dict[str, Any]:
    selection = build_product_readfeel_p4_target_case_selection_from_p3_9_20260610(
        p3_connection_decision=p3_connection_decision,
        baseline_public_safe_index=baseline_public_safe_index,
        run_id=run_id,
    )
    return build_product_readfeel_p4_target_case_selection_public_summary_20260610(selection)


def dump_product_readfeel_p4_target_case_selection_summary_from_p3_9_20260610(
    *,
    p3_connection_decision: Mapping[str, Any] | None = None,
    baseline_public_safe_index: Sequence[Mapping[str, Any]] | None = None,
    run_id: str | None = None,
) -> str:
    summary = build_product_readfeel_p4_target_case_selection_summary_from_p3_9_20260610(
        p3_connection_decision=p3_connection_decision,
        baseline_public_safe_index=baseline_public_safe_index,
        run_id=run_id,
    )
    return json.dumps(summary, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


__all__ = [
    "PRODUCT_READFEEL_P4_TARGET_CASE_SELECTION_VERSION_20260610",
    "PRODUCT_READFEEL_P4_TARGET_CASE_SELECTION_SUMMARY_VERSION_20260610",
    "PRODUCT_READFEEL_P4_TARGET_CASE_SELECTION_STEP_20260610",
    "PRODUCT_READFEEL_P4_TARGET_CASE_SELECTION_PROFILE_20260610",
    "assert_product_readfeel_p4_target_case_selection_meta_only_20260610",
    "build_product_readfeel_p4_target_case_selection_from_p3_9_20260610",
    "build_product_readfeel_p4_target_case_selection_summary_from_p3_9_20260610",
    "dump_product_readfeel_p4_target_case_selection_summary_from_p3_9_20260610",
]
