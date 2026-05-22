# -*- coding: utf-8 -*-
from __future__ import annotations

"""Step 1 meta contract for EmlisAI observation replies.

This module defines the shared, meta-only contract for the next observation
reply implementation.  It does not change the public ``observation_status``
enum, does not create user-facing text, and does not relax Display Gate.

Low-information observation is represented as an internal reply kind.  The RN
surface still sees the existing public contract: ``observation_status=passed``
with non-empty ``input_feedback.comment_text``.
"""

import json
from collections.abc import Mapping, Sequence
from typing import Any, Final

OBSERVATION_REPLY_CONTRACT_VERSION: Final = "emlis.observation_reply_contract.v1"
OBSERVATION_REPLY_CONTRACT_STEP: Final = "Step1_Observation_Reply_Contract"
OBSERVATION_COMMENT_TEXT_CONTRACT: Final = "passed_only"
OBSERVATION_PUBLIC_STATUS_FOR_DISPLAY: Final = "passed"
MAX_OBSERVATION_INFERENCE_DEPTH: Final = 3

OBSERVATION_REPLY_KIND_ELIGIBLE: Final = "eligible_observation"
OBSERVATION_REPLY_KIND_LOW_INFORMATION: Final = "low_information_observation"

OBSERVATION_ELIGIBILITY_STATUS_ELIGIBLE: Final = "eligible"
OBSERVATION_ELIGIBILITY_STATUS_LOW_INFORMATION: Final = "low_information"

USER_FACT_GROUNDING_MODE_DISABLED: Final = "disabled"
USER_FACT_GROUNDING_MODE_EXPLICIT_REFERENCE: Final = "explicit_reference"
USER_FACT_GROUNDING_MODE_IMPLICIT_FOCUS: Final = "implicit_focus"

OBSERVATION_ROLE_EMPATHY: Final = "empathy"
OBSERVATION_ROLE_INPUT_ARRANGEMENT: Final = "input_arrangement"
OBSERVATION_ROLE_STATE_VERBALIZATION: Final = "state_verbalization"
OBSERVATION_ROLE_COMPANION_CLOSE: Final = "companion_close"
OBSERVATION_ROLE_LOW_INFO_RECEIVE: Final = "low_info_receive"
OBSERVATION_ROLE_LOW_INFO_KNOWN_SCOPE: Final = "low_info_known_scope"
OBSERVATION_ROLE_LOW_INFO_QUESTION: Final = "low_info_question"

UNKNOWN_SLOT_EVENT: Final = "event"
UNKNOWN_SLOT_TARGET: Final = "target"
UNKNOWN_SLOT_CAUSE: Final = "cause"
UNKNOWN_SLOT_RELATION: Final = "relation"
UNKNOWN_SLOT_TIME: Final = "time"
UNKNOWN_SLOT_DESIRED_DIRECTION: Final = "desired_direction"
UNKNOWN_SLOT_CURRENT_FEELING_TARGET: Final = "current_feeling_target"

