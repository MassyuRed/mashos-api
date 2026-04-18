# -*- coding: utf-8 -*-
from __future__ import annotations

"""Shared types for the EmlisAI reply pipeline.

This file stays dependency-light so the reply pipeline can share typed payloads
without introducing circular imports.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Literal, Optional

HistoryMode = Literal["none", "extended", "full"]
ContinuityMode = Literal["off", "basic", "advanced"]
StyleMode = Literal["base", "adaptive", "personalized"]
PartnerMode = Literal["off", "on_basic", "on_advanced"]
ModelMode = Literal["off", "compact", "deep"]
InterpretationMode = Literal[
    "current_only",
    "memory_aligned",
    "precision_aligned",
]
StyleFamily = Literal[
    "accepting",
    "sensitive",
    "analytical",
    "structured",
    "action_oriented",
]
CandidateKind = Literal[
    "receive",
    "continuity",
    "change",
    "recovery",
    "topic_anchor",
    "interpretation",
    "preference",
    "partner_line",
]
MemoryLayer = Literal[
    "canonical_history",
    "derived_user_model",
    "side_state",
]
ReplyLengthMode = Literal[
    "short_present_only",
    "input_scaled",
    "input_and_history_scaled",
]
HypothesisStatus = Literal["active", "stale", "suppressed"]


@dataclass(frozen=True)
class EmlisAICapabilityConfig:
    tier: str
    history_mode: HistoryMode
    continuity_mode: ContinuityMode
    style_mode: StyleMode
    partner_mode: PartnerMode
    retrieval_window_days: Optional[int] = None
    max_same_day_inputs: int = 3
    max_similar_inputs: int = 3
    include_input_summary: bool = True
    include_myweb_summary: bool = False
    include_today_question_history: bool = False
    include_long_term_history: bool = False
    strict_evidence_mode: bool = True
    model_mode: ModelMode = "off"
    interpretation_mode: InterpretationMode = "current_only"
    model_read_enabled: bool = False
    model_write_enabled: bool = False
    max_anchor_count: int = 0
    max_hypothesis_count: int = 0
    max_reply_lines: int = 3
    reply_length_mode: ReplyLengthMode = "short_present_only"
    include_derived_user_model: bool = False


@dataclass(frozen=True)
class GreetingDecision:
    slot_name: str
    slot_key: str
    greeting_text: str
    first_in_slot: bool


@dataclass(frozen=True)
class EvidenceRef:
    kind: str
    ref_id: str
    weight: float = 1.0
    note: Optional[str] = None


@dataclass
class SourceCursor:
    last_emotion_id: Optional[str] = None
    last_emotion_created_at: Optional[str] = None
    last_today_question_answer_id: Optional[str] = None


@dataclass
class ValueAnchor:
    key: str
    confidence: float = 0.0
    evidence: List[EvidenceRef] = field(default_factory=list)
    last_seen_at: Optional[str] = None


@dataclass
class MeaningMapEntry:
    trigger: str
    likely_meaning: str
    confidence: float = 0.0
    evidence: List[EvidenceRef] = field(default_factory=list)
    last_seen_at: Optional[str] = None


@dataclass
class ResponsePreferenceCues:
    prefers_receive_first: bool = False
    prefers_structure_when_long_memo: bool = False
    prefers_continuity_reference: bool = False
    evidence: List[EvidenceRef] = field(default_factory=list)


@dataclass
class PartnerExpectationProfile:
    wants_continuity: bool = False
    wants_non_judgmental_receive: bool = False
    wants_precise_observation: bool = False
    evidence: List[EvidenceRef] = field(default_factory=list)


@dataclass
class InterpretiveFrameProfile:
    value_anchors: List[ValueAnchor] = field(default_factory=list)
    meaning_map: List[MeaningMapEntry] = field(default_factory=list)
    response_preference_cues: ResponsePreferenceCues = field(default_factory=ResponsePreferenceCues)
    partner_expectation: PartnerExpectationProfile = field(default_factory=PartnerExpectationProfile)
    sensitivity_cues: Dict[str, Any] = field(default_factory=dict)
    expression_style_cues: Dict[str, Any] = field(default_factory=dict)


@dataclass
class DerivedModelHypothesis:
    key: str
    text: str
    confidence: float = 0.0
    evidence: List[EvidenceRef] = field(default_factory=list)
    status: HypothesisStatus = "active"
    last_seen_at: Optional[str] = None


@dataclass
class TopicAnchor:
    anchor_key: str
    label: str
    confidence: float = 0.0
    evidence: List[EvidenceRef] = field(default_factory=list)
    last_seen_at: Optional[str] = None


@dataclass
class DerivedUserModel:
    schema_version: str
    model_tier: str
    source_cursor: SourceCursor = field(default_factory=SourceCursor)
    factual_profile: Dict[str, Any] = field(default_factory=dict)
    interpretive_frame: InterpretiveFrameProfile = field(default_factory=InterpretiveFrameProfile)
    hypotheses: List[DerivedModelHypothesis] = field(default_factory=list)
    open_topic_anchors: List[TopicAnchor] = field(default_factory=list)
    recovery_anchors: List[TopicAnchor] = field(default_factory=list)
    updated_at: Optional[str] = None
    debug: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SourceBundle:
    user_id: str
    display_name: Optional[str]
    current_input: Dict[str, Any]
    greeting: Optional[GreetingDecision] = None
    last_input: Optional[Dict[str, Any]] = None
    same_day_recent_inputs: List[Dict[str, Any]] = field(default_factory=list)
    similar_inputs: List[Dict[str, Any]] = field(default_factory=list)
    input_summary: Dict[str, Any] = field(default_factory=dict)
    myweb_home_summary: Dict[str, Any] = field(default_factory=dict)
    latest_today_question_answer: Dict[str, Any] = field(default_factory=dict)
    recent_today_question_answers: List[Dict[str, Any]] = field(default_factory=list)
    derived_user_model: Optional[DerivedUserModel] = None
    side_state: Dict[str, Any] = field(default_factory=dict)
    input_effort: Dict[str, Any] = field(default_factory=dict)
    memory_richness: Dict[str, Any] = field(default_factory=dict)
    debug: Dict[str, Any] = field(default_factory=dict)


@dataclass
class WorldModelFacts:
    dominant_emotion: Optional[str] = None
    dominant_strength: Optional[str] = None
    has_memo_input: bool = False
    same_day_input_count: int = 0
    week_input_count: int = 0
    month_input_count: int = 0
    streak_days: int = 0
    last_input_at: Optional[str] = None
    weekly_top_emotions: List[str] = field(default_factory=list)
    current_categories: List[str] = field(default_factory=list)
    current_emotion_labels: List[str] = field(default_factory=list)
    latest_today_question_text: Optional[str] = None
    latest_today_question_answer_text: Optional[str] = None


@dataclass
class WorldModelHypothesis:
    key: str
    text: str
    evidence: List[EvidenceRef] = field(default_factory=list)
    confidence: float = 0.0


@dataclass
class WorldModel:
    facts: WorldModelFacts
    hypotheses: List[WorldModelHypothesis] = field(default_factory=list)
    unknowns: List[str] = field(default_factory=list)
    conflicts: List[str] = field(default_factory=list)
    rejected_hypotheses: List[WorldModelHypothesis] = field(default_factory=list)
    debug: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class StyleProfile:
    family: StyleFamily
    tone_reason: str
    lexical_softness: str = "soft"
    structure_density: str = "light"


@dataclass
class ObservationCandidate:
    candidate_key: str
    kind: CandidateKind
    text: str
    evidence: List[EvidenceRef] = field(default_factory=list)
    confidence: float = 0.0
    recency_score: float = 0.0
    alignment_score: float = 0.0
    overclaim_risk: float = 0.0
    source_layers: List[MemoryLayer] = field(default_factory=list)
    notes: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SentenceEvidence:
    line_key: str
    evidence: List[EvidenceRef] = field(default_factory=list)


@dataclass
class ReplyLine:
    key: str
    text: str
    sentence_evidence: SentenceEvidence
    candidate_key: Optional[str] = None


@dataclass
class ReplyLengthPlan:
    mode: ReplyLengthMode
    max_lines: int
    reason: str
    input_effort_score: float = 0.0
    memory_richness_score: float = 0.0


@dataclass
class ObservationDecision:
    accepted_candidates: List[ObservationCandidate] = field(default_factory=list)
    rejected_candidates: List[ObservationCandidate] = field(default_factory=list)
    unknowns: List[str] = field(default_factory=list)
    conflicts: List[str] = field(default_factory=list)
    reply_lines: List[ReplyLine] = field(default_factory=list)
    reply_length_plan: Optional[ReplyLengthPlan] = None
    debug: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ReplyPlan:
    receive: str = ""
    continuity: str = ""
    change: str = ""
    partner_line: str = ""
    reply_lines: List[ReplyLine] = field(default_factory=list)
    used_evidence: List[EvidenceRef] = field(default_factory=list)
    rejected_candidates: List[ObservationCandidate] = field(default_factory=list)
    reply_length_plan: Optional[ReplyLengthPlan] = None
    notes: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ReplyEnvelope:
    comment_text: str
    meta: Dict[str, Any] = field(default_factory=dict)
    used_evidence: List[EvidenceRef] = field(default_factory=list)
    evidence_by_line: Dict[str, List[EvidenceRef]] = field(default_factory=dict)
    used_memory_layers: List[MemoryLayer] = field(default_factory=list)
    fallback_used: bool = False
