# -*- coding: utf-8 -*-
"""astor_deep_insight_store.py

Deep Insight Answer Store v0.1

目的:
- Deep Insight で得られた Q&A を保存する。
- **MyProfileの分析情報としてのみ活用**し、MyWeb（週報/月報）には反映しない。

v0.1 実装:
- まずは JSON ファイル（ローカル）に保存。
- 将来 Supabase テーブル等に移行しやすいように、users -> answers の構造で保持。

保存先（既定）:
- mashos-api/ai/data/state/astor_deep_insight_answers.json
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional

import datetime as _dt
import json


class DeepInsightAnswerStore:
    def __init__(self, path: Optional[Path] = None) -> None:
        if path is None:
            here = Path(__file__).resolve()
            parents = list(here.parents)
            base = parents[3] if len(parents) > 3 else here.parent
            path = base / "ai" / "data" / "state" / "astor_deep_insight_answers.json"
        self.path = path
        self._state: Dict[str, Any] = self._load()

    # ---------- Public API ----------

    def append_answers(self, user_id: str, answers: List[Dict[str, Any]]) -> int:
        """指定ユーザーの answers を追記して保存する。"""

        uid = str(user_id or "").strip()
        if not uid:
            return 0

        clean: List[Dict[str, Any]] = []
        now_iso = _dt.datetime.utcnow().replace(microsecond=0).isoformat() + "Z"

        for a in answers or []:
            if not isinstance(a, dict):
                continue
            text = str(a.get("text") or "").strip()
            if not text:
                continue

            item: Dict[str, Any] = {
                "question_id": str(a.get("question_id") or "").strip() or None,
                "question_text": (str(a.get("question_text") or "").strip() or None),
                "structure_key": (str(a.get("structure_key") or "").strip() or None),
                "text": text,
                "is_secret": bool(a.get("is_secret", True)),
                "created_at": str(a.get("created_at") or now_iso),
                "depth": int(a.get("depth") or 1) if str(a.get("depth") or "").strip() else 1,
                "strategy": (str(a.get("strategy") or "").strip() or None),
            }

            clean.append(item)

        if not clean:
            return 0

        users = self._state.setdefault("users", {})
        user_entry = users.setdefault(uid, {"answers": [], "count": 0, "last_updated": None})

        lst = user_entry.setdefault("answers", [])
        if not isinstance(lst, list):
            lst = []
            user_entry["answers"] = lst

        lst.extend(clean)

        # 上限（暴走防止）: 200件
        max_items = 200
        if len(lst) > max_items:
            del lst[0 : len(lst) - max_items]

        user_entry["count"] = int(len(lst))
        user_entry["last_updated"] = now_iso

        self._save()
        return len(clean)

    def get_user_bundle(self, user_id: str) -> Dict[str, Any]:
        """生のユーザーエントリ（answers/last_updated/count）を返す。"""
        users = self._state.get("users") or {}
        entry = users.get(str(user_id), None)
        if isinstance(entry, dict):
            return entry
        return {"answers": [], "count": 0, "last_updated": None}

    def get_user_answers(self, user_id: str, *, limit: int = 8, include_secret: bool = True) -> List[Dict[str, Any]]:
        """最新の回答を返す（新しい順）。"""
        entry = self.get_user_bundle(user_id)
        answers = entry.get("answers") or []
        if not isinstance(answers, list) or not answers:
            return []

        out: List[Dict[str, Any]] = []
        for a in reversed(answers):
            if not isinstance(a, dict):
                continue
            if not include_secret and bool(a.get("is_secret", False)):
                continue
            out.append(a)
            if len(out) >= max(1, int(limit)):
                break
        return out

    # ---------- Internal ----------

    def _load(self) -> Dict[str, Any]:
        if not self.path.exists():
            self.path.parent.mkdir(parents=True, exist_ok=True)
            return {}
        try:
            raw = json.loads(self.path.read_text(encoding="utf-8"))
        except Exception:
            return {}
        return raw if isinstance(raw, dict) else {}

    def _save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self.path.with_suffix(".tmp")
        tmp.write_text(json.dumps(self._state, ensure_ascii=False, indent=2), encoding="utf-8")
        tmp.replace(self.path)
