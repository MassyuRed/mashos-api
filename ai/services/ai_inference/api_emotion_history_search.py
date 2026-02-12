# -*- coding: utf-8 -*-
"""Emotion History Search API (server-side)
------------------------------------------------

Phase 2: 履歴検索を完全にAPI化（クライアントの全件取得 + フロントfilter を廃止するための土台）

提供エンドポイント
  - POST /emotion/history/search
  - GET  /emotion/history/search   (同等。デバッグ/検証用)

要件（Mash 確定）
  - AND検索（スペース区切り）
  - 日検索: YYYY-MM-DD / YYYY/M/D
  - 月検索: YYYY-MM / YYYY/M
  - 強度検索: 強/中/弱（= strong/medium/weak）
  - 検索対象:
      - memo / memo_action
      - emotions(text[])（配列 contains）
      - emotion_details(jsonb[]) の type / strength
  - is_secret は既定で含める（all）。public-only / secret-only も指定可能。
  - 返却は必ずページング（offset/limit）。count は重いので既定では返さない。

実装メモ
  - Supabase(PostgREST) を service_role で叩く（RLSをバイパス）。
  - ただし access_token で user_id を解決し、必ず user_id=eq.<self> を付ける。
  - AND 検索は PostgREST の論理ツリー `and=(or(...),or(...))` で表現する。
"""

from __future__ import annotations

import json
import logging
import os
import re
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Literal, Optional, Tuple

import httpx
from fastapi import FastAPI, Header, HTTPException, Query
from pydantic import BaseModel, Field

from api_emotion_submit import (
    SUPABASE_SERVICE_ROLE_KEY,
    SUPABASE_URL,
    _ensure_supabase_config,
    _extract_bearer_token,
    _resolve_user_id_from_token,
)


logger = logging.getLogger("emotion_history_search")


# -------------------------
# Timezone (JST fixed)
# -------------------------
JST_OFFSET = timedelta(hours=9)
JST = timezone(JST_OFFSET)


# -------------------------
# Parsing helpers
# -------------------------

_RE_DAY = re.compile(r"^(\d{4})[-/](\d{1,2})[-/](\d{1,2})$")
_RE_MONTH = re.compile(r"^(\d{4})[-/](\d{1,2})$")


def _to_utc_iso(dt: datetime) -> str:
    """UTC ISO string with 'Z'."""
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    dt_utc = dt.astimezone(timezone.utc)
    # keep milliseconds for upper bound precision
    return dt_utc.isoformat().replace("+00:00", "Z")


def _jst_day_range_utc(year: int, month: int, day: int) -> Tuple[datetime, datetime]:
    """Return [start,end] UTC datetime range for a JST calendar day."""
    start_jst = datetime(year, month, day, 0, 0, 0, 0, tzinfo=JST)
    end_jst = datetime(year, month, day, 23, 59, 59, 999000, tzinfo=JST)
    return start_jst.astimezone(timezone.utc), end_jst.astimezone(timezone.utc)


def _jst_month_range_utc(year: int, month: int) -> Tuple[datetime, datetime]:
    """Return [start,end] UTC datetime range for a JST calendar month."""
    start_jst = datetime(year, month, 1, 0, 0, 0, 0, tzinfo=JST)
    # next month 1st - 1ms
    if month == 12:
        next_jst = datetime(year + 1, 1, 1, 0, 0, 0, 0, tzinfo=JST)
    else:
        next_jst = datetime(year, month + 1, 1, 0, 0, 0, 0, tzinfo=JST)
    end_jst = next_jst - timedelta(milliseconds=1)
    return start_jst.astimezone(timezone.utc), end_jst.astimezone(timezone.utc)


