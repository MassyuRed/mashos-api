# -*- coding: utf-8 -*-
from __future__ import annotations

"""Safe understanding fallback for EmlisAI.

Used only when generated reply text fails final review / pre-return quality gate.
It avoids raw-anchor insertion and builds a deterministic companion reply from
safe shaped phrases.
"""

from typing import Any, List, Optional, Sequence

from emlis_ai_phrase_shaping_service import safe_phrases, shape_user_phrases
from emlis_ai_types import ShapedUserPhrase, WorldModel


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
    if text:
        return text
    return "Emlisです。"


def _presence_line(phrases: Sequence[ShapedUserPhrase], labels: Sequence[str]) -> str:
    if _has_role(phrases, "work_frustration", "anger_surface", "chat_relief", "missing_guidance", "effort_confusion"):
        return "ここでは、悔しさも、むかつきも、癒されたい気持ちも、雑に扱いません。"
    if "怒り" in labels and "悲しみ" in labels:
        return "ここでは、悲しみも怒りも、無理にきれいにしなくて大丈夫です。"
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

    if _has_role(phrases, "sadness_surface") and _has_role(phrases, "work_frustration"):
        lines.append("泣きそうになるくらい嫌になる時があるのに、そのまま折れるのは悔しいし、もったいないとも感じていたのですね。")
        if _has_role(phrases, "missing_guidance", "effort_confusion"):
            lines.append("むかつく気持ちの奥には、本当は「どう頑張ればいいのか」を教えてほしい気持ちも近くにありました。")
        if _has_role(phrases, "mentor_attachment", "fatigue_accumulation", "anger_surface"):
            lines.append("好きな先輩以外の時はミスしても知らないと思いたくなるくらい、最近はかなりイライラが溜まっていたのだと思います。")
        if _has_role(phrases, "chat_relief", "relief_source"):
            lines.append("その重さを忘れたい時に、チャットで話す時間が少し癒しになっていたのですね。")
        lines.append(_presence_line(phrases, labels))
        return "\n".join(line for line in lines if line).strip()

    # Personal-space / self-awareness conflict fallback.
    if _has_role(phrases, "boundary_violation", "self_awareness", "self_avoidance", "fear_of_rejection"):
        lines.append("パーソナルスペースに入ってしまったことだけでなく、怒ると知っていながら触れてしまった自覚もあったのですね。")
        if _has_role(phrases, "justification", "self_avoidance", "self_fault_awareness"):
            lines.append("理由を置きたくなる一方で、自分の非を見たくない自分にも気づいていて、そこが苦しかったのだと思います。")
        if _has_role(phrases, "fear_of_rejection"):
            lines.append("その自分ごと嫌われてしまいそうで、悲しみや不安が重なっていたのですね。")
        lines.append(_presence_line(phrases, labels))
        return "\n".join(line for line in lines if line).strip()

    if phrases:
        first = phrases[0].sentence_fragment or phrases[0].phrase
        lines.append(f"あなたは、{first}ことを、少しでも言葉にしたかったのですね。")
        if len(phrases) >= 2:
            second = phrases[1].sentence_fragment or phrases[1].phrase
            lines.append(f"そこには、{second}気持ちも近くにありました。")
    elif labels:
        joined = "と".join(labels[:2]) if len(labels) <= 2 else "、".join(labels[:-1]) + "、そして" + labels[-1]
        lines.append(f"今日は、{joined}が近くにあったのですね。")
        lines.append("まだ全部をきれいに言葉にしきれなくても、そのまま置いて大丈夫です。")
    else:
        lines.append("今日は、言葉にしきれない気持ちを少し置いておきたかったのですね。")
    lines.append(_presence_line(phrases, labels))
    return "\n".join(line for line in lines if line).strip()


__all__ = ["build_safe_understanding_fallback"]
