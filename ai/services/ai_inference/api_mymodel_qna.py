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
- "body"  := mymodel_create_answers.answer_text (for the target user)

Popularity (views/resonances) is aggregated by q_key.
Unread ("New") is tracked per viewer x q_instance_id.
"""

from __future__ import annotations

import logging
import os
from datetime import datetime, timezone
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
from subscription import SubscriptionTier
from subscription_store import get_subscription_tier_for_user


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
    is_new: bool = False


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


# ----------------------------
# Supabase helpers
# ----------------------------


def _sb_headers_json(*, prefer: Optional[str] = None) -> Dict[str, str]:
    _ensure_supabase_config()
    h = {
        "apikey": SUPABASE_SERVICE_ROLE_KEY,
        "Authorization": f"Bearer {SUPABASE_SERVICE_ROLE_KEY}",
        "Content-Type": "application/json",
    }
    if prefer:
        h["Prefer"] = prefer
    return h


async def _sb_get(path: str, *, params: Optional[Dict[str, str]] = None) -> httpx.Response:
    _ensure_supabase_config()
    url = f"{SUPABASE_URL}{path}"
    async with httpx.AsyncClient(timeout=8.0) as client:
        return await client.get(url, headers=_sb_headers_json(), params=params)


async def _sb_post(path: str, *, json: Any, prefer: Optional[str] = None) -> httpx.Response:
    _ensure_supabase_config()
    url = f"{SUPABASE_URL}{path}"
    async with httpx.AsyncClient(timeout=8.0) as client:
        return await client.post(url, headers=_sb_headers_json(prefer=prefer), json=json)


async def _sb_patch(
    path: str, *, params: Dict[str, str], json: Any, prefer: Optional[str] = None
) -> httpx.Response:
    _ensure_supabase_config()
    url = f"{SUPABASE_URL}{path}"
    async with httpx.AsyncClient(timeout=8.0) as client:
        return await client.patch(url, headers=_sb_headers_json(prefer=prefer), params=params, json=json)


# ----------------------------
# Internal helpers
# ----------------------------


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _build_tier_for_subscription(tier: SubscriptionTier) -> str:
    return "light" if tier == SubscriptionTier.FREE else "standard"


def _view_tier_for_subscription(tier: SubscriptionTier) -> str:
    # Spec: Free => Light, Plus/Premium => Standard (Premium extra is TODO)
    return "light" if tier == SubscriptionTier.FREE else "standard"


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
    """Return user_id list (deduped, ordered) who answered the question."""
    qid = int(question_id)
    resp = await _sb_get(
        "/rest/v1/mymodel_create_answers",
        params={
            "select": "user_id,updated_at",
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


# ----------------------------
# Routes
# ----------------------------


def register_mymodel_qna_routes(app: FastAPI) -> None:
    """Register Q&A (new architecture) routes."""

    @app.get("/mymodel/qna/list", response_model=QnaListResponse)
    async def qna_list(
        target_user_id: Optional[str] = Query(default=None, description="Owner of the MyModel (defaults to viewer)"),
        sort: str = Query(default="newest", description="newest | popular"),
        metric: str = Query(default="views", description="views | resonances (only for popular)"),
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

        # Fetch Create questions (effective tier)
        try:
            qrows = await _fetch_create_questions(build_tier=effective_tier)
        except Exception as exc:
            logger.error("failed to fetch create questions: %s", exc)
            raise HTTPException(status_code=502, detail="Failed to load questions")

        question_ids: List[int] = []
        qtext: Dict[int, str] = {}
        for r in qrows or []:
            try:
                qid = int(r.get("id"))
            except Exception:
                continue
            txt = str(r.get("question_text") or "").strip()
            if not txt:
                continue
            question_ids.append(qid)
            qtext[qid] = txt

        if not question_ids:
            meta = QnaListMeta(
                viewer_user_id=viewer_user_id,
                target_user_id=tgt,
                subscription_tier=subscription_tier,
                view_tier=view_tier,
                build_tier=build_tier,
                effective_tier=effective_tier,
                total_items=0,
            )
            return QnaListResponse(items=[], meta=meta)

        # Fetch target answers
        answers = await _fetch_create_answers(user_id=tgt, question_ids=set(question_ids))

        # Only answered items (avoid blank experiences)
        items: List[QnaListItem] = []
        q_keys: Set[str] = set()
        q_instance_ids: Set[str] = set()

        for qid in question_ids:
            a = answers.get(qid)
            ans = str((a or {}).get("answer_text") or "").strip()
            if not ans:
                continue
            qk = _q_key_for_question_id(qid)
            qid2 = _instance_id_for_target_question(tgt, qid)
            q_keys.add(qk)
            q_instance_ids.add(qid2)
            generated_at = None
            try:
                generated_at = str((a or {}).get("updated_at") or "").strip() or None
            except Exception:
                generated_at = None
            items.append(
                QnaListItem(
                    title=qtext.get(qid, ""),
                    q_key=qk,
                    q_instance_id=qid2,
                    generated_at=generated_at,
                    views=0,
                    resonances=0,
                    is_new=False,
                )
            )

        metrics_map = await _fetch_instance_metrics(q_instance_ids)
        read_set = await _fetch_reads(viewer_user_id, q_instance_ids)

        # Attach metrics + new
        for it in items:
            m = metrics_map.get(it.q_instance_id) or {}
            try:
                it.views = int(m.get("views") or 0)
            except Exception:
                it.views = 0
            try:
                it.resonances = int(m.get("resonances") or 0)
            except Exception:
                it.resonances = 0
            it.is_new = it.q_instance_id not in read_set

        # Sort
        sort_key = str(sort or "newest").strip().lower()
        metric_key = str(metric or "views").strip().lower()

        if sort_key == "popular":
            if metric_key not in ("views", "resonances"):
                metric_key = "views"
            if metric_key == "resonances":
                items.sort(key=lambda x: (x.resonances, x.views, x.generated_at or ""), reverse=True)
            else:
                items.sort(key=lambda x: (x.views, x.resonances, x.generated_at or ""), reverse=True)
        else:
            items.sort(key=lambda x: (x.generated_at or ""), reverse=True)

        meta = QnaListMeta(
            viewer_user_id=viewer_user_id,
            target_user_id=tgt,
            subscription_tier=subscription_tier,
            view_tier=view_tier,
            build_tier=build_tier,
            effective_tier=effective_tier,
            total_items=len(items),
        )
        return QnaListResponse(items=items, meta=meta)


    @app.get("/mymodel/qna/trending", response_model=QnaTrendingResponse)
    async def qna_trending(
        limit: int = Query(default=5, ge=1, le=20, description="Number of trending questions to return"),
        authorization: Optional[str] = Header(default=None, alias="Authorization"),
    ) -> QnaTrendingResponse:
        """Return trending questions (global popularity by q_key).

        Notes:
        - Uses global metrics rows where q_instance_id IS NULL.
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

        # Fetch top global metrics and then filter to allowed q_keys.
        scan_limit = int(max(50, min(500, int(limit) * 25)))
        resp = await _sb_get(
            f"/rest/v1/{METRICS_TABLE}",
            params={
                "select": "q_key,views,resonances",
                "q_instance_id": "is.null",
                "order": "views.desc,resonances.desc",
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
        items: List[QnaTrendingItem] = []

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

                items.append(
                    QnaTrendingItem(
                        question_id=int(qid),
                        title=title,
                        q_key=qk,
                        views=views,
                        resonances=res_cnt,
                    )
                )
                if len(items) >= int(limit):
                    break

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

        holder_ids = await _fetch_holder_user_ids_for_question(question_id=int(question_id), scan_limit=scan_limit)

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
        body = str(a.get("answer_text") or "").strip()
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

        read_set = await _fetch_reads(viewer_user_id, {str(q_instance_id)})
        is_new = str(q_instance_id) not in read_set

        return QnaDetailResponse(
            title=title,
            body=body,
            q_key=qk,
            q_instance_id=str(q_instance_id),
            views=views,
            resonances=resonances,
            is_new=is_new,
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

        already = await _is_resonated(viewer_user_id, req.q_instance_id)
        if already:
            # Return current counts
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
                status="already",
                q_key=qk,
                q_instance_id=req.q_instance_id,
                resonated=False,
                views=views,
                resonances=res_cnt,
            )

        # Insert resonance record (best-effort). If insert fails, we still fail-soft.
        payload = {
            "viewer_user_id": str(viewer_user_id),
            "q_instance_id": str(req.q_instance_id),
            "q_key": str(qk),
            "created_at": _now_iso(),
        }
        resp = await _sb_post(
            f"/rest/v1/{RESONANCES_TABLE}",
            json=payload,
            prefer="resolution=merge-duplicates,return=minimal",
        )
        if resp.status_code >= 300:
            logger.warning("Supabase %s insert failed: %s %s", RESONANCES_TABLE, resp.status_code, resp.text[:800])

        counts = await _inc_metric(q_key=qk, q_instance_id=req.q_instance_id, field="resonances", delta=1)
        return QnaResonanceResponse(
            status="ok",
            q_key=qk,
            q_instance_id=req.q_instance_id,
            resonated=True,
            views=int(counts.get("views") or 0),
            resonances=int(counts.get("resonances") or 0),
        )
