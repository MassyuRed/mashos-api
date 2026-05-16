# -*- coding: utf-8 -*-
from __future__ import annotations

"""Generic phrase shaping for EmlisAI replies.

This module must not contain example-answer rules.  It only normalizes raw
current-input fragments into safe Japanese sentence fragments by applying
language-level cleanup: whitespace cleanup, unfinished connector removal,
light colloquial softening, typo normalization, and role-neutral nominalization.
"""

import re
from typing import Any, Iterable, List, Mapping, Sequence

from emlis_ai_limited_sentence_quality_guard import judge_phrase_unit_material_quality
from emlis_ai_types import EvidenceRef, ShapedUserPhrase, UserWordAnchor

_SPACE_RE = re.compile(r"\s+")
_SENTENCE_SPLIT_RE = re.compile(r"[。！？!?\n\r]+")
_SOFT_SPLIT_RE = re.compile(r"(?<=、)|(?<=,)|(?<=けど)|(?<=けれど)|(?<=でも)|(?<=のに)|(?<=から)|(?<=ので)")
_UNFINISHED_CONNECTOR_RE = re.compile(r"(?:けどさ|だけどさ|でもさ|それだと|けれど|だけど|けど|でも|から|ので|のに|だって|ただ|それで)$")

_ROLE_KEYWORDS: tuple[tuple[str, tuple[str, ...]], ...] = (
    ("support_need", ("頼", "相談", "話", "助け", "支え")),
    ("self_protection", ("守", "距離", "境界", "無理しない", "離れ")),
    ("self_suppression", ("我慢", "抑え", "飲み込", "耐え")),
    ("burden_avoidance", ("心配", "負担", "迷惑", "丸く", "収ま")),
    ("wish", ("したい", "なりたい", "ほしい", "欲しい", "願", "叶")),
    ("fear_or_disappointment", ("怖", "恐", "不安", "裏切", "嫌われ", "傷つ")),
    ("self_view", ("自分", "好きになれ", "弱", "限界", "中途", "責任", "非")),
    ("effort_direction", ("頑張", "進", "続け", "整え", "大切")),
    ("anger_or_frustration", ("怒", "むかつ", "イライラ", "悔", "腹立")),
    ("relief_source", ("癒", "安心", "落ち着", "楽になる")),
    ("relationship_context", ("相手", "恋人", "友達", "家族", "職場", "上司", "同僚", "他者", "周り")),
    ("sadness_or_pain", ("悲", "つら", "辛", "泣", "しんど", "苦し")),
)

_COLLOQUIAL_REPLACEMENTS: tuple[tuple[str, str], ...] = (
        ("くんない", "もらえない"),
    ("めっちゃ", "かなり"),
    ("だもん", "から"),
    ("って思う", "と思っている"),
    ("って気持ち", "という気持ち"),
    ("できん", "できない"),
    ("届かい", "届かない"),
    ("1番", "一番"),
)


def _clean(value: Any) -> str:
    text = str(value or "").replace("\u3000", " ")
    text = _SPACE_RE.sub(" ", text)
    return text.strip(" 、,。.!！?？\t\n\r")


def _compact(value: Any) -> str:
    return re.sub(r"[\s　、,。.!！?？\t\n\r「」『』（）()]", "", str(value or ""))


def _strip_unfinished_connectors(text: str) -> tuple[str, list[str]]:
    clean = _clean(text)
    reasons: list[str] = []
    if clean.endswith("中途半端だから"):
        return clean[: -len("だから")] + "に感じている", reasons
    while True:
        match = _UNFINISHED_CONNECTOR_RE.search(clean)
        if not match:
            break
        clean = clean[: match.start()].rstrip(" 、,")
        reasons.append("unfinished_connector")
    return clean, reasons


def _soften_colloquial(text: str) -> str:
    out = _clean(text)
    for before, after in _COLLOQUIAL_REPLACEMENTS:
        out = out.replace(before, after)
    out = re.sub(r"時ある", "時がある", out)
    out = re.sub(r"ことある", "ことがある", out)
    out = re.sub(r"(.{1,60})だから$", r"\1で", out)
    out = re.sub(r"(.{1,60})けど$", r"\1気持ちがありながら", out)
    return _clean(out)


def _role_from_text(text: str, fallback: str) -> str:
    normalized_fallback = str(fallback or "").strip()
    # Explicit anchors may carry a caller-owned semantic label. Keep it unless
    # it is one of the generic placeholders used for synthesized chunks.
    if normalized_fallback and normalized_fallback not in {"other", "current_expression", "action"}:
        return normalized_fallback
    compact = _compact(text)
    for role, keywords in _ROLE_KEYWORDS:
        if any(keyword in compact for keyword in keywords):
            return role
    if normalized_fallback and normalized_fallback != "other":
        return normalized_fallback
    return "current_expression"


