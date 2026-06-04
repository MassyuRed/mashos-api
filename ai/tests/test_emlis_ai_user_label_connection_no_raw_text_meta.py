# -*- coding: utf-8 -*-
from __future__ import annotations

import json
from collections.abc import Mapping
from typing import Any

from emlis_ai_capability import resolve_emlis_ai_capability_for_tier
from emlis_ai_types import SourceBundle
from emlis_ai_user_label_connection_material import (
    assert_user_label_connection_material_meta_contract,
    build_user_label_connection_material,
)

SECRET_CURRENT_MEMO = "PHASE2_SECRET_CURRENT_MEMO_SHOULD_NOT_LEAK"
SECRET_CURRENT_ACTION = "PHASE2_SECRET_CURRENT_ACTION_SHOULD_NOT_LEAK"
SECRET_HISTORY_MEMO = "PHASE2_SECRET_HISTORY_MEMO_SHOULD_NOT_LEAK"
SECRET_HISTORY_ACTION = "PHASE2_SECRET_HISTORY_ACTION_SHOULD_NOT_LEAK"
SECRET_COMMENT_BODY = "PHASE2_SECRET_COMMENT_BODY_SHOULD_NOT_LEAK"

FORBIDDEN_META_KEYS = {
    "raw_input",
    "rawInput",
    "raw_text",
    "rawText",
    "current_input",
    "currentInput",
    "history_input",
    "historyInput",
    "memo",
    "memo_action",
    "comment_text",
    "commentText",
    "comment_text_body",
    "commentTextBody",
    "candidate_body",
    "surface_body",
    "body",
    "text",
}


def _all_keys(value: Any) -> set[str]:
    keys: set[str] = set()
    if isinstance(value, Mapping):
        for key, child in value.items():
            keys.add(str(key))
            keys.update(_all_keys(child))
    elif isinstance(value, list):
        for child in value:
            keys.update(_all_keys(child))
    return keys


def test_phase2_material_meta_does_not_include_raw_current_history_or_comment_body() -> None:
    capability = resolve_emlis_ai_capability_for_tier("plus")
    current_input = {
        "id": "current-no-raw-001",
        "created_at": "2026-06-03T00:00:00+00:00",
        "category": ["仕事"],
        "emotion_details": [{"type": "不安", "strength": "strong"}],
        "memo_action": SECRET_CURRENT_ACTION,
        "memo": SECRET_CURRENT_MEMO,
        "comment_text": SECRET_COMMENT_BODY,
    }
    source_bundle = SourceBundle(
        user_id="phase2-no-raw-user",
        display_name="Mash",
        current_input=current_input,
        last_input={
            "id": "history-no-raw-last-001",
            "created_at": "2026-06-01T00:00:00+00:00",
            "category": ["仕事"],
            "emotion_details": [{"type": "不安", "strength": "medium"}],
            "memo_action": SECRET_HISTORY_ACTION,
            "memo": SECRET_HISTORY_MEMO,
            "comment_text": SECRET_COMMENT_BODY,
        },
    )

    material = build_user_label_connection_material(current_input, source_bundle=source_bundle, capability=capability)
    meta = material.as_meta()
    dumped = json.dumps(meta, ensure_ascii=False, sort_keys=True)

    assert FORBIDDEN_META_KEYS.isdisjoint(_all_keys(meta))
    for secret in (
        SECRET_CURRENT_MEMO,
        SECRET_CURRENT_ACTION,
        SECRET_HISTORY_MEMO,
        SECRET_HISTORY_ACTION,
        SECRET_COMMENT_BODY,
    ):
        assert secret not in dumped

    assert meta["raw_input_included"] is False
    assert meta["raw_text_included"] is False
    assert meta["history_raw_text_included"] is False
    assert meta["comment_text_body_included"] is False
    assert meta["candidate_body_included"] is False
    assert_user_label_connection_material_meta_contract(meta)
