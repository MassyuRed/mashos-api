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


# ---------------------------------------------------------------------------
# EmlisAI multi-perspective observation architecture (2026-05-09)
# ---------------------------------------------------------------------------

ObservationRiskLevel = Literal["low", "medium", "high"]
ObservationStatus = Literal["passed", "rejected", "unavailable", "safety_blocked"]
DiagnosticStage = Literal[
    "flag",
    "rollout",
    "scope",
    "composer",
    "reader",
    "grounding",
    "template",
    "display",
]


@dataclass(frozen=True)
class DiagnosticGateResult:
    passed: bool
    rejection_reasons: List[str] = field(default_factory=list)
    primary_reason: str = ""
    reason_category: str = ""
    diagnostics: Dict[str, Any] = field(default_factory=dict)

    def as_meta(self) -> Dict[str, Any]:
        diagnostics = dict(self.diagnostics or {})
        data = {
            "passed": bool(self.passed),
            "status": "passed" if self.passed else "failed",
            "primary_reason": self.primary_reason or ("passed" if self.passed else "gate_failed"),
            "rejection_reasons": list(self.rejection_reasons),
            "reason_category": self.reason_category or ("passed" if self.passed else "gate_general"),
            "diagnostics": diagnostics,
        }
        # Step 7 keeps binding visibility at the gate result level so the
        # diagnostic summary can be read without drilling into gate-specific
        # diagnostics. This is meta-only and does not change pass/fail behavior.
        for key in (
            "binding_used",
            "binding_present",
            "binding_available",
            "binding_missing",
            "binding_required",
            "binding_count",
            "sentence_count",
            "expected_binding_count",
            "binding_version",
            "step7_gate_binding_reflection",
        ):
            if key in diagnostics:
                data[key] = diagnostics[key]
        return data


