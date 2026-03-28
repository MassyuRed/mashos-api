# -*- coding: utf-8 -*-
"""api_mymodel_qna.py

MyModel 一問一答（新構造）API
----------------------------

Spec: MyModel_QnA_NewArchitecture_Spec.txt (2026-02-05)

This module implements the *view* side of the new Q&A architecture:

- RN is display-only: it asks MashOS for a question list, shows it, then asks
  for a body, and sends lightweight events (view / resonance).
- Questions are *not* freely typed by end-users.

Implementation note (v1):
-------------------------
To keep this change set small and deterministic, v1 uses **MyModel Create**
questions + answers as the Q&A corpus.

- "title" := mymodel_create_questions.question_text
- "body"  := mymodel_create_answers.reflection_display_text (fallback: formatted answer_text)

Popularity (views/resonances) is aggregated by q_key.
Unread ("New") is tracked per viewer x q_instance_id.
"""

from __future__ import annotations

import logging
import os
import random
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional, Set, Tuple

import httpx
from fastapi import FastAPI, Header, HTTPException, Query
from pydantic import BaseModel, Field

from api_emotion_submit import (
    _ensure_supabase_config,
    _extract_bearer_token,
    _resolve_user_id_from_token,
)
from api_mymodel_create import _fetch_answers as _fetch_create_answers
from api_mymodel_create import _fetch_questions as _fetch_create_questions
from reflection_text_formatter import get_public_create_reflection_text
from subscription import SubscriptionTier
from subscription_store import get_subscription_tier_for_user
from publish_governance import history_retention_bounds_for_query, normalize_tier_str
from mymodel_entitlements import resolve_mymodel_entitlement
from astor_snapshot_enqueue import enqueue_global_snapshot_refresh
from astor_ranking_enqueue import enqueue_ranking_board_refresh
from astor_account_status_enqueue import enqueue_account_status_refresh
from astor_global_summary_enqueue import (
    enqueue_global_summary_refresh,
    enqueue_global_summary_refresh_many,
)

# Shared Supabase HTTP client (connection pooled)
from supabase_client import (
    sb_delete as _sb_delete_shared,
    sb_get as _sb_get_shared,
    sb_patch as _sb_patch_shared,
    sb_post as _sb_post_shared,
    sb_post_rpc as _sb_post_rpc_shared,
    sb_service_role_headers_json as _sb_headers_json_shared,
)


logger = logging.getLogger("mymodel.qna")

# Supabase (service role)
SUPABASE_URL = os.getenv("SUPABASE_URL", "").rstrip("/")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")

# Tables (overrideable)
METRICS_TABLE = os.getenv("COCOLON_MYMODEL_QNA_METRICS_TABLE", "mymodel_qna_metrics")
READS_TABLE = os.getenv("COCOLON_MYMODEL_QNA_READS_TABLE", "mymodel_qna_reads")
RESONANCES_TABLE = os.getenv(
    "COCOLON_MYMODEL_QNA_RESONANCES_TABLE", "mymodel_qna_resonances"
)


# Echoes / Discoveries tables (overrideable)
ECHOES_TABLE = os.getenv("COCOLON_MYMODEL_QNA_ECHOES_TABLE", "mymodel_qna_echoes")
DISCOVERY_LOGS_TABLE = os.getenv(
    "COCOLON_MYMODEL_QNA_DISCOVERY_LOGS_TABLE", "mymodel_qna_discovery_logs"
)

# History limits (legacy env kept for backward compatibility; detail endpoints now paginate by retention window)
FREE_HISTORY_LIMIT = int(os.getenv("COCOLON_MYMODEL_QNA_FREE_HISTORY_LIMIT", "5") or "5")


def _viewer_history_retention(viewer_tier: Any, *, now_utc: Optional[datetime] = None) -> Tuple[str, Dict[str, Any]]:
    tier_str = normalize_tier_str(getattr(viewer_tier, "value", viewer_tier))
    bounds = history_retention_bounds_for_query(tier_str, now_utc=now_utc)
    return tier_str, bounds


def _apply_created_at_retention_params(params: Dict[str, str], bounds: Dict[str, Any]) -> Dict[str, str]:
    out = dict(params or {})
    gte_iso = str(bounds.get("gte_iso") or "").strip()
    lt_iso = str(bounds.get("lt_iso") or "").strip()
    if gte_iso and lt_iso:
        out["and"] = f"(created_at.gte.{gte_iso},created_at.lt.{lt_iso})"
    elif gte_iso:
        out["created_at"] = f"gte.{gte_iso}"
    elif lt_iso:
        out["created_at"] = f"lt.{lt_iso}"
    return out

# Ranking logs tables (overrideable)
VIEW_LOGS_TABLE = os.getenv("COCOLON_MYMODEL_QNA_VIEW_LOGS_TABLE", "mymodel_qna_view_logs")
RESONANCE_LOGS_TABLE = os.getenv(
    "COCOLON_MYMODEL_QNA_RESONANCE_LOGS_TABLE", "mymodel_qna_resonance_logs"
)


VISIBILITY_TABLE = (os.getenv("COCOLON_VISIBILITY_SETTINGS_TABLE", "account_visibility_settings") or "account_visibility_settings").strip()

# RPC function names (overrideable)
QNA_LIST_RPC = (
    os.getenv("COCOLON_MYMODEL_QNA_LIST_RPC", "mymodel_qna_list_v1")
    or "mymodel_qna_list_v1"
).strip()
QNA_UNREAD_RPC = (
    os.getenv("COCOLON_MYMODEL_QNA_UNREAD_RPC", "mymodel_qna_unread_v1")
    or "mymodel_qna_unread_v1"
).strip()
QNA_LIST_RPC_LIMIT = int(os.getenv("COCOLON_MYMODEL_QNA_LIST_RPC_LIMIT", "2000") or "2000")


# ----------------------------
# Models
# ----------------------------


class QnaListItem(BaseModel):
    title: str
    q_key: str
    q_instance_id: str
    generated_at: Optional[str] = None
    views: int = 0
    resonances: int = 0
    discoveries: int = 0
    is_new: bool = False


class QnaListMeta(BaseModel):
    viewer_user_id: str
    target_user_id: str
    subscription_tier: str
    view_tier: str
    build_tier: str
    effective_tier: str
    total_items: int


class QnaListResponse(BaseModel):
    items: List[QnaListItem]
    meta: QnaListMeta


class QnaDetailResponse(BaseModel):
    title: str
    body: str
    q_key: str
    q_instance_id: str
    views: int = 0
    resonances: int = 0
    discoveries: int = 0
    is_new: bool = False
    is_resonated: bool = False


class QnaViewRequest(BaseModel):
    q_instance_id: str = Field(..., description="<target_user_id>:<question_id>")
    q_key: Optional[str] = Field(None, description="Optional; derived if omitted")


class QnaViewResponse(BaseModel):
    status: str = "ok"
    q_key: str
    q_instance_id: str
    views: int
    resonances: int
    is_new: bool = False


class QnaResonanceRequest(BaseModel):
    q_instance_id: str = Field(..., description="<target_user_id>:<question_id>")
    q_key: Optional[str] = Field(None, description="Optional; derived if omitted")


class QnaResonanceResponse(BaseModel):
    status: str
    q_key: str
    q_instance_id: str
    resonated: bool
    views: int
    resonances: int


# --- Echoes / Discoveries (Cocolon) ---

class QnaEchoesSubmitRequest(BaseModel):
    q_instance_id: str = Field(..., description="<target_user_id>:<question_id>")
    q_key: Optional[str] = Field(None, description="Optional; derived if omitted")
    strength: str = Field(..., description="small | medium | large")
    memo: Optional[str] = Field(None, description="Optional memo text")


class QnaEchoesSubmitResponse(BaseModel):
    status: str = Field("ok", description="ok")
    q_key: str
    q_instance_id: str
    strength: str
    memo: Optional[str] = None
    resonated: bool = True
    views: int = 0
    resonances: int = 0


class QnaEchoesDeleteRequest(BaseModel):
    q_instance_id: str = Field(..., description="<target_user_id>:<question_id>")
    q_key: Optional[str] = Field(None, description="Optional; derived if omitted")


class QnaEchoesDeleteResponse(BaseModel):
    status: str = Field("ok", description="ok")
    q_key: str
    q_instance_id: str
    resonated: bool = False
    views: int = 0
    resonances: int = 0


class QnaEchoesHistoryItem(BaseModel):
    strength: str
    created_at: str


class QnaEchoesHistoryResponse(BaseModel):
    status: str = Field("ok", description="ok")
    q_key: str
    q_instance_id: str
    subscription_tier: str
    total: int = 0
    count_small: int = 0
    count_medium: int = 0
    count_large: int = 0
    my_strength: Optional[str] = None
    my_memo: Optional[str] = None
    limit: int = 0
    offset: int = 0
    has_more: bool = False
    next_offset: Optional[int] = None
    retention_mode: Optional[str] = None
    is_limited: bool = False
    items: List[QnaEchoesHistoryItem] = Field(default_factory=list)


class QnaDiscoverySubmitRequest(BaseModel):
    q_instance_id: str = Field(..., description="<target_user_id>:<question_id>")
    q_key: Optional[str] = Field(None, description="Optional; derived if omitted")
    category: str = Field(
        ..., description="new_perspective | different_fun | well_worded | not_sorted | shocked"
    )
    memo: Optional[str] = Field(None, description="Optional memo text")


class QnaDiscoverySubmitResponse(BaseModel):
    status: str = Field("ok", description="ok")
    q_key: str
    q_instance_id: str
    id: Optional[str] = None


class QnaDiscoveryDeleteRequest(BaseModel):
    q_instance_id: str = Field(..., description="<target_user_id>:<question_id>")
    q_key: Optional[str] = Field(None, description="Optional; derived if omitted")


class QnaDiscoveryDeleteResponse(BaseModel):
    status: str = Field("ok", description="ok")
    q_key: str
    q_instance_id: str
    discoveries: int = 0


class QnaDiscoveryHistoryItem(BaseModel):
    id: str
    category: str
    memo: Optional[str] = None
    created_at: str


class QnaDiscoveryHistoryResponse(BaseModel):
    status: str = Field("ok", description="ok")
    q_key: str
    q_instance_id: str
    subscription_tier: str
    total: int = 0
    limit: int = 0
    offset: int = 0
    has_more: bool = False
    next_offset: Optional[int] = None
    retention_mode: Optional[str] = None
    is_limited: bool = False
    items: List[QnaDiscoveryHistoryItem] = Field(default_factory=list)


class QnaSavedReflectionItem(BaseModel):
    q_instance_id: str
    q_key: str
    title: str
    owner_user_id: str
    owner_display_name: Optional[str] = None
    saved_at: str


class QnaSavedReflectionsResponse(BaseModel):
    status: str = Field("ok", description="ok")
    order: str = Field("newest", description="newest | oldest")
    total_items: int = 0
    limit: int = 0
    offset: int = 0
    items: List[QnaSavedReflectionItem] = Field(default_factory=list)







class QnaUnreadResponse(BaseModel):
    status: str = Field("ok", description="ok")
    viewer_user_id: str
    target_user_id: str
    total_items: int = 0
    unread_count: int = 0
    has_unread: bool = False


class QnaUnreadStatusResponse(BaseModel):
    status: str = Field("ok", description="ok")
    viewer_user_id: str
    scope: str = Field("accessible", description="accessible")
    accessible_target_count: int = 0
    self_has_unread: bool = False
    following_has_unread: bool = False
    has_unread: bool = False


class QnaTrendingItem(BaseModel):
    question_id: int
    title: str
    q_key: str
    views: int = 0
    resonances: int = 0


class QnaTrendingResponse(BaseModel):
    status: str = Field("ok", description="ok")
    view_tier: str = Field(..., description="light | standard")
    total_items: int
    items: List[QnaTrendingItem]


class QnaHolderUser(BaseModel):
    id: str
    display_name: Optional[str] = None
    friend_code: Optional[str] = None
    myprofile_code: Optional[str] = None
    is_following: bool = False


class QnaHoldersResponse(BaseModel):
    status: str = Field("ok", description="ok")
    view_tier: str = Field(..., description="light | standard")
    question_id: int
    title: str
    q_key: str
    total_items: int
    users: List[QnaHolderUser]



class QnaRecommendUsersResponse(BaseModel):
    status: str = Field("ok", description="ok")
    days: int = Field(7, description="Activity window in days")
    total_items: int
    users: List[QnaHolderUser]

# ----------------------------
# Supabase helpers
# ----------------------------


def _sb_headers_json(*, prefer: Optional[str] = None) -> Dict[str, str]:
    return _sb_headers_json_shared(prefer=prefer)


async def _sb_get(path: str, *, params: Optional[Dict[str, str]] = None) -> httpx.Response:
    return await _sb_get_shared(path, params=params, timeout=8.0)


async def _sb_get_with_prefer(
    path: str, *, params: Optional[Dict[str, str]] = None, prefer: Optional[str] = None
) -> httpx.Response:
    """GET with optional Prefer header (e.g., count=exact)."""
    return await _sb_get_shared(path, params=params, prefer=prefer, timeout=8.0)


def _parse_content_range_total(content_range: Optional[str]) -> int:
    """Parse total count from PostgREST Content-Range header.

    Examples:
    - "0-0/12" -> 12
    - "*/12"   -> 12
    """
    if not content_range:
        return 0
    try:
        if "/" not in content_range:
            return 0
        total_part = content_range.split("/", 1)[1].strip()
        if not total_part or total_part == "*":
            return 0
        return int(total_part)
    except Exception:
        return 0


async def _sb_count_rows(path: str, *, params: Dict[str, str]) -> int:
    """Count rows via PostgREST (Prefer: count=exact).

    Note: Uses limit=0 to avoid transferring row payloads.
    """
    p: Dict[str, str] = {"select": "*", "limit": "0"}
    for k, v in (params or {}).items():
        if v is None:
            continue
        p[str(k)] = str(v)
    resp = await _sb_get_with_prefer(path, params=p, prefer="count=exact")
    if resp.status_code >= 300:
        logger.error("Supabase count failed: %s %s", resp.status_code, (resp.text or "")[:800])
        raise HTTPException(status_code=502, detail="Failed to count rows")
    cr = resp.headers.get("content-range") or resp.headers.get("Content-Range")
    return _parse_content_range_total(cr)



async def _sb_post(path: str, *, json: Any, prefer: Optional[str] = None) -> httpx.Response:
    return await _sb_post_shared(path, json=json, prefer=prefer, timeout=8.0)


async def _sb_post_rpc(fn: str, payload: Dict[str, Any]) -> httpx.Response:
    """POST to Supabase RPC endpoint (service_role)."""
    return await _sb_post_rpc_shared(fn, payload, timeout=8.0)



async def _sb_patch(
    path: str, *, params: Dict[str, str], json: Any, prefer: Optional[str] = None
) -> httpx.Response:
    return await _sb_patch_shared(path, params=params, json=json, prefer=prefer, timeout=8.0)


async def _sb_delete(
    path: str, *, params: Dict[str, str], prefer: Optional[str] = None
) -> httpx.Response:
    return await _sb_delete_shared(path, params=params, prefer=prefer, timeout=8.0)


# ----------------------------
# Internal helpers
# ----------------------------


async def _filter_recommendation_enabled(user_ids: List[str]) -> List[str]:
    """Filter out users who have is_recommendation_enabled = false.

    Missing settings rows are treated as enabled (public default).
    """
    ids = [str(x).strip() for x in (user_ids or []) if str(x).strip()]
    if not ids:
        return []

    # Default: enabled unless explicitly disabled.
    enabled_set = set(ids)

    # Chunk to avoid huge query strings.
    chunk_size = 200
    for i in range(0, len(ids), chunk_size):
        chunk = ids[i : i + chunk_size]
        in_list = ",".join(chunk)
        resp = await _sb_get(
            f"/rest/v1/{VISIBILITY_TABLE}",
            params={
                "select": "user_id,is_recommendation_enabled",
                "user_id": f"in.({in_list})",
            },
        )
        if resp.status_code >= 300:
            logger.warning(
                "Supabase visibility settings fetch failed (recommendation filter): %s %s",
                resp.status_code,
                (resp.text or "")[:500],
            )
            continue
        rows = resp.json()
        if not isinstance(rows, list):
            continue
        for r in rows:
            if not isinstance(r, dict):
                continue
            uid = str(r.get("user_id") or "").strip()
            if not uid:
                continue
            flag = r.get("is_recommendation_enabled")
            if flag is False:
                enabled_set.discard(uid)

    # Preserve original order.
    return [uid for uid in ids if uid in enabled_set]


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _build_tier_for_subscription(tier: SubscriptionTier) -> str:
    entitlement = resolve_mymodel_entitlement(tier)
    return str(entitlement.build_tier or "light")


def _view_tier_for_subscription(tier: SubscriptionTier) -> str:
    # Viewing (Reflections) is open for all tiers.
    # Subscription affects **creation/build** side only, not the viewer's readable range.
    # Therefore we always allow the viewer to see up to the target's build_tier.
    return "standard"


def _effective_tier(*, view_tier: str, build_tier: str) -> str:
    order = {"light": 0, "standard": 1}
    v = order.get(str(view_tier), 0)
    b = order.get(str(build_tier), 0)
    return "standard" if min(v, b) >= 1 else "light"


def _parse_instance_id(q_instance_id: str) -> Tuple[str, int]:
    """Parse '<target_user_id>:<question_id>'"""
    raw = str(q_instance_id or "").strip()
    if ":" not in raw:
        raise ValueError("invalid q_instance_id")
    target_user_id, qid_raw = raw.split(":", 1)
    target_user_id = target_user_id.strip()
    if not target_user_id:
        raise ValueError("invalid target_user_id")
    try:
        qid = int(str(qid_raw).strip())
    except Exception as exc:
        raise ValueError("invalid question_id") from exc
    return target_user_id, qid


def _is_secret_flag(value: Any) -> bool:
    """Return True if the value should be treated as secret.

    Accepts bool/int/str values defensively.
    """
    if value is True:
        return True
    if isinstance(value, int):
        return value == 1
    if isinstance(value, str):
        v = value.strip().lower()
        return v in ("true", "t", "1", "yes", "y")
    return False


def _public_create_body_from_answer_row(answer_row: Any) -> Optional[str]:
    if not isinstance(answer_row, dict):
        return None
    if _is_secret_flag(answer_row.get("is_secret")):
        return None
    body = get_public_create_reflection_text(answer_row)
    body_s = str(body or "").strip()
    return body_s or None


async def _fetch_secret_question_ids(*, target_user_id: str, question_ids: Set[int]) -> Set[int]:
    """Return question_ids that are marked as secret for the target user."""
    uid = str(target_user_id or "").strip()
    if not uid:
        return set()

    ids: Set[int] = set()
    for x in (question_ids or set()):
        try:
            ids.add(int(x))
        except Exception:
            continue
    if not ids:
        return set()

    answers = await _fetch_create_answers(user_id=uid, question_ids=ids)
    secret_ids: Set[int] = set()
    for qid in ids:
        a = answers.get(int(qid)) if isinstance(answers, dict) else None
        if isinstance(a, dict) and _is_secret_flag(a.get("is_secret")):
            secret_ids.add(int(qid))
    return secret_ids


def _q_key_for_question_id(question_id: int) -> str:
    return f"create:{int(question_id)}"


def _instance_id_for_target_question(target_user_id: str, question_id: int) -> str:
    return f"{str(target_user_id)}:{int(question_id)}"


def _quoted_in(values: Set[str]) -> str:
    """Build PostgREST `in.(...)` value with quotes.

    Example: in.("a","b")
    """

    vals = [str(v) for v in values if str(v).strip()]
    vals_sorted = sorted(vals)
    inner = ",".join([f'"{v}"' for v in vals_sorted])
    return f"in.({inner})"


async def _has_myprofile_link(*, viewer_user_id: str, owner_user_id: str) -> bool:
    """viewer -> owner のアクセス許可があるか（myprofile_links で判定）。"""
    resp = await _sb_get(
        "/rest/v1/myprofile_links",
        params={
            "select": "viewer_user_id",
            "viewer_user_id": f"eq.{viewer_user_id}",
            "owner_user_id": f"eq.{owner_user_id}",
            "limit": "1",
        },
    )
    if resp.status_code >= 300:
        logger.error(
            "Supabase myprofile_links select failed: %s %s",
            resp.status_code,
            resp.text[:1500],
        )
        raise HTTPException(status_code=502, detail="Failed to check myprofile link")
    rows = resp.json()
    return bool(isinstance(rows, list) and rows)

async def _fetch_profiles_by_ids(user_ids: List[str]) -> Dict[str, Dict[str, Any]]:
    """Bulk fetch profiles by ids (service_role)."""
    ids = [str(x).strip() for x in (user_ids or []) if str(x).strip()]
    if not ids:
        return {}
    out: Dict[str, Dict[str, Any]] = {}
    chunk_size = 200
    for i in range(0, len(ids), chunk_size):
        chunk = ids[i : i + chunk_size]
        resp = await _sb_get(
            "/rest/v1/profiles",
            params={
                "select": "id,display_name,friend_code,myprofile_code",
                "id": _quoted_in(set(chunk)),
                "limit": str(len(chunk)),
            },
        )
        if resp.status_code >= 300:
            logger.error("Supabase profiles select failed: %s %s", resp.status_code, resp.text[:1500])
            raise HTTPException(status_code=502, detail="Failed to load profiles")
        rows = resp.json()
        if isinstance(rows, list):
            for r in rows:
                if isinstance(r, dict) and r.get("id") is not None:
                    out[str(r.get("id"))] = r
    return out


async def _fetch_following_set(*, viewer_user_id: str, owner_ids: Set[str]) -> Set[str]:
    """Return subset of owner_ids that viewer is already following."""
    if not viewer_user_id or not owner_ids:
        return set()
    resp = await _sb_get(
        "/rest/v1/myprofile_links",
        params={
            "select": "owner_user_id",
            "viewer_user_id": f"eq.{viewer_user_id}",
            "owner_user_id": _quoted_in(set(owner_ids)),
            "limit": str(max(1, len(owner_ids))),
        },
    )
    if resp.status_code >= 300:
        logger.error("Supabase myprofile_links select failed: %s %s", resp.status_code, resp.text[:1500])
        # Fail-soft (treat as none followed)
        return set()
    rows = resp.json()
    out: Set[str] = set()
    if isinstance(rows, list):
        for r in rows:
            oid = str((r or {}).get("owner_user_id") or "").strip()
            if oid:
                out.add(oid)
    return out


