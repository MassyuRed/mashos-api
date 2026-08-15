# -*- coding: utf-8 -*-
from __future__ import annotations

"""Private contracts for the first runnable CMEE Emlis vertical.

Only :meth:`EngineOutcome.as_body_free` is public-report safe. Source bytes,
locators, graph values and generated text intentionally have no serializer.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Mapping, Optional, Tuple


CMEE_SCHEMA_VERSION = "cocolon.cmee.v1a.i1sx.text_grounded_limited.v1"
CMEE_ROUTE_B_POLICY_VERSION = "cocolon.cmee.v1a.acceptance.route_b.v1"
CMEE_SOURCE_CONTRACT_VERSION = "cocolon.cmee.emlis.current_input.text_grounded.v1"
CMEE_OBLIGATION_VERSION = "cocolon.cmee.emlis.i1sx.owner_obligation.v1"
CMEE_OWNER_UNIVERSE_SCHEMA_VERSION = "cocolon.cmee.v1a.owner_universe.v1"
CMEE_TERMINAL_GENERATED_DISABLED = (
    "CMEE_V1A_I1SX_TEXT_GROUNDED_VERTICAL_WIP_DISABLED"
)


class CoreId(str, Enum):
    EMLIS_AI = "emlis_ai"


class ProductJob(str, Enum):
    OBSERVE_AND_CLARIFY = "OBSERVE_AND_CLARIFY"


class ExecutionMode(str, Enum):
    OFFLINE_CANDIDATE = "OFFLINE_CANDIDATE"


class EngineStatus(str, Enum):
    GENERATED = "GENERATED"
    LIMITED = "LIMITED"
    QUESTION_PENDING = "QUESTION_PENDING"
    UNAVAILABLE = "UNAVAILABLE"
    SEPARATE_SAFETY = "SEPARATE_SAFETY"
    REJECTED = "REJECTED"


class EpistemicState(str, Enum):
    SOURCE_EXPLICIT = "SOURCE_EXPLICIT"
    UNKNOWN = "UNKNOWN"


class RouteBDisposition(str, Enum):
    """Exact Route B owner disposition set from the CMEE V1 contract."""

    SOURCE_EXPLICIT_VISIBLE = "SOURCE_EXPLICIT_VISIBLE"
    SUPPLEMENTAL_USER_VISIBLE = "SUPPLEMENTAL_USER_VISIBLE"
    UNKNOWN_PRESERVED_LIMITED = "UNKNOWN_PRESERVED_LIMITED"
    CLARIFICATION_TARGET = "CLARIFICATION_TARGET"
    NOT_VISIBLE_UNRESOLVED = "NOT_VISIBLE_UNRESOLVED"
    SEPARATE_SAFETY = "SEPARATE_SAFETY"


class OwnerClass(str, Enum):
    REQUIRED = "REQUIRED"
    ACTIVE_OPTIONAL = "ACTIVE_OPTIONAL"


class ProviderResolution(str, Enum):
    UNIQUE = "UNIQUE"
    AMBIGUOUS = "AMBIGUOUS"
    UNRESOLVED = "UNRESOLVED"
    MISSING_OR_INVALID = "MISSING_OR_INVALID"


class AttachmentAdmission(str, Enum):
    PROVISIONAL_ONLY = "PROVISIONAL_ONLY"
    UNRESOLVED = "UNRESOLVED"
    UNAVAILABLE = "UNAVAILABLE"


class VisibleAuthority(str, Enum):
    SOURCE_EXPLICIT = "SOURCE_EXPLICIT"
    SUPPLEMENTAL_USER = "SUPPLEMENTAL_USER"
    NONE = "NONE"


@dataclass(frozen=True, slots=True, repr=False)
class GenerationRequest:
    request_id: str
    current_input_bundle: object
    expected_source_record_id: str
    core_id: str = CoreId.EMLIS_AI.value
    product_job: str = ProductJob.OBSERVE_AND_CLARIFY.value
    execution_mode: str = ExecutionMode.OFFLINE_CANDIDATE.value


@dataclass(frozen=True, slots=True, repr=False)
class SourceEnvelope:
    envelope_id: str
    source_record_id: str
    source_role: str
    source_schema_version: str
    source_contract_version: str
    source_encoding: str
    label_contract_id: str
    label_contract_digest: str
    raw_utf8: bytes = field(repr=False, compare=True)
    raw_sha256: str = field(repr=False, compare=True)


@dataclass(frozen=True, slots=True, repr=False)
class EvidenceRef:
    evidence_id: str
    source_span_id: str
    source_envelope_id: str
    field_path: str
    element_index: int
    field_utf8_start: int
    field_utf8_end: int
    utf8_start: int
    utf8_end: int
    field_sha256: str = field(repr=False)
    literal_sha256: str = field(repr=False)


@dataclass(frozen=True, slots=True)
class SourceOwnerObligation:
    meaning_owner_id: str
    owner_class: OwnerClass
    obligation_kind: str
    source_span_ids: Tuple[str, ...]
    evidence_refs: Tuple[str, ...]


@dataclass(frozen=True, slots=True)
class SourceOwnerUniverse:
    schema_version: str
    source_envelope_id: str
    source_version: str
    obligation_version: str
    required_owner_refs: Tuple[str, ...]
    active_optional_owner_refs: Tuple[str, ...]
    credit_only_owner_refs: Tuple[str, ...]
    obligations: Tuple[SourceOwnerObligation, ...]
    owner_universe_digest: str


@dataclass(frozen=True, slots=True)
class RouteBOwnerDisposition:
    """Complete exact-one Route B disposition for one meaning owner."""

    meaning_owner_id: str
    owner_class: OwnerClass
    provider_resolution: ProviderResolution
    attachment_admission: AttachmentAdmission
    visible_authority: VisibleAuthority
    route_b_disposition: RouteBDisposition
    visible_claim_refs: Tuple[str, ...]
    evidence_refs: Tuple[str, ...]
    target_unknown_ref: Optional[str]
    reason_codes: Tuple[str, ...]

    # Compatibility aliases are intentionally read-only. The disabled exact8
    # runner remains byte-identical while the private R1 contract uses the
    # approved Route B field names above.
    @property
    def owner_id(self) -> str:
        return self.meaning_owner_id

    @property
    def disposition(self) -> RouteBDisposition:
        return self.route_b_disposition

    @property
    def evidence_ids(self) -> Tuple[str, ...]:
        return self.evidence_refs


# Read-only compatibility name for the byte-identical disabled exact8 runner
# and the already-open PR's first vertical implementation.
OwnerDisposition = RouteBOwnerDisposition


@dataclass(frozen=True, slots=True, repr=False)
class MeaningNode:
    node_id: str
    owner_id: str
    node_kind: str
    grounding_kind: str
    value: str = field(repr=False)
    epistemic_state: EpistemicState = EpistemicState.UNKNOWN
    evidence_ids: Tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class MeaningEdge:
    edge_id: str
    owner_id: str
    relation: str
    source_node_id: str
    target_node_id: str
    grounding_kind: str
    epistemic_state: EpistemicState
    evidence_ids: Tuple[str, ...]


@dataclass(frozen=True, slots=True, repr=False)
class GroundedMeaningGraph:
    graph_id: str
    source_envelope_id: str
    nodes: Tuple[MeaningNode, ...]
    edges: Tuple[MeaningEdge, ...]
    owner_dispositions: Tuple[OwnerDisposition, ...]
    required_owner_refs: Tuple[str, ...]
    active_optional_owner_refs: Tuple[str, ...]
    source_version: str
    obligation_version: str
    owner_universe_digest: str


@dataclass(frozen=True, slots=True)
class ExperiencePlan:
    plan_id: str
    source_envelope_id: str
    source_version: str
    obligation_version: str
    owner_universe_digest: str
    source_plan_version: str
    observation_duty_id: str
    unknown_duty_id: str
    reception_duty_id: str
    reception_plan_digest: str
    allowed_reception_act_ids: Tuple[str, ...]
    required_observation_owner_ids: Tuple[str, ...]
    reception_target_owner_ids: Tuple[str, ...]
    visible_owner_ids: Tuple[str, ...]
    unresolved_owner_ids: Tuple[str, ...]
    visible_unknown_owner_ids: Tuple[str, ...]
    required_unknown_owner_ids: Tuple[str, ...]
    visible_line_ids: Tuple[str, ...]


@dataclass(frozen=True, slots=True, repr=False)
class VisibleUnitTrace:
    visible_unit_id: str
    source_sentence_id: str
    source_envelope_id: str
    source_version: str
    obligation_version: str
    owner_universe_digest: str
    role: str
    operation: str
    text_sha256: str = field(repr=False)
    duty_id: str
    meaning_node_ids: Tuple[str, ...]
    meaning_edge_ids: Tuple[str, ...]
    evidence_ids: Tuple[str, ...]
    constrained_by_owner_ids: Tuple[str, ...] = ()


@dataclass(frozen=True, slots=True, repr=False)
class VisibleUnknownUnit:
    unknown_unit_id: str
    source_sentence_id: str
    source_envelope_id: str
    source_version: str
    obligation_version: str
    owner_universe_digest: str
    duty_id: str
    text: str = field(repr=False)
    owner_ids: Tuple[str, ...] = ()
    evidence_ids: Tuple[str, ...] = ()


@dataclass(frozen=True, slots=True, repr=False)
class GenerationArtifactBundle:
    artifact_id: str
    realizer_contract_ids: Tuple[str, ...]
    trust_policy_ids: Tuple[str, ...]
    observation: str = field(repr=False)
    reception: str = field(repr=False)
    plan: ExperiencePlan
    trace: Tuple[VisibleUnitTrace, ...]
    visible_unknowns: Tuple[VisibleUnknownUnit, ...]

    @property
    def text(self) -> str:
        unknown = "\n".join(row.text for row in self.visible_unknowns)
        return (
            f"見えたこと：\n{self.observation}"
            f"\n\nまだ分からないこと：\n{unknown}"
            f"\n\nEmlisから：\n{self.reception}"
        )


@dataclass(frozen=True, slots=True, repr=False)
class EngineOutcome:
    status: EngineStatus
    reason_codes: Tuple[str, ...]
    source_envelope: Optional[SourceEnvelope] = field(default=None, repr=False)
    meaning_graph: Optional[GroundedMeaningGraph] = field(default=None, repr=False)
    artifact: Optional[GenerationArtifactBundle] = field(default=None, repr=False)
    terminal_state: str = ""
    automatic_progression: bool = False
    schema_version: str = CMEE_SCHEMA_VERSION
    route_policy_version: str = CMEE_ROUTE_B_POLICY_VERSION

    def as_body_free(self) -> Mapping[str, Any]:
        graph = self.meaning_graph
        artifact = self.artifact
        dispositions = tuple(graph.owner_dispositions) if graph else ()
        visible = {
            RouteBDisposition.SOURCE_EXPLICIT_VISIBLE,
            RouteBDisposition.SUPPLEMENTAL_USER_VISIBLE,
        }
        return {
            "schema_version": self.schema_version,
            "route_policy_version": self.route_policy_version,
            "core_id": CoreId.EMLIS_AI.value,
            "product_job": ProductJob.OBSERVE_AND_CLARIFY.value,
            "execution_mode": ExecutionMode.OFFLINE_CANDIDATE.value,
            "status": self.status.value,
            "reason_codes": list(self.reason_codes),
            "source_envelope_count": int(self.source_envelope is not None),
            "meaning_node_count": len(graph.nodes) if graph else 0,
            "meaning_edge_count": len(graph.edges) if graph else 0,
            "required_active_owner_count": len(dispositions),
            "visible_owner_count": sum(row.route_b_disposition in visible for row in dispositions),
            "unresolved_owner_count": sum(
                row.route_b_disposition not in visible for row in dispositions
            ),
            "unresolved_required_owner_count": sum(
                row.owner_class is OwnerClass.REQUIRED
                and row.route_b_disposition not in visible
                for row in dispositions
            ),
            "visible_unit_trace_count": len(artifact.trace) if artifact else 0,
            "realizer_contract_count": len(artifact.realizer_contract_ids) if artifact else 0,
            "trust_policy_count": len(artifact.trust_policy_ids) if artifact else 0,
            "observation_unit_count": sum(row.role == "OBSERVATION" for row in artifact.trace) if artifact else 0,
            "unknown_unit_count": len(artifact.visible_unknowns) if artifact else 0,
            "unknown_trace_count": sum(row.role == "UNKNOWN" for row in artifact.trace) if artifact else 0,
            "reception_unit_count": sum(row.role == "RECEPTION" for row in artifact.trace) if artifact else 0,
            "artifact_present": artifact is not None,
            "implementation_state": "DRAFT_WIP_DISABLED",
            "route_b_contract_complete": False,
            "candidate_ready": False,
            "product_read_eligible": False,
            "exact8_acceptance_complete": False,
            "product_read_evaluated": False,
            "terminal_state": self.terminal_state,
            "p0_credit": 0,
            "l3i_credit": 0,
            "full_i1_credit": 0,
            "cycle001_credit": 0,
            "production_effect": 0,
            "automatic_progression": False,
        }


__all__ = [
    "AttachmentAdmission",
    "CMEE_OBLIGATION_VERSION",
    "CMEE_OWNER_UNIVERSE_SCHEMA_VERSION",
    "CMEE_ROUTE_B_POLICY_VERSION",
    "CMEE_SCHEMA_VERSION",
    "CMEE_SOURCE_CONTRACT_VERSION",
    "CMEE_TERMINAL_GENERATED_DISABLED",
    "CoreId",
    "EngineOutcome",
    "EngineStatus",
    "EpistemicState",
    "EvidenceRef",
    "ExecutionMode",
    "ExperiencePlan",
    "GenerationArtifactBundle",
    "GenerationRequest",
    "GroundedMeaningGraph",
    "MeaningEdge",
    "MeaningNode",
    "OwnerClass",
    "OwnerDisposition",
    "ProductJob",
    "ProviderResolution",
    "RouteBDisposition",
    "RouteBOwnerDisposition",
    "SourceEnvelope",
    "SourceOwnerObligation",
    "SourceOwnerUniverse",
    "VisibleAuthority",
    "VisibleUnknownUnit",
    "VisibleUnitTrace",
]
