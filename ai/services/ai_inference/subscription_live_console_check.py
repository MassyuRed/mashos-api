# -*- coding: utf-8 -*-
from __future__ import annotations

import logging
import os
import time
from datetime import datetime, timezone
from typing import Any, Dict, Iterable, List, Optional
from urllib.parse import quote

import httpx
import jwt
from fastapi import FastAPI, Header

from subscription_config import (
    clean_optional_str,
    get_android_package_name,
    get_android_plus_product_ids,
    get_android_premium_product_ids,
    get_apple_bundle_id,
    get_apple_issuer_id,
    get_apple_key_id,
    get_apple_private_key,
    get_ios_plus_product_ids,
    get_ios_premium_product_ids,
    get_plus_trial_offer_tag_android,
)
from subscription_release_config import _require_admin_bearer
from subscription_verifier_android import _get_google_access_token

logger = logging.getLogger("subscription_live_console_check")

_ASC_TOKEN_CACHE: Dict[str, Any] = {"token": None, "expires_at": 0.0}


class _ConsoleCheckError(RuntimeError):
    pass


class _AppleConsoleConfigError(_ConsoleCheckError):
    pass


class _GoogleConsoleConfigError(_ConsoleCheckError):
    pass


class _AppleConsoleHTTPError(_ConsoleCheckError):
    pass


class _GoogleConsoleHTTPError(_ConsoleCheckError):
    pass


def _clean(value: Any) -> str:
    return str(value or "").strip()


def _normalize_url(raw: Any) -> str:
    value = _clean(raw)
    return value.rstrip("/") if value else ""


def _first_non_empty(*values: Any) -> str:
    for value in values:
        txt = _clean(value)
        if txt:
            return txt
    return ""


def _apple_connect_issuer_id() -> str:
    value = _first_non_empty(
        os.getenv("COCOLON_IAP_ASC_ISSUER_ID"),
        os.getenv("COCOLON_IAP_APPSTORE_CONNECT_ISSUER_ID"),
    )
    if value:
        return value
    return get_apple_issuer_id()


def _apple_connect_key_id() -> str:
    value = _first_non_empty(
        os.getenv("COCOLON_IAP_ASC_KEY_ID"),
        os.getenv("COCOLON_IAP_APPSTORE_CONNECT_KEY_ID"),
    )
    if value:
        return value
    return get_apple_key_id()


def _apple_connect_private_key() -> str:
    raw = str(
        os.getenv("COCOLON_IAP_ASC_PRIVATE_KEY", "")
        or os.getenv("COCOLON_IAP_APPSTORE_CONNECT_PRIVATE_KEY", "")
    ).replace("\\n", "\n").strip()
    if raw:
        return raw

    file_path = _first_non_empty(
        os.getenv("COCOLON_IAP_ASC_PRIVATE_KEY_FILE"),
        os.getenv("COCOLON_IAP_APPSTORE_CONNECT_PRIVATE_KEY_FILE"),
    )
    if file_path:
        with open(file_path, "r", encoding="utf-8") as fh:
            return fh.read()

    return get_apple_private_key()


def _apple_console_credentials_source() -> str:
    if _clean(os.getenv("COCOLON_IAP_ASC_PRIVATE_KEY")) or _clean(os.getenv("COCOLON_IAP_APPSTORE_CONNECT_PRIVATE_KEY")):
        return "asc_inline"
    if _clean(os.getenv("COCOLON_IAP_ASC_PRIVATE_KEY_FILE")) or _clean(os.getenv("COCOLON_IAP_APPSTORE_CONNECT_PRIVATE_KEY_FILE")):
        return "asc_file"
    if _clean(os.getenv("COCOLON_IAP_APPLE_PRIVATE_KEY")):
        return "apple_server_inline_fallback"
    if _clean(os.getenv("COCOLON_IAP_APPLE_PRIVATE_KEY_FILE")):
        return "apple_server_file_fallback"
    return "missing"


def _apple_connect_ready() -> bool:
    try:
        _apple_connect_issuer_id()
        _apple_connect_key_id()
        _apple_connect_private_key()
        get_apple_bundle_id()
        return True
    except Exception:
        return False


