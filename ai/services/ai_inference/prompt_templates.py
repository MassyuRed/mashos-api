# -*- coding: utf-8 -*-
"""Server-side prompt templates registry (Phase5)

目的
----
- アプリ（JS）側に埋め込まれている「プロンプト/テンプレ/文面」を MashOS 側へ集約する。
- クライアントは template_id と template_vars を送るだけでよくなり、
  文章調整はサーバ側だけで更新できる。

使い方（例: /mymodel/infer）
---------------------------
POST /mymodel/infer
{
  "template_id": "myprofile_qna_v1",
  "template_vars": { "question": "なんで不安になるの？" },
  "target": "self",
  "report_mode": "standard"
}

注意
----
- /mymodel/infer は日付関連ワードをブロックするため、
  ここで生成するテンプレには「いつ/今日/明日/先週/来月」などを入れないこと。
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional


class TemplateError(ValueError):
    """Template rendering error (bad vars / unknown template)."""


@dataclass(frozen=True)
class TemplateInfo:
    template_id: str
    description: str
    required_vars: List[str]
    optional_vars: List[str]


_TEMPLATES: Dict[str, TemplateInfo] = {
    "myprofile_qna_v1": TemplateInfo(
        template_id="myprofile_qna_v1",
        description="MyProfile 一問一答（質問を構造化して送る）",
        required_vars=["question"],
        optional_vars=[],
    ),
    "myprofile_monthly_report_v1": TemplateInfo(
        template_id="myprofile_monthly_report_v1",
        description="MyProfile 月次自己構造分析レポート（互換用・検出マーカー付き）",
        required_vars=[],
        optional_vars=["range_label", "prev_report_text"],
    ),
}


def list_prompt_templates() -> List[Dict[str, Any]]:
    """Return template metadata list for debug/inspection."""
    out: List[Dict[str, Any]] = []
    for tid, info in sorted(_TEMPLATES.items(), key=lambda kv: kv[0]):
        out.append(
            {
                "template_id": info.template_id,
                "description": info.description,
                "required_vars": list(info.required_vars),
                "optional_vars": list(info.optional_vars),
            }
        )
    return out


def render_prompt_template(template_id: str, template_vars: Optional[Dict[str, Any]] = None, *, target: str = "self") -> str:
    """Render a prompt template into a concrete instruction string.

    Parameters
    ----------
    template_id:
        ID string (e.g., myprofile_qna_v1)
    template_vars:
        Variables dict. Missing required vars raise TemplateError.
    target:
        self | external (used only for a small label in some templates)
    """
    tid = str(template_id or "").strip()
    if not tid:
        raise TemplateError("template_id is required")

    vars_ = template_vars or {}

    if tid == "myprofile_qna_v1":
        return _tpl_myprofile_qna_v1(vars_, target=target)

    if tid == "myprofile_monthly_report_v1":
        return _tpl_myprofile_monthly_report_v1(vars_, target=target)

    raise TemplateError(f"Unknown template_id: {tid}")


def _tpl_myprofile_qna_v1(vars_: Dict[str, Any], *, target: str) -> str:
    q = str(vars_.get("question") or "").strip()
    if not q:
        raise TemplateError("template_vars.question is required")

    # NOTE: /mymodel/infer 側で contains_date_like を弾くので、日付関連語は書かない。
    lines = []
    lines.append("【MyProfile 一問一答】")
    lines.append(f"【対象】{str(target or 'self')}")
    lines.append("【質問】")
    lines.append(q)
    return "\n".join(lines).strip()


def _tpl_myprofile_monthly_report_v1(vars_: Dict[str, Any], *, target: str) -> str:
    # 互換用。/mymodel/infer が is_myprofile_monthly_report_instruction() で検出するための
    # マーカー文字列を含める。実際の生成は astor_myprofile_report に移譲される。
    range_label = str(vars_.get("range_label") or "").strip()
    prev = str(vars_.get("prev_report_text") or "").strip()
    has_prev = bool(prev)

    # range_label は UI 表示用の文字列なので、ここでは必須にしない。
    # ただし入っている場合はタイトル用に先頭に置く。
    if not range_label:
        range_label = "（期間ラベル未指定）"

    lines: List[str] = []
    lines.append("【自己構造分析レポート（月次）】")
    lines.append("")
    lines.append(f"対象: {str(target or 'self')}")
    lines.append(f"期間: {range_label}")
    lines.append("")
    lines.append("【要点（答え）】")
    lines.append("・（この期間の自己モデルの核を1行）")
    lines.append("・（崩れやすい引き金/条件を1行）")
    lines.append("・（安定しやすい条件/整え方を1行）")
    lines.append("")
    lines.append("1. いまの自己モデル（仮説・1〜4行）")
    lines.append("2. 主要な反応パターン（刺激→認知→感情→行動）")
    lines.append("3. 安定条件 / 崩れ条件（それぞれ箇条書き）")
    lines.append("4. 思考のクセ・判断のクセ（あれば）")
    lines.append("5. 領域別メモ（仕事/対人/孤独/挑戦/評価など、見えている範囲で）")
    lines.append("6. 次の観測ポイント（3つ。行動に落ちる形で）")

    if has_prev:
        lines.append("7. 前回との差分（変化点 / 更新点 / 揺れ方の違い）")
        lines.append("8. 感情構造との接続（MyWebに譲る前提で、短く1〜2行）")
        lines.append("")
        lines.append("前回レポート（参考。コピーせず、差分観測の材料として扱ってください）：")
        lines.append("<<PREVIOUS_REPORT_START>>")
        # 長すぎるとリクエストが重くなるので上限
        lines.append(prev[:8000])
        lines.append("<<PREVIOUS_REPORT_END>>")
    else:
        lines.append("7. 比較メモ（前回レポートがまだ無い場合は1〜2行）")
        lines.append("8. 感情構造との接続（MyWebに譲る前提で、短く1〜2行）")

    lines.append("")
    lines.append("【追加の注意】")
    lines.append("・『あなたは〜な人』のような人格の断定表現は禁止。")
    lines.append("・専門用語は避け、アプリのユーザーが読んで理解できる言葉で。")
    lines.append("・一貫して『観測→仮説』の順で書く。")

    return "\n".join(lines).strip()
