# -*- coding: utf-8 -*-
"""Global Summary generation kernel for ASTOR (Step 1).

Purpose
-------
既存の `daily_global_activity` / `refresh_daily_global_activity` をそのまま活かしつつ、
ASTOR worker から machine-readable な app-wide daily summary payload を生成する。

Step 1 policy
-------------
- 計算 kernel は既存 SQL/RPC をそのまま利用する
- 本モジュールは「legacy surface 実行」と「summary payload 正規化」だけを担当する
- DRAFT 保存・READY 昇格は `astor_global_summary_store.py` 側で担当する
- GET `/global_summary` の read 差し替えは Step 4 で行う

Design notes
------------
- canonical payload の totals key は `reflection_views` を採用する
- legacy row の `reflection_view_count` / `reflection_count` は normalize 時に吸収する
- worker refresh では refresh RPC を優先し、必要なら table read へ fallback できる
"""

from __future__ import annotations

import logging
import os
from typing import Any, Dict, Iterable, Optional

from supabase_client import ensure_supabase_config, sb_get, sb_post_rpc
from astor_global_summary_store import (
    GLOBAL_SUMMARY_TIMEZONE,
    GLOBAL_SUMMARY_TOTAL_KEYS,
    canonical_global_summary_activity_date,
    canonical_global_summary_timezone,
    normalize_global_summary_payload,
)

logger = logging.getLogger("astor_global_summary_kernel")


LEGACY_GLOBAL_SUMMARY_TABLE = (
    os.getenv("GLOBAL_SUMMARY_TABLE") or "daily_global_activity"
).strip() or "daily_global_activity"

LEGACY_GLOBAL_SUMMARY_REFRESH_RPC = (
    os.getenv("GLOBAL_SUMMARY_REFRESH_RPC") or "refresh_daily_global_activity"
).strip() or "refresh_daily_global_activity"

SUPPORTED_GLOBAL_SUMMARY_TOTAL_KEYS = tuple(GLOBAL_SUMMARY_TOTAL_KEYS or ())


def _extract_first_dict(data: Any) -> Dict[str, Any]:
    if isinstance(data, list) and data:
        first = data[0]
        if isinstance(first, dict):
            return dict(first)
        return {}
    if isinstance(data, dict):
        return dict(data)
    return {}


async def _fetch_legacy_global_summary_row(
    activity_date: str,
    *,
    timezone_name: str,
) -> Optional[Dict[str, Any]]:
    ensure_supabase_config()
    resp = await sb_get(
        f"/rest/v1/{LEGACY_GLOBAL_SUMMARY_TABLE}",
        params={
            "select": "activity_date,tz,emotion_users,reflection_view_count,echo_count,discovery_count,updated_at",
            "activity_date": f"eq.{activity_date}",
            "tz": f"eq.{timezone_name}",
            "limit": "1",
        },
        timeout=8.0,
    )
    if resp.status_code >= 300:
        logger.warning(
            "legacy global summary table read failed: table=%s activity_date=%s timezone=%s status=%s body=%s",
            LEGACY_GLOBAL_SUMMARY_TABLE,
            activity_date,
            timezone_name,
            resp.status_code,
            (resp.text or "")[:800],
        )
        return None

    try:
        rows = resp.json()
    except Exception as exc:
        logger.warning(
            "legacy global summary table returned non-json: table=%s activity_date=%s timezone=%s err=%s",
            LEGACY_GLOBAL_SUMMARY_TABLE,
            activity_date,
            timezone_name,
            exc,
        )
        return None

    row = _extract_first_dict(rows)
    return row or None


async def _refresh_legacy_global_summary_row(
    activity_date: str,
    *,
    timezone_name: str,
) -> Optional[Dict[str, Any]]:
    ensure_supabase_config()
    try:
        resp = await sb_post_rpc(
            LEGACY_GLOBAL_SUMMARY_REFRESH_RPC,
            {
                "p_activity_date": activity_date,
                "p_tz": timezone_name,
            },
            timeout=8.0,
        )
    except Exception as exc:
        logger.warning(
            "legacy global summary refresh rpc failed (network): fn=%s activity_date=%s timezone=%s err=%s",
            LEGACY_GLOBAL_SUMMARY_REFRESH_RPC,
            activity_date,
            timezone_name,
            exc,
        )
        return None

    if resp.status_code >= 300:
        logger.warning(
            "legacy global summary refresh rpc failed: fn=%s activity_date=%s timezone=%s status=%s body=%s",
            LEGACY_GLOBAL_SUMMARY_REFRESH_RPC,
            activity_date,
            timezone_name,
            resp.status_code,
            (resp.text or "")[:800],
        )
        return None

    try:
        data = resp.json()
    except Exception as exc:
        logger.warning(
            "legacy global summary refresh rpc returned non-json: fn=%s activity_date=%s timezone=%s err=%s",
            LEGACY_GLOBAL_SUMMARY_REFRESH_RPC,
            activity_date,
            timezone_name,
            exc,
        )
        return None

    row = _extract_first_dict(data)
    return row or None