@dataclass(frozen=True)
class EmlisAIDiagnosticSummary:
    """Developer-facing stop-point summary for the Emlis observation pipeline.

    This object is meta only. It must not be copied into user-facing
    ``comment_text``. It makes the B-D0 diagnostic path explicit: one
    submitted input can be classified by the first meaningful stage that
    stopped or passed the B-plan observation path.
    """

    observation_status: ObservationStatus
    stage: DiagnosticStage
    primary_reason: str
    secondary_reasons: List[str] = field(default_factory=list)
    feature_flag_enabled: bool = False
    rollout_stage: str = ""
    scope_status: str = ""
    coverage_scope: str = ""
    scope_diagnostic: Dict[str, Any] = field(default_factory=dict)
    scope_rejection_reasons: List[str] = field(default_factory=list)
    scope_safety_boundaries: List[str] = field(default_factory=list)
    scope_excluded_reason_codes: List[str] = field(default_factory=list)
    scope_reason_category: str = ""
    scope_coverage_matrix_hints: List[str] = field(default_factory=list)
    composer_model: str = ""
    composer_status: str = ""
    composer_diagnostic: Dict[str, Any] = field(default_factory=dict)
    composer_rejection_reasons: List[str] = field(default_factory=list)
    composer_reason_category: str = ""
    composer_coverage_matrix_hints: List[str] = field(default_factory=list)
    gate_diagnostic: Dict[str, Any] = field(default_factory=dict)
    gate_rejection_reasons: List[str] = field(default_factory=list)
    gate_reason_category: str = ""
    gate_coverage_matrix_hints: List[str] = field(default_factory=list)
    gate_failure_stage: str = ""
    safety_boundary: Dict[str, Any] = field(default_factory=dict)
    coverage_matrix: Dict[str, Any] = field(default_factory=dict)
    coverage_groups: List[str] = field(default_factory=list)
    coverage_primary_group: str = ""
    coverage_next_steps: List[str] = field(default_factory=list)
    coverage_unclassified_reasons: List[str] = field(default_factory=list)
    coverage_unmapped_reasons: List[str] = field(default_factory=list)
    feature_flag_state: Dict[str, Any] = field(default_factory=dict)
    release_enabled: bool = False
    release_cohort: str = ""
    release_reason_code: str = ""
    release_decision: Dict[str, Any] = field(default_factory=dict)
    default_composer_resolution: Dict[str, Any] = field(default_factory=dict)
    rollout_decision: Dict[str, Any] = field(default_factory=dict)
    registry_resolution: Dict[str, Any] = field(default_factory=dict)
    pre_connection: Dict[str, Any] = field(default_factory=dict)
    b_plan_connection: Dict[str, Any] = field(default_factory=dict)
    normal_connection: Dict[str, Any] = field(default_factory=dict)
    composer_connection_attempted: bool = False
    rollout_attempted: bool = False
    used_evidence_span_count: int = 0
    included_claim_count: int = 0
    excluded_claim_count: int = 0
    comment_text_allowed: bool = False
    gate_results: Dict[str, DiagnosticGateResult] = field(default_factory=dict)

    def as_meta(self) -> Dict[str, Any]:
        return {
            "version": "emlis.diagnostic_summary.v1",
            "observation_status": self.observation_status,
            "stage": self.stage,
            "primary_reason": self.primary_reason,
            "secondary_reasons": list(self.secondary_reasons),
            "feature_flag_enabled": bool(self.feature_flag_enabled),
            "rollout_stage": self.rollout_stage,
            "scope_status": self.scope_status,
            "coverage_scope": self.coverage_scope,
            "scope_diagnostic": dict(self.scope_diagnostic or {}),
            "scope_rejection_reasons": list(self.scope_rejection_reasons or []),
            "scope_safety_boundaries": list(self.scope_safety_boundaries or []),
            "scope_excluded_reason_codes": list(self.scope_excluded_reason_codes or []),
            "scope_reason_category": self.scope_reason_category,
            "scope_coverage_matrix_hints": list(self.scope_coverage_matrix_hints or []),
            "composer_model": self.composer_model,
            "composer_status": self.composer_status,
            "composer_diagnostic": dict(self.composer_diagnostic or {}),
            "composer_rejection_reasons": list(self.composer_rejection_reasons or []),
            "composer_reason_category": self.composer_reason_category,
            "composer_coverage_matrix_hints": list(self.composer_coverage_matrix_hints or []),
            "gate_diagnostic": dict(self.gate_diagnostic or {}),
            "gate_rejection_reasons": list(self.gate_rejection_reasons or []),
            "gate_reason_category": self.gate_reason_category,
            "gate_coverage_matrix_hints": list(self.gate_coverage_matrix_hints or []),
            "gate_failure_stage": self.gate_failure_stage,
            "safety_boundary": dict(self.safety_boundary or {}),
            "coverage_matrix": dict(self.coverage_matrix or {}),
            "coverage_groups": list(self.coverage_groups or []),
            "coverage_primary_group": self.coverage_primary_group,
            "coverage_next_steps": list(self.coverage_next_steps or []),
            "coverage_unclassified_reasons": list(self.coverage_unclassified_reasons or []),
            "coverage_unmapped_reasons": list(self.coverage_unmapped_reasons or []),
            "feature_flag_state": dict(self.feature_flag_state or {}),
            "release_enabled": bool(self.release_enabled),
            "release_cohort": self.release_cohort,
            "release_reason_code": self.release_reason_code,
            "release_decision": dict(self.release_decision or {}),
            "default_composer_resolution": dict(self.default_composer_resolution or {}),
            "rollout_decision": dict(self.rollout_decision or {}),
            "registry_resolution": dict(self.registry_resolution or {}),
            "pre_connection": dict(self.pre_connection or {}),
            "b_plan_connection": dict(self.b_plan_connection or {}),
            "normal_connection": dict(self.normal_connection or self.b_plan_connection or {}),
            "composer_connection_attempted": bool(self.composer_connection_attempted),
            "rollout_attempted": bool(self.rollout_attempted),
            "used_evidence_span_count": int(self.used_evidence_span_count),
            "included_claim_count": int(self.included_claim_count),
            "excluded_claim_count": int(self.excluded_claim_count),
            "comment_text_allowed": bool(self.comment_text_allowed),
            "gate_results": {
                key: value.as_meta()
                for key, value in dict(self.gate_results or {}).items()
            },
        }


@dataclass(frozen=True)
class EvidenceSpan:
    """Source span kept before interpretation.

    This is a grounding object, not a sentence fragment for direct display.
    """

    span_id: str
    raw_text: str
    start_index: int = 0
    end_index: int = 0
    detected_type: str = "event"
    confidence: float = 1.0
    source_field: str = "memo"


