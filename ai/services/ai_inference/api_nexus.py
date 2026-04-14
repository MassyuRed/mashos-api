# -*- coding: utf-8 -*-
"""api_nexus.py

Nexus read-side routes for the new emotion-generated Reflection feed.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional, Set, Tuple

from fastapi import FastAPI, Header, HTTPException, Query
from pydantic import BaseModel, Field

from api_emotion_submit import _extract_bearer_token, _resolve_user_id_from_token
from api_mymodel_qna import (
    MYMODEL_REFLECTIONS_TABLE,
    _fetch_discovery_counts_for_instances,
    _fetch_followed_owner_ids,
    _fetch_instance_metrics,
    _fetch_profiles_by_ids,
    _fetch_reads,
    _quoted_in,
    _sb_get,
)
from generated_reflection_display import get_public_generated_reflection_text


EMOTION_GENERATED_SOURCE_TYPE = "emotion_generated"


class NexusOwner(BaseModel):
    user_id: str
    display_name: Optional[str] = None
    friend_code: Optional[str] = None


class NexusQuestion(BaseModel):
    q_key: str
    title: str


class NexusMetrics(BaseModel):
    views: int = 0
    resonances: int = 0
    discoveries: int = 0


class NexusViewerState(BaseModel):
    is_new: bool = False


class NexusReflectionItem(BaseModel):
    q_instance_id: str
    source_type: str = Field(default=EMOTION_GENERATED_SOURCE_TYPE)
    owner: NexusOwner
    question: NexusQuestion
    body: str
    created_at: Optional[str] = None
    metrics: NexusMetrics
    viewer_state: NexusViewerState


class NexusReflectionResponse(BaseModel):
    status: str = Field(default="ok")
    sort: str = Field(default="latest")
    total_items: int = 0
    has_more: bool = False
    items: List[NexusReflectionItem] = Field(default_factory=list)


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


async def _sb_get_json(path: str, *, params: Dict[str, str]) -> List[Dict[str, Any]]:
    resp = await _sb_get(path, params=params)
    if resp.status_code >= 300:
        raise HTTPException(status_code=502, detail="Failed to load Nexus reflections")
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
) -> List[Dict[str, Any]]:
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
            "order": "published_at.desc,updated_at.desc",
            "limit": str(max(50, int(scan_limit))),
        }
        rows = await _sb_get_json(f"/rest/v1/{MYMODEL_REFLECTIONS_TABLE}", params=params)
        for row in rows:
            row_id = str((row or {}).get("id") or "").strip()
            if row_id:
                merged[row_id] = row

    visible_rows = [row for row in merged.values() if get_public_generated_reflection_text(row)]
    return sorted(visible_rows, key=_row_sort_key, reverse=True)


def _sort_items(items: List[NexusReflectionItem], sort_key: str) -> List[NexusReflectionItem]:
    mode = str(sort_key or "latest").strip().lower()
    if mode == "views":
        return sorted(items, key=lambda item: (item.metrics.views, item.metrics.resonances, item.created_at or ""), reverse=True)
    if mode == "resonance":
        return sorted(items, key=lambda item: (item.metrics.resonances, item.metrics.views, item.created_at or ""), reverse=True)
    if mode == "discovery":
        return sorted(items, key=lambda item: (item.metrics.discoveries, item.metrics.resonances, item.created_at or ""), reverse=True)
    return sorted(items, key=lambda item: (item.created_at or "", item.q_instance_id), reverse=True)


def register_nexus_routes(app: FastAPI) -> None:
    @app.get("/nexus/reflections", response_model=NexusReflectionResponse)
    async def nexus_reflections(
        sort: str = Query(default="latest", description="latest | views | resonance | discovery"),
        limit: int = Query(default=20, ge=1, le=100),
        user_id: Optional[str] = Query(default=None, description="Optional followed user filter"),
        following_only: bool = Query(default=True),
        authorization: Optional[str] = Header(default=None, alias="Authorization"),
    ) -> NexusReflectionResponse:
        token = _extract_bearer_token(authorization) if authorization else None
        if not token:
            raise HTTPException(status_code=401, detail="Authorization header with Bearer token is required")

        viewer_user_id = await _resolve_user_id_from_token(token)
        if not viewer_user_id:
            raise HTTPException(status_code=401, detail="Invalid token")

        followed_owner_ids = await _fetch_followed_owner_ids(viewer_user_id=str(viewer_user_id), limit=5000)
        owner_filter = str(user_id or "").strip()

        if owner_filter:
            if owner_filter != str(viewer_user_id) and owner_filter not in followed_owner_ids:
                raise HTTPException(status_code=403, detail="You are not allowed to query this MyProfile")
            target_owner_ids = {owner_filter}
        elif following_only:
            target_owner_ids = set(followed_owner_ids)
        else:
            target_owner_ids = set(followed_owner_ids)
            target_owner_ids.add(str(viewer_user_id))

        if not target_owner_ids:
            return NexusReflectionResponse(status="ok", sort=str(sort or "latest"), total_items=0, has_more=False, items=[])

        scan_limit = max(int(limit) * 3, 50)
        rows = await _fetch_emotion_generated_rows_for_owner_ids(target_owner_ids, scan_limit=scan_limit)
        if not rows:
            return NexusReflectionResponse(status="ok", sort=str(sort or "latest"), total_items=0, has_more=False, items=[])

        owner_ids = {str((row or {}).get("owner_user_id") or "").strip() for row in rows if str((row or {}).get("owner_user_id") or "").strip()}
        profiles_map = await _fetch_profiles_by_ids(list(owner_ids))

        q_instance_ids: Set[str] = {_row_instance_id(row) for row in rows if _row_instance_id(row)}
        metrics_task = _fetch_instance_metrics(q_instance_ids)
        discoveries_task = _fetch_discovery_counts_for_instances(q_instance_ids)
        reads_task = _fetch_reads(str(viewer_user_id), q_instance_ids)
        metrics, discoveries_map, read_set = await __import__("asyncio").gather(
            metrics_task,
            discoveries_task,
            reads_task,
        )

        items: List[NexusReflectionItem] = []
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
                NexusReflectionItem(
                    q_instance_id=iid,
                    source_type=EMOTION_GENERATED_SOURCE_TYPE,
                    owner=NexusOwner(
                        user_id=owner_user_id,
                        display_name=str(owner_profile.get("display_name") or "").strip() or None,
                        friend_code=str(owner_profile.get("friend_code") or "").strip() or None,
                    ),
                    question=NexusQuestion(
                        q_key=q_key,
                        title=question_text,
                    ),
                    body=body,
                    created_at=created_at,
                    metrics=NexusMetrics(
                        views=views,
                        resonances=resonances,
                        discoveries=discoveries,
                    ),
                    viewer_state=NexusViewerState(
                        is_new=(iid not in read_set),
                    ),
                )
            )

        sorted_items = _sort_items(items, str(sort or "latest"))
        total_items = len(sorted_items)
        sliced_items = sorted_items[: int(limit)]
        return NexusReflectionResponse(
            status="ok",
            sort=str(sort or "latest"),
            total_items=total_items,
            has_more=total_items > int(limit),
            items=sliced_items,
        )
