# -*- coding: utf-8 -*-
"""emotion_piece_generation_service.py

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

from piece_generated_display import (
    STATE_MASKED,
    STATE_READY,
    GeneratedReflectionDisplayResult,
    build_generated_reflection_display,
    compute_generated_answer_norm_hash,
)
from piece_text_formatter import STATE_BLOCKED, format_reflection_text
from piece_generated_identity import compute_generated_question_q_key
from piece_generation_policy import build_piece_generation_policy

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


def _append_once(values: List[str], value: str) -> None:
    text = str(value or "").strip()
    if text and text not in values:
        values.append(text)


def _merge_unique(*items: Sequence[Any]) -> List[str]:
    merged: List[str] = []
    for values in items:
        for value in values or []:
            _append_once(merged, str(value or ""))
    return merged


def _has_raw_attack_or_target_signal(text: Any) -> bool:
    raw = _collapse(text)
    return any(
        token in raw
        for token in (
            "ムカつく",
            "むかつく",
            "腹が立",
            "消えてほしい",
            "消えろ",
            "死ね",
            "殺",
            "晒",
            "許せない",
            "クソ",
            "ゴミ",
        )
    )


def _has_sensitive_or_attack_signal(flags: Sequence[str], actions: Sequence[str]) -> bool:
    joined = " ".join([*(str(x or "") for x in flags or []), *(str(x or "") for x in actions or [])])
    return any(
        token in joined
        for token in (
            "pii:",
            "mask:url",
            "mask:phone",
            "mask:email",
            "mask:address",
            "mask:handle",
            "mask:line_id",
            "abuse:",
            "privacy:doxxing",
            "block:severe",
        )
    )


def _build_abstracted_safe_preview_text(question: str, raw_answer: str) -> str:
    q = _collapse(question)
    raw = _collapse(raw_answer)
    has_anger = any(token in raw for token in ("怒", "腹が立", "ムカ", "嫌", "許せ", "消えて", "死ね", "殺"))
    has_url = any(token in raw.lower() for token in ("http://", "https://", "www."))
    has_contact = any(token in raw for token in ("電話", "住所", "連絡先", "LINE", "ライン", "メール", "@"))

    if "仕事で気にしていること" in q:
        return "仕事では、気持ちが強く揺れたことを気にしています。"
    if "仕事で大切にしていること" in q:
        return "仕事では、気持ちを落ち着けて向き合うことを大切にしています。"
    if "仕事で伸ばしたいこと" in q:
        return "仕事で伸ばしたいのは、落ち着いて向き合う力です。"
    if "最近気づいたこと" in q:
        return "最近気づいたのは、気持ちが強く動く場面があったことです。"
    if "最近気になること" in q:
        if has_url:
            return "最近気になっているのは、外から入ってくる情報で気持ちが動いたことです。"
        if has_contact or has_anger:
            return "最近気になっているのは、強い感情が残っていることです。"
        return "最近気になっているのは、気持ちがはっきり残っていることです。"
    if "最近の楽しみ" in q:
        return "最近の楽しみは、気持ちが少し軽くなる時間です。"
    if "最近夢中なこと" in q:
        return "最近夢中なのは、気持ちを少し外へ向けられる時間です。"
    if "大切にしていること" in q:
        return "大切にしているのは、気持ちを落ち着ける時間です。"
    if "気持ちを整える方法" in q:
        return "気持ちを整えるために、少し距離を置いて落ち着くことを大事にしています。"
    return "今の入力から見えてきたのは、気持ちが強く動いたことです。"


def _finalize_public_safe_preview_result(
    *,
    result: GeneratedReflectionDisplayResult,
    question: str,
    raw_answer: str,
    candidate_text: str,
    force_fallback: bool = False,
) -> GeneratedReflectionDisplayResult:
    source_safety = format_reflection_text(raw_answer)
    candidate_safety = format_reflection_text(candidate_text)
    flags = _merge_unique(result.flags, source_safety.flags, candidate_safety.flags)
    actions = _merge_unique(result.actions, source_safety.actions, candidate_safety.actions)
    if _has_raw_attack_or_target_signal(raw_answer):
        flags = _merge_unique(flags, ["abuse:attack"])
        actions = _merge_unique(actions, ["mask:abuse"])

    should_abstract = (
        force_fallback
        and _has_sensitive_or_attack_signal(flags, actions)
    ) or str(source_safety.display_state) == STATE_BLOCKED or str(candidate_safety.display_state) == STATE_BLOCKED

    if should_abstract:
        safe_text = _build_abstracted_safe_preview_text(question, raw_answer)
        safe_safety = format_reflection_text(safe_text)
        flags = _merge_unique(flags, safe_safety.flags, ["piece:abstracted_public_safe"])
        actions = _merge_unique(actions, safe_safety.actions, ["piece:abstracted_public_safe"])
        return replace(
            result,
            answer_display_text=safe_text,
            answer_display_state=STATE_READY,
            changed=True,
            flags=flags,
            actions=actions,
            answer_norm_hash=compute_generated_answer_norm_hash(safe_text),
            rewrite_needed=False,
        )

    display_text = str(candidate_safety.display_text or candidate_text or "").strip()
    display_state = str(candidate_safety.display_state or STATE_READY).strip().lower()
    if not display_text:
        display_text = _build_abstracted_safe_preview_text(question, raw_answer)
        display_state = STATE_READY
        flags = _merge_unique(flags, ["piece:abstracted_public_safe"])
        actions = _merge_unique(actions, ["piece:abstracted_public_safe"])

    if display_text != str(result.answer_display_text or "") or flags != list(result.flags or []) or actions != list(result.actions or []):
        return replace(
            result,
            answer_display_text=display_text,
            answer_display_state=STATE_MASKED if display_state == STATE_MASKED else STATE_READY,
            changed=True,
            flags=flags,
            actions=actions,
            answer_norm_hash=compute_generated_answer_norm_hash(display_text),
            rewrite_needed=False,
        )
    return result


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
        return _finalize_public_safe_preview_result(
            result=result,
            question=question,
            raw_answer=raw_answer,
            candidate_text=str(result.answer_display_text or ""),
        )

    fallback_text = _build_fallback_preview_text(question, raw_answer)
    flags = list(result.flags or [])
    if "preview:fallback_display" not in flags:
        flags.append("preview:fallback_display")
    actions = list(result.actions or [])
    if "preview:fallback_display" not in actions:
        actions.append("preview:fallback_display")

    fallback_result = replace(
        result,
        answer_display_text=fallback_text,
        answer_display_state=STATE_READY,
        changed=True,
        flags=flags,
        actions=actions,
        answer_norm_hash=compute_generated_answer_norm_hash(fallback_text),
        rewrite_needed=False,
    )
    return _finalize_public_safe_preview_result(
        result=fallback_result,
        question=question,
        raw_answer=raw_answer,
        candidate_text=fallback_text,
        force_fallback=True,
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
    answer_display_text = display_result.answer_display_text or _build_fallback_preview_text(question, raw_answer)
    piece_policy = build_piece_generation_policy(
        piece_text=answer_display_text,
        raw_answer=raw_answer,
        display_result=display_result,
        source_texts=text_candidates,
        emotion_input={
            "emotions": list(emotion_details or []),
            "memo": normalized_memo,
            "memo_action": normalized_memo_action,
            "category": normalized_categories,
        },
    )

    return {
        "question": question,
        "focus_key": focus_key,
        "q_key": compute_generated_question_q_key(question),
        "raw_answer": raw_answer,
        "answer_display_text": answer_display_text,
        "answer_display_state": display_result.answer_display_state,
        "answer_norm_hash": display_result.answer_norm_hash,
        "display_result": display_result,
        "piece_policy": piece_policy,
        "category": primary_category,
        "text_candidates": text_candidates,
    }


__all__ = [
    "generate_emotion_reflection_preview",
]
