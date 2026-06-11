# -*- coding: utf-8 -*-
from __future__ import annotations

"""P6-2 target-family and no-connect-family boundary for Structure Insight.

This module decides whether a family may become a limited Structure Insight
surface candidate, must stay meta-only, should hold, or must be blocked.  It is
body-free and never creates visible text, public response keys, DB fields, or
release flags.
"""

from collections.abc import Iterable, Mapping
import json
from typing import Any, Final


STRUCTURE_INSIGHT_P6_FAMILY_BOUNDARY_SCHEMA_VERSION: Final = (
    "cocolon.emlis.structure_insight.p6_family_boundary.v1"
)
STRUCTURE_INSIGHT_P6_FAMILY_BOUNDARY_SUMMARY_SCHEMA_VERSION: Final = (
    "cocolon.emlis.structure_insight.p6_family_boundary_summary.v1"
)
STRUCTURE_INSIGHT_P6_FAMILY_BOUNDARY_STEP: Final = "P6-2_TargetFamilyNoConnectBoundary"
STRUCTURE_INSIGHT_P6_FAMILY_BOUNDARY_SOURCE: Final = (
    "Cocolon_EmlisAI_P6_StructureInsight_TargetFamilyNoConnectBoundary_20260611"
)

DECISION_ALLOW_LIMITED_SURFACE: Final = "allow_limited_surface"
DECISION_META_ONLY: Final = "meta_only"
DECISION_HOLD: Final = "hold"
DECISION_BLOCK: Final = "block"

FAMILY_STRUCTURE_QUESTION: Final = "structure_question"
FAMILY_LONG_MEANING_ARC: Final = "long_meaning_arc"
FAMILY_SELF_UNDERSTANDING_FOLLOW: Final = "self_understanding_follow"
FAMILY_DAILY_UNPLEASANT: Final = "daily_unpleasant"
FAMILY_DAILY_POSITIVE: Final = "daily_positive"
FAMILY_POSITIVE_ONLY: Final = "positive_only"
FAMILY_LOW_INFORMATION: Final = "low_information"
FAMILY_LIMITED_GROUNDING: Final = "limited_grounding"
FAMILY_SAFETY_TRIAGE_REQUIRED: Final = "safety_triage_required"
FAMILY_EMERGENCY_SAFETY: Final = "emergency_safety"
FAMILY_TARGET_JUDGEMENT: Final = "target_judgement"
FAMILY_SELF_DENIAL_SAFETY_ADJACENT: Final = "self_denial_safety_adjacent"
FAMILY_ANGER_ATTACK_OR_TARGET_BLAME: Final = "anger_attack_or_target_blame"
FAMILY_SOURCE_UNAVAILABLE: Final = "source_unavailable"

MATERIAL_QUALITY_ELIGIBLE: Final = "eligible"
MATERIAL_QUALITY_LOW_INFORMATION: Final = "low_information"
MATERIAL_QUALITY_LIMITED_GROUNDING: Final = "limited_grounding"
MATERIAL_QUALITY_SAFETY_TRIAGE_REQUIRED: Final = "safety_triage_required"

P6_ALLOWED_TARGET_FAMILIES: Final[tuple[str, ...]] = (
    FAMILY_STRUCTURE_QUESTION,
    FAMILY_LONG_MEANING_ARC,
    FAMILY_SELF_UNDERSTANDING_FOLLOW,
)
P6_NO_CONNECT_FAMILIES: Final[tuple[str, ...]] = (
    FAMILY_DAILY_UNPLEASANT,
    FAMILY_DAILY_POSITIVE,
    FAMILY_POSITIVE_ONLY,
    FAMILY_LOW_INFORMATION,
    FAMILY_LIMITED_GROUNDING,
    FAMILY_SAFETY_TRIAGE_REQUIRED,
    FAMILY_EMERGENCY_SAFETY,
    FAMILY_TARGET_JUDGEMENT,
    FAMILY_SELF_DENIAL_SAFETY_ADJACENT,
    FAMILY_ANGER_ATTACK_OR_TARGET_BLAME,
    FAMILY_SOURCE_UNAVAILABLE,
)
P6_NO_CONNECT_MATERIAL_QUALITIES: Final[tuple[str, ...]] = (
    MATERIAL_QUALITY_LOW_INFORMATION,
    MATERIAL_QUALITY_LIMITED_GROUNDING,
    MATERIAL_QUALITY_SAFETY_TRIAGE_REQUIRED,
)

