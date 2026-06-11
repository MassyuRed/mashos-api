# -*- coding: utf-8 -*-
from __future__ import annotations

"""P5-3 surface role plan for User Label Connection.

The plan maps a P5-2 eligible history line to section order and role
requirements.  It is role-driven and body-free: it does not create fixed
sentences, visible text, ``comment_text``, or runtime wiring.
"""

from collections.abc import Iterable, Mapping
import json
from typing import Any, Final

from emlis_ai_user_label_connection_p5_eligibility_matrix import (
    DECISION_BLOCKED as ELIGIBILITY_BLOCKED,
    DECISION_CONNECTABLE as ELIGIBILITY_CONNECTABLE,
    DECISION_META_ONLY as ELIGIBILITY_META_ONLY,
    DECISION_REVIEW_REQUIRED as ELIGIBILITY_REVIEW_REQUIRED,
    assert_user_label_connection_p5_eligibility_matrix_contract,
)
from emlis_ai_user_label_connection_types import (
    EDGE_FAMILY_CATEGORY_STATE_RECURRENCE,
    EDGE_FAMILY_LABEL_ROUTE_CURRENT_ALIGNMENT,
)


USER_LABEL_CONNECTION_P5_SURFACE_ROLE_PLAN_SCHEMA_VERSION: Final = (
    "cocolon.emlis.user_label_connection.p5_surface_role_plan.v1"
)
USER_LABEL_CONNECTION_P5_SURFACE_ROLE_PLAN_STEP: Final = (
    "P5-3_SurfaceRolePlan_EdgeFamilyMapping"
)
USER_LABEL_CONNECTION_P5_SURFACE_ROLE_PLAN_SOURCE: Final = (
    "Cocolon_EmlisAI_P5_UserLabelConnection_SurfaceRolePlan_EdgeFamilyMapping_20260611"
)

SURFACE_PLAN_KIND_LIMITED_HISTORY_LINE_OBSERVATION: Final = "limited_history_line_observation"
SURFACE_PLAN_KIND_META_ONLY: Final = "meta_only"
SURFACE_PLAN_KIND_BLOCKED: Final = "blocked"

CONNECTABLE_FAMILY_STRUCTURE_QUESTION: Final = "structure_question"
CONNECTABLE_FAMILY_LONG_MEANING_ARC: Final = "long_meaning_arc"
CONNECTABLE_FAMILY_SELF_UNDERSTANDING_FOLLOW: Final = "self_understanding_follow"
CONNECTABLE_FAMILY_REVIEW_REQUIRED: Final = "review_required"
CONNECTABLE_FAMILY_BLOCKED: Final = "blocked"

SECTION_CURRENT_OBSERVATION: Final = "current_observation"
SECTION_HISTORY_SUPPORT_LINE: Final = "history_support_line"
SECTION_NOT_PERSONALITY_BOUNDARY: Final = "not_personality_boundary"

ROLE_SCOPE_MARKER: Final = "scope_marker"
ROLE_CURRENT_INPUT_ANCHOR: Final = "current_input_anchor"
ROLE_HISTORY_LINE_MARKER: Final = "history_line_marker"
ROLE_SOFT_OBSERVATION: Final = "soft_observation"
ROLE_NOT_PERSONALITY_DISCLAIMER: Final = "not_personality_disclaimer"
ROLE_SELF_UNDERSTANDING_SUPPORT: Final = "self_understanding_support"
ROLE_CURRENT_OBSERVATION_FIRST: Final = "current_observation_first"
ROLE_HISTORY_AS_SUPPORT_LINE: Final = "history_as_support_line"
ROLE_EVIDENCE_COUNT_BOUNDARY: Final = "evidence_count_boundary"
ROLE_SAME_LABEL_OVERLAP: Final = "same_label_overlap"
ROLE_DIFFERENT_STATE_ROUTE: Final = "different_state_route"
ROLE_TIME_SCOPE_LIMITED: Final = "time_scope_limited"
ROLE_DO_NOT_GENERALIZE_MARKER: Final = "do_not_generalize_marker"
ROLE_NOT_CAUSE_MARKER: Final = "not_cause_marker"
ROLE_NOT_ADVICE_MARKER: Final = "not_advice_marker"

