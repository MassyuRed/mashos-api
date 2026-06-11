# -*- coding: utf-8 -*-
from __future__ import annotations

"""P6-3 relation-family initial set and risk classification.

The policy fixes which Structure Insight relation families may be initial
visible candidates, which require review, and which must remain non-visible.
It is body-free: it never returns candidate bodies, proposed surfaces, raw
input, public response keys, or release flags.
"""

from collections.abc import Iterable, Mapping
import json
from typing import Any, Final


STRUCTURE_INSIGHT_P6_RELATION_POLICY_SCHEMA_VERSION: Final = (
    "cocolon.emlis.structure_insight.p6_relation_policy.v1"
)
STRUCTURE_INSIGHT_P6_RELATION_POLICY_SUMMARY_SCHEMA_VERSION: Final = (
    "cocolon.emlis.structure_insight.p6_relation_policy_summary.v1"
)
STRUCTURE_INSIGHT_P6_RELATION_POLICY_STEP: Final = "P6-3_RelationFamilyInitialSetRiskClassification"
STRUCTURE_INSIGHT_P6_RELATION_POLICY_SOURCE: Final = (
    "Cocolon_EmlisAI_P6_StructureInsight_RelationPolicy_20260611"
)

RISK_LEVEL_LOW: Final = "low"
RISK_LEVEL_MEDIUM: Final = "medium"
RISK_LEVEL_HIGH: Final = "high"
RISK_LEVEL_BLOCKED: Final = "blocked"

VISIBILITY_ALLOW_INITIAL_VISIBLE: Final = "allow_initial_visible"
VISIBILITY_REVIEW_REQUIRED: Final = "review_required"
VISIBILITY_META_ONLY: Final = "meta_only"
VISIBILITY_BLOCKED: Final = "blocked"

RELATION_EVENT_REACTION_LINK: Final = "event_reaction_link"
RELATION_DESIRE_BLOCKAGE_CONFLICT: Final = "desire_blockage_conflict"
RELATION_EFFORT_RESIDUE: Final = "effort_residue"
RELATION_VALUE_LINE_CROSSED: Final = "value_line_crossed"
RELATION_FEAR_LOAD_PAIR: Final = "fear_load_pair"
RELATION_POSITIVE_CHANGE_RECOVERY: Final = "positive_change_recovery"
RELATION_SELF_DENIAL_IDENTITY_SPLIT: Final = "self_denial_identity_split"
RELATION_UNCERTAINTY_EFFORT_PAIR: Final = "uncertainty_effort_pair"
RELATION_MIXED_EMOTION_COEXISTENCE: Final = "mixed_emotion_coexistence"
RELATION_LONG_ARC_MULTIPLE_CORE: Final = "long_arc_multiple_core"
RELATION_LOW_INFORMATION_UNSPECIFIED_WEIGHT: Final = "low_information_unspecified_weight"
RELATION_TARGET_JUDGEMENT_AGREEMENT: Final = "target_judgement_agreement"
RELATION_HISTORY_FACT_LINE_AS_INSIGHT: Final = "history_fact_line_as_insight"
RELATION_PERIOD_TENDENCY_FROM_SINGLE_RECORD: Final = "period_tendency_from_single_record"
RELATION_USER_DICTIONARY_FACT_CLAIM: Final = "user_dictionary_fact_claim"

