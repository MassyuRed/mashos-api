# -*- coding: utf-8 -*-
"""mashlogic_profile_enhancer.py

Deep-mode enhancer for MyProfile monthly reports.
-------------------------------------------------

This module is intentionally *isolated* from Light/Standard.

Current status (Step 3):
- Provides a safe placeholder enhancer that adds a Deep-only appendix.
- No external dependencies.

Future (spec):
- Replace/extend the appendix generation with MashLogic:
  definition / interference / misrecognition / environment-dependence,
  using Mash構造辞書候補などを材料に推論段を上位化する。
"""

from __future__ import annotations

from typing import Any, Dict, List


def enhance_myprofile_monthly_report(lines: List[str], context: Dict[str, Any]) -> List[str]:
    """Return enhanced report lines for Deep mode.

    Parameters
    ----------
    lines:
        The already-built monthly report lines.
    context:
        A light context payload (user_id, top_keys, top_views, etc.).

    Notes
    -----
    - Must never raise (Deep mode should degrade gracefully).
    - Must not mutate the input list.
    """

    try:
        out = list(lines or [])
        top_keys = list(context.get("top_keys") or [])
        mode = str(context.get("mode") or "deep")

        # Insert right before "8. 感情構造との接続" if present.
        insert_at = len(out)
        for i, l in enumerate(out):
            if str(l).startswith("8. 感情構造との接続"):
                insert_at = i
                break

        deep_lines: List[str] = []
        deep_lines.append("")
        deep_lines.append("【Deepモード追記】")
        deep_lines.append("※ここからは“構造の定義/干渉/誤認”の観点で、仮説をもう1段だけ深掘りします。")
        deep_lines.append("※断定ではなく“観測→仮説→次の観測”の循環を強制するための追記です。")
        deep_lines.append("")

        if top_keys:
            deep_lines.append(f"・核候補: 『{top_keys[0]}』")
            deep_lines.append("  - チェック: これは“人格”ではなく、“条件が揃うと出る反応”として扱えているか")
            deep_lines.append("  - 次の観測: 何が揃うと立ち上がる？（睡眠/空腹/期限/評価/未確定 など）")
            if len(top_keys) >= 2:
                deep_lines.append(f"・干渉仮説: 『{top_keys[0]}』が強い日に『{top_keys[1]}』が重なり、判断が硬くなる可能性")
                deep_lines.append("  - 次の観測: “重なった順番”を1行だけ記録（先にどっちが来た？）")
        else:
            deep_lines.append("・材料が少ないため、Deep追記は“観測設計”に寄せます。")
            deep_lines.append("  - 次の観測: 揺れた時に『刺激→解釈→身体』を1行で残す（最低1回）")

        deep_lines.append("")
        deep_lines.append("・誤認チェック（よく起きるズレ）")
        deep_lines.append("  - 相手/環境の問題を“自分の欠陥”に回収していないか")
        deep_lines.append("  - 未確定を“確定した悪い未来”として扱っていないか")
        deep_lines.append("  - 1回の失敗を“恒常的な自己定義”にしていないか")

        deep_lines.append("")
        deep_lines.append("・Deepの使い方")
        deep_lines.append("  - ‘正しい答え’を得るためではなく、‘観測の角度’を増やすために使う")
        deep_lines.append("  - 次の月は、上の観測を1つだけ継続して“条件”を特定する")

        # Re-assemble
        return out[:insert_at] + deep_lines + out[insert_at:]
    except Exception:
        # Deep mode must degrade gracefully.
        return list(lines or [])
