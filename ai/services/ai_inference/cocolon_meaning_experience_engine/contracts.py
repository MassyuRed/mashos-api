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
CMEE_GROUNDED_GRAPH_SCHEMA_VERSION = "cocolon.cmee.grounded_meaning_graph.v1alpha1"
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


CMEE_STAGE1_RECEPTION_ASSET_MAPPING_VERSION = (
    "cocolon.emlis.stage1.reception_asset_mapping.v1"
)
CMEE_STAGE1_VALUE_POLICY_ID = "cocolon.emlis.stage1.value_policy.v1"
CMEE_STAGE1_VALUE_POLICY_REF = (
    "policy:cocolon.emlis.stage1.value_policy"
    "@cocolon.emlis.stage1.value_policy.v1"
)
CMEE_STAGE1_MICROGRAMMAR_POLICY_REF = (
    "policy:cocolon.emlis.stage1.microgrammar"
    "@cocolon.emlis.stage1.microgrammar.v1"
)
CMEE_STAGE1_VALUE_PRINCIPLE_REFS = (
    ("V1", "policy:V1@cocolon.emlis.stage1.value_policy.v1"),
    ("V2", "policy:V2@cocolon.emlis.stage1.value_policy.v1"),
    ("V3", "policy:V3@cocolon.emlis.stage1.value_policy.v1"),
    ("V4", "policy:V4@cocolon.emlis.stage1.value_policy.v1"),
    ("V5", "policy:V5@cocolon.emlis.stage1.value_policy.v1"),
    ("V6", "policy:V6@cocolon.emlis.stage1.value_policy.v1"),
    ("V7", "policy:V7@cocolon.emlis.stage1.value_policy.v1"),
    ("V8", "policy:V8@cocolon.emlis.stage1.value_policy.v1"),
    ("V9", "policy:V9@cocolon.emlis.stage1.value_policy.v1"),
)


@dataclass(frozen=True, slots=True)
class ReceptionActMappingRow:
    reception_act: str
    eligible_mode_operator_pairs: Tuple[Tuple[SubjectiveMode, SubjectiveOperator], ...]
    affect_categories: Tuple[AffectCategory, ...]
    material_visible_value_codes: Tuple[str, ...]
    suppression_value_codes: Tuple[str, ...]
    object_contract: str


@dataclass(frozen=True, slots=True)
class ReceptionStanceMappingRow:
    stance: str
    eligible_stance_operators: Tuple[StanceOperator, ...]
    temperature_rule: str
    distance_policy_id: str
    distance_policy_ref: str


CMEE_STAGE1_RECEPTION_ACT_MAPPING_EXACT7 = (
    ReceptionActMappingRow(
        "stay_with_current_burden",
        (
            (SubjectiveMode.ATTENTION, SubjectiveOperator.ATTEND_TO),
            (SubjectiveMode.AFFECTIVE_RESPONSE, SubjectiveOperator.FEEL_TOWARD),
        ),
        (AffectCategory.CONCERN, AffectCategory.SADNESS),
        (),
        (),
        "burden_object_required",
    ),
    ReceptionActMappingRow(
        "honor_concrete_effort",
        (
            (SubjectiveMode.ATTENTION, SubjectiveOperator.ATTEND_TO),
            (
                SubjectiveMode.PERSONAL_APPRAISAL,
                SubjectiveOperator.APPRAISE_AS_MATERIAL,
            ),
            (SubjectiveMode.AFFECTIVE_RESPONSE, SubjectiveOperator.FEEL_TOWARD),
        ),
        (AffectCategory.RESPECT,),
        (),
        (),
        "concrete_effort_object_required",
    ),
    ReceptionActMappingRow(
        "protect_retained_intention",
        (
            (SubjectiveMode.ATTENTION, SubjectiveOperator.ATTEND_TO),
            (
                SubjectiveMode.VALUE_POSITION,
                SubjectiveOperator.PROTECT_VALUE_BOUNDARY,
            ),
            (
                SubjectiveMode.RELATIONAL_STANCE,
                SubjectiveOperator.TAKE_RELATIONAL_STANCE,
            ),
        ),
        (),
        ("V2", "V8"),
        (),
        "retained_intention_object_required",
    ),
    ReceptionActMappingRow(
        "recognize_lived_change",
        (
            (SubjectiveMode.ATTENTION, SubjectiveOperator.ATTEND_TO),
            (
                SubjectiveMode.PERSONAL_APPRAISAL,
                SubjectiveOperator.APPRAISE_AS_MATERIAL,
            ),
            (SubjectiveMode.AFFECTIVE_RESPONSE, SubjectiveOperator.FEEL_TOWARD),
        ),
        (AffectCategory.RELIEF, AffectCategory.JOY, AffectCategory.RESPECT),
        (),
        ("V4", "V5"),
        "lived_change_object_required",
    ),
    ReceptionActMappingRow(
        "hold_help_seeking",
        (
            (SubjectiveMode.ATTENTION, SubjectiveOperator.ATTEND_TO),
            (
                SubjectiveMode.RELATIONAL_STANCE,
                SubjectiveOperator.TAKE_RELATIONAL_STANCE,
            ),
            (SubjectiveMode.AFFECTIVE_RESPONSE, SubjectiveOperator.FEEL_TOWARD),
        ),
        (AffectCategory.CONCERN, AffectCategory.RESPECT),
        ("V8",),
        (),
        "help_seeking_object_required",
    ),
    ReceptionActMappingRow(
        "bounded_counter_self_denial",
        (
            (
                SubjectiveMode.BOUNDED_COUNTERPOSITION,
                SubjectiveOperator.COUNTER_SPECIFIC_PROMOTION,
            ),
            (
                SubjectiveMode.RELATIONAL_STANCE,
                SubjectiveOperator.TAKE_RELATIONAL_STANCE,
            ),
        ),
        (),
        ("V1", "V8"),
        (),
        "counterposition_target_and_input_evidence_required",
    ),
    ReceptionActMappingRow(
        "respect_words_placed",
        (
            (SubjectiveMode.ATTENTION, SubjectiveOperator.ATTEND_TO),
            (SubjectiveMode.AFFECTIVE_RESPONSE, SubjectiveOperator.FEEL_TOWARD),
        ),
        (AffectCategory.RESPECT,),
        (),
        (),
        "words_placed_object_required",
    ),
)


def _distance_policy_ref(policy_id: str) -> str:
    versionless = policy_id.removesuffix(".v1")
    return f"policy:{versionless}@{policy_id}"


CMEE_STAGE1_RECEPTION_STANCE_MAPPING_EXACT5 = (
    ReceptionStanceMappingRow(
        "quiet_presence",
        (StanceOperator.STAY_WITH_SPECIFIC_OBJECT,),
        "STANDARD",
        "cocolon.emlis.distance.quiet_near.v1",
        _distance_policy_ref("cocolon.emlis.distance.quiet_near.v1"),
    ),
    ReceptionStanceMappingRow(
        "warm_recognition",
        (
            StanceOperator.STAY_WITH_SPECIFIC_OBJECT,
            StanceOperator.WELCOME_BOUNDED_CHANGE,
        ),
        "STANDARD",
        "cocolon.emlis.distance.warm_near.v1",
        _distance_policy_ref("cocolon.emlis.distance.warm_near.v1"),
    ),
    ReceptionStanceMappingRow(
        "gentle_respect",
        (
            StanceOperator.STAY_WITH_SPECIFIC_OBJECT,
            StanceOperator.PROTECT_USER_AGENCY,
        ),
        "STANDARD",
        "cocolon.emlis.distance.gentle_respect.v1",
        _distance_policy_ref("cocolon.emlis.distance.gentle_respect.v1"),
    ),
    ReceptionStanceMappingRow(
        "protective_presence",
        (
            StanceOperator.STAY_WITH_SPECIFIC_OBJECT,
            StanceOperator.HOLD_UNFINISHED_OPEN,
            StanceOperator.PROTECT_USER_AGENCY,
        ),
        "ELEVATED_NON_SAFETY_IF_CLEAR_NON_SAFETY_ELSE_STANDARD",
        "cocolon.emlis.distance.protective_boundaried.v1",
        _distance_policy_ref("cocolon.emlis.distance.protective_boundaried.v1"),
    ),
    ReceptionStanceMappingRow(
        "bounded_disagreement",
        (StanceOperator.PROTECT_USER_AGENCY,),
        "ELEVATED_NON_SAFETY_IF_CLEAR_NON_SAFETY_ELSE_STANDARD",
        "cocolon.emlis.distance.explicit_boundaried.v1",
        _distance_policy_ref("cocolon.emlis.distance.explicit_boundaried.v1"),
    ),
)

CMEE_STAGE1_RECEPTION_ACT_STANCE_EXACT7 = (
    ("stay_with_current_burden", "quiet_presence"),
    ("honor_concrete_effort", "warm_recognition"),
    ("protect_retained_intention", "gentle_respect"),
    ("recognize_lived_change", "warm_recognition"),
    ("hold_help_seeking", "protective_presence"),
    ("bounded_counter_self_denial", "bounded_disagreement"),
    ("respect_words_placed", "gentle_respect"),
)
CMEE_STAGE1_RECEPTION_MOVE_ROLE_MAPPING = (
    ("stay_with_current_burden", ("felt_response",)),
    ("honor_concrete_effort", ("attention", "felt_response")),
    (
        "protect_retained_intention",
        ("attention", "significance", "felt_response"),
    ),
    ("recognize_lived_change", ("attention", "felt_response")),
    ("hold_help_seeking", ("felt_response",)),
    ("bounded_counter_self_denial", ("bounded_counterposition",)),
    ("respect_words_placed", ("felt_response",)),
)
CMEE_STAGE1_RECEPTION_SPEAKER_MAPPING_EXACT2 = (
    ("implicit_emlis", "speaker_marker_null_when_unambiguous"),
    ("explicit_emlis", "first_eligible_layer2_speaker_marker_emlis_exact1"),
)
CMEE_STAGE1_RECEPTION_REFERENCE_MAPPING_EXACT3 = (
    ("anaphoric_first", "unique_prior_object_required"),
    ("short_anchor_if_ambiguous", "short_anchor_exact0_or1"),
    (
        "explicit_emlis_counterposition",
        "explicit_emlis_and_counterposition_target_exact1",
    ),
)
CMEE_STAGE1_RECEPTION_SURFACE_STRATEGY_MAPPING_EXACT5 = (
    ("quiet_referent_first", "response_object_then_subjective_predicate"),
    ("emlis_attention_first", "optional_emlis_then_attention_then_object"),
    ("referent_significance_first", "response_object_then_appraisal"),
    ("felt_response_first", "optional_emlis_then_affect_then_object"),
    (
        "explicit_emlis_counterposition",
        "emlis_then_counterposition_then_target",
    ),
)
CMEE_STAGE1_RECEPTION_SAFETY_CODE_MAPPING_EXACT3 = (
    ("felt_state_is_real", "source_feeling_dismissal_or_negation_forbidden"),
    (
        "identity_claim_is_not_accepted",
        "identity_promotion_to_user_fact_forbidden",
    ),
    (
        "counterposition_requires_input_evidence",
        "counterposition_target_input_evidence_reachability_required",
    ),
)
CMEE_STAGE1_RECEPTION_FORBIDDEN_SURFACE_CODES_EXACT6 = (
    "generic_empathy_suffix",
    "second_observation_summary",
    "internal_policy_explanation",
    "full_source_quote_replay",
    "all_input_enumeration",
    "duplicate_reception_move",
)
CMEE_STAGE1_RECEPTION_DISTINCTNESS_FIELDS = (
    "observation_summary_repetition_allowed",
    "relation_reexplanation_allowed",
    "all_input_enumeration_allowed",
    "policy_explanation_allowed",
    "new_cause_allowed",
    "new_identity_claim_allowed",
    "advice_allowed",
    "question_allowed",
)
CMEE_STAGE1_SUBJECTIVE_FORBIDDEN_PROMOTIONS = (
    "generic-subjective-claim",
    "layer1-observation-restatement",
    "user-personality-target",
    "persistent-affect",
    "hidden-self-state",
    "autobiographical-memory",
    "cross-request-affect-carryover",
    "internal-policy-explanation",
)


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
class RealizationCandidateSet:
    """Bounded S8 surfaces for one immutable Stage 1 projection."""

    projection_ref: str
    candidates: Tuple[Tuple[RealizedSentenceUnit, ...], ...]


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
    RealizationCandidateSet: ("candidates",),
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


