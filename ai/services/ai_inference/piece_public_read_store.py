from __future__ import annotations

import logging
import os
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Set

from fastapi import HTTPException

from supabase_client import (
    sb_get as _sb_get_shared,
    sb_patch as _sb_patch_shared,
    sb_post as _sb_post_shared,
)

logger = logging.getLogger("piece.public_read.store")

METRICS_TABLE = os.getenv("COCOLON_MYMODEL_QNA_METRICS_TABLE", "mymodel_qna_metrics")
READS_TABLE = os.getenv("COCOLON_MYMODEL_QNA_READS_TABLE", "mymodel_qna_reads")
RESONANCES_TABLE = os.getenv("COCOLON_MYMODEL_QNA_RESONANCES_TABLE", "mymodel_qna_resonances")
VIEW_LOGS_TABLE = os.getenv("COCOLON_MYMODEL_QNA_VIEW_LOGS_TABLE", "mymodel_qna_view_logs")
MYMODEL_REFLECTIONS_TABLE = (
    os.getenv("MYMODEL_REFLECTIONS_TABLE", "mymodel_reflections") or "mymodel_reflections"
).strip() or "mymodel_reflections"


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def quoted_in(values: Set[str]) -> str:
    vals = [str(v) for v in values if str(v).strip()]
    vals_sorted = sorted(vals)
    inner = ",".join([f'"{v}"' for v in vals_sorted])
    return f"in.({inner})"


async def sb_get(path: str, *, params: Optional[Dict[str, str]] = None):
    return await _sb_get_shared(path, params=params, timeout=8.0)


async def sb_get_json(path: str, *, params: Dict[str, str]) -> List[Dict[str, Any]]:
    resp = await sb_get(path, params=params)
    if resp.status_code >= 300:
        logger.error("Supabase GET failed: %s %s", resp.status_code, (resp.text or "")[:1200])
        raise HTTPException(status_code=502, detail="Failed to load Piece artifacts")
    try:
        data = resp.json()
    except Exception:
        return []
    if isinstance(data, list):
        return [x for x in data if isinstance(x, dict)]
    return []


async def has_myprofile_link(*, viewer_user_id: str, owner_user_id: str) -> bool:
    resp = await sb_get(
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
            (resp.text or "")[:1500],
        )
        raise HTTPException(status_code=502, detail="Failed to check myprofile link")
    rows = resp.json()
    return bool(isinstance(rows, list) and rows)


async def fetch_profiles_by_ids(user_ids: List[str]) -> Dict[str, Dict[str, Any]]:
    ids = [str(x).strip() for x in (user_ids or []) if str(x).strip()]
    if not ids:
        return {}
    out: Dict[str, Dict[str, Any]] = {}
    chunk_size = 200
    for i in range(0, len(ids), chunk_size):
        chunk = ids[i : i + chunk_size]
        rows = await sb_get_json(
            "/rest/v1/profiles",
            params={
                "select": "id,display_name,friend_code,myprofile_code",
                "id": quoted_in(set(chunk)),
                "limit": str(len(chunk)),
            },
        )
        for r in rows:
            if isinstance(r, dict) and r.get("id") is not None:
                out[str(r.get("id"))] = r
    return out


async def fetch_followed_owner_ids(*, viewer_user_id: str, limit: int = 5000) -> Set[str]:
    if not viewer_user_id:
        return set()
    try:
        rows = await sb_get_json(
            "/rest/v1/myprofile_links",
            params={
                "select": "owner_user_id",
                "viewer_user_id": f"eq.{viewer_user_id}",
                "limit": str(int(limit)),
            },
        )
    except Exception:
        return set()
    out: Set[str] = set()
    for r in rows:
        oid = str((r or {}).get("owner_user_id") or "").strip()
        if oid:
            out.add(oid)
    return out


async def fetch_instance_metrics(q_instance_ids: Set[str]) -> Dict[str, Dict[str, Any]]:
    if not q_instance_ids:
        return {}
    try:
        rows = await sb_get_json(
            f"/rest/v1/{METRICS_TABLE}",
            params={
                "select": "q_instance_id,q_key,views,resonances",
                "q_instance_id": quoted_in(set(q_instance_ids)),
                "limit": str(max(1, len(q_instance_ids))),
            },
        )
    except Exception:
        return {}
    out: Dict[str, Dict[str, Any]] = {}
    for r in rows:
        iid = str(r.get("q_instance_id") or "").strip()
        if iid:
            out[iid] = r
    return out


async def fetch_reads(viewer_user_id: str, q_instance_ids: Set[str]) -> Set[str]:
    if not viewer_user_id or not q_instance_ids:
        return set()
    try:
        rows = await sb_get_json(
            f"/rest/v1/{READS_TABLE}",
            params={
                "select": "q_instance_id",
                "viewer_user_id": f"eq.{viewer_user_id}",
                "q_instance_id": quoted_in(set(q_instance_ids)),
                "limit": str(max(1, len(q_instance_ids))),
            },
        )
    except Exception:
        return set()
    out: Set[str] = set()
    for r in rows:
        qid = str(r.get("q_instance_id") or "").strip()
        if qid:
            out.add(qid)
    return out