_ALLOWED_REPLY_KINDS = {
    OBSERVATION_REPLY_KIND_ELIGIBLE,
    OBSERVATION_REPLY_KIND_LOW_INFORMATION,
}
_ALLOWED_ELIGIBILITY_STATUSES = {
    OBSERVATION_ELIGIBILITY_STATUS_ELIGIBLE,
    OBSERVATION_ELIGIBILITY_STATUS_LOW_INFORMATION,
}
_ALLOWED_USER_FACT_MODES = {
    USER_FACT_GROUNDING_MODE_DISABLED,
    USER_FACT_GROUNDING_MODE_EXPLICIT_REFERENCE,
    USER_FACT_GROUNDING_MODE_IMPLICIT_FOCUS,
}
_ALLOWED_OBSERVATION_ROLES = {
    OBSERVATION_ROLE_EMPATHY,
    OBSERVATION_ROLE_INPUT_ARRANGEMENT,
    OBSERVATION_ROLE_STATE_VERBALIZATION,
    OBSERVATION_ROLE_COMPANION_CLOSE,
    OBSERVATION_ROLE_LOW_INFO_RECEIVE,
    OBSERVATION_ROLE_LOW_INFO_KNOWN_SCOPE,
    OBSERVATION_ROLE_LOW_INFO_QUESTION,
}
_ALLOWED_UNKNOWN_SLOTS = {
    UNKNOWN_SLOT_EVENT,
    UNKNOWN_SLOT_TARGET,
    UNKNOWN_SLOT_CAUSE,
    UNKNOWN_SLOT_RELATION,
    UNKNOWN_SLOT_TIME,
    UNKNOWN_SLOT_DESIRED_DIRECTION,
    UNKNOWN_SLOT_CURRENT_FEELING_TARGET,
}
_SUBSCRIPTION_PLAN_KEYS = {"plus", "premium", "subscription", "subscriber"}
_FREE_PLAN_KEYS = {"", "free"}

_FORBIDDEN_TEXT_PAYLOAD_KEYS = {
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
    "current_input",
    "currentInput",
    "comment_text",
    "commentText",
    "input_feedback_comment",
    "inputFeedbackComment",
    "candidate_comment_text",
    "public_comment_text",
    "reply_text",
    "replyText",
    "surface_text",
    "realized_text",
    "body",
    "text",
}

_FORBIDDEN_TRUE_FLAGS = {
    "public_status_extended",
    "observation_status_enum_extended",
    "public_response_key_change",
    "public_response_key_changed",
    "api_response_key_change",
    "api_response_key_changed",
    "api_route_changed",
    "db_physical_name_changed",
    "rn_visible_contract_changed",
    "rn_visible_title_changed",
    "display_gate_relaxed",
    "reader_gate_relaxed",
    "grounding_gate_relaxed",
    "template_gate_relaxed",
    "gate_relaxed",
    "fixed_fallback_used",
    "fixed_sentence_template_used",
    "completed_sentence_template_used",
    "external_ai_used",
    "local_llm_used",
    "user_fact_may_promote_to_eligible",
    "promote_low_info_to_eligible",
    "assert_current_event_from_user_fact",
    "personality_tendency_allowed",
    "raw_input_included",
    "raw_text_included",
    "comment_text_included",
    "comment_text_body_included",
}


def _clean(value: Any) -> str:
    return str(value or "").strip()


def _dedupe_strings(values: Any) -> list[str]:
    out: list[str] = []
    if values is None:
        return out
    iterable = values if isinstance(values, Sequence) and not isinstance(values, (str, bytes, bytearray)) else [values]
    for value in iterable:
        item = _clean(value)
        if item and item not in out:
            out.append(item)
    return out


def _contains_forbidden_text_payload_key(value: Any) -> bool:
    if isinstance(value, Mapping):
        for key, nested in value.items():
            if _clean(key) in _FORBIDDEN_TEXT_PAYLOAD_KEYS:
                return True
            if _contains_forbidden_text_payload_key(nested):
                return True
        return False
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        return any(_contains_forbidden_text_payload_key(item) for item in value)
    return False


def _normalize_reply_kind(value: Any) -> str:
    kind = _clean(value)
    if kind not in _ALLOWED_REPLY_KINDS:
        raise ValueError(f"unsupported observation_reply_kind: {kind or '<empty>'}")
    return kind


def _default_eligibility_status(kind: str) -> str:
    if kind == OBSERVATION_REPLY_KIND_LOW_INFORMATION:
        return OBSERVATION_ELIGIBILITY_STATUS_LOW_INFORMATION
    return OBSERVATION_ELIGIBILITY_STATUS_ELIGIBLE


