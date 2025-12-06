
from __future__ import annotations
from typing import List, Dict, Any, Optional
import statistics
from .models import WeeklySnapshot, BaselineProfile

def build_baseline(user_id: str, weeks: List[WeeklySnapshot], window_weeks:int=3, window_months:int=2) -> BaselineProfile:
    # Use last W weeks
    W = min(window_weeks, len(weeks))
    sub = weeks[-W:] if W>0 else []
    metrics: Dict[str, Any] = {}
    reliability = {
        "coverage_weeks": len(sub),
        "coverage_months": 0,  # not used here
        "data_density": float(statistics.median([w.n_events for w in sub])) if sub else 0.0,
        "last_period": sub[-1].period if sub else None
    }
    def _agg_scalar(values: List[float]) -> Dict[str, float]:
        if not values:
            return {"mu": 0.0, "sigma": 0.0, "n": 0}
        if len(values)==1:
            return {"mu": float(values[0]), "sigma": 0.0, "n": 1}
        return {"mu": float(statistics.mean(values)), "sigma": float(statistics.pstdev(values)), "n": len(values)}
    # alternation
    metrics["alternation"] = _agg_scalar([w.alternation_rate for w in sub if w.alternation_rate is not None])
    # intensity std
    metrics["intensity_std"] = _agg_scalar([w.intensity.get("std") for w in sub if w.intensity and w.intensity.get("std") is not None])
    # entropy & gini
    metrics["entropy"] = _agg_scalar([w.entropy for w in sub if w.entropy is not None])
    metrics["gini_simpson"] = _agg_scalar([w.gini_simpson for w in sub if w.gini_simpson is not None])
    # motifs (per name)
    all_names = set()
    for w in sub:
        for name in (w.motif_counts or {}).keys():
            all_names.add(name)
    motif_metrics = {}
    for name in all_names:
        motif_metrics[name] = _agg_scalar([w.motif_counts.get(name,0) for w in sub])
    metrics["motif"] = motif_metrics
    # center2d
    metrics["center2d"] = {
        "x": _agg_scalar([w.center2d.get("x") for w in sub]),
        "y": _agg_scalar([w.center2d.get("y") for w in sub]),
        "n": len(sub)
    }
    return BaselineProfile(
        user_id=user_id,
        window_weeks=window_weeks,
        window_months=window_months,
        metrics=metrics,
        reliability=reliability
    )
