# -*- coding: utf-8 -*-
from __future__ import annotations

"""Template and echo guard for EmlisAI observation text.

The guard is a mechanical rejection layer.  It never generates or rewrites
Emlis observation text; it only blocks fixed surfaces, non-AI/fallback sources,
legacy template smell, over-quotation of raw input, and repeated Limited
Composer surface forms.
"""

import re
from difflib import SequenceMatcher
from typing import Any, Iterable, List, Mapping, Sequence, Set, Tuple

from emlis_ai_types import EvidenceSpan, TemplateEchoReport
from emlis_ai_limited_sentence_quality_guard import judge_limited_sentence_quality

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
    r"^\s*(喜び|悲しみ|怒り|不安|平穏|自己理解|恐れ|焦り)[。.!！]?\s*$",
    r".+がつながっています",
    r".+同じ中にあります",
    r"なんであ(?:が|$)",
    r"考え始めが|考え始め[。.!！]?$",
    r"悪化するが(?:同じ中にあります|$)",
]
_BANNED_RE = [re.compile(p) for p in _BANNED_PATTERNS]
_GENERIC_CLOSING_RE = re.compile(
    r"(?:今の言葉として|ここに置いてくれた言葉|急いで片づけず|一つの結論へ急がず)[^。！？!?]{0,40}"
    r"(?:一緒に見ます|一緒に見ていきます|小さく扱いません|軽く扱いません)[。.!！]?"
)
_STEP14_FORBIDDEN_SURFACE_PATTERNS: Tuple[Tuple[str, re.Pattern[str]], ...] = (
    ("diagnosis_like", re.compile(r"診断|治療|病気|症状|トラウマ|障害|発達障害|ADHD|うつ|鬱|自律神経|依存症|PTSD|医療|心理療法|心理学的")),
    ("personality_label", re.compile(r"(?:あなた|その人|本人)(?:は|の)(?:[^。！？!?]{0,28})?(?:性格|人格|本質|タイプ|こういう人|弱い人|強い人|怠け|甘え)")),
    ("general_knowledge_completion", re.compile(r"(?:一般的に|普通は|多くの人|誰でも|人はみんな|よくあること|心理学的には|科学的には|医学的には)(?:[^。！？!?]{0,48})(?:です|あります|なります|と言われています)")),
)
_SENTENCE_SPLIT_RE = re.compile(r"(?<=[。！？!?])\s*|\n+")
_GREETING_RE = re.compile(r"^(?:[^。！？!?\n]{1,36}さん、)?(?:おはようございます|こんにちは|こんばんは|Emlisです|.+Emlisです)[。.!！]?$")

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
_LIMITED_MODEL_MARKERS = (
    "cocolon_limited_composer",
    "limited_composer",
    "cocolon_emlis_observation_composer",
    "emlis_observation_composer.a1",
    "a_plan_equivalent",
)
_LIMITED_METHOD_MARKERS = ("scoped_graph_evidence_composer", "scoped_graph_only")
_LIMITED_COVERAGE_VALUES = {"partial_observation", "current_input_core"}

# Limited Composer endings may be used once.  Repetition across body lines makes
# the output read like a renderer rather than a scoped conversation candidate.
_LIMITED_SURFACE_PATTERNS: Tuple[Tuple[str, re.Pattern[str]], ...] = (
    ("stacking", re.compile(r"重なっています[。.!！]?$")),
    ("connected", re.compile(r"つながっています[。.!！]?$")),
    ("same_inside", re.compile(r"同じ中にあります[。.!！]?$")),
    ("coexisting", re.compile(r"同時に(?:あります|残っています|置かれています)[。.!！]?$")),
    ("parallel", re.compile(r"並んで(?:います|あります)[。.!！]?$")),
    ("placed", re.compile(r"置かれています[。.!！]?$")),
    ("plain_exists", re.compile(r"(?:があります|にあります)[。.!！]?$")),
)
_ABSTRACT_SURFACE_TERMS = (
    "言葉の流れ",
    "外からは見えにくい緊張",
    "まだ決めきれない揺れ",
    "今の状態を形づくる",
    "大事な手がかり",
    "急いで片づけず",
    "一緒に見ます",
    "小さく扱いません",
    "軽く扱いません",
)
_MIN_QUOTE_NORM_CHARS = 7


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


