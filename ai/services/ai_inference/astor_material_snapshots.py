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
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Tuple

import httpx

# Downstream jobs are best-effort.
try:
    from astor_job_queue import enqueue_job  # type: ignore
except Exception:  # pragma: no cover
    enqueue_job = None  # type: ignore


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



try:
    SNAPSHOT_SELF_STRUCTURE_PAGE_SIZE = int(os.getenv("SNAPSHOT_SELF_STRUCTURE_PAGE_SIZE", "1000") or "1000")
except Exception:
    SNAPSHOT_SELF_STRUCTURE_PAGE_SIZE = 1000

try:
    SNAPSHOT_SELF_STRUCTURE_MAX_ROWS = int(os.getenv("SNAPSHOT_SELF_STRUCTURE_MAX_ROWS", "20000") or "20000")
except Exception:
    SNAPSHOT_SELF_STRUCTURE_MAX_ROWS = 20000

MYMODEL_CREATE_ANSWERS_TABLE = (os.getenv("MYMODEL_CREATE_ANSWERS_TABLE") or "mymodel_create_answers").strip()
MYMODEL_CREATE_USER_ID_COLUMN = (os.getenv("MYMODEL_CREATE_USER_ID_COLUMN") or "user_id").strip() or "user_id"

DEEP_INSIGHT_INPUTS_TABLE = (os.getenv("DEEP_INSIGHT_INPUTS_TABLE") or "deep_insight_answers").strip()
DEEP_INSIGHT_USER_ID_COLUMN = (os.getenv("DEEP_INSIGHT_USER_ID_COLUMN") or "user_id").strip() or "user_id"

ECHO_INPUTS_TABLE = (os.getenv("ECHO_INPUTS_TABLE") or "mymodel_echoes").strip()
ECHO_USER_ID_COLUMN = (os.getenv("ECHO_USER_ID_COLUMN") or "user_id").strip() or "user_id"

DISCOVERY_INPUTS_TABLE = (os.getenv("DISCOVERY_INPUTS_TABLE") or "mymodel_discoveries").strip()
DISCOVERY_USER_ID_COLUMN = (os.getenv("DISCOVERY_USER_ID_COLUMN") or "user_id").strip() or "user_id"




# --- Emotion period scopes (weekly/monthly) ---
# JST fixed (UTC+9) to match MyWeb report definitions.
JST_OFFSET = timedelta(hours=9)
JST = timezone(JST_OFFSET)
DAY = timedelta(days=1)

# Strength weights (match client / api_myweb_reports)
STRENGTH_SCORE: Dict[str, int] = {"weak": 1, "medium": 2, "strong": 3}

# Emotion mapping (JP labels -> keys)
JP_TO_KEY: Dict[str, str] = {
    "喜び": "joy",
    "悲しみ": "sadness",
    "不安": "anxiety",
    "怒り": "anger",
    "平穏": "calm",
}
EMOTION_KEYS: Tuple[str, ...] = ("joy", "sadness", "anxiety", "anger", "calm")
KEY_TO_JP: Dict[str, str] = {v: k for k, v in JP_TO_KEY.items()}

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


async def _fetch_latest_snapshot_meta(
    user_id: str,
    *,
    scope: str,
    snapshot_type: str,
) -> Optional[Dict[str, Any]]:
    """Fetch latest snapshot row meta (id/source_hash/created_at) for downstream jobs."""
    uid = str(user_id or "").strip()
    if not uid:
        return None
    sc = str(scope or "").strip() or SNAPSHOT_SCOPE_DEFAULT
    st = str(snapshot_type or "").strip() or "public"

    rows = await _sb_get_json(
        f"/rest/v1/{MATERIAL_SNAPSHOTS_TABLE}",
        params=[
            ("select", "id,source_hash,created_at"),
            ("user_id", f"eq.{uid}"),
            ("scope", f"eq.{sc}"),
            ("snapshot_type", f"eq.{st}"),
            ("order", "created_at.desc"),
            ("limit", "1"),
        ],
        timeout=8.0,
    )
    if rows:
        return rows[0]
    return None


def _latest_weekly_scope_for_now(now_utc: Optional[datetime] = None) -> str:
    dt = (now_utc or datetime.now(timezone.utc)).astimezone(JST)
    days_back = (dt.weekday() + 1) % 7  # Sunday=0 boundary
    last_sun = dt.date() - timedelta(days=days_back)
    return f"emotion_weekly:{last_sun.year:04d}-{last_sun.month:02d}-{last_sun.day:02d}"


def _latest_monthly_scope_for_now(now_utc: Optional[datetime] = None) -> str:
    dt = (now_utc or datetime.now(timezone.utc)).astimezone(JST)
    if dt.month == 1:
        y, m = dt.year - 1, 12
    else:
        y, m = dt.year, dt.month - 1
    return f"emotion_monthly:{y:04d}-{m:02d}"


async def fetch_emotion_meta_for_hash(user_id: str, *, start_iso: Optional[str] = None, end_iso: Optional[str] = None) -> List[Dict[str, Any]]:
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

        
        params: List[Tuple[str, str]] = [
            ("select", "id,created_at,is_secret"),
            ("user_id", f"eq.{uid}"),
        ]
        if start_iso:
            params.append(("created_at", f"gte.{start_iso}"))
        if end_iso:
            params.append(("created_at", f"lte.{end_iso}"))
        params.extend(
            [
                ("order", "created_at.asc"),
                ("limit", str(limit)),
                ("offset", str(offset)),
            ]
        )

        rows = await _sb_get_json(
            "/rest/v1/emotions",
            params=params,
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
    summary: Dict[str, Any],
    views: Dict[str, Any],
) -> Dict[str, Any]:
    payload: Dict[str, Any] = {
        "version": "v2",
        "scope": scope,
        "snapshot_type": snapshot_type,
        "source_hash": source_hash,
        "generated_at": _now_iso_z(),
        "summary": summary or {},
        "views": views or {},
    }
    # Worker compatibility: expose aliases at payload root as well.
    if isinstance(views, dict):
        if "self_structure_view" in views:
            payload["self_structure_view"] = views.get("self_structure_view")
        if "premium_reflection_view" in views:
            payload["premium_reflection_view"] = views.get("premium_reflection_view")
        if "emotions_recent" in views:
            payload["emotions_recent"] = views.get("emotions_recent")
    return payload


async def _safe_optional_sb_get_json(path: str, *, params: List[Tuple[str, str]], timeout: float = 8.0) -> List[Dict[str, Any]]:
    try:
        return await _sb_get_json(path, params=params, timeout=timeout)
    except Exception as exc:
        logger.debug("optional Supabase GET failed: path=%s err=%s", path, exc)
        return []


def _row_is_secret(row: Dict[str, Any]) -> bool:
    v = row.get("is_secret")
    if isinstance(v, bool):
        return v
    if isinstance(v, (int, float)):
        return bool(v)
    s = str(v or "").strip().lower()
    return s in ("1", "true", "t", "yes", "y", "on")


def _row_created_at(row: Dict[str, Any]) -> str:
    return str(row.get("created_at") or row.get("updated_at") or "")


def _row_updated_at(row: Dict[str, Any]) -> str:
    return str(row.get("updated_at") or row.get("created_at") or "")


def _row_timestamp(row: Dict[str, Any]) -> str:
    return str(row.get("created_at") or row.get("updated_at") or _now_iso_z())


