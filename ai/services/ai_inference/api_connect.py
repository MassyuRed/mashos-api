# -*- coding: utf-8 -*-
"""Current Connect API entrypoint.

This module now owns the current-vocabulary Connect route definition.
Legacy aggregate entrypoints may still delegate here during the
rename-safe / split-safe phase.
"""

from __future__ import annotations

from typing import Optional

from fastapi import FastAPI, Header, HTTPException, Query

from api_self_structure import (
    MyProfileLookupResponse,
    _extract_bearer_token,
    _has_follow_request,
    _is_already_registered,
    _is_private_account,
    _lookup_profile_by_myprofile_code,
    _resolve_user_id_from_token,
)

ConnectLookupResponse = MyProfileLookupResponse

def register_connect_routes(app: FastAPI) -> None:
    """Register current Connect lookup routes on the given FastAPI app."""

    @app.get("/connect/lookup", response_model=MyProfileLookupResponse)
    async def lookup_myprofile_by_code(
        myprofile_code: Optional[str] = Query(default=None, min_length=4, max_length=64, description="Target user's myprofile_code (legacy Connect ID)"),
        connect_code: Optional[str] = Query(default=None, min_length=4, max_length=64, description="Target user's connect_code (Connect ID)"),
        authorization: Optional[str] = Header(default=None, alias="Authorization"),
    ) -> MyProfileLookupResponse:
        access_token = _extract_bearer_token(authorization)
        if not access_token:
            raise HTTPException(status_code=401, detail="Authorization header with Bearer token is required")

        viewer_user_id = await _resolve_user_id_from_token(access_token)
        code = str(connect_code or myprofile_code or "").strip()
        if not code:
            raise HTTPException(status_code=400, detail="connect_code is required")

        target_profile = await _lookup_profile_by_myprofile_code(code)
        if not target_profile:
            return MyProfileLookupResponse(status="ok", found=False)

        owner_user_id = str(target_profile.get("id") or "").strip()
        if not owner_user_id:
            return MyProfileLookupResponse(status="ok", found=False)

        is_private_account = False
        try:
            is_private_account = await _is_private_account(owner_user_id)
        except Exception:
            is_private_account = False

        is_following = False
        is_follow_requested = False
        if viewer_user_id and str(viewer_user_id) != owner_user_id:
            try:
                is_following = await _is_already_registered(str(viewer_user_id), owner_user_id)
            except Exception:
                is_following = False

            if not is_following:
                try:
                    is_follow_requested = bool(await _has_follow_request(str(viewer_user_id), owner_user_id))
                except Exception:
                    is_follow_requested = False

        return MyProfileLookupResponse(
            status="ok",
            found=True,
            target_user_id=owner_user_id,
            display_name=(target_profile.get("display_name") if isinstance(target_profile.get("display_name"), str) else None),
            connect_code=(target_profile.get("myprofile_code") if isinstance(target_profile.get("myprofile_code"), str) else code),
            myprofile_code=(target_profile.get("myprofile_code") if isinstance(target_profile.get("myprofile_code"), str) else code),
            is_private_account=bool(is_private_account),
            is_following=bool(is_following),
            is_follow_requested=bool(is_follow_requested),
        )

__all__ = [
    "ConnectLookupResponse",
    "register_connect_routes",
]
