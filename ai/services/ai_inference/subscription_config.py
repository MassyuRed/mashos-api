# -*- coding: utf-8 -*-
from __future__ import annotations

import json
import os
from typing import Any, Dict, List, Optional

APPLE_WEBHOOK_PATH = "/subscription/webhooks/apple"
GOOGLE_WEBHOOK_PATH = "/subscription/webhooks/google"
LEGACY_FRONTEND_ENV_ALIASES = {
    "EXPO_PUBLIC_IAP_IOS_PLUS_PRODUCT_ID": [
        "EXPO_PUBLIC_IAP_IOS_PLUS_PRODUCT_IDS",
        "EXPO_PUBLIC_IAP_PLUS_SKU_IOS",
    ],
    "EXPO_PUBLIC_IAP_IOS_PREMIUM_PRODUCT_ID": [
        "EXPO_PUBLIC_IAP_IOS_PREMIUM_PRODUCT_IDS",
        "EXPO_PUBLIC_IAP_PREMIUM_SKU_IOS",
    ],
    "EXPO_PUBLIC_IAP_ANDROID_PLUS_PRODUCT_ID": [
        "EXPO_PUBLIC_IAP_ANDROID_PLUS_PRODUCT_IDS",
        "EXPO_PUBLIC_IAP_PLUS_SKU_ANDROID",
    ],
    "EXPO_PUBLIC_IAP_ANDROID_PREMIUM_PRODUCT_ID": [
        "EXPO_PUBLIC_IAP_ANDROID_PREMIUM_PRODUCT_IDS",
        "EXPO_PUBLIC_IAP_PREMIUM_SKU_ANDROID",
    ],
}

EXPECTED_FRONTEND_ENV_NAMES = [
    "EXPO_PUBLIC_IAP_IOS_PLUS_PRODUCT_ID",
    "EXPO_PUBLIC_IAP_IOS_PREMIUM_PRODUCT_ID",
    "EXPO_PUBLIC_IAP_ANDROID_PLUS_PRODUCT_ID",
    "EXPO_PUBLIC_IAP_ANDROID_PREMIUM_PRODUCT_ID",
    "EXPO_PUBLIC_ANDROID_PACKAGE_NAME",
    "EXPO_PUBLIC_IOS_BUNDLE_ID",
    "EXPO_PUBLIC_TERMS_URL",
    "EXPO_PUBLIC_PRIVACY_URL",
    "EXPO_PUBLIC_MYMODEL_API_URL",
]


def clean_optional_str(value: Any) -> Optional[str]:
    s = str(value or "").strip()
    return s or None


def _first_env(*names: str) -> str:
    for name in names:
        if not name:
            continue
        raw = os.getenv(name)
        if raw is None:
            continue
        txt = str(raw).strip()
        if txt:
            return txt
    return ""


def _split_csv(raw: Any) -> List[str]:
    text = str(raw or "")
    return [item.strip() for item in text.split(",") if item.strip()]


def _mask_tail(value: Optional[str], *, keep: int = 4) -> Optional[str]:
    s = clean_optional_str(value)
    if not s:
        return None
    if len(s) <= keep:
        return "*" * len(s)
    return ("*" * max(0, len(s) - keep)) + s[-keep:]


def _public_product_id(primary: str, *aliases: str) -> str:
    raw = _first_env(primary, *aliases)
    if not raw:
        return ""
    if "," in raw:
        parts = _split_csv(raw)
        return parts[0] if parts else ""
    return raw


def get_ios_plus_product_ids() -> List[str]:
    raw = _first_env(
        "COCOLON_IAP_IOS_PLUS_PRODUCT_IDS",
        "COCOLON_IAP_IOS_PLUS_PRODUCT_ID",
        "EXPO_PUBLIC_IAP_IOS_PLUS_PRODUCT_IDS",
        "EXPO_PUBLIC_IAP_IOS_PLUS_PRODUCT_ID",
        "EXPO_PUBLIC_IAP_PLUS_SKU_IOS",
    )
    return _split_csv(raw)


