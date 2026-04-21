# -*- coding: utf-8 -*-
"""astor_myprofile_report.py

ASTOR MyProfile（月次）自己構造分析レポート生成
-------------------------------------------------

狙い
  - MyProfile の月次レポートを「読める構文」で安定生成する。
  - 現段階では LLM を必須にせず、ASTOR が保持している
    構造パターン（astor_structure_patterns.json）と
    観測ベースの文章を組み立てる。

注意
  - これは診断ではなく、観測に基づく仮説生成。
  - 外部（target=external）では secret を除外する。
"""

from __future__ import annotations

import datetime as _dt
import os
import re
import json
import hashlib
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import httpx

# MyProfile section text templates (Phase9+)
try:
    from myprofile_section_text_templates import (
        DEFAULT_MYPROFILE_SECTION_TEXT_TEMPLATE_ID,
        get_myprofile_section_phrases,
        safe_format as _safe_format,
    )
except Exception:  # pragma: no cover
    DEFAULT_MYPROFILE_SECTION_TEXT_TEMPLATE_ID = "myprofile_sections_ja_v1"

    def get_myprofile_section_phrases(template_id: str) -> Dict[str, Any]:
        return {}

    def _safe_format(template: str, **kwargs: Any) -> str:
        try:
            return str(template or "").format(**kwargs)
        except Exception:
            return str(template or "")


# 既存ストア（JSONローカル）
try:
    from astor_patterns import StructurePatternsStore
except Exception:  # pragma: no cover
    StructurePatternsStore = None  # type: ignore



# 構造辞書（ある場合のみ）
try:
    from structure_dict import load_structure_dict
except Exception:  # pragma: no cover
    load_structure_dict = None  # type: ignore


# Subscription / modes (Step 3)
try:
    from subscription import MyProfileMode, normalize_myprofile_mode
except Exception:  # pragma: no cover
    MyProfileMode = None  # type: ignore
    normalize_myprofile_mode = None  # type: ignore

# Self-structure dictionaries (used for Deep visual contract labels)
try:
    from analysis_engine.self_structure_engine.rules import ACTION_DICT, THINKING_DICT, ROLE_LABELS_JA
except Exception:  # pragma: no cover
    try:
        from self_structure_engine.rules import ACTION_DICT, THINKING_DICT, ROLE_LABELS_JA  # type: ignore
    except Exception:  # pragma: no cover
        ACTION_DICT = {}  # type: ignore
        THINKING_DICT = {}  # type: ignore
        ROLE_LABELS_JA = {}  # type: ignore


def _normalize_report_mode(x: Any) -> str:
    """Normalize report_mode into one of: standard / deep.

    Backward-compat:
    - structural -> deep
    - light -> standard (MyProfile API should gate this, but keep safe fallback)
    """
    # Prefer subscription.py normalizer if available
    if normalize_myprofile_mode is not None and MyProfileMode is not None:
        try:
            raw = normalize_myprofile_mode(x, default=MyProfileMode.STANDARD).value
            if str(raw) == "structural":
                return "deep"
            if str(raw) == "light":
                return "standard"
            return str(raw)
        except Exception:
            return "standard"

    # Fallback: string normalization
    s = str(x or "").strip()
    if not s:
        return "standard"
    s2 = s.lower()
    if s2 in ("standard", "deep"):
        return s2
    if s2 in ("structural",):
        return "deep"
    if s2 in ("light",):
        return "standard"
    # common JP labels
    if s in ("ライト", "Light"):
        return "standard"
    if s in ("スタンダード", "Standard"):
        return "standard"
    if s in ("ディープ", "Deep", "Structural", "ストラクチュラル"):
        return "deep"
    return "standard"


# ---------- Supabase (MyProfile source of truth) ----------

SUPABASE_URL = os.getenv("SUPABASE_URL", "").rstrip("/")
SUPABASE_SERVICE_ROLE_KEY = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")


def _has_supabase_config() -> bool:
    return bool(SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY)


def _sb_headers_json(*, prefer: Optional[str] = None) -> Dict[str, str]:
    h = {
        "apikey": SUPABASE_SERVICE_ROLE_KEY,
        "Authorization": f"Bearer {SUPABASE_SERVICE_ROLE_KEY}",
        "Content-Type": "application/json",
    }
    if prefer:
        h["Prefer"] = prefer
    return h


def _sb_headers(*, prefer: Optional[str] = None) -> Dict[str, str]:
    h = {
        "apikey": SUPABASE_SERVICE_ROLE_KEY,
        "Authorization": f"Bearer {SUPABASE_SERVICE_ROLE_KEY}",
    }
    if prefer:
        h["Prefer"] = prefer
    return h


STRENGTH_SCORE: Dict[str, float] = {"weak": 1.0, "medium": 2.0, "strong": 3.0}

JP_TO_EMO_EN: Dict[str, str] = {
    "喜び": "Joy",
    "悲しみ": "Sadness",
    "不安": "Anxiety",
    "怒り": "Anger",
    "平穏": "Calm",
    "落ち着き": "Calm",
    "自己理解": "SelfInsight",
}

SELF_INSIGHT_EMOTION_LABELS = {"SelfInsight", "自己理解"}


MYPROFILE_REPORT_SCHEMA_VERSION = "myprofile.report.v5"

THINKING_LABELS_JA: Dict[str, str] = {
    str(k): str((v or {}).get("label_ja") or k)
    for k, v in (THINKING_DICT.items() if isinstance(THINKING_DICT, dict) else [])
}
ACTION_LABELS_JA: Dict[str, str] = {
    str(k): str((v or {}).get("label_ja") or k)
    for k, v in (ACTION_DICT.items() if isinstance(ACTION_DICT, dict) else [])
}


def _to_iso_z(dt: _dt.datetime) -> str:
    # Ensure tz-aware (treat naive timestamps as UTC to avoid compare errors downstream)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=_dt.timezone.utc)
    dtu = dt.astimezone(_dt.timezone.utc)
    return dtu.isoformat(timespec="milliseconds").replace("+00:00", "Z")


def _normalize_emotion_details(row: Dict[str, Any]) -> List[Tuple[str, float]]:
    """Return list of (emotion_label_en, intensity_score[1..3])."""
    out: List[Tuple[str, float]] = []

    details = row.get("emotion_details")
    if isinstance(details, list):
        for it in details:
            if not isinstance(it, dict):
                continue
            t = str(it.get("type") or "").strip()
            if not t:
                continue
            s = str(it.get("strength") or "medium").strip().lower()
            if s not in STRENGTH_SCORE:
                s = "medium"

            en = JP_TO_EMO_EN.get(t, t)
            out.append((en, float(STRENGTH_SCORE.get(s, 2.0))))
        return out

    emos = row.get("emotions")
    if isinstance(emos, list):
        for t in emos:
            tt = str(t or "").strip()
            if not tt:
                continue
            en = JP_TO_EMO_EN.get(tt, tt)
            out.append((en, 2.0))
        return out

    return out


def _fetch_emotion_rows(user_id: str, *, start: _dt.datetime, end: _dt.datetime) -> List[Dict[str, Any]]:
    """Fetch emotion rows for period.

    NOTE: This is sync (called from sync report builder).
    """
    if not _has_supabase_config():
        return []

    uid = str(user_id or "").strip()
    if not uid:
        return []

    start_iso = _to_iso_z(start)
    end_iso = _to_iso_z(end)

    url = f"{SUPABASE_URL}/rest/v1/emotions"
    params = [
        ("select", "created_at,emotions,emotion_details,memo,memo_action,is_secret"),
        ("user_id", f"eq.{uid}"),
        ("created_at", f"gte.{start_iso}"),
        ("created_at", f"lte.{end_iso}"),
        ("order", "created_at.asc"),
    ]

    try:
        with httpx.Client(timeout=6.0) as client:
            resp = client.get(url, headers=_sb_headers(), params=params)
    except Exception:
        return []

    if resp.status_code != 200:
        return []

    try:
        data = resp.json()
        return data if isinstance(data, list) else []
    except Exception:
        return []


EMO_JA = {
    "Joy": "喜び",
    "Sadness": "悲しみ",
    "Anxiety": "不安",
    "Anger": "怒り",
    "Calm": "落ち着き",
    "SelfInsight": "自己理解",
    "自己理解": "自己理解",
}


def emo_label_ja(x: Optional[str]) -> str:
    s = str(x or "").strip()
    return EMO_JA.get(s, s or "感情")


def parse_period_days(period: Optional[str]) -> int:
    """"7d","30d","12w","3m" をざっくり日数へ。"""
    if not period:
        return 30
    s = str(period).strip().lower()
    if not s:
        return 30
    try:
        if s.endswith("d"):
            return max(1, int(s[:-1] or "30"))
        if s.endswith("w"):
            return max(1, int(s[:-1] or "1") * 7)
        if s.endswith("m"):
            return max(1, int(s[:-1] or "1") * 30)
        return max(1, int(s))
    except Exception:
        return 30


def is_myprofile_monthly_report_instruction(text: str) -> bool:
    """/mymodel/infer の instruction が「月次自己構造レポ生成」かを判定。"""
    t = str(text or "")
    # なるべく事故らない、広めの判定
    keys = [
        "自己構造分析レポート",
        "自己構造レポート",
        "MyProfile",
        "月次",
        "【自己構造分析レポート",
    ]
    hit = sum(1 for k in keys if k in t)
    return hit >= 2


def _parse_ts(ts: Any) -> Optional[_dt.datetime]:
    if not ts:
        return None
    try:
        dt = _dt.datetime.fromisoformat(str(ts).replace("Z", "+00:00"))
        # Supabase may return naive timestamps depending on column type / serializer.
        # Normalize to tz-aware UTC to avoid mixing naive/aware datetimes.
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=_dt.timezone.utc)
        return dt
    except Exception:
        return None


@dataclass
class StructurePeriodView:
    key: str
    count: int
    avg_intensity: float
    avg_score: float
    top_emotions: List[str]
    sample_memos: List[str]


def _intensity_label(avg_intensity: float) -> str:
    if avg_intensity >= 2.6:
        return "強め"
    if avg_intensity >= 1.9:
        return "中くらい"
    if avg_intensity >= 1.2:
        return "やわらかめ"
    return "かなりやわらかめ"


def _load_structures_map(user_id: str) -> Dict[str, Any]:
    if StructurePatternsStore is None:
        return {}
    try:
        store = StructurePatternsStore()
        user_entry = store.get_user_patterns(user_id)
        return user_entry.get("structures", {}) or {}
    except Exception:
        return {}


# ---------- MyProfile v2: direct matching from raw logs ----------

_STANDARD_DICT_CACHE: Optional[Dict[str, Dict[str, Any]]] = None


def _load_standard_structure_dict() -> Dict[str, Dict[str, Any]]:
    """Load Standard structure dict (ai/data/config/astor_structure_dict.json)."""
    global _STANDARD_DICT_CACHE
    if _STANDARD_DICT_CACHE is not None:
        return _STANDARD_DICT_CACHE

    here = Path(__file__).resolve()
    ai_root = here.parents[2]
    candidates = [
        ai_root / "data" / "config" / "astor_structure_dict.json",
        Path.cwd() / "ai" / "data" / "config" / "astor_structure_dict.json",
    ]
    for p in candidates:
        if not p.exists():
            continue
        try:
            raw = json.loads(p.read_text(encoding="utf-8"))
            if isinstance(raw, dict):
                _STANDARD_DICT_CACHE = raw
                return _STANDARD_DICT_CACHE
        except Exception:
            continue

    _STANDARD_DICT_CACHE = {}
    return _STANDARD_DICT_CACHE


def _collapse_ws(text: str) -> str:
    return re.sub(r"\s+", " ", str(text or "").strip())


def _excerpt(text: str, limit: int = 96) -> str:
    t = _collapse_ws(text)
    return t[:limit] + ("…" if len(t) > limit else "")


def _build_event_excerpt(thought: str, action: str, self_insight: str = "", deep_text: str = "") -> str:
    parts: List[str] = []
    if thought:
        parts.append(f"思考: {_excerpt(thought)}")
    if action:
        parts.append(f"行動: {_excerpt(action)}")
    if self_insight:
        parts.append(f"理解: {_excerpt(self_insight)}")
    if deep_text:
        parts.append(f"一問一答: {_excerpt(deep_text)}")
    return " / ".join(parts)[:220]


def _is_self_insight_row(details: List[Tuple[str, float]]) -> bool:
    return any((lbl in SELF_INSIGHT_EMOTION_LABELS) for (lbl, _) in (details or []))


def _parse_created_at(row: Dict[str, Any]) -> Optional[_dt.datetime]:
    return _parse_ts(row.get("created_at"))


def _build_text_events_from_emotions(
    rows: List[Dict[str, Any]],
    *,
    start: _dt.datetime,
    end: _dt.datetime,
    include_secret: bool,
) -> Tuple[List[Dict[str, Any]], List[str]]:
    """Return (events, self_insight_quotes).

    events: each event includes combined_text, emotions[], intensity, excerpt, ts.
    """
    events: List[Dict[str, Any]] = []
    self_insights: List[Tuple[_dt.datetime, str]] = []

    for row in rows or []:
        if not isinstance(row, dict):
            continue
        if (not include_secret) and bool(row.get("is_secret", False)):
            continue
        ts = _parse_created_at(row)
        if ts is None:
            continue
        if ts < start or ts >= end:
            continue

        thought = str(row.get("memo") or "").strip()
        action = str(row.get("memo_action") or "").strip()

        details = _normalize_emotion_details(row)
        labels = [lbl for (lbl, _) in details if lbl]
        # intensity: use the strongest selected emotion as the representative
        inten = 0.0
        if details:
            inten = max(float(x[1]) for x in details)

        if _is_self_insight_row(details):
            if thought:
                self_insights.append((ts, thought))
            combined = "\n".join([thought, action]).strip()
            events.append(
                {
                    "ts": ts,
                    "kind": "self_insight",
                    "combined_text": combined,
                    "thought": thought,
                    "action": action,
                    "emotions": labels,
                    "intensity": 0.0,
                    "excerpt": _build_event_excerpt(thought, action, self_insight=thought),
                }
            )
            continue

        combined = "\n".join([thought, action]).strip()
        if not combined:
            # no text -> skip for matching, but keep for emotion counting? (skip)
            continue

        events.append(
            {
                "ts": ts,
                "kind": "emotion",
                "combined_text": combined,
                "thought": thought,
                "action": action,
                "emotions": labels,
                "intensity": inten,
                "excerpt": _build_event_excerpt(thought, action),
            }
        )

    self_insights.sort(key=lambda x: x[0])
    quotes = [q for _, q in self_insights[-2:]]  # latest 1~2
    return events, quotes


def _score_standard_one(
    *,
    conf: Dict[str, Any],
    emotions: List[str],
    intensity: float,
    text: str,
) -> Tuple[float, List[str]]:
    base = float(conf.get("base_weight", 0.0))
    keyword_weight = float(conf.get("keyword_weight", 0.5))

    ew: Dict[str, float] = conf.get("emotion_weights") or {}
    norm_intensity = max(0.0, min((float(intensity or 0.0) - 1.0) / 2.0, 1.0))
    emotion_score = 0.0
    if emotions and ew and norm_intensity > 0:
        for lbl in emotions:
            if lbl in ew:
                emotion_score = max(emotion_score, float(ew.get(lbl) or 0.0) * norm_intensity)

    kw_list: List[str] = conf.get("keywords") or []
    kw_hits: List[str] = []
    memo_score = 0.0
    if text and kw_list:
        for kw in kw_list:
            if kw and kw in text:
                kw_hits.append(kw)
        if kw_hits:
            memo_score = min(len(kw_hits) / max(len(kw_list), 1), 1.0)

    score = base + emotion_score + memo_score * keyword_weight
    return score, kw_hits[:4]


def _score_structural_one(*, entry: Dict[str, Any], text: str) -> Tuple[float, List[str]]:
    kw_list: List[str] = entry.get("memo_keywords") or []
    kw_hits: List[str] = []
    memo_score = 0.0
    if text and kw_list:
        for kw in kw_list:
            if kw and kw in text:
                kw_hits.append(kw)
        if kw_hits:
            memo_score = min(len(kw_hits) / max(len(kw_list), 1), 1.0)
    # simple, stable scoring (avoid exposing internals)
    base = 0.05
    keyword_weight = 0.75
    score = base + memo_score * keyword_weight
    return score, kw_hits[:4]