def _normalize_eligibility_status(value: Any, *, kind: str) -> str:
    status = _clean(value) or _default_eligibility_status(kind)
    if status not in _ALLOWED_ELIGIBILITY_STATUSES:
        raise ValueError(f"unsupported eligibility_status: {status or '<empty>'}")
    if kind == OBSERVATION_REPLY_KIND_LOW_INFORMATION and status != OBSERVATION_ELIGIBILITY_STATUS_LOW_INFORMATION:
        raise ValueError("low_information_observation must keep eligibility_status=low_information")
    if kind == OBSERVATION_REPLY_KIND_ELIGIBLE and status != OBSERVATION_ELIGIBILITY_STATUS_ELIGIBLE:
        raise ValueError("eligible_observation must keep eligibility_status=eligible")
    return status


def _normalize_user_fact_mode(value: Any) -> str:
    mode = _clean(value) or USER_FACT_GROUNDING_MODE_DISABLED
    if mode not in _ALLOWED_USER_FACT_MODES:
        raise ValueError(f"unsupported user_fact_grounding_mode: {mode or '<empty>'}")
    return mode


def _normalize_plan(value: Any) -> str:
    plan = _clean(value).lower()
    if plan in _SUBSCRIPTION_PLAN_KEYS:
        return "subscription"
    if plan in _FREE_PLAN_KEYS:
        return "free"
    return plan or "free"


def _normalize_fact_refs(facts_used: Any) -> list[dict[str, Any]]:
    if facts_used is None:
        return []
    if _contains_forbidden_text_payload_key(facts_used):
        raise ValueError("facts_used must not contain raw text or comment_text payload keys")
    iterable = facts_used if isinstance(facts_used, Sequence) and not isinstance(facts_used, (str, bytes, bytearray)) else [facts_used]
    refs: list[dict[str, Any]] = []
    for index, item in enumerate(iterable):
        if isinstance(item, Mapping):
            fact_id = _clean(item.get("fact_id") or item.get("id") or item.get("ref_id") or item.get("source_id"))
            ref: dict[str, Any] = {"fact_id": fact_id or f"fact_ref_{index + 1}"}
            for key in ("source", "source_kind", "kind", "ref_id", "mode", "role"):
                value = _clean(item.get(key))
                if value:
                    ref[key] = value
            refs.append(ref)
        else:
            fact_id = _clean(item)
            if fact_id:
                refs.append({"fact_id": fact_id})
    return refs


def _normalize_observation_roles(values: Any) -> list[str]:
    roles = _dedupe_strings(values)
    unsupported = [role for role in roles if role not in _ALLOWED_OBSERVATION_ROLES]
    if unsupported:
        raise ValueError(f"unsupported observation role(s): {', '.join(unsupported)}")
    return roles


def _normalize_unknown_slots(values: Any) -> list[str]:
    slots = _dedupe_strings(values)
    unsupported = [slot for slot in slots if slot not in _ALLOWED_UNKNOWN_SLOTS]
    if unsupported:
        raise ValueError(f"unsupported unknown slot(s): {', '.join(unsupported)}")
    return slots


def _normalize_inference_depths(values: Any) -> list[int]:
    if values is None:
        return []
    iterable = values if isinstance(values, Sequence) and not isinstance(values, (str, bytes, bytearray)) else [values]
    depths: list[int] = []
    for value in iterable:
        try:
            depth = int(value)
        except (TypeError, ValueError) as exc:
            raise ValueError(f"invalid inference depth: {value!r}") from exc
        if depth < 1 or depth > MAX_OBSERVATION_INFERENCE_DEPTH:
            raise ValueError("inference_depth must be between 1 and 3")
        if depth not in depths:
            depths.append(depth)
    return depths


