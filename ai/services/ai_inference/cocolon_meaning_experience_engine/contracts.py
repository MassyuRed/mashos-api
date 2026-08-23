# -*- coding: utf-8 -*-
from __future__ import annotations

"""Private contracts for the first runnable CMEE Emlis vertical.

Only :meth:`EngineOutcome.as_body_free` is public-report safe. Source bytes,
locators, graph values and generated text intentionally have no serializer.
"""

import hashlib
import hmac
import json
import re
from dataclasses import dataclass, field, fields as dataclass_fields, is_dataclass
from enum import Enum
from typing import Any, Mapping, Optional, Sequence, Tuple


CMEE_SCHEMA_VERSION = "cocolon.cmee.v1a.i1sx.material_unknown.v2"
CMEE_ROUTE_B_POLICY_VERSION = "cocolon.cmee.v1a.acceptance.route_b.v1"
CMEE_SOURCE_CONTRACT_VERSION = "cocolon.cmee.emlis.current_input.text_grounded.v2"
CMEE_OBLIGATION_VERSION = "cocolon.cmee.emlis.i1sx.owner_obligation.v1"
CMEE_OWNER_UNIVERSE_SCHEMA_VERSION = "cocolon.cmee.v1a.owner_universe.v1"
CMEE_COMMON_GUARD_PROOF_VERSION = "cocolon.cmee.v1a.common_guard_proof.v1"
CMEE_STAGE1_RESPONSE_SCHEMA_VERSION = "cocolon.cmee.v1a.emlis_stage1_response.v1"
CMEE_STAGE1_TRACE_EXTENSION_SCHEMA_VERSION = (
    "cocolon.cmee.v1a.emlis_stage1_positive_trace_extension.v1"
)
CMEE_STAGE1_IDENTITY_ALGORITHM = (
    "cocolon.cmee.identity.typed_canonical_json_sha256.v1"
)
CMEE_STAGE1_EMLIS_OWNER_REF = (
    "owner:emlis@cocolon.cmee.v1a.emlis_stage1_response.v1"
)
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


class InterpretationEpistemicState(str, Enum):
    PROVISIONAL_INTERPRETATION = "PROVISIONAL_INTERPRETATION"


class InterpretationKind(str, Enum):
    DIRECT_STATE = "DIRECT_STATE"
    DIRECT_DIRECTION = "DIRECT_DIRECTION"
    COEXISTENCE = "COEXISTENCE"
    TENSION = "TENSION"
    DIRECTION_UNDER_BURDEN = "DIRECTION_UNDER_BURDEN"
    ACTION_THEN_CHANGE_ONCE = "ACTION_THEN_CHANGE_ONCE"
    RESIDUE_AFTER_EVENT = "RESIDUE_AFTER_EVENT"
    SOURCE_STATED_CAUSE = "SOURCE_STATED_CAUSE"
    UNFINISHED = "UNFINISHED"


class RelationOperator(str, Enum):
    NO_RELATION_CLAIM = "NO_RELATION_CLAIM"
    COEXISTS_WITH = "COEXISTS_WITH"
    TENSION_WITH = "TENSION_WITH"
    TEMPORALLY_PRECEDES = "TEMPORALLY_PRECEDES"
    ACTION_PRECEDES_CHANGE = "ACTION_PRECEDES_CHANGE"
    SOURCE_EXPLICIT_CAUSE = "SOURCE_EXPLICIT_CAUSE"


class ArgumentRole(str, Enum):
    PRIMARY = "PRIMARY"
    EXPERIENCER = "EXPERIENCER"
    LEFT = "LEFT"
    RIGHT = "RIGHT"
    BEFORE = "BEFORE"
    AFTER = "AFTER"
    ACTION = "ACTION"
    CHANGE = "CHANGE"
    CAUSE = "CAUSE"
    EFFECT = "EFFECT"


class SemanticOperator(str, Enum):
    PRESENT_STATE = "PRESENT_STATE"
    PRESENT_DIRECTION = "PRESENT_DIRECTION"
    PRESENT_BURDEN = "PRESENT_BURDEN"
    PRESENT_CHANGE = "PRESENT_CHANGE"
    PRESENT_ACTUAL_OUTPUT = "PRESENT_ACTUAL_OUTPUT"
    PRESENT_RESIDUE = "PRESENT_RESIDUE"
    PRESENT_UNFINISHED = "PRESENT_UNFINISHED"
    SYNTHESIZE_RELATION = "SYNTHESIZE_RELATION"


class MeaningFieldSlot(str, Enum):
    CENTER = "CENTER"
    COEXISTENCE = "COEXISTENCE"
    TENSION = "TENSION"
    DIRECTION = "DIRECTION"
    BURDEN = "BURDEN"
    CHANGE = "CHANGE"
    OUTPUT = "OUTPUT"
    TIME_RELATION = "TIME_RELATION"
    RESIDUE = "RESIDUE"
    UNFINISHED = "UNFINISHED"
    UNKNOWN = "UNKNOWN"


class TemperatureClass(str, Enum):
    STANDARD = "STANDARD"
    ELEVATED_NON_SAFETY = "ELEVATED_NON_SAFETY"


class ObservationDepthClass(str, Enum):
    FOCUSED = "FOCUSED"
    LAYERED = "LAYERED"
    DENSE = "DENSE"


class SubjectiveDepthClass(str, Enum):
    FOCUSED = "FOCUSED"
    LAYERED = "LAYERED"
    DENSE = "DENSE"


class ObservationContributionKind(str, Enum):
    OBSERVE_CENTER = "OBSERVE_CENTER"
    OBSERVE_COEXISTENCE = "OBSERVE_COEXISTENCE"
    OBSERVE_TENSION = "OBSERVE_TENSION"
    OBSERVE_DIRECTION = "OBSERVE_DIRECTION"
    OBSERVE_BURDEN = "OBSERVE_BURDEN"
    OBSERVE_CHANGE = "OBSERVE_CHANGE"
    OBSERVE_ACTION_THEN_CHANGE = "OBSERVE_ACTION_THEN_CHANGE"
    OBSERVE_ACTUAL_OUTPUT = "OBSERVE_ACTUAL_OUTPUT"
    OBSERVE_TIME_RELATION = "OBSERVE_TIME_RELATION"
    PRESERVE_RESIDUE = "PRESERVE_RESIDUE"
    PRESERVE_UNFINISHED = "PRESERVE_UNFINISHED"


class SubjectiveMode(str, Enum):
    ATTENTION = "ATTENTION"
    AFFECTIVE_RESPONSE = "AFFECTIVE_RESPONSE"
    PERSONAL_APPRAISAL = "PERSONAL_APPRAISAL"
    VALUE_POSITION = "VALUE_POSITION"
    RELATIONAL_STANCE = "RELATIONAL_STANCE"
    BOUNDED_COUNTERPOSITION = "BOUNDED_COUNTERPOSITION"


class AffectCategory(str, Enum):
    CONCERN = "CONCERN"
    RELIEF = "RELIEF"
    JOY = "JOY"
    SADNESS = "SADNESS"
    RESPECT = "RESPECT"
    DISCOMFORT = "DISCOMFORT"


class AffectIntensity(str, Enum):
    QUIET = "QUIET"
    MODERATE = "MODERATE"