async def _get_apple_connect_bearer_token() -> str:
    now = time.time()
    cached = _clean(_ASC_TOKEN_CACHE.get("token"))
    expires_at = float(_ASC_TOKEN_CACHE.get("expires_at") or 0.0)
    if cached and expires_at - 60 > now:
        return cached

    issuer_id = _apple_connect_issuer_id()
    key_id = _apple_connect_key_id()
    private_key = _apple_connect_private_key()
    iat = int(now)
    exp = iat + 15 * 60
    token = jwt.encode(
        {
            "iss": issuer_id,
            "iat": iat,
            "exp": exp,
            "aud": "appstoreconnect-v1",
        },
        private_key,
        algorithm="ES256",
        headers={"kid": key_id, "typ": "JWT"},
    )
    _ASC_TOKEN_CACHE["token"] = token
    _ASC_TOKEN_CACHE["expires_at"] = float(exp)
    return token


async def _apple_connect_request(path_or_url: str, *, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    url = path_or_url if str(path_or_url).startswith("http") else f"https://api.appstoreconnect.apple.com{path_or_url}"
    bearer = await _get_apple_connect_bearer_token()
    async with httpx.AsyncClient(timeout=18.0) as client:
        resp = await client.get(
            url,
            params=params,
            headers={
                "Authorization": f"Bearer {bearer}",
                "Accept": "application/json",
            },
        )
    if resp.status_code >= 300:
        raise _AppleConsoleHTTPError(
            f"Apple App Store Connect API request failed: status={resp.status_code} body={resp.text[:1200]}"
        )
    data = resp.json()
    if not isinstance(data, dict):
        raise _AppleConsoleHTTPError("Apple App Store Connect API response was not a JSON object")
    return data


async def _apple_connect_list(path: str, *, params: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
    items: List[Dict[str, Any]] = []
    next_url: Optional[str] = path
    next_params = dict(params or {})
    while next_url:
        payload = await _apple_connect_request(next_url, params=next_params)
        next_params = None
        rows = payload.get("data") or []
        if isinstance(rows, list):
            items.extend([row for row in rows if isinstance(row, dict)])
        links = payload.get("links") if isinstance(payload.get("links"), dict) else {}
        candidate = links.get("next")
        if isinstance(candidate, dict):
            candidate = candidate.get("href")
        next_url = _clean(candidate) or None
    return items


async def _google_console_request(path: str, *, params: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    access_token = await _get_google_access_token()
    url = f"https://androidpublisher.googleapis.com/androidpublisher/v3{path}"
    async with httpx.AsyncClient(timeout=18.0) as client:
        resp = await client.get(
            url,
            params=params,
            headers={
                "Authorization": f"Bearer {access_token}",
                "Accept": "application/json",
            },
        )
    if resp.status_code >= 300:
        raise _GoogleConsoleHTTPError(
            f"Google Play Developer API request failed: status={resp.status_code} body={resp.text[:1200]}"
        )
    data = resp.json()
    if not isinstance(data, dict):
        raise _GoogleConsoleHTTPError("Google Play Developer API response was not a JSON object")
    return data


async def _google_console_list_offers(*, package_name: str, product_id: str, base_plan_id: str) -> List[Dict[str, Any]]:
    offers: List[Dict[str, Any]] = []
    page_token: Optional[str] = None
    while True:
        params: Dict[str, Any] = {"pageSize": 1000}
        if page_token:
            params["pageToken"] = page_token
        payload = await _google_console_request(
            f"/applications/{quote(package_name, safe='')}/subscriptions/{quote(product_id, safe='')}/basePlans/{quote(base_plan_id, safe='')}/offers",
            params=params,
        )
        rows = payload.get("subscriptionOffers") or []
        if isinstance(rows, list):
            offers.extend([row for row in rows if isinstance(row, dict)])
        page_token = _clean(payload.get("nextPageToken")) or None
        if not page_token:
            break
    return offers


def _apple_attr(row: Dict[str, Any], *keys: str) -> Any:
    attrs = row.get("attributes") if isinstance(row.get("attributes"), dict) else {}
    for key in keys:
        if key in attrs and attrs.get(key) is not None:
            return attrs.get(key)
    return None


def _apple_relationship_ids(row: Dict[str, Any], relationship_name: str) -> List[str]:
    relationships = row.get("relationships") if isinstance(row.get("relationships"), dict) else {}
    rel = relationships.get(relationship_name) if isinstance(relationships.get(relationship_name), dict) else {}
    data = rel.get("data") if isinstance(rel.get("data"), list) else []
    out: List[str] = []
    for item in data:
        if isinstance(item, dict):
            value = _clean(item.get("id"))
            if value:
                out.append(value)
    return out


def _gplay_offer_tags(raw: Iterable[Any]) -> List[str]:
    out: List[str] = []
    for item in raw or []:
        if isinstance(item, dict):
            tag = _first_non_empty(item.get("tag"), item.get("name"), item.get("value"))
        else:
            tag = _clean(item)
        if tag and tag not in out:
            out.append(tag)
    return out


def _bool_from_strings(*values: Any, equals: Optional[Iterable[str]] = None) -> bool:
    allowed = {str(v).strip().upper() for v in (equals or []) if str(v).strip()}
    for value in values:
        raw = str(value or "").strip().upper()
        if not raw:
            continue
        if allowed:
            if raw in allowed:
                return True
        elif raw in {"1", "TRUE", "YES", "ON"}:
            return True
    return False


def _apple_intro_offer_summary(offer: Dict[str, Any]) -> Dict[str, Any]:
    attrs = offer.get("attributes") if isinstance(offer.get("attributes"), dict) else {}
    mode = _first_non_empty(attrs.get("offerMode"), attrs.get("mode"), attrs.get("paymentMode"))
    period = _first_non_empty(
        attrs.get("subscriptionPeriod"),
        attrs.get("duration"),
        attrs.get("offerDuration"),
        attrs.get("durationValue"),
    )
    periods = attrs.get("numberOfPeriods")
    joined = " ".join([str(v) for v in attrs.values() if v is not None]).upper()
    free_trial_detected = "FREE" in joined or "TRIAL" in joined or mode.upper() in {"FREE_TRIAL", "FREE"}
    one_month_detected = "P1M" in joined or "ONE_MONTH" in joined or ("MONTH" in joined and "1" in joined)
    return {
        "id": _clean(offer.get("id")) or None,
        "mode": mode or None,
        "period": period or None,
        "number_of_periods": periods,
        "free_trial_detected": free_trial_detected,
        "one_month_detected": one_month_detected,
        "raw_attributes": attrs,
    }


def _gplay_offer_has_free_trial(offer: Dict[str, Any]) -> bool:
    phases = offer.get("phases") or []
    if not isinstance(phases, list):
        return False
    for phase in phases:
        if not isinstance(phase, dict):
            continue
        regional_configs = phase.get("regionalConfigs") or []
        if not isinstance(regional_configs, list):
            regional_configs = []
        other_regions = phase.get("otherRegionsConfig") or {}
        for config in regional_configs:
            if isinstance(config, dict) and config.get("free") is not None:
                return True
        if isinstance(other_regions, dict) and other_regions.get("free") is not None:
            return True
    return False


def _gplay_offer_is_one_month(offer: Dict[str, Any]) -> bool:
    phases = offer.get("phases") or []
    if not isinstance(phases, list) or not phases:
        return False
    joined = " ".join([str(v) for phase in phases if isinstance(phase, dict) for v in phase.values() if v is not None]).upper()
    return "P1M" in joined or ("MONTH" in joined and "1" in joined)


def _gplay_offer_summary(offer: Dict[str, Any]) -> Dict[str, Any]:
    offer_tags = _gplay_offer_tags(offer.get("offerTags") or [])
    targeting = offer.get("targeting") if isinstance(offer.get("targeting"), dict) else {}
    targeting_rule = ""
    if targeting.get("acquisitionRule") is not None:
        targeting_rule = "acquisition"
    elif targeting.get("upgradeRule") is not None:
        targeting_rule = "upgrade"
    phase_summaries = []
    phases = offer.get("phases") or []
    if isinstance(phases, list):
        for phase in phases:
            if not isinstance(phase, dict):
                continue
            phase_summaries.append(
                {
                    "duration": _clean(phase.get("duration")) or None,
                    "recurrence_count": phase.get("recurrenceCount"),
                    "has_free_region_override": any(
                        isinstance(cfg, dict) and cfg.get("free") is not None
                        for cfg in (phase.get("regionalConfigs") or [])
                    ) or (
                        isinstance(phase.get("otherRegionsConfig"), dict)
                        and phase.get("otherRegionsConfig", {}).get("free") is not None
                    ),
                }
            )
    return {
        "offer_id": _clean(offer.get("offerId")) or None,
        "base_plan_id": _clean(offer.get("basePlanId")) or None,
        "state": _clean(offer.get("state")) or None,
        "offer_tags": offer_tags,
        "targeting_rule": targeting_rule or None,
        "has_free_trial_phase": _gplay_offer_has_free_trial(offer),
        "has_one_month_phase": _gplay_offer_is_one_month(offer),
        "phases": phase_summaries,
    }


async def _fetch_apple_live_snapshot() -> Dict[str, Any]:
    bundle_id = clean_optional_str(get_apple_bundle_id())
    if not bundle_id:
        raise _AppleConsoleConfigError("Apple bundle ID is not configured")

    expected_plus_ids = sorted({pid for pid in get_ios_plus_product_ids() if clean_optional_str(pid)})
    expected_premium_ids = sorted({pid for pid in get_ios_premium_product_ids() if clean_optional_str(pid)})

    apps = await _apple_connect_list("/v1/apps", params={"filter[bundleId]": bundle_id, "limit": 50})
    app_row = apps[0] if apps else {}
    app_id = _clean(app_row.get("id")) or None
    app_name = _apple_attr(app_row, "name") or _apple_attr(app_row, "bundleId") or None

    groups: List[Dict[str, Any]] = []
    subscriptions: List[Dict[str, Any]] = []
    if app_id:
        groups = await _apple_connect_list(f"/v1/apps/{quote(app_id, safe='')}/subscriptionGroups", params={"limit": 200})
        for group in groups:
            group_id = _clean(group.get("id"))
            if not group_id:
                continue
            subscriptions.extend(
                await _apple_connect_list(f"/v1/subscriptionGroups/{quote(group_id, safe='')}/subscriptions", params={"limit": 200})
            )

    product_map: Dict[str, Dict[str, Any]] = {}
    subscription_rows: List[Dict[str, Any]] = []
    for sub in subscriptions:
        sub_id = _clean(sub.get("id")) or None
        product_id = _first_non_empty(
            _apple_attr(sub, "productId"),
            _apple_attr(sub, "productID"),
            _apple_attr(sub, "productIdentifier"),
            _apple_attr(sub, "referenceName"),
        )
        group_ids = _apple_relationship_ids(sub, "subscriptionGroup")
        intro_rows: List[Dict[str, Any]] = []
        if sub_id:
            try:
                intro_rows = await _apple_connect_list(
                    f"/v1/subscriptions/{quote(sub_id, safe='')}/introductoryOffers",
                    params={"limit": 200},
                )
            except Exception as exc:
                logger.warning("Failed to fetch Apple introductory offers for %s: %s", sub_id, exc)
                intro_rows = []
        intro_summaries = [_apple_intro_offer_summary(row) for row in intro_rows]
        row = {
            "id": sub_id,
            "product_id": product_id or None,
            "reference_name": _first_non_empty(_apple_attr(sub, "referenceName"), _apple_attr(sub, "name")) or None,
            "state": _first_non_empty(_apple_attr(sub, "state"), _apple_attr(sub, "status")) or None,
            "group_ids": group_ids,
            "introductory_offer_count": len(intro_summaries),
            "introductory_offers": intro_summaries,
            "raw_attributes": sub.get("attributes") if isinstance(sub.get("attributes"), dict) else {},
        }
        subscription_rows.append(row)
        if product_id:
            product_map[product_id] = row

    found_product_ids = sorted(product_map.keys())
    missing_plus_ids = sorted(pid for pid in expected_plus_ids if pid not in product_map)
    missing_premium_ids = sorted(pid for pid in expected_premium_ids if pid not in product_map)
    plus_intro_present = all(
        bool(product_map.get(pid, {}).get("introductory_offer_count")) for pid in expected_plus_ids if product_map.get(pid)
    ) if expected_plus_ids else False
    plus_intro_one_month = all(
        any(
            bool(item.get("free_trial_detected")) and bool(item.get("one_month_detected"))
            for item in (product_map.get(pid, {}).get("introductory_offers") or [])
        )
        for pid in expected_plus_ids if product_map.get(pid)
    ) if expected_plus_ids else False

    blocking_issues: List[str] = []
    warnings: List[str] = []
    if not app_id:
        blocking_issues.append(f"Apple app was not found in App Store Connect for bundleId={bundle_id}.")
    if missing_plus_ids:
        blocking_issues.append(f"Apple Plus product IDs are missing in App Store Connect: {', '.join(missing_plus_ids)}")
    if missing_premium_ids:
        warnings.append(f"Apple Premium product IDs are missing in App Store Connect: {', '.join(missing_premium_ids)}")
    if expected_plus_ids and not plus_intro_present:
        blocking_issues.append("Apple Plus subscription exists, but no introductory offer was found for at least one expected Plus product.")
    if expected_plus_ids and plus_intro_present and not plus_intro_one_month:
        warnings.append("Apple introductory offer exists, but its exact 1-month free-trial shape could not be confirmed automatically. Review the returned raw offer attributes.")

    return {
        "credentials_source": _apple_console_credentials_source(),
        "bundle_id": bundle_id,
        "app_found": bool(app_id),
        "app_id": app_id,
        "app_name": app_name,
        "subscription_group_count": len(groups),
        "expected_plus_product_ids": expected_plus_ids,
        "expected_premium_product_ids": expected_premium_ids,
        "found_product_ids": found_product_ids,
        "missing_plus_product_ids": missing_plus_ids,
        "missing_premium_product_ids": missing_premium_ids,
        "plus_intro_offer_present_for_all_expected_products": plus_intro_present,
        "plus_intro_offer_one_month_free_trial_confirmed": plus_intro_one_month,
        "subscriptions": subscription_rows,
        "blocking_issues": blocking_issues,
        "warnings": warnings,
        "ready": len(blocking_issues) == 0,
    }


async def _fetch_google_live_snapshot() -> Dict[str, Any]:
    package_name = clean_optional_str(get_android_package_name())
    if not package_name:
        raise _GoogleConsoleConfigError("Google package name is not configured")

    expected_plus_ids = sorted({pid for pid in get_android_plus_product_ids() if clean_optional_str(pid)})
    expected_premium_ids = sorted({pid for pid in get_android_premium_product_ids() if clean_optional_str(pid)})
    expected_trial_offer_tag = clean_optional_str(get_plus_trial_offer_tag_android())

    product_ids = sorted(set(expected_plus_ids + expected_premium_ids))
    product_rows: List[Dict[str, Any]] = []
    found_product_ids: List[str] = []
    blocking_issues: List[str] = []
    warnings: List[str] = []

    for product_id in product_ids:
        try:
            sub = await _google_console_request(
                f"/applications/{quote(package_name, safe='')}/subscriptions/{quote(product_id, safe='')}"
            )
        except Exception as exc:
            blocking_issues.append(f"Google subscription could not be fetched for productId={product_id}: {exc}")
            continue

        found_product_ids.append(product_id)
        base_plans = sub.get("basePlans") or []
        if not isinstance(base_plans, list):
            base_plans = []
        base_plan_rows: List[Dict[str, Any]] = []
        any_active_base_plan = False
        plus_trial_offer_present = False
        plus_trial_tag_match = False
        plus_trial_one_month = False

        for base_plan in base_plans:
            if not isinstance(base_plan, dict):
                continue
            base_plan_id = _clean(base_plan.get("basePlanId"))
            state = _clean(base_plan.get("state"))
            if state.upper() == "ACTIVE":
                any_active_base_plan = True
            offers: List[Dict[str, Any]] = []
            if base_plan_id:
                try:
                    offers = await _google_console_list_offers(
                        package_name=package_name,
                        product_id=product_id,
                        base_plan_id=base_plan_id,
                    )
                except Exception as exc:
                    warnings.append(f"Google offers could not be listed for productId={product_id}, basePlanId={base_plan_id}: {exc}")
                    offers = []
            offer_summaries = [_gplay_offer_summary(offer) for offer in offers]
            if product_id in expected_plus_ids:
                active_offers = [offer for offer in offer_summaries if _clean(offer.get("state")).upper() == "ACTIVE"]
                plus_trial_offer_present = plus_trial_offer_present or any(
                    bool(offer.get("has_free_trial_phase")) for offer in active_offers
                )
                plus_trial_tag_match = plus_trial_tag_match or any(
                    expected_trial_offer_tag and expected_trial_offer_tag in (offer.get("offer_tags") or [])
                    for offer in active_offers
                )
                plus_trial_one_month = plus_trial_one_month or any(
                    bool(offer.get("has_free_trial_phase")) and bool(offer.get("has_one_month_phase"))
                    for offer in active_offers
                )
            base_plan_rows.append(
                {
                    "base_plan_id": base_plan_id or None,
                    "state": state or None,
                    "billing_period_duration": _first_non_empty(
                        ((base_plan.get("autoRenewingBasePlanType") or {}).get("billingPeriodDuration") if isinstance(base_plan.get("autoRenewingBasePlanType"), dict) else None),
                        ((base_plan.get("prepaidBasePlanType") or {}).get("billingPeriodDuration") if isinstance(base_plan.get("prepaidBasePlanType"), dict) else None),
                        ((base_plan.get("installmentsBasePlanType") or {}).get("billingPeriodDuration") if isinstance(base_plan.get("installmentsBasePlanType"), dict) else None),
                    ) or None,
                    "offer_tags": _gplay_offer_tags(base_plan.get("offerTags") or []),
                    "offers": offer_summaries,
                }
            )

        product_rows.append(
            {
                "product_id": product_id,
                "title": _first_non_empty(
                    ((sub.get("listings") or [{}])[0] or {}).get("title") if isinstance(sub.get("listings"), list) and sub.get("listings") else None,
                    ((sub.get("listings") or [{}])[0] or {}).get("name") if isinstance(sub.get("listings"), list) and sub.get("listings") else None,
                ) or None,
                "base_plan_count": len(base_plan_rows),
                "has_active_base_plan": any_active_base_plan,
                "plus_trial_offer_present": plus_trial_offer_present if product_id in expected_plus_ids else None,
                "plus_trial_offer_tag_match": plus_trial_tag_match if product_id in expected_plus_ids else None,
                "plus_trial_one_month_confirmed": plus_trial_one_month if product_id in expected_plus_ids else None,
                "base_plans": base_plan_rows,
            }
        )

    missing_plus_ids = sorted(pid for pid in expected_plus_ids if pid not in found_product_ids)
    missing_premium_ids = sorted(pid for pid in expected_premium_ids if pid not in found_product_ids)

    plus_rows = [row for row in product_rows if row.get("product_id") in expected_plus_ids]
    plus_active_base_plan_present = all(bool(row.get("has_active_base_plan")) for row in plus_rows) if plus_rows else False
    plus_trial_offer_present = all(bool(row.get("plus_trial_offer_present")) for row in plus_rows) if plus_rows else False
    plus_trial_offer_tag_match = all(bool(row.get("plus_trial_offer_tag_match")) for row in plus_rows) if plus_rows and expected_trial_offer_tag else False
    plus_trial_one_month = all(bool(row.get("plus_trial_one_month_confirmed")) for row in plus_rows) if plus_rows else False

    if missing_plus_ids:
        blocking_issues.append(f"Google Plus product IDs are missing in Play Console: {', '.join(missing_plus_ids)}")
    if missing_premium_ids:
        warnings.append(f"Google Premium product IDs are missing in Play Console: {', '.join(missing_premium_ids)}")
    if plus_rows and not plus_active_base_plan_present:
        blocking_issues.append("Google Plus subscription exists, but at least one expected Plus product has no ACTIVE base plan.")
    if plus_rows and not plus_trial_offer_present:
        blocking_issues.append("Google Plus subscription exists, but no ACTIVE free-trial offer was found under the expected Plus products.")
    if plus_rows and plus_trial_offer_present and expected_trial_offer_tag and not plus_trial_offer_tag_match:
        warnings.append(
            f"Google free-trial offer exists, but the expected offer tag '{expected_trial_offer_tag}' was not found on any ACTIVE Plus offer."
        )
    if plus_rows and plus_trial_offer_present and not plus_trial_one_month:
        warnings.append("Google free-trial offer exists, but its exact 1-month phase could not be confirmed automatically from the returned offer data.")

    return {
        "package_name": package_name,
        "expected_plus_product_ids": expected_plus_ids,
        "expected_premium_product_ids": expected_premium_ids,
        "expected_plus_trial_offer_tag": expected_trial_offer_tag or None,
        "found_product_ids": sorted(found_product_ids),
        "missing_plus_product_ids": missing_plus_ids,
        "missing_premium_product_ids": missing_premium_ids,
        "plus_active_base_plan_present_for_all_expected_products": plus_active_base_plan_present,
        "plus_trial_offer_present_for_all_expected_products": plus_trial_offer_present,
        "plus_trial_offer_tag_match_for_all_expected_products": plus_trial_offer_tag_match if expected_trial_offer_tag else None,
        "plus_trial_offer_one_month_confirmed": plus_trial_one_month,
        "subscriptions": product_rows,
        "blocking_issues": blocking_issues,
        "warnings": warnings,
        "ready": len(blocking_issues) == 0,
    }


async def build_subscription_live_console_report() -> Dict[str, Any]:
    report: Dict[str, Any] = {
        "checked_at": datetime.now(timezone.utc).isoformat(),
        "environment": _first_non_empty(os.getenv("MYMODEL_ENV"), os.getenv("ENVIRONMENT"), os.getenv("RENDER_ENV")) or "unknown",
        "ready": False,
        "providers": {},
        "blocking_issues": [],
        "warnings": [],
        "manual_checks": [
            {
                "field": "apple_app_store_server_notifications_url",
                "status": "manual",
                "reason": "App Store Server Notifications endpoint URL is not fetched here. Confirm it points to /subscription/webhooks/apple in App Store Connect.",
            },
            {
                "field": "google_rtdn_pubsub_delivery",
                "status": "manual",
                "reason": "Google RTDN Pub/Sub push wiring is outside the Android Publisher subscription catalog APIs. Confirm the topic/subscription reaches /subscription/webhooks/google.",
            },
            {
                "field": "terms_and_privacy_urls",
                "status": "manual",
                "reason": "Terms / Privacy URLs are outside App Store Connect and Play Console catalog APIs. Confirm the app build uses the intended public URLs.",
            },
        ],
    }

    apple_blocking: List[str] = []
    google_blocking: List[str] = []
    apple_warnings: List[str] = []
    google_warnings: List[str] = []

    if not _apple_connect_ready():
        apple_snapshot = {
            "ready": False,
            "blocking_issues": [
                "Apple App Store Connect live check is not configured. Provide App Store Connect API credentials (or fall back to the Apple server verification key) and bundle ID."
            ],
            "warnings": [],
            "credentials_source": _apple_console_credentials_source(),
            "bundle_id": clean_optional_str(os.getenv("COCOLON_IAP_APPLE_BUNDLE_ID") or os.getenv("EXPO_PUBLIC_IOS_BUNDLE_ID")) or None,
        }
    else:
        try:
            apple_snapshot = await _fetch_apple_live_snapshot()
        except Exception as exc:
            apple_snapshot = {
                "ready": False,
                "blocking_issues": [f"Apple live check failed: {exc}"],
                "warnings": [],
                "credentials_source": _apple_console_credentials_source(),
            }
    apple_blocking.extend(apple_snapshot.get("blocking_issues") or [])
    apple_warnings.extend(apple_snapshot.get("warnings") or [])
    report["providers"]["apple"] = apple_snapshot

    try:
        package_name_preview = clean_optional_str(get_android_package_name())
    except Exception:
        package_name_preview = None

    try:
        await _get_google_access_token()
        google_auth_ready = True
    except Exception:
        google_auth_ready = False

    if not package_name_preview or not google_auth_ready:
        google_snapshot = {
            "ready": False,
            "blocking_issues": [
                "Google Play live check is not configured. Provide package name plus Play Developer API service-account credentials."
            ],
            "warnings": [],
            "package_name": package_name_preview,
        }
    else:
        try:
            google_snapshot = await _fetch_google_live_snapshot()
        except Exception as exc:
            google_snapshot = {
                "ready": False,
                "blocking_issues": [f"Google live check failed: {exc}"],
                "warnings": [],
                "package_name": package_name_preview,
            }
    google_blocking.extend(google_snapshot.get("blocking_issues") or [])
    google_warnings.extend(google_snapshot.get("warnings") or [])
    report["providers"]["google"] = google_snapshot

    report["blocking_issues"] = apple_blocking + google_blocking
    report["warnings"] = apple_warnings + google_warnings
    report["ready"] = len(report["blocking_issues"]) == 0
    return report


def register_subscription_live_console_routes(app: FastAPI) -> None:
    @app.get("/subscription/config/release-check/live")
    async def subscription_release_check_live(
        authorization: Optional[str] = Header(default=None, alias="Authorization"),
    ) -> Dict[str, Any]:
        _require_admin_bearer(authorization)
        return await build_subscription_live_console_report()
