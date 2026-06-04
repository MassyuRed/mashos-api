# -*- coding: utf-8 -*-
from __future__ import annotations

"""Phase 6 Surface Plan for EmlisAI User Label Connection Observation v1.

This module converts a passed User Label Connection Gate decision into a
backend-internal, text-free surface plan.  It deliberately does not generate
``comment_text``, does not add public response keys, does not connect to RN/API,
and does not emit a fixed visible sentence.  Later phases may decide how to hand
this role plan to the existing composer/surface realizer.
"""

from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
import json
from typing import Any, Final

from emlis_ai_user_label_connection_candidate import (
    MECHANISM_FAMILY_SAME_ENVIRONMENT_DIFFERENT_STATE_ROUTE,
    MECHANISM_FAMILY_SAME_LABEL_LINE_CURRENT_ALIGNMENT,
    MECHANISM_FAMILY_SAME_STATE_DIFFERENT_ENVIRONMENT_ROUTE,
    MECHANISM_FAMILY_UNRESOLVED_WEIGHT_LINE,
    MECHANISM_FAMILY_VALUE_ANCHOR_LINE,
    USER_LABEL_CONNECTION_CANDIDATE_SCHEMA_VERSION,
)
from emlis_ai_user_label_connection_gate import (
    GATE_ACTION_ALLOW_LIMITED_SURFACE_PLAN,
    GATE_ACTION_BLOCK_SURFACE_PLAN,
    GATE_ACTION_META_ONLY,
    GATE_ACTION_NO_CANDIDATE,
    USER_LABEL_CONNECTION_GATE_SCHEMA_VERSION,
    build_user_label_connection_gate_decision,
)

USER_LABEL_CONNECTION_SURFACE_PLAN_SCHEMA_VERSION: Final = "cocolon.emlis.user_label_connection_surface_plan.v1"
USER_LABEL_CONNECTION_SURFACE_PLAN_STEP: Final = "UserLabelConnection_SurfacePlan_v1"

SURFACE_PLAN_KIND_LIMITED_HISTORY_LINE_OBSERVATION: Final = "limited_history_line_observation"
SURFACE_PLAN_KIND_META_ONLY: Final = "meta_only"
SURFACE_PLAN_KIND_BLOCKED: Final = "blocked"

CONNECTABLE_FAMILY_STRUCTURE_QUESTION: Final = "structure_question"
CONNECTABLE_FAMILY_LONG_MEANING_ARC: Final = "long_meaning_arc"
CONNECTABLE_FAMILY_SELF_UNDERSTANDING_FOLLOW: Final = "self_understanding_follow"

SECTION_TARGET_OBSERVATION: Final = "observation"
SECTION_TARGET_RECEPTION: Final = "reception"

ROLE_SCOPE_MARKER: Final = "scope_marker"
ROLE_CURRENT_INPUT_ANCHOR: Final = "current_input_anchor"
ROLE_HISTORY_LINE_MARKER: Final = "history_line_marker"
ROLE_SOFT_OBSERVATION: Final = "soft_observation"
ROLE_NOT_PERSONALITY_DISCLAIMER: Final = "not_personality_disclaimer"
ROLE_SELF_UNDERSTANDING_SUPPORT: Final = "self_understanding_support"

ROLE_ADVICE: Final = "advice"
ROLE_DIAGNOSIS: Final = "diagnosis"
ROLE_PERSONALITY_CLAIM: Final = "personality_claim"
ROLE_FUTURE_PREDICTION: Final = "future_prediction"
ROLE_ALWAYS_CLAIM: Final = "always_claim"
ROLE_SHOULD_STATEMENT: Final = "should_statement"

REJECTION_GATE_NOT_PASSED: Final = "user_label_connection_gate_not_passed"
REJECTION_CONNECTABLE_FAMILY_SUPPRESSED: Final = "connectable_family_suppressed"
REJECTION_CONNECTABLE_FAMILY_UNSUPPORTED: Final = "connectable_family_unsupported"
REJECTION_CANDIDATE_MISSING: Final = "surface_plan_candidate_missing"
REJECTION_RAW_TEXT_PAYLOAD_DETECTED: Final = "surface_plan_raw_text_payload_detected"
REJECTION_FIXED_SENTENCE_TEMPLATE_DETECTED: Final = "fixed_sentence_template_detected"

USER_LABEL_CONNECTION_VISIBLE_SURFACE_SCHEMA_VERSION: Final = "cocolon.emlis.user_label_connection.visible_surface_connection.v1"
USER_LABEL_CONNECTION_VISIBLE_SURFACE_STEP: Final = "UserLabelConnection_LimitedVisibleSurfaceConnection_v1"
USER_LABEL_CONNECTION_VISIBLE_SURFACE_PHASE: Final = "Phase8_LimitedVisibleSurfaceConnection"
USER_LABEL_CONNECTION_VISIBLE_SURFACE_META_KEY: Final = "user_label_connection_visible_surface"

REJECTION_VISIBLE_EXISTING_COMMENT_TEXT_MISSING: Final = "visible_existing_comment_text_missing"
REJECTION_VISIBLE_SURFACE_PLAN_NOT_READY: Final = "visible_surface_plan_not_ready"
REJECTION_VISIBLE_EXISTING_GATE_REPORT_MISSING: Final = "visible_existing_gate_report_missing"
REJECTION_VISIBLE_EXISTING_GATE_BLOCKED: Final = "visible_existing_gate_blocked"
REJECTION_VISIBLE_SCOPE_MARKER_MISSING: Final = "visible_scope_marker_missing"
REJECTION_VISIBLE_SOFT_MARKER_MISSING: Final = "visible_soft_marker_missing"
REJECTION_VISIBLE_FORBIDDEN_CLAIM_DETECTED: Final = "visible_forbidden_claim_detected"
REJECTION_VISIBLE_ALREADY_CONNECTED: Final = "visible_history_connection_already_connected"
REJECTION_VISIBLE_SAFETY_CONTEXT_BLOCKED: Final = "visible_safety_context_blocked"

_ALLOWED_SURFACE_PLAN_KINDS: Final = frozenset(
    {
        SURFACE_PLAN_KIND_LIMITED_HISTORY_LINE_OBSERVATION,
        SURFACE_PLAN_KIND_META_ONLY,
        SURFACE_PLAN_KIND_BLOCKED,
    }
)
_ALLOWED_CONNECTABLE_FAMILIES: Final = frozenset(
    {
        "",
        CONNECTABLE_FAMILY_STRUCTURE_QUESTION,
        CONNECTABLE_FAMILY_LONG_MEANING_ARC,
        CONNECTABLE_FAMILY_SELF_UNDERSTANDING_FOLLOW,
    }
)
_LIMITED_CONNECTABLE_FAMILIES: Final = frozenset(
    {
        CONNECTABLE_FAMILY_STRUCTURE_QUESTION,
        CONNECTABLE_FAMILY_LONG_MEANING_ARC,
        CONNECTABLE_FAMILY_SELF_UNDERSTANDING_FOLLOW,
    }
)
_SUPPRESSED_FAMILIES: Final = frozenset(
    {
        "daily_unpleasant",
        "daily_positive",
        "positive_only",
        "low_information",
        "low_information_short",
        "safety_triage_required",
        "safety_required",
        "safety_adjacent",
    }
)
_REQUIRED_SURFACE_ROLES: Final = (
    ROLE_SCOPE_MARKER,
    ROLE_CURRENT_INPUT_ANCHOR,
    ROLE_HISTORY_LINE_MARKER,
    ROLE_SOFT_OBSERVATION,
    ROLE_NOT_PERSONALITY_DISCLAIMER,
    ROLE_SELF_UNDERSTANDING_SUPPORT,
)
_FORBIDDEN_SURFACE_ROLES: Final = (
    ROLE_ADVICE,
    ROLE_DIAGNOSIS,
    ROLE_PERSONALITY_CLAIM,
    ROLE_FUTURE_PREDICTION,
    ROLE_ALWAYS_CLAIM,
    ROLE_SHOULD_STATEMENT,
)
CONNECTABLE_FAMILIES: Final = _LIMITED_CONNECTABLE_FAMILIES
SUPPRESSED_CONTEXT_FAMILIES: Final = _SUPPRESSED_FAMILIES
MUST_INCLUDE_ROLES: Final = _REQUIRED_SURFACE_ROLES
MUST_NOT_INCLUDE_ROLES: Final = _FORBIDDEN_SURFACE_ROLES
REJECTION_SUPPRESSED_CONTEXT_FAMILY: Final = REJECTION_CONNECTABLE_FAMILY_SUPPRESSED
REJECTION_CONNECTABLE_FAMILY_NOT_ALLOWED: Final = REJECTION_CONNECTABLE_FAMILY_UNSUPPORTED


# Public aliases keep the Phase 6 role contract visible to tests and later phases.
REQUIRED_INCLUDE_ROLES: Final = _REQUIRED_SURFACE_ROLES
REQUIRED_MUST_NOT_ROLES: Final = _FORBIDDEN_SURFACE_ROLES
REJECTION_SUPPRESSED_REPLY_FAMILY: Final = REJECTION_CONNECTABLE_FAMILY_SUPPRESSED
_ALLOWED_SECTION_TARGETS: Final = frozenset({SECTION_TARGET_OBSERVATION, SECTION_TARGET_RECEPTION})

_MODE_TO_FAMILY: Final = {
    "structure_question": CONNECTABLE_FAMILY_STRUCTURE_QUESTION,
    "structure_question_observation": CONNECTABLE_FAMILY_STRUCTURE_QUESTION,
    "long_meaning_arc": CONNECTABLE_FAMILY_LONG_MEANING_ARC,
    "self_understanding_follow": CONNECTABLE_FAMILY_SELF_UNDERSTANDING_FOLLOW,
    "self_understanding": CONNECTABLE_FAMILY_SELF_UNDERSTANDING_FOLLOW,
}
_MECHANISM_TO_FAMILY: Final = {
    MECHANISM_FAMILY_SAME_LABEL_LINE_CURRENT_ALIGNMENT: CONNECTABLE_FAMILY_SELF_UNDERSTANDING_FOLLOW,
    MECHANISM_FAMILY_SAME_ENVIRONMENT_DIFFERENT_STATE_ROUTE: CONNECTABLE_FAMILY_STRUCTURE_QUESTION,
    MECHANISM_FAMILY_SAME_STATE_DIFFERENT_ENVIRONMENT_ROUTE: CONNECTABLE_FAMILY_STRUCTURE_QUESTION,
    MECHANISM_FAMILY_UNRESOLVED_WEIGHT_LINE: CONNECTABLE_FAMILY_SELF_UNDERSTANDING_FOLLOW,
    MECHANISM_FAMILY_VALUE_ANCHOR_LINE: CONNECTABLE_FAMILY_LONG_MEANING_ARC,
}

# Keys that would carry visible/raw body payloads if present.  The plan may keep
# boolean ``*_included``/``*_generated``/``*_added`` contract flags, but it must
# never carry the body keys themselves.
_TEXT_PAYLOAD_KEYS: Final = frozenset(
    {
        "raw_input",
        "rawInput",
        "raw_text",
        "rawText",
        "raw_user_text",
        "rawUserText",
        "source_text",
        "sourceText",
        "input",
        "input_text",
        "inputText",
        "user_input",
        "userInput",
        "current_input",
        "currentInput",
        "history_input",
        "historyInput",
        "memo",
        "memo_text",
        "memoText",
        "memo_action",
        "memoAction",
        "memo_action_text",
        "memoActionText",
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
        "realized_text",
        "realizedText",
        "display_text",
        "displayText",
        "observation_text",
        "reception_text",
        "internal_question_body",
        "private_user_dictionary_text",
        "body",
        "text",
    }
)
_FORBIDDEN_TRUE_FLAGS: Final = frozenset(
    {
        "api_route_changed",
        "request_key_changed",
        "response_shape_changed",
        "public_response_key_added",
        "db_physical_name_changed",
        "rn_visible_contract_changed",
        "rn_visible_title_changed",
        "raw_input_included",
        "raw_text_included",
        "history_raw_text_included",
        "raw_fact_text_included",
        "comment_text_body_included",
        "candidate_body_included",
        "surface_body_included",
        "surface_text_body_included",
        "internal_question_body_included",
        "private_user_dictionary_text_included",
        "record_ids_included",
        "fixed_sentence_template_added",
        "comment_text_generated",
        "comment_text_generated_by_this_layer",
        "diagnosis_allowed",
        "personality_claim_allowed",
        "cause_claim_allowed",
        "advice_allowed",
        "future_prediction_allowed",
        "always_claim_allowed",
        "should_statement_allowed",
    }
)


def _clean(value: Any) -> str:
    if value is None or isinstance(value, (Mapping, list, tuple, set)):
        return ""
    return str(value).replace("\u3000", " ").strip()


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
        for key, item in value.items():
            normalized = str(key)
            if normalized in _TEXT_PAYLOAD_KEYS:
                return True
            if _contains_text_payload_key(item):
                return True
    elif isinstance(value, (list, tuple, set)):
        return any(_contains_text_payload_key(item) for item in value)
    return False


def _flag_true(value: Any, names: Iterable[str]) -> bool:
    wanted = {str(name) for name in names}
    if isinstance(value, Mapping):
        for key, item in value.items():
            if str(key) in wanted and item is True:
                return True
            if _flag_true(item, wanted):
                return True
    elif isinstance(value, (list, tuple, set)):
        return any(_flag_true(item, wanted) for item in value)
    return False


def _int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def _surface_shape_for_limited_plan() -> dict[str, str]:
    return {
        "opening_reception": "optional",
        "current_input_observation": "required",
        "history_connection_observation": "required_when_history_surface",
        "meaning_support": "required",
        "closing_partner_line": "optional",
    }


def _surface_shape_for_blocked_plan() -> dict[str, str]:
    return {
        "opening_reception": "forbidden",
        "current_input_observation": "forbidden",
        "history_connection_observation": "forbidden",
        "meaning_support": "forbidden",
        "closing_partner_line": "forbidden",
    }


def _plan_roles_for_family(family: str) -> list[str]:
    # Keep the Phase 6 contract stable: every limited history-line plan carries
    # all required roles.  Later surface realization may decide how to map roles
    # to actual phrasing.
    if family not in _LIMITED_CONNECTABLE_FAMILIES:
        return []
    return list(_REQUIRED_SURFACE_ROLES)


