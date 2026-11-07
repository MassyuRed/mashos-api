from __future__ import annotations

import asyncio
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
for candidate in (ROOT, ROOT / "services", ROOT / "services" / "ai_inference"):
    path_str = str(candidate)
    if path_str not in sys.path:
        sys.path.insert(0, path_str)

import subscription_live_console_check as console
import subscription_bootstrap_store as runtime_catalog


@pytest.fixture
def catalog(monkeypatch):
    state = {
        "ios_plus_ids": ["synthetic.plus"],
        "ios_premium_ids": ["synthetic.premium"],
        "apple_products": ["synthetic.plus", "synthetic.premium"],
        "android_plus_ids": ["synthetic.shared"],
        "android_premium_ids": ["synthetic.shared"],
        "android_purchase_ids": ["synthetic.shared"],
        "google_products": {
            "synthetic.shared": {"plus": "ACTIVE", "premium": "ACTIVE"},
        },
        "base_plan_config": {
            "COCOLON_IAP_ANDROID_PLUS_BASE_PLAN_IDS": ["plus"],
            "COCOLON_IAP_ANDROID_PREMIUM_BASE_PLAN_IDS": ["premium"],
        },
    }

    monkeypatch.setattr(console, "get_apple_bundle_id", lambda: "synthetic.app")
    monkeypatch.setattr(console, "get_android_package_name", lambda: "synthetic.app")
    monkeypatch.setattr(console, "_apple_console_credentials_source", lambda: "synthetic-only")
    monkeypatch.setattr(console, "get_ios_plus_product_ids", lambda: state["ios_plus_ids"])
    monkeypatch.setattr(console, "get_ios_premium_product_ids", lambda: state["ios_premium_ids"])
    monkeypatch.setattr(console, "get_android_plus_product_ids", lambda: state["android_plus_ids"])
    monkeypatch.setattr(console, "get_android_premium_product_ids", lambda: state["android_premium_ids"])
    monkeypatch.setattr(console, "_android_shared_product_ids", lambda: state["android_purchase_ids"])
    monkeypatch.setattr(runtime_catalog, "_android_base_plan_ids", lambda tier: state["base_plan_config"].get(
        f"COCOLON_IAP_ANDROID_{tier.upper()}_BASE_PLAN_IDS", []
    ))

    async def apple_list(path, **kwargs):
        if path == "/v1/apps":
            return [{"id": "synthetic-app"}]
        if path.endswith("/subscriptionGroups"):
            return [{"id": "synthetic-group"}]
        return [
            {"id": product_id, "attributes": {"productId": product_id}}
            for product_id in state["apple_products"]
        ]

    async def google_request(path, **kwargs):
        product_id = path.rsplit("/", 1)[-1]
        if product_id not in state["google_products"]:
            raise RuntimeError("synthetic product missing")
        return {
            "basePlans": [
                {"basePlanId": plan_id, "state": plan_state}
                for plan_id, plan_state in state["google_products"][product_id].items()
            ],
        }

    async def no_offers(**kwargs):
        return []

    monkeypatch.setattr(console, "_apple_connect_list", apple_list)
    monkeypatch.setattr(console, "_google_console_request", google_request)
    monkeypatch.setattr(console, "_google_console_list_offers", no_offers)
    return state


def test_apple_both_expected_products_present(catalog):
    snapshot = asyncio.run(console._fetch_apple_live_snapshot())
    assert snapshot["ready"] is True
    assert snapshot["blocking_issues"] == []


@pytest.mark.parametrize("tier", ["plus", "premium"])
def test_apple_missing_product_blocks_readiness(tier, catalog):
    catalog["apple_products"].remove(f"synthetic.{tier}")
    snapshot = asyncio.run(console._fetch_apple_live_snapshot())
    assert snapshot["ready"] is False
    assert snapshot[f"missing_{tier}_product_ids"] == [f"synthetic.{tier}"]
    assert snapshot["blocking_issues"]


@pytest.mark.parametrize("tier", ["plus", "premium"])
def test_apple_missing_expected_configuration_is_not_ready(tier, catalog):
    catalog[f"ios_{tier}_ids"] = []
    snapshot = asyncio.run(console._fetch_apple_live_snapshot())
    assert snapshot["ready"] is False
    assert snapshot["blocking_issues"]


def test_google_shared_product_has_each_tier_active(catalog):
    snapshot = asyncio.run(console._fetch_google_live_snapshot())
    assert snapshot["ready"] is True
    assert snapshot["plus_active_base_plan_present_for_all_expected_products"] is True
    assert snapshot["blocking_issues"] == []


