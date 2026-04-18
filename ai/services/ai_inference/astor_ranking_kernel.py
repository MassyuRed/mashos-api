# -*- coding: utf-8 -*-
"""Ranking board generation kernel for ASTOR (Phase 1).

Purpose
-------
既存の Supabase RPC ベース Ranking 計算式をそのまま活かしつつ、
ASTOR worker から machine-readable な global board payload を生成する。

Phase 1 policy
--------------
- 計算 kernel は既存 SQL/RPC をそのまま利用する
- 本モジュールは「RPC 実行」と「board payload 正規化」だけを担当する
- display_name / visibility / private flag など presentation 情報はここでは保存しない
- board 保存・READY 昇格は `astor_ranking_boards.py` 側で担当する

Notes
-----
- emotions は aggregate board
- それ以外は user leaderboard
- range は day/week/month/year の 4 系統を board に持つ
"""

from __future__ import annotations

import logging
import os
from datetime import datetime, timezone
from typing import Any, Callable, Dict, Iterable, List, Mapping, MutableMapping, Optional, Sequence

from supabase_client import ensure_supabase_config, sb_post_rpc
from astor_ranking_boards import (
    RANKING_BOARD_TIMEZONE,
    RANKING_BOARD_VERSION,
    normalize_board_payload,
)
from piece_generated_metrics import build_piece_generated_ranking_rows

logger = logging.getLogger("astor_ranking_kernel")


RANKING_RANGE_KEYS: Sequence[str] = ("day", "week", "month", "year")

try:
    DEFAULT_RANKING_LIMIT = int(
        os.getenv("ASTOR_RANKING_BOARD_LIMIT", os.getenv("COCOLON_RANKING_BOARD_LIMIT", "100")) or "100"
    )
except Exception:
    DEFAULT_RANKING_LIMIT = 100
DEFAULT_RANKING_LIMIT = max(1, min(int(DEFAULT_RANKING_LIMIT or 100), 500))

SUPPORTED_RANKING_METRICS: Sequence[str] = (
    "emotions",
    "input_count",
    "input_length",
    "mymodel_questions",
    "login_streak",
    "mymodel_views",
    "mymodel_resonances",
    "mymodel_discoveries",
)