ROLE_ADVICE: Final = "advice"
ROLE_DIAGNOSIS: Final = "diagnosis"
ROLE_PERSONALITY_CLAIM: Final = "personality_claim"
ROLE_FUTURE_PREDICTION: Final = "future_prediction"
ROLE_ALWAYS_CLAIM: Final = "always_claim"
ROLE_SHOULD_STATEMENT: Final = "should_statement"
ROLE_CAUSE_CLAIM: Final = "cause_claim"
ROLE_OPPONENT_INTENT_CLAIM: Final = "opponent_intent_claim"
ROLE_SELF_BLAME_AMPLIFICATION: Final = "self_blame_amplification"

REASON_P5_ELIGIBILITY_NOT_CONNECTABLE: Final = "p5_eligibility_not_connectable"
REASON_FORBIDDEN_ROLE_DETECTED: Final = "forbidden_role_detected"
REASON_CURRENT_OBSERVATION_NOT_FIRST: Final = "current_observation_not_first"
REASON_HISTORY_NOT_SUPPORT_LINE: Final = "history_line_not_support_line"
REASON_FIXED_SENTENCE_TEMPLATE_DETECTED: Final = "fixed_sentence_template_detected"
REASON_RAW_TEXT_PAYLOAD_DETECTED: Final = "raw_text_payload_detected"
REASON_CONTRACT_MUTATION_DETECTED: Final = "contract_mutation_detected"

