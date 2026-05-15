# -*- coding: utf-8 -*-
from __future__ import annotations

"""Core-agnostic grounding guard for generated body text."""

import re
from difflib import SequenceMatcher
from typing import Any, Iterable, Mapping, Sequence

from cocolon_text_generation_core.guards.base import GuardResult, make_guard_result, normalize_text, split_sentences, token_list

GROUNDING_GUARD_NAME = "cocolon_text_generation_core.guards.grounding.v1"
REJECTION_GROUNDING_EMPTY_TEXT = "grounding_empty_text"
REJECTION_GROUNDING_EVIDENCE_MISSING = "grounding_evidence_missing"
REJECTION_USED_EVIDENCE_IDS_MISSING = "used_evidence_span_ids_missing"
REJECTION_USED_EVIDENCE_NOT_FOUND = "used_evidence_span_ids_not_found"
REJECTION_UNSUPPORTED_SENTENCE = "unsupported_sentence"
REJECTION_DECLARED_EVIDENCE_NOT_REFLECTED = "declared_evidence_not_reflected"
REJECTION_UNSUPPORTED_DIAGNOSIS_LIKE = "unsupported_diagnosis_like"
REJECTION_UNSUPPORTED_PERSONALITY_LABEL = "unsupported_personality_label"
REJECTION_UNSUPPORTED_GENERAL_KNOWLEDGE_COMPLETION = "unsupported_general_knowledge_completion"
REJECTION_UNSUPPORTED_ADVICE_ASSERTION = "unsupported_advice_assertion"
QUALITY_FLAG_GROUNDING_FAILED = "grounding_failed"

REJECTION_GROUNDING_TEXT_MISSING = REJECTION_GROUNDING_EMPTY_TEXT
REJECTION_USED_EVIDENCE_SPAN_IDS_MISSING = REJECTION_USED_EVIDENCE_IDS_MISSING
REJECTION_GROUNDING_USED_EVIDENCE_MISSING = REJECTION_USED_EVIDENCE_IDS_MISSING
REJECTION_USED_EVIDENCE_SPAN_ID_NOT_FOUND = REJECTION_USED_EVIDENCE_NOT_FOUND
REJECTION_GROUNDING_USED_EVIDENCE_UNKNOWN = REJECTION_USED_EVIDENCE_NOT_FOUND
REJECTION_GROUNDING_OVERCLAIM_NOT_IN_EVIDENCE = REJECTION_UNSUPPORTED_SENTENCE
QUALITY_FLAG_UNSUPPORTED_SENTENCE = REJECTION_UNSUPPORTED_SENTENCE
QUALITY_FLAG_USED_EVIDENCE_MISSING = "used_evidence_missing"

# Compatibility aliases.
REJECTION_GROUNDING_UNSUPPORTED_SENTENCE = REJECTION_UNSUPPORTED_SENTENCE
REJECTION_GROUNDING_DECLARED_EVIDENCE_NOT_REFLECTED = REJECTION_DECLARED_EVIDENCE_NOT_REFLECTED

_GREETING_RE = re.compile(r"^(?:[^。！？!?\n]{1,36}さん、)?(?:おはようございます|こんにちは|こんばんは|Emlisです|.+Emlisです)[。.!！]?")
_FUNCTION_WORDS = frozenset({"入力全体", "言葉", "気持ち", "状態", "場所", "重さ", "願い", "反応", "感覚", "中", "今", "今回", "あります", "出ています"})
_STEP14_DIAGNOSIS_LIKE_RE = re.compile(r"診断|治療|病気|症状|トラウマ|障害|発達障害|ADHD|うつ|鬱|自律神経|依存症|PTSD|医療|心理療法|心理学的")
_STEP14_PERSONALITY_LABEL_RE = re.compile(r"(?:あなた|その人|本人)(?:は|の)(?:[^。！？!?]{0,28})?(?:性格|人格|本質|タイプ|こういう人|弱い人|強い人|怠け|甘え)")
_STEP14_GENERAL_KNOWLEDGE_RE = re.compile(r"(?:一般的に|普通は|多くの人|誰でも|人はみんな|よくあること|心理学的には|科学的には|医学的には)(?:[^。！？!?]{0,48})(?:です|あります|なります|と言われています)")
_STEP14_ADVICE_ASSERTION_RE = re.compile(r"(?:必要があります|すべきです|するべきです|しなければなりません|正解です|間違いです)")


def _mapping_get(value: Any, key: str, default: Any = None) -> Any:
    if isinstance(value, Mapping):
        return value.get(key, default)
    return getattr(value, key, default)


def _span_id(span: Any) -> str:
    return str(_mapping_get(span, "span_id", "") or "").strip()


def _span_raw(span: Any) -> str:
    raw = _mapping_get(span, "raw_text", "")
    if not raw:
        raw = _mapping_get(_mapping_get(span, "source_anchor", None), "raw_text", "")
    return str(raw or "").strip()


def _unit_id(unit: Any) -> str:
    return str(_mapping_get(unit, "phrase_unit_id", "") or "").strip()


