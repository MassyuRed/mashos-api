# -*- coding: utf-8 -*-
"""
ASTOR Core v0.1

Artificial Self Thinking Observer & Resonator

Cocolon 内で動作する「構造思考エンジン ASTOR」の最小スケルトン。

v0.1 の目的:
- 既存の /mymodel/infer, /emotion/submit の挙動を壊さずに、
  将来 ASTOR による構造思考を差し込める入口を用意すること。
- EmotionIngest モードを通じて、感情ログを ASTOR でも観測できるようにすること。
"""

from __future__ import annotations

from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional

import json
from pydantic import BaseModel, Field

from astor_structure_matcher import StructureMatcher
from astor_myweb_insight import generate_myweb_insight_payload


# ---------- モード定義 ----------


class AstorMode(str, Enum):
    EMOTION_INGEST = "EmotionIngest"
    MYMODEL_REPLY = "MyModelReply"
    MYWEB_INSIGHT = "MyWebInsight"


# ---------- ペイロード定義 ----------


class AstorEmotionPayload(BaseModel):
    """
    EmotionIngest モードで ASTOR に渡される情報。
    /emotion/submit で Supabase に保存された内容のうち、
    ASTOR が構造思考に使いたい要素のみをまとめたもの。
    """

    user_id: str = Field(..., description="感情を入力したユーザーのID")
    created_at: str = Field(..., description="感情レコードの作成時刻（ISO8601, UTC想定）")
    emotions: List[Dict[str, Any]] = Field(
        ...,
        description="emotion_details 相当（type / strength などを含む辞書の配列）",
    )
    emotion_strength_avg: float = Field(..., description="平均強度")
    memo: Optional[str] = Field(default=None, description="自由記述メモ")
    is_secret: bool = Field(default=False, description="シークレットフラグ（外部照会に使わない）")


class AstorRequest(BaseModel):
    """
    ASTOR に渡す共通リクエストモデル。
    mode に応じて、使用するフィールドが変わる。
    """

    mode: AstorMode

    # EmotionIngest 用
    emotion: Optional[AstorEmotionPayload] = None

    # MyModelReply 用（将来接続）
    user_id: Optional[str] = None
    instruction: Optional[str] = None
    input: Optional[Dict[str, Any]] = None
    target: Optional[str] = "self"

    # MyWebInsight 用（将来接続）
    period: Optional[str] = None

    options: Dict[str, Any] = {}


class AstorResponse(BaseModel):
    text: Optional[str]
    meta: Dict[str, Any] = {}


# ---------- ユーティリティ ----------


def _parse_period_days(period: Optional[str]) -> int:
    """
    "7d", "30d", "12w", "3m" などの文字列から日数をざっくり算出するユーティリティ。
    - サフィックス:
        d: 日
        w: 週 (×7日)
        m: 月 (×30日程度のラフな換算)
    - うまく解釈できなかった場合は 30 日を返す。
    """
    if not period:
        return 30
    s = str(period).strip().lower()
    if not s:
        return 30
    try:
        if s.endswith("d"):
            n = int(s[:-1] or "30")
            return max(1, n)
        if s.endswith("w"):
            n = int(s[:-1] or "1")
            return max(1, n * 7)
        if s.endswith("m"):
            n = int(s[:-1] or "1")
            return max(1, n * 30)
        # サフィックス無しは日数とみなす
        n = int(s)
        return max(1, n)
    except Exception:
        return 30


# ---------- ASTOR 本体 ----------