def _collect_period_views_from_events(
    events: List[Dict[str, Any]],
    *,
    mode: str,
    match_threshold: float = 0.20,
    max_samples: int = 2,
) -> List[StructurePeriodView]:
    """Compute StructurePeriodView from raw text events."""

    out: List[StructurePeriodView] = []
    m = str(mode or "standard").strip().lower()

    if m in ("structural", "deep") and load_structure_dict is not None:
        entries = load_structure_dict() or {}
        for key, entry in entries.items():
            if not isinstance(entry, dict):
                continue
            cnt = 0
            score_sum = 0.0
            inten_sum = 0.0
            inten_n = 0
            emo_counter: Dict[str, int] = {}
            memos: List[str] = []
            for ev in events or []:
                text = str(ev.get("combined_text") or "")
                if not text:
                    continue
                score, _kw = _score_structural_one(entry=entry, text=text)
                if score < match_threshold:
                    continue
                cnt += 1
                score_sum += float(score)
                inten = float(ev.get("intensity") or 0.0)
                if inten > 0:
                    inten_sum += inten
                    inten_n += 1
                for emo in (ev.get("emotions") or []):
                    if emo:
                        emo_counter[str(emo)] = emo_counter.get(str(emo), 0) + 1
                ex = str(ev.get("excerpt") or "").strip()
                if ex and ex not in memos and len(memos) < max_samples:
                    memos.append(ex)

            if cnt <= 0:
                continue
            avg_score = (score_sum / cnt) if cnt else 0.0
            avg_intensity = (inten_sum / inten_n) if inten_n > 0 else 0.0
            top_emotions = [k for k, _ in sorted(emo_counter.items(), key=lambda kv: kv[1], reverse=True)[:2]]
            out.append(
                StructurePeriodView(
                    key=str(key),
                    count=cnt,
                    avg_intensity=avg_intensity,
                    avg_score=avg_score,
                    top_emotions=top_emotions,
                    sample_memos=memos[:max_samples],
                )
            )

        out.sort(key=lambda v: (v.count, v.avg_intensity, v.avg_score), reverse=True)
        return out

    # Standard mode
    defs = _load_standard_structure_dict()
    for key, conf in (defs or {}).items():
        if not isinstance(conf, dict):
            continue
        cnt = 0
        score_sum = 0.0
        inten_sum = 0.0
        inten_n = 0
        emo_counter: Dict[str, int] = {}
        memos: List[str] = []
        for ev in events or []:
            text = str(ev.get("combined_text") or "")
            if not text:
                continue
            emotions = [str(x) for x in (ev.get("emotions") or []) if str(x).strip()]
            intensity = float(ev.get("intensity") or 0.0)
            score, _kw = _score_standard_one(conf=conf, emotions=emotions, intensity=intensity, text=text)
            if score < match_threshold:
                continue
            cnt += 1
            score_sum += float(score)
            if intensity > 0:
                inten_sum += intensity
                inten_n += 1
            for emo in emotions:
                emo_counter[emo] = emo_counter.get(emo, 0) + 1
            ex = str(ev.get("excerpt") or "").strip()
            if ex and ex not in memos and len(memos) < max_samples:
                memos.append(ex)

        if cnt <= 0:
            continue
        avg_score = (score_sum / cnt) if cnt else 0.0
        avg_intensity = (inten_sum / inten_n) if inten_n > 0 else 0.0
        top_emotions = [k for k, _ in sorted(emo_counter.items(), key=lambda kv: kv[1], reverse=True)[:2]]
        out.append(
            StructurePeriodView(
                key=str(key),
                count=cnt,
                avg_intensity=avg_intensity,
                avg_score=avg_score,
                top_emotions=top_emotions,
                sample_memos=memos[:max_samples],
            )
        )

    out.sort(key=lambda v: (v.count, v.avg_intensity, v.avg_score), reverse=True)
    return out


def _collect_period_views(
    structures_map: Dict[str, Any],
    *,
    start: _dt.datetime,
    end: _dt.datetime,
    include_secret: bool,
) -> List[StructurePeriodView]:
    out: List[StructurePeriodView] = []

    for entry in (structures_map or {}).values():
        if not isinstance(entry, dict):
            continue
        key = str(entry.get("structure_key") or "").strip()
        if not key:
            continue
        triggers = entry.get("triggers") or []
        if not isinstance(triggers, list) or not triggers:
            continue

        cnt = 0
        score_sum = 0.0
        inten_sum = 0.0
        inten_n = 0
        emo_counter: Dict[str, int] = {}
        memos: List[str] = []

        for t in triggers:
            if not isinstance(t, dict):
                continue
            if (not include_secret) and bool(t.get("is_secret", False)):
                continue
            ts = _parse_ts(t.get("ts"))
            if ts is None:
                continue
            if ts < start or ts >= end:
                continue

            cnt += 1

            try:
                score_sum += float(t.get("score") or 0.0)
            except Exception:
                pass

            inten = t.get("intensity")
            if inten is not None:
                try:
                    inten_sum += float(inten)
                    inten_n += 1
                except Exception:
                    pass

            emo = str(t.get("emotion") or "").strip()
            if emo:
                emo_counter[emo] = emo_counter.get(emo, 0) + 1

            me = str(t.get("memo_excerpt") or "").strip()
            if me:
                # 同じ行の重複を減らす
                if me not in memos:
                    memos.append(me)

        if cnt <= 0:
            continue

        avg_score = (score_sum / cnt) if cnt else 0.0
        avg_intensity = (inten_sum / inten_n) if inten_n > 0 else 0.0

        top_emotions = [k for k, _ in sorted(emo_counter.items(), key=lambda kv: kv[1], reverse=True)[:2]]

        out.append(
            StructurePeriodView(
                key=key,
                count=cnt,
                avg_intensity=avg_intensity,
                avg_score=avg_score,
                top_emotions=top_emotions,
                sample_memos=memos[:2],
            )
        )

    out.sort(key=lambda v: (v.count, v.avg_intensity, v.avg_score), reverse=True)
    return out


def _short_structure_gloss(struct_key: str) -> str:
    """構造辞書があれば、短い説明（1行）を返す。"""
    if not load_structure_dict:
        return ""
    try:
        d = load_structure_dict() or {}
        entry = d.get(struct_key)
        if not isinstance(entry, dict):
            return ""
        # まずは「定義」を短く
        secs = entry.get("sections") or {}
        defin = str(secs.get("定義") or "").strip()
        if defin:
            # 先頭1文っぽく切る（長すぎないように）
            defin = re.split(r"[。\n]", defin)[0].strip()
            if defin:
                return defin[:64]
    except Exception:
        return ""
    return ""


def _guess_domain_hints(struct_keys: List[str]) -> Dict[str, List[str]]:
    """領域別メモ用の雑な割り当て（断定しない前提の“ヒント”）。"""
    buckets = {
        "仕事": [],
        "対人": [],
        "孤独": [],
        "挑戦": [],
        "評価": [],
    }

    for k in struct_keys:
        if any(w in k for w in ["評価", "承認", "比較"]):
            buckets["評価"].append(k)
        if any(w in k for w in ["罪悪感", "承認", "羞恥", "対人"]):
            buckets["対人"].append(k)
        if any(w in k for w in ["孤独", "寂", "疎外"]):
            buckets["孤独"].append(k)
        if any(w in k for w in ["挑戦", "達成", "無力", "停滞"]):
            buckets["挑戦"].append(k)
        # 仕事は万能すぎるので、挑戦/評価寄りを補助
        if any(w in k for w in ["達成", "評価", "無力", "焦り"]):
            buckets["仕事"].append(k)

    # 重複は除く
    for kk in list(buckets.keys()):
        seen = set()
        uniq = []
        for x in buckets[kk]:
            if x in seen:
                continue
            uniq.append(x)
            seen.add(x)
        buckets[kk] = uniq[:2]
    return buckets


def _extract_quoted_terms(text: str, limit: int = 8) -> List[str]:
    """『...』で囲まれた語を抽出（MyProfileレポ内の構造キー想定）。"""
    if not text:
        return []
    terms: List[str] = []
    for m in re.finditer(r"『([^』]{1,48})』", str(text)):
        t = str(m.group(1) or "").strip()
        if not t:
            continue
        if t in terms:
            continue
        terms.append(t)
        if len(terms) >= limit:
            break
    return terms


def _extract_prev_report_summary(prev_text: str, *, summary_heading: str = "【要点（答え）】") -> Dict[str, Any]:
    """前回レポ本文から、差分要約に使える“要点”を抜き出す（ルールベース）。

    - summary_heading（デフォ: 【要点（答え）】）ブロックの行（核/崩れ/安定）を優先
    - 見つからない場合は、本文全体から『...』語を拾う

    NOTE:
      - テンプレ差し替えで summary_heading が変わる可能性があるため、
        default見出しも併せて探索する（互換性のため）。
    """
    out: Dict[str, Any] = {
        "core_line": "",
        "shaky_line": "",
        "steady_line": "",
        "keys": [],
    }
    if not prev_text:
        return out

    lines0 = [str(x).strip() for x in str(prev_text).splitlines()]
    lines = [l for l in lines0 if l is not None]

    # 【要点（答え）】セクションの抽出（テンプレ差し替えに備えて候補を複数持つ）
    candidates = []
    if summary_heading:
        candidates.append(str(summary_heading))
    candidates.append("【要点（答え）】")
    candidates = [c for i, c in enumerate(candidates) if c and c not in candidates[:i]]

    sidx = -1
    for i, l in enumerate(lines):
        if any(c in l for c in candidates):
            sidx = i
            break

    bullet_lines: List[str] = []
    if sidx >= 0:
        for j in range(sidx + 1, min(sidx + 12, len(lines))):
            l = lines[j].strip()
            if not l:
                break
            # 次の大見出しに入ったら終わる
            if re.match(r"^\s*\d\s*[\.\)\:：]", l) or l.startswith("【"):
                break
            bullet_lines.append(l)

    # 分類（少し広め）
    for l in bullet_lines:
        if (not out["core_line"]) and any(k in l for k in ["核", "中心"]):
            out["core_line"] = l
        if (not out["shaky_line"]) and any(k in l for k in ["崩れ", "引き金", "揺れ"]):
            out["shaky_line"] = l
        if (not out["steady_line"]) and any(k in l for k in ["安定", "整え", "回復"]):
            out["steady_line"] = l

    keys = _extract_quoted_terms("\n".join(bullet_lines), limit=8)
    if not keys:
        keys = _extract_quoted_terms(prev_text, limit=8)

    out["keys"] = keys
    return out


def _build_prev_diff_summary_lines(
    *,
    prev_text: str,
    current_top_keys: List[str],
    current_core_line: str,
    current_shaky_line: str,
    current_steady_line: str,
    deltas: List[Tuple[str, int, float]],
    phrases: Optional[Dict[str, Any]] = None,
) -> List[str]:
    """前回本文も参照して、差分を“要約差分”として返す。

    目的:
      - 人が欲しい「更新点」を先に明示する
      - ただし人格の断定はしない（観測→仮説の範囲）

    phrases:
      - Phase9+ のセクション固定文テンプレ（無い場合は従来互換の固定文で生成）
    """
    if not prev_text:
        return []

    ph = phrases or {}

    def P(key: str, default: str) -> str:
        v = ph.get(key)
        return str(v) if isinstance(v, str) and v else default

    def PF(key: str, default: str, **kwargs: Any) -> str:
        return _safe_format(P(key, default), **kwargs).strip()

    prev = _extract_prev_report_summary(prev_text, summary_heading=P("summary_title", "【要点（答え）】"))
    prev_keys: List[str] = list(prev.get("keys") or [])

    def _clean(line: str) -> str:
        return str(line or "").lstrip("・").strip()

    prev_core = _clean(str(prev.get("core_line") or ""))
    prev_shaky = _clean(str(prev.get("shaky_line") or ""))
    prev_steady = _clean(str(prev.get("steady_line") or ""))

    cur_core = _clean(str(current_core_line or ""))
    cur_shaky = _clean(str(current_shaky_line or ""))
    cur_steady = _clean(str(current_steady_line or ""))

    cur_keys = [k for k in (current_top_keys or []) if k][:3]
    prev_main = prev_keys[0] if prev_keys else ""
    cur_main = cur_keys[0] if cur_keys else ""

    lines: List[str] = []
    lines.append(P("diff_summary_title", "【差分の要約（前回→今回）】"))

    # 1) 核（答え）の比較（前回要点が取れていれば優先）
    if prev_core and cur_core:
        lines.append(PF("diff_core_compare", "・核の要点: 前回 {prev} / 今回 {cur}", prev=prev_core, cur=cur_core))
    else:
        if prev_main and cur_main:
            if prev_main != cur_main:
                lines.append(PF("diff_center_move", "・中心テーマ: 『{prev}』→『{cur}』へ移動した可能性", prev=prev_main, cur=cur_main))
            else:
                lines.append(PF("diff_center_same", "・中心テーマ: 『{cur}』が継続している可能性", cur=cur_main))
        elif cur_main:
            lines.append(PF("diff_center_cur_is_core", "・中心テーマ: 今回は『{cur}』が核になっている可能性", cur=cur_main))
        else:
            lines.append(P("diff_center_unknown", "・中心テーマ: 今月は入力が少ないため、中心テーマはまだ特定できません"))

    # 2) 崩れ/安定の要点比較（取れたときだけ）
    if prev_shaky and cur_shaky:
        lines.append(PF("diff_shaky_compare", "・崩れ条件: 前回 {prev} / 今回 {cur}", prev=prev_shaky, cur=cur_shaky))
    if prev_steady and cur_steady:
        lines.append(PF("diff_steady_compare", "・安定条件: 前回 {prev} / 今回 {cur}", prev=prev_steady, cur=cur_steady))

    # 3) 新規/減衰（短く）
    if cur_keys and prev_keys:
        new_keys = [k for k in cur_keys if k not in prev_keys]
        faded_keys = [k for k in prev_keys[:3] if k not in cur_keys]
        if new_keys:
            lines.append(PF("diff_new_key", "・新しく目立ち始めた: 『{key}』", key=new_keys[0]))
        if faded_keys:
            lines.append(PF("diff_faded_key", "・落ち着いた可能性: 『{key}』", key=faded_keys[0]))

    # 4) データ差分（1行だけ）
    for k, dc, di in (deltas or [])[:8]:
        if dc == 0 and abs(di) < 0.12:
            continue
        sign = "増えた" if dc > 0 else "減った"
        lines.append(PF("diff_data_line", "・データ差分: 『{key}』が{sign}（回数 {count:+d} / 強度差 {intensity:+.1f}）", key=k, sign=sign, count=dc, intensity=di))
        break

    # 余計に長くしない
    return lines[:8]


