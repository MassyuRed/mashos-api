"""Author-controlled sharing policy for active follower relationships."""
from __future__ import annotations

import os
from uuid import UUID

from fastapi import HTTPException

NO_STORE = {"Cache-Control": "private, no-store"}
CONTENT_VISIBILITY_FIELDS = frozenset({"can_view_pieces", "can_receive_emotion_notifications"})
_VISIBILITY_ROW_FIELDS = CONTENT_VISIBILITY_FIELDS | {"follower_user_id"}


def follower_sharing_enabled() -> bool:
    return os.getenv("FOLLOWER_SHARING_ENABLED") == "true"


def canonical_user_id(value: object) -> str:
    if not isinstance(value, str):
        raise ValueError("Invalid user ID")
    identifier = UUID(value)
    if identifier.int == 0 or str(identifier) != value:
        raise ValueError("Invalid user ID")
    return value


async def _visibility_rpc(name: str, arguments: dict):
    from supabase_client import sb_post_rpc

    try:
        response = await sb_post_rpc(name, arguments, timeout=8.0)
        if response.status_code == 200:
            return response.json()
        if response.status_code == 400:
            error = response.json()
            if isinstance(error, dict) and error.get("code") == "P0001":
                if error.get("message") == "FOLLOW_RELATION_NOT_FOUND":
                    raise HTTPException(status_code=404, detail="Follower not found", headers=NO_STORE)
                if error.get("message") == "FOLLOW_VISIBILITY_INVALID":
                    raise HTTPException(status_code=400, detail="Invalid sharing options", headers=NO_STORE)
    except HTTPException:
        raise
    except Exception:
        pass
    raise HTTPException(status_code=503, detail="Follower sharing unavailable", headers=NO_STORE)


def _validate_visibility_row(row: object) -> dict:
    try:
        if (type(row) is not dict or row.keys() != _VISIBILITY_ROW_FIELDS
                or any(type(row[field]) is not bool for field in CONTENT_VISIBILITY_FIELDS)):
            raise ValueError
        canonical_user_id(row["follower_user_id"])
    except ValueError:
        raise HTTPException(status_code=503, detail="Follower sharing unavailable", headers=NO_STORE) from None
    return row


async def list_author_follower_visibility(author_user_id: str) -> list[dict]:
    rows = await _visibility_rpc("follow_author_visibility_list_v1", {"p_author_user_id": author_user_id})
    if not isinstance(rows, list):
        raise HTTPException(status_code=503, detail="Follower sharing unavailable", headers=NO_STORE)
    return [_validate_visibility_row(row) for row in rows]


async def patch_author_follower_visibility(author_user_id: str, follower_user_id: str, changes: dict) -> dict:
    arguments = {
        "p_author_user_id": author_user_id,
        "p_follower_user_id": follower_user_id,
        "p_can_view_pieces": changes.get("can_view_pieces"),
        "p_can_receive_emotion_notifications": changes.get("can_receive_emotion_notifications"),
    }
    row = _validate_visibility_row(await _visibility_rpc("follow_author_visibility_patch_v1", arguments))
    if (row["follower_user_id"] != follower_user_id
            or any(row[field] is not value for field, value in changes.items())):
        raise HTTPException(status_code=503, detail="Follower sharing unavailable", headers=NO_STORE)
    return row


async def filter_piece_visible_owner_ids(viewer_user_id: str, owner_user_ids: set[str]) -> set[str]:
    """Return only currently visible authors; never use stale allowed choices on failure."""
    own = owner_user_ids & {viewer_user_id}
    other = owner_user_ids - own
    if not other:
        return own
    try:
        requested = {canonical_user_id(owner) for owner in other}
        viewer = canonical_user_id(viewer_user_id)
        rows = await _visibility_rpc("follow_piece_visible_owner_ids_v1", {
            "p_viewer_user_id": viewer,
            "p_owner_user_ids": sorted(requested),
        })
        if type(rows) is not list or len(rows) > len(requested):
            raise ValueError
        selected = {canonical_user_id(owner) for owner in rows}
        if not selected <= requested:
            raise ValueError
        return selected | own
    except ValueError:
        raise HTTPException(status_code=503, detail="Follower sharing unavailable", headers=NO_STORE) from None


async def hidden_share_code_owner_ids(owner_user_ids: set[str]) -> set[str]:
    """Retain opted-out public ID display when removing the legacy account switch."""
    if not owner_user_ids:
        return set()
    from supabase_client import sb_get

    hidden = set()
    try:
        owners = sorted(canonical_user_id(owner) for owner in owner_user_ids)
        for offset in range(0, len(owners), 200):
            chunk = owners[offset:offset + 200]
            response = await sb_get("/rest/v1/account_visibility_settings", params={
                "select": "user_id,is_friend_code_public",
                "user_id": f"in.({','.join(chunk)})",
                "limit": str(len(chunk)),
            }, timeout=8.0)
            rows = response.json()
            if (response.status_code != 200 or type(rows) is not list
                    or any(type(row) is not dict or row.get("user_id") not in chunk
                           for row in rows)):
                raise ValueError
            hidden.update(row["user_id"] for row in rows if row.get("is_friend_code_public") is not True)
    except Exception:
        return owner_user_ids
    return hidden
