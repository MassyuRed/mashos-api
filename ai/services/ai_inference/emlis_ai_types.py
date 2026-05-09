# -*- coding: utf-8 -*-
from __future__ import annotations

"""Shared types for the EmlisAI reply pipeline.

This file stays dependency-light so the reply pipeline can share typed payloads
without introducing circular imports.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Literal, Optional, Tuple

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
    "word_reflection",
    "emotion_response",
    "selected_emotions",
    "continuity",
    "change",
    "recovery",
    "topic_anchor",
    "interpretation",
    "preference",
    "partner_line",
    "receiving_close",
]
MemoryLayer = Literal[
    "canonical_history",
    "derived_user_model",
    "side_state",
    "cross_core_context",
]
ReplyLengthMode = Literal[
    "short_present_only",
    "input_scaled",
    "input_and_history_scaled",
]
SourceScope = Literal[
    "current_input_only",
    "current_input_with_owned_history",
    "current_input_with_owned_history_and_cross_core",
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
    source_scope: SourceScope = "current_input_only"
    cross_core_enabled: bool = False
    structure_model_enabled: bool = False


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


@dataclass(frozen=True)
class EmotionDisplayItem:
    type: str
    strength: str = ""
    strength_label: str = ""
    role: str = "secondary"


@dataclass(frozen=True)
class UserWordAnchor:
    anchor_key: str
    text: str
    source_field: str = "memo"
    role: str = "other"
    evidence: List[EvidenceRef] = field(default_factory=list)
    confidence: float = 1.0


@dataclass(frozen=True)
class ShapedUserPhrase:
    anchor_key: str
    raw_text: str
    phrase: str
    sentence_fragment: str
    nominal: str
    role: str
    source_field: str
    usability: str = "safe"
    unsafe_reasons: List[str] = field(default_factory=list)
    evidence: List[EvidenceRef] = field(default_factory=list)




@dataclass(frozen=True)
class InputMeaningBlock:
    """A source-bound meaning unit extracted from a clear long current input.

    ``UserWordAnchor`` and ``ShapedUserPhrase`` are small fragments. For long
    inputs, EmlisAI and Piece need a higher-level unit so the final reply does
    not compress the whole entry into one narrow focus.
    """

    block_key: str
    role: str
    title: str
    summary: str
    user_phrases: List[ShapedUserPhrase] = field(default_factory=list)
    evidence: List[EvidenceRef] = field(default_factory=list)
    priority: float = 0.0
    clarity: float = 0.0
    include_in_emlis_reply: bool = False
    include_in_piece_core: bool = False


@dataclass(frozen=True)
class MeaningCoveragePlan:
    input_level: str
    clear_long_input: bool
    meaning_block_count: int
    required_roles: List[str] = field(default_factory=list)
    selected_block_keys: List[str] = field(default_factory=list)
    min_blocks_to_cover: int = 0
    max_blocks_to_cover: int = 0
    coverage_ratio_target: float = 0.0
    reason: str = ""


@dataclass(frozen=True)
class EmlisDepthReplyPlan:
    input_level: str
    clear_long_input: bool
    target_lines: int
    min_meaning_blocks: int
    selected_block_keys: List[str] = field(default_factory=list)
    line_roles: List[str] = field(default_factory=list)
    allow_paragraph_breaks: bool = False
    require_presence_line: bool = True
    reason: str = ""

@dataclass(frozen=True)
class WholeInputMeaningArc:
    """Ordered meaning flow for a clear long current input.

    Meaning blocks capture individual units.  The arc keeps the user's own flow
    so EmlisAI and Piece do not collapse a detailed entry into one generic topic.
    """

    arc_key: str
    title: str
    summary: str
    ordered_block_keys: List[str] = field(default_factory=list)
    tension_pairs: List[Tuple[str, str]] = field(default_factory=list)
    core_wish_keys: List[str] = field(default_factory=list)
    fear_keys: List[str] = field(default_factory=list)
    present_action_keys: List[str] = field(default_factory=list)
    clarity: float = 0.0
    evidence: List[EvidenceRef] = field(default_factory=list)


@dataclass(frozen=True)
class MajorMeaningRetentionPlan:
    """Coverage contract for meanings that must not be dropped from long input."""

    clear_long_input: bool
    total_block_count: int
    must_keep_block_keys: List[str] = field(default_factory=list)
    should_keep_block_keys: List[str] = field(default_factory=list)
    optional_block_keys: List[str] = field(default_factory=list)
    forbidden_overcompression_targets: List[str] = field(default_factory=list)
    min_must_keep_coverage_ratio: float = 0.0
    reason: str = ""


@dataclass(frozen=True)
class EmlisWholeInputReplyPlan:
    input_level: str
    clear_long_input: bool
    target_lines: int
    must_keep_block_keys: List[str] = field(default_factory=list)
    covered_block_keys: List[str] = field(default_factory=list)
    require_presence_line: bool = True
    reason: str = ""




@dataclass(frozen=True)
class ResponseCompositionPlan:
    """Reply-level composition contract for long clear current inputs.

    Meaning blocks decide what to keep.  This plan decides how those meanings are
    ordered for a human reader: opening thesis first, then background, limit,
    realization, new direction, and companion presence.
    """

    composition_key: str
    input_level: str
    clear_long_input: bool
    narrative_pattern: str
    opening_role: str
    ordered_line_roles: List[str] = field(default_factory=list)
    required_line_roles: List[str] = field(default_factory=list)
    optional_line_roles: List[str] = field(default_factory=list)
    transition_policy: str = "guarded"
    require_opening_thesis: bool = True
    require_presence_line: bool = True
    allow_paragraph_breaks: bool = True
    max_lines: int = 9
    min_lines: int = 4
    reason: str = ""


@dataclass(frozen=True)
class ReplyNarrativeArc:
    """A reading order for EmlisAI's response to the current input."""

    arc_key: str
    title: str
    opening_thesis: str
    ordered_roles: List[str] = field(default_factory=list)
    role_to_block_keys: Dict[str, List[str]] = field(default_factory=dict)
    transition_groups: Dict[str, str] = field(default_factory=dict)
    grounding_required: bool = True
    clarity: float = 0.0
    evidence: List[EvidenceRef] = field(default_factory=list)