def build_observation_reply_meta(
    *,
    observation_reply_kind: Any,
    eligibility_status: Any = "",
    plan: Any = "free",
    eligible_for_full_observation: bool | None = None,
    question_required: bool | None = None,
    user_fact_grounding_mode: Any = USER_FACT_GROUNDING_MODE_DISABLED,
    user_fact_allowed: bool | None = None,
    user_fact_may_hint: bool | None = None,
    facts_used: Any = None,
    surface_disclosure_required: bool | None = None,
    sentence_plan_observation_roles: Any = None,
    unknown_slots: Any = None,
    inference_depths: Any = None,
    primary_reason: Any = "",
) -> dict[str, Any]:
    """Build the shared meta contract for eligible/low-info observation replies.

    The returned payload is intentionally safe to attach to diagnostics: it
    carries only branch/role/status metadata and fact identifiers, never raw user
    text or generated comment text.
    """

    kind = _normalize_reply_kind(observation_reply_kind)
    status = _normalize_eligibility_status(eligibility_status, kind=kind)
    plan_key = _normalize_plan(plan)
    requested_mode = _normalize_user_fact_mode(user_fact_grounding_mode)
    requested_facts = _normalize_fact_refs(facts_used)
    requested_user_fact_allowed = bool(user_fact_allowed) if user_fact_allowed is not None else requested_mode != USER_FACT_GROUNDING_MODE_DISABLED or bool(requested_facts)

    free_plan = plan_key == "free"
    subscription_plan = plan_key == "subscription"
    if not (free_plan or subscription_plan):
        requested_user_fact_allowed = False

    free_user_fact_blocked = False
    if free_plan:
        free_user_fact_blocked = bool(requested_user_fact_allowed or requested_facts or requested_mode != USER_FACT_GROUNDING_MODE_DISABLED)
        mode = USER_FACT_GROUNDING_MODE_DISABLED
        facts = []
        fact_allowed = False
        may_hint = False
    else:
        mode = requested_mode
        facts = requested_facts
        fact_allowed = bool(subscription_plan and requested_user_fact_allowed)
        may_hint = bool(user_fact_may_hint) if user_fact_may_hint is not None else bool(fact_allowed and facts)
        if facts and mode == USER_FACT_GROUNDING_MODE_DISABLED:
            raise ValueError("subscription facts_used require explicit_reference or implicit_focus mode")

    if eligible_for_full_observation is None:
        eligible_full = kind == OBSERVATION_REPLY_KIND_ELIGIBLE
    else:
        eligible_full = bool(eligible_for_full_observation)
    if kind == OBSERVATION_REPLY_KIND_LOW_INFORMATION and eligible_full:
        raise ValueError("low_information_observation must not be eligible_for_full_observation")

    if question_required is None:
        question = kind == OBSERVATION_REPLY_KIND_LOW_INFORMATION
    else:
        question = bool(question_required)
    if kind == OBSERVATION_REPLY_KIND_LOW_INFORMATION and not question:
        raise ValueError("low_information_observation must require a question")

    roles = _normalize_observation_roles(sentence_plan_observation_roles)
    slots = _normalize_unknown_slots(unknown_slots)
    depths = _normalize_inference_depths(inference_depths)

    if kind == OBSERVATION_REPLY_KIND_LOW_INFORMATION and not slots:
        slots = [UNKNOWN_SLOT_EVENT]
    if kind == OBSERVATION_REPLY_KIND_LOW_INFORMATION and not roles:
        roles = [
            OBSERVATION_ROLE_LOW_INFO_RECEIVE,
            OBSERVATION_ROLE_LOW_INFO_KNOWN_SCOPE,
            OBSERVATION_ROLE_LOW_INFO_QUESTION,
        ]

    disclosure_required = (
        bool(surface_disclosure_required)
        if surface_disclosure_required is not None
        else mode == USER_FACT_GROUNDING_MODE_EXPLICIT_REFERENCE
    )
    if mode == USER_FACT_GROUNDING_MODE_EXPLICIT_REFERENCE and not disclosure_required:
        raise ValueError("explicit user fact reference requires surface disclosure")

    meta: dict[str, Any] = {
        "version": OBSERVATION_REPLY_CONTRACT_VERSION,
        "contract_version": OBSERVATION_REPLY_CONTRACT_VERSION,
        "source_step": OBSERVATION_REPLY_CONTRACT_STEP,
        "step": OBSERVATION_REPLY_CONTRACT_STEP,
        "observation_reply_contract_ready": True,
        "observation_reply_kind": kind,
        "eligibility_status": status,
        "eligible_for_full_observation": eligible_full,
        "question_required": question,
        "primary_reason": _clean(primary_reason) or status,
        "public_observation_status": OBSERVATION_PUBLIC_STATUS_FOR_DISPLAY,
        "public_status_for_display": OBSERVATION_PUBLIC_STATUS_FOR_DISPLAY,
        "comment_text_contract": OBSERVATION_COMMENT_TEXT_CONTRACT,
        "low_information_public_status_is_passed": kind == OBSERVATION_REPLY_KIND_LOW_INFORMATION,
        "public_status_extended": False,
        "observation_status_enum_extended": False,
        "api_response_key_change": False,
        "public_response_key_change": False,
        "api_route_changed": False,
        "db_physical_name_changed": False,
        "rn_visible_contract_changed": False,
        "rn_visible_title_changed": False,
        "display_gate_relaxed": False,
        "reader_gate_relaxed": False,
        "grounding_gate_relaxed": False,
        "template_gate_relaxed": False,
        "fixed_fallback_used": False,
        "fixed_sentence_template_used": False,
        "external_ai_used": False,
        "local_llm_used": False,
        "raw_input_included": False,
        "raw_text_included": False,
        "comment_text_included": False,
        "comment_text_body_included": False,
        "current_input_grounding_required": True,
        "max_inference_depth_allowed": MAX_OBSERVATION_INFERENCE_DEPTH,
        "inference_depths": depths,
        "sentence_plan_observation_roles": roles,
        "unknown_slots": slots,
        "plan": plan_key,
        "user_fact_allowed": fact_allowed,
        "user_fact_read_enabled": bool(fact_allowed),
        "user_fact_grounding_mode": mode,
        "user_fact_may_hint": may_hint,
        "user_fact_may_promote_to_eligible": False,
        "surface_disclosure_required": disclosure_required,
        "facts_used": facts,
        "free_user_fact_blocked": free_user_fact_blocked,
        "must_not_assert_current_event_from_user_fact": True,
        "must_not_promote_low_info_to_eligible": True,
        "forbidden_uses": [
            "promote_low_info_to_eligible",
            "assert_current_event",
            "personality_tendency",
        ],
    }
    assert_observation_reply_meta_contract(meta)
    return meta


