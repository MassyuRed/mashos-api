# -*- coding: utf-8 -*-
"""astor_material_snapshots.py

Phase X: Central Material Snapshot Generator (v1)
------------------------------------------------

目的
- ユーザーの入力（materials）を「材料スナップショット」としてまとめる。
- internal/public を同時に生成し、後続の生成/公開判定の土台を作る。

v1 のスコープ
- まずは `emotions` テーブル（InputScreen相当）を対象にする。
- MyModelCreate / DeepInsight / Echoes / Discoveries は後続フェーズで追加できる設計にする。

重要な方針（国家仕様）
- internal: secret を含む材料
- public  : secret を除外した材料
- source_hash は「材料集合の指紋」として計算し、同じ材料なら再生成をスキップできるようにする。

環境変数
- SUPABASE_URL
- SUPABASE_SERVICE_ROLE_KEY
- MATERIAL_SNAPSHOTS_TABLE (default: material_snapshots)
- SNAPSHOT_SCOPE_DEFAULT (default: global)
- SNAPSHOT_RECENT_EMOTIONS_LIMIT (default: 200)
- SNAPSHOT_META_PAGE_SIZE (default: 1000)
- SNAPSHOT_META_MAX_ROWS (default: 20000)

注意
- material_snapshots テーブルは別途用意する必要がある。
  (このパッチはコード導入のみ。SQLは別ファイルで同梱可)
"""

from __future__ import annotations

import hashlib
import logging
import os
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

import httpx


logger = logging.getLogger("astor_material_snapshots")

SUPABASE_URL = (os.getenv("SUPABASE_URL") or "").rstrip("/")
SUPABASE_SERVICE_ROLE_KEY = (os.getenv("SUPABASE_SERVICE_ROLE_KEY") or "").strip()

MATERIAL_SNAPSHOTS_TABLE = (os.getenv("MATERIAL_SNAPSHOTS_TABLE") or "material_snapshots").strip() or "material_snapshots"

SNAPSHOT_SCOPE_DEFAULT = (os.getenv("SNAPSHOT_SCOPE_DEFAULT") or "global").strip() or "global"

try:
    SNAPSHOT_RECENT_EMOTIONS_LIMIT = int(os.getenv("SNAPSHOT_RECENT_EMOTIONS_LIMIT", "200") or "200")
except Exception:
    SNAPSHOT_RECENT_EMOTIONS_LIMIT = 200

try:
    SNAPSHOT_META_PAGE_SIZE = int(os.getenv("SNAPSHOT_META_PAGE_SIZE", "1000") or "1000")
except Exception:
    SNAPSHOT_META_PAGE_SIZE = 1000

try:
    SNAPSHOT_META_MAX_ROWS = int(os.getenv("SNAPSHOT_META_MAX_ROWS", "20000") or "20000")
except Exception:
    SNAPSHOT_META_MAX_ROWS = 20000


def _now_iso_z() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _has_supabase_config() -> bool:
    return bool(SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY)


def _sb_headers_json(*, prefer: str = "return=minimal") -> Dict[str, str]:
    return {
        "apikey": SUPABASE_SERVICE_ROLE_KEY,
        "Authorization": f"Bearer {SUPABASE_SERVICE_ROLE_KEY}",
        "Content-Type": "application/json",
        "Prefer": prefer,
    }


def _sb_headers(*, prefer: str = "") -> Dict[str, str]:
    h = {
        "apikey": SUPABASE_SERVICE_ROLE_KEY,
        "Authorization": f"Bearer {SUPABASE_SERVICE_ROLE_KEY}",
    }
    if prefer:
        h["Prefer"] = prefer
    return h


async def _sb_get_json(path: str, *, params: List[Tuple[str, str]], timeout: float = 8.0) -> List[Dict[str, Any]]:
    if not _has_supabase_config():
        return []
    url = f"{SUPABASE_URL}{path}"
    async with httpx.AsyncClient(timeout=timeout) as client:
        resp = await client.get(url, headers=_sb_headers(), params=params)
    if resp.status_code not in (200, 206):
        raise RuntimeError(f"Supabase GET failed: {resp.status_code} {(resp.text or '')[:800]}")
    try:
        data = resp.json()
    except Exception:
        return []
    if isinstance(data, list):
        return [x for x in data if isinstance(x, dict)]
    return []


async def _sb_post_json(path: str, *, json_body: Any, timeout: float = 8.0, prefer: str = "return=minimal") -> httpx.Response:
    if not _has_supabase_config():
        raise RuntimeError("Supabase config missing")
    url = f"{SUPABASE_URL}{path}"
    async with httpx.AsyncClient(timeout=timeout) as client:
        resp = await client.post(url, headers=_sb_headers_json(prefer=prefer), json=json_body)
    return resp


