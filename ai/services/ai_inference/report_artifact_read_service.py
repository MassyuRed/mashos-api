from __future__ import annotations

import json
import logging
import os
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
from emlis_context_anchor_service import sanitize_content_json_for_public_read

logger = logging.getLogger("report_artifact_read_service")

ANALYSIS_REPORTS_READ_TABLE = (
    os.getenv("COCOLON_ANALYSIS_REPORTS_READ_TABLE")
    or os.getenv("ANALYSIS_REPORTS_READ_TABLE")
    or os.getenv("COCOLON_MYWEB_REPORTS_READ_TABLE")
    or os.getenv("MYWEB_REPORTS_READ_TABLE")
    or "analysis_reports"
).strip() or "analysis_reports"
SELF_STRUCTURE_REPORTS_READ_TABLE = (
    os.getenv("COCOLON_SELF_STRUCTURE_REPORTS_READ_TABLE")
    or os.getenv("SELF_STRUCTURE_REPORTS_READ_TABLE")
    or os.getenv("COCOLON_MYPROFILE_REPORTS_READ_TABLE")
    or os.getenv("MYPROFILE_REPORTS_READ_TABLE")
    or "self_structure_reports"
).strip() or "self_structure_reports"

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
        table=SELF_STRUCTURE_REPORTS_READ_TABLE,
        access_fn=apply_myprofile_report_access_for_viewer,
        not_found_detail="Self-structure report not found",
    ),
    "myweb": ReportArtifactFamilyConfig(
        table=ANALYSIS_REPORTS_READ_TABLE,
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
        return sanitize_content_json_for_public_read(raw)
    if isinstance(raw, str):
        try:
            data = json.loads(raw)
            return sanitize_content_json_for_public_read(data) if isinstance(data, dict) else {}
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
    from analysis_observed_service import observed_enabled, read_saved
    observed = family == 'self_structure' and observed_enabled()
    observed_rows = []
    if observed:
        if off > 10000:
            raise HTTPException(400, 'analysis_page_invalid')
        while len(observed_rows) < needed:
            take = min(200, needed-len(observed_rows))
            result = await read_saved(me, report_type=report_type, history=True,
                limit=take, offset=len(observed_rows))
            tier_str = result['subscription_tier']
            observed_rows.extend(result['items'])
            if len(result['items']) < take:
                break
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
            "order": "period_end.desc,generated_at.desc,updated_at.desc,id.desc",
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
            if observed and not _legacy_mode_allowed(row, tier_str):
                continue
            published_row = config.access_fn(
                row,
                context=None if observed else context,
                tier_str=tier_str,
                requested_report_type=str(report_type or "monthly"),
                now_utc=now,
            )
            if published_row:
                filtered_rows.append(published_row)
                if len(filtered_rows) >= needed:
                    break

        if len(chunk) < raw_page_size:
            break

    if observed:
        filtered_rows = sorted(filtered_rows + observed_rows, key=_history_sort_key, reverse=True)
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

    from analysis_observed_service import observed_enabled, read_saved
    observed = family == 'self_structure' and observed_enabled()
    observed_tier = None
    if observed:
        result = await read_saved(me, report_id=rid, history=True, limit=1)
        observed_tier = result['subscription_tier']
        if result['items']:
            return {'status': 'ok', 'item': result['items'][0]}
        if result['matched']:
            raise HTTPException(404, 'analysis_report_unavailable')

    tier_str = observed_tier or await _resolve_subscription_tier(me)
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
    if observed and not _legacy_mode_allowed(rows[0], tier_str):
        raise HTTPException(404, config.not_found_detail)

    published_row = config.access_fn(rows[0], context=None if observed else context,
                                   tier_str=tier_str, now_utc=now)
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


def _legacy_mode_allowed(row, tier):
    from api_self_structure import _extract_saved_report_mode
    mode = _extract_saved_report_mode(row) or 'standard'
    return tier == 'premium' or (tier == 'plus' and mode in {'light', 'standard'})


def _history_sort_key(row):
    def instant(key):
        try:
            dt = datetime.fromisoformat(str(row.get(key) or '').replace('Z', '+00:00'))
            return dt.replace(tzinfo=timezone.utc) if dt.tzinfo is None else dt.astimezone(timezone.utc)
        except ValueError:
            return datetime.min.replace(tzinfo=timezone.utc)
    return (instant('period_end'), instant('generated_at'), instant('updated_at'), str(row.get('id') or ''))