def assert_observation_reply_meta_contract(
    value: Mapping[str, Any],
    *,
    source: str = "observation_reply_meta",
) -> None:
    """Validate that a payload preserves the Step 1 observation reply contract."""

    if not isinstance(value, Mapping):
        raise ValueError(f"{source} must be a mapping")
    if _contains_forbidden_text_payload_key(value):
        raise ValueError(f"{source} must stay meta-only and must not include text payload keys")
    for key in _FORBIDDEN_TRUE_FLAGS:
        if value.get(key) is True:
            raise ValueError(f"{source} violates fixed contract: {key}=true")

    kind = _normalize_reply_kind(value.get("observation_reply_kind"))
    status = _normalize_eligibility_status(value.get("eligibility_status"), kind=kind)
    if value.get("version") != OBSERVATION_REPLY_CONTRACT_VERSION:
        raise ValueError(f"{source} has invalid version")
    if _clean(value.get("public_observation_status") or value.get("public_status_for_display")) != OBSERVATION_PUBLIC_STATUS_FOR_DISPLAY:
        raise ValueError(f"{source} must keep public observation_status=passed for displayable branches")
    if _clean(value.get("comment_text_contract")) != OBSERVATION_COMMENT_TEXT_CONTRACT:
        raise ValueError(f"{source} must keep comment_text contract passed_only")

    if kind == OBSERVATION_REPLY_KIND_LOW_INFORMATION:
        if value.get("eligible_for_full_observation") is True:
            raise ValueError("low-information reply must not be full-observation eligible")
        if value.get("question_required") is not True:
            raise ValueError("low-information reply must require a question")
        if status != OBSERVATION_ELIGIBILITY_STATUS_LOW_INFORMATION:
            raise ValueError("low-information reply has mismatched eligibility status")
    if kind == OBSERVATION_REPLY_KIND_ELIGIBLE:
        if value.get("eligible_for_full_observation") is not True:
            raise ValueError("eligible reply must be eligible_for_full_observation")
        if status != OBSERVATION_ELIGIBILITY_STATUS_ELIGIBLE:
            raise ValueError("eligible reply has mismatched eligibility status")

    mode = _normalize_user_fact_mode(value.get("user_fact_grounding_mode"))
    facts = value.get("facts_used") or []
    if mode == USER_FACT_GROUNDING_MODE_DISABLED and facts:
        raise ValueError("disabled user fact mode must not carry facts_used")
    if mode == USER_FACT_GROUNDING_MODE_EXPLICIT_REFERENCE and value.get("surface_disclosure_required") is not True:
        raise ValueError("explicit_reference mode requires surface_disclosure_required")
    if _normalize_plan(value.get("plan")) == "free":
        if value.get("user_fact_allowed") is True or facts:
            raise ValueError("free plan must not allow or carry user facts")

    for depth in list(value.get("inference_depths") or []):
        try:
            normalized = int(depth)
        except (TypeError, ValueError) as exc:
            raise ValueError("inference_depths must contain integers") from exc
        if normalized < 1 or normalized > MAX_OBSERVATION_INFERENCE_DEPTH:
            raise ValueError("inference depth exceeds max allowed depth 3")