class SubjectiveOperator(str, Enum):
    ATTEND_TO = "ATTEND_TO"
    FEEL_TOWARD = "FEEL_TOWARD"
    APPRAISE_AS_MATERIAL = "APPRAISE_AS_MATERIAL"
    PROTECT_VALUE_BOUNDARY = "PROTECT_VALUE_BOUNDARY"
    TAKE_RELATIONAL_STANCE = "TAKE_RELATIONAL_STANCE"
    COUNTER_SPECIFIC_PROMOTION = "COUNTER_SPECIFIC_PROMOTION"


class StanceOperator(str, Enum):
    STAY_WITH_SPECIFIC_OBJECT = "STAY_WITH_SPECIFIC_OBJECT"
    PROTECT_USER_AGENCY = "PROTECT_USER_AGENCY"
    HOLD_UNFINISHED_OPEN = "HOLD_UNFINISHED_OPEN"
    WELCOME_BOUNDED_CHANGE = "WELCOME_BOUNDED_CHANGE"


class EmlisTraceClaimDomain(str, Enum):
    INTERPRETIVE_OBSERVATION = "EMLIS_INTERPRETIVE_OBSERVATION"
    SUBJECTIVE_RESPONSE = "EMLIS_SUBJECTIVE_RESPONSE"


class CMEEStage1ContractError(ValueError):
    """Raised when the private Stage 1 identity/ref spine is not canonical."""


@dataclass(frozen=True, slots=True)
class ArgumentBinding:
    role: ArgumentRole
    semantic_ref: str


@dataclass(frozen=True, slots=True)
class EmlisInterpretationCandidate:
    schema_version: str
    candidate_id: str
    candidate_kind: InterpretationKind
    claim_domain: str
    semantic_operator: SemanticOperator
    argument_bindings: Tuple[ArgumentBinding, ...]
    relation_operator: RelationOperator
    relation_basis_refs: Tuple[str, ...]
    derivation_rule_id: str
    semantic_refs: Tuple[str, ...]
    evidence_refs: Tuple[str, ...]
    basis_candidate_refs: Tuple[str, ...]
    epistemic_state: InterpretationEpistemicState
    required_qualifiers: Tuple[str, ...]
    forbidden_promotions: Tuple[str, ...]


@dataclass(frozen=True, slots=True)
class MeaningFieldEntry:
    slot: MeaningFieldSlot
    interpretation_candidate_refs: Tuple[str, ...]
    semantic_refs: Tuple[str, ...]
    evidence_refs: Tuple[str, ...]


@dataclass(frozen=True, slots=True)
class EmlisMeaningField:
    schema_version: str
    meaning_field_id: str
    grounded_graph_ref: str
    center_candidate_ref: str
    entries: Tuple[MeaningFieldEntry, ...]
    required_candidate_refs: Tuple[str, ...]
    material_unknown_refs: Tuple[str, ...]


@dataclass(frozen=True, slots=True)
class PlannedObservationContribution:
    schema_version: str
    contribution_id: str
    parent_duty_ref: str
    contribution_kind: ObservationContributionKind
    interpretation_candidate_refs: Tuple[str, ...]
    semantic_operator: SemanticOperator
    argument_bindings: Tuple[ArgumentBinding, ...]
    relation_operator: RelationOperator
    relation_basis_refs: Tuple[str, ...]
    derivation_rule_id: str
    semantic_refs: Tuple[str, ...]
    evidence_refs: Tuple[str, ...]
    retention: str
    semantic_key_version: str
    canonical_semantic_key: str
    prerequisite_contribution_refs: Tuple[str, ...]
    forbidden_operations: Tuple[str, ...]


@dataclass(frozen=True, slots=True)
class SubjectiveProposition:
    subjective_operator: SubjectiveOperator
    target_contribution_refs: Tuple[str, ...]
    response_object_refs: Tuple[str, ...]
    affect_category: Optional[AffectCategory]
    affect_intensity: Optional[AffectIntensity]
    stance_operator: Optional[StanceOperator]
    counterposition_target_ref: Optional[str]
    referenced_actor_refs: Tuple[str, ...]
    referenced_experiencer_refs: Tuple[str, ...]
    addressee_role: str
    polarity: str
    modality: str


@dataclass(frozen=True, slots=True)
class EmlisSubjectiveClaim:
    schema_version: str
    subjective_claim_id: str
    parent_duty_ref: str
    speaker_owner: str
    claim_domain: str
    subjective_mode: SubjectiveMode
    asserted_subjective_proposition: SubjectiveProposition
    basis_observation_contribution_refs: Tuple[str, ...]
    basis_semantic_refs: Tuple[str, ...]
    source_reception_act_refs: Tuple[str, ...]
    value_principle_refs: Tuple[str, ...]
    user_fact_effect: int
    forbidden_promotions: Tuple[str, ...]


@dataclass(frozen=True, slots=True)
class EmlisStage1Projection:
    schema_version: str
    projection_id: str
    grounded_graph_ref: str
    parent_observation_duty_ref: str
    parent_reception_duty_ref: str
    interpretation_candidates: Tuple[EmlisInterpretationCandidate, ...]
    meaning_field: EmlisMeaningField
    observation_contributions: Tuple[PlannedObservationContribution, ...]
    subjective_claims: Tuple[EmlisSubjectiveClaim, ...]
    ordered_observation_refs: Tuple[str, ...]
    ordered_subjective_refs: Tuple[str, ...]
    retained_reception_act_ids: Tuple[str, ...]
    observation_depth_class: ObservationDepthClass
    subjective_depth_class: SubjectiveDepthClass
    temperature_class: TemperatureClass
    reception_style_policy_ref: str
    emlis_value_policy_ref: str
    emlis_microgrammar_policy_ref: str


@dataclass(frozen=True, slots=True)
class ClauseFrame:
    move_ref: str
    discourse_relation: str
    topic_ref: Optional[str]
    predicate_operator: str
    object_ref: Optional[str]
    argument_bindings: Tuple[ArgumentBinding, ...]
    qualifier_refs: Tuple[str, ...]
    polarity: str
    modality: str
    time_scope: str
    actor_refs: Tuple[str, ...]
    experiencer_refs: Tuple[str, ...]
    addressee_role: str
    epistemic_marker: Optional[str]
    speaker_marker: Optional[str]
    connective_requirement: Optional[str]
    reception_style_policy_ref: str
    terminal_style: str


@dataclass(frozen=True, slots=True)
class RealizedSemanticBinding:
    semantic_ref: str
    clause_slot: str
    surface_scalar_start: int
    surface_scalar_end: int
    surface_span_sha256: str


@dataclass(frozen=True, slots=True, repr=False)
class RealizedSentenceUnit:
    unit_id: str
    projection_ref: str
    layer: str
    move_ref: str
    clause_frames: Tuple[ClauseFrame, ...]
    text: str = field(repr=False)
    basis_anchor_refs: Tuple[str, ...] = ()
    realized_semantic_bindings: Tuple[RealizedSemanticBinding, ...] = ()
    discourse_link_to_prior_sentence: Optional[str] = None
    composition_variant_id: str = ""