def _sentences(text: Any) -> List[str]:
    return [s.strip() for s in _SENTENCE_SPLIT_RE.split(str(text or "")) if s.strip()]


def _body_sentences(text: Any) -> List[str]:
    out: List[str] = []
    for sentence in _sentences(text):
        if _GREETING_RE.match(sentence):
            continue
        out.append(sentence)
    return out


def _sentence_shapes(text: str) -> List[str]:
    shapes: List[str] = []
    for sentence in _sentences(text):
        s = re.sub(r"「[^」]+」", "「x」", sentence)
        s = re.sub(r"[\w\u3040-\u30ff\u3400-\u9fff]{3,}", "x", s)
        shapes.append(s[-18:])
    return shapes


def _clean_source(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "").replace("\r", " ").replace("\n", " ")).strip()


def _evidence_source_field(span: EvidenceSpan) -> str:
    return str(getattr(span, "source_field", "") or "").strip()


def _evidence_raw_text(span: EvidenceSpan) -> str:
    return _clean_source(getattr(span, "raw_text", ""))


def _as_id_set(values: Any) -> Set[str]:
    if not isinstance(values, (list, tuple, set)):
        return set()
    return {str(v or "").strip() for v in values if str(v or "").strip()}


def _candidate_spans(evidence_spans: Sequence[EvidenceSpan], *, used_evidence_span_ids: Any = None) -> List[EvidenceSpan]:
    used_ids = _as_id_set(used_evidence_span_ids)
    if not used_ids:
        return list(evidence_spans or [])
    return [span for span in list(evidence_spans or []) if str(getattr(span, "span_id", "") or "") in used_ids]


def _source_fragments(evidence_spans: Sequence[EvidenceSpan], *, used_evidence_span_ids: Any = None, min_chars: int = _MIN_QUOTE_NORM_CHARS) -> List[str]:
    fragments: List[str] = []
    for span in _candidate_spans(evidence_spans, used_evidence_span_ids=used_evidence_span_ids):
        if _evidence_source_field(span) not in {"memo", "memo_action"}:
            continue
        norm = _normalize(_evidence_raw_text(span))
        if len(norm) < min_chars:
            continue
        if norm not in fragments:
            fragments.append(norm)
    fragments.sort(key=len, reverse=True)
    return fragments[:24]


def _raw_quote_stats(text: Any, evidence_spans: Sequence[EvidenceSpan], *, used_evidence_span_ids: Any = None) -> Tuple[float, List[str]]:
    text_norm = _normalize(text)
    if not text_norm:
        return 0.0, []
    hits: List[str] = []
    used_ranges: List[Tuple[int, int]] = []
    for fragment in _source_fragments(evidence_spans, used_evidence_span_ids=used_evidence_span_ids):
        candidates = [fragment]
        if len(fragment) >= 24:
            candidates.append(fragment[: min(len(fragment), 36)])
        for candidate in candidates:
            if len(candidate) < _MIN_QUOTE_NORM_CHARS:
                continue
            start = text_norm.find(candidate)
            if start < 0:
                continue
            end = start + len(candidate)
            if any(not (end <= left or right <= start) for left, right in used_ranges):
                continue
            used_ranges.append((start, end))
            hits.append(candidate)
            break
    quoted_chars = sum(right - left for left, right in used_ranges)
    return min(1.0, quoted_chars / max(1, len(text_norm))), hits


def _max_sentence_echo_ratio(text: Any, evidence_spans: Sequence[EvidenceSpan], *, used_evidence_span_ids: Any = None) -> float:
    fragments = _source_fragments(evidence_spans, used_evidence_span_ids=used_evidence_span_ids)
    if not fragments:
        return 0.0
    score = 0.0
    for sentence in _body_sentences(text):
        for fragment in fragments:
            score = max(score, _ngram_overlap(sentence, fragment))
    return max(0.0, min(1.0, score))


