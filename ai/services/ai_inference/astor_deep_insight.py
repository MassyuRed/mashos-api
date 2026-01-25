# -*- coding: utf-8 -*-
"""astor_deep_insight.py

Deep Insight (質問生成) v0.1

目的:
- ユーザーの感情ログ（観測）が
  - 豊富な場合: 既に観測できている領域の「深掘り」を行う
  - 少ない場合: まだ未開拓の領域を「開拓」する

v0.1 の方針:
- まずは「画面と出力の形」を作ることを優先。
- 実際の問いの文章や、選定アルゴリズムは後から差し替え可能にする。
  - テンプレートJSON（ai/data/config/deep_insight_questions.json）を参照
  - max_questions / max_depth / tier などのパラメータを受け取れる

重要:
- Deep Insight の回答は **MyProfile にのみ活用**し、MyWeb（週報/月報）には反映しない。
  → そのため、本モジュールは「質問生成」のみを担当し、
     astor_structure_patterns.json（MyWeb参照）を更新しない。

更新: 2025-12
- "別の問いを受け取る" で同じ問いが続かないように、
  提示済み（served）履歴を見てローテーション/シャッフルするロジックを追加。
"""

from __future__ import annotations

from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Set

import datetime as _dt
import hashlib
import json
import os
import random
import re
import time

try:
    from astor_patterns import StructurePatternsStore
except ImportError:
    StructurePatternsStore = None  # type: ignore

from astor_deep_insight_question_store import DeepInsightServedStore
from astor_deep_insight_store import DeepInsightAnswerStore
from deep_insight_strategy import decide_deep_insight_strategy


ENGINE_NAME = "astor.deep_insight.v0.1"


# ----------------------------
# Models
# ----------------------------


@dataclass
class DeepInsightQuestion:
    id: str
    text: str
    structure_key: Optional[str] = None
    hint: Optional[str] = None
    depth: int = 1
    strategy: str = "unexplored"  # "deep_dive" | "unexplored"


# ----------------------------
# Template Store
# ----------------------------


class DeepInsightTemplateStore:
    """deep_insight_questions.json を読む軽量ストア。"""

    def __init__(self, path: Optional[Path] = None) -> None:
        if path is None:
            here = Path(__file__).resolve()
            parents = list(here.parents)
            base = parents[3] if len(parents) > 3 else here.parent
            cfg_dir = base / "ai" / "data" / "config"

            # Phase5.3: 質問セットの差し替え（文体/戦略の検証用）
            # - 例: DEEP_INSIGHT_QUESTION_SET_ID=v2
            # - 読み込み候補: deep_insight_questions.v2.json
            set_id = str(os.getenv("DEEP_INSIGHT_QUESTION_SET_ID", "") or "").strip()
            safe_set_id = re.sub(r"[^0-9A-Za-z_\-]", "", set_id)[:32] if set_id else ""

            alt = cfg_dir / f"deep_insight_questions.{safe_set_id}.json" if safe_set_id else None
            default_path = cfg_dir / "deep_insight_questions.json"
            path = alt if (alt is not None and alt.exists()) else default_path
        self.path = path
        self._raw: Dict[str, Any] = self._load()

    def _load(self) -> Dict[str, Any]:
        if not self.path.exists():
            return {}
        try:
            raw = json.loads(self.path.read_text(encoding="utf-8"))
        except Exception:
            return {}
        return raw if isinstance(raw, dict) else {}

    def get_templates_for_structure(self, structure_key: Optional[str]) -> List[Dict[str, Any]]:
        if not self._raw:
            return []
        key = str(structure_key) if structure_key else ""
        if key and isinstance(self._raw.get(key), list):
            return list(self._raw.get(key) or [])
        return []

    def get_global_templates(self) -> List[Dict[str, Any]]:
        if not self._raw:
            return []
        if isinstance(self._raw.get("_global"), list):
            return list(self._raw.get("_global") or [])
        return []

    def get_deep_dive_fallback(self) -> List[Dict[str, Any]]:
        if not self._raw:
            return []
        if isinstance(self._raw.get("_deep_dive_fallback"), list):
            return list(self._raw.get("_deep_dive_fallback") or [])
        return []

    def find_by_id(self, question_id: str) -> Optional[Dict[str, Any]]:
        if not question_id or not self._raw:
            return None

        for item in self.get_global_templates() + self.get_deep_dive_fallback():
            if isinstance(item, dict) and str(item.get("id") or "") == question_id:
                return item

        for _, v in self._raw.items():
            if not isinstance(v, list):
                continue
            for item in v:
                if isinstance(item, dict) and str(item.get("id") or "") == question_id:
                    return item
        return None


