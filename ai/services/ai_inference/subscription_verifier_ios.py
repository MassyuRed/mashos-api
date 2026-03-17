# -*- coding: utf-8 -*-
from __future__ import annotations

import base64
import json
import logging
import os
import time
from typing import Any, Dict, Optional
from urllib.parse import quote

import httpx
import jwt

from subscription_projection import (
    VerifiedPurchase,
    clean_optional_str,
    normalize_entitlement_status,
    normalize_plan_code,
    plan_code_from_product_id,
)

logger = logging.getLogger("subscription_verifier_ios")

_APPLE_TOKEN_CACHE: Dict[str, Any] = {"token": None, "expires_at": 0.0}


class IOSVerificationConfigError(RuntimeError):
    pass


class IOSVerificationError(RuntimeError):
    pass


class IOSVerificationInactive(RuntimeError):
    def __init__(self, code: str, message: str, verified_purchase: VerifiedPurchase):
        super().__init__(message)
        self.code = code
        self.message = message
        self.verified_purchase = verified_purchase



def _apple_private_key() -> str:
    raw = str(os.getenv("COCOLON_IAP_APPLE_PRIVATE_KEY", "")).replace("\\n", "\n").strip()
    if raw:
        return raw
    file_path = str(os.getenv("COCOLON_IAP_APPLE_PRIVATE_KEY_FILE", "")).strip()
    if file_path:
        with open(file_path, "r", encoding="utf-8") as fh:
            return fh.read()
    raise IOSVerificationConfigError("COCOLON_IAP_APPLE_PRIVATE_KEY is not configured")



def _apple_issuer_id() -> str:
    issuer_id = str(os.getenv("COCOLON_IAP_APPLE_ISSUER_ID", "")).strip()
    if not issuer_id:
        raise IOSVerificationConfigError("COCOLON_IAP_APPLE_ISSUER_ID is not configured")
    return issuer_id



def _apple_key_id() -> str:
    key_id = str(os.getenv("COCOLON_IAP_APPLE_KEY_ID", "")).strip()
    if not key_id:
        raise IOSVerificationConfigError("COCOLON_IAP_APPLE_KEY_ID is not configured")
    return key_id



def _apple_bundle_id() -> str:
    bundle_id = str(
        os.getenv("COCOLON_IAP_APPLE_BUNDLE_ID", "")
        or os.getenv("EXPO_PUBLIC_IOS_BUNDLE_ID", "")
        or os.getenv("IOS_BUNDLE_IDENTIFIER", "")
    ).strip()
    if not bundle_id:
        raise IOSVerificationConfigError("COCOLON_IAP_APPLE_BUNDLE_ID is not configured")
    return bundle_id



def is_ios_verification_configured() -> bool:
    try:
        _apple_private_key()
        _apple_issuer_id()
        _apple_key_id()
        _apple_bundle_id()
        return True
    except Exception:
        return False



def decode_apple_jws_payload(token: str) -> Dict[str, Any]:
    raw = clean_optional_str(token)
    if not raw:
        return {}
    try:
        payload = jwt.decode(
            raw,
            options={
                "verify_signature": False,
                "verify_aud": False,
                "verify_iss": False,
                "verify_exp": False,
                "verify_iat": False,
                "verify_nbf": False,
            },
            algorithms=["ES256", "RS256"],
        )
        return payload if isinstance(payload, dict) else {}
    except Exception:
        parts = raw.split(".")
        if len(parts) != 3:
            return {}
        try:
            padded = parts[1] + ("=" * (-len(parts[1]) % 4))
            return json.loads(base64.urlsafe_b64decode(padded.encode("utf-8")).decode("utf-8"))
        except Exception:
            return {}


async def _get_apple_bearer_token() -> str:
    now = time.time()
    cached = clean_optional_str(_APPLE_TOKEN_CACHE.get("token"))
    expires_at = float(_APPLE_TOKEN_CACHE.get("expires_at") or 0.0)
    if cached and expires_at - 60 > now:
        return cached

    issuer_id = _apple_issuer_id()
    key_id = _apple_key_id()
    bundle_id = _apple_bundle_id()
    private_key = _apple_private_key()

    iat = int(now)
    exp = iat + 55 * 60
    token = jwt.encode(
        {
            "iss": issuer_id,
            "iat": iat,
            "exp": exp,
            "aud": "appstoreconnect-v1",
            "bid": bundle_id,
        },
        private_key,
        algorithm="ES256",
        headers={"kid": key_id, "typ": "JWT"},
    )
    _APPLE_TOKEN_CACHE["token"] = token
    _APPLE_TOKEN_CACHE["expires_at"] = float(exp)
    return token


async def _apple_get(path: str) -> Dict[str, Any]:
    bearer = await _get_apple_bearer_token()
    bases = ["https://api.storekit.itunes.apple.com"]
    try_sandbox = str(os.getenv("COCOLON_IAP_APPLE_TRY_SANDBOX", "true")).strip().lower() in {"1", "true", "yes", "on"}
    if try_sandbox:
        bases.append("https://api.storekit-sandbox.itunes.apple.com")

    last_error: Optional[str] = None
    for base in bases:
        async with httpx.AsyncClient(timeout=12.0) as client:
            resp = await client.get(
                f"{base}{path}",
                headers={
                    "Authorization": f"Bearer {bearer}",
                    "Accept": "application/json",
                },
            )
        if resp.status_code < 300:
            data = resp.json()
            if isinstance(data, dict):
                data.setdefault("_apple_base_url", base)
                return data
            raise IOSVerificationError("Apple verification response was not a JSON object")

        last_error = f"status={resp.status_code} body={resp.text[:1200]}"
        if resp.status_code not in {400, 404, 410}:
            break

    raise IOSVerificationError(f"Apple verification failed: {last_error or 'unknown error'}")