def _raw_copy_sentence_ratio(text: Any, evidence_spans: Sequence[EvidenceSpan], *, used_evidence_span_ids: Any = None) -> float:
    fragments = _source_fragments(evidence_spans, used_evidence_span_ids=used_evidence_span_ids, min_chars=6)
    body = _body_sentences(text)
    if not body or not fragments:
        return 0.0
    copied = 0
    for sentence in body:
        sentence_norm = _normalize(sentence)
        if len(sentence_norm) < 6:
            continue
        for fragment in fragments:
            if len(fragment) < 6:
                continue
            direct_copy = sentence_norm == fragment
            embedded_copy = fragment in sentence_norm and len(fragment) / max(1, len(sentence_norm)) >= 0.78
            high_overlap_copy = _ngram_overlap(sentence_norm, fragment) >= 0.92 and len(fragment) / max(1, len(sentence_norm)) >= 0.70
            if direct_copy or embedded_copy or high_overlap_copy:
                copied += 1
                break
    return copied / max(1, len(body))


def _is_limited_composer(
    *,
    composer_model: Any = None,
    generation_method: Any = None,
    generation_scope: Any = None,
    coverage_scope: Any = None,
    composer_meta: Mapping[str, Any] | None = None,
) -> bool:
    values = " ".join(
        str(v or "").strip().lower()
        for v in (composer_model, generation_method, generation_scope, coverage_scope)
        if str(v or "").strip()
    )
    if any(marker in values for marker in (*_LIMITED_MODEL_MARKERS, *_LIMITED_METHOD_MARKERS)):
        return True
    if str(coverage_scope or "").strip() in _LIMITED_COVERAGE_VALUES:
        return True
    meta = composer_meta if isinstance(composer_meta, Mapping) else {}
    if bool(meta.get("limited_composer")):
        return True
    meta_values = " ".join(str(v or "").strip().lower() for v in meta.values() if isinstance(v, (str, int, float, bool)))
    return any(marker in meta_values for marker in (*_LIMITED_MODEL_MARKERS, *_LIMITED_METHOD_MARKERS))


def _limited_surface_signatures(text: Any) -> List[str]:
    signatures: List[str] = []
    for sentence in _body_sentences(text):
        for key, pattern in _LIMITED_SURFACE_PATTERNS:
            if pattern.search(sentence):
                signatures.append(key)
                break
    return signatures


def _repeated_values(values: Sequence[str], *, min_count: int = 2) -> List[str]:
    out: List[str] = []
    for value in values:
        if values.count(value) >= min_count and value not in out:
            out.append(value)
    return out


def _surface_signature_rows_from_meta(
    *,
    composer_meta: Mapping[str, Any] | None = None,
    surface_signatures: Sequence[Mapping[str, Any]] | None = None,
) -> List[Mapping[str, Any]]:
    rows: List[Mapping[str, Any]] = []

    def add_from(value: Any) -> None:
        if isinstance(value, Mapping):
            rows.append(value)
        elif isinstance(value, (list, tuple)):
            for item in value:
                add_from(item)

    add_from(surface_signatures or ())
    meta = composer_meta if isinstance(composer_meta, Mapping) else {}
    for key in ("surface_signature_rows", "surface_signatures"):
        add_from(meta.get(key))
    for signature_key in ("surface_signature", "surface_signature_meta"):
        signature_meta = meta.get(signature_key)
        if isinstance(signature_meta, Mapping):
            for key in ("surface_signature_rows", "surface_signatures"):
                add_from(signature_meta.get(key))
    for nested_key in ("surface_realizer", "surface_realization", "surface_variation_report", "complete_surface_realizer"):
        nested = meta.get(nested_key)
        if isinstance(nested, Mapping):
            for key in ("surface_signature_rows", "surface_signatures", "surface_lines"):
                add_from(nested.get(key))
            signature_meta = nested.get("surface_signature")
            if isinstance(signature_meta, Mapping):
                for key in ("surface_signature_rows", "surface_signatures"):
                    add_from(signature_meta.get(key))
    # The rows can arrive from surface_lines where the signature is nested.
    normalized: List[Mapping[str, Any]] = []
    for row in rows:
        if not isinstance(row, Mapping):
            continue
        signature = row.get("surface_signature")
        if isinstance(signature, Mapping):
            normalized.append(signature)
        else:
            normalized.append(row)
    # Keep order but de-duplicate by full row representation.
    deduped: List[Mapping[str, Any]] = []
    seen: Set[str] = set()
    for row in normalized:
        marker = repr(sorted((str(k), str(v)) for k, v in row.items()))
        if marker in seen:
            continue
        seen.add(marker)
        deduped.append(row)
    return deduped


