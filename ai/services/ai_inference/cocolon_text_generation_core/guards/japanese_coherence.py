# -*- coding: utf-8 -*-
from __future__ import annotations

"""Core-agnostic Japanese coherence guard.

The guard only checks mechanical breakage surfaces shared across Cocolon's
text-output cores. It does not decide Emlis/Piece/Analysis tone.
"""

import re
from typing import Any, Iterable, Pattern, Tuple

from cocolon_text_generation_core.guards.base import GuardResult, make_guard_result, normalize_text, split_sentences, token_list

JAPANESE_COHERENCE_GUARD_NAME = "cocolon_text_generation_core.guards.japanese_coherence.v1"
GUARD_NAME = JAPANESE_COHERENCE_GUARD_NAME

QUALITY_FLAG_JAPANESE_COHERENCE_FAILED = "japanese_coherence_failed"
QUALITY_FLAG_EMOTION_LABEL_BODY = "emotion_label_body_line"
QUALITY_FLAG_FORBIDDEN_SURFACE = "forbidden_surface_pattern"
QUALITY_FLAG_GENERIC_RELATION_SUFFIX = "generic_relation_suffix"
QUALITY_FLAG_INTERNAL_MARKER_VISIBLE = "internal_marker_visible"
QUALITY_FLAG_JAPANESE_EMPTY_TEXT = "japanese_coherence_empty_text"
QUALITY_FLAG_ORPHAN_PARTICLE_FRAGMENT = "orphan_particle_fragment"
QUALITY_FLAG_UNFINISHED_PHRASE = "unfinished_phrase"
QUALITY_FLAG_REPEATED_SURFACE = "repeated_surface"

REJECTION_EMOTION_LABEL_BODY = "emotion_label_body_line"
REJECTION_EMOTION_LABEL_BODY_LINE = REJECTION_EMOTION_LABEL_BODY
REJECTION_FORBIDDEN_SURFACE = "forbidden_surface_pattern"
REJECTION_GENERIC_RELATION_SUFFIX = "generic_relation_suffix"
REJECTION_INTERNAL_MARKER_VISIBLE = "internal_marker_visible"
REJECTION_JAPANESE_EMPTY_TEXT = "japanese_coherence_empty_text"
REJECTION_ORPHAN_PARTICLE_FRAGMENT = "orphan_particle_fragment"
REJECTION_UNFINISHED_PHRASE = "unfinished_phrase"
REJECTION_REPEATED_SURFACE = "repeated_surface"

# Compatibility aliases used by earlier phase drafts.
REJECTION_JAPANESE_EMOTION_LABEL_BODY_LINE = REJECTION_EMOTION_LABEL_BODY
REJECTION_JAPANESE_FORBIDDEN_SURFACE = REJECTION_FORBIDDEN_SURFACE
REJECTION_JAPANESE_GENERIC_RELATION_SUFFIX = REJECTION_GENERIC_RELATION_SUFFIX
REJECTION_JAPANESE_ORPHAN_PARTICLE_FRAGMENT = REJECTION_ORPHAN_PARTICLE_FRAGMENT
REJECTION_JAPANESE_UNFINISHED_PHRASE = REJECTION_UNFINISHED_PHRASE

_EMOTION_LABELS = frozenset({"喜び", "悲しみ", "怒り", "不安", "平穏", "安心", "焦り", "恐れ", "怖さ", "自己理解", "期待", "疲労"})
_GREETING_RE = re.compile(r"^(?:[^。！？!?\n]{1,36}さん、)?(?:おはようございます|こんにちは|こんばんは|Emlisです|.+Emlisです)[。.!！]?")
_INTERNAL_MARKER_RE = re.compile(
    r"role_template|static_observation_text|fallback_observation|input_feedback_text_templates|"
    r"ObservationProfile|PhraseUnit|SentencePlan|primary_state|core_tension|pressure_sources|"
    r"limit_signal|value_or_strength"
)
_UNFINISHED_PATTERNS: Tuple[Pattern[str], ...] = (
    re.compile(r"なんであ(?:が|$)"),
    re.compile(r"考え始めが|考え始め$|先のことを考え始め$"),
    re.compile(r"悪化するが(?:同じ中にあります|$)"),
    re.compile(r"(?:けど|だけど|でも|のに|から|なら|すると|したら|そうしたら)$"),
)
_ORPHAN_PARTICLE_RE = re.compile(r"(?:を|が|に|は|へ|で)$")
_GENERIC_RELATION_SUFFIX_PATTERNS: Tuple[Pattern[str], ...] = (
    re.compile(r"がつながっています[。.!！]?$"),
    re.compile(r"同じ中にあります[。.!！]?$"),
    re.compile(r"(?:けど|でも|のに|から|なら|すると|したい|怖い|嬉しい)が(?:同じ中|つながって)"),
)


