# -*- coding: utf-8 -*-
from __future__ import annotations

"""Core-agnostic template and raw echo guard."""

import re
from difflib import SequenceMatcher
from typing import Any, Iterable, Mapping, Sequence

from .base import GuardResult, make_guard_result, normalize_text, ngram_overlap, split_sentences, token_list

TEMPLATE_ECHO_GUARD_NAME = "cocolon_text_generation_core.guards.template_echo.v1"
GUARD_NAME = TEMPLATE_ECHO_GUARD_NAME

REJECTION_TEMPLATE_EMPTY_TEXT = "template_echo_empty_text"
REJECTION_TEMPLATE_FIXED_META = "fixed_template_meta"
REJECTION_TEMPLATE_INTERNAL_MARKER = "internal_template_marker"
REJECTION_TEMPLATE_FIXED_SOURCE = "fixed_template_source"
REJECTION_TEMPLATE_FIXED_SURFACE = "fixed_template_surface"
REJECTION_PREVIOUS_OUTPUT_SIMILARITY = "previous_output_similarity"
REJECTION_RAW_INPUT_ECHO = "raw_input_echo"
REJECTION_EXCESSIVE_RAW_QUOTE = "excessive_raw_quote"
REJECTION_REPEATED_SURFACE_PATTERN = "repeated_surface_pattern"
REJECTION_REPEATED_LIMITED_SURFACE_PATTERN = "repeated_limited_surface_pattern"
REJECTION_GENERAL_KNOWLEDGE_COMPLETION = "general_knowledge_completion"
REJECTION_DIAGNOSIS_LIKE = "diagnosis_like"
REJECTION_PERSONALITY_LABEL = "personality_label"
REJECTION_TEMPLATE_EXCESSIVE_RAW_QUOTE = REJECTION_EXCESSIVE_RAW_QUOTE

QUALITY_FLAG_TEMPLATE_ECHO_FAILED = "template_echo_failed"

_INTERNAL_TEMPLATE_MARKER_RE = re.compile(r"role_template|static_observation_text|fallback_observation|input_feedback_text_templates|fixed_string_renderer|ObservationProfile|PhraseUnit|SentencePlan|primary_state|core_tension|pressure_sources|limit_signal|value_or_strength")
_TEMPLATE_META_FLAGS = ("fixed_string_renderer_used", "role_template_used", "example_phrase_replacement_used", "fixed_observation_template_used", "fallback_observation_used")
_FIXED_SOURCES = {"rule_rendered", "fallback", "fixed_string_renderer", "template_renderer"}
_FIXED_SURFACE_PATTERNS = (
    re.compile(r"そこには、?[^。！？!?]{0,24}もありました[。.!！]?"),
    re.compile(r"[^。！？!?]{0,24}と見ています[。.!！]?"),
    re.compile(r"一緒に見ます[。.!！]?"),
)
_STEP14_FORBIDDEN_SURFACES = (
    (REJECTION_DIAGNOSIS_LIKE, re.compile(r"診断|治療|病気|症状|トラウマ|障害|発達障害|ADHD|うつ|鬱|自律神経|依存症|PTSD|医療|心理療法|心理学的")),
    (REJECTION_PERSONALITY_LABEL, re.compile(r"(?:あなた|その人|本人)(?:は|の)(?:[^。！？!?]{0,28})?(?:性格|人格|本質|タイプ|こういう人|弱い人|強い人|怠け|甘え)")),
    (REJECTION_GENERAL_KNOWLEDGE_COMPLETION, re.compile(r"(?:一般的に|普通は|多くの人|誰でも|人はみんな|よくあること|心理学的には|科学的には|医学的には)(?:[^。！？!?]{0,48})(?:です|あります|なります|と言われています)")),
)

_LIMITED_SURFACE_PATTERNS = (
    ("remain", re.compile(r"(?:が|も|同時に)残っています[。.!！]?$")),
    ("mixed", re.compile(r"混ざっています[。.!！]?$")),
    ("stack", re.compile(r"重なっています[。.!！]?$")),
    ("continue", re.compile(r"続いています[。.!！]?$")),
    ("front", re.compile(r"前面にあります[。.!！]?$")),
    ("surface_visible", re.compile(r"表に出ています[。.!！]?$")),
    ("same_inside", re.compile(r"同じ中にあります[。.!！]?$")),
)


def _mapping_get(value: Any, key: str, default: Any = None) -> Any:
    return value.get(key, default) if isinstance(value, Mapping) else getattr(value, key, default)


def _span_id(span: Any) -> str:
    return str(_mapping_get(span, "span_id", "") or "").strip()


def _span_raw(span: Any) -> str:
    raw = _mapping_get(span, "raw_text", "")
    if not raw:
        raw = _mapping_get(_mapping_get(span, "source_anchor", None), "raw_text", "")
    return str(raw or "").strip()


def _candidate_raws(evidence_spans: Iterable[Any] | None, used_evidence_span_ids: Sequence[object] | None) -> list[str]:
    used = set(token_list(used_evidence_span_ids))
    raws: list[str] = []
    for span in evidence_spans or ():
        if used and _span_id(span) not in used:
            continue
        raw = _span_raw(span)
        if raw:
            raws.append(raw)
    return raws


def _previous_similarity(text: Any, previous_outputs: Iterable[Any] | None) -> float:
    text_norm = normalize_text(text)
    score = 0.0
    for previous in previous_outputs or ():
        prev_norm = normalize_text(previous)
        if prev_norm:
            score = max(score, SequenceMatcher(None, text_norm, prev_norm).ratio(), ngram_overlap(text_norm, prev_norm))
    return round(score, 3)


def _raw_quote_ratio_and_hits(text: Any, evidence_spans: Iterable[Any] | None, used_evidence_span_ids: Sequence[object] | None) -> tuple[float, tuple[str, ...]]:
    body = normalize_text(text)
    if not body:
        return 0.0, tuple()
    hits: list[str] = []
    used_ranges: list[tuple[int, int]] = []
    for raw in sorted(_candidate_raws(evidence_spans, used_evidence_span_ids), key=lambda v: len(normalize_text(v)), reverse=True):
        norm = normalize_text(raw)
        if len(norm) < 7:
            continue
        candidates = [norm]
        if len(norm) >= 24:
            candidates.append(norm[: min(len(norm), 36)])
        for candidate in candidates:
            start = body.find(candidate)
            if start < 0:
                continue
            end = start + len(candidate)
            if any(not (end <= left or right <= start) for left, right in used_ranges):
                continue
            used_ranges.append((start, end))
            hits.append(candidate)
            break
    ratio = sum(right - left for left, right in used_ranges) / max(1, len(body))
    return round(min(1.0, ratio), 3), tuple(dict.fromkeys(hits))


def _limited_surface_signatures(text: Any) -> tuple[str, ...]:
    signatures: list[str] = []
    for sentence in split_sentences(text):
        for key, pattern in _LIMITED_SURFACE_PATTERNS:
            if pattern.search(sentence):
                signatures.append(key)
                break
    return tuple(signatures)


def _repetition_score(values: Sequence[str]) -> float:
    if not values:
        return 0.0
    return round(max(values.count(value) for value in set(values)) / max(1, len(values)), 3)


