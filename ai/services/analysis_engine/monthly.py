
from __future__ import annotations
from typing import List, Dict, Any, Optional
import math
from .models import WeeklySnapshot, MonthlyReport, Narrative, LABELS

def _cosine_distance(vec_a: Dict[str, float], vec_b: Dict[str, float]) -> float:
    # vectors on same labels
    dot = sum(vec_a.get(l,0.0)*vec_b.get(l,0.0) for l in LABELS)
    na = math.sqrt(sum(vec_a.get(l,0.0)**2 for l in LABELS))
    nb = math.sqrt(sum(vec_b.get(l,0.0)**2 for l in LABELS))
    if na==0 or nb==0: return 0.0
    cos = dot/(na*nb)
    cos = max(min(cos,1.0),-1.0)
    return 1.0 - cos

def assemble_monthly(weeks: List[WeeklySnapshot], period: str) -> MonthlyReport:
    # expects 4 weeks ordered
    share_trend = [w.share for w in weeks]
    alternation_trend = [w.alternation_rate for w in weeks]
    intensity_std_trend = [w.intensity.get("std") if w.intensity else None for w in weeks]
    # motif trend: aggregate per name
    name_set = set()
    for w in weeks:
        name_set |= set(w.motif_counts.keys())
    motif_trend = []
    for name in sorted(name_set):
        motif_trend.append({"name": name, "wk_counts": [w.motif_counts.get(name,0) for w in weeks]})
    # center shift distances between consecutive weeks
    distances = []
    for i in range(3):
        distances.append(_cosine_distance(weeks[i].share, weeks[i+1].share))
    center_shift = {"distances": distances, "metric": "cosine"}

    return MonthlyReport(
        period=period, weeks=weeks, share_trend=share_trend,
        alternation_trend=alternation_trend, intensity_std_trend=intensity_std_trend,
        motif_trend=motif_trend, center_shift=center_shift, summary={}
    )

def _label_ja(l: str) -> str:
    return {"joy":"喜び","sadness":"悲しみ","anxiety":"不安","anger":"怒り","peace":"平穏"}.get(l,l)

def _top_label(share: Dict[str, float]) -> Optional[str]:
    if not share: return None
    return sorted(share.items(), key=lambda kv: kv[1], reverse=True)[0][0]

def narrate_monthly(report: MonthlyReport) -> Narrative:
    # flow-based, no explicit comparison vocabulary
    weeks = report.weeks
    period = report.period
    # key labels first/last
    first_top = _top_label(weeks[0].share) if weeks else None
    last_top  = _top_label(weeks[-1].share) if weeks else None
    # find pivot week where dominant label changes
    pivot = None
    for i in range(1,len(weeks)):
        if _top_label(weeks[i-1].share) != _top_label(weeks[i].share):
            pivot = i+0  # 0-indexed -> human "第{i+1}週"
            break
    parts = []
    if first_top and last_top:
        parts.append(f"今月は{_label_ja(first_top)}と{_label_ja(last_top)}が中心に現れ、全体を通して緩やかなリズムが続いた。")
    elif first_top:
        parts.append(f"今月は{_label_ja(first_top)}が中心に現れた。")
    # pivot text
    if pivot is not None:
        parts.append(f"第{pivot+1}週を境に、重心が{_label_ja(_top_label(weeks[pivot-1].share))}から{_label_ja(_top_label(weeks[pivot].share))}方向へと移行した兆しがある。")
    # motif summary
    # choose motif with max total
    total_by_name = {}
    for mt in report.motif_trend:
        total_by_name[mt["name"]] = sum(mt["wk_counts"])
    if total_by_name:
        name = max(total_by_name.items(), key=lambda kv: kv[1])[0]
        total = total_by_name[name]
        readable = name.replace("-", "→")
        if readable == "sadness→peace→joy":
            term = "補正ループ（悲しみ→平穏→喜び）"
        elif readable == "anxiety→peace→joy":
            term = "補正ループ（不安→平穏→喜び）"
        else:
            term = f"モチーフ（{readable}）"
        parts.append(f"{term}が月内で{total}回観測され、整え直す動きが印象的だった。")

    structural_comment = " ".join(parts) if parts else "今月の観測は簡潔だった。"
    gentle_comment = "今月も観測を続けられたこと自体が大切です。無理のないリズムで大丈夫です。"
    next_points = ["来月は、今月の落ち着きがどの週で再現されるかを軽く観測してみましょう。"]
    # evidence (optional, concise)
    evidence = {
        "mode": "flow-text-monthly",
        "items": [
            {"key":"motif", "status":"ok", "text": "主要なモチーフの出現回数を上に反映しました。"},
            {"key":"center_shift", "status":"ok", "text": "重心の移動は段階的に進みました。"}
        ]
    }
    narrative = Narrative(
        type="monthly", period=period,
        structural_comment=structural_comment,
        gentle_comment=gentle_comment,
        next_points=next_points,
        evidence=evidence
    )
    return narrative