def _parse_date_token(token: str) -> Optional[Tuple[str, int, int, int]]:
    """Return ('day'|'month', y, m, d) where d=1 for month."""
    t = token.strip()
    if not t:
        return None

    m = _RE_DAY.match(t)
    if m:
        y, mo, d = int(m.group(1)), int(m.group(2)), int(m.group(3))
        if 1 <= mo <= 12 and 1 <= d <= 31:
            return ("day", y, mo, d)
        return None

    m2 = _RE_MONTH.match(t)
    if m2:
        y, mo = int(m2.group(1)), int(m2.group(2))
        if 1 <= mo <= 12:
            return ("month", y, mo, 1)
        return None

    return None


def _normalize_strength_token(token: str) -> Optional[str]:
    t = token.strip().lower()
    if not t:
        return None

    # JP
    if t in ("強", "強い"):
        return "strong"
    if t in ("中", "普通"):
        return "medium"
    if t in ("弱", "弱い"):
        return "weak"

    # EN
    if t in ("strong", "medium", "weak"):
        return t

    return None


def _sanitize_keyword_token(token: str) -> str:
    """Sanitize a keyword token to avoid breaking PostgREST logic-tree syntax.

    Notes:
      - PostgREST logical tree uses ',', '(', ')' as separators.
      - We strip those chars from keyword tokens to keep the query valid.
      - This is a pragmatic guard; typical user input is JP words without these.
    """
    t = token.strip()
    if not t:
        return ""
    # Remove chars that can break logical-tree parsing.
    t = re.sub(r"[(),]", " ", t)
    # wildcard '*' is meaningful in PostgREST like/ilike patterns
    t = t.replace("*", " ")
    # quotes can also confuse
    t = t.replace('"', " ").replace("'", " ")
    # collapse spaces
    t = re.sub(r"\s+", " ", t).strip()
    return t


def _tokenize_query(raw: Optional[str]) -> List[str]:
    if not raw:
        return []
    s = str(raw).strip()
    if not s:
        return []
    return [t for t in re.split(r"\s+", s) if t]


# -------------------------
# Supabase helpers
# -------------------------


def _sb_headers(*, prefer: Optional[str] = None) -> Dict[str, str]:
    _ensure_supabase_config()
    h = {
        "apikey": SUPABASE_SERVICE_ROLE_KEY,
        "Authorization": f"Bearer {SUPABASE_SERVICE_ROLE_KEY}",
        "Content-Type": "application/json",
    }
    if prefer:
        h["Prefer"] = prefer
    return h


async def _sb_get_emotions(*, params: List[Tuple[str, str]]) -> httpx.Response:
    _ensure_supabase_config()
    if not SUPABASE_URL:
        raise HTTPException(status_code=500, detail="Supabase URL is not configured")
    url = f"{SUPABASE_URL}/rest/v1/emotions"
    async with httpx.AsyncClient(timeout=10.0) as client:
        return await client.get(url, headers=_sb_headers(), params=params)


# -------------------------
# Request/Response models
# -------------------------


class EmotionHistorySearchRequest(BaseModel):
    query: Optional[str] = Field(default=None, description="検索文字列（スペース区切りAND）")
    secret_filter: Literal["all", "public", "secret"] = Field(
        default="all",
        description="secret を含めるか（all=両方, public=公開のみ, secret=secretのみ）",
    )
    order: Literal["desc", "asc"] = Field(default="desc", description="created_at の並び")
    offset: int = Field(default=0, ge=0, description="ページング offset")
    limit: int = Field(default=50, ge=1, le=200, description="ページング limit（最大200）")


class EmotionHistorySearchMeta(BaseModel):
    offset: int
    limit: int
    has_more: bool
    next_offset: Optional[int] = None
    applied: Dict[str, Any] = {}


class EmotionHistorySearchResponse(BaseModel):
    status: str = "ok"
    user_id: str
    items: List[Dict[str, Any]]
    meta: EmotionHistorySearchMeta


# -------------------------
# Query building
# -------------------------


@dataclass
class _ParsedSearch:
    keyword_tokens: List[str]
    strength_tokens: List[str]
    date_start_utc: Optional[datetime]
    date_end_utc: Optional[datetime]


