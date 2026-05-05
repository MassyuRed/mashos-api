# -*- coding: utf-8 -*-
from __future__ import annotations

"""Safe understanding fallback for EmlisAI.

Fallback generation is generic and category-based.  It uses current-input meaning
blocks / shaped phrases; it never returns a sample-specific fixed answer.
"""

from typing import Any, List, Optional, Sequence

from emlis_ai_phrase_shaping_service import safe_phrases, shape_user_phrases
from emlis_ai_types import InputMeaningBlock, ShapedUserPhrase, WorldModel


def _clean(value: Any) -> str:
    return str(value or "").strip()


def _has_role(phrases: Sequence[ShapedUserPhrase], *roles: str) -> bool:
    role_set = set(roles)
    return any(item.role in role_set for item in phrases)


def _selected_labels(world_model: Optional[WorldModel]) -> List[str]:
    if world_model is None:
        return []
    selected = list(getattr(world_model.facts, "selected_emotions", []) or [])
    labels = [str(getattr(item, "type", "") or "").strip() for item in selected if str(getattr(item, "type", "") or "").strip()]
    if labels:
        return labels
    return [str(item or "").strip() for item in list(getattr(world_model.facts, "current_emotion_labels", []) or []) if str(item or "").strip()]


def _greeting_line(greeting_text: Any) -> str:
    text = _clean(greeting_text)
    return text or "Emlisです。"


def _block_summary(block: InputMeaningBlock) -> str:
    return str(getattr(block, "summary", "") or getattr(block, "title", "") or "").strip("。")


def _line_from_block(block: InputMeaningBlock) -> str:
    summary = _block_summary(block)
    if not summary:
        return ""
    if summary.endswith(("いる", "ある", "見ている", "気づいている", "感じている", "思っている", "しようとしている")):
        return f"{summary}のだと思います。"
    return f"{summary}。"


def _presence_from_blocks(blocks: Sequence[InputMeaningBlock], phrases: Sequence[ShapedUserPhrase], labels: Sequence[str]) -> str:
    high = [str(getattr(block, "title", "") or "").strip("。") for block in blocks[:3] if str(getattr(block, "title", "") or "").strip()]
    if high:
        return f"ここでは、{ '、'.join(high) }を、急いで小さくまとめず大切に扱います。"
    if _has_role(phrases, "anger_surface") and ("怒り" in labels or "悲しみ" in labels):
        return "ここでは、怒りも悲しみも、無理にきれいに整えなくて大丈夫です。"
    return "ここに置いてくれた言葉を、Emlisは軽く扱いません。"


def build_safe_understanding_fallback(
    *,
    current_input: dict[str, Any],
    world_model: Optional[WorldModel],
    greeting_text: Any = "",
) -> str:
    phrases = safe_phrases(list(getattr(getattr(world_model, "facts", None), "shaped_user_phrases", []) or [])) if world_model is not None else []
    if not phrases:
        anchors = list(getattr(getattr(world_model, "facts", None), "user_word_anchors", []) or []) if world_model is not None else []
        phrases = safe_phrases(shape_user_phrases(anchors=anchors, current_input=current_input))
    labels = _selected_labels(world_model)
    lines: List[str] = [_greeting_line(greeting_text)]

    meaning_blocks = list(getattr(getattr(world_model, "facts", None), "meaning_blocks", []) or []) if world_model is not None else []
    coverage = getattr(getattr(world_model, "facts", None), "meaning_coverage_plan", None) if world_model is not None else None
    if coverage is not None and bool(getattr(coverage, "clear_long_input", False)) and meaning_blocks:
        ordered = sorted(meaning_blocks, key=lambda item: (-float(getattr(item, "priority", 0.0) or 0.0), str(getattr(item, "role", ""))))
        for block in ordered[: max(4, min(7, len(ordered)))]:
            line = _line_from_block(block)
            if line and line not in lines:
                lines.append(line)
        lines.append(_presence_from_blocks(ordered, phrases, labels))
        return "\n".join(line for line in lines if line).strip()

    if phrases:
        first = phrases[0].sentence_fragment or phrases[0].phrase
        lines.append(f"あなたは、{first}ことを、少しでも言葉にしたかったのですね。")
        if len(phrases) >= 2:
            second = phrases[1].nominal or phrases[1].phrase
            lines.append(f"そこには、{second}も近くにありました。")
    elif labels:
        joined = "と".join(labels[:2]) if len(labels) <= 2 else "、".join(labels[:-1]) + "、そして" + labels[-1]
        lines.append(f"今日は、{joined}が近くにあったのですね。")
        lines.append("まだ全部をきれいに言葉にしきれなくても、そのまま置いて大丈夫です。")
    else:
        lines.append("今日は、言葉にしきれない気持ちを少し置いておきたかったのですね。")
    lines.append(_presence_from_blocks([], phrases, labels))
    return "\n".join(line for line in lines if line).strip()


__all__ = ["build_safe_understanding_fallback"]
