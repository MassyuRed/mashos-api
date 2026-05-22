# -*- coding: utf-8 -*-
from __future__ import annotations

"""Step 3 User Fact Grounding Boundary for EmlisAI observation replies.

This module defines the pre-composer boundary for using user dictionary / user
fact material in observation replies.  It is intentionally meta-only:

* Free never reads or carries user facts into ``facts_used``;
* subscription plans may use sanitized fact identifiers;
* explicit references require surface disclosure;
* implicit references may only help focus/relation weighting;
* low-information input must not be promoted to eligible from facts alone;
* no raw user input, raw fact text, or generated ``comment_text`` is returned.

The boundary is designed to sit between capability/context collection and later
composer layers.  Runtime integration remains Step 10; this service gives those
later layers a single, testable contract to consume.
"""

from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass, field
import json
import re
from typing import Any, Final

from emlis_ai_observation_reply_contract import (
    OBSERVATION_ELIGIBILITY_STATUS_ELIGIBLE,
    OBSERVATION_ELIGIBILITY_STATUS_LOW_INFORMATION,
    OBSERVATION_REPLY_KIND_ELIGIBLE,
    OBSERVATION_REPLY_KIND_LOW_INFORMATION,
    UNKNOWN_SLOT_EVENT,
    USER_FACT_GROUNDING_MODE_DISABLED,
    USER_FACT_GROUNDING_MODE_EXPLICIT_REFERENCE,
    USER_FACT_GROUNDING_MODE_IMPLICIT_FOCUS,
    assert_observation_reply_meta_contract,
    build_observation_reply_meta,
)

USER_FACT_GROUNDING_BOUNDARY_VERSION: Final = "emlis.user_fact_grounding_boundary.v1"
USER_FACT_GROUNDING_BOUNDARY_STEP: Final = "Step3_User_Fact_Grounding_Boundary"

PLAN_FREE: Final = "free"
PLAN_SUBSCRIPTION: Final = "subscription"

USER_FACT_USE_INTERNAL_QUESTION_ANSWER: Final = "internal_question_answer"
USER_FACT_USE_FOCUS_SELECTION: Final = "focus_selection"
USER_FACT_USE_RELATION_WEIGHT: Final = "relation_weight"

FORBIDDEN_USER_FACT_USE_PROMOTE_LOW_INFO: Final = "promote_low_info_to_eligible"
FORBIDDEN_USER_FACT_USE_ASSERT_CURRENT_EVENT: Final = "assert_current_event"
FORBIDDEN_USER_FACT_USE_PERSONALITY_TENDENCY: Final = "personality_tendency"

_ALLOWED_MODES: Final = frozenset(
    {
        USER_FACT_GROUNDING_MODE_DISABLED,
        USER_FACT_GROUNDING_MODE_EXPLICIT_REFERENCE,
        USER_FACT_GROUNDING_MODE_IMPLICIT_FOCUS,
    }
)
_SUBSCRIPTION_PLAN_KEYS: Final = frozenset({"plus", "premium", "subscription", "subscriber"})
_FREE_PLAN_KEYS: Final = frozenset({"", "free"})
_SPACE_RE: Final = re.compile(r"\s+")
_EXPLICIT_PAST_REFERENCE_RE: Final = re.compile(
    r"(前に|以前|以前にも|前回|この前|前の|過去|また同じ|同じ感じ|前話した|話したこと|残していた|残していました)"
)

_TEXT_PAYLOAD_KEYS: Final = frozenset(
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
        "note",
        "summary",
        "label",
        "trigger",
        "likely_meaning",
    }
)
_FORBIDDEN_TRUE_FLAGS: Final = frozenset(
    {
        "raw_input_included",
        "raw_text_included",
        "comment_text_included",
        "comment_text_body_included",
        "public_status_extended",
        "observation_status_enum_extended",
        "api_response_key_change",
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
        "external_ai_used",
        "local_llm_used",
        "user_fact_may_promote_to_eligible",
        "promote_low_info_to_eligible",
        "assert_current_event_from_user_fact",
        "personality_tendency_allowed",
        "current_event_assertion_allowed",
    }
)


