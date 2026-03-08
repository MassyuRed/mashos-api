# -*- coding: utf-8 -*-
"""Storage helpers for ASTOR account status summary artifacts.

Purpose
-------
既存の `account_status_summary_v2` RPC kernel を維持しながら、結果を
`public.account_status_summaries` に DRAFT / READY artifact として保存・取得する。

Scope (Phase 1)
---------------
- per-user account status summary の保存
- latest READY summary の取得
- inspection 後の READY promote / failed mark
- payload から totals を安全に取り出す
- source_hash の deterministic 計算

Design notes
------------
- Account Status は Ranking の sibling だが global board ではなく per-user artifact
- Phase 1 は generic products table ではなく専用 `account_status_summaries` を使う
- visibility 系 (`is_private_account` / `is_friend_code_public`) は保存時に焼かず、publish 時に後付けする
- source_hash は snapshot ではなく normalized payload 指紋から作る
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

logger = logging.getLogger("astor_account_status_store")


ACCOUNT_STATUS_SUMMARIES_TABLE = (
    os.getenv("ASTOR_ACCOUNT_STATUS_SUMMARIES_TABLE")
    or os.getenv("ACCOUNT_STATUS_SUMMARIES_TABLE")
    or "account_status_summaries"
).strip() or "account_status_summaries"

ACCOUNT_STATUS_VERSION = "account_status.v1"
ACCOUNT_STATUS_TIMEZONE = os.getenv("ASTOR_ACCOUNT_STATUS_TIMEZONE", "Asia/Tokyo") or "Asia/Tokyo"

STATUS_DRAFT = "draft"
STATUS_READY = "ready"
STATUS_FAILED = "failed"
ALLOWED_STATUSES = {
    STATUS_DRAFT,
    STATUS_READY,
    STATUS_FAILED,
}

ACCOUNT_STATUS_TOTAL_KEYS: Sequence[str] = (
    "login_days_total",
    "login_streak_max",
    "input_count_total",
    "input_chars_total",
    "mymodel_questions_total",
    "mymodel_views_total",
    "mymodel_resonances_total",
    "mymodel_discoveries_total",
)


def _now_iso_z() -> str:
    return (
        datetime.now(timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )


def _canonical_target_user_id(value: Any) -> str:
    return str(value or "").strip()


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


def _normalize_totals(raw: Any) -> Dict[str, int]:
    src = raw if isinstance(raw, dict) else {}
    out: Dict[str, int] = {}
    for key in ACCOUNT_STATUS_TOTAL_KEYS:
        out[key] = max(0, _to_int(src.get(key)))
    return out


def normalize_account_status_payload(
    target_user_id: str,
    payload: Optional[Dict[str, Any]],
) -> Dict[str, Any]:
    """Normalize an account status payload into the canonical v1 shape."""
    tgt = _canonical_target_user_id(target_user_id) or _canonical_target_user_id(
        (payload or {}).get("target_user_id")
    )
    if not tgt:
        raise ValueError("target_user_id is required")

    base = payload if isinstance(payload, dict) else {}
    normalized = _json_ready(base)
    if not isinstance(normalized, dict):
        normalized = {}

    raw_totals = normalized.get("totals") if isinstance(normalized.get("totals"), dict) else normalized
    totals = _normalize_totals(raw_totals)

    normalized["version"] = (
        str(normalized.get("version") or ACCOUNT_STATUS_VERSION).strip()
        or ACCOUNT_STATUS_VERSION
    )
    normalized["target_user_id"] = tgt
    normalized["timezone"] = (
        str(normalized.get("timezone") or ACCOUNT_STATUS_TIMEZONE).strip()
        or ACCOUNT_STATUS_TIMEZONE
    )
    normalized["generated_at"] = (
        str(normalized.get("generated_at") or _now_iso_z()).strip() or _now_iso_z()
    )
    normalized["totals"] = totals
    return normalized


def build_account_status_source_hash(target_user_id: str, payload: Dict[str, Any]) -> str:
    """Build a deterministic source hash for an account status payload.

    We intentionally exclude volatile metadata such as `generated_at` so that
    identical totals produce the same hash.
    """
    normalized = normalize_account_status_payload(target_user_id, payload)
    basis = {
        "version": str(normalized.get("version") or ACCOUNT_STATUS_VERSION),
        "target_user_id": str(normalized.get("target_user_id") or ""),
        "timezone": str(normalized.get("timezone") or ACCOUNT_STATUS_TIMEZONE),
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
        "target_user_id": _canonical_target_user_id(row.get("target_user_id")),
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
        f"/rest/v1/{ACCOUNT_STATUS_SUMMARIES_TABLE}",
        params={
            "select": "id,target_user_id,status,payload,source_hash,version,meta,created_at,updated_at,published_at",
            "id": f"eq.{sid}",
            "limit": "1",
        },
        timeout=8.0,
    )
    if resp.status_code not in (200, 206):
        raise RuntimeError(
            f"fetch account_status_summary by id failed: {resp.status_code} {(resp.text or '')[:800]}"
        )
    data = resp.json()
    if isinstance(data, list) and data:
        return _summary_row(data[0])
    return None


async def _fetch_summary_by_target_and_source_hash(
    target_user_id: str,
    source_hash: str,
) -> Optional[Dict[str, Any]]:
    tgt = _canonical_target_user_id(target_user_id)
    sh = str(source_hash or "").strip()
    if not tgt or not sh:
        return None
    ensure_supabase_config()
    resp = await sb_get(
        f"/rest/v1/{ACCOUNT_STATUS_SUMMARIES_TABLE}",
        params={
            "select": "id,target_user_id,status,payload,source_hash,version,meta,created_at,updated_at,published_at",
            "target_user_id": f"eq.{tgt}",
            "source_hash": f"eq.{sh}",
            "order": "updated_at.desc,id.desc",
            "limit": "1",
        },
        timeout=8.0,
    )
    if resp.status_code not in (200, 206):
        raise RuntimeError(
            f"fetch account_status_summary by source_hash failed: {resp.status_code} {(resp.text or '')[:800]}"
        )
    data = resp.json()
    if isinstance(data, list) and data:
        return _summary_row(data[0])
    return None


async def upsert_account_status_draft(
    target_user_id: str,
    payload: Dict[str, Any],
    meta: Optional[Dict[str, Any]] = None,
    *,
    version: int = 1,
) -> Dict[str, Any]:
    """Create or update an account status summary artifact.

    Behavior
    --------
    - same target_user_id + source_hash already exists and is READY:
        keep READY, refresh payload/meta/updated_at only
    - same target_user_id + source_hash already exists and is DRAFT/FAILED:
        move to DRAFT and update payload/meta/updated_at
    - otherwise:
        insert a new row (status defaults to draft via DB default)
    """
    tgt = _canonical_target_user_id(target_user_id)
    if not tgt:
        raise ValueError("target_user_id is required")

    ensure_supabase_config()

    normalized_payload = normalize_account_status_payload(tgt, payload)
    meta_payload = _json_ready(meta or {})
    if not isinstance(meta_payload, dict):
        meta_payload = {}
    now_iso = _now_iso_z()
    source_hash = build_account_status_source_hash(tgt, normalized_payload)

    existing = await _fetch_summary_by_target_and_source_hash(tgt, source_hash)
    if existing:
        patch_body: Dict[str, Any] = {
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
            f"/rest/v1/{ACCOUNT_STATUS_SUMMARIES_TABLE}",
            json=patch_body,
            params={"id": f"eq.{existing['id']}"},
            prefer="return=representation",
            timeout=8.0,
        )
        if resp.status_code not in (200, 204):
            raise RuntimeError(
                f"account_status_summary patch failed: {resp.status_code} {(resp.text or '')[:800]}"
            )
        data = resp.json() if resp.status_code == 200 else []
        if isinstance(data, list) and data:
            return _summary_row(data[0])
        latest = await _fetch_summary_by_id(existing["id"])
        if latest:
            return latest
        raise RuntimeError("account_status_summary patch succeeded but row not found")

    insert_row: Dict[str, Any] = {
        "target_user_id": tgt,
        "payload": normalized_payload,
        "source_hash": source_hash,
        "version": int(version or 1),
        "meta": meta_payload,
        "updated_at": now_iso,
    }
    resp = await sb_post(
        f"/rest/v1/{ACCOUNT_STATUS_SUMMARIES_TABLE}",
        json=insert_row,
        params={"on_conflict": "target_user_id,source_hash"},
        prefer="resolution=merge-duplicates,return=representation",
        timeout=8.0,
    )
    if resp.status_code not in (200, 201, 204):
        raise RuntimeError(
            f"account_status_summary insert failed: {resp.status_code} {(resp.text or '')[:800]}"
        )
    data = resp.json() if resp.status_code in (200, 201) else []
    if isinstance(data, list) and data:
        row = _summary_row(data[0])
        if row:
            return row

    latest = await _fetch_summary_by_target_and_source_hash(tgt, source_hash)
    if latest:
        return latest
    raise RuntimeError("account_status_summary insert succeeded but row not found")


async def fetch_latest_account_status_summary(
    target_user_id: str,
    statuses: Optional[Iterable[str]] = None,
) -> Optional[Dict[str, Any]]:
    tgt = _canonical_target_user_id(target_user_id)
    if not tgt:
        return None
    ensure_supabase_config()

    params: Dict[str, str] = {
        "select": "id,target_user_id,status,payload,source_hash,version,meta,created_at,updated_at,published_at",
        "target_user_id": f"eq.{tgt}",
        "order": "updated_at.desc,id.desc",
        "limit": "1",
    }
    normalized_statuses = _normalize_statuses(statuses)
    if len(normalized_statuses) == 1:
        params["status"] = f"eq.{normalized_statuses[0]}"
    elif len(normalized_statuses) > 1:
        params["status"] = _in_list(normalized_statuses)

    resp = await sb_get(
        f"/rest/v1/{ACCOUNT_STATUS_SUMMARIES_TABLE}",
        params=params,
        timeout=8.0,
    )
    if resp.status_code not in (200, 206):
        raise RuntimeError(
            f"fetch latest account_status_summary failed: {resp.status_code} {(resp.text or '')[:800]}"
        )
    data = resp.json()
    if isinstance(data, list) and data:
        return _summary_row(data[0])
    return None


async def fetch_latest_ready_account_status_summary(target_user_id: str) -> Optional[Dict[str, Any]]:
    return await fetch_latest_account_status_summary(target_user_id, statuses=[STATUS_READY])


async def promote_account_status_summary(
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
        raise RuntimeError(f"account_status_summary not found: {sid}")

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
        f"/rest/v1/{ACCOUNT_STATUS_SUMMARIES_TABLE}",
        json=patch_body,
        params={"id": f"eq.{sid}"},
        prefer="return=representation",
        timeout=8.0,
    )
    if resp.status_code not in (200, 204):
        raise RuntimeError(
            f"account_status_summary promote failed: {resp.status_code} {(resp.text or '')[:800]}"
        )
    data = resp.json() if resp.status_code == 200 else []
    if isinstance(data, list) and data:
        return _summary_row(data[0])
    latest = await _fetch_summary_by_id(sid)
    if latest:
        return latest
    raise RuntimeError("account_status_summary promote succeeded but row not found")


async def fail_account_status_summary(
    summary_id: str,
    reason: str,
    *,
    flags: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    sid = str(summary_id or "").strip()
    msg = str(reason or "").strip() or "account_status_summary inspection failed"
    if not sid:
        raise ValueError("summary_id is required")
    ensure_supabase_config()

    current = await _fetch_summary_by_id(sid)
    if not current:
        raise RuntimeError(f"account_status_summary not found: {sid}")

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
        f"/rest/v1/{ACCOUNT_STATUS_SUMMARIES_TABLE}",
        json=patch_body,
        params={"id": f"eq.{sid}"},
        prefer="return=representation",
        timeout=8.0,
    )
    if resp.status_code not in (200, 204):
        raise RuntimeError(
            f"account_status_summary fail patch failed: {resp.status_code} {(resp.text or '')[:800]}"
        )
    data = resp.json() if resp.status_code == 200 else []
    if isinstance(data, list) and data:
        return _summary_row(data[0])
    latest = await _fetch_summary_by_id(sid)
    if latest:
        return latest
    raise RuntimeError("account_status_summary fail patch succeeded but row not found")


def extract_account_status_totals(summary_payload: Any) -> Dict[str, int]:
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
    "ACCOUNT_STATUS_SUMMARIES_TABLE",
    "ACCOUNT_STATUS_VERSION",
    "ACCOUNT_STATUS_TIMEZONE",
    "STATUS_DRAFT",
    "STATUS_READY",
    "STATUS_FAILED",
    "ALLOWED_STATUSES",
    "ACCOUNT_STATUS_TOTAL_KEYS",
    "normalize_account_status_payload",
    "build_account_status_source_hash",
    "upsert_account_status_draft",
    "fetch_latest_account_status_summary",
    "fetch_latest_ready_account_status_summary",
    "promote_account_status_summary",
    "fail_account_status_summary",
    "extract_account_status_totals",
]
