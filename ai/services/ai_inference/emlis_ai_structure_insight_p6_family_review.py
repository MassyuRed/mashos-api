# -*- coding: utf-8 -*-
from __future__ import annotations

"""P6-7 review for long-arc and self-understanding families.

P6-6 fixes the limited surface role plan for ``structure_question``.  This
module deliberately does not copy that plan to other families.  It classifies
``long_meaning_arc`` and ``self_understanding_follow`` as allow / hold / block
review candidates using body-free metadata only.
"""

from collections.abc import Iterable, Mapping
import json
from typing import Any, Final


STRUCTURE_INSIGHT_P6_FAMILY_REVIEW_SCHEMA_VERSION: Final = (
    "cocolon.emlis.structure_insight.p6_family_review.v1"
)
STRUCTURE_INSIGHT_P6_FAMILY_REVIEW_SUMMARY_SCHEMA_VERSION: Final = (
    "cocolon.emlis.structure_insight.p6_family_review_summary.v1"
)
STRUCTURE_INSIGHT_P6_FAMILY_REVIEW_STEP: Final = "P6-7_LongMeaningArcSelfUnderstandingFollowReview"
STRUCTURE_INSIGHT_P6_FAMILY_REVIEW_SOURCE: Final = (
    "Cocolon_EmlisAI_P6_StructureInsight_FamilyReview_20260612"
)

FAMILY_STRUCTURE_QUESTION: Final = "structure_question"
FAMILY_LONG_MEANING_ARC: Final = "long_meaning_arc"
FAMILY_SELF_UNDERSTANDING_FOLLOW: Final = "self_understanding_follow"
P6_FAMILY_REVIEW_TARGET_FAMILIES: Final[tuple[str, ...]] = (
    FAMILY_LONG_MEANING_ARC,
    FAMILY_SELF_UNDERSTANDING_FOLLOW,
)

FAMILY_REVIEW_ALLOW: Final = "allow"
FAMILY_REVIEW_HOLD: Final = "hold"
FAMILY_REVIEW_BLOCK: Final = "block"
DECISION_ALLOW_REVIEW_CANDIDATE: Final = "allow_review_candidate"
DECISION_HOLD_FOR_MANUAL_REVIEW: Final = "hold_for_manual_review"
DECISION_BLOCK_REVIEW_CANDIDATE: Final = "block_review_candidate"

RELATION_DESIRE_BLOCKAGE_CONFLICT: Final = "desire_blockage_conflict"
RELATION_EFFORT_RESIDUE: Final = "effort_residue"
RELATION_MIXED_EMOTION_COEXISTENCE: Final = "mixed_emotion_coexistence"
RELATION_UNCERTAINTY_EFFORT_PAIR: Final = "uncertainty_effort_pair"
RELATION_LONG_ARC_MULTIPLE_CORE: Final = "long_arc_multiple_core"
RELATION_POSITIVE_CHANGE_RECOVERY: Final = "positive_change_recovery"
RELATION_FEAR_LOAD_PAIR: Final = "fear_load_pair"
RELATION_SELF_DENIAL_IDENTITY_SPLIT: Final = "self_denial_identity_split"
RELATION_VALUE_LINE_CROSSED: Final = "value_line_crossed"
RELATION_TARGET_JUDGEMENT_AGREEMENT: Final = "target_judgement_agreement"
RELATION_LOW_INFORMATION_UNSPECIFIED_WEIGHT: Final = "low_information_unspecified_weight"
RELATION_PERIOD_TENDENCY_FROM_SINGLE_RECORD: Final = "period_tendency_from_single_record"
RELATION_HISTORY_FACT_LINE_AS_INSIGHT: Final = "history_fact_line_as_insight"
RELATION_USER_DICTIONARY_FACT_CLAIM: Final = "user_dictionary_fact_claim"

