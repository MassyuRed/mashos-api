# -*- coding: utf-8 -*-
"""
astor_patterns.py

ASTOR 用の「構造語パターン集約ストア」。

目的:
- EmotionIngest で正規化 & 構造マッチ済みの emotion_record を受け取り、
  user_id × structure_key ごとの「パターン状態」に集約していく。

ストレージ:
- 既定: Supabase テーブル (mymodel_structure_patterns) に永続化（複数インスタンスでも共有）
- フォールバック: JSON ファイル（mashos-api/ai/data/state/astor_structure_patterns.json）

※ Supabase 側のテーブルが未作成の場合でもサービスが落ちないよう、
  テーブル検出に失敗した場合は自動的にファイルストアにフォールバックします。
"""

from __future__ import annotations

from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any, Dict, List, Optional
import datetime as _dt
import json
import logging
import os

import httpx


logger = logging.getLogger(__name__)

# Supabase (Service Role) による永続化
SUPABASE_URL = str(os.getenv("SUPABASE_URL") or "").strip()
SUPABASE_SERVICE_ROLE_KEY = str(os.getenv("SUPABASE_SERVICE_ROLE_KEY") or "").strip()

# テーブル名は変更可能（必要なら env で差し替え）
PATTERNS_TABLE = str(os.getenv("ASTOR_STRUCTURE_PATTERNS_TABLE") or "mymodel_structure_patterns").strip()