def get_ios_premium_product_ids() -> List[str]:
    raw = _first_env(
        "COCOLON_IAP_IOS_PREMIUM_PRODUCT_IDS",
        "COCOLON_IAP_IOS_PREMIUM_PRODUCT_ID",
        "EXPO_PUBLIC_IAP_IOS_PREMIUM_PRODUCT_IDS",
        "EXPO_PUBLIC_IAP_IOS_PREMIUM_PRODUCT_ID",
        "EXPO_PUBLIC_IAP_PREMIUM_SKU_IOS",
    )
    return _split_csv(raw)


def get_android_plus_product_ids() -> List[str]:
    raw = _first_env(
        "COCOLON_IAP_ANDROID_PLUS_PRODUCT_IDS",
        "COCOLON_IAP_ANDROID_PLUS_PRODUCT_ID",
        "EXPO_PUBLIC_IAP_ANDROID_PLUS_PRODUCT_IDS",
        "EXPO_PUBLIC_IAP_ANDROID_PLUS_PRODUCT_ID",
        "EXPO_PUBLIC_IAP_PLUS_SKU_ANDROID",
    )
    return _split_csv(raw)


def get_android_premium_product_ids() -> List[str]:
    raw = _first_env(
        "COCOLON_IAP_ANDROID_PREMIUM_PRODUCT_IDS",
        "COCOLON_IAP_ANDROID_PREMIUM_PRODUCT_ID",
        "EXPO_PUBLIC_IAP_ANDROID_PREMIUM_PRODUCT_IDS",
        "EXPO_PUBLIC_IAP_ANDROID_PREMIUM_PRODUCT_ID",
        "EXPO_PUBLIC_IAP_PREMIUM_SKU_ANDROID",
    )
    return _split_csv(raw)


def get_subscription_product_ids(platform: Optional[str], plan: Optional[str]) -> List[str]:
    plat = str(platform or "").strip().lower()
    normalized_plan = str(plan or "").strip().lower()
    if plat == "ios" and normalized_plan == "plus":
        return get_ios_plus_product_ids()
    if plat == "ios" and normalized_plan == "premium":
        return get_ios_premium_product_ids()
    if plat == "android" and normalized_plan == "plus":
        return get_android_plus_product_ids()
    if plat == "android" and normalized_plan == "premium":
        return get_android_premium_product_ids()
    return []


def get_apple_private_key_source() -> str:
    if clean_optional_str(os.getenv("COCOLON_IAP_APPLE_PRIVATE_KEY")):
        return "env_inline"
    if clean_optional_str(os.getenv("COCOLON_IAP_APPLE_PRIVATE_KEY_FILE")):
        return "env_file"
    return "missing"


def get_apple_private_key() -> str:
    raw = str(os.getenv("COCOLON_IAP_APPLE_PRIVATE_KEY", "")).replace("\\n", "\n").strip()
    if raw:
        return raw
    file_path = clean_optional_str(os.getenv("COCOLON_IAP_APPLE_PRIVATE_KEY_FILE"))
    if file_path:
        with open(file_path, "r", encoding="utf-8") as fh:
            return fh.read()
    raise RuntimeError("COCOLON_IAP_APPLE_PRIVATE_KEY is not configured")


def get_apple_issuer_id() -> str:
    issuer_id = clean_optional_str(os.getenv("COCOLON_IAP_APPLE_ISSUER_ID"))
    if not issuer_id:
        raise RuntimeError("COCOLON_IAP_APPLE_ISSUER_ID is not configured")
    return issuer_id


def get_apple_key_id() -> str:
    key_id = clean_optional_str(os.getenv("COCOLON_IAP_APPLE_KEY_ID"))
    if not key_id:
        raise RuntimeError("COCOLON_IAP_APPLE_KEY_ID is not configured")
    return key_id


def get_apple_bundle_id() -> str:
    bundle_id = _first_env(
        "COCOLON_IAP_APPLE_BUNDLE_ID",
        "APPLE_BUNDLE_ID",
        "EXPO_PUBLIC_IOS_BUNDLE_ID",
        "IOS_BUNDLE_IDENTIFIER",
    )
    if not bundle_id:
        raise RuntimeError("COCOLON_IAP_APPLE_BUNDLE_ID is not configured")
    return bundle_id


def get_apple_try_sandbox() -> bool:
    return str(os.getenv("COCOLON_IAP_APPLE_TRY_SANDBOX", "true")).strip().lower() in {"1", "true", "yes", "on"}


def is_ios_subscription_env_ready() -> bool:
    try:
        get_apple_private_key()
        get_apple_issuer_id()
        get_apple_key_id()
        get_apple_bundle_id()
        return True
    except Exception:
        return False


def get_google_service_account_source() -> str:
    if clean_optional_str(os.getenv("COCOLON_IAP_GOOGLE_SERVICE_ACCOUNT_JSON")) or clean_optional_str(os.getenv("GOOGLE_PLAY_SERVICE_ACCOUNT_JSON")):
        return "json_env"
    if clean_optional_str(os.getenv("COCOLON_IAP_GOOGLE_SERVICE_ACCOUNT_JSON_FILE")) or clean_optional_str(os.getenv("GOOGLE_PLAY_SERVICE_ACCOUNT_JSON_FILE")):
        return "json_file"
    if clean_optional_str(os.getenv("COCOLON_IAP_GOOGLE_CLIENT_EMAIL")) and clean_optional_str(os.getenv("COCOLON_IAP_GOOGLE_PRIVATE_KEY")):
        return "inline_parts"
    return "missing"


def get_google_service_account_info() -> Dict[str, Any]:
    raw_json = _first_env(
        "COCOLON_IAP_GOOGLE_SERVICE_ACCOUNT_JSON",
        "GOOGLE_PLAY_SERVICE_ACCOUNT_JSON",
    )
    if raw_json:
        return json.loads(raw_json)

    file_path = _first_env(
        "COCOLON_IAP_GOOGLE_SERVICE_ACCOUNT_JSON_FILE",
        "GOOGLE_PLAY_SERVICE_ACCOUNT_JSON_FILE",
    )
    if file_path:
        with open(file_path, "r", encoding="utf-8") as fh:
            return json.load(fh)

    client_email = clean_optional_str(os.getenv("COCOLON_IAP_GOOGLE_CLIENT_EMAIL"))
    private_key = str(os.getenv("COCOLON_IAP_GOOGLE_PRIVATE_KEY", "")).replace("\\n", "\n").strip()
    token_uri = _first_env("COCOLON_IAP_GOOGLE_TOKEN_URI") or "https://oauth2.googleapis.com/token"
    if client_email and private_key:
        return {
            "client_email": client_email,
            "private_key": private_key,
            "token_uri": token_uri,
        }

    raise RuntimeError("Google Play service account credentials are not configured.")


def get_google_client_email_preview() -> Optional[str]:
    try:
        info = get_google_service_account_info()
    except Exception:
        return None
    return _mask_tail(info.get("client_email"), keep=10)


def get_google_token_uri() -> str:
    try:
        info = get_google_service_account_info()
        return str(info.get("token_uri") or "https://oauth2.googleapis.com/token").strip()
    except Exception:
        return str(os.getenv("COCOLON_IAP_GOOGLE_TOKEN_URI", "https://oauth2.googleapis.com/token")).strip()


def get_android_package_name() -> str:
    package_name = _first_env(
        "COCOLON_IAP_ANDROID_PACKAGE_NAME",
        "GOOGLE_PLAY_PACKAGE_NAME",
        "ANDROID_PACKAGE_NAME",
        "EXPO_PUBLIC_ANDROID_PACKAGE_NAME",
    )
    if not package_name:
        raise RuntimeError("COCOLON_IAP_ANDROID_PACKAGE_NAME is not configured")
    return package_name


def is_android_subscription_env_ready() -> bool:
    try:
        get_android_package_name()
        get_google_service_account_info()
        return True
    except Exception:
        return False


