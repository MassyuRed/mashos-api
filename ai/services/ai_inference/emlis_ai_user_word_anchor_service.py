# -*- coding: utf-8 -*-
from __future__ import annotations

"""Current-input word anchor extraction for EmlisAI.

The extractor is intentionally deterministic and source-bound.  It does not try
resource-heavy semantic inference; it only keeps the important words and clauses
that the user actually wrote, so the immediate reply can feel read and received
without inventing context.
"""

import re
from typing import Any, Dict, Iterable, List, Tuple

from emlis_ai_types import EvidenceRef, UserWordAnchor

_EMOTION_WORDS = (
    "悲しい",
    "悲しかった",
    "つらい",
    "辛い",
    "苦しい",
    "不安",
    "怖い",
    "恐い",
    "焦り",
    "焦った",
    "怒り",
    "怒った",
    "腹が立つ",
    "嬉しい",
    "うれしい",
    "喜び",
    "安心",
    "平穏",
    "寂しい",
    "さみしい",
)
_ANXIETY_CONDITION_WORDS = (
    "不安になる",
    "不安にな",
    "怖くなる",
    "恐くなる",
)
_UNCERTAINTY_WORDS = (
    "かなぁ",
    "かなあ",
    "かな",
    "できるの",
    "どうなる",
    "わからない",
    "分からない",
    "不確か",
)
_WISH_WORDS = (
    "したい",
    "なりたい",
    "ほしい",
    "欲しい",
    "叶えたい",
    "せめて",
)
_ACTION_WORDS = (
    "話した",
    "会った",
    "行った",
    "書いた",
    "片づけた",
    "作った",
    "休んだ",
    "寝た",
    "歩いた",
    "連絡した",
)
_RELATION_WORDS = (
    "恋人",
    "彼氏",
    "彼女",
    "パートナー",
    "相手",
    "友達",
    "家族",
    "親",
    "職場",
    "上司",
    "同僚",
    "自分",
)
_MISMATCH_WORDS = (
    "すれ違",
    "合わない",
    "不一致",
    "違い",
    "噛み合わ",
    "わかり合え",
    "分かり合え",
    "伝わら",
    "届かな",
    "ズレ",
    "距離感",
    "頻度",
)
_NEED_WORDS = (
    "したい",
    "してほしい",
    "ほしかった",
    "大事",
    "大切",
    "向き合",
    "わかって",
    "分かって",
    "安心したい",
)
_UNRESOLVED_WORDS = (
    "わからない",
    "分からない",
    "決められない",
    "迷って",
    "残って",
    "引っかか",
    "モヤモヤ",
    "もやもや",
)

_SPLIT_RE = re.compile(r"[。！？!?\n\r]+")
_SOFT_SPLIT_RE = re.compile(r"(?<=[、,])|(?<=けど)|(?<=けれど)|(?<=でも)|(?<=のに)|(?<=から)|(?<=ので)")
_SPACE_RE = re.compile(r"\s+")
_GENERIC_NOISE_RE = re.compile(r"^(です|ます|でした|だった|ので|から|けど|でも|そして|それで|あと)$")


def _clean_text(value: Any) -> str:
    text = _SPACE_RE.sub(" ", str(value or "").replace("\u3000", " ")).strip()
    return text.strip(" 、,。.!！?？\t")


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
            if len(piece) > 70:
                # Keep surface wording but avoid turning a whole paragraph into one anchor.
                piece = piece[:70].rstrip("、,")
            if len(piece) >= 3:
                chunks.append(piece)
    return chunks


def _has_anxiety_condition(text: str) -> bool:
    if not any(word in text for word in _ANXIETY_CONDITION_WORDS):
        return False
    return any(marker in text for marker in ("考えると", "思うと", "見ると", "聞くと", "なる", "将来"))


def _role_for(text: str, *, source_field: str = "memo") -> str:
    if source_field == "memo_action":
        return "action"
    if _has_anxiety_condition(text):
        return "anxiety_condition"
    if any(word in text for word in _UNCERTAINTY_WORDS):
        return "uncertainty"
    if any(word in text for word in _WISH_WORDS):
        return "wish"
    if any(word in text for word in _EMOTION_WORDS):
        return "explicit_emotion"
    if "喧嘩" in text or "けんか" in text:
        return "event"
    if any(word in text for word in _MISMATCH_WORDS):
        return "mismatch"
    if any(word in text for word in _NEED_WORDS):
        return "need"
    if any(word in text for word in _UNRESOLVED_WORDS):
        return "unresolved"
    if any(word in text for word in _RELATION_WORDS):
        return "relationship"
    return "event"