# ----------------------------
# Planning helpers
# ----------------------------


def _parse_ts(ts_str: Any) -> Optional[_dt.datetime]:
    if not isinstance(ts_str, str):
        return None
    try:
        return _dt.datetime.fromisoformat(ts_str.replace("Z", "+00:00"))
    except Exception:
        return None


def _unique_emotion_events_in_period(struct_map: Dict[str, Any], period_days: int) -> int:
    """patterns から "入力イベント数" を推定（tsユニーク）。"""
    if not struct_map:
        return 0

    now = _dt.datetime.utcnow().replace(tzinfo=_dt.timezone.utc)
    start = now - _dt.timedelta(days=max(1, int(period_days)))

    ts_set = set()
    for entry in struct_map.values():
        triggers = (entry or {}).get("triggers") or []
        for t in triggers:
            if not isinstance(t, dict):
                continue
            ts = _parse_ts(t.get("ts"))
            if ts is None:
                continue
            if ts < start or ts > now:
                continue
            ts_set.add(t.get("ts"))

    return len(ts_set)


def _pick_top_structure_in_period(struct_map: Dict[str, Any], period_days: int) -> Optional[str]:
    """直近 period_days の triggers が多い構造語を1つ選ぶ。"""
    if not struct_map:
        return None

    now = _dt.datetime.utcnow().replace(tzinfo=_dt.timezone.utc)
    start = now - _dt.timedelta(days=max(1, int(period_days)))

    best_key: Optional[str] = None
    best_cnt = 0
    best_score_sum = 0.0

    for entry in struct_map.values():
        key = str((entry or {}).get("structure_key") or "").strip()
        if not key:
            continue

        cnt = 0
        score_sum = 0.0
        triggers = (entry or {}).get("triggers") or []
        for t in triggers:
            if not isinstance(t, dict):
                continue
            ts = _parse_ts(t.get("ts"))
            if ts is None:
                continue
            if ts < start or ts > now:
                continue
            cnt += 1
            try:
                score_sum += float(t.get("score") or 0.0)
            except Exception:
                pass

        if cnt <= 0:
            continue

        if cnt > best_cnt or (cnt == best_cnt and score_sum > best_score_sum):
            best_cnt = cnt
            best_score_sum = score_sum
            best_key = key

    return best_key


def _seed_for_user(uid: str) -> int:
    """ユーザー/時刻から seed を作る（毎回変化するが user_id で偏りは抑える）。"""
    material = f"{uid}:{time.time_ns()}".encode("utf-8")
    digest = hashlib.sha256(material).digest()
    return int.from_bytes(digest[:8], "big", signed=False)


