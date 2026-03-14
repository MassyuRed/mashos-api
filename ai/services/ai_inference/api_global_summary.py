# -*- coding: utf-8 -*-
"""api_global_summary.py

Global Summary API
------------------
Purpose
  - Keep the public `/global_summary` contract stable.
  - For the current JST day, prefer a synchronous refresh so app-wide counters stay fresh.
  - For historical JST days, prefer READY artifacts from `global_activity_summaries`.
  - During migration, retain legacy `daily_global_activity` / refresh RPC fallback.

Read order
  - Current JST day:
      1) synchronous legacy refresh
      2) latest READY artifact
      3) migration fallback: legacy daily table, then legacy refresh RPC
      4) zero response
  - Historical JST day:
      1) latest READY artifact
      2) migration fallback: legacy daily table, then legacy refresh RPC
      3) zero response
"""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional, Tuple

from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field

from astor_global_summary_kernel import generate_global_summary_payload
from astor_global_summary_store import (
    GLOBAL_SUMMARY_TIMEZONE,
    extract_global_summary_totals,
    fetch_latest_ready_global_summary,
)

logger = logging.getLogger("global_summary_api")

JST = timezone(timedelta(hours=9))
GLOBAL_SUMMARY_DB_TZ = GLOBAL_SUMMARY_TIMEZONE
GLOBAL_SUMMARY_RESPONSE_TZ = "+09:00"


class GlobalSummaryResponse(BaseModel):
    date: str = Field(..., description="Target activity date in JST (YYYY-MM-DD)")
    tz: str = Field(default=GLOBAL_SUMMARY_RESPONSE_TZ, description="Response timezone (+09:00)")
    emotion_users: int = 0
    reflection_views: int = 0
    echo_count: int = 0
    discovery_count: int = 0
    updated_at: Optional[str] = None


def _normalize_global_summary_tz(raw_tz: Optional[str]) -> Tuple[str, str]:
    s = str(raw_tz or "").strip()
    if not s:
        return (GLOBAL_SUMMARY_DB_TZ, GLOBAL_SUMMARY_RESPONSE_TZ)

    normalized = s.replace(" ", "")
    if normalized in {"Asia/Tokyo", "asia/tokyo", "JST", "jst", "+09:00", "+0900", "09:00"}:
        return (GLOBAL_SUMMARY_DB_TZ, GLOBAL_SUMMARY_RESPONSE_TZ)

    raise HTTPException(status_code=400, detail="Only Asia/Tokyo (+09:00) is supported currently")


def _today_jst_date_iso() -> str:
    return datetime.now(JST).date().isoformat()


def _is_today_jst(activity_date: str) -> bool:
    return activity_date == _today_jst_date_iso()


def _resolve_global_summary_date(raw_date: Optional[str]) -> str:
    s = str(raw_date or "").strip()
    if not s:
        return _today_jst_date_iso()

    try:
        return datetime.strptime(s, "%Y-%m-%d").date().isoformat()
    except Exception as exc:
        raise HTTPException(status_code=400, detail="date must be YYYY-MM-DD") from exc


def _to_text(value: Any) -> Optional[str]:
    if value is None:
        return None
    s = str(value).strip()
    return s or None


def _global_summary_zero(*, activity_date: str, response_tz: str) -> GlobalSummaryResponse:
    return GlobalSummaryResponse(
        date=activity_date,
        tz=response_tz,
        emotion_users=0,
        reflection_views=0,
        echo_count=0,
        discovery_count=0,
        updated_at=None,
    )


def _response_from_payload(
    payload: Dict[str, Any],
    *,
    activity_date: str,
    response_tz: str,
    updated_at: Optional[str] = None,
) -> GlobalSummaryResponse:
    totals = extract_global_summary_totals(payload)
    payload_date = _to_text((payload or {}).get("activity_date") or (payload or {}).get("date")) or activity_date
    final_updated_at = (
        _to_text(updated_at)
        or _to_text((payload or {}).get("generated_at"))
        or _to_text((payload or {}).get("updated_at"))
    )

    return GlobalSummaryResponse(
        date=payload_date,
        tz=response_tz,
        emotion_users=int(totals.get("emotion_users") or 0),
        reflection_views=int(totals.get("reflection_views") or 0),
        echo_count=int(totals.get("echo_count") or 0),
        discovery_count=int(totals.get("discovery_count") or 0),
        updated_at=final_updated_at,
    )


