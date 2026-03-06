# analysis_engine_adapter.py
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from analysis_engine.models import EmotionEntry

JP_TO_LABEL = {
    "喜び": "joy",
    "悲しみ": "sadness",
    "不安": "anxiety",
    "怒り": "anger",
    "平穏": "peace",
}

STRENGTH_TO_INTENSITY = {
    "weak": 1,
    "medium": 2,
    "strong": 3,
}

SELF_INSIGHT_LABELS = {"自己理解", "SelfInsight"}


def _parse_iso_to_local_date(iso_str: str) -> str:
    s = str(iso_str or "").strip()
    if not s:
        return ""
    if s.endswith("Z"):
        s = s[:-1] + "+00:00"
    dt = datetime.fromisoformat(s)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    # ここでは snapshot 側がJST基準で期間切っているので、
    # 表示上の日付はUTC→ローカル日付文字列として十分
    return dt.astimezone().date().isoformat()


def _normalize_details(row: Dict[str, Any]) -> List[Dict[str, Any]]:
    details = row.get("emotion_details")
    if isinstance(details, list):
        out: List[Dict[str, Any]] = []
        for it in details:
            if not isinstance(it, dict):
                continue
            t = str(it.get("type") or "").strip()
            s = str(it.get("strength") or "medium").strip().lower()
            if not t or t in SELF_INSIGHT_LABELS:
                continue
            if s not in STRENGTH_TO_INTENSITY:
                s = "medium"
            out.append({"type": t, "strength": s})
        return out

    emos = row.get("emotions")
    if isinstance(emos, list):
        out = []
        for t in emos:
            tt = str(t or "").strip()
            if not tt or tt in SELF_INSIGHT_LABELS:
                continue
            out.append({"type": tt, "strength": "medium"})
        return out

    return []


def build_emotion_entries_from_rows(rows: List[Dict[str, Any]]) -> List[EmotionEntry]:
    entries: List[EmotionEntry] = []

    for row in rows or []:
        row_id = str(row.get("id") or "").strip()
        created_at = str(row.get("created_at") or "").strip()
        memo = (row.get("memo") or None)

        if not row_id or not created_at:
            continue

        date_str = _parse_iso_to_local_date(created_at)
        details = _normalize_details(row)

        for idx, d in enumerate(details):
            jp = str(d.get("type") or "").strip()
            label = JP_TO_LABEL.get(jp)
            if not label:
                continue

            strength = str(d.get("strength") or "medium").strip().lower()
            intensity = STRENGTH_TO_INTENSITY.get(strength, 2)

            entries.append(
                EmotionEntry(
                    id=f"{row_id}:{idx}",
                    timestamp=created_at,
                    date=date_str,
                    label=label,
                    intensity=intensity,
                    memo=memo,
                )
            )

    entries.sort(key=lambda x: x.timestamp)
    return entries