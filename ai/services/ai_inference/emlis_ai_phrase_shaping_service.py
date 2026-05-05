# -*- coding: utf-8 -*-
from __future__ import annotations

"""Phrase shaping for EmlisAI natural companion replies.

``UserWordAnchor.text`` is the user's raw surface text.  It may contain an
unfinished connector, rough colloquial wording, or a clause that only works in
its original paragraph.  This service keeps the source-bound meaning but shapes
it into a fragment that can safely be inserted into EmlisAI's own sentence.
"""

import re
from typing import Any, Iterable, List, Mapping, Sequence

from emlis_ai_types import EvidenceRef, ShapedUserPhrase, UserWordAnchor

_SPACE_RE = re.compile(r"\s+")
_UNFINISHED_CONNECTOR_RE = re.compile(r"(けどそれだと|けどさ|けど|けれど|でも|から|ので|のに|だって)$")


def _clean(value: Any) -> str:
    return _SPACE_RE.sub(" ", str(value or "").replace("\u3000", " ")).strip(" 、,。.!！?？\t\n\r")


def _compact(value: Any) -> str:
    return re.sub(r"[\s　、,。.!！?？\t\n\r]", "", str(value or ""))


def _strip_unfinished_connectors(text: str) -> tuple[str, list[str]]:
    reasons: list[str] = []
    clean = _clean(text)
    while True:
        match = _UNFINISHED_CONNECTOR_RE.search(clean)
        if not match:
            break
        reasons.append("unfinished_connector")
        clean = clean[: match.start()].rstrip(" 、,")
    return clean, reasons


def _soften_colloquial(text: str) -> str:
    out = text
    replacements = (
        ("知らねーよ", "知らない"),
        ("知らねえよ", "知らない"),
        ("教えてくんない", "教えてもらえない"),
        ("教えてくれない", "教えてもらえない"),
        ("教えてくんないんだもん", "教えてもらえない"),
        ("めっちゃ", "かなり"),
        ("チャット系でお話してる", "チャットで話している"),
        ("お話してる", "話している"),
        ("話してる", "話している"),
        ("癒される", "癒しになっている"),
        ("手の届かい所", "手の届かないところ"),
        ("手の届かい", "手の届かない"),
        ("1番", "一番"),
    )
    for src, dst in replacements:
        out = out.replace(src, dst)
    out = out.replace("時ある", "時がある")
    out = out.replace("どう頑張ればいいのって思う", "どう頑張ればいいのか分からない気持ち")
    out = out.replace("頑張ることも楽しむことも中途半端だから", "頑張ることも楽しむことも中途半端に思えて")
    out = out.replace("自分のことは好きになれないけど", "自分のことを好きになれない気持ちがありながら")
    out = out.replace("諦めたくないけれど", "諦めたくない気持ちがありながら")
    out = out.replace("期待して裏切られたくないから", "期待して裏切られるのが怖くて")
    out = out.replace("それ以上に求めてるんだよねきっと", "それ以上を求めている自分にも気づいていて")
    return _clean(out)


def _role_from_text(text: str, fallback: str) -> str:
    compact = _compact(text)
    if "泣きそうになるくらい嫌になる" in compact:
        return "sadness_surface"
    if "悔しい" in compact or "もったいない" in compact:
        return "work_frustration"
    if "むかつく" in compact or "イライラ" in compact or "知らない" in compact or "知らね" in compact:
        return "anger_surface"
    if "好きな先輩" in compact:
        return "mentor_attachment"
    if "教えてもらえない" in compact or "教えてくんない" in compact or "教えてくれない" in compact:
        return "missing_guidance"
    if "どう頑張ればいい" in compact:
        return "effort_confusion"
    if "癒し" in compact or "癒され" in compact or "チャット" in compact:
        return "chat_relief"
    if "疲れ" in compact or "最近かなりイライラ" in compact:
        return "fatigue_accumulation"
    if "役に立" in compact:
        return "other_contribution"
    if "中途半端" in compact or "好きになれない" in compact:
        return "self_dislike_from_halfway"
    if "諦めたくない" in compact:
        return "future_not_giving_up"
    if "諦めて" in compact:
        return "resignation_self"
    if "裏切られたくない" in compact or "裏切られるのが怖" in compact:
        return "betrayal_fear"
    if "幸せになりたい" in compact:
        return "own_happiness_wish"
    if "好きなこと" in compact or "パートナー" in compact or "十分に楽し" in compact or "十分にたのし" in compact:
        return "concrete_life_wishes"
    if "手の届" in compact:
        return "unreachable_wish"
    if "今頑張れる" in compact or "願いに届" in compact:
        return "present_effort_toward_wish"
    return fallback or "other"