def _frontend_public_snapshot() -> Dict[str, Optional[str]]:
    return {
        "EXPO_PUBLIC_IAP_IOS_PLUS_PRODUCT_ID": clean_optional_str(
            _public_product_id(
                "EXPO_PUBLIC_IAP_IOS_PLUS_PRODUCT_ID",
                "EXPO_PUBLIC_IAP_IOS_PLUS_PRODUCT_IDS",
                "EXPO_PUBLIC_IAP_PLUS_SKU_IOS",
            )
        ),
        "EXPO_PUBLIC_IAP_IOS_PREMIUM_PRODUCT_ID": clean_optional_str(
            _public_product_id(
                "EXPO_PUBLIC_IAP_IOS_PREMIUM_PRODUCT_ID",
                "EXPO_PUBLIC_IAP_IOS_PREMIUM_PRODUCT_IDS",
                "EXPO_PUBLIC_IAP_PREMIUM_SKU_IOS",
            )
        ),
        "EXPO_PUBLIC_IAP_ANDROID_PLUS_PRODUCT_ID": clean_optional_str(
            _public_product_id(
                "EXPO_PUBLIC_IAP_ANDROID_PLUS_PRODUCT_ID",
                "EXPO_PUBLIC_IAP_ANDROID_PLUS_PRODUCT_IDS",
                "EXPO_PUBLIC_IAP_PLUS_SKU_ANDROID",
            )
        ),
        "EXPO_PUBLIC_IAP_ANDROID_PREMIUM_PRODUCT_ID": clean_optional_str(
            _public_product_id(
                "EXPO_PUBLIC_IAP_ANDROID_PREMIUM_PRODUCT_ID",
                "EXPO_PUBLIC_IAP_ANDROID_PREMIUM_PRODUCT_IDS",
                "EXPO_PUBLIC_IAP_PREMIUM_SKU_ANDROID",
            )
        ),
        "EXPO_PUBLIC_ANDROID_PACKAGE_NAME": clean_optional_str(_first_env("EXPO_PUBLIC_ANDROID_PACKAGE_NAME")),
        "EXPO_PUBLIC_IOS_BUNDLE_ID": clean_optional_str(_first_env("EXPO_PUBLIC_IOS_BUNDLE_ID")),
        "EXPO_PUBLIC_TERMS_URL": clean_optional_str(_first_env("EXPO_PUBLIC_TERMS_URL")),
        "EXPO_PUBLIC_PRIVACY_URL": clean_optional_str(_first_env("EXPO_PUBLIC_PRIVACY_URL")),
        "EXPO_PUBLIC_MYMODEL_API_URL": clean_optional_str(_first_env("EXPO_PUBLIC_MYMODEL_API_URL")),
    }


def _build_warnings(snapshot: Dict[str, Any]) -> List[str]:
    warnings: List[str] = []
    ios = snapshot.get("ios") or {}
    android = snapshot.get("android") or {}
    frontend = snapshot.get("frontend_public") or {}

    if not ios.get("bundle_id"):
        warnings.append("Apple bundle ID が未設定です。App Store Server API 検証は動作しません。")
    if not ios.get("plus_product_ids"):
        warnings.append("iOS Plus product ID が未設定です。App Store Connect の商品IDと突合できません。")
    if not android.get("package_name"):
        warnings.append("Android package name が未設定です。Google Play 検証は動作しません。")
    if not android.get("plus_product_ids"):
        warnings.append("Android Plus product ID が未設定です。Google Play Console の subscription ID と突合できません。")
    if not frontend.get("EXPO_PUBLIC_TERMS_URL"):
        warnings.append("EXPO_PUBLIC_TERMS_URL が未設定です。申込画面の利用規約導線を確認してください。")
    if not frontend.get("EXPO_PUBLIC_PRIVACY_URL"):
        warnings.append("EXPO_PUBLIC_PRIVACY_URL が未設定です。申込画面のプライバシーポリシー導線を確認してください。")

    frontend_android_pkg = frontend.get("EXPO_PUBLIC_ANDROID_PACKAGE_NAME")
    backend_android_pkg = android.get("package_name")
    if frontend_android_pkg and backend_android_pkg and frontend_android_pkg != backend_android_pkg:
        warnings.append("Android package name が frontend と backend で不一致です。Google Play Console の package name と同一値に揃えてください。")

    frontend_ios_bundle = frontend.get("EXPO_PUBLIC_IOS_BUNDLE_ID")
    backend_ios_bundle = ios.get("bundle_id")
    if frontend_ios_bundle and backend_ios_bundle and frontend_ios_bundle != backend_ios_bundle:
        warnings.append("iOS bundle ID が frontend と backend で不一致です。App Store Connect の bundle ID と同一値に揃えてください。")

    for platform, plan, frontend_key in (
        ("ios", "plus", "EXPO_PUBLIC_IAP_IOS_PLUS_PRODUCT_ID"),
        ("ios", "premium", "EXPO_PUBLIC_IAP_IOS_PREMIUM_PRODUCT_ID"),
        ("android", "plus", "EXPO_PUBLIC_IAP_ANDROID_PLUS_PRODUCT_ID"),
        ("android", "premium", "EXPO_PUBLIC_IAP_ANDROID_PREMIUM_PRODUCT_ID"),
    ):
        frontend_value = frontend.get(frontend_key)
        product_ids = snapshot.get(platform, {}).get(f"{plan}_product_ids") or []
        if frontend_value and product_ids and frontend_value not in product_ids:
            warnings.append(f"{frontend_key} が backend の {platform}/{plan} product IDs に含まれていません。")

    if set(ios.get("plus_product_ids") or []) & set(ios.get("premium_product_ids") or []):
        warnings.append("iOS の Plus / Premium product IDs が重複しています。")
    if set(android.get("plus_product_ids") or []) & set(android.get("premium_product_ids") or []):
        warnings.append("Android の Plus / Premium product IDs が重複しています。")

    return warnings


