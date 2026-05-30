# -*- coding: utf-8 -*-
from __future__ import annotations

"""Visible Surface Acceptance Gate for EmlisAI.

Step3 adds a meta-only QA gate for the visible Emlis observation surface.  It
checks whether the candidate body is acceptable as a UI-visible response, while
keeping raw input and candidate text out of the returned report.

This module does not call external AI, does not rewrite text, and does not
change RN/API/DB contracts.  Step4 can connect this report to the reply path.
"""

import json
import re
from collections.abc import Iterable, Mapping, Sequence
from typing import Any

from emlis_ai_state_answer_special_cases import (
    state_answer_special_cases_forward_meta,
    state_answer_special_cases_surface_gate_check,
)
from emlis_ai_state_answer_gate_boundary import (
    build_state_answer_gate_boundary_report,
    state_answer_gate_boundary_public_summary,
)
from emlis_ai_two_stage_reception_gate import (
    build_two_stage_reception_gate_report,
    two_stage_reception_gate_public_summary,
)

from emlis_ai_visible_readability_quality import (
    build_visible_readability_quality_report,
    visible_readability_quality_public_summary,
)

VISIBLE_SURFACE_ACCEPTANCE_GATE_VERSION = "emlis.visible_surface_acceptance_gate.v1"
VISIBLE_SURFACE_ACCEPTANCE_GATE_SOURCE = "emlis_visible_surface_acceptance_gate"
VISIBLE_SURFACE_ACCEPTANCE_GATE_STEP = "Step3_Visible_Surface_Acceptance_Gate"

CLASSIFICATION_PASS = "pass"
CLASSIFICATION_YELLOW = "yellow"
CLASSIFICATION_REPAIR_REQUIRED = "repair_required"
CLASSIFICATION_RED = "red"
VISIBLE_SURFACE_CLASSIFICATIONS = (
    CLASSIFICATION_PASS,
    CLASSIFICATION_YELLOW,
    CLASSIFICATION_REPAIR_REQUIRED,
    CLASSIFICATION_RED,
)
# Alias kept for callers/tests that use the full Step3 contract name.
VISIBLE_SURFACE_ACCEPTANCE_CLASSIFICATIONS = VISIBLE_SURFACE_CLASSIFICATIONS

ACTION_ALLOW = "allow"
ACTION_WARN = "warn"
ACTION_RERENDER_SURFACE = "rerender_surface"
ACTION_REROUTE_LOW_INFORMATION = "reroute_low_information"
ACTION_BLOCK = "block"
ACTION_FAIL_CLOSED = "fail_closed"
VISIBLE_SURFACE_ACCEPTANCE_ACTIONS = (
    ACTION_ALLOW,
    ACTION_WARN,
    ACTION_RERENDER_SURFACE,
    ACTION_REROUTE_LOW_INFORMATION,
    ACTION_BLOCK,
    ACTION_FAIL_CLOSED,
)

POSITIVE_TONE_PROFILE_POSITIVE_ONLY = "positive_only"
POSITIVE_TONE_PROFILE_NEGATIVE_ONLY = "negative_only"
POSITIVE_TONE_PROFILE_MIXED = "mixed"
POSITIVE_TONE_PROFILE_SELF_INSIGHT = "self_insight"
POSITIVE_TONE_PROFILE_NEUTRAL_OR_UNKNOWN = "neutral_or_unknown"
VISIBLE_SURFACE_TONE_PROFILES = (
    POSITIVE_TONE_PROFILE_POSITIVE_ONLY,
    POSITIVE_TONE_PROFILE_NEGATIVE_ONLY,
    POSITIVE_TONE_PROFILE_MIXED,
    POSITIVE_TONE_PROFILE_SELF_INSIGHT,
    POSITIVE_TONE_PROFILE_NEUTRAL_OR_UNKNOWN,
)

_STRENGTH_SCORE = {"weak": 1, "medium": 2, "strong": 3}
_POSITIVE_EMOTIONS = {"喜び", "平穏"}
_NEGATIVE_EMOTIONS = {"悲しみ", "怒り", "不安"}
_SELF_INSIGHT_EMOTIONS = {"自己理解"}
_KNOWN_EMOTION_FOCUS_LABELS = tuple(
    sorted(
        _POSITIVE_EMOTIONS
        | _NEGATIVE_EMOTIONS
        | _SELF_INSIGHT_EMOTIONS
        | {"疲れ", "疲労", "焦り", "怖さ", "安心"},
        key=len,
        reverse=True,
    )
)

_NEGATIVE_ANCHOR_MARKERS = (
    "不安",
    "悲しみ",
    "怒り",
    "疲れ",
    "疲労",
    "つらい",
    "辛い",
    "苦しい",
    "しんどい",
    "怖い",
    "焦り",
    "負荷",
    "重さ",
    "重い",
    "無理",
    "眠れ",
)
_BURDEN_SURFACE_MARKERS = (
    "不安の重さ",
    "疲れの重さ",
    "言葉になる前の重さ",
    "軽く流せるものではなさそう",
    "無理かもしれない",
    "無理をして",
    "無理して",
    "無理がある",
    "負荷",
    "重さ",
)
_BRIDGE_MARKERS = (
    "中心に",
    "中心として",
    "近く",
    "そば",
    "周辺",
    "重な",
    "混ざ",
    "並ん",
    "同時",
    "片方だけ",
    "一色では",
    "中に",
    "含ま",
    "その近く",
)
_GREETING_MARKERS = ("Emlisです", "Emlisです。", "Emlisです!", "Emlisです！")

# These are generic surface-level forms that must not be returned as
# ``passed + comment_text``.  They intentionally describe malformed
# nominalization families, not screenshot-specific strings.
_MALFORMED_NOMINALIZATION_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("malformed_nominalization_tari_fragment", re.compile(r"たりこと(?:$|[もがはにをでへ、。,.])")),
    (
        "malformed_nominalization_conditional_fragment",
        re.compile(
            r"(?:なければ|なきゃ|ないと|しないと|しなくては|せねば|しなければ|"
            r"行かなければ|出なければ|やらなければ|取らなければ)こと(?:$|[もがはにをでへ、。,.])"
        ),
    ),
    (
        "malformed_nominalization_prediction_noun_fragment",
        re.compile(r"(?:予感|気配|予定|必要|つもり|はず|可能性|見込み|感じ)こと(?:$|[もがはにをでへ、。,.])"),
    ),
    (
        "residual_koto_splice_fragment",
        re.compile(
            r"(?:ことこと|(?:なければ|なきゃ|ないと|しないと|しなくては|せねば|しなければ|"
            r"行かなければ|出なければ|やらなければ|取らなければ)こと|予感こと|気配こと|予定こと|"
            r"必要こと|つもりこと|はずこと|可能性こと|見込みこと|感じこと)(?:$|[もがはにをでへ、。,.])"
        ),
    ),
    (
        "long_clause_koto_attachment_risk",
        re.compile(
            r"[^。！？!?\n]{18,120}(?:(?:なければ|なきゃ|ないと|しないと|しなくては|せねば)こと|"
            r"(?:予感|気配|予定|必要|可能性|見込み)こと)(?:$|[もがはにをでへ、。,.])"
        ),
    ),
)

