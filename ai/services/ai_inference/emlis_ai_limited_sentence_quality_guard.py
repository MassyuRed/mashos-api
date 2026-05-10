# -*- coding: utf-8 -*-
from __future__ import annotations

"""Mechanical Japanese coherence guard for Phase8 Limited Composer output."""

import re
from dataclasses import dataclass, field
from typing import Any, Dict, Iterable, List, Mapping, Sequence

_EMOTION_LABELS = {"喜び", "悲しみ", "怒り", "不安", "平穏", "自己理解", "恐れ", "焦り"}
_SENTENCE_SPLIT_RE = re.compile(r"(?<=[。！？!?])\s*|\n+")
_GREETING_RE = re.compile(r"^(?:[^。！？!?\n]{1,36}さん、)?(?:おはようございます|こんにちは|こんばんは|Emlisです|.+Emlisです)[。.!！]?$")
_BROKEN_SURFACE_PATTERNS: tuple[tuple[str, re.Pattern[str]], ...] = (
    ("phase8_generic_relation_suffix", re.compile(r"がつながっています[。.!！]?$")),
    ("phase8_generic_relation_suffix", re.compile(r"同じ中にあります[。.!！]?$")),
    ("phase8_unfinished_phrase", re.compile(r"なんであ(?:が|$)")),
    ("phase8_unfinished_phrase", re.compile(r"考え始めが|考え始め[。.!！]?$")),
    ("phase8_unfinished_phrase", re.compile(r"悪化するが(?:同じ中にあります|$)")),
    ("phase8_orphan_particle_fragment", re.compile(r"(?:けど|でも|のに|から|なら|すると|したい|怖い|嬉しい)が(?:同じ中|つながって)")),
)
_TRAILING_UNFINISHED_RE = re.compile(r"(なんであ|考え始め|現実と|普通に|けど|でも|のに|から|なら|すると)$")


@dataclass(frozen=True)
class LimitedSentenceQualityReport:
    passed: bool
    rejection_reasons: List[str] = field(default_factory=list)
    matched_patterns: List[str] = field(default_factory=list)
    emotion_label_lines: List[str] = field(default_factory=list)
    unfinished_fragments: List[str] = field(default_factory=list)


def _sentences(text: Any) -> List[str]:
    return [s.strip() for s in _SENTENCE_SPLIT_RE.split(str(text or "")) if s.strip()]


def _body_sentences(text: Any) -> List[str]:
    return [s for s in _sentences(text) if not _GREETING_RE.match(s)]


def _span_raw(span: Any) -> str:
    if isinstance(span, Mapping):
        return str(span.get("raw_text") or "")
    return str(getattr(span, "raw_text", "") or "")


def _span_source(span: Any) -> str:
    if isinstance(span, Mapping):
        return str(span.get("source_field") or "")
    return str(getattr(span, "source_field", "") or "")


def detect_phase8_profile(evidence_spans: Sequence[Any] | None = None) -> str:
    text = "\n".join(_span_raw(span) for span in list(evidence_spans or []) if _span_source(span) in {"memo", "memo_action"})
    if re.search(r"生活したい|悪化|逃げ出", text):
        return "reality_escape_tension"
    if re.search(r"頼りたい|迷惑|嫌われ|限界", text):
        return "relationship_approach_avoidance"
    if re.search(r"腹が立|大事に扱われなかった", text):
        return "anger_hurt_boundary"
    if re.search(r"考えすぎ|分かって|完璧|適当", text):
        return "self_understanding_loop"
    if re.search(r"だるい|何もしたくない", text) and len(re.sub(r"\s+", "", text)) < 40:
        return "short_ambiguous_low_evidence"
    if re.search(r"片付け|気持ちが軽|ちゃんとでき", text):
        return "positive_progress"
    if re.search(r"楽しか|元気|不安|落ちる", text):
        return "mixed_positive_anxiety"
    return "unknown"


def judge_limited_sentence_quality(
    *,
    comment_text: Any,
    evidence_spans: Sequence[Any] = (),
    profile_key: str = "",
    used_evidence_span_ids: Sequence[str] | None = None,
    composer_meta: Mapping[str, Any] | None = None,
) -> Dict[str, Any]:
    text = str(comment_text or "").strip()
    reasons: List[str] = []
    matched: List[str] = []
    label_lines: List[str] = []
    unfinished: List[str] = []
    body = _body_sentences(text)

    if not text:
        reasons.append("empty_text")

    for sentence in body:
        normalized = sentence.strip(" 　、,。.!！?？")
        if normalized in _EMOTION_LABELS:
            label_lines.append(normalized)
        if _TRAILING_UNFINISHED_RE.search(normalized):
            unfinished.append(sentence)
        for key, pattern in _BROKEN_SURFACE_PATTERNS:
            if pattern.search(sentence):
                reasons.append(key)
                matched.append(sentence)

    if label_lines:
        reasons.append("phase8_emotion_label_body_line")
        matched.extend(label_lines)
    if unfinished:
        reasons.append("phase8_unfinished_phrase")
        matched.extend(unfinished)
    effective_profile = profile_key or str((composer_meta or {}).get("phase8_profile_key") or "") or detect_phase8_profile(evidence_spans)
    if effective_profile not in {"", "unknown", "short_ambiguous_low_evidence"} and len(body) < 2:
        reasons.append("phase8_body_too_short")

    reasons = list(dict.fromkeys(reasons))
    matched = list(dict.fromkeys(matched))
    return {
        "passed": not reasons,
        "rejection_reasons": reasons,
        "matched_surfaces": matched,
        "matched_patterns": matched,
        "matched_fragments": matched,
        "emotion_label_lines": label_lines,
        "unfinished_fragments": unfinished,
        "profile_key": effective_profile,
        "body_sentence_count": len(body),
    }


def evaluate_limited_sentence_quality(*args: Any, **kwargs: Any) -> Dict[str, Any]:
    comment_text = kwargs.pop("comment_text", None)
    if args:
        comment_text = args[0]
    # Ignore compatibility-only kwargs that this mechanical guard does not need.
    kwargs.pop("composer_model", None)
    return judge_limited_sentence_quality(comment_text=comment_text, **kwargs)


__all__ = ["LimitedSentenceQualityReport", "detect_phase8_profile", "judge_limited_sentence_quality", "evaluate_limited_sentence_quality"]