def _clean(value: Any) -> str:
    return _SPACE_RE.sub(" ", str(value or "").replace("\u3000", " ")).strip()


def _dedupe_strings(values: Iterable[Any] | Any | None) -> list[str]:
    if values is None:
        return []
    if isinstance(values, (str, bytes, bytearray)):
        iterable: Iterable[Any] = [values]
    elif isinstance(values, Iterable):
        iterable = values
    else:
        iterable = [values]
    out: list[str] = []
    for value in iterable:
        item = _clean(value)
        if item and item not in out:
            out.append(item)
    return out


def _contains_text_payload_key(value: Any) -> bool:
    if isinstance(value, Mapping):
        for key, item in value.items():
            if _clean(key) in _TEXT_PAYLOAD_KEYS:
                return True
            if _contains_text_payload_key(item):
                return True
        return False
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        return any(_contains_text_payload_key(item) for item in value)
    if hasattr(value, "__dict__"):
        return _contains_text_payload_key(vars(value))
    return False


def _normalize_plan(raw_plan: Any = None, capability: Any = None) -> str:
    candidates = [raw_plan]
    if capability is not None:
        candidates.extend(
            [
                getattr(capability, "tier", None),
                getattr(capability, "subscription_tier", None),
                getattr(capability, "plan", None),
            ]
        )
        if getattr(capability, "model_read_enabled", False) or getattr(capability, "include_derived_user_model", False):
            candidates.append(PLAN_SUBSCRIPTION)
    saw_explicit_free = False
    for candidate in candidates:
        value = _clean(candidate).lower()
        if value in _SUBSCRIPTION_PLAN_KEYS:
            return PLAN_SUBSCRIPTION
        if value == PLAN_FREE:
            saw_explicit_free = True
    return PLAN_FREE if saw_explicit_free or not candidates else PLAN_FREE


def _normalize_mode(value: Any) -> str:
    mode = _clean(value) or USER_FACT_GROUNDING_MODE_DISABLED
    if mode not in _ALLOWED_MODES:
        raise ValueError(f"unsupported user fact grounding mode: {mode}")
    return mode


def _mapping_get(value: Any, key: str, default: Any = None) -> Any:
    if isinstance(value, Mapping):
        return value.get(key, default)
    return getattr(value, key, default)


def _fact_ref_from_mapping(item: Mapping[str, Any], index: int, *, fallback_kind: str = "user_fact") -> dict[str, Any]:
    fact_id = _clean(item.get("fact_id") or item.get("id") or item.get("ref_id") or item.get("source_id") or item.get("anchor_key") or item.get("key"))
    if not fact_id:
        fact_id = f"{fallback_kind}_{index + 1}"
    ref: dict[str, Any] = {"fact_id": fact_id}
    source_kind = _clean(item.get("source_kind") or item.get("kind") or fallback_kind)
    if source_kind:
        ref["source_kind"] = source_kind
    for key in ("source", "ref_id", "mode", "role", "status"):
        value = _clean(item.get(key))
        if value:
            ref[key] = value
    return ref


def _fact_ref_from_object(item: Any, index: int, *, fallback_kind: str = "user_fact") -> dict[str, Any]:
    fact_id = _clean(
        getattr(item, "fact_id", None)
        or getattr(item, "id", None)
        or getattr(item, "ref_id", None)
        or getattr(item, "source_id", None)
        or getattr(item, "anchor_key", None)
        or getattr(item, "key", None)
    )
    if not fact_id:
        fact_id = f"{fallback_kind}_{index + 1}"
    ref: dict[str, Any] = {"fact_id": fact_id, "source_kind": fallback_kind}
    status = _clean(getattr(item, "status", None))
    if status:
        ref["status"] = status
    return ref


