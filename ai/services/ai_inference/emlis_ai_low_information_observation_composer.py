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
LOW_INFORMATION_SPECIFICITY_PLAN_VERSION: Final = "emlis.low_information_specificity_plan.v1"
LOW_INFORMATION_SPECIFICITY_STEP: Final = "Step6_Low_Information_Specificity"

QUESTION_SURFACE_WHAT_HAPPENED: Final = "what_happened"
QUESTION_SURFACE_WHAT_CHANGED: Final = "what_changed"
QUESTION_SURFACE_WHICH_PART_FEELS_HEAVY: Final = "which_part_feels_heavy"
QUESTION_SURFACE_WHAT_IS_HARD_TO_SAY: Final = "what_is_hard_to_say"

LOW_INFORMATION_TONE_PROFILE_VERSION: Final = "emlis.low_information_tone_profile.v1"
LOW_INFORMATION_TONE_PROFILE_STEP: Final = "Step5_Low_Information_Tone_Profile"
LOW_INFORMATION_TONE_PROFILE_POSITIVE_ONLY: Final = "positive_only"
LOW_INFORMATION_TONE_PROFILE_NEGATIVE_ONLY: Final = "negative_only"
LOW_INFORMATION_TONE_PROFILE_MIXED: Final = "mixed"
LOW_INFORMATION_TONE_PROFILE_SELF_INSIGHT: Final = "self_insight"
LOW_INFORMATION_TONE_PROFILE_NEUTRAL_OR_UNKNOWN: Final = "neutral_or_unknown"
LOW_INFORMATION_TONE_PROFILES: Final = (
    LOW_INFORMATION_TONE_PROFILE_POSITIVE_ONLY,
    LOW_INFORMATION_TONE_PROFILE_NEGATIVE_ONLY,
    LOW_INFORMATION_TONE_PROFILE_MIXED,
    LOW_INFORMATION_TONE_PROFILE_SELF_INSIGHT,
    LOW_INFORMATION_TONE_PROFILE_NEUTRAL_OR_UNKNOWN,
)

_LINE_ROLE_OPENING: Final = "opening"
_LINE_ROLE_CORE: Final = "core"
_LINE_ROLE_CLOSING: Final = "closing"

_SPACE_RE: Final = re.compile(r"\s+")
_SENTENCE_SPLIT_RE: Final = re.compile(r"[。！？!?]+")
_FORBIDDEN_COMPLETE_TEMPLATE_RE: Final = re.compile(
    r"(Emlisです|Emlisでは観測できません|もっと詳しく教えてください|つらかったですね[。\s]*無理しないでくださいね|無理しないでくださいね|あなたは十分頑張っています|よければ、何がありましたか|何がありましたか)"
)
_PAST_REFERENCE_RE: Final = re.compile(r"(以前にも|前にも|過去にも|前回も)")
_EVENT_ASSERTION_RE: Final = re.compile(r"(同じことで疲れている|環境の件で疲れている|前と同じことで|今回も環境|あなたはいつも|しやすい人)")
_QUESTION_MARK_RE: Final = re.compile(
    r"(詳しく残せそうなら、(?:何があったか|どのあたりが重くなっているか|何が変わったのか|どこから言いにくくなっているか|何について大丈夫か気になっているのか)残してみませんか|残してみませんか|何がありましたか|何が起きたか|どの部分が重くなっていますか|どの部分が重くなっているか|何が変わりましたか|どこから言いにくくなっていますか|何を言いにくく感じていますか|どうしましたか|何について大丈夫か気になっていますか)"
)
_LEGACY_LOW_INFORMATION_PROMPT_RE: Final = re.compile(r"(よければ、|何がありましたか[。！？!?]?)")
_HUMILITY_MARKER_RE: Final = re.compile(r"(ように見えます|かもしれません|まだ見えていません|まだ決められません|なさそうです)")
_KNOWN_SCOPE_RE: Final = re.compile(r"(言葉になる前の重さ|疲れの重さ|不安の重さ|無理かもしれない感じ|大丈夫かどうか|安心してよいか|ここから見えているのは|軽く流せるものではなさそう|詳しい出来事まではまだ見えません|まだ詳しい出来事までは見えません|まだ詳細までは見えません|穏やかに残っているもの|大切に置かれている|同時に残っている範囲)")

