from __future__ import annotations

import asyncio
from typing import Any, Dict, List, Optional, Set, Tuple

from fastapi import HTTPException

from generated_reflection_display import get_public_generated_reflection_text

EMOTION_GENERATED_SOURCE_TYPE = "emotion_generated"


def _dump_model(model: Any) -> Any:
    if hasattr(model, "model_dump"):
        return model.model_dump()
    if hasattr(model, "dict"):
        return model.dict()
    return model


def _strip_reflection_instance_prefix(q_instance_id: str) -> str:
    raw = str(q_instance_id or "").strip()
    if raw.startswith("reflection:"):
        return raw.split(":", 1)[1].strip()
    return raw


def _row_instance_id(row: Dict[str, Any]) -> str:
    raw = str((row or {}).get("public_id") or (row or {}).get("id") or "").strip()
    if not raw:
        return ""
    return raw if raw.startswith("reflection:") else f"reflection:{raw}"


def _row_sort_key(row: Dict[str, Any]) -> Tuple[str, str]:
    return (
        str((row or {}).get("published_at") or (row or {}).get("updated_at") or (row or {}).get("created_at") or "").strip(),
        str((row or {}).get("id") or "").strip(),
    )


def _normalize_public_sort(raw_sort: str) -> str:
    mode = str(raw_sort or "latest").strip().lower()
    if mode in {"latest", "oldest", "views", "resonance"}:
        return mode
    if mode == "discovery":
        return "resonance"
    return "latest"


async def _sb_get_json(path: str, *, params: Dict[str, str]) -> List[Dict[str, Any]]:
    from api_mymodel_qna import _sb_get

    resp = await _sb_get(path, params=params)
    if resp.status_code >= 300:
        raise HTTPException(status_code=502, detail="Failed to load public Piece artifacts")
    try:
        data = resp.json()
    except Exception:
        return []
    if isinstance(data, list):
        return [row for row in data if isinstance(row, dict)]
    return []


async def _fetch_emotion_generated_rows_for_owner_ids(
    owner_ids: Set[str],
    *,
    scan_limit: int,
    ascending: bool = False,
) -> List[Dict[str, Any]]:
    from api_mymodel_qna import MYMODEL_REFLECTIONS_TABLE, _quoted_in

    ids = [str(owner_id).strip() for owner_id in (owner_ids or set()) if str(owner_id).strip()]
    if not ids:
        return []

    merged: Dict[str, Dict[str, Any]] = {}
    chunk_size = 100
    for index in range(0, len(ids), chunk_size):
        chunk = set(ids[index:index + chunk_size])
        params = {
            "select": "*",
            "owner_user_id": _quoted_in(chunk),
            "source_type": f"eq.{EMOTION_GENERATED_SOURCE_TYPE}",
            "is_active": "eq.true",
            "status": "in.(ready,published)",
            "order": "published_at.asc,updated_at.asc" if ascending else "published_at.desc,updated_at.desc",
            "limit": str(max(50, int(scan_limit))),
        }
        rows = await _sb_get_json(f"/rest/v1/{MYMODEL_REFLECTIONS_TABLE}", params=params)
        for row in rows:
            row_id = str((row or {}).get("id") or "").strip()
            if row_id:
                merged[row_id] = row

    visible_rows = [row for row in merged.values() if get_public_generated_reflection_text(row)]
    return sorted(visible_rows, key=_row_sort_key, reverse=(not ascending))


async def _fetch_emotion_generated_row_by_instance_id(q_instance_id: str) -> Optional[Dict[str, Any]]:
    from api_mymodel_qna import MYMODEL_REFLECTIONS_TABLE

    reflection_id = _strip_reflection_instance_prefix(q_instance_id)
    if not reflection_id:
        return None

    rows = await _sb_get_json(
        f"/rest/v1/{MYMODEL_REFLECTIONS_TABLE}",
        params={
            "select": "*",
            "id": f"eq.{reflection_id}",
            "source_type": f"eq.{EMOTION_GENERATED_SOURCE_TYPE}",
            "is_active": "eq.true",
            "status": "in.(ready,published)",
            "limit": "1",
        },
    )
    if not rows:
        return None
    row = rows[0] if isinstance(rows[0], dict) else None
    if not row:
        return None
    if not get_public_generated_reflection_text(row):
        return None
    return row


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


