# -*- coding: utf-8 -*-
from __future__ import annotations

import logging
import os
from typing import Optional, Tuple

from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel, Field

from api_emotion_submit import _extract_bearer_token, _resolve_user_id_from_token
from subscription import (
    SubscriptionTier,
    allowed_myprofile_modes_for_tier,
    normalize_subscription_tier,
)
from subscription_store import get_subscription_tier_for_user, set_subscription_tier_for_user
from subscription_trial_store import get_trial_state, mark_trial_consumed
from active_users_store import touch_active_user

logger = logging.getLogger("subscription_api")

PLUS_TRIAL_KEY = "plus_intro_v1"


class SubscriptionMeResponse(BaseModel):
    user_id: str = Field(..., description="Supabase user id")
    subscription_tier: str = Field(..., description="free | plus | premium")
    allowed_myprofile_modes: list[str] = Field(..., description="Allowed MyProfile modes for the tier")
    plus_trial_eligible: bool = Field(..., description="Whether the user can be shown the Plus free trial")
    plus_trial_consumed: bool = Field(..., description="Whether the user has already used the Plus free trial")
    plus_trial_consumed_at: Optional[str] = Field(default=None, description="When the Plus free trial was first consumed")


class SubscriptionUpdateRequest(BaseModel):
    platform: Optional[str] = Field(default=None, description="android | ios")
    product_id: Optional[str] = Field(default=None, description="IAP product id")
    purchase_token: Optional[str] = Field(default=None, description="Android purchaseToken")
    transaction_receipt: Optional[str] = Field(default=None, description="iOS receipt / Android raw receipt")
    transaction_id: Optional[str] = Field(default=None, description="iOS transaction id")
    subscription_tier: Optional[str] = Field(default=None, description="free | plus | premium")


class SubscriptionUpdateResponse(BaseModel):
    user_id: str = Field(..., description="Supabase user id")
    subscription_tier: str = Field(..., description="free | plus | premium")
    allowed_myprofile_modes: list[str] = Field(..., description="Allowed MyProfile modes for the tier")
    updated: bool = Field(..., description="True if tier was updated")
    verification: str = Field(..., description="verification mode")


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


def _user_in_unverified_allowlist(user_id: str) -> bool:
    uid = str(user_id or "").strip()
    if not uid:
        return False
    allow = set(_split_env_list("COCOLON_IAP_ALLOW_UNVERIFIED_USER_IDS"))
    return uid in allow


def _resolve_tier_from_request(req: SubscriptionUpdateRequest) -> SubscriptionTier:
    if req.subscription_tier:
        return normalize_subscription_tier(req.subscription_tier, default=SubscriptionTier.FREE)

    pid = str(req.product_id or "").strip()
    if not pid:
        return SubscriptionTier.FREE

    plat = str(req.platform or "").strip().lower()

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

    low = pid.lower()
    if "premium" in low:
        return SubscriptionTier.PREMIUM
    if "plus" in low:
        return SubscriptionTier.PLUS
    return SubscriptionTier.FREE


async def _get_plus_trial_payload(
    user_id: str,
    tier: SubscriptionTier,
) -> Tuple[bool, bool, Optional[str]]:
    try:
        trial_state = await get_trial_state(user_id, PLUS_TRIAL_KEY)
        plus_trial_consumed = bool(trial_state.get("consumed"))
        plus_trial_consumed_at = trial_state.get("consumed_at")
    except Exception as exc:
        logger.warning("Failed to read plus trial state: %s", exc)
        plus_trial_consumed = True
        plus_trial_consumed_at = None

    plus_trial_eligible = (tier == SubscriptionTier.FREE) and (not plus_trial_consumed)
    return plus_trial_eligible, plus_trial_consumed, plus_trial_consumed_at


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

        plus_trial_eligible, plus_trial_consumed, plus_trial_consumed_at = await _get_plus_trial_payload(
            user_id,
            tier,
        )

        return SubscriptionMeResponse(
            user_id=user_id,
            subscription_tier=tier.value,
            allowed_myprofile_modes=modes,
            plus_trial_eligible=plus_trial_eligible,
            plus_trial_consumed=plus_trial_consumed,
            plus_trial_consumed_at=plus_trial_consumed_at,
        )

    @app.post("/subscription/update", response_model=SubscriptionUpdateResponse)
    async def subscription_update(
        req: SubscriptionUpdateRequest,
        authorization: Optional[str] = Header(default=None, alias="Authorization"),
    ) -> SubscriptionUpdateResponse:
        access_token = _extract_bearer_token(authorization)
        if not access_token:
            raise HTTPException(status_code=401, detail="Authorization header with Bearer token is required")

        user_id = await _resolve_user_id_from_token(access_token)

        if not (req.purchase_token or req.transaction_receipt):
            raise HTTPException(
                status_code=400,
                detail="purchase_token (Android) or transaction_receipt (iOS/Android) is required",
            )

        desired_tier = _resolve_tier_from_request(req)

        allow_unverified = _env_flag("COCOLON_IAP_ALLOW_UNVERIFIED", default=False)
        verification_mode = ""

        if allow_unverified:
            verification_mode = "unverified_dev"
        elif _user_in_unverified_allowlist(user_id):
            allow_unverified = True
            verification_mode = "unverified_dev_user_allowlist"

        if not allow_unverified:
            raise HTTPException(
                status_code=501,
                detail=(
                    "IAP verification is not configured. "
                    "Set COCOLON_IAP_ALLOW_UNVERIFIED=true for dev, "
                    "or set COCOLON_IAP_ALLOW_UNVERIFIED_USER_IDS for a safer dev allowlist, "
                    "or implement server-side purchase verification before production."
                ),
            )

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

        try:
            await touch_active_user(
                user_id,
                activity="subscription/update",
                subscription_tier=updated_tier.value,
                force=True,
            )
        except Exception:
            pass

        if updated_tier in (SubscriptionTier.PLUS, SubscriptionTier.PREMIUM):
            store_ref = str(req.transaction_id or req.purchase_token or "").strip() or None
            try:
                await mark_trial_consumed(
                    user_id=user_id,
                    trial_key=PLUS_TRIAL_KEY,
                    platform=req.platform,
                    product_id=req.product_id,
                    store_ref=store_ref,
                    source="subscription_update_paid_plan",
                )
            except Exception as exc:
                logger.warning("Failed to mark plus trial consumed: %s", exc)

        return SubscriptionUpdateResponse(
            user_id=user_id,
            subscription_tier=updated_tier.value,
            allowed_myprofile_modes=modes,
            updated=True,
            verification=verification_mode or "unverified_dev",
        )