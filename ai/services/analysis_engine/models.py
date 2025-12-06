
from __future__ import annotations
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Optional, Any
import math

LABELS = ["joy", "sadness", "anxiety", "anger", "peace"]

@dataclass
class EmotionEntry:
    id: str
    timestamp: str  # ISO-8601
    date: str       # YYYY-MM-DD (local)
    label: str      # one of LABELS
    intensity: int  # 1..3
    memo: Optional[str] = None

@dataclass
class WeeklySnapshot:
    period: str
    n_events: int
    counts: Dict[str, int]
    wcounts: Dict[str, int]
    share: Dict[str, float]
    daily_share: List[Dict[str, Any]]
    alternation_rate: Optional[float]
    run_stats: Dict[str, float]
    intensity: Dict[str, float]
    motifs: List[Dict[str, str]]
    motif_counts: Dict[str, int]
    entropy: Optional[float]
    gini_simpson: Optional[float]
    center2d: Dict[str, float]
    keywords: List[str] = field(default_factory=list)
    notes: List[str] = field(default_factory=list)

    def to_dict(self):
        return asdict(self)

@dataclass
class MonthlyReport:
    period: str
    weeks: List[WeeklySnapshot]
    share_trend: List[Dict[str, float]]
    alternation_trend: List[Optional[float]]
    intensity_std_trend: List[Optional[float]]
    motif_trend: List[Dict[str, Any]]
    center_shift: Dict[str, Any]
    summary: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self):
        d = asdict(self)
        d["weeks"] = [w.to_dict() for w in self.weeks]
        return d

@dataclass
class BaselineMetric:
    mu: float
    sigma: float
    n: int

@dataclass
class BaselineProfile:
    user_id: str
    window_weeks: int
    window_months: int
    metrics: Dict[str, Any]
    reliability: Dict[str, Any]

    def to_dict(self):
        return asdict(self)

@dataclass
class Narrative:
    type: str  # "weekly" or "monthly"
    period: str
    structural_comment: str
    gentle_comment: str
    next_points: List[str]
    evidence: Dict[str, Any]

    def to_dict(self):
        return asdict(self)
