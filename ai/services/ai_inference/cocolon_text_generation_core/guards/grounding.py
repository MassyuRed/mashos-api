# -*- coding: utf-8 -*-
from __future__ import annotations

"""Core-agnostic grounding guard for generated body text."""

import re
from difflib import SequenceMatcher
from typing import Any, Iterable, Mapping, Sequence

from cocolon_text_generation_core.guards.base import GuardResult, make_guard_result, normalize_text, split_sentences, token_list

GROUNDING_GUARD_NAME = "cocolon_text_generation_core.guards.grounding.v1"
BINDING_AWARE_GROUNDING_VERSION = "cocolon_text_generation_core.binding_aware_grounding.v1"
REJECTION_GROUNDING_EMPTY_TEXT = "grounding_empty_text"
REJECTION_GROUNDING_EVIDENCE_MISSING = "grounding_evidence_missing"
REJECTION_USED_EVIDENCE_IDS_MISSING = "used_evidence_span_ids_missing"
REJECTION_USED_EVIDENCE_NOT_FOUND = "used_evidence_span_ids_not_found"
REJECTION_UNSUPPORTED_SENTENCE = "unsupported_sentence"
REJECTION_DECLARED_EVIDENCE_NOT_REFLECTED = "declared_evidence_not_reflected"
REJECTION_BINDING_EVIDENCE_NOT_FOUND = "binding_declared_evidence_not_found"
REJECTION_BINDING_PHRASE_UNIT_NOT_FOUND = "binding_declared_phrase_unit_not_found"
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


def _clean_token(value: Any) -> str:
    return str(value or "").strip()


def _span_id(span: Any) -> str:
    return _clean_token(_mapping_get(span, "span_id", ""))


def _span_raw(span: Any) -> str:
    raw = _mapping_get(span, "raw_text", "")
    if not raw:
        raw = _mapping_get(_mapping_get(span, "source_anchor", None), "raw_text", "")
    return str(raw or "").strip()


def _unit_id(unit: Any) -> str:
    return _clean_token(_mapping_get(unit, "phrase_unit_id", ""))


def _unit_span_id(unit: Any) -> str:
    return _clean_token(_mapping_get(unit, "evidence_span_id", ""))


def _unit_text(unit: Any) -> str:
    return str(_mapping_get(unit, "text", "") or _mapping_get(unit, "compressed_text", "") or "").strip()


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


def _binding_row(value: Any) -> dict[str, Any]:
    if value is None:
        return {}
    if isinstance(value, Mapping):
        row = dict(value)
    elif hasattr(value, "as_meta"):
        try:
            row = dict(value.as_meta(include_text=True))
        except TypeError:
            row = dict(value.as_meta())
    else:
        row = {
            "sentence_id": _mapping_get(value, "sentence_id", ""),
            "text": _mapping_get(value, "text", ""),
            "used_evidence_span_ids": _mapping_get(value, "used_evidence_span_ids", ()),
            "used_phrase_unit_ids": _mapping_get(value, "used_phrase_unit_ids", ()),
            "relation_type": _mapping_get(value, "relation_type", ""),
            "line_role": _mapping_get(value, "line_role", ""),
            "coverage_scope": _mapping_get(value, "coverage_scope", ""),
        }
    meta = row.get("meta") if isinstance(row.get("meta"), Mapping) else {}
    out = {
        "sentence_id": _clean_token(row.get("sentence_id") or row.get("id")),
        "text": str(row.get("text") or row.get("sentence") or "").strip(),
        "used_evidence_span_ids": token_list(row.get("used_evidence_span_ids") or row.get("evidence_span_ids") or ()),
        "used_phrase_unit_ids": token_list(row.get("used_phrase_unit_ids") or row.get("phrase_unit_ids") or ()),
        "relation_type": _clean_token(row.get("relation_type") or row.get("relation") or meta.get("canonical_relation_type")),
        "line_role": _clean_token(row.get("line_role") or row.get("role")),
        "coverage_scope": _clean_token(row.get("coverage_scope")),
    }
    if not any((out["sentence_id"], out["text"], out["used_evidence_span_ids"], out["used_phrase_unit_ids"], out["relation_type"])):
        return {}
    return out


def _binding_rows(value: Any) -> tuple[dict[str, Any], ...]:
    if not value:
        return ()
    candidates: list[Any] = []
    if isinstance(value, Mapping):
        candidates.extend(value.get("bindings") or value.get("sentence_bindings") or value.get("items") or value.get("binding_rows_sanitized") or [])
        for key in ("sentence_binding_bundle", "binding_bundle", "binding"):
            nested = value.get(key)
            if isinstance(nested, Mapping):
                candidates.extend(nested.get("bindings") or nested.get("sentence_bindings") or nested.get("items") or [])
        if not candidates and (value.get("sentence_id") or value.get("text")):
            candidates.append(value)
    elif isinstance(value, (list, tuple)):
        candidates.extend(value)
    else:
        candidates.append(value)

    rows: list[dict[str, Any]] = []
    seen: set[str] = set()
    for item in candidates:
        row = _binding_row(item)
        if not row:
            continue
        key = f"{row.get('sentence_id') or len(rows)}:{normalize_text(row.get('text') or '')}"
        if key in seen:
            continue
        seen.add(key)
        rows.append(row)
    return tuple(rows)


