from __future__ import annotations

import pytest

from emlis_ai_composer_client_registry import (
    default_limited_composer_enabled,
    resolve_default_emlis_composer_client,
)
from emlis_ai_limited_composer_client import CocolonAPlanEquivalentComposerClient, CocolonLimitedComposerClient
from emlis_ai_complete_composer_client import CocolonCompleteComposerClient


SAMPLE_MEMO = """
ずっと家にいて、リラックスできて自分のことを優先して色々整えたりお家のことも出来るから嬉しいんだけど、ふっと気が抜けたときに現実と向き合うことがあるからその時にダメージでかい。
今の生活不便だな、と。
気をつけなきゃ行けないこと、全部無視して普通に生活したい。でもそうしたらもっと悪化する。
そんなの分かってる。たまに逃げ出したくなる。
"""


def _clear_flags(monkeypatch: pytest.MonkeyPatch) -> None:
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
    ):
        monkeypatch.delenv(name, raising=False)


def test_default_limited_composer_registry_is_disabled_by_default(monkeypatch):
    _clear_flags(monkeypatch)

    client, meta = resolve_default_emlis_composer_client()

    assert default_limited_composer_enabled() is False
    assert client is None
    assert meta["default_client_used"] is False
    assert meta["source"] == "none"
    assert "default_limited_composer_feature_disabled" in meta["rejection_reasons"]


def test_default_limited_composer_registry_resolves_when_feature_flag_enabled(monkeypatch):
    _clear_flags(monkeypatch)
    monkeypatch.setenv("COCOLON_EMLIS_LIMITED_COMPOSER_ENABLED", "true")

    client, meta = resolve_default_emlis_composer_client()

    assert default_limited_composer_enabled() is True
    assert isinstance(client, CocolonLimitedComposerClient)
    assert meta["default_client_used"] is True
    assert meta["source"] == "cocolon_limited_composer"
    assert meta["composer_model"] == "cocolon_limited_composer.v1"


def test_default_registry_blocks_complete_initial_alias_until_ap0_and_rollout_are_green(monkeypatch):
    _clear_flags(monkeypatch)
    monkeypatch.setenv("COCOLON_EMLIS_LIMITED_COMPOSER_ENABLED", "true")
    monkeypatch.setenv("COCOLON_EMLIS_DEFAULT_COMPOSER", "complete_initial")

    client, meta = resolve_default_emlis_composer_client(release_allowed=True)

    assert client is None
    assert meta["default_client_used"] is False
    assert meta["connection_status"] == "blocked_ap0"
    assert meta["pre_connection_stop_stage"] == "ap0"
    assert meta["target_composer_term"] == "完全Composer初期版"
    assert meta["feature_flag_state"]["requested_composer"] == "complete_initial"
    assert meta["feature_flag_state"]["canonical_requested_composer"] == "complete_composer_initial"
    assert meta["feature_flag_state"]["requested_composer_stage"] == "complete_composer_initial"
    assert meta["feature_flag_state"]["complete_initial_composer_requested"] is True
    assert meta["feature_flag_state"]["step10_complete_composer_client_requested"] is True
    assert meta["default_composer_resolution"]["connection_status"] == "blocked_ap0"


def test_default_registry_resolves_complete_initial_alias_when_ap0_and_rollout_are_green(monkeypatch):
    _clear_flags(monkeypatch)
    monkeypatch.setenv("COCOLON_EMLIS_LIMITED_COMPOSER_ENABLED", "true")
    monkeypatch.setenv("COCOLON_EMLIS_DEFAULT_COMPOSER", "complete_initial")

    client, meta = resolve_default_emlis_composer_client(
        release_allowed=True,
        ap0_decision={"can_proceed_to_a1": True},
    )

    assert isinstance(client, CocolonCompleteComposerClient)
    assert meta["default_client_used"] is True
    assert meta["source"] == "cocolon_complete_composer_initial"
    assert meta["composer_model"] == "cocolon_emlis_observation_composer.a1.v1"
    assert meta["target_composer_term"] == "完全Composer初期版"
    assert meta["feature_flag_state"]["requested_composer"] == "complete_initial"
    assert meta["feature_flag_state"]["canonical_requested_composer"] == "complete_composer_initial"
    assert meta["feature_flag_state"]["requested_composer_stage"] == "complete_composer_initial"
    assert meta["feature_flag_state"]["complete_initial_composer_requested"] is True
    assert meta["feature_flag_state"]["step10_complete_composer_client_requested"] is True
    assert meta["default_composer_resolution"]["connection_status"] == "default_client_resolved"


def test_default_limited_composer_registry_preserves_explicit_client(monkeypatch):
    _clear_flags(monkeypatch)
    explicit = CocolonLimitedComposerClient()

    client, meta = resolve_default_emlis_composer_client(composer_client=explicit)

    assert client is explicit
    assert meta["source"] == "provided"
    assert meta["explicit_client_provided"] is True
    assert meta["default_client_used"] is False


