# -*- coding: utf-8 -*-
"""api_nexus.py

Nexus read-side routes for the new emotion-generated Reflection feed.
"""

from __future__ import annotations

import asyncio
import inspect
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Set, Tuple

from fastapi import FastAPI, Header, HTTPException, Query
from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel, Field

from api_emotion_submit import _extract_bearer_token, _resolve_user_id_from_token
from piece_public_read_service import (
    EMOTION_GENERATED_SOURCE_TYPE,
    build_nexus_reflections_payload,
    build_qna_public_detail_payload,
    build_qna_public_unread_status_payload,
    delete_nexus_piece_payload,
)
from api_piece_runtime import (
    _fetch_active_user_ids,
    _fetch_followed_owner_ids,
    _fetch_profiles_by_ids,
    _filter_recommendation_enabled,
)


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


class NexusViewerState(BaseModel):
    is_new: bool = False
    is_resonated: bool = False
    can_resonate: bool = False


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



class NexusReflectionsUnreadStatusResponse(BaseModel):
    status: str = Field(default="ok")
    viewer_user_id: str
    scope: str = Field(default="accessible")
    accessible_target_count: int = 0
    self_has_unread: bool = False
    following_has_unread: bool = False
    has_unread: bool = False


class NexusReflectionDetailResponse(BaseModel):
    title: str
    body: str
    q_key: str
    q_instance_id: str
    owner_user_id: Optional[str] = None
    views: int = 0
    resonances: int = 0
    is_new: bool = False
    is_resonated: bool = False
    can_resonate: bool = False


class NexusPieceDeleteResponse(BaseModel):
    status: str = Field(default="ok")
    q_instance_id: str
    deleted: bool = True


class NexusRecommendUser(BaseModel):
    id: str
    display_name: Optional[str] = None
    share_code: Optional[str] = None
    friend_code: Optional[str] = None
    connect_code: Optional[str] = None
    myprofile_code: Optional[str] = None
    is_following: bool = False


class NexusRecommendUsersResponse(BaseModel):
    status: str = Field(default="ok")
    days: int = 7
    total_items: int = 0
    users: List[NexusRecommendUser] = Field(default_factory=list)


NEXUS_SOURCE_PATHS: Dict[str, str] = {
    "emotion_ranking": "/ranking/emotions",
    "emotion_log": "/emotion-log/feed",
    "recommend_users": "/nexus/recommend/users",
    "history_echoes": "/piece/resonances/pieces",
}


def _fastapi_default_value(default: Any) -> Tuple[bool, Any]:
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
    }
    if "all" in values:
        return set(allowed)
    return values & allowed


async def _build_nexus_recommend_users_payload(
    *,
    viewer_user_id: str,
    limit: int,
    days: int = 7,
) -> Dict[str, Any]:
    viewer = str(viewer_user_id or "").strip()
    if not viewer:
        raise HTTPException(status_code=401, detail="Invalid token")

    safe_limit = max(1, min(int(limit or 8), 100))
    safe_days = max(1, min(int(days or 7), 30))
    since_dt = datetime.now(timezone.utc) - timedelta(days=safe_days)
    since_iso = since_dt.isoformat().replace("+00:00", "Z")
    scan_limit = max(200, safe_limit * 30)

    active_ids = await _fetch_active_user_ids(since_iso=since_iso, scan_limit=scan_limit)
    candidate_ids = [uid for uid in sorted(active_ids) if uid and uid != viewer]

    followed_ids = await _fetch_followed_owner_ids(viewer_user_id=viewer, limit=5000)
    candidate_ids = [uid for uid in candidate_ids if uid not in followed_ids]
    candidate_ids = await _filter_recommendation_enabled(candidate_ids)
    candidate_ids = candidate_ids[:safe_limit]

    profiles_map = await _fetch_profiles_by_ids(candidate_ids)
    users: List[NexusRecommendUser] = []
    for uid in candidate_ids:
        profile = profiles_map.get(str(uid)) or {}
        display_name = profile.get("display_name") if isinstance(profile, dict) else None
        friend_code = profile.get("friend_code") if isinstance(profile, dict) else None
        myprofile_code = profile.get("myprofile_code") if isinstance(profile, dict) else None
        users.append(
            NexusRecommendUser(
                id=str(uid),
                display_name=(str(display_name).strip() if display_name is not None else None) or None,
                share_code=(str(friend_code).strip() if friend_code is not None else None) or None,
                friend_code=(str(friend_code).strip() if friend_code is not None else None) or None,
                connect_code=(str(myprofile_code).strip() if myprofile_code is not None else None) or None,
                myprofile_code=(str(myprofile_code).strip() if myprofile_code is not None else None) or None,
                is_following=False,
            )
        )

    return {
        "status": "ok",
        "days": safe_days,
        "total_items": len(users),
        "users": [user.dict() for user in users],
    }