@dataclass(frozen=True, slots=True)
class EmlisStage1PositiveTraceExtension:
    schema_version: str
    claim_domain: EmlisTraceClaimDomain
    owner_ref: str
    contribution_refs: Tuple[str, ...]
    basis_trace_refs: Tuple[str, ...]
    interpretation_candidate_refs: Tuple[str, ...]
    subjective_claim_ref: Optional[str]
    basis_observation_contribution_refs: Tuple[str, ...]
    value_principle_refs: Tuple[str, ...]
    speaker_owner: Optional[str]
    user_fact_effect: int
    composition_variant_id: str


_STAGE1_IDENTITY_FIELDS = {
    EmlisInterpretationCandidate: ("candidate_id", "candidate"),
    EmlisMeaningField: ("meaning_field_id", "meaning-field"),
    PlannedObservationContribution: ("contribution_id", "contribution"),
    EmlisSubjectiveClaim: ("subjective_claim_id", "subjective-claim"),
    EmlisStage1Projection: ("projection_id", "projection"),
    RealizedSentenceUnit: ("unit_id", "unit"),
}
_STAGE1_TUPLE_FIELDS = {
    EmlisInterpretationCandidate: (
        "argument_bindings",
        "relation_basis_refs",
        "semantic_refs",
        "evidence_refs",
        "basis_candidate_refs",
        "required_qualifiers",
        "forbidden_promotions",
    ),
    MeaningFieldEntry: (
        "interpretation_candidate_refs",
        "semantic_refs",
        "evidence_refs",
    ),
    EmlisMeaningField: (
        "entries",
        "required_candidate_refs",
        "material_unknown_refs",
    ),
    PlannedObservationContribution: (
        "interpretation_candidate_refs",
        "argument_bindings",
        "relation_basis_refs",
        "semantic_refs",
        "evidence_refs",
        "prerequisite_contribution_refs",
        "forbidden_operations",
    ),
    SubjectiveProposition: (
        "target_contribution_refs",
        "response_object_refs",
        "referenced_actor_refs",
        "referenced_experiencer_refs",
    ),
    EmlisSubjectiveClaim: (
        "basis_observation_contribution_refs",
        "basis_semantic_refs",
        "source_reception_act_refs",
        "value_principle_refs",
        "forbidden_promotions",
    ),
    EmlisStage1Projection: (
        "interpretation_candidates",
        "observation_contributions",
        "subjective_claims",
        "ordered_observation_refs",
        "ordered_subjective_refs",
        "retained_reception_act_ids",
    ),
    ClauseFrame: (
        "argument_bindings",
        "qualifier_refs",
        "actor_refs",
        "experiencer_refs",
    ),
    RealizedSentenceUnit: (
        "clause_frames",
        "basis_anchor_refs",
        "realized_semantic_bindings",
    ),
    EmlisStage1PositiveTraceExtension: (
        "contribution_refs",
        "basis_trace_refs",
        "interpretation_candidate_refs",
        "basis_observation_contribution_refs",
        "value_principle_refs",
    ),
}
_VERSION_QUALIFIED_REF_RE = re.compile(
    r"^(?P<ref_type>[a-z][a-z0-9_-]*):(?P<ref_id>[^@\s]+)@(?P<version>[^@\s]+)$"
)


def _stage1_json_value(value: Any) -> Any:
    if isinstance(value, Enum):
        return value.value
    if is_dataclass(value):
        return {
            row.name: _stage1_json_value(getattr(value, row.name))
            for row in dataclass_fields(value)
        }
    if isinstance(value, Mapping):
        if any(type(key) is not str for key in value):
            raise CMEEStage1ContractError("stage1_canonical_json_key_invalid")
        return {key: _stage1_json_value(item) for key, item in value.items()}
    if isinstance(value, (tuple, list)):
        return [_stage1_json_value(item) for item in value]
    if value is None or type(value) in {str, int, bool}:
        return value
    raise CMEEStage1ContractError("stage1_canonical_json_value_invalid")


def _validate_stage1_immutable_shape(value: object) -> None:
    tuple_fields = _STAGE1_TUPLE_FIELDS.get(type(value))
    if tuple_fields is None:
        raise CMEEStage1ContractError("stage1_contract_type_invalid")
    if any(type(getattr(value, name)) is not tuple for name in tuple_fields):
        raise CMEEStage1ContractError("stage1_contract_array_not_tuple")


def stage1_canonical_json_bytes(value: Any) -> bytes:
    """Return the sole Stage 1 canonical UTF-8 JSON representation."""

    try:
        return json.dumps(
            _stage1_json_value(value),
            ensure_ascii=False,
            sort_keys=True,
            separators=(",", ":"),
            allow_nan=False,
        ).encode("utf-8")
    except CMEEStage1ContractError:
        raise
    except (TypeError, ValueError):
        raise CMEEStage1ContractError("stage1_canonical_json_invalid") from None


def _stage1_identity_material(value: object) -> tuple[str, Mapping[str, Any]]:
    identity_shape = _STAGE1_IDENTITY_FIELDS.get(type(value))
    if identity_shape is None:
        raise CMEEStage1ContractError("stage1_identity_type_invalid")
    identity_field, prefix = identity_shape
    if isinstance(value, EmlisStage1Projection):
        material: Mapping[str, Any] = {
            "schema_version": value.schema_version,
            "grounded_graph_ref": value.grounded_graph_ref,
            "parent_observation_duty_ref": value.parent_observation_duty_ref,
            "parent_reception_duty_ref": value.parent_reception_duty_ref,
            "interpretation_candidate_ids": [
                row.candidate_id for row in value.interpretation_candidates
            ],
            "meaning_field_id": value.meaning_field.meaning_field_id,
            "observation_contribution_ids": [
                row.contribution_id for row in value.observation_contributions
            ],
            "subjective_claim_ids": [
                row.subjective_claim_id for row in value.subjective_claims
            ],
            "ordered_observation_refs": value.ordered_observation_refs,
            "ordered_subjective_refs": value.ordered_subjective_refs,
            "retained_reception_act_ids": value.retained_reception_act_ids,
            "observation_depth_class": value.observation_depth_class,
            "subjective_depth_class": value.subjective_depth_class,
            "temperature_class": value.temperature_class,
            "reception_style_policy_ref": value.reception_style_policy_ref,
            "emlis_value_policy_ref": value.emlis_value_policy_ref,
            "emlis_microgrammar_policy_ref": value.emlis_microgrammar_policy_ref,
        }
    else:
        material = {
            row.name: getattr(value, row.name)
            for row in dataclass_fields(value)
            if row.name != identity_field
        }
    return prefix, material


def recompute_stage1_identity(value: object) -> str:
    """Recompute one of the exact-six typed Stage 1 identities."""

    prefix, material = _stage1_identity_material(value)
    canonical = stage1_canonical_json_bytes(material)
    digest = hashlib.sha256(prefix.encode("utf-8") + b"\0" + canonical).hexdigest()
    return f"{prefix}-{digest}"


def validate_stage1_identity(value: object) -> None:
    identity_field, _prefix = _STAGE1_IDENTITY_FIELDS.get(type(value), (None, None))
    if identity_field is None:
        raise CMEEStage1ContractError("stage1_identity_type_invalid")
    claimed = getattr(value, identity_field)
    expected = recompute_stage1_identity(value)
    if type(claimed) is not str or not hmac.compare_digest(claimed, expected):
        raise CMEEStage1ContractError("stage1_identity_mismatch")