async def _fetch_holder_user_ids_for_question(*, question_id: int, scan_limit: int) -> List[str]:
    """Return user_id list (deduped, ordered) who answered the question and remain publishable."""
    qid = int(question_id)
    resp = await _sb_get(
        "/rest/v1/mymodel_create_answers",
        params={
            "select": "*",
            "question_id": f"eq.{qid}",
            "answer_text": "not.is.null",
            "order": "updated_at.desc",
            "limit": str(int(scan_limit)),
        },
    )
    if resp.status_code >= 300:
        logger.error("Supabase mymodel_create_answers select failed: %s %s", resp.status_code, resp.text[:1500])
        raise HTTPException(status_code=502, detail="Failed to load answer holders")
    rows = resp.json()
    ids_raw: List[str] = []
    if isinstance(rows, list):
        for r in rows:
            if not isinstance(r, dict):
                continue
            if not _public_create_body_from_answer_row(r):
                continue
            uid = str((r or {}).get("user_id") or "").strip()
            if uid:
                ids_raw.append(uid)

    # dedupe preserving order
    seen: Set[str] = set()
    out: List[str] = []
    for uid in ids_raw:
        if uid in seen:
            continue
        seen.add(uid)
        out.append(uid)
    return out




async def _fetch_followed_owner_ids(*, viewer_user_id: str, limit: int = 5000) -> Set[str]:
    """Fetch all owner_user_id that viewer is following (best-effort).

    This avoids very long `in.(...)` filters when candidate lists are large.
    """
    if not viewer_user_id:
        return set()
    resp = await _sb_get(
        "/rest/v1/myprofile_links",
        params={
            "select": "owner_user_id",
            "viewer_user_id": f"eq.{viewer_user_id}",
            "limit": str(int(limit)),
        },
    )
    if resp.status_code >= 300:
        logger.error("Supabase myprofile_links select failed: %s %s", resp.status_code, resp.text[:1500])
        return set()
    rows = resp.json()
    out: Set[str] = set()
    if isinstance(rows, list):
        for r in rows:
            oid = str((r or {}).get("owner_user_id") or "").strip()
            if oid:
                out.add(oid)
    return out


async def _fetch_active_user_ids(*, since_iso: str, scan_limit: int) -> Set[str]:
    """Fetch active user ids within window, based on:
    - emotions.created_at >= since
    - OR mymodel_create_answers.updated_at >= since

    Fail-soft: if a source fails, it is skipped.
    """
    out: Set[str] = set()
    # 1) emotions
    try:
        resp1 = await _sb_get(
            "/rest/v1/emotions",
            params={
                "select": "user_id,created_at",
                "created_at": f"gte.{since_iso}",
                "order": "created_at.desc",
                "limit": str(int(scan_limit)),
            },
        )
        if resp1.status_code < 300:
            rows1 = resp1.json()
            if isinstance(rows1, list):
                for r in rows1:
                    uid = str((r or {}).get("user_id") or "").strip()
                    if uid:
                        out.add(uid)
        else:
            logger.error("Supabase emotions select failed: %s %s", resp1.status_code, resp1.text[:800])
    except Exception as exc:
        logger.warning("active users: emotions fetch failed: %s", exc)

    # 2) mymodel_create_answers
    try:
        resp2 = await _sb_get(
            "/rest/v1/mymodel_create_answers",
            params={
                "select": "user_id,updated_at",
                "updated_at": f"gte.{since_iso}",
                "order": "updated_at.desc",
                "limit": str(int(scan_limit)),
            },
        )
        if resp2.status_code < 300:
            rows2 = resp2.json()
            if isinstance(rows2, list):
                for r in rows2:
                    uid = str((r or {}).get("user_id") or "").strip()
                    if uid:
                        out.add(uid)
        else:
            logger.error("Supabase mymodel_create_answers select failed: %s %s", resp2.status_code, resp2.text[:800])
    except Exception as exc:
        logger.warning("active users: mymodel_create_answers fetch failed: %s", exc)

    return out

async def _fetch_metrics(q_keys: Set[str]) -> Dict[str, Dict[str, Any]]:
    """Fetch *global* popularity metrics aggregated by q_key.

    Note:
    - Global metrics rows are stored with q_instance_id IS NULL.
    - Per-answer (per target user) metrics are stored with q_instance_id set.
    """
    if not q_keys:
        return {}
    resp = await _sb_get(
        f"/rest/v1/{METRICS_TABLE}",
        params={
            "select": "q_key,views,resonances",
            "q_key": _quoted_in(set(q_keys)),
            "q_instance_id": "is.null",
            "limit": str(max(1, len(q_keys))),
        },
    )
    if resp.status_code >= 300:
        logger.error("Supabase %s select failed: %s %s", METRICS_TABLE, resp.status_code, resp.text[:1500])
        # Fail-soft: no metrics
        return {}
    rows = resp.json()
    out: Dict[str, Dict[str, Any]] = {}
    if isinstance(rows, list):
        for r in rows:
            k = str(r.get("q_key") or "").strip()
            if not k:
                continue
            out[k] = r
    return out


async def _fetch_instance_metrics(q_instance_ids: Set[str]) -> Dict[str, Dict[str, Any]]:
    """Fetch per-answer metrics aggregated by q_instance_id."""
    if not q_instance_ids:
        return {}
    resp = await _sb_get(
        f"/rest/v1/{METRICS_TABLE}",
        params={
            "select": "q_instance_id,q_key,views,resonances",
            "q_instance_id": _quoted_in(set(q_instance_ids)),
            "limit": str(max(1, len(q_instance_ids))),
        },
    )
    if resp.status_code >= 300:
        logger.error("Supabase %s select failed: %s %s", METRICS_TABLE, resp.status_code, resp.text[:1500])
        # Fail-soft: no metrics
        return {}
    rows = resp.json()
    out: Dict[str, Dict[str, Any]] = {}
    if isinstance(rows, list):
        for r in rows:
            iid = str(r.get("q_instance_id") or "").strip()
            if not iid:
                continue
            out[iid] = r
    return out



async def _fetch_discovery_counts_for_instances(q_instance_ids: Set[str]) -> Dict[str, int]:
    """Fetch discovery (気づき) counts aggregated by q_instance_id.

    Implementation notes:
    - Discoveries are stored as rows in DISCOVERY_LOGS_TABLE.
    - PostgREST has no guaranteed group-by in all setups, so we fetch q_instance_id rows and count in Python.
    - Chunking is used to keep query strings reasonable.

    Fail-soft: returns empty dict on errors.
    """
    ids = [str(x).strip() for x in (q_instance_ids or set()) if str(x).strip()]
    if not ids:
        return {}

    out: Dict[str, int] = {}

    # Keep the IN(...) filter size modest
    chunk_size = 120
    # Safety cap to avoid transferring too many rows at once (rare in practice)
    max_rows = 50000

    for i in range(0, len(ids), chunk_size):
        chunk = set(ids[i : i + chunk_size])
        try:
            resp = await _sb_get(
                f"/rest/v1/{DISCOVERY_LOGS_TABLE}",
                params={
                    "select": "q_instance_id",
                    "q_instance_id": _quoted_in(chunk),
                    "limit": str(max_rows),
                },
            )
            if resp.status_code >= 300:
                logger.warning(
                    "Supabase %s select failed (discoveries): %s %s",
                    DISCOVERY_LOGS_TABLE,
                    resp.status_code,
                    (resp.text or "")[:800],
                )
                continue

            rows = resp.json()
            if not isinstance(rows, list):
                continue

            for r in rows:
                iid = str((r or {}).get("q_instance_id") or "").strip()
                if not iid:
                    continue
                out[iid] = int(out.get(iid) or 0) + 1
        except Exception as exc:
            logger.warning("discoveries count fetch failed: %s", exc)

    return out
async def _fetch_reads(viewer_user_id: str, q_instance_ids: Set[str]) -> Set[str]:
    if not viewer_user_id or not q_instance_ids:
        return set()
    resp = await _sb_get(
        f"/rest/v1/{READS_TABLE}",
        params={
            "select": "q_instance_id",
            "viewer_user_id": f"eq.{viewer_user_id}",
            "q_instance_id": _quoted_in(set(q_instance_ids)),
            "limit": str(max(1, len(q_instance_ids))),
        },
    )
    if resp.status_code >= 300:
        logger.error("Supabase %s select failed: %s %s", READS_TABLE, resp.status_code, resp.text[:1500])
        return set()
    rows = resp.json()
    out: Set[str] = set()
    if isinstance(rows, list):
        for r in rows:
            qid = str(r.get("q_instance_id") or "").strip()
            if qid:
                out.add(qid)
    return out


async def _is_resonated(viewer_user_id: str, q_instance_id: str) -> bool:
    if not viewer_user_id or not q_instance_id:
        return False
    resp = await _sb_get(
        f"/rest/v1/{RESONANCES_TABLE}",
        params={
            "select": "viewer_user_id",
            "viewer_user_id": f"eq.{viewer_user_id}",
            "q_instance_id": f"eq.{q_instance_id}",
            "limit": "1",
        },
    )
    if resp.status_code >= 300:
        logger.error("Supabase %s select failed: %s %s", RESONANCES_TABLE, resp.status_code, resp.text[:800])
        return False
    rows = resp.json()
    return bool(isinstance(rows, list) and rows)


async def _upsert_read(viewer_user_id: str, q_instance_id: str) -> None:
    if not viewer_user_id or not q_instance_id:
        return
    payload = {
        "viewer_user_id": str(viewer_user_id),
        "q_instance_id": str(q_instance_id),
        "viewed_at": _now_iso(),
    }
    resp = await _sb_post(
        f"/rest/v1/{READS_TABLE}",
        json=payload,
        prefer="resolution=merge-duplicates,return=minimal",
    )
    if resp.status_code >= 300:
        # Fail-soft
        logger.warning("Supabase %s upsert failed: %s %s", READS_TABLE, resp.status_code, resp.text[:800])


async def _insert_view_log(
    *, target_user_id: str, viewer_user_id: str, question_id: int, q_key: str, q_instance_id: str
) -> None:
    """Insert ranking view log (best-effort).

    Notes:
    - This is for *user rankings* (views = other people opened the Q&A).
    - Duplicates are allowed (every open is counted).
    - Self-view is ignored.
    """
    if not target_user_id or not viewer_user_id or not q_instance_id:
        return
    if str(target_user_id) == str(viewer_user_id):
        return

    payload = {
        "target_user_id": str(target_user_id),
        "viewer_user_id": str(viewer_user_id),
        "question_id": int(question_id),
        "q_key": str(q_key or "").strip(),
        "q_instance_id": str(q_instance_id),
        "created_at": _now_iso(),
    }

    try:
        resp = await _sb_post(
            f"/rest/v1/{VIEW_LOGS_TABLE}",
            json=payload,
            prefer="return=minimal",
        )
        if resp.status_code >= 300:
            logger.warning(
                "Supabase %s insert failed: %s %s",
                VIEW_LOGS_TABLE,
                resp.status_code,
                resp.text[:800],
            )
    except Exception as exc:
        logger.warning("Supabase %s insert failed: %s", VIEW_LOGS_TABLE, exc)


async def _insert_resonance_log(
    *, target_user_id: str, viewer_user_id: str, question_id: int, q_key: str, q_instance_id: str
) -> None:
    """Insert ranking resonance log (best-effort).

    Notes:
    - This is for *user rankings* (resonances = other people resonated).
    - Self-resonance is ignored.
    - Duplicates are ignored (viewer x q_instance_id is unique).
    """
    if not target_user_id or not viewer_user_id or not q_instance_id:
        return
    if str(target_user_id) == str(viewer_user_id):
        return

    payload = {
        "target_user_id": str(target_user_id),
        "viewer_user_id": str(viewer_user_id),
        "question_id": int(question_id),
        "q_key": str(q_key or "").strip(),
        "q_instance_id": str(q_instance_id),
        "created_at": _now_iso(),
    }

    try:
        resp = await _sb_post(
            f"/rest/v1/{RESONANCE_LOGS_TABLE}",
            json=payload,
            prefer="resolution=ignore-duplicates,return=minimal",
        )
        if resp.status_code >= 300:
            logger.warning(
                "Supabase %s insert failed: %s %s",
                RESONANCE_LOGS_TABLE,
                resp.status_code,
                resp.text[:800],
            )
    except Exception as exc:
        logger.warning("Supabase %s insert failed: %s", RESONANCE_LOGS_TABLE, exc)


async def _inc_metric(
    *, q_key: str, q_instance_id: Optional[str] = None, field: str, delta: int = 1
) -> Dict[str, int]:
    """Increment views/resonances for both:
    - per-answer row (q_instance_id = '<target_user_id>:<question_id>')
    - global popularity row (q_instance_id IS NULL)

    This is best-effort and not strictly atomic.

    Return:
    - views/resonances: per-answer counts if q_instance_id is provided, otherwise global counts
    - global_views/global_resonances: attached when q_instance_id is provided
    """

    kk = str(q_key or "").strip()
    iid = str(q_instance_id or "").strip() or None
    if not kk:
        return {"views": 0, "resonances": 0}
    if field not in ("views", "resonances"):
        raise ValueError("invalid metric field")

    async def _inc_one(*, iid_filter: Optional[str]) -> Dict[str, int]:
        # 1) Fetch current
        cur_views = 0
        cur_res = 0
        exists = False

        params_get = {
            "select": "q_key,q_instance_id,views,resonances",
            "q_key": f"eq.{kk}",
            "limit": "1",
        }
        if iid_filter is None:
            params_get["q_instance_id"] = "is.null"
        else:
            params_get["q_instance_id"] = f"eq.{iid_filter}"

        try:
            resp = await _sb_get(f"/rest/v1/{METRICS_TABLE}", params=params_get)
            if resp.status_code < 300:
                rows = resp.json()
                if isinstance(rows, list) and rows:
                    exists = True
                    try:
                        cur_views = int(rows[0].get("views") or 0)
                    except Exception:
                        cur_views = 0
                    try:
                        cur_res = int(rows[0].get("resonances") or 0)
                    except Exception:
                        cur_res = 0
        except Exception as exc:
            logger.warning("Supabase %s select failed (metrics inc): %s", METRICS_TABLE, exc)
            exists = False
            cur_views = 0
            cur_res = 0

        # 2) Increment in memory
        if field == "views":
            cur_views += int(delta)
        else:
            cur_res += int(delta)

        # Clamp (allow decrement for toggle; never go below 0)
        if cur_views < 0:
            cur_views = 0
        if cur_res < 0:
            cur_res = 0

        # 3) Upsert
        params_patch = {"q_key": f"eq.{kk}"}
        if iid_filter is None:
            params_patch["q_instance_id"] = "is.null"
        else:
            params_patch["q_instance_id"] = f"eq.{iid_filter}"

        if exists:
            try:
                resp2 = await _sb_patch(
                    f"/rest/v1/{METRICS_TABLE}",
                    params=params_patch,
                    json={
                        "views": cur_views,
                        "resonances": cur_res,
                        "updated_at": _now_iso(),
                    },
                    prefer="return=minimal",
                )
                if resp2.status_code >= 300:
                    logger.warning(
                        "Supabase %s patch failed: %s %s",
                        METRICS_TABLE,
                        resp2.status_code,
                        resp2.text[:800],
                    )
            except Exception as exc:
                logger.warning("Supabase %s patch failed (metrics inc): %s", METRICS_TABLE, exc)
        else:
            payload = {
                "q_key": kk,
                "q_instance_id": iid_filter,
                "views": cur_views,
                "resonances": cur_res,
                "updated_at": _now_iso(),
            }
            try:
                resp3 = await _sb_post(
                    f"/rest/v1/{METRICS_TABLE}",
                    json=payload,
                    prefer="return=minimal",
                )
                if resp3.status_code >= 300:
                    logger.warning(
                        "Supabase %s insert failed: %s %s",
                        METRICS_TABLE,
                        resp3.status_code,
                        resp3.text[:800],
                    )
            except Exception as exc:
                logger.warning("Supabase %s insert failed (metrics inc): %s", METRICS_TABLE, exc)

        return {"views": cur_views, "resonances": cur_res}

    # Per-answer (if provided)
    instance_counts: Optional[Dict[str, int]] = None
    if iid is not None:
        instance_counts = await _inc_one(iid_filter=iid)

    # Global popularity (always maintained)
    global_counts = await _inc_one(iid_filter=None)

    if instance_counts is None:
        return {"views": int(global_counts.get("views") or 0), "resonances": int(global_counts.get("resonances") or 0)}

    return {
        "views": int(instance_counts.get("views") or 0),
        "resonances": int(instance_counts.get("resonances") or 0),
        "global_views": int(global_counts.get("views") or 0),
        "global_resonances": int(global_counts.get("resonances") or 0),
    }

async def _resolve_tiers(*, viewer_user_id: str, target_user_id: str) -> Tuple[str, str, str, str]:
    """Return (subscription_tier, view_tier, build_tier, effective_tier)."""

    viewer_tier = SubscriptionTier.FREE
    target_tier = SubscriptionTier.FREE
    try:
        viewer_tier = await get_subscription_tier_for_user(viewer_user_id, default=SubscriptionTier.FREE)
    except Exception as exc:
        logger.warning("viewer subscription tier resolve failed: %s", exc)
        viewer_tier = SubscriptionTier.FREE
    try:
        target_tier = await get_subscription_tier_for_user(target_user_id, default=SubscriptionTier.FREE)
    except Exception as exc:
        logger.warning("target subscription tier resolve failed: %s", exc)
        target_tier = SubscriptionTier.FREE

    view_tier = _view_tier_for_subscription(viewer_tier)
    build_tier = _build_tier_for_subscription(target_tier)
    eff = _effective_tier(view_tier=view_tier, build_tier=build_tier)
    return (viewer_tier.value, view_tier, build_tier, eff)


def _owner_reflection_policy_from_tier(tier: SubscriptionTier) -> Dict[str, Any]:
    entitlement = resolve_mymodel_entitlement(tier)
    return {
        "subscription_tier": str(tier.value),
        "build_tier": str(entitlement.build_tier or "light"),
        "template_question_limit": int(entitlement.template_question_limit),
        "can_expose_generated_reflections": bool(entitlement.can_expose_generated_reflections),
        "can_expose_original_reflections": bool(entitlement.can_expose_original_reflections),
    }


async def _resolve_owner_reflection_policy(owner_user_id: str) -> Dict[str, Any]:
    oid = str(owner_user_id or "").strip()
    tier = SubscriptionTier.FREE
    if oid:
        try:
            tier = await get_subscription_tier_for_user(oid, default=SubscriptionTier.FREE)
        except Exception as exc:
            logger.warning("owner subscription tier resolve failed: %s", exc)
            tier = SubscriptionTier.FREE
    return _owner_reflection_policy_from_tier(tier)


async def _resolve_owner_reflection_policies(owner_user_ids: Set[str]) -> Dict[str, Dict[str, Any]]:
    out: Dict[str, Dict[str, Any]] = {}
    for owner_user_id in owner_user_ids or set():
        oid = str(owner_user_id or "").strip()
        if not oid or oid in out:
            continue
        out[oid] = await _resolve_owner_reflection_policy(oid)
    return out


async def _fetch_question_maps_for_build_tiers(build_tiers: Set[str]) -> Dict[str, Dict[int, str]]:
    order = {"light": 0, "standard": 1}
    out: Dict[str, Dict[int, str]] = {}
    for build_tier in sorted({str(t or "light").strip() or "light" for t in (build_tiers or set())}, key=lambda x: order.get(x, 99)):
        qrows = await _fetch_create_questions(build_tier=build_tier)
        qmap: Dict[int, str] = {}
        for r in qrows or []:
            try:
                qid = int((r or {}).get("id"))
            except Exception:
                continue
            txt = str((r or {}).get("question_text") or "").strip()
            if txt:
                qmap[int(qid)] = txt
        out[build_tier] = qmap
    return out


# ----------------------------
# Routes
# ----------------------------