_CONNECTABLE_FAMILIES: Final[frozenset[str]] = frozenset(
    {
        CONNECTABLE_FAMILY_STRUCTURE_QUESTION,
        CONNECTABLE_FAMILY_LONG_MEANING_ARC,
        CONNECTABLE_FAMILY_SELF_UNDERSTANDING_FOLLOW,
    }
)
_BASE_REQUIRED_ROLES: Final[tuple[str, ...]] = (
    ROLE_SCOPE_MARKER,
    ROLE_CURRENT_INPUT_ANCHOR,
    ROLE_HISTORY_LINE_MARKER,
    ROLE_SOFT_OBSERVATION,
    ROLE_NOT_PERSONALITY_DISCLAIMER,
    ROLE_SELF_UNDERSTANDING_SUPPORT,
    ROLE_CURRENT_OBSERVATION_FIRST,
    ROLE_HISTORY_AS_SUPPORT_LINE,
    ROLE_EVIDENCE_COUNT_BOUNDARY,
    ROLE_TIME_SCOPE_LIMITED,
    ROLE_DO_NOT_GENERALIZE_MARKER,
    ROLE_NOT_CAUSE_MARKER,
    ROLE_NOT_ADVICE_MARKER,
)
_FORBIDDEN_ROLES: Final[tuple[str, ...]] = (
    ROLE_ADVICE,
    ROLE_DIAGNOSIS,
    ROLE_PERSONALITY_CLAIM,
    ROLE_FUTURE_PREDICTION,
    ROLE_ALWAYS_CLAIM,
    ROLE_SHOULD_STATEMENT,
    ROLE_CAUSE_CLAIM,
    ROLE_OPPONENT_INTENT_CLAIM,
    ROLE_SELF_BLAME_AMPLIFICATION,
)
_SECTION_ORDER: Final[tuple[str, ...]] = (
    SECTION_CURRENT_OBSERVATION,
    SECTION_HISTORY_SUPPORT_LINE,
    SECTION_NOT_PERSONALITY_BOUNDARY,
)
_FAMILY_ROLE_MAP: Final[dict[str, tuple[str, ...]]] = {
    CONNECTABLE_FAMILY_STRUCTURE_QUESTION: (
        ROLE_CURRENT_OBSERVATION_FIRST,
        ROLE_HISTORY_AS_SUPPORT_LINE,
        ROLE_DIFFERENT_STATE_ROUTE,
    ),
    CONNECTABLE_FAMILY_LONG_MEANING_ARC: (
        ROLE_HISTORY_AS_SUPPORT_LINE,
        ROLE_TIME_SCOPE_LIMITED,
        ROLE_EVIDENCE_COUNT_BOUNDARY,
    ),
    CONNECTABLE_FAMILY_SELF_UNDERSTANDING_FOLLOW: (
        ROLE_SELF_UNDERSTANDING_SUPPORT,
        ROLE_SAME_LABEL_OVERLAP,
        ROLE_DO_NOT_GENERALIZE_MARKER,
    ),
}
_EDGE_ROLE_MAP: Final[dict[str, tuple[str, ...]]] = {
    EDGE_FAMILY_CATEGORY_STATE_RECURRENCE: (
        ROLE_SAME_LABEL_OVERLAP,
        ROLE_HISTORY_AS_SUPPORT_LINE,
        ROLE_NOT_CAUSE_MARKER,
    ),
    EDGE_FAMILY_LABEL_ROUTE_CURRENT_ALIGNMENT: (
        ROLE_SAME_LABEL_OVERLAP,
        ROLE_CURRENT_OBSERVATION_FIRST,
        ROLE_NOT_ADVICE_MARKER,
    ),
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
        "fixed_sentence",
        "fixedSentence",
        "template_text",
        "templateText",
        "sentence_template",
        "sentenceTemplate",
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
        "db_schema_changed",
        "db_physical_name_changed",
        "rn_contract_changed",
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
        "existing_gate_relaxed",
        "raw_input_included",
        "raw_text_included",
        "comment_text_included",
        "comment_text_body_included",
        "candidate_body_included",
        "surface_body_included",
        "history_raw_text_included",
        "fixed_sentence_template_added",
        "input_specific_template_added",
        "diagnosis_allowed",
        "personality_claim_allowed",
        "cause_claim_allowed",
        "advice_allowed",
        "future_prediction_allowed",
        "always_claim_allowed",
        "should_statement_allowed",
        "opponent_intent_claim_allowed",
        "self_blame_amplification_allowed",
        "public_release_applied",
        "release_allowed",
        "p5_visible_surface_strengthened",
        "p5_runtime_change_applied",
        "p5_limited_visible_connection_applied",
        "external_ai_used",
        "local_llm_used",
    }
)


def _clean(value: Any) -> str:
    if value is None or isinstance(value, (Mapping, list, tuple, set)):
        return ""
    return str(value).strip()


def _safe_mapping(value: Any) -> dict[str, Any]:
    if isinstance(value, Mapping):
        return {str(key): item for key, item in value.items()}
    as_meta = getattr(value, "as_meta", None)
    if callable(as_meta):
        meta = as_meta()
        if isinstance(meta, Mapping):
            return {str(key): item for key, item in meta.items()}
    return {}


def _listify(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, Mapping):
        return [value]
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


def _roles_from_sources(*sources: Any) -> list[str]:
    roles: list[str] = []
    role_keys = ("requested_roles", "must_include_roles", "include_roles", "roles", "role_overrides")
    for source in sources:
        meta = _safe_mapping(source)
        if meta:
            for key in role_keys:
                roles.extend(_dedupe(meta.get(key)))
        else:
            roles.extend(_dedupe(source))
    return _dedupe(roles)


def _family_token(family: str, eligibility_decision: str) -> str:
    if family in _CONNECTABLE_FAMILIES:
        return family
    if eligibility_decision == ELIGIBILITY_REVIEW_REQUIRED:
        return CONNECTABLE_FAMILY_REVIEW_REQUIRED
    return CONNECTABLE_FAMILY_BLOCKED


