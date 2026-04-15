# -*- coding: utf-8 -*-
"""Legacy Friends / EmotionLog API for Cocolon (MashOS / FastAPI)

This module keeps legacy ``/friends/*`` routes for compatibility while serving
the current EmotionLog / emotion-notification behavior used by the app.

Implements the minimum endpoints required for the MVP:

- POST /friends/request
    Body: {"friend_code": "XXXXXXXXXX"}
    Creates a pending friend request.

- POST /friends/requests/{id}/accept
    The receiver accepts a pending request. Creates friendships (both directions).

- POST /friends/requests/{id}/reject
    The receiver rejects a pending request.

Notes
-----
* The caller must pass Supabase Auth access token via:
    Authorization: Bearer <access_token>
  We resolve the user_id by calling Supabase Auth `/auth/v1/user`.
* DB writes are performed via Supabase PostgREST using the service role key.
* We do NOT expose secret memo content anywhere.
"""

from __future__ import annotations

import asyncio
import logging
import os
from datetime import datetime, timezone, timedelta
from typing import Any, Dict, List, Optional

import httpx
from fastapi import FastAPI, Header, HTTPException, Path
from fastapi.encoders import jsonable_encoder
from pydantic import BaseModel, Field

# Reuse auth helpers & config checks from emotion submit module
from api_emotion_submit import (
    _ensure_supabase_config,
    _extract_bearer_token,
    _resolve_user_id_from_token,
    _fetch_profile_display_name,
    _fetch_push_tokens_for_users,
    _send_fcm_push,
)
from astor_friend_feed_store import (
    fetch_latest_ready_friend_feed_summary as fetch_latest_ready_emotion_log_feed_summary,
    select_friend_feed_items as select_emotion_log_feed_items,
)
from response_microcache import get_or_compute, invalidate_prefix
from supabase_client import sb_count, sb_delete, sb_get, sb_patch, sb_post

logger = logging.getLogger("friends_api")

SUPABASE_URL = os.getenv("SUPABASE_URL", "").rstrip("/")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")
FRIENDS_MANAGE_CACHE_TTL_SECONDS = 5.0
FRIENDS_UNREAD_CACHE_TTL_SECONDS = 5.0


# ----------------------------
# Pydantic models
# ----------------------------


class FriendRequestCreateBody(BaseModel):
    friend_code: str = Field(..., min_length=4, max_length=64, description="Target user's friend_code")


class FriendRequestCreateResponse(BaseModel):
    status: str = Field(..., description="ok | already_friends | already_pending")
    request_id: Optional[int] = None
    requested_user_id: Optional[str] = None
    requested_display_name: Optional[str] = None


class FriendRequestActionResponse(BaseModel):
    status: str = Field(..., description="ok")
    request_id: int


class FriendRemoveBody(BaseModel):
    friend_user_id: str = Field(..., min_length=1, max_length=128, description="Target user's user id")


class FriendRemoveResponse(BaseModel):
    status: str = Field(..., description="ok")
    friend_user_id: str




class FriendNotificationSettingUpsertBody(BaseModel):
    is_enabled: bool = Field(..., description="true: receive notifications from this friend, false: mute")


class FriendNotificationSettingItem(BaseModel):
    friend_user_id: str = Field(..., description="Friend (owner) user id")
    is_enabled: bool = Field(..., description="Whether notifications are enabled for this friend")


class FriendNotificationSettingResponse(BaseModel):
    status: str = Field(..., description="ok")
    friend_user_id: str
    is_enabled: bool


class FriendNotificationSettingsResponse(BaseModel):
    status: str = Field(..., description="ok")
    settings: List[FriendNotificationSettingItem]


# Canonical aliases for the current emotion-notification behavior.
EmotionNotificationSettingUpsertBody = FriendNotificationSettingUpsertBody
EmotionNotificationSettingItem = FriendNotificationSettingItem
EmotionNotificationSettingResponse = FriendNotificationSettingResponse
EmotionNotificationSettingsResponse = FriendNotificationSettingsResponse


class FriendUnreadStatusResponse(BaseModel):
    status: str = Field(default="ok", description="ok")
    feed_unread: bool = Field(default=False, description="Whether friend feed has unread items")
    requests_unread: bool = Field(default=False, description="Whether incoming friend requests have unread items")
    incoming_pending_count: int = Field(default=0, description="Incoming pending friend request count")
    feed_last_read_at: Optional[str] = None
    requests_last_read_at: Optional[str] = None


class FriendUnreadMarkReadResponse(BaseModel):
    status: str = Field(default="ok", description="ok")
    last_read_at: Optional[str] = None


class FriendUnreadMarkReadBody(BaseModel):
    last_seen_created_at: Optional[str] = Field(
        default=None,
        description="Latest friend feed created_at that was actually shown to the user",
    )

# ----------------------------
# Supabase helpers
# ----------------------------


def _sb_headers_json(*, prefer: Optional[str] = None) -> Dict[str, str]:
    _ensure_supabase_config()
    h = {
        "apikey": SUPABASE_SERVICE_ROLE_KEY,
        "Authorization": f"Bearer {SUPABASE_SERVICE_ROLE_KEY}",
        "Content-Type": "application/json",
    }
    if prefer:
        h["Prefer"] = prefer
    return h


async def _sb_get(
    path: str,
    *,
    params: Optional[Dict[str, str]] = None,
    prefer: Optional[str] = None,
) -> httpx.Response:
    return await sb_get(
        path,
        params=params,
        prefer=prefer,
        timeout=8.0,
        headers=_sb_headers_json(prefer=prefer),
    )


async def _sb_post(path: str, *, json: Any, prefer: Optional[str] = None) -> httpx.Response:
    return await sb_post(path, json=json, prefer=prefer, timeout=8.0, headers=_sb_headers_json(prefer=prefer))


async def _sb_patch(path: str, *, params: Dict[str, str], json: Any, prefer: Optional[str] = None) -> httpx.Response:
    return await sb_patch(path, params=params, json=json, prefer=prefer, timeout=8.0, headers=_sb_headers_json(prefer=prefer))

async def _sb_delete(path: str, *, params: Dict[str, str], prefer: Optional[str] = None) -> httpx.Response:
    return await sb_delete(path, params=params, prefer=prefer, timeout=8.0, headers=_sb_headers_json(prefer=prefer))


async def _invalidate_friend_api_caches(*user_ids: str) -> None:
    seen = set()
    for raw in user_ids:
        uid = str(raw or "").strip()
        if not uid or uid in seen:
            continue
        seen.add(uid)
        await invalidate_prefix(f"friends:manage:{uid}")
        await invalidate_prefix(f"friends:unread:{uid}")


async def _fetch_incoming_pending_count(user_id: str) -> int:
    try:
        return int(
            await sb_count(
                "/rest/v1/friend_requests",
                params={
                    "requested_user_id": f"eq.{user_id}",
                    "status": "eq.pending",
                    "select": "id",
                },
                timeout=8.0,
            )
        )
    except Exception as exc:
        logger.warning("Supabase incoming friend_requests count failed: %s", exc)
        return 0


