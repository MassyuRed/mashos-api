# -*- coding: utf-8 -*-
from __future__ import annotations

import json
import logging
import os
import time
from typing import Any, Dict, Optional
from urllib.parse import quote

import httpx
import jwt

from subscription_bootstrap_store import resolve_plan_code_by_product_id
from subscription_projection import (
    VerifiedPurchase,
    clean_optional_str,
    normalize_entitlement_status,
    normalize_plan_code,
)

logger = logging.getLogger("subscription_verifier_android")

_GOOGLE_SCOPE = "https://www.googleapis.com/auth/androidpublisher"
_GOOGLE_TOKEN_CACHE: Dict[str, Any] = {"access_token": None, "expires_at": 0.0}


class AndroidVerificationConfigError(RuntimeError):
    pass


class AndroidVerificationError(RuntimeError):
    pass


class AndroidVerificationInactive(RuntimeError):
    def __init__(self, code: str, message: str, verified_purchase: VerifiedPurchase):
        super().__init__(message)
        self.code = code
        self.message = message
        self.verified_purchase = verified_purchase



def _load_service_account_info() -> Dict[str, Any]:
    raw_json = str(
        os.getenv("COCOLON_IAP_GOOGLE_SERVICE_ACCOUNT_JSON", "")
        or os.getenv("GOOGLE_PLAY_SERVICE_ACCOUNT_JSON", "")
    ).strip()
    if raw_json:
        return json.loads(raw_json)

    file_path = str(
        os.getenv("COCOLON_IAP_GOOGLE_SERVICE_ACCOUNT_JSON_FILE", "")
        or os.getenv("GOOGLE_PLAY_SERVICE_ACCOUNT_JSON_FILE", "")
    ).strip()
    if file_path:
        with open(file_path, "r", encoding="utf-8") as fh:
            return json.load(fh)

    client_email = str(os.getenv("COCOLON_IAP_GOOGLE_CLIENT_EMAIL", "")).strip()
    private_key = str(os.getenv("COCOLON_IAP_GOOGLE_PRIVATE_KEY", "")).replace("\\n", "\n").strip()
    token_uri = str(os.getenv("COCOLON_IAP_GOOGLE_TOKEN_URI", "https://oauth2.googleapis.com/token")).strip()
    if client_email and private_key:
        return {
            "client_email": client_email,
            "private_key": private_key,
            "token_uri": token_uri,
        }

    raise AndroidVerificationConfigError(
        "Google Play service account credentials are not configured."
    )



def is_android_verification_configured() -> bool:
    if not str(
        os.getenv("COCOLON_IAP_ANDROID_PACKAGE_NAME", "")
        or os.getenv("ANDROID_PACKAGE_NAME", "")
    ).strip():
        return False
    try:
        _load_service_account_info()
        return True
    except Exception:
        return False


async def _get_google_access_token() -> str:
    now = time.time()
    cached_token = clean_optional_str(_GOOGLE_TOKEN_CACHE.get("access_token"))
    expires_at = float(_GOOGLE_TOKEN_CACHE.get("expires_at") or 0.0)
    if cached_token and expires_at - 60 > now:
        return cached_token

    info = _load_service_account_info()
    token_uri = str(info.get("token_uri") or "https://oauth2.googleapis.com/token").strip()
    client_email = str(info.get("client_email") or "").strip()
    private_key = str(info.get("private_key") or "").replace("\\n", "\n").strip()
    if not client_email or not private_key:
        raise AndroidVerificationConfigError(
            "Google Play service account credentials are incomplete."
        )

    iat = int(now)
    exp = iat + 3600
    assertion = jwt.encode(
        {
            "iss": client_email,
            "scope": _GOOGLE_SCOPE,
            "aud": token_uri,
            "iat": iat,
            "exp": exp,
        },
        private_key,
        algorithm="RS256",
    )

    async with httpx.AsyncClient(timeout=12.0) as client:
        resp = await client.post(
            token_uri,
            data={
                "grant_type": "urn:ietf:params:oauth:grant-type:jwt-bearer",
                "assertion": assertion,
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )

    if resp.status_code >= 300:
        raise AndroidVerificationConfigError(
            f"Failed to get Google access token: status={resp.status_code} body={resp.text[:800]}"
        )

    data = resp.json()
    token = clean_optional_str(data.get("access_token"))
    expires_in = int(data.get("expires_in") or 3600)
    if not token:
        raise AndroidVerificationConfigError("Google token response did not include access_token")

    _GOOGLE_TOKEN_CACHE["access_token"] = token
    _GOOGLE_TOKEN_CACHE["expires_at"] = now + max(60, expires_in)
    return token



def _google_package_name() -> str:
    package_name = str(
        os.getenv("COCOLON_IAP_ANDROID_PACKAGE_NAME", "")
        or os.getenv("ANDROID_PACKAGE_NAME", "")
    ).strip()
    if not package_name:
        raise AndroidVerificationConfigError(
            "COCOLON_IAP_ANDROID_PACKAGE_NAME (or ANDROID_PACKAGE_NAME) is required for Google Play verification."
        )
    return package_name



def _select_line_item(data: Dict[str, Any], product_id: Optional[str]) -> Dict[str, Any]:
    requested = clean_optional_str(product_id)
    items = data.get("lineItems") or []
    if not isinstance(items, list):
        items = []
    if requested:
        for item in items:
            if clean_optional_str((item or {}).get("productId")) == requested:
                return item if isinstance(item, dict) else {}
    if items:
        return items[0] if isinstance(items[0], dict) else {}
    return {}



def _map_google_state_to_status(state: Optional[str]) -> str:
    raw = str(state or "").strip().upper()
    mapping = {
        "SUBSCRIPTION_STATE_ACTIVE": "active",
        "SUBSCRIPTION_STATE_IN_GRACE_PERIOD": "grace_period",
        "SUBSCRIPTION_STATE_ON_HOLD": "account_hold",
        "SUBSCRIPTION_STATE_PAUSED": "paused",
        "SUBSCRIPTION_STATE_CANCELED": "cancelled",
        "SUBSCRIPTION_STATE_EXPIRED": "expired",
        "SUBSCRIPTION_STATE_PENDING": "pending",
        "SUBSCRIPTION_STATE_PENDING_PURCHASE_CANCELED": "revoked",
    }
    return mapping.get(raw, "expired")



def _verification_status_from_status(status: str) -> str:
    status = normalize_entitlement_status(status)
    if status in {"active", "grace_period", "cancelled"}:
        return "verified"
    if status == "pending":
        return "pending"
    if status == "revoked":
        return "revoked"
    if status in {"expired", "account_hold", "paused"}:
        return "expired"
    return "error"


async def acknowledge_android_subscription(*, purchase_token: str, product_id: str) -> None:
    token = await _get_google_access_token()
    package_name = _google_package_name()
    url = (
        "https://androidpublisher.googleapis.com/androidpublisher/v3/"
        f"applications/{quote(package_name, safe='')}/purchases/subscriptions/"
        f"{quote(product_id, safe='')}/tokens/{quote(purchase_token, safe='')}:acknowledge"
    )
    async with httpx.AsyncClient(timeout=12.0) as client:
        resp = await client.post(
            url,
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
            },
            json={},
        )
    if resp.status_code >= 300:
        logger.warning(
            "Failed to acknowledge Android subscription: status=%s body=%s",
            resp.status_code,
            resp.text[:800],
        )