REASON_FAMILY_MISSING: Final = "family_missing"
REASON_FAMILY_NOT_IN_INITIAL_P6_SCOPE: Final = "family_not_in_initial_p6_scope"
REASON_NO_CONNECT_FAMILY: Final = "no_connect_family"
REASON_MATERIAL_QUALITY_NOT_CONFIRMED: Final = "material_quality_not_confirmed"
REASON_MATERIAL_QUALITY_NOT_CONNECTABLE: Final = "material_quality_not_connectable"
REASON_CURRENT_INPUT_GROUNDING_NOT_CONFIRMED: Final = "current_input_grounding_not_confirmed"
REASON_CURRENT_INPUT_EVIDENCE_INSUFFICIENT: Final = "current_input_evidence_insufficient"
REASON_OBSERVATION_STATUS_NOT_CONNECTABLE: Final = "observation_status_not_connectable"
REASON_OBSERVATION_STATUS_NOT_CONFIRMED: Final = "observation_status_not_confirmed"
REASON_BODY_GENERATED_BEFORE_GATE: Final = "body_generated_before_gate"
REASON_USER_DICTIONARY_FACT_ASSERTION_REQUIRED: Final = "user_dictionary_fact_assertion_required"
REASON_TARGET_JUDGEMENT_REQUIRED: Final = "target_judgement_required"
REASON_SAFETY_ADJACENT: Final = "safety_adjacent_family"
REASON_EMERGENCY_SAFETY: Final = "emergency_safety_family"
REASON_SOURCE_UNAVAILABLE: Final = "source_unavailable_family"
REASON_P6_ENTRY_NOT_ALLOWED: Final = "p6_entry_not_allowed"
REASON_RAW_TEXT_PAYLOAD_DETECTED: Final = "raw_text_payload_detected"
REASON_CONTRACT_MUTATION_DETECTED: Final = "contract_mutation_detected"