async def fetch_emotion_meta_for_hash(user_id: str) -> List[Dict[str, Any]]:
    """Fetch (id, created_at, is_secret) rows for hashing.

    Uses pagination and caps at SNAPSHOT_META_MAX_ROWS to avoid runaway loads.
    """
    uid = str(user_id or "").strip()
    if not uid:
        return []

    out: List[Dict[str, Any]] = []
    offset = 0
    page_size = max(1, int(SNAPSHOT_META_PAGE_SIZE))
    max_rows = max(1000, int(SNAPSHOT_META_MAX_ROWS))

    while True:
        limit = min(page_size, max_rows - len(out))
        if limit <= 0:
            break

        rows = await _sb_get_json(
            "/rest/v1/emotions",
            params=[
                ("select", "id,created_at,is_secret"),
                ("user_id", f"eq.{uid}"),
                ("order", "created_at.asc"),
                ("limit", str(limit)),
                ("offset", str(offset)),
            ],
        )
        if not rows:
            break

        out.extend(rows)
        if len(rows) < limit:
            break

        offset += limit

    return out


async def fetch_recent_emotions(user_id: str, *, include_secret: bool) -> List[Dict[str, Any]]:
    """Fetch recent emotion rows (for snapshot payload)."""
    uid = str(user_id or "").strip()
    if not uid:
        return []

    params: List[Tuple[str, str]] = [
        ("select", "id,created_at,emotions,emotion_details,memo,memo_action,is_secret,emotion_strength_avg"),
        ("user_id", f"eq.{uid}"),
        ("order", "created_at.desc"),
        ("limit", str(max(1, int(SNAPSHOT_RECENT_EMOTIONS_LIMIT)))),
    ]
    if not include_secret:
        params.append(("is_secret", "eq.false"))

    rows = await _sb_get_json("/rest/v1/emotions", params=params)
    # order is desc; make it asc for readability
    return list(reversed(rows))


def compute_source_hash_from_emotion_meta(
    *,
    user_id: str,
    scope: str,
    snapshot_type: str,
    meta_rows: List[Dict[str, Any]],
) -> str:
    """Compute a stable sha256 hash based on emotion meta rows.

    We hash only meta fields to keep memory usage stable.
    Hash changes when:
    - a new row is added
    - is_secret toggles (if included in the snapshot_type)
    """
    uid = str(user_id or "").strip()
    sc = str(scope or "").strip() or SNAPSHOT_SCOPE_DEFAULT
    st = str(snapshot_type or "").strip() or "internal"

    h = hashlib.sha256()
    h.update(f"v1|{uid}|{sc}|{st}|".encode("utf-8"))

    for r in meta_rows:
        rid = str(r.get("id") or "")
        created_at = str(r.get("created_at") or "")
        is_secret = bool(r.get("is_secret"))
        # public snapshots should exclude secret rows entirely
        if st == "public" and is_secret:
            continue
        h.update((rid + "|" + created_at + "|" + ("1" if is_secret else "0") + "\n").encode("utf-8"))

    return h.hexdigest()


def build_snapshot_payload(
    *,
    scope: str,
    snapshot_type: str,
    source_hash: str,
    total_rows: int,
    public_rows: int,
    secret_rows: int,
    recent_emotions: List[Dict[str, Any]],
) -> Dict[str, Any]:
    return {
        "version": "v1",
        "scope": scope,
        "snapshot_type": snapshot_type,
        "source_hash": source_hash,
        "generated_at": _now_iso_z(),
        "summary": {
            "emotions_total": int(total_rows),
            "emotions_public": int(public_rows),
            "emotions_secret": int(secret_rows),
            "recent_limit": int(SNAPSHOT_RECENT_EMOTIONS_LIMIT),
        },
        "views": {
            # 部署別配給ビュー（まずは emotions だけ）
            "emotions_recent": recent_emotions,
        },
    }


async def _fetch_latest_snapshot_hash(user_id: str, *, scope: str, snapshot_type: str) -> Optional[str]:
    """Fetch latest snapshot source_hash (if table exists)."""
    uid = str(user_id or "").strip()
    if not uid:
        return None
    sc = str(scope or "").strip() or SNAPSHOT_SCOPE_DEFAULT
    st = str(snapshot_type or "").strip() or "internal"

    rows = await _sb_get_json(
        f"/rest/v1/{MATERIAL_SNAPSHOTS_TABLE}",
        params=[
            ("select", "source_hash,created_at"),
            ("user_id", f"eq.{uid}"),
            ("scope", f"eq.{sc}"),
            ("snapshot_type", f"eq.{st}"),
            ("order", "created_at.desc"),
            ("limit", "1"),
        ],
    )
    if rows:
        return str(rows[0].get("source_hash") or "") or None
    return None


