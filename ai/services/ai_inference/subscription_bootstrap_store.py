# -*- coding: utf-8 -*-
from __future__ import annotations

import json
import os
import re
from datetime import datetime, timezone
from typing import Any, Dict, Iterable, List, Mapping, Optional

from emlis_ai_capability import build_emlis_ai_public_plan_meta
from supabase_client import ensure_supabase_config, sb_get

SETTINGS_TABLE = (os.getenv("COCOLON_SUBSCRIPTION_RUNTIME_SETTINGS_TABLE") or "subscription_runtime_settings").strip() or "subscription_runtime_settings"
PLAN_TABLE = (os.getenv("COCOLON_SUBSCRIPTION_PLAN_CATALOG_TABLE") or "subscription_plan_catalog").strip() or "subscription_plan_catalog"
ALIASES_TABLE = (os.getenv("COCOLON_SUBSCRIPTION_PRODUCT_ALIASES_TABLE") or "subscription_product_aliases").strip() or "subscription_product_aliases"
IOS_MANAGE_SUBSCRIPTIONS_URL = "https://apps.apple.com/account/subscriptions"
_VERSION_SPLIT_RE = re.compile(r"[^0-9A-Za-z]+")
PLUS_CANONICAL_SUBTITLE = "レポート閲覧 / Piece作成拡張"
PREMIUM_CANONICAL_SUBTITLE = "表示期間無制限 / 深いレポート / Piece作成無制限"
PREMIUM_CANONICAL_FEATURES = [
    "履歴全般：表示期間無制限",
    "Analysis：感情構造分析レポートがさらに深くなります",
    "Analysis：自己構造分析レポートがさらに深くなります",
    "Piece：今月の作成回数が無制限です",
]


PLUS_EMLIS_AI_MARKETING_LINES = [
    "EmlisAI：最近の流れを見ながら返してくれます",
    "EmlisAI：入力履歴を踏まえた返答になります",
]
PREMIUM_EMLIS_AI_MARKETING_LINES = [
    "EmlisAI：あなたの流れに合わせて返し方まで変わります",
    "EmlisAI：長い時間の変化や回復も踏まえて寄り添います",
]


def _append_unique_strings(values: Any, additions: Iterable[str]) -> List[str]:
    out = _string_list(values, [])
    seen = {item for item in out}
    for item in additions:
        value = _string_or_none(item)
        if not value or value in seen:
            continue
        out.append(value)
        seen.add(value)
    return out


def _emlis_ai_marketing_lines_for_plan(plan_code: str) -> List[str]:
    normalized = _clean(plan_code).lower()
    if normalized == "premium":
        return list(PREMIUM_EMLIS_AI_MARKETING_LINES)
    if normalized == "plus":
        return list(PLUS_EMLIS_AI_MARKETING_LINES)
    return []


def _attach_emlis_ai_plan_meta(plan_code: str, plan: Mapping[str, Any]) -> Dict[str, Any]:
    normalized = _clean(plan_code).lower()
    out = dict(plan)
    if normalized not in {"plus", "premium"}:
        return out
    marketing_lines = _emlis_ai_marketing_lines_for_plan(normalized)
    out["features"] = _append_unique_strings(out.get("features"), marketing_lines)
    out["emlis_ai"] = {
        **build_emlis_ai_public_plan_meta(normalized),
        "marketing_lines": marketing_lines,
    }
    return out


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
    for name in names:
        raw = _clean(os.getenv(name, ""))
        if raw:
            return _split_csv(raw)
    return []


def _android_shared_product_ids() -> list[str]:
    ids = _csv_env("COCOLON_IAP_ANDROID_PLUS_PRODUCT_IDS")
    if ids:
        return ids
    ids = _csv_env("COCOLON_IAP_ANDROID_PREMIUM_PRODUCT_IDS")
    if ids:
        return ids
    fallback = _string_or_none(
        _first_env("EXPO_PUBLIC_IAP_PLUS_SKU_ANDROID", "EXPO_PUBLIC_IAP_PREMIUM_SKU_ANDROID")
    )
    return [fallback] if fallback else []