_KOTO_SPLICE_CODES = {
    "malformed_nominalization_conditional_fragment",
    "malformed_nominalization_prediction_noun_fragment",
    "residual_koto_splice_fragment",
    "long_clause_koto_attachment_risk",
}

_INTERNAL_ROLE_LABEL_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("achievement", re.compile(r"\bachievement\b", re.IGNORECASE)),
    ("positive_state", re.compile(r"positive[\s_]+state", re.IGNORECASE)),
    ("perfection_fear", re.compile(r"perfection[\s_]+fear", re.IGNORECASE)),
    ("pressure_or_limit", re.compile(r"pressure[\s_]+or[\s_]+limit", re.IGNORECASE)),
    ("role_key", re.compile(r"role_", re.IGNORECASE)),
)

_RELATION_SKELETON_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("same_flow_same_place", re.compile(r"同じ流れが同じ場所")),
    ("same_flow", re.compile(r"同じ流れ")),
    ("same_place", re.compile(r"同じ場所")),
    ("separate_directions", re.compile(r"別々の向き")),
    ("not_reduced_to_one_side", re.compile(r"片方だけに減らさず")),
    ("not_leaning_to_one_side", re.compile(r"片方だけに寄らず")),
    ("overlap_kept", re.compile(r"重なりを保っています")),
    ("not_decided_one_direction", re.compile(r"一方向には決まりきっていません")),
    ("state_not_one_color", re.compile(r"状態が一色ではありません")),
    ("visible_range_not_single_element", re.compile(r"今見えている範囲は一つの要素だけではありません")),
    ("not_single_element", re.compile(r"一つの要素だけではありません")),
    ("overlap_as_aligned", re.compile(r"重なりとして並んで")),
)

_ANALYTIC_REGISTER_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("coverage", re.compile(r"網羅")),
    ("element", re.compile(r"要素")),
    ("range", re.compile(r"範囲")),
)

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
    "public_comment_text",
    "candidate_comment_text",
    "reply_text",
    "replyText",
    "surface_text",
    "realized_text",
    "line_text",
    "body",
    "text",
    "sentence",
    "sentences",
    "phrase",
    "raw_quote",
    "raw_quotes",
    "evidence_text",
    "matched_raw_quote_fragments",
    "observation_text",
    "observationText",
    "reception_text",
    "receptionText",
}

_CONTRACT_TRUE_FLAGS = (
    "raw_input_included",
    "raw_text_included",
    "input_text_included",
    "comment_text_included",
    "comment_text_body_included",
    "rn_visible_contract_changed",
    "response_shape_changed",
    "public_response_key_change",
    "api_route_changed",
    "db_physical_name_changed",
    "display_gate_relaxed",
    "grounding_gate_relaxed",
    "template_gate_relaxed",
    "reader_gate_relaxed",
    "gate_relaxed",
    "fixed_sentence_template_added",
    "input_specific_template_used",
    "external_ai_used",
    "local_llm_used",
)

_REQUIRED_REPORT_KEYS = (
    "version",
    "evaluated",
    "passed",
    "classification",
    "action",
    "rejection_reasons",
    "raw_input_included",
    "comment_text_body_included",
    "rn_visible_contract_changed",
    "public_response_key_change",
    "db_physical_name_changed",
    "display_gate_relaxed",
)


def _clean(value: Any) -> str:
    return str(value or "").strip()


def _safe_mapping(value: Any) -> dict[str, Any]:
    return {str(key): item for key, item in value.items()} if isinstance(value, Mapping) else {}


def _dedupe(values: Iterable[Any] | Any | None) -> list[str]:
    if values is None:
        return []
    if isinstance(values, (str, bytes)):
        source: Iterable[Any] = [values]
    elif isinstance(values, Iterable):
        source = values
    else:
        source = [values]
    out: list[str] = []
    seen: set[str] = set()
    for raw in source:
        item = _clean(raw)
        if item and item not in seen:
            seen.add(item)
            out.append(item)
    return out


def _contains_forbidden_text_payload_key(value: Any) -> bool:
    if isinstance(value, Mapping):
        for key, item in value.items():
            if str(key) in _FORBIDDEN_TEXT_PAYLOAD_KEYS:
                return True
            if _contains_forbidden_text_payload_key(item):
                return True
        return False
    if isinstance(value, (list, tuple, set)):
        return any(_contains_forbidden_text_payload_key(item) for item in value)
    return False


def assert_visible_surface_acceptance_gate_meta_only(
    value: Mapping[str, Any],
    *,
    source: str = VISIBLE_SURFACE_ACCEPTANCE_GATE_SOURCE,
) -> None:
    """Validate that a visible-surface gate report contains only safe meta."""

    data = _safe_mapping(value)
    missing = [key for key in _REQUIRED_REPORT_KEYS if key not in data]
    if missing:
        raise ValueError(f"{source} is missing required keys: {missing}")
    if _contains_forbidden_text_payload_key(data):
        raise ValueError(f"{source} must stay meta-only and must not include text payload keys")
    action = _clean(data.get("action"))
    if action not in VISIBLE_SURFACE_ACCEPTANCE_ACTIONS:
        raise ValueError(f"{source} has invalid action: {action}")
    classification = _clean(data.get("classification"))
    if classification not in VISIBLE_SURFACE_CLASSIFICATIONS:
        raise ValueError(f"{source} has invalid classification: {classification}")
    if not isinstance(data.get("rejection_reasons"), list):
        raise ValueError(f"{source} rejection_reasons must be a list")
    if not isinstance(data.get("passed"), bool) or not isinstance(data.get("evaluated"), bool):
        raise ValueError(f"{source} passed/evaluated must be boolean")
    for flag in _CONTRACT_TRUE_FLAGS:
        if data.get(flag) is True:
            raise ValueError(f"{source} violates fixed contract: {flag}=true")


