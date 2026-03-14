# -*- coding: utf-8 -*-
"""Storage helpers for ASTOR global summary artifacts.

Purpose
-------
既存の `/global_summary` contract を維持したまま、日次の app-wide 集計結果を
`public.global_activity_summaries` に DRAFT / READY artifact として保存・取得する。

Scope (Step 1)
--------------
- per-day global summary の保存
- latest READY summary の取得
- inspection 後の READY promote / failed mark
- payload から totals を安全に取り出す
- source_hash の deterministic 計算

Design notes
------------
- Global Summary は cross-user aggregate だが ranking_board とは shape が異なるため
  dedicated artifact table を使う
- Step 1 は generic products table ではなく専用 `global_activity_summaries`
  を使う
- source_hash は `activity_date + timezone + totals` 指紋から計算する
- payload では canonical key を `reflection_views` に統一し、legacy alias
  (`reflection_view_count` / `reflection_count`) は normalize 時だけ吸収する
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
from datetime import date, datetime, timezone
from decimal import Decimal
from typing import Any, Dict, Iterable, List, Optional, Sequence

from supabase_client import ensure_supabase_config, sb_get, sb_patch, sb_post

logger = logging.getLogger("astor_global_summary_store")


GLOBAL_ACTIVITY_SUMMARIES_TABLE = (
    os.getenv("ASTOR_GLOBAL_ACTIVITY_SUMMARIES_TABLE")
    or os.getenv("GLOBAL_ACTIVITY_SUMMARIES_TABLE")
    or "global_activity_summaries"
).strip() or "global_activity_summaries"

GLOBAL_SUMMARY_VERSION = "global_summary.v1"
GLOBAL_SUMMARY_TIMEZONE = (
    os.getenv("ASTOR_GLOBAL_SUMMARY_TIMEZONE", "Asia/Tokyo") or "Asia/Tokyo"
)

STATUS_DRAFT = "draft"
STATUS_READY = "ready"
STATUS_FAILED = "failed"
ALLOWED_STATUSES = {
    STATUS_DRAFT,
    STATUS_READY,
    STATUS_FAILED,
}

GLOBAL_SUMMARY_TOTAL_KEYS: Sequence[str] = (
    "emotion_users",
    "reflection_views",
    "echo_count",
    "discovery_count",
)

GLOBAL_SUMMARY_TOTAL_ALIASES: Dict[str, Sequence[str]] = {
    "emotion_users": ("emotion_users",),
    "reflection_views": (
        "reflection_views",
        "reflection_view_count",
        "reflection_count",
    ),
    "echo_count": ("echo_count", "echoes", "echoes_count"),
    "discovery_count": (
        "discovery_count",
        "discoveries",
        "discoveries_count",
    ),
}


def _now_iso_z() -> str:
    return (
        datetime.now(timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )


def canonical_global_summary_activity_date(value: Any) -> str:
    if isinstance(value, datetime):
        return value.date().isoformat()
    if isinstance(value, date):
        return value.isoformat()

    s = str(value or "").strip()
    if not s:
        return ""

    candidate = s[:10] if len(s) >= 10 else s
    try:
        return datetime.strptime(candidate, "%Y-%m-%d").date().isoformat()
    except Exception:
        return ""


def canonical_global_summary_timezone(value: Any) -> str:
    s = str(value or "").strip()
    if not s:
        return GLOBAL_SUMMARY_TIMEZONE

    normalized = s.replace(" ", "")
    lowered = normalized.lower()
    if lowered in {"asia/tokyo", "jst"}:
        return "Asia/Tokyo"
    if normalized in {"+09:00", "+0900", "09:00"}:
        return "Asia/Tokyo"
    return s


def _canonical_status(value: Any) -> str:
    s = str(value or "").strip().lower()
    if s in ALLOWED_STATUSES:
        return s
    return ""


def _normalize_statuses(statuses: Optional[Iterable[str]]) -> List[str]:
    out: List[str] = []
    seen = set()
    for raw in statuses or []:
        s = _canonical_status(raw)
        if not s or s in seen:
            continue
        seen.add(s)
        out.append(s)
    return out


def _to_int(value: Any) -> int:
    if value is None or value == "" or isinstance(value, bool):
        return 0
    try:
        return int(value)
    except Exception:
        try:
            return int(float(str(value)))
        except Exception:
            return 0


def _json_ready(value: Any) -> Any:
    """Best-effort conversion into a JSON-serializable structure."""
    if value is None:
        return None
    if isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, Decimal):
        try:
            i = int(value)
            if Decimal(i) == value:
                return i
        except Exception:
            pass
        return float(value)
    if isinstance(value, (datetime, date)):
        return value.isoformat()
    if isinstance(value, dict):
        return {str(k): _json_ready(v) for k, v in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [_json_ready(v) for v in value]
    return str(value)


def _pick_first_value(src: Dict[str, Any], aliases: Sequence[str]) -> Any:
    for key in aliases or ():
        if key in src and src.get(key) is not None:
            return src.get(key)
    return None


def _normalize_totals(raw: Any) -> Dict[str, int]:
    src = raw if isinstance(raw, dict) else {}
    out: Dict[str, int] = {}
    for key in GLOBAL_SUMMARY_TOTAL_KEYS:
        aliases = GLOBAL_SUMMARY_TOTAL_ALIASES.get(key) or (key,)
        out[key] = max(0, _to_int(_pick_first_value(src, aliases)))
    return out


def normalize_global_summary_payload(
    activity_date: Any,
    payload: Optional[Dict[str, Any]],
    *,
    timezone_name: Optional[str] = None,
) -> Dict[str, Any]:
    """Normalize a global summary payload into the canonical v1 shape."""
    base = payload if isinstance(payload, dict) else {}
    act_date = canonical_global_summary_activity_date(activity_date) or canonical_global_summary_activity_date(
        base.get("activity_date") or base.get("date")
    )
    if not act_date:
        raise ValueError("activity_date is required")

    normalized = _json_ready(base)
    if not isinstance(normalized, dict):
        normalized = {}

    totals_source = normalized.get("totals") if isinstance(normalized.get("totals"), dict) else normalized
    totals = _normalize_totals(totals_source)

    normalized["version"] = (
        str(normalized.get("version") or GLOBAL_SUMMARY_VERSION).strip()
        or GLOBAL_SUMMARY_VERSION
    )
    normalized["activity_date"] = act_date
    normalized["timezone"] = canonical_global_summary_timezone(
        timezone_name or normalized.get("timezone") or normalized.get("tz") or GLOBAL_SUMMARY_TIMEZONE
    )
    normalized["generated_at"] = (
        str(normalized.get("generated_at") or normalized.get("updated_at") or _now_iso_z()).strip()
        or _now_iso_z()
    )
    normalized["totals"] = totals
    return normalized


def build_global_summary_source_hash(
    activity_date: Any,
    payload: Dict[str, Any],
    *,
    timezone_name: Optional[str] = None,
) -> str:
    """Build a deterministic source hash for a global summary payload.

    We intentionally exclude volatile metadata such as `generated_at` so that
    identical daily totals produce the same hash.
    """
    normalized = normalize_global_summary_payload(
        activity_date,
        payload,
        timezone_name=timezone_name,
    )
    basis = {
        "activity_date": str(normalized.get("activity_date") or ""),
        "timezone": str(normalized.get("timezone") or GLOBAL_SUMMARY_TIMEZONE),
        "totals": normalized.get("totals") if isinstance(normalized.get("totals"), dict) else {},
    }
    raw = json.dumps(basis, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _summary_row(row: Dict[str, Any]) -> Dict[str, Any]:
    if not isinstance(row, dict):
        return {}
    payload = row.get("payload") if isinstance(row.get("payload"), dict) else {}
    meta = row.get("meta") if isinstance(row.get("meta"), dict) else {}
    return {
        "id": str(row.get("id") or "").strip(),
        "activity_date": canonical_global_summary_activity_date(row.get("activity_date")),
        "timezone": canonical_global_summary_timezone(row.get("timezone")),
        "status": _canonical_status(row.get("status")),
        "payload": payload,
        "source_hash": str(row.get("source_hash") or "").strip(),
        "version": int(row.get("version") or 1),
        "meta": meta,
        "created_at": row.get("created_at"),
        "updated_at": row.get("updated_at"),
        "published_at": row.get("published_at"),
    }


def _in_list(values: Iterable[str]) -> str:
    xs: List[str] = []
    for raw in values:
        v = str(raw or "").strip().replace('"', '\\"')
        if not v:
            continue
        xs.append(f'"{v}"')
    return f"in.({','.join(xs)})"


async def _fetch_summary_by_id(summary_id: str) -> Optional[Dict[str, Any]]:
    sid = str(summary_id or "").strip()
    if not sid:
        return None
    ensure_supabase_config()
    resp = await sb_get(
        f"/rest/v1/{GLOBAL_ACTIVITY_SUMMARIES_TABLE}",
        params={
            "select": "id,activity_date,timezone,status,payload,source_hash,version,meta,created_at,updated_at,published_at",
            "id": f"eq.{sid}",
            "limit": "1",
        },
        timeout=8.0,
    )
    if resp.status_code not in (200, 206):
        raise RuntimeError(
            f"fetch global_activity_summary by id failed: {resp.status_code} {(resp.text or '')[:800]}"
        )
    data = resp.json()
    if isinstance(data, list) and data:
        return _summary_row(data[0])
    return None


async def _fetch_summary_by_activity_date_and_source_hash(
    activity_date: Any,
    source_hash: str,
    *,
    timezone_name: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    act_date = canonical_global_summary_activity_date(activity_date)
    sh = str(source_hash or "").strip()
    tz_name = canonical_global_summary_timezone(timezone_name)
    if not act_date or not sh:
        return None

    ensure_supabase_config()
    resp = await sb_get(
        f"/rest/v1/{GLOBAL_ACTIVITY_SUMMARIES_TABLE}",
        params={
            "select": "id,activity_date,timezone,status,payload,source_hash,version,meta,created_at,updated_at,published_at",
            "activity_date": f"eq.{act_date}",
            "timezone": f"eq.{tz_name}",
            "source_hash": f"eq.{sh}",
            "order": "updated_at.desc,id.desc",
            "limit": "1",
        },
        timeout=8.0,
    )
    if resp.status_code not in (200, 206):
        raise RuntimeError(
            f"fetch global_activity_summary by source_hash failed: {resp.status_code} {(resp.text or '')[:800]}"
        )
    data = resp.json()
    if isinstance(data, list) and data:
        return _summary_row(data[0])
    return None


async def upsert_global_summary_draft(
    activity_date: Any,
    payload: Dict[str, Any],
    meta: Optional[Dict[str, Any]] = None,
    *,
    timezone_name: Optional[str] = None,
    version: int = 1,
) -> Dict[str, Any]:
    """Create or update a global daily summary artifact.

    Behavior
    --------
    - same activity_date + timezone + source_hash already exists and is READY:
        keep READY, refresh payload/meta/updated_at only
    - same activity_date + timezone + source_hash already exists and is DRAFT/FAILED:
        move to DRAFT and update payload/meta/updated_at
    - otherwise:
        insert a new row (status defaults to draft via DB default)
    """
    act_date = canonical_global_summary_activity_date(activity_date)
    if not act_date:
        raise ValueError("activity_date is required")

    ensure_supabase_config()

    normalized_payload = normalize_global_summary_payload(
        act_date,
        payload,
        timezone_name=timezone_name,
    )
    tz_name = canonical_global_summary_timezone(normalized_payload.get("timezone"))
    meta_payload = _json_ready(meta or {})
    if not isinstance(meta_payload, dict):
        meta_payload = {}
    now_iso = _now_iso_z()
    source_hash = build_global_summary_source_hash(
        act_date,
        normalized_payload,
        timezone_name=tz_name,
    )

    existing = await _fetch_summary_by_activity_date_and_source_hash(
        act_date,
        source_hash,
        timezone_name=tz_name,
    )
    if existing:
        patch_body: Dict[str, Any] = {
            "activity_date": act_date,
            "timezone": tz_name,
            "payload": normalized_payload,
            "meta": meta_payload,
            "version": int(version or 1),
            "source_hash": source_hash,
            "updated_at": now_iso,
        }
        if existing.get("status") != STATUS_READY:
            patch_body["status"] = STATUS_DRAFT
            patch_body["published_at"] = None
        resp = await sb_patch(
            f"/rest/v1/{GLOBAL_ACTIVITY_SUMMARIES_TABLE}",
            json=patch_body,
            params={"id": f"eq.{existing['id']}"},
            prefer="return=representation",
            timeout=8.0,
        )
        if resp.status_code not in (200, 204):
            raise RuntimeError(
                f"global_activity_summary patch failed: {resp.status_code} {(resp.text or '')[:800]}"
            )
        data = resp.json() if resp.status_code == 200 else []
        if isinstance(data, list) and data:
            return _summary_row(data[0])
        latest = await _fetch_summary_by_id(existing["id"])
        if latest:
            return latest
        raise RuntimeError("global_activity_summary patch succeeded but row not found")

    insert_row: Dict[str, Any] = {
        "activity_date": act_date,
        "timezone": tz_name,
        "payload": normalized_payload,
        "source_hash": source_hash,
        "version": int(version or 1),
        "meta": meta_payload,
        "updated_at": now_iso,
    }
    resp = await sb_post(
        f"/rest/v1/{GLOBAL_ACTIVITY_SUMMARIES_TABLE}",
        json=insert_row,
        params={"on_conflict": "activity_date,timezone,source_hash"},
        prefer="resolution=merge-duplicates,return=representation",
        timeout=8.0,
    )
    if resp.status_code not in (200, 201, 204):
        raise RuntimeError(
            f"global_activity_summary insert failed: {resp.status_code} {(resp.text or '')[:800]}"
        )
    data = resp.json() if resp.status_code in (200, 201) else []
    if isinstance(data, list) and data:
        row = _summary_row(data[0])
        if row:
            return row

    latest = await _fetch_summary_by_activity_date_and_source_hash(
        act_date,
        source_hash,
        timezone_name=tz_name,
    )
    if latest:
        return latest
    raise RuntimeError("global_activity_summary insert succeeded but row not found")


async def fetch_latest_global_summary(
    activity_date: Any,
    *,
    timezone_name: Optional[str] = None,
    statuses: Optional[Iterable[str]] = None,
) -> Optional[Dict[str, Any]]:
    act_date = canonical_global_summary_activity_date(activity_date)
    if not act_date:
        return None
    ensure_supabase_config()

    params: Dict[str, str] = {
        "select": "id,activity_date,timezone,status,payload,source_hash,version,meta,created_at,updated_at,published_at",
        "activity_date": f"eq.{act_date}",
        "timezone": f"eq.{canonical_global_summary_timezone(timezone_name)}",
        "order": "updated_at.desc,id.desc",
        "limit": "1",
    }
    normalized_statuses = _normalize_statuses(statuses)
    if len(normalized_statuses) == 1:
        params["status"] = f"eq.{normalized_statuses[0]}"
    elif len(normalized_statuses) > 1:
        params["status"] = _in_list(normalized_statuses)

    resp = await sb_get(
        f"/rest/v1/{GLOBAL_ACTIVITY_SUMMARIES_TABLE}",
        params=params,
        timeout=8.0,
    )
    if resp.status_code not in (200, 206):
        raise RuntimeError(
            f"fetch latest global_activity_summary failed: {resp.status_code} {(resp.text or '')[:800]}"
        )
    data = resp.json()
    if isinstance(data, list) and data:
        return _summary_row(data[0])
    return None


async def fetch_latest_ready_global_summary(
    activity_date: Any,
    *,
    timezone_name: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    return await fetch_latest_global_summary(
        activity_date,
        timezone_name=timezone_name,
        statuses=[STATUS_READY],
    )


async def promote_global_summary(
    summary_id: str,
    *,
    published_at: Optional[str] = None,
    extra_meta: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    sid = str(summary_id or "").strip()
    if not sid:
        raise ValueError("summary_id is required")
    ensure_supabase_config()

    current = await _fetch_summary_by_id(sid)
    if not current:
        raise RuntimeError(f"global_activity_summary not found: {sid}")

    merged_meta = dict(current.get("meta") or {})
    if isinstance(extra_meta, dict) and extra_meta:
        merged_meta.update(_json_ready(extra_meta))

    patch_body = {
        "status": STATUS_READY,
        "meta": merged_meta,
        "updated_at": _now_iso_z(),
        "published_at": str(published_at or _now_iso_z()).strip() or _now_iso_z(),
    }
    resp = await sb_patch(
        f"/rest/v1/{GLOBAL_ACTIVITY_SUMMARIES_TABLE}",
        json=patch_body,
        params={"id": f"eq.{sid}"},
        prefer="return=representation",
        timeout=8.0,
    )
    if resp.status_code not in (200, 204):
        raise RuntimeError(
            f"global_activity_summary promote failed: {resp.status_code} {(resp.text or '')[:800]}"
        )
    data = resp.json() if resp.status_code == 200 else []
    if isinstance(data, list) and data:
        return _summary_row(data[0])
    latest = await _fetch_summary_by_id(sid)
    if latest:
        return latest
    raise RuntimeError("global_activity_summary promote succeeded but row not found")


async def fail_global_summary(
    summary_id: str,
    reason: str,
    *,
    flags: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    sid = str(summary_id or "").strip()
    msg = str(reason or "").strip() or "global_activity_summary inspection failed"
    if not sid:
        raise ValueError("summary_id is required")
    ensure_supabase_config()

    current = await _fetch_summary_by_id(sid)
    if not current:
        raise RuntimeError(f"global_activity_summary not found: {sid}")

    merged_meta = dict(current.get("meta") or {})
    merged_meta["last_error"] = msg
    merged_meta["last_failed_at"] = _now_iso_z()
    if isinstance(flags, dict) and flags:
        merged_meta.setdefault("flags", {})
        flags_map = merged_meta.get("flags") if isinstance(merged_meta.get("flags"), dict) else {}
        flags_map.update(_json_ready(flags))
        merged_meta["flags"] = flags_map

    patch_body = {
        "status": STATUS_FAILED,
        "meta": merged_meta,
        "updated_at": _now_iso_z(),
    }
    resp = await sb_patch(
        f"/rest/v1/{GLOBAL_ACTIVITY_SUMMARIES_TABLE}",
        json=patch_body,
        params={"id": f"eq.{sid}"},
        prefer="return=representation",
        timeout=8.0,
    )
    if resp.status_code not in (200, 204):
        raise RuntimeError(
            f"global_activity_summary fail patch failed: {resp.status_code} {(resp.text or '')[:800]}"
        )
    data = resp.json() if resp.status_code == 200 else []
    if isinstance(data, list) and data:
        return _summary_row(data[0])
    latest = await _fetch_summary_by_id(sid)
    if latest:
        return latest
    raise RuntimeError("global_activity_summary fail patch succeeded but row not found")


def extract_global_summary_totals(summary_payload: Any) -> Dict[str, int]:
    """Return normalized totals from either a summary row or a raw payload."""
    if isinstance(summary_payload, dict) and isinstance(summary_payload.get("payload"), dict):
        payload = summary_payload.get("payload") or {}
    elif isinstance(summary_payload, dict):
        payload = summary_payload
    else:
        return _normalize_totals({})

    totals = payload.get("totals") if isinstance(payload.get("totals"), dict) else payload
    return _normalize_totals(totals)


__all__ = [
    "GLOBAL_ACTIVITY_SUMMARIES_TABLE",
    "GLOBAL_SUMMARY_VERSION",
    "GLOBAL_SUMMARY_TIMEZONE",
    "STATUS_DRAFT",
    "STATUS_READY",
    "STATUS_FAILED",
    "GLOBAL_SUMMARY_TOTAL_KEYS",
    "GLOBAL_SUMMARY_TOTAL_ALIASES",
    "canonical_global_summary_activity_date",
    "canonical_global_summary_timezone",
    "normalize_global_summary_payload",
    "build_global_summary_source_hash",
    "upsert_global_summary_draft",
    "fetch_latest_global_summary",
    "fetch_latest_ready_global_summary",
    "promote_global_summary",
    "fail_global_summary",
    "extract_global_summary_totals",
]
