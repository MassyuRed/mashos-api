# -*- coding: utf-8 -*-
from __future__ import annotations

"""Step 9 Observation Surface Realizer / Tone Update for EmlisAI.

This module connects observation reply roles to a surface/tone/template-guard
contract without wiring the result into ``ReplyEnvelope.comment_text``.  Step 10
will decide whether the realized candidate is promoted through Display Gate.

Scope of this step:

* accept observation roles from Step 7;
* keep low-information observations as 2-3 sentence observation + question;
* select low-information question endings from ``unknown_slots``;
* require eligible state verbalization to be relation-connected;
* apply tone/template guard metadata without changing public status, API route,
  DB physical names, RN display contract, or external-AI usage.
"""

from collections import Counter
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass, field
import hashlib
import json
import re
from typing import Any, Final

from emlis_ai_complete_composer_types import CompleteSentencePlanLine, CompleteSentencePlanV2
from emlis_ai_complete_sentence_planner import build_complete_sentence_plan_v2
from emlis_ai_complete_surface_realizer_anti_template import build_surface_realizer_anti_template_report
from emlis_ai_low_information_observation_composer import (
    LowInformationObservationDraft,
    compose_low_information_observation,
    format_low_information_question_prompt,
)
from emlis_ai_observation_dictionary_loader import (
    CATEGORY_FORBIDDEN_TEMPLATE_SIGNATURE,
    CATEGORY_QUESTION_ENDING,
    select_observation_dictionary_entries,
)
from emlis_ai_observation_reply_contract import (
    OBSERVATION_ELIGIBILITY_STATUS_ELIGIBLE,
    OBSERVATION_ELIGIBILITY_STATUS_LOW_INFORMATION,
    OBSERVATION_REPLY_KIND_ELIGIBLE,
    OBSERVATION_REPLY_KIND_LOW_INFORMATION,
    OBSERVATION_ROLE_COMPANION_CLOSE,
    OBSERVATION_ROLE_EMPATHY,
    OBSERVATION_ROLE_INPUT_ARRANGEMENT,
    OBSERVATION_ROLE_LOW_INFO_KNOWN_SCOPE,
    OBSERVATION_ROLE_LOW_INFO_QUESTION,
    OBSERVATION_ROLE_LOW_INFO_RECEIVE,
    OBSERVATION_ROLE_STATE_VERBALIZATION,
    UNKNOWN_SLOT_CAUSE,
    UNKNOWN_SLOT_CURRENT_FEELING_TARGET,
    UNKNOWN_SLOT_DESIRED_DIRECTION,
    UNKNOWN_SLOT_EVENT,
    UNKNOWN_SLOT_RELATION,
    UNKNOWN_SLOT_TARGET,
    UNKNOWN_SLOT_TIME,
    USER_FACT_GROUNDING_MODE_DISABLED,
)

OBSERVATION_SURFACE_REALIZER_TONE_VERSION: Final = "emlis.observation_surface_realizer_tone.v1"
OBSERVATION_SURFACE_REALIZER_TONE_SCHEMA_VERSION: Final = "emlis.observation_surface_realization.v1"
OBSERVATION_SURFACE_REALIZER_TONE_STEP: Final = "Step9_Surface_Realizer_Tone_Update"

OBSERVATION_TONE_POLICY_VERSION: Final = "emlis.observation_tone_policy.v1"
OBSERVATION_TEMPLATE_GUARD_VERSION: Final = "emlis.observation_template_guard.v1"
OBSERVATION_SURFACE_LINE_SCHEMA_VERSION: Final = "emlis.observation_surface_line.v1"

QUESTION_SURFACE_KIND_WHAT_HAPPENED: Final = "what_happened"
QUESTION_SURFACE_KIND_WHAT_CHANGED: Final = "what_changed"
QUESTION_SURFACE_KIND_WHICH_PART_FEELS_HEAVY: Final = "which_part_feels_heavy"
QUESTION_SURFACE_KIND_WHAT_IS_HARD_TO_SAY: Final = "what_is_hard_to_say"
QUESTION_SURFACE_WHAT_HAPPENED: Final = QUESTION_SURFACE_KIND_WHAT_HAPPENED
QUESTION_SURFACE_WHAT_CHANGED: Final = QUESTION_SURFACE_KIND_WHAT_CHANGED
QUESTION_SURFACE_WHICH_PART_FEELS_HEAVY: Final = QUESTION_SURFACE_KIND_WHICH_PART_FEELS_HEAVY
QUESTION_SURFACE_WHAT_IS_HARD_TO_SAY: Final = QUESTION_SURFACE_KIND_WHAT_IS_HARD_TO_SAY
OBSERVATION_SURFACE_REALIZER_VERSION: Final = OBSERVATION_SURFACE_REALIZER_TONE_VERSION
OBSERVATION_SURFACE_REALIZER_STEP: Final = OBSERVATION_SURFACE_REALIZER_TONE_STEP

_LINE_ROLE_OPENING: Final = "opening"
_LINE_ROLE_CORE: Final = "core"
_LINE_ROLE_RELATION: Final = "relation"
_LINE_ROLE_CLOSING: Final = "closing"
_ALLOWED_LINE_ROLES: Final = frozenset({_LINE_ROLE_OPENING, _LINE_ROLE_CORE, _LINE_ROLE_RELATION, _LINE_ROLE_CLOSING})

_ALLOWED_OBSERVATION_ROLES: Final = frozenset(
    {
        OBSERVATION_ROLE_EMPATHY,
        OBSERVATION_ROLE_INPUT_ARRANGEMENT,
        OBSERVATION_ROLE_STATE_VERBALIZATION,
        OBSERVATION_ROLE_COMPANION_CLOSE,
        OBSERVATION_ROLE_LOW_INFO_RECEIVE,
        OBSERVATION_ROLE_LOW_INFO_KNOWN_SCOPE,
        OBSERVATION_ROLE_LOW_INFO_QUESTION,
    }
)
_ALLOWED_REPLY_KINDS: Final = frozenset({OBSERVATION_REPLY_KIND_ELIGIBLE, OBSERVATION_REPLY_KIND_LOW_INFORMATION})
_ALLOWED_ELIGIBILITY_STATUSES: Final = frozenset({OBSERVATION_ELIGIBILITY_STATUS_ELIGIBLE, OBSERVATION_ELIGIBILITY_STATUS_LOW_INFORMATION})
_ALLOWED_QUESTION_SURFACE_KINDS: Final = frozenset(
    {
        QUESTION_SURFACE_KIND_WHAT_HAPPENED,
        QUESTION_SURFACE_KIND_WHAT_CHANGED,
        QUESTION_SURFACE_KIND_WHICH_PART_FEELS_HEAVY,
        QUESTION_SURFACE_KIND_WHAT_IS_HARD_TO_SAY,
    }
)
_ALLOWED_UNKNOWN_SLOTS: Final = frozenset(
    {
        UNKNOWN_SLOT_EVENT,
        UNKNOWN_SLOT_TARGET,
        UNKNOWN_SLOT_CAUSE,
        UNKNOWN_SLOT_RELATION,
        UNKNOWN_SLOT_TIME,
        UNKNOWN_SLOT_DESIRED_DIRECTION,
        UNKNOWN_SLOT_CURRENT_FEELING_TARGET,
    }
)

