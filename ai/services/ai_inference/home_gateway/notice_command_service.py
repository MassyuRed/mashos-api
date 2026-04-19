from __future__ import annotations

import sys

from typing import Any, Dict, Iterable, Mapping, Optional

from notice_store import NoticeStore
from response_microcache import invalidate_prefix

fallback_store = NoticeStore()


def _get_notice_store() -> NoticeStore:
    module = sys.modules.get("api_notice")
    candidate = getattr(module, "store", None) if module is not None else None
    return candidate if candidate is not None else fallback_store


async def mark_notices_read(
    *,
    user_id: str,
    notice_ids: Iterable[str],
    client_meta: Optional[Mapping[str, Any]] = None,
) -> Dict[str, Any]:
    uid = str(user_id or "").strip()
    store = _get_notice_store()
    updated_count = await store.mark_notices_read(uid, notice_ids)
    await invalidate_prefix(f"notices:current:{uid}")
    current = await store.fetch_current_notice_bundle(uid, dict(client_meta or {}))
    return {
        "status": "ok",
        "updated_count": int(updated_count or 0),
        "unread_count": int(current.get("unread_count") or 0),
    }


async def mark_notice_popup_seen(
    *,
    user_id: str,
    notice_id: str,
) -> Dict[str, Any]:
    uid = str(user_id or "").strip()
    store = _get_notice_store()
    popup_seen = await store.mark_notice_popup_seen(uid, notice_id)
    await invalidate_prefix(f"notices:current:{uid}")
    return {
        "status": "ok",
        "popup_seen": bool(popup_seen),
    }
