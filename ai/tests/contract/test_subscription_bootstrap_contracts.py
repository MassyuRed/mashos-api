from __future__ import annotations


def test_subscription_bootstrap_contract_shape(client, monkeypatch):
    import api_subscription as subscription_module

    async def fake_build_subscription_bootstrap(*, client_meta):
        assert client_meta.get("platform") == "ios"
        assert client_meta.get("app_version") == "1.2.3"
        return {
            "sales_enabled": True,
            "client_sales_enabled": True,
            "client_sales_disabled_reason": None,
            "links": {
                "terms_url": "https://example.com/terms",
                "privacy_url": "https://example.com/privacy",
                "support_url": "https://example.com/support",
            },
            "policy": {
                "restore_enabled": True,
                "manage_enabled": True,
                "ios_manage_url": "https://apps.apple.com/account/subscriptions",
                "android_manage_mode": "specific_subscription",
                "android_package_name": "com.example.cocolon",
                "review_notice": None,
            },
            "plans": {
                "plus": {
                    "visible": True,
                    "purchasable": True,
                    "launch_stage": "live",
                    "title": "Plusプラン",
                    "price_label": "月額300円",
                    "subtitle": "レポート閲覧 / ReflectionCreate拡張",
                    "features": ["feature-a"],
                    "note_lines": ["note-a"],
                    "cta_label": "このプランを選ぶ",
                    "recommended": True,
                    "purchase_product_id": {
                        "ios": "cocolon_plus_monthly",
                        "android": "emlis",
                    },
                    "recognized_product_ids": {
                        "ios": ["cocolon_plus_monthly"],
                        "android": ["emlis"],
                    },
                    "purchase_base_plan_id": {
                        "ios": None,
                        "android": "plus",
                    },
                    "recognized_base_plan_ids": {
                        "ios": [],
                        "android": ["plus"],
                    },
                },
                "premium": {
                    "visible": True,
                    "purchasable": True,
                    "launch_stage": "live",
                    "title": "Premiumプラン",
                    "price_label": "月額980円",
                    "subtitle": "表示期間無制限 / 深いレポート / Reflection生成",
                    "features": ["feature-p"],
                    "note_lines": ["月額980円で自動更新されます。"],
                    "cta_label": "このプランを選ぶ",
                    "recommended": False,
                    "purchase_product_id": {
                        "ios": "cocolon_premium_monthly",
                        "android": "emlis",
                    },
                    "recognized_product_ids": {
                        "ios": ["cocolon_premium_monthly"],
                        "android": ["emlis"],
                    },
                    "purchase_base_plan_id": {
                        "ios": None,
                        "android": "premium",
                    },
                    "recognized_base_plan_ids": {
                        "ios": [],
                        "android": ["premium"],
                    },
                },
            },
        }

    monkeypatch.setattr(subscription_module, "build_subscription_bootstrap", fake_build_subscription_bootstrap)

    response = client.get(
        "/subscription/bootstrap",
        headers={
            "X-App-Version": "1.2.3",
            "X-App-Build": "123",
            "X-Platform": "ios",
        },
    )

    assert response.status_code == 200, response.text
    assert response.headers["X-Cocolon-Contract-Id"] == "subscription.bootstrap.v1"
    body = response.json()
    assert body["sales_enabled"] is True
    assert body["client_sales_enabled"] is True
    assert body["links"]["terms_url"] == "https://example.com/terms"
    assert body["plans"]["plus"]["purchase_product_id"]["ios"] == "cocolon_plus_monthly"
    assert body["plans"]["premium"]["purchasable"] is True


def test_subscription_bootstrap_respects_disabled_reason_shape(client, monkeypatch):
    import api_subscription as subscription_module

    async def fake_build_subscription_bootstrap(*, client_meta):
        return {
            "sales_enabled": True,
            "client_sales_enabled": False,
            "client_sales_disabled_reason": "このバージョンでは購入できません。",
            "links": {
                "terms_url": "https://example.com/terms",
                "privacy_url": "https://example.com/privacy",
                "support_url": "https://example.com/support",
            },
            "policy": {
                "restore_enabled": True,
                "manage_enabled": True,
                "ios_manage_url": "https://apps.apple.com/account/subscriptions",
                "android_manage_mode": "specific_subscription",
                "android_package_name": "com.example.cocolon",
                "review_notice": "現在、サブスクリプション販売を一時停止しています。",
            },
            "plans": {
                "plus": {
                    "visible": True,
                    "purchasable": False,
                    "launch_stage": "live",
                    "title": "Plusプラン",
                    "price_label": "月額300円",
                    "subtitle": "レポート閲覧 / ReflectionCreate拡張",
                    "features": [],
                    "note_lines": [],
                    "cta_label": "このプランを選ぶ",
                    "recommended": True,
                    "purchase_product_id": {"ios": "cocolon_plus_monthly", "android": "emlis"},
                    "recognized_product_ids": {"ios": ["cocolon_plus_monthly"], "android": ["emlis"]},
                    "purchase_base_plan_id": {"ios": None, "android": "plus"},
                    "recognized_base_plan_ids": {"ios": [], "android": ["plus"]},
                }
            },
        }

    monkeypatch.setattr(subscription_module, "build_subscription_bootstrap", fake_build_subscription_bootstrap)
    response = client.get("/subscription/bootstrap", headers={"X-Platform": "ios"})
    assert response.status_code == 200, response.text
    body = response.json()
    assert body["client_sales_enabled"] is False
    assert body["client_sales_disabled_reason"] == "このバージョンでは購入できません。"
    assert body["policy"]["review_notice"] == "現在、サブスクリプション販売を一時停止しています。"
