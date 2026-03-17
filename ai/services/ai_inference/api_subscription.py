# -*- coding: utf-8 -*-
from __future__ import annotations

import hashlib
import logging
import os
from datetime import datetime, timezone
from typing import Any, Dict, Optional

from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel, Field

from active_users_store import touch_active_user
from api_emotion_submit import _extract_bearer_token, _resolve_user_id_from_token
from subscription import SubscriptionTier, normalize_subscription_tier
from subscription_projection import (
    CanonicalSubscriptionState,
    PurchaseOwnershipConflictError,
    VerifiedPurchase,
    build_subscription_state,
    clean_optional_str,
    find_entitlement_by_store_ref,
    find_purchase_claim,
    normalize_plan_code,
    persist_verified_purchase,
    plan_code_from_product_id,
    project_profile_tier,
)
from subscription_verifier_android import (
    AndroidVerificationConfigError,
    AndroidVerificationError,
    AndroidVerificationInactive,
    acknowledge_android_subscription,
    is_android_verification_configured,
    verify_android_subscription,
)
from subscription_verifier_ios import (
    IOSVerificationConfigError,
    IOSVerificationError,
    IOSVerificationInactive,
    is_ios_verification_configured,
    verify_ios_subscription,
)

logger = logging.getLogger("subscription_api")

ENTITLEMENT_STATUS_NONE = "none"


class SubscriptionMeResponse(BaseModel):
    user_id: str = Field(..., description="Supabase user id")
    subscription_tier: str = Field(..., description="free | plus | premium")
    allowed_myprofile_modes: list[str] = Field(..., description="Allowed MyProfile modes for the tier")
    plan_code: Optional[str] = Field(default=None, description="plus | premium | null")
    entitlement_status: str = Field(default=ENTITLEMENT_STATUS_NONE, description="Canonical entitlement status")
    expires_at: Optional[str] = Field(default=None, description="ISO datetime when the entitlement expires")
    auto_renew: bool = Field(default=False, description="Whether auto renew is currently enabled")
    store: Optional[str] = Field(default=None, description="ios | android | null")
    product_id: Optional[str] = Field(default=None, description="Current product id when known")
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
    plan_code: Optional[str] = Field(default=None, description="plus | premium | null")
    entitlement_status: str = Field(default=ENTITLEMENT_STATUS_NONE, description="Canonical entitlement status")
    expires_at: Optional[str] = Field(default=None, description="ISO datetime when the entitlement expires")
    auto_renew: bool = Field(default=False, description="Whether auto renew is currently enabled")
    store: Optional[str] = Field(default=None, description="ios | android | null")
    product_id: Optional[str] = Field(default=None, description="Resolved product id when known")
    plus_trial_eligible: bool = Field(..., description="Whether the user can be shown the Plus free trial")
    plus_trial_consumed: bool = Field(..., description="Whether the user has already used the Plus free trial")
    plus_trial_consumed_at: Optional[str] = Field(default=None, description="When the Plus free trial was first consumed")
    updated: bool = Field(..., description="True if the projection ran successfully")
    verification: str = Field(..., description="verification / sync mode")


# ---------------------------------------------------------------------------
# Small helpers
# ---------------------------------------------------------------------------


def _env_flag(name: str, default: bool = False) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return str(raw).strip().lower() in {"1", "true", "yes", "on"}



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



def _normalize_platform(platform: Optional[str]) -> Optional[str]:
    plat = str(platform or "").strip().lower()
    if plat in {"ios", "android"}:
        return plat
    return None



def _receipt_fingerprint(receipt: Optional[str]) -> Optional[str]:
    raw = str(receipt or "").strip()
    if not raw:
        return None
    digest = hashlib.sha256(raw.encode("utf-8")).hexdigest()[:40]
    return f"receiptsha256:{digest}"



def _infer_platform_from_request(req: SubscriptionUpdateRequest) -> Optional[str]:
    plat = _normalize_platform(req.platform)
    if plat:
        return plat
    if clean_optional_str(req.purchase_token):
        return "android"
    if clean_optional_str(req.transaction_id) or clean_optional_str(req.transaction_receipt):
        return "ios"
    return None



