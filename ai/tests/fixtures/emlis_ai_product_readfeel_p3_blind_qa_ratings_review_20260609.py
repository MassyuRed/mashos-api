# -*- coding: utf-8 -*-
from __future__ import annotations

"""P3-5 fixture connector for Product Read Feel Blind QA ratings-only review.

This fixture intentionally creates ratings-only QA material for contract tests.
It does not keep the local review packet or any rendered display body.  Real
Blind QA can supply the same ratings-only rows after reviewers read the local
P3-2 packet outside scorecard/inventory material.
"""

from collections.abc import Mapping, Sequence
import json
from typing import Any

from emlis_ai_product_readfeel_p3_blind_qa_ratings_review import (
    PRODUCT_READFEEL_P3_BLIND_QA_MATERIAL_VERSION_20260609,
    PRODUCT_READFEEL_P3_BLIND_QA_REVIEW_VERSION_20260609,
    PRODUCT_READFEEL_P3_BLIND_QA_STEP_20260609,
    PRODUCT_READFEEL_P3_BLIND_QA_SUMMARY_VERSION_20260609,
    assert_product_readfeel_p3_blind_qa_ratings_review_meta_only_20260609,
    build_product_readfeel_p3_blind_qa_ratings_review_20260609,
    build_product_readfeel_p3_blind_qa_ratings_public_summary_20260609,
    dump_product_readfeel_p3_blind_qa_ratings_public_summary_20260609,
)
from emlis_ai_product_readfeel_p3_verdict_split import (
    VERDICT_LAYER_NOT_EVALUATED,
    VERDICT_LAYER_P2_RED,
    VERDICT_LAYER_P3_REPAIR_REQUIRED,
    VERDICT_LAYER_P3_YELLOW,
)
from emlis_ai_product_readfeel_rubric import (
    DIMENSION_EMOTION_TEMPERATURE_RETENTION,
    DIMENSION_EVIDENCE_BOUNDARY,
    DIMENSION_FOLLOW_DEPTH,
    DIMENSION_INSIGHT_DELTA,
    DIMENSION_NATURALNESS,
    DIMENSION_NON_TEMPLATE,
    DIMENSION_READ_FEELING,
    DIMENSION_SELF_REPORT_RETENTION,
    DIMENSION_SOFT_INFERENCE_SURFACE,
    DIMENSION_STATE_STRUCTURE_RETENTION,
    DIMENSION_STRUCTURE_INSIGHT_CANDIDATE_QUALITY,
)
from fixtures.emlis_ai_product_readfeel_p3_verdict_split_20260609 import (
    build_product_readfeel_p3_verdict_split_from_inventory_connection_20260609,
)


def _score_profile_for_verdict_row_20260609(row: Mapping[str, Any]) -> dict[str, float]:
    layer = str(row.get("verdict_layer") or "")
    if layer == VERDICT_LAYER_P2_RED:
        base = 0.0
        naturalness = 0.0
        non_template = 0.0
    elif layer == VERDICT_LAYER_P3_REPAIR_REQUIRED:
        base = 0.42
        naturalness = 0.62
        non_template = 0.58
    elif layer == VERDICT_LAYER_P3_YELLOW:
        base = 0.68
        naturalness = 0.74
        non_template = 0.70
    elif layer == VERDICT_LAYER_NOT_EVALUATED:
        base = 0.0
        naturalness = 0.0
        non_template = 0.0
    else:
        base = 0.91
        naturalness = 0.92
        non_template = 0.91
    return {
        DIMENSION_READ_FEELING: base,
        DIMENSION_SELF_REPORT_RETENTION: base,
        DIMENSION_STATE_STRUCTURE_RETENTION: max(0.0, min(1.0, base - 0.02 if base else 0.0)),
        DIMENSION_EMOTION_TEMPERATURE_RETENTION: base,
        DIMENSION_FOLLOW_DEPTH: max(0.0, min(1.0, base - 0.03 if base else 0.0)),
        DIMENSION_EVIDENCE_BOUNDARY: 0.92 if base else 0.0,
        DIMENSION_SOFT_INFERENCE_SURFACE: 0.90 if base else 0.0,
        DIMENSION_NATURALNESS: naturalness,
        DIMENSION_NON_TEMPLATE: non_template,
        DIMENSION_INSIGHT_DELTA: 0.50 if base else 0.0,
        DIMENSION_STRUCTURE_INSIGHT_CANDIDATE_QUALITY: 0.50 if base else 0.0,
    }


