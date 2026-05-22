# -*- coding: utf-8 -*-
from __future__ import annotations

"""Step 4 Internal Question Layer for EmlisAI observation replies.

This layer converts the Step 2 eligibility routing result and the Step 3 user
fact grounding boundary into a meta-only set of internal questions.  It does
not generate public ``comment_text``, does not change the public
``observation_status`` enum, and does not relax Display Gate.

The contract deliberately separates:

* questions answered by the current input;
* questions supported by permitted subscription user-fact identifiers; and
* unanswered questions that must be handed to the low-information question
  surface in later composer steps.

Raw current input, generated text, and raw user-fact text are never copied into
this payload.  Only sanitized evidence ids and fact ids are retained.
"""

from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass, field
import json
import re
from typing import Any, Final

from emlis_ai_observation_eligibility_service import (
    OBSERVATION_ELIGIBILITY_STATUS_SAFETY_BLOCKED,
    assert_observation_eligibility_decision_contract,
    route_observation_eligibility,
)
from emlis_ai_observation_reply_contract import (
    MAX_OBSERVATION_INFERENCE_DEPTH,
    OBSERVATION_ELIGIBILITY_STATUS_ELIGIBLE,
    OBSERVATION_ELIGIBILITY_STATUS_LOW_INFORMATION,
    OBSERVATION_REPLY_KIND_ELIGIBLE,
    OBSERVATION_REPLY_KIND_LOW_INFORMATION,
    UNKNOWN_SLOT_EVENT,
    UNKNOWN_SLOT_TARGET,
    USER_FACT_GROUNDING_MODE_DISABLED,
    USER_FACT_GROUNDING_MODE_EXPLICIT_REFERENCE,
    USER_FACT_GROUNDING_MODE_IMPLICIT_FOCUS,
    assert_observation_reply_meta_contract,
    build_observation_reply_meta,
)
from emlis_ai_user_fact_grounding_boundary import (
    USER_FACT_USE_FOCUS_SELECTION,
    USER_FACT_USE_INTERNAL_QUESTION_ANSWER,
    USER_FACT_USE_RELATION_WEIGHT,
    assert_user_fact_grounding_decision_contract,
    resolve_user_fact_grounding_boundary,
)

INTERNAL_QUESTION_LAYER_VERSION: Final = "emlis.internal_question_layer.v1"
INTERNAL_QUESTION_LAYER_STEP: Final = "Step4_Internal_Question_Layer"

INTERNAL_QUESTION_KIND_WHY_THIS_WORD: Final = "why_this_word"
INTERNAL_QUESTION_KIND_WHY_THIS_BURDEN: Final = "why_this_burden"
INTERNAL_QUESTION_KIND_WHAT_RELATION: Final = "what_relation"
INTERNAL_QUESTION_KIND_WHAT_IS_UNKNOWN: Final = "what_is_unknown"

INTERNAL_QUESTION_ANSWERED_BY_CURRENT_INPUT: Final = "answered_by_current_input"
INTERNAL_QUESTION_SUPPORTED_BY_USER_FACT: Final = "supported_by_user_fact"
INTERNAL_QUESTION_UNANSWERED: Final = "unanswered"

INTERNAL_QUESTION_SURFACE_DIRECT: Final = "direct"
INTERNAL_QUESTION_SURFACE_DISSOLVED: Final = "dissolved"
INTERNAL_QUESTION_SURFACE_QUESTION: Final = "question"
INTERNAL_QUESTION_SURFACE_NOT_SURFACE: Final = "not_surface"

# Backward-friendly short aliases for tests and future integration code.
ANSWER_STATUS_ANSWERED_BY_CURRENT_INPUT: Final = INTERNAL_QUESTION_ANSWERED_BY_CURRENT_INPUT
ANSWER_STATUS_SUPPORTED_BY_USER_FACT: Final = INTERNAL_QUESTION_SUPPORTED_BY_USER_FACT
ANSWER_STATUS_UNANSWERED: Final = INTERNAL_QUESTION_UNANSWERED
SURFACE_USE_DIRECT: Final = INTERNAL_QUESTION_SURFACE_DIRECT
SURFACE_USE_DISSOLVED: Final = INTERNAL_QUESTION_SURFACE_DISSOLVED
SURFACE_USE_QUESTION: Final = INTERNAL_QUESTION_SURFACE_QUESTION
SURFACE_USE_NOT_SURFACE: Final = INTERNAL_QUESTION_SURFACE_NOT_SURFACE

