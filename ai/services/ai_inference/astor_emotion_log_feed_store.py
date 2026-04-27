
# -*- coding: utf-8 -*-
"""Storage helpers for ASTOR EmotionLog feed summary artifacts.

Purpose
-------
`friend_emotion_feed` を source log としながら、EmotionLog の viewer 単位 feed を
`public.friend_feed_summaries` に DRAFT / READY artifact として保存・取得する。

Scope (Phase 1)
---------------
- per-viewer EmotionLog feed summary の保存
- latest READY summary の取得
- inspection 後の READY promote / failed mark
- payload から items を安全に取り出す
- source_hash の deterministic 計算

Design notes
------------
- EmotionLog feed は viewer 単位の受信 surface なので global board ではなく per-viewer artifact
- request / accept / reject / cancel / remove / mute は transactional state なのでここでは扱わない
- `friend_emotion_feed` の semantics（viewer 別 materialization）を壊さずに national artifact 化する
- `timeLabel` は保存時に焼かず、publish 時に後付けする
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

logger = logging.getLogger("astor_emotion_log_feed_store")


FRIEND_FEED_SUMMARIES_TABLE = (
    os.getenv("ASTOR_EMOTION_LOG_FEED_SUMMARIES_TABLE")
    or os.getenv("EMOTION_LOG_FEED_SUMMARIES_TABLE")
    or os.getenv("ASTOR_FRIEND_FEED_SUMMARIES_TABLE")
    or os.getenv("FRIEND_FEED_SUMMARIES_TABLE")
    or "friend_feed_summaries"
).strip() or "friend_feed_summaries"
FRIEND_FEED_SUMMARIES_READ_TABLE = (
    os.getenv("ASTOR_EMOTION_LOG_FEED_SUMMARIES_READ_TABLE")
    or os.getenv("EMOTION_LOG_FEED_SUMMARIES_READ_TABLE")
    or os.getenv("COCOLON_EMOTION_LOG_FEED_SUMMARIES_READ_TABLE")
    or os.getenv("ASTOR_FRIEND_FEED_SUMMARIES_READ_TABLE")
    or os.getenv("FRIEND_FEED_SUMMARIES_READ_TABLE")
    or os.getenv("COCOLON_FRIEND_FEED_SUMMARIES_READ_TABLE")
    or "emotion_log_feed_summaries"
).strip() or "emotion_log_feed_summaries"

FRIEND_FEED_VERSION = "friend_feed.v1"

# Canonical aliases for the current EmotionLog feed implementation.
EMOTION_LOG_FEED_SUMMARIES_TABLE = FRIEND_FEED_SUMMARIES_TABLE
EMOTION_LOG_FEED_SUMMARIES_READ_TABLE = FRIEND_FEED_SUMMARIES_READ_TABLE
EMOTION_LOG_FEED_VERSION = FRIEND_FEED_VERSION

STATUS_DRAFT = "draft"
STATUS_READY = "ready"
STATUS_FAILED = "failed"
ALLOWED_STATUSES = {
    STATUS_DRAFT,
    STATUS_READY,
    STATUS_FAILED,
}

try:
    FRIEND_FEED_MAX_ITEMS = int(
        os.getenv(
            "ASTOR_EMOTION_LOG_FEED_MAX_ITEMS",
            os.getenv("ASTOR_FRIEND_FEED_MAX_ITEMS", "20"),
        )
        or "20"
    )
except Exception:
    FRIEND_FEED_MAX_ITEMS = 20

EMOTION_LOG_FEED_MAX_ITEMS = FRIEND_FEED_MAX_ITEMS

ALLOWED_STRENGTHS = {"weak", "medium", "strong"}


def _now_iso_z() -> str:
    return (
        datetime.now(timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )


def _canonical_viewer_user_id(value: Any) -> str:
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


def _canonical_strength(value: Any) -> Optional[str]:
    s = str(value or "").strip().lower()
    if not s:
        return None
    return s if s in ALLOWED_STRENGTHS else None


def _normalize_emotion_item(raw: Any) -> Optional[Dict[str, Any]]:
    if not isinstance(raw, dict):
        return None
    emotion_type = str(raw.get("type") or raw.get("emotion") or "").strip()
    if not emotion_type:
        return None
    out: Dict[str, Any] = {"type": emotion_type}
    strength = _canonical_strength(raw.get("strength"))
    if strength:
        out["strength"] = strength
    return out


def _normalize_feed_item(raw: Any) -> Optional[Dict[str, Any]]:
    if not isinstance(raw, dict):
        return None

    item_id = str(raw.get("id") or "").strip()
    owner_user_id = str(raw.get("owner_user_id") or raw.get("ownerUserId") or "").strip()
    owner_name = str(raw.get("owner_name") or raw.get("ownerName") or "").strip()
    created_at = str(raw.get("created_at") or raw.get("createdAt") or "").strip()

    raw_emotions = raw.get("items")
    if not isinstance(raw_emotions, list):
        raw_emotions = []

    emotions: List[Dict[str, Any]] = []
    for e in raw_emotions:
        norm = _normalize_emotion_item(e)
        if norm is not None:
            emotions.append(norm)

    if not item_id:
        return None
    if not owner_name:
        owner_name = "Friend"
    if not created_at:
        created_at = _now_iso_z()

    return {
        "id": item_id,
        "owner_user_id": owner_user_id or None,
        "owner_name": owner_name,
        "items": emotions,
        "created_at": created_at,
    }


def _sort_feed_items(items: Iterable[Dict[str, Any]]) -> List[Dict[str, Any]]:
    normalized: List[Dict[str, Any]] = []
    for raw in items or []:
        item = _normalize_feed_item(raw)
        if item is not None:
            normalized.append(item)

    normalized.sort(
        key=lambda x: (
            str(x.get("created_at") or ""),
            str(x.get("id") or ""),
        ),
        reverse=True,
    )
    if FRIEND_FEED_MAX_ITEMS > 0:
        normalized = normalized[:FRIEND_FEED_MAX_ITEMS]
    return normalized


def normalize_friend_feed_payload(
    viewer_user_id: str,
    payload: Optional[Dict[str, Any]],
) -> Dict[str, Any]:
    """Normalize an EmotionLog feed payload into the canonical v1 shape."""
    viewer_id = _canonical_viewer_user_id(viewer_user_id) or _canonical_viewer_user_id(
        (payload or {}).get("viewer_user_id")
    )
    if not viewer_id:
        raise ValueError("viewer_user_id is required")

    base = payload if isinstance(payload, dict) else {}
    normalized = _json_ready(base)
    if not isinstance(normalized, dict):
        normalized = {}

    raw_items = normalized.get("items")
    if not isinstance(raw_items, list):
        raw_items = []

    items = _sort_feed_items(raw_items)
    latest_created_at = str(items[0].get("created_at") or "").strip() if items else None

    counts = normalized.get("counts") if isinstance(normalized.get("counts"), dict) else {}
    counts = _json_ready(counts)
    if not isinstance(counts, dict):
        counts = {}
    counts["item_count"] = len(items)

    normalized["version"] = (
        str(normalized.get("version") or FRIEND_FEED_VERSION).strip()
        or FRIEND_FEED_VERSION
    )
    normalized["viewer_user_id"] = viewer_id
    normalized["generated_at"] = (
        str(normalized.get("generated_at") or _now_iso_z()).strip() or _now_iso_z()
    )
    normalized["items"] = items
    normalized["counts"] = counts
    normalized["latest_created_at"] = latest_created_at
    return normalized


def build_friend_feed_source_hash(viewer_user_id: str, payload: Dict[str, Any]) -> str:
    """Build a deterministic source hash for a friend feed payload.

    We intentionally exclude volatile metadata such as `generated_at` so that
    identical feed contents produce the same hash.
    """
    normalized = normalize_friend_feed_payload(viewer_user_id, payload)
    basis = {
        "version": str(normalized.get("version") or FRIEND_FEED_VERSION),
        "viewer_user_id": str(normalized.get("viewer_user_id") or ""),
        "items": normalized.get("items") if isinstance(normalized.get("items"), list) else [],
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
        "viewer_user_id": _canonical_viewer_user_id(row.get("viewer_user_id")),
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
        f"/rest/v1/{FRIEND_FEED_SUMMARIES_READ_TABLE}",
        params={
            "select": "id,viewer_user_id,status,payload,source_hash,version,meta,created_at,updated_at,published_at",
            "id": f"eq.{sid}",
            "limit": "1",
        },
        timeout=8.0,
    )
    if resp.status_code not in (200, 206):
        raise RuntimeError(
            f"fetch friend_feed_summary by id failed: {resp.status_code} {(resp.text or '')[:800]}"
        )
    data = resp.json()
    if isinstance(data, list) and data:
        return _summary_row(data[0])
    return None


async def _fetch_summary_by_viewer_and_source_hash(
    viewer_user_id: str,
    source_hash: str,
) -> Optional[Dict[str, Any]]:
    viewer_id = _canonical_viewer_user_id(viewer_user_id)
    sh = str(source_hash or "").strip()
    if not viewer_id or not sh:
        return None
    ensure_supabase_config()
    resp = await sb_get(
        f"/rest/v1/{FRIEND_FEED_SUMMARIES_READ_TABLE}",
        params={
            "select": "id,viewer_user_id,status,payload,source_hash,version,meta,created_at,updated_at,published_at",
            "viewer_user_id": f"eq.{viewer_id}",
            "source_hash": f"eq.{sh}",
            "order": "updated_at.desc,id.desc",
            "limit": "1",
        },
        timeout=8.0,
    )
    if resp.status_code not in (200, 206):
        raise RuntimeError(
            f"fetch friend_feed_summary by source_hash failed: {resp.status_code} {(resp.text or '')[:800]}"
        )
    data = resp.json()
    if isinstance(data, list) and data:
        return _summary_row(data[0])
    return None


async def upsert_friend_feed_draft(
    viewer_user_id: str,
    payload: Dict[str, Any],
    meta: Optional[Dict[str, Any]] = None,
    *,
    version: int = 1,
) -> Dict[str, Any]:
    """Create or update an EmotionLog feed summary artifact.

    Behavior
    --------
    - same viewer_user_id + source_hash already exists and is READY:
        keep READY, refresh payload/meta/updated_at only
    - same viewer_user_id + source_hash already exists and is DRAFT/FAILED:
        move to DRAFT and update payload/meta/updated_at
    - otherwise:
        insert a new row (status defaults to draft via DB default)
    """
    viewer_id = _canonical_viewer_user_id(viewer_user_id)
    if not viewer_id:
        raise ValueError("viewer_user_id is required")

    ensure_supabase_config()

    normalized_payload = normalize_friend_feed_payload(viewer_id, payload)
    meta_payload = _json_ready(meta or {})
    if not isinstance(meta_payload, dict):
        meta_payload = {}
    now_iso = _now_iso_z()
    source_hash = build_friend_feed_source_hash(viewer_id, normalized_payload)

    existing = await _fetch_summary_by_viewer_and_source_hash(viewer_id, source_hash)
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
            f"/rest/v1/{FRIEND_FEED_SUMMARIES_TABLE}",
            json=patch_body,
            params={"id": f"eq.{existing['id']}"},
            prefer="return=representation",
            timeout=8.0,
        )
        if resp.status_code not in (200, 204):
            raise RuntimeError(
                f"friend_feed_summary patch failed: {resp.status_code} {(resp.text or '')[:800]}"
            )
        data = resp.json() if resp.status_code == 200 else []
        if isinstance(data, list) and data:
            return _summary_row(data[0])
        latest = await _fetch_summary_by_id(existing["id"])
        if latest:
            return latest
        raise RuntimeError("friend_feed_summary patch succeeded but row not found")

    insert_row: Dict[str, Any] = {
        "viewer_user_id": viewer_id,
        "payload": normalized_payload,
        "source_hash": source_hash,
        "version": int(version or 1),
        "meta": meta_payload,
        "updated_at": now_iso,
    }
    resp = await sb_post(
        f"/rest/v1/{FRIEND_FEED_SUMMARIES_TABLE}",
        json=insert_row,
        params={"on_conflict": "viewer_user_id,source_hash"},
        prefer="resolution=merge-duplicates,return=representation",
        timeout=8.0,
    )
    if resp.status_code not in (200, 201, 204):
        raise RuntimeError(
            f"friend_feed_summary insert failed: {resp.status_code} {(resp.text or '')[:800]}"
        )
    data = resp.json() if resp.status_code in (200, 201) else []
    if isinstance(data, list) and data:
        row = _summary_row(data[0])
        if row:
            return row

    latest = await _fetch_summary_by_viewer_and_source_hash(viewer_id, source_hash)
    if latest:
        return latest
    raise RuntimeError("friend_feed_summary insert succeeded but row not found")


async def fetch_latest_friend_feed_summary(
    viewer_user_id: str,
    statuses: Optional[Iterable[str]] = None,
) -> Optional[Dict[str, Any]]:
    viewer_id = _canonical_viewer_user_id(viewer_user_id)
    if not viewer_id:
        return None
    ensure_supabase_config()

    params: Dict[str, str] = {
        "select": "id,viewer_user_id,status,payload,source_hash,version,meta,created_at,updated_at,published_at",
        "viewer_user_id": f"eq.{viewer_id}",
        "order": "updated_at.desc,id.desc",
        "limit": "1",
    }
    normalized_statuses = _normalize_statuses(statuses)
    if len(normalized_statuses) == 1:
        params["status"] = f"eq.{normalized_statuses[0]}"
    elif len(normalized_statuses) > 1:
        params["status"] = _in_list(normalized_statuses)

    resp = await sb_get(
        f"/rest/v1/{FRIEND_FEED_SUMMARIES_READ_TABLE}",
        params=params,
        timeout=8.0,
    )
    if resp.status_code not in (200, 206):
        raise RuntimeError(
            f"fetch latest friend_feed_summary failed: {resp.status_code} {(resp.text or '')[:800]}"
        )
    data = resp.json()
    if isinstance(data, list) and data:
        return _summary_row(data[0])
    return None


async def fetch_latest_ready_friend_feed_summary(viewer_user_id: str) -> Optional[Dict[str, Any]]:
    return await fetch_latest_friend_feed_summary(viewer_user_id, statuses=[STATUS_READY])


async def promote_friend_feed_summary(
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
        raise RuntimeError(f"friend_feed_summary not found: {sid}")

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
        f"/rest/v1/{FRIEND_FEED_SUMMARIES_TABLE}",
        json=patch_body,
        params={"id": f"eq.{sid}"},
        prefer="return=representation",
        timeout=8.0,
    )
    if resp.status_code not in (200, 204):
        raise RuntimeError(
            f"friend_feed_summary promote failed: {resp.status_code} {(resp.text or '')[:800]}"
        )
    data = resp.json() if resp.status_code == 200 else []
    if isinstance(data, list) and data:
        return _summary_row(data[0])
    latest = await _fetch_summary_by_id(sid)
    if latest:
        return latest
    raise RuntimeError("friend_feed_summary promote succeeded but row not found")


async def fail_friend_feed_summary(
    summary_id: str,
    reason: str,
    *,
    flags: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    sid = str(summary_id or "").strip()
    msg = str(reason or "").strip() or "friend_feed_summary inspection failed"
    if not sid:
        raise ValueError("summary_id is required")
    ensure_supabase_config()

    current = await _fetch_summary_by_id(sid)
    if not current:
        raise RuntimeError(f"friend_feed_summary not found: {sid}")

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
        f"/rest/v1/{FRIEND_FEED_SUMMARIES_TABLE}",
        json=patch_body,
        params={"id": f"eq.{sid}"},
        prefer="return=representation",
        timeout=8.0,
    )
    if resp.status_code not in (200, 204):
        raise RuntimeError(
            f"friend_feed_summary fail patch failed: {resp.status_code} {(resp.text or '')[:800]}"
        )
    data = resp.json() if resp.status_code == 200 else []
    if isinstance(data, list) and data:
        return _summary_row(data[0])
    latest = await _fetch_summary_by_id(sid)
    if latest:
        return latest
    raise RuntimeError("friend_feed_summary fail patch succeeded but row not found")


def select_friend_feed_items(summary_payload: Any) -> List[Dict[str, Any]]:
    """Return normalized EmotionLog items from either a summary row or a raw payload."""
    if isinstance(summary_payload, dict) and isinstance(summary_payload.get("payload"), dict):
        payload = summary_payload.get("payload") or {}
    elif isinstance(summary_payload, dict):
        payload = summary_payload
    else:
        return []

    raw_items = payload.get("items")
    if not isinstance(raw_items, list):
        return []
    return _sort_feed_items(raw_items)



# Canonical EmotionLog-named aliases. The physical table/function names remain
# legacy-compatible so existing workers and migrations keep working.
normalize_emotion_log_feed_payload = normalize_friend_feed_payload
build_emotion_log_feed_source_hash = build_friend_feed_source_hash
upsert_emotion_log_feed_draft = upsert_friend_feed_draft
fetch_latest_emotion_log_feed_summary = fetch_latest_friend_feed_summary
fetch_latest_ready_emotion_log_feed_summary = fetch_latest_ready_friend_feed_summary
promote_emotion_log_feed_summary = promote_friend_feed_summary
fail_emotion_log_feed_summary = fail_friend_feed_summary
select_emotion_log_feed_items = select_friend_feed_items

__all__ = [
    "FRIEND_FEED_SUMMARIES_TABLE",
    "FRIEND_FEED_SUMMARIES_READ_TABLE",
    "EMOTION_LOG_FEED_SUMMARIES_TABLE",
    "EMOTION_LOG_FEED_SUMMARIES_READ_TABLE",
    "FRIEND_FEED_VERSION",
    "EMOTION_LOG_FEED_VERSION",
    "STATUS_DRAFT",
    "STATUS_READY",
    "STATUS_FAILED",
    "ALLOWED_STATUSES",
    "FRIEND_FEED_MAX_ITEMS",
    "EMOTION_LOG_FEED_MAX_ITEMS",
    "ALLOWED_STRENGTHS",
    "normalize_friend_feed_payload",
    "build_friend_feed_source_hash",
    "upsert_friend_feed_draft",
    "fetch_latest_friend_feed_summary",
    "fetch_latest_ready_friend_feed_summary",
    "promote_friend_feed_summary",
    "fail_friend_feed_summary",
    "select_friend_feed_items",
    "normalize_emotion_log_feed_payload",
    "build_emotion_log_feed_source_hash",
    "upsert_emotion_log_feed_draft",
    "fetch_latest_emotion_log_feed_summary",
    "fetch_latest_ready_emotion_log_feed_summary",
    "promote_emotion_log_feed_summary",
    "fail_emotion_log_feed_summary",
    "select_emotion_log_feed_items",
]
