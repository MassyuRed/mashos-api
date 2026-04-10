# -*- coding: utf-8 -*-
"""api_global_summary.py

Global Summary API
------------------
Purpose
  - Keep the public `/global_summary` contract stable.
  - For the current JST day, favor a synchronous legacy refresh so Home can reflect the latest input immediately.
  - For historical JST days, prefer READY artifacts from `global_activity_summaries`.
  - During migration, retain legacy `daily_global_activity` / refresh RPC fallback so current clients keep working.

Read order
  - Current JST day:
      1) synchronous legacy refresh RPC/table read
      2) latest READY artifact
      3) legacy fallback without forced refresh
      4) zero response
      + best-effort enqueue a READY refresh so published artifacts catch up
  - Historical JST day:
      1) latest READY artifact
      2) migration fallback: legacy daily table, then legacy refresh RPC
      3) zero response
"""

from __future__ import annotations

import asyncio
import logging
import os
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional, Tuple

from fastapi import FastAPI, HTTPException, Query
from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel, Field

from astor_global_summary_kernel import generate_global_summary_payload
from astor_global_summary_store import (
    GLOBAL_SUMMARY_TIMEZONE,
    extract_global_summary_totals,
    fetch_latest_ready_global_summary,
)
from response_microcache import build_cache_key, get_or_compute

try:
    from astor_global_summary_enqueue import enqueue_global_summary_refresh
except Exception:  # pragma: no cover
    enqueue_global_summary_refresh = None  # type: ignore

logger = logging.getLogger("global_summary_api")

JST = timezone(timedelta(hours=9))
GLOBAL_SUMMARY_DB_TZ = GLOBAL_SUMMARY_TIMEZONE
GLOBAL_SUMMARY_RESPONSE_TZ = "+09:00"
GLOBAL_SUMMARY_TODAY_CACHE_TTL_SECONDS = 5.0
GLOBAL_SUMMARY_HISTORY_CACHE_TTL_SECONDS = 60.0
try:
    GLOBAL_SUMMARY_READY_STALE_AFTER_SECONDS = float(
        os.getenv("GLOBAL_SUMMARY_READY_STALE_AFTER_SECONDS", "180") or "180"
    )
except Exception:
    GLOBAL_SUMMARY_READY_STALE_AFTER_SECONDS = 180.0
try:
    GLOBAL_SUMMARY_READY_REFRESH_ENQUEUE_THROTTLE_SECONDS = float(
        os.getenv("GLOBAL_SUMMARY_READY_REFRESH_ENQUEUE_THROTTLE_SECONDS", "90") or "90"
    )
except Exception:
    GLOBAL_SUMMARY_READY_REFRESH_ENQUEUE_THROTTLE_SECONDS = 90.0

GLOBAL_SUMMARY_MODE_DEFAULT = "default"
GLOBAL_SUMMARY_MODE_READY_FIRST = "ready_first"
GLOBAL_SUMMARY_MODE_SYNC = "sync"


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


def _normalize_global_summary_mode(raw_mode: Optional[str]) -> str:
    s = str(raw_mode or "").strip().lower().replace("-", "_")
    if not s:
        return GLOBAL_SUMMARY_MODE_DEFAULT
    if s in {"ready_first", "ready", "cache", "passive"}:
        return GLOBAL_SUMMARY_MODE_READY_FIRST
    if s in {"sync", "fresh", "force_refresh"}:
        return GLOBAL_SUMMARY_MODE_SYNC
    raise HTTPException(status_code=400, detail="mode must be ready_first or sync")


def _to_text(value: Any) -> Optional[str]:
    if value is None:
        return None
    s = str(value).strip()
    return s or None


def _parse_iso_utc(value: Any) -> Optional[datetime]:
    s = str(value or "").strip()
    if not s:
        return None
    try:
        if s.endswith("Z"):
            s = s[:-1] + "+00:00"
        dt = datetime.fromisoformat(s)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)
    except Exception:
        return None


def _ready_summary_is_stale(updated_at: Optional[str]) -> bool:
    updated_dt = _parse_iso_utc(updated_at)
    if updated_dt is None:
        return True
    age_seconds = (datetime.now(timezone.utc) - updated_dt).total_seconds()
    return age_seconds >= max(1.0, float(GLOBAL_SUMMARY_READY_STALE_AFTER_SECONDS or 0.0))


