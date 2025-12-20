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
import os

try:
    from astor_patterns import StructurePatternsStore
except ImportError:
    StructurePatternsStore = None  # type: ignore

try:
    from astor_deep_insight_store import DeepInsightAnswerStore
except ImportError:
    DeepInsightAnswerStore = None  # type: ignore


# ユーザーに見せるエンジン名（リネーム時にここだけ替えられるようにする）
ENGINE_DISPLAY_NAME = os.getenv("COCOLON_ENGINE_DISPLAY_NAME", "ASTOR")


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



def _load_deep_insight_answers(user_id: str, *, limit: int = 5, include_secret: bool = True) -> Dict[str, Any]:
    """Deep Insight の回答を取得する（MyProfile用）。

    - MyWeb には反映しないため、astor_structure_patterns.json とは別ストアから読む。
    - include_secret=False の場合は secret を除外した回答のみ返す（external用）。
    """
    if DeepInsightAnswerStore is None:
        return {"answers": [], "count": 0, "last_updated": None}

    try:
        store = DeepInsightAnswerStore()
        bundle = store.get_user_bundle(user_id)
        answers = store.get_user_answers(user_id, limit=limit, include_secret=include_secret)
        # count は include_secret に応じて再計算する（externalで secret を除外）
        if not include_secret:
            answers_all = store.get_user_answers(user_id, limit=9999, include_secret=False)
            count = len(answers_all)
        else:
            count = int(bundle.get("count") or 0)
        return {
            "answers": answers,
            "count": count,
            "last_updated": bundle.get("last_updated"),
        }
    except Exception:
        return {"answers": [], "count": 0, "last_updated": None}

def _compute_stats_from_triggers(triggers: List[Dict[str, Any]]) -> tuple[int, float, float, Optional[str]]:
    """triggers から count/avg_score/avg_intensity/last_updated を算出する。

    - 外部（公開）照会で secret を除外した後でも正しく算出できるよう、
      保存済みの stats に依存しない。
    - triggers のスキーマは astor_patterns.StructureTrigger を想定する。
    """

    count = 0
    score_sum = 0.0

    intensity_sum = 0.0
    intensity_n = 0

    last_updated: Optional[str] = None

    for t in triggers or []:
        if not isinstance(t, dict):
            continue
        count += 1

        try:
            score_sum += float(t.get("score", 0.0) or 0.0)
        except Exception:
            pass

        inten = t.get("intensity")
        if inten is not None:
            try:
                intensity_sum += float(inten)
                intensity_n += 1
            except Exception:
                pass

        ts = t.get("ts")
        if ts:
            ts_s = str(ts)
            if last_updated is None or ts_s > last_updated:
                last_updated = ts_s

    avg_score = (score_sum / count) if count > 0 else 0.0
    avg_intensity = (intensity_sum / intensity_n) if intensity_n > 0 else 0.0
    return count, avg_score, avg_intensity, last_updated


def build_persona_state(user_id: str, limit: int = 5, include_secret: bool = True) -> AstorPersonaState:
    """
    MyModel 用に、指定ユーザーの構造傾向サマリを生成する。

    - limit: 返す構造数の上限（出現回数とスコアでソートした上位）
    - include_secret: secret を含めるか（self: True / external: False）
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

        # NOTE:
        # - stats は「全ログ（secret含む）」前提で集計されている可能性がある。
        # - external のときは secret を除外して “公開用の構造傾向” を再計算する。
        triggers = entry.get("triggers") or []
        if not include_secret:
            triggers = [
                t
                for t in triggers
                if isinstance(t, dict) and not bool(t.get("is_secret", False))
            ]

        count, avg_score, avg_intensity, last_updated = _compute_stats_from_triggers(triggers)
        if count <= 0:
            continue

        # triggers から last_updated が取れない場合は、格納値をフォールバックとして使う。
        if not last_updated:
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


def persona_state_to_brief_text(
    state: AstorPersonaState,
    lang: str = "ja",
    include_secret: bool = True,
    deep_insight: Optional[Dict[str, Any]] = None,
) -> str:
    """
    AstorPersonaState を MyModel 用のシンプルなテキストに変換する。

    - このテキストは、「いま ASTOR が観測している構造の傾向」を
      MyModel の内部プロンプトに添えるための下地を想定している。
    - deep_insight は Deep Insight で得た回答（MyProfileのみ）を補助情報として差し込むための引数。
    """
    if lang != "ja":
        lang = "ja"

    if not state.top_structures:
        if include_secret:
            return f"{ENGINE_DISPLAY_NAME}はまだ、あなたの感情から安定した構造の傾向をつかめていません。"
        return f"{ENGINE_DISPLAY_NAME}はまだ、公開範囲の記録だけでは安定した構造の傾向をつかめていません。"

    lines: List[str] = []
    scope_txt = "最近の感情ログ" if include_secret else "公開範囲の感情ログ"
    lines.append(f"{ENGINE_DISPLAY_NAME}が{scope_txt}から観測している構造の傾向:")

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

    # Deep Insight の補助情報（MyProfileのみ）
    if deep_insight and isinstance(deep_insight, dict):
        entries = deep_insight.get("answers") or []
        if isinstance(entries, list) and entries:
            lines.append("")
            lines.append("Deep Insight で補足できたこと（最新）:")
            for a in entries[:3]:
                if not isinstance(a, dict):
                    continue
                q = (a.get("question_text") or "").strip() or (a.get("question_id") or "")
                ans = (a.get("text") or "").strip()
                if not ans:
                    continue
                if q:
                    lines.append(f"- Q: {q}")
                # 長すぎる回答は切る（UIの形を作る段階なので、過剰に長い文字列を避ける）
                if len(ans) > 120:
                    ans = ans[:120] + "…"
                lines.append(f"  A: {ans}")

    lines.append("")
    lines.append(
        f"これは診断ではなく、『最近の感情の背景として現れやすい構造』を{ENGINE_DISPLAY_NAME}がメモしているだけの情報です。"
    )
    return "\n".join(lines)




def build_persona_context_payload(user_id: str, limit: int = 5, include_secret: bool = True) -> Dict[str, Any]:
    """
    MyModel の /mymodel/infer などから利用しやすいように、
    構造サマリとテキストを1つの dict としてまとめて返す。
    """
    state = build_persona_state(user_id=user_id, limit=limit, include_secret=include_secret)
    deep_bundle = _load_deep_insight_answers(user_id=user_id, limit=5, include_secret=include_secret)
    text = persona_state_to_brief_text(state, lang="ja", include_secret=include_secret, deep_insight=deep_bundle)
    return {
        "user_id": state.user_id,
        "generated_at": state.generated_at,
        "data_scope": "self" if include_secret else "public",
        "include_secret": bool(include_secret),
        "structures": [asdict(v) for v in state.top_structures],
        "brief_text": text,
        "deep_insight": deep_bundle,
    }