def test_default_limited_composer_registry_does_not_auto_connect_on_safety(monkeypatch):
    _clear_flags(monkeypatch)
    monkeypatch.setenv("COCOLON_EMLIS_LIMITED_COMPOSER_ENABLED", "true")

    client, meta = resolve_default_emlis_composer_client(safety_requires_block=True)

    assert client is None
    assert meta["safety_blocked"] is True
    assert meta["default_client_used"] is False
    assert "safety_boundary" in meta["rejection_reasons"]


@pytest.mark.asyncio
async def test_render_uses_default_limited_composer_when_feature_flag_enabled(monkeypatch):
    _clear_flags(monkeypatch)
    monkeypatch.setenv("COCOLON_EMLIS_LIMITED_COMPOSER_ENABLED", "true")
    from emlis_ai_reply_service import render_emlis_ai_reply

    reply = await render_emlis_ai_reply(
        user_id="phase3-user",
        subscription_tier="free",
        current_input={
            "id": "phase3-emotion",
            "created_at": "2026-05-10T00:00:00Z",
            "memo": SAMPLE_MEMO,
            "memo_action": "",
            "emotion_details": [{"type": "自己理解", "strength": "medium"}],
            "emotions": ["自己理解"],
            "category": ["生活"],
        },
        display_name="Mash",
        timezone_name="Asia/Tokyo",
    )

    multi = reply.meta.get("multi_perspective") if isinstance(reply.meta, dict) else {}
    client_meta = multi.get("composer_client_resolution") if isinstance(multi, dict) else {}
    candidate = multi.get("composer_candidate") if isinstance(multi, dict) else {}

    assert client_meta["default_client_used"] is True
    assert client_meta["source"] == "cocolon_limited_composer"
    assert candidate.get("composer_model") == "cocolon_limited_composer.v1"
    assert candidate.get("fixed_string_renderer_used") is False
    assert multi.get("composer_source") in {"ai_generated", "unavailable"}
    assert reply.meta["observation_status"] in {"passed", "rejected", "unavailable"}


@pytest.mark.asyncio
async def test_render_keeps_default_composer_connection_fail_closed_when_feature_flag_disabled(monkeypatch):
    _clear_flags(monkeypatch)
    from emlis_ai_reply_service import render_emlis_ai_reply

    reply = await render_emlis_ai_reply(
        user_id="phase3-disabled-user",
        subscription_tier="free",
        current_input={
            "id": "phase3-disabled-emotion",
            "created_at": "2026-05-10T00:00:00Z",
            "memo": SAMPLE_MEMO,
            "memo_action": "",
            "emotion_details": [{"type": "自己理解", "strength": "medium"}],
            "emotions": ["自己理解"],
            "category": ["生活"],
        },
        display_name="Mash",
        timezone_name="Asia/Tokyo",
    )

    multi = reply.meta["multi_perspective"]
    client_meta = multi["composer_client_resolution"]
    visibility = client_meta["connection_visibility"]

    # Composer itself must remain fail-closed when the feature flag is disabled.
    # A later bounded recovery path may still produce a safe observation, so this
    # contract must not require an empty comment_text as proof of Composer block.
    assert client_meta["default_client_used"] is False
    assert client_meta["source"] == "none"
    assert client_meta["connection_status"] == "blocked_feature_flag"
    assert client_meta["pre_connection_stop_stage"] == "flag"
    assert client_meta["composer_attempted"] is False
    assert "default_limited_composer_feature_disabled" in client_meta["rejection_reasons"]
    assert visibility["blocked_before_composer"] is True
    assert visibility["composer_generation_attempted"] is False
    assert multi["limited_composer_release"]["enabled"] is False
    assert multi["limited_composer_release"]["reason_code"] == "feature_flag_disabled"
    assert multi["composer_source"] in {"ai_generated", "unavailable"}
    assert reply.meta["observation_status"] in {"passed", "rejected", "unavailable", "safety_blocked"}


def test_step06_default_registry_marks_scope_block_before_composer(monkeypatch):
    _clear_flags(monkeypatch)
    monkeypatch.setenv("COCOLON_EMLIS_LIMITED_COMPOSER_ENABLED", "true")

    client, meta = resolve_default_emlis_composer_client(
        release_allowed=False,
        release_meta={
            "stage": "limited_cases",
            "enabled": False,
            "attempted": False,
            "reason_code": "scope_limited_case_not_eligible",
            "rejection_reasons": ["limited_composer_scope_not_allowed", "scope_out_of_scope"],
        },
    )

    assert client is None
    assert meta["default_limited_enabled"] is True
    assert meta["default_client_used"] is False
    assert meta["composer_attempted"] is False
    assert meta["connection_status"] == "blocked_scope"
    assert meta["pre_connection_stop_stage"] == "scope"
    assert meta["default_composer_resolution"]["release_allowed"] is False
    assert meta["default_composer_resolution"]["connection_status"] == "blocked_scope"
    assert "limited_composer_rollout_not_allowed" in meta["rejection_reasons"]
    assert "limited_composer_scope_not_allowed" in meta["rejection_reasons"]
