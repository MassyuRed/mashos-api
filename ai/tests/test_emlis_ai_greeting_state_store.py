from __future__ import annotations

import asyncio
from datetime import datetime, timezone


def test_greeting_state_reuses_short_greeting_in_same_slot(monkeypatch):
    import emlis_ai_greeting_state_store as greeting_module

    greeting_module._MEMORY_STATE.clear()
    monkeypatch.setattr(greeting_module, "sb_get", None)
    monkeypatch.setattr(greeting_module, "sb_patch", None)
    monkeypatch.setattr(greeting_module, "sb_post", None)

    first = asyncio.run(
        greeting_module.decide_greeting_for_user(
            user_id="user-1",
            display_name="Mash",
            timezone_name="Asia/Tokyo",
            now_utc=datetime(2026, 4, 18, 0, 0, tzinfo=timezone.utc),
        )
    )
    second = asyncio.run(
        greeting_module.decide_greeting_for_user(
            user_id="user-1",
            display_name="Mash",
            timezone_name="Asia/Tokyo",
            now_utc=datetime(2026, 4, 18, 0, 10, tzinfo=timezone.utc),
        )
    )

    assert first.first_in_slot is True
    assert first.greeting_text == "Mashさん、おはようございます。Emlisです。"
    assert second.first_in_slot is False
    assert second.greeting_text == "Emlisです。"


def test_greeting_state_re_greets_when_slot_changes(monkeypatch):
    import emlis_ai_greeting_state_store as greeting_module

    greeting_module._MEMORY_STATE.clear()
    monkeypatch.setattr(greeting_module, "sb_get", None)
    monkeypatch.setattr(greeting_module, "sb_patch", None)
    monkeypatch.setattr(greeting_module, "sb_post", None)

    morning = asyncio.run(
        greeting_module.decide_greeting_for_user(
            user_id="user-1",
            display_name="Mash",
            timezone_name="Asia/Tokyo",
            now_utc=datetime(2026, 4, 18, 0, 0, tzinfo=timezone.utc),
        )
    )
    day = asyncio.run(
        greeting_module.decide_greeting_for_user(
            user_id="user-1",
            display_name="Mash",
            timezone_name="Asia/Tokyo",
            now_utc=datetime(2026, 4, 18, 4, 0, tzinfo=timezone.utc),
        )
    )

    assert morning.slot_name == "morning"
    assert day.slot_name == "day"
    assert day.first_in_slot is True
    assert day.greeting_text == "Mashさん、こんにちは。Emlisです。"