def _pick_first_text(row: Dict[str, Any], keys: List[str]) -> str:
    for k in keys:
        v = row.get(k)
        if v is None:
            continue
        s = str(v).strip()
        if s:
            return s
    return ""


def _normalize_emotion_signals_all(row: Dict[str, Any]) -> List[str]:
    out: List[str] = []
    details = row.get("emotion_details")
    if isinstance(details, list):
        for it in details:
            if not isinstance(it, dict):
                continue
            t = str(it.get("type") or "").strip()
            if t:
                out.append(t)
    emos = row.get("emotions")
    if isinstance(emos, list):
        for it in emos:
            s = str(it or "").strip()
            if s:
                out.append(s)
    seen = set()
    uniq: List[str] = []
    for s in out:
        if s in seen:
            continue
        seen.add(s)
        uniq.append(s)
    return uniq


def compute_source_hash_from_material_meta(
    *,
    user_id: str,
    scope: str,
    snapshot_type: str,
    meta_rows: List[Dict[str, Any]],
) -> str:
    uid = str(user_id or "").strip()
    sc = str(scope or "").strip() or SNAPSHOT_SCOPE_DEFAULT
    st = str(snapshot_type or "").strip() or "internal"

    h = hashlib.sha256()
    h.update(f"v2|{uid}|{sc}|{st}|".encode("utf-8"))

    rows = sorted(
        meta_rows or [],
        key=lambda r: (
            str(r.get("material_kind") or ""),
            str(r.get("created_at") or ""),
            str(r.get("updated_at") or ""),
            str(r.get("id") or ""),
        ),
    )
    for r in rows:
        is_secret = _row_is_secret(r)
        if st == "public" and is_secret:
            continue
        h.update(
            (
                str(r.get("material_kind") or "") + "|"
                + str(r.get("id") or "") + "|"
                + str(r.get("created_at") or "") + "|"
                + str(r.get("updated_at") or "") + "|"
                + ("1" if is_secret else "0") + "\n"
            ).encode("utf-8")
        )

    return h.hexdigest()


async def _fetch_optional_rows_by_user(
    *,
    table: str,
    user_id: str,
    user_id_column: str = "user_id",
    include_secret: bool = True,
    page_size: int = SNAPSHOT_SELF_STRUCTURE_PAGE_SIZE,
    max_rows: int = SNAPSHOT_SELF_STRUCTURE_MAX_ROWS,
) -> List[Dict[str, Any]]:
    tbl = str(table or "").strip()
    uid = str(user_id or "").strip()
    col = str(user_id_column or "user_id").strip() or "user_id"
    if not tbl or not uid:
        return []

    out: List[Dict[str, Any]] = []
    offset = 0
    ps = max(1, int(page_size or 1000))
    mx = max(ps, int(max_rows or 20000))

    while True:
        limit = min(ps, mx - len(out))
        if limit <= 0:
            break

        rows = await _safe_optional_sb_get_json(
            f"/rest/v1/{tbl}",
            params=[
                ("select", "*"),
                (col, f"eq.{uid}"),
                ("order", "created_at.asc"),
                ("limit", str(limit)),
                ("offset", str(offset)),
            ],
            timeout=10.0,
        )
        if not rows:
            break

        if not include_secret:
            rows = [r for r in rows if not _row_is_secret(r)]

        out.extend(rows)
        if len(rows) < limit:
            break
        offset += limit

    out.sort(key=lambda r: (_row_created_at(r), str(r.get("id") or "")))
    return out


async def fetch_emotions_for_self_structure(
    user_id: str,
    *,
    include_secret: bool,
    page_size: int = SNAPSHOT_SELF_STRUCTURE_PAGE_SIZE,
    max_rows: int = SNAPSHOT_SELF_STRUCTURE_MAX_ROWS,
) -> List[Dict[str, Any]]:
    uid = str(user_id or "").strip()
    if not uid:
        return []

    out: List[Dict[str, Any]] = []
    offset = 0
    ps = max(1, int(page_size or 1000))
    mx = max(ps, int(max_rows or 20000))

    while True:
        limit = min(ps, mx - len(out))
        if limit <= 0:
            break

        params: List[Tuple[str, str]] = [
            ("select", "id,created_at,emotions,emotion_details,memo,memo_action,is_secret,emotion_strength_avg"),
            ("user_id", f"eq.{uid}"),
            ("order", "created_at.asc"),
            ("limit", str(limit)),
            ("offset", str(offset)),
        ]
        if not include_secret:
            params.append(("is_secret", "eq.false"))

        rows = await _sb_get_json("/rest/v1/emotions", params=params, timeout=10.0)
        if not rows:
            break

        out.extend(rows)
        if len(rows) < limit:
            break
        offset += limit

    return out


async def fetch_emotions_for_premium_reflection(
    user_id: str,
    *,
    include_secret: bool,
    page_size: int = SNAPSHOT_SELF_STRUCTURE_PAGE_SIZE,
    max_rows: int = SNAPSHOT_SELF_STRUCTURE_MAX_ROWS,
) -> List[Dict[str, Any]]:
    """Fetch InputScreen rows for Premium Reflections.

    Intentionally uses `select=*` so future category fields added to emotions
    are automatically available without further snapshot patches.
    """
    uid = str(user_id or "").strip()
    if not uid:
        return []

    out: List[Dict[str, Any]] = []
    offset = 0
    ps = max(1, int(page_size or 1000))
    mx = max(ps, int(max_rows or 20000))

    while True:
        limit = min(ps, mx - len(out))
        if limit <= 0:
            break

        params: List[Tuple[str, str]] = [
            ("select", "*"),
            ("user_id", f"eq.{uid}"),
            ("order", "created_at.asc"),
            ("limit", str(limit)),
            ("offset", str(offset)),
        ]
        if not include_secret:
            params.append(("is_secret", "eq.false"))

        rows = await _sb_get_json("/rest/v1/emotions", params=params, timeout=10.0)
        if not rows:
            break

        out.extend(rows)
        if len(rows) < limit:
            break
        offset += limit

    return out


async def fetch_mymodel_create_rows_for_self_structure(user_id: str, *, include_secret: bool) -> List[Dict[str, Any]]:
    return await _fetch_optional_rows_by_user(
        table=MYMODEL_CREATE_ANSWERS_TABLE,
        user_id=user_id,
        user_id_column=MYMODEL_CREATE_USER_ID_COLUMN,
        include_secret=include_secret,
    )


async def fetch_deep_insight_rows_for_self_structure(user_id: str, *, include_secret: bool) -> List[Dict[str, Any]]:
    return await _fetch_optional_rows_by_user(
        table=DEEP_INSIGHT_INPUTS_TABLE,
        user_id=user_id,
        user_id_column=DEEP_INSIGHT_USER_ID_COLUMN,
        include_secret=include_secret,
    )


async def fetch_echo_rows_for_self_structure(user_id: str, *, include_secret: bool) -> List[Dict[str, Any]]:
    return await _fetch_optional_rows_by_user(
        table=ECHO_INPUTS_TABLE,
        user_id=user_id,
        user_id_column=ECHO_USER_ID_COLUMN,
        include_secret=include_secret,
    )


async def fetch_discovery_rows_for_self_structure(user_id: str, *, include_secret: bool) -> List[Dict[str, Any]]:
    return await _fetch_optional_rows_by_user(
        table=DISCOVERY_INPUTS_TABLE,
        user_id=user_id,
        user_id_column=DISCOVERY_USER_ID_COLUMN,
        include_secret=include_secret,
    )


