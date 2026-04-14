# -*- coding: utf-8 -*-
"""emotion_reflection_generation_service.py

Deterministic preview generator for the new emotion-generated Reflection flow.

Scope
-----
- Input is limited to the current emotion submission payload.
- Output is suitable for preview and later publish.
- This module intentionally stays rule-based / deterministic for the first step.
"""

from __future__ import annotations

from dataclasses import replace
from typing import Any, Dict, Iterable, List, Optional, Sequence, Tuple

from generated_reflection_display import (
    STATE_READY,
    GeneratedReflectionDisplayResult,
    build_generated_reflection_display,
    compute_generated_answer_norm_hash,
)
from generated_reflection_identity import compute_generated_question_q_key

SELF_INSIGHT_EMOTION_TYPE = "自己理解"
_NEGATIVE_EMOTIONS = {"悲しみ", "怒り", "不安"}
_POSITIVE_EMOTIONS = {"喜び", "平穏"}
_STRENGTH_WEIGHT = {"weak": 1, "medium": 2, "strong": 3}


def _collapse(text: Any) -> str:
    return " ".join(str(text or "").replace("\r", " ").replace("\n", " ").split()).strip()


def _first_non_empty(*values: Any) -> str:
    for value in values:
        text = _collapse(value)
        if text:
            return text
    return ""


def _unique_texts(values: Iterable[Any]) -> List[str]:
    out: List[str] = []
    seen = set()
    for value in values:
        text = _collapse(value)
        if not text or text in seen:
            continue
        seen.add(text)
        out.append(text)
    return out