_POSITIVE_EMOTIONS: Final = frozenset({"喜び", "平穏"})
_NEGATIVE_EMOTIONS: Final = frozenset({"悲しみ", "怒り", "不安", "疲れ", "疲労"})
_SELF_INSIGHT_EMOTIONS: Final = frozenset({"自己理解"})
_NEGATIVE_TEXT_ANCHOR_RE: Final = re.compile(
    r"(不安|悲し|怒り|疲れ|つかれ|疲労|つらい|辛い|苦しい|しんどい|きつい|怖い|こわい|焦り|焦っ|負荷|重さ|重い|無理|限界|消耗|眠れ)",
    re.IGNORECASE,
)
_BURDEN_SURFACE_RE: Final = re.compile(r"(不安の重さ|疲れの重さ|言葉になる前の重さ|軽く流せるものではなさそう|無理かもしれない|負荷|重さ)")
_POSITIVE_OPENING_SURFACE_BY_EMOTION: Final = {
    "喜び": "大切にしたい気持ち",
    "平穏": "穏やかに残っているもの",
}
_POSITIVE_DEFAULT_OPENING_SURFACE: Final = "その日に感じたこと"
_POSITIVE_KNOWN_SCOPE_SURFACE: Final = "まだ詳しい出来事までは見えませんが、その日に感じたことは大切に置かれているように見えます。"
_MIXED_KNOWN_SCOPE_SURFACE: Final = "まだ詳しい出来事までは見えませんが、同時に残っている範囲だけが見えています。"
_SELF_INSIGHT_OPENING_SURFACE: Final = "自分について見えかけているもの"
_SELF_INSIGHT_KNOWN_SCOPE_SURFACE: Final = "まだ詳細までは見えませんが、理解がどこから出てきたのかはまだ決められません。"

_SAFE_ANCHOR_PATTERNS: Final = (
    ("question", "safety_confirmation", re.compile(r"(大丈夫|だいじょうぶ|平気|安心)", re.IGNORECASE), "「大丈夫かどうか」を確かめたい感じ"),
    ("emotion", "anxiety_weight", re.compile(r"(不安|こわい|怖い|焦り|焦っ)", re.IGNORECASE), "不安の重さ"),
    ("state", "overload", re.compile(r"(無理|限界|しんど|つらい|辛い|きつい)", re.IGNORECASE), "無理かもしれない感じ"),
    ("emotion", "fatigue_weight", re.compile(r"(疲れ|つかれ|消耗)", re.IGNORECASE), "疲れの重さ"),
    ("uncertainty", "uncertainty", re.compile(r"(分からな|わからな|迷|決められな)", re.IGNORECASE), "まだ決めきれない感じ"),
    ("state", "hard_to_say", re.compile(r"(言えな|言いにく|話しにく)", re.IGNORECASE), "言いにくさ"),
)
_EMOTION_ANCHOR_SURFACES: Final = {
    "疲れ": ("emotion", "fatigue_weight", "疲れの重さ"),
    "つかれ": ("emotion", "fatigue_weight", "疲れの重さ"),
    "不安": ("emotion", "anxiety_weight", "不安の重さ"),
    "焦り": ("emotion", "anxiety_weight", "不安の重さ"),
    "怖い": ("emotion", "anxiety_weight", "不安の重さ"),
    "こわい": ("emotion", "anxiety_weight", "不安の重さ"),
}

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
    surface = _normalize_low_information_question_fragment(selected_entry.get("surface"))
    if surface:
        if kind == QUESTION_SURFACE_WHICH_PART_FEELS_HEAVY and surface == "どのあたりが重くなっているか":
            return surface
        if kind == QUESTION_SURFACE_WHAT_CHANGED and surface == "何が変わったのか":
            return surface
        if kind == QUESTION_SURFACE_WHAT_IS_HARD_TO_SAY and surface == "どこから言いにくくなっているか":
            return surface
        if kind == QUESTION_SURFACE_WHAT_HAPPENED and surface == "何があったか":
            return surface
    if kind == QUESTION_SURFACE_WHICH_PART_FEELS_HEAVY:
        return "どのあたりが重くなっているか"
    if kind == QUESTION_SURFACE_WHAT_CHANGED:
        return "何が変わったのか"
    if kind == QUESTION_SURFACE_WHAT_IS_HARD_TO_SAY:
        return "どこから言いにくくなっているか"
    return "何があったか"


def _normalize_low_information_question_fragment(question_surface: Any) -> str:
    fragment = _clean(question_surface)
    if not fragment:
        return "何があったか"
    fragment = re.sub(r"^よければ、", "", fragment).strip()
    fragment = re.sub(r"^詳しく残せそうなら、", "", fragment).strip()
    fragment = re.sub(r"残してみませんか[。！？!?]*$", "", fragment).strip()
    fragment = fragment.rstrip("。！？!?")
    legacy_map = {
        "何がありましたか": "何があったか",
        "何が起きたか": "何があったか",
        "どの部分が重くなっていますか": "どのあたりが重くなっているか",
        "どの部分が重くなっているか": "どのあたりが重くなっているか",
        "何が変わりましたか": "何が変わったのか",
        "どこから言いにくくなっていますか": "どこから言いにくくなっているか",
        "何を言いにくく感じていますか": "どこから言いにくくなっているか",
        "何について大丈夫か気になっていますか": "何について大丈夫か気になっているのか",
    }
    return legacy_map.get(fragment, fragment or "何があったか")


