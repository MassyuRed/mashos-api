# -*- coding: utf-8 -*-
from __future__ import annotations

"""Phase 1 current-output inventory for EmlisAI Product Read Feel.

The Phase 1 inventory is a meta-only bridge from existing fixture/runtime
scorecard events and ratings-only Blind QA reviews to the Product Read Feel
rubric.  It deliberately does not keep raw user input or public
``comment_text`` bodies.  Display bodies may be inspected by callers before
normalization, but this module keeps only family, verdict, failure buckets, and
safe structural markers needed for the棚卸し.
"""

from collections import Counter
from collections.abc import Iterable, Mapping, Sequence
import json
import re
from typing import Any, Final

from emlis_ai_mirror_only_surface_detector import (
    detect_mirror_only_surface,
    normalize_mirror_only_surface_to_scorecard_event,
)

PRODUCT_READFEEL_CURRENT_OUTPUT_INVENTORY_VERSION: Final = (
    "cocolon.emlis.product_readfeel.current_output_inventory.v1"
)
PRODUCT_READFEEL_CURRENT_OUTPUT_INVENTORY_STEP: Final = "Phase1_Current_Output_Inventory"
PRODUCT_READFEEL_CURRENT_OUTPUT_INVENTORY_SOURCE: Final = (
    "Cocolon_EmlisAI_ProductReadFeel_Phase1_CurrentOutputInventory"
)
PRODUCT_READFEEL_REVIEW_VERSION: Final = "cocolon.emlis.product_readfeel.phase1.review.v1"
PRODUCT_READFEEL_ITEM_VERSION: Final = "cocolon.emlis.product_readfeel.phase1.item.v1"
PRODUCT_READFEEL_FAMILY_SUMMARY_VERSION: Final = "cocolon.emlis.product_readfeel.phase1.family_summary.v1"

VERDICT_RED: Final = "RED"
VERDICT_REPAIR_REQUIRED: Final = "REPAIR_REQUIRED"
VERDICT_YELLOW: Final = "YELLOW"
VERDICT_PASS: Final = "PASS"
VERDICT_NOT_EVALUATED: Final = "NOT_EVALUATED"

FAILURE_DISPLAY_NOT_REACHED: Final = "display_not_reached"
FAILURE_CONTRACT_VIOLATION: Final = "contract_violation"
FAILURE_SURFACE_BREAKAGE: Final = "surface_breakage"
FAILURE_READFEEL_GAP: Final = "readfeel_gap"
FAILURE_STRUCTURE_INSIGHT_GAP: Final = "structure_insight_gap"

FAMILY_LOW_INFORMATION_SHORT: Final = "low_information_short"
FAMILY_DAILY_UNPLEASANT: Final = "daily_unpleasant"
FAMILY_DAILY_POSITIVE: Final = "daily_positive"
FAMILY_SELF_DENIAL: Final = "self_denial"
FAMILY_UNCERTAINTY: Final = "uncertainty"
FAMILY_MIXED_EMOTION: Final = "mixed_emotion"
FAMILY_LONG_MEANING_ARC: Final = "long_meaning_arc"
FAMILY_RELATIONSHIP_BOUNDARY: Final = "relationship_boundary"
FAMILY_STRUCTURE_QUESTION: Final = "structure_question"
FAMILY_POSITIVE_ONLY: Final = "positive_only"
FAMILY_SELF_UNDERSTANDING_FOLLOW: Final = "self_understanding_follow"
FAMILY_INPUT_SELF_REPORT_ONLY_FAILURE: Final = "input_self_report_only_failure"
FAMILY_UNCLASSIFIED: Final = "unclassified"

PRODUCT_READFEEL_REQUIRED_FAMILIES: Final[tuple[str, ...]] = (
    FAMILY_LOW_INFORMATION_SHORT,
    FAMILY_DAILY_UNPLEASANT,
    FAMILY_DAILY_POSITIVE,
    FAMILY_SELF_DENIAL,
    FAMILY_UNCERTAINTY,
    FAMILY_MIXED_EMOTION,
    FAMILY_LONG_MEANING_ARC,
    FAMILY_RELATIONSHIP_BOUNDARY,
    FAMILY_STRUCTURE_QUESTION,
    FAMILY_POSITIVE_ONLY,
    FAMILY_SELF_UNDERSTANDING_FOLLOW,
    FAMILY_INPUT_SELF_REPORT_ONLY_FAILURE,
)

_VERDICT_ORDER: Final[dict[str, int]] = {
    VERDICT_PASS: 0,
    VERDICT_NOT_EVALUATED: 1,
    VERDICT_YELLOW: 2,
    VERDICT_REPAIR_REQUIRED: 3,
    VERDICT_RED: 4,
}

_SPACE_RE: Final = re.compile(r"\s+")

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
        "memo",
        "memo_text",
        "memoText",
        "memo_action",
        "memoAction",
        "current_input",
        "currentInput",
        "comment_text",
        "commentText",
        "input_feedback_comment",
        "inputFeedbackComment",
        "public_comment_text",
        "candidate_comment_text",
        "reply_text",
        "replyText",
        "surface_text",
        "surfaceText",
        "accepted_surface_probe",
        "blocked_surface_probe",
        "realized_text",
        "display_text",
        "body",
        "text",
    }
)

_FORBIDDEN_TRUE_FLAGS: Final[tuple[str, ...]] = (
    "raw_input_included",
    "raw_text_included",
    "comment_text_included",
    "comment_text_body_included",
    "display_gate_relaxed",
    "grounding_gate_relaxed",
    "reader_gate_relaxed",
    "template_gate_relaxed",
    "gate_relaxed",
    "public_status_extended",
    "observation_status_enum_extended",
    "response_shape_changed",
    "public_response_key_change",
    "api_route_changed",
    "db_physical_name_changed",
    "rn_visible_contract_changed",
    "rn_visible_title_changed",
    "product_gate_public_release_applied",
    "public_release_applied",
    "product_quality_released",
    "fixed_sentence_template_used",
    "fixed_completed_sentence_template_added",
    "input_specific_template_added",
    "external_ai_used",
    "local_llm_used",
)