_SPACE_RE: Final = re.compile(r"\s+")
_SENTENCE_SPLIT_RE: Final = re.compile(r"[。！？!?]+")
_QUESTION_RE: Final = re.compile(
    r"(詳しく残せそうなら、(?:何があったか|どのあたりが重くなっているか|何が変わったのか|どこから言いにくくなっているか|何について大丈夫か気になっているのか)残してみませんか|残してみませんか|何がありましたか|何が起きたか|どの部分が重くなっていますか|何が変わりましたか|どこから言いにくくなっていますか|何を言いにくく感じていますか|どうしましたか|何について大丈夫か気になっていますか)"
)
_LEGACY_LOW_INFORMATION_PROMPT_RE: Final = re.compile(r"(よければ、|何がありましたか[。！？!?]?)")
_HUMILITY_RE: Final = re.compile(r"(ように見えます|かもしれません|まだ見えていません|まだ決められません|なさそうです)")
_FORBIDDEN_COMPLETE_TEMPLATE_RE: Final = re.compile(
    r"(Emlisです|Emlisでは観測できません|もっと詳しく教えてください|つらかったですね[。\s]*無理しないでくださいね|無理しないでくださいね|あなたは十分頑張っています|よければ、何がありましたか|何がありましたか)"
)
_UNSUPPORTED_EVENT_ASSERTION_RE: Final = re.compile(
    r"(前と同じことで疲れている|環境の件で疲れている|あなたはいつも|しやすい人|診断|治療|症状|トラウマ|障害|ADHD|うつ|鬱|PTSD)"
)
_ACTION_INSTRUCTION_RE: Final = re.compile(r"(してください|しましょう|するべき|しなければ|行動しましょう|変えましょう|まずは.+やってみ)")
_GENERIC_COMFORT_RE: Final = re.compile(r"(よくあること|誰でも|大丈夫です|もう大丈夫|必ず良く|安心してください|一緒に見ます|無理しないでくださいね)")
_PAST_REF_RE: Final = re.compile(r"(以前にも|前にも|過去にも)")

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
        "public_comment_text",
        "candidate_comment_text",
        "reply_text",
        "replyText",
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
        "role_completed_sentence_template_used",
        "input_specific_template_used",
        "external_ai_used",
        "local_llm_used",
        "comment_text_generated",
        "comment_text_key_written",
        "comment_text_publicly_assigned",
        "public_comment_text_assigned",
        "user_fact_may_promote_to_eligible",
        "promote_low_info_to_eligible",
        "assert_current_event_from_user_fact",
        "user_fact_used_for_current_event_assertion",
        "unsupported_assertion_allowed",
    }
)

_TONE_BY_ROLE: Final = {
    OBSERVATION_ROLE_EMPATHY: {
        "tone_policy_key": "warm_receive_not_comfort_only",
        "temperature_key": "low_warm",
        "tone_guard_keys": ["over_empathy", "generic_comfort"],
    },
    OBSERVATION_ROLE_INPUT_ARRANGEMENT: {
        "tone_policy_key": "input_arrangement_grounded",
        "temperature_key": "steady_warm",
        "tone_guard_keys": ["raw_echo", "template"],
    },
    OBSERVATION_ROLE_STATE_VERBALIZATION: {
        "tone_policy_key": "relation_connected_state_verbalization",
        "temperature_key": "steady_warm",
        "tone_guard_keys": ["overclaim", "diagnostic_tone", "action_instruction"],
    },
    OBSERVATION_ROLE_COMPANION_CLOSE: {
        "tone_policy_key": "companion_close_no_instruction",
        "temperature_key": "low_warm",
        "tone_guard_keys": ["advice_like", "generic_comfort"],
    },
    OBSERVATION_ROLE_LOW_INFO_RECEIVE: {
        "tone_policy_key": "low_info_receive_without_pressure",
        "temperature_key": "low_warm",
        "tone_guard_keys": ["generic_comfort", "question_only"],
    },
    OBSERVATION_ROLE_LOW_INFO_KNOWN_SCOPE: {
        "tone_policy_key": "low_info_known_scope_humble",
        "temperature_key": "calm_low",
        "tone_guard_keys": ["overclaim", "unsupported_event_assertion"],
    },
    OBSERVATION_ROLE_LOW_INFO_QUESTION: {
        "tone_policy_key": "low_info_question_gentle",
        "temperature_key": "calm_low",
        "tone_guard_keys": ["question_only", "pushy_question"],
    },
}


def _clean(value: Any, *, limit: int = 0) -> str:
    text = _SPACE_RE.sub(" ", str(value or "").replace("\u3000", " ").replace("\r", " ").replace("\n", " ")).strip()
    if limit > 0 and len(text) > limit:
        text = text[:limit].rstrip(" 、,。.!！?？")
    return text


def _clean_token(value: Any) -> str:
    return re.sub(r"[^0-9a-zA-Z_\-.]+", "_", str(value or "").strip().lower()).strip("_")


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


def _body_sentence_count(body: str) -> int:
    return len([part for part in _SENTENCE_SPLIT_RE.split(_clean(body)) if _clean(part)])


def _ensure_sentence(fragment: str) -> str:
    text = _clean(fragment)
    if not text:
        return ""
    if text[-1] not in "。！？!?":
        text += "。"
    return text


def _normalize_question_surface_kind(kind: Any, unknown_slots: Sequence[str]) -> str:
    value = _clean(kind)
    if value in _ALLOWED_QUESTION_SURFACE_KINDS:
        return value
    slots = set(unknown_slots)
    if UNKNOWN_SLOT_EVENT in slots or UNKNOWN_SLOT_CAUSE in slots:
        return QUESTION_SURFACE_KIND_WHAT_HAPPENED
    if UNKNOWN_SLOT_TARGET in slots or UNKNOWN_SLOT_RELATION in slots:
        return QUESTION_SURFACE_KIND_WHICH_PART_FEELS_HEAVY
    if UNKNOWN_SLOT_DESIRED_DIRECTION in slots or UNKNOWN_SLOT_TIME in slots:
        return QUESTION_SURFACE_KIND_WHAT_CHANGED
    if UNKNOWN_SLOT_CURRENT_FEELING_TARGET in slots:
        return QUESTION_SURFACE_KIND_WHAT_IS_HARD_TO_SAY
    return QUESTION_SURFACE_KIND_WHAT_HAPPENED


def _question_entry_for_kind(kind: str, unknown_slots: Sequence[str]) -> dict[str, Any]:
    entries = select_observation_dictionary_entries(
        category=CATEGORY_QUESTION_ENDING,
        reply_kind=OBSERVATION_REPLY_KIND_LOW_INFORMATION,
        evidence_roles=["unknown_slot"],
        unknown_slots=unknown_slots,
    )
    if kind == QUESTION_SURFACE_KIND_WHICH_PART_FEELS_HEAVY:
        wanted = {UNKNOWN_SLOT_TARGET, UNKNOWN_SLOT_RELATION}
    elif kind == QUESTION_SURFACE_KIND_WHAT_CHANGED:
        wanted = {UNKNOWN_SLOT_DESIRED_DIRECTION, UNKNOWN_SLOT_TIME}
    elif kind == QUESTION_SURFACE_KIND_WHAT_IS_HARD_TO_SAY:
        wanted = {UNKNOWN_SLOT_CURRENT_FEELING_TARGET}
    else:
        wanted = {UNKNOWN_SLOT_EVENT, UNKNOWN_SLOT_CAUSE}
    for entry in entries:
        entry_slots = set(_dedupe(entry.get("unknown_slots")))
        if entry_slots & wanted:
            return dict(entry)
    fallback_surface = {
        QUESTION_SURFACE_KIND_WHICH_PART_FEELS_HEAVY: "どのあたりが重くなっているか",
        QUESTION_SURFACE_KIND_WHAT_CHANGED: "何が変わったのか",
        QUESTION_SURFACE_KIND_WHAT_IS_HARD_TO_SAY: "どこから言いにくくなっているか",
    }.get(kind, "何があったか")
    return {
        "entry_id": f"fallback_question_ending_{kind}",
        "category": CATEGORY_QUESTION_ENDING,
        "surface": fallback_surface,
        "allowed_reply_kinds": [OBSERVATION_REPLY_KIND_LOW_INFORMATION],
        "requires_evidence_role": ["unknown_slot"],
        "must_not_be_complete_sentence": True,
        "template_signature_weight": 0.0,
        "positive_material": True,
        "unknown_slots": list(unknown_slots),
    }



