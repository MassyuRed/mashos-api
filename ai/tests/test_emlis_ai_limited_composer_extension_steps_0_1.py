from __future__ import annotations

import pytest


SAMPLE_MEMO = """
ずっと家にいて、リラックスできて自分のことを優先して色々整えたりお家のことも出来るから嬉しいんだけど、ふっと気が抜けたときに現実と向き合うことがあるからその時にダメージでかい。
今の生活不便だな、と。
気をつけなきゃ行けないこと、全部無視して普通に生活したい。でもそうしたらもっと悪化する。
そんなの分かってる。たまに逃げ出したくなる。
"""

GATE_READER_FAIL_TEXT = "Mashさん、Emlisです。"


def _input(memo: str = SAMPLE_MEMO):
    return {
        "id": "limited-extension-step01-emotion",
        "created_at": "2026-05-15T00:00:00Z",
        "memo": memo,
        "memo_action": "",
        "emotion_details": [{"type": "自己理解", "strength": "medium"}],
        "emotions": ["自己理解"],
        "category": ["生活"],
    }


def _clear_limited_composer_env(monkeypatch: pytest.MonkeyPatch) -> None:
    for name in (
        "COCOLON_EMLIS_LIMITED_COMPOSER_ENABLED",
        "COCOLON_EMLIS_AI_LIMITED_COMPOSER_ENABLED",
        "EMLIS_AI_LIMITED_COMPOSER_ENABLED",
        "COCOLON_LIMITED_COMPOSER_ENABLED",
        "COCOLON_EMLIS_AI_DEFAULT_LIMITED_COMPOSER_ENABLED",
        "EMLIS_AI_DEFAULT_LIMITED_COMPOSER_ENABLED",
        "COCOLON_EMLIS_DEFAULT_COMPOSER",
        "COCOLON_EMLIS_AI_DEFAULT_COMPOSER",
        "EMLIS_AI_DEFAULT_COMPOSER",
        "COCOLON_EMLIS_LIMITED_COMPOSER_ROLLOUT_STAGE",
        "COCOLON_EMLIS_AI_LIMITED_COMPOSER_ROLLOUT_STAGE",
        "EMLIS_AI_LIMITED_COMPOSER_ROLLOUT_STAGE",
        "COCOLON_EMLIS_LIMITED_COMPOSER_ROLLOUT",
        "EMLIS_AI_LIMITED_COMPOSER_ROLLOUT",
        "COCOLON_EMLIS_LIMITED_COMPOSER_INTERNAL_USER_IDS",
        "COCOLON_EMLIS_AI_LIMITED_COMPOSER_INTERNAL_USER_IDS",
        "EMLIS_AI_LIMITED_COMPOSER_INTERNAL_USER_IDS",
    ):
        monkeypatch.delenv(name, raising=False)


class _UnavailableComposer:
    composer_model = "limited_extension_unavailable_fake.v1"

    def generate(self, payload):
        return {
            "response_schema_version": "emlis.composer.response.v1",
            "composer_source": "unavailable",
            "composer_model": self.composer_model,
            "generation_method": "test_composer",
            "generation_scope": "scoped_graph_only",
            "coverage_scope": "partial_observation",
            "fixed_string_renderer_used": False,
            "confidence": 0.0,
            "comment_text": "",
            "rejection_reasons": ["limited_composer_required_role_missing"],
        }


class _TextComposer:
    composer_model = "limited_extension_text_fake.v1"

    def __init__(self, text: str):
        self.text = text

    def generate(self, payload):
        return {
            "response_schema_version": "emlis.composer.response.v1",
            "composer_source": "ai_generated",
            "composer_model": self.composer_model,
            "generation_method": "test_composer",
            "generation_scope": "scoped_graph_only",
            "coverage_scope": "current_input_core",
            "fixed_string_renderer_used": False,
            "confidence": 0.91,
            "comment_text": self.text,
            "used_evidence_span_ids": [item["span_id"] for item in payload["evidence_spans"][:2]],
        }


def test_step01_registry_exposes_connection_visibility_for_disabled_default(monkeypatch):
    _clear_limited_composer_env(monkeypatch)
    from emlis_ai_composer_client_registry import resolve_default_emlis_composer_client

    client, meta = resolve_default_emlis_composer_client()

    assert client is None
    visibility = meta["connection_visibility"]
    assert visibility["version"] == "emlis.limited_composer_registry_connection_visibility.v1"
    assert visibility["baseline_stage"] == "limited_composer_extension"
    assert visibility["connection_status"] == "blocked_feature_flag"
    assert visibility["pre_connection_stop_stage"] == "flag"
    assert visibility["pre_connection_stop"] is True
    assert visibility["blocked_before_composer"] is True
    assert visibility["composer_connection_attempted"] is False
    assert visibility["composer_client_not_connected_class"] == "pre_connection"
    assert meta["canonical_composer_term"] == "限定Composer"
    assert meta["target_composer_term"] == "完全Composer初期版"