P6_LOW_RISK_RELATION_FAMILIES: Final[tuple[str, ...]] = (
    RELATION_DESIRE_BLOCKAGE_CONFLICT,
    RELATION_EFFORT_RESIDUE,
    RELATION_MIXED_EMOTION_COEXISTENCE,
    RELATION_LONG_ARC_MULTIPLE_CORE,
    RELATION_UNCERTAINTY_EFFORT_PAIR,
)
P6_MEDIUM_RISK_RELATION_FAMILIES: Final[tuple[str, ...]] = (
    RELATION_EVENT_REACTION_LINK,
    RELATION_POSITIVE_CHANGE_RECOVERY,
    RELATION_FEAR_LOAD_PAIR,
)
P6_HIGH_RISK_RELATION_FAMILIES: Final[tuple[str, ...]] = (
    RELATION_VALUE_LINE_CROSSED,
    RELATION_SELF_DENIAL_IDENTITY_SPLIT,
)
P6_BLOCKED_RELATION_FAMILIES: Final[tuple[str, ...]] = (
    RELATION_LOW_INFORMATION_UNSPECIFIED_WEIGHT,
    RELATION_TARGET_JUDGEMENT_AGREEMENT,
    RELATION_PERIOD_TENDENCY_FROM_SINGLE_RECORD,
    RELATION_USER_DICTIONARY_FACT_CLAIM,
)
P6_META_ONLY_RELATION_FAMILIES: Final[tuple[str, ...]] = (
    RELATION_HISTORY_FACT_LINE_AS_INSIGHT,
)
P6_INITIAL_RELATION_FAMILIES: Final[tuple[str, ...]] = (
    *P6_LOW_RISK_RELATION_FAMILIES,
    *P6_MEDIUM_RISK_RELATION_FAMILIES,
    *P6_HIGH_RISK_RELATION_FAMILIES,
    *P6_BLOCKED_RELATION_FAMILIES,
    *P6_META_ONLY_RELATION_FAMILIES,
)

FORBIDDEN_CLAIMS_BASE: Final[tuple[str, ...]] = (
    "diagnosis",
    "personality_claim",
    "cause_claim_without_evidence",
    "advice",
    "future_prediction",
    "target_judgement_agreement",
    "period_tendency_from_single_record",
    "user_dictionary_fact_claim",
)
GATE_REQUIRED_BASE: Final[tuple[str, ...]] = (
    "evidence_boundary_gate",
    "soft_inference_surface_gate",
    "visible_surface_acceptance_gate",
    "public_meta_sanitizer",
)

REASON_RELATION_FAMILY_MISSING: Final = "relation_family_missing"
REASON_RELATION_NOT_IN_INITIAL_SET: Final = "relation_family_not_in_initial_p6_set"
REASON_LOW_RISK_ALLOW_CANDIDATE: Final = "low_risk_relation_initial_visible_candidate"
REASON_MEDIUM_RISK_REVIEW_REQUIRED: Final = "medium_risk_relation_review_required"
REASON_HIGH_RISK_REVIEW_REQUIRED: Final = "high_risk_relation_review_required"
REASON_HIGH_RISK_AUTO_VISIBLE_BLOCKED: Final = "high_risk_relation_auto_visible_blocked"
REASON_BLOCKED_RELATION_FAMILY: Final = "blocked_relation_family"
REASON_META_ONLY_RELATION_FAMILY: Final = "meta_only_relation_family"
REASON_LOW_INFORMATION_VISIBLE_BLOCKED: Final = "low_information_visible_blocked"
REASON_LOW_INFORMATION_OVERREAD_BLOCKED: Final = "low_information_overread_blocked"
REASON_TARGET_JUDGEMENT_BLOCKED: Final = "target_judgement_blocked"
REASON_SELF_DENIAL_IDENTITY_REVIEW_REQUIRED: Final = "self_denial_identity_review_required"
REASON_SELF_DENIAL_IDENTITY_FACT_BLOCKED: Final = "self_denial_identity_fact_blocked"
REASON_PERIOD_TENDENCY_SINGLE_RECORD_BLOCKED: Final = "period_tendency_from_single_record_blocked"
REASON_USER_DICTIONARY_FACT_CLAIM_BLOCKED: Final = "user_dictionary_fact_claim_blocked"
REASON_HISTORY_FACT_LINE_META_ONLY: Final = "history_fact_line_as_insight_meta_only"
REASON_P6_FAMILY_BOUNDARY_NOT_ALLOWING_SURFACE: Final = "p6_family_boundary_not_allowing_surface"
REASON_GATE_REQUIRED_BYPASSED: Final = "gate_required_bypassed"
REASON_BODY_GENERATED_BEFORE_GATE: Final = "body_generated_before_gate"
REASON_RAW_TEXT_PAYLOAD_DETECTED: Final = "raw_text_payload_detected"
REASON_CONTRACT_MUTATION_DETECTED: Final = "contract_mutation_detected"