def _android_base_plan_ids(plan_code: str) -> list[str]:
    if plan_code == "premium":
        values = _csv_env("COCOLON_IAP_ANDROID_PREMIUM_BASE_PLAN_IDS")
        fallback = _string_or_none(_first_env("EXPO_PUBLIC_IAP_ANDROID_PREMIUM_BASE_PLAN_ID")) or "premium"
    else:
        values = _csv_env("COCOLON_IAP_ANDROID_PLUS_BASE_PLAN_IDS")
        fallback = _string_or_none(_first_env("EXPO_PUBLIC_IAP_ANDROID_PLUS_BASE_PLAN_ID")) or "plus"
    return _string_list(values or ([fallback] if fallback else []), [])


def _primary_android_base_plan_id(plan_code: str) -> Optional[str]:
    values = _android_base_plan_ids(plan_code)
    return values[0] if values else None


def _android_plan_code_from_base_plan_id(base_plan_id: Optional[str]) -> Optional[str]:
    raw = _string_or_none(base_plan_id)
    if not raw:
        return None
    low = raw.lower()
    if "premium" in low:
        return "premium"
    if "plus" in low or "trial" in low:
        return "plus"
    if raw in set(_android_base_plan_ids("premium")):
        return "premium"
    if raw in set(_android_base_plan_ids("plus")):
        return "plus"
    return None


def _bool(value: Any, default: bool = False) -> bool:
    if value is None:
        return default
    if isinstance(value, bool):
        return value
    s = _clean(value).lower()
    if s in {"1", "true", "yes", "on"}:
        return True
    if s in {"0", "false", "no", "off"}:
        return False
    return default


def _jsonish(value: Any, default: Any):
    if value is None:
        return default
    if isinstance(value, (dict, list)):
        return value
    s = _clean(value)
    if not s:
        return default
    try:
        return json.loads(s)
    except Exception:
        return default


def _string_list(value: Any, default: Optional[list[str]] = None) -> list[str]:
    raw = value if isinstance(value, list) else _jsonish(value, default or [])
    if isinstance(raw, str):
        raw = [raw]
    if not isinstance(raw, list):
        raw = default or []
    out: list[str] = []
    seen = set()
    for item in raw:
        s = _clean(item)
        if not s or s in seen:
            continue
        out.append(s)
        seen.add(s)
    return out


def _string_or_none(value: Any) -> Optional[str]:
    s = _clean(value)
    return s or None


def _replace_legacy_subscription_text(value: Any) -> Optional[str]:
    s = _string_or_none(value)
    if not s:
        return None
    return (
        s.replace("無料会員", "Freeプラン")
        .replace("Plus会員", "Plusプラン")
        .replace("Premium会員", "Premiumプラン")
        .replace("MyModelCreate", "ProfileCreate")
        .replace("ReflectionCreate", "ProfileCreate")
        .replace("Reflections", "Piece")
        .replace("Reflection", "Piece")
        .replace("MyModel", "Piece画面")
        .replace("MyWeb", "Analysis")
    )


def _normalize_platform(value: Any) -> str:
    return "ios" if _clean(value).lower() == "ios" else "android"


def _extract_version_parts(value: Any) -> List[int]:
    raw = _clean(value)
    if not raw:
        return []
    out: List[int] = []
    for piece in _VERSION_SPLIT_RE.split(raw):
        if not piece:
            continue
        if piece.isdigit():
            out.append(int(piece))
            continue
        digit_prefix = ""
        for ch in piece:
            if ch.isdigit():
                digit_prefix += ch
            else:
                break
        if digit_prefix:
            out.append(int(digit_prefix))
    return out


def _compare_versions(left: Any, right: Any) -> int:
    left_parts = _extract_version_parts(left)
    right_parts = _extract_version_parts(right)
    if not left_parts or not right_parts:
        return 0
    length = max(len(left_parts), len(right_parts))
    for idx in range(length):
        l_val = left_parts[idx] if idx < len(left_parts) else 0
        r_val = right_parts[idx] if idx < len(right_parts) else 0
        if l_val < r_val:
            return -1
        if l_val > r_val:
            return 1
    return 0


def _client_allowed(client_version: Optional[str], min_version: Optional[str]) -> bool:
    cur = _clean(client_version)
    min_v = _clean(min_version)
    if not cur or not min_v:
        return True
    return _compare_versions(cur, min_v) >= 0


def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


def _parse_iso(value: Any) -> Optional[datetime]:
    raw = _clean(value)
    if not raw:
        return None
    try:
        dt = datetime.fromisoformat(raw.replace("Z", "+00:00"))
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt.astimezone(timezone.utc)
    except Exception:
        return None


