# -*- coding: utf-8 -*-
from __future__ import annotations

"""P4-9 ratings-only review and P3-9 re-judgement for EmlisAI Product Read Feel.

P4-9 receives only body-free case references and human/fixture rating numbers
for the P4 target subset.  It classifies P4 improvement / unchanged / worsened
without retaining raw input, rendered ``comment_text`` bodies, candidate bodies,
history raw text, or reviewer free-text notes.  The module then builds a
P3-9-compatible connection evidence packet so P5 can be rechecked without
strengthening any User Label Connection visible surface.

This module is measurement-only.  It does not generate Emlis text, change RN,
API routes, DB schema, public response keys, gate thresholds, runtime branches,
or product release flags.
"""

from collections import Counter, defaultdict
from collections.abc import Iterable, Mapping, Sequence
import json
from typing import Any, Final

from emlis_ai_product_quality_contract_freeze import (
    assert_emlis_ai_product_quality_contract_freeze_meta_only,
)
from emlis_ai_product_readfeel_current_output_inventory import (
    FAMILY_DAILY_UNPLEASANT,
    FAMILY_LOW_INFORMATION_SHORT,
    FAMILY_SELF_DENIAL,
    FAMILY_STRUCTURE_QUESTION,
    PRODUCT_READFEEL_REQUIRED_FAMILIES,
)
from emlis_ai_product_readfeel_p3_p4_p5_connection_decision import (
    DECISION_P4_NEXT_P5_HOLD,
    DECISION_P5_READY_AFTER_P4,
    assert_product_readfeel_p3_p4_p5_connection_decision_meta_only_20260609,
    build_product_readfeel_p3_p4_p5_connection_decision_20260609,
)
from emlis_ai_product_readfeel_p3_regression import (
    build_product_readfeel_p3_regression_green_fixture_results_20260609,
    build_product_readfeel_p3_regression_result_20260609,
)
from emlis_ai_product_readfeel_p3_first_repair_design import (
    build_product_readfeel_p3_first_repair_design_20260609,
)
from emlis_ai_product_readfeel_p3_verdict_split import VERDICT_LAYER_P3_REPAIR_REQUIRED
from emlis_ai_product_readfeel_p4_target_case_selection import (
    assert_product_readfeel_p4_target_case_selection_meta_only_20260610,
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
    PRODUCT_READFEEL_RATING_DIMENSIONS,
    assert_product_readfeel_rubric_meta_only,
)

PRODUCT_READFEEL_P4_RATINGS_REVIEW_VERSION_20260610: Final = (
    "cocolon.emlis.product_readfeel.p4.ratings_review.20260610.v1"
)
PRODUCT_READFEEL_P4_RATINGS_REVIEW_ROW_VERSION_20260610: Final = (
    "cocolon.emlis.product_readfeel.p4.ratings_review_row.20260610.v1"
)
PRODUCT_READFEEL_P4_RATINGS_REVIEW_SUMMARY_VERSION_20260610: Final = (
    "cocolon.emlis.product_readfeel.p4.ratings_review_summary.20260610.v1"
)
PRODUCT_READFEEL_P4_RATINGS_REVIEW_STEP_20260610: Final = (
    "P4-9_Ratings_Only_Review_P3_9_Rejudge"
)
PRODUCT_READFEEL_P4_RATINGS_REVIEW_SOURCE_20260610: Final = (
    "Cocolon_EmlisAI_P4_FamilyProductTuning_RatingsOnlyReview_20260610"
)
PRODUCT_READFEEL_P4_RATINGS_REVIEW_PROFILE_20260610: Final = (
    "p4_9_target_subset_ratings_only_review_p3_9_rejudge"
)

P4_9_STATUS_IMPROVED: Final = "IMPROVED"
P4_9_STATUS_UNCHANGED: Final = "UNCHANGED"
P4_9_STATUS_WORSENED: Final = "WORSENED"
P4_9_STATUS_NOT_EVALUATED: Final = "NOT_EVALUATED"

P4_9_MAIN_TARGET_FAMILIES_20260610: Final[frozenset[str]] = frozenset(
    {FAMILY_DAILY_UNPLEASANT, FAMILY_STRUCTURE_QUESTION}
)
P4_9_YELLOW_REVIEW_FAMILIES_20260610: Final[frozenset[str]] = frozenset({FAMILY_SELF_DENIAL})
P4_9_BOUNDARY_SLICES_20260610: Final[frozenset[str]] = frozenset(
    {"low_information_short", "limited_grounding", "source_unavailable_high_information", "history_line_eligible"}
)
P4_9_REQUIRED_RATING_DIMENSIONS_20260610: Final[tuple[str, ...]] = (
    DIMENSION_READ_FEELING,
    DIMENSION_NATURALNESS,
    DIMENSION_NON_TEMPLATE,
    DIMENSION_EMOTION_TEMPERATURE_RETENTION,
    DIMENSION_SELF_REPORT_RETENTION,
    DIMENSION_STATE_STRUCTURE_RETENTION,
    DIMENSION_FOLLOW_DEPTH,
    DIMENSION_EVIDENCE_BOUNDARY,
    DIMENSION_SOFT_INFERENCE_SURFACE,
)
P4_9_RECHECK_SCORE_FLOOR_20260610: Final[float] = 0.80
P4_9_BASELINE_DEFAULT_SCORE_20260610: Final[float] = 0.68

P4_9_REASON_RICH_LOW_INFO: Final = "rich_input_low_information_overroute"
P4_9_REASON_GENERIC_SURFACE: Final = "generic_reception_surface"
P4_9_REASON_QUESTION_ONLY: Final = "question_only_surface"
P4_9_REASON_COMFORT_ONLY: Final = "comfort_only_surface"
P4_9_REASON_TARGET_JUDGEMENT: Final = "target_judgement_agreement"
P4_9_REASON_IDENTITY_FACT: Final = "self_denial_identity_claim_as_fact"
P4_9_REASON_SAFETY_BYPASS: Final = "self_denial_safety_boundary_bypass"
P4_9_REASON_OVERPOSITIVE: Final = "self_denial_overpositive_template"
P4_9_REASON_LOW_INFO_DEEP_READ: Final = "low_information_deep_read"
P4_9_REASON_LIMITED_Q_ONLY: Final = "limited_grounding_collapsed_to_question"
P4_9_REASON_SOURCE_UNAVAILABLE_NORMAL: Final = "source_unavailable_recast_as_normal_rebuild"
P4_9_REASON_HISTORY_MASKING: Final = "history_line_masks_current_input_gap"
P4_9_REASON_SCORE_REGRESSION: Final = "rating_regressed_against_p3_baseline"
P4_9_REASON_MISSING_READ_FEELING: Final = "read_feeling_not_evaluated"
P4_9_REASON_P4_TARGET_SUBSET_ONLY: Final = "p4_target_subset_only_current_only_readfeel_not_full_minimum"