def _resolve_tier_from_request(req: SubscriptionUpdateRequest) -> SubscriptionTier:
    if req.subscription_tier:
        return normalize_subscription_tier(req.subscription_tier, default=SubscriptionTier.FREE)
    plan = plan_code_from_product_id(_infer_platform_from_request(req), req.product_id)
    if plan == SubscriptionTier.PLUS.value:
        return SubscriptionTier.PLUS
    if plan == SubscriptionTier.PREMIUM.value:
        return SubscriptionTier.PREMIUM
    return SubscriptionTier.FREE



def _resolve_request_refs(req: SubscriptionUpdateRequest) -> tuple[str, Optional[str], Optional[str], Optional[str], str]:
    platform = _infer_platform_from_request(req)
    if not platform:
        raise HTTPException(status_code=400, detail={"code": "platform_missing", "message": "platform (ios/android) could not be resolved from the purchase payload."})

    purchase_token = clean_optional_str(req.purchase_token)
    transaction_id = clean_optional_str(req.transaction_id)
    original_transaction_id = None

    if platform == "android":
        store_ref = purchase_token
    else:
        store_ref = transaction_id or _receipt_fingerprint(req.transaction_receipt)

    store_ref = clean_optional_str(store_ref)
    if not store_ref:
        raise HTTPException(
            status_code=400,
            detail={
                "code": "store_ref_missing",
                "message": "A stable store reference is required. Send purchase_token for Android, or transaction_id for iOS.",
            },
        )

    return platform, purchase_token, transaction_id, original_transaction_id, store_ref



def _storage_payload(req: SubscriptionUpdateRequest, *, plan_code: Optional[str], store_ref: Optional[str]) -> Dict[str, Any]:
    return {
        "platform": _infer_platform_from_request(req),
        "product_id": clean_optional_str(req.product_id),
        "subscription_tier_hint": clean_optional_str(req.subscription_tier),
        "plan_code": normalize_plan_code(plan_code),
        "purchase_token_present": bool(clean_optional_str(req.purchase_token)),
        "transaction_receipt_present": bool(clean_optional_str(req.transaction_receipt)),
        "transaction_receipt_fingerprint": _receipt_fingerprint(req.transaction_receipt),
        "transaction_id": clean_optional_str(req.transaction_id),
        "store_ref": clean_optional_str(store_ref),
    }



def _verification_mode_for_user(user_id: str) -> tuple[bool, Optional[str]]:
    if _env_flag("COCOLON_IAP_ALLOW_UNVERIFIED", default=False):
        return True, "unverified_dev"
    if _user_in_unverified_allowlist(user_id):
        return True, "unverified_dev_user_allowlist"
    return False, None



def _http_detail(code: str, message: str, **extra: Any) -> Dict[str, Any]:
    payload = {"code": code, "message": message}
    payload.update({k: v for k, v in extra.items() if v is not None})
    return payload



def _response_from_snapshot(snapshot: CanonicalSubscriptionState, *, updated: bool, verification: str) -> SubscriptionUpdateResponse:
    return SubscriptionUpdateResponse(
        **snapshot.as_dict(),
        updated=updated,
        verification=verification,
    )


async def _verify_purchase_or_raise(req: SubscriptionUpdateRequest, *, store: str) -> VerifiedPurchase:
    if store == "android":
        if not clean_optional_str(req.purchase_token):
            raise HTTPException(status_code=400, detail=_http_detail("purchase_token_missing", "purchase_token is required for Android verification."))
        try:
            return await verify_android_subscription(
                purchase_token=str(req.purchase_token),
                product_id=clean_optional_str(req.product_id),
            )
        except AndroidVerificationInactive as exc:
            raise HTTPException(
                status_code=422,
                detail=_http_detail(
                    exc.code,
                    exc.message,
                    entitlement_status=exc.verified_purchase.status,
                    plan_code=exc.verified_purchase.plan_code,
                    product_id=exc.verified_purchase.product_id,
                    expires_at=exc.verified_purchase.expires_at,
                ),
            ) from exc
        except AndroidVerificationConfigError as exc:
            raise HTTPException(status_code=503, detail=_http_detail("verification_unavailable", str(exc))) from exc
        except AndroidVerificationError as exc:
            raise HTTPException(status_code=503, detail=_http_detail("verification_failed", str(exc))) from exc

    if not clean_optional_str(req.transaction_id):
        raise HTTPException(
            status_code=400,
            detail=_http_detail(
                "transaction_id_missing",
                "transaction_id is required for iOS verification. Update the client to send transactionId from StoreKit.",
            ),
        )
    try:
        return await verify_ios_subscription(
            transaction_id=str(req.transaction_id),
            product_id=clean_optional_str(req.product_id),
        )
    except IOSVerificationInactive as exc:
        raise HTTPException(
            status_code=422,
            detail=_http_detail(
                exc.code,
                exc.message,
                entitlement_status=exc.verified_purchase.status,
                plan_code=exc.verified_purchase.plan_code,
                product_id=exc.verified_purchase.product_id,
                expires_at=exc.verified_purchase.expires_at,
            ),
        ) from exc
    except IOSVerificationConfigError as exc:
        raise HTTPException(status_code=503, detail=_http_detail("verification_unavailable", str(exc))) from exc
    except IOSVerificationError as exc:
        raise HTTPException(status_code=503, detail=_http_detail("verification_failed", str(exc))) from exc


