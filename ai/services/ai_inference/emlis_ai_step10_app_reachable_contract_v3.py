# -*- coding: utf-8 -*-
from __future__ import annotations

"""Frozen App-Reachable input adapter for Step 10 runtime evidence.

The corpus registry remains evaluation tooling.  This production-side owner
contains only the input projection that the current RN submit path can reach,
so runtime evidence never imports a test helper or trusts backend-only shapes.
"""

from typing import Any, Mapping

from emlis_ai_nls_v3_artifact_contract import artifact_sha256


APP_REACHABLE_INPUT_POLICY = {
    "schema_version": "cocolon.emlis.nls_v3.app_reachable_input_policy.v1",
    "authority": "step1_frozen_current_rn_production_contract",
    "step1_input_contract_sha256": (
        "d577ac80457e25389c0bac351139b2c80a9a506f225023fb7928a1b9068d53c6"
    ),
    "text_presence": "ecmascript_string_trim_thought_or_action_nonempty",
    "text_length_limit": None,
    "emotion_types": ["喜び", "悲しみ", "怒り", "不安", "平穏", "自己理解"],
    "strength_types": ["weak", "medium", "strong"],
    "emotion_unique": True,
    "self_insight_exclusive": True,
    "self_insight_strength": "medium",
    "category_types": [
        "生活",
        "仕事",
        "趣味",
        "人間関係",
        "恋愛",
        "健康",
        "学習",
        "価値観",
        "人生",
    ],
    "category_unique": True,
    "backend_permissiveness_is_app_reachable_authority": False,
}
FROZEN_APP_REACHABLE_INPUT_POLICY_SHA256 = (
    "cca85dafcf338637e2338e47306ce4b4c9c7ad18c98ae1bd89935313cc8c7d39"
)

_INPUT_KEYS = frozenset(
    {"thought_text", "action_text", "emotions", "categories"}
)
_EMOTION_KEYS = frozenset({"type", "strength"})
_EMOTION_TYPES = tuple(APP_REACHABLE_INPUT_POLICY["emotion_types"])
_STRENGTH_TYPES = tuple(APP_REACHABLE_INPUT_POLICY["strength_types"])
_CATEGORY_TYPES = tuple(APP_REACHABLE_INPUT_POLICY["category_types"])
_ECMASCRIPT_TRIM_CODEPOINTS = frozenset(
    {
        0x0009,
        0x000A,
        0x000B,
        0x000C,
        0x000D,
        0x0020,
        0x00A0,
        0x1680,
        0x2000,
        0x2001,
        0x2002,
        0x2003,
        0x2004,
        0x2005,
        0x2006,
        0x2007,
        0x2008,
        0x2009,
        0x200A,
        0x2028,
        0x2029,
        0x202F,
        0x205F,
        0x3000,
        0xFEFF,
    }
)


def _issue(path: str, code: str) -> str:
    return f"{path}:{code}"


def _exact_keys(value: Any, expected: frozenset[str]) -> bool:
    return isinstance(value, Mapping) and set(value) == expected


def _valid_scalar_text(value: Any) -> bool:
    return isinstance(value, str) and not any(
        0xD800 <= ord(character) <= 0xDFFF for character in value
    )


def ecmascript_trim(value: str) -> str:
    if type(value) is not str:
        raise TypeError("app_reachable_text_required")
    start = 0
    end = len(value)
    while start < end and ord(value[start]) in _ECMASCRIPT_TRIM_CODEPOINTS:
        start += 1
    while end > start and ord(value[end - 1]) in _ECMASCRIPT_TRIM_CODEPOINTS:
        end -= 1
    return value[start:end]


def validate_app_reachable_input_policy() -> tuple[str, ...]:
    try:
        current = artifact_sha256(APP_REACHABLE_INPUT_POLICY)
    except (RecursionError, TypeError, ValueError, UnicodeError):
        return ("app_reachable_input_policy_not_canonical",)
    return (
        ()
        if current == FROZEN_APP_REACHABLE_INPUT_POLICY_SHA256
        else ("app_reachable_input_policy_hash_drift",)
    )