def validate_version_qualified_ref(
    value: str,
    *,
    expected_types: Sequence[str] = (),
) -> None:
    if type(value) is not str:
        raise CMEEStage1ContractError("stage1_external_ref_type_invalid")
    match = _VERSION_QUALIFIED_REF_RE.fullmatch(value)
    if match is None:
        raise CMEEStage1ContractError("stage1_external_ref_not_version_qualified")
    if expected_types and match.group("ref_type") not in set(expected_types):
        raise CMEEStage1ContractError("stage1_external_ref_kind_invalid")


def _version_qualified_local_id(value: str) -> str:
    match = _VERSION_QUALIFIED_REF_RE.fullmatch(value)
    if match is None:
        raise CMEEStage1ContractError("stage1_external_ref_not_version_qualified")
    return match.group("ref_id")


def validate_stage1_local_ref_dag(
    ordered_ids: Sequence[str],
    dependencies: Mapping[str, Sequence[str]],
) -> None:
    """Reject missing, foreign, self, forward and cyclic local references."""

    ids = tuple(ordered_ids)
    if any(type(row) is not str or not row for row in ids) or len(ids) != len(set(ids)):
        raise CMEEStage1ContractError("stage1_local_ref_identity_invalid")
    if set(dependencies) != set(ids):
        raise CMEEStage1ContractError("stage1_local_ref_owner_set_mismatch")
    known = set(ids)
    normalized: dict[str, tuple[str, ...]] = {}
    for owner_id in ids:
        refs = tuple(dependencies[owner_id])
        if any(type(ref) is not str or not ref for ref in refs):
            raise CMEEStage1ContractError("stage1_local_ref_identity_invalid")
        if len(refs) != len(set(refs)):
            raise CMEEStage1ContractError("stage1_local_ref_duplicate")
        if owner_id in refs:
            raise CMEEStage1ContractError("stage1_local_ref_self")
        if any("@" in ref or _VERSION_QUALIFIED_REF_RE.fullmatch(ref) for ref in refs):
            raise CMEEStage1ContractError("stage1_local_ref_foreign")
        if any(ref not in known for ref in refs):
            raise CMEEStage1ContractError("stage1_local_ref_missing")
        normalized[owner_id] = refs

    state: dict[str, int] = {}

    def visit(owner_id: str) -> None:
        current = state.get(owner_id, 0)
        if current == 1:
            raise CMEEStage1ContractError("stage1_local_ref_cycle")
        if current == 2:
            return
        state[owner_id] = 1
        for ref in normalized[owner_id]:
            visit(ref)
        state[owner_id] = 2

    for owner_id in ids:
        visit(owner_id)

    position = {owner_id: index for index, owner_id in enumerate(ids)}
    if any(
        position[ref] >= position[owner_id]
        for owner_id, refs in normalized.items()
        for ref in refs
    ):
        raise CMEEStage1ContractError("stage1_local_ref_forward")


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
    """Private source evidence with field-relative scalar coordinates.

    ``scalar_start/end`` index the canonical original field body. The UTF-8
    coordinates remain absolute offsets into ``SourceEnvelope.raw_utf8``.
    """

    evidence_id: str
    source_span_id: str
    source_envelope_id: str
    field_path: str
    element_index: int
    field_utf8_start: int
    field_utf8_end: int
    scalar_start: int
    scalar_end: int
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


def _require_unique_nonempty_refs(values: Sequence[str], *, code: str) -> None:
    refs = tuple(values)
    if (
        not refs
        or any(type(ref) is not str or not ref for ref in refs)
        or len(refs) != len(set(refs))
    ):
        raise CMEEStage1ContractError(code)


def _require_local_subset(
    values: Sequence[str],
    allowed: set[str],
    *,
    code: str,
    allow_empty: bool = True,
) -> None:
    refs = tuple(values)
    if not allow_empty and not refs:
        raise CMEEStage1ContractError(code)
    if (
        any(type(ref) is not str or not ref for ref in refs)
        or len(refs) != len(set(refs))
        or any(ref not in allowed for ref in refs)
    ):
        raise CMEEStage1ContractError(code)


def _validate_stage1_external_refs(
    values: Sequence[str],
    *,
    expected_types: Sequence[str] = (),
) -> None:
    for ref in values:
        validate_version_qualified_ref(ref, expected_types=expected_types)


