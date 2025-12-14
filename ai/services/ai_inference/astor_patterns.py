
# -*- coding: utf-8 -*-
"""
astor_patterns.py

ASTOR 用の「構造語パターン集約ストア」。

目的:
- EmotionIngest で正規化 & 構造マッチ済みの emotion_record を受け取り、
  user_id × structure_key ごとの「パターン状態」に集約していく。
- ストレージ形式は JSON ファイル（mashos-api/ai/data/state/astor_structure_patterns.json）。
  後で Supabase テーブル (mymodel_structure_patterns) に移行してもよいように、
  スキーマはドキュメント仕様に寄せる。
"""

from __future__ import annotations

from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any, Dict, List, Optional
import json
import datetime as _dt


@dataclass
class StructureTrigger:
    ts: str
    emotion: Optional[str]
    intensity: Optional[float]
    score: float
    is_secret: bool
    memo_excerpt: str


@dataclass
class StructureStats:
    count: int = 0
    avg_score: float = 0.0
    avg_intensity: float = 0.0


class StructurePatternsStore:
    """
    - in-memory で dict を保持しつつ、更新時に JSON に書き戻すシンプル実装。
    - 想定パス: mashos-api/ai/data/state/astor_structure_patterns.json
    - JSON スキーマ例:
        {
          "users": {
            "user-123": {
              "structures": {
                "執着": {
                  "structure_key": "執着",
                  "triggers": [ ... StructureTrigger ... ],
                  "stats": { "count": 12, "avg_score": 0.73, "avg_intensity": 2.4 },
                  "last_updated": "2025-12-03T12:34:56Z"
                }
              }
            }
          }
        }
    """

    def __init__(self, path: Optional[Path] = None) -> None:
        if path is None:
            # 既定は mashos-api/ai/data/state/astor_structure_patterns.json を想定。
            # ただしテスト/単体実行などでフォルダ深度が足りない場合に IndexError で落ちないよう、
            # 安全にフォールバックする。
            here = Path(__file__).resolve()
            parents = list(here.parents)
            base = parents[3] if len(parents) > 3 else here.parent
            path = base / "ai" / "data" / "state" / "astor_structure_patterns.json"
        self.path = path
        self._state: Dict[str, Any] = self._load()

    # ---------- パブリック API ----------

    def update_with_emotion_record(self, record: Dict[str, Any]) -> None:
        """
        astor_core._build_emotion_record() ＋ matcher.match() 済みの record を受け取り、
        user_id × structure_key のパターンに反映する。
        """
        uid = str(record.get("uid") or "").strip()
        if not uid:
            return

        structures = record.get("structures") or []
        if not structures:
            return

        emotion = record.get("emotion")
        intensity = record.get("intensity")
        ts = record.get("ts")
        if not ts:
            # 念のため現在時刻を補う
            ts = _dt.datetime.utcnow().replace(microsecond=0).isoformat() + "Z"

        memo = record.get("memo") or ""
        is_secret = bool(record.get("is_secret", False))

        users = self._state.setdefault("users", {})
        user_entry = users.setdefault(uid, {"structures": {}})
        struct_map: Dict[str, Any] = user_entry.setdefault("structures", {})

        for s in structures:
            key = str(s.get("key") or "").strip()
            if not key:
                continue
            try:
                score = float(s.get("score") or 0.0)
            except (TypeError, ValueError):
                score = 0.0

            # 0 以下は無視
            if score <= 0.0:
                continue

            struct_entry = struct_map.setdefault(
                key,
                {
                    "structure_key": key,
                    "triggers": [],
                    "stats": {
                        "count": 0,
                        "avg_score": 0.0,
                        "avg_intensity": 0.0,
                    },
                    "last_updated": ts,
                },
            )

            # トリガー履歴を更新（末尾に追加）
            trigger = StructureTrigger(
                ts=ts,
                emotion=emotion,
                intensity=float(intensity) if intensity is not None else None,
                score=score,
                is_secret=is_secret,
                memo_excerpt=memo[:80],
            )
            triggers: List[Dict[str, Any]] = struct_entry.setdefault("triggers", [])
            triggers.append(asdict(trigger))

            # 上限件数（古いものから間引く）
            max_triggers = 50
            if len(triggers) > max_triggers:
                del triggers[0 : len(triggers) - max_triggers]

            # 統計値を更新
            stats: Dict[str, Any] = struct_entry.setdefault("stats", {})
            prev_count = int(stats.get("count", 0))
            prev_avg_score = float(stats.get("avg_score", 0.0))
            prev_avg_intensity = float(stats.get("avg_intensity", 0.0))

            new_count = prev_count + 1
            new_avg_score = (prev_avg_score * prev_count + score) / new_count
            if intensity is not None:
                try:
                    f_int = float(intensity)
                    new_avg_intensity = (prev_avg_intensity * prev_count + f_int) / new_count
                except (TypeError, ValueError):
                    new_avg_intensity = prev_avg_intensity
            else:
                new_avg_intensity = prev_avg_intensity

            stats["count"] = new_count
            stats["avg_score"] = new_avg_score
            stats["avg_intensity"] = new_avg_intensity

            struct_entry["stats"] = stats
            struct_entry["last_updated"] = ts

        # 変更を保存
        self._save()

    def get_user_patterns(self, user_id: str) -> Dict[str, Any]:
        """
        特定ユーザーの構造語パターン状態を返す。
        - MyModelReply / MyWebInsight からの参照用。
        """
        users = self._state.get("users") or {}
        return users.get(str(user_id), {"structures": {}})

    # ---------- 内部実装 ----------

    def _load(self) -> Dict[str, Any]:
        path = self.path
        if not path.exists():
            path.parent.mkdir(parents=True, exist_ok=True)
            return {}
        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            return {}
        if not isinstance(raw, dict):
            return {}
        return raw

    def _save(self) -> None:
        path = self.path
        path.parent.mkdir(parents=True, exist_ok=True)
        tmp = path.with_suffix(".tmp")
        tmp.write_text(json.dumps(self._state, ensure_ascii=False, indent=2), encoding="utf-8")
        tmp.replace(path)
