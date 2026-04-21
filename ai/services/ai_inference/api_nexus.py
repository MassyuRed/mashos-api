# -*- coding: utf-8 -*-
"""api_nexus.py

Nexus read-side routes for the new emotion-generated Reflection feed.
"""

from __future__ import annotations

import asyncio
import inspect
from typing import Any, Dict, List, Optional, Set, Tuple

from fastapi import FastAPI, Header, HTTPException, Query
from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel, Field

from api_emotion_submit import _extract_bearer_token, _resolve_user_id_from_token
from api_mymodel_qna import (
    MYMODEL_REFLECTIONS_TABLE,
    QnaDetailResponse,
    QnaUnreadStatusResponse,
    _build_qna_detail_response,
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


NEXUS_SOURCE_PATHS: Dict[str, str] = {
    "emotion_ranking": "/ranking/emotions",
    "emotion_log": "/friends/feed",
    "recommend_users": "/mymodel/recommend/users",
    "history_echoes": "/mymodel/qna/echoes/reflections",
    "history_discoveries": "/mymodel/qna/discoveries/reflections",
}


def _fastapi_default_value(default: Any) -> Tuple[bool, Any]:
    """Return (has_value, value) for FastAPI Query/Header defaults."""
    if default is inspect.Signature.empty:
        return False, None
    if hasattr(default, "default"):
        nested_default = getattr(default, "default")
        if nested_default is not inspect.Signature.empty:
            return True, nested_default
    return True, default


def _find_registered_route_endpoint(app: FastAPI, *, path: str, method: str = "GET"):
    target_path = str(path or "").strip()
    target_method = str(method or "GET").strip().upper()
    for route in getattr(app, "routes", []) or []:
        if str(getattr(route, "path", "") or "") != target_path:
            continue
        methods = {str(m or "").upper() for m in (getattr(route, "methods", set()) or set())}
        if target_method not in methods:
            continue
        endpoint = getattr(route, "endpoint", None)
        if endpoint is not None:
            return endpoint
    return None


async def _call_registered_route_json(
    app: FastAPI,
    *,
    path: str,
    method: str = "GET",
    detail: str,
    **values: Any,
) -> Any:
    """Call another registered read route and return JSON-safe data.

    Nexus uses these wrappers as stable /nexus/* entry points while preserving
    the source endpoint semantics that already power the existing screens.
    """
    endpoint = _find_registered_route_endpoint(app, path=path, method=method)
    if endpoint is None:
        raise HTTPException(status_code=502, detail=f"{detail}: route not registered")

    kwargs: Dict[str, Any] = {}
    try:
        signature = inspect.signature(endpoint)
    except Exception:
        signature = None

    if signature is not None:
        for name, param in signature.parameters.items():
            if name in values:
                kwargs[name] = values[name]
                continue
            has_default, default_value = _fastapi_default_value(param.default)
            if has_default:
                kwargs[name] = default_value
    else:
        kwargs = dict(values)

    try:
        result = endpoint(**kwargs)
        if inspect.isawaitable(result):
            result = await result
        return jsonable_encoder(result)
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=502, detail=f"{detail}: {exc}") from exc


def _normalize_include_sections(raw: Optional[str]) -> Set[str]:
    if raw is None:
        return {"emotion_ranking", "reflections"}
    values = {
        str(part or "").strip().lower()
        for part in str(raw or "").replace("|", ",").split(",")
    }
    values.discard("")
    allowed = {
        "emotion_ranking",
        "reflections",
        "emotion_log",
        "recommend_users",
        "history_echoes",
        "history_discoveries",
    }
    if "all" in values:
        return set(allowed)
    return values & allowed


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


def _strip_reflection_instance_prefix(q_instance_id: str) -> str:
    raw = str(q_instance_id or "").strip()
    if not raw:
        return ""
    if raw.startswith("reflection:"):
        return raw.split(":", 1)[1].strip()
    return raw


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
    ascending: bool = False,
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