def _parse_content_range_total(content_range: str) -> Optional[int]:
    raw = str(content_range or "").strip()
    if not raw or "/" not in raw:
        return None
    tail = raw.split("/")[-1].strip()
    if not tail or tail == "*":
        return None
    try:
        return int(tail)
    except Exception:
        return None


def _parse_iso_utc(value: Any) -> Optional[datetime]:
    s = str(value or "").strip()
    if not s:
        return None
    try:
        if s.endswith("Z"):
            s = s[:-1] + "+00:00"
        dt = datetime.fromisoformat(s)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)
    except Exception:
        return None


def _has_newer_iso(candidate_iso: Optional[str], cursor_iso: Optional[str]) -> bool:
    candidate_dt = _parse_iso_utc(candidate_iso)
    if candidate_dt is None:
        return False
    cursor_dt = _parse_iso_utc(cursor_iso) if cursor_iso else None
    if cursor_dt is None:
        return True
    return candidate_dt > cursor_dt


async def _fetch_latest_pending_request_head_and_count(user_id: str) -> Tuple[Optional[str], int]:
    try:
        resp = await _sb_get(
            "/rest/v1/friend_requests",
            params={
                "select": "id,created_at",
                "requested_user_id": f"eq.{user_id}",
                "status": "eq.pending",
                "order": "created_at.desc",
                "limit": "1",
            },
            prefer="count=exact",
        )
    except Exception as exc:
        logger.warning("Supabase friend_requests head+count failed: %s", exc)
        latest_created_at = await _latest_friend_request_created_at(user_id)
        total_count = await _fetch_incoming_pending_count(user_id)
        return latest_created_at, total_count

    if resp.status_code >= 300:
        logger.warning("Supabase friend_requests head+count failed: %s %s", resp.status_code, resp.text[:1500])
        latest_created_at = await _latest_friend_request_created_at(user_id)
        total_count = await _fetch_incoming_pending_count(user_id)
        return latest_created_at, total_count

    rows = resp.json()
    rows = rows if isinstance(rows, list) else []
    latest_created_at: Optional[str] = None
    if rows and isinstance(rows[0], dict):
        value = rows[0].get("created_at")
        latest_created_at = str(value).strip() if value else None

    total_count = _parse_content_range_total(resp.headers.get("content-range") or resp.headers.get("Content-Range") or "")
    if total_count is None:
        total_count = await _fetch_incoming_pending_count(user_id)
    return latest_created_at, max(0, int(total_count or 0))


async def get_friend_unread_status_payload_for_user(user_id: str) -> Dict[str, Any]:
    uid = str(user_id or "").strip()
    cache_key = f"friends:unread:{uid}"

    async def _build_payload() -> Dict[str, Any]:
        feed_last_read_at, requests_last_read_at, latest_feed_created_at, pending_request_head = await asyncio.gather(
            _fetch_last_read_at("friend_feed_reads", uid),
            _fetch_last_read_at("friend_request_reads", uid),
            _latest_emotion_log_feed_created_at(uid),
            _fetch_latest_pending_request_head_and_count(uid),
        )

        latest_request_created_at, incoming_pending_count = pending_request_head

        response = FriendUnreadStatusResponse(
            feed_unread=_has_newer_iso(latest_feed_created_at, feed_last_read_at),
            requests_unread=_has_newer_iso(latest_request_created_at, requests_last_read_at),
            incoming_pending_count=int(incoming_pending_count or 0),
            feed_last_read_at=feed_last_read_at,
            requests_last_read_at=requests_last_read_at,
        )
        return jsonable_encoder(response)

    return await get_or_compute(cache_key, FRIENDS_UNREAD_CACHE_TTL_SECONDS, _build_payload)


async def _lookup_profile_by_friend_code(friend_code: str) -> Optional[Dict[str, Any]]:
    """Return {id, display_name} or None"""
    resp = await _sb_get(
        "/rest/v1/profiles",
        params={
            "select": "id,display_name,friend_code",
            "friend_code": f"eq.{friend_code}",
            "limit": "1",
        },
    )
    if resp.status_code >= 300:
        logger.error("Supabase profiles lookup failed: %s %s", resp.status_code, resp.text[:1500])
        raise HTTPException(status_code=502, detail="Failed to look up friend code")
    rows = resp.json()
    if isinstance(rows, list) and rows:
        return rows[0]
    return None


async def _are_already_friends(user_id: str, friend_user_id: str) -> bool:
    resp = await _sb_get(
        "/rest/v1/friendships",
        params={
            "select": "user_id",
            "user_id": f"eq.{user_id}",
            "friend_user_id": f"eq.{friend_user_id}",
            "limit": "1",
        },
    )
    if resp.status_code >= 300:
        logger.error("Supabase friendships select failed: %s %s", resp.status_code, resp.text[:1500])
        raise HTTPException(status_code=502, detail="Failed to check friendship")
    rows = resp.json()
    return bool(isinstance(rows, list) and rows)


async def _find_existing_pending_request(user_a: str, user_b: str) -> Optional[Dict[str, Any]]:
    """Return a pending request for the pair in either direction."""
    # PostgREST OR syntax
    or_expr = (
        f"and(requester_user_id.eq.{user_a},requested_user_id.eq.{user_b}),"
        f"and(requester_user_id.eq.{user_b},requested_user_id.eq.{user_a})"
    )
    resp = await _sb_get(
        "/rest/v1/friend_requests",
        params={
            "select": "id,requester_user_id,requested_user_id,status,created_at",
            "status": "eq.pending",
            "or": f"({or_expr})",
            "limit": "1",
        },
    )
    if resp.status_code >= 300:
        logger.error("Supabase friend_requests select failed: %s %s", resp.status_code, resp.text[:1500])
        raise HTTPException(status_code=502, detail="Failed to query friend requests")
    rows = resp.json()
    if isinstance(rows, list) and rows:
        return rows[0]
    return None


async def _get_friend_request_by_id(req_id: int) -> Dict[str, Any]:
    resp = await _sb_get(
        "/rest/v1/friend_requests",
        params={
            "select": "id,requester_user_id,requested_user_id,status,created_at,responded_at",
            "id": f"eq.{req_id}",
            "limit": "1",
        },
    )
    if resp.status_code >= 300:
        logger.error("Supabase friend_requests get failed: %s %s", resp.status_code, resp.text[:1500])
        raise HTTPException(status_code=502, detail="Failed to query friend request")
    rows = resp.json()
    if not (isinstance(rows, list) and rows):
        raise HTTPException(status_code=404, detail="Friend request not found")
    return rows[0]


async def _insert_friendships_bidirectional(user_a: str, user_b: str) -> None:
    payload = [
        {"user_id": user_a, "friend_user_id": user_b},
        {"user_id": user_b, "friend_user_id": user_a},
    ]
    resp = await _sb_post(
        "/rest/v1/friendships",
        json=payload,
        prefer="return=minimal",
    )

    # 201/204 ok. 409 can happen if already exists; treat as ok.
    if resp.status_code in (200, 201, 204):
        return
    if resp.status_code == 409:
        logger.info("friendships already exist for %s<->%s", user_a, user_b)
        return
    logger.error("Supabase insert friendships failed: %s %s", resp.status_code, resp.text[:1500])
    raise HTTPException(status_code=502, detail="Failed to create friendship")


