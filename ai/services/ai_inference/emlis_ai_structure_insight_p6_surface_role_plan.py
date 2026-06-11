# -*- coding: utf-8 -*-
from __future__ import annotations

"""P6-6 limited surface role plan for ``structure_question``.

The plan decides whether a P6 Structure Insight candidate may be treated as a
limited surface connection candidate, and where it may sit.  It does not render
or return a visible sentence.  The output is body-free and keeps the initial
connection limited to ``structure_question`` only.
"""

from collections.abc import Iterable, Mapping
import json
from typing import Any, Final


STRUCTURE_INSIGHT_P6_SURFACE_ROLE_PLAN_SCHEMA_VERSION: Final = (
    "cocolon.emlis.structure_insight.p6_surface_role_plan.v1"
)
STRUCTURE_INSIGHT_P6_SURFACE_ROLE_PLAN_SUMMARY_SCHEMA_VERSION: Final = (
    "cocolon.emlis.structure_insight.p6_surface_role_plan_summary.v1"
)
STRUCTURE_INSIGHT_P6_SURFACE_ROLE_PLAN_STEP: Final = "P6-6_LimitedSurfaceRolePlanForStructureQuestion"
STRUCTURE_INSIGHT_P6_SURFACE_ROLE_PLAN_SOURCE: Final = (
    "Cocolon_EmlisAI_P6_StructureInsight_LimitedSurfaceRolePlan_20260611"
)

FAMILY_STRUCTURE_QUESTION: Final = "structure_question"
FAMILY_LONG_MEANING_ARC: Final = "long_meaning_arc"
FAMILY_SELF_UNDERSTANDING_FOLLOW: Final = "self_understanding_follow"

SURFACE_PLAN_LIMITED_STRUCTURE_INSIGHT_SEED: Final = "limited_structure_insight_seed"
SURFACE_PLAN_META_ONLY: Final = "meta_only"
SURFACE_PLAN_BLOCKED: Final = "blocked"

SECTION_CURRENT_OBSERVATION: Final = "current_observation"
SECTION_STRUCTURE_INSIGHT_SEED: Final = "structure_insight_seed"
SECTION_HUMAN_RECEPTION: Final = "human_reception"
SECTION_SAFETY_BOUNDARY: Final = "safety_boundary"
P6_SURFACE_ROLE_PLAN_SECTION_ORDER: Final[tuple[str, ...]] = (
    SECTION_CURRENT_OBSERVATION,
    SECTION_STRUCTURE_INSIGHT_SEED,
    SECTION_HUMAN_RECEPTION,
    SECTION_SAFETY_BOUNDARY,
)

ROLE_OBSERVATION_INSIGHT_SEED: Final = "observation_insight_seed"
ROLE_STRUCTURE_INSIGHT_TEMPERATURE_SUPPORT: Final = "structure_insight_temperature_support"
ROLE_SOFT_INFERENCE_SURFACE_REQUIRED: Final = "soft_inference_surface_required"
ROLE_CURRENT_INPUT_GROUNDED_RELATION: Final = "current_input_grounded_relation"
ROLE_NOT_PERSONALITY_BOUNDARY: Final = "not_personality_boundary"
ROLE_NOT_CAUSE_BOUNDARY: Final = "not_cause_boundary"
ROLE_NON_IMPOSING_RECEPTION_BOUNDARY: Final = "non_imposing_reception_boundary"
ROLE_GATE_PASSED_SURFACE_ONLY: Final = "gate_passed_surface_only"

P6_SURFACE_ROLE_PLAN_MUST_INCLUDE_ROLES: Final[tuple[str, ...]] = (
    ROLE_OBSERVATION_INSIGHT_SEED,
    ROLE_STRUCTURE_INSIGHT_TEMPERATURE_SUPPORT,
    ROLE_SOFT_INFERENCE_SURFACE_REQUIRED,
    ROLE_CURRENT_INPUT_GROUNDED_RELATION,
    ROLE_NOT_PERSONALITY_BOUNDARY,
    ROLE_NOT_CAUSE_BOUNDARY,
)
P6_SURFACE_ROLE_PLAN_MUST_NOT_INCLUDE_ROLES: Final[tuple[str, ...]] = (
    "diagnosis",
    "personality_label",
    "cause_answer",
    "advice",
    "future_prediction",
    "target_judgement",
    "history_fact_assertion",
)