@dataclass(frozen=True)
class ObservationClaim:
    claim_id: str
    claim_type: str
    subject: str
    object: Optional[str] = None
    evidence_span_ids: List[str] = field(default_factory=list)
    confidence: float = 0.0
    risk_level: ObservationRiskLevel = "low"


@dataclass(frozen=True)
class RelationEdge:
    edge_id: str
    from_claim_id: str
    to_claim_id: str
    relation_type: str
    evidence_span_ids: List[str] = field(default_factory=list)
    confidence: float = 0.0


@dataclass(frozen=True)
class PerspectiveReport:
    observer_id: str
    viewpoint: str
    claims: List[ObservationClaim] = field(default_factory=list)
    relations: List[RelationEdge] = field(default_factory=list)
    evidence_span_ids: List[str] = field(default_factory=list)
    confidence: float = 0.0
    uncertainty: List[str] = field(default_factory=list)
    do_not_say: List[str] = field(default_factory=list)


@dataclass(frozen=True)
class PerspectiveBoard:
    reports: List[PerspectiveReport] = field(default_factory=list)
    evidence_spans: List[EvidenceSpan] = field(default_factory=list)
    report_ids: List[str] = field(default_factory=list)
    claim_ids: List[str] = field(default_factory=list)
    relation_ids: List[str] = field(default_factory=list)
    evidence_span_ids: List[str] = field(default_factory=list)
    claim_index: Dict[str, ObservationClaim] = field(default_factory=dict)
    relation_index: Dict[str, RelationEdge] = field(default_factory=dict)
    evidence_span_index: Dict[str, EvidenceSpan] = field(default_factory=dict)
    uncertainty: List[str] = field(default_factory=list)
    do_not_say: List[str] = field(default_factory=list)
    claims_by_id: Dict[str, ObservationClaim] = field(default_factory=dict)
    relations_by_id: Dict[str, RelationEdge] = field(default_factory=dict)
    validation_issues: List[str] = field(default_factory=list)

    @property
    def report_count(self) -> int:
        return len(self.reports)

    @property
    def claim_count(self) -> int:
        return len(self.claim_ids)

    @property
    def relation_count(self) -> int:
        return len(self.relation_ids)


@dataclass(frozen=True)
class GraphClaim:
    claim_id: str
    claim_type: str
    text: str
    evidence_span_ids: List[str] = field(default_factory=list)
    confidence: float = 0.0


@dataclass(frozen=True)
class AddresseeNotes:
    display_name_call: str = ""
    sentence_target: int = 5
    voice_distance: str = "close"
    needs_gentle_pacing: bool = True
    avoid_report_like: bool = True


@dataclass(frozen=True)
class ObservationGraph:
    primary_state: GraphClaim
    core_tensions: List[RelationEdge] = field(default_factory=list)
    pressure_sources: List[GraphClaim] = field(default_factory=list)
    limit_signals: List[GraphClaim] = field(default_factory=list)
    self_awareness: List[GraphClaim] = field(default_factory=list)
    value_or_strength_signals: List[GraphClaim] = field(default_factory=list)
    addressee_notes: AddresseeNotes = field(default_factory=AddresseeNotes)
    safety_boundaries: List[str] = field(default_factory=list)
    forbidden_claims: List[str] = field(default_factory=list)
    missing_information: List[str] = field(default_factory=list)


LimitedScopeStatus = Literal["eligible", "out_of_scope", "safety_blocked"]
LimitedCoverageScope = Literal["partial_observation", "current_input_core"]


@dataclass(frozen=True)
class LimitedScopeExcludedItem:
    item_kind: str
    item_id: str
    reason_code: str
    source: str = ""

    def as_meta(self) -> Dict[str, Any]:
        return {
            "item_kind": self.item_kind,
            "item_id": self.item_id,
            "reason_code": self.reason_code,
            "source": self.source,
        }


def _limited_scope_count_reasons(values: List[str]) -> Dict[str, int]:
    counts: Dict[str, int] = {}
    for value in values or []:
        key = str(value or "").strip()
        if key:
            counts[key] = counts.get(key, 0) + 1
    return counts


