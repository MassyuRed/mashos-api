# -*- coding: utf-8 -*-
from __future__ import annotations

"""Step 8 Low Information Observation Composer for EmlisAI.

This module adds the dedicated low-information observation composer branch.  It
is a normal observation branch selected by Step 2, not a fixed fallback and not a
Display Gate bypass.

The composer generates an internal ``body`` candidate made of 2-3 observation
sentences plus a question.  It deliberately does not write ``comment_text``, does
not alter the public ``observation_status`` enum, does not change API/RN/DB
contracts, and does not promote low-information input to an eligible observation
using user facts.
"""

from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass, field
import hashlib
import json
import re
from typing import Any, Final

from emlis_ai_internal_question_service import (
    INTERNAL_QUESTION_KIND_WHAT_IS_UNKNOWN,
    INTERNAL_QUESTION_SURFACE_QUESTION,
    build_internal_question_set,
)
from emlis_ai_observation_dictionary_loader import (
    CATEGORY_BURDEN_PHRASE,
    CATEGORY_FORBIDDEN_TEMPLATE_SIGNATURE,
    CATEGORY_HUMILITY_MARKER,
    CATEGORY_KNOWN_SCOPE_PHRASE,
    CATEGORY_QUESTION_ENDING,
    CATEGORY_RECEIVE_PHRASE,
    CATEGORY_UNKNOWN_SLOT_MARKER,
    select_observation_dictionary_entries,
)
from emlis_ai_observation_eligibility_service import route_observation_eligibility
from emlis_ai_observation_material_connector import build_material_focus_relation_connector
from emlis_ai_observation_reply_contract import (
    OBSERVATION_ELIGIBILITY_STATUS_LOW_INFORMATION,
    OBSERVATION_REPLY_KIND_LOW_INFORMATION,
    OBSERVATION_ROLE_LOW_INFO_KNOWN_SCOPE,
    OBSERVATION_ROLE_LOW_INFO_QUESTION,
    OBSERVATION_ROLE_LOW_INFO_RECEIVE,
    UNKNOWN_SLOT_CAUSE,
    UNKNOWN_SLOT_CURRENT_FEELING_TARGET,
    UNKNOWN_SLOT_DESIRED_DIRECTION,
    UNKNOWN_SLOT_EVENT,
    UNKNOWN_SLOT_RELATION,
    UNKNOWN_SLOT_TARGET,
    UNKNOWN_SLOT_TIME,
    USER_FACT_GROUNDING_MODE_DISABLED,
    USER_FACT_GROUNDING_MODE_EXPLICIT_REFERENCE,
    USER_FACT_GROUNDING_MODE_IMPLICIT_FOCUS,
    assert_observation_reply_meta_contract,
    build_observation_reply_meta,
)
from emlis_ai_observation_sentence_plan_roles import (
    OBSERVATION_SENTENCE_PLAN_ROLES_STEP,
    assert_observation_sentence_plan_roles_contract,
)
from emlis_ai_user_fact_grounding_boundary import resolve_user_fact_grounding_boundary

LOW_INFORMATION_OBSERVATION_COMPOSER_VERSION: Final = "emlis.low_information_observation_composer.v1"
LOW_INFORMATION_OBSERVATION_COMPOSER_STEP: Final = "Step8_Low_Information_Observation_Composer"
LOW_INFORMATION_OBSERVATION_BODY_SCHEMA_VERSION: Final = "emlis.low_information_observation_body.v1"

QUESTION_SURFACE_WHAT_HAPPENED: Final = "what_happened"
QUESTION_SURFACE_WHAT_CHANGED: Final = "what_changed"
QUESTION_SURFACE_WHICH_PART_FEELS_HEAVY: Final = "which_part_feels_heavy"
QUESTION_SURFACE_WHAT_IS_HARD_TO_SAY: Final = "what_is_hard_to_say"

_LINE_ROLE_OPENING: Final = "opening"
_LINE_ROLE_CORE: Final = "core"
_LINE_ROLE_CLOSING: Final = "closing"

_SPACE_RE: Final = re.compile(r"\s+")
_SENTENCE_SPLIT_RE: Final = re.compile(r"[。！？!?]+")
_FORBIDDEN_COMPLETE_TEMPLATE_RE: Final = re.compile(
    r"(Emlisです|Emlisでは観測できません|もっと詳しく教えてください|つらかったですね[。\s]*無理しないでくださいね|無理しないでくださいね|あなたは十分頑張っています)"
)
_PAST_REFERENCE_RE: Final = re.compile(r"(以前にも|前にも|過去にも|前回も)")
_EVENT_ASSERTION_RE: Final = re.compile(r"(同じことで疲れている|環境の件で疲れている|前と同じことで|今回も環境|あなたはいつも|しやすい人)")
_QUESTION_MARK_RE: Final = re.compile(r"(何がありましたか|何が起きたか|どの部分が重くなっていますか|どの部分が重くなっているか|何が変わりましたか|どこから言いにくくなっていますか|何を言いにくく感じていますか|どうしましたか)")
_HUMILITY_MARKER_RE: Final = re.compile(r"(ように見えます|かもしれません|まだ見えていません|まだ決められません|なさそうです)")
_KNOWN_SCOPE_RE: Final = re.compile(r"(言葉になる前の重さ|ここから見えているのは|軽く流せるものではなさそう|詳しい出来事まではまだ見えません|まだ詳しい出来事までは見えません|まだ詳細までは見えません)")

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
        "realized_text",
    }
)
_FORBIDDEN_TRUE_FLAGS: Final = frozenset(
    {
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
        "complete_sentence_template_used",
        "external_ai_used",
        "local_llm_used",
        "user_fact_may_promote_to_eligible",
        "promote_low_info_to_eligible",
        "assert_current_event_from_user_fact",
        "user_fact_used_for_current_event_assertion",
        "personality_tendency_allowed",
        "unsupported_assertion_allowed",
        "raw_input_included",
        "raw_text_included",
        "comment_text_included",
        "comment_text_body_included",
        "comment_text_generated",
    }
)
_ALLOWED_LINE_ROLES: Final = frozenset({_LINE_ROLE_OPENING, _LINE_ROLE_CORE, _LINE_ROLE_CLOSING})
_ALLOWED_OBSERVATION_ROLES: Final = frozenset(
    {OBSERVATION_ROLE_LOW_INFO_RECEIVE, OBSERVATION_ROLE_LOW_INFO_KNOWN_SCOPE, OBSERVATION_ROLE_LOW_INFO_QUESTION}
)