def format_low_information_question_prompt(
    question_surface: Any = "",
    *,
    safe_anchor_kind: str = "",
) -> str:
    if _clean(safe_anchor_kind) == "safety_confirmation":
        fragment = "何について大丈夫か気になっているのか"
    else:
        fragment = _normalize_low_information_question_fragment(question_surface)
    return _ensure_sentence(f"詳しく残せそうなら、{fragment}残してみませんか")


def _unknown_marker_for_slots(unknown_slots: Sequence[str]) -> str:
    slots = set(unknown_slots)
    if UNKNOWN_SLOT_TARGET in slots or UNKNOWN_SLOT_RELATION in slots:
        return "どのあたりが重くなっているか"
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


def _emotion_labels(current_input: Any) -> list[str]:
    if not isinstance(current_input, Mapping):
        return []
    out: list[str] = []
    for key in ("emotions", "emotion_details", "emotion_labels"):
        value = current_input.get(key)
        if isinstance(value, Mapping):
            iterable: Iterable[Any] = [value]
        elif isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
            iterable = value
        else:
            iterable = [value] if value is not None else []
        for item in iterable:
            if isinstance(item, Mapping):
                label = _clean(item.get("type") or item.get("label") or item.get("name") or item.get("emotion"))
            else:
                label = _clean(item)
            if label and label not in out:
                out.append(label)
    return out


def _negative_text_anchor_present(current_input: Any) -> bool:
    return bool(_NEGATIVE_TEXT_ANCHOR_RE.search(_current_input_text(current_input)))


def _low_information_tone_profile(current_input: Any) -> str:
    labels = set(_emotion_labels(current_input))
    negative_anchor_present = _negative_text_anchor_present(current_input)
    if not labels:
        return LOW_INFORMATION_TONE_PROFILE_NEGATIVE_ONLY if negative_anchor_present else LOW_INFORMATION_TONE_PROFILE_NEUTRAL_OR_UNKNOWN
    has_positive = bool(labels & _POSITIVE_EMOTIONS)
    has_negative = bool(labels & _NEGATIVE_EMOTIONS)
    has_self_insight = bool(labels & _SELF_INSIGHT_EMOTIONS)
    if has_self_insight and not has_positive and not has_negative and labels <= _SELF_INSIGHT_EMOTIONS:
        return LOW_INFORMATION_TONE_PROFILE_SELF_INSIGHT
    if has_positive and not has_negative and not negative_anchor_present:
        return LOW_INFORMATION_TONE_PROFILE_POSITIVE_ONLY
    if has_positive and (has_negative or negative_anchor_present):
        return LOW_INFORMATION_TONE_PROFILE_MIXED
    if has_negative and not has_positive:
        return LOW_INFORMATION_TONE_PROFILE_NEGATIVE_ONLY
    if negative_anchor_present and not has_positive:
        return LOW_INFORMATION_TONE_PROFILE_NEGATIVE_ONLY
    return LOW_INFORMATION_TONE_PROFILE_NEUTRAL_OR_UNKNOWN


def _positive_opening_surface(current_input: Any) -> str:
    labels = _emotion_labels(current_input)
    for label in labels:
        surface = _POSITIVE_OPENING_SURFACE_BY_EMOTION.get(label)
        if surface:
            return surface
    return _POSITIVE_DEFAULT_OPENING_SURFACE


def _bridge_opening_text(
    *,
    receive_surface: str,
    selected_positive_surface: str,
    anchor_surface: str,
    burden_surface: str,
    humility_surface: str,
) -> str:
    secondary_surface = anchor_surface or burden_surface
    primary_surface = selected_positive_surface or _POSITIVE_DEFAULT_OPENING_SURFACE
    if secondary_surface:
        return f"{receive_surface}、{primary_surface}だけではなく、{secondary_surface}も近くにある{humility_surface}。"
    return f"{receive_surface}、状態が一色ではない{humility_surface}。"