def _row_text(row: Mapping[str, Any], key: str) -> str:
    return str(row.get(key) or "").strip()


def _surface_signature_repetition_stats(rows: Sequence[Mapping[str, Any]]) -> dict[str, Any]:
    row_list = [row for row in rows if isinstance(row, Mapping)]
    signatures = [_row_text(row, "signature") for row in row_list if _row_text(row, "signature")]
    ending_keys = [_row_text(row, "ending_key") for row in row_list if _row_text(row, "ending_key")]
    connector_keys = [_row_text(row, "connector_key") for row in row_list if _row_text(row, "connector_key")]
    repeated_signatures = _repeated_values(signatures, min_count=2)
    repeated_endings = _repeated_values(ending_keys, min_count=3)
    repeated_connectors = [key for key in _repeated_values(connector_keys, min_count=3) if key != "none"]
    template_flags = (
        "completion_sentence_template_used",
        "role_completed_sentence_template_used",
        "input_specific_template_used",
        "fixed_sentence_template_used",
    )
    flagged_template_rows = [
        str(row.get("sentence_id") or index)
        for index, row in enumerate(row_list, start=1)
        if any(bool(row.get(flag)) for flag in template_flags)
    ]
    raw_rows = [
        str(row.get("sentence_id") or index)
        for index, row in enumerate(row_list, start=1)
        if bool(row.get("raw_input_included") or row.get("raw_text_included"))
    ]
    return {
        "row_count": len(row_list),
        "surface_signature_repeat_count": len(repeated_signatures),
        "repeated_surface_signature_keys": repeated_signatures,
        "same_ending_major_count": len(repeated_endings),
        "repeated_ending_keys": repeated_endings,
        "connector_repetition_major_count": len(repeated_connectors),
        "repeated_connector_keys": repeated_connectors,
        "flagged_template_sentence_ids": flagged_template_rows,
        "raw_input_sentence_ids": raw_rows,
    }


def _tone_guard_report_from_meta(composer_meta: Mapping[str, Any] | None) -> dict[str, Any]:
    """Return Step5 Tone Guard report from Complete composer meta.

    Template/Echo Guard stays mechanical: it does not rewrite tone, but it can
    fail closed when the Tone Engine has already detected over-empathy,
    diagnostic voice, advice-like surface, or generic comfort.
    """

    if not isinstance(composer_meta, Mapping):
        return {}
    direct = composer_meta.get("tone_guard_report")
    if isinstance(direct, Mapping):
        return dict(direct)
    surface = composer_meta.get("surface_realizer")
    if isinstance(surface, Mapping):
        nested = surface.get("tone_guard_report")
        if isinstance(nested, Mapping):
            return dict(nested)
    complete_runtime = composer_meta.get("complete_initial_runtime")
    if isinstance(complete_runtime, Mapping):
        nested = complete_runtime.get("tone_guard_report")
        if isinstance(nested, Mapping):
            return dict(nested)
    return {}


