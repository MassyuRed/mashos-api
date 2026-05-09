# -*- coding: utf-8 -*-
from __future__ import annotations

"""Candidate extraction for source-grounded personal Today Questions.

The MVP deliberately uses deterministic heuristics rather than asking a model to
invent user-specific claims.  The only text shown back to the user is a literal
substring from the original emotion input.
"""

import os
import re
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Set, Tuple

from fastapi import HTTPException

from supabase_client import sb_get
from today_question_personal_templates import (
    QUESTION_TYPE_AFTER_ACTION_CHANGE,
    QUESTION_TYPE_JOY_OR_VALUE,
    QUESTION_TYPE_PROTECTED_VALUE,
    QUESTION_TYPE_REASON_FOR_OBLIGATION,
    QUESTION_TYPE_RELATIONSHIP_MEANING,
    QUESTION_TYPE_WISH_BEHIND_DISCOMFORT,
    build_source_hash,
)

EMOTIONS_TABLE = (os.getenv("EMOTIONS_TABLE") or "emotions").strip() or "emotions"
PERSONAL_CANDIDATE_LOOKBACK_DAYS = max(1, int(os.getenv("TODAY_QUESTION_PERSONAL_CANDIDATE_LOOKBACK_DAYS", "30") or "30"))
PERSONAL_CANDIDATE_FETCH_LIMIT = max(5, int(os.getenv("TODAY_QUESTION_PERSONAL_CANDIDATE_FETCH_LIMIT", "80") or "80"))
PERSONAL_ANCHOR_MIN_CHARS = max(2, int(os.getenv("TODAY_QUESTION_PERSONAL_ANCHOR_MIN_CHARS", "4") or "4"))
PERSONAL_ANCHOR_MAX_CHARS = max(PERSONAL_ANCHOR_MIN_CHARS, int(os.getenv("TODAY_QUESTION_PERSONAL_ANCHOR_MAX_CHARS", "42") or "42"))

_SENTENCE_RE = re.compile(r"[^。！？!?\n\r]+[。！？!?]?", re.MULTILINE)
_SPACE_RE = re.compile(r"\s+")

_TYPE_PATTERNS: Sequence[Tuple[str, Sequence[str], int]] = (
    (
        QUESTION_TYPE_REASON_FOR_OBLIGATION,
        (
            "頑張らないといけない",
            "頑張らなきゃ",
            "がんばらなきゃ",
            "やらないといけない",
            "やらなきゃ",
            "しないといけない",
            "しなきゃ",
            "必要がある",
            "頑張る必要",
        ),
        95,
    ),
    (
        QUESTION_TYPE_JOY_OR_VALUE,
        (
            "人と関わるのが好き",
            "関わるのが好き",
            "好き",
            "嬉しい",
            "うれしい",
            "楽しい",
            "楽しかった",
            "心地いい",
            "心地よい",
        ),
        88,
    ),
    (
        QUESTION_TYPE_WISH_BEHIND_DISCOMFORT,
        (
            "嫌だった",
            "いやだった",
            "嫌だ",
            "つらかった",
            "辛かった",
            "つらい",
            "辛い",
            "悲しい",
            "しんどい",
            "苦しい",
            "もやもや",
        ),
        82,
    ),
    (
        QUESTION_TYPE_PROTECTED_VALUE,
        (
            "不安",
            "怖い",
            "こわい",
            "怒り",
            "怒った",
            "腹が立った",
            "焦り",
            "焦った",
            "イライラ",
            "いらいら",
        ),
        78,
    ),
    (
        QUESTION_TYPE_RELATIONSHIP_MEANING,
        (
            "人と関わる",
            "関係",
            "友達",
            "家族",
            "相手",
            "会話",
            "話した",
            "聞いて",
            "伝えた",
        ),
        70,
    ),
)

_HEAVY_CONTENT_TERMS = (
    "死にたい",
    "消えたい",
    "自殺",
    "殺したい",
    "暴力",
    "虐待",
    "性的",
    "レイプ",
    "薬物",
    "OD",
    "オーバードーズ",
    "医者",
    "診断",
    "訴訟",
    "逮捕",
)


