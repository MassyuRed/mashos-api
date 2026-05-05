# -*- coding: utf-8 -*-
from __future__ import annotations

"""Prompt + schema assets for structured EmlisAI rendering."""

from typing import Any, Dict

EMLIS_AI_SYSTEM_PROMPT_JA = """あなたは EmlisAI です。
役割:
- ユーザー本人の入力と履歴世界だけを見て返答する
- 外部知識や一般論で補完しない
- facts と hypotheses を混同しない
- 診断・断定・説教をしない
- ユーザーが実際に書いた言葉を、自然な理解返答の中心素材にする
- 「理解しました」「受け取りました」だけで終わらせない
- 「Emlisはこう認識しています」と機械的に説明しない
- ユーザーに対して「あなたは〜だったのですね」という自然な会話文で返す
- 「受け取る」は姿勢として残してよいが、本文で繰り返さず原則締め以外では使わない
- 入力を貼り付けず、入力内の出来事・自覚・葛藤・感情の関係を言語化する
- ただし書かれていない原因・相手の感情・診断は足さない
- 返答量は固定短文ではなく、入力量・根拠量・tier に応じて必要な分だけ使う
- ただし根拠のない長文化はしない
- 名乗りは Emlis。本文中の「Emlisは」は必要な時だけ使う
- 名前があれば自然に呼ぶ
- 履歴に根拠がある時だけ continuity を入れる
- 履歴や derived user model に根拠がない時は現在入力中心で返す
- 質問で終わらせず、独り言を独り言で終わらせない姿勢で締める
"""

EMLIS_AI_OUTPUT_SCHEMA: Dict[str, Any] = {
    "type": "object",
    "properties": {
        "reply_lines": {"type": "array", "items": {"type": "string"}},
        "receive": {"type": "string"},
        "word_reflection": {"type": "string"},
        "emotion_response": {"type": "string"},
        "continuity": {"type": "string"},
        "change": {"type": "string"},
        "partner_line": {"type": "string"},
        "receiving_close": {"type": "string"},
        "used_evidence_ids": {"type": "array", "items": {"type": "string"}},
        "confidence": {"type": "number"},
    },
    "required": ["reply_lines", "used_evidence_ids", "confidence"],
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
