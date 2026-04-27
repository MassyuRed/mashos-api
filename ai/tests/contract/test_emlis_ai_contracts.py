from __future__ import annotations


def test_emotion_submit_contract_allows_additive_emlis_ai_meta(client, monkeypatch):
    import api_emotion_submit as emotion_submit_module
    import emotion_submit_service as emotion_submit_service_module

    async def fake_resolve_user_id_from_token(_access_token: str) -> str:
        return "user-123"

    async def fake_persist_emotion_submission(**kwargs):
        assert kwargs["user_id"] == "user-123"
        return {
            "inserted": {"id": "emo-1"},
            "created_at": "2026-04-18T00:00:00Z",
            "input_feedback_comment": "Mashさん、こんにちは。Emlisです。今回は不安が近かったのですね。",
            "input_feedback_meta": {
                "version": "emlis_ai_v2",
                "kernel_version": "observation_kernel.v2",
                "tier": "plus",
                "capability": {
                    "history_mode": "extended",
                    "continuity_mode": "basic",
                    "style_mode": "adaptive",
                    "partner_mode": "on_basic",
                    "model_mode": "compact",
                    "interpretation_mode": "memory_aligned",
                },
                "used_sources": ["current_input", "history", "greeting_state", "derived_user_model"],
                "used_memory_layers": ["canonical_history", "derived_user_model", "side_state"],
                "reply_length_mode": "input_scaled",
                "evidence_count": 2,
                "evidence_by_line": {
                    "receive": [{"kind": "emotion", "ref_id": "emo-1", "weight": 1.0, "note": None}],
                },
                "rejected_candidate_count": 1,
                "fallback_used": False,
                "model_revision": "2026-04-18T00:00:00Z",
            },
        }

    monkeypatch.setattr(emotion_submit_module, "_resolve_user_id_from_token", fake_resolve_user_id_from_token)
    monkeypatch.setattr(emotion_submit_service_module, "persist_emotion_submission", fake_persist_emotion_submission)

    response = client.post(
        "/emotion/submit",
        headers={"Authorization": "Bearer test-token"},
        json={"emotions": ["不安"]},
    )

    assert response.status_code == 200, response.text
    assert response.headers["X-Cocolon-Contract-Id"] == "emotion.submit.v1"
    body = response.json()
    assert body["input_feedback"]["comment_text"] == "Mashさん、こんにちは。Emlisです。今回は不安が近かったのですね。"
    assert body["input_feedback"]["emlis_ai"]["version"] == "emlis_ai_v2"
    assert body["input_feedback"]["emlis_ai"]["kernel_version"] == "observation_kernel.v2"
    assert body["input_feedback"]["emlis_ai"]["capability"]["history_mode"] == "extended"
    assert body["input_feedback"]["emlis_ai"]["capability"]["model_mode"] == "compact"
    assert body["input_feedback"]["emlis_ai"]["capability"]["interpretation_mode"] == "memory_aligned"
    assert body["input_feedback"]["emlis_ai"]["used_memory_layers"] == ["canonical_history", "derived_user_model", "side_state"]
    assert body["input_feedback"]["emlis_ai"]["reply_length_mode"] == "input_scaled"
    assert body["input_feedback"]["emlis_ai"]["evidence_by_line"]["receive"][0]["ref_id"] == "emo-1"
    assert body["input_feedback"]["emlis_ai"]["rejected_candidate_count"] == 1
    assert body["input_feedback"]["emlis_ai"]["fallback_used"] is False