def _unit_span_id(unit: Any) -> str:
    return str(_mapping_get(unit, "evidence_span_id", "") or "").strip()


def _unit_text(unit: Any) -> str:
    return str(_mapping_get(unit, "text", "") or _mapping_get(unit, "compressed_text", "") or "").strip()


def _phrase_supports(
    *,
    phrase_units: Iterable[Any] | None,
    used_phrase_unit_ids: Sequence[object] | None,
    allowed_evidence_span_ids: set[str],
) -> tuple[tuple[str, str], ...]:
    used_units = set(token_list(used_phrase_unit_ids))
    out: list[tuple[str, str]] = []
    seen: set[tuple[str, str]] = set()
    for unit in phrase_units or ():
        unit_id = _unit_id(unit)
        if used_units and unit_id not in used_units:
            continue
        span_id = _unit_span_id(unit)
        text = _unit_text(unit)
        if not span_id or not text or (allowed_evidence_span_ids and span_id not in allowed_evidence_span_ids):
            continue
        key = (span_id, text)
        if key in seen:
            continue
        seen.add(key)
        out.append(key)
    return tuple(out)


def _body_sentences(text: Any) -> tuple[str, ...]:
    return tuple(sentence for sentence in split_sentences(text) if not _GREETING_RE.match(sentence))


def _char_ngrams(text: Any, n: int = 3) -> set[str]:
    compact = normalize_text(text)
    if len(compact) < n:
        return {compact} if compact else set()
    return {compact[index : index + n] for index in range(len(compact) - n + 1)}


def _ngram_overlap(a: Any, b: Any) -> float:
    aa = _char_ngrams(a)
    bb = _char_ngrams(b)
    if not aa or not bb:
        return 0.0
    return len(aa.intersection(bb)) / max(1, min(len(aa), len(bb)))


def _terms(text: Any) -> set[str]:
    cleaned = re.sub(r"[「」『』、。.!！?？\s]", " ", str(text or ""))
    chunks = [chunk.strip() for chunk in re.split(r"[ /・,，]+", cleaned) if chunk.strip()]
    out: set[str] = set()
    for chunk in chunks:
        chunk = re.sub(r"(があります|あります|出ています|ています|です|ます|する|した|している|して|なる|なって)$", "", chunk)
        if not chunk or chunk in _FUNCTION_WORDS:
            continue
        if len(chunk) >= 2:
            out.add(chunk[:18])
        if len(chunk) >= 4:
            out.add(chunk[:4])
            out.add(chunk[-4:])
        if len(chunk) >= 6:
            out.add(chunk[:6])
            out.add(chunk[-6:])
    return out


def _span_matches_sentence(sentence: str, raw: str) -> bool:
    raw_norm = normalize_text(raw)
    sent_norm = normalize_text(sentence)
    if len(raw_norm) >= 3 and (raw_norm in sent_norm or sent_norm in raw_norm):
        return True
    sentence_terms = _terms(sentence)
    raw_terms = _terms(raw)
    shared = sentence_terms.intersection(raw_terms)
    if len(shared) >= 1 and any(len(token) >= 4 for token in shared):
        return True
    if len(shared) >= 2:
        return True
    if _ngram_overlap(sentence, raw) >= 0.12:
        return True
    return SequenceMatcher(None, sent_norm, raw_norm).ratio() >= 0.42


def _step14_unbacked_reason(sentence: str, evidence_text: str) -> str:
    if _STEP14_DIAGNOSIS_LIKE_RE.search(sentence) and not _STEP14_DIAGNOSIS_LIKE_RE.search(evidence_text):
        return REJECTION_UNSUPPORTED_DIAGNOSIS_LIKE
    if _STEP14_PERSONALITY_LABEL_RE.search(sentence) and not _STEP14_PERSONALITY_LABEL_RE.search(evidence_text):
        return REJECTION_UNSUPPORTED_PERSONALITY_LABEL
    if _STEP14_GENERAL_KNOWLEDGE_RE.search(sentence) and not _STEP14_GENERAL_KNOWLEDGE_RE.search(evidence_text):
        return REJECTION_UNSUPPORTED_GENERAL_KNOWLEDGE_COMPLETION
    if _STEP14_ADVICE_ASSERTION_RE.search(sentence) and not _STEP14_ADVICE_ASSERTION_RE.search(evidence_text):
        return REJECTION_UNSUPPORTED_ADVICE_ASSERTION
    return ""