def _limited_scope_claim_counts(graph: ObservationGraph) -> Dict[str, int]:
    return {
        "primary_state": 1 if str(getattr(graph.primary_state, "text", "") or "").strip() else 0,
        "pressure_sources": len(list(graph.pressure_sources or [])),
        "limit_signals": len(list(graph.limit_signals or [])),
        "self_awareness": len(list(graph.self_awareness or [])),
        "value_or_strength_signals": len(list(graph.value_or_strength_signals or [])),
        "core_tensions": len(list(graph.core_tensions or [])),
    }


def _limited_scope_coverage_matrix_hint(
    *,
    scope_status: str,
    coverage_scope: str,
    rejection_reasons: List[str],
    excluded_reason_codes: List[str],
    safety_boundaries: List[str],
) -> str:
    reasons = {str(value or "") for value in [*rejection_reasons, *excluded_reason_codes, *safety_boundaries]}
    joined = " ".join(sorted(reasons)).lower()
    if scope_status == "safety_blocked" or safety_boundaries or "safety" in joined:
        return "safety_boundary"
    if "limited_scope_required_structure_missing" in reasons or "required_structure" in joined:
        return "required_structure"
    if "limited_scope_no_grounded_primary_state" in reasons or "no_grounded_primary_state" in reasons or "primary" in joined:
        return "primary_state_grounding"
    if any(reason.endswith("claim_limit") or reason.endswith("relation_limit") for reason in reasons):
        return "complexity_limit"
    if scope_status == "out_of_scope":
        return "minimum_claim"
    if coverage_scope == "partial_observation":
        return "eligible_partial_observation"
    return "eligible_current_input_core"


