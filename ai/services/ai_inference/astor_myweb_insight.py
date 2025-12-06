# -*- coding: utf-8 -*-
"""
astor_myweb_insight.py

ASTOR MyWeb Insight v0.1

役割:
- ASTOR が蓄積した構造パターン (astor_structure_patterns.json) をもとに、
  特定ユーザーの「最近の構造傾向」を日本語テキストとしてレポートする。
- MyWeb 週報 / 月報 から呼び出すことを想定した純粋関数群。

前提:
- astor_patterns.StructurePatternsStore が JSON を管理している。
- JSON スキーマ例は astor_patterns.py の docstring を参照。
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional
import datetime as _dt
import json

try:
    # Cocolon 環境でのパス解決前提
    from astor_patterns import StructurePatternsStore
except ImportError:  # 単体テストなどでは直接 JSON を読むフォールバックにできる
    StructurePatternsStore = None  # type: ignore


@dataclass
class PeriodStructureStat:
    key: str
    count: int
    avg_score: float
    avg_intensity: float


def _load_user_structures(user_id: str) -> Dict[str, Any]:
    """
    StructurePatternsStore からユーザーごとの構造状態を取得する。
    Store が import できない場合は、直接 JSON ファイルを読むフォールバック。
    """
    if StructurePatternsStore is not None:
        store = StructurePatternsStore()
        user_entry = store.get_user_patterns(user_id)
        return user_entry.get("structures", {})

    # フォールバック: 直接 JSON を読む
    base = Path(__file__).resolve().parents[3]  # mashos-api/
    path = base / "ai" / "data" / "state" / "astor_structure_patterns.json"
    if not path.exists():
        return {}
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    users = raw.get("users") or {}
    entry = users.get(user_id) or {}
    return entry.get("structures", {})


def _filter_by_period(struct_entry: Dict[str, Any], period_days: int) -> PeriodStructureStat:
    """
    単一構造語について、指定日数の範囲に絞った統計値を計算する。
    """
    key = str(struct_entry.get("structure_key") or "")
    triggers = struct_entry.get("triggers") or []
    now = _dt.datetime.utcnow()
    cutoff = now - _dt.timedelta(days=period_days)

    cnt = 0
    sum_score = 0.0
    sum_intensity = 0.0

    for t in triggers:
        ts_str = t.get("ts")
        if not isinstance(ts_str, str):
            continue
        try:
            # 末尾が "Z" の ISO8601 を想定
            ts = _dt.datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
        except Exception:
            continue
        if ts < cutoff:
            continue

        try:
            score = float(t.get("score") or 0.0)
        except (TypeError, ValueError):
            score = 0.0
        try:
            intensity = float(t.get("intensity") or 0.0) if t.get("intensity") is not None else 0.0
        except (TypeError, ValueError):
            intensity = 0.0

        cnt += 1
        sum_score += score
        sum_intensity += intensity

    if cnt == 0:
        return PeriodStructureStat(key=key, count=0, avg_score=0.0, avg_intensity=0.0)

    return PeriodStructureStat(
        key=key,
        count=cnt,
        avg_score=sum_score / cnt,
        avg_intensity=sum_intensity / cnt,
    )


def generate_myweb_insight_text(user_id: str, period_days: int = 30, lang: str = "ja") -> str:
    """
    指定ユーザーについて、直近 period_days 日間の構造傾向を
    シンプルな日本語テキストとして生成する。

    MyWeb の週報 / 月報から呼び出し、LLM を使わずに
    「構造の観測結果」を返すことを目的とする。
    """
    if lang != "ja":
        # いったん日本語のみサポート
        lang = "ja"

    struct_map = _load_user_structures(user_id)
    if not struct_map:
        return "まだASTORが観測できている構造の傾向はありません。"

    stats: List[PeriodStructureStat] = []
    for struct_entry in struct_map.values():
        s = _filter_by_period(struct_entry, period_days=period_days)
        if s.count > 0:
            stats.append(s)

    if not stats:
        return f"直近{period_days}日間では、ASTORが特に強く反応している構造は見つかりませんでした。"

    # 出現回数でソートし、上位3件程度をレポート
    stats.sort(key=lambda s: (s.count, s.avg_score), reverse=True)
    top = stats[:3]

    lines: List[str] = []
    if period_days <= 8:
        lines.append(f"直近{period_days}日間の感情ログから、ASTORが観測している構造の傾向をまとめました。")
    elif period_days <= 35:
        lines.append(f"直近{period_days}日間（約1ヶ月）の感情ログから、ASTORが観測している構造の傾向をまとめました。")
    else:
        lines.append(f"直近{period_days}日間の感情ログから、ASTORが観測している構造の傾向をまとめました。")

    lines.append("")
    lines.append("よく現れている構造（上位）:")

    for s in top:
        # 強度のざっくりした言語化
        if s.avg_intensity >= 2.5:
            intensity_label = "かなり強く出やすい状態です。"
        elif s.avg_intensity >= 1.8:
            intensity_label = "ほどよく強く出やすい状態です。"
        else:
            intensity_label = "比較的やわらかく出ている状態です。"

        lines.append(f"- 「{s.key}」: 出現回数 {s.count} 回（平均強度 {s.avg_intensity:.1f}） … {intensity_label}")

    # 余裕があれば、全体傾向を一文でまとめる
    if len(top) == 1:
        lines.append("")
        lines.append(
            f"いまは「{top[0].key}」という構造が、とくにあなたの感情に影響しやすいタイミングかもしれません。"
        )
    elif len(top) >= 2:
        names = "」「".join([s.key for s in top])
        lines.append("")
        lines.append(
            f"いまは「{names}」といった構造たちが、感情の動きの背景に同時に関わっている可能性があります。"
        )

    lines.append("")
    lines.append("これは診断ではなく、「ASTORが感情の流れから観測した傾向」のメモとして受け取ってみてください。")

    return "\n".join(lines)