def _build_myprofile_monthly_report_fallback(
    *,
    user_id: str,
    period: str = "30d",
    report_mode: Optional[str] = "standard",
    include_secret: bool = True,
    now: Optional[_dt.datetime] = None,
    prev_report_text: Optional[str] = None,
    section_text_template_id: Optional[str] = None,
) -> Tuple[str, Dict[str, Any]]:
    """月次自己構造分析レポート本文と meta を返す。

    Phase9+:
      - 固定文（見出し/セクション文言/定型フレーズ）を template_id で差し替え可能にする。
    """
    uid = str(user_id or "").strip()

    # --- template selection ---
    def _resolve_section_template_id(override: Optional[str]) -> str:
        if override:
            return str(override).strip()
        # monthly 専用があれば優先
        tid = (os.getenv("MYPROFILE_MONTHLY_SECTION_TEXT_TEMPLATE_ID") or "").strip()
        if tid:
            return tid
        tid = (os.getenv("MYPROFILE_SECTION_TEXT_TEMPLATE_ID") or "").strip()
        if tid:
            return tid
        return DEFAULT_MYPROFILE_SECTION_TEXT_TEMPLATE_ID

    section_tid = _resolve_section_template_id(section_text_template_id)
    phrases = get_myprofile_section_phrases(section_tid)

    def P(key: str, default: str) -> str:
        v = phrases.get(key)
        return str(v) if isinstance(v, str) and v else default

    def PL(key: str, default: List[str]) -> List[str]:
        v = phrases.get(key)
        if isinstance(v, list):
            return [str(x) for x in v if str(x).strip()]
        return list(default)

    def PF(key: str, default: str, **kwargs: Any) -> str:
        return _safe_format(P(key, default), **kwargs).strip()

    report_title = P("report_title", "【自己構造分析レポート（月次）】")

    if not uid:
        return (
            f"{report_title}\n\n{P('error_no_user_id', '（ユーザーIDが指定されていないため生成できませんでした）')}",
            {"engine": "astor_myprofile_report", "status": "no_user_id", "section_text_template_id": section_tid},
        )

    days = parse_period_days(period)
    mode = _normalize_report_mode(report_mode)
    # Spec v2: definitions are only appended in Structural mode
    use_structure_gloss = (mode in ("structural", "deep"))
    # Legacy deep enhancer is not used for Spec v2; keep the variable for meta only.
    use_mashlogic = False
    now_dt = now or _dt.datetime.utcnow().replace(microsecond=0, tzinfo=_dt.timezone.utc)
    if now_dt.tzinfo is None:
        now_dt = now_dt.replace(tzinfo=_dt.timezone.utc)

    end = now_dt
    start = end - _dt.timedelta(days=max(days, 1))
    prev_end = start
    prev_start = prev_end - _dt.timedelta(days=max(days, 1))

    # Materials (Spec v2): thought/action logs + self-insight

    analysis_source = "supabase_emotions" if _has_supabase_config() else "patterns_store"

    # Prefer raw logs (Supabase emotions) for v2; fallback to legacy patterns store when unavailable.
    cur_rows = _fetch_emotion_rows(uid, start=start, end=end)
    prev_rows = _fetch_emotion_rows(uid, start=prev_start, end=prev_end)

    cur_events, self_insight_quotes = _build_text_events_from_emotions(cur_rows, start=start, end=end, include_secret=include_secret)
    prev_events, _ = _build_text_events_from_emotions(prev_rows, start=prev_start, end=prev_end, include_secret=include_secret)


    cur_views = _collect_period_views_from_events(cur_events, mode=mode)
    prev_views = _collect_period_views_from_events(prev_events, mode=mode)

    if not cur_views:
        # legacy fallback
        analysis_source = "patterns_store"
        self_insight_quotes = []
        structures_map = _load_structures_map(uid)
        cur_views = _collect_period_views(structures_map, start=start, end=end, include_secret=include_secret)
        prev_views = _collect_period_views(structures_map, start=prev_start, end=prev_end, include_secret=include_secret)

    prev_map = {v.key: v for v in prev_views}

    # top structures
    top = cur_views[:3]
    top_keys = [v.key for v in top]


    # 差分
    deltas: List[Tuple[str, int, float]] = []  # key, delta_count, delta_intensity
    for v in cur_views[:8]:
        pv = prev_map.get(v.key)
        dc = v.count - (pv.count if pv else 0)
        di = v.avg_intensity - (pv.avg_intensity if pv else 0.0)
        deltas.append((v.key, dc, di))
    deltas.sort(key=lambda x: (abs(x[1]), abs(x[2])), reverse=True)

    # --- summary bullets ---
    # Spec v2: focus on thought/action alignment as "崩れ条件".
    def _has_any(text: str, words: List[str]) -> bool:
        t = str(text or "")
        return any(w in t for w in words)

    mismatch_events: List[Dict[str, Any]] = []
    for ev in cur_events:
        if str(ev.get("kind")) != "emotion":
            continue
        th = str(ev.get("thought") or "")
        ac = str(ev.get("action") or "")
        if not th or not ac:
            continue
        if _has_any(th, ["したい", "やりたい", "言いたい", "伝えたい", "必要", "べき"]) and _has_any(
            ac,
            ["できな", "できなかった", "しなかった", "やらな", "言わな", "送らな", "固ま", "止ま", "動け", "先延ばし", "延期", "逃げ"],
        ):
            mismatch_events.append(ev)
    if top:
        themes = "、".join([f"『{k}』" for k in top_keys[:2]])
        core = PF("summary_core", "・核（いちばん出やすい自己テーマ）: {themes}", themes=themes)

        # top構造に紐づく感情ヒント（数値や内部ロジックは出さない）
        ehs: List[str] = []
        for v in top[:2]:
            if v.top_emotions:
                ehs.extend([emo_label_ja(x) for x in v.top_emotions])
        ehs = [x for i, x in enumerate(ehs) if x and x not in ehs[:i]]

        if mismatch_events:
            shaky = "・崩れ条件（揺れを強めやすい引き金）: 思考では『したい/必要』が出ても、行動が止まりやすい場面が増えた可能性"
        elif ehs:
            shaky = PF(
                "summary_shaky_with_emotions",
                "・崩れ条件（揺れを強めやすい引き金）: {emotions}が強い場面で、判断が硬くなりやすい可能性",
                emotions="／".join(ehs[:2]),
            )
        else:
            shaky = P(
                "summary_shaky_default",
                "・崩れ条件（揺れを強めやすい引き金）: 刺激が重なった場面で、意味づけが固定されやすい可能性",
            )

        steady = P(
            "summary_steady_default",
            "・安定に寄せるキー（整える1手）: 揺れた瞬間に「思考内容1文」「行動内容1文」を分けて書くと、迷いがほどけやすい",
        )

        one_liner = PF(
            "summary_one_liner",
            "・ひとこと: いまは『{core_key}』が起点になりやすい状態。判断が硬くなる前に“1行メモ”が効きやすい。",
            core_key=top[0].key,
        )
    else:
        core = P("summary_core_no_data", "・核（いちばん出やすい自己テーマ）: まだ情報がありません")
        shaky = P("summary_shaky_no_data", "・崩れ条件（揺れを強めやすい引き金）: まだ情報がありません")
        steady = P("summary_steady_no_data", "・安定に寄せるキー（整える1手）: まずは短い観測メモを増やす")
        one_liner = P(
            "summary_one_liner_no_data",
            "・ひとこと: 今月は入力が少ないため、レポートは簡易版です。短文でOKなので『刺激→解釈→感情→行動』を1セットだけ記録してみてください。",
        )

    # 領域メモの割り当て
    bucket = _guess_domain_hints(top_keys)

    lines: List[str] = []
    lines.append(report_title)
    lines.append("")
    lines.append(P("summary_title", "【要点（答え）】"))
    lines.append(core)
    lines.append(shaky)
    lines.append(steady)
    lines.append(one_liner)
    lines.append(P("summary_disclaimer", "※診断ではなく、観測に基づく仮説です。"))
    lines.append("")

    # 1. 輪郭
    lines.append(P("sec1_title", "1. 今月の輪郭（仮説・1〜4行）"))
    if not top:
        lines.extend(
            PL(
                "sec1_no_data_lines",
                [
                    "今月は入力が少ないため、はっきりした傾向はまだ読み取れません。",
                    "短文で大丈夫なので、感情入力やメモ（刺激・解釈・感情・行動）が増えると、次回以降のレポートが具体的になります。",
                ],
            )
        )
    else:
        gloss1 = _short_structure_gloss(top[0].key) if use_structure_gloss else ""
        if gloss1:
            lines.append(
                PF(
                    "sec1_core_line_with_gloss",
                    "核として『{core_key}』が出やすく（意味: {gloss}）、判断の起点になっている可能性があります。",
                    core_key=top[0].key,
                    gloss=gloss1,
                )
            )
        else:
            lines.append(
                PF(
                    "sec1_core_line",
                    "核として『{core_key}』が出やすく、判断の起点になっている可能性があります。",
                    core_key=top[0].key,
                )
            )
        if len(top) >= 2:
            lines.append(
                PF(
                    "sec1_secondary_line",
                    "さらに『{secondary_key}』が重なると、見立てが揺れた瞬間に構造が濃くなりやすい可能性があります。",
                    secondary_key=top[1].key,
                )
            )
        lines.append(P("sec1_note_line", "※これは診断ではなく、最近の入力から読み取れる“仮の自己モデル”です。"))
        if self_insight_quotes:
            q = self_insight_quotes[-1]
            lines.append(f"今月あなたが言語化できた理解: 「{_excerpt(q, 120)}」")
    lines.append("")

    # 2. 反応パターン
    lines.append(P("sec2_title", "2. 主要な反応パターン（刺激→認知→感情→行動）"))
    if not top:
        lines.extend(
            PL(
                "sec2_no_data_lines",
                [
                    "今月は反応パターンを特定できるほどの情報がありません。",
                    "次の4点を、1回だけでもメモしてみてください（短文でOKです）。",
                    "・刺激（何が起きたか）",
                    "・認知（どう解釈したか）",
                    "・感情（何を感じたか）",
                    "・行動（どうしたか）",
                ],
            )
        )
    else:
        for i, v in enumerate(top[:2], start=1):
            emo_hint = "、".join([emo_label_ja(x) for x in v.top_emotions]) if v.top_emotions else "感情"
            lines.append(PF("sec2_pattern_title", "- パターン{index}: 『{structure_key}』", index=i, structure_key=v.key))
            lines.append(P("sec2_pattern_flow", "  流れ: 刺激 → 認知 → 感情 → 行動"))
            lines.append(PF("sec2_pattern_stimulus", "  刺激: （例）評価/比較/期待のズレ/未確定など、『{structure_key}』を強めやすい出来事", structure_key=v.key))
            lines.append(PF("sec2_pattern_cognition", "  認知: （仮）『{structure_key}』の判断が入り、意味づけが固定されやすい", structure_key=v.key))
            lines.append(PF("sec2_pattern_emotion", "  感情: {emotion_hint} に寄りやすい", emotion_hint=emo_hint))
            lines.append(P("sec2_pattern_action", "  行動: （仮）確認/修正へ向かう、または一時停止して距離を取る"))
            if v.sample_memos:
                lines.append(PF("sec2_pattern_memo", "  観測メモ（例）: {memo}", memo=v.sample_memos[0]))
    lines.append("")

    # 3. 条件
    lines.append(P("sec3_title", "3. 安定条件（安心が生まれやすい条件） / 崩れ条件（揺れやすい条件）"))
    lines.append(P("sec3_stable_heading", "安定条件:"))
    lines.append(P("sec3_stable_line_1", "・判断の前に『刺激/解釈/身体』を1行で切り分けられる"))
    lines.append(P("sec3_stable_line_3", "・忙しい日は短文でもいいので“観測”だけは継続できる"))
    lines.append(P("sec3_shaky_heading", "崩れ条件:"))
    if top:
        worst = max(top, key=lambda x: x.avg_intensity)
        lines.append(
            PF(
                "sec3_shaky_line_top",
                "・『{structure_key}』が{intensity_label}で出ている日に、判断が硬直しやすい",
                structure_key=worst.key,
                intensity_label=_intensity_label(worst.avg_intensity),
            )
        )
    lines.append(P("sec3_shaky_line_default", "・未確定/比較/評価が重なる場面で、解釈が一気に固定されやすい（視野が狭くなりやすい）"))
    lines.append("")

    # 4. 思考のクセ
    lines.append(P("sec4_title", "4. 思考のクセ・判断のクセ（あれば）"))
    if not top:
        lines.extend(
            PL(
                "sec4_no_data_lines",
                [
                    "今月は思考のクセが見えるほどの情報がありません。",
                    "気づいたときに「考えたこと（1文）」を残すと、次回以降で傾向が見えやすくなります。",
                ],
            )
        )
    else:
        lines.append(
            PF(
                "sec4_line_1",
                "・『{core_key}』が上位に出ているため、判断の起点が“評価/意味づけ”に寄りやすい可能性があります。",
                core_key=top[0].key,
            )
        )
        if len(top) >= 2:
            lines.append(
                PF(
                    "sec4_line_2",
                    "・『{secondary_key}』が重なると、白黒を急がず“仮置き”するのが難しくなることがあります。",
                    secondary_key=top[1].key,
                )
            )
        lines.append(P("sec4_line_3", "・対策としては、結論を急がず『観測→仮説』の順に戻すのが有効です。"))
    lines.append("")

    # 5. 領域別
    lines.append(P("sec5_title", "5. 領域別メモ（仕事/対人/孤独/挑戦/評価など、見えている範囲で）"))
    domains = phrases.get("sec5_domains") if isinstance(phrases.get("sec5_domains"), list) else ["仕事", "対人", "孤独", "挑戦", "評価"]
    for domain in domains:
        d = str(domain)
        hints = bucket.get(d) or []
        if hints:
            lines.append(
                PF(
                    "sec5_domain_with_hints",
                    "- {domain}: 『{hints_joined}』が絡む場面で自己モデルが動きやすい可能性",
                    domain=d,
                    hints_joined="』『".join(hints),
                )
            )
        else:
            lines.append(PF("sec5_domain_no_hints", "- {domain}: 今月はまだ傾向を判断できません。", domain=d))
    lines.append("")

    # 6. 観測ポイント
    lines.append(P("sec6_title", "6. 次の観測ポイント（3つ。行動に落ちる形で）"))
    for l in PL(
        "sec6_lines",
        [
            "・揺れた瞬間に『何が刺激だったか』を1語で書く",
            "・その刺激を『どう解釈したか（1文）』を書いてから、感情ラベルを選ぶ",
            "・強い日は『身体（睡眠/空腹/疲労）』も一緒にメモして、構造と身体を分けて観測する",
        ],
    ):
        lines.append(str(l))
    lines.append("")

    # 7. 差分
    lines.append(P("sec7_title", "7. 前回との差分（変化点 / 更新点 / 揺れ方の違い）"))

    used_prev_text = False
    if prev_report_text:
        try:
            diff_lines = _build_prev_diff_summary_lines(
                prev_text=str(prev_report_text),
                current_top_keys=top_keys,
                current_core_line=core,
                current_shaky_line=shaky,
                current_steady_line=steady,
                deltas=deltas,
                phrases=phrases,
            )
            if diff_lines:
                lines.extend(diff_lines)
                used_prev_text = True
        except Exception:
            used_prev_text = False

    # 前回本文が無い場合/抽出できない場合は、データ差分で補う
    if not used_prev_text:
        if not prev_views and not cur_views:
            lines.append(P("diff_no_data", "前回と今回の入力が少ないため、差分はまだまとめられません。"))
        elif not prev_views and cur_views:
            lines.append(P("diff_prev_missing", "前回は入力が少なく、今月から傾向が見え始めている状態です。"))
        else:
            shown = 0
            for k, dc, di in deltas:
                if shown >= 3:
                    break
                if dc == 0 and abs(di) < 0.1:
                    continue
                sign = "増えた" if dc > 0 else "減った"
                lines.append(PF("diff_delta_line", "・『{key}』が{sign}（出現回数の差分: {count:+d} / 強度差: {intensity:+.1f}）", key=k, sign=sign, count=dc, intensity=di))
                shown += 1
            if shown == 0:
                lines.append(P("diff_no_major", "大きな差分は目立たず、構造は安定して推移しています。"))

    lines.append("")

    # Structural appendix (Premium): short, user-facing; no internal names.
    if mode in ("structural", "deep"):
        lines.append("【Structural追記】")
        lines.append("※ここからは構造の『定義/干渉/誤認』の観点で、仮説をもう1段だけ深掘りします。")
        lines.append("※断定ではなく『観測→仮説→次の観測』の循環を作るための追記です。")
        lines.append("")
        if top_keys:
            lines.append(f"・核候補: 『{top_keys[0]}』")
            lines.append("  - チェック: これは“人格”ではなく、“条件が揃うと出る反応”として扱えているか")
            lines.append("  - 次の観測: 何が揃うと立ち上がる？（睡眠/空腹/期限/評価/未確定 など）")
            if len(top_keys) >= 2:
                lines.append(f"・干渉仮説: 『{top_keys[0]}』が強い日に『{top_keys[1]}』が重なり、判断が硬くなる可能性")
                lines.append("  - 次の観測: “重なった順番”を1行だけ記録（先にどっちが来た？）")
        else:
            lines.append("・材料が少ないため、追記は“観測設計”に寄せます。")
            lines.append("  - 次の観測: 揺れた時に『思考/行動』を1行ずつ残す（最低1回）")

        lines.append("")
        lines.append("・誤認チェック（よく起きるズレ）")
        lines.append("  - 相手/環境の問題を“自分の欠陥”に回収していないか")
        lines.append("  - 未確定を“確定した悪い未来”として扱っていないか")
        lines.append("  - 1回の失敗を“恒常的な自己定義”にしていないか")
        lines.append("")

    # 8. 感情の動きとの接続
    lines.append(P("sec8_title", "8. 感情の動きとの接続（短く）"))
    if top:
        lines.append(PF("sec8_with_top_line_1", "不安/怒りなどの揺れが目立つとき、背景で『{core_key}』が立っている可能性があります。", core_key=top[0].key))
        lines.append(P("sec8_with_top_line_2", "気持ちの“天気”と、自己の判断の“クセ”を分けて見るほど、回復が速くなります。"))
    else:
        lines.append(P("sec8_no_data_line", "感情の揺れが見えたら、“刺激→解釈”の観測を増やすと接続が強くなります。"))

    mashlogic_applied = False

    meta = {
        "engine": "astor_myprofile_report",
        "version": "myprofile.report.v2",
        "report_mode": mode,
        "period": period,
        "period_days": days,
        "analysis_source": analysis_source,
        "data_scope": "self" if include_secret else "public",
        "diff_reference": "prev_report_text" if (prev_report_text and used_prev_text) else "data_only",
        "structure_gloss_used": bool(use_structure_gloss),
        "mashlogic_applied": bool(mashlogic_applied),
        "section_text_template_id": section_tid,
        "top_structures": [
            {"key": v.key, "count": v.count, "avg_intensity": v.avg_intensity} for v in top
        ],
        "self_insight_quotes": len(self_insight_quotes),
        "thought_action_mismatch_count": len(mismatch_events),
    }

    return ("\n".join(lines).strip() + "\n", meta)