def _alias_active(row: Mapping[str, Any], *, now_utc: datetime) -> bool:
    status = _clean(row.get("status") or "active").lower()
    if status and status != "active":
        return False
    start_dt = _parse_iso(row.get("effective_from"))
    end_dt = _parse_iso(row.get("effective_to"))
    if start_dt and start_dt > now_utc:
        return False
    if end_dt and end_dt <= now_utc:
        return False
    return True


async def _fetch_rows(table: str, *, params: Dict[str, str]) -> list[Dict[str, Any]]:
    try:
        ensure_supabase_config()
    except Exception:
        return []
    try:
        resp = await sb_get(f"/rest/v1/{table}", params=params, timeout=6.0)
    except Exception:
        return []
    if resp.status_code >= 300:
        return []
    try:
        data = resp.json()
    except Exception:
        return []
    if isinstance(data, list):
        return [row for row in data if isinstance(row, dict)]
    if isinstance(data, dict):
        return [data]
    return []


async def _fetch_runtime_settings() -> Optional[Dict[str, Any]]:
    rows = await _fetch_rows(
        SETTINGS_TABLE,
        params={"select": "*", "order": "updated_at.desc", "limit": "1"},
    )
    return rows[0] if rows else None


async def _fetch_plan_catalog_rows() -> list[Dict[str, Any]]:
    return await _fetch_rows(
        PLAN_TABLE,
        params={"select": "*", "order": "display_order.asc,updated_at.desc"},
    )


async def _fetch_alias_rows() -> list[Dict[str, Any]]:
    return await _fetch_rows(
        ALIASES_TABLE,
        params={"select": "*", "order": "updated_at.desc"},
    )


def _default_links() -> Dict[str, Optional[str]]:
    return {
        "terms_url": _string_or_none(_first_env("COCOLON_SUBSCRIPTION_TERMS_URL", "EXPO_PUBLIC_TERMS_URL")),
        "privacy_url": _string_or_none(_first_env("COCOLON_SUBSCRIPTION_PRIVACY_URL", "EXPO_PUBLIC_PRIVACY_URL")),
        "support_url": _string_or_none(_first_env("COCOLON_SUBSCRIPTION_SUPPORT_URL", "EXPO_PUBLIC_SUPPORT_URL")),
    }


def _default_policy() -> Dict[str, Any]:
    return {
        "restore_enabled": True,
        "manage_enabled": True,
        "ios_manage_url": _string_or_none(_first_env("COCOLON_SUBSCRIPTION_IOS_MANAGE_URL")) or IOS_MANAGE_SUBSCRIPTIONS_URL,
        "android_manage_mode": _string_or_none(_first_env("COCOLON_SUBSCRIPTION_ANDROID_MANAGE_MODE")) or "specific_subscription",
        "android_package_name": _string_or_none(_first_env("COCOLON_IAP_ANDROID_PACKAGE_NAME", "EXPO_PUBLIC_ANDROID_PACKAGE_NAME")),
        "review_notice": _string_or_none(_first_env("COCOLON_SUBSCRIPTION_REVIEW_NOTICE")),
    }


def _default_runtime_settings() -> Dict[str, Any]:
    return {
        "sales_enabled": _bool(os.getenv("COCOLON_SUBSCRIPTION_SALES_ENABLED"), default=True),
        "ios_sales_enabled": _bool(os.getenv("COCOLON_SUBSCRIPTION_IOS_SALES_ENABLED"), default=True),
        "android_sales_enabled": _bool(os.getenv("COCOLON_SUBSCRIPTION_ANDROID_SALES_ENABLED"), default=True),
        "ios_min_app_version": _string_or_none(os.getenv("COCOLON_SUBSCRIPTION_IOS_MIN_APP_VERSION")),
        "android_min_app_version": _string_or_none(os.getenv("COCOLON_SUBSCRIPTION_ANDROID_MIN_APP_VERSION")),
        **_default_links(),
        **_default_policy(),
    }


