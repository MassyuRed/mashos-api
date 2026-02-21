# -*- coding: utf-8 -*-
"""astor_myprofile_report.py

ASTOR MyProfile（月次）自己構造分析レポート生成
-------------------------------------------------

狙い
  - MyProfile の月次レポートを「読める構文」で安定生成する。
  - 現段階では LLM を必須にせず、ASTOR が保持している
    構造パターン（astor_structure_patterns.json）と
    Deep Insight の回答（astor_deep_insight_answers.json）から、
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

try:
    from astor_deep_insight_store import DeepInsightAnswerStore
except Exception:  # pragma: no cover
    DeepInsightAnswerStore = None  # type: ignore


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


def _normalize_report_mode(x: Any) -> str:
    """Normalize report_mode into one of: standard / structural.

    Backward-compat:
    - deep -> structural
    - light -> standard (MyProfile API should gate this, but keep safe fallback)
    """
    # Prefer subscription.py normalizer if available
    if normalize_myprofile_mode is not None and MyProfileMode is not None:
        try:
            return normalize_myprofile_mode(x, default=MyProfileMode.STANDARD).value
        except Exception:
            return "standard"

    # Fallback: string normalization
    s = str(x or "").strip()
    if not s:
        return "standard"
    s2 = s.lower()
    if s2 in ("standard", "structural"):
        return s2
    if s2 in ("deep",):
        return "structural"
    if s2 in ("light",):
        return "standard"
    # common JP labels
    if s in ("ライト", "Light"):
        return "standard"
    if s in ("スタンダード", "Standard"):
        return "standard"
    if s in ("ディープ", "Deep"):
        return "structural"
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


def _to_iso_z(dt: _dt.datetime) -> str:
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
        return _dt.datetime.fromisoformat(str(ts).replace("Z", "+00:00"))
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


def _load_deep_insight_answers(user_id: str, *, include_secret: bool, limit: int = 6) -> List[Dict[str, Any]]:
    if DeepInsightAnswerStore is None:
        return []
    try:
        store = DeepInsightAnswerStore()
        return store.get_user_answers(user_id, limit=limit, include_secret=include_secret)
    except Exception:
        return []


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


def _build_text_events_from_deep_answers(
    answers: List[Dict[str, Any]],
    *,
    start: _dt.datetime,
    end: _dt.datetime,
    include_secret: bool,
    limit: int = 6,
) -> List[Dict[str, Any]]:
    events: List[Dict[str, Any]] = []
    for a in (answers or [])[: max(1, int(limit))]:
        if not isinstance(a, dict):
            continue
        if (not include_secret) and bool(a.get("is_secret", False)):
            continue
        ts = _parse_ts(a.get("created_at"))
        if ts is None:
            continue
        if ts < start or ts >= end:
            continue
        text = str(a.get("text") or a.get("answer_text") or "").strip()
        if not text:
            continue
        events.append(
            {
                "ts": ts,
                "kind": "deep",
                "combined_text": text,
                "thought": "",
                "action": "",
                "emotions": [],
                "intensity": 0.0,
                "excerpt": _build_event_excerpt("", "", deep_text=text),
            }
        )
    return events


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

    if m == "structural" and load_structure_dict is not None:
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


def build_myprofile_monthly_report(
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
    use_structure_gloss = (mode == "structural")
    # Legacy deep enhancer is not used for Spec v2; keep the variable for meta only.
    use_mashlogic = False
    now_dt = now or _dt.datetime.utcnow().replace(microsecond=0, tzinfo=_dt.timezone.utc)

    end = now_dt
    start = end - _dt.timedelta(days=max(days, 1))
    prev_end = start
    prev_start = prev_end - _dt.timedelta(days=max(days, 1))

    # Materials (Spec v2): thought/action logs + self-insight + deep answers
    deep_answers = _load_deep_insight_answers(uid, include_secret=include_secret, limit=12)

    analysis_source = "supabase_emotions" if _has_supabase_config() else "patterns_store"

    # Prefer raw logs (Supabase emotions) for v2; fallback to legacy patterns store when unavailable.
    cur_rows = _fetch_emotion_rows(uid, start=start, end=end)
    prev_rows = _fetch_emotion_rows(uid, start=prev_start, end=prev_end)

    cur_events, self_insight_quotes = _build_text_events_from_emotions(cur_rows, start=start, end=end, include_secret=include_secret)
    prev_events, _ = _build_text_events_from_emotions(prev_rows, start=prev_start, end=prev_end, include_secret=include_secret)

    # Deep Insight answers: include those within the window as additional text material (best-effort).
    cur_events.extend(_build_text_events_from_deep_answers(deep_answers, start=start, end=end, include_secret=include_secret, limit=6))
    prev_events.extend(_build_text_events_from_deep_answers(deep_answers, start=prev_start, end=prev_end, include_secret=include_secret, limit=6))

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

    # Deep Insight (narrative)
    deep_answers = deep_answers[:6]

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

        if deep_answers:
            steady = P(
                "summary_steady_deep",
                "・安定に寄せるキー（整える1手）: 判断の前に『基準を1行だけ言語化』すると、構造の暴走が収まりやすい",
            )
        else:
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
    if deep_answers:
        lines.append(P("sec3_stable_line_deep", "・Deep Insight の回答で自分の基準を言語化できているとき"))
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
    if mode == "structural":
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
        "deep_insight_answers": len(deep_answers),
        "self_insight_quotes": len(self_insight_quotes),
        "thought_action_mismatch_count": len(mismatch_events),
    }

    return ("\n".join(lines).strip() + "\n", meta)

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


async def refresh_myprofile_latest_report(
    *,
    user_id: str,
    trigger: str = "worker",
    force: bool = False,
) -> _Dict[str, _Any]:
    """Generate + upsert the latest MyProfile report (preview).

    Returns a small dict for logging/observability:
      - status: ok / skipped_throttle / skipped_locked / empty
      - report_mode, generated_at (when ok)
    """
    uid = str(user_id or "").strip()
    if not uid:
        raise ValueError("user_id is required")

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
                "period": MYPROFILE_LATEST_PERIOD,
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
            period=MYPROFILE_LATEST_PERIOD or "28d",
            report_mode=report_mode,
            include_secret=True,
            now=now_dt,
            prev_report_text=None,
        )

        text = str(text or "").strip()
        if not text:
            return {"status": "empty", "user_id": uid}

        # snapshot window (for debugging / UI hints)
        snap = {"period": MYPROFILE_LATEST_PERIOD}
        try:
            days = 28
            try:
                days = int(parse_period_days(MYPROFILE_LATEST_PERIOD))
            except Exception:
                pass
            end_dt = _datetime.now(_timezone.utc).replace(microsecond=0)
            start_dt = end_dt - _timedelta(days=max(days, 1))
            snap = {
                "start": start_dt.isoformat().replace("+00:00", "Z"),
                "end": end_dt.isoformat().replace("+00:00", "Z"),
                "period": MYPROFILE_LATEST_PERIOD,
            }
        except Exception:
            pass

        generated_at = _now_iso_z()

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
                "generated_at_server": generated_at,
            },
            "generated_at": generated_at,
        }

        await _upsert_myprofile_latest_report_row(payload)

        return {
            "status": "ok",
            "user_id": uid,
            "report_mode": report_mode,
            "generated_at": generated_at,
        }
    finally:
        try:
            from generation_lock import release_lock

            if lock_key:
                await release_lock(lock_key=lock_key, owner_id=lock_owner)
        except Exception:
            pass
