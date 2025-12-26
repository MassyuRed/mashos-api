# -*- coding: utf-8 -*-
"""astor_deep_insight_question_store.py

Deep Insight Question Batch Store v0.2 (Supabase)

- Deep Insight の「提示した質問バッチ（3問）」を Supabase に保存する。
- free の 1日1回制限のために「今日のバッチ」を再利用できるようにする。
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

import datetime as _dt
import json
import logging
import os

import httpx

logger = logging.getLogger("deep_insight_batch_store")

SUPABASE_URL = os.getenv("SUPABASE_URL", "").rstrip("/")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")
BATCH_TABLE = os.getenv("COCOLON_DEEP_INSIGHT_BATCH_TABLE", "deep_insight_question_batches")

USE_SUPABASE = os.getenv("COCOLON_DEEP_INSIGHT_USE_SUPABASE", "true").strip().lower() in ("1", "true", "yes", "on")


def _has_supabase_config() -> bool:
    return bool(SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY)


def _sb_headers(*, prefer: Optional[str] = None) -> Dict[str, str]:
    h = {
        "apikey": SUPABASE_SERVICE_ROLE_KEY,
        "Authorization": f"Bearer {SUPABASE_SERVICE_ROLE_KEY}",
    }
    if prefer:
        h["Prefer"] = prefer
    return h


def _sb_headers_json(*, prefer: Optional[str] = None) -> Dict[str, str]:
    h = {
        "apikey": SUPABASE_SERVICE_ROLE_KEY,
        "Authorization": f"Bearer {SUPABASE_SERVICE_ROLE_KEY}",
        "Content-Type": "application/json",
    }
    if prefer:
        h["Prefer"] = prefer
    return h


def _parse_ts(ts: Any) -> Optional[_dt.datetime]:
    if not ts:
        return None
    s = str(ts).strip()
    if not s:
        return None
    try:
        return _dt.datetime.fromisoformat(s.replace("Z", "+00:00"))
    except Exception:
        return None


class DeepInsightServedStore:
    """互換APIを維持しつつ、内部を Supabase に寄せる。"""

    def __init__(self, path: Optional[Path] = None) -> None:
        self._use_supabase = bool(USE_SUPABASE and _has_supabase_config())

        # fallback (legacy local JSON)
        if path is None:
            here = Path(__file__).resolve()
            parents = list(here.parents)
            base = parents[3] if len(parents) > 3 else here.parent
            path = base / "ai" / "data" / "state" / "astor_deep_insight_served.json"
        self.path = path
        self._state: Dict[str, Any] = self._load_local() if not self._use_supabase else {}

    # ---------- Public API ----------

    def get_last_batch(self, user_id: str) -> List[str]:
        uid = str(user_id or "").strip()
        if not uid:
            return []

        if self._use_supabase:
            rec = self.get_latest_batch_record(uid)
            if not rec:
                return []
            qids = rec.get("question_ids") or []
            return [str(x) for x in qids if str(x).strip()]

        # local fallback
        entry = self._get_user_entry_local(uid)
        lst = entry.get("last_batch") or []
        if isinstance(lst, list):
            return [str(x) for x in lst if str(x).strip()]
        return []

    def get_recent_question_ids(self, user_id: str, *, limit: int = 50) -> Set[str]:
        # v0.2: 現状は DeepInsight 側で使っていないので、必要になったら実装拡張でOK
        # 互換のため残す
        uid = str(user_id or "").strip()
        if not uid:
            return set()

        if self._use_supabase:
            # 最新N件のバッチを取って flatten
            url = f"{SUPABASE_URL}/rest/v1/{BATCH_TABLE}"
            params = {
                "select": "question_ids",
                "user_id": f"eq.{uid}",
                "order": "generated_at.desc",
                "limit": str(max(1, int(limit))),
            }
            try:
                with httpx.Client(timeout=6.0) as client:
                    resp = client.get(url, headers=_sb_headers(), params=params)
                if resp.status_code >= 300:
                    return set()
                rows = resp.json()
                out: Set[str] = set()
                if isinstance(rows, list):
                    for r in rows:
                        if not isinstance(r, dict):
                            continue
                        qids = r.get("question_ids") or []
                        for q in qids:
                            s = str(q).strip()
                            if s:
                                out.add(s)
                return out
            except Exception:
                return set()

        # local fallback
        entry = self._get_user_entry_local(uid)
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

        if self._use_supabase:
            url = f"{SUPABASE_URL}/rest/v1/{BATCH_TABLE}"
            payload = {"user_id": uid, "question_ids": qids}
            try:
                with httpx.Client(timeout=6.0) as client:
                    resp = client.post(url, headers=_sb_headers_json(prefer="return=minimal"), json=payload)
                if resp.status_code >= 300:
                    logger.warning("Supabase batch insert failed: status=%s body=%s", resp.status_code, resp.text[:1200])
            except Exception as exc:
                logger.warning("Supabase batch insert failed (network): %s", exc)
            return

        # local fallback (旧仕様)
        self._record_batch_local(uid, qids)

    def reset_last_batch(self, user_id: str) -> None:
        # Supabase 版は「空バッチを挿入」でも良いが、現状呼ばれてないので noop でOK
        uid = str(user_id or "").strip()
        if not uid:
            return
        if self._use_supabase:
            self.record_batch(uid, [])
            return
        self._set_last_batch_local(uid, [])
        self._save_local()

    # ---------- Supabase helpers ----------

    def get_latest_batch_record(self, user_id: str) -> Optional[Dict[str, Any]]:
        """最新のバッチ（question_ids, generated_at）を返す。"""
        uid = str(user_id or "").strip()
        if not uid or not self._use_supabase:
            return None

        url = f"{SUPABASE_URL}/rest/v1/{BATCH_TABLE}"
        params = {
            "select": "question_ids,generated_at",
            "user_id": f"eq.{uid}",
            "order": "generated_at.desc",
            "limit": "1",
        }

        try:
            with httpx.Client(timeout=6.0) as client:
                resp = client.get(url, headers=_sb_headers(), params=params)
            if resp.status_code >= 300:
                return None
            rows = resp.json()
            if isinstance(rows, list) and rows and isinstance(rows[0], dict):
                return rows[0]
            return None
        except Exception:
            return None

    def latest_batch_is_today_utc(self, user_id: str) -> Tuple[bool, Optional[List[str]], Optional[str]]:
        """free制限用：最新バッチが「今日(UTC)」か判定し、今日ならquestion_idsも返す。"""
        rec = self.get_latest_batch_record(user_id)
        if not rec:
            return False, None, None

        ts = _parse_ts(rec.get("generated_at"))
        if ts is None:
            return False, None, None

        now = _dt.datetime.utcnow().replace(tzinfo=_dt.timezone.utc)
        if ts.tzinfo is None:
            ts = ts.replace(tzinfo=_dt.timezone.utc)

        if ts.date() != now.date():
            return False, None, None

        qids = rec.get("question_ids") or []
        qids2 = [str(x) for x in qids if str(x).strip()]
        return True, qids2, str(rec.get("generated_at") or "")

    # ---------- Local fallback (legacy) ----------

    def _load_local(self) -> Dict[str, Any]:
        if not self.path.exists():
            self.path.parent.mkdir(parents=True, exist_ok=True)
            return {}
        try:
            raw = json.loads(self.path.read_text(encoding="utf-8"))
        except Exception:
            return {}
        return raw if isinstance(raw, dict) else {}

    def _save_local(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self.path.with_suffix(".tmp")
        tmp.write_text(json.dumps(self._state, ensure_ascii=False, indent=2), encoding="utf-8")
        tmp.replace(self.path)

    def _get_user_entry_local(self, user_id: str) -> Dict[str, Any]:
        uid = str(user_id or "").strip()
        if not uid:
            return {"history": [], "last_batch": [], "count": 0, "last_updated": None}
        users = self._state.setdefault("users", {})
        entry = users.setdefault(uid, {"history": [], "last_batch": [], "count": 0, "last_updated": None})
        if isinstance(entry, dict):
            return entry
        users[uid] = {"history": [], "last_batch": [], "count": 0, "last_updated": None}
        return users[uid]

    def _set_last_batch_local(self, user_id: str, batch: List[str]) -> None:
        users = self._state.setdefault("users", {})
        entry = users.setdefault(user_id, {"history": [], "last_batch": [], "count": 0, "last_updated": None})
        if not isinstance(entry, dict):
            entry = {"history": [], "last_batch": [], "count": 0, "last_updated": None}
            users[user_id] = entry
        entry["last_batch"] = list(batch or [])

    def _record_batch_local(self, uid: str, qids: List[str]) -> None:
        now_iso = _dt.datetime.utcnow().replace(microsecond=0).isoformat() + "Z"
        users = self._state.setdefault("users", {})
        entry = users.setdefault(uid, {"history": [], "last_batch": [], "count": 0, "last_updated": None})

        hist = entry.setdefault("history", [])
        if not isinstance(hist, list):
            hist = []
            entry["history"] = hist

        for qid in qids:
            hist.append({"question_id": qid, "served_at": now_iso})

        max_items = 200
        if len(hist) > max_items:
            del hist[0 : len(hist) - max_items]

        entry["last_batch"] = qids
        entry["count"] = int(len(hist))
        entry["last_updated"] = now_iso
        self._save_local()