class AstorEngine:
    """
    ASTOR の中核クラス。

    - handle() に AstorRequest を渡すと、mode に応じて処理を切り替える。
    - v0.1 では EmotionIngest を中心に実装し、
      MyModelReply / MyWebInsight はプレースホルダのまま。
    """

    def __init__(self) -> None:
        # 構造語マッチャ（設定ファイルが無ければ空で動く）
        self._matcher = StructureMatcher()
        # 構造語パターンストア（ユーザーごとの構造状態を保持）
        from astor_patterns import StructurePatternsStore  # 局所 import で循環を避ける

        self._patterns = StructurePatternsStore()

    def handle(self, req: AstorRequest) -> AstorResponse:
        if req.mode == AstorMode.EMOTION_INGEST:
            return self._handle_emotion_ingest(req)
        elif req.mode == AstorMode.MYMODEL_REPLY:
            return self._handle_mymodel_reply(req)
        elif req.mode == AstorMode.MYWEB_INSIGHT:
            return self._handle_myweb_insight(req)
        else:
            return AstorResponse(text=None, meta={"error": "unsupported_mode", "mode": req.mode})

    # ------ EmotionIngest: 感情入力を受け取り、ASTOR側で観測するモード ------

    def _handle_emotion_ingest(self, req: AstorRequest) -> AstorResponse:
        """
        感情入力を ASTOR 側でも観測する。

        v0.1 方針:
        - ai/data/raw/astor_emotions.jsonl に 1行JSONとして追記し、
          「ASTOR が独自に参照できる感情履歴」を残す。
        - astor_structure_patterns.json にユーザーごとの構造パターンを集約する。
        """
        payload = req.emotion
        if payload is None:
            return AstorResponse(text=None, meta={"mode": req.mode.value, "status": "no_payload"})

        # ログ1件ぶんをASTOR用のシンプルな形式に変換
        record = self._build_emotion_record(payload)

        # 構造語マッチング（どの構造語が関係していそうかを推定）
        try:
            hits = self._matcher.match(record)
            record["structures"] = [
                {
                    "key": h.key,
                    "score": h.score,
                }
                for h in hits
            ]
        except Exception as exc:
            # マッチャの不具合で EmotionIngest 全体が落ちないようにする
            record["structures"] = []
            record["structure_match_error"] = str(exc)

        # 構造パターン集約（ユーザーごとの状態に反映）
        try:
            self._patterns.update_with_emotion_record(record)
        except Exception as exc:
            record["patterns_update_error"] = str(exc)

        # jsonl として追記保存
        try:
            path = self._astor_emotion_log_path()
            path.parent.mkdir(parents=True, exist_ok=True)
            with path.open("a", encoding="utf-8") as f:
                f.write(json.dumps(record, ensure_ascii=False) + "\n")
            status = "logged"
        except Exception as exc:  # ログ失敗は致命的ではない
            status = f"log_error:{exc}"

        return AstorResponse(
            text=None,
            meta={
                "mode": req.mode.value,
                "status": status,
            },
        )

    def _build_emotion_record(self, payload: AstorEmotionPayload) -> Dict[str, Any]:
        """
        EmotionSubmit の詳細を ASTOR 内部で扱いやすい形に正規化する。
        - MyWeb の EmotionEntry / logs.jsonl に近い形に寄せておく。
        """
        # type を英語ラベルに寄せるための簡易マップ（暫定）
        TYPE_MAP = {
            "喜び": "Joy",
            "Joy": "Joy",
            "Sadness": "Sadness",
            "悲しみ": "Sadness",
            "不安": "Anxiety",
            "Anxiety": "Anxiety",
            "怒り": "Anger",
            "Anger": "Anger",
            "落ち着き": "Calm",
            "Calm": "Calm",
        }

        # 強度 weak / medium / strong を 1..3 にマップ（暫定）
        STRENGTH_MAP = {
            "weak": 1,
            "medium": 2,
            "strong": 3,
        }

        main_emotion = None
        if payload.emotions:
            # ひとまず最初の要素を代表とする（v0.1）
            e0 = payload.emotions[0]
            etype_raw = str(e0.get("type") or "")
            strength_raw = str(e0.get("strength") or "").lower()

            main_emotion = {
                "label": TYPE_MAP.get(etype_raw, etype_raw),
                "intensity": STRENGTH_MAP.get(strength_raw, 2),
            }

        record: Dict[str, Any] = {
            "uid": payload.user_id,
            "ts": payload.created_at,
            "emotion": (main_emotion or {}).get("label", None),
            "intensity": (main_emotion or {}).get("intensity", None),
            "strength_avg": payload.emotion_strength_avg,
            "memo": payload.memo or "",
            "is_secret": payload.is_secret,
        }
        return record

    def _astor_emotion_log_path(self) -> Path:
        """
        ASTOR専用の感情ログ保存先を返す。
        - 既存の ai/data/raw/logs.jsonl とは分けておく。
        """
        # このファイル: mashos-api/ai/services/ai_inference/astor_core.py 想定。
        # テスト/単体実行などでフォルダ深度が足りない場合でも IndexError で落ちないようにする。
        here = Path(__file__).resolve()
        parents = list(here.parents)
        base = parents[3] if len(parents) > 3 else here.parent
        return base / "ai" / "data" / "raw" / "astor_emotions.jsonl"

    # ------ MyModelReply: 既存人格応答をラップするモード（v0.1では未接続） ------

    def _handle_mymodel_reply(self, req: AstorRequest) -> AstorResponse:
        """
        v0.1 の時点ではまだ ASTOR 独自の思考は行わず、
        既存の compose_response() をラップする土台だけ用意する。

        実際の接続は、別ステップで /mymodel/infer を ASTOR 経由に差し替える際に行う。
        """
        return AstorResponse(
            text=None,
            meta={"mode": req.mode.value, "status": "not_implemented"},
        )

    # ------ MyWebInsight: 週報・月報など期間分析モード ------

    def _handle_myweb_insight(self, req: AstorRequest) -> AstorResponse:
        """
        MyWeb 用の期間レポート生成モード。

        v1.0 では astor_myweb_insight.generate_myweb_insight_payload() を呼び出し、
        MyWeb 用の「構文（=レポートスキーマ）」と、表示用テキストを返す。
        """
        user_id = req.user_id
        if not user_id:
            return AstorResponse(
                text=None,
                meta={
                    "mode": req.mode.value,
                    "status": "no_user_id",
                    "error": "MyWebInsight requires user_id",
                    "engine": "astor.myweb.v1",
                },
            )

        period_str = req.period or "30d"
        period_days = _parse_period_days(period_str)

        try:
            text, report = generate_myweb_insight_payload(user_id=user_id, period_days=period_days, lang="ja")
            meta: Dict[str, Any] = {
                "mode": req.mode.value,
                "engine": "astor.myweb.v1",
                "period": period_str,
                "period_days": period_days,
                "status": "ok",
                # UI 側で安定して表示するためのレポート構文
                "report": report,
            }
            return AstorResponse(text=text, meta=meta)
        except Exception as exc:
            # ここでエラーになっても MyWeb 全体は落とさない方針
            return AstorResponse(
                text=None,
                meta={
                    "mode": req.mode.value,
                    "engine": "astor.myweb.v1",
                    "period": period_str,
                    "period_days": period_days,
                    "status": "error",
                    "error": str(exc),
                },
            )
