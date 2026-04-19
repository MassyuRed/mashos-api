from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from fastapi import FastAPI, Header, HTTPException, Path, Query
from pydantic import BaseModel, Field

from api_account_visibility import _require_user_id
from access_policy.viewer_access_policy import (
    apply_myprofile_report_access_for_viewer,
    build_report_history_retention,
    resolve_report_view_context,
    resolve_viewer_tier_str as _resolve_viewer_tier_str_from_policy,
)
from supabase_client import sb_get

logger = logging.getLogger("myprofile_reports_read_api")

MYPROFILE_HISTORY_PROJECTION_SELECT = (
    "id,report_type,title,period_start,period_end,generated_at,updated_at,"
    "has_visible_content:content_json->visibility->>has_visible_content,"
    "archive_eligible:content_json->history->>archive_eligible"
)
MYPROFILE_HISTORY_FALLBACK_SELECT = (
    "id,report_type,title,period_start,period_end,generated_at,updated_at,content_text,content_json"
)


class MyProfileReportHistoryItem(BaseModel):
    id: str
    report_type: str
    title: Optional[str] = None
    period_start: Optional[str] = None
    period_end: Optional[str] = None
    generated_at: Optional[str] = None
    updated_at: Optional[str] = None


class MyProfileReportHistoryResponse(BaseModel):
    status: str = "ok"
    items: List[MyProfileReportHistoryItem] = Field(default_factory=list)
    limit: int = 60
    offset: int = 0
    has_more: bool = False
    next_offset: Optional[int] = None
    subscription_tier: str = "free"


class MyProfileReportDetailItem(MyProfileReportHistoryItem):
    content_text: Optional[str] = None
    content_json: Dict[str, Any] = Field(default_factory=dict)


class MyProfileReportDetailResponse(BaseModel):
    status: str = "ok"
    item: MyProfileReportDetailItem


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


async def _resolve_subscription_tier(user_id: str) -> str:
    return await _resolve_viewer_tier_str_from_policy(user_id)


