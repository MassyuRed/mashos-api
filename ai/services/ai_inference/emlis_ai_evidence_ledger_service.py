# -*- coding: utf-8 -*-
from __future__ import annotations

"""Evidence ledger for EmlisAI multi-perspective observation.

This layer stores source spans only. It does not produce user-facing text and
it does not turn a span into an interpretation.
"""

import re
from typing import Any, Dict, List, Tuple

from emlis_ai_types import EvidenceSpan

_SPLIT_RE = re.compile(r"[\n。.!！?？]+|(?<=[、,])")
_SPACE_RE = re.compile(r"\s+")

_SELF_AWARENESS_RE = re.compile(r"(分かって|わかって|分かる|分かっ|自分でも|ちゃんと見|理解して|気づいて)")
_LIMIT_RE = re.compile(r"(逃げ出|投げ出|もう無理|限界|休みたい|疲れ|しんど|苦し|分からな|わからな|泣き|ボロボロ|崩れ|気が抜け)")
_WISH_RE = re.compile(r"(したい|いたい|ありたい|欲しい|ほしい|願い|普通に生活|楽しみたい|繋がっていたい|つながっていたい|過ごしたい|優先したい|整え)")
_CONSTRAINT_RE = re.compile(r"(気をつけ|気を付け|不便|悪化|できない|出来ない|制約|我慢|無視|責め|ミス|怖|こわ|圧|来られる|追いつ)")
_FEAR_RE = re.compile(r"(怖|こわ|不安|心配|ダメージ|悪化|責め|ミス)")
_VALUE_RE = re.compile(r"(嬉し|うれし|リラックス|楽しい|大切|好き|整え|守り|安心|休ま|家のこと|優先)")
_RELATION_RE = re.compile(r"(でも|だけど|けど|一方|同時に|その中で|ただ|なのに|からこそ|だからこそ|とはいえ)")
_EMOTION_WORD_RE = re.compile(r"(喜び|悲しみ|怒り|不安|平穏|自己理解|恐れ|焦り|寂し|さびし|嬉し|怖|こわ|しんど|苦し)")
_SAFETY_RISK_RE = re.compile(r"(死にたい|消えたい|自傷|殺したい|OD|首を吊|飛び降り|リスカ)")


def _clean(text: Any) -> str:
    return _SPACE_RE.sub(" ", str(text or "").replace("\u3000", " ")).strip(" 、,\t")


def _split_clauses(text: str, *, max_len: int = 72) -> List[Tuple[str, int, int]]:
    out: List[Tuple[str, int, int]] = []
    if not text:
        return out
    cursor = 0
    for part in _SPLIT_RE.split(text):
        raw = part
        idx = text.find(raw, cursor) if raw else -1
        if idx < 0:
            idx = cursor
        cursor = idx + len(raw)
        value = _clean(raw)
        if not value:
            continue
        if len(value) <= max_len:
            out.append((value, idx, idx + len(raw)))
            continue
        # Long sentence: cut at soft Japanese separators without losing order.
        chunks = re.split(r"(?<=、)|(?<=,)|(?<=\s)", value)
        start = idx
        buffer = ""
        for chunk in chunks:
            c = _clean(chunk)
            if not c:
                continue
            if len(buffer) + len(c) > max_len and buffer:
                out.append((_clean(buffer), start, start + len(buffer)))
                start += len(buffer)
                buffer = c
            else:
                buffer = f"{buffer}{c}" if not buffer else f"{buffer}{c}"
        if buffer:
            out.append((_clean(buffer), start, start + len(buffer)))
    return out


def _detect_type(text: str, selected_emotions: List[str]) -> str:
    if _SAFETY_RISK_RE.search(text):
        return "safety_risk"
    if _RELATION_RE.search(text):
        return "relation_marker"
    if _SELF_AWARENESS_RE.search(text):
        return "self_awareness"
    if _LIMIT_RE.search(text):
        return "limit_signal"
    if "普通に" in text and "悪化" not in text:
        return "wish"
    if _CONSTRAINT_RE.search(text):
        return "constraint"
    if _WISH_RE.search(text):
        return "wish"
    if _FEAR_RE.search(text):
        return "fear"
    if _VALUE_RE.search(text):
        return "value"
    if any(em and em in text for em in selected_emotions) or _EMOTION_WORD_RE.search(text):
        return "emotion"
    return "event"


def build_evidence_ledger(current_input: Dict[str, Any]) -> List[EvidenceSpan]:
    selected_emotions = []
    for item in current_input.get("emotion_details") if isinstance(current_input.get("emotion_details"), list) else []:
        if isinstance(item, dict):
            t = _clean(item.get("type"))
            if t:
                selected_emotions.append(t)
    for item in current_input.get("emotions") if isinstance(current_input.get("emotions"), list) else []:
        t = _clean(item)
        if t and t not in selected_emotions:
            selected_emotions.append(t)

    spans: List[EvidenceSpan] = []

    def add(field: str, text: Any, *, base_offset: int = 0) -> None:
        raw_text = str(text or "")
        clauses = _split_clauses(raw_text)
        merged: List[Tuple[str, int, int]] = []
        idx = 0
        while idx < len(clauses):
            value, start, end = clauses[idx]
            # Drop isolated particles created by punctuation such as "..., と。".
            if value in {"と", "を", "に", "で", "が", "は"}:
                idx += 1
                continue
            # A newline often cuts Japanese particles in the middle of a thought.
            # Keep the source span readable before any interpretation happens.
            def _needs_continuation(v: str) -> bool:
                if v.endswith("こと"):
                    return False
                return v.endswith(("と", "を", "に", "で", "が", "は", "から"))
            while idx + 1 < len(clauses) and _needs_continuation(value):
                nxt, nstart, nend = clauses[idx + 1]
                value = _clean(f"{value}{nxt}")
                end = nend
                idx += 1
            merged.append((value, start, end))
            idx += 1
        for value, start, end in merged:
            detected = _detect_type(value, selected_emotions)
            spans.append(
                EvidenceSpan(
                    span_id=f"s{len(spans) + 1}",
                    raw_text=value,
                    start_index=base_offset + start,
                    end_index=base_offset + end,
                    detected_type=detected,
                    confidence=0.86 if detected != "event" else 0.72,
                    source_field=field,
                )
            )

    add("memo", current_input.get("memo"), base_offset=0)
    add("memo_action", current_input.get("memo_action"), base_offset=100000)

    for emotion in selected_emotions:
        spans.append(
            EvidenceSpan(
                span_id=f"s{len(spans) + 1}",
                raw_text=emotion,
                start_index=-1,
                end_index=-1,
                detected_type="emotion",
                confidence=1.0,
                source_field="emotion_details",
            )
        )

    categories = current_input.get("category") if isinstance(current_input.get("category"), list) else []
    for category in categories:
        value = _clean(category)
        if not value:
            continue
        spans.append(
            EvidenceSpan(
                span_id=f"s{len(spans) + 1}",
                raw_text=value,
                start_index=-1,
                end_index=-1,
                detected_type="event",
                confidence=0.76,
                source_field="category",
            )
        )

    return spans


__all__ = ["build_evidence_ledger"]