def _select_questions_from_templates(
    templates: List[Dict[str, Any]],
    *,
    max_questions: int,
    max_depth: int,
    strategy: str,
    structure_key_fallback: Optional[str] = None,
    exclude_ids: Optional[Set[str]] = None,
    rng: Optional[random.Random] = None,
) -> List[DeepInsightQuestion]:
    """テンプレート群から質問を選ぶ。

    - depth / strategy / text の基本条件を満たした候補を作る
    - exclude_ids に含まれる question_id は除外
    - rng が与えられている場合、候補をシャッフルしてから先頭から採用

    注意:
    - v0.1 は "形式を提供する" が目的なので、ここでは heavy な推論はしない。
    """

    out: List[DeepInsightQuestion] = []
    exclude: Set[str] = set(exclude_ids or set())

    # 重複排除（テンプレ側の重複耐性）
    seen: Set[str] = set()

    # まず候補を集める
    cand: List[Dict[str, Any]] = []

    for item in templates or []:
        if not isinstance(item, dict):
            continue
        qid = str(item.get("id") or "").strip()
        if not qid or qid in seen or qid in exclude:
            continue

        try:
            d = int(item.get("depth") or 1)
        except Exception:
            d = 1
        if d > int(max_depth):
            continue

        s = str(item.get("strategy") or "").strip() or None
        if s and s != strategy:
            continue

        if not str(item.get("text") or "").strip():
            continue

        seen.add(qid)
        cand.append(item)

    if rng is not None and len(cand) >= 2:
        rng.shuffle(cand)

    # 候補から採用
    for item in cand:
        qid = str(item.get("id") or "").strip()

        sk = item.get("structure_key")
        if sk is None:
            sk = structure_key_fallback
        sk_s = str(sk).strip() if sk is not None else None

        try:
            depth = int(item.get("depth") or 1)
        except Exception:
            depth = 1

        hint = item.get("hint")
        hint_s = str(hint).strip() if isinstance(hint, str) and hint.strip() else None

        out.append(
            DeepInsightQuestion(
                id=qid,
                text=str(item.get("text") or "").strip(),
                hint=hint_s,
                structure_key=sk_s or None,
                depth=max(1, depth),
                strategy=str(item.get("strategy") or strategy) or strategy,
            )
        )

        if len(out) >= int(max_questions):
            break

    return out


# ----------------------------
# Public API
# ----------------------------


