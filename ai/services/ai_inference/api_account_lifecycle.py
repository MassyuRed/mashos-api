from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, Header, HTTPException, Query
from pydantic import BaseModel, Field

from api_account_visibility import _get_profile_row, _pick_row, _require_user_id
from supabase_client import sb_auth_headers, sb_delete, sb_get, sb_patch, sb_post

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


class AccountDisplayNameAvailabilityResponse(BaseModel):
    candidate: str
    available: bool = False


class AccountDeleteResponse(BaseModel):
    status: str = "ok"
    user_id: str
    deleted_tables: List[str] = Field(default_factory=list)
    failed_tables: List[str] = Field(default_factory=list)
    sign_out_required: bool = True


async def _fetch_profile_me(user_id: str) -> Dict[str, Any]:
    row = await _get_profile_row(user_id)
    return row or {}


def _extract_bearer_token(authorization: Optional[str]) -> Optional[str]:
    if not authorization:
        return None
    parts = str(authorization).split()
    if len(parts) == 2 and parts[0].lower() == "bearer" and parts[1]:
        return parts[1]
    return None


def _coerce_display_name(value: Any) -> Optional[str]:
    if isinstance(value, str):
        s = value.strip()
        if s:
            return s
    return None


def _looks_like_display_name_conflict(error_like: Any) -> bool:
    if isinstance(error_like, dict):
        raw = " ".join(
            str(error_like.get(key) or "") for key in ("code", "message", "details", "hint")
        )
    else:
        raw = str(error_like or "")
    lower = raw.lower()
    if "profiles_display_name_unique" in lower:
        return True
    return "display_name" in lower and any(
        token in lower for token in ("unique", "duplicate", "already exists", "already")
    )


async def _is_display_name_available(
    candidate: str,
    *,
    exclude_user_id: Optional[str] = None,
) -> bool:
    normalized = _coerce_display_name(candidate)
    if not normalized:
        return False

    params = {
        "select": "id",
        "display_name": f"eq.{normalized}",
        "limit": "1",
    }
    if exclude_user_id:
        params["id"] = f"neq.{exclude_user_id}"

    resp = await sb_get(
        "/rest/v1/profiles",
        params=params,
        timeout=5.0,
    )
    if resp.status_code >= 300:
        logger.error(
            "account/display-name/availability failed: status=%s body=%s",
            resp.status_code,
            resp.text[:1500],
        )
        raise HTTPException(status_code=502, detail="Failed to check display name availability")

    try:
        data = resp.json()
    except Exception:
        data = None

    if isinstance(data, list):
        return len(data) == 0
    if isinstance(data, dict):
        return not bool(data.get("id"))
    return True


def _raise_profile_update_error(resp: Any, *, operation: str) -> None:
    try:
        payload = resp.json()
    except Exception:
        payload = None

    if _looks_like_display_name_conflict(payload) or _looks_like_display_name_conflict(getattr(resp, "text", "")):
        raise HTTPException(status_code=409, detail="display_name already exists")

    logger.error(
        "account/profile/me %s failed: status=%s body=%s",
        operation,
        getattr(resp, "status_code", "?"),
        str(getattr(resp, "text", ""))[:1500],
    )
    raise HTTPException(status_code=502, detail="Failed to update profile")


async def _fetch_auth_user(authorization: Optional[str]) -> Dict[str, Any]:
    token = _extract_bearer_token(authorization)
    if not token:
        return {}

    try:
        resp = await sb_get(
            "/auth/v1/user",
            headers=sb_auth_headers(token),
            timeout=5.0,
        )
    except Exception as exc:
        logger.warning("account/profile/me auth fetch exception: %r", exc)
        return {}

    if resp.status_code != 200:
        logger.warning(
            "account/profile/me auth fetch failed: status=%s body=%s",
            resp.status_code,
            resp.text[:1500],
        )
        return {}

    try:
        data = resp.json()
    except Exception:
        return {}
    return data if isinstance(data, dict) else {}


async def _resolve_insert_display_name(
    authorization: Optional[str],
    *,
    requested_display_name: Optional[str] = None,
    existing_row: Optional[Dict[str, Any]] = None,
) -> str:
    requested = _coerce_display_name(requested_display_name)
    if requested:
        return requested

    current = _coerce_display_name((existing_row or {}).get("display_name"))
    if current:
        return current

    auth_user = await _fetch_auth_user(authorization)
    meta = auth_user.get("user_metadata") if isinstance(auth_user.get("user_metadata"), dict) else {}
    for key in ("display_name", "displayName", "name", "full_name"):
        value = _coerce_display_name(meta.get(key))
        if value:
            return value

    email = _coerce_display_name(auth_user.get("email"))
    if email and "@" in email:
        local = email.split("@", 1)[0].strip()
        if local:
            return local

    return "ユーザー"


async def _update_or_create_profile_me(
    user_id: str,
    *,
    authorization: Optional[str],
    display_name: Optional[str] = None,
    push_enabled: Optional[bool] = None,
) -> Dict[str, Any]:
    existing = await _fetch_profile_me(user_id)

    update_fields: Dict[str, Any] = {}
    if display_name is not None:
        update_fields["display_name"] = await _resolve_insert_display_name(
            authorization,
            requested_display_name=display_name,
            existing_row=existing,
        )
    if push_enabled is not None:
        update_fields["push_enabled"] = bool(push_enabled)

    if not update_fields:
        raise HTTPException(status_code=400, detail="No fields to update")

    if existing:
        resp = await sb_patch(
            "/rest/v1/profiles",
            params={"id": f"eq.{user_id}"},
            json=update_fields,
            prefer="return=representation",
            timeout=8.0,
        )
        if resp.status_code not in (200, 204):
            _raise_profile_update_error(resp, operation="patch")
        return _pick_row(resp) or await _fetch_profile_me(user_id)

    insert_payload: Dict[str, Any] = {
        "id": user_id,
        "display_name": await _resolve_insert_display_name(
            authorization,
            requested_display_name=display_name,
            existing_row=existing,
        ),
    }
    insert_payload.update(update_fields)

    resp = await sb_post(
        "/rest/v1/profiles",
        json=insert_payload,
        prefer="return=representation",
        timeout=8.0,
    )
    if resp.status_code not in (200, 201):
        _raise_profile_update_error(resp, operation="insert")

    return _pick_row(resp) or await _fetch_profile_me(user_id)


def register_account_lifecycle_routes(app: FastAPI) -> None:
    @app.get("/account/display-name/availability", response_model=AccountDisplayNameAvailabilityResponse)
    async def get_account_display_name_availability(
        candidate: str = Query(..., min_length=1, max_length=20),
        authorization: Optional[str] = Header(default=None, alias="Authorization"),
    ) -> AccountDisplayNameAvailabilityResponse:
        me = await _require_user_id(authorization)
        normalized = _coerce_display_name(candidate)
        if not normalized:
            raise HTTPException(status_code=400, detail="candidate is required")
        available = await _is_display_name_available(normalized, exclude_user_id=me)
        return AccountDisplayNameAvailabilityResponse(candidate=normalized, available=available)

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

        row = await _update_or_create_profile_me(
            me,
            authorization=authorization,
            display_name=body.display_name,
            push_enabled=body.push_enabled,
        )
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