def _negative_multi_emotion_bridge_opening_text(
    *,
    current_input: Any,
    receive_surface: str,
    anchor_surface: str,
    burden_surface: str,
    humility_surface: str,
) -> str:
    """Bridge multiple selected negative labels without asserting a deep relation.

    Visible Surface Gate treats the first selected emotion as the visible
    dominant label.  When a low-information surface mentions only a secondary
    negative label such as ``不安の重さ``, the gate correctly asks for a bridge.
    This helper keeps the same low-information scope while explicitly holding
    the visible dominant label and the bounded anchor together.
    """

    negative_labels = [label for label in _emotion_labels(current_input) if label in _NEGATIVE_EMOTIONS]
    if len(negative_labels) < 2:
        return ""
    dominant_label = negative_labels[0]
    secondary_surface = anchor_surface if anchor_surface and dominant_label not in anchor_surface else ""
    if not secondary_surface:
        for label in negative_labels[1:]:
            if label != dominant_label:
                secondary_surface = f"{label}の重さ"
                break
    secondary_surface = secondary_surface or burden_surface
    return f"{receive_surface}、{dominant_label}だけではなく、{secondary_surface}も近くにある{humility_surface}。"


def _apply_tone_profile_question_surface_kind(
    *,
    question_surface_kind: str,
    unknown_slots: Sequence[str],
    tone_profile: str,
) -> str:
    if tone_profile != LOW_INFORMATION_TONE_PROFILE_POSITIVE_ONLY:
        return question_surface_kind
    if UNKNOWN_SLOT_DESIRED_DIRECTION in set(unknown_slots):
        return QUESTION_SURFACE_WHAT_CHANGED
    if question_surface_kind in {QUESTION_SURFACE_WHICH_PART_FEELS_HEAVY, QUESTION_SURFACE_WHAT_IS_HARD_TO_SAY}:
        return QUESTION_SURFACE_WHAT_HAPPENED
    return question_surface_kind


def _low_information_tone_profile_plan(
    *,
    tone_profile: str,
    current_input: Any,
    question_surface_kind: str,
) -> dict[str, Any]:
    negative_anchor_present = _negative_text_anchor_present(current_input)
    selected_labels = _emotion_labels(current_input)
    burden_default_allowed = tone_profile in {
        LOW_INFORMATION_TONE_PROFILE_NEGATIVE_ONLY,
        LOW_INFORMATION_TONE_PROFILE_MIXED,
        LOW_INFORMATION_TONE_PROFILE_NEUTRAL_OR_UNKNOWN,
    } or negative_anchor_present
    return {
        "version": LOW_INFORMATION_TONE_PROFILE_VERSION,
        "source_step": LOW_INFORMATION_TONE_PROFILE_STEP,
        "connected_to_composer_step": LOW_INFORMATION_OBSERVATION_COMPOSER_STEP,
        "tone_profile": tone_profile if tone_profile in LOW_INFORMATION_TONE_PROFILES else LOW_INFORMATION_TONE_PROFILE_NEUTRAL_OR_UNKNOWN,
        "selected_emotion_count": len(selected_labels),
        "negative_text_anchor_present": bool(negative_anchor_present),
        "burden_surface_default_allowed": bool(burden_default_allowed),
        "positive_burden_surface_default_blocked": bool(tone_profile == LOW_INFORMATION_TONE_PROFILE_POSITIVE_ONLY and not negative_anchor_present),
        "mixed_requires_bridge_between_emotions": bool(tone_profile == LOW_INFORMATION_TONE_PROFILE_MIXED),
        "question_surface_kind": question_surface_kind,
        "raw_input_included": False,
        "raw_text_included": False,
        "comment_text_body_included": False,
        "comment_text_included": False,
    }


def _observed_scope_for_tone_profile(tone_profile: str) -> tuple[str, ...]:
    if tone_profile == LOW_INFORMATION_TONE_PROFILE_POSITIVE_ONLY:
        return ("positive_feeling", "low_information_known_scope", "under_specified_detail")
    if tone_profile == LOW_INFORMATION_TONE_PROFILE_MIXED:
        return ("coexisting_emotions", "low_information_known_scope", "under_specified_detail")
    if tone_profile == LOW_INFORMATION_TONE_PROFILE_SELF_INSIGHT:
        return ("unformed_self_insight", "low_information_known_scope", "under_specified_detail")
    return ("emotion_weight", "language_before_detail", "unspecified_burden")


def _question_entry_for_low_information_tone_profile(
    *,
    base_question_surface_kind: str,
    question_surface_kind: str,
    unknown_slots: Sequence[str],
) -> dict[str, Any]:
    # When Step5 tone profile changes the preferred question family, avoid
    # retaining a mismatched dictionary entry id such as question_what_happened
    # while rendering a what_changed surface. The profile-selected question stays
    # dictionary-shaped but is marked as a bounded profile preference.
    if question_surface_kind != base_question_surface_kind:
        return {
            "entry_id": f"tone_profile_question_{question_surface_kind}",
            "category": CATEGORY_QUESTION_ENDING,
            "surface": _question_surface_for_kind(question_surface_kind, {}),
            "allowed_reply_kinds": [OBSERVATION_REPLY_KIND_LOW_INFORMATION],
            "requires_evidence_role": ["unknown_slot"],
            "unknown_slots": list(unknown_slots),
            "selected_by_tone_profile": True,
            "template_signature_weight": 0.0,
            "positive_material": True,
        }
    return _select_first_material(
        category=CATEGORY_QUESTION_ENDING,
        evidence_roles=["unknown_slot"],
        unknown_slots=unknown_slots,
        default_surface=_question_surface_for_kind(question_surface_kind, {}),
    )


