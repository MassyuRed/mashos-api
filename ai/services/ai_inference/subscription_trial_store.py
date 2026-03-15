# -*- coding: utf-8 -*-
from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from supabase_client import (
    ensure_supabase_config as _ensure_supabase_config_shared,
    sb_get as _sb_get_shared,
    sb_patch as _sb_patch_shared,
    sb_post as _sb_post_shared,
    sb_service_role_headers as _sb_headers_shared,
)

logger = logging.getLogger("subscription_trial_store")

TRIAL_TABLE = "subscription_trial_state"


def _headers(*, prefer: Optional[str] = None) -> Dict[str, str]:
    h = {
        **_sb_headers_shared(),
        "Content-Type": "application/json",
    }
    if prefer:
        h["Prefer"] = prefer
    return h


def _normalize_platform(platform: Optional[str]) -> Optional[str]:
    p = str(platform or "").strip().lower()
    if p in {"ios", "android"}:
        return p
    return None


def _row_to_dict(data: Any) -> Dict[str, Any]:
    if isinstance(data, list):
        if not data:
            return {}
        row0 = data[0]
        return row0 if isinstance(row0, dict) else {}
    if isinstance(data, dict):
        return data
    return {}


async def _fetch_trial_row(user_id: str, trial_key: str) -> Optional[Dict[str, Any]]:
    _ensure_supabase_config_shared()

    resp = await _sb_get_shared(
        f"/rest/v1/{TRIAL_TABLE}",
        params={
            "select": "*",
            "user_id": f"eq.{user_id}",
            "trial_key": f"eq.{trial_key}",
            "limit": "1",
        },
        headers=_headers(),
        timeout=6.0,
    )

    if resp.status_code >= 300:
        raise RuntimeError(
            f"Failed to fetch trial state: status={resp.status_code} body={resp.text[:800]}"
        )

    try:
        data = resp.json()
    except Exception as exc:
        raise RuntimeError("Trial state response was not JSON") from exc

    row = _row_to_dict(data)
    return row or None


async def get_trial_state(user_id: str, trial_key: str) -> Dict[str, Any]:
    uid = str(user_id or "").strip()
    key = str(trial_key or "").strip()
    if not uid:
        raise ValueError("user_id is required")
    if not key:
        raise ValueError("trial_key is required")

    row = await _fetch_trial_row(uid, key)
    if row:
        return row

    return {
        "user_id": uid,
        "trial_key": key,
        "consumed": False,
        "consumed_at": None,
        "consumed_platform": None,
        "first_product_id": None,
        "first_store_ref": None,
        "source": None,
    }


async def is_trial_eligible(user_id: str, trial_key: str) -> bool:
    state = await get_trial_state(user_id, trial_key)
    return not bool(state.get("consumed"))


async def _insert_trial_row(payload: Dict[str, Any]) -> Dict[str, Any]:
    resp = await _sb_post_shared(
        f"/rest/v1/{TRIAL_TABLE}",
        params={"on_conflict": "user_id,trial_key"},
        json=payload,
        headers=_headers(prefer="resolution=merge-duplicates,return=representation"),
        timeout=6.0,
    )

    if resp.status_code >= 300:
        raise RuntimeError(
            f"Failed to insert trial state: status={resp.status_code} body={resp.text[:800]}"
        )

    try:
        return _row_to_dict(resp.json())
    except Exception:
        return {}


async def _patch_trial_row(user_id: str, trial_key: str, patch: Dict[str, Any]) -> Dict[str, Any]:
    resp = await _sb_patch_shared(
        f"/rest/v1/{TRIAL_TABLE}",
        params={
            "user_id": f"eq.{user_id}",
            "trial_key": f"eq.{trial_key}",
        },
        json=patch,
        headers=_headers(prefer="return=representation"),
        timeout=6.0,
    )

    if resp.status_code >= 300:
        raise RuntimeError(
            f"Failed to patch trial state: status={resp.status_code} body={resp.text[:800]}"
        )

    try:
        return _row_to_dict(resp.json())
    except Exception:
        return {}


async def mark_trial_consumed(
    user_id: str,
    trial_key: str,
    *,
    platform: Optional[str] = None,
    product_id: Optional[str] = None,
    store_ref: Optional[str] = None,
    source: str = "subscription_update",
) -> Dict[str, Any]:
    uid = str(user_id or "").strip()
    key = str(trial_key or "").strip()
    if not uid:
        raise ValueError("user_id is required")
    if not key:
        raise ValueError("trial_key is required")

    existing = await _fetch_trial_row(uid, key)
    if existing and bool(existing.get("consumed")):
        return existing

    now_iso = datetime.now(timezone.utc).isoformat()
    patch = {
        "consumed": True,
        "consumed_at": now_iso,
        "consumed_platform": _normalize_platform(platform),
        "first_product_id": str(product_id or "").strip() or None,
        "first_store_ref": str(store_ref or "").strip() or None,
        "source": str(source or "").strip() or "subscription_update",
    }

    if existing:
        updated = await _patch_trial_row(uid, key, patch)
        return updated or await get_trial_state(uid, key)

    created = await _insert_trial_row(
        {
            "user_id": uid,
            "trial_key": key,
            **patch,
        }
    )
    return created or await get_trial_state(uid, key)