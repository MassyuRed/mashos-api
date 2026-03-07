
from __future__ import annotations
from typing import List, Dict, Optional
from collections import defaultdict
from datetime import datetime
from .models import EmotionEntry, Narrative, LABELS

# DailyReport (MyNews) — soft, readable, and no numeric exposure.
# Policy:
# - Generate a report only when there is >=1 entry. If 0, raise ValueError so caller can skip.
# - No 'few data' judgement. We never tell the user it was 'few' or 'insufficient' (Mash policy).
# - Sections: headline (top1-2), timeline (morning/afternoon/night), memo quotes (max 3), gentle comment.
# - Tone: softer than Weekly/Monthly. Easy to read in the morning.

def _label_ja(l: str) -> str:
    return {"joy":"喜び","sadness":"悲しみ","anxiety":"不安","anger":"怒り","peace":"平穏"}.get(l,l)

def _top2_labels(entries: List[EmotionEntry]) -> List[str]:
    # intensity-weighted top labels
    counter = defaultdict(int)
    for e in entries:
        counter[e.label] += int(e.intensity or 0)
    sorted_labels = sorted(counter.items(), key=lambda kv: kv[1], reverse=True)
    return [k for k,_ in sorted_labels[:2] if k in LABELS]

def _timeline_block(hour: int) -> str:
    # Simple blocks: morning [5-11], afternoon [12-17], night [18-4]
    if 5 <= hour <= 11:
        return "morning"
    if 12 <= hour <= 17:
        return "afternoon"
    # night: 18..23 or 0..4
    return "night"

def _timeline_summary(entries: List[EmotionEntry]) -> List[str]:
    # For each block, find the modal label among entries in that time block
    blocks = {"morning": [], "afternoon": [], "night": []}
    for e in entries:
        try:
            dt = datetime.fromisoformat(e.timestamp)
            blk = _timeline_block(dt.hour)
            blocks[blk].append(e.label)
        except Exception:
            # If timestamp parse fails, ignore for timeline
            continue
    out = []
    for blk, labels in blocks.items():
        if not labels:
            continue
        # simple mode; fallback to first if ambiguous
        label = max(set(labels), key=labels.count)
        jp = _label_ja(label)
        jp_blk = {"morning":"朝", "afternoon":"昼", "night":"夜"}[blk]
        out.append(f"{jp_blk}は「{jp}」が多く見られました")
    return out

def _quote_memos(entries: List[EmotionEntry], max_items: int = 3) -> List[str]:
    seen = set()
    quotes = []
    for e in entries:
        m = (e.memo or '').strip()
        if not m:
            continue
        if m in seen:
            continue
        seen.add(m)
        quotes.append(m)
        if len(quotes) >= max_items:
            break
    return quotes

def narrate_daily(entries: List[EmotionEntry], period: str) -> Narrative:
    if not entries:
        # Caller should skip DailyReport generation on empty day
        raise ValueError("DailyReport: no EmotionEntry for the day")
    # Headline
    labels = _top2_labels(entries)
    if len(labels) >= 2:
        headline = f"この日は「{_label_ja(labels[0])}」と「{_label_ja(labels[1])}」が中心に現れていました。"
    elif len(labels) == 1:
        headline = f"この日は「{_label_ja(labels[0])}」が主に観測されました。"
    else:
        headline = "この日の観測は控えめでした。"
    # Timeline
    tnotes = _timeline_summary(entries)
    # Memos
    quotes = _quote_memos(entries, max_items=3)

    # Compose structural (softer tone; short sentences; no numbers)
    lines = [headline]
    if tnotes:
        lines.append("時間帯の雰囲気として、" + "／".join(tnotes) + "。")
    if quotes:
        lines.append("メモから少しだけ：")
        for q in quotes:
            lines.append(f"「{q}」")

    structural_comment = "\n".join(lines)
    gentle_comment = "1日おつかれさまでした。あなたの感じたことは、ここにちゃんと残っています。"
    next_points = ["明日も、無理なく一言だけでも記録してみてください。"]

    evidence = {
        "mode": "daily-friendly",
        "items": [],
        "note": "前日の感情を軽く振り返るレポートです（数値は表示しません）。"
    }
    return Narrative(
        type="daily",
        period=period,
        structural_comment=structural_comment,
        gentle_comment=gentle_comment,
        next_points=next_points,
        evidence=evidence
    )
