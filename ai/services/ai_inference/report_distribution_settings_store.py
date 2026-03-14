# -*- coding: utf-8 -*-
from __future__ import annotations

import logging
import os
import re
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
from zoneinfo import ZoneInfo

from fastapi import HTTPException

from supabase_client import ensure_supabase_config, sb_get, sb_post

logger = logging.getLogger("report_distribution_settings_store")

REPORT_DISTRIBUTION_SETTINGS_TABLE = (
    os.getenv("REPORT_DISTRIBUTION_SETTINGS_TABLE") or "report_distribution_user_settings"
).strip() or "report_distribution_user_settings"
REPORT_DISTRIBUTION_DEFAULT_TIMEZONE = (
    os.getenv("REPORT_DISTRIBUTION_DEFAULT_TIMEZONE") or "Asia/Tokyo"
).strip() or "Asia/Tokyo"
REPORT_DISTRIBUTION_DEFAULT_DELIVERY_TIME = (
    os.getenv("REPORT_DISTRIBUTION_DEFAULT_DELIVERY_TIME") or "00:00"
).strip() or "00:00"
REPORT_DISTRIBUTION_DEFAULT_NOTIFICATION_ENABLED = (
    os.getenv("REPORT_DISTRIBUTION_DEFAULT_NOTIFICATION_ENABLED") or "true"
).strip().lower() in ("1", "true", "yes", "on")

_HHMM_RE = re.compile(r"^(?:[01]\d|2[0-3]):[0-5]\d$")


def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


