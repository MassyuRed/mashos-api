from __future__ import annotations
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Optional, Any
import math

LABELS = ["joy", "sadness", "anxiety", "anger", "peace"]


def _with_time_bucket_aliases(d: Dict[str, Any]) -> Dict[str, Any]:
    if "time_buckets" in d and "timeBuckets" not in d:
        d["timeBuckets"] = d.get("time_buckets")
    return d


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
    time_buckets: List[Dict[str, Any]] = field(default_factory=list)

    def to_dict(self):
        return _with_time_bucket_aliases(asdict(self))


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
    time_buckets: List[Dict[str, Any]] = field(default_factory=list)

    def to_dict(self):
        d = asdict(self)
        d["weeks"] = [w.to_dict() for w in self.weeks]
        return _with_time_bucket_aliases(d)


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


@dataclass
class TransitionEdge:
    from_label: str
    to_label: str
    count: int
    share: Optional[float] = None
    mean_minutes: Optional[float] = None
    median_minutes: Optional[float] = None
    p75_minutes: Optional[float] = None
    mean_intensity_from: Optional[float] = None
    mean_intensity_to: Optional[float] = None
    dominant_time_buckets: List[str] = field(default_factory=list)
    evidence: Dict[str, Any] = field(default_factory=dict)
    notes: List[str] = field(default_factory=list)

    def to_dict(self):
        return asdict(self)


@dataclass
class RecoveryTime:
    from_label: str
    to_label: str
    count: int
    mean_minutes: Optional[float] = None
    median_minutes: Optional[float] = None
    min_minutes: Optional[float] = None
    max_minutes: Optional[float] = None
    dominant_time_buckets: List[str] = field(default_factory=list)
    evidence: Dict[str, Any] = field(default_factory=dict)
    notes: List[str] = field(default_factory=list)

    def to_dict(self):
        return asdict(self)


@dataclass
class MemoTrigger:
    keyword: str
    count: int
    related_emotions: List[str] = field(default_factory=list)
    related_transitions: List[str] = field(default_factory=list)
    dominant_time_buckets: List[str] = field(default_factory=list)
    evidence: Dict[str, Any] = field(default_factory=dict)
    notes: List[str] = field(default_factory=list)

    def to_dict(self):
        return asdict(self)


@dataclass
class ControlPattern:
    pattern_id: str
    label: str
    description: str
    size: int
    score: Optional[float] = None
    transition_keys: List[str] = field(default_factory=list)
    representative_edges: List[TransitionEdge] = field(default_factory=list)
    memo_triggers: List[MemoTrigger] = field(default_factory=list)
    dominant_time_buckets: List[str] = field(default_factory=list)
    evidence: Dict[str, Any] = field(default_factory=dict)
    notes: List[str] = field(default_factory=list)

    def to_dict(self):
        return asdict(self)


@dataclass
class DeepControlModel:
    period: str
    scope: str
    transition_matrix: Dict[str, Dict[str, int]]
    transition_edges: List[TransitionEdge] = field(default_factory=list)
    recovery_time: List[RecoveryTime] = field(default_factory=list)
    memo_triggers: List[MemoTrigger] = field(default_factory=list)
    control_patterns: List[ControlPattern] = field(default_factory=list)
    summary: Dict[str, Any] = field(default_factory=dict)
    meta: Dict[str, Any] = field(default_factory=dict)
    notes: List[str] = field(default_factory=list)

    def to_dict(self):
        d = asdict(self)
        d["transitionMatrix"] = d.get("transition_matrix")
        d["transitionEdges"] = d.get("transition_edges")
        d["recoveryTime"] = d.get("recovery_time")
        d["memoTriggers"] = d.get("memo_triggers")
        d["controlPatterns"] = d.get("control_patterns")
        return d