def _clean(value: Any, *, limit: int = 0) -> str:
    text = _SPACE_RE.sub(" ", str(value or "").replace("\u3000", " ").replace("\r", " ").replace("\n", " ")).strip()
    if limit > 0 and len(text) > limit:
        text = text[:limit].rstrip(" 、,。.!！?？")
    return text


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


def _contains_payload_key(value: Any) -> bool:
    if isinstance(value, Mapping):
        for key, item in value.items():
            if _clean(key) in _TEXT_PAYLOAD_KEYS:
                return True
            if _contains_payload_key(item):
                return True
        return False
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        return any(_contains_payload_key(item) for item in value)
    if hasattr(value, "__dict__"):
        return _contains_payload_key(vars(value))
    return False


def _current_input_text(current_input: Any) -> str:
    if isinstance(current_input, Mapping):
        return _clean("。".join(_clean(current_input.get(key)) for key in ("memo", "memo_action") if _clean(current_input.get(key))))
    return _clean(current_input)


def _body_sentence_count(body: str) -> int:
    return len([part for part in _SENTENCE_SPLIT_RE.split(_clean(body)) if _clean(part)])


def _ensure_sentence(fragment: str) -> str:
    text = _clean(fragment)
    if not text:
        return ""
    if text[-1] not in "。！？!?":
        text += "。"
    return text


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


def _select_first_material(
    *,
    category: str,
    evidence_roles: Iterable[str] | None = None,
    unknown_slots: Iterable[str] | None = None,
    default_surface: str,
) -> dict[str, Any]:
    entries = select_observation_dictionary_entries(
        category=category,
        reply_kind=OBSERVATION_REPLY_KIND_LOW_INFORMATION,
        evidence_roles=evidence_roles,
        unknown_slots=unknown_slots,
    )
    if entries:
        return dict(entries[0])
    return {
        "entry_id": f"fallback_fragment_{category}",
        "category": category,
        "surface": default_surface,
        "allowed_reply_kinds": [OBSERVATION_REPLY_KIND_LOW_INFORMATION],
        "requires_evidence_role": list(evidence_roles or ["current_input"]),
        "must_not_be_complete_sentence": True,
        "template_signature_weight": 0.0,
        "positive_material": True,
    }


def _select_forbidden_signatures() -> list[dict[str, Any]]:
    return select_observation_dictionary_entries(
        category=CATEGORY_FORBIDDEN_TEMPLATE_SIGNATURE,
        reply_kind=OBSERVATION_REPLY_KIND_LOW_INFORMATION,
        include_forbidden_signatures=True,
    )


def _question_surface_kind_for_slots(unknown_slots: Sequence[str]) -> str:
    slots = set(unknown_slots)
    # When the current input is globally under-specified, the event/cause slot
    # should remain the safest first question even if the router also marks
    # target or desired_direction as unknown.  Target/relation questions are
    # used only when those are the primary missing slots.
    if UNKNOWN_SLOT_EVENT in slots or UNKNOWN_SLOT_CAUSE in slots:
        return QUESTION_SURFACE_WHAT_HAPPENED
    if UNKNOWN_SLOT_TARGET in slots or UNKNOWN_SLOT_RELATION in slots:
        return QUESTION_SURFACE_WHICH_PART_FEELS_HEAVY
    if UNKNOWN_SLOT_DESIRED_DIRECTION in slots or UNKNOWN_SLOT_TIME in slots:
        return QUESTION_SURFACE_WHAT_CHANGED
    if UNKNOWN_SLOT_CURRENT_FEELING_TARGET in slots:
        return QUESTION_SURFACE_WHAT_IS_HARD_TO_SAY
    return QUESTION_SURFACE_WHAT_HAPPENED


def _question_surface_for_kind(kind: str, selected_entry: Mapping[str, Any]) -> str:
    surface = _clean(selected_entry.get("surface"))
    if surface:
        return surface
    if kind == QUESTION_SURFACE_WHICH_PART_FEELS_HEAVY:
        return "どの部分が重くなっていますか"
    if kind == QUESTION_SURFACE_WHAT_CHANGED:
        return "何が変わりましたか"
    if kind == QUESTION_SURFACE_WHAT_IS_HARD_TO_SAY:
        return "どこから言いにくくなっていますか"
    return "何がありましたか"


def _unknown_marker_for_slots(unknown_slots: Sequence[str]) -> str:
    slots = set(unknown_slots)
    if UNKNOWN_SLOT_TARGET in slots or UNKNOWN_SLOT_RELATION in slots:
        return "どの部分が重くなっているか"
    if UNKNOWN_SLOT_DESIRED_DIRECTION in slots:
        return "何が変わったのか"
    if UNKNOWN_SLOT_CURRENT_FEELING_TARGET in slots:
        return "どこから言いにくくなっているか"
    if UNKNOWN_SLOT_CAUSE in slots:
        return "何が負荷になったのか"
    return "何が起きたか"


def _line_hash(text: str, *, role: str) -> str:
    digest = hashlib.sha1(f"{role}:{text}".encode("utf-8")).hexdigest()[:10]
    return f"low_info_{role}_{digest}"


def _body_contains_raw_input(body: str, current_input: Any) -> bool:
    current_text = _current_input_text(current_input)
    if not current_text or len(current_text) > 40:
        return False
    return current_text in body