def _parse_millis_to_iso(value: Any) -> Optional[str]:
    raw = clean_optional_str(value)
    if not raw:
        return None
    try:
        iv = int(float(raw))
        return time.strftime("%Y-%m-%dT%H:%M:%S+00:00", time.gmtime(iv / 1000.0))
    except Exception:
        return raw



def _map_apple_status(value: Any) -> str:
    if isinstance(value, str):
        raw = value.strip().upper()
        mapping = {
            "ACTIVE": "active",
            "EXPIRED": "expired",
            "BILLING_RETRY": "account_hold",
            "BILLING_GRACE_PERIOD": "grace_period",
            "REVOKED": "revoked",
        }
        if raw in mapping:
            return mapping[raw]
        if raw.isdigit():
            value = int(raw)
    if isinstance(value, int):
        mapping = {
            1: "active",
            2: "expired",
            3: "account_hold",
            4: "grace_period",
            5: "revoked",
        }
        return mapping.get(value, "expired")
    return "expired"



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



def _select_last_transaction(data: Dict[str, Any]) -> tuple[Dict[str, Any], Dict[str, Any], Dict[str, Any]]:
    groups = data.get("data") or []
    if not isinstance(groups, list):
        groups = []

    best_status: Optional[Any] = None
    best_tx: Dict[str, Any] = {}
    best_renewal: Dict[str, Any] = {}
    best_expires = -1

    for group in groups:
        group_dict = group if isinstance(group, dict) else {}
        for last_tx in group_dict.get("lastTransactions") or []:
            row = last_tx if isinstance(last_tx, dict) else {}
            tx_payload = decode_apple_jws_payload(row.get("signedTransactionInfo") or "")
            renewal_payload = decode_apple_jws_payload(row.get("signedRenewalInfo") or "")
            expires_ms = tx_payload.get("expiresDate") or tx_payload.get("expiresDateMs") or 0
            try:
                expires_num = int(float(str(expires_ms)))
            except Exception:
                expires_num = 0
            if expires_num >= best_expires:
                best_expires = expires_num
                best_status = row.get("status")
                best_tx = tx_payload
                best_renewal = renewal_payload

    return {"status": best_status}, best_tx, best_renewal


async def verify_ios_subscription(*, transaction_id: str, product_id: Optional[str] = None) -> VerifiedPurchase:
    tx = clean_optional_str(transaction_id)
    if not tx:
        raise IOSVerificationError("transaction_id is required for iOS verification")

    data = await _apple_get(f"/inApps/v1/subscriptions/{quote(tx, safe='')}")
    wrapper, tx_payload, renewal_payload = _select_last_transaction(data)
    status = _map_apple_status(wrapper.get("status"))

    resolved_product_id = clean_optional_str(tx_payload.get("productId")) or clean_optional_str(product_id)
    plan_code = normalize_plan_code(plan_code_from_product_id("ios", resolved_product_id))
    if not plan_code:
        raise IOSVerificationError(
            f"Could not map iOS product_id to plan_code: {resolved_product_id or '<empty>'}"
        )

    bundle_id = clean_optional_str(tx_payload.get("bundleId"))
    expected_bundle_id = _apple_bundle_id()
    if bundle_id and bundle_id != expected_bundle_id:
        raise IOSVerificationError(
            f"Apple bundleId mismatch: expected={expected_bundle_id} actual={bundle_id}"
        )

    original_transaction_id = clean_optional_str(tx_payload.get("originalTransactionId")) or tx
    app_user_id_hint = clean_optional_str(tx_payload.get("appAccountToken"))
    expires_at = _parse_millis_to_iso(tx_payload.get("expiresDate") or tx_payload.get("expiresDateMs"))
    starts_at = _parse_millis_to_iso(tx_payload.get("purchaseDate") or tx_payload.get("purchaseDateMs"))
    auto_renew_raw = renewal_payload.get("autoRenewStatus")
    auto_renew = auto_renew_raw in (1, "1", True, "true", "TRUE")
    verification_status = _verification_status_from_status(status)

    verified_purchase = VerifiedPurchase(
        store="ios",
        product_id=resolved_product_id or "",
        plan_code=plan_code,
        status=status,
        verification_status=verification_status,
        store_ref=original_transaction_id,
        purchase_token=None,
        transaction_id=clean_optional_str(tx_payload.get("transactionId")) or tx,
        original_transaction_id=original_transaction_id,
        starts_at=starts_at,
        expires_at=expires_at,
        auto_renew=bool(auto_renew),
        source="apple_app_store_verification",
        raw_payload={
            "subscription_status": data,
            "transaction_info": tx_payload,
            "renewal_info": renewal_payload,
        },
        app_user_id_hint=app_user_id_hint,
        needs_acknowledge=False,
    )

    if status in {"expired", "revoked", "account_hold", "pending", "paused"}:
        code_map = {
            "expired": "subscription_inactive",
            "revoked": "subscription_revoked",
            "account_hold": "subscription_account_hold",
            "pending": "subscription_pending",
            "paused": "subscription_paused",
        }
        message_map = {
            "expired": "このサブスクリプションは現在有効ではありません。",
            "revoked": "このサブスクリプションは取り消されています。",
            "account_hold": "このサブスクリプションはお支払い保留中です。App Store のお支払い設定をご確認ください。",
            "pending": "購入がまだ確定していません。購入完了後にもう一度お試しください。",
            "paused": "このサブスクリプションは一時停止中です。",
        }
        raise IOSVerificationInactive(
            code_map.get(status, "subscription_inactive"),
            message_map.get(status, "このサブスクリプションは現在有効ではありません。"),
            verified_purchase,
        )

    return verified_purchase