def _sort_items(items: List[NexusReflectionItem], sort_key: str) -> List[NexusReflectionItem]:
    mode = str(sort_key or "latest").strip().lower()
    if mode == "oldest":
        return sorted(items, key=lambda item: (item.created_at or "", item.q_instance_id))
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
        sort: str = Query(default="latest", description="latest | oldest | views | resonance | discovery"),
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
        fetch_oldest_first = str(sort or "latest").strip().lower() == "oldest"
        rows = await _fetch_emotion_generated_rows_for_owner_ids(
            target_owner_ids,
            scan_limit=scan_limit,
            ascending=fetch_oldest_first,
        )
        if not rows:
            return NexusReflectionResponse(status="ok", sort=str(sort or "latest"), total_items=0, has_more=False, items=[])

        owner_ids = {str((row or {}).get("owner_user_id") or "").strip() for row in rows if str((row or {}).get("owner_user_id") or "").strip()}
        profiles_map = await _fetch_profiles_by_ids(list(owner_ids))

        q_instance_ids: Set[str] = {_row_instance_id(row) for row in rows if _row_instance_id(row)}
        metrics_task = _fetch_instance_metrics(q_instance_ids)
        discoveries_task = _fetch_discovery_counts_for_instances(q_instance_ids)
        reads_task = _fetch_reads(str(viewer_user_id), q_instance_ids)
        metrics, discoveries_map, read_set = await asyncio.gather(
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

    @app.get("/nexus/reflections/unread-status", response_model=QnaUnreadStatusResponse)
    async def nexus_reflections_unread_status(
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
            raise HTTPException(status_code=502, detail=f"Failed to load Nexus reflection unread status: {exc}") from exc

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

        return QnaUnreadStatusResponse(
            status="ok",
            viewer_user_id=viewer_id,
            scope="accessible",
            accessible_target_count=int(accessible_target_count),
            self_has_unread=bool(self_has_unread),
            following_has_unread=bool(following_has_unread),
            has_unread=bool(self_has_unread or following_has_unread),
        )

    @app.get("/nexus/reflections/{q_instance_id}", response_model=QnaDetailResponse)
    async def nexus_reflection_detail(
        q_instance_id: str,
        mark_viewed: bool = Query(default=False, description="If true, mark the reflection as viewed"),
        include_my_discovery_latest: bool = Query(
            default=False,
            description="Compatibility flag forwarded to the reaction layer",
        ),
        authorization: Optional[str] = Header(default=None, alias="Authorization"),
    ) -> QnaDetailResponse:
        token = _extract_bearer_token(authorization) if authorization else None
        if not token:
            raise HTTPException(status_code=401, detail="Authorization header with Bearer token is required")

        viewer_user_id = await _resolve_user_id_from_token(token)
        if not viewer_user_id:
            raise HTTPException(status_code=401, detail="Invalid token")

        row = await _fetch_emotion_generated_row_by_instance_id(q_instance_id)
        if not row:
            raise HTTPException(status_code=404, detail="Nexus reflection not found")

        owner_user_id = str((row or {}).get("owner_user_id") or "").strip()
        if not owner_user_id:
            raise HTTPException(status_code=404, detail="Nexus reflection owner is missing")

        if owner_user_id != str(viewer_user_id):
            followed_owner_ids = await _fetch_followed_owner_ids(str(viewer_user_id), limit=5000)
            if owner_user_id not in followed_owner_ids:
                raise HTTPException(status_code=403, detail="You are not allowed to query this MyProfile")

        question_text = str((row or {}).get("question") or "").strip()
        body = get_public_generated_reflection_text(row)
        if not question_text or not body:
            raise HTTPException(status_code=404, detail="Nexus reflection is not readable")

        q_key = str((row or {}).get("q_key") or "").strip()
        if not q_key:
            q_key = f"emotion_generated:{_strip_reflection_instance_prefix(q_instance_id) or 'unknown'}"

        question_id = 0
        try:
            question_id = int((row or {}).get("question_id") or 0)
        except Exception:
            question_id = 0

        return await _build_qna_detail_response(
            viewer_user_id=str(viewer_user_id),
            target_user_id=owner_user_id,
            q_instance_id=_row_instance_id(row),
            q_key=q_key,
            title=question_text,
            body=body,
            question_id=question_id,
            include_my_discovery_latest=bool(include_my_discovery_latest),
            mark_viewed=bool(mark_viewed),
        )

    @app.get("/nexus/emotion-ranking")
    async def nexus_emotion_ranking(
        limit: int = Query(default=5, ge=1, le=50),
        range: str = Query(default="day"),
        authorization: Optional[str] = Header(default=None, alias="Authorization"),
    ) -> Any:
        return await _call_registered_route_json(
            app,
            path=NEXUS_SOURCE_PATHS["emotion_ranking"],
            detail="Failed to load Nexus emotion ranking",
            limit=int(limit),
            range=str(range or "day"),
            authorization=authorization,
        )

    @app.get("/nexus/emotion-log")
    async def nexus_emotion_log(
        limit: int = Query(default=20, ge=1, le=100),
        authorization: Optional[str] = Header(default=None, alias="Authorization"),
    ) -> Any:
        return await _call_registered_route_json(
            app,
            path=NEXUS_SOURCE_PATHS["emotion_log"],
            detail="Failed to load Nexus emotion log",
            limit=int(limit),
            authorization=authorization,
        )

    @app.get("/nexus/recommend/users")
    async def nexus_recommend_users(
        limit: int = Query(default=8, ge=1, le=100),
        authorization: Optional[str] = Header(default=None, alias="Authorization"),
    ) -> Any:
        return await _call_registered_route_json(
            app,
            path=NEXUS_SOURCE_PATHS["recommend_users"],
            detail="Failed to load Nexus recommend users",
            limit=int(limit),
            authorization=authorization,
        )

    @app.get("/nexus/history/echoes")
    async def nexus_history_echoes(
        limit: int = Query(default=20, ge=1, le=100),
        offset: int = Query(default=0, ge=0),
        authorization: Optional[str] = Header(default=None, alias="Authorization"),
    ) -> Any:
        return await _call_registered_route_json(
            app,
            path=NEXUS_SOURCE_PATHS["history_echoes"],
            detail="Failed to load Nexus echoes history",
            limit=int(limit),
            offset=int(offset),
            authorization=authorization,
        )

    @app.get("/nexus/history/discoveries")
    async def nexus_history_discoveries(
        limit: int = Query(default=20, ge=1, le=100),
        offset: int = Query(default=0, ge=0),
        authorization: Optional[str] = Header(default=None, alias="Authorization"),
    ) -> Any:
        return await _call_registered_route_json(
            app,
            path=NEXUS_SOURCE_PATHS["history_discoveries"],
            detail="Failed to load Nexus discoveries history",
            limit=int(limit),
            offset=int(offset),
            authorization=authorization,
        )

    @app.get("/nexus/bootstrap")
    async def nexus_bootstrap(
        include: Optional[str] = Query(
            default=None,
            description="Comma-separated sections. Default: emotion_ranking,reflections. Use all for every Nexus tab.",
        ),
        reflection_limit: int = Query(default=20, ge=1, le=100),
        ranking_limit: int = Query(default=5, ge=1, le=50),
        tab_limit: int = Query(default=8, ge=1, le=100),
        authorization: Optional[str] = Header(default=None, alias="Authorization"),
    ) -> Dict[str, Any]:
        token = _extract_bearer_token(authorization) if authorization else None
        if not token:
            raise HTTPException(status_code=401, detail="Authorization header with Bearer token is required")
        viewer_user_id = await _resolve_user_id_from_token(token)
        if not viewer_user_id:
            raise HTTPException(status_code=401, detail="Invalid token")

        include_sections = _normalize_include_sections(include)
        sections: Dict[str, Any] = {}
        errors: Dict[str, str] = {}

        async def _load_section(name: str, coro) -> None:
            try:
                sections[name] = await coro
            except HTTPException as exc:
                errors[name] = str(exc.detail)
            except Exception as exc:
                errors[name] = str(exc)

        tasks = []
        if "emotion_ranking" in include_sections:
            tasks.append(_load_section("emotion_ranking", _call_registered_route_json(
                app, path=NEXUS_SOURCE_PATHS["emotion_ranking"], detail="Failed to load Nexus emotion ranking",
                limit=int(ranking_limit), period="today", authorization=authorization)))
        if "reflections" in include_sections:
            tasks.append(_load_section("reflections", _call_registered_route_json(
                app, path="/nexus/reflections", detail="Failed to load Nexus reflections",
                sort="latest", limit=int(reflection_limit), following_only=True, authorization=authorization)))
        if "emotion_log" in include_sections:
            tasks.append(_load_section("emotion_log", _call_registered_route_json(
                app, path=NEXUS_SOURCE_PATHS["emotion_log"], detail="Failed to load Nexus emotion log",
                limit=int(tab_limit), authorization=authorization)))
        if "recommend_users" in include_sections:
            tasks.append(_load_section("recommend_users", _call_registered_route_json(
                app, path=NEXUS_SOURCE_PATHS["recommend_users"], detail="Failed to load Nexus recommend users",
                limit=int(tab_limit), authorization=authorization)))
        if "history_echoes" in include_sections:
            tasks.append(_load_section("history_echoes", _call_registered_route_json(
                app, path=NEXUS_SOURCE_PATHS["history_echoes"], detail="Failed to load Nexus echoes history",
                limit=int(tab_limit), offset=0, authorization=authorization)))
        if "history_discoveries" in include_sections:
            tasks.append(_load_section("history_discoveries", _call_registered_route_json(
                app, path=NEXUS_SOURCE_PATHS["history_discoveries"], detail="Failed to load Nexus discoveries history",
                limit=int(tab_limit), offset=0, authorization=authorization)))

        if tasks:
            await asyncio.gather(*tasks)

        return {
            "status": "partial" if errors else "ok",
            "viewer_user_id": str(viewer_user_id),
            "sections": sections,
            "errors": errors,
            "source_paths": {
                key: value
                for key, value in NEXUS_SOURCE_PATHS.items()
                if key in include_sections or key == "emotion_ranking"
            },
        }