_CONTRACT_REASON_MARKERS: Final[tuple[str, ...]] = (
    "contract",
    "public_response_key",
    "response_key",
    "api_route",
    "db_physical",
    "rn_visible",
    "rn_title",
    "gate_relaxed",
    "raw_text_public_leak",
    "raw_input_public_leak",
    "comment_text_public_leak",
)
_SURFACE_REASON_MARKERS: Final[tuple[str, ...]] = (
    "diagnosis",
    "diagnostic",
    "personality",
    "personality_claim",
    "target_judgement_agreement",
    "other_person_intent_claim",
    "self_denial_identity_claim_risk",
    "relationship_target_judgement_risk",
    "cause_claim_without_evidence",
    "action_instruction",
    "advice",
    "malformed",
    "bad_grammar",
    "koto_splice",
    "nominalization",
    "label_order",
    "section_order",
    "section_mixed",
    "role_fixed",
    "internal_role",
    "fixed_fallback",
    "fixed_template",
    "template_major",
    "surface_template_major",
    "skeleton_repeat",
    "surface_signature_repeat",
    "raw_echo",
    "over_echo",
    "grammar_warning",
)
_READFEEL_REASON_MARKERS: Final[tuple[str, ...]] = (
    "read_feeling",
    "readfeel",
    "rich_input_low_information_overroute",
    "family_temperature_flattened",
    "input_core_missing",
    "event_reaction_missing",
    "desire_fear_conflict_missing",
    "state_structure_missing",
    "positive_overweighted",
    "positive_underreceived",
    "structure_question_answered_as_comfort",
    "generic_reception_surface",
    "repeated_surface_signature",
    "history_line_masks_current_input_gap",
    "limited_grounding_collapsed_to_question",
    "generic_comfort",
    "generic_follow",
    "follow_depth",
    "follow_shallow",
    "weak_follow",
    "input_specificity_weak",
    "evidence_retention",
    "self_report_retention",
    "state_structure_retention",
    "emotion_temperature_retention",
    "selected_emotion_missing",
    "memo_action_missing",
    "important_slot_missing",
    "category_as_cause",
    "low_information_question_escape",
    "daily_reception_question_escape",
    "mixed_emotion_flattened",
    "positive_too_heavy",
    "positive_heavy",
    "positive_only_heavy",
    "long_input_crushed",
    "too_short_for_long_input",
    "template_feel",
    "natural_but_generic",
)
_STRUCTURE_REASON_MARKERS: Final[tuple[str, ...]] = (
    "mirror_only",
    "mirror-only",
    "self_report_only",
    "input_self_report_only",
    "summary_only",
    "rephrase_only",
    "recap_only",
    "insight_delta",
    "insight_missing",
    "structure_insight",
    "structure_relation_missing",
    "relation_missing",
    "full_summary_only",
    "input_material_relation_missing",
)
_SAFETY_OR_INFRA_MARKERS: Final[tuple[str, ...]] = (
    "safety",
    "self_harm",
    "harm",
    "policy_blocked",
    "infra",
    "infrastructure",
    "timeout",
    "server_error",
    "exception",
    "network_error",
    "system_error",
)

_FAMILY_ALIASES: Final[dict[str, str]] = {
    "low_information": FAMILY_LOW_INFORMATION_SHORT,
    "low_information_short": FAMILY_LOW_INFORMATION_SHORT,
    "short_low_information": FAMILY_LOW_INFORMATION_SHORT,
    "long_low_information": FAMILY_LOW_INFORMATION_SHORT,
    "low_info": FAMILY_LOW_INFORMATION_SHORT,
    "daily_unpleasant": FAMILY_DAILY_UNPLEASANT,
    "daily_unpleasant_reception": FAMILY_DAILY_UNPLEASANT,
    "anger_hurt": FAMILY_DAILY_UNPLEASANT,
    "daily_positive": FAMILY_DAILY_POSITIVE,
    "daily_positive_reception": FAMILY_DAILY_POSITIVE,
    "recovery": FAMILY_DAILY_POSITIVE,
    "positive_recovery": FAMILY_DAILY_POSITIVE,
    "self_denial": FAMILY_SELF_DENIAL,
    "self_denial_support": FAMILY_SELF_DENIAL,
    "self_denial_non_emergency": FAMILY_SELF_DENIAL,
    "uncertainty": FAMILY_UNCERTAINTY,
    "uncertainty_support": FAMILY_UNCERTAINTY,
    "pressure": FAMILY_UNCERTAINTY,
    "desire_fear": FAMILY_UNCERTAINTY,
    "desire_and_fear": FAMILY_UNCERTAINTY,
    "mixed_emotion": FAMILY_MIXED_EMOTION,
    "mixed_emotion_relationship": FAMILY_MIXED_EMOTION,
    "conflict": FAMILY_MIXED_EMOTION,
    "long_meaning_arc": FAMILY_LONG_MEANING_ARC,
    "limited_grounding_long": FAMILY_LONG_MEANING_ARC,
    "history_cross_core": FAMILY_LONG_MEANING_ARC,
    "relationship": FAMILY_RELATIONSHIP_BOUNDARY,
    "relationship_boundary": FAMILY_RELATIONSHIP_BOUNDARY,
    "structure_question": FAMILY_STRUCTURE_QUESTION,
    "structure_question_observation": FAMILY_STRUCTURE_QUESTION,
    "positive_only": FAMILY_POSITIVE_ONLY,
    "self_understanding": FAMILY_SELF_UNDERSTANDING_FOLLOW,
    "self_understanding_follow": FAMILY_SELF_UNDERSTANDING_FOLLOW,
    "input_self_report_only_failure": FAMILY_INPUT_SELF_REPORT_ONLY_FAILURE,
    "self_report_only_failure": FAMILY_INPUT_SELF_REPORT_ONLY_FAILURE,
}
_RELATION_FAMILY_ALIASES: Final[dict[str, str]] = {
    "recovery": FAMILY_DAILY_POSITIVE,
    "positive_change_recovery": FAMILY_DAILY_POSITIVE,
    "pressure": FAMILY_UNCERTAINTY,
    "approach_avoidance": FAMILY_UNCERTAINTY,
    "desire_blockage_conflict": FAMILY_UNCERTAINTY,
    "relationship": FAMILY_RELATIONSHIP_BOUNDARY,
    "boundary": FAMILY_RELATIONSHIP_BOUNDARY,
    "contrast": FAMILY_MIXED_EMOTION,
    "coexistence": FAMILY_MIXED_EMOTION,
    "mixed_emotion_coexistence": FAMILY_MIXED_EMOTION,
    "history_cross_core": FAMILY_LONG_MEANING_ARC,
    "long_arc_multiple_core": FAMILY_LONG_MEANING_ARC,
    "self_denial_identity_split": FAMILY_SELF_DENIAL,
}