def select_observation_question_ending(
    unknown_slots: Sequence[str] | None = None,
    *,
    question_surface_kind: str = "",
) -> dict[str, Any]:
    """Select the low-information question ending from unknown slots.

    This is a Step 9 surface helper only.  It returns dictionary metadata for
    composer/surface tests and does not write ReplyEnvelope/comment_text.
    """
    slots = tuple(slot for slot in _dedupe(unknown_slots) if slot in _ALLOWED_UNKNOWN_SLOTS)
    kind = _normalize_question_surface_kind(question_surface_kind, slots)
    entry = _question_entry_for_kind(kind, slots)
    return {
        "version": OBSERVATION_SURFACE_REALIZER_TONE_VERSION,
        "schema_version": OBSERVATION_SURFACE_REALIZER_TONE_SCHEMA_VERSION,
        "source_step": OBSERVATION_SURFACE_REALIZER_TONE_STEP,
        "question_surface_kind": kind,
        "question_ending_entry_id": _clean(entry.get("entry_id")),
        "question_ending_surface": _clean(entry.get("surface")),
        "unknown_slots": list(slots),
        "must_not_be_complete_sentence": bool(entry.get("must_not_be_complete_sentence", True)),
        "completed_sentence_template_used": False,
        "fixed_sentence_template_used": False,
        "input_specific_template_used": False,
        "comment_text_generated": False,
        "comment_text_key_written": False,
        "public_comment_text_assigned": False,
        "raw_input_included": False,
        "raw_text_included": False,
    }

def _forbidden_signature_ids(reply_kind: str) -> list[str]:
    entries = select_observation_dictionary_entries(
        category=CATEGORY_FORBIDDEN_TEMPLATE_SIGNATURE,
        reply_kind=reply_kind,
        include_forbidden_signatures=True,
    )
    return [str(entry.get("entry_id")) for entry in entries if entry.get("entry_id")]


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


def _json_safe(value: Any) -> Any:
    if isinstance(value, (str, int, float, bool)) or value is None:
        return value
    if isinstance(value, Mapping):
        return {str(key): _json_safe(item) for key, item in value.items() if _clean(key) not in _TEXT_PAYLOAD_KEYS}
    if isinstance(value, (list, tuple, set)):
        return [_json_safe(item) for item in value]
    if hasattr(value, "as_meta") and callable(value.as_meta):
        result = value.as_meta()
        return _json_safe(result if isinstance(result, Mapping) else {})
    if hasattr(value, "__dict__"):
        return _json_safe(vars(value))
    return str(value)


def _source_meta(value: Any) -> dict[str, Any]:
    if value is None:
        return {}
    if isinstance(value, Mapping):
        return dict(value)
    as_meta = getattr(value, "as_meta", None)
    if callable(as_meta):
        meta = as_meta()
        return dict(meta) if isinstance(meta, Mapping) else {}
    return {}


def _line_hash(text: str, role: str) -> str:
    digest = hashlib.sha1(f"{role}:{text}".encode("utf-8")).hexdigest()[:10]
    return f"obs_surface_{role}_{digest}"


def _line_skeleton(line_role: str, observation_roles: Sequence[str], question_surface_kind: str, line_role_merge: Sequence[str]) -> str:
    role_key = "+".join(_dedupe(observation_roles)) or "none"
    merge_key = "+".join(_dedupe(line_role_merge)) or "none"
    question_key = question_surface_kind or "none"
    return f"{line_role}:{role_key}:{question_key}:{merge_key}"


def _tone_for_roles(observation_roles: Sequence[str]) -> dict[str, Any]:
    roles = _dedupe(observation_roles)
    primary = roles[0] if roles else OBSERVATION_ROLE_INPUT_ARRANGEMENT
    base = dict(_TONE_BY_ROLE.get(primary) or _TONE_BY_ROLE[OBSERVATION_ROLE_INPUT_ARRANGEMENT])
    guard_keys: list[str] = []
    for role in roles or [primary]:
        for key in (_TONE_BY_ROLE.get(role) or {}).get("tone_guard_keys", []):
            if key not in guard_keys:
                guard_keys.append(key)
    base["tone_guard_keys"] = guard_keys or list(base.get("tone_guard_keys") or [])
    return base


def _tone_guard_report(*, body: str, observation_roles: Sequence[str], reply_kind: str) -> dict[str, Any]:
    roles = set(_dedupe(observation_roles))
    low_info = reply_kind == OBSERVATION_REPLY_KIND_LOW_INFORMATION
    eligible = reply_kind == OBSERVATION_REPLY_KIND_ELIGIBLE
    reasons: list[str] = []
    if _FORBIDDEN_COMPLETE_TEMPLATE_RE.search(body):
        reasons.append("forbidden_completed_template")
    if _UNSUPPORTED_EVENT_ASSERTION_RE.search(body):
        reasons.append("unsupported_event_or_diagnostic_assertion")
    if _ACTION_INSTRUCTION_RE.search(body):
        reasons.append("advice_like_instruction")
    if _GENERIC_COMFORT_RE.search(body):
        reasons.append("generic_comfort_or_over_empathy")
    if low_info and _LEGACY_LOW_INFORMATION_PROMPT_RE.search(body):
        reasons.append("legacy_low_information_question_wording")
    if low_info:
        if OBSERVATION_ROLE_LOW_INFO_KNOWN_SCOPE not in roles:
            reasons.append("low_info_known_scope_missing")
        if OBSERVATION_ROLE_LOW_INFO_QUESTION not in roles:
            reasons.append("low_info_question_missing")
        if not _QUESTION_RE.search(body):
            reasons.append("low_info_question_surface_missing")
        if not _HUMILITY_RE.search(body):
            reasons.append("low_info_humility_marker_missing")
    if eligible:
        if OBSERVATION_ROLE_INPUT_ARRANGEMENT not in roles and OBSERVATION_ROLE_STATE_VERBALIZATION not in roles:
            reasons.append("eligible_observation_role_missing")
        if roles and roles.issubset({OBSERVATION_ROLE_EMPATHY, OBSERVATION_ROLE_COMPANION_CLOSE}):
            reasons.append("empathy_only")
    return {
        "version": OBSERVATION_TONE_POLICY_VERSION,
        "source_step": OBSERVATION_SURFACE_REALIZER_TONE_STEP,
        "tone_policy_applied": True,
        "tone_is_surface_constraint_not_post_decoration": True,
        "meaning_added_by_tone_policy": False,
        "observation_roles": sorted(roles),
        "reply_kind": reply_kind,
        "major_reasons": reasons,
        "major_count": len(reasons),
        "tone_guard_passed": not reasons,
        "empathy_only_detected": "empathy_only" in reasons,
        "generic_comfort_detected": "generic_comfort_or_over_empathy" in reasons,
        "advice_like_detected": "advice_like_instruction" in reasons,
        "diagnostic_tone_detected": "unsupported_event_or_diagnostic_assertion" in reasons,
        "comment_text_generated": False,
        "raw_input_included": False,
        "raw_text_included": False,
    }


