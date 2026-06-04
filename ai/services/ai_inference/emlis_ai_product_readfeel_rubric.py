# -*- coding: utf-8 -*-
from __future__ import annotations

"""Phase 2 Product Read Feel rubric candidate for EmlisAI.

This module fixes the Phase 2 implementation decision as a separated,
meta-only rubric module that can be projected into existing scorecards.  It
normalizes ratings-only Blind QA reviews for Product Read Feel v1 dimensions
and keeps machine metrics separate.  It never stores raw user input or public
``comment_text`` bodies, never writes public response keys, and never turns
``read_feeling`` into a machine-derived score.
"""

from collections.abc import Iterable, Mapping, Sequence
import json
from typing import Any, Final

PRODUCT_READFEEL_RUBRIC_VERSION: Final = "cocolon.emlis.product_readfeel.rubric.v1"
PRODUCT_READFEEL_RUBRIC_PHASE2_STEP: Final = "Phase2_Product_Read_Feel_Rubric_Design"
PRODUCT_READFEEL_RUBRIC_SOURCE: Final = "Cocolon_EmlisAI_ProductReadFeel_Phase2_Rubric"
PRODUCT_READFEEL_BLIND_QA_REVIEW_VERSION: Final = "cocolon.emlis.product_readfeel.blind_qa_review.v1"
PRODUCT_READFEEL_BLIND_QA_AGGREGATE_VERSION: Final = "cocolon.emlis.product_readfeel.blind_qa_aggregate.v1"
PRODUCT_READFEEL_RUBRIC_PHASE2_MATERIAL_VERSION: Final = "cocolon.emlis.product_readfeel.phase2.material.v1"
PRODUCT_READFEEL_RUBRIC_SCORECARD_FIELDS_VERSION: Final = "cocolon.emlis.product_readfeel.rubric_scorecard_fields.v1"
PRODUCT_READFEEL_SCORECARD_FIELDS_VERSION: Final = PRODUCT_READFEEL_RUBRIC_SCORECARD_FIELDS_VERSION
PRODUCT_READFEEL_RUBRIC_IMPLEMENTATION_DECISION: Final = "separate_meta_only_rubric_connected_to_scorecard"

PRODUCT_READFEEL_CONNECTION_READ_FEELING_TARGET: Final = 0.85
PRODUCT_READFEEL_PRODUCT_READ_FEELING_TARGET: Final = 0.90
PRODUCT_READFEEL_V1_DIMENSION_TARGET: Final = 0.65
PRODUCT_READFEEL_V2_INSIGHT_READY_TARGET: Final = 0.90

DIMENSION_READ_FEELING: Final = "read_feeling"
DIMENSION_SELF_REPORT_RETENTION: Final = "self_report_retention"
DIMENSION_STATE_STRUCTURE_RETENTION: Final = "state_structure_retention"
DIMENSION_EMOTION_TEMPERATURE_RETENTION: Final = "emotion_temperature_retention"
DIMENSION_FOLLOW_DEPTH: Final = "follow_depth"
DIMENSION_EVIDENCE_BOUNDARY: Final = "evidence_boundary"
DIMENSION_SOFT_INFERENCE_SURFACE: Final = "soft_inference_surface"
DIMENSION_NATURALNESS: Final = "naturalness"
DIMENSION_NON_TEMPLATE: Final = "non_template"
DIMENSION_INSIGHT_DELTA: Final = "insight_delta"
DIMENSION_STRUCTURE_INSIGHT_CANDIDATE_QUALITY: Final = "structure_insight_candidate_quality"

PRODUCT_READFEEL_V1_RATING_DIMENSIONS: Final[tuple[str, ...]] = (
    DIMENSION_READ_FEELING,
    DIMENSION_SELF_REPORT_RETENTION,
    DIMENSION_STATE_STRUCTURE_RETENTION,
    DIMENSION_EMOTION_TEMPERATURE_RETENTION,
    DIMENSION_FOLLOW_DEPTH,
    DIMENSION_EVIDENCE_BOUNDARY,
    DIMENSION_SOFT_INFERENCE_SURFACE,
    DIMENSION_NATURALNESS,
    DIMENSION_NON_TEMPLATE,
)
PRODUCT_READFEEL_V2_CANDIDATE_DIMENSIONS: Final[tuple[str, ...]] = (
    DIMENSION_INSIGHT_DELTA,
    DIMENSION_STRUCTURE_INSIGHT_CANDIDATE_QUALITY,
)
PRODUCT_READFEEL_RATING_DIMENSIONS: Final[tuple[str, ...]] = (
    *PRODUCT_READFEEL_V1_RATING_DIMENSIONS,
    *PRODUCT_READFEEL_V2_CANDIDATE_DIMENSIONS,
)

PRODUCT_READFEEL_RUBRIC_STEP: Final = PRODUCT_READFEEL_RUBRIC_PHASE2_STEP
PRODUCT_READFEEL_V1_REQUIRED_DIMENSIONS: Final[tuple[str, ...]] = PRODUCT_READFEEL_V1_RATING_DIMENSIONS
PRODUCT_READFEEL_V2_OPTIONAL_DIMENSIONS: Final[tuple[str, ...]] = PRODUCT_READFEEL_V2_CANDIDATE_DIMENSIONS

VERDICT_RED: Final = "RED"
VERDICT_REPAIR_REQUIRED: Final = "REPAIR_REQUIRED"
VERDICT_YELLOW: Final = "YELLOW"
VERDICT_PASS: Final = "PASS"
VERDICT_PRODUCT_PASS: Final = "PRODUCT_PASS"
VERDICT_STRUCTURE_INSIGHT_READY: Final = "STRUCTURE_INSIGHT_READY"
VERDICT_NOT_EVALUATED: Final = "NOT_EVALUATED"