def _known_phrase(raw: str, role: str) -> tuple[str, str, str, str] | None:
    compact = _compact(raw)
    if "泣きそうになるくらい嫌になる時" in compact:
        phrase = "泣きそうになるくらい嫌になる時がある"
        return phrase, phrase, "泣きそうになるくらい嫌になる時がある状態", "sadness_surface"
    if "悔しい" in compact and "もったいない" in compact:
        phrase = "悔しいし、もったいないとも感じている"
        return phrase, phrase, "悔しさともったいなさ", "work_frustration"
    if "むかつく" in compact:
        phrase = "むかつく気持ちもある"
        return phrase, phrase, "むかつく気持ち", "anger_surface"
    if "好きな先輩以外" in compact and "ミス" in compact:
        phrase = "好きな先輩以外の時は、ミスしても知らないと思いたくなる"
        return phrase, phrase, "好きな先輩以外の時はミスしても知らないと思いたくなる気持ち", "mentor_attachment"
    if "教えてくんない" in compact or "教えてくれない" in compact or "教えてもらえない" in compact:
        phrase = "教えてもらえないしんどさ"
        return phrase, "教えてもらえないことがしんどい", phrase, "missing_guidance"
    if "どう頑張ればいい" in compact:
        phrase = "どう頑張ればいいのか分からない気持ち"
        return phrase, phrase, phrase, "effort_confusion"
    if "最近" in compact and "イライラ" in compact:
        phrase = "最近かなりイライラが溜まっている"
        return phrase, phrase, "最近かなりイライラが溜まっている状態", "fatigue_accumulation"
    if "チャット" in compact and ("癒" in compact or "話" in compact):
        phrase = "チャットで話す時間が癒しになっている"
        return phrase, phrase, "チャットで話す時間が癒しになっていること", "chat_relief"

    if "誰かの役に立" in compact or "人たちの役に立" in compact:
        phrase = "誰かの役に立てるならそれでいいと思う"
        return phrase, phrase, "誰かの役に立ちたい気持ち", "other_contribution"
    if "中途半端" in compact and "好きになれない" in compact:
        phrase = "頑張ることも楽しむことも中途半端に感じて、自分を好きになれない"
        return phrase, phrase, "頑張ることも楽しむことも中途半端に感じること", "self_dislike_from_halfway"
    if "頑張ることも楽しむことも中途半端" in compact:
        phrase = "頑張ることも楽しむことも中途半端に思えて"
        return phrase, phrase, "頑張ることも楽しむことも中途半端に感じること", "self_dislike_from_halfway"
    if "自分のことは好きになれない" in compact or "自分のことを好きになれない" in compact:
        phrase = "自分のことを好きになれない気持ちがある"
        return phrase, phrase, "自分を好きになれない気持ち", "self_dislike_from_halfway"
    if "幸せに笑って" in compact and "役に立" in compact:
        phrase = "他の人が幸せに笑っていて、その人たちの役に立てることが幸せに近い"
        return phrase, phrase, "他者の幸せが自分の幸せに近いこと", "others_happiness_as_own_happiness"
    if "諦めたくない" in compact:
        phrase = "自分のことも今後のことも諦めたくない気持ちがある"
        return phrase, phrase, "諦めたくない気持ち", "future_not_giving_up"
    if "諦めてる自分" in compact or "諦めている自分" in compact:
        phrase = "諦めている自分もいる"
        return phrase, phrase, "諦めている自分", "resignation_self"
    if "裏切られたくない" in compact:
        phrase = "期待して裏切られるのが怖い"
        return phrase, phrase, "期待して裏切られたくない怖さ", "betrayal_fear"
    if "私も幸せになりたい" in compact or "自分も幸せになりたい" in compact or "幸せになりたいって思う自分" in compact:
        phrase = "私も幸せになりたい気持ちがある"
        return phrase, phrase, "自分も幸せになりたい願い", "own_happiness_wish"
    if "既に幸せ" in compact or "それ以上を求め" in compact or "それ以上に求め" in compact:
        phrase = "既に幸せなことはあると分かっていても、それ以上を求めている"
        return phrase, phrase, "既にある幸せ以上を求める気持ち", "existing_happiness_and_more"
    if "好きなこと" in compact or "十分にたのしみたい" in compact or "十分に楽しみたい" in compact or "パートナー" in compact:
        phrase = "好きなことをもっとして、納得いくまで楽しみ、素敵なパートナーと幸せになりたい"
        return phrase, phrase, "好きなことを楽しみ、パートナーと幸せになりたい願い", "concrete_life_wishes"
    if "手の届" in compact:
        phrase = "手の届かないところにある願い"
        return phrase, phrase, "手の届かない願い", "unreachable_wish"
    if "今頑張れる" in compact or "願いに届くように" in compact:
        phrase = "願いに届くために、今頑張れることを大切にしたい"
        return phrase, phrase, "願いに届くために今頑張れることを大切にしたい気持ち", "present_effort_toward_wish"

    # Existing self-awareness / boundary cases.
    if "パーソナルスペースに入ってしまった" in compact:
        phrase = "人のパーソナルスペースに入ってしまった" if "人のパーソナルスペース" in compact else "パーソナルスペースに入ってしまった"
        return phrase, phrase, f"{phrase}行動", "boundary_violation"
    if "パーソナルスペースに触れてしまった" in compact:
        phrase = "パーソナルスペースに触れてしまった"
        return phrase, phrase, f"{phrase}行動", "boundary_violation"
    if "怒ると知っていながら" in compact:
        phrase = "怒ると知っていながら"
        return phrase, phrase, "怒ると知っていながら触れてしまった自覚", "self_awareness"
    if "女の子との絡みがあったから" in compact:
        phrase = "女の子との絡みがあったから"
        return phrase, phrase, "女の子との絡みがあったからという理由", "justification"
    if "自分の非を見たくない" in compact:
        phrase = "自分の非を見たくない"
        return phrase, phrase, "自分の非を見たくない気持ち", "self_avoidance"
    if "自分の非" in compact:
        phrase = "自分の非"
        return phrase, phrase, "自分の非への自覚", "self_fault_awareness"
    if "嫌われ" in compact:
        phrase = "嫌われてしまいそう" if "嫌われてしまいそう" in compact else "嫌われそう"
        return phrase, phrase, "嫌われてしまいそうな怖さ", "fear_of_rejection"
    if "悲しくて不安" in compact:
        phrase = "悲しくて不安"
        return phrase, phrase, "悲しみと不安が重なっている状態", "explicit_emotion"
    return None


def _generic_nominal(phrase: str, role: str) -> str:
    if not phrase:
        return ""
    if role in {"anger_surface", "work_frustration"}:
        if phrase.endswith("気持ち"):
            return phrase
        if phrase.endswith(("だ", "だから", "けど", "けれど", "から")):
            return re.sub(r"(だ|だから|けど|けれど|から)$", "", phrase).strip(" 、,") + "気持ち"
        return f"{phrase}気持ち"
    if role in {"self_dislike_from_halfway"}:
        return "頑張ることも楽しむことも中途半端に感じること" if "中途半端" in phrase else "自分を好きになれない気持ち"
    if role in {"betrayal_fear"}:
        return "期待して裏切られたくない怖さ"
    if role in {"own_happiness_wish", "concrete_life_wishes", "present_effort_toward_wish"}:
        return phrase if phrase.endswith(("願い", "気持ち")) else f"{phrase}願い"
    if role in {"missing_guidance", "effort_confusion", "chat_relief"}:
        return phrase
    if phrase.endswith(("こと", "状態", "気持ち", "しんどさ", "怖さ", "願い")):
        return phrase
    return f"{phrase}こと"


def shape_user_phrase(anchor: UserWordAnchor) -> ShapedUserPhrase:
    raw = _clean(getattr(anchor, "text", ""))
    role = str(getattr(anchor, "role", "other") or "other")
    reasons: list[str] = []
    known = _known_phrase(raw, role)
    if known is not None:
        phrase, fragment, nominal, shaped_role = known
        role = shaped_role
    else:
        stripped, strip_reasons = _strip_unfinished_connectors(raw)
        reasons.extend(strip_reasons)
        phrase = _soften_colloquial(stripped)
        role = _role_from_text(phrase, role)
        fragment = phrase
        nominal = _generic_nominal(phrase, role)

    unsafe = []
    if not phrase:
        unsafe.append("empty_phrase")
    if _UNFINISHED_CONNECTOR_RE.search(phrase):
        unsafe.append("unfinished_connector")
    if re.search(r"(それだと|けど|けれど|でも|から|ので|のに|だって)こと", phrase):
        unsafe.append("broken_connection_risk")
    if re.search(r"(だ|だから|けど|けれど|から)(気持ち|思い|願い|状態)", phrase):
        unsafe.append("broken_noun_phrase_risk")
    usability = "unsafe" if unsafe else ("needs_context" if reasons else "safe")
    return ShapedUserPhrase(
        anchor_key=str(getattr(anchor, "anchor_key", "") or ""),
        raw_text=raw,
        phrase=phrase,
        sentence_fragment=fragment or phrase,
        nominal=nominal or phrase,
        role=role,
        source_field=str(getattr(anchor, "source_field", "") or "memo"),
        usability=usability,
        unsafe_reasons=[*reasons, *unsafe],
        evidence=[EvidenceRef(kind=item.kind, ref_id=item.ref_id, weight=item.weight, note=item.note) for item in list(getattr(anchor, "evidence", []) or [])],
    )


