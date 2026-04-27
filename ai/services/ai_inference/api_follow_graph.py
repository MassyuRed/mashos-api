# -*- coding: utf-8 -*-
"""Current Follow graph API entrypoint.

This module now owns the current-vocabulary Follow graph route definitions.
Legacy aggregate entrypoints may still delegate here during the
rename-safe / split-safe phase.
"""

from __future__ import annotations

from typing import Any, Dict, Optional

from fastapi import FastAPI, Header, HTTPException, Query
from fastapi.responses import JSONResponse

from api_self_structure import (
    FOLLOW_REQUESTS_TABLE,
    MYPROFILE_FOLLOW_LIST_RPC,
    MyProfileFollowListItem,
    MyProfileFollowListResponse,
    MyProfileFollowRequestCancelBody,
    MyProfileFollowRequestIdBody,
    MyProfileFollowStatsResponse,
    MyProfileIncomingFollowRequestItem,
    MyProfileIncomingFollowRequestsResponse,
    MyProfileLinkActionResponse,
    MyProfileLinkBody,
    MyProfileOutgoingFollowRequestItem,
    MyProfileOutgoingFollowRequestsResponse,
    MyProfileRemoveFollowerBody,
    _delete_follow_request_by_id,
    _delete_follow_request_pair,
    _delete_myprofile_link,
    _extract_bearer_token,
    _fetch_profiles_basic_map,
    _find_existing_follow_request_id,
    _get_follow_request_by_id,
    _has_follow_request,
    _insert_follow_request,
    _insert_myprofile_link,
    _is_already_registered,
    _is_private_account,
    _lookup_profile_by_myprofile_code,
    _resolve_user_id_from_token,
    _sb_count,
    _sb_get,
    _sb_post_rpc,
    logger,
)

FollowGraphListItem = MyProfileFollowListItem
FollowGraphListResponse = MyProfileFollowListResponse
FollowGraphRequestCancelBody = MyProfileFollowRequestCancelBody
FollowGraphStatsResponse = MyProfileFollowStatsResponse
FollowGraphIncomingRequestItem = MyProfileIncomingFollowRequestItem
FollowGraphIncomingRequestsResponse = MyProfileIncomingFollowRequestsResponse
FollowGraphLinkActionResponse = MyProfileLinkActionResponse
FollowGraphLinkBody = MyProfileLinkBody
FollowGraphOutgoingRequestItem = MyProfileOutgoingFollowRequestItem
FollowGraphOutgoingRequestsResponse = MyProfileOutgoingFollowRequestsResponse
FollowGraphRemoveFollowerBody = MyProfileRemoveFollowerBody