def _compile_patterns(patterns: Iterable[object] | None) -> tuple[Pattern[str], ...]:
    out: list[Pattern[str]] = []
    for item in patterns or ():
        if isinstance(item, re.Pattern):
            out.append(item)
        else:
            text = str(item or "").strip()
            if text:
                out.append(re.compile(re.escape(text)))
    return tuple(out)


def _body_sentences(text: Any, *, ignore_greeting_lines: bool) -> tuple[str, ...]:
    sentences = split_sentences(text)
    if not ignore_greeting_lines:
        return sentences
    return tuple(sentence for sentence in sentences if not _GREETING_RE.match(sentence))


def is_emotion_label_body_line(value: object) -> bool:
    return normalize_text(value) in _EMOTION_LABELS


def _repeated_surface_shapes(sentences: tuple[str, ...]) -> tuple[str, ...]:
    suffix_patterns = (
        ("表に出ています", re.compile(r"表に出ています[。.!！]?$")),
        ("重なっています", re.compile(r"重なっています[。.!！]?$")),
        ("混ざっています", re.compile(r"混ざっています[。.!！]?$")),
        ("残っています", re.compile(r"残っています[。.!！]?$")),
        ("続いています", re.compile(r"続いています[。.!！]?$")),
        ("同じ中にあります", re.compile(r"同じ中にあります[。.!！]?$")),
    )
    shapes: list[str] = []
    for sentence in sentences:
        for key, pattern in suffix_patterns:
            if pattern.search(sentence):
                shapes.append(key)
                break
    return tuple(value for value in dict.fromkeys(shapes) if shapes.count(value) >= 3)


def guard_japanese_coherence(
    text: Any,
    *,
    forbidden_surface_patterns: Iterable[object] | None = None,
    allow_empty: bool = False,
    ignore_greeting_lines: bool = True,
) -> GuardResult:
    sentences = _body_sentences(text, ignore_greeting_lines=ignore_greeting_lines)
    raw_text = str(text or "")
    reasons: list[str] = []
    flags: list[str] = []
    matched: list[str] = []

    if not sentences and not allow_empty:
        reasons.append(REJECTION_JAPANESE_EMPTY_TEXT)
        flags.extend((QUALITY_FLAG_JAPANESE_COHERENCE_FAILED, QUALITY_FLAG_JAPANESE_EMPTY_TEXT))

    if _INTERNAL_MARKER_RE.search(raw_text):
        reasons.append(REJECTION_INTERNAL_MARKER_VISIBLE)
        flags.extend((QUALITY_FLAG_JAPANESE_COHERENCE_FAILED, QUALITY_FLAG_INTERNAL_MARKER_VISIBLE))
        matched.append("internal_marker_visible")

    for regex in _compile_patterns(forbidden_surface_patterns):
        if regex.search(raw_text):
            reasons.append(REJECTION_FORBIDDEN_SURFACE)
            flags.extend((QUALITY_FLAG_JAPANESE_COHERENCE_FAILED, QUALITY_FLAG_FORBIDDEN_SURFACE))
            matched.append(regex.pattern)

    for sentence in sentences:
        compact = normalize_text(sentence)
        if is_emotion_label_body_line(sentence):
            reasons.append(REJECTION_EMOTION_LABEL_BODY)
            flags.extend((QUALITY_FLAG_JAPANESE_COHERENCE_FAILED, QUALITY_FLAG_EMOTION_LABEL_BODY))
            matched.append(sentence)
        if any(regex.search(sentence) or regex.search(compact) for regex in _GENERIC_RELATION_SUFFIX_PATTERNS):
            reasons.append(REJECTION_GENERIC_RELATION_SUFFIX)
            flags.extend((QUALITY_FLAG_JAPANESE_COHERENCE_FAILED, QUALITY_FLAG_GENERIC_RELATION_SUFFIX))
            matched.append(sentence)
        if any(regex.search(sentence) or regex.search(compact) for regex in _UNFINISHED_PATTERNS):
            reasons.append(REJECTION_UNFINISHED_PHRASE)
            flags.extend((QUALITY_FLAG_JAPANESE_COHERENCE_FAILED, QUALITY_FLAG_UNFINISHED_PHRASE))
            matched.append(sentence)
        if compact and _ORPHAN_PARTICLE_RE.search(compact):
            reasons.append(REJECTION_ORPHAN_PARTICLE_FRAGMENT)
            flags.extend((QUALITY_FLAG_JAPANESE_COHERENCE_FAILED, QUALITY_FLAG_ORPHAN_PARTICLE_FRAGMENT))
            matched.append(sentence)

    repeated_shapes = _repeated_surface_shapes(sentences)
    if len(sentences) >= 4 and repeated_shapes:
        reasons.append(REJECTION_REPEATED_SURFACE)
        flags.extend((QUALITY_FLAG_JAPANESE_COHERENCE_FAILED, QUALITY_FLAG_REPEATED_SURFACE))
        matched.extend(repeated_shapes)

    return make_guard_result(
        guard_name=JAPANESE_COHERENCE_GUARD_NAME,
        reasons=reasons,
        quality_flags=flags,
        matched_texts=matched,
        meta={"body_sentence_count": len(sentences), "forbidden_surface_count": len(token_list(forbidden_surface_patterns)), "repeated_surface_shapes": list(repeated_shapes)},
    )


