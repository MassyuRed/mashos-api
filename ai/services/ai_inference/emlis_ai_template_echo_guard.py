# -*- coding: utf-8 -*-
from __future__ import annotations

"""Template and echo guard for EmlisAI observation text."""

import re
from difflib import SequenceMatcher
from typing import Any, Iterable, List, Sequence, Set

from emlis_ai_types import EvidenceSpan, TemplateEchoReport

# Old and newly-discovered surface patterns that caused broken outputs. These
# are rejection signatures, not generation templates.
_BANNED_PATTERNS = [
    r"そこには、?.+もありました",
    r".+も含まれていました",
    r".+と受け取りました",
    r".+と思います",
    r".+として見ています",
    r"ここでは、.+小さく扱いません",
    r"ここに置いてくれた言葉を、?Emlisは軽く扱いません",
    r"生活したいことも大切な場所",
    r"大切な場所として見えています",
    r"今の私は",
    r"私は、",
    r"あなたは|あなたの|あなたが|あなたに",
    r"入力全体では、?.+中心に出ています",
    r"選択した感情[:：].+中心として見ている感情",
    r"言葉の流れには、?外からは見えにくい緊張",
    r"外からは見えにくい緊張が含まれています",
    r"まだ決めきれない揺れ",
    r"今の状態を形づくる大事な手がかり",
    r"急いで片づけず",
    r"今の言葉として一緒に見ます",
    r"一つの結論へ急がず",
    r"Emlisは、?「?.+」?を急いで片づけず",
]
_BANNED_RE = [re.compile(p) for p in _BANNED_PATTERNS]
_SENTENCE_SPLIT_RE = re.compile(r"(?<=[。！？!?])\s*|\n+")

_OLD_TEMPLATE_SIGNATURES = [
    "そこには、感覚もありました。",
    "同時に、今の状態を形づくる大切な要素として見ています。",
    "ここでは、願いも怖さも、今できることを大切にしたい気持ちも、小さく扱いません。",
    "逃げ出したくなる気持ちは、弱さではなく、それだけ気を張ってきた反応として見ています。",
    "今の生活にある良さと、ふっと現実に戻った時の不便さを同時に抱えている状態として見ています。",
    "入力全体では、中心に出ています。",
    "言葉の流れには、外からは見えにくい緊張が含まれています。",
    "まだ決めきれない揺れも、今の状態を形づくる大事な手がかりです。",
    "Emlisは、急いで片づけず、今の言葉として一緒に見ます。",
]
_NON_AI_SOURCES = {"rule_rendered", "fallback", "static_string", "legacy_kernel", "safe_fallback"}


def _normalize(text: Any) -> str:
    return re.sub(r"[\s、。.!！?？「」『』（）()]+", "", str(text or "")).strip()


def _char_ngrams(text: str, n: int = 3) -> Set[str]:
    compact = _normalize(text)
    if len(compact) < n:
        return {compact} if compact else set()
    return {compact[i : i + n] for i in range(len(compact) - n + 1)}


def _ngram_overlap(a: str, b: str) -> float:
    aa = _char_ngrams(a)
    bb = _char_ngrams(b)
    if not aa or not bb:
        return 0.0
    return len(aa.intersection(bb)) / max(1, min(len(aa), len(bb)))


def _sentence_shapes(text: str) -> List[str]:
    shapes: List[str] = []
    for sentence in [s.strip() for s in _SENTENCE_SPLIT_RE.split(text) if s.strip()]:
        s = re.sub(r"「[^」]+」", "「x」", sentence)
        s = re.sub(r"[\w\u3040-\u30ff\u3400-\u9fff]{3,}", "x", s)
        shapes.append(s[-18:])
    return shapes


def guard_template_echo(
    *,
    comment_text: Any,
    evidence_spans: Sequence[EvidenceSpan],
    previous_outputs: Iterable[str] | None = None,
    composer_source: Any = None,
) -> TemplateEchoReport:
    text = str(comment_text or "").strip()
    reasons: List[str] = []
    matched: List[str] = []

    source = str(composer_source or "").strip()
    if source and source != "ai_generated":
        reasons.append("composer_source_not_ai_generated")
        if source in _NON_AI_SOURCES:
            reasons.append("rule_rendered_or_fallback_source")

    for pattern in _BANNED_RE:
        if pattern.search(text):
            matched.append(pattern.pattern)
    if matched:
        reasons.append("banned_legacy_pattern")

    max_old = 0.0
    for signature in _OLD_TEMPLATE_SIGNATURES:
        max_old = max(max_old, SequenceMatcher(None, _normalize(text), _normalize(signature)).ratio(), _ngram_overlap(text, signature))
    if max_old >= 0.62:
        reasons.append("old_template_similarity")

    previous_max = 0.0
    for prev in previous_outputs or []:
        previous_max = max(previous_max, _ngram_overlap(text, str(prev or "")))
    if previous_max >= 0.72:
        reasons.append("previous_output_similarity")

    evidence_text = "\n".join(span.raw_text for span in evidence_spans if span.source_field in {"memo", "memo_action"})
    raw_echo_ratio = _ngram_overlap(text, evidence_text)
    if raw_echo_ratio >= 0.82:
        reasons.append("raw_input_echo")

    shapes = _sentence_shapes(text)
    repeated_shape_score = 0.0
    if shapes:
        repeated_shape_score = 1.0 - (len(set(shapes)) / max(1, len(shapes)))
    if repeated_shape_score >= 0.45 and len(shapes) >= 4:
        reasons.append("repeated_sentence_pattern")

    reasons = list(dict.fromkeys(reasons))
    return TemplateEchoReport(
        passed=not reasons,
        max_old_template_similarity=round(max_old, 3),
        max_previous_output_similarity=round(previous_max, 3),
        raw_echo_ratio=round(raw_echo_ratio, 3),
        repeated_sentence_pattern_score=round(repeated_shape_score, 3),
        matched_banned_patterns=matched,
        rejection_reasons=reasons,
    )


__all__ = ["guard_template_echo"]