_ALLOWED_QUESTION_KINDS: Final = frozenset(
    {
        INTERNAL_QUESTION_KIND_WHY_THIS_WORD,
        INTERNAL_QUESTION_KIND_WHY_THIS_BURDEN,
        INTERNAL_QUESTION_KIND_WHAT_RELATION,
        INTERNAL_QUESTION_KIND_WHAT_IS_UNKNOWN,
    }
)
_ALLOWED_ANSWER_STATUSES: Final = frozenset(
    {
        INTERNAL_QUESTION_ANSWERED_BY_CURRENT_INPUT,
        INTERNAL_QUESTION_SUPPORTED_BY_USER_FACT,
        INTERNAL_QUESTION_UNANSWERED,
    }
)
_ALLOWED_SURFACE_USES: Final = frozenset(
    {
        INTERNAL_QUESTION_SURFACE_DIRECT,
        INTERNAL_QUESTION_SURFACE_DISSOLVED,
        INTERNAL_QUESTION_SURFACE_QUESTION,
        INTERNAL_QUESTION_SURFACE_NOT_SURFACE,
    }
)
_SPACE_RE: Final = re.compile(r"\s+")
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
        "comment_text_generated",
        "public_status_extended",
        "observation_status_enum_extended",
        "public_response_key_change",
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
        "user_fact_used_for_current_event_assertion",
        "personality_tendency_allowed",
        "unsupported_assertion_allowed",
    }
)


def _clean(value: Any) -> str:
    return _SPACE_RE.sub(" ", str(value or "").replace("\u3000", " ")).strip()


def _dedupe(values: Iterable[Any] | Any | None) -> list[str]:
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


def _meta(value: Any) -> dict[str, Any]:
    if value is None:
        return {}
    if isinstance(value, Mapping):
        return dict(value)
    as_meta = getattr(value, "as_meta", None)
    if callable(as_meta):
        result = as_meta()
        return dict(result) if isinstance(result, Mapping) else {}
    return {}


def _safe_fact_refs(refs: Any) -> list[dict[str, Any]]:
    if refs is None:
        return []
    if isinstance(refs, Mapping):
        iterable: Iterable[Any] = [refs]
    elif isinstance(refs, Sequence) and not isinstance(refs, (str, bytes, bytearray)):
        iterable = refs
    else:
        iterable = [refs]

    out: list[dict[str, Any]] = []
    seen: set[str] = set()
    for index, item in enumerate(iterable):
        if isinstance(item, Mapping):
            fact_id = _clean(item.get("fact_id") or item.get("id") or item.get("ref_id") or item.get("source_id"))
            safe: dict[str, Any] = {"fact_id": fact_id or f"user_fact_ref_{index + 1}"}
            for key in ("source", "source_kind", "kind", "ref_id", "mode", "role", "status"):
                value = _clean(item.get(key))
                if value:
                    safe[key] = value
        else:
            fact_id = _clean(item)
            if not fact_id:
                continue
            safe = {"fact_id": fact_id}
        encoded = json.dumps(safe, ensure_ascii=False, sort_keys=True)
        if encoded in seen:
            continue
        seen.add(encoded)
        out.append(safe)
    return out


def _fact_ids(refs: Any) -> list[str]:
    return _dedupe(ref.get("fact_id") for ref in _safe_fact_refs(refs))


def _evidence_ids(known_fragments: Any, *, roles: Sequence[str] | None = None) -> list[str]:
    allowed_roles = set(_dedupe(roles)) if roles else set()
    if not known_fragments:
        return []
    if isinstance(known_fragments, Mapping):
        iterable: Iterable[Any] = [known_fragments]
    elif isinstance(known_fragments, Sequence) and not isinstance(known_fragments, (str, bytes, bytearray)):
        iterable = known_fragments
    else:
        iterable = [known_fragments]

    out: list[str] = []
    for index, item in enumerate(iterable):
        if isinstance(item, Mapping):
            role = _clean(item.get("role"))
            if allowed_roles and role not in allowed_roles:
                continue
            evidence_id = _clean(item.get("evidence_span_id") or item.get("span_id") or item.get("id") or item.get("ref_id"))
        else:
            role = _clean(getattr(item, "role", None))
            if allowed_roles and role not in allowed_roles:
                continue
            evidence_id = _clean(
                getattr(item, "evidence_span_id", None)
                or getattr(item, "span_id", None)
                or getattr(item, "id", None)
                or getattr(item, "ref_id", None)
            )
        if not evidence_id:
            evidence_id = f"evidence_span_{index + 1}"
        if evidence_id not in out:
            out.append(evidence_id)
    return out


def _question_label(kind: str) -> str:
    # Internal labels only.  These are not display templates and are not derived
    # from raw user input.
    return {
        INTERNAL_QUESTION_KIND_WHY_THIS_WORD: "その言葉は、どの状態を示しているか。",
        INTERNAL_QUESTION_KIND_WHY_THIS_BURDEN: "その重さは、どの負荷として残っているか。",
        INTERNAL_QUESTION_KIND_WHAT_RELATION: "入力内の言葉同士に、どの関係があるか。",
        INTERNAL_QUESTION_KIND_WHAT_IS_UNKNOWN: "現時点では、何がまだ見えていないか。",
    }[kind]


def _answer_summary(kind: str, answer_status: str) -> str | None:
    if answer_status == INTERNAL_QUESTION_UNANSWERED:
        return None
    if answer_status == INTERNAL_QUESTION_SUPPORTED_BY_USER_FACT:
        return "user_fact_supports_internal_question_without_current_event_assertion"
    return {
        INTERNAL_QUESTION_KIND_WHY_THIS_WORD: "current_input_has_state_or_load_signal",
        INTERNAL_QUESTION_KIND_WHY_THIS_BURDEN: "current_input_supports_burden_or_handling_weight",
        INTERNAL_QUESTION_KIND_WHAT_RELATION: "current_input_supports_relation_between_signals",
        INTERNAL_QUESTION_KIND_WHAT_IS_UNKNOWN: "current_input_marks_unknown_scope",
    }.get(kind, "current_input_supports_question")


@dataclass(frozen=True)
class InternalQuestion:
    question_id: str
    kind: str
    question: str
    answer_status: str
    inference_depth: int
    surface_use: str
    answer_summary: str | None = None
    supporting_evidence_ids: Sequence[str] = field(default_factory=tuple)
    supporting_user_fact_ids: Sequence[str] = field(default_factory=tuple)
    unknown_slots: Sequence[str] = field(default_factory=tuple)
    allowed_user_fact_uses: Sequence[str] = field(default_factory=tuple)
    current_event_assertion_from_user_fact: bool = False

    def as_meta(self) -> dict[str, Any]:
        return {
            "question_id": self.question_id,
            "kind": self.kind,
            "question": self.question,
            "answer_status": self.answer_status,
            "answer_summary": self.answer_summary,
            "supporting_evidence_ids": list(self.supporting_evidence_ids),
            "supporting_user_fact_ids": list(self.supporting_user_fact_ids),
            "unknown_slots": list(self.unknown_slots),
            "allowed_user_fact_uses": list(self.allowed_user_fact_uses),
            "inference_depth": int(self.inference_depth),
            "surface_use": self.surface_use,
            "current_event_assertion_from_user_fact": False,
            "raw_input_included": False,
            "raw_text_included": False,
            "comment_text_included": False,
        }


