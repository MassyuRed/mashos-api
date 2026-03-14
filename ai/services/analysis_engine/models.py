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

# ============================================================================
# Self structure analysis models
# ============================================================================
# These dataclasses are shared by:
# - analysis_engine/self_structure_engine/signal_extraction.py
# - analysis_engine/self_structure_engine/fusion.py
# - analysis_engine/self_structure_engine/builders.py
#
# They are intentionally kept here so the self structure engine can reuse the
# existing analysis_engine.models module without introducing a second models
# file for common transport objects.
# ============================================================================


@dataclass
class SelfStructureInput:
    source_type: str
    source_id: str
    timestamp: str  # ISO-8601
    text_primary: str = ""
    text_secondary: str = ""
    prompt_key: Optional[str] = None
    question_text: Optional[str] = None
    emotion_signals: List[str] = field(default_factory=list)
    action_signals: List[str] = field(default_factory=list)
    social_signals: List[str] = field(default_factory=list)
    source_weight: float = 1.0
    answer_mode: Optional[str] = None
    choice_key: Optional[str] = None
    role_hint: Optional[str] = None
    target_hint: Optional[str] = None
    world_kind_hint: Optional[str] = None
    analysis_tags: List[str] = field(default_factory=list)

    def to_dict(self):
        return asdict(self)


@dataclass
class TargetCandidate:
    key: str
    label_ja: str
    target_type: str   # person / environment / activity / concept / self
    domain: str
    score: float

    def to_dict(self):
        return asdict(self)


@dataclass
class TagScore:
    key: str
    label_ja: str
    score: float
    matched_terms: List[str] = field(default_factory=list)

    def to_dict(self):
        return asdict(self)


@dataclass
class RoleScore:
    role_key: str
    score: float
    reasons: List[str] = field(default_factory=list)

    def to_dict(self):
        return asdict(self)


@dataclass
class SurfaceSignals:
    has_negation: bool = False
    has_intent: bool = False
    has_execution: bool = False
    has_inability: bool = False
    has_reason_marker: bool = False

    def to_dict(self):
        return asdict(self)


@dataclass
class SignalExtractionResult:
    source_type: str
    source_id: str
    timestamp: str

    reliability: str
    surface: SurfaceSignals = field(default_factory=SurfaceSignals)

    primary_target: Optional[TargetCandidate] = None
    secondary_targets: List[TargetCandidate] = field(default_factory=list)

    thinking_tags: List[TagScore] = field(default_factory=list)
    action_tags: List[TagScore] = field(default_factory=list)

    role_scores: List[RoleScore] = field(default_factory=list)

    raw_text_primary: str = ""
    raw_text_secondary: str = ""

    def to_dict(self):
        return asdict(self)


@dataclass
class PatternScore:
    key: str
    label_ja: str
    score: float

    def to_dict(self):
        return asdict(self)


@dataclass
class TargetRoleScore:
    target_key: str
    target_label_ja: str
    target_type: str
    role_key: str
    role_label_ja: str
    score: float
    evidence_count: int
    last_seen: Optional[str] = None

    def to_dict(self):
        return asdict(self)


@dataclass
class WorldRoleEvidence:
    world_kind: str   # self / real / desired
    role_key: str
    role_label_ja: str
    score: float
    target_key: Optional[str] = None
    reason: Optional[str] = None

    def to_dict(self):
        return asdict(self)


@dataclass
class RoleGap:
    target_key: Optional[str]
    left_kind: str    # self / real / desired
    left_role: str
    right_kind: str
    right_role: str
    gap_score: float
    note: str

    def to_dict(self):
        return asdict(self)


@dataclass
class UnknownNeed:
    kind: str
    priority: float
    target_key: Optional[str]
    reason: str
    hint: Optional[str] = None

    def to_dict(self):
        return asdict(self)


@dataclass
class TargetSignature:
    target_key: str
    target_label_ja: str
    target_type: str
    top_role_key: str
    top_role_score: float
    top_cluster_key: Optional[str] = None
    top_thinking_keys: List[str] = field(default_factory=list)
    top_action_keys: List[str] = field(default_factory=list)
    evidence_count: int = 0
    last_seen: Optional[str] = None

    def to_dict(self):
        return asdict(self)


@dataclass
class FusionResult:
    stage: str

    template_role_scores: List[PatternScore] = field(default_factory=list)
    cluster_scores: List[PatternScore] = field(default_factory=list)

    target_role_scores: List[TargetRoleScore] = field(default_factory=list)

    thinking_patterns: List[PatternScore] = field(default_factory=list)
    action_patterns: List[PatternScore] = field(default_factory=list)

    self_world_roles: List[WorldRoleEvidence] = field(default_factory=list)
    real_world_roles: List[WorldRoleEvidence] = field(default_factory=list)
    desired_roles: List[WorldRoleEvidence] = field(default_factory=list)
    role_gaps: List[RoleGap] = field(default_factory=list)

    target_signatures: List[TargetSignature] = field(default_factory=list)
    role_history: List[Dict[str, Any]] = field(default_factory=list)
    unknowns: List[UnknownNeed] = field(default_factory=list)

    standard_view: Dict[str, Any] = field(default_factory=dict)
    deep_view: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self):
        return asdict(self)


@dataclass(frozen=True)
class BuildContext:
    target_user_id: str
    snapshot_id: str
    scope: str                 # "global"
    source_hash: str
    analysis_type: str         # "self_structure"
    analysis_version: str      # e.g. "self_structure_v1"
    generated_at: str

    def to_dict(self):
        return asdict(self)
