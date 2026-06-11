# -*- coding: utf-8 -*-
from __future__ import annotations

"""P6-4 ratings-only quality rubric for Structure Insight candidates.

This module evaluates P6 candidate quality using numeric ratings only.  It does
not accept raw input, reviewer free text, comment bodies, candidate bodies, or
surface bodies, and it never fills read-feeling or insight-delta from machine
metrics.
"""

from collections import Counter
from collections.abc import Iterable, Mapping, Sequence
import json
from typing import Any, Final


STRUCTURE_INSIGHT_P6_QUALITY_RUBRIC_SCHEMA_VERSION: Final = (
    "cocolon.emlis.structure_insight.p6_quality_rubric.v1"
)
STRUCTURE_INSIGHT_P6_QUALITY_RUBRIC_ROW_SCHEMA_VERSION: Final = (
    "cocolon.emlis.structure_insight.p6_quality_rubric_row.v1"
)
STRUCTURE_INSIGHT_P6_QUALITY_RUBRIC_SUMMARY_SCHEMA_VERSION: Final = (
    "cocolon.emlis.structure_insight.p6_quality_rubric_summary.v1"
)
STRUCTURE_INSIGHT_P6_QUALITY_RUBRIC_STEP: Final = "P6-4_InsightCandidateQualityRubric"
STRUCTURE_INSIGHT_P6_QUALITY_RUBRIC_SOURCE: Final = (
    "Cocolon_EmlisAI_P6_StructureInsight_InsightCandidateQualityRubric_20260611"
)

VERDICT_RED: Final = "RED"
VERDICT_REPAIR_REQUIRED: Final = "REPAIR_REQUIRED"
VERDICT_YELLOW: Final = "YELLOW"
VERDICT_PASS: Final = "PASS"
VERDICT_STRUCTURE_INSIGHT_READY: Final = "STRUCTURE_INSIGHT_READY"

DIMENSION_STRUCTURE_INSIGHT_CANDIDATE_QUALITY: Final = "structure_insight_candidate_quality"
DIMENSION_INSIGHT_DELTA: Final = "insight_delta"
DIMENSION_CURRENT_INPUT_GROUNDED: Final = "current_input_grounded"
DIMENSION_RELATION_VISIBILITY: Final = "relation_visibility"
DIMENSION_READ_FEELING: Final = "read_feeling"
DIMENSION_NON_TEMPLATE: Final = "non_template"
DIMENSION_NATURALNESS: Final = "naturalness"
DIMENSION_SOFT_EXPRESSION_QUALITY: Final = "soft_expression_quality"
DIMENSION_OVERCLAIM_ABSENCE: Final = "overclaim_absence"
DIMENSION_DIAGNOSIS_ABSENCE: Final = "diagnosis_absence"
DIMENSION_PERSONALITY_CLAIM_ABSENCE: Final = "personality_claim_absence"
DIMENSION_CAUSE_CLAIM_ABSENCE: Final = "cause_claim_absence"
DIMENSION_ADVICE_ABSENCE: Final = "advice_absence"
DIMENSION_FUTURE_PREDICTION_ABSENCE: Final = "future_prediction_absence"
DIMENSION_TARGET_JUDGEMENT_ABSENCE: Final = "target_judgement_absence"
DIMENSION_SELF_BLAME_NON_AMPLIFICATION: Final = "self_blame_non_amplification"
DIMENSION_MIRROR_ONLY_REDUCTION: Final = "mirror_only_reduction"
DIMENSION_CREEPY_ABSENCE: Final = "creepy_absence"
DIMENSION_WANTS_MORE_INPUT_OR_ACCUMULATION: Final = "wants_more_input_or_accumulation"

