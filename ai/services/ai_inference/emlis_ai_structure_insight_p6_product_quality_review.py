# -*- coding: utf-8 -*-
from __future__ import annotations

"""P6-8 ratings-only Product QA / Blind QA material.

P6 Product QA is not a release gate.  It aggregates ratings-only review rows
into body-free material for P7 long-run evaluation.  It must not store raw
input, comment bodies, candidate bodies, surface bodies, reviewer free text, or
terminal output.
"""

from collections import Counter
from collections.abc import Iterable, Mapping, Sequence
import json
from typing import Any, Final


STRUCTURE_INSIGHT_P6_PRODUCT_QUALITY_REVIEW_SCHEMA_VERSION: Final = (
    "cocolon.emlis.structure_insight.p6_product_quality_review.v1"
)
STRUCTURE_INSIGHT_P6_PRODUCT_QUALITY_REVIEW_ROW_SCHEMA_VERSION: Final = (
    "cocolon.emlis.structure_insight.p6_product_quality_review_row.v1"
)
STRUCTURE_INSIGHT_P6_PRODUCT_QUALITY_REVIEW_SUMMARY_SCHEMA_VERSION: Final = (
    "cocolon.emlis.structure_insight.p6_product_quality_review_summary.v1"
)
STRUCTURE_INSIGHT_P6_PRODUCT_QUALITY_REVIEW_STEP: Final = (
    "P6-8_RatingsOnlyProductQABlindQAMaterial"
)
STRUCTURE_INSIGHT_P6_PRODUCT_QUALITY_REVIEW_SOURCE: Final = (
    "Cocolon_EmlisAI_P6_StructureInsight_ProductQualityReview_20260612"
)

VERDICT_RED: Final = "RED"
VERDICT_REPAIR_REQUIRED: Final = "REPAIR_REQUIRED"
VERDICT_YELLOW: Final = "YELLOW"
VERDICT_PASS: Final = "PASS"
VERDICT_STRUCTURE_INSIGHT_READY: Final = "STRUCTURE_INSIGHT_READY"
P6_PRODUCT_QA_VERDICTS: Final[tuple[str, ...]] = (
    VERDICT_RED,
    VERDICT_REPAIR_REQUIRED,
    VERDICT_YELLOW,
    VERDICT_PASS,
    VERDICT_STRUCTURE_INSIGHT_READY,
)

QA_BUCKET_READY: Final = "ready"
QA_BUCKET_WEAK: Final = "weak"
QA_BUCKET_UNSAFE: Final = "unsafe"

FAMILY_STRUCTURE_QUESTION: Final = "structure_question"
FAMILY_LONG_MEANING_ARC: Final = "long_meaning_arc"
FAMILY_SELF_UNDERSTANDING_FOLLOW: Final = "self_understanding_follow"
FAMILY_NO_CONNECT_REGRESSION: Final = "no_connect_family_regression"
FAMILY_HIGH_RISK_RELATION_HOLD: Final = "high_risk_relation_hold_case"
P6_PRODUCT_QA_REVIEW_TARGETS: Final[tuple[str, ...]] = (
    FAMILY_STRUCTURE_QUESTION,
    FAMILY_LONG_MEANING_ARC,
    FAMILY_SELF_UNDERSTANDING_FOLLOW,
    FAMILY_NO_CONNECT_REGRESSION,
    FAMILY_HIGH_RISK_RELATION_HOLD,
)

REASON_REVIEW_ROWS_MISSING: Final = "ratings_only_review_rows_missing"
REASON_RATING_NUMBERS_MISSING: Final = "rating_numbers_missing"
REASON_UNSAFE_VERDICT: Final = "unsafe_verdict"
REASON_WEAK_VERDICT: Final = "weak_verdict"
REASON_REVIEW_TARGET_UNKNOWN: Final = "review_target_unknown"
REASON_FAMILY_REVIEW_BLOCKED: Final = "family_review_blocked"
REASON_FAMILY_REVIEW_HELD: Final = "family_review_held"
REASON_SURFACE_ROLE_PLAN_BLOCKED: Final = "surface_role_plan_blocked"
REASON_GATE_OR_POLICY_BLOCKED: Final = "gate_or_policy_blocked"
REASON_RAW_TEXT_PAYLOAD_DETECTED: Final = "raw_text_payload_detected"
REASON_COMMENT_TEXT_BODY_DETECTED: Final = "comment_text_body_detected"
REASON_REVIEWER_FREE_TEXT_DETECTED: Final = "reviewer_free_text_detected"
REASON_PUBLIC_CONTRACT_MUTATION_DETECTED: Final = "public_contract_mutation_detected"
REASON_FIXED_SENTENCE_TEMPLATE_DETECTED: Final = "fixed_sentence_template_detected"
REASON_RELEASE_FLAG_DETECTED: Final = "release_flag_detected"