def _default_plan_catalog() -> Dict[str, Dict[str, Any]]:
    plus_ios = _csv_env("COCOLON_IAP_IOS_PLUS_PRODUCT_IDS")
    premium_ios = _csv_env("COCOLON_IAP_IOS_PREMIUM_PRODUCT_IDS")
    android_shared = _android_shared_product_ids()

    plus_ios_fallback = _string_or_none(_first_env("EXPO_PUBLIC_IAP_PLUS_SKU_IOS"))
    premium_ios_fallback = _string_or_none(_first_env("EXPO_PUBLIC_IAP_PREMIUM_SKU_IOS"))
    android_shared_fallback = _string_or_none(
        _first_env("EXPO_PUBLIC_IAP_PLUS_SKU_ANDROID", "EXPO_PUBLIC_IAP_PREMIUM_SKU_ANDROID")
    )

    android_purchase_product_id = (
        android_shared[0] if android_shared else android_shared_fallback
    )
    android_recognized_product_ids = (
        android_shared or ([android_shared_fallback] if android_shared_fallback else [])
    )
    plus_android_base_plan_ids = _android_base_plan_ids("plus")
    premium_android_base_plan_ids = _android_base_plan_ids("premium")

    return {
        "plus": {
            "visible": True,
            "purchasable": True,
            "launch_stage": "live",
            "title": "Plusプラン",
            "price_label": "月額300円",
            "subtitle": "レポート閲覧 / Piece作成拡張",
            "features": [
                "履歴全般：表示期間１年",
                "Analysis：感情構造分析レポートが深くなります",
                "Analysis：自己構造分析レポートを閲覧できます",
                "Analysis：今日の問いを履歴から編集できます",
                "Piece：今月30回まで作成できます",
                "ProfileCreate：回答を保存したあとでも編集できます",
            ],
            "note_lines": [
                "月額300円で自動更新されます。",
                "解約はいつでも行えます。",
            ],
            "cta_label": "このプランを選ぶ",
            "recommended": True,
            "purchase_product_id": {
                "ios": plus_ios[0] if plus_ios else plus_ios_fallback,
                "android": android_purchase_product_id,
            },
            "recognized_product_ids": {
                "ios": plus_ios or ([plus_ios_fallback] if plus_ios_fallback else []),
                "android": android_recognized_product_ids,
            },
            "purchase_base_plan_id": {
                "ios": None,
                "android": _primary_android_base_plan_id("plus"),
            },
            "recognized_base_plan_ids": {
                "ios": [],
                "android": plus_android_base_plan_ids,
            },
        },
        "premium": {
            "visible": True,
            "purchasable": True,
            "launch_stage": "live",
            "title": "Premiumプラン",
            "price_label": "月額980円",
            "subtitle": "表示期間無制限 / 深いレポート / Piece作成無制限",
            "features": [
                "履歴全般：表示期間無制限",
                "Analysis：感情構造分析レポートがさらに深くなります",
                "Analysis：自己構造分析レポートがさらに深くなります",
                "Piece：今月の作成回数が無制限です",
            ],
            "note_lines": [
                "月額980円で自動更新されます。",
                "解約はいつでもストアのサブスクリプション管理から行えます。",
            ],
            "cta_label": "このプランを選ぶ",
            "recommended": False,
            "purchase_product_id": {
                "ios": premium_ios[0] if premium_ios else premium_ios_fallback,
                "android": android_purchase_product_id,
            },
            "recognized_product_ids": {
                "ios": premium_ios or ([premium_ios_fallback] if premium_ios_fallback else []),
                "android": android_recognized_product_ids,
            },
            "purchase_base_plan_id": {
                "ios": None,
                "android": _primary_android_base_plan_id("premium"),
            },
            "recognized_base_plan_ids": {
                "ios": [],
                "android": premium_android_base_plan_ids,
            },
        },
    }


def _normalize_plan_catalog_item(plan_code: str, plan: Optional[Mapping[str, Any]]) -> Dict[str, Any]:
    src = dict(plan or {})
    out = dict(src)

    if plan_code == "plus":
        out["title"] = _replace_legacy_subscription_text(src.get("title")) or "Plusプラン"
        out["subtitle"] = (
            _replace_legacy_subscription_text(src.get("subtitle")) or PLUS_CANONICAL_SUBTITLE
        )
        out["features"] = []
        for item in _string_list(src.get("features"), src.get("features") or []):
            text = _replace_legacy_subscription_text(item) or _clean(item)
            if text:
                out["features"].append(text)
    elif plan_code == "premium":
        out["title"] = "Premiumプラン"
        out["subtitle"] = PREMIUM_CANONICAL_SUBTITLE
        out["features"] = list(PREMIUM_CANONICAL_FEATURES)

    out["note_lines"] = []
    for item in _string_list(src.get("note_lines"), src.get("note_lines") or []):
        text = _replace_legacy_subscription_text(item) or _clean(item)
        if text:
            out["note_lines"].append(text)
    out["cta_label"] = _replace_legacy_subscription_text(src.get("cta_label")) or _string_or_none(
        src.get("cta_label")
    )
    return out