def _section_targets_for_family(family: str, explicit_targets: Sequence[Any] | None = None) -> list[str]:
    explicit = [target for target in _dedupe(explicit_targets) if target in _ALLOWED_SECTION_TARGETS]
    if explicit:
        return explicit
    if family in _LIMITED_CONNECTABLE_FAMILIES:
        return [SECTION_TARGET_OBSERVATION, SECTION_TARGET_RECEPTION]
    return []


def _candidate_meta_from(candidate: Any = None, *, candidate_meta: Mapping[str, Any] | None = None) -> dict[str, Any]:
    meta = _safe_mapping(candidate)
    meta.update(_safe_mapping(candidate_meta))
    return meta


def _gate_meta_from(gate: Any = None, *, gate_meta: Mapping[str, Any] | None = None) -> dict[str, Any]:
    meta = _safe_mapping(gate)
    meta.update(_safe_mapping(gate_meta))
    return meta


def _family_from_observation_meta(observation_reply_meta: Mapping[str, Any]) -> str:
    for key in ("connectable_family", "coverage_group", "fixture_family", "product_readfeel_fixture_family"):
        value = _clean(observation_reply_meta.get(key)).lower()
        if value in _SUPPRESSED_FAMILIES:
            return value
        if value in _LIMITED_CONNECTABLE_FAMILIES:
            return value
    for key in ("two_stage_reception_mode_id", "reception_mode_id", "two_stage_mode_context_reception_mode_id", "mode_id"):
        value = _clean(observation_reply_meta.get(key)).lower()
        if value in _SUPPRESSED_FAMILIES:
            return value
        if value in _MODE_TO_FAMILY:
            return _MODE_TO_FAMILY[value]
    return ""


def _resolve_connectable_family(
    *,
    candidate_meta: Mapping[str, Any],
    gate_meta: Mapping[str, Any],
    observation_reply_meta: Mapping[str, Any],
    connectable_family: Any = None,
    mode_id: Any = None,
    coverage_group: Any = None,
) -> str:
    for value in (connectable_family, coverage_group):
        text = _clean(value).lower()
        if text:
            return text
    mode = _clean(mode_id).lower()
    if mode:
        return _MODE_TO_FAMILY.get(mode, mode)
    meta_family = _family_from_observation_meta(observation_reply_meta)
    if meta_family:
        return meta_family
    for source in (gate_meta, candidate_meta):
        text = _clean(source.get("connectable_family")).lower()
        if text:
            return text
    mechanism_family = _clean(candidate_meta.get("mechanism_family") or gate_meta.get("mechanism_family"))
    return _MECHANISM_TO_FAMILY.get(mechanism_family, "")


def _evidence_summary(gate_meta: Mapping[str, Any], candidate_meta: Mapping[str, Any]) -> dict[str, Any]:
    gate_evidence = _safe_mapping(gate_meta.get("evidence_contract"))
    candidate_evidence = _safe_mapping(candidate_meta.get("evidence"))
    return {
        "evidence_record_count": _int(gate_evidence.get("evidence_record_count", candidate_evidence.get("evidence_record_count"))),
        "minimum_evidence_record_count": _int(gate_evidence.get("minimum_evidence_record_count"), 2) or 2,
        "current_record_included": bool(gate_evidence.get("current_record_included", candidate_evidence.get("current_record_included") is True)),
        "history_record_count": _int(gate_evidence.get("history_record_count", candidate_evidence.get("history_record_count"))),
        "period_tendency_from_single_record_allowed": False,
        "source_field_ids": _dedupe(candidate_evidence.get("source_field_ids") or []),
    }


def _public_contract() -> dict[str, bool]:
    return {
        "api_route_changed": False,
        "request_key_changed": False,
        "response_shape_changed": False,
        "public_response_key_added": False,
        "db_physical_name_changed": False,
        "rn_visible_contract_changed": False,
        "rn_visible_title_changed": False,
        "comment_text_body_included": False,
        "raw_input_included": False,
        "raw_text_included": False,
    }


def _base_meta() -> dict[str, Any]:
    return {
        "schema_version": USER_LABEL_CONNECTION_SURFACE_PLAN_SCHEMA_VERSION,
        "step": USER_LABEL_CONNECTION_SURFACE_PLAN_STEP,
        "fixed_sentence_template_added": False,
        "comment_text_generated_by_this_layer": False,
        "comment_text_generated": False,
        "public_response_key_added": False,
        "api_route_changed": False,
        "request_key_changed": False,
        "response_shape_changed": False,
        "db_physical_name_changed": False,
        "rn_visible_contract_changed": False,
        "rn_visible_title_changed": False,
        "raw_input_included": False,
        "raw_text_included": False,
        "history_raw_text_included": False,
        "raw_fact_text_included": False,
        "comment_text_body_included": False,
        "candidate_body_included": False,
        "surface_body_included": False,
        "surface_text_body_included": False,
        "internal_question_body_included": False,
        "private_user_dictionary_text_included": False,
        "record_ids_included": False,
        "diagnosis_allowed": False,
        "personality_claim_allowed": False,
        "cause_claim_allowed": False,
        "advice_allowed": False,
        "future_prediction_allowed": False,
        "always_claim_allowed": False,
        "should_statement_allowed": False,
        "surface_plan_generated_by_phase6": True,
        "comment_text_visible_connection_deferred": True,
        "public_release_applied": False,
    }


def _blocked_plan(
    *,
    gate_meta: Mapping[str, Any],
    candidate_meta: Mapping[str, Any],
    family: str,
    reasons: Sequence[Any],
    plan_kind: str = SURFACE_PLAN_KIND_BLOCKED,
) -> dict[str, Any]:
    candidate_id = _clean(candidate_meta.get("candidate_id") or gate_meta.get("candidate_id"))
    meta = {
        **_base_meta(),
        "candidate_id": candidate_id,
        "candidate_schema_version": _clean(candidate_meta.get("schema_version")) or _clean(gate_meta.get("candidate_schema_version")),
        "gate_schema_version": _clean(gate_meta.get("schema_version")),
        "gate_action": _clean(gate_meta.get("action")),
        "gate_passed": bool(gate_meta.get("passed") is True),
        "gate_blocked": bool(gate_meta.get("blocked") is True),
        "surface_plan_kind": plan_kind,
        "connectable_family": "" if family in _SUPPRESSED_FAMILIES or family not in _LIMITED_CONNECTABLE_FAMILIES else family,
        "section_targets": [],
        "must_include_roles": [],
        "must_not_include_roles": list(_FORBIDDEN_SURFACE_ROLES),
        "surface_shape": _surface_shape_for_blocked_plan(),
        "surface_permission": {
            "may_surface_now": False,
            "may_surface_after_user_label_connection_gate": False,
            "must_use_soft_expression": True,
            "must_use_scope_marker": True,
            "must_not_surface_as_fact": True,
            "must_not_surface_as_personality": True,
            "must_not_surface_as_diagnosis": True,
            "must_not_surface_as_cause": True,
            "must_not_surface_as_advice": True,
        },
        "evidence_contract": _evidence_summary(gate_meta, candidate_meta),
        "public_contract": _public_contract(),
        "gate_rejection_reasons": _dedupe(gate_meta.get("rejection_reasons") or []),
        "surface_plan_rejection_reasons": _dedupe(reasons),
        "history_connection_surface_plan_allowed": False,
        "history_connection_surface_connected": False,
        "limited_history_line_observation_ready": False,
        "history_line_surface_plan_ready": False,
        "history_line_surface_connected": False,
        "visible_surface_connected": False,
        "runtime_surface_connected": False,
        "comment_text_connected": False,
        "visible_text_generated": False,
    }
    assert_user_label_connection_surface_plan_meta_contract(meta)
    return meta


