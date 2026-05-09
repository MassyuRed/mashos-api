# -*- coding: utf-8 -*-
from __future__ import annotations

"""Conversation composer for EmlisAI.

Only this layer writes user-facing text. It receives an ObservationGraph and
EvidenceSpans. It does not receive sample replies or legacy wording lists.
"""

import re
from typing import Dict, List, Sequence, Tuple

from emlis_ai_types import EvidenceSpan, GraphClaim, ObservationGraph, RelationEdge
from emlis_ai_user_address_service import build_emlis_observation_greeting

_SPACE_RE = re.compile(r"\s+")
_QUOTE_WRAP_RE = re.compile(r"^[「『](.*)[」』]$")


def _clean(text: object, limit: int = 52) -> str:
    value = _SPACE_RE.sub(" ", str(text or "")).strip(" 、,。.!！?？")
    m = _QUOTE_WRAP_RE.match(value)
    if m:
        value = m.group(1).strip()
    if len(value) <= limit:
        return value
    return value[: limit - 1].rstrip("、,") + "…"


def _span_map(spans: Sequence[EvidenceSpan]) -> Dict[str, EvidenceSpan]:
    return {span.span_id: span for span in spans}


def _complete_wish_fragment(value: str, spans_by_id: Dict[str, EvidenceSpan]) -> str:
    text = _clean(value)
    if not text:
        return text
    if text.endswith("普通に") or text.endswith("普通に生活"):
        for span in spans_by_id.values():
            candidate = _clean(span.raw_text, 24)
            if candidate.endswith("したい") and candidate not in text:
                return f"{text}{candidate}"
    return text


def _edge_phrases(edge: RelationEdge, spans_by_id: Dict[str, EvidenceSpan]) -> Tuple[str, str]:
    values = [_clean(spans_by_id[sid].raw_text) for sid in edge.evidence_span_ids if sid in spans_by_id]
    values = [v for v in values if v]
    if len(values) >= 2:
        return _complete_wish_fragment(values[0], spans_by_id), _complete_wish_fragment(values[-1], spans_by_id)
    if len(values) == 1:
        return _complete_wish_fragment(values[0], spans_by_id), "まだ言葉にしきれない重さ"
    return "今の気持ち", "別の気持ち"


def _join_items(items: Sequence[str], *, limit: int = 3) -> str:
    values = []
    raw_values = [_clean(item, 34) for item in items]
    skip_next = False
    for idx, text in enumerate(raw_values):
        if skip_next:
            skip_next = False
            continue
        if text.endswith("普通に") and idx + 1 < len(raw_values) and raw_values[idx + 1].endswith("したい"):
            text = f"{text}{raw_values[idx + 1]}"
            skip_next = True
        if text and text not in values:
            values.append(text)
        if len(values) >= limit:
            break
    if not values:
        return ""
    if len(values) == 1:
        return values[0]
    return "、".join(values[:-1]) + "、そして" + values[-1]


def _line_primary(graph: ObservationGraph, spans_by_id: Dict[str, EvidenceSpan]) -> str:
    if graph.core_tensions:
        left, right = _edge_phrases(graph.core_tensions[0], spans_by_id)
        if graph.core_tensions[0].relation_type in {"limit_tension", "tension", "explicit_transition"}:
            return f"入力全体では、「{left}」という動きと、「{right}」という重さが、同じ場所でせめぎ合っています。"
        return f"入力全体では、「{left}」と「{right}」が、どちらか一方だけではなく並んでいます。"
    primary = _clean(graph.primary_state.text)
    if primary:
        return f"入力全体では、「{primary}」が中心に出ています。"
    return "今ここに出した言葉は、まだ一つの意味に決めきれないまま置かれています。"


def _line_pressure(graph: ObservationGraph) -> str:
    pressure = _join_items([item.text for item in graph.pressure_sources], limit=3)
    self_awareness = _join_items([item.text for item in graph.self_awareness], limit=2)
    if pressure and self_awareness:
        return f"負荷になっているのは「{pressure}」で、そこに「{self_awareness}」という自覚も重なっています。"
    if pressure:
        return f"負荷として強く出ているのは、「{pressure}」の部分です。"
    if self_awareness:
        return f"自分の中で「{self_awareness}」まで見えているから、簡単には流せない状態です。"
    return "言葉の流れには、外からは見えにくい緊張が含まれています。"


def _line_limit(graph: ObservationGraph) -> str:
    limits = _join_items([item.text for item in graph.limit_signals], limit=2)
    if not limits:
        return "まだ決めきれない揺れも、今の状態を形づくる大事な手がかりです。"
    return f"「{limits}」という言葉は、張りつめた状態が外へ出てきたサインとして扱います。"


def _line_value(graph: ObservationGraph) -> str:
    values = [item.text for item in graph.value_or_strength_signals if item.claim_type == "value_signal"]
    strengths = [item.text for item in graph.value_or_strength_signals if item.claim_type == "grounded_strength_signal"]
    value_text = _join_items(values, limit=3)
    strength_text = _join_items(strengths, limit=2)
    if value_text and strength_text:
        return f"それでも「{value_text}」を残していて、「{strength_text}」まで見ているところに、現実から目を逸らしきっていない力があります。"
    if value_text:
        return f"その中でも「{value_text}」が残っているので、苦しさだけで全部が埋まっているわけではありません。"
    if strength_text:
        return f"「{strength_text}」まで言葉にしているところには、自分の状態を見失わない力があります。"
    return "Emlisは、その揺れを一つの結論へ急がず、今のままの重さとして並べます。"


def _line_close(graph: ObservationGraph) -> str:
    primary = _clean(graph.primary_state.text, 34)
    if graph.limit_signals and graph.value_or_strength_signals:
        return "Emlisは、苦しさだけを取り出さず、その奥に残っている願いや自覚も一緒に追います。"
    if graph.core_tensions:
        return "Emlisは、片方だけを正解にせず、並んでいる気持ちの関係を一緒に見ます。"
    if primary:
        return f"Emlisは、「{primary}」を急いで片づけず、今の言葉として一緒に見ます。"
    return "Emlisは、今ここに出た言葉を急いで結論にせず、一緒に見ます。"


def _dedupe_lines(lines: Sequence[str]) -> List[str]:
    out: List[str] = []
    seen = set()
    for raw in lines:
        text = _SPACE_RE.sub(" ", str(raw or "")).strip()
        if not text:
            continue
        key = re.sub(r"[「」『』、。\s]", "", text)
        if key in seen:
            continue
        seen.add(key)
        out.append(text)
    return out


def compose_emlis_conversation(
    *,
    graph: ObservationGraph,
    evidence_spans: Sequence[EvidenceSpan],
    display_name: object = None,
    greeting_text: object = "",
) -> str:
    if graph.safety_boundaries:
        return ""
    spans_by_id = _span_map(evidence_spans)
    greeting = build_emlis_observation_greeting(display_name=display_name, greeting_text=greeting_text)
    target = max(3, min(7, int(graph.addressee_notes.sentence_target or 5)))
    lines = [
        greeting,
        _line_primary(graph, spans_by_id),
        _line_pressure(graph),
        _line_limit(graph),
        _line_value(graph),
        _line_close(graph),
    ]
    lines = _dedupe_lines(lines)
    if len(lines) > target + 1:
        # Keep greeting, primary and closing while trimming middle observations.
        greeting_line = lines[0:1]
        body = lines[1:-1]
        close = lines[-1:]
        body = body[: max(1, target - 1)]
        lines = [*greeting_line, *body, *close]
    return "\n".join(lines).strip()


__all__ = ["compose_emlis_conversation"]