def _low_information_safe_anchor_evidence_ids(
    eligibility_meta: Mapping[str, Any],
    material_meta: Mapping[str, Any],
    *,
    limit: int = 2,
) -> list[str]:
    ids = _known_fragment_ids(eligibility_meta, material_meta)
    return ids[: max(0, int(limit))]


def _select_low_information_safe_anchor(
    current_input: Any,
    eligibility_meta: Mapping[str, Any],
    material_meta: Mapping[str, Any],
) -> dict[str, Any]:
    """Select one bounded current-input anchor for Step 6 specificity.

    The returned mapping may contain a short display surface, but only the role,
    kind, and evidence ids are exposed in diagnostics.  Long raw input is never
    stored in meta, and the surface is a constrained rephrase rather than a raw
    memo copy.
    """

    text = _current_input_text(current_input)
    evidence_ids = _low_information_safe_anchor_evidence_ids(eligibility_meta, material_meta)
    for role, kind, pattern, surface in _SAFE_ANCHOR_PATTERNS:
        if text and pattern.search(text):
            return {
                "role": role,
                "surface_kind": kind,
                "surface": surface,
                "source": "current_input_safe_anchor",
                "evidence_ids": evidence_ids,
            }

    for label in _emotion_labels(current_input):
        normalized = _clean(label)
        for needle, (role, kind, surface) in _EMOTION_ANCHOR_SURFACES.items():
            if needle in normalized:
                return {
                    "role": role,
                    "surface_kind": kind,
                    "surface": surface,
                    "source": "emotion_label_safe_anchor",
                    "evidence_ids": evidence_ids,
                }

    return {
        "role": "none",
        "surface_kind": "none",
        "surface": "",
        "source": "none",
        "evidence_ids": [],
    }