async def _delete_friendships_bidirectional(user_a: str, user_b: str) -> None:
    """Delete friendships rows in both directions (idempotent)."""
    for u, f in ((user_a, user_b), (user_b, user_a)):
        resp = await _sb_delete(
            "/rest/v1/friendships",
            params={
                "user_id": f"eq.{u}",
                "friend_user_id": f"eq.{f}",
            },
            prefer="return=minimal",
        )
        # 204 No Content even when nothing deleted; treat as ok
        if resp.status_code in (200, 204):
            continue
        # Some PostgREST setups may return 404; treat as idempotent ok
        if resp.status_code == 404:
            continue
        logger.error("Supabase delete friendships failed: %s %s", resp.status_code, resp.text[:1500])
        raise HTTPException(status_code=502, detail="Failed to remove friendship")


JST = timezone(timedelta(hours=9))


def _in_list(values: List[str]) -> str:
    xs: List[str] = []
    for raw in values:
        v = str(raw or "").strip().replace('"', '\"')
        if not v:
            continue
        xs.append(f'"{v}"')
    return f"in.({','.join(xs)})"


def _dedupe_user_ids(values: List[str]) -> List[str]:
    out: List[str] = []
    seen = set()
    for raw in values or []:
        uid = str(raw or "").strip()
        if not uid or uid in seen:
            continue
        seen.add(uid)
        out.append(uid)
    return out


def _format_emotion_log_feed_time_label(iso_value: Any) -> str:
    s = str(iso_value or "").strip()
    if not s:
        return ""
    try:
        if s.endswith("Z"):
            s = s[:-1] + "+00:00"
        dt = datetime.fromisoformat(s)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        dt = dt.astimezone(JST)
        return f"{dt.month}/{dt.day} {dt.hour:02d}:{dt.minute:02d}"
    except Exception:
        return ""


def _normalize_emotion_log_feed_items(raw_items: Any) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    if not isinstance(raw_items, list):
        return out
    for it in raw_items:
        if not isinstance(it, dict):
            continue
        emotion_type = str(it.get("type") or it.get("emotion") or "").strip()
        if not emotion_type:
            continue
        item: Dict[str, Any] = {"type": emotion_type}
        strength = str(it.get("strength") or "").strip().lower()
        if strength in {"weak", "medium", "strong"}:
            item["strength"] = strength
        out.append(item)
    return out