_MODE_TO_FAMILY: Final[dict[str, str]] = {
    "structure_question_observation": FAMILY_STRUCTURE_QUESTION,
    "long_meaning_arc": FAMILY_LONG_MEANING_ARC,
    "self_understanding_follow": FAMILY_SELF_UNDERSTANDING_FOLLOW,
    "daily_unpleasant_reception": FAMILY_DAILY_UNPLEASANT,
    "daily_positive_reception": FAMILY_DAILY_POSITIVE,
    "low_information_question": FAMILY_LOW_INFORMATION,
}
_FAMILY_ALIASES: Final[dict[str, str]] = {
    "structure-question": FAMILY_STRUCTURE_QUESTION,
    "structure_question_observation": FAMILY_STRUCTURE_QUESTION,
    "long-meaning-arc": FAMILY_LONG_MEANING_ARC,
    "self-understanding-follow": FAMILY_SELF_UNDERSTANDING_FOLLOW,
    "daily_unpleasant_reception": FAMILY_DAILY_UNPLEASANT,
    "daily_positive_reception": FAMILY_DAILY_POSITIVE,
    "positive": FAMILY_POSITIVE_ONLY,
    "positive_only_reception": FAMILY_POSITIVE_ONLY,
    "low_information_short": FAMILY_LOW_INFORMATION,
    "low_information_question": FAMILY_LOW_INFORMATION,
    "safety": FAMILY_SAFETY_TRIAGE_REQUIRED,
    "safety_triage": FAMILY_SAFETY_TRIAGE_REQUIRED,
    "emergency": FAMILY_EMERGENCY_SAFETY,
    "anger_target_blame": FAMILY_ANGER_ATTACK_OR_TARGET_BLAME,
    "target_blame": FAMILY_ANGER_ATTACK_OR_TARGET_BLAME,
    "source_missing": FAMILY_SOURCE_UNAVAILABLE,
}
_OBSERVATION_CONNECTABLE_STATUSES: Final[frozenset[str]] = frozenset(
    {"passed", "ready", "connectable", "allow", "allowed"}
)
_OBSERVATION_NON_CONNECTABLE_STATUSES: Final[frozenset[str]] = frozenset(
    {"hold", "blocked", "safety_blocked", "failed", "not_passed", "not_ready", "suppressed"}
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
        "reviewer_free_text",
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
        "read_feeling_auto_filled_from_machine_metrics",
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


def _maybe_bool(value: Any) -> bool | None:
    if isinstance(value, bool):
        return value
    if value is None:
        return None
    if isinstance(value, str):
        text = value.strip().lower()
        if text in {"1", "true", "yes", "y", "on", "passed", "ready", "allow", "allowed"}:
            return True
        if text in {"0", "false", "no", "n", "off", "hold", "blocked", "failed", "not_ready"}:
            return False
    return bool(value)


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


def _canonical_family(value: Any) -> str:
    family = _clean(value).lower().replace(" ", "_")
    return _FAMILY_ALIASES.get(family, family)


def _family_from_sources(*, explicit_family: Any, family_meta: Mapping[str, Any]) -> str:
    family = _canonical_family(explicit_family)
    if family:
        return family
    for key in (
        "family",
        "target_family",
        "p6_family",
        "structure_insight_family",
        "coverage_group",
        "fixture_family",
    ):
        family = _canonical_family(family_meta.get(key))
        if family:
            return family
    for key in ("reception_mode_id", "two_stage_reception_mode_id", "mode_id"):
        mode = _clean(family_meta.get(key)).lower()
        if mode in _MODE_TO_FAMILY:
            return _MODE_TO_FAMILY[mode]
    return ""


def _material_quality_from_sources(explicit_quality: Any, family_meta: Mapping[str, Any]) -> str:
    quality = _clean(explicit_quality).lower()
    if quality:
        return quality
    for key in ("material_quality", "input_material_quality", "quality"):
        quality = _clean(family_meta.get(key)).lower()
        if quality:
            return quality
    return ""


def _current_input_grounded(explicit_value: Any, family_meta: Mapping[str, Any]) -> bool | None:
    value = _maybe_bool(explicit_value)
    if value is not None:
        return value
    for key in (
        "current_input_grounded",
        "current_input_evidence_sufficient",
        "evidence_grounded",
        "grounded",
    ):
        value = _maybe_bool(family_meta.get(key))
        if value is not None:
            return value
    return None


def _observation_status_connectable(
    *,
    observation_status: Any,
    observation_status_connectable: Any,
    family_meta: Mapping[str, Any],
) -> bool | None:
    explicit = _maybe_bool(observation_status_connectable)
    if explicit is not None:
        return explicit
    for key in ("observation_status_connectable", "observation_passed", "observation_status_passed"):
        value = _maybe_bool(family_meta.get(key))
        if value is not None:
            return value
    status = _clean(observation_status or family_meta.get("observation_status")).lower()
    if status in _OBSERVATION_CONNECTABLE_STATUSES:
        return True
    if status in _OBSERVATION_NON_CONNECTABLE_STATUSES:
        return False
    return None


def _p6_entry_allowed(entry_freeze: Mapping[str, Any]) -> bool | None:
    if not entry_freeze:
        return None
    source = _safe_mapping(entry_freeze.get("summary")) or entry_freeze
    if source.get("p6_entry_allowed") is True:
        return True
    if source.get("p6_entry_hold") is True or source.get("p5_return_required") is True or source.get("p4_return_required") is True:
        return False
    return None


def _reason_with_id(reason: str, value: str) -> str:
    return f"{reason}:{value}" if value else reason


def _decision(*, block: list[str], hold: list[str], meta_only: list[str]) -> str:
    if block:
        return DECISION_BLOCK
    if hold:
        return DECISION_HOLD
    if meta_only:
        return DECISION_META_ONLY
    return DECISION_ALLOW_LIMITED_SURFACE


def build_structure_insight_p6_family_boundary(
    *,
    family: Any = None,
    family_meta: Mapping[str, Any] | None = None,
    material_quality: Any = None,
    current_input_grounded: Any = None,
    observation_status: Any = None,
    observation_status_connectable: Any = None,
    pre_gate_body_generated: Any = None,
    user_dictionary_fact_assertion_required: Any = None,
    target_judgement_required: Any = None,
    safety_adjacent: Any = None,
    emergency_safety: Any = None,
    source_unavailable: Any = None,
    p6_entry_freeze: Mapping[str, Any] | None = None,
    run_id: str | None = None,
) -> dict[str, Any]:
    """Build a body-free P6 target/no-connect family boundary decision."""

    run = _clean(run_id) or "p6_family_boundary"
    meta = _safe_mapping(family_meta)
    entry_freeze = _safe_mapping(p6_entry_freeze)
    resolved_family = _family_from_sources(explicit_family=family, family_meta=meta)
    resolved_quality = _material_quality_from_sources(material_quality, meta)
    grounded = _current_input_grounded(current_input_grounded, meta)
    observation_connectable = _observation_status_connectable(
        observation_status=observation_status,
        observation_status_connectable=observation_status_connectable,
        family_meta=meta,
    )
    body_before_gate = _maybe_bool(pre_gate_body_generated)
    if body_before_gate is None:
        body_before_gate = _maybe_bool(meta.get("pre_gate_body_generated") or meta.get("body_generated_before_gate"))
    body_before_gate = body_before_gate is True
    p6_allowed = _p6_entry_allowed(entry_freeze)

    unsafe_payload = any(_contains_text_payload_key(source) for source in (meta, entry_freeze))
    contract_mutation = any(_flag_true(source) for source in (meta, entry_freeze))
    explicit_user_dictionary_fact = _maybe_bool(
        user_dictionary_fact_assertion_required
        if user_dictionary_fact_assertion_required is not None
        else meta.get("user_dictionary_fact_assertion_required")
    )
    explicit_target_judgement = _maybe_bool(
        target_judgement_required if target_judgement_required is not None else meta.get("target_judgement_required")
    )
    explicit_safety_adjacent = _maybe_bool(safety_adjacent if safety_adjacent is not None else meta.get("safety_adjacent"))
    explicit_emergency_safety = _maybe_bool(
        emergency_safety if emergency_safety is not None else meta.get("emergency_safety")
    )
    explicit_source_unavailable = _maybe_bool(
        source_unavailable if source_unavailable is not None else meta.get("source_unavailable")
    )

    allowed_target_family = resolved_family in P6_ALLOWED_TARGET_FAMILIES
    no_connect_family = resolved_family in P6_NO_CONNECT_FAMILIES
    no_connect_material_quality = resolved_quality in P6_NO_CONNECT_MATERIAL_QUALITIES

    block_reasons: list[str] = []
    hold_reasons: list[str] = []
    meta_only_reasons: list[str] = []

    if unsafe_payload:
        block_reasons.append(REASON_RAW_TEXT_PAYLOAD_DETECTED)
    if contract_mutation:
        block_reasons.append(REASON_CONTRACT_MUTATION_DETECTED)
    if not resolved_family:
        hold_reasons.append(REASON_FAMILY_MISSING)
    elif no_connect_family:
        block_reasons.append(_reason_with_id(REASON_NO_CONNECT_FAMILY, resolved_family))
    elif not allowed_target_family:
        hold_reasons.append(REASON_FAMILY_NOT_IN_INITIAL_P6_SCOPE)

    if no_connect_material_quality:
        block_reasons.append(_reason_with_id(REASON_MATERIAL_QUALITY_NOT_CONNECTABLE, resolved_quality))
    elif not resolved_quality:
        hold_reasons.append(REASON_MATERIAL_QUALITY_NOT_CONFIRMED)
    elif resolved_quality != MATERIAL_QUALITY_ELIGIBLE:
        hold_reasons.append(REASON_MATERIAL_QUALITY_NOT_CONFIRMED)

    if grounded is False:
        block_reasons.append(REASON_CURRENT_INPUT_EVIDENCE_INSUFFICIENT)
    elif grounded is None:
        hold_reasons.append(REASON_CURRENT_INPUT_GROUNDING_NOT_CONFIRMED)

    if observation_connectable is False:
        meta_only_reasons.append(REASON_OBSERVATION_STATUS_NOT_CONNECTABLE)
    elif observation_connectable is None:
        hold_reasons.append(REASON_OBSERVATION_STATUS_NOT_CONFIRMED)

    if body_before_gate:
        block_reasons.append(REASON_BODY_GENERATED_BEFORE_GATE)
    if explicit_user_dictionary_fact is True:
        block_reasons.append(REASON_USER_DICTIONARY_FACT_ASSERTION_REQUIRED)
    if explicit_target_judgement is True:
        block_reasons.append(REASON_TARGET_JUDGEMENT_REQUIRED)
    if explicit_safety_adjacent is True:
        block_reasons.append(REASON_SAFETY_ADJACENT)
    if explicit_emergency_safety is True:
        block_reasons.append(REASON_EMERGENCY_SAFETY)
    if explicit_source_unavailable is True:
        block_reasons.append(REASON_SOURCE_UNAVAILABLE)
    if p6_allowed is False:
        hold_reasons.append(REASON_P6_ENTRY_NOT_ALLOWED)

    block_reasons = _dedupe(block_reasons)
    hold_reasons = _dedupe(hold_reasons)
    meta_only_reasons = _dedupe(meta_only_reasons)
    family_decision = _decision(block=block_reasons, hold=hold_reasons, meta_only=meta_only_reasons)
    no_connect_reason_codes = _dedupe([*block_reasons, *hold_reasons, *meta_only_reasons])
    limited_surface_candidate = family_decision == DECISION_ALLOW_LIMITED_SURFACE
    deep_insight_blocked = family_decision in {DECISION_BLOCK, DECISION_HOLD, DECISION_META_ONLY}

    summary = {
        "schema_version": STRUCTURE_INSIGHT_P6_FAMILY_BOUNDARY_SUMMARY_SCHEMA_VERSION,
        "version": STRUCTURE_INSIGHT_P6_FAMILY_BOUNDARY_SUMMARY_SCHEMA_VERSION,
        "source": STRUCTURE_INSIGHT_P6_FAMILY_BOUNDARY_SOURCE,
        "step": STRUCTURE_INSIGHT_P6_FAMILY_BOUNDARY_STEP,
        "run_id": run,
        "p6_family_boundary_created": True,
        "p6_family_boundary_only": True,
        "family": resolved_family,
        "material_quality": resolved_quality,
        "decision": family_decision,
        "allow_limited_surface": limited_surface_candidate,
        "meta_only": family_decision == DECISION_META_ONLY,
        "hold": family_decision == DECISION_HOLD,
        "block": family_decision == DECISION_BLOCK,
        "allowed_target_family": allowed_target_family,
        "allowed_families": list(P6_ALLOWED_TARGET_FAMILIES),
        "no_connect_family": no_connect_family,
        "no_connect_families": list(P6_NO_CONNECT_FAMILIES),
        "no_connect_reason_codes": no_connect_reason_codes,
        "deep_insight_blocked": deep_insight_blocked,
        "limited_surface_candidate": limited_surface_candidate,
        "current_input_grounded": grounded is True,
        "current_input_grounding_confirmed": grounded is not None,
        "observation_status_connectable": observation_connectable is True,
        "observation_status_confirmed": observation_connectable is not None,
        "pre_gate_body_generated": False,
        "body_generation_before_gate_blocked": body_before_gate,
        "user_dictionary_fact_assertion_blocked": explicit_user_dictionary_fact is True,
        "target_judgement_blocked": explicit_target_judgement is True,
        "safety_adjacent_blocked": explicit_safety_adjacent is True or explicit_emergency_safety is True,
        "source_unavailable_blocked": explicit_source_unavailable is True,
        "no_deep_insight_for_daily": True,
        "no_deep_insight_for_low_information": True,
        "no_deep_insight_for_positive_only": True,
        "no_deep_insight_for_safety_adjacent": True,
        "body_free_boundary_status_only": True,
        "ratings_only_payload": True,
        "public_text_payload_excluded": True,
        "local_command_packet_retained": False,
        "local_command_packet_body_retained": False,
        "machine_metrics_used_for_read_feeling": False,
        "read_feeling_auto_filled_from_machine_metrics": False,
        "fixed_sentence_template_added": False,
        "public_release_applied": False,
        "product_quality_released": False,
        "release_allowed": False,
        "public_contract": _public_contract(),
        "body_free": _body_free_contract(),
    }
    payload = {
        "schema_version": STRUCTURE_INSIGHT_P6_FAMILY_BOUNDARY_SCHEMA_VERSION,
        "version": STRUCTURE_INSIGHT_P6_FAMILY_BOUNDARY_SCHEMA_VERSION,
        "source": STRUCTURE_INSIGHT_P6_FAMILY_BOUNDARY_SOURCE,
        "step": STRUCTURE_INSIGHT_P6_FAMILY_BOUNDARY_STEP,
        "run_id": run,
        "summary": summary,
        "public_summary": {},
        "family": resolved_family,
        "material_quality": resolved_quality,
        "decision": family_decision,
        "allowed_target_family": allowed_target_family,
        "allowed_families": list(P6_ALLOWED_TARGET_FAMILIES),
        "no_connect_reason_codes": no_connect_reason_codes,
        "p6_family_boundary_created": True,
        "p6_family_boundary_only": True,
        "body_free_boundary_status_only": True,
        "ratings_only_payload": True,
        "public_text_payload_excluded": True,
        "local_command_packet_retained": False,
        "local_command_packet_body_retained": False,
        "machine_metrics_used_for_read_feeling": False,
        "read_feeling_auto_filled_from_machine_metrics": False,
        "fixed_sentence_template_added": False,
        "public_release_applied": False,
        "product_quality_released": False,
        "release_allowed": False,
        "public_contract": _public_contract(),
        "body_free": _body_free_contract(),
    }
    payload["public_summary"] = structure_insight_p6_family_boundary_public_summary(payload)
    assert_structure_insight_p6_family_boundary_contract(payload)
    return payload


def structure_insight_p6_family_boundary_public_summary(
    family_boundary_payload_or_summary: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    payload = _safe_mapping(family_boundary_payload_or_summary)
    source = _safe_mapping(payload.get("summary")) or payload
    summary = {
        "schema_version": STRUCTURE_INSIGHT_P6_FAMILY_BOUNDARY_SUMMARY_SCHEMA_VERSION,
        "version": STRUCTURE_INSIGHT_P6_FAMILY_BOUNDARY_SUMMARY_SCHEMA_VERSION,
        "source": STRUCTURE_INSIGHT_P6_FAMILY_BOUNDARY_SOURCE,
        "step": STRUCTURE_INSIGHT_P6_FAMILY_BOUNDARY_STEP,
        "run_id": _clean(source.get("run_id")),
        "p6_family_boundary_created": source.get("p6_family_boundary_created") is True,
        "family": _clean(source.get("family")),
        "material_quality": _clean(source.get("material_quality")),
        "decision": _clean(source.get("decision")) or DECISION_HOLD,
        "allow_limited_surface": source.get("allow_limited_surface") is True,
        "meta_only": source.get("meta_only") is True,
        "hold": source.get("hold") is True,
        "block": source.get("block") is True,
        "allowed_target_family": source.get("allowed_target_family") is True,
        "allowed_families": list(P6_ALLOWED_TARGET_FAMILIES),
        "no_connect_family": source.get("no_connect_family") is True,
        "no_connect_families": list(P6_NO_CONNECT_FAMILIES),
        "no_connect_reason_codes": _dedupe(source.get("no_connect_reason_codes")),
        "deep_insight_blocked": source.get("deep_insight_blocked") is True,
        "limited_surface_candidate": source.get("limited_surface_candidate") is True,
        "current_input_grounded": source.get("current_input_grounded") is True,
        "current_input_grounding_confirmed": source.get("current_input_grounding_confirmed") is True,
        "observation_status_connectable": source.get("observation_status_connectable") is True,
        "observation_status_confirmed": source.get("observation_status_confirmed") is True,
        "pre_gate_body_generated": False,
        "body_generation_before_gate_blocked": source.get("body_generation_before_gate_blocked") is True,
        "user_dictionary_fact_assertion_blocked": source.get("user_dictionary_fact_assertion_blocked") is True,
        "target_judgement_blocked": source.get("target_judgement_blocked") is True,
        "safety_adjacent_blocked": source.get("safety_adjacent_blocked") is True,
        "source_unavailable_blocked": source.get("source_unavailable_blocked") is True,
        "no_deep_insight_for_daily": True,
        "no_deep_insight_for_low_information": True,
        "no_deep_insight_for_positive_only": True,
        "no_deep_insight_for_safety_adjacent": True,
        "body_free_boundary_status_only": True,
        "ratings_only_payload": True,
        "public_text_payload_excluded": True,
        "raw_input_included": False,
        "raw_text_included": False,
        "input_text_included": False,
        "comment_text_body_included": False,
        "candidate_body_included": False,
        "surface_body_included": False,
        "history_raw_text_included": False,
        "raw_test_output_included": False,
        "command_output_included": False,
        "terminal_output_included": False,
        "machine_metrics_used_for_read_feeling": False,
        "read_feeling_auto_filled_from_machine_metrics": False,
        "fixed_sentence_template_added": False,
        "public_response_key_added": False,
        "response_shape_changed": False,
        "rn_visible_contract_changed": False,
        "public_release_applied": False,
        "product_quality_released": False,
        "release_allowed": False,
    }
    assert_structure_insight_p6_family_boundary_contract(summary, allow_partial=True)
    return summary


def dump_structure_insight_p6_family_boundary_public_summary(
    family_boundary_payload_or_summary: Mapping[str, Any] | None = None,
) -> str:
    summary = structure_insight_p6_family_boundary_public_summary(family_boundary_payload_or_summary)
    return json.dumps(summary, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def assert_structure_insight_p6_family_boundary_contract(value: Any, *, allow_partial: bool = False) -> None:
    meta = _safe_mapping(value)
    if not meta:
        raise ValueError("P6 Structure Insight family boundary must be a mapping")
    if _contains_text_payload_key(meta):
        raise ValueError("P6 Structure Insight family boundary must not include raw/comment/history/test body keys")
    if _flag_true(meta):
        raise ValueError("P6 Structure Insight family boundary contains a forbidden true flag")
    json.dumps(meta, ensure_ascii=False, sort_keys=True)
    if allow_partial:
        return
    if meta.get("schema_version") != STRUCTURE_INSIGHT_P6_FAMILY_BOUNDARY_SCHEMA_VERSION:
        raise ValueError("unexpected P6 Structure Insight family boundary schema_version")
    if meta.get("step") != STRUCTURE_INSIGHT_P6_FAMILY_BOUNDARY_STEP:
        raise ValueError("unexpected P6 Structure Insight family boundary step")
    if meta.get("decision") not in {
        DECISION_ALLOW_LIMITED_SURFACE,
        DECISION_META_ONLY,
        DECISION_HOLD,
        DECISION_BLOCK,
    }:
        raise ValueError("unexpected P6 Structure Insight family boundary decision")
    summary = _safe_mapping(meta.get("summary"))
    if summary.get("schema_version") != STRUCTURE_INSIGHT_P6_FAMILY_BOUNDARY_SUMMARY_SCHEMA_VERSION:
        raise ValueError("unexpected P6 Structure Insight family boundary summary schema_version")
    if summary.get("release_allowed") is not False or meta.get("release_allowed") is not False:
        raise ValueError("P6 Structure Insight family boundary must not allow release")
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
                raise ValueError(f"P6 family boundary {source_name}.public_contract.{key} must be false")
        for key in (
            "raw_input_included",
            "raw_text_included",
            "input_text_included",
            "comment_text_body_included",
            "candidate_body_included",
            "surface_body_included",
            "history_raw_text_included",
            "raw_test_output_included",
            "command_output_included",
            "terminal_output_included",
        ):
            if body_free.get(key) is not False:
                raise ValueError(f"P6 family boundary {source_name}.body_free.{key} must be false")


__all__ = [
    "STRUCTURE_INSIGHT_P6_FAMILY_BOUNDARY_SCHEMA_VERSION",
    "STRUCTURE_INSIGHT_P6_FAMILY_BOUNDARY_SUMMARY_SCHEMA_VERSION",
    "STRUCTURE_INSIGHT_P6_FAMILY_BOUNDARY_STEP",
    "DECISION_ALLOW_LIMITED_SURFACE",
    "DECISION_META_ONLY",
    "DECISION_HOLD",
    "DECISION_BLOCK",
    "P6_ALLOWED_TARGET_FAMILIES",
    "P6_NO_CONNECT_FAMILIES",
    "build_structure_insight_p6_family_boundary",
    "structure_insight_p6_family_boundary_public_summary",
    "dump_structure_insight_p6_family_boundary_public_summary",
    "assert_structure_insight_p6_family_boundary_contract",
]