def _dedupe_fact_refs(refs: Sequence[Mapping[str, Any]]) -> list[dict[str, Any]]:
    out: list[dict[str, Any]] = []
    seen: set[str] = set()
    for ref in refs:
        safe_ref = {str(key): value for key, value in dict(ref).items() if _clean(value)}
        key = json.dumps(safe_ref, ensure_ascii=False, sort_keys=True)
        if key in seen:
            continue
        seen.add(key)
        out.append(safe_ref)
    return out


def _sanitize_fact_refs(user_facts: Any, *, fallback_kind: str = "user_fact") -> list[dict[str, Any]]:
    if user_facts is None:
        return []
    if isinstance(user_facts, Mapping):
        iterable: Iterable[Any] = [user_facts]
    elif isinstance(user_facts, Sequence) and not isinstance(user_facts, (str, bytes, bytearray)):
        iterable = user_facts
    else:
        iterable = [user_facts]

    refs: list[dict[str, Any]] = []
    for index, item in enumerate(iterable):
        if isinstance(item, Mapping):
            refs.append(_fact_ref_from_mapping(item, index, fallback_kind=fallback_kind))
        elif hasattr(item, "__dict__"):
            refs.append(_fact_ref_from_object(item, index, fallback_kind=fallback_kind))
        else:
            fact_id = _clean(item)
            if fact_id:
                refs.append({"fact_id": fact_id, "source_kind": fallback_kind})
    return _dedupe_fact_refs(refs)


def _extract_refs_from_derived_user_model(model: Any) -> list[dict[str, Any]]:
    if not model:
        return []
    refs: list[dict[str, Any]] = []
    buckets = [
        ("hypotheses", "derived_user_model_hypothesis"),
        ("open_topic_anchors", "derived_user_model_topic_anchor"),
        ("recovery_anchors", "derived_user_model_recovery_anchor"),
    ]
    for attr, kind in buckets:
        values = _mapping_get(model, attr, []) or []
        if isinstance(values, Sequence) and not isinstance(values, (str, bytes, bytearray)):
            refs.extend(_sanitize_fact_refs(values, fallback_kind=kind))

    interpretive_frame = _mapping_get(model, "interpretive_frame", None)
    if interpretive_frame:
        for attr, kind in (
            ("value_anchors", "derived_user_model_value_anchor"),
            ("meaning_map", "derived_user_model_meaning_map"),
        ):
            values = _mapping_get(interpretive_frame, attr, []) or []
            if isinstance(values, Sequence) and not isinstance(values, (str, bytes, bytearray)):
                refs.extend(_sanitize_fact_refs(values, fallback_kind=kind))
    return _dedupe_fact_refs(refs)


def _extract_refs_from_history_rows(rows: Any, *, fallback_kind: str) -> list[dict[str, Any]]:
    if not rows:
        return []
    if isinstance(rows, Mapping):
        iterable: Iterable[Any] = [rows]
    elif isinstance(rows, Sequence) and not isinstance(rows, (str, bytes, bytearray)):
        iterable = rows
    else:
        iterable = [rows]
    refs: list[dict[str, Any]] = []
    for index, item in enumerate(iterable):
        if isinstance(item, Mapping):
            row_id = _clean(item.get("id") or item.get("emotion_id") or item.get("answer_id") or item.get("created_at"))
            refs.append({"fact_id": row_id or f"{fallback_kind}_{index + 1}", "source_kind": fallback_kind})
        else:
            refs.append({"fact_id": f"{fallback_kind}_{index + 1}", "source_kind": fallback_kind})
    return _dedupe_fact_refs(refs)