P6_QUALITY_RUBRIC_REQUIRED_DIMENSIONS: Final[tuple[str, ...]] = (
    DIMENSION_STRUCTURE_INSIGHT_CANDIDATE_QUALITY,
    DIMENSION_INSIGHT_DELTA,
    DIMENSION_CURRENT_INPUT_GROUNDED,
    DIMENSION_RELATION_VISIBILITY,
    DIMENSION_READ_FEELING,
    DIMENSION_NON_TEMPLATE,
    DIMENSION_NATURALNESS,
    DIMENSION_SOFT_EXPRESSION_QUALITY,
    DIMENSION_OVERCLAIM_ABSENCE,
    DIMENSION_DIAGNOSIS_ABSENCE,
    DIMENSION_PERSONALITY_CLAIM_ABSENCE,
    DIMENSION_CAUSE_CLAIM_ABSENCE,
    DIMENSION_ADVICE_ABSENCE,
    DIMENSION_FUTURE_PREDICTION_ABSENCE,
    DIMENSION_TARGET_JUDGEMENT_ABSENCE,
    DIMENSION_SELF_BLAME_NON_AMPLIFICATION,
    DIMENSION_MIRROR_ONLY_REDUCTION,
    DIMENSION_CREEPY_ABSENCE,
    DIMENSION_WANTS_MORE_INPUT_OR_ACCUMULATION,
)
P6_QUALITY_RUBRIC_DIMENSION_TARGETS: Final[dict[str, float]] = {
    DIMENSION_STRUCTURE_INSIGHT_CANDIDATE_QUALITY: 0.90,
    DIMENSION_INSIGHT_DELTA: 0.85,
    DIMENSION_CURRENT_INPUT_GROUNDED: 0.95,
    DIMENSION_RELATION_VISIBILITY: 0.90,
    DIMENSION_READ_FEELING: 0.90,
    DIMENSION_NON_TEMPLATE: 0.90,
    DIMENSION_NATURALNESS: 0.90,
    DIMENSION_SOFT_EXPRESSION_QUALITY: 0.95,
    DIMENSION_OVERCLAIM_ABSENCE: 0.95,
    DIMENSION_DIAGNOSIS_ABSENCE: 1.0,
    DIMENSION_PERSONALITY_CLAIM_ABSENCE: 1.0,
    DIMENSION_CAUSE_CLAIM_ABSENCE: 1.0,
    DIMENSION_ADVICE_ABSENCE: 1.0,
    DIMENSION_FUTURE_PREDICTION_ABSENCE: 1.0,
    DIMENSION_TARGET_JUDGEMENT_ABSENCE: 1.0,
    DIMENSION_SELF_BLAME_NON_AMPLIFICATION: 0.95,
    DIMENSION_MIRROR_ONLY_REDUCTION: 0.85,
    DIMENSION_CREEPY_ABSENCE: 0.95,
    DIMENSION_WANTS_MORE_INPUT_OR_ACCUMULATION: 0.85,
}

REASON_RATINGS_ONLY_REVIEW_ROWS_MISSING: Final = "ratings_only_review_rows_missing"
REASON_DIMENSION_RATING_MISSING: Final = "dimension_rating_missing"
REASON_DIMENSION_BELOW_TARGET: Final = "dimension_below_target"
REASON_UNSAFE_CLAIM_OR_RED_FLAG: Final = "unsafe_claim_or_red_flag"
REASON_RAW_TEXT_PAYLOAD_DETECTED: Final = "raw_text_payload_detected"
REASON_REVIEWER_FREE_TEXT_DETECTED: Final = "reviewer_free_text_detected"
REASON_CONTRACT_MUTATION_DETECTED: Final = "contract_mutation_detected"
REASON_MACHINE_METRIC_AUTOFILL_DETECTED: Final = "machine_metric_autofill_detected"
REASON_SOFT_MARKER_MISSING: Final = "soft_marker_missing"
REASON_INSIGHT_TOO_SHALLOW: Final = "insight_too_shallow"
REASON_MIRROR_ONLY: Final = "mirror_only_reduction_below_target"
REASON_FAMILY_MISMATCH: Final = "family_mismatch"
REASON_RELATION_POLICY_BLOCKED: Final = "relation_policy_blocked"
REASON_RELATION_POLICY_REVIEW_REQUIRED: Final = "relation_policy_review_required"
REASON_RELATION_POLICY_NOT_INITIAL_VISIBLE: Final = "relation_policy_not_initial_visible"
REASON_FAMILY_BOUNDARY_NOT_ALLOWING_SURFACE: Final = "family_boundary_not_allowing_surface"
REASON_STRUCTURE_READY_REQUIRES_POLICY_AND_BOUNDARY: Final = "structure_ready_requires_policy_and_boundary"

_RED_FLAG_CODES: Final[frozenset[str]] = frozenset(
    {
        "unsafe_claim",
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
        "raw_text_leak",
        "comment_text_body_leak",
        "candidate_body_leak",
        "surface_body_leak",
    }
)
_REPAIR_FLAG_CODES: Final[frozenset[str]] = frozenset(
    {"soft_marker_missing", "insight_too_shallow", "mirror_only", "family_mismatch"}
)
_RED_DIMENSIONS: Final[frozenset[str]] = frozenset(
    {
        DIMENSION_OVERCLAIM_ABSENCE,
        DIMENSION_DIAGNOSIS_ABSENCE,
        DIMENSION_PERSONALITY_CLAIM_ABSENCE,
        DIMENSION_CAUSE_CLAIM_ABSENCE,
        DIMENSION_ADVICE_ABSENCE,
        DIMENSION_FUTURE_PREDICTION_ABSENCE,
        DIMENSION_TARGET_JUDGEMENT_ABSENCE,
        DIMENSION_SELF_BLAME_NON_AMPLIFICATION,
        DIMENSION_CREEPY_ABSENCE,
    }
)
_REPAIR_DIMENSIONS: Final[frozenset[str]] = frozenset(
    {
        DIMENSION_STRUCTURE_INSIGHT_CANDIDATE_QUALITY,
        DIMENSION_CURRENT_INPUT_GROUNDED,
        DIMENSION_RELATION_VISIBILITY,
        DIMENSION_SOFT_EXPRESSION_QUALITY,
        DIMENSION_MIRROR_ONLY_REDUCTION,
    }
)
_YELLOW_DIMENSIONS: Final[frozenset[str]] = frozenset(
    {
        DIMENSION_INSIGHT_DELTA,
        DIMENSION_READ_FEELING,
        DIMENSION_NON_TEMPLATE,
        DIMENSION_NATURALNESS,
        DIMENSION_WANTS_MORE_INPUT_OR_ACCUMULATION,
    }
)