def build_visible_surface_acceptance_gate_contract_schema() -> dict[str, Any]:
    """Return the Step3 gate report schema as an in-code contract object."""

    return {
        "$id": VISIBLE_SURFACE_ACCEPTANCE_GATE_VERSION,
        "type": "object",
        "required": list(_REQUIRED_REPORT_KEYS),
        "properties": {
            "version": {"const": VISIBLE_SURFACE_ACCEPTANCE_GATE_VERSION},
            "source": {"const": VISIBLE_SURFACE_ACCEPTANCE_GATE_SOURCE},
            "evaluated": {"type": "boolean"},
            "passed": {"type": "boolean"},
            "blocked": {"type": "boolean"},
            "classification": {"type": "string", "enum": list(VISIBLE_SURFACE_CLASSIFICATIONS)},
            "action": {"type": "string", "enum": list(VISIBLE_SURFACE_ACCEPTANCE_ACTIONS)},
            "rejection_reasons": {"type": "array", "items": {"type": "string"}, "maxItems": 20},
            "warning_reasons": {"type": "array", "items": {"type": "string"}, "maxItems": 20},
            "visible_header_dominant_emotion_present": {"type": "boolean"},
            "visible_header_dominant_emotion_source": {"type": "string"},
            "opening_emotion_focus_present": {"type": "boolean"},
            "dominant_emotion_bridge_present": {"type": "boolean"},
            "selected_emotion_count": {"type": "integer", "minimum": 0},
            "secondary_emotion_focus_detected": {"type": "boolean"},
            "unselected_emotion_focus_detected": {"type": "boolean"},
            "negative_text_anchor_present": {"type": "boolean"},
            "positive_tone_profile": {"type": "string", "enum": list(VISIBLE_SURFACE_TONE_PROFILES)},
            "burden_surface_without_anchor_detected": {"type": "boolean"},
            "malformed_nominalization_detected": {"type": "boolean"},
            "malformed_nominalization_codes": {"type": "array", "items": {"type": "string"}, "maxItems": 20},
            "koto_splice_detected": {"type": "boolean"},
            "koto_splice_codes": {"type": "array", "items": {"type": "string"}, "maxItems": 20},
            "internal_role_label_marker_count": {"type": "integer", "minimum": 0},
            "internal_role_label_marker_codes": {"type": "array", "items": {"type": "string"}, "maxItems": 20},
            "internal_role_label_leak_detected": {"type": "boolean"},
            "relation_skeleton_marker_count": {"type": "integer", "minimum": 0},
            "relation_skeleton_marker_codes": {"type": "array", "items": {"type": "string"}, "maxItems": 20},
            "relation_skeleton_major": {"type": "boolean"},
            "analytic_register_leak_count": {"type": "integer", "minimum": 0},
            "analytic_register_leak_codes": {"type": "array", "items": {"type": "string"}, "maxItems": 20},
            "analytic_register_leak": {"type": "boolean"},
            "surface_repair_requested": {"type": "boolean"},
            "repair_reason_family": {"type": "string"},
            "rerender_allowed": {"type": "boolean"},
            "rerender_attempted": {"type": "boolean"},
            "raw_input_included": {"const": False},
            "raw_text_included": {"const": False},
            "input_text_included": {"const": False},
            "comment_text_included": {"const": False},
            "comment_text_body_included": {"const": False},
            "rn_visible_contract_changed": {"const": False},
            "response_shape_changed": {"const": False},
            "public_response_key_change": {"const": False},
            "api_route_changed": {"const": False},
            "db_physical_name_changed": {"const": False},
            "display_gate_relaxed": {"const": False},
            "grounding_gate_relaxed": {"const": False},
            "template_gate_relaxed": {"const": False},
            "fixed_sentence_template_added": {"const": False},
            "external_ai_used": {"const": False},
            "local_llm_used": {"const": False},
        },
    }


def build_visible_surface_acceptance_gate_schema() -> dict[str, Any]:
    """Alias for the Step3 in-code report schema contract."""

    return build_visible_surface_acceptance_gate_contract_schema()


def _emotion_item_from_raw(raw: Any) -> dict[str, str] | None:
    if isinstance(raw, Mapping):
        label = _clean(
            raw.get("type")
            or raw.get("label")
            or raw.get("emotion")
            or raw.get("name")
            or raw.get("value")
        )
        strength = _clean(raw.get("strength") or raw.get("intensity") or "medium") or "medium"
    elif isinstance(raw, (list, tuple)) and raw:
        label = _clean(raw[0])
        strength = _clean(raw[1] if len(raw) > 1 else "medium") or "medium"
    else:
        label = _clean(raw)
        strength = "medium"
    if not label:
        return None
    return {"type": label, "strength": strength}


def _coerce_selected_emotions(
    *,
    selected_emotions: Sequence[Any] | None,
    emotion_details: Sequence[Any] | None,
    emotions: Sequence[Any] | None,
    current_input: Mapping[str, Any] | None,
) -> list[dict[str, str]]:
    current = _safe_mapping(current_input)
    source: Any = selected_emotions
    if source is None:
        source = emotion_details if emotion_details is not None else current.get("emotion_details")
    if source is None:
        source = emotions if emotions is not None else current.get("emotions")
    if not isinstance(source, Sequence) or isinstance(source, (str, bytes)):
        return []
    items: list[dict[str, str]] = []
    for raw in source:
        item = _emotion_item_from_raw(raw)
        if item is not None:
            items.append(item)
    return items


def _dominant_emotion_label(items: Sequence[Mapping[str, str]]) -> str:
    if not items:
        return ""
    dominant = items[0]
    dominant_score = _STRENGTH_SCORE.get(_clean(dominant.get("strength")), 0)
    for item in items:
        score = _STRENGTH_SCORE.get(_clean(item.get("strength")), 0)
        if score > dominant_score:
            dominant = item
            dominant_score = score
    return _clean(dominant.get("type"))

def infer_visible_header_dominant_emotion(
    selected_emotions: Sequence[Any] | None = None,
    *,
    emotion_details: Sequence[Any] | None = None,
    emotions: Sequence[Any] | None = None,
) -> str:
    """Infer RN-visible dominant emotion: strongest score, first tie wins."""

    return _dominant_emotion_label(
        _coerce_selected_emotions(
            selected_emotions=selected_emotions,
            emotion_details=emotion_details,
            emotions=emotions,
            current_input=None,
        )
    )