RELATION_DESIRE_BLOCKAGE_CONFLICT: Final = "desire_blockage_conflict"
RELATION_EFFORT_RESIDUE: Final = "effort_residue"
RELATION_MIXED_EMOTION_COEXISTENCE: Final = "mixed_emotion_coexistence"
RELATION_UNCERTAINTY_EFFORT_PAIR: Final = "uncertainty_effort_pair"
RELATION_SELF_DENIAL_IDENTITY_SPLIT: Final = "self_denial_identity_split"
RELATION_VALUE_LINE_CROSSED: Final = "value_line_crossed"
RELATION_LOW_INFORMATION_UNSPECIFIED_WEIGHT: Final = "low_information_unspecified_weight"
RELATION_PERIOD_TENDENCY_FROM_SINGLE_RECORD: Final = "period_tendency_from_single_record"
RELATION_HISTORY_FACT_LINE_AS_INSIGHT: Final = "history_fact_line_as_insight"
RELATION_TARGET_JUDGEMENT_AGREEMENT: Final = "target_judgement_agreement"
RELATION_USER_DICTIONARY_FACT_CLAIM: Final = "user_dictionary_fact_claim"

P6_STRUCTURE_QUESTION_ALLOWED_RELATION_FAMILIES: Final[tuple[str, ...]] = (
    RELATION_DESIRE_BLOCKAGE_CONFLICT,
    RELATION_EFFORT_RESIDUE,
    RELATION_MIXED_EMOTION_COEXISTENCE,
    RELATION_UNCERTAINTY_EFFORT_PAIR,
)
P6_STRUCTURE_QUESTION_INITIAL_BLOCK_RELATION_FAMILIES: Final[tuple[str, ...]] = (
    RELATION_SELF_DENIAL_IDENTITY_SPLIT,
    RELATION_LOW_INFORMATION_UNSPECIFIED_WEIGHT,
    RELATION_PERIOD_TENDENCY_FROM_SINGLE_RECORD,
    RELATION_HISTORY_FACT_LINE_AS_INSIGHT,
    RELATION_TARGET_JUDGEMENT_AGREEMENT,
    RELATION_USER_DICTIONARY_FACT_CLAIM,
)

VISIBILITY_ALLOW_INITIAL_VISIBLE: Final = "allow_initial_visible"
GATE_DECISION_ALLOW_INTERNAL_SURFACE_CANDIDATE: Final = "allow_internal_surface_candidate"
VERDICT_STRUCTURE_INSIGHT_READY: Final = "STRUCTURE_INSIGHT_READY"

REASON_FAMILY_NOT_STRUCTURE_QUESTION: Final = "family_not_structure_question_surface_role_target"
REASON_FAMILY_REVIEW_DEFERRED_TO_P6_7: Final = "family_review_deferred_to_p6_7"
REASON_RELATION_FAMILY_MISSING: Final = "relation_family_missing"
REASON_RELATION_NOT_ALLOWED_FOR_STRUCTURE_QUESTION: Final = "relation_not_allowed_for_structure_question_initial_surface"
REASON_INITIAL_BLOCK_RELATION_FAMILY: Final = "initial_block_relation_family"
REASON_VALUE_LINE_TARGET_JUDGEMENT_RISK_BLOCKED: Final = "value_line_target_judgement_risk_blocked"
REASON_P6_FAMILY_BOUNDARY_NOT_ALLOWING_SURFACE: Final = "p6_family_boundary_not_allowing_surface"
REASON_P6_RELATION_POLICY_NOT_INITIAL_VISIBLE: Final = "p6_relation_policy_not_initial_visible"
REASON_P6_QUALITY_RUBRIC_NOT_STRUCTURE_READY: Final = "p6_quality_rubric_not_structure_ready"
REASON_P6_GATE_HARDENING_REQUIRED: Final = "p6_gate_hardening_required"
REASON_P6_GATE_HARDENING_NOT_PASSED: Final = "p6_gate_hardening_not_passed"
REASON_INSIGHT_SEED_COUNT_ABOVE_LIMIT: Final = "insight_seed_count_above_limit"
REASON_RAW_TEXT_PAYLOAD_DETECTED: Final = "raw_text_payload_detected"
REASON_COMMENT_TEXT_BODY_DETECTED: Final = "comment_text_body_detected"
REASON_PUBLIC_CONTRACT_MUTATION_DETECTED: Final = "public_contract_mutation_detected"
REASON_FIXED_SENTENCE_TEMPLATE_DETECTED: Final = "fixed_sentence_template_detected"

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
            "comment_text_written_by_gate",
            "surface_body_returned",
            "candidate_body_returned",
            "gate_bypass_allowed",
            "ungated_surface_connected",
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