@dataclass(frozen=True)
class InternalQuestionSet:
    questions: Sequence[InternalQuestion] = field(default_factory=tuple)
    observation_reply_kind: str = OBSERVATION_REPLY_KIND_ELIGIBLE
    eligibility_status: str = OBSERVATION_ELIGIBILITY_STATUS_ELIGIBLE
    eligible_for_full_observation: bool = True
    question_required: bool = False
    unknown_slots: Sequence[str] = field(default_factory=tuple)
    user_fact_grounding_mode: str = USER_FACT_GROUNDING_MODE_DISABLED
    plan: str = "free"
    facts_used: Sequence[Mapping[str, Any]] = field(default_factory=tuple)
    user_fact_focus_hint_ids: Sequence[str] = field(default_factory=tuple)
    surface_disclosure_required: bool = False
    allowed_user_fact_uses: Sequence[str] = field(default_factory=tuple)
    max_inference_depth_allowed: int = MAX_OBSERVATION_INFERENCE_DEPTH
    overclaim_guard_passed: bool = True
    observation_reply_meta: Mapping[str, Any] = field(default_factory=dict)
    observation_structure_connection: Mapping[str, Any] = field(default_factory=dict)

    @property
    def version(self) -> str:
        return INTERNAL_QUESTION_LAYER_VERSION

    @property
    def step(self) -> str:
        return INTERNAL_QUESTION_LAYER_STEP

    def as_meta(self) -> dict[str, Any]:
        question_metas = [question.as_meta() for question in self.questions]
        max_depth_used = max([int(question.get("inference_depth") or 0) for question in question_metas] or [0])
        answered_count = sum(
            1 for question in question_metas if question.get("answer_status") == INTERNAL_QUESTION_ANSWERED_BY_CURRENT_INPUT
        )
        supported_count = sum(
            1 for question in question_metas if question.get("answer_status") == INTERNAL_QUESTION_SUPPORTED_BY_USER_FACT
        )
        unanswered_count = sum(
            1 for question in question_metas if question.get("answer_status") == INTERNAL_QUESTION_UNANSWERED
        )
        low_information = (
            self.observation_reply_kind == OBSERVATION_REPLY_KIND_LOW_INFORMATION
            or self.eligibility_status == OBSERVATION_ELIGIBILITY_STATUS_LOW_INFORMATION
        )
        low_info_question_surface_required = bool(
            low_information
            and any(
                question.get("kind") == INTERNAL_QUESTION_KIND_WHAT_IS_UNKNOWN
                and question.get("answer_status") == INTERNAL_QUESTION_UNANSWERED
                and question.get("surface_use") == INTERNAL_QUESTION_SURFACE_QUESTION
                for question in question_metas
            )
        )
        meta: dict[str, Any] = {
            "version": INTERNAL_QUESTION_LAYER_VERSION,
            "schema_version": INTERNAL_QUESTION_LAYER_VERSION,
            "source_step": INTERNAL_QUESTION_LAYER_STEP,
            "step": INTERNAL_QUESTION_LAYER_STEP,
            "internal_question_layer_ready": True,
            "observation_reply_kind": self.observation_reply_kind,
            "eligibility_status": self.eligibility_status,
            "eligible_for_full_observation": bool(self.eligible_for_full_observation),
            "question_required": bool(self.question_required),
            "questions": question_metas,
            "unknown_slots": list(self.unknown_slots),
            "max_inference_depth_allowed": int(self.max_inference_depth_allowed),
            "max_inference_depth_used": int(max_depth_used),
            "overclaim_guard_passed": bool(self.overclaim_guard_passed),
            "answered_by_current_input_count": answered_count,
            "answerable_by_current_input_count": answered_count,
            "supported_by_user_fact_count": supported_count,
            "unanswered_count": unanswered_count,
            "unanswered_question_count": unanswered_count,
            "low_information_question_surface_required": low_info_question_surface_required,
            "user_fact_grounding_mode": self.user_fact_grounding_mode,
            "plan": self.plan,
            "facts_used": [dict(item) for item in self.facts_used],
            "user_fact_focus_hint_ids": list(self.user_fact_focus_hint_ids),
            "surface_disclosure_required": bool(self.surface_disclosure_required),
            "allowed_user_fact_uses": list(self.allowed_user_fact_uses),
            "observation_reply_meta": dict(self.observation_reply_meta or {}),
            "observation_structure_dictionary_connected": bool(self.observation_structure_connection),
            "observation_structure_connection": dict(self.observation_structure_connection or {}),
            "structure_internal_question_policy_connected": bool(self.observation_structure_connection),
            "structure_relation_ids": list((self.observation_structure_connection or {}).get("selected_relation_ids") or []),
            "structure_entry_ids": list((self.observation_structure_connection or {}).get("selected_entry_ids") or []),
            "structure_question_ids": list((self.observation_structure_connection or {}).get("composer_entry_ids") or []),
            "structure_forbidden_inference_relation_ids": list((self.observation_structure_connection or {}).get("forbidden_inference_relation_ids") or []),
            "raw_input_included": False,
            "raw_text_included": False,
            "comment_text_included": False,
            "comment_text_body_included": False,
            "comment_text_generated": False,
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
            "user_fact_may_promote_to_eligible": False,
            "promote_low_info_to_eligible": False,
            "assert_current_event_from_user_fact": False,
            "user_fact_used_for_current_event_assertion": False,
            "personality_tendency_allowed": False,
            "unsupported_assertion_allowed": False,
        }
        assert_internal_question_set_contract(meta)
        return meta


def _append_question(
    questions: list[InternalQuestion],
    *,
    kind: str,
    answer_status: str,
    inference_depth: int,
    surface_use: str,
    supporting_evidence_ids: Sequence[str] | None = None,
    supporting_user_fact_ids: Sequence[str] | None = None,
    unknown_slots: Sequence[str] | None = None,
    allowed_user_fact_uses: Sequence[str] | None = None,
) -> None:
    questions.append(
        InternalQuestion(
            question_id=f"iq_{len(questions) + 1:03d}",
            kind=kind,
            question=_question_label(kind),
            answer_status=answer_status,
            answer_summary=_answer_summary(kind, answer_status),
            supporting_evidence_ids=tuple(_dedupe(supporting_evidence_ids)),
            supporting_user_fact_ids=tuple(_dedupe(supporting_user_fact_ids)),
            unknown_slots=tuple(_dedupe(unknown_slots)),
            allowed_user_fact_uses=tuple(_dedupe(allowed_user_fact_uses)),
            inference_depth=int(inference_depth),
            surface_use=surface_use,
            current_event_assertion_from_user_fact=False,
        )
    )


def _resolve_inputs(
    *,
    current_input: Any = None,
    eligibility_decision: Any = None,
    user_fact_grounding_decision: Any = None,
    subscription_tier: Any = None,
    capability: Any = None,
    user_facts: Any = None,
    source_bundle: Any = None,
    evidence_ledger: Any = None,
    observation_graph: Any = None,
    observation_structure_connection: Any = None,
    observation_structure_dictionary: Any = None,
) -> tuple[dict[str, Any], dict[str, Any]]:
    eligibility = eligibility_decision
    if eligibility is None:
        eligibility = route_observation_eligibility(
            current_input=current_input,
            evidence_ledger=evidence_ledger,
            observation_graph=observation_graph,
            capability=capability,
            subscription_tier=subscription_tier,
            user_facts=user_facts,
            observation_structure_connection=observation_structure_connection,
            observation_structure_dictionary=observation_structure_dictionary,
        )
    eligibility_meta = _meta(eligibility)
    assert_observation_eligibility_decision_contract(eligibility_meta)

    user_fact_boundary = user_fact_grounding_decision
    if user_fact_boundary is None:
        user_fact_boundary = resolve_user_fact_grounding_boundary(
            current_input=current_input,
            eligibility_decision=eligibility,
            subscription_tier=subscription_tier,
            capability=capability,
            user_facts=user_facts,
            source_bundle=source_bundle,
        )
    user_fact_meta = _meta(user_fact_boundary)
    assert_user_fact_grounding_decision_contract(user_fact_meta)
    return eligibility_meta, user_fact_meta