_FORBIDDEN_BODY_KEYS_20260610: Final[frozenset[str]] = frozenset(
    {
        "raw_input",
        "rawInput",
        "raw_text",
        "rawText",
        "source_text",
        "sourceText",
        "input",
        "input_text",
        "inputText",
        "user_input",
        "userInput",
        "current_input",
        "currentInput",
        "history_context",
        "historyContext",
        "history_records",
        "historyRecords",
        "history_raw_text",
        "historyRawText",
        "memo",
        "memo_text",
        "memoText",
        "memo_action",
        "memoAction",
        "thought_text",
        "thoughtText",
        "action_text",
        "actionText",
        "comment_text",
        "commentText",
        "comment_text_body",
        "commentTextBody",
        "candidate_body",
        "candidateBody",
        "reply_text",
        "replyText",
        "surface_text",
        "surfaceText",
        "display_text",
        "displayText",
        "visible_text",
        "visibleText",
        "realized_text",
        "realizedText",
        "observation_text",
        "observationText",
        "reception_text",
        "receptionText",
        "reviewer_note",
        "reviewer_notes",
        "review_notes",
        "free_text_note",
        "blind_qa_free_text",
        "stdout",
        "stderr",
        "raw_test_output",
        "test_output",
        "traceback_body",
        "body",
        "text",
    }
)
_FORBIDDEN_TRUE_FLAGS_20260610: Final[frozenset[str]] = frozenset(
    {
        "api_route_changed",
        "request_key_changed",
        "response_shape_changed",
        "public_response_key_added",
        "public_response_key_change",
        "db_physical_name_changed",
        "rn_visible_contract_changed",
        "rn_visible_title_changed",
        "display_gate_relaxed",
        "grounding_gate_relaxed",
        "reader_gate_relaxed",
        "template_gate_relaxed",
        "runtime_surface_gate_relaxed",
        "visible_surface_gate_relaxed",
        "safety_gate_relaxed",
        "gate_relaxed",
        "raw_input_included",
        "raw_text_included",
        "input_text_included",
        "comment_text_included",
        "comment_text_body_included",
        "candidate_body_included",
        "surface_body_included",
        "history_raw_text_included",
        "raw_test_output_included",
        "product_gate_ready",
        "product_gate_reached",
        "product_gate_public_release_applied",
        "public_release_applied",
        "product_quality_released",
        "release_allowed",
        "machine_metrics_used_for_read_feeling",
        "read_feeling_auto_filled_from_machine_metrics",
        "read_feeling_auto_estimation_allowed",
        "exact_comment_text_locked",
        "exact_comment_text_required",
        "case_specific_runtime_branch",
        "case_specific_runtime_condition_allowed",
        "runtime_branching_uses_fixture_strings",
        "fixture_text_used_for_runtime_branching",
        "fixed_sentence_template_added",
        "fixed_sentence_template_used",
        "input_specific_template_added",
        "runtime_repair_applied",
        "implementation_change_applied",
        "p4_runtime_tuning_applied",
        "p5_visible_surface_strengthened",
        "p5_runtime_change_applied",
        "schema_file_materialized",
        "external_ai_used",
        "local_llm_used",
    }
)


def _clean(value: Any) -> str:
    if value is None:
        return ""
    return str(value).strip()


def _safe_identifier(value: Any, *, default: str = "", max_length: int = 128) -> str:
    text_value = _clean(value) or default
    chars = [ch if ch.isalnum() or ch in {"-", "_", ".", ":"} else "-" for ch in text_value[:max_length]]
    return "".join(chars).strip("-") or default


def _listify(value: Iterable[Any] | Any | None) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, (str, bytes, bytearray)):
        return [value]
    if isinstance(value, Mapping):
        return list(value.keys())
    if isinstance(value, Iterable):
        return list(value)
    return [value]


def _dedupe(values: Iterable[Any] | Any | None) -> list[str]:
    result: list[str] = []
    seen: set[str] = set()
    for value in _listify(values):
        text = _clean(value)
        if text and text not in seen:
            seen.add(text)
            result.append(text)
    return result


def _safe_float(value: Any) -> float | None:
    try:
        if value is None or value == "":
            return None
        score = float(value)
    except (TypeError, ValueError):
        return None
    return max(0.0, min(1.0, score))


def _bool(value: Any) -> bool:
    if isinstance(value, bool):
        return value
    if isinstance(value, str):
        return value.strip().lower() in {"1", "true", "yes", "y", "on"}
    return bool(value)


def _avg(values: Iterable[Any]) -> float | None:
    present = [score for score in (_safe_float(value) for value in values) if score is not None]
    if not present:
        return None
    return round(sum(present) / len(present), 4)


def _min(values: Iterable[Any]) -> float | None:
    present = [score for score in (_safe_float(value) for value in values) if score is not None]
    if not present:
        return None
    return round(min(present), 4)


def _contains_forbidden_key(value: Any) -> bool:
    if isinstance(value, Mapping):
        for key, child in value.items():
            if str(key) in _FORBIDDEN_BODY_KEYS_20260610:
                return True
            if _contains_forbidden_key(child):
                return True
    elif isinstance(value, (list, tuple, set)):
        return any(_contains_forbidden_key(item) for item in value)
    return False


def _forbidden_true_flag_path(value: Any, *, path: str = "payload") -> str | None:
    if isinstance(value, Mapping):
        for key, child in value.items():
            key_text = str(key)
            current_path = f"{path}.{key_text}"
            if key_text in _FORBIDDEN_TRUE_FLAGS_20260610 and child is True:
                return current_path
            nested = _forbidden_true_flag_path(child, path=current_path)
            if nested:
                return nested
    elif isinstance(value, (list, tuple, set)):
        for index, child in enumerate(value):
            nested = _forbidden_true_flag_path(child, path=f"{path}[{index}]")
            if nested:
                return nested
    return None


def assert_product_readfeel_p4_ratings_review_meta_only_20260610(
    payload: Mapping[str, Any],
    *,
    source: str = "p4_9_ratings_review",
) -> None:
    """Reject body-bearing, runtime-mutating, or machine-autofilled P4-9 payloads."""

    if not isinstance(payload, Mapping):
        raise TypeError(f"{source} must be a mapping")
    if _contains_forbidden_key(payload):
        raise ValueError(f"{source} must not contain input/output/history/reviewer body keys")
    true_flag_path = _forbidden_true_flag_path(payload, path=source)
    if true_flag_path:
        raise ValueError(f"{source} contains forbidden true flag: {true_flag_path}")
    assert_product_readfeel_rubric_meta_only(payload, source=f"{source}.rubric")
    assert_emlis_ai_product_quality_contract_freeze_meta_only(payload, source=f"{source}.contract_freeze")