def build_product_readfeel_p3_blind_qa_rating_fixture_reviews_20260609(
    *,
    verdict_split: Mapping[str, Any],
    reviewer_kind: str = "internal_karen_review_fixture",
) -> list[dict[str, Any]]:
    reviews: list[dict[str, Any]] = []
    for index, row in enumerate(verdict_split.get("verdict_rows") or [], start=1):
        if row.get("verdict_layer") == VERDICT_LAYER_NOT_EVALUATED:
            # NOT_EVALUATED rows stay out of read-feeling scoring; they remain visible
            # in the P3-4 ledger, not as P3 ratings.
            continue
        ratings = _score_profile_for_verdict_row_20260609(row)
        reviews.append(
            {
                "schema_version": "cocolon.emlis.product_readfeel.blind_qa_review.v1",
                "review_id": f"p3-5-rating-{index:03d}",
                "candidate_id": row.get("row_id"),
                "case_id": row.get("case_id"),
                "fixture_id": row.get("fixture_id") or row.get("case_id"),
                "product_readfeel_family": row.get("product_readfeel_family") or row.get("family"),
                "coverage_slices": list(row.get("coverage_slices") or []),
                "reviewer_kind": reviewer_kind,
                "ratings": ratings,
                "red_flags": ["p2_red_source_context"] if row.get("verdict_layer") == VERDICT_LAYER_P2_RED else [],
                "repair_reasons": list(row.get("blocker_ids") or row.get("repair_reasons") or []),
                "source_verdict": row.get("verdict"),
                "source_verdict_layer": row.get("verdict_layer"),
                "source_reason_codes": list(row.get("reason_codes") or []),
                "source_blocker_ids": list(row.get("blocker_ids") or []),
                "source_failure_buckets": list(row.get("failure_buckets") or []),
                "ratings_only_payload": True,
                "comment_text_body_included": False,
                "raw_input_included": False,
                "candidate_body_included": False,
                "machine_metrics_used_for_read_feeling": False,
                "read_feeling_auto_filled_from_machine_metrics": False,
                "product_gate_ready": False,
                "public_release_applied": False,
            }
        )
    return reviews


def build_product_readfeel_p3_blind_qa_ratings_review_from_verdict_split_20260609(
    *,
    verdict_split: Mapping[str, Any] | None = None,
    blind_qa_reviews: Sequence[Mapping[str, Any] | None] | None = None,
    renderer: Any = None,
    run_id: str | None = None,
    use_fixture_reviews: bool = False,
) -> dict[str, Any]:
    split = verdict_split or build_product_readfeel_p3_verdict_split_from_inventory_connection_20260609(
        renderer=renderer,
        run_id=run_id or "p3-5-blind-qa-verdict-split-fixture",
    )
    reviews = list(blind_qa_reviews or [])
    if use_fixture_reviews and not reviews:
        reviews = build_product_readfeel_p3_blind_qa_rating_fixture_reviews_20260609(verdict_split=split)
    material = build_product_readfeel_p3_blind_qa_ratings_review_20260609(
        verdict_split=split,
        blind_qa_reviews=reviews,
        run_id=run_id or str(split.get("run_id") or "p3-5-blind-qa-ratings-fixture"),
    )
    assert_product_readfeel_p3_blind_qa_ratings_review_meta_only_20260609(material)
    return material


def build_product_readfeel_p3_blind_qa_ratings_summary_from_verdict_split_20260609(
    *,
    verdict_split: Mapping[str, Any] | None = None,
    blind_qa_reviews: Sequence[Mapping[str, Any] | None] | None = None,
    renderer: Any = None,
    run_id: str | None = None,
    use_fixture_reviews: bool = False,
) -> dict[str, Any]:
    material = build_product_readfeel_p3_blind_qa_ratings_review_from_verdict_split_20260609(
        verdict_split=verdict_split,
        blind_qa_reviews=blind_qa_reviews,
        renderer=renderer,
        run_id=run_id,
        use_fixture_reviews=use_fixture_reviews,
    )
    return build_product_readfeel_p3_blind_qa_ratings_public_summary_20260609(material)


def dump_product_readfeel_p3_blind_qa_ratings_summary_from_verdict_split_20260609(
    *,
    verdict_split: Mapping[str, Any] | None = None,
    blind_qa_reviews: Sequence[Mapping[str, Any] | None] | None = None,
    renderer: Any = None,
    run_id: str | None = None,
    use_fixture_reviews: bool = False,
) -> str:
    summary = build_product_readfeel_p3_blind_qa_ratings_summary_from_verdict_split_20260609(
        verdict_split=verdict_split,
        blind_qa_reviews=blind_qa_reviews,
        renderer=renderer,
        run_id=run_id,
        use_fixture_reviews=use_fixture_reviews,
    )
    return json.dumps(summary, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


__all__ = [
    "PRODUCT_READFEEL_P3_BLIND_QA_REVIEW_VERSION_20260609",
    "PRODUCT_READFEEL_P3_BLIND_QA_MATERIAL_VERSION_20260609",
    "PRODUCT_READFEEL_P3_BLIND_QA_SUMMARY_VERSION_20260609",
    "PRODUCT_READFEEL_P3_BLIND_QA_STEP_20260609",
    "assert_product_readfeel_p3_blind_qa_ratings_review_meta_only_20260609",
    "build_product_readfeel_p3_blind_qa_rating_fixture_reviews_20260609",
    "build_product_readfeel_p3_blind_qa_ratings_review_from_verdict_split_20260609",
    "build_product_readfeel_p3_blind_qa_ratings_summary_from_verdict_split_20260609",
    "dump_product_readfeel_p3_blind_qa_ratings_public_summary_20260609",
    "dump_product_readfeel_p3_blind_qa_ratings_summary_from_verdict_split_20260609",
]
