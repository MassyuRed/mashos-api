# -*- coding: utf-8 -*-
from __future__ import annotations

"""P3-8 fixture connector for Product Read Feel regression confirmation.

This fixture connects the P3-7 first repair design to a body-free regression
plan/result envelope.  It does not retain local review packets, rendered output
bodies, raw test logs, or source inputs.
"""

from collections.abc import Mapping, Sequence
import json
from typing import Any

from emlis_ai_product_readfeel_p3_regression import (
    PRODUCT_READFEEL_P3_REGRESSION_STEP_20260609,
    PRODUCT_READFEEL_P3_REGRESSION_SUMMARY_VERSION_20260609,
    PRODUCT_READFEEL_P3_REGRESSION_VERSION_20260609,
    assert_product_readfeel_p3_regression_meta_only_20260609,
    build_product_readfeel_p3_regression_green_fixture_results_20260609,
    build_product_readfeel_p3_regression_plan_20260609,
    build_product_readfeel_p3_regression_public_summary_20260609,
    build_product_readfeel_p3_regression_result_20260609,
    dump_product_readfeel_p3_regression_public_summary_20260609,
)
from fixtures.emlis_ai_product_readfeel_p3_first_repair_design_20260609 import (
    build_product_readfeel_p3_first_repair_design_from_repair_priority_ledger_20260609,
)


def build_product_readfeel_p3_regression_plan_from_first_repair_design_20260609(
    *,
    first_repair_design: Mapping[str, Any] | None = None,
    renderer: Any = None,
    run_id: str | None = None,
    include_optional_suites: bool = True,
) -> dict[str, Any]:
    design = first_repair_design or build_product_readfeel_p3_first_repair_design_from_repair_priority_ledger_20260609(
        renderer=renderer,
        run_id=run_id or "p3_8_first_repair_design_fixture",
    )
    plan = build_product_readfeel_p3_regression_plan_20260609(
        first_repair_design=design,
        run_id=run_id or str(design.get("run_id") or "p3_8_regression_plan_fixture"),
        include_optional_suites=include_optional_suites,
    )
    assert_product_readfeel_p3_regression_meta_only_20260609(plan)
    return plan


def build_product_readfeel_p3_regression_result_from_first_repair_design_20260609(
    *,
    first_repair_design: Mapping[str, Any] | None = None,
    regression_plan: Mapping[str, Any] | None = None,
    command_results: Sequence[Mapping[str, Any]] | None = None,
    renderer: Any = None,
    run_id: str | None = None,
    include_optional_timeout: bool = False,
) -> dict[str, Any]:
    plan = regression_plan or build_product_readfeel_p3_regression_plan_from_first_repair_design_20260609(
        first_repair_design=first_repair_design,
        renderer=renderer,
        run_id=run_id,
        include_optional_suites=True,
    )
    results = list(command_results) if command_results is not None else build_product_readfeel_p3_regression_green_fixture_results_20260609(
        include_optional_timeout=include_optional_timeout
    )
    regression = build_product_readfeel_p3_regression_result_20260609(
        regression_plan=plan,
        command_results=results,
        run_id=run_id or str(plan.get("run_id") or "p3_8_regression_result_fixture"),
    )
    assert_product_readfeel_p3_regression_meta_only_20260609(regression)
    return regression


def build_product_readfeel_p3_regression_summary_from_first_repair_design_20260609(
    *,
    first_repair_design: Mapping[str, Any] | None = None,
    regression_plan: Mapping[str, Any] | None = None,
    command_results: Sequence[Mapping[str, Any]] | None = None,
    renderer: Any = None,
    run_id: str | None = None,
    include_optional_timeout: bool = False,
) -> dict[str, Any]:
    regression = build_product_readfeel_p3_regression_result_from_first_repair_design_20260609(
        first_repair_design=first_repair_design,
        regression_plan=regression_plan,
        command_results=command_results,
        renderer=renderer,
        run_id=run_id,
        include_optional_timeout=include_optional_timeout,
    )
    return build_product_readfeel_p3_regression_public_summary_20260609(regression)


def dump_product_readfeel_p3_regression_summary_from_first_repair_design_20260609(
    *,
    first_repair_design: Mapping[str, Any] | None = None,
    regression_plan: Mapping[str, Any] | None = None,
    command_results: Sequence[Mapping[str, Any]] | None = None,
    renderer: Any = None,
    run_id: str | None = None,
    include_optional_timeout: bool = False,
) -> str:
    summary = build_product_readfeel_p3_regression_summary_from_first_repair_design_20260609(
        first_repair_design=first_repair_design,
        regression_plan=regression_plan,
        command_results=command_results,
        renderer=renderer,
        run_id=run_id,
        include_optional_timeout=include_optional_timeout,
    )
    return json.dumps(summary, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


__all__ = [
    "PRODUCT_READFEEL_P3_REGRESSION_VERSION_20260609",
    "PRODUCT_READFEEL_P3_REGRESSION_SUMMARY_VERSION_20260609",
    "PRODUCT_READFEEL_P3_REGRESSION_STEP_20260609",
    "assert_product_readfeel_p3_regression_meta_only_20260609",
    "build_product_readfeel_p3_regression_green_fixture_results_20260609",
    "build_product_readfeel_p3_regression_plan_from_first_repair_design_20260609",
    "build_product_readfeel_p3_regression_result_from_first_repair_design_20260609",
    "build_product_readfeel_p3_regression_summary_from_first_repair_design_20260609",
    "dump_product_readfeel_p3_regression_public_summary_20260609",
    "dump_product_readfeel_p3_regression_summary_from_first_repair_design_20260609",
]
