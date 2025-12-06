# -*- coding: utf-8 -*-
"""
astor_mymodel_persona.py

ASTOR MyModel Persona Context v0.1

役割:
- ASTOR が蓄積している構造パターン (astor_structure_patterns.json) から、
  特定ユーザーの「いまの構造傾向」を取り出し、
  MyModel 用の文脈情報として使える形に整形する。
- ここでは LLM への直接プロンプト組み込みは行わず、
  「構造ベースの下地情報」を返す純粋関数群のみを提供する。
"""

from __future__ import annotations

from dataclasses import dataclass, asdict
from typing import Any, Dict, List, Optional
import datetime as _dt

try:
    from astor_patterns import StructurePatternsStore
except ImportError:
    StructurePatternsStore = None  # type: ignore


@dataclass
class PersonaStructureView:
    key: str
    count: int
    avg_score: float
    avg_intensity: float
    last_updated: Optional[str] = None


@dataclass
class AstorPersonaState:
    user_id: str
    top_structures: List[PersonaStructureView]
    generated_at: str


def _load_user_structures(user_id: str) -> Dict[str, Any]:
    """
    StructurePatternsStore からユーザーごとの構造状態を取得する。
    取得できない場合は空 dict を返す。
    """
    if StructurePatternsStore is None:
        return {}

    store = StructurePatternsStore()
    user_entry = store.get_user_patterns(user_id)
    return user_entry.get("structures", {})


def build_persona_state(user_id: str, limit: int = 5) -> AstorPersonaState:
    """
    MyModel 用に、指定ユーザーの構造傾向サマリを生成する。

    - limit: 返す構造数の上限（出現回数とスコアでソートした上位）
    """
    struct_map = _load_user_structures(user_id)
    now_iso = _dt.datetime.utcnow().replace(microsecond=0).isoformat() + "Z"

    if not struct_map:
        return AstorPersonaState(user_id=user_id, top_structures=[], generated_at=now_iso)

    views: List[PersonaStructureView] = []

    for entry in struct_map.values():
        key = str(entry.get("structure_key") or "")
        if not key:
            continue
        stats = entry.get("stats") or {}
        count = int(stats.get("count", 0))
        if count <= 0:
            continue
        avg_score = float(stats.get("avg_score", 0.0))
        avg_intensity = float(stats.get("avg_intensity", 0.0))
        last_updated = entry.get("last_updated")

        views.append(
            PersonaStructureView(
                key=key,
                count=count,
                avg_score=avg_score,
                avg_intensity=avg_intensity,
                last_updated=last_updated,
            )
        )

    if not views:
        return AstorPersonaState(user_id=user_id, top_structures=[], generated_at=now_iso)

    # 出現回数とスコアでソート
    views.sort(key=lambda v: (v.count, v.avg_score), reverse=True)
    top = views[: max(limit, 1)]

    return AstorPersonaState(user_id=user_id, top_structures=top, generated_at=now_iso)


def persona_state_to_brief_text(state: AstorPersonaState, lang: str = "ja") -> str:
    """
    AstorPersonaState を MyModel 用のシンプルなテキストに変換する。

    - このテキストは、「いま ASTOR が観測している構造の傾向」を
      MyModel の内部プロンプトに添えるための下地を想定している。
    """
    if lang != "ja":
        lang = "ja"

    if not state.top_structures:
        return "ASTORはまだ、あなたの感情から安定した構造の傾向をつかめていません。"

    lines: List[str] = []
    lines.append("ASTORが最近の感情ログから観測している構造の傾向:")

    for v in state.top_structures:
        if v.avg_intensity >= 2.5:
            intensity_label = "かなり強く出やすい構造"
        elif v.avg_intensity >= 1.8:
            intensity_label = "ほどよく強く出やすい構造"
        else:
            intensity_label = "比較的やわらかく出ている構造"

        lines.append(
            f"- 「{v.key}」: 出現回数 {v.count} 回 / 平均強度 {v.avg_intensity:.1f} （{intensity_label}）"
        )

    lines.append("")
    lines.append(
        "これは診断ではなく、「最近の感情の背景として現れやすい構造」をASTORがメモしているだけの情報です。"
    )
    return "\n".join(lines)


def build_persona_context_payload(user_id: str, limit: int = 5) -> Dict[str, Any]:
    """
    MyModel の /mymodel/infer などから利用しやすいように、
    構造サマリとテキストを1つの dict としてまとめて返す。
    """
    state = build_persona_state(user_id=user_id, limit=limit)
    text = persona_state_to_brief_text(state, lang="ja")
    return {
        "user_id": state.user_id,
        "generated_at": state.generated_at,
        "structures": [asdict(v) for v in state.top_structures],
        "brief_text": text,
    }