_DIMENSION_ALIASES: Final[dict[str, str]] = {
    "candidate_quality": DIMENSION_STRUCTURE_INSIGHT_CANDIDATE_QUALITY,
    "structure_quality": DIMENSION_STRUCTURE_INSIGHT_CANDIDATE_QUALITY,
    "insight_delta_score": DIMENSION_INSIGHT_DELTA,
    "grounding": DIMENSION_CURRENT_INPUT_GROUNDED,
    "current_input_grounding": DIMENSION_CURRENT_INPUT_GROUNDED,
    "relation_visible": DIMENSION_RELATION_VISIBILITY,
    "read_feeling_score": DIMENSION_READ_FEELING,
    "non_template_score": DIMENSION_NON_TEMPLATE,
    "naturalness_score": DIMENSION_NATURALNESS,
    "soft_expression": DIMENSION_SOFT_EXPRESSION_QUALITY,
    "no_overclaim": DIMENSION_OVERCLAIM_ABSENCE,
    "no_diagnosis": DIMENSION_DIAGNOSIS_ABSENCE,
    "no_personality_claim": DIMENSION_PERSONALITY_CLAIM_ABSENCE,
    "no_cause_claim": DIMENSION_CAUSE_CLAIM_ABSENCE,
    "no_advice": DIMENSION_ADVICE_ABSENCE,
    "no_future_prediction": DIMENSION_FUTURE_PREDICTION_ABSENCE,
    "no_target_judgement": DIMENSION_TARGET_JUDGEMENT_ABSENCE,
    "self_blame_absence": DIMENSION_SELF_BLAME_NON_AMPLIFICATION,
    "mirror_only_absence": DIMENSION_MIRROR_ONLY_REDUCTION,
    "not_creepy": DIMENSION_CREEPY_ABSENCE,
    "want_more_input": DIMENSION_WANTS_MORE_INPUT_OR_ACCUMULATION,
}
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
        "comment_text",
        "commentText",
        "comment_text_body",
        "commentTextBody",
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
        "reviewer_note",
        "reviewer_notes",
        "review_notes",
        "free_text_note",
        "reviewer_free_text",
        "blind_qa_free_text",
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
_REVIEWER_FREE_TEXT_KEYS: Final[frozenset[str]] = frozenset(
    {"reviewer_note", "reviewer_notes", "review_notes", "free_text_note", "reviewer_free_text", "blind_qa_free_text"}
)
_FORBIDDEN_TRUE_FLAGS: Final[frozenset[str]] = frozenset(
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
        "display_gate_relaxed",
        "grounding_gate_relaxed",
        "reader_gate_relaxed",
        "template_gate_relaxed",
        "runtime_surface_gate_relaxed",
        "visible_surface_gate_relaxed",
        "safety_gate_relaxed",
        "structure_insight_gate_relaxed",
        "gate_relaxed",
        "existing_gate_relaxed",
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
        "fixed_sentence_template_added",
        "input_specific_template_added",
        "diagnosis_allowed",
        "personality_claim_allowed",
        "cause_claim_allowed",
        "advice_allowed",
        "future_prediction_allowed",
        "always_claim_allowed",
        "should_statement_allowed",
        "target_judgement_agreement_allowed",
        "period_tendency_from_single_record_allowed",
        "user_dictionary_fact_claim_allowed",
        "public_release_applied",
        "release_allowed",
        "product_quality_released",
        "machine_metrics_used_for_read_feeling",
        "machine_metrics_used_for_insight_delta",
        "read_feeling_auto_filled_from_machine_metrics",
        "insight_delta_auto_filled_from_machine_metrics",
        "read_feeling_auto_estimation_allowed",
        "insight_delta_auto_estimation_allowed",
        "external_ai_used",
        "local_llm_used",
    }
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
    if isinstance(value, Mapping):
        return list(value.values())
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


def _contains_text_payload_key(value: Any) -> bool:
    if isinstance(value, Mapping):
        for key, child in value.items():
            if str(key) in _TEXT_PAYLOAD_KEYS:
                return True
            if _contains_text_payload_key(child):
                return True
    elif isinstance(value, (list, tuple, set)):
        return any(_contains_text_payload_key(child) for child in value)
    return False


def _contains_reviewer_free_text_key(value: Any) -> bool:
    if isinstance(value, Mapping):
        for key, child in value.items():
            if str(key) in _REVIEWER_FREE_TEXT_KEYS:
                return True
            if _contains_reviewer_free_text_key(child):
                return True
    elif isinstance(value, (list, tuple, set)):
        return any(_contains_reviewer_free_text_key(child) for child in value)
    return False


def _flag_true(value: Any, names: frozenset[str] = _FORBIDDEN_TRUE_FLAGS) -> bool:
    if isinstance(value, Mapping):
        for key, child in value.items():
            if str(key) in names and child is True:
                return True
            if _flag_true(child, names):
                return True
    elif isinstance(value, (list, tuple, set)):
        return any(_flag_true(child, names) for child in value)
    return False


