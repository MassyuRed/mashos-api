# -*- coding: utf-8 -*-
"""EmotionLog feed generation kernel for ASTOR (Phase 1).

Purpose
-------
既存の `friend_emotion_feed` を source log として、そのまま viewer 単位の
EmotionLog feed summary payload を生成する。

Phase 1 policy
--------------
- feed source は `friend_emotion_feed` をそのまま利用する（物理テーブル名は legacy 維持）
- snapshot から再構成しない
- request / accept / reject / cancel / remove / mute はここでは扱わない
- push notification は live のまま残し、本 module は表示用 feed payload だけを作る
- DRAFT 保存 / READY 昇格は `astor_emotion_log_feed_store.py` 側が担当する

Design notes
------------
- emotion submit 時点で viewer 別 materialization が完了しているため、
  EmotionLog feed の nationalization は source log -> summary artifact の形が最も安全
- 保存時に `timeLabel` は焼かず、公開 API 側で整形する
- viewer 単位 summary なので global board ではない
"""

from __future__ import annotations

import json
import logging
import os
from typing import Any, Dict, Iterable, List, Mapping

from supabase_client import ensure_supabase_config, sb_get
from astor_emotion_log_feed_store import (
    EMOTION_LOG_FEED_MAX_ITEMS,
    EMOTION_LOG_FEED_VERSION,
    normalize_emotion_log_feed_payload,
)

# Backward-compatible local aliases for legacy imports / callers.
FRIEND_FEED_MAX_ITEMS = EMOTION_LOG_FEED_MAX_ITEMS
FRIEND_FEED_VERSION = EMOTION_LOG_FEED_VERSION
normalize_friend_feed_payload = normalize_emotion_log_feed_payload

logger = logging.getLogger("astor_emotion_log_feed_kernel")


# The source table is SELECT-only in this kernel. Use the current bridge view by
# default; legacy physical table names remain available via explicit READ envs.
FRIEND_FEED_SOURCE_TABLE = (
    os.getenv("ASTOR_EMOTION_LOG_FEED_SOURCE_READ_TABLE")
    or os.getenv("EMOTION_LOG_FEED_SOURCE_READ_TABLE")
    or os.getenv("COCOLON_EMOTION_LOG_FEED_READ_TABLE")
    or os.getenv("ASTOR_FRIEND_FEED_SOURCE_READ_TABLE")
    or os.getenv("FRIEND_FEED_SOURCE_READ_TABLE")
    or os.getenv("COCOLON_FRIEND_EMOTION_FEED_READ_TABLE")
    or "emotion_log_feed"
).strip() or "emotion_log_feed"

FRIEND_FEED_TIMEZONE = (
    os.getenv("ASTOR_EMOTION_LOG_FEED_TIMEZONE")
    or os.getenv("EMOTION_LOG_FEED_TIMEZONE")
    or os.getenv("ASTOR_FRIEND_FEED_TIMEZONE")
    or os.getenv("FRIEND_FEED_TIMEZONE")
    or "Asia/Tokyo"
).strip() or "Asia/Tokyo"

# Canonical aliases for EmotionLog naming.
EMOTION_LOG_FEED_SOURCE_TABLE = FRIEND_FEED_SOURCE_TABLE
EMOTION_LOG_FEED_TIMEZONE = FRIEND_FEED_TIMEZONE


def _canonical_viewer_user_id(value: Any) -> str:
    return str(value or "").strip()


def _canonical_owner_user_id(value: Any) -> str:
    return str(value or "").strip()


def _canonical_owner_name(value: Any) -> str:
    s = str(value or "").strip()
    return s or "Friend"


def _canonical_created_at(value: Any) -> str:
    return str(value or "").strip()


def _coerce_items(value: Any) -> List[Dict[str, Any]]:
    if isinstance(value, list):
        return [x for x in value if isinstance(x, dict)]
    if isinstance(value, str):
        s = value.strip()
        if not s:
            return []
        try:
            data = json.loads(s)
        except Exception:
            return []
        if isinstance(data, list):
            return [x for x in data if isinstance(x, dict)]
    return []


def _normalize_source_row(row: Mapping[str, Any]) -> Dict[str, Any]:
    src = row if isinstance(row, Mapping) else {}
    return {
        "id": str(src.get("id") or "").strip(),
        "owner_user_id": _canonical_owner_user_id(src.get("owner_user_id")),
        "owner_name": _canonical_owner_name(src.get("owner_name")),
        "items": _coerce_items(src.get("items")),
        "created_at": _canonical_created_at(src.get("created_at")),
    }