def build_internal_question_set(
    *,
    current_input: Any = None,
    eligibility_decision: Any = None,
    user_fact_grounding_decision: Any = None,
    subscription_tier: Any = None,
    capability: Any = None,
    user_facts: Any = None,
    source_bundle: Any = None,
    evidence_ledger: Any = None,
    observation_graph: Any = None,
    observation_structure_connection: Any = None,
    observation_structure_dictionary: Any = None,
) -> InternalQuestionSet:
    """Build the Step 4 meta-only internal question set."""

    eligibility_meta, user_fact_meta = _resolve_inputs(
        current_input=current_input,
        eligibility_decision=eligibility_decision,
        user_fact_grounding_decision=user_fact_grounding_decision,
        subscription_tier=subscription_tier,
        capability=capability,
        user_facts=user_facts,
        source_bundle=source_bundle,
        evidence_ledger=evidence_ledger,
        observation_graph=observation_graph,
        observation_structure_connection=observation_structure_connection,
        observation_structure_dictionary=observation_structure_dictionary,
    )

    status = _clean(eligibility_meta.get("eligibility_status") or eligibility_meta.get("status"))
    if status == OBSERVATION_ELIGIBILITY_STATUS_SAFETY_BLOCKED:
        raise ValueError("Step 4 Internal Question Layer expects inputs after the safety boundary")

    kind = _clean(eligibility_meta.get("observation_reply_kind"))
    low_information = status == OBSERVATION_ELIGIBILITY_STATUS_LOW_INFORMATION or kind == OBSERVATION_REPLY_KIND_LOW_INFORMATION
    if low_information:
        status = OBSERVATION_ELIGIBILITY_STATUS_LOW_INFORMATION
        kind = OBSERVATION_REPLY_KIND_LOW_INFORMATION
    else:
        status = OBSERVATION_ELIGIBILITY_STATUS_ELIGIBLE
        kind = OBSERVATION_REPLY_KIND_ELIGIBLE

    known_fragments = list(eligibility_meta.get("known_fragments") or [])
    detected_roles = set(_dedupe(eligibility_meta.get("detected_signal_roles")))
    relation_types = _dedupe(eligibility_meta.get("relation_types"))
    unknown_slots = _dedupe(eligibility_meta.get("unknown_slots"))
    if low_information and not unknown_slots:
        unknown_slots = [UNKNOWN_SLOT_EVENT, UNKNOWN_SLOT_TARGET]

    all_evidence_ids = _evidence_ids(known_fragments)
    state_evidence_ids = _evidence_ids(known_fragments, roles=["state"])
    relation_evidence_ids = _evidence_ids(
        known_fragments,
        roles=["wish", "blockage", "contrast", "relation_graph", "self_awareness", "repetition", "target", "state"],
    ) or all_evidence_ids

    plan = _clean(user_fact_meta.get("plan")) or _clean(eligibility_meta.get("plan")) or "free"
    user_fact_mode = _clean(user_fact_meta.get("mode") or user_fact_meta.get("user_fact_grounding_mode")) or USER_FACT_GROUNDING_MODE_DISABLED
    allowed_uses = _dedupe(user_fact_meta.get("allowed_uses") or user_fact_meta.get("allowed_user_fact_uses"))
    facts_used = _safe_fact_refs(user_fact_meta.get("facts_used")) if plan == "subscription" else []
    fact_ids = _fact_ids(facts_used)

    questions: list[InternalQuestion] = []
    if all_evidence_ids:
        _append_question(
            questions,
            kind=INTERNAL_QUESTION_KIND_WHY_THIS_WORD,
            answer_status=INTERNAL_QUESTION_ANSWERED_BY_CURRENT_INPUT,
            inference_depth=1,
            surface_use=INTERNAL_QUESTION_SURFACE_DISSOLVED if low_information else INTERNAL_QUESTION_SURFACE_DIRECT,
            supporting_evidence_ids=state_evidence_ids or all_evidence_ids[:2],
        )

    relation_signal_present = bool(
        relation_types
        or {"wish", "blockage", "contrast", "relation_graph", "self_awareness"}.intersection(detected_roles)
        or float(eligibility_meta.get("relation_confidence") or 0.0) >= 0.42
    )
    if not low_information and relation_signal_present and relation_evidence_ids:
        _append_question(
            questions,
            kind=INTERNAL_QUESTION_KIND_WHAT_RELATION,
            answer_status=INTERNAL_QUESTION_ANSWERED_BY_CURRENT_INPUT,
            inference_depth=2,
            surface_use=INTERNAL_QUESTION_SURFACE_DISSOLVED,
            supporting_evidence_ids=relation_evidence_ids[:4],
        )

    handling_weight_supported = bool(
        not low_information
        and all_evidence_ids
        and (
            {"state", "repetition", "self_awareness", "target", "blockage", "wish"}.intersection(detected_roles)
            or float(eligibility_meta.get("current_input_evidence_score") or 0.0) >= 0.58
        )
    )
    if handling_weight_supported:
        _append_question(
            questions,
            kind=INTERNAL_QUESTION_KIND_WHY_THIS_BURDEN,
            answer_status=INTERNAL_QUESTION_ANSWERED_BY_CURRENT_INPUT,
            inference_depth=3,
            surface_use=INTERNAL_QUESTION_SURFACE_DISSOLVED,
            supporting_evidence_ids=all_evidence_ids[:4],
        )

    explicit_internal_answer_allowed = bool(
        not low_information
        and fact_ids
        and plan == "subscription"
        and user_fact_mode == USER_FACT_GROUNDING_MODE_EXPLICIT_REFERENCE
        and USER_FACT_USE_INTERNAL_QUESTION_ANSWER in set(allowed_uses)
    )
    if explicit_internal_answer_allowed:
        _append_question(
            questions,
            kind=INTERNAL_QUESTION_KIND_WHY_THIS_BURDEN,
            answer_status=INTERNAL_QUESTION_SUPPORTED_BY_USER_FACT,
            inference_depth=2,
            surface_use=INTERNAL_QUESTION_SURFACE_DISSOLVED,
            supporting_user_fact_ids=fact_ids,
            allowed_user_fact_uses=allowed_uses,
        )

    user_fact_focus_hint_ids: list[str] = []
    if fact_ids and plan == "subscription" and user_fact_mode != USER_FACT_GROUNDING_MODE_DISABLED:
        if low_information or USER_FACT_USE_INTERNAL_QUESTION_ANSWER not in set(allowed_uses):
            if USER_FACT_USE_FOCUS_SELECTION in allowed_uses or USER_FACT_USE_RELATION_WEIGHT in allowed_uses:
                user_fact_focus_hint_ids = fact_ids

    if low_information or unknown_slots:
        _append_question(
            questions,
            kind=INTERNAL_QUESTION_KIND_WHAT_IS_UNKNOWN,
            answer_status=INTERNAL_QUESTION_UNANSWERED,
            inference_depth=1,
            surface_use=INTERNAL_QUESTION_SURFACE_QUESTION if low_information else INTERNAL_QUESTION_SURFACE_NOT_SURFACE,
            supporting_evidence_ids=all_evidence_ids[:2],
            unknown_slots=unknown_slots,
        )

    if not questions:
        unknown_slots = unknown_slots or [UNKNOWN_SLOT_EVENT, UNKNOWN_SLOT_TARGET]
        _append_question(
            questions,
            kind=INTERNAL_QUESTION_KIND_WHAT_IS_UNKNOWN,
            answer_status=INTERNAL_QUESTION_UNANSWERED,
            inference_depth=1,
            surface_use=INTERNAL_QUESTION_SURFACE_QUESTION,
            unknown_slots=unknown_slots,
        )
        low_information = True
        kind = OBSERVATION_REPLY_KIND_LOW_INFORMATION
        status = OBSERVATION_ELIGIBILITY_STATUS_LOW_INFORMATION

    inference_depths = [question.inference_depth for question in questions]
    observation_reply_meta = build_observation_reply_meta(
        observation_reply_kind=kind,
        eligibility_status=status,
        plan=plan,
        eligible_for_full_observation=not low_information,
        question_required=low_information,
        user_fact_grounding_mode=user_fact_mode,
        user_fact_allowed=bool(plan == "subscription" and facts_used),
        user_fact_may_hint=bool(plan == "subscription" and fact_ids),
        facts_used=facts_used,
        surface_disclosure_required=bool(user_fact_meta.get("surface_disclosure_required")),
        unknown_slots=unknown_slots,
        inference_depths=inference_depths,
        primary_reason="internal_question_layer_ready",
    )
    assert_observation_reply_meta_contract(observation_reply_meta)

    result = InternalQuestionSet(
        questions=tuple(questions),
        observation_reply_kind=kind,
        eligibility_status=status,
        eligible_for_full_observation=not low_information,
        question_required=low_information,
        unknown_slots=tuple(unknown_slots),
        user_fact_grounding_mode=user_fact_mode,
        plan=plan,
        facts_used=tuple(facts_used),
        user_fact_focus_hint_ids=tuple(user_fact_focus_hint_ids),
        surface_disclosure_required=bool(user_fact_meta.get("surface_disclosure_required")),
        allowed_user_fact_uses=tuple(allowed_uses),
        max_inference_depth_allowed=MAX_OBSERVATION_INFERENCE_DEPTH,
        overclaim_guard_passed=True,
        observation_reply_meta=observation_reply_meta,
        observation_structure_connection=dict(eligibility_meta.get("observation_structure_connection") or {}),
    )
    assert_internal_question_set_contract(result.as_meta())
    return result


