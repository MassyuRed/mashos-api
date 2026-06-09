# -*- coding: utf-8 -*-
from __future__ import annotations

"""P3-6 fixture connector for Product Read Feel repair priority ledger.

This fixture intentionally keeps the local review packet and rendered bodies out
of the ledger.  It connects the P3-4 verdict split and the P3-5 ratings-only
material to P3-6 using body-free rows and safe identifiers only.
"""

from collections.abc import Mapping, Sequence
import json
from typing import Any

from emlis_ai_product_readfeel_p3_repair_priority_ledger import (
    PRODUCT_READFEEL_P3_REPAIR_PRIORITY_LEDGER_STEP_20260609,
    PRODUCT_READFEEL_P3_REPAIR_PRIORITY_LEDGER_SUMMARY_VERSION_20260609,
    PRODUCT_READFEEL_P3_REPAIR_PRIORITY_LEDGER_VERSION_20260609,
    assert_product_readfeel_p3_repair_priority_ledger_meta_only_20260609,
    build_product_readfeel_p3_repair_priority_ledger_20260609,
    build_product_readfeel_p3_repair_priority_ledger_public_summary_20260609,
    dump_product_readfeel_p3_repair_priority_ledger_public_summary_20260609,
)
from fixtures.emlis_ai_product_readfeel_p3_blind_qa_ratings_review_20260609 import (
    build_product_readfeel_p3_blind_qa_rating_fixture_reviews_20260609,
    build_product_readfeel_p3_blind_qa_ratings_review_from_verdict_split_20260609,
)
from fixtures.emlis_ai_product_readfeel_p3_verdict_split_20260609 import (
    build_product_readfeel_p3_verdict_split_from_inventory_connection_20260609,
)


def build_product_readfeel_p3_repair_priority_ledger_from_blind_qa_20260609(
    *,
    verdict_split: Mapping[str, Any] | None = None,
    blind_qa_material: Mapping[str, Any] | None = None,
    blind_qa_reviews: Sequence[Mapping[str, Any]] | None = None,
    renderer: Any = None,
    run_id: str | None = None,
) -> dict[str, Any]:
    if verdict_split is None:
        verdict_split = build_product_readfeel_p3_verdict_split_from_inventory_connection_20260609(
            renderer=renderer,
            run_id=run_id or "p3_6_verdict_split_fixture",
        )
    if blind_qa_material is None:
        reviews = list(blind_qa_reviews) if blind_qa_reviews is not None else build_product_readfeel_p3_blind_qa_rating_fixture_reviews_20260609(
            verdict_split=verdict_split
        )
        blind_qa_material = build_product_readfeel_p3_blind_qa_ratings_review_from_verdict_split_20260609(
            verdict_split=verdict_split,
            blind_qa_reviews=reviews,
            run_id=run_id or "p3_6_blind_qa_fixture",
        )
    ledger = build_product_readfeel_p3_repair_priority_ledger_20260609(
        blind_qa_material=blind_qa_material,
        verdict_split=verdict_split,
        run_id=run_id or str(blind_qa_material.get("run_id") or "p3_6_repair_priority_fixture"),
    )
    assert_product_readfeel_p3_repair_priority_ledger_meta_only_20260609(ledger)
    return ledger


def build_product_readfeel_p3_repair_priority_ledger_summary_from_blind_qa_20260609(
    *,
    verdict_split: Mapping[str, Any] | None = None,
    blind_qa_material: Mapping[str, Any] | None = None,
    blind_qa_reviews: Sequence[Mapping[str, Any]] | None = None,
    renderer: Any = None,
    run_id: str | None = None,
) -> dict[str, Any]:
    ledger = build_product_readfeel_p3_repair_priority_ledger_from_blind_qa_20260609(
        verdict_split=verdict_split,
        blind_qa_material=blind_qa_material,
        blind_qa_reviews=blind_qa_reviews,
        renderer=renderer,
        run_id=run_id,
    )
    return build_product_readfeel_p3_repair_priority_ledger_public_summary_20260609(ledger)


def dump_product_readfeel_p3_repair_priority_ledger_summary_from_blind_qa_20260609(
    *,
    verdict_split: Mapping[str, Any] | None = None,
    blind_qa_material: Mapping[str, Any] | None = None,
    blind_qa_reviews: Sequence[Mapping[str, Any]] | None = None,
    renderer: Any = None,
    run_id: str | None = None,
) -> str:
    summary = build_product_readfeel_p3_repair_priority_ledger_summary_from_blind_qa_20260609(
        verdict_split=verdict_split,
        blind_qa_material=blind_qa_material,
        blind_qa_reviews=blind_qa_reviews,
        renderer=renderer,
        run_id=run_id,
    )
    return json.dumps(summary, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


__all__ = [
    "PRODUCT_READFEEL_P3_REPAIR_PRIORITY_LEDGER_VERSION_20260609",
    "PRODUCT_READFEEL_P3_REPAIR_PRIORITY_LEDGER_SUMMARY_VERSION_20260609",
    "PRODUCT_READFEEL_P3_REPAIR_PRIORITY_LEDGER_STEP_20260609",
    "assert_product_readfeel_p3_repair_priority_ledger_meta_only_20260609",
    "build_product_readfeel_p3_repair_priority_ledger_from_blind_qa_20260609",
    "build_product_readfeel_p3_repair_priority_ledger_summary_from_blind_qa_20260609",
    "dump_product_readfeel_p3_repair_priority_ledger_public_summary_20260609",
    "dump_product_readfeel_p3_repair_priority_ledger_summary_from_blind_qa_20260609",
]