def _pick_rows(resp: Any) -> List[Dict[str, Any]]:
    try:
        data = resp.json()
    except Exception:
        return []
    if isinstance(data, list):
        return [row for row in data if isinstance(row, dict)]
    if isinstance(data, dict):
        return [data]
    return []


def _iso_z(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


async def list_recent_emotion_inputs_for_personal_today_question(
    user_id: str,
    *,
    limit: int = PERSONAL_CANDIDATE_FETCH_LIMIT,
    lookback_days: int = PERSONAL_CANDIDATE_LOOKBACK_DAYS,
) -> List[Dict[str, Any]]:
    uid = str(user_id or "").strip()
    if not uid:
        return []
    floor_dt = datetime.now(timezone.utc) - timedelta(days=max(1, int(lookback_days or PERSONAL_CANDIDATE_LOOKBACK_DAYS)))
    params = {
        "select": "id,created_at,emotions,emotion_details,memo,memo_action,category,is_secret",
        "user_id": f"eq.{uid}",
        "created_at": f"gte.{_iso_z(floor_dt)}",
        "order": "created_at.desc,id.desc",
        "limit": str(max(1, int(limit or PERSONAL_CANDIDATE_FETCH_LIMIT))),
    }
    resp = await sb_get(f"/rest/v1/{EMOTIONS_TABLE}", params=params, timeout=8.0)
    if resp.status_code >= 300:
        raise HTTPException(status_code=502, detail="Failed to load emotion inputs for personal today question")
    return _pick_rows(resp)


def _clean_display_text(value: Any) -> str:
    text = str(value or "").strip()
    return _SPACE_RE.sub(" ", text)


def _contains_heavy_content(text: str) -> bool:
    target = str(text or "")
    return any(term in target for term in _HEAVY_CONTENT_TERMS)


def _sentences_with_offsets(text: str) -> Iterable[Tuple[str, int, int]]:
    raw = str(text or "")
    for match in _SENTENCE_RE.finditer(raw):
        fragment = match.group(0)
        if not fragment or not fragment.strip():
            continue
        start = match.start()
        end = match.end()
        while start < end and raw[start].isspace():
            start += 1
        while end > start and raw[end - 1].isspace():
            end -= 1
        if end <= start:
            continue
        yield raw[start:end], start, end


def _anchor_from_keyword(text: str, keyword: str) -> Optional[Tuple[str, int, int]]:
    raw = str(text or "")
    idx = raw.find(keyword)
    if idx < 0:
        return None
    end = idx + len(keyword)
    return raw[idx:end], idx, end


def _anchor_from_sentence(text: str, keyword: str) -> Optional[Tuple[str, int, int]]:
    for sentence, start, end in _sentences_with_offsets(text):
        if keyword not in sentence:
            continue
        display = _clean_display_text(sentence)
        if PERSONAL_ANCHOR_MIN_CHARS <= len(display) <= PERSONAL_ANCHOR_MAX_CHARS:
            return sentence, start, end
        return _anchor_from_keyword(text, keyword)
    return None


def _candidate_for_text_field(
    *,
    row: Mapping[str, Any],
    source_field: str,
    text: str,
    seen_keys: Set[Tuple[str, str, str]],
) -> Optional[Dict[str, Any]]:
    if not text or _contains_heavy_content(text):
        return None
    source_id = str(row.get("id") or "").strip()
    if not source_id:
        return None

    for question_type, keywords, base_score in _TYPE_PATTERNS:
        for keyword in keywords:
            if keyword not in text:
                continue
            anchor = _anchor_from_sentence(text, keyword) or _anchor_from_keyword(text, keyword)
            if not anchor:
                continue
            anchor_text, anchor_start, anchor_end = anchor
            anchor_display = _clean_display_text(anchor_text)
            if not (PERSONAL_ANCHOR_MIN_CHARS <= len(anchor_display) <= PERSONAL_ANCHOR_MAX_CHARS):
                continue
            if anchor_text not in text:
                continue
            dedupe_key = (source_id, anchor_display, question_type)
            if dedupe_key in seen_keys:
                continue
            score = int(base_score)
            if source_field == "memo":
                score += 4
            if question_type == QUESTION_TYPE_REASON_FOR_OBLIGATION:
                score += 3
            source_hash = build_source_hash(
                source_id=source_id,
                source_field=source_field,
                anchor_text=anchor_display,
                question_type=question_type,
            )
            return {
                "source_type": "emotion_input",
                "source_id": source_id,
                "source_field": source_field,
                "anchor_text": anchor_display,
                "anchor_start": anchor_start,
                "anchor_end": anchor_end,
                "question_type": question_type,
                "score": score,
                "source_hash": source_hash,
                "source_created_at": str(row.get("created_at") or "").strip() or None,
                "reason_json": {
                    "matched_keyword": keyword,
                    "source_field": source_field,
                    "source_created_at": str(row.get("created_at") or "").strip() or None,
                },
            }
    return None


def _candidate_for_action_field(
    *,
    row: Mapping[str, Any],
    seen_keys: Set[Tuple[str, str, str]],
) -> Optional[Dict[str, Any]]:
    source_id = str(row.get("id") or "").strip()
    text = str(row.get("memo_action") or "").strip()
    if not source_id or not text or _contains_heavy_content(text):
        return None
    for sentence, start, end in _sentences_with_offsets(text):
        display = _clean_display_text(sentence)
        if not (PERSONAL_ANCHOR_MIN_CHARS <= len(display) <= PERSONAL_ANCHOR_MAX_CHARS):
            continue
        dedupe_key = (source_id, display, QUESTION_TYPE_AFTER_ACTION_CHANGE)
        if dedupe_key in seen_keys:
            continue
        source_hash = build_source_hash(
            source_id=source_id,
            source_field="memo_action",
            anchor_text=display,
            question_type=QUESTION_TYPE_AFTER_ACTION_CHANGE,
        )
        return {
            "source_type": "emotion_input",
            "source_id": source_id,
            "source_field": "memo_action",
            "anchor_text": display,
            "anchor_start": start,
            "anchor_end": end,
            "question_type": QUESTION_TYPE_AFTER_ACTION_CHANGE,
            "score": 74,
            "source_hash": source_hash,
            "source_created_at": str(row.get("created_at") or "").strip() or None,
            "reason_json": {
                "matched_keyword": "memo_action",
                "source_field": "memo_action",
                "source_created_at": str(row.get("created_at") or "").strip() or None,
            },
        }
    return None


def build_best_personal_today_question_candidate(
    rows: Sequence[Mapping[str, Any]],
    *,
    seen_keys: Optional[Set[Tuple[str, str, str]]] = None,
) -> Optional[Dict[str, Any]]:
    seen = set(seen_keys or set())
    candidates: List[Dict[str, Any]] = []
    for index, row in enumerate(rows or []):
        if not isinstance(row, Mapping):
            continue
        memo = str(row.get("memo") or "")
        memo_action = str(row.get("memo_action") or "")
        # Main memo first: this tends to carry the user's reason/value words.
        cand = _candidate_for_text_field(
            row=row,
            source_field="memo",
            text=memo,
            seen_keys=seen,
        )
        if cand:
            cand["score"] = int(cand.get("score") or 0) + max(0, 20 - index)
            candidates.append(cand)
        # Action follow-up is useful when the user recorded an actual action.
        action_cand = _candidate_for_action_field(row=row, seen_keys=seen)
        if action_cand:
            action_cand["score"] = int(action_cand.get("score") or 0) + max(0, 15 - index)
            candidates.append(action_cand)
        # Relationship / joy words sometimes appear in action text too.
        cand2 = _candidate_for_text_field(
            row=row,
            source_field="memo_action",
            text=memo_action,
            seen_keys=seen,
        )
        if cand2:
            cand2["score"] = int(cand2.get("score") or 0) + max(0, 12 - index)
            candidates.append(cand2)

    if not candidates:
        return None
    candidates.sort(
        key=lambda c: (
            -int(c.get("score") or 0),
            str(c.get("source_created_at") or ""),
            str(c.get("source_id") or ""),
        )
    )
    return candidates[0]
