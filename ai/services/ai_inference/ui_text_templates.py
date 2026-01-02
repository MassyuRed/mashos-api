# -*- coding: utf-8 -*-
"""ui_text_templates.py (Phase5.3)

目的
----
- DeepInsight の "質問の文体" をサーバ側テンプレIDで切り替えられるようにする。
- クライアントは単に API が返した questions[].text を表示するだけ。

設計
----
- 既存の deep_insight_questions.json の質問文（core_text）をベースに、
  サーバ側で "包む" / "言い換える" / "補助文を加える" などを行う。
- デフォルトは "passthrough"（= 何も変えない）にして互換性を守る。

注意
----
- これは LLM への instruction ではない（/mymodel/infer のガード対象外）。
- ここを更新すれば、アプリ更新無しで質問のトーンを変更できる。
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional


class UITextTemplateError(ValueError):
    """UI text template rendering error."""


@dataclass(frozen=True)
class UITextTemplateInfo:
    template_id: str
    description: str
    required_vars: List[str]
    optional_vars: List[str]


_UI_TEXT_TEMPLATES: Dict[str, UITextTemplateInfo] = {
    # --- DeepInsight question text (JA) ---
    "deep_insight_qtext_passthrough_v1": UITextTemplateInfo(
        template_id="deep_insight_qtext_passthrough_v1",
        description="DeepInsight question: no-op（元の質問文をそのまま返す）",
        required_vars=["core_text"],
        optional_vars=["structure_key", "hint", "strategy", "depth", "lang"],
    ),
    "deep_insight_qtext_ja_gentle_v1": UITextTemplateInfo(
        template_id="deep_insight_qtext_ja_gentle_v1",
        description="DeepInsight question: gentle tone（やわらかい言い回しに包む）",
        required_vars=["core_text"],
        optional_vars=["structure_key", "hint", "strategy", "depth", "lang"],
    ),
    "deep_insight_qtext_ja_direct_v1": UITextTemplateInfo(
        template_id="deep_insight_qtext_ja_direct_v1",
        description="DeepInsight question: direct tone（短く、要点を明確に）",
        required_vars=["core_text"],
        optional_vars=["structure_key", "hint", "strategy", "depth", "lang"],
    ),
}


def list_ui_text_templates() -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    for tid, info in sorted(_UI_TEXT_TEMPLATES.items(), key=lambda kv: kv[0]):
        out.append(
            {
                "template_id": info.template_id,
                "description": info.description,
                "required_vars": list(info.required_vars),
                "optional_vars": list(info.optional_vars),
            }
        )
    return out


def _require_str(vars_: Dict[str, Any], key: str) -> str:
    s = str(vars_.get(key) or "").strip()
    if not s:
        raise UITextTemplateError(f"ui template var '{key}' is required")
    return s


def render_ui_text_template(template_id: str, template_vars: Optional[Dict[str, Any]] = None) -> str:
    tid = str(template_id or "").strip()
    if not tid:
        raise UITextTemplateError("template_id is required")

    vars_ = template_vars or {}

    if tid == "deep_insight_qtext_passthrough_v1":
        return _require_str(vars_, "core_text")

    if tid == "deep_insight_qtext_ja_gentle_v1":
        core = _require_str(vars_, "core_text")
        # 例: やわらかく包む（接頭辞だけ付ける）
        return f"よければ：{core}" if core else core

    if tid == "deep_insight_qtext_ja_direct_v1":
        core = _require_str(vars_, "core_text")
        return core

    raise UITextTemplateError(f"Unknown ui text template_id: {tid}")


def render_deep_insight_question_text(
    template_id: str,
    *,
    core_text: str,
    structure_key: Optional[str] = None,
    hint: Optional[str] = None,
    strategy: Optional[str] = None,
    depth: Optional[int] = None,
    lang: str = "ja",
) -> str:
    """Convenience wrapper for DeepInsight question text."""

    vars_: Dict[str, Any] = {
        "core_text": str(core_text or "").strip(),
        "structure_key": (str(structure_key).strip() if structure_key else None),
        "hint": (str(hint).strip() if hint else None),
        "strategy": (str(strategy).strip() if strategy else None),
        "depth": int(depth) if isinstance(depth, int) else None,
        "lang": (str(lang or "ja").strip().lower() or "ja"),
    }
    try:
        out = render_ui_text_template(template_id, vars_)
    except Exception:
        out = vars_["core_text"]

    out = str(out or "").strip()
    return out if out else vars_["core_text"]