async def _fetch_history_rows(
    user_id: str,
    report_type: str,
    limit: int,
    offset: int,
    *,
    tier_str: str,
    now_utc: datetime,
) -> Tuple[List[Dict[str, Any]], bool, Optional[int]]:
    lim = max(1, min(int(limit or 60), 200))
    off = max(0, int(offset or 0))
    needed = off + lim + 1
    raw_offset = 0
    raw_page_size = max(50, min(200, lim * 2))
    filtered_rows: List[Dict[str, Any]] = []

    retention = build_report_history_retention(tier_str, now_utc=now_utc)
    gte_iso = str(retention.get("gte_iso") or "").strip()
    lt_iso = str(retention.get("lt_iso") or "").strip()

    def _base_params(select_clause: str) -> Dict[str, str]:
        params = {
            "select": select_clause,
            "user_id": f"eq.{user_id}",
            "report_type": f"eq.{report_type}",
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
        return params

    while len(filtered_rows) < needed:
        resp = await sb_get(
            "/rest/v1/myprofile_reports",
            params=_base_params(MYPROFILE_HISTORY_PROJECTION_SELECT),
            timeout=8.0,
        )
        chunk = _pick_rows(resp) if resp.status_code < 300 else []
        projection_ok = resp.status_code < 300 and (
            not chunk
            or any(
                any(key in row for key in ("has_visible_content", "archive_eligible"))
                for row in chunk[:3]
            )
        )

        if not projection_ok:
            if resp.status_code >= 300:
                logger.warning(
                    "myprofile_reports history projection select failed: %s %s",
                    resp.status_code,
                    (resp.text or "")[:800],
                )
            else:
                logger.warning(
                    "myprofile_reports history projection missing expected fields; falling back to legacy body select"
                )
            resp = await sb_get(
                "/rest/v1/myprofile_reports",
                params=_base_params(MYPROFILE_HISTORY_FALLBACK_SELECT),
                timeout=8.0,
            )
            if resp.status_code >= 300:
                logger.warning(
                    "myprofile_reports history legacy select failed: %s %s",
                    resp.status_code,
                    (resp.text or "")[:800],
                )
                raise HTTPException(status_code=502, detail="Failed to load self-structure report history")
            chunk = _pick_rows(resp)

        if not chunk:
            break
        raw_offset += len(chunk)

        for row in chunk:
            published_row = apply_myprofile_report_access_for_viewer(
                row,
                tier_str=tier_str,
                requested_report_type=report_type,
                now_utc=now_utc,
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
    return page, has_more, next_offset


async def _fetch_detail_row(
    user_id: str,
    report_id: str,
    *,
    tier_str: str,
    now_utc: datetime,
) -> Dict[str, Any]:
    resp = await sb_get(
        "/rest/v1/myprofile_reports",
        params={
            "select": "id,report_type,title,period_start,period_end,content_text,content_json,generated_at,updated_at",
            "user_id": f"eq.{user_id}",
            "id": f"eq.{report_id}",
            "limit": "1",
        },
        timeout=8.0,
    )
    if resp.status_code >= 300:
        logger.warning("myprofile_reports detail select failed: %s %s", resp.status_code, (resp.text or "")[:800])
        raise HTTPException(status_code=502, detail="Failed to load self-structure report")
    rows = _pick_rows(resp)
    if not rows:
        raise HTTPException(status_code=404, detail="Self-structure report not found")
    published_row = apply_myprofile_report_access_for_viewer(rows[0], tier_str=tier_str, now_utc=now_utc)
    if not published_row:
        raise HTTPException(status_code=404, detail="Self-structure report not found")
    return published_row


def register_myprofile_report_read_routes(app: FastAPI) -> None:
    @app.get("/myprofile/reports/history", response_model=MyProfileReportHistoryResponse)
    async def get_myprofile_report_history(
        report_type: str = Query(default="monthly"),
        limit: int = Query(default=60, ge=1, le=200),
        offset: int = Query(default=0, ge=0),
        authorization: Optional[str] = Header(default=None, alias="Authorization"),
    ) -> MyProfileReportHistoryResponse:
        me = await _require_user_id(authorization)
        tier_str = await _resolve_subscription_tier(me)
        now_utc = datetime.now(timezone.utc)
        rows, has_more, next_offset = await _fetch_history_rows(
            me,
            str(report_type or "monthly"),
            int(limit or 60),
            int(offset or 0),
            tier_str=tier_str,
            now_utc=now_utc,
        )
        items = [MyProfileReportHistoryItem(**row) for row in rows]
        return MyProfileReportHistoryResponse(
            items=items,
            limit=int(limit or 60),
            offset=int(offset or 0),
            has_more=bool(has_more),
            next_offset=next_offset,
            subscription_tier=tier_str,
        )

    @app.get("/myprofile/reports/{report_id}", response_model=MyProfileReportDetailResponse)
    async def get_myprofile_report_detail(
        report_id: str = Path(..., min_length=1),
        authorization: Optional[str] = Header(default=None, alias="Authorization"),
    ) -> MyProfileReportDetailResponse:
        me = await _require_user_id(authorization)
        tier_str = await _resolve_subscription_tier(me)
        now_utc = datetime.now(timezone.utc)
        row = await _fetch_detail_row(me, str(report_id or "").strip(), tier_str=tier_str, now_utc=now_utc)
        item = MyProfileReportDetailItem(
            id=str(row.get("id") or report_id),
            report_type=str(row.get("report_type") or ""),
            title=row.get("title"),
            period_start=row.get("period_start"),
            period_end=row.get("period_end"),
            generated_at=row.get("generated_at"),
            updated_at=row.get("updated_at"),
            content_text=row.get("content_text"),
            content_json=_normalize_content_json(row.get("content_json")),
        )
        return MyProfileReportDetailResponse(item=item)