def _int(value: Any, *, default: int = 1) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


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
        "surface_body_included": False,
        "comment_text_body_included": False,
        "candidate_body_included": False,
        "raw_input_included": False,
        "raw_text_included": False,
        "input_text_included": False,
        "history_raw_text_included": False,
        "reviewer_free_text_included": False,
        "raw_test_output_included": False,
        "command_output_included": False,
        "terminal_output_included": False,
    }


def _section_role_plan() -> dict[str, list[str]]:
    return {
        SECTION_CURRENT_OBSERVATION: [ROLE_CURRENT_INPUT_GROUNDED_RELATION],
        SECTION_STRUCTURE_INSIGHT_SEED: [
            ROLE_OBSERVATION_INSIGHT_SEED,
            ROLE_SOFT_INFERENCE_SURFACE_REQUIRED,
            ROLE_NOT_PERSONALITY_BOUNDARY,
            ROLE_NOT_CAUSE_BOUNDARY,
            ROLE_GATE_PASSED_SURFACE_ONLY,
        ],
        SECTION_HUMAN_RECEPTION: [
            ROLE_STRUCTURE_INSIGHT_TEMPERATURE_SUPPORT,
            ROLE_NON_IMPOSING_RECEPTION_BOUNDARY,
        ],
        SECTION_SAFETY_BOUNDARY: list(P6_SURFACE_ROLE_PLAN_MUST_NOT_INCLUDE_ROLES),
    }


def _family_boundary_allows_surface(value: Mapping[str, Any]) -> bool | None:
    if not value:
        return None
    source = _summary(value)
    if source.get("allow_limited_surface") is True or source.get("limited_surface_candidate") is True:
        return True
    if source.get("block") is True or source.get("hold") is True or source.get("meta_only") is True:
        return False
    decision = _clean(source.get("decision"))
    if decision == "allow_limited_surface":
        return True
    if decision in {"block", "hold", "meta_only"}:
        return False
    return None


def _relation_policy_visibility(value: Mapping[str, Any]) -> str:
    if not value:
        return ""
    return _clean(_summary(value).get("visibility_decision"))


def _quality_verdict(value: Mapping[str, Any]) -> str:
    if not value:
        return ""
    return _clean(_summary(value).get("verdict"))


def _gate_passed(value: Mapping[str, Any]) -> bool | None:
    if not value:
        return None
    source = _summary(value)
    decision = _clean(source.get("decision"))
    if source.get("passed") is True and decision == GATE_DECISION_ALLOW_INTERNAL_SURFACE_CANDIDATE:
        return True
    if source.get("blocked") is True or source.get("review_required") is True:
        return False
    if decision:
        return decision == GATE_DECISION_ALLOW_INTERNAL_SURFACE_CANDIDATE
    return None


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


def _plan_kind_from_reasons(reasons: Iterable[str]) -> str:
    reason_set = set(reasons)
    if not reason_set:
        return SURFACE_PLAN_LIMITED_STRUCTURE_INSIGHT_SEED
    if reason_set == {REASON_FAMILY_REVIEW_DEFERRED_TO_P6_7}:
        return SURFACE_PLAN_META_ONLY
    if reason_set == {REASON_RELATION_NOT_ALLOWED_FOR_STRUCTURE_QUESTION}:
        return SURFACE_PLAN_META_ONLY
    return SURFACE_PLAN_BLOCKED


