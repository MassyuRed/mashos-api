from __future__ import annotations

import logging
import os
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Set

from fastapi import HTTPException

from supabase_client import (
    sb_delete as _sb_delete_shared,
    sb_get as _sb_get_shared,
    sb_patch as _sb_patch_shared,
    sb_post as _sb_post_shared,
)

logger = logging.getLogger("piece.public_read.store")

# Current bridge views are backend read-only. Read helpers use dedicated current-name
# view constants; write/upsert/log paths keep the legacy physical table constants.
METRICS_TABLE = os.getenv("COCOLON_MYMODEL_QNA_METRICS_TABLE", "mymodel_qna_metrics")
METRICS_READ_TABLE = (
    os.getenv("COCOLON_PIECE_METRICS_READ_TABLE")
    or os.getenv("COCOLON_MYMODEL_QNA_METRICS_READ_TABLE")
    or "piece_metrics"
).strip() or "piece_metrics"
READS_TABLE = os.getenv("COCOLON_MYMODEL_QNA_READS_TABLE", "mymodel_qna_reads")
READS_READ_TABLE = (
    os.getenv("COCOLON_PIECE_READS_READ_TABLE")
    or os.getenv("COCOLON_MYMODEL_QNA_READS_READ_TABLE")
    or "piece_reads"
).strip() or "piece_reads"
RESONANCES_TABLE = os.getenv("COCOLON_MYMODEL_QNA_RESONANCES_TABLE", "mymodel_qna_resonances")
ECHOES_TABLE = os.getenv("COCOLON_MYMODEL_QNA_ECHOES_TABLE", "mymodel_qna_echoes")
DISCOVERY_LOGS_TABLE = os.getenv(
    "COCOLON_MYMODEL_QNA_DISCOVERY_LOGS_TABLE", "mymodel_qna_discovery_logs"
)
VIEW_LOGS_TABLE = os.getenv("COCOLON_MYMODEL_QNA_VIEW_LOGS_TABLE", "mymodel_qna_view_logs")
RESONANCE_LOGS_TABLE = os.getenv(
    "COCOLON_MYMODEL_QNA_RESONANCE_LOGS_TABLE", "mymodel_qna_resonance_logs"
)
MYMODEL_REFLECTIONS_TABLE = (
    os.getenv("MYMODEL_REFLECTIONS_TABLE", "mymodel_reflections") or "mymodel_reflections"
).strip() or "mymodel_reflections"
MYMODEL_REFLECTIONS_READ_TABLE = (
    os.getenv("COCOLON_PIECES_READ_TABLE")
    or os.getenv("COCOLON_MYMODEL_REFLECTIONS_READ_TABLE")
    or os.getenv("MYMODEL_REFLECTIONS_READ_TABLE")
    or "pieces"
).strip() or "pieces"


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
            f"/rest/v1/{METRICS_READ_TABLE}",
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
            f"/rest/v1/{READS_READ_TABLE}",
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


async def fetch_resonated_instances(viewer_user_id: str, q_instance_ids: Set[str]) -> Set[str]:
    if not viewer_user_id or not q_instance_ids:
        return set()
    try:
        rows = await sb_get_json(
            f"/rest/v1/{RESONANCES_TABLE}",
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
        qid = str((r or {}).get("q_instance_id") or "").strip()
        if qid:
            out.add(qid)
    return out


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


async def _delete_by_q_instance_ids(table: str, q_instance_ids: Set[str]) -> bool:
    table_name = str(table or "").strip()
    ids = {str(value or "").strip() for value in (q_instance_ids or set()) if str(value or "").strip()}
    if not table_name or not ids:
        return True

    params = {
        "q_instance_id": (
            f"eq.{next(iter(ids))}" if len(ids) == 1 else quoted_in(ids)
        )
    }
    try:
        resp = await _sb_delete_shared(
            f"/rest/v1/{table_name}",
            params=params,
            prefer="return=minimal",
            timeout=8.0,
        )
    except Exception as exc:
        logger.warning("Supabase %s delete failed: %s", table_name, exc)
        return False
    if resp.status_code >= 300:
        logger.warning(
            "Supabase %s delete failed: %s %s",
            table_name,
            resp.status_code,
            (resp.text or "")[:800],
        )
        return False
    return True


async def delete_piece_related_state(q_instance_ids: Set[str]) -> Dict[str, List[str]]:
    ids = {str(value or "").strip() for value in (q_instance_ids or set()) if str(value or "").strip()}
    result: Dict[str, List[str]] = {"deleted": [], "failed": []}
    if not ids:
        return result

    for table_name in [
        READS_TABLE,
        RESONANCES_TABLE,
        ECHOES_TABLE,
        DISCOVERY_LOGS_TABLE,
        VIEW_LOGS_TABLE,
        RESONANCE_LOGS_TABLE,
        METRICS_TABLE,
    ]:
        ok = await _delete_by_q_instance_ids(table_name, ids)
        result["deleted" if ok else "failed"].append(str(table_name))
    return result


async def delete_generated_piece_row(
    *,
    row_id: str,
    owner_user_id: str,
    source_type: str = "emotion_generated",
) -> bool:
    rid = str(row_id or "").strip()
    owner_id = str(owner_user_id or "").strip()
    source = str(source_type or "emotion_generated").strip() or "emotion_generated"
    if not rid or not owner_id:
        return False

    resp = await _sb_delete_shared(
        f"/rest/v1/{MYMODEL_REFLECTIONS_TABLE}",
        params={
            "id": f"eq.{rid}",
            "owner_user_id": f"eq.{owner_id}",
            "source_type": f"eq.{source}",
        },
        prefer="return=representation",
        timeout=8.0,
    )
    if resp.status_code >= 300:
        logger.error(
            "Supabase %s delete failed: %s %s",
            MYMODEL_REFLECTIONS_TABLE,
            resp.status_code,
            (resp.text or "")[:1200],
        )
        raise HTTPException(status_code=502, detail="Failed to delete Piece")
    try:
        rows = resp.json()
    except Exception:
        rows = []
    return bool(isinstance(rows, list) and rows)


__all__ = [
    "METRICS_TABLE",
    "METRICS_READ_TABLE",
    "READS_TABLE",
    "READS_READ_TABLE",
    "RESONANCES_TABLE",
    "ECHOES_TABLE",
    "DISCOVERY_LOGS_TABLE",
    "VIEW_LOGS_TABLE",
    "RESONANCE_LOGS_TABLE",
    "MYMODEL_REFLECTIONS_TABLE",
    "MYMODEL_REFLECTIONS_READ_TABLE",
    "quoted_in",
    "sb_get",
    "sb_get_json",
    "has_myprofile_link",
    "fetch_profiles_by_ids",
    "fetch_followed_owner_ids",
    "fetch_instance_metrics",
    "fetch_reads",
    "fetch_resonated_instances",
    "is_resonated",
    "upsert_read",
    "insert_view_log",
    "inc_metric",
    "delete_generated_piece_row",
    "delete_piece_related_state",
]