def _surface_kind_for_eligibility(eligibility_decision: str) -> str:
    if eligibility_decision == ELIGIBILITY_CONNECTABLE:
        return SURFACE_PLAN_KIND_LIMITED_HISTORY_LINE_OBSERVATION
    if eligibility_decision in {ELIGIBILITY_META_ONLY, ELIGIBILITY_REVIEW_REQUIRED}:
        return SURFACE_PLAN_KIND_META_ONLY
    return SURFACE_PLAN_KIND_BLOCKED


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
    }


def _body_free_contract() -> dict[str, bool]:
    return {
        "raw_input_included": False,
        "raw_text_included": False,
        "comment_text_body_included": False,
        "candidate_body_included": False,
        "surface_body_included": False,
        "history_raw_text_included": False,
    }


def build_user_label_connection_p5_surface_role_plan(
    *,
    p5_eligibility_matrix: Mapping[str, Any] | None = None,
    requested_roles: Iterable[Any] | None = None,
    role_overrides: Mapping[str, Any] | None = None,
    surface_plan_meta: Mapping[str, Any] | None = None,
    run_id: str | None = None,
) -> dict[str, Any]:
    """Build a body-free P5-3 surface role plan."""

    eligibility = _safe_mapping(p5_eligibility_matrix)
    role_override_meta = _safe_mapping(role_overrides)
    surface = _safe_mapping(surface_plan_meta)
    if eligibility:
        assert_user_label_connection_p5_eligibility_matrix_contract(eligibility, allow_partial=True)

    sources = [eligibility, role_override_meta, surface]
    unsafe_payload = any(_contains_text_payload_key(source) for source in sources)
    contract_mutation = any(_flag_true(source) for source in sources)

    eligibility_decision = _clean(eligibility.get("decision")) or ELIGIBILITY_BLOCKED
    eligibility_connectable = eligibility.get("connectable") is True and eligibility_decision == ELIGIBILITY_CONNECTABLE
    source_family = _clean(eligibility.get("connectable_family"))
    edge_family = _clean(eligibility.get("edge_family"))
    connectable_family = _family_token(source_family, eligibility_decision)

    requested = _roles_from_sources(requested_roles, role_override_meta, surface)
    family_roles = _FAMILY_ROLE_MAP.get(source_family, ())
    edge_roles = _EDGE_ROLE_MAP.get(edge_family, ())
    must_include_roles = _dedupe([*_BASE_REQUIRED_ROLES, *family_roles, *edge_roles])
    must_not_include_roles = _dedupe(_FORBIDDEN_ROLES)
    forbidden_requested_roles = sorted(set(requested) & set(_FORBIDDEN_ROLES))

    section_order = _dedupe(_SECTION_ORDER)
    reasons: list[str] = []
    if unsafe_payload:
        reasons.append(REASON_RAW_TEXT_PAYLOAD_DETECTED)
    if contract_mutation:
        reasons.append(REASON_CONTRACT_MUTATION_DETECTED)
    if not eligibility_connectable:
        reasons.append(REASON_P5_ELIGIBILITY_NOT_CONNECTABLE)
        reasons.extend(f"p5_eligibility:{reason}" for reason in _dedupe(eligibility.get("rejection_reasons")))
    if forbidden_requested_roles:
        reasons.append(REASON_FORBIDDEN_ROLE_DETECTED)
        reasons.extend(f"forbidden_role:{role}" for role in forbidden_requested_roles)
    if not section_order or section_order[0] != SECTION_CURRENT_OBSERVATION:
        reasons.append(REASON_CURRENT_OBSERVATION_NOT_FIRST)
    if SECTION_HISTORY_SUPPORT_LINE not in section_order:
        reasons.append(REASON_HISTORY_NOT_SUPPORT_LINE)
    if surface.get("fixed_sentence_template_added") is True or role_override_meta.get("fixed_sentence_template_added") is True:
        reasons.append(REASON_FIXED_SENTENCE_TEMPLATE_DETECTED)
    reasons = _dedupe(reasons)

    surface_plan_kind = _surface_kind_for_eligibility(eligibility_decision)
    if unsafe_payload or contract_mutation or forbidden_requested_roles or REASON_FIXED_SENTENCE_TEMPLATE_DETECTED in reasons:
        surface_plan_kind = SURFACE_PLAN_KIND_BLOCKED
    role_plan_ready = surface_plan_kind == SURFACE_PLAN_KIND_LIMITED_HISTORY_LINE_OBSERVATION and not reasons

    summary = {
        "schema_version": USER_LABEL_CONNECTION_P5_SURFACE_ROLE_PLAN_SCHEMA_VERSION,
        "version": USER_LABEL_CONNECTION_P5_SURFACE_ROLE_PLAN_SCHEMA_VERSION,
        "step": USER_LABEL_CONNECTION_P5_SURFACE_ROLE_PLAN_STEP,
        "source": USER_LABEL_CONNECTION_P5_SURFACE_ROLE_PLAN_SOURCE,
        "run_id": run_id or "p5_surface_role_plan",
        "surface_plan_kind": surface_plan_kind,
        "role_plan_ready": role_plan_ready,
        "meta_only": surface_plan_kind == SURFACE_PLAN_KIND_META_ONLY,
        "blocked": surface_plan_kind == SURFACE_PLAN_KIND_BLOCKED,
        "review_required": eligibility_decision == ELIGIBILITY_REVIEW_REQUIRED,
        "rejection_reasons": reasons,
        "connectable_family": connectable_family,
        "source_connectable_family": source_family,
        "edge_family": edge_family,
        "must_include_roles": must_include_roles,
        "must_not_include_roles": must_not_include_roles,
        "section_order": section_order,
        "role_family_mapping": {
            "family": source_family,
            "roles": _dedupe(family_roles),
        },
        "edge_family_mapping": {
            "edge_family": edge_family,
            "roles": _dedupe(edge_roles),
        },
        "surface_shape": {
            "existing_visible_body_is_primary": True,
            "current_observation_first": True,
            "history_line_is_support": True,
            "scope_marker_required": True,
            "soft_marker_required": True,
            "not_personality_boundary_required": True,
        },
        "fixed_sentence_template_added": False,
        "comment_text_generated_by_this_layer": False,
        "visible_text_generated": False,
        "visible_surface_connected": False,
        "runtime_change_applied": False,
        "public_contract": _public_contract(),
        "body_free": _body_free_contract(),
    }
    assert_user_label_connection_p5_surface_role_plan_contract(summary)
    return summary