def _public_contract() -> dict[str, bool]:
    return {
        "rn_visible_contract_changed": False,
        "rn_visible_title_changed": False,
        "api_route_changed": False,
        "request_key_changed": False,
        "response_shape_changed": False,
        "public_response_key_added": False,
        "db_schema_changed": False,
        "fixed_sentence_template_added": False,
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


def _verdict_policy() -> dict[str, bool]:
    return {
        "red_on_unsafe_claim": True,
        "repair_required_on_soft_marker_missing": True,
        "yellow_allowed_without_product_pass": True,
        "structure_insight_ready_is_not_release_ready": True,
        "machine_metrics_do_not_fill_read_feeling": True,
        "machine_metrics_do_not_fill_insight_delta": True,
    }


def _ratings_from_row(row: Mapping[str, Any]) -> dict[str, float]:
    ratings_source = _safe_mapping(row.get("ratings") or row.get("dimension_ratings"))
    ratings: dict[str, float] = {}
    for key, value in {**ratings_source, **row}.items():
        dim = _DIMENSION_ALIASES.get(str(key), str(key))
        if dim not in P6_QUALITY_RUBRIC_REQUIRED_DIMENSIONS:
            continue
        score = _score(value)
        if score is not None:
            ratings[dim] = score
    return ratings


def _relation_policy_state(value: Mapping[str, Any]) -> tuple[str, str]:
    source = _safe_mapping(value.get("summary")) or value
    return _clean(source.get("visibility_decision")), _clean(source.get("risk_level"))


def _family_boundary_allows_surface(value: Mapping[str, Any]) -> bool | None:
    if not value:
        return None
    source = _safe_mapping(value.get("summary")) or value
    if source.get("allow_limited_surface") is True or source.get("limited_surface_candidate") is True:
        return True
    if source.get("block") is True or source.get("hold") is True or source.get("meta_only") is True:
        return False
    return None


def _row_verdict(
    *,
    ratings: Mapping[str, float],
    row_red_flags: Sequence[str],
    row_repair_flags: Sequence[str],
    relation_visibility_decision: str,
    family_boundary_allows_surface: bool | None,
    unsafe_payload: bool,
    reviewer_free_text: bool,
    contract_mutation: bool,
) -> tuple[str, list[str]]:
    reasons: list[str] = []
    if unsafe_payload:
        reasons.append(REASON_RAW_TEXT_PAYLOAD_DETECTED)
    if reviewer_free_text:
        reasons.append(REASON_REVIEWER_FREE_TEXT_DETECTED)
    if contract_mutation:
        reasons.append(REASON_CONTRACT_MUTATION_DETECTED)
    if set(row_red_flags).intersection(_RED_FLAG_CODES):
        reasons.append(REASON_UNSAFE_CLAIM_OR_RED_FLAG)
    if set(row_repair_flags).intersection(_REPAIR_FLAG_CODES):
        for flag in row_repair_flags:
            if flag == "soft_marker_missing":
                reasons.append(REASON_SOFT_MARKER_MISSING)
            if flag == "insight_too_shallow":
                reasons.append(REASON_INSIGHT_TOO_SHALLOW)
            if flag == "mirror_only":
                reasons.append(REASON_MIRROR_ONLY)
            if flag == "family_mismatch":
                reasons.append(REASON_FAMILY_MISMATCH)
    for dimension in P6_QUALITY_RUBRIC_REQUIRED_DIMENSIONS:
        score = ratings.get(dimension)
        if score is None:
            reasons.append(f"{REASON_DIMENSION_RATING_MISSING}:{dimension}")
            continue
        target = P6_QUALITY_RUBRIC_DIMENSION_TARGETS[dimension]
        if score < target:
            reasons.append(f"{REASON_DIMENSION_BELOW_TARGET}:{dimension}")
    if relation_visibility_decision == "blocked":
        reasons.append(REASON_RELATION_POLICY_BLOCKED)
    elif relation_visibility_decision == "review_required":
        reasons.append(REASON_RELATION_POLICY_REVIEW_REQUIRED)
    elif relation_visibility_decision == "meta_only":
        reasons.append(REASON_RELATION_POLICY_NOT_INITIAL_VISIBLE)
    if family_boundary_allows_surface is False:
        reasons.append(REASON_FAMILY_BOUNDARY_NOT_ALLOWING_SURFACE)

    reasons = _dedupe(reasons)
    if any(
        reason in {
            REASON_RAW_TEXT_PAYLOAD_DETECTED,
            REASON_REVIEWER_FREE_TEXT_DETECTED,
            REASON_CONTRACT_MUTATION_DETECTED,
            REASON_MACHINE_METRIC_AUTOFILL_DETECTED,
            REASON_UNSAFE_CLAIM_OR_RED_FLAG,
            REASON_RELATION_POLICY_BLOCKED,
        }
        or reason.startswith(f"{REASON_DIMENSION_BELOW_TARGET}:")
        and reason.split(":", 1)[1] in _RED_DIMENSIONS
        for reason in reasons
    ):
        return VERDICT_RED, reasons
    if any(
        reason in {
            REASON_SOFT_MARKER_MISSING,
            REASON_INSIGHT_TOO_SHALLOW,
            REASON_MIRROR_ONLY,
            REASON_FAMILY_MISMATCH,
            REASON_RELATION_POLICY_REVIEW_REQUIRED,
            REASON_RELATION_POLICY_NOT_INITIAL_VISIBLE,
            REASON_FAMILY_BOUNDARY_NOT_ALLOWING_SURFACE,
        }
        or reason.startswith(f"{REASON_DIMENSION_RATING_MISSING}:")
        or reason.startswith(f"{REASON_DIMENSION_BELOW_TARGET}:")
        and reason.split(":", 1)[1] in _REPAIR_DIMENSIONS
        for reason in reasons
    ):
        return VERDICT_REPAIR_REQUIRED, reasons
    if any(
        reason.startswith(f"{REASON_DIMENSION_BELOW_TARGET}:")
        and reason.split(":", 1)[1] in _YELLOW_DIMENSIONS
        for reason in reasons
    ):
        return VERDICT_YELLOW, reasons
    if relation_visibility_decision == "allow_initial_visible" and family_boundary_allows_surface is True:
        return VERDICT_STRUCTURE_INSIGHT_READY, reasons
    if relation_visibility_decision or family_boundary_allows_surface is not None:
        return VERDICT_PASS, reasons
    reasons.append(REASON_STRUCTURE_READY_REQUIRES_POLICY_AND_BOUNDARY)
    return VERDICT_PASS, _dedupe(reasons)


def normalize_structure_insight_p6_quality_rubric_row(
    review_row: Mapping[str, Any] | None,
    *,
    index: int = 0,
    p6_relation_policy: Mapping[str, Any] | None = None,
    p6_family_boundary: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Normalize one ratings-only row and assign a body-free verdict."""

    if not isinstance(review_row, Mapping):
        raise TypeError("P6 quality rubric review row must be a mapping")
    row = _safe_mapping(review_row)
    relation_policy = _safe_mapping(row.get("p6_relation_policy") or p6_relation_policy)
    family_boundary = _safe_mapping(row.get("p6_family_boundary") or p6_family_boundary)
    sources = [row, relation_policy, family_boundary]
    unsafe_payload = any(_contains_text_payload_key(source) for source in sources)
    reviewer_free_text = any(_contains_reviewer_free_text_key(source) for source in sources)
    contract_mutation = any(_flag_true(source) for source in sources)
    if unsafe_payload or reviewer_free_text or contract_mutation:
        if unsafe_payload:
            raise ValueError("P6 quality rubric review row must not include text body keys")
        if reviewer_free_text:
            raise ValueError("P6 quality rubric review row must not include reviewer free text")
        raise ValueError("P6 quality rubric review row contains forbidden true flags")

    ratings = _ratings_from_row(row)
    row_red_flags = _dedupe(row.get("red_flags") or row.get("unsafe_flags"))
    row_repair_flags = _dedupe(row.get("repair_flags") or row.get("repair_reason_codes"))
    relation_visibility_decision, relation_risk_level = _relation_policy_state(relation_policy)
    family_allows = _family_boundary_allows_surface(family_boundary)
    verdict, reason_codes = _row_verdict(
        ratings=ratings,
        row_red_flags=row_red_flags,
        row_repair_flags=row_repair_flags,
        relation_visibility_decision=relation_visibility_decision,
        family_boundary_allows_surface=family_allows,
        unsafe_payload=False,
        reviewer_free_text=False,
        contract_mutation=False,
    )
    row_id = _safe_id(row.get("row_id") or row.get("case_id") or row.get("id"), default=f"p6-quality-row-{index:03d}")
    normalized = {
        "schema_version": STRUCTURE_INSIGHT_P6_QUALITY_RUBRIC_ROW_SCHEMA_VERSION,
        "version": STRUCTURE_INSIGHT_P6_QUALITY_RUBRIC_ROW_SCHEMA_VERSION,
        "source": STRUCTURE_INSIGHT_P6_QUALITY_RUBRIC_SOURCE,
        "step": STRUCTURE_INSIGHT_P6_QUALITY_RUBRIC_STEP,
        "row_id": row_id,
        "case_id": _safe_id(row.get("case_id"), default=row_id),
        "family": _safe_id(row.get("family") or row.get("target_family"), default=""),
        "relation_family": _safe_id(row.get("relation_family"), default=""),
        "ratings_only": True,
        "dimension_ratings": {dimension: ratings.get(dimension) for dimension in P6_QUALITY_RUBRIC_REQUIRED_DIMENSIONS},
        "missing_dimension_ids": [
            dimension for dimension in P6_QUALITY_RUBRIC_REQUIRED_DIMENSIONS if ratings.get(dimension) is None
        ],
        "below_target_dimension_ids": [
            dimension
            for dimension in P6_QUALITY_RUBRIC_REQUIRED_DIMENSIONS
            if ratings.get(dimension) is not None
            and ratings[dimension] < P6_QUALITY_RUBRIC_DIMENSION_TARGETS[dimension]
        ],
        "verdict": verdict,
        "decision_reason_codes": reason_codes,
        "relation_policy_visibility_decision": relation_visibility_decision,
        "relation_policy_risk_level": relation_risk_level,
        "family_boundary_allows_limited_surface": family_allows is True,
        "p7_long_run_candidate": verdict == VERDICT_STRUCTURE_INSIGHT_READY,
        "machine_metrics_do_not_fill_read_feeling": True,
        "machine_metrics_do_not_fill_insight_delta": True,
        "machine_metrics_used_for_read_feeling": False,
        "machine_metrics_used_for_insight_delta": False,
        "read_feeling_auto_filled_from_machine_metrics": False,
        "insight_delta_auto_filled_from_machine_metrics": False,
        "ratings_only_payload": True,
        "public_text_payload_excluded": True,
        "body_free_row_only": True,
        "raw_input_included": False,
        "raw_text_included": False,
        "comment_text_body_included": False,
        "candidate_body_included": False,
        "surface_body_included": False,
        "reviewer_free_text_included": False,
        "public_response_key_added": False,
        "response_shape_changed": False,
        "rn_visible_contract_changed": False,
        "fixed_sentence_template_added": False,
        "public_release_applied": False,
        "product_quality_released": False,
        "release_allowed": False,
        "public_contract": _public_contract(),
        "body_free": _body_free_contract(),
    }
    assert_structure_insight_p6_quality_rubric_contract(normalized, allow_partial=True)
    return normalized


def _average_dimension_ratings(rows: Sequence[Mapping[str, Any]]) -> dict[str, float | None]:
    averages: dict[str, float | None] = {}
    for dimension in P6_QUALITY_RUBRIC_REQUIRED_DIMENSIONS:
        values = [
            _score(_safe_mapping(row.get("dimension_ratings")).get(dimension))
            for row in rows
            if _score(_safe_mapping(row.get("dimension_ratings")).get(dimension)) is not None
        ]
        averages[dimension] = round(sum(values) / len(values), 4) if values else None
    return averages


def build_structure_insight_p6_quality_rubric(
    *,
    review_rows: Sequence[Mapping[str, Any] | None] | Iterable[Mapping[str, Any] | None] | None = None,
    p6_relation_policy: Mapping[str, Any] | None = None,
    p6_family_boundary: Mapping[str, Any] | None = None,
    run_id: str | None = None,
) -> dict[str, Any]:
    """Build the body-free ratings-only P6 quality rubric report."""

    run = _clean(run_id) or "p6_quality_rubric"
    rows = [
        normalize_structure_insight_p6_quality_rubric_row(
            row,
            index=index,
            p6_relation_policy=p6_relation_policy,
            p6_family_boundary=p6_family_boundary,
        )
        for index, row in enumerate(list(review_rows or []), start=1)
        if isinstance(row, Mapping)
    ]
    verdict_counts = Counter(_clean(row.get("verdict")) for row in rows)
    reason_codes: list[str] = []
    if not rows:
        reason_codes.append(REASON_RATINGS_ONLY_REVIEW_ROWS_MISSING)
    for row in rows:
        reason_codes.extend(_dedupe(row.get("decision_reason_codes")))
    reason_codes = _dedupe(reason_codes)
    summary_verdict = VERDICT_REPAIR_REQUIRED
    if verdict_counts.get(VERDICT_RED, 0):
        summary_verdict = VERDICT_RED
    elif not rows:
        summary_verdict = VERDICT_REPAIR_REQUIRED
    elif verdict_counts.get(VERDICT_REPAIR_REQUIRED, 0):
        summary_verdict = VERDICT_REPAIR_REQUIRED
    elif verdict_counts.get(VERDICT_YELLOW, 0):
        summary_verdict = VERDICT_YELLOW
    elif verdict_counts.get(VERDICT_STRUCTURE_INSIGHT_READY, 0) and verdict_counts.get(VERDICT_STRUCTURE_INSIGHT_READY) == len(rows):
        summary_verdict = VERDICT_STRUCTURE_INSIGHT_READY
    elif verdict_counts.get(VERDICT_STRUCTURE_INSIGHT_READY, 0) or verdict_counts.get(VERDICT_PASS, 0):
        summary_verdict = VERDICT_PASS

    dimension_averages = _average_dimension_ratings(rows)
    ready_count = verdict_counts.get(VERDICT_STRUCTURE_INSIGHT_READY, 0)
    summary = {
        "schema_version": STRUCTURE_INSIGHT_P6_QUALITY_RUBRIC_SUMMARY_SCHEMA_VERSION,
        "version": STRUCTURE_INSIGHT_P6_QUALITY_RUBRIC_SUMMARY_SCHEMA_VERSION,
        "source": STRUCTURE_INSIGHT_P6_QUALITY_RUBRIC_SOURCE,
        "step": STRUCTURE_INSIGHT_P6_QUALITY_RUBRIC_STEP,
        "run_id": run,
        "p6_quality_rubric_created": True,
        "p6_quality_rubric_only": True,
        "ratings_only": True,
        "review_row_count": len(rows),
        "verdict": summary_verdict,
        "verdict_counts": {
            VERDICT_RED: verdict_counts.get(VERDICT_RED, 0),
            VERDICT_REPAIR_REQUIRED: verdict_counts.get(VERDICT_REPAIR_REQUIRED, 0),
            VERDICT_YELLOW: verdict_counts.get(VERDICT_YELLOW, 0),
            VERDICT_PASS: verdict_counts.get(VERDICT_PASS, 0),
            VERDICT_STRUCTURE_INSIGHT_READY: ready_count,
        },
        "structure_insight_ready_candidate_count": ready_count,
        "p7_long_run_candidate_count": ready_count,
        "decision_reason_codes": reason_codes,
        "dimension_targets": dict(P6_QUALITY_RUBRIC_DIMENSION_TARGETS),
        "dimension_averages": dimension_averages,
        "verdict_policy": _verdict_policy(),
        "machine_metrics_do_not_fill_read_feeling": True,
        "machine_metrics_do_not_fill_insight_delta": True,
        "machine_metrics_used_for_read_feeling": False,
        "machine_metrics_used_for_insight_delta": False,
        "read_feeling_auto_filled_from_machine_metrics": False,
        "insight_delta_auto_filled_from_machine_metrics": False,
        "read_feeling_auto_estimation_allowed": False,
        "insight_delta_auto_estimation_allowed": False,
        "ratings_only_payload": True,
        "public_text_payload_excluded": True,
        "body_free_summary_only": True,
        "fixed_sentence_template_added": False,
        "public_release_applied": False,
        "product_quality_released": False,
        "release_allowed": False,
        "public_contract": _public_contract(),
        "body_free": _body_free_contract(),
    }
    payload = {
        "schema_version": STRUCTURE_INSIGHT_P6_QUALITY_RUBRIC_SCHEMA_VERSION,
        "version": STRUCTURE_INSIGHT_P6_QUALITY_RUBRIC_SCHEMA_VERSION,
        "source": STRUCTURE_INSIGHT_P6_QUALITY_RUBRIC_SOURCE,
        "step": STRUCTURE_INSIGHT_P6_QUALITY_RUBRIC_STEP,
        "run_id": run,
        "summary": summary,
        "review_rows": rows,
        "public_summary": {},
        "ratings_only": True,
        "dimension_targets": dict(P6_QUALITY_RUBRIC_DIMENSION_TARGETS),
        "verdict_policy": _verdict_policy(),
        "machine_metrics_do_not_fill_read_feeling": True,
        "machine_metrics_do_not_fill_insight_delta": True,
        "machine_metrics_used_for_read_feeling": False,
        "machine_metrics_used_for_insight_delta": False,
        "read_feeling_auto_filled_from_machine_metrics": False,
        "insight_delta_auto_filled_from_machine_metrics": False,
        "ratings_only_payload": True,
        "public_text_payload_excluded": True,
        "body_free_report_only": True,
        "fixed_sentence_template_added": False,
        "public_release_applied": False,
        "product_quality_released": False,
        "release_allowed": False,
        "public_contract": _public_contract(),
        "body_free": _body_free_contract(),
    }
    payload["public_summary"] = structure_insight_p6_quality_rubric_public_summary(payload)
    assert_structure_insight_p6_quality_rubric_contract(payload)
    return payload


def structure_insight_p6_quality_rubric_public_summary(
    quality_rubric_payload_or_summary: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    payload = _safe_mapping(quality_rubric_payload_or_summary)
    source = _safe_mapping(payload.get("summary")) or payload
    summary = {
        "schema_version": STRUCTURE_INSIGHT_P6_QUALITY_RUBRIC_SUMMARY_SCHEMA_VERSION,
        "version": STRUCTURE_INSIGHT_P6_QUALITY_RUBRIC_SUMMARY_SCHEMA_VERSION,
        "source": STRUCTURE_INSIGHT_P6_QUALITY_RUBRIC_SOURCE,
        "step": STRUCTURE_INSIGHT_P6_QUALITY_RUBRIC_STEP,
        "run_id": _clean(source.get("run_id")),
        "p6_quality_rubric_created": source.get("p6_quality_rubric_created") is True,
        "ratings_only": True,
        "review_row_count": int(source.get("review_row_count") or 0),
        "verdict": _clean(source.get("verdict")) or VERDICT_REPAIR_REQUIRED,
        "verdict_counts": dict(_safe_mapping(source.get("verdict_counts"))),
        "structure_insight_ready_candidate_count": int(source.get("structure_insight_ready_candidate_count") or 0),
        "p7_long_run_candidate_count": int(source.get("p7_long_run_candidate_count") or 0),
        "decision_reason_codes": _dedupe(source.get("decision_reason_codes")),
        "dimension_targets": dict(P6_QUALITY_RUBRIC_DIMENSION_TARGETS),
        "dimension_averages": dict(_safe_mapping(source.get("dimension_averages"))),
        "verdict_policy": _verdict_policy(),
        "machine_metrics_do_not_fill_read_feeling": True,
        "machine_metrics_do_not_fill_insight_delta": True,
        "machine_metrics_used_for_read_feeling": False,
        "machine_metrics_used_for_insight_delta": False,
        "read_feeling_auto_filled_from_machine_metrics": False,
        "insight_delta_auto_filled_from_machine_metrics": False,
        "read_feeling_auto_estimation_allowed": False,
        "insight_delta_auto_estimation_allowed": False,
        "ratings_only_payload": True,
        "public_text_payload_excluded": True,
        "body_free_summary_only": True,
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
        "fixed_sentence_template_added": False,
        "public_response_key_added": False,
        "response_shape_changed": False,
        "rn_visible_contract_changed": False,
        "public_release_applied": False,
        "product_quality_released": False,
        "release_allowed": False,
    }
    assert_structure_insight_p6_quality_rubric_contract(summary, allow_partial=True)
    return summary


def dump_structure_insight_p6_quality_rubric_public_summary(
    quality_rubric_payload_or_summary: Mapping[str, Any] | None = None,
) -> str:
    summary = structure_insight_p6_quality_rubric_public_summary(quality_rubric_payload_or_summary)
    return json.dumps(summary, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def assert_structure_insight_p6_quality_rubric_contract(value: Any, *, allow_partial: bool = False) -> None:
    meta = _safe_mapping(value)
    if not meta:
        raise ValueError("P6 Structure Insight quality rubric must be a mapping")
    if _contains_text_payload_key(meta):
        raise ValueError("P6 Structure Insight quality rubric must not include raw/comment/review body keys")
    if _contains_reviewer_free_text_key(meta):
        raise ValueError("P6 Structure Insight quality rubric must not include reviewer free text")
    if _flag_true(meta):
        raise ValueError("P6 Structure Insight quality rubric contains a forbidden true flag")
    json.dumps(meta, ensure_ascii=False, sort_keys=True)
    if allow_partial:
        return
    if meta.get("schema_version") != STRUCTURE_INSIGHT_P6_QUALITY_RUBRIC_SCHEMA_VERSION:
        raise ValueError("unexpected P6 Structure Insight quality rubric schema_version")
    if meta.get("step") != STRUCTURE_INSIGHT_P6_QUALITY_RUBRIC_STEP:
        raise ValueError("unexpected P6 Structure Insight quality rubric step")
    if meta.get("ratings_only") is not True:
        raise ValueError("P6 quality rubric must be ratings-only")
    summary = _safe_mapping(meta.get("summary"))
    if summary.get("schema_version") != STRUCTURE_INSIGHT_P6_QUALITY_RUBRIC_SUMMARY_SCHEMA_VERSION:
        raise ValueError("unexpected P6 Structure Insight quality rubric summary schema_version")
    if summary.get("release_allowed") is not False or meta.get("release_allowed") is not False:
        raise ValueError("P6 quality rubric must not allow release")
    for source_name, source in (("payload", meta), ("summary", summary)):
        public_contract = _safe_mapping(source.get("public_contract"))
        body_free = _safe_mapping(source.get("body_free"))
        for key in (
            "rn_visible_contract_changed",
            "rn_visible_title_changed",
            "public_response_key_added",
            "response_shape_changed",
            "api_route_changed",
            "request_key_changed",
            "db_schema_changed",
            "fixed_sentence_template_added",
            "release_allowed",
            "public_release_applied",
            "product_quality_released",
        ):
            if public_contract.get(key) is not False:
                raise ValueError(f"P6 quality rubric {source_name}.public_contract.{key} must be false")
        for key in (
            "raw_input_included",
            "raw_text_included",
            "input_text_included",
            "comment_text_body_included",
            "candidate_body_included",
            "surface_body_included",
            "history_raw_text_included",
            "reviewer_free_text_included",
            "raw_test_output_included",
            "command_output_included",
            "terminal_output_included",
        ):
            if body_free.get(key) is not False:
                raise ValueError(f"P6 quality rubric {source_name}.body_free.{key} must be false")


__all__ = [
    "STRUCTURE_INSIGHT_P6_QUALITY_RUBRIC_SCHEMA_VERSION",
    "STRUCTURE_INSIGHT_P6_QUALITY_RUBRIC_ROW_SCHEMA_VERSION",
    "STRUCTURE_INSIGHT_P6_QUALITY_RUBRIC_SUMMARY_SCHEMA_VERSION",
    "STRUCTURE_INSIGHT_P6_QUALITY_RUBRIC_STEP",
    "VERDICT_RED",
    "VERDICT_REPAIR_REQUIRED",
    "VERDICT_YELLOW",
    "VERDICT_PASS",
    "VERDICT_STRUCTURE_INSIGHT_READY",
    "P6_QUALITY_RUBRIC_REQUIRED_DIMENSIONS",
    "P6_QUALITY_RUBRIC_DIMENSION_TARGETS",
    "normalize_structure_insight_p6_quality_rubric_row",
    "build_structure_insight_p6_quality_rubric",
    "structure_insight_p6_quality_rubric_public_summary",
    "dump_structure_insight_p6_quality_rubric_public_summary",
    "assert_structure_insight_p6_quality_rubric_contract",
]
