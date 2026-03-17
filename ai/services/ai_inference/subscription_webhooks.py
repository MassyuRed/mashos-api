# -*- coding: utf-8 -*-
from __future__ import annotations

import base64
import json
import logging
import os
from typing import Any, Dict, Optional

from fastapi import FastAPI, Header, HTTPException, Request

from subscription_projection import (
    PurchaseOwnershipConflictError,
    clean_optional_str,
    log_store_notification,
    mark_store_notification_processed,
    persist_verified_purchase,
    resolve_user_id_for_purchase,
)
from subscription_verifier_android import (
    AndroidVerificationInactive,
    acknowledge_android_subscription,
    is_android_verification_configured,
    verify_android_subscription,
)
from subscription_verifier_ios import (
    IOSVerificationInactive,
    decode_apple_jws_payload,
    is_ios_verification_configured,
    verify_ios_subscription,
)

logger = logging.getLogger("subscription_webhooks")


async def _read_json_body(request: Request) -> Dict[str, Any]:
    try:
        body = await request.json()
        return body if isinstance(body, dict) else {}
    except Exception:
        return {}



def _require_optional_bearer(header_value: Optional[str], expected_token_env: str) -> None:
    expected = str(os.getenv(expected_token_env, "")).strip()
    if not expected:
        return
    auth = str(header_value or "").strip()
    if auth != f"Bearer {expected}":
        raise HTTPException(status_code=401, detail="Unauthorized webhook")



def _decode_google_pubsub_message(payload: Dict[str, Any]) -> tuple[str, str, Dict[str, Any]]:
    message = payload.get("message") if isinstance(payload.get("message"), dict) else {}
    message_id = clean_optional_str(message.get("messageId")) or clean_optional_str(payload.get("messageId")) or "google-webhook"
    raw_data = clean_optional_str(message.get("data"))
    decoded: Dict[str, Any] = {}
    if raw_data:
        try:
            padded = raw_data + ("=" * (-len(raw_data) % 4))
            decoded = json.loads(base64.b64decode(padded).decode("utf-8"))
            if not isinstance(decoded, dict):
                decoded = {}
        except Exception:
            decoded = {}
    elif isinstance(payload.get("developerNotification"), dict):
        decoded = payload
    subscription_notification = decoded.get("subscriptionNotification") if isinstance(decoded.get("subscriptionNotification"), dict) else {}
    event_type = clean_optional_str(subscription_notification.get("notificationType")) or "subscriptionNotification"
    return message_id, event_type, decoded



def _decode_apple_notification(payload: Dict[str, Any]) -> tuple[str, str, Dict[str, Any], Dict[str, Any], Dict[str, Any]]:
    signed_payload = clean_optional_str(payload.get("signedPayload"))
    outer = decode_apple_jws_payload(signed_payload or "")
    data = outer.get("data") if isinstance(outer.get("data"), dict) else {}
    tx_payload = decode_apple_jws_payload(data.get("signedTransactionInfo") or "")
    renewal_payload = decode_apple_jws_payload(data.get("signedRenewalInfo") or "")
    event_id = clean_optional_str(outer.get("notificationUUID")) or clean_optional_str(tx_payload.get("transactionId")) or "apple-webhook"
    notification_type = clean_optional_str(outer.get("notificationType")) or "notification"
    subtype = clean_optional_str(outer.get("subtype"))
    event_type = f"{notification_type}.{subtype}" if subtype else notification_type
    return event_id, event_type, outer, tx_payload, renewal_payload