P6_LONG_MEANING_ARC_REVIEW_RELATIONS: Final[tuple[str, ...]] = (
    RELATION_LONG_ARC_MULTIPLE_CORE,
    RELATION_DESIRE_BLOCKAGE_CONFLICT,
    RELATION_EFFORT_RESIDUE,
    RELATION_MIXED_EMOTION_COEXISTENCE,
    RELATION_UNCERTAINTY_EFFORT_PAIR,
    RELATION_POSITIVE_CHANGE_RECOVERY,
    RELATION_FEAR_LOAD_PAIR,
)
P6_SELF_UNDERSTANDING_FOLLOW_REVIEW_RELATIONS: Final[tuple[str, ...]] = (
    RELATION_UNCERTAINTY_EFFORT_PAIR,
    RELATION_MIXED_EMOTION_COEXISTENCE,
    RELATION_DESIRE_BLOCKAGE_CONFLICT,
    RELATION_FEAR_LOAD_PAIR,
)
P6_FAMILY_REVIEW_HIGH_RISK_RELATIONS: Final[tuple[str, ...]] = (
    RELATION_SELF_DENIAL_IDENTITY_SPLIT,
    RELATION_VALUE_LINE_CROSSED,
)
P6_FAMILY_REVIEW_BLOCKED_RELATIONS: Final[tuple[str, ...]] = (
    RELATION_TARGET_JUDGEMENT_AGREEMENT,
    RELATION_LOW_INFORMATION_UNSPECIFIED_WEIGHT,
    RELATION_PERIOD_TENDENCY_FROM_SINGLE_RECORD,
    RELATION_HISTORY_FACT_LINE_AS_INSIGHT,
    RELATION_USER_DICTIONARY_FACT_CLAIM,
)

VERDICT_RED: Final = "RED"
VERDICT_REPAIR_REQUIRED: Final = "REPAIR_REQUIRED"
VERDICT_YELLOW: Final = "YELLOW"
VERDICT_PASS: Final = "PASS"
VERDICT_STRUCTURE_INSIGHT_READY: Final = "STRUCTURE_INSIGHT_READY"

SURFACE_PLAN_LIMITED_STRUCTURE_INSIGHT_SEED: Final = "limited_structure_insight_seed"

REASON_FAMILY_NOT_P6_7_REVIEW_TARGET: Final = "family_not_p6_7_review_target"
REASON_RELATION_FAMILY_MISSING: Final = "relation_family_missing"
REASON_RELATION_NOT_REVIEWABLE_FOR_FAMILY: Final = "relation_not_reviewable_for_family"
REASON_HIGH_RISK_RELATION_HELD_FOR_REVIEW: Final = "high_risk_relation_held_for_review"
REASON_BLOCKED_RELATION_FAMILY: Final = "blocked_relation_family"
REASON_LONG_MEANING_ARC_SUMMARY_ONLY_BLOCKED: Final = "long_meaning_arc_summary_only_blocked"
REASON_LONG_MEANING_ARC_MULTIPLE_CORE_MISSING: Final = "long_meaning_arc_multiple_core_missing"
REASON_LONG_MEANING_ARC_RELATION_FLOW_MISSING: Final = "long_meaning_arc_relation_flow_missing"
REASON_SELF_UNDERSTANDING_OBSERVATION_INTENT_MISSING: Final = (
    "self_understanding_observation_intent_missing"
)
REASON_SELF_UNDERSTANDING_UNCERTAINTY_BOUNDARY_MISSING: Final = (
    "self_understanding_uncertainty_boundary_missing"
)
REASON_SELF_DENIAL_IDENTITY_NOT_INITIAL_AUTO_VISIBLE: Final = (
    "self_denial_identity_split_not_initial_auto_visible"
)
REASON_SELF_DENIAL_IDENTITY_FACT_BLOCKED: Final = "self_denial_identity_fact_blocked"
REASON_TARGET_JUDGEMENT_RISK_BLOCKED: Final = "target_judgement_risk_blocked"
REASON_STRUCTURE_QUESTION_SURFACE_PLAN_REUSE_BLOCKED: Final = (
    "structure_question_surface_plan_reuse_blocked"
)
REASON_P6_RELATION_POLICY_BLOCKED: Final = "p6_relation_policy_blocked"
REASON_P6_RELATION_POLICY_REVIEW_REQUIRED: Final = "p6_relation_policy_review_required"
REASON_P6_RELATION_POLICY_META_ONLY: Final = "p6_relation_policy_meta_only"
REASON_P6_QUALITY_RUBRIC_RED: Final = "p6_quality_rubric_red"
REASON_P6_QUALITY_RUBRIC_REPAIR_REQUIRED: Final = "p6_quality_rubric_repair_required"
REASON_RAW_TEXT_PAYLOAD_DETECTED: Final = "raw_text_payload_detected"
REASON_COMMENT_TEXT_BODY_DETECTED: Final = "comment_text_body_detected"
REASON_PUBLIC_CONTRACT_MUTATION_DETECTED: Final = "public_contract_mutation_detected"
REASON_FIXED_SENTENCE_TEMPLATE_DETECTED: Final = "fixed_sentence_template_detected"

