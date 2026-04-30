from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Set, Tuple

from fastapi import HTTPException

from access_policy.viewer_access_policy import resolve_piece_view_tiers
from astor_account_status_enqueue import enqueue_account_status_refresh
from astor_global_summary_enqueue import enqueue_global_summary_refresh
from astor_ranking_enqueue import enqueue_ranking_board_refresh
from piece_generated_display import get_public_generated_reflection_text
from piece_generated_access import (
    EMOTION_GENERATED_SOURCE_TYPE,
    build_generated_q_key,
    fetch_active_emotion_generated_reflections_for_owner,
    generated_public_id,
    generated_row_sort_key,
    is_generated_reflection_instance_id,
    resolve_generated_reflection_access,
)
from piece_public_read_store import (
    fetch_followed_owner_ids,
    fetch_instance_metrics,
    fetch_profiles_by_ids,
    fetch_reads,
    fetch_resonated_instances,
    has_myprofile_link,
    inc_metric,
    is_resonated,
    upsert_read,
)


def _dump_model(model: Any) -> Any:
    if hasattr(model, "model_dump"):
        return model.model_dump()
    if hasattr(model, "dict"):
        return model.dict()
    return model


def _normalize_public_sort(raw_sort: str) -> str:
    mode = str(raw_sort or "latest").strip().lower()
    if mode in {"latest", "oldest", "views", "resonance"}:
        return mode
    return "latest"


def _sort_nexus_items(items: List[Dict[str, Any]], sort_key: str) -> List[Dict[str, Any]]:
    mode = _normalize_public_sort(sort_key)

    def created(item: Dict[str, Any]) -> str:
        return str(item.get("created_at") or "")

    def qid(item: Dict[str, Any]) -> str:
        return str(item.get("q_instance_id") or "")

    if mode == "oldest":
        return sorted(items, key=lambda item: (created(item), qid(item)))
    if mode == "views":
        return sorted(
            items,
            key=lambda item: (
                int(((item.get("metrics") or {}).get("views") or 0)),
                int(((item.get("metrics") or {}).get("resonances") or 0)),
                created(item),
            ),
            reverse=True,
        )
    if mode == "resonance":
        return sorted(
            items,
            key=lambda item: (
                int(((item.get("metrics") or {}).get("resonances") or 0)),
                int(((item.get("metrics") or {}).get("views") or 0)),
                created(item),
            ),
            reverse=True,
        )
    return sorted(items, key=lambda item: (created(item), qid(item)), reverse=True)


def _generated_created_at(row: Dict[str, Any]) -> Optional[str]:
    return str((row or {}).get("published_at") or (row or {}).get("updated_at") or (row or {}).get("created_at") or "").strip() or None


def _run_in_background(coro: Any) -> None:
    async def _runner() -> None:
        try:
            await coro
        except Exception:
            return

    try:
        asyncio.create_task(_runner())
    except Exception:
        return


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


