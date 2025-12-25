# -*- coding: utf-8 -*-
"""mashlogic_qa_enhancer.py

Deep-mode enhancer for MyProfile Q&A responses.
----------------------------------------------

This module is intentionally *isolated* from Light/Standard.

Purpose (Step 4):
- Attach a Deep-only appendix to the end of a MyProfile Q&A response.
- Keep the enhancer import/call path separate so Light/Standard are unaffected.

Design notes:
- No external dependencies.
- Must fail gracefully (return original text on any error).
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional


def _safe_str(x: Any) -> str:
    try:
        s = str(x)
    except Exception:
        s = ""
    return s


def _truncate(s: str, n: int = 120) -> str:
    s = (s or "").replace("\r\n", "\n").replace("\r", "\n").strip()
    s = " ".join(s.split())  # normalize whitespace
    if len(s) <= n:
        return s
    return s[: n - 1] + "…"


def enhance_myprofile_qa_response(text: str, ctx: Optional[Dict[str, Any]] = None) -> str:
    """Append a Deep-only appendix to a Q&A response.

    Args:
        text: Base Q&A response (already formatted by compose_response).
        ctx: Context dictionary passed from compose_response.

    Returns:
        Enhanced response text (or original text if anything fails).
    """
    try:
        if not isinstance(text, str) or not text.strip():
            return text

        ctx = ctx or {}
        lang = _safe_str(ctx.get("lang") or "ja").strip().lower()
        # compose_response only calls this in ja/deep, but keep it safe.
        if lang not in ("ja", "japanese"):
            return text

        # Idempotency guard: don't append twice.
        if "【Deep追記" in text:
            return text

        mode = _safe_str(ctx.get("mode") or "deep").strip().lower()
        if mode != "deep":
            return text

        qtype = _safe_str(ctx.get("qtype") or "general").strip().lower()
        question = _safe_str(ctx.get("question") or "").strip()
        top_keys = ctx.get("top_keys") or []
        if not isinstance(top_keys, list):
            top_keys = []
        top_keys = [k for k in (_safe_str(k).strip() for k in top_keys) if k]

        deep_answers = ctx.get("deep_insight_answers") or []
        if not isinstance(deep_answers, list):
            deep_answers = []

        lines: List[str] = []
        lines.append("")
        lines.append("【Deep追記（MashLogic / 観測設計）】")

        if top_keys:
            lines.append(f"・核候補: 『{top_keys[0]}』が立ち上がる“条件”を1つだけ特定する")
            lines.append("  - 観測: 直前の『刺激（出来事）』『身体（感覚）』『解釈（頭の言葉）』を各1語でメモ")
            if len(top_keys) >= 2:
                lines.append(f"・干渉仮説: 『{top_keys[0]}』×『{top_keys[1]}』が重なった日に判断が硬くなる可能性")
                lines.append("  - 観測: 先に来たのはどっちか（順番だけ）")
        else:
            lines.append("・材料が少ないため、Deepは『観測設計』に寄せます。")
            lines.append("  - 観測: 揺れた瞬間の『刺激→解釈→身体』を1行で残す（1回だけでOK）")

        lines.append("")
        lines.append("・誤認チェック（ズレの定番）")
        lines.append("  - 未確定を“確定した悪い未来”として扱っていないか")
        lines.append("  - 他者/環境の要因を“自分の欠陥”に回収していないか")
        lines.append("  - 1回の失敗を“恒常的な自己定義”にしていないか")

        lines.append("")
        lines.append("・次の1アクション（最小）")
        if qtype == "decision":
            lines.append("  - 選択肢を2つに絞り、各々の『失うもの』を1語で書いて比較する")
        elif qtype == "action":
            lines.append("  - 今すぐ5分でできる“試行”を1つだけ決めて実行する（完璧は不要）")
        elif qtype == "why":
            lines.append("  - 原因探しの前に『守りたいもの』を1語で言語化する（ズレやすい軸）")
        else:
            lines.append("  - いま一番強い感情を1語で言い、その感情が守っているものを1語で書く")

        # Optional: reflect Deep Insight answers as short notes (if provided).
        samples: List[str] = []
        for a in deep_answers:
            s = _truncate(_safe_str(a), 120)
            if s:
                samples.append(s)
        if samples:
            lines.append("")
            lines.append("・Deep Insight メモ（参考・最大2）")
            for s in samples[:2]:
                lines.append(f"  - {s}")

        if question:
            lines.append("")
            lines.append("・この問いに対する“観測の焦点”")
            lines.append(f"  - 問い: {_truncate(question, 80)}")
            lines.append("  - 焦点: 『何が揃うと反応が出るか』だけを見る（正しさ判定は後回し）")

        # Assemble
        enhanced = text.rstrip() + "\n" + "\n".join(lines).rstrip()
        return enhanced.strip() + "\n"
    except Exception:
        return text