def register_nexus_routes(app: FastAPI) -> None:
    @app.get("/nexus/pieces", response_model=NexusReflectionResponse)
    async def nexus_reflections(
        sort: str = Query(default="latest", description="latest | oldest | views | resonance"),
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

        payload = await build_nexus_reflections_payload(
            viewer_user_id=str(viewer_user_id),
            target_user_id=str(user_id or "").strip() or None,
            sort=str(sort or "latest"),
            limit=int(limit),
            following_only=bool(following_only),
        )
        return NexusReflectionResponse(**payload)

    @app.get("/nexus/pieces/unread-status", response_model=NexusReflectionsUnreadStatusResponse)
    async def nexus_reflections_unread_status(
        authorization: Optional[str] = Header(default=None, alias="Authorization"),
    ) -> NexusReflectionsUnreadStatusResponse:
        token = _extract_bearer_token(authorization) if authorization else None
        if not token:
            raise HTTPException(status_code=401, detail="Authorization header with Bearer token is required")

        viewer_user_id = await _resolve_user_id_from_token(token)
        if not viewer_user_id:
            raise HTTPException(status_code=401, detail="Invalid token")

        payload = await build_qna_public_unread_status_payload(
            viewer_user_id=str(viewer_user_id),
        )
        return NexusReflectionsUnreadStatusResponse(**payload)

    @app.get("/nexus/pieces/{q_instance_id}", response_model=NexusReflectionDetailResponse)
    async def nexus_reflection_detail(
        q_instance_id: str,
        mark_viewed: bool = Query(default=False, description="If true, mark the reflection as viewed"),
        authorization: Optional[str] = Header(default=None, alias="Authorization"),
    ) -> NexusReflectionDetailResponse:
        token = _extract_bearer_token(authorization) if authorization else None
        if not token:
            raise HTTPException(status_code=401, detail="Authorization header with Bearer token is required")

        viewer_user_id = await _resolve_user_id_from_token(token)
        if not viewer_user_id:
            raise HTTPException(status_code=401, detail="Invalid token")

        payload = await build_qna_public_detail_payload(
            viewer_user_id=str(viewer_user_id),
            q_instance_id=q_instance_id,
            mark_viewed=bool(mark_viewed),
        )
        return NexusReflectionDetailResponse(**payload)

    @app.delete("/nexus/pieces/{q_instance_id}", response_model=NexusPieceDeleteResponse)
    async def nexus_piece_delete(
        q_instance_id: str,
        authorization: Optional[str] = Header(default=None, alias="Authorization"),
    ) -> NexusPieceDeleteResponse:
        token = _extract_bearer_token(authorization) if authorization else None
        if not token:
            raise HTTPException(status_code=401, detail="Authorization header with Bearer token is required")

        viewer_user_id = await _resolve_user_id_from_token(token)
        if not viewer_user_id:
            raise HTTPException(status_code=401, detail="Invalid token")

        payload = await delete_nexus_piece_payload(
            viewer_user_id=str(viewer_user_id),
            q_instance_id=str(q_instance_id or "").strip(),
        )
        return NexusPieceDeleteResponse(**payload)

    @app.get("/nexus/emotion-ranking", response_model=Any)
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

    @app.get("/nexus/emotion-log", response_model=Any)
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

    @app.get("/nexus/recommend/users", response_model=NexusRecommendUsersResponse)
    async def nexus_recommend_users(
        limit: int = Query(default=8, ge=1, le=100),
        authorization: Optional[str] = Header(default=None, alias="Authorization"),
    ) -> NexusRecommendUsersResponse:
        token = _extract_bearer_token(authorization) if authorization else None
        if not token:
            raise HTTPException(status_code=401, detail="Authorization header with Bearer token is required")

        viewer_user_id = await _resolve_user_id_from_token(token)
        if not viewer_user_id:
            raise HTTPException(status_code=401, detail="Invalid token")

        payload = await _build_nexus_recommend_users_payload(
            viewer_user_id=str(viewer_user_id),
            limit=int(limit),
        )
        return NexusRecommendUsersResponse(**payload)

    @app.get("/nexus/history/resonances")
    async def nexus_history_echoes(
        limit: int = Query(default=20, ge=1, le=100),
        offset: int = Query(default=0, ge=0),
        authorization: Optional[str] = Header(default=None, alias="Authorization"),
    ) -> Any:
        return await _call_registered_route_json(
            app,
            path=NEXUS_SOURCE_PATHS["history_echoes"],
            detail="Failed to load Nexus resonance history",
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
            tasks.append(_load_section("reflections", build_nexus_reflections_payload(
                viewer_user_id=str(viewer_user_id),
                target_user_id=None,
                sort="latest",
                limit=int(reflection_limit),
                following_only=True,
            )))
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
                app, path=NEXUS_SOURCE_PATHS["history_echoes"], detail="Failed to load Nexus resonance history",
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
