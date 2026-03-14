# -*- coding: utf-8 -*-
from __future__ import annotations

import json
import logging
import os
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from fastapi import HTTPException

from supabase_client import ensure_supabase_config, sb_get, sb_patch, sb_post

logger = logging.getLogger("report_distribution_push_store")

REPORT_DISTRIBUTION_PUSH_CANDIDATES_TABLE = (
    os.getenv("REPORT_DISTRIBUTION_PUSH_CANDIDATES_TABLE") or "report_distribution_push_candidates"
).strip() or "report_distribution_push_candidates"
REPORT_DISTRIBUTION_PUSH_DELIVERIES_TABLE = (
    os.getenv("REPORT_DISTRIBUTION_PUSH_DELIVERIES_TABLE") or "report_distribution_push_deliveries"
).strip() or "report_distribution_push_deliveries"
REPORT_DISTRIBUTION_PUSH_SCAN_LIMIT = int(
    os.getenv("REPORT_DISTRIBUTION_PUSH_SCAN_LIMIT", "1000") or "1000"
)


def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


def _iso_utc(dt: Optional[datetime] = None) -> str:
    return (dt or _now_utc()).astimezone(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _raise_http_from_supabase(resp, default_detail: str) -> None:
    detail = default_detail
    try:
        js = resp.json()
        if isinstance(js, dict):
            detail = str(js.get("message") or js.get("hint") or js.get("details") or js.get("detail") or default_detail)
        elif js:
            detail = str(js)
    except Exception:
        txt = (getattr(resp, "text", "") or "").strip()
        if txt:
            detail = txt[:500]
    raise HTTPException(status_code=502, detail=detail)


def _parse_jsonish(value: Any, default: Any) -> Any:
    if value is None:
        return default
    if isinstance(value, (dict, list)):
        return value
    if isinstance(value, str):
        s = value.strip()
        if not s:
            return default
        try:
            return json.loads(s)
        except Exception:
            return default
    return default


class ReportDistributionPushStore:
    async def create_candidate(
        self,
        *,
        user_id: str,
        distribution_key: str,
        report_family: str,
        report_table: str,
        report_id: Any,
        report_type: Optional[str],
        period_start: Optional[str],
        period_end: Optional[str],
        open_target: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        ensure_supabase_config()
        uid = str(user_id or "").strip()
        dist_key = str(distribution_key or "").strip()
        family = str(report_family or "").strip()
        table = str(report_table or "").strip()
        if not uid or not dist_key or not family or not table:
            raise HTTPException(status_code=400, detail="user_id, distribution_key, report_family, report_table are required")

        payload = {
            "user_id": uid,
            "distribution_key": dist_key,
            "report_family": family,
            "report_table": table,
            "report_id": str(report_id or "").strip() or None,
            "report_type": str(report_type or "").strip() or None,
            "period_start": str(period_start or "").strip() or None,
            "period_end": str(period_end or "").strip() or None,
            "open_target_json": open_target or {},
            "created_at": _iso_utc(),
        }
        resp = await sb_post(
            f"/rest/v1/{REPORT_DISTRIBUTION_PUSH_CANDIDATES_TABLE}?on_conflict=user_id,distribution_key,report_family",
            json=payload,
            prefer="resolution=merge-duplicates,return=representation",
            timeout=10.0,
        )
        if resp.status_code not in (200, 201):
            _raise_http_from_supabase(resp, "Failed to save report distribution push candidate")
        rows = resp.json()
        if isinstance(rows, list) and rows and isinstance(rows[0], dict):
            return rows[0]
        return payload

    async def list_pending_candidates(self, *, limit: int = REPORT_DISTRIBUTION_PUSH_SCAN_LIMIT) -> List[Dict[str, Any]]:
        ensure_supabase_config()
        lim = max(1, min(int(limit or REPORT_DISTRIBUTION_PUSH_SCAN_LIMIT), REPORT_DISTRIBUTION_PUSH_SCAN_LIMIT))
        resp = await sb_get(
            f"/rest/v1/{REPORT_DISTRIBUTION_PUSH_CANDIDATES_TABLE}",
            params={
                "select": "id,user_id,distribution_key,report_family,report_table,report_id,report_type,period_start,period_end,open_target_json,created_at,delivered_at",
                "delivered_at": "is.null",
                "order": "distribution_key.asc,created_at.asc,id.asc",
                "limit": str(lim),
            },
            timeout=10.0,
        )
        if resp.status_code not in (200, 206):
            _raise_http_from_supabase(resp, "Failed to fetch pending report distribution push candidates")
        rows = resp.json()
        out: List[Dict[str, Any]] = []
        if isinstance(rows, list):
            for row in rows:
                if not isinstance(row, dict):
                    continue
                row2 = dict(row)
                row2["open_target_json"] = _parse_jsonish(row.get("open_target_json"), {})
                out.append(row2)
        return out

    async def mark_bundle_delivered(
        self,
        *,
        user_id: str,
        distribution_key: str,
        bundle_families: List[str],
        payload: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        ensure_supabase_config()
        uid = str(user_id or "").strip()
        dist_key = str(distribution_key or "").strip()
        if not uid or not dist_key:
            raise HTTPException(status_code=400, detail="user_id and distribution_key are required")

        delivered_at = _iso_utc()
        families = [str(x or "").strip() for x in (bundle_families or []) if str(x or "").strip()]
        delivery_payload = {
            "user_id": uid,
            "distribution_key": dist_key,
            "bundle_families_json": families,
            "payload_json": payload or {},
            "delivered_at": delivered_at,
        }
        resp = await sb_post(
            f"/rest/v1/{REPORT_DISTRIBUTION_PUSH_DELIVERIES_TABLE}?on_conflict=user_id,distribution_key",
            json=delivery_payload,
            prefer="resolution=merge-duplicates,return=representation",
            timeout=10.0,
        )
        if resp.status_code not in (200, 201):
            _raise_http_from_supabase(resp, "Failed to save report distribution push delivery")

        patch_resp = await sb_patch(
            f"/rest/v1/{REPORT_DISTRIBUTION_PUSH_CANDIDATES_TABLE}",
            params={
                "user_id": f"eq.{uid}",
                "distribution_key": f"eq.{dist_key}",
                "delivered_at": "is.null",
            },
            json={"delivered_at": delivered_at},
            prefer="return=minimal",
            timeout=10.0,
        )
        if patch_resp.status_code not in (200, 204):
            _raise_http_from_supabase(patch_resp, "Failed to mark report distribution push candidates delivered")

        rows = resp.json()
        if isinstance(rows, list) and rows and isinstance(rows[0], dict):
            return rows[0]
        return delivery_payload
