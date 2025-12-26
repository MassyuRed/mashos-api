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

import logging
import os
from typing import Optional

from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel, Field

from api_emotion_submit import _extract_bearer_token, _resolve_user_id_from_token
from subscription import (
    SubscriptionTier,
    allowed_myprofile_modes_for_tier,
    normalize_subscription_tier,
)
from subscription_store import get_subscription_tier_for_user, set_subscription_tier_for_user


logger = logging.getLogger("subscription_api")


class SubscriptionMeResponse(BaseModel):
    user_id: str = Field(..., description="Supabase user id")
    subscription_tier: str = Field(..., description="free | plus | premium")
    allowed_myprofile_modes: list[str] = Field(..., description="Allowed MyProfile modes for the tier")


class SubscriptionUpdateRequest(BaseModel):
    """Client -> server subscription update (IAP result).

    IMPORTANT:
    - This endpoint should be backed by server-side purchase verification.
    - For MVP/dev only, you may enable unverified updates via env.
    """

    platform: Optional[str] = Field(
        default=None,
        description="android | ios (optional, used for product_id mapping)",
    )
    product_id: Optional[str] = Field(
        default=None,
        description="IAP product id (SKU). Used to map to plus/premium.",
    )
    purchase_token: Optional[str] = Field(
        default=None,
        description="Android: purchaseToken (from Google Play)",
    )
    transaction_receipt: Optional[str] = Field(
        default=None,
        description="iOS: base64 receipt / Android: transactionReceipt (raw)",
    )
    subscription_tier: Optional[str] = Field(
        default=None,
        description="Requested tier (free|plus|premium). If omitted, derived from product_id.",
    )


class SubscriptionUpdateResponse(BaseModel):
    user_id: str = Field(..., description="Supabase user id")
    subscription_tier: str = Field(..., description="free | plus | premium")
    allowed_myprofile_modes: list[str] = Field(..., description="Allowed MyProfile modes for the tier")
    updated: bool = Field(..., description="True if tier was updated")
    verification: str = Field(..., description="verification mode (e.g. unverified_dev)")


def _env_flag(name: str, default: bool = False) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return str(raw).strip().lower() in ("1", "true", "yes", "on")


def _split_env_list(name: str) -> list[str]:
    raw = os.getenv(name, "")
    if not raw:
        return []
    return [s.strip() for s in raw.split(",") if s.strip()]


def _resolve_tier_from_request(req: SubscriptionUpdateRequest) -> SubscriptionTier:
    """Resolve desired tier from request.

    Priority:
    1) req.subscription_tier (explicit)
    2) req.product_id mapping via env vars
    3) heuristic fallback ("premium"/"plus" in product id)
    """

    if req.subscription_tier:
        return normalize_subscription_tier(req.subscription_tier, default=SubscriptionTier.FREE)

    pid = str(req.product_id or "").strip()
    if not pid:
        return SubscriptionTier.FREE

    plat = str(req.platform or "").strip().lower()

    # Env-driven mapping (recommended)
    # - Allow comma-separated lists so you can add yearly/monthly SKUs, etc.
    if plat == "android":
        plus_ids = set(_split_env_list("COCOLON_IAP_ANDROID_PLUS_PRODUCT_IDS"))
        prem_ids = set(_split_env_list("COCOLON_IAP_ANDROID_PREMIUM_PRODUCT_IDS"))
        if pid in prem_ids:
            return SubscriptionTier.PREMIUM
        if pid in plus_ids:
            return SubscriptionTier.PLUS
    elif plat == "ios":
        plus_ids = set(_split_env_list("COCOLON_IAP_IOS_PLUS_PRODUCT_IDS"))
        prem_ids = set(_split_env_list("COCOLON_IAP_IOS_PREMIUM_PRODUCT_IDS"))
        if pid in prem_ids:
            return SubscriptionTier.PREMIUM
        if pid in plus_ids:
            return SubscriptionTier.PLUS

    # Fallback heuristic (dev convenience only)
    low = pid.lower()
    if "premium" in low:
        return SubscriptionTier.PREMIUM
    if "plus" in low:
        return SubscriptionTier.PLUS
    return SubscriptionTier.FREE


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

    @app.post("/subscription/update", response_model=SubscriptionUpdateResponse)
    async def subscription_update(
        req: SubscriptionUpdateRequest,
        authorization: Optional[str] = Header(default=None, alias="Authorization"),
    ) -> SubscriptionUpdateResponse:
        """Update the caller's subscription tier.

        Security note:
        - This endpoint MUST be protected by server-side purchase verification
          before production use.
        - For MVP/dev, you can enable *unverified* updates via:
            COCOLON_IAP_ALLOW_UNVERIFIED=true
        """

        access_token = _extract_bearer_token(authorization)
        if not access_token:
            raise HTTPException(status_code=401, detail="Authorization header with Bearer token is required")

        # Ensure caller is a valid Supabase user
        user_id = await _resolve_user_id_from_token(access_token)

        # Basic payload sanity: require at least *some* purchase proof fields.
        # (Real verification should be added later.)
        if not (req.purchase_token or req.transaction_receipt):
            raise HTTPException(
                status_code=400,
                detail="purchase_token (Android) or transaction_receipt (iOS/Android) is required",
            )

        desired_tier = _resolve_tier_from_request(req)

        # Fail-closed by default.
        # In production, do NOT enable unverified updates.
        allow_unverified = _env_flag("COCOLON_IAP_ALLOW_UNVERIFIED", default=False)
        if not allow_unverified:
            raise HTTPException(
                status_code=501,
                detail=(
                    "IAP verification is not configured. "
                    "Set COCOLON_IAP_ALLOW_UNVERIFIED=true for dev, "
                    "or implement server-side purchase verification before production."
                ),
            )

        # Apply tier update (service_role bypasses RLS)
        try:
            updated_tier = await set_subscription_tier_for_user(user_id, desired_tier)
        except Exception as exc:
            logger.warning("Failed to update subscription tier: %s", exc)
            raise HTTPException(
                status_code=502,
                detail=(
                    "Failed to update subscription tier (Supabase). "
                    "Ensure public.profiles has column 'subscription_tier' and the backend has SUPABASE_URL / SUPABASE_SERVICE_ROLE_KEY."
                ),
            )
        modes = [m.value for m in allowed_myprofile_modes_for_tier(updated_tier)]

        return SubscriptionUpdateResponse(
            user_id=user_id,
            subscription_tier=updated_tier.value,
            allowed_myprofile_modes=modes,
            updated=True,
            verification="unverified_dev",
        )
