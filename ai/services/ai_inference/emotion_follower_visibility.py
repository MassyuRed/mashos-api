"""Authority for the current sender-side filter on EmotionLog and push delivery."""
from __future__ import annotations

from collections.abc import Iterable
from uuid import UUID

from supabase_client import sb_post_rpc

_FEED_FIELDS = {"id", "viewer_user_id", "owner_user_id", "owner_name", "items", "created_at"}


def _canonical_uuid(value: object) -> str | None:
    if not isinstance(value, str):
        return None
    try:
        parsed = UUID(value)
    except ValueError:
        return None
    return str(parsed) if parsed.int else None


async def _query_rows(function: str, arguments: dict) -> list:
    try:
        response = await sb_post_rpc(function, arguments, timeout=5.0)
        if response.status_code == 200:
            rows = response.json()
            if type(rows) is list:
                return rows
    except Exception:
        pass
    # Never use an older unfiltered query or expose a raw diagnostic.
    raise RuntimeError("EmotionLog visibility unavailable")


async def permitted_emotion_recipients(owner_user_id: str, viewer_user_ids: Iterable[str]) -> list[str]:
    owner = _canonical_uuid(owner_user_id)
    if not owner:
        return []
    candidates = list(dict.fromkeys(
        uid for value in viewer_user_ids
        if (uid := _canonical_uuid(value)) and uid != owner
    ))
    if not candidates:
        return []
    accepted = set()
    for start in range(0, len(candidates), 200):
        recipients = candidates[start:start + 200]
        rows = await _query_rows("emotion_notification_recipients_allowed", {
            "p_owner_user_id": owner,
            "p_viewer_user_ids": recipients,
        })
        if len(rows) > len(recipients) or any(_canonical_uuid(value) != value or value is None for value in rows):
            raise RuntimeError("EmotionLog visibility unavailable")
        returned = set(rows)
        if len(returned) != len(rows) or not returned <= set(recipients):
            raise RuntimeError("EmotionLog visibility unavailable")
        accepted.update(returned)
    return [uid for uid in candidates if uid in accepted]


async def fetch_visible_emotion_log_feed(viewer_user_id: str, *, limit: int) -> list[dict]:
    viewer = _canonical_uuid(viewer_user_id)
    if not viewer:
        raise RuntimeError("EmotionLog visibility unavailable")
    max_rows = max(1, min(limit, 200))
    rows = await _query_rows("emotion_log_feed_for_viewer", {
        "p_viewer_user_id": viewer,
        "p_limit": max_rows,
    })
    if len(rows) > max_rows or any(
        type(row) is not dict or set(row) != _FEED_FIELDS
        or row["viewer_user_id"] != viewer
        or row["owner_user_id"] in (None, viewer)
        or _canonical_uuid(row["owner_user_id"]) != row["owner_user_id"]
        for row in rows
    ):
        raise RuntimeError("EmotionLog visibility unavailable")
    return rows