def _dominant_emotion(emotion_details: Sequence[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    candidates = []
    for item in emotion_details or []:
        if not isinstance(item, dict):
            continue
        emotion_type = _collapse(item.get("type"))
        if not emotion_type:
            continue
        strength = str(item.get("strength") or "medium").strip().lower()
        score = _STRENGTH_WEIGHT.get(strength, 2)
        candidates.append((score, emotion_type, strength, item))
    if not candidates:
        return None
    candidates.sort(key=lambda value: (value[0], value[1]), reverse=True)
    return dict(candidates[0][3])


def _pick_question(
    *,
    emotion_details: Sequence[Dict[str, Any]],
    categories: Sequence[str],
    memo: str,
    memo_action: str,
) -> Tuple[str, str]:
    dominant = _dominant_emotion(emotion_details)
    dominant_type = _collapse((dominant or {}).get("type"))
    category_set = set(_unique_texts(categories or []))
    compact_source = " ".join(_unique_texts([memo, memo_action, *list(category_set)]))

    if "仕事" in category_set:
        if dominant_type in _NEGATIVE_EMOTIONS:
            return "仕事で気にしていることは？", "work"
        if dominant_type in _POSITIVE_EMOTIONS:
            return "仕事で大切にしていることは？", "work"
        return "仕事で伸ばしたいことは？", "work"

    if dominant_type == SELF_INSIGHT_EMOTION_TYPE:
        if memo or memo_action:
            return "最近気づいたことは？", "notice"
        return "大切にしていることは？", "values"

    if dominant_type in _NEGATIVE_EMOTIONS:
        if "健康" in category_set or "生活" in category_set:
            return "気持ちを整える方法は？", "care"
        return "最近気になることは？", "concern"

    if dominant_type in _POSITIVE_EMOTIONS:
        if "趣味" in category_set or "恋愛" in category_set or "人間関係" in category_set:
            return "最近の楽しみは？", "joy"
        return "大切にしていることは？", "values"

    if any(key in compact_source for key in ("気づ", "分か", "見えて")):
        return "最近気づいたことは？", "notice"

    return "最近気になることは？", "concern"


def _build_raw_answer(
    *,
    emotion_details: Sequence[Dict[str, Any]],
    memo: str,
    memo_action: str,
    categories: Sequence[str],
) -> str:
    parts = _unique_texts([memo_action, memo])
    if parts:
        if len(parts) >= 2:
            text = f"{parts[0]}。そのとき、{parts[1]}"
        else:
            text = parts[0]
    else:
        dominant = _dominant_emotion(emotion_details)
        dominant_type = _collapse((dominant or {}).get("type"))
        if dominant_type == SELF_INSIGHT_EMOTION_TYPE:
            text = "自分の中で気づいたことがありました"
        elif dominant_type:
            text = f"{dominant_type}を強く感じました"
        else:
            text = "心に残る出来事がありました"

    category_text = _collapse(" / ".join(_unique_texts(categories or [])))
    if category_text:
        text = f"{text}。特に{category_text}のこととして意識に残っています"
    return _collapse(text)


def _build_fallback_preview_text(question: str, raw_answer: str) -> str:
    source = _collapse(raw_answer)
    if not source:
        source = "今の入力から生まれた気づき"

    if "仕事で気にしていること" in question:
        return f"仕事では、{source}を気にしています。"
    if "仕事で大切にしていること" in question:
        return f"仕事では、{source}を大切にしています。"
    if "仕事で伸ばしたいこと" in question:
        return f"仕事で伸ばしたいのは、{source}です。"
    if "最近気づいたこと" in question:
        return f"最近気づいたのは、{source}です。"
    if "最近気になること" in question:
        return f"最近気になっているのは、{source}です。"
    if "最近の楽しみ" in question:
        return f"最近の楽しみは、{source}です。"
    if "最近夢中なこと" in question:
        return f"最近夢中なのは、{source}です。"
    if "大切にしていること" in question:
        return f"大切にしているのは、{source}です。"
    if "気持ちを整える方法" in question:
        return f"気持ちを整えるために、{source}を大事にしています。"
    return f"今の入力から見えてきたのは、{source}です。"


def _ensure_preview_display_result(
    *,
    question: str,
    raw_answer: str,
    category: Optional[str],
    focus_key: Optional[str],
    text_candidates: Sequence[str],
) -> GeneratedReflectionDisplayResult:
    result = build_generated_reflection_display(
        question=question,
        raw_answer=raw_answer,
        category=category,
        focus_key=focus_key,
        topic_summary_text=raw_answer,
        text_candidates=text_candidates,
    )

    if result.answer_display_text and str(result.answer_display_state).lower() == STATE_READY:
        return result

    fallback_text = _build_fallback_preview_text(question, raw_answer)
    flags = list(result.flags or [])
    if "preview:fallback_display" not in flags:
        flags.append("preview:fallback_display")
    actions = list(result.actions or [])
    if "preview:fallback_display" not in actions:
        actions.append("preview:fallback_display")

    return replace(
        result,
        answer_display_text=fallback_text,
        answer_display_state=STATE_READY,
        changed=True,
        flags=flags,
        actions=actions,
        answer_norm_hash=compute_generated_answer_norm_hash(fallback_text),
        rewrite_needed=False,
    )


def generate_emotion_reflection_preview(
    *,
    emotion_details: Sequence[Dict[str, Any]],
    memo: Optional[str],
    memo_action: Optional[str],
    categories: Optional[Sequence[str]],
) -> Dict[str, Any]:
    normalized_memo = _collapse(memo)
    normalized_memo_action = _collapse(memo_action)
    normalized_categories = _unique_texts(categories or [])
    question, focus_key = _pick_question(
        emotion_details=emotion_details,
        categories=normalized_categories,
        memo=normalized_memo,
        memo_action=normalized_memo_action,
    )
    raw_answer = _build_raw_answer(
        emotion_details=emotion_details,
        memo=normalized_memo,
        memo_action=normalized_memo_action,
        categories=normalized_categories,
    )
    text_candidates = _unique_texts([normalized_memo, normalized_memo_action, *normalized_categories])
    primary_category = normalized_categories[0] if normalized_categories else None
    display_result = _ensure_preview_display_result(
        question=question,
        raw_answer=raw_answer,
        category=primary_category,
        focus_key=focus_key,
        text_candidates=text_candidates,
    )

    return {
        "question": question,
        "focus_key": focus_key,
        "q_key": compute_generated_question_q_key(question),
        "raw_answer": raw_answer,
        "answer_display_text": display_result.answer_display_text or _build_fallback_preview_text(question, raw_answer),
        "answer_display_state": display_result.answer_display_state,
        "answer_norm_hash": display_result.answer_norm_hash,
        "display_result": display_result,
        "category": primary_category,
        "text_candidates": text_candidates,
    }


__all__ = [
    "generate_emotion_reflection_preview",
]