_DIMENSION_ALIASES: Final[dict[str, str]] = {
    "read": "read_feeling",
    "read_feeling": "read_feeling",
    "read-feeling": "read_feeling",
    "read_feeling_score": "read_feeling",
    "evidence_retention": "self_report_retention",
    "input_arrangement": "self_report_retention",
    "input_specific_structure_reflected": "state_structure_retention",
    "relation_kept": "state_structure_retention",
    "relation_verbalization": "state_structure_retention",
    "state_verbalization": "state_structure_retention",
    "self_report_retention": "self_report_retention",
    "state_structure_retention": "state_structure_retention",
    "emotion_temperature_retention": "emotion_temperature_retention",
    "follow_depth": "follow_depth",
    "distance": "evidence_boundary",
    "evidence_boundary": "evidence_boundary",
    "evidence_bound": "evidence_boundary",
    "user_fact_boundary": "evidence_boundary",
    "overclaim_absence": "evidence_boundary",
    "no_overclaim": "evidence_boundary",
    "soft_inference_surface": "soft_inference_surface",
    "insight_delta": "insight_delta",
    "structure_insight_delta": "insight_delta",
    "naturalness": "naturalness",
    "surface_naturalness": "naturalness",
    "non_template": "non_template",
    "non-template": "non_template",
    "template": "non_template",
}
_VERDICT_SCORES: Final[dict[str, float]] = {
    "green": 1.0,
    "g": 1.0,
    "pass": 1.0,
    "passed": 1.0,
    "ok": 1.0,
    "yellow": 0.65,
    "y": 0.65,
    "warn": 0.65,
    "warning": 0.65,
    "red": 0.0,
    "r": 0.0,
    "fail": 0.0,
    "failed": 0.0,
    "ng": 0.0,
}


def _clean(value: Any) -> str:
    if value is None or isinstance(value, (Mapping, list, tuple, set)):
        return ""
    return _SPACE_RE.sub(" ", str(value).replace("\u3000", " ")).strip()


def _clean_key(value: Any) -> str:
    return _clean(value).lower()


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
    return [value]


def _dedupe(values: Iterable[Any] | Any | None) -> list[str]:
    out: list[str] = []
    seen: set[str] = set()
    for value in _listify(values):
        text = _clean(value)
        if text and text not in seen:
            seen.add(text)
            out.append(text)
    return out


def _safe_int(value: Any, default: int = 0) -> int:
    try:
        if value is None or value == "":
            return default
        return int(float(value))
    except (TypeError, ValueError):
        return default


def _safe_float(value: Any) -> float | None:
    try:
        if value is None or value == "":
            return None
        return max(0.0, min(1.0, float(value)))
    except (TypeError, ValueError):
        return None


def _score_from_verdict(value: Any) -> float | None:
    text = _clean(value).lower()
    if text in _VERDICT_SCORES:
        return _VERDICT_SCORES[text]
    return _safe_float(value)


def _rate(numerator: int, denominator: int) -> float:
    if denominator <= 0:
        return 0.0
    return round(max(0.0, min(1.0, numerator / denominator)), 4)


def _contains_text_payload_key(value: Any) -> bool:
    if isinstance(value, Mapping):
        for key, item in value.items():
            if str(key) in _TEXT_PAYLOAD_KEYS:
                return True
            if _contains_text_payload_key(item):
                return True
        return False
    if isinstance(value, (list, tuple, set)):
        return any(_contains_text_payload_key(item) for item in value)
    return False


def _strip_text_payload_keys(value: Any) -> Any:
    if isinstance(value, Mapping):
        return {
            str(key): _strip_text_payload_keys(item)
            for key, item in value.items()
            if str(key) not in _TEXT_PAYLOAD_KEYS
        }
    if isinstance(value, list):
        return [_strip_text_payload_keys(item) for item in value]
    if isinstance(value, tuple):
        return tuple(_strip_text_payload_keys(item) for item in value)
    if isinstance(value, set):
        return {_strip_text_payload_keys(item) for item in value}
    return value


def assert_product_readfeel_current_output_inventory_meta_only(
    payload: Mapping[str, Any],
    *,
    source: str = "product_readfeel_current_output_inventory",
) -> None:
    if _contains_text_payload_key(payload):
        raise ValueError(f"{source} must stay meta-only and must not include text payload keys")
    for flag in _FORBIDDEN_TRUE_FLAGS:
        if payload.get(flag) is True:
            raise ValueError(f"{source} violates fixed contract: {flag}=true")