def _now_iso_z() -> str:
    return (
        datetime.now(timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )


def _canonical_metric_key(value: Any) -> str:
    return str(value or "").strip().lower()


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
    if s in {"day", "week", "month", "year"}:
        return s
    return s or "week"


def _coerce_int(value: Any, default: int = 0) -> int:
    try:
        return int(value or 0)
    except Exception:
        return int(default)


def _coerce_text(value: Any) -> Optional[str]:
    if value is None:
        return None
    s = str(value).strip()
    return s or None


async def _rpc_rows(fn: str, payload: Mapping[str, Any]) -> List[Dict[str, Any]]:
    ensure_supabase_config()
    resp = await sb_post_rpc(str(fn or "").strip(), dict(payload or {}), timeout=10.0)
    if resp.status_code >= 300:
        body = (resp.text or "")[:1500]
        logger.error("ranking rpc failed: fn=%s status=%s body=%s", fn, resp.status_code, body)
        raise RuntimeError(f"ranking rpc failed: {fn} ({resp.status_code})")
    try:
        data = resp.json()
    except Exception as exc:
        logger.error("ranking rpc returned non-json: fn=%s err=%s", fn, exc)
        raise RuntimeError(f"ranking rpc returned invalid json: {fn}") from exc
    if not isinstance(data, list):
        return []
    return [row for row in data if isinstance(row, dict)]


def _strip_presentation_fields(row: MutableMapping[str, Any]) -> None:
    for key in (
        "display_name",
        "username",
        "avatar_url",
        "profile_image_url",
        "is_private_account",
        "is_ranking_visible",
        "private_account",
        "ranking_visible",
    ):
        row.pop(key, None)


def _normalize_emotions_rows(rows: Iterable[Mapping[str, Any]]) -> List[Dict[str, Any]]:
    items: List[Dict[str, Any]] = []
    for raw in rows or []:
        if not isinstance(raw, Mapping):
            continue
        emotion = _coerce_text(raw.get("emotion"))
        if not emotion:
            continue
        count = _coerce_int(raw.get("count"), 0)
        rank = _coerce_int(raw.get("rank"), 0)
        items.append(
            {
                "rank": rank or (len(items) + 1),
                "emotion": emotion,
                "count": count,
                "value": count,
            }
        )
    items.sort(key=lambda x: (int(x.get("rank") or 0), str(x.get("emotion") or "")))
    return items


def _normalize_user_rows(
    rows: Iterable[Mapping[str, Any]],
    *,
    value_keys: Sequence[str],
    primary_value_key: str,
    extra_fields: Optional[Sequence[str]] = None,
) -> List[Dict[str, Any]]:
    items: List[Dict[str, Any]] = []
    extra_fields = tuple(extra_fields or ())
    for raw in rows or []:
        if not isinstance(raw, Mapping):
            continue
        uid = _coerce_text(raw.get("user_id"))
        if not uid:
            continue
        rank = _coerce_int(raw.get("rank"), 0)

        value = None
        for key in value_keys:
            if raw.get(key) is not None:
                value = _coerce_int(raw.get(key), 0)
                break
        if value is None:
            value = 0

        item: Dict[str, Any] = {
            "rank": rank or (len(items) + 1),
            "user_id": uid,
            primary_value_key: int(value),
            "value": int(value),
        }
        for key in extra_fields:
            if key in raw:
                item[key] = raw.get(key)
        _strip_presentation_fields(item)
        items.append(item)

    items.sort(key=lambda x: (int(x.get("rank") or 0), str(x.get("user_id") or "")))
    return items


def _normalize_input_count_rows(rows: Iterable[Mapping[str, Any]]) -> List[Dict[str, Any]]:
    return _normalize_user_rows(
        rows,
        value_keys=("input_count", "count", "value"),
        primary_value_key="input_count",
    )


def _normalize_input_length_rows(rows: Iterable[Mapping[str, Any]]) -> List[Dict[str, Any]]:
    return _normalize_user_rows(
        rows,
        value_keys=("total_chars", "input_length", "chars", "value"),
        primary_value_key="total_chars",
    )


def _normalize_mymodel_questions_rows(rows: Iterable[Mapping[str, Any]]) -> List[Dict[str, Any]]:
    base_items = _normalize_user_rows(
        rows,
        value_keys=("piece_generated_total", "mymodel_questions_total", "questions_total", "value"),
        primary_value_key="piece_generated_total",
    )
    out: List[Dict[str, Any]] = []
    for item in base_items:
        value = _coerce_int(item.get("piece_generated_total"), 0)
        out.append({
            **item,
            "piece_generated_total": value,
            "mymodel_questions_total": value,
            "questions_total": value,
            "value": value,
        })
    return out


def _normalize_login_streak_rows(rows: Iterable[Mapping[str, Any]]) -> List[Dict[str, Any]]:
    items = _normalize_user_rows(
        rows,
        value_keys=("streak_days", "streak", "days", "value"),
        primary_value_key="streak_days",
        extra_fields=("last_login_date", "last_date"),
    )
    out: List[Dict[str, Any]] = []
    for item in items:
        last_login_date = item.pop("last_date", None)
        if item.get("last_login_date") is None:
            item["last_login_date"] = _coerce_text(last_login_date)
        else:
            item["last_login_date"] = _coerce_text(item.get("last_login_date"))
        out.append(item)
    return out


def _normalize_mymodel_views_rows(rows: Iterable[Mapping[str, Any]]) -> List[Dict[str, Any]]:
    return _normalize_user_rows(
        rows,
        value_keys=("view_count", "views", "value"),
        primary_value_key="view_count",
    )


def _normalize_mymodel_resonances_rows(rows: Iterable[Mapping[str, Any]]) -> List[Dict[str, Any]]:
    return _normalize_user_rows(
        rows,
        value_keys=("resonance_count", "resonances", "value"),
        primary_value_key="resonance_count",
    )


def _normalize_mymodel_discoveries_rows(rows: Iterable[Mapping[str, Any]]) -> List[Dict[str, Any]]:
    return _normalize_user_rows(
        rows,
        value_keys=("discovery_count", "discoveries", "value"),
        primary_value_key="discovery_count",
    )


MetricNormalizer = Callable[[Iterable[Mapping[str, Any]]], List[Dict[str, Any]]]


_METRIC_CONFIG: Dict[str, Dict[str, Any]] = {
    "emotions": {
        "rpc_fn": "rank_emotions",
        "uses_limit": False,
        "normalizer": _normalize_emotions_rows,
    },
    "input_count": {
        "rpc_fn": "rank_input_count_v2",
        "uses_limit": True,
        "normalizer": _normalize_input_count_rows,
    },
    "input_length": {
        "rpc_fn": "rank_input_length_v2",
        "uses_limit": True,
        "normalizer": _normalize_input_length_rows,
    },
    "mymodel_questions": {
        "rpc_fn": "rank_mymodel_questions_v2",
        "uses_limit": True,
        "normalizer": _normalize_mymodel_questions_rows,
    },
    "login_streak": {
        "rpc_fn": "rank_login_streak",
        "uses_limit": True,
        "normalizer": _normalize_login_streak_rows,
    },
    "mymodel_views": {
        "rpc_fn": "rank_mymodel_views",
        "uses_limit": True,
        "normalizer": _normalize_mymodel_views_rows,
    },
    "mymodel_resonances": {
        "rpc_fn": "rank_mymodel_resonances",
        "uses_limit": True,
        "normalizer": _normalize_mymodel_resonances_rows,
    },
    "mymodel_discoveries": {
        "rpc_fn": "rank_mymodel_discoveries",
        "uses_limit": True,
        "normalizer": _normalize_mymodel_discoveries_rows,
    },
}


def get_metric_config(metric_key: str) -> Dict[str, Any]:
    mk = _canonical_metric_key(metric_key)
    cfg = _METRIC_CONFIG.get(mk)
    if not cfg:
        raise ValueError(f"Unsupported ranking metric: {metric_key}")
    return cfg


async def generate_metric_range_rows(
    metric_key: str,
    *,
    range_key: str,
    limit: Optional[int] = None,
) -> List[Dict[str, Any]]:
    """Generate normalized raw rows for one metric and one range."""
    mk = _canonical_metric_key(metric_key)
    rk = _canonical_range_key(range_key)
    if rk not in RANKING_RANGE_KEYS:
        raise ValueError(f"Unsupported ranking range: {range_key}")

    if mk == "mymodel_questions":
        rows = await build_piece_generated_ranking_rows(range_key=rk)
        if limit is not None:
            return list(rows[: max(1, int(limit))])
        return rows

    cfg = get_metric_config(mk)
    rpc_fn = str(cfg.get("rpc_fn") or "").strip()
    normalizer: MetricNormalizer = cfg["normalizer"]

    payload: Dict[str, Any] = {"p_range": rk}
    if bool(cfg.get("uses_limit")):
        payload["p_limit"] = int(limit or DEFAULT_RANKING_LIMIT)

    rows = await _rpc_rows(rpc_fn, payload)
    return normalizer(rows)


async def generate_ranking_board(
    metric_key: str,
    *,
    limit: Optional[int] = None,
    range_keys: Optional[Sequence[str]] = None,
) -> Dict[str, Any]:
    """Generate a machine-readable ranking board payload for one metric.

    The returned payload is already normalized into `ranking_board.v1` shape and
    can be stored directly via `astor_ranking_boards.upsert_ranking_board_draft`.
    """
    mk = _canonical_metric_key(metric_key)
    get_metric_config(mk)  # validate

    chosen_ranges: List[str] = []
    seen = set()
    for raw in (range_keys or RANKING_RANGE_KEYS):
        rk = _canonical_range_key(raw)
        if rk not in RANKING_RANGE_KEYS or rk in seen:
            continue
        seen.add(rk)
        chosen_ranges.append(rk)
    if not chosen_ranges:
        chosen_ranges = list(RANKING_RANGE_KEYS)

    ranges_payload: Dict[str, List[Dict[str, Any]]] = {}
    for rk in chosen_ranges:
        ranges_payload[rk] = await generate_metric_range_rows(
            mk,
            range_key=rk,
            limit=limit,
        )

    board = {
        "version": RANKING_BOARD_VERSION,
        "metric_key": mk,
        "timezone": RANKING_BOARD_TIMEZONE,
        "generated_at": _now_iso_z(),
        "ranges": ranges_payload,
        "meta": {
            "kernel": "rpc_kernel_v1",
            "rpc_limit": int(limit or DEFAULT_RANKING_LIMIT),
        },
    }
    return normalize_board_payload(mk, board)


async def generate_multiple_ranking_boards(
    metric_keys: Iterable[str],
    *,
    limit: Optional[int] = None,
    range_keys: Optional[Sequence[str]] = None,
) -> Dict[str, Dict[str, Any]]:
    """Generate boards for multiple metrics sequentially."""
    out: Dict[str, Dict[str, Any]] = {}
    seen = set()
    for raw_metric in metric_keys or []:
        mk = _canonical_metric_key(raw_metric)
        if not mk or mk in seen:
            continue
        seen.add(mk)
        out[mk] = await generate_ranking_board(
            mk,
            limit=limit,
            range_keys=range_keys,
        )
    return out


__all__ = [
    "DEFAULT_RANKING_LIMIT",
    "RANKING_RANGE_KEYS",
    "SUPPORTED_RANKING_METRICS",
    "generate_metric_range_rows",
    "generate_multiple_ranking_boards",
    "generate_ranking_board",
    "get_metric_config",
]
