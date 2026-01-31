
# -*- coding: utf-8 -*-
"""
astor_structure_matcher.py

ASTOR 用の「構造語マッチング」モジュール。

- EmotionIngest で正規化された感情レコード
    (emotion, intensity, memo, is_secret ...)
  から、
    -> どの構造語がどのくらい関係していそうか
  をスコアリングして返す。

v0.1 では:
- 単純な感情ラベル + キーワードベースの重み付けでスコアを算出する。
- 設定ファイル ai/data/config/astor_structure_dict.json が存在すればそれを使い、
  無ければマッチングは行わず空リストを返す。
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional
import json


@dataclass
class StructureHit:
    key: str          # 例: "執着", "愛", "選択肢消失"
    score: float      # 0.0〜1.0 想定
    reasons: Dict[str, Any]  # マッチ理由（感情/キーワードなど）


class StructureMatcher:
    """
    感情レコード -> 構造語スコア の変換を行うクラス。

    設定ファイル:
    - デフォルト: mashos-api/ai/data/config/astor_structure_dict.json
    - スキーマ例:
        {
          "執着": {
            "base_weight": 0.2,
            "emotion_weights": { "Anxiety": 0.6, "Anger": 0.4 },
            "keywords": ["手放せない", "離れたくない", "失いたくない"],
            "keyword_weight": 0.7
          }
        }
    """

    def __init__(self, config_path: Optional[Path] = None) -> None:
        if config_path is None:
            # 既定は mashos-api/ai/data/config/astor_structure_dict.json を想定。
            # ただしテスト/単体実行などでフォルダ深度が足りない場合に IndexError で落ちないよう、
            # 安全にフォールバックする。
            here = Path(__file__).resolve()
            parents = list(here.parents)
            base = parents[3] if len(parents) > 3 else here.parent
            config_path = base / "ai" / "data" / "config" / "astor_structure_dict.json"

        self.config_path = config_path
        self.struct_defs = self._load_config(config_path)

    # ---------- 公開メソッド ----------

    def match(self, emotion_record: Dict[str, Any]) -> List[StructureHit]:
        """
        ASTOR の EmotionIngest で作られたレコードから構造語スコアを計算する。

        emotion_record 例:
        {
            "uid": "user-123",
            "ts": "2025-12-03T12:34:56Z",
            "emotion": "Anxiety",
            "intensity": 3,
            "strength_avg": 2.5,
            "memo": "大事な人に無視されて、不安と怒りが混ざってる感じがする",
            "is_secret": false
        }
        """
        if not self.struct_defs:
            return []

        label = str(emotion_record.get("emotion") or "")
        intensity = float(emotion_record.get("intensity") or 0.0)
        memo = str(emotion_record.get("memo") or "")

        hits: List[StructureHit] = []

        for key, conf in self.struct_defs.items():
            score, reasons = self._score_one(key, conf, label, intensity, memo)
            if score <= 0.0:
                continue
            hits.append(StructureHit(key=key, score=min(score, 1.0), reasons=reasons))

        # スコア順にソートして、上位数件だけに絞る
        hits.sort(key=lambda h: h.score, reverse=True)
        if not hits:
            return []

        THRESHOLD = 0.20
        MAX_HITS = 5
        filtered = [h for h in hits if h.score >= THRESHOLD][:MAX_HITS]
        return filtered

    # ---------- 内部実装 ----------

    def _load_config(self, path: Path) -> Dict[str, Dict[str, Any]]:
        """
        構造語設定をロードする。
        - 存在しなければ空 dict を返す。
        - スキーマ例はクラス docstring を参照。
        """
        if not path.exists():
            return {}

        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            return {}

        if not isinstance(raw, dict):
            return {}

        return raw

    def _score_one(
        self,
        key: str,
        conf: Dict[str, Any],
        label: str,
        intensity: float,
        memo: str,
    ) -> (float, Dict[str, Any]):
        """
        1構造語ぶんのスコアを計算する。

        conf の想定スキーマ例:
        {
          "emotion_weights": { "Anxiety": 0.6, "Anger": 0.4 },
          "keywords": ["手放せない", "離れたくない", "失いたくない"],
          "base_weight": 0.1,
          "keyword_weight": 0.5
        }
        """
        base = float(conf.get("base_weight", 0.0))

        # 感情ラベルとのマッチ
        ew: Dict[str, float] = conf.get("emotion_weights") or {}
        emotion_score = 0.0
        if label and label in ew:
            # intensity: 1〜3 を 0.0〜1.0 に正規化
            norm_intensity = max(0.0, min((intensity - 1.0) / 2.0, 1.0))
            emotion_score = ew[label] * norm_intensity

        # キーワードマッチ
        kw_list: List[str] = conf.get("keywords") or []
        kw_hits: List[str] = []
        memo_score = 0.0
        if memo and kw_list:
            for kw in kw_list:
                if kw and kw in memo:
                    kw_hits.append(kw)
            if kw_hits:
                memo_score = min(len(kw_hits) / max(len(kw_list), 1), 1.0)

        # 総合スコア
        keyword_weight = float(conf.get("keyword_weight", 0.5))
        score = base + emotion_score + memo_score * keyword_weight

        reasons = {
            "emotion_label": label,
            "emotion_weight_used": ew.get(label, 0.0),
            "intensity": intensity,
            "emotion_score": emotion_score,
            "keyword_hits": kw_hits,
            "memo_score": memo_score,
            "base_weight": base,
            "keyword_weight": keyword_weight,
        }
        return score, reasons