def _template_guard_report(
    *,
    body: str,
    lines: Sequence["ObservationSurfaceLine"],
    reply_kind: str,
    forbidden_template_signature_ids: Sequence[str],
) -> dict[str, Any]:
    skeletons = [line.template_skeleton_key for line in lines]
    counts = Counter(skeletons)
    repeat_count = sum(max(0, count - 1) for count in counts.values())
    forbidden_hits: list[str] = []
    if _FORBIDDEN_COMPLETE_TEMPLATE_RE.search(body):
        forbidden_hits.append("completed_template_text")
    question_only = _body_sentence_count(body) <= 1 and bool(_QUESTION_RE.search(body))
    if question_only:
        forbidden_hits.append("question_only")
    anti_template_rows = [line.surface_signature for line in lines]
    anti_template_report = build_surface_realizer_anti_template_report(anti_template_rows)
    guard_passed = not forbidden_hits and repeat_count == 0 and not anti_template_report.get("anti_template_major_detected")
    return {
        "version": OBSERVATION_TEMPLATE_GUARD_VERSION,
        "source_step": OBSERVATION_SURFACE_REALIZER_TONE_STEP,
        "template_guard_applied": True,
        "completion_sentence_template_used": False,
        "role_completed_sentence_template_used": False,
        "input_specific_template_used": False,
        "fixed_sentence_template_used": False,
        "surface_skeleton_keys": skeletons,
        "surface_skeleton_repeat_count": repeat_count,
        "same_skeleton_repeated": repeat_count > 0,
        "question_only_detected": question_only,
        "forbidden_template_signature_ids": list(forbidden_template_signature_ids),
        "forbidden_template_hits": forbidden_hits,
        "surface_realizer_anti_template_report": anti_template_report,
        "template_guard_passed": guard_passed,
        "reply_kind": reply_kind,
        "comment_text_generated": False,
        "raw_input_included": False,
        "raw_text_included": False,
    }


def _coerce_sentence_plan(value: CompleteSentencePlanV2 | Mapping[str, Any] | None) -> CompleteSentencePlanV2 | None:
    if isinstance(value, CompleteSentencePlanV2):
        return value
    if isinstance(value, Mapping):
        return CompleteSentencePlanV2(
            plan_id=value.get("plan_id") or "observation_surface_sentence_plan",
            sentence_budget=value.get("sentence_budget") or value.get("planned_sentence_count") or 2,
            coverage_group=value.get("coverage_group") or value.get("coverage_scope") or "observation_reply",
            sentence_plans=value.get("sentence_plans") or value.get("lines") or (),
            meta=value.get("meta") or {},
        )
    return None


def _line_roles_from_meta(line: CompleteSentencePlanLine | Mapping[str, Any]) -> tuple[str, ...]:
    meta = line.meta if isinstance(line, CompleteSentencePlanLine) else line.get("meta") if isinstance(line, Mapping) else {}
    roles = _dedupe((meta or {}).get("observation_roles"))
    if roles:
        return tuple(role for role in roles if role in _ALLOWED_OBSERVATION_ROLES)
    if isinstance(line, CompleteSentencePlanLine):
        line_role = line.line_role
    elif isinstance(line, Mapping):
        line_role = _clean(line.get("line_role") or line.get("role"))
    else:
        line_role = "core"
    if line_role == _LINE_ROLE_OPENING:
        return (OBSERVATION_ROLE_EMPATHY, OBSERVATION_ROLE_INPUT_ARRANGEMENT)
    if line_role == _LINE_ROLE_RELATION:
        return (OBSERVATION_ROLE_STATE_VERBALIZATION,)
    if line_role == _LINE_ROLE_CLOSING:
        return (OBSERVATION_ROLE_COMPANION_CLOSE,)
    return (OBSERVATION_ROLE_INPUT_ARRANGEMENT,)


def _safe_source_line_meta(line: CompleteSentencePlanLine | Mapping[str, Any]) -> dict[str, Any]:
    if isinstance(line, CompleteSentencePlanLine):
        meta = line.as_meta()
    elif isinstance(line, Mapping):
        meta = dict(line)
    else:
        meta = {}
    safe = _json_safe(meta)
    return safe if isinstance(safe, dict) else {}


@dataclass(frozen=True)
class ObservationSurfaceLine:
    line_id: str
    line_role: str
    observation_roles: Sequence[str]
    surface_text: str
    relation_type: str = "center"
    question_surface_kind: str = ""
    question_ending_entry_id: str = ""
    unknown_slots: Sequence[str] = field(default_factory=tuple)
    material_entry_ids: Sequence[str] = field(default_factory=tuple)
    supporting_evidence_ids: Sequence[str] = field(default_factory=tuple)
    tone_policy_key: str = "observe_without_overclaim"
    temperature_key: str = "steady_warm"
    tone_guard_keys: Sequence[str] = field(default_factory=tuple)
    template_skeleton_key: str = ""
    surface_signature: Mapping[str, Any] = field(default_factory=dict)
    source_line_meta: Mapping[str, Any] = field(default_factory=dict)
    line_role_merge: Sequence[str] = field(default_factory=tuple)

    def __post_init__(self) -> None:
        roles = _dedupe(self.observation_roles)
        valid_roles = [role for role in roles if role in _ALLOWED_OBSERVATION_ROLES]
        line_role = _clean(self.line_role) or _LINE_ROLE_CORE
        object.__setattr__(self, "line_id", _clean_token(self.line_id) or _line_hash(self.surface_text, line_role))
        object.__setattr__(self, "line_role", line_role if line_role in _ALLOWED_LINE_ROLES else _LINE_ROLE_CORE)
        object.__setattr__(self, "observation_roles", tuple(valid_roles))
        object.__setattr__(self, "surface_text", _ensure_sentence(self.surface_text))
        object.__setattr__(self, "relation_type", _clean_token(self.relation_type) or "center")
        object.__setattr__(self, "question_surface_kind", _clean(self.question_surface_kind))
        object.__setattr__(self, "question_ending_entry_id", _clean(self.question_ending_entry_id))
        object.__setattr__(self, "unknown_slots", tuple(slot for slot in _dedupe(self.unknown_slots) if slot in _ALLOWED_UNKNOWN_SLOTS))
        object.__setattr__(self, "material_entry_ids", tuple(_dedupe(self.material_entry_ids)))
        object.__setattr__(self, "supporting_evidence_ids", tuple(_dedupe(self.supporting_evidence_ids)))
        object.__setattr__(self, "tone_policy_key", _clean_token(self.tone_policy_key) or "observe_without_overclaim")
        object.__setattr__(self, "temperature_key", _clean_token(self.temperature_key) or "steady_warm")
        object.__setattr__(self, "tone_guard_keys", tuple(_dedupe(self.tone_guard_keys)))
        skeleton = _clean(self.template_skeleton_key) or _line_skeleton(line_role, valid_roles, self.question_surface_kind, self.line_role_merge)
        object.__setattr__(self, "template_skeleton_key", skeleton)
        object.__setattr__(self, "surface_signature", _json_safe(self.surface_signature) if isinstance(_json_safe(self.surface_signature), Mapping) else {})
        object.__setattr__(self, "source_line_meta", _json_safe(self.source_line_meta) if isinstance(_json_safe(self.source_line_meta), Mapping) else {})
        object.__setattr__(self, "line_role_merge", tuple(_dedupe(self.line_role_merge)))

    def as_meta(self, *, include_surface_text: bool = False) -> dict[str, Any]:
        meta: dict[str, Any] = {
            "version": OBSERVATION_SURFACE_LINE_SCHEMA_VERSION,
            "line_id": self.line_id,
            "line_role": self.line_role,
            "observation_roles": list(self.observation_roles),
            "relation_type": self.relation_type,
            "question_surface_kind": self.question_surface_kind,
            "question_ending_entry_id": self.question_ending_entry_id,
            "unknown_slots": list(self.unknown_slots),
            "material_entry_ids": list(self.material_entry_ids),
            "supporting_evidence_ids": list(self.supporting_evidence_ids),
            "tone_policy_key": self.tone_policy_key,
            "temperature_key": self.temperature_key,
            "tone_guard_keys": list(self.tone_guard_keys),
            "template_skeleton_key": self.template_skeleton_key,
            "surface_signature": dict(self.surface_signature),
            "source_line_meta": dict(self.source_line_meta),
            "line_role_merge": list(self.line_role_merge),
            "surface_text_present": bool(self.surface_text),
            "surface_text_length": len(self.surface_text),
            "raw_input_included": False,
            "raw_text_included": False,
            "comment_text_included": False,
        }
        if include_surface_text:
            meta["surface_text"] = self.surface_text
        return meta