CMEE_STAGE1_RECEPTION_ASSET_MAPPING_DOCS_TUPLE = (
    ("mapping_version", CMEE_STAGE1_RECEPTION_ASSET_MAPPING_VERSION),
    (
        "value_policy",
        (
            ("policy_id", CMEE_STAGE1_VALUE_POLICY_ID),
            ("policy_ref", CMEE_STAGE1_VALUE_POLICY_REF),
            ("principle_refs", CMEE_STAGE1_VALUE_PRINCIPLE_REFS),
            ("default_visibility", "SUPPRESSION_ONLY"),
            ("visible_only_when", "MATERIAL_PROMOTION_RISK"),
        ),
    ),
    ("act_rows", CMEE_STAGE1_RECEPTION_ACT_MAPPING_EXACT7),
    ("move_role_rows", CMEE_STAGE1_RECEPTION_MOVE_ROLE_MAPPING),
    ("act_stance_rows", CMEE_STAGE1_RECEPTION_ACT_STANCE_EXACT7),
    ("stance_rows", CMEE_STAGE1_RECEPTION_STANCE_MAPPING_EXACT5),
    ("speaker_rows", CMEE_STAGE1_RECEPTION_SPEAKER_MAPPING_EXACT2),
    ("reference_rows", CMEE_STAGE1_RECEPTION_REFERENCE_MAPPING_EXACT3),
    (
        "surface_strategy_rows",
        CMEE_STAGE1_RECEPTION_SURFACE_STRATEGY_MAPPING_EXACT5,
    ),
    (
        "quote_policy",
        (
            ("mode", "no_full_quote_replay"),
            ("max_anchor_count", 1),
            ("max_anchor_visible_chars", 16),
        ),
    ),
    (
        "distinctness_exact8_false",
        CMEE_STAGE1_RECEPTION_DISTINCTNESS_FIELDS,
    ),
    ("safety_rows", CMEE_STAGE1_RECEPTION_SAFETY_CODE_MAPPING_EXACT3),
    (
        "forbidden_surface_codes",
        CMEE_STAGE1_RECEPTION_FORBIDDEN_SURFACE_CODES_EXACT6,
    ),
    (
        "discomfort",
        (
            ("generated_by_current_mapping", False),
            (
                "allowed_target_kinds",
                ("event", "source_explicit_value_conflict", "promotion_risk"),
            ),
            ("forbidden_target_kinds", ("user", "personality", "attribute")),
        ),
    ),
)
CMEE_STAGE1_RECEPTION_ASSET_MAPPING_DOCS_BYTES = stage1_canonical_json_bytes(
    CMEE_STAGE1_RECEPTION_ASSET_MAPPING_DOCS_TUPLE
)
CMEE_STAGE1_RECEPTION_ASSET_MAPPING_DOCS_SHA256 = hashlib.sha256(
    CMEE_STAGE1_RECEPTION_ASSET_MAPPING_DOCS_BYTES
).hexdigest()


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


def stage1_projection_artifact_ref(projection: EmlisStage1Projection) -> str:
    """Return the versioned identity seam used by the later artifact cutover."""

    if type(projection) is not EmlisStage1Projection:
        raise CMEEStage1ContractError("stage1_projection_type_invalid")
    validate_stage1_identity(projection)
    return (
        f"projection:{projection.projection_id}"
        f"@{CMEE_STAGE1_RESPONSE_SCHEMA_VERSION}"
    )


def validate_stage1_projection_artifact_ref(value: str) -> None:
    validate_version_qualified_ref(value, expected_types=("projection",))
    match = _VERSION_QUALIFIED_REF_RE.fullmatch(value)
    if (
        match is None
        or match.group("version") != CMEE_STAGE1_RESPONSE_SCHEMA_VERSION
        or re.fullmatch(r"projection-[0-9a-f]{64}", match.group("ref_id"))
        is None
    ):
        raise CMEEStage1ContractError(
            "stage1_projection_artifact_ref_invalid"
        )


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


def _stage1_ref_parts(
    value: str,
    *,
    expected_types: Sequence[str],
    expected_version: str,
) -> tuple[str, str]:
    validate_version_qualified_ref(value, expected_types=expected_types)
    match = _VERSION_QUALIFIED_REF_RE.fullmatch(value)
    if match is None:
        raise CMEEStage1ContractError("stage1_external_ref_not_version_qualified")
    if match.group("version") != expected_version:
        raise CMEEStage1ContractError("stage1_external_ref_version_mismatch")
    return match.group("ref_type"), match.group("ref_id")


def _stage1_graph_universe(
    projection: EmlisStage1Projection,
    grounded_graph: GroundedMeaningGraph,
) -> tuple[set[str], set[str], set[str]]:
    if type(grounded_graph) is not GroundedMeaningGraph:
        raise CMEEStage1ContractError("stage1_grounded_graph_required")
    graph_type, graph_id = _stage1_ref_parts(
        projection.grounded_graph_ref,
        expected_types=("grounded",),
        expected_version=CMEE_GROUNDED_GRAPH_SCHEMA_VERSION,
    )
    if graph_type != "grounded" or graph_id != grounded_graph.graph_id:
        raise CMEEStage1ContractError("stage1_grounded_graph_ref_mismatch")
    node_ids = {row.node_id for row in grounded_graph.nodes}
    edge_ids = {row.edge_id for row in grounded_graph.edges}
    if (
        len(node_ids) != len(grounded_graph.nodes)
        or len(edge_ids) != len(grounded_graph.edges)
        or node_ids & edge_ids
    ):
        raise CMEEStage1ContractError("stage1_grounded_graph_identity_invalid")
    evidence_ids = {
        evidence_id
        for row in (*grounded_graph.nodes, *grounded_graph.edges)
        for evidence_id in row.evidence_ids
    }
    return node_ids, edge_ids, evidence_ids


def _validate_stage1_semantic_refs(
    values: Sequence[str],
    *,
    node_ids: set[str],
    edge_ids: set[str],
) -> None:
    for ref in values:
        ref_type, ref_id = _stage1_ref_parts(
            ref,
            expected_types=("node", "edge"),
            expected_version=CMEE_GROUNDED_GRAPH_SCHEMA_VERSION,
        )
        allowed = node_ids if ref_type == "node" else edge_ids
        if ref_id not in allowed:
            raise CMEEStage1ContractError("stage1_semantic_ref_missing")


def _validate_stage1_evidence_refs(
    values: Sequence[str],
    *,
    evidence_ids: set[str],
    source_version: str,
) -> None:
    for ref in values:
        _ref_type, ref_id = _stage1_ref_parts(
            ref,
            expected_types=("evidence",),
            expected_version=source_version,
        )
        if ref_id not in evidence_ids:
            raise CMEEStage1ContractError("stage1_evidence_ref_missing")


_STAGE1_INTERPRETATION_CANDIDATE_KIND_CAP = 2
_STAGE1_LAYER1_OBSERVATION_CAP = 5
_STAGE2_OBSERVATION_SEMANTIC_KEY_VERSION = (
    "cocolon.cmee.v1a.emlis_stage1.observation_semantic_key.v1"
)
_STAGE1_MEANING_SLOT_ORDER = (
    MeaningFieldSlot.CENTER,
    MeaningFieldSlot.TENSION,
    MeaningFieldSlot.COEXISTENCE,
    MeaningFieldSlot.CHANGE,
    MeaningFieldSlot.TIME_RELATION,
    MeaningFieldSlot.DIRECTION,
    MeaningFieldSlot.BURDEN,
    MeaningFieldSlot.OUTPUT,
    MeaningFieldSlot.RESIDUE,
    MeaningFieldSlot.UNFINISHED,
)
_STAGE1_DIRECTION_NODE_KINDS = frozenset(
    {"wish", "direction", "desire", "intention", "goal", "help_seeking"}
)
_STAGE1_CORE_BURDEN_NODE_KINDS = frozenset(
    {"constraint", "burden", "fatigue", "anxiety", "hesitation", "block"}
)
_STAGE1_BURDEN_NODE_KINDS = frozenset(
    {
        *_STAGE1_CORE_BURDEN_NODE_KINDS,
        # The canonical grounded planner can type a source reaction as burden
        # from its finite semantic-frame codes.  This metadata-derived case
        # must remain sealed by a retained direct burden shape.
        "reaction",
    }
)
_STAGE1_ACTION_NODE_KINDS = frozenset({"action", "attempt"})
_STAGE1_CHANGE_NODE_KINDS = frozenset({"change", "bounded_change"})
_STAGE1_EVENT_NODE_KINDS = frozenset({"event", "action", "change"})
_STAGE1_RESIDUE_NODE_KINDS = frozenset(
    {"reaction", "residue", "lingering_state", "unfinished", "uncertainty"}
)
_STAGE1_DIRECTION_DIRECT_SHAPE = (
    InterpretationKind.DIRECT_DIRECTION,
    SemanticOperator.PRESENT_DIRECTION,
)
_STAGE1_BURDEN_DIRECT_SHAPE = (
    InterpretationKind.DIRECT_STATE,
    SemanticOperator.PRESENT_BURDEN,
)
_STAGE1_ACTION_DIRECT_SHAPE = (
    InterpretationKind.DIRECT_STATE,
    SemanticOperator.PRESENT_ACTUAL_OUTPUT,
)
_STAGE1_CHANGE_DIRECT_SHAPE = (
    InterpretationKind.DIRECT_STATE,
    SemanticOperator.PRESENT_CHANGE,
)
_STAGE1_STATE_DIRECT_SHAPE = (
    InterpretationKind.DIRECT_STATE,
    SemanticOperator.PRESENT_STATE,
)
_STAGE1_UNFINISHED_DIRECT_SHAPE = (
    InterpretationKind.UNFINISHED,
    SemanticOperator.PRESENT_UNFINISHED,
)

# Keep the projection validator closed over the same exact-thirteen public
# contract as the Step 2 builder.  The builder is layered on this module, so
# importing its table here would introduce a circular dependency.
_STAGE1_INTERPRETATION_MATRIX_EXACT13 = (
    (InterpretationKind.DIRECT_STATE, SemanticOperator.PRESENT_STATE, RelationOperator.NO_RELATION_CLAIM, (ArgumentRole.PRIMARY,)),
    (InterpretationKind.DIRECT_STATE, SemanticOperator.PRESENT_BURDEN, RelationOperator.NO_RELATION_CLAIM, (ArgumentRole.PRIMARY,)),
    (InterpretationKind.DIRECT_STATE, SemanticOperator.PRESENT_CHANGE, RelationOperator.NO_RELATION_CLAIM, (ArgumentRole.PRIMARY,)),
    (InterpretationKind.DIRECT_STATE, SemanticOperator.PRESENT_ACTUAL_OUTPUT, RelationOperator.NO_RELATION_CLAIM, (ArgumentRole.PRIMARY,)),
    (InterpretationKind.DIRECT_DIRECTION, SemanticOperator.PRESENT_DIRECTION, RelationOperator.NO_RELATION_CLAIM, (ArgumentRole.PRIMARY,)),
    (InterpretationKind.COEXISTENCE, SemanticOperator.SYNTHESIZE_RELATION, RelationOperator.COEXISTS_WITH, (ArgumentRole.LEFT, ArgumentRole.RIGHT)),
    (InterpretationKind.TENSION, SemanticOperator.SYNTHESIZE_RELATION, RelationOperator.TENSION_WITH, (ArgumentRole.LEFT, ArgumentRole.RIGHT)),
    (InterpretationKind.DIRECTION_UNDER_BURDEN, SemanticOperator.SYNTHESIZE_RELATION, RelationOperator.COEXISTS_WITH, (ArgumentRole.LEFT, ArgumentRole.RIGHT)),
    (InterpretationKind.DIRECTION_UNDER_BURDEN, SemanticOperator.SYNTHESIZE_RELATION, RelationOperator.TENSION_WITH, (ArgumentRole.LEFT, ArgumentRole.RIGHT)),
    (InterpretationKind.ACTION_THEN_CHANGE_ONCE, SemanticOperator.PRESENT_CHANGE, RelationOperator.ACTION_PRECEDES_CHANGE, (ArgumentRole.ACTION, ArgumentRole.CHANGE)),
    (InterpretationKind.RESIDUE_AFTER_EVENT, SemanticOperator.PRESENT_RESIDUE, RelationOperator.TEMPORALLY_PRECEDES, (ArgumentRole.BEFORE, ArgumentRole.AFTER)),
    (InterpretationKind.SOURCE_STATED_CAUSE, SemanticOperator.SYNTHESIZE_RELATION, RelationOperator.SOURCE_EXPLICIT_CAUSE, (ArgumentRole.CAUSE, ArgumentRole.EFFECT)),
    (InterpretationKind.UNFINISHED, SemanticOperator.PRESENT_UNFINISHED, RelationOperator.NO_RELATION_CLAIM, (ArgumentRole.PRIMARY,)),
)