def generate_deep_insight_questions_payload(
    *,
    user_id: str,
    max_questions: int = 3,
    max_depth: int = 1,
    period_days: int = 30,
    lang: str = "ja",
    tier: str = "free",
    context: Optional[str] = None,
) -> Dict[str, Any]:
    """Deep Insight 質問一覧（構文）を生成して返す。"""

    uid = str(user_id or "").strip()
    if not uid:
        return {
            "questions": [],
            "meta": {
                "status": "no_user_id",
                "engine": ENGINE_NAME,
            },
        }

    # v0.1 は ja 固定（将来拡張）
    if lang != "ja":
        lang = "ja"

    try:
        max_depth_i = int(max_depth)
    except Exception:
        max_depth_i = 1
    max_depth_i = max(1, min(max_depth_i, 5))

    try:
        max_q_i = int(max_questions)
    except Exception:
        max_q_i = 3
    max_q_i = max(1, min(max_q_i, 5))

    # ---- 構造の密度判定（rich/sparse） ----
    struct_map: Dict[str, Any] = {}
    if StructurePatternsStore is not None:
        try:
            store = StructurePatternsStore()
            user_entry = store.get_user_patterns(uid)
            struct_map = user_entry.get("structures", {}) or {}
        except Exception:
            struct_map = {}

        unique_events = _unique_emotion_events_in_period(struct_map, period_days=period_days)

        # Phase5.4: 戦略判定（deep_dive / unexplored）をサーバ設定（ENV）で切替可能にする
        # - 例: DEEP_INSIGHT_RICH_THRESHOLD=8
        # - 例: DEEP_INSIGHT_FREE_ALWAYS_UNEXPLORED=true
        # - 例: DEEP_INSIGHT_STRATEGY_FORCE=unexplored
        strategy, decision = decide_deep_insight_strategy(unique_events=unique_events, tier=str(tier or "free"))
        density = str(decision.get("density") or "").strip() or ("rich" if int(unique_events) >= 8 else "sparse")
        try:
            rich_threshold = int(decision.get("rich_threshold") or 8)
        except Exception:
            rich_threshold = 8

    template_store = DeepInsightTemplateStore()

    chosen_structure: Optional[str] = None
    candidates: List[Dict[str, Any]] = []

    if strategy == "deep_dive":
        chosen_structure = _pick_top_structure_in_period(struct_map, period_days=max(period_days, 30))
        if chosen_structure:
            candidates.extend(template_store.get_templates_for_structure(chosen_structure))
        candidates.extend(template_store.get_deep_dive_fallback())
    else:
        candidates.extend(template_store.get_global_templates())

    # ---- ローテーション: 直前提示の除外 / 回答済みの除外 ----
    served_store = DeepInsightServedStore()
    answer_store = DeepInsightAnswerStore()

    answered_ids: Set[str] = set()
    try:
        # secret も含めて「回答済み」は避ける（再提示を防ぐ）
        # NOTE: 長期ユーザーが増えると直近N件だけでは重複が発生し得るため、question_id の集合を広めに取得する。
        answered_ids = set(answer_store.get_answered_question_ids(uid, limit=5000, include_secret=True) or set())
    except Exception:
        answered_ids = set()

    last_batch = set(served_store.get_last_batch(uid))

    rng = random.Random(_seed_for_user(uid))

    # 1) まずは "回答済み + 直前バッチ" を除外して選ぶ
    exclude_primary = answered_ids | last_batch
    questions = _select_questions_from_templates(
        candidates,
        max_questions=max_q_i,
        max_depth=max_depth_i,
        strategy=strategy,
        structure_key_fallback=chosen_structure,
        exclude_ids=exclude_primary,
        rng=rng,
    )

    # 2) 足りない場合は "回答済み" だけ除外（= 直前バッチの再利用は許可）
    if len(questions) < max_q_i:
        already = {q.id for q in questions}
        more = _select_questions_from_templates(
            candidates,
            max_questions=max_q_i,
            max_depth=max_depth_i,
            strategy=strategy,
            structure_key_fallback=chosen_structure,
            exclude_ids=(answered_ids | already),
            rng=rng,
        )
        for q in more:
            if q.id in already:
                continue
            questions.append(q)
            already.add(q.id)
            if len(questions) >= max_q_i:
                break

    # 3) それでも足りない場合は、反対戦略のテンプレも試す（ただし回答済みは避ける）
    if len(questions) < max_q_i:
        alt_strategy = "deep_dive" if strategy != "deep_dive" else "unexplored"
        alt_candidates: List[Dict[str, Any]] = []
        alt_structure: Optional[str] = None

        if alt_strategy == "deep_dive":
            alt_structure = _pick_top_structure_in_period(struct_map, period_days=max(period_days, 30))
            if alt_structure:
                alt_candidates.extend(template_store.get_templates_for_structure(alt_structure))
            alt_candidates.extend(template_store.get_deep_dive_fallback())
        else:
            alt_candidates.extend(template_store.get_global_templates())

        if alt_candidates:
            already = {q.id for q in questions}
            more = _select_questions_from_templates(
                alt_candidates,
                max_questions=max_q_i,
                max_depth=max_depth_i,
                strategy=alt_strategy,
                structure_key_fallback=alt_structure,
                exclude_ids=(answered_ids | last_batch | already),
                rng=rng,
            )
            for q in more:
                if q.id in already:
                    continue
                questions.append(q)
                already.add(q.id)
                if len(questions) >= max_q_i:
                    break

    # 候補が0の時だけ、別系統のフォールバック候補からも拾う（ただし回答済みは避ける）
    if not questions:
        fb = template_store.get_global_templates() if strategy != "deep_dive" else template_store.get_deep_dive_fallback()
        questions = _select_questions_from_templates(
            fb,
            max_questions=max_q_i,
            max_depth=max_depth_i,
            strategy=strategy,
            structure_key_fallback=chosen_structure,
            exclude_ids=(answered_ids | last_batch),
            rng=rng,
        )

    # 提示履歴に記録（次回の "別の問い" で直前を避ける）
    try:
        served_store.record_batch(uid, [q.id for q in questions])
    except Exception:
        # served 保存の失敗は致命ではない
        pass

    now_iso = _dt.datetime.utcnow().replace(microsecond=0).isoformat() + "Z"

    return {
        "questions": [asdict(q) for q in questions],
        "meta": {
            "status": "ok",
            "engine": ENGINE_NAME,
            "user_id": uid,
            "generated_at": now_iso,
            "lang": lang,
            "tier": str(tier or "free"),
            "max_depth": max_depth_i,
            "max_questions": max_q_i,
            "density": density,
            "unique_emotion_events": unique_events,
            "rich_threshold": int(rich_threshold),
            "strategy": strategy,
            "strategy_decision": (decision if isinstance(decision, dict) else None),
            "chosen_structure_key": chosen_structure,
            "context": (str(context)[:200] if context else None),
            # デバッグ用（必要ならフロントで非表示にしてOK）
            "rotation": {
                "excluded_answered": len(answered_ids),
                "excluded_last_batch": len(last_batch),
            },
        },
    }