async def _insert_snapshot_row(
    *,
    user_id: str,
    scope: str,
    snapshot_type: str,
    source_hash: str,
    payload: Dict[str, Any],
) -> bool:
    """Insert a snapshot row. Returns True if inserted, False if skipped."""
    uid = str(user_id or "").strip()
    if not uid:
        return False
    sc = str(scope or "").strip() or SNAPSHOT_SCOPE_DEFAULT
    st = str(snapshot_type or "").strip() or "internal"
    sh = str(source_hash or "").strip()
    if not sh:
        return False

    # If the latest hash is identical, skip insert (idempotent)
    try:
        latest = await _fetch_latest_snapshot_hash(uid, scope=sc, snapshot_type=st)
        if latest and latest == sh:
            return False
    except Exception:
        # If we can't read latest, continue to insert (best-effort)
        pass

    row = {
        "user_id": uid,
        "scope": sc,
        "snapshot_type": st,
        "source_hash": sh,
        "payload": payload or {},
        "created_at": _now_iso_z(),
    }

    resp = await _sb_post_json(f"/rest/v1/{MATERIAL_SNAPSHOTS_TABLE}", json_body=row, prefer="return=minimal")
    if resp.status_code in (200, 201, 204):
        return True
    # Common when table missing: 404
    raise RuntimeError(f"Supabase insert snapshot failed: {resp.status_code} {(resp.text or '')[:800]}")


async def generate_and_store_material_snapshots(
    *,
    user_id: str,
    scope: str = SNAPSHOT_SCOPE_DEFAULT,
    trigger: str = "worker",
) -> Dict[str, Any]:
    """Generate internal/public snapshots for a user and store them.

    Returns:
    {
      "status": "ok",
      "user_id": ...,
      "scope": ...,
      "internal": {"source_hash": ..., "inserted": bool},
      "public": {"source_hash": ..., "inserted": bool},
      "counts": {...}
    }
    """
    uid = str(user_id or "").strip()
    if not uid:
        raise ValueError("user_id is required")
    if not _has_supabase_config():
        raise RuntimeError("Supabase config missing")

    sc = str(scope or "").strip() or SNAPSHOT_SCOPE_DEFAULT

    # 1) Fetch meta rows for hashing (includes secret flag)
    meta = await fetch_emotion_meta_for_hash(uid)
    total_rows = len(meta)
    secret_rows = sum(1 for r in meta if bool(r.get("is_secret")))
    public_rows = total_rows - secret_rows

    # 2) Compute hashes
    internal_hash = compute_source_hash_from_emotion_meta(user_id=uid, scope=sc, snapshot_type="internal", meta_rows=meta)
    public_hash = compute_source_hash_from_emotion_meta(user_id=uid, scope=sc, snapshot_type="public", meta_rows=meta)

    # 3) Fetch recent rows for payload (bounded)
    internal_recent = await fetch_recent_emotions(uid, include_secret=True)
    public_recent = await fetch_recent_emotions(uid, include_secret=False)

    # 4) Build payloads
    internal_payload = build_snapshot_payload(
        scope=sc,
        snapshot_type="internal",
        source_hash=internal_hash,
        total_rows=total_rows,
        public_rows=public_rows,
        secret_rows=secret_rows,
        recent_emotions=internal_recent,
    )
    public_payload = build_snapshot_payload(
        scope=sc,
        snapshot_type="public",
        source_hash=public_hash,
        total_rows=total_rows,
        public_rows=public_rows,
        secret_rows=secret_rows,
        recent_emotions=public_recent,
    )

    # 5) Store snapshots
    inserted_internal = await _insert_snapshot_row(user_id=uid, scope=sc, snapshot_type="internal", source_hash=internal_hash, payload=internal_payload)
    inserted_public = await _insert_snapshot_row(user_id=uid, scope=sc, snapshot_type="public", source_hash=public_hash, payload=public_payload)

    logger.info(
        "material_snapshots generated. user=%s scope=%s internal=%s public=%s trigger=%s",
        uid,
        sc,
        internal_hash[:10],
        public_hash[:10],
        trigger,
    )

    return {
        "status": "ok",
        "user_id": uid,
        "scope": sc,
        "trigger": trigger,
        "internal": {"source_hash": internal_hash, "inserted": bool(inserted_internal)},
        "public": {"source_hash": public_hash, "inserted": bool(inserted_public)},
        "counts": {"total": total_rows, "public": public_rows, "secret": secret_rows},
    }