def register_mymodel_qna_routes(app: FastAPI) -> None:
    """Register Q&A (new architecture) routes."""

    @app.get("/mymodel/qna/list", response_model=QnaListResponse)
    async def qna_list(
        target_user_id: Optional[str] = Query(default=None, description="Owner of the MyModel (defaults to viewer)"),
        sort: str = Query(default="newest", description="newest | popular"),
        metric: str = Query(default="views", description="views | resonances | discoveries (only for popular)"),
        authorization: Optional[str] = Header(default=None, alias="Authorization"),
    ) -> QnaListResponse:
        token = _extract_bearer_token(authorization) if authorization else None
        if not token:
            raise HTTPException(status_code=401, detail="Authorization header with Bearer token is required")

        viewer_user_id = await _resolve_user_id_from_token(token)
        if not viewer_user_id:
            raise HTTPException(status_code=401, detail="Invalid token")

        tgt = str(target_user_id or viewer_user_id).strip()
        if not tgt:
            raise HTTPException(status_code=400, detail="target_user_id is required")

        # External access control (same as /mymodel/infer)
        if tgt != viewer_user_id:
            allowed = await _has_myprofile_link(viewer_user_id=viewer_user_id, owner_user_id=tgt)
            if not allowed:
                raise HTTPException(status_code=403, detail="You are not allowed to query this MyProfile")

        subscription_tier, view_tier, build_tier, effective_tier = await _resolve_tiers(
            viewer_user_id=viewer_user_id, target_user_id=tgt
        )

        # Fetch answered reflections with JOINed metrics / discoveries / reads in a single RPC call.
        try:
            resp = await _sb_post_rpc(
                QNA_LIST_RPC,
                {
                    "p_viewer_user_id": str(viewer_user_id),
                    "p_target_user_id": str(tgt),
                    "p_effective_tier": str(effective_tier or "").strip() or None,
                    "p_limit": int(QNA_LIST_RPC_LIMIT),
                },
            )
        except Exception as exc:
            logger.error("Supabase rpc %s failed (network): %s", QNA_LIST_RPC, exc)
            raise HTTPException(status_code=502, detail="Failed to load reflections")

        if resp.status_code >= 300:
            logger.error(
                "Supabase rpc %s failed: %s %s",
                QNA_LIST_RPC,
                resp.status_code,
                (resp.text or "")[:1500],
            )
            raise HTTPException(status_code=502, detail="Failed to load reflections")

        rows: Any = []
        try:
            rows = resp.json()
        except Exception:
            rows = []

        items: List[QnaListItem] = []

        if isinstance(rows, list):
            for r in rows:
                if not isinstance(r, dict):
                    continue

                title = str(r.get("title") or "").strip()
                q_key = str(r.get("q_key") or "").strip()
                q_instance_id = str(r.get("q_instance_id") or "").strip()
                if not title or not q_key or not q_instance_id:
                    continue

                gen_raw = r.get("generated_at")
                generated_at = None if gen_raw is None else (str(gen_raw).strip() or None)

                try:
                    views = int(r.get("views") or 0)
                except Exception:
                    views = 0
                try:
                    resonances = int(r.get("resonances") or 0)
                except Exception:
                    resonances = 0
                try:
                    discoveries = int(r.get("discoveries") or 0)
                except Exception:
                    discoveries = 0

                is_new = True if r.get("is_new") is True else False

                items.append(
                    QnaListItem(
                        title=title,
                        q_key=q_key,
                        q_instance_id=q_instance_id,
                        generated_at=generated_at,
                        views=views,
                        resonances=resonances,
                        discoveries=discoveries,
                        is_new=is_new,
                    )
                )

        # Sort (same behavior as v1)
        sort_key = str(sort or "newest").strip().lower()
        metric_key = str(metric or "views").strip().lower()

        if sort_key == "popular":
            if metric_key not in ("views", "resonances", "discoveries"):
                metric_key = "views"

            if metric_key == "discoveries":
                items.sort(
                    key=lambda x: (x.discoveries, x.resonances, x.views, x.generated_at or ""),
                    reverse=True,
                )
            elif metric_key == "resonances":
                items.sort(key=lambda x: (x.resonances, x.views, x.generated_at or ""), reverse=True)
            else:
                items.sort(key=lambda x: (x.views, x.resonances, x.generated_at or ""), reverse=True)
        else:
            items.sort(key=lambda x: (x.generated_at or ""), reverse=True)

        # MyModel Create "secret" answers are never visible (to self or others).
        if items:
            try:
                qids: Set[int] = set()
                qid_by_instance: Dict[str, int] = {}
                for it in items:
                    try:
                        _, qid_val = _parse_instance_id(it.q_instance_id)
                        qids.add(int(qid_val))
                        qid_by_instance[str(it.q_instance_id)] = int(qid_val)
                    except Exception:
                        continue

                secret_qids = (
                    await _fetch_secret_question_ids(target_user_id=str(tgt), question_ids=qids)
                    if qids
                    else set()
                )
                if secret_qids:
                    items = [
                        it
                        for it in items
                        if qid_by_instance.get(str(it.q_instance_id)) not in secret_qids
                    ]
            except HTTPException:
                raise
            except Exception as exc:
                logger.error("secret filter failed (list): %s", exc)
                raise HTTPException(status_code=502, detail="Failed to load reflections")

        meta = QnaListMeta(
            viewer_user_id=str(viewer_user_id),
            target_user_id=tgt,
            subscription_tier=subscription_tier,
            view_tier=view_tier,
            build_tier=build_tier,
            effective_tier=effective_tier,
            total_items=len(items),
        )
        return QnaListResponse(items=items, meta=meta)

    @app.get("/mymodel/qna/unread", response_model=QnaUnreadResponse)
    async def qna_unread(
        target_user_id: Optional[str] = Query(
            default=None,
            description="Owner of the MyModel (defaults to viewer)",
        ),
        authorization: Optional[str] = Header(default=None, alias="Authorization"),
    ) -> QnaUnreadResponse:
        """Lightweight unread badge endpoint (for bottom tab prefetch)."""

        token = _extract_bearer_token(authorization) if authorization else None
        if not token:
            raise HTTPException(
                status_code=401,
                detail="Authorization header with Bearer token is required",
            )

        viewer_user_id = await _resolve_user_id_from_token(token)
        if not viewer_user_id:
            raise HTTPException(status_code=401, detail="Invalid token")

        tgt = str(target_user_id or viewer_user_id).strip()
        if not tgt:
            raise HTTPException(status_code=400, detail="target_user_id is required")

        # External access control (same as /mymodel/qna/list)
        if tgt != viewer_user_id:
            allowed = await _has_myprofile_link(
                viewer_user_id=viewer_user_id, owner_user_id=tgt
            )
            if not allowed:
                raise HTTPException(
                    status_code=403, detail="You are not allowed to query this MyProfile"
                )

        try:
            _, _, _, effective_tier = await _resolve_tiers(
                viewer_user_id=viewer_user_id, target_user_id=tgt
            )

            # Single RPC for unread counts (answered reflections only).
            resp = await _sb_post_rpc(
                QNA_UNREAD_RPC,
                {
                    "p_viewer_user_id": str(viewer_user_id),
                    "p_target_user_id": str(tgt),
                    "p_effective_tier": str(effective_tier or "").strip() or None,
                },
            )

            if resp.status_code >= 300:
                logger.warning(
                    "Supabase rpc %s failed (unread): %s %s",
                    QNA_UNREAD_RPC,
                    resp.status_code,
                    (resp.text or "")[:800],
                )
                return QnaUnreadResponse(
                    status="ok",
                    viewer_user_id=str(viewer_user_id),
                    target_user_id=tgt,
                    total_items=0,
                    unread_count=0,
                    has_unread=False,
                )

            data: Any = None
            try:
                data = resp.json()
            except Exception:
                data = None

            row: Dict[str, Any] = {}
            if isinstance(data, list) and data and isinstance(data[0], dict):
                row = data[0]
            elif isinstance(data, dict):
                row = data

            try:
                total_items = int(row.get("total_items") or 0)
            except Exception:
                total_items = 0
            try:
                unread_count = int(row.get("unread_count") or 0)
            except Exception:
                unread_count = 0

            return QnaUnreadResponse(
                status="ok",
                viewer_user_id=str(viewer_user_id),
                target_user_id=tgt,
                total_items=int(total_items or 0),
                unread_count=int(unread_count or 0),
                has_unread=int(unread_count or 0) > 0,
            )
        except HTTPException:
            raise
        except Exception as exc:
            logger.warning("qna_unread failed: %s", exc)
            # Fail-soft: badge endpoint should never crash the app
            return QnaUnreadResponse(
                status="ok",
                viewer_user_id=str(viewer_user_id),
                target_user_id=tgt,
                total_items=0,
                unread_count=0,
                has_unread=False,
            )

    @app.get("/mymodel/qna/trending", response_model=QnaTrendingResponse)
    async def qna_trending(
        limit: int = Query(default=5, ge=1, le=20, description="Number of trending questions to return"),
        mode: str = Query(default="overall", description="overall | resonance | views"),
        authorization: Optional[str] = Header(default=None, alias="Authorization"),
    ) -> QnaTrendingResponse:
        """Return trending questions (global popularity by q_key).

        Notes:
        - Uses global metrics rows where q_instance_id IS NULL.
        - Filters to recent activity window (updated_at) to keep results fresh.
        - Returned questions are filtered by viewer's view_tier (light|standard).
        """

        token = _extract_bearer_token(authorization) if authorization else None
        if not token:
            raise HTTPException(status_code=401, detail="Authorization header with Bearer token is required")

        viewer_user_id = await _resolve_user_id_from_token(token)
        if not viewer_user_id:
            raise HTTPException(status_code=401, detail="Invalid token")

        # Viewer tier -> view_tier (light|standard) to avoid showing inaccessible questions.
        viewer_tier = SubscriptionTier.FREE
        try:
            viewer_tier = await get_subscription_tier_for_user(viewer_user_id, default=SubscriptionTier.FREE)
        except Exception:
            viewer_tier = SubscriptionTier.FREE

        view_tier = _view_tier_for_subscription(viewer_tier)

        mode_key = str(mode or "overall").strip().lower()
        if mode_key not in ("overall", "resonance", "views"):
            mode_key = "overall"

        # Fixed window for now (Mash decision): "今週の空気感"
        window_days = 7
        since_iso = (datetime.now(timezone.utc) - timedelta(days=int(window_days))).isoformat()

        # Load questions allowed for this view_tier.
        try:
            qrows = await _fetch_create_questions(build_tier=view_tier)
        except Exception as exc:
            logger.error("failed to fetch create questions (trending): %s", exc)
            raise HTTPException(status_code=502, detail="Failed to load questions")

        qmap_by_key: Dict[str, Tuple[int, str]] = {}
        for r in qrows or []:
            try:
                qid = int(r.get("id"))
            except Exception:
                continue
            txt = str(r.get("question_text") or "").strip()
            if not txt:
                continue
            qk = _q_key_for_question_id(qid)
            qmap_by_key[qk] = (qid, txt)

        if not qmap_by_key:
            return QnaTrendingResponse(status="ok", view_tier=view_tier, total_items=0, items=[])

        order = "resonances.desc,views.desc"
        if mode_key == "views":
            order = "views.desc,resonances.desc"

        # Fetch top global metrics and then filter to allowed q_keys.
        scan_limit = int(max(50, min(500, int(limit) * 25)))
        resp = await _sb_get(
            f"/rest/v1/{METRICS_TABLE}",
            params={
                "select": "q_key,views,resonances",
                "q_instance_id": "is.null",
                "updated_at": f"gte.{since_iso}",
                "order": order,
                "limit": str(scan_limit),
            },
        )

        if resp.status_code >= 300:
            logger.error(
                "Supabase %s trending select failed: %s %s",
                METRICS_TABLE,
                resp.status_code,
                resp.text[:1500],
            )
            # Fail-soft
            return QnaTrendingResponse(status="ok", view_tier=view_tier, total_items=0, items=[])

        rows = resp.json()

        # Collect candidates (bounded by scan_limit)
        candidates: List[Tuple[int, str, str, int, int]] = []
        # tuple: (question_id, title, q_key, views, resonances)

        if isinstance(rows, list):
            for r in rows:
                qk = str((r or {}).get("q_key") or "").strip()
                if not qk or qk not in qmap_by_key:
                    continue

                qid, title = qmap_by_key[qk]

                try:
                    views = int((r or {}).get("views") or 0)
                except Exception:
                    views = 0
                try:
                    res_cnt = int((r or {}).get("resonances") or 0)
                except Exception:
                    res_cnt = 0

                candidates.append((int(qid), str(title), qk, int(views), int(res_cnt)))

        if not candidates:
            return QnaTrendingResponse(status="ok", view_tier=view_tier, total_items=0, items=[])

        # Ranking (mode)
        if mode_key == "views":
            candidates.sort(key=lambda x: (x[3], x[4]), reverse=True)
        elif mode_key == "resonance":
            candidates.sort(key=lambda x: (x[4], x[3]), reverse=True)
        else:
            # overall: views + (resonances * 3)
            w_res = 3
            candidates.sort(key=lambda x: (x[3] + (x[4] * w_res), x[4], x[3]), reverse=True)

        items: List[QnaTrendingItem] = []
        for qid, title, qk, views, res_cnt in candidates[: int(limit)]:
            items.append(
                QnaTrendingItem(
                    question_id=int(qid),
                    title=str(title),
                    q_key=str(qk),
                    views=int(views or 0),
                    resonances=int(res_cnt or 0),
                )
            )

        return QnaTrendingResponse(
            status="ok",
            view_tier=view_tier,
            total_items=len(items),
            items=items,
        )


    @app.get("/mymodel/qna/holders", response_model=QnaHoldersResponse)
    async def qna_holders(
        question_id: int = Query(..., ge=1, description="Create question id"),
        limit: int = Query(default=20, ge=1, le=200, description="Max users to return"),
        exclude_followed: bool = Query(default=True, description="Exclude users already followed by viewer"),
        exclude_self: bool = Query(default=True, description="Exclude the viewer themselves"),
        authorization: Optional[str] = Header(default=None, alias="Authorization"),
    ) -> QnaHoldersResponse:
        """Return users who have answered (hold) the given question.

        This endpoint is used for "問いで表示":
        - Pick a trending question -> show users who have that Q&A -> jump to their Account page to follow.
        """

        token = _extract_bearer_token(authorization) if authorization else None
        if not token:
            raise HTTPException(status_code=401, detail="Authorization header with Bearer token is required")

        viewer_user_id = await _resolve_user_id_from_token(token)
        if not viewer_user_id:
            raise HTTPException(status_code=401, detail="Invalid token")

        # Viewer tier -> view_tier (light|standard) to avoid leaking inaccessible questions.
        viewer_tier = SubscriptionTier.FREE
        try:
            viewer_tier = await get_subscription_tier_for_user(viewer_user_id, default=SubscriptionTier.FREE)
        except Exception:
            viewer_tier = SubscriptionTier.FREE
        view_tier = _view_tier_for_subscription(viewer_tier)

        # Validate question id within viewable tier and get title.
        try:
            qrows = await _fetch_create_questions(build_tier=view_tier)
        except Exception as exc:
            logger.error("failed to fetch create questions (holders): %s", exc)
            raise HTTPException(status_code=502, detail="Failed to load questions")

        title = None
        for r in qrows or []:
            try:
                qid = int(r.get("id"))
            except Exception:
                continue
            if int(qid) != int(question_id):
                continue
            txt = str(r.get("question_text") or "").strip()
            if txt:
                title = txt
                break

        if not title:
            raise HTTPException(status_code=404, detail="Question not found")

        qk = _q_key_for_question_id(int(question_id))

        # Scan a bit more than limit to allow filtering
        scan_limit = int(max(50, min(2000, int(limit) * 25)))

        # Candidates:
        # - Primary: order by per-answer resonances for this question (metrics)
        # - Fallback: recent answer holders (updated_at desc)
        metric_ordered_ids: List[str] = []
        try:
            resp_m = await _sb_get(
                f"/rest/v1/{METRICS_TABLE}",
                params={
                    "select": "q_instance_id,resonances",
                    "q_key": f"eq.{qk}",
                    "q_instance_id": "not.is.null",
                    "order": "resonances.desc",
                    "limit": str(int(scan_limit)),
                },
            )
            if resp_m.status_code < 300:
                rows_m = resp_m.json()
                if isinstance(rows_m, list):
                    for r in rows_m:
                        iid = str((r or {}).get("q_instance_id") or "").strip()
                        if not iid:
                            continue
                        try:
                            uid, qid2 = _parse_instance_id(iid)
                        except Exception:
                            continue
                        if int(qid2) != int(question_id):
                            continue
                        if uid:
                            metric_ordered_ids.append(uid)
            else:
                logger.warning(
                    "Supabase %s select failed (holders metrics): %s %s",
                    METRICS_TABLE,
                    resp_m.status_code,
                    (resp_m.text or "")[:800],
                )
        except Exception as exc:
            logger.warning("holders metrics fetch failed: %s", exc)

        recent_holder_ids = await _fetch_holder_user_ids_for_question(
            question_id=int(question_id), scan_limit=scan_limit
        )
        public_holder_id_set = set(recent_holder_ids)
        metric_ordered_ids = [uid for uid in metric_ordered_ids if str(uid or "").strip() in public_holder_id_set]

        # Merge (unique) with size cap = scan_limit (avoid huge IN filters downstream)
        holder_ids: List[str] = []
        seen_ids: Set[str] = set()

        for uid in metric_ordered_ids:
            uid2 = str(uid or "").strip()
            if not uid2 or uid2 in seen_ids:
                continue
            seen_ids.add(uid2)
            holder_ids.append(uid2)
            if len(holder_ids) >= int(scan_limit):
                break

        if len(holder_ids) < int(scan_limit):
            for uid in recent_holder_ids:
                uid2 = str(uid or "").strip()
                if not uid2 or uid2 in seen_ids:
                    continue
                seen_ids.add(uid2)
                holder_ids.append(uid2)
                if len(holder_ids) >= int(scan_limit):
                    break

        # Optional filters
        if exclude_self:
            holder_ids = [x for x in holder_ids if str(x) != str(viewer_user_id)]

        following_set: Set[str] = set()
        if exclude_followed and holder_ids:
            following_set = await _fetch_following_set(
                viewer_user_id=str(viewer_user_id), owner_ids=set(holder_ids)
            )
            holder_ids = [x for x in holder_ids if str(x) not in following_set]

        # Trim
        holder_ids = holder_ids[: int(limit)]

        if not holder_ids:
            return QnaHoldersResponse(
                status="ok",
                view_tier=view_tier,
                question_id=int(question_id),
                title=title,
                q_key=qk,
                total_items=0,
                users=[],
            )

        profiles_map = await _fetch_profiles_by_ids(holder_ids)

        # Determine follow state for returned users (best-effort)
        follow_state: Set[str] = following_set
        if (not exclude_followed) and holder_ids:
            follow_state = await _fetch_following_set(
                viewer_user_id=str(viewer_user_id), owner_ids=set(holder_ids)
            )

        users: List[QnaHolderUser] = []
        for uid in holder_ids:
            p = profiles_map.get(str(uid))
            if not p:
                continue
            users.append(
                QnaHolderUser(
                    id=str(p.get("id") or uid),
                    display_name=(p.get("display_name") if isinstance(p.get("display_name"), str) else None),
                    friend_code=(p.get("friend_code") if isinstance(p.get("friend_code"), str) else None),
                    myprofile_code=(p.get("myprofile_code") if isinstance(p.get("myprofile_code"), str) else None),
                    is_following=(str(uid) in follow_state),
                )
            )

        return QnaHoldersResponse(
            status="ok",
            view_tier=view_tier,
            question_id=int(question_id),
            title=title,
            q_key=qk,
            total_items=len(users),
            users=users,
        )




    @app.get("/mymodel/recommend/users", response_model=QnaRecommendUsersResponse)
    async def recommend_users(
        limit: int = Query(default=5, ge=1, le=20, description="Number of users to return"),
        days: int = Query(default=7, ge=1, le=30, description="Activity window in days"),
        authorization: Optional[str] = Header(default=None, alias="Authorization"),
    ) -> QnaRecommendUsersResponse:
        """Recommend active users not yet followed by the viewer.

        Active definition (Mash confirmed):
        - within `days` (default 3), either
          - emotions.created_at >= now - days
          - OR mymodel_create_answers.updated_at >= now - days
        - count not required; either table is enough
        """

        token = _extract_bearer_token(authorization) if authorization else None
        if not token:
            raise HTTPException(status_code=401, detail="Authorization header with Bearer token is required")

        viewer_user_id = await _resolve_user_id_from_token(token)
        if not viewer_user_id:
            raise HTTPException(status_code=401, detail="Invalid token")

        window_days = int(days)
        since_iso = (datetime.now(timezone.utc) - timedelta(days=window_days)).isoformat()

        # Scan a bit more than limit to allow filtering + randomness
        scan_limit = int(max(300, min(5000, int(limit) * 800)))

        candidate_ids = await _fetch_active_user_ids(since_iso=since_iso, scan_limit=scan_limit)
        if not candidate_ids:
            return QnaRecommendUsersResponse(status="ok", days=window_days, total_items=0, users=[])

        # Exclude self
        candidate_ids.discard(str(viewer_user_id))

        # Exclude already-followed users
        followed_set = await _fetch_followed_owner_ids(viewer_user_id=str(viewer_user_id))

        pool = [uid for uid in candidate_ids if uid and (uid not in followed_set)]

        # Exclude users who disabled recommendations
        pool = await _filter_recommendation_enabled(pool)
        if not pool:
            return QnaRecommendUsersResponse(status="ok", days=window_days, total_items=0, users=[])

        random.shuffle(pool)
        picked = pool[: int(limit)]

        profiles_map = await _fetch_profiles_by_ids(picked)

        users: List[QnaHolderUser] = []
        for uid in picked:
            p = profiles_map.get(str(uid))
            if not p:
                continue
            users.append(
                QnaHolderUser(
                    id=str(p.get("id") or uid),
                    display_name=(p.get("display_name") if isinstance(p.get("display_name"), str) else None),
                    friend_code=(p.get("friend_code") if isinstance(p.get("friend_code"), str) else None),
                    myprofile_code=(p.get("myprofile_code") if isinstance(p.get("myprofile_code"), str) else None),
                    is_following=False,
                )
            )

        return QnaRecommendUsersResponse(
            status="ok",
            days=window_days,
            total_items=len(users),
            users=users,
        )

    @app.get("/mymodel/qna/detail", response_model=QnaDetailResponse)
    async def qna_detail(
        q_instance_id: str = Query(..., description="<target_user_id>:<question_id>"),
        authorization: Optional[str] = Header(default=None, alias="Authorization"),
    ) -> QnaDetailResponse:
        token = _extract_bearer_token(authorization) if authorization else None
        if not token:
            raise HTTPException(status_code=401, detail="Authorization header with Bearer token is required")
        viewer_user_id = await _resolve_user_id_from_token(token)
        if not viewer_user_id:
            raise HTTPException(status_code=401, detail="Invalid token")

        try:
            tgt, qid = _parse_instance_id(q_instance_id)
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid q_instance_id")

        # External access control
        if tgt != viewer_user_id:
            allowed = await _has_myprofile_link(viewer_user_id=viewer_user_id, owner_user_id=tgt)
            if not allowed:
                raise HTTPException(status_code=403, detail="You are not allowed to query this MyProfile")

        # Tier gating (viewer can only see effective tier)
        _, _, _, effective_tier = await _resolve_tiers(viewer_user_id=viewer_user_id, target_user_id=tgt)
        qrows = await _fetch_create_questions(build_tier=effective_tier)
        qmap = {int(r.get("id")): str(r.get("question_text") or "").strip() for r in (qrows or []) if r.get("id") is not None}
        title = qmap.get(int(qid))
        if not title:
            raise HTTPException(status_code=404, detail="Question not found")

        answers = await _fetch_create_answers(user_id=tgt, question_ids={int(qid)})
        a = answers.get(int(qid)) or {}
        body = _public_create_body_from_answer_row(a)
        if not body:
            raise HTTPException(status_code=404, detail="Answer not found")

        qk = _q_key_for_question_id(int(qid))
        metrics = await _fetch_instance_metrics({str(q_instance_id)})
        m = metrics.get(str(q_instance_id)) or {}
        try:
            views = int(m.get("views") or 0)
        except Exception:
            views = 0
        try:
            resonances = int(m.get("resonances") or 0)
        except Exception:
            resonances = 0


        discoveries = 0
        try:
            # Discoveries are stored as rows in the discovery logs table.
            discoveries = await _sb_count_rows(
                f"/rest/v1/{DISCOVERY_LOGS_TABLE}",
                params={"q_instance_id": f"eq.{q_instance_id}"},
            )
        except Exception as exc:
            # Fail-soft: discoveries are non-critical for reading the Q&A
            logger.warning("discoveries count failed (detail): %s", exc)
            discoveries = 0

        read_set = await _fetch_reads(viewer_user_id, {str(q_instance_id)})
        is_new = str(q_instance_id) not in read_set
        is_resonated = await _is_resonated(viewer_user_id, str(q_instance_id))

        return QnaDetailResponse(
            title=title,
            body=body,
            q_key=qk,
            q_instance_id=str(q_instance_id),
            views=views,
            resonances=resonances,
            discoveries=int(discoveries or 0),
            is_new=is_new,
            is_resonated=bool(is_resonated),
        )

    @app.post("/mymodel/qna/view", response_model=QnaViewResponse)
    async def qna_view(
        req: QnaViewRequest,
        authorization: Optional[str] = Header(default=None, alias="Authorization"),
    ) -> QnaViewResponse:
        token = _extract_bearer_token(authorization) if authorization else None
        if not token:
            raise HTTPException(status_code=401, detail="Authorization header with Bearer token is required")
        viewer_user_id = await _resolve_user_id_from_token(token)
        if not viewer_user_id:
            raise HTTPException(status_code=401, detail="Invalid token")

        try:
            tgt, qid = _parse_instance_id(req.q_instance_id)
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid q_instance_id")

        # External access control
        if tgt != viewer_user_id:
            allowed = await _has_myprofile_link(viewer_user_id=viewer_user_id, owner_user_id=tgt)
            if not allowed:
                raise HTTPException(status_code=403, detail="You are not allowed to query this MyProfile")

        qk = str(req.q_key or "").strip() or _q_key_for_question_id(int(qid))

        # Mark read (best-effort)
        await _upsert_read(viewer_user_id, req.q_instance_id)

        # Self views should not affect popularity metrics.
        if tgt == viewer_user_id:
            metrics = await _fetch_instance_metrics({str(req.q_instance_id)})
            m = metrics.get(str(req.q_instance_id)) or {}
            try:
                views = int(m.get("views") or 0)
            except Exception:
                views = 0
            try:
                resonances = int(m.get("resonances") or 0)
            except Exception:
                resonances = 0
            return QnaViewResponse(
                status="self",
                q_key=qk,
                q_instance_id=req.q_instance_id,
                views=views,
                resonances=resonances,
                is_new=False,
            )


        # Ranking view log (best-effort)
        await _insert_view_log(
            target_user_id=tgt,
            viewer_user_id=viewer_user_id,
            question_id=int(qid),
            q_key=qk,
            q_instance_id=req.q_instance_id,
        )

        # Increment views (count every display)
        counts = await _inc_metric(q_key=qk, q_instance_id=req.q_instance_id, field="views", delta=1)
        return QnaViewResponse(
            status="ok",
            q_key=qk,
            q_instance_id=req.q_instance_id,
            views=int(counts.get("views") or 0),
            resonances=int(counts.get("resonances") or 0),
            is_new=False,
        )

    @app.post("/mymodel/qna/resonance", response_model=QnaResonanceResponse)
    async def qna_resonance(
        req: QnaResonanceRequest,
        authorization: Optional[str] = Header(default=None, alias="Authorization"),
    ) -> QnaResonanceResponse:
        token = _extract_bearer_token(authorization) if authorization else None
        if not token:
            raise HTTPException(status_code=401, detail="Authorization header with Bearer token is required")
        viewer_user_id = await _resolve_user_id_from_token(token)
        if not viewer_user_id:
            raise HTTPException(status_code=401, detail="Invalid token")

        try:
            tgt, qid = _parse_instance_id(req.q_instance_id)
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid q_instance_id")

        # External access control
        if tgt != viewer_user_id:
            allowed = await _has_myprofile_link(viewer_user_id=viewer_user_id, owner_user_id=tgt)
            if not allowed:
                raise HTTPException(status_code=403, detail="You are not allowed to query this MyProfile")

        qk = str(req.q_key or "").strip() or _q_key_for_question_id(int(qid))

        # Self resonance is not allowed.
        if tgt == viewer_user_id:
            metrics = await _fetch_instance_metrics({str(req.q_instance_id)})
            m = metrics.get(str(req.q_instance_id)) or {}
            try:
                views = int(m.get("views") or 0)
            except Exception:
                views = 0
            try:
                res_cnt = int(m.get("resonances") or 0)
            except Exception:
                res_cnt = 0
            return QnaResonanceResponse(
                status="self",
                q_key=qk,
                q_instance_id=req.q_instance_id,
                resonated=False,
                views=views,
                resonances=res_cnt,
            )

        # NOTE:
        # Resonance (+1) is confirmed only after Echoes submission.
        # This endpoint is kept for backward compatibility, but it does not turn resonance "on".
        already = await _is_resonated(viewer_user_id, req.q_instance_id)

        # Return current counts without changing state.
        metrics = await _fetch_instance_metrics({str(req.q_instance_id)})
        m = metrics.get(str(req.q_instance_id)) or {}
        try:
            views = int(m.get("views") or 0)
        except Exception:
            views = 0
        try:
            res_cnt = int(m.get("resonances") or 0)
        except Exception:
            res_cnt = 0

        return QnaResonanceResponse(
            status="already" if already else "noop",
            q_key=qk,
            q_instance_id=req.q_instance_id,
            resonated=bool(already),
            views=views,
            resonances=res_cnt,
        )
