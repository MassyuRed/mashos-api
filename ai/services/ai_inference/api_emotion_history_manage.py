from __future__ import annotations

import logging
from typing import Any, Dict, Optional

from fastapi import FastAPI, Header, HTTPException, Path
from pydantic import BaseModel, Field

from api_account_visibility import _require_user_id
from astor_global_summary_enqueue import enqueue_global_summary_refresh
from supabase_client import sb_delete

logger = logging.getLogger("emotion_history_manage_api")


class EmotionHistoryDeleteResponse(BaseModel):
    status: str = "ok"
    emotion_id: str
    deleted: bool = True


def _pick_rows(resp) -> list[dict[str, Any]]:
    try:
        data = resp.json()
    except Exception:
        return []
    if isinstance(data, list):
        return [row for row in data if isinstance(row, dict)]
    if isinstance(data, dict):
        return [data]
    return []


def register_emotion_history_manage_routes(app: FastAPI) -> None:
    @app.delete("/emotion/history/{emotion_id}", response_model=EmotionHistoryDeleteResponse)
    async def delete_emotion_history_row(
        emotion_id: str = Path(..., min_length=1),
        authorization: Optional[str] = Header(default=None, alias="Authorization"),
    ) -> EmotionHistoryDeleteResponse:
        me = await _require_user_id(authorization)
        resp = await sb_delete(
            "/rest/v1/emotions",
            params={
                "id": f"eq.{str(emotion_id or '').strip()}",
                "user_id": f"eq.{me}",
                "select": "id,created_at",
            },
            prefer="return=representation",
            timeout=8.0,
        )
        if resp.status_code >= 300:
            logger.warning("emotions delete failed: %s %s", resp.status_code, (resp.text or "")[:800])
            raise HTTPException(status_code=502, detail="Failed to delete emotion history")

        rows = _pick_rows(resp)
        if not rows:
            raise HTTPException(status_code=404, detail="Emotion history not found")

        deleted_row = rows[0] or {}
        deleted_created_at = str(deleted_row.get("created_at") or "").strip() or None

        try:
            await enqueue_global_summary_refresh(
                trigger="emotion_history_delete",
                requested_at=deleted_created_at,
                actor_user_id=me,
                debounce=True,
            )
        except Exception as exc:
            logger.warning("global summary enqueue failed (emotion_history_delete): %s", exc)

        return EmotionHistoryDeleteResponse(emotion_id=str(deleted_row.get("id") or emotion_id), deleted=True)