def test_subscription_bootstrap_contract_allows_plan_emlis_ai_meta(client, monkeypatch):
    import api_subscription as subscription_module

    async def fake_build_subscription_bootstrap(*, client_meta):
        assert client_meta.get("platform") == "ios"
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
                    "subtitle": "レポート閲覧 / Piece作成拡張",
                    "features": ["feature-a"],
                    "note_lines": ["note-a"],
                    "cta_label": "このプランを選ぶ",
                    "recommended": True,
                    "purchase_product_id": {"ios": "cocolon_plus_monthly", "android": "emlis"},
                    "recognized_product_ids": {"ios": ["cocolon_plus_monthly"], "android": ["emlis"]},
                    "purchase_base_plan_id": {"ios": None, "android": "plus"},
                    "recognized_base_plan_ids": {"ios": [], "android": ["plus"]},
                    "emlis_ai": {
                        "history_mode": "extended",
                        "continuity_mode": "basic",
                        "style_mode": "adaptive",
                        "partner_mode": "on_basic",
                        "model_mode": "compact",
                        "interpretation_mode": "memory_aligned",
                        "reply_length_mode": "input_scaled",
                        "marketing_lines": [
                            "EmlisAI：最近の流れを見ながら返してくれます",
                            "EmlisAI：入力履歴を踏まえた返答になります",
                        ],
                    },
                },
                "premium": {
                    "visible": True,
                    "purchasable": True,
                    "launch_stage": "live",
                    "title": "Premiumプラン",
                    "price_label": "月額980円",
                    "subtitle": "表示期間無制限 / 深いレポート / Piece作成無制限",
                    "features": ["feature-p"],
                    "note_lines": ["note-p"],
                    "cta_label": "このプランを選ぶ",
                    "recommended": False,
                    "purchase_product_id": {"ios": "cocolon_premium_monthly", "android": "emlis"},
                    "recognized_product_ids": {"ios": ["cocolon_premium_monthly"], "android": ["emlis"]},
                    "purchase_base_plan_id": {"ios": None, "android": "premium"},
                    "recognized_base_plan_ids": {"ios": [], "android": ["premium"]},
                    "emlis_ai": {
                        "history_mode": "full",
                        "continuity_mode": "advanced",
                        "style_mode": "personalized",
                        "partner_mode": "on_advanced",
                        "model_mode": "deep",
                        "interpretation_mode": "precision_aligned",
                        "reply_length_mode": "input_and_history_scaled",
                        "marketing_lines": [
                            "EmlisAI：あなたの流れに合わせて返し方まで変わります",
                            "EmlisAI：長い時間の変化や回復も踏まえて寄り添います",
                        ],
                    },
                },
            },
        }

    monkeypatch.setattr(subscription_module, "build_subscription_bootstrap", fake_build_subscription_bootstrap)

    response = client.get(
        "/subscription/bootstrap",
        headers={"X-Platform": "ios", "X-App-Version": "1.2.3", "X-App-Build": "123"},
    )

    assert response.status_code == 200, response.text
    assert response.headers["X-Cocolon-Contract-Id"] == "subscription.bootstrap.v1"
    body = response.json()
    assert body["plans"]["plus"]["emlis_ai"]["history_mode"] == "extended"
    assert body["plans"]["plus"]["emlis_ai"]["partner_mode"] == "on_basic"
    assert body["plans"]["plus"]["emlis_ai"]["model_mode"] == "compact"
    assert body["plans"]["plus"]["emlis_ai"]["interpretation_mode"] == "memory_aligned"
    assert body["plans"]["plus"]["emlis_ai"]["reply_length_mode"] == "input_scaled"
    assert body["plans"]["premium"]["emlis_ai"]["history_mode"] == "full"
    assert body["plans"]["premium"]["emlis_ai"]["partner_mode"] == "on_advanced"
    assert body["plans"]["premium"]["emlis_ai"]["model_mode"] == "deep"
    assert body["plans"]["premium"]["emlis_ai"]["interpretation_mode"] == "precision_aligned"
    assert body["plans"]["premium"]["emlis_ai"]["reply_length_mode"] == "input_and_history_scaled"



def test_emotion_reflection_publish_contract_keeps_additive_emlis_ai_meta(client, monkeypatch):
    import api_emotion_piece as emotion_piece_module

    async def fake_resolve_authenticated_user_id(*, authorization=None, legacy_user_id=None):
        return "user-123"

    class _FakeExecutionResult:
        data = {
            "preview_id": "preview-1",
            "reflection_id": "reflection-1",
            "emotion_id": "emo-2",
            "created_at": "2026-04-18T00:00:00Z",
            "question": "今日の気持ちは？",
            "reflection_text": "published reflection",
            "quota": {
                "status": "ok",
                "subscription_tier": "premium",
                "month_key": "2026-04",
                "publish_limit": None,
                "published_count": 4,
                "remaining_count": None,
                "can_publish": True,
            },
            "input_feedback": {
                "comment_text": "Mashさん、Emlisです。今回は不安が近かったのですね。",
                "emlis_ai": {
                    "version": "emlis_ai_v2",
                    "kernel_version": "observation_kernel.v2",
                    "tier": "premium",
                    "capability": {
                        "history_mode": "full",
                        "continuity_mode": "advanced",
                        "style_mode": "personalized",
                        "partner_mode": "on_advanced",
                        "model_mode": "deep",
                        "interpretation_mode": "precision_aligned",
                    },
                    "used_memory_layers": ["canonical_history", "derived_user_model", "side_state"],
                    "reply_length_mode": "input_and_history_scaled",
                    "evidence_count": 3,
                    "evidence_by_line": {
                        "receive": [{"kind": "emotion", "ref_id": "emo-2", "weight": 1.0, "note": None}],
                    },
                    "rejected_candidate_count": 1,
                    "fallback_used": False,
                    "model_revision": "2026-04-18T00:00:01Z",
                },
            },
        }

    class _FakeExecution:
        result = _FakeExecutionResult()

    async def fake_execute_home_command(command: str, *, payload=None, user_id: str, source: str):
        assert command == "emotion.reflection.publish"
        assert payload == {"preview_id": "preview-1"}
        assert user_id == "user-123"
        return _FakeExecution()

    monkeypatch.setattr(emotion_piece_module, "ResolveEmotionPieceAuthenticatedUserId", fake_resolve_authenticated_user_id)
    monkeypatch.setattr(emotion_piece_module, "ExecuteEmotionPieceHomeCommand", fake_execute_home_command)

    response = client.post(
        "/emotion/reflection/publish",
        headers={"Authorization": "Bearer test-token"},
        json={"preview_id": "preview-1"},
    )

    assert response.status_code == 200, response.text
    assert response.headers["X-Cocolon-Contract-Id"] == "emotion.reflection.publish.v1"
    assert response.headers["X-Cocolon-Deprecated"] == "true"
    assert response.headers["X-Cocolon-Replacement"] == "/emotion/piece/publish"
    body = response.json()
    assert body["input_feedback"]["comment_text"] == "Mashさん、Emlisです。今回は不安が近かったのですね。"
    assert body["input_feedback"]["emlis_ai"]["version"] == "emlis_ai_v2"
    assert body["input_feedback"]["emlis_ai"]["capability"]["model_mode"] == "deep"
    assert body["input_feedback"]["emlis_ai"]["used_memory_layers"] == ["canonical_history", "derived_user_model", "side_state"]
    assert body["input_feedback"]["emlis_ai"]["reply_length_mode"] == "input_and_history_scaled"