def _parse_search_query(raw_query: Optional[str]) -> _ParsedSearch:
    tokens = _tokenize_query(raw_query)

    keyword_tokens: List[str] = []
    strength_tokens: List[str] = []
    date_start_utc: Optional[datetime] = None
    date_end_utc: Optional[datetime] = None

    for tok in tokens:
        # 1) date
        dt = _parse_date_token(tok)
        if dt:
            kind, y, m, d = dt
            if kind == "day":
                s, e = _jst_day_range_utc(y, m, d)
            else:
                s, e = _jst_month_range_utc(y, m)

            if date_start_utc is None or s > date_start_utc:
                date_start_utc = s
            if date_end_utc is None or e < date_end_utc:
                date_end_utc = e
            continue

        # 2) strength
        st = _normalize_strength_token(tok)
        if st:
            strength_tokens.append(st)
            continue

        # 3) keyword
        safe = _sanitize_keyword_token(tok)
        if safe:
            keyword_tokens.append(safe)

    return _ParsedSearch(
        keyword_tokens=keyword_tokens,
        strength_tokens=strength_tokens,
        date_start_utc=date_start_utc,
        date_end_utc=date_end_utc,
    )


def _build_postgrest_and_expr(parsed: _ParsedSearch) -> Optional[str]:
    """Build PostgREST logical-tree `and=(...)` value.

    We only include dynamic conditions here (keyword OR-groups + strength contains).
    Other simple filters (user_id / created_at / is_secret) are passed as normal params.
    """
    clauses: List[str] = []

    # strength filters: emotion_details contains an element with strength
    for st in parsed.strength_tokens:
        js = json.dumps([{"strength": st}], ensure_ascii=False, separators=(",", ":"))
        clauses.append(f"emotion_details.cs.{js}")

    # keyword tokens: OR across memo/memo_action/emotions/emotion_details.type
    for tok in parsed.keyword_tokens:
        # PostgREST like/ilike uses '*' as wildcard
        pattern = f"*{tok}*"
        js_type = json.dumps([{"type": tok}], ensure_ascii=False, separators=(",", ":"))
        or_clauses = [
            f"memo.ilike.{pattern}",
            f"memo_action.ilike.{pattern}",
            f"emotions.cs.{{{tok}}}",
            f"emotion_details.cs.{js_type}",
        ]
        clauses.append(f"or({','.join(or_clauses)})")

    if not clauses:
        return None
    return f"({','.join(clauses)})"


# -------------------------
# Routes
# -------------------------