def user_label_connection_p5_surface_role_plan_public_summary(value: Mapping[str, Any] | None) -> dict[str, Any]:
    meta = _safe_mapping(value)
    summary = {
        "schema_version": USER_LABEL_CONNECTION_P5_SURFACE_ROLE_PLAN_SCHEMA_VERSION,
        "step": USER_LABEL_CONNECTION_P5_SURFACE_ROLE_PLAN_STEP,
        "surface_plan_kind": _clean(meta.get("surface_plan_kind")) or SURFACE_PLAN_KIND_BLOCKED,
        "role_plan_ready": meta.get("role_plan_ready") is True,
        "meta_only": meta.get("meta_only") is True,
        "blocked": meta.get("blocked") is True,
        "review_required": meta.get("review_required") is True,
        "rejection_reasons": _dedupe(meta.get("rejection_reasons")),
        "connectable_family": _clean(meta.get("connectable_family")),
        "edge_family": _clean(meta.get("edge_family")),
        "must_include_roles": _dedupe(meta.get("must_include_roles")),
        "must_not_include_roles": _dedupe(meta.get("must_not_include_roles")),
        "section_order": _dedupe(meta.get("section_order")),
        "public_meta_summary_only": True,
        "public_response_key_added": False,
        "response_shape_changed": False,
        "raw_text_included": False,
        "comment_text_body_included": False,
        "history_raw_text_included": False,
    }
    assert_user_label_connection_p5_surface_role_plan_contract(summary, allow_partial=True)
    return summary


