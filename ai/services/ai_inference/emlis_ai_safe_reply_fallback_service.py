# -*- coding: utf-8 -*-
from __future__ import annotations

"""Generic safe understanding fallback for EmlisAI.

Fallback is used after a generated reply fails review.  It must never return a
memorized answer for a sample input.  It builds a small but grounded reply from
current-input meaning blocks or safe shaped phrases.
"""

from typing import Any, List, Optional, Sequence

from emlis_ai_phrase_shaping_service import safe_phrases, shape_user_phrases
from emlis_ai_types import InputMeaningBlock, ShapedUserPhrase, WorldModel


def _clean(value: Any) -> str:
    return str(value or "").strip()


def _greeting_line(greeting_text: Any) -> str:
    return _clean(greeting_text) or "Emlisです。"


def _selected_labels(world_model: Optional[WorldModel]) -> List[str]:
    if world_model is None:
        return []
    selected = list(getattr(world_model.facts, "selected_emotions", []) or [])
    labels = [str(getattr(item, "type", "") or "").strip() for item in selected if str(getattr(item, "type", "") or "").strip()]
    if labels:
        return labels
    return [str(item or "").strip() for item in list(getattr(world_model.facts, "current_emotion_labels", []) or []) if str(item or "").strip()]


def _meaning_blocks(world_model: Optional[WorldModel]) -> List[InputMeaningBlock]:
    if world_model is None:
        return []
    return list(getattr(world_model.facts, "meaning_blocks", []) or [])


def _coverage_plan(world_model: Optional[WorldModel]):
    return getattr(getattr(world_model, "facts", None), "meaning_coverage_plan", None) if world_model is not None else None


def _value_observation_lines(world_model: Optional[WorldModel], *, limit: int = 1) -> List[str]:
    if world_model is None:
        return []
    out: List[str] = []
    for signal in list(getattr(world_model.facts, "value_observation_signals", []) or [])[: max(0, int(limit))]:
        text = _clean(getattr(signal, "emlis_text", "") or getattr(signal, "value_conversion", ""))
        if text and text not in out:
            out.append(text)
    return out


def _presence_line(blocks: Sequence[InputMeaningBlock], phrases: Sequence[ShapedUserPhrase], labels: Sequence[str]) -> str:
    roles = {str(getattr(item, "role", "") or "") for item in list(blocks or []) + list(phrases or [])}
    if {"self_suppression", "self_protection", "support_need", "burden_avoidance"} & roles:
        return "ここでは、抑えてきた気持ちも、自分を守ろうとしている気持ちも、どちらも大切に扱います。"
    if {"wish_or_hope", "fear_or_disappointment", "effort_direction"} & roles:
        return "ここでは、願いも怖さも、今できることを大切にしたい気持ちも、小さく扱いません。"
    if {"anger_or_frustration", "sadness_or_pain", "relief_source"} & roles:
        return "ここでは、しんどさも、怒りも、少し楽になりたい気持ちも、雑に扱いません。"
    if "怒り" in labels and "悲しみ" in labels:
        return "ここでは、悲しみも怒りも、無理にきれいにしなくて大丈夫です。"
    return "ここに置いてくれた言葉を、Emlisは軽く扱いません。"



def _as_topic(text: str) -> str:
    clean = _clean(text).rstrip("。")
    if not clean:
        return ""
    if clean.endswith(("こと", "気持ち", "願い", "状態", "感覚", "不安", "怖さ", "思い")):
        return clean
    return f"{clean}こと"

def _line_from_block(block: InputMeaningBlock, *, index: int) -> str:
    summary = _clean(getattr(block, "summary", ""))
    role = str(getattr(block, "role", "") or "")
    if not summary:
        return ""
    summary = summary.rstrip("。")
    if index == 0:
        return f"あなたは、{_as_topic(summary)}を、今ここに置こうとしているのですね。"
    if role in {"fear_or_disappointment", "limit_or_exhaustion", "sadness_or_pain", "anger_or_frustration"}:
        return f"そこには、{summary}感覚もありました。"
    if role in {"support_need", "self_protection", "effort_direction", "wish_or_hope"}:
        return f"同時に、{_as_topic(summary)}も大切な場所として見えています。"
    if role in {"self_suppression", "burden_avoidance", "self_view"}:
        return f"その背景には、{summary}流れもありました。"
    return f"そこには、{_as_topic(summary)}も含まれていました。"


def _line_from_phrase(phrase: ShapedUserPhrase, *, index: int) -> str:
    fragment = _clean(getattr(phrase, "sentence_fragment", "") or getattr(phrase, "phrase", ""))
    role = str(getattr(phrase, "role", "") or "")
    if not fragment:
        return ""
    fragment = fragment.rstrip("。")
    if index == 0:
        return f"あなたは、{_as_topic(fragment)}を言葉にしようとしていたのですね。"
    if role in {"fear_or_disappointment", "sadness_or_pain", "anger_or_frustration"}:
        return f"そこには、{fragment}感覚も近くにありました。"
    return f"そこには、{_as_topic(fragment)}も一緒にありました。"


def build_safe_understanding_fallback(
    *,
    current_input: dict[str, Any],
    world_model: Optional[WorldModel],
    greeting_text: Any = "",
) -> str:
    lines: List[str] = [_greeting_line(greeting_text)]
    blocks = _meaning_blocks(world_model)
    coverage = _coverage_plan(world_model)
    phrases = safe_phrases(list(getattr(getattr(world_model, "facts", None), "shaped_user_phrases", []) or [])) if world_model is not None else []
    if not phrases:
        anchors = list(getattr(getattr(world_model, "facts", None), "user_word_anchors", []) or []) if world_model is not None else []
        phrases = safe_phrases(shape_user_phrases(anchors=anchors, current_input=current_input))
    labels = _selected_labels(world_model)
    value_lines = _value_observation_lines(world_model)

    if blocks:
        clear_long = bool(getattr(coverage, "clear_long_input", False)) if coverage is not None else False
        limit = 6 if clear_long else 3
        ordered = sorted(blocks, key=lambda block: (-float(getattr(block, "priority", 0.0) or 0.0), str(getattr(block, "block_key", "") or "")))[:limit]
        for idx, block in enumerate(ordered):
            line = _line_from_block(block, index=idx)
            if line:
                lines.append(line)
        for line in value_lines:
            if line and line not in lines:
                lines.append(line)
        lines.append(_presence_line(ordered, phrases, labels))
        return "\n".join(line for line in lines if line).strip()

    if phrases:
        for idx, phrase in enumerate(phrases[:3]):
            line = _line_from_phrase(phrase, index=idx)
            if line:
                lines.append(line)
        for line in value_lines:
            if line and line not in lines:
                lines.append(line)
        lines.append(_presence_line([], phrases, labels))
        return "\n".join(line for line in lines if line).strip()

    if labels:
        joined = "と".join(labels[:2]) if len(labels) <= 2 else "、".join(labels[:-1]) + "、そして" + labels[-1]
        lines.append(f"今日は、{joined}が近くにあったのですね。")
        if value_lines:
            lines.extend(value_lines)
        else:
            lines.append("まだ全部をきれいに言葉にしきれなくても、そのまま置いて大丈夫です。")
    else:
        lines.append("今日は、言葉にしきれない気持ちを少し置いておきたかったのですね。")
        lines.extend(value_lines)
    lines.append(_presence_line([], phrases, labels))
    return "\n".join(line for line in lines if line).strip()


__all__ = ["build_safe_understanding_fallback"]