def _merge_settings(row: Optional[Mapping[str, Any]]) -> Dict[str, Any]:
    base = _default_runtime_settings()
    if not row:
        return base
    merged = dict(base)
    for key in (
        "sales_enabled",
        "ios_sales_enabled",
        "android_sales_enabled",
        "restore_enabled",
        "manage_enabled",
    ):
        merged[key] = _bool(row.get(key), default=base[key])
    for key in (
        "ios_min_app_version",
        "android_min_app_version",
        "terms_url",
        "privacy_url",
        "support_url",
        "ios_manage_url",
        "android_manage_mode",
        "android_package_name",
        "review_notice",
    ):
        merged[key] = _string_or_none(row.get(key)) or base.get(key)
    return merged


def _merge_plan_catalog(rows: Iterable[Mapping[str, Any]]) -> Dict[str, Dict[str, Any]]:
    catalog = _default_plan_catalog()
    resolved_plan_codes: set[str] = set()
    for row in rows or []:
        plan_code = _clean(row.get("plan_code")).lower()
        if plan_code not in catalog or plan_code in resolved_plan_codes:
            continue
        target = dict(catalog[plan_code])
        target["visible"] = _bool(row.get("visible"), default=target.get("visible", True))
        target["purchasable"] = _bool(row.get("purchasable"), default=target.get("purchasable", False))
        target["launch_stage"] = _string_or_none(row.get("launch_stage")) or target.get("launch_stage")
        target["title"] = _string_or_none(row.get("title")) or target.get("title")
        target["price_label"] = _string_or_none(row.get("price_label")) or target.get("price_label")
        target["subtitle"] = _string_or_none(row.get("subtitle")) or target.get("subtitle")
        target["features"] = _string_list(row.get("features_json"), target.get("features") or [])
        target["note_lines"] = _string_list(row.get("note_lines_json"), target.get("note_lines") or [])
        target["cta_label"] = _string_or_none(row.get("cta_label")) or target.get("cta_label")
        target["recommended"] = _bool(row.get("recommended"), default=target.get("recommended", False))
        catalog[plan_code] = _normalize_plan_catalog_item(plan_code, target)
        resolved_plan_codes.add(plan_code)
    return {code: _normalize_plan_catalog_item(code, plan) for code, plan in catalog.items()}


def _apply_alias_rows(catalog: Dict[str, Dict[str, Any]], rows: Iterable[Mapping[str, Any]]) -> Dict[str, Dict[str, Any]]:
    now_utc = _now_utc()
    merged = {key: dict(value) for key, value in (catalog or {}).items()}
    purchase_default_resolved: set[tuple[str, str]] = set()

    android_shared_product = _string_or_none(
        ((merged.get("plus") or {}).get("purchase_product_id") or {}).get("android")
    ) or _string_or_none(
        ((merged.get("premium") or {}).get("purchase_product_id") or {}).get("android")
    )
    android_shared_mode = bool(
        android_shared_product
        and _string_or_none(((merged.get("plus") or {}).get("purchase_base_plan_id") or {}).get("android"))
        and _string_or_none(((merged.get("premium") or {}).get("purchase_base_plan_id") or {}).get("android"))
    )

    for plan_code, plan in merged.items():
        plan["purchase_product_id"] = dict(plan.get("purchase_product_id") or {})
        plan["recognized_product_ids"] = {
            "ios": list((plan.get("recognized_product_ids") or {}).get("ios") or []),
            "android": list((plan.get("recognized_product_ids") or {}).get("android") or []),
        }
        plan["purchase_base_plan_id"] = dict(plan.get("purchase_base_plan_id") or {})
        plan["recognized_base_plan_ids"] = {
            "ios": list((plan.get("recognized_base_plan_ids") or {}).get("ios") or []),
            "android": list((plan.get("recognized_base_plan_ids") or {}).get("android") or []),
        }

        if android_shared_mode:
            plan["purchase_product_id"]["android"] = android_shared_product
            plan["recognized_product_ids"]["android"] = [android_shared_product]

    for row in rows or []:
        plan_code = _clean(row.get("plan_code")).lower()
        if plan_code not in merged or not _alias_active(row, now_utc=now_utc):
            continue
        platform = _normalize_platform(row.get("platform"))
        product_id = _string_or_none(row.get("store_product_id"))
        if not product_id:
            continue

        if platform == "android" and android_shared_mode:
            if product_id != android_shared_product:
                continue
            recognized = merged[plan_code]["recognized_product_ids"].setdefault("android", [])
            if product_id not in recognized:
                recognized.append(product_id)
            merged[plan_code]["purchase_product_id"]["android"] = android_shared_product
            continue

        recognized = merged[plan_code]["recognized_product_ids"].setdefault(platform, [])
        if product_id not in recognized:
            recognized.append(product_id)
        if _bool(row.get("is_purchase_default"), default=False):
            default_key = (plan_code, platform)
            if default_key not in purchase_default_resolved:
                merged[plan_code]["purchase_product_id"][platform] = product_id
                purchase_default_resolved.add(default_key)

    return merged