# 明示指定:
# - "supabase" を指定すると Supabase 優先（ただし接続不可/テーブル無しならフォールバック）
# - "file" を指定すると常にファイル
BACKEND_PREF = str(os.getenv("ASTOR_STRUCTURE_PATTERNS_BACKEND") or "").strip().lower()


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
    構造語パターン集約ストア（user_id × structure_key）。

    もともとは JSON ファイル保存のみの実装だったが、Render などの複数インスタンス環境で
    「入力は保存されているのにレポートに反映されない（インスタンスごとに状態がズレる）」を避けるため、
    Supabase テーブルへ永続化できるようにしている。

    JSON スキーマ例（ユーザー単位の保持構造）:
        {
          "structures": {
            "執着": {
              "structure_key": "執着",
              "triggers": [ ... StructureTrigger ... ],
              "stats": { "count": 12, "avg_score": 0.73, "avg_intensity": 2.4 },
              "last_updated": "2025-12-03T12:34:56Z"
            }
          }
        }
    """

    _SB_CHECKED: bool = False
    _SB_AVAILABLE: bool = False
    _SB_CHECK_ERROR: str = ""

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

        self._use_supabase = self._detect_supabase_available()

        # file backend のみ全量ロード（supabase は user 単位で取得するためロード不要）
        self._state: Dict[str, Any] = {} if self._use_supabase else self._load()

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

        if self._use_supabase:
            user_entry = self.get_user_patterns(uid)  # DBから読む
            struct_map: Dict[str, Any] = user_entry.get("structures") or {}
            if not isinstance(struct_map, dict):
                struct_map = {}
                user_entry["structures"] = struct_map
        else:
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
        if self._use_supabase:
            try:
                self._sb_upsert_user_patterns(uid, user_entry.get("structures") or {})
            except Exception as exc:
                # 失敗しても emotion ingest 自体は落とさない（best effort）
                logger.warning("ASTOR patterns save to Supabase failed: %s", exc)
        else:
            self._save()

    def update_triggers_secret_by_ts(self, user_id: str, ts: str, is_secret: bool) -> int:
        """指定ユーザーの trigger 群のうち、ts が一致するものの is_secret を更新する。

        目的:
        - MyWeb 履歴画面などで「後から secret を切り替えた」場合に、
          既に蓄積されている triggers 側も整合させる。

        仕様:
        - 1つの感情ログが複数の構造語にヒットしている場合、複数 trigger が同じ ts を持つ。
          そのため、ts 一致の trigger をまとめて更新する。
        - 更新が発生した場合のみ保存する。
        """

        uid = str(user_id or "").strip()
        ts_s = str(ts or "").strip()
        if not uid or not ts_s:
            return 0

        target = bool(is_secret)

        if self._use_supabase:
            user_entry = self.get_user_patterns(uid)
            struct_map: Dict[str, Any] = user_entry.get("structures") or {}
            if not isinstance(struct_map, dict) or not struct_map:
                return 0

            updated = 0
            for entry in struct_map.values():
                triggers = entry.get("triggers") or []
                for t in triggers:
                    if not isinstance(t, dict):
                        continue
                    if str(t.get("ts") or "") != ts_s:
                        continue
                    if bool(t.get("is_secret", False)) == target:
                        continue
                    t["is_secret"] = target
                    updated += 1

            if updated > 0:
                try:
                    self._sb_upsert_user_patterns(uid, struct_map)
                except Exception as exc:
                    logger.warning("ASTOR patterns secret update failed: %s", exc)
            return updated

        # --- file backend ---
        users = self._state.get("users") or {}
        user_entry = users.get(uid) or {}
        struct_map: Dict[str, Any] = user_entry.get("structures") or {}
        if not struct_map:
            return 0

        updated = 0
        for entry in struct_map.values():
            triggers = entry.get("triggers") or []
            for t in triggers:
                if not isinstance(t, dict):
                    continue
                if str(t.get("ts") or "") != ts_s:
                    continue
                if bool(t.get("is_secret", False)) == target:
                    continue
                t["is_secret"] = target
                updated += 1

        if updated > 0:
            self._save()
        return updated

    def get_user_patterns(self, user_id: str) -> Dict[str, Any]:
        """
        特定ユーザーの構造語パターン状態を返す。
        - MyModelReply / MyProfile / MyWebInsight からの参照用。
        """
        uid = str(user_id or "").strip()
        if not uid:
            return {"structures": {}}

        if self._use_supabase:
            try:
                structures = self._sb_get_user_structures(uid)
                if not isinstance(structures, dict):
                    structures = {}
                return {"structures": structures}
            except Exception as exc:
                logger.warning("ASTOR patterns load from Supabase failed: %s", exc)
                return {"structures": {}}

        users = self._state.get("users") or {}
        return users.get(uid, {"structures": {}})

    # ---------- 内部実装（Supabase）----------

    @classmethod
    def _detect_supabase_available(cls) -> bool:
        if cls._SB_CHECKED:
            return cls._SB_AVAILABLE

        cls._SB_CHECKED = True

        if BACKEND_PREF == "file":
            cls._SB_AVAILABLE = False
            return False

        if not SUPABASE_URL or not SUPABASE_SERVICE_ROLE_KEY or not PATTERNS_TABLE:
            cls._SB_AVAILABLE = False
            cls._SB_CHECK_ERROR = "missing_supabase_env"
            return False

        # テーブルの存在を軽くプローブ（空でも 200 + [] になる）
        try:
            url = f"{SUPABASE_URL}/rest/v1/{PATTERNS_TABLE}?select=user_id&limit=1"
            headers = cls._sb_headers()
            with httpx.Client(timeout=5.0) as client:
                resp = client.get(url, headers=headers)

            if resp.status_code == 200:
                cls._SB_AVAILABLE = True
                cls._SB_CHECK_ERROR = ""
                return True

            if resp.status_code == 404:
                cls._SB_AVAILABLE = False
                cls._SB_CHECK_ERROR = f"table_not_found:{PATTERNS_TABLE}"
                return False

            cls._SB_AVAILABLE = False
            cls._SB_CHECK_ERROR = f"http_{resp.status_code}:{resp.text[:200]}"
            return False
        except Exception as exc:
            cls._SB_AVAILABLE = False
            cls._SB_CHECK_ERROR = str(exc)
            return False

    @staticmethod
    def _sb_headers(prefer: Optional[str] = None) -> Dict[str, str]:
        headers = {
            "Authorization": f"Bearer {SUPABASE_SERVICE_ROLE_KEY}",
            "apikey": SUPABASE_SERVICE_ROLE_KEY,
            "Content-Type": "application/json",
        }
        if prefer:
            headers["Prefer"] = prefer
        return headers

    def _sb_get_user_structures(self, user_id: str) -> Dict[str, Any]:
        """Supabase から user_id の structures を取得する。無ければ空dict。"""
        url = (
            f"{SUPABASE_URL}/rest/v1/{PATTERNS_TABLE}"
            f"?user_id=eq.{user_id}&select=structures&limit=1"
        )
        with httpx.Client(timeout=5.0) as client:
            resp = client.get(url, headers=self._sb_headers())

        if resp.status_code != 200:
            raise RuntimeError(f"Supabase GET failed: {resp.status_code} {resp.text[:200]}")

        data = resp.json()
        if isinstance(data, list) and data:
            row = data[0] if isinstance(data[0], dict) else {}
            structures = row.get("structures")
            return structures if isinstance(structures, dict) else {}
        return {}

    def _sb_upsert_user_patterns(self, user_id: str, structures: Dict[str, Any]) -> None:
        """Supabase に user_id の patterns（structures）を upsert する。"""
        now = _dt.datetime.utcnow().replace(microsecond=0).isoformat() + "Z"

        payload = {
            "user_id": user_id,
            "structures": structures or {},
            "updated_at": now,
        }

        url = f"{SUPABASE_URL}/rest/v1/{PATTERNS_TABLE}?on_conflict=user_id"
        prefer = "resolution=merge-duplicates,return=minimal"
        with httpx.Client(timeout=5.0) as client:
            resp = client.post(url, headers=self._sb_headers(prefer=prefer), json=payload)

        # PostgREST: 201 created / 204 no content / 200 ok が想定
        if resp.status_code not in (200, 201, 204):
            raise RuntimeError(f"Supabase UPSERT failed: {resp.status_code} {resp.text[:200]}")

    # ---------- 内部実装（File）----------

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