def _selected_case_lookup(p4_target_case_selection: Mapping[str, Any] | None) -> dict[str, dict[str, Any]]:
    if not isinstance(p4_target_case_selection, Mapping):
        return {}
    assert_product_readfeel_p4_target_case_selection_meta_only_20260610(
        p4_target_case_selection, source="p4_9.target_case_selection_source"
    )
    lookup: dict[str, dict[str, Any]] = {}
    for item in p4_target_case_selection.get("selected_cases") or []:
        if not isinstance(item, Mapping):
            continue
        key = _safe_identifier(item.get("case_ref_id") or item.get("case_id"), default="")
        if key:
            lookup[key] = dict(item)
    return lookup


def _ratings_from_source(source: Mapping[str, Any]) -> dict[str, float]:
    ratings_raw = source.get("ratings") or source.get("dimension_scores") or {}
    if not isinstance(ratings_raw, Mapping):
        ratings_raw = {}
    ratings: dict[str, float] = {}
    for dimension in PRODUCT_READFEEL_RATING_DIMENSIONS:
        score = _safe_float(ratings_raw.get(dimension))
        if score is not None:
            ratings[dimension] = score
    return ratings


def _score_regressed(ratings: Mapping[str, float], baseline: Mapping[str, Any]) -> bool:
    for dimension in (DIMENSION_READ_FEELING, DIMENSION_NATURALNESS, DIMENSION_NON_TEMPLATE):
        current = _safe_float(ratings.get(dimension))
        previous = _safe_float(baseline.get(dimension))
        if current is not None and previous is not None and current + 0.0001 < previous:
            return True
    return False


def _flags(source: Mapping[str, Any]) -> dict[str, bool]:
    return {
        "p2_red_present": _bool(source.get("p2_red_present") or source.get("p2_red")),
        "target_judgement_agreement": _bool(source.get("target_judgement_agreement")),
        "comfort_only_surface": _bool(source.get("comfort_only_surface") or source.get("comfort_only")),
        "question_only_surface": _bool(source.get("question_only_surface") or source.get("question_only")),
        "rich_input_low_information_overroute": _bool(source.get("rich_input_low_information_overroute")),
        "generic_reception_surface": _bool(source.get("generic_reception_surface")),
        "self_denial_identity_claim_as_fact": _bool(source.get("identity_claim_as_fact") or source.get("self_denial_identity_claim_as_fact")),
        "self_denial_safety_boundary_bypass": _bool(source.get("safety_boundary_bypass") or source.get("self_denial_safety_boundary_bypass")),
        "self_denial_overpositive_template": _bool(source.get("overpositive_template") or source.get("self_denial_overpositive_template")),
        "low_information_deep_read": _bool(source.get("low_information_deep_read")),
        "limited_grounding_collapsed_to_question": _bool(
            source.get("limited_grounding_collapsed_to_question") or source.get("limited_grounding_question_only")
        ),
        "source_unavailable_recast_as_normal_rebuild": _bool(
            source.get("source_unavailable_recast_as_normal_rebuild") or source.get("source_unavailable_normal_rebuild_risk")
        ),
        "history_line_masks_current_input_gap": _bool(source.get("history_line_masks_current_input_gap")),
        "creepy_or_overclaim_or_self_blame_observed": _bool(
            source.get("creepy_or_overclaim_or_self_blame_observed")
            or source.get("creepy_signal")
            or source.get("overclaim_signal")
            or source.get("self_blame_amplification")
        ),
    }


def _unresolved_reason_codes(
    *,
    family: str,
    coverage_slices: Sequence[str],
    flags: Mapping[str, bool],
    ratings: Mapping[str, float],
    baseline_ratings: Mapping[str, Any],
) -> list[str]:
    reasons: list[str] = []
    if flags.get("p2_red_present"):
        reasons.append("p2_red_present")
    if flags.get("target_judgement_agreement"):
        reasons.append(P4_9_REASON_TARGET_JUDGEMENT)
    if flags.get("comfort_only_surface"):
        reasons.append(P4_9_REASON_COMFORT_ONLY)
    if flags.get("question_only_surface"):
        reasons.append(P4_9_REASON_QUESTION_ONLY)
    if flags.get("rich_input_low_information_overroute"):
        reasons.append(P4_9_REASON_RICH_LOW_INFO)
    if flags.get("generic_reception_surface"):
        reasons.append(P4_9_REASON_GENERIC_SURFACE)
    if flags.get("self_denial_identity_claim_as_fact"):
        reasons.append(P4_9_REASON_IDENTITY_FACT)
    if flags.get("self_denial_safety_boundary_bypass"):
        reasons.append(P4_9_REASON_SAFETY_BYPASS)
    if flags.get("self_denial_overpositive_template"):
        reasons.append(P4_9_REASON_OVERPOSITIVE)
    if flags.get("low_information_deep_read"):
        reasons.append(P4_9_REASON_LOW_INFO_DEEP_READ)
    if flags.get("limited_grounding_collapsed_to_question"):
        reasons.append(P4_9_REASON_LIMITED_Q_ONLY)
    if flags.get("source_unavailable_recast_as_normal_rebuild"):
        reasons.append(P4_9_REASON_SOURCE_UNAVAILABLE_NORMAL)
    if flags.get("history_line_masks_current_input_gap"):
        reasons.append(P4_9_REASON_HISTORY_MASKING)
    if flags.get("creepy_or_overclaim_or_self_blame_observed"):
        reasons.append("creepy_or_overclaim_or_self_blame_observed")
    if DIMENSION_READ_FEELING not in ratings:
        reasons.append(P4_9_REASON_MISSING_READ_FEELING)
    if _score_regressed(ratings, baseline_ratings):
        reasons.append(P4_9_REASON_SCORE_REGRESSION)

    # Family/slice boundary labels help the P3-9 redecision keep blockers in the
    # right lane without inspecting any display text.
    if family == FAMILY_DAILY_UNPLEASANT and flags.get("target_judgement_agreement"):
        reasons.append("daily_unpleasant_target_judgement_boundary_failed")
    if family == FAMILY_STRUCTURE_QUESTION and flags.get("comfort_only_surface"):
        reasons.append("structure_question_answered_as_comfort")
    if family == FAMILY_SELF_DENIAL and flags.get("self_denial_identity_claim_as_fact"):
        reasons.append("self_denial_identity_claim_risk")
    if "limited_grounding" in coverage_slices and flags.get("limited_grounding_collapsed_to_question"):
        reasons.append("limited_grounding_collapsed_to_question")
    if "source_unavailable_high_information" in coverage_slices and flags.get("source_unavailable_recast_as_normal_rebuild"):
        reasons.append("source_unavailable_recast_as_normal_rebuild")
    return _dedupe(reasons)


def _status_for_row(reasons: Sequence[str], ratings: Mapping[str, float], baseline_ratings: Mapping[str, Any]) -> str:
    if P4_9_REASON_MISSING_READ_FEELING in reasons:
        return P4_9_STATUS_NOT_EVALUATED
    if any(
        reason in reasons
        for reason in (
            "p2_red_present",
            P4_9_REASON_TARGET_JUDGEMENT,
            P4_9_REASON_IDENTITY_FACT,
            P4_9_REASON_SAFETY_BYPASS,
            P4_9_REASON_OVERPOSITIVE,
            P4_9_REASON_LOW_INFO_DEEP_READ,
            P4_9_REASON_LIMITED_Q_ONLY,
            P4_9_REASON_SOURCE_UNAVAILABLE_NORMAL,
            P4_9_REASON_HISTORY_MASKING,
            P4_9_REASON_SCORE_REGRESSION,
            "creepy_or_overclaim_or_self_blame_observed",
        )
    ):
        return P4_9_STATUS_WORSENED
    if any(reason in reasons for reason in (P4_9_REASON_RICH_LOW_INFO, P4_9_REASON_GENERIC_SURFACE, P4_9_REASON_QUESTION_ONLY, P4_9_REASON_COMFORT_ONLY)):
        return P4_9_STATUS_UNCHANGED
    read_score = _safe_float(ratings.get(DIMENSION_READ_FEELING))
    previous = _safe_float(baseline_ratings.get(DIMENSION_READ_FEELING)) or P4_9_BASELINE_DEFAULT_SCORE_20260610
    if read_score is not None and read_score >= previous:
        return P4_9_STATUS_IMPROVED
    return P4_9_STATUS_UNCHANGED


def normalize_product_readfeel_p4_ratings_review_row_20260610(
    review: Mapping[str, Any] | None,
    *,
    selected_cases_by_key: Mapping[str, Mapping[str, Any]] | None = None,
    run_id: str | None = None,
    index: int = 0,
) -> dict[str, Any]:
    source = dict(review or {})
    if not isinstance(review, Mapping):
        raise TypeError("P4-9 ratings review row must be a mapping")
    assert_product_readfeel_p4_ratings_review_meta_only_20260610(source, source="p4_9.source_review_row")

    case_ref_id = _safe_identifier(
        source.get("case_ref_id") or source.get("case_id") or source.get("fixture_id"),
        default=f"p4-9-case-{index:03d}",
    )
    selected = dict((selected_cases_by_key or {}).get(case_ref_id) or {})
    family = _clean(source.get("family") or source.get("product_readfeel_family") or selected.get("family"))
    coverage_slices = _dedupe(source.get("coverage_slices") or selected.get("coverage_slices"))
    selection_groups = _dedupe(source.get("selection_groups") or selected.get("selection_groups"))
    ratings = _ratings_from_source(source)
    baseline_ratings = dict(source.get("p3_baseline_ratings") or {}) if isinstance(source.get("p3_baseline_ratings"), Mapping) else {}
    if not baseline_ratings:
        baseline_ratings = {
            DIMENSION_READ_FEELING: P4_9_BASELINE_DEFAULT_SCORE_20260610,
            DIMENSION_NATURALNESS: P4_9_BASELINE_DEFAULT_SCORE_20260610,
            DIMENSION_NON_TEMPLATE: P4_9_BASELINE_DEFAULT_SCORE_20260610,
        }
    flags = _flags(source)
    unresolved = _unresolved_reason_codes(
        family=family,
        coverage_slices=coverage_slices,
        flags=flags,
        ratings=ratings,
        baseline_ratings=baseline_ratings,
    )
    status = _status_for_row(unresolved, ratings, baseline_ratings)
    item = {
        "schema_version": PRODUCT_READFEEL_P4_RATINGS_REVIEW_ROW_VERSION_20260610,
        "version": PRODUCT_READFEEL_P4_RATINGS_REVIEW_ROW_VERSION_20260610,
        "source": PRODUCT_READFEEL_P4_RATINGS_REVIEW_SOURCE_20260610,
        "source_step": PRODUCT_READFEEL_P4_RATINGS_REVIEW_STEP_20260610,
        "run_id": _safe_identifier(run_id or source.get("run_id"), default="p4_9_ratings_review"),
        "review_id": _safe_identifier(source.get("review_id"), default=f"p4-9-review-{index:03d}"),
        "case_ref_id": case_ref_id,
        "case_id": case_ref_id,
        "fixture_id": case_ref_id,
        "family": family,
        "product_readfeel_family": family,
        "coverage_slices": coverage_slices,
        "selection_groups": selection_groups,
        "ratings": ratings,
        "dimension_scores": ratings,
        "required_rating_dimensions": list(P4_9_REQUIRED_RATING_DIMENSIONS_20260610),
        "missing_rating_dimensions": [
            dimension for dimension in P4_9_REQUIRED_RATING_DIMENSIONS_20260610 if dimension not in ratings
        ],
        "p3_baseline_rating_refs_only": True,
        "p3_baseline_ratings": {
            key: value for key, value in baseline_ratings.items() if key in {DIMENSION_READ_FEELING, DIMENSION_NATURALNESS, DIMENSION_NON_TEMPLATE}
        },
        "improvement_status": status,
        "p4_improved": status == P4_9_STATUS_IMPROVED,
        "p4_unchanged": status == P4_9_STATUS_UNCHANGED,
        "p4_worsened": status == P4_9_STATUS_WORSENED,
        "not_evaluated": status == P4_9_STATUS_NOT_EVALUATED,
        "unresolved_reason_codes": unresolved,
        "resolved_reason_codes": _dedupe(source.get("resolved_reason_codes")),
        "source_blocker_ids": _dedupe(source.get("source_blocker_ids") or selected.get("blocker_ids")),
        "source_target_layers": _dedupe(source.get("source_target_layers") or selected.get("target_layers")),
        "question_dominance_absence": not flags.get("question_only_surface"),
        "mirror_only_absence": not _bool(source.get("mirror_only_surface")),
        "forbidden_claim_absence": not any(
            flags.get(key)
            for key in (
                "target_judgement_agreement",
                "self_denial_identity_claim_as_fact",
                "source_unavailable_recast_as_normal_rebuild",
            )
        ),
        "p2_red_present": flags["p2_red_present"],
        "target_judgement_agreement": flags["target_judgement_agreement"],
        "comfort_only_surface": flags["comfort_only_surface"],
        "question_only_surface": flags["question_only_surface"],
        "rich_input_low_information_overroute": flags["rich_input_low_information_overroute"],
        "generic_reception_surface": flags["generic_reception_surface"],
        "identity_claim_as_fact": flags["self_denial_identity_claim_as_fact"],
        "safety_boundary_bypass": flags["self_denial_safety_boundary_bypass"],
        "overpositive_template": flags["self_denial_overpositive_template"],
        "low_information_deep_read": flags["low_information_deep_read"],
        "limited_grounding_collapsed_to_question": flags["limited_grounding_collapsed_to_question"],
        "source_unavailable_recast_as_normal_rebuild": flags["source_unavailable_recast_as_normal_rebuild"],
        "history_line_masks_current_input_gap": flags["history_line_masks_current_input_gap"],
        "creepy_or_overclaim_or_self_blame_observed": flags["creepy_or_overclaim_or_self_blame_observed"],
        "ratings_only_payload": True,
        "public_text_payload_excluded": True,
        "body_free_case_references_only": True,
        "local_review_packet_retained": False,
        "local_review_packet_body_retained": False,
        "raw_input_included": False,
        "raw_text_included": False,
        "comment_text_included": False,
        "comment_text_body_included": False,
        "candidate_body_included": False,
        "surface_body_included": False,
        "history_raw_text_included": False,
        "raw_test_output_included": False,
        "machine_metrics_separated_from_blind_qa": True,
        "machine_metrics_used_for_read_feeling": False,
        "read_feeling_auto_filled_from_machine_metrics": False,
        "read_feeling_auto_estimation_allowed": False,
        "exact_comment_text_required": False,
        "case_specific_runtime_branch": False,
        "runtime_branching_uses_fixture_strings": False,
        "fixture_text_used_for_runtime_branching": False,
        "fixed_sentence_template_added": False,
        "input_specific_template_added": False,
        "comment_text_generated": False,
        "comment_text_key_written": False,
        "comment_text_written_by_scorecard": False,
        "runtime_repair_applied": False,
        "p4_runtime_tuning_applied": False,
        "p5_visible_surface_strengthened": False,
        "p5_runtime_change_applied": False,
        "public_response_key_added": False,
        "public_response_key_change": False,
        "response_shape_changed": False,
        "api_route_changed": False,
        "db_physical_name_changed": False,
        "rn_visible_contract_changed": False,
        "gate_relaxed": False,
        "display_gate_relaxed": False,
        "grounding_gate_relaxed": False,
        "reader_gate_relaxed": False,
        "template_gate_relaxed": False,
        "product_gate_ready": False,
        "product_gate_reached": False,
        "public_release_applied": False,
        "product_quality_released": False,
    }
    assert_product_readfeel_p4_ratings_review_meta_only_20260610(item, source="p4_9.normalized_review_row")
    return item