def _reason_values(record: Mapping[str, Any]) -> list[str]:
    reasons: list[str] = []
    for key in (
        "top_rejection_reasons",
        "rejection_reasons",
        "secondary_reasons",
        "reason_codes",
        "gate_reasons",
        "gate_rejection_reasons",
        "surface_major_reasons",
        "surface_grammar_warning_codes",
        "grammar_warning_codes",
        "release_blockers",
        "qa_gaps",
        "red_flags",
        "repair_reasons",
        "failure_reasons",
        "inventory_reasons",
    ):
        reasons.extend(_dedupe(record.get(key)))
    for key in (
        "primary_reason",
        "gate_primary_reason",
        "first_failed_reason",
        "failed_stage",
        "stage",
        "unavailable_reason",
        "reason_code",
        "v1_repair_reason",
        "v2_backlog_reason",
    ):
        text = _clean(record.get(key))
        if text:
            reasons.append(text)
    gate_results = _safe_mapping(record.get("gate_results"))
    for gate_name, gate in gate_results.items():
        gate_data = _safe_mapping(gate)
        reasons.extend(_dedupe(gate_data.get("rejection_reasons")))
        reasons.extend(_dedupe(gate_data.get("reasons")))
        first = _clean(gate_data.get("first_failed_reason"))
        if first:
            reasons.append(f"{gate_name}:{first}")
    return _dedupe(reasons)


def _has_marker(values: Iterable[str], markers: Sequence[str]) -> bool:
    for value in values:
        lower = value.lower()
        if any(marker in lower for marker in markers):
            return True
    return False


def _family_from_record(record: Mapping[str, Any]) -> str:
    for key in (
        "product_readfeel_family",
        "readfeel_family",
        "fixture_family",
        "fixtureFamily",
        "case_family",
        "family",
        "input_family",
        "fixture_group",
        "observation_fixture_group",
        "coverage_group",
        "reception_mode",
        "mode",
    ):
        raw = _clean(record.get(key))
        if not raw:
            continue
        normalized = _FAMILY_ALIASES.get(raw.lower())
        if normalized:
            return normalized
        if raw in PRODUCT_READFEEL_REQUIRED_FAMILIES:
            return raw
    for relation in _dedupe(
        record.get("relation_types")
        or record.get("expected_relation_types")
        or record.get("used_relation_types")
        or record.get("relation_type")
    ):
        normalized = _RELATION_FAMILY_ALIASES.get(relation.lower())
        if normalized:
            return normalized
    return FAMILY_UNCLASSIFIED


def _rating_scores(record: Mapping[str, Any]) -> dict[str, float | None]:
    ratings = _safe_mapping(record.get("ratings")) or _safe_mapping(record.get("dimension_ratings"))
    if not ratings:
        ratings = {key: value for key, value in record.items() if _DIMENSION_ALIASES.get(str(key).strip().lower())}
    scores: dict[str, float | None] = {}
    for raw_key, raw_value in ratings.items():
        dimension = _DIMENSION_ALIASES.get(str(raw_key).strip().lower())
        if not dimension:
            continue
        score = _score_from_verdict(raw_value)
        if score is not None:
            scores[dimension] = score
    return scores


def _display_expected(record: Mapping[str, Any], reasons: Sequence[str]) -> bool:
    if record.get("expected_public_feedback") is False or record.get("expected_display") is False:
        return False
    if record.get("safety_or_infra_excluded") is True:
        return False
    status = _clean(record.get("observation_status") or record.get("backend_observation_status") or record.get("status")).lower()
    if status in {"safety_blocked", "infrastructure_error", "infra_error", "safety_emergency"}:
        return False
    if _has_marker(reasons, _SAFETY_OR_INFRA_MARKERS) and status in {"rejected", "unavailable", "safety_blocked"}:
        return False
    if any(key in record for key in ("eligible_count", "display_confirmed", "passed_display_count", "comment_text_present", "public_passed", "backend_public_passed", "observation_status")):
        return True
    return False


def _display_returned(record: Mapping[str, Any]) -> bool:
    status = _clean(record.get("observation_status") or record.get("backend_observation_status") or record.get("status")).lower()
    if status == "passed":
        return True
    return bool(
        record.get("display_confirmed") is True
        or record.get("public_passed") is True
        or record.get("backend_public_passed") is True
        or record.get("comment_text_present") is True
        or record.get("backend_comment_text_present") is True
        or _safe_int(record.get("passed_display_count"), 0) > 0
    )


def _source_body_seen(record: Mapping[str, Any]) -> bool:
    return any(key in record for key in _TEXT_PAYLOAD_KEYS if key not in {"input"})


def _mirror_only_detector_fields(record: Mapping[str, Any]) -> dict[str, Any]:
    existing_report = (
        _safe_mapping(record.get("mirror_only_surface_report"))
        or _safe_mapping(record.get("phase6_mirror_only_surface_report"))
        or _safe_mapping(record.get("mirror_only_detector_report"))
    )
    if existing_report:
        return normalize_mirror_only_surface_to_scorecard_event(existing_report)
    detector_report = detect_mirror_only_surface(record)
    return normalize_mirror_only_surface_to_scorecard_event(detector_report)


def _sufficient_material_for_insight(record: Mapping[str, Any], family: str) -> bool:
    flags = _safe_mapping(record.get("input_material_flags") or record.get("material_flags"))
    if any(flags.get(key) is True for key in ("long_input", "structure_question_requested", "memo_action_present", "emotion_details_present")):
        return True
    if _safe_int(record.get("material_slot_count"), 0) >= 3:
        return True
    if _safe_int(record.get("evidence_slot_count"), 0) >= 3:
        return True
    if len(_dedupe(record.get("source_field_ids") or record.get("evidence_slot_ids"))) >= 3:
        return True
    return family in {
        FAMILY_LONG_MEANING_ARC,
        FAMILY_STRUCTURE_QUESTION,
        FAMILY_SELF_UNDERSTANDING_FOLLOW,
        FAMILY_INPUT_SELF_REPORT_ONLY_FAILURE,
        FAMILY_MIXED_EMOTION,
    }