@dataclass(frozen=True)
class LowInformationObservationLine:
    line_id: str
    line_role: str
    observation_role: str
    text: str
    material_entry_ids: Sequence[str] = field(default_factory=tuple)
    supporting_evidence_ids: Sequence[str] = field(default_factory=tuple)
    unknown_slots: Sequence[str] = field(default_factory=tuple)
    question_surface_kind: str = ""

    def as_meta(self) -> dict[str, Any]:
        return {
            "version": LOW_INFORMATION_OBSERVATION_BODY_SCHEMA_VERSION,
            "line_id": self.line_id,
            "line_role": self.line_role,
            "observation_roles": [self.observation_role],
            "observation_reply_kind": OBSERVATION_REPLY_KIND_LOW_INFORMATION,
            "known_scope_only": self.observation_role != OBSERVATION_ROLE_LOW_INFO_QUESTION,
            "question_required": self.observation_role == OBSERVATION_ROLE_LOW_INFO_QUESTION,
            "question_surface_kind": self.question_surface_kind,
            "material_entry_ids": list(self.material_entry_ids),
            "supporting_evidence_ids": list(self.supporting_evidence_ids),
            "unknown_slots": list(self.unknown_slots),
            "raw_input_included": False,
            "raw_text_included": False,
            "comment_text_included": False,
        }


@dataclass(frozen=True)
class LowInformationObservationDraft:
    body: str
    lines: Sequence[LowInformationObservationLine]
    observation_reply_kind: str = OBSERVATION_REPLY_KIND_LOW_INFORMATION
    eligibility_status: str = OBSERVATION_ELIGIBILITY_STATUS_LOW_INFORMATION
    eligible_for_full_observation: bool = False
    question_required: bool = True
    unknown_slots: Sequence[str] = field(default_factory=tuple)
    observed_scope: Sequence[str] = field(default_factory=tuple)
    question_surface_kind: str = QUESTION_SURFACE_WHAT_HAPPENED
    user_fact_hint_mode: str = USER_FACT_GROUNDING_MODE_DISABLED
    plan: str = "free"
    facts_used: Sequence[Mapping[str, Any]] = field(default_factory=tuple)
    user_fact_focus_hint_ids: Sequence[str] = field(default_factory=tuple)
    surface_disclosure_required: bool = False
    known_fragment_evidence_ids: Sequence[str] = field(default_factory=tuple)
    internal_question_ids: Sequence[str] = field(default_factory=tuple)
    question_surface_internal_question_ids: Sequence[str] = field(default_factory=tuple)
    selected_material_entry_ids: Sequence[str] = field(default_factory=tuple)
    forbidden_template_signature_ids: Sequence[str] = field(default_factory=tuple)
    observation_reply_meta: Mapping[str, Any] = field(default_factory=dict)

    @property
    def version(self) -> str:
        return LOW_INFORMATION_OBSERVATION_COMPOSER_VERSION

    @property
    def step(self) -> str:
        return LOW_INFORMATION_OBSERVATION_COMPOSER_STEP

    def as_meta(self) -> dict[str, Any]:
        facts = _safe_fact_refs(self.facts_used) if self.plan == "subscription" else []
        meta: dict[str, Any] = {
            "version": LOW_INFORMATION_OBSERVATION_COMPOSER_VERSION,
            "schema_version": LOW_INFORMATION_OBSERVATION_COMPOSER_VERSION,
            "source_step": LOW_INFORMATION_OBSERVATION_COMPOSER_STEP,
            "step": LOW_INFORMATION_OBSERVATION_COMPOSER_STEP,
            "low_information_observation_composer_ready": True,
            "low_information_observation_branch_ready": True,
            "regular_branch_not_fallback": True,
            "observation_reply_kind": self.observation_reply_kind,
            "eligibility_status": self.eligibility_status,
            "eligible_for_full_observation": bool(self.eligible_for_full_observation),
            "question_required": bool(self.question_required),
            "body_non_empty": bool(_clean(self.body)),
            "body_sentence_count": _body_sentence_count(self.body),
            "body_line_count": len(self.lines),
            "line_metas": [line.as_meta() for line in self.lines],
            "line_roles": [line.line_role for line in self.lines],
            "sentence_plan_observation_roles": [line.observation_role for line in self.lines],
            "low_info_receive_present": any(line.observation_role == OBSERVATION_ROLE_LOW_INFO_RECEIVE for line in self.lines),
            "low_info_known_scope_present": any(line.observation_role == OBSERVATION_ROLE_LOW_INFO_KNOWN_SCOPE for line in self.lines),
            "low_info_question_present": any(line.observation_role == OBSERVATION_ROLE_LOW_INFO_QUESTION for line in self.lines),
            "contains_known_scope_observation": bool(_KNOWN_SCOPE_RE.search(self.body)),
            "contains_humility_marker": bool(_HUMILITY_MARKER_RE.search(self.body)),
            "contains_question": bool(_QUESTION_MARK_RE.search(self.body)),
            "question_not_only": _body_sentence_count(self.body) >= 2 and bool(_QUESTION_MARK_RE.search(self.body)),
            "unknown_slots": list(self.unknown_slots),
            "observed_scope": list(self.observed_scope),
            "question_surface_kind": self.question_surface_kind,
            "question_targets_unknown_slots": list(self.unknown_slots[:2]),
            "user_fact_hint_mode": self.user_fact_hint_mode,
            "user_fact_grounding_mode": self.user_fact_hint_mode,
            "plan": self.plan,
            "facts_used": facts,
            "user_fact_focus_hint_ids": list(self.user_fact_focus_hint_ids),
            "surface_disclosure_required": bool(self.surface_disclosure_required),
            "known_fragment_evidence_ids": list(self.known_fragment_evidence_ids),
            "internal_question_ids": list(self.internal_question_ids),
            "question_surface_internal_question_ids": list(self.question_surface_internal_question_ids),
            "selected_material_entry_ids": list(self.selected_material_entry_ids),
            "forbidden_template_signature_ids": list(self.forbidden_template_signature_ids),
            "observation_reply_meta": dict(self.observation_reply_meta or {}),
            "low_information_known_scope_only": True,
            "known_scope_only": True,
            "deep_relation_allowed": False,
            "relation_confidence_limited": True,
            "user_fact_may_hint": bool(self.plan == "subscription" and (facts or self.user_fact_focus_hint_ids)),
            "user_fact_may_promote_to_eligible": False,
            "must_not_promote_low_info_to_eligible": True,
            "must_not_assert_current_event_from_user_fact": True,
            "assert_current_event_from_user_fact": False,
            "user_fact_used_for_current_event_assertion": False,
            "personality_tendency_allowed": False,
            "unsupported_assertion_allowed": False,
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
            "completed_sentence_template_used": False,
            "external_ai_used": False,
            "local_llm_used": False,
        }
        assert_low_information_observation_composer_contract(self)
        return meta

    def as_payload(self) -> dict[str, Any]:
        """Return a Step-8 candidate payload for later Step 10 integration."""

        return {
            "version": LOW_INFORMATION_OBSERVATION_BODY_SCHEMA_VERSION,
            "observation_reply_kind": self.observation_reply_kind,
            "eligibility_status": self.eligibility_status,
            "body": self.body,
            "lines": [line.as_meta() for line in self.lines],
            "meta": self.as_meta(),
            "comment_text_generated": False,
            "public_status_extended": False,
            "api_route_changed": False,
            "db_physical_name_changed": False,
            "rn_visible_contract_changed": False,
        }


