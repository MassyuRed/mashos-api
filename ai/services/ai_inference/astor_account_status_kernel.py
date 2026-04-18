# -*- coding: utf-8 -*-
"""Account Status summary generation kernel for ASTOR (Phase 1).

Purpose
-------
既存の `account_status_summary_v2` RPC をそのまま活かしつつ、
ASTOR worker から machine-readable な per-user summary payload を生成する。

Phase 1 policy
--------------
- 計算 kernel は既存 SQL/RPC をそのまま利用する
- 本モジュールは「RPC 実行」と「summary payload 正規化」だけを担当する
- visibility 系 (`is_private_account` / `is_friend_code_public`) は保存しない
- DRAFT 保存・READY 昇格は `astor_account_status_store.py` 側で担当する

Design notes
------------
- Account Status は Ranking の sibling だが global board ではなく per-user summary
- source_hash は snapshot ではなく normalized payload 指紋から作る
- read API で current visibility を後付け join する前提
"""

from __future__ import annotations

import logging
import os
from typing import Any, Dict, Iterable, List, Mapping, Optional

from supabase_client import ensure_supabase_config, sb_post_rpc
from astor_account_status_store import (
    ACCOUNT_STATUS_TIMEZONE,
    ACCOUNT_STATUS_TOTAL_KEYS,
    ACCOUNT_STATUS_VERSION,
    normalize_account_status_payload,
)
from piece_generated_metrics import count_piece_generated_total_for_owner

logger = logging.getLogger("astor_account_status_kernel")


ACCOUNT_STATUS_RPC = (
    os.getenv("COCOLON_ACCOUNT_STATUS_RPC", "account_status_summary_v2")
    or "account_status_summary_v2"
).strip() or "account_status_summary_v2"

SUPPORTED_ACCOUNT_STATUS_TOTAL_KEYS = tuple(ACCOUNT_STATUS_TOTAL_KEYS or ())


def _canonical_target_user_id(value: Any) -> str:
    return str(value or "").strip()


def _to_int(value: Any, default: int = 0) -> int:
    if value is None or value == "" or isinstance(value, bool):
        return int(default)
    try:
        return int(value)
    except Exception:
        try:
            return int(float(str(value)))
        except Exception:
            return int(default)


def _extract_rpc_row(data: Any) -> Dict[str, Any]:
    if isinstance(data, list) and data:
        first = data[0]
        if isinstance(first, dict):
            return dict(first)
        return {}
    if isinstance(data, dict):
        return dict(data)
    return {}


async def _rpc_account_status_row(target_user_id: str) -> Dict[str, Any]:
    tgt = _canonical_target_user_id(target_user_id)
    if not tgt:
        raise ValueError("target_user_id is required")

    ensure_supabase_config()
    resp = await sb_post_rpc(
        ACCOUNT_STATUS_RPC,
        {"p_target_user_id": tgt},
        timeout=8.0,
    )
    if resp.status_code >= 300:
        body = (resp.text or "")[:1500]
        logger.error(
            "account status rpc failed: fn=%s target=%s status=%s body=%s",
            ACCOUNT_STATUS_RPC,
            tgt,
            resp.status_code,
            body,
        )
        raise RuntimeError(f"account status rpc failed: {ACCOUNT_STATUS_RPC} ({resp.status_code})")

    try:
        data = resp.json()
    except Exception as exc:
        logger.error(
            "account status rpc returned non-json: fn=%s target=%s err=%s",
            ACCOUNT_STATUS_RPC,
            tgt,
            exc,
        )
        raise RuntimeError(f"account status rpc returned invalid json: {ACCOUNT_STATUS_RPC}") from exc

    return _extract_rpc_row(data)


def _normalize_totals_from_rpc_row(row: Mapping[str, Any]) -> Dict[str, int]:
    src = row if isinstance(row, Mapping) else {}
    totals: Dict[str, int] = {}

    piece_total = max(0, _to_int(
        src.get("piece_generated_total")
        if src.get("piece_generated_total") is not None
        else src.get("mymodel_questions_total"),
        0,
    ))

    for key in SUPPORTED_ACCOUNT_STATUS_TOTAL_KEYS:
        if str(key) in {"piece_generated_total", "mymodel_questions_total"}:
            continue
        totals[str(key)] = max(0, _to_int(src.get(key), 0))

    totals["piece_generated_total"] = piece_total
    totals["mymodel_questions_total"] = piece_total
    return totals


def _build_summary_payload(target_user_id: str, row: Mapping[str, Any]) -> Dict[str, Any]:
    tgt = _canonical_target_user_id(target_user_id)
    if not tgt:
        raise ValueError("target_user_id is required")

    totals = _normalize_totals_from_rpc_row(row)
    raw_payload = {
        "version": ACCOUNT_STATUS_VERSION,
        "target_user_id": tgt,
        "timezone": ACCOUNT_STATUS_TIMEZONE,
        "totals": totals,
    }
    return normalize_account_status_payload(tgt, raw_payload)


async def generate_account_status_summary(target_user_id: str) -> Dict[str, Any]:
    """Generate a normalized account status summary payload for one user."""
    tgt = _canonical_target_user_id(target_user_id)
    if not tgt:
        raise ValueError("target_user_id is required")

    row = await _rpc_account_status_row(tgt)
    row = dict(row or {})
    try:
        piece_total = await count_piece_generated_total_for_owner(tgt)
        row["piece_generated_total"] = int(piece_total or 0)
        row["mymodel_questions_total"] = int(piece_total or 0)
    except Exception as exc:
        logger.warning("account status live piece count failed: target=%s err=%s", tgt, exc)
    payload = _build_summary_payload(tgt, row)
    return payload


async def generate_multiple_account_status_summaries(
    target_user_ids: Iterable[str],
) -> Dict[str, Dict[str, Any]]:
    """Generate normalized account status payloads for multiple users.

    This helper is optional for Phase 1 but useful for backfills / admin tasks.
    """
    out: Dict[str, Dict[str, Any]] = {}
    seen = set()
    for raw in target_user_ids or []:
        tgt = _canonical_target_user_id(raw)
        if not tgt or tgt in seen:
            continue
        seen.add(tgt)
        out[tgt] = await generate_account_status_summary(tgt)
    return out


__all__ = [
    "ACCOUNT_STATUS_RPC",
    "SUPPORTED_ACCOUNT_STATUS_TOTAL_KEYS",
    "generate_account_status_summary",
    "generate_multiple_account_status_summaries",
]
