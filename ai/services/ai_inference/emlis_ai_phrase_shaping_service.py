# -*- coding: utf-8 -*-
from __future__ import annotations

"""Generic phrase shaping for EmlisAI natural replies.

This module does not memorise sample inputs.  It shapes raw user clauses into
safe sentence fragments using reusable grammar / role rules.
"""

import re
from typing import Any, Iterable, List, Mapping, Sequence

from emlis_ai_types import EvidenceRef, ShapedUserPhrase, UserWordAnchor

_SPACE_RE = re.compile(r"\s+")
_UNFINISHED_CONNECTOR_RE = re.compile(r"(けどそれだと|けどさ|けど|けれど|でも|から|ので|のに|だって|だから|それだと)$")
_SPLIT_RE = re.compile(r"[。！？!?\n\r]+")
_SOFT_SPLIT_RE = re.compile(r"(?<=[、,])|(?<=けど)|(?<=けれど)|(?<=でも)|(?<=のに)|(?<=から)|(?<=ので)")


_ROLE_KEYWORDS: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("self_sacrifice_no_worry", ("我慢", "心配", "負担", "迷惑")),
    ("self_sacrifice_rounds_off", ("我慢", "収ま", "丸く", "波風")),
    ("alone_burden", ("一人", "ひとり", "抱え", "背負")),
    ("talk_or_rely_when_hard", ("話", "頼", "相談", "助け")),
    ("protective_distance", ("距離", "離れ", "守る", "境界")),
    ("no_overdoing_choice", ("無理しない", "休む", "選択")),
    ("other_contribution", ("役に立", "助け", "支え", "誰かのため", "人のため")),
    ("self_dislike_from_halfway", ("好きになれない", "中途半端", "自己嫌悪", "自分が嫌")),
    ("future_not_giving_up", ("諦めたくない", "諦めない", "終わりにしたくない")),
    ("resignation_self", ("諦めて", "諦めよう", "期待しない")),
    ("betrayal_fear", ("裏切", "期待", "傷つきたく", "怖")),
    ("own_happiness_wish", ("幸せになりたい", "自分も幸せ", "私も幸せ", "自分自身の幸せ")),
    ("concrete_life_wishes", ("好きなこと", "楽しみたい", "たのしみたい", "大切な人", "恋人", "出会", "暮らし")),
    ("unreachable_wish", ("届かない", "遠い", "願い", "夢", "届きにく")),
    ("present_effort_toward_wish", ("今", "できること", "頑張れること", "大切", "届く")),
    ("state_awareness", ("疲れ", "しんど", "限界", "ボロボロ", "分か", "気づ")),
    ("effort_history", ("頑張ってき", "がんばってき", "無理してき", "積み重")),
    ("continuation_wish", ("頑張りたい", "がんばりたい", "続けたい", "まだ")),
    ("fatigue_or_limit", ("しんど", "疲れ", "重い", "ついてこない", "余裕がない")),
    ("collapse_anxiety", ("崩れ", "壊れ", "無理したら", "不安")),
    ("dual_holding", ("どっちも", "どちらも", "両方", "抱えたまま")),
    ("paced_progress", ("立ち止", "整え", "少しずつ", "休む", "ペース")),
    ("self_understanding", ("弱いわけ", "限界に気づ", "状態なんだ")),
    ("missing_guidance", ("教えて", "頑張り方", "どう頑張", "分から")),
    ("anger_surface", ("むかつ", "イライラ", "怒", "腹立")),
    ("relief_source", ("癒", "落ち着", "安心", "チャット", "話して")),
    ("boundary_violation", ("境界", "距離感", "踏み込", "入ってしま", "触れてしま", "越えて")),
    ("self_awareness", ("知っていながら", "分かっていながら", "わかっていながら")),
    ("self_fault_awareness", ("自分の非", "自分が悪", "自分のせい", "責任")),
    ("self_avoidance", ("見たくない", "向き合いたくない", "認めたくない", "目をそら")),
    ("fear_of_rejection", ("嫌われ", "見捨て", "否定され", "離れていきそう")),
)