def _mirror_only_detected(record: Mapping[str, Any], reasons: Sequence[str], scores: Mapping[str, float | None], family: str) -> bool:
    if record.get("mirror_only_detected") is True or record.get("self_report_only_detected") is True:
        return True
    if _has_marker(reasons, _STRUCTURE_REASON_MARKERS):
        return True
    insight_score = scores.get("insight_delta")
    if insight_score is not None and insight_score < 0.90 and _sufficient_material_for_insight(record, family):
        return True
    if family == FAMILY_INPUT_SELF_REPORT_ONLY_FAILURE:
        return True
    return False


def _failure_buckets(record: Mapping[str, Any], family: str) -> tuple[list[str], list[str], dict[str, float | None], bool]:
    reasons = _reason_values(record)
    scores = _rating_scores(record)
    buckets: list[str] = []
    if _display_expected(record, reasons) and not _display_returned(record):
        buckets.append(FAILURE_DISPLAY_NOT_REACHED)
    if any(record.get(flag) is True for flag in _FORBIDDEN_TRUE_FLAGS) or _has_marker(reasons, _CONTRACT_REASON_MARKERS):
        buckets.append(FAILURE_CONTRACT_VIOLATION)
    surface_score = min(
        [score for key, score in scores.items() if key in {"evidence_boundary", "soft_inference_surface", "naturalness", "non_template"} and score is not None]
        or [1.0]
    )
    if (
        _safe_int(record.get("safety_major_count"), 0) > 0
        or _safe_int(record.get("template_major_count"), 0) > 0
        or _safe_int(record.get("surface_template_major_count"), 0) > 0
        or _safe_int(record.get("surface_grammar_warning_count"), 0) > 0
        or record.get("fixed_fallback_used") is True
        or _has_marker(reasons, _SURFACE_REASON_MARKERS)
        or surface_score == 0.0
    ):
        buckets.append(FAILURE_SURFACE_BREAKAGE)
    readfeel_dims = {
        "read_feeling",
        "self_report_retention",
        "state_structure_retention",
        "emotion_temperature_retention",
        "follow_depth",
    }
    readfeel_score = min([score for key, score in scores.items() if key in readfeel_dims and score is not None] or [1.0])
    if readfeel_score < 0.90 or _has_marker(reasons, _READFEEL_REASON_MARKERS):
        buckets.append(FAILURE_READFEEL_GAP)
    mirror_only = _mirror_only_detected(record, reasons, scores, family)
    if mirror_only:
        buckets.append(FAILURE_STRUCTURE_INSIGHT_GAP)
    return _dedupe(buckets), reasons, dict(scores), mirror_only


def _verdict_for_item(
    *,
    buckets: Sequence[str],
    mirror_only: bool,
    family: str,
    scores: Mapping[str, float | None],
    sufficient_material_for_insight: bool,
) -> str:
    if FAILURE_CONTRACT_VIOLATION in buckets or FAILURE_SURFACE_BREAKAGE in buckets:
        return VERDICT_RED
    if FAILURE_DISPLAY_NOT_REACHED in buckets:
        return VERDICT_REPAIR_REQUIRED
    if mirror_only and sufficient_material_for_insight:
        return VERDICT_REPAIR_REQUIRED
    if mirror_only and family not in {FAMILY_LOW_INFORMATION_SHORT, FAMILY_DAILY_UNPLEASANT, FAMILY_DAILY_POSITIVE}:
        return VERDICT_REPAIR_REQUIRED
    if FAILURE_READFEEL_GAP in buckets:
        read_score = scores.get("read_feeling")
        if read_score == 0.0:
            return VERDICT_REPAIR_REQUIRED
        return VERDICT_YELLOW
    if FAILURE_STRUCTURE_INSIGHT_GAP in buckets:
        return VERDICT_YELLOW
    if buckets:
        return VERDICT_YELLOW
    return VERDICT_PASS