def _resolve_low_information_inputs(
    *,
    current_input: Any = None,
    eligibility_decision: Any = None,
    user_fact_grounding_decision: Any = None,
    internal_question_set: Any = None,
    material_connector: Any = None,
    subscription_tier: Any = None,
    capability: Any = None,
    user_facts: Any = None,
    source_bundle: Any = None,
    evidence_ledger: Any = None,
    observation_graph: Any = None,
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any], dict[str, Any]]:
    if eligibility_decision is None:
        eligibility_decision = route_observation_eligibility(
            current_input=current_input,
            subscription_tier=subscription_tier,
            capability=capability,
            user_facts=user_facts,
            evidence_ledger=evidence_ledger,
            observation_graph=observation_graph,
        )
    eligibility_meta = _meta(eligibility_decision)

    if user_fact_grounding_decision is None:
        user_fact_grounding_decision = resolve_user_fact_grounding_boundary(
            current_input=current_input,
            subscription_tier=subscription_tier,
            capability=capability,
            user_facts=user_facts,
            eligibility_decision=eligibility_meta,
            unknown_slots=eligibility_meta.get("unknown_slots"),
        )
    user_fact_meta = _meta(user_fact_grounding_decision)

    if internal_question_set is None:
        internal_question_set = build_internal_question_set(
            current_input=current_input,
            eligibility_decision=eligibility_meta,
            user_fact_grounding_decision=user_fact_meta,
            subscription_tier=subscription_tier,
            capability=capability,
            user_facts=user_facts,
            evidence_ledger=evidence_ledger,
            observation_graph=observation_graph,
        )
    internal_meta = _meta(internal_question_set)

    if material_connector is None:
        material_connector = build_material_focus_relation_connector(
            current_input=current_input,
            eligibility_decision=eligibility_meta,
            user_fact_grounding_decision=user_fact_meta,
            internal_question_set=internal_meta,
            subscription_tier=subscription_tier,
            capability=capability,
            user_facts=user_facts,
            evidence_ledger=evidence_ledger,
            observation_graph=observation_graph,
        )
    material_meta = _meta(material_connector)
    return eligibility_meta, user_fact_meta, internal_meta, material_meta


def _known_fragment_ids(eligibility_meta: Mapping[str, Any], material_meta: Mapping[str, Any]) -> list[str]:
    from_material = _dedupe(material_meta.get("known_fragment_evidence_ids"))
    if from_material:
        return from_material
    out: list[str] = []
    for item in eligibility_meta.get("known_fragments") or []:
        if isinstance(item, Mapping):
            evidence_id = _clean(item.get("evidence_span_id") or item.get("span_id") or item.get("id"))
            if evidence_id and evidence_id not in out:
                out.append(evidence_id)
    return out


def _question_internal_ids(internal_meta: Mapping[str, Any], material_meta: Mapping[str, Any]) -> list[str]:
    material_ids = _dedupe(material_meta.get("question_surface_internal_question_ids"))
    if material_ids:
        return material_ids
    out: list[str] = []
    for question in internal_meta.get("questions") or []:
        if not isinstance(question, Mapping):
            continue
        if question.get("kind") == INTERNAL_QUESTION_KIND_WHAT_IS_UNKNOWN or question.get("surface_use") == INTERNAL_QUESTION_SURFACE_QUESTION:
            qid = _clean(question.get("question_id"))
            if qid and qid not in out:
                out.append(qid)
    return out


