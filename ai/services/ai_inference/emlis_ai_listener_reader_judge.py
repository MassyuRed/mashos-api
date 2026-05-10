# -*- coding: utf-8 -*-
from __future__ import annotations

"""Listener reader judge for EmlisAI output.

This judge reads only the generated text. It does not use the source input so it
can answer the question: can a listener understand what Emlis is saying?
"""

import re
from typing import Any, List

from emlis_ai_types import ListenerReaderReport

_SENTENCE_SPLIT_RE = re.compile(r"(?<=[。！？!?])\s*|\n+")
_SECOND_PERSON_RE = re.compile(r"(あなたは|あなたの|あなたが|あなたに)")
_FIRST_PERSON_HIJACK_RE = re.compile(r"(^|[\n。！？!?])\s*(今の)?私[はがもに]|(^|[\n。！？!?])\s*私は")
_UNCLEAR_RE = re.compile(
    r"(こととしてちゃんと|大切な場所として|含まれていました|ありました|受け取りました|と思います|として見ています|"
    r"ここにいていいんだってこと|言葉の流れには|外からは見えにくい緊張|決めきれない揺れ|急いで片づけず|一緒に見ます)"
)
_REPORT_LIKE_RE = re.compile(r"(観測結果|判定|分析すると|構造としては|以下の|項目|レポート|結論として)")
_RELATION_RE = re.compile(
    r"(同じ場所|同じ中|並んで|せめぎ合|重なって|一方|だけではなく|離れていない|簡単には|"
    r"その二つ|二つの間|つながって|同時に|抱えて|混ざって|残って)"
)
_ADDRESSEE_RE = re.compile(r"(^[^\n]{0,32}さん、[^\n]{0,24}Emlisです。|^Emlisです。)")
_LISTING_RE = re.compile(r"(.+もありました。?\s*){2,}|(.+も含まれていました。?\s*){2,}")
_GENERIC_CLOSING_RE = re.compile(r"(小さく扱いません|軽く扱いません|今の言葉として一緒に見ます|一つの結論へ急がず)")


def _sentences(text: Any) -> List[str]:
    return [s.strip() for s in _SENTENCE_SPLIT_RE.split(str(text or "")) if s.strip()]


def _dedupe(values: List[str]) -> List[str]:
    return list(dict.fromkeys(values))


def judge_listener_readability(comment_text: Any) -> ListenerReaderReport:
    text = str(comment_text or "").strip()
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    sentences = _sentences(text)
    reasons: List[str] = []
    unclear: List[str] = []

    if not text:
        reasons.append("empty_text")
    if len(lines) < 3:
        reasons.append("too_short_for_observation")
    if len(lines) > 8:
        reasons.append("too_long_for_immediate_observation")
    if _SECOND_PERSON_RE.search(text):
        reasons.append("second_person_pronoun_present")
    if _FIRST_PERSON_HIJACK_RE.search(text):
        reasons.append("first_person_hijack")
    if _LISTING_RE.search(text):
        reasons.append("result_listing_pattern")
    if _GENERIC_CLOSING_RE.search(text):
        reasons.append("generic_fixed_closing")

    for sentence in sentences:
        if _UNCLEAR_RE.search(sentence):
            unclear.append(sentence)
    if unclear:
        reasons.append("unclear_legacy_phrase")

    addressee_clear = bool(_ADDRESSEE_RE.search(lines[0] if lines else ""))
    if not addressee_clear:
        reasons.append("addressee_not_clear")

    relation_count = sum(1 for sentence in sentences if _RELATION_RE.search(sentence))
    if relation_count < 1 and len(sentences) >= 3:
        reasons.append("relation_not_expressed")

    report_like = bool(_REPORT_LIKE_RE.search(text))
    if report_like:
        reasons.append("report_like_language")

    # Repeated ending shapes are a sign that the output is listing results.
    endings = [re.sub(r"^.*?(が|は|を|に|で)", "", s)[-10:] for s in sentences if len(s) >= 8]
    if len(endings) >= 3 and len(set(endings)) <= max(1, len(endings) // 2):
        reasons.append("repeated_sentence_endings")

    reasons = _dedupe(reasons)
    speaker_integrity_ok = "first_person_hijack" not in reasons and "second_person_pronoun_present" not in reasons
    conversational = not report_like and bool(addressee_clear) and len(lines) >= 3 and speaker_integrity_ok
    understandable = not reasons and speaker_integrity_ok and addressee_clear and conversational and relation_count >= 1

    summary = ""
    if sentences:
        body = [s for s in sentences if "Emlisです" not in s]
        summary = " / ".join(body[:2])[:160]

    return ListenerReaderReport(
        understandable=bool(understandable),
        addressee_clear=addressee_clear,
        speaker_integrity_ok=speaker_integrity_ok,
        conversational=conversational,
        report_like=report_like,
        summary_of_output=summary,
        unclear_sentences=unclear,
        rejection_reasons=reasons,
        confidence=0.88 if not reasons else 0.42,
    )


__all__ = ["judge_listener_readability"]