def _material_meta_rows_from_rows(material_kind: str, rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    mk = str(material_kind or "").strip()
    out: List[Dict[str, Any]] = []
    for r in rows or []:
        out.append(
            {
                "material_kind": mk,
                "id": str(r.get("id") or ""),
                "created_at": _row_created_at(r),
                "updated_at": _row_updated_at(r),
                "is_secret": _row_is_secret(r),
            }
        )
    return out


def _dedupe_material_meta_rows(rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    seen = set()
    for r in rows or []:
        key = (str(r.get("material_kind") or ""), str(r.get("id") or ""))
        if key in seen:
            continue
        seen.add(key)
        out.append(r)
    return out


def _emotion_row_to_self_structure_item(row: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "source_type": "emotion_input",
        "source_id": str(row.get("id") or ""),
        "timestamp": _row_timestamp(row),
        "text_primary": str(row.get("memo") or ""),
        "text_secondary": str(row.get("memo_action") or ""),
        "prompt_key": None,
        "question_text": None,
        "emotion_signals": _normalize_emotion_signals_all(row),
        "action_signals": [],
        "social_signals": [],
        "source_weight": 1.0,
    }


def _mymodel_row_to_self_structure_item(row: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "source_type": "mymodel_create",
        "source_id": str(row.get("id") or ""),
        "timestamp": _row_timestamp(row),
        "text_primary": _pick_first_text(row, ["answer_text", "answer", "response_text", "text", "content", "body"]),
        "text_secondary": _pick_first_text(row, ["text_secondary", "context_text", "notes"]),
        "prompt_key": _pick_first_text(row, ["prompt_key", "question_key", "q_key"]) or None,
        "question_text": _pick_first_text(row, ["question_text", "question", "prompt", "title"]) or None,
        "emotion_signals": [],
        "action_signals": [],
        "social_signals": [],
        "source_weight": 0.9,
    }


def _deep_insight_row_to_self_structure_item(row: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "source_type": "deep_insight",
        "source_id": str(row.get("id") or ""),
        "timestamp": _row_timestamp(row),
        "text_primary": _pick_first_text(row, ["answer_text", "answer", "response_text", "text", "content", "body"]),
        "text_secondary": _pick_first_text(row, ["text_secondary", "context_text", "notes"]),
        "prompt_key": _pick_first_text(row, ["prompt_key", "question_key", "q_key"]) or None,
        "question_text": _pick_first_text(row, ["question_text", "question", "prompt", "title"]) or None,
        "emotion_signals": [],
        "action_signals": [],
        "social_signals": [],
        "source_weight": 1.1,
    }


def _extract_reflection_category(row: Dict[str, Any]) -> Optional[str]:
    cat = _pick_first_text(
        row,
        [
            "category",
            "category_key",
            "category_name",
            "input_category",
            "selected_category",
            "context_category",
        ],
    )
    return cat or None


def _emotion_row_to_premium_reflection_item(row: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "source_type": "emotion_input",
        "source_id": str(row.get("id") or ""),
        "timestamp": _row_timestamp(row),
        "category": _extract_reflection_category(row),
        "text_primary": str(row.get("memo") or ""),
        "text_secondary": str(row.get("memo_action") or ""),
        "emotion_signals": _normalize_emotion_signals_all(row),
        "question_text": None,
        "source_weight": 1.0,
    }


def _deep_insight_row_to_premium_reflection_item(row: Dict[str, Any]) -> Dict[str, Any]:
    category = _extract_reflection_category(row) or "deep_insight"
    return {
        "source_type": "deep_insight",
        "source_id": str(row.get("id") or ""),
        "timestamp": _row_timestamp(row),
        "category": category,
        "text_primary": _pick_first_text(row, ["answer_text", "answer", "response_text", "text", "content", "body"]),
        "text_secondary": _pick_first_text(row, ["text_secondary", "context_text", "notes"]),
        "emotion_signals": [],
        "question_text": _pick_first_text(row, ["question_text", "question", "prompt", "title"]) or None,
        "source_weight": 1.1,
    }


def build_premium_reflection_view(
    *,
    emotion_rows: List[Dict[str, Any]],
    deep_insight_rows: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """Build public-safe material view for Premium Reflection generation.

    Premium Reflections are generated only from secret-OFF InputScreen rows and
    secret-OFF DeepInsight inputs, so this view is intentionally public-safe.
    """
    items: List[Dict[str, Any]] = []

    for row in emotion_rows or []:
        items.append(_emotion_row_to_premium_reflection_item(row))
    for row in deep_insight_rows or []:
        items.append(_deep_insight_row_to_premium_reflection_item(row))

    items = [
        it for it in items
        if str(it.get("text_primary") or "").strip() or str(it.get("text_secondary") or "").strip()
    ]
    items.sort(key=lambda r: (str(r.get("timestamp") or ""), str(r.get("source_id") or "")))

    timestamps = [str(it.get("timestamp") or "") for it in items if str(it.get("timestamp") or "").strip()]
    category_counts: Dict[str, int] = {}
    for it in items:
        cat = str(it.get("category") or "").strip()
        if not cat:
            continue
        category_counts[cat] = category_counts.get(cat, 0) + 1

    return {
        "version": "premium_reflection_view.v1",
        "items": items,
        "source_counts": {
            "emotion_input": len(emotion_rows or []),
            "deep_insight": len(deep_insight_rows or []),
        },
        "category_counts": category_counts,
        "time_span_start": timestamps[0] if timestamps else None,
        "time_span_end": timestamps[-1] if timestamps else None,
    }


def _echo_row_to_self_structure_item(row: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "source_type": "echo",
        "source_id": str(row.get("id") or ""),
        "timestamp": _row_timestamp(row),
        "text_primary": _pick_first_text(row, ["text", "content", "body", "memo", "comment_text"]),
        "text_secondary": _pick_first_text(row, ["text_secondary", "context_text", "notes"]),
        "prompt_key": _pick_first_text(row, ["prompt_key", "question_key", "q_key"]) or None,
        "question_text": _pick_first_text(row, ["question_text", "question", "prompt", "title"]) or None,
        "emotion_signals": [],
        "action_signals": [],
        "social_signals": ["echo"],
        "source_weight": 0.4,
    }


def _discovery_row_to_self_structure_item(row: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "source_type": "discovery",
        "source_id": str(row.get("id") or ""),
        "timestamp": _row_timestamp(row),
        "text_primary": _pick_first_text(row, ["text", "content", "body", "memo", "comment_text"]),
        "text_secondary": _pick_first_text(row, ["text_secondary", "context_text", "notes"]),
        "prompt_key": _pick_first_text(row, ["prompt_key", "question_key", "q_key"]) or None,
        "question_text": _pick_first_text(row, ["question_text", "question", "prompt", "title"]) or None,
        "emotion_signals": [],
        "action_signals": [],
        "social_signals": ["discovery"],
        "source_weight": 0.4,
    }


def build_self_structure_view(
    *,
    emotion_rows: List[Dict[str, Any]],
    mymodel_rows: List[Dict[str, Any]],
    deep_insight_rows: List[Dict[str, Any]],
    echo_rows: List[Dict[str, Any]],
    discovery_rows: List[Dict[str, Any]],
) -> Dict[str, Any]:
    items: List[Dict[str, Any]] = []

    for row in emotion_rows or []:
        items.append(_emotion_row_to_self_structure_item(row))
    for row in mymodel_rows or []:
        items.append(_mymodel_row_to_self_structure_item(row))
    for row in deep_insight_rows or []:
        items.append(_deep_insight_row_to_self_structure_item(row))
    for row in echo_rows or []:
        items.append(_echo_row_to_self_structure_item(row))
    for row in discovery_rows or []:
        items.append(_discovery_row_to_self_structure_item(row))

    items.sort(key=lambda r: (str(r.get("timestamp") or ""), str(r.get("source_id") or "")))
    timestamps = [str(it.get("timestamp") or "") for it in items if str(it.get("timestamp") or "").strip()]
    source_counts = {
        "emotion_input": len(emotion_rows or []),
        "mymodel_create": len(mymodel_rows or []),
        "deep_insight": len(deep_insight_rows or []),
        "echo": len(echo_rows or []),
        "discovery": len(discovery_rows or []),
    }

    return {
        "version": "self_structure_view.v1",
        "items": items,
        "source_counts": source_counts,
        "time_span_start": timestamps[0] if timestamps else None,
        "time_span_end": timestamps[-1] if timestamps else None,
    }


def _build_global_views(
    *,
    recent_emotions: List[Dict[str, Any]],
    self_structure_view: Dict[str, Any],
    premium_reflection_view: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    return {
        "emotions_recent": recent_emotions or [],
        "self_structure_view": self_structure_view or {
            "version": "self_structure_view.v1",
            "items": [],
            "source_counts": {},
            "time_span_start": None,
            "time_span_end": None,
        },
        "premium_reflection_view": premium_reflection_view or {
            "version": "premium_reflection_view.v1",
            "items": [],
            "source_counts": {},
            "category_counts": {},
            "time_span_start": None,
            "time_span_end": None,
        },
    }


def _build_global_summary(
    *,
    material_meta: List[Dict[str, Any]],
    emotion_total_rows: int,
    emotion_public_rows: int,
    emotion_secret_rows: int,
    self_structure_view: Dict[str, Any],
    premium_reflection_view: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    source_counts: Dict[str, int] = {}
    secret_total = 0
    for r in material_meta or []:
        mk = str(r.get("material_kind") or "")
        source_counts[mk] = source_counts.get(mk, 0) + 1
        if _row_is_secret(r):
            secret_total += 1

    total_materials = len(material_meta or [])
    public_materials = total_materials - secret_total

    return {
        "materials_total": int(total_materials),
        "materials_public": int(public_materials),
        "materials_secret": int(secret_total),
        "source_counts": source_counts,
        "emotions_total": int(emotion_total_rows),
        "emotions_public": int(emotion_public_rows),
        "emotions_secret": int(emotion_secret_rows),
        "recent_limit": int(SNAPSHOT_RECENT_EMOTIONS_LIMIT),
        "self_structure_items": int(len((self_structure_view or {}).get("items") or [])),
        "premium_reflection_items": int(len(((premium_reflection_view or {}).get("items") or []))),
    }


def _iso_ms_z(dt: datetime) -> str:
    """UTC ISO string with milliseconds (JS-like)."""
    return dt.astimezone(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")


def _jst_midnight_utc(year: int, month: int, day: int) -> datetime:
    """JSTの指定日 00:00 を UTC datetime で返す。"""
    jst_dt = datetime(year, month, day, 0, 0, 0, 0, tzinfo=JST)
    return jst_dt.astimezone(timezone.utc)


def _is_emotion_period_scope(scope: str) -> bool:
    sc = str(scope or "").strip()
    return bool(
        sc.startswith("emotion_daily:")
        or sc.startswith("emotion_weekly:")
        or sc.startswith("emotion_monthly:")
    )


def _parse_emotion_period_scope(scope: str) -> Dict[str, Any]:
    """Parse emotion period scope and return period boundaries.

    Supported scopes:
    - emotion_daily:YYYY-MM-DD   (target day in JST)
    - emotion_weekly:YYYY-MM-DD  (dist boundary date in JST, typically Sunday 00:00 JST)
    - emotion_monthly:YYYY-MM    (report month, used for 28-day monthly window)
    """
    sc = str(scope or "").strip()
    if sc.startswith("emotion_daily:"):
        s = sc.split(":", 1)[1].strip()
        try:
            y, m, d = [int(x) for x in s.split("-")]
        except Exception:
            raise ValueError(f"Invalid daily scope: {sc}")

        period_start_utc = _jst_midnight_utc(y, m, d)
        period_end_utc = (period_start_utc + DAY) - timedelta(milliseconds=1)
        prev_period_start_utc = period_start_utc - DAY
        prev_period_end_utc = period_start_utc - timedelta(milliseconds=1)
        return {
            "kind": "daily",
            "scope": sc,
            "timezone": "Asia/Tokyo",
            "report_date": f"{y:04d}-{m:02d}-{d:02d}",
            "period_start_utc": period_start_utc,
            "period_end_utc": period_end_utc,
            "period_start_iso": _iso_ms_z(period_start_utc),
            "period_end_iso": _iso_ms_z(period_end_utc),
            "prev_period_start_utc": prev_period_start_utc,
            "prev_period_end_utc": prev_period_end_utc,
            "prev_period_start_iso": _iso_ms_z(prev_period_start_utc),
            "prev_period_end_iso": _iso_ms_z(prev_period_end_utc),
        }

    if sc.startswith("emotion_weekly:"):
        s = sc.split(":", 1)[1].strip()
        try:
            y, m, d = [int(x) for x in s.split("-")]
        except Exception:
            raise ValueError(f"Invalid weekly scope: {sc}")
        dist_utc = _jst_midnight_utc(y, m, d)
        period_start_utc = dist_utc - 7 * DAY
        period_end_utc = dist_utc - timedelta(milliseconds=1)
        return {
            "kind": "weekly",
            "scope": sc,
            "timezone": "Asia/Tokyo",
            "dist_jst": f"{y:04d}-{m:02d}-{d:02d}",
            "dist_utc": dist_utc,
            "period_start_utc": period_start_utc,
            "period_end_utc": period_end_utc,
            "period_start_iso": _iso_ms_z(period_start_utc),
            "period_end_iso": _iso_ms_z(period_end_utc),
        }

    if sc.startswith("emotion_monthly:"):
        s = sc.split(":", 1)[1].strip()
        try:
            y, m = [int(x) for x in s.split("-")]
        except Exception:
            raise ValueError(f"Invalid monthly scope: {sc}")

        # dist = next month 1st 00:00 JST
        if m == 12:
            ny, nm = y + 1, 1
        else:
            ny, nm = y, m + 1
        dist_utc = _jst_midnight_utc(ny, nm, 1)
        period_start_utc = dist_utc - 28 * DAY
        period_end_utc = dist_utc - timedelta(milliseconds=1)
        return {
            "kind": "monthly_28d",
            "scope": sc,
            "timezone": "Asia/Tokyo",
            "report_month": f"{y:04d}-{m:02d}",
            "dist_jst": f"{ny:04d}-{nm:02d}-01",
            "dist_utc": dist_utc,
            "period_start_utc": period_start_utc,
            "period_end_utc": period_end_utc,
            "period_start_iso": _iso_ms_z(period_start_utc),
            "period_end_iso": _iso_ms_z(period_end_utc),
        }

    raise ValueError(f"Unsupported scope: {sc}")


async def fetch_emotions_in_range(
    user_id: str,
    *,
    start_iso: str,
    end_iso: str,
    include_secret: bool,
    page_size: int = 1000,
    max_rows: int = 20000,
) -> List[Dict[str, Any]]:
    """Fetch emotion rows in a period range (for aggregation / period snapshots).

    Uses pagination and caps at max_rows to avoid runaway loads.
    """
    uid = str(user_id or "").strip()
    if not uid:
        return []

    out: List[Dict[str, Any]] = []
    offset = 0
    ps = max(1, int(page_size or 1000))
    mx = max(ps, int(max_rows or 20000))

    while True:
        limit = min(ps, mx - len(out))
        if limit <= 0:
            break

        params: List[Tuple[str, str]] = [
            ("select", "id,created_at,emotions,emotion_details,memo,memo_action,is_secret,emotion_strength_avg"),
            ("user_id", f"eq.{uid}"),
            ("created_at", f"gte.{start_iso}"),
            ("created_at", f"lte.{end_iso}"),
            ("order", "created_at.asc"),
            ("limit", str(limit)),
            ("offset", str(offset)),
        ]
        if not include_secret:
            params.append(("is_secret", "eq.false"))

        rows = await _sb_get_json("/rest/v1/emotions", params=params, timeout=10.0)
        if not rows:
            break

        out.extend(rows)
        if len(rows) < limit:
            break

        offset += limit

    return out


def _normalize_details(row: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Normalize emotion details into [{type, strength}, ...]. (Match MyWeb logic)"""
    details = row.get("emotion_details")
    if isinstance(details, list):
        out = []
        for it in details:
            if isinstance(it, dict):
                t = str(it.get("type") or "").strip()
                s = str(it.get("strength") or "medium").strip().lower()
                if not t:
                    continue
                if t == "自己理解":
                    continue
                if s not in STRENGTH_SCORE:
                    s = "medium"
                out.append({"type": t, "strength": s})
        return out

    emos = row.get("emotions")
    if isinstance(emos, list):
        out = []
        for t in emos:
            tt = str(t or "").strip()
            if not tt:
                continue
            if tt == "自己理解":
                continue
            out.append({"type": tt, "strength": "medium"})
        return out

    return []


def _map_key(jp: str) -> Optional[str]:
    return JP_TO_KEY.get(str(jp).strip())


def _parse_created_at_utc(row: Dict[str, Any]) -> Optional[datetime]:
    """Parse row.created_at into timezone-aware UTC datetime."""
    try:
        t = row.get("created_at")
        if not t:
            return None
        s = str(t)
        if s.endswith("Z"):
            s = s[:-1] + "+00:00"
        dt = datetime.fromisoformat(s)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)
    except Exception:
        return None


def _build_days_fixed7(rows: List[Dict[str, Any]], period_start_utc: datetime) -> List[Dict[str, Any]]:
    buckets: List[Dict[str, Any]] = []
    for i in range(7):
        utc_start = period_start_utc + i * DAY
        j = utc_start.astimezone(JST)
        date_key = f"{j.year:04d}-{j.month:02d}-{j.day:02d}"
        buckets.append(
            {
                "dateKey": date_key,
                "label": f"{j.month}/{j.day}",
                "utcStartMs": int(utc_start.timestamp() * 1000),
                "joy": 0,
                "sadness": 0,
                "anxiety": 0,
                "anger": 0,
                "calm": 0,
                "dominantKey": None,
            }
        )

    for row in rows:
        dt = _parse_created_at_utc(row)
        if dt is None:
            continue

        idx = int(((dt - period_start_utc).total_seconds()) // 86400)
        if idx < 0 or idx >= 7:
            continue
        bucket = buckets[idx]
        for it in _normalize_details(row):
            k = _map_key(it.get("type", ""))
            if not k:
                continue
            w = STRENGTH_SCORE.get(str(it.get("strength", "medium")).lower(), 0)
            bucket[k] += w

    # dominant key per day
    for b in buckets:
        dom = None
        maxv = 0
        for k in EMOTION_KEYS:
            v = int(b.get(k, 0))
            if v > maxv:
                maxv = v
                dom = k if v > 0 else None
        b["dominantKey"] = dom

    return buckets


def _build_day_single(rows: List[Dict[str, Any]], period_start_utc: datetime) -> Dict[str, Any]:
    j = period_start_utc.astimezone(JST)
    bucket: Dict[str, Any] = {
        "dateKey": f"{j.year:04d}-{j.month:02d}-{j.day:02d}",
        "label": f"{j.month}/{j.day}",
        "utcStartMs": int(period_start_utc.timestamp() * 1000),
        "joy": 0,
        "sadness": 0,
        "anxiety": 0,
        "anger": 0,
        "calm": 0,
        "dominantKey": None,
    }

    for row in rows:
        for it in _normalize_details(row):
            k = _map_key(it.get("type", ""))
            if not k:
                continue
            w = STRENGTH_SCORE.get(str(it.get("strength", "medium")).lower(), 0)
            bucket[k] += w

    dom = None
    maxv = 0
    for k in EMOTION_KEYS:
        v = int(bucket.get(k, 0))
        if v > maxv:
            maxv = v
            dom = k if v > 0 else None
    bucket["dominantKey"] = dom
    return bucket


def _build_weeks_fixed4(rows: List[Dict[str, Any]], period_start_utc: datetime) -> List[Dict[str, Any]]:
    buckets: List[Dict[str, Any]] = [
        {"index": 0, "label": "第1週", "joy": 0, "sadness": 0, "anxiety": 0, "anger": 0, "calm": 0, "total": 0},
        {"index": 1, "label": "第2週", "joy": 0, "sadness": 0, "anxiety": 0, "anger": 0, "calm": 0, "total": 0},
        {"index": 2, "label": "第3週", "joy": 0, "sadness": 0, "anxiety": 0, "anger": 0, "calm": 0, "total": 0},
        {"index": 3, "label": "第4週", "joy": 0, "sadness": 0, "anxiety": 0, "anger": 0, "calm": 0, "total": 0},
    ]

    for row in rows:
        dt = _parse_created_at_utc(row)
        if dt is None:
            continue

        idx_raw = int(((dt - period_start_utc).total_seconds()) // (7 * 86400))
        idx = max(0, min(3, idx_raw))
        bucket = buckets[idx]

        for it in _normalize_details(row):
            k = _map_key(it.get("type", ""))
            if not k:
                continue
            w = STRENGTH_SCORE.get(str(it.get("strength", "medium")).lower(), 0)
            bucket[k] += w
            bucket["total"] += w

    return buckets


def _compute_weekly_metrics(days: List[Dict[str, Any]]) -> Dict[str, Any]:
    totals = {k: 0 for k in EMOTION_KEYS}
    for d in days:
        for k in EMOTION_KEYS:
            totals[k] += int(d.get(k, 0))
    total_all = sum(totals.values())
    share_pct = {k: 0 for k in EMOTION_KEYS}
    if total_all > 0:
        for k in EMOTION_KEYS:
            share_pct[k] = int(round((totals[k] / total_all) * 100))
    top = sorted([[k, totals[k]] for k in EMOTION_KEYS], key=lambda x: x[1], reverse=True)
    return {
        "totals": totals,
        "totalAll": total_all,
        "sharePct": share_pct,
        "top": top,
        "hasData": total_all > 0,
    }


def _compute_monthly_metrics(weeks: List[Dict[str, Any]]) -> Dict[str, Any]:
    totals = {k: 0 for k in EMOTION_KEYS}
    for w in weeks:
        for k in EMOTION_KEYS:
            totals[k] += int(w.get(k, 0))
    total_all = sum(totals.values())
    share_pct = {k: 0 for k in EMOTION_KEYS}
    if total_all > 0:
        for k in EMOTION_KEYS:
            share_pct[k] = int(round((totals[k] / total_all) * 100))
    return {
        "weeks": weeks,
        "totals": totals,
        "totalAll": total_all,
        "sharePct": share_pct,
        "hasData": total_all > 0,
    }


def _compute_daily_metrics(day: Dict[str, Any]) -> Dict[str, Any]:
    totals = {k: int(day.get(k, 0)) for k in EMOTION_KEYS}
    total_all = sum(totals.values())
    share_pct = {k: 0 for k in EMOTION_KEYS}
    if total_all > 0:
        for k in EMOTION_KEYS:
            share_pct[k] = int(round((totals[k] / total_all) * 100))
    top = sorted([[k, totals[k]] for k in EMOTION_KEYS], key=lambda x: x[1], reverse=True)
    return {
        "totals": totals,
        "totalAll": total_all,
        "sharePct": share_pct,
        "top": top,
        "hasData": total_all > 0,
    }


def _compute_daily_movement(today_metrics: Dict[str, Any], prev_metrics: Dict[str, Any], *, dominant_today: Optional[str], dominant_yesterday: Optional[str]) -> Dict[str, Any]:
    total_today = int((today_metrics or {}).get("totalAll") or 0)
    total_yesterday = int((prev_metrics or {}).get("totalAll") or 0)
    diff_total = total_today - total_yesterday
    abs_diff = abs(diff_total)

    dominant_changed = bool(dominant_today and dominant_yesterday and dominant_today != dominant_yesterday)
    if dominant_changed:
        motion_key = "swing"
        motion_label = "揺れ"
    else:
        ratio = (abs_diff / max(total_yesterday, 1)) if abs_diff > 0 else 0.0
        if abs_diff <= 1 or ratio <= 0.2:
            motion_key = "stable"
            motion_label = "安定"
        elif diff_total > 0:
            motion_key = "up"
            motion_label = "上昇"
        elif diff_total < 0:
            motion_key = "down"
            motion_label = "減少"
        else:
            motion_key = "stable"
            motion_label = "安定"

    return {
        "ruleVersion": "daily_motion.v1",
        "key": motion_key,
        "label": motion_label,
        "totalToday": total_today,
        "totalYesterday": total_yesterday,
        "diffTotal": diff_total,
        "dominantToday": dominant_today,
        "dominantYesterday": dominant_yesterday,
        "thresholds": {
            "absStableMax": 1,
            "ratioStableMax": 0.2,
            "dominantChangeFirst": True,
        },
    }


def build_emotion_period_payload(
    *,
    scope: str,
    snapshot_type: str,
    source_hash: str,
    total_rows: int,
    public_rows: int,
    secret_rows: int,
    period_meta: Dict[str, Any],
    views: Dict[str, Any],
) -> Dict[str, Any]:
    """Build payload for emotion period snapshots (weekly/monthly)."""
    return {
        "version": "emotion_period.v1",
        "scope": scope,
        "snapshot_type": snapshot_type,
        "source_hash": source_hash,
        "generated_at": _now_iso_z(),
        "period": period_meta,
        "summary": {
            "emotions_total": int(total_rows),
            "emotions_public": int(public_rows),
            "emotions_secret": int(secret_rows),
        },
        "views": views or {},
    }


async def _generate_and_store_emotion_period_snapshots(
    *,
    user_id: str,
    scope: str,
    trigger: str,
) -> Dict[str, Any]:
    """Generate internal/public emotion period snapshots (daily/weekly/monthly) and store them."""
    uid = str(user_id or "").strip()
    if not uid:
        raise ValueError("user_id is required")

    sc = str(scope or "").strip()
    info = _parse_emotion_period_scope(sc)
    kind = str(info.get("kind") or "")
    period_start_iso = str(info.get("period_start_iso") or "").strip()
    period_end_iso = str(info.get("period_end_iso") or "").strip()
    period_start_utc = info.get("period_start_utc")
    if not isinstance(period_start_utc, datetime):
        raise ValueError(f"Invalid period_start_utc for scope: {sc}")

    prev_period_start_iso = str(info.get("prev_period_start_iso") or "").strip()
    prev_period_end_iso = str(info.get("prev_period_end_iso") or "").strip()
    prev_period_start_utc = info.get("prev_period_start_utc")

    # 1) Fetch meta rows for hashing within the target period (includes secret flag)
    meta = await fetch_emotion_meta_for_hash(uid, start_iso=period_start_iso, end_iso=period_end_iso)

    # 2) Fetch rows for aggregation (bounded)
    internal_rows = await fetch_emotions_in_range(uid, start_iso=period_start_iso, end_iso=period_end_iso, include_secret=True)
    public_rows_data = await fetch_emotions_in_range(uid, start_iso=period_start_iso, end_iso=period_end_iso, include_secret=False)

    prev_meta: List[Dict[str, Any]] = []
    prev_internal_rows: List[Dict[str, Any]] = []
    prev_public_rows_data: List[Dict[str, Any]] = []
    if kind == "daily" and prev_period_start_iso and prev_period_end_iso:
        prev_meta = await fetch_emotion_meta_for_hash(uid, start_iso=prev_period_start_iso, end_iso=prev_period_end_iso)
        prev_internal_rows = await fetch_emotions_in_range(uid, start_iso=prev_period_start_iso, end_iso=prev_period_end_iso, include_secret=True)
        prev_public_rows_data = await fetch_emotions_in_range(uid, start_iso=prev_period_start_iso, end_iso=prev_period_end_iso, include_secret=False)

    # 2.5) Exclude "自己理解" rows from emotion structure materials (MyWeb).
    #      InputScreen provides SELF_INSIGHT as a dedicated emotion button.
    def _is_self_insight_only(row: Dict[str, Any]) -> bool:
        # Treat as self-insight-only only when all emotion labels are "自己理解".
        details = row.get("emotion_details")
        if isinstance(details, list):
            types = []
            for it in details:
                if not isinstance(it, dict):
                    continue
                t = str(it.get("type") or "").strip()
                if t:
                    types.append(t)
            if types:
                return all(t == "自己理解" for t in types)

        emos = row.get("emotions")
        if isinstance(emos, list):
            types = [str(t or "").strip() for t in emos if str(t or "").strip()]
            if types:
                return all(t == "自己理解" for t in types)

        return False

    exclude_ids = {str(r.get("id") or "") for r in internal_rows if _is_self_insight_only(r)}
    if exclude_ids:
        meta = [r for r in meta if str(r.get("id") or "") not in exclude_ids]
        internal_rows = [r for r in internal_rows if str(r.get("id") or "") not in exclude_ids]
        public_rows_data = [r for r in public_rows_data if str(r.get("id") or "") not in exclude_ids]

    prev_exclude_ids = {str(r.get("id") or "") for r in prev_internal_rows if _is_self_insight_only(r)}
    if prev_exclude_ids:
        prev_meta = [r for r in prev_meta if str(r.get("id") or "") not in prev_exclude_ids]
        prev_internal_rows = [r for r in prev_internal_rows if str(r.get("id") or "") not in prev_exclude_ids]
        prev_public_rows_data = [r for r in prev_public_rows_data if str(r.get("id") or "") not in prev_exclude_ids]

    # 3) Compute counts / hashes for this scope (after filtering)
    total_rows = len(meta)
    secret_rows = sum(1 for r in meta if bool(r.get("is_secret")))
    public_rows = total_rows - secret_rows

    hash_meta = meta
    if kind == "daily" and prev_meta:
        hash_meta = sorted(
            [*prev_meta, *meta],
            key=lambda r: (str(r.get("created_at") or ""), str(r.get("id") or "")),
        )

    internal_hash = compute_source_hash_from_emotion_meta(user_id=uid, scope=sc, snapshot_type="internal", meta_rows=hash_meta)
    public_hash = compute_source_hash_from_emotion_meta(user_id=uid, scope=sc, snapshot_type="public", meta_rows=hash_meta)

    # 4) Build views (match MyWeb structure)
    if kind == "daily":
        if not isinstance(prev_period_start_utc, datetime):
            raise ValueError(f"Invalid prev_period_start_utc for scope: {sc}")

        internal_day = _build_day_single(internal_rows, period_start_utc)
        public_day = _build_day_single(public_rows_data, period_start_utc)
        prev_internal_day = _build_day_single(prev_internal_rows, prev_period_start_utc)
        prev_public_day = _build_day_single(prev_public_rows_data, prev_period_start_utc)

        internal_metrics = _compute_daily_metrics(internal_day)
        public_metrics = _compute_daily_metrics(public_day)
        prev_internal_metrics = _compute_daily_metrics(prev_internal_day)
        prev_public_metrics = _compute_daily_metrics(prev_public_day)

        internal_movement = _compute_daily_movement(
            internal_metrics,
            prev_internal_metrics,
            dominant_today=internal_day.get("dominantKey"),
            dominant_yesterday=prev_internal_day.get("dominantKey"),
        )
        public_movement = _compute_daily_movement(
            public_metrics,
            prev_public_metrics,
            dominant_today=public_day.get("dominantKey"),
            dominant_yesterday=prev_public_day.get("dominantKey"),
        )

        internal_views = {
            "day": internal_day,
            "metrics": internal_metrics,
            "movement": internal_movement,
        }
        public_views = {
            "day": public_day,
            "metrics": public_metrics,
            "movement": public_movement,
        }
        period_meta = {
            "type": "daily",
            "timezone": info.get("timezone") or "Asia/Tokyo",
            "reportDate": info.get("report_date"),
            "periodStartIso": period_start_iso,
            "periodEndIso": period_end_iso,
            "previousPeriodStartIso": prev_period_start_iso,
            "previousPeriodEndIso": prev_period_end_iso,
        }
    elif kind == "weekly":
        internal_days = _build_days_fixed7(internal_rows, period_start_utc)
        public_days = _build_days_fixed7(public_rows_data, period_start_utc)
        internal_metrics = _compute_weekly_metrics(internal_days)
        public_metrics = _compute_weekly_metrics(public_days)
        internal_views = {"days": internal_days, "metrics": internal_metrics}
        public_views = {"days": public_days, "metrics": public_metrics}
        period_meta = {
            "type": "weekly",
            "timezone": info.get("timezone") or "Asia/Tokyo",
            "distJst": info.get("dist_jst"),
            "periodStartIso": period_start_iso,
            "periodEndIso": period_end_iso,
        }
    else:
        internal_weeks = _build_weeks_fixed4(internal_rows, period_start_utc)
        public_weeks = _build_weeks_fixed4(public_rows_data, period_start_utc)
        internal_metrics = _compute_monthly_metrics(internal_weeks)
        public_metrics = _compute_monthly_metrics(public_weeks)
        internal_views = {"weeks": internal_weeks, "metrics": internal_metrics}
        public_views = {"weeks": public_weeks, "metrics": public_metrics}
        period_meta = {
            "type": "monthly_28d",
            "timezone": info.get("timezone") or "Asia/Tokyo",
            "reportMonth": info.get("report_month"),
            "distJst": info.get("dist_jst"),
            "periodStartIso": period_start_iso,
            "periodEndIso": period_end_iso,
        }

    internal_payload = build_emotion_period_payload(
        scope=sc,
        snapshot_type="internal",
        source_hash=internal_hash,
        total_rows=total_rows,
        public_rows=public_rows,
        secret_rows=secret_rows,
        period_meta=period_meta,
        views=internal_views,
    )
    public_payload = build_emotion_period_payload(
        scope=sc,
        snapshot_type="public",
        source_hash=public_hash,
        total_rows=total_rows,
        public_rows=public_rows,
        secret_rows=secret_rows,
        period_meta=period_meta,
        views=public_views,
    )

    # 5) Store snapshots
    inserted_internal = await _insert_snapshot_row(user_id=uid, scope=sc, snapshot_type="internal", source_hash=internal_hash, payload=internal_payload)
    inserted_public = await _insert_snapshot_row(user_id=uid, scope=sc, snapshot_type="public", source_hash=public_hash, payload=public_payload)

    # 5.5) Downstream: enqueue emotion structure analysis (standard) for latest public snapshot.
    #      Best-effort and safe to call multiple times because job_key coalesces.
    try:
        if callable(enqueue_job):
            latest_public = await _fetch_latest_snapshot_meta(uid, scope=sc, snapshot_type="public")
            latest_public_hash = str((latest_public or {}).get("source_hash") or "").strip()
            latest_public_snapshot_id = str((latest_public or {}).get("id") or "").strip()
            if latest_public_hash:
                await enqueue_job(
                    job_key=f"analysis_emotion_structure_standard:{uid}:{sc}:{latest_public_hash}",
                    job_type="analyze_emotion_structure_standard_v1",
                    user_id=uid,
                    payload={
                        "trigger": "material_snapshot_emotion_period",
                        "scope": sc,
                        "source_hash": latest_public_hash,
                        "snapshot_id": latest_public_snapshot_id,
                        "requested_at": _now_iso_z(),
                    },
                    priority=18,
                )
    except Exception as exc:
        logger.error("Failed to enqueue analyze_emotion_structure_standard_v1: %s", exc)

    logger.info(
        "emotion_period snapshots generated. user=%s scope=%s internal=%s public=%s trigger=%s",
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
        "period": period_meta,
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

    Global snapshots now include:
    - views.emotions_recent
    - views.self_structure_view
    - views.premium_reflection_view
    """
    uid = str(user_id or "").strip()
    if not uid:
        raise ValueError("user_id is required")
    if not _has_supabase_config():
        raise RuntimeError("Supabase config missing")

    sc = str(scope or "").strip() or SNAPSHOT_SCOPE_DEFAULT

    if _is_emotion_period_scope(sc):
        return await _generate_and_store_emotion_period_snapshots(user_id=uid, scope=sc, trigger=trigger)

    # Legacy emotion stats / recent view
    emotion_meta = await fetch_emotion_meta_for_hash(uid)
    emotion_total_rows = len(emotion_meta)
    emotion_secret_rows = sum(1 for r in emotion_meta if _row_is_secret(r))
    emotion_public_rows = emotion_total_rows - emotion_secret_rows

    internal_recent = await fetch_recent_emotions(uid, include_secret=True)
    public_recent = await fetch_recent_emotions(uid, include_secret=False)

    # Global cumulative materials for self structure analysis
    internal_emotion_rows = await fetch_emotions_for_self_structure(uid, include_secret=True)
    public_emotion_rows = await fetch_emotions_for_self_structure(uid, include_secret=False)

    internal_mymodel_rows = await fetch_mymodel_create_rows_for_self_structure(uid, include_secret=True)
    public_mymodel_rows = await fetch_mymodel_create_rows_for_self_structure(uid, include_secret=False)

    internal_deep_rows = await fetch_deep_insight_rows_for_self_structure(uid, include_secret=True)
    public_deep_rows = await fetch_deep_insight_rows_for_self_structure(uid, include_secret=False)

    # Premium Reflections are intentionally built from public-safe materials only
    # to avoid secret contamination in topic clustering / question / answer generation.
    premium_reflection_emotion_rows = await fetch_emotions_for_premium_reflection(uid, include_secret=False)
    premium_reflection_deep_rows = public_deep_rows

    internal_echo_rows = await fetch_echo_rows_for_self_structure(uid, include_secret=True)
    public_echo_rows = await fetch_echo_rows_for_self_structure(uid, include_secret=False)

    internal_discovery_rows = await fetch_discovery_rows_for_self_structure(uid, include_secret=True)
    public_discovery_rows = await fetch_discovery_rows_for_self_structure(uid, include_secret=False)

    internal_self_structure_view = build_self_structure_view(
        emotion_rows=internal_emotion_rows,
        mymodel_rows=internal_mymodel_rows,
        deep_insight_rows=internal_deep_rows,
        echo_rows=internal_echo_rows,
        discovery_rows=internal_discovery_rows,
    )
    public_self_structure_view = build_self_structure_view(
        emotion_rows=public_emotion_rows,
        mymodel_rows=public_mymodel_rows,
        deep_insight_rows=public_deep_rows,
        echo_rows=public_echo_rows,
        discovery_rows=public_discovery_rows,
    )

    premium_reflection_view = build_premium_reflection_view(
        emotion_rows=premium_reflection_emotion_rows,
        deep_insight_rows=premium_reflection_deep_rows,
    )

    internal_material_meta: List[Dict[str, Any]] = []
    internal_material_meta.extend(_material_meta_rows_from_rows("emotion_input", internal_emotion_rows))
    internal_material_meta.extend(_material_meta_rows_from_rows("mymodel_create", internal_mymodel_rows))
    internal_material_meta.extend(_material_meta_rows_from_rows("deep_insight", internal_deep_rows))
    internal_material_meta.extend(_material_meta_rows_from_rows("echo", internal_echo_rows))
    internal_material_meta.extend(_material_meta_rows_from_rows("discovery", internal_discovery_rows))
    internal_material_meta = _dedupe_material_meta_rows(internal_material_meta)

    internal_hash = compute_source_hash_from_material_meta(
        user_id=uid,
        scope=sc,
        snapshot_type="internal",
        meta_rows=internal_material_meta,
    )
    public_hash = compute_source_hash_from_material_meta(
        user_id=uid,
        scope=sc,
        snapshot_type="public",
        meta_rows=internal_material_meta,
    )

    internal_views = _build_global_views(
        recent_emotions=internal_recent,
        self_structure_view=internal_self_structure_view,
        premium_reflection_view=premium_reflection_view,
    )
    public_views = _build_global_views(
        recent_emotions=public_recent,
        self_structure_view=public_self_structure_view,
        premium_reflection_view=premium_reflection_view,
    )

    internal_summary = _build_global_summary(
        material_meta=internal_material_meta,
        emotion_total_rows=emotion_total_rows,
        emotion_public_rows=emotion_public_rows,
        emotion_secret_rows=emotion_secret_rows,
        self_structure_view=internal_self_structure_view,
        premium_reflection_view=premium_reflection_view,
    )
    public_summary = _build_global_summary(
        material_meta=[r for r in internal_material_meta if not _row_is_secret(r)],
        emotion_total_rows=emotion_total_rows,
        emotion_public_rows=emotion_public_rows,
        emotion_secret_rows=emotion_secret_rows,
        self_structure_view=public_self_structure_view,
        premium_reflection_view=premium_reflection_view,
    )

    internal_payload = build_snapshot_payload(
        scope=sc,
        snapshot_type="internal",
        source_hash=internal_hash,
        summary=internal_summary,
        views=internal_views,
    )
    public_payload = build_snapshot_payload(
        scope=sc,
        snapshot_type="public",
        source_hash=public_hash,
        summary=public_summary,
        views=public_views,
    )

    inserted_internal = await _insert_snapshot_row(user_id=uid, scope=sc, snapshot_type="internal", source_hash=internal_hash, payload=internal_payload)
    inserted_public = await _insert_snapshot_row(user_id=uid, scope=sc, snapshot_type="public", source_hash=public_hash, payload=public_payload)

    # Keep existing emotion_period downstream only; self structure analysis is enqueued by worker.
    try:
        if sc == SNAPSHOT_SCOPE_DEFAULT and callable(enqueue_job):
            requested_at = _now_iso_z()
            weekly_scope = _latest_weekly_scope_for_now()
            monthly_scope = _latest_monthly_scope_for_now()

            await enqueue_job(
                job_key=f"snapshot_generate_v1:{uid}:{weekly_scope}",
                job_type="snapshot_generate_v1",
                user_id=uid,
                payload={
                    "scope": weekly_scope,
                    "trigger": "material_snapshot_global",
                    "requested_at": requested_at,
                },
                priority=12,
            )
            await enqueue_job(
                job_key=f"snapshot_generate_v1:{uid}:{monthly_scope}",
                job_type="snapshot_generate_v1",
                user_id=uid,
                payload={
                    "scope": monthly_scope,
                    "trigger": "material_snapshot_global",
                    "requested_at": requested_at,
                },
                priority=12,
            )
    except Exception as exc:
        logger.error("Failed to enqueue downstream emotion_period snapshots: %s", exc)

    logger.info(
        "material_snapshots generated. user=%s scope=%s internal=%s public=%s trigger=%s self_items=%s premium_items=%s",
        uid,
        sc,
        internal_hash[:10],
        public_hash[:10],
        trigger,
        len((internal_self_structure_view or {}).get("items") or []),
        len((premium_reflection_view or {}).get("items") or []),
    )

    material_secret_rows = sum(1 for r in internal_material_meta if _row_is_secret(r))
    material_total_rows = len(internal_material_meta)

    return {
        "status": "ok",
        "user_id": uid,
        "scope": sc,
        "trigger": trigger,
        "internal": {"source_hash": internal_hash, "inserted": bool(inserted_internal)},
        "public": {"source_hash": public_hash, "inserted": bool(inserted_public)},
        "counts": {
            "total": material_total_rows,
            "public": material_total_rows - material_secret_rows,
            "secret": material_secret_rows,
            "source_counts": (internal_self_structure_view or {}).get("source_counts") or {},
            "self_structure_items": len((internal_self_structure_view or {}).get("items") or []),
            "premium_reflection_items": len((premium_reflection_view or {}).get("items") or []),
        },
    }