class JapaneseCoherenceGuard:
    guard_name = JAPANESE_COHERENCE_GUARD_NAME

    def check(self, text: Any, **kwargs: Any) -> GuardResult:
        return guard_japanese_coherence(text, **kwargs)

    def evaluate(self, text: Any, **kwargs: Any) -> GuardResult:
        return self.check(text, **kwargs)


check_japanese_coherence = guard_japanese_coherence
evaluate_japanese_coherence = guard_japanese_coherence
judge_japanese_coherence = guard_japanese_coherence

__all__ = [
    "GUARD_NAME",
    "JAPANESE_COHERENCE_GUARD_NAME",
    "QUALITY_FLAG_JAPANESE_COHERENCE_FAILED",
    "QUALITY_FLAG_EMOTION_LABEL_BODY",
    "QUALITY_FLAG_FORBIDDEN_SURFACE",
    "QUALITY_FLAG_GENERIC_RELATION_SUFFIX",
    "QUALITY_FLAG_INTERNAL_MARKER_VISIBLE",
    "QUALITY_FLAG_JAPANESE_EMPTY_TEXT",
    "QUALITY_FLAG_ORPHAN_PARTICLE_FRAGMENT",
    "QUALITY_FLAG_UNFINISHED_PHRASE",
    "QUALITY_FLAG_REPEATED_SURFACE",
    "REJECTION_EMOTION_LABEL_BODY",
    "REJECTION_EMOTION_LABEL_BODY_LINE",
    "REJECTION_FORBIDDEN_SURFACE",
    "REJECTION_GENERIC_RELATION_SUFFIX",
    "REJECTION_INTERNAL_MARKER_VISIBLE",
    "REJECTION_JAPANESE_EMPTY_TEXT",
    "REJECTION_JAPANESE_EMOTION_LABEL_BODY_LINE",
    "REJECTION_JAPANESE_FORBIDDEN_SURFACE",
    "REJECTION_JAPANESE_GENERIC_RELATION_SUFFIX",
    "REJECTION_JAPANESE_ORPHAN_PARTICLE_FRAGMENT",
    "REJECTION_JAPANESE_UNFINISHED_PHRASE",
    "REJECTION_ORPHAN_PARTICLE_FRAGMENT",
    "REJECTION_UNFINISHED_PHRASE",
    "REJECTION_REPEATED_SURFACE",
    "JapaneseCoherenceGuard",
    "check_japanese_coherence",
    "evaluate_japanese_coherence",
    "guard_japanese_coherence",
    "is_emotion_label_body_line",
    "judge_japanese_coherence",
]
