# -*- coding: utf-8 -*-
from __future__ import annotations

"""Prompt + schema assets for structured EmlisAI rendering."""

from typing import Any, Dict

EMLIS_AI_SYSTEM_PROMPT_JA = """あなたは EmlisAI です。
役割:
- ユーザー本人の履歴世界だけを見て返答する
- 外部知識や一般論で補完しない
- facts と hypotheses を混同しない
- 診断・断定・説教をしない
- 日本語で短く、やわらかく返す
- 一人称は必ず Emlis
- 名前があれば自然に呼ぶ
- 履歴に根拠がある時だけ continuity を入れる
- 履歴に根拠がない時は現在入力中心で返す
"""

EMLIS_AI_OUTPUT_SCHEMA: Dict[str, Any] = {
    "type": "object",
    "properties": {
        "receive": {"type": "string"},
        "continuity": {"type": "string"},
        "change": {"type": "string"},
        "partner_line": {"type": "string"},
        "used_evidence_ids": {"type": "array", "items": {"type": "string"}},
        "confidence": {"type": "number"},
    },
    "required": ["receive", "continuity", "change", "partner_line", "used_evidence_ids", "confidence"],
}


def build_emlis_ai_prompt_payload(*, source_bundle: Dict[str, Any], world_model: Dict[str, Any], reply_policy: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "system_prompt": EMLIS_AI_SYSTEM_PROMPT_JA,
        "schema": EMLIS_AI_OUTPUT_SCHEMA,
        "input": {
            "source_bundle": source_bundle,
            "world_model": world_model,
            "reply_policy": reply_policy,
        },
    }
