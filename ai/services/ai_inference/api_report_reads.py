
from __future__ import annotations

import asyncio
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, Header, HTTPException, Query
from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel, Field

from api_account_visibility import _require_user_id
from publish_governance import (
    decide_myprofile_report_publish,
    decide_myweb_report_publish,
    history_retention_bounds_for_query,
)
from supabase_client import sb_get, sb_post
from response_microcache import build_cache_key, get_or_compute, invalidate_prefix

try:
    from subscription import SubscriptionTier  # type: ignore
    from subscription_store import get_subscription_tier_for_user  # type: ignore
except Exception:  # pragma: no cover
    SubscriptionTier = None  # type: ignore
    get_subscription_tier_for_user = None  # type: ignore


logger = logging.getLogger("report_reads_api")
MYWEB_UNREAD_STATUS_CACHE_TTL_SECONDS = 8.0


class ReportReadStatusResponse(BaseModel):
    status: str = "ok"
    read_ids: List[str] = Field(default_factory=list)
    read_map: Dict[str, bool] = Field(default_factory=dict)


class ReportReadMarkBody(BaseModel):
    report_id: str = Field(..., min_length=1)
    report_table: Optional[str] = None
    report_scope: Optional[str] = None
    read_at: Optional[str] = None


class ReportReadMarkResponse(BaseModel):
    status: str = "ok"
    report_id: str
    marked: bool = True


class MyWebUnreadIdsByType(BaseModel):
    daily: List[str] = Field(default_factory=list)
    weekly: List[str] = Field(default_factory=list)
    monthly: List[str] = Field(default_factory=list)
    selfStructure: List[str] = Field(default_factory=list)


class MyWebUnreadFlags(BaseModel):
    daily: bool = False
    weekly: bool = False
    monthly: bool = False
    selfStructure: bool = False


class MyWebUnreadStatusResponse(BaseModel):
    status: str = "ok"
    viewer_tier: str = "free"
    ids_by_type: MyWebUnreadIdsByType
    read_ids: List[str] = Field(default_factory=list)
    unread_by_type: MyWebUnreadFlags


def _pick_rows(resp) -> List[Dict[str, Any]]:
    try:
        data = resp.json()
    except Exception:
        return []
    if isinstance(data, list):
        return [r for r in data if isinstance(r, dict)]
    if isinstance(data, dict):
        return [data]
    return []


