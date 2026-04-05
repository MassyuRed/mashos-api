# -*- coding: utf-8 -*-
from __future__ import annotations

import os
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, Header, HTTPException
from pydantic import BaseModel, Field

from subscription_bootstrap_store import audit_subscription_bootstrap_runtime


def _clean(value: Any) -> str:
    return str(value or "").strip()


def _first_env(*names: str) -> str:
    for name in names:
        value = _clean(os.getenv(name, ""))
        if value:
            return value
    return ""


def _split_csv(raw: str) -> list[str]:
    return [part.strip() for part in str(raw or "").split(",") if part.strip()]


def _csv_env(*names: str) -> list[str]:
    return _split_csv(_first_env(*names))


def _bool_env(name: str, default: bool = False) -> bool:
    raw = os.getenv(name)
    if raw is None:
        return default
    return str(raw).strip().lower() in {"1", "true", "yes", "on"}


def _normalize_url(raw: str) -> str:
    value = _clean(raw)
    return value.rstrip("/") if value else ""


def _join_url(base: str, path: str) -> str:
    normalized = _normalize_url(base)
    if not normalized:
        return ""
    return f"{normalized}{path if path.startswith('/') else '/' + path}"


def _public_api_base_url() -> str:
    return _normalize_url(
        _first_env(
            "COCOLON_IAP_PUBLIC_API_BASE_URL",
            "MYMODEL_PUBLIC_BASE_URL",
            "RENDER_EXTERNAL_URL",
            "EXPO_PUBLIC_MYMODEL_API_URL",
        )
    )


def _apple_private_key_source() -> str:
    if _clean(os.getenv("COCOLON_IAP_APPLE_PRIVATE_KEY", "")):
        return "COCOLON_IAP_APPLE_PRIVATE_KEY"
    if _clean(os.getenv("COCOLON_IAP_APPLE_PRIVATE_KEY_FILE", "")):
        return "COCOLON_IAP_APPLE_PRIVATE_KEY_FILE"
    return ""


def _google_service_account_source() -> str:
    if _clean(_first_env("COCOLON_IAP_GOOGLE_SERVICE_ACCOUNT_JSON", "GOOGLE_PLAY_SERVICE_ACCOUNT_JSON")):
        return "service_account_json"
    if _clean(_first_env("COCOLON_IAP_GOOGLE_SERVICE_ACCOUNT_JSON_FILE", "GOOGLE_PLAY_SERVICE_ACCOUNT_JSON_FILE")):
        return "service_account_json_file"
    if _clean(os.getenv("COCOLON_IAP_GOOGLE_CLIENT_EMAIL", "")) and _clean(os.getenv("COCOLON_IAP_GOOGLE_PRIVATE_KEY", "")):
        return "client_email_private_key"
    return ""


def _ios_bundle_id() -> str:
    return _first_env(
        "COCOLON_IAP_APPLE_BUNDLE_ID",
        "APPLE_BUNDLE_ID",
        "EXPO_PUBLIC_IOS_BUNDLE_ID",
        "IOS_BUNDLE_IDENTIFIER",
    )


def _android_package_name() -> str:
    return _first_env(
        "COCOLON_IAP_ANDROID_PACKAGE_NAME",
        "GOOGLE_PLAY_PACKAGE_NAME",
        "ANDROID_PACKAGE_NAME",
        "EXPO_PUBLIC_ANDROID_PACKAGE_NAME",
    )


def _internal_admin_tokens() -> list[str]:
    values = [
        _clean(os.getenv("COCOLON_SUBSCRIPTION_ADMIN_BEARER", "")),
        _clean(os.getenv("INTERNAL_API_TOKEN", "")),
        _clean(os.getenv("INTERNAL_ROLLOVER_TOKEN", "")),
        _clean(os.getenv("CRON_INTERNAL_TOKEN", "")),
    ]
    return [value for value in values if value]