# ---------------------------------------------------------
    # Echoes (響き) API
    # ---------------------------------------------------------


    @app.get("/mymodel/qna/echoes/reflections", response_model=QnaSavedReflectionsResponse)
    async def qna_echoes_reflections(
        order: str = Query(default="newest", description="newest | oldest"),
        limit: int = Query(default=50, ge=1, le=200, description="Max items to return"),
        offset: int = Query(default=0, ge=0, description="Offset (best-effort)"),
        authorization: Optional[str] = Header(default=None, alias="Authorization"),
    ) -> QnaSavedReflectionsResponse:
        """List reflections that the viewer has Echoes-saved (履歴ありのみ).

        Notes:
        - Ordering is by the viewer's saved timestamp (created_at in echoes table).
        - Only reflections currently accessible to the viewer (myprofile_links) are returned.
        - Titles are filtered by the viewer's view_tier (light|standard).
        """
        token = _extract_bearer_token(authorization) if authorization else None
        if not token:
            raise HTTPException(status_code=401, detail="Authorization header with Bearer token is required")

        viewer_user_id = await _resolve_user_id_from_token(token)
        if not viewer_user_id:
            raise HTTPException(status_code=401, detail="Invalid token")

        order_key = str(order or "newest").strip().lower()
        if order_key not in ("newest", "oldest"):
            order_key = "newest"
        sb_order = "created_at.desc" if order_key == "newest" else "created_at.asc"

        # Viewer tier -> view_tier (light|standard) to avoid leaking inaccessible questions.
        viewer_tier = SubscriptionTier.FREE
        try:
            viewer_tier = await get_subscription_tier_for_user(viewer_user_id, default=SubscriptionTier.FREE)
        except Exception:
            viewer_tier = SubscriptionTier.FREE
        view_tier = _view_tier_for_subscription(viewer_tier)

        # Load questions allowed for this view_tier.
        try:
            qrows = await _fetch_create_questions(build_tier=view_tier)
        except Exception as exc:
            logger.error("failed to fetch create questions (echoes reflections): %s", exc)
            raise HTTPException(status_code=502, detail="Failed to load questions")

        qmap: Dict[int, str] = {}
        for r in qrows or []:
            try:
                qid = int((r or {}).get("id"))
            except Exception:
                continue
            txt = str((r or {}).get("question_text") or "").strip()
            if txt:
                qmap[int(qid)] = txt

        if not qmap:
            return QnaSavedReflectionsResponse(
                status="ok",
                order=order_key,
                total_items=0,
                limit=int(limit),
                offset=int(offset),
                items=[],
            )

        # Only reflections currently accessible to the viewer.
        followed_set = await _fetch_followed_owner_ids(viewer_user_id=str(viewer_user_id))
        if not followed_set:
            return QnaSavedReflectionsResponse(
                status="ok",
                order=order_key,
                total_items=0,
                limit=int(limit),
                offset=int(offset),
                items=[],
            )

        scan_limit = int(min(max(int(limit) * 5, 50), 2000))

        resp = await _sb_get(
            f"/rest/v1/{ECHOES_TABLE}",
            params={
                "select": "q_instance_id,q_key,question_id,target_user_id,created_at",
                "viewer_user_id": f"eq.{viewer_user_id}",
                "order": sb_order,
                "limit": str(scan_limit),
                "offset": str(int(offset)),
            },
        )
        if resp.status_code >= 300:
            logger.error(
                "Supabase %s select failed (echoes reflections): %s %s",
                ECHOES_TABLE,
                resp.status_code,
                (resp.text or "")[:800],
            )
            raise HTTPException(status_code=502, detail="Failed to load echoes reflections")

        rows = resp.json()
        if not isinstance(rows, list) or not rows:
            return QnaSavedReflectionsResponse(
                status="ok",
                order=order_key,
                total_items=0,
                limit=int(limit),
                offset=int(offset),
                items=[],
            )

        # Deduplicate by q_instance_id (keep first in the requested order).
        picked: List[Dict[str, Any]] = []
        seen_iids: Set[str] = set()
        for r in rows:
            if not isinstance(r, dict):
                continue
            iid = str((r or {}).get("q_instance_id") or "").strip()
            if not iid or iid in seen_iids:
                continue
            seen_iids.add(iid)
            picked.append(r)
            if len(picked) >= int(limit):
                break

        # Collect owner ids for profile lookup.
        owner_ids: Set[str] = set()
        prepared: List[Tuple[str, str, int, str, str]] = []
        # tuple: (q_instance_id, owner_user_id, question_id, q_key, saved_at)

        for r in picked:
            iid = str((r or {}).get("q_instance_id") or "").strip()
            tgt = str((r or {}).get("target_user_id") or "").strip()
            if not iid or not tgt:
                continue
            if tgt not in followed_set:
                continue

            qid_val = None
            try:
                qid_val = int((r or {}).get("question_id") or 0)
            except Exception:
                qid_val = None

            if not qid_val:
                try:
                    _, qid2 = _parse_instance_id(iid)
                    qid_val = int(qid2)
                except Exception:
                    qid_val = None

            if not qid_val or int(qid_val) not in qmap:
                continue

            qk = str((r or {}).get("q_key") or "").strip() or _q_key_for_question_id(int(qid_val))
            saved_at = str((r or {}).get("created_at") or "").strip()
            if not saved_at:
                continue

            owner_ids.add(tgt)
            prepared.append((iid, tgt, int(qid_val), qk, saved_at))

        if not prepared:
            return QnaSavedReflectionsResponse(
                status="ok",
                order=order_key,
                total_items=0,
                limit=int(limit),
                offset=int(offset),
                items=[],
            )

        # MyModel Create "secret" answers are never visible (to self or others).
        if prepared:
            qids_by_owner: Dict[str, Set[int]] = {}
            for _, owner_uid, qid_val, _, _ in prepared:
                qids_by_owner.setdefault(str(owner_uid), set()).add(int(qid_val))

            secret_pairs: Set[Tuple[str, int]] = set()
            for owner_id, qids in qids_by_owner.items():
                try:
                    secret_qids = await _fetch_secret_question_ids(
                        target_user_id=str(owner_id), question_ids=set(qids)
                    )
                except Exception as exc:
                    logger.warning("secret check failed (saved reflections): %s", exc)
                    secret_qids = set(qids)  # fail-closed for this owner
                for qid_val in (secret_qids or set()):
                    secret_pairs.add((str(owner_id), int(qid_val)))

            if secret_pairs:
                prepared = [t for t in prepared if (str(t[1]), int(t[2])) not in secret_pairs]
                if not prepared:
                    return QnaSavedReflectionsResponse(
                        status="ok",
                        order=order_key,
                        total_items=0,
                        limit=int(limit),
                        offset=int(offset),
                        items=[],
                    )
                owner_ids = {t[1] for t in prepared}

        profiles_map = await _fetch_profiles_by_ids(list(owner_ids))

        items: List[QnaSavedReflectionItem] = []
        for iid, tgt, qid_val, qk, saved_at in prepared:
            p = profiles_map.get(str(tgt)) or {}
            dn = p.get("display_name") if isinstance(p, dict) else None
            dn_s = dn.strip() if isinstance(dn, str) else None
            items.append(
                QnaSavedReflectionItem(
                    q_instance_id=iid,
                    q_key=qk,
                    title=str(qmap.get(int(qid_val)) or ""),
                    owner_user_id=tgt,
                    owner_display_name=dn_s,
                    saved_at=saved_at,
                )
            )

        return QnaSavedReflectionsResponse(
            status="ok",
            order=order_key,
            total_items=len(items),
            limit=int(limit),
            offset=int(offset),
            items=items,
        )

    @app.post("/mymodel/qna/echoes/submit", response_model=QnaEchoesSubmitResponse)
    async def qna_echoes_submit(
        req: QnaEchoesSubmitRequest,
        authorization: Optional[str] = Header(default=None, alias="Authorization"),
    ) -> QnaEchoesSubmitResponse:
        token = _extract_bearer_token(authorization) if authorization else None
        if not token:
            raise HTTPException(status_code=401, detail="Authorization header with Bearer token is required")

        viewer_user_id = await _resolve_user_id_from_token(token)
        if not viewer_user_id:
            raise HTTPException(status_code=401, detail="Invalid token")

        try:
            tgt, qid = _parse_instance_id(req.q_instance_id)
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid q_instance_id")

        # External access control
        if tgt != viewer_user_id:
            allowed = await _has_myprofile_link(viewer_user_id=viewer_user_id, owner_user_id=tgt)
            if not allowed:
                raise HTTPException(status_code=403, detail="You are not allowed to query this MyProfile")

        # Self Echoes is not allowed (same as resonance)
        if tgt == viewer_user_id:
            raise HTTPException(status_code=400, detail="Self echoes is not allowed")

        qk = str(req.q_key or "").strip() or _q_key_for_question_id(int(qid))

        strength = str(req.strength or "").strip().lower()
        if strength not in ("small", "medium", "large"):
            raise HTTPException(status_code=400, detail="Invalid strength (small|medium|large)")

        memo = None
        if req.memo is not None:
            memo = str(req.memo)
            # Keep it conservative (UI may enforce its own limits)
            if len(memo) > 2000:
                raise HTTPException(status_code=400, detail="Memo too long")
            if not memo.strip():
                memo = None

        payload = {
            "viewer_user_id": str(viewer_user_id),
            "target_user_id": str(tgt),
            "question_id": int(qid),
            "q_key": str(qk),
            "q_instance_id": str(req.q_instance_id),
            "strength": strength,
            "memo": memo,
            "created_at": _now_iso(),
        }

        resp = await _sb_post(
            f"/rest/v1/{ECHOES_TABLE}",
            json=payload,
            prefer="resolution=merge-duplicates,return=minimal",
        )
        if resp.status_code >= 300:
            logger.error("Supabase %s upsert failed: %s %s", ECHOES_TABLE, resp.status_code, (resp.text or "")[:800])
            raise HTTPException(status_code=502, detail="Failed to submit echoes")

                # Echoes送信 = 共鳴確定（共鳴数は Echoes 送信後に増える）
        resonated = await _is_resonated(viewer_user_id, req.q_instance_id)

        views = 0
        res_cnt = 0

        if not resonated:
            payload_res = {
                "viewer_user_id": str(viewer_user_id),
                "q_instance_id": str(req.q_instance_id),
                "q_key": str(qk),
                "created_at": _now_iso(),
            }
            resp2 = await _sb_post(
                f"/rest/v1/{RESONANCES_TABLE}",
                json=payload_res,
                prefer="resolution=merge-duplicates,return=minimal",
            )
            if resp2.status_code >= 300:
                logger.error(
                    "Supabase %s insert failed (echoes->resonance): %s %s",
                    RESONANCES_TABLE,
                    resp2.status_code,
                    (resp2.text or "")[:800],
                )
                raise HTTPException(status_code=502, detail="Failed to confirm resonance")

            # Ranking resonance log (best-effort)
            await _insert_resonance_log(
                target_user_id=tgt,
                viewer_user_id=viewer_user_id,
                question_id=int(qid),
                q_key=qk,
                q_instance_id=req.q_instance_id,
            )

            counts = await _inc_metric(q_key=qk, q_instance_id=req.q_instance_id, field="resonances", delta=1)
            views = int(counts.get("views") or 0)
            res_cnt = int(counts.get("resonances") or 0)
            resonated = True
        else:
            metrics = await _fetch_instance_metrics({str(req.q_instance_id)})
            m = metrics.get(str(req.q_instance_id)) or {}
            try:
                views = int(m.get("views") or 0)
            except Exception:
                views = 0
            try:
                res_cnt = int(m.get("resonances") or 0)
            except Exception:
                res_cnt = 0

        return QnaEchoesSubmitResponse(
            status="ok",
            q_key=qk,
            q_instance_id=req.q_instance_id,
            strength=strength,
            memo=memo,
            resonated=bool(resonated),
            views=int(views or 0),
            resonances=int(res_cnt or 0),
        )

    @app.post("/mymodel/qna/echoes/delete", response_model=QnaEchoesDeleteResponse)
    async def qna_echoes_delete(
        req: QnaEchoesDeleteRequest,
        authorization: Optional[str] = Header(default=None, alias="Authorization"),
    ) -> QnaEchoesDeleteResponse:
        token = _extract_bearer_token(authorization) if authorization else None
        if not token:
            raise HTTPException(status_code=401, detail="Authorization header with Bearer token is required")

        viewer_user_id = await _resolve_user_id_from_token(token)
        if not viewer_user_id:
            raise HTTPException(status_code=401, detail="Invalid token")

        try:
            tgt, qid = _parse_instance_id(req.q_instance_id)
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid q_instance_id")

        # External access control
        if tgt != viewer_user_id:
            allowed = await _has_myprofile_link(viewer_user_id=viewer_user_id, owner_user_id=tgt)
            if not allowed:
                raise HTTPException(status_code=403, detail="You are not allowed to query this MyProfile")

        # Self Echoes is not allowed
        if tgt == viewer_user_id:
            raise HTTPException(status_code=400, detail="Self echoes is not allowed")

        qk = str(req.q_key or "").strip() or _q_key_for_question_id(int(qid))

        # Delete Echoes row (idempotent)
        resp_del = await _sb_delete(
            f"/rest/v1/{ECHOES_TABLE}",
            params={
                "viewer_user_id": f"eq.{viewer_user_id}",
                "q_instance_id": f"eq.{req.q_instance_id}",
            },
            prefer="return=minimal",
        )
        if resp_del.status_code >= 300:
            logger.error(
                "Supabase %s delete failed (echoes): %s %s",
                ECHOES_TABLE,
                resp_del.status_code,
                (resp_del.text or "")[:800],
            )
            raise HTTPException(status_code=502, detail="Failed to delete echoes")

        # If resonance was confirmed, delete resonance row + decrement metric
        was_resonated = await _is_resonated(viewer_user_id, req.q_instance_id)

        resp_del2 = await _sb_delete(
            f"/rest/v1/{RESONANCES_TABLE}",
            params={
                "viewer_user_id": f"eq.{viewer_user_id}",
                "q_instance_id": f"eq.{req.q_instance_id}",
            },
            prefer="return=minimal",
        )
        if resp_del2.status_code >= 300:
            logger.error(
                "Supabase %s delete failed (resonances): %s %s",
                RESONANCES_TABLE,
                resp_del2.status_code,
                (resp_del2.text or "")[:800],
            )
            raise HTTPException(status_code=502, detail="Failed to delete resonance state")

        views = 0
        res_cnt = 0

        if was_resonated:
            counts = await _inc_metric(q_key=qk, q_instance_id=req.q_instance_id, field="resonances", delta=-1)
            views = int(counts.get("views") or 0)
            res_cnt = int(counts.get("resonances") or 0)
        else:
            metrics = await _fetch_instance_metrics({str(req.q_instance_id)})
            m = metrics.get(str(req.q_instance_id)) or {}
            try:
                views = int(m.get("views") or 0)
            except Exception:
                views = 0
            try:
                res_cnt = int(m.get("resonances") or 0)
            except Exception:
                res_cnt = 0

        return QnaEchoesDeleteResponse(
            status="ok",
            q_key=qk,
            q_instance_id=req.q_instance_id,
            resonated=False,
            views=int(views or 0),
            resonances=int(res_cnt or 0),
        )

    @app.get("/mymodel/qna/echoes/history", response_model=QnaEchoesHistoryResponse)
    async def qna_echoes_history(
        q_instance_id: str = Query(..., description="<target_user_id>:<question_id>"),
        q_key: Optional[str] = Query(default=None, description="Optional; derived if omitted"),
        limit: Optional[int] = Query(default=None, description="Max items (Plus/Premium only)"),
        offset: Optional[int] = Query(default=None, description="Offset (Plus/Premium only)"),
        authorization: Optional[str] = Header(default=None, alias="Authorization"),
    ) -> QnaEchoesHistoryResponse:
        token = _extract_bearer_token(authorization) if authorization else None
        if not token:
            raise HTTPException(status_code=401, detail="Authorization header with Bearer token is required")

        viewer_user_id = await _resolve_user_id_from_token(token)
        if not viewer_user_id:
            raise HTTPException(status_code=401, detail="Invalid token")

        try:
            tgt, qid = _parse_instance_id(q_instance_id)
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid q_instance_id")

        # External access control
        if tgt != viewer_user_id:
            allowed = await _has_myprofile_link(viewer_user_id=viewer_user_id, owner_user_id=tgt)
            if not allowed:
                raise HTTPException(status_code=403, detail="You are not allowed to query this MyProfile")

        qk = str(q_key or "").strip() or _q_key_for_question_id(int(qid))

        # Entitlement (Free: latest N only; Plus/Premium: pagination)
        viewer_tier = SubscriptionTier.FREE
        try:
            viewer_tier = await get_subscription_tier_for_user(viewer_user_id, default=SubscriptionTier.FREE)
        except Exception as exc:
            logger.warning("viewer subscription tier resolve failed (echoes history): %s", exc)
            viewer_tier = SubscriptionTier.FREE

        is_free = viewer_tier == SubscriptionTier.FREE
        eff_limit = int(FREE_HISTORY_LIMIT) if is_free else int(limit or 200)
        eff_limit = max(1, min(eff_limit, 1000))
        eff_offset = 0 if is_free else int(offset or 0)
        eff_offset = max(0, eff_offset)

        # Counts (total + breakdown)
        total = await _sb_count_rows(
            f"/rest/v1/{ECHOES_TABLE}",
            params={
                "q_instance_id": f"eq.{q_instance_id}",
            },
        )
        cnt_small = await _sb_count_rows(
            f"/rest/v1/{ECHOES_TABLE}",
            params={
                "q_instance_id": f"eq.{q_instance_id}",
                "strength": "eq.small",
            },
        )
        cnt_medium = await _sb_count_rows(
            f"/rest/v1/{ECHOES_TABLE}",
            params={
                "q_instance_id": f"eq.{q_instance_id}",
                "strength": "eq.medium",
            },
        )
        cnt_large = await _sb_count_rows(
            f"/rest/v1/{ECHOES_TABLE}",
            params={
                "q_instance_id": f"eq.{q_instance_id}",
                "strength": "eq.large",
            },
        )

        # Items (anonymized: do not include viewer_user_id)
        resp = await _sb_get(
            f"/rest/v1/{ECHOES_TABLE}",
            params={
                "select": "strength,created_at",
                "q_instance_id": f"eq.{q_instance_id}",
                "order": "created_at.desc",
                "limit": str(eff_limit),
                "offset": str(eff_offset),
            },
        )
        if resp.status_code >= 300:
            logger.error("Supabase %s select failed: %s %s", ECHOES_TABLE, resp.status_code, (resp.text or "")[:800])
            raise HTTPException(status_code=502, detail="Failed to load echoes history")

        rows = resp.json()
        items: List[QnaEchoesHistoryItem] = []
        if isinstance(rows, list):
            for r in rows:
                if not isinstance(r, dict):
                    continue
                st = str(r.get("strength") or "").strip()
                ca = str(r.get("created_at") or "").strip()
                if not st or not ca:
                    continue
                items.append(QnaEchoesHistoryItem(strength=st, created_at=ca))

        # My strength / memo (optional)
        my_strength: Optional[str] = None
        my_memo: Optional[str] = None
        try:
            resp_my = await _sb_get(
                f"/rest/v1/{ECHOES_TABLE}",
                params={
                    "select": "strength,memo,created_at",
                    "viewer_user_id": f"eq.{viewer_user_id}",
                    "q_instance_id": f"eq.{q_instance_id}",
                    "order": "created_at.desc",
                    "limit": "1",
                },
            )
            if resp_my.status_code < 300:
                rr = resp_my.json()
                if isinstance(rr, list) and rr:
                    row0 = rr[0] if isinstance(rr[0], dict) else {}
                    my_strength = str((row0 or {}).get("strength") or "").strip() or None
                    memo_raw = (row0 or {}).get("memo")
                    my_memo = None if memo_raw is None else (str(memo_raw).strip() or None)
        except Exception:
            my_strength = None
            my_memo = None

        return QnaEchoesHistoryResponse(
            status="ok",
            q_key=qk,
            q_instance_id=q_instance_id,
            subscription_tier=str(viewer_tier.value),
            total=int(total or 0),
            count_small=int(cnt_small or 0),
            count_medium=int(cnt_medium or 0),
            count_large=int(cnt_large or 0),
            my_strength=my_strength,
            my_memo=my_memo,
            limit=int(eff_limit),
            is_limited=bool(is_free),
            items=items,
        )

    # ---------------------------------------------------------
    # Discoveries (気づき) API
    # ---------------------------------------------------------


    @app.get("/mymodel/qna/discoveries/reflections", response_model=QnaSavedReflectionsResponse)
    async def qna_discoveries_reflections(
        order: str = Query(default="newest", description="newest | oldest"),
        limit: int = Query(default=50, ge=1, le=200, description="Max items to return"),
        offset: int = Query(default=0, ge=0, description="Offset (best-effort)"),
        authorization: Optional[str] = Header(default=None, alias="Authorization"),
    ) -> QnaSavedReflectionsResponse:
        """List reflections that the viewer has Discoveries-saved (履歴ありのみ).

        Notes:
        - Ordering is by the viewer's saved timestamp (created_at in discovery logs table).
        - Only reflections currently accessible to the viewer (myprofile_links) are returned.
        - Titles are filtered by the viewer's view_tier (light|standard).
        """
        token = _extract_bearer_token(authorization) if authorization else None
        if not token:
            raise HTTPException(status_code=401, detail="Authorization header with Bearer token is required")

        viewer_user_id = await _resolve_user_id_from_token(token)
        if not viewer_user_id:
            raise HTTPException(status_code=401, detail="Invalid token")

        order_key = str(order or "newest").strip().lower()
        if order_key not in ("newest", "oldest"):
            order_key = "newest"
        sb_order = "created_at.desc" if order_key == "newest" else "created_at.asc"

        # Viewer tier -> view_tier (light|standard) to avoid leaking inaccessible questions.
        viewer_tier = SubscriptionTier.FREE
        try:
            viewer_tier = await get_subscription_tier_for_user(viewer_user_id, default=SubscriptionTier.FREE)
        except Exception:
            viewer_tier = SubscriptionTier.FREE
        view_tier = _view_tier_for_subscription(viewer_tier)

        # Load questions allowed for this view_tier.
        try:
            qrows = await _fetch_create_questions(build_tier=view_tier)
        except Exception as exc:
            logger.error("failed to fetch create questions (discoveries reflections): %s", exc)
            raise HTTPException(status_code=502, detail="Failed to load questions")

        qmap: Dict[int, str] = {}
        for r in qrows or []:
            try:
                qid = int((r or {}).get("id"))
            except Exception:
                continue
            txt = str((r or {}).get("question_text") or "").strip()
            if txt:
                qmap[int(qid)] = txt

        if not qmap:
            return QnaSavedReflectionsResponse(
                status="ok",
                order=order_key,
                total_items=0,
                limit=int(limit),
                offset=int(offset),
                items=[],
            )

        # Only reflections currently accessible to the viewer.
        followed_set = await _fetch_followed_owner_ids(viewer_user_id=str(viewer_user_id))
        if not followed_set:
            return QnaSavedReflectionsResponse(
                status="ok",
                order=order_key,
                total_items=0,
                limit=int(limit),
                offset=int(offset),
                items=[],
            )

        scan_limit = int(min(max(int(limit) * 5, 50), 2000))

        resp = await _sb_get(
            f"/rest/v1/{DISCOVERY_LOGS_TABLE}",
            params={
                "select": "q_instance_id,q_key,question_id,target_user_id,created_at",
                "viewer_user_id": f"eq.{viewer_user_id}",
                "order": sb_order,
                "limit": str(scan_limit),
                "offset": str(int(offset)),
            },
        )
        if resp.status_code >= 300:
            logger.error(
                "Supabase %s select failed (discoveries reflections): %s %s",
                DISCOVERY_LOGS_TABLE,
                resp.status_code,
                (resp.text or "")[:800],
            )
            raise HTTPException(status_code=502, detail="Failed to load discoveries reflections")

        rows = resp.json()
        if not isinstance(rows, list) or not rows:
            return QnaSavedReflectionsResponse(
                status="ok",
                order=order_key,
                total_items=0,
                limit=int(limit),
                offset=int(offset),
                items=[],
            )

        # Deduplicate by q_instance_id (keep first in the requested order).
        picked: List[Dict[str, Any]] = []
        seen_iids: Set[str] = set()
        for r in rows:
            if not isinstance(r, dict):
                continue
            iid = str((r or {}).get("q_instance_id") or "").strip()
            if not iid or iid in seen_iids:
                continue
            seen_iids.add(iid)
            picked.append(r)
            if len(picked) >= int(limit):
                break

        owner_ids: Set[str] = set()
        prepared: List[Tuple[str, str, int, str, str]] = []
        # tuple: (q_instance_id, owner_user_id, question_id, q_key, saved_at)

        for r in picked:
            iid = str((r or {}).get("q_instance_id") or "").strip()
            tgt = str((r or {}).get("target_user_id") or "").strip()
            if not iid or not tgt:
                continue
            if tgt not in followed_set:
                continue

            qid_val = None
            try:
                qid_val = int((r or {}).get("question_id") or 0)
            except Exception:
                qid_val = None

            if not qid_val:
                try:
                    _, qid2 = _parse_instance_id(iid)
                    qid_val = int(qid2)
                except Exception:
                    qid_val = None

            if not qid_val or int(qid_val) not in qmap:
                continue

            qk = str((r or {}).get("q_key") or "").strip() or _q_key_for_question_id(int(qid_val))
            saved_at = str((r or {}).get("created_at") or "").strip()
            if not saved_at:
                continue

            owner_ids.add(tgt)
            prepared.append((iid, tgt, int(qid_val), qk, saved_at))

        if not prepared:
            return QnaSavedReflectionsResponse(
                status="ok",
                order=order_key,
                total_items=0,
                limit=int(limit),
                offset=int(offset),
                items=[],
            )

        # MyModel Create "secret" answers are never visible (to self or others).
        if prepared:
            qids_by_owner: Dict[str, Set[int]] = {}
            for _, owner_uid, qid_val, _, _ in prepared:
                qids_by_owner.setdefault(str(owner_uid), set()).add(int(qid_val))

            secret_pairs: Set[Tuple[str, int]] = set()
            for owner_id, qids in qids_by_owner.items():
                try:
                    secret_qids = await _fetch_secret_question_ids(
                        target_user_id=str(owner_id), question_ids=set(qids)
                    )
                except Exception as exc:
                    logger.warning("secret check failed (saved reflections): %s", exc)
                    secret_qids = set(qids)  # fail-closed for this owner
                for qid_val in (secret_qids or set()):
                    secret_pairs.add((str(owner_id), int(qid_val)))

            if secret_pairs:
                prepared = [t for t in prepared if (str(t[1]), int(t[2])) not in secret_pairs]
                if not prepared:
                    return QnaSavedReflectionsResponse(
                        status="ok",
                        order=order_key,
                        total_items=0,
                        limit=int(limit),
                        offset=int(offset),
                        items=[],
                    )
                owner_ids = {t[1] for t in prepared}

        profiles_map = await _fetch_profiles_by_ids(list(owner_ids))

        items: List[QnaSavedReflectionItem] = []
        for iid, tgt, qid_val, qk, saved_at in prepared:
            p = profiles_map.get(str(tgt)) or {}
            dn = p.get("display_name") if isinstance(p, dict) else None
            dn_s = dn.strip() if isinstance(dn, str) else None
            items.append(
                QnaSavedReflectionItem(
                    q_instance_id=iid,
                    q_key=qk,
                    title=str(qmap.get(int(qid_val)) or ""),
                    owner_user_id=tgt,
                    owner_display_name=dn_s,
                    saved_at=saved_at,
                )
            )

        return QnaSavedReflectionsResponse(
            status="ok",
            order=order_key,
            total_items=len(items),
            limit=int(limit),
            offset=int(offset),
            items=items,
        )

    @app.post("/mymodel/qna/discoveries/submit", response_model=QnaDiscoverySubmitResponse)
    async def qna_discovery_submit(
        req: QnaDiscoverySubmitRequest,
        authorization: Optional[str] = Header(default=None, alias="Authorization"),
    ) -> QnaDiscoverySubmitResponse:
        token = _extract_bearer_token(authorization) if authorization else None
        if not token:
            raise HTTPException(status_code=401, detail="Authorization header with Bearer token is required")

        viewer_user_id = await _resolve_user_id_from_token(token)
        if not viewer_user_id:
            raise HTTPException(status_code=401, detail="Invalid token")

        try:
            tgt, qid = _parse_instance_id(req.q_instance_id)
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid q_instance_id")

        # External access control
        if tgt != viewer_user_id:
            allowed = await _has_myprofile_link(viewer_user_id=viewer_user_id, owner_user_id=tgt)
            if not allowed:
                raise HTTPException(status_code=403, detail="You are not allowed to query this MyProfile")

        # Self discovery is not allowed (Discoveries are for "other people's reflections")
        if tgt == viewer_user_id:
            raise HTTPException(status_code=400, detail="Self discoveries is not allowed")

        qk = str(req.q_key or "").strip() or _q_key_for_question_id(int(qid))

        category = str(req.category or "").strip()
        allowed_cats = {"new_perspective", "different_fun", "well_worded", "not_sorted", "shocked"}
        if category not in allowed_cats:
            raise HTTPException(status_code=400, detail="Invalid category")

        memo = None
        if req.memo is not None:
            memo = str(req.memo)
            # Keep it conservative (UI may enforce its own limits)
            if len(memo) > 2000:
                raise HTTPException(status_code=400, detail="Memo too long")

        payload = {
            "viewer_user_id": str(viewer_user_id),
            "target_user_id": str(tgt),
            "question_id": int(qid),
            "q_key": str(qk),
            "q_instance_id": str(req.q_instance_id),
            "category": category,
            "memo": memo,
            "created_at": _now_iso(),
        }

        resp = await _sb_post(
            f"/rest/v1/{DISCOVERY_LOGS_TABLE}",
            json=payload,
            prefer="return=representation",
        )
        if resp.status_code >= 300:
            logger.error(
                "Supabase %s insert failed: %s %s",
                DISCOVERY_LOGS_TABLE,
                resp.status_code,
                (resp.text or "")[:800],
            )
            raise HTTPException(status_code=502, detail="Failed to submit discovery")

        inserted_id: Optional[str] = None
        try:
            data = resp.json()
            if isinstance(data, list) and data:
                inserted_id = str((data[0] or {}).get("id") or "").strip() or None
        except Exception:
            inserted_id = None

        return QnaDiscoverySubmitResponse(status="ok", q_key=qk, q_instance_id=req.q_instance_id, id=inserted_id)

    @app.post("/mymodel/qna/discoveries/delete", response_model=QnaDiscoveryDeleteResponse)
    async def qna_discovery_delete(
        req: QnaDiscoveryDeleteRequest,
        authorization: Optional[str] = Header(default=None, alias="Authorization"),
    ) -> QnaDiscoveryDeleteResponse:
        token = _extract_bearer_token(authorization) if authorization else None
        if not token:
            raise HTTPException(status_code=401, detail="Authorization header with Bearer token is required")

        viewer_user_id = await _resolve_user_id_from_token(token)
        if not viewer_user_id:
            raise HTTPException(status_code=401, detail="Invalid token")

        try:
            tgt, qid = _parse_instance_id(req.q_instance_id)
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid q_instance_id")

        # External access control
        if tgt != viewer_user_id:
            allowed = await _has_myprofile_link(viewer_user_id=viewer_user_id, owner_user_id=tgt)
            if not allowed:
                raise HTTPException(status_code=403, detail="You are not allowed to query this MyProfile")

        # Self discovery is not allowed
        if tgt == viewer_user_id:
            raise HTTPException(status_code=400, detail="Self discoveries is not allowed")

        qk = str(req.q_key or "").strip() or _q_key_for_question_id(int(qid))

        # Delete discovery row(s) (idempotent)
        resp_del = await _sb_delete(
            f"/rest/v1/{DISCOVERY_LOGS_TABLE}",
            params={
                "viewer_user_id": f"eq.{viewer_user_id}",
                "q_instance_id": f"eq.{req.q_instance_id}",
            },
            prefer="return=minimal",
        )
        if resp_del.status_code >= 300:
            logger.error(
                "Supabase %s delete failed (discoveries): %s %s",
                DISCOVERY_LOGS_TABLE,
                resp_del.status_code,
                (resp_del.text or "")[:800],
            )
            raise HTTPException(status_code=502, detail="Failed to delete discovery")

        # Return updated global count for this reflection
        discoveries = 0
        try:
            discoveries = await _sb_count_rows(
                f"/rest/v1/{DISCOVERY_LOGS_TABLE}",
                params={"q_instance_id": f"eq.{req.q_instance_id}"},
            )
        except Exception as exc:
            logger.warning("discoveries count failed (delete): %s", exc)
            discoveries = 0

        return QnaDiscoveryDeleteResponse(
            status="ok",
            q_key=qk,
            q_instance_id=req.q_instance_id,
            discoveries=int(discoveries or 0),
        )

    @app.get("/mymodel/qna/discoveries/history", response_model=QnaDiscoveryHistoryResponse)
    async def qna_discovery_history(
        q_instance_id: str = Query(..., description="<target_user_id>:<question_id>"),
        q_key: Optional[str] = Query(default=None, description="Optional; derived if omitted"),
        limit: Optional[int] = Query(default=None, description="Max items (Plus/Premium only)"),
        offset: Optional[int] = Query(default=None, description="Offset (Plus/Premium only)"),
        authorization: Optional[str] = Header(default=None, alias="Authorization"),
    ) -> QnaDiscoveryHistoryResponse:
        token = _extract_bearer_token(authorization) if authorization else None
        if not token:
            raise HTTPException(status_code=401, detail="Authorization header with Bearer token is required")

        viewer_user_id = await _resolve_user_id_from_token(token)
        if not viewer_user_id:
            raise HTTPException(status_code=401, detail="Invalid token")

        try:
            tgt, qid = _parse_instance_id(q_instance_id)
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid q_instance_id")

        # External access control (viewer must be able to view the reflection to see their discoveries)
        if tgt != viewer_user_id:
            allowed = await _has_myprofile_link(viewer_user_id=viewer_user_id, owner_user_id=tgt)
            if not allowed:
                raise HTTPException(status_code=403, detail="You are not allowed to query this MyProfile")

        qk = str(q_key or "").strip() or _q_key_for_question_id(int(qid))

        viewer_tier = SubscriptionTier.FREE
        try:
            viewer_tier = await get_subscription_tier_for_user(viewer_user_id, default=SubscriptionTier.FREE)
        except Exception as exc:
            logger.warning("viewer subscription tier resolve failed (discoveries history): %s", exc)
            viewer_tier = SubscriptionTier.FREE

        is_free = viewer_tier == SubscriptionTier.FREE
        eff_limit = int(FREE_HISTORY_LIMIT) if is_free else int(limit or 200)
        eff_limit = max(1, min(eff_limit, 1000))
        eff_offset = 0 if is_free else int(offset or 0)
        eff_offset = max(0, eff_offset)

        total = await _sb_count_rows(
            f"/rest/v1/{DISCOVERY_LOGS_TABLE}",
            params={
                "viewer_user_id": f"eq.{viewer_user_id}",
                "q_instance_id": f"eq.{q_instance_id}",
            },
        )

        resp = await _sb_get(
            f"/rest/v1/{DISCOVERY_LOGS_TABLE}",
            params={
                "select": "id,category,memo,created_at",
                "viewer_user_id": f"eq.{viewer_user_id}",
                "q_instance_id": f"eq.{q_instance_id}",
                "order": "created_at.desc",
                "limit": str(eff_limit),
                "offset": str(eff_offset),
            },
        )
        if resp.status_code >= 300:
            logger.error(
                "Supabase %s select failed: %s %s",
                DISCOVERY_LOGS_TABLE,
                resp.status_code,
                (resp.text or "")[:800],
            )
            raise HTTPException(status_code=502, detail="Failed to load discoveries history")

        rows = resp.json()
        items: List[QnaDiscoveryHistoryItem] = []
        if isinstance(rows, list):
            for r in rows:
                if not isinstance(r, dict):
                    continue
                iid = str(r.get("id") or "").strip()
                if not iid:
                    continue
                cat = str(r.get("category") or "").strip()
                memo = r.get("memo")
                memo_s = None if memo is None else str(memo)
                ca = str(r.get("created_at") or "").strip()
                items.append(QnaDiscoveryHistoryItem(id=iid, category=cat, memo=memo_s, created_at=ca))

        return QnaDiscoveryHistoryResponse(
            status="ok",
            q_key=qk,
            q_instance_id=q_instance_id,
            subscription_tier=str(viewer_tier.value),
            total=int(total or 0),
            limit=int(eff_limit),
            is_limited=bool(is_free),
            items=items,
        )