def _build_lines(
    *,
    unknown_slots: Sequence[str],
    question_surface_kind: str,
    question_surface: str,
    plan: str,
    user_fact_mode: str,
    facts_used: Sequence[Mapping[str, Any]],
    surface_disclosure_required: bool,
    known_fragment_evidence_ids: Sequence[str],
) -> tuple[LowInformationObservationLine, ...]:
    receive = _select_first_material(
        category=CATEGORY_RECEIVE_PHRASE,
        evidence_roles=["current_input"],
        default_surface="今は",
    )
    burden = _select_first_material(
        category=CATEGORY_BURDEN_PHRASE,
        evidence_roles=["state"],
        default_surface="言葉になる前の重さ",
    )
    known_scope = _select_first_material(
        category=CATEGORY_KNOWN_SCOPE_PHRASE,
        evidence_roles=["unknown_slot"],
        unknown_slots=unknown_slots,
        default_surface="まだ詳しい出来事までは見えませんが",
    )
    humility = _select_first_material(
        category=CATEGORY_HUMILITY_MARKER,
        evidence_roles=["state", "unknown_slot"],
        unknown_slots=unknown_slots,
        default_surface="ように見えます",
    )
    unknown_marker = _select_first_material(
        category=CATEGORY_UNKNOWN_SLOT_MARKER,
        evidence_roles=["unknown_slot"],
        unknown_slots=unknown_slots,
        default_surface=_unknown_marker_for_slots(unknown_slots),
    )

    selected_ids = [
        _clean(item.get("entry_id"))
        for item in (receive, burden, known_scope, humility, unknown_marker)
        if _clean(item.get("entry_id"))
    ]

    receive_surface = _clean(receive.get("surface")) or "今は"
    burden_surface = _clean(burden.get("surface")) or "言葉になる前の重さ"
    humility_surface = _clean(humility.get("surface")) or "ように見えます"
    if humility_surface == "かもしれません":
        opening_text = f"{receive_surface}、{burden_surface}が先に出ている{humility_surface}。"
    else:
        opening_text = f"{receive_surface}、{burden_surface}が先に出ている{humility_surface}。"

    unknown_surface = _clean(unknown_marker.get("surface")) or _unknown_marker_for_slots(unknown_slots)
    if plan == "subscription" and facts_used and user_fact_mode == USER_FACT_GROUNDING_MODE_EXPLICIT_REFERENCE and surface_disclosure_required:
        known_scope_text = f"以前にも近い重さが残っていたことはありますが、今回{unknown_surface}まではまだ見えていません。"
    elif question_surface_kind == QUESTION_SURFACE_WHICH_PART_FEELS_HEAVY:
        known_scope_text = f"まだ詳しい出来事までは見えませんが、{unknown_surface}はまだ見えていません。"
    elif question_surface_kind == QUESTION_SURFACE_WHAT_CHANGED:
        known_scope_text = f"まだ詳細までは見えませんが、何が変わったのかはまだ決められません。"
    else:
        known_surface = _clean(known_scope.get("surface")) or "まだ詳しい出来事までは見えませんが"
        known_scope_text = f"{known_surface}、軽く流せるものではなさそうです。"

    question_text = _ensure_sentence(f"よければ、{question_surface}")

    lines = (
        LowInformationObservationLine(
            line_id=_line_hash(opening_text, role="receive"),
            line_role=_LINE_ROLE_OPENING,
            observation_role=OBSERVATION_ROLE_LOW_INFO_RECEIVE,
            text=opening_text,
            material_entry_ids=tuple(selected_ids[:3]),
            supporting_evidence_ids=tuple(known_fragment_evidence_ids[:2]),
            unknown_slots=tuple(),
        ),
        LowInformationObservationLine(
            line_id=_line_hash(known_scope_text, role="known_scope"),
            line_role=_LINE_ROLE_CORE,
            observation_role=OBSERVATION_ROLE_LOW_INFO_KNOWN_SCOPE,
            text=known_scope_text,
            material_entry_ids=tuple(selected_ids[2:]),
            supporting_evidence_ids=tuple(known_fragment_evidence_ids[:2]),
            unknown_slots=tuple(unknown_slots),
        ),
        LowInformationObservationLine(
            line_id=_line_hash(question_text, role="question"),
            line_role=_LINE_ROLE_CLOSING,
            observation_role=OBSERVATION_ROLE_LOW_INFO_QUESTION,
            text=question_text,
            material_entry_ids=tuple(selected_ids[-2:]),
            supporting_evidence_ids=tuple(known_fragment_evidence_ids[:2]),
            unknown_slots=tuple(unknown_slots),
            question_surface_kind=question_surface_kind,
        ),
    )
    return lines


