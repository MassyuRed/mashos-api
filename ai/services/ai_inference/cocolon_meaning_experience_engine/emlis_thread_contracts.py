from __future__ import annotations

"""Emlis-only, process-local Q1 contracts. No issuance or persistence effects.

The containing GenerationRequest owns the unchanged CURRENT_INPUT. Answers
have separate envelopes; control records and previous prose are never evidence.
Shared v1 and Analysis clarification contracts are deliberately independent.
"""

from dataclasses import dataclass
from typing import Any

from .contracts import EngineOutcome, EngineStatus, EvidenceRef, SourceEnvelope

THREAD_SCHEMA = "cocolon.cmee.emlis_thread.v1"
SEMANTIC_SCHEMA = "cocolon.cmee.emlis_answer_meaning.v1"
ANSWER_FIELD = "answer_text_private"


@dataclass(frozen=True, slots=True, repr=False)
class QualifiedEvidenceRef:
    """A compatibility alias never changes the original evidence identity."""

    thread_span_id: str
    local_source_span_id: str
    evidence: EvidenceRef

    @property
    def source_envelope_id(self) -> str:
        return self.evidence.source_envelope_id


@dataclass(frozen=True, slots=True, repr=False)
class SupplementalAnswerSource:
    answer_id: str
    thread_id: str
    question_id: str
    round_index: int
    original_source_ref: str
    answer_text_private: str
    recorded_at: str
    authored_at: str | None = None
    source_version: str = "cocolon.cmee.supplemental_answer.v1"
    source_role: str = "SUPPLEMENTAL_ANSWER"


@dataclass(frozen=True, slots=True)
class AnswerTemporalBindingV1:
    about_time: str
    anchor_source_ref: str
    time_expression_evidence_refs: tuple[str, ...] = ()
    relative_relation: str | None = None
    resolved_interval: tuple[str, str] | None = None
    timezone_basis: str | None = None


@dataclass(frozen=True, slots=True, repr=False)
class EmlisQuestionDecisionV1:
    disposition: str
    target_ref: str | None = None
    target_kind: str | None = None
    supporting_evidence_refs: tuple[str, ...] = ()
    missing_dimension: str | None = None
    affected_meaning_refs: tuple[str, ...] = ()
    affected_reception_refs: tuple[str, ...] = ()
    asked_target_refs: tuple[str, ...] = ()
    decision_reason: str = "meaning_sufficient"


@dataclass(frozen=True, slots=True, repr=False)
class EmlisClarificationV1:
    question_id: str
    parent_request_id: str
    thread_id: str
    original_source_ref: str
    decision: EmlisQuestionDecisionV1
    prompt_private: str
    skip_allowed: bool = True
    answer_limit: int = 1
    answer_source_role: str = "SUPPLEMENTAL_ANSWER"
    schema_version: str = "cocolon.cmee.emlis_clarification.v1"


@dataclass(frozen=True, slots=True, repr=False)
class EmlisQuestionControlV1:
    pending_question: EmlisClarificationV1 | None = None
    asked_target_refs: tuple[str, ...] = ()
    issued_count: int = 0
    stop: bool = False
    issued_questions: tuple[EmlisClarificationV1, ...] = ()
    question_limit: int = 1


@dataclass(frozen=True, slots=True, repr=False)
class EmlisThreadInputV1:
    thread_id: str
    original_source_ref: str
    answers: tuple[SupplementalAnswerSource, ...] = ()
    admitted_history: tuple[Any, ...] = ()
    current_round: int = 0
    capability_snapshot: str = "FREE_Q1"
    question_control_context: EmlisQuestionControlV1 = EmlisQuestionControlV1()
    prepared_meaning_checkpoint_ref: str | None = None
    schema_version: str = THREAD_SCHEMA
    rejected_frame_keys: tuple[str, ...] = ()
    frame_feedback_sources: tuple[Any, ...] = ()


@dataclass(frozen=True, slots=True, repr=False)
class EmlisAnswerUpdateItemV1:
    update_ref: str
    binding_kind: str
    target_meaning_refs: tuple[str, ...]
    evidence_refs: tuple[str, ...]
    temporal_binding: AnswerTemporalBindingV1
    operation: str
    changed_claim_refs: tuple[str, ...]
    superseded_claim_refs: tuple[str, ...]
    affected_dependency_refs: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class EmlisUnresolvedPartV1:
    evidence_refs: tuple[str, ...]
    reason_code: str


@dataclass(frozen=True, slots=True, repr=False)
class AnswerMeaningUpdateV1:
    answer_source_ref: str
    question_ref: str
    prior_meaning_ref: str
    updates: tuple[EmlisAnswerUpdateItemV1, ...]
    unresolved_parts: tuple[EmlisUnresolvedPartV1, ...]
    disposition: str
    new_meaning_ref: str


@dataclass(frozen=True, slots=True, repr=False)
class EmlisMeaningCheckpointV1:
    checkpoint_id: str
    source_prefix_ref: str
    base_meaning_ref: str
    answer_update: AnswerMeaningUpdateV1 | None
    assessment_status: str
    accepted_update_refs: tuple[str, ...]
    inactive_claim_refs: tuple[str, ...]
    unresolved_parts: tuple[EmlisUnresolvedPartV1, ...]
    semantic_schema_version: str = SEMANTIC_SCHEMA


@dataclass(frozen=True, slots=True, repr=False)
class EmlisThreadOutcomeV1:
    status: EngineStatus
    body: EngineOutcome | EmlisThreadBodyOutcomeV1 | None
    question_decision: EmlisQuestionDecisionV1
    question: EmlisClarificationV1 | None = None
    meaning_checkpoint: EmlisMeaningCheckpointV1 | None = None
    body_sufficiency: str | None = None
    body_state: str = "UNAVAILABLE"
    reason_codes: tuple[str, ...] = ()
    schema_version: str = THREAD_SCHEMA
    automatic_progression: bool = False

    @property
    def artifact(self):
        return self.body.artifact if self.body else None

    @property
    def meaning_graph(self):
        return self.body.meaning_graph if self.body else None


@dataclass(frozen=True, slots=True, repr=False)
class EmlisThreadBodyArtifactV1:
    artifact_id: str
    observation: str
    reception: str
    source_prefix_ref: str
    meaning_checkpoint_ref: str
    qualified_evidence_refs: tuple[QualifiedEvidenceRef, ...]
    meaning_trace: tuple[Any, ...]
    reception_trace: tuple[Any, ...]
    body_status: EngineStatus
    schema_version: str = "cocolon.cmee.emlis_thread_artifact.v1"
    history_line: str | None = None
    history_line_plan: Any = None
    interpretive_frames: tuple[Any, ...] = ()

    @property
    def text(self) -> str:
        return f"見えたこと：\n{self.observation}\n\nEmlisから：\n{self.reception}" + (f"\n\nこれまでの記録から：\n{self.history_line}" if self.history_line else "")


@dataclass(frozen=True, slots=True, repr=False)
class EmlisThreadBodyOutcomeV1:
    status: EngineStatus
    artifact: EmlisThreadBodyArtifactV1
    meaning_graph: Any
    reason_codes: tuple[str, ...] = ()