@pytest.mark.asyncio
async def test_step0_baseline_and_step1_visibility_mark_feature_flag_stop(monkeypatch):
    _clear_limited_composer_env(monkeypatch)
    from emlis_ai_reply_service import render_emlis_ai_reply

    reply = await render_emlis_ai_reply(
        user_id="limited-extension-step01-flag-user",
        subscription_tier="free",
        current_input=_input(),
        display_name="Mash",
        timezone_name="Asia/Tokyo",
    )

    summary = reply.meta["diagnostic_summary"]
    baseline = summary["limited_composer_extension_baseline"]
    assert baseline["version"] == "emlis.limited_composer_extension_baseline.v1"
    assert baseline["current_state"] == "limited_composer_basis_available_extension_in_progress"
    assert baseline["target_state"] == "limited_composer_extension_complete"
    assert baseline["canonical_terms"]["current_composer"] == "限定Composer"
    assert baseline["canonical_terms"]["next_goal"] == "完全Composer"
    assert baseline["db_api_rename_performed"] is False
    assert baseline["response_key_rename_performed"] is False
    assert baseline["display_contract_preserved"] is True

    visibility = summary["connection_visibility"]
    assert visibility == reply.meta["connection_visibility"]
    assert visibility == reply.meta["multi_perspective"]["connection_visibility"]
    assert visibility["version"] == "emlis.limited_composer_connection_visibility.v1"
    assert visibility["connection_status"] == "blocked_feature_flag"
    assert visibility["pre_connection_stop"] is True
    assert visibility["blocked_before_composer"] is True
    assert visibility["composer_connection_attempted"] is False
    assert visibility["composer_client_not_connected_present"] is True
    assert visibility["composer_client_not_connected_class"] == "pre_connection"
    assert visibility["actual_composer_rejection"] is False
    assert visibility["gate_rejection"] is False
    assert visibility["rejection_groups"]["composer_runtime"] == []
    assert visibility["primary_reason"] == "default_limited_composer_feature_disabled"
    assert reply.comment_text == ""


@pytest.mark.asyncio
async def test_step1_visibility_separates_connected_composer_rejection(monkeypatch):
    _clear_limited_composer_env(monkeypatch)
    from emlis_ai_reply_service import render_emlis_ai_reply

    reply = await render_emlis_ai_reply(
        user_id="limited-extension-step01-composer-user",
        subscription_tier="free",
        current_input=_input(),
        display_name="Mash",
        timezone_name="Asia/Tokyo",
        composer_client=_UnavailableComposer(),
    )

    visibility = reply.meta["diagnostic_summary"]["connection_visibility"]
    assert visibility["pre_connection_stop"] is False
    assert visibility["composer_connection_attempted"] is True
    assert visibility["composer_client_not_connected_present"] is False
    assert visibility["composer_client_not_connected_class"] == ""
    assert visibility["actual_composer_rejection"] is True
    assert visibility["gate_rejection"] is False
    assert visibility["primary_stage"] == "composer"
    assert visibility["primary_reason"] == "limited_composer_required_role_missing"
    assert visibility["rejection_groups"]["pre_connection"] == []
    assert visibility["rejection_groups"]["composer_runtime"] == ["limited_composer_required_role_missing"]
    assert reply.comment_text == ""


@pytest.mark.asyncio
async def test_step1_visibility_separates_gate_rejection_after_connection(monkeypatch):
    _clear_limited_composer_env(monkeypatch)
    from emlis_ai_reply_service import render_emlis_ai_reply

    reply = await render_emlis_ai_reply(
        user_id="limited-extension-step01-gate-user",
        subscription_tier="free",
        current_input=_input(),
        display_name="Mash",
        timezone_name="Asia/Tokyo",
        composer_client=_TextComposer(GATE_READER_FAIL_TEXT),
    )

    visibility = reply.meta["diagnostic_summary"]["connection_visibility"]
    assert visibility["pre_connection_stop"] is False
    assert visibility["composer_connection_attempted"] is True
    assert visibility["actual_composer_rejection"] is False
    assert visibility["gate_rejection"] is True
    assert visibility["primary_stage"] == "gate"
    assert visibility["primary_reason"] == "too_short_for_observation"
    assert visibility["rejection_groups"]["composer_runtime"] == []
    assert "too_short_for_observation" in visibility["rejection_groups"]["gate"]
    assert reply.comment_text == ""