def _stage1_ordered_unique(values: Sequence[str]) -> tuple[str, ...]:
    return tuple(dict.fromkeys(values))


def stage1_value_principle_ref(code: str) -> str:
    for registered_code, ref in CMEE_STAGE1_VALUE_PRINCIPLE_REFS:
        if code == registered_code:
            return ref
    raise CMEEStage1ContractError("stage1_value_principle_unknown")


def _stage1_suppression_value_codes(
    contributions: Sequence[PlannedObservationContribution],
    *,
    material_unknown_refs: Sequence[str] = (),
) -> tuple[str, ...]:
    rows = tuple(contributions)
    codes: list[str] = []
    if any(
        row.semantic_operator
        in {SemanticOperator.PRESENT_BURDEN, SemanticOperator.PRESENT_RESIDUE}
        or row.contribution_kind
        in {
            ObservationContributionKind.OBSERVE_BURDEN,
            ObservationContributionKind.PRESERVE_RESIDUE,
        }
        for row in rows
    ):
        codes.append("V1")
    if any(row.semantic_operator is SemanticOperator.PRESENT_DIRECTION for row in rows):
        codes.extend(("V2", "V8"))
    if any(
        row.semantic_operator
        in {
            SemanticOperator.PRESENT_CHANGE,
            SemanticOperator.PRESENT_ACTUAL_OUTPUT,
        }
        for row in rows
    ):
        codes.extend(("V4", "V5"))
    if any(
        row.relation_operator
        in {RelationOperator.COEXISTS_WITH, RelationOperator.TENSION_WITH}
        for row in rows
    ):
        codes.append("V6")
    if any(
        row.semantic_operator is SemanticOperator.PRESENT_UNFINISHED
        or row.contribution_kind
        is ObservationContributionKind.PRESERVE_UNFINISHED
        for row in rows
    ):
        codes.extend(("V3", "V7", "V9"))
    if material_unknown_refs:
        codes.append("V9")
    ordered_codes = tuple(code for code, _ref in CMEE_STAGE1_VALUE_PRINCIPLE_REFS)
    selected = set(codes)
    return tuple(code for code in ordered_codes if code in selected)


def stage1_subjective_forbidden_promotions(
    contributions: Sequence[PlannedObservationContribution],
    *,
    material_unknown_refs: tuple[str, ...] = (),
) -> tuple[str, ...]:
    if not contributions or any(
        type(row) is not PlannedObservationContribution for row in contributions
    ):
        raise CMEEStage1ContractError(
            "stage1_subjective_basis_contribution_invalid"
        )
    if (
        type(material_unknown_refs) is not tuple
        or any(type(ref) is not str or not ref for ref in material_unknown_refs)
        or len(material_unknown_refs) != len(set(material_unknown_refs))
    ):
        raise CMEEStage1ContractError(
            "stage1_subjective_material_unknown_ref_invalid"
        )
    return (
        *CMEE_STAGE1_SUBJECTIVE_FORBIDDEN_PROMOTIONS,
        *(
            f"value-policy-suppression:{code}"
            for code in _stage1_suppression_value_codes(
                contributions,
                material_unknown_refs=material_unknown_refs,
            )
        ),
    )


def stage1_subjective_semantic_key(claim: EmlisSubjectiveClaim) -> str:
    if type(claim) is not EmlisSubjectiveClaim:
        raise CMEEStage1ContractError("stage1_subjective_type_invalid")
    material = {
        "asserted_subjective_proposition": claim.asserted_subjective_proposition,
        "value_principle_refs": claim.value_principle_refs,
    }
    digest = hashlib.sha256(stage1_canonical_json_bytes(material)).hexdigest()
    return f"subjective-key-{digest}"


def _validate_stage1_interpretation_matrix(
    candidate: EmlisInterpretationCandidate,
) -> None:
    matches = tuple(
        row
        for row in _STAGE1_INTERPRETATION_MATRIX_EXACT13
        if row[:3]
        == (
            candidate.candidate_kind,
            candidate.semantic_operator,
            candidate.relation_operator,
        )
    )
    if len(matches) != 1:
        raise CMEEStage1ContractError("stage1_interpretation_matrix_invalid")
    required_roles = matches[0][3]
    actual_roles = tuple(row.role for row in candidate.argument_bindings)
    if actual_roles not in {
        required_roles,
        (*required_roles, ArgumentRole.EXPERIENCER),
    }:
        raise CMEEStage1ContractError("stage1_interpretation_matrix_invalid")
    if (
        actual_roles != required_roles
        and candidate.relation_operator is not RelationOperator.NO_RELATION_CLAIM
    ):
        raise CMEEStage1ContractError("stage1_interpretation_matrix_invalid")
    if candidate.relation_operator is RelationOperator.NO_RELATION_CLAIM:
        if candidate.relation_basis_refs:
            raise CMEEStage1ContractError("stage1_interpretation_matrix_invalid")
    elif len(candidate.relation_basis_refs) != 1:
        raise CMEEStage1ContractError("stage1_interpretation_matrix_invalid")


def _stage1_node_ref(node_id: str) -> str:
    return f"node:{node_id}@{CMEE_GROUNDED_GRAPH_SCHEMA_VERSION}"


def _stage1_allowed_direct_shapes(
    node: MeaningNode,
) -> frozenset[tuple[InterpretationKind, SemanticOperator]]:
    kind = str(node.node_kind).lower()
    if kind in _STAGE1_DIRECTION_NODE_KINDS:
        return frozenset({_STAGE1_DIRECTION_DIRECT_SHAPE})
    if kind in {
        "constraint",
        "burden",
        "fatigue",
        "anxiety",
        "hesitation",
        "block",
    }:
        return frozenset({_STAGE1_BURDEN_DIRECT_SHAPE})
    if kind in _STAGE1_ACTION_NODE_KINDS:
        return frozenset({_STAGE1_ACTION_DIRECT_SHAPE})
    if kind in _STAGE1_CHANGE_NODE_KINDS:
        return frozenset({_STAGE1_CHANGE_DIRECT_SHAPE})
    if kind in {"uncertainty", "unfinished", "open_question"}:
        return frozenset({_STAGE1_UNFINISHED_DIRECT_SHAPE})
    if kind == "state":
        # Canonical semantic-frame metadata can refine a state nucleus into a
        # burden without changing the compact graph node kind.
        return frozenset(
            {_STAGE1_STATE_DIRECT_SHAPE, _STAGE1_BURDEN_DIRECT_SHAPE}
        )
    if kind == "reaction":
        # Exact8 contains source-grounded reaction nuclei refined to state,
        # burden, or bounded change by the canonical grounded plan.
        return frozenset(
            {
                _STAGE1_STATE_DIRECT_SHAPE,
                _STAGE1_BURDEN_DIRECT_SHAPE,
                _STAGE1_CHANGE_DIRECT_SHAPE,
            }
        )
    return frozenset({_STAGE1_STATE_DIRECT_SHAPE})


def _validate_stage1_relation_binding(
    candidate: EmlisInterpretationCandidate,
    *,
    edge_by_id: Mapping[str, MeaningEdge],
    node_by_id: Mapping[str, MeaningNode],
    direct_shapes_by_node_ref: Mapping[
        str,
        frozenset[tuple[InterpretationKind, SemanticOperator]],
    ],
) -> None:
    if candidate.relation_operator is RelationOperator.NO_RELATION_CLAIM:
        return
    _ref_type, edge_id = _stage1_ref_parts(
        candidate.relation_basis_refs[0],
        expected_types=("edge",),
        expected_version=CMEE_GROUNDED_GRAPH_SCHEMA_VERSION,
    )
    edge = edge_by_id[edge_id]
    if (
        edge.source_node_id == edge.target_node_id
        or edge.source_node_id not in node_by_id
        or edge.target_node_id not in node_by_id
    ):
        raise CMEEStage1ContractError("stage1_candidate_relation_binding_invalid")
    source_ref = _stage1_node_ref(edge.source_node_id)
    target_ref = _stage1_node_ref(edge.target_node_id)
    source_kind = str(node_by_id[edge.source_node_id].node_kind).lower()
    target_kind = str(node_by_id[edge.target_node_id].node_kind).lower()
    source_direct_shapes = direct_shapes_by_node_ref.get(source_ref, frozenset())
    target_direct_shapes = direct_shapes_by_node_ref.get(target_ref, frozenset())
    relation = str(edge.relation).lower()
    expected_relation: Optional[set[str]] = None
    expected_bindings: tuple[ArgumentBinding, ...]
    if candidate.candidate_kind is InterpretationKind.COEXISTENCE:
        expected_relation = {"coexistence"}
        left, right = sorted((source_ref, target_ref))
        expected_bindings = (
            ArgumentBinding(ArgumentRole.LEFT, left),
            ArgumentBinding(ArgumentRole.RIGHT, right),
        )
    elif candidate.candidate_kind is InterpretationKind.TENSION:
        expected_relation = {"contrast"}
        left, right = sorted((source_ref, target_ref))
        expected_bindings = (
            ArgumentBinding(ArgumentRole.LEFT, left),
            ArgumentBinding(ArgumentRole.RIGHT, right),
        )
    elif candidate.candidate_kind is InterpretationKind.DIRECTION_UNDER_BURDEN:
        source_shape_valid = (
            _STAGE1_DIRECTION_DIRECT_SHAPE in source_direct_shapes
            if source_direct_shapes
            else source_kind in _STAGE1_DIRECTION_NODE_KINDS
        )
        target_shape_valid = (
            _STAGE1_BURDEN_DIRECT_SHAPE in target_direct_shapes
            if target_direct_shapes
            else target_kind in _STAGE1_BURDEN_NODE_KINDS
        )
        if (
            source_kind not in _STAGE1_DIRECTION_NODE_KINDS
            or target_kind not in _STAGE1_BURDEN_NODE_KINDS
            or not source_shape_valid
            or not target_shape_valid
        ):
            raise CMEEStage1ContractError(
                "stage1_candidate_relation_binding_invalid"
            )
        expected_relation = (
            {"wish_and_constraint"}
            if candidate.relation_operator is RelationOperator.COEXISTS_WITH
            else {"preserves_despite", "attempt_and_block"}
        )
        expected_bindings = (
            ArgumentBinding(ArgumentRole.LEFT, source_ref),
            ArgumentBinding(ArgumentRole.RIGHT, target_ref),
        )
    elif candidate.candidate_kind is InterpretationKind.ACTION_THEN_CHANGE_ONCE:
        source_shape_valid = (
            _STAGE1_ACTION_DIRECT_SHAPE in source_direct_shapes
            if source_direct_shapes
            else source_kind in _STAGE1_ACTION_NODE_KINDS
        )
        target_shape_valid = (
            _STAGE1_CHANGE_DIRECT_SHAPE in target_direct_shapes
            if target_direct_shapes
            else target_kind in _STAGE1_CHANGE_NODE_KINDS
        )
        if (
            source_kind not in _STAGE1_ACTION_NODE_KINDS
            or target_kind not in _STAGE1_CHANGE_NODE_KINDS
            or not source_shape_valid
            or not target_shape_valid
        ):
            raise CMEEStage1ContractError(
                "stage1_candidate_relation_binding_invalid"
            )
        expected_relation = {"action_supports_change"}
        expected_bindings = (
            ArgumentBinding(ArgumentRole.ACTION, source_ref),
            ArgumentBinding(ArgumentRole.CHANGE, target_ref),
        )
    elif candidate.candidate_kind is InterpretationKind.RESIDUE_AFTER_EVENT:
        source_shape_valid = (
            bool(
                source_direct_shapes.intersection(
                    {
                        _STAGE1_STATE_DIRECT_SHAPE,
                        _STAGE1_ACTION_DIRECT_SHAPE,
                        _STAGE1_CHANGE_DIRECT_SHAPE,
                    }
                )
            )
            if source_direct_shapes
            else source_kind in _STAGE1_EVENT_NODE_KINDS
        )
        target_shape_valid = (
            bool(
                target_direct_shapes.intersection(
                    {
                        _STAGE1_STATE_DIRECT_SHAPE,
                        _STAGE1_BURDEN_DIRECT_SHAPE,
                        _STAGE1_CHANGE_DIRECT_SHAPE,
                        _STAGE1_UNFINISHED_DIRECT_SHAPE,
                    }
                )
            )
            if target_direct_shapes
            else target_kind in _STAGE1_RESIDUE_NODE_KINDS
        )
        if (
            source_kind not in _STAGE1_EVENT_NODE_KINDS
            or target_kind not in _STAGE1_RESIDUE_NODE_KINDS
            or not source_shape_valid
            or not target_shape_valid
        ):
            raise CMEEStage1ContractError(
                "stage1_candidate_relation_binding_invalid"
            )
        expected_relation = {"temporal_before_after", "shift_from_to"}
        expected_bindings = (
            ArgumentBinding(ArgumentRole.BEFORE, source_ref),
            ArgumentBinding(ArgumentRole.AFTER, target_ref),
        )
    elif candidate.candidate_kind is InterpretationKind.SOURCE_STATED_CAUSE:
        expected_relation = {"user_stated_cause"}
        expected_bindings = (
            ArgumentBinding(ArgumentRole.CAUSE, source_ref),
            ArgumentBinding(ArgumentRole.EFFECT, target_ref),
        )
    else:
        raise CMEEStage1ContractError("stage1_candidate_relation_binding_invalid")
    if relation not in expected_relation or candidate.argument_bindings != expected_bindings:
        raise CMEEStage1ContractError("stage1_candidate_relation_binding_invalid")