def _require_admin_bearer(authorization: Optional[str]) -> None:
    expected = _internal_admin_tokens()
    if not expected:
        return
    auth = _clean(authorization)
    if not auth.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Unauthorized")
    token = auth[7:].strip()
    if token not in expected:
        raise HTTPException(status_code=401, detail="Unauthorized")


def _is_ios_verification_ready() -> bool:
    try:
        from subscription_verifier_ios import is_ios_verification_configured

        return bool(is_ios_verification_configured())
    except Exception:
        return False


def _is_android_verification_ready() -> bool:
    try:
        from subscription_verifier_android import is_android_verification_configured

        return bool(is_android_verification_configured())
    except Exception:
        return False


def _detected_public_snapshot() -> Dict[str, Any]:
    return {
        "api_base_url": _normalize_url(_first_env("EXPO_PUBLIC_MYMODEL_API_URL")),
        "ios_bundle_id": _first_env("EXPO_PUBLIC_IOS_BUNDLE_ID"),
        "android_package_name": _first_env("EXPO_PUBLIC_ANDROID_PACKAGE_NAME"),
        "plus_sku_ios": _first_env("EXPO_PUBLIC_IAP_PLUS_SKU_IOS"),
        "plus_sku_android": _first_env("EXPO_PUBLIC_IAP_PLUS_SKU_ANDROID"),
        "premium_sku_ios": _first_env("EXPO_PUBLIC_IAP_PREMIUM_SKU_IOS"),
        "premium_sku_android": _first_env("EXPO_PUBLIC_IAP_PREMIUM_SKU_ANDROID"),
        "android_plus_base_plan_id": _first_env("EXPO_PUBLIC_IAP_ANDROID_PLUS_BASE_PLAN_ID"),
        "android_premium_base_plan_id": _first_env("EXPO_PUBLIC_IAP_ANDROID_PREMIUM_BASE_PLAN_ID"),
        "terms_url": _first_env("EXPO_PUBLIC_TERMS_URL"),
        "privacy_url": _first_env("EXPO_PUBLIC_PRIVACY_URL"),
        "support_url": _first_env("EXPO_PUBLIC_SUPPORT_URL"),
    }


def _comparison_payload(public_snapshot: Optional[Dict[str, Any]], *, backend: Dict[str, Any]) -> Dict[str, Any]:
    snapshot = dict(public_snapshot or {})
    matches: list[Dict[str, str]] = []
    mismatches: list[Dict[str, str]] = []
    warnings: list[str] = []

    def compare_equal(label: str, public_value: Any, backend_value: Any, *, normalize_url: bool = False) -> None:
        left = _normalize_url(public_value) if normalize_url else _clean(public_value)
        right = _normalize_url(backend_value) if normalize_url else _clean(backend_value)
        if not left:
            return
        if not right:
            warnings.append(f"{label}: backend value is not configured yet.")
            return
        if left == right:
            matches.append({"field": label, "value": left})
        else:
            mismatches.append({"field": label, "public": left, "backend": right})

    def compare_membership(label: str, public_value: Any, backend_values: List[str]) -> None:
        left = _clean(public_value)
        if not left:
            return
        right = [value for value in backend_values if _clean(value)]
        if not right:
            warnings.append(f"{label}: backend product id list is empty.")
            return
        if left in right:
            matches.append({"field": label, "value": left})
        else:
            mismatches.append({"field": label, "public": left, "backend": ", ".join(right)})

    compare_equal("api_base_url", snapshot.get("api_base_url"), backend.get("public_api_base_url"), normalize_url=True)
    compare_equal("ios_bundle_id", snapshot.get("ios_bundle_id"), backend.get("ios_bundle_id"))
    compare_equal("android_package_name", snapshot.get("android_package_name"), backend.get("android_package_name"))
    compare_membership("plus_sku_ios", snapshot.get("plus_sku_ios"), backend.get("ios_plus_product_ids") or [])
    compare_membership("plus_sku_android", snapshot.get("plus_sku_android"), backend.get("android_plus_product_ids") or [])
    compare_membership("premium_sku_ios", snapshot.get("premium_sku_ios"), backend.get("ios_premium_product_ids") or [])
    compare_membership("premium_sku_android", snapshot.get("premium_sku_android"), backend.get("android_premium_product_ids") or [])
    compare_membership("android_plus_base_plan_id", snapshot.get("android_plus_base_plan_id"), backend.get("android_plus_base_plan_ids") or [])
    compare_membership("android_premium_base_plan_id", snapshot.get("android_premium_base_plan_id"), backend.get("android_premium_base_plan_ids") or [])

    if _clean(snapshot.get("terms_url")):
        warnings.append("terms_url: EXPO_PUBLIC_TERMS_URL is set, but runtime legal links are now sourced from /subscription/bootstrap.")
    if _clean(snapshot.get("privacy_url")):
        warnings.append("privacy_url: EXPO_PUBLIC_PRIVACY_URL is set, but runtime legal links are now sourced from /subscription/bootstrap.")
    if _clean(snapshot.get("support_url")):
        warnings.append("support_url: EXPO_PUBLIC_SUPPORT_URL is set, but runtime legal links are now sourced from /subscription/bootstrap.")

    ready = len(mismatches) == 0
    return {
        "provided": snapshot,
        "matches": matches,
        "mismatches": mismatches,
        "warnings": warnings,
        "ready": ready,
    }