def _observation_surface_reports_from_meta(composer_meta: Mapping[str, Any] | None) -> dict[str, dict[str, Any]]:
    """Return Step9 observation surface reports from composer meta.

    The guard consumes these reports as diagnostics only.  It does not generate
    or repair text and it does not change public response contracts.
    """

    reports: dict[str, dict[str, Any]] = {}
    if not isinstance(composer_meta, Mapping):
        return reports

    def add_report(name: str, value: Any) -> None:
        if isinstance(value, Mapping) and value:
            reports[name] = dict(value)

    add_report("template", composer_meta.get("observation_surface_template_report"))
    add_report("tone", composer_meta.get("observation_surface_tone_report"))
    add_report("template", composer_meta.get("template_report") if "observation_surface" in str(composer_meta.get("template_report", {})) else reports.get("template"))
    add_report("tone", composer_meta.get("tone_report") if "observation_surface" in str(composer_meta.get("tone_report", {})) else reports.get("tone"))

    for nested_key in (
        "observation_surface_realizer",
        "observation_surface_realization",
        "surface_realizer",
        "surface_realization",
        "complete_initial_runtime",
    ):
        nested = composer_meta.get(nested_key)
        if not isinstance(nested, Mapping):
            continue
        add_report("template", nested.get("observation_surface_template_report") or nested.get("template_report"))
        add_report("tone", nested.get("observation_surface_tone_report") or nested.get("tone_report"))
    return reports


def _limited_surface_repetition_score(signatures: Sequence[str]) -> float:
    if not signatures:
        return 0.0
    counts = {value: list(signatures).count(value) for value in set(signatures)}
    return max(counts.values()) / max(1, len(signatures))


def _abstract_repetition_score(text: Any) -> float:
    body_norm = _normalize("\n".join(_body_sentences(text)))
    if not body_norm:
        return 0.0
    counts = [body_norm.count(_normalize(term)) for term in _ABSTRACT_SURFACE_TERMS if _normalize(term)]
    if not counts:
        return 0.0
    return max(counts) / max(1, len(_body_sentences(text)))