def _stage1_contribution_kind_for_candidate(
    candidate: EmlisInterpretationCandidate,
) -> ObservationContributionKind:
    slot = _stage1_meaning_field_slot_for_candidate(candidate)
    mapping = {
        MeaningFieldSlot.CENTER: ObservationContributionKind.OBSERVE_CENTER,
        MeaningFieldSlot.COEXISTENCE: ObservationContributionKind.OBSERVE_COEXISTENCE,
        MeaningFieldSlot.TENSION: ObservationContributionKind.OBSERVE_TENSION,
        MeaningFieldSlot.DIRECTION: ObservationContributionKind.OBSERVE_DIRECTION,
        MeaningFieldSlot.BURDEN: ObservationContributionKind.OBSERVE_BURDEN,
        MeaningFieldSlot.CHANGE: (
            ObservationContributionKind.OBSERVE_ACTION_THEN_CHANGE
            if candidate.candidate_kind
            is InterpretationKind.ACTION_THEN_CHANGE_ONCE
            else ObservationContributionKind.OBSERVE_CHANGE
        ),
        MeaningFieldSlot.OUTPUT: ObservationContributionKind.OBSERVE_ACTUAL_OUTPUT,
        MeaningFieldSlot.TIME_RELATION: ObservationContributionKind.OBSERVE_TIME_RELATION,
        MeaningFieldSlot.RESIDUE: ObservationContributionKind.PRESERVE_RESIDUE,
        MeaningFieldSlot.UNFINISHED: ObservationContributionKind.PRESERVE_UNFINISHED,
    }
    try:
        return mapping[slot]
    except KeyError:
        raise CMEEStage1ContractError(
            "stage1_observation_slot_mapping_invalid"
        ) from None


def _stage1_meaning_field_slot_for_candidate(
    candidate: EmlisInterpretationCandidate,
) -> MeaningFieldSlot:
    if candidate.candidate_kind is InterpretationKind.DIRECT_DIRECTION:
        return MeaningFieldSlot.DIRECTION
    if candidate.candidate_kind is InterpretationKind.UNFINISHED:
        return MeaningFieldSlot.UNFINISHED
    if candidate.candidate_kind is InterpretationKind.COEXISTENCE:
        return MeaningFieldSlot.COEXISTENCE
    if candidate.candidate_kind in {
        InterpretationKind.TENSION,
        InterpretationKind.DIRECTION_UNDER_BURDEN,
    }:
        return (
            MeaningFieldSlot.COEXISTENCE
            if candidate.relation_operator is RelationOperator.COEXISTS_WITH
            else MeaningFieldSlot.TENSION
        )
    if candidate.candidate_kind is InterpretationKind.ACTION_THEN_CHANGE_ONCE:
        return MeaningFieldSlot.CHANGE
    if candidate.candidate_kind is InterpretationKind.RESIDUE_AFTER_EVENT:
        return MeaningFieldSlot.RESIDUE
    if candidate.candidate_kind is InterpretationKind.SOURCE_STATED_CAUSE:
        return MeaningFieldSlot.TIME_RELATION
    direct_mapping = {
        SemanticOperator.PRESENT_BURDEN: MeaningFieldSlot.BURDEN,
        SemanticOperator.PRESENT_CHANGE: MeaningFieldSlot.CHANGE,
        SemanticOperator.PRESENT_ACTUAL_OUTPUT: MeaningFieldSlot.OUTPUT,
    }
    return direct_mapping.get(
        candidate.semantic_operator,
        MeaningFieldSlot.CENTER,
    )


def _stage2_observation_semantic_key(
    candidate: EmlisInterpretationCandidate,
) -> str:
    material = {
        "semantic_key_version": _STAGE2_OBSERVATION_SEMANTIC_KEY_VERSION,
        "claim_domain": candidate.claim_domain,
        "semantic_operator": candidate.semantic_operator,
        "argument_bindings": candidate.argument_bindings,
        "relation_operator": candidate.relation_operator,
        "relation_basis_refs": candidate.relation_basis_refs,
        "required_qualifiers": candidate.required_qualifiers,
    }
    digest = hashlib.sha256(stage1_canonical_json_bytes(material)).hexdigest()
    return f"observation-key-{digest}"


def _stage1_grounded_evidence_for_refs(
    semantic_refs: Sequence[str],
    relation_basis_refs: Sequence[str],
    *,
    node_by_id: Mapping[str, MeaningNode],
    edge_by_id: Mapping[str, MeaningEdge],
) -> tuple[str, ...]:
    evidence: list[str] = []
    for ref in (*semantic_refs, *relation_basis_refs):
        ref_type, ref_id = _stage1_ref_parts(
            ref,
            expected_types=("node", "edge"),
            expected_version=CMEE_GROUNDED_GRAPH_SCHEMA_VERSION,
        )
        grounded_row = (
            node_by_id[ref_id] if ref_type == "node" else edge_by_id[ref_id]
        )
        grounding_kind = str(grounded_row.grounding_kind).lower()
        admitted_grounding = (
            {"explicit", "user_stated_relation"}
            if ref_type == "node"
            else {"user_stated_relation"}
        )
        if (
            grounded_row.epistemic_state is not EpistemicState.SOURCE_EXPLICIT
            or not grounded_row.evidence_ids
            or len(grounded_row.evidence_ids) != len(set(grounded_row.evidence_ids))
            or grounding_kind not in admitted_grounding
        ):
            raise CMEEStage1ContractError(
                "stage1_candidate_source_evidence_unreachable"
            )
        evidence.extend(grounded_row.evidence_ids)
    return _stage1_ordered_unique(evidence)


def _stage1_expected_material_unknown_refs(
    grounded_graph: GroundedMeaningGraph,
    parent_plan: ExperiencePlan,
) -> tuple[str, ...]:
    unknown_owners = tuple(parent_plan.visible_unknown_owner_ids)
    if (
        any(type(row) is not str or not row for row in unknown_owners)
        or len(unknown_owners) != len(set(unknown_owners))
        or not set(parent_plan.required_unknown_owner_ids).issubset(
            set(unknown_owners)
        )
        or not set(unknown_owners).issubset(
            set(parent_plan.unresolved_owner_ids)
        )
    ):
        raise CMEEStage1ContractError("stage1_material_unknown_owner_invalid")
    disposition_by_owner = {
        row.meaning_owner_id: row for row in grounded_graph.owner_dispositions
    }
    if len(disposition_by_owner) != len(grounded_graph.owner_dispositions):
        raise CMEEStage1ContractError("stage1_owner_disposition_duplicate")
    node_by_id = {row.node_id: row for row in grounded_graph.nodes}
    refs: list[str] = []
    for owner_id in unknown_owners:
        disposition = disposition_by_owner.get(owner_id)
        target = (
            disposition.target_unknown_ref if disposition is not None else None
        )
        node = node_by_id.get(str(target or ""))
        if (
            disposition is None
            or disposition.route_b_disposition
            is not RouteBDisposition.UNKNOWN_PRESERVED_LIMITED
            or type(target) is not str
            or not target
            or disposition.visible_claim_refs != (target,)
            or node is None
            or node.owner_id != owner_id
            or node.epistemic_state is not EpistemicState.UNKNOWN
            or str(node.grounding_kind).lower()
            != "unresolved_attachment_relation"
            or not node.evidence_ids
            or len(node.evidence_ids) != len(set(node.evidence_ids))
            or tuple(node.evidence_ids) != tuple(disposition.evidence_refs)
        ):
            raise CMEEStage1ContractError("stage1_material_unknown_unreachable")
        refs.append(f"unknown:{target}@{grounded_graph.obligation_version}")
    return tuple(refs)


def _stage1_reception_act_row(value: str) -> ReceptionActMappingRow:
    rows = tuple(
        row
        for row in CMEE_STAGE1_RECEPTION_ACT_MAPPING_EXACT7
        if row.reception_act == value
    )
    if len(rows) != 1:
        raise CMEEStage1ContractError("stage1_reception_act_unregistered")
    return rows[0]


def _stage1_reception_stance_row(value: str) -> ReceptionStanceMappingRow:
    rows = tuple(
        row
        for row in CMEE_STAGE1_RECEPTION_STANCE_MAPPING_EXACT5
        if row.stance == value
    )
    if len(rows) != 1:
        raise CMEEStage1ContractError("stage1_reception_stance_unregistered")
    return rows[0]


def _stage1_stance_for_act(value: str) -> str:
    rows = tuple(
        stance
        for act, stance in CMEE_STAGE1_RECEPTION_ACT_STANCE_EXACT7
        if act == value
    )
    if len(rows) != 1:
        raise CMEEStage1ContractError("stage1_reception_act_unregistered")
    return rows[0]


def _stage1_basis_semantic_refs(
    contributions: Sequence[PlannedObservationContribution],
) -> tuple[str, ...]:
    return _stage1_ordered_unique(
        tuple(
            ref
            for contribution in contributions
            for ref in (
                *contribution.semantic_refs,
                *contribution.relation_basis_refs,
            )
        )
    )