def validate_stage1_projection(
    projection: EmlisStage1Projection,
    *,
    parent_plan: Optional[ExperiencePlan] = None,
) -> None:
    """Validate the disabled request-local projection and its identity DAG.

    The projection is not an ExperiencePlan and this validator never installs a
    second duty owner.  ``parent_plan`` is only an optional equality check for
    the existing flat provisional mapping.
    """

    if type(projection) is not EmlisStage1Projection:
        raise CMEEStage1ContractError("stage1_projection_type_invalid")
    _validate_stage1_immutable_shape(projection)
    if projection.schema_version != CMEE_STAGE1_RESPONSE_SCHEMA_VERSION:
        raise CMEEStage1ContractError("stage1_projection_schema_version_invalid")
    validate_version_qualified_ref(
        projection.grounded_graph_ref, expected_types=("grounded",)
    )
    for ref in (
        projection.reception_style_policy_ref,
        projection.emlis_value_policy_ref,
        projection.emlis_microgrammar_policy_ref,
    ):
        validate_version_qualified_ref(ref, expected_types=("policy",))
    if (
        type(projection.parent_observation_duty_ref) is not str
        or not projection.parent_observation_duty_ref
        or type(projection.parent_reception_duty_ref) is not str
        or not projection.parent_reception_duty_ref
        or projection.parent_observation_duty_ref
        == projection.parent_reception_duty_ref
    ):
        raise CMEEStage1ContractError("stage1_parent_duty_ref_invalid")

    candidates = projection.interpretation_candidates
    contributions = projection.observation_contributions
    claims = projection.subjective_claims
    if not candidates or not contributions or not claims:
        raise CMEEStage1ContractError("stage1_projection_required_child_missing")
    if (
        any(type(row) is not EmlisInterpretationCandidate for row in candidates)
        or type(projection.meaning_field) is not EmlisMeaningField
        or any(
            type(row) is not PlannedObservationContribution
            for row in contributions
        )
        or any(type(row) is not EmlisSubjectiveClaim for row in claims)
    ):
        raise CMEEStage1ContractError("stage1_projection_child_type_invalid")
    if len(candidates) > 16:
        raise CMEEStage1ContractError("stage1_candidate_pool_cap_exceeded")
    for child in (*candidates, projection.meaning_field, *contributions, *claims):
        _validate_stage1_immutable_shape(child)
        if child.schema_version != projection.schema_version:
            raise CMEEStage1ContractError("stage1_child_schema_version_mismatch")
        validate_stage1_identity(child)

    candidate_ids = tuple(row.candidate_id for row in candidates)
    contribution_ids = tuple(row.contribution_id for row in contributions)
    claim_ids = tuple(row.subjective_claim_id for row in claims)
    _require_unique_nonempty_refs(candidate_ids, code="stage1_candidate_identity_invalid")
    _require_unique_nonempty_refs(
        contribution_ids, code="stage1_contribution_identity_invalid"
    )
    _require_unique_nonempty_refs(claim_ids, code="stage1_subjective_identity_invalid")

    validate_stage1_local_ref_dag(
        candidate_ids,
        {row.candidate_id: row.basis_candidate_refs for row in candidates},
    )
    validate_stage1_local_ref_dag(
        contribution_ids,
        {
            row.contribution_id: row.prerequisite_contribution_refs
            for row in contributions
        },
    )

    candidate_set = set(candidate_ids)
    contribution_set = set(contribution_ids)
    claim_set = set(claim_ids)
    meaning_field = projection.meaning_field
    if meaning_field.grounded_graph_ref != projection.grounded_graph_ref:
        raise CMEEStage1ContractError("stage1_meaning_field_graph_mismatch")
    if meaning_field.center_candidate_ref not in candidate_set:
        raise CMEEStage1ContractError("stage1_meaning_field_center_missing")
    _require_local_subset(
        meaning_field.required_candidate_refs,
        candidate_set,
        code="stage1_meaning_field_required_candidate_invalid",
        allow_empty=False,
    )
    seen_slots: set[MeaningFieldSlot] = set()
    for entry in meaning_field.entries:
        if type(entry) is not MeaningFieldEntry:
            raise CMEEStage1ContractError("stage1_meaning_field_entry_type_invalid")
        _validate_stage1_immutable_shape(entry)
        if type(entry.slot) is not MeaningFieldSlot:
            raise CMEEStage1ContractError("stage1_meaning_field_slot_invalid")
        if entry.slot in seen_slots:
            raise CMEEStage1ContractError("stage1_meaning_field_slot_duplicate")
        seen_slots.add(entry.slot)
        _require_local_subset(
            entry.interpretation_candidate_refs,
            candidate_set,
            code="stage1_meaning_field_candidate_ref_invalid",
            allow_empty=False,
        )
        _validate_stage1_external_refs(
            entry.semantic_refs, expected_types=("node", "edge")
        )
        _validate_stage1_external_refs(
            entry.evidence_refs, expected_types=("evidence",)
        )
    _validate_stage1_external_refs(
        meaning_field.material_unknown_refs, expected_types=("unknown",)
    )

    for row in candidates:
        if (
            type(row.candidate_kind) is not InterpretationKind
            or type(row.semantic_operator) is not SemanticOperator
            or type(row.relation_operator) is not RelationOperator
            or type(row.epistemic_state) is not InterpretationEpistemicState
            or any(type(binding) is not ArgumentBinding for binding in row.argument_bindings)
            or any(type(binding.role) is not ArgumentRole for binding in row.argument_bindings)
        ):
            raise CMEEStage1ContractError("stage1_candidate_type_invalid")
        if row.claim_domain != EmlisTraceClaimDomain.INTERPRETIVE_OBSERVATION.value:
            raise CMEEStage1ContractError("stage1_candidate_claim_domain_invalid")
        if row.epistemic_state is not InterpretationEpistemicState.PROVISIONAL_INTERPRETATION:
            raise CMEEStage1ContractError("stage1_candidate_epistemic_state_invalid")
        _require_unique_nonempty_refs(
            row.semantic_refs, code="stage1_candidate_semantic_ref_invalid"
        )
        _require_unique_nonempty_refs(
            row.evidence_refs, code="stage1_candidate_evidence_ref_invalid"
        )
        _validate_stage1_external_refs(
            row.semantic_refs, expected_types=("node", "edge")
        )
        _validate_stage1_external_refs(
            row.evidence_refs, expected_types=("evidence",)
        )
        _validate_stage1_external_refs(
            row.relation_basis_refs, expected_types=("edge",)
        )
        if any(
            binding.semantic_ref not in set(row.semantic_refs)
            for binding in row.argument_bindings
        ):
            raise CMEEStage1ContractError("stage1_candidate_argument_ref_invalid")
        if row.relation_operator is RelationOperator.NO_RELATION_CLAIM:
            if row.relation_basis_refs:
                raise CMEEStage1ContractError("stage1_candidate_relation_basis_invalid")
        elif not row.relation_basis_refs:
            raise CMEEStage1ContractError("stage1_candidate_relation_basis_missing")

    for row in contributions:
        if (
            type(row.contribution_kind) is not ObservationContributionKind
            or type(row.semantic_operator) is not SemanticOperator
            or type(row.relation_operator) is not RelationOperator
            or any(type(binding) is not ArgumentBinding for binding in row.argument_bindings)
            or any(type(binding.role) is not ArgumentRole for binding in row.argument_bindings)
        ):
            raise CMEEStage1ContractError("stage1_contribution_type_invalid")
        if row.parent_duty_ref != projection.parent_observation_duty_ref:
            raise CMEEStage1ContractError("stage1_contribution_parent_duty_mismatch")
        _require_local_subset(
            row.interpretation_candidate_refs,
            candidate_set,
            code="stage1_contribution_candidate_ref_invalid",
            allow_empty=False,
        )
        _validate_stage1_external_refs(
            row.semantic_refs, expected_types=("node", "edge")
        )
        _validate_stage1_external_refs(
            row.evidence_refs, expected_types=("evidence",)
        )
        _validate_stage1_external_refs(
            row.relation_basis_refs, expected_types=("edge",)
        )

    retained_acts = set(projection.retained_reception_act_ids)
    _require_unique_nonempty_refs(
        projection.retained_reception_act_ids,
        code="stage1_retained_reception_act_invalid",
    )
    referenced_acts: set[str] = set()
    for row in claims:
        proposition = row.asserted_subjective_proposition
        if (
            type(row.subjective_mode) is not SubjectiveMode
            or type(proposition) is not SubjectiveProposition
        ):
            raise CMEEStage1ContractError("stage1_subjective_type_invalid")
        _validate_stage1_immutable_shape(proposition)
        if type(proposition.subjective_operator) is not SubjectiveOperator:
            raise CMEEStage1ContractError("stage1_subjective_operator_invalid")
        if row.parent_duty_ref != projection.parent_reception_duty_ref:
            raise CMEEStage1ContractError("stage1_subjective_parent_duty_mismatch")
        if row.speaker_owner != "EMLIS":
            raise CMEEStage1ContractError("stage1_subjective_speaker_invalid")
        if row.claim_domain != EmlisTraceClaimDomain.SUBJECTIVE_RESPONSE.value:
            raise CMEEStage1ContractError("stage1_subjective_claim_domain_invalid")
        if row.user_fact_effect != 0 or type(row.user_fact_effect) is not int:
            raise CMEEStage1ContractError("stage1_subjective_user_fact_effect_invalid")
        _require_local_subset(
            row.basis_observation_contribution_refs,
            contribution_set,
            code="stage1_subjective_basis_contribution_invalid",
            allow_empty=False,
        )
        _require_local_subset(
            proposition.target_contribution_refs,
            set(row.basis_observation_contribution_refs),
            code="stage1_subjective_target_contribution_invalid",
            allow_empty=False,
        )
        _require_unique_nonempty_refs(
            proposition.response_object_refs,
            code="stage1_subjective_response_object_invalid",
        )
        for ref in proposition.response_object_refs:
            if ref not in contribution_set:
                validate_version_qualified_ref(ref, expected_types=("node", "edge"))
        if proposition.counterposition_target_ref is not None:
            counterposition_ref = proposition.counterposition_target_ref
            if type(counterposition_ref) is not str or not counterposition_ref:
                raise CMEEStage1ContractError(
                    "stage1_subjective_counterposition_ref_invalid"
                )
            if counterposition_ref not in contribution_set:
                validate_version_qualified_ref(
                    counterposition_ref, expected_types=("node", "edge")
                )
        _validate_stage1_external_refs(
            proposition.referenced_actor_refs, expected_types=("node",)
        )
        _validate_stage1_external_refs(
            proposition.referenced_experiencer_refs, expected_types=("node",)
        )
        _require_local_subset(
            row.source_reception_act_refs,
            retained_acts,
            code="stage1_subjective_reception_act_unknown",
            allow_empty=False,
        )
        referenced_acts.update(row.source_reception_act_refs)
        _validate_stage1_external_refs(
            row.basis_semantic_refs, expected_types=("node", "edge")
        )
        _validate_stage1_external_refs(
            row.value_principle_refs, expected_types=("policy",)
        )
    if referenced_acts != retained_acts:
        raise CMEEStage1ContractError("stage1_retained_reception_act_uncovered")

    if (
        len(projection.ordered_observation_refs)
        != len(set(projection.ordered_observation_refs))
        or set(projection.ordered_observation_refs) != contribution_set
    ):
        raise CMEEStage1ContractError("stage1_observation_order_not_exact_cover")
    if (
        len(projection.ordered_subjective_refs)
        != len(set(projection.ordered_subjective_refs))
        or set(projection.ordered_subjective_refs) != claim_set
    ):
        raise CMEEStage1ContractError("stage1_subjective_order_not_exact_cover")

    if type(projection.observation_depth_class) is not ObservationDepthClass:
        raise CMEEStage1ContractError("stage1_observation_depth_class_invalid")
    if type(projection.subjective_depth_class) is not SubjectiveDepthClass:
        raise CMEEStage1ContractError("stage1_subjective_depth_class_invalid")
    if type(projection.temperature_class) is not TemperatureClass:
        raise CMEEStage1ContractError("stage1_temperature_class_invalid")
    observation_count = len(contribution_set)
    observation_ranges = {
        ObservationDepthClass.FOCUSED: (1, 1),
        ObservationDepthClass.LAYERED: (2, 3),
        ObservationDepthClass.DENSE: (4, 5),
    }
    observation_floor, observation_ceiling = observation_ranges[
        projection.observation_depth_class
    ]
    if not observation_floor <= observation_count <= observation_ceiling:
        raise CMEEStage1ContractError("stage1_observation_depth_mismatch")
    subjective_count = len(claim_set)
    subjective_ranges = {
        SubjectiveDepthClass.FOCUSED: (1, 1),
        SubjectiveDepthClass.LAYERED: (2, 3),
        SubjectiveDepthClass.DENSE: (3, 4),
    }
    subjective_floor, subjective_ceiling = subjective_ranges[
        projection.subjective_depth_class
    ]
    if not subjective_floor <= subjective_count <= subjective_ceiling:
        raise CMEEStage1ContractError("stage1_subjective_depth_mismatch")

    if parent_plan is not None:
        if type(parent_plan) is not ExperiencePlan:
            raise CMEEStage1ContractError("stage1_parent_plan_type_invalid")
        if (
            projection.parent_observation_duty_ref
            != parent_plan.observation_duty_id
            or projection.parent_reception_duty_ref != parent_plan.reception_duty_id
            or projection.retained_reception_act_ids
            != parent_plan.allowed_reception_act_ids
        ):
            raise CMEEStage1ContractError("stage1_parent_plan_projection_mismatch")

    validate_stage1_identity(projection)