@dataclass(frozen=True)
class LimitedObservationScope:
    scope_status: LimitedScopeStatus
    scoped_graph: ObservationGraph
    included_claim_ids: List[str] = field(default_factory=list)
    included_relation_ids: List[str] = field(default_factory=list)
    excluded_claims: List[LimitedScopeExcludedItem] = field(default_factory=list)
    min_reply_sentence_count: int = 2
    max_reply_sentence_count: int = 4
    coverage_scope: LimitedCoverageScope = "current_input_core"
    rejection_reasons: List[str] = field(default_factory=list)
    coverage_groups: List[str] = field(default_factory=list)
    scope_expansion: Dict[str, Any] = field(default_factory=dict)
    safety_boundary: Dict[str, Any] = field(default_factory=dict)
    safety_boundary_policy: Dict[str, Any] = field(default_factory=dict)

    def as_meta(self) -> Dict[str, Any]:
        included_claim_ids = list(self.included_claim_ids or [])
        included_relation_ids = list(self.included_relation_ids or [])
        excluded_claims = [item.as_meta() for item in self.excluded_claims]
        excluded_reason_codes = [
            str(item.get("reason_code") or "")
            for item in excluded_claims
            if str(item.get("reason_code") or "").strip()
        ]
        rejection_reasons = list(self.rejection_reasons or [])
        safety_boundary = dict(self.safety_boundary or {})
        safety_boundary_policy = dict(self.safety_boundary_policy or safety_boundary or {})
        if safety_boundary_policy and not safety_boundary_policy.get("version"):
            safety_boundary_policy["version"] = "emlis.scope_safety_boundary.v1"
        if safety_boundary and not safety_boundary.get("version"):
            safety_boundary["version"] = "emlis.scope_safety_boundary.v1"

        safety_boundaries = [
            *list(getattr(self.scoped_graph, "safety_boundaries", []) or []),
            *list(safety_boundary.get("safety_boundaries") or []),
            *list(safety_boundary_policy.get("safety_boundaries") or []),
        ]
        safety_boundaries = list(dict.fromkeys(str(item or "").strip() for item in safety_boundaries if str(item or "").strip()))

        missing_information = list(getattr(self.scoped_graph, "missing_information", []) or [])
        scoped_claim_counts = _limited_scope_claim_counts(self.scoped_graph)
        coverage_groups = [str(item or "").strip() for item in list(self.coverage_groups or []) if str(item or "").strip()]
        scope_expansion = dict(self.scope_expansion or {})
        safety_policy_groups = [
            str(item or "").strip()
            for item in list(safety_boundary.get("coverage_groups") or safety_boundary_policy.get("coverage_groups") or [])
            if str(item or "").strip()
        ]
        coverage_groups = list(dict.fromkeys([*coverage_groups, *safety_policy_groups]))
        if coverage_groups and not scope_expansion.get("coverage_groups"):
            scope_expansion["coverage_groups"] = list(coverage_groups)
        if scope_expansion and not scope_expansion.get("version"):
            scope_expansion["version"] = "emlis.scope_expansion.v1"

        safety_blocked_before_composer = bool(
            self.scope_status == "safety_blocked"
            or safety_boundary.get("requires_block")
            or safety_boundary.get("blocked_before_composer")
            or safety_boundary_policy.get("requires_block")
            or safety_boundary_policy.get("blocked_before_composer")
            or safety_boundaries
        )
        safety_pre_generation_block = (
            safety_boundary.get("safety_pre_generation_block")
            if isinstance(safety_boundary.get("safety_pre_generation_block"), dict)
            else safety_boundary_policy.get("safety_pre_generation_block")
            if isinstance(safety_boundary_policy.get("safety_pre_generation_block"), dict)
            else {}
        )
        safety_pre_generation_block = dict(safety_pre_generation_block or {})
        safety_pre_generation_block.setdefault("version", "emlis.safety_pre_generation_block.v1")
        safety_pre_generation_block.setdefault("target_step", "Step10_safety_boundary")
        safety_pre_generation_block.setdefault("phase", "B-S1")
        safety_pre_generation_block.setdefault("policy", "scope_pre_composer_block")
        safety_pre_generation_block.setdefault("scope_status", self.scope_status)
        safety_pre_generation_block.setdefault("blocked_before_composer", safety_blocked_before_composer)
        safety_pre_generation_block.setdefault("composer_generation_allowed", not safety_blocked_before_composer)
        safety_pre_generation_block.setdefault("fixed_reply_allowed", False)
        safety_pre_generation_block.setdefault("fallback_observation_allowed", False)
        safety_pre_generation_block.setdefault("comment_text_allowed", False if safety_blocked_before_composer else True)
        safety_pre_generation_block.setdefault("normal_observation_allowed", not safety_blocked_before_composer)
        safety_pre_generation_block.setdefault("user_facing_text_allowed", not safety_blocked_before_composer)
        safety_pre_generation_block.setdefault("safety_boundaries", list(safety_boundaries))
        safety_pre_generation_block.setdefault("reason_codes", list(safety_boundary.get("reason_codes") or safety_boundary_policy.get("reason_codes") or rejection_reasons or []))
        safety_pre_generation_block.setdefault("evidence_span_ids", list(safety_boundary.get("evidence_span_ids") or safety_boundary_policy.get("evidence_span_ids") or []))
        safety_pre_generation_block.setdefault("coverage_groups", list(coverage_groups))
        safety_pre_generation_block.setdefault("raw_user_text_included", False)

        coverage_matrix_hint = _limited_scope_coverage_matrix_hint(
            scope_status=self.scope_status,
            coverage_scope=self.coverage_scope,
            rejection_reasons=rejection_reasons,
            excluded_reason_codes=excluded_reason_codes,
            safety_boundaries=safety_boundaries,
        )
        scope_diagnostic = {
            "version": "emlis.limited_scope_diagnostic.v1",
            "scope_status": self.scope_status,
            "coverage_scope": self.coverage_scope,
            "coverage_matrix_hint": coverage_matrix_hint,
            "included_claim_count": len(included_claim_ids),
            "included_relation_count": len(included_relation_ids),
            "excluded_claim_count": len(excluded_claims),
            "rejection_reasons": rejection_reasons,
            "safety_boundaries": safety_boundaries,
            "missing_information": missing_information,
            "excluded_reason_codes": excluded_reason_codes,
            "scoped_claim_counts": scoped_claim_counts,
            "excluded_reason_counts": _limited_scope_count_reasons(excluded_reason_codes),
            "coverage_groups": list(coverage_groups),
            "scope_expansion": dict(scope_expansion),
            "safety_boundary": dict(safety_boundary),
            "safety_boundary_policy": dict(safety_boundary_policy),
            "safety_pre_generation_block": dict(safety_pre_generation_block),
            "safety_blocked_before_composer": safety_blocked_before_composer,
            "safety_evidence_span_ids": list(safety_boundary.get("evidence_span_ids") or safety_boundary_policy.get("evidence_span_ids") or []),
            "minimum_coverage": {
                "has_primary_state": bool(scoped_claim_counts.get("primary_state", 0)),
                "included_claim_count": len(included_claim_ids),
                "included_relation_count": len(included_relation_ids),
                "meets_minimum_claim": bool(len(included_claim_ids) >= 1 and scoped_claim_counts.get("primary_state", 0) >= 1),
            },
        }
        return {
            "version": "emlis.limited_observation_scope.v2",
            "scope_status": self.scope_status,
            "included_claim_ids": included_claim_ids,
            "included_relation_ids": included_relation_ids,
            "included_claim_count": len(included_claim_ids),
            "included_relation_count": len(included_relation_ids),
            "excluded_claims": excluded_claims,
            "excluded_claim_count": len(excluded_claims),
            "excluded_reason_codes": excluded_reason_codes,
            "min_reply_sentence_count": int(self.min_reply_sentence_count),
            "max_reply_sentence_count": int(self.max_reply_sentence_count),
            "coverage_scope": self.coverage_scope,
            "rejection_reasons": rejection_reasons,
            "rejection_reason_count": len(rejection_reasons),
            "safety_boundaries": safety_boundaries,
            "safety_boundary_count": len(safety_boundaries),
            "missing_information": missing_information,
            "missing_information_count": len(missing_information),
            "scoped_claim_counts": scoped_claim_counts,
            "coverage_groups": list(coverage_groups),
            "scope_expansion": dict(scope_expansion),
            "safety_boundary": dict(safety_boundary),
            "safety_boundary_policy": dict(safety_boundary_policy),
            "safety_pre_generation_block": dict(safety_pre_generation_block),
            "safety_blocked_before_composer": safety_blocked_before_composer,
            "safety_evidence_span_ids": list(safety_boundary.get("evidence_span_ids") or safety_boundary_policy.get("evidence_span_ids") or []),
            "scope_diagnostic": scope_diagnostic,
        }