def build_structure_insight_p6_surface_role_plan(
    *,
    family: Any = FAMILY_STRUCTURE_QUESTION,
    relation_family: Any = None,
    p6_family_boundary: Mapping[str, Any] | None = None,
    p6_relation_policy: Mapping[str, Any] | None = None,
    p6_quality_rubric: Mapping[str, Any] | None = None,
    p6_gate_hardening: Mapping[str, Any] | None = None,
    requested_insight_seed_count: Any = 1,
    target_judgement_risk: Any = None,
    surface_plan_meta: Mapping[str, Any] | None = None,
    run_id: str | None = None,
) -> dict[str, Any]:
    """Build a body-free P6-6 role plan."""

    run = _clean(run_id) or "p6_surface_role_plan"
    resolved_family = _canonical_id(family)
    boundary = _safe_mapping(p6_family_boundary)
    policy = _safe_mapping(p6_relation_policy)
    quality = _safe_mapping(p6_quality_rubric)
    gate = _safe_mapping(p6_gate_hardening)
    meta = _safe_mapping(surface_plan_meta)
    relation = _canonical_id(relation_family) or _canonical_id(_summary(policy).get("relation_family"))
    boundary_allows = _family_boundary_allows_surface(boundary)
    visibility_decision = _relation_policy_visibility(policy)
    quality_state = _quality_verdict(quality)
    gate_state = _gate_passed(gate)
    requested_seed_count = max(0, _int(requested_insight_seed_count, default=1))
    has_target_judgement_risk = bool(
        target_judgement_risk is True
        or meta.get("target_judgement_risk") is True
        or _summary(policy).get("target_judgement_blocked") is True
    )

    reasons: list[str] = []
    reasons.extend(_meta_reasons((boundary, policy, quality, gate, meta)))
    if resolved_family != FAMILY_STRUCTURE_QUESTION:
        if resolved_family in {FAMILY_LONG_MEANING_ARC, FAMILY_SELF_UNDERSTANDING_FOLLOW}:
            reasons.append(REASON_FAMILY_REVIEW_DEFERRED_TO_P6_7)
        else:
            reasons.append(REASON_FAMILY_NOT_STRUCTURE_QUESTION)
    if not relation:
        reasons.append(REASON_RELATION_FAMILY_MISSING)
    elif relation in P6_STRUCTURE_QUESTION_INITIAL_BLOCK_RELATION_FAMILIES:
        reasons.append(REASON_INITIAL_BLOCK_RELATION_FAMILY)
    elif relation == RELATION_VALUE_LINE_CROSSED and has_target_judgement_risk:
        reasons.append(REASON_VALUE_LINE_TARGET_JUDGEMENT_RISK_BLOCKED)
    elif relation not in P6_STRUCTURE_QUESTION_ALLOWED_RELATION_FAMILIES:
        reasons.append(REASON_RELATION_NOT_ALLOWED_FOR_STRUCTURE_QUESTION)

    requires_surface_prereqs = (
        resolved_family == FAMILY_STRUCTURE_QUESTION
        and relation in P6_STRUCTURE_QUESTION_ALLOWED_RELATION_FAMILIES
        and REASON_RELATION_NOT_ALLOWED_FOR_STRUCTURE_QUESTION not in reasons
    )
    if requires_surface_prereqs:
        if boundary_allows is not True:
            reasons.append(REASON_P6_FAMILY_BOUNDARY_NOT_ALLOWING_SURFACE)
        if visibility_decision != VISIBILITY_ALLOW_INITIAL_VISIBLE:
            reasons.append(REASON_P6_RELATION_POLICY_NOT_INITIAL_VISIBLE)
        if quality_state != VERDICT_STRUCTURE_INSIGHT_READY:
            reasons.append(REASON_P6_QUALITY_RUBRIC_NOT_STRUCTURE_READY)
        if gate_state is None:
            reasons.append(REASON_P6_GATE_HARDENING_REQUIRED)
        elif gate_state is not True:
            reasons.append(REASON_P6_GATE_HARDENING_NOT_PASSED)
        if requested_seed_count > 1:
            reasons.append(REASON_INSIGHT_SEED_COUNT_ABOVE_LIMIT)

    reasons = _dedupe(reasons)
    surface_plan_kind = _plan_kind_from_reasons(reasons)
    limited_surface_candidate = surface_plan_kind == SURFACE_PLAN_LIMITED_STRUCTURE_INSIGHT_SEED
    planned_seed_count = 1 if limited_surface_candidate else 0

    summary = {
        "schema_version": STRUCTURE_INSIGHT_P6_SURFACE_ROLE_PLAN_SUMMARY_SCHEMA_VERSION,
        "version": STRUCTURE_INSIGHT_P6_SURFACE_ROLE_PLAN_SUMMARY_SCHEMA_VERSION,
        "source": STRUCTURE_INSIGHT_P6_SURFACE_ROLE_PLAN_SOURCE,
        "step": STRUCTURE_INSIGHT_P6_SURFACE_ROLE_PLAN_STEP,
        "run_id": run,
        "family": resolved_family,
        "relation_family": relation,
        "surface_plan_kind": surface_plan_kind,
        "limited_surface_candidate": limited_surface_candidate,
        "planned_insight_seed_count": planned_seed_count,
        "requested_insight_seed_count": requested_seed_count,
        "max_insight_seed_count": 1,
        "observation_section_seed_count": planned_seed_count,
        "human_reception_softening_required": True,
        "non_imposing_reception_boundary": True,
        "gate_pass_required": True,
        "gate_passed": gate_state is True,
        "ungated_surface_connected": False,
        "section_order": list(P6_SURFACE_ROLE_PLAN_SECTION_ORDER),
        "must_include_roles": list(P6_SURFACE_ROLE_PLAN_MUST_INCLUDE_ROLES),
        "must_not_include_roles": list(P6_SURFACE_ROLE_PLAN_MUST_NOT_INCLUDE_ROLES),
        "section_role_plan": _section_role_plan(),
        "allowed_structure_question_relation_families": list(P6_STRUCTURE_QUESTION_ALLOWED_RELATION_FAMILIES),
        "blocked_structure_question_relation_families": list(P6_STRUCTURE_QUESTION_INITIAL_BLOCK_RELATION_FAMILIES),
        "decision_reason_codes": reasons,
        "public_contract": _public_contract(),
        "body_free": _body_free_contract(),
    }
    plan = {
        "schema_version": STRUCTURE_INSIGHT_P6_SURFACE_ROLE_PLAN_SCHEMA_VERSION,
        "version": STRUCTURE_INSIGHT_P6_SURFACE_ROLE_PLAN_SCHEMA_VERSION,
        "source": STRUCTURE_INSIGHT_P6_SURFACE_ROLE_PLAN_SOURCE,
        "step": STRUCTURE_INSIGHT_P6_SURFACE_ROLE_PLAN_STEP,
        "run_id": run,
        "family": resolved_family,
        "relation_family": relation,
        "surface_plan_kind": surface_plan_kind,
        "limited_surface_candidate": limited_surface_candidate,
        "section_order": list(P6_SURFACE_ROLE_PLAN_SECTION_ORDER),
        "max_insight_seed_count": 1,
        "planned_insight_seed_count": planned_seed_count,
        "observation_section_seed_count": planned_seed_count,
        "must_include_roles": list(P6_SURFACE_ROLE_PLAN_MUST_INCLUDE_ROLES),
        "must_not_include_roles": list(P6_SURFACE_ROLE_PLAN_MUST_NOT_INCLUDE_ROLES),
        "section_role_plan": _section_role_plan(),
        "gate_pass_required": True,
        "gate_passed": gate_state is True,
        "ungated_surface_connected": False,
        "fixed_sentence_template_added": False,
        "input_specific_template_added": False,
        "public_response_key_added": False,
        "rn_visible_contract_changed": False,
        "response_shape_changed": False,
        "release_allowed": False,
        "public_release_applied": False,
        "decision_reason_codes": reasons,
        "public_contract": _public_contract(),
        "body_free": _body_free_contract(),
        "summary": summary,
    }
    assert_structure_insight_p6_surface_role_plan_contract(plan)
    return plan