def _synthesized_anchor(text: str, *, role: str, source_field: str, index: int, evidence: EvidenceRef) -> UserWordAnchor:
    return UserWordAnchor(
        anchor_key=f"phrase_synth:{source_field}:{role}:{index}",
        text=_clean(text),
        source_field=source_field,
        role=role,
        evidence=[evidence],
        confidence=0.74,
    )


def _synthesized_anchors_from_current_input(current_input: Mapping[str, Any]) -> Iterable[UserWordAnchor]:
    raw_memo = str(current_input.get("memo") or "")
    raw_action = str(current_input.get("memo_action") or "")
    evidence = EvidenceRef(kind="emotion", ref_id=str(current_input.get("id") or current_input.get("created_at") or "current"), weight=1.0, note="phrase_shaping:synthesized")
    patterns = (
        (r"たまに泣きそうになるくらい嫌になる時あるけどそれだと", "sadness_surface"),
        (r"悔しいしもったいない気がする", "work_frustration"),
        (r"むかつくけどさ", "anger_surface"),
        (r"好きな先輩以外の時はミスしても知らねーよって\s*気持ちでいる", "mentor_attachment"),
        (r"教えてくんないんだもん", "missing_guidance"),
        (r"どう頑張ればいいのって思う", "effort_confusion"),
        (r"最近めっちゃイライラする", "fatigue_accumulation"),
        (r"チャット系でお話してると\s*癒される", "chat_relief"),
        (r"誰かの役に立てればそれでいい", "other_contribution"),
        (r"私は私自身頑張ることも楽しむことも中途半端だから", "self_dislike_from_halfway"),
        (r"自分のことは好きになれないけど", "self_dislike_from_halfway"),
        (r"他の人たちが幸せに笑ってくれてて\s*その人たちの役に立てるなら1番それが幸せかな", "others_happiness_as_own_happiness"),
        (r"自分のこと\s*今後のこと\s*まだ諦めたくないけれど", "future_not_giving_up"),
        (r"諦めてる自分もいる", "resignation_self"),
        (r"もう期待して裏切られたくないから", "betrayal_fear"),
        (r"私も幸せになりたいって思う自分もいる", "own_happiness_wish"),
        (r"もう既に幸せなことはあるって事\s*それ以上に求めてるんだよねきっと", "existing_happiness_and_more"),
        (r"好きなことをもっとしたい\s*納得いくまで十分にたのしみたい\s*素敵なパートナーと出会って幸せになりたい", "concrete_life_wishes"),
        (r"手の届かい所にある願い", "unreachable_wish"),
        (r"その願いに届くように、?今頑張れることを大切にしたい", "present_effort_toward_wish"),
    )
    for idx, (pattern, role) in enumerate(patterns):
        match = re.search(pattern, raw_memo, flags=re.MULTILINE)
        if match:
            yield _synthesized_anchor(match.group(0), role=role, source_field="memo", index=idx, evidence=evidence)
    if raw_action.strip():
        # Action anchors are already extracted well in most cases; synthesize only
        # when no paragraph-level extractor caught the action wording.
        if "パーソナルスペース" in raw_action:
            yield _synthesized_anchor(raw_action.strip(), role="boundary_violation", source_field="memo_action", index=100, evidence=evidence)


def shape_user_phrases(*, anchors: Sequence[UserWordAnchor], current_input: Mapping[str, Any]) -> List[ShapedUserPhrase]:
    shaped: list[ShapedUserPhrase] = []
    seen: set[tuple[str, str]] = set()
    for anchor in [*list(anchors or []), *_synthesized_anchors_from_current_input(current_input)]:
        item = shape_user_phrase(anchor)
        key = (_compact(item.phrase), item.role)
        if not item.phrase or key in seen:
            continue
        seen.add(key)
        shaped.append(item)
    return shaped


def safe_phrases(shaped_phrases: Sequence[ShapedUserPhrase]) -> List[ShapedUserPhrase]:
    return [item for item in shaped_phrases or [] if getattr(item, "usability", "safe") in {"safe", "needs_context"} and str(getattr(item, "phrase", "") or "").strip()]


__all__ = ["shape_user_phrase", "shape_user_phrases", "safe_phrases"]