def guard_template_echo(
    *,
    comment_text: Any,
    evidence_spans: Sequence[EvidenceSpan],
    previous_outputs: Iterable[str] | None = None,
    composer_source: Any = None,
    composer_model: Any = None,
    generation_method: Any = None,
    generation_scope: Any = None,
    coverage_scope: Any = None,
    composer_meta: Mapping[str, Any] | None = None,
    used_evidence_span_ids: Sequence[str] | None = None,
    surface_signatures: Sequence[Mapping[str, Any]] | None = None,
) -> TemplateEchoReport:
    text = str(comment_text or "").strip()
    reasons: List[str] = []
    matched: List[str] = []
    matched_limited: List[str] = []

    source = str(composer_source or "").strip()
    if source and source != "ai_generated":
        reasons.append("composer_source_not_ai_generated")
        if source in _NON_AI_SOURCES:
            reasons.append("rule_rendered_or_fallback_source")

    for pattern in _BANNED_RE:
        if pattern.search(text):
            matched.append(pattern.pattern)
    if _GENERIC_CLOSING_RE.search(text):
        matched.append("generic_closing_surface")
        reasons.append("generic_closing")

    step14_forbidden: List[str] = []
    for reason, pattern in _STEP14_FORBIDDEN_SURFACE_PATTERNS:
        if pattern.search(text):
            step14_forbidden.append(reason)
            matched.append(reason)
    if step14_forbidden:
        reasons.append("phase14_overclaim_guard")
        reasons.extend(step14_forbidden)

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

    evidence_text = "\n".join(_evidence_raw_text(span) for span in evidence_spans if _evidence_source_field(span) in {"memo", "memo_action"})
    raw_echo_ratio = _ngram_overlap(text, evidence_text)
    if raw_echo_ratio >= 0.82:
        reasons.append("raw_input_echo")

    limited = _is_limited_composer(
        composer_model=composer_model,
        generation_method=generation_method,
        generation_scope=generation_scope,
        coverage_scope=coverage_scope,
        composer_meta=composer_meta,
    )
    raw_quote_char_ratio, quote_hits = _raw_quote_stats(
        text,
        evidence_spans,
        used_evidence_span_ids=used_evidence_span_ids,
    )
    max_sentence_echo = _max_sentence_echo_ratio(
        text,
        evidence_spans,
        used_evidence_span_ids=used_evidence_span_ids,
    )
    raw_copy_sentence_ratio = _raw_copy_sentence_ratio(
        text,
        evidence_spans,
        used_evidence_span_ids=used_evidence_span_ids,
    )
    quote_threshold = 0.48 if limited else 0.62
    if quote_hits and (
        (len(quote_hits) >= 2 and raw_quote_char_ratio >= quote_threshold)
        or (len(quote_hits) >= 3 and raw_quote_char_ratio >= 0.42)
        or (max(len(hit) for hit in quote_hits) >= 42 and raw_quote_char_ratio >= 0.54)
    ):
        reasons.append("excessive_raw_quote")
        if limited:
            reasons.append("limited_composer_excessive_raw_quote")

    if limited and raw_copy_sentence_ratio >= 0.67:
        reasons.append("excessive_raw_quote")
        reasons.append("limited_composer_excessive_raw_quote")

    signatures = _limited_surface_signatures(text)
    limited_surface_score = _limited_surface_repetition_score(signatures)
    repeated_limited = _repeated_values(signatures, min_count=2)
    if limited and repeated_limited:
        reasons.append("repeated_limited_surface_pattern")
        reasons.append("limited_composer_repeated_surface")
        matched_limited.extend(repeated_limited)

    abstract_score = _abstract_repetition_score(text)
    if abstract_score >= 1.0:
        reasons.append("abstract_phrase_repetition")

    quality_report = judge_limited_sentence_quality(
        comment_text=text,
        evidence_spans=evidence_spans,
        used_evidence_span_ids=used_evidence_span_ids,
        composer_meta=composer_meta,
    )
    if limited and not bool(quality_report.get("passed")):
        for reason in list(quality_report.get("rejection_reasons") or []):
            reasons.append(str(reason))
            if str(reason) == "phase8_generic_closing":
                reasons.append("limited_composer_generic_closing")
            if str(reason) == "general_knowledge_completion":
                reasons.append("limited_composer_general_knowledge_completion")
            if str(reason) == "diagnosis_like":
                reasons.append("limited_composer_diagnosis_like")
            if str(reason) == "personality_label":
                reasons.append("limited_composer_personality_label")
            if str(reason) == "repeated_surface":
                reasons.append("limited_composer_repeated_surface")
        for fragment in list(quality_report.get("matched_surfaces") or quality_report.get("matched_fragments") or []):
            if fragment and fragment not in matched:
                matched.append(str(fragment))

    # Generic repeated-shape detection is kept as a broad legacy/template guard,
    # but it looks at body sentences only so a greeting does not turn a short
    # three-sentence candidate into a false positive.
    shapes = _sentence_shapes("\n".join(_body_sentences(text)))
    repeated_shape_score = 0.0
    if shapes:
        repeated_shape_score = 1.0 - (len(set(shapes)) / max(1, len(shapes)))
    if repeated_shape_score >= 0.45 and len(shapes) >= 4:
        reasons.append("repeated_sentence_pattern")

    # Product-quality Step3: consume surface signatures emitted by the
    # Complete Surface Realizer. This keeps template detection structural: the
    # guard inspects connector / ending / signature repetition instead of exact
    # sentence matches, and it still never rewrites text.
    surface_signature_rows = _surface_signature_rows_from_meta(
        composer_meta=composer_meta,
        surface_signatures=surface_signatures,
    )
    surface_signature_stats = _surface_signature_repetition_stats(surface_signature_rows)
    if surface_signature_stats["same_ending_major_count"] > 0:
        reasons.append("same_ending_major")
    if surface_signature_stats["surface_signature_repeat_count"] > 0:
        reasons.append("surface_signature_repeat")
    if surface_signature_stats["connector_repetition_major_count"] > 0:
        reasons.append("surface_connector_repetition")
    if surface_signature_stats["flagged_template_sentence_ids"]:
        reasons.append("surface_signature_template_flag")
    if surface_signature_stats["raw_input_sentence_ids"]:
        reasons.append("surface_signature_raw_input_included")

    # Product-quality Step5: consume Tone Engine diagnostics as a fail-closed
    # signal.  Tone is planned before surface realization, and this guard only
    # reads its report; it does not add wording or relax Template checks.
    tone_guard_report = _tone_guard_report_from_meta(composer_meta)
    tone_guard_major_count = 0
    try:
        tone_guard_major_count = int(tone_guard_report.get("tone_guard_major_count") or 0)
    except (TypeError, ValueError):
        tone_guard_major_count = 0
    if bool(tone_guard_report.get("release_blocker")) or tone_guard_major_count > 0:
        reasons.append("tone_guard_major")
        for reason in list(tone_guard_report.get("tone_guard_reasons") or tone_guard_report.get("blocker_reasons") or []):
            reason_text = str(reason or "").strip()
            if reason_text:
                reasons.append(f"tone_guard:{reason_text}")

    # Step9 Observation Surface Realizer/Tone diagnostics are consumed as a
    # fail-closed signal.  The Template/Echo Guard still does not generate,
    # repair, or relax any public Display Gate contract.
    observation_surface_reports = _observation_surface_reports_from_meta(composer_meta)
    observation_template_report = observation_surface_reports.get("template", {})
    if bool(observation_template_report.get("release_blocker")):
        reasons.append("observation_surface_template_guard")
        for reason in list(observation_template_report.get("template_guard_reasons") or observation_template_report.get("blocker_reasons") or []):
            reason_text = str(reason or "").strip()
            if reason_text:
                reasons.append(f"observation_surface_template:{reason_text}")
    observation_tone_report = observation_surface_reports.get("tone", {})
    if bool(observation_tone_report.get("release_blocker")):
        reasons.append("observation_surface_tone_guard")
        for reason in list(observation_tone_report.get("tone_guard_reasons") or observation_tone_report.get("blocker_reasons") or []):
            reason_text = str(reason or "").strip()
            if reason_text:
                reasons.append(f"observation_surface_tone:{reason_text}")

    reasons = list(dict.fromkeys(reasons))
    return TemplateEchoReport(
        passed=not reasons,
        max_old_template_similarity=round(max_old, 3),
        max_previous_output_similarity=round(previous_max, 3),
        raw_echo_ratio=round(raw_echo_ratio, 3),
        repeated_sentence_pattern_score=round(repeated_shape_score, 3),
        max_sentence_echo_ratio=round(max_sentence_echo, 3),
        raw_quote_span_count=len(quote_hits),
        raw_copy_sentence_ratio=round(raw_copy_sentence_ratio, 3),
        limited_surface_repetition_score=round(limited_surface_score, 3),
        abstract_repetition_score=round(abstract_score, 3),
        abstract_phrase_repetition_score=round(abstract_score, 3),
        surface_signature_row_count=int(surface_signature_stats.get("row_count") or 0),
        surface_signature_repeat_count=int(surface_signature_stats.get("surface_signature_repeat_count") or 0),
        same_ending_major_count=int(surface_signature_stats.get("same_ending_major_count") or 0),
        surface_connector_repetition_count=int(surface_signature_stats.get("connector_repetition_major_count") or 0),
        repeated_surface_signature_keys=list(surface_signature_stats.get("repeated_surface_signature_keys") or []),
        repeated_surface_ending_keys=list(surface_signature_stats.get("repeated_ending_keys") or []),
        repeated_surface_connector_keys=list(surface_signature_stats.get("repeated_connector_keys") or []),
        # Compatibility aliases for Phase 5 traces/tests.
        raw_quote_char_ratio=round(raw_quote_char_ratio, 3),
        matched_raw_quote_fragments=quote_hits[:6],
        repeated_limited_surface_score=round(limited_surface_score, 3),
        matched_limited_surface_patterns=matched_limited,
        phase8_emotion_label_body_line_count=len([r for r in list(quality_report.get("rejection_reasons") or []) if r == "phase8_emotion_label_body_line"]),
        phase8_missing_must_keep_roles=list(quality_report.get("missing_must_keep_roles") or quality_report.get("missing_required_roles") or []),
        phase8_quality_rejection_reasons=list(quality_report.get("rejection_reasons") or []),
        matched_banned_patterns=matched,
        rejection_reasons=reasons,
    )


__all__ = ["guard_template_echo"]