def _sentences_from_text(text: str) -> list[str]:
    chunks = re.split(r"(?<=[。！？!?])|[\r\n]+", text)
    out: list[str] = []
    for chunk in chunks:
        sentence = _clean(chunk).strip("。！？!?")
        if sentence:
            out.append(sentence)
    return out


def _is_greeting_sentence(sentence: str) -> bool:
    if any(marker in sentence for marker in _GREETING_MARKERS):
        return True
    # Covers local display-name greetings such as "Userさん、Emlisです".
    return bool(re.search(r"Emlis\s*です", sentence))


def _opening_content_sentences(comment_text: Any, *, limit: int = 2) -> list[str]:
    text = _clean(comment_text)
    if not text:
        return []
    sentences = [sentence for sentence in _sentences_from_text(text) if not _is_greeting_sentence(sentence)]
    return sentences[: max(1, int(limit))]


def _focus_pattern_for_emotion(emotion: str) -> re.Pattern[str]:
    escaped = re.escape(emotion)
    return re.compile(
        rf"(?:^|[、\s])(?:今は、?)?{escaped}"
        rf"(?:の(?:重さ|強さ|感じ|気持ち)|が(?:先|中心|前面|強く|強い)|を中心|として|は(?:先|中心))"
    )


def _focused_emotions(sentences: Sequence[str], *, selected_labels: Sequence[str]) -> list[str]:
    known_labels = tuple(sorted(set(_KNOWN_EMOTION_FOCUS_LABELS) | set(selected_labels), key=len, reverse=True))
    focused: list[str] = []
    for sentence in sentences:
        for label in known_labels:
            if label and label in sentence and _focus_pattern_for_emotion(label).search(sentence):
                focused.append(label)
    return _dedupe(focused)


def _dominant_bridge_present(
    *,
    sentences: Sequence[str],
    dominant_label: str,
    secondary_labels: Sequence[str],
) -> bool:
    if not dominant_label or not secondary_labels:
        return False
    window = "。".join(sentences)
    if dominant_label not in window:
        return False
    present_secondary_labels = [label for label in secondary_labels if label in window]
    if not present_secondary_labels:
        return False
    if any(marker in window for marker in _BRIDGE_MARKERS):
        return True
    return any(re.search(rf"{re.escape(dominant_label)}.*{re.escape(label)}も", window) for label in present_secondary_labels)


def _negative_anchor_present(
    *,
    current_text: Any,
    current_text_negative_anchor_present: bool | None,
    current_input: Mapping[str, Any] | None,
) -> bool:
    if current_text_negative_anchor_present is True:
        return True
    if current_text_negative_anchor_present is False:
        return False
    current = _safe_mapping(current_input)
    text = _clean(
        current_text
        or current.get("memo")
        or current.get("memo_text")
        or current.get("text")
        or current.get("input_text")
        or current.get("comment_text")
    )
    return any(marker in text for marker in _NEGATIVE_ANCHOR_MARKERS)


def _tone_profile(*, selected_labels: Sequence[str], negative_anchor_present: bool) -> str:
    labels = set(selected_labels)
    if not labels:
        return POSITIVE_TONE_PROFILE_NEUTRAL_OR_UNKNOWN
    has_positive = bool(labels & _POSITIVE_EMOTIONS)
    has_negative = bool(labels & _NEGATIVE_EMOTIONS)
    has_self_insight = bool(labels & _SELF_INSIGHT_EMOTIONS)
    if has_self_insight and not has_positive and not has_negative and labels <= _SELF_INSIGHT_EMOTIONS:
        return POSITIVE_TONE_PROFILE_SELF_INSIGHT
    if has_positive and not has_negative and not negative_anchor_present:
        return POSITIVE_TONE_PROFILE_POSITIVE_ONLY
    if has_negative and not has_positive:
        return POSITIVE_TONE_PROFILE_NEGATIVE_ONLY
    if has_positive and (has_negative or negative_anchor_present):
        return POSITIVE_TONE_PROFILE_MIXED
    return POSITIVE_TONE_PROFILE_NEUTRAL_OR_UNKNOWN


def _burden_surface_without_anchor(*, sentences: Sequence[str], profile: str, negative_anchor_present: bool) -> bool:
    if profile != POSITIVE_TONE_PROFILE_POSITIVE_ONLY or negative_anchor_present:
        return False
    window = "。".join(sentences)
    return any(marker in window for marker in _BURDEN_SURFACE_MARKERS)


def _malformed_nominalization_codes(comment_text: Any) -> list[str]:
    text = _clean(comment_text)
    if not text:
        return []
    return _dedupe(code for code, pattern in _MALFORMED_NOMINALIZATION_PATTERNS if pattern.search(text))


def _internal_role_label_marker_codes(comment_text: Any) -> list[str]:
    text = _clean(comment_text)
    if not text:
        return []
    return _dedupe(code for code, pattern in _INTERNAL_ROLE_LABEL_PATTERNS if pattern.search(text))


def _relation_skeleton_marker_codes(comment_text: Any) -> list[str]:
    text = _clean(comment_text)
    if not text:
        return []
    codes = _dedupe(code for code, pattern in _RELATION_SKELETON_PATTERNS if pattern.search(text))
    if "same_flow_same_place" in codes:
        codes = [code for code in codes if code not in {"same_flow", "same_place"}]
    if "visible_range_not_single_element" in codes and "not_single_element" in codes:
        codes = [code for code in codes if code != "not_single_element"]
    return codes


def _input_derived_marker_values(
    *,
    current_text: Any,
    current_input: Mapping[str, Any] | None,
    input_derived_surface_markers: Sequence[Any] | None,
) -> list[str]:
    current = _safe_mapping(current_input)
    values: list[Any] = []
    if input_derived_surface_markers is not None:
        values.extend(input_derived_surface_markers)
    for key in ("input_derived_surface_markers", "inputDerivedSurfaceMarkers"):
        raw = current.get(key)
        if isinstance(raw, Sequence) and not isinstance(raw, (str, bytes)):
            values.extend(raw)
    text = _clean(
        current_text
        or current.get("memo")
        or current.get("memo_text")
        or current.get("text")
        or current.get("input_text")
    )
    if text:
        values.append(text)
    return _dedupe(values)