@dataclass(frozen=True)
class ObservationSurfaceRealization:
    body: str
    lines: Sequence[ObservationSurfaceLine]
    observation_reply_kind: str
    eligibility_status: str
    eligible_for_full_observation: bool
    question_required: bool = False
    unknown_slots: Sequence[str] = field(default_factory=tuple)
    question_surface_kind: str = ""
    question_ending_entry_id: str = ""
    user_fact_grounding_mode: str = USER_FACT_GROUNDING_MODE_DISABLED
    facts_used: Sequence[Mapping[str, Any]] = field(default_factory=tuple)
    surface_disclosure_required: bool = False
    tone_guard_report: Mapping[str, Any] = field(default_factory=dict)
    template_guard_report: Mapping[str, Any] = field(default_factory=dict)
    source_meta: Mapping[str, Any] = field(default_factory=dict)

    @property
    def version(self) -> str:
        return OBSERVATION_SURFACE_REALIZER_TONE_VERSION

    @property
    def step(self) -> str:
        return OBSERVATION_SURFACE_REALIZER_TONE_STEP

    @property
    def observation_roles(self) -> list[str]:
        roles: list[str] = []
        for line in self.lines:
            for role in line.observation_roles:
                if role not in roles:
                    roles.append(role)
        return roles

    def as_meta(self, *, include_surface_text: bool = False) -> dict[str, Any]:
        roles = self.observation_roles
        line_metas = [line.as_meta(include_surface_text=include_surface_text) for line in self.lines]
        low_info = self.observation_reply_kind == OBSERVATION_REPLY_KIND_LOW_INFORMATION
        eligible = self.observation_reply_kind == OBSERVATION_REPLY_KIND_ELIGIBLE
        meta: dict[str, Any] = {
            "version": OBSERVATION_SURFACE_REALIZER_TONE_VERSION,
            "schema_version": OBSERVATION_SURFACE_REALIZER_TONE_SCHEMA_VERSION,
            "source_step": OBSERVATION_SURFACE_REALIZER_TONE_STEP,
            "step": OBSERVATION_SURFACE_REALIZER_TONE_STEP,
            "observation_surface_realizer_tone_ready": True,
            "observation_roles_supported": True,
            "low_information_roles_supported": True,
            "eligible_roles_supported": True,
            "observation_reply_kind": self.observation_reply_kind,
            "eligibility_status": self.eligibility_status,
            "eligible_for_full_observation": bool(self.eligible_for_full_observation),
            "question_required": bool(self.question_required),
            "body_non_empty": bool(_clean(self.body)),
            "body_sentence_count": _body_sentence_count(self.body),
            "body_line_count": len(self.lines),
            "line_metas": line_metas,
            "line_roles": [line.line_role for line in self.lines],
            "sentence_plan_observation_roles": roles,
            "unknown_slots": list(self.unknown_slots),
            "question_surface_kind": self.question_surface_kind,
            "question_ending_entry_id": self.question_ending_entry_id,
            "question_ending_selected_by_unknown_slot": low_info and bool(self.question_ending_entry_id),
            "low_info_receive_present": OBSERVATION_ROLE_LOW_INFO_RECEIVE in roles,
            "low_info_known_scope_present": OBSERVATION_ROLE_LOW_INFO_KNOWN_SCOPE in roles,
            "low_info_question_present": OBSERVATION_ROLE_LOW_INFO_QUESTION in roles,
            "contains_humility_marker": bool(_HUMILITY_RE.search(self.body)),
            "contains_question": bool(_QUESTION_RE.search(self.body)),
            "question_not_only": _body_sentence_count(self.body) >= 2 and bool(_QUESTION_RE.search(self.body)),
            "eligible_state_verbalization_present": OBSERVATION_ROLE_STATE_VERBALIZATION in roles,
            "eligible_state_verbalization_relation_connected": bool(
                eligible
                and any(
                    OBSERVATION_ROLE_STATE_VERBALIZATION in line.observation_roles
                    and line.line_role in {_LINE_ROLE_CORE, _LINE_ROLE_RELATION}
                    and _clean(line.relation_type)
                    for line in self.lines
                )
            ),
            "eligible_input_arrangement_present": OBSERVATION_ROLE_INPUT_ARRANGEMENT in roles,
            "empathy_only_detected": bool((self.tone_guard_report or {}).get("empathy_only_detected")),
            "tone_policy_version": OBSERVATION_TONE_POLICY_VERSION,
            "tone_policy_applied": True,
            "tone_guard_report": dict(self.tone_guard_report),
            "tone_guard_passed": bool((self.tone_guard_report or {}).get("tone_guard_passed", True)),
            "template_guard_version": OBSERVATION_TEMPLATE_GUARD_VERSION,
            "template_guard_report": dict(self.template_guard_report),
            "template_guard_passed": bool((self.template_guard_report or {}).get("template_guard_passed", True)),
            "surface_skeleton_repeat_count": int((self.template_guard_report or {}).get("surface_skeleton_repeat_count") or 0),
            "completion_sentence_template_used": False,
            "role_completed_sentence_template_used": False,
            "input_specific_template_used": False,
            "fixed_sentence_template_used": False,
            "surface_disclosure_required": bool(self.surface_disclosure_required),
            "user_fact_grounding_mode": self.user_fact_grounding_mode,
            "facts_used": _json_safe(self.facts_used),
            "source_meta": _json_safe(self.source_meta),
            "surface_text_internal_only": not include_surface_text,
            "comment_text_generated": False,
            "comment_text_key_written": False,
            "comment_text_publicly_assigned": False,
            "public_comment_text_assigned": False,
            "display_gate_relaxed": False,
            "reader_gate_relaxed": False,
            "grounding_gate_relaxed": False,
            "template_gate_relaxed": False,
            "gate_relaxed": False,
            "public_status_extended": False,
            "observation_status_enum_extended": False,
            "api_route_changed": False,
            "db_physical_name_changed": False,
            "public_response_key_change": False,
            "rn_visible_contract_changed": False,
            "rn_visible_title_changed": False,
            "external_ai_used": False,
            "local_llm_used": False,
            "raw_input_included": False,
            "raw_text_included": False,
        }
        if include_surface_text:
            meta["realized_text"] = self.body
        return meta


