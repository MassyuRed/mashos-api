from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from typing import Any, Callable, Dict, List, Optional, Tuple

from fastapi import HTTPException

from access_policy.viewer_access_policy import (
    apply_myprofile_report_access_for_viewer,
    apply_myweb_report_access_for_viewer,
    build_report_history_retention,
    resolve_report_view_context,
    resolve_viewer_tier_str as _resolve_viewer_tier_str_from_policy,
)
from supabase_client import sb_get

logger = logging.getLogger("report_artifact_read_service")

REPORT_FULL_SELECT = (
    "id,report_type,title,period_start,period_end,content_text,content_json,generated_at,updated_at"
)
REPORT_HISTORY_SELECT = (
    "id,report_type,title,period_start,period_end,generated_at,updated_at,content_text,content_json"
)


class ReportArtifactFamilyConfig:
    def __init__(self, *, table: str, access_fn: Callable[..., Optional[Dict[str, Any]]], not_found_detail: str):
        self.table = table
        self.access_fn = access_fn
        self.not_found_detail = not_found_detail


FAMILY_CONFIGS: Dict[str, ReportArtifactFamilyConfig] = {
    "self_structure": ReportArtifactFamilyConfig(
        table="myprofile_reports",
        access_fn=apply_myprofile_report_access_for_viewer,
        not_found_detail="Self-structure report not found",
    ),
    "myweb": ReportArtifactFamilyConfig(
        table="myweb_reports",
        access_fn=apply_myweb_report_access_for_viewer,
        not_found_detail="MyWeb report not found",
    ),
}


def _get_family_config(family: str) -> ReportArtifactFamilyConfig:
    key = str(family or "").strip().lower()
    config = FAMILY_CONFIGS.get(key)
    if config is None:
        raise HTTPException(status_code=400, detail=f"Unsupported report artifact family: {family}")
    return config


async def _resolve_subscription_tier(user_id: str) -> str:
    return await _resolve_viewer_tier_str_from_policy(user_id)


def _pick_rows(resp) -> List[Dict[str, Any]]:
    try:
        data = resp.json()
    except Exception:
        return []
    if isinstance(data, list):
        return [row for row in data if isinstance(row, dict)]
    if isinstance(data, dict):
        return [data]
    return []


def _normalize_content_json(raw: Any) -> Dict[str, Any]:
    if isinstance(raw, dict):
        return raw
    if isinstance(raw, str):
        try:
            data = json.loads(raw)
            return data if isinstance(data, dict) else {}
        except Exception:
            return {}
    return {}


async def list_history(
    *,
    user_id: str,
    family: str,
    report_type: str,
    limit: int,
    offset: int,
    now_utc: Optional[datetime] = None,
) -> Dict[str, Any]:
    config = _get_family_config(family)
    me = str(user_id or "").strip()
    if not me:
        raise HTTPException(status_code=401, detail="Invalid user")

    tier_str = await _resolve_subscription_tier(me)
    now = now_utc or datetime.now(timezone.utc)
    context = await resolve_report_view_context(me, now_utc=now)

    lim = max(1, min(int(limit or 60), 200))
    off = max(0, int(offset or 0))
    needed = off + lim + 1
    raw_offset = 0
    raw_page_size = max(50, min(200, lim * 2))
    filtered_rows: List[Dict[str, Any]] = []

    retention = build_report_history_retention(tier_str, now_utc=now)
    gte_iso = str(retention.get("gte_iso") or "").strip()
    lt_iso = str(retention.get("lt_iso") or "").strip()

    while len(filtered_rows) < needed:
        params: Dict[str, str] = {
            "select": REPORT_HISTORY_SELECT,
            "user_id": f"eq.{me}",
            "report_type": f"eq.{str(report_type or 'monthly')}",
            "order": "period_end.desc,generated_at.desc,updated_at.desc",
            "limit": str(raw_page_size),
            "offset": str(raw_offset),
        }
        if gte_iso and lt_iso:
            params["and"] = f"(period_end.gte.{gte_iso},period_end.lt.{lt_iso})"
        elif gte_iso:
            params["period_end"] = f"gte.{gte_iso}"
        elif lt_iso:
            params["period_end"] = f"lt.{lt_iso}"

        resp = await sb_get(
            f"/rest/v1/{config.table}",
            params=params,
            timeout=8.0,
        )
        if resp.status_code >= 300:
            logger.warning(
                "%s history select failed: %s %s",
                config.table,
                resp.status_code,
                (resp.text or "")[:800],
            )
            raise HTTPException(status_code=502, detail=f"Failed to load {family} report history")

        chunk = _pick_rows(resp)
        if not chunk:
            break
        raw_offset += len(chunk)

        for row in chunk:
            published_row = config.access_fn(
                row,
                context=context,
                requested_report_type=str(report_type or "monthly"),
                now_utc=now,
            )
            if published_row:
                filtered_rows.append(published_row)
                if len(filtered_rows) >= needed:
                    break

        if len(chunk) < raw_page_size:
            break

    page = filtered_rows[off : off + lim]
    has_more = len(filtered_rows) > (off + lim)
    next_offset = (off + lim) if has_more else None
    items = [
        {
            "id": str(row.get("id") or ""),
            "report_type": str(row.get("report_type") or ""),
            "title": row.get("title"),
            "period_start": row.get("period_start"),
            "period_end": row.get("period_end"),
            "generated_at": row.get("generated_at"),
            "updated_at": row.get("updated_at"),
        }
        for row in page
    ]
    return {
        "status": "ok",
        "items": items,
        "limit": lim,
        "offset": off,
        "has_more": bool(has_more),
        "next_offset": next_offset,
        "subscription_tier": tier_str,
    }


async def get_detail(
    *,
    user_id: str,
    family: str,
    report_id: str,
    now_utc: Optional[datetime] = None,
) -> Dict[str, Any]:
    config = _get_family_config(family)
    me = str(user_id or "").strip()
    rid = str(report_id or "").strip()
    if not me:
        raise HTTPException(status_code=401, detail="Invalid user")
    if not rid:
        raise HTTPException(status_code=400, detail="report_id is required")

    tier_str = await _resolve_subscription_tier(me)
    now = now_utc or datetime.now(timezone.utc)
    context = await resolve_report_view_context(me, now_utc=now)

    resp = await sb_get(
        f"/rest/v1/{config.table}",
        params={
            "select": REPORT_FULL_SELECT,
            "user_id": f"eq.{me}",
            "id": f"eq.{rid}",
            "limit": "1",
        },
        timeout=8.0,
    )
    if resp.status_code >= 300:
        logger.warning(
            "%s detail select failed: %s %s",
            config.table,
            resp.status_code,
            (resp.text or "")[:800],
        )
        raise HTTPException(status_code=502, detail=f"Failed to load {family} report")

    rows = _pick_rows(resp)
    if not rows:
        raise HTTPException(status_code=404, detail=config.not_found_detail)

    published_row = config.access_fn(rows[0], context=context, now_utc=now)
    if not published_row:
        raise HTTPException(status_code=404, detail=config.not_found_detail)

    item = {
        "id": str(published_row.get("id") or rid),
        "report_type": str(published_row.get("report_type") or ""),
        "title": published_row.get("title"),
        "period_start": published_row.get("period_start"),
        "period_end": published_row.get("period_end"),
        "generated_at": published_row.get("generated_at"),
        "updated_at": published_row.get("updated_at"),
        "content_text": published_row.get("content_text"),
        "content_json": _normalize_content_json(published_row.get("content_json")),
    }
    return {
        "status": "ok",
        "item": item,
    }