_DIMENSION_ALIASES: Final[dict[str, str]] = {
    "read": DIMENSION_READ_FEELING,
    "read_feeling": DIMENSION_READ_FEELING,
    "read_feeling_score": DIMENSION_READ_FEELING,
    "read-feeling": DIMENSION_READ_FEELING,
    "product_read_feeling": DIMENSION_READ_FEELING,
    "input_specific_structure_reflected": DIMENSION_READ_FEELING,
    "self_report": DIMENSION_SELF_REPORT_RETENTION,
    "self_report_retention": DIMENSION_SELF_REPORT_RETENTION,
    "self-report-retention": DIMENSION_SELF_REPORT_RETENTION,
    "material_retention": DIMENSION_SELF_REPORT_RETENTION,
    "evidence_retention": DIMENSION_SELF_REPORT_RETENTION,
    "selected_material_retention": DIMENSION_SELF_REPORT_RETENTION,
    "state_structure": DIMENSION_STATE_STRUCTURE_RETENTION,
    "state_structure_retention": DIMENSION_STATE_STRUCTURE_RETENTION,
    "state-structure-retention": DIMENSION_STATE_STRUCTURE_RETENTION,
    "structure_retention": DIMENSION_STATE_STRUCTURE_RETENTION,
    "relation_kept": DIMENSION_STATE_STRUCTURE_RETENTION,
    "relation_retention": DIMENSION_STATE_STRUCTURE_RETENTION,
    "emotion_temperature": DIMENSION_EMOTION_TEMPERATURE_RETENTION,
    "emotion_temperature_retention": DIMENSION_EMOTION_TEMPERATURE_RETENTION,
    "emotion-temperature-retention": DIMENSION_EMOTION_TEMPERATURE_RETENTION,
    "temperature_retention": DIMENSION_EMOTION_TEMPERATURE_RETENTION,
    "emotion_focus_retention": DIMENSION_EMOTION_TEMPERATURE_RETENTION,
    "follow": DIMENSION_FOLLOW_DEPTH,
    "follow_depth": DIMENSION_FOLLOW_DEPTH,
    "follow-depth": DIMENSION_FOLLOW_DEPTH,
    "reception_depth": DIMENSION_FOLLOW_DEPTH,
    "human_follow_depth": DIMENSION_FOLLOW_DEPTH,
    "evidence_boundary": DIMENSION_EVIDENCE_BOUNDARY,
    "evidence-boundary": DIMENSION_EVIDENCE_BOUNDARY,
    "evidence_bound": DIMENSION_EVIDENCE_BOUNDARY,
    "distance": DIMENSION_EVIDENCE_BOUNDARY,
    "tone_distance_stable": DIMENSION_EVIDENCE_BOUNDARY,
    "soft_inference": DIMENSION_SOFT_INFERENCE_SURFACE,
    "soft_inference_surface": DIMENSION_SOFT_INFERENCE_SURFACE,
    "soft-inference-surface": DIMENSION_SOFT_INFERENCE_SURFACE,
    "soft_surface": DIMENSION_SOFT_INFERENCE_SURFACE,
    "soft_expression": DIMENSION_SOFT_INFERENCE_SURFACE,
    "natural": DIMENSION_NATURALNESS,
    "naturalness": DIMENSION_NATURALNESS,
    "surface_naturalness": DIMENSION_NATURALNESS,
    "natural_but_not_template": DIMENSION_NON_TEMPLATE,
    "template": DIMENSION_NON_TEMPLATE,
    "non_template": DIMENSION_NON_TEMPLATE,
    "non-template": DIMENSION_NON_TEMPLATE,
    "non_template_surface": DIMENSION_NON_TEMPLATE,
    "insight": DIMENSION_INSIGHT_DELTA,
    "insight_delta": DIMENSION_INSIGHT_DELTA,
    "insight-delta": DIMENSION_INSIGHT_DELTA,
    "structure_insight_delta": DIMENSION_INSIGHT_DELTA,
    "structure_insight_candidate_quality": DIMENSION_STRUCTURE_INSIGHT_CANDIDATE_QUALITY,
    "structure-insight-candidate-quality": DIMENSION_STRUCTURE_INSIGHT_CANDIDATE_QUALITY,
    "insight_candidate_quality": DIMENSION_STRUCTURE_INSIGHT_CANDIDATE_QUALITY,
}

_VERDICT_SCORES: Final[dict[str, float]] = {
    "green": 1.0,
    "g": 1.0,
    "pass": 1.0,
    "passed": 1.0,
    "ok": 1.0,
    "product_pass": 1.0,
    "yellow": 0.65,
    "y": 0.65,
    "warn": 0.65,
    "warning": 0.65,
    "repair_required": 0.4,
    "repair": 0.4,
    "red": 0.0,
    "r": 0.0,
    "fail": 0.0,
    "failed": 0.0,
    "ng": 0.0,
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
        "candidate_body",
        "body",
        "text",
    }
)

_FORBIDDEN_TRUE_FLAGS: Final[tuple[str, ...]] = (
    "raw_input_included",
    "raw_text_included",
    "comment_text_included",
    "comment_text_body_included",
    "candidate_body_included",
    "machine_metrics_used_for_read_feeling",
    "read_feeling_auto_filled_from_machine_metrics",
    "read_feeling_auto_estimation_allowed",
    "display_gate_relaxed",
    "grounding_gate_relaxed",
    "reader_gate_relaxed",
    "template_gate_relaxed",
    "gate_relaxed",
    "public_status_extended",
    "observation_status_enum_extended",
    "response_shape_changed",
    "public_response_key_change",
    "public_response_key_added",
    "api_route_changed",
    "db_physical_name_changed",
    "rn_visible_contract_changed",
    "rn_visible_title_changed",
    "product_gate_ready",
    "product_gate_reached",
    "product_gate_public_release_applied",
    "public_release_applied",
    "product_quality_released",
    "comment_text_generated",
    "comment_text_key_written",
    "comment_text_written_by_scorecard",
    "fixed_sentence_template_used",
    "fixed_completed_sentence_template_added",
    "input_specific_template_added",
    "external_ai_used",
    "local_llm_used",
)

_HARD_FAIL_MARKERS: Final[tuple[str, ...]] = (
    "diagnosis",
    "diagnostic",
    "personality",
    "personality_claim",
    "cause_claim_without_evidence",
    "target_judgement_agreement",
    "other_person_intent_claim",
    "advice",
    "action_instruction",
    "raw_text_public_leak",
    "raw_input_public_leak",
    "comment_text_public_leak",
    "fixed_template_surface",
    "case_specific_runtime_branch",
    "gate_relaxed",
)

_MACHINE_METRIC_KEYS: Final[tuple[str, ...]] = (
    "display_reach_rate",
    "binding_pass_rate",
    "reason_coverage_rate",
    "template_major_count",
    "safety_major_count",
    "surface_signature_repeat_rate",
    "connector_repetition_rate",
    "grammar_warning_rate",
    "surface_template_major_count",
    "public_text_payload_leak_count",
)


def _clean(value: Any) -> str:
    return str(value or "").strip()


def _clean_key(value: Any) -> str:
    return _clean(value).lower().replace("-", "_")


def _safe_mapping(value: Any) -> dict[str, Any]:
    if isinstance(value, Mapping):
        return {str(k): v for k, v in value.items()}
    return {}