def validate_stage1_sentence_unit(
    unit: RealizedSentenceUnit,
    projection: EmlisStage1Projection,
    *,
    prior_unit_ids: Sequence[str] = (),
) -> None:
    validate_stage1_projection(projection)
    if type(unit) is not RealizedSentenceUnit:
        raise CMEEStage1ContractError("stage1_unit_type_invalid")
    _validate_stage1_immutable_shape(unit)
    if type(prior_unit_ids) is not tuple:
        raise CMEEStage1ContractError("stage1_unit_prior_ids_not_tuple")
    if any(type(frame) is not ClauseFrame for frame in unit.clause_frames):
        raise CMEEStage1ContractError("stage1_unit_clause_frame_type_invalid")
    for frame in unit.clause_frames:
        _validate_stage1_immutable_shape(frame)
        validate_version_qualified_ref(frame.move_ref, expected_types=("move",))
        validate_version_qualified_ref(
            frame.reception_style_policy_ref, expected_types=("policy",)
        )
        if frame.topic_ref is not None:
            validate_version_qualified_ref(
                frame.topic_ref, expected_types=("node", "edge")
            )
        if frame.object_ref is not None:
            validate_version_qualified_ref(
                frame.object_ref, expected_types=("node", "edge")
            )
        _validate_stage1_external_refs(frame.actor_refs, expected_types=("node",))
        _validate_stage1_external_refs(
            frame.experiencer_refs, expected_types=("node",)
        )
        if (
            any(type(binding) is not ArgumentBinding for binding in frame.argument_bindings)
            or any(
                type(binding.role) is not ArgumentRole
                for binding in frame.argument_bindings
            )
        ):
            raise CMEEStage1ContractError("stage1_unit_argument_binding_invalid")
    if unit.projection_ref != projection.projection_id:
        raise CMEEStage1ContractError("stage1_unit_foreign_projection")
    if unit.layer not in {"LAYER_1", "LAYER_2"}:
        raise CMEEStage1ContractError("stage1_unit_layer_invalid")
    if (
        not unit.clause_frames
        or type(unit.text) is not str
        or not unit.text
        or type(unit.composition_variant_id) is not str
        or not unit.composition_variant_id
    ):
        raise CMEEStage1ContractError("stage1_unit_required_field_missing")
    validate_version_qualified_ref(unit.move_ref, expected_types=("move",))
    if unit.discourse_link_to_prior_sentence is not None:
        prior_ref = unit.discourse_link_to_prior_sentence
        if (
            type(prior_ref) is not str
            or not prior_ref
            or "@" in prior_ref
            or prior_ref == unit.unit_id
            or prior_ref not in set(prior_unit_ids)
        ):
            raise CMEEStage1ContractError("stage1_unit_prior_ref_invalid")
    local_anchor_set = {
        *(row.contribution_id for row in projection.observation_contributions),
        *(row.subjective_claim_id for row in projection.subjective_claims),
    }
    _require_local_subset(
        unit.basis_anchor_refs,
        local_anchor_set,
        code="stage1_unit_basis_anchor_invalid",
        allow_empty=False,
    )
    text_scalar_length = len(unit.text)
    for binding in unit.realized_semantic_bindings:
        if type(binding) is not RealizedSemanticBinding:
            raise CMEEStage1ContractError("stage1_unit_binding_type_invalid")
        validate_version_qualified_ref(
            binding.semantic_ref, expected_types=("node", "edge")
        )
        if (
            type(binding.surface_scalar_start) is not int
            or type(binding.surface_scalar_end) is not int
            or not 0 <= binding.surface_scalar_start < binding.surface_scalar_end
            <= text_scalar_length
        ):
            raise CMEEStage1ContractError("stage1_unit_surface_range_invalid")
        if (
            type(binding.surface_span_sha256) is not str
            or re.fullmatch(r"[0-9a-f]{64}", binding.surface_span_sha256) is None
        ):
            raise CMEEStage1ContractError("stage1_unit_surface_digest_invalid")
        selected = unit.text[
            binding.surface_scalar_start : binding.surface_scalar_end
        ].encode("utf-8")
        if not hmac.compare_digest(
            hashlib.sha256(selected).hexdigest(), binding.surface_span_sha256
        ):
            raise CMEEStage1ContractError("stage1_unit_surface_digest_invalid")
    validate_stage1_identity(unit)


