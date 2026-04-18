# -*- coding: utf-8 -*-
from __future__ import annotations

"""Internal history-search helpers for EmlisAI."""

from collections import Counter
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional

from fastapi import HTTPException

from supabase_client import sb_get

EMOTIONS_TABLE = "emotions"
JST = timezone(timedelta(hours=9))


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


def _parse_iso(value: Any) -> Optional[datetime]:
    raw = str(value or "").strip()
    if not raw:
        return None
    try:
        dt = datetime.fromisoformat(raw.replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)
    except Exception:
        return None


def _to_jst_date_key(value: Any) -> Optional[str]:
    dt = _parse_iso(value)
    if dt is None:
        return None
    local = dt.astimezone(JST)
    return f"{local.year:04d}-{local.month:02d}-{local.day:02d}"


def _emotion_labels_from_details(raw: Any) -> set[str]:
    out: set[str] = set()
    if not isinstance(raw, list):
        return out
    for item in raw:
        if not isinstance(item, dict):
            continue
        label = str(item.get("type") or item.get("emotion_type") or item.get("emotion") or "").strip()
        if label:
            out.add(label)
    return out


def _category_labels(raw: Any) -> set[str]:
    if not isinstance(raw, list):
        return set()
    return {str(v).strip() for v in raw if str(v).strip()}


def _memo_tokens(*values: Optional[str]) -> set[str]:
    tokens: set[str] = set()
    for value in values:
        text = str(value or "").strip()
        if not text:
            continue
        for token in text.replace("\n", " ").replace("、", " ").replace("。", " ").split():
            t = token.strip()
            if len(t) >= 2:
                tokens.add(t)
    return tokens


async def get_last_input_for_user(
    user_id: str,
    *,
    include_secret: bool = True,
    exclude_emotion_id: Optional[Any] = None,
) -> Optional[Dict[str, Any]]:
    params = {
        "select": "id,created_at,emotions,emotion_details,memo,memo_action,category,is_secret",
        "user_id": f"eq.{str(user_id or '').strip()}",
        "order": "created_at.desc,id.desc",
        "limit": "5",
    }
    if not include_secret:
        params["is_secret"] = "eq.false"
    resp = await sb_get(f"/rest/v1/{EMOTIONS_TABLE}", params=params, timeout=6.0)
    if resp.status_code >= 300:
        raise HTTPException(status_code=502, detail="Failed to load last emotion input")
    rows = _pick_rows(resp)
    excluded = str(exclude_emotion_id or "").strip()
    for row in rows:
        if excluded and str(row.get("id") or "").strip() == excluded:
            continue
        return row
    return None


async def list_same_day_recent_inputs(
    user_id: str,
    *,
    created_at: str,
    include_secret: bool = True,
    limit: int = 3,
    exclude_emotion_id: Optional[Any] = None,
) -> List[Dict[str, Any]]:
    date_key = _to_jst_date_key(created_at)
    if not date_key:
        return []
    created_dt = _parse_iso(created_at) or datetime.now(timezone.utc)
    local = created_dt.astimezone(JST)
    start_local = datetime(local.year, local.month, local.day, tzinfo=JST)
    params = {
        "select": "id,created_at,emotions,emotion_details,memo,memo_action,category,is_secret",
        "user_id": f"eq.{str(user_id or '').strip()}",
        "created_at": f"gte.{start_local.astimezone(timezone.utc).isoformat().replace('+00:00', 'Z')}",
        "order": "created_at.desc,id.desc",
        "limit": str(max(1, int(limit) * 6)),
    }
    if not include_secret:
        params["is_secret"] = "eq.false"
    resp = await sb_get(f"/rest/v1/{EMOTIONS_TABLE}", params=params, timeout=6.0)
    if resp.status_code >= 300:
        raise HTTPException(status_code=502, detail="Failed to load same-day emotion inputs")
    rows: List[Dict[str, Any]] = []
    excluded = str(exclude_emotion_id or "").strip()
    for row in _pick_rows(resp):
        if excluded and str(row.get("id") or "").strip() == excluded:
            continue
        row_key = _to_jst_date_key(row.get("created_at"))
        if row_key != date_key:
            continue
        row_created_at = str(row.get("created_at") or "")
        if row_created_at >= str(created_at or ""):
            continue
        rows.append(row)
        if len(rows) >= max(0, int(limit)):
            break
    return rows