# =============================================================================
# Phase 5b: analysis_results-based MyProfile report generation
# -----------------------------------------------------------------------------
# Main path:
#   analysis_results(self_structure standard/deep)
#     + optional emotion_structure bridge
#     -> report basis
#     -> content_text / content_json
#
# Fallback path:
#   _build_myprofile_monthly_report_fallback(...)
# =============================================================================

def _analysis_as_of_iso(as_of: Optional[_dt.datetime]) -> Optional[str]:
    if as_of is None:
        return None
    return _to_iso_z(as_of)


def _fetch_analysis_result_row(
    *,
    user_id: str,
    analysis_type: str,
    scope: str,
    analysis_stage: str,
    as_of: Optional[_dt.datetime] = None,
) -> Optional[Dict[str, Any]]:
    if not _has_supabase_config():
        return None

    uid = str(user_id or "").strip()
    if not uid:
        return None

    params: List[Tuple[str, str]] = [
        ("select", "id,target_user_id,snapshot_id,analysis_type,scope,analysis_stage,analysis_version,source_hash,payload,created_at,updated_at"),
        ("target_user_id", f"eq.{uid}"),
        ("analysis_type", f"eq.{analysis_type}"),
        ("scope", f"eq.{scope}"),
        ("analysis_stage", f"eq.{analysis_stage}"),
        ("order", "created_at.desc"),
        ("limit", "1"),
    ]
    as_of_iso = _analysis_as_of_iso(as_of)
    if as_of_iso:
        params.append(("created_at", f"lte.{as_of_iso}"))

    url = f"{SUPABASE_URL}/rest/v1/analysis_results"
    try:
        with httpx.Client(timeout=6.0) as client:
            resp = client.get(url, headers=_sb_headers(), params=params)
    except Exception:
        return None

    if resp.status_code not in (200, 206):
        return None
    try:
        data = resp.json()
    except Exception:
        return None
    if isinstance(data, list) and data:
        return data[0] if isinstance(data[0], dict) else None
    if isinstance(data, dict):
        return data
    return None