def _binding_text_matches_sentence(binding: Mapping[str, Any], sentence: str) -> bool:
    text = str(binding.get("text") or "").strip()
    if not text:
        return False
    b = normalize_text(text)
    s = normalize_text(sentence)
    if not b or not s:
        return False
    if b == s or b in s or s in b:
        return True
    return _ngram_overlap(text, sentence) >= 0.72


def _binding_for_sentence(sentence: str, body_index: int, rows: Sequence[Mapping[str, Any]]) -> Mapping[str, Any] | None:
    for row in rows or ():
        if _binding_text_matches_sentence(row, sentence):
            return row
    expected_id = f"s{body_index + 1}"
    for row in rows or ():
        if str(row.get("sentence_id") or "").strip() == expected_id:
            return row
    if 0 <= body_index < len(rows or ()):  # order fallback for sanitized rows without text
        return rows[body_index]
    return None


def _binding_support(
    *,
    binding: Mapping[str, Any] | None,
    allowed_evidence_span_ids: set[str],
    evidence_by_id: Mapping[str, Any],
    phrase_by_id: Mapping[str, Any],
) -> dict[str, Any]:
    if not binding:
        return {
            "binding_used": False,
            "declared_evidence_span_ids": [],
            "declared_phrase_unit_ids": [],
            "used_evidence_span_ids": [],
            "used_phrase_unit_ids": [],
            "missing_evidence_span_ids": [],
            "missing_phrase_unit_ids": [],
            "relation_type": "",
            "line_role": "",
            "sentence_id": "",
        }
    declared_phrase = list(token_list(binding.get("used_phrase_unit_ids") or ()))
    declared_evidence = list(token_list(binding.get("used_evidence_span_ids") or ()))
    for phrase_id in declared_phrase:
        unit = phrase_by_id.get(phrase_id)
        span_id = _unit_span_id(unit) if unit is not None else ""
        if span_id and span_id not in declared_evidence:
            declared_evidence.append(span_id)

    effective_allowed = set(allowed_evidence_span_ids or evidence_by_id.keys())
    used_evidence = [span_id for span_id in declared_evidence if span_id in evidence_by_id and (not effective_allowed or span_id in effective_allowed)]
    missing_evidence = [span_id for span_id in declared_evidence if span_id not in evidence_by_id or (effective_allowed and span_id not in effective_allowed)]
    used_phrase = [phrase_id for phrase_id in declared_phrase if phrase_id in phrase_by_id]
    missing_phrase = [phrase_id for phrase_id in declared_phrase if phrase_id not in phrase_by_id]
    relation_type = _clean_token(binding.get("relation_type"))

    # Step 6: binding can ground safe abstraction only when it carries an in-scope
    # evidence id and at least one structural anchor (phrase id or relation type).
    # Step14 / overclaim checks still run before acceptance.
    binding_used = bool(used_evidence and (used_phrase or relation_type))
    return {
        "binding_used": binding_used,
        "declared_evidence_span_ids": list(dict.fromkeys(declared_evidence)),
        "declared_phrase_unit_ids": list(dict.fromkeys(declared_phrase)),
        "used_evidence_span_ids": list(dict.fromkeys(used_evidence)),
        "used_phrase_unit_ids": list(dict.fromkeys(used_phrase)),
        "missing_evidence_span_ids": list(dict.fromkeys(missing_evidence)),
        "missing_phrase_unit_ids": list(dict.fromkeys(missing_phrase)),
        "relation_type": relation_type,
        "line_role": _clean_token(binding.get("line_role")),
        "sentence_id": _clean_token(binding.get("sentence_id")),
    }