def resolve_internal_question_layer(**kwargs: Any) -> InternalQuestionSet:
    return build_internal_question_set(**kwargs)


def build_emlis_ai_internal_question_set(**kwargs: Any) -> InternalQuestionSet:
    return build_internal_question_set(**kwargs)


def resolve_emlis_ai_internal_question_layer(**kwargs: Any) -> InternalQuestionSet:
    return build_internal_question_set(**kwargs)


def assert_internal_question_set_contract(
    value: Mapping[str, Any] | InternalQuestionSet,
    *,
    source: str = "internal_question_set",
) -> None:
    if isinstance(value, InternalQuestionSet):
        value = value.as_meta()
    if not isinstance(value, Mapping):
        raise ValueError(f"{source} must be a mapping")
    if _contains_text_payload_key(value):
        raise ValueError(f"{source} must remain meta-only and must not contain raw text/comment keys")
    for key in _FORBIDDEN_TRUE_FLAGS:
        if value.get(key) is True:
            raise ValueError(f"{source} violates fixed contract: {key}=true")

    kind = _clean(value.get("observation_reply_kind"))
    status = _clean(value.get("eligibility_status"))
    if kind not in {OBSERVATION_REPLY_KIND_ELIGIBLE, OBSERVATION_REPLY_KIND_LOW_INFORMATION}:
        raise ValueError(f"{source} has unsupported observation_reply_kind: {kind or '<empty>'}")
    if status not in {OBSERVATION_ELIGIBILITY_STATUS_ELIGIBLE, OBSERVATION_ELIGIBILITY_STATUS_LOW_INFORMATION}:
        raise ValueError(f"{source} has unsupported eligibility_status: {status or '<empty>'}")
    low_information = kind == OBSERVATION_REPLY_KIND_LOW_INFORMATION or status == OBSERVATION_ELIGIBILITY_STATUS_LOW_INFORMATION
    if low_information:
        if value.get("eligible_for_full_observation") is True:
            raise ValueError("low-information internal questions must not be full-observation eligible")
        if value.get("question_required") is not True:
            raise ValueError("low-information internal questions must require a question")
    else:
        if value.get("eligible_for_full_observation") is not True:
            raise ValueError("eligible internal questions must remain full-observation eligible")

    max_allowed = int(value.get("max_inference_depth_allowed") or 0)
    if max_allowed != MAX_OBSERVATION_INFERENCE_DEPTH:
        raise ValueError("max inference depth must remain 3")
    if value.get("overclaim_guard_passed") is not True:
        raise ValueError("internal question overclaim guard must pass")

    plan = _clean(value.get("plan")) or "free"
    if plan == "free" and value.get("facts_used"):
        raise ValueError("Free internal question set must not carry facts_used")

    questions = list(value.get("questions") or [])
    if not questions:
        raise ValueError(f"{source} must include at least one question")

    seen_ids: set[str] = set()
    has_current_answer = False
    has_unanswered_surface_question = False
    for index, question in enumerate(questions):
        if not isinstance(question, Mapping):
            raise ValueError(f"{source}.questions[{index}] must be a mapping")
        qid = _clean(question.get("question_id"))
        if not qid:
            raise ValueError(f"{source}.questions[{index}] missing question_id")
        if qid in seen_ids:
            raise ValueError(f"{source}.questions duplicate question_id: {qid}")
        seen_ids.add(qid)

        qkind = _clean(question.get("kind"))
        answer_status = _clean(question.get("answer_status"))
        surface_use = _clean(question.get("surface_use"))
        if qkind not in _ALLOWED_QUESTION_KINDS:
            raise ValueError(f"{source}.questions[{index}] has unsupported kind: {qkind}")
        if answer_status not in _ALLOWED_ANSWER_STATUSES:
            raise ValueError(f"{source}.questions[{index}] has unsupported answer_status: {answer_status}")
        if surface_use not in _ALLOWED_SURFACE_USES:
            raise ValueError(f"{source}.questions[{index}] has unsupported surface_use: {surface_use}")
        try:
            depth = int(question.get("inference_depth"))
        except (TypeError, ValueError):
            raise ValueError(f"{source}.questions[{index}] has invalid inference_depth") from None
        if depth < 1 or depth > MAX_OBSERVATION_INFERENCE_DEPTH:
            raise ValueError("inference depth must be within 1..3")
        if low_information and depth > 2:
            raise ValueError("low-information internal questions must not use depth 3")

        evidence_ids = _dedupe(question.get("supporting_evidence_ids"))
        fact_ids = _dedupe(question.get("supporting_user_fact_ids"))
        if answer_status == INTERNAL_QUESTION_ANSWERED_BY_CURRENT_INPUT:
            has_current_answer = True
            if not evidence_ids:
                raise ValueError("current-input answered question requires supporting_evidence_ids")
        if answer_status == INTERNAL_QUESTION_SUPPORTED_BY_USER_FACT:
            if plan == "free":
                raise ValueError("Free internal questions must not use user facts")
            if low_information:
                raise ValueError("low-information user facts may hint only and must not answer internal questions")
            if not fact_ids:
                raise ValueError("user-fact supported question requires supporting_user_fact_ids")
            if question.get("current_event_assertion_from_user_fact") is True:
                raise ValueError("user fact must not assert the current event")
            allowed_uses = set(_dedupe(question.get("allowed_user_fact_uses")))
            if USER_FACT_USE_INTERNAL_QUESTION_ANSWER not in allowed_uses:
                raise ValueError("user-fact supported question requires internal_question_answer use")
        if answer_status == INTERNAL_QUESTION_UNANSWERED:
            if question.get("answer_summary") is not None:
                raise ValueError("unanswered questions must not carry answer_summary")
            if low_information and qkind == INTERNAL_QUESTION_KIND_WHAT_IS_UNKNOWN and surface_use == INTERNAL_QUESTION_SURFACE_QUESTION:
                has_unanswered_surface_question = True
        if qkind == INTERNAL_QUESTION_KIND_WHAT_IS_UNKNOWN and answer_status != INTERNAL_QUESTION_UNANSWERED:
            raise ValueError("what_is_unknown must stay unanswered")

    if kind == OBSERVATION_REPLY_KIND_ELIGIBLE and not has_current_answer:
        raise ValueError("eligible internal question set requires a current-input answer")
    if low_information and not has_unanswered_surface_question:
        raise ValueError("low-information internal question set requires an unanswered surface question")
    if int(value.get("max_inference_depth_used") or 0) > MAX_OBSERVATION_INFERENCE_DEPTH:
        raise ValueError("max_inference_depth_used must stay within 3")

    reply_meta = value.get("observation_reply_meta") or {}
    if reply_meta:
        assert_observation_reply_meta_contract(reply_meta, source=f"{source}.observation_reply_meta")