async def build_nexus_reflections_payload(
    *,
    viewer_user_id: str,
    target_user_id: Optional[str],
    sort: str,
    limit: int,
    following_only: bool,
) -> Dict[str, Any]:
    from api_mymodel_qna import (
        _fetch_discovery_counts_for_instances,
        _fetch_followed_owner_ids,
        _fetch_instance_metrics,
        _fetch_profiles_by_ids,
        _fetch_reads,
    )

    viewer_id = str(viewer_user_id or "").strip()
    if not viewer_id:
        raise HTTPException(status_code=401, detail="Invalid token")

    followed_owner_ids = await _fetch_followed_owner_ids(viewer_user_id=viewer_id, limit=5000)
    owner_filter = str(target_user_id or "").strip()

    if owner_filter:
        if owner_filter != viewer_id and owner_filter not in followed_owner_ids:
            raise HTTPException(status_code=403, detail="You are not allowed to query this MyProfile")
        target_owner_ids = {owner_filter}
    elif following_only:
        target_owner_ids = set(followed_owner_ids)
    else:
        target_owner_ids = set(followed_owner_ids)
        target_owner_ids.add(viewer_id)

    if not target_owner_ids:
        return {
            "status": "ok",
            "sort": _normalize_public_sort(sort),
            "total_items": 0,
            "has_more": False,
            "items": [],
        }

    scan_limit = max(int(limit) * 3, 50)
    fetch_oldest_first = _normalize_public_sort(sort) == "oldest"
    rows = await _fetch_emotion_generated_rows_for_owner_ids(
        target_owner_ids,
        scan_limit=scan_limit,
        ascending=fetch_oldest_first,
    )
    if not rows:
        return {
            "status": "ok",
            "sort": _normalize_public_sort(sort),
            "total_items": 0,
            "has_more": False,
            "items": [],
        }

    owner_ids = {
        str((row or {}).get("owner_user_id") or "").strip()
        for row in rows
        if str((row or {}).get("owner_user_id") or "").strip()
    }
    profiles_map = await _fetch_profiles_by_ids(list(owner_ids))

    q_instance_ids: Set[str] = {_row_instance_id(row) for row in rows if _row_instance_id(row)}
    metrics_task = _fetch_instance_metrics(q_instance_ids)
    discoveries_task = _fetch_discovery_counts_for_instances(q_instance_ids)
    reads_task = _fetch_reads(viewer_id, q_instance_ids)
    metrics, discoveries_map, read_set = await asyncio.gather(
        metrics_task,
        discoveries_task,
        reads_task,
    )

    items: List[Dict[str, Any]] = []
    for row in rows:
        iid = _row_instance_id(row)
        if not iid:
            continue

        owner_user_id = str((row or {}).get("owner_user_id") or "").strip()
        owner_profile = profiles_map.get(owner_user_id) or {}
        question_text = str((row or {}).get("question") or "").strip()
        body = get_public_generated_reflection_text(row)
        if not question_text or not body:
            continue

        q_key = str((row or {}).get("q_key") or "").strip()
        if not q_key:
            q_key = f"emotion_generated:{str((row or {}).get('id') or '').strip() or 'unknown'}"

        metric_row = metrics.get(iid) or {}
        try:
            views = int(metric_row.get("views") or 0)
        except Exception:
            views = 0
        try:
            resonances = int(metric_row.get("resonances") or 0)
        except Exception:
            resonances = 0
        try:
            discoveries = int(discoveries_map.get(iid) or 0)
        except Exception:
            discoveries = 0

        created_at = str((row or {}).get("published_at") or (row or {}).get("updated_at") or (row or {}).get("created_at") or "").strip() or None

        items.append(
            {
                "q_instance_id": iid,
                "source_type": EMOTION_GENERATED_SOURCE_TYPE,
                "owner": {
                    "user_id": owner_user_id,
                    "display_name": str(owner_profile.get("display_name") or "").strip() or None,
                    "friend_code": str(owner_profile.get("friend_code") or "").strip() or None,
                },
                "question": {
                    "q_key": q_key,
                    "title": question_text,
                },
                "body": body,
                "created_at": created_at,
                "metrics": {
                    "views": views,
                    "resonances": resonances,
                    "discoveries": discoveries,
                },
                "viewer_state": {
                    "is_new": iid not in read_set,
                },
            }
        )

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
    from api_mymodel_qna import _fetch_generated_list_items, _has_myprofile_link, _resolve_tiers

    viewer_id = str(viewer_user_id or "").strip()
    tgt = str(target_user_id or viewer_id).strip()
    if not tgt:
        raise HTTPException(status_code=400, detail="target_user_id is required")

    if tgt != viewer_id:
        allowed = await _has_myprofile_link(viewer_user_id=viewer_id, owner_user_id=tgt)
        if not allowed:
            raise HTTPException(status_code=403, detail="You are not allowed to query this MyProfile")

    subscription_tier, view_tier, build_tier, effective_tier = await _resolve_tiers(
        viewer_user_id=viewer_id,
        target_user_id=tgt,
    )

    try:
        items = await _fetch_generated_list_items(
            viewer_user_id=viewer_id,
            target_user_id=tgt,
        )
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Failed to load public Piece list: {exc}") from exc

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
        items.sort(key=lambda x: (x.generated_at or "", x.q_instance_id), reverse=True)

    return {
        "items": [_dump_model(item) for item in items],
        "meta": {
            "viewer_user_id": viewer_id,
            "target_user_id": tgt,
            "subscription_tier": subscription_tier,
            "view_tier": view_tier,
            "build_tier": build_tier,
            "effective_tier": effective_tier,
            "total_items": len(items),
        },
    }


