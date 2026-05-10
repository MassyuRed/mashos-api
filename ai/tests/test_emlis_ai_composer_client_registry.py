from __future__ import annotations

import pytest

from emlis_ai_composer_client_registry import (
    default_limited_composer_enabled,
    resolve_default_emlis_composer_client,
)
from emlis_ai_limited_composer_client import CocolonLimitedComposerClient


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
async def test_render_keeps_fail_closed_when_feature_flag_disabled(monkeypatch):
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
    assert multi["composer_client_resolution"]["default_client_used"] is False
    assert multi["composer_client_resolution"]["source"] == "none"
    assert reply.comment_text == ""
    assert multi["composer_source"] == "unavailable"
