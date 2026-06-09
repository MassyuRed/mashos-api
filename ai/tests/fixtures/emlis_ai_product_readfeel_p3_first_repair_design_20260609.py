# -*- coding: utf-8 -*-
from __future__ import annotations

"""P3-7 fixture connector for Product Read Feel first repair design.

This fixture connects the P3-6 repair priority ledger to P3-7 without retaining
local review packet bodies, rendered bodies, or source inputs.  It is a design
connector only; it does not change runtime rendering or release state.
"""

from collections.abc import Mapping
import json
from typing import Any

from emlis_ai_product_readfeel_p3_first_repair_design import (
    PRODUCT_READFEEL_P3_FIRST_REPAIR_DESIGN_STEP_20260609,
    PRODUCT_READFEEL_P3_FIRST_REPAIR_DESIGN_SUMMARY_VERSION_20260609,
    PRODUCT_READFEEL_P3_FIRST_REPAIR_DESIGN_VERSION_20260609,
    assert_product_readfeel_p3_first_repair_design_meta_only_20260609,
    build_product_readfeel_p3_first_repair_design_20260609,
    build_product_readfeel_p3_first_repair_design_public_summary_20260609,
    dump_product_readfeel_p3_first_repair_design_public_summary_20260609,
)
from fixtures.emlis_ai_product_readfeel_p3_repair_priority_ledger_20260609 import (
    build_product_readfeel_p3_repair_priority_ledger_from_blind_qa_20260609,
)


def build_product_readfeel_p3_first_repair_design_from_repair_priority_ledger_20260609(
    *,
    repair_priority_ledger: Mapping[str, Any] | None = None,
    renderer: Any = None,
    run_id: str | None = None,
) -> dict[str, Any]:
    if repair_priority_ledger is None:
        repair_priority_ledger = build_product_readfeel_p3_repair_priority_ledger_from_blind_qa_20260609(
            renderer=renderer,
            run_id=run_id or "p3_7_repair_priority_fixture",
        )
    design = build_product_readfeel_p3_first_repair_design_20260609(
        repair_priority_ledger=repair_priority_ledger,
        run_id=run_id or str(repair_priority_ledger.get("run_id") or "p3_7_first_repair_design_fixture"),
    )
    assert_product_readfeel_p3_first_repair_design_meta_only_20260609(design)
    return design


def build_product_readfeel_p3_first_repair_design_summary_from_repair_priority_ledger_20260609(
    *,
    repair_priority_ledger: Mapping[str, Any] | None = None,
    renderer: Any = None,
    run_id: str | None = None,
) -> dict[str, Any]:
    design = build_product_readfeel_p3_first_repair_design_from_repair_priority_ledger_20260609(
        repair_priority_ledger=repair_priority_ledger,
        renderer=renderer,
        run_id=run_id,
    )
    return build_product_readfeel_p3_first_repair_design_public_summary_20260609(design)


def dump_product_readfeel_p3_first_repair_design_summary_from_repair_priority_ledger_20260609(
    *,
    repair_priority_ledger: Mapping[str, Any] | None = None,
    renderer: Any = None,
    run_id: str | None = None,
) -> str:
    summary = build_product_readfeel_p3_first_repair_design_summary_from_repair_priority_ledger_20260609(
        repair_priority_ledger=repair_priority_ledger,
        renderer=renderer,
        run_id=run_id,
    )
    return json.dumps(summary, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


__all__ = [
    "PRODUCT_READFEEL_P3_FIRST_REPAIR_DESIGN_VERSION_20260609",
    "PRODUCT_READFEEL_P3_FIRST_REPAIR_DESIGN_SUMMARY_VERSION_20260609",
    "PRODUCT_READFEEL_P3_FIRST_REPAIR_DESIGN_STEP_20260609",
    "assert_product_readfeel_p3_first_repair_design_meta_only_20260609",
    "build_product_readfeel_p3_first_repair_design_from_repair_priority_ledger_20260609",
    "build_product_readfeel_p3_first_repair_design_summary_from_repair_priority_ledger_20260609",
    "dump_product_readfeel_p3_first_repair_design_public_summary_20260609",
    "dump_product_readfeel_p3_first_repair_design_summary_from_repair_priority_ledger_20260609",
]