def collect_user_fact_refs_from_source_bundle(source_bundle: Any) -> list[dict[str, Any]]:
    """Collect sanitized identifiers from a SourceBundle-like object.

    Raw row text, labels, summaries, and memo bodies are intentionally omitted.
    """

    if not source_bundle:
        return []
    refs: list[dict[str, Any]] = []
    refs.extend(_extract_refs_from_derived_user_model(_mapping_get(source_bundle, "derived_user_model", None)))
    refs.extend(_extract_refs_from_history_rows(_mapping_get(source_bundle, "last_input", None), fallback_kind="last_input"))
    refs.extend(_extract_refs_from_history_rows(_mapping_get(source_bundle, "same_day_recent_inputs", []), fallback_kind="same_day_recent_input"))
    refs.extend(_extract_refs_from_history_rows(_mapping_get(source_bundle, "similar_inputs", []), fallback_kind="similar_input"))
    refs.extend(_extract_refs_from_history_rows(_mapping_get(source_bundle, "latest_today_question_answer", None), fallback_kind="today_question_answer"))
    return _dedupe_fact_refs(refs)


def _eligibility_meta(eligibility_decision: Any) -> dict[str, Any]:
    if eligibility_decision is None:
        return {}
    if isinstance(eligibility_decision, Mapping):
        return dict(eligibility_decision)
    as_meta = getattr(eligibility_decision, "as_meta", None)
    if callable(as_meta):
        meta = as_meta()
        return dict(meta) if isinstance(meta, Mapping) else {}
    return {}


def _current_input_text(current_input: Any) -> str:
    if isinstance(current_input, Mapping):
        parts = [current_input.get("memo"), current_input.get("memo_action")]
        return _clean("。".join(_clean(part) for part in parts if _clean(part)))
    return _clean(current_input)


def _has_explicit_past_reference(current_input: Any) -> bool:
    return bool(_EXPLICIT_PAST_REFERENCE_RE.search(_current_input_text(current_input)))


def _normalize_unknown_slots(eligibility: Mapping[str, Any], explicit_unknown_slots: Any = None) -> list[str]:
    slots = _dedupe_strings(explicit_unknown_slots)
    if not slots:
        slots = _dedupe_strings(eligibility.get("unknown_slots"))
    return slots


def _resolve_reply_kind_and_status(
    *,
    eligibility_decision: Any = None,
    observation_reply_kind: Any = None,
    eligibility_status: Any = None,
) -> tuple[str, str, bool]:
    meta = _eligibility_meta(eligibility_decision)
    kind = _clean(observation_reply_kind) or _clean(meta.get("observation_reply_kind")) or OBSERVATION_REPLY_KIND_ELIGIBLE
    status = _clean(eligibility_status) or _clean(meta.get("eligibility_status")) or _clean(meta.get("status"))
    if kind not in {OBSERVATION_REPLY_KIND_ELIGIBLE, OBSERVATION_REPLY_KIND_LOW_INFORMATION}:
        kind = OBSERVATION_REPLY_KIND_LOW_INFORMATION if status == OBSERVATION_ELIGIBILITY_STATUS_LOW_INFORMATION else OBSERVATION_REPLY_KIND_ELIGIBLE
    if not status or status not in {OBSERVATION_ELIGIBILITY_STATUS_ELIGIBLE, OBSERVATION_ELIGIBILITY_STATUS_LOW_INFORMATION}:
        status = OBSERVATION_ELIGIBILITY_STATUS_LOW_INFORMATION if kind == OBSERVATION_REPLY_KIND_LOW_INFORMATION else OBSERVATION_ELIGIBILITY_STATUS_ELIGIBLE
    low_info = kind == OBSERVATION_REPLY_KIND_LOW_INFORMATION or status == OBSERVATION_ELIGIBILITY_STATUS_LOW_INFORMATION
    if low_info:
        return OBSERVATION_REPLY_KIND_LOW_INFORMATION, OBSERVATION_ELIGIBILITY_STATUS_LOW_INFORMATION, True
    return OBSERVATION_REPLY_KIND_ELIGIBLE, OBSERVATION_ELIGIBILITY_STATUS_ELIGIBLE, False