def _stage1_material_visible_value_refs(
    *,
    reception_act: str,
    contributions: Sequence[PlannedObservationContribution],
) -> tuple[str, ...]:
    row = _stage1_reception_act_row(reception_act)
    allowed_codes = set(row.material_visible_value_codes)
    if not allowed_codes:
        return ()
    if reception_act == "bounded_counter_self_denial":
        material_codes = {"V1", "V8"}
    elif reception_act == "protect_retained_intention":
        has_direction = any(
            contribution.semantic_operator is SemanticOperator.PRESENT_DIRECTION
            for contribution in contributions
        )
        has_burden_or_tension = any(
            contribution.semantic_operator is SemanticOperator.PRESENT_BURDEN
            or contribution.relation_operator
            in {RelationOperator.COEXISTS_WITH, RelationOperator.TENSION_WITH}
            for contribution in contributions
        )
        material_codes = {"V2", "V8"} if has_direction and has_burden_or_tension else set()
    elif reception_act == "hold_help_seeking":
        material_codes = (
            {"V8"}
            if any(
                contribution.retention == "REQUIRED"
                and contribution.semantic_operator
                is SemanticOperator.PRESENT_ACTUAL_OUTPUT
                for contribution in contributions
            )
            else set()
        )
    else:
        material_codes = set()
    return tuple(
        ref
        for code, ref in CMEE_STAGE1_VALUE_PRINCIPLE_REFS
        if code in allowed_codes & material_codes
    )


def _stage1_discomfort_target_is_allowed(
    ref: str,
    *,
    contribution_by_id: Mapping[str, PlannedObservationContribution],
    node_by_id: Mapping[str, MeaningNode],
    edge_by_id: Mapping[str, MeaningEdge],
) -> bool:
    if ref in contribution_by_id:
        contribution = contribution_by_id[ref]
        if contribution.semantic_operator in {
            SemanticOperator.PRESENT_CHANGE,
            SemanticOperator.PRESENT_ACTUAL_OUTPUT,
        }:
            return bool(contribution.evidence_refs)
        if (
            contribution.relation_operator is RelationOperator.TENSION_WITH
            and contribution.relation_basis_refs
        ):
            return all(
                _stage1_discomfort_target_is_allowed(
                    relation_ref,
                    contribution_by_id={},
                    node_by_id=node_by_id,
                    edge_by_id=edge_by_id,
                )
                for relation_ref in contribution.relation_basis_refs
            )
        return any(
            _stage1_discomfort_target_is_allowed(
                semantic_ref,
                contribution_by_id={},
                node_by_id=node_by_id,
                edge_by_id=edge_by_id,
            )
            for semantic_ref in contribution.semantic_refs
        )
    ref_type, ref_id = _stage1_ref_parts(
        ref,
        expected_types=("node", "edge"),
        expected_version=CMEE_GROUNDED_GRAPH_SCHEMA_VERSION,
    )
    if ref_type == "node":
        node = node_by_id.get(ref_id)
        return bool(
            node is not None
            and str(node.node_kind).lower()
            in {
                "event",
                "action",
                "change",
                "bounded_change",
                "promotion_risk",
            }
        )
    edge = edge_by_id.get(ref_id)
    return bool(
        edge is not None
        and str(edge.relation).lower()
        in {
            "contrast",
            "wish_and_constraint",
            "unsupported_promotion_risk",
        }
    )


def _validate_stage1_subjective_cross_field(
    row: EmlisSubjectiveClaim,
    *,
    projection: EmlisStage1Projection,
    parent_plan: ExperiencePlan,
    contribution_by_id: Mapping[str, PlannedObservationContribution],
    node_by_id: Mapping[str, MeaningNode],
    edge_by_id: Mapping[str, MeaningEdge],
) -> str:
    proposition = row.asserted_subjective_proposition
    mode = row.subjective_mode
    operator = proposition.subjective_operator
    matrix = {
        SubjectiveMode.ATTENTION: SubjectiveOperator.ATTEND_TO,
        SubjectiveMode.AFFECTIVE_RESPONSE: SubjectiveOperator.FEEL_TOWARD,
        SubjectiveMode.PERSONAL_APPRAISAL: SubjectiveOperator.APPRAISE_AS_MATERIAL,
        SubjectiveMode.VALUE_POSITION: SubjectiveOperator.PROTECT_VALUE_BOUNDARY,
        SubjectiveMode.RELATIONAL_STANCE: SubjectiveOperator.TAKE_RELATIONAL_STANCE,
        SubjectiveMode.BOUNDED_COUNTERPOSITION: SubjectiveOperator.COUNTER_SPECIFIC_PROMOTION,
    }
    if matrix.get(mode) is not operator:
        raise CMEEStage1ContractError("stage1_subjective_cross_field_invalid")

    affect_present = (
        proposition.affect_category is not None
        or proposition.affect_intensity is not None
    )
    if mode is SubjectiveMode.AFFECTIVE_RESPONSE:
        if (
            type(proposition.affect_category) is not AffectCategory
            or type(proposition.affect_intensity) is not AffectIntensity
            or proposition.stance_operator is not None
            or proposition.counterposition_target_ref is not None
            or row.value_principle_refs
        ):
            raise CMEEStage1ContractError("stage1_subjective_cross_field_invalid")
    elif mode is SubjectiveMode.RELATIONAL_STANCE:
        if (
            affect_present
            or type(proposition.stance_operator) is not StanceOperator
            or proposition.counterposition_target_ref is not None
        ):
            raise CMEEStage1ContractError("stage1_subjective_cross_field_invalid")
    elif mode is SubjectiveMode.BOUNDED_COUNTERPOSITION:
        if (
            affect_present
            or proposition.stance_operator is not StanceOperator.PROTECT_USER_AGENCY
            or proposition.counterposition_target_ref is None
            or not row.value_principle_refs
        ):
            raise CMEEStage1ContractError("stage1_subjective_cross_field_invalid")
    elif mode is SubjectiveMode.VALUE_POSITION:
        if (
            affect_present
            or proposition.stance_operator is not None
            or proposition.counterposition_target_ref is not None
            or not row.value_principle_refs
        ):
            raise CMEEStage1ContractError("stage1_subjective_cross_field_invalid")
    elif (
        affect_present
        or proposition.stance_operator is not None
        or proposition.counterposition_target_ref is not None
        or row.value_principle_refs
    ):
        raise CMEEStage1ContractError("stage1_subjective_cross_field_invalid")

    if (
        proposition.addressee_role not in {"USER", "NONE"}
        or proposition.polarity not in {"positive", "negative", "mixed", "neutral"}
        or proposition.modality
        not in {"fact", "feeling", "wish", "possibility", "uncertain", "refusal", "intention"}
    ):
        raise CMEEStage1ContractError("stage1_subjective_grounded_field_invalid")

    if len(row.source_reception_act_refs) != 1:
        raise CMEEStage1ContractError("stage1_subjective_reception_act_union_invalid")
    reception_act = row.source_reception_act_refs[0]
    act_row = _stage1_reception_act_row(reception_act)
    if (mode, operator) not in act_row.eligible_mode_operator_pairs:
        raise CMEEStage1ContractError("stage1_subjective_act_mode_invalid")

    stance_name = _stage1_stance_for_act(reception_act)
    stance_row = _stage1_reception_stance_row(stance_name)
    if (
        mode
        in {SubjectiveMode.RELATIONAL_STANCE, SubjectiveMode.BOUNDED_COUNTERPOSITION}
        and proposition.stance_operator not in stance_row.eligible_stance_operators
    ):
        raise CMEEStage1ContractError("stage1_subjective_stance_invalid")

    basis_contributions = tuple(
        contribution_by_id[ref]
        for ref in row.basis_observation_contribution_refs
    )
    if (
        proposition.stance_operator is StanceOperator.WELCOME_BOUNDED_CHANGE
        and not any(
            contribution.semantic_operator is SemanticOperator.PRESENT_CHANGE
            for contribution in basis_contributions
        )
    ):
        raise CMEEStage1ContractError("stage1_subjective_stance_material_invalid")
    if (
        proposition.stance_operator is StanceOperator.HOLD_UNFINISHED_OPEN
        and not any(
            contribution.semantic_operator is SemanticOperator.PRESENT_UNFINISHED
            or contribution.contribution_kind
            is ObservationContributionKind.PRESERVE_UNFINISHED
            for contribution in basis_contributions
        )
    ):
        raise CMEEStage1ContractError("stage1_subjective_stance_material_invalid")
    target_contributions = tuple(
        contribution_by_id[ref]
        for ref in proposition.target_contribution_refs
    )
    target_node_kinds: set[str] = set()
    for contribution in target_contributions:
        for semantic_ref in contribution.semantic_refs:
            ref_type, ref_id = _stage1_ref_parts(
                semantic_ref,
                expected_types=("node",),
                expected_version=CMEE_GROUNDED_GRAPH_SCHEMA_VERSION,
            )
            if ref_type == "node" and ref_id in node_by_id:
                target_node_kinds.add(str(node_by_id[ref_id].node_kind).lower())
    reception_target_owners = set(parent_plan.reception_target_owner_ids)
    if not reception_target_owners:
        raise CMEEStage1ContractError(
            "stage1_subjective_reception_target_owner_missing"
        )
    reception_target_node_kinds = {
        str(node.node_kind).lower()
        for node in node_by_id.values()
        if node.owner_id in reception_target_owners
    }

    def response_ref_reaches_parent_target(ref: str) -> bool:
        if ref in contribution_by_id:
            contribution = contribution_by_id[ref]
            node_ids: set[str] = set()
            for semantic_ref in contribution.semantic_refs:
                ref_type, ref_id = _stage1_ref_parts(
                    semantic_ref,
                    expected_types=("node",),
                    expected_version=CMEE_GROUNDED_GRAPH_SCHEMA_VERSION,
                )
                if ref_type == "node":
                    node_ids.add(ref_id)
            return any(
                node_by_id[node_id].owner_id in reception_target_owners
                for node_id in node_ids
                if node_id in node_by_id
            )
        ref_type, ref_id = _stage1_ref_parts(
            ref,
            expected_types=("node", "edge"),
            expected_version=CMEE_GROUNDED_GRAPH_SCHEMA_VERSION,
        )
        if ref_type == "node":
            node = node_by_id.get(ref_id)
            return bool(
                node is not None
                and node.owner_id in reception_target_owners
            )
        edge = edge_by_id.get(ref_id)
        return bool(
            edge is not None
            and any(
                node_by_id[node_id].owner_id in reception_target_owners
                for node_id in (edge.source_node_id, edge.target_node_id)
                if node_id in node_by_id
            )
        )

    target_operators = {
        contribution.semantic_operator for contribution in target_contributions
    }
    paired_bounded_counterposition_targets = {
        claim.asserted_subjective_proposition.counterposition_target_ref
        for claim in projection.subjective_claims
        if claim.subjective_mode is SubjectiveMode.BOUNDED_COUNTERPOSITION
        and claim.source_reception_act_refs
        == ("bounded_counter_self_denial",)
        and claim.asserted_subjective_proposition.counterposition_target_ref
        is not None
    }
    object_contract_satisfied = {
        "stay_with_current_burden": bool(
            target_operators
            & {SemanticOperator.PRESENT_BURDEN, SemanticOperator.PRESENT_RESIDUE}
            or target_node_kinds
            & {
                "constraint",
                "burden",
                "fatigue",
                "anxiety",
                "hesitation",
                "block",
                "residue",
                "reaction",
            }
        ),
        "honor_concrete_effort": bool(
            SemanticOperator.PRESENT_ACTUAL_OUTPUT in target_operators
            or target_node_kinds & {"action", "attempt", "actual_output"}
        ),
        "protect_retained_intention": bool(
            SemanticOperator.PRESENT_DIRECTION in target_operators
            or target_node_kinds
            & {"wish", "direction", "desire", "intention", "goal", "help_seeking"}
        ),
        "recognize_lived_change": bool(
            SemanticOperator.PRESENT_CHANGE in target_operators
            or target_node_kinds & {"change", "bounded_change"}
        ),
        "hold_help_seeking": bool(
            SemanticOperator.PRESENT_DIRECTION in target_operators
            or target_node_kinds & {"help_seeking"}
            or (
                SemanticOperator.PRESENT_STATE in target_operators
                and reception_target_node_kinds
                & {"wish", "direction", "desire", "intention", "goal"}
            )
            or (
                target_node_kinds & {"self_evaluation"}
                and len(proposition.response_object_refs) == 1
                and proposition.response_object_refs[0]
                in paired_bounded_counterposition_targets
                and all(
                    contribution.evidence_refs
                    for contribution in target_contributions
                )
            )
        ),
        "bounded_counter_self_denial": bool(
            all(
                contribution.evidence_refs
                for contribution in target_contributions
            )
            and (
                mode is not SubjectiveMode.BOUNDED_COUNTERPOSITION
                or proposition.counterposition_target_ref is not None
            )
        ),
        "respect_words_placed": bool(
            target_contributions
            and all(
                contribution.evidence_refs
                for contribution in target_contributions
            )
        ),
    }[reception_act]
    if not object_contract_satisfied:
        raise CMEEStage1ContractError(
            "stage1_subjective_object_contract_invalid"
        )
    expected_basis_semantic_refs = _stage1_basis_semantic_refs(
        basis_contributions
    )
    if row.basis_semantic_refs != expected_basis_semantic_refs:
        raise CMEEStage1ContractError(
            "stage1_subjective_basis_semantic_projection_mismatch"
        )
    if not set(
        (
            *proposition.referenced_actor_refs,
            *proposition.referenced_experiencer_refs,
        )
    ).issubset(set(expected_basis_semantic_refs)):
        raise CMEEStage1ContractError("stage1_subjective_actor_unreachable")
    reachable_response_refs = {
        *proposition.target_contribution_refs,
        *(
            ref
            for contribution in target_contributions
            for ref in (
                *contribution.semantic_refs,
                *contribution.relation_basis_refs,
            )
        ),
    }
    if not set(proposition.response_object_refs).issubset(
        reachable_response_refs
    ):
        raise CMEEStage1ContractError(
            "stage1_subjective_response_object_unreachable"
        )
    if (
        proposition.counterposition_target_ref is not None
        and proposition.counterposition_target_ref not in reachable_response_refs
    ):
        raise CMEEStage1ContractError(
            "stage1_subjective_counterposition_target_unreachable"
        )
    if any(
        not response_ref_reaches_parent_target(ref)
        for ref in proposition.response_object_refs
    ):
        raise CMEEStage1ContractError(
            "stage1_subjective_response_object_not_reception_target"
        )
    if (
        proposition.counterposition_target_ref is not None
        and not response_ref_reaches_parent_target(
            proposition.counterposition_target_ref
        )
    ):
        raise CMEEStage1ContractError(
            "stage1_subjective_counterposition_not_reception_target"
        )

    if proposition.affect_category is AffectCategory.DISCOMFORT:
        if any(
            not _stage1_discomfort_target_is_allowed(
                ref,
                contribution_by_id=contribution_by_id,
                node_by_id=node_by_id,
                edge_by_id=edge_by_id,
            )
            for ref in proposition.response_object_refs
        ):
            raise CMEEStage1ContractError(
                "stage1_subjective_discomfort_target_invalid"
            )
    if mode is SubjectiveMode.AFFECTIVE_RESPONSE:
        if proposition.affect_category not in act_row.affect_categories:
            raise CMEEStage1ContractError(
                "stage1_subjective_affect_category_invalid"
            )
        if proposition.affect_intensity is AffectIntensity.MODERATE:
            if (
                proposition.affect_category
                not in {AffectCategory.RELIEF, AffectCategory.JOY, AffectCategory.RESPECT}
                or any(
                    contribution.retention != "REQUIRED"
                    or not contribution.evidence_refs
                    for contribution in target_contributions
                )
                or projection.reception_style_policy_ref
                not in {
                    _stage1_reception_stance_row("warm_recognition").distance_policy_ref,
                    _stage1_reception_stance_row("gentle_respect").distance_policy_ref,
                }
            ):
                raise CMEEStage1ContractError(
                    "stage1_subjective_affect_intensity_invalid"
                )

    value_ref_order = tuple(ref for _code, ref in CMEE_STAGE1_VALUE_PRINCIPLE_REFS)
    if (
        len(row.value_principle_refs) != len(set(row.value_principle_refs))
        or any(ref not in value_ref_order for ref in row.value_principle_refs)
        or row.value_principle_refs
        != tuple(ref for ref in value_ref_order if ref in set(row.value_principle_refs))
    ):
        raise CMEEStage1ContractError("stage1_value_principle_ref_invalid")
    material_refs = _stage1_material_visible_value_refs(
        reception_act=reception_act,
        contributions=basis_contributions,
    )
    if not set(row.value_principle_refs).issubset(set(material_refs)):
        raise CMEEStage1ContractError("stage1_nonmaterial_value_visible")
    if mode in {
        SubjectiveMode.VALUE_POSITION,
        SubjectiveMode.BOUNDED_COUNTERPOSITION,
    } and not row.value_principle_refs:
        raise CMEEStage1ContractError("stage1_material_value_ref_missing")

    expected_forbidden = stage1_subjective_forbidden_promotions(
        basis_contributions,
        material_unknown_refs=projection.meaning_field.material_unknown_refs,
    )
    if row.forbidden_promotions != expected_forbidden:
        raise CMEEStage1ContractError(
            "stage1_subjective_forbidden_promotion_mismatch"
        )
    return stage1_subjective_semantic_key(row)