async def is_resonated(viewer_user_id: str, q_instance_id: str) -> bool:
    if not viewer_user_id or not q_instance_id:
        return False
    resp = await sb_get(
        f"/rest/v1/{RESONANCES_TABLE}",
        params={
            "select": "viewer_user_id",
            "viewer_user_id": f"eq.{viewer_user_id}",
            "q_instance_id": f"eq.{q_instance_id}",
            "limit": "1",
        },
    )
    if resp.status_code >= 300:
        logger.error("Supabase %s select failed: %s %s", RESONANCES_TABLE, resp.status_code, (resp.text or "")[:800])
        return False
    rows = resp.json()
    return bool(isinstance(rows, list) and rows)


async def upsert_read(viewer_user_id: str, q_instance_id: str) -> None:
    if not viewer_user_id or not q_instance_id:
        return
    payload = {
        "viewer_user_id": str(viewer_user_id),
        "q_instance_id": str(q_instance_id),
        "viewed_at": _now_iso(),
    }
    resp = await _sb_post_shared(
        f"/rest/v1/{READS_TABLE}",
        json=payload,
        prefer="resolution=merge-duplicates,return=minimal",
    )
    if resp.status_code >= 300:
        logger.warning("Supabase %s upsert failed: %s %s", READS_TABLE, resp.status_code, (resp.text or "")[:800])


async def insert_view_log(*, target_user_id: str, viewer_user_id: str, question_id: int, q_key: str, q_instance_id: str) -> None:
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
        resp = await _sb_post_shared(
            f"/rest/v1/{VIEW_LOGS_TABLE}",
            json=payload,
            prefer="return=minimal",
        )
        if resp.status_code >= 300:
            logger.warning("Supabase %s insert failed: %s %s", VIEW_LOGS_TABLE, resp.status_code, (resp.text or "")[:800])
    except Exception as exc:
        logger.warning("Supabase %s insert failed: %s", VIEW_LOGS_TABLE, exc)


async def inc_metric(*, q_key: str, q_instance_id: Optional[str] = None, field: str, delta: int = 1) -> Dict[str, int]:
    kk = str(q_key or "").strip()
    iid = str(q_instance_id or "").strip() or None
    if not kk:
        return {"views": 0, "resonances": 0}
    if field not in ("views", "resonances"):
        raise ValueError("invalid metric field")

    async def _inc_one(*, iid_filter: Optional[str]) -> Dict[str, int]:
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
            resp = await sb_get(f"/rest/v1/{METRICS_TABLE}", params=params_get)
            if resp.status_code < 300:
                rows = resp.json()
                if isinstance(rows, list) and rows:
                    exists = True
                    cur_views = int((rows[0] or {}).get("views") or 0)
                    cur_res = int((rows[0] or {}).get("resonances") or 0)
        except Exception as exc:
            logger.warning("Supabase %s select failed (metrics inc): %s", METRICS_TABLE, exc)
        if field == "views":
            cur_views += int(delta)
        else:
            cur_res += int(delta)
        cur_views = max(cur_views, 0)
        cur_res = max(cur_res, 0)
        params_patch = {"q_key": f"eq.{kk}"}
        if iid_filter is None:
            params_patch["q_instance_id"] = "is.null"
        else:
            params_patch["q_instance_id"] = f"eq.{iid_filter}"
        if exists:
            try:
                resp2 = await _sb_patch_shared(
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
                    logger.warning("Supabase %s patch failed: %s %s", METRICS_TABLE, resp2.status_code, (resp2.text or "")[:800])
            except Exception as exc:
                logger.warning("Supabase %s patch failed (metrics inc): %s", METRICS_TABLE, exc)
        else:
            try:
                resp3 = await _sb_post_shared(
                    f"/rest/v1/{METRICS_TABLE}",
                    json={
                        "q_key": kk,
                        "q_instance_id": iid_filter,
                        "views": cur_views,
                        "resonances": cur_res,
                        "updated_at": _now_iso(),
                    },
                    prefer="return=minimal",
                )
                if resp3.status_code >= 300:
                    logger.warning("Supabase %s insert failed: %s %s", METRICS_TABLE, resp3.status_code, (resp3.text or "")[:800])
            except Exception as exc:
                logger.warning("Supabase %s insert failed (metrics inc): %s", METRICS_TABLE, exc)
        return {"views": cur_views, "resonances": cur_res}

    instance_counts: Optional[Dict[str, int]] = None
    if iid is not None:
        instance_counts = await _inc_one(iid_filter=iid)
    global_counts = await _inc_one(iid_filter=None)
    if instance_counts is None:
        return {"views": int(global_counts.get("views") or 0), "resonances": int(global_counts.get("resonances") or 0)}
    return {
        "views": int(instance_counts.get("views") or 0),
        "resonances": int(instance_counts.get("resonances") or 0),
        "global_views": int(global_counts.get("views") or 0),
        "global_resonances": int(global_counts.get("resonances") or 0),
    }


__all__ = [
    "METRICS_TABLE",
    "MYMODEL_REFLECTIONS_TABLE",
    "quoted_in",
    "sb_get",
    "sb_get_json",
    "has_myprofile_link",
    "fetch_profiles_by_ids",
    "fetch_followed_owner_ids",
    "fetch_instance_metrics",
    "fetch_reads",
    "is_resonated",
    "upsert_read",
    "insert_view_log",
    "inc_metric",
]