def _allowed_uses_for(mode: str, *, low_information: bool, has_facts: bool) -> list[str]:
    if mode == USER_FACT_GROUNDING_MODE_DISABLED or not has_facts:
        return []
    if low_information:
        # In low-information replies, user facts can only bias the next focus or
        # relation weight. They must not answer the current event for the user.
        return [USER_FACT_USE_FOCUS_SELECTION, USER_FACT_USE_RELATION_WEIGHT]
    if mode == USER_FACT_GROUNDING_MODE_EXPLICIT_REFERENCE:
        return [USER_FACT_USE_INTERNAL_QUESTION_ANSWER, USER_FACT_USE_FOCUS_SELECTION, USER_FACT_USE_RELATION_WEIGHT]
    return [USER_FACT_USE_FOCUS_SELECTION, USER_FACT_USE_RELATION_WEIGHT]


@dataclass(frozen=True)
class UserFactGroundingDecision:
    plan: str
    mode: str
    user_fact_allowed: bool
    user_fact_read_enabled: bool
    facts_used: Sequence[Mapping[str, Any]] = field(default_factory=tuple)
    facts_ignored: Sequence[Mapping[str, Any]] = field(default_factory=tuple)
    surface_disclosure_required: bool = False
    allowed_uses: Sequence[str] = field(default_factory=tuple)
    forbidden_uses: Sequence[str] = field(default_factory=tuple)
    eligibility_status: str = OBSERVATION_ELIGIBILITY_STATUS_ELIGIBLE
    observation_reply_kind: str = OBSERVATION_REPLY_KIND_ELIGIBLE
    eligible_for_full_observation: bool = True
    question_required: bool = False
    user_fact_may_hint: bool = False
    user_fact_may_promote_to_eligible: bool = False
    low_information_protected: bool = False
    free_violation_guard: bool = False
    free_user_fact_blocked: bool = False
    fact_raw_text_stripped: bool = False
    unknown_slots: Sequence[str] = field(default_factory=tuple)
    observation_reply_meta: Mapping[str, Any] = field(default_factory=dict)

    @property
    def version(self) -> str:
        return USER_FACT_GROUNDING_BOUNDARY_VERSION

    @property
    def step(self) -> str:
        return USER_FACT_GROUNDING_BOUNDARY_STEP

    def as_meta(self) -> dict[str, Any]:
        meta: dict[str, Any] = {
            "version": USER_FACT_GROUNDING_BOUNDARY_VERSION,
            "schema_version": USER_FACT_GROUNDING_BOUNDARY_VERSION,
            "source_step": USER_FACT_GROUNDING_BOUNDARY_STEP,
            "step": USER_FACT_GROUNDING_BOUNDARY_STEP,
            "user_fact_grounding_boundary_ready": True,
            "plan": self.plan,
            "user_fact_allowed": bool(self.user_fact_allowed),
            "user_fact_read_enabled": bool(self.user_fact_read_enabled),
            "mode": self.mode,
            "user_fact_grounding_mode": self.mode,
            "facts_used": [dict(item) for item in self.facts_used],
            "facts_ignored": [dict(item) for item in self.facts_ignored],
            "surface_disclosure_required": bool(self.surface_disclosure_required),
            "allowed_uses": list(self.allowed_uses),
            "forbidden_uses": list(self.forbidden_uses),
            "eligibility_status": self.eligibility_status,
            "observation_reply_kind": self.observation_reply_kind,
            "eligible_for_full_observation": bool(self.eligible_for_full_observation),
            "question_required": bool(self.question_required),
            "user_fact_may_hint": bool(self.user_fact_may_hint),
            "user_fact_may_promote_to_eligible": False,
            "must_not_promote_low_info_to_eligible": True,
            "must_not_assert_current_event_from_user_fact": True,
            "assert_current_event_from_user_fact": False,
            "personality_tendency_allowed": False,
            "low_information_protected": bool(self.low_information_protected),
            "free_violation_guard": bool(self.free_violation_guard),
            "free_user_fact_blocked": bool(self.free_user_fact_blocked),
            "fact_raw_text_stripped": bool(self.fact_raw_text_stripped),
            "unknown_slots": list(self.unknown_slots),
            "observation_reply_meta": dict(self.observation_reply_meta or {}),
            "raw_input_included": False,
            "raw_text_included": False,
            "comment_text_included": False,
            "comment_text_body_included": False,
            "public_status_extended": False,
            "observation_status_enum_extended": False,
            "api_response_key_change": False,
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
        }
        assert_user_fact_grounding_decision_contract(meta)
        return meta