_ROLE_NOMINAL_SUFFIX = {
    "anger_surface": "気持ち",
    "missing_guidance": "しんどさ",
    "effort_confusion": "気持ち",
    "relief_source": "こと",
    "chat_relief": "こと",
    "betrayal_fear": "怖さ",
    "fear_of_rejection": "怖さ",
    "own_happiness_wish": "願い",
    "concrete_life_wishes": "願い",
    "present_effort_toward_wish": "気持ち",
    "unreachable_wish": "願い",
}


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
        ("めっちゃ", "かなり"),
        ("お話してる", "話している"),
        ("話してる", "話している"),
        ("癒される", "癒しになっている"),
        ("1番", "一番"),
    )
    for src, dst in replacements:
        out = out.replace(src, dst)
    out = out.replace("時ある", "時がある")
    out = re.sub(r"どう([^。！？!?]{0,16})?頑張ればいい[^。！？!?]*", "どう頑張ればいいのか分からない気持ち", out)
    out = re.sub(r"([^。！？!?]{0,26}中途半端)(?:だから|なので|で)", r"\1に感じて", out)
    out = re.sub(r"好きになれない(?:けど|けれど)", "好きになれない気持ちがありながら", out)
    out = re.sub(r"諦めたくない(?:けど|けれど)", "諦めたくない気持ちがありながら", out)
    out = re.sub(r"期待[^。！？!?]{0,16}裏切られたくない(?:から|ので)?", "期待して裏切られるのが怖くて", out)
    out = re.sub(r"それ以上(?:に|を)?求めて(?:る|いる)[^。！？!?]*", "それ以上を求めている", out)
    return _clean(out)


def _role_from_text(text: str, fallback: str) -> str:
    compact = _compact(text)
    for role, keywords in _ROLE_KEYWORDS:
        if any(keyword in compact for keyword in keywords):
            return role
    return fallback or "other"


def _generic_nominal(phrase: str, role: str) -> str:
    clean = _clean(phrase)
    if not clean:
        return ""
    if clean.endswith(("こと", "状態", "気持ち", "しんどさ", "怖さ", "願い", "自覚")):
        return clean
    # Avoid broken noun phrases after predicate/connective endings.
    clean = re.sub(r"(だ|だから|けど|けれど|から|なので)$", "", clean).strip(" 、,")
    suffix = _ROLE_NOMINAL_SUFFIX.get(role)
    if suffix:
        return f"{clean}{suffix}"
    if role in {"state_awareness", "fatigue_or_limit", "collapse_anxiety", "dual_holding", "paced_progress", "self_understanding"}:
        return f"{clean}状態"
    return f"{clean}こと"


def shape_user_phrase(anchor: UserWordAnchor) -> ShapedUserPhrase:
    raw = _clean(getattr(anchor, "text", ""))
    role = str(getattr(anchor, "role", "other") or "other")
    reasons: list[str] = []
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


def _split_clauses(text: str) -> Iterable[str]:
    for sentence in _SPLIT_RE.split(str(text or "")):
        sentence = _clean(sentence)
        if not sentence:
            continue
        pieces = _SOFT_SPLIT_RE.split(sentence) if len(sentence) > 36 else [sentence]
        for piece in pieces:
            piece = _clean(piece)
            if len(piece) >= 3:
                yield piece[:90].rstrip("、,")


def _synthesized_anchors_from_current_input(current_input: Mapping[str, Any]) -> Iterable[UserWordAnchor]:
    evidence = EvidenceRef(kind="emotion", ref_id=str(current_input.get("id") or current_input.get("created_at") or "current"), weight=1.0, note="phrase_shaping:synthesized")
    idx = 0
    for source_field in ("memo", "memo_action"):
        raw = str(current_input.get(source_field) or "")
        if not raw.strip():
            continue
        for clause in _split_clauses(raw):
            role = _role_from_text(clause, "action" if source_field == "memo_action" else "other")
            if role == "other" and source_field != "memo_action":
                continue
            yield _synthesized_anchor(clause, role=role, source_field=source_field, index=idx, evidence=evidence)
            idx += 1


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