async def _persist_or_conflict(user_id: str, verified_purchase: VerifiedPurchase) -> CanonicalSubscriptionState:
    try:
        return await persist_verified_purchase(user_id=user_id, verified_purchase=verified_purchase)
    except PurchaseOwnershipConflictError as exc:
        raise HTTPException(
            status_code=409,
            detail=_http_detail("purchase_already_claimed", str(exc)),
        ) from exc
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail=_http_detail(
                "runtime_persist_failed",
                "Failed to persist runtime subscription rows. Ensure the Phase 1 subscription migrations have been applied.",
                error=str(exc),
            ),
        ) from exc


# ---------------------------------------------------------------------------
# Route registration
# ---------------------------------------------------------------------------


def register_subscription_routes(app: FastAPI) -> None:
    @app.get("/subscription/me", response_model=SubscriptionMeResponse)
    async def subscription_me(
        authorization: Optional[str] = Header(default=None, alias="Authorization"),
    ) -> SubscriptionMeResponse:
        access_token = _extract_bearer_token(authorization)
        if not access_token:
            raise HTTPException(status_code=401, detail="Authorization header with Bearer token is required")

        user_id = await _resolve_user_id_from_token(access_token)
        snapshot = await build_subscription_state(user_id)
        return SubscriptionMeResponse(**snapshot.as_dict())

    @app.post("/subscription/update", response_model=SubscriptionUpdateResponse)
    async def subscription_update(
        req: SubscriptionUpdateRequest,
        authorization: Optional[str] = Header(default=None, alias="Authorization"),
    ) -> SubscriptionUpdateResponse:
        access_token = _extract_bearer_token(authorization)
        if not access_token:
            raise HTTPException(status_code=401, detail="Authorization header with Bearer token is required")

        user_id = await _resolve_user_id_from_token(access_token)

        if not (req.purchase_token or req.transaction_receipt or req.transaction_id):
            raise HTTPException(
                status_code=400,
                detail=_http_detail(
                    "purchase_proof_missing",
                    "purchase_token (Android), transaction_id (iOS), or transaction_receipt is required",
                ),
            )

        desired_tier = _resolve_tier_from_request(req)
        desired_plan_code = normalize_plan_code(desired_tier.value)
        if desired_tier not in (SubscriptionTier.PLUS, SubscriptionTier.PREMIUM) or not desired_plan_code:
            raise HTTPException(
                status_code=422,
                detail=_http_detail(
                    "tier_resolution_failed",
                    "Could not resolve a paid subscription tier from the purchase payload.",
                ),
            )

        store, purchase_token, transaction_id, original_transaction_id, store_ref = _resolve_request_refs(req)
        raw_payload = _storage_payload(req, plan_code=desired_plan_code, store_ref=store_ref)
        verification_mode = ""

        verifier_available = (
            is_android_verification_configured() if store == "android" else is_ios_verification_configured()
        )

        if verifier_available:
            verified_purchase: Optional[VerifiedPurchase] = None
            try:
                verified_purchase = await _verify_purchase_or_raise(req, store=store)
            except HTTPException as exc:
                detail = exc.detail if isinstance(exc.detail, dict) else {}
                if isinstance(detail, dict) and detail.get("code") in {
                    "subscription_pending",
                    "subscription_inactive",
                    "subscription_revoked",
                    "subscription_account_hold",
                    "subscription_paused",
                }:
                    if store == "android" and purchase_token:
                        try:
                            verified_purchase = await verify_android_subscription(
                                purchase_token=purchase_token,
                                product_id=clean_optional_str(req.product_id),
                            )
                        except AndroidVerificationInactive as inactive_exc:
                            verified_purchase = inactive_exc.verified_purchase
                        except Exception:
                            verified_purchase = None
                    elif store == "ios" and transaction_id:
                        try:
                            verified_purchase = await verify_ios_subscription(
                                transaction_id=transaction_id,
                                product_id=clean_optional_str(req.product_id),
                            )
                        except IOSVerificationInactive as inactive_exc:
                            verified_purchase = inactive_exc.verified_purchase
                        except Exception:
                            verified_purchase = None
                    if verified_purchase is not None:
                        await _persist_or_conflict(user_id, verified_purchase)
                raise

            snapshot = await _persist_or_conflict(user_id, verified_purchase)
            verification_mode = f"{store}_store_verification"

            if store == "android" and verified_purchase.needs_acknowledge and verified_purchase.purchase_token and verified_purchase.product_id:
                try:
                    await acknowledge_android_subscription(
                        purchase_token=verified_purchase.purchase_token,
                        product_id=verified_purchase.product_id,
                    )
                except Exception as exc:
                    logger.warning("Android acknowledge failed: %s", exc)

        else:
            try:
                existing_claim = await find_purchase_claim(
                    store=store,
                    purchase_token=purchase_token,
                    transaction_id=transaction_id,
                    original_transaction_id=original_transaction_id,
                )
            except Exception as exc:
                logger.warning("Failed to query purchase claims: %s", exc)
                existing_claim = None

            existing_entitlement = None
            try:
                existing_entitlement = await find_entitlement_by_store_ref(store, store_ref)
            except Exception as exc:
                logger.warning("Failed to query entitlements by store_ref: %s", exc)

            if existing_claim and clean_optional_str(existing_claim.get("user_id")) not in {None, user_id}:
                raise HTTPException(status_code=409, detail=_http_detail("purchase_already_claimed", "This purchase is already linked to another Cocolon account."))
            if existing_entitlement and clean_optional_str(existing_entitlement.get("user_id")) not in {None, user_id}:
                raise HTTPException(status_code=409, detail=_http_detail("purchase_already_claimed", "This purchase entitlement is already linked to another Cocolon account."))

            if existing_claim or existing_entitlement:
                snapshot = await project_profile_tier(user_id)
                verification_mode = "existing_entitlement_projection"
            else:
                allow_unverified, dev_mode = _verification_mode_for_user(user_id)
                if not allow_unverified:
                    raise HTTPException(
                        status_code=503,
                        detail=_http_detail(
                            "verification_unavailable",
                            "IAP verification is not configured. Finish the store-verification phase for production, or enable the explicit dev allowlist for local sync.",
                        ),
                    )

                verified_purchase = VerifiedPurchase(
                    store=store,
                    product_id=clean_optional_str(req.product_id) or clean_optional_str(desired_plan_code) or "",
                    plan_code=desired_plan_code,
                    status="active",
                    verification_status="verified",
                    store_ref=store_ref,
                    purchase_token=purchase_token,
                    transaction_id=transaction_id,
                    original_transaction_id=original_transaction_id,
                    starts_at=datetime.now(timezone.utc).isoformat(),
                    expires_at=None,
                    auto_renew=False,
                    source=f"subscription_update_{dev_mode or 'unverified_dev'}",
                    raw_payload=raw_payload,
                    app_user_id_hint=user_id,
                    needs_acknowledge=False,
                )
                snapshot = await _persist_or_conflict(user_id, verified_purchase)
                verification_mode = dev_mode or "unverified_dev"

        try:
            await touch_active_user(
                user_id,
                activity="subscription/update",
                subscription_tier=snapshot.subscription_tier,
                force=True,
            )
        except Exception:
            pass

        return _response_from_snapshot(snapshot, updated=True, verification=verification_mode or "unknown")