_UNSAFE_REASON_CODES: Final[frozenset[str]] = frozenset(
    {
        "unsafe_claim",
        "unsafe_claim_or_red_flag",
        "diagnosis",
        "diagnosis_surface",
        "personality_claim",
        "personality_claim_surface",
        "cause_claim_without_evidence",
        "cause_claim_without_evidence_surface",
        "advice",
        "advice_surface",
        "future_prediction",
        "future_prediction_surface",
        "target_judgement",
        "target_judgement_surface",
        "target_judgement_agreement",
        "target_judgement_risk_blocked",
        "self_denial_identity_fact_blocked",
        "raw_text_payload_detected",
        "comment_text_body_detected",
        "reviewer_free_text_detected",
        "public_contract_mutation_detected",
        "release_flag_detected",
    }
)
_WEAK_REASON_CODES: Final[frozenset[str]] = frozenset(
    {
        "weak_verdict",
        "soft_marker_missing",
        "insight_too_shallow",
        "mirror_only_reduction_below_target",
        "family_mismatch",
        "family_review_held",
        "high_risk_relation_held_for_review",
        "long_meaning_arc_multiple_core_missing",
        "long_meaning_arc_relation_flow_missing",
        "self_understanding_observation_intent_missing",
        "self_understanding_uncertainty_boundary_missing",
        "rating_numbers_missing",
    }
)

_TEXT_PAYLOAD_KEYS: Final[frozenset[str]] = frozenset(
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
        "candidate_body",
        "candidateBody",
        "surface_body",
        "surfaceBody",
        "surface_text",
        "surfaceText",
        "visible_text",
        "visibleText",
        "reply_text",
        "replyText",
        "display_text",
        "displayText",
        "observation_text",
        "reception_text",
        "raw_test_output",
        "test_output",
        "command_output",
        "terminal_output",
        "stdout",
        "stderr",
        "traceback",
        "body",
        "text",
    }
)
_COMMENT_TEXT_PAYLOAD_KEYS: Final[frozenset[str]] = frozenset(
    {"comment_text", "commentText", "comment_text_body", "commentTextBody", "candidate_comment_text"}
)
_REVIEWER_FREE_TEXT_KEYS: Final[frozenset[str]] = frozenset(
    {"reviewer_note", "reviewer_notes", "review_notes", "free_text_note", "reviewer_free_text", "blind_qa_free_text"}
)
_PUBLIC_CONTRACT_TRUE_FLAGS: Final[frozenset[str]] = frozenset(
    {
        "api_route_changed",
        "request_key_changed",
        "response_shape_changed",
        "public_response_key_added",
        "public_response_key_change",
        "public_payload_changed",
        "db_schema_changed",
        "db_physical_name_changed",
        "rn_visible_contract_changed",
        "rn_visible_title_changed",
        "public_release_applied",
        "product_quality_released",
    }
)
_FIXED_TEMPLATE_TRUE_FLAGS: Final[frozenset[str]] = frozenset(
    {
        "fixed_sentence_template_added",
        "fixed_sentence_template_used",
        "fixed_template_added",
        "fixed_template_used",
        "input_specific_template_added",
        "input_specific_template_used",
        "completed_sentence_template_used",
        "completion_sentence_template_used",
        "role_completed_sentence_template_used",
        "fallback_observation_sentence_added",
    }
)
_FORBIDDEN_TRUE_FLAGS: Final[frozenset[str]] = (
    _PUBLIC_CONTRACT_TRUE_FLAGS
    | _FIXED_TEMPLATE_TRUE_FLAGS
    | frozenset(
        {
            "raw_input_included",
            "raw_text_included",
            "input_text_included",
            "comment_text_included",
            "comment_text_body_included",
            "candidate_body_included",
            "surface_body_included",
            "history_raw_text_included",
            "reviewer_free_text_included",
            "raw_test_output_included",
            "command_output_included",
            "terminal_output_included",
            "comment_text_generated",
            "comment_text_key_written",
            "surface_body_returned",
            "candidate_body_returned",
            "release_allowed",
            "external_ai_used",
            "local_llm_used",
        }
    )
)


