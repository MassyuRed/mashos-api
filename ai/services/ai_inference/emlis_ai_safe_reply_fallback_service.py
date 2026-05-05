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
    if _has_role(phrases, "other_contribution", "own_happiness_wish", "present_effort_toward_wish", "concrete_life_wishes"):
        return "ここでは、誰かの幸せを願う気持ちも、自分の幸せを諦めたくない気持ちも、どちらも小さく扱いません。"
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

    meaning_blocks = list(getattr(getattr(world_model, "facts", None), "meaning_blocks", []) or []) if world_model is not None else []
    coverage = getattr(getattr(world_model, "facts", None), "meaning_coverage_plan", None) if world_model is not None else None
    if coverage is not None and bool(getattr(coverage, "clear_long_input", False)) and meaning_blocks:
        roles = {str(getattr(block, "role", "") or "") for block in meaning_blocks}
        if "other_contribution" in roles:
            lines.append("誰かの役に立てて、その人たちが幸せに笑ってくれるなら、それが自分の幸せに近いと感じているのですね。")
        if "self_dislike_from_halfway" in roles:
            lines.append("頑張ることも楽しむことも中途半端に感じて、自分のことを好きになれない気持ちもありました。")
        if "future_not_giving_up" in roles or "resignation_self" in roles or "betrayal_fear" in roles:
            lines.append("自分のことも今後のこともまだ諦めたくないのに、期待してまた裏切られたくないから、諦めている自分もいるのだと思います。")
        if "own_happiness_wish" in roles:
            lines.append("それでも、自分も幸せになりたい気持ちは残っていて、そこは本当は諦めたくない場所なのですね。")
        if "concrete_life_wishes" in roles:
            lines.append("好きなことをもっとして、納得いくまで楽しんで、素敵なパートナーと出会って幸せになりたい願いも、ちゃんとここにあります。")
        if "present_effort_toward_wish" in roles or "unreachable_wish" in roles:
            lines.append("その願いが今は手の届かないところに見えても、そこへ届くために、今頑張れることを大切にしたいのですね。")
        if "other_contribution" in roles or "own_happiness_wish" in roles:
            lines.append("ここでは、誰かの幸せを願う気持ちも、自分の幸せを諦めたくない気持ちも、どちらも小さく扱いません。")
            return "\n".join(line for line in lines if line).strip()
        if "state_awareness" in roles:
            lines.append("体も心もボロボロになってきていることを、自分でもちゃんと分かっているのですね。")
        if "effort_history" in roles:
            lines.append("ここまで頑張ってきた時間や、無理してきた時間が積み重なってきたからこそ、今の限界が見えてきているのだと思います。")
        if "continuation_wish" in roles or "not_want_to_quit" in roles:
            lines.append("それでも、もう少し頑張りたい気持ちは残っていて、投げ出したいわけでも、ここで終わりにしたいわけでもないのですね。")
        if "fatigue_or_limit" in roles or "collapse_anxiety" in roles:
            lines.append("ただ同時に、体が重かったり、気持ちがついてこなかったり、このまま無理を続けたら崩れてしまいそうな不安もちゃんとあります。")
        if "dual_holding" in roles:
            lines.append("頑張りたい気持ちもしんどい気持ちも、どちらかに切り捨てず、両方抱えたまま進みたいのだと思います。")
        if "paced_progress" in roles or "self_permission" in roles:
            lines.append("頑張れる日は少し前に進んで、しんどい日は立ち止まりながら、無理に削らず整えて進もうとしているのですね。")
        if "self_understanding" in roles:
            lines.append("今のあなたは弱いのではなく、自分の限界に気づけている状態です。")
        lines.append("ここでは、頑張りたい気持ちも、しんどさも、崩れそうな不安も、どれかひとつに削らずに大切にします。")
        return "\n".join(line for line in lines if line).strip()

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