_BLOCK_REASONS: Final[frozenset[str]] = frozenset(
    {
        REASON_FAMILY_NOT_P6_7_REVIEW_TARGET,
        REASON_BLOCKED_RELATION_FAMILY,
        REASON_LONG_MEANING_ARC_SUMMARY_ONLY_BLOCKED,
        REASON_SELF_DENIAL_IDENTITY_FACT_BLOCKED,
        REASON_TARGET_JUDGEMENT_RISK_BLOCKED,
        REASON_STRUCTURE_QUESTION_SURFACE_PLAN_REUSE_BLOCKED,
        REASON_P6_RELATION_POLICY_BLOCKED,
        REASON_P6_QUALITY_RUBRIC_RED,
        REASON_RAW_TEXT_PAYLOAD_DETECTED,
        REASON_COMMENT_TEXT_BODY_DETECTED,
        REASON_PUBLIC_CONTRACT_MUTATION_DETECTED,
        REASON_FIXED_SENTENCE_TEMPLATE_DETECTED,
    }
)
_HOLD_REASONS: Final[frozenset[str]] = frozenset(
    {
        REASON_RELATION_FAMILY_MISSING,
        REASON_RELATION_NOT_REVIEWABLE_FOR_FAMILY,
        REASON_HIGH_RISK_RELATION_HELD_FOR_REVIEW,
        REASON_LONG_MEANING_ARC_MULTIPLE_CORE_MISSING,
        REASON_LONG_MEANING_ARC_RELATION_FLOW_MISSING,
        REASON_SELF_UNDERSTANDING_OBSERVATION_INTENT_MISSING,
        REASON_SELF_UNDERSTANDING_UNCERTAINTY_BOUNDARY_MISSING,
        REASON_SELF_DENIAL_IDENTITY_NOT_INITIAL_AUTO_VISIBLE,
        REASON_P6_RELATION_POLICY_REVIEW_REQUIRED,
        REASON_P6_RELATION_POLICY_META_ONLY,
        REASON_P6_QUALITY_RUBRIC_REPAIR_REQUIRED,
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
        "release_allowed",
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
            "initial_auto_visible_allowed",
            "structure_question_surface_plan_reused",
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


def _int(value: Any, *, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _maybe_bool(value: Any) -> bool | None:
    if isinstance(value, bool):
        return value
    if value is None or value == "":
        return None
    if isinstance(value, str):
        text = value.strip().lower()
        if text in {"1", "true", "yes", "y", "on", "allow", "allowed", "passed"}:
            return True
        if text in {"0", "false", "no", "n", "off", "block", "blocked", "hold", "failed"}:
            return False
    return bool(value)


def _canonical_id(value: Any) -> str:
    return _clean(value).lower().replace(" ", "_").replace("-", "_")


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


def _meta_reasons(sources: Iterable[Mapping[str, Any]]) -> list[str]:
    reasons: list[str] = []
    for source in sources:
        if _contains_key(source, _TEXT_PAYLOAD_KEYS):
            reasons.append(REASON_RAW_TEXT_PAYLOAD_DETECTED)
        if _contains_key(source, _COMMENT_TEXT_PAYLOAD_KEYS):
            reasons.append(REASON_COMMENT_TEXT_BODY_DETECTED)
        if _flag_true(source, _PUBLIC_CONTRACT_TRUE_FLAGS):
            reasons.append(REASON_PUBLIC_CONTRACT_MUTATION_DETECTED)
        if _flag_true(source, _FIXED_TEMPLATE_TRUE_FLAGS):
            reasons.append(REASON_FIXED_SENTENCE_TEMPLATE_DETECTED)
    return _dedupe(reasons)


def _surface_plan_reuse_reason(*, family: str, plan: Mapping[str, Any]) -> list[str]:
    if not plan:
        return []
    source = _summary(plan)
    plan_family = _canonical_id(source.get("family"))
    plan_kind = _clean(source.get("surface_plan_kind"))
    if (
        family in P6_FAMILY_REVIEW_TARGET_FAMILIES
        and plan_family == FAMILY_STRUCTURE_QUESTION
        and plan_kind == SURFACE_PLAN_LIMITED_STRUCTURE_INSIGHT_SEED
    ):
        return [REASON_STRUCTURE_QUESTION_SURFACE_PLAN_REUSE_BLOCKED]
    return []


def _relation_policy_reasons(policy: Mapping[str, Any]) -> list[str]:
    if not policy:
        return []
    visibility = _clean(_summary(policy).get("visibility_decision"))
    if visibility == "blocked":
        return [REASON_P6_RELATION_POLICY_BLOCKED]
    if visibility == "review_required":
        return [REASON_P6_RELATION_POLICY_REVIEW_REQUIRED]
    if visibility == "meta_only":
        return [REASON_P6_RELATION_POLICY_META_ONLY]
    return []


def _quality_reasons(quality: Mapping[str, Any]) -> list[str]:
    if not quality:
        return []
    verdict = _clean(_summary(quality).get("verdict"))
    if verdict == VERDICT_RED:
        return [REASON_P6_QUALITY_RUBRIC_RED]
    if verdict == VERDICT_REPAIR_REQUIRED:
        return [REASON_P6_QUALITY_RUBRIC_REPAIR_REQUIRED]
    return []


def _long_arc_reasons(
    *,
    relation: str,
    meta: Mapping[str, Any],
    core_count: int,
    summary_only: bool | None,
    relation_flow_present: bool | None,
) -> list[str]:
    reasons: list[str] = []
    if relation in P6_FAMILY_REVIEW_BLOCKED_RELATIONS:
        reasons.append(REASON_BLOCKED_RELATION_FAMILY)
    elif relation in P6_FAMILY_REVIEW_HIGH_RISK_RELATIONS:
        reasons.append(REASON_HIGH_RISK_RELATION_HELD_FOR_REVIEW)
    elif relation and relation not in P6_LONG_MEANING_ARC_REVIEW_RELATIONS:
        reasons.append(REASON_RELATION_NOT_REVIEWABLE_FOR_FAMILY)
    if summary_only is True:
        reasons.append(REASON_LONG_MEANING_ARC_SUMMARY_ONLY_BLOCKED)
    if core_count < 2:
        reasons.append(REASON_LONG_MEANING_ARC_MULTIPLE_CORE_MISSING)
    if relation_flow_present is not True:
        reasons.append(REASON_LONG_MEANING_ARC_RELATION_FLOW_MISSING)
    if _maybe_bool(meta.get("target_judgement_risk")) is True:
        reasons.append(REASON_TARGET_JUDGEMENT_RISK_BLOCKED)
    return _dedupe(reasons)


def _self_understanding_reasons(
    *,
    relation: str,
    meta: Mapping[str, Any],
    observation_intent: bool | None,
    uncertainty_boundary: bool | None,
    self_denial_fact: bool | None,
    target_judgement_risk: bool | None,
) -> list[str]:
    reasons: list[str] = []
    if relation in P6_FAMILY_REVIEW_BLOCKED_RELATIONS:
        reasons.append(REASON_BLOCKED_RELATION_FAMILY)
    elif relation == RELATION_SELF_DENIAL_IDENTITY_SPLIT:
        reasons.append(REASON_SELF_DENIAL_IDENTITY_NOT_INITIAL_AUTO_VISIBLE)
        reasons.append(REASON_HIGH_RISK_RELATION_HELD_FOR_REVIEW)
    elif relation == RELATION_VALUE_LINE_CROSSED:
        reasons.append(REASON_HIGH_RISK_RELATION_HELD_FOR_REVIEW)
    elif relation and relation not in P6_SELF_UNDERSTANDING_FOLLOW_REVIEW_RELATIONS:
        reasons.append(REASON_RELATION_NOT_REVIEWABLE_FOR_FAMILY)
    if observation_intent is not True:
        reasons.append(REASON_SELF_UNDERSTANDING_OBSERVATION_INTENT_MISSING)
    if uncertainty_boundary is not True:
        reasons.append(REASON_SELF_UNDERSTANDING_UNCERTAINTY_BOUNDARY_MISSING)
    if self_denial_fact is True or _maybe_bool(meta.get("self_denial_identity_claim_as_fact")) is True:
        reasons.append(REASON_SELF_DENIAL_IDENTITY_FACT_BLOCKED)
    if target_judgement_risk is True or _maybe_bool(meta.get("target_judgement_risk")) is True:
        reasons.append(REASON_TARGET_JUDGEMENT_RISK_BLOCKED)
    return _dedupe(reasons)


def _classification_for(reasons: Iterable[str]) -> tuple[str, str]:
    reason_set = set(reasons)
    if reason_set.intersection(_BLOCK_REASONS):
        return FAMILY_REVIEW_BLOCK, DECISION_BLOCK_REVIEW_CANDIDATE
    if reason_set.intersection(_HOLD_REASONS) or reason_set:
        return FAMILY_REVIEW_HOLD, DECISION_HOLD_FOR_MANUAL_REVIEW
    return FAMILY_REVIEW_ALLOW, DECISION_ALLOW_REVIEW_CANDIDATE


def build_structure_insight_p6_family_review(
    *,
    family: Any = None,
    relation_family: Any = None,
    family_review_meta: Mapping[str, Any] | None = None,
    p6_surface_role_plan: Mapping[str, Any] | None = None,
    p6_relation_policy: Mapping[str, Any] | None = None,
    p6_quality_rubric: Mapping[str, Any] | None = None,
    long_arc_core_count: Any = None,
    long_arc_summary_only: Any = None,
    long_arc_relation_flow_present: Any = None,
    self_understanding_observation_intent: Any = None,
    self_understanding_uncertainty_boundary: Any = None,
    self_denial_identity_fact_required: Any = None,
    target_judgement_risk: Any = None,
    run_id: str | None = None,
) -> dict[str, Any]:
    """Build a body-free P6-7 family review row."""

    run = _clean(run_id) or "p6_family_review"
    meta = _safe_mapping(family_review_meta)
    surface_plan = _safe_mapping(p6_surface_role_plan)
    relation_policy = _safe_mapping(p6_relation_policy)
    quality = _safe_mapping(p6_quality_rubric)
    resolved_family = _canonical_id(family) or _canonical_id(meta.get("family"))
    relation = (
        _canonical_id(relation_family)
        or _canonical_id(meta.get("relation_family"))
        or _canonical_id(_summary(relation_policy).get("relation_family"))
    )
    core_count = _int(long_arc_core_count if long_arc_core_count is not None else meta.get("long_arc_core_count"))
    summary_only = _maybe_bool(
        long_arc_summary_only if long_arc_summary_only is not None else meta.get("long_arc_summary_only")
    )
    relation_flow_present = _maybe_bool(
        long_arc_relation_flow_present
        if long_arc_relation_flow_present is not None
        else meta.get("long_arc_relation_flow_present")
    )
    observation_intent = _maybe_bool(
        self_understanding_observation_intent
        if self_understanding_observation_intent is not None
        else meta.get("self_understanding_observation_intent")
    )
    uncertainty_boundary = _maybe_bool(
        self_understanding_uncertainty_boundary
        if self_understanding_uncertainty_boundary is not None
        else meta.get("self_understanding_uncertainty_boundary")
    )
    self_denial_fact = _maybe_bool(
        self_denial_identity_fact_required
        if self_denial_identity_fact_required is not None
        else meta.get("self_denial_identity_fact_required")
    )
    target_judgement = _maybe_bool(
        target_judgement_risk if target_judgement_risk is not None else meta.get("target_judgement_risk")
    )

    reasons: list[str] = []
    reasons.extend(_meta_reasons((meta, surface_plan, relation_policy, quality)))
    reasons.extend(_surface_plan_reuse_reason(family=resolved_family, plan=surface_plan))
    reasons.extend(_relation_policy_reasons(relation_policy))
    reasons.extend(_quality_reasons(quality))
    if resolved_family not in P6_FAMILY_REVIEW_TARGET_FAMILIES:
        reasons.append(REASON_FAMILY_NOT_P6_7_REVIEW_TARGET)
    if not relation:
        reasons.append(REASON_RELATION_FAMILY_MISSING)
    elif resolved_family == FAMILY_LONG_MEANING_ARC:
        reasons.extend(
            _long_arc_reasons(
                relation=relation,
                meta=meta,
                core_count=core_count,
                summary_only=summary_only,
                relation_flow_present=relation_flow_present,
            )
        )
    elif resolved_family == FAMILY_SELF_UNDERSTANDING_FOLLOW:
        reasons.extend(
            _self_understanding_reasons(
                relation=relation,
                meta=meta,
                observation_intent=observation_intent,
                uncertainty_boundary=uncertainty_boundary,
                self_denial_fact=self_denial_fact,
                target_judgement_risk=target_judgement,
            )
        )

    reasons = _dedupe(reasons)
    classification, decision = _classification_for(reasons)
    allow = classification == FAMILY_REVIEW_ALLOW
    hold = classification == FAMILY_REVIEW_HOLD
    block = classification == FAMILY_REVIEW_BLOCK
    high_risk_held = REASON_HIGH_RISK_RELATION_HELD_FOR_REVIEW in reasons
    self_denial_not_auto = (
        relation == RELATION_SELF_DENIAL_IDENTITY_SPLIT
        or REASON_SELF_DENIAL_IDENTITY_NOT_INITIAL_AUTO_VISIBLE in reasons
    )
    long_arc_not_summary_only = resolved_family != FAMILY_LONG_MEANING_ARC or (
        summary_only is not True and REASON_LONG_MEANING_ARC_SUMMARY_ONLY_BLOCKED not in reasons
    )

    summary = {
        "schema_version": STRUCTURE_INSIGHT_P6_FAMILY_REVIEW_SUMMARY_SCHEMA_VERSION,
        "version": STRUCTURE_INSIGHT_P6_FAMILY_REVIEW_SUMMARY_SCHEMA_VERSION,
        "source": STRUCTURE_INSIGHT_P6_FAMILY_REVIEW_SOURCE,
        "step": STRUCTURE_INSIGHT_P6_FAMILY_REVIEW_STEP,
        "run_id": run,
        "family": resolved_family,
        "relation_family": relation,
        "family_review_classification": classification,
        "decision": decision,
        "allow": allow,
        "hold": hold,
        "block": block,
        "review_only": True,
        "initial_auto_visible_allowed": False,
        "initial_auto_visible_blocked": True,
        "structure_question_surface_plan_reused": False,
        "structure_question_surface_plan_reuse_blocked": (
            REASON_STRUCTURE_QUESTION_SURFACE_PLAN_REUSE_BLOCKED in reasons
        ),
        "high_risk_relation_held": high_risk_held,
        "self_denial_identity_split_not_initial_auto_visible": self_denial_not_auto,
        "self_denial_identity_fact_blocked": REASON_SELF_DENIAL_IDENTITY_FACT_BLOCKED in reasons,
        "long_meaning_arc_not_summary_only_enforced": long_arc_not_summary_only,
        "long_arc_core_count": core_count,
        "long_arc_relation_flow_present": relation_flow_present is True,
        "self_understanding_observation_intent_present": observation_intent is True,
        "self_understanding_uncertainty_boundary_present": uncertainty_boundary is True,
        "target_judgement_risk_blocked": REASON_TARGET_JUDGEMENT_RISK_BLOCKED in reasons,
        "decision_reason_codes": reasons,
        "review_target_families": list(P6_FAMILY_REVIEW_TARGET_FAMILIES),
        "long_meaning_arc_review_relations": list(P6_LONG_MEANING_ARC_REVIEW_RELATIONS),
        "self_understanding_follow_review_relations": list(P6_SELF_UNDERSTANDING_FOLLOW_REVIEW_RELATIONS),
        "high_risk_review_relations": list(P6_FAMILY_REVIEW_HIGH_RISK_RELATIONS),
        "blocked_relation_families": list(P6_FAMILY_REVIEW_BLOCKED_RELATIONS),
        "public_contract": _public_contract(),
        "body_free": _body_free_contract(),
    }
    review = {
        "schema_version": STRUCTURE_INSIGHT_P6_FAMILY_REVIEW_SCHEMA_VERSION,
        "version": STRUCTURE_INSIGHT_P6_FAMILY_REVIEW_SCHEMA_VERSION,
        "source": STRUCTURE_INSIGHT_P6_FAMILY_REVIEW_SOURCE,
        "step": STRUCTURE_INSIGHT_P6_FAMILY_REVIEW_STEP,
        "run_id": run,
        "family": resolved_family,
        "relation_family": relation,
        "family_review_classification": classification,
        "decision": decision,
        "allow": allow,
        "hold": hold,
        "block": block,
        "review_only": True,
        "initial_auto_visible_allowed": False,
        "initial_auto_visible_blocked": True,
        "structure_question_surface_plan_reused": False,
        "high_risk_relation_held": high_risk_held,
        "self_denial_identity_split_not_initial_auto_visible": self_denial_not_auto,
        "long_meaning_arc_not_summary_only_enforced": long_arc_not_summary_only,
        "decision_reason_codes": reasons,
        "public_response_key_added": False,
        "rn_visible_contract_changed": False,
        "response_shape_changed": False,
        "fixed_sentence_template_added": False,
        "input_specific_template_added": False,
        "release_allowed": False,
        "public_release_applied": False,
        "public_contract": _public_contract(),
        "body_free": _body_free_contract(),
        "summary": summary,
    }
    assert_structure_insight_p6_family_review_contract(review)
    return review


def assert_structure_insight_p6_family_review_contract(
    review: Mapping[str, Any],
    *,
    allow_partial: bool = False,
) -> bool:
    """Validate that the P6-7 family review remains body-free and review-only."""

    if not isinstance(review, Mapping):
        raise TypeError("P6 family review must be a mapping")
    data = _safe_mapping(review)
    if not allow_partial and data.get("schema_version") != STRUCTURE_INSIGHT_P6_FAMILY_REVIEW_SCHEMA_VERSION:
        raise ValueError("Unexpected P6 family review schema version")
    if not allow_partial and data.get("step") != STRUCTURE_INSIGHT_P6_FAMILY_REVIEW_STEP:
        raise ValueError("Unexpected P6 family review step")
    if _contains_key(data, _TEXT_PAYLOAD_KEYS | _COMMENT_TEXT_PAYLOAD_KEYS):
        raise ValueError("P6 family review must not include text body keys")
    if _flag_true(data, _FORBIDDEN_TRUE_FLAGS):
        raise ValueError("P6 family review contains forbidden true flags")
    public_contract = _safe_mapping(data.get("public_contract"))
    if public_contract and _flag_true(public_contract, _PUBLIC_CONTRACT_TRUE_FLAGS | _FIXED_TEMPLATE_TRUE_FLAGS):
        raise ValueError("P6 family review mutates public contract or adds templates")
    body_free = _safe_mapping(data.get("body_free"))
    if body_free and _flag_true(body_free, _FORBIDDEN_TRUE_FLAGS):
        raise ValueError("P6 family review includes body payload flags")
    summary = _safe_mapping(data.get("summary"))
    if summary:
        if not allow_partial and summary.get("schema_version") != STRUCTURE_INSIGHT_P6_FAMILY_REVIEW_SUMMARY_SCHEMA_VERSION:
            raise ValueError("Unexpected P6 family review summary schema version")
        if _contains_key(summary, _TEXT_PAYLOAD_KEYS | _COMMENT_TEXT_PAYLOAD_KEYS):
            raise ValueError("P6 family review summary must not include text body keys")
        if _flag_true(summary, _FORBIDDEN_TRUE_FLAGS):
            raise ValueError("P6 family review summary contains forbidden true flags")
    return True


def dump_structure_insight_p6_family_review_public_summary(review: Mapping[str, Any]) -> str:
    """Serialize only safe P6-7 review metadata."""

    data = _safe_mapping(review)
    assert_structure_insight_p6_family_review_contract(data)
    summary = _safe_mapping(data.get("summary")) or data
    assert_structure_insight_p6_family_review_contract(summary, allow_partial=True)
    safe_summary = {
        "schema_version": summary.get("schema_version"),
        "step": summary.get("step"),
        "run_id": summary.get("run_id"),
        "family": summary.get("family"),
        "relation_family": summary.get("relation_family"),
        "family_review_classification": summary.get("family_review_classification"),
        "decision": summary.get("decision"),
        "review_only": True,
        "initial_auto_visible_allowed": False,
        "self_denial_identity_split_not_initial_auto_visible": summary.get(
            "self_denial_identity_split_not_initial_auto_visible"
        ),
        "long_meaning_arc_not_summary_only_enforced": summary.get(
            "long_meaning_arc_not_summary_only_enforced"
        ),
        "high_risk_relation_held": summary.get("high_risk_relation_held"),
        "decision_reason_codes": list(summary.get("decision_reason_codes") or []),
        "public_contract": _safe_mapping(summary.get("public_contract")),
        "body_free": _safe_mapping(summary.get("body_free")),
    }
    assert_structure_insight_p6_family_review_contract(safe_summary, allow_partial=True)
    return json.dumps(safe_summary, ensure_ascii=False, sort_keys=True)