def guard_template_echo(
    comment_text: Any,
    *,
    evidence_spans: Iterable[Any] | None = None,
    previous_outputs: Iterable[Any] | None = None,
    composer_meta: Mapping[str, Any] | None = None,
    used_evidence_span_ids: Sequence[object] | None = None,
    composer_source: object = "",
) -> GuardResult:
    text = str(comment_text or "").strip()
    reasons: list[str] = []
    matched: list[str] = []
    if not text:
        reasons.append(REJECTION_TEMPLATE_EMPTY_TEXT)

    meta = composer_meta if isinstance(composer_meta, Mapping) else {}
    piece_preserves_source_claims = (
        str(meta.get("core_id") or "").strip().lower() == "piece"
        and str(meta.get("answer_preservation_policy") or "").strip() in {"preserve_user_claims", "source_scaled"}
    )
    fixed_meta = [key for key in _TEMPLATE_META_FLAGS if bool(meta.get(key))]
    if fixed_meta:
        reasons.append(REJECTION_TEMPLATE_FIXED_META)
        matched.extend(fixed_meta)

    source = str(composer_source or meta.get("composer_source") or "").strip()
    if source in _FIXED_SOURCES:
        reasons.append(REJECTION_TEMPLATE_FIXED_SOURCE)
        matched.append(source)

    if _INTERNAL_TEMPLATE_MARKER_RE.search(text):
        reasons.append(REJECTION_TEMPLATE_INTERNAL_MARKER)
        matched.append("internal_template_marker")

    for pattern in _FIXED_SURFACE_PATTERNS:
        if pattern.search(text):
            reasons.append(REJECTION_TEMPLATE_FIXED_SURFACE)
            matched.append(pattern.pattern)
    for reason, pattern in _STEP14_FORBIDDEN_SURFACES:
        if pattern.search(text):
            reasons.append(reason)
            matched.append(reason)

    previous_similarity = _previous_similarity(text, previous_outputs)
    if previous_similarity >= 0.72:
        reasons.append(REJECTION_PREVIOUS_OUTPUT_SIMILARITY)

    raw_quote_ratio, quote_hits = _raw_quote_ratio_and_hits(text, evidence_spans, used_evidence_span_ids)
    evidence_text = "\n".join(_candidate_raws(evidence_spans, used_evidence_span_ids))
    raw_echo_ratio = round(ngram_overlap(text, evidence_text), 3) if evidence_text else 0.0
    source_core = str(meta.get("source_core") or meta.get("core_id") or "").strip().lower()
    preservation_policy = str(meta.get("answer_preservation_policy") or "").strip().lower()
    analysis_report_observation = source_core == "analysis" and bool(
        meta.get("analysis_report_observation") or meta.get("analysis_composer_connected")
    )
    # Piece intentionally keeps user claims and must_keep terms visible in a
    # public Q&A answer.  Keep the anti-template guard strict for full raw echo,
    # but do not reject a Piece answer only because source claims survive.
    piece_claim_preservation = source_core == "piece" and preservation_policy == "preserve_user_claims"
    raw_echo_limit = 1.01 if analysis_report_observation else (0.97 if piece_preserves_source_claims else 0.82)
    multi_quote_limit = 1.01 if analysis_report_observation else (0.82 if piece_claim_preservation else 0.42)
    single_quote_limit = 1.01 if analysis_report_observation else (0.90 if piece_claim_preservation else 0.56)
    if raw_echo_ratio >= raw_echo_limit:
        reasons.append(REJECTION_RAW_INPUT_ECHO)
    if quote_hits and ((len(quote_hits) >= 2 and raw_quote_ratio >= multi_quote_limit) or raw_quote_ratio >= single_quote_limit):
        reasons.append(REJECTION_EXCESSIVE_RAW_QUOTE)
        matched.extend(quote_hits[:6])

    signatures = _limited_surface_signatures(text)
    limited_surface_repetition_score = _repetition_score(signatures)
    repeated = tuple(value for value in dict.fromkeys(signatures) if signatures.count(value) >= 2)
    if repeated:
        reasons.append(REJECTION_REPEATED_LIMITED_SURFACE_PATTERN)
        matched.extend(repeated)

    body_sentences = split_sentences(text)
    repeated_sentence_score = 0.0
    if body_sentences:
        shapes = [re.sub(r"[\w\u3040-\u30ff\u3400-\u9fff]{3,}", "x", sentence)[-18:] for sentence in body_sentences]
        repeated_sentence_score = round(1.0 - (len(set(shapes)) / max(1, len(shapes))), 3)
        if repeated_sentence_score >= 0.45 and len(shapes) >= 4 and not piece_preserves_source_claims and not analysis_report_observation:
            reasons.append(REJECTION_REPEATED_SURFACE_PATTERN)

    return make_guard_result(
        guard_name=TEMPLATE_ECHO_GUARD_NAME,
        reasons=reasons,
        quality_flags=(QUALITY_FLAG_TEMPLATE_ECHO_FAILED,) if reasons else (),
        matched_texts=matched,
        meta={
            "previous_similarity": previous_similarity,
            "raw_quote_ratio": raw_quote_ratio,
            "raw_quote_hits": quote_hits,
            "raw_echo_ratio": raw_echo_ratio,
            "limited_surface_repetition_score": limited_surface_repetition_score,
            "repeated_limited_surface_patterns": repeated,
            "repeated_sentence_pattern_score": repeated_sentence_score,
            "piece_preserves_source_claims": piece_preserves_source_claims,
            "analysis_report_observation": analysis_report_observation,
        },
    )


class TemplateEchoGuard:
    guard_name = TEMPLATE_ECHO_GUARD_NAME

    def check(self, comment_text: Any, **kwargs: Any) -> GuardResult:
        return guard_template_echo(comment_text, **kwargs)

    def evaluate(self, comment_text: Any, **kwargs: Any) -> GuardResult:
        return self.check(comment_text, **kwargs)


def evaluate_template_echo(text: Any, **kwargs: Any) -> GuardResult:
    return guard_template_echo(text, **kwargs)


def judge_template_echo(text: Any, **kwargs: Any) -> GuardResult:
    return guard_template_echo(text, **kwargs)


def check_template_echo(text: Any, **kwargs: Any) -> GuardResult:
    return guard_template_echo(text, **kwargs)


__all__ = [
    "GUARD_NAME",
    "TEMPLATE_ECHO_GUARD_NAME",
    "QUALITY_FLAG_TEMPLATE_ECHO_FAILED",
    "TemplateEchoGuard",
    "check_template_echo",
    "evaluate_template_echo",
    "guard_template_echo",
    "judge_template_echo",
    "REJECTION_TEMPLATE_EMPTY_TEXT",
    "REJECTION_TEMPLATE_FIXED_META",
    "REJECTION_TEMPLATE_INTERNAL_MARKER",
    "REJECTION_TEMPLATE_FIXED_SOURCE",
    "REJECTION_TEMPLATE_FIXED_SURFACE",
    "REJECTION_PREVIOUS_OUTPUT_SIMILARITY",
    "REJECTION_RAW_INPUT_ECHO",
    "REJECTION_EXCESSIVE_RAW_QUOTE",
    "REJECTION_TEMPLATE_EXCESSIVE_RAW_QUOTE",
    "REJECTION_REPEATED_SURFACE_PATTERN",
    "REJECTION_REPEATED_LIMITED_SURFACE_PATTERN",
    "REJECTION_GENERAL_KNOWLEDGE_COMPLETION",
    "REJECTION_DIAGNOSIS_LIKE",
    "REJECTION_PERSONALITY_LABEL",
]
