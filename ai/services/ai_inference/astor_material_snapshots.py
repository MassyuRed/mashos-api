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



def _iso_ms_z(dt: datetime) -> str:
    """UTC ISO string with milliseconds (JS-like)."""
    return dt.astimezone(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")


def _jst_midnight_utc(year: int, month: int, day: int) -> datetime:
    """JSTの指定日 00:00 を UTC datetime で返す。"""
    jst_dt = datetime(year, month, day, 0, 0, 0, 0, tzinfo=JST)
    return jst_dt.astimezone(timezone.utc)


def _is_emotion_period_scope(scope: str) -> bool:
    sc = str(scope or "").strip()
    return bool(sc.startswith("emotion_weekly:") or sc.startswith("emotion_monthly:"))


def _parse_emotion_period_scope(scope: str) -> Dict[str, Any]:
    """Parse emotion period scope and return period boundaries.

    Supported scopes:
    - emotion_weekly:YYYY-MM-DD  (dist boundary date in JST, typically Sunday 00:00 JST)
    - emotion_monthly:YYYY-MM    (report month, used for 28-day monthly window)
    """
    sc = str(scope or "").strip()
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
    """Generate internal/public emotion period snapshots (weekly/monthly) and store them."""
    uid = str(user_id or "").strip()
    if not uid:
        raise ValueError("user_id is required")

    sc = str(scope or "").strip()
    info = _parse_emotion_period_scope(sc)
    period_start_iso = str(info.get("period_start_iso") or "").strip()
    period_end_iso = str(info.get("period_end_iso") or "").strip()
    period_start_utc = info.get("period_start_utc")
    if not isinstance(period_start_utc, datetime):
        raise ValueError(f"Invalid period_start_utc for scope: {sc}")

    # 1) Fetch meta rows for hashing within the period (includes secret flag)
    meta = await fetch_emotion_meta_for_hash(uid, start_iso=period_start_iso, end_iso=period_end_iso)

    # 2) Fetch rows for aggregation (bounded)
    internal_rows = await fetch_emotions_in_range(uid, start_iso=period_start_iso, end_iso=period_end_iso, include_secret=True)
    public_rows_data = await fetch_emotions_in_range(uid, start_iso=period_start_iso, end_iso=period_end_iso, include_secret=False)

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

    # 3) Compute counts / hashes for this scope (after filtering)
    total_rows = len(meta)
    secret_rows = sum(1 for r in meta if bool(r.get("is_secret")))
    public_rows = total_rows - secret_rows

    internal_hash = compute_source_hash_from_emotion_meta(user_id=uid, scope=sc, snapshot_type="internal", meta_rows=meta)
    public_hash = compute_source_hash_from_emotion_meta(user_id=uid, scope=sc, snapshot_type="public", meta_rows=meta)

    # 4) Build views (match MyWeb structure)
    kind = str(info.get("kind") or "")
    if kind == "weekly":
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


    # emotion_period snapshots (weekly/monthly): build period material snapshots (days/weeks/metrics)
    if _is_emotion_period_scope(sc):
        return await _generate_and_store_emotion_period_snapshots(user_id=uid, scope=sc, trigger=trigger)

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