def _low_information_lines_from_draft(draft: LowInformationObservationDraft) -> tuple[ObservationSurfaceLine, ...]:
    draft_meta = draft.as_meta()
    unknown_slots = _dedupe(draft_meta.get("unknown_slots"))
    question_surface_kind = _normalize_question_surface_kind(draft_meta.get("question_surface_kind"), unknown_slots)
    question_entry = _question_entry_for_kind(question_surface_kind, unknown_slots)
    question_surface = _clean(question_entry.get("surface")) or "何があったか"
    safe_anchor_kind = _clean(draft_meta.get("safe_anchor_surface_kind"))
    lines: list[ObservationSurfaceLine] = []
    for item in draft.lines:
        line_meta = item.as_meta()
        roles = _dedupe(line_meta.get("observation_roles"))
        role = roles[0] if roles else OBSERVATION_ROLE_LOW_INFO_KNOWN_SCOPE
        text = item.text
        q_kind = ""
        q_entry_id = ""
        material_ids = _dedupe(line_meta.get("material_entry_ids"))
        if role == OBSERVATION_ROLE_LOW_INFO_QUESTION:
            if _QUESTION_RE.search(text) and not _LEGACY_LOW_INFORMATION_PROMPT_RE.search(text):
                text = _ensure_sentence(text)
            else:
                text = format_low_information_question_prompt(
                    question_surface,
                    safe_anchor_kind=safe_anchor_kind,
                )
            q_kind = question_surface_kind
            q_entry_id = _clean(question_entry.get("entry_id"))
            if q_entry_id and q_entry_id not in material_ids:
                material_ids.append(q_entry_id)
        tone = _tone_for_roles(roles)
        skeleton = _line_skeleton(item.line_role, roles, q_kind, [])
        signature = {
            "version": OBSERVATION_TEMPLATE_GUARD_VERSION,
            "line_role": item.line_role,
            "observation_role_key": role,
            "observation_roles": roles,
            "connector_key": f"low_info_{role}",
            "predicate_key": f"low_info_{role}",
            "ending_key": q_kind if q_kind else "humble_observation",
            "role_phrase_key": role,
            "question_surface_kind": q_kind,
            "template_skeleton_key": skeleton,
            "raw_input_included": False,
        }
        lines.append(
            ObservationSurfaceLine(
                line_id=item.line_id,
                line_role=item.line_role,
                observation_roles=roles,
                surface_text=text,
                relation_type="low_information_known_scope" if role != OBSERVATION_ROLE_LOW_INFO_QUESTION else "low_information_question",
                question_surface_kind=q_kind,
                question_ending_entry_id=q_entry_id,
                unknown_slots=unknown_slots if role == OBSERVATION_ROLE_LOW_INFO_QUESTION else line_meta.get("unknown_slots") or (),
                material_entry_ids=material_ids,
                supporting_evidence_ids=line_meta.get("supporting_evidence_ids") or (),
                tone_policy_key=tone["tone_policy_key"],
                temperature_key=tone["temperature_key"],
                tone_guard_keys=tone["tone_guard_keys"],
                template_skeleton_key=skeleton,
                surface_signature=signature,
                source_line_meta=line_meta,
            )
        )
    return tuple(lines)


def realize_low_information_observation_surface(
    draft: LowInformationObservationDraft | Mapping[str, Any] | None = None,
    *,
    current_input: Any = None,
    **composer_kwargs: Any,
) -> ObservationSurfaceRealization:
    if not isinstance(draft, LowInformationObservationDraft):
        if isinstance(draft, Mapping):
            # Mapping input is diagnostic-only; build a fresh draft unless tests pass
            # an actual Step8 dataclass.  This keeps raw text maps out of Step9.
            composer_kwargs = {**composer_kwargs, "eligibility_decision": draft}
        draft = compose_low_information_observation(current_input=current_input, **composer_kwargs)
    draft_meta = draft.as_meta()
    lines = _low_information_lines_from_draft(draft)
    body = "".join(line.surface_text for line in lines)
    roles: list[str] = []
    for line in lines:
        roles.extend(line.observation_roles)
    forbidden_ids = _forbidden_signature_ids(OBSERVATION_REPLY_KIND_LOW_INFORMATION)
    tone_report = _tone_guard_report(body=body, observation_roles=roles, reply_kind=OBSERVATION_REPLY_KIND_LOW_INFORMATION)
    template_report = _template_guard_report(body=body, lines=lines, reply_kind=OBSERVATION_REPLY_KIND_LOW_INFORMATION, forbidden_template_signature_ids=forbidden_ids)
    realization = ObservationSurfaceRealization(
        body=body,
        lines=lines,
        observation_reply_kind=OBSERVATION_REPLY_KIND_LOW_INFORMATION,
        eligibility_status=OBSERVATION_ELIGIBILITY_STATUS_LOW_INFORMATION,
        eligible_for_full_observation=False,
        question_required=True,
        unknown_slots=tuple(_dedupe(draft_meta.get("unknown_slots"))),
        question_surface_kind=_normalize_question_surface_kind(draft_meta.get("question_surface_kind"), _dedupe(draft_meta.get("unknown_slots"))),
        question_ending_entry_id=next((line.question_ending_entry_id for line in lines if line.question_ending_entry_id), ""),
        user_fact_grounding_mode=_clean(draft_meta.get("user_fact_grounding_mode")) or USER_FACT_GROUNDING_MODE_DISABLED,
        facts_used=tuple(draft_meta.get("facts_used") or ()),
        surface_disclosure_required=bool(draft_meta.get("surface_disclosure_required")),
        tone_guard_report=tone_report,
        template_guard_report=template_report,
        source_meta={
            "source_step": draft_meta.get("source_step"),
            "low_information_observation_composer_ready": bool(draft_meta.get("low_information_observation_composer_ready")),
            "low_information_specificity_plan": dict(draft_meta.get("low_information_specificity_plan") or {}),
            "low_information_specificity_used": bool(draft_meta.get("low_information_specificity_used")),
            "step6_low_information_specificity_ready": bool(draft_meta.get("step6_low_information_specificity_ready")),
            "safe_anchor_count": int(draft_meta.get("safe_anchor_count") or 0),
            "uses_safe_anchor": bool(draft_meta.get("uses_safe_anchor")),
            "safe_anchor_role": _clean(draft_meta.get("safe_anchor_role")) or "none",
            "safe_anchor_surface_kind": _clean(draft_meta.get("safe_anchor_surface_kind")) or "none",
            "comment_text_generated": False,
            "raw_input_included": False,
        },
    )
    assert_observation_surface_realizer_tone_contract(realization)
    return realization


def _eligible_line_text(line: CompleteSentencePlanLine, roles: Sequence[str], index: int) -> str:
    relation = _clean(line.relation_type) or "center"
    if OBSERVATION_ROLE_STATE_VERBALIZATION in roles:
        if relation in {"coexistence", "contrast"}:
            return "入力の中では、違う向きが同じ場所に残っているように見えます。"
        if relation in {"pressure", "limit"}:
            return "その関係の中で、負荷が軽く流せない形で残っているように見えます。"
        if relation in {"approach_avoidance", "desire_fear"}:
            return "近づきたい向きと止まる向きが、同じ線上に残っているように見えます。"
        return "入力内の言葉同士の関係が、ひとつの重さとして残っているように見えます。"
    if OBSERVATION_ROLE_INPUT_ARRANGEMENT in roles:
        return "今の入力では、見えている状態と詰まりが同じ流れの中に置かれています。"
    if OBSERVATION_ROLE_EMPATHY in roles:
        return "まず、ここまで言葉にするだけでも軽くない状態として受け取っています。"
    if OBSERVATION_ROLE_COMPANION_CLOSE in roles:
        return "ここでは結論を急がず、残っている形をそのまま見ています。"
    return f"根拠のある範囲が観測文の中に置かれています。"