# ============================================================================
# Reflection-unified overrides (create + generated)
# Appended patch: preserve legacy implementation above, override only the
# route registration function while reusing existing helpers.
# ============================================================================
from fastapi.routing import APIRoute as _FastAPIRoute

MYMODEL_REFLECTIONS_TABLE = (
    os.getenv("MYMODEL_REFLECTIONS_TABLE", "mymodel_reflections") or "mymodel_reflections"
).strip() or "mymodel_reflections"


def _remove_registered_route(app: FastAPI, path: str, methods: Set[str]) -> None:
    methods_u = {str(m).upper() for m in (methods or set())}
    kept = []
    for r in list(app.router.routes):
        if isinstance(r, _FastAPIRoute) and getattr(r, "path", None) == path:
            route_methods = {str(m).upper() for m in (getattr(r, "methods", set()) or set())}
            if route_methods & methods_u:
                continue
        kept.append(r)
    app.router.routes[:] = kept


async def _sb_get_json_local(path: str, *, params: Dict[str, str]) -> List[Dict[str, Any]]:
    resp = await _sb_get(path, params=params)
    if resp.status_code >= 300:
        logger.error("Supabase GET failed: %s %s", resp.status_code, (resp.text or "")[:1200])
        raise HTTPException(status_code=502, detail="Failed to load reflections")
    try:
        data = resp.json()
    except Exception:
        return []
    if isinstance(data, list):
        return [x for x in data if isinstance(x, dict)]
    return []


def _is_generated_reflection_instance_id(q_instance_id: str) -> bool:
    return str(q_instance_id or "").strip().startswith("reflection:")


def _build_generated_q_key(row: Dict[str, Any]) -> str:
    qk = str((row or {}).get("q_key") or "").strip()
    if qk:
        return qk
    topic_key = str((row or {}).get("topic_key") or "").strip()
    if topic_key:
        return f"generated:{topic_key}"
    rid = str((row or {}).get("id") or "").strip()
    return f"generated:{rid}" if rid else "generated:unknown"


def _generated_public_id(row: Dict[str, Any]) -> str:
    return str((row or {}).get("public_id") or "").strip()


async def _fetch_generated_reflection_by_public_id(
    public_id: str,
    *,
    owner_user_id: Optional[str] = None,
    require_active: bool = True,
    require_ready: bool = True,
) -> Optional[Dict[str, Any]]:
    pid = str(public_id or "").strip()
    if not pid:
        return None
    params: Dict[str, str] = {
        "select": "*",
        "public_id": f"eq.{pid}",
        "source_type": "eq.generated",
        "limit": "1",
    }
    oid = str(owner_user_id or "").strip()
    if oid:
        params["owner_user_id"] = f"eq.{oid}"
    if require_active:
        params["is_active"] = "eq.true"
    if require_ready:
        params["status"] = "in.(ready,published)"
    rows = await _sb_get_json_local(f"/rest/v1/{MYMODEL_REFLECTIONS_TABLE}", params=params)
    return rows[0] if rows else None


async def _fetch_generated_reflections_by_public_ids(
    public_ids: Set[str],
    *,
    require_active: bool = True,
    require_ready: bool = True,
) -> Dict[str, Dict[str, Any]]:
    ids = {str(x).strip() for x in (public_ids or set()) if str(x).strip()}
    if not ids:
        return {}
    params: Dict[str, str] = {
        "select": "*",
        "public_id": _quoted_in(ids),
        "source_type": "eq.generated",
        "limit": str(max(1, len(ids))),
    }
    if require_active:
        params["is_active"] = "eq.true"
    if require_ready:
        params["status"] = "in.(ready,published)"
    rows = await _sb_get_json_local(f"/rest/v1/{MYMODEL_REFLECTIONS_TABLE}", params=params)
    out: Dict[str, Dict[str, Any]] = {}
    for r in rows:
        pid = _generated_public_id(r)
        if pid:
            out[pid] = r
    return out


