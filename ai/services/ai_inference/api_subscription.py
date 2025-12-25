# -*- coding: utf-8 -*-
"""Subscription (tier) API for Cocolon (MashOS / FastAPI)

MVP endpoint:
- GET /subscription/me

Purpose:
- Debugging / UI gating: allow the client to know the current tier and the
  allowed MyProfile modes.

Auth:
- Requires Authorization: Bearer <supabase_access_token>
- Resolves the user via Supabase Auth `/auth/v1/user`.

Note:
- Tier lookup is fail-closed: if missing/unknown, returns 'free'.
"""

from __future__ import annotations

from typing import Optional

from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel, Field

from api_emotion_submit import _extract_bearer_token, _resolve_user_id_from_token
from subscription import allowed_myprofile_modes_for_tier
from subscription_store import get_subscription_tier_for_user


class SubscriptionMeResponse(BaseModel):
    user_id: str = Field(..., description="Supabase user id")
    subscription_tier: str = Field(..., description="free | plus | premium")
    allowed_myprofile_modes: list[str] = Field(..., description="Allowed MyProfile modes for the tier")


def register_subscription_routes(app: FastAPI) -> None:
    @app.get("/subscription/me", response_model=SubscriptionMeResponse)
    async def subscription_me(
        authorization: Optional[str] = Header(default=None, alias="Authorization"),
    ) -> SubscriptionMeResponse:
        access_token = _extract_bearer_token(authorization)
        if not access_token:
            raise HTTPException(status_code=401, detail="Authorization header with Bearer token is required")

        user_id = await _resolve_user_id_from_token(access_token)
        tier = await get_subscription_tier_for_user(user_id)
        modes = [m.value for m in allowed_myprofile_modes_for_tier(tier)]
        return SubscriptionMeResponse(
            user_id=user_id,
            subscription_tier=tier.value,
            allowed_myprofile_modes=modes,
        )
