# -*- coding: utf-8 -*-
"""astor_deep_insight_question_store.py

Deep Insight Question Served Store v0.1

目的:
- Deep Insight の "questions" をユーザーに提示した履歴を軽量に保持する。
- "別の問いを受け取る" で同じ問いが連続しないようにするための補助。

v0.1 実装:
- まずはローカル JSON に保存（Render 等で永続化しない可能性がある点は了承の上）。
- 将来 Supabase テーブルへ移行できるよう、users -> history/last_batch の構造にしている。

保存先（既定）:
- mashos-api/ai/data/state/astor_deep_insight_served.json

備考:
- ここでいう "served" は "質問を返した" という意味で、回答の有無は問わない。
"""

from __future__ import annotations

import datetime as _dt
import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Set


class DeepInsightServedStore:
    def __init__(self, path: Optional[Path] = None) -> None:
        if path is None:
            here = Path(__file__).resolve()
            parents = list(here.parents)
            base = parents[3] if len(parents) > 3 else here.parent
            path = base / "ai" / "data" / "state" / "astor_deep_insight_served.json"
        self.path = path
        self._state: Dict[str, Any] = self._load()

    # ---------- Public API ----------

    def get_last_batch(self, user_id: str) -> List[str]:
        entry = self._get_user_entry(user_id)
        lst = entry.get("last_batch") or []
        if isinstance(lst, list):
            return [str(x) for x in lst if str(x).strip()]
        return []

    def get_recent_question_ids(self, user_id: str, *, limit: int = 50) -> Set[str]:
        """直近履歴から question_id を返す（集合）。"""
        entry = self._get_user_entry(user_id)
        hist = entry.get("history") or []
        if not isinstance(hist, list) or not hist:
            return set()
        out: List[str] = []
        for it in reversed(hist):
            if not isinstance(it, dict):
                continue
            qid = str(it.get("question_id") or "").strip()
            if not qid:
                continue
            out.append(qid)
            if len(out) >= max(1, int(limit)):
                break
        return set(out)

    def record_batch(self, user_id: str, question_ids: List[str]) -> None:
        uid = str(user_id or "").strip()
        if not uid:
            return

        qids = [str(x).strip() for x in (question_ids or []) if str(x).strip()]
        if not qids:
            # 何も出せていない場合も last_batch は空にする
            self._set_last_batch(uid, [])
            return

        now_iso = _dt.datetime.utcnow().replace(microsecond=0).isoformat() + "Z"

        users = self._state.setdefault("users", {})
        entry = users.setdefault(uid, {"history": [], "last_batch": [], "count": 0, "last_updated": None})

        hist = entry.setdefault("history", [])
        if not isinstance(hist, list):
            hist = []
            entry["history"] = hist

        for qid in qids:
            hist.append({"question_id": qid, "served_at": now_iso})

        # 上限（暴走防止）
        max_items = 200
        if len(hist) > max_items:
            del hist[0 : len(hist) - max_items]

        entry["last_batch"] = qids
        entry["count"] = int(len(hist))
        entry["last_updated"] = now_iso

        self._save()

    def reset_last_batch(self, user_id: str) -> None:
        uid = str(user_id or "").strip()
        if not uid:
            return
        self._set_last_batch(uid, [])
        self._save()

    # ---------- Internal ----------

    def _get_user_entry(self, user_id: str) -> Dict[str, Any]:
        uid = str(user_id or "").strip()
        if not uid:
            return {"history": [], "last_batch": [], "count": 0, "last_updated": None}
        users = self._state.setdefault("users", {})
        entry = users.setdefault(uid, {"history": [], "last_batch": [], "count": 0, "last_updated": None})
        if isinstance(entry, dict):
            return entry
        # 壊れてたら作り直す
        users[uid] = {"history": [], "last_batch": [], "count": 0, "last_updated": None}
        return users[uid]

    def _set_last_batch(self, user_id: str, batch: List[str]) -> None:
        users = self._state.setdefault("users", {})
        entry = users.setdefault(user_id, {"history": [], "last_batch": [], "count": 0, "last_updated": None})
        if not isinstance(entry, dict):
            entry = {"history": [], "last_batch": [], "count": 0, "last_updated": None}
            users[user_id] = entry
        entry["last_batch"] = list(batch or [])

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