def normalize_product_readfeel_current_output_item(
    record: Mapping[str, Any] | None,
    *,
    source_kind: str = "scorecard_event",
) -> dict[str, Any]:
    source = _safe_mapping(record)
    source_had_text_payload_keys = _source_body_seen(source)
    mirror_detector_fields = _mirror_only_detector_fields(source)
    # Keep contract/safety flags from the original scorecard event authoritative.
    # Phase6 detector fields may carry fixed false boundary flags for their own
    # meta-only report, but those must not overwrite a true violation observed
    # in the source event.
    merged_source = {**mirror_detector_fields, **source}
    if mirror_detector_fields.get("mirror_only_detected") is True:
        merged_source["mirror_only_detected"] = True
        merged_source["self_report_only_detected"] = True
        merged_source["inventory_reasons"] = _dedupe(
            [
                *_dedupe(source.get("inventory_reasons")),
                "mirror_only_surface_detector_detected",
                *_dedupe(mirror_detector_fields.get("mirror_only_reason_codes")),
            ]
        )
    data = _safe_mapping(_strip_text_payload_keys(merged_source))
    family = _family_from_record(data)
    buckets, reasons, scores, mirror_only = _failure_buckets(data, family)
    sufficient_material = _sufficient_material_for_insight(data, family)
    verdict = _verdict_for_item(
        buckets=buckets,
        mirror_only=mirror_only,
        family=family,
        scores=scores,
        sufficient_material_for_insight=sufficient_material,
    )
    item = {
        "version": PRODUCT_READFEEL_ITEM_VERSION,
        "schema_version": PRODUCT_READFEEL_ITEM_VERSION,
        "source_step": PRODUCT_READFEEL_CURRENT_OUTPUT_INVENTORY_STEP,
        "source_kind": source_kind,
        "item_id": _clean(data.get("item_id") or data.get("row_id") or data.get("candidate_id") or data.get("review_id") or data.get("trace_id") or data.get("fixture_id")),
        "row_id": _clean(data.get("row_id")),
        "candidate_id": _clean(data.get("candidate_id")),
        "review_id": _clean(data.get("review_id")),
        "trace_id": _clean(data.get("trace_id")),
        "fixture_id": _clean(data.get("fixture_id")),
        "coverage_group": _clean(data.get("coverage_group")),
        "fixture_group": _clean(data.get("fixture_group") or data.get("observation_fixture_group")),
        "product_readfeel_family": family,
        "family": family,
        "verdict": verdict,
        "failure_buckets": buckets,
        "failure_bucket_count": len(buckets),
        "display_not_reached": FAILURE_DISPLAY_NOT_REACHED in buckets,
        "contract_violation": FAILURE_CONTRACT_VIOLATION in buckets,
        "surface_breakage": FAILURE_SURFACE_BREAKAGE in buckets,
        "readfeel_gap": FAILURE_READFEEL_GAP in buckets,
        "structure_insight_gap": FAILURE_STRUCTURE_INSIGHT_GAP in buckets,
        "mirror_only_detected": mirror_only,
        "phase6_mirror_only_detector_ready": bool(mirror_detector_fields.get("phase6_mirror_only_detector_ready")),
        "mirror_only_detector_ready": bool(mirror_detector_fields.get("mirror_only_detector_ready")),
        "mirror_only_v1_verdict_hint": _clean(mirror_detector_fields.get("mirror_only_v1_verdict_hint")),
        "mirror_only_v2_insight_delta_gap": bool(mirror_detector_fields.get("mirror_only_v2_insight_delta_gap")),
        "mirror_only_reason_codes": _dedupe(mirror_detector_fields.get("mirror_only_reason_codes")),
        "display_expected": _display_expected(data, reasons),
        "display_returned": _display_returned(data),
        "source_display_body_seen": source_had_text_payload_keys,
        "source_display_body_retained": False,
        "exact_comment_text_required": False,
        "runtime_branching_uses_fixture_strings": False,
        "fixture_text_used_for_runtime_branching": False,
        "v1_action": "repair" if verdict in {VERDICT_RED, VERDICT_REPAIR_REQUIRED} or FAILURE_READFEEL_GAP in buckets else "monitor_or_pass",
        "v2_action": "structure_insight_backlog" if FAILURE_STRUCTURE_INSIGHT_GAP in buckets else "not_required_for_phase1",
        "v1_repair_required": verdict in {VERDICT_RED, VERDICT_REPAIR_REQUIRED} or FAILURE_READFEEL_GAP in buckets,
        "v2_structure_insight_backlog": FAILURE_STRUCTURE_INSIGHT_GAP in buckets,
        "dimension_scores": scores,
        "reason_codes": reasons,
        "raw_input_included": False,
        "raw_text_included": False,
        "comment_text_included": False,
        "comment_text_body_included": False,
        "display_gate_relaxed": False,
        "grounding_gate_relaxed": False,
        "template_gate_relaxed": False,
        "reader_gate_relaxed": False,
        "gate_relaxed": False,
        "public_response_key_change": False,
        "api_route_changed": False,
        "db_physical_name_changed": False,
        "rn_visible_contract_changed": False,
        "rn_visible_title_changed": False,
        "product_gate_ready": False,
        "public_release_applied": False,
    }
    assert_product_readfeel_current_output_inventory_meta_only(item, source="product_readfeel_current_output_item")
    return item


def normalize_product_readfeel_current_output_review(review: Mapping[str, Any] | None) -> dict[str, Any]:
    item = normalize_product_readfeel_current_output_item(review, source_kind="blind_qa_review")
    item["version"] = PRODUCT_READFEEL_REVIEW_VERSION
    item["schema_version"] = PRODUCT_READFEEL_REVIEW_VERSION
    item["ratings_only_payload"] = True
    item["machine_metrics_used_for_read_feeling"] = False
    item["read_feeling_auto_filled_from_machine_metrics"] = False
    assert_product_readfeel_current_output_inventory_meta_only(item, source="product_readfeel_current_output_review")
    return item


def _worst_verdict(values: Iterable[str]) -> str:
    verdicts = list(values)
    if not verdicts:
        return VERDICT_NOT_EVALUATED
    return max(verdicts, key=lambda value: _VERDICT_ORDER.get(value, 0))


