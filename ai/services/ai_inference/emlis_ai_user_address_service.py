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
_ADDRESS_START = r"(?:^|(?<=[。．.!！?？]))[ \t　]*"
_ADDRESS_COMMA = r"[ \t　]*[、，,][ \t　]*"
_SELF_NAME = rf"Emlis(?:{'|'.join(_HONORIFICS)})?"


def _reply_address_pattern(bare_name: str = "") -> re.Pattern[str]:
    address = "あなた" + (f"|{re.escape(bare_name)}" if bare_name else "")
    return re.compile(
        rf"{_ADDRESS_START}(?P<address>{_SELF_NAME}|(?P<recipient>{address})){_ADDRESS_COMMA}",
        re.IGNORECASE | re.MULTILINE,
    )


_UNBOUND_REPLY_ADDRESS = _reply_address_pattern()


def normalize_display_name(value: Any) -> str:
    text = str(value or "").replace("\u3000", " ").strip()
    text = re.sub(r"\s+", " ", text)
    if text.lower() in _GENERIC_DISPLAY_NAMES:
        return ""
    return text[:40]


def display_name_call(value: Any, *, honorific: str | None = None) -> str:
    name = normalize_display_name(value)
    if not name:
        return ""
    if honorific is not None:
        return name if name.endswith(honorific) else f"{name}{honorific}"
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


def repair_emlis_reply_address(text: str, *, recipient_call: str = "", leading_only: bool = False) -> str:
    """Repair direct calls, keeping genuine first person, references and quotes."""
    if leading_only:
        # Legacy reads only project a suffix of the original body. A displayed
        # excerpt remains a valid contiguous correction target in storage.
        leading = _UNBOUND_REPLY_ADDRESS.match(text)
        return text[leading.end():] if leading else text

    bare_name = recipient_call.removesuffix("さん")
    pattern = _reply_address_pattern(bare_name) if bare_name else _UNBOUND_REPLY_ADDRESS
    if not pattern.search(text):
        return text

    from emlis_ai_grounded_observation_plan import _top_level_pattern_matches

    matches = _top_level_pattern_matches(text, pattern)
    if not matches:
        # A malformed bracket later in a body cannot conceal its unquoted opening.
        leading = pattern.match(text)
        if leading:
            matches = (leading,)
    end = 0
    parts = []
    for match in matches:
        start = match.start("address")
        parts.append(text[end:start])
        if recipient_call and match.group("recipient") and not re.fullmatch(_SELF_NAME, recipient_call, re.IGNORECASE):
            parts.append(f"{recipient_call}、")
        end = match.end()
    if not parts:
        return text
    parts.append(text[end:])
    return "".join(parts).strip()


__all__ = [
    "build_emlis_observation_greeting",
    "display_name_call",
    "has_display_name_call",
    "has_second_person_pronoun",
    "normalize_display_name",
    "repair_emlis_reply_address",
]
