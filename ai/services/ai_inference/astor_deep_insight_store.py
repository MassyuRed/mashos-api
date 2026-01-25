# -*- coding: utf-8 -*-
"""astor_deep_insight_store.py

Deep Insight Answer Store v0.2 (Supabase)

- Deep Insight の回答を Supabase (PostgREST) に保存する。
- 旧v0.1 のローカルJSON保存は、Supabase設定が無い場合のフォールバックとして残す。
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Optional, Set

import datetime as _dt
import json
import logging
import os

import httpx

logger = logging.getLogger("deep_insight_answer_store")

# Supabase
SUPABASE_URL = os.getenv("SUPABASE_URL", "").rstrip("/")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")
ANSWERS_TABLE = os.getenv("COCOLON_DEEP_INSIGHT_ANSWERS_TABLE", "deep_insight_answers")

# 明示的に Supabase を使いたい場合
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


def _parse_iso(ts: Any) -> Optional[_dt.datetime]:
    if not ts:
        return None
    s = str(ts).strip()
    if not s:
        return None
    try:
        return _dt.datetime.fromisoformat(s.replace("Z", "+00:00"))
    except Exception:
        return None


class DeepInsightAnswerStore:
    """Deep Insight Answer Store.

    Public API is kept compatible with v0.1:
    - append_answers(user_id, answers) -> int
    - get_user_bundle(user_id) -> {answers,count,last_updated}
    - get_user_answers(user_id, limit=..., include_secret=...) -> List[dict]
    """

    def __init__(self, path: Optional[Path] = None) -> None:
        self._use_supabase = bool(USE_SUPABASE and _has_supabase_config())

        # ---- fallback (legacy local JSON) ----
        if path is None:
            here = Path(__file__).resolve()
            parents = list(here.parents)
            base = parents[3] if len(parents) > 3 else here.parent
            path = base / "ai" / "data" / "state" / "astor_deep_insight_answers.json"
        self.path = path
        self._state: Dict[str, Any] = self._load_local() if not self._use_supabase else {}

    # ---------- Public API ----------

    def append_answers(self, user_id: str, answers: List[Dict[str, Any]]) -> int:
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
                "user_id": uid,
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

        # ---- Supabase ----
        if self._use_supabase:
            url = f"{SUPABASE_URL}/rest/v1/{ANSWERS_TABLE}"
            try:
                with httpx.Client(timeout=6.0) as client:
                    resp = client.post(
                        url,
                        headers=_sb_headers_json(prefer="return=minimal"),
                        json=clean,
                    )
                if resp.status_code >= 300:
                    logger.warning("Supabase insert failed: status=%s body=%s", resp.status_code, resp.text[:1200])
                    return 0
                return len(clean)
            except Exception as exc:
                logger.warning("Supabase insert failed (network): %s", exc)
                return 0

        # ---- local fallback ----
        return self._append_answers_local(uid, clean)

    def get_user_bundle(self, user_id: str) -> Dict[str, Any]:
        uid = str(user_id or "").strip()
        if not uid:
            return {"answers": [], "count": 0, "last_updated": None}

        if self._use_supabase:
            count = self._count_rows(uid, include_secret=True)
            last_updated = self._fetch_latest_created_at(uid, include_secret=True)
            return {"answers": [], "count": int(count), "last_updated": last_updated}

        # local fallback
        users = self._state.get("users") or {}
        entry = users.get(uid, None)
        if isinstance(entry, dict):
            return entry
        return {"answers": [], "count": 0, "last_updated": None}

    def get_user_answers(self, user_id: str, *, limit: int = 8, include_secret: bool = True) -> List[Dict[str, Any]]:
        uid = str(user_id or "").strip()
        if not uid:
            return []

        lim = max(1, int(limit))

        if self._use_supabase:
            url = f"{SUPABASE_URL}/rest/v1/{ANSWERS_TABLE}"
            fields = "question_id,question_text,structure_key,text,is_secret,created_at,depth,strategy"
            params: Dict[str, str] = {
                "select": fields,
                "user_id": f"eq.{uid}",
                "order": "created_at.desc",
                "limit": str(lim),
            }
            if not include_secret:
                params["is_secret"] = "eq.false"

            try:
                with httpx.Client(timeout=6.0) as client:
                    resp = client.get(url, headers=_sb_headers(), params=params)
                if resp.status_code >= 300:
                    logger.warning("Supabase select failed: status=%s body=%s", resp.status_code, resp.text[:1200])
                    return []
                data = resp.json()
                if isinstance(data, list):
                    return [x for x in data if isinstance(x, dict)]
                return []
            except Exception as exc:
                logger.warning("Supabase select failed (network): %s", exc)
                return []

        # local fallback
        return self._get_user_answers_local(uid, limit=lim, include_secret=include_secret)

    def get_answered_question_ids(self, user_id: str, *, limit: int = 5000, include_secret: bool = True) -> Set[str]:
        """Return a set of answered question_id for the user.

        Notes:
        - Used by question generation to avoid re-serving already answered questions.
        - For Supabase, fetches only question_id with pagination (best-effort).
        - include_secret=True means even secret answers will exclude the question from rotation.
        """

        uid = str(user_id or "").strip()
        if not uid:
            return set()

        max_rows = max(1, int(limit))

        if self._use_supabase:
            url = f"{SUPABASE_URL}/rest/v1/{ANSWERS_TABLE}"
            out: Set[str] = set()

            page_size = 1000
            offset = 0

            while offset < max_rows:
                lim = min(page_size, max_rows - offset)
                params: Dict[str, str] = {
                    "select": "question_id",
                    "user_id": f"eq.{uid}",
                    # skip null/empty ids
                    "question_id": "not.is.null",
                    "order": "created_at.desc",
                    "limit": str(lim),
                    "offset": str(offset),
                }
                if not include_secret:
                    params["is_secret"] = "eq.false"

                try:
                    with httpx.Client(timeout=6.0) as client:
                        resp = client.get(url, headers=_sb_headers(), params=params)
                    if resp.status_code >= 300:
                        logger.warning(
                            "Supabase select(question_id) failed: status=%s body=%s",
                            resp.status_code,
                            resp.text[:600],
                        )
                        break
                    rows = resp.json()
                    if not isinstance(rows, list) or not rows:
                        break
                    for r in rows:
                        if not isinstance(r, dict):
                            continue
                        qid = str(r.get("question_id") or "").strip()
                        if qid:
                            out.add(qid)
                    # stop when fewer than requested rows returned
                    if len(rows) < lim:
                        break
                    offset += len(rows)
                except Exception as exc:
                    logger.warning("Supabase select(question_id) failed (network): %s", exc)
                    break

            return out

        # local fallback
        users = self._state.get("users") or {}
        entry = users.get(uid, None)
        if not isinstance(entry, dict):
            return set()
        answers = entry.get("answers") or []
        if not isinstance(answers, list) or not answers:
            return set()

        out: Set[str] = set()
        for a in answers:
            if not isinstance(a, dict):
                continue
            if not include_secret and bool(a.get("is_secret", False)):
                continue
            qid = str(a.get("question_id") or "").strip()
            if qid:
                out.add(qid)
            if len(out) >= max_rows:
                break
        return out

    # ---------- Supabase helpers ----------

    def _fetch_latest_created_at(self, uid: str, *, include_secret: bool) -> Optional[str]:
        url = f"{SUPABASE_URL}/rest/v1/{ANSWERS_TABLE}"
        params: Dict[str, str] = {
            "select": "created_at",
            "user_id": f"eq.{uid}",
            "order": "created_at.desc",
            "limit": "1",
        }
        if not include_secret:
            params["is_secret"] = "eq.false"

        try:
            with httpx.Client(timeout=6.0) as client:
                resp = client.get(url, headers=_sb_headers(), params=params)
            if resp.status_code >= 300:
                return None
            rows = resp.json()
            if isinstance(rows, list) and rows:
                ts = rows[0].get("created_at")
                return str(ts) if ts else None
            return None
        except Exception:
            return None

    def _count_rows(self, uid: str, *, include_secret: bool) -> int:
        """PostgREST の Content-Range を使って count を取る。"""
        url = f"{SUPABASE_URL}/rest/v1/{ANSWERS_TABLE}"
        params: Dict[str, str] = {
            "select": "id",
            "user_id": f"eq.{uid}",
            "limit": "1",
        }
        if not include_secret:
            params["is_secret"] = "eq.false"

        try:
            with httpx.Client(timeout=6.0) as client:
                resp = client.get(url, headers=_sb_headers(prefer="count=exact"), params=params)
            if resp.status_code >= 300:
                return 0
            cr = resp.headers.get("Content-Range") or resp.headers.get("content-range") or ""
            # 例: "0-0/123"
            if "/" in cr:
                tail = cr.split("/")[-1].strip()
                return int(tail) if tail.isdigit() else 0
            return 0
        except Exception:
            return 0

    # ---------- Local fallback implementation (v0.1) ----------

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

    def _append_answers_local(self, uid: str, clean: List[Dict[str, Any]]) -> int:
        users = self._state.setdefault("users", {})
        user_entry = users.setdefault(uid, {"answers": [], "count": 0, "last_updated": None})

        lst = user_entry.setdefault("answers", [])
        if not isinstance(lst, list):
            lst = []
            user_entry["answers"] = lst

        lst.extend([{k: v for k, v in item.items() if k != "user_id"} for item in clean])

        # 旧仕様：暴走防止 200件（必要なら外してOK）
        max_items = 200
        if len(lst) > max_items:
            del lst[0 : len(lst) - max_items]

        now_iso = _dt.datetime.utcnow().replace(microsecond=0).isoformat() + "Z"
        user_entry["count"] = int(len(lst))
        user_entry["last_updated"] = now_iso
        self._save_local()
        return len(clean)

    def _get_user_answers_local(self, uid: str, *, limit: int, include_secret: bool) -> List[Dict[str, Any]]:
        users = self._state.get("users") or {}
        entry = users.get(uid, None)
        if not isinstance(entry, dict):
            return []
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
            if len(out) >= limit:
                break
        return out