def dump_observation_reply_meta(value: Mapping[str, Any]) -> str:
    assert_observation_reply_meta_contract(value)
    return json.dumps(dict(value), ensure_ascii=False, sort_keys=True)


__all__ = [
    "OBSERVATION_REPLY_CONTRACT_VERSION",
    "OBSERVATION_REPLY_CONTRACT_STEP",
    "OBSERVATION_COMMENT_TEXT_CONTRACT",
    "OBSERVATION_PUBLIC_STATUS_FOR_DISPLAY",
    "MAX_OBSERVATION_INFERENCE_DEPTH",
    "OBSERVATION_REPLY_KIND_ELIGIBLE",
    "OBSERVATION_REPLY_KIND_LOW_INFORMATION",
    "OBSERVATION_ELIGIBILITY_STATUS_ELIGIBLE",
    "OBSERVATION_ELIGIBILITY_STATUS_LOW_INFORMATION",
    "USER_FACT_GROUNDING_MODE_DISABLED",
    "USER_FACT_GROUNDING_MODE_EXPLICIT_REFERENCE",
    "USER_FACT_GROUNDING_MODE_IMPLICIT_FOCUS",
    "OBSERVATION_ROLE_EMPATHY",
    "OBSERVATION_ROLE_INPUT_ARRANGEMENT",
    "OBSERVATION_ROLE_STATE_VERBALIZATION",
    "OBSERVATION_ROLE_COMPANION_CLOSE",
    "OBSERVATION_ROLE_LOW_INFO_RECEIVE",
    "OBSERVATION_ROLE_LOW_INFO_KNOWN_SCOPE",
    "OBSERVATION_ROLE_LOW_INFO_QUESTION",
    "UNKNOWN_SLOT_EVENT",
    "UNKNOWN_SLOT_TARGET",
    "UNKNOWN_SLOT_CAUSE",
    "UNKNOWN_SLOT_RELATION",
    "UNKNOWN_SLOT_TIME",
    "UNKNOWN_SLOT_DESIRED_DIRECTION",
    "UNKNOWN_SLOT_CURRENT_FEELING_TARGET",
    "build_observation_reply_meta",
    "assert_observation_reply_meta_contract",
    "dump_observation_reply_meta",
]
