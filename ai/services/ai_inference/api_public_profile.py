# -*- coding: utf-8 -*-
from typing import Any, Dict, Optional

from fastapi import APIRouter, HTTPException
import httpx
import os

SUPABASE_URL = os.getenv("SUPABASE_URL", "").rstrip("/")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")


def _ensure_supabase_config():
    if not SUPABASE_URL or not SUPABASE_SERVICE_ROLE_KEY:
        raise HTTPException(status_code=500, detail="Supabase config missing")


def _sb_headers():
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
            resp = await client.get(
                f"{SUPABASE_URL}/rest/v1/profiles",
                headers=_sb_headers(),
                params={
                    "select": "id,display_name,friend_code,is_private_account",
                    "friend_code": f"eq.{code}",
                    "limit": "1",
                },
            )

        if resp.status_code >= 300:
            raise HTTPException(status_code=502, detail="Supabase query failed")

        rows = resp.json()
        if not rows:
            raise HTTPException(status_code=404, detail="User not found")

        row = rows[0]

        # 非公開アカウントなら最低限だけ返す
        if row.get("is_private_account"):
            return {
                "status": "ok",
                "user_id": row["id"],
                "display_name": None,
                "friend_code": row["friend_code"],
                "is_private_account": True,
            }

        return {
            "status": "ok",
            "user_id": row["id"],
            "display_name": row["display_name"],
            "friend_code": row["friend_code"],
            "is_private_account": False,
        }

    app.include_router(router)