async def _build_public_piece_items(*, viewer_user_id: str, rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    if not rows:
        return []
    owner_ids = {
        str((row or {}).get("owner_user_id") or "").strip()
        for row in rows
        if str((row or {}).get("owner_user_id") or "").strip()
    }
    profiles_map = await fetch_profiles_by_ids(list(owner_ids))
    q_instance_ids: Set[str] = {generated_public_id(row) for row in rows if generated_public_id(row)}
    metrics_task = asyncio.create_task(fetch_instance_metrics(q_instance_ids))
    reads_task = asyncio.create_task(fetch_reads(viewer_user_id, q_instance_ids))
    resonated_task = asyncio.create_task(fetch_resonated_instances(viewer_user_id, q_instance_ids))
    followed_owner_ids_task = asyncio.create_task(
        fetch_followed_owner_ids(viewer_user_id=viewer_user_id, limit=5000)
    )
    metrics, read_set, resonated_set, followed_owner_ids = await asyncio.gather(
        metrics_task,
        reads_task,
        resonated_task,
        followed_owner_ids_task,
    )
    items: List[Dict[str, Any]] = []
    for row in rows:
        iid = generated_public_id(row)
        if not iid:
            continue
        owner_user_id = str((row or {}).get("owner_user_id") or "").strip()
        owner_profile = profiles_map.get(owner_user_id) or {}
        question_text = str((row or {}).get("question") or "").strip()
        body = get_public_generated_reflection_text(row)
        if not question_text or not body:
            continue
        q_key = build_generated_q_key(row)
        metric_row = metrics.get(iid) or {}
        views = int(metric_row.get("views") or 0)
        resonances = int(metric_row.get("resonances") or 0)
        items.append(
            {
                "q_instance_id": iid,
                "source_type": EMOTION_GENERATED_SOURCE_TYPE,
                "owner": {
                    "user_id": owner_user_id,
                    "display_name": str(owner_profile.get("display_name") or "").strip() or None,
                    "friend_code": str(owner_profile.get("friend_code") or "").strip() or None,
                },
                "question": {"q_key": q_key, "title": question_text},
                "body": body,
                "created_at": _generated_created_at(row),
                "metrics": {
                    "views": views,
                    "resonances": resonances,
                },
                "viewer_state": {
                    "is_new": iid not in read_set,
                    "is_resonated": iid in resonated_set,
                    "can_resonate": bool(
                        owner_user_id
                        and owner_user_id != str(viewer_user_id)
                        and owner_user_id in followed_owner_ids
                    ),
                },
            }
        )
    return items


async def _fetch_generated_list_items_public(*, viewer_user_id: str, target_user_id: str) -> List[Dict[str, Any]]:
    rows = await fetch_active_emotion_generated_reflections_for_owner(target_user_id, limit=200)
    items = await _build_public_piece_items(viewer_user_id=viewer_user_id, rows=rows)
    out: List[Dict[str, Any]] = []
    for item in items:
        out.append(
            {
                "title": str(((item.get("question") or {}).get("title") or "")).strip(),
                "q_key": str(((item.get("question") or {}).get("q_key") or "")).strip(),
                "q_instance_id": str(item.get("q_instance_id") or "").strip(),
                "generated_at": item.get("created_at"),
                "views": int(((item.get("metrics") or {}).get("views") or 0)),
                "resonances": int(((item.get("metrics") or {}).get("resonances") or 0)),
                "is_new": bool(((item.get("viewer_state") or {}).get("is_new") or False)),
            }
        )
    return out


async def _compute_public_unread_for_target(*, viewer_user_id: str, target_user_id: str) -> Dict[str, Any]:
    if str(viewer_user_id or "").strip() == str(target_user_id or "").strip():
        return {
            "status": "ok",
            "viewer_user_id": str(viewer_user_id),
            "target_user_id": str(target_user_id),
            "total_items": 0,
            "unread_count": 0,
            "has_unread": False,
        }
    rows = await fetch_active_emotion_generated_reflections_for_owner(target_user_id, limit=500)
    q_instance_ids = {generated_public_id(row) for row in rows if generated_public_id(row)}
    read_set = await fetch_reads(viewer_user_id, q_instance_ids)
    total_items = len(q_instance_ids)
    unread_count = sum(1 for iid in q_instance_ids if iid not in read_set)
    return {
        "status": "ok",
        "viewer_user_id": str(viewer_user_id),
        "target_user_id": str(target_user_id),
        "total_items": int(total_items),
        "unread_count": int(unread_count),
        "has_unread": bool(unread_count > 0),
    }


async def _build_public_piece_detail_response(
    *,
    viewer_user_id: str,
    q_instance_id: str,
    mark_viewed: bool,
) -> Dict[str, Any]:
    iid = str(q_instance_id or "").strip()
    row = await resolve_generated_reflection_access(viewer_user_id=viewer_user_id, q_instance_id=iid)
    body = get_public_generated_reflection_text(row)
    if not body:
        raise HTTPException(status_code=404, detail="Reflection not found")
    q_key = build_generated_q_key(row)
    title = str((row or {}).get("question") or "").strip()
    if not title:
        raise HTTPException(status_code=404, detail="Reflection not found")
    target_user_id = str((row or {}).get("owner_user_id") or "").strip()
    is_self = target_user_id == str(viewer_user_id)
    followed_owner_ids: Set[str] = set()
    if target_user_id and not is_self:
        followed_owner_ids = await fetch_followed_owner_ids(
            viewer_user_id=str(viewer_user_id),
            limit=5000,
        )
    can_resonate = bool(target_user_id and not is_self and target_user_id in followed_owner_ids)
    resonated_task = asyncio.create_task(is_resonated(viewer_user_id, iid))

    views = 0
    resonances = 0
    is_new = False
    if mark_viewed:
        await upsert_read(viewer_user_id, iid)
        if is_self:
            metrics = await fetch_instance_metrics({iid})
            metric_row = metrics.get(iid) or {}
            views = int(metric_row.get("views") or 0)
            resonances = int(metric_row.get("resonances") or 0)
        else:
            counts = await inc_metric(q_key=q_key, q_instance_id=iid, field="views", delta=1)
            views = int(counts.get("views") or 0)
            resonances = int(counts.get("resonances") or 0)
            requested_at = _now_iso()
            _run_in_background(
                enqueue_ranking_board_refresh(
                    metric_key="mymodel_views",
                    user_id=viewer_user_id,
                    trigger="piece_public_detail_mark_viewed",
                    requested_at=requested_at,
                    debounce=True,
                )
            )
            _run_in_background(
                enqueue_account_status_refresh(
                    target_user_id=target_user_id,
                    actor_user_id=viewer_user_id,
                    trigger="piece_public_detail_mark_viewed",
                    requested_at=requested_at,
                    debounce=True,
                )
            )
            _run_in_background(
                enqueue_global_summary_refresh(
                    trigger="piece_public_detail_mark_viewed",
                    requested_at=requested_at,
                    actor_user_id=viewer_user_id,
                    debounce=True,
                )
            )
    else:
        metrics_task = asyncio.create_task(fetch_instance_metrics({iid}))
        reads_task = asyncio.create_task(fetch_reads(viewer_user_id, {iid}))
        metrics, read_set = await asyncio.gather(metrics_task, reads_task)
        metric_row = metrics.get(iid) or {}
        views = int(metric_row.get("views") or 0)
        resonances = int(metric_row.get("resonances") or 0)
        is_new = iid not in read_set

    is_resonated_now = await resonated_task
    return {
        "title": title,
        "body": body,
        "q_key": q_key,
        "q_instance_id": iid,
        "owner_user_id": target_user_id or None,
        "views": int(views or 0),
        "resonances": int(resonances or 0),
        "is_new": bool(is_new),
        "is_resonated": bool(is_resonated_now),
        "can_resonate": bool(can_resonate),
    }


async def build_nexus_reflections_payload(
    *,
    viewer_user_id: str,
    target_user_id: Optional[str],
    sort: str,
    limit: int,
    following_only: bool,
) -> Dict[str, Any]:
    viewer_id = str(viewer_user_id or "").strip()
    if not viewer_id:
        raise HTTPException(status_code=401, detail="Invalid token")
    followed_owner_ids = await fetch_followed_owner_ids(viewer_user_id=viewer_id, limit=5000)
    owner_filter = str(target_user_id or "").strip()
    if owner_filter:
        if owner_filter != viewer_id and owner_filter not in followed_owner_ids:
            allowed = await has_myprofile_link(viewer_user_id=viewer_id, owner_user_id=owner_filter)
            if not allowed:
                raise HTTPException(status_code=403, detail="You are not allowed to query this MyProfile")
        target_owner_ids = {owner_filter}
    elif following_only:
        target_owner_ids = set(followed_owner_ids)
    else:
        target_owner_ids = set(followed_owner_ids)
        target_owner_ids.add(viewer_id)
    if not target_owner_ids:
        return {"status": "ok", "sort": _normalize_public_sort(sort), "total_items": 0, "has_more": False, "items": []}
    fetch_oldest_first = _normalize_public_sort(sort) == "oldest"
    owner_tasks = [
        fetch_active_emotion_generated_reflections_for_owner(
            owner_id,
            limit=max(int(limit) * 3, 50),
            ascending=fetch_oldest_first,
        )
        for owner_id in sorted(target_owner_ids)
    ]
    rows_nested = await asyncio.gather(*owner_tasks)
    merged: Dict[str, Dict[str, Any]] = {}
    for owner_rows in rows_nested:
        for row in owner_rows or []:
            pid = generated_public_id(row)
            if pid:
                merged[pid] = row
    rows = sorted(list(merged.values()), key=generated_row_sort_key, reverse=(not fetch_oldest_first))
    items = await _build_public_piece_items(viewer_user_id=viewer_id, rows=rows)
    sorted_items = _sort_nexus_items(items, sort)
    total_items = len(sorted_items)
    return {
        "status": "ok",
        "sort": _normalize_public_sort(sort),
        "total_items": total_items,
        "has_more": total_items > int(limit),
        "items": sorted_items[: int(limit)],
    }


async def build_qna_public_list_payload(
    *,
    viewer_user_id: str,
    target_user_id: Optional[str],
    sort: str,
    metric: str,
) -> Dict[str, Any]:
    viewer_id = str(viewer_user_id or "").strip()
    tgt = str(target_user_id or viewer_id).strip()
    if not tgt:
        raise HTTPException(status_code=400, detail="target_user_id is required")
    if tgt != viewer_id:
        allowed = await has_myprofile_link(viewer_user_id=viewer_id, owner_user_id=tgt)
        if not allowed:
            raise HTTPException(status_code=403, detail="You are not allowed to query this MyProfile")
    tiers = await resolve_piece_view_tiers(viewer_user_id=viewer_id, target_user_id=tgt)
    items = await _fetch_generated_list_items_public(viewer_user_id=viewer_id, target_user_id=tgt)
    sort_key = str(sort or "newest").strip().lower()
    metric_key = str(metric or "views").strip().lower()
    if sort_key == "popular":
        if metric_key not in ("views", "resonances"):
            metric_key = "views"
        if metric_key == "resonances":
            items.sort(key=lambda x: (int(x.get("resonances") or 0), int(x.get("views") or 0), x.get("generated_at") or ""), reverse=True)
        else:
            items.sort(key=lambda x: (int(x.get("views") or 0), int(x.get("resonances") or 0), x.get("generated_at") or ""), reverse=True)
    else:
        items.sort(key=lambda x: (x.get("generated_at") or "", x.get("q_instance_id") or ""), reverse=True)
    return {
        "items": items,
        "meta": {
            "viewer_user_id": viewer_id,
            "target_user_id": tgt,
            "subscription_tier": str(tiers.subscription_tier),
            "view_tier": str(tiers.view_tier),
            "build_tier": str(tiers.build_tier),
            "effective_tier": str(tiers.effective_tier),
            "total_items": len(items),
        },
    }


async def build_qna_public_unread_payload(*, viewer_user_id: str, target_user_id: Optional[str]) -> Dict[str, Any]:
    viewer_id = str(viewer_user_id or "").strip()
    tgt = str(target_user_id or viewer_id).strip()
    if not tgt:
        raise HTTPException(status_code=400, detail="target_user_id is required")
    if tgt != viewer_id:
        allowed = await has_myprofile_link(viewer_user_id=viewer_id, owner_user_id=tgt)
        if not allowed:
            raise HTTPException(status_code=403, detail="You are not allowed to query this MyProfile")
    return await _compute_public_unread_for_target(viewer_user_id=viewer_id, target_user_id=tgt)


async def build_qna_public_unread_status_payload(*, viewer_user_id: str) -> Dict[str, Any]:
    viewer_id = str(viewer_user_id or "").strip()
    if not viewer_id:
        raise HTTPException(status_code=401, detail="Invalid token")
    followed_owner_ids = await fetch_followed_owner_ids(viewer_user_id=viewer_id, limit=5000)
    followed_owner_ids.discard(viewer_id)
    accessible_target_count = 1 + len(followed_owner_ids)
    following_has_unread = False
    if followed_owner_ids:
        owner_tasks = [fetch_active_emotion_generated_reflections_for_owner(owner_id, limit=500) for owner_id in sorted(followed_owner_ids)]
        rows_nested = await asyncio.gather(*owner_tasks)
        q_instance_ids: Set[str] = set()
        for owner_rows in rows_nested:
            for row in owner_rows or []:
                iid = generated_public_id(row)
                if iid:
                    q_instance_ids.add(iid)
        read_set = await fetch_reads(viewer_id, q_instance_ids)
        for iid in q_instance_ids:
            if iid not in read_set:
                following_has_unread = True
                break
    return {
        "status": "ok",
        "viewer_user_id": viewer_id,
        "scope": "accessible",
        "accessible_target_count": int(accessible_target_count),
        "self_has_unread": False,
        "following_has_unread": bool(following_has_unread),
        "has_unread": bool(following_has_unread),
    }


async def build_qna_public_detail_payload(
    *,
    viewer_user_id: str,
    q_instance_id: str,
    mark_viewed: bool,
) -> Dict[str, Any]:
    iid = str(q_instance_id or "").strip()
    if not is_generated_reflection_instance_id(iid):
        raise HTTPException(status_code=404, detail="Reflection not found")
    return await _build_public_piece_detail_response(
        viewer_user_id=str(viewer_user_id),
        q_instance_id=iid,
        mark_viewed=bool(mark_viewed),
    )