def assert_user_label_connection_p5_surface_role_plan_contract(value: Any, *, allow_partial: bool = False) -> None:
    if _contains_text_payload_key(value):
        raise ValueError("P5 surface role plan must not include raw text/comment/surface payload keys")
    if _flag_true(value):
        raise ValueError("P5 surface role plan contains a forbidden true flag")
    json.dumps(value, ensure_ascii=False, sort_keys=True)
    if allow_partial:
        return
    if not isinstance(value, Mapping):
        raise ValueError("P5 surface role plan must be a mapping")
    if value.get("schema_version") != USER_LABEL_CONNECTION_P5_SURFACE_ROLE_PLAN_SCHEMA_VERSION:
        raise ValueError("unexpected P5 surface role plan schema_version")
    if value.get("step") != USER_LABEL_CONNECTION_P5_SURFACE_ROLE_PLAN_STEP:
        raise ValueError("unexpected P5 surface role plan step")
    if value.get("surface_plan_kind") not in {
        SURFACE_PLAN_KIND_LIMITED_HISTORY_LINE_OBSERVATION,
        SURFACE_PLAN_KIND_META_ONLY,
        SURFACE_PLAN_KIND_BLOCKED,
    }:
        raise ValueError("unexpected P5 surface_plan_kind")
    if value.get("surface_plan_kind") == SURFACE_PLAN_KIND_LIMITED_HISTORY_LINE_OBSERVATION:
        if value.get("role_plan_ready") is not True:
            raise ValueError("limited P5 surface role plan must be ready")
        section_order = _dedupe(value.get("section_order"))
        if not section_order or section_order[0] != SECTION_CURRENT_OBSERVATION:
            raise ValueError("P5 surface role plan must put current_observation first")
        if SECTION_HISTORY_SUPPORT_LINE not in section_order:
            raise ValueError("P5 surface role plan must keep history as support line")
    included = set(_dedupe(value.get("must_include_roles")))
    forbidden = set(_dedupe(value.get("must_not_include_roles")))
    if included & set(_FORBIDDEN_ROLES):
        raise ValueError("P5 surface role plan includes a forbidden role")
    if not set(_FORBIDDEN_ROLES).issubset(forbidden):
        raise ValueError("P5 surface role plan must preserve forbidden roles")
    public_contract = _safe_mapping(value.get("public_contract"))
    body_free = _safe_mapping(value.get("body_free"))
    for key in ("rn_visible_contract_changed", "public_response_key_added", "response_shape_changed", "db_schema_changed", "fixed_sentence_template_added"):
        if public_contract.get(key) is not False:
            raise ValueError(f"P5 surface role public_contract.{key} must be false")
    for key in ("raw_text_included", "comment_text_body_included", "candidate_body_included", "surface_body_included", "history_raw_text_included"):
        if body_free.get(key) is not False:
            raise ValueError(f"P5 surface role body_free.{key} must be false")


__all__ = [
    "USER_LABEL_CONNECTION_P5_SURFACE_ROLE_PLAN_SCHEMA_VERSION",
    "USER_LABEL_CONNECTION_P5_SURFACE_ROLE_PLAN_STEP",
    "USER_LABEL_CONNECTION_P5_SURFACE_ROLE_PLAN_SOURCE",
    "SURFACE_PLAN_KIND_LIMITED_HISTORY_LINE_OBSERVATION",
    "SURFACE_PLAN_KIND_META_ONLY",
    "SURFACE_PLAN_KIND_BLOCKED",
    "CONNECTABLE_FAMILY_STRUCTURE_QUESTION",
    "CONNECTABLE_FAMILY_LONG_MEANING_ARC",
    "CONNECTABLE_FAMILY_SELF_UNDERSTANDING_FOLLOW",
    "CONNECTABLE_FAMILY_REVIEW_REQUIRED",
    "CONNECTABLE_FAMILY_BLOCKED",
    "build_user_label_connection_p5_surface_role_plan",
    "user_label_connection_p5_surface_role_plan_public_summary",
    "assert_user_label_connection_p5_surface_role_plan_contract",
]