ComposerCandidateStatus = Literal["generated", "unavailable", "schema_invalid", "empty", "blocked"]


@dataclass(frozen=True)
class ConversationComposerCandidate:
    """Conversation Composer output candidate.

    This object records whether final text came from the Composer AI boundary.
    It is not a fallback renderer and does not make display decisions by itself.
    """

    comment_text: str = ""
    composer_source: str = ""
    status: ComposerCandidateStatus = "unavailable"
    ai_generated: bool = False
    trace_id: str = ""
    attempt_count: int = 0
    used_evidence_span_ids: List[str] = field(default_factory=list)
    confidence: float = 0.0
    rejection_reasons: List[str] = field(default_factory=list)
    request_schema_version: str = "emlis.composer.request.v1"
    response_schema_version: str = ""
    fixed_string_renderer_used: bool = False
    composer_model: str = ""
    generation_method: str = ""
    coverage_scope: str = ""
    generation_scope: str = ""
    composer_meta: Dict[str, Any] = field(default_factory=dict)
    used_claim_ids: List[str] = field(default_factory=list)
    used_relation_ids: List[str] = field(default_factory=list)


@dataclass(frozen=True)
class ListenerReaderReport:
    understandable: bool
    addressee_clear: bool
    speaker_integrity_ok: bool
    conversational: bool
    report_like: bool
    summary_of_output: str = ""
    unclear_sentences: List[str] = field(default_factory=list)
    rejection_reasons: List[str] = field(default_factory=list)
    confidence: float = 0.0


@dataclass(frozen=True)
class GroundingSentenceClaim:
    sentence_index: int
    sentence: str
    evidence_span_ids: List[str] = field(default_factory=list)
    relation_supported: bool = False
    unsupported_reason: str = ""
    # Step 6: binding-aware Grounding diagnostics. These fields describe
    # generated sentence bindings only; they do not include raw user input and
    # do not change the passed-only display contract.
    binding_used: bool = False
    binding_sentence_id: str = ""
    binding_evidence_span_ids: List[str] = field(default_factory=list)
    binding_phrase_unit_ids: List[str] = field(default_factory=list)
    binding_relation_type: str = ""
    declared_evidence_span_ids: List[str] = field(default_factory=list)
    declared_phrase_unit_ids: List[str] = field(default_factory=list)
    declared_relation_type: str = ""
    grounding_support_source: str = ""
    binding_support_reason: str = ""
    used_phrase_unit_ids: List[str] = field(default_factory=list)
    relation_type: str = ""