def _analytic_register_leak_codes(
    comment_text: Any,
    *,
    current_text: Any,
    current_input: Mapping[str, Any] | None,
    input_derived_surface_markers: Sequence[Any] | None,
) -> list[str]:
    text = _clean(comment_text)
    if not text:
        return []
    input_derived_values = _input_derived_marker_values(
        current_text=current_text,
        current_input=current_input,
        input_derived_surface_markers=input_derived_surface_markers,
    )
    out: list[str] = []
    for code, pattern in _ANALYTIC_REGISTER_PATTERNS:
        if not pattern.search(text):
            continue
        # Input-derived analytic wording is not over-read.  It may still be
        # repaired when stacked with mechanical relation skeletons, but the leak
        # counter should not mark it as non-derived.
        if any(pattern.search(value) for value in input_derived_values):
            continue
        out.append(code)
    return _dedupe(out)


def _state_answer_special_cases_from_inputs(
    *,
    state_answer_special_cases: Any = None,
    composer_meta: Mapping[str, Any] | None = None,
) -> dict[str, Any]:
    explicit = state_answer_special_cases_forward_meta(state_answer_special_cases)
    if explicit:
        return explicit
    meta = _safe_mapping(composer_meta)
    for key in ("state_answer_special_cases", "state_answer_special_cases_payload", "special_handling"):
        found = state_answer_special_cases_forward_meta(meta.get(key))
        if found:
            return found
    contract = _safe_mapping(meta.get("state_answer_surface_contract"))
    for key in ("special_handling", "state_answer_special_cases", "state_answer_special_cases_payload"):
        found = state_answer_special_cases_forward_meta(contract.get(key))
        if found:
            return found
    return {}


def _repair_reason_family(
    *,
    red_reasons: Sequence[str],
    repair_reasons: Sequence[str],
    warning_reasons: Sequence[str],
) -> str:
    reasons = set(red_reasons) | set(repair_reasons) | set(warning_reasons)
    if _KOTO_SPLICE_CODES & reasons:
        return "koto_splice"
    relation_reasons = {
        "surface_relation_skeleton_major",
        "surface_relation_skeleton_stack",
        "surface_relation_skeleton_minor",
        "analytic_register_leak",
    }
    if relation_reasons & reasons:
        return "relation_skeleton"
    if any(reason.startswith("emotion_focus_") for reason in reasons):
        return "emotion_focus"
    if "positive_tone_over_burden_without_anchor" in reasons:
        return "tone_profile"
    if reasons:
        return "surface_general"
    return "none"


def _action_for_classification(
    *,
    classification: str,
    rerender_allowed: bool,
    rerender_attempted: bool,
    low_information_reroute_allowed: bool,
) -> str:
    if classification == CLASSIFICATION_PASS:
        return ACTION_ALLOW
    if classification == CLASSIFICATION_YELLOW:
        return ACTION_WARN
    if rerender_allowed and not rerender_attempted:
        return ACTION_RERENDER_SURFACE
    if low_information_reroute_allowed and not rerender_attempted:
        return ACTION_REROUTE_LOW_INFORMATION
    if classification == CLASSIFICATION_RED:
        return ACTION_BLOCK
    return ACTION_FAIL_CLOSED