def validate_app_reachable_input(value: Any) -> tuple[str, ...]:
    policy_issues = validate_app_reachable_input_policy()
    if policy_issues:
        return (_issue("input.policy", policy_issues[0]),)
    if not _exact_keys(value, _INPUT_KEYS):
        return (_issue("input", "keyset_mismatch"),)

    issues: list[str] = []
    thought = value.get("thought_text")
    action = value.get("action_text")
    if not _valid_scalar_text(thought):
        issues.append(_issue("input.thought_text", "string_or_unicode_invalid"))
    if not _valid_scalar_text(action):
        issues.append(_issue("input.action_text", "string_or_unicode_invalid"))
    if _valid_scalar_text(thought) and _valid_scalar_text(action):
        if not ecmascript_trim(thought) and not ecmascript_trim(action):
            issues.append(
                _issue("input", "thought_action_both_empty_after_js_trim")
            )

    emotions = value.get("emotions")
    emotion_types: list[str] = []
    if not isinstance(emotions, list):
        issues.append(_issue("input.emotions", "array_required"))
    elif not emotions:
        issues.append(_issue("input.emotions", "minimum_one_required"))
    else:
        for index, emotion in enumerate(emotions):
            path = f"input.emotions[{index}]"
            if not _exact_keys(emotion, _EMOTION_KEYS):
                issues.append(_issue(path, "keyset_mismatch"))
                continue
            emotion_type = emotion.get("type")
            strength = emotion.get("strength")
            if not _valid_scalar_text(emotion_type):
                issues.append(_issue(f"{path}.type", "string_or_unicode_invalid"))
            elif emotion_type not in _EMOTION_TYPES:
                issues.append(_issue(f"{path}.type", "unknown_emotion_type"))
            else:
                emotion_types.append(emotion_type)
            if not _valid_scalar_text(strength):
                issues.append(
                    _issue(f"{path}.strength", "string_or_unicode_invalid")
                )
            elif strength not in _STRENGTH_TYPES:
                issues.append(_issue(f"{path}.strength", "unknown_strength"))
        if len(emotion_types) != len(set(emotion_types)):
            issues.append(_issue("input.emotions", "duplicate_emotion_type"))
        if "自己理解" in emotion_types:
            if len(emotions) != 1:
                issues.append(
                    _issue("input.emotions", "self_insight_must_be_exclusive")
                )
            elif emotions[0].get("strength") != "medium":
                issues.append(
                    _issue(
                        "input.emotions[0].strength",
                        "self_insight_requires_medium",
                    )
                )

    categories = value.get("categories")
    valid_categories: list[str] = []
    if not isinstance(categories, list):
        issues.append(_issue("input.categories", "array_required"))
    elif not categories:
        issues.append(_issue("input.categories", "minimum_one_required"))
    else:
        for index, category in enumerate(categories):
            path = f"input.categories[{index}]"
            if not _valid_scalar_text(category):
                issues.append(_issue(path, "string_or_unicode_invalid"))
            elif category not in _CATEGORY_TYPES:
                issues.append(_issue(path, "unknown_category"))
            else:
                valid_categories.append(category)
        if len(valid_categories) != len(set(valid_categories)):
            issues.append(_issue("input.categories", "duplicate_category"))
    return tuple(dict.fromkeys(issues))


def project_app_reachable_input(value: Mapping[str, Any]) -> dict[str, Any]:
    issues = validate_app_reachable_input(value)
    if issues:
        raise ValueError("app_reachable_input_invalid:" + issues[0])
    return {
        "thought_text": str(value["thought_text"]),
        "action_text": str(value["action_text"]),
        "emotions": [
            {"type": str(item["type"]), "strength": str(item["strength"])}
            for item in value["emotions"]
        ],
        "categories": [str(item) for item in value["categories"]],
    }


__all__ = [
    "APP_REACHABLE_INPUT_POLICY",
    "FROZEN_APP_REACHABLE_INPUT_POLICY_SHA256",
    "ecmascript_trim",
    "project_app_reachable_input",
    "validate_app_reachable_input",
    "validate_app_reachable_input_policy",
]