@dataclass(frozen=True)
class GroundingReport:
    passed: bool
    sentence_claims: List[GroundingSentenceClaim] = field(default_factory=list)
    rejection_reasons: List[str] = field(default_factory=list)
    coverage_ratio: float = 0.0
    confidence: float = 0.0
    grounding_scope: str = "full_graph"
    allowed_evidence_span_ids: List[str] = field(default_factory=list)
    ignored_evidence_span_ids: List[str] = field(default_factory=list)
    # Step 6: meta-only binding-aware Grounding trace. Display remains
    # fail-closed; this only records whether declared sentence binding was read.
    binding_used: bool = False
    binding_present: bool = False
    binding_missing: bool = False
    binding_count: int = 0
    expected_binding_count: int = 0
    binding_version: str = ""
    relation_types: List[str] = field(default_factory=list)
    binding_supported_sentence_count: int = 0
    binding_diagnostics: Dict[str, Any] = field(default_factory=dict)
    binding_aware_grounding: Dict[str, Any] = field(default_factory=dict)
    binding_rejection_reasons: List[str] = field(default_factory=list)
    declared_relation_types: List[str] = field(default_factory=list)
    declared_phrase_unit_ids: List[str] = field(default_factory=list)


@dataclass(frozen=True)
class TemplateEchoReport:
    passed: bool
    max_old_template_similarity: float = 0.0
    max_previous_output_similarity: float = 0.0
    raw_echo_ratio: float = 0.0
    repeated_sentence_pattern_score: float = 0.0
    # Phase 5: Limited Composer guard metrics. These are diagnostic meta only;
    # the public response contract remains observation_status/comment_text.
    max_sentence_echo_ratio: float = 0.0
    raw_quote_span_count: int = 0
    raw_copy_sentence_ratio: float = 0.0
    limited_surface_repetition_score: float = 0.0
    abstract_repetition_score: float = 0.0
    abstract_phrase_repetition_score: float = 0.0
    # Compatibility aliases retained for trace readers that use Phase 5 names.
    raw_quote_char_ratio: float = 0.0
    matched_raw_quote_fragments: List[str] = field(default_factory=list)
    repeated_limited_surface_score: float = 0.0
    matched_limited_surface_patterns: List[str] = field(default_factory=list)
    # Phase 8: Japanese / semantic coherence diagnostics for Limited Composer.
    phase8_emotion_label_body_line_count: int = 0
    phase8_missing_must_keep_roles: List[str] = field(default_factory=list)
    phase8_quality_rejection_reasons: List[str] = field(default_factory=list)
    matched_banned_patterns: List[str] = field(default_factory=list)
    rejection_reasons: List[str] = field(default_factory=list)


@dataclass(frozen=True)
class SafetyBoundaryReport:
    requires_block: bool = False
    reasons: List[str] = field(default_factory=list)
    boundary_count: int = 0
    boundary_kinds: List[str] = field(default_factory=list)
    source_span_ids: List[str] = field(default_factory=list)
    source_fields: List[str] = field(default_factory=list)
    policy_version: str = "emlis.safety_boundary_policy.v1"
    blocks_before_composer: bool = False
    normal_observation_allowed: bool = True
    user_facing_text_allowed: bool = True

    def as_meta(self) -> Dict[str, Any]:
        requires_block = bool(self.requires_block)
        return {
            "version": "emlis.safety_boundary_report.v1",
            "policy_version": str(self.policy_version or ""),
            "requires_block": requires_block,
            "blocks_before_composer": bool(self.blocks_before_composer or requires_block),
            "normal_observation_allowed": bool(self.normal_observation_allowed and not requires_block),
            "user_facing_text_allowed": bool(self.user_facing_text_allowed and not requires_block),
            "reasons": list(self.reasons or []),
            "boundary_count": int(self.boundary_count or 0),
            "boundary_kinds": list(self.boundary_kinds or []),
            "source_span_ids": list(self.source_span_ids or []),
            "source_fields": list(self.source_fields or []),
            "raw_user_text_included": False,
        }


@dataclass(frozen=True)
class DisplayDecision:
    observation_status: ObservationStatus
    comment_text: str = ""
    rejection_reasons: List[str] = field(default_factory=list)
    trace_id: str = ""
    gate_trace: Dict[str, Any] = field(default_factory=dict)