def guard_grounding(
    comment_text: Any,
    *,
    evidence_spans: Iterable[Any] | None = None,
    used_evidence_span_ids: Sequence[object] | None = None,
    phrase_units: Iterable[Any] | None = None,
    used_phrase_unit_ids: Sequence[object] | None = None,
    require_used_evidence_span_ids: bool = True,
) -> GuardResult:
    text = str(comment_text or "").strip()
    body = _body_sentences(text)
    spans = tuple(span for span in evidence_spans or () if _span_id(span) and _span_raw(span))
    declared = token_list(used_evidence_span_ids)
    all_ids = {_span_id(span) for span in spans}
    reasons: list[str] = []
    matched: list[str] = []
    matched_ids: list[str] = []
    sentence_claims: list[dict[str, Any]] = []

    if not text or not body:
        reasons.append(REJECTION_GROUNDING_EMPTY_TEXT)
    if not spans:
        reasons.append(REJECTION_GROUNDING_EVIDENCE_MISSING)
    if require_used_evidence_span_ids and not declared:
        reasons.append(REJECTION_USED_EVIDENCE_IDS_MISSING)

    missing_declared = [span_id for span_id in declared if span_id not in all_ids]
    if missing_declared:
        reasons.append(REJECTION_USED_EVIDENCE_NOT_FOUND)
        matched.extend(missing_declared)

    allowed = set(declared) if declared else all_ids
    scoped = tuple(span for span in spans if _span_id(span) in allowed)
    evidence_text = "\n".join(_span_raw(span) for span in scoped)
    phrase_supports = _phrase_supports(
        phrase_units=phrase_units,
        used_phrase_unit_ids=used_phrase_unit_ids,
        allowed_evidence_span_ids=allowed,
    )
    unsupported: list[str] = []

    for sentence in body:
        sentence_matches = [_span_id(span) for span in scoped if _span_matches_sentence(sentence, _span_raw(span))]
        phrase_matches = [span_id for span_id, phrase_text in phrase_supports if _span_matches_sentence(sentence, phrase_text)]
        sentence_matches = list(dict.fromkeys(sentence_matches + phrase_matches))
        sentence_claims.append({"sentence": sentence, "evidence_span_ids": sentence_matches})
        step14_reason = _step14_unbacked_reason(sentence, evidence_text)
        if step14_reason:
            reasons.append(step14_reason)
            matched.append(sentence)
            unsupported.append(sentence)
        elif sentence_matches:
            matched_ids.extend(sentence_matches)
        else:
            unsupported.append(sentence)

    if unsupported:
        reasons.append(REJECTION_UNSUPPORTED_SENTENCE)
        matched.extend(unsupported)
    if declared and not set(declared).intersection(matched_ids):
        reasons.append(REJECTION_DECLARED_EVIDENCE_NOT_REFLECTED)

    coverage_ratio = 0.0 if not body else (len(body) - len(unsupported)) / max(1, len(body))
    return make_guard_result(
        guard_name=GROUNDING_GUARD_NAME,
        reasons=reasons,
        quality_flags=(QUALITY_FLAG_GROUNDING_FAILED,) if reasons else (),
        matched_texts=matched,
        coverage_ratio=coverage_ratio,
        used_evidence_span_ids=tuple(dict.fromkeys(matched_ids)),
        meta={
            "body_sentence_count": len(body),
            "evidence_span_count": len(spans),
            "declared_used_evidence_span_ids": list(declared),
            "sentence_claims": sentence_claims,
            "phrase_support_count": len(phrase_supports),
        },
    )


class GroundingGuard:
    guard_name = GROUNDING_GUARD_NAME

    def evaluate(self, comment_text: Any, **kwargs: Any) -> GuardResult:
        return guard_grounding(comment_text, **kwargs)

    def check(self, comment_text: Any, **kwargs: Any) -> GuardResult:
        return self.evaluate(comment_text, **kwargs)


check_grounding = guard_grounding
evaluate_grounding = guard_grounding
judge_grounding = guard_grounding

__all__ = [
    "GROUNDING_GUARD_NAME",
    "GroundingGuard",
    "guard_grounding",
    "evaluate_grounding",
    "judge_grounding",
    "check_grounding",
    "REJECTION_GROUNDING_TEXT_MISSING",
    "REJECTION_USED_EVIDENCE_SPAN_IDS_MISSING",
    "REJECTION_GROUNDING_USED_EVIDENCE_MISSING",
    "REJECTION_USED_EVIDENCE_SPAN_ID_NOT_FOUND",
    "REJECTION_GROUNDING_USED_EVIDENCE_UNKNOWN",
    "REJECTION_GROUNDING_OVERCLAIM_NOT_IN_EVIDENCE",
    "QUALITY_FLAG_UNSUPPORTED_SENTENCE",
    "QUALITY_FLAG_USED_EVIDENCE_MISSING",
    "REJECTION_GROUNDING_EMPTY_TEXT",
    "REJECTION_GROUNDING_EVIDENCE_MISSING",
    "REJECTION_USED_EVIDENCE_IDS_MISSING",
    "REJECTION_USED_EVIDENCE_NOT_FOUND",
    "REJECTION_UNSUPPORTED_SENTENCE",
    "REJECTION_UNSUPPORTED_DIAGNOSIS_LIKE",
    "REJECTION_UNSUPPORTED_PERSONALITY_LABEL",
    "REJECTION_UNSUPPORTED_GENERAL_KNOWLEDGE_COMPLETION",
    "REJECTION_UNSUPPORTED_ADVICE_ASSERTION",
    "REJECTION_GROUNDING_UNSUPPORTED_SENTENCE",
    "REJECTION_DECLARED_EVIDENCE_NOT_REFLECTED",
    "REJECTION_GROUNDING_DECLARED_EVIDENCE_NOT_REFLECTED",
]