def build_user_label_connection_surface_plan(
    gate: Any = None,
    *,
    gate_meta: Mapping[str, Any] | None = None,
    candidate: Any = None,
    candidate_meta: Mapping[str, Any] | None = None,
    material: Any = None,
    connectable_family: Any = None,
    mode_id: Any = None,
    coverage_group: Any = None,
    section_targets: Sequence[Any] | None = None,
    observation_reply_meta: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    """Build a Phase 6 surface plan from an already evaluated Gate decision.

    The returned object is a structural plan only.  It intentionally contains no
    visible sentence, no raw memo/action text, no comment body, and no public API
    shape change.
    """

    resolved_candidate_meta = _candidate_meta_from(candidate, candidate_meta=candidate_meta)
    resolved_gate_meta = _gate_meta_from(gate, gate_meta=gate_meta)
    observation_meta = _safe_mapping(observation_reply_meta)

    if _contains_text_payload_key(resolved_candidate_meta) or _contains_text_payload_key(resolved_gate_meta) or _contains_text_payload_key(observation_meta):
        return _blocked_plan(
            gate_meta=resolved_gate_meta,
            candidate_meta=resolved_candidate_meta,
            family="",
            reasons=[REJECTION_RAW_TEXT_PAYLOAD_DETECTED],
        )
    if _flag_true(resolved_candidate_meta, _FORBIDDEN_TRUE_FLAGS) or _flag_true(resolved_gate_meta, _FORBIDDEN_TRUE_FLAGS) or _flag_true(observation_meta, _FORBIDDEN_TRUE_FLAGS):
        return _blocked_plan(
            gate_meta=resolved_gate_meta,
            candidate_meta=resolved_candidate_meta,
            family="",
            reasons=[REJECTION_RAW_TEXT_PAYLOAD_DETECTED],
        )

    if not resolved_gate_meta and material is not None:
        try:
            resolved_gate_meta = build_user_label_connection_gate_decision(
                resolved_candidate_meta or None,
                material=material,
                observation_reply_meta=observation_meta,
            )
        except Exception:
            resolved_gate_meta = {}

    family = _resolve_connectable_family(
        candidate_meta=resolved_candidate_meta,
        gate_meta=resolved_gate_meta,
        observation_reply_meta=observation_meta,
        connectable_family=connectable_family,
        mode_id=mode_id,
        coverage_group=coverage_group,
    )

    gate_action = _clean(resolved_gate_meta.get("action"))
    gate_passed = bool(
        resolved_gate_meta.get("passed") is True
        and gate_action == GATE_ACTION_ALLOW_LIMITED_SURFACE_PLAN
        and resolved_gate_meta.get("allow_limited_surface_plan") is not False
    )
    if gate_action in {GATE_ACTION_META_ONLY, GATE_ACTION_NO_CANDIDATE}:
        return _blocked_plan(
            gate_meta=resolved_gate_meta,
            candidate_meta=resolved_candidate_meta,
            family=family,
            reasons=[REJECTION_GATE_NOT_PASSED],
            plan_kind=SURFACE_PLAN_KIND_META_ONLY,
        )
    if not gate_passed:
        reasons = _dedupe(resolved_gate_meta.get("rejection_reasons") or []) or [REJECTION_GATE_NOT_PASSED]
        return _blocked_plan(
            gate_meta=resolved_gate_meta,
            candidate_meta=resolved_candidate_meta,
            family=family,
            reasons=reasons,
            plan_kind=SURFACE_PLAN_KIND_BLOCKED,
        )
    if not resolved_candidate_meta and not _clean(resolved_gate_meta.get("candidate_id")):
        return _blocked_plan(
            gate_meta=resolved_gate_meta,
            candidate_meta=resolved_candidate_meta,
            family=family,
            reasons=[REJECTION_CANDIDATE_MISSING],
            plan_kind=SURFACE_PLAN_KIND_BLOCKED,
        )
    if family in _SUPPRESSED_FAMILIES:
        return _blocked_plan(
            gate_meta=resolved_gate_meta,
            candidate_meta=resolved_candidate_meta,
            family=family,
            reasons=[REJECTION_CONNECTABLE_FAMILY_SUPPRESSED],
            plan_kind=SURFACE_PLAN_KIND_BLOCKED,
        )
    if family not in _LIMITED_CONNECTABLE_FAMILIES:
        return _blocked_plan(
            gate_meta=resolved_gate_meta,
            candidate_meta=resolved_candidate_meta,
            family=family,
            reasons=[REJECTION_CONNECTABLE_FAMILY_UNSUPPORTED],
            plan_kind=SURFACE_PLAN_KIND_BLOCKED,
        )

    candidate_id = _clean(resolved_candidate_meta.get("candidate_id") or resolved_gate_meta.get("candidate_id"))
    meta = {
        **_base_meta(),
        "candidate_id": candidate_id,
        "candidate_schema_version": _clean(resolved_candidate_meta.get("schema_version")) or _clean(resolved_gate_meta.get("candidate_schema_version")) or USER_LABEL_CONNECTION_CANDIDATE_SCHEMA_VERSION,
        "gate_schema_version": _clean(resolved_gate_meta.get("schema_version")) or USER_LABEL_CONNECTION_GATE_SCHEMA_VERSION,
        "gate_action": gate_action,
        "gate_passed": True,
        "gate_blocked": False,
        "surface_plan_kind": SURFACE_PLAN_KIND_LIMITED_HISTORY_LINE_OBSERVATION,
        "connectable_family": family,
        "section_targets": _section_targets_for_family(family, section_targets),
        "must_include_roles": _plan_roles_for_family(family),
        "must_not_include_roles": list(_FORBIDDEN_SURFACE_ROLES),
        "surface_shape": _surface_shape_for_limited_plan(),
        "surface_permission": {
            "may_surface_now": False,
            "may_surface_after_user_label_connection_gate": True,
            "must_use_soft_expression": True,
            "must_use_scope_marker": True,
            "must_not_surface_as_fact": True,
            "must_not_surface_as_personality": True,
            "must_not_surface_as_diagnosis": True,
            "must_not_surface_as_cause": True,
            "must_not_surface_as_advice": True,
        },
        "evidence_contract": _evidence_summary(resolved_gate_meta, resolved_candidate_meta),
        "public_contract": _public_contract(),
        "gate_rejection_reasons": [],
        "surface_plan_rejection_reasons": [],
        "history_connection_surface_plan_allowed": True,
        "history_connection_surface_connected": False,
        "limited_history_line_observation_ready": True,
        "history_line_surface_plan_ready": True,
        "history_line_surface_connected": False,
        "visible_surface_connected": False,
        "runtime_surface_connected": False,
        "comment_text_connected": False,
        "visible_text_generated": False,
    }
    assert_user_label_connection_surface_plan_meta_contract(meta)
    return meta


def build_user_label_connection_surface_plan_meta(*args: Any, **kwargs: Any) -> dict[str, Any]:
    return build_user_label_connection_surface_plan(*args, **kwargs)


def user_label_connection_surface_plan_public_summary(value: Mapping[str, Any] | None) -> dict[str, Any]:
    source = _safe_mapping(value)
    if not source:
        return {}
    if _contains_text_payload_key(source) or _flag_true(source, _FORBIDDEN_TRUE_FLAGS):
        return {
            "evaluated": True,
            "surface_plan_kind": SURFACE_PLAN_KIND_BLOCKED,
            "blocked": True,
            "rejection_reasons": ["user_label_connection_surface_plan_public_meta_unsafe"],
            "public_meta_summary_only": True,
            "raw_text_included": False,
            "comment_text_body_included": False,
            "public_response_key_added": False,
        }
    summary: dict[str, Any] = {
        "public_meta_summary_only": True,
        "schema_version": _clean(source.get("schema_version")),
        "surface_plan_kind": _clean(source.get("surface_plan_kind")),
        "connectable_family": _clean(source.get("connectable_family")),
        "history_connection_surface_plan_allowed": bool(source.get("history_connection_surface_plan_allowed") is True),
        "limited_history_line_observation_ready": bool(source.get("limited_history_line_observation_ready") is True),
        "history_line_surface_plan_ready": bool(source.get("history_line_surface_plan_ready") is True),
        "history_line_surface_connected": bool(source.get("history_line_surface_connected") is True),
        "visible_surface_connected": bool(source.get("visible_surface_connected") is True),
        "raw_text_included": False,
        "comment_text_body_included": False,
        "public_response_key_added": False,
    }
    reasons = _dedupe(source.get("surface_plan_rejection_reasons") or [])
    if reasons:
        summary["rejection_reasons"] = reasons[:20]
    return {key: value for key, value in summary.items() if value != "" and value is not None}


def assert_user_label_connection_surface_plan_meta_contract(value: Any, *, allow_partial: bool = False) -> None:
    if _contains_text_payload_key(value):
        raise ValueError("UserLabelConnectionSurfacePlan meta must not include raw text/comment/surface payload keys")
    if _flag_true(value, _FORBIDDEN_TRUE_FLAGS):
        raise ValueError("UserLabelConnectionSurfacePlan meta contains a forbidden true flag")
    if allow_partial:
        json.dumps(value, ensure_ascii=False, sort_keys=True)
        return
    if not isinstance(value, Mapping):
        raise ValueError("UserLabelConnectionSurfacePlan meta must be a mapping")
    if value.get("schema_version") != USER_LABEL_CONNECTION_SURFACE_PLAN_SCHEMA_VERSION:
        raise ValueError("unexpected UserLabelConnectionSurfacePlan schema_version")
    if value.get("step") != USER_LABEL_CONNECTION_SURFACE_PLAN_STEP:
        raise ValueError("unexpected UserLabelConnectionSurfacePlan step")
    if value.get("surface_plan_kind") not in _ALLOWED_SURFACE_PLAN_KINDS:
        raise ValueError("unexpected surface_plan_kind")
    if value.get("connectable_family") not in _ALLOWED_CONNECTABLE_FAMILIES:
        raise ValueError("unexpected connectable_family")
    if value.get("fixed_sentence_template_added") is not False:
        raise ValueError("Surface Plan must not add a fixed sentence template")
    if value.get("comment_text_generated_by_this_layer") is not False:
        raise ValueError("Surface Plan must not generate comment_text")
    if value.get("public_response_key_added") is not False:
        raise ValueError("Surface Plan must not add public response keys")
    for key in (
        "raw_input_included",
        "raw_text_included",
        "comment_text_body_included",
        "candidate_body_included",
        "surface_body_included",
        "surface_text_body_included",
        "internal_question_body_included",
        "private_user_dictionary_text_included",
    ):
        if value.get(key) is not False:
            raise ValueError(f"Surface Plan requires {key}=false")

    roles = set(_dedupe(value.get("must_include_roles") or []))
    must_not_roles = set(_dedupe(value.get("must_not_include_roles") or []))
    shape = _safe_mapping(value.get("surface_shape"))
    for key in ("opening_reception", "current_input_observation", "history_connection_observation", "meaning_support", "closing_partner_line"):
        if key not in shape:
            raise ValueError(f"Surface Plan surface_shape missing {key}")
    for role in _FORBIDDEN_SURFACE_ROLES:
        if role not in must_not_roles:
            raise ValueError(f"Surface Plan must_not_include_roles missing {role}")

    if value.get("history_line_surface_connected") is not False:
        raise ValueError("Phase 6 must not connect history line surface")
    if value.get("visible_surface_connected") is not False:
        raise ValueError("Phase 6 must not connect visible surface")
    if value.get("runtime_surface_connected") is not False:
        raise ValueError("Phase 6 must not connect runtime surface")
    if value.get("comment_text_connected") is not False:
        raise ValueError("Phase 6 must not connect comment_text")

    if value.get("surface_plan_kind") == SURFACE_PLAN_KIND_LIMITED_HISTORY_LINE_OBSERVATION:
        if value.get("gate_passed") is not True:
            raise ValueError("limited surface plan requires passed gate")
        if value.get("connectable_family") not in _LIMITED_CONNECTABLE_FAMILIES:
            raise ValueError("limited surface plan requires limited connectable family")
        if not set(_REQUIRED_SURFACE_ROLES).issubset(roles):
            raise ValueError("limited surface plan missing required roles")
        targets = set(_dedupe(value.get("section_targets") or []))
        if not targets or not targets.issubset(_ALLOWED_SECTION_TARGETS):
            raise ValueError("limited surface plan has invalid section targets")
        if shape.get("current_input_observation") != "required":
            raise ValueError("limited surface plan requires current_input_observation")
        if shape.get("history_connection_observation") != "required_when_history_surface":
            raise ValueError("limited surface plan requires history_connection_observation")
        if shape.get("meaning_support") != "required":
            raise ValueError("limited surface plan requires meaning_support")
        permission = _safe_mapping(value.get("surface_permission"))
        if permission.get("may_surface_now") is not False:
            raise ValueError("Phase 6 plan must not surface immediately")
        if permission.get("may_surface_after_user_label_connection_gate") is not True:
            raise ValueError("limited Phase 6 plan requires Gate permission")
    else:
        if value.get("history_connection_surface_plan_allowed") is True:
            raise ValueError("blocked/meta-only surface plan cannot be allowed")

    public = _safe_mapping(value.get("public_contract"))
    for key, expected in _public_contract().items():
        if public.get(key) is not expected:
            raise ValueError(f"Surface Plan public contract violates {key}=false")
    json.dumps(value, ensure_ascii=False, sort_keys=True)




@dataclass(frozen=True)
class UserLabelConnectionVisibleSurfaceConnection:
    """Phase 8 result: visible text is separate from safe internal meta.

    The ``meta`` payload is safe to pass through the public sanitizer.  The
    generated/comment text is intentionally held outside the meta object so raw
    body text never leaks into ``input_feedback.emlis_ai`` diagnostics.
    """

    comment_text: str
    applied: bool
    meta: dict[str, Any]

    def as_meta(self) -> dict[str, Any]:
        return dict(self.meta)


_PHASE8_SCOPE_MARKERS: Final = (
    "この期間の記録では",
    "以前の近い記録にも",
    "今回と近い記録の範囲では",
    "残っている記録を並べると",
    "Emlisから見える範囲では",
)
_PHASE8_SOFT_MARKERS: Final = (
    "ように見えます",
    "ように思います",
    "かもしれません",
    "近い形に見えます",
    "線として見え始めています",
)
_PHASE8_FORBIDDEN_SURFACE_FRAGMENTS: Final = (
    "あなたはこういう人",
    "あなたはいつも",
    "今後も",
    "原因は",
    "本当は",
    "こうするべき",
    "してください",
    "性格",
    "診断",
    "相手が悪い",
    "治ります",
    "治りません",
)
_PHASE8_BLOCKED_CONTEXT_MARKERS: Final = (
    "low_information",
    "safety",
    "safety_adjacent",
    "safety_triage_required",
    "self_denial",
    "target_judgement",
)
_PHASE8_REQUIRED_EXISTING_GATES: Final = (
    "tone_guard",
    "grounding",
    "visible_surface_acceptance_gate",
    "runtime_surface_pre_return_gate",
)


def _phase8_has_any(text: str, markers: Iterable[str]) -> bool:
    return any(marker and marker in text for marker in markers)


def _phase8_gate_passed(report: Any) -> bool:
    gate = _safe_mapping(report)
    if not gate:
        return False
    if gate.get("passed") is True:
        return True
    if gate.get("blocked") is True:
        return False
    action = _clean(gate.get("action")).lower()
    classification = _clean(gate.get("classification")).lower()
    status = _clean(gate.get("status")).lower()
    if action in {"allow", "pass", "passed", "accept"}:
        return True
    if status in {"passed", "pass", "ok", "accepted"}:
        return True
    if classification in {"green", "safe", "accepted", "passed"}:
        return True
    return False


def _phase8_existing_gate_report_summary(existing_gate_reports: Mapping[str, Any] | None) -> tuple[dict[str, dict[str, Any]], list[str]]:
    source = _safe_mapping(existing_gate_reports)
    summary: dict[str, dict[str, Any]] = {}
    reasons: list[str] = []
    for gate_name in _PHASE8_REQUIRED_EXISTING_GATES:
        raw = source.get(gate_name)
        gate = _safe_mapping(raw)
        if not gate:
            summary[gate_name] = {"passed": False, "primary_reason": REJECTION_VISIBLE_EXISTING_GATE_REPORT_MISSING}
            reasons.append(f"{REJECTION_VISIBLE_EXISTING_GATE_REPORT_MISSING}:{gate_name}")
            continue
        passed = _phase8_gate_passed(gate)
        primary_reason = _clean(gate.get("primary_reason") or gate.get("reason"))
        if not primary_reason:
            nested_reasons = _dedupe(gate.get("rejection_reasons") or [])
            primary_reason = nested_reasons[0] if nested_reasons else ""
        if not passed:
            reasons.append(primary_reason or f"{REJECTION_VISIBLE_EXISTING_GATE_BLOCKED}:{gate_name}")
        summary[gate_name] = {
            "passed": passed,
            "primary_reason": primary_reason or None,
        }
    return summary, _dedupe(reasons)


def _phase8_safe_base_meta(surface_plan: Mapping[str, Any] | None, *, applied: bool, rejection_reasons: Sequence[Any]) -> dict[str, Any]:
    plan = _safe_mapping(surface_plan)
    evidence = _safe_mapping(plan.get("evidence_contract"))
    roles = _dedupe(plan.get("must_include_roles") or [])
    return {
        "schema_version": USER_LABEL_CONNECTION_VISIBLE_SURFACE_SCHEMA_VERSION,
        "step": USER_LABEL_CONNECTION_VISIBLE_SURFACE_STEP,
        "phase": USER_LABEL_CONNECTION_VISIBLE_SURFACE_PHASE,
        "surface_plan_schema_version": _clean(plan.get("schema_version")),
        "surface_plan_kind": _clean(plan.get("surface_plan_kind")),
        "connectable_family": _clean(plan.get("connectable_family")),
        "candidate_id_present": bool(_clean(plan.get("candidate_id"))),
        "evaluated": True,
        "applied": bool(applied),
        "history_connection_applied": bool(applied),
        "history_line_surface_connected": bool(applied),
        "visible_surface_connected": bool(applied),
        "runtime_surface_connected": bool(applied),
        "comment_text_connected": bool(applied),
        "limited_visible_surface_connection_applied": bool(applied),
        "scope_marker_required": True,
        "soft_marker_required": True,
        "scope_marker_present": bool(applied),
        "soft_marker_present": bool(applied),
        "not_personality_disclaimer_present": bool(applied),
        "existing_surface_gates_required": list(_PHASE8_REQUIRED_EXISTING_GATES),
        "existing_surface_gates_passed": bool(applied),
        "evidence_record_count": _int(evidence.get("evidence_record_count")),
        "minimum_evidence_record_count": _int(evidence.get("minimum_evidence_record_count"), 2) or 2,
        "current_record_included": bool(evidence.get("current_record_included") is True),
        "history_record_count": _int(evidence.get("history_record_count")),
        "must_include_roles_present": list(roles),
        "rejection_reasons": _dedupe(rejection_reasons),
        "public_meta_summary_only": True,
        "fixed_sentence_template_added": False,
        "public_response_key_added": False,
        "api_route_changed": False,
        "request_key_changed": False,
        "response_shape_changed": False,
        "db_physical_name_changed": False,
        "rn_visible_contract_changed": False,
        "rn_visible_title_changed": False,
        "raw_input_included": False,
        "raw_text_included": False,
        "history_raw_text_included": False,
        "raw_fact_text_included": False,
        "comment_text_body_included": False,
        "candidate_body_included": False,
        "surface_body_included": False,
        "surface_text_body_included": False,
        "internal_question_body_included": False,
        "private_user_dictionary_text_included": False,
        "record_ids_included": False,
        "diagnosis_allowed": False,
        "personality_claim_allowed": False,
        "cause_claim_allowed": False,
        "advice_allowed": False,
        "future_prediction_allowed": False,
        "always_claim_allowed": False,
        "should_statement_allowed": False,
    }


def _phase8_blocked_result(existing_comment_text: str, surface_plan: Mapping[str, Any] | None, reasons: Sequence[Any], *, gate_reports: Mapping[str, Any] | None = None) -> UserLabelConnectionVisibleSurfaceConnection:
    meta = _phase8_safe_base_meta(surface_plan, applied=False, rejection_reasons=reasons)
    if gate_reports:
        meta["existing_surface_gate_reports"] = {key: dict(value) for key, value in gate_reports.items() if isinstance(value, Mapping)}
    assert_user_label_connection_visible_surface_connection_meta_contract(meta)
    return UserLabelConnectionVisibleSurfaceConnection(comment_text=existing_comment_text, applied=False, meta=meta)


def _phase8_history_observation_line(connectable_family: str) -> str:
    # This is the minimal visible connection surface.  It is not a user-specific
    # template body, does not mention raw inputs, and always carries scope + soft
    # markers required by the dedicated Gate.
    if connectable_family == CONNECTABLE_FAMILY_LONG_MEANING_ARC:
        support = "残っている記録を並べたときの、自己情報の長い線として扱います。"
    elif connectable_family == CONNECTABLE_FAMILY_STRUCTURE_QUESTION:
        support = "残っている記録を並べたときの、状態と環境の関係として扱います。"
    else:
        support = "残っている記録を並べたときに、自己情報が少し線として見え始めている、という扱いです。"
    return (
        "Emlisから見える範囲では、今回と近い記録の範囲にも、"
        "似た状態ラベルと環境ラベルが重なっているように見えます。"
        "人を決めつけるものではなく、"
        f"{support}"
    )


def build_user_label_connection_limited_visible_surface_connection(
    existing_comment_text: Any,
    surface_plan: Mapping[str, Any] | None,
    *,
    existing_gate_reports: Mapping[str, Any] | None = None,
    safety_context: Any = "",
) -> UserLabelConnectionVisibleSurfaceConnection:
    """Connect a Phase 6 surface plan to visible ``comment_text`` for Phase 8.

    This layer is intentionally narrow: it only appends a safe, generic
    history-line observation when the Phase 6 plan is ready and the existing
    tone/grounding/runtime/visible gates have already passed.  It keeps the
    public contract additive-only by returning body text separately from safe
    identifier/count/boolean meta.
    """

    base_text = _clean(existing_comment_text)
    plan = _safe_mapping(surface_plan)
    if not base_text:
        return _phase8_blocked_result(base_text, plan, [REJECTION_VISIBLE_EXISTING_COMMENT_TEXT_MISSING])
    if USER_LABEL_CONNECTION_VISIBLE_SURFACE_PHASE in base_text:
        return _phase8_blocked_result(base_text, plan, [REJECTION_VISIBLE_ALREADY_CONNECTED])
    if _clean(safety_context).lower() in _PHASE8_BLOCKED_CONTEXT_MARKERS or any(marker in _clean(safety_context).lower() for marker in _PHASE8_BLOCKED_CONTEXT_MARKERS):
        return _phase8_blocked_result(base_text, plan, [REJECTION_VISIBLE_SAFETY_CONTEXT_BLOCKED])
    if _contains_text_payload_key(plan) or _flag_true(plan, _FORBIDDEN_TRUE_FLAGS):
        return _phase8_blocked_result(base_text, plan, [REJECTION_RAW_TEXT_PAYLOAD_DETECTED])
    if plan.get("surface_plan_kind") != SURFACE_PLAN_KIND_LIMITED_HISTORY_LINE_OBSERVATION:
        return _phase8_blocked_result(base_text, plan, [REJECTION_VISIBLE_SURFACE_PLAN_NOT_READY])
    family = _clean(plan.get("connectable_family"))
    if family not in _LIMITED_CONNECTABLE_FAMILIES:
        return _phase8_blocked_result(base_text, plan, [REJECTION_CONNECTABLE_FAMILY_UNSUPPORTED])
    if plan.get("history_connection_surface_plan_allowed") is not True or plan.get("limited_history_line_observation_ready") is not True:
        return _phase8_blocked_result(base_text, plan, [REJECTION_VISIBLE_SURFACE_PLAN_NOT_READY])
    evidence = _safe_mapping(plan.get("evidence_contract"))
    if _int(evidence.get("evidence_record_count")) < 2 or evidence.get("current_record_included") is not True:
        return _phase8_blocked_result(base_text, plan, [REJECTION_VISIBLE_SURFACE_PLAN_NOT_READY])
    roles = set(_dedupe(plan.get("must_include_roles") or []))
    if not set(_REQUIRED_SURFACE_ROLES).issubset(roles):
        return _phase8_blocked_result(base_text, plan, [REJECTION_VISIBLE_SURFACE_PLAN_NOT_READY])

    gate_summary, gate_reasons = _phase8_existing_gate_report_summary(existing_gate_reports)
    if gate_reasons:
        return _phase8_blocked_result(base_text, plan, gate_reasons or [REJECTION_VISIBLE_EXISTING_GATE_BLOCKED], gate_reports=gate_summary)

    history_line = _phase8_history_observation_line(family)
    if not _phase8_has_any(history_line, _PHASE8_SCOPE_MARKERS):
        return _phase8_blocked_result(base_text, plan, [REJECTION_VISIBLE_SCOPE_MARKER_MISSING], gate_reports=gate_summary)
    if not _phase8_has_any(history_line, _PHASE8_SOFT_MARKERS):
        return _phase8_blocked_result(base_text, plan, [REJECTION_VISIBLE_SOFT_MARKER_MISSING], gate_reports=gate_summary)
    if _phase8_has_any(history_line, _PHASE8_FORBIDDEN_SURFACE_FRAGMENTS):
        return _phase8_blocked_result(base_text, plan, [REJECTION_VISIBLE_FORBIDDEN_CLAIM_DETECTED], gate_reports=gate_summary)

    comment_text = f"{base_text}\n\n{history_line}"
    meta = _phase8_safe_base_meta(plan, applied=True, rejection_reasons=[])
    meta["existing_surface_gate_reports"] = gate_summary
    meta["surface_connection_style"] = "append_limited_history_line_observation"
    meta["comment_text_body_in_meta_included"] = False
    assert_user_label_connection_visible_surface_connection_meta_contract(meta)
    return UserLabelConnectionVisibleSurfaceConnection(comment_text=comment_text, applied=True, meta=meta)


def build_user_label_connection_limited_visible_comment_text(existing_comment_text: Any, surface_plan: Mapping[str, Any] | None, **kwargs: Any) -> str:
    return build_user_label_connection_limited_visible_surface_connection(existing_comment_text, surface_plan, **kwargs).comment_text


def user_label_connection_visible_surface_public_summary(value: Mapping[str, Any] | None) -> dict[str, Any]:
    source = _safe_mapping(value)
    if not source:
        return {}
    if _contains_text_payload_key(source):
        return {
            "public_meta_summary_only": True,
            "phase": USER_LABEL_CONNECTION_VISIBLE_SURFACE_PHASE,
            "evaluated": True,
            "applied": False,
            "history_connection_applied": False,
            "visible_surface_connected": False,
            "comment_text_connected": False,
            "rejection_reasons": ["user_label_connection_visible_surface_public_meta_unsafe"],
            "raw_text_included": False,
            "comment_text_body_included": False,
            "public_response_key_added": False,
        }
    summary = {
        "public_meta_summary_only": True,
        "schema_version": _clean(source.get("schema_version")),
        "phase": _clean(source.get("phase")),
        "evaluated": bool(source.get("evaluated") is True),
        "applied": bool(source.get("applied") is True),
        "limited_visible_surface_connection_applied": bool(source.get("limited_visible_surface_connection_applied") is True),
        "history_connection_applied": bool(source.get("history_connection_applied") is True),
        "history_line_surface_connected": bool(source.get("history_line_surface_connected") is True),
        "visible_surface_connected": bool(source.get("visible_surface_connected") is True),
        "runtime_surface_connected": bool(source.get("runtime_surface_connected") is True),
        "comment_text_connected": bool(source.get("comment_text_connected") is True),
        "surface_plan_kind": _clean(source.get("surface_plan_kind")),
        "connectable_family": _clean(source.get("connectable_family")),
        "history_connection_evidence_record_count": _int(source.get("evidence_record_count")),
        "history_record_count": _int(source.get("history_record_count")),
        "scope_marker_required": bool(source.get("scope_marker_required") is True),
        "soft_marker_required": bool(source.get("soft_marker_required") is True),
        "scope_marker_present": bool(source.get("scope_marker_present") is True),
        "soft_marker_present": bool(source.get("soft_marker_present") is True),
        "existing_surface_gates_passed": bool(source.get("existing_surface_gates_passed") is True),
        "raw_text_included": False,
        "comment_text_body_included": False,
        "public_response_key_added": False,
    }
    reasons = _dedupe(source.get("rejection_reasons") or [])
    if reasons:
        summary["rejection_reasons"] = reasons[:20]
    return {key: value for key, value in summary.items() if value not in ("", None)}


def assert_user_label_connection_visible_surface_connection_meta_contract(value: Any) -> None:
    if _contains_text_payload_key(value):
        raise ValueError("UserLabelConnection visible surface meta must not include raw/comment/surface body keys")
    if not isinstance(value, Mapping):
        raise ValueError("UserLabelConnection visible surface meta must be a mapping")
    if value.get("schema_version") != USER_LABEL_CONNECTION_VISIBLE_SURFACE_SCHEMA_VERSION:
        raise ValueError("unexpected UserLabelConnection visible surface schema_version")
    if value.get("step") != USER_LABEL_CONNECTION_VISIBLE_SURFACE_STEP:
        raise ValueError("unexpected UserLabelConnection visible surface step")
    if value.get("public_response_key_added") is not False:
        raise ValueError("Phase 8 must not add public response keys")
    for key in (
        "api_route_changed",
        "request_key_changed",
        "response_shape_changed",
        "db_physical_name_changed",
        "rn_visible_contract_changed",
        "rn_visible_title_changed",
        "raw_input_included",
        "raw_text_included",
        "history_raw_text_included",
        "raw_fact_text_included",
        "comment_text_body_included",
        "candidate_body_included",
        "surface_body_included",
        "surface_text_body_included",
        "internal_question_body_included",
        "private_user_dictionary_text_included",
        "record_ids_included",
        "fixed_sentence_template_added",
        "diagnosis_allowed",
        "personality_claim_allowed",
        "cause_claim_allowed",
        "advice_allowed",
        "future_prediction_allowed",
        "always_claim_allowed",
        "should_statement_allowed",
    ):
        if value.get(key) is not False:
            raise ValueError(f"Phase 8 visible surface meta requires {key}=false")
    applied = bool(value.get("applied") is True)
    for key in ("history_connection_applied", "history_line_surface_connected", "visible_surface_connected", "runtime_surface_connected", "comment_text_connected"):
        if value.get(key) is not applied:
            raise ValueError(f"Phase 8 visible surface meta requires {key}=applied")
    if applied:
        if value.get("scope_marker_present") is not True or value.get("soft_marker_present") is not True:
            raise ValueError("Phase 8 visible surface requires scope and soft markers")
        if value.get("existing_surface_gates_passed") is not True:
            raise ValueError("Phase 8 visible surface requires existing gates to pass")
        if _clean(value.get("connectable_family")) not in _LIMITED_CONNECTABLE_FAMILIES:
            raise ValueError("Phase 8 visible surface requires limited connectable family")
    json.dumps(value, ensure_ascii=False, sort_keys=True)


def build_user_label_connection_visible_surface_binding_meta(visible_surface_meta: Mapping[str, Any] | None, *, evidence_span_ids: Sequence[Any] | None = None) -> dict[str, Any]:
    source = _safe_mapping(visible_surface_meta)
    return {
        "binding_contract_version": "cocolon.emlis.user_label_connection.visible_surface_binding.v1",
        "user_label_connection_visible_surface_binding_ready": bool(source.get("applied") is True),
        "history_line_surface_connected": bool(source.get("history_line_surface_connected") is True),
        "scope_marker_present": bool(source.get("scope_marker_present") is True),
        "soft_marker_present": bool(source.get("soft_marker_present") is True),
        "evidence_record_count": _int(source.get("evidence_record_count")),
        "evidence_span_count": len(_dedupe(evidence_span_ids or [])),
        "comment_text_body_included": False,
        "raw_text_included": False,
        "public_response_key_added": False,
    }

# Compatibility alias for later phases/tests.
def assert_user_label_connection_surface_plan_meta(value: Any) -> None:
    assert_user_label_connection_surface_plan_meta_contract(value)


__all__ = [
    "USER_LABEL_CONNECTION_SURFACE_PLAN_SCHEMA_VERSION",
    "USER_LABEL_CONNECTION_SURFACE_PLAN_STEP",
    "SURFACE_PLAN_KIND_LIMITED_HISTORY_LINE_OBSERVATION",
    "SURFACE_PLAN_KIND_META_ONLY",
    "SURFACE_PLAN_KIND_BLOCKED",
    "CONNECTABLE_FAMILY_STRUCTURE_QUESTION",
    "CONNECTABLE_FAMILY_LONG_MEANING_ARC",
    "CONNECTABLE_FAMILY_SELF_UNDERSTANDING_FOLLOW",
    "CONNECTABLE_FAMILIES",
    "SUPPRESSED_CONTEXT_FAMILIES",
    "MUST_INCLUDE_ROLES",
    "MUST_NOT_INCLUDE_ROLES",
    "REJECTION_GATE_NOT_PASSED",
    "REJECTION_CONNECTABLE_FAMILY_SUPPRESSED",
    "REJECTION_SUPPRESSED_CONTEXT_FAMILY",
    "REJECTION_CONNECTABLE_FAMILY_UNSUPPORTED",
    "REJECTION_CONNECTABLE_FAMILY_NOT_ALLOWED",
    "REJECTION_CANDIDATE_MISSING",
    "REJECTION_RAW_TEXT_PAYLOAD_DETECTED",
    "REJECTION_FIXED_SENTENCE_TEMPLATE_DETECTED",
    "build_user_label_connection_surface_plan",
    "build_user_label_connection_surface_plan_meta",
    "user_label_connection_surface_plan_public_summary",
    "assert_user_label_connection_surface_plan_meta",
    "assert_user_label_connection_surface_plan_meta_contract",
    "USER_LABEL_CONNECTION_VISIBLE_SURFACE_SCHEMA_VERSION",
    "USER_LABEL_CONNECTION_VISIBLE_SURFACE_STEP",
    "USER_LABEL_CONNECTION_VISIBLE_SURFACE_PHASE",
    "USER_LABEL_CONNECTION_VISIBLE_SURFACE_META_KEY",
    "REJECTION_VISIBLE_EXISTING_COMMENT_TEXT_MISSING",
    "REJECTION_VISIBLE_SURFACE_PLAN_NOT_READY",
    "REJECTION_VISIBLE_EXISTING_GATE_REPORT_MISSING",
    "REJECTION_VISIBLE_EXISTING_GATE_BLOCKED",
    "REJECTION_VISIBLE_SCOPE_MARKER_MISSING",
    "REJECTION_VISIBLE_SOFT_MARKER_MISSING",
    "REJECTION_VISIBLE_FORBIDDEN_CLAIM_DETECTED",
    "REJECTION_VISIBLE_ALREADY_CONNECTED",
    "REJECTION_VISIBLE_SAFETY_CONTEXT_BLOCKED",
    "UserLabelConnectionVisibleSurfaceConnection",
    "build_user_label_connection_limited_visible_surface_connection",
    "build_user_label_connection_limited_visible_comment_text",
    "build_user_label_connection_visible_surface_binding_meta",
    "user_label_connection_visible_surface_public_summary",
    "assert_user_label_connection_visible_surface_connection_meta_contract",
]