def _build_emotion_log_feed_response_items(rows: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    items: List[Dict[str, Any]] = []
    for row in rows or []:
        if not isinstance(row, dict):
            continue
        feed_id = row.get("id")
        owner_name = str(row.get("owner_name") or row.get("ownerName") or "").strip() or "Friend"
        created_at = row.get("created_at") or row.get("createdAt")
        items.append(
            {
                "id": feed_id,
                "ownerName": owner_name,
                "items": _normalize_emotion_log_feed_items(row.get("items")),
                "timeLabel": _format_emotion_log_feed_time_label(created_at),
                "createdAt": created_at,
                "created_at": created_at,
            }
        )
    return items


def _summary_latest_emotion_log_feed_created_at(summary: Optional[Dict[str, Any]]) -> Optional[str]:
    if not isinstance(summary, dict):
        return None

    payload = summary.get("payload") if isinstance(summary.get("payload"), dict) else summary
    if not isinstance(payload, dict):
        payload = {}

    latest_created_at = str(payload.get("latest_created_at") or "").strip()
    if latest_created_at:
        return latest_created_at

    raw_items = payload.get("items") if isinstance(payload.get("items"), list) else []
    for item in raw_items:
        if not isinstance(item, dict):
            continue
        value = str(item.get("created_at") or item.get("createdAt") or "").strip()
        if value:
            return value

    fallback = str(
        summary.get("published_at")
        or summary.get("updated_at")
        or summary.get("created_at")
        or ""
    ).strip()
    return fallback or None


async def _fetch_live_emotion_log_feed_rows(viewer_user_id: str, *, limit: int = 20) -> List[Dict[str, Any]]:
    resp = await _sb_get(
        "/rest/v1/friend_emotion_feed",
        params={
            "select": "id,owner_user_id,owner_name,items,created_at",
            "viewer_user_id": f"eq.{viewer_user_id}",
            "order": "created_at.desc",
            "limit": str(max(1, min(int(limit or 20), 50))),
        },
    )
    if resp.status_code >= 300:
        logger.error("Supabase friend_emotion_feed select failed (emotion log feed): %s %s", resp.status_code, resp.text[:1500])
        raise HTTPException(status_code=502, detail="Failed to query emotion log feed")
    rows = resp.json()
    return rows if isinstance(rows, list) else []


async def _fetch_profiles_map(user_ids: List[str]) -> Dict[str, Dict[str, Any]]:
    ids: List[str] = []
    seen = set()
    for raw in user_ids or []:
        uid = str(raw or "").strip()
        if not uid or uid in seen:
            continue
        seen.add(uid)
        ids.append(uid)
    if not ids:
        return {}

    resp = await _sb_get(
        "/rest/v1/profiles",
        params={
            "select": "id,display_name,friend_code",
            "id": _in_list(ids),
        },
    )
    if resp.status_code >= 300:
        logger.error("Supabase profiles map select failed: %s %s", resp.status_code, resp.text[:1500])
        raise HTTPException(status_code=502, detail="Failed to query profiles")

    rows = resp.json()
    out: Dict[str, Dict[str, Any]] = {}
    if isinstance(rows, list):
        for row in rows:
            if not isinstance(row, dict):
                continue
            uid = str(row.get("id") or "").strip()
            if not uid:
                continue
            out[uid] = {
                "display_name": row.get("display_name") or None,
                "friend_code": row.get("friend_code") or None,
            }
    return out


async def _fetch_or_create_my_profile(user_id: str) -> Dict[str, Any]:
    resp = await _sb_get(
        "/rest/v1/profiles",
        params={
            "select": "id,display_name,friend_code",
            "id": f"eq.{user_id}",
            "limit": "1",
        },
    )
    if resp.status_code >= 300:
        logger.error("Supabase my profile select failed: %s %s", resp.status_code, resp.text[:1500])
        raise HTTPException(status_code=502, detail="Failed to query profile")

    rows = resp.json()
    if isinstance(rows, list) and rows:
        row = rows[0] if isinstance(rows[0], dict) else {}
        return {
            "id": user_id,
            "displayName": row.get("display_name") or "",
            "friendCode": row.get("friend_code") or "",
        }

    try:
        ins = await _sb_post(
            "/rest/v1/profiles",
            json={"id": user_id, "display_name": "User"},
            prefer="return=minimal",
        )
        if ins.status_code not in (200, 201, 204, 409):
            logger.warning("profiles insert fallback failed: %s %s", ins.status_code, ins.text[:1500])
    except Exception as exc:
        logger.warning("profiles insert fallback error: %s", exc)

    resp2 = await _sb_get(
        "/rest/v1/profiles",
        params={
            "select": "id,display_name,friend_code",
            "id": f"eq.{user_id}",
            "limit": "1",
        },
    )
    if resp2.status_code >= 300:
        logger.error("Supabase my profile refetch failed: %s %s", resp2.status_code, resp2.text[:1500])
        raise HTTPException(status_code=502, detail="Failed to query profile")

    rows2 = resp2.json()
    row2 = rows2[0] if isinstance(rows2, list) and rows2 and isinstance(rows2[0], dict) else {}
    return {
        "id": user_id,
        "displayName": row2.get("display_name") or "",
        "friendCode": row2.get("friend_code") or "",
    }


async def _fetch_manage_friendship_rows(user_id: str) -> List[Dict[str, Any]]:
    resp = await _sb_get(
        "/rest/v1/friendships",
        params={
            "select": "friend_user_id,created_at",
            "user_id": f"eq.{user_id}",
            "order": "created_at.desc",
        },
    )
    if resp.status_code >= 300:
        logger.error("Supabase friendships select failed: %s %s", resp.status_code, resp.text[:1500])
        raise HTTPException(status_code=502, detail="Failed to query friendships")

    rows = resp.json()
    return rows if isinstance(rows, list) else []


async def _fetch_manage_request_rows_legacy(user_id: str) -> List[Dict[str, Any]]:
    in_resp, out_resp = await asyncio.gather(
        _sb_get(
            "/rest/v1/friend_requests",
            params={
                "select": "id,requester_user_id,requested_user_id,created_at",
                "requested_user_id": f"eq.{user_id}",
                "status": "eq.pending",
                "order": "created_at.desc",
            },
        ),
        _sb_get(
            "/rest/v1/friend_requests",
            params={
                "select": "id,requester_user_id,requested_user_id,created_at",
                "requester_user_id": f"eq.{user_id}",
                "status": "eq.pending",
                "order": "created_at.desc",
            },
        ),
    )
    if in_resp.status_code >= 300:
        logger.error("Supabase incoming friend_requests select failed: %s %s", in_resp.status_code, in_resp.text[:1500])
        raise HTTPException(status_code=502, detail="Failed to query friend requests")
    if out_resp.status_code >= 300:
        logger.error("Supabase outgoing friend_requests select failed: %s %s", out_resp.status_code, out_resp.text[:1500])
        raise HTTPException(status_code=502, detail="Failed to query friend requests")

    rows: List[Dict[str, Any]] = []
    incoming_payload = in_resp.json()
    outgoing_payload = out_resp.json()
    incoming_rows = incoming_payload if isinstance(incoming_payload, list) else []
    outgoing_rows = outgoing_payload if isinstance(outgoing_payload, list) else []
    for row in incoming_rows:
        if isinstance(row, dict):
            rows.append(row)
    for row in outgoing_rows:
        if isinstance(row, dict):
            rows.append(row)
    rows.sort(key=lambda row: str(row.get("created_at") or ""), reverse=True)
    return rows


async def _fetch_manage_request_rows(user_id: str) -> List[Dict[str, Any]]:
    try:
        resp = await _sb_get(
            "/rest/v1/friend_requests",
            params={
                "select": "id,requester_user_id,requested_user_id,created_at",
                "status": "eq.pending",
                "or": f"(requested_user_id.eq.{user_id},requester_user_id.eq.{user_id})",
                "order": "created_at.desc",
            },
        )
    except Exception as exc:
        logger.warning("Supabase combined friend_requests select failed, falling back: %s", exc)
        return await _fetch_manage_request_rows_legacy(user_id)

    if resp.status_code >= 300:
        logger.warning(
            "Supabase combined friend_requests select failed, falling back: %s %s",
            resp.status_code,
            resp.text[:1500],
        )
        return await _fetch_manage_request_rows_legacy(user_id)

    rows = resp.json()
    return rows if isinstance(rows, list) else []


async def _fetch_emotion_notification_map(
    viewer_user_id: str,
    owner_user_ids: Optional[List[str]] = None,
) -> Dict[str, bool]:
    ids_filter = _dedupe_user_ids(owner_user_ids or []) if owner_user_ids is not None else None
    if owner_user_ids is not None and not ids_filter:
        return {}

    params = {
        "select": "owner_user_id,is_enabled",
        "viewer_user_id": f"eq.{viewer_user_id}",
        "order": "owner_user_id.asc",
    }
    if ids_filter is not None:
        params["owner_user_id"] = _in_list(ids_filter)

    try:
        resp = await _sb_get(
            "/rest/v1/friend_notification_settings",
            params=params,
        )
    except Exception as exc:
        if ids_filter is not None:
            logger.warning("Failed to query filtered friend notification settings, retrying unfiltered: %s", exc)
            return await _fetch_friend_notification_map(viewer_user_id, owner_user_ids=None)
        logger.warning("Failed to query friend notification settings: %s", exc)
        return {}

    if resp.status_code == 404:
        return {}
    if resp.status_code >= 300:
        if ids_filter is not None:
            logger.warning(
                "Supabase select filtered friend_notification_settings failed, retrying unfiltered: %s %s",
                resp.status_code,
                resp.text[:1500],
            )
            return await _fetch_friend_notification_map(viewer_user_id, owner_user_ids=None)
        logger.warning(
            "Supabase select friend_notification_settings failed: %s %s",
            resp.status_code,
            resp.text[:1500],
        )
        return {}

    rows = resp.json()
    out: Dict[str, bool] = {}
    if isinstance(rows, list):
        for row in rows:
            if not isinstance(row, dict):
                continue
            fid = str(row.get("owner_user_id") or "").strip()
            if not fid:
                continue
            enabled = row.get("is_enabled")
            out[fid] = True if enabled is None else bool(enabled)
    return out


# ----------------------------
# Route registration
# ----------------------------




async def _fetch_last_read_at(table_name: str, user_id: str) -> Optional[str]:
    resp = await _sb_get(
        f"/rest/v1/{table_name}",
        params={
            "select": "last_read_at",
            "user_id": f"eq.{user_id}",
            "limit": "1",
        },
    )
    if resp.status_code == 404:
        return None
    if resp.status_code >= 300:
        logger.warning("Supabase %s select failed: %s %s", table_name, resp.status_code, resp.text[:1500])
        return None
    rows = resp.json()
    if isinstance(rows, list) and rows and isinstance(rows[0], dict):
        value = rows[0].get("last_read_at")
        return str(value).strip() if value else None
    if isinstance(rows, dict):
        value = rows.get("last_read_at")
        return str(value).strip() if value else None
    return None


async def _upsert_last_read_at(table_name: str, user_id: str, last_read_at: str) -> bool:
    resp = await _sb_post(
        f"/rest/v1/{table_name}?on_conflict=user_id",
        json={"user_id": user_id, "last_read_at": last_read_at},
        prefer="resolution=merge-duplicates,return=minimal",
    )
    if resp.status_code == 404:
        return False
    return resp.status_code in (200, 201)


async def _latest_emotion_log_feed_created_at(user_id: str) -> Optional[str]:
    resp = await _sb_get(
        "/rest/v1/friend_emotion_feed",
        params={
            "select": "created_at",
            "viewer_user_id": f"eq.{user_id}",
            "order": "created_at.desc",
            "limit": "1",
        },
    )
    if resp.status_code >= 300:
        logger.warning("Supabase friend_emotion_feed latest failed (emotion log): %s %s", resp.status_code, resp.text[:1500])
        return None
    rows = resp.json()
    if isinstance(rows, list) and rows and isinstance(rows[0], dict):
        value = rows[0].get("created_at")
        return str(value).strip() if value else None
    return None


async def _latest_friend_request_created_at(user_id: str) -> Optional[str]:
    resp = await _sb_get(
        "/rest/v1/friend_requests",
        params={
            "select": "created_at",
            "requested_user_id": f"eq.{user_id}",
            "status": "eq.pending",
            "order": "created_at.desc",
            "limit": "1",
        },
    )
    if resp.status_code >= 300:
        logger.warning("Supabase friend_requests latest failed: %s %s", resp.status_code, resp.text[:1500])
        return None
    rows = resp.json()
    if isinstance(rows, list) and rows and isinstance(rows[0], dict):
        value = rows[0].get("created_at")
        return str(value).strip() if value else None
    return None


async def _has_newer_emotion_log_feed(user_id: str, last_read_at: str) -> bool:
    resp = await _sb_get(
        "/rest/v1/friend_emotion_feed",
        params={
            "select": "id,created_at",
            "viewer_user_id": f"eq.{user_id}",
            "created_at": f"gt.{last_read_at}",
            "order": "created_at.desc",
            "limit": "1",
        },
    )
    if resp.status_code >= 300:
        logger.warning("Supabase friend_emotion_feed unread failed (emotion log): %s %s", resp.status_code, resp.text[:1500])
        return False
    rows = resp.json()
    return bool(isinstance(rows, list) and rows)


async def _has_newer_friend_requests(user_id: str, last_read_at: str) -> bool:
    resp = await _sb_get(
        "/rest/v1/friend_requests",
        params={
            "select": "id,created_at",
            "requested_user_id": f"eq.{user_id}",
            "status": "eq.pending",
            "created_at": f"gt.{last_read_at}",
            "order": "created_at.desc",
            "limit": "1",
        },
    )
    if resp.status_code >= 300:
        logger.warning("Supabase friend_requests unread failed: %s %s", resp.status_code, resp.text[:1500])
        return False
    rows = resp.json()
    return bool(isinstance(rows, list) and rows)


# Backward-compatible aliases for legacy helper names.
_format_friend_feed_time_label = _format_emotion_log_feed_time_label
_normalize_friend_feed_emotions = _normalize_emotion_log_feed_items
_build_friend_feed_response_items = _build_emotion_log_feed_response_items
_summary_latest_friend_feed_created_at = _summary_latest_emotion_log_feed_created_at
_fetch_live_friend_feed_rows = _fetch_live_emotion_log_feed_rows
_fetch_friend_notification_map = _fetch_emotion_notification_map
_latest_friend_feed_created_at = _latest_emotion_log_feed_created_at
_has_newer_friend_feed = _has_newer_emotion_log_feed

def register_friend_routes(app: FastAPI) -> None:
    """Register friend request endpoints on the given FastAPI app."""

    @app.post("/friends/request", response_model=FriendRequestCreateResponse)
    async def create_friend_request(
        body: FriendRequestCreateBody,
        authorization: Optional[str] = Header(default=None, alias="Authorization"),
    ) -> FriendRequestCreateResponse:
        access_token = _extract_bearer_token(authorization)
        if not access_token:
            raise HTTPException(status_code=401, detail="Authorization header with Bearer token is required")

        requester_user_id = await _resolve_user_id_from_token(access_token)
        friend_code = body.friend_code.strip()
        if not friend_code:
            raise HTTPException(status_code=400, detail="friend_code is required")

        target_profile = await _lookup_profile_by_friend_code(friend_code)
        if not target_profile:
            raise HTTPException(status_code=404, detail="User not found for the given friend_code")

        requested_user_id = str(target_profile.get("id") or "")
        requested_display_name = target_profile.get("display_name") or None

        if not requested_user_id:
            raise HTTPException(status_code=404, detail="User not found for the given friend_code")

        if requested_user_id == requester_user_id:
            raise HTTPException(status_code=400, detail="You cannot send a friend request to yourself")

        # If already friends -> idempotent ok
        if await _are_already_friends(requester_user_id, requested_user_id):
            return FriendRequestCreateResponse(
                status="already_friends",
                request_id=None,
                requested_user_id=requested_user_id,
                requested_display_name=requested_display_name,
            )

        # If pending already exists (either direction) -> return that
        existing = await _find_existing_pending_request(requester_user_id, requested_user_id)
        if existing:
            return FriendRequestCreateResponse(
                status="already_pending",
                request_id=int(existing.get("id")),
                requested_user_id=requested_user_id,
                requested_display_name=requested_display_name,
            )

        # Create request
        payload = {
            "requester_user_id": requester_user_id,
            "requested_user_id": requested_user_id,
            "status": "pending",
        }
        resp = await _sb_post(
            "/rest/v1/friend_requests",
            json=payload,
            prefer="return=representation",
        )
        if resp.status_code not in (200, 201):
            # Unique pending pair index may fire -> try to return existing pending
            if resp.status_code == 409:
                existing2 = await _find_existing_pending_request(requester_user_id, requested_user_id)
                if existing2:
                    return FriendRequestCreateResponse(
                        status="already_pending",
                        request_id=int(existing2.get("id")),
                        requested_user_id=requested_user_id,
                        requested_display_name=requested_display_name,
                    )
            logger.error("Supabase insert friend_requests failed: %s %s", resp.status_code, resp.text[:1500])
            raise HTTPException(status_code=502, detail="Failed to create friend request")

        data = resp.json()
        row = data[0] if isinstance(data, list) and data else (data if isinstance(data, dict) else {})
        request_id = int(row.get("id")) if row.get("id") is not None else None

        # Push通知（best-effort）：申請先ユーザーへ通知
        try:
            token_map = await _fetch_push_tokens_for_users([requested_user_id])
            tokens = list(token_map.values())
            if tokens:
                requester_name = await _fetch_profile_display_name(requester_user_id)
                requester_label = (requester_name or "").strip() or "フレンド"
                if requester_label == "Friend":
                    requester_label = "フレンド"

                body_text = f"{requester_label}さんからフレンド通知が届きました"
                data_payload: Dict[str, str] = {"type": "friend_request"}
                if request_id is not None:
                    data_payload["request_id"] = str(request_id)

                await _send_fcm_push(tokens=tokens, title="Cocolon", body=body_text, data=data_payload)
        except Exception as exc:
            logger.warning("Failed to send friend request push: %s", exc)

        await _invalidate_friend_api_caches(requester_user_id, requested_user_id)
        return FriendRequestCreateResponse(
            status="ok",
            request_id=request_id,
            requested_user_id=requested_user_id,
            requested_display_name=requested_display_name,
        )

    @app.post("/friends/requests/{request_id}/accept", response_model=FriendRequestActionResponse)
    async def accept_friend_request(
        request_id: int = Path(..., ge=1),
        authorization: Optional[str] = Header(default=None, alias="Authorization"),
    ) -> FriendRequestActionResponse:
        access_token = _extract_bearer_token(authorization)
        if not access_token:
            raise HTTPException(status_code=401, detail="Authorization header with Bearer token is required")

        me = await _resolve_user_id_from_token(access_token)
        req = await _get_friend_request_by_id(request_id)

        if req.get("status") != "pending":
            raise HTTPException(status_code=400, detail="Friend request is not pending")

        requested_user_id = str(req.get("requested_user_id"))
        requester_user_id = str(req.get("requester_user_id"))
        if requested_user_id != me:
            raise HTTPException(status_code=403, detail="You are not allowed to accept this request")

        now = datetime.now(timezone.utc).isoformat()
        # Update request status
        resp = await _sb_patch(
            "/rest/v1/friend_requests",
            params={"id": f"eq.{request_id}"},
            json={"status": "accepted", "responded_at": now},
            prefer="return=minimal",
        )
        if resp.status_code not in (200, 204):
            logger.error("Supabase update friend_requests failed: %s %s", resp.status_code, resp.text[:1500])
            raise HTTPException(status_code=502, detail="Failed to accept friend request")

        # Create friendships (both directions)
        await _insert_friendships_bidirectional(requester_user_id, requested_user_id)
        await _invalidate_friend_api_caches(requester_user_id, requested_user_id)
        return FriendRequestActionResponse(status="ok", request_id=request_id)

    @app.post("/friends/requests/{request_id}/reject", response_model=FriendRequestActionResponse)
    async def reject_friend_request(
        request_id: int = Path(..., ge=1),
        authorization: Optional[str] = Header(default=None, alias="Authorization"),
    ) -> FriendRequestActionResponse:
        access_token = _extract_bearer_token(authorization)
        if not access_token:
            raise HTTPException(status_code=401, detail="Authorization header with Bearer token is required")

        me = await _resolve_user_id_from_token(access_token)
        req = await _get_friend_request_by_id(request_id)

        if req.get("status") != "pending":
            raise HTTPException(status_code=400, detail="Friend request is not pending")

        requested_user_id = str(req.get("requested_user_id"))
        if requested_user_id != me:
            raise HTTPException(status_code=403, detail="You are not allowed to reject this request")

        now = datetime.now(timezone.utc).isoformat()
        resp = await _sb_patch(
            "/rest/v1/friend_requests",
            params={"id": f"eq.{request_id}"},
            json={"status": "rejected", "responded_at": now},
            prefer="return=minimal",
        )
        if resp.status_code not in (200, 204):
            logger.error("Supabase update friend_requests failed: %s %s", resp.status_code, resp.text[:1500])
            raise HTTPException(status_code=502, detail="Failed to reject friend request")

        await _invalidate_friend_api_caches(requested_user_id, str(req.get("requester_user_id") or ""))
        return FriendRequestActionResponse(status="ok", request_id=request_id)



    @app.post("/friends/requests/{request_id}/cancel", response_model=FriendRequestActionResponse)
    async def cancel_friend_request(
        request_id: int = Path(..., ge=1),
        authorization: Optional[str] = Header(default=None, alias="Authorization"),
    ) -> FriendRequestActionResponse:
        """Requester cancels (withdraws) a pending friend request.

        Behavior:
        - Only requester_user_id can cancel.
        - Only pending requests can be canceled.
        - Implementation deletes the pending row (robust against status enum/constraints).
        """
        access_token = _extract_bearer_token(authorization)
        if not access_token:
            raise HTTPException(status_code=401, detail="Authorization header with Bearer token is required")

        me = await _resolve_user_id_from_token(access_token)
        req = await _get_friend_request_by_id(request_id)

        if req.get("status") != "pending":
            raise HTTPException(status_code=400, detail="Friend request is not pending")

        requester_user_id = str(req.get("requester_user_id"))
        if requester_user_id != me:
            raise HTTPException(status_code=403, detail="You are not allowed to cancel this request")

        # Delete request row (idempotent best-effort)
        resp = await _sb_delete(
            "/rest/v1/friend_requests",
            params={"id": f"eq.{request_id}"},
            prefer="return=minimal",
        )
        if resp.status_code not in (200, 204):
            if resp.status_code == 404:
                return FriendRequestActionResponse(status="ok", request_id=request_id)
            logger.error("Supabase delete friend_requests failed: %s %s", resp.status_code, resp.text[:1500])
            raise HTTPException(status_code=502, detail="Failed to cancel friend request")

        await _invalidate_friend_api_caches(requester_user_id, str(req.get("requested_user_id") or ""))
        return FriendRequestActionResponse(status="ok", request_id=request_id)

    @app.post("/friends/remove", response_model=FriendRemoveResponse)
    async def remove_friend(
        body: FriendRemoveBody,
        authorization: Optional[str] = Header(default=None, alias="Authorization"),
    ) -> FriendRemoveResponse:
        access_token = _extract_bearer_token(authorization)
        if not access_token:
            raise HTTPException(status_code=401, detail="Authorization header with Bearer token is required")

        me = await _resolve_user_id_from_token(access_token)
        friend_user_id = (body.friend_user_id or "").strip()
        if not friend_user_id:
            raise HTTPException(status_code=400, detail="friend_user_id is required")
        if friend_user_id == me:
            raise HTTPException(status_code=400, detail="You cannot remove yourself from friends")

        await _delete_friendships_bidirectional(me, friend_user_id)
        await _invalidate_friend_api_caches(me, friend_user_id)
        return FriendRemoveResponse(status="ok", friend_user_id=friend_user_id)


    @app.get("/emotion-log/feed")
    @app.get("/friends/feed")
    async def get_emotion_log_feed(
        authorization: Optional[str] = Header(default=None, alias="Authorization"),
    ) -> Dict[str, Any]:
        access_token = _extract_bearer_token(authorization)
        if not access_token:
            raise HTTPException(status_code=401, detail="Authorization header with Bearer token is required")

        me = await _resolve_user_id_from_token(access_token)

        summary = None
        latest_live_created_at: Optional[str] = None
        try:
            summary, latest_live_created_at = await asyncio.gather(
                fetch_latest_ready_emotion_log_feed_summary(me),
                _latest_emotion_log_feed_created_at(me),
            )
        except Exception as exc:
            logger.warning("Failed to prefetch emotion log feed freshness info: %s", exc)
            try:
                summary = await fetch_latest_ready_emotion_log_feed_summary(me)
            except Exception as inner_exc:
                logger.warning("Failed to fetch ready emotion log feed summary: %s", inner_exc)
                summary = None
            try:
                latest_live_created_at = await _latest_emotion_log_feed_created_at(me)
            except Exception as inner_exc:
                logger.warning("Failed to fetch latest live emotion log feed created_at: %s", inner_exc)
                latest_live_created_at = None

        summary_latest_created_at = _summary_latest_emotion_log_feed_created_at(summary)
        summary_is_fresh = bool(summary) and not _has_newer_iso(
            latest_live_created_at,
            summary_latest_created_at,
        )

        if summary_is_fresh and summary:
            items = _build_friend_feed_response_items(select_emotion_log_feed_items(summary))
            return {"status": "ok", "items": items}

        try:
            live_rows = await _fetch_live_emotion_log_feed_rows(me, limit=20)
            return {"status": "ok", "items": _build_friend_feed_response_items(live_rows)}
        except HTTPException:
            if summary:
                logger.warning(
                    "Emotion log feed live fetch failed; falling back to ready summary (viewer_user_id=%s)",
                    me,
                )
                items = _build_friend_feed_response_items(select_emotion_log_feed_items(summary))
                return {"status": "ok", "items": items}
            raise

    @app.get("/friends/manage")
    async def get_friend_manage(
        authorization: Optional[str] = Header(default=None, alias="Authorization"),
    ) -> Dict[str, Any]:
        access_token = _extract_bearer_token(authorization)
        if not access_token:
            raise HTTPException(status_code=401, detail="Authorization header with Bearer token is required")

        me = await _resolve_user_id_from_token(access_token)
        cache_key = f"friends:manage:{me}"

        async def _build_payload() -> Dict[str, Any]:
            my_profile, friend_rows, request_rows = await asyncio.gather(
                _fetch_or_create_my_profile(me),
                _fetch_manage_friendship_rows(me),
                _fetch_manage_request_rows(me),
            )

            friend_ids = _dedupe_user_ids(
                [str((row or {}).get("friend_user_id") or "").strip() for row in friend_rows if isinstance(row, dict)]
            )

            profile_ids: List[str] = list(friend_ids)
            for row in request_rows:
                if not isinstance(row, dict):
                    continue
                requester_user_id = str(row.get("requester_user_id") or "").strip()
                requested_user_id = str(row.get("requested_user_id") or "").strip()
                if requested_user_id == me and requester_user_id:
                    profile_ids.append(requester_user_id)
                elif requester_user_id == me and requested_user_id:
                    profile_ids.append(requested_user_id)
            profile_ids = _dedupe_user_ids(profile_ids)

            profiles, friend_notif_map = await asyncio.gather(
                _fetch_profiles_map(profile_ids) if profile_ids else asyncio.sleep(0, result={}),
                _fetch_emotion_notification_map(me, owner_user_ids=friend_ids) if friend_ids else asyncio.sleep(0, result={}),
            )

            friends_list: List[Dict[str, Any]] = []
            for row in friend_rows:
                if not isinstance(row, dict):
                    continue
                fid = str(row.get("friend_user_id") or "").strip()
                if not fid:
                    continue
                prof = profiles.get(fid) or {}
                friends_list.append(
                    {
                        "userId": fid,
                        "displayName": prof.get("display_name") or "Friend",
                        "friendCode": prof.get("friend_code") or None,
                    }
                )

            incoming: List[Dict[str, Any]] = []
            outgoing: List[Dict[str, Any]] = []
            for row in request_rows:
                if not isinstance(row, dict):
                    continue
                requester_user_id = str(row.get("requester_user_id") or "").strip()
                requested_user_id = str(row.get("requested_user_id") or "").strip()
                if requested_user_id == me and requester_user_id:
                    prof = profiles.get(requester_user_id) or {}
                    incoming.append(
                        {
                            "id": int(row.get("id") or 0),
                            "requesterUserId": requester_user_id,
                            "requesterName": prof.get("display_name") or "Friend",
                            "createdAt": row.get("created_at"),
                        }
                    )
                elif requester_user_id == me and requested_user_id:
                    prof = profiles.get(requested_user_id) or {}
                    outgoing.append(
                        {
                            "id": int(row.get("id") or 0),
                            "requestedUserId": requested_user_id,
                            "requestedName": prof.get("display_name") or "Friend",
                            "friendCode": prof.get("friend_code") or None,
                            "createdAt": row.get("created_at"),
                        }
                    )

            return {
                "status": "ok",
                "myProfile": my_profile,
                "friendsList": friends_list,
                "incoming": incoming,
                "outgoing": outgoing,
                "friendNotifMap": friend_notif_map,
                "incomingPendingCount": len(incoming),
            }

        return await get_or_compute(cache_key, FRIENDS_MANAGE_CACHE_TTL_SECONDS, _build_payload)


    @app.get("/emotion-log/unread-status", response_model=FriendUnreadStatusResponse)
    @app.get("/friends/unread-status", response_model=FriendUnreadStatusResponse)
    async def get_friend_unread_status(
        authorization: Optional[str] = Header(default=None, alias="Authorization"),
    ) -> FriendUnreadStatusResponse:
        access_token = _extract_bearer_token(authorization)
        if not access_token:
            raise HTTPException(status_code=401, detail="Authorization header with Bearer token is required")

        me = await _resolve_user_id_from_token(access_token)
        payload = await get_friend_unread_status_payload_for_user(me)
        return FriendUnreadStatusResponse(**payload)

    @app.post("/emotion-log/unread/read-feed", response_model=FriendUnreadMarkReadResponse)
    @app.post("/friends/unread/read-feed", response_model=FriendUnreadMarkReadResponse)
    async def post_emotion_log_feed_mark_read(
        body: Optional[FriendUnreadMarkReadBody] = None,
        authorization: Optional[str] = Header(default=None, alias="Authorization"),
    ) -> FriendUnreadMarkReadResponse:
        access_token = _extract_bearer_token(authorization)
        if not access_token:
            raise HTTPException(status_code=401, detail="Authorization header with Bearer token is required")

        me = await _resolve_user_id_from_token(access_token)
        requested_last_read_at = str((body.last_seen_created_at if body else "") or "").strip() or None
        if requested_last_read_at and _parse_iso_utc(requested_last_read_at) is None:
            requested_last_read_at = None

        current_last_read_at_task = _fetch_last_read_at("friend_feed_reads", me)
        latest_live_created_at_task = (
            _latest_emotion_log_feed_created_at(me)
            if not requested_last_read_at
            else asyncio.sleep(0, result=None)
        )
        current_last_read_at, latest_live_created_at = await asyncio.gather(
            current_last_read_at_task,
            latest_live_created_at_task,
        )

        candidate_last_read_at = (
            requested_last_read_at
            or latest_live_created_at
            or datetime.now(timezone.utc).isoformat()
        )
        last_read_at = (
            current_last_read_at
            if _has_newer_iso(current_last_read_at, candidate_last_read_at)
            else candidate_last_read_at
        )

        ok = await _upsert_last_read_at("friend_feed_reads", me, last_read_at)
        if not ok:
            raise HTTPException(status_code=502, detail="Failed to mark friend feed as read")

        await _invalidate_friend_api_caches(me)
        return FriendUnreadMarkReadResponse(last_read_at=last_read_at)

    @app.post("/emotion-log/unread/read-requests", response_model=FriendUnreadMarkReadResponse)
    @app.post("/friends/unread/read-requests", response_model=FriendUnreadMarkReadResponse)
    async def post_friend_requests_mark_read(
        authorization: Optional[str] = Header(default=None, alias="Authorization"),
    ) -> FriendUnreadMarkReadResponse:
        access_token = _extract_bearer_token(authorization)
        if not access_token:
            raise HTTPException(status_code=401, detail="Authorization header with Bearer token is required")

        me = await _resolve_user_id_from_token(access_token)
        last_read_at = await _latest_friend_request_created_at(me) or datetime.now(timezone.utc).isoformat()

        ok = await _upsert_last_read_at("friend_request_reads", me, last_read_at)
        if not ok:
            raise HTTPException(status_code=502, detail="Failed to mark friend requests as read")

        await _invalidate_friend_api_caches(me)
        return FriendUnreadMarkReadResponse(last_read_at=last_read_at)

    @app.get("/emotion-notifications/settings", response_model=FriendNotificationSettingsResponse)
    @app.get("/friends/notification-settings", response_model=FriendNotificationSettingsResponse)
    async def list_emotion_notification_settings(
        authorization: Optional[str] = Header(default=None, alias="Authorization"),
    ) -> FriendNotificationSettingsResponse:
        """List per-owner emotion-notification settings for the caller (viewer).

        Note:
        - Missing rows should be treated as enabled (true) by the client.
        - This endpoint returns only explicitly saved settings rows.
        """
        access_token = _extract_bearer_token(authorization)
        if not access_token:
            raise HTTPException(status_code=401, detail="Authorization header with Bearer token is required")

        me = await _resolve_user_id_from_token(access_token)

        resp = await _sb_get(
            "/rest/v1/friend_notification_settings",
            params={
                "select": "owner_user_id,is_enabled",
                "viewer_user_id": f"eq.{me}",
                "order": "owner_user_id.asc",
            },
        )

        # If the legacy table isn't provisioned yet, tell the client explicitly.
        if resp.status_code == 404:
            raise HTTPException(status_code=501, detail="friend_notification_settings table is not configured")

        if resp.status_code >= 300:
            logger.error(
                "Supabase select friend_notification_settings failed: %s %s",
                resp.status_code,
                resp.text[:1500],
            )
            raise HTTPException(status_code=502, detail="Failed to query notification settings")

        rows = resp.json()
        settings: List[FriendNotificationSettingItem] = []
        if isinstance(rows, list):
            for r in rows:
                if not isinstance(r, dict):
                    continue
                fid = r.get("owner_user_id")
                enabled = r.get("is_enabled")
                if isinstance(fid, str) and fid:
                    settings.append(
                        FriendNotificationSettingItem(
                            friend_user_id=fid,
                            is_enabled=(True if enabled is None else bool(enabled)),
                        )
                    )

        return FriendNotificationSettingsResponse(status="ok", settings=settings)

    @app.post("/emotion-notifications/settings/{friend_user_id}", response_model=FriendNotificationSettingResponse)
    @app.post("/friends/notification-settings/{friend_user_id}", response_model=FriendNotificationSettingResponse)
    async def set_emotion_notification_setting(
        body: FriendNotificationSettingUpsertBody,
        friend_user_id: str = Path(..., min_length=1, max_length=128),
        authorization: Optional[str] = Header(default=None, alias="Authorization"),
    ) -> FriendNotificationSettingResponse:
        """Upsert per-owner emotion-notification setting (viewer -> owner)."""
        access_token = _extract_bearer_token(authorization)
        if not access_token:
            raise HTTPException(status_code=401, detail="Authorization header with Bearer token is required")

        me = await _resolve_user_id_from_token(access_token)
        owner_user_id = (friend_user_id or "").strip()
        if not owner_user_id:
            raise HTTPException(status_code=400, detail="friend_user_id is required")
        if owner_user_id == me:
            raise HTTPException(status_code=400, detail="You cannot set notification setting for yourself")

        is_enabled = bool(body.is_enabled)
        now = datetime.now(timezone.utc).isoformat()

        # 1) Check existing row
        resp_get = await _sb_get(
            "/rest/v1/friend_notification_settings",
            params={
                "select": "viewer_user_id,owner_user_id,is_enabled",
                "viewer_user_id": f"eq.{me}",
                "owner_user_id": f"eq.{owner_user_id}",
                "limit": "1",
            },
        )

        if resp_get.status_code == 404:
            raise HTTPException(status_code=501, detail="friend_notification_settings table is not configured")
        if resp_get.status_code >= 300:
            logger.error(
                "Supabase get friend_notification_settings failed: %s %s",
                resp_get.status_code,
                resp_get.text[:1500],
            )
            raise HTTPException(status_code=502, detail="Failed to query notification settings")

        rows = resp_get.json()
        exists = bool(isinstance(rows, list) and rows)

        if exists:
            resp_upd = await _sb_patch(
                "/rest/v1/friend_notification_settings",
                params={
                    "viewer_user_id": f"eq.{me}",
                    "owner_user_id": f"eq.{owner_user_id}",
                },
                json={"is_enabled": is_enabled, "updated_at": now},
                prefer="return=minimal",
            )
            if resp_upd.status_code not in (200, 204):
                logger.error(
                    "Supabase update friend_notification_settings failed: %s %s",
                    resp_upd.status_code,
                    resp_upd.text[:1500],
                )
                raise HTTPException(status_code=502, detail="Failed to update notification setting")
        else:
            resp_ins = await _sb_post(
                "/rest/v1/friend_notification_settings",
                json={
                    "viewer_user_id": me,
                    "owner_user_id": owner_user_id,
                    "is_enabled": is_enabled,
                    "updated_at": now,
                },
                prefer="return=minimal",
            )
            if resp_ins.status_code not in (200, 201, 204):
                logger.error(
                    "Supabase insert friend_notification_settings failed: %s %s",
                    resp_ins.status_code,
                    resp_ins.text[:1500],
                )
                raise HTTPException(status_code=502, detail="Failed to save notification setting")

        await _invalidate_friend_api_caches(me)
        return FriendNotificationSettingResponse(
            status="ok",
            friend_user_id=owner_user_id,
            is_enabled=is_enabled,
        )


# Canonical registration/helper aliases.
# The registered routes above keep legacy /friends/* compatibility while exposing
# EmotionLog / Emotion Notifications as the public interface names.
register_emotion_log_routes = register_friend_routes
register_emotion_notification_routes = register_friend_routes
get_emotion_log_unread_status_payload_for_user = get_friend_unread_status_payload_for_user