def register_follow_graph_routes(app: FastAPI) -> None:
    """Register current Follow graph routes on the given FastAPI app."""

    @app.post("/follow/create", response_model=MyProfileLinkActionResponse)
    async def follow_myprofile(
        body: MyProfileLinkBody,
        authorization: Optional[str] = Header(default=None, alias="Authorization"),
    ) -> MyProfileLinkActionResponse:
        access_token = _extract_bearer_token(authorization)
        if not access_token:
            raise HTTPException(status_code=401, detail="Authorization header with Bearer token is required")

        viewer_user_id = await _resolve_user_id_from_token(access_token)

        owner_user_id = str(body.owner_user_id or "").strip()
        if not owner_user_id:
            code = str(body.connect_code or body.myprofile_code or "").strip()
            if not code:
                raise HTTPException(status_code=400, detail="owner_user_id or connect_code is required")
            target_profile = await _lookup_profile_by_myprofile_code(code)
            if not target_profile:
                raise HTTPException(status_code=404, detail="User not found for the given connect_code")
            owner_user_id = str(target_profile.get("id") or "").strip()

        if not owner_user_id:
            raise HTTPException(status_code=404, detail="Owner user not found")

        if owner_user_id == viewer_user_id:
            raise HTTPException(status_code=400, detail="You cannot follow yourself")

        # If already following, treat as ok (idempotent).
        try:
            if await _is_already_registered(viewer_user_id, owner_user_id):
                return MyProfileLinkActionResponse(
                    status="ok",
                    viewer_user_id=viewer_user_id,
                    owner_user_id=owner_user_id,
                    is_following=True,
                    is_follow_requested=False,
                    result="followed",
                )
        except Exception:
            # Best-effort; fall through.
            pass

        # Private account => create a follow request (approval required)
        is_private = False
        try:
            is_private = await _is_private_account(owner_user_id)
        except Exception:
            is_private = False

        if is_private:
            existing_id = await _find_existing_follow_request_id(viewer_user_id, owner_user_id)
            if existing_id:
                return MyProfileLinkActionResponse(
                    status="ok",
                    viewer_user_id=viewer_user_id,
                    owner_user_id=owner_user_id,
                    is_following=False,
                    is_follow_requested=True,
                    result="requested",
                )

            created = await _insert_follow_request(viewer_user_id, owner_user_id)
            if not created:
                # Likely already requested (race). Treat as requested.
                return MyProfileLinkActionResponse(
                    status="ok",
                    viewer_user_id=viewer_user_id,
                    owner_user_id=owner_user_id,
                    is_following=False,
                    is_follow_requested=True,
                    result="requested",
                )

            return MyProfileLinkActionResponse(
                status="ok",
                viewer_user_id=viewer_user_id,
                owner_user_id=owner_user_id,
                is_following=False,
                is_follow_requested=True,
                result="requested",
            )

        # Public account => create link immediately
        await _insert_myprofile_link(viewer_user_id, owner_user_id)

        # If there was a pending request from the same viewer->owner, clean it up (best-effort).
        try:
            await _delete_follow_request_pair(viewer_user_id, owner_user_id)
        except Exception:
            pass

        return MyProfileLinkActionResponse(
            status="ok",
            viewer_user_id=viewer_user_id,
            owner_user_id=owner_user_id,
            is_following=True,
            is_follow_requested=False,
            result="followed",
        )

    @app.post("/follow/delete", response_model=MyProfileLinkActionResponse)
    async def unfollow_myprofile(
        body: MyProfileLinkBody,
        authorization: Optional[str] = Header(default=None, alias="Authorization"),
    ) -> MyProfileLinkActionResponse:
        access_token = _extract_bearer_token(authorization)
        if not access_token:
            raise HTTPException(status_code=401, detail="Authorization header with Bearer token is required")

        viewer_user_id = await _resolve_user_id_from_token(access_token)

        owner_user_id = str(body.owner_user_id or "").strip()
        if not owner_user_id:
            code = str(body.connect_code or body.myprofile_code or "").strip()
            if not code:
                raise HTTPException(status_code=400, detail="owner_user_id or connect_code is required")
            target_profile = await _lookup_profile_by_myprofile_code(code)
            if not target_profile:
                raise HTTPException(status_code=404, detail="User not found for the given connect_code")
            owner_user_id = str(target_profile.get("id") or "").strip()

        if not owner_user_id:
            raise HTTPException(status_code=404, detail="Owner user not found")

        # Deleting a non-existing link is treated as ok (idempotent)
        await _delete_myprofile_link(viewer_user_id, owner_user_id)
        return MyProfileLinkActionResponse(
            status="ok",
            viewer_user_id=viewer_user_id,
            owner_user_id=owner_user_id,
            is_following=False,
        )
    

    @app.post("/follow/remove-follower", response_model=MyProfileLinkActionResponse)
    async def remove_myprofile_follower(
        body: MyProfileRemoveFollowerBody,
        authorization: Optional[str] = Header(default=None, alias="Authorization"),
    ) -> MyProfileLinkActionResponse:
        access_token = _extract_bearer_token(authorization)
        if not access_token:
            raise HTTPException(status_code=401, detail="Authorization header with Bearer token is required")

        owner_user_id = await _resolve_user_id_from_token(access_token)

        viewer_user_id = str(body.viewer_user_id or "").strip()
        if not viewer_user_id:
            raise HTTPException(status_code=400, detail="viewer_user_id is required")

        if viewer_user_id == owner_user_id:
            raise HTTPException(status_code=400, detail="You cannot remove yourself")

        # Delete follower link: viewer -> owner(me)
        await _delete_myprofile_link(viewer_user_id, owner_user_id)
        return MyProfileLinkActionResponse(
            status="ok",
            viewer_user_id=viewer_user_id,
            owner_user_id=owner_user_id,
            is_following=False,
        )


    @app.get("/follow/stats", response_model=MyProfileFollowStatsResponse)
    async def get_myprofile_follow_stats(
        target_user_id: str = Query(..., description="Target user's UUID (profiles.id)"),
        authorization: Optional[str] = Header(default=None, alias="Authorization"),
    ) -> MyProfileFollowStatsResponse:
        """Return follow stats for a target user.

        - following_count: number of users the target is following
        - follower_count: number of users following the target
        - is_following: whether the caller follows the target (false if not authenticated)
        """
        uid = str(target_user_id or "").strip()
        if not uid:
            raise HTTPException(status_code=400, detail="target_user_id is required")

        # Resolve viewer (optional). If no token, is_following is always False.
        viewer_user_id: Optional[str] = None
        access_token = _extract_bearer_token(authorization)
        if access_token:
            try:
                viewer_user_id = await _resolve_user_id_from_token(access_token)
            except Exception:
                viewer_user_id = None

        # Count following / followers via service_role (avoid client-side RLS)
        following_count = await _sb_count(
            "/rest/v1/myprofile_links",
            params={
                "select": "owner_user_id",
                "viewer_user_id": f"eq.{uid}",
                "limit": "1",
            },
        )

        follower_count = await _sb_count(
            "/rest/v1/myprofile_links",
            params={
                "select": "viewer_user_id",
                "owner_user_id": f"eq.{uid}",
                "limit": "1",
            },
        )

        is_following = False
        if viewer_user_id and str(viewer_user_id) != uid:
            try:
                is_following = await _is_already_registered(str(viewer_user_id), uid)
            except Exception:
                is_following = False

        is_follow_requested = False
        if viewer_user_id and str(viewer_user_id) != uid and (not is_following):
            try:
                is_follow_requested = bool(await _has_follow_request(str(viewer_user_id), uid))
            except Exception:
                is_follow_requested = False

        return MyProfileFollowStatsResponse(
            status="ok",
            target_user_id=uid,
            following_count=int(following_count or 0),
            follower_count=int(follower_count or 0),
            is_following=bool(is_following),
            is_follow_requested=bool(is_follow_requested),
        )



    @app.post("/follow/request/cancel")
    async def cancel_follow_request(
        body: MyProfileFollowRequestCancelBody,
        authorization: Optional[str] = Header(default=None, alias="Authorization"),
    ) -> Dict[str, Any]:
        access_token = _extract_bearer_token(authorization)
        if not access_token:
            raise HTTPException(status_code=401, detail="Authorization header with Bearer token is required")

        requester_user_id = await _resolve_user_id_from_token(access_token)
        tgt = str(body.target_user_id or "").strip()
        if not tgt:
            return JSONResponse(status_code=400, content={"detail": "target_user_id is required", "code": "invalid_target_user_id"})
        if tgt == str(requester_user_id):
            return JSONResponse(status_code=400, content={"detail": "You cannot cancel for yourself", "code": "invalid_target_user_id"})

        existing_id = await _find_existing_follow_request_id(str(requester_user_id), tgt)
        if not existing_id:
            return JSONResponse(status_code=404, content={"detail": "申請が見つかりません", "code": "request_not_found"})

        await _delete_follow_request_pair(str(requester_user_id), tgt)
        return {"status": "ok", "result": "canceled", "target_user_id": tgt}


    @app.get("/follow/requests/incoming", response_model=MyProfileIncomingFollowRequestsResponse)
    async def incoming_follow_requests(
        limit: int = Query(default=100, ge=1, le=300, description="Max number of requests"),
        authorization: Optional[str] = Header(default=None, alias="Authorization"),
    ) -> MyProfileIncomingFollowRequestsResponse:
        access_token = _extract_bearer_token(authorization)
        if not access_token:
            raise HTTPException(status_code=401, detail="Authorization header with Bearer token is required")

        me = await _resolve_user_id_from_token(access_token)

        resp = await _sb_get(
            f"/rest/v1/{FOLLOW_REQUESTS_TABLE}",
            params={
                "select": "id,requester_user_id,created_at",
                "target_user_id": f"eq.{me}",
                "order": "created_at.desc",
                "limit": str(int(limit)),
            },
        )
        if resp.status_code >= 300:
            logger.error("Supabase follow_requests incoming failed: %s %s", resp.status_code, resp.text[:1500])
            raise HTTPException(status_code=502, detail="Failed to load follow requests")

        rows = resp.json()
        if not isinstance(rows, list):
            rows = []

        requester_ids = [str((r or {}).get("requester_user_id") or "").strip() for r in rows if isinstance(r, dict)]
        profiles_map = await _fetch_profiles_basic_map(requester_ids)

        items: list[MyProfileIncomingFollowRequestItem] = []
        for r in rows:
            if not isinstance(r, dict):
                continue
            req_id = str(r.get("id") or "").strip()
            requester_id = str(r.get("requester_user_id") or "").strip()
            if not req_id or not requester_id:
                continue
            p = profiles_map.get(requester_id) or {}
            items.append(
                MyProfileIncomingFollowRequestItem(
                    request_id=req_id,
                    requester_user_id=requester_id,
                    requester_display_name=(p.get("display_name") if isinstance(p.get("display_name"), str) else None),
                    requester_connect_code=(p.get("myprofile_code") if isinstance(p.get("myprofile_code"), str) else None),
                    requester_myprofile_code=(p.get("myprofile_code") if isinstance(p.get("myprofile_code"), str) else None),
                    created_at=(str(r.get("created_at")) if r.get("created_at") is not None else None),
                )
            )

        return MyProfileIncomingFollowRequestsResponse(status="ok", total_items=len(items), requests=items)


    @app.get("/follow/requests/outgoing", response_model=MyProfileOutgoingFollowRequestsResponse)
    async def outgoing_follow_requests(
        limit: int = Query(default=100, ge=1, le=300, description="Max number of requests"),
        authorization: Optional[str] = Header(default=None, alias="Authorization"),
    ) -> MyProfileOutgoingFollowRequestsResponse:
        access_token = _extract_bearer_token(authorization)
        if not access_token:
            raise HTTPException(status_code=401, detail="Authorization header with Bearer token is required")

        me = await _resolve_user_id_from_token(access_token)

        resp = await _sb_get(
            f"/rest/v1/{FOLLOW_REQUESTS_TABLE}",
            params={
                "select": "id,target_user_id,created_at",
                "requester_user_id": f"eq.{me}",
                "order": "created_at.desc",
                "limit": str(int(limit)),
            },
        )
        if resp.status_code >= 300:
            logger.error("Supabase follow_requests outgoing failed: %s %s", resp.status_code, resp.text[:1500])
            raise HTTPException(status_code=502, detail="Failed to load follow requests")

        rows = resp.json()
        if not isinstance(rows, list):
            rows = []

        target_ids = [str((r or {}).get("target_user_id") or "").strip() for r in rows if isinstance(r, dict)]
        profiles_map = await _fetch_profiles_basic_map(target_ids)

        items: list[MyProfileOutgoingFollowRequestItem] = []
        for r in rows:
            if not isinstance(r, dict):
                continue
            req_id = str(r.get("id") or "").strip()
            target_id = str(r.get("target_user_id") or "").strip()
            if not req_id or not target_id:
                continue
            p = profiles_map.get(target_id) or {}
            items.append(
                MyProfileOutgoingFollowRequestItem(
                    request_id=req_id,
                    target_user_id=target_id,
                    target_display_name=(p.get("display_name") if isinstance(p.get("display_name"), str) else None),
                    target_connect_code=(p.get("myprofile_code") if isinstance(p.get("myprofile_code"), str) else None),
                    target_myprofile_code=(p.get("myprofile_code") if isinstance(p.get("myprofile_code"), str) else None),
                    created_at=(str(r.get("created_at")) if r.get("created_at") is not None else None),
                )
            )

        return MyProfileOutgoingFollowRequestsResponse(status="ok", total_items=len(items), requests=items)


    @app.post("/follow/requests/approve")
    async def approve_follow_request(
        body: MyProfileFollowRequestIdBody,
        authorization: Optional[str] = Header(default=None, alias="Authorization"),
    ) -> Dict[str, Any]:
        access_token = _extract_bearer_token(authorization)
        if not access_token:
            raise HTTPException(status_code=401, detail="Authorization header with Bearer token is required")

        me = await _resolve_user_id_from_token(access_token)
        request_id = str(body.request_id or "").strip()
        if not request_id:
            return JSONResponse(status_code=400, content={"detail": "request_id is required", "code": "invalid_request_id"})

        req = await _get_follow_request_by_id(request_id)
        if not req:
            return JSONResponse(status_code=404, content={"detail": "申請が見つかりません", "code": "request_not_found"})

        target_user_id = str(req.get("target_user_id") or "").strip()
        requester_user_id = str(req.get("requester_user_id") or "").strip()
        if not target_user_id or not requester_user_id:
            return JSONResponse(status_code=404, content={"detail": "申請が見つかりません", "code": "request_not_found"})

        if str(target_user_id) != str(me):
            raise HTTPException(status_code=403, detail="You are not allowed to approve this request")

        # Create link (requester follows me)
        await _insert_myprofile_link(requester_user_id, str(me))

        # Remove request (best-effort)
        try:
            await _delete_follow_request_by_id(request_id)
        except Exception:
            pass

        return {
            "status": "ok",
            "result": "approved",
            "request_id": request_id,
            "requester_user_id": requester_user_id,
            "target_user_id": str(me),
        }


    @app.post("/follow/requests/reject")
    async def reject_follow_request(
        body: MyProfileFollowRequestIdBody,
        authorization: Optional[str] = Header(default=None, alias="Authorization"),
    ) -> Dict[str, Any]:
        access_token = _extract_bearer_token(authorization)
        if not access_token:
            raise HTTPException(status_code=401, detail="Authorization header with Bearer token is required")

        me = await _resolve_user_id_from_token(access_token)
        request_id = str(body.request_id or "").strip()
        if not request_id:
            return JSONResponse(status_code=400, content={"detail": "request_id is required", "code": "invalid_request_id"})

        req = await _get_follow_request_by_id(request_id)
        if not req:
            return JSONResponse(status_code=404, content={"detail": "申請が見つかりません", "code": "request_not_found"})

        target_user_id = str(req.get("target_user_id") or "").strip()
        if str(target_user_id) != str(me):
            raise HTTPException(status_code=403, detail="You are not allowed to reject this request")

        await _delete_follow_request_by_id(request_id)

        return {
            "status": "ok",
            "result": "rejected",
            "request_id": request_id,
        }


    @app.get("/follow/list", response_model=MyProfileFollowListResponse)
    async def get_myprofile_follow_list(
        target_user_id: str = Query(..., description="Target user's UUID (profiles.id)"),
        tab: str = Query(default="following", description="following | followers"),
        limit: int = Query(default=1000, ge=1, le=1000, description="Max number of rows"),
        authorization: Optional[str] = Header(default=None, alias="Authorization"),
    ) -> MyProfileFollowListResponse:
        """Return follow list (profiles) for a target user.

        - tab=following: users the target is following
        - tab=followers: users who follow the target
        """
        uid = str(target_user_id or "").strip()
        if not uid:
            raise HTTPException(status_code=400, detail="target_user_id is required")

        t = str(tab or "").strip().lower()
        if t not in ("following", "followers"):
            t = "following"

        # authorization is accepted for future-proofing, but currently optional
        _ = authorization  # noqa: F841

        # Phase2: Fetch follow list via Supabase RPC (single roundtrip)
        fn = (MYPROFILE_FOLLOW_LIST_RPC or "myprofile_follow_list_v1").strip() or "myprofile_follow_list_v1"
        payload = {
            "p_target_user_id": uid,
            "p_tab": t,
            "p_limit": int(limit),
        }
        resp = await _sb_post_rpc(fn, payload=payload)
        if resp.status_code >= 300:
            logger.error(
                "Supabase rpc %s failed: %s %s",
                fn,
                resp.status_code,
                (resp.text or "")[:1500],
            )
            raise HTTPException(status_code=502, detail="Failed to load follow list")

        data = resp.json()
        if not isinstance(data, list):
            data = []

        ordered: list[MyProfileFollowListItem] = []
        for r in data:
            if not isinstance(r, dict):
                continue
            pid = str(r.get("id") or "").strip()
            if not pid:
                continue
            ordered.append(
                MyProfileFollowListItem(
                    id=pid,
                    display_name=(r.get("display_name") if isinstance(r.get("display_name"), str) else None),
                    share_code=(r.get("friend_code") if isinstance(r.get("friend_code"), str) else None),
                    friend_code=(r.get("friend_code") if isinstance(r.get("friend_code"), str) else None),
                    connect_code=(r.get("myprofile_code") if isinstance(r.get("myprofile_code"), str) else None),
                    myprofile_code=(r.get("myprofile_code") if isinstance(r.get("myprofile_code"), str) else None),
                    is_private_account=bool(r.get("is_private_account") or False),
                )
            )

        return MyProfileFollowListResponse(
            status="ok",
            target_user_id=uid,
            tab=t,
            rows=ordered,
        )

__all__ = [
    "FollowGraphListItem",
    "FollowGraphListResponse",
    "FollowGraphRequestCancelBody",
    "FollowGraphStatsResponse",
    "FollowGraphIncomingRequestItem",
    "FollowGraphIncomingRequestsResponse",
    "FollowGraphLinkActionResponse",
    "FollowGraphLinkBody",
    "FollowGraphOutgoingRequestItem",
    "FollowGraphOutgoingRequestsResponse",
    "FollowGraphRemoveFollowerBody",
    "register_follow_graph_routes",
]