def realize_eligible_observation_surface(
    sentence_plan: CompleteSentencePlanV2 | Mapping[str, Any] | None = None,
    *,
    current_input: Any = None,
    **planner_kwargs: Any,
) -> ObservationSurfaceRealization:
    del current_input  # Step 9 does not inspect raw input directly.
    plan = _coerce_sentence_plan(sentence_plan)
    if plan is None:
        plan = build_complete_sentence_plan_v2(**planner_kwargs)
    lines: list[ObservationSurfaceLine] = []
    for index, source_line in enumerate(plan.sentence_plans):
        roles = _line_roles_from_meta(source_line)
        tone = _tone_for_roles(roles)
        source_meta = _safe_source_line_meta(source_line)
        relation = _clean(source_line.relation_type) or "center"
        q_kind = ""
        merge = _dedupe((source_meta.get("meta") or {}).get("surface_role_merge") if isinstance(source_meta.get("meta"), Mapping) else [])
        skeleton = _line_skeleton(source_line.line_role, roles, q_kind, merge)
        text = _eligible_line_text(source_line, roles, index)
        signature = {
            "version": OBSERVATION_TEMPLATE_GUARD_VERSION,
            "line_role": source_line.line_role,
            "observation_roles": list(roles),
            "connector_key": f"eligible_{source_line.line_role}_{relation}",
            "predicate_key": "state_verbalization_relation" if OBSERVATION_ROLE_STATE_VERBALIZATION in roles else f"eligible_{source_line.line_role}",
            "ending_key": "humble_observation",
            "role_phrase_key": "+".join(roles),
            "relation_type": relation,
            "template_skeleton_key": skeleton,
            "raw_input_included": False,
        }
        lines.append(
            ObservationSurfaceLine(
                line_id=_line_hash(text, source_line.line_role),
                line_role=source_line.line_role,
                observation_roles=roles,
                surface_text=text,
                relation_type=relation,
                material_entry_ids=_dedupe(source_meta.get("phrase_unit_ids") or source_meta.get("used_phrase_unit_ids")),
                supporting_evidence_ids=_dedupe(source_meta.get("evidence_span_ids") or source_meta.get("used_evidence_span_ids")),
                tone_policy_key=tone["tone_policy_key"],
                temperature_key=tone["temperature_key"],
                tone_guard_keys=tone["tone_guard_keys"],
                template_skeleton_key=skeleton,
                surface_signature=signature,
                source_line_meta=source_meta,
                line_role_merge=merge,
            )
        )
    body = "".join(line.surface_text for line in lines)
    roles: list[str] = []
    for line in lines:
        roles.extend(line.observation_roles)
    forbidden_ids = _forbidden_signature_ids(OBSERVATION_REPLY_KIND_ELIGIBLE)
    tone_report = _tone_guard_report(body=body, observation_roles=roles, reply_kind=OBSERVATION_REPLY_KIND_ELIGIBLE)
    template_report = _template_guard_report(body=body, lines=lines, reply_kind=OBSERVATION_REPLY_KIND_ELIGIBLE, forbidden_template_signature_ids=forbidden_ids)
    realization = ObservationSurfaceRealization(
        body=body,
        lines=tuple(lines),
        observation_reply_kind=OBSERVATION_REPLY_KIND_ELIGIBLE,
        eligibility_status=OBSERVATION_ELIGIBILITY_STATUS_ELIGIBLE,
        eligible_for_full_observation=True,
        question_required=False,
        tone_guard_report=tone_report,
        template_guard_report=template_report,
        source_meta={
            "source_step": getattr(plan, "schema_version", "complete_sentence_plan"),
            "plan_id": getattr(plan, "plan_id", ""),
            "coverage_group": getattr(plan, "coverage_group", ""),
            "comment_text_generated": False,
            "raw_input_included": False,
        },
    )
    assert_observation_surface_realizer_tone_contract(realization)
    return realization


def realize_observation_surface_tone(
    *,
    observation_reply_kind: str = "",
    low_information_draft: LowInformationObservationDraft | Mapping[str, Any] | None = None,
    sentence_plan: CompleteSentencePlanV2 | Mapping[str, Any] | None = None,
    current_input: Any = None,
    **kwargs: Any,
) -> ObservationSurfaceRealization:
    kind = _clean(observation_reply_kind)
    if kind == OBSERVATION_REPLY_KIND_ELIGIBLE or sentence_plan is not None:
        return realize_eligible_observation_surface(sentence_plan=sentence_plan, current_input=current_input, **kwargs)
    return realize_low_information_observation_surface(low_information_draft, current_input=current_input, **kwargs)


def build_observation_surface_realizer_tone_meta(*, include_surface_text: bool = False, **kwargs: Any) -> dict[str, Any]:
    realization = realize_observation_surface_tone(**kwargs)
    return realization.as_meta(include_surface_text=include_surface_text)


def build_observation_surface_realizer_tone_contract_meta(*, include_nested_contract: bool = True) -> dict[str, Any]:
    del include_nested_contract
    meta = {
        "version": OBSERVATION_SURFACE_REALIZER_TONE_VERSION,
        "schema_version": OBSERVATION_SURFACE_REALIZER_TONE_SCHEMA_VERSION,
        "source_step": OBSERVATION_SURFACE_REALIZER_TONE_STEP,
        "step": OBSERVATION_SURFACE_REALIZER_TONE_STEP,
        "surface_realizer_observation_roles_supported": True,
        "observation_roles_supported": True,
        "low_info_roles_supported": True,
        "low_information_observation_roles_supported": True,
        "eligible_roles_supported": True,
        "eligible_observation_roles_supported": True,
        "low_info_question_ending_by_unknown_slot": True,
        "unknown_slot_question_ending_policy_enabled": True,
        "eligible_relation_state_verbalization_enabled": True,
        "eligible_state_verbalization_relation_required": True,
        "template_skeleton_guard_enabled": True,
        "tone_update_applied": True,
        "tone_policy_version": OBSERVATION_TONE_POLICY_VERSION,
        "tone_is_surface_constraint_not_post_decoration": True,
        "tone_adjusts_temperature_not_meaning": True,
        "tone_guard_blocks_empathy_only": True,
        "tone_guard_blocks_generic_comfort": True,
        "tone_guard_blocks_advice_and_diagnosis": True,
        "template_guard_version": OBSERVATION_TEMPLATE_GUARD_VERSION,
        "template_guard_detects_completed_sentence_templates": True,
        "template_guard_detects_question_only": True,
        "template_guard_detects_skeleton_repeat": True,
        "surface_text_internal_only": True,
        "comment_text_generated": False,
        "comment_text_key_written": False,
        "comment_text_publicly_assigned": False,
        "public_comment_text_assigned": False,
        "display_gate_relaxed": False,
        "reader_gate_relaxed": False,
        "grounding_gate_relaxed": False,
        "template_gate_relaxed": False,
        "gate_relaxed": False,
        "public_status_extended": False,
        "observation_status_enum_extended": False,
        "api_route_changed": False,
        "db_physical_name_changed": False,
        "public_response_key_change": False,
        "rn_visible_contract_changed": False,
        "rn_visible_title_changed": False,
        "external_ai_used": False,
        "local_llm_used": False,
        "fixed_sentence_template_used": False,
        "completed_sentence_template_used": False,
        "role_completed_sentence_template_used": False,
        "input_specific_template_used": False,
        "raw_input_included": False,
        "raw_text_included": False,
    }
    assert_observation_surface_realizer_tone_contract(meta)
    return meta