async def _fetch_active_generated_reflections_for_owner(owner_user_id: str, *, limit: int = 200) -> List[Dict[str, Any]]:
    oid = str(owner_user_id or "").strip()
    if not oid:
        return []
    owner_policy = await _resolve_owner_reflection_policy(oid)
    if not bool(owner_policy.get("can_expose_generated_reflections")):
        return []
    return await _sb_get_json_local(
        f"/rest/v1/{MYMODEL_REFLECTIONS_TABLE}",
        params={
            "select": "*",
            "owner_user_id": f"eq.{oid}",
            "source_type": "eq.generated",
            "is_active": "eq.true",
            "status": "in.(ready,published)",
            "order": "updated_at.desc",
            "limit": str(max(1, int(limit))),
        },
    )


async def _resolve_generated_reflection_access(
    *, viewer_user_id: str, q_instance_id: str
) -> Dict[str, Any]:
    row = await _fetch_generated_reflection_by_public_id(q_instance_id)
    if not row:
        raise HTTPException(status_code=404, detail="Reflection not found")
    owner_user_id = str((row or {}).get("owner_user_id") or "").strip()
    if not owner_user_id:
        raise HTTPException(status_code=404, detail="Reflection not found")
    owner_policy = await _resolve_owner_reflection_policy(owner_user_id)
    if not bool(owner_policy.get("can_expose_generated_reflections")):
        raise HTTPException(status_code=404, detail="Reflection not found")
    if owner_user_id != str(viewer_user_id):
        allowed = await _has_myprofile_link(viewer_user_id=viewer_user_id, owner_user_id=owner_user_id)
        if not allowed:
            raise HTTPException(status_code=403, detail="You are not allowed to query this MyProfile")
    return row


async def _resolve_qna_context_for_reaction(
    *, viewer_user_id: str, q_instance_id: str, q_key: Optional[str]
) -> Dict[str, Any]:
    iid = str(q_instance_id or "").strip()
    if _is_generated_reflection_instance_id(iid):
        row = await _resolve_generated_reflection_access(
            viewer_user_id=viewer_user_id,
            q_instance_id=iid,
        )
        owner_user_id = str((row or {}).get("owner_user_id") or "").strip()
        return {
            "kind": "generated",
            "target_user_id": owner_user_id,
            "question_id": 0,
            "q_key": str(q_key or "").strip() or _build_generated_q_key(row),
            "row": row,
            "context_source_type": str((row or {}).get("source_type") or "generated").strip() or "generated",
            "context_question": str((row or {}).get("question") or "").strip() or None,
            "context_answer": str((row or {}).get("answer") or "").strip() or None,
            "context_topic_key": str((row or {}).get("topic_key") or "").strip() or None,
            "context_category": str((row or {}).get("category") or "").strip() or None,
        }

    try:
        tgt, qid = _parse_instance_id(iid)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid q_instance_id")

    if tgt != viewer_user_id:
        allowed = await _has_myprofile_link(viewer_user_id=viewer_user_id, owner_user_id=tgt)
        if not allowed:
            raise HTTPException(status_code=403, detail="You are not allowed to query this MyProfile")

    _, _, _, effective_tier = await _resolve_tiers(
        viewer_user_id=viewer_user_id,
        target_user_id=tgt,
    )
    qrows = await _fetch_create_questions(build_tier=effective_tier)
    qmap = {
        int(r.get("id")): str(r.get("question_text") or "").strip()
        for r in (qrows or [])
        if r.get("id") is not None
    }
    title = qmap.get(int(qid))
    if not title:
        raise HTTPException(status_code=404, detail="Question not found")

    answers = await _fetch_create_answers(user_id=tgt, question_ids={int(qid)})
    a = answers.get(int(qid)) or {}
    body = _public_create_body_from_answer_row(a)
    if not body:
        raise HTTPException(status_code=404, detail="Answer not found")

    return {
        "kind": "create",
        "target_user_id": str(tgt),
        "question_id": int(qid),
        "q_key": str(q_key or "").strip() or _q_key_for_question_id(int(qid)),
        "row": None,
        "context_source_type": "create",
        "context_question": title or None,
        "context_answer": body or None,
        "context_topic_key": None,
        "context_category": None,
    }


async def _fetch_create_list_items(
    *, viewer_user_id: str, target_user_id: str, effective_tier: str
) -> List[QnaListItem]:
    qrows = await _fetch_create_questions(build_tier=effective_tier)
    if not qrows:
        return []

    qmap: Dict[int, str] = {}
    ordered_qids: List[int] = []
    for r in qrows or []:
        try:
            qid = int((r or {}).get("id"))
        except Exception:
            continue
        txt = str((r or {}).get("question_text") or "").strip()
        if not txt:
            continue
        qmap[int(qid)] = txt
        ordered_qids.append(int(qid))

    if not qmap:
        return []

    answers = await _fetch_create_answers(user_id=target_user_id, question_ids=set(qmap.keys()))
    visible_answer_ids: Set[int] = set()
    for qid in ordered_qids:
        row = answers.get(int(qid)) or {}
        body = _public_create_body_from_answer_row(row)
        if not body:
            continue
        visible_answer_ids.add(int(qid))

    if not visible_answer_ids:
        return []

    q_instance_ids: Set[str] = {f"{target_user_id}:{qid}" for qid in visible_answer_ids}
    metrics = await _fetch_instance_metrics(q_instance_ids)
    discoveries_map = await _fetch_discovery_counts_for_instances(q_instance_ids)
    read_set = await _fetch_reads(viewer_user_id, q_instance_ids)

    items: List[QnaListItem] = []
    for qid in ordered_qids:
        if int(qid) not in visible_answer_ids:
            continue
        iid = f"{target_user_id}:{int(qid)}"
        m = metrics.get(iid) or {}
        try:
            views = int(m.get("views") or 0)
        except Exception:
            views = 0
        try:
            resonances = int(m.get("resonances") or 0)
        except Exception:
            resonances = 0
        try:
            discoveries = int(discoveries_map.get(iid) or 0)
        except Exception:
            discoveries = 0
        a = answers.get(int(qid)) or {}
        generated_at = str(a.get("updated_at") or "").strip() or None
        items.append(
            QnaListItem(
                title=str(qmap.get(int(qid)) or ""),
                q_key=_q_key_for_question_id(int(qid)),
                q_instance_id=iid,
                generated_at=generated_at,
                views=views,
                resonances=resonances,
                discoveries=discoveries,
                is_new=(iid not in read_set),
            )
        )
    return items


async def _fetch_generated_list_items(*, viewer_user_id: str, target_user_id: str) -> List[QnaListItem]:
    rows = await _fetch_active_generated_reflections_for_owner(target_user_id, limit=200)
    if not rows:
        return []

    q_instance_ids: Set[str] = {_generated_public_id(r) for r in rows if _generated_public_id(r)}
    metrics = await _fetch_instance_metrics(q_instance_ids)
    discoveries_map = await _fetch_discovery_counts_for_instances(q_instance_ids)
    read_set = await _fetch_reads(viewer_user_id, q_instance_ids)

    items: List[QnaListItem] = []
    for r in rows:
        iid = _generated_public_id(r)
        if not iid:
            continue
        qk = _build_generated_q_key(r)
        title = str((r or {}).get("question") or "").strip()
        if not title:
            continue
        m = metrics.get(iid) or {}
        try:
            views = int(m.get("views") or 0)
        except Exception:
            views = 0
        try:
            resonances = int(m.get("resonances") or 0)
        except Exception:
            resonances = 0
        try:
            discoveries = int(discoveries_map.get(iid) or 0)
        except Exception:
            discoveries = 0
        generated_at = str((r or {}).get("updated_at") or (r or {}).get("created_at") or "").strip() or None
        items.append(
            QnaListItem(
                title=title,
                q_key=qk,
                q_instance_id=iid,
                generated_at=generated_at,
                views=views,
                resonances=resonances,
                discoveries=discoveries,
                is_new=(iid not in read_set),
            )
        )
    return items


async def _fetch_generated_unread_counts(*, viewer_user_id: str, target_user_id: str) -> Tuple[int, int]:
    rows = await _fetch_active_generated_reflections_for_owner(target_user_id, limit=500)
    if not rows:
        return (0, 0)
    q_instance_ids: Set[str] = {_generated_public_id(r) for r in rows if _generated_public_id(r)}
    read_set = await _fetch_reads(viewer_user_id, q_instance_ids)
    total = len(q_instance_ids)
    unread = sum(1 for iid in q_instance_ids if iid not in read_set)
    return (total, unread)


async def _fetch_create_unread_counts(
    *, viewer_user_id: str, target_user_id: str, effective_tier: str
) -> Tuple[int, int]:
    qrows = await _fetch_create_questions(build_tier=effective_tier)
    if not qrows:
        return (0, 0)

    question_ids: Set[int] = set()
    for row in qrows or []:
        try:
            question_ids.add(int((row or {}).get("id")))
        except Exception:
            continue

    if not question_ids:
        return (0, 0)

    answers = await _fetch_create_answers(user_id=target_user_id, question_ids=question_ids)
    visible_instance_ids: Set[str] = set()
    for qid in question_ids:
        answer_row = answers.get(int(qid)) or {}
        answer_text = _public_create_body_from_answer_row(answer_row)
        if not answer_text:
            continue
        visible_instance_ids.add(f"{target_user_id}:{int(qid)}")

    if not visible_instance_ids:
        return (0, 0)

    read_set = await _fetch_reads(viewer_user_id, visible_instance_ids)
    total_items = len(visible_instance_ids)
    unread_count = sum(1 for iid in visible_instance_ids if iid not in read_set)
    return (total_items, unread_count)


async def _compute_qna_unread_for_target(*, viewer_user_id: str, target_user_id: str) -> QnaUnreadResponse:
    create_total = 0
    create_unread = 0
    try:
        _, _, _, effective_tier = await _resolve_tiers(
            viewer_user_id=viewer_user_id,
            target_user_id=target_user_id,
        )
        create_total, create_unread = await _fetch_create_unread_counts(
            viewer_user_id=str(viewer_user_id),
            target_user_id=str(target_user_id),
            effective_tier=str(effective_tier),
        )
    except Exception as exc:
        logger.warning("create unread probe failed: %s", exc)

    gen_total = 0
    gen_unread = 0
    try:
        gen_total, gen_unread = await _fetch_generated_unread_counts(
            viewer_user_id=str(viewer_user_id),
            target_user_id=str(target_user_id),
        )
    except Exception as exc:
        logger.warning("generated unread probe failed: %s", exc)

    total_items = int(create_total) + int(gen_total)
    unread_count = int(create_unread) + int(gen_unread)
    return QnaUnreadResponse(
        status="ok",
        viewer_user_id=str(viewer_user_id),
        target_user_id=str(target_user_id),
        total_items=total_items,
        unread_count=unread_count,
        has_unread=unread_count > 0,
    )


async def _build_saved_generated_items(
    *,
    prepared_rows: List[Tuple[str, str, str]],  # (q_instance_id, owner_user_id, saved_at)
) -> List[QnaSavedReflectionItem]:
    if not prepared_rows:
        return []
    owner_ids = {str(owner) for _, owner, _ in prepared_rows if str(owner or "").strip()}
    owner_policies = await _resolve_owner_reflection_policies(owner_ids)
    visible_rows = [
        row
        for row in prepared_rows
        if bool((owner_policies.get(str(row[1])) or {}).get("can_expose_generated_reflections"))
    ]
    if not visible_rows:
        return []
    ids = {iid for iid, _, _ in visible_rows}
    rows_map = await _fetch_generated_reflections_by_public_ids(ids, require_active=True, require_ready=True)
    profiles_map = await _fetch_profiles_by_ids(list({owner for _, owner, _ in visible_rows}))
    items: List[QnaSavedReflectionItem] = []
    for iid, owner_uid, saved_at in visible_rows:
        row = rows_map.get(iid)
        if not row:
            continue
        title = str((row or {}).get("question") or "").strip()
        if not title:
            continue
        p = profiles_map.get(str(owner_uid)) or {}
        dn = p.get("display_name") if isinstance(p, dict) else None
        dn_s = dn.strip() if isinstance(dn, str) else None
        items.append(
            QnaSavedReflectionItem(
                q_instance_id=iid,
                q_key=_build_generated_q_key(row),
                title=title,
                owner_user_id=str(owner_uid),
                owner_display_name=dn_s,
                saved_at=saved_at,
            )
        )
    return items


async def _build_saved_create_items(
    *,
    prepared_rows: List[Tuple[str, str, int, str, str]],  # (q_instance_id, owner_user_id, question_id, q_key, saved_at)
) -> List[QnaSavedReflectionItem]:
    if not prepared_rows:
        return []

    owner_ids = {str(owner_uid) for _, owner_uid, _, _, _ in prepared_rows if str(owner_uid or "").strip()}
    owner_policies = await _resolve_owner_reflection_policies(owner_ids)
    question_maps = await _fetch_question_maps_for_build_tiers(
        {str((owner_policies.get(owner_id) or {}).get("build_tier") or "light") for owner_id in owner_ids}
    )

    visible_rows: List[Tuple[str, str, int, str, str, str]] = []
    qids_by_owner: Dict[str, Set[int]] = {}
    for iid, owner_uid, qid_val, qk, saved_at in prepared_rows:
        owner_id = str(owner_uid or "").strip()
        policy = owner_policies.get(owner_id) or {}
        owner_build_tier = str(policy.get("build_tier") or "light")
        owner_qmap = question_maps.get(owner_build_tier) or {}
        title = str(owner_qmap.get(int(qid_val)) or "").strip()
        if not title:
            continue
        visible_rows.append((iid, owner_id, int(qid_val), qk, saved_at, title))
        qids_by_owner.setdefault(owner_id, set()).add(int(qid_val))

    if not visible_rows:
        return []

    public_pairs: Set[Tuple[str, int]] = set()
    for owner_id, qids in qids_by_owner.items():
        try:
            owner_answers = await _fetch_create_answers(user_id=str(owner_id), question_ids=set(qids))
        except Exception as exc:
            logger.warning("public reflection check failed (saved reflections): %s", exc)
            owner_answers = {}
        for qid_val in qids:
            answer_row = owner_answers.get(int(qid_val)) if isinstance(owner_answers, dict) else None
            if _public_create_body_from_answer_row(answer_row):
                public_pairs.add((str(owner_id), int(qid_val)))

    visible_rows = [
        row
        for row in visible_rows
        if (str(row[1]), int(row[2])) in public_pairs
    ]
    if not visible_rows:
        return []

    profiles_map = await _fetch_profiles_by_ids(list({row[1] for row in visible_rows}))
    items: List[QnaSavedReflectionItem] = []
    for iid, owner_uid, qid_val, qk, saved_at, title in visible_rows:
        p = profiles_map.get(str(owner_uid)) or {}
        dn = p.get("display_name") if isinstance(p, dict) else None
        dn_s = dn.strip() if isinstance(dn, str) else None
        items.append(
            QnaSavedReflectionItem(
                q_instance_id=iid,
                q_key=qk,
                title=title,
                owner_user_id=str(owner_uid),
                owner_display_name=dn_s,
                saved_at=saved_at,
            )
        )
    return items


_register_mymodel_qna_routes_legacy = register_mymodel_qna_routes