def _sentence_fragment(phrase: str, role: str) -> str:
    phrase = _clean(phrase)
    if not phrase:
        return ""
    if role in {"wish", "effort_direction"} and not phrase.endswith(("気持ち", "願い", "こと")):
        return f"{phrase}気持ち"
    if role in {"fear_or_disappointment", "anger_or_frustration", "sadness_or_pain"} and not phrase.endswith(("気持ち", "感覚", "不安", "怖さ")):
        return f"{phrase}感覚"
    return phrase


def _nominal_for_role(phrase: str, role: str) -> str:
    fragment = _sentence_fragment(phrase, role)
    if not fragment:
        return ""
    if fragment.endswith(("気持ち", "感覚", "願い", "不安", "怖さ", "状態", "こと")):
        return fragment
    if role in {"self_suppression", "self_protection", "support_need", "effort_direction"}:
        return f"{fragment}こと"
    return f"{fragment}気持ち"


def shape_user_phrase(anchor: UserWordAnchor) -> ShapedUserPhrase:
    raw = _clean(getattr(anchor, "text", ""))
    stripped, reasons = _strip_unfinished_connectors(raw)
    softened = _soften_colloquial(stripped or raw)
    role = _role_from_text(softened, str(getattr(anchor, "role", "other") or "other"))
    material_report = judge_phrase_unit_material_quality(
        softened,
        raw_text=raw,
        role=role,
        source_field=str(getattr(anchor, "source_field", "memo") or "memo"),
    )
    material_reasons = list(material_report.get("rejection_reasons") or [])
    usability = "safe" if softened and len(softened) >= 2 and bool(material_report.get("passed")) else "unsafe"
    if reasons and len(softened) < 4:
        usability = "unsafe"
    unsafe_reasons = list(dict.fromkeys([*reasons, *material_reasons]))
    return ShapedUserPhrase(
        anchor_key=str(getattr(anchor, "anchor_key", "") or ""),
        raw_text=raw,
        phrase=softened,
        sentence_fragment=_sentence_fragment(softened, role),
        nominal=_nominal_for_role(softened, role),
        role=role,
        source_field=str(getattr(anchor, "source_field", "memo") or "memo"),
        usability=usability,
        unsafe_reasons=unsafe_reasons if usability != "safe" else [],
        evidence=list(getattr(anchor, "evidence", []) or []),
    )

def _synthesized_anchor(text: str, *, role: str, source_field: str, index: int, evidence: EvidenceRef) -> UserWordAnchor:
    return UserWordAnchor(
        anchor_key=f"current_phrase:{source_field}:{index}",
        text=_clean(text),
        source_field=source_field,
        role=role,
        evidence=[evidence],
        confidence=0.72,
    )


def _split_source_text(text: str) -> List[str]:
    chunks: List[str] = []
    for sentence in _SENTENCE_SPLIT_RE.split(str(text or "")):
        sentence = _clean(sentence)
        if not sentence:
            continue
        parts = _SOFT_SPLIT_RE.split(sentence) if len(sentence) > 48 else [sentence]
        for part in parts:
            part = _clean(part)
            if not part:
                continue
            if len(part) > 72:
                part = part[:72].rstrip("、,")
            if len(part) >= 3:
                chunks.append(part)
    return chunks


def _synthesized_anchors_from_current_input(current_input: Mapping[str, Any]) -> Iterable[UserWordAnchor]:
    evidence = EvidenceRef(kind="emotion", ref_id=str(current_input.get("id") or current_input.get("created_at") or "current"), weight=1.0)
    index = 0
    for field in ("memo", "memo_action"):
        for chunk in _split_source_text(str(current_input.get(field) or "")):
            role = _role_from_text(chunk, "action" if field == "memo_action" else "current_expression")
            yield _synthesized_anchor(chunk, role=role, source_field=field, index=index, evidence=evidence)
            index += 1


def shape_user_phrases(*, anchors: Sequence[UserWordAnchor], current_input: Mapping[str, Any]) -> List[ShapedUserPhrase]:
    shaped: List[ShapedUserPhrase] = []
    source = list(anchors or []) or list(_synthesized_anchors_from_current_input(current_input))
    seen: set[tuple[str, str]] = set()
    for anchor in source:
        item = shape_user_phrase(anchor)
        key = (_compact(item.phrase), item.role)
        if not item.phrase or key in seen:
            continue
        seen.add(key)
        shaped.append(item)
    return shaped


def safe_phrases(shaped_phrases: Sequence[ShapedUserPhrase]) -> List[ShapedUserPhrase]:
    return [item for item in shaped_phrases or [] if getattr(item, "usability", "safe") == "safe" and _clean(getattr(item, "phrase", ""))]


__all__ = ["shape_user_phrase", "shape_user_phrases", "safe_phrases"]
