# -*- coding: utf-8 -*-
from __future__ import annotations

"""P4-9 fixture connector for ratings-only review / P3-9 redecision.

The fixture builds synthetic ratings rows from the P4-1 body-free target case
selection.  Reviewers are assumed to have read local material outside this
packet.  The packet itself never retains raw input, rendered ``comment_text``,
candidate bodies, raw history, or free-text notes.
"""

from collections.abc import Mapping, Sequence
import json
from typing import Any

from emlis_ai_product_readfeel_p4_ratings_review import (
    PRODUCT_READFEEL_P4_RATINGS_REVIEW_PROFILE_20260610,
    PRODUCT_READFEEL_P4_RATINGS_REVIEW_STEP_20260610,
    PRODUCT_READFEEL_P4_RATINGS_REVIEW_SUMMARY_VERSION_20260610,
    PRODUCT_READFEEL_P4_RATINGS_REVIEW_VERSION_20260610,
    assert_product_readfeel_p4_ratings_review_meta_only_20260610,
    build_product_readfeel_p4_ratings_review_20260610,
    build_product_readfeel_p4_ratings_review_public_summary_20260610,
)
from emlis_ai_product_readfeel_rubric import (
    DIMENSION_EMOTION_TEMPERATURE_RETENTION,
    DIMENSION_EVIDENCE_BOUNDARY,
    DIMENSION_FOLLOW_DEPTH,
    DIMENSION_NATURALNESS,
    DIMENSION_NON_TEMPLATE,
    DIMENSION_READ_FEELING,
    DIMENSION_SELF_REPORT_RETENTION,
    DIMENSION_SOFT_INFERENCE_SURFACE,
    DIMENSION_STATE_STRUCTURE_RETENTION,
)
from fixtures.emlis_ai_product_readfeel_p4_target_cases_20260610 import (
    build_product_readfeel_p4_target_case_selection_from_p3_9_20260610,
)

SCENARIO_TARGET_SUBSET_IMPROVED_P5_HOLD = "target_subset_improved_p5_hold"
SCENARIO_REMAINING_BLOCKERS = "remaining_blockers"
SCENARIO_MISSING_READ_FEELING = "missing_read_feeling"
SCENARIO_P5_READY = "p5_ready"


def _scores_for_family(family: str, *, index: int) -> dict[str, float]:
    # Synthetic ratings are intentionally numeric-only. They represent a local
    # ratings worksheet after a human read; they are not derived from machine
    # metrics or rendered body text.
    base_by_family = {
        "daily_unpleasant": 0.84,
        "structure_question": 0.83,
        "self_denial": 0.82,
        "low_information_short": 0.85,
        "daily_positive": 0.87,
        "relationship_boundary": 0.84,
        "long_meaning_arc": 0.82,
        "uncertainty": 0.83,
    }
    base = base_by_family.get(family, 0.84)
    # Keep a tiny deterministic spread without crossing the P4-9 floor.
    spread = 0.0 if index % 3 == 0 else (0.01 if index % 3 == 1 else -0.01)
    read = max(0.80, min(0.92, base + spread))
    return {
        DIMENSION_READ_FEELING: round(read, 2),
        DIMENSION_NATURALNESS: round(min(0.93, read + 0.02), 2),
        DIMENSION_NON_TEMPLATE: round(min(0.92, read + 0.01), 2),
        DIMENSION_EMOTION_TEMPERATURE_RETENTION: round(min(0.92, read + 0.01), 2),
        DIMENSION_SELF_REPORT_RETENTION: round(read, 2),
        DIMENSION_STATE_STRUCTURE_RETENTION: round(max(0.80, read - 0.01), 2),
        DIMENSION_FOLLOW_DEPTH: round(max(0.80, read - 0.02), 2),
        DIMENSION_EVIDENCE_BOUNDARY: 0.92,
        DIMENSION_SOFT_INFERENCE_SURFACE: 0.91,
    }


def build_product_readfeel_p4_ratings_review_fixture_reviews_20260610(
    *,
    p4_target_case_selection: Mapping[str, Any] | None = None,
    scenario: str = SCENARIO_TARGET_SUBSET_IMPROVED_P5_HOLD,
) -> list[dict[str, Any]]:
    selection = p4_target_case_selection or build_product_readfeel_p4_target_case_selection_from_p3_9_20260610()
    reviews: list[dict[str, Any]] = []
    for index, case in enumerate(selection.get("selected_cases") or [], start=1):
        family = str(case.get("family") or "")
        ratings = _scores_for_family(family, index=index)
        if scenario == SCENARIO_MISSING_READ_FEELING and index == 1:
            ratings = dict(ratings)
            ratings.pop(DIMENSION_READ_FEELING, None)
        review = {
            "schema_version": "cocolon.emlis.product_readfeel.p4.fixture_rating_row.20260610.v1",
            "review_id": f"p4-9-rating-{index:03d}",
            "case_ref_id": case.get("case_ref_id"),
            "case_id": case.get("case_ref_id"),
            "fixture_id": case.get("case_ref_id"),
            "family": family,
            "product_readfeel_family": family,
            "coverage_slices": list(case.get("coverage_slices") or []),
            "selection_groups": list(case.get("selection_groups") or []),
            "ratings": ratings,
            "p3_baseline_ratings": {
                DIMENSION_READ_FEELING: 0.68,
                DIMENSION_NATURALNESS: 0.68,
                DIMENSION_NON_TEMPLATE: 0.68,
            },
            "source_blocker_ids": list(case.get("blocker_ids") or []),
            "source_target_layers": list(case.get("target_layers") or []),
            "resolved_reason_codes": list(case.get("blocker_ids") or []),
            "ratings_only_payload": True,
            "comment_text_body_included": False,
            "raw_input_included": False,
            "candidate_body_included": False,
            "machine_metrics_used_for_read_feeling": False,
            "read_feeling_auto_filled_from_machine_metrics": False,
            "product_gate_ready": False,
            "public_release_applied": False,
        }
        if scenario == SCENARIO_REMAINING_BLOCKERS:
            if index == 1:
                review["rich_input_low_information_overroute"] = True
                review["generic_reception_surface"] = True
            elif family == "structure_question" and not any(
                item.get("family") == "structure_question" and item.get("question_only_surface")
                for item in reviews
            ):
                review["question_only_surface"] = True
                review["comfort_only_surface"] = True
            elif family == "self_denial" and not any(
                item.get("family") == "self_denial" and item.get("identity_claim_as_fact")
                for item in reviews
            ):
                review["identity_claim_as_fact"] = True
        reviews.append(review)
    return reviews


