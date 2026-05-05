# -*- coding: utf-8 -*-
from __future__ import annotations

"""Generic current-input anchor extraction for EmlisAI.

The extractor intentionally avoids sample-specific exact phrases.  It keeps
source-bound clauses and assigns broad semantic roles so later stages can build
an answer from the current input rather than from memorized examples.
"""

import re
from typing import Any, Dict, List, Tuple

from emlis_ai_types import EvidenceRef, UserWordAnchor

_SPLIT_RE = re.compile(r"[。！？!?\n\r]+")
_SOFT_SPLIT_RE = re.compile(r"(?<=、)|(?<=,)|(?<=けど)|(?<=けれど)|(?<=でも)|(?<=のに)|(?<=から)|(?<=ので)")
_SPACE_RE = re.compile(r"\s+")
_GENERIC_NOISE_RE = re.compile(r"^(です|ます|でした|だった|ので|から|けど|でも|そして|それで|あと|ただ)$")

_ROLE_KEYWORDS: tuple[tuple[str, tuple[str, ...], float], ...] = (
    ("self_awareness", ("気づ", "分かって", "わかって", "知って", "自覚"), 4.9),
    ("self_view", ("自分", "好きになれ", "弱", "限界", "中途", "責任", "非"), 4.7),
    ("fear_or_disappointment", ("怖", "恐", "不安", "裏切", "嫌われ", "見捨", "否定", "傷つ"), 4.8),
    ("self_suppression", ("我慢", "抑え", "飲み込", "耐え", "抱え込"), 4.7),
    ("burden_avoidance", ("心配", "負担", "迷惑", "丸く", "収ま"), 4.3),
    ("support_need", ("頼", "相談", "話", "助け", "支え"), 4.4),
    ("self_protection", ("守", "距離", "境界", "離れ", "無理しない"), 4.4),
    ("wish", ("したい", "なりたい", "ほしい", "欲しい", "願", "叶"), 4.5),
    ("effort_direction", ("頑張", "進", "続け", "整え", "大切", "諦め"), 4.2),
    ("sadness_or_pain", ("悲", "つら", "辛", "泣", "しんど", "苦し"), 4.1),
    ("anger_or_frustration", ("怒", "むかつ", "イライラ", "悔", "腹立"), 4.0),
    ("relief_source", ("癒", "安心", "落ち着", "楽になる"), 3.8),
    ("relationship_context", ("相手", "恋人", "友達", "家族", "職場", "上司", "同僚", "他者", "周り"), 3.5),
    ("mismatch_or_boundary", ("すれ違", "合わな", "違い", "境界", "距離感", "踏み込"), 3.7),
)


def _clean_text(value: Any) -> str:
    text = _SPACE_RE.sub(" ", str(value or "").replace("\u3000", " ")).strip()
    return text.strip(" 、,。.!！?？\t")


def _compact(value: Any) -> str:
    return re.sub(r"[\s　、,。.!！?？\t\n\r「」『』（）()]", "", str(value or ""))


def _split_clauses(text: str) -> List[str]:
    chunks: List[str] = []
    for sentence in _SPLIT_RE.split(str(text or "")):
        sentence = _clean_text(sentence)
        if not sentence:
            continue
        pieces = _SOFT_SPLIT_RE.split(sentence) if len(sentence) > 42 else [sentence]
        for piece in pieces:
            piece = _clean_text(piece)
            if not piece or _GENERIC_NOISE_RE.match(piece):
                continue
            if len(piece) > 76:
                piece = piece[:76].rstrip("、,")
            if len(piece) >= 3:
                chunks.append(piece)
    return chunks


def _role_for(text: str, *, source_field: str = "memo") -> str:
    if source_field == "memo_action":
        return "action"
    compact = _compact(text)
    for role, keywords, _weight in _ROLE_KEYWORDS:
        if any(keyword in compact for keyword in keywords):
            return role
    return "current_expression"


def _score_clause(text: str, *, order: int, source_field: str = "memo") -> float:
    compact = _compact(text)
    role = _role_for(text, source_field=source_field)
    score = 1.0
    for candidate_role, keywords, weight in _ROLE_KEYWORDS:
        if role == candidate_role:
            score += weight
        if any(keyword in compact for keyword in keywords):
            score += min(2.0, weight / 3.0)
    if 6 <= len(text) <= 54:
        score += 1.0
    elif len(text) <= 86:
        score += 0.4
    score += max(0.0, 0.45 - order * 0.02)
    return score


def extract_user_word_anchors(
    *,
    current_input: Dict[str, Any],
    max_anchors: int,
    evidence: EvidenceRef,
) -> List[UserWordAnchor]:
    """Return high-value current-input clauses in source order after scoring."""

    scored: List[Tuple[float, int, str, str, str]] = []
    order = 0
    for field in ("memo", "memo_action"):
        raw = str(current_input.get(field) or "")
        if not raw.strip():
            continue
        for clause in _split_clauses(raw):
            role = _role_for(clause, source_field=field)
            scored.append((_score_clause(clause, order=order, source_field=field), order, clause, field, role))
            order += 1
    if not scored:
        return []

    limit = max(0, int(max_anchors or 0))
    if limit <= 0:
        return []

    # Reserve role diversity first, then fill by score. This is generic; it does
    # not reserve any example sentence or fixed answer path.
    scored.sort(key=lambda item: (-item[0], item[1]))
    selected: List[Tuple[float, int, str, str, str]] = []
    seen_compact: set[str] = set()

    def _append(item: Tuple[float, int, str, str, str]) -> bool:
        clean = _clean_text(item[2])
        key = _compact(clean)
        if not clean or key in seen_compact:
            return False
        seen_compact.add(key)
        selected.append((item[0], item[1], clean, item[3], item[4]))
        return True

    for role, _keywords, _weight in _ROLE_KEYWORDS:
        if len(selected) >= limit:
            break
        role_items = [item for item in scored if item[4] == role]
        if role_items:
            role_items.sort(key=lambda item: (len(_clean_text(item[2])) > 58, -item[0], item[1]))
            _append(role_items[0])

    role_counts: Dict[str, int] = {}
    for item in selected:
        role_counts[item[4]] = role_counts.get(item[4], 0) + 1
    for item in scored:
        if len(selected) >= limit:
            break
        if role_counts.get(item[4], 0) >= 2:
            continue
        if _append(item):
            role_counts[item[4]] = role_counts.get(item[4], 0) + 1

    selected.sort(key=lambda item: item[1])
    anchors: List[UserWordAnchor] = []
    for idx, (score, _order, text, field, role) in enumerate(selected):
        anchors.append(
            UserWordAnchor(
                anchor_key=f"current_word:{field}:{idx}",
                text=text,
                source_field=field,
                role=role,
                evidence=[EvidenceRef(kind=evidence.kind, ref_id=evidence.ref_id, weight=evidence.weight, note=f"user_word_anchor:{field}")],
                confidence=max(0.45, min(1.0, score / 8.0)),
            )
        )
    return anchors


__all__ = ["extract_user_word_anchors"]