def assert_structure_insight_p6_surface_role_plan_contract(
    plan: Mapping[str, Any],
    *,
    allow_partial: bool = False,
) -> bool:
    """Validate the P6-6 role plan contract."""

    if not isinstance(plan, Mapping):
        raise TypeError("P6 surface role plan must be a mapping")
    data = _safe_mapping(plan)
    if not allow_partial and data.get("schema_version") != STRUCTURE_INSIGHT_P6_SURFACE_ROLE_PLAN_SCHEMA_VERSION:
        raise ValueError("Unexpected P6 surface role plan schema version")
    if not allow_partial and data.get("step") != STRUCTURE_INSIGHT_P6_SURFACE_ROLE_PLAN_STEP:
        raise ValueError("Unexpected P6 surface role plan step")
    if data.get("max_insight_seed_count") not in {None, 1}:
        raise ValueError("P6 surface role plan must limit insight seed count to one")
    if _contains_key(data, _TEXT_PAYLOAD_KEYS | _COMMENT_TEXT_PAYLOAD_KEYS):
        raise ValueError("P6 surface role plan must not include text body keys")
    if _flag_true(data, _FORBIDDEN_TRUE_FLAGS):
        raise ValueError("P6 surface role plan contains forbidden true flags")
    public_contract = _safe_mapping(data.get("public_contract"))
    if public_contract and _flag_true(public_contract, _PUBLIC_CONTRACT_TRUE_FLAGS | _FIXED_TEMPLATE_TRUE_FLAGS):
        raise ValueError("P6 surface role plan mutates public contract or adds templates")
    body_free = _safe_mapping(data.get("body_free"))
    if body_free and _flag_true(body_free, _FORBIDDEN_TRUE_FLAGS):
        raise ValueError("P6 surface role plan includes body payload flags")
    summary = _safe_mapping(data.get("summary"))
    if summary:
        if not allow_partial and summary.get("schema_version") != STRUCTURE_INSIGHT_P6_SURFACE_ROLE_PLAN_SUMMARY_SCHEMA_VERSION:
            raise ValueError("Unexpected P6 surface role plan summary schema version")
        if _contains_key(summary, _TEXT_PAYLOAD_KEYS | _COMMENT_TEXT_PAYLOAD_KEYS):
            raise ValueError("P6 surface role plan summary must not include text body keys")
        if _flag_true(summary, _FORBIDDEN_TRUE_FLAGS):
            raise ValueError("P6 surface role plan summary contains forbidden true flags")
    return True