async def _fetch_friend_feed_rows(viewer_user_id: str, *, limit: int = FRIEND_FEED_MAX_ITEMS) -> List[Dict[str, Any]]:
    viewer_id = _canonical_viewer_user_id(viewer_user_id)
    if not viewer_id:
        raise ValueError("viewer_user_id is required")

    ensure_supabase_config()
    p_limit = max(1, int(limit or FRIEND_FEED_MAX_ITEMS or 20))

    resp = await sb_get(
        f"/rest/v1/{EMOTION_LOG_FEED_SOURCE_TABLE}",
        params={
            "select": "id,viewer_user_id,owner_user_id,owner_name,items,created_at",
            "viewer_user_id": f"eq.{viewer_id}",
            "order": "created_at.desc,id.desc",
            "limit": str(p_limit),
        },
        timeout=8.0,
    )
    if resp.status_code not in (200, 206):
        body = (resp.text or "")[:1500]
        logger.error(
            "friend feed source fetch failed: table=%s viewer=%s status=%s body=%s",
            EMOTION_LOG_FEED_SOURCE_TABLE,
            viewer_id,
            resp.status_code,
            body,
        )
        raise RuntimeError(f"emotion log feed source fetch failed: {EMOTION_LOG_FEED_SOURCE_TABLE} ({resp.status_code})")

    try:
        data = resp.json()
    except Exception as exc:
        logger.error(
            "friend feed source returned non-json: table=%s viewer=%s err=%s",
            EMOTION_LOG_FEED_SOURCE_TABLE,
            viewer_id,
            exc,
        )
        raise RuntimeError(f"friend feed source returned invalid json: {FRIEND_FEED_SOURCE_TABLE}") from exc

    if not isinstance(data, list):
        return []
    return [_normalize_source_row(row) for row in data if isinstance(row, dict)]


def _build_friend_feed_payload(viewer_user_id: str, rows: Iterable[Mapping[str, Any]]) -> Dict[str, Any]:
    viewer_id = _canonical_viewer_user_id(viewer_user_id)
    if not viewer_id:
        raise ValueError("viewer_user_id is required")

    raw_items: List[Dict[str, Any]] = []
    for row in rows or []:
        if not isinstance(row, Mapping):
            continue
        raw_items.append(
            {
                "id": str(row.get("id") or "").strip(),
                "owner_user_id": _canonical_owner_user_id(row.get("owner_user_id")),
                "owner_name": _canonical_owner_name(row.get("owner_name")),
                "items": _coerce_items(row.get("items")),
                "created_at": _canonical_created_at(row.get("created_at")),
            }
        )

    payload = {
        "version": EMOTION_LOG_FEED_VERSION,
        "viewer_user_id": viewer_id,
        "timezone": EMOTION_LOG_FEED_TIMEZONE,
        "items": raw_items,
        "meta": {
            "kernel": "emotion_log_feed_source_v1",
            "source_table": EMOTION_LOG_FEED_SOURCE_TABLE,
            "limit": int(FRIEND_FEED_MAX_ITEMS or 20),
        },
    }
    return normalize_friend_feed_payload(viewer_id, payload)


async def generate_friend_feed(viewer_user_id: str, *, limit: int = FRIEND_FEED_MAX_ITEMS) -> Dict[str, Any]:
    """Generate a normalized friend feed payload for one viewer."""
    viewer_id = _canonical_viewer_user_id(viewer_user_id)
    if not viewer_id:
        raise ValueError("viewer_user_id is required")

    rows = await _fetch_friend_feed_rows(viewer_id, limit=limit)
    return _build_friend_feed_payload(viewer_id, rows)


async def generate_multiple_friend_feeds(
    viewer_user_ids: Iterable[str],
    *,
    limit: int = FRIEND_FEED_MAX_ITEMS,
) -> Dict[str, Dict[str, Any]]:
    """Generate normalized friend feed payloads for multiple viewers sequentially."""
    out: Dict[str, Dict[str, Any]] = {}
    seen = set()
    for raw in viewer_user_ids or []:
        viewer_id = _canonical_viewer_user_id(raw)
        if not viewer_id or viewer_id in seen:
            continue
        seen.add(viewer_id)
        out[viewer_id] = await generate_friend_feed(viewer_id, limit=limit)
    return out



async def generate_emotion_log_feed(viewer_user_id: str, *, limit: int = EMOTION_LOG_FEED_MAX_ITEMS) -> Dict[str, Any]:
    """Generate a normalized EmotionLog feed payload for one viewer."""
    return await generate_friend_feed(viewer_user_id, limit=limit)


async def generate_multiple_emotion_log_feeds(
    viewer_user_ids: Iterable[str],
    *,
    limit: int = EMOTION_LOG_FEED_MAX_ITEMS,
) -> Dict[str, Dict[str, Any]]:
    """Generate normalized EmotionLog feed payloads for multiple viewers sequentially."""
    return await generate_multiple_friend_feeds(viewer_user_ids, limit=limit)


__all__ = [
    "FRIEND_FEED_SOURCE_TABLE",
    "FRIEND_FEED_TIMEZONE",
    "FRIEND_FEED_MAX_ITEMS",
    "FRIEND_FEED_VERSION",
    "EMOTION_LOG_FEED_SOURCE_TABLE",
    "EMOTION_LOG_FEED_TIMEZONE",
    "EMOTION_LOG_FEED_MAX_ITEMS",
    "EMOTION_LOG_FEED_VERSION",
    "generate_friend_feed",
    "generate_multiple_friend_feeds",
    "generate_emotion_log_feed",
    "generate_multiple_emotion_log_feeds",
]