async def search_similar_inputs(
    user_id: str,
    *,
    memo: Optional[str],
    memo_action: Optional[str],
    category: Optional[List[str]],
    emotion_details: Optional[List[Dict[str, Any]]],
    include_secret: bool = True,
    window_days: Optional[int] = 365,
    limit: int = 3,
    exclude_emotion_id: Optional[Any] = None,
) -> List[Dict[str, Any]]:
    params = {
        "select": "id,created_at,emotions,emotion_details,memo,memo_action,category,is_secret",
        "user_id": f"eq.{str(user_id or '').strip()}",
        "order": "created_at.desc,id.desc",
        "limit": str(max(1, int(limit) * 10)),
    }
    if not include_secret:
        params["is_secret"] = "eq.false"
    if window_days:
        floor_dt = datetime.now(timezone.utc) - timedelta(days=int(window_days))
        params["created_at"] = f"gte.{floor_dt.isoformat().replace('+00:00', 'Z')}"
    resp = await sb_get(f"/rest/v1/{EMOTIONS_TABLE}", params=params, timeout=6.0)
    if resp.status_code >= 300:
        raise HTTPException(status_code=502, detail="Failed to load similar emotion inputs")
    desired_categories = _category_labels(category)
    desired_emotions = _emotion_labels_from_details(emotion_details)
    desired_memo_tokens = _memo_tokens(memo, memo_action)
    ranked: List[Dict[str, Any]] = []
    excluded = str(exclude_emotion_id or "").strip()
    for row in _pick_rows(resp):
        if excluded and str(row.get("id") or "").strip() == excluded:
            continue
        score = 0
        row_categories = _category_labels(row.get("category"))
        row_emotions = _emotion_labels_from_details(row.get("emotion_details"))
        row_memo_tokens = _memo_tokens(row.get("memo"), row.get("memo_action"))
        score += len(desired_categories & row_categories) * 3
        score += len(desired_emotions & row_emotions) * 2
        score += len(desired_memo_tokens & row_memo_tokens)
        if score <= 0:
            continue
        row_copy = dict(row)
        row_copy["_emlis_score"] = score
        ranked.append(row_copy)
    ranked.sort(
        key=lambda item: (
            -int(item.get("_emlis_score") or 0),
            str(item.get("created_at") or ""),
            str(item.get("id") or ""),
        )
    )
    return ranked[: max(0, int(limit))]


def extract_repeated_categories(inputs: List[Dict[str, Any]], *, topn: int = 5) -> List[Dict[str, Any]]:
    counter: Counter[str] = Counter()
    last_seen: Dict[str, str] = {}
    for row in inputs:
        for label in _category_labels(row.get("category")):
            counter[label] += 1
            created_at = str(row.get("created_at") or "").strip()
            if created_at and (label not in last_seen or created_at > last_seen[label]):
                last_seen[label] = created_at
    out: List[Dict[str, Any]] = []
    for label, count in counter.most_common(max(0, int(topn))):
        out.append({"label": label, "count": int(count), "last_seen_at": last_seen.get(label)})
    return out


def extract_repeated_memo_tokens(inputs: List[Dict[str, Any]], *, topn: int = 8) -> List[Dict[str, Any]]:
    counter: Counter[str] = Counter()
    last_seen: Dict[str, str] = {}
    for row in inputs:
        tokens = _memo_tokens(row.get("memo"), row.get("memo_action"))
        for token in tokens:
            counter[token] += 1
            created_at = str(row.get("created_at") or "").strip()
            if created_at and (token not in last_seen or created_at > last_seen[token]):
                last_seen[token] = created_at
    out: List[Dict[str, Any]] = []
    for token, count in counter.most_common(max(0, int(topn))):
        out.append({"token": token, "count": int(count), "last_seen_at": last_seen.get(token)})
    return out


def build_open_topic_anchor_candidates(inputs: List[Dict[str, Any]], *, topn: int = 5) -> List[Dict[str, Any]]:
    anchors: List[Dict[str, Any]] = []
    for item in extract_repeated_categories(inputs, topn=topn):
        anchors.append(
            {
                "anchor_key": f"category:{item['label']}",
                "label": str(item["label"]),
                "count": int(item.get("count") or 0),
                "last_seen_at": item.get("last_seen_at"),
            }
        )
    remaining = max(0, int(topn) - len(anchors))
    if remaining > 0:
        for item in extract_repeated_memo_tokens(inputs, topn=remaining):
            anchors.append(
                {
                    "anchor_key": f"token:{item['token']}",
                    "label": str(item["token"]),
                    "count": int(item.get("count") or 0),
                    "last_seen_at": item.get("last_seen_at"),
                }
            )
    return anchors[: max(0, int(topn))]
