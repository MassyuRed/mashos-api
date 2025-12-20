# -*- coding: utf-8 -*-
"""Emotion Secret Update API for Cocolon
----------------------------------------
- POST /emotion/secret

役割:
- MyWeb 履歴画面などから、既存の emotions レコードの is_secret を切り替える。
- 併せて astor_structure_patterns.json（ASTOR の構造トリガー蓄積）側も更新し、
  self/external の参照範囲（シークレット除外）が破綻しないよう整合させる。

設計方針:
- 更新操作（書き込み）は MashOS 側（service_role）で行う。
- 認証は /emotion/submit と同様に Supabase Auth の JWT を検証して user_id を確定する。
"""

from __future__ import annotations

import logging
from typing import Any, Optional

import httpx
from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel, Field

# 既存の token / user_id 解決ロジックを流用
from api_emotion_submit import (
    SUPABASE_SERVICE_ROLE_KEY,
    SUPABASE_URL,
    _ensure_supabase_config,
    _extract_bearer_token,
    _resolve_user_id_from_token,
    astor_engine,
)

logger = logging.getLogger("emotion_secret")


class EmotionSecretUpdateRequest(BaseModel):
    emotion_id: Any = Field(..., description="emotions.id")
    is_secret: bool = Field(..., description="更新後の secret 状態")
    created_at: Optional[str] = Field(
        default=None,
        description=(
            "感情ログの created_at（ISO8601）。"
            "未指定の場合は Supabase 側のレコードから取得し、ASTOR の trigger 更新に使う。"
        ),
    )


class EmotionSecretUpdateResponse(BaseModel):
    status: str = Field(..., description="'ok' 固定")
    id: Optional[Any] = Field(default=None, description="更新対象の emotions.id")
    is_secret: bool = Field(..., description="更新後の secret 状態")
    updated_triggers: int = Field(default=0, description="更新した ASTOR triggers の件数")


async def _update_emotion_is_secret(*, user_id: str, emotion_id: Any, is_secret: bool) -> dict:
    """Supabase の emotions を service_role で更新する。"""
    _ensure_supabase_config()
    url = f"{SUPABASE_URL}/rest/v1/emotions"
    headers = {
        "apikey": SUPABASE_SERVICE_ROLE_KEY,
        "Authorization": f"Bearer {SUPABASE_SERVICE_ROLE_KEY}",
        "Content-Type": "application/json",
        "Prefer": "return=representation",
    }
    params = {
        "id": f"eq.{emotion_id}",
        "user_id": f"eq.{user_id}",
    }

    async with httpx.AsyncClient(timeout=6.0) as client:
        resp = await client.patch(url, headers=headers, params=params, json={"is_secret": bool(is_secret)})

    if resp.status_code not in (200, 204):
        logger.error(
            "Supabase update emotions.is_secret failed: status=%s body=%s",
            resp.status_code,
            resp.text[:2000],
        )
        raise HTTPException(status_code=502, detail="Failed to update secret flag")

    # return=representation の場合は list が返る。0件なら []。
    try:
        data = resp.json() if resp.text else []
    except Exception:
        data = []

    if isinstance(data, list) and data:
        return data[0]
    if isinstance(data, dict) and data:
        return data

    # フォールバック:
    # 一部環境で PATCH が 204(no-content) を返すことがあるため、
    # ここで owner 条件付きで1件取得して「存在/所有」を確定させる。
    get_headers = {
        "apikey": SUPABASE_SERVICE_ROLE_KEY,
        "Authorization": f"Bearer {SUPABASE_SERVICE_ROLE_KEY}",
    }
    get_params = {
        "select": "id,created_at,is_secret",
        "id": f"eq.{emotion_id}",
        "user_id": f"eq.{user_id}",
        "limit": "1",
    }
    async with httpx.AsyncClient(timeout=6.0) as client:
        resp2 = await client.get(url, headers=get_headers, params=get_params)
    if resp2.status_code >= 300:
        logger.error(
            "Supabase select emotions fallback failed: status=%s body=%s",
            resp2.status_code,
            resp2.text[:2000],
        )
        return {}
    try:
        rows = resp2.json()
    except Exception:
        rows = []
    if isinstance(rows, list) and rows:
        return rows[0]
    return {}


def register_emotion_secret_routes(app: FastAPI) -> None:
    """FastAPI に /emotion/secret を登録する。"""

    @app.post("/emotion/secret", response_model=EmotionSecretUpdateResponse)
    async def emotion_secret_update(
        payload: EmotionSecretUpdateRequest,
        authorization: Optional[str] = Header(default=None, alias="Authorization"),
    ) -> EmotionSecretUpdateResponse:
        # 1) 認証して user_id を確定
        access_token = _extract_bearer_token(authorization)
        if not access_token:
            raise HTTPException(status_code=401, detail="Authorization header with Bearer token is required")

        user_id = await _resolve_user_id_from_token(access_token)

        # 2) Supabase で更新（所有者以外は 0 件更新になりうる）
        updated_row = await _update_emotion_is_secret(
            user_id=user_id,
            emotion_id=payload.emotion_id,
            is_secret=bool(payload.is_secret),
        )

        # 3) ASTOR patterns の trigger 側も整合（ts で突合）
        # - created_at が指定されていればそれを優先
        # - なければ Supabase の返却行から拾う
        ts = (payload.created_at or updated_row.get("created_at") or "").strip()
        updated_triggers = 0
        if ts:
            try:
                # NOTE: /emotion/submit が使っている astor_engine インスタンスの
                # in-memory state を更新することで、次回の ingest/save で上書きされる事故を避ける。
                updated_triggers = astor_engine._patterns.update_triggers_secret_by_ts(  # type: ignore[attr-defined]
                    user_id=user_id,
                    ts=ts,
                    is_secret=bool(payload.is_secret),
                )
            except Exception as exc:
                logger.error("Failed to update ASTOR triggers secret flag: %s", exc)

        # 4) 0件更新（= 対象が無い or 所有者でない）を 404 扱いにする
        if not updated_row:
            raise HTTPException(status_code=404, detail="Emotion record not found")

        return EmotionSecretUpdateResponse(
            status="ok",
            id=updated_row.get("id", payload.emotion_id),
            is_secret=bool(payload.is_secret),
            updated_triggers=int(updated_triggers or 0),
        )