def build_visible_surface_acceptance_gate_report(
    *,
    comment_text: Any = "",
    selected_emotions: Sequence[Any] | None = None,
    emotion_details: Sequence[Any] | None = None,
    emotions: Sequence[Any] | None = None,
    visible_header_dominant_emotion: Any = "",
    current_input: Mapping[str, Any] | None = None,
    current_text: Any = "",
    input_derived_surface_markers: Sequence[Any] | None = None,
    current_text_negative_anchor_present: bool | None = None,
    negative_text_anchor_present: bool | None = None,
    composer_meta: Mapping[str, Any] | None = None,
    state_answer_special_cases: Any = None,
    state_answer_surface_contract: Any = None,
    two_stage_reception_gate_required: bool = False,
    shared_reception_evidence: Any = None,
    reception_mode: Any = None,
    rerender_allowed: bool = True,
    rerender_attempted: bool = False,
    low_information_reroute_allowed: bool = False,
) -> dict[str, Any]:
    """Build a meta-only Step3 visible-surface acceptance report.

    ``comment_text`` and optional current input text are used only as in-memory
    evaluation material.  They are never copied into the returned report.
    """

    selected_items = _coerce_selected_emotions(
        selected_emotions=selected_emotions,
        emotion_details=emotion_details,
        emotions=emotions,
        current_input=current_input,
    )
    selected_labels = [_clean(item.get("type")) for item in selected_items if _clean(item.get("type"))]
    computed_dominant = _dominant_emotion_label(selected_items)
    provided_dominant = _clean(visible_header_dominant_emotion)
    dominant_label = provided_dominant or computed_dominant
    dominant_source = "provided" if provided_dominant else "computed" if computed_dominant else "unavailable"

    opening_sentences = _opening_content_sentences(comment_text, limit=2)
    focused_labels = _focused_emotions(opening_sentences, selected_labels=selected_labels)
    secondary_labels = [label for label in selected_labels if label != dominant_label]
    focused_secondary_labels = [label for label in focused_labels if label in secondary_labels]
    unselected_focused_labels = [label for label in focused_labels if label not in selected_labels]
    bridge_present = _dominant_bridge_present(
        sentences=opening_sentences,
        dominant_label=dominant_label,
        secondary_labels=secondary_labels,
    )
    effective_negative_anchor_flag = (
        negative_text_anchor_present
        if negative_text_anchor_present is not None
        else current_text_negative_anchor_present
    )
    negative_anchor = _negative_anchor_present(
        current_text=current_text,
        current_text_negative_anchor_present=effective_negative_anchor_flag,
        current_input=current_input,
    )
    profile = _tone_profile(selected_labels=selected_labels, negative_anchor_present=negative_anchor)
    burden_without_anchor = _burden_surface_without_anchor(
        sentences=opening_sentences,
        profile=profile,
        negative_anchor_present=negative_anchor,
    )
    malformed_codes = _malformed_nominalization_codes(comment_text)
    koto_splice_codes = [code for code in malformed_codes if code in _KOTO_SPLICE_CODES]
    internal_role_label_codes = _internal_role_label_marker_codes(comment_text)
    internal_role_label_marker_count = len(internal_role_label_codes)
    internal_role_label_leak_detected = internal_role_label_marker_count > 0
    relation_skeleton_codes = _relation_skeleton_marker_codes(comment_text)
    relation_skeleton_marker_count = len(relation_skeleton_codes)
    relation_skeleton_major = relation_skeleton_marker_count >= 2
    analytic_register_codes = _analytic_register_leak_codes(
        comment_text,
        current_text=current_text,
        current_input=current_input,
        input_derived_surface_markers=input_derived_surface_markers,
    )
    analytic_register_leak_count = len(analytic_register_codes)
    special_cases_meta = _state_answer_special_cases_from_inputs(
        state_answer_special_cases=state_answer_special_cases,
        composer_meta=composer_meta,
    )
    special_case_surface_report = state_answer_special_cases_surface_gate_check(
        visible_surface=comment_text,
        special_cases=special_cases_meta,
    )
    state_answer_gate_boundary_report = build_state_answer_gate_boundary_report(
        visible_surface=comment_text,
        state_answer_surface_contract=state_answer_surface_contract,
        state_answer_special_cases=special_cases_meta,
        composer_meta=composer_meta,
        current_input=current_input,
    )
    # Phase16-1: do not activate the two-stage gate only when labels already
    # exist in the body.  When composer_meta / state answer contract marks
    # labelled_two_stage_text as required, leave ``two_stage_required`` unset so
    # build_two_stage_reception_gate_report can derive the requirement from the
    # meta and fail closed on missing labels.
    two_stage_required_override = True if two_stage_reception_gate_required else None
    two_stage_reception_gate_report = build_two_stage_reception_gate_report(
        comment_text=comment_text,
        state_answer_surface_contract=state_answer_surface_contract,
        composer_meta=composer_meta,
        shared_reception_evidence=shared_reception_evidence,
        reception_mode=reception_mode,
        current_input=current_input,
        two_stage_required=two_stage_required_override,
    )
    two_stage_gate_active = bool(two_stage_reception_gate_report.get("evaluated"))
    special_case_blockers = _dedupe(special_case_surface_report.get("surface_blocker_reasons") or [])
    state_answer_gate_boundary_blockers = _dedupe(
        state_answer_gate_boundary_report.get("surface_blocker_reasons")
        or state_answer_gate_boundary_report.get("rejection_reasons")
        or []
    )
    two_stage_gate_blockers = _dedupe(
        two_stage_reception_gate_report.get("surface_blocker_reasons")
        or two_stage_reception_gate_report.get("rejection_reasons")
        or []
    )
    two_stage_unavailable_reason_codes = _dedupe(
        two_stage_reception_gate_report.get("two_stage_unavailable_reason_codes")
        or two_stage_reception_gate_report.get("phase16_7_unavailable_reason_codes")
        or []
    )
    visible_readability_quality_report = build_visible_readability_quality_report(
        comment_text=comment_text,
    )
    visible_readability_hard_blockers = _dedupe(
        visible_readability_quality_report.get("hard_block_reasons") or []
    )
    visible_readability_repair_reasons = _dedupe(
        visible_readability_quality_report.get("soft_repair_reasons") or []
    )

    rejection_reasons: list[str] = []
    warning_reasons: list[str] = []
    red_reasons: list[str] = []
    repair_reasons: list[str] = []

    if malformed_codes:
        red_reasons.extend(["malformed_phrase_unit", *malformed_codes])
    if internal_role_label_leak_detected:
        red_reasons.extend([
            "two_stage_internal_role_label_leak",
            "two_stage_complete_surface_internal_label_leak",
        ])
    if relation_skeleton_major:
        repair_reasons.append("surface_relation_skeleton_major")
        if relation_skeleton_marker_count >= 3:
            repair_reasons.append("surface_relation_skeleton_stack")
    elif relation_skeleton_marker_count == 1:
        warning_reasons.append("surface_relation_skeleton_minor")
    if analytic_register_leak_count:
        if relation_skeleton_major or analytic_register_leak_count >= 2:
            repair_reasons.append("analytic_register_leak")
        else:
            warning_reasons.append("analytic_register_leak")
    if burden_without_anchor:
        repair_reasons.append("positive_tone_over_burden_without_anchor")
    if focused_secondary_labels and not bridge_present:
        repair_reasons.append("emotion_focus_unbridged_secondary")
    if unselected_focused_labels and not negative_anchor and not burden_without_anchor:
        red_reasons.append("emotion_focus_unselected_without_evidence")
    if special_case_blockers:
        red_reasons.extend(special_case_blockers)
    if state_answer_gate_boundary_blockers:
        red_reasons.extend(state_answer_gate_boundary_blockers)
    if two_stage_gate_blockers:
        red_reasons.extend(two_stage_gate_blockers)
    if visible_readability_hard_blockers:
        red_reasons.extend(visible_readability_hard_blockers)
    if visible_readability_repair_reasons:
        repair_reasons.extend(visible_readability_repair_reasons)

    rejection_reasons.extend(red_reasons)
    rejection_reasons.extend(repair_reasons)
    rejection_reasons = _dedupe(rejection_reasons)
    warning_reasons = _dedupe(warning_reasons)

    if red_reasons:
        classification = CLASSIFICATION_RED
    elif repair_reasons:
        classification = CLASSIFICATION_REPAIR_REQUIRED
    elif warning_reasons:
        classification = CLASSIFICATION_YELLOW
    else:
        classification = CLASSIFICATION_PASS

    action = _action_for_classification(
        classification=classification,
        rerender_allowed=bool(rerender_allowed) and not bool(visible_readability_hard_blockers),
        rerender_attempted=bool(rerender_attempted),
        low_information_reroute_allowed=bool(low_information_reroute_allowed),
    )
    passed = classification == CLASSIFICATION_PASS and action == ACTION_ALLOW
    surface_repair_requested = action in {ACTION_RERENDER_SURFACE, ACTION_REROUTE_LOW_INFORMATION}
    repair_reason_family = _repair_reason_family(
        red_reasons=red_reasons,
        repair_reasons=repair_reasons,
        warning_reasons=warning_reasons,
    )
    report: dict[str, Any] = {
        "version": VISIBLE_SURFACE_ACCEPTANCE_GATE_VERSION,
        "schema_version": VISIBLE_SURFACE_ACCEPTANCE_GATE_VERSION,
        "source": VISIBLE_SURFACE_ACCEPTANCE_GATE_SOURCE,
        "source_step": VISIBLE_SURFACE_ACCEPTANCE_GATE_STEP,
        "step": VISIBLE_SURFACE_ACCEPTANCE_GATE_STEP,
        "visible_surface_acceptance_gate_ready": True,
        "visible_surface_acceptance_gate_contract_ready": True,
        "evaluated": True,
        "passed": bool(passed),
        "blocked": not bool(passed),
        "classification": classification,
        "action": action,
        "rerender_recommended": action == ACTION_RERENDER_SURFACE,
        "reroute_low_information_recommended": action == ACTION_REROUTE_LOW_INFORMATION,
        "rejection_reasons": list(rejection_reasons),
        "warning_reasons": list(warning_reasons),
        "visible_header_dominant_emotion_present": bool(dominant_label),
        "visible_header_dominant_emotion_source": dominant_source,
        "opening_emotion_focus_present": bool(focused_labels),
        "dominant_emotion_bridge_present": bool(bridge_present),
        "selected_emotion_count": len(selected_labels),
        "secondary_emotion_focus_detected": bool(focused_secondary_labels),
        "unselected_emotion_focus_detected": bool(unselected_focused_labels),
        "negative_text_anchor_present": bool(negative_anchor),
        "positive_tone_profile": profile,
        "burden_surface_without_anchor_detected": bool(burden_without_anchor),
        "malformed_nominalization_detected": bool(malformed_codes),
        "malformed_nominalization_codes": list(malformed_codes),
        "koto_splice_detected": bool(koto_splice_codes),
        "koto_splice_codes": list(koto_splice_codes),
        "internal_role_label_marker_count": int(internal_role_label_marker_count),
        "internal_role_label_marker_codes": list(internal_role_label_codes),
        "internal_role_label_leak_detected": bool(internal_role_label_leak_detected),
        "relation_skeleton_marker_count": int(relation_skeleton_marker_count),
        "relation_skeleton_marker_codes": list(relation_skeleton_codes),
        "relation_skeleton_major": bool(relation_skeleton_major),
        "analytic_register_leak_count": int(analytic_register_leak_count),
        "analytic_register_leak_codes": list(analytic_register_codes),
        "analytic_register_leak": bool(analytic_register_codes),
        "visible_readability_quality": visible_readability_quality_public_summary(visible_readability_quality_report),
        "visible_readability_quality_passed": bool(visible_readability_quality_report.get("passed")),
        "visible_readability_quality_classification": visible_readability_quality_report.get("classification"),
        "visible_readability_quality_action": visible_readability_quality_report.get("action"),
        "visible_readability_quality_rejection_reasons": list(
            visible_readability_quality_report.get("hard_block_reasons") or []
        ),
        "visible_readability_quality_repair_reasons": list(
            visible_readability_quality_report.get("soft_repair_reasons") or []
        ),
        "visible_readability_quality_comment_text_body_included": False,
        "visible_readability_quality_raw_input_included": False,
        "visible_readability_quality_public_response_key_added": False,
        "visible_readability_quality_rn_visible_contract_changed": False,
        "state_answer_special_case_surface_guard": _safe_mapping(special_case_surface_report),
        "state_answer_special_case_guard_reasons": list(special_case_blockers),
        "state_answer_special_case_allowed_exception_ids": list(special_case_surface_report.get("allowed_exception_ids_detected") or []),
        "self_denial_limited_counter_opinion_allowed_by_special_case": bool(
            special_case_surface_report.get("self_denial_limited_counter_opinion_allowed")
        ),
        "anger_target_judgement_agreement_blocked_by_special_case": bool(
            special_case_surface_report.get("anger_target_judgement_agreement_detected")
        ),
        "state_answer_gate_boundary": state_answer_gate_boundary_public_summary(state_answer_gate_boundary_report),
        "state_answer_gate_boundary_rejection_reasons": list(state_answer_gate_boundary_blockers),
        "state_answer_gate_boundary_terminal_surface_block": bool(
            state_answer_gate_boundary_report.get("terminal_surface_block") or state_answer_gate_boundary_blockers
        ),
        "state_answer_forbidden_claim_reasons": list(state_answer_gate_boundary_report.get("forbidden_claim_reasons") or []),
        "state_answer_allowed_exception_ids_detected": list(
            state_answer_gate_boundary_report.get("allowed_exception_ids_detected")
            or state_answer_gate_boundary_report.get("allowed_exception_ids")
            or []
        ),
        "two_stage_reception_gate": two_stage_reception_gate_public_summary(two_stage_reception_gate_report),
        "two_stage_reception_gate_rejection_reasons": list(two_stage_gate_blockers),
        "phase16_7_unavailable_reason_codes": list(two_stage_unavailable_reason_codes),
        "two_stage_unavailable_reason_codes": list(two_stage_unavailable_reason_codes),
        "two_stage_required_but_unrealized": "two_stage_required_but_unrealized" in two_stage_gate_blockers,
        "two_stage_complete_surface_blocked_by_gate": bool(
            "two_stage_complete_surface_blocked_by_gate" in two_stage_gate_blockers
        ),
        "two_stage_reception_gate_terminal_surface_block": bool(
            two_stage_reception_gate_report.get("terminal_surface_block") or two_stage_gate_blockers
        ),
        "two_stage_reception_gate_required": bool(two_stage_gate_active),
        "two_stage_reception_gate_public_meta_summary_only": True,
        "state_answer_public_meta_summary_only": True,
        "state_answer_contract_body_returned": False,
        "state_answer_raw_evidence_included": False,
        "self_denial_limited_counter_opinion_allowed_by_state_answer_boundary": bool(
            state_answer_gate_boundary_report.get("self_denial_limited_counter_opinion_allowed")
        ),
        "anger_target_judgement_agreement_blocked_by_state_answer_boundary": bool(
            state_answer_gate_boundary_report.get("anger_target_judgement_agreement_blocked")
        ),
        "surface_repair_requested": bool(surface_repair_requested),
        "repair_reason_family": repair_reason_family,
        "rerender_allowed": bool(rerender_allowed),
        "rerender_attempted": bool(rerender_attempted),
        "low_information_reroute_allowed": bool(low_information_reroute_allowed),
        "raw_input_included": False,
        "raw_text_included": False,
        "input_text_included": False,
        "comment_text_included": False,
        "comment_text_body_included": False,
        "rn_visible_contract_changed": False,
        "response_shape_changed": False,
        "public_response_key_change": False,
        "api_route_changed": False,
        "db_physical_name_changed": False,
        "display_gate_relaxed": False,
        "grounding_gate_relaxed": False,
        "template_gate_relaxed": False,
        "reader_gate_relaxed": False,
        "gate_relaxed": False,
        "fixed_sentence_template_added": False,
        "input_specific_template_used": False,
        "external_ai_used": False,
        "local_llm_used": False,
    }
    assert_visible_surface_acceptance_gate_meta_only(report)
    return report