def _p5_ready_overrides() -> dict[str, Any]:
    return {
        "full_current_only_recheck_complete": True,
        "current_only_readfeel_minimum_met": True,
        "main_family_readfeel_minimum_met": True,
        "history_line_eligible_slice_checked": True,
        "history_line_masks_current_input_gap": False,
        "subscription_boundary_ok": True,
        "user_label_connection_surface_safe": True,
        "creepy_or_overclaim_or_self_blame_observed": False,
        "repair_required_families": [],
        "yellow_families": [],
        "classified_reason_codes": ["p4_ratings_only_current_only_readfeel_minimum_met"],
        "p5_hold_reason_codes": [],
        "p4_family_tuning_completed": True,
    }


def build_product_readfeel_p4_ratings_review_from_target_selection_20260610(
    *,
    p4_target_case_selection: Mapping[str, Any] | None = None,
    p4_ratings_reviews: Sequence[Mapping[str, Any] | None] | None = None,
    scenario: str = SCENARIO_TARGET_SUBSET_IMPROVED_P5_HOLD,
    run_id: str | None = None,
) -> dict[str, Any]:
    selection = p4_target_case_selection or build_product_readfeel_p4_target_case_selection_from_p3_9_20260610(
        run_id=run_id or "p4_9_target_selection_fixture"
    )
    reviews = list(p4_ratings_reviews or build_product_readfeel_p4_ratings_review_fixture_reviews_20260610(
        p4_target_case_selection=selection,
        scenario=scenario,
    ))
    review = build_product_readfeel_p4_ratings_review_20260610(
        p4_target_case_selection=selection,
        p4_ratings_reviews=reviews,
        p5_recheck_overrides=_p5_ready_overrides() if scenario == SCENARIO_P5_READY else None,
        run_id=run_id or f"p4_9_ratings_review_{scenario}",
    )
    assert_product_readfeel_p4_ratings_review_meta_only_20260610(review)
    return review


def build_product_readfeel_p4_ratings_review_summary_from_target_selection_20260610(
    *,
    p4_target_case_selection: Mapping[str, Any] | None = None,
    p4_ratings_reviews: Sequence[Mapping[str, Any] | None] | None = None,
    scenario: str = SCENARIO_TARGET_SUBSET_IMPROVED_P5_HOLD,
    run_id: str | None = None,
) -> dict[str, Any]:
    review = build_product_readfeel_p4_ratings_review_from_target_selection_20260610(
        p4_target_case_selection=p4_target_case_selection,
        p4_ratings_reviews=p4_ratings_reviews,
        scenario=scenario,
        run_id=run_id,
    )
    return build_product_readfeel_p4_ratings_review_public_summary_20260610(review)


def dump_product_readfeel_p4_ratings_review_summary_from_target_selection_20260610(
    *,
    p4_target_case_selection: Mapping[str, Any] | None = None,
    p4_ratings_reviews: Sequence[Mapping[str, Any] | None] | None = None,
    scenario: str = SCENARIO_TARGET_SUBSET_IMPROVED_P5_HOLD,
    run_id: str | None = None,
) -> str:
    summary = build_product_readfeel_p4_ratings_review_summary_from_target_selection_20260610(
        p4_target_case_selection=p4_target_case_selection,
        p4_ratings_reviews=p4_ratings_reviews,
        scenario=scenario,
        run_id=run_id,
    )
    return json.dumps(summary, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


__all__ = [
    "PRODUCT_READFEEL_P4_RATINGS_REVIEW_VERSION_20260610",
    "PRODUCT_READFEEL_P4_RATINGS_REVIEW_SUMMARY_VERSION_20260610",
    "PRODUCT_READFEEL_P4_RATINGS_REVIEW_STEP_20260610",
    "PRODUCT_READFEEL_P4_RATINGS_REVIEW_PROFILE_20260610",
    "SCENARIO_TARGET_SUBSET_IMPROVED_P5_HOLD",
    "SCENARIO_REMAINING_BLOCKERS",
    "SCENARIO_MISSING_READ_FEELING",
    "SCENARIO_P5_READY",
    "assert_product_readfeel_p4_ratings_review_meta_only_20260610",
    "build_product_readfeel_p4_ratings_review_fixture_reviews_20260610",
    "build_product_readfeel_p4_ratings_review_from_target_selection_20260610",
    "build_product_readfeel_p4_ratings_review_summary_from_target_selection_20260610",
    "dump_product_readfeel_p4_ratings_review_summary_from_target_selection_20260610",
]
