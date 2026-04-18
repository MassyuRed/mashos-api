# -*- coding: utf-8 -*-
from __future__ import annotations

"""Shared types for the EmlisAI reply pipeline.

This file is intentionally dependency-light so every other EmlisAI module can
import these types without causing circular imports.
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Literal, Optional

HistoryMode = Literal["none", "extended", "full"]
ContinuityMode = Literal["off", "basic", "advanced"]
StyleMode = Literal["base", "adaptive", "personalized"]
PartnerMode = Literal["off", "on_basic", "on_advanced"]
StyleFamily = Literal[
    "accepting",
    "sensitive",
    "analytical",
    "structured",
    "action_oriented",
]


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
    debug: Dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class StyleProfile:
    family: StyleFamily
    tone_reason: str
    lexical_softness: str = "soft"
    structure_density: str = "light"


@dataclass
class ReplyPlan:
    receive: str = ""
    continuity: str = ""
    change: str = ""
    partner_line: str = ""
    used_evidence: List[EvidenceRef] = field(default_factory=list)
    notes: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ReplyEnvelope:
    comment_text: str
    meta: Dict[str, Any] = field(default_factory=dict)
    used_evidence: List[EvidenceRef] = field(default_factory=list)
    fallback_used: bool = False