def _build_summary_payload(
    activity_date: str,
    *,
    timezone_name: str,
    row: Optional[Dict[str, Any]],
) -> Dict[str, Any]:
    base = row if isinstance(row, dict) else {}
    raw_payload = {
        "version": "global_summary.v1",
        "activity_date": activity_date,
        "timezone": timezone_name,
        "generated_at": base.get("updated_at"),
        "totals": {
            "emotion_users": base.get("emotion_users"),
            "reflection_views": base.get("reflection_views")
            if base.get("reflection_views") is not None
            else base.get("reflection_view_count"),
            "echo_count": base.get("echo_count"),
            "discovery_count": base.get("discovery_count"),
        },
    }
    return normalize_global_summary_payload(
        activity_date,
        raw_payload,
        timezone_name=timezone_name,
    )


async def generate_global_summary_payload(
    activity_date: Any,
    *,
    timezone_name: Optional[str] = None,
    prefer_refresh: bool = True,
    fallback_to_table: bool = True,
    allow_empty: bool = False,
) -> Dict[str, Any]:
    """Generate a normalized global summary payload for one activity date.

    Parameters
    ----------
    activity_date:
        Target aggregate day (`YYYY-MM-DD`).
    timezone_name:
        Aggregate timezone. Defaults to `Asia/Tokyo`.
    prefer_refresh:
        When True, call the legacy refresh RPC first.
    fallback_to_table:
        When True, try the legacy daily table if the preferred source returns nothing.
    allow_empty:
        When True, return a zero-valued canonical payload instead of raising when both
        legacy surfaces are unavailable.
    """
    act_date = canonical_global_summary_activity_date(activity_date)
    if not act_date:
        raise ValueError("activity_date is required")
    tz_name = canonical_global_summary_timezone(timezone_name or GLOBAL_SUMMARY_TIMEZONE)

    row: Optional[Dict[str, Any]] = None
    if prefer_refresh:
        row = await _refresh_legacy_global_summary_row(act_date, timezone_name=tz_name)
        if row is None and fallback_to_table:
            row = await _fetch_legacy_global_summary_row(act_date, timezone_name=tz_name)
    else:
        row = await _fetch_legacy_global_summary_row(act_date, timezone_name=tz_name)
        if row is None and fallback_to_table:
            row = await _refresh_legacy_global_summary_row(act_date, timezone_name=tz_name)

    if row is None and not allow_empty:
        raise RuntimeError(
            f"global summary source unavailable: activity_date={act_date} timezone={tz_name}"
        )

    return _build_summary_payload(
        act_date,
        timezone_name=tz_name,
        row=row,
    )


async def generate_multiple_global_summary_payloads(
    activity_dates: Iterable[Any],
    *,
    timezone_name: Optional[str] = None,
    prefer_refresh: bool = True,
    fallback_to_table: bool = True,
    allow_empty: bool = False,
) -> Dict[str, Dict[str, Any]]:
    """Generate normalized global summary payloads for multiple days."""
    out: Dict[str, Dict[str, Any]] = {}
    seen = set()
    for raw_date in activity_dates or []:
        act_date = canonical_global_summary_activity_date(raw_date)
        if not act_date or act_date in seen:
            continue
        seen.add(act_date)
        out[act_date] = await generate_global_summary_payload(
            act_date,
            timezone_name=timezone_name,
            prefer_refresh=prefer_refresh,
            fallback_to_table=fallback_to_table,
            allow_empty=allow_empty,
        )
    return out


__all__ = [
    "LEGACY_GLOBAL_SUMMARY_TABLE",
    "LEGACY_GLOBAL_SUMMARY_REFRESH_RPC",
    "SUPPORTED_GLOBAL_SUMMARY_TOTAL_KEYS",
    "generate_global_summary_payload",
    "generate_multiple_global_summary_payloads",
]