def _to_iso_z(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")


def _normalize_report_ids(report_ids: Optional[List[str]]) -> List[str]:
    out: List[str] = []
    seen = set()
    for raw in report_ids or []:
        if raw is None:
            continue
        for piece in str(raw).split(","):
            rid = piece.strip()
            if not rid or rid in seen:
                continue
            seen.add(rid)
            out.append(rid)
    return out


async def _fetch_read_id_set(user_id: str, report_ids: List[str]) -> set[str]:
    ids = _normalize_report_ids(report_ids)
    if not user_id or not ids:
        return set()

    resp = await sb_get(
        "/rest/v1/report_reads",
        params={
            "select": "report_id",
            "user_id": f"eq.{user_id}",
            "report_id": f"in.({','.join(ids)})",
        },
        timeout=8.0,
    )
    if resp.status_code >= 300:
        logger.warning("report_reads select failed: %s %s", resp.status_code, resp.text[:800])
        raise HTTPException(status_code=502, detail="Failed to load report read status")

    rows = _pick_rows(resp)
    return {
        str(row.get("report_id") or "").strip()
        for row in rows
        if str(row.get("report_id") or "").strip()
    }


async def _mark_report_as_read(user_id: str, report_id: str, *, report_table: Optional[str] = None, report_scope: Optional[str] = None, read_at: Optional[str] = None) -> bool:
    rid = str(report_id or "").strip()
    if not user_id or not rid:
        return False

    now_iso = str(read_at or "").strip() or _to_iso_z(datetime.now(timezone.utc))
    scope = str(report_scope or "").strip() or None
    table = str(report_table or "").strip() or None

    candidates: List[Dict[str, Any]] = [
        {
            "row": {"user_id": user_id, "report_id": rid, "read_at": now_iso},
            "on_conflict": "user_id,report_id",
        },
    ]

    if table:
        candidates.append(
            {
                "row": {
                    "user_id": user_id,
                    "report_id": rid,
                    "report_table": table,
                    "read_at": now_iso,
                },
                "on_conflict": "user_id,report_table,report_id",
            }
        )

    if scope:
        candidates.extend(
            [
                {
                    "row": {
                        "user_id": user_id,
                        "report_id": rid,
                        "report_scope": scope,
                        "read_at": now_iso,
                    },
                    "on_conflict": "user_id,report_scope,report_id",
                },
                {
                    "row": {
                        "user_id": user_id,
                        "report_id": rid,
                        "scope": scope,
                        "read_at": now_iso,
                    },
                    "on_conflict": "user_id,scope,report_id",
                },
            ]
        )

    candidates.extend(
        [
            {"row": {"user_id": user_id, "report_id": rid}, "on_conflict": "user_id,report_id"},
        ]
    )

    if table:
        candidates.append(
            {
                "row": {"user_id": user_id, "report_id": rid, "report_table": table},
                "on_conflict": "user_id,report_table,report_id",
            }
        )

    if scope:
        candidates.extend(
            [
                {
                    "row": {"user_id": user_id, "report_id": rid, "report_scope": scope},
                    "on_conflict": "user_id,report_scope,report_id",
                },
                {
                    "row": {"user_id": user_id, "report_id": rid, "scope": scope},
                    "on_conflict": "user_id,scope,report_id",
                },
            ]
        )

    for candidate in candidates:
        try:
            resp = await sb_post(
                "/rest/v1/report_reads",
                json=candidate["row"],
                params={"on_conflict": str(candidate["on_conflict"])},
                prefer="resolution=merge-duplicates,return=minimal",
                timeout=8.0,
            )
            if resp.status_code in (200, 201):
                return True
        except Exception as exc:
            logger.warning("report_reads upsert candidate failed: %s", exc)

    return False



async def _resolve_viewer_tier(user_id: str) -> str:
    tier_str = "free"
    if user_id and SubscriptionTier is not None and get_subscription_tier_for_user is not None:
        try:
            tier_enum = await get_subscription_tier_for_user(user_id, default=SubscriptionTier.FREE)
            tier_str = tier_enum.value if hasattr(tier_enum, "value") else str(tier_enum)
        except Exception:
            tier_str = "free"
    return str(tier_str or "free")


async def _fetch_latest_ready_myweb_ids(user_id: str, report_type: str, *, tier_str: str, limit: int) -> List[str]:
    fetch_limit = max(limit * 4, 30)
    projection_select = (
        "id,report_type,period_start,period_end,"
        "publish_status:content_json->publish->>status,"
        "metrics_total_all:content_json->metrics->>totalAll,"
        "standard_total_all:content_json->standardReport->metrics->>totalAll"
    )
    fallback_select = "id,report_type,period_start,period_end,content_json"

    resp = await sb_get(
        "/rest/v1/myweb_reports",
        params={
            "select": projection_select,
            "user_id": f"eq.{user_id}",
            "report_type": f"eq.{report_type}",
            "order": "period_start.desc",
            "limit": str(fetch_limit),
        },
        timeout=8.0,
    )
    rows = _pick_rows(resp) if resp.status_code < 300 else []
    projection_ok = resp.status_code < 300 and (
        not rows or any(
            any(key in row for key in ("publish_status", "metrics_total_all", "standard_total_all"))
            for row in rows[:3]
        )
    )

    if not projection_ok:
        logger.warning(
            "myweb unread projection select fallback: status=%s body=%s",
            resp.status_code,
            (resp.text or "")[:800],
        )
        resp = await sb_get(
            "/rest/v1/myweb_reports",
            params={
                "select": fallback_select,
                "user_id": f"eq.{user_id}",
                "report_type": f"eq.{report_type}",
                "order": "period_start.desc",
                "limit": str(fetch_limit),
            },
            timeout=8.0,
        )
        if resp.status_code >= 300:
            logger.warning("myweb_reports select failed: %s %s", resp.status_code, resp.text[:800])
            raise HTTPException(status_code=502, detail="Failed to load MyWeb report status")
        rows = _pick_rows(resp)

    ids: List[str] = []
    for row in rows:
        published_row = decide_myweb_report_publish(
            row,
            tier_str=tier_str,
            requested_report_type=report_type,
        )
        if not published_row:
            continue

        rid = str(published_row.get("id") or "").strip()
        if not rid:
            continue
        ids.append(rid)
        if len(ids) >= limit:
            break

    return ids


async def _fetch_latest_self_structure_ids(user_id: str, *, tier_str: str, limit: int) -> List[str]:
    retention = history_retention_bounds_for_query(tier_str)
    gte_iso = str(retention.get("gte_iso") or "").strip()
    lt_iso = str(retention.get("lt_iso") or "").strip()

    def _params(select_clause: str) -> Dict[str, str]:
        params = {
            "select": select_clause,
            "user_id": f"eq.{user_id}",
            "report_type": "eq.monthly",
            "order": "period_end.desc,generated_at.desc,updated_at.desc",
            "limit": str(max(limit * 3, limit)),
        }
        if gte_iso and lt_iso:
            params["and"] = f"(period_end.gte.{gte_iso},period_end.lt.{lt_iso})"
        elif gte_iso:
            params["period_end"] = f"gte.{gte_iso}"
        elif lt_iso:
            params["period_end"] = f"lt.{lt_iso}"
        return params

    projection_select = (
        "id,report_type,period_end,"
        "has_visible_content:content_json->visibility->>has_visible_content,"
        "archive_eligible:content_json->history->>archive_eligible"
    )
    fallback_select = "id,report_type,period_end,content_text,content_json"

    resp = await sb_get(
        "/rest/v1/myprofile_reports",
        params=_params(projection_select),
        timeout=8.0,
    )
    rows = _pick_rows(resp) if resp.status_code < 300 else []
    projection_ok = resp.status_code < 300 and (
        not rows
        or any(any(key in row for key in ("has_visible_content", "archive_eligible")) for row in rows[:3])
    )
    if not projection_ok:
        logger.warning(
            "myprofile unread projection select fallback: status=%s body=%s",
            resp.status_code,
            (resp.text or "")[:800],
        )
        resp = await sb_get(
            "/rest/v1/myprofile_reports",
            params=_params(fallback_select),
            timeout=8.0,
        )
        if resp.status_code >= 300:
            logger.warning("myprofile_reports select failed: %s %s", resp.status_code, resp.text[:800])
            raise HTTPException(status_code=502, detail="Failed to load self-structure report status")
        rows = _pick_rows(resp)

    ids: List[str] = []
    for row in rows:
        published_row = decide_myprofile_report_publish(
            row,
            requested_report_type="monthly",
            tier_str=tier_str,
        )
        if not published_row:
            continue
        rid = str(published_row.get("id") or "").strip()
        if rid:
            ids.append(rid)
        if len(ids) >= limit:
            break
    return ids[:limit]


async def get_myweb_unread_status_payload_for_user(
    user_id: str,
    *,
    limit: int = 1,
    include_self_structure: bool = True,
) -> Dict[str, Any]:
    uid = str(user_id or "").strip()
    lim = max(1, min(int(limit or 1), 10))
    cache_key = build_cache_key(
        f"report_reads:myweb_unread:{uid}",
        {"limit": lim, "include_self_structure": bool(include_self_structure)},
    )

    async def _build_payload() -> Dict[str, Any]:
        tier_str = await _resolve_viewer_tier(uid)
        daily_task = _fetch_latest_ready_myweb_ids(uid, "daily", tier_str=tier_str, limit=lim)
        weekly_task = _fetch_latest_ready_myweb_ids(uid, "weekly", tier_str=tier_str, limit=lim)
        monthly_task = _fetch_latest_ready_myweb_ids(uid, "monthly", tier_str=tier_str, limit=lim)

        gather_tasks = [daily_task, weekly_task, monthly_task]
        include_self_structure_task = include_self_structure and tier_str in {"plus", "premium"}
        if include_self_structure_task:
            gather_tasks.append(
                _fetch_latest_self_structure_ids(uid, tier_str=tier_str, limit=lim)
            )

        gather_results = await asyncio.gather(*gather_tasks, return_exceptions=True)
        daily_ids, weekly_ids, monthly_ids = gather_results[:3]

        for result in (daily_ids, weekly_ids, monthly_ids):
            if isinstance(result, HTTPException):
                raise result
            if isinstance(result, Exception):
                raise result

        self_structure_ids: List[str] = []
        if include_self_structure_task:
            self_structure_result = gather_results[3]
            if isinstance(self_structure_result, HTTPException):
                raise self_structure_result
            if isinstance(self_structure_result, Exception):
                logger.warning("failed to load self-structure unread ids: %s", self_structure_result)
            else:
                self_structure_ids = self_structure_result

        ids_by_type = {
            "daily": daily_ids,
            "weekly": weekly_ids,
            "monthly": monthly_ids,
            "selfStructure": self_structure_ids,
        }

        all_ids: List[str] = []
        for key in ("daily", "weekly", "monthly", "selfStructure"):
            all_ids.extend(ids_by_type.get(key) or [])
        all_ids = list(dict.fromkeys([str(x or "").strip() for x in all_ids if str(x or "").strip()]))

        read_set = await _fetch_read_id_set(uid, all_ids) if all_ids else set()

        def _latest_unread(ids: List[str]) -> bool:
            latest_id = ids[0] if ids else None
            return bool(latest_id) and latest_id not in read_set

        response = MyWebUnreadStatusResponse(
            viewer_tier=tier_str,
            ids_by_type=MyWebUnreadIdsByType(**ids_by_type),
            read_ids=[rid for rid in all_ids if rid in read_set],
            unread_by_type=MyWebUnreadFlags(
                daily=_latest_unread(ids_by_type["daily"]),
                weekly=_latest_unread(ids_by_type["weekly"]),
                monthly=_latest_unread(ids_by_type["monthly"]),
                selfStructure=_latest_unread(ids_by_type["selfStructure"]),
            ),
        )
        return jsonable_encoder(response)

    return await get_or_compute(cache_key, MYWEB_UNREAD_STATUS_CACHE_TTL_SECONDS, _build_payload)


def register_report_reads_routes(app: FastAPI) -> None:
    @app.get("/report-reads/status", response_model=ReportReadStatusResponse)
    async def get_report_reads_status(
        report_ids: Optional[List[str]] = Query(default=None),
        authorization: Optional[str] = Header(default=None, alias="Authorization"),
    ) -> ReportReadStatusResponse:
        me = await _require_user_id(authorization)
        ids = _normalize_report_ids(report_ids)
        if not ids:
            return ReportReadStatusResponse(read_ids=[], read_map={})
        read_set = await _fetch_read_id_set(me, ids)
        read_ids = [rid for rid in ids if rid in read_set]
        return ReportReadStatusResponse(
            read_ids=read_ids,
            read_map={rid: (rid in read_set) for rid in ids},
        )

    @app.post("/report-reads/mark", response_model=ReportReadMarkResponse)
    async def post_report_reads_mark(
        body: ReportReadMarkBody,
        authorization: Optional[str] = Header(default=None, alias="Authorization"),
    ) -> ReportReadMarkResponse:
        me = await _require_user_id(authorization)
        rid = str(body.report_id or "").strip()
        if not rid:
            raise HTTPException(status_code=400, detail="report_id is required")

        marked = await _mark_report_as_read(
            me,
            rid,
            report_table=body.report_table,
            report_scope=body.report_scope,
            read_at=body.read_at,
        )
        if not marked:
            raise HTTPException(status_code=502, detail="Failed to mark report as read")

        await invalidate_prefix(f"report_reads:myweb_unread:{me}")
        return ReportReadMarkResponse(report_id=rid, marked=True)

    @app.get("/report-reads/myweb-unread-status", response_model=MyWebUnreadStatusResponse)
    async def get_myweb_unread_status(
        limit: int = Query(default=1, ge=1, le=10),
        include_self_structure: bool = Query(default=True),
        authorization: Optional[str] = Header(default=None, alias="Authorization"),
    ) -> MyWebUnreadStatusResponse:
        me = await _require_user_id(authorization)
        payload = await get_myweb_unread_status_payload_for_user(
            me,
            limit=limit,
            include_self_structure=include_self_structure,
        )
        return MyWebUnreadStatusResponse(**payload)