@dataclass(frozen=True)
class CompositionLinePlan:
    line_role: str
    candidate_key: str
    required: bool = False
    block_keys: List[str] = field(default_factory=list)
    allowed_opening_connectors: List[str] = field(default_factory=list)
    forbidden_when_first_content_line: bool = False
    evidence: List[EvidenceRef] = field(default_factory=list)


@dataclass(frozen=True)
class ReplyEndingPlan:
    line_index: int
    line_role: str
    preferred_ending_group: str
    avoid_endings: List[str] = field(default_factory=list)


@dataclass(frozen=True)
class FinalReviewIssue:
    code: str
    severity: str
    line_index: Optional[int] = None
    message: str = ""


@dataclass(frozen=True)
class FinalReviewResult:
    passed: bool
    issues: List[FinalReviewIssue] = field(default_factory=list)
    repaired_text: Optional[str] = None
    review_version: str = "emlis.final_reader.v1"


@dataclass(frozen=True)
class ReplyRepairResult:
    text: str
    repair_attempted: bool = False
    repair_passed: bool = False
    safe_fallback_used: bool = False
    issue_codes: List[str] = field(default_factory=list)


@dataclass(frozen=True)
class CurrentInputReading:
    selected_emotions: List[EmotionDisplayItem] = field(default_factory=list)
    dominant_emotion: Optional[EmotionDisplayItem] = None
    secondary_emotions: List[EmotionDisplayItem] = field(default_factory=list)
    user_word_anchors: List[UserWordAnchor] = field(default_factory=list)
    shaped_user_phrases: List[ShapedUserPhrase] = field(default_factory=list)
    response_mode: str = "receive"
    memo_richness: str = "none"




@dataclass(frozen=True)
class UnderstandingFrame:
    event: Optional[UserWordAnchor] = None
    action: Optional[UserWordAnchor] = None
    relationship_or_other: Optional[UserWordAnchor] = None
    boundary_violation: Optional[UserWordAnchor] = None
    self_awareness: Optional[UserWordAnchor] = None
    self_fault_awareness: Optional[UserWordAnchor] = None
    self_avoidance: Optional[UserWordAnchor] = None
    justification: Optional[UserWordAnchor] = None
    fear_of_rejection: Optional[UserWordAnchor] = None
    self_dislike: Optional[UserWordAnchor] = None
    guilt_or_remorse: Optional[UserWordAnchor] = None
    explicit_emotion: Optional[UserWordAnchor] = None
    need_or_wish: Optional[UserWordAnchor] = None
    unresolved: Optional[UserWordAnchor] = None
    work_frustration: Optional[UserWordAnchor] = None
    mentor_attachment: Optional[UserWordAnchor] = None
    missing_guidance: Optional[UserWordAnchor] = None
    effort_confusion: Optional[UserWordAnchor] = None
    anger_surface: Optional[UserWordAnchor] = None
    sadness_surface: Optional[UserWordAnchor] = None
    relief_source: Optional[UserWordAnchor] = None
    chat_relief: Optional[UserWordAnchor] = None
    fatigue_accumulation: Optional[UserWordAnchor] = None
    relation_patterns: List[str] = field(default_factory=list)
    confidence: float = 0.0
    evidence: List[EvidenceRef] = field(default_factory=list)




