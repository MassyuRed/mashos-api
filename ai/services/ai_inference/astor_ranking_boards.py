# -*- coding: utf-8 -*-
"""Storage helpers for ASTOR ranking board artifacts.

Purpose
-------
既存の Ranking RPC kernel をそのまま使いながら、結果を
`public.ranking_boards` に DRAFT / READY artifact として保存・取得する。

Scope (Phase 1)
---------------
- global ranking board の保存
- latest READY board の取得
- inspection 後の READY promote / failed mark
- payload から range 別の rows を安全に取り出す
- source_hash の deterministic 計算

Design notes
------------
- Ranking は cross-user artifact なので `analysis_results` には入れない
- Phase 1 は generic products table ではなく専用 `ranking_boards` を使う
- board payload は machine-readable raw rows を保存する
- display_name / visibility などの presentation 情報は publish 時に後付けする
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

logger = logging.getLogger("astor_ranking_boards")


RANKING_BOARDS_TABLE = (
    os.getenv("ASTOR_RANKING_BOARDS_TABLE")
    or os.getenv("RANKING_BOARDS_TABLE")
    or "ranking_boards"
).strip() or "ranking_boards"

RANKING_BOARD_VERSION = "ranking_board.v1"
RANKING_BOARD_TIMEZONE = os.getenv("ASTOR_RANKING_TIMEZONE", "Asia/Tokyo") or "Asia/Tokyo"

BOARD_STATUS_DRAFT = "draft"
BOARD_STATUS_READY = "ready"
BOARD_STATUS_FAILED = "failed"
ALLOWED_BOARD_STATUSES = {
    BOARD_STATUS_DRAFT,
    BOARD_STATUS_READY,
    BOARD_STATUS_FAILED,
}

_DEFAULT_RANGE_KEYS: Sequence[str] = ("day", "week", "month", "year")


def _now_iso_z() -> str:
    return (
        datetime.now(timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )


def _canonical_metric_key(value: Any) -> str:
    return str(value or "").strip()


def _canonical_range_key(value: Any) -> str:
    s = str(value or "").strip().lower()
    if s in ("日",):
        return "day"
    if s in ("週",):
        return "week"
    if s in ("月",):
        return "month"
    if s in ("年",):
        return "year"
    return s or "week"


def _canonical_status(value: Any) -> str:
    s = str(value or "").strip().lower()
    if s in ALLOWED_BOARD_STATUSES:
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


def _normalize_rows(rows: Any) -> List[Dict[str, Any]]:
    if not isinstance(rows, list):
        return []
    out: List[Dict[str, Any]] = []
    for item in rows:
        if isinstance(item, dict):
            out.append(_json_ready(item))
    return out


def normalize_board_payload(metric_key: str, payload: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """Normalize a ranking board payload into the canonical v1 shape."""
    mk = _canonical_metric_key(metric_key)
    base = payload if isinstance(payload, dict) else {}

    ranges_in = base.get("ranges") if isinstance(base.get("ranges"), dict) else {}
    ranges_out: Dict[str, List[Dict[str, Any]]] = {}

    for rk in _DEFAULT_RANGE_KEYS:
        ranges_out[rk] = _normalize_rows(ranges_in.get(rk))

    for raw_key, raw_rows in ranges_in.items():
        ck = _canonical_range_key(raw_key)
        if not ck or ck in ranges_out:
            continue
        ranges_out[ck] = _normalize_rows(raw_rows)

    normalized = _json_ready(base)
    if not isinstance(normalized, dict):
        normalized = {}

    normalized["version"] = str(normalized.get("version") or RANKING_BOARD_VERSION).strip() or RANKING_BOARD_VERSION
    normalized["metric_key"] = mk
    normalized["timezone"] = str(normalized.get("timezone") or RANKING_BOARD_TIMEZONE).strip() or RANKING_BOARD_TIMEZONE
    normalized["generated_at"] = str(normalized.get("generated_at") or _now_iso_z()).strip() or _now_iso_z()
    normalized["ranges"] = ranges_out
    return normalized


def build_ranking_board_source_hash(metric_key: str, payload: Dict[str, Any]) -> str:
    """Build a deterministic source hash for a board payload.

    We intentionally exclude volatile metadata such as `generated_at` so that
    identical ranking results produce the same hash.
    """
    mk = _canonical_metric_key(metric_key)
    p = normalize_board_payload(mk, payload)
    basis = {
        "metric_key": mk,
        "version": str(p.get("version") or RANKING_BOARD_VERSION),
        "timezone": str(p.get("timezone") or RANKING_BOARD_TIMEZONE),
        "ranges": p.get("ranges") if isinstance(p.get("ranges"), dict) else {},
    }
    raw = json.dumps(basis, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _board_row(row: Dict[str, Any]) -> Dict[str, Any]:
    if not isinstance(row, dict):
        return {}
    payload = row.get("payload") if isinstance(row.get("payload"), dict) else {}
    meta = row.get("meta") if isinstance(row.get("meta"), dict) else {}
    return {
        "id": str(row.get("id") or "").strip(),
        "metric_key": _canonical_metric_key(row.get("metric_key")),
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


async def _fetch_board_by_id(board_id: str) -> Optional[Dict[str, Any]]:
    bid = str(board_id or "").strip()
    if not bid:
        return None
    ensure_supabase_config()
    resp = await sb_get(
        f"/rest/v1/{RANKING_BOARDS_TABLE}",
        params={
            "select": "id,metric_key,status,payload,source_hash,version,meta,created_at,updated_at,published_at",
            "id": f"eq.{bid}",
            "limit": "1",
        },
        timeout=8.0,
    )
    if resp.status_code not in (200, 206):
        raise RuntimeError(
            f"fetch ranking_board by id failed: {resp.status_code} {(resp.text or '')[:800]}"
        )
    data = resp.json()
    if isinstance(data, list) and data:
        return _board_row(data[0])
    return None


async def _fetch_board_by_metric_and_source_hash(metric_key: str, source_hash: str) -> Optional[Dict[str, Any]]:
    mk = _canonical_metric_key(metric_key)
    sh = str(source_hash or "").strip()
    if not mk or not sh:
        return None
    ensure_supabase_config()
    resp = await sb_get(
        f"/rest/v1/{RANKING_BOARDS_TABLE}",
        params={
            "select": "id,metric_key,status,payload,source_hash,version,meta,created_at,updated_at,published_at",
            "metric_key": f"eq.{mk}",
            "source_hash": f"eq.{sh}",
            "order": "updated_at.desc,id.desc",
            "limit": "1",
        },
        timeout=8.0,
    )
    if resp.status_code not in (200, 206):
        raise RuntimeError(
            f"fetch ranking_board by source_hash failed: {resp.status_code} {(resp.text or '')[:800]}"
        )
    data = resp.json()
    if isinstance(data, list) and data:
        return _board_row(data[0])
    return None


async def upsert_ranking_board_draft(
    metric_key: str,
    payload: Dict[str, Any],
    meta: Optional[Dict[str, Any]] = None,
    *,
    version: int = 1,
) -> Dict[str, Any]:
    """Create or update a ranking board artifact.

    Behavior
    --------
    - same metric_key + source_hash already exists and is READY:
        keep READY, refresh payload/meta/updated_at only
    - same metric_key + source_hash already exists and is DRAFT/FAILED:
        move to DRAFT and update payload/meta/updated_at
    - otherwise:
        insert a new row (status defaults to draft via DB default)
    """
    mk = _canonical_metric_key(metric_key)
    if not mk:
        raise ValueError("metric_key is required")

    ensure_supabase_config()

    normalized_payload = normalize_board_payload(mk, payload)
    meta_payload = _json_ready(meta or {})
    if not isinstance(meta_payload, dict):
        meta_payload = {}
    now_iso = _now_iso_z()
    source_hash = build_ranking_board_source_hash(mk, normalized_payload)

    existing = await _fetch_board_by_metric_and_source_hash(mk, source_hash)
    if existing:
        patch_body: Dict[str, Any] = {
            "payload": normalized_payload,
            "meta": meta_payload,
            "version": int(version or 1),
            "source_hash": source_hash,
            "updated_at": now_iso,
        }
        if existing.get("status") != BOARD_STATUS_READY:
            patch_body["status"] = BOARD_STATUS_DRAFT
            patch_body["published_at"] = None
        resp = await sb_patch(
            f"/rest/v1/{RANKING_BOARDS_TABLE}",
            json=patch_body,
            params={"id": f"eq.{existing['id']}"},
            prefer="return=representation",
            timeout=8.0,
        )
        if resp.status_code not in (200, 204):
            raise RuntimeError(
                f"ranking_board patch failed: {resp.status_code} {(resp.text or '')[:800]}"
            )
        data = resp.json() if resp.status_code == 200 else []
        if isinstance(data, list) and data:
            return _board_row(data[0])
        latest = await _fetch_board_by_id(existing["id"])
        if latest:
            return latest
        raise RuntimeError("ranking_board patch succeeded but row not found")

    insert_row: Dict[str, Any] = {
        "metric_key": mk,
        "payload": normalized_payload,
        "source_hash": source_hash,
        "version": int(version or 1),
        "meta": meta_payload,
        "updated_at": now_iso,
    }
    resp = await sb_post(
        f"/rest/v1/{RANKING_BOARDS_TABLE}",
        json=insert_row,
        params={"on_conflict": "metric_key,source_hash"},
        prefer="resolution=merge-duplicates,return=representation",
        timeout=8.0,
    )
    if resp.status_code not in (200, 201, 204):
        raise RuntimeError(
            f"ranking_board insert failed: {resp.status_code} {(resp.text or '')[:800]}"
        )
    data = resp.json() if resp.status_code in (200, 201) else []
    if isinstance(data, list) and data:
        row = _board_row(data[0])
        # merge-duplicates on an existing ready row should keep ready.
        if row:
            return row

    latest = await _fetch_board_by_metric_and_source_hash(mk, source_hash)
    if latest:
        return latest
    raise RuntimeError("ranking_board insert succeeded but row not found")


async def fetch_latest_ranking_board(
    metric_key: str,
    statuses: Optional[Iterable[str]] = None,
) -> Optional[Dict[str, Any]]:
    mk = _canonical_metric_key(metric_key)
    if not mk:
        return None
    ensure_supabase_config()

    params: Dict[str, str] = {
        "select": "id,metric_key,status,payload,source_hash,version,meta,created_at,updated_at,published_at",
        "metric_key": f"eq.{mk}",
        "order": "updated_at.desc,id.desc",
        "limit": "1",
    }
    normalized_statuses = _normalize_statuses(statuses)
    if len(normalized_statuses) == 1:
        params["status"] = f"eq.{normalized_statuses[0]}"
    elif len(normalized_statuses) > 1:
        params["status"] = _in_list(normalized_statuses)

    resp = await sb_get(f"/rest/v1/{RANKING_BOARDS_TABLE}", params=params, timeout=8.0)
    if resp.status_code not in (200, 206):
        raise RuntimeError(
            f"fetch latest ranking_board failed: {resp.status_code} {(resp.text or '')[:800]}"
        )
    data = resp.json()
    if isinstance(data, list) and data:
        return _board_row(data[0])
    return None


async def fetch_latest_ready_ranking_board(metric_key: str) -> Optional[Dict[str, Any]]:
    return await fetch_latest_ranking_board(metric_key, statuses=[BOARD_STATUS_READY])


async def promote_ranking_board(
    board_id: str,
    *,
    published_at: Optional[str] = None,
    extra_meta: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    bid = str(board_id or "").strip()
    if not bid:
        raise ValueError("board_id is required")
    ensure_supabase_config()

    current = await _fetch_board_by_id(bid)
    if not current:
        raise RuntimeError(f"ranking_board not found: {bid}")

    merged_meta = dict(current.get("meta") or {})
    if isinstance(extra_meta, dict) and extra_meta:
        merged_meta.update(_json_ready(extra_meta))

    patch_body = {
        "status": BOARD_STATUS_READY,
        "meta": merged_meta,
        "updated_at": _now_iso_z(),
        "published_at": str(published_at or _now_iso_z()).strip() or _now_iso_z(),
    }
    resp = await sb_patch(
        f"/rest/v1/{RANKING_BOARDS_TABLE}",
        json=patch_body,
        params={"id": f"eq.{bid}"},
        prefer="return=representation",
        timeout=8.0,
    )
    if resp.status_code not in (200, 204):
        raise RuntimeError(
            f"ranking_board promote failed: {resp.status_code} {(resp.text or '')[:800]}"
        )
    data = resp.json() if resp.status_code == 200 else []
    if isinstance(data, list) and data:
        return _board_row(data[0])
    latest = await _fetch_board_by_id(bid)
    if latest:
        return latest
    raise RuntimeError("ranking_board promote succeeded but row not found")


async def fail_ranking_board(
    board_id: str,
    reason: str,
    *,
    flags: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    bid = str(board_id or "").strip()
    msg = str(reason or "").strip() or "ranking_board inspection failed"
    if not bid:
        raise ValueError("board_id is required")
    ensure_supabase_config()

    current = await _fetch_board_by_id(bid)
    if not current:
        raise RuntimeError(f"ranking_board not found: {bid}")

    merged_meta = dict(current.get("meta") or {})
    merged_meta["last_error"] = msg
    merged_meta["last_failed_at"] = _now_iso_z()
    if isinstance(flags, dict) and flags:
        merged_meta.setdefault("flags", {})
        flags_map = merged_meta.get("flags") if isinstance(merged_meta.get("flags"), dict) else {}
        flags_map.update(_json_ready(flags))
        merged_meta["flags"] = flags_map

    patch_body = {
        "status": BOARD_STATUS_FAILED,
        "meta": merged_meta,
        "updated_at": _now_iso_z(),
    }
    resp = await sb_patch(
        f"/rest/v1/{RANKING_BOARDS_TABLE}",
        json=patch_body,
        params={"id": f"eq.{bid}"},
        prefer="return=representation",
        timeout=8.0,
    )
    if resp.status_code not in (200, 204):
        raise RuntimeError(
            f"ranking_board fail patch failed: {resp.status_code} {(resp.text or '')[:800]}"
        )
    data = resp.json() if resp.status_code == 200 else []
    if isinstance(data, list) and data:
        return _board_row(data[0])
    latest = await _fetch_board_by_id(bid)
    if latest:
        return latest
    raise RuntimeError("ranking_board fail patch succeeded but row not found")


def select_board_rows(board_payload: Any, range_key: str) -> List[Dict[str, Any]]:
    """Return rows for one range from either a board row or a raw payload."""
    rk = _canonical_range_key(range_key)
    if isinstance(board_payload, dict) and isinstance(board_payload.get("payload"), dict):
        payload = board_payload.get("payload") or {}
    elif isinstance(board_payload, dict):
        payload = board_payload
    else:
        return []

    ranges = payload.get("ranges") if isinstance(payload.get("ranges"), dict) else {}
    return _normalize_rows(ranges.get(rk))


__all__ = [
    "RANKING_BOARDS_TABLE",
    "RANKING_BOARD_VERSION",
    "RANKING_BOARD_TIMEZONE",
    "BOARD_STATUS_DRAFT",
    "BOARD_STATUS_READY",
    "BOARD_STATUS_FAILED",
    "ALLOWED_BOARD_STATUSES",
    "normalize_board_payload",
    "build_ranking_board_source_hash",
    "upsert_ranking_board_draft",
    "fetch_latest_ranking_board",
    "fetch_latest_ready_ranking_board",
    "promote_ranking_board",
    "fail_ranking_board",
    "select_board_rows",
]