def _iso_utc(dt: Optional[datetime] = None) -> str:
    return (dt or _now_utc()).astimezone(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _normalize_timezone_name(raw: Any) -> str:
    s = str(raw or "").strip() or REPORT_DISTRIBUTION_DEFAULT_TIMEZONE
    try:
        ZoneInfo(s)
        return s
    except Exception:
        return REPORT_DISTRIBUTION_DEFAULT_TIMEZONE


def _normalize_delivery_time_local(raw: Any) -> str:
    s = str(raw or "").strip() or REPORT_DISTRIBUTION_DEFAULT_DELIVERY_TIME
    return s if _HHMM_RE.match(s) else REPORT_DISTRIBUTION_DEFAULT_DELIVERY_TIME


def _parse_iso_utcish(raw: Any) -> Optional[datetime]:
    s = str(raw or "").strip()
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


def _in_filter(ids: List[str]) -> str:
    quoted: List[str] = []
    for raw in ids or []:
        s = str(raw or "").strip()
        if not s:
            continue
        quoted.append('"' + s.replace('"', '') + '"')
    return f"in.({','.join(quoted)})"


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


def report_distribution_default_settings_public(timezone_name: Optional[str] = None) -> Dict[str, Any]:
    return {
        "notification_enabled": bool(REPORT_DISTRIBUTION_DEFAULT_NOTIFICATION_ENABLED),
        "delivery_time_local": _normalize_delivery_time_local(None),
        "timezone_name": _normalize_timezone_name(timezone_name),
    }


def _settings_public(row: Dict[str, Any]) -> Dict[str, Any]:
    base = report_distribution_default_settings_public(str((row or {}).get("timezone_name") or "") or None)
    base["notification_enabled"] = bool((row or {}).get("notification_enabled", base["notification_enabled"]))
    base["delivery_time_local"] = _normalize_delivery_time_local((row or {}).get("delivery_time_local"))
    base["timezone_name"] = _normalize_timezone_name((row or {}).get("timezone_name"))
    return base


def is_bundle_due_for_settings(
    *,
    candidate_created_at: Any,
    settings: Optional[Dict[str, Any]],
    now_utc: Optional[datetime] = None,
) -> bool:
    current = now_utc or _now_utc()
    normalized = _settings_public(settings or {})
    timezone_name = _normalize_timezone_name(normalized.get("timezone_name"))
    delivery_time_local = _normalize_delivery_time_local(normalized.get("delivery_time_local"))
    ready_at = _parse_iso_utcish(candidate_created_at) or current
    zone = ZoneInfo(timezone_name)
    ready_local = ready_at.astimezone(zone)
    now_local = current.astimezone(zone)

    if now_local.date() > ready_local.date():
        return True
    if now_local.date() < ready_local.date():
        return False
    return now_local.strftime("%H:%M") >= delivery_time_local


class ReportDistributionSettingsStore:
    async def _select_rows(self, *, params: Dict[str, str]) -> List[Dict[str, Any]]:
        ensure_supabase_config()
        resp = await sb_get(
            f"/rest/v1/{REPORT_DISTRIBUTION_SETTINGS_TABLE}",
            params=params,
            timeout=10.0,
        )
        if resp.status_code not in (200, 206):
            _raise_http_from_supabase(resp, f"Failed to query {REPORT_DISTRIBUTION_SETTINGS_TABLE}")
        data = resp.json()
        if isinstance(data, list):
            return [x for x in data if isinstance(x, dict)]
        if isinstance(data, dict):
            return [data]
        return []

    async def _upsert_row(self, body: Dict[str, Any]) -> Dict[str, Any]:
        ensure_supabase_config()
        resp = await sb_post(
            f"/rest/v1/{REPORT_DISTRIBUTION_SETTINGS_TABLE}?on_conflict=user_id",
            json=body,
            prefer="resolution=merge-duplicates,return=representation",
            timeout=10.0,
        )
        if resp.status_code not in (200, 201):
            _raise_http_from_supabase(resp, f"Failed to upsert {REPORT_DISTRIBUTION_SETTINGS_TABLE}")
        data = resp.json()
        if isinstance(data, list) and data and isinstance(data[0], dict):
            return data[0]
        if isinstance(data, dict):
            return data
        return body

    async def get_or_create_user_settings(self, user_id: str, *, timezone_name: Optional[str] = None) -> Dict[str, Any]:
        uid = str(user_id or "").strip()
        if not uid:
            raise HTTPException(status_code=401, detail="Unauthorized")

        rows = await self._select_rows(
            params={
                "select": "*",
                "user_id": f"eq.{uid}",
                "limit": "1",
            },
        )
        if rows:
            return _settings_public(rows[0])

        created = {
            "user_id": uid,
            "notification_enabled": REPORT_DISTRIBUTION_DEFAULT_NOTIFICATION_ENABLED,
            "delivery_time_local": _normalize_delivery_time_local(None),
            "timezone_name": _normalize_timezone_name(timezone_name),
            "created_at": _iso_utc(),
            "updated_at": _iso_utc(),
        }
        row = await self._upsert_row(created)
        return _settings_public(row if isinstance(row, dict) else created)

    async def patch_user_settings(
        self,
        user_id: str,
        *,
        notification_enabled: Optional[bool] = None,
        delivery_time_local: Optional[str] = None,
        timezone_name: Optional[str] = None,
    ) -> Dict[str, Any]:
        uid = str(user_id or "").strip()
        current = await self.get_or_create_user_settings(uid, timezone_name=timezone_name)
        body = {
            "user_id": uid,
            "notification_enabled": current["notification_enabled"] if notification_enabled is None else bool(notification_enabled),
            "delivery_time_local": current["delivery_time_local"] if delivery_time_local is None else _normalize_delivery_time_local(delivery_time_local),
            "timezone_name": current["timezone_name"] if timezone_name is None else _normalize_timezone_name(timezone_name),
            "updated_at": _iso_utc(),
        }
        row = await self._upsert_row(body)
        return _settings_public(row if isinstance(row, dict) else body)

    async def fetch_settings_map_for_users(self, user_ids: List[str]) -> Dict[str, Dict[str, Any]]:
        ids = [str(x or "").strip() for x in (user_ids or []) if str(x or "").strip()]
        if not ids:
            return {}
        rows = await self._select_rows(
            params={
                "select": "*",
                "user_id": _in_filter(ids),
                "limit": str(len(ids)),
            },
        )
        out: Dict[str, Dict[str, Any]] = {}
        for row in rows:
            uid = str((row or {}).get("user_id") or "").strip()
            if not uid:
                continue
            out[uid] = _settings_public(row)
        return out


__all__ = [
    "REPORT_DISTRIBUTION_SETTINGS_TABLE",
    "REPORT_DISTRIBUTION_DEFAULT_TIMEZONE",
    "REPORT_DISTRIBUTION_DEFAULT_DELIVERY_TIME",
    "REPORT_DISTRIBUTION_DEFAULT_NOTIFICATION_ENABLED",
    "ReportDistributionSettingsStore",
    "report_distribution_default_settings_public",
    "is_bundle_due_for_settings",
]