def _listify(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return list(value)
    if isinstance(value, tuple) or isinstance(value, set):
        return list(value)
    return [value]


def _dedupe(values: Iterable[Any] | Any | None) -> list[str]:
    seen: set[str] = set()
    result: list[str] = []
    for item in _listify(values):
        text = _clean(item)
        if not text or text in seen:
            continue
        seen.add(text)
        result.append(text)
    return result


def _safe_float(value: Any) -> float | None:
    try:
        if value is None or value == "":
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def _safe_int(value: Any, default: int = 0) -> int:
    try:
        if value is None or value == "":
            return default
        return int(float(value))
    except (TypeError, ValueError):
        return default


def _avg(values: Iterable[Any]) -> float | None:
    scores: list[float] = []
    for value in values:
        score = _safe_float(value)
        if score is not None:
            scores.append(max(0.0, min(1.0, score)))
    if not scores:
        return None
    return round(sum(scores) / len(scores), 4)


def _rate(numerator: int, denominator: int) -> float:
    if denominator <= 0:
        return 0.0
    return round(max(0.0, min(1.0, float(numerator) / float(denominator))), 4)


def _score_from_verdict(value: Any) -> float | None:
    key = _clean_key(value)
    if key in _VERDICT_SCORES:
        return _VERDICT_SCORES[key]
    score = _safe_float(value)
    if score is None:
        return None
    return max(0.0, min(1.0, score))


def _verdict_from_score(score: float | None) -> str:
    if score is None:
        return VERDICT_NOT_EVALUATED
    if score >= 0.90:
        return VERDICT_PASS
    if score >= 0.65:
        return VERDICT_YELLOW
    if score > 0.0:
        return VERDICT_REPAIR_REQUIRED
    return VERDICT_RED


def _contains_text_payload_key(value: Any) -> bool:
    if isinstance(value, Mapping):
        for key, item in value.items():
            if str(key) in _TEXT_PAYLOAD_KEYS:
                return True
            if _contains_text_payload_key(item):
                return True
    elif isinstance(value, (list, tuple)):
        return any(_contains_text_payload_key(item) for item in value)
    return False


def _strip_text_payload_keys(value: Any) -> Any:
    if isinstance(value, Mapping):
        result: dict[str, Any] = {}
        for key, item in value.items():
            key_text = str(key)
            if key_text in _TEXT_PAYLOAD_KEYS:
                continue
            result[key_text] = _strip_text_payload_keys(item)
        return result
    if isinstance(value, list):
        return [_strip_text_payload_keys(item) for item in value]
    if isinstance(value, tuple):
        return [_strip_text_payload_keys(item) for item in value]
    return value


def assert_product_readfeel_rubric_meta_only(value: Any, *, source: str = "product_readfeel_rubric") -> None:
    """Raise when a Product Read Feel rubric payload keeps unsafe text or contract mutations."""

    if _contains_text_payload_key(value):
        raise ValueError(f"{source}: raw input/comment display body key must not be retained")
    if isinstance(value, Mapping):
        for key in _FORBIDDEN_TRUE_FLAGS:
            if value.get(key) is True:
                raise ValueError(f"{source}: forbidden true flag {key}")
        for item in value.values():
            assert_product_readfeel_rubric_meta_only(item, source=source)
    elif isinstance(value, (list, tuple)):
        for item in value:
            assert_product_readfeel_rubric_meta_only(item, source=source)


def build_product_readfeel_rubric() -> dict[str, Any]:
    """Return the fixed Phase 2 Product Read Feel rubric candidate."""

    rubric = {
        "version": PRODUCT_READFEEL_RUBRIC_VERSION,
        "schema_version": PRODUCT_READFEEL_RUBRIC_VERSION,
        "source": PRODUCT_READFEEL_RUBRIC_SOURCE,
        "step": PRODUCT_READFEEL_RUBRIC_PHASE2_STEP,
        "target_step": "ProductReadFeel_v1",
        "rubric_type": "product_readfeel_v1_blind_qa_ratings_only",
        "phase2_product_readfeel_rubric_design_confirmed": True,
        "implementation_decision": PRODUCT_READFEEL_RUBRIC_IMPLEMENTATION_DECISION,
        "existing_scorecard_connection": "attach_prefixed_fields_without_replacing_step6_machine_metrics",
        "existing_scorecard_direct_dimension_mutation": False,
        "scorecard_projection_allowed": True,
        "machine_metrics_separated_from_blind_qa": True,
        "machine_metrics_are_separate": True,
        "read_feeling_requires_blind_qa": True,
        "machine_metrics_used_for_read_feeling": False,
        "read_feeling_auto_filled_from_machine_metrics": False,
        "read_feeling_auto_estimation_allowed": False,
        "read_feeling_connection_target": PRODUCT_READFEEL_CONNECTION_READ_FEELING_TARGET,
        "read_feeling_product_target": PRODUCT_READFEEL_PRODUCT_READ_FEELING_TARGET,
        "rating_source_policy": {
            "machine_metrics_used_for_read_feeling": False,
            "read_feeling_auto_filled_from_machine_metrics": False,
            "read_feeling_auto_estimation_allowed": False,
            "read_feeling_source": "blind_qa_review_rating",
        },
        "dimension_source_policy": {
            "blind_qa_only_dimensions": list(PRODUCT_READFEEL_RATING_DIMENSIONS),
            "machine_metric_names": list(_MACHINE_METRIC_KEYS),
            "machine_metrics_used_for_read_feeling": False,
            "read_feeling_auto_filled_from_machine_metrics": False,
            "read_feeling_auto_estimation_allowed": False,
        },
        "v1_dimension_target": PRODUCT_READFEEL_V1_DIMENSION_TARGET,
        "v2_insight_ready_target": PRODUCT_READFEEL_V2_INSIGHT_READY_TARGET,
        "read_feeling_definition": (
            "Product Read Feel v1: input-specific state structure, emotion temperature, "
            "and follow depth are present, so the reply does not feel roughly processed."
        ),
        "required_dimensions": list(PRODUCT_READFEEL_V1_REQUIRED_DIMENSIONS),
        "required_v1_dimensions": list(PRODUCT_READFEEL_V1_REQUIRED_DIMENSIONS),
        "v1_required_dimensions": list(PRODUCT_READFEEL_V1_REQUIRED_DIMENSIONS),
        "optional_v2_dimensions": list(PRODUCT_READFEEL_V2_OPTIONAL_DIMENSIONS),
        "v2_candidate_dimensions": list(PRODUCT_READFEEL_V2_OPTIONAL_DIMENSIONS),
        "dimensions": {
            DIMENSION_READ_FEELING: {
                "scope": "blind_qa_only",
                "machine_metric_fill_forbidden": True,
                "green": "input_specific_structure_temperature_and_follow_depth_are_felt",
                "yellow": "displayable_but_somewhat_generic_or_shallow",
                "red": "generic_comfort_summary_only_or_unread_feeling",
            },
            DIMENSION_SELF_REPORT_RETENTION: {
                "scope": "blind_qa_rating",
                "green": "important_declared_material_slots_are_reflected",
                "yellow": "main_material_is_present_but_some_slot_weight_is_weak",
                "red": "selected_emotion_action_category_or_key_reaction_is_missing",
            },
            DIMENSION_STATE_STRUCTURE_RETENTION: {
                "scope": "blind_qa_rating",
                "green": "multiple_input_materials_are_rearranged_as_relation_not_flat_summary",
                "yellow": "relation_is_partly_visible_but_still_shallow",
                "red": "long_or_structural_input_is_crushed_to_one_emotion_or_recap",
            },
            DIMENSION_EMOTION_TEMPERATURE_RETENTION: {
                "scope": "blind_qa_rating",
                "green": "anger_fear_relief_joy_or_exhaustion_temperature_remains",
                "yellow": "emotion_is_named_but_temperature_is_weak",
                "red": "emotion_temperature_is_erased_or_shifted_to_wrong_focus",
            },
            DIMENSION_FOLLOW_DEPTH: {
                "scope": "blind_qa_rating",
                "green": "follow_chooses_the_important_weight_and_receives_it_warmly",
                "yellow": "kind_but_somewhat_generic_or_rephrased",
                "red": "template_comfort_or_mechanical_restating",
            },
            DIMENSION_EVIDENCE_BOUNDARY: {
                "scope": "blind_qa_boundary_rating",
                "green": "claims_stay_within_current_input_or_safe_known_user_fact",
                "yellow": "slightly_strong_but_not_unsafe",
                "red": "diagnosis_personality_cause_target_judgement_or_advice",
            },
            DIMENSION_SOFT_INFERENCE_SURFACE: {
                "scope": "blind_qa_boundary_rating",
                "green": "insight_or_relation_uses_soft_observation_surface",
                "yellow": "surface_is_mostly_soft_but_a_little_direct",
                "red": "hard_assertion_or_overclaim_surface",
            },
            DIMENSION_NATURALNESS: {
                "scope": "blind_qa_rating",
                "green": "natural_japanese_without_section_or_particle_breakage",
                "yellow": "readable_but_somewhat_stiff",
                "red": "malformed_label_order_breakage_or_fragmented_surface",
            },
            DIMENSION_NON_TEMPLATE: {
                "scope": "blind_qa_and_long_run_rating",
                "green": "not_fixed_opening_closing_or_repeated_signature",
                "yellow": "some_similarity_but_not_fixed_fallback",
                "red": "fixed_template_raw_echo_or_role_skeleton",
            },
            DIMENSION_INSIGHT_DELTA: {
                "scope": "optional_v2_readiness_rating",
                "green": "safe_relation_between_user_materials_goes_beyond_recap",
                "yellow": "insight_seed_exists_but_is_not_ready_as_strong_requirement",
                "red": "sufficient_material_exists_but_only_recap_or_summary_is_returned",
            },
            DIMENSION_STRUCTURE_INSIGHT_CANDIDATE_QUALITY: {
                "scope": "optional_v2_readiness_rating",
                "green": "candidate_has_evidence_slots_soft_strength_and_forbidden_claims",
                "yellow": "candidate_is_promising_but_evidence_or_surface_policy_is_incomplete",
                "red": "candidate_depends_on_general_theory_diagnosis_personality_or_cause_claim",
            },
        },
        "hard_fail_conditions": [
            "diagnosis",
            "personality_claim",
            "cause_claim_without_evidence",
            "target_judgement_agreement",
            "other_person_intent_claim",
            "advice_or_action_instruction",
            "fixed_template_surface",
            "case_specific_runtime_branch",
            "public_text_payload_leak",
        ],
        "completion_conditions": {
            "read_feeling_expanded_to_product_readfeel_v1": True,
            "candidate_dimensions_added": True,
            "new_rubric_module_selected_after_file_review": True,
            "existing_scorecard_projection_selected": True,
            "machine_metrics_and_blind_qa_separated": True,
            "read_feeling_machine_auto_fill_disabled": True,
            "public_meta_text_payload_excluded": True,
        },
        "exact_comment_text_required": False,
        "examples_are_runtime_templates": False,
        "runtime_branching_uses_fixture_strings": False,
        "fixture_text_used_for_runtime_branching": False,
        "public_text_payload_excluded": True,
        "raw_input_included": False,
        "raw_text_included": False,
        "comment_text_included": False,
        "comment_text_body_included": False,
        "candidate_body_included": False,
        "comment_text_generated": False,
        "comment_text_key_written": False,
        "comment_text_written_by_scorecard": False,
        "response_shape_changed": False,
        "public_response_key_change": False,
        "public_response_key_added": False,
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
        "external_ai_used": False,
        "local_llm_used": False,
    }
    assert_product_readfeel_rubric_meta_only(rubric, source="product_readfeel_rubric")
    return rubric


def _ratings_from_review(data: Mapping[str, Any]) -> dict[str, Any]:
    ratings = (
        _safe_mapping(data.get("ratings"))
        or _safe_mapping(data.get("dimension_ratings"))
        or _safe_mapping(data.get("product_readfeel_ratings"))
        or _safe_mapping(data.get("blind_qa_ratings"))
    )
    if ratings:
        return ratings
    return {key: value for key, value in data.items() if _DIMENSION_ALIASES.get(_clean_key(key))}


def _score_dimensions(ratings: Mapping[str, Any]) -> tuple[dict[str, float | None], dict[str, str]]:
    scores: dict[str, float | None] = {dimension: None for dimension in PRODUCT_READFEEL_RATING_DIMENSIONS}
    verdicts: dict[str, str] = {dimension: VERDICT_NOT_EVALUATED for dimension in PRODUCT_READFEEL_RATING_DIMENSIONS}
    for raw_key, raw_value in ratings.items():
        dimension = _DIMENSION_ALIASES.get(_clean_key(raw_key))
        if not dimension:
            continue
        score = _score_from_verdict(raw_value)
        if score is None:
            continue
        scores[dimension] = score
        verdicts[dimension] = _verdict_from_score(score)
    return scores, verdicts


def _has_hard_fail(values: Iterable[Any] | Any | None) -> bool:
    joined = " ".join(_clean(value).lower() for value in _listify(values))
    return any(marker in joined for marker in _HARD_FAIL_MARKERS)


def _v1_verdict(scores: Mapping[str, float | None], *, hard_fail: bool) -> str:
    if hard_fail:
        return VERDICT_RED
    evaluated_scores = [scores.get(dimension) for dimension in PRODUCT_READFEEL_V1_RATING_DIMENSIONS]
    if all(score is None for score in evaluated_scores):
        return VERDICT_NOT_EVALUATED
    if any(score == 0.0 for score in evaluated_scores if score is not None):
        return VERDICT_RED
    read_score = scores.get(DIMENSION_READ_FEELING)
    v1_score = _avg(evaluated_scores)
    if read_score is None or v1_score is None:
        return VERDICT_NOT_EVALUATED
    if read_score >= PRODUCT_READFEEL_PRODUCT_READ_FEELING_TARGET and v1_score >= PRODUCT_READFEEL_PRODUCT_READ_FEELING_TARGET:
        if all((scores.get(dimension) or 0.0) >= PRODUCT_READFEEL_V1_DIMENSION_TARGET for dimension in PRODUCT_READFEEL_V1_RATING_DIMENSIONS if scores.get(dimension) is not None):
            return VERDICT_PASS
    if v1_score >= PRODUCT_READFEEL_V1_DIMENSION_TARGET:
        return VERDICT_YELLOW
    return VERDICT_REPAIR_REQUIRED


def _v2_verdict(scores: Mapping[str, float | None], *, v1_verdict: str, hard_fail: bool) -> str:
    if hard_fail or v1_verdict == VERDICT_RED:
        return VERDICT_RED
    insight_score = scores.get(DIMENSION_INSIGHT_DELTA)
    candidate_score = scores.get(DIMENSION_STRUCTURE_INSIGHT_CANDIDATE_QUALITY)
    if insight_score is None and candidate_score is None:
        return VERDICT_NOT_EVALUATED
    score = _avg((insight_score, candidate_score))
    if score is None:
        return VERDICT_NOT_EVALUATED
    if score >= PRODUCT_READFEEL_V2_INSIGHT_READY_TARGET:
        return VERDICT_STRUCTURE_INSIGHT_READY
    if score >= PRODUCT_READFEEL_V1_DIMENSION_TARGET:
        return VERDICT_YELLOW
    if score > 0.0:
        return VERDICT_REPAIR_REQUIRED
    return VERDICT_RED


def normalize_product_readfeel_blind_qa_review(review: Mapping[str, Any] | None) -> dict[str, Any]:
    """Normalize a ratings-only Product Read Feel Blind QA review.

    The returned payload contains reviewer scores and safe identifiers only.  It
    strips raw input and rendered display bodies before any aggregation.
    """

    source = _safe_mapping(review)
    source_text_payload_seen = _contains_text_payload_key(source)
    data = _strip_text_payload_keys(source)
    ratings = _ratings_from_review(data)
    dimension_scores, dimension_verdicts = _score_dimensions(ratings)
    v1_scores = [dimension_scores.get(dimension) for dimension in PRODUCT_READFEEL_V1_RATING_DIMENSIONS]
    v2_scores = [dimension_scores.get(dimension) for dimension in PRODUCT_READFEEL_V2_CANDIDATE_DIMENSIONS]
    red_flags = _dedupe(data.get("red_flags") or data.get("hard_fail_conditions") or data.get("hard_fails"))
    repair_reasons = _dedupe(data.get("repair_reasons") or data.get("repair_reason_codes") or data.get("reasons"))
    hard_fail = _has_hard_fail([*red_flags, *repair_reasons])
    v1_verdict = _v1_verdict(dimension_scores, hard_fail=hard_fail)
    v2_verdict = _v2_verdict(dimension_scores, v1_verdict=v1_verdict, hard_fail=hard_fail)
    read_score = dimension_scores.get(DIMENSION_READ_FEELING)
    missing_v1_dimensions = [
        dimension for dimension in PRODUCT_READFEEL_V1_REQUIRED_DIMENSIONS if dimension_scores.get(dimension) is None
    ]
    missing_v2_dimensions = [
        dimension for dimension in PRODUCT_READFEEL_V2_OPTIONAL_DIMENSIONS if dimension_scores.get(dimension) is None
    ]
    product_readfeel_v1_pass = v1_verdict in {VERDICT_PASS, VERDICT_PRODUCT_PASS}
    structure_insight_v2_ready = v2_verdict == VERDICT_STRUCTURE_INSIGHT_READY
    item = {
        "version": PRODUCT_READFEEL_BLIND_QA_REVIEW_VERSION,
        "schema_version": PRODUCT_READFEEL_BLIND_QA_REVIEW_VERSION,
        "source_step": PRODUCT_READFEEL_RUBRIC_PHASE2_STEP,
        "target_step": "ProductReadFeel_v1",
        "review_id": _clean(data.get("review_id")) or _clean(data.get("id")),
        "candidate_id": _clean(data.get("candidate_id")) or _clean(data.get("row_id")) or _clean(data.get("trace_id")) or _clean(data.get("emotion_log_id")),
        "fixture_family": _clean(data.get("fixture_family")) or _clean(data.get("product_readfeel_family")),
        "product_readfeel_family": _clean(data.get("product_readfeel_family")) or _clean(data.get("fixture_family")) or _clean(data.get("coverage_group")),
        "coverage_group": _clean(data.get("coverage_group")),
        "reviewer_kind": _clean(data.get("reviewer_kind")) or "human_blind_qa",
        "dimension_scores": dimension_scores,
        "dimension_verdicts": dimension_verdicts,
        "v1_score": _avg(v1_scores),
        "v2_score": _avg(v2_scores),
        "read_feeling_score": read_score,
        "read_feeling_source": "blind_qa_review_ratings" if read_score is not None else "blind_qa_required_not_evaluated",
        "self_report_retention_score": dimension_scores.get(DIMENSION_SELF_REPORT_RETENTION),
        "state_structure_retention_score": dimension_scores.get(DIMENSION_STATE_STRUCTURE_RETENTION),
        "emotion_temperature_retention_score": dimension_scores.get(DIMENSION_EMOTION_TEMPERATURE_RETENTION),
        "follow_depth_score": dimension_scores.get(DIMENSION_FOLLOW_DEPTH),
        "insight_delta_score": dimension_scores.get(DIMENSION_INSIGHT_DELTA),
        "red_flags": red_flags,
        "repair_reasons": repair_reasons,
        "hard_fail_detected": hard_fail,
        "v1_verdict": v1_verdict,
        "v2_verdict": v2_verdict,
        "missing_v1_dimensions": missing_v1_dimensions,
        "missing_required_dimensions": missing_v1_dimensions,
        "missing_v2_dimensions": missing_v2_dimensions,
        "product_readfeel_v1_pass": product_readfeel_v1_pass,
        "product_readfeel_v1_product_pass_candidate": product_readfeel_v1_pass,
        "structure_insight_v2_ready_candidate": structure_insight_v2_ready,
        "v2_insight_delta_release_blocker": False,
        "source_text_payload_seen": source_text_payload_seen,
        "source_text_payload_retained": False,
        "ratings_only_payload": True,
        "machine_metrics_separated_from_blind_qa": True,
        "machine_metrics_used_for_read_feeling": False,
        "read_feeling_auto_filled_from_machine_metrics": False,
        "read_feeling_auto_estimation_allowed": False,
        "exact_comment_text_required": False,
        "public_text_payload_excluded": True,
        "raw_input_included": False,
        "raw_text_included": False,
        "comment_text_included": False,
        "comment_text_body_included": False,
        "candidate_body_included": False,
        "comment_text_generated": False,
        "comment_text_key_written": False,
        "comment_text_written_by_scorecard": False,
        "response_shape_changed": False,
        "public_response_key_change": False,
        "public_response_key_added": False,
        "product_gate_ready": False,
        "public_release_applied": False,
    }
    assert_product_readfeel_rubric_meta_only(item, source="product_readfeel_blind_qa_review")
    return item


def aggregate_product_readfeel_blind_qa_reviews(
    reviews: Sequence[Mapping[str, Any] | None] | Iterable[Mapping[str, Any] | None] | None = None,
) -> dict[str, Any]:
    normalized = [normalize_product_readfeel_blind_qa_review(review) for review in list(reviews or [])]
    dimension_scores: dict[str, float | None] = {}
    dimension_pass_rates: dict[str, float] = {}
    review_count = len(normalized)
    for dimension in PRODUCT_READFEEL_RATING_DIMENSIONS:
        scores = [(item.get("dimension_scores") or {}).get(dimension) for item in normalized]
        present_scores = [score for score in scores if score is not None]
        dimension_scores[dimension] = _avg(present_scores)
        dimension_pass_rates[dimension] = _rate(
            sum(1 for score in present_scores if float(score) >= PRODUCT_READFEEL_V1_DIMENSION_TARGET),
            len(present_scores),
        )
    read_scores = [item.get("read_feeling_score") for item in normalized if item.get("read_feeling_score") is not None]
    insight_scores = [(item.get("dimension_scores") or {}).get(DIMENSION_INSIGHT_DELTA) for item in normalized]
    v1_scores = [item.get("v1_score") for item in normalized if item.get("v1_score") is not None]
    v2_scores = [item.get("v2_score") for item in normalized if item.get("v2_score") is not None]
    v1_pass_count = sum(1 for item in normalized if item.get("v1_verdict") in {VERDICT_PASS, VERDICT_PRODUCT_PASS})
    v2_ready_count = sum(1 for item in normalized if item.get("v2_verdict") == VERDICT_STRUCTURE_INSIGHT_READY)
    red_review_count = sum(1 for item in normalized if item.get("v1_verdict") == VERDICT_RED)
    read_feeling_score = _avg(read_scores)
    insight_delta_score = _avg(score for score in insight_scores if score is not None)
    aggregate = {
        "version": PRODUCT_READFEEL_BLIND_QA_AGGREGATE_VERSION,
        "schema_version": PRODUCT_READFEEL_BLIND_QA_AGGREGATE_VERSION,
        "source_step": PRODUCT_READFEEL_RUBRIC_PHASE2_STEP,
        "target_step": "ProductReadFeel_v1",
        "phase2_product_readfeel_rubric_ready": True,
        "product_readfeel_phase2_ready": True,
        "product_readfeel_rubric_ready": True,
        "implementation_decision": PRODUCT_READFEEL_RUBRIC_IMPLEMENTATION_DECISION,
        "blind_qa_ready": bool(normalized),
        "review_count": review_count,
        "v1_pass_count": v1_pass_count,
        "v1_pass_rate": round(v1_pass_count / review_count, 4) if review_count else 0.0,
        "v1_product_pass_candidate_rate": round(v1_pass_count / review_count, 4) if review_count else 0.0,
        "v2_structure_insight_ready_count": v2_ready_count,
        "v2_structure_insight_ready_candidate_rate": round(v2_ready_count / review_count, 4) if review_count else 0.0,
        "v2_structure_insight_ready_rate": round(v2_ready_count / review_count, 4) if review_count else 0.0,
        "missing_required_dimension_counts": {
            dimension: sum(1 for review in normalized if dimension in (review.get("missing_required_dimensions") or []))
            for dimension in PRODUCT_READFEEL_V1_REQUIRED_DIMENSIONS
        },
        "red_review_count": red_review_count,
        "read_feeling_score": read_feeling_score,
        "read_feeling_source": "blind_qa_review_ratings" if read_scores else "blind_qa_required_not_evaluated",
        "read_feeling_product_target": PRODUCT_READFEEL_PRODUCT_READ_FEELING_TARGET,
        "read_feeling_product_target_met": bool(read_feeling_score is not None and read_feeling_score >= PRODUCT_READFEEL_PRODUCT_READ_FEELING_TARGET),
        "read_feeling_pass_rate": _rate(
            sum(1 for score in read_scores if float(score) >= PRODUCT_READFEEL_PRODUCT_READ_FEELING_TARGET),
            len(read_scores),
        ),
        "dimension_score_source": "blind_qa_review_ratings" if normalized else "blind_qa_required_not_evaluated",
        "v1_score": _avg(v1_scores),
        "v2_score": _avg(v2_scores),
        "dimension_scores": dimension_scores,
        "dimension_pass_rates": dimension_pass_rates,
        "self_report_retention_score": dimension_scores.get(DIMENSION_SELF_REPORT_RETENTION),
        "state_structure_retention_score": dimension_scores.get(DIMENSION_STATE_STRUCTURE_RETENTION),
        "emotion_temperature_retention_score": dimension_scores.get(DIMENSION_EMOTION_TEMPERATURE_RETENTION),
        "follow_depth_score": dimension_scores.get(DIMENSION_FOLLOW_DEPTH),
        "insight_delta_score": insight_delta_score,
        "v1_product_pass_candidate": bool(
            normalized
            and read_feeling_score is not None
            and read_feeling_score >= PRODUCT_READFEEL_PRODUCT_READ_FEELING_TARGET
            and red_review_count == 0
        ),
        "v2_structure_insight_ready_candidate": bool(
            normalized
            and insight_delta_score is not None
            and insight_delta_score >= PRODUCT_READFEEL_V2_INSIGHT_READY_TARGET
            and red_review_count == 0
        ),
        "reviews": normalized,
        "machine_metrics_separated_from_blind_qa": True,
        "machine_metrics_used_for_read_feeling": False,
        "read_feeling_auto_filled_from_machine_metrics": False,
        "read_feeling_auto_estimation_allowed": False,
        "public_text_payload_excluded": True,
        "raw_input_included": False,
        "raw_text_included": False,
        "comment_text_included": False,
        "comment_text_body_included": False,
        "candidate_body_included": False,
        "comment_text_generated": False,
        "comment_text_key_written": False,
        "comment_text_written_by_scorecard": False,
        "product_gate_ready": False,
        "public_release_applied": False,
    }
    assert_product_readfeel_rubric_meta_only(aggregate, source="product_readfeel_blind_qa_aggregate")
    return aggregate


build_product_readfeel_blind_qa_aggregate = aggregate_product_readfeel_blind_qa_reviews
build_product_readfeel_rubric_scorecard = aggregate_product_readfeel_blind_qa_reviews


def normalize_product_readfeel_machine_metrics_boundary(machine_metrics: Mapping[str, Any] | None = None) -> dict[str, Any]:
    """Return the machine side of Phase 2 without deriving read_feeling."""

    data = _strip_text_payload_keys(_safe_mapping(machine_metrics))
    metrics: dict[str, Any] = {
        "machine_metrics_ready": bool(data),
        "machine_metric_keys": list(_MACHINE_METRIC_KEYS),
        "read_feeling_score": None,
        "read_feeling_source": "blind_qa_required_not_machine_metric",
        "read_feeling_requires_blind_qa": True,
        "machine_metrics_separated_from_blind_qa": True,
        "machine_metrics_used_for_read_feeling": False,
        "read_feeling_auto_filled_from_machine_metrics": False,
        "read_feeling_auto_estimation_allowed": False,
    }
    for key in _MACHINE_METRIC_KEYS:
        if key in data:
            metrics[key] = data.get(key)
    metrics.update(
        {
            "public_text_payload_excluded": True,
            "raw_input_included": False,
            "raw_text_included": False,
            "comment_text_included": False,
            "comment_text_body_included": False,
            "candidate_body_included": False,
            "comment_text_generated": False,
            "comment_text_key_written": False,
            "comment_text_written_by_scorecard": False,
            "product_gate_ready": False,
            "public_release_applied": False,
        }
    )
    assert_product_readfeel_rubric_meta_only(metrics, source="product_readfeel_machine_metrics_boundary")
    return metrics


def build_product_readfeel_rubric_phase2_material(
    *,
    machine_metrics: Mapping[str, Any] | None = None,
    blind_qa_reviews: Sequence[Mapping[str, Any] | None] | Iterable[Mapping[str, Any] | None] | None = None,
    phase1_inventory_fields: Mapping[str, Any] | None = None,
    run_id: str = "",
) -> dict[str, Any]:
    """Build Phase 2 material confirming the Product Read Feel rubric choice."""

    rubric = build_product_readfeel_rubric()
    machine = normalize_product_readfeel_machine_metrics_boundary(machine_metrics)
    blind_qa = aggregate_product_readfeel_blind_qa_reviews(blind_qa_reviews)
    phase1_fields = _strip_text_payload_keys(_safe_mapping(phase1_inventory_fields))
    completion_conditions = {
        "phase1_inventory_available": bool(phase1_fields),
        "read_feeling_expanded_to_product_readfeel_v1": True,
        "candidate_dimensions_added": True,
        "new_rubric_module_selected_after_file_review": True,
        "existing_scorecard_projection_selected": True,
        "machine_metrics_and_blind_qa_separated": True,
        "read_feeling_machine_auto_fill_disabled": True,
        "public_meta_text_payload_excluded": True,
    }
    material = {
        "version": PRODUCT_READFEEL_RUBRIC_PHASE2_MATERIAL_VERSION,
        "schema_version": PRODUCT_READFEEL_RUBRIC_PHASE2_MATERIAL_VERSION,
        "source": PRODUCT_READFEEL_RUBRIC_SOURCE,
        "step": PRODUCT_READFEEL_RUBRIC_PHASE2_STEP,
        "target_step": "ProductReadFeel_v1",
        "run_id": _clean(run_id),
        "phase2_product_readfeel_rubric_design_confirmed": all(completion_conditions.values()),
        "product_readfeel_rubric_ready": True,
        "implementation_decision": PRODUCT_READFEEL_RUBRIC_IMPLEMENTATION_DECISION,
        "completion_conditions": completion_conditions,
        "rubric": rubric,
        "machine_metrics": machine,
        "blind_qa_metrics": blind_qa,
        "phase1_inventory_fields_seen": bool(phase1_fields),
        "phase1_inventory_ready": bool(
            phase1_fields.get("phase1_product_readfeel_current_output_inventory_ready")
            or phase1_fields.get("product_readfeel_phase1_ready")
        ),
        "read_feeling_score": blind_qa.get("read_feeling_score"),
        "read_feeling_source": blind_qa.get("read_feeling_source"),
        "self_report_retention_score": blind_qa.get("self_report_retention_score"),
        "state_structure_retention_score": blind_qa.get("state_structure_retention_score"),
        "emotion_temperature_retention_score": blind_qa.get("emotion_temperature_retention_score"),
        "follow_depth_score": blind_qa.get("follow_depth_score"),
        "insight_delta_score": blind_qa.get("insight_delta_score"),
        "machine_metrics_separated_from_blind_qa": True,
        "read_feeling_requires_blind_qa": True,
        "machine_metrics_used_for_read_feeling": False,
        "read_feeling_auto_filled_from_machine_metrics": False,
        "read_feeling_auto_estimation_allowed": False,
        "public_text_payload_excluded": True,
        "raw_input_included": False,
        "raw_text_included": False,
        "comment_text_included": False,
        "comment_text_body_included": False,
        "candidate_body_included": False,
        "comment_text_generated": False,
        "comment_text_key_written": False,
        "comment_text_written_by_scorecard": False,
        "response_shape_changed": False,
        "public_response_key_change": False,
        "public_response_key_added": False,
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
        "external_ai_used": False,
        "local_llm_used": False,
    }
    assert_product_readfeel_rubric_meta_only(material, source="product_readfeel_rubric_phase2_material")
    return material


def normalize_product_readfeel_rubric_to_scorecard_fields(
    rubric_or_aggregate: Mapping[str, Any] | None,
    blind_qa_aggregate: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Project the Phase 2 rubric/Blind QA aggregate into scorecard-safe fields.

    Existing scorecard callers pass ``(rubric, blind_qa_aggregate)`` while new
    callers may pass only the aggregate because it already embeds the rubric.
    Both forms are supported to keep Phase 2 additive and non-breaking.
    """

    first = _safe_mapping(rubric_or_aggregate)
    second = _safe_mapping(blind_qa_aggregate)
    if second:
        rubric = first or build_product_readfeel_rubric()
        data = second
    elif first.get("version") == PRODUCT_READFEEL_RUBRIC_VERSION or first.get("rubric_type"):
        rubric = first
        data = build_product_readfeel_blind_qa_aggregate(reviews=[])
    else:
        data = first or build_product_readfeel_blind_qa_aggregate(reviews=[])
        rubric = _safe_mapping(data.get("rubric")) or build_product_readfeel_rubric()

    assert_product_readfeel_rubric_meta_only(rubric, source="product_readfeel_rubric_scorecard_fields_rubric")
    assert_product_readfeel_rubric_meta_only(data, source="product_readfeel_rubric_scorecard_fields_source")

    missing_required_counts: dict[str, int] = {dimension: 0 for dimension in PRODUCT_READFEEL_V1_REQUIRED_DIMENSIONS}
    for review in data.get("reviews") or []:
        review_data = _safe_mapping(review)
        for dimension in review_data.get("missing_v1_dimensions") or []:
            key = _clean(dimension)
            if key in missing_required_counts:
                missing_required_counts[key] += 1

    product_readfeel_phase2_ready = bool(
        rubric.get("machine_metrics_are_separate") is True
        and rubric.get("read_feeling_auto_filled_from_machine_metrics") is False
        and data.get("machine_metrics_used_for_read_feeling") is False
        and data.get("read_feeling_auto_filled_from_machine_metrics") is False
    )
    fields = {
        "product_readfeel_scorecard_fields_version": PRODUCT_READFEEL_SCORECARD_FIELDS_VERSION,
        "product_readfeel_rubric_version": _clean(rubric.get("version")) or PRODUCT_READFEEL_RUBRIC_VERSION,
        "product_readfeel_rubric_step": _clean(rubric.get("step")) or PRODUCT_READFEEL_RUBRIC_STEP,
        "phase2_product_readfeel_rubric_ready": product_readfeel_phase2_ready,
        "product_readfeel_phase2_ready": product_readfeel_phase2_ready,
        "product_readfeel_rubric_ready": product_readfeel_phase2_ready,
        "product_readfeel_rubric_implementation_decision": PRODUCT_READFEEL_RUBRIC_IMPLEMENTATION_DECISION,
        "product_readfeel_blind_qa_ready": bool(data.get("blind_qa_ready")),
        "product_readfeel_blind_qa_review_count": int(data.get("review_count") or 0),
        "product_readfeel_rating_dimensions": list(rubric.get("rating_dimensions") or PRODUCT_READFEEL_RATING_DIMENSIONS),
        "product_readfeel_required_dimensions": list(
            rubric.get("v1_required_dimensions") or PRODUCT_READFEEL_V1_REQUIRED_DIMENSIONS
        ),
        "product_readfeel_required_v1_dimensions": list(
            rubric.get("v1_required_dimensions") or PRODUCT_READFEEL_V1_REQUIRED_DIMENSIONS
        ),
        "product_readfeel_v1_required_dimensions": list(
            rubric.get("v1_required_dimensions") or PRODUCT_READFEEL_V1_REQUIRED_DIMENSIONS
        ),
        "product_readfeel_optional_v2_dimensions": list(
            rubric.get("v2_candidate_dimensions") or PRODUCT_READFEEL_V2_CANDIDATE_DIMENSIONS
        ),
        "product_readfeel_v2_candidate_dimensions": list(
            rubric.get("v2_candidate_dimensions") or PRODUCT_READFEEL_V2_CANDIDATE_DIMENSIONS
        ),
        "product_readfeel_dimension_scores": dict(data.get("dimension_scores") or {}),
        "product_readfeel_read_feeling_score": data.get("read_feeling_score"),
        "product_readfeel_self_report_retention_score": data.get("self_report_retention_score"),
        "product_readfeel_state_structure_retention_score": data.get("state_structure_retention_score"),
        "product_readfeel_emotion_temperature_retention_score": data.get("emotion_temperature_retention_score"),
        "product_readfeel_follow_depth_score": data.get("follow_depth_score"),
        "product_readfeel_insight_delta_score": data.get("insight_delta_score"),
        "product_readfeel_v1_score": data.get("v1_score"),
        "product_readfeel_v1_product_readfeel_score": data.get("v1_score"),
        "product_readfeel_v1_pass_rate": data.get("v1_pass_rate"),
        "product_readfeel_v1_product_pass_rate": data.get("v1_pass_rate"),
        "product_readfeel_v1_product_pass_candidate_rate": data.get("v1_pass_rate"),
        "product_readfeel_read_feeling_pass_rate": data.get("read_feeling_pass_rate"),
        "product_readfeel_v2_structure_insight_ready_rate": data.get("v2_structure_insight_ready_candidate_rate"),
        "product_readfeel_structure_insight_ready_candidate_rate": data.get("v2_structure_insight_ready_candidate_rate"),
        "product_readfeel_v2_structure_insight_ready_candidate_rate": data.get(
            "v2_structure_insight_ready_candidate_rate"
        ),
        "product_readfeel_read_feeling_source": _clean(data.get("read_feeling_source")),
        "product_readfeel_dimension_score_source": _clean(data.get("dimension_score_source")),
        "product_readfeel_missing_required_dimension_counts": missing_required_counts,
        "product_readfeel_machine_metrics_separated_from_blind_qa": True,
        "product_readfeel_machine_metrics_and_blind_qa_separated": True,
        "product_readfeel_read_feeling_requires_blind_qa": True,
        "product_readfeel_machine_metrics_used_for_read_feeling": False,
        "product_readfeel_read_feeling_auto_filled_from_machine_metrics": False,
        "machine_metrics_used_for_read_feeling": False,
        "read_feeling_auto_filled_from_machine_metrics": False,
        "raw_input_included": False,
        "raw_text_included": False,
        "comment_text_included": False,
        "comment_text_body_included": False,
        "candidate_body_included": False,
        "response_shape_changed": False,
        "public_response_key_change": False,
        "api_route_changed": False,
        "db_physical_name_changed": False,
        "rn_visible_contract_changed": False,
        "rn_visible_title_changed": False,
        "product_gate_ready": False,
        "public_release_applied": False,
    }
    assert_product_readfeel_rubric_meta_only(fields, source="product_readfeel_rubric_scorecard_fields")
    return fields


def dump_product_readfeel_rubric_phase2_material(material: Mapping[str, Any] | None = None) -> str:
    data = dict(material or build_product_readfeel_rubric_phase2_material())
    assert_product_readfeel_rubric_meta_only(data)
    return json.dumps(data, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


__all__ = [
    "PRODUCT_READFEEL_RUBRIC_VERSION",
    "PRODUCT_READFEEL_RUBRIC_PHASE2_STEP",
    "PRODUCT_READFEEL_RUBRIC_STEP",
    "PRODUCT_READFEEL_RUBRIC_IMPLEMENTATION_DECISION",
    "PRODUCT_READFEEL_BLIND_QA_REVIEW_VERSION",
    "PRODUCT_READFEEL_BLIND_QA_AGGREGATE_VERSION",
    "PRODUCT_READFEEL_RUBRIC_PHASE2_MATERIAL_VERSION",
    "PRODUCT_READFEEL_RUBRIC_SCORECARD_FIELDS_VERSION",
    "PRODUCT_READFEEL_SCORECARD_FIELDS_VERSION",
    "PRODUCT_READFEEL_V1_RATING_DIMENSIONS",
    "PRODUCT_READFEEL_V1_REQUIRED_DIMENSIONS",
    "PRODUCT_READFEEL_V2_CANDIDATE_DIMENSIONS",
    "PRODUCT_READFEEL_V2_OPTIONAL_DIMENSIONS",
    "PRODUCT_READFEEL_RATING_DIMENSIONS",
    "DIMENSION_READ_FEELING",
    "DIMENSION_SELF_REPORT_RETENTION",
    "DIMENSION_STATE_STRUCTURE_RETENTION",
    "DIMENSION_EMOTION_TEMPERATURE_RETENTION",
    "DIMENSION_FOLLOW_DEPTH",
    "DIMENSION_EVIDENCE_BOUNDARY",
    "DIMENSION_SOFT_INFERENCE_SURFACE",
    "DIMENSION_NATURALNESS",
    "DIMENSION_NON_TEMPLATE",
    "DIMENSION_INSIGHT_DELTA",
    "DIMENSION_STRUCTURE_INSIGHT_CANDIDATE_QUALITY",
    "VERDICT_RED",
    "VERDICT_REPAIR_REQUIRED",
    "VERDICT_YELLOW",
    "VERDICT_PASS",
    "VERDICT_PRODUCT_PASS",
    "VERDICT_STRUCTURE_INSIGHT_READY",
    "VERDICT_NOT_EVALUATED",
    "assert_product_readfeel_rubric_meta_only",
    "build_product_readfeel_rubric",
    "normalize_product_readfeel_blind_qa_review",
    "aggregate_product_readfeel_blind_qa_reviews",
    "build_product_readfeel_blind_qa_aggregate",
    "build_product_readfeel_rubric_scorecard",
    "normalize_product_readfeel_machine_metrics_boundary",
    "build_product_readfeel_rubric_phase2_material",
    "normalize_product_readfeel_rubric_to_scorecard_fields",
    "dump_product_readfeel_rubric_phase2_material",
]