def compose_low_information_observation(
    *,
    current_input: Any = None,
    eligibility_decision: Any = None,
    user_fact_grounding_decision: Any = None,
    internal_question_set: Any = None,
    material_connector: Any = None,
    subscription_tier: Any = None,
    capability: Any = None,
    user_facts: Any = None,
    source_bundle: Any = None,
    evidence_ledger: Any = None,
    observation_graph: Any = None,
    observation_dictionary: Any = None,  # reserved for future Step 9 dictionary injection; default loader is used for Step 8.
) -> LowInformationObservationDraft:
    """Build a low-information observation body candidate.

    The returned draft is meant for later Display / Repair integration.  It is
    not written into ``comment_text`` by this step.
    """

    del observation_dictionary  # Step 8 uses the default validated dictionary loader.
    eligibility_meta, user_fact_meta, internal_meta, material_meta = _resolve_low_information_inputs(
        current_input=current_input,
        eligibility_decision=eligibility_decision,
        user_fact_grounding_decision=user_fact_grounding_decision,
        internal_question_set=internal_question_set,
        material_connector=material_connector,
        subscription_tier=subscription_tier,
        capability=capability,
        user_facts=user_facts,
        source_bundle=source_bundle,
        evidence_ledger=evidence_ledger,
        observation_graph=observation_graph,
    )

    kind = _clean(material_meta.get("observation_reply_kind") or internal_meta.get("observation_reply_kind") or eligibility_meta.get("observation_reply_kind"))
    status = _clean(material_meta.get("eligibility_status") or internal_meta.get("eligibility_status") or eligibility_meta.get("eligibility_status"))
    low_information = kind == OBSERVATION_REPLY_KIND_LOW_INFORMATION or status == OBSERVATION_ELIGIBILITY_STATUS_LOW_INFORMATION
    if not low_information:
        raise ValueError("Step 8 Low Information Composer only accepts low-information routed inputs")

    unknown_slots = _dedupe(material_meta.get("unknown_slots") or internal_meta.get("unknown_slots") or eligibility_meta.get("unknown_slots"))
    if not unknown_slots:
        unknown_slots = [UNKNOWN_SLOT_EVENT]
    question_surface_kind = _question_surface_kind_for_slots(unknown_slots)
    question_entry = _select_first_material(
        category=CATEGORY_QUESTION_ENDING,
        evidence_roles=["unknown_slot"],
        unknown_slots=unknown_slots,
        default_surface=_question_surface_for_kind(question_surface_kind, {}),
    )
    question_surface = _question_surface_for_kind(question_surface_kind, question_entry)

    plan = _clean(material_meta.get("plan") or internal_meta.get("plan") or user_fact_meta.get("plan")) or "free"
    if plan != "subscription":
        plan = "free"
    facts_used = _safe_fact_refs(material_meta.get("facts_used") or internal_meta.get("facts_used") or user_fact_meta.get("facts_used")) if plan == "subscription" else []
    user_fact_mode = _clean(material_meta.get("user_fact_grounding_mode") or internal_meta.get("user_fact_grounding_mode") or user_fact_meta.get("mode")) or USER_FACT_GROUNDING_MODE_DISABLED
    if user_fact_mode not in {USER_FACT_GROUNDING_MODE_DISABLED, USER_FACT_GROUNDING_MODE_EXPLICIT_REFERENCE, USER_FACT_GROUNDING_MODE_IMPLICIT_FOCUS}:
        user_fact_mode = USER_FACT_GROUNDING_MODE_DISABLED
    surface_disclosure_required = bool(material_meta.get("surface_disclosure_required") or internal_meta.get("surface_disclosure_required") or user_fact_meta.get("surface_disclosure_required"))
    user_fact_focus_hint_ids = _dedupe(material_meta.get("user_fact_focus_hint_ids") or internal_meta.get("user_fact_focus_hint_ids") or _fact_ids(facts_used))
    known_ids = _known_fragment_ids(eligibility_meta, material_meta)
    internal_question_ids = _dedupe(material_meta.get("internal_question_ids") or (q.get("question_id") for q in internal_meta.get("questions") or [] if isinstance(q, Mapping)))
    question_internal_ids = _question_internal_ids(internal_meta, material_meta)

    lines = _build_lines(
        unknown_slots=unknown_slots,
        question_surface_kind=question_surface_kind,
        question_surface=question_surface,
        plan=plan,
        user_fact_mode=user_fact_mode,
        facts_used=facts_used,
        surface_disclosure_required=surface_disclosure_required,
        known_fragment_evidence_ids=known_ids,
    )
    body = "".join(line.text for line in lines)
    selected_material_ids = _dedupe(line_id for line in lines for line_id in line.material_entry_ids)
    if _clean(question_entry.get("entry_id")) and _clean(question_entry.get("entry_id")) not in selected_material_ids:
        selected_material_ids.append(_clean(question_entry.get("entry_id")))
    forbidden_signature_ids = _dedupe(entry.get("entry_id") for entry in _select_forbidden_signatures())

    observation_reply_meta = build_observation_reply_meta(
        observation_reply_kind=OBSERVATION_REPLY_KIND_LOW_INFORMATION,
        eligibility_status=OBSERVATION_ELIGIBILITY_STATUS_LOW_INFORMATION,
        plan=plan,
        eligible_for_full_observation=False,
        question_required=True,
        user_fact_grounding_mode=user_fact_mode,
        user_fact_allowed=bool(plan == "subscription" and facts_used),
        user_fact_may_hint=bool(plan == "subscription" and (facts_used or user_fact_focus_hint_ids)),
        facts_used=facts_used,
        surface_disclosure_required=surface_disclosure_required,
        unknown_slots=unknown_slots,
        inference_depths=[1, 1],
        primary_reason="low_information_observation_composer_ready",
    )
    assert_observation_reply_meta_contract(observation_reply_meta)

    draft = LowInformationObservationDraft(
        body=body,
        lines=lines,
        unknown_slots=tuple(unknown_slots),
        observed_scope=("emotion_weight", "language_before_detail", "unspecified_burden"),
        question_surface_kind=question_surface_kind,
        user_fact_hint_mode=user_fact_mode,
        plan=plan,
        facts_used=tuple(facts_used),
        user_fact_focus_hint_ids=tuple(user_fact_focus_hint_ids),
        surface_disclosure_required=surface_disclosure_required,
        known_fragment_evidence_ids=tuple(known_ids),
        internal_question_ids=tuple(internal_question_ids),
        question_surface_internal_question_ids=tuple(question_internal_ids),
        selected_material_entry_ids=tuple(selected_material_ids),
        forbidden_template_signature_ids=tuple(forbidden_signature_ids),
        observation_reply_meta=observation_reply_meta,
    )
    assert_low_information_observation_composer_contract(draft, current_input=current_input)
    return draft


def build_low_information_observation(**kwargs: Any) -> LowInformationObservationDraft:
    return compose_low_information_observation(**kwargs)


def compose_emlis_ai_low_information_observation(**kwargs: Any) -> LowInformationObservationDraft:
    return compose_low_information_observation(**kwargs)


def build_emlis_ai_low_information_observation(**kwargs: Any) -> LowInformationObservationDraft:
    return compose_low_information_observation(**kwargs)


def build_low_information_observation_composer_meta(**kwargs: Any) -> dict[str, Any]:
    return compose_low_information_observation(**kwargs).as_meta()


def build_low_information_observation_composer_contract_meta() -> dict[str, Any]:
    draft = compose_low_information_observation(current_input={"memo": "疲れた", "memo_action": ""}, subscription_tier="free")
    meta = draft.as_meta()
    meta.update(
        {
            "contract_only_fixture": True,
            "source_step": LOW_INFORMATION_OBSERVATION_COMPOSER_STEP,
            "step7_role_source_step": OBSERVATION_SENTENCE_PLAN_ROLES_STEP,
        }
    )
    assert_low_information_observation_composer_contract({**meta, "body": draft.body})
    return meta


