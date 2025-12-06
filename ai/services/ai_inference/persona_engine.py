# -*- coding: utf-8 -*-
"""
persona_engine.py

既存 app.py 内の compose_response / detect_lang / contains_date_like_adv 相当を
ASTOR から再利用しやすいように切り出すためのスケルトン。

※ 現時点では「ここに既存ロジックを移してね」というガイド用途。
"""

from __future__ import annotations
from typing import Any, Optional

# from .app import InputPayload  # 実際のパスに合わせて調整すること

def detect_lang(text: str) -> str:
  """
  既存 app.py の detect_lang と同じ実装をここに移動して使う想定。
  """
  for ch in text:
      if '\u3040' <= ch <= '\u30ff' or '\u4e00' <= ch <= '\u9fff':
          return 'ja'
  return 'en'


def contains_date_like_adv(text: str) -> bool:
    """
    日付・時系列に関する照会を弾くためのガード。
    既存 date_guard.py のロジックをここに集約する想定。
    """
    from guards.date_guard import contains_date_like_adv as _impl  # type: ignore
    return _impl(text)


def compose_persona_response(instr: str, payload: Optional[Any], target: str) -> str:
    """
    既存 compose_response() のボディをここに移す想定。

    - 一問一答だが会話的な口調
    - 数値や割合の列挙を避け、人格としての「私」が感じ取ったことを伝える
    - 診断・断定はせず、相対的・非断定的に述べる
    """
    # TODO: app.py の compose_response() 本体をここへコピーし、
    #       InputPayload 型もこちらで import / 定義する。
    raise NotImplementedError("compose_persona_response is not wired yet")