def get_subscription_config_audit_snapshot() -> Dict[str, Any]:
    ios_plus = get_ios_plus_product_ids()
    ios_premium = get_ios_premium_product_ids()
    android_plus = get_android_plus_product_ids()
    android_premium = get_android_premium_product_ids()

    snapshot: Dict[str, Any] = {
        "ios": {
            "verification_ready": is_ios_subscription_env_ready(),
            "bundle_id": clean_optional_str(_first_env("COCOLON_IAP_APPLE_BUNDLE_ID", "APPLE_BUNDLE_ID", "EXPO_PUBLIC_IOS_BUNDLE_ID", "IOS_BUNDLE_IDENTIFIER")),
            "plus_product_ids": ios_plus,
            "premium_product_ids": ios_premium,
            "private_key_source": get_apple_private_key_source(),
            "issuer_id_configured": bool(clean_optional_str(os.getenv("COCOLON_IAP_APPLE_ISSUER_ID"))),
            "key_id_configured": bool(clean_optional_str(os.getenv("COCOLON_IAP_APPLE_KEY_ID"))),
            "try_sandbox": get_apple_try_sandbox(),
            "webhook_path": APPLE_WEBHOOK_PATH,
        },
        "android": {
            "verification_ready": is_android_subscription_env_ready(),
            "package_name": clean_optional_str(_first_env("COCOLON_IAP_ANDROID_PACKAGE_NAME", "GOOGLE_PLAY_PACKAGE_NAME", "ANDROID_PACKAGE_NAME", "EXPO_PUBLIC_ANDROID_PACKAGE_NAME")),
            "plus_product_ids": android_plus,
            "premium_product_ids": android_premium,
            "service_account_source": get_google_service_account_source(),
            "client_email_preview": get_google_client_email_preview(),
            "token_uri": get_google_token_uri(),
            "webhook_path": GOOGLE_WEBHOOK_PATH,
            "google_webhook_bearer_configured": bool(clean_optional_str(os.getenv("COCOLON_IAP_GOOGLE_WEBHOOK_BEARER"))),
        },
        "frontend_public": _frontend_public_snapshot(),
        "expected_frontend_env_names": list(EXPECTED_FRONTEND_ENV_NAMES),
        "console_mapping": {
            "apple": {
                "app_store_connect_bundle_id": clean_optional_str(_first_env("COCOLON_IAP_APPLE_BUNDLE_ID", "APPLE_BUNDLE_ID", "EXPO_PUBLIC_IOS_BUNDLE_ID", "IOS_BUNDLE_IDENTIFIER")),
                "subscription_product_ids": {"plus": ios_plus, "premium": ios_premium},
                "server_notification_relative_path": APPLE_WEBHOOK_PATH,
            },
            "google": {
                "play_console_package_name": clean_optional_str(_first_env("COCOLON_IAP_ANDROID_PACKAGE_NAME", "GOOGLE_PLAY_PACKAGE_NAME", "ANDROID_PACKAGE_NAME", "EXPO_PUBLIC_ANDROID_PACKAGE_NAME")),
                "subscription_ids": {"plus": android_plus, "premium": android_premium},
                "rtdn_relative_path": GOOGLE_WEBHOOK_PATH,
            },
        },
    }
    snapshot["warnings"] = _build_warnings(snapshot)
    return snapshot