async def verify_android_subscription(*, purchase_token: str, product_id: Optional[str] = None) -> VerifiedPurchase:
    token = clean_optional_str(purchase_token)
    if not token:
        raise AndroidVerificationError("purchase_token is required for Android verification")

    access_token = await _get_google_access_token()
    package_name = _google_package_name()
    url = (
        "https://androidpublisher.googleapis.com/androidpublisher/v3/"
        f"applications/{quote(package_name, safe='')}/purchases/subscriptionsv2/tokens/{quote(token, safe='')}"
    )

    async with httpx.AsyncClient(timeout=12.0) as client:
        resp = await client.get(
            url,
            headers={
                "Authorization": f"Bearer {access_token}",
                "Accept": "application/json",
            },
        )

    if resp.status_code >= 300:
        raise AndroidVerificationError(
            f"Google Play verification failed: status={resp.status_code} body={resp.text[:1000]}"
        )

    data = resp.json()
    line_item = _select_line_item(data, product_id)
    resolved_product_id = clean_optional_str(line_item.get("productId")) or clean_optional_str(product_id)
    plan_code = normalize_plan_code(await resolve_plan_code_by_product_id("android", resolved_product_id))
    if not plan_code:
        raise AndroidVerificationError(
            f"Could not map Android product_id to plan_code: {resolved_product_id or '<empty>'}"
        )

    status = _map_google_state_to_status(data.get("subscriptionState"))
    verification_status = _verification_status_from_status(status)
    auto_renew_plan = line_item.get("autoRenewingPlan") if isinstance(line_item, dict) else None
    auto_renew = bool(auto_renew_plan) and status not in {"expired", "revoked", "paused", "account_hold"}
    expires_at = clean_optional_str(line_item.get("expiryTime"))
    starts_at = clean_optional_str(data.get("startTime"))
    external_ids = data.get("externalAccountIdentifiers") if isinstance(data.get("externalAccountIdentifiers"), dict) else {}
    app_user_id_hint = clean_optional_str(external_ids.get("obfuscatedExternalAccountId"))
    acknowledgement_state = str(data.get("acknowledgementState") or "").strip().upper()
    needs_acknowledge = acknowledgement_state == "ACKNOWLEDGEMENT_STATE_PENDING"

    verified_purchase = VerifiedPurchase(
        store="android",
        product_id=resolved_product_id or "",
        plan_code=plan_code,
        status=status,
        verification_status=verification_status,
        store_ref=token,
        purchase_token=token,
        transaction_id=clean_optional_str(data.get("latestOrderId")),
        original_transaction_id=clean_optional_str(data.get("linkedPurchaseToken")),
        starts_at=starts_at,
        expires_at=expires_at,
        auto_renew=auto_renew,
        source="google_play_verification",
        raw_payload=data,
        app_user_id_hint=app_user_id_hint,
        needs_acknowledge=needs_acknowledge,
    )

    if status in {"pending", "expired", "revoked", "account_hold", "paused"}:
        code_map = {
            "pending": "subscription_pending",
            "expired": "subscription_inactive",
            "revoked": "subscription_revoked",
            "account_hold": "subscription_account_hold",
            "paused": "subscription_paused",
        }
        message_map = {
            "pending": "Google Play で購入がまだ確定していません。購入完了後にもう一度お試しください。",
            "expired": "このサブスクリプションは現在有効ではありません。",
            "revoked": "このサブスクリプションは取り消されています。",
            "account_hold": "このサブスクリプションは支払い保留中です。Google Play のお支払い設定をご確認ください。",
            "paused": "このサブスクリプションは一時停止中です。",
        }
        raise AndroidVerificationInactive(code_map[status], message_map[status], verified_purchase)

    return verified_purchase