async def _enqueue_global_summary_ready_refresh(
    *,
    activity_date: str,
    timezone_name: str,
    reason: str,
) -> None:
    if enqueue_global_summary_refresh is None:
        return

    throttle_key = build_cache_key(
        f"global_summary:enqueue:{activity_date}",
        {
            "timezone": str(timezone_name or GLOBAL_SUMMARY_DB_TZ),
            "reason": str(reason or "ready_first"),
        },
    )

    async def _producer() -> Dict[str, Any]:
        try:
            ok = await enqueue_global_summary_refresh(
                trigger="api_global_summary_ready_first",
                activity_date=activity_date,
                timezone_name=timezone_name,
                debounce=True,
                extra_payload={
                    "source": "api_global_summary",
                    "mode": "ready_first",
                    "reason": str(reason or "ready_first"),
                },
            )
            return {"ok": bool(ok)}
        except Exception as exc:  # pragma: no cover - best effort
            logger.warning(
                "global summary refresh enqueue failed: activity_date=%s timezone=%s reason=%s err=%s",
                activity_date,
                timezone_name,
                reason,
                exc,
            )
            return {"ok": False}

    try:
        await get_or_compute(
            throttle_key,
            GLOBAL_SUMMARY_READY_REFRESH_ENQUEUE_THROTTLE_SECONDS,
            _producer,
        )
    except Exception as exc:  # pragma: no cover - best effort
        logger.warning(
            "global summary refresh enqueue throttle failed: activity_date=%s timezone=%s reason=%s err=%s",
            activity_date,
            timezone_name,
            reason,
            exc,
        )


def _schedule_global_summary_ready_refresh(
    *,
    activity_date: str,
    timezone_name: str,
    reason: str,
) -> None:
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        return
    loop.create_task(
        _enqueue_global_summary_ready_refresh(
            activity_date=activity_date,
            timezone_name=timezone_name,
            reason=reason,
        )
    )


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


async def _fetch_current_day_synchronous_response(
    *,
    activity_date: str,
    timezone_name: str,
    response_tz: str,
) -> Optional[GlobalSummaryResponse]:
    """Refresh the current JST day synchronously via legacy surfaces.

    Home re-fetches `/global_summary` immediately after an emotion submit. If we return READY-first
    for the current day, the response can lag behind the just-saved input even when the artifact is
    only a few seconds old. To keep the existing UI contract, the current day must prefer a fresh
    synchronous read.
    """

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
            "current-day synchronous global summary refresh failed: activity_date=%s timezone=%s err=%s",
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