async def _fetch_sync_refresh_summary_response(
    *,
    activity_date: str,
    timezone_name: str,
    response_tz: str,
) -> Optional[GlobalSummaryResponse]:
    try:
        payload = await generate_global_summary_payload(
            activity_date,
            timezone_name=timezone_name,
            prefer_refresh=True,
            fallback_to_table=True,
            allow_empty=False,
        )
    except Exception as exc:
        logger.warning(
            "sync global summary refresh failed: activity_date=%s timezone=%s err=%s",
            activity_date,
            timezone_name,
            exc,
        )
        return None

    return _response_from_payload(
        payload,
        activity_date=activity_date,
        response_tz=response_tz,
        updated_at=_to_text((payload or {}).get("generated_at")) or _to_text((payload or {}).get("updated_at")),
    )


async def _fetch_ready_summary_response(
    *,
    activity_date: str,
    timezone_name: str,
    response_tz: str,
) -> Optional[GlobalSummaryResponse]:
    try:
        ready_row = await fetch_latest_ready_global_summary(
            activity_date,
            timezone_name=timezone_name,
        )
    except Exception as exc:
        logger.warning(
            "READY global summary fetch failed: activity_date=%s timezone=%s err=%s",
            activity_date,
            timezone_name,
            exc,
        )
        return None

    if not ready_row:
        return None

    payload = ready_row.get("payload") if isinstance(ready_row.get("payload"), dict) else {}
    updated_at = (
        _to_text(ready_row.get("published_at"))
        or _to_text(ready_row.get("updated_at"))
        or _to_text((payload or {}).get("generated_at"))
    )
    return _response_from_payload(
        payload,
        activity_date=activity_date,
        response_tz=response_tz,
        updated_at=updated_at,
    )


async def _fetch_migration_fallback_response(
    *,
    activity_date: str,
    timezone_name: str,
    response_tz: str,
) -> Optional[GlobalSummaryResponse]:
    try:
        payload = await generate_global_summary_payload(
            activity_date,
            timezone_name=timezone_name,
            prefer_refresh=False,
            fallback_to_table=True,
            allow_empty=False,
        )
    except Exception as exc:
        logger.warning(
            "legacy global summary fallback failed: activity_date=%s timezone=%s err=%s",
            activity_date,
            timezone_name,
            exc,
        )
        return None

    return _response_from_payload(
        payload,
        activity_date=activity_date,
        response_tz=response_tz,
        updated_at=_to_text((payload or {}).get("generated_at")) or _to_text((payload or {}).get("updated_at")),
    )


def register_global_summary_routes(app: FastAPI) -> None:
    @app.get("/global_summary", response_model=GlobalSummaryResponse)
    async def global_summary(
        date: Optional[str] = Query(default=None, description="YYYY-MM-DD. Defaults to today in JST."),
        tz: Optional[str] = Query(default=GLOBAL_SUMMARY_RESPONSE_TZ, description="Currently fixed to +09:00 / Asia/Tokyo."),
    ) -> GlobalSummaryResponse:
        db_tz, response_tz = _normalize_global_summary_tz(tz)
        activity_date = _resolve_global_summary_date(date)

        try:
            if _is_today_jst(activity_date):
                fresh_response = await _fetch_sync_refresh_summary_response(
                    activity_date=activity_date,
                    timezone_name=db_tz,
                    response_tz=response_tz,
                )
                if fresh_response is not None:
                    return fresh_response

            ready_response = await _fetch_ready_summary_response(
                activity_date=activity_date,
                timezone_name=db_tz,
                response_tz=response_tz,
            )
            if ready_response is not None:
                return ready_response

            fallback_response = await _fetch_migration_fallback_response(
                activity_date=activity_date,
                timezone_name=db_tz,
                response_tz=response_tz,
            )
            if fallback_response is not None:
                return fallback_response

            return _global_summary_zero(activity_date=activity_date, response_tz=response_tz)
        except HTTPException:
            raise
        except Exception as exc:
            logger.warning("global_summary failed: %s", exc)
            return _global_summary_zero(activity_date=activity_date, response_tz=response_tz)


__all__ = [
    "GlobalSummaryResponse",
    "register_global_summary_routes",
]