@dataclass(frozen=True)
class EmlisContextAnchorPacket:
    schema_version: str
    source_kind: str
    source_id: Optional[str] = None
    source_updated_at: Optional[str] = None
    value_anchors: List[Dict[str, Any]] = field(default_factory=list)
    state_anchors: List[Dict[str, Any]] = field(default_factory=list)
    individuality_anchors: List[Dict[str, Any]] = field(default_factory=list)
    boundary_anchors: List[Dict[str, Any]] = field(default_factory=list)
    concept_anchors: List[Dict[str, Any]] = field(default_factory=list)
    reply_hints: List[Dict[str, Any]] = field(default_factory=list)
    evidence_refs: List[Dict[str, Any]] = field(default_factory=list)
    safety: Dict[str, Any] = field(default_factory=dict)

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
    cross_core_context: List[EmlisContextAnchorPacket] = field(default_factory=list)
    derived_user_model: Optional[DerivedUserModel] = None
    side_state: Dict[str, Any] = field(default_factory=dict)
    input_effort: Dict[str, Any] = field(default_factory=dict)
    memory_richness: Dict[str, Any] = field(default_factory=dict)
    debug: Dict[str, Any] = field(default_factory=dict)




@dataclass(frozen=True)
class ObservationTensionPair:
    left: str
    right: str
    relation: str = "tension"


@dataclass(frozen=True)
class EmlisObservationFrame:
    primary_state: str = ""
    tension_pairs: List[ObservationTensionPair] = field(default_factory=list)
    pressure_sources: List[str] = field(default_factory=list)
    escape_or_limit_signal: str = ""
    self_awareness_signal: str = ""
    strength_signal: str = ""
    companion_close: str = ""
    evidence_terms: List[str] = field(default_factory=list)
    required_line_roles: List[str] = field(default_factory=list)
    evidence: List[EvidenceRef] = field(default_factory=list)

@dataclass
class WorldModelFacts:
    dominant_emotion: Optional[str] = None
    dominant_strength: Optional[str] = None
    has_memo_input: bool = False
    selected_emotions: List[EmotionDisplayItem] = field(default_factory=list)
    secondary_emotions: List[EmotionDisplayItem] = field(default_factory=list)
    user_word_anchors: List[UserWordAnchor] = field(default_factory=list)
    shaped_user_phrases: List[ShapedUserPhrase] = field(default_factory=list)
    response_mode: str = "receive"
    memo_richness: str = "none"
    understanding_frame: Optional[UnderstandingFrame] = None
    understanding_patterns: List[str] = field(default_factory=list)
    meaning_blocks: List[InputMeaningBlock] = field(default_factory=list)
    meaning_coverage_plan: Optional[MeaningCoveragePlan] = None
    whole_input_meaning_arc: Optional[WholeInputMeaningArc] = None
    major_meaning_retention_plan: Optional[MajorMeaningRetentionPlan] = None
    response_composition_plan: Optional[ResponseCompositionPlan] = None
    reply_narrative_arc: Optional[ReplyNarrativeArc] = None
    emlis_observation_frame: Optional[EmlisObservationFrame] = None
    same_day_input_count: int = 0
    week_input_count: int = 0
    month_input_count: int = 0
    streak_days: int = 0
    last_input_at: Optional[str] = None
    weekly_top_emotions: List[str] = field(default_factory=list)
    current_categories: List[str] = field(default_factory=list)
    current_emotion_labels: List[str] = field(default_factory=list)
    cross_core_context: List[EmlisContextAnchorPacket] = field(default_factory=list)
    latest_today_question_text: Optional[str] = None
    latest_today_question_answer_text: Optional[str] = None
    value_observation_signals: List[Any] = field(default_factory=list)
    value_observation_plan: Optional[Any] = None


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
    tier_ceiling: int = 0
    evidence_ceiling: int = 0
    target_lines: int = 0
    user_word_anchor_count: int = 0
    history_usable: bool = False
    interpretive_frame_usable: bool = False
    cross_core_usable: bool = False
    meaning_block_count: int = 0
    selected_meaning_block_count: int = 0
    meaning_coverage_ratio: float = 0.0
    clear_long_input: bool = False
    major_must_keep_count: int = 0
    major_must_keep_covered_count: int = 0
    major_must_keep_coverage_ratio: float = 0.0


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