async def get_global_summary_payload(
    date: Optional[str] = None,
    tz: Optional[str] = GLOBAL_SUMMARY_RESPONSE_TZ,
    mode: Optional[str] = None,
) -> Dict[str, Any]:
    db_tz, response_tz = _normalize_global_summary_tz(tz)
    activity_date = _resolve_global_summary_date(date)
    mode_key = _normalize_global_summary_mode(mode)
    ttl_seconds = GLOBAL_SUMMARY_TODAY_CACHE_TTL_SECONDS if _is_today_jst(activity_date) else GLOBAL_SUMMARY_HISTORY_CACHE_TTL_SECONDS
    cache_key = build_cache_key(
        f"global_summary:{activity_date}:{response_tz}",
        {
            "db_tz": db_tz,
            "mode": mode_key,
            "ready_reader_id": id(fetch_latest_ready_global_summary),
            "fallback_reader_id": id(generate_global_summary_payload),
            "pytest_current_test": os.getenv("PYTEST_CURRENT_TEST") or None,
        },
    )

    async def _build_payload() -> Dict[str, Any]:
        try:
            is_today = _is_today_jst(activity_date)

            if is_today:
                if mode_key == GLOBAL_SUMMARY_MODE_READY_FIRST:
                    ready_response = await _fetch_ready_summary_response(
                        activity_date=activity_date,
                        timezone_name=db_tz,
                        response_tz=response_tz,
                    )
                    if ready_response is not None:
                        if _ready_summary_is_stale(ready_response.updated_at):
                            _schedule_global_summary_ready_refresh(
                                activity_date=activity_date,
                                timezone_name=db_tz,
                                reason="current_day_ready_first_stale_ready_used",
                            )
                        return jsonable_encoder(ready_response)

                    fallback_response = await _fetch_migration_fallback_response(
                        activity_date=activity_date,
                        timezone_name=db_tz,
                        response_tz=response_tz,
                    )
                    if fallback_response is not None:
                        _schedule_global_summary_ready_refresh(
                            activity_date=activity_date,
                            timezone_name=db_tz,
                            reason="current_day_ready_first_legacy_fallback",
                        )
                        return jsonable_encoder(fallback_response)

                    _schedule_global_summary_ready_refresh(
                        activity_date=activity_date,
                        timezone_name=db_tz,
                        reason="current_day_ready_first_zero_used",
                    )
                    return jsonable_encoder(_global_summary_zero(activity_date=activity_date, response_tz=response_tz))

                sync_response = await _fetch_current_day_synchronous_response(
                    activity_date=activity_date,
                    timezone_name=db_tz,
                    response_tz=response_tz,
                )
                if sync_response is not None:
                    _schedule_global_summary_ready_refresh(
                        activity_date=activity_date,
                        timezone_name=db_tz,
                        reason="current_day_sync_used",
                    )
                    return jsonable_encoder(sync_response)

                ready_response = await _fetch_ready_summary_response(
                    activity_date=activity_date,
                    timezone_name=db_tz,
                    response_tz=response_tz,
                )
                if ready_response is not None:
                    _schedule_global_summary_ready_refresh(
                        activity_date=activity_date,
                        timezone_name=db_tz,
                        reason="current_day_sync_failed_ready_fallback",
                    )
                    return jsonable_encoder(ready_response)

                fallback_response = await _fetch_migration_fallback_response(
                    activity_date=activity_date,
                    timezone_name=db_tz,
                    response_tz=response_tz,
                )
                if fallback_response is not None:
                    _schedule_global_summary_ready_refresh(
                        activity_date=activity_date,
                        timezone_name=db_tz,
                        reason="current_day_sync_failed_legacy_fallback",
                    )
                    return jsonable_encoder(fallback_response)

                _schedule_global_summary_ready_refresh(
                    activity_date=activity_date,
                    timezone_name=db_tz,
                    reason="current_day_zero_used",
                )
                return jsonable_encoder(_global_summary_zero(activity_date=activity_date, response_tz=response_tz))

            ready_response = await _fetch_ready_summary_response(
                activity_date=activity_date,
                timezone_name=db_tz,
                response_tz=response_tz,
            )
            if ready_response is not None:
                return jsonable_encoder(ready_response)

            fallback_response = await _fetch_migration_fallback_response(
                activity_date=activity_date,
                timezone_name=db_tz,
                response_tz=response_tz,
            )
            if fallback_response is not None:
                return jsonable_encoder(fallback_response)

            return jsonable_encoder(_global_summary_zero(activity_date=activity_date, response_tz=response_tz))
        except HTTPException:
            raise
        except Exception as exc:
            logger.warning("global_summary failed: %s", exc)
            return jsonable_encoder(_global_summary_zero(activity_date=activity_date, response_tz=response_tz))

    return await get_or_compute(cache_key, ttl_seconds, _build_payload)


def register_global_summary_routes(app: FastAPI) -> None:
    @app.get("/global_summary", response_model=GlobalSummaryResponse)
    async def global_summary(
        date: Optional[str] = Query(default=None, description="YYYY-MM-DD. Defaults to today in JST."),
        tz: Optional[str] = Query(default=GLOBAL_SUMMARY_RESPONSE_TZ, description="Currently fixed to +09:00 / Asia/Tokyo."),
        mode: Optional[str] = Query(default=None, description="Set ready_first to skip the current-day synchronous refresh and prefer READY artifacts."),
    ) -> GlobalSummaryResponse:
        payload = await get_global_summary_payload(date=date, tz=tz, mode=mode)
        return GlobalSummaryResponse(**payload)


__all__ = [
    "GlobalSummaryResponse",
    "get_global_summary_payload",
    "register_global_summary_routes",
]