class PublicSubscriptionConfigRequest(BaseModel):
    api_base_url: Optional[str] = Field(default=None)
    ios_bundle_id: Optional[str] = Field(default=None)
    android_package_name: Optional[str] = Field(default=None)
    plus_sku_ios: Optional[str] = Field(default=None)
    plus_sku_android: Optional[str] = Field(default=None)
    premium_sku_ios: Optional[str] = Field(default=None)
    premium_sku_android: Optional[str] = Field(default=None)
    android_plus_base_plan_id: Optional[str] = Field(default=None)
    android_premium_base_plan_id: Optional[str] = Field(default=None)
    terms_url: Optional[str] = Field(default=None)
    privacy_url: Optional[str] = Field(default=None)
    support_url: Optional[str] = Field(default=None)


async def build_subscription_release_report(*, public_snapshot: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    ios_plus_ids = _csv_env("COCOLON_IAP_IOS_PLUS_PRODUCT_IDS")
    ios_premium_ids = _csv_env("COCOLON_IAP_IOS_PREMIUM_PRODUCT_IDS")
    android_plus_ids = _csv_env("COCOLON_IAP_ANDROID_PLUS_PRODUCT_IDS")
    android_premium_ids = _csv_env("COCOLON_IAP_ANDROID_PREMIUM_PRODUCT_IDS")
    android_plus_base_plan_ids = _csv_env("COCOLON_IAP_ANDROID_PLUS_BASE_PLAN_IDS") or ["plus"]
    android_premium_base_plan_ids = _csv_env("COCOLON_IAP_ANDROID_PREMIUM_BASE_PLAN_IDS") or ["premium"]

    public_api_base_url = _public_api_base_url()
    ios_bundle_id = _ios_bundle_id()
    android_package_name = _android_package_name()
    apple_key_source = _apple_private_key_source()
    google_sa_source = _google_service_account_source()
    allow_unverified = _bool_env("COCOLON_IAP_ALLOW_UNVERIFIED", default=False)
    try_sandbox = _bool_env("COCOLON_IAP_APPLE_TRY_SANDBOX", default=True)

    backend_missing: list[str] = []
    if not public_api_base_url:
        backend_missing.append("COCOLON_IAP_PUBLIC_API_BASE_URL")
    if not ios_bundle_id:
        backend_missing.append("COCOLON_IAP_APPLE_BUNDLE_ID")
    if not _clean(os.getenv("COCOLON_IAP_APPLE_ISSUER_ID", "")):
        backend_missing.append("COCOLON_IAP_APPLE_ISSUER_ID")
    if not _clean(os.getenv("COCOLON_IAP_APPLE_KEY_ID", "")):
        backend_missing.append("COCOLON_IAP_APPLE_KEY_ID")
    if not apple_key_source:
        backend_missing.append("COCOLON_IAP_APPLE_PRIVATE_KEY or COCOLON_IAP_APPLE_PRIVATE_KEY_FILE")
    if not ios_plus_ids:
        backend_missing.append("COCOLON_IAP_IOS_PLUS_PRODUCT_IDS")
    if not android_package_name:
        backend_missing.append("COCOLON_IAP_ANDROID_PACKAGE_NAME")
    if not google_sa_source:
        backend_missing.append("COCOLON_IAP_GOOGLE_SERVICE_ACCOUNT_JSON / FILE")
    if not android_plus_ids:
        backend_missing.append("COCOLON_IAP_ANDROID_PLUS_PRODUCT_IDS")
    if not ios_premium_ids:
        backend_missing.append("COCOLON_IAP_IOS_PREMIUM_PRODUCT_IDS")
    if not android_premium_ids:
        backend_missing.append("COCOLON_IAP_ANDROID_PREMIUM_PRODUCT_IDS")
    if not _csv_env("COCOLON_IAP_ANDROID_PLUS_BASE_PLAN_IDS"):
        backend_missing.append("COCOLON_IAP_ANDROID_PLUS_BASE_PLAN_IDS")
    if not _csv_env("COCOLON_IAP_ANDROID_PREMIUM_BASE_PLAN_IDS"):
        backend_missing.append("COCOLON_IAP_ANDROID_PREMIUM_BASE_PLAN_IDS")

    warnings: list[str] = []
    if allow_unverified:
        warnings.append("COCOLON_IAP_ALLOW_UNVERIFIED is ON. Turn it OFF before production release.")
    if not _clean(os.getenv("COCOLON_IAP_GOOGLE_WEBHOOK_BEARER", "")):
        warnings.append("COCOLON_IAP_GOOGLE_WEBHOOK_BEARER is not set. Add a bearer token if the Google webhook endpoint is internet-reachable.")
    if not _internal_admin_tokens():
        warnings.append("No internal admin bearer token is configured. /subscription/config/release-check will be publicly readable until an admin token is set.")
    if android_plus_ids and android_premium_ids and set(android_plus_ids) == set(android_premium_ids):
        warnings.append("Android plus/premium product ids are shared. This is expected when Google Play uses one subscription product with multiple base plans.")

    backend_resolved = {
        "public_api_base_url": public_api_base_url,
        "ios_bundle_id": ios_bundle_id,
        "android_package_name": android_package_name,
        "ios_plus_product_ids": ios_plus_ids,
        "ios_premium_product_ids": ios_premium_ids,
        "android_plus_product_ids": android_plus_ids,
        "android_premium_product_ids": android_premium_ids,
        "android_plus_base_plan_ids": android_plus_base_plan_ids,
        "android_premium_base_plan_ids": android_premium_base_plan_ids,
        "apple_private_key_source": apple_key_source or None,
        "google_service_account_source": google_sa_source or None,
        "google_webhook_bearer_configured": bool(_clean(os.getenv("COCOLON_IAP_GOOGLE_WEBHOOK_BEARER", ""))),
        "allow_unverified": allow_unverified,
        "allow_unverified_user_ids_count": len(_csv_env("COCOLON_IAP_ALLOW_UNVERIFIED_USER_IDS")),
        "apple_try_sandbox": try_sandbox,
        "apple_verification_ready": _is_ios_verification_ready(),
        "google_verification_ready": _is_android_verification_ready(),
        "apple_notifications": {
            "production_url": _join_url(public_api_base_url, "/subscription/webhooks/apple"),
            "sandbox_url": _join_url(public_api_base_url, "/subscription/webhooks/apple"),
        },
        "google_notifications": {
            "push_url": _join_url(public_api_base_url, "/subscription/webhooks/google"),
            "bearer_header_env": "COCOLON_IAP_GOOGLE_WEBHOOK_BEARER",
        },
    }

    public_env_reference = {
        "required": [
            "EXPO_PUBLIC_MYMODEL_API_URL",
            "EXPO_PUBLIC_IAP_PLUS_SKU_IOS",
            "EXPO_PUBLIC_IAP_PLUS_SKU_ANDROID",
            "EXPO_PUBLIC_IAP_PREMIUM_SKU_IOS",
            "EXPO_PUBLIC_IAP_PREMIUM_SKU_ANDROID",
            "EXPO_PUBLIC_IAP_ANDROID_PLUS_BASE_PLAN_ID",
            "EXPO_PUBLIC_IAP_ANDROID_PREMIUM_BASE_PLAN_ID",
            "EXPO_PUBLIC_ANDROID_PACKAGE_NAME",
        ],
        "recommended": [
            "EXPO_PUBLIC_IOS_BUNDLE_ID",
            "EXPO_PUBLIC_SUPPORT_URL",
        ],
        "notes": [
            "Legal/support links are runtime-managed via /subscription/bootstrap.",
            "Android uses a shared subscription product with base plans (for example emlis + plus/premium).",
            "Premium is now sold live. Keep premium identifiers aligned with backend/runtime aliases.",
        ],
    }

    detected_public = _detected_public_snapshot()
    comparison = _comparison_payload(public_snapshot if public_snapshot is not None else detected_public, backend=backend_resolved)
    runtime_bootstrap = await audit_subscription_bootstrap_runtime()
    warnings.extend(runtime_bootstrap.get("warnings") or [])

    ready = (
        len(backend_missing) == 0
        and not allow_unverified
        and comparison.get("ready", False)
        and runtime_bootstrap.get("ready", False)
    )

    return {
        "checked_at": datetime.now(timezone.utc).isoformat(),
        "environment": _first_env("MYMODEL_ENV", "ENVIRONMENT", "RENDER_ENV") or "unknown",
        "ready": ready,
        "backend": {
            "missing_required": backend_missing,
            "warnings": warnings,
            "resolved": backend_resolved,
        },
        "public_env_reference": public_env_reference,
        "public_env_detected_on_server": detected_public,
        "comparison": comparison,
        "runtime_bootstrap": runtime_bootstrap,
        "console_targets": {
            "apple": {
                "bundle_id": ios_bundle_id,
                "plus_product_ids": ios_plus_ids,
                "premium_product_ids": ios_premium_ids,
                "intro_offer_expectation": "Plus should exist as a paid subscription in the expected App Store Connect subscription group.",
                "server_notification_urls": backend_resolved["apple_notifications"],
            },
            "google": {
                "package_name": android_package_name,
                "shared_product_ids": sorted(set(android_plus_ids + android_premium_ids)),
                "plus_base_plan_ids": android_plus_base_plan_ids,
                "premium_base_plan_ids": android_premium_base_plan_ids,
                "offer_expectation": "Plus and Premium should be active base plans under the expected Google Play subscription product.",
                "rtdn_push_url": backend_resolved["google_notifications"]["push_url"],
            },
        },
    }


def register_subscription_release_config_routes(app: FastAPI) -> None:
    @app.get("/subscription/config/release-check")
    async def subscription_release_check(
        authorization: Optional[str] = Header(default=None, alias="Authorization"),
    ) -> Dict[str, Any]:
        _require_admin_bearer(authorization)
        return await build_subscription_release_report()

    @app.post("/subscription/config/release-check/compare-public")
    async def subscription_release_check_compare_public(
        body: PublicSubscriptionConfigRequest,
        authorization: Optional[str] = Header(default=None, alias="Authorization"),
    ) -> Dict[str, Any]:
        _require_admin_bearer(authorization)
        return await build_subscription_release_report(public_snapshot=body.model_dump(exclude_none=True))