def _serialize_analysis_ref(row: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
    if not isinstance(row, dict):
        return None
    return {
        "analysis_result_id": row.get("id"),
        "snapshot_id": row.get("snapshot_id"),
        "source_hash": row.get("source_hash"),
        "generated_at": row.get("created_at") or row.get("updated_at"),
        "analysis_stage": row.get("analysis_stage"),
        "scope": row.get("scope"),
    }


def _fetch_self_structure_analysis_set(
    *,
    user_id: str,
    as_of: Optional[_dt.datetime],
    report_mode: str,
) -> Dict[str, Any]:
    mode = _normalize_report_mode(report_mode)
    standard_row = _fetch_analysis_result_row(
        user_id=user_id,
        analysis_type="self_structure",
        scope="global",
        analysis_stage="standard",
        as_of=as_of,
    )
    deep_row = None
    if mode == "deep":
        deep_row = _fetch_analysis_result_row(
            user_id=user_id,
            analysis_type="self_structure",
            scope="global",
            analysis_stage="deep",
            as_of=as_of,
        )
    return {
        "standard_row": standard_row,
        "deep_row": deep_row,
        "refs": {
            "standard": _serialize_analysis_ref(standard_row),
            "deep": _serialize_analysis_ref(deep_row),
        },
    }


def _fetch_emotion_bridge_analysis_set(
    *,
    user_id: str,
    as_of: Optional[_dt.datetime],
    preferred_scope: str = "monthly",
    report_mode: str = "standard",
) -> Dict[str, Any]:
    mode = _normalize_report_mode(report_mode)
    scopes = [preferred_scope]
    if preferred_scope != "weekly":
        scopes.append("weekly")

    standard_row = None
    deep_row = None
    used_scope = None

    for scope in scopes:
        standard_row = _fetch_analysis_result_row(
            user_id=user_id,
            analysis_type="emotion_structure",
            scope=scope,
            analysis_stage="standard",
            as_of=as_of,
        )
        if standard_row:
            used_scope = scope
            break

    if mode == "deep":
        target_scope = used_scope or preferred_scope
        deep_row = _fetch_analysis_result_row(
            user_id=user_id,
            analysis_type="emotion_structure",
            scope=target_scope,
            analysis_stage="deep",
            as_of=as_of,
        )
        if deep_row and used_scope is None:
            used_scope = target_scope

    return {
        "scope": used_scope,
        "standard_row": standard_row,
        "deep_row": deep_row,
        "refs": {
            "standard": _serialize_analysis_ref(standard_row),
            "deep": _serialize_analysis_ref(deep_row),
        },
    }


def _payload_of(row: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    if isinstance(row, dict) and isinstance(row.get("payload"), dict):
        return dict(row.get("payload") or {})
    return {}


def _extract_self_structure_payloads(analysis_set: Dict[str, Any]) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    return _payload_of((analysis_set or {}).get("standard_row")), _payload_of((analysis_set or {}).get("deep_row"))


def _extract_emotion_bridge_payloads(analysis_set: Dict[str, Any]) -> Tuple[Dict[str, Any], Dict[str, Any]]:
    return _payload_of((analysis_set or {}).get("standard_row")), _payload_of((analysis_set or {}).get("deep_row"))


def _take_list(x: Any) -> List[Any]:
    return x if isinstance(x, list) else []


def _take_dict(x: Any) -> Dict[str, Any]:
    return x if isinstance(x, dict) else {}


def _top_items(items: List[Dict[str, Any]], top_k: int = 5) -> List[Dict[str, Any]]:
    xs = [x for x in items if isinstance(x, dict)]
    xs.sort(key=lambda d: float(d.get("score") or 0.0), reverse=True)
    return xs[:top_k]


def _extract_self_structure_standard_report(payload: Dict[str, Any]) -> Dict[str, Any]:
    return _take_dict(payload.get("standard")) or _take_dict(payload.get("standardReport"))


def _extract_self_structure_deep_report(payload: Dict[str, Any]) -> Dict[str, Any]:
    return _take_dict(payload.get("deep")) or _take_dict(payload.get("deepReport"))


def _extract_identity_state(payload: Dict[str, Any]) -> Dict[str, Any]:
    return _take_dict(payload.get("identity_state")) or _take_dict(payload.get("identityState"))


def _extract_core_role(standard_payload: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    std = _extract_self_structure_standard_report(standard_payload)
    summary = _take_dict(std.get("summary"))
    core = summary.get("core_role")
    if isinstance(core, dict):
        return core
    top_roles = _take_list(std.get("top_roles"))
    return top_roles[0] if top_roles and isinstance(top_roles[0], dict) else None


def _extract_core_target(standard_payload: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    std = _extract_self_structure_standard_report(standard_payload)
    summary = _take_dict(std.get("summary"))
    core = summary.get("core_target")
    if isinstance(core, dict):
        return core
    top_targets = _take_list(std.get("top_targets"))
    return top_targets[0] if top_targets and isinstance(top_targets[0], dict) else None


def _extract_core_thinking(standard_payload: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    std = _extract_self_structure_standard_report(standard_payload)
    summary = _take_dict(std.get("summary"))
    core = summary.get("core_thinking")
    if isinstance(core, dict):
        return core
    arr = _take_list(std.get("top_thinking_patterns"))
    return arr[0] if arr and isinstance(arr[0], dict) else None


def _extract_core_action(standard_payload: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    std = _extract_self_structure_standard_report(standard_payload)
    summary = _take_dict(std.get("summary"))
    core = summary.get("core_action")
    if isinstance(core, dict):
        return core
    arr = _take_list(std.get("top_action_patterns"))
    return arr[0] if arr and isinstance(arr[0], dict) else None


def _summarize_emotion_bridge(
    standard_payload: Dict[str, Any],
    deep_payload: Dict[str, Any],
    *,
    bridge_scope: Optional[str] = None,
) -> Dict[str, Any]:
    out = {
        "scope": bridge_scope,
        "top_emotions": [],
        "movement_summary": "",
        "time_bias_summary": "",
        "control_note": "",
    }

    cand_lists = [
        _take_list(_take_dict(standard_payload.get("standard")).get("top_emotions")),
        _take_list(_take_dict(standard_payload.get("summary")).get("top_emotions")),
        _take_list(_take_dict(standard_payload.get("analysisPayload")).get("top_emotions")),
        _take_list(_take_dict(standard_payload.get("payload")).get("top_emotions")),
    ]
    top_emotions: List[str] = []
    for arr in cand_lists:
        for x in arr:
            s = str(x or "").strip()
            if s and s not in top_emotions:
                top_emotions.append(s)
    out["top_emotions"] = top_emotions[:3]

    for cand in [
        _take_dict(standard_payload.get("standard")).get("contentText"),
        _take_dict(standard_payload.get("summary")).get("movement_summary"),
        _take_dict(standard_payload.get("summary")).get("contentText"),
        _take_dict(standard_payload.get("standard")).get("summary"),
        standard_payload.get("summary"),
    ]:
        if isinstance(cand, str) and cand.strip():
            out["movement_summary"] = _excerpt(cand, 140)
            break

    deep_obj = _take_dict(deep_payload.get("deep")) or _take_dict(deep_payload.get("deepReport"))
    for cand in [
        deep_obj.get("contentText"),
        _take_dict(deep_obj.get("summary")).get("control_note"),
        deep_obj.get("control_note"),
    ]:
        if isinstance(cand, str) and cand.strip():
            out["control_note"] = _excerpt(cand, 140)
            break

    return out


def _build_identity_snapshot_excerpt(
    standard_payload: Dict[str, Any],
    deep_payload: Dict[str, Any],
) -> Dict[str, Any]:
    std_state = _extract_identity_state(standard_payload)
    deep_state = _extract_identity_state(deep_payload)

    def _pick(state: Dict[str, Any], key: str, top_k: int) -> List[Dict[str, Any]]:
        return _top_items(_take_list(state.get(key)), top_k=top_k)

    excerpt = {
        "template_role_scores": _pick(std_state, "template_role_scores", 10),
        "cluster_scores": _pick(deep_state or std_state, "cluster_scores", 5),
        "target_role_scores": _top_items(_take_list(std_state.get("target_role_scores")), top_k=12),
        "thinking_patterns": _pick(std_state, "thinking_patterns", 10),
        "action_patterns": _pick(std_state, "action_patterns", 10),
        "target_signatures": _top_items(_take_list(deep_state.get("target_signatures") or std_state.get("target_signatures")), top_k=10),
    }
    return excerpt


def _build_report_basis_from_analysis(
    *,
    self_standard_payload: Dict[str, Any],
    self_deep_payload: Dict[str, Any],
    emotion_standard_payload: Dict[str, Any],
    emotion_deep_payload: Dict[str, Any],
    report_mode: str,
    emotion_bridge_scope: Optional[str] = None,
) -> Dict[str, Any]:
    std = _extract_self_structure_standard_report(self_standard_payload)
    deep = _extract_self_structure_deep_report(self_deep_payload)
    state_std = _extract_identity_state(self_standard_payload)
    state_deep = _extract_identity_state(self_deep_payload)

    top_roles = _top_items(_take_list(std.get("top_roles")) or _take_list(state_std.get("template_role_scores")), top_k=3)
    top_targets = _top_items(_take_list(std.get("top_targets")), top_k=5)
    if not top_targets:
        # derive top targets from target-role map (one per target)
        tr_map = _top_items(_take_list(state_std.get("target_role_scores")), top_k=20)
        seen = set()
        derived = []
        for row in tr_map:
            tk = str(row.get("target_key") or "")
            if not tk or tk in seen:
                continue
            seen.add(tk)
            derived.append({
                "target_key": row.get("target_key"),
                "target_label_ja": row.get("target_label_ja"),
                "target_type": row.get("target_type"),
                "score": row.get("score"),
                "role_key": row.get("role_key"),
                "role_label_ja": row.get("role_label_ja"),
            })
            if len(derived) >= 5:
                break
        top_targets = derived

    basis = {
        "report_mode": _normalize_report_mode(report_mode),
        "core_role": _extract_core_role(self_standard_payload),
        "core_target": _extract_core_target(self_standard_payload),
        "core_thinking": _extract_core_thinking(self_standard_payload),
        "core_action": _extract_core_action(self_standard_payload),
        "top_roles": top_roles,
        "top_targets": top_targets,
        "thinking_patterns": _top_items(_take_list(std.get("top_thinking_patterns")) or _take_list(state_std.get("thinking_patterns")), top_k=5),
        "action_patterns": _top_items(_take_list(std.get("top_action_patterns")) or _take_list(state_std.get("action_patterns")), top_k=5),
        "generated_roles": _top_items(_take_list(deep.get("generated_roles")), top_k=5),
        "cluster_distribution": _top_items(_take_list(deep.get("cluster_distribution")) or _take_list(state_deep.get("cluster_scores")), top_k=5),
        "target_role_map": _top_items(_take_list(deep.get("target_role_map")) or _take_list(state_std.get("target_role_scores")), top_k=12),
        "target_signatures": _top_items(_take_list(deep.get("target_signatures") or state_deep.get("target_signatures") or state_std.get("target_signatures")), top_k=10),
        "self_world_roles": _top_items(_take_list(deep.get("self_world_roles")), top_k=5),
        "real_world_roles": _top_items(_take_list(deep.get("real_world_roles")), top_k=5),
        "desired_roles": _top_items(_take_list(deep.get("desired_roles")), top_k=5),
        "role_gaps": _top_items(_take_list(deep.get("role_gaps")), top_k=5),
        "question_candidates": _top_items(_take_list(deep.get("question_candidates")), top_k=5),
        "emotion_bridge": _summarize_emotion_bridge(
            emotion_standard_payload,
            emotion_deep_payload,
            bridge_scope=emotion_bridge_scope,
        ),
        "identity_snapshot_excerpt": _build_identity_snapshot_excerpt(
            self_standard_payload,
            self_deep_payload,
        ),
    }
    return basis


def _build_summary_lines_from_basis(
    basis: Dict[str, Any],
    *,
    phrases: Dict[str, Any],
) -> List[str]:
    def P(key: str, default: str) -> str:
        v = phrases.get(key)
        return str(v) if isinstance(v, str) and v else default
    def PF(key: str, default: str, **kwargs: Any) -> str:
        return _safe_format(P(key, default), **kwargs).strip()

    core_role = _take_dict(basis.get("core_role"))
    core_target = _take_dict(basis.get("core_target"))
    core_th = _take_dict(basis.get("core_thinking"))
    core_act = _take_dict(basis.get("core_action"))
    top_roles = _take_list(basis.get("top_roles"))

    lines: List[str] = []
    if core_role:
        lines.append(
            PF(
                "summary_core",
                "・核（いちばん出やすい自己テーマ）: 『{role}』が出やすい可能性",
                role=core_role.get("label_ja") or core_role.get("key") or "役割",
            )
        )
    else:
        lines.append(P("summary_core_no_data", "・核（いちばん出やすい自己テーマ）: まだ情報がありません"))

    if core_target and core_role:
        lines.append(
            PF(
                "summary_shaky_default",
                "・崩れ条件（揺れを強めやすい引き金）: 主に『{target}』で『{role}』が立ち上がりやすい可能性",
                target=core_target.get("target_label_ja") or core_target.get("label_ja") or "対象",
                role=core_role.get("label_ja") or core_role.get("key") or "役割",
            )
        )
    elif core_target:
        lines.append(
            PF(
                "summary_shaky_default",
                "・崩れ条件（揺れを強めやすい引き金）: 主に『{target}』が反応の起点になりやすい可能性",
                target=core_target.get("target_label_ja") or core_target.get("label_ja") or "対象",
            )
        )
    else:
        lines.append(P("summary_shaky_no_data", "・崩れ条件（揺れを強めやすい引き金）: まだ情報がありません"))

    if core_th or core_act:
        lines.append(
            PF(
                "summary_steady_default",
                "・安定に寄せるキー（整える1手）: 『{thinking}』と『{action}』を切り分けて観測する",
                thinking=(core_th.get("label_ja") or core_th.get("key") or "思考"),
                action=(core_act.get("label_ja") or core_act.get("key") or "行動"),
            )
        )
    else:
        lines.append(P("summary_steady_no_data", "・安定に寄せるキー（整える1手）: まずは短い観測メモを増やす"))

    if top_roles:
        role_names = "、".join([str(x.get("label_ja") or x.get("key") or "") for x in top_roles[:2] if str(x.get("label_ja") or x.get("key") or "").strip()])
        if role_names:
            lines.append(
                PF(
                    "summary_one_liner",
                    "・ひとこと: いまは{roles}が前面に出やすい状態。対象と反応を分けて見るほど整いやすい。",
                    roles=role_names,
                )
            )
        else:
            lines.append(P("summary_one_liner_no_data", "・ひとこと: まだ十分な観測がありません。"))
    else:
        lines.append(P("summary_one_liner_no_data", "・ひとこと: まだ十分な観測がありません。"))

    return lines[:4]


def _build_reaction_pattern_lines_from_basis(
    basis: Dict[str, Any],
    *,
    phrases: Dict[str, Any],
) -> List[str]:
    lines: List[str] = []
    targets = _take_list(basis.get("top_targets"))
    generated = _take_list(basis.get("generated_roles"))
    target_role_map = _take_list(basis.get("target_role_map"))

    if generated:
        for i, row in enumerate(generated[:2], start=1):
            lines.append(f"- パターン{i}: 『{row.get('description') or row.get('template_role_label_ja') or row.get('template_role') or '役割'}』")
            tlabel = row.get("target_label_ja") or row.get("target_key")
            if tlabel:
                lines.append(f"  対象: {tlabel}")
            ths = [str(x) for x in (row.get("top_thinking_keys") or []) if str(x).strip()]
            acts = [str(x) for x in (row.get("top_action_keys") or []) if str(x).strip()]
            if ths:
                lines.append(f"  思考: {' / '.join(ths[:2])}")
            if acts:
                lines.append(f"  行動: {' / '.join(acts[:2])}")
        return lines[:8]

    if target_role_map:
        seen = set()
        idx = 0
        for row in target_role_map:
            tk = str(row.get("target_key") or "")
            if not tk or tk in seen:
                continue
            seen.add(tk)
            idx += 1
            lines.append(f"- パターン{idx}: 『{row.get('role_label_ja') or row.get('role_key') or '役割'}』")
            lines.append(f"  対象: {row.get('target_label_ja') or tk}")
            if idx >= 2:
                break
        return lines[:8]

    if targets:
        for i, row in enumerate(targets[:2], start=1):
            lines.append(f"- パターン{i}: 対象『{row.get('target_label_ja') or row.get('target_key') or '対象'}』への反応が強い可能性")
        return lines[:6]

    return ["今月は主要な反応パターンを特定できるほどの材料がまだ揃っていません。"]


def _build_stability_lines_from_basis(
    basis: Dict[str, Any],
    *,
    phrases: Dict[str, Any],
) -> List[str]:
    clusters = _take_list(basis.get("cluster_distribution"))
    role_gaps = _take_list(basis.get("role_gaps"))
    lines: List[str] = ["安定条件:"]
    if clusters:
        top = clusters[0]
        lines.append(f"・{top.get('label_ja') or top.get('key') or '上位クラスター'} が優位な時は、反応が比較的まとまりやすい可能性")
    else:
        lines.append("・対象と反応を1行で切り分けられる時、状態が整いやすい可能性")
    lines.append("崩れ条件:")
    if role_gaps:
        g = role_gaps[0]
        left = g.get("left_role") or "自己側"
        right = g.get("right_role") or "現実側"
        lines.append(f"・{left} と {right} のずれが強いとき、反応が硬くなりやすい可能性")
    else:
        lines.append("・期待・評価・未確定が重なる場面で、反応が固定されやすい可能性")
    return lines[:5]


def _build_thinking_habit_lines_from_basis(
    basis: Dict[str, Any],
    *,
    phrases: Dict[str, Any],
) -> List[str]:
    thinking = _take_list(basis.get("thinking_patterns"))
    action = _take_list(basis.get("action_patterns"))
    lines: List[str] = []
    if thinking:
        top_names = "、".join([str(x.get("label_ja") or x.get("key") or "") for x in thinking[:2] if str(x.get("label_ja") or x.get("key") or "").strip()])
        if top_names:
            lines.append(f"・思考の軸として {top_names} が出やすい可能性")
    if action:
        top_names = "、".join([str(x.get("label_ja") or x.get("key") or "") for x in action[:2] if str(x.get("label_ja") or x.get("key") or "").strip()])
        if top_names:
            lines.append(f"・行動の出方として {top_names} が選ばれやすい可能性")
    if not lines:
        lines.append("・思考や行動のクセが見えるほどの情報はまだ十分ではありません。")
    return lines[:4]


def _build_domain_note_lines_from_basis(
    basis: Dict[str, Any],
    *,
    phrases: Dict[str, Any],
) -> List[str]:
    targets = _take_list(basis.get("top_targets"))
    by_type: Dict[str, List[str]] = {"person": [], "environment": [], "activity": [], "concept": [], "self": []}
    for t in targets:
        if not isinstance(t, dict):
            continue
        tp = str(t.get("target_type") or "")
        label = str(t.get("target_label_ja") or t.get("target_key") or "").strip()
        if tp in by_type and label and label not in by_type[tp]:
            by_type[tp].append(label)
    lines: List[str] = []
    mapping = [("person", "人"), ("environment", "環境"), ("activity", "活動"), ("concept", "概念"), ("self", "自分")]
    for tp, label in mapping:
        vals = by_type.get(tp) or []
        if vals:
            lines.append(f"- {label}: {'、'.join(vals[:2])} が主な観測対象として出ています。")
        else:
            lines.append(f"- {label}: 今月はまだ傾向を判断できません。")
    return lines[:6]


def _build_next_observation_lines_from_basis(
    basis: Dict[str, Any],
    *,
    phrases: Dict[str, Any],
) -> List[str]:
    qs = _take_list(basis.get("question_candidates"))
    lines: List[str] = []
    for q in qs[:3]:
        hint = str(q.get("hint") or q.get("reason") or "").strip()
        if hint:
            lines.append(f"・次に見たい点: {hint}")
    if not lines:
        lines = [
            "・揺れた瞬間に『対象』を1語だけ書く",
            "・その対象をどう解釈したかを1文で残す",
            "・行動できなかった時も“反応”として残す",
        ]
    return lines[:3]


def _build_diff_lines_from_reports(
    *,
    prev_report_text: Optional[str],
    prev_report_json: Optional[Dict[str, Any]],
    current_excerpt: Dict[str, Any],
    phrases: Dict[str, Any],
) -> List[str]:
    current_keys = [str(x.get("key") or x.get("label_ja") or "").strip() for x in _take_list(current_excerpt.get("template_role_scores"))[:3] if str(x.get("key") or x.get("label_ja") or "").strip()]
    cur_core = ""
    if current_keys:
        cur_core = f"・核（いちばん出やすい自己テーマ）: {'、'.join([f'『{k}』' for k in current_keys[:2]])}"
    current_shaky = ""
    current_steady = ""
    deltas: List[Tuple[str, int, float]] = []

    prev_json_excerpt = _take_dict((prev_report_json or {}).get("identity_snapshot_excerpt"))
    if prev_json_excerpt:
        prev_keys = [str(x.get("key") or x.get("label_ja") or "").strip() for x in _take_list(prev_json_excerpt.get("template_role_scores"))[:3] if str(x.get("key") or x.get("label_ja") or "").strip()]
        lines = ["【差分の要約（前回→今回）】"]
        if prev_keys and current_keys:
            if prev_keys[0] != current_keys[0]:
                lines.append(f"・中心テーマ: 『{prev_keys[0]}』→『{current_keys[0]}』へ移動した可能性")
            else:
                lines.append(f"・中心テーマ: 『{current_keys[0]}』が継続している可能性")
            new_keys = [k for k in current_keys if k not in prev_keys]
            if new_keys:
                lines.append(f"・新しく目立ち始めた: 『{new_keys[0]}』")
            faded = [k for k in prev_keys if k not in current_keys]
            if faded:
                lines.append(f"・落ち着いた可能性: 『{faded[0]}』")
        return lines[:6]

    if prev_report_text:
        return _build_prev_diff_summary_lines(
            prev_text=str(prev_report_text),
            current_top_keys=current_keys,
            current_core_line=cur_core,
            current_shaky_line=current_shaky,
            current_steady_line=current_steady,
            deltas=deltas,
            phrases=phrases,
        )
    return ["前回比較に使える十分な参照がまだありません。"]


def _build_emotion_bridge_lines_from_basis(
    basis: Dict[str, Any],
    *,
    phrases: Dict[str, Any],
) -> List[str]:
    bridge = _take_dict(basis.get("emotion_bridge"))
    top_emos = [emo_label_ja(x) for x in (_take_list(bridge.get("top_emotions")) or [])[:3]]
    lines: List[str] = []
    if top_emos:
        lines.append(f"主に {'／'.join(top_emos)} の揺れが背景に見える可能性があります。")
    movement = str(bridge.get("movement_summary") or "").strip()
    if movement:
        lines.append(_excerpt(movement, 120))
    control = str(bridge.get("control_note") or "").strip()
    if control:
        lines.append(_excerpt(control, 120))
    if not lines:
        lines.append("感情の動きとの接続は、もう少し材料が増えると見えやすくなります。")
    return lines[:3]


def _coerce_float(value: Any, default: float = 0.0) -> float:
    try:
        return float(value)
    except Exception:
        return default


def _coerce_int(value: Any, default: int = 0) -> int:
    try:
        return int(value)
    except Exception:
        return default


def _thinking_key_to_label_ja(key: Any) -> str:
    s = str(key or "").strip()
    if not s:
        return ""
    return THINKING_LABELS_JA.get(s, s)


def _action_key_to_label_ja(key: Any) -> str:
    s = str(key or "").strip()
    if not s:
        return ""
    return ACTION_LABELS_JA.get(s, s)


def _unknown_kind_to_label_ja(kind: Any) -> str:
    mapping = {
        "real_world_role_missing": "現実での役割がまだ薄い",
        "desired_role_missing": "理想の役割がまだ薄い",
        "self_world_role_missing": "自己認識の役割がまだ薄い",
        "role_gap_unclear": "役割のズレがまだ曖昧",
        "target_missing": "対象の切り分けがまだ薄い",
    }
    s = str(kind or "").strip()
    return mapping.get(s, "追加観測が必要")


def _build_role_ref(role_key: Any, role_label_ja: Any) -> Optional[Dict[str, Any]]:
    key = str(role_key or "").strip()
    label = str(role_label_ja or "").strip()
    if not key and not label:
        return None
    if not label and key:
        label = str(ROLE_LABELS_JA.get(key, key))
    return {
        "role_key": key or None,
        "role_label_ja": label or None,
    }


def _role_ref_from_row(row: Any) -> Optional[Dict[str, Any]]:
    if not isinstance(row, dict):
        return None
    return _build_role_ref(
        row.get("role_key") or row.get("key") or row.get("template_role"),
        row.get("role_label_ja") or row.get("label_ja") or row.get("template_role_label_ja"),
    )


def _role_ref_from_gap_side(row: Any, kind: str) -> Optional[Dict[str, Any]]:
    if not isinstance(row, dict):
        return None
    s_kind = str(kind or "").strip()
    if not s_kind:
        return None
    if str(row.get("left_kind") or "").strip() == s_kind:
        return _build_role_ref(row.get("left_role"), row.get("left_role_label_ja"))
    if str(row.get("right_kind") or "").strip() == s_kind:
        return _build_role_ref(row.get("right_role"), row.get("right_role_label_ja"))
    return None


def _target_meta_lookup_from_basis(basis: Dict[str, Any]) -> Dict[str, Dict[str, Any]]:
    lookup: Dict[str, Dict[str, Any]] = {}

    def _remember(row: Any) -> None:
        if not isinstance(row, dict):
            return
        target_key = str(row.get("target_key") or row.get("key") or "").strip()
        if not target_key:
            return
        current = dict(lookup.get(target_key) or {})
        current["target_key"] = target_key
        label = str(row.get("target_label_ja") or row.get("label_ja") or "").strip()
        target_type = str(row.get("target_type") or "").strip()
        if label and not current.get("target_label_ja"):
            current["target_label_ja"] = label
        if target_type and not current.get("target_type"):
            current["target_type"] = target_type
        lookup[target_key] = current

    _remember(_take_dict((basis or {}).get("core_target")))
    for key in (
        "top_targets",
        "target_role_map",
        "target_signatures",
        "generated_roles",
        "self_world_roles",
        "real_world_roles",
        "desired_roles",
        "role_gaps",
        "question_candidates",
    ):
        for row in _take_list((basis or {}).get(key)):
            _remember(row)
    return lookup


def _resolve_target_meta(
    target_lookup: Dict[str, Dict[str, Any]],
    *,
    target_key: Any,
    fallback_label: Any = None,
    fallback_type: Any = None,
) -> Dict[str, Any]:
    key = str(target_key or "").strip()
    meta = dict(target_lookup.get(key) or {})
    label = str(fallback_label or meta.get("target_label_ja") or key or "").strip()
    target_type = str(fallback_type or meta.get("target_type") or "").strip()
    return {
        "target_key": key or None,
        "target_label_ja": label or None,
        "target_type": target_type or None,
    }


def _role_switch_rows_from_basis(basis: Dict[str, Any]) -> List[Dict[str, Any]]:
    rows = [dict(x) for x in _take_list((basis or {}).get("target_role_map")) if isinstance(x, dict)]
    if rows:
        return rows

    fallback_rows: List[Dict[str, Any]] = []
    generated_by_target = {
        str(x.get("target_key") or "").strip(): x
        for x in _take_list((basis or {}).get("generated_roles"))
        if isinstance(x, dict) and str(x.get("target_key") or "").strip()
    }
    for sig in _take_list((basis or {}).get("target_signatures")):
        if not isinstance(sig, dict):
            continue
        target_key = str(sig.get("target_key") or "").strip()
        if not target_key:
            continue
        generated = generated_by_target.get(target_key) or {}
        fallback_rows.append(
            {
                "target_key": target_key,
                "target_label_ja": sig.get("target_label_ja") or generated.get("target_label_ja"),
                "target_type": sig.get("target_type") or generated.get("target_type"),
                "role_key": sig.get("top_role_key") or generated.get("template_role"),
                "role_label_ja": sig.get("top_role_label_ja") or generated.get("template_role_label_ja"),
                "score": sig.get("top_role_score") or generated.get("score"),
                "evidence_count": sig.get("evidence_count") or generated.get("evidence_count"),
            }
        )
    return fallback_rows


def _top_roles_catalog_from_target_rows(rows: List[Dict[str, Any]], top_k: int = 5) -> List[Dict[str, Any]]:
    catalog: Dict[str, Dict[str, Any]] = {}
    for row in rows:
        if not isinstance(row, dict):
            continue
        role_key = str(row.get("role_key") or "").strip()
        if not role_key:
            continue
        score = _coerce_float(row.get("score"))
        prev = catalog.get(role_key)
        if prev is None or score > _coerce_float(prev.get("score")):
            catalog[role_key] = {
                "role_key": role_key,
                "role_label_ja": str(row.get("role_label_ja") or ROLE_LABELS_JA.get(role_key, role_key)).strip(),
                "score": score,
            }
    ranked = sorted(catalog.values(), key=lambda d: (-_coerce_float(d.get("score")), str(d.get("role_label_ja") or "")))
    return ranked[:max(top_k, 1)]


def _world_roles_by_target(rows: List[Dict[str, Any]]) -> Tuple[Dict[str, Dict[str, Any]], Optional[Dict[str, Any]]]:
    by_target: Dict[str, Dict[str, Any]] = {}
    global_best: Optional[Dict[str, Any]] = None
    for row in rows:
        if not isinstance(row, dict):
            continue
        score = _coerce_float(row.get("score"))
        target_key = str(row.get("target_key") or "").strip()
        if target_key:
            prev = by_target.get(target_key)
            if prev is None or score > _coerce_float(prev.get("score")):
                by_target[target_key] = row
        elif global_best is None or score > _coerce_float(global_best.get("score")):
            global_best = row
    return by_target, global_best


def _build_deep_summary_card_from_basis(basis: Dict[str, Any]) -> Dict[str, Any]:
    target_lookup = _target_meta_lookup_from_basis(basis)
    generated = _take_dict((_take_list((basis or {}).get("generated_roles")) or [{}])[0])
    core_target = _take_dict((basis or {}).get("core_target"))
    core_role = _take_dict((basis or {}).get("core_role"))

    target_meta = _resolve_target_meta(
        target_lookup,
        target_key=generated.get("target_key") or core_target.get("target_key"),
        fallback_label=generated.get("target_label_ja") or core_target.get("target_label_ja"),
        fallback_type=generated.get("target_type") or core_target.get("target_type"),
    )
    role_ref = _build_role_ref(
        generated.get("template_role") or core_role.get("key") or core_role.get("role_key"),
        generated.get("template_role_label_ja") or core_role.get("label_ja") or core_role.get("role_label_ja"),
    )
    description = str(generated.get("description") or "").strip()

    target_label = str(target_meta.get("target_label_ja") or "").strip()
    role_label = str((role_ref or {}).get("role_label_ja") or "").strip()

    if target_label and role_label:
        headline = f"現在は『{target_label}』に触れたときに『{role_label}』が立ち上がりやすい状態です。"
    elif target_label and description:
        headline = f"現在は『{target_label}』に触れたとき、{description}傾向が出やすい状態です。"
    elif role_label:
        headline = f"現在は『{role_label}』が前に出やすい状態です。"
    else:
        headline = "現在の役割スイッチの地図を整理しています。"

    chips: List[str] = []
    target_keys = _unique_keep_order([
        str(x.get("target_key") or "").strip()
        for x in _take_list((basis or {}).get("target_role_map"))
        if isinstance(x, dict) and str(x.get("target_key") or "").strip()
    ])
    if len(target_keys) >= 2:
        chips.append("対象で役割が切り替わりやすい")

    thinking_labels = _unique_keep_order([
        _pattern_label_from_row(x)
        for x in _take_list((basis or {}).get("thinking_patterns"))[:2]
    ])
    action_labels = _unique_keep_order([
        _pattern_label_from_row(x)
        for x in _take_list((basis or {}).get("action_patterns"))[:2]
    ])
    if thinking_labels:
        chips.append(f"思考は{' / '.join(thinking_labels[:2])}寄り")
    if action_labels:
        chips.append(f"行動は{' / '.join(action_labels[:2])}寄り")
    if _take_list((basis or {}).get("role_gaps")):
        chips.append("役割ギャップが見られる対象あり")

    return {
        "headline": headline,
        "core_target": target_meta if target_meta.get("target_key") or target_meta.get("target_label_ja") else None,
        "core_role": role_ref,
        "core_generated_role": {
            "description": description or None,
            "target_key": target_meta.get("target_key"),
            "target_label_ja": target_meta.get("target_label_ja"),
        } if description or target_meta.get("target_key") or target_meta.get("target_label_ja") else None,
        "chips": chips[:3],
    }


def _build_deep_role_switch_map_from_basis(basis: Dict[str, Any]) -> Dict[str, Any]:
    target_lookup = _target_meta_lookup_from_basis(basis)
    rows = _role_switch_rows_from_basis(basis)
    if not rows:
        return {
            "targets": [],
            "roles": [],
            "cells": [],
            "dominant_by_target": [],
            "max_score": 0.0,
        }

    target_best: Dict[str, Dict[str, Any]] = {}
    for row in rows:
        target_key = str(row.get("target_key") or "").strip()
        if not target_key:
            continue
        score = _coerce_float(row.get("score"))
        prev = target_best.get(target_key)
        if prev is None or score > _coerce_float(prev.get("score")):
            target_best[target_key] = row

    dominant_rows = sorted(
        target_best.values(),
        key=lambda d: (-_coerce_float(d.get("score")), _target_label_from_row(d), _role_label_from_row(d)),
    )[:5]
    selected_target_keys = [
        str(row.get("target_key") or "").strip()
        for row in dominant_rows
        if str(row.get("target_key") or "").strip()
    ]
    selected_rows = [
        row for row in rows
        if str(row.get("target_key") or "").strip() in selected_target_keys
    ]

    roles = _top_roles_catalog_from_target_rows(selected_rows, top_k=5)
    selected_role_keys = {str(x.get("role_key") or "").strip() for x in roles if str(x.get("role_key") or "").strip()}
    if selected_role_keys:
        selected_rows = [
            row for row in selected_rows
            if str(row.get("role_key") or "").strip() in selected_role_keys
        ]

    cells = [
        {
            "target_key": str(row.get("target_key") or "").strip() or None,
            "target_label_ja": str(row.get("target_label_ja") or _resolve_target_meta(target_lookup, target_key=row.get("target_key")).get("target_label_ja") or "").strip() or None,
            "role_key": str(row.get("role_key") or "").strip() or None,
            "role_label_ja": str(row.get("role_label_ja") or ROLE_LABELS_JA.get(str(row.get("role_key") or "").strip(), row.get("role_key") or "")).strip() or None,
            "score": _coerce_float(row.get("score")),
            "evidence_count": _coerce_int(row.get("evidence_count")),
        }
        for row in selected_rows
        if isinstance(row, dict)
    ]

    targets = [
        _resolve_target_meta(
            target_lookup,
            target_key=row.get("target_key"),
            fallback_label=row.get("target_label_ja"),
            fallback_type=row.get("target_type"),
        )
        for row in dominant_rows
    ]

    dominant_by_target = [
        {
            **_resolve_target_meta(
                target_lookup,
                target_key=row.get("target_key"),
                fallback_label=row.get("target_label_ja"),
                fallback_type=row.get("target_type"),
            ),
            "role_key": str(row.get("role_key") or "").strip() or None,
            "role_label_ja": str(row.get("role_label_ja") or ROLE_LABELS_JA.get(str(row.get("role_key") or "").strip(), row.get("role_key") or "")).strip() or None,
            "score": _coerce_float(row.get("score")),
        }
        for row in dominant_rows
    ]

    return {
        "targets": targets,
        "roles": [
            {
                "role_key": str(row.get("role_key") or "").strip() or None,
                "role_label_ja": str(row.get("role_label_ja") or "").strip() or None,
            }
            for row in roles
        ],
        "cells": cells,
        "dominant_by_target": dominant_by_target,
        "max_score": max([_coerce_float(x.get("score")) for x in cells] or [0.0]),
    }


def _build_deep_behavior_cards_from_basis(basis: Dict[str, Any]) -> List[Dict[str, Any]]:
    target_lookup = _target_meta_lookup_from_basis(basis)
    generated_by_target = {
        str(x.get("target_key") or "").strip(): x
        for x in _take_list((basis or {}).get("generated_roles"))
        if isinstance(x, dict) and str(x.get("target_key") or "").strip()
    }

    signature_rows = [dict(x) for x in _take_list((basis or {}).get("target_signatures")) if isinstance(x, dict)]
    if not signature_rows:
        for row in _take_list((basis or {}).get("generated_roles")):
            if not isinstance(row, dict):
                continue
            signature_rows.append(
                {
                    "target_key": row.get("target_key"),
                    "target_label_ja": row.get("target_label_ja"),
                    "target_type": row.get("target_type"),
                    "top_role_key": row.get("template_role"),
                    "top_role_label_ja": row.get("template_role_label_ja"),
                    "top_role_score": row.get("score"),
                    "top_cluster_key": row.get("cluster"),
                    "top_thinking_keys": row.get("top_thinking_keys") or [],
                    "top_action_keys": row.get("top_action_keys") or [],
                    "evidence_count": row.get("evidence_count"),
                }
            )

    signature_rows.sort(key=lambda d: (-_coerce_float(d.get("top_role_score") or d.get("score")), str(d.get("target_label_ja") or d.get("target_key") or "")))

    cards: List[Dict[str, Any]] = []
    for sig in signature_rows[:4]:
        target_meta = _resolve_target_meta(
            target_lookup,
            target_key=sig.get("target_key"),
            fallback_label=sig.get("target_label_ja"),
            fallback_type=sig.get("target_type"),
        )
        generated = generated_by_target.get(str(sig.get("target_key") or "").strip()) or {}
        thinking = [
            {"key": key, "label_ja": _thinking_key_to_label_ja(key)}
            for key in list(sig.get("top_thinking_keys") or [])[:2]
            if str(key or "").strip()
        ]
        actions = [
            {"key": key, "label_ja": _action_key_to_label_ja(key)}
            for key in list(sig.get("top_action_keys") or [])[:2]
            if str(key or "").strip()
        ]
        cards.append(
            {
                **target_meta,
                "generated_role_description": str(generated.get("description") or "").strip() or None,
                "template_role_key": str(sig.get("top_role_key") or generated.get("template_role") or "").strip() or None,
                "template_role_label_ja": str(sig.get("top_role_label_ja") or generated.get("template_role_label_ja") or ROLE_LABELS_JA.get(str(sig.get("top_role_key") or generated.get("template_role") or "").strip(), sig.get("top_role_key") or generated.get("template_role") or "")).strip() or None,
                "cluster_key": str(sig.get("top_cluster_key") or generated.get("cluster") or "").strip() or None,
                "score": _coerce_float(sig.get("top_role_score") or generated.get("score")),
                "evidence_count": _coerce_int(sig.get("evidence_count") or generated.get("evidence_count")),
                "thinking": thinking,
                "actions": actions,
            }
        )
    return cards


def _build_deep_role_gap_cards_from_basis(basis: Dict[str, Any]) -> List[Dict[str, Any]]:
    target_lookup = _target_meta_lookup_from_basis(basis)
    self_by_target, self_global = _world_roles_by_target(_take_list((basis or {}).get("self_world_roles")))
    real_by_target, real_global = _world_roles_by_target(_take_list((basis or {}).get("real_world_roles")))
    desired_by_target, desired_global = _world_roles_by_target(_take_list((basis or {}).get("desired_roles")))

    def _select(kind: str, target_key: str, gap_row: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        kind_key = str(kind or "").strip()
        if kind_key == "self":
            return _role_ref_from_row(self_by_target.get(target_key) or self_global) or _role_ref_from_gap_side(gap_row, "self")
        if kind_key == "real":
            return _role_ref_from_row(real_by_target.get(target_key) or real_global) or _role_ref_from_gap_side(gap_row, "real")
        if kind_key == "desired":
            return _role_ref_from_row(desired_by_target.get(target_key) or desired_global) or _role_ref_from_gap_side(gap_row, "desired")
        return _role_ref_from_gap_side(gap_row, kind_key)

    cards: List[Dict[str, Any]] = []
    seen: List[str] = []
    for gap in _take_list((basis or {}).get("role_gaps")):
        if not isinstance(gap, dict):
            continue
        target_key = str(gap.get("target_key") or "").strip()
        uniq = target_key or f"{gap.get('left_kind')}:{gap.get('left_role')}:{gap.get('right_kind')}:{gap.get('right_role')}"
        if uniq in seen:
            continue
        seen.append(uniq)
        target_meta = _resolve_target_meta(
            target_lookup,
            target_key=target_key,
            fallback_label=gap.get("target_label_ja") or ("全体" if not target_key else None),
        )
        cards.append(
            {
                **target_meta,
                "self_role": _select("self", target_key, gap),
                "real_role": _select("real", target_key, gap),
                "desired_role": _select("desired", target_key, gap),
                "primary_gap": {
                    "left_kind": str(gap.get("left_kind") or "").strip() or None,
                    "right_kind": str(gap.get("right_kind") or "").strip() or None,
                    "left_role_label_ja": str(gap.get("left_role_label_ja") or ROLE_LABELS_JA.get(str(gap.get("left_role") or "").strip(), gap.get("left_role") or "")).strip() or None,
                    "right_role_label_ja": str(gap.get("right_role_label_ja") or ROLE_LABELS_JA.get(str(gap.get("right_role") or "").strip(), gap.get("right_role") or "")).strip() or None,
                    "gap_score": _coerce_float(gap.get("gap_score")),
                    "note": str(gap.get("note") or "").strip() or None,
                },
            }
        )
    return cards


def _build_deep_unknown_area_from_basis(basis: Dict[str, Any]) -> Dict[str, Any]:
    target_lookup = _target_meta_lookup_from_basis(basis)
    items: List[Dict[str, Any]] = []
    for row in _take_list((basis or {}).get("question_candidates"))[:4]:
        if not isinstance(row, dict):
            continue
        target_meta = _resolve_target_meta(
            target_lookup,
            target_key=row.get("target_key"),
            fallback_label=("全体" if not str(row.get("target_key") or "").strip() else None),
        )
        items.append(
            {
                **target_meta,
                "kind": str(row.get("kind") or "").strip() or None,
                "kind_label_ja": _unknown_kind_to_label_ja(row.get("kind")),
                "reason": str(row.get("reason") or "").strip() or None,
                "hint": str(row.get("hint") or "").strip() or None,
            }
        )
    return {"items": items}


def _build_self_structure_deep_visual_from_basis(basis: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "schema": "self_structure_deep_visual.v1",
        "presentationProfile": "role_switch_map",
        "summaryCard": _build_deep_summary_card_from_basis(basis),
        "roleSwitchMap": _build_deep_role_switch_map_from_basis(basis),
        "behaviorCards": _build_deep_behavior_cards_from_basis(basis),
        "roleGapCards": _build_deep_role_gap_cards_from_basis(basis),
        "unknownArea": _build_deep_unknown_area_from_basis(basis),
    }


def _build_myprofile_report_content_json(
    *,
    report_mode: str,
    report_type: str,
    period: str,
    period_start: Optional[str],
    period_end: Optional[str],
    distribution_utc: Optional[str],
    self_structure_set: Dict[str, Any],
    emotion_bridge_set: Dict[str, Any],
    basis: Dict[str, Any],
    sections: Dict[str, List[str]],
    generated_at_server: str,
) -> Dict[str, Any]:
    std_payload = _payload_of((self_structure_set or {}).get("standard_row"))
    deep_payload = _payload_of((self_structure_set or {}).get("deep_row"))
    normalized_mode = _normalize_report_mode(report_mode)

    content = {
        "engine": "astor_myprofile_report",
        "version": MYPROFILE_REPORT_SCHEMA_VERSION,
        "report_mode": normalized_mode,
        "report_type": str(report_type or "monthly"),
        "report_source": "analysis_results",
        "distribution": {
            "report_type": str(report_type or "monthly"),
            "period": str(period or "30d"),
            "period_start": period_start,
            "period_end": period_end,
            "distribution_utc": distribution_utc,
        },
        "analysis_refs": {
            "self_structure": (self_structure_set or {}).get("refs") or {},
            "emotion_bridge": (emotion_bridge_set or {}).get("refs") or {},
        },
        "identity_snapshot_excerpt": basis.get("identity_snapshot_excerpt") or {},
        "standardReport": _extract_self_structure_standard_report(std_payload),
        "deepReport": _extract_self_structure_deep_report(deep_payload),
        "emotionBridge": basis.get("emotion_bridge") or {},
        "sections": sections,
        "generated_at_server": generated_at_server,
    }

    if normalized_mode == "deep":
        deep_visual = _build_self_structure_deep_visual_from_basis(basis)
        if deep_visual:
            content["selfStructureDeepVisual"] = deep_visual
            content["visual_contracts"] = ["self_structure_deep_visual.v1"]

    return content



def _unique_keep_order(values: List[str]) -> List[str]:
    out: List[str] = []
    for raw in values:
        s = str(raw or "").strip()
        if s and s not in out:
            out.append(s)
    return out


def _role_label_from_row(row: Any) -> str:
    if not isinstance(row, dict):
        return ""
    for key in ("label_ja", "role_label_ja", "template_role_label_ja", "key", "role_key", "template_role"):
        s = str(row.get(key) or "").strip()
        if s:
            return s
    return ""


def _role_summary_from_row(row: Any) -> str:
    if not isinstance(row, dict):
        return ""
    for key in ("summary_ja", "role_summary_ja", "template_role_summary_ja", "description"):
        s = str(row.get(key) or "").strip()
        if s:
            return s.rstrip("。")
    return ""


def _role_flow_phrase(row: Any) -> str:
    summary = _role_summary_from_row(row)
    if not summary:
        return ""
    return re.sub(r"役割$", "", summary).strip()


def _target_label_from_row(row: Any) -> str:
    if not isinstance(row, dict):
        return ""
    for key in ("target_label_ja", "label_ja", "target_key", "key"):
        s = str(row.get(key) or "").strip()
        if s:
            return s
    return ""


def _pattern_label_from_row(row: Any) -> str:
    if not isinstance(row, dict):
        return ""
    for key in ("label_ja", "key"):
        s = str(row.get(key) or "").strip()
        if s:
            return s
    return ""


def _role_digest(row: Any) -> Dict[str, Any]:
    return {
        "label": _role_label_from_row(row),
        "summary": _role_summary_from_row(row),
        "score": (row.get("score") if isinstance(row, dict) else None),
    }


def _target_digest(row: Any) -> Dict[str, Any]:
    if not isinstance(row, dict):
        return {"label": "", "role_label": "", "score": None}
    return {
        "label": _target_label_from_row(row),
        "role_label": _role_label_from_row(row),
        "score": row.get("score"),
        "target_type": row.get("target_type"),
    }


def _pattern_digest(row: Any) -> Dict[str, Any]:
    if not isinstance(row, dict):
        return {"label": "", "score": None}
    return {"label": _pattern_label_from_row(row), "score": row.get("score")}


def _generated_role_digest(row: Any) -> Dict[str, Any]:
    if not isinstance(row, dict):
        return {"target": "", "role": "", "description": "", "score": None}
    return {
        "target": _target_label_from_row(row),
        "role": _role_label_from_row(row),
        "description": str(row.get("description") or "").strip(),
        "score": row.get("score"),
    }


def _basis_snapshot_for_history(basis: Dict[str, Any]) -> Dict[str, Any]:
    bridge = _take_dict((basis or {}).get("emotion_bridge"))
    return {
        "report_mode": (basis or {}).get("report_mode"),
        "core_role": _role_digest((basis or {}).get("core_role")),
        "top_roles": [_role_digest(x) for x in _take_list((basis or {}).get("top_roles"))[:3]],
        "top_targets": [_target_digest(x) for x in _take_list((basis or {}).get("top_targets"))[:3]],
        "thinking_patterns": [_pattern_digest(x) for x in _take_list((basis or {}).get("thinking_patterns"))[:3]],
        "action_patterns": [_pattern_digest(x) for x in _take_list((basis or {}).get("action_patterns"))[:3]],
        "generated_roles": [_generated_role_digest(x) for x in _take_list((basis or {}).get("generated_roles"))[:3]],
        "emotion_bridge": {
            "top_emotions": _unique_keep_order([emo_label_ja(x) for x in _take_list(bridge.get("top_emotions"))[:3]]),
            "movement_summary": _excerpt(str(bridge.get("movement_summary") or "").strip(), 140),
            "control_note": _excerpt(str(bridge.get("control_note") or "").strip(), 140),
        },
    }


def _compute_history_fingerprint(
    *,
    basis_snapshot: Dict[str, Any],
    self_structure_refs: Dict[str, Any],
    emotion_bridge_refs: Dict[str, Any],
    report_mode: str,
) -> str:
    def _hash_ref_block(refs: Dict[str, Any]) -> Dict[str, Any]:
        out: Dict[str, Any] = {}
        for key in ("standard", "deep"):
            node = refs.get(key) if isinstance(refs.get(key), dict) else {}
            out[key] = {
                "source_hash": str(node.get("source_hash") or "").strip(),
                "analysis_result_id": node.get("analysis_result_id"),
                "analysis_stage": node.get("analysis_stage"),
                "scope": node.get("scope"),
            }
        return out

    payload = {
        "report_mode": _normalize_report_mode(report_mode),
        "basis_snapshot": basis_snapshot,
        "analysis_refs": {
            "self_structure": _hash_ref_block(self_structure_refs or {}),
            "emotion_bridge": _hash_ref_block(emotion_bridge_refs or {}),
        },
    }
    raw = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()


def _build_current_structure_summary_from_basis(basis: Dict[str, Any]) -> str:
    core_role = _take_dict((basis or {}).get("core_role"))
    core_label = _role_label_from_row(core_role)
    if not core_label:
        top_roles = _take_list((basis or {}).get("top_roles"))
        if top_roles:
            core_role = _take_dict(top_roles[0])
            core_label = _role_label_from_row(core_role)
    if not core_label:
        return ""

    role_names = _unique_keep_order([_role_label_from_row(x) for x in _take_list((basis or {}).get("top_roles"))[:3]])
    secondary = [x for x in role_names if x and x != core_label][:2]
    flow = _role_flow_phrase(core_role)
    if flow:
        first = f"今のあなたは、{flow}流れが前に出ています。"
    else:
        first = f"今のあなたは、『{core_label}』に近い出方が中心になっています。"
    if secondary:
        if len(secondary) == 1:
            second = f"その上で『{secondary[0]}』の向きも重なっていて、ひとつの動きだけでは言い切れない状態です。"
        else:
            second = f"その上で『{secondary[0]}』『{secondary[1]}』の向きも重なっていて、いくつかの出方が同時に立っています。"
    else:
        second = f"役割ラベルで見ると、『{core_label}』がいちばん近い位置にあります。"
    return "\n".join([first, second]).strip()

def _build_role_content_lines_from_basis(basis: Dict[str, Any]) -> List[str]:
    top_roles = _take_list((basis or {}).get("top_roles"))
    if not top_roles and isinstance((basis or {}).get("core_role"), dict):
        top_roles = [_take_dict((basis or {}).get("core_role"))]

    lines: List[str] = []
    seen: List[str] = []
    for idx, row in enumerate(top_roles[:3]):
        role_label = _role_label_from_row(row)
        if not role_label or role_label in seen:
            continue
        seen.append(role_label)
        role_summary = _role_summary_from_row(row)
        role_flow = _role_flow_phrase(row) or role_summary
        if idx == 0:
            if role_flow:
                lines.append(f"・いちばん前に出やすいのは『{role_label}』で、{role_flow}傾向があります。")
            else:
                lines.append(f"・いちばん前に出やすいのは『{role_label}』という向きです。")
        else:
            if role_flow:
                lines.append(f"・その横で『{role_label}』も重なり、{role_flow}向きが支えています。")
            else:
                lines.append(f"・その横で『{role_label}』の向きも少し重なっています。")
    return lines

def _build_role_background_lines_from_basis(basis: Dict[str, Any]) -> List[str]:
    lines: List[str] = []
    thinking_labels = _unique_keep_order([_pattern_label_from_row(x) for x in _take_list((basis or {}).get("thinking_patterns"))[:2]])
    if thinking_labels:
        quoted = "、".join([f"『{x}』" for x in thinking_labels])
        lines.append(f"・考え方では{quoted}が前に出やすく、まず意味や背景を確かめながら受け止めようとする流れがあります。")

    action_labels = _unique_keep_order([_pattern_label_from_row(x) for x in _take_list((basis or {}).get("action_patterns"))[:2]])
    if action_labels:
        quoted = "、".join([f"『{x}』" for x in action_labels])
        lines.append(f"・動き方では{quoted}が選ばれやすく、外へ出る反応にもその傾向がにじみやすいようです。")

    target_labels = _unique_keep_order([_target_label_from_row(x) for x in _take_list((basis or {}).get("top_targets"))[:2]])
    if target_labels:
        quoted = "、".join([f"『{x}』" for x in target_labels])
        lines.append(f"・とくに{quoted}の場面でこの出方が立ち上がりやすく、置かれている文脈の影響も大きそうです。")

    generated = _take_list((basis or {}).get("generated_roles"))
    if generated:
        row = _take_dict(generated[0])
        desc = str(row.get("description") or "").strip()
        target = _target_label_from_row(row)
        if desc and target:
            lines.append(f"・『{target}』に向くときは、{desc}ような関わり方になりやすいようです。")
    return lines

def _build_reaction_flow_lines_from_basis(basis: Dict[str, Any]) -> List[str]:
    lines: List[str] = []
    used_targets: List[str] = []

    for row in _take_list((basis or {}).get("target_role_map")):
        target = _target_label_from_row(row)
        role_label = _role_label_from_row(row)
        if not target or target in used_targets:
            continue
        used_targets.append(target)
        if role_label:
            lines.append(f"・『{target}』に触れると、まず『{role_label}』の向きで受け止め、そのあと行動を選びやすい流れがあります。")
        else:
            lines.append(f"・『{target}』に触れると、いったん内側で受け止めてから反応が立ち上がりやすいようです。")
        if len(lines) >= 2:
            break

    if not lines:
        for row in _take_list((basis or {}).get("generated_roles")):
            target = _target_label_from_row(row)
            desc = str(row.get("description") or "").strip()
            if not target:
                continue
            used_targets.append(target)
            if desc:
                lines.append(f"・『{target}』に対しては、{desc}ような流れが立ち上がりやすいようです。")
            else:
                lines.append(f"・『{target}』に対して反応が濃く立ち上がりやすいようです。")
            if len(lines) >= 2:
                break

    if not lines:
        target_labels = _unique_keep_order([_target_label_from_row(x) for x in _take_list((basis or {}).get("top_targets"))[:2]])
        for target in target_labels[:2]:
            lines.append(f"・『{target}』がきっかけになると、いまの出方がはっきり表れやすいようです。")
    return lines

def _build_emotion_connection_lines_from_basis(basis: Dict[str, Any]) -> List[str]:
    bridge = _take_dict((basis or {}).get("emotion_bridge"))
    top_emotions = _unique_keep_order([emo_label_ja(x) for x in _take_list(bridge.get("top_emotions"))[:3]])
    lines: List[str] = []
    core_label = _role_label_from_row(_take_dict((basis or {}).get("core_role")))
    if top_emotions:
        joined = " / ".join(top_emotions[:2])
        if core_label:
            lines.append(f"・背景には{joined}の揺れがあり、その気持ちをそのまま外に出すより『{core_label}』の出方に変えて持ちやすいようです。")
        else:
            lines.append(f"・背景には{joined}の揺れが重なっているようです。")
    movement = str(bridge.get("movement_summary") or "").strip()
    if movement:
        lines.append(f"・気持ちの流れとしては、{_excerpt(movement, 110)}。")
    control = str(bridge.get("control_note") or "").strip()
    if control:
        lines.append(f"・もう少し深いところでは、{_excerpt(control, 110)}。")
    return lines[:3]

def _build_change_lines_v2(
    *,
    prev_report_json: Optional[Dict[str, Any]],
    basis: Dict[str, Any],
) -> List[str]:
    prev_basis = _take_dict((prev_report_json or {}).get("basis_snapshot"))
    if not prev_basis:
        return []

    lines: List[str] = []
    prev_core = _role_label_from_row(_take_dict(prev_basis.get("core_role")))
    cur_core = _role_label_from_row(_take_dict((basis or {}).get("core_role")))
    if prev_core and cur_core:
        if prev_core != cur_core:
            lines.append(f"・前回は『{prev_core}』寄りでしたが、今回は『{cur_core}』の出方が少し前に出ています。")
        else:
            lines.append(f"・前回から引き続き、『{cur_core}』に近い出方が中心です。")

    prev_targets = _unique_keep_order([_target_label_from_row(x) for x in _take_list(prev_basis.get("top_targets"))[:2]])
    cur_targets = _unique_keep_order([_target_label_from_row(x) for x in _take_list((basis or {}).get("top_targets"))[:2]])
    if prev_targets and cur_targets:
        if prev_targets[0] != cur_targets[0]:
            lines.append(f"・反応が立ち上がりやすい対象は、『{prev_targets[0]}』から『{cur_targets[0]}』へ少し移っています。")
        else:
            lines.append(f"・反応が立ち上がりやすい対象は、引き続き『{cur_targets[0]}』です。")

    prev_emotions = _unique_keep_order([str(x) for x in _take_list(_take_dict(prev_basis.get("emotion_bridge")).get("top_emotions"))[:2]])
    cur_emotions = _unique_keep_order([emo_label_ja(x) for x in _take_list(_take_dict((basis or {}).get("emotion_bridge")).get("top_emotions"))[:2]])
    if prev_emotions and cur_emotions and prev_emotions[0] != cur_emotions[0]:
        lines.append(f"・背景に重なりやすい感情は『{prev_emotions[0]}』寄りから『{cur_emotions[0]}』寄りへ動いています。")

    return lines[:3]

def build_myprofile_monthly_report(
    *,
    user_id: str,
    period: str = "30d",
    report_mode: Optional[str] = "standard",
    include_secret: bool = True,
    now: Optional[_dt.datetime] = None,
    prev_report_text: Optional[str] = None,
    prev_report_json: Optional[Dict[str, Any]] = None,
    report_type: str = "monthly",
    distribution_utc: Optional[str] = None,
    section_text_template_id: Optional[str] = None,
) -> Tuple[str, Dict[str, Any]]:
    """Build MyProfile report text + metadata from analysis results.

    Standard / Deep どちらも同じ本文構造を使い、monthly は latest 相当本文の保存履歴として扱う。
    入力不足時は legacy 構文へフォールバックせず、no-data を返す。
    """
    uid = str(user_id or "").strip()
    mode = _normalize_report_mode(report_mode)

    def _resolve_section_template_id(override: Optional[str]) -> str:
        if override:
            return str(override).strip()
        tid = (os.getenv("MYPROFILE_MONTHLY_SECTION_TEXT_TEMPLATE_ID") or "").strip()
        if tid:
            return tid
        tid = (os.getenv("MYPROFILE_SECTION_TEXT_TEMPLATE_ID") or "").strip()
        if tid:
            return tid
        return DEFAULT_MYPROFILE_SECTION_TEXT_TEMPLATE_ID

    section_tid = _resolve_section_template_id(section_text_template_id)
    phrases = get_myprofile_section_phrases(section_tid)

    def P(key: str, default: str) -> str:
        v = phrases.get(key)
        return str(v) if isinstance(v, str) and v else default

    report_title = P("report_title", "【自己構造分析レポート】")
    no_data_text = P("report_no_data", "データがありません。")
    summary_title = P("summary_title_current", "【今回の自己構造】")
    disclaimer_line = P(
        "summary_disclaimer_current",
        "※これは固定的な性格診断ではなく、現在の観測から見える役割傾向です。",
    )

    if not uid:
        return (
            f"{report_title}\n\n{P('error_no_user_id', '（ユーザーIDが指定されていないため生成できませんでした）')}",
            {
                "engine": "astor_myprofile_report",
                "version": MYPROFILE_REPORT_SCHEMA_VERSION,
                "status": "no_user_id",
                "section_text_template_id": section_tid,
                "visibility": {
                    "has_visible_content": False,
                    "visible_sections": [],
                    "hidden_sections": [],
                },
                "history": {
                    "archive_eligible": False,
                    "history_fingerprint": None,
                    "skip_reason": "no_user_id",
                },
            },
        )

    now_dt = now or _dt.datetime.utcnow().replace(microsecond=0, tzinfo=_dt.timezone.utc)
    if now_dt.tzinfo is None:
        now_dt = now_dt.replace(tzinfo=_dt.timezone.utc)

    days = parse_period_days(period)
    end = now_dt
    start = end - _dt.timedelta(days=max(days, 1))
    report_type_norm = str(report_type or "monthly").strip().lower() or "monthly"
    dist_utc_iso = distribution_utc or _to_iso_z(now_dt)

    self_set = _fetch_self_structure_analysis_set(
        user_id=uid,
        as_of=now_dt,
        report_mode=mode,
    )
    emotion_set = _fetch_emotion_bridge_analysis_set(
        user_id=uid,
        as_of=now_dt,
        preferred_scope="monthly",
        report_mode=mode,
    )

    self_std_payload, self_deep_payload = _extract_self_structure_payloads(self_set)
    emo_std_payload, emo_deep_payload = _extract_emotion_bridge_payloads(emotion_set)

    basis = _build_report_basis_from_analysis(
        self_standard_payload=self_std_payload,
        self_deep_payload=self_deep_payload,
        emotion_standard_payload=emo_std_payload,
        emotion_deep_payload=emo_deep_payload,
        report_mode=mode,
        emotion_bridge_scope=(emotion_set or {}).get("scope"),
    )

    summary_text = _build_current_structure_summary_from_basis(basis)
    role_lines = _build_role_content_lines_from_basis(basis)
    background_lines = _build_role_background_lines_from_basis(basis)
    flow_lines = _build_reaction_flow_lines_from_basis(basis)
    emotion_lines = _build_emotion_connection_lines_from_basis(basis)
    change_lines = _build_change_lines_v2(
        prev_report_json=prev_report_json,
        basis=basis,
    )

    numbered_sections: List[Tuple[str, str, List[str]]] = [
        ("role_content", P("sec_role_title", "役割内容"), role_lines),
        ("role_background", P("sec_background_title", "この役割が表れた背景"), background_lines),
        ("reaction_flow", P("sec_flow_title", "今の反応の流れ"), flow_lines),
        ("emotion_bridge", P("sec_emotion_title", "感情とのつながり"), emotion_lines),
        ("diff", P("sec_change_title", "前回からの変化"), change_lines),
    ]

    visible_sections = [
        section_key
        for section_key, _, lines in numbered_sections
        if any(str(x or "").strip() for x in lines)
    ]
    hidden_sections = [section_key for section_key, _, _ in numbered_sections if section_key not in visible_sections]
    has_visible_content = bool(summary_text.strip() or visible_sections)

    sections_for_meta: Dict[str, List[str]] = {
        "current_structure": [summary_text] if summary_text.strip() else [],
        "role_content": role_lines,
        "role_background": background_lines,
        "reaction_flow": flow_lines,
        "emotion_bridge": emotion_lines,
        "diff": change_lines,
    }

    basis_snapshot = _basis_snapshot_for_history(basis)
    history_fingerprint = None
    if has_visible_content:
        history_fingerprint = _compute_history_fingerprint(
            basis_snapshot=basis_snapshot,
            self_structure_refs=_take_dict((self_set or {}).get("refs")),
            emotion_bridge_refs=_take_dict((emotion_set or {}).get("refs")),
            report_mode=mode,
        )

    meta = _build_myprofile_report_content_json(
        report_mode=mode,
        report_type=report_type_norm,
        period=period,
        period_start=_to_iso_z(start),
        period_end=_to_iso_z(end),
        distribution_utc=dist_utc_iso,
        self_structure_set=self_set,
        emotion_bridge_set=emotion_set,
        basis=basis,
        sections=sections_for_meta,
        generated_at_server=_to_iso_z(_dt.datetime.now(_dt.timezone.utc).replace(microsecond=0)),
    )
    meta["engine"] = "astor_myprofile_report"
    meta["version"] = MYPROFILE_REPORT_SCHEMA_VERSION
    meta["section_text_template_id"] = section_tid
    meta["analysis_source"] = "analysis_results"
    meta["data_scope"] = "self" if include_secret else "public"
    meta["basis_snapshot"] = basis_snapshot
    meta["visibility"] = {
        "has_visible_content": has_visible_content,
        "visible_sections": (["current_structure"] if summary_text.strip() else []) + visible_sections,
        "hidden_sections": ([] if summary_text.strip() else ["current_structure"]) + hidden_sections,
    }
    meta["history"] = {
        "archive_eligible": has_visible_content,
        "history_fingerprint": history_fingerprint,
        "skip_reason": None if has_visible_content else "no_visible_content",
    }
    meta["summaryText"] = summary_text.strip() or None

    if not has_visible_content:
        return (f"{report_title}\n\n{no_data_text}\n", meta)

    lines: List[str] = [report_title, "", summary_title, summary_text.strip(), disclaimer_line]
    section_no = 1
    for _, title, content_lines in numbered_sections:
        clean_lines = [str(x) for x in content_lines if str(x or "").strip()]
        if not clean_lines:
            continue
        lines.append("")
        lines.append(f"{section_no}. {title}")
        lines.extend(clean_lines)
        section_no += 1

    return ("\n".join([str(x) for x in lines if x is not None]).strip() + "\n", meta)

# =============================================================================
# Phase 6: ASTOR heavy processing -> separate worker support
# -----------------------------------------------------------------------------
# This section adds a small "latest report refresh" helper that:
# - determines MyProfile report_mode from subscription tier
# - applies throttle (min interval) to avoid repeated heavy generation
# - uses generation_lock to avoid duplicate generation
# - upserts into Supabase table: myprofile_reports (report_type='latest')
#
# Intended to be called from a background worker process (Render worker).
# =============================================================================

import asyncio as _asyncio
import logging as _logging
from datetime import datetime as _datetime, timezone as _timezone, timedelta as _timedelta
from typing import Any as _Any, Dict as _Dict, Optional as _Optional

from supabase_client import (
    ensure_supabase_config as _ensure_supabase_config_shared,
    sb_get as _sb_get_shared,
    sb_post as _sb_post_shared,
)

_logger = _logging.getLogger("astor_myprofile_report")

# For app compatibility: latest uses fixed period_start/end and reuses one row.
LATEST_REPORT_PERIOD_START = "1970-01-01T00:00:00.000Z"
LATEST_REPORT_PERIOD_END = "1970-01-01T00:00:00.000Z"

# Env (optional):
# - MYPROFILE_LATEST_REFRESH_MIN_INTERVAL_SECONDS=90
# - MYPROFILE_LATEST_PERIOD=28d  (例: 7d / 28d / 30d)
try:
    MYPROFILE_LATEST_REFRESH_MIN_INTERVAL_SECONDS = int(
        os.getenv("MYPROFILE_LATEST_REFRESH_MIN_INTERVAL_SECONDS", "90") or "90"
    )
except Exception:
    MYPROFILE_LATEST_REFRESH_MIN_INTERVAL_SECONDS = 90

MYPROFILE_LATEST_PERIOD = str(os.getenv("MYPROFILE_LATEST_PERIOD", "28d") or "28d").strip() or "28d"


def _now_iso_z() -> str:
    return (
        _datetime.now(_timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )


def _parse_iso(iso: _Optional[str]) -> _Optional[_datetime]:
    if not iso:
        return None
    try:
        s = str(iso).strip()
        if s.endswith("Z"):
            s = s[:-1] + "+00:00"
        dt = _datetime.fromisoformat(s)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=_timezone.utc)
        return dt.astimezone(_timezone.utc)
    except Exception:
        return None


async def _fetch_myprofile_latest_generated_at(user_id: str) -> _Optional[str]:
    """Fetch generated_at from myprofile_reports(latest)."""
    _ensure_supabase_config_shared()

    params = {
        "select": "generated_at",
        "user_id": f"eq.{user_id}",
        "report_type": "eq.latest",
        "period_start": f"eq.{LATEST_REPORT_PERIOD_START}",
        "period_end": f"eq.{LATEST_REPORT_PERIOD_END}",
        "limit": "1",
    }
    resp = await _sb_get_shared("/rest/v1/myprofile_reports", params=params, timeout=5.0)
    if resp.status_code not in (200, 206):
        _logger.warning(
            "Fetch myprofile_reports(latest) failed: %s %s",
            resp.status_code,
            (resp.text or "")[:500],
        )
        return None
    try:
        data = resp.json()
    except Exception:
        return None
    if isinstance(data, list) and data:
        if isinstance(data[0], dict):
            return data[0].get("generated_at")
    if isinstance(data, dict):
        return data.get("generated_at")
    return None


async def _upsert_myprofile_latest_report_row(payload: _Dict[str, _Any]) -> None:
    """Upsert myprofile_reports(latest). Raises on failure."""
    _ensure_supabase_config_shared()

    params = {"on_conflict": "user_id,report_type,period_start,period_end"}
    prefer = "resolution=merge-duplicates,return=minimal"
    resp = await _sb_post_shared(
        "/rest/v1/myprofile_reports",
        json=payload,
        params=params,
        prefer=prefer,
        timeout=10.0,
    )
    if resp.status_code not in (200, 201, 204):
        raise RuntimeError(
            f"Upsert myprofile_reports(latest) failed: HTTP {resp.status_code} {(resp.text or '')[:800]}"
        )

async def refresh_myprofile_monthly_report(
    *,
    user_id: str,
    period_override: _Optional[str] = None,
    report_mode_override: _Optional[str] = None,
    include_secret: bool = True,
    now: _Optional[_dt.datetime] = None,
    prev_report_text: _Optional[str] = None,
    prev_report_json: _Optional[_Dict[str, _Any]] = None,
    distribution_utc: _Optional[str] = None,
) -> _Dict[str, _Any]:
    """Build the monthly MyProfile report through a shared refresher contract.

    This keeps route façades from calling `build_myprofile_monthly_report(...)` directly.
    The function returns a small orchestration payload that callers can persist or shape
    into their own API responses.
    """
    uid = str(user_id or "").strip()
    if not uid:
        raise ValueError("user_id is required")

    period_used = str(period_override or "28d").strip() or "28d"
    report_mode = _normalize_report_mode(report_mode_override)
    now_dt = (now or _dt.datetime.now(_dt.timezone.utc)).astimezone(_dt.timezone.utc).replace(microsecond=0)
    distribution_value = str(distribution_utc or "").strip() or _to_iso_z(now_dt)

    text, meta = await _asyncio.to_thread(
        build_myprofile_monthly_report,
        user_id=uid,
        period=period_used,
        report_mode=report_mode,
        include_secret=include_secret,
        now=now_dt,
        prev_report_text=prev_report_text,
        prev_report_json=prev_report_json,
        report_type="monthly",
        distribution_utc=distribution_value,
    )

    return {
        "status": "ok",
        "user_id": uid,
        "period": period_used,
        "report_mode": report_mode,
        "distribution_utc": distribution_value,
        "generated_at": _now_iso_z(),
        "report_text": str(text or "").strip(),
        "report_meta": meta if isinstance(meta, dict) else {},
    }


async def refresh_myprofile_latest_report(
    *,
    user_id: str,
    trigger: str = "worker",
    force: bool = False,
    period_override: _Optional[str] = None,
    report_mode_override: _Optional[str] = None,
) -> _Dict[str, _Any]:
    """Generate + upsert the latest MyProfile report (preview).

    Returns a small dict for logging/observability:
      - status: ok / skipped_throttle / skipped_locked / empty
      - report_mode, period, generated_at (when ok)
    """
    uid = str(user_id or "").strip()
    if not uid:
        raise ValueError("user_id is required")

    period_used = str(period_override or MYPROFILE_LATEST_PERIOD or "28d").strip() or "28d"

    # ---- throttle ----
    if not force:
        min_interval = int(MYPROFILE_LATEST_REFRESH_MIN_INTERVAL_SECONDS or 0)
        if min_interval > 0:
            try:
                last_iso = await _fetch_myprofile_latest_generated_at(uid)
                last_dt = _parse_iso(last_iso)
                if last_dt is not None:
                    now_dt = _datetime.now(_timezone.utc)
                    if (now_dt - last_dt).total_seconds() < float(min_interval):
                        return {
                            "status": "skipped_throttle",
                            "user_id": uid,
                            "last_generated_at": last_iso,
                            "min_interval_sec": min_interval,
                        }
            except Exception:
                # If we can't read last time, continue generation.
                pass

    # ---- determine report_mode (fail-closed) ----
    # Spec v2: Plus=standard, Premium=structural, Free=not entitled (keep "light" for compatibility).
    if str(report_mode_override or "").strip():
        report_mode = _normalize_report_mode(report_mode_override)
    else:
        report_mode = "light"
        try:
            from subscription_store import get_subscription_tier_for_user
            from subscription import SubscriptionTier

            tier = await get_subscription_tier_for_user(uid, default=SubscriptionTier.FREE)
            if tier == SubscriptionTier.PREMIUM:
                report_mode = "structural"
            elif tier == SubscriptionTier.PLUS:
                report_mode = "standard"
            else:
                report_mode = "light"
        except Exception:
            report_mode = "light"

    # ---- generation lock (best-effort) ----
    lock_key = None
    lock_owner = None
    lock_acquired = True
    try:
        from generation_lock import build_lock_key, make_owner_id, release_lock, try_acquire_lock

        lock_key = build_lock_key(
            namespace="myprofile",
            user_id=uid,
            report_type="latest",
            period_start=LATEST_REPORT_PERIOD_START,
            period_end=LATEST_REPORT_PERIOD_END,
        )
        lock_owner = make_owner_id(f"myprofile_latest:{trigger}")
        ttl = int(os.getenv("GENERATION_LOCK_TTL_SECONDS_MYPROFILE_LATEST", "180") or "180")
        lr = await try_acquire_lock(
            lock_key=lock_key,
            ttl_seconds=ttl,
            owner_id=lock_owner,
            context={
                "namespace": "myprofile",
                "user_id": uid,
                "report_type": "latest",
                    "period": period_used,
                "report_mode": report_mode,
                "source": trigger,
            },
        )
        lock_acquired = bool(getattr(lr, "acquired", False))
        lock_owner = getattr(lr, "owner_id", lock_owner)
    except Exception:
        lock_acquired = True

    if not lock_acquired:
        return {"status": "skipped_locked", "user_id": uid}

    try:
        # ---- generate latest text (rule-based; no LLM) ----
        now_dt = _datetime.now(_timezone.utc).replace(microsecond=0)

        # build_myprofile_monthly_report is sync; run in a thread to keep worker loop responsive.
        text, meta = await _asyncio.to_thread(
            build_myprofile_monthly_report,
            user_id=uid,
            period=period_used,
            report_mode=report_mode,
            include_secret=True,
            now=now_dt,
            prev_report_text=None,
        )

        text = str(text or "").strip()
        visibility = meta.get("visibility") if isinstance(meta, dict) else {}
        has_visible_content = bool((visibility or {}).get("has_visible_content"))
        generated_at = _now_iso_z()
        if not text:
            return {"status": "empty", "user_id": uid}
        if not has_visible_content:
            distribution_meta = ((meta or {}).get("distribution") or {}) if isinstance(meta, dict) else {}
            return {
                "status": "no_visible_content",
                "user_id": uid,
                "report_mode": report_mode,
                "period": period_used,
                "generated_at": generated_at,
                "period_start": str(distribution_meta.get("period_start") or "").strip() or None,
                "period_end": str(distribution_meta.get("period_end") or "").strip() or None,
                "title": "現在の自己構造",
                "content_text": text,
                "meta": meta,
                "has_visible_content": False,
                "skip_reason": ((meta or {}).get("history") or {}).get("skip_reason") if isinstance(meta, dict) else None,
            }

        # snapshot window (for debugging / UI hints)
        snap = {"period": MYPROFILE_LATEST_PERIOD}
        try:
            days = 28
            try:
                days = int(parse_period_days(period_used))
            except Exception:
                pass
            end_dt = _datetime.now(_timezone.utc).replace(microsecond=0)
            start_dt = end_dt - _timedelta(days=max(days, 1))
            snap = {
                "start": start_dt.isoformat().replace("+00:00", "Z"),
                "end": end_dt.isoformat().replace("+00:00", "Z"),
                "period": period_used,
            }
        except Exception:
            pass

        payload = {
            "user_id": uid,
            "report_type": "latest",
            "period_start": LATEST_REPORT_PERIOD_START,
            "period_end": LATEST_REPORT_PERIOD_END,
            "title": "自己構造レポート（最新版）",
            "content_text": text,
            "content_json": {
                **(meta or {}),
                "source": trigger,
                "snapshot": snap,
                "snapshot_period": period_used,
                "generated_at_server": generated_at,
            },
            "generated_at": generated_at,
        }

        await _upsert_myprofile_latest_report_row(payload)

        return {
            "status": "ok",
            "user_id": uid,
            "report_mode": report_mode,
            "period": period_used,
            "generated_at": generated_at,
            "period_start": str((((meta or {}).get("distribution") or {}).get("period_start") or "")).strip() or None,
            "period_end": str((((meta or {}).get("distribution") or {}).get("period_end") or "")).strip() or None,
            "title": "現在の自己構造",
            "content_text": text,
            "meta": payload.get("content_json"),
            "has_visible_content": True,
            "skip_reason": None,
        }
    finally:
        try:
            from generation_lock import release_lock

            if lock_key:
                await release_lock(lock_key=lock_key, owner_id=lock_owner)
        except Exception:
            pass