def dump_structure_insight_p6_surface_role_plan_public_summary(plan: Mapping[str, Any]) -> str:
    """Serialize only the body-free P6-6 summary."""

    data = _safe_mapping(plan)
    assert_structure_insight_p6_surface_role_plan_contract(data)
    summary = _safe_mapping(data.get("summary")) or data
    assert_structure_insight_p6_surface_role_plan_contract(summary, allow_partial=True)
    safe_summary = {
        "schema_version": summary.get("schema_version"),
        "step": summary.get("step"),
        "run_id": summary.get("run_id"),
        "family": summary.get("family"),
        "relation_family": summary.get("relation_family"),
        "surface_plan_kind": summary.get("surface_plan_kind"),
        "limited_surface_candidate": summary.get("limited_surface_candidate"),
        "planned_insight_seed_count": summary.get("planned_insight_seed_count"),
        "max_insight_seed_count": summary.get("max_insight_seed_count"),
        "section_order": list(summary.get("section_order") or []),
        "must_include_roles": list(summary.get("must_include_roles") or []),
        "must_not_include_roles": list(summary.get("must_not_include_roles") or []),
        "gate_pass_required": summary.get("gate_pass_required"),
        "gate_passed": summary.get("gate_passed"),
        "decision_reason_codes": list(summary.get("decision_reason_codes") or []),
        "public_contract": _safe_mapping(summary.get("public_contract")),
        "body_free": _safe_mapping(summary.get("body_free")),
    }
    assert_structure_insight_p6_surface_role_plan_contract(safe_summary, allow_partial=True)
    return json.dumps(safe_summary, ensure_ascii=False, sort_keys=True)
