from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel, Field

from api_account_visibility import _get_profile_row, _pick_row, _require_user_id
from supabase_client import sb_delete, sb_post

logger = logging.getLogger("account_lifecycle_api")


class AccountProfileMeResponse(BaseModel):
    user_id: str
    display_name: Optional[str] = None
    friend_code: Optional[str] = None
    myprofile_code: Optional[str] = None
    push_enabled: bool = True
    tutorial_completed: bool = False
    tutorial_skipped: bool = False


class AccountProfileMePatchBody(BaseModel):
    display_name: Optional[str] = None
    push_enabled: Optional[bool] = None


class AccountDeleteResponse(BaseModel):
    status: str = "ok"
    user_id: str
    deleted_tables: List[str] = Field(default_factory=list)
    failed_tables: List[str] = Field(default_factory=list)
    sign_out_required: bool = True


async def _fetch_profile_me(user_id: str) -> Dict[str, Any]:
    row = await _get_profile_row(user_id)
    return row or {}


def register_account_lifecycle_routes(app: FastAPI) -> None:
    @app.get("/account/profile/me", response_model=AccountProfileMeResponse)
    async def get_account_profile_me(
        authorization: Optional[str] = Header(default=None, alias="Authorization"),
    ) -> AccountProfileMeResponse:
        me = await _require_user_id(authorization)
        row = await _fetch_profile_me(me)
        return AccountProfileMeResponse(
            user_id=me,
            display_name=(row.get("display_name") if isinstance(row.get("display_name"), str) else None),
            friend_code=(row.get("friend_code") if isinstance(row.get("friend_code"), str) else None),
            myprofile_code=(row.get("myprofile_code") if isinstance(row.get("myprofile_code"), str) else None),
            push_enabled=(bool(row.get("push_enabled")) if row.get("push_enabled") is not None else True),
            tutorial_completed=(bool(row.get("tutorial_completed")) if row.get("tutorial_completed") is not None else False),
            tutorial_skipped=(bool(row.get("tutorial_skipped")) if row.get("tutorial_skipped") is not None else False),
        )

    @app.patch("/account/profile/me", response_model=AccountProfileMeResponse)
    async def patch_account_profile_me(
        body: AccountProfileMePatchBody,
        authorization: Optional[str] = Header(default=None, alias="Authorization"),
    ) -> AccountProfileMeResponse:
        me = await _require_user_id(authorization)

        payload: Dict[str, Any] = {"id": me}
        if body.display_name is not None:
            payload["display_name"] = str(body.display_name).strip()
        if body.push_enabled is not None:
            payload["push_enabled"] = bool(body.push_enabled)

        if len(payload.keys()) == 1:
            raise HTTPException(status_code=400, detail="No fields to update")

        resp = await sb_post(
            "/rest/v1/profiles",
            json=payload,
            prefer="resolution=merge-duplicates,return=representation",
            timeout=8.0,
        )
        if resp.status_code not in (200, 201):
            raise HTTPException(status_code=502, detail="Failed to update profile")

        row = _pick_row(resp) or await _fetch_profile_me(me)
        return AccountProfileMeResponse(
            user_id=me,
            display_name=(row.get("display_name") if isinstance(row.get("display_name"), str) else None),
            friend_code=(row.get("friend_code") if isinstance(row.get("friend_code"), str) else None),
            myprofile_code=(row.get("myprofile_code") if isinstance(row.get("myprofile_code"), str) else None),
            push_enabled=(bool(row.get("push_enabled")) if row.get("push_enabled") is not None else True),
            tutorial_completed=(bool(row.get("tutorial_completed")) if row.get("tutorial_completed") is not None else False),
            tutorial_skipped=(bool(row.get("tutorial_skipped")) if row.get("tutorial_skipped") is not None else False),
        )

    @app.post("/account/delete", response_model=AccountDeleteResponse)
    async def post_account_delete(
        authorization: Optional[str] = Header(default=None, alias="Authorization"),
    ) -> AccountDeleteResponse:
        me = await _require_user_id(authorization)

        deleted_tables: List[str] = []
        failed_tables: List[str] = []

        async def _try_delete(label: str, path: str, params: Dict[str, str]) -> None:
            try:
                resp = await sb_delete(path, params=params, prefer="return=minimal", timeout=8.0)
                if resp.status_code >= 300:
                    raise RuntimeError(resp.text[:800])
                deleted_tables.append(label)
            except Exception as exc:
                logger.warning("account/delete failed: %s %s", label, exc)
                failed_tables.append(label)

        await _try_delete("report_reads", "/rest/v1/report_reads", {"user_id": f"eq.{me}"})
        await _try_delete("friend_requests", "/rest/v1/friend_requests", {"or": f"(requester_user_id.eq.{me},requested_user_id.eq.{me})"})
        await _try_delete("friendships", "/rest/v1/friendships", {"or": f"(user_id.eq.{me},friend_user_id.eq.{me})"})
        await _try_delete("myprofile_requests", "/rest/v1/myprofile_requests", {"or": f"(requester_user_id.eq.{me},requested_user_id.eq.{me})"})
        await _try_delete("myprofile_links", "/rest/v1/myprofile_links", {"or": f"(owner_user_id.eq.{me},viewer_user_id.eq.{me})"})
        await _try_delete("myprofile_reports", "/rest/v1/myprofile_reports", {"user_id": f"eq.{me}"})
        await _try_delete("myweb_reports", "/rest/v1/myweb_reports", {"user_id": f"eq.{me}"})
        await _try_delete("emotions", "/rest/v1/emotions", {"user_id": f"eq.{me}"})
        await _try_delete("account_visibility_settings", "/rest/v1/account_visibility_settings", {"user_id": f"eq.{me}"})
        await _try_delete("profiles", "/rest/v1/profiles", {"id": f"eq.{me}"})

        return AccountDeleteResponse(
            user_id=me,
            deleted_tables=deleted_tables,
            failed_tables=failed_tables,
            sign_out_required=True,
        )