def _low_information_specificity_plan(anchor: Mapping[str, Any] | None) -> dict[str, Any]:
    role = _clean((anchor or {}).get("role")) or "none"
    surface_kind = _clean((anchor or {}).get("surface_kind")) or "none"
    uses_anchor = role != "none" and surface_kind != "none"
    evidence_ids = _dedupe((anchor or {}).get("evidence_ids")) if uses_anchor else []
    return {
        "version": LOW_INFORMATION_SPECIFICITY_PLAN_VERSION,
        "source_step": LOW_INFORMATION_SPECIFICITY_STEP,
        "eligible": True,
        "safe_anchor_count": 1 if uses_anchor else 0,
        "uses_safe_anchor": bool(uses_anchor),
        "safe_anchor_role": role if uses_anchor else "none",
        "safe_anchor_surface_kind": surface_kind if uses_anchor else "none",
        "safe_anchor_source": _clean((anchor or {}).get("source")) if uses_anchor else "none",
        "safe_anchor_evidence_ids": evidence_ids,
        "contains_humility_marker": True,
        "contains_question": True,
        "unsupported_event_assertion_present": False,
        "user_fact_promotion_attempt": False,
        "raw_input_included": False,
        "raw_text_included": False,
        "comment_text_body_included": False,
        "comment_text_included": False,
    }


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
    low_information_specificity_plan: Mapping[str, Any] = field(default_factory=dict)
    low_information_tone_profile_plan: Mapping[str, Any] = field(default_factory=dict)
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
            "low_information_specificity_plan": dict(self.low_information_specificity_plan or {}),
            "low_information_tone_profile_plan": dict(self.low_information_tone_profile_plan or {}),
            "low_information_tone_profile": _clean((self.low_information_tone_profile_plan or {}).get("tone_profile")) or LOW_INFORMATION_TONE_PROFILE_NEUTRAL_OR_UNKNOWN,
            "positive_tone_profile": _clean((self.low_information_tone_profile_plan or {}).get("tone_profile")) or LOW_INFORMATION_TONE_PROFILE_NEUTRAL_OR_UNKNOWN,
            "negative_text_anchor_present": bool((self.low_information_tone_profile_plan or {}).get("negative_text_anchor_present")),
            "burden_surface_default_allowed": bool((self.low_information_tone_profile_plan or {}).get("burden_surface_default_allowed")),
            "positive_burden_surface_default_blocked": bool((self.low_information_tone_profile_plan or {}).get("positive_burden_surface_default_blocked")),
            "mixed_requires_bridge_between_emotions": bool((self.low_information_tone_profile_plan or {}).get("mixed_requires_bridge_between_emotions")),
            "step5_low_information_tone_profile_ready": True,
            "low_information_specificity_used": bool((self.low_information_specificity_plan or {}).get("uses_safe_anchor")),
            "step6_low_information_specificity_ready": True,
            "safe_anchor_count": int((self.low_information_specificity_plan or {}).get("safe_anchor_count") or 0),
            "uses_safe_anchor": bool((self.low_information_specificity_plan or {}).get("uses_safe_anchor")),
            "safe_anchor_role": _clean((self.low_information_specificity_plan or {}).get("safe_anchor_role")) or "none",
            "safe_anchor_surface_kind": _clean((self.low_information_specificity_plan or {}).get("safe_anchor_surface_kind")) or "none",
            "safe_anchor_evidence_ids": list((self.low_information_specificity_plan or {}).get("safe_anchor_evidence_ids") or []),
            "unsupported_event_assertion_present": bool(_EVENT_ASSERTION_RE.search(self.body)),
            "user_fact_promotion_attempt": False,
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
    safe_anchor: Mapping[str, Any] | None = None,
    tone_profile: str = LOW_INFORMATION_TONE_PROFILE_NEUTRAL_OR_UNKNOWN,
    current_input: Any = None,
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

    material_items_for_ids = (receive, burden, known_scope, humility, unknown_marker)
    if tone_profile in {LOW_INFORMATION_TONE_PROFILE_POSITIVE_ONLY, LOW_INFORMATION_TONE_PROFILE_SELF_INSIGHT}:
        material_items_for_ids = (receive, known_scope, humility, unknown_marker)
    selected_ids = [_clean(item.get("entry_id")) for item in material_items_for_ids if _clean(item.get("entry_id"))]

    receive_surface = _clean(receive.get("surface")) or "今は"
    burden_surface = _clean(burden.get("surface")) or "言葉になる前の重さ"
    humility_surface = _clean(humility.get("surface")) or "ように見えます"
    anchor_surface = _clean((safe_anchor or {}).get("surface"))
    anchor_role = _clean((safe_anchor or {}).get("role")) or "none"
    anchor_kind = _clean((safe_anchor or {}).get("surface_kind")) or "none"
    positive_surface = _positive_opening_surface(current_input)

    if tone_profile == LOW_INFORMATION_TONE_PROFILE_POSITIVE_ONLY:
        opening_text = f"{receive_surface}、{positive_surface}がある{humility_surface}。"
    elif tone_profile == LOW_INFORMATION_TONE_PROFILE_MIXED:
        opening_text = _bridge_opening_text(
            receive_surface=receive_surface,
            selected_positive_surface=positive_surface,
            anchor_surface=anchor_surface,
            burden_surface=burden_surface,
            humility_surface=humility_surface,
        )
    elif tone_profile == LOW_INFORMATION_TONE_PROFILE_SELF_INSIGHT:
        opening_text = f"{receive_surface}、{_SELF_INSIGHT_OPENING_SURFACE}がある{humility_surface}。"
    elif tone_profile == LOW_INFORMATION_TONE_PROFILE_NEGATIVE_ONLY and len(_emotion_labels(current_input)) > 1:
        opening_text = _negative_multi_emotion_bridge_opening_text(
            current_input=current_input,
            receive_surface=receive_surface,
            anchor_surface=anchor_surface,
            burden_surface=burden_surface,
            humility_surface=humility_surface,
        ) or (
            f"{receive_surface}、{anchor_surface}が先に出ています。"
            if anchor_surface and anchor_role == "question"
            else f"{receive_surface}、{anchor_surface or burden_surface}が先に出ている{humility_surface}。"
        )
    elif anchor_surface:
        opening_text = f"{receive_surface}、{anchor_surface}が先に出ています。" if anchor_role == "question" else f"{receive_surface}、{anchor_surface}が先に出ている{humility_surface}。"
    elif humility_surface == "かもしれません":
        opening_text = f"{receive_surface}、{burden_surface}が先に出ている{humility_surface}。"
    else:
        opening_text = f"{receive_surface}、{burden_surface}が先に出ている{humility_surface}。"

    unknown_surface = _clean(unknown_marker.get("surface")) or _unknown_marker_for_slots(unknown_slots)
    if plan == "subscription" and facts_used and user_fact_mode == USER_FACT_GROUNDING_MODE_EXPLICIT_REFERENCE and surface_disclosure_required:
        known_scope_text = f"以前にも近い重さが残っていたことはありますが、今回{unknown_surface}まではまだ見えていません。"
    elif tone_profile == LOW_INFORMATION_TONE_PROFILE_POSITIVE_ONLY:
        known_scope_text = _POSITIVE_KNOWN_SCOPE_SURFACE
    elif tone_profile == LOW_INFORMATION_TONE_PROFILE_MIXED:
        known_scope_text = _MIXED_KNOWN_SCOPE_SURFACE
    elif tone_profile == LOW_INFORMATION_TONE_PROFILE_SELF_INSIGHT:
        known_scope_text = _SELF_INSIGHT_KNOWN_SCOPE_SURFACE
    elif anchor_kind == "safety_confirmation":
        known_scope_text = "まだ何が起きたかまでは見えていませんが、安心してよいかを探しているように見えます。"
    elif question_surface_kind == QUESTION_SURFACE_WHICH_PART_FEELS_HEAVY:
        known_scope_text = f"まだ詳しい出来事までは見えませんが、{unknown_surface}はまだ見えていません。"
    elif question_surface_kind == QUESTION_SURFACE_WHAT_CHANGED:
        known_scope_text = f"まだ詳細までは見えませんが、何が変わったのかはまだ決められません。"
    else:
        known_surface = _clean(known_scope.get("surface")) or "まだ詳しい出来事までは見えませんが"
        known_scope_text = f"{known_surface}、軽く流せるものではなさそうです。"

    question_text = format_low_information_question_prompt(
        question_surface,
        safe_anchor_kind=anchor_kind,
    )

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
    tone_profile = _low_information_tone_profile(current_input)
    base_question_surface_kind = _question_surface_kind_for_slots(unknown_slots)
    question_surface_kind = _apply_tone_profile_question_surface_kind(
        question_surface_kind=base_question_surface_kind,
        unknown_slots=unknown_slots,
        tone_profile=tone_profile,
    )
    question_entry = _question_entry_for_low_information_tone_profile(
        base_question_surface_kind=base_question_surface_kind,
        question_surface_kind=question_surface_kind,
        unknown_slots=unknown_slots,
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
    safe_anchor = _select_low_information_safe_anchor(current_input, eligibility_meta, material_meta)
    specificity_plan = _low_information_specificity_plan(safe_anchor)
    tone_profile_plan = _low_information_tone_profile_plan(
        tone_profile=tone_profile,
        current_input=current_input,
        question_surface_kind=question_surface_kind,
    )

    lines = _build_lines(
        unknown_slots=unknown_slots,
        question_surface_kind=question_surface_kind,
        question_surface=question_surface,
        plan=plan,
        user_fact_mode=user_fact_mode,
        facts_used=facts_used,
        surface_disclosure_required=surface_disclosure_required,
        known_fragment_evidence_ids=known_ids,
        safe_anchor=safe_anchor,
        tone_profile=tone_profile,
        current_input=current_input,
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
        observed_scope=_observed_scope_for_tone_profile(tone_profile),
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
        low_information_specificity_plan=specificity_plan,
        low_information_tone_profile_plan=tone_profile_plan,
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
    if _LEGACY_LOW_INFORMATION_PROMPT_RE.search(body):
        raise ValueError(f"{source} must not use legacy low-information question wording")
    if not _QUESTION_MARK_RE.search(body):
        raise ValueError(f"{source} body must include a question for an unknown slot")
    if _QUESTION_MARK_RE.fullmatch(body.strip("。！？!?")):
        raise ValueError(f"{source} must not return question-only text")

    specificity_plan = meta.get("low_information_specificity_plan") if isinstance(meta.get("low_information_specificity_plan"), Mapping) else {}
    safe_anchor_count = int(meta.get("safe_anchor_count") if meta.get("safe_anchor_count") is not None else specificity_plan.get("safe_anchor_count") or 0)
    uses_safe_anchor = bool(meta.get("uses_safe_anchor") or specificity_plan.get("uses_safe_anchor"))
    if safe_anchor_count > 0 and not uses_safe_anchor:
        raise ValueError(f"{source} must use a safe anchor when safe_anchor_count is positive")
    if safe_anchor_count == 0 and uses_safe_anchor:
        raise ValueError(f"{source} must not mark safe anchor usage without a safe anchor")
    if safe_anchor_count > 0 and _clean(meta.get("safe_anchor_role") or specificity_plan.get("safe_anchor_role")) in {"", "none"}:
        raise ValueError(f"{source} must expose safe_anchor_role as meta-only classification")
    if meta.get("unsupported_event_assertion_present") is True or specificity_plan.get("unsupported_event_assertion_present") is True:
        raise ValueError(f"{source} must not contain unsupported event assertions")
    if meta.get("user_fact_promotion_attempt") is True or specificity_plan.get("user_fact_promotion_attempt") is True:
        raise ValueError(f"{source} must not attempt user fact promotion")

    tone_profile_plan = meta.get("low_information_tone_profile_plan") if isinstance(meta.get("low_information_tone_profile_plan"), Mapping) else {}
    tone_profile = _clean(meta.get("low_information_tone_profile") or meta.get("positive_tone_profile") or tone_profile_plan.get("tone_profile"))
    if tone_profile and tone_profile not in LOW_INFORMATION_TONE_PROFILES:
        raise ValueError(f"{source} has invalid low-information tone profile")
    if tone_profile == LOW_INFORMATION_TONE_PROFILE_POSITIVE_ONLY and not bool(meta.get("negative_text_anchor_present") or tone_profile_plan.get("negative_text_anchor_present")):
        if _BURDEN_SURFACE_RE.search(body):
            raise ValueError(f"{source} must not default positive-only low information to burden surfaces")
        if _clean(meta.get("question_surface_kind")) == QUESTION_SURFACE_WHICH_PART_FEELS_HEAVY:
            raise ValueError(f"{source} positive-only low information must not default to heavy-part question surface")

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
        "low_information_specificity_plan": dict(self.low_information_specificity_plan or {}),
        "low_information_tone_profile_plan": dict(self.low_information_tone_profile_plan or {}),
        "low_information_tone_profile": _clean((self.low_information_tone_profile_plan or {}).get("tone_profile")) or LOW_INFORMATION_TONE_PROFILE_NEUTRAL_OR_UNKNOWN,
        "positive_tone_profile": _clean((self.low_information_tone_profile_plan or {}).get("tone_profile")) or LOW_INFORMATION_TONE_PROFILE_NEUTRAL_OR_UNKNOWN,
        "negative_text_anchor_present": bool((self.low_information_tone_profile_plan or {}).get("negative_text_anchor_present")),
        "burden_surface_default_allowed": bool((self.low_information_tone_profile_plan or {}).get("burden_surface_default_allowed")),
        "positive_burden_surface_default_blocked": bool((self.low_information_tone_profile_plan or {}).get("positive_burden_surface_default_blocked")),
        "mixed_requires_bridge_between_emotions": bool((self.low_information_tone_profile_plan or {}).get("mixed_requires_bridge_between_emotions")),
        "step5_low_information_tone_profile_ready": True,
        "low_information_specificity_used": bool((self.low_information_specificity_plan or {}).get("uses_safe_anchor")),
        "step6_low_information_specificity_ready": True,
        "safe_anchor_count": int((self.low_information_specificity_plan or {}).get("safe_anchor_count") or 0),
        "uses_safe_anchor": bool((self.low_information_specificity_plan or {}).get("uses_safe_anchor")),
        "safe_anchor_role": _clean((self.low_information_specificity_plan or {}).get("safe_anchor_role")) or "none",
        "safe_anchor_surface_kind": _clean((self.low_information_specificity_plan or {}).get("safe_anchor_surface_kind")) or "none",
        "safe_anchor_evidence_ids": list((self.low_information_specificity_plan or {}).get("safe_anchor_evidence_ids") or []),
        "unsupported_event_assertion_present": bool(_EVENT_ASSERTION_RE.search(self.body)),
        "user_fact_promotion_attempt": False,
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
LOW_INFORMATION_SPECIFICITY_PLAN_SCHEMA_VERSION: Final = LOW_INFORMATION_SPECIFICITY_PLAN_VERSION
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
    "LOW_INFORMATION_SPECIFICITY_PLAN_VERSION",
    "LOW_INFORMATION_TONE_PROFILE_VERSION",
    "LOW_INFORMATION_TONE_PROFILE_POSITIVE_ONLY",
    "LOW_INFORMATION_TONE_PROFILE_NEGATIVE_ONLY",
    "LOW_INFORMATION_TONE_PROFILE_MIXED",
    "LOW_INFORMATION_TONE_PROFILE_SELF_INSIGHT",
    "LOW_INFORMATION_TONE_PROFILE_NEUTRAL_OR_UNKNOWN",
    "LOW_INFORMATION_TONE_PROFILES",
    "LOW_INFORMATION_SPECIFICITY_PLAN_SCHEMA_VERSION",
    "LOW_INFORMATION_SPECIFICITY_STEP",
    "LOW_INFORMATION_TONE_PROFILE_VERSION",
    "LOW_INFORMATION_TONE_PROFILE_STEP",
    "LOW_INFORMATION_TONE_PROFILE_POSITIVE_ONLY",
    "LOW_INFORMATION_TONE_PROFILE_NEGATIVE_ONLY",
    "LOW_INFORMATION_TONE_PROFILE_MIXED",
    "LOW_INFORMATION_TONE_PROFILE_SELF_INSIGHT",
    "LOW_INFORMATION_TONE_PROFILE_NEUTRAL_OR_UNKNOWN",
    "LOW_INFORMATION_TONE_PROFILES",
    "format_low_information_question_prompt",
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