def register_mymodel_qna_routes(app: FastAPI) -> None:  # type: ignore[override]
    """Register routes with generated-reflection support.

    Strategy:
    - register legacy routes first
    - remove only the paths that need generated-reflection support
    - re-register patched routes
    """
    _register_mymodel_qna_routes_legacy(app)

    for path, methods in [
        ("/mymodel/qna/list", {"GET"}),
        ("/mymodel/qna/unread", {"GET"}),
        ("/mymodel/qna/unread-status", {"GET"}),
        ("/mymodel/qna/detail", {"GET"}),
        ("/mymodel/qna/view", {"POST"}),
        ("/mymodel/qna/resonance", {"POST"}),
        ("/mymodel/qna/echoes/reflections", {"GET"}),
        ("/mymodel/qna/echoes/submit", {"POST"}),
        ("/mymodel/qna/echoes/delete", {"POST"}),
        ("/mymodel/qna/echoes/history", {"GET"}),
        ("/mymodel/qna/discoveries/reflections", {"GET"}),
        ("/mymodel/qna/discoveries/submit", {"POST"}),
        ("/mymodel/qna/discoveries/delete", {"POST"}),
        ("/mymodel/qna/discoveries/history", {"GET"}),
    ]:
        _remove_registered_route(app, path, methods)

    @app.get("/mymodel/qna/list", response_model=QnaListResponse)
    async def qna_list(
        target_user_id: Optional[str] = Query(default=None, description="Owner of the MyModel (defaults to viewer)"),
        sort: str = Query(default="newest", description="newest | popular"),
        metric: str = Query(default="views", description="views | resonances | discoveries (only for popular)"),
        authorization: Optional[str] = Header(default=None, alias="Authorization"),
    ) -> QnaListResponse:
        token = _extract_bearer_token(authorization) if authorization else None
        if not token:
            raise HTTPException(status_code=401, detail="Authorization header with Bearer token is required")

        viewer_user_id = await _resolve_user_id_from_token(token)
        if not viewer_user_id:
            raise HTTPException(status_code=401, detail="Invalid token")

        tgt = str(target_user_id or viewer_user_id).strip()
        if not tgt:
            raise HTTPException(status_code=400, detail="target_user_id is required")

        if tgt != viewer_user_id:
            allowed = await _has_myprofile_link(viewer_user_id=viewer_user_id, owner_user_id=tgt)
            if not allowed:
                raise HTTPException(status_code=403, detail="You are not allowed to query this MyProfile")

        subscription_tier, view_tier, build_tier, effective_tier = await _resolve_tiers(
            viewer_user_id=viewer_user_id, target_user_id=tgt
        )

        try:
            create_items = await _fetch_create_list_items(
                viewer_user_id=str(viewer_user_id),
                target_user_id=str(tgt),
                effective_tier=str(effective_tier),
            )
        except HTTPException:
            raise
        except Exception as exc:
            logger.error("create list build failed: %s", exc)
            raise HTTPException(status_code=502, detail="Failed to load reflections")

        generated_items = await _fetch_generated_list_items(viewer_user_id=str(viewer_user_id), target_user_id=str(tgt))

        items = [*create_items, *generated_items]

        sort_key = str(sort or "newest").strip().lower()
        metric_key = str(metric or "views").strip().lower()
        if sort_key == "popular":
            if metric_key not in ("views", "resonances", "discoveries"):
                metric_key = "views"
            if metric_key == "discoveries":
                items.sort(key=lambda x: (x.discoveries, x.resonances, x.views, x.generated_at or ""), reverse=True)
            elif metric_key == "resonances":
                items.sort(key=lambda x: (x.resonances, x.views, x.generated_at or ""), reverse=True)
            else:
                items.sort(key=lambda x: (x.views, x.resonances, x.generated_at or ""), reverse=True)
        else:
            items.sort(key=lambda x: (x.generated_at or ""), reverse=True)

        meta = QnaListMeta(
            viewer_user_id=str(viewer_user_id),
            target_user_id=tgt,
            subscription_tier=subscription_tier,
            view_tier=view_tier,
            build_tier=build_tier,
            effective_tier=effective_tier,
            total_items=len(items),
        )
        return QnaListResponse(items=items, meta=meta)

    @app.get("/mymodel/qna/unread", response_model=QnaUnreadResponse)
    async def qna_unread(
        target_user_id: Optional[str] = Query(default=None, description="Owner of the MyModel (defaults to viewer)"),
        authorization: Optional[str] = Header(default=None, alias="Authorization"),
    ) -> QnaUnreadResponse:
        token = _extract_bearer_token(authorization) if authorization else None
        if not token:
            raise HTTPException(status_code=401, detail="Authorization header with Bearer token is required")
        viewer_user_id = await _resolve_user_id_from_token(token)
        if not viewer_user_id:
            raise HTTPException(status_code=401, detail="Invalid token")
        tgt = str(target_user_id or viewer_user_id).strip()
        if not tgt:
            raise HTTPException(status_code=400, detail="target_user_id is required")
        if tgt != viewer_user_id:
            allowed = await _has_myprofile_link(viewer_user_id=viewer_user_id, owner_user_id=tgt)
            if not allowed:
                raise HTTPException(status_code=403, detail="You are not allowed to query this MyProfile")

        return await _compute_qna_unread_for_target(
            viewer_user_id=str(viewer_user_id),
            target_user_id=str(tgt),
        )

    @app.get("/mymodel/qna/unread-status", response_model=QnaUnreadStatusResponse)
    async def qna_unread_status(
        authorization: Optional[str] = Header(default=None, alias="Authorization"),
    ) -> QnaUnreadStatusResponse:
        token = _extract_bearer_token(authorization) if authorization else None
        if not token:
            raise HTTPException(status_code=401, detail="Authorization header with Bearer token is required")
        viewer_user_id = await _resolve_user_id_from_token(token)
        if not viewer_user_id:
            raise HTTPException(status_code=401, detail="Invalid token")

        viewer_id = str(viewer_user_id)
        try:
            followed_owner_ids = await _fetch_followed_owner_ids(viewer_user_id=viewer_id, limit=5000)
        except Exception as exc:
            logger.warning("qna unread status follow-list load failed: %s", exc)
            followed_owner_ids = set()
        followed_owner_ids.discard(viewer_id)

        accessible_target_count = 1 + len(followed_owner_ids)
        self_has_unread = False
        following_has_unread = False

        try:
            self_unread = await _compute_qna_unread_for_target(
                viewer_user_id=viewer_id,
                target_user_id=viewer_id,
            )
            self_has_unread = bool(self_unread.has_unread)
        except Exception as exc:
            logger.warning("qna unread status self probe failed: %s", exc)

        if followed_owner_ids:
            for owner_user_id in sorted(followed_owner_ids):
                try:
                    owner_unread = await _compute_qna_unread_for_target(
                        viewer_user_id=viewer_id,
                        target_user_id=str(owner_user_id),
                    )
                except Exception as exc:
                    logger.warning(
                        "qna unread status probe failed for owner=%s: %s",
                        owner_user_id,
                        exc,
                    )
                    continue
                if bool(owner_unread.has_unread):
                    following_has_unread = True
                    break

        return QnaUnreadStatusResponse(
            status="ok",
            viewer_user_id=viewer_id,
            scope="accessible",
            accessible_target_count=int(accessible_target_count),
            self_has_unread=bool(self_has_unread),
            following_has_unread=bool(following_has_unread),
            has_unread=bool(self_has_unread or following_has_unread),
        )

    @app.get("/mymodel/qna/detail", response_model=QnaDetailResponse)
    async def qna_detail(
        q_instance_id: str = Query(..., description="<target_user_id>:<question_id> or reflection:<uuid>"),
        authorization: Optional[str] = Header(default=None, alias="Authorization"),
    ) -> QnaDetailResponse:
        token = _extract_bearer_token(authorization) if authorization else None
        if not token:
            raise HTTPException(status_code=401, detail="Authorization header with Bearer token is required")
        viewer_user_id = await _resolve_user_id_from_token(token)
        if not viewer_user_id:
            raise HTTPException(status_code=401, detail="Invalid token")

        iid = str(q_instance_id or "").strip()
        if _is_generated_reflection_instance_id(iid):
            row = await _resolve_generated_reflection_access(viewer_user_id=viewer_user_id, q_instance_id=iid)
            qk = _build_generated_q_key(row)
            metrics = await _fetch_instance_metrics({iid})
            m = metrics.get(iid) or {}
            try:
                views = int(m.get("views") or 0)
            except Exception:
                views = 0
            try:
                resonances = int(m.get("resonances") or 0)
            except Exception:
                resonances = 0
            discoveries = 0
            try:
                discoveries = await _sb_count_rows(f"/rest/v1/{DISCOVERY_LOGS_TABLE}", params={"q_instance_id": f"eq.{iid}"})
            except Exception as exc:
                logger.warning("discoveries count failed (detail/generated): %s", exc)
            read_set = await _fetch_reads(viewer_user_id, {iid})
            is_new = iid not in read_set
            is_resonated = await _is_resonated(viewer_user_id, iid)
            return QnaDetailResponse(
                title=str((row or {}).get("question") or "").strip(),
                body=str((row or {}).get("answer") or "").strip(),
                q_key=qk,
                q_instance_id=iid,
                views=views,
                resonances=resonances,
                discoveries=int(discoveries or 0),
                is_new=is_new,
                is_resonated=bool(is_resonated),
            )

        # legacy create path
        try:
            tgt, qid = _parse_instance_id(iid)
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid q_instance_id")
        if tgt != viewer_user_id:
            allowed = await _has_myprofile_link(viewer_user_id=viewer_user_id, owner_user_id=tgt)
            if not allowed:
                raise HTTPException(status_code=403, detail="You are not allowed to query this MyProfile")
        _, _, _, effective_tier = await _resolve_tiers(viewer_user_id=viewer_user_id, target_user_id=tgt)
        qrows = await _fetch_create_questions(build_tier=effective_tier)
        qmap = {int(r.get("id")): str(r.get("question_text") or "").strip() for r in (qrows or []) if r.get("id") is not None}
        title = qmap.get(int(qid))
        if not title:
            raise HTTPException(status_code=404, detail="Question not found")
        answers = await _fetch_create_answers(user_id=tgt, question_ids={int(qid)})
        a = answers.get(int(qid)) or {}
        body = _public_create_body_from_answer_row(a)
        if not body:
            raise HTTPException(status_code=404, detail="Answer not found")
        qk = _q_key_for_question_id(int(qid))
        metrics = await _fetch_instance_metrics({iid})
        m = metrics.get(iid) or {}
        try:
            views = int(m.get("views") or 0)
        except Exception:
            views = 0
        try:
            resonances = int(m.get("resonances") or 0)
        except Exception:
            resonances = 0
        discoveries = 0
        try:
            discoveries = await _sb_count_rows(f"/rest/v1/{DISCOVERY_LOGS_TABLE}", params={"q_instance_id": f"eq.{iid}"})
        except Exception as exc:
            logger.warning("discoveries count failed (detail): %s", exc)
        read_set = await _fetch_reads(viewer_user_id, {iid})
        is_new = iid not in read_set
        is_resonated = await _is_resonated(viewer_user_id, iid)
        return QnaDetailResponse(title=title, body=body, q_key=qk, q_instance_id=iid, views=views, resonances=resonances, discoveries=int(discoveries or 0), is_new=is_new, is_resonated=bool(is_resonated))

    @app.post("/mymodel/qna/view", response_model=QnaViewResponse)
    async def qna_view(
        req: QnaViewRequest,
        authorization: Optional[str] = Header(default=None, alias="Authorization"),
    ) -> QnaViewResponse:
        token = _extract_bearer_token(authorization) if authorization else None
        if not token:
            raise HTTPException(status_code=401, detail="Authorization header with Bearer token is required")
        viewer_user_id = await _resolve_user_id_from_token(token)
        if not viewer_user_id:
            raise HTTPException(status_code=401, detail="Invalid token")

        ctx = await _resolve_qna_context_for_reaction(viewer_user_id=viewer_user_id, q_instance_id=req.q_instance_id, q_key=req.q_key)
        tgt = str(ctx.get("target_user_id") or "")
        qid = int(ctx.get("question_id") or 0)
        qk = str(ctx.get("q_key") or "")
        iid = str(req.q_instance_id or "").strip()
        await _upsert_read(viewer_user_id, iid)

        if tgt == viewer_user_id:
            metrics = await _fetch_instance_metrics({iid})
            m = metrics.get(iid) or {}
            try:
                views = int(m.get("views") or 0)
            except Exception:
                views = 0
            try:
                resonances = int(m.get("resonances") or 0)
            except Exception:
                resonances = 0
            return QnaViewResponse(status="self", q_key=qk, q_instance_id=iid, views=views, resonances=resonances, is_new=False)

        if qid > 0:
            await _insert_view_log(target_user_id=tgt, viewer_user_id=viewer_user_id, question_id=int(qid), q_key=qk, q_instance_id=iid)
        counts = await _inc_metric(q_key=qk, q_instance_id=iid, field="views", delta=1)
        requested_at = _now_iso()
        try:
            await enqueue_ranking_board_refresh(
                metric_key="mymodel_views",
                user_id=viewer_user_id,
                trigger="qna_view",
                requested_at=requested_at,
                debounce=True,
            )
        except Exception as exc:
            logger.warning("ranking enqueue failed (qna_view): %s", exc)
        try:
            await enqueue_account_status_refresh(
                target_user_id=tgt,
                actor_user_id=viewer_user_id,
                trigger="qna_view",
                requested_at=requested_at,
                debounce=True,
            )
        except Exception as exc:
            logger.warning("account status enqueue failed (qna_view): %s", exc)
        try:
            await enqueue_global_summary_refresh(
                trigger="qna_view",
                requested_at=requested_at,
                actor_user_id=viewer_user_id,
                debounce=True,
            )
        except Exception as exc:
            logger.warning("global summary enqueue failed (qna_view): %s", exc)
        return QnaViewResponse(status="ok", q_key=qk, q_instance_id=iid, views=int(counts.get("views") or 0), resonances=int(counts.get("resonances") or 0), is_new=False)

    @app.post("/mymodel/qna/resonance", response_model=QnaResonanceResponse)
    async def qna_resonance(
        req: QnaResonanceRequest,
        authorization: Optional[str] = Header(default=None, alias="Authorization"),
    ) -> QnaResonanceResponse:
        token = _extract_bearer_token(authorization) if authorization else None
        if not token:
            raise HTTPException(status_code=401, detail="Authorization header with Bearer token is required")
        viewer_user_id = await _resolve_user_id_from_token(token)
        if not viewer_user_id:
            raise HTTPException(status_code=401, detail="Invalid token")

        ctx = await _resolve_qna_context_for_reaction(viewer_user_id=viewer_user_id, q_instance_id=req.q_instance_id, q_key=req.q_key)
        tgt = str(ctx.get("target_user_id") or "")
        qk = str(ctx.get("q_key") or "")
        iid = str(req.q_instance_id or "").strip()

        if tgt == viewer_user_id:
            metrics = await _fetch_instance_metrics({iid})
            m = metrics.get(iid) or {}
            try:
                views = int(m.get("views") or 0)
            except Exception:
                views = 0
            try:
                res_cnt = int(m.get("resonances") or 0)
            except Exception:
                res_cnt = 0
            return QnaResonanceResponse(status="self", q_key=qk, q_instance_id=iid, resonated=False, views=views, resonances=res_cnt)

        already = await _is_resonated(viewer_user_id, iid)
        metrics = await _fetch_instance_metrics({iid})
        m = metrics.get(iid) or {}
        try:
            views = int(m.get("views") or 0)
        except Exception:
            views = 0
        try:
            res_cnt = int(m.get("resonances") or 0)
        except Exception:
            res_cnt = 0
        return QnaResonanceResponse(status="already" if already else "noop", q_key=qk, q_instance_id=iid, resonated=bool(already), views=views, resonances=res_cnt)

    @app.get("/mymodel/qna/echoes/reflections", response_model=QnaSavedReflectionsResponse)
    async def qna_echoes_reflections(
        order: str = Query(default="newest", description="newest | oldest"),
        limit: int = Query(default=50, ge=1, le=200, description="Max items to return"),
        offset: int = Query(default=0, ge=0, description="Offset (best-effort)"),
        authorization: Optional[str] = Header(default=None, alias="Authorization"),
    ) -> QnaSavedReflectionsResponse:
        token = _extract_bearer_token(authorization) if authorization else None
        if not token:
            raise HTTPException(status_code=401, detail="Authorization header with Bearer token is required")
        viewer_user_id = await _resolve_user_id_from_token(token)
        if not viewer_user_id:
            raise HTTPException(status_code=401, detail="Invalid token")
        order_key = str(order or "newest").strip().lower()
        if order_key not in ("newest", "oldest"):
            order_key = "newest"
        sb_order = "created_at.desc" if order_key == "newest" else "created_at.asc"
        viewer_tier = SubscriptionTier.FREE
        try:
            viewer_tier = await get_subscription_tier_for_user(viewer_user_id, default=SubscriptionTier.FREE)
        except Exception:
            viewer_tier = SubscriptionTier.FREE
        retention = history_retention_bounds_for_query(str(viewer_tier.value), now_utc=datetime.now(timezone.utc))
        followed_set = await _fetch_followed_owner_ids(viewer_user_id=str(viewer_user_id))
        if not followed_set:
            return QnaSavedReflectionsResponse(status="ok", order=order_key, total_items=0, limit=int(limit), offset=int(offset), items=[])
        scan_limit = int(min(max(int(limit) * 5, 50), 2000))
        params: Dict[str, str] = {
            "select": "q_instance_id,q_key,question_id,target_user_id,created_at",
            "viewer_user_id": f"eq.{viewer_user_id}",
            "order": sb_order,
            "limit": str(scan_limit),
            "offset": str(int(offset)),
        }
        clauses: List[str] = []
        gte_iso = str(retention.get("gte_iso") or "").strip()
        lt_iso = str(retention.get("lt_iso") or "").strip()
        if gte_iso:
            clauses.append(f"created_at.gte.{gte_iso}")
        if lt_iso:
            clauses.append(f"created_at.lt.{lt_iso}")
        if clauses:
            params["and"] = f"({','.join(clauses)})"
        rows = await _sb_get_json_local(f"/rest/v1/{ECHOES_TABLE}", params=params)
        if not rows:
            return QnaSavedReflectionsResponse(status="ok", order=order_key, total_items=0, limit=int(limit), offset=int(offset), items=[])
        picked: List[Dict[str, Any]] = []
        seen_iids: Set[str] = set()
        for r in rows:
            iid = str((r or {}).get("q_instance_id") or "").strip()
            if not iid or iid in seen_iids:
                continue
            seen_iids.add(iid)
            picked.append(r)
            if len(picked) >= int(limit):
                break

        generated_prepared: List[Tuple[str, str, str]] = []
        create_prepared: List[Tuple[str, str, int, str, str]] = []
        for r in picked:
            iid = str((r or {}).get("q_instance_id") or "").strip()
            tgt = str((r or {}).get("target_user_id") or "").strip()
            saved_at = str((r or {}).get("created_at") or "").strip()
            if not iid or not tgt or not saved_at or tgt not in followed_set:
                continue
            if _is_generated_reflection_instance_id(iid):
                generated_prepared.append((iid, tgt, saved_at))
                continue
            qid_val = None
            try:
                qid_val = int((r or {}).get("question_id") or 0)
            except Exception:
                qid_val = None
            if not qid_val:
                try:
                    _, qid2 = _parse_instance_id(iid)
                    qid_val = int(qid2)
                except Exception:
                    qid_val = None
            if not qid_val:
                continue
            qk = str((r or {}).get("q_key") or "").strip() or _q_key_for_question_id(int(qid_val))
            create_prepared.append((iid, tgt, int(qid_val), qk, saved_at))

        create_items = await _build_saved_create_items(prepared_rows=create_prepared)
        generated_items = await _build_saved_generated_items(prepared_rows=generated_prepared)
        items = [*generated_items, *create_items]
        items.sort(key=lambda x: x.saved_at, reverse=(order_key == "newest"))
        return QnaSavedReflectionsResponse(status="ok", order=order_key, total_items=len(items), limit=int(limit), offset=int(offset), items=items)

    @app.post("/mymodel/qna/echoes/submit", response_model=QnaEchoesSubmitResponse)
    async def qna_echoes_submit(
        req: QnaEchoesSubmitRequest,
        authorization: Optional[str] = Header(default=None, alias="Authorization"),
    ) -> QnaEchoesSubmitResponse:
        token = _extract_bearer_token(authorization) if authorization else None
        if not token:
            raise HTTPException(status_code=401, detail="Authorization header with Bearer token is required")
        viewer_user_id = await _resolve_user_id_from_token(token)
        if not viewer_user_id:
            raise HTTPException(status_code=401, detail="Invalid token")
        ctx = await _resolve_qna_context_for_reaction(viewer_user_id=viewer_user_id, q_instance_id=req.q_instance_id, q_key=req.q_key)
        tgt = str(ctx.get("target_user_id") or "")
        qid = int(ctx.get("question_id") or 0)
        qk = str(ctx.get("q_key") or "")
        iid = str(req.q_instance_id or "").strip()
        if tgt == viewer_user_id:
            raise HTTPException(status_code=400, detail="Self echoes is not allowed")
        strength = str(req.strength or "").strip().lower()
        if strength not in ("small", "medium", "large"):
            raise HTTPException(status_code=400, detail="Invalid strength (small|medium|large)")
        memo = None
        if req.memo is not None:
            memo = str(req.memo)
            if len(memo) > 2000:
                raise HTTPException(status_code=400, detail="Memo too long")
            if not memo.strip():
                memo = None
        requested_at = _now_iso()
        payload = {
            "viewer_user_id": str(viewer_user_id),
            "target_user_id": str(tgt),
            "question_id": int(qid),
            "q_key": str(qk),
            "q_instance_id": iid,
            "strength": strength,
            "memo": memo,
            "context_source_type": ctx.get("context_source_type"),
            "context_question": ctx.get("context_question"),
            "context_answer": ctx.get("context_answer"),
            "context_topic_key": ctx.get("context_topic_key"),
            "context_category": ctx.get("context_category"),
            "created_at": requested_at,
        }
        resp = await _sb_post(f"/rest/v1/{ECHOES_TABLE}", json=payload, prefer="resolution=merge-duplicates,return=minimal")
        if resp.status_code >= 300:
            logger.error("Supabase %s upsert failed: %s %s", ECHOES_TABLE, resp.status_code, (resp.text or "")[:800])
            raise HTTPException(status_code=502, detail="Failed to submit echoes")
        resonated = await _is_resonated(viewer_user_id, iid)
        views = 0
        res_cnt = 0
        if not resonated:
            payload_res = {"viewer_user_id": str(viewer_user_id), "q_instance_id": iid, "q_key": str(qk), "created_at": _now_iso()}
            resp2 = await _sb_post(f"/rest/v1/{RESONANCES_TABLE}", json=payload_res, prefer="resolution=merge-duplicates,return=minimal")
            if resp2.status_code >= 300:
                logger.error("Supabase %s insert failed (echoes->resonance): %s %s", RESONANCES_TABLE, resp2.status_code, (resp2.text or "")[:800])
                raise HTTPException(status_code=502, detail="Failed to confirm resonance")
            if qid > 0:
                await _insert_resonance_log(target_user_id=tgt, viewer_user_id=viewer_user_id, question_id=int(qid), q_key=qk, q_instance_id=iid)
            counts = await _inc_metric(q_key=qk, q_instance_id=iid, field="resonances", delta=1)
            views = int(counts.get("views") or 0)
            res_cnt = int(counts.get("resonances") or 0)
            resonated = True
        else:
            metrics = await _fetch_instance_metrics({iid})
            m = metrics.get(iid) or {}
            try:
                views = int(m.get("views") or 0)
            except Exception:
                views = 0
            try:
                res_cnt = int(m.get("resonances") or 0)
            except Exception:
                res_cnt = 0
        try:
            await enqueue_global_snapshot_refresh(
                user_id=viewer_user_id,
                trigger="qna_echoes_submit",
                requested_at=requested_at,
                debounce=True,
            )
        except Exception as exc:
            logger.warning("snapshot enqueue failed (qna_echoes_submit): %s", exc)
        try:
            await enqueue_ranking_board_refresh(
                metric_key="mymodel_resonances",
                user_id=viewer_user_id,
                trigger="qna_echoes_submit",
                requested_at=requested_at,
                debounce=True,
            )
        except Exception as exc:
            logger.warning("ranking enqueue failed (qna_echoes_submit): %s", exc)
        try:
            await enqueue_account_status_refresh(
                target_user_id=tgt,
                actor_user_id=viewer_user_id,
                trigger="qna_echoes_submit",
                requested_at=requested_at,
                debounce=True,
            )
        except Exception as exc:
            logger.warning("account status enqueue failed (qna_echoes_submit): %s", exc)
        try:
            await enqueue_global_summary_refresh(
                trigger="qna_echoes_submit",
                requested_at=requested_at,
                actor_user_id=viewer_user_id,
                debounce=True,
            )
        except Exception as exc:
            logger.warning("global summary enqueue failed (qna_echoes_submit): %s", exc)
        return QnaEchoesSubmitResponse(status="ok", q_key=qk, q_instance_id=iid, strength=strength, memo=memo, resonated=bool(resonated), views=int(views or 0), resonances=int(res_cnt or 0))

    @app.post("/mymodel/qna/echoes/delete", response_model=QnaEchoesDeleteResponse)
    async def qna_echoes_delete(
        req: QnaEchoesDeleteRequest,
        authorization: Optional[str] = Header(default=None, alias="Authorization"),
    ) -> QnaEchoesDeleteResponse:
        token = _extract_bearer_token(authorization) if authorization else None
        if not token:
            raise HTTPException(status_code=401, detail="Authorization header with Bearer token is required")
        viewer_user_id = await _resolve_user_id_from_token(token)
        if not viewer_user_id:
            raise HTTPException(status_code=401, detail="Invalid token")
        ctx = await _resolve_qna_context_for_reaction(viewer_user_id=viewer_user_id, q_instance_id=req.q_instance_id, q_key=req.q_key)
        tgt = str(ctx.get("target_user_id") or "")
        qk = str(ctx.get("q_key") or "")
        iid = str(req.q_instance_id or "").strip()
        if tgt == viewer_user_id:
            raise HTTPException(status_code=400, detail="Self echoes is not allowed")
        resp_del = await _sb_delete(
            f"/rest/v1/{ECHOES_TABLE}",
            params={
                "viewer_user_id": f"eq.{viewer_user_id}",
                "q_instance_id": f"eq.{iid}",
                "select": "created_at",
            },
            prefer="return=representation",
        )
        if resp_del.status_code >= 300:
            logger.error("Supabase %s delete failed (echoes): %s %s", ECHOES_TABLE, resp_del.status_code, (resp_del.text or "")[:800])
            raise HTTPException(status_code=502, detail="Failed to delete echoes")
        deleted_echo_activity_dates: List[str] = []
        try:
            deleted_rows = resp_del.json()
        except Exception:
            deleted_rows = []
        if isinstance(deleted_rows, list):
            for row in deleted_rows:
                if not isinstance(row, dict):
                    continue
                deleted_created_at = str(row.get("created_at") or "").strip()
                if deleted_created_at:
                    deleted_echo_activity_dates.append(deleted_created_at)
        was_resonated = await _is_resonated(viewer_user_id, iid)
        resp_del2 = await _sb_delete(f"/rest/v1/{RESONANCES_TABLE}", params={"viewer_user_id": f"eq.{viewer_user_id}", "q_instance_id": f"eq.{iid}"}, prefer="return=minimal")
        if resp_del2.status_code >= 300:
            logger.error("Supabase %s delete failed (resonances): %s %s", RESONANCES_TABLE, resp_del2.status_code, (resp_del2.text or "")[:800])
            raise HTTPException(status_code=502, detail="Failed to delete resonance state")
        if was_resonated:
            counts = await _inc_metric(q_key=qk, q_instance_id=iid, field="resonances", delta=-1)
            views = int(counts.get("views") or 0)
            res_cnt = int(counts.get("resonances") or 0)
        else:
            metrics = await _fetch_instance_metrics({iid})
            m = metrics.get(iid) or {}
            try:
                views = int(m.get("views") or 0)
            except Exception:
                views = 0
            try:
                res_cnt = int(m.get("resonances") or 0)
            except Exception:
                res_cnt = 0
        requested_at = _now_iso()
        try:
            await enqueue_global_snapshot_refresh(
                user_id=viewer_user_id,
                trigger="qna_echoes_delete",
                requested_at=requested_at,
                debounce=True,
            )
        except Exception as exc:
            logger.warning("snapshot enqueue failed (qna_echoes_delete): %s", exc)
        try:
            await enqueue_ranking_board_refresh(
                metric_key="mymodel_resonances",
                user_id=viewer_user_id,
                trigger="qna_echoes_delete",
                requested_at=requested_at,
                debounce=True,
            )
        except Exception as exc:
            logger.warning("ranking enqueue failed (qna_echoes_delete): %s", exc)
        try:
            await enqueue_account_status_refresh(
                target_user_id=tgt,
                actor_user_id=viewer_user_id,
                trigger="qna_echoes_delete",
                requested_at=requested_at,
                debounce=True,
            )
        except Exception as exc:
            logger.warning("account status enqueue failed (qna_echoes_delete): %s", exc)
        try:
            if deleted_echo_activity_dates:
                await enqueue_global_summary_refresh_many(
                    activity_dates=deleted_echo_activity_dates,
                    trigger="qna_echoes_delete",
                    requested_at=requested_at,
                    actor_user_id=viewer_user_id,
                    debounce=True,
                )
            else:
                await enqueue_global_summary_refresh(
                    trigger="qna_echoes_delete",
                    requested_at=requested_at,
                    actor_user_id=viewer_user_id,
                    debounce=True,
                )
        except Exception as exc:
            logger.warning("global summary enqueue failed (qna_echoes_delete): %s", exc)
        return QnaEchoesDeleteResponse(status="ok", q_key=qk, q_instance_id=iid, resonated=False, views=int(views or 0), resonances=int(res_cnt or 0))

    @app.get("/mymodel/qna/echoes/history", response_model=QnaEchoesHistoryResponse)
    async def qna_echoes_history(
        q_instance_id: str = Query(..., description="<target_user_id>:<question_id> or reflection:<uuid>"),
        q_key: Optional[str] = Query(default=None, description="Optional; derived if omitted"),
        limit: Optional[int] = Query(default=None, description="Max items to return"),
        offset: Optional[int] = Query(default=None, description="Offset"),
        authorization: Optional[str] = Header(default=None, alias="Authorization"),
    ) -> QnaEchoesHistoryResponse:
        token = _extract_bearer_token(authorization) if authorization else None
        if not token:
            raise HTTPException(status_code=401, detail="Authorization header with Bearer token is required")
        viewer_user_id = await _resolve_user_id_from_token(token)
        if not viewer_user_id:
            raise HTTPException(status_code=401, detail="Invalid token")
        ctx = await _resolve_qna_context_for_reaction(viewer_user_id=viewer_user_id, q_instance_id=q_instance_id, q_key=q_key)
        qk = str(ctx.get("q_key") or "")
        iid = str(q_instance_id or "").strip()
        viewer_tier = SubscriptionTier.FREE
        try:
            viewer_tier = await get_subscription_tier_for_user(viewer_user_id, default=SubscriptionTier.FREE)
        except Exception as exc:
            logger.warning("viewer subscription tier resolve failed (echoes history): %s", exc)
            viewer_tier = SubscriptionTier.FREE
        tier_str = str(viewer_tier.value)
        retention = history_retention_bounds_for_query(tier_str, now_utc=datetime.now(timezone.utc))
        gte_iso = str(retention.get("gte_iso") or "").strip()
        lt_iso = str(retention.get("lt_iso") or "").strip()
        eff_limit = max(1, min(int(limit or 50), 1000))
        eff_offset = max(0, int(offset or 0))

        def _apply_created_at_retention(params: Dict[str, str]) -> Dict[str, str]:
            clauses: List[str] = []
            if gte_iso:
                clauses.append(f"created_at.gte.{gte_iso}")
            if lt_iso:
                clauses.append(f"created_at.lt.{lt_iso}")
            if clauses:
                params["and"] = f"({','.join(clauses)})"
            return params

        # Viewer must still have at least one Echoes save within the visible retention window.
        my_resp = await _sb_get(
            f"/rest/v1/{ECHOES_TABLE}",
            params=_apply_created_at_retention({
                "select": "strength,memo,created_at",
                "viewer_user_id": f"eq.{viewer_user_id}",
                "q_instance_id": f"eq.{iid}",
                "order": "created_at.desc",
                "limit": "1",
            }),
        )
        if my_resp.status_code >= 300:
            logger.error("Supabase %s select failed (my echoes history): %s %s", ECHOES_TABLE, my_resp.status_code, (my_resp.text or "")[:800])
            raise HTTPException(status_code=502, detail="Failed to load echoes history")
        my_rows = my_resp.json() if my_resp is not None else []
        if not isinstance(my_rows, list) or not my_rows:
            raise HTTPException(status_code=404, detail="Echoes history not found")
        row0 = my_rows[0] if isinstance(my_rows[0], dict) else {}
        my_strength = str((row0 or {}).get("strength") or "").strip() or None
        memo_raw = (row0 or {}).get("memo")
        my_memo = None if memo_raw is None else (str(memo_raw).strip() or None)

        total = await _sb_count_rows(
            f"/rest/v1/{ECHOES_TABLE}",
            params=_apply_created_at_retention({"q_instance_id": f"eq.{iid}"}),
        )
        cnt_small = await _sb_count_rows(
            f"/rest/v1/{ECHOES_TABLE}",
            params=_apply_created_at_retention({"q_instance_id": f"eq.{iid}", "strength": "eq.small"}),
        )
        cnt_medium = await _sb_count_rows(
            f"/rest/v1/{ECHOES_TABLE}",
            params=_apply_created_at_retention({"q_instance_id": f"eq.{iid}", "strength": "eq.medium"}),
        )
        cnt_large = await _sb_count_rows(
            f"/rest/v1/{ECHOES_TABLE}",
            params=_apply_created_at_retention({"q_instance_id": f"eq.{iid}", "strength": "eq.large"}),
        )
        resp = await _sb_get(
            f"/rest/v1/{ECHOES_TABLE}",
            params=_apply_created_at_retention({
                "select": "strength,created_at",
                "q_instance_id": f"eq.{iid}",
                "order": "created_at.desc",
                "limit": str(eff_limit + 1),
                "offset": str(eff_offset),
            }),
        )
        if resp.status_code >= 300:
            logger.error("Supabase %s select failed: %s %s", ECHOES_TABLE, resp.status_code, (resp.text or "")[:800])
            raise HTTPException(status_code=502, detail="Failed to load echoes history")
        rows = resp.json()
        items: List[QnaEchoesHistoryItem] = []
        if isinstance(rows, list):
            for r in rows[:eff_limit]:
                if not isinstance(r, dict):
                    continue
                st = str(r.get("strength") or "").strip()
                ca = str(r.get("created_at") or "").strip()
                if st and ca:
                    items.append(QnaEchoesHistoryItem(strength=st, created_at=ca))
        has_more = isinstance(rows, list) and len(rows) > eff_limit
        next_offset = (eff_offset + eff_limit) if has_more else None
        return QnaEchoesHistoryResponse(
            status="ok",
            q_key=qk,
            q_instance_id=iid,
            subscription_tier=tier_str,
            total=int(total or 0),
            count_small=int(cnt_small or 0),
            count_medium=int(cnt_medium or 0),
            count_large=int(cnt_large or 0),
            my_strength=my_strength,
            my_memo=my_memo,
            limit=int(eff_limit),
            offset=int(eff_offset),
            has_more=bool(has_more),
            next_offset=next_offset,
            retention_mode=str(retention.get("mode") or ""),
            is_limited=bool(tier_str != SubscriptionTier.PREMIUM.value),
            items=items,
        )

    @app.get("/mymodel/qna/discoveries/reflections", response_model=QnaSavedReflectionsResponse)
    async def qna_discoveries_reflections(
        order: str = Query(default="newest", description="newest | oldest"),
        limit: int = Query(default=50, ge=1, le=200, description="Max items to return"),
        offset: int = Query(default=0, ge=0, description="Offset (best-effort)"),
        authorization: Optional[str] = Header(default=None, alias="Authorization"),
    ) -> QnaSavedReflectionsResponse:
        token = _extract_bearer_token(authorization) if authorization else None
        if not token:
            raise HTTPException(status_code=401, detail="Authorization header with Bearer token is required")
        viewer_user_id = await _resolve_user_id_from_token(token)
        if not viewer_user_id:
            raise HTTPException(status_code=401, detail="Invalid token")
        order_key = str(order or "newest").strip().lower()
        if order_key not in ("newest", "oldest"):
            order_key = "newest"
        sb_order = "created_at.desc" if order_key == "newest" else "created_at.asc"
        viewer_tier = SubscriptionTier.FREE
        try:
            viewer_tier = await get_subscription_tier_for_user(viewer_user_id, default=SubscriptionTier.FREE)
        except Exception:
            viewer_tier = SubscriptionTier.FREE
        retention = history_retention_bounds_for_query(str(viewer_tier.value), now_utc=datetime.now(timezone.utc))
        followed_set = await _fetch_followed_owner_ids(viewer_user_id=str(viewer_user_id))
        if not followed_set:
            return QnaSavedReflectionsResponse(status="ok", order=order_key, total_items=0, limit=int(limit), offset=int(offset), items=[])
        scan_limit = int(min(max(int(limit) * 5, 50), 2000))
        params: Dict[str, str] = {
            "select": "q_instance_id,q_key,question_id,target_user_id,created_at",
            "viewer_user_id": f"eq.{viewer_user_id}",
            "order": sb_order,
            "limit": str(scan_limit),
            "offset": str(int(offset)),
        }
        clauses: List[str] = []
        gte_iso = str(retention.get("gte_iso") or "").strip()
        lt_iso = str(retention.get("lt_iso") or "").strip()
        if gte_iso:
            clauses.append(f"created_at.gte.{gte_iso}")
        if lt_iso:
            clauses.append(f"created_at.lt.{lt_iso}")
        if clauses:
            params["and"] = f"({','.join(clauses)})"
        rows = await _sb_get_json_local(f"/rest/v1/{DISCOVERY_LOGS_TABLE}", params=params)
        if not rows:
            return QnaSavedReflectionsResponse(status="ok", order=order_key, total_items=0, limit=int(limit), offset=int(offset), items=[])
        picked: List[Dict[str, Any]] = []
        seen_iids: Set[str] = set()
        for r in rows:
            iid = str((r or {}).get("q_instance_id") or "").strip()
            if not iid or iid in seen_iids:
                continue
            seen_iids.add(iid)
            picked.append(r)
            if len(picked) >= int(limit):
                break

        generated_prepared: List[Tuple[str, str, str]] = []
        create_prepared: List[Tuple[str, str, int, str, str]] = []
        for r in picked:
            iid = str((r or {}).get("q_instance_id") or "").strip()
            tgt = str((r or {}).get("target_user_id") or "").strip()
            saved_at = str((r or {}).get("created_at") or "").strip()
            if not iid or not tgt or not saved_at or tgt not in followed_set:
                continue
            if _is_generated_reflection_instance_id(iid):
                generated_prepared.append((iid, tgt, saved_at))
                continue
            qid_val = None
            try:
                qid_val = int((r or {}).get("question_id") or 0)
            except Exception:
                qid_val = None
            if not qid_val:
                try:
                    _, qid2 = _parse_instance_id(iid)
                    qid_val = int(qid2)
                except Exception:
                    qid_val = None
            if not qid_val:
                continue
            qk = str((r or {}).get("q_key") or "").strip() or _q_key_for_question_id(int(qid_val))
            create_prepared.append((iid, tgt, int(qid_val), qk, saved_at))

        create_items = await _build_saved_create_items(prepared_rows=create_prepared)
        generated_items = await _build_saved_generated_items(prepared_rows=generated_prepared)
        items = [*generated_items, *create_items]
        items.sort(key=lambda x: x.saved_at, reverse=(order_key == "newest"))
        return QnaSavedReflectionsResponse(status="ok", order=order_key, total_items=len(items), limit=int(limit), offset=int(offset), items=items)

    @app.post("/mymodel/qna/discoveries/submit", response_model=QnaDiscoverySubmitResponse)
    async def qna_discovery_submit(
        req: QnaDiscoverySubmitRequest,
        authorization: Optional[str] = Header(default=None, alias="Authorization"),
    ) -> QnaDiscoverySubmitResponse:
        token = _extract_bearer_token(authorization) if authorization else None
        if not token:
            raise HTTPException(status_code=401, detail="Authorization header with Bearer token is required")
        viewer_user_id = await _resolve_user_id_from_token(token)
        if not viewer_user_id:
            raise HTTPException(status_code=401, detail="Invalid token")
        ctx = await _resolve_qna_context_for_reaction(viewer_user_id=viewer_user_id, q_instance_id=req.q_instance_id, q_key=req.q_key)
        tgt = str(ctx.get("target_user_id") or "")
        qid = int(ctx.get("question_id") or 0)
        qk = str(ctx.get("q_key") or "")
        iid = str(req.q_instance_id or "").strip()
        if tgt == viewer_user_id:
            raise HTTPException(status_code=400, detail="Self discoveries is not allowed")
        category = str(req.category or "").strip()
        allowed_cats = {"new_perspective", "different_fun", "well_worded", "not_sorted", "shocked"}
        if category not in allowed_cats:
            raise HTTPException(status_code=400, detail="Invalid category")
        memo = None
        if req.memo is not None:
            memo = str(req.memo)
            if len(memo) > 2000:
                raise HTTPException(status_code=400, detail="Memo too long")
        requested_at = _now_iso()
        payload = {
            "viewer_user_id": str(viewer_user_id),
            "target_user_id": str(tgt),
            "question_id": int(qid),
            "q_key": str(qk),
            "q_instance_id": iid,
            "category": category,
            "memo": memo,
            "context_source_type": ctx.get("context_source_type"),
            "context_question": ctx.get("context_question"),
            "context_answer": ctx.get("context_answer"),
            "context_topic_key": ctx.get("context_topic_key"),
            "context_category": ctx.get("context_category"),
            "created_at": requested_at,
        }
        resp = await _sb_post(f"/rest/v1/{DISCOVERY_LOGS_TABLE}", json=payload, prefer="return=representation")
        if resp.status_code >= 300:
            logger.error("Supabase %s insert failed: %s %s", DISCOVERY_LOGS_TABLE, resp.status_code, (resp.text or "")[:800])
            raise HTTPException(status_code=502, detail="Failed to submit discovery")
        inserted_id = None
        try:
            data = resp.json()
            if isinstance(data, list) and data:
                inserted_id = str((data[0] or {}).get("id") or "").strip() or None
        except Exception:
            inserted_id = None
        try:
            await enqueue_global_snapshot_refresh(
                user_id=viewer_user_id,
                trigger="qna_discoveries_submit",
                requested_at=requested_at,
                debounce=True,
            )
        except Exception as exc:
            logger.warning("snapshot enqueue failed (qna_discoveries_submit): %s", exc)
        try:
            await enqueue_ranking_board_refresh(
                metric_key="mymodel_discoveries",
                user_id=viewer_user_id,
                trigger="qna_discoveries_submit",
                requested_at=requested_at,
                debounce=True,
            )
        except Exception as exc:
            logger.warning("ranking enqueue failed (qna_discoveries_submit): %s", exc)
        try:
            await enqueue_account_status_refresh(
                target_user_id=tgt,
                actor_user_id=viewer_user_id,
                trigger="qna_discoveries_submit",
                requested_at=requested_at,
                debounce=True,
            )
        except Exception as exc:
            logger.warning("account status enqueue failed (qna_discoveries_submit): %s", exc)
        try:
            await enqueue_global_summary_refresh(
                trigger="qna_discoveries_submit",
                requested_at=requested_at,
                actor_user_id=viewer_user_id,
                debounce=True,
            )
        except Exception as exc:
            logger.warning("global summary enqueue failed (qna_discoveries_submit): %s", exc)
        return QnaDiscoverySubmitResponse(status="ok", q_key=qk, q_instance_id=iid, id=inserted_id)

    @app.post("/mymodel/qna/discoveries/delete", response_model=QnaDiscoveryDeleteResponse)
    async def qna_discovery_delete(
        req: QnaDiscoveryDeleteRequest,
        authorization: Optional[str] = Header(default=None, alias="Authorization"),
    ) -> QnaDiscoveryDeleteResponse:
        token = _extract_bearer_token(authorization) if authorization else None
        if not token:
            raise HTTPException(status_code=401, detail="Authorization header with Bearer token is required")
        viewer_user_id = await _resolve_user_id_from_token(token)
        if not viewer_user_id:
            raise HTTPException(status_code=401, detail="Invalid token")
        ctx = await _resolve_qna_context_for_reaction(viewer_user_id=viewer_user_id, q_instance_id=req.q_instance_id, q_key=req.q_key)
        tgt = str(ctx.get("target_user_id") or "")
        qk = str(ctx.get("q_key") or "")
        iid = str(req.q_instance_id or "").strip()
        if tgt == viewer_user_id:
            raise HTTPException(status_code=400, detail="Self discoveries is not allowed")
        resp_del = await _sb_delete(
            f"/rest/v1/{DISCOVERY_LOGS_TABLE}",
            params={
                "viewer_user_id": f"eq.{viewer_user_id}",
                "q_instance_id": f"eq.{iid}",
                "select": "created_at",
            },
            prefer="return=representation",
        )
        if resp_del.status_code >= 300:
            logger.error("Supabase %s delete failed (discoveries): %s %s", DISCOVERY_LOGS_TABLE, resp_del.status_code, (resp_del.text or "")[:800])
            raise HTTPException(status_code=502, detail="Failed to delete discovery")
        deleted_discovery_activity_dates: List[str] = []
        try:
            deleted_rows = resp_del.json()
        except Exception:
            deleted_rows = []
        if isinstance(deleted_rows, list):
            for row in deleted_rows:
                if not isinstance(row, dict):
                    continue
                deleted_created_at = str(row.get("created_at") or "").strip()
                if deleted_created_at:
                    deleted_discovery_activity_dates.append(deleted_created_at)
        discoveries = 0
        try:
            discoveries = await _sb_count_rows(f"/rest/v1/{DISCOVERY_LOGS_TABLE}", params={"q_instance_id": f"eq.{iid}"})
        except Exception as exc:
            logger.warning("discoveries count failed (delete): %s", exc)
        requested_at = _now_iso()
        try:
            await enqueue_global_snapshot_refresh(
                user_id=viewer_user_id,
                trigger="qna_discoveries_delete",
                requested_at=requested_at,
                debounce=True,
            )
        except Exception as exc:
            logger.warning("snapshot enqueue failed (qna_discoveries_delete): %s", exc)
        try:
            await enqueue_ranking_board_refresh(
                metric_key="mymodel_discoveries",
                user_id=viewer_user_id,
                trigger="qna_discoveries_delete",
                requested_at=requested_at,
                debounce=True,
            )
        except Exception as exc:
            logger.warning("ranking enqueue failed (qna_discoveries_delete): %s", exc)
        try:
            await enqueue_account_status_refresh(
                target_user_id=tgt,
                actor_user_id=viewer_user_id,
                trigger="qna_discoveries_delete",
                requested_at=requested_at,
                debounce=True,
            )
        except Exception as exc:
            logger.warning("account status enqueue failed (qna_discoveries_delete): %s", exc)
        try:
            if deleted_discovery_activity_dates:
                await enqueue_global_summary_refresh_many(
                    activity_dates=deleted_discovery_activity_dates,
                    trigger="qna_discoveries_delete",
                    requested_at=requested_at,
                    actor_user_id=viewer_user_id,
                    debounce=True,
                )
            else:
                await enqueue_global_summary_refresh(
                    trigger="qna_discoveries_delete",
                    requested_at=requested_at,
                    actor_user_id=viewer_user_id,
                    debounce=True,
                )
        except Exception as exc:
            logger.warning("global summary enqueue failed (qna_discoveries_delete): %s", exc)
        return QnaDiscoveryDeleteResponse(status="ok", q_key=qk, q_instance_id=iid, discoveries=int(discoveries or 0))

    @app.get("/mymodel/qna/discoveries/history", response_model=QnaDiscoveryHistoryResponse)
    async def qna_discovery_history(
        q_instance_id: str = Query(..., description="<target_user_id>:<question_id> or reflection:<uuid>"),
        q_key: Optional[str] = Query(default=None, description="Optional; derived if omitted"),
        limit: Optional[int] = Query(default=None, description="Max items to return"),
        offset: Optional[int] = Query(default=None, description="Offset"),
        authorization: Optional[str] = Header(default=None, alias="Authorization"),
    ) -> QnaDiscoveryHistoryResponse:
        token = _extract_bearer_token(authorization) if authorization else None
        if not token:
            raise HTTPException(status_code=401, detail="Authorization header with Bearer token is required")
        viewer_user_id = await _resolve_user_id_from_token(token)
        if not viewer_user_id:
            raise HTTPException(status_code=401, detail="Invalid token")
        ctx = await _resolve_qna_context_for_reaction(viewer_user_id=viewer_user_id, q_instance_id=q_instance_id, q_key=q_key)
        qk = str(ctx.get("q_key") or "")
        iid = str(q_instance_id or "").strip()
        viewer_tier = SubscriptionTier.FREE
        try:
            viewer_tier = await get_subscription_tier_for_user(viewer_user_id, default=SubscriptionTier.FREE)
        except Exception as exc:
            logger.warning("viewer subscription tier resolve failed (discoveries history): %s", exc)
            viewer_tier = SubscriptionTier.FREE
        tier_str = str(viewer_tier.value)
        retention = history_retention_bounds_for_query(tier_str, now_utc=datetime.now(timezone.utc))
        gte_iso = str(retention.get("gte_iso") or "").strip()
        lt_iso = str(retention.get("lt_iso") or "").strip()
        eff_limit = max(1, min(int(limit or 50), 1000))
        eff_offset = max(0, int(offset or 0))

        def _apply_created_at_retention(params: Dict[str, str]) -> Dict[str, str]:
            clauses: List[str] = []
            if gte_iso:
                clauses.append(f"created_at.gte.{gte_iso}")
            if lt_iso:
                clauses.append(f"created_at.lt.{lt_iso}")
            if clauses:
                params["and"] = f"({','.join(clauses)})"
            return params

        my_total = await _sb_count_rows(
            f"/rest/v1/{DISCOVERY_LOGS_TABLE}",
            params=_apply_created_at_retention({
                "viewer_user_id": f"eq.{viewer_user_id}",
                "q_instance_id": f"eq.{iid}",
            }),
        )
        if int(my_total or 0) <= 0:
            raise HTTPException(status_code=404, detail="Discoveries history not found")

        resp = await _sb_get(
            f"/rest/v1/{DISCOVERY_LOGS_TABLE}",
            params=_apply_created_at_retention({
                "select": "id,category,memo,created_at",
                "viewer_user_id": f"eq.{viewer_user_id}",
                "q_instance_id": f"eq.{iid}",
                "order": "created_at.desc",
                "limit": str(eff_limit + 1),
                "offset": str(eff_offset),
            }),
        )
        if resp.status_code >= 300:
            logger.error("Supabase %s select failed: %s %s", DISCOVERY_LOGS_TABLE, resp.status_code, (resp.text or "")[:800])
            raise HTTPException(status_code=502, detail="Failed to load discoveries history")
        rows = resp.json()
        items: List[QnaDiscoveryHistoryItem] = []
        if isinstance(rows, list):
            for r in rows[:eff_limit]:
                if not isinstance(r, dict):
                    continue
                rid = str(r.get("id") or "").strip()
                if not rid:
                    continue
                cat = str(r.get("category") or "").strip()
                memo = r.get("memo")
                memo_s = None if memo is None else str(memo)
                ca = str(r.get("created_at") or "").strip()
                items.append(QnaDiscoveryHistoryItem(id=rid, category=cat, memo=memo_s, created_at=ca))
        has_more = isinstance(rows, list) and len(rows) > eff_limit
        next_offset = (eff_offset + eff_limit) if has_more else None
        return QnaDiscoveryHistoryResponse(
            status="ok",
            q_key=qk,
            q_instance_id=iid,
            subscription_tier=tier_str,
            total=int(my_total or 0),
            limit=int(eff_limit),
            offset=int(eff_offset),
            has_more=bool(has_more),
            next_offset=next_offset,
            retention_mode=str(retention.get("mode") or ""),
            is_limited=bool(tier_str != SubscriptionTier.PREMIUM.value),
            items=items,
        )