def evaluate_visible_surface_acceptance_gate(**kwargs: Any) -> dict[str, Any]:
    """Alias kept for call sites that use evaluator naming."""

    return build_visible_surface_acceptance_gate_report(**kwargs)


def build_visible_surface_acceptance_gate_contract_meta() -> dict[str, Any]:
    report = {
        "version": VISIBLE_SURFACE_ACCEPTANCE_GATE_VERSION,
        "schema_version": VISIBLE_SURFACE_ACCEPTANCE_GATE_VERSION,
        "source": VISIBLE_SURFACE_ACCEPTANCE_GATE_SOURCE,
        "source_step": VISIBLE_SURFACE_ACCEPTANCE_GATE_STEP,
        "step": VISIBLE_SURFACE_ACCEPTANCE_GATE_STEP,
        "visible_surface_acceptance_gate_ready": True,
        "visible_surface_acceptance_gate_contract_ready": True,
        "evaluated": True,
        "passed": True,
        "blocked": False,
        "classification": CLASSIFICATION_PASS,
        "action": ACTION_ALLOW,
        "rejection_reasons": [],
        "warning_reasons": [],
        "visible_header_dominant_emotion_present": False,
        "visible_header_dominant_emotion_source": "unavailable",
        "opening_emotion_focus_present": False,
        "dominant_emotion_bridge_present": False,
        "selected_emotion_count": 0,
        "secondary_emotion_focus_detected": False,
        "unselected_emotion_focus_detected": False,
        "negative_text_anchor_present": False,
        "positive_tone_profile": POSITIVE_TONE_PROFILE_NEUTRAL_OR_UNKNOWN,
        "burden_surface_without_anchor_detected": False,
        "malformed_nominalization_detected": False,
        "malformed_nominalization_codes": [],
        "koto_splice_detected": False,
        "koto_splice_codes": [],
        "internal_role_label_marker_count": 0,
        "internal_role_label_marker_codes": [],
        "internal_role_label_leak_detected": False,
        "relation_skeleton_marker_count": 0,
        "relation_skeleton_marker_codes": [],
        "relation_skeleton_major": False,
        "analytic_register_leak_count": 0,
        "analytic_register_leak_codes": [],
        "analytic_register_leak": False,
        "visible_readability_quality": visible_readability_quality_public_summary({"evaluated": True, "passed": True}),
        "visible_readability_quality_passed": True,
        "visible_readability_quality_classification": "passed",
        "visible_readability_quality_action": "allow",
        "visible_readability_quality_rejection_reasons": [],
        "visible_readability_quality_repair_reasons": [],
        "visible_readability_quality_comment_text_body_included": False,
        "visible_readability_quality_raw_input_included": False,
        "visible_readability_quality_public_response_key_added": False,
        "visible_readability_quality_rn_visible_contract_changed": False,
        "surface_repair_requested": False,
        "repair_reason_family": "none",
        "rerender_allowed": False,
        "rerender_attempted": False,
        "low_information_reroute_allowed": False,
        "raw_input_included": False,
        "raw_text_included": False,
        "input_text_included": False,
        "comment_text_included": False,
        "comment_text_body_included": False,
        "rn_visible_contract_changed": False,
        "response_shape_changed": False,
        "public_response_key_change": False,
        "api_route_changed": False,
        "db_physical_name_changed": False,
        "display_gate_relaxed": False,
        "grounding_gate_relaxed": False,
        "template_gate_relaxed": False,
        "reader_gate_relaxed": False,
        "gate_relaxed": False,
        "fixed_sentence_template_added": False,
        "input_specific_template_used": False,
        "external_ai_used": False,
        "local_llm_used": False,
    }
    assert_visible_surface_acceptance_gate_meta_only(report)
    return report