def guard_grounding(
    comment_text: Any,
    *,
    evidence_spans: Iterable[Any] | None = None,
    used_evidence_span_ids: Sequence[object] | None = None,
    phrase_units: Iterable[Any] | None = None,
    used_phrase_unit_ids: Sequence[object] | None = None,
    sentence_bindings: Iterable[Any] | Mapping[str, Any] | None = None,
    require_used_evidence_span_ids: bool = True,
) -> GuardResult:
    text = str(comment_text or "").strip()
    body = _body_sentences(text)
    spans = tuple(span for span in evidence_spans or () if _span_id(span) and _span_raw(span))
    declared = token_list(used_evidence_span_ids)
    all_ids = {_span_id(span) for span in spans}
    evidence_by_id = {_span_id(span): span for span in spans}
    phrase_by_id = {_unit_id(unit): unit for unit in phrase_units or () if _unit_id(unit)}
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
    binding_rows = _binding_rows(sentence_bindings)
    unsupported: list[str] = []
    binding_supported_count = 0
    binding_missing_evidence: list[str] = []
    binding_missing_phrase: list[str] = []
    relation_types: list[str] = []

    for index, sentence in enumerate(body):
        binding = _binding_for_sentence(sentence, index, binding_rows)
        binding_support = _binding_support(
            binding=binding,
            allowed_evidence_span_ids=allowed,
            evidence_by_id=evidence_by_id,
            phrase_by_id=phrase_by_id,
        )
        binding_missing_evidence.extend(binding_support["missing_evidence_span_ids"])
        binding_missing_phrase.extend(binding_support["missing_phrase_unit_ids"])
        if binding_support["relation_type"] and binding_support["relation_type"] not in relation_types:
            relation_types.append(binding_support["relation_type"])

        sentence_matches = [_span_id(span) for span in scoped if _span_matches_sentence(sentence, _span_raw(span))]
        phrase_matches = [span_id for span_id, phrase_text in phrase_supports if _span_matches_sentence(sentence, phrase_text)]
        sentence_matches = list(dict.fromkeys(sentence_matches + phrase_matches))
        if binding_support["binding_used"]:
            sentence_matches = list(dict.fromkeys([*sentence_matches, *binding_support["used_evidence_span_ids"]]))

        sentence_claims.append({
            "sentence": sentence,
            "evidence_span_ids": sentence_matches,
            "binding_present": bool(binding),
            "binding_used": bool(binding_support["binding_used"]),
            "binding_sentence_id": binding_support["sentence_id"],
            "binding_evidence_span_ids": list(binding_support["used_evidence_span_ids"]),
            "binding_phrase_unit_ids": list(binding_support["used_phrase_unit_ids"]),
            "binding_relation_type": binding_support["relation_type"],
            "declared_evidence_span_ids": list(binding_support["declared_evidence_span_ids"]),
            "declared_phrase_unit_ids": list(binding_support["declared_phrase_unit_ids"]),
        })

        step14_reason = _step14_unbacked_reason(sentence, evidence_text)
        if step14_reason:
            reasons.append(step14_reason)
            matched.append(sentence)
            unsupported.append(sentence)
        elif sentence_matches:
            matched_ids.extend(sentence_matches)
            if binding_support["binding_used"]:
                binding_supported_count += 1
        else:
            unsupported.append(sentence)

    if unsupported:
        reasons.append(REJECTION_UNSUPPORTED_SENTENCE)
        matched.extend(unsupported)
    if declared and not set(declared).intersection(matched_ids):
        reasons.append(REJECTION_DECLARED_EVIDENCE_NOT_REFLECTED)

    coverage_ratio = 0.0 if not body else (len(body) - len(unsupported)) / max(1, len(body))
    step6 = {
        "version": BINDING_AWARE_GROUNDING_VERSION,
        "target_step": "6_binding_aware_grounding",
        "binding_aware_grounding": True,
        "binding_present": bool(binding_rows),
        "binding_count": len(binding_rows),
        "binding_used": bool(binding_supported_count),
        "binding_supported_sentence_count": binding_supported_count,
        "binding_missing_evidence_span_ids": list(dict.fromkeys(binding_missing_evidence)),
        "binding_missing_phrase_unit_ids": list(dict.fromkeys(binding_missing_phrase)),
        "relation_types": relation_types,
        "surface_threshold_relaxed": False,
        "raw_input_included": False,
    }
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
            "binding_aware_grounding": True,
            "step6_binding_aware_grounding": step6,
            "binding_present": bool(binding_rows),
            "binding_count": len(binding_rows),
            "binding_used": bool(binding_supported_count),
            "binding_supported_sentence_count": binding_supported_count,
            "binding_missing_evidence_span_ids": list(dict.fromkeys(binding_missing_evidence)),
            "binding_missing_phrase_unit_ids": list(dict.fromkeys(binding_missing_phrase)),
            "relation_types": relation_types,
            "raw_input_included": False,
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
    "BINDING_AWARE_GROUNDING_VERSION",
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
    "REJECTION_BINDING_EVIDENCE_NOT_FOUND",
    "REJECTION_BINDING_PHRASE_UNIT_NOT_FOUND",
    "REJECTION_UNSUPPORTED_DIAGNOSIS_LIKE",
    "REJECTION_UNSUPPORTED_PERSONALITY_LABEL",
    "REJECTION_UNSUPPORTED_GENERAL_KNOWLEDGE_COMPLETION",
    "REJECTION_UNSUPPORTED_ADVICE_ASSERTION",
    "REJECTION_GROUNDING_UNSUPPORTED_SENTENCE",
    "REJECTION_DECLARED_EVIDENCE_NOT_REFLECTED",
    "REJECTION_GROUNDING_DECLARED_EVIDENCE_NOT_REFLECTED",
]