_RELATION_ALIASES: Final[dict[str, str]] = {
    "approach_avoidance": RELATION_DESIRE_BLOCKAGE_CONFLICT,
    "desire_stagnation": RELATION_DESIRE_BLOCKAGE_CONFLICT,
    "action_blocked": RELATION_DESIRE_BLOCKAGE_CONFLICT,
    "pressure_gap": RELATION_DESIRE_BLOCKAGE_CONFLICT,
    "load_accumulation": RELATION_EFFORT_RESIDUE,
    "repetition": RELATION_EFFORT_RESIDUE,
    "thought_action_discrepancy": RELATION_MIXED_EMOTION_COEXISTENCE,
    "emotion_nesting": RELATION_MIXED_EMOTION_COEXISTENCE,
    "coexistence": RELATION_MIXED_EMOTION_COEXISTENCE,
    "long_meaning_arc": RELATION_LONG_ARC_MULTIPLE_CORE,
    "self_insight_discovery": RELATION_UNCERTAINTY_EFFORT_PAIR,
    "uncertainty_effort": RELATION_UNCERTAINTY_EFFORT_PAIR,
    "priority_pressure": RELATION_VALUE_LINE_CROSSED,
    "boundary": RELATION_VALUE_LINE_CROSSED,
    "value_line": RELATION_VALUE_LINE_CROSSED,
    "state_text_gap": RELATION_FEAR_LOAD_PAIR,
    "recovery": RELATION_POSITIVE_CHANGE_RECOVERY,
    "repair": RELATION_POSITIVE_CHANGE_RECOVERY,
    "self_denial": RELATION_SELF_DENIAL_IDENTITY_SPLIT,
    "identity_claim": RELATION_SELF_DENIAL_IDENTITY_SPLIT,
    "low_information_weight": RELATION_LOW_INFORMATION_UNSPECIFIED_WEIGHT,
    "target_attack_agreement": RELATION_TARGET_JUDGEMENT_AGREEMENT,
    "opponent_intent_claim": RELATION_TARGET_JUDGEMENT_AGREEMENT,
    "period_tendency": RELATION_PERIOD_TENDENCY_FROM_SINGLE_RECORD,
    "user_dictionary_fact": RELATION_USER_DICTIONARY_FACT_CLAIM,
    "history_fact_line": RELATION_HISTORY_FACT_LINE_AS_INSIGHT,
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
        if text in {"1", "true", "yes", "y", "on", "allow", "allowed", "passed"}:
            return True
        if text in {"0", "false", "no", "n", "off", "blocked", "hold", "failed"}:
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


def _canonical_relation_family(value: Any) -> str:
    relation = _clean(value).lower().replace(" ", "_").replace("-", "_")
    return _RELATION_ALIASES.get(relation, relation)


def _relation_from_sources(*, explicit_relation_family: Any, relation_meta: Mapping[str, Any]) -> str:
    relation = _canonical_relation_family(explicit_relation_family)
    if relation:
        return relation
    for key in ("relation_family", "relation_type", "candidate_relation_family", "structure_relation_family"):
        relation = _canonical_relation_family(relation_meta.get(key))
        if relation:
            return relation
    return ""


def _family_boundary_allows_limited_surface(value: Mapping[str, Any]) -> bool | None:
    if not value:
        return None
    source = _safe_mapping(value.get("summary")) or value
    if source.get("allow_limited_surface") is True or source.get("limited_surface_candidate") is True:
        return True
    if source.get("block") is True or source.get("hold") is True or source.get("meta_only") is True:
        return False
    return None


def _risk_level_for(relation_family: str) -> str:
    if relation_family in P6_LOW_RISK_RELATION_FAMILIES:
        return RISK_LEVEL_LOW
    if relation_family in P6_MEDIUM_RISK_RELATION_FAMILIES:
        return RISK_LEVEL_MEDIUM
    if relation_family in P6_HIGH_RISK_RELATION_FAMILIES:
        return RISK_LEVEL_HIGH
    return RISK_LEVEL_BLOCKED


def _base_visibility_for(relation_family: str, risk_level: str) -> str:
    if relation_family in P6_META_ONLY_RELATION_FAMILIES:
        return VISIBILITY_META_ONLY
    if risk_level == RISK_LEVEL_LOW:
        return VISIBILITY_ALLOW_INITIAL_VISIBLE
    if risk_level in {RISK_LEVEL_MEDIUM, RISK_LEVEL_HIGH}:
        return VISIBILITY_REVIEW_REQUIRED
    return VISIBILITY_BLOCKED


def _gate_required_for(relation_family: str, risk_level: str) -> list[str]:
    gates = list(GATE_REQUIRED_BASE)
    if risk_level in {RISK_LEVEL_MEDIUM, RISK_LEVEL_HIGH, RISK_LEVEL_BLOCKED}:
        gates.append("p6_relation_policy_review_gate")
    if relation_family == RELATION_VALUE_LINE_CROSSED:
        gates.extend(("anger_or_boundary_strict_gate", "target_judgement_block_gate", "target_intent_block_gate"))
    if relation_family == RELATION_SELF_DENIAL_IDENTITY_SPLIT:
        gates.extend(("self_denial_identity_fact_gate", "self_blame_non_amplification_gate"))
    if relation_family == RELATION_LOW_INFORMATION_UNSPECIFIED_WEIGHT:
        gates.extend(("low_information_overread_gate", "no_visible_surface_gate"))
    if relation_family == RELATION_TARGET_JUDGEMENT_AGREEMENT:
        gates.extend(("target_judgement_block_gate", "no_visible_surface_gate"))
    if relation_family == RELATION_PERIOD_TENDENCY_FROM_SINGLE_RECORD:
        gates.extend(("single_record_period_tendency_gate", "no_visible_surface_gate"))
    if relation_family == RELATION_USER_DICTIONARY_FACT_CLAIM:
        gates.extend(("user_dictionary_fact_claim_gate", "no_visible_surface_gate"))
    if relation_family == RELATION_HISTORY_FACT_LINE_AS_INSIGHT:
        gates.extend(("history_fact_line_meta_only_gate", "no_visible_surface_gate"))
    return _dedupe(gates)


def _forbidden_claims_for(relation_family: str) -> list[str]:
    claims = list(FORBIDDEN_CLAIMS_BASE)
    if relation_family == RELATION_SELF_DENIAL_IDENTITY_SPLIT:
        claims.append("self_denial_identity_claim_as_fact")
    if relation_family == RELATION_VALUE_LINE_CROSSED:
        claims.extend(("target_attack_agreement", "opponent_intent_claim"))
    if relation_family == RELATION_LOW_INFORMATION_UNSPECIFIED_WEIGHT:
        claims.append("background_deep_reading")
    if relation_family == RELATION_HISTORY_FACT_LINE_AS_INSIGHT:
        claims.append("history_as_current_insight_fact")
    return _dedupe(claims)


def _reason_with_id(reason: str, value: str) -> str:
    return f"{reason}:{value}" if value else reason


def build_structure_insight_p6_relation_policy(
    *,
    relation_family: Any = None,
    relation_meta: Mapping[str, Any] | None = None,
    p6_family_boundary: Mapping[str, Any] | None = None,
    low_information_overread_risk: Any = None,
    target_judgement_required: Any = None,
    self_denial_identity_fact_required: Any = None,
    period_tendency_required: Any = None,
    user_dictionary_fact_claim_required: Any = None,
    gate_required_bypassed: Any = None,
    pre_gate_body_generated: Any = None,
    run_id: str | None = None,
) -> dict[str, Any]:
    """Build a body-free P6 relation policy row."""

    run = _clean(run_id) or "p6_relation_policy"
    meta = _safe_mapping(relation_meta)
    boundary = _safe_mapping(p6_family_boundary)
    resolved_relation = _relation_from_sources(explicit_relation_family=relation_family, relation_meta=meta)
    risk_level = _risk_level_for(resolved_relation) if resolved_relation else RISK_LEVEL_BLOCKED
    visibility_decision = _base_visibility_for(resolved_relation, risk_level)
    family_boundary_allowed = _family_boundary_allows_limited_surface(boundary)
    forbidden_claims = _forbidden_claims_for(resolved_relation)
    gate_required = _gate_required_for(resolved_relation, risk_level)

    unsafe_payload = any(_contains_text_payload_key(source) for source in (meta, boundary))
    contract_mutation = any(_flag_true(source) for source in (meta, boundary))
    low_info_overread = _maybe_bool(
        low_information_overread_risk
        if low_information_overread_risk is not None
        else meta.get("low_information_overread_risk")
    )
    target_judgement = _maybe_bool(
        target_judgement_required
        if target_judgement_required is not None
        else meta.get("target_judgement_required")
    )
    self_denial_fact = _maybe_bool(
        self_denial_identity_fact_required
        if self_denial_identity_fact_required is not None
        else meta.get("self_denial_identity_fact_required")
    )
    period_tendency = _maybe_bool(
        period_tendency_required
        if period_tendency_required is not None
        else meta.get("period_tendency_required")
    )
    user_dictionary_fact = _maybe_bool(
        user_dictionary_fact_claim_required
        if user_dictionary_fact_claim_required is not None
        else meta.get("user_dictionary_fact_claim_required")
    )
    gate_bypassed = _maybe_bool(
        gate_required_bypassed if gate_required_bypassed is not None else meta.get("gate_required_bypassed")
    )
    body_before_gate = _maybe_bool(
        pre_gate_body_generated if pre_gate_body_generated is not None else meta.get("pre_gate_body_generated")
    )

    reason_codes: list[str] = []
    if unsafe_payload:
        reason_codes.append(REASON_RAW_TEXT_PAYLOAD_DETECTED)
        visibility_decision = VISIBILITY_BLOCKED
    if contract_mutation:
        reason_codes.append(REASON_CONTRACT_MUTATION_DETECTED)
        visibility_decision = VISIBILITY_BLOCKED
    if not resolved_relation:
        reason_codes.append(REASON_RELATION_FAMILY_MISSING)
        visibility_decision = VISIBILITY_META_ONLY
    elif resolved_relation not in P6_INITIAL_RELATION_FAMILIES:
        reason_codes.append(_reason_with_id(REASON_RELATION_NOT_IN_INITIAL_SET, resolved_relation))
        visibility_decision = VISIBILITY_META_ONLY
    elif resolved_relation in P6_LOW_RISK_RELATION_FAMILIES:
        reason_codes.append(_reason_with_id(REASON_LOW_RISK_ALLOW_CANDIDATE, resolved_relation))
    elif resolved_relation in P6_MEDIUM_RISK_RELATION_FAMILIES:
        reason_codes.append(_reason_with_id(REASON_MEDIUM_RISK_REVIEW_REQUIRED, resolved_relation))
    elif resolved_relation in P6_HIGH_RISK_RELATION_FAMILIES:
        reason_codes.append(_reason_with_id(REASON_HIGH_RISK_REVIEW_REQUIRED, resolved_relation))
        reason_codes.append(REASON_HIGH_RISK_AUTO_VISIBLE_BLOCKED)
    elif resolved_relation in P6_BLOCKED_RELATION_FAMILIES:
        reason_codes.append(_reason_with_id(REASON_BLOCKED_RELATION_FAMILY, resolved_relation))
        visibility_decision = VISIBILITY_BLOCKED
    elif resolved_relation in P6_META_ONLY_RELATION_FAMILIES:
        reason_codes.append(_reason_with_id(REASON_META_ONLY_RELATION_FAMILY, resolved_relation))
        visibility_decision = VISIBILITY_META_ONLY

    if family_boundary_allowed is False and visibility_decision == VISIBILITY_ALLOW_INITIAL_VISIBLE:
        visibility_decision = VISIBILITY_META_ONLY
        reason_codes.append(REASON_P6_FAMILY_BOUNDARY_NOT_ALLOWING_SURFACE)
    if resolved_relation == RELATION_LOW_INFORMATION_UNSPECIFIED_WEIGHT:
        reason_codes.append(REASON_LOW_INFORMATION_VISIBLE_BLOCKED)
    if low_info_overread is True:
        reason_codes.append(REASON_LOW_INFORMATION_OVERREAD_BLOCKED)
        visibility_decision = VISIBILITY_BLOCKED
    if resolved_relation == RELATION_TARGET_JUDGEMENT_AGREEMENT or target_judgement is True:
        reason_codes.append(REASON_TARGET_JUDGEMENT_BLOCKED)
        visibility_decision = VISIBILITY_BLOCKED
    if resolved_relation == RELATION_SELF_DENIAL_IDENTITY_SPLIT:
        reason_codes.append(REASON_SELF_DENIAL_IDENTITY_REVIEW_REQUIRED)
    if self_denial_fact is True:
        reason_codes.append(REASON_SELF_DENIAL_IDENTITY_FACT_BLOCKED)
        visibility_decision = VISIBILITY_BLOCKED
    if resolved_relation == RELATION_PERIOD_TENDENCY_FROM_SINGLE_RECORD or period_tendency is True:
        reason_codes.append(REASON_PERIOD_TENDENCY_SINGLE_RECORD_BLOCKED)
        visibility_decision = VISIBILITY_BLOCKED
    if resolved_relation == RELATION_USER_DICTIONARY_FACT_CLAIM or user_dictionary_fact is True:
        reason_codes.append(REASON_USER_DICTIONARY_FACT_CLAIM_BLOCKED)
        visibility_decision = VISIBILITY_BLOCKED
    if resolved_relation == RELATION_HISTORY_FACT_LINE_AS_INSIGHT:
        reason_codes.append(REASON_HISTORY_FACT_LINE_META_ONLY)
        visibility_decision = VISIBILITY_META_ONLY
    if gate_bypassed is True:
        reason_codes.append(REASON_GATE_REQUIRED_BYPASSED)
        visibility_decision = VISIBILITY_BLOCKED
    if body_before_gate is True:
        reason_codes.append(REASON_BODY_GENERATED_BEFORE_GATE)
        visibility_decision = VISIBILITY_BLOCKED

    reason_codes = _dedupe(reason_codes)
    allow_initial_visible = visibility_decision == VISIBILITY_ALLOW_INITIAL_VISIBLE
    review_required = visibility_decision == VISIBILITY_REVIEW_REQUIRED
    meta_only = visibility_decision == VISIBILITY_META_ONLY
    blocked = visibility_decision == VISIBILITY_BLOCKED
    high_risk_auto_visible_blocked = risk_level == RISK_LEVEL_HIGH and not allow_initial_visible

    summary = {
        "schema_version": STRUCTURE_INSIGHT_P6_RELATION_POLICY_SUMMARY_SCHEMA_VERSION,
        "version": STRUCTURE_INSIGHT_P6_RELATION_POLICY_SUMMARY_SCHEMA_VERSION,
        "source": STRUCTURE_INSIGHT_P6_RELATION_POLICY_SOURCE,
        "step": STRUCTURE_INSIGHT_P6_RELATION_POLICY_STEP,
        "run_id": run,
        "p6_relation_policy_created": True,
        "p6_relation_policy_only": True,
        "relation_family": resolved_relation,
        "risk_level": risk_level,
        "visibility_decision": visibility_decision,
        "allow_initial_visible": allow_initial_visible,
        "review_required": review_required,
        "meta_only": meta_only,
        "blocked": blocked,
        "auto_visible_allowed": allow_initial_visible,
        "high_risk_auto_visible_blocked": high_risk_auto_visible_blocked,
        "low_information_visible_blocked": resolved_relation == RELATION_LOW_INFORMATION_UNSPECIFIED_WEIGHT,
        "target_judgement_blocked": REASON_TARGET_JUDGEMENT_BLOCKED in reason_codes,
        "self_denial_identity_review_required": REASON_SELF_DENIAL_IDENTITY_REVIEW_REQUIRED in reason_codes,
        "self_denial_identity_fact_blocked": REASON_SELF_DENIAL_IDENTITY_FACT_BLOCKED in reason_codes,
        "period_tendency_single_record_blocked": REASON_PERIOD_TENDENCY_SINGLE_RECORD_BLOCKED in reason_codes,
        "user_dictionary_fact_claim_blocked": REASON_USER_DICTIONARY_FACT_CLAIM_BLOCKED in reason_codes,
        "history_fact_line_meta_only": REASON_HISTORY_FACT_LINE_META_ONLY in reason_codes,
        "gate_required": gate_required,
        "forbidden_claims": forbidden_claims,
        "decision_reason_codes": reason_codes,
        "initial_allow_relation_families": list(P6_LOW_RISK_RELATION_FAMILIES),
        "review_relation_families": [*P6_MEDIUM_RISK_RELATION_FAMILIES, *P6_HIGH_RISK_RELATION_FAMILIES],
        "blocked_relation_families": list(P6_BLOCKED_RELATION_FAMILIES),
        "meta_only_relation_families": list(P6_META_ONLY_RELATION_FAMILIES),
        "gate_bypass_blocked": gate_bypassed is True,
        "body_generation_before_gate_blocked": body_before_gate is True,
        "ratings_only_payload": True,
        "public_text_payload_excluded": True,
        "body_free_policy_status_only": True,
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
        "schema_version": STRUCTURE_INSIGHT_P6_RELATION_POLICY_SCHEMA_VERSION,
        "version": STRUCTURE_INSIGHT_P6_RELATION_POLICY_SCHEMA_VERSION,
        "source": STRUCTURE_INSIGHT_P6_RELATION_POLICY_SOURCE,
        "step": STRUCTURE_INSIGHT_P6_RELATION_POLICY_STEP,
        "run_id": run,
        "summary": summary,
        "public_summary": {},
        "relation_family": resolved_relation,
        "risk_level": risk_level,
        "visibility_decision": visibility_decision,
        "gate_required": gate_required,
        "forbidden_claims": forbidden_claims,
        "decision_reason_codes": reason_codes,
        "p6_relation_policy_created": True,
        "p6_relation_policy_only": True,
        "ratings_only_payload": True,
        "public_text_payload_excluded": True,
        "body_free_policy_status_only": True,
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
    payload["public_summary"] = structure_insight_p6_relation_policy_public_summary(payload)
    assert_structure_insight_p6_relation_policy_contract(payload)
    return payload


def structure_insight_p6_relation_policy_public_summary(
    relation_policy_payload_or_summary: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    payload = _safe_mapping(relation_policy_payload_or_summary)
    source = _safe_mapping(payload.get("summary")) or payload
    summary = {
        "schema_version": STRUCTURE_INSIGHT_P6_RELATION_POLICY_SUMMARY_SCHEMA_VERSION,
        "version": STRUCTURE_INSIGHT_P6_RELATION_POLICY_SUMMARY_SCHEMA_VERSION,
        "source": STRUCTURE_INSIGHT_P6_RELATION_POLICY_SOURCE,
        "step": STRUCTURE_INSIGHT_P6_RELATION_POLICY_STEP,
        "run_id": _clean(source.get("run_id")),
        "p6_relation_policy_created": source.get("p6_relation_policy_created") is True,
        "relation_family": _clean(source.get("relation_family")),
        "risk_level": _clean(source.get("risk_level")) or RISK_LEVEL_BLOCKED,
        "visibility_decision": _clean(source.get("visibility_decision")) or VISIBILITY_META_ONLY,
        "allow_initial_visible": source.get("allow_initial_visible") is True,
        "review_required": source.get("review_required") is True,
        "meta_only": source.get("meta_only") is True,
        "blocked": source.get("blocked") is True,
        "auto_visible_allowed": source.get("auto_visible_allowed") is True,
        "high_risk_auto_visible_blocked": source.get("high_risk_auto_visible_blocked") is True,
        "low_information_visible_blocked": source.get("low_information_visible_blocked") is True,
        "target_judgement_blocked": source.get("target_judgement_blocked") is True,
        "self_denial_identity_review_required": source.get("self_denial_identity_review_required") is True,
        "self_denial_identity_fact_blocked": source.get("self_denial_identity_fact_blocked") is True,
        "period_tendency_single_record_blocked": source.get("period_tendency_single_record_blocked") is True,
        "user_dictionary_fact_claim_blocked": source.get("user_dictionary_fact_claim_blocked") is True,
        "history_fact_line_meta_only": source.get("history_fact_line_meta_only") is True,
        "gate_required": _dedupe(source.get("gate_required")),
        "forbidden_claims": _dedupe(source.get("forbidden_claims")),
        "decision_reason_codes": _dedupe(source.get("decision_reason_codes")),
        "initial_allow_relation_families": list(P6_LOW_RISK_RELATION_FAMILIES),
        "review_relation_families": [*P6_MEDIUM_RISK_RELATION_FAMILIES, *P6_HIGH_RISK_RELATION_FAMILIES],
        "blocked_relation_families": list(P6_BLOCKED_RELATION_FAMILIES),
        "meta_only_relation_families": list(P6_META_ONLY_RELATION_FAMILIES),
        "gate_bypass_blocked": source.get("gate_bypass_blocked") is True,
        "body_generation_before_gate_blocked": source.get("body_generation_before_gate_blocked") is True,
        "ratings_only_payload": True,
        "public_text_payload_excluded": True,
        "body_free_policy_status_only": True,
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
    assert_structure_insight_p6_relation_policy_contract(summary, allow_partial=True)
    return summary


def dump_structure_insight_p6_relation_policy_public_summary(
    relation_policy_payload_or_summary: Mapping[str, Any] | None = None,
) -> str:
    summary = structure_insight_p6_relation_policy_public_summary(relation_policy_payload_or_summary)
    return json.dumps(summary, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def assert_structure_insight_p6_relation_policy_contract(value: Any, *, allow_partial: bool = False) -> None:
    meta = _safe_mapping(value)
    if not meta:
        raise ValueError("P6 Structure Insight relation policy must be a mapping")
    if _contains_text_payload_key(meta):
        raise ValueError("P6 Structure Insight relation policy must not include raw/comment/history/test body keys")
    if _flag_true(meta):
        raise ValueError("P6 Structure Insight relation policy contains a forbidden true flag")
    json.dumps(meta, ensure_ascii=False, sort_keys=True)
    if allow_partial:
        return
    if meta.get("schema_version") != STRUCTURE_INSIGHT_P6_RELATION_POLICY_SCHEMA_VERSION:
        raise ValueError("unexpected P6 Structure Insight relation policy schema_version")
    if meta.get("step") != STRUCTURE_INSIGHT_P6_RELATION_POLICY_STEP:
        raise ValueError("unexpected P6 Structure Insight relation policy step")
    if meta.get("risk_level") not in {RISK_LEVEL_LOW, RISK_LEVEL_MEDIUM, RISK_LEVEL_HIGH, RISK_LEVEL_BLOCKED}:
        raise ValueError("unexpected P6 Structure Insight relation policy risk_level")
    if meta.get("visibility_decision") not in {
        VISIBILITY_ALLOW_INITIAL_VISIBLE,
        VISIBILITY_REVIEW_REQUIRED,
        VISIBILITY_META_ONLY,
        VISIBILITY_BLOCKED,
    }:
        raise ValueError("unexpected P6 Structure Insight relation policy visibility_decision")
    summary = _safe_mapping(meta.get("summary"))
    if summary.get("schema_version") != STRUCTURE_INSIGHT_P6_RELATION_POLICY_SUMMARY_SCHEMA_VERSION:
        raise ValueError("unexpected P6 Structure Insight relation policy summary schema_version")
    if summary.get("release_allowed") is not False or meta.get("release_allowed") is not False:
        raise ValueError("P6 Structure Insight relation policy must not allow release")
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
                raise ValueError(f"P6 relation policy {source_name}.public_contract.{key} must be false")
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
                raise ValueError(f"P6 relation policy {source_name}.body_free.{key} must be false")


__all__ = [
    "STRUCTURE_INSIGHT_P6_RELATION_POLICY_SCHEMA_VERSION",
    "STRUCTURE_INSIGHT_P6_RELATION_POLICY_SUMMARY_SCHEMA_VERSION",
    "STRUCTURE_INSIGHT_P6_RELATION_POLICY_STEP",
    "RISK_LEVEL_LOW",
    "RISK_LEVEL_MEDIUM",
    "RISK_LEVEL_HIGH",
    "RISK_LEVEL_BLOCKED",
    "VISIBILITY_ALLOW_INITIAL_VISIBLE",
    "VISIBILITY_REVIEW_REQUIRED",
    "VISIBILITY_META_ONLY",
    "VISIBILITY_BLOCKED",
    "P6_LOW_RISK_RELATION_FAMILIES",
    "P6_MEDIUM_RISK_RELATION_FAMILIES",
    "P6_HIGH_RISK_RELATION_FAMILIES",
    "P6_BLOCKED_RELATION_FAMILIES",
    "P6_META_ONLY_RELATION_FAMILIES",
    "build_structure_insight_p6_relation_policy",
    "structure_insight_p6_relation_policy_public_summary",
    "dump_structure_insight_p6_relation_policy_public_summary",
    "assert_structure_insight_p6_relation_policy_contract",
]