def _plan_public(plan: Mapping[str, Any]) -> Dict[str, Any]:
    purchase_map = plan.get("purchase_product_id") or {}
    recognized = plan.get("recognized_product_ids") or {}
    purchase_base_plan_map = plan.get("purchase_base_plan_id") or {}
    recognized_base_plan_map = plan.get("recognized_base_plan_ids") or {}
    return {
        "visible": _bool(plan.get("visible"), default=True),
        "purchasable": _bool(plan.get("purchasable"), default=False),
        "launch_stage": _string_or_none(plan.get("launch_stage")) or "hidden",
        "title": _string_or_none(plan.get("title")) or "",
        "price_label": _string_or_none(plan.get("price_label")),
        "subtitle": _string_or_none(plan.get("subtitle")),
        "features": _string_list(plan.get("features"), []),
        "note_lines": _string_list(plan.get("note_lines"), []),
        "cta_label": _string_or_none(plan.get("cta_label")),
        "recommended": _bool(plan.get("recommended"), default=False),
        "purchase_product_id": {
            "ios": _string_or_none((purchase_map or {}).get("ios")),
            "android": _string_or_none((purchase_map or {}).get("android")),
        },
        "recognized_product_ids": {
            "ios": _string_list((recognized or {}).get("ios"), []),
            "android": _string_list((recognized or {}).get("android"), []),
        },
        "purchase_base_plan_id": {
            "ios": _string_or_none((purchase_base_plan_map or {}).get("ios")),
            "android": _string_or_none((purchase_base_plan_map or {}).get("android")),
        },
        "recognized_base_plan_ids": {
            "ios": _string_list((recognized_base_plan_map or {}).get("ios"), []),
            "android": _string_list((recognized_base_plan_map or {}).get("android"), []),
        },
    }