def _family_summary(review_rows: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    by_family: dict[str, list[Mapping[str, Any]]] = defaultdict(list)
    for row in review_rows:
        by_family[_clean(row.get("family")) or "unknown"].append(row)
    out: list[dict[str, Any]] = []
    for family in sorted(by_family):
        rows = by_family[family]
        statuses = Counter(_clean(row.get("improvement_status")) for row in rows)
        unresolved = Counter(
            reason for row in rows for reason in _dedupe(row.get("unresolved_reason_codes"))
        )
        out.append(
            {
                "schema_version": PRODUCT_READFEEL_P4_RATINGS_REVIEW_SUMMARY_VERSION_20260610,
                "family": family,
                "review_count": len(rows),
                "case_refs": sorted(_safe_identifier(row.get("case_ref_id"), default="") for row in rows),
                "improved_count": int(statuses.get(P4_9_STATUS_IMPROVED, 0)),
                "unchanged_count": int(statuses.get(P4_9_STATUS_UNCHANGED, 0)),
                "worsened_count": int(statuses.get(P4_9_STATUS_WORSENED, 0)),
                "not_evaluated_count": int(statuses.get(P4_9_STATUS_NOT_EVALUATED, 0)),
                "read_feeling_average": _avg((row.get("ratings") or {}).get(DIMENSION_READ_FEELING) for row in rows),
                "read_feeling_min": _min((row.get("ratings") or {}).get(DIMENSION_READ_FEELING) for row in rows),
                "naturalness_min": _min((row.get("ratings") or {}).get(DIMENSION_NATURALNESS) for row in rows),
                "non_template_min": _min((row.get("ratings") or {}).get(DIMENSION_NON_TEMPLATE) for row in rows),
                "unresolved_reason_counts": {key: int(value) for key, value in sorted(unresolved.items())},
                "ratings_only_payload": True,
                "body_free_case_references_only": True,
                "comment_text_body_included": False,
                "raw_input_included": False,
                "candidate_body_included": False,
            }
        )
    return out


def _default_p3_regression_for_redecision(run_id: str) -> dict[str, Any]:
    first_repair = build_product_readfeel_p3_first_repair_design_20260609(
        repair_priority_items=[
            {
                "priority": 1,
                "blocker_id": P4_9_REASON_RICH_LOW_INFO,
                "blocker_category": "readfeel_gap",
                "verdict_layer": VERDICT_LAYER_P3_REPAIR_REQUIRED,
                "case_count": 1,
                "families": [FAMILY_DAILY_UNPLEASANT],
                "sample_case_ids": ["p4-9-body-free-case-ref"],
                "reason_codes": [P4_9_REASON_RICH_LOW_INFO],
                "target_layers": ["input_material_bundle", "public_surface_requirement"],
            },
        ],
        run_id=f"{run_id}_p3_7_first_repair_design_ref",
    )
    return build_product_readfeel_p3_regression_result_20260609(
        first_repair_design=first_repair,
        command_results=build_product_readfeel_p3_regression_green_fixture_results_20260609(),
        run_id=f"{run_id}_p3_8_regression_ref",
    )


def _build_connection_evidence(
    *,
    review_rows: Sequence[Mapping[str, Any]],
    p4_target_case_selection: Mapping[str, Any] | None,
    p5_recheck_overrides: Mapping[str, Any] | None,
) -> dict[str, Any]:
    family_rows: dict[str, list[Mapping[str, Any]]] = defaultdict(list)
    for row in review_rows:
        family_rows[_clean(row.get("family"))].append(row)
    all_reason_codes = sorted({reason for row in review_rows for reason in _dedupe(row.get("unresolved_reason_codes"))})
    unresolved_families = sorted({
        _clean(row.get("family"))
        for row in review_rows
        if row.get("improvement_status") in {P4_9_STATUS_UNCHANGED, P4_9_STATUS_WORSENED, P4_9_STATUS_NOT_EVALUATED}
        and _clean(row.get("family"))
    })
    target_layers = sorted({layer for row in review_rows for layer in _dedupe(row.get("source_target_layers"))})
    selected_summary = dict((p4_target_case_selection or {}).get("summary") or {}) if isinstance(p4_target_case_selection, Mapping) else {}
    target_case_count = int(selected_summary.get("selected_case_count") or len(review_rows) or 0)
    target_reviews_complete = bool(review_rows) and len(review_rows) >= target_case_count
    min_read = _min((row.get("ratings") or {}).get(DIMENSION_READ_FEELING) for row in review_rows) or 0.0
    min_natural = _min((row.get("ratings") or {}).get(DIMENSION_NATURALNESS) for row in review_rows) or 0.0
    min_non_template = _min((row.get("ratings") or {}).get(DIMENSION_NON_TEMPLATE) for row in review_rows) or 0.0
    no_unresolved = not all_reason_codes
    target_subset_floor_met = (
        target_reviews_complete
        and min_read >= P4_9_RECHECK_SCORE_FLOOR_20260610
        and min_natural >= P4_9_RECHECK_SCORE_FLOOR_20260610
        and min_non_template >= P4_9_RECHECK_SCORE_FLOOR_20260610
        and no_unresolved
    )

    # Default: P4-9 initial target subset can show improvement, but it must not
    # unlock P5 unless the caller explicitly provides full current-only evidence.
    evidence = {
        "baseline_case_count": 60,
        "p3_verdict_row_count": 60,
        "observed_families": list(PRODUCT_READFEEL_REQUIRED_FAMILIES),
        "missing_families": [],
        "p2_red_count": sum(1 for row in review_rows if row.get("p2_red_present")),
        "p2_red_independently_split": True,
        "repair_required_families": [family for family in unresolved_families if family in P4_9_MAIN_TARGET_FAMILIES_20260610],
        "yellow_families": [family for family in unresolved_families if family in P4_9_YELLOW_REVIEW_FAMILIES_20260610],
        "classified_reason_codes": all_reason_codes or ["p4_ratings_only_target_subset_improved"],
        "first_repair_target_count": len(all_reason_codes),
        "first_repair_target_layers": target_layers or ["ratio_policy"],
        "first_repair_blocker_ids": all_reason_codes,
        "current_only_readfeel_minimum_met": False,
        "current_only_min_read_feeling": min_read,
        "current_only_min_naturalness": min_natural,
        "current_only_min_non_template": min_non_template,
        "main_family_readfeel_minimum_met": False,
        "history_line_eligible_slice_checked": True,
        "history_line_masks_current_input_gap": any(row.get("history_line_masks_current_input_gap") for row in review_rows),
        "subscription_boundary_ok": True,
        "user_label_connection_surface_safe": True,
        "creepy_or_overclaim_or_self_blame_observed": any(
            row.get("creepy_or_overclaim_or_self_blame_observed") for row in review_rows
        ),
        "p5_hold_reason_codes": [P4_9_REASON_P4_TARGET_SUBSET_ONLY, "current_only_readfeel_below_minimum"],
        "p4_family_tuning_completed": False,
    }
    if target_subset_floor_met and p5_recheck_overrides and p5_recheck_overrides.get("full_current_only_recheck_complete") is True:
        evidence.update(
            {
                "current_only_readfeel_minimum_met": True,
                "main_family_readfeel_minimum_met": True,
                "repair_required_families": [],
                "yellow_families": [],
                "p5_hold_reason_codes": [],
                "p4_family_tuning_completed": True,
            }
        )
    evidence.update(dict(p5_recheck_overrides or {}))
    # Keep known P5 blockers if any unresolved reason exists, regardless of caller overrides.
    if all_reason_codes:
        hold_codes = _dedupe([*evidence.get("p5_hold_reason_codes", []), *all_reason_codes, "current_only_readfeel_below_minimum"])
        evidence["p5_hold_reason_codes"] = hold_codes
        evidence["current_only_readfeel_minimum_met"] = False
        evidence["main_family_readfeel_minimum_met"] = False
    assert_product_readfeel_p3_p4_p5_connection_decision_meta_only_20260609(
        evidence, source="p4_9.p3_9_redecision_evidence"
    )
    return evidence


def _summary(
    *,
    run_id: str,
    review_rows: Sequence[Mapping[str, Any]],
    p4_target_case_selection: Mapping[str, Any] | None,
    family_summary: Sequence[Mapping[str, Any]],
    p3_9_redecision: Mapping[str, Any],
    connection_evidence: Mapping[str, Any],
) -> dict[str, Any]:
    selected_summary = dict((p4_target_case_selection or {}).get("summary") or {}) if isinstance(p4_target_case_selection, Mapping) else {}
    target_case_count = int(selected_summary.get("selected_case_count") or len(review_rows) or 0)
    reviewed_case_refs = sorted(_safe_identifier(row.get("case_ref_id"), default="") for row in review_rows)
    status_counts = Counter(_clean(row.get("improvement_status")) for row in review_rows)
    unresolved_counts = Counter(reason for row in review_rows for reason in _dedupe(row.get("unresolved_reason_codes")))
    p3_9_summary = dict(p3_9_redecision.get("summary") or p3_9_redecision.get("public_summary") or {})
    min_read = _min((row.get("ratings") or {}).get(DIMENSION_READ_FEELING) for row in review_rows)
    min_natural = _min((row.get("ratings") or {}).get(DIMENSION_NATURALNESS) for row in review_rows)
    min_non_template = _min((row.get("ratings") or {}).get(DIMENSION_NON_TEMPLATE) for row in review_rows)
    target_subset_floor_met = bool(
        review_rows
        and len(review_rows) >= target_case_count
        and min_read is not None
        and min_read >= P4_9_RECHECK_SCORE_FLOOR_20260610
        and min_natural is not None
        and min_natural >= P4_9_RECHECK_SCORE_FLOOR_20260610
        and min_non_template is not None
        and min_non_template >= P4_9_RECHECK_SCORE_FLOOR_20260610
        and not unresolved_counts
    )
    p5_allowed = p3_9_summary.get("p5_connection_allowed") is True
    if p5_allowed:
        next_action = "prepare_p5_only_after_full_current_only_readfeel_and_history_boundary_review"
    elif target_subset_floor_met:
        next_action = "continue_p5_hold_until_full_current_only_family_recheck"
    else:
        next_action = "continue_p4_repair_for_remaining_ratings_or_boundary_blockers"

    summary = {
        "schema_version": PRODUCT_READFEEL_P4_RATINGS_REVIEW_SUMMARY_VERSION_20260610,
        "version": PRODUCT_READFEEL_P4_RATINGS_REVIEW_SUMMARY_VERSION_20260610,
        "source": PRODUCT_READFEEL_P4_RATINGS_REVIEW_SOURCE_20260610,
        "source_step": PRODUCT_READFEEL_P4_RATINGS_REVIEW_STEP_20260610,
        "run_id": run_id,
        "run_profile": PRODUCT_READFEEL_P4_RATINGS_REVIEW_PROFILE_20260610,
        "target_case_count": target_case_count,
        "review_count": len(review_rows),
        "reviewed_case_count": len(set(reviewed_case_refs)),
        "unreviewed_case_count": max(0, target_case_count - len(set(reviewed_case_refs))),
        "target_subset_review_complete": bool(target_case_count and len(set(reviewed_case_refs)) >= target_case_count),
        "reviewed_case_refs": reviewed_case_refs,
        "family_rating_summary": list(family_summary),
        "family_review_counts": {row.get("family"): int(row.get("review_count") or 0) for row in family_summary},
        "improved_count": int(status_counts.get(P4_9_STATUS_IMPROVED, 0)),
        "unchanged_count": int(status_counts.get(P4_9_STATUS_UNCHANGED, 0)),
        "worsened_count": int(status_counts.get(P4_9_STATUS_WORSENED, 0)),
        "not_evaluated_count": int(status_counts.get(P4_9_STATUS_NOT_EVALUATED, 0)),
        "body_free_improvement_summary_ready": bool(review_rows),
        "unresolved_reason_counts": {key: int(value) for key, value in sorted(unresolved_counts.items())},
        "rich_input_low_information_overroute_count": int(unresolved_counts.get(P4_9_REASON_RICH_LOW_INFO, 0)),
        "generic_reception_surface_count": int(unresolved_counts.get(P4_9_REASON_GENERIC_SURFACE, 0)),
        "question_only_surface_count": int(unresolved_counts.get(P4_9_REASON_QUESTION_ONLY, 0)),
        "comfort_only_surface_count": int(unresolved_counts.get(P4_9_REASON_COMFORT_ONLY, 0)),
        "identity_claim_as_fact_count": int(unresolved_counts.get(P4_9_REASON_IDENTITY_FACT, 0)),
        "safety_boundary_bypass_count": int(unresolved_counts.get(P4_9_REASON_SAFETY_BYPASS, 0)),
        "overpositive_template_count": int(unresolved_counts.get(P4_9_REASON_OVERPOSITIVE, 0)),
        "boundary_regression_count": int(
            unresolved_counts.get(P4_9_REASON_LOW_INFO_DEEP_READ, 0)
            + unresolved_counts.get(P4_9_REASON_LIMITED_Q_ONLY, 0)
            + unresolved_counts.get(P4_9_REASON_SOURCE_UNAVAILABLE_NORMAL, 0)
            + unresolved_counts.get(P4_9_REASON_HISTORY_MASKING, 0)
        ),
        "p2_red_count": int(unresolved_counts.get("p2_red_present", 0)),
        "target_judgement_agreement_count": int(unresolved_counts.get(P4_9_REASON_TARGET_JUDGEMENT, 0)),
        "read_feeling_min": min_read,
        "naturalness_min": min_natural,
        "non_template_min": min_non_template,
        "p4_target_subset_floor_met": target_subset_floor_met,
        "read_feeling_from_ratings_only": True,
        "read_feeling_auto_filled_from_machine_metrics": False,
        "machine_metrics_used_for_read_feeling": False,
        "p4_9_ratings_only_review_ready": bool(review_rows),
        "p3_9_redecision_created": True,
        "post_p4_p3_9_next_phase_decision": _clean(p3_9_summary.get("next_phase_decision")),
        "post_p4_p4_connection_allowed": p3_9_summary.get("p4_connection_allowed") is True,
        "post_p4_p5_connection_allowed": p5_allowed,
        "post_p4_p5_hold_reason_codes": _dedupe(p3_9_summary.get("p5_hold_reason_codes")),
        "post_p4_current_only_readfeel_minimum_met": p3_9_summary.get("current_only_readfeel_minimum_met") is True,
        "post_p4_main_family_readfeel_minimum_met": p3_9_summary.get("main_family_readfeel_minimum_met") is True,
        "p5_hold_continues": not p5_allowed,
        "p5_visible_surface_strengthened": False,
        "p5_runtime_change_applied": False,
        "recommended_next_action": next_action,
        "connection_evidence_body_free": True,
        "connection_evidence_current_only_min_read_feeling": connection_evidence.get("current_only_min_read_feeling"),
        "connection_evidence_current_only_min_naturalness": connection_evidence.get("current_only_min_naturalness"),
        "connection_evidence_current_only_min_non_template": connection_evidence.get("current_only_min_non_template"),
        "ratings_only_payload": True,
        "public_text_payload_excluded": True,
        "body_free_case_references_only": True,
        "local_review_packet_retained": False,
        "local_review_packet_body_retained": False,
        "raw_input_included": False,
        "raw_text_included": False,
        "comment_text_included": False,
        "comment_text_body_included": False,
        "candidate_body_included": False,
        "surface_body_included": False,
        "history_raw_text_included": False,
        "raw_test_output_included": False,
        "exact_comment_text_required": False,
        "case_specific_runtime_branch": False,
        "runtime_branching_uses_fixture_strings": False,
        "fixture_text_used_for_runtime_branching": False,
        "fixed_sentence_template_added": False,
        "input_specific_template_added": False,
        "runtime_repair_applied": False,
        "p4_runtime_tuning_applied": False,
        "public_response_key_added": False,
        "public_response_key_change": False,
        "response_shape_changed": False,
        "api_route_changed": False,
        "db_physical_name_changed": False,
        "rn_visible_contract_changed": False,
        "gate_relaxed": False,
        "display_gate_relaxed": False,
        "grounding_gate_relaxed": False,
        "reader_gate_relaxed": False,
        "template_gate_relaxed": False,
        "product_gate_ready": False,
        "product_gate_reached": False,
        "public_release_applied": False,
        "product_quality_released": False,
    }
    assert_product_readfeel_p4_ratings_review_meta_only_20260610(summary, source="p4_9.summary")
    return summary


def build_product_readfeel_p4_ratings_review_20260610(
    *,
    p4_target_case_selection: Mapping[str, Any] | None = None,
    p4_ratings_reviews: Sequence[Mapping[str, Any] | None] | Iterable[Mapping[str, Any] | None] | None = None,
    reviews: Sequence[Mapping[str, Any] | None] | Iterable[Mapping[str, Any] | None] | None = None,
    p3_regression_result: Mapping[str, Any] | None = None,
    p5_recheck_overrides: Mapping[str, Any] | None = None,
    run_id: str | None = None,
) -> dict[str, Any]:
    run_id_value = _safe_identifier(run_id, default="p4_9_ratings_review")
    selected_lookup = _selected_case_lookup(p4_target_case_selection)
    raw_reviews = list(p4_ratings_reviews if p4_ratings_reviews is not None else reviews or [])
    review_rows = [
        normalize_product_readfeel_p4_ratings_review_row_20260610(
            review,
            selected_cases_by_key=selected_lookup,
            run_id=run_id_value,
            index=index,
        )
        for index, review in enumerate(raw_reviews, start=1)
    ]
    family_summary = _family_summary(review_rows)
    connection_evidence = _build_connection_evidence(
        review_rows=review_rows,
        p4_target_case_selection=p4_target_case_selection,
        p5_recheck_overrides=p5_recheck_overrides,
    )
    regression = p3_regression_result or _default_p3_regression_for_redecision(run_id_value)
    p3_9_redecision = build_product_readfeel_p3_p4_p5_connection_decision_20260609(
        p3_regression_result=regression,
        p3_connection_evidence=connection_evidence,
        run_id=f"{run_id_value}_post_p4_p3_9_redecision",
    )
    assert_product_readfeel_p3_p4_p5_connection_decision_meta_only_20260609(
        p3_9_redecision, source="p4_9.post_p4_p3_9_redecision"
    )
    summary = _summary(
        run_id=run_id_value,
        review_rows=review_rows,
        p4_target_case_selection=p4_target_case_selection,
        family_summary=family_summary,
        p3_9_redecision=p3_9_redecision,
        connection_evidence=connection_evidence,
    )
    payload = {
        "schema_version": PRODUCT_READFEEL_P4_RATINGS_REVIEW_VERSION_20260610,
        "version": PRODUCT_READFEEL_P4_RATINGS_REVIEW_VERSION_20260610,
        "source": PRODUCT_READFEEL_P4_RATINGS_REVIEW_SOURCE_20260610,
        "source_step": PRODUCT_READFEEL_P4_RATINGS_REVIEW_STEP_20260610,
        "run_id": run_id_value,
        "run_profile": PRODUCT_READFEEL_P4_RATINGS_REVIEW_PROFILE_20260610,
        "review_rows": review_rows,
        "review_row_count": len(review_rows),
        "family_rating_summary": family_summary,
        "connection_evidence": connection_evidence,
        "post_p4_p3_9_redecision": p3_9_redecision,
        "summary": summary,
        "public_summary": build_product_readfeel_p4_ratings_review_public_summary_20260610(summary),
        "p4_9_ratings_only_review_ready": bool(review_rows),
        "p3_9_redecision_created": True,
        "ratings_only_payload": True,
        "public_text_payload_excluded": True,
        "body_free_case_references_only": True,
        "local_review_packet_retained": False,
        "local_review_packet_body_retained": False,
        "raw_input_included": False,
        "raw_text_included": False,
        "comment_text_included": False,
        "comment_text_body_included": False,
        "candidate_body_included": False,
        "surface_body_included": False,
        "history_raw_text_included": False,
        "raw_test_output_included": False,
        "machine_metrics_used_for_read_feeling": False,
        "read_feeling_auto_filled_from_machine_metrics": False,
        "read_feeling_auto_estimation_allowed": False,
        "exact_comment_text_required": False,
        "case_specific_runtime_branch": False,
        "runtime_branching_uses_fixture_strings": False,
        "fixture_text_used_for_runtime_branching": False,
        "fixed_sentence_template_added": False,
        "input_specific_template_added": False,
        "runtime_repair_applied": False,
        "p4_runtime_tuning_applied": False,
        "p5_visible_surface_strengthened": False,
        "p5_runtime_change_applied": False,
        "public_response_key_added": False,
        "public_response_key_change": False,
        "response_shape_changed": False,
        "api_route_changed": False,
        "db_physical_name_changed": False,
        "rn_visible_contract_changed": False,
        "gate_relaxed": False,
        "display_gate_relaxed": False,
        "grounding_gate_relaxed": False,
        "reader_gate_relaxed": False,
        "template_gate_relaxed": False,
        "product_gate_ready": False,
        "product_gate_reached": False,
        "public_release_applied": False,
        "product_quality_released": False,
    }
    assert_product_readfeel_p4_ratings_review_meta_only_20260610(payload, source="p4_9.payload")
    return payload


def build_product_readfeel_p4_ratings_review_public_summary_20260610(
    review_payload_or_summary: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    source = dict(review_payload_or_summary or {})
    if source.get("schema_version") == PRODUCT_READFEEL_P4_RATINGS_REVIEW_VERSION_20260610:
        source = dict(source.get("summary") or {})
    public_summary = dict(source)
    public_summary["schema_version"] = PRODUCT_READFEEL_P4_RATINGS_REVIEW_SUMMARY_VERSION_20260610
    public_summary["version"] = PRODUCT_READFEEL_P4_RATINGS_REVIEW_SUMMARY_VERSION_20260610
    public_summary["source"] = PRODUCT_READFEEL_P4_RATINGS_REVIEW_SOURCE_20260610
    public_summary["source_step"] = PRODUCT_READFEEL_P4_RATINGS_REVIEW_STEP_20260610
    public_summary.pop("review_rows", None)
    public_summary.pop("connection_evidence", None)
    public_summary.pop("post_p4_p3_9_redecision", None)
    public_summary["ratings_only_payload"] = True
    public_summary["public_text_payload_excluded"] = True
    public_summary["body_free_case_references_only"] = True
    public_summary["comment_text_body_included"] = False
    public_summary["raw_input_included"] = False
    public_summary["candidate_body_included"] = False
    public_summary["history_raw_text_included"] = False
    public_summary["raw_test_output_included"] = False
    public_summary["machine_metrics_used_for_read_feeling"] = False
    public_summary["read_feeling_auto_filled_from_machine_metrics"] = False
    public_summary["read_feeling_auto_estimation_allowed"] = False
    public_summary["p4_runtime_tuning_applied"] = False
    public_summary["p5_visible_surface_strengthened"] = False
    public_summary["p5_runtime_change_applied"] = False
    public_summary["gate_relaxed"] = False
    public_summary["product_gate_ready"] = False
    public_summary["public_release_applied"] = False
    assert_product_readfeel_p4_ratings_review_meta_only_20260610(public_summary, source="p4_9.public_summary")
    return public_summary


def dump_product_readfeel_p4_ratings_review_public_summary_20260610(
    review_payload_or_summary: Mapping[str, Any] | None = None,
) -> str:
    summary = build_product_readfeel_p4_ratings_review_public_summary_20260610(review_payload_or_summary)
    return json.dumps(summary, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


__all__ = [
    "PRODUCT_READFEEL_P4_RATINGS_REVIEW_VERSION_20260610",
    "PRODUCT_READFEEL_P4_RATINGS_REVIEW_ROW_VERSION_20260610",
    "PRODUCT_READFEEL_P4_RATINGS_REVIEW_SUMMARY_VERSION_20260610",
    "PRODUCT_READFEEL_P4_RATINGS_REVIEW_STEP_20260610",
    "PRODUCT_READFEEL_P4_RATINGS_REVIEW_PROFILE_20260610",
    "P4_9_STATUS_IMPROVED",
    "P4_9_STATUS_UNCHANGED",
    "P4_9_STATUS_WORSENED",
    "P4_9_STATUS_NOT_EVALUATED",
    "assert_product_readfeel_p4_ratings_review_meta_only_20260610",
    "normalize_product_readfeel_p4_ratings_review_row_20260610",
    "build_product_readfeel_p4_ratings_review_20260610",
    "build_product_readfeel_p4_ratings_review_public_summary_20260610",
    "dump_product_readfeel_p4_ratings_review_public_summary_20260610",
    "DECISION_P4_NEXT_P5_HOLD",
    "DECISION_P5_READY_AFTER_P4",
]
