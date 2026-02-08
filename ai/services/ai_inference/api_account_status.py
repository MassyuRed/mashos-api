# -*- coding: utf-8 -*-
"""api_account_status.py

Account Status (public profile stats) API
----------------------------------------

Purpose
  - Provide a single, stable summary payload for the Account screen "ステータス".
  - Values are totals ("トータル").
  - Designed to be viewable by both self and other users.

Endpoint
  - GET /account/status?target_user_id=<uuid>

Auth
  - Requires Authorization: Bearer <supabase_access_token>
  - Any authenticated user may read others' status (Phase A).
    (Future: allow per-user privacy toggle.)

Data source
  - Supabase PostgREST RPC (service role): account_status_summary(p_target_user_id)

Notes
  - The API returns numbers only (no units) for i18n friendliness.
"""

from __future__ import annotations

import logging
import os
from typing import Any, Dict, Optional

import httpx
from fastapi import FastAPI, Header, HTTPException, Query
from pydantic import BaseModel, Field

from api_emotion_submit import (
    _ensure_supabase_config,
    _extract_bearer_token,
    _resolve_user_id_from_token,
)


logger = logging.getLogger("account_status_api")

SUPABASE_URL = os.getenv("SUPABASE_URL", "").rstrip("/")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")

# RPC function name (overrideable)
ACCOUNT_STATUS_RPC = (
    os.getenv("COCOLON_ACCOUNT_STATUS_RPC", "account_status_summary")
    or "account_status_summary"
).strip()


class AccountStatusResponse(BaseModel):
    status: str = Field("ok", description="ok")
    target_user_id: str = Field(..., description="Target user UUID")

    # Totals (numbers only)
    login_days_total: int = 0
    login_streak_max: int = 0
    input_count_total: int = 0
    input_chars_total: int = 0
    mymodel_questions_total: int = 0
    mymodel_views_total: int = 0
    mymodel_resonances_total: int = 0


def _sb_headers_json(*, prefer: Optional[str] = None) -> Dict[str, str]:
    _ensure_supabase_config()
    h = {
        "apikey": SUPABASE_SERVICE_ROLE_KEY,
        "Authorization": f"Bearer {SUPABASE_SERVICE_ROLE_KEY}",
        "Content-Type": "application/json",
    }
    if prefer:
        h["Prefer"] = prefer
    return h


async def _sb_post_rpc(fn: str, payload: Dict[str, Any]) -> Any:
    _ensure_supabase_config()
    url = f"{SUPABASE_URL}/rest/v1/rpc/{fn}"
    async with httpx.AsyncClient(timeout=8.0) as client:
        return await client.post(url, headers=_sb_headers_json(), json=payload)


async def _require_user_id(authorization: Optional[str]) -> str:
    token = _extract_bearer_token(authorization)
    if not token:
        raise HTTPException(status_code=401, detail="Missing bearer token")
    user_id = await _resolve_user_id_from_token(token)
    if not user_id:
        raise HTTPException(status_code=401, detail="Invalid token")
    return str(user_id)


def _to_int(v: Any) -> int:
    try:
        return int(v)
    except Exception:
        return 0


def register_account_status_routes(app: FastAPI) -> None:
    """Register /account/status endpoint."""

    @app.get("/account/status", response_model=AccountStatusResponse)
    async def account_status(
        target_user_id: Optional[str] = Query(default=None),
        user_id: Optional[str] = Query(default=None),
        viewed_user_id: Optional[str] = Query(default=None),
        authorization: Optional[str] = Header(default=None, alias="Authorization"),
    ) -> AccountStatusResponse:
        viewer_user_id = await _require_user_id(authorization)

        tgt = (
            str(target_user_id or "").strip()
            or str(user_id or "").strip()
            or str(viewed_user_id or "").strip()
            or str(viewer_user_id)
        )

        # Call RPC (preferred, fast)
        resp = await _sb_post_rpc(ACCOUNT_STATUS_RPC, {"p_target_user_id": tgt})
        if resp.status_code >= 300:
            logger.error(
                "Supabase rpc %s failed: %s %s",
                ACCOUNT_STATUS_RPC,
                resp.status_code,
                (resp.text or "")[:1500],
            )
            raise HTTPException(status_code=502, detail="Failed to fetch account status")

        data = None
        try:
            data = resp.json()
        except Exception:
            data = None

        row: Dict[str, Any] = {}
        if isinstance(data, list) and data:
            if isinstance(data[0], dict):
                row = data[0]
        elif isinstance(data, dict):
            row = data

        return AccountStatusResponse(
            status="ok",
            target_user_id=tgt,
            login_days_total=_to_int(row.get("login_days_total")),
            login_streak_max=_to_int(row.get("login_streak_max")),
            input_count_total=_to_int(row.get("input_count_total")),
            input_chars_total=_to_int(row.get("input_chars_total")),
            mymodel_questions_total=_to_int(row.get("mymodel_questions_total")),
            mymodel_views_total=_to_int(row.get("mymodel_views_total")),
            mymodel_resonances_total=_to_int(row.get("mymodel_resonances_total")),
        )