async def build_subscription_bootstrap(*, client_meta: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    settings_row = await _fetch_runtime_settings()
    plan_rows = await _fetch_plan_catalog_rows()
    alias_rows = await _fetch_alias_rows()

    settings = _merge_settings(settings_row)
    catalog = _apply_alias_rows(_merge_plan_catalog(plan_rows), alias_rows)

    platform = _normalize_platform((client_meta or {}).get("platform"))
    app_version = _string_or_none((client_meta or {}).get("app_version"))

    sales_enabled = _bool(settings.get("sales_enabled"), default=True)
    platform_sales_enabled = _bool(settings.get(f"{platform}_sales_enabled"), default=True)
    min_version = _string_or_none(settings.get(f"{platform}_min_app_version"))
    version_allowed = _client_allowed(app_version, min_version)

    client_sales_enabled = sales_enabled and platform_sales_enabled and version_allowed
    disabled_reason = None
    if not sales_enabled:
        disabled_reason = "現在はサブスクリプション販売を停止しています。"
    elif not platform_sales_enabled:
        disabled_reason = "この端末では現在サブスクリプション販売を停止しています。"
    elif not version_allowed:
        disabled_reason = "このバージョンではサブスクリプション購入をご利用いただけません。最新バージョンをご利用ください。"

    public_catalog: Dict[str, Dict[str, Any]] = {}
    for plan_code, plan in catalog.items():
        item = _plan_public(plan)
        if not client_sales_enabled:
            item["purchasable"] = False
        item = _attach_emlis_ai_plan_meta(plan_code, item)
        public_catalog[plan_code] = item

    return {
        "sales_enabled": sales_enabled,
        "client_sales_enabled": client_sales_enabled,
        "client_sales_disabled_reason": disabled_reason,
        "links": {
            "terms_url": _string_or_none(settings.get("terms_url")),
            "privacy_url": _string_or_none(settings.get("privacy_url")),
            "support_url": _string_or_none(settings.get("support_url")),
        },
        "policy": {
            "restore_enabled": _bool(settings.get("restore_enabled"), default=True),
            "manage_enabled": _bool(settings.get("manage_enabled"), default=True),
            "ios_manage_url": _string_or_none(settings.get("ios_manage_url")) or IOS_MANAGE_SUBSCRIPTIONS_URL,
            "android_manage_mode": _string_or_none(settings.get("android_manage_mode")) or "specific_subscription",
            "android_package_name": _string_or_none(settings.get("android_package_name")),
            "review_notice": _string_or_none(settings.get("review_notice")),
        },
        "plans": public_catalog,
    }


def _env_plan_code_from_product_id(store: Optional[str], product_id: Optional[str]) -> Optional[str]:
    pid = _string_or_none(product_id)
    if not pid:
        return None
    low = pid.lower()
    if "premium" in low:
        return "premium"
    if "plus" in low:
        return "plus"
    platform = _normalize_platform(store)
    if platform == "ios":
        plus_ids = set(_csv_env("COCOLON_IAP_IOS_PLUS_PRODUCT_IDS"))
        premium_ids = set(_csv_env("COCOLON_IAP_IOS_PREMIUM_PRODUCT_IDS"))
    else:
        plus_ids = set(_android_shared_product_ids() or _csv_env("COCOLON_IAP_ANDROID_PLUS_PRODUCT_IDS"))
        premium_ids = set(_android_shared_product_ids() or _csv_env("COCOLON_IAP_ANDROID_PREMIUM_PRODUCT_IDS"))
    plus_match = pid in plus_ids
    premium_match = pid in premium_ids
    if premium_match and not plus_match:
        return "premium"
    if plus_match and not premium_match:
        return "plus"
    return None


async def resolve_plan_code_by_product_id(store: Optional[str], product_id: Optional[str]) -> Optional[str]:
    pid = _string_or_none(product_id)
    platform = _normalize_platform(store)
    if not pid:
        return None
    rows = await _fetch_rows(
        ALIASES_TABLE,
        params={
            "select": "plan_code,platform,status,effective_from,effective_to,store_product_id",
            "platform": f"eq.{platform}",
            "store_product_id": f"eq.{pid}",
            "limit": "10",
        },
    )
    now_utc = _now_utc()
    matched_plan_codes: set[str] = set()
    for row in rows:
        if _alias_active(row, now_utc=now_utc):
            plan_code = _clean(row.get("plan_code")).lower()
            if plan_code in {"plus", "premium"}:
                matched_plan_codes.add(plan_code)
    if len(matched_plan_codes) == 1:
        return next(iter(matched_plan_codes))
    return _env_plan_code_from_product_id(platform, pid)


async def resolve_plan_code_for_purchase(
    store: Optional[str],
    product_id: Optional[str],
    base_plan_id: Optional[str] = None,
) -> Optional[str]:
    platform = _normalize_platform(store)
    if platform == "android":
        by_base_plan = _android_plan_code_from_base_plan_id(base_plan_id)
        if by_base_plan:
            return by_base_plan
    return await resolve_plan_code_by_product_id(platform, product_id)


async def audit_subscription_bootstrap_runtime() -> Dict[str, Any]:
    settings_row = await _fetch_runtime_settings()
    plan_rows = await _fetch_plan_catalog_rows()
    alias_rows = await _fetch_alias_rows()
    settings = _merge_settings(settings_row)
    catalog = _apply_alias_rows(_merge_plan_catalog(plan_rows), alias_rows)

    missing_required: list[str] = []
    warnings: list[str] = []

    if not _string_or_none(settings.get("terms_url")):
        missing_required.append(f"{SETTINGS_TABLE}.terms_url")
    if not _string_or_none(settings.get("privacy_url")):
        missing_required.append(f"{SETTINGS_TABLE}.privacy_url")
    if not _string_or_none(settings.get("support_url")):
        missing_required.append(f"{SETTINGS_TABLE}.support_url")

    plus = catalog.get("plus") or {}
    premium = catalog.get("premium") or {}

    if not _bool(plus.get("visible"), default=False):
        missing_required.append(f"{PLAN_TABLE}[plus].visible")
    if not _bool(plus.get("purchasable"), default=False):
        missing_required.append(f"{PLAN_TABLE}[plus].purchasable")
    if not _bool(premium.get("visible"), default=True):
        warnings.append("Premium plan is hidden. This is acceptable only if you want no coming-soon surface.")

    plus_ios_purchase = _string_or_none((plus.get("purchase_product_id") or {}).get("ios"))
    plus_android_purchase = _string_or_none((plus.get("purchase_product_id") or {}).get("android"))
    premium_ios_purchase = _string_or_none((premium.get("purchase_product_id") or {}).get("ios"))
    premium_android_purchase = _string_or_none((premium.get("purchase_product_id") or {}).get("android"))
    plus_android_base_plan = _string_or_none((plus.get("purchase_base_plan_id") or {}).get("android"))
    premium_android_base_plan = _string_or_none((premium.get("purchase_base_plan_id") or {}).get("android"))
    plus_android_recognized_base_plans = _string_list((plus.get("recognized_base_plan_ids") or {}).get("android"), [])
    premium_android_recognized_base_plans = _string_list((premium.get("recognized_base_plan_ids") or {}).get("android"), [])

    if not plus_ios_purchase:
        missing_required.append(f"{ALIASES_TABLE}[plus/ios].is_purchase_default")
    if not plus_android_purchase:
        missing_required.append(f"{ALIASES_TABLE}[plus/android].is_purchase_default")

    if len(_string_list((plus.get("recognized_product_ids") or {}).get("ios"), [])) == 0:
        missing_required.append(f"{ALIASES_TABLE}[plus/ios].store_product_id")
    if len(_string_list((plus.get("recognized_product_ids") or {}).get("android"), [])) == 0:
        missing_required.append(f"{ALIASES_TABLE}[plus/android].store_product_id")

    if not plus_android_base_plan:
        missing_required.append("android.plus.purchase_base_plan_id")
    if len(plus_android_recognized_base_plans) == 0:
        missing_required.append("android.plus.recognized_base_plan_ids")

    premium_purchasable = _bool(premium.get("purchasable"), default=False)
    if premium_purchasable:
        if not premium_ios_purchase:
            missing_required.append(f"{ALIASES_TABLE}[premium/ios].is_purchase_default")
        if not premium_android_purchase:
            missing_required.append(f"{ALIASES_TABLE}[premium/android].is_purchase_default")
        if len(_string_list((premium.get("recognized_product_ids") or {}).get("ios"), [])) == 0:
            missing_required.append(f"{ALIASES_TABLE}[premium/ios].store_product_id")
        if len(_string_list((premium.get("recognized_product_ids") or {}).get("android"), [])) == 0:
            missing_required.append(f"{ALIASES_TABLE}[premium/android].store_product_id")
        if not premium_android_base_plan:
            missing_required.append("android.premium.purchase_base_plan_id")
        if len(premium_android_recognized_base_plans) == 0:
            missing_required.append("android.premium.recognized_base_plan_ids")

    if plus_android_purchase and premium_android_purchase and plus_android_purchase == premium_android_purchase:
        warnings.append(
            "Android plus/premium share the same subscription product id. This is expected when Google Play uses one subscription with multiple base plans."
        )

    ready = len(missing_required) == 0
    return {
        "settings_table": SETTINGS_TABLE,
        "plan_table": PLAN_TABLE,
        "aliases_table": ALIASES_TABLE,
        "settings_row_present": bool(settings_row),
        "plan_rows_present": bool(plan_rows),
        "alias_rows_present": bool(alias_rows),
        "missing_required": missing_required,
        "warnings": warnings,
        "resolved": {
            "sales_enabled": _bool(settings.get("sales_enabled"), default=True),
            "terms_url": _string_or_none(settings.get("terms_url")),
            "privacy_url": _string_or_none(settings.get("privacy_url")),
            "support_url": _string_or_none(settings.get("support_url")),
            "plus_ios_purchase": plus_ios_purchase,
            "plus_android_purchase": plus_android_purchase,
            "plus_android_base_plan": plus_android_base_plan,
            "plus_android_recognized_base_plans": plus_android_recognized_base_plans,
            "premium_ios_purchase": premium_ios_purchase,
            "premium_android_purchase": premium_android_purchase,
            "premium_android_base_plan": premium_android_base_plan,
            "premium_android_recognized_base_plans": premium_android_recognized_base_plans,
            "premium_launch_stage": _string_or_none(premium.get("launch_stage")) or "coming_soon",
            "premium_purchasable": premium_purchasable,
        },
        "ready": ready,
    }