def resolve_user_fact_grounding_boundary(
    *,
    subscription_tier: Any = None,
    capability: Any = None,
    source_bundle: Any = None,
    user_facts: Any = None,
    eligibility_decision: Any = None,
    observation_reply_kind: Any = None,
    eligibility_status: Any = None,
    current_input: Any = None,
    requested_mode: Any = None,
    explicit_reference_requested: bool | None = None,
    surface_disclosure_requested: bool | None = None,
    unknown_slots: Any = None,
) -> UserFactGroundingDecision:
    """Resolve the Step 3 user-fact boundary for the next composer layer."""

    plan = _normalize_plan(subscription_tier, capability)
    eligibility = _eligibility_meta(eligibility_decision)
    kind, status, low_info = _resolve_reply_kind_and_status(
        eligibility_decision=eligibility,
        observation_reply_kind=observation_reply_kind,
        eligibility_status=eligibility_status,
    )
    slots = _normalize_unknown_slots(eligibility, unknown_slots)
    if low_info and not slots:
        slots = [UNKNOWN_SLOT_EVENT]

    provided_fact_refs = _sanitize_fact_refs(user_facts, fallback_kind="user_fact")
    source_bundle_refs = collect_user_fact_refs_from_source_bundle(source_bundle)
    all_fact_refs = _dedupe_fact_refs([*provided_fact_refs, *source_bundle_refs])
    fact_raw_text_stripped = _contains_text_payload_key(user_facts) or _contains_text_payload_key(source_bundle)

    if plan == PLAN_FREE:
        mode = USER_FACT_GROUNDING_MODE_DISABLED
        facts_used: list[dict[str, Any]] = []
        facts_ignored = all_fact_refs
        user_fact_allowed = False
        user_fact_read_enabled = False
        may_hint = False
        surface_disclosure_required = False
        free_blocked = bool(all_fact_refs)
    else:
        user_fact_allowed = True
        user_fact_read_enabled = True
        facts_used = all_fact_refs
        facts_ignored = []
        has_facts = bool(facts_used)
        requested = _normalize_mode(requested_mode) if requested_mode else ""
        explicit = bool(explicit_reference_requested) or bool(surface_disclosure_requested) or requested == USER_FACT_GROUNDING_MODE_EXPLICIT_REFERENCE
        if not explicit and current_input is not None:
            explicit = _has_explicit_past_reference(current_input)
        if not has_facts:
            mode = USER_FACT_GROUNDING_MODE_DISABLED
        elif explicit:
            mode = USER_FACT_GROUNDING_MODE_EXPLICIT_REFERENCE
        elif requested == USER_FACT_GROUNDING_MODE_IMPLICIT_FOCUS:
            mode = USER_FACT_GROUNDING_MODE_IMPLICIT_FOCUS
        else:
            mode = USER_FACT_GROUNDING_MODE_IMPLICIT_FOCUS
        may_hint = bool(has_facts and mode != USER_FACT_GROUNDING_MODE_DISABLED)
        surface_disclosure_required = mode == USER_FACT_GROUNDING_MODE_EXPLICIT_REFERENCE
        free_blocked = False

    has_effective_facts = bool(facts_used)
    allowed_uses = _allowed_uses_for(mode, low_information=low_info, has_facts=has_effective_facts)
    forbidden_uses = [
        FORBIDDEN_USER_FACT_USE_PROMOTE_LOW_INFO,
        FORBIDDEN_USER_FACT_USE_ASSERT_CURRENT_EVENT,
        FORBIDDEN_USER_FACT_USE_PERSONALITY_TENDENCY,
    ]
    eligible_full = kind == OBSERVATION_REPLY_KIND_ELIGIBLE and not low_info
    question_required = low_info

    # Feed sanitized refs into Step 1 meta.  For Free, pass attempted refs so the
    # Step 1 guard marks free_user_fact_blocked=true while still returning no
    # facts_used.
    facts_for_contract: list[dict[str, Any]] = all_fact_refs if plan == PLAN_FREE else list(facts_used)
    observation_reply_meta = build_observation_reply_meta(
        observation_reply_kind=kind,
        eligibility_status=status,
        plan=plan,
        eligible_for_full_observation=eligible_full,
        question_required=question_required,
        user_fact_grounding_mode=mode,
        user_fact_allowed=user_fact_allowed or free_blocked,
        user_fact_may_hint=may_hint,
        facts_used=facts_for_contract,
        surface_disclosure_required=surface_disclosure_required,
        unknown_slots=slots,
        inference_depths=[1, 2, 3] if eligible_full else [],
        primary_reason="user_fact_grounding_boundary",
    )
    assert_observation_reply_meta_contract(observation_reply_meta)

    return UserFactGroundingDecision(
        plan=plan,
        mode=mode,
        user_fact_allowed=user_fact_allowed,
        user_fact_read_enabled=user_fact_read_enabled,
        facts_used=tuple(facts_used),
        facts_ignored=tuple(facts_ignored),
        surface_disclosure_required=surface_disclosure_required,
        allowed_uses=tuple(allowed_uses),
        forbidden_uses=tuple(forbidden_uses),
        eligibility_status=status,
        observation_reply_kind=kind,
        eligible_for_full_observation=eligible_full,
        question_required=question_required,
        user_fact_may_hint=may_hint,
        user_fact_may_promote_to_eligible=False,
        low_information_protected=low_info,
        free_violation_guard=plan == PLAN_FREE,
        free_user_fact_blocked=free_blocked,
        fact_raw_text_stripped=fact_raw_text_stripped,
        unknown_slots=tuple(slots),
        observation_reply_meta=observation_reply_meta,
    )


