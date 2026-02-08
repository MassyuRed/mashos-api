# -*- coding: utf-8 -*-
"""api_activity_login.py

Activity API (Login day touch)
-----------------------------

Endpoint:
- POST /activity/login

Purpose:
- Record that the authenticated user has been active on the app for the
  current JST day (Asia/Tokyo). This is used for "連続ログイン日数" ranking.

Design:
- JST day boundary (Asia/Tokyo) at 00:00.
- `login_date` is computed server-side (prevents client clock spoofing).
- 1 user x 1 date is enforced by DB PK(user_id, login_date).
- Best-effort: if the upsert fails, return ok with stored=false (so the app UI
  won't break) and log a warning.
"""

from __future__ import annotations

import logging
import os
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, Optional

import httpx
from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel, Field

from api_emotion_submit import (
    _ensure_supabase_config,
    _extract_bearer_token,
    _resolve_user_id_from_token,
)


logger = logging.getLogger("activity.login")

SUPABASE_URL = os.getenv("SUPABASE_URL", "").rstrip("/")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")

# Tables (overrideable)
LOGIN_DAYS_TABLE = os.getenv("COCOLON_LOGIN_DAYS_TABLE", "user_login_days")


class ActivityLoginResponse(BaseModel):
    status: str = Field("ok", description="ok")
    login_date: str = Field(..., description="JST date (YYYY-MM-DD)")
    stored: bool = Field(..., description="Whether the server stored/updated the row")


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


def _iso_z(dt: datetime) -> str:
    dtu = dt.astimezone(timezone.utc)
    # Keep milliseconds for debugging; strip nothing aggressively.
    s = dtu.isoformat()
    return s.replace("+00:00", "Z")


def _today_jst_date_iso() -> str:
    # JST has no DST; fixed +09:00 is safe and avoids tzdata dependency.
    jst = timezone(timedelta(hours=9))
    return datetime.now(timezone.utc).astimezone(jst).date().isoformat()


async def _sb_upsert_login_day(*, user_id: str, login_date_iso: str) -> bool:
    """Upsert one row into user_login_days.

    - On insert: login_date default exists, but we send explicitly.
    - On conflict: update last_seen_at only.
    """

    _ensure_supabase_config()
    url = f"{SUPABASE_URL}/rest/v1/{LOGIN_DAYS_TABLE}"

    now_iso = _iso_z(datetime.now(timezone.utc))
    payload: Dict[str, Any] = {
        "user_id": str(user_id),
        "login_date": str(login_date_iso),
        "last_seen_at": now_iso,
    }

    # Composite PK: (user_id, login_date)
    params = {"on_conflict": "user_id,login_date"}

    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.post(
                url,
                headers=_sb_headers_json(prefer="resolution=merge-duplicates,return=minimal"),
                params=params,
                json=payload,
            )

        if resp.status_code in (200, 201, 204):
            return True

        logger.warning(
            "login_days upsert failed: status=%s body=%s",
            resp.status_code,
            (resp.text or "")[:500],
        )
        return False
    except Exception as exc:
        logger.warning("login_days upsert failed (network/exception): %s", exc)
        return False


def register_activity_login_routes(app: FastAPI) -> None:
    """Register /activity/login endpoint."""

    @app.post("/activity/login", response_model=ActivityLoginResponse)
    async def activity_login(
        authorization: Optional[str] = Header(default=None, alias="Authorization"),
    ) -> ActivityLoginResponse:
        token = _extract_bearer_token(authorization) if authorization else None
        if not token:
            raise HTTPException(status_code=401, detail="Authorization header with Bearer token is required")

        user_id = await _resolve_user_id_from_token(token)
        if not user_id:
            raise HTTPException(status_code=401, detail="Invalid token")

        login_date = _today_jst_date_iso()
        stored = await _sb_upsert_login_day(user_id=str(user_id), login_date_iso=login_date)
        return ActivityLoginResponse(status="ok", login_date=login_date, stored=bool(stored))
