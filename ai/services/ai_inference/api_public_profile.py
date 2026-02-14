# -*- coding: utf-8 -*-
"""api_public_profile.py

Public (unauthenticated) profile resolver for share URLs.

Endpoint
- GET /public/profile/by-friend-code?code=<friend_code>

Design notes
- This endpoint is meant for emlis.app/u/{friend_code} (OG tags / share landing).
- It should **not** expose private account details.
- Privacy flags are stored in `account_visibility_settings` (not in `profiles`).

Env
- SUPABASE_URL
- SUPABASE_SERVICE_ROLE_KEY  (Legacy service_role key)
"""

from typing import Any, Dict

import logging
import os

import httpx
from fastapi import APIRouter, HTTPException

logger = logging.getLogger("public_profile_api")

SUPABASE_URL = os.getenv("SUPABASE_URL", "").rstrip("/")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")


def _ensure_supabase_config() -> None:
    if not SUPABASE_URL or not SUPABASE_SERVICE_ROLE_KEY:
        raise HTTPException(status_code=500, detail="Supabase config missing")


def _sb_headers() -> Dict[str, str]:
    return {
        "apikey": SUPABASE_SERVICE_ROLE_KEY,
        "Authorization": f"Bearer {SUPABASE_SERVICE_ROLE_KEY}",
        "Content-Type": "application/json",
    }


def register_public_profile_routes(app):
    router = APIRouter()

    @router.get("/public/profile/by-friend-code")
    async def get_profile_by_friend_code(code: str) -> Dict[str, Any]:
        _ensure_supabase_config()

        async with httpx.AsyncClient(timeout=8.0) as client:
            # 1) Resolve by friend_code from profiles
            prof = await client.get(
                f"{SUPABASE_URL}/rest/v1/profiles",
                headers=_sb_headers(),
                params={
                    # NOTE: profiles does NOT have is_private_account; it lives in account_visibility_settings
                    "select": "id,display_name,friend_code,myprofile_code",
                    "friend_code": f"eq.{code}",
                    "limit": "1",
                },
            )

            if prof.status_code >= 300:
                logger.error(
                    "Supabase profiles query failed: %s %s",
                    prof.status_code,
                    prof.text[:1500],
                )
                raise HTTPException(status_code=502, detail="Supabase profiles query failed")

            rows = prof.json()
            if not rows:
                raise HTTPException(status_code=404, detail="User not found")

            row = rows[0]
            user_id = row.get("id")

            # 2) Read privacy flags (optional)
            is_private_account = False
            is_friend_code_public = True
            if user_id:
                vis = await client.get(
                    f"{SUPABASE_URL}/rest/v1/account_visibility_settings",
                    headers=_sb_headers(),
                    params={
                        "select": "is_private_account,is_friend_code_public",
                        "user_id": f"eq.{user_id}",
                        "limit": "1",
                    },
                )
                if vis.status_code < 300:
                    vrows = vis.json()
                    if isinstance(vrows, list) and vrows:
                        v = vrows[0] or {}
                        if v.get("is_private_account") is not None:
                            is_private_account = bool(v.get("is_private_account"))
                        if v.get("is_friend_code_public") is not None:
                            is_friend_code_public = bool(v.get("is_friend_code_public"))
                else:
                    # Not fatal for Phase1; keep defaults.
                    logger.warning(
                        "Supabase visibility query failed: %s %s",
                        vis.status_code,
                        vis.text[:500],
                    )

            # Anti-enumeration: if user disabled public friend_code, behave as "not found".
            if not is_friend_code_public:
                raise HTTPException(status_code=404, detail="User not found")

            # Private account: do NOT expose display_name publicly
            if is_private_account:
                return {
                    "status": "ok",
                    "user_id": user_id,
                    "display_name": None,
                    "friend_code": row.get("friend_code"),
                    "myprofile_code": None,
                    "is_private_account": True,
                    "is_friend_code_public": is_friend_code_public,
                }

            return {
                "status": "ok",
                "user_id": user_id,
                "display_name": row.get("display_name"),
                "friend_code": row.get("friend_code"),
                "myprofile_code": row.get("myprofile_code"),
                "is_private_account": False,
                "is_friend_code_public": is_friend_code_public,
            }

    app.include_router(router)