def register_subscription_webhook_routes(app: FastAPI) -> None:
    @app.post("/subscription/webhooks/google")
    async def google_subscription_webhook(
        request: Request,
        authorization: Optional[str] = Header(default=None, alias="Authorization"),
    ) -> Dict[str, Any]:
        _require_optional_bearer(authorization, "COCOLON_IAP_GOOGLE_WEBHOOK_BEARER")
        payload = await _read_json_body(request)
        event_id, event_type, decoded = _decode_google_pubsub_message(payload)
        notification = await log_store_notification(
            store="android",
            event_id=event_id,
            event_type=event_type,
            payload=decoded or payload,
        )

        if bool(notification.get("processed")):
            return {"ok": True, "duplicate": True}

        try:
            sub_n = decoded.get("subscriptionNotification") if isinstance(decoded.get("subscriptionNotification"), dict) else {}
            purchase_token = clean_optional_str(sub_n.get("purchaseToken"))
            product_id = clean_optional_str(sub_n.get("subscriptionId"))
            if not purchase_token:
                await mark_store_notification_processed(notification.get("id"), processed=True, error_message="no_purchase_token")
                return {"ok": True, "logged_only": True}

            if not is_android_verification_configured():
                await mark_store_notification_processed(notification.get("id"), processed=False, error_message="google_verification_not_configured")
                return {"ok": True, "logged_only": True}

            try:
                verified = await verify_android_subscription(purchase_token=purchase_token, product_id=product_id)
            except AndroidVerificationInactive as exc:
                verified = exc.verified_purchase
            user_id = await resolve_user_id_for_purchase(
                store="android",
                purchase_token=verified.purchase_token,
                transaction_id=verified.transaction_id,
                original_transaction_id=verified.original_transaction_id,
                app_user_id_hint=verified.app_user_id_hint,
            )
            if not user_id:
                await mark_store_notification_processed(notification.get("id"), processed=True, error_message="no_user_mapping")
                return {"ok": True, "logged_only": True}

            await persist_verified_purchase(user_id=user_id, verified_purchase=verified)
            if verified.needs_acknowledge and verified.purchase_token and verified.product_id:
                await acknowledge_android_subscription(
                    purchase_token=verified.purchase_token,
                    product_id=verified.product_id,
                )

            await mark_store_notification_processed(notification.get("id"), processed=True)
            return {"ok": True, "processed": True}
        except PurchaseOwnershipConflictError as exc:
            await mark_store_notification_processed(notification.get("id"), processed=False, error_message=str(exc))
            return {"ok": True, "conflict": True}
        except Exception as exc:
            logger.warning("Google webhook processing failed: %s", exc)
            await mark_store_notification_processed(notification.get("id"), processed=False, error_message=str(exc))
            return {"ok": True, "processed": False}

    @app.post("/subscription/webhooks/apple")
    async def apple_subscription_webhook(request: Request) -> Dict[str, Any]:
        payload = await _read_json_body(request)
        event_id, event_type, outer, tx_payload, renewal_payload = _decode_apple_notification(payload)
        notification = await log_store_notification(
            store="ios",
            event_id=event_id,
            event_type=event_type,
            payload={
                "outer": outer,
                "transaction_info": tx_payload,
                "renewal_info": renewal_payload,
            },
        )

        if bool(notification.get("processed")):
            return {"ok": True, "duplicate": True}

        try:
            transaction_id = clean_optional_str(tx_payload.get("transactionId")) or clean_optional_str(tx_payload.get("originalTransactionId"))
            product_id = clean_optional_str(tx_payload.get("productId"))
            if not transaction_id:
                await mark_store_notification_processed(notification.get("id"), processed=True, error_message="no_transaction_id")
                return {"ok": True, "logged_only": True}

            if not is_ios_verification_configured():
                await mark_store_notification_processed(notification.get("id"), processed=False, error_message="ios_verification_not_configured")
                return {"ok": True, "logged_only": True}

            try:
                verified = await verify_ios_subscription(transaction_id=transaction_id, product_id=product_id)
            except IOSVerificationInactive as exc:
                verified = exc.verified_purchase

            user_id = await resolve_user_id_for_purchase(
                store="ios",
                purchase_token=None,
                transaction_id=verified.transaction_id,
                original_transaction_id=verified.original_transaction_id,
                app_user_id_hint=verified.app_user_id_hint,
            )
            if not user_id:
                await mark_store_notification_processed(notification.get("id"), processed=True, error_message="no_user_mapping")
                return {"ok": True, "logged_only": True}

            await persist_verified_purchase(user_id=user_id, verified_purchase=verified)
            await mark_store_notification_processed(notification.get("id"), processed=True)
            return {"ok": True, "processed": True}
        except PurchaseOwnershipConflictError as exc:
            await mark_store_notification_processed(notification.get("id"), processed=False, error_message=str(exc))
            return {"ok": True, "conflict": True}
        except Exception as exc:
            logger.warning("Apple webhook processing failed: %s", exc)
            await mark_store_notification_processed(notification.get("id"), processed=False, error_message=str(exc))
            return {"ok": True, "processed": False}