@dataclass(frozen=True, slots=True)
class CommonGuardResultProof:
    """Body-free identity/pass projection of one actual common guard result."""

    guard_id: str
    passed: bool


@dataclass(frozen=True, slots=True, repr=False)
class CommonGuardProof:
    """Private proof for the common guards applied to Observation units only."""

    schema_version: str
    proof_id: str
    source_envelope_id: str
    graph_id: str
    plan_id: str
    guarded_observation_units: Tuple[Tuple[str, str], ...]
    guard_results: Tuple[CommonGuardResultProof, ...]
    stabilization_report_name: str
    stabilization_phase: str
    stabilization_core_id: str
    stabilization_passed: bool
    common_shapes_ready: bool
    stabilization_guard_names: Tuple[str, ...]
    issue_codes: Tuple[str, ...]


@dataclass(frozen=True, slots=True, repr=False)
class VisibleUnitTrace:
    visible_unit_id: str
    source_sentence_id: str
    source_envelope_id: str
    source_version: str
    obligation_version: str
    owner_universe_digest: str
    artifact_common_guard_proof_ref: str
    role: str
    operation: str
    text_sha256: str = field(repr=False)
    duty_id: str
    meaning_node_ids: Tuple[str, ...]
    meaning_edge_ids: Tuple[str, ...]
    evidence_ids: Tuple[str, ...]
    constrained_by_owner_ids: Tuple[str, ...] = ()
    emlis_stage1_extension: Optional[EmlisStage1PositiveTraceExtension] = None