def validate_stage1_projection(
    projection: EmlisStage1Projection,
    *,
    grounded_graph: GroundedMeaningGraph,
    parent_plan: ExperiencePlan,
) -> None:
    """Validate the disabled request-local projection and its identity DAG.

    The projection is not an ExperiencePlan and this validator never installs a
    second duty owner.  The required ``parent_plan`` resolves every duty and
    retained act against the existing flat provisional mapping.
    """

    if type(projection) is not EmlisStage1Projection:
        raise CMEEStage1ContractError("stage1_projection_type_invalid")
    if type(parent_plan) is not ExperiencePlan:
        raise CMEEStage1ContractError("stage1_parent_plan_type_invalid")
    _validate_stage1_immutable_shape(projection)
    if projection.schema_version != CMEE_STAGE1_RESPONSE_SCHEMA_VERSION:
        raise CMEEStage1ContractError("stage1_projection_schema_version_invalid")
    node_ids, edge_ids, evidence_ids = _stage1_graph_universe(
        projection, grounded_graph
    )
    node_by_id = {row.node_id: row for row in grounded_graph.nodes}
    edge_by_id = {row.edge_id: row for row in grounded_graph.edges}
    for ref in (
        projection.reception_style_policy_ref,
        projection.emlis_value_policy_ref,
        projection.emlis_microgrammar_policy_ref,
    ):
        validate_version_qualified_ref(ref, expected_types=("policy",))
    if projection.emlis_value_policy_ref != CMEE_STAGE1_VALUE_POLICY_REF:
        raise CMEEStage1ContractError("stage1_value_policy_ref_invalid")
    if projection.emlis_microgrammar_policy_ref != CMEE_STAGE1_MICROGRAMMAR_POLICY_REF:
        raise CMEEStage1ContractError("stage1_microgrammar_policy_ref_invalid")
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
    contribution_by_id = {row.contribution_id: row for row in contributions}
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
    if meaning_field.center_candidate_ref not in set(
        meaning_field.required_candidate_refs
    ):
        raise CMEEStage1ContractError("stage1_meaning_field_center_not_required")
    candidate_by_id = {row.candidate_id: row for row in candidates}
    seen_slots: set[MeaningFieldSlot] = set()
    meaning_field_candidate_refs: list[str] = []
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
        meaning_field_candidate_refs.extend(entry.interpretation_candidate_refs)
        _validate_stage1_semantic_refs(
            entry.semantic_refs, node_ids=node_ids, edge_ids=edge_ids
        )
        _validate_stage1_evidence_refs(
            entry.evidence_refs,
            evidence_ids=evidence_ids,
            source_version=grounded_graph.source_version,
        )
        entry_candidates = tuple(
            candidate_by_id[ref]
            for ref in entry.interpretation_candidate_refs
        )
        if any(
            _stage1_meaning_field_slot_for_candidate(candidate) is not entry.slot
            for candidate in entry_candidates
        ):
            raise CMEEStage1ContractError(
                "stage1_meaning_field_slot_mapping_invalid"
            )
        expected_semantic_refs = _stage1_ordered_unique(
            tuple(
                ref
                for candidate in entry_candidates
                for ref in candidate.semantic_refs
            )
        )
        expected_evidence_refs = _stage1_ordered_unique(
            tuple(
                ref
                for candidate in entry_candidates
                for ref in candidate.evidence_refs
            )
        )
        if (
            entry.semantic_refs != expected_semantic_refs
            or entry.evidence_refs != expected_evidence_refs
        ):
            raise CMEEStage1ContractError(
                "stage1_meaning_field_entry_projection_mismatch"
            )
    if (
        len(meaning_field_candidate_refs) != len(set(meaning_field_candidate_refs))
        or set(meaning_field_candidate_refs) != candidate_set
        or any(
            meaning_field_candidate_refs.count(ref) != 1
            for ref in meaning_field.required_candidate_refs
        )
    ):
        raise CMEEStage1ContractError(
            "stage1_meaning_field_required_not_exact_cover"
        )
    slot_order = {slot: index for index, slot in enumerate(_STAGE1_MEANING_SLOT_ORDER)}
    entry_slots = tuple(entry.slot for entry in meaning_field.entries)
    if any(slot not in slot_order for slot in entry_slots) or entry_slots != tuple(
        sorted(entry_slots, key=slot_order.__getitem__)
    ):
        raise CMEEStage1ContractError("stage1_meaning_field_slot_order_invalid")

    direct_shape_sets: dict[
        str,
        set[tuple[InterpretationKind, SemanticOperator]],
    ] = {}
    for row in candidates:
        if (
            row.relation_operator is RelationOperator.NO_RELATION_CLAIM
            and type(row.candidate_kind) is InterpretationKind
            and type(row.semantic_operator) is SemanticOperator
        ):
            primary_refs = tuple(
                binding.semantic_ref
                for binding in row.argument_bindings
                if type(binding) is ArgumentBinding
                and binding.role is ArgumentRole.PRIMARY
            )
            if len(primary_refs) == 1:
                direct_shape_sets.setdefault(primary_refs[0], set()).add(
                    (row.candidate_kind, row.semantic_operator)
                )
    direct_shapes_by_node_ref = {
        ref: frozenset(shapes) for ref, shapes in direct_shape_sets.items()
    }

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
        _validate_stage1_interpretation_matrix(row)
        _require_unique_nonempty_refs(
            row.semantic_refs, code="stage1_candidate_semantic_ref_invalid"
        )
        _require_unique_nonempty_refs(
            row.evidence_refs, code="stage1_candidate_evidence_ref_invalid"
        )
        _validate_stage1_semantic_refs(
            row.semantic_refs, node_ids=node_ids, edge_ids=edge_ids
        )
        _validate_stage1_evidence_refs(
            row.evidence_refs,
            evidence_ids=evidence_ids,
            source_version=grounded_graph.source_version,
        )
        _validate_stage1_semantic_refs(
            row.relation_basis_refs, node_ids=set(), edge_ids=edge_ids
        )
        if any(
            binding.semantic_ref not in set(row.semantic_refs)
            for binding in row.argument_bindings
        ):
            raise CMEEStage1ContractError("stage1_candidate_argument_ref_invalid")
        for binding in row.argument_bindings:
            ref_type, ref_id = _stage1_ref_parts(
                binding.semantic_ref,
                expected_types=("node",),
                expected_version=CMEE_GROUNDED_GRAPH_SCHEMA_VERSION,
            )
            if ref_type != "node" or ref_id not in node_ids:
                raise CMEEStage1ContractError(
                    "stage1_candidate_argument_ref_invalid"
                )
        binding_refs = _stage1_ordered_unique(
            tuple(binding.semantic_ref for binding in row.argument_bindings)
        )
        if row.semantic_refs != binding_refs:
            raise CMEEStage1ContractError("stage1_candidate_argument_ref_invalid")
        if (
            row.relation_operator is RelationOperator.NO_RELATION_CLAIM
            and len(row.argument_bindings) == 2
            and row.argument_bindings[0].semantic_ref
            != row.argument_bindings[1].semantic_ref
        ):
            raise CMEEStage1ContractError("stage1_candidate_argument_ref_invalid")
        if row.relation_operator is RelationOperator.NO_RELATION_CLAIM:
            if row.relation_basis_refs:
                raise CMEEStage1ContractError("stage1_candidate_relation_basis_invalid")
            primary_ref = row.argument_bindings[0].semantic_ref
            _primary_type, primary_node_id = _stage1_ref_parts(
                primary_ref,
                expected_types=("node",),
                expected_version=CMEE_GROUNDED_GRAPH_SCHEMA_VERSION,
            )
            if (
                (row.candidate_kind, row.semantic_operator)
                not in _stage1_allowed_direct_shapes(node_by_id[primary_node_id])
            ):
                raise CMEEStage1ContractError(
                    "stage1_candidate_direct_shape_invalid"
                )
        elif not row.relation_basis_refs:
            raise CMEEStage1ContractError("stage1_candidate_relation_basis_missing")
        _validate_stage1_relation_binding(
            row,
            edge_by_id=edge_by_id,
            node_by_id=node_by_id,
            direct_shapes_by_node_ref=direct_shapes_by_node_ref,
        )
        if row.relation_operator is RelationOperator.NO_RELATION_CLAIM:
            expected_derivation_rule_id = (
                "cocolon.cmee.v1a.stage1.direct."
                f"{row.candidate_kind.value.lower()}.v1"
            )
        else:
            _edge_type, derivation_edge_id = _stage1_ref_parts(
                row.relation_basis_refs[0],
                expected_types=("edge",),
                expected_version=CMEE_GROUNDED_GRAPH_SCHEMA_VERSION,
            )
            expected_derivation_rule_id = (
                "cocolon.cmee.v1a.stage1.relation."
                f"{str(edge_by_id[derivation_edge_id].relation).lower()}.v1"
            )
        if row.derivation_rule_id != expected_derivation_rule_id:
            raise CMEEStage1ContractError(
                "stage1_candidate_derivation_rule_invalid"
            )
        grounded_evidence_ids = _stage1_grounded_evidence_for_refs(
            row.semantic_refs,
            row.relation_basis_refs,
            node_by_id=node_by_id,
            edge_by_id=edge_by_id,
        )
        candidate_evidence_ids = tuple(
            _stage1_ref_parts(
                ref,
                expected_types=("evidence",),
                expected_version=grounded_graph.source_version,
            )[1]
            for ref in row.evidence_refs
        )
        if candidate_evidence_ids != grounded_evidence_ids:
            raise CMEEStage1ContractError(
                "stage1_candidate_source_evidence_unreachable"
            )

    kind_counts: dict[InterpretationKind, int] = {}
    required_candidate_set = set(meaning_field.required_candidate_refs)
    for row in candidates:
        kind_counts[row.candidate_kind] = kind_counts.get(row.candidate_kind, 0) + 1
        if kind_counts[row.candidate_kind] > _STAGE1_INTERPRETATION_CANDIDATE_KIND_CAP:
            code = (
                "stage1_required_candidate_overflow"
                if row.candidate_id in required_candidate_set
                else "stage1_candidate_kind_cap_exceeded"
            )
            raise CMEEStage1ContractError(code)

    required_contribution_candidate_refs: list[str] = []
    optional_contribution_count = 0
    semantic_keys: list[str] = []
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
        if len(row.interpretation_candidate_refs) != 1:
            raise CMEEStage1ContractError(
                "stage1_observation_candidate_binding_invalid"
            )
        candidate = candidate_by_id[row.interpretation_candidate_refs[0]]
        _validate_stage1_semantic_refs(
            row.semantic_refs, node_ids=node_ids, edge_ids=edge_ids
        )
        _validate_stage1_evidence_refs(
            row.evidence_refs,
            evidence_ids=evidence_ids,
            source_version=grounded_graph.source_version,
        )
        _validate_stage1_semantic_refs(
            row.relation_basis_refs, node_ids=set(), edge_ids=edge_ids
        )
        if any(
            binding.semantic_ref not in set(row.semantic_refs)
            for binding in row.argument_bindings
        ):
            raise CMEEStage1ContractError("stage1_contribution_argument_ref_invalid")
        if (
            row.contribution_kind
            is not _stage1_contribution_kind_for_candidate(candidate)
            or row.semantic_operator is not candidate.semantic_operator
            or row.argument_bindings != candidate.argument_bindings
            or row.relation_operator is not candidate.relation_operator
            or row.relation_basis_refs != candidate.relation_basis_refs
            or row.semantic_refs != candidate.semantic_refs
            or row.evidence_refs != candidate.evidence_refs
        ):
            raise CMEEStage1ContractError(
                "stage1_observation_candidate_binding_invalid"
            )
        expected_contribution_rule_id = (
            "cocolon.cmee.v1a.stage1.layer1."
            f"{row.contribution_kind.value.lower()}.v1"
        )
        if row.derivation_rule_id != expected_contribution_rule_id:
            raise CMEEStage1ContractError(
                "stage1_observation_derivation_rule_invalid"
            )
        if row.retention not in {"REQUIRED", "OPTIONAL"}:
            raise CMEEStage1ContractError("stage1_observation_retention_invalid")
        if row.retention == "REQUIRED":
            required_contribution_candidate_refs.append(candidate.candidate_id)
        else:
            optional_contribution_count += 1
        if (
            row.semantic_key_version != _STAGE2_OBSERVATION_SEMANTIC_KEY_VERSION
            or row.canonical_semantic_key
            != _stage2_observation_semantic_key(candidate)
        ):
            raise CMEEStage1ContractError(
                "stage1_observation_semantic_key_mismatch"
            )
        semantic_keys.append(row.canonical_semantic_key)

    if set(required_contribution_candidate_refs) != required_candidate_set or len(
        required_contribution_candidate_refs
    ) != len(required_candidate_set):
        raise CMEEStage1ContractError(
            "stage1_required_observation_candidate_uncovered"
        )
    if optional_contribution_count > 1 or (
        len(required_candidate_set) != 1 and optional_contribution_count
    ):
        raise CMEEStage1ContractError("stage1_observation_optional_tail_invalid")
    if len(required_candidate_set) > _STAGE1_LAYER1_OBSERVATION_CAP:
        raise CMEEStage1ContractError("stage1_required_observation_unrealizable")
    if len(semantic_keys) != len(set(semantic_keys)):
        raise CMEEStage1ContractError("stage1_duplicate_observation_contribution")

    _require_unique_nonempty_refs(
        projection.retained_reception_act_ids,
        code="stage1_retained_reception_act_invalid",
    )
    if not projection.retained_reception_act_ids:
        raise CMEEStage1ContractError("stage1_retained_reception_act_invalid")
    retained_acts = set(projection.retained_reception_act_ids)
    for reception_act in projection.retained_reception_act_ids:
        _stage1_reception_act_row(reception_act)
    primary_stance = _stage1_stance_for_act(
        projection.retained_reception_act_ids[0]
    )
    primary_stance_row = _stage1_reception_stance_row(primary_stance)
    if projection.reception_style_policy_ref != primary_stance_row.distance_policy_ref:
        raise CMEEStage1ContractError("stage1_reception_style_policy_ref_invalid")
    referenced_acts: set[str] = set()
    subjective_semantic_keys: list[str] = []
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
                _validate_stage1_semantic_refs(
                    (ref,), node_ids=node_ids, edge_ids=edge_ids
                )
        if proposition.counterposition_target_ref is not None:
            counterposition_ref = proposition.counterposition_target_ref
            if type(counterposition_ref) is not str or not counterposition_ref:
                raise CMEEStage1ContractError(
                    "stage1_subjective_counterposition_ref_invalid"
                )
            if counterposition_ref not in contribution_set:
                _validate_stage1_semantic_refs(
                    (counterposition_ref,), node_ids=node_ids, edge_ids=edge_ids
                )
        for ref in (
            *proposition.referenced_actor_refs,
            *proposition.referenced_experiencer_refs,
        ):
            ref_type, ref_id = _stage1_ref_parts(
                ref,
                expected_types=("node",),
                expected_version=CMEE_GROUNDED_GRAPH_SCHEMA_VERSION,
            )
            if ref_type != "node" or ref_id not in node_ids:
                raise CMEEStage1ContractError("stage1_actor_ref_missing")
        if (
            len(proposition.referenced_actor_refs)
            != len(set(proposition.referenced_actor_refs))
            or len(proposition.referenced_experiencer_refs)
            != len(set(proposition.referenced_experiencer_refs))
        ):
            raise CMEEStage1ContractError("stage1_actor_ref_duplicate")
        if len(row.source_reception_act_refs) != 1:
            raise CMEEStage1ContractError(
                "stage1_subjective_reception_act_union_invalid"
            )
        _require_local_subset(
            row.source_reception_act_refs,
            retained_acts,
            code="stage1_subjective_reception_act_unknown",
            allow_empty=False,
        )
        referenced_acts.update(row.source_reception_act_refs)
        _validate_stage1_semantic_refs(
            row.basis_semantic_refs, node_ids=node_ids, edge_ids=edge_ids
        )
        _validate_stage1_external_refs(
            row.value_principle_refs, expected_types=("policy",)
        )
        subjective_semantic_keys.append(
            _validate_stage1_subjective_cross_field(
                row,
                projection=projection,
                parent_plan=parent_plan,
                contribution_by_id=contribution_by_id,
                node_by_id=node_by_id,
                edge_by_id=edge_by_id,
            )
        )
    if referenced_acts != retained_acts:
        raise CMEEStage1ContractError("stage1_retained_reception_act_uncovered")
    if len(subjective_semantic_keys) != len(set(subjective_semantic_keys)):
        raise CMEEStage1ContractError("stage1_duplicate_subjective_claim")

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
    if primary_stance_row.temperature_rule == "STANDARD":
        if projection.temperature_class is not TemperatureClass.STANDARD:
            raise CMEEStage1ContractError("stage1_temperature_policy_mismatch")
    elif projection.temperature_class not in {
        TemperatureClass.STANDARD,
        TemperatureClass.ELEVATED_NON_SAFETY,
    }:
        raise CMEEStage1ContractError("stage1_temperature_policy_mismatch")
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

    if type(parent_plan) is not ExperiencePlan:
        raise CMEEStage1ContractError("stage1_parent_plan_type_invalid")
    if (
        parent_plan.source_envelope_id != grounded_graph.source_envelope_id
        or parent_plan.source_version != grounded_graph.source_version
        or parent_plan.obligation_version != grounded_graph.obligation_version
        or parent_plan.owner_universe_digest
        != grounded_graph.owner_universe_digest
    ):
        raise CMEEStage1ContractError("stage1_parent_plan_lineage_mismatch")
    expected_material_unknown_refs = _stage1_expected_material_unknown_refs(
        grounded_graph, parent_plan
    )
    for ref in meaning_field.material_unknown_refs:
        _stage1_ref_parts(
            ref,
            expected_types=("unknown",),
            expected_version=grounded_graph.obligation_version,
        )
    if meaning_field.material_unknown_refs != expected_material_unknown_refs:
        raise CMEEStage1ContractError("stage1_material_unknown_unreachable")
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
    grounded_graph: GroundedMeaningGraph,
    parent_plan: ExperiencePlan,
    prior_unit_ids: Sequence[str] = (),
) -> None:
    validate_stage1_projection(
        projection, grounded_graph=grounded_graph, parent_plan=parent_plan
    )
    if type(unit) is not RealizedSentenceUnit:
        raise CMEEStage1ContractError("stage1_unit_type_invalid")
    _validate_stage1_immutable_shape(unit)
    if type(prior_unit_ids) is not tuple:
        raise CMEEStage1ContractError("stage1_unit_prior_ids_not_tuple")
    if any(type(frame) is not ClauseFrame for frame in unit.clause_frames):
        raise CMEEStage1ContractError("stage1_unit_clause_frame_type_invalid")
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
    node_ids = {row.node_id for row in grounded_graph.nodes}
    edge_ids = {row.edge_id for row in grounded_graph.edges}
    contribution_by_id = {
        row.contribution_id: row for row in projection.observation_contributions
    }
    claim_by_id = {row.subjective_claim_id: row for row in projection.subjective_claims}
    if unit.layer == "LAYER_1":
        allowed_anchors = set(contribution_by_id)
    elif unit.layer == "LAYER_2":
        allowed_anchors = set(claim_by_id)
    else:
        allowed_anchors = set()
    _require_local_subset(
        unit.basis_anchor_refs,
        allowed_anchors,
        code="stage1_unit_basis_anchor_invalid",
        allow_empty=False,
    )
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
    reachable_semantic_refs: set[str] = set()
    if unit.layer == "LAYER_1":
        for anchor_ref in unit.basis_anchor_refs:
            contribution = contribution_by_id.get(anchor_ref)
            if contribution is not None:
                reachable_semantic_refs.update(
                    (*contribution.semantic_refs, *contribution.relation_basis_refs)
                )
    elif unit.layer == "LAYER_2":
        for anchor_ref in unit.basis_anchor_refs:
            claim = claim_by_id.get(anchor_ref)
            if claim is not None:
                reachable_semantic_refs.update(claim.basis_semantic_refs)
    for frame in unit.clause_frames:
        _validate_stage1_immutable_shape(frame)
        validate_version_qualified_ref(frame.move_ref, expected_types=("move",))
        validate_version_qualified_ref(
            frame.reception_style_policy_ref, expected_types=("policy",)
        )
        if frame.topic_ref is not None:
            _validate_stage1_semantic_refs(
                (frame.topic_ref,), node_ids=node_ids, edge_ids=edge_ids
            )
            if frame.topic_ref not in reachable_semantic_refs:
                raise CMEEStage1ContractError("stage1_unit_semantic_ref_unreachable")
        if frame.object_ref is not None:
            _validate_stage1_semantic_refs(
                (frame.object_ref,), node_ids=node_ids, edge_ids=edge_ids
            )
            if frame.object_ref not in reachable_semantic_refs:
                raise CMEEStage1ContractError("stage1_unit_semantic_ref_unreachable")
        for ref in (*frame.actor_refs, *frame.experiencer_refs):
            ref_type, ref_id = _stage1_ref_parts(
                ref,
                expected_types=("node",),
                expected_version=CMEE_GROUNDED_GRAPH_SCHEMA_VERSION,
            )
            if (
                ref_type != "node"
                or ref_id not in node_ids
                or ref not in reachable_semantic_refs
            ):
                raise CMEEStage1ContractError("stage1_unit_semantic_ref_unreachable")
        if (
            any(type(binding) is not ArgumentBinding for binding in frame.argument_bindings)
            or any(
                type(binding.role) is not ArgumentRole
                for binding in frame.argument_bindings
            )
        ):
            raise CMEEStage1ContractError("stage1_unit_argument_binding_invalid")
        for binding in frame.argument_bindings:
            _validate_stage1_semantic_refs(
                (binding.semantic_ref,), node_ids=node_ids, edge_ids=edge_ids
            )
            if binding.semantic_ref not in reachable_semantic_refs:
                raise CMEEStage1ContractError("stage1_unit_semantic_ref_unreachable")
    text_scalar_length = len(unit.text)
    for binding in unit.realized_semantic_bindings:
        if type(binding) is not RealizedSemanticBinding:
            raise CMEEStage1ContractError("stage1_unit_binding_type_invalid")
        _validate_stage1_semantic_refs(
            (binding.semantic_ref,), node_ids=node_ids, edge_ids=edge_ids
        )
        if binding.semantic_ref not in reachable_semantic_refs:
            raise CMEEStage1ContractError("stage1_unit_semantic_ref_unreachable")
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
    *,
    grounded_graph: GroundedMeaningGraph,
    parent_plan: ExperiencePlan,
) -> None:
    """Validate the registered private Emlis trace specialization by role."""

    validate_stage1_projection(
        projection, grounded_graph=grounded_graph, parent_plan=parent_plan
    )
    graph_node_ids = {row.node_id for row in grounded_graph.nodes}
    graph_edge_ids = {row.edge_id for row in grounded_graph.edges}
    rows = tuple(trace_rows)
    if any(type(row) is not VisibleUnitTrace for row in rows):
        raise CMEEStage1ContractError("stage1_trace_row_type_invalid")
    roles = tuple(row.role for row in rows)
    observation_count = roles.count("OBSERVATION")
    unknown_count = roles.count("UNKNOWN")
    reception_count = roles.count("RECEPTION")
    if (
        not 1 <= observation_count <= 5
        or not 0 <= unknown_count <= 1
        or not 1 <= reception_count <= 4
        or observation_count != len(projection.ordered_observation_refs)
        or reception_count != len(projection.ordered_subjective_refs)
        or roles
        != (
            *("OBSERVATION" for _ in range(observation_count)),
            *("UNKNOWN" for _ in range(unknown_count)),
            *("RECEPTION" for _ in range(reception_count)),
        )
    ):
        raise CMEEStage1ContractError("stage1_trace_role_order_invalid")
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
    ordered_observation_trace_refs: list[str] = []
    ordered_reception_trace_refs: list[str] = []
    positive_composition_variants: set[str] = set()

    for index, row in enumerate(rows):
        if (
            row.source_envelope_id != grounded_graph.source_envelope_id
            or row.source_version != grounded_graph.source_version
            or row.obligation_version != grounded_graph.obligation_version
            or row.owner_universe_digest != grounded_graph.owner_universe_digest
        ):
            raise CMEEStage1ContractError("stage1_trace_lineage_metadata_mismatch")
        for field_name in (
            "meaning_node_ids",
            "meaning_edge_ids",
            "evidence_ids",
            "constrained_by_owner_ids",
        ):
            refs = getattr(row, field_name)
            if (
                any(type(ref) is not str or not ref for ref in refs)
                or len(refs) != len(set(refs))
            ):
                raise CMEEStage1ContractError("stage1_trace_base_ref_invalid")
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
        positive_composition_variants.add(extension.composition_variant_id)
        if not (row.meaning_node_ids or row.meaning_edge_ids) or not row.evidence_ids:
            raise CMEEStage1ContractError("stage1_trace_base_lineage_missing")

        if row.role == "OBSERVATION":
            if row.duty_id != projection.parent_observation_duty_ref:
                raise CMEEStage1ContractError("stage1_observation_trace_duty_mismatch")
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
            if len(extension.contribution_refs) != 1:
                raise CMEEStage1ContractError(
                    "stage1_observation_trace_contribution_invalid"
                )
            ordered_observation_trace_refs.append(extension.contribution_refs[0])
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
            reachable_node_ids = {
                _version_qualified_local_id(ref)
                for contribution_ref in extension.contribution_refs
                for ref in contributions[contribution_ref].semantic_refs
                if ref.startswith("node:")
            } | {
                _version_qualified_local_id(ref)
                for candidate_ref in extension.interpretation_candidate_refs
                for ref in next(
                    candidate
                    for candidate in projection.interpretation_candidates
                    if candidate.candidate_id == candidate_ref
                ).semantic_refs
                if ref.startswith("node:")
            }
            reachable_edge_ids = {
                _version_qualified_local_id(ref)
                for contribution_ref in extension.contribution_refs
                for ref in (
                    *contributions[contribution_ref].semantic_refs,
                    *contributions[contribution_ref].relation_basis_refs,
                )
                if ref.startswith("edge:")
            } | {
                _version_qualified_local_id(ref)
                for candidate_ref in extension.interpretation_candidate_refs
                for ref in next(
                    candidate
                    for candidate in projection.interpretation_candidates
                    if candidate.candidate_id == candidate_ref
                ).semantic_refs
                if ref.startswith("edge:")
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
            if (
                not set(row.meaning_node_ids).issubset(
                    reachable_node_ids & graph_node_ids
                )
                or not set(row.meaning_edge_ids).issubset(
                    reachable_edge_ids & graph_edge_ids
                )
                or not set(row.evidence_ids).issubset(reachable_evidence_ids)
            ):
                raise CMEEStage1ContractError(
                    "stage1_observation_trace_lineage_unreachable"
                )
            for contribution_ref in extension.contribution_refs:
                observation_contribution_counts[contribution_ref] += 1
            continue

        if row.duty_id != projection.parent_reception_duty_ref:
            raise CMEEStage1ContractError("stage1_reception_trace_duty_mismatch")
        if (
            extension.claim_domain is not EmlisTraceClaimDomain.SUBJECTIVE_RESPONSE
            or extension.contribution_refs
            or extension.interpretation_candidate_refs
            or extension.speaker_owner != "EMLIS"
            or extension.subjective_claim_ref not in claims
        ):
            raise CMEEStage1ContractError("stage1_reception_trace_domain_invalid")
        claim = claims[extension.subjective_claim_ref]
        ordered_reception_trace_refs.append(extension.subjective_claim_ref)
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
        reachable_basis_contributions: list[str] = []
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
            reachable_basis_contributions.extend(basis_extension.contribution_refs)
        if tuple(extension.basis_observation_contribution_refs) != tuple(
            reachable_basis_contributions
        ):
            raise CMEEStage1ContractError(
                "stage1_reception_trace_basis_unreachable"
            )
        reachable_node_ids = {
            _version_qualified_local_id(ref)
            for ref in claim.basis_semantic_refs
            if ref.startswith("node:")
        } | {
            _version_qualified_local_id(ref)
            for contribution_ref in extension.basis_observation_contribution_refs
            for ref in contributions[contribution_ref].semantic_refs
            if ref.startswith("node:")
        }
        reachable_edge_ids = {
            _version_qualified_local_id(ref)
            for ref in claim.basis_semantic_refs
            if ref.startswith("edge:")
        } | {
            _version_qualified_local_id(ref)
            for contribution_ref in extension.basis_observation_contribution_refs
            for ref in (
                *contributions[contribution_ref].semantic_refs,
                *contributions[contribution_ref].relation_basis_refs,
            )
            if ref.startswith("edge:")
        }
        reachable_evidence_ids = {
            _version_qualified_local_id(ref)
            for contribution_ref in extension.basis_observation_contribution_refs
            for ref in contributions[contribution_ref].evidence_refs
        }
        if (
            not set(row.meaning_node_ids).issubset(
                reachable_node_ids & graph_node_ids
            )
            or not set(row.meaning_edge_ids).issubset(
                reachable_edge_ids & graph_edge_ids
            )
            or not set(row.evidence_ids).issubset(reachable_evidence_ids)
        ):
            raise CMEEStage1ContractError(
                "stage1_reception_trace_lineage_unreachable"
            )

    if any(count != 1 for count in observation_contribution_counts.values()):
        raise CMEEStage1ContractError("stage1_observation_trace_coverage_invalid")
    if any(count != 1 for count in subjective_claim_counts.values()):
        raise CMEEStage1ContractError("stage1_reception_trace_coverage_invalid")
    if tuple(ordered_observation_trace_refs) != projection.ordered_observation_refs:
        raise CMEEStage1ContractError("stage1_observation_trace_order_invalid")
    if tuple(ordered_reception_trace_refs) != projection.ordered_subjective_refs:
        raise CMEEStage1ContractError("stage1_reception_trace_order_invalid")
    if len(positive_composition_variants) != 1:
        raise CMEEStage1ContractError("stage1_trace_variant_mismatch")


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
    "CMEE_GROUNDED_GRAPH_SCHEMA_VERSION",
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
    "RealizationCandidateSet",
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