async def build_qna_public_unread_payload(
    *,
    viewer_user_id: str,
    target_user_id: Optional[str],
) -> Dict[str, Any]:
    from api_mymodel_qna import _compute_qna_unread_for_target, _has_myprofile_link

    viewer_id = str(viewer_user_id or "").strip()
    tgt = str(target_user_id or viewer_id).strip()
    if not tgt:
        raise HTTPException(status_code=400, detail="target_user_id is required")
    if tgt != viewer_id:
        allowed = await _has_myprofile_link(viewer_user_id=viewer_id, owner_user_id=tgt)
        if not allowed:
            raise HTTPException(status_code=403, detail="You are not allowed to query this MyProfile")

    unread = await _compute_qna_unread_for_target(
        viewer_user_id=viewer_id,
        target_user_id=tgt,
    )
    return _dump_model(unread)


async def build_qna_public_unread_status_payload(*, viewer_user_id: str) -> Dict[str, Any]:
    from api_mymodel_qna import _fetch_followed_owner_ids, _fetch_reads

    viewer_id = str(viewer_user_id or "").strip()
    if not viewer_id:
        raise HTTPException(status_code=401, detail="Invalid token")

    try:
        followed_owner_ids = await _fetch_followed_owner_ids(viewer_user_id=viewer_id, limit=5000)
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"Failed to load public Piece unread status: {exc}") from exc

    followed_owner_ids.discard(viewer_id)
    accessible_target_count = 1 + len(followed_owner_ids)
    self_has_unread = False
    following_has_unread = False

    if followed_owner_ids:
        rows = await _fetch_emotion_generated_rows_for_owner_ids(
            set(followed_owner_ids),
            scan_limit=max(500, len(followed_owner_ids) * 50),
            ascending=False,
        )
        q_instance_ids: Set[str] = {_row_instance_id(row) for row in rows if _row_instance_id(row)}
        read_set = await _fetch_reads(viewer_id, q_instance_ids)
        for row in rows:
            owner_user_id = str((row or {}).get("owner_user_id") or "").strip()
            q_instance_id = _row_instance_id(row)
            if not owner_user_id or not q_instance_id or owner_user_id == viewer_id:
                continue
            if q_instance_id not in read_set:
                following_has_unread = True
                break

    return {
        "status": "ok",
        "viewer_user_id": viewer_id,
        "scope": "accessible",
        "accessible_target_count": int(accessible_target_count),
        "self_has_unread": bool(self_has_unread),
        "following_has_unread": bool(following_has_unread),
        "has_unread": bool(self_has_unread or following_has_unread),
    }


async def build_qna_public_detail_payload(
    *,
    viewer_user_id: str,
    q_instance_id: str,
    mark_viewed: bool,
    include_my_discovery_latest: bool,
) -> Dict[str, Any]:
    from api_mymodel_qna import (
        _build_generated_q_key,
        _build_qna_detail_response,
        _is_generated_reflection_instance_id,
        _resolve_generated_reflection_access,
    )

    viewer_id = str(viewer_user_id or "").strip()
    iid = str(q_instance_id or "").strip()
    if not _is_generated_reflection_instance_id(iid):
        raise HTTPException(status_code=404, detail="Reflection not found")

    row = await _resolve_generated_reflection_access(viewer_user_id=viewer_id, q_instance_id=iid)
    body = get_public_generated_reflection_text(row)
    if not body:
        raise HTTPException(status_code=404, detail="Reflection not found")
    qk = _build_generated_q_key(row)
    title = str((row or {}).get("question") or "").strip()
    if not title:
        raise HTTPException(status_code=404, detail="Reflection not found")
    owner_user_id = str((row or {}).get("owner_user_id") or "").strip()
    response = await _build_qna_detail_response(
        viewer_user_id=viewer_id,
        target_user_id=owner_user_id,
        q_instance_id=iid,
        q_key=qk,
        title=title,
        body=body,
        question_id=0,
        include_my_discovery_latest=bool(include_my_discovery_latest),
        mark_viewed=bool(mark_viewed),
    )
    return _dump_model(response)