def validate_stage1_trace_spine(
    trace_rows: Sequence[VisibleUnitTrace],
    projection: EmlisStage1Projection,
) -> None:
    """Validate the registered private Emlis trace specialization by role."""

    validate_stage1_projection(projection)
    rows = tuple(trace_rows)
    if any(type(row) is not VisibleUnitTrace for row in rows):
        raise CMEEStage1ContractError("stage1_trace_row_type_invalid")
    if any(
        any(
            type(getattr(row, field_name)) is not tuple
            for field_name in (
                "meaning_node_ids",
                "meaning_edge_ids",
                "evidence_ids",
                "constrained_by_owner_ids",
            )
        )
        for row in rows
    ):
        raise CMEEStage1ContractError("stage1_trace_array_not_tuple")
    visible_ids = tuple(row.visible_unit_id for row in rows)
    _require_unique_nonempty_refs(visible_ids, code="stage1_trace_identity_invalid")
    position = {visible_id: index for index, visible_id in enumerate(visible_ids)}
    candidates = {row.candidate_id for row in projection.interpretation_candidates}
    contributions = {
        row.contribution_id: row for row in projection.observation_contributions
    }
    claims = {row.subjective_claim_id: row for row in projection.subjective_claims}
    observation_contribution_counts = {ref: 0 for ref in contributions}
    subjective_claim_counts = {ref: 0 for ref in claims}

    for index, row in enumerate(rows):
        extension = row.emlis_stage1_extension
        if row.role == "UNKNOWN":
            if extension is not None:
                raise CMEEStage1ContractError("stage1_unknown_trace_extension_present")
            if (
                row.meaning_node_ids
                or row.meaning_edge_ids
                or not row.evidence_ids
                or not row.constrained_by_owner_ids
            ):
                raise CMEEStage1ContractError("stage1_unknown_trace_lineage_invalid")
            continue
        if row.role not in {"OBSERVATION", "RECEPTION"}:
            raise CMEEStage1ContractError("stage1_trace_role_invalid")
        if extension is None:
            raise CMEEStage1ContractError("stage1_trace_extension_missing")
        if type(extension) is not EmlisStage1PositiveTraceExtension:
            raise CMEEStage1ContractError("stage1_trace_extension_type_invalid")
        _validate_stage1_immutable_shape(extension)
        if extension.schema_version != CMEE_STAGE1_TRACE_EXTENSION_SCHEMA_VERSION:
            raise CMEEStage1ContractError("stage1_trace_extension_version_invalid")
        if extension.owner_ref != CMEE_STAGE1_EMLIS_OWNER_REF:
            raise CMEEStage1ContractError("stage1_trace_owner_invalid")
        if extension.user_fact_effect != 0 or type(extension.user_fact_effect) is not int:
            raise CMEEStage1ContractError("stage1_trace_user_fact_effect_invalid")
        if (
            type(extension.composition_variant_id) is not str
            or not extension.composition_variant_id
        ):
            raise CMEEStage1ContractError("stage1_trace_variant_missing")
        if not (row.meaning_node_ids or row.meaning_edge_ids) or not row.evidence_ids:
            raise CMEEStage1ContractError("stage1_trace_base_lineage_missing")

        if row.role == "OBSERVATION":
            if (
                extension.claim_domain
                is not EmlisTraceClaimDomain.INTERPRETIVE_OBSERVATION
                or extension.subjective_claim_ref is not None
                or extension.basis_trace_refs
                or extension.basis_observation_contribution_refs
                or extension.value_principle_refs
                or extension.speaker_owner is not None
            ):
                raise CMEEStage1ContractError("stage1_observation_trace_domain_invalid")
            _require_local_subset(
                extension.contribution_refs,
                set(contributions),
                code="stage1_observation_trace_contribution_invalid",
                allow_empty=False,
            )
            _require_local_subset(
                extension.interpretation_candidate_refs,
                candidates,
                code="stage1_observation_trace_candidate_invalid",
                allow_empty=False,
            )
            reachable_candidates = {
                candidate_ref
                for contribution_ref in extension.contribution_refs
                for candidate_ref in contributions[
                    contribution_ref
                ].interpretation_candidate_refs
            }
            if not set(extension.interpretation_candidate_refs).issubset(
                reachable_candidates
            ):
                raise CMEEStage1ContractError(
                    "stage1_observation_trace_candidate_unreachable"
                )
            reachable_semantic_ids = {
                _version_qualified_local_id(ref)
                for contribution_ref in extension.contribution_refs
                for ref in contributions[contribution_ref].semantic_refs
            } | {
                _version_qualified_local_id(ref)
                for candidate_ref in extension.interpretation_candidate_refs
                for ref in next(
                    candidate
                    for candidate in projection.interpretation_candidates
                    if candidate.candidate_id == candidate_ref
                ).semantic_refs
            }
            reachable_evidence_ids = {
                _version_qualified_local_id(ref)
                for contribution_ref in extension.contribution_refs
                for ref in contributions[contribution_ref].evidence_refs
            } | {
                _version_qualified_local_id(ref)
                for candidate_ref in extension.interpretation_candidate_refs
                for ref in next(
                    candidate
                    for candidate in projection.interpretation_candidates
                    if candidate.candidate_id == candidate_ref
                ).evidence_refs
            }
            if not set((*row.meaning_node_ids, *row.meaning_edge_ids)).issubset(
                reachable_semantic_ids
            ) or not set(row.evidence_ids).issubset(reachable_evidence_ids):
                raise CMEEStage1ContractError(
                    "stage1_observation_trace_lineage_unreachable"
                )
            for contribution_ref in extension.contribution_refs:
                observation_contribution_counts[contribution_ref] += 1
            continue

        if (
            extension.claim_domain is not EmlisTraceClaimDomain.SUBJECTIVE_RESPONSE
            or extension.contribution_refs
            or extension.interpretation_candidate_refs
            or extension.speaker_owner != "EMLIS"
            or extension.subjective_claim_ref not in claims
        ):
            raise CMEEStage1ContractError("stage1_reception_trace_domain_invalid")
        claim = claims[extension.subjective_claim_ref]
        subjective_claim_counts[extension.subjective_claim_ref] += 1
        if (
            tuple(extension.basis_observation_contribution_refs)
            != claim.basis_observation_contribution_refs
            or tuple(extension.value_principle_refs) != claim.value_principle_refs
        ):
            raise CMEEStage1ContractError("stage1_reception_trace_claim_mismatch")
        _require_local_subset(
            extension.basis_observation_contribution_refs,
            set(contributions),
            code="stage1_reception_trace_basis_invalid",
            allow_empty=False,
        )
        _require_unique_nonempty_refs(
            extension.basis_trace_refs,
            code="stage1_reception_trace_ref_invalid",
        )
        reachable_basis_contributions: set[str] = set()
        for basis_ref in extension.basis_trace_refs:
            basis_position = position.get(basis_ref)
            if basis_position is None:
                raise CMEEStage1ContractError("stage1_reception_trace_ref_missing")
            if basis_position >= index:
                raise CMEEStage1ContractError("stage1_reception_trace_ref_forward")
            if rows[basis_position].role != "OBSERVATION":
                raise CMEEStage1ContractError("stage1_reception_trace_ref_foreign")
            basis_extension = rows[basis_position].emlis_stage1_extension
            if basis_extension is None:
                raise CMEEStage1ContractError("stage1_reception_trace_ref_foreign")
            reachable_basis_contributions.update(basis_extension.contribution_refs)
        if not set(extension.basis_observation_contribution_refs).issubset(
            reachable_basis_contributions
        ):
            raise CMEEStage1ContractError(
                "stage1_reception_trace_basis_unreachable"
            )
        reachable_semantic_ids = {
            _version_qualified_local_id(ref) for ref in claim.basis_semantic_refs
        } | {
            _version_qualified_local_id(ref)
            for contribution_ref in extension.basis_observation_contribution_refs
            for ref in contributions[contribution_ref].semantic_refs
        }
        reachable_evidence_ids = {
            _version_qualified_local_id(ref)
            for contribution_ref in extension.basis_observation_contribution_refs
            for ref in contributions[contribution_ref].evidence_refs
        }
        if not set((*row.meaning_node_ids, *row.meaning_edge_ids)).issubset(
            reachable_semantic_ids
        ) or not set(row.evidence_ids).issubset(reachable_evidence_ids):
            raise CMEEStage1ContractError(
                "stage1_reception_trace_lineage_unreachable"
            )

    if any(count != 1 for count in observation_contribution_counts.values()):
        raise CMEEStage1ContractError("stage1_observation_trace_coverage_invalid")
    if any(count != 1 for count in subjective_claim_counts.values()):
        raise CMEEStage1ContractError("stage1_reception_trace_coverage_invalid")


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
    common_guard_proof: CommonGuardProof
    observation: str = field(repr=False)
    reception: str = field(repr=False)
    plan: ExperiencePlan
    trace: Tuple[VisibleUnitTrace, ...]
    visible_unknowns: Tuple[VisibleUnknownUnit, ...]

    @property
    def text(self) -> str:
        layer1 = "\n".join(
            (self.observation, *(row.text for row in self.visible_unknowns))
        )
        return (
            f"見えたこと：\n{layer1}"
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
    "AffectCategory",
    "AffectIntensity",
    "ArgumentBinding",
    "ArgumentRole",
    "AttachmentAdmission",
    "CMEE_COMMON_GUARD_PROOF_VERSION",
    "CMEE_OBLIGATION_VERSION",
    "CMEE_OWNER_UNIVERSE_SCHEMA_VERSION",
    "CMEE_ROUTE_B_POLICY_VERSION",
    "CMEE_SCHEMA_VERSION",
    "CMEE_SOURCE_CONTRACT_VERSION",
    "CMEE_STAGE1_EMLIS_OWNER_REF",
    "CMEE_STAGE1_IDENTITY_ALGORITHM",
    "CMEE_STAGE1_RESPONSE_SCHEMA_VERSION",
    "CMEE_STAGE1_TRACE_EXTENSION_SCHEMA_VERSION",
    "CMEE_TERMINAL_GENERATED_DISABLED",
    "CMEEStage1ContractError",
    "ClauseFrame",
    "CommonGuardProof",
    "CommonGuardResultProof",
    "CoreId",
    "EmlisInterpretationCandidate",
    "EmlisMeaningField",
    "EmlisStage1PositiveTraceExtension",
    "EmlisStage1Projection",
    "EmlisSubjectiveClaim",
    "EmlisTraceClaimDomain",
    "EngineOutcome",
    "EngineStatus",
    "EpistemicState",
    "EvidenceRef",
    "ExecutionMode",
    "ExperiencePlan",
    "GenerationArtifactBundle",
    "GenerationRequest",
    "GroundedMeaningGraph",
    "InterpretationEpistemicState",
    "InterpretationKind",
    "MeaningFieldEntry",
    "MeaningFieldSlot",
    "MeaningEdge",
    "MeaningNode",
    "ObservationContributionKind",
    "ObservationDepthClass",
    "OwnerClass",
    "OwnerDisposition",
    "PlannedObservationContribution",
    "ProductJob",
    "ProviderResolution",
    "RealizedSemanticBinding",
    "RealizedSentenceUnit",
    "RelationOperator",
    "RouteBDisposition",
    "RouteBOwnerDisposition",
    "SemanticOperator",
    "SourceEnvelope",
    "SourceOwnerObligation",
    "SourceOwnerUniverse",
    "StanceOperator",
    "SubjectiveDepthClass",
    "SubjectiveMode",
    "SubjectiveOperator",
    "SubjectiveProposition",
    "TemperatureClass",
    "VisibleAuthority",
    "VisibleUnknownUnit",
    "VisibleUnitTrace",
    "recompute_stage1_identity",
    "stage1_canonical_json_bytes",
    "validate_stage1_identity",
    "validate_stage1_local_ref_dag",
    "validate_stage1_projection",
    "validate_stage1_sentence_unit",
    "validate_stage1_trace_spine",
    "validate_version_qualified_ref",
]