def _clean(value: Any) -> str:
    if value is None or isinstance(value, (Mapping, list, tuple, set)):
        return ""
    return str(value).replace("\u3000", " ").strip()


def _safe_mapping(value: Any) -> dict[str, Any]:
    if isinstance(value, Mapping):
        return {str(key): item for key, item in value.items()}
    return {}


def _listify(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return list(value)
    if isinstance(value, (tuple, set)):
        return list(value)
    if isinstance(value, (str, bytes, bytearray)):
        return [value]
    try:
        return list(value)
    except TypeError:
        return [value]


def _dedupe(values: Iterable[Any] | Any | None) -> list[str]:
    out: list[str] = []
    for value in _listify(values):
        item = _clean(value)
        if item and item not in out:
            out.append(item)
    return out


def _safe_id(value: Any, *, default: str = "", max_length: int = 96) -> str:
    text = _clean(value) or default
    safe = "".join(ch if ch.isalnum() or ch in "._:-" else "_" for ch in text)
    safe = safe.strip("_")
    return (safe or default)[:max_length]


def _canonical_id(value: Any) -> str:
    return _clean(value).lower().replace(" ", "_").replace("-", "_")


def _score(value: Any) -> float | None:
    if isinstance(value, bool):
        return 1.0 if value else 0.0
    try:
        if value is None or value == "":
            return None
        number = float(value)
    except (TypeError, ValueError):
        return None
    if 1.0 < number <= 100.0:
        number = number / 100.0
    return max(0.0, min(1.0, round(number, 4)))


def _contains_key(value: Any, names: frozenset[str]) -> bool:
    if isinstance(value, Mapping):
        for key, child in value.items():
            if str(key) in names:
                return True
            if _contains_key(child, names):
                return True
    elif isinstance(value, (list, tuple, set)):
        return any(_contains_key(child, names) for child in value)
    return False


def _flag_true(value: Any, names: frozenset[str]) -> bool:
    if isinstance(value, Mapping):
        for key, child in value.items():
            if str(key) in names and child is True:
                return True
            if _flag_true(child, names):
                return True
    elif isinstance(value, (list, tuple, set)):
        return any(_flag_true(child, names) for child in value)
    return False


def _summary(value: Mapping[str, Any]) -> dict[str, Any]:
    return _safe_mapping(value.get("summary")) or dict(value)


def _public_contract() -> dict[str, bool]:
    return {
        "public_response_key_added": False,
        "rn_visible_contract_changed": False,
        "response_shape_changed": False,
        "api_route_changed": False,
        "request_key_changed": False,
        "db_schema_changed": False,
        "fixed_sentence_template_added": False,
        "input_specific_template_added": False,
        "release_allowed": False,
        "public_release_applied": False,
        "product_quality_released": False,
    }


def _body_free_contract() -> dict[str, bool]:
    return {
        "raw_input_included": False,
        "raw_text_included": False,
        "input_text_included": False,
        "comment_text_body_included": False,
        "candidate_body_included": False,
        "surface_body_included": False,
        "history_raw_text_included": False,
        "reviewer_free_text_included": False,
        "raw_test_output_included": False,
        "command_output_included": False,
        "terminal_output_included": False,
    }


def _ratings_from_row(row: Mapping[str, Any]) -> dict[str, float]:
    ratings_source = _safe_mapping(row.get("ratings") or row.get("dimension_ratings") or row.get("rating_numbers"))
    ratings: dict[str, float] = {}
    for key, value in {**ratings_source, **row}.items():
        if str(key) in {
            "schema_version",
            "version",
            "source",
            "step",
            "row_id",
            "case_id",
            "family",
            "relation_family",
            "surface_role",
            "verdict",
            "reason_codes",
            "decision_reason_codes",
            "safe_reason_codes",
            "blocker_reason_codes",
        }:
            continue
        score = _score(value)
        if score is not None:
            ratings[str(key)] = score
    return dict(sorted(ratings.items()))


def _source_reasons(*sources: Mapping[str, Any]) -> list[str]:
    reasons: list[str] = []
    for source in sources:
        data = _summary(source)
        reasons.extend(_dedupe(data.get("decision_reason_codes")))
        reasons.extend(_dedupe(data.get("safe_reason_codes")))
        reasons.extend(_dedupe(data.get("blocker_reason_codes")))
        if data.get("blocked") is True or data.get("block") is True:
            reasons.append(REASON_GATE_OR_POLICY_BLOCKED)
        if data.get("family_review_classification") == "block":
            reasons.append(REASON_FAMILY_REVIEW_BLOCKED)
        if data.get("family_review_classification") == "hold":
            reasons.append(REASON_FAMILY_REVIEW_HELD)
        if data.get("surface_plan_kind") == "blocked":
            reasons.append(REASON_SURFACE_ROLE_PLAN_BLOCKED)
        if data.get("release_allowed") is True:
            reasons.append(REASON_RELEASE_FLAG_DETECTED)
    return _dedupe(reasons)


def _meta_reasons(sources: Iterable[Mapping[str, Any]]) -> list[str]:
    reasons: list[str] = []
    for source in sources:
        if _contains_key(source, _TEXT_PAYLOAD_KEYS):
            reasons.append(REASON_RAW_TEXT_PAYLOAD_DETECTED)
        if _contains_key(source, _COMMENT_TEXT_PAYLOAD_KEYS):
            reasons.append(REASON_COMMENT_TEXT_BODY_DETECTED)
        if _contains_key(source, _REVIEWER_FREE_TEXT_KEYS):
            reasons.append(REASON_REVIEWER_FREE_TEXT_DETECTED)
        if _flag_true(source, _PUBLIC_CONTRACT_TRUE_FLAGS):
            reasons.append(REASON_PUBLIC_CONTRACT_MUTATION_DETECTED)
        if _flag_true(source, _FIXED_TEMPLATE_TRUE_FLAGS):
            reasons.append(REASON_FIXED_SENTENCE_TEMPLATE_DETECTED)
        if _flag_true(source, frozenset({"release_allowed", "public_release_applied"})):
            reasons.append(REASON_RELEASE_FLAG_DETECTED)
    return _dedupe(reasons)


def _verdict_from_sources(
    *,
    row: Mapping[str, Any],
    p6_quality_rubric: Mapping[str, Any],
    p6_family_review: Mapping[str, Any],
) -> str:
    explicit = _clean(row.get("verdict")).upper()
    if explicit in P6_PRODUCT_QA_VERDICTS:
        return explicit
    quality_verdict = _clean(_summary(p6_quality_rubric).get("verdict")).upper()
    if quality_verdict in P6_PRODUCT_QA_VERDICTS:
        return quality_verdict
    family_classification = _clean(_summary(p6_family_review).get("family_review_classification"))
    if family_classification == "block":
        return VERDICT_RED
    if family_classification == "hold":
        return VERDICT_REPAIR_REQUIRED
    if family_classification == "allow":
        return VERDICT_PASS
    return VERDICT_PASS


def _bucket_for(verdict: str, reasons: Sequence[str]) -> str:
    reason_set = set(reasons)
    if verdict == VERDICT_RED or reason_set.intersection(_UNSAFE_REASON_CODES):
        return QA_BUCKET_UNSAFE
    if verdict in {VERDICT_REPAIR_REQUIRED, VERDICT_YELLOW} or reason_set.intersection(_WEAK_REASON_CODES):
        return QA_BUCKET_WEAK
    if verdict == VERDICT_STRUCTURE_INSIGHT_READY:
        return QA_BUCKET_READY
    return QA_BUCKET_WEAK


def _p7_field_candidate(row: Mapping[str, Any]) -> dict[str, Any]:
    return {
        "case_id": row.get("case_id"),
        "family": row.get("family"),
        "relation_family": row.get("relation_family"),
        "surface_role": row.get("surface_role"),
        "verdict": row.get("verdict"),
        "qa_bucket": row.get("qa_bucket"),
        "rating_numbers": dict(row.get("rating_numbers") or {}),
        "safe_reason_codes": list(row.get("safe_reason_codes") or []),
        "body_free": _body_free_contract(),
        "public_contract": _public_contract(),
    }


def normalize_structure_insight_p6_product_quality_review_row(
    review_row: Mapping[str, Any] | None,
    *,
    index: int = 0,
    p6_quality_rubric: Mapping[str, Any] | None = None,
    p6_surface_role_plan: Mapping[str, Any] | None = None,
    p6_family_review: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Normalize a ratings-only P6 Product QA row."""

    row = _safe_mapping(review_row)
    quality = _safe_mapping(row.get("p6_quality_rubric") or p6_quality_rubric)
    surface_plan = _safe_mapping(row.get("p6_surface_role_plan") or p6_surface_role_plan)
    family_review = _safe_mapping(row.get("p6_family_review") or p6_family_review)
    row_id = _safe_id(row.get("row_id") or row.get("id"), default=f"p6-product-qa-row-{index:03d}")
    family = _canonical_id(row.get("family")) or _canonical_id(_summary(family_review).get("family"))
    relation = (
        _canonical_id(row.get("relation_family"))
        or _canonical_id(_summary(family_review).get("relation_family"))
        or _canonical_id(_summary(quality).get("relation_family"))
    )
    surface_role = _safe_id(row.get("surface_role"), default="ratings_only_review")
    ratings = _ratings_from_row(row)
    verdict = _verdict_from_sources(row=row, p6_quality_rubric=quality, p6_family_review=family_review)
    reasons = _dedupe(
        [
            *_meta_reasons((row, quality, surface_plan, family_review)),
            *_source_reasons(row, quality, surface_plan, family_review),
            *_dedupe(row.get("reason_codes")),
            *_dedupe(row.get("decision_reason_codes")),
            *_dedupe(row.get("safe_reason_codes")),
            *_dedupe(row.get("blocker_reason_codes")),
        ]
    )
    if not ratings:
        reasons.append(REASON_RATING_NUMBERS_MISSING)
    if family and family not in P6_PRODUCT_QA_REVIEW_TARGETS:
        reasons.append(REASON_REVIEW_TARGET_UNKNOWN)
    if verdict == VERDICT_RED:
        reasons.append(REASON_UNSAFE_VERDICT)
    if verdict in {VERDICT_REPAIR_REQUIRED, VERDICT_YELLOW}:
        reasons.append(REASON_WEAK_VERDICT)
    reasons = _dedupe(reasons)
    bucket = _bucket_for(verdict, reasons)
    p7_candidate = bucket == QA_BUCKET_READY and verdict == VERDICT_STRUCTURE_INSIGHT_READY
    normalized = {
        "schema_version": STRUCTURE_INSIGHT_P6_PRODUCT_QUALITY_REVIEW_ROW_SCHEMA_VERSION,
        "version": STRUCTURE_INSIGHT_P6_PRODUCT_QUALITY_REVIEW_ROW_SCHEMA_VERSION,
        "source": STRUCTURE_INSIGHT_P6_PRODUCT_QUALITY_REVIEW_SOURCE,
        "step": STRUCTURE_INSIGHT_P6_PRODUCT_QUALITY_REVIEW_STEP,
        "row_id": row_id,
        "case_id": _safe_id(row.get("case_id"), default=row_id),
        "family": family,
        "relation_family": relation,
        "surface_role": surface_role,
        "verdict": verdict,
        "qa_bucket": bucket,
        "unsafe": bucket == QA_BUCKET_UNSAFE,
        "weak": bucket == QA_BUCKET_WEAK,
        "ready": bucket == QA_BUCKET_READY,
        "rating_numbers": ratings,
        "safe_reason_codes": reasons,
        "blocker_reason_codes": [reason for reason in reasons if reason in _UNSAFE_REASON_CODES or reason in _WEAK_REASON_CODES],
        "p7_long_run_field_candidate": p7_candidate,
        "ratings_only": True,
        "body_free_row_only": True,
        "raw_input_included": False,
        "raw_text_included": False,
        "comment_text_body_included": False,
        "candidate_body_included": False,
        "surface_body_included": False,
        "reviewer_free_text_included": False,
        "public_response_key_added": False,
        "rn_visible_contract_changed": False,
        "response_shape_changed": False,
        "fixed_sentence_template_added": False,
        "release_allowed": False,
        "public_release_applied": False,
        "public_contract": _public_contract(),
        "body_free": _body_free_contract(),
    }
    assert_structure_insight_p6_product_quality_review_contract(normalized, allow_partial=True)
    return normalized


def _rows_from_sources(
    *,
    p6_quality_rubric: Mapping[str, Any],
    p6_surface_role_plan: Mapping[str, Any],
    p6_family_review: Mapping[str, Any],
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    quality_summary = _summary(p6_quality_rubric)
    if quality_summary:
        averages = _safe_mapping(quality_summary.get("dimension_averages"))
        if averages:
            rows.append(
                {
                    "row_id": "p6-product-qa-quality-summary",
                    "case_id": "p6-product-qa-quality-summary",
                    "family": quality_summary.get("family") or _summary(p6_surface_role_plan).get("family"),
                    "relation_family": quality_summary.get("relation_family")
                    or _summary(p6_surface_role_plan).get("relation_family"),
                    "surface_role": _summary(p6_surface_role_plan).get("surface_plan_kind") or "quality_summary",
                    "verdict": quality_summary.get("verdict"),
                    "ratings": averages,
                    "decision_reason_codes": quality_summary.get("decision_reason_codes"),
                }
            )
    family_summary = _summary(p6_family_review)
    if family_summary:
        rows.append(
            {
                "row_id": f"p6-product-qa-family-review-{_canonical_id(family_summary.get('family')) or 'family'}",
                "case_id": f"p6-product-qa-family-review-{_canonical_id(family_summary.get('family')) or 'family'}",
                "family": family_summary.get("family"),
                "relation_family": family_summary.get("relation_family"),
                "surface_role": "family_review",
                "verdict": VERDICT_PASS if family_summary.get("family_review_classification") == "allow" else "",
                "ratings": {"family_review_body_free": 1.0},
                "decision_reason_codes": family_summary.get("decision_reason_codes"),
                "p6_family_review": p6_family_review,
            }
        )
    return rows


def _average_dimension_ratings(rows: Sequence[Mapping[str, Any]]) -> dict[str, float]:
    values_by_key: dict[str, list[float]] = {}
    for row in rows:
        for key, value in _safe_mapping(row.get("rating_numbers")).items():
            score = _score(value)
            if score is not None:
                values_by_key.setdefault(key, []).append(score)
    return {
        key: round(sum(values) / len(values), 4)
        for key, values in sorted(values_by_key.items())
        if values
    }


def build_structure_insight_p6_product_quality_review(
    *,
    review_rows: Sequence[Mapping[str, Any] | None] | Iterable[Mapping[str, Any] | None] | None = None,
    p6_quality_rubric: Mapping[str, Any] | None = None,
    p6_surface_role_plan: Mapping[str, Any] | None = None,
    p6_family_review: Mapping[str, Any] | None = None,
    run_id: str | None = None,
) -> dict[str, Any]:
    """Build a body-free P6 ratings-only Product QA summary."""

    run = _clean(run_id) or "p6_product_quality_review"
    quality = _safe_mapping(p6_quality_rubric)
    surface_plan = _safe_mapping(p6_surface_role_plan)
    family_review = _safe_mapping(p6_family_review)
    source_rows = [row for row in _listify(review_rows) if isinstance(row, Mapping)]
    if not source_rows:
        source_rows = _rows_from_sources(
            p6_quality_rubric=quality,
            p6_surface_role_plan=surface_plan,
            p6_family_review=family_review,
        )
    rows = [
        normalize_structure_insight_p6_product_quality_review_row(
            row,
            index=index,
            p6_quality_rubric=quality,
            p6_surface_role_plan=surface_plan,
            p6_family_review=family_review,
        )
        for index, row in enumerate(source_rows)
    ]
    summary_reasons = _meta_reasons((quality, surface_plan, family_review))
    if not rows:
        summary_reasons.append(REASON_REVIEW_ROWS_MISSING)
    verdict_counts = {verdict: 0 for verdict in P6_PRODUCT_QA_VERDICTS}
    bucket_counts = {QA_BUCKET_READY: 0, QA_BUCKET_WEAK: 0, QA_BUCKET_UNSAFE: 0}
    for row in rows:
        verdict_counts[_clean(row.get("verdict")) or VERDICT_PASS] = verdict_counts.get(_clean(row.get("verdict")), 0) + 1
        bucket_counts[_clean(row.get("qa_bucket"))] = bucket_counts.get(_clean(row.get("qa_bucket")), 0) + 1
    blocker_reason_codes = _dedupe(
        [
            *summary_reasons,
            *(reason for row in rows for reason in _dedupe(row.get("blocker_reason_codes"))),
            *(reason for row in rows for reason in _dedupe(row.get("safe_reason_codes")) if reason in _UNSAFE_REASON_CODES),
        ]
    )
    p7_candidates = [_p7_field_candidate(row) for row in rows if row.get("p7_long_run_field_candidate") is True]
    structure_ready_count = sum(1 for row in rows if row.get("verdict") == VERDICT_STRUCTURE_INSIGHT_READY)
    summary = {
        "schema_version": STRUCTURE_INSIGHT_P6_PRODUCT_QUALITY_REVIEW_SUMMARY_SCHEMA_VERSION,
        "version": STRUCTURE_INSIGHT_P6_PRODUCT_QUALITY_REVIEW_SUMMARY_SCHEMA_VERSION,
        "source": STRUCTURE_INSIGHT_P6_PRODUCT_QUALITY_REVIEW_SOURCE,
        "step": STRUCTURE_INSIGHT_P6_PRODUCT_QUALITY_REVIEW_STEP,
        "run_id": run,
        "ratings_only": True,
        "review_count": len(rows),
        "dimension_averages": _average_dimension_ratings(rows),
        "verdict_counts": verdict_counts,
        "bucket_counts": bucket_counts,
        "structure_insight_ready_candidate_count": structure_ready_count,
        "unsafe_candidate_count": bucket_counts.get(QA_BUCKET_UNSAFE, 0),
        "weak_candidate_count": bucket_counts.get(QA_BUCKET_WEAK, 0),
        "ready_candidate_count": bucket_counts.get(QA_BUCKET_READY, 0),
        "p7_long_run_field_candidate_count": len(p7_candidates),
        "p7_long_run_field_candidates": p7_candidates,
        "blocker_reason_codes": blocker_reason_codes,
        "release_allowed": False,
        "public_release_applied": False,
        "product_quality_released": False,
        "public_contract": _public_contract(),
        "body_free": _body_free_contract(),
    }
    report = {
        "schema_version": STRUCTURE_INSIGHT_P6_PRODUCT_QUALITY_REVIEW_SCHEMA_VERSION,
        "version": STRUCTURE_INSIGHT_P6_PRODUCT_QUALITY_REVIEW_SCHEMA_VERSION,
        "source": STRUCTURE_INSIGHT_P6_PRODUCT_QUALITY_REVIEW_SOURCE,
        "step": STRUCTURE_INSIGHT_P6_PRODUCT_QUALITY_REVIEW_STEP,
        "run_id": run,
        "ratings_only": True,
        "review_count": len(rows),
        "rows": rows,
        "dimension_averages": summary["dimension_averages"],
        "verdict_counts": verdict_counts,
        "bucket_counts": bucket_counts,
        "structure_insight_ready_candidate_count": structure_ready_count,
        "unsafe_candidate_count": bucket_counts.get(QA_BUCKET_UNSAFE, 0),
        "weak_candidate_count": bucket_counts.get(QA_BUCKET_WEAK, 0),
        "ready_candidate_count": bucket_counts.get(QA_BUCKET_READY, 0),
        "p7_long_run_field_candidate_count": len(p7_candidates),
        "p7_long_run_field_candidates": p7_candidates,
        "blocker_reason_codes": blocker_reason_codes,
        "release_allowed": False,
        "public_release_applied": False,
        "product_quality_released": False,
        "public_contract": _public_contract(),
        "body_free": _body_free_contract(),
        "summary": summary,
    }
    assert_structure_insight_p6_product_quality_review_contract(report)
    return report


def assert_structure_insight_p6_product_quality_review_contract(
    report: Mapping[str, Any],
    *,
    allow_partial: bool = False,
) -> bool:
    """Validate that P6-8 Product QA material stays ratings-only and body-free."""

    if not isinstance(report, Mapping):
        raise TypeError("P6 product quality review must be a mapping")
    data = _safe_mapping(report)
    if not allow_partial and data.get("schema_version") != STRUCTURE_INSIGHT_P6_PRODUCT_QUALITY_REVIEW_SCHEMA_VERSION:
        raise ValueError("Unexpected P6 product quality review schema version")
    if not allow_partial and data.get("step") != STRUCTURE_INSIGHT_P6_PRODUCT_QUALITY_REVIEW_STEP:
        raise ValueError("Unexpected P6 product quality review step")
    if data.get("ratings_only") is False:
        raise ValueError("P6 product quality review must be ratings-only")
    if _contains_key(data, _TEXT_PAYLOAD_KEYS | _COMMENT_TEXT_PAYLOAD_KEYS | _REVIEWER_FREE_TEXT_KEYS):
        raise ValueError("P6 product quality review must not include body or reviewer free text keys")
    if _flag_true(data, _FORBIDDEN_TRUE_FLAGS):
        raise ValueError("P6 product quality review contains forbidden true flags")
    public_contract = _safe_mapping(data.get("public_contract"))
    if public_contract and _flag_true(public_contract, _PUBLIC_CONTRACT_TRUE_FLAGS | _FIXED_TEMPLATE_TRUE_FLAGS):
        raise ValueError("P6 product quality review mutates public contract or adds templates")
    body_free = _safe_mapping(data.get("body_free"))
    if body_free and _flag_true(body_free, _FORBIDDEN_TRUE_FLAGS):
        raise ValueError("P6 product quality review includes body payload flags")
    summary = _safe_mapping(data.get("summary"))
    if summary:
        if not allow_partial and summary.get("schema_version") != STRUCTURE_INSIGHT_P6_PRODUCT_QUALITY_REVIEW_SUMMARY_SCHEMA_VERSION:
            raise ValueError("Unexpected P6 product quality review summary schema version")
        if _contains_key(summary, _TEXT_PAYLOAD_KEYS | _COMMENT_TEXT_PAYLOAD_KEYS | _REVIEWER_FREE_TEXT_KEYS):
            raise ValueError("P6 product quality review summary must not include body or reviewer free text keys")
        if _flag_true(summary, _FORBIDDEN_TRUE_FLAGS):
            raise ValueError("P6 product quality review summary contains forbidden true flags")
    return True


def dump_structure_insight_p6_product_quality_review_public_summary(report: Mapping[str, Any]) -> str:
    """Serialize only safe P6-8 Product QA summary fields."""

    data = _safe_mapping(report)
    assert_structure_insight_p6_product_quality_review_contract(data)
    summary = _safe_mapping(data.get("summary")) or data
    assert_structure_insight_p6_product_quality_review_contract(summary, allow_partial=True)
    safe_summary = {
        "schema_version": summary.get("schema_version"),
        "step": summary.get("step"),
        "run_id": summary.get("run_id"),
        "ratings_only": True,
        "review_count": summary.get("review_count"),
        "dimension_averages": _safe_mapping(summary.get("dimension_averages")),
        "verdict_counts": _safe_mapping(summary.get("verdict_counts")),
        "bucket_counts": _safe_mapping(summary.get("bucket_counts")),
        "structure_insight_ready_candidate_count": summary.get("structure_insight_ready_candidate_count"),
        "unsafe_candidate_count": summary.get("unsafe_candidate_count"),
        "weak_candidate_count": summary.get("weak_candidate_count"),
        "ready_candidate_count": summary.get("ready_candidate_count"),
        "p7_long_run_field_candidate_count": summary.get("p7_long_run_field_candidate_count"),
        "p7_long_run_field_candidates": list(summary.get("p7_long_run_field_candidates") or []),
        "blocker_reason_codes": list(summary.get("blocker_reason_codes") or []),
        "release_allowed": False,
        "public_contract": _safe_mapping(summary.get("public_contract")),
        "body_free": _safe_mapping(summary.get("body_free")),
    }
    assert_structure_insight_p6_product_quality_review_contract(safe_summary, allow_partial=True)
    return json.dumps(safe_summary, ensure_ascii=False, sort_keys=True)