def assert_observation_surface_realizer_tone_contract(value: ObservationSurfaceRealization | Mapping[str, Any]) -> None:
    meta = value.as_meta() if isinstance(value, ObservationSurfaceRealization) else dict(value)
    body = value.body if isinstance(value, ObservationSurfaceRealization) else _clean(meta.get("body"))
    if _contains_payload_key(meta):
        raise ValueError("Step 9 observation surface meta must not contain raw input/comment payload keys")
    for key in _FORBIDDEN_TRUE_FLAGS:
        if meta.get(key) is True:
            raise ValueError(f"Step 9 must not change public/runtime contract: {key}=true")
    kind = _clean(meta.get("observation_reply_kind"))
    status = _clean(meta.get("eligibility_status"))
    if kind and kind not in _ALLOWED_REPLY_KINDS:
        raise ValueError(f"unsupported observation_reply_kind: {kind}")
    if status and status not in _ALLOWED_ELIGIBILITY_STATUSES:
        raise ValueError(f"unsupported eligibility_status: {status}")
    if kind == OBSERVATION_REPLY_KIND_LOW_INFORMATION:
        if status and status != OBSERVATION_ELIGIBILITY_STATUS_LOW_INFORMATION:
            raise ValueError("low information surface must keep eligibility_status=low_information")
        if meta.get("eligible_for_full_observation") is True:
            raise ValueError("low information surface must not be promoted to eligible")
        if meta.get("question_required") is not True:
            raise ValueError("low information surface must require a question")
        if not meta.get("low_info_known_scope_present"):
            raise ValueError("low information surface must include known-scope observation role")
        if not meta.get("low_info_question_present"):
            raise ValueError("low information surface must include question role")
        if not meta.get("question_ending_selected_by_unknown_slot"):
            raise ValueError("low information surface must select a question ending from unknown slots")
        if body and _LEGACY_LOW_INFORMATION_PROMPT_RE.search(body):
            raise ValueError("low information surface must not use legacy question wording")
        if body and not _QUESTION_RE.search(body):
            raise ValueError("low information surface body must contain a question")
        if body and _body_sentence_count(body) < 2:
            raise ValueError("low information surface must not be question-only")
    if kind == OBSERVATION_REPLY_KIND_ELIGIBLE:
        if status and status != OBSERVATION_ELIGIBILITY_STATUS_ELIGIBLE:
            raise ValueError("eligible surface must keep eligibility_status=eligible")
        if meta.get("eligible_for_full_observation") is False:
            raise ValueError("eligible surface must keep eligible_for_full_observation=true")
        if not meta.get("eligible_state_verbalization_present"):
            raise ValueError("eligible surface must include state_verbalization role")
        if not meta.get("eligible_state_verbalization_relation_connected"):
            raise ValueError("eligible surface state_verbalization must be relation-connected")
        if meta.get("empathy_only_detected") is True:
            raise ValueError("eligible surface must not be empathy-only")
    if meta.get("tone_guard_passed") is False:
        raise ValueError("Step 9 tone guard did not pass")
    if meta.get("template_guard_passed") is False:
        raise ValueError("Step 9 template guard did not pass")
    if int(meta.get("surface_skeleton_repeat_count") or 0) > 0:
        raise ValueError("Step 9 surface skeleton repeat guard did not pass")
    if body:
        if _FORBIDDEN_COMPLETE_TEMPLATE_RE.search(body):
            raise ValueError("Step 9 body contains a forbidden completed template")
        if _UNSUPPORTED_EVENT_ASSERTION_RE.search(body):
            raise ValueError("Step 9 body contains unsupported assertion/diagnostic wording")
        if _ACTION_INSTRUCTION_RE.search(body):
            raise ValueError("Step 9 body contains advice-like instruction")
    roles = _dedupe(meta.get("sentence_plan_observation_roles"))
    unsupported_roles = [role for role in roles if role not in _ALLOWED_OBSERVATION_ROLES]
    if unsupported_roles:
        raise ValueError(f"unsupported observation role(s): {', '.join(unsupported_roles)}")


def _roles_from_lines_for_report(lines: Sequence[Any] | None) -> list[str]:
    roles: list[str] = []
    for line in lines or []:
        if isinstance(line, ObservationSurfaceLine):
            src = line.observation_roles
        elif isinstance(line, Mapping):
            src = line.get("observation_roles") or line.get("sentence_plan_observation_roles") or []
        else:
            src = getattr(line, "observation_roles", [])
        for role in _dedupe(src):
            if role not in roles:
                roles.append(role)
    return roles


def build_observation_surface_tone_report(
    *,
    text: str = "",
    body: str = "",
    surface_text: str = "",
    surface_lines: Sequence[Any] | None = None,
    lines: Sequence[Any] | None = None,
    observation_reply_kind: str = OBSERVATION_REPLY_KIND_ELIGIBLE,
    question_required: bool = False,
    tone_policy: Mapping[str, Any] | None = None,
    **_: Any,
) -> dict[str, Any]:
    del question_required, tone_policy
    line_values = tuple(surface_lines or lines or ())
    roles = _roles_from_lines_for_report(line_values)
    return _tone_guard_report(
        body=_clean(body or surface_text or text),
        observation_roles=roles,
        reply_kind=observation_reply_kind,
    )


def build_observation_surface_template_report(
    *,
    text: str = "",
    body: str = "",
    surface_text: str = "",
    surface_lines: Sequence[ObservationSurfaceLine] | None = None,
    lines: Sequence[ObservationSurfaceLine] | None = None,
    observation_reply_kind: str = OBSERVATION_REPLY_KIND_ELIGIBLE,
    forbidden_template_signature_ids: Sequence[str] | None = None,
    **_: Any,
) -> dict[str, Any]:
    line_values = tuple(surface_lines or lines or ())
    return _template_guard_report(
        body=_clean(body or surface_text or text),
        lines=line_values,
        reply_kind=observation_reply_kind,
        forbidden_template_signature_ids=forbidden_template_signature_ids or _forbidden_signature_ids(observation_reply_kind),
    )


def dump_observation_surface_realizer_tone(value: ObservationSurfaceRealization | Mapping[str, Any]) -> str:
    meta = value.as_meta(include_surface_text=False) if isinstance(value, ObservationSurfaceRealization) else dict(value)
    return json.dumps(_json_safe(meta), ensure_ascii=False, sort_keys=True, indent=2)


# Backward-friendly aliases for tests/callers.
realize_observation_surface = realize_observation_surface_tone
build_observation_surface_realizer = realize_observation_surface_tone
build_observation_surface_realizer_meta = build_observation_surface_realizer_tone_meta
build_observation_surface_realizer_contract_meta = build_observation_surface_realizer_tone_contract_meta
assert_observation_surface_realizer_contract = assert_observation_surface_realizer_tone_contract
build_observation_surface_tone_meta = build_observation_surface_realizer_tone_meta
dump_observation_surface_realizer = dump_observation_surface_realizer_tone
build_emlis_ai_observation_surface_realizer_tone_meta = build_observation_surface_realizer_tone_meta
build_emlis_ai_observation_surface = realize_observation_surface_tone
realize_emlis_ai_observation_surface_tone = realize_observation_surface_tone

__all__ = [
    "OBSERVATION_SURFACE_REALIZER_TONE_SCHEMA_VERSION",
    "OBSERVATION_SURFACE_REALIZER_TONE_STEP",
    "OBSERVATION_SURFACE_REALIZER_TONE_VERSION",
    "OBSERVATION_TEMPLATE_GUARD_VERSION",
    "OBSERVATION_TONE_POLICY_VERSION",
    "QUESTION_SURFACE_KIND_WHAT_CHANGED",
    "QUESTION_SURFACE_KIND_WHAT_HAPPENED",
    "QUESTION_SURFACE_KIND_WHAT_IS_HARD_TO_SAY",
    "QUESTION_SURFACE_KIND_WHICH_PART_FEELS_HEAVY",
    "ObservationSurfaceLine",
    "ObservationSurfaceRealization",
    "assert_observation_surface_realizer_tone_contract",
    "build_emlis_ai_observation_surface",
    "build_emlis_ai_observation_surface_realizer_tone_meta",
    "build_observation_surface_realizer_tone_contract_meta",
    "build_observation_surface_realizer_tone_meta",
    "build_observation_surface_tone_meta",
    "dump_observation_surface_realizer_tone",
    "realize_eligible_observation_surface",
    "realize_emlis_ai_observation_surface_tone",
    "realize_low_information_observation_surface",
    "select_observation_question_ending",
    "realize_observation_surface",
    "build_observation_surface_realizer",
    "build_observation_surface_realizer_meta",
    "build_observation_surface_realizer_contract_meta",
    "assert_observation_surface_realizer_contract",
    "dump_observation_surface_realizer",
    "build_observation_surface_template_report",
    "build_observation_surface_tone_report",
    "realize_observation_surface_tone",
]