def _family_summary(family: str, items: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    verdict_counter: Counter[str] = Counter(_clean(item.get("verdict")) for item in items)
    bucket_counter: Counter[str] = Counter()
    reason_counter: Counter[str] = Counter()
    for item in items:
        bucket_counter.update(_dedupe(item.get("failure_buckets")))
        reason_counter.update(_dedupe(item.get("reason_codes")))
    verdict = _worst_verdict(item.get("verdict") for item in items)
    v1_repair_required = any(item.get("v1_repair_required") is True for item in items)
    v2_backlog = any(item.get("v2_structure_insight_backlog") is True for item in items)
    summary = {
        "version": PRODUCT_READFEEL_FAMILY_SUMMARY_VERSION,
        "schema_version": PRODUCT_READFEEL_FAMILY_SUMMARY_VERSION,
        "source_step": PRODUCT_READFEEL_CURRENT_OUTPUT_INVENTORY_STEP,
        "family": family,
        "product_readfeel_family": family,
        "item_count": len(items),
        "verdict": verdict,
        "verdict_counts": dict(verdict_counter),
        "failure_bucket_counts": dict(bucket_counter),
        "display_not_reached_count": int(bucket_counter.get(FAILURE_DISPLAY_NOT_REACHED, 0)),
        "contract_violation_count": int(bucket_counter.get(FAILURE_CONTRACT_VIOLATION, 0)),
        "surface_breakage_count": int(bucket_counter.get(FAILURE_SURFACE_BREAKAGE, 0)),
        "readfeel_gap_count": int(bucket_counter.get(FAILURE_READFEEL_GAP, 0)),
        "structure_insight_gap_count": int(bucket_counter.get(FAILURE_STRUCTURE_INSIGHT_GAP, 0)),
        "mirror_only_count": sum(1 for item in items if item.get("mirror_only_detected") is True),
        "v1_repair_required": v1_repair_required,
        "v2_structure_insight_backlog": v2_backlog,
        "v1_action": "repair_or_review" if v1_repair_required else "pass_or_monitor",
        "v2_action": "structure_insight_backlog" if v2_backlog else "not_required_for_phase1",
        "top_reasons": [reason for reason, _count in reason_counter.most_common(8)],
        "raw_input_included": False,
        "raw_text_included": False,
        "comment_text_included": False,
        "comment_text_body_included": False,
        "product_gate_ready": False,
        "public_release_applied": False,
    }
    assert_product_readfeel_current_output_inventory_meta_only(summary, source="product_readfeel_family_summary")
    return summary


def build_product_readfeel_current_output_inventory(
    *,
    events: Iterable[Mapping[str, Any] | None] | None = None,
    scorecard_events: Iterable[Mapping[str, Any] | None] | None = None,
    records: Iterable[Mapping[str, Any] | None] | None = None,
    blind_qa_reviews: Iterable[Mapping[str, Any] | None] | None = None,
    run_id: str = "",
) -> dict[str, Any]:
    raw_events: list[Mapping[str, Any] | None] = []
    raw_events.extend(list(events or []))
    raw_events.extend(list(scorecard_events or []))
    raw_events.extend(list(records or []))
    items = [normalize_product_readfeel_current_output_item(event, source_kind="scorecard_event") for event in raw_events]
    review_items = [normalize_product_readfeel_current_output_review(review) for review in list(blind_qa_reviews or [])]
    all_items = items + review_items
    by_family: dict[str, list[dict[str, Any]]] = {}
    for item in all_items:
        family = _clean(item.get("product_readfeel_family")) or FAMILY_UNCLASSIFIED
        by_family.setdefault(family, []).append(item)
    family_summaries = [_family_summary(family, by_family[family]) for family in sorted(by_family)]
    family_verdicts = {summary["family"]: summary["verdict"] for summary in family_summaries}
    bucket_counter: Counter[str] = Counter()
    for item in all_items:
        bucket_counter.update(_dedupe(item.get("failure_buckets")))
    observed_families = [summary["family"] for summary in family_summaries]
    missing_families = [family for family in PRODUCT_READFEEL_REQUIRED_FAMILIES if family not in observed_families]
    mirror_only_cases = [
        {
            "item_id": item.get("item_id"),
            "family": item.get("family"),
            "verdict": item.get("verdict"),
            "v1_action": item.get("v1_action"),
            "v2_action": item.get("v2_action"),
        }
        for item in all_items
        if item.get("mirror_only_detected") is True
    ]
    v1_fix_families = [summary["family"] for summary in family_summaries if summary.get("v1_repair_required") is True]
    v2_backlog_families = [
        summary["family"] for summary in family_summaries if summary.get("v2_structure_insight_backlog") is True
    ]
    completion_conditions = {
        "family_verdicts_present": bool(family_summaries),
        "failure_taxonomy_present": bool(all_items),
        "mirror_only_cases_visible": True,
        "v1_v2_separated": True,
        "exact_comment_text_required": False,
        "public_contract_unchanged": True,
    }
    phase1_ready = (
        bool(completion_conditions["family_verdicts_present"])
        and bool(completion_conditions["failure_taxonomy_present"])
        and bool(completion_conditions["mirror_only_cases_visible"])
        and bool(completion_conditions["v1_v2_separated"])
        and completion_conditions["exact_comment_text_required"] is False
        and bool(completion_conditions["public_contract_unchanged"])
    )
    inventory = {
        "version": PRODUCT_READFEEL_CURRENT_OUTPUT_INVENTORY_VERSION,
        "schema_version": PRODUCT_READFEEL_CURRENT_OUTPUT_INVENTORY_VERSION,
        "source": PRODUCT_READFEEL_CURRENT_OUTPUT_INVENTORY_SOURCE,
        "source_step": PRODUCT_READFEEL_CURRENT_OUTPUT_INVENTORY_STEP,
        "step": PRODUCT_READFEEL_CURRENT_OUTPUT_INVENTORY_STEP,
        "run_id": _clean(run_id),
        "inventory_type": "current_output_readfeel_inventory_meta_only",
        "phase1_current_output_inventory_ready": phase1_ready,
        "product_readfeel_phase1_ready": phase1_ready,
        "completion_conditions": completion_conditions,
        "required_families": list(PRODUCT_READFEEL_REQUIRED_FAMILIES),
        "observed_families": observed_families,
        "missing_families": missing_families,
        "item_count": len(all_items),
        "scorecard_event_item_count": len(items),
        "blind_qa_review_item_count": len(review_items),
        "family_summaries": family_summaries,
        "family_verdicts": family_verdicts,
        "failure_bucket_counts": dict(bucket_counter),
        "display_not_reached_count": int(bucket_counter.get(FAILURE_DISPLAY_NOT_REACHED, 0)),
        "contract_violation_count": int(bucket_counter.get(FAILURE_CONTRACT_VIOLATION, 0)),
        "surface_breakage_count": int(bucket_counter.get(FAILURE_SURFACE_BREAKAGE, 0)),
        "readfeel_gap_count": int(bucket_counter.get(FAILURE_READFEEL_GAP, 0)),
        "structure_insight_gap_count": int(bucket_counter.get(FAILURE_STRUCTURE_INSIGHT_GAP, 0)),
        "mirror_only_detected_count": len(mirror_only_cases),
        "phase6_mirror_only_detector_ready": any(item.get("phase6_mirror_only_detector_ready") for item in all_items),
        "mirror_only_detector_ready": any(item.get("mirror_only_detector_ready") for item in all_items),
        "mirror_only_cases": mirror_only_cases,
        "v1_fix_families": v1_fix_families,
        "v2_structure_insight_backlog_families": v2_backlog_families,
        "v1_fix_required_count": len(v1_fix_families),
        "v2_structure_insight_backlog_count": len(v2_backlog_families),
        "items": all_items,
        "exact_comment_text_required": False,
        "runtime_branching_uses_fixture_strings": False,
        "fixture_text_used_for_runtime_branching": False,
        "machine_metrics_used_for_read_feeling": False,
        "read_feeling_auto_filled_from_machine_metrics": False,
        "comment_text_generated": False,
        "comment_text_key_written": False,
        "raw_input_included": False,
        "raw_text_included": False,
        "comment_text_included": False,
        "comment_text_body_included": False,
        "response_shape_changed": False,
        "public_response_key_change": False,
        "api_route_changed": False,
        "db_physical_name_changed": False,
        "rn_visible_contract_changed": False,
        "rn_visible_title_changed": False,
        "display_gate_relaxed": False,
        "grounding_gate_relaxed": False,
        "template_gate_relaxed": False,
        "reader_gate_relaxed": False,
        "gate_relaxed": False,
        "product_gate_ready": False,
        "product_gate_reached": False,
        "product_gate_public_release_applied": False,
        "public_release_applied": False,
        "product_quality_released": False,
        "external_ai_used": False,
        "local_llm_used": False,
    }
    assert_product_readfeel_current_output_inventory_meta_only(
        inventory,
        source="product_readfeel_current_output_inventory",
    )
    return inventory


def normalize_product_readfeel_current_output_inventory_to_scorecard_fields(
    inventory: Mapping[str, Any] | None,
) -> dict[str, Any]:
    data = _safe_mapping(inventory)
    if not data:
        data = build_product_readfeel_current_output_inventory(events=[], blind_qa_reviews=[])
    assert_product_readfeel_current_output_inventory_meta_only(
        data,
        source="product_readfeel_inventory_scorecard_fields_source",
    )
    return {
        "product_readfeel_current_output_inventory_version": _clean(data.get("version"))
        or PRODUCT_READFEEL_CURRENT_OUTPUT_INVENTORY_VERSION,
        "product_readfeel_current_output_inventory_step": _clean(data.get("step"))
        or PRODUCT_READFEEL_CURRENT_OUTPUT_INVENTORY_STEP,
        "phase1_product_readfeel_current_output_inventory_ready": bool(
            data.get("phase1_current_output_inventory_ready")
        ),
        "product_readfeel_phase1_ready": bool(data.get("product_readfeel_phase1_ready")),
        "product_readfeel_item_count": _safe_int(data.get("item_count"), 0),
        "product_readfeel_family_verdicts": dict(data.get("family_verdicts") or {}),
        "product_readfeel_observed_families": list(data.get("observed_families") or []),
        "product_readfeel_missing_families": list(data.get("missing_families") or []),
        "product_readfeel_failure_bucket_counts": dict(data.get("failure_bucket_counts") or {}),
        "product_readfeel_display_not_reached_count": _safe_int(data.get("display_not_reached_count"), 0),
        "product_readfeel_contract_violation_count": _safe_int(data.get("contract_violation_count"), 0),
        "product_readfeel_surface_breakage_count": _safe_int(data.get("surface_breakage_count"), 0),
        "product_readfeel_readfeel_gap_count": _safe_int(data.get("readfeel_gap_count"), 0),
        "product_readfeel_structure_insight_gap_count": _safe_int(data.get("structure_insight_gap_count"), 0),
        "product_readfeel_mirror_only_detected_count": _safe_int(data.get("mirror_only_detected_count"), 0),
        "phase6_product_readfeel_mirror_only_detector_ready": bool(data.get("phase6_mirror_only_detector_ready") or data.get("mirror_only_detector_ready")),
        "product_readfeel_mirror_only_detector_ready": bool(data.get("mirror_only_detector_ready") or data.get("phase6_mirror_only_detector_ready")),
        "product_readfeel_v1_fix_families": list(data.get("v1_fix_families") or []),
        "product_readfeel_v2_structure_insight_backlog_families": list(
            data.get("v2_structure_insight_backlog_families") or []
        ),
        "machine_metrics_used_for_read_feeling": False,
        "read_feeling_auto_filled_from_machine_metrics": False,
        "raw_input_included": False,
        "comment_text_body_included": False,
        "product_gate_ready": False,
        "public_release_applied": False,
    }


def dump_product_readfeel_current_output_inventory(inventory: Mapping[str, Any] | None = None) -> str:
    data = dict(inventory or build_product_readfeel_current_output_inventory(events=[], blind_qa_reviews=[]))
    assert_product_readfeel_current_output_inventory_meta_only(data)
    return json.dumps(data, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


__all__ = [
    "PRODUCT_READFEEL_CURRENT_OUTPUT_INVENTORY_VERSION",
    "PRODUCT_READFEEL_CURRENT_OUTPUT_INVENTORY_STEP",
    "PRODUCT_READFEEL_REQUIRED_FAMILIES",
    "VERDICT_RED",
    "VERDICT_REPAIR_REQUIRED",
    "VERDICT_YELLOW",
    "VERDICT_PASS",
    "FAILURE_DISPLAY_NOT_REACHED",
    "FAILURE_CONTRACT_VIOLATION",
    "FAILURE_SURFACE_BREAKAGE",
    "FAILURE_READFEEL_GAP",
    "FAILURE_STRUCTURE_INSIGHT_GAP",
    "assert_product_readfeel_current_output_inventory_meta_only",
    "normalize_product_readfeel_current_output_item",
    "normalize_product_readfeel_current_output_review",
    "build_product_readfeel_current_output_inventory",
    "normalize_product_readfeel_current_output_inventory_to_scorecard_fields",
    "dump_product_readfeel_current_output_inventory",
]
