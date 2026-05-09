# -*- coding: utf-8 -*-
from __future__ import annotations

"""User-facing address helpers for EmlisAI observation text.

This module keeps the visible speaking policy in one place: EmlisAI should
start by addressing the user by display name when available and should not rely
on second-person pronouns in the observation body.
"""

import re
from typing import Any, Optional

_HONORIFICS = ("さん", "様", "くん", "君", "ちゃん", "氏")
_SECOND_PERSON_PRONOUN_RE = re.compile(r"(あなたは|あなたの|あなたが|あなたに)")
_GENERIC_DISPLAY_NAMES = {"", "user", "ユーザー", "guest", "ゲスト", "none", "null"}


def normalize_display_name(value: Any) -> str:
    text = str(value or "").replace("\u3000", " ").strip()
    text = re.sub(r"\s+", " ", text)
    if text.lower() in _GENERIC_DISPLAY_NAMES:
        return ""
    return text[:40]


def display_name_call(value: Any) -> str:
    name = normalize_display_name(value)
    if not name:
        return ""
    if name.endswith(_HONORIFICS):
        return name
    return f"{name}さん"


def build_emlis_observation_greeting(*, display_name: Optional[Any], greeting_text: Any = "") -> str:
    name = display_name_call(display_name)
    greeting = str(greeting_text or "").strip()
    if name:
        if greeting.startswith(name):
            return greeting
        if greeting and greeting not in {"Emlisです。", "Emlis です。"}:
            return f"{name}、{greeting}"
        return f"{name}、Emlisです。"
    return greeting or "Emlisです。"


def has_second_person_pronoun(text: Any) -> bool:
    return bool(_SECOND_PERSON_PRONOUN_RE.search(str(text or "")))


def has_display_name_call(text: Any, display_name: Any) -> bool:
    call = display_name_call(display_name)
    if not call:
        return True
    return call in str(text or "")


__all__ = [
    "build_emlis_observation_greeting",
    "display_name_call",
    "has_display_name_call",
    "has_second_person_pronoun",
    "normalize_display_name",
]
