# -*- coding: utf-8 -*-
from __future__ import annotations

"""P4-8 fixture connector for self_denial yellow safety-adjacent review.

The fixture reads P3 baseline cases as local test material, but the exported
review packet is body-free and contains only case refs, family ids, reason ids,
ratios, and guard flags.
"""

from collections.abc import Mapping, Sequence
import json
from typing import Any

from emlis_ai_product_readfeel_p4_self_denial_yellow_review import (
    PRODUCT_READFEEL_P4_SELF_DENIAL_YELLOW_REVIEW_ITEM_VERSION_20260610,
    PRODUCT_READFEEL_P4_SELF_DENIAL_YELLOW_REVIEW_PROFILE_20260610,
    PRODUCT_READFEEL_P4_SELF_DENIAL_YELLOW_REVIEW_STEP_20260610,
    PRODUCT_READFEEL_P4_SELF_DENIAL_YELLOW_REVIEW_VERSION_20260610,
    assert_product_readfeel_p4_self_denial_yellow_review_meta_only_20260610,
    build_product_readfeel_p4_self_denial_boundary_sample_review_20260610,
    build_product_readfeel_p4_self_denial_yellow_review_20260610,
)
from fixtures.emlis_ai_product_readfeel_baseline_cases_20260609 import (
    build_product_readfeel_baseline_cases_20260609,
)


def build_product_readfeel_p4_self_denial_yellow_review_from_baseline_20260610(
    *, cases: Sequence[Mapping[str, Any]] | None = None, run_id: str | None = None
) -> dict[str, Any]:
    review = build_product_readfeel_p4_self_denial_yellow_review_20260610(
        cases or build_product_readfeel_baseline_cases_20260609(),
        run_id=run_id or "p4_8_self_denial_yellow_review_fixture",
    )
    assert_product_readfeel_p4_self_denial_yellow_review_meta_only_20260610(review)
    return review


def build_product_readfeel_p4_self_denial_boundary_sample_review_fixture_20260610(
    *, sample_id: str, current_input: Mapping[str, Any]
) -> dict[str, Any]:
    item = build_product_readfeel_p4_self_denial_boundary_sample_review_20260610(
        sample_id=sample_id,
        current_input=current_input,
    )
    assert_product_readfeel_p4_self_denial_yellow_review_meta_only_20260610(item)
    return item


def dump_product_readfeel_p4_self_denial_yellow_review_from_baseline_20260610(
    *, cases: Sequence[Mapping[str, Any]] | None = None, run_id: str | None = None
) -> str:
    return json.dumps(
        build_product_readfeel_p4_self_denial_yellow_review_from_baseline_20260610(cases=cases, run_id=run_id),
        ensure_ascii=False,
        sort_keys=True,
        separators=(",", ":"),
    )


__all__ = [
    "PRODUCT_READFEEL_P4_SELF_DENIAL_YELLOW_REVIEW_VERSION_20260610",
    "PRODUCT_READFEEL_P4_SELF_DENIAL_YELLOW_REVIEW_ITEM_VERSION_20260610",
    "PRODUCT_READFEEL_P4_SELF_DENIAL_YELLOW_REVIEW_STEP_20260610",
    "PRODUCT_READFEEL_P4_SELF_DENIAL_YELLOW_REVIEW_PROFILE_20260610",
    "assert_product_readfeel_p4_self_denial_yellow_review_meta_only_20260610",
    "build_product_readfeel_p4_self_denial_yellow_review_from_baseline_20260610",
    "build_product_readfeel_p4_self_denial_boundary_sample_review_fixture_20260610",
    "dump_product_readfeel_p4_self_denial_yellow_review_from_baseline_20260610",
]