def register_emotion_history_search_routes(app: FastAPI) -> None:
    """Register /emotion/history/search routes."""

    async def _handle_search(
        *,
        authorization: Optional[str],
        payload: EmotionHistorySearchRequest,
    ) -> EmotionHistorySearchResponse:
        access_token = _extract_bearer_token(authorization)
        if not access_token:
            raise HTTPException(status_code=401, detail="Authorization header with Bearer token is required")

        user_id = await _resolve_user_id_from_token(access_token)

        parsed = _parse_search_query(payload.query)
        # If date range collapses to empty, return early.
        if parsed.date_start_utc and parsed.date_end_utc and parsed.date_start_utc > parsed.date_end_utc:
            return EmotionHistorySearchResponse(
                user_id=user_id,
                items=[],
                meta=EmotionHistorySearchMeta(
                    offset=payload.offset,
                    limit=payload.limit,
                    has_more=False,
                    next_offset=None,
                    applied={
                        "query": payload.query or "",
                        "secret_filter": payload.secret_filter,
                        "order": payload.order,
                        "date": "empty",
                    },
                ),
            )

        # ---- Build Supabase(PostgREST) params ----
        # NOTE: limit+1 for has_more detection (no count query)
        limit_plus = int(payload.limit) + 1

        select_cols = (
            "id,created_at,emotions,emotion_details,emotion_strength_avg,memo,memo_action,is_secret"
        )

        params: List[Tuple[str, str]] = [
            ("select", select_cols),
            ("user_id", f"eq.{user_id}"),
            ("offset", str(int(payload.offset))),
            ("limit", str(limit_plus)),
        ]

        # created_at range (UTC ISO)
        if parsed.date_start_utc is not None:
            params.append(("created_at", f"gte.{_to_utc_iso(parsed.date_start_utc)}"))
        if parsed.date_end_utc is not None:
            params.append(("created_at", f"lte.{_to_utc_iso(parsed.date_end_utc)}"))

        # secret filter
        if payload.secret_filter == "public":
            params.append(("is_secret", "eq.false"))
        elif payload.secret_filter == "secret":
            params.append(("is_secret", "eq.true"))

        # order (stable)
        if payload.order == "asc":
            params.append(("order", "created_at.asc,id.asc"))
        else:
            params.append(("order", "created_at.desc,id.desc"))

        # AND expr (dynamic)
        and_expr = _build_postgrest_and_expr(parsed)
        if and_expr:
            params.append(("and", and_expr))

        # ---- Query ----
        resp = await _sb_get_emotions(params=params)
        if resp.status_code >= 300:
            logger.error(
                "Supabase emotions search failed: status=%s body=%s",
                resp.status_code,
                resp.text[:2000],
            )
            raise HTTPException(status_code=502, detail="Failed to search emotion history")

        try:
            rows = resp.json()
        except Exception:
            rows = []

        if not isinstance(rows, list):
            rows = []

        has_more = len(rows) > payload.limit
        items = rows[: payload.limit]
        next_offset = int(payload.offset) + int(payload.limit) if has_more else None

        applied: Dict[str, Any] = {
            "query": payload.query or "",
            "secret_filter": payload.secret_filter,
            "order": payload.order,
            "offset": int(payload.offset),
            "limit": int(payload.limit),
        }
        if parsed.date_start_utc is not None or parsed.date_end_utc is not None:
            applied["created_at_utc"] = {
                "gte": _to_utc_iso(parsed.date_start_utc) if parsed.date_start_utc else None,
                "lte": _to_utc_iso(parsed.date_end_utc) if parsed.date_end_utc else None,
            }
        if parsed.strength_tokens:
            applied["strength"] = parsed.strength_tokens
        if parsed.keyword_tokens:
            applied["keywords"] = parsed.keyword_tokens

        return EmotionHistorySearchResponse(
            user_id=user_id,
            items=items,
            meta=EmotionHistorySearchMeta(
                offset=int(payload.offset),
                limit=int(payload.limit),
                has_more=bool(has_more),
                next_offset=next_offset,
                applied=applied,
            ),
        )

    @app.post("/emotion/history/search", response_model=EmotionHistorySearchResponse)
    async def emotion_history_search_post(
        payload: EmotionHistorySearchRequest,
        authorization: Optional[str] = Header(default=None, alias="Authorization"),
    ) -> EmotionHistorySearchResponse:
        return await _handle_search(authorization=authorization, payload=payload)

    # デバッグ/検証用: GETでも叩けるようにしておく（本番クライアントはPOST推奨）
    @app.get("/emotion/history/search", response_model=EmotionHistorySearchResponse)
    async def emotion_history_search_get(
        query: Optional[str] = Query(default=None, description="検索文字列（スペース区切りAND）"),
        secret_filter: Literal["all", "public", "secret"] = Query(default="all"),
        order: Literal["desc", "asc"] = Query(default="desc"),
        offset: int = Query(default=0, ge=0),
        limit: int = Query(default=50, ge=1, le=200),
        authorization: Optional[str] = Header(default=None, alias="Authorization"),
    ) -> EmotionHistorySearchResponse:
        payload = EmotionHistorySearchRequest(
            query=query,
            secret_filter=secret_filter,
            order=order,
            offset=offset,
            limit=limit,
        )
        return await _handle_search(authorization=authorization, payload=payload)