def build_user_fact_grounding_boundary(**kwargs: Any) -> UserFactGroundingDecision:
    """Alias for integration sites that prefer build_* naming."""

    return resolve_user_fact_grounding_boundary(**kwargs)


def resolve_emlis_ai_user_fact_grounding_boundary(**kwargs: Any) -> UserFactGroundingDecision:
    """EmlisAI-specific alias for Step 3 boundary integration/tests."""

    return resolve_user_fact_grounding_boundary(**kwargs)


def assert_user_fact_grounding_decision_contract(
    value: Mapping[str, Any] | UserFactGroundingDecision,
    *,
    source: str = "user_fact_grounding_decision",
) -> None:
    """Validate the Step 3 boundary payload."""

    if isinstance(value, UserFactGroundingDecision):
        value = value.as_meta()
    if not isinstance(value, Mapping):
        raise ValueError(f"{source} must be a mapping")
    if _contains_text_payload_key(value):
        raise ValueError(f"{source} must be meta-only and must not include raw text/comment keys")
    for key in _FORBIDDEN_TRUE_FLAGS:
        if value.get(key) is True:
            raise ValueError(f"{source} violates fixed contract: {key}=true")

    plan = _clean(value.get("plan"))
    mode = _normalize_mode(value.get("mode") or value.get("user_fact_grounding_mode"))
    facts_used = list(value.get("facts_used") or [])
    facts_ignored = list(value.get("facts_ignored") or [])
    if plan not in {PLAN_FREE, PLAN_SUBSCRIPTION}:
        raise ValueError(f"{source} has unsupported plan: {plan or '<empty>'}")
    if plan == PLAN_FREE:
        if value.get("user_fact_allowed") is True or value.get("user_fact_read_enabled") is True:
            raise ValueError("Free must not allow user fact reads")
        if facts_used:
            raise ValueError("Free must not carry facts_used")
        if mode != USER_FACT_GROUNDING_MODE_DISABLED:
            raise ValueError("Free must force disabled user fact mode")
        # Free can ignore zero or more facts; when facts exist, guard must show
        # that they were blocked before composer use.
        if facts_ignored and value.get("free_user_fact_blocked") is not True:
            raise ValueError("Free ignored facts must set free_user_fact_blocked")
    else:
        if value.get("user_fact_allowed") is not True or value.get("user_fact_read_enabled") is not True:
            raise ValueError("Subscription must expose user fact read permission")
        if facts_used and mode == USER_FACT_GROUNDING_MODE_DISABLED:
            raise ValueError("Subscription facts_used require explicit or implicit mode")

    if mode == USER_FACT_GROUNDING_MODE_EXPLICIT_REFERENCE and value.get("surface_disclosure_required") is not True:
        raise ValueError("explicit_reference requires surface_disclosure_required")
    if mode == USER_FACT_GROUNDING_MODE_IMPLICIT_FOCUS and value.get("surface_disclosure_required") is True:
        raise ValueError("implicit_focus must not require surface disclosure")

    if value.get("user_fact_may_promote_to_eligible") is True:
        raise ValueError("user facts must not promote low information to eligible")
    if value.get("assert_current_event_from_user_fact") is True:
        raise ValueError("user facts must not assert the current event")
    if value.get("personality_tendency_allowed") is True:
        raise ValueError("user facts must not allow personality tendency assertions")

    forbidden_uses = set(_dedupe_strings(value.get("forbidden_uses")))
    for required in (
        FORBIDDEN_USER_FACT_USE_PROMOTE_LOW_INFO,
        FORBIDDEN_USER_FACT_USE_ASSERT_CURRENT_EVENT,
        FORBIDDEN_USER_FACT_USE_PERSONALITY_TENDENCY,
    ):
        if required not in forbidden_uses:
            raise ValueError(f"{source} missing forbidden use: {required}")

    low_info = bool(value.get("low_information_protected")) or _clean(value.get("eligibility_status")) == OBSERVATION_ELIGIBILITY_STATUS_LOW_INFORMATION
    allowed_uses = set(_dedupe_strings(value.get("allowed_uses")))
    if low_info:
        if value.get("eligible_for_full_observation") is True:
            raise ValueError("low information must not be full-observation eligible")
        if value.get("question_required") is not True:
            raise ValueError("low information must require question")
        if USER_FACT_USE_INTERNAL_QUESTION_ANSWER in allowed_uses:
            raise ValueError("low-information facts must not answer the current event internally")

    reply_meta = value.get("observation_reply_meta") or {}
    if reply_meta:
        assert_observation_reply_meta_contract(reply_meta, source=f"{source}.observation_reply_meta")