def assert_low_information_observation_composer_contract(
    value: LowInformationObservationDraft | Mapping[str, Any],
    *,
    current_input: Any = None,
    source: str = "low_information_observation_composer",
) -> None:
    if isinstance(value, LowInformationObservationDraft):
        body = _clean(value.body)
        meta = {
            "body": body,
            **{
                key: item
                for key, item in value.as_meta_without_assert().items()
                if key != "body"
            },
        }
    elif isinstance(value, Mapping):
        meta = dict(value)
        body = _clean(meta.get("body") or meta.get("observation_body") or meta.get("candidate_body"))
    else:
        raise ValueError(f"{source} must be a LowInformationObservationDraft or mapping")

    if not body:
        raise ValueError(f"{source} must produce a non-empty body")
    if _FORBIDDEN_COMPLETE_TEMPLATE_RE.search(body):
        raise ValueError(f"{source} must not use fixed fallback or forbidden completed templates")
    if _EVENT_ASSERTION_RE.search(body):
        raise ValueError(f"{source} must not assert current event or personality from low information/user facts")
    if current_input is not None and _body_contains_raw_input(body, current_input):
        raise ValueError(f"{source} must not quote raw low-information input as its observation body")

    kind = _clean(meta.get("observation_reply_kind"))
    status = _clean(meta.get("eligibility_status"))
    if kind != OBSERVATION_REPLY_KIND_LOW_INFORMATION or status != OBSERVATION_ELIGIBILITY_STATUS_LOW_INFORMATION:
        raise ValueError(f"{source} must stay in low_information_observation branch")
    if meta.get("eligible_for_full_observation") is True:
        raise ValueError(f"{source} must not be eligible_for_full_observation")
    if meta.get("question_required") is not True:
        raise ValueError(f"{source} must require a question")
    if not meta.get("unknown_slots"):
        raise ValueError(f"{source} must carry unknown_slots")

    sentence_count = int(meta.get("body_sentence_count") or _body_sentence_count(body))
    if sentence_count < 2 or sentence_count > 3:
        raise ValueError(f"{source} body must be 2-3 sentences")
    if not _KNOWN_SCOPE_RE.search(body):
        raise ValueError(f"{source} body must include known-scope observation")
    if not _HUMILITY_MARKER_RE.search(body):
        raise ValueError(f"{source} body must include a humility marker")
    if not _QUESTION_MARK_RE.search(body):
        raise ValueError(f"{source} body must include a question for an unknown slot")
    if _QUESTION_MARK_RE.fullmatch(body.strip("。！？!?")):
        raise ValueError(f"{source} must not return question-only text")

    roles = _dedupe(meta.get("sentence_plan_observation_roles"))
    if not set(roles).issuperset(_ALLOWED_OBSERVATION_ROLES):
        raise ValueError(f"{source} must include low_info receive / known_scope / question roles")
    line_roles = set(_dedupe(meta.get("line_roles")))
    if line_roles and not line_roles.issubset(_ALLOWED_LINE_ROLES):
        raise ValueError(f"{source} must preserve existing public line_role enum")

    plan = _clean(meta.get("plan")) or "free"
    if plan == "free" and meta.get("facts_used"):
        raise ValueError(f"{source} must not use user facts for Free")
    if plan == "subscription":
        mode = _clean(meta.get("user_fact_hint_mode") or meta.get("user_fact_grounding_mode"))
        if mode == USER_FACT_GROUNDING_MODE_IMPLICIT_FOCUS and _PAST_REFERENCE_RE.search(body):
            raise ValueError(f"{source} implicit user fact mode must not surface past references")
    for flag in _FORBIDDEN_TRUE_FLAGS:
        if meta.get(flag) is True:
            raise ValueError(f"{source} violates fixed contract: {flag}=true")
    if meta.get("must_not_promote_low_info_to_eligible") is not True:
        raise ValueError(f"{source} must explicitly forbid low-info promotion")
    if meta.get("must_not_assert_current_event_from_user_fact") is not True:
        raise ValueError(f"{source} must explicitly forbid current event assertion from user facts")

    # Nested meta remains meta-only.  The top-level mapping may carry generated
    # body for Step 8 candidate validation, but nested contract objects must not
    # carry raw input or comment_text payload keys.
    nested_meta = dict(meta)
    for key in ("body", "observation_body", "candidate_body"):
        nested_meta.pop(key, None)
    if _contains_payload_key(nested_meta):
        raise ValueError(f"{source} nested meta must not contain raw input/comment payload keys")