def dump_visible_surface_acceptance_gate_report(report: Mapping[str, Any]) -> str:
    data = dict(report or {})
    data.setdefault("raw_input_included", False)
    data.setdefault("raw_text_included", False)
    data.setdefault("input_text_included", False)
    data.setdefault("comment_text_included", False)
    data.setdefault("comment_text_body_included", False)
    assert_visible_surface_acceptance_gate_meta_only(data)
    return json.dumps(data, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


__all__ = [
    "ACTION_ALLOW",
    "ACTION_BLOCK",
    "ACTION_FAIL_CLOSED",
    "ACTION_RERENDER_SURFACE",
    "ACTION_REROUTE_LOW_INFORMATION",
    "ACTION_WARN",
    "CLASSIFICATION_PASS",
    "CLASSIFICATION_RED",
    "CLASSIFICATION_REPAIR_REQUIRED",
    "CLASSIFICATION_YELLOW",
    "POSITIVE_TONE_PROFILE_MIXED",
    "POSITIVE_TONE_PROFILE_NEGATIVE_ONLY",
    "POSITIVE_TONE_PROFILE_NEUTRAL_OR_UNKNOWN",
    "POSITIVE_TONE_PROFILE_POSITIVE_ONLY",
    "POSITIVE_TONE_PROFILE_SELF_INSIGHT",
    "VISIBLE_SURFACE_ACCEPTANCE_ACTIONS",
    "VISIBLE_SURFACE_ACCEPTANCE_CLASSIFICATIONS",
    "VISIBLE_SURFACE_ACCEPTANCE_GATE_SOURCE",
    "VISIBLE_SURFACE_ACCEPTANCE_GATE_STEP",
    "VISIBLE_SURFACE_ACCEPTANCE_GATE_VERSION",
    "VISIBLE_SURFACE_CLASSIFICATIONS",
    "VISIBLE_SURFACE_TONE_PROFILES",
    "assert_visible_surface_acceptance_gate_meta_only",
    "build_visible_surface_acceptance_gate_contract_meta",
    "build_visible_surface_acceptance_gate_contract_schema",
    "build_visible_surface_acceptance_gate_schema",
    "build_visible_surface_acceptance_gate_report",
    "dump_visible_surface_acceptance_gate_report",
    "evaluate_visible_surface_acceptance_gate",
    "infer_visible_header_dominant_emotion",
]