def dump_user_fact_grounding_decision(value: UserFactGroundingDecision | Mapping[str, Any]) -> str:
    meta = value.as_meta() if isinstance(value, UserFactGroundingDecision) else dict(value)
    assert_user_fact_grounding_decision_contract(meta)
    return json.dumps(meta, ensure_ascii=False, sort_keys=True)


__all__ = [
    "USER_FACT_GROUNDING_BOUNDARY_VERSION",
    "USER_FACT_GROUNDING_BOUNDARY_STEP",
    "PLAN_FREE",
    "PLAN_SUBSCRIPTION",
    "USER_FACT_USE_INTERNAL_QUESTION_ANSWER",
    "USER_FACT_USE_FOCUS_SELECTION",
    "USER_FACT_USE_RELATION_WEIGHT",
    "FORBIDDEN_USER_FACT_USE_PROMOTE_LOW_INFO",
    "FORBIDDEN_USER_FACT_USE_ASSERT_CURRENT_EVENT",
    "FORBIDDEN_USER_FACT_USE_PERSONALITY_TENDENCY",
    "UserFactGroundingDecision",
    "collect_user_fact_refs_from_source_bundle",
    "resolve_user_fact_grounding_boundary",
    "build_user_fact_grounding_boundary",
    "resolve_emlis_ai_user_fact_grounding_boundary",
    "assert_user_fact_grounding_decision_contract",
    "dump_user_fact_grounding_decision",
]