def _draft_as_meta_without_assert(self: LowInformationObservationDraft) -> dict[str, Any]:
    facts = _safe_fact_refs(self.facts_used) if self.plan == "subscription" else []
    return {
        "version": LOW_INFORMATION_OBSERVATION_COMPOSER_VERSION,
        "schema_version": LOW_INFORMATION_OBSERVATION_COMPOSER_VERSION,
        "source_step": LOW_INFORMATION_OBSERVATION_COMPOSER_STEP,
        "step": LOW_INFORMATION_OBSERVATION_COMPOSER_STEP,
        "low_information_observation_composer_ready": True,
        "low_information_observation_branch_ready": True,
        "regular_branch_not_fallback": True,
        "observation_reply_kind": self.observation_reply_kind,
        "eligibility_status": self.eligibility_status,
        "eligible_for_full_observation": bool(self.eligible_for_full_observation),
        "question_required": bool(self.question_required),
        "body_non_empty": bool(_clean(self.body)),
        "body_sentence_count": _body_sentence_count(self.body),
        "body_line_count": len(self.lines),
        "line_metas": [line.as_meta() for line in self.lines],
        "line_roles": [line.line_role for line in self.lines],
        "sentence_plan_observation_roles": [line.observation_role for line in self.lines],
        "low_info_receive_present": any(line.observation_role == OBSERVATION_ROLE_LOW_INFO_RECEIVE for line in self.lines),
        "low_info_known_scope_present": any(line.observation_role == OBSERVATION_ROLE_LOW_INFO_KNOWN_SCOPE for line in self.lines),
        "low_info_question_present": any(line.observation_role == OBSERVATION_ROLE_LOW_INFO_QUESTION for line in self.lines),
        "contains_known_scope_observation": bool(_KNOWN_SCOPE_RE.search(self.body)),
        "contains_humility_marker": bool(_HUMILITY_MARKER_RE.search(self.body)),
        "contains_question": bool(_QUESTION_MARK_RE.search(self.body)),
        "question_not_only": _body_sentence_count(self.body) >= 2 and bool(_QUESTION_MARK_RE.search(self.body)),
        "unknown_slots": list(self.unknown_slots),
        "observed_scope": list(self.observed_scope),
        "question_surface_kind": self.question_surface_kind,
        "question_targets_unknown_slots": list(self.unknown_slots[:2]),
        "user_fact_hint_mode": self.user_fact_hint_mode,
        "user_fact_grounding_mode": self.user_fact_hint_mode,
        "plan": self.plan,
        "facts_used": facts,
        "user_fact_focus_hint_ids": list(self.user_fact_focus_hint_ids),
        "surface_disclosure_required": bool(self.surface_disclosure_required),
        "known_fragment_evidence_ids": list(self.known_fragment_evidence_ids),
        "internal_question_ids": list(self.internal_question_ids),
        "question_surface_internal_question_ids": list(self.question_surface_internal_question_ids),
        "selected_material_entry_ids": list(self.selected_material_entry_ids),
        "forbidden_template_signature_ids": list(self.forbidden_template_signature_ids),
        "observation_reply_meta": dict(self.observation_reply_meta or {}),
        "low_information_known_scope_only": True,
        "known_scope_only": True,
        "deep_relation_allowed": False,
        "relation_confidence_limited": True,
        "user_fact_may_hint": bool(self.plan == "subscription" and (facts or self.user_fact_focus_hint_ids)),
        "user_fact_may_promote_to_eligible": False,
        "must_not_promote_low_info_to_eligible": True,
        "must_not_assert_current_event_from_user_fact": True,
        "assert_current_event_from_user_fact": False,
        "user_fact_used_for_current_event_assertion": False,
        "personality_tendency_allowed": False,
        "unsupported_assertion_allowed": False,
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
        "completed_sentence_template_used": False,
        "external_ai_used": False,
        "local_llm_used": False,
    }


# Keep the public dataclass frozen while avoiding recursion in the assertion
# helper.  The monkey-patched method is intentionally private to this module.
LowInformationObservationDraft.as_meta_without_assert = _draft_as_meta_without_assert  # type: ignore[attr-defined]


def dump_low_information_observation(value: LowInformationObservationDraft | Mapping[str, Any]) -> str:
    if isinstance(value, LowInformationObservationDraft):
        meta = value.as_meta_without_assert()  # type: ignore[attr-defined]
    else:
        meta = dict(value)
        assert_low_information_observation_composer_contract(meta)
    # Generated body is intentionally redacted from dumps.  Step 8 may generate a
    # body, but debug dumps must not leak user input, user facts, or comment_text.
    meta.pop("body", None)
    return json.dumps(meta, ensure_ascii=False, sort_keys=True)

# Design-document friendly aliases. Existing constants above remain the canonical
# names used by this module.
OBSERVED_SCOPE_EMOTION_WEIGHT: Final = "emotion_weight"
OBSERVED_SCOPE_LANGUAGE_BEFORE_DETAIL: Final = "language_before_detail"
OBSERVED_SCOPE_UNSPECIFIED_BURDEN: Final = "unspecified_burden"
QUESTION_SURFACE_KIND_WHAT_HAPPENED: Final = QUESTION_SURFACE_WHAT_HAPPENED
QUESTION_SURFACE_KIND_WHAT_CHANGED: Final = QUESTION_SURFACE_WHAT_CHANGED
QUESTION_SURFACE_KIND_WHICH_PART_FEELS_HEAVY: Final = QUESTION_SURFACE_WHICH_PART_FEELS_HEAVY
QUESTION_SURFACE_KIND_WHAT_IS_HARD_TO_SAY: Final = QUESTION_SURFACE_WHAT_IS_HARD_TO_SAY

def dump_low_information_observation_composition(value: LowInformationObservationDraft | Mapping[str, Any]) -> str:
    return dump_low_information_observation(value)

def dump_low_information_observation_plan(value: LowInformationObservationDraft | Mapping[str, Any]) -> str:
    return dump_low_information_observation(value)


__all__ = [
    "LOW_INFORMATION_OBSERVATION_BODY_SCHEMA_VERSION",
    "LOW_INFORMATION_OBSERVATION_COMPOSER_STEP",
    "LOW_INFORMATION_OBSERVATION_COMPOSER_VERSION",
    "QUESTION_SURFACE_WHAT_CHANGED",
    "QUESTION_SURFACE_WHAT_HAPPENED",
    "QUESTION_SURFACE_WHAT_IS_HARD_TO_SAY",
    "QUESTION_SURFACE_WHICH_PART_FEELS_HEAVY",
    "LowInformationObservationDraft",
    "LowInformationObservationLine",
    "assert_low_information_observation_composer_contract",
    "build_emlis_ai_low_information_observation",
    "build_low_information_observation",
    "build_low_information_observation_composer_contract_meta",
    "build_low_information_observation_composer_meta",
    "compose_emlis_ai_low_information_observation",
    "compose_low_information_observation",
    "OBSERVED_SCOPE_EMOTION_WEIGHT",
    "OBSERVED_SCOPE_LANGUAGE_BEFORE_DETAIL",
    "OBSERVED_SCOPE_UNSPECIFIED_BURDEN",
    "QUESTION_SURFACE_KIND_WHAT_HAPPENED",
    "QUESTION_SURFACE_KIND_WHAT_CHANGED",
    "QUESTION_SURFACE_KIND_WHICH_PART_FEELS_HEAVY",
    "QUESTION_SURFACE_KIND_WHAT_IS_HARD_TO_SAY",
    "dump_low_information_observation_composition",
    "dump_low_information_observation_plan",
    "dump_low_information_observation",
]