def dump_internal_question_set(value: InternalQuestionSet | Mapping[str, Any]) -> str:
    meta = value.as_meta() if isinstance(value, InternalQuestionSet) else dict(value)
    assert_internal_question_set_contract(meta)
    return json.dumps(meta, ensure_ascii=False, sort_keys=True)


def dump_emlis_ai_internal_question_set(value: InternalQuestionSet | Mapping[str, Any]) -> str:
    return dump_internal_question_set(value)


__all__ = [
    "INTERNAL_QUESTION_LAYER_VERSION",
    "INTERNAL_QUESTION_LAYER_STEP",
    "INTERNAL_QUESTION_KIND_WHY_THIS_WORD",
    "INTERNAL_QUESTION_KIND_WHY_THIS_BURDEN",
    "INTERNAL_QUESTION_KIND_WHAT_RELATION",
    "INTERNAL_QUESTION_KIND_WHAT_IS_UNKNOWN",
    "INTERNAL_QUESTION_ANSWERED_BY_CURRENT_INPUT",
    "INTERNAL_QUESTION_SUPPORTED_BY_USER_FACT",
    "INTERNAL_QUESTION_UNANSWERED",
    "ANSWER_STATUS_ANSWERED_BY_CURRENT_INPUT",
    "ANSWER_STATUS_SUPPORTED_BY_USER_FACT",
    "ANSWER_STATUS_UNANSWERED",
    "INTERNAL_QUESTION_SURFACE_DIRECT",
    "INTERNAL_QUESTION_SURFACE_DISSOLVED",
    "INTERNAL_QUESTION_SURFACE_QUESTION",
    "INTERNAL_QUESTION_SURFACE_NOT_SURFACE",
    "SURFACE_USE_DIRECT",
    "SURFACE_USE_DISSOLVED",
    "SURFACE_USE_QUESTION",
    "SURFACE_USE_NOT_SURFACE",
    "InternalQuestion",
    "InternalQuestionSet",
    "build_internal_question_set",
    "resolve_internal_question_layer",
    "build_emlis_ai_internal_question_set",
    "resolve_emlis_ai_internal_question_layer",
    "assert_internal_question_set_contract",
    "dump_internal_question_set",
    "dump_emlis_ai_internal_question_set",
]