def _score_clause(text: str, *, order: int, source_field: str = "memo") -> float:
    score = 0.0
    role = _role_for(text, source_field=source_field)
    if role == "anxiety_condition":
        score += 4.6
    if role == "uncertainty":
        score += 3.7
    if role == "wish":
        score += 3.4
    if role == "action":
        score += 2.8
    if any(word in text for word in _EMOTION_WORDS):
        score += 3.2 if role == "anxiety_condition" else 4.0
    if any(word in text for word in _MISMATCH_WORDS):
        score += 3.2
    if any(word in text for word in _RELATION_WORDS):
        score += 2.2
    if "喧嘩" in text or "けんか" in text:
        score += 3.0
    if any(word in text for word in _NEED_WORDS):
        score += 1.8
    if any(word in text for word in _UNRESOLVED_WORDS):
        score += 1.8
    if 6 <= len(text) <= 48:
        score += 1.0
    elif len(text) <= 70:
        score += 0.6
    score += max(0.0, 0.5 - (order * 0.03))
    return score


def _keyword_anchors(text: str, *, source_field: str = "memo") -> Iterable[Tuple[str, str]]:
    # Extract compact phrases that often represent the user's own explanation,
    # without replacing or generalizing the surrounding sentence.
    patterns = (
        r"[^。！？!?、,\n\r]{0,24}不安になる",
        r"[^。！？!?、,\n\r]{0,24}不安になっている",
        r"[^。！？!?、,\n\r]{1,24}できるのかなぁ",
        r"[^。！？!?、,\n\r]{1,24}できるのかなあ",
        r"せめて[^。！？!?、,\n\r]{0,24}したい",
        r"[^。！？!?、,\n\r]{1,18}同棲[^。！？!?、,\n\r]{0,12}したい",
        r"[^。！？!?、,\n\r]{1,14}と話した",
        r"[ぁ-んァ-ヶ一-龠A-Za-z0-9]{1,14}の頻度",
        r"[ぁ-んァ-ヶ一-龠A-Za-z0-9]{1,14}の距離感",
        r"[ぁ-んァ-ヶ一-龠A-Za-z0-9]{1,14}の違い",
        r"[ぁ-んァ-ヶ一-龠A-Za-z0-9]{1,14}の不一致",
        r"[ぁ-んァ-ヶ一-龠A-Za-z0-9]{1,14}と喧嘩した",
        r"わかり合えなくて[^。！？!?、,\n\r]{0,18}",
        r"分かり合えなくて[^。！？!?、,\n\r]{0,18}",
        r"すれ違ってしまった",
        r"すれ違った",
    )
    seen: set[str] = set()
    for pattern in patterns:
        for match in re.finditer(pattern, text):
            phrase = _clean_text(match.group(0))
            phrase = re.sub(r"^(自分は|私は|僕は|俺は|相手は)", "", phrase)
            if len(phrase) < 3 or phrase in seen:
                continue
            seen.add(phrase)
            yield phrase, _role_for(phrase, source_field=source_field)


def extract_user_word_anchors(
    *,
    current_input: Dict[str, Any],
    max_anchors: int,
    evidence: EvidenceRef,
) -> List[UserWordAnchor]:
    """Return high-value current-input words/clauses in priority order."""

    scored: List[Tuple[float, int, str, str, str]] = []
    source_fields = ("memo", "memo_action")
    order = 0
    for field in source_fields:
        raw = str(current_input.get(field) or "")
        if not raw.strip():
            continue
        for phrase, role in _keyword_anchors(raw, source_field=field):
            scored.append((_score_clause(phrase, order=order, source_field=field) + 1.2, order, phrase, field, role))
            order += 1
        for clause in _split_clauses(raw):
            scored.append((_score_clause(clause, order=order, source_field=field), order, clause, field, _role_for(clause, source_field=field)))
            order += 1

    if not scored:
        return []

    # Prefer high-value anchors, but de-duplicate before applying the cap.
    # Otherwise a keyword and its full clause can consume multiple slots and
    # push out important adjacent words such as uncertainty or wishes.
    scored.sort(key=lambda item: (-item[0], item[1]))
    selected: List[Tuple[float, int, str, str, str]] = []
    seen_text: set[str] = set()
    limit = max(0, int(max_anchors or 0))
    if limit <= 0:
        return []
    for item in scored:
        clean = _clean_text(item[2])
        if not clean or clean in seen_text:
            continue
        seen_text.add(clean)
        selected.append(item)
        if len(selected) >= limit:
            break
    selected.sort(key=lambda item: item[1])

    anchors: List[UserWordAnchor] = []
    for idx, (score, _order, text, field, role) in enumerate(selected):
        clean = _clean_text(text)
        if not clean:
            continue
        anchors.append(
            UserWordAnchor(
                anchor_key=f"current_word:{field}:{idx}",
                text=clean,
                source_field=field,
                role=role,
                evidence=[EvidenceRef(kind=evidence.kind, ref_id=evidence.ref_id, weight=evidence.weight, note=f"user_word_anchor:{field}")],
                confidence=max(0.45, min(1.0, score / 7.0)),
            )
        )
    return anchors


__all__ = ["extract_user_word_anchors"]