@pytest.mark.parametrize("missing_tier", ["plus", "premium"])
def test_google_other_active_tier_does_not_satisfy_missing_base_plan(missing_tier, catalog):
    del catalog["google_products"]["synthetic.shared"][missing_tier]
    snapshot = asyncio.run(console._fetch_google_live_snapshot())
    assert snapshot["ready"] is False
    assert snapshot["plus_active_base_plan_present_for_all_expected_products"] is (missing_tier != "plus")
    assert any(missing_tier in issue.lower() for issue in snapshot["blocking_issues"])


@pytest.mark.parametrize("tier", ["plus", "premium"])
@pytest.mark.parametrize("inactive_state", ["DRAFT", "INACTIVE"])
def test_google_expected_base_plan_must_itself_be_active(tier, inactive_state, catalog):
    catalog["google_products"]["synthetic.shared"][tier] = inactive_state
    snapshot = asyncio.run(console._fetch_google_live_snapshot())
    assert snapshot["ready"] is False
    assert any(tier in issue.lower() for issue in snapshot["blocking_issues"])


def test_google_unrelated_active_base_plan_is_not_paid_tier(catalog):
    catalog["google_products"]["synthetic.shared"] = {"unrelated": "ACTIVE"}
    snapshot = asyncio.run(console._fetch_google_live_snapshot())
    assert snapshot["ready"] is False
    assert snapshot["plus_active_base_plan_present_for_all_expected_products"] is False


@pytest.mark.parametrize("legacy_state", [None, "INACTIVE"])
def test_google_checks_purchase_default_and_allows_inactive_or_absent_legacy_base_plan(legacy_state, catalog):
    catalog["base_plan_config"] = {
        "COCOLON_IAP_ANDROID_PLUS_BASE_PLAN_IDS": ["alpha", "alpha-old"],
        "COCOLON_IAP_ANDROID_PREMIUM_BASE_PLAN_IDS": ["beta"],
    }
    catalog["google_products"]["synthetic.shared"] = {
        "alpha": "ACTIVE", "beta": "ACTIVE",
    }
    if legacy_state:
        catalog["google_products"]["synthetic.shared"]["alpha-old"] = legacy_state
    snapshot = asyncio.run(console._fetch_google_live_snapshot())
    assert snapshot["ready"] is True


def test_google_active_recognized_alias_cannot_replace_inactive_purchase_default(catalog):
    catalog["base_plan_config"]["COCOLON_IAP_ANDROID_PLUS_BASE_PLAN_IDS"] = ["alpha", "alpha-old"]
    catalog["google_products"]["synthetic.shared"] = {
        "alpha": "INACTIVE", "alpha-old": "ACTIVE", "premium": "ACTIVE",
    }
    snapshot = asyncio.run(console._fetch_google_live_snapshot())
    assert snapshot["ready"] is False
    assert snapshot["plus_active_base_plan_present_for_all_expected_products"] is False


def test_google_inactive_recognized_legacy_product_does_not_block_purchase_product(catalog):
    catalog["android_plus_ids"].append("synthetic.legacy")
    catalog["android_premium_ids"].append("synthetic.legacy")
    catalog["android_purchase_ids"].append("synthetic.legacy")
    catalog["google_products"]["synthetic.legacy"] = {"legacy": "INACTIVE"}
    snapshot = asyncio.run(console._fetch_google_live_snapshot())
    assert snapshot["ready"] is True


def test_google_active_plans_in_other_product_cannot_replace_purchase_product(catalog):
    catalog["android_plus_ids"].append("synthetic.legacy")
    catalog["android_premium_ids"].append("synthetic.legacy")
    catalog["google_products"]["synthetic.legacy"] = {"plus": "ACTIVE", "premium": "ACTIVE"}
    catalog["google_products"]["synthetic.shared"] = {"plus": "INACTIVE", "premium": "INACTIVE"}
    snapshot = asyncio.run(console._fetch_google_live_snapshot())
    assert snapshot["ready"] is False


@pytest.mark.parametrize("tier", ["plus", "premium"])
def test_google_missing_expected_product_configuration_is_not_ready(tier, catalog):
    catalog[f"android_{tier}_ids"] = []
    snapshot = asyncio.run(console._fetch_google_live_snapshot())
    assert snapshot["ready"] is False
    assert snapshot["blocking_issues"]


def test_google_missing_separate_premium_product_blocks_readiness(catalog):
    catalog["android_premium_ids"] = ["synthetic.premium"]
    snapshot = asyncio.run(console._fetch_google_live_snapshot())
    assert snapshot["ready"] is False
    assert snapshot["missing_premium_product_ids"] == ["synthetic.premium"]
    assert snapshot["blocking_issues"]
