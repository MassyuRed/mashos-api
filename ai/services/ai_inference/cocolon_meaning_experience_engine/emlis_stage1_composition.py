# -*- coding: utf-8 -*-
from __future__ import annotations

"""Final, request-local CMEE Stage 1 composition core.

This module is deliberately not wired to the active v1 response facade.  It
contains the Step 2 language core which both early and final execution use.
It consumes frozen typed semantics, never reparses the request, and has no
alternate compatibility realizer.
"""

from dataclasses import dataclass, fields
from enum import Enum
import hashlib
from pathlib import Path
from typing import Any, Iterable, Mapping, Optional, Sequence, Tuple

from .contracts import (
    AffectCategory,
    AffectIntensity,
    AppraisalDimension,
    AppraisalOperation,
    ArgumentBinding,
    ArgumentRole,
    ClauseFrame,
    CMEE_GROUNDED_GRAPH_SCHEMA_VERSION,
    CMEE_STAGE1_FINAL_LOGICAL_ID_REGISTRY,
    CMEE_STAGE1_RECEPTION_ACT_MAPPING_EXACT7,
    CMEE_STAGE1_SUBJECTIVE_FORBIDDEN_PROMOTIONS,
    CMEE_STAGE1_VALUE_PRINCIPLE_REFS,
    EmlisAffectContent,
    EmlisAppraisalContent,
    EmlisInterpretationCandidate,
    EmlisMeaningField,
    EmlisRelationalPosition,
    EmlisStage1Projection,
    EmlisSubjectiveClaim,
    MaterialRisk,
    MaterialValueContent,
    MeaningFieldEntry,
    ObservationContributionKind,
    PlannedObservationContribution,
    PolicyBasisBinding,
    PolicyBasisOwnerKind,
    PolicyBasisRole,
    RelationOperator,
    RealizedSemanticBinding,
    RealizedSentenceUnit,
    RelationalClosure,
    RelationalCommitment,
    RelationalPositionKind,
    SemanticOperator,
    SourceQualifierBinding,
    StanceOperator,
    SubjectiveAssertionModality,
    SubjectiveBasisBinding,
    SubjectiveBasisRole,
    SubjectiveContentKind,
    SubjectiveMode,
    SubjectiveOperator,
    SubjectivePropositionV2,
    SurfaceDerivation,
    ValueApplication,
    _stage1_material_visible_value_refs,
    project_stage1_policy_basis_binding_ref,
    project_stage1_source_qualifier_binding_ref,
    project_stage1_subjective_basis_binding_ref,
    stage1_canonical_json_bytes,
    stage1_subjective_forbidden_promotions,
    validate_stage1_anti_template_registry_invariant,
    validate_stage1_identity,
)


_FINAL_ID = dict(CMEE_STAGE1_FINAL_LOGICAL_ID_REGISTRY)
CMEE_STAGE1_RESPONSE_SCHEMA_VERSION = _FINAL_ID["CMEE_STAGE1_RESPONSE_SCHEMA_VERSION"]
CMEE_STAGE1_SUBJECTIVE_PROPOSITION_SCHEMA_VERSION = _FINAL_ID[
    "CMEE_STAGE1_SUBJECTIVE_PROPOSITION_SCHEMA_VERSION"
]
CMEE_STAGE1_COMPOSITION_POLICY_VERSION = _FINAL_ID[
    "CMEE_STAGE1_COMPOSITION_POLICY_VERSION"
]
CMEE_STAGE1_NORMAL_FORM_VERSION = _FINAL_ID["CMEE_STAGE1_NORMAL_FORM_VERSION"]
CMEE_STAGE1_CONSTRUCTION_GRAMMAR_POLICY_VERSION = _FINAL_ID[
    "CMEE_STAGE1_CONSTRUCTION_GRAMMAR_POLICY_VERSION"
]
CMEE_STAGE1_EMLIS_OWNER_REF = _FINAL_ID["CMEE_STAGE1_EMLIS_OWNER_REF"]


class Stage1CompositionError(ValueError):
    """Named fail-closed stop in the disabled final Stage 1 core."""


class QualifierLookupScope(str, Enum):
    DIRECT_UNQUALIFIED = "DIRECT_UNQUALIFIED"
    RELATION_SOURCE_BINDING = "RELATION_SOURCE_BINDING"


class ClauseScalarAxis(str, Enum):
    POLARITY = "POLARITY"
    MODALITY = "MODALITY"
    TIME_SCOPE = "TIME_SCOPE"


class SentenceJob(str, Enum):
    OBSERVE_CENTER = "OBSERVE_CENTER"
    RELATE_COEXISTING_OR_TENSION = "RELATE_COEXISTING_OR_TENSION"
    TRACE_CHANGE_OR_SEQUENCE = "TRACE_CHANGE_OR_SEQUENCE"
    PRESERVE_RESIDUE_OR_UNFINISHED = "PRESERVE_RESIDUE_OR_UNFINISHED"
    FEEL_TOWARD_OBJECT = "FEEL_TOWARD_OBJECT"
    CONSIDER_MATERIAL_MEANING = "CONSIDER_MATERIAL_MEANING"
    TAKE_MATERIAL_POSITION = "TAKE_MATERIAL_POSITION"
    STAY_WITH_UNFINISHED = "STAY_WITH_UNFINISHED"


class ArcDependencyKind(str, Enum):
    ADMITTED_RELATION_DIRECTION = "ADMITTED_RELATION_DIRECTION"
    SOURCE_DEPENDENCY_ORDER = "SOURCE_DEPENDENCY_ORDER"
    GROUNDED_BEFORE_SUBJECTIVE = "GROUNDED_BEFORE_SUBJECTIVE"
    SUBJECTIVE_CONTENT_DEPENDENCY = "SUBJECTIVE_CONTENT_DEPENDENCY"
    UNFINISHED_TERMINAL = "UNFINISHED_TERMINAL"


class DutySuppressionReason(str, Enum):
    NONMATERIAL_OPTIONAL = "NONMATERIAL_OPTIONAL"
    DUPLICATE_SEMANTIC_COVERAGE = "DUPLICATE_SEMANTIC_COVERAGE"
    ABSORBED_INTO_VISIBLE_OWNER = "ABSORBED_INTO_VISIBLE_OWNER"


class SemanticClauseKind(str, Enum):
    GROUNDED_PREDICATE = "GROUNDED_PREDICATE"
    SUBJECTIVE_PREDICATE = "SUBJECTIVE_PREDICATE"
    ADMITTED_RELATION = "ADMITTED_RELATION"


class SubjectivePredicationKind(str, Enum):
    AFFECT = "AFFECT"
    APPRAISAL = "APPRAISAL"
    MATERIAL_VALUE = "MATERIAL_VALUE"
    RELATIONAL_STANCE = "RELATIONAL_STANCE"
    BOUNDED_COUNTERPOSITION = "BOUNDED_COUNTERPOSITION"


class PredicateValency(str, Enum):
    MONADIC_ARGUMENT = "MONADIC_ARGUMENT"
    DYADIC_ACTOR_TARGET = "DYADIC_ACTOR_TARGET"
    TRIADIC_ACTOR_TARGET_BOUNDARY = "TRIADIC_ACTOR_TARGET_BOUNDARY"
    DYADIC_RELATION_ENDPOINTS = "DYADIC_RELATION_ENDPOINTS"


class ClauseArgumentRole(str, Enum):
    SUBJECT = "SUBJECT"
    PRIMARY_OBJECT = "PRIMARY_OBJECT"
    SECONDARY_OBJECT = "SECONDARY_OBJECT"
    LEFT_ENDPOINT = "LEFT_ENDPOINT"
    RIGHT_ENDPOINT = "RIGHT_ENDPOINT"
    BEFORE_EVENT = "BEFORE_EVENT"
    AFTER_EVENT = "AFTER_EVENT"
    ACTION_EVENT = "ACTION_EVENT"
    CHANGE_EVENT = "CHANGE_EVENT"
    CAUSE_EVENT = "CAUSE_EVENT"
    EFFECT_EVENT = "EFFECT_EVENT"


class GrammaticalRoleAssignmentRule(str, Enum):
    DIRECT_REFERENT_SUBJECT = "DIRECT_REFERENT_SUBJECT"
    GROUNDED_ACTOR_TARGET = "GROUNDED_ACTOR_TARGET"
    EMLIS_TARGET_OR_BOUNDARY = "EMLIS_TARGET_OR_BOUNDARY"
    ADMITTED_RELATION_ENDPOINT_PAIR = "ADMITTED_RELATION_ENDPOINT_PAIR"


class SyntacticOrientation(str, Enum):
    REFERENT_FIRST = "REFERENT_FIRST"
    GROUNDED_ACTOR_SUBJECT = "GROUNDED_ACTOR_SUBJECT"
    EMLIS_SUBJECT = "EMLIS_SUBJECT"
    EVENT_FIRST = "EVENT_FIRST"
    RELATION_FIRST = "RELATION_FIRST"


class SpeakerRequirement(str, Enum):
    GROUNDED_NARRATION = "GROUNDED_NARRATION"
    EMLIS_EXPLICIT_REQUIRED = "EMLIS_EXPLICIT_REQUIRED"
    EMLIS_ZERO_ALLOWED = "EMLIS_ZERO_ALLOWED"


class ScalarSurfaceRealizationMode(str, Enum):
    OVERT_FUNCTIONAL_PART = "OVERT_FUNCTIONAL_PART"
    FUSED_IN_REGISTERED_PART = "FUSED_IN_REGISTERED_PART"
    UNMARKED_DEFAULT = "UNMARKED_DEFAULT"
    SEMANTIC_PROVENANCE_ONLY = "SEMANTIC_PROVENANCE_ONLY"


class RegisteredFunctionalSlotRef(str, Enum):
    PREDICATE_HEAD = "functional-slot:predicate-head.v1"
    QUALIFIER = "functional-slot:qualifier.v1"


class ResponseObjectExpressionMode(str, Enum):
    EXPLICIT = "EXPLICIT"
    COMPOSITE = "COMPOSITE"
    ANAPHORIC = "ANAPHORIC"


class CorrectableDefectKind(str, Enum):
    NONMATERIAL_OR_DUPLICATE_DUTY = "NONMATERIAL_OR_DUPLICATE_DUTY"
    INCOMPATIBLE_SENTENCE_LOAD = "INCOMPATIBLE_SENTENCE_LOAD"
    DEPENDENCY_OR_INFORMATION_ORDER = "DEPENDENCY_OR_INFORMATION_ORDER"
    UNRESOLVED_OR_DISTANT_REFERENT = "UNRESOLVED_OR_DISTANT_REFERENT"
    TOPIC_OR_SPEAKER_PLACEMENT = "TOPIC_OR_SPEAKER_PLACEMENT"
    RELATION_OR_CONNECTIVE_FIT = "RELATION_OR_CONNECTIVE_FIT"
    SUBJECTIVE_SEQUENCE_FIT = "SUBJECTIVE_SEQUENCE_FIT"
    TERMINAL_FIT = "TERMINAL_FIT"


class NormalFormPhase(str, Enum):
    SUPPRESSION = "SUPPRESSION"
    SEED_CONSTRAINED_MERGE_SPLIT = "SEED_CONSTRAINED_MERGE_SPLIT"
    DEPENDENCY_INFORMATION_ORDER = "DEPENDENCY_INFORMATION_ORDER"
    REFERENCE_ANTECEDENT_RECALCULATION = "REFERENCE_ANTECEDENT_RECALCULATION"
    TOPIC_SPEAKER_CONNECTIVE_TERMINAL = "TOPIC_SPEAKER_CONNECTIVE_TERMINAL"
    EXPRESSION_SELECTION_FINAL_LINEARIZATION = (
        "EXPRESSION_SELECTION_FINAL_LINEARIZATION"
    )


class ProfileFit(str, Enum):
    ARC_ALIGNED = "ARC_ALIGNED"
    PERMITTED = "PERMITTED"
    NOT_APPLICABLE = "NOT_APPLICABLE"


class ProfileEvidenceField(str, Enum):
    INFORMATION_FLOW = "INFORMATION_FLOW"
    CONCRETE_BEFORE_ABSTRACT = "CONCRETE_BEFORE_ABSTRACT"
    SENTENCE_LOAD = "SENTENCE_LOAD"
    TOPIC_TRANSITION = "TOPIC_TRANSITION"
    REFERENT_CONTINUITY = "REFERENT_CONTINUITY"
    RELATION_REALIZATION = "RELATION_REALIZATION"
    SUBJECTIVE_SEQUENCE = "SUBJECTIVE_SEQUENCE"
    TERMINAL = "TERMINAL"


class ProfileEvidenceRuleKind(str, Enum):
    ARC_DEPENDENCY = "ARC_DEPENDENCY"
    CONCRETE_INTRODUCTION = "CONCRETE_INTRODUCTION"
    PREDICATION_LOAD = "PREDICATION_LOAD"
    TOPIC_STATE = "TOPIC_STATE"
    REFERENT_STATE = "REFERENT_STATE"
    RELATION_REALIZATION = "RELATION_REALIZATION"
    SUBJECTIVE_DEPENDENCY = "SUBJECTIVE_DEPENDENCY"
    TERMINAL_DUTY = "TERMINAL_DUTY"


class SubjectiveResponsibilityKind(str, Enum):
    AFFECTIVE_RESPONSE = "AFFECTIVE_RESPONSE"
    MATERIAL_APPRAISAL = "MATERIAL_APPRAISAL"
    POLICY_VISIBLE_VALUE = "POLICY_VISIBLE_VALUE"
    RELATIONAL_POSITION = "RELATIONAL_POSITION"


class SubjectiveSpecificity(str, Enum):
    RELATION_BOUND_MULTI_ROLE = "RELATION_BOUND_MULTI_ROLE"
    MULTI_ROLE = "MULTI_ROLE"
    SINGLE_ROLE = "SINGLE_ROLE"


class SubjectiveFacetSuppressionReason(str, Enum):
    NONMATERIAL = "NONMATERIAL"
    DUPLICATE = "DUPLICATE"
    ABSORBED_ATTENTION = "ABSORBED_ATTENTION"


@dataclass(frozen=True, slots=True)
class CandidateFrameRow:
    candidate_ref: str
    grounded_frame: Any


@dataclass(frozen=True, slots=True)
class RelationEndpointCandidateRow:
    relation_candidate_ref: str
    source_argument_role: ArgumentRole
    source_semantic_ref: str
    endpoint_grounded_candidate_ref: str


@dataclass(frozen=True, slots=True)
class QualifierValueRow:
    candidate_ref: str
    qualifier_scope: QualifierLookupScope
    source_argument_role: Optional[ArgumentRole]
    source_semantic_ref: Optional[str]
    axis: ClauseScalarAxis
    value: str


@dataclass(frozen=True, slots=True)
class RetainedReceptionActRow:
    act_ref: str
    reception_act: str
    basis_contribution_refs: Tuple[str, ...]


@dataclass(frozen=True, slots=True)
class Stage1SubjectivePlanningInputs:
    admitted_source: Any
    grounded_graph: Any
    grounded_plan: Any
    parent_plan: Any
    projection_preimage_ref: str
    interpretation_candidate_rows: Tuple[EmlisInterpretationCandidate, ...]
    meaning_field: Any
    observation_contribution_rows: Tuple[PlannedObservationContribution, ...]
    retained_reception_act_rows: Tuple[RetainedReceptionActRow, ...]
    material_unknown_refs: Tuple[str, ...]
    observation_depth_class: Any
    temperature_class: Any
    reception_style_policy_ref: str
    emlis_value_policy_ref: str
    contribution_to_candidate_ref_map: Tuple[Tuple[str, str], ...]
    resolved_grounded_frame_by_candidate_ref: Tuple[CandidateFrameRow, ...]
    relation_endpoint_grounded_candidate_ref_by_binding_key: Tuple[
        RelationEndpointCandidateRow, ...
    ]
    qualifier_value_by_candidate_scope_axis_key: Tuple[QualifierValueRow, ...]
    construction_registry_snapshot: Tuple[Any, ...]
    expression_asset_registry_snapshot: Tuple[Any, ...]
    response_object_registry_snapshot: Tuple[Any, ...]
    functional_asset_registry_snapshot: Tuple[Any, ...]
    participant_asset_registry_snapshot: Tuple[Any, ...]
    structural_asset_registry_snapshot: Tuple[Any, ...]
    profile_rule_registry_snapshot: Tuple[Any, ...]


@dataclass(frozen=True, slots=True)
class Stage1SurfaceCompositionInputs:
    admitted_source: Any
    grounded_graph: Any
    grounded_plan: Any
    parent_plan: Any
    projection: Any
    resolved_grounded_frame_by_candidate_ref: Tuple[CandidateFrameRow, ...]
    relation_endpoint_grounded_candidate_ref_by_binding_key: Tuple[
        RelationEndpointCandidateRow, ...
    ]
    qualifier_value_by_candidate_scope_axis_key: Tuple[QualifierValueRow, ...]
    addressee_deictic_context: bool
    section_speaker_owner_ref: Optional[str]
    construction_registry_snapshot: Tuple[Any, ...]
    expression_asset_registry_snapshot: Tuple[Any, ...]
    response_object_registry_snapshot: Tuple[Any, ...]
    functional_asset_registry_snapshot: Tuple[Any, ...]
    participant_asset_registry_snapshot: Tuple[Any, ...]
    structural_asset_registry_snapshot: Tuple[Any, ...]
    profile_rule_registry_snapshot: Tuple[Any, ...]


@dataclass(frozen=True, slots=True)
class SubjectiveResponsibilityRow:
    responsibility_ref: str
    responsibility_kind: SubjectiveResponsibilityKind
    owner_component_refs: Tuple[str, ...]
    retained_reception_act_refs: Tuple[str, ...]


@dataclass(frozen=True, slots=True)
class SubjectiveOpportunityRow:
    opportunity_key: str
    responsibility_refs: Tuple[str, ...]
    content_kind: SubjectiveContentKind
    content: Any
    specificity_key: SubjectiveSpecificity


@dataclass(frozen=True, slots=True)
class ResponsibilityCoverageRow:
    responsibility_ref: str
    reception_act_refs: Tuple[str, ...]
    covered_by_claim_refs: Tuple[str, ...]


@dataclass(frozen=True, slots=True)
class SubjectiveFacetSuppressionRow:
    suppressed_opportunity_key: str
    reason: SubjectiveFacetSuppressionReason
    absorbed_by_selected_opportunity_key: Optional[str]


@dataclass(frozen=True, slots=True)
class PolicyApplicationRow:
    policy_application_row_ref: str
    application_kind: str
    principle_ref: str
    material_risk: MaterialRisk
    policy_basis_binding_refs: Tuple[str, ...]
    affected_claim_ref: str
    visible_claim_ref: Optional[str]


@dataclass(frozen=True, slots=True)
class ProjectedSubjectiveClaim:
    schema_version: str
    subjective_claim_id: str
    parent_duty_ref: str
    speaker_owner: str
    claim_domain: str
    subjective_responsibility_refs: Tuple[str, ...]
    selected_subjective_opportunity_key: str
    asserted_subjective_proposition: SubjectivePropositionV2
    basis_observation_contribution_refs: Tuple[str, ...]
    basis_semantic_refs: Tuple[str, ...]
    source_reception_act_refs: Tuple[str, ...]
    value_principle_refs: Tuple[str, ...]
    user_fact_effect: int
    forbidden_promotions: Tuple[str, ...]


@dataclass(frozen=True, slots=True)
class EmlisSubjectiveMeaningPlan:
    projection_preimage_ref: str
    subjective_claim_rows: Tuple[ProjectedSubjectiveClaim, ...]
    thought_support_status: str
    content_bearing_thought_claim_refs: Tuple[str, ...]
    retained_reception_act_refs: Tuple[str, ...]
    subjective_responsibility_rows: Tuple[SubjectiveResponsibilityRow, ...]
    subjective_opportunity_rows: Tuple[SubjectiveOpportunityRow, ...]
    responsibility_coverage_rows: Tuple[ResponsibilityCoverageRow, ...]
    subjective_basis_binding_rows: Tuple[SubjectiveBasisBinding, ...]
    source_qualifier_binding_rows: Tuple[SourceQualifierBinding, ...]
    policy_basis_binding_rows: Tuple[PolicyBasisBinding, ...]
    policy_application_rows: Tuple[PolicyApplicationRow, ...]
    subjective_facet_suppression_rows: Tuple[SubjectiveFacetSuppressionRow, ...]


@dataclass(frozen=True, slots=True)
class ArcDependencyRow:
    arc_dependency_ref: str
    predecessor_owner_ref: str
    successor_owner_ref: str
    dependency_kind: ArcDependencyKind
    source_relation_ref: Optional[str]


@dataclass(frozen=True, slots=True)
class Stage1DiscourseArcView:
    arc_ref: str
    projection_ref: str
    nucleus_owner_refs: Tuple[str, ...]
    supporting_owner_refs: Tuple[str, ...]
    admitted_relation_refs: Tuple[str, ...]
    dependency_rows: Tuple[ArcDependencyRow, ...]
    root_owner_refs: Tuple[str, ...]
    unresolved_or_residue_refs: Tuple[str, ...]
    terminal_owner_refs: Tuple[str, ...]
    layer2_response_target_refs: Tuple[str, ...]


@dataclass(frozen=True, slots=True)
class CompositionDutyView:
    duty_ref: str
    projection_ref: str
    layer: str
    sentence_job: SentenceJob
    basis_projection_refs: Tuple[str, ...]
    relation_refs: Tuple[str, ...]
    response_object_refs: Tuple[str, ...]
    retention: str


@dataclass(frozen=True, slots=True)
class ConstructionSpec:
    construction_id: str
    argument_slots: Tuple[ClauseArgumentRole, ...]
    role_order: Tuple[ClauseArgumentRole, ...]
    valency: PredicateValency
    particle_rules: Tuple[Tuple[ClauseArgumentRole, str], ...]
    auxiliary_rules: Tuple[str, ...]
    relation_combinators: Tuple[RelationOperator, ...]
    inflection_order: Tuple[str, ...]


@dataclass(frozen=True, slots=True)
class GrammaticalShapeKey:
    semantic_clause_kind: SemanticClauseKind
    sentence_job: SentenceJob
    required_argument_roles: Tuple[ClauseArgumentRole, ...]
    grammatical_role_assignment_rule: GrammaticalRoleAssignmentRule
    predicate_valency: PredicateValency
    admitted_relation_operator: RelationOperator
    scalar_shape_rows: Tuple[Tuple[ClauseScalarAxis, str], ...]
    syntactic_orientation: SyntacticOrientation


@dataclass(frozen=True, slots=True)
class ClauseScalarConstraintRow:
    clause_scalar_constraint_ref: str
    owner_ref: str
    clause_argument_role: Optional[ClauseArgumentRole]
    polarity: str
    modality: str
    time_scope: str


@dataclass(frozen=True, slots=True)
class ScalarSurfaceRealizationRow:
    clause_scalar_constraint_ref: str
    scalar_axis: ClauseScalarAxis
    realization_mode: ScalarSurfaceRealizationMode
    registered_realization_rule_ref: str
    target_clause_slot_ref: Optional[str]


@dataclass(frozen=True, slots=True)
class ExpressionAssetSpec:
    expression_asset_id: str
    sentence_job: SentenceJob
    semantic_clause_kind: SemanticClauseKind
    predicate_key: str
    predicate_lexemes: Tuple[str, ...]
    compatible_valencies: Tuple[PredicateValency, ...]


@dataclass(frozen=True, slots=True)
class RelationMorphologyAssetSpec:
    morphology_asset_id: str
    relation_operator: RelationOperator
    left_particle: str
    connective: str
    right_particle: str


@dataclass(frozen=True, slots=True)
class ScalarMorphologyAssetSpec:
    morphology_asset_id: str
    scalar_axis: ClauseScalarAxis
    compatible_values: Tuple[str, ...]
    realization_mode: ScalarSurfaceRealizationMode
    realization_target_slot_ref: Optional[str]
    morphemes: Tuple[str, ...]


@dataclass(frozen=True, slots=True)
class SourceScalarMorphologyAssetSpec:
    morphology_asset_id: str
    predicate_kind: str
    required_attribute_codes: Tuple[str, ...]
    terminal_rewrites: Tuple[Tuple[str, str], ...]
    preserved_finite_terminals: Tuple[str, ...]


@dataclass(frozen=True, slots=True)
class ParticipantLexemeAssetSpec:
    participant_ref: str
    surface_lexeme: str


@dataclass(frozen=True, slots=True)
class StructuralSurfaceAssetSpec:
    structural_asset_id: str
    surface_lexeme: str


@dataclass(frozen=True, slots=True)
class ClausePlan:
    clause_plan_ref: str
    duty_ref: str
    semantic_clause_kind: SemanticClauseKind
    predicate_valency: PredicateValency
    grammatical_role_assignment_rule: GrammaticalRoleAssignmentRule
    syntactic_orientation: SyntacticOrientation
    speaker_requirement: SpeakerRequirement
    construction_id: str
    scalar_constraint_rows: Tuple[ClauseScalarConstraintRow, ...]
    scalar_surface_realization_rows: Tuple[ScalarSurfaceRealizationRow, ...]


@dataclass(frozen=True, slots=True)
class ResponseObjectExpression:
    response_object_expression_ref: str
    clause_plan_ref: str
    unit_ref: str
    basis_semantic_refs: Tuple[str, ...]
    relation_refs: Tuple[str, ...]
    expression_mode: ResponseObjectExpressionMode
    antecedent_unit_ref: Optional[str]


@dataclass(frozen=True, slots=True)
class DutyGroupRow:
    ordered_duty_refs: Tuple[str, ...]


@dataclass(frozen=True, slots=True)
class LayoutPreferenceSeed:
    opening_duty_ref: str
    layer1_group_rows: Tuple[DutyGroupRow, ...]
    layer2_group_rows: Tuple[DutyGroupRow, ...]
    subjective_progression_duty_refs: Tuple[str, ...]
    terminal_duty_ref: str


@dataclass(frozen=True, slots=True)
class CorrectableDefectRow:
    defect_kind: CorrectableDefectKind
    defect_owner_refs: Tuple[str, ...]


@dataclass(frozen=True, slots=True)
class ComposedSentenceUnit:
    unit_ref: str
    layer: str
    duty_refs: Tuple[str, ...]
    sentence_job_refs: Tuple[str, ...]
    basis_anchor_refs: Tuple[str, ...]
    clause_plan_refs: Tuple[str, ...]
    text: str
    surface_text_sha256: str


@dataclass(frozen=True, slots=True)
class DraftArtifact:
    projection_ref: str
    discourse_arc: Stage1DiscourseArcView
    layout_preference_seed: LayoutPreferenceSeed
    composition_duty_rows: Tuple[CompositionDutyView, ...]
    full_duty_refs: Tuple[str, ...]
    required_duty_refs: Tuple[str, ...]
    suppressed_duty_rows: Tuple[Any, ...]
    suppressed_claim_rows: Tuple[Any, ...]
    clause_plan_rows: Tuple[ClausePlan, ...]
    response_object_expression_rows: Tuple[ResponseObjectExpression, ...]
    sentence_units: Tuple[ComposedSentenceUnit, ...]
    correctable_defect_rows: Tuple[CorrectableDefectRow, ...]


@dataclass(frozen=True, slots=True)
class NormalizedDraftArtifact:
    projection_ref: str
    discourse_arc: Stage1DiscourseArcView
    layout_preference_seed: LayoutPreferenceSeed
    composition_duty_rows: Tuple[CompositionDutyView, ...]
    full_duty_refs: Tuple[str, ...]
    required_duty_refs: Tuple[str, ...]
    suppressed_duty_rows: Tuple[Any, ...]
    suppressed_claim_rows: Tuple[Any, ...]
    clause_plan_rows: Tuple[ClausePlan, ...]
    response_object_expression_rows: Tuple[ResponseObjectExpression, ...]
    sentence_units: Tuple[ComposedSentenceUnit, ...]
    correctable_defect_rows: Tuple[CorrectableDefectRow, ...]
    normal_form_version: str
    normal_form_applied: bool
    normalization_phase_trace: Tuple[NormalFormPhase, ...]


@dataclass(frozen=True, slots=True)
class ProfileEvidenceRow:
    profile_evidence_ref: str
    profile_field: ProfileEvidenceField
    rule_kind: ProfileEvidenceRuleKind
    evidence_owner_refs: Tuple[str, ...]
    preferred_form_ref: str
    observed_form_ref: str
    result: ProfileFit


@dataclass(frozen=True, slots=True)
class DiscoursePreferenceProfile:
    information_flow_fit: ProfileFit
    concrete_before_abstract_fit: ProfileFit
    sentence_load_fit: ProfileFit
    topic_transition_fit: ProfileFit
    referent_continuity_fit: ProfileFit
    relation_realization_fit: ProfileFit
    subjective_sequence_fit: ProfileFit
    terminal_fit: ProfileFit
    profile_evidence_rows: Tuple[ProfileEvidenceRow, ...]


@dataclass(frozen=True, slots=True)
class ArtifactCompositionCandidate:
    artifact_composition_candidate_id: str
    composition_signature: str
    rank: int
    shared_variant_id: str
    normalized_artifact: NormalizedDraftArtifact
    discourse_preference_profile: DiscoursePreferenceProfile
    sentence_units: Tuple[ComposedSentenceUnit, ...]


@dataclass(frozen=True, slots=True)
class Stage1CompositionResult:
    language_core_identity: str
    discourse_arc: Stage1DiscourseArcView
    internal_candidate_count: int
    ranked_candidates: Tuple[ArtifactCompositionCandidate, ...]
    selected_candidate: ArtifactCompositionCandidate


def _ref(prefix: str, value: Any) -> str:
    return f"{prefix}-{hashlib.sha256(stage1_canonical_json_bytes(value)).hexdigest()}"


def _unique(values: Iterable[str]) -> Tuple[str, ...]:
    return tuple(dict.fromkeys(values))


def _projection_ref(projection: Any) -> str:
    try:
        if (
            type(projection) is not EmlisStage1Projection
            or projection.schema_version != CMEE_STAGE1_RESPONSE_SCHEMA_VERSION
            or not projection.projection_id
        ):
            raise Stage1CompositionError("STAGE1_PROJECTION_IDENTITY_STOP")
        validate_stage1_identity(projection)
    except Exception:
        raise Stage1CompositionError("STAGE1_PROJECTION_IDENTITY_STOP") from None
    return (
        f"projection:{projection.projection_id}"
        f"@{CMEE_STAGE1_RESPONSE_SCHEMA_VERSION}"
    )


def _claims(projection: Any) -> Tuple[Any, ...]:
    return tuple(getattr(projection, "subjective_claims", ()))


def _contributions(projection: Any) -> Tuple[PlannedObservationContribution, ...]:
    rows = tuple(getattr(projection, "observation_contributions", ()))
    if not rows:
        raise Stage1CompositionError("STAGE1_COMPOSITION_EMPTY_PROJECTION_STOP")
    return rows


def _prop(claim: Any) -> Any:
    return getattr(claim, "asserted_subjective_proposition")


def _content_kind(claim: Any) -> SubjectiveContentKind:
    proposition = _prop(claim)
    if type(proposition) is not SubjectivePropositionV2:
        raise Stage1CompositionError("STAGE1_SUBJECTIVE_PROPOSITION_V2_STOP")
    return proposition.content_kind


def _expected_registry_snapshots() -> Tuple[Tuple[Any, ...], ...]:
    return (
        CONSTRUCTION_REGISTRY,
        EXPRESSION_ASSET_REGISTRY,
        RESPONSE_OBJECT_ASSET_REGISTRY,
        FUNCTIONAL_ASSET_REGISTRY,
        PARTICIPANT_ASSET_REGISTRY,
        STRUCTURAL_ASSET_REGISTRY,
        PROFILE_RULE_REGISTRY,
    )


def _validate_registry_snapshots(value: Any) -> None:
    stored = (
        value.construction_registry_snapshot,
        value.expression_asset_registry_snapshot,
        value.response_object_registry_snapshot,
        value.functional_asset_registry_snapshot,
        value.participant_asset_registry_snapshot,
        value.structural_asset_registry_snapshot,
        value.profile_rule_registry_snapshot,
    )
    if stored != _expected_registry_snapshots():
        raise Stage1CompositionError("LANGUAGE_CORE_REGISTRY_SNAPSHOT_STOP")


def _candidate_qualifier_value(
    candidate: EmlisInterpretationCandidate,
    axis: ClauseScalarAxis,
    role: Optional[ArgumentRole],
) -> str:
    prefix = "" if role is None else f"{role.value.lower()}_"
    marker = f"{prefix}{axis.value.lower()}:"
    values = tuple(
        item[len(marker) :]
        for item in candidate.required_qualifiers
        if item.startswith(marker)
    )
    if len(values) != 1 or not values[0]:
        raise Stage1CompositionError("STAGE1_QUALIFIER_CLOSURE_STOP")
    return values[0]


def _validate_frozen_semantic_maps(
    *,
    projection: Any,
    frame_rows: Tuple[CandidateFrameRow, ...],
    endpoint_rows: Tuple[RelationEndpointCandidateRow, ...],
    qualifier_rows: Tuple[QualifierValueRow, ...],
) -> None:
    candidates = tuple(getattr(projection, "interpretation_candidates", ()))
    if not candidates or len({row.candidate_id for row in candidates}) != len(candidates):
        raise Stage1CompositionError("STAGE1_CANDIDATE_CLOSURE_STOP")
    candidate_by_id = {row.candidate_id: row for row in candidates}
    direct = tuple(
        row
        for row in candidates
        if row.relation_operator is RelationOperator.NO_RELATION_CLAIM
    )
    if (
        len({row.candidate_ref for row in frame_rows}) != len(frame_rows)
        or {row.candidate_ref for row in frame_rows}
        != {row.candidate_id for row in direct}
    ):
        raise Stage1CompositionError("STAGE1_GROUNDED_FRAME_CLOSURE_STOP")
    frame_by_id = {row.candidate_ref: row.grounded_frame for row in frame_rows}
    for candidate in direct:
        primary = tuple(
            row
            for row in candidate.argument_bindings
            if row.role is ArgumentRole.PRIMARY
        )
        if len(primary) != 1:
            raise Stage1CompositionError("STAGE1_SOURCE_BINDING_CLOSURE_STOP")
        frame = frame_by_id[candidate.candidate_id]
        scalar_values = (
            str(getattr(frame, "polarity", "")),
            str(getattr(frame, "modality", "")),
            str(getattr(frame, "time_scope", "")),
        )
        expected_values = tuple(
            _candidate_qualifier_value(candidate, axis, None)
            for axis in ClauseScalarAxis
        )
        if scalar_values != expected_values:
            raise Stage1CompositionError("STAGE1_GROUNDED_FRAME_CLOSURE_STOP")

    expected_endpoint_keys: list[Tuple[str, ArgumentRole, str]] = []
    for candidate in candidates:
        if candidate.relation_operator is RelationOperator.NO_RELATION_CLAIM:
            continue
        for binding in candidate.argument_bindings:
            expected_endpoint_keys.append(
                (candidate.candidate_id, binding.role, binding.semantic_ref)
            )
    actual_endpoint_keys = tuple(
        (
            row.relation_candidate_ref,
            row.source_argument_role,
            row.source_semantic_ref,
        )
        for row in endpoint_rows
    )
    if (
        len(set(actual_endpoint_keys)) != len(actual_endpoint_keys)
        or set(actual_endpoint_keys) != set(expected_endpoint_keys)
    ):
        raise Stage1CompositionError("STAGE1_RELATION_ENDPOINT_CLOSURE_STOP")
    for row in endpoint_rows:
        direct_candidate = candidate_by_id.get(row.endpoint_grounded_candidate_ref)
        if (
            direct_candidate is None
            or direct_candidate.relation_operator
            is not RelationOperator.NO_RELATION_CLAIM
            or not any(
                binding.role is ArgumentRole.PRIMARY
                and binding.semantic_ref == row.source_semantic_ref
                for binding in direct_candidate.argument_bindings
            )
        ):
            raise Stage1CompositionError("STAGE1_RELATION_ENDPOINT_CLOSURE_STOP")

    expected_qualifiers: list[QualifierValueRow] = []
    for candidate in candidates:
        relation = candidate.relation_operator is not RelationOperator.NO_RELATION_CLAIM
        bindings = (
            tuple(candidate.argument_bindings)
            if relation
            else (None,)
        )
        for binding in bindings:
            role = None if binding is None else binding.role
            semantic_ref = None if binding is None else binding.semantic_ref
            for axis in ClauseScalarAxis:
                expected_qualifiers.append(
                    QualifierValueRow(
                        candidate.candidate_id,
                        QualifierLookupScope.RELATION_SOURCE_BINDING
                        if relation
                        else QualifierLookupScope.DIRECT_UNQUALIFIED,
                        role,
                        semantic_ref,
                        axis,
                        _candidate_qualifier_value(candidate, axis, role),
                    )
                )
    if tuple(qualifier_rows) != tuple(expected_qualifiers):
        raise Stage1CompositionError("STAGE1_QUALIFIER_CLOSURE_STOP")


def _validate_phase_lineage(value: Any, *, projection: Any) -> None:
    source = value.admitted_source
    graph = value.grounded_graph
    parent = value.parent_plan
    if (
        getattr(getattr(source, "envelope", None), "envelope_id", None)
        != getattr(graph, "source_envelope_id", None)
        or getattr(graph, "source_envelope_id", None)
        != getattr(parent, "source_envelope_id", None)
        or getattr(projection, "grounded_graph_ref", None)
        not in {
            None,
            f"grounded:{getattr(graph, 'graph_id', '')}"
            f"@{CMEE_GROUNDED_GRAPH_SCHEMA_VERSION}",
        }
        or getattr(projection, "parent_observation_duty_ref", None)
        != getattr(parent, "observation_duty_id", None)
        or getattr(projection, "parent_reception_duty_ref", None)
        != getattr(parent, "reception_duty_id", None)
    ):
        raise Stage1CompositionError("STAGE1_COMPOSITION_LINEAGE_STOP")
    # The graph schema and response schema are intentionally different, so
    # closure is checked on the stable local node identity rather than by
    # fabricating a version-qualified ref.
    local_node_ids = {row.node_id for row in getattr(graph, "nodes", ())}
    for candidate in getattr(projection, "interpretation_candidates", ()):
        for binding in candidate.argument_bindings:
            if _semantic_ref_node_id(binding.semantic_ref) not in local_node_ids:
                raise Stage1CompositionError("STAGE1_COMPOSITION_LINEAGE_STOP")


def _validate_phase_A(phase_A: Stage1SubjectivePlanningInputs) -> None:
    _validate_registry_snapshots(phase_A)
    projection_view = type(
        "_PhaseAProjectionClosure",
        (),
        {
            "interpretation_candidates": phase_A.interpretation_candidate_rows,
            "parent_observation_duty_ref": phase_A.parent_plan.observation_duty_id,
            "parent_reception_duty_ref": phase_A.parent_plan.reception_duty_id,
            "schema_version": CMEE_STAGE1_RESPONSE_SCHEMA_VERSION,
        },
    )()
    _validate_phase_lineage(phase_A, projection=projection_view)
    contribution_ids = {
        row.contribution_id for row in phase_A.observation_contribution_rows
    }
    candidate_ids = {
        row.candidate_id for row in phase_A.interpretation_candidate_rows
    }
    retained_act_refs = tuple(
        row.act_ref for row in phase_A.retained_reception_act_rows
    )
    if (
        not phase_A.projection_preimage_ref
        or not candidate_ids
        or not contribution_ids
        or len(candidate_ids) != len(phase_A.interpretation_candidate_rows)
        or len(contribution_ids) != len(phase_A.observation_contribution_rows)
        or len(phase_A.contribution_to_candidate_ref_map) != len(contribution_ids)
        or set(dict(phase_A.contribution_to_candidate_ref_map)) != contribution_ids
        or phase_A.material_unknown_refs
        != tuple(getattr(phase_A.meaning_field, "material_unknown_refs", ()))
        or not retained_act_refs
        or len(retained_act_refs) != len(set(retained_act_refs))
        or retained_act_refs
        != tuple(getattr(phase_A.parent_plan, "allowed_reception_act_ids", ()))
    ):
        raise Stage1CompositionError("STAGE1_CONTRIBUTION_CANDIDATE_CLOSURE_STOP")
    if any(
        candidate_ref not in candidate_ids
        for _contribution_ref, candidate_ref in phase_A.contribution_to_candidate_ref_map
    ) or any(
        not row.basis_contribution_refs
        or not set(row.basis_contribution_refs).issubset(contribution_ids)
        for row in phase_A.retained_reception_act_rows
    ):
        raise Stage1CompositionError("STAGE1_CONTRIBUTION_CANDIDATE_CLOSURE_STOP")
    _validate_frozen_semantic_maps(
        projection=projection_view,
        frame_rows=phase_A.resolved_grounded_frame_by_candidate_ref,
        endpoint_rows=phase_A.relation_endpoint_grounded_candidate_ref_by_binding_key,
        qualifier_rows=phase_A.qualifier_value_by_candidate_scope_axis_key,
    )


def _validate_phase_B(phase_B: Stage1SurfaceCompositionInputs) -> None:
    _validate_registry_snapshots(phase_B)
    _validate_phase_lineage(phase_B, projection=phase_B.projection)
    _projection_ref(phase_B.projection)
    if type(phase_B.addressee_deictic_context) is not bool:
        raise Stage1CompositionError("STAGE1_COMPOSITION_DEICTIC_CONTEXT_STOP")
    claims = _claims(phase_B.projection)
    if (
        not 1 <= len(claims) <= 4
        or any(
            type(claim) is not EmlisSubjectiveClaim
            or claim.schema_version != CMEE_STAGE1_RESPONSE_SCHEMA_VERSION
            or claim.speaker_owner != CMEE_STAGE1_EMLIS_OWNER_REF
            or type(claim.asserted_subjective_proposition)
            is not SubjectivePropositionV2
            or claim.subjective_mode
            is not claim.asserted_subjective_proposition.subjective_mode
            for claim in claims
        )
        or tuple(phase_B.projection.ordered_observation_refs)
        != tuple(
            row.contribution_id
            for row in phase_B.projection.observation_contributions
        )
        or tuple(phase_B.projection.ordered_subjective_refs)
        != tuple(claim.subjective_claim_id for claim in claims)
    ):
        raise Stage1CompositionError("STAGE1_FINAL_PROJECTION_CLOSURE_STOP")
    expected_speaker = CMEE_STAGE1_EMLIS_OWNER_REF if claims else None
    if phase_B.section_speaker_owner_ref != expected_speaker:
        raise Stage1CompositionError("STAGE1_COMPOSITION_SPEAKER_OWNER_STOP")
    _validate_frozen_semantic_maps(
        projection=phase_B.projection,
        frame_rows=phase_B.resolved_grounded_frame_by_candidate_ref,
        endpoint_rows=phase_B.relation_endpoint_grounded_candidate_ref_by_binding_key,
        qualifier_rows=phase_B.qualifier_value_by_candidate_scope_axis_key,
    )


_ROLE_TO_BASIS = {
    ArgumentRole.LEFT: SubjectiveBasisRole.RELATION_LEFT,
    ArgumentRole.RIGHT: SubjectiveBasisRole.RELATION_RIGHT,
    ArgumentRole.ACTION: SubjectiveBasisRole.ACTION,
    ArgumentRole.CHANGE: SubjectiveBasisRole.CHANGE,
    ArgumentRole.BEFORE: SubjectiveBasisRole.BEFORE,
    ArgumentRole.AFTER: SubjectiveBasisRole.AFTER,
    ArgumentRole.CAUSE: SubjectiveBasisRole.RELATION_LEFT,
    ArgumentRole.EFFECT: SubjectiveBasisRole.RELATION_RIGHT,
}


def _basis_role(row: PlannedObservationContribution, role: ArgumentRole) -> SubjectiveBasisRole:
    if role in _ROLE_TO_BASIS:
        return _ROLE_TO_BASIS[role]
    if row.semantic_operator is SemanticOperator.PRESENT_DIRECTION:
        return SubjectiveBasisRole.CHOICE_TARGET
    if row.semantic_operator is SemanticOperator.PRESENT_RESIDUE:
        return SubjectiveBasisRole.RESIDUE
    if row.semantic_operator is SemanticOperator.PRESENT_UNFINISHED:
        return SubjectiveBasisRole.UNFINISHED
    return SubjectiveBasisRole.APPRAISED_OBJECT


def _qualifier_lookup(
    phase_A: Stage1SubjectivePlanningInputs,
    candidate: EmlisInterpretationCandidate,
    binding: Any,
) -> Tuple[str, str, str, Optional[ArgumentRole]]:
    relation = candidate.relation_operator is not RelationOperator.NO_RELATION_CLAIM
    scope = (
        QualifierLookupScope.RELATION_SOURCE_BINDING
        if relation
        else QualifierLookupScope.DIRECT_UNQUALIFIED
    )
    role = binding.role if relation else None
    semantic_ref = binding.semantic_ref if relation else None
    values = []
    for axis in ClauseScalarAxis:
        rows = tuple(
            row
            for row in phase_A.qualifier_value_by_candidate_scope_axis_key
            if row.candidate_ref == candidate.candidate_id
            and row.qualifier_scope is scope
            and row.source_argument_role is role
            and row.source_semantic_ref == semantic_ref
            and row.axis is axis
        )
        if len(rows) != 1 or not rows[0].value:
            raise Stage1CompositionError("STAGE1_QUALIFIER_CLOSURE_STOP")
        values.append(rows[0].value)
    return values[0], values[1], values[2], role


def _selected_basis(
    basis_rows: Sequence[SubjectiveBasisBinding],
    contribution_refs: Sequence[str],
) -> Tuple[SubjectiveBasisBinding, ...]:
    selected = tuple(row for row in basis_rows if row.contribution_ref in set(contribution_refs))
    if not selected:
        raise Stage1CompositionError("GENERIC_SUBJECTIVE_CONTENT_STOP")
    return selected


def _opportunity_owner_component_refs(
    opportunity: SubjectiveOpportunityRow,
    responsibility_by_ref: Mapping[str, SubjectiveResponsibilityRow],
) -> Tuple[str, ...]:
    rows = tuple(
        responsibility_by_ref.get(ref)
        for ref in opportunity.responsibility_refs
    )
    if not rows or any(row is None for row in rows):
        raise Stage1CompositionError("SUBJECTIVE_OPPORTUNITY_PARTITION_STOP")
    return _unique(
        owner_ref
        for row in rows
        if row is not None
        for owner_ref in row.owner_component_refs
    )


def _select_generic_affect_absorber(
    *,
    opportunities: Sequence[SubjectiveOpportunityRow],
    responsibility_by_ref: Mapping[str, SubjectiveResponsibilityRow],
    selected_opportunity_keys: set[str],
    target_contribution_refs: Tuple[str, ...],
) -> Optional[SubjectiveOpportunityRow]:
    """Select the exact typed same-target absorber without row-order policy."""

    for preferred_kind in (
        SubjectiveContentKind.RELATIONAL_POSITION,
        SubjectiveContentKind.APPRAISAL,
    ):
        matches = tuple(
            row
            for row in opportunities
            if row.opportunity_key in selected_opportunity_keys
            and row.content_kind is preferred_kind
            and _opportunity_owner_component_refs(
                row,
                responsibility_by_ref,
            )
            == target_contribution_refs
        )
        if len(matches) > 1:
            raise Stage1CompositionError(
                "SUBJECTIVE_OPPORTUNITY_PARTITION_STOP"
            )
        if matches:
            return matches[0]
    return None


def _validate_subjective_opportunity_partition(
    *,
    responsibilities: Sequence[SubjectiveResponsibilityRow],
    opportunities: Sequence[SubjectiveOpportunityRow],
    claims: Sequence[ProjectedSubjectiveClaim],
    coverage: Sequence[ResponsibilityCoverageRow],
    suppressions: Sequence[SubjectiveFacetSuppressionRow],
) -> None:
    responsibility_by_ref = {
        row.responsibility_ref: row for row in responsibilities
    }
    opportunity_by_key = {row.opportunity_key: row for row in opportunities}
    coverage_by_ref = {row.responsibility_ref: row for row in coverage}
    selected_keys = tuple(
        row.selected_subjective_opportunity_key for row in claims
    )
    suppressed_keys = tuple(
        row.suppressed_opportunity_key for row in suppressions
    )
    flattened_responsibility_refs = tuple(
        ref for row in opportunities for ref in row.responsibility_refs
    )
    if (
        not claims
        or len(responsibility_by_ref) != len(responsibilities)
        or len(opportunity_by_key) != len(opportunities)
        or len(coverage_by_ref) != len(coverage)
        or set(coverage_by_ref) != set(responsibility_by_ref)
        or len(selected_keys) != len(set(selected_keys))
        or len(suppressed_keys) != len(set(suppressed_keys))
        or set(selected_keys).intersection(suppressed_keys)
        or set((*selected_keys, *suppressed_keys)) != set(opportunity_by_key)
        or any(
            type(row.responsibility_refs) is not tuple
            or not row.responsibility_refs
            or len(row.responsibility_refs)
            != len(set(row.responsibility_refs))
            or any(
                ref not in responsibility_by_ref
                for ref in row.responsibility_refs
            )
            for row in opportunities
        )
        or flattened_responsibility_refs
        != tuple(row.responsibility_ref for row in responsibilities)
    ):
        raise Stage1CompositionError("SUBJECTIVE_OPPORTUNITY_PARTITION_STOP")

    for claim in claims:
        opportunity = opportunity_by_key.get(
            claim.selected_subjective_opportunity_key
        )
        proposition = claim.asserted_subjective_proposition
        selected_content = {
            SubjectiveContentKind.AFFECT: proposition.affect_content,
            SubjectiveContentKind.APPRAISAL: proposition.appraisal_content,
            SubjectiveContentKind.MATERIAL_VALUE: (
                proposition.material_value_content
            ),
            SubjectiveContentKind.RELATIONAL_POSITION: (
                proposition.relational_position
            ),
        }.get(proposition.content_kind)
        if (
            opportunity is None
            or claim.subjective_responsibility_refs
            != opportunity.responsibility_refs
            or any(
                ref not in responsibility_by_ref
                for ref in claim.subjective_responsibility_refs
            )
            or opportunity.content_kind is not proposition.content_kind
            or opportunity.content != selected_content
            or _opportunity_owner_component_refs(
                opportunity,
                responsibility_by_ref,
            )
            != proposition.target_contribution_refs
            or proposition.target_contribution_refs
            != claim.basis_observation_contribution_refs
        ):
            raise Stage1CompositionError(
                "SUBJECTIVE_OPPORTUNITY_PARTITION_STOP"
            )
    for responsibility in responsibilities:
        coverage_row = coverage_by_ref[responsibility.responsibility_ref]
        expected_claim_refs = tuple(
            claim.subjective_claim_id
            for claim in claims
            if responsibility.responsibility_ref
            in claim.subjective_responsibility_refs
        )
        if (
            coverage_row.reception_act_refs
            != responsibility.retained_reception_act_refs
            or coverage_row.covered_by_claim_refs != expected_claim_refs
        ):
            raise Stage1CompositionError(
                "SUBJECTIVE_OPPORTUNITY_PARTITION_STOP"
            )

    suppression_by_key = {
        row.suppressed_opportunity_key: row for row in suppressions
    }
    for affect_opportunity in (
        row
        for row in opportunities
        if row.content_kind is SubjectiveContentKind.AFFECT
    ):
        expected_absorber = _select_generic_affect_absorber(
            opportunities=opportunities,
            responsibility_by_ref=responsibility_by_ref,
            selected_opportunity_keys=set(selected_keys),
            target_contribution_refs=_opportunity_owner_component_refs(
                affect_opportunity,
                responsibility_by_ref,
            ),
        )
        suppression = suppression_by_key.get(
            affect_opportunity.opportunity_key
        )
        if (
            expected_absorber is not None
            and (
                affect_opportunity.opportunity_key in set(selected_keys)
                or suppression is None
                or suppression.absorbed_by_selected_opportunity_key
                != expected_absorber.opportunity_key
            )
        ) or (
            expected_absorber is None
            and (
                affect_opportunity.opportunity_key not in set(selected_keys)
                or suppression is not None
            )
        ):
            raise Stage1CompositionError(
                "SUBJECTIVE_OPPORTUNITY_PARTITION_STOP"
            )

    for suppression in suppressions:
        suppressed = opportunity_by_key[suppression.suppressed_opportunity_key]
        absorber = opportunity_by_key.get(
            suppression.absorbed_by_selected_opportunity_key or ""
        )
        expected_absorber = _select_generic_affect_absorber(
            opportunities=opportunities,
            responsibility_by_ref=responsibility_by_ref,
            selected_opportunity_keys=set(selected_keys),
            target_contribution_refs=_opportunity_owner_component_refs(
                suppressed,
                responsibility_by_ref,
            ),
        )
        if (
            suppression.reason
            is not SubjectiveFacetSuppressionReason.ABSORBED_ATTENTION
            or suppressed.content_kind is not SubjectiveContentKind.AFFECT
            or absorber is None
            or absorber.opportunity_key not in set(selected_keys)
            or absorber.content_kind
            not in {
                SubjectiveContentKind.APPRAISAL,
                SubjectiveContentKind.RELATIONAL_POSITION,
            }
            or expected_absorber is None
            or absorber.opportunity_key != expected_absorber.opportunity_key
            or _opportunity_owner_component_refs(
                suppressed,
                responsibility_by_ref,
            )
            != _opportunity_owner_component_refs(
                absorber,
                responsibility_by_ref,
            )
            or any(
                coverage_by_ref[ref].covered_by_claim_refs
                for ref in suppressed.responsibility_refs
            )
        ):
            raise Stage1CompositionError(
                "SUBJECTIVE_OPPORTUNITY_PARTITION_STOP"
            )


_RISK_BY_PRINCIPLE = dict(
    zip(
        (ref for _code, ref in CMEE_STAGE1_VALUE_PRINCIPLE_REFS),
        tuple(MaterialRisk),
        strict=True,
    )
)


def project_subjective_meaning_plan(
    phase_A: Stage1SubjectivePlanningInputs,
) -> EmlisSubjectiveMeaningPlan:
    """Sole Phase-A projector for request-local Emlis subjective meaning."""

    if type(phase_A) is not Stage1SubjectivePlanningInputs:
        raise Stage1CompositionError("STAGE1_COMPOSITION_PHASE_A_TYPE_STOP")
    _validate_phase_A(phase_A)
    contributions = phase_A.observation_contribution_rows
    candidates = {row.candidate_id: row for row in phase_A.interpretation_candidate_rows}
    contribution_candidate = dict(phase_A.contribution_to_candidate_ref_map)
    if set(contribution_candidate) != {row.contribution_id for row in contributions}:
        raise Stage1CompositionError("STAGE1_CONTRIBUTION_CANDIDATE_CLOSURE_STOP")
    basis_rows: list[SubjectiveBasisBinding] = []
    qualifier_rows: list[SourceQualifierBinding] = []
    for contribution in contributions:
        candidate = candidates.get(contribution_candidate[contribution.contribution_id])
        if candidate is None:
            raise Stage1CompositionError("STAGE1_CONTRIBUTION_CANDIDATE_CLOSURE_STOP")
        for binding in candidate.argument_bindings:
            if binding.role is ArgumentRole.EXPERIENCER:
                continue
            role = _basis_role(contribution, binding.role)
            basis_ref = project_stage1_subjective_basis_binding_ref(
                projection_preimage_ref=phase_A.projection_preimage_ref,
                contribution_ref=contribution.contribution_id,
                semantic_ref=binding.semantic_ref,
                role=role,
            )
            basis = SubjectiveBasisBinding(
                phase_A.projection_preimage_ref,
                basis_ref,
                contribution.contribution_id,
                binding.semantic_ref,
                role,
            )
            polarity, modality, time_scope, qualifier_role = _qualifier_lookup(
                phase_A, candidate, binding
            )
            prefix = "" if qualifier_role is None else f"{qualifier_role.value.lower()}_"
            codes = (
                f"{prefix}polarity:{polarity}",
                f"{prefix}modality:{modality}",
                f"{prefix}time_scope:{time_scope}",
            )
            qualifier_ref = project_stage1_source_qualifier_binding_ref(
                projection_preimage_ref=phase_A.projection_preimage_ref,
                basis_binding_ref=basis_ref,
                source_candidate_ref=candidate.candidate_id,
                source_argument_role=qualifier_role,
                canonical_qualifier_codes=codes,
                polarity=polarity,
                modality=modality,
                time_scope=time_scope,
            )
            basis_rows.append(basis)
            qualifier_rows.append(
                SourceQualifierBinding(
                    phase_A.projection_preimage_ref,
                    qualifier_ref,
                    basis_ref,
                    candidate.candidate_id,
                    qualifier_role,
                    codes,
                    polarity,
                    modality,
                    time_scope,
                )
            )
    if not basis_rows:
        raise Stage1CompositionError("GENERIC_SUBJECTIVE_CONTENT_STOP")
    act_refs = tuple(row.act_ref for row in phase_A.retained_reception_act_rows)
    act_codes = tuple(row.reception_act for row in phase_A.retained_reception_act_rows)
    allowed_acts = {row.reception_act for row in CMEE_STAGE1_RECEPTION_ACT_MAPPING_EXACT7}
    if not act_refs or len(set(act_refs)) != len(act_refs) or not set(act_codes) <= allowed_acts:
        raise Stage1CompositionError("STAGE1_RECEPTION_ACT_CLOSURE_STOP")

    policy_basis_rows: list[PolicyBasisBinding] = []
    for contribution in contributions:
        if contribution.semantic_operator in {SemanticOperator.PRESENT_BURDEN, SemanticOperator.PRESENT_RESIDUE}:
            role = PolicyBasisRole.BURDEN_OR_RESIDUE
        elif contribution.semantic_operator is SemanticOperator.PRESENT_DIRECTION:
            role = PolicyBasisRole.DIRECTION
        elif contribution.semantic_operator in {SemanticOperator.PRESENT_CHANGE, SemanticOperator.PRESENT_ACTUAL_OUTPUT}:
            role = PolicyBasisRole.CHANGE_OR_ACTUAL_OUTPUT
        elif contribution.semantic_operator is SemanticOperator.PRESENT_UNFINISHED:
            role = PolicyBasisRole.UNFINISHED
        else:
            role = PolicyBasisRole.COEXISTENCE_OR_TENSION
        ref = project_stage1_policy_basis_binding_ref(
            projection_preimage_ref=phase_A.projection_preimage_ref,
            owner_kind=PolicyBasisOwnerKind.CONTRIBUTION,
            owner_ref=contribution.contribution_id,
            role=role,
        )
        policy_basis_rows.append(
            PolicyBasisBinding(
                phase_A.projection_preimage_ref,
                ref,
                PolicyBasisOwnerKind.CONTRIBUTION,
                contribution.contribution_id,
                role,
            )
        )
    for unknown_ref in phase_A.material_unknown_refs:
        ref = project_stage1_policy_basis_binding_ref(
            projection_preimage_ref=phase_A.projection_preimage_ref,
            owner_kind=PolicyBasisOwnerKind.MATERIAL_UNKNOWN,
            owner_ref=unknown_ref,
            role=PolicyBasisRole.MATERIAL_UNKNOWN,
        )
        policy_basis_rows.append(
            PolicyBasisBinding(
                phase_A.projection_preimage_ref,
                ref,
                PolicyBasisOwnerKind.MATERIAL_UNKNOWN,
                unknown_ref,
                PolicyBasisRole.MATERIAL_UNKNOWN,
            )
        )

    def unique_material_owner(
        rows: Iterable[PlannedObservationContribution],
    ) -> Optional[PlannedObservationContribution]:
        selected = tuple(rows)
        if len(selected) > 1:
            raise Stage1CompositionError("SUBJECTIVE_MEANING_NONUNIQUE_STOP")
        return selected[0] if selected else None

    action_change = unique_material_owner(
        row
        for row in contributions
        if row.relation_operator is RelationOperator.ACTION_PRECEDES_CHANGE
    )
    noncollapse = unique_material_owner(
        row
        for row in contributions
        if row.relation_operator
        in {RelationOperator.COEXISTS_WITH, RelationOperator.TENSION_WITH}
    )
    open_unfinished = unique_material_owner(
        row
        for row in contributions
        if row.semantic_operator is SemanticOperator.PRESENT_UNFINISHED
        or row.contribution_kind
        is ObservationContributionKind.PRESERVE_UNFINISHED
    )
    residue = unique_material_owner(
        row
        for row in contributions
        if row.semantic_operator is SemanticOperator.PRESENT_RESIDUE
        or row.contribution_kind is ObservationContributionKind.PRESERVE_RESIDUE
    )
    unfinished = open_unfinished or residue
    direction = unique_material_owner(
        row
        for row in contributions
        if row.semantic_operator is SemanticOperator.PRESENT_DIRECTION
    )
    change = unique_material_owner(
        row
        for row in contributions
        if row.semantic_operator
        in {SemanticOperator.PRESENT_CHANGE, SemanticOperator.PRESENT_ACTUAL_OUTPUT}
        and row is not action_change
    )
    burden = unique_material_owner(
        row
        for row in contributions
        if row.semantic_operator is SemanticOperator.PRESENT_BURDEN
    )
    focus = (
        open_unfinished
        or action_change
        or noncollapse
        or residue
        or direction
        or change
        or burden
    )
    if focus is None:
        raise Stage1CompositionError("GENERIC_SUBJECTIVE_CONTENT_STOP")
    selected_basis = _selected_basis(basis_rows, (focus.contribution_id,))
    primary_refs = _unique(row.semantic_ref for row in selected_basis)
    focal_relation_ref = (
        focus.relation_basis_refs[0]
        if focus.relation_operator is not RelationOperator.NO_RELATION_CLAIM
        and focus.relation_basis_refs
        else None
    )

    claim_specs: list[tuple[SubjectiveContentKind, Any, tuple[str, ...]]] = []
    if focus is noncollapse:
        appraisal = EmlisAppraisalContent(
            AppraisalDimension.RELATIONAL_NONCOLLAPSE,
            AppraisalOperation.PRESERVE_BOTH_ENDPOINTS,
            tuple(row.binding_ref for row in selected_basis),
            focal_relation_ref,
            (),
            (focus.contribution_id,),
        )
    elif focus is open_unfinished or focus is residue:
        appraisal = EmlisAppraisalContent(
            AppraisalDimension.UNFINISHED_OPENNESS,
            AppraisalOperation.LEAVE_UNFINISHED,
            tuple(row.binding_ref for row in selected_basis),
            focal_relation_ref,
            (),
            (focus.contribution_id,),
        )
    elif focus is action_change or focus is change:
        appraisal = EmlisAppraisalContent(
            AppraisalDimension.BOUNDED_CHANGE,
            AppraisalOperation.RECOGNIZE_AS_BOUNDED,
            tuple(row.binding_ref for row in selected_basis),
            focal_relation_ref,
            (),
            (focus.contribution_id,),
        )
    elif direction:
        appraisal = EmlisAppraisalContent(
            AppraisalDimension.AGENCY_BOUNDARY,
            AppraisalOperation.RESPECT_CHOICE,
            tuple(row.binding_ref for row in selected_basis),
            focal_relation_ref,
            (),
            (focus.contribution_id,),
        )
    else:
        appraisal = EmlisAppraisalContent(
            AppraisalDimension.MATERIAL_WEIGHT,
            AppraisalOperation.RECEIVE_AS_MATERIAL,
            tuple(row.binding_ref for row in selected_basis),
            focal_relation_ref,
            (),
            (focus.contribution_id,),
        )
    claim_specs.append((SubjectiveContentKind.APPRAISAL, appraisal, (focus.contribution_id,)))

    if unfinished or direction:
        target = unfinished or direction
        stance_basis = _selected_basis(basis_rows, (target.contribution_id,))
        position = EmlisRelationalPosition(
            RelationalPositionKind.STANCE,
            StanceOperator.HOLD_UNFINISHED_OPEN if unfinished else StanceOperator.PROTECT_USER_AGENCY,
            tuple(row.binding_ref for row in stance_basis),
            (),
            RelationalCommitment.HOLD_OPEN if unfinished else RelationalCommitment.PROTECT_AGENCY,
            RelationalClosure.OPEN if unfinished else RelationalClosure.BOUNDED,
        )
        claim_specs.append((SubjectiveContentKind.RELATIONAL_POSITION, position, (target.contribution_id,)))

    visible_principles: list[str] = []
    for act in phase_A.retained_reception_act_rows:
        act_contributions = tuple(
            row
            for row in contributions
            if not act.basis_contribution_refs
            or row.contribution_id in set(act.basis_contribution_refs)
        )
        visible_principles.extend(
            _stage1_material_visible_value_refs(
                reception_act=act.reception_act,
                contributions=act_contributions,
            )
        )
    visible_principles = list(_unique(visible_principles))

    affect_category = (
        AffectCategory.RELIEF
        if change
        else AffectCategory.RESPECT
        if direction or "honor_concrete_effort" in act_codes or "respect_words_placed" in act_codes
        else AffectCategory.CONCERN
    )
    affect = EmlisAffectContent(
        affect_category,
        AffectIntensity.QUIET,
        tuple(row.binding_ref for row in selected_basis),
    )
    claim_specs.append((SubjectiveContentKind.AFFECT, affect, (focus.contribution_id,)))
    claim_specs = claim_specs[:4]

    responsibilities: list[SubjectiveResponsibilityRow] = []
    opportunities: list[SubjectiveOpportunityRow] = []
    claims: list[ProjectedSubjectiveClaim] = []
    policy_applications: list[PolicyApplicationRow] = []
    suppressions: list[SubjectiveFacetSuppressionRow] = []
    for index, (kind, content, contribution_refs) in enumerate(claim_specs):
        responsibility_kind = {
            SubjectiveContentKind.AFFECT: SubjectiveResponsibilityKind.AFFECTIVE_RESPONSE,
            SubjectiveContentKind.APPRAISAL: SubjectiveResponsibilityKind.MATERIAL_APPRAISAL,
            SubjectiveContentKind.MATERIAL_VALUE: SubjectiveResponsibilityKind.POLICY_VISIBLE_VALUE,
            SubjectiveContentKind.RELATIONAL_POSITION: SubjectiveResponsibilityKind.RELATIONAL_POSITION,
        }[kind]
        responsibility_ref = _ref(
            "subjective-responsibility",
            (phase_A.projection_preimage_ref, responsibility_kind, contribution_refs, act_refs),
        )
        opportunity_key = _ref(
            "subjective-opportunity",
            (phase_A.projection_preimage_ref, kind, content, contribution_refs),
        )
        responsibilities.append(
            SubjectiveResponsibilityRow(
                responsibility_ref, responsibility_kind, contribution_refs, act_refs
            )
        )
        opportunities.append(
            SubjectiveOpportunityRow(
                opportunity_key,
                (responsibility_ref,),
                kind,
                content,
                SubjectiveSpecificity.RELATION_BOUND_MULTI_ROLE
                if focal_relation_ref
                else SubjectiveSpecificity.MULTI_ROLE
                if len(primary_refs) > 1
                else SubjectiveSpecificity.SINGLE_ROLE,
            )
        )
        if kind is SubjectiveContentKind.AFFECT:
            responsibility_by_ref = {
                row.responsibility_ref: row for row in responsibilities
            }
            selected_keys = {
                claim.selected_subjective_opportunity_key for claim in claims
            }
            absorber = _select_generic_affect_absorber(
                opportunities=opportunities[:-1],
                responsibility_by_ref=responsibility_by_ref,
                selected_opportunity_keys=selected_keys,
                target_contribution_refs=contribution_refs,
            )
            if absorber is not None:
                suppressions.append(
                    SubjectiveFacetSuppressionRow(
                        opportunity_key,
                        SubjectiveFacetSuppressionReason.ABSORBED_ATTENTION,
                        absorber.opportunity_key,
                    )
                )
                continue
        own_basis = _selected_basis(basis_rows, contribution_refs)
        own_qualifier_refs = tuple(
            row.source_qualifier_binding_ref
            for row in qualifier_rows
            if row.basis_binding_ref in {basis.binding_ref for basis in own_basis}
        )
        own_primary = _unique(row.semantic_ref for row in own_basis)
        relation_position = content if kind is SubjectiveContentKind.RELATIONAL_POSITION else None
        proposition = SubjectivePropositionV2(
            CMEE_STAGE1_SUBJECTIVE_PROPOSITION_SCHEMA_VERSION,
            kind,
            {
                SubjectiveContentKind.AFFECT: SubjectiveMode.AFFECTIVE_RESPONSE,
                SubjectiveContentKind.APPRAISAL: SubjectiveMode.PERSONAL_APPRAISAL,
                SubjectiveContentKind.MATERIAL_VALUE: SubjectiveMode.VALUE_POSITION,
                SubjectiveContentKind.RELATIONAL_POSITION: SubjectiveMode.RELATIONAL_STANCE,
            }[kind],
            {
                SubjectiveContentKind.AFFECT: SubjectiveOperator.FEEL_TOWARD,
                SubjectiveContentKind.APPRAISAL: SubjectiveOperator.APPRAISE_AS_MATERIAL,
                SubjectiveContentKind.MATERIAL_VALUE: SubjectiveOperator.PROTECT_VALUE_BOUNDARY,
                SubjectiveContentKind.RELATIONAL_POSITION: SubjectiveOperator.TAKE_RELATIONAL_STANCE,
            }[kind],
            contribution_refs,
            own_primary,
            (),
            own_primary,
            tuple(row.binding_ref for row in own_basis),
            own_qualifier_refs,
            focal_relation_ref if kind is SubjectiveContentKind.APPRAISAL else None,
            content if kind is SubjectiveContentKind.AFFECT else None,
            content if kind is SubjectiveContentKind.APPRAISAL else None,
            content if kind is SubjectiveContentKind.MATERIAL_VALUE else None,
            relation_position,
            (),
            (),
            "USER",
            {
                SubjectiveContentKind.AFFECT: SubjectiveAssertionModality.EMLIS_FEELING,
                SubjectiveContentKind.APPRAISAL: SubjectiveAssertionModality.EMLIS_APPRAISAL,
                SubjectiveContentKind.MATERIAL_VALUE: SubjectiveAssertionModality.EMLIS_VALUE_POSITION,
                SubjectiveContentKind.RELATIONAL_POSITION: SubjectiveAssertionModality.EMLIS_RELATIONAL_INTENTION,
            }[kind],
            "REQUEST_LOCAL_EMLIS_SUBJECTIVITY",
        )
        forbidden = stage1_subjective_forbidden_promotions(
            tuple(row for row in contributions if row.contribution_id in set(contribution_refs)),
            material_unknown_refs=phase_A.material_unknown_refs,
        )
        claim_id = _ref(
            "subjective-claim",
            (
                phase_A.projection_preimage_ref,
                CMEE_STAGE1_RESPONSE_SCHEMA_VERSION,
                phase_A.parent_plan.reception_duty_id,
                CMEE_STAGE1_EMLIS_OWNER_REF,
                "EMLIS_SUBJECTIVE_RESPONSE",
                (responsibility_ref,),
                opportunity_key,
                proposition,
                contribution_refs,
                own_primary,
                act_refs,
                (),
                0,
                forbidden,
            ),
        )
        claims.append(
            ProjectedSubjectiveClaim(
                CMEE_STAGE1_RESPONSE_SCHEMA_VERSION,
                claim_id,
                phase_A.parent_plan.reception_duty_id,
                CMEE_STAGE1_EMLIS_OWNER_REF,
                "EMLIS_SUBJECTIVE_RESPONSE",
                (responsibility_ref,),
                opportunity_key,
                proposition,
                contribution_refs,
                own_primary,
                act_refs,
                (),
                0,
                forbidden,
            )
        )

    # Material visibility becomes its own content-bearing claim only when the
    # current policy returns a concrete visible principle and budget remains.
    if visible_principles and len(claims) < 4:
        own_basis = tuple(basis_rows)
        policy_refs = tuple(
            row.binding_ref
            for row in policy_basis_rows
            if row.owner_kind is PolicyBasisOwnerKind.CONTRIBUTION
        )
        application_ref_by_principle = {
            ref: _ref(
                "policy-application",
                (
                    phase_A.projection_preimage_ref,
                    "VISIBILITY",
                    ref,
                    policy_refs,
                    tuple(row.binding_ref for row in own_basis),
                ),
            )
            for ref in visible_principles
        }
        applications = tuple(
            ValueApplication(
                ref,
                _RISK_BY_PRINCIPLE[ref],
                (application_ref_by_principle[ref],),
                policy_refs,
                tuple(row.binding_ref for row in own_basis),
            )
            for ref in visible_principles
        )
        value_content = MaterialValueContent(
            applications, tuple(row.binding_ref for row in own_basis), ()
        )
        responsibility_ref = _ref("subjective-responsibility", (phase_A.projection_preimage_ref, "VALUE", visible_principles))
        opportunity_key = _ref("subjective-opportunity", (phase_A.projection_preimage_ref, value_content))
        proposition = SubjectivePropositionV2(
            CMEE_STAGE1_SUBJECTIVE_PROPOSITION_SCHEMA_VERSION,
            SubjectiveContentKind.MATERIAL_VALUE,
            SubjectiveMode.VALUE_POSITION,
            SubjectiveOperator.PROTECT_VALUE_BOUNDARY,
            _unique(row.contribution_ref for row in own_basis),
            _unique(row.semantic_ref for row in own_basis),
            (),
            _unique(row.semantic_ref for row in own_basis),
            tuple(row.binding_ref for row in own_basis),
            tuple(row.source_qualifier_binding_ref for row in qualifier_rows),
            None,
            None,
            None,
            value_content,
            None,
            (),
            (),
            "USER",
            SubjectiveAssertionModality.EMLIS_VALUE_POSITION,
            "REQUEST_LOCAL_EMLIS_SUBJECTIVITY",
        )
        forbidden = stage1_subjective_forbidden_promotions(contributions, material_unknown_refs=phase_A.material_unknown_refs)
        value_contribution_refs = _unique(
            row.contribution_ref for row in own_basis
        )
        value_semantic_refs = _unique(row.semantic_ref for row in own_basis)
        claim_id = _ref(
            "subjective-claim",
            (
                phase_A.projection_preimage_ref,
                CMEE_STAGE1_RESPONSE_SCHEMA_VERSION,
                phase_A.parent_plan.reception_duty_id,
                CMEE_STAGE1_EMLIS_OWNER_REF,
                "EMLIS_SUBJECTIVE_RESPONSE",
                (responsibility_ref,),
                opportunity_key,
                proposition,
                value_contribution_refs,
                value_semantic_refs,
                act_refs,
                tuple(visible_principles),
                0,
                forbidden,
            ),
        )
        responsibilities.append(SubjectiveResponsibilityRow(responsibility_ref, SubjectiveResponsibilityKind.POLICY_VISIBLE_VALUE, tuple(row.contribution_id for row in contributions), act_refs))
        opportunities.append(SubjectiveOpportunityRow(opportunity_key, (responsibility_ref,), SubjectiveContentKind.MATERIAL_VALUE, value_content, SubjectiveSpecificity.MULTI_ROLE))
        claims.append(ProjectedSubjectiveClaim(CMEE_STAGE1_RESPONSE_SCHEMA_VERSION, claim_id, phase_A.parent_plan.reception_duty_id, CMEE_STAGE1_EMLIS_OWNER_REF, "EMLIS_SUBJECTIVE_RESPONSE", (responsibility_ref,), opportunity_key, proposition, value_contribution_refs, value_semantic_refs, act_refs, tuple(visible_principles), 0, forbidden))
        for principle in visible_principles:
            row_ref = application_ref_by_principle[principle]
            policy_applications.append(PolicyApplicationRow(row_ref, "VISIBILITY", principle, _RISK_BY_PRINCIPLE[principle], policy_refs, claim_id, claim_id))

    coverage = tuple(
        ResponsibilityCoverageRow(
            row.responsibility_ref,
            row.retained_reception_act_refs,
            tuple(
                claim.subjective_claim_id
                for claim in claims
                if row.responsibility_ref in claim.subjective_responsibility_refs
            ),
        )
        for row in responsibilities
    )
    thought_refs = tuple(
        claim.subjective_claim_id
        for claim in claims
        if claim.asserted_subjective_proposition.content_kind is not SubjectiveContentKind.AFFECT
    )
    _validate_subjective_opportunity_partition(
        responsibilities=responsibilities,
        opportunities=opportunities,
        claims=claims,
        coverage=coverage,
        suppressions=suppressions,
    )
    return EmlisSubjectiveMeaningPlan(
        phase_A.projection_preimage_ref,
        tuple(claims),
        "SUPPORTED" if thought_refs else "NOT_SUPPORTED",
        thought_refs,
        act_refs,
        tuple(responsibilities),
        tuple(opportunities),
        coverage,
        tuple(basis_rows),
        tuple(qualifier_rows),
        tuple(policy_basis_rows),
        tuple(policy_applications),
        tuple(suppressions),
    )


_ORDERED_RELATION_ARGUMENT_ROLES = {
    RelationOperator.COEXISTS_WITH: (ArgumentRole.LEFT, ArgumentRole.RIGHT),
    RelationOperator.TENSION_WITH: (ArgumentRole.LEFT, ArgumentRole.RIGHT),
    RelationOperator.TEMPORALLY_PRECEDES: (
        ArgumentRole.BEFORE,
        ArgumentRole.AFTER,
    ),
    RelationOperator.ACTION_PRECEDES_CHANGE: (
        ArgumentRole.ACTION,
        ArgumentRole.CHANGE,
    ),
    RelationOperator.SOURCE_EXPLICIT_CAUSE: (
        ArgumentRole.CAUSE,
        ArgumentRole.EFFECT,
    ),
}


def _relation_refs(contribution: PlannedObservationContribution) -> Tuple[str, ...]:
    relation = contribution.relation_operator
    refs = tuple(contribution.relation_basis_refs)
    if relation is RelationOperator.NO_RELATION_CLAIM:
        if refs:
            raise Stage1CompositionError("STAGE1_RELATION_CARDINALITY_STOP")
        return ()
    if relation not in _ORDERED_RELATION_ARGUMENT_ROLES or len(refs) != 1:
        raise Stage1CompositionError("STAGE1_RELATION_CARDINALITY_STOP")
    return refs


def _ordered_relation_endpoint_refs(
    contribution: PlannedObservationContribution,
) -> Tuple[str, str]:
    expected_roles = _ORDERED_RELATION_ARGUMENT_ROLES.get(
        contribution.relation_operator
    )
    if expected_roles is None:
        raise Stage1CompositionError("STAGE1_RELATION_DIRECTION_STOP")
    bindings = tuple(contribution.argument_bindings)
    if (
        len(bindings) != 2
        or tuple(row.role for row in bindings) != expected_roles
        or len({row.semantic_ref for row in bindings}) != 2
        or any(not row.semantic_ref for row in bindings)
    ):
        raise Stage1CompositionError("STAGE1_RELATION_DIRECTION_STOP")
    _relation_refs(contribution)
    return bindings[0].semantic_ref, bindings[1].semantic_ref


def _append_arc_dependency(
    rows: list[ArcDependencyRow],
    *,
    projection_ref: str,
    predecessor_owner_ref: str,
    successor_owner_ref: str,
    dependency_kind: ArcDependencyKind,
    source_relation_ref: Optional[str],
) -> None:
    if (
        not predecessor_owner_ref
        or not successor_owner_ref
        or predecessor_owner_ref == successor_owner_ref
        or (source_relation_ref is not None)
        != (dependency_kind is ArcDependencyKind.ADMITTED_RELATION_DIRECTION)
    ):
        raise Stage1CompositionError("STAGE1_ARC_DEPENDENCY_STOP")
    row = ArcDependencyRow(
        _ref(
            "arc-dependency",
            (
                projection_ref,
                predecessor_owner_ref,
                successor_owner_ref,
                dependency_kind,
                source_relation_ref,
            ),
        ),
        predecessor_owner_ref,
        successor_owner_ref,
        dependency_kind,
        source_relation_ref,
    )
    typed_key = (
        row.predecessor_owner_ref,
        row.successor_owner_ref,
        row.dependency_kind,
        row.source_relation_ref,
    )
    if any(
        (
            prior.predecessor_owner_ref,
            prior.successor_owner_ref,
            prior.dependency_kind,
            prior.source_relation_ref,
        )
        == typed_key
        for prior in rows
    ):
        raise Stage1CompositionError("STAGE1_ARC_DEPENDENCY_DUPLICATE_STOP")
    rows.append(row)


def project_stage1_discourse_arc(
    phase_B: Stage1SurfaceCompositionInputs,
) -> Stage1DiscourseArcView:
    """Sole Phase-B projection of the frozen material meaning arc."""

    if type(phase_B) is not Stage1SurfaceCompositionInputs:
        raise Stage1CompositionError("STAGE1_COMPOSITION_PHASE_B_TYPE_STOP")
    _validate_phase_B(phase_B)
    projection = phase_B.projection
    projection_ref = _projection_ref(projection)
    contributions = _contributions(projection)
    claims = _claims(projection)
    nucleus = tuple(row.contribution_id for row in contributions)
    relations = _unique(
        ref
        for row in contributions
        if row.relation_operator is not RelationOperator.NO_RELATION_CLAIM
        for ref in _relation_refs(row)
    )
    dependencies: list[ArcDependencyRow] = []
    for contribution in contributions:
        if contribution.relation_operator is not RelationOperator.NO_RELATION_CLAIM:
            predecessor, successor = _ordered_relation_endpoint_refs(contribution)
            _append_arc_dependency(
                dependencies,
                projection_ref=projection_ref,
                predecessor_owner_ref=predecessor,
                successor_owner_ref=successor,
                dependency_kind=ArcDependencyKind.ADMITTED_RELATION_DIRECTION,
                source_relation_ref=_relation_refs(contribution)[0],
            )
        for predecessor in contribution.prerequisite_contribution_refs:
            _append_arc_dependency(
                dependencies,
                projection_ref=projection_ref,
                predecessor_owner_ref=predecessor,
                successor_owner_ref=contribution.contribution_id,
                dependency_kind=ArcDependencyKind.SOURCE_DEPENDENCY_ORDER,
                source_relation_ref=None,
            )
    for claim in claims:
        claim_ref = claim.subjective_claim_id
        for predecessor in claim.basis_observation_contribution_refs:
            _append_arc_dependency(
                dependencies,
                projection_ref=projection_ref,
                predecessor_owner_ref=predecessor,
                successor_owner_ref=claim_ref,
                dependency_kind=ArcDependencyKind.GROUNDED_BEFORE_SUBJECTIVE,
                source_relation_ref=None,
            )

    early_content_kinds = {
        SubjectiveContentKind.AFFECT,
        SubjectiveContentKind.APPRAISAL,
    }
    late_content_kinds = {
        SubjectiveContentKind.MATERIAL_VALUE,
        SubjectiveContentKind.RELATIONAL_POSITION,
    }
    for predecessor_claim in claims:
        predecessor_prop = _prop(predecessor_claim)
        if predecessor_prop.content_kind not in early_content_kinds:
            continue
        predecessor_basis = set(
            predecessor_claim.basis_observation_contribution_refs
        )
        predecessor_acts = set(predecessor_claim.source_reception_act_refs)
        for successor_claim in claims:
            successor_prop = _prop(successor_claim)
            if (
                successor_prop.content_kind not in late_content_kinds
                or not (
                    predecessor_basis.intersection(
                        successor_claim.basis_observation_contribution_refs
                    )
                    or predecessor_acts.intersection(
                        successor_claim.source_reception_act_refs
                    )
                )
            ):
                continue
            _append_arc_dependency(
                dependencies,
                projection_ref=projection_ref,
                predecessor_owner_ref=predecessor_claim.subjective_claim_id,
                successor_owner_ref=successor_claim.subjective_claim_id,
                dependency_kind=ArcDependencyKind.SUBJECTIVE_CONTENT_DEPENDENCY,
                source_relation_ref=None,
            )

    unresolved = tuple(
        row.contribution_id
        for row in contributions
        if row.semantic_operator is SemanticOperator.PRESENT_UNFINISHED
        or row.contribution_kind
        is ObservationContributionKind.PRESERVE_UNFINISHED
    )
    if not unresolved:
        unresolved = tuple(
            row.contribution_id
            for row in contributions
            if row.semantic_operator is SemanticOperator.PRESENT_RESIDUE
            or row.contribution_kind
            is ObservationContributionKind.PRESERVE_RESIDUE
        )
    terminal: Tuple[str, ...] = ()
    if unresolved:
        closure_claims: list[str] = []
        for unresolved_ref in unresolved:
            matches = tuple(
                claim
                for claim in claims
                if unresolved_ref
                in _prop(claim).target_contribution_refs
                and _content_kind(claim)
                is SubjectiveContentKind.RELATIONAL_POSITION
                and _prop(claim).relational_position is not None
                and (
                    _prop(claim).relational_position.closure
                    is RelationalClosure.OPEN
                    or _prop(claim).relational_position.commitment
                    is RelationalCommitment.HOLD_OPEN
                )
            )
            if len(matches) != 1:
                raise Stage1CompositionError(
                    "STAGE1_UNFINISHED_TERMINAL_CLOSURE_STOP"
                )
            closure = matches[0]
            closure_claims.append(closure.subjective_claim_id)
            for claim in claims:
                if (
                    claim.subjective_claim_id != closure.subjective_claim_id
                    and unresolved_ref
                    in claim.basis_observation_contribution_refs
                ):
                    _append_arc_dependency(
                        dependencies,
                        projection_ref=projection_ref,
                        predecessor_owner_ref=claim.subjective_claim_id,
                        successor_owner_ref=closure.subjective_claim_id,
                        dependency_kind=ArcDependencyKind.UNFINISHED_TERMINAL,
                        source_relation_ref=None,
                    )
        terminal = _unique(closure_claims)

    supporting = _unique(
        ref
        for contribution in contributions
        if contribution.relation_operator
        is not RelationOperator.NO_RELATION_CLAIM
        for ref in _ordered_relation_endpoint_refs(contribution)
    )
    all_owners = _unique(
        (*nucleus, *supporting, *(claim.subjective_claim_id for claim in claims))
    )
    incoming = {row.successor_owner_ref for row in dependencies}
    outgoing = {row.predecessor_owner_ref for row in dependencies}
    roots = tuple(ref for ref in all_owners if ref not in incoming)
    if not terminal:
        terminal = tuple(ref for ref in all_owners if ref not in outgoing)
    if not roots or not terminal:
        raise Stage1CompositionError("STAGE1_DISCOURSE_ARC_BOUNDARY_STOP")
    if any(
        row.predecessor_owner_ref in set(terminal)
        for row in dependencies
    ):
        raise Stage1CompositionError("STAGE1_UNFINISHED_TERMINAL_CLOSURE_STOP")

    adjacency: dict[str, set[str]] = {ref: set() for ref in all_owners}
    for row in dependencies:
        adjacency.setdefault(row.predecessor_owner_ref, set()).add(
            row.successor_owner_ref
        )
        adjacency.setdefault(row.successor_owner_ref, set())
    visiting: set[str] = set()
    visited: set[str] = set()

    def visit(owner_ref: str) -> None:
        if owner_ref in visiting:
            raise Stage1CompositionError("STAGE1_DISCOURSE_DEPENDENCY_CYCLE_STOP")
        if owner_ref in visited:
            return
        visiting.add(owner_ref)
        for successor_ref in adjacency.get(owner_ref, ()):
            visit(successor_ref)
        visiting.remove(owner_ref)
        visited.add(owner_ref)

    for owner_ref in adjacency:
        visit(owner_ref)

    targets = _unique(
        ref
        for claim in claims
        for ref in (
            *_prop(claim).primary_target_refs,
            *_prop(claim).boundary_target_refs,
        )
    )
    if not targets:
        raise Stage1CompositionError("STAGE1_DISCOURSE_RESPONSE_TARGET_STOP")
    arc_material = (
        projection_ref,
        nucleus,
        supporting,
        relations,
        tuple(dependencies),
        roots,
        unresolved,
        terminal,
        targets,
    )
    return Stage1DiscourseArcView(
        _ref("stage1-discourse-arc", arc_material),
        projection_ref,
        nucleus,
        supporting,
        relations,
        tuple(dependencies),
        roots,
        unresolved,
        terminal,
        targets,
    )


def _project_duties(phase_B: Stage1SurfaceCompositionInputs, arc: Stage1DiscourseArcView) -> Tuple[CompositionDutyView, ...]:
    projection = phase_B.projection
    duties: list[CompositionDutyView] = []
    contributions = _contributions(projection)
    relation_rows = tuple(
        row
        for row in contributions
        if row.relation_operator is not RelationOperator.NO_RELATION_CLAIM
    )
    relation_endpoint_refs = {
        semantic_ref
        for row in relation_rows
        for semantic_ref in row.semantic_refs
    }
    for row in contributions:
        if row.relation_operator in {RelationOperator.COEXISTS_WITH, RelationOperator.TENSION_WITH}:
            job = SentenceJob.RELATE_COEXISTING_OR_TENSION
        elif row.relation_operator in {RelationOperator.TEMPORALLY_PRECEDES, RelationOperator.ACTION_PRECEDES_CHANGE, RelationOperator.SOURCE_EXPLICIT_CAUSE}:
            job = SentenceJob.TRACE_CHANGE_OR_SEQUENCE
        elif (
            row.relation_operator is RelationOperator.NO_RELATION_CLAIM
            and set(row.semantic_refs)
            and set(row.semantic_refs).issubset(relation_endpoint_refs)
        ):
            # Direct endpoint owners remain in the frozen projection and are
            # covered by their admitted relation duty.  Re-emitting them as
            # standalone observations would repeat the same source role.
            continue
        elif row.semantic_operator in {SemanticOperator.PRESENT_RESIDUE, SemanticOperator.PRESENT_UNFINISHED} or row.contribution_kind in {ObservationContributionKind.PRESERVE_RESIDUE, ObservationContributionKind.PRESERVE_UNFINISHED}:
            job = SentenceJob.PRESERVE_RESIDUE_OR_UNFINISHED
        else:
            job = SentenceJob.OBSERVE_CENTER
        retention = "OPTIONAL" if row.retention == "OPTIONAL" else "REQUIRED"
        absorbed_endpoint_owners = (
            tuple(
                owner.contribution_id
                for owner in contributions
                if owner.relation_operator is RelationOperator.NO_RELATION_CLAIM
                and owner.contribution_id != row.contribution_id
                and set(owner.semantic_refs)
                and set(owner.semantic_refs).issubset(set(row.semantic_refs))
            )
            if row.relation_operator is not RelationOperator.NO_RELATION_CLAIM
            else ()
        )
        basis_projection_refs = _unique(
            (row.contribution_id, *absorbed_endpoint_owners)
        )
        material = (
            arc.projection_ref,
            "LAYER_1",
            job,
            basis_projection_refs,
            _relation_refs(row),
            row.semantic_refs,
            retention,
        )
        duties.append(
            CompositionDutyView(
                _ref("composition-duty", material),
                arc.projection_ref,
                "LAYER_1",
                job,
                basis_projection_refs,
                _relation_refs(row),
                row.semantic_refs,
                retention,
            )
        )
    for claim in _claims(projection):
        kind = _content_kind(claim)
        if kind is SubjectiveContentKind.AFFECT:
            job = SentenceJob.FEEL_TOWARD_OBJECT
        elif kind is SubjectiveContentKind.APPRAISAL:
            job = SentenceJob.CONSIDER_MATERIAL_MEANING
        elif kind is SubjectiveContentKind.RELATIONAL_POSITION:
            position = getattr(_prop(claim), "relational_position", None)
            job = SentenceJob.STAY_WITH_UNFINISHED if position is not None and position.closure is RelationalClosure.OPEN else SentenceJob.TAKE_MATERIAL_POSITION
        else:
            job = SentenceJob.TAKE_MATERIAL_POSITION
        response_object_refs = _unique(
            (
                *_prop(claim).response_object_refs,
                *_prop(claim).boundary_target_refs,
            )
        )
        material = (arc.projection_ref, "LAYER_2", job, (claim.subjective_claim_id,), (), response_object_refs, "REQUIRED")
        duties.append(CompositionDutyView(_ref("composition-duty", material), arc.projection_ref, "LAYER_2", job, (claim.subjective_claim_id,), (), response_object_refs, "REQUIRED"))
    return tuple(duties)


CONSTRUCTION_REGISTRY = (
    ConstructionSpec(
        "construction:grounded-referent-monadic.v1",
        (ClauseArgumentRole.SUBJECT,),
        (ClauseArgumentRole.SUBJECT,),
        PredicateValency.MONADIC_ARGUMENT,
        ((ClauseArgumentRole.SUBJECT, "は"),),
        ("auxiliary:polite-terminal.v1",),
        (),
        ("argument", "particle", "predicate", "auxiliary"),
    ),
    ConstructionSpec(
        "construction:grounded-actor-target.v1",
        (ClauseArgumentRole.SUBJECT, ClauseArgumentRole.PRIMARY_OBJECT),
        (ClauseArgumentRole.SUBJECT, ClauseArgumentRole.PRIMARY_OBJECT),
        PredicateValency.DYADIC_ACTOR_TARGET,
        (
            (ClauseArgumentRole.SUBJECT, "は"),
            (ClauseArgumentRole.PRIMARY_OBJECT, "を"),
        ),
        ("auxiliary:polite-terminal.v1",),
        (),
        ("subject", "particle", "object", "particle", "predicate", "auxiliary"),
    ),
    ConstructionSpec(
        "construction:subjective-emlis-target.v1",
        (ClauseArgumentRole.SUBJECT, ClauseArgumentRole.PRIMARY_OBJECT),
        (ClauseArgumentRole.SUBJECT, ClauseArgumentRole.PRIMARY_OBJECT),
        PredicateValency.DYADIC_ACTOR_TARGET,
        (
            (ClauseArgumentRole.SUBJECT, "は"),
            (ClauseArgumentRole.PRIMARY_OBJECT, "を"),
        ),
        ("auxiliary:polite-terminal.v1",),
        (),
        ("subject", "particle", "object", "particle", "predicate", "auxiliary"),
    ),
    ConstructionSpec(
        "construction:subjective-emlis-target-boundary.v1",
        (
            ClauseArgumentRole.SUBJECT,
            ClauseArgumentRole.PRIMARY_OBJECT,
            ClauseArgumentRole.SECONDARY_OBJECT,
        ),
        (
            ClauseArgumentRole.SUBJECT,
            ClauseArgumentRole.PRIMARY_OBJECT,
            ClauseArgumentRole.SECONDARY_OBJECT,
        ),
        PredicateValency.TRIADIC_ACTOR_TARGET_BOUNDARY,
        (
            (ClauseArgumentRole.SUBJECT, "は"),
            (ClauseArgumentRole.PRIMARY_OBJECT, "を"),
            (ClauseArgumentRole.SECONDARY_OBJECT, "から"),
        ),
        ("auxiliary:polite-terminal.v1",),
        (),
        (
            "subject",
            "particle",
            "primary",
            "particle",
            "boundary",
            "particle",
            "predicate",
            "auxiliary",
        ),
    ),
    ConstructionSpec(
        "construction:relation-noncollapse.v1",
        (ClauseArgumentRole.LEFT_ENDPOINT, ClauseArgumentRole.RIGHT_ENDPOINT),
        (ClauseArgumentRole.LEFT_ENDPOINT, ClauseArgumentRole.RIGHT_ENDPOINT),
        PredicateValency.DYADIC_RELATION_ENDPOINTS,
        (
            (ClauseArgumentRole.LEFT_ENDPOINT, "と"),
            (ClauseArgumentRole.RIGHT_ENDPOINT, "は"),
        ),
        ("auxiliary:polite-terminal.v1",),
        (RelationOperator.COEXISTS_WITH, RelationOperator.TENSION_WITH),
        ("left", "particle", "right", "particle", "predicate", "auxiliary"),
    ),
    ConstructionSpec(
        "construction:relation-temporal.v1",
        (ClauseArgumentRole.BEFORE_EVENT, ClauseArgumentRole.AFTER_EVENT),
        (ClauseArgumentRole.BEFORE_EVENT, ClauseArgumentRole.AFTER_EVENT),
        PredicateValency.DYADIC_RELATION_ENDPOINTS,
        (
            (ClauseArgumentRole.BEFORE_EVENT, "のあとに"),
            (ClauseArgumentRole.AFTER_EVENT, "が"),
        ),
        ("auxiliary:polite-terminal.v1",),
        (RelationOperator.TEMPORALLY_PRECEDES,),
        ("before", "combinator", "after", "particle", "predicate", "auxiliary"),
    ),
    ConstructionSpec(
        "construction:relation-action-change.v1",
        (ClauseArgumentRole.ACTION_EVENT, ClauseArgumentRole.CHANGE_EVENT),
        (ClauseArgumentRole.ACTION_EVENT, ClauseArgumentRole.CHANGE_EVENT),
        PredicateValency.DYADIC_RELATION_ENDPOINTS,
        (
            (ClauseArgumentRole.ACTION_EVENT, "のあとに"),
            (ClauseArgumentRole.CHANGE_EVENT, "が"),
        ),
        ("auxiliary:polite-terminal.v1",),
        (RelationOperator.ACTION_PRECEDES_CHANGE,),
        ("action", "combinator", "change", "particle", "predicate", "auxiliary"),
    ),
    ConstructionSpec(
        "construction:relation-explicit-cause.v1",
        (ClauseArgumentRole.CAUSE_EVENT, ClauseArgumentRole.EFFECT_EVENT),
        (ClauseArgumentRole.CAUSE_EVENT, ClauseArgumentRole.EFFECT_EVENT),
        PredicateValency.DYADIC_RELATION_ENDPOINTS,
        (
            (ClauseArgumentRole.CAUSE_EVENT, "によって"),
            (ClauseArgumentRole.EFFECT_EVENT, "が"),
        ),
        ("auxiliary:polite-terminal.v1",),
        (RelationOperator.SOURCE_EXPLICIT_CAUSE,),
        ("cause", "combinator", "effect", "particle", "predicate", "auxiliary"),
    ),
)


EXPRESSION_ASSET_REGISTRY = (
    ExpressionAssetSpec("expression:observe-center.v1", SentenceJob.OBSERVE_CENTER, SemanticClauseKind.GROUNDED_PREDICATE, "center", ("今ここに", "表れています"), (PredicateValency.MONADIC_ARGUMENT, PredicateValency.DYADIC_ACTOR_TARGET)),
    ExpressionAssetSpec("expression:observe-direction.v1", SentenceJob.OBSERVE_CENTER, SemanticClauseKind.GROUNDED_PREDICATE, "direction", ("今の向きとして", "表れています"), (PredicateValency.MONADIC_ARGUMENT,)),
    ExpressionAssetSpec("expression:observe-burden.v1", SentenceJob.OBSERVE_CENTER, SemanticClauseKind.GROUNDED_PREDICATE, "burden", ("今の重さとして", "表れています"), (PredicateValency.MONADIC_ARGUMENT,)),
    ExpressionAssetSpec("expression:observe-change.v1", SentenceJob.OBSERVE_CENTER, SemanticClauseKind.GROUNDED_PREDICATE, "bounded-change", ("今回の具体的な変化として", "表れています"), (PredicateValency.MONADIC_ARGUMENT,)),
    ExpressionAssetSpec("expression:relation-coexistence.v1", SentenceJob.RELATE_COEXISTING_OR_TENSION, SemanticClauseKind.ADMITTED_RELATION, "coexistence", ("どちらも保たれたまま", "並んでいます"), (PredicateValency.DYADIC_RELATION_ENDPOINTS,)),
    ExpressionAssetSpec("expression:relation-tension.v1", SentenceJob.RELATE_COEXISTING_OR_TENSION, SemanticClauseKind.ADMITTED_RELATION, "tension", ("一方だけにまとめられず", "並んでいます"), (PredicateValency.DYADIC_RELATION_ENDPOINTS,)),
    ExpressionAssetSpec("expression:relation-sequence.v1", SentenceJob.TRACE_CHANGE_OR_SEQUENCE, SemanticClauseKind.ADMITTED_RELATION, "sequence", ("その順序のまま", "表れています"), (PredicateValency.DYADIC_RELATION_ENDPOINTS,)),
    ExpressionAssetSpec("expression:preserve-unfinished.v1", SentenceJob.PRESERVE_RESIDUE_OR_UNFINISHED, SemanticClauseKind.GROUNDED_PREDICATE, "unfinished", ("まだ閉じていないものとして", "残っています"), (PredicateValency.MONADIC_ARGUMENT,)),
    ExpressionAssetSpec("expression:emlis-affect.v1", SentenceJob.FEEL_TOWARD_OBJECT, SemanticClauseKind.SUBJECTIVE_PREDICATE, "affect", ("静かに", "気にかけています"), (PredicateValency.DYADIC_ACTOR_TARGET,)),
    ExpressionAssetSpec("expression:emlis-appraisal-material.v1", SentenceJob.CONSIDER_MATERIAL_MEANING, SemanticClauseKind.SUBJECTIVE_PREDICATE, "appraisal-material", ("軽く扱えないものとして", "受け止めたいです"), (PredicateValency.DYADIC_ACTOR_TARGET,)),
    ExpressionAssetSpec("expression:emlis-appraisal-noncollapse.v1", SentenceJob.CONSIDER_MATERIAL_MEANING, SemanticClauseKind.SUBJECTIVE_PREDICATE, "appraisal-noncollapse", ("どちらか一方に決めず", "大切に受け止めたいです"), (PredicateValency.DYADIC_ACTOR_TARGET,)),
    ExpressionAssetSpec("expression:emlis-appraisal-change.v1", SentenceJob.CONSIDER_MATERIAL_MEANING, SemanticClauseKind.SUBJECTIVE_PREDICATE, "appraisal-change", ("今回起きた変化として", "大切に受け止めたいです"), (PredicateValency.DYADIC_ACTOR_TARGET,)),
    ExpressionAssetSpec("expression:emlis-appraisal-unfinished.v1", SentenceJob.CONSIDER_MATERIAL_MEANING, SemanticClauseKind.SUBJECTIVE_PREDICATE, "appraisal-unfinished", ("まだ結論にしなくてよいものとして", "受け止めたいです"), (PredicateValency.DYADIC_ACTOR_TARGET,)),
    ExpressionAssetSpec("expression:emlis-appraisal-agency.v1", SentenceJob.CONSIDER_MATERIAL_MEANING, SemanticClauseKind.SUBJECTIVE_PREDICATE, "appraisal-agency", ("本人が選べる向きとして", "大切に受け止めたいです"), (PredicateValency.DYADIC_ACTOR_TARGET,)),
    ExpressionAssetSpec("expression:emlis-value.v1", SentenceJob.TAKE_MATERIAL_POSITION, SemanticClauseKind.SUBJECTIVE_PREDICATE, "material-value", ("決めつけに変えず", "大切にしたいです"), (PredicateValency.DYADIC_ACTOR_TARGET, PredicateValency.TRIADIC_ACTOR_TARGET_BOUNDARY)),
    ExpressionAssetSpec("expression:emlis-position.v1", SentenceJob.TAKE_MATERIAL_POSITION, SemanticClauseKind.SUBJECTIVE_PREDICATE, "position", ("選べる向きとして", "尊重したいです"), (PredicateValency.DYADIC_ACTOR_TARGET, PredicateValency.TRIADIC_ACTOR_TARGET_BOUNDARY)),
    ExpressionAssetSpec("expression:emlis-open-position.v1", SentenceJob.STAY_WITH_UNFINISHED, SemanticClauseKind.SUBJECTIVE_PREDICATE, "open-position", ("急いで閉じず", "一緒に置いていたいです"), (PredicateValency.DYADIC_ACTOR_TARGET, PredicateValency.TRIADIC_ACTOR_TARGET_BOUNDARY)),
)


RELATION_MORPHOLOGY_ASSET_REGISTRY = (
    RelationMorphologyAssetSpec("relation-morphology:coexistence.v1", RelationOperator.COEXISTS_WITH, "と", "", "は"),
    RelationMorphologyAssetSpec("relation-morphology:tension.v1", RelationOperator.TENSION_WITH, "と", "", "は"),
    RelationMorphologyAssetSpec("relation-morphology:temporal.v1", RelationOperator.TEMPORALLY_PRECEDES, "のあとに", "、", "が"),
    RelationMorphologyAssetSpec("relation-morphology:action-change.v1", RelationOperator.ACTION_PRECEDES_CHANGE, "のあとに", "、", "が"),
    RelationMorphologyAssetSpec("relation-morphology:explicit-cause.v1", RelationOperator.SOURCE_EXPLICIT_CAUSE, "によって", "、", "が"),
)


SCALAR_MORPHOLOGY_ASSET_REGISTRY = (
    ScalarMorphologyAssetSpec("scalar:polarity:negative:fused.v1", ClauseScalarAxis.POLARITY, ("negative",), ScalarSurfaceRealizationMode.FUSED_IN_REGISTERED_PART, RegisteredFunctionalSlotRef.PREDICATE_HEAD.value, ("否定の含みもあり",)),
    ScalarMorphologyAssetSpec("scalar:modality:refusal:fused.v1", ClauseScalarAxis.MODALITY, ("refusal",), ScalarSurfaceRealizationMode.FUSED_IN_REGISTERED_PART, RegisteredFunctionalSlotRef.PREDICATE_HEAD.value, ("拒みたい気持ちも残り",)),
    ScalarMorphologyAssetSpec("scalar:modality:uncertain:fused.v1", ClauseScalarAxis.MODALITY, ("uncertain",), ScalarSurfaceRealizationMode.FUSED_IN_REGISTERED_PART, RegisteredFunctionalSlotRef.PREDICATE_HEAD.value, ("不確かさも残り",)),
    ScalarMorphologyAssetSpec("scalar:time:continuing:fused.v1", ClauseScalarAxis.TIME_SCOPE, ("continuing",), ScalarSurfaceRealizationMode.FUSED_IN_REGISTERED_PART, RegisteredFunctionalSlotRef.PREDICATE_HEAD.value, ("今も続き",)),
    ScalarMorphologyAssetSpec("scalar:time:one-time:fused.v1", ClauseScalarAxis.TIME_SCOPE, ("one_time",), ScalarSurfaceRealizationMode.FUSED_IN_REGISTERED_PART, RegisteredFunctionalSlotRef.PREDICATE_HEAD.value, ("今回に限られ",)),
    ScalarMorphologyAssetSpec("scalar:time:past-present:fused.v1", ClauseScalarAxis.TIME_SCOPE, ("past_to_present",), ScalarSurfaceRealizationMode.FUSED_IN_REGISTERED_PART, RegisteredFunctionalSlotRef.PREDICATE_HEAD.value, ("前から今へ続き",)),
    ScalarMorphologyAssetSpec("scalar:polarity:mixed:overt.v1", ClauseScalarAxis.POLARITY, ("mixed",), ScalarSurfaceRealizationMode.OVERT_FUNCTIONAL_PART, RegisteredFunctionalSlotRef.QUALIFIER.value, ("相反する向きを含み",)),
    ScalarMorphologyAssetSpec("scalar:polarity:positive:overt.v1", ClauseScalarAxis.POLARITY, ("positive",), ScalarSurfaceRealizationMode.OVERT_FUNCTIONAL_PART, RegisteredFunctionalSlotRef.QUALIFIER.value, ("肯定の向きがあり",)),
    ScalarMorphologyAssetSpec("scalar:modality:wish:overt.v1", ClauseScalarAxis.MODALITY, ("wish",), ScalarSurfaceRealizationMode.OVERT_FUNCTIONAL_PART, RegisteredFunctionalSlotRef.QUALIFIER.value, ("願いがあり",)),
    ScalarMorphologyAssetSpec("scalar:modality:possibility:overt.v1", ClauseScalarAxis.MODALITY, ("possibility",), ScalarSurfaceRealizationMode.OVERT_FUNCTIONAL_PART, RegisteredFunctionalSlotRef.QUALIFIER.value, ("可能性も残り",)),
    ScalarMorphologyAssetSpec("scalar:modality:intention:overt.v1", ClauseScalarAxis.MODALITY, ("intention",), ScalarSurfaceRealizationMode.OVERT_FUNCTIONAL_PART, RegisteredFunctionalSlotRef.QUALIFIER.value, ("意図があり",)),
    ScalarMorphologyAssetSpec("scalar:modality:feeling:overt.v1", ClauseScalarAxis.MODALITY, ("feeling",), ScalarSurfaceRealizationMode.OVERT_FUNCTIONAL_PART, RegisteredFunctionalSlotRef.QUALIFIER.value, ("そう感じられ",)),
    ScalarMorphologyAssetSpec("scalar:time:past:overt.v1", ClauseScalarAxis.TIME_SCOPE, ("past",), ScalarSurfaceRealizationMode.OVERT_FUNCTIONAL_PART, RegisteredFunctionalSlotRef.QUALIFIER.value, ("すでに起きており",)),
    ScalarMorphologyAssetSpec("scalar:time:present:overt.v1", ClauseScalarAxis.TIME_SCOPE, ("present",), ScalarSurfaceRealizationMode.OVERT_FUNCTIONAL_PART, RegisteredFunctionalSlotRef.QUALIFIER.value, ("今もあり",)),
    ScalarMorphologyAssetSpec("scalar:time:future:overt.v1", ClauseScalarAxis.TIME_SCOPE, ("future",), ScalarSurfaceRealizationMode.OVERT_FUNCTIONAL_PART, RegisteredFunctionalSlotRef.QUALIFIER.value, ("これからに向かい",)),
    ScalarMorphologyAssetSpec("scalar:time:present-future:overt.v1", ClauseScalarAxis.TIME_SCOPE, ("present_to_future",), ScalarSurfaceRealizationMode.OVERT_FUNCTIONAL_PART, RegisteredFunctionalSlotRef.QUALIFIER.value, ("今から先へ続き",)),
    ScalarMorphologyAssetSpec("scalar:polarity:neutral:unmarked.v1", ClauseScalarAxis.POLARITY, ("neutral", "source_bounded"), ScalarSurfaceRealizationMode.UNMARKED_DEFAULT, None, ()),
    ScalarMorphologyAssetSpec("scalar:modality:fact:unmarked.v1", ClauseScalarAxis.MODALITY, ("fact", "emlis_subjective", "source_bounded"), ScalarSurfaceRealizationMode.UNMARKED_DEFAULT, None, ()),
    ScalarMorphologyAssetSpec("scalar:time:current:unmarked.v1", ClauseScalarAxis.TIME_SCOPE, ("current_input", "source_bounded"), ScalarSurfaceRealizationMode.UNMARKED_DEFAULT, None, ()),
)


SOURCE_SCALAR_MORPHOLOGY_ASSET_REGISTRY = (
    SourceScalarMorphologyAssetSpec(
        "source-scalar-morphology:performed-action-finite.v1",
        "action",
        ("operator:performed_action",),
        (("て", "た"), ("で", "だ")),
        ("た", "だ"),
    ),
    SourceScalarMorphologyAssetSpec(
        "source-scalar-morphology:bounded-change-finite.v1",
        "change",
        ("operator:bounded_change",),
        (),
        ("ました", "でした", "だった", "た", "だ"),
    ),
    SourceScalarMorphologyAssetSpec(
        "source-scalar-morphology:present-residue-finite.v1",
        "residue",
        ("operator:residue",),
        (("ていて", "ている"),),
        ("ている", "いる", "ある"),
    ),
    SourceScalarMorphologyAssetSpec(
        "source-scalar-morphology:unfinished-finite.v1",
        "unfinished",
        ("operator:unfinished",),
        (),
        ("わからない", "分からない", "ない", "未定", "途中"),
    ),
)


RESPONSE_OBJECT_ASSET_REGISTRY = (
    (ResponseObjectExpressionMode.EXPLICIT.value, ("",), False),
    (ResponseObjectExpressionMode.COMPOSITE.value, ("と",), False),
    (
        ResponseObjectExpressionMode.ANAPHORIC.value,
        ("そのこと", "その両方"),
        True,
    ),
)
FUNCTIONAL_ASSET_REGISTRY = (
    tuple(slot.value for slot in RegisteredFunctionalSlotRef),
    SCALAR_MORPHOLOGY_ASSET_REGISTRY,
    RELATION_MORPHOLOGY_ASSET_REGISTRY,
    SOURCE_SCALAR_MORPHOLOGY_ASSET_REGISTRY,
)
PARTICIPANT_ASSET_REGISTRY = (
    ParticipantLexemeAssetSpec("participant:current-user.v1", "あなた"),
    ParticipantLexemeAssetSpec(CMEE_STAGE1_EMLIS_OWNER_REF, "Emlis"),
)
STRUCTURAL_ASSET_REGISTRY = (
    StructuralSurfaceAssetSpec("structural:comma.v1", "、"),
    StructuralSurfaceAssetSpec("structural:sentence.v1", "。"),
    StructuralSurfaceAssetSpec("structural:sentence-join.v1", "。また、"),
    StructuralSurfaceAssetSpec("structural:nominalizer.v1", "ということ"),
    StructuralSurfaceAssetSpec("structural:quote-open.v1", "「"),
    StructuralSurfaceAssetSpec("structural:quote-close.v1", "」"),
)


validate_stage1_anti_template_registry_invariant(
    tuple(field.name for field in fields(ConstructionSpec)),
    ("grammatical_shape_key", "predicate_valency", "syntactic_orientation"),
)


def select_eligible_constructions(
    grammatical_shape_key: GrammaticalShapeKey,
    predicate_valency: PredicateValency,
    syntactic_orientation: SyntacticOrientation,
) -> Tuple[ConstructionSpec, ...]:
    if type(grammatical_shape_key) is not GrammaticalShapeKey or type(predicate_valency) is not PredicateValency or type(syntactic_orientation) is not SyntacticOrientation:
        raise Stage1CompositionError("STAGE1_CONSTRUCTION_SELECTOR_STOP")
    if (
        grammatical_shape_key.predicate_valency is not predicate_valency
        or grammatical_shape_key.syntactic_orientation is not syntactic_orientation
    ):
        raise Stage1CompositionError("STAGE1_CONSTRUCTION_SELECTOR_STOP")
    rows = tuple(row for row in CONSTRUCTION_REGISTRY if row.valency is predicate_valency)
    if grammatical_shape_key.semantic_clause_kind is SemanticClauseKind.SUBJECTIVE_PREDICATE:
        rows = tuple(row for row in rows if row.construction_id.startswith("construction:subjective-"))
    elif grammatical_shape_key.semantic_clause_kind is SemanticClauseKind.GROUNDED_PREDICATE:
        rows = tuple(row for row in rows if row.construction_id.startswith("construction:grounded-"))
    else:
        operator = grammatical_shape_key.admitted_relation_operator
        rows = tuple(row for row in rows if operator in row.relation_combinators)
    rows = tuple(row for row in rows if row.argument_slots == grammatical_shape_key.required_argument_roles)
    if len(rows) != 1:
        raise Stage1CompositionError("STAGE1_CONSTRUCTION_NONUNIQUE_STOP")
    return rows


def project_scalar_surface_realization_rows(
    clause_plan_ref: str,
    scalar_constraint_rows: Tuple[ClauseScalarConstraintRow, ...],
) -> Tuple[ScalarSurfaceRealizationRow, ...]:
    result: list[ScalarSurfaceRealizationRow] = []
    for constraint in scalar_constraint_rows:
        for axis, value in (
            (ClauseScalarAxis.POLARITY, constraint.polarity),
            (ClauseScalarAxis.MODALITY, constraint.modality),
            (ClauseScalarAxis.TIME_SCOPE, constraint.time_scope),
        ):
            if constraint.clause_argument_role is None:
                result.append(
                    ScalarSurfaceRealizationRow(
                        constraint.clause_scalar_constraint_ref,
                        axis,
                        ScalarSurfaceRealizationMode.SEMANTIC_PROVENANCE_ONLY,
                        f"scalar:{axis.value.lower()}:semantic-provenance-only.v1",
                        None,
                    )
                )
                continue
            compatible = tuple(
                row
                for row in SCALAR_MORPHOLOGY_ASSET_REGISTRY
                if row.scalar_axis is axis and value in row.compatible_values
            )
            selected = next(
                (
                    row
                    for mode in (
                        ScalarSurfaceRealizationMode.FUSED_IN_REGISTERED_PART,
                        ScalarSurfaceRealizationMode.OVERT_FUNCTIONAL_PART,
                        ScalarSurfaceRealizationMode.UNMARKED_DEFAULT,
                    )
                    for row in compatible
                    if row.realization_mode is mode
                ),
                None,
            )
            if selected is None or sum(
                row.realization_mode is selected.realization_mode
                for row in compatible
            ) != 1:
                raise Stage1CompositionError("STAGE1_SCALAR_MORPHOLOGY_NONUNIQUE_STOP")
            result.append(
                ScalarSurfaceRealizationRow(
                    constraint.clause_scalar_constraint_ref,
                    axis,
                    selected.realization_mode,
                    selected.morphology_asset_id,
                    selected.realization_target_slot_ref,
                )
            )
    return tuple(result)


def _semantic_ref_node_id(value: str) -> str:
    local = value.split("@", 1)[0]
    return local.split(":", 1)[1] if ":" in local else local


def _structural_lexeme(asset_id: str) -> str:
    rows = tuple(
        row for row in STRUCTURAL_ASSET_REGISTRY if row.structural_asset_id == asset_id
    )
    if len(rows) != 1:
        raise Stage1CompositionError("STAGE1_STRUCTURAL_ASSET_STOP")
    return rows[0].surface_lexeme


def _participant_lexeme(participant_ref: str) -> str:
    rows = tuple(
        row for row in PARTICIPANT_ASSET_REGISTRY if row.participant_ref == participant_ref
    )
    if len(rows) != 1:
        raise Stage1CompositionError("STAGE1_PARTICIPANT_ASSET_STOP")
    return rows[0].surface_lexeme


def _frame_row(
    phase_B: Stage1SurfaceCompositionInputs,
    candidate_ref: str,
) -> CandidateFrameRow:
    rows = tuple(
        row
        for row in phase_B.resolved_grounded_frame_by_candidate_ref
        if row.candidate_ref == candidate_ref
    )
    if len(rows) != 1:
        raise Stage1CompositionError("STAGE1_GROUNDED_FRAME_CLOSURE_STOP")
    return rows[0]


def _candidate_for_ref(
    projection: Any,
    candidate_ref: str,
) -> EmlisInterpretationCandidate:
    rows = tuple(
        row
        for row in getattr(projection, "interpretation_candidates", ())
        if row.candidate_id == candidate_ref
    )
    if len(rows) != 1:
        raise Stage1CompositionError("STAGE1_CANDIDATE_CLOSURE_STOP")
    return rows[0]


def _frame_for_semantic_ref(
    owner: Any,
    semantic_ref: str,
    phase_B: Stage1SurfaceCompositionInputs,
) -> Any:
    candidate_refs = tuple(getattr(owner, "interpretation_candidate_refs", ()))
    if candidate_refs:
        if len(candidate_refs) != 1:
            raise Stage1CompositionError("STAGE1_CANDIDATE_CLOSURE_STOP")
        candidate = _candidate_for_ref(phase_B.projection, candidate_refs[0])
        if candidate.relation_operator is RelationOperator.NO_RELATION_CLAIM:
            if not any(row.semantic_ref == semantic_ref for row in candidate.argument_bindings):
                raise Stage1CompositionError("STAGE1_SOURCE_BINDING_CLOSURE_STOP")
            return _frame_row(phase_B, candidate.candidate_id).grounded_frame
        source_bindings = tuple(
            row
            for row in candidate.argument_bindings
            if row.semantic_ref == semantic_ref
        )
        if len(source_bindings) != 1:
            raise Stage1CompositionError("STAGE1_RELATION_ENDPOINT_CLOSURE_STOP")
        endpoint_rows = tuple(
            row
            for row in phase_B.relation_endpoint_grounded_candidate_ref_by_binding_key
            if row.relation_candidate_ref == candidate.candidate_id
            and row.source_argument_role is source_bindings[0].role
            and row.source_semantic_ref == semantic_ref
        )
        if len(endpoint_rows) != 1:
            raise Stage1CompositionError("STAGE1_RELATION_ENDPOINT_CLOSURE_STOP")
        return _frame_row(
            phase_B, endpoint_rows[0].endpoint_grounded_candidate_ref
        ).grounded_frame
    direct_rows = tuple(
        candidate
        for candidate in getattr(phase_B.projection, "interpretation_candidates", ())
        if candidate.relation_operator is RelationOperator.NO_RELATION_CLAIM
        and any(
            binding.role is ArgumentRole.PRIMARY
            and binding.semantic_ref == semantic_ref
            for binding in candidate.argument_bindings
        )
    )
    if len(direct_rows) != 1:
        raise Stage1CompositionError("STAGE1_SOURCE_BINDING_CLOSURE_STOP")
    return _frame_row(phase_B, direct_rows[0].candidate_id).grounded_frame


def _surface_scalar_range(frame: Any, value_length: int) -> Optional[Tuple[int, int]]:
    range_rows = tuple(
        code
        for code in getattr(frame, "attribute_codes", ())
        if isinstance(code, str) and code.startswith("surface_scalar_range:")
    )
    source_rows = tuple(
        code
        for code in getattr(frame, "attribute_codes", ())
        if isinstance(code, str) and code.startswith("surface_scalar_source:")
    )
    if not range_rows:
        if source_rows:
            raise Stage1CompositionError("STAGE1_SOURCE_SCALAR_RANGE_STOP")
        return None
    if (
        len(range_rows) != 1
        or source_rows != ("surface_scalar_source:normalized_raw_text",)
    ):
        raise Stage1CompositionError("STAGE1_SOURCE_SCALAR_RANGE_STOP")
    parts = range_rows[0].split(":")
    if len(parts) != 3 or not all(part.isdigit() for part in parts[1:]):
        raise Stage1CompositionError("STAGE1_SOURCE_SCALAR_RANGE_STOP")
    start, end = int(parts[1]), int(parts[2])
    if not (0 <= start < end <= value_length):
        raise Stage1CompositionError("STAGE1_SOURCE_SCALAR_RANGE_STOP")
    return start, end


def _normalize_source_scalar_text(value: str) -> str:
    # Byte-for-byte equivalent whitespace rule to the upstream normalized raw
    # text owner: full-width spaces become ASCII and every whitespace run is
    # one ASCII space.  This is normalization only, never semantic parsing.
    return " ".join(value.replace("\u3000", " ").split()).strip()


def _source_scalar_text(frame: Any, admitted_source: Any) -> str:
    anchor_ids = tuple(getattr(frame, "target_anchor_ids", ()))
    if len(anchor_ids) != 1:
        raise Stage1CompositionError("STAGE1_SOURCE_SCALAR_RANGE_STOP")
    rows = tuple(
        row
        for row in getattr(admitted_source, "evidence_spans", ())
        if getattr(row, "span_id", None) == anchor_ids[0]
    )
    if len(rows) != 1 or not isinstance(getattr(rows[0], "raw_text", None), str):
        raise Stage1CompositionError("STAGE1_SOURCE_SCALAR_RANGE_STOP")
    value = _normalize_source_scalar_text(rows[0].raw_text)
    if not value:
        raise Stage1CompositionError("STAGE1_SOURCE_SCALAR_RANGE_STOP")
    return value


def _source_scalar_finite_form(value: str, frame: Any) -> str:
    predicate_kind = str(getattr(frame, "predicate_kind", ""))
    attribute_codes = tuple(getattr(frame, "attribute_codes", ()))
    rows = tuple(
        row
        for row in SOURCE_SCALAR_MORPHOLOGY_ASSET_REGISTRY
        if row.predicate_kind == predicate_kind
        and all(code in attribute_codes for code in row.required_attribute_codes)
    )
    if len(rows) != 1:
        raise Stage1CompositionError("STAGE1_SOURCE_SCALAR_MORPHOLOGY_STOP")
    asset = rows[0]
    rewrites = tuple(
        (source_terminal, finite_terminal)
        for source_terminal, finite_terminal in asset.terminal_rewrites
        if value.endswith(source_terminal)
    )
    if len(rewrites) > 1:
        raise Stage1CompositionError("STAGE1_SOURCE_SCALAR_MORPHOLOGY_STOP")
    if rewrites:
        source_terminal, finite_terminal = rewrites[0]
        result = value[: -len(source_terminal)] + finite_terminal
        if not result:
            raise Stage1CompositionError("STAGE1_SOURCE_SCALAR_MORPHOLOGY_STOP")
        return result
    if asset.preserved_finite_terminals and value.endswith(
        asset.preserved_finite_terminals
    ):
        return value
    raise Stage1CompositionError("STAGE1_SOURCE_SCALAR_MORPHOLOGY_STOP")


def _source_expression(ref: str, phase_B: Stage1SurfaceCompositionInputs, frame: Any) -> str:
    graph = phase_B.grounded_graph
    node_id = _semantic_ref_node_id(ref)
    rows = tuple(row for row in graph.nodes if row.node_id == node_id)
    if len(rows) != 1 or not isinstance(rows[0].value, str):
        raise Stage1CompositionError("STAGE1_SOURCE_EXPRESSION_STOP")
    graph_value = _normalize_source_scalar_text(rows[0].value)
    has_scalar_range = any(
        isinstance(code, str) and code.startswith("surface_scalar_range:")
        for code in getattr(frame, "attribute_codes", ())
    )
    value = (
        _source_scalar_text(frame, phase_B.admitted_source)
        if has_scalar_range
        else graph_value
    )
    scalar_range = _surface_scalar_range(frame, len(value))
    if scalar_range is not None:
        value = value[scalar_range[0] : scalar_range[1]].strip()
        value = _source_scalar_finite_form(value, frame)
    if not value or "\n" in value or "\r" in value:
        raise Stage1CompositionError("STAGE1_SOURCE_EXPRESSION_STOP")
    return "".join(
        (
            _structural_lexeme("structural:quote-open.v1"),
            value,
            _structural_lexeme("structural:quote-close.v1"),
            _structural_lexeme("structural:nominalizer.v1"),
        )
    )


def _duty_semantics(duty: CompositionDutyView, phase_B: Stage1SurfaceCompositionInputs) -> tuple[Any, Tuple[str, ...]]:
    if not duty.basis_projection_refs:
        raise Stage1CompositionError("STAGE1_DUTY_OWNER_CLOSURE_STOP")
    if duty.layer == "LAYER_1":
        owners = tuple(
            row
            for row in _contributions(phase_B.projection)
            if row.contribution_id in set(duty.basis_projection_refs)
        )
        primary_owners = tuple(
            row
            for row in owners
            if (
                duty.relation_refs
                and row.relation_basis_refs == duty.relation_refs
            )
            or (
                not duty.relation_refs
                and row.contribution_id == duty.basis_projection_refs[0]
            )
        )
        if (
            len(owners) != len(duty.basis_projection_refs)
            or len(primary_owners) != 1
        ):
            raise Stage1CompositionError("STAGE1_DUTY_OWNER_CLOSURE_STOP")
        contribution = primary_owners[0]
        return contribution, tuple(binding.semantic_ref for binding in contribution.argument_bindings if binding.role is not ArgumentRole.EXPERIENCER)
    owners = tuple(
        row
        for row in _claims(phase_B.projection)
        if row.subjective_claim_id == duty.basis_projection_refs[0]
    )
    if len(owners) != 1:
        raise Stage1CompositionError("STAGE1_DUTY_OWNER_CLOSURE_STOP")
    claim = owners[0]
    return claim, tuple(_prop(claim).response_object_refs)


def _clause_plan(duty: CompositionDutyView, phase_B: Stage1SurfaceCompositionInputs) -> ClausePlan:
    owner, refs = _duty_semantics(duty, phase_B)
    if duty.layer == "LAYER_2":
        semantic_kind = SemanticClauseKind.SUBJECTIVE_PREDICATE
        valency = PredicateValency.TRIADIC_ACTOR_TARGET_BOUNDARY if getattr(_prop(owner), "boundary_target_refs", ()) else PredicateValency.DYADIC_ACTOR_TARGET
        assignment = GrammaticalRoleAssignmentRule.EMLIS_TARGET_OR_BOUNDARY
        orientation = SyntacticOrientation.EMLIS_SUBJECT
        speaker = SpeakerRequirement.EMLIS_ZERO_ALLOWED if phase_B.section_speaker_owner_ref == CMEE_STAGE1_EMLIS_OWNER_REF else SpeakerRequirement.EMLIS_EXPLICIT_REQUIRED
        roles = (
            ClauseArgumentRole.SUBJECT,
            ClauseArgumentRole.PRIMARY_OBJECT,
            *(
                (ClauseArgumentRole.SECONDARY_OBJECT,)
                if valency is PredicateValency.TRIADIC_ACTOR_TARGET_BOUNDARY
                else ()
            ),
        )
        relation_operator = RelationOperator.NO_RELATION_CLAIM
    elif owner.relation_operator is not RelationOperator.NO_RELATION_CLAIM:
        semantic_kind = SemanticClauseKind.ADMITTED_RELATION
        valency = PredicateValency.DYADIC_RELATION_ENDPOINTS
        assignment = GrammaticalRoleAssignmentRule.ADMITTED_RELATION_ENDPOINT_PAIR
        relation_operator = owner.relation_operator
        orientation = (
            SyntacticOrientation.EVENT_FIRST
            if relation_operator
            in {
                RelationOperator.TEMPORALLY_PRECEDES,
                RelationOperator.ACTION_PRECEDES_CHANGE,
                RelationOperator.SOURCE_EXPLICIT_CAUSE,
            }
            else SyntacticOrientation.RELATION_FIRST
        )
        speaker = SpeakerRequirement.GROUNDED_NARRATION
        roles = {
            RelationOperator.COEXISTS_WITH: (
                ClauseArgumentRole.LEFT_ENDPOINT,
                ClauseArgumentRole.RIGHT_ENDPOINT,
            ),
            RelationOperator.TENSION_WITH: (
                ClauseArgumentRole.LEFT_ENDPOINT,
                ClauseArgumentRole.RIGHT_ENDPOINT,
            ),
            RelationOperator.TEMPORALLY_PRECEDES: (
                ClauseArgumentRole.BEFORE_EVENT,
                ClauseArgumentRole.AFTER_EVENT,
            ),
            RelationOperator.ACTION_PRECEDES_CHANGE: (
                ClauseArgumentRole.ACTION_EVENT,
                ClauseArgumentRole.CHANGE_EVENT,
            ),
            RelationOperator.SOURCE_EXPLICIT_CAUSE: (
                ClauseArgumentRole.CAUSE_EVENT,
                ClauseArgumentRole.EFFECT_EVENT,
            ),
        }.get(relation_operator, ())
        if not roles:
            raise Stage1CompositionError("STAGE1_RELATION_ROLE_STOP")
    else:
        semantic_kind = SemanticClauseKind.GROUNDED_PREDICATE
        valency = PredicateValency.MONADIC_ARGUMENT
        assignment = GrammaticalRoleAssignmentRule.DIRECT_REFERENT_SUBJECT
        orientation = SyntacticOrientation.REFERENT_FIRST
        speaker = SpeakerRequirement.GROUNDED_NARRATION
        roles = (ClauseArgumentRole.SUBJECT,)
        relation_operator = RelationOperator.NO_RELATION_CLAIM
    scalar_rows: list[ClauseScalarConstraintRow] = []
    for index, ref in enumerate(refs or duty.response_object_refs):
        polarity = modality = time_scope = "source_bounded"
        if duty.layer == "LAYER_1":
            if len(owner.interpretation_candidate_refs) != 1:
                raise Stage1CompositionError("STAGE1_CANDIDATE_CLOSURE_STOP")
            candidate_ref = owner.interpretation_candidate_refs[0]
            candidate = _candidate_for_ref(phase_B.projection, candidate_ref)
            relation = candidate.relation_operator is not RelationOperator.NO_RELATION_CLAIM
            source_role = next(
                (
                    binding.role
                    for binding in candidate.argument_bindings
                    if binding.semantic_ref == ref
                    and binding.role is not ArgumentRole.EXPERIENCER
                ),
                None,
            )
            candidate_rows = tuple(
                row
                for row in phase_B.qualifier_value_by_candidate_scope_axis_key
                if row.candidate_ref == candidate_ref
                and row.qualifier_scope
                is (
                    QualifierLookupScope.RELATION_SOURCE_BINDING
                    if relation
                    else QualifierLookupScope.DIRECT_UNQUALIFIED
                )
                and row.source_argument_role is (source_role if relation else None)
                and row.source_semantic_ref == (ref if relation else None)
            )
            by_axis = {
                axis: tuple(row.value for row in candidate_rows if row.axis is axis)
                for axis in ClauseScalarAxis
            }
            if any(len(values) != 1 for values in by_axis.values()):
                raise Stage1CompositionError("STAGE1_QUALIFIER_CLOSURE_STOP")
            polarity = by_axis[ClauseScalarAxis.POLARITY][0]
            modality = by_axis[ClauseScalarAxis.MODALITY][0]
            time_scope = by_axis[ClauseScalarAxis.TIME_SCOPE][0]
        if semantic_kind is SemanticClauseKind.ADMITTED_RELATION:
            role = roles[index]
        elif valency is PredicateValency.MONADIC_ARGUMENT:
            role = ClauseArgumentRole.SUBJECT
        else:
            role = ClauseArgumentRole.PRIMARY_OBJECT
        scalar_rows.append(ClauseScalarConstraintRow(_ref("clause-scalar", (duty.duty_ref, index, ref, polarity, modality, time_scope)), ref, role, polarity, modality, time_scope))
    if not scalar_rows:
        scalar_rows.append(ClauseScalarConstraintRow(_ref("clause-scalar", (duty.duty_ref, "emlis")), duty.duty_ref, ClauseArgumentRole.PRIMARY_OBJECT, "neutral", "emlis_subjective", "current_input"))
    if duty.layer == "LAYER_2":
        scalar_rows.append(
            ClauseScalarConstraintRow(
                _ref("clause-scalar", (duty.duty_ref, "subjective-basis-owner")),
                duty.basis_projection_refs[0],
                None,
                "source_bounded",
                "source_bounded",
                "source_bounded",
            )
        )
    scalar_shape = tuple(
        item
        for row in scalar_rows
        for item in (
            (ClauseScalarAxis.POLARITY, row.polarity),
            (ClauseScalarAxis.MODALITY, row.modality),
            (ClauseScalarAxis.TIME_SCOPE, row.time_scope),
        )
    )
    shape = GrammaticalShapeKey(
        semantic_kind,
        duty.sentence_job,
        roles,
        assignment,
        valency,
        relation_operator,
        scalar_shape,
        orientation,
    )
    construction = select_eligible_constructions(shape, valency, orientation)[0]
    plan_ref = _ref("clause-plan", (duty, semantic_kind, valency, assignment, orientation, speaker, construction.construction_id, tuple(scalar_rows)))
    scalar_realization = project_scalar_surface_realization_rows(plan_ref, tuple(scalar_rows))
    return ClausePlan(plan_ref, duty.duty_ref, semantic_kind, valency, assignment, orientation, speaker, construction.construction_id, tuple(scalar_rows), scalar_realization)


def _predicate_key(duty: CompositionDutyView, owner: Any) -> str:
    if duty.sentence_job is SentenceJob.OBSERVE_CENTER:
        if owner.semantic_operator is SemanticOperator.PRESENT_DIRECTION:
            return "direction"
        if owner.semantic_operator is SemanticOperator.PRESENT_BURDEN:
            return "burden"
        if owner.semantic_operator in {
            SemanticOperator.PRESENT_CHANGE,
            SemanticOperator.PRESENT_ACTUAL_OUTPUT,
        }:
            return "bounded-change"
        return "center"
    if duty.sentence_job is SentenceJob.RELATE_COEXISTING_OR_TENSION:
        return (
            "tension"
            if owner.relation_operator is RelationOperator.TENSION_WITH
            else "coexistence"
        )
    if duty.sentence_job is SentenceJob.TRACE_CHANGE_OR_SEQUENCE:
        return "sequence"
    if duty.sentence_job is SentenceJob.PRESERVE_RESIDUE_OR_UNFINISHED:
        return "unfinished"
    if duty.sentence_job is SentenceJob.FEEL_TOWARD_OBJECT:
        return "affect"
    if duty.sentence_job is SentenceJob.CONSIDER_MATERIAL_MEANING:
        dimension = getattr(
            getattr(_prop(owner), "appraisal_content", None),
            "dimension",
            AppraisalDimension.MATERIAL_WEIGHT,
        )
        return {
            AppraisalDimension.MATERIAL_WEIGHT: "appraisal-material",
            AppraisalDimension.RELATIONAL_NONCOLLAPSE: "appraisal-noncollapse",
            AppraisalDimension.BOUNDED_CHANGE: "appraisal-change",
            AppraisalDimension.UNFINISHED_OPENNESS: "appraisal-unfinished",
            AppraisalDimension.AGENCY_BOUNDARY: "appraisal-agency",
        }[dimension]
    if duty.sentence_job is SentenceJob.STAY_WITH_UNFINISHED:
        return "open-position"
    return (
        "material-value"
        if _content_kind(owner) is SubjectiveContentKind.MATERIAL_VALUE
        else "position"
    )


def _expression_asset(
    duty: CompositionDutyView,
    plan: ClausePlan,
    owner: Any,
) -> ExpressionAssetSpec:
    key = _predicate_key(duty, owner)
    rows = tuple(
        row
        for row in EXPRESSION_ASSET_REGISTRY
        if row.sentence_job is duty.sentence_job
        and row.semantic_clause_kind is plan.semantic_clause_kind
        and row.predicate_key == key
        and plan.predicate_valency in row.compatible_valencies
    )
    if len(rows) != 1:
        raise Stage1CompositionError("STAGE1_EXPRESSION_ASSET_NONUNIQUE_STOP")
    return rows[0]


def _response_object_surface(
    expression: ResponseObjectExpression,
    owner: Any,
    phase_B: Stage1SurfaceCompositionInputs,
) -> Tuple[str, ...]:
    asset_rows = tuple(
        row
        for row in RESPONSE_OBJECT_ASSET_REGISTRY
        if row[0] == expression.expression_mode.value
    )
    if len(asset_rows) != 1:
        raise Stage1CompositionError("STAGE1_RESPONSE_OBJECT_ASSET_STOP")
    _mode, lexemes, antecedent_required = asset_rows[0]
    if (
        type(lexemes) is not tuple
        or not lexemes
        or any(type(lexeme) is not str for lexeme in lexemes)
    ):
        raise Stage1CompositionError("STAGE1_RESPONSE_OBJECT_ASSET_STOP")
    if expression.expression_mode is ResponseObjectExpressionMode.ANAPHORIC:
        if (
            not antecedent_required
            or expression.antecedent_unit_ref is None
            or len(lexemes) != 2
        ):
            raise Stage1CompositionError("STAGE1_RESPONSE_ANTECEDENT_STOP")
        return (lexemes[0] if len(expression.basis_semantic_refs) == 1 else lexemes[1],)
    if antecedent_required or expression.antecedent_unit_ref is not None:
        raise Stage1CompositionError("STAGE1_RESPONSE_ANTECEDENT_STOP")
    if len(lexemes) != 1:
        raise Stage1CompositionError("STAGE1_RESPONSE_OBJECT_ASSET_STOP")
    lexeme = lexemes[0]
    objects = tuple(
        _source_expression(
            ref,
            phase_B,
            _frame_for_semantic_ref(owner, ref, phase_B),
        )
        for ref in expression.basis_semantic_refs
    )
    if not objects:
        raise Stage1CompositionError("STAGE1_RESPONSE_OBJECT_EMPTY_STOP")
    if expression.expression_mode is ResponseObjectExpressionMode.EXPLICIT:
        if len(objects) != 1:
            raise Stage1CompositionError("STAGE1_RESPONSE_OBJECT_CARDINALITY_STOP")
        return objects
    if len(objects) < 2:
        raise Stage1CompositionError("STAGE1_RESPONSE_OBJECT_CARDINALITY_STOP")
    return (lexeme.join(objects),)


def _functional_surface_lexemes_by_role(
    plan: ClausePlan,
) -> Tuple[
    Tuple[
        Optional[ClauseArgumentRole],
        Tuple[str, ...],
        Tuple[str, ...],
    ],
    ...,
]:
    if plan.scalar_surface_realization_rows != project_scalar_surface_realization_rows(
        plan.clause_plan_ref,
        plan.scalar_constraint_rows,
    ):
        raise Stage1CompositionError("STAGE1_SCALAR_MORPHOLOGY_NONUNIQUE_STOP")
    asset_by_id = {
        row.morphology_asset_id: row for row in SCALAR_MORPHOLOGY_ASSET_REGISTRY
    }
    constraint_by_ref = {
        row.clause_scalar_constraint_ref: row for row in plan.scalar_constraint_rows
    }
    role_order = _unique(
        row.clause_argument_role for row in plan.scalar_constraint_rows
    )
    scalar_values_by_role: dict[
        Optional[ClauseArgumentRole], set[tuple[ClauseScalarAxis, str]]
    ] = {role: set() for role in role_order}
    overt_by_role: dict[Optional[ClauseArgumentRole], list[str]] = {
        role: [] for role in role_order
    }
    fused_by_role: dict[Optional[ClauseArgumentRole], list[str]] = {
        role: [] for role in role_order
    }
    for realization in plan.scalar_surface_realization_rows:
        constraint = constraint_by_ref.get(realization.clause_scalar_constraint_ref)
        if constraint is None:
            raise Stage1CompositionError("STAGE1_SCALAR_MORPHOLOGY_NONUNIQUE_STOP")
        role = constraint.clause_argument_role
        if role not in scalar_values_by_role:
            raise Stage1CompositionError("STAGE1_SCALAR_MORPHOLOGY_NONUNIQUE_STOP")
        scalar_values_by_role[role].add(
            (
                realization.scalar_axis,
                {
                    ClauseScalarAxis.POLARITY: constraint.polarity,
                    ClauseScalarAxis.MODALITY: constraint.modality,
                    ClauseScalarAxis.TIME_SCOPE: constraint.time_scope,
                }[realization.scalar_axis],
            )
        )
        if realization.realization_mode in {
            ScalarSurfaceRealizationMode.UNMARKED_DEFAULT,
            ScalarSurfaceRealizationMode.SEMANTIC_PROVENANCE_ONLY,
        }:
            continue
        asset = asset_by_id.get(realization.registered_realization_rule_ref)
        if (
            asset is None
            or asset.scalar_axis is not realization.scalar_axis
            or asset.realization_mode is not realization.realization_mode
            or asset.realization_target_slot_ref
            != realization.target_clause_slot_ref
        ):
            raise Stage1CompositionError("STAGE1_SCALAR_MORPHOLOGY_NONUNIQUE_STOP")
        if realization.realization_mode is ScalarSurfaceRealizationMode.OVERT_FUNCTIONAL_PART:
            if (
                realization.target_clause_slot_ref
                != RegisteredFunctionalSlotRef.QUALIFIER.value
            ):
                raise Stage1CompositionError(
                    "STAGE1_SCALAR_MORPHOLOGY_NONUNIQUE_STOP"
                )
            overt_by_role[role].extend(asset.morphemes)
        elif realization.realization_mode is ScalarSurfaceRealizationMode.FUSED_IN_REGISTERED_PART:
            if (
                realization.target_clause_slot_ref
                != RegisteredFunctionalSlotRef.PREDICATE_HEAD.value
            ):
                raise Stage1CompositionError(
                    "STAGE1_SCALAR_MORPHOLOGY_NONUNIQUE_STOP"
                )
            fused_by_role[role].extend(asset.morphemes)
        else:
            raise Stage1CompositionError("STAGE1_SCALAR_MORPHOLOGY_NONUNIQUE_STOP")

    # Each visible carrier stays with its existing grammatical role.  This
    # prevents a relation's LEFT/RIGHT or BEFORE/AFTER scalar rows from being
    # serialized as one semantic-label list with an ambiguous host.  The
    # combinations below use only frozen grammatical axes; no case id, raw
    # text, fixture family or expected sentence participates in the decision.
    result: list[
        Tuple[Optional[ClauseArgumentRole], Tuple[str, ...], Tuple[str, ...]]
    ] = []
    for role in role_order:
        scalar_values = scalar_values_by_role[role]
        polarity = {
            value
            for axis, value in scalar_values
            if axis is ClauseScalarAxis.POLARITY
        }
        modality = {
            value
            for axis, value in scalar_values
            if axis is ClauseScalarAxis.MODALITY
        }
        time_scope = {
            value
            for axis, value in scalar_values
            if axis is ClauseScalarAxis.TIME_SCOPE
        }
        if "positive" in polarity and "wish" in modality:
            carrier = (
                "前を向く願いが今も残り"
                if "continuing" in time_scope
                else "前を向く願いがあり"
            )
            overt, fused = (carrier,), ()
        elif "negative" in polarity and "possibility" in modality:
            overt, fused = ("否定の含みと可能性があり",), ()
        elif "negative" in polarity and "uncertain" in modality:
            overt, fused = ("不確かさと否定の含みが残り",), ()
        elif "feeling" in modality and "past" in time_scope:
            overt, fused = ("すでに実感があり",), ()
        elif "feeling" in modality and "present" in time_scope:
            overt, fused = ("今も実感があり",), ()
        elif "negative" in polarity:
            overt, fused = ("否定の含みがあり",), ()
        elif "uncertain" in modality and "present" in time_scope:
            overt, fused = ("今も不確かなまま",), ()
        else:
            overt = _unique(overt_by_role[role])
            fused = _unique(fused_by_role[role])
        result.append((role, overt, fused))
    return tuple(result)


def _functional_surface_lexemes(
    plan: ClausePlan,
) -> Tuple[Tuple[str, ...], Tuple[str, ...]]:
    by_role = _functional_surface_lexemes_by_role(plan)
    return (
        _unique(morpheme for _role, overt, _fused in by_role for morpheme in overt),
        _unique(morpheme for _role, _overt, fused in by_role for morpheme in fused),
    )


def _finite_relation_carrier(value: str) -> str:
    """Close one existing role-local scalar carrier without changing its axis."""

    suffixes = (
        ("起きており", "起きています"),
        ("があり", "があります"),
        ("が残り", "が残っています"),
        ("今も続き", "今も続いています"),
        ("今もあり", "今もあります"),
        ("不確かなまま", "不確かなままです"),
    )
    matches = tuple(
        (source, target)
        for source, target in suffixes
        if value.endswith(source)
    )
    if len(matches) != 1:
        raise Stage1CompositionError("STAGE1_SCALAR_MORPHOLOGY_NONUNIQUE_STOP")
    source, target = matches[0]
    return value[: -len(source)] + target


def _relation_endpoint_particle(carrier: str) -> str:
    if carrier.startswith("すでに起き"):
        return "が"
    if carrier == "今もあり":
        return "が"
    if "が" in carrier:
        return "には"
    return "は"


def _surface_for_plan(
    duty: CompositionDutyView,
    plan: ClausePlan,
    expression: ResponseObjectExpression,
    phase_B: Stage1SurfaceCompositionInputs,
    *,
    emlis_subject_visible: bool = True,
) -> str:
    owner, _refs = _duty_semantics(duty, phase_B)
    construction_rows = tuple(
        row for row in CONSTRUCTION_REGISTRY if row.construction_id == plan.construction_id
    )
    if len(construction_rows) != 1:
        raise Stage1CompositionError("STAGE1_CONSTRUCTION_NONUNIQUE_STOP")
    construction = construction_rows[0]
    expression_asset = _expression_asset(duty, plan, owner)
    objects = _response_object_surface(expression, owner, phase_B)
    comma = _structural_lexeme("structural:comma.v1")
    terminal = _structural_lexeme("structural:sentence.v1")
    overt_qualifiers, fused_predicate_prefixes = _functional_surface_lexemes(plan)
    predicate = comma.join(
        (
            *overt_qualifiers,
            *fused_predicate_prefixes,
            *expression_asset.predicate_lexemes,
        )
    )
    particles = dict(construction.particle_rules)
    if plan.semantic_clause_kind is SemanticClauseKind.ADMITTED_RELATION:
        if len(expression.basis_semantic_refs) != 2:
            raise Stage1CompositionError("STAGE1_RELATION_ENDPOINT_CLOSURE_STOP")
        relation_rows = tuple(
            row
            for row in RELATION_MORPHOLOGY_ASSET_REGISTRY
            if row.relation_operator is owner.relation_operator
        )
        if len(relation_rows) != 1:
            raise Stage1CompositionError("STAGE1_RELATION_MORPHOLOGY_STOP")
        relation = relation_rows[0]
        endpoint_objects = tuple(
            _source_expression(
                ref,
                phase_B,
                _frame_for_semantic_ref(owner, ref, phase_B),
            )
            for ref in expression.basis_semantic_refs
        )
        scalar_by_role = _functional_surface_lexemes_by_role(plan)
        endpoint_roles = _unique(
            row.clause_argument_role for row in plan.scalar_constraint_rows
        )
        if (
            len(endpoint_roles) != 2
            or tuple(role for role, _overt, _fused in scalar_by_role)
            != endpoint_roles
        ):
            raise Stage1CompositionError("STAGE1_RELATION_ROLE_STOP")
        carrier_by_role = {
            role: comma.join((*overt, *fused))
            for role, overt, fused in scalar_by_role
        }
        left_carrier = carrier_by_role[endpoint_roles[0]]
        right_carrier = carrier_by_role[endpoint_roles[1]]
        if owner.relation_operator in {
            RelationOperator.TEMPORALLY_PRECEDES,
            RelationOperator.ACTION_PRECEDES_CHANGE,
        }:
            left_clause = (
                "".join(
                    (
                        endpoint_objects[0],
                        _relation_endpoint_particle(left_carrier),
                        left_carrier,
                    )
                )
                if left_carrier
                else "".join((endpoint_objects[0], relation.left_particle))
            )
            right_clause = (
                "".join(
                    (
                        endpoint_objects[1],
                        _relation_endpoint_particle(right_carrier),
                        _finite_relation_carrier(right_carrier),
                    )
                )
                if right_carrier
                else "".join((endpoint_objects[1], "が続いています"))
            )
            return "".join(
                (
                    left_clause,
                    comma,
                    "そのあとに" if left_carrier else "",
                    right_clause,
                    terminal,
                )
            )
        if owner.relation_operator in {
            RelationOperator.COEXISTS_WITH,
            RelationOperator.TENSION_WITH,
        } and (left_carrier or right_carrier):
            endpoint_clauses = (
                "".join(
                    (
                        endpoint_objects[0],
                        (
                            "には"
                            if "が" in left_carrier
                            else "は"
                            if left_carrier
                            else "が"
                        ),
                        left_carrier or "あり",
                    )
                ),
                "".join(
                    (
                        endpoint_objects[1],
                        (
                            "には"
                            if "が" in right_carrier
                            else "は"
                            if right_carrier
                            else "が"
                        ),
                        right_carrier or "あり",
                    )
                ),
            )
            return "".join(
                (
                    comma.join(
                        (
                            *endpoint_clauses,
                            *expression_asset.predicate_lexemes,
                        )
                    ),
                    terminal,
                )
            )
        relation_left = (
            "".join(
                (
                    endpoint_objects[0],
                    "が",
                    left_carrier,
                    comma,
                    "そのこと",
                    relation.left_particle,
                )
            )
            if left_carrier
            else "".join((endpoint_objects[0], relation.left_particle))
        )
        return "".join(
            (
                relation_left,
                relation.connective,
                endpoint_objects[1],
                (
                    "には"
                    if "が" in right_carrier
                    else relation.right_particle
                ),
                right_carrier,
                comma if right_carrier else "",
                comma.join(expression_asset.predicate_lexemes),
                terminal,
            )
        )
    object_surface = objects[0]
    if plan.semantic_clause_kind is SemanticClauseKind.SUBJECTIVE_PREDICATE:
        emlis_subject = (
            "".join(
                (
                    _participant_lexeme(CMEE_STAGE1_EMLIS_OWNER_REF),
                    particles[ClauseArgumentRole.SUBJECT],
                )
            )
            if emlis_subject_visible
            else ""
        )
        subjective_predicate = comma.join(
            (
                *overt_qualifiers,
                *fused_predicate_prefixes,
                "".join(expression_asset.predicate_lexemes),
            )
        )
        if plan.predicate_valency is PredicateValency.TRIADIC_ACTOR_TARGET_BOUNDARY:
            if (
                expression.expression_mode
                is not ResponseObjectExpressionMode.COMPOSITE
                or len(expression.basis_semantic_refs) != 2
            ):
                raise Stage1CompositionError(
                    "STAGE1_RESPONSE_OBJECT_CARDINALITY_STOP"
                )
            primary_surface, boundary_surface = tuple(
                _source_expression(
                    ref,
                    phase_B,
                    _frame_for_semantic_ref(owner, ref, phase_B),
                )
                for ref in expression.basis_semantic_refs
            )
            return "".join(
                (
                    emlis_subject,
                    primary_surface,
                    particles[ClauseArgumentRole.PRIMARY_OBJECT],
                    boundary_surface,
                    particles[ClauseArgumentRole.SECONDARY_OBJECT],
                    subjective_predicate,
                    terminal,
                )
            )
        return "".join(
            (
                emlis_subject,
                object_surface,
                particles[ClauseArgumentRole.PRIMARY_OBJECT],
                subjective_predicate,
                terminal,
            )
        )
    return "".join(
        (
            object_surface,
            particles[ClauseArgumentRole.SUBJECT],
            predicate,
            terminal,
        )
    )


def _bounded_layout_dimension(values: Iterable[Any]) -> Tuple[Any, ...]:
    unique: list[Any] = []
    exact_keys: set[bytes] = set()
    for value in values:
        exact_key = stage1_canonical_json_bytes(value)
        if exact_key not in exact_keys:
            exact_keys.add(exact_key)
            unique.append(value)
    if not unique:
        raise Stage1CompositionError("STAGE1_LAYOUT_DIMENSION_EMPTY_STOP")
    if len(unique) > 2:
        raise Stage1CompositionError("CANDIDATE_BUDGET_INSUFFICIENT_STOP")
    return tuple(unique)


def _dedupe_layout_seeds(
    values: Iterable[LayoutPreferenceSeed],
) -> Tuple[LayoutPreferenceSeed, ...]:
    unique: list[LayoutPreferenceSeed] = []
    exact_keys: set[bytes] = set()
    for value in values:
        exact_key = stage1_canonical_json_bytes(value)
        if exact_key not in exact_keys:
            exact_keys.add(exact_key)
            unique.append(value)
    if not unique:
        raise Stage1CompositionError("STAGE1_LAYOUT_DIMENSION_EMPTY_STOP")
    if len(unique) > 32:
        raise Stage1CompositionError("CANDIDATE_BUDGET_INSUFFICIENT_STOP")
    return tuple(unique)


def _duty_dependency_maps(
    required: Tuple[CompositionDutyView, ...],
    arc: Stage1DiscourseArcView,
) -> Tuple[dict[str, set[str]], dict[str, set[str]]]:
    required_refs = {row.duty_ref for row in required}
    basis_owner_to_duties: dict[str, list[str]] = {}
    layer1_response_owner_to_duties: dict[str, list[str]] = {}
    for duty in required:
        for owner_ref in duty.basis_projection_refs:
            basis_owner_to_duties.setdefault(owner_ref, []).append(duty.duty_ref)
        if duty.layer == "LAYER_1":
            for owner_ref in duty.response_object_refs:
                layer1_response_owner_to_duties.setdefault(
                    owner_ref, []
                ).append(duty.duty_ref)
    predecessors = {ref: set() for ref in required_refs}
    successors = {ref: set() for ref in required_refs}
    for dependency in arc.dependency_rows:
        owner_to_duties = (
            layer1_response_owner_to_duties
            if dependency.dependency_kind
            is ArcDependencyKind.ADMITTED_RELATION_DIRECTION
            else basis_owner_to_duties
        )
        for predecessor_ref in owner_to_duties.get(
            dependency.predecessor_owner_ref, ()
        ):
            for successor_ref in owner_to_duties.get(
                dependency.successor_owner_ref, ()
            ):
                if predecessor_ref == successor_ref:
                    continue
                predecessors[successor_ref].add(predecessor_ref)
                successors[predecessor_ref].add(successor_ref)
    return predecessors, successors


def _semantic_topological_orders(
    duty_refs: Tuple[str, ...],
    predecessor_by_duty: dict[str, set[str]],
) -> Tuple[Tuple[str, ...], ...]:
    """Return the semantic canonical order and at most one material alternate."""

    duty_ref_set = set(duty_refs)
    source_index = {ref: index for index, ref in enumerate(duty_refs)}

    def project(*, material_alternate: bool) -> Tuple[str, ...]:
        remaining = set(duty_refs)
        ordered: list[str] = []
        while remaining:
            eligible = tuple(
                ref
                for ref in duty_refs
                if ref in remaining
                and predecessor_by_duty[ref].intersection(duty_ref_set).isdisjoint(
                    remaining
                )
            )
            if not eligible:
                raise Stage1CompositionError(
                    "STAGE1_DISCOURSE_DEPENDENCY_CYCLE_STOP"
                )
            selected = sorted(
                eligible,
                key=lambda ref: source_index[ref],
                reverse=material_alternate,
            )[0]
            remaining.remove(selected)
            ordered.append(selected)
        return tuple(ordered)

    canonical = project(material_alternate=False)
    alternate = project(material_alternate=True)
    return _bounded_layout_dimension((canonical, alternate))


def _material_ordered_partitions(
    topological_orders: Tuple[Tuple[str, ...], ...],
) -> Tuple[Tuple[DutyGroupRow, ...], ...]:
    canonical_order = topological_orders[0]
    canonical = tuple(DutyGroupRow((ref,)) for ref in canonical_order)
    material_order = (
        topological_orders[1]
        if len(topological_orders) == 2
        else canonical_order
    )
    material = tuple(
        DutyGroupRow(material_order[index : index + 2])
        for index in range(0, len(material_order), 2)
    )
    return _bounded_layout_dimension((canonical, material))


def _ordered_partition_refs(
    partition: Tuple[DutyGroupRow, ...],
) -> Tuple[str, ...]:
    return tuple(
        ref for group in partition for ref in group.ordered_duty_refs
    )


def _respects_duty_dependencies(
    ordered_refs: Tuple[str, ...],
    predecessor_by_duty: dict[str, set[str]],
) -> bool:
    positions = {ref: index for index, ref in enumerate(ordered_refs)}
    return len(positions) == len(ordered_refs) and all(
        positions[predecessor_ref] < positions[successor_ref]
        for successor_ref in ordered_refs
        for predecessor_ref in predecessor_by_duty[successor_ref]
        if predecessor_ref in positions
    )


def _layout_seeds(
    duties: Tuple[CompositionDutyView, ...],
    arc: Stage1DiscourseArcView,
) -> Tuple[LayoutPreferenceSeed, ...]:
    required = tuple(row for row in duties if row.retention == "REQUIRED")
    duty_by_ref = {row.duty_ref: row for row in required}
    l1 = tuple(row.duty_ref for row in required if row.layer == "LAYER_1")
    l2 = tuple(row.duty_ref for row in required if row.layer == "LAYER_2")
    if not l1 or not l2:
        raise Stage1CompositionError("STAGE1_LAYOUT_LAYER_COVERAGE_STOP")

    predecessor_by_duty, successor_by_duty = _duty_dependency_maps(
        required, arc
    )
    root_owner_refs = set(arc.root_owner_refs)
    terminal_owner_refs = set(arc.terminal_owner_refs)
    opening_choices = _bounded_layout_dimension(
        row.duty_ref
        for row in required
        if row.layer == "LAYER_1"
        and root_owner_refs.intersection(row.basis_projection_refs)
        and not predecessor_by_duty[row.duty_ref]
    )
    terminal_choices = _bounded_layout_dimension(
        row.duty_ref
        for row in required
        if row.layer == "LAYER_2"
        and terminal_owner_refs.intersection(row.basis_projection_refs)
        and not successor_by_duty[row.duty_ref]
    )
    l1_orders = _semantic_topological_orders(l1, predecessor_by_duty)
    subjective_progressions = _semantic_topological_orders(
        l2, predecessor_by_duty
    )
    layer1_partitions = _material_ordered_partitions(l1_orders)
    layer2_partitions = _material_ordered_partitions(
        subjective_progressions
    )

    exact5_product_size = (
        len(opening_choices)
        * len(layer1_partitions)
        * len(layer2_partitions)
        * len(subjective_progressions)
        * len(terminal_choices)
    )
    if exact5_product_size > 32:
        raise Stage1CompositionError("CANDIDATE_BUDGET_INSUFFICIENT_STOP")

    valid: list[LayoutPreferenceSeed] = []
    for opening_ref in opening_choices:
        for layer1_partition in layer1_partitions:
            layer1_refs = _ordered_partition_refs(layer1_partition)
            if (
                layer1_refs[0] != opening_ref
                or set(layer1_refs) != set(l1)
                or not _respects_duty_dependencies(
                    layer1_refs, predecessor_by_duty
                )
            ):
                continue
            for layer2_partition in layer2_partitions:
                layer2_refs = _ordered_partition_refs(layer2_partition)
                if set(layer2_refs) != set(l2):
                    continue
                for progression in subjective_progressions:
                    if (
                        layer2_refs != progression
                        or not _respects_duty_dependencies(
                            progression, predecessor_by_duty
                        )
                    ):
                        continue
                    for terminal_ref in terminal_choices:
                        if layer2_refs[-1] != terminal_ref:
                            continue
                        seed = LayoutPreferenceSeed(
                            opening_ref,
                            layer1_partition,
                            layer2_partition,
                            progression,
                            terminal_ref,
                        )
                        all_refs = (*layer1_refs, *layer2_refs)
                        if (
                            len(all_refs) == len(set(all_refs))
                            and set(all_refs) == set(duty_by_ref)
                            and _respects_duty_dependencies(
                                all_refs, predecessor_by_duty
                            )
                        ):
                            valid.append(seed)
    seeds = _dedupe_layout_seeds(valid)
    if len(seeds) > exact5_product_size:
        raise Stage1CompositionError("CANDIDATE_RESOURCE_ENVELOPE_STOP")
    return tuple(seeds)


def _fresh_draft(phase_B: Stage1SurfaceCompositionInputs, seed: LayoutPreferenceSeed) -> DraftArtifact:
    _validate_phase_B(phase_B)
    arc = project_stage1_discourse_arc(phase_B)
    duties = _project_duties(phase_B, arc)
    duty_by_ref = {row.duty_ref: row for row in duties}
    required = tuple(row.duty_ref for row in duties if row.retention == "REQUIRED")
    seed_refs = tuple(ref for group in (*seed.layer1_group_rows, *seed.layer2_group_rows) for ref in group.ordered_duty_refs)
    layer2_seed_refs = _ordered_partition_refs(seed.layer2_group_rows)
    if (
        seed not in _layout_seeds(duties, arc)
        or len(seed_refs) != len(set(seed_refs))
        or set(seed_refs) != set(required)
        or seed.subjective_progression_duty_refs != layer2_seed_refs
    ):
        raise Stage1CompositionError("STAGE1_LAYOUT_SEED_COVERAGE_STOP")
    clause_plans = tuple(_clause_plan(duty_by_ref[ref], phase_B) for ref in seed_refs)
    plan_by_duty = {row.duty_ref: row for row in clause_plans}
    units: list[ComposedSentenceUnit] = []
    expressions: list[ResponseObjectExpression] = []
    groups = (*seed.layer1_group_rows, *seed.layer2_group_rows)
    for index, group in enumerate(groups):
        group_duties = tuple(duty_by_ref[ref] for ref in group.ordered_duty_refs)
        layer = group_duties[0].layer
        if any(row.layer != layer for row in group_duties):
            raise Stage1CompositionError("STAGE1_LAYOUT_LAYER_MIX_STOP")
        unit_ref = _ref("draft-unit", (arc.arc_ref, index, group))
        units.append(
            ComposedSentenceUnit(
                unit_ref,
                layer,
                group.ordered_duty_refs,
                tuple(row.sentence_job.value for row in group_duties),
                _unique(
                    ref
                    for row in group_duties
                    for ref in row.response_object_refs
                ),
                tuple(
                    plan_by_duty[ref].clause_plan_ref
                    for ref in group.ordered_duty_refs
                ),
                "",
                "",
            )
        )
        for duty in group_duties:
            refs = duty.response_object_refs
            mode = ResponseObjectExpressionMode.COMPOSITE if len(refs) > 1 or duty.relation_refs else ResponseObjectExpressionMode.EXPLICIT
            plan = plan_by_duty[duty.duty_ref]
            expressions.append(ResponseObjectExpression(_ref("response-object-expression", (plan.clause_plan_ref, unit_ref, refs, duty.relation_refs, mode)), plan.clause_plan_ref, unit_ref, refs, duty.relation_refs, mode, None))
    defects: list[CorrectableDefectRow] = []
    if any(len(group.ordered_duty_refs) > 2 for group in groups):
        defects.append(CorrectableDefectRow(CorrectableDefectKind.INCOMPATIBLE_SENTENCE_LOAD, tuple(ref for group in groups if len(group.ordered_duty_refs) > 2 for ref in group.ordered_duty_refs)))
    optional = tuple(row for row in duties if row.retention == "OPTIONAL")
    suppressed = tuple((row.duty_ref, DutySuppressionReason.NONMATERIAL_OPTIONAL, None) for row in optional)
    return DraftArtifact(arc.projection_ref, arc, seed, duties, tuple(row.duty_ref for row in duties), required, suppressed, (), clause_plans, tuple(expressions), tuple(units), tuple(defects))


def _normal_form_phase_suppression(
    duties: Tuple[CompositionDutyView, ...],
) -> Tuple[Tuple[Any, ...], Tuple[Any, ...]]:
    optional = tuple(row for row in duties if row.retention == "OPTIONAL")
    required = tuple(row for row in duties if row.retention == "REQUIRED")
    if not required or len(required) + len(optional) != len(duties):
        raise Stage1CompositionError("RECOMPOSITION_SUPPRESSION_STOP")
    return (
        tuple(
            (row.duty_ref, DutySuppressionReason.NONMATERIAL_OPTIONAL, None)
            for row in optional
        ),
        (),
    )


def _normal_form_phase_seed_constrained_merge_split(
    seed: LayoutPreferenceSeed,
    duty_by_ref: dict[str, CompositionDutyView],
) -> Tuple[DutyGroupRow, ...]:
    groups = (*seed.layer1_group_rows, *seed.layer2_group_rows)
    if not groups:
        raise Stage1CompositionError("STAGE1_LAYOUT_SEED_COVERAGE_STOP")
    seen_refs: set[str] = set()
    for group in groups:
        if not 1 <= len(group.ordered_duty_refs) <= 2:
            raise Stage1CompositionError("RECOMPOSITION_SENTENCE_LOAD_STOP")
        group_duties = tuple(
            duty_by_ref.get(ref) for ref in group.ordered_duty_refs
        )
        if (
            any(duty is None or duty.retention != "REQUIRED" for duty in group_duties)
            or len({duty.layer for duty in group_duties if duty is not None}) != 1
            or any(ref in seen_refs for ref in group.ordered_duty_refs)
        ):
            raise Stage1CompositionError("STAGE1_LAYOUT_SEED_COVERAGE_STOP")
        seen_refs.update(group.ordered_duty_refs)
    if seen_refs != set(duty_by_ref):
        raise Stage1CompositionError("STAGE1_LAYOUT_SEED_COVERAGE_STOP")
    return tuple(groups)


def _normal_form_phase_dependency_information_order(
    groups: Tuple[DutyGroupRow, ...],
    duties: Tuple[CompositionDutyView, ...],
    arc: Stage1DiscourseArcView,
) -> Tuple[DutyGroupRow, ...]:
    duty_by_ref = {row.duty_ref: row for row in duties}
    input_refs = tuple(ref for group in groups for ref in group.ordered_duty_refs)
    owner_to_duties: dict[str, list[str]] = {}
    for duty in duties:
        for owner in duty.basis_projection_refs:
            owner_to_duties.setdefault(owner, []).append(duty.duty_ref)
    predecessor_by_duty: dict[str, set[str]] = {ref: set() for ref in input_refs}
    for edge in arc.dependency_rows:
        for predecessor in owner_to_duties.get(edge.predecessor_owner_ref, ()):
            for successor in owner_to_duties.get(edge.successor_owner_ref, ()):
                if predecessor != successor and successor in predecessor_by_duty:
                    predecessor_by_duty[successor].add(predecessor)
    source_order = {ref: index for index, ref in enumerate(input_refs)}
    remaining = set(input_refs)
    ordered_refs: list[str] = []
    while remaining:
        eligible = tuple(
            ref
            for ref in remaining
            if predecessor_by_duty[ref].isdisjoint(remaining)
        )
        if not eligible:
            raise Stage1CompositionError("STAGE1_DISCOURSE_DEPENDENCY_CYCLE_STOP")
        chosen = min(
            eligible,
            key=lambda ref: (
                0 if duty_by_ref[ref].layer == "LAYER_1" else 1,
                source_order[ref],
            ),
        )
        remaining.remove(chosen)
        ordered_refs.append(chosen)
    group_by_ref = {
        ref: group for group in groups for ref in group.ordered_duty_refs
    }
    emitted: set[DutyGroupRow] = set()
    ordered_groups: list[DutyGroupRow] = []
    for ref in ordered_refs:
        group = group_by_ref[ref]
        if group not in emitted:
            emitted.add(group)
            ordered_groups.append(group)
    return tuple(ordered_groups)


def _normal_form_phase_reference_antecedent_recalculation(
    groups: Tuple[DutyGroupRow, ...],
    duty_by_ref: dict[str, CompositionDutyView],
    plan_by_duty: dict[str, ClausePlan],
    arc: Stage1DiscourseArcView,
) -> Tuple[Tuple[ResponseObjectExpression, ...], Tuple[ComposedSentenceUnit, ...]]:
    expressions: list[ResponseObjectExpression] = []
    units: list[ComposedSentenceUnit] = []
    antecedent_by_refs: dict[
        Tuple[str, ...], Tuple[str, str, int, Tuple[str, ...]]
    ] = {}
    for index, group in enumerate(groups):
        duties = tuple(duty_by_ref[ref] for ref in group.ordered_duty_refs)
        layer = duties[0].layer
        if any(row.layer != layer for row in duties):
            raise Stage1CompositionError("STAGE1_LAYOUT_LAYER_MIX_STOP")
        unit_ref = _ref("sealed-unit", (arc.arc_ref, index, group))
        unit_anchor_refs = _unique(
            ref for row in duties for ref in row.response_object_refs
        )
        units.append(
            ComposedSentenceUnit(
                unit_ref,
                layer,
                group.ordered_duty_refs,
                tuple(row.sentence_job.value for row in duties),
                unit_anchor_refs,
                tuple(plan_by_duty[ref].clause_plan_ref for ref in group.ordered_duty_refs),
                "",
                "",
            )
        )
        for duty in duties:
            refs = duty.response_object_refs
            prior = antecedent_by_refs.get(refs)
            plan = plan_by_duty[duty.duty_ref]
            same_layer_prior = (
                prior is not None
                and prior[1] == layer
                and prior[2] < index
                and (prior[2] == index - 1 or len(refs) > 1)
            )
            exact_immediate_layer_transition = (
                prior is not None
                and prior[1] == "LAYER_1"
                and layer == "LAYER_2"
                and prior[2] == index - 1
                and prior[3] == refs
            )
            if (
                prior is not None
                and (same_layer_prior or exact_immediate_layer_transition)
                and not duty.relation_refs
                and plan.predicate_valency
                is not PredicateValency.TRIADIC_ACTOR_TARGET_BOUNDARY
            ):
                mode = ResponseObjectExpressionMode.ANAPHORIC
                antecedent = prior[0]
            else:
                mode = (
                    ResponseObjectExpressionMode.COMPOSITE
                    if len(refs) > 1 or duty.relation_refs
                    else ResponseObjectExpressionMode.EXPLICIT
                )
                antecedent = None
            expression = ResponseObjectExpression(
                _ref(
                    "response-object-expression",
                    (plan.clause_plan_ref, unit_ref, refs, duty.relation_refs, mode, antecedent),
                ),
                plan.clause_plan_ref,
                unit_ref,
                refs,
                duty.relation_refs,
                mode,
                antecedent,
            )
            expressions.append(expression)
            antecedent_by_refs[refs] = (
                unit_ref,
                layer,
                index,
                unit_anchor_refs,
            )
    return tuple(expressions), tuple(units)


def _normal_form_phase_topic_speaker_connective_terminal(
    groups: Tuple[DutyGroupRow, ...],
    seed: LayoutPreferenceSeed,
    duty_by_ref: dict[str, CompositionDutyView],
) -> None:
    ordered_refs = tuple(ref for group in groups for ref in group.ordered_duty_refs)
    if (
        not ordered_refs
        or ordered_refs[0] != seed.opening_duty_ref
        or seed.terminal_duty_ref not in groups[-1].ordered_duty_refs
        or any(
            duty_by_ref[ref].layer == "LAYER_1"
            for ref in ordered_refs[
                next(
                    (
                        index
                        for index, ref in enumerate(ordered_refs)
                        if duty_by_ref[ref].layer == "LAYER_2"
                    ),
                    len(ordered_refs),
                ) :
            ]
        )
    ):
        raise Stage1CompositionError("RECOMPOSITION_TERMINAL_OR_TOPIC_STOP")


def _shared_endpoint_relation_chain(
    duty_refs: Tuple[str, ...],
    duty_by_ref: dict[str, CompositionDutyView],
    plan_by_duty: dict[str, ClausePlan],
) -> Optional[Tuple[CompositionDutyView, CompositionDutyView]]:
    """Recognize an existing exact2 relation group with one typed shared endpoint."""

    if len(duty_refs) != 2:
        return None
    first = duty_by_ref.get(duty_refs[0])
    second = duty_by_ref.get(duty_refs[1])
    if (
        first is None
        or second is None
        or first.layer != second.layer
        or first.layer != "LAYER_1"
        or first.sentence_job is not SentenceJob.TRACE_CHANGE_OR_SEQUENCE
        or second.sentence_job
        is not SentenceJob.RELATE_COEXISTING_OR_TENSION
        or len(first.relation_refs) != 1
        or len(second.relation_refs) != 1
        or len(first.response_object_refs) != 2
        or len(second.response_object_refs) != 2
        or first.response_object_refs[1] != second.response_object_refs[0]
        or len(
            set(first.response_object_refs).union(second.response_object_refs)
        )
        != 3
    ):
        return None
    first_plan = plan_by_duty.get(first.duty_ref)
    second_plan = plan_by_duty.get(second.duty_ref)
    if (
        first_plan is None
        or second_plan is None
        or first_plan.semantic_clause_kind
        is not SemanticClauseKind.ADMITTED_RELATION
        or second_plan.semantic_clause_kind
        is not SemanticClauseKind.ADMITTED_RELATION
        or first_plan.predicate_valency
        is not PredicateValency.DYADIC_RELATION_ENDPOINTS
        or second_plan.predicate_valency
        is not PredicateValency.DYADIC_RELATION_ENDPOINTS
    ):
        return None
    shared_ref = first.response_object_refs[1]
    first_shared = tuple(
        row for row in first_plan.scalar_constraint_rows if row.owner_ref == shared_ref
    )
    second_shared = tuple(
        row for row in second_plan.scalar_constraint_rows if row.owner_ref == shared_ref
    )
    if (
        len(first_shared) != 1
        or len(second_shared) != 1
        or (
            first_shared[0].polarity,
            first_shared[0].modality,
            first_shared[0].time_scope,
        )
        != (
            second_shared[0].polarity,
            second_shared[0].modality,
            second_shared[0].time_scope,
        )
    ):
        return None
    return first, second


def _quoted_source_object(value: str) -> str:
    nominalizer = _structural_lexeme("structural:nominalizer.v1")
    if not value.endswith(nominalizer):
        raise Stage1CompositionError("STAGE1_SOURCE_EXPRESSION_STOP")
    return value[: -len(nominalizer)]


def _shared_endpoint_conjunct(value: str, carrier: str) -> str:
    if carrier == "すでに実感があり":
        return "".join((_quoted_source_object(value), "という実感があり"))
    if carrier == "今も実感があり":
        return "".join((_quoted_source_object(value), "という実感が今もあり"))
    if not carrier:
        return "".join((value, "が続き"))
    return "".join((value, _relation_endpoint_particle(carrier), carrier))


def _new_endpoint_followup(
    value: str,
    constraint: ClauseScalarConstraintRow,
) -> str:
    if constraint.modality == "wish":
        nominal = "願い"
    elif constraint.modality == "feeling":
        nominal = "実感"
    elif constraint.modality == "uncertain":
        nominal = "迷い"
    elif constraint.polarity == "negative" or constraint.modality == "possibility":
        nominal = "留保"
    else:
        nominal = "こと"
    return "".join(
        (
            _quoted_source_object(value),
            "という",
            nominal,
            "も残っています",
        )
    )


def _shared_endpoint_relation_chain_surface(
    chain: Tuple[CompositionDutyView, CompositionDutyView],
    plan_by_duty: dict[str, ClausePlan],
    expression_by_plan: dict[str, ResponseObjectExpression],
    phase_B: Stage1SurfaceCompositionInputs,
) -> str:
    first, second = chain
    first_plan = plan_by_duty[first.duty_ref]
    second_plan = plan_by_duty[second.duty_ref]
    first_expression = expression_by_plan[first_plan.clause_plan_ref]
    second_expression = expression_by_plan[second_plan.clause_plan_ref]
    if (
        first_expression.expression_mode
        is not ResponseObjectExpressionMode.COMPOSITE
        or second_expression.expression_mode
        is not ResponseObjectExpressionMode.COMPOSITE
        or first_expression.basis_semantic_refs != first.response_object_refs
        or second_expression.basis_semantic_refs != second.response_object_refs
    ):
        raise Stage1CompositionError("STAGE1_RELATION_ENDPOINT_CLOSURE_STOP")
    first_owner, _ = _duty_semantics(first, phase_B)
    second_owner, _ = _duty_semantics(second, phase_B)
    if (
        first_owner.relation_operator
        not in {
            RelationOperator.TEMPORALLY_PRECEDES,
            RelationOperator.ACTION_PRECEDES_CHANGE,
        }
        or second_owner.relation_operator
        not in {RelationOperator.COEXISTS_WITH, RelationOperator.TENSION_WITH}
    ):
        raise Stage1CompositionError("STAGE1_RELATION_ENDPOINT_CLOSURE_STOP")
    first_objects = tuple(
        _source_expression(
            ref,
            phase_B,
            _frame_for_semantic_ref(first_owner, ref, phase_B),
        )
        for ref in first.response_object_refs
    )
    final_ref = second.response_object_refs[1]
    final_object = _source_expression(
        final_ref,
        phase_B,
        _frame_for_semantic_ref(second_owner, final_ref, phase_B),
    )
    first_carriers = _functional_surface_lexemes_by_role(first_plan)
    if len(first_carriers) != 2:
        raise Stage1CompositionError("STAGE1_RELATION_ROLE_STOP")
    left_carrier = "、".join((*first_carriers[0][1], *first_carriers[0][2]))
    shared_carrier = "、".join((*first_carriers[1][1], *first_carriers[1][2]))
    final_constraints = tuple(
        row for row in second_plan.scalar_constraint_rows if row.owner_ref == final_ref
    )
    if len(final_constraints) != 1:
        raise Stage1CompositionError("STAGE1_RELATION_ROLE_STOP")
    left_surface = (
        "".join(
            (
                first_objects[0],
                _relation_endpoint_particle(left_carrier),
                left_carrier,
                "、そのあとに",
            )
        )
        if left_carrier
        else "".join((first_objects[0], "のあとに"))
    )
    relation_connective = (
        "ただ"
        if second_owner.relation_operator is RelationOperator.TENSION_WITH
        else "同時に"
    )
    return "".join(
        (
            left_surface,
            _shared_endpoint_conjunct(first_objects[1], shared_carrier),
            "、",
            relation_connective,
            "、",
            _new_endpoint_followup(final_object, final_constraints[0]),
            _structural_lexeme("structural:sentence.v1"),
        )
    )


def _normal_form_phase_expression_selection_final_linearization(
    units: Tuple[ComposedSentenceUnit, ...],
    expressions: Tuple[ResponseObjectExpression, ...],
    duty_by_ref: dict[str, CompositionDutyView],
    plan_by_duty: dict[str, ClausePlan],
    phase_B: Stage1SurfaceCompositionInputs,
) -> Tuple[ComposedSentenceUnit, ...]:
    expression_by_plan = {
        row.clause_plan_ref: row for row in expressions
    }
    terminal = _structural_lexeme("structural:sentence.v1")
    joiner = _structural_lexeme("structural:sentence-join.v1")
    output: list[ComposedSentenceUnit] = []
    emlis_subject_established = False
    for unit in units:
        chain = _shared_endpoint_relation_chain(
            unit.duty_refs,
            duty_by_ref,
            plan_by_duty,
        )
        if chain is not None:
            surfaces = (
                _shared_endpoint_relation_chain_surface(
                    chain,
                    plan_by_duty,
                    expression_by_plan,
                    phase_B,
                ),
            )
        else:
            projected_surfaces: list[str] = []
            for ref in unit.duty_refs:
                duty = duty_by_ref[ref]
                plan = plan_by_duty[ref]
                subject_visible = True
                if duty.layer == "LAYER_2":
                    subject_visible = (
                        not emlis_subject_established
                        or plan.speaker_requirement
                        is SpeakerRequirement.EMLIS_EXPLICIT_REQUIRED
                    )
                    emlis_subject_established = True
                projected_surfaces.append(
                    _surface_for_plan(
                        duty,
                        plan,
                        expression_by_plan[plan.clause_plan_ref],
                        phase_B,
                        emlis_subject_visible=subject_visible,
                    )
                )
            surfaces = tuple(projected_surfaces)
        text = joiner.join(surface.removesuffix(terminal) for surface in surfaces) + terminal
        if not text.endswith(terminal) or text.count(terminal) < 1:
            raise Stage1CompositionError("RECOMPOSITION_FINAL_LINEARIZATION_STOP")
        output.append(
            ComposedSentenceUnit(
                unit.unit_ref,
                unit.layer,
                unit.duty_refs,
                unit.sentence_job_refs,
                unit.basis_anchor_refs,
                unit.clause_plan_refs,
                text,
                hashlib.sha256(text.encode("utf-8")).hexdigest(),
            )
        )
    return tuple(output)


def _project_post_normalization_defect_rows(
    *,
    arc: Stage1DiscourseArcView,
    seed: LayoutPreferenceSeed,
    duties: Tuple[CompositionDutyView, ...],
    required_duty_refs: Tuple[str, ...],
    suppressed_duty_rows: Tuple[Any, ...],
    clause_plans: Tuple[ClausePlan, ...],
    expressions: Tuple[ResponseObjectExpression, ...],
    units: Tuple[ComposedSentenceUnit, ...],
) -> Tuple[CorrectableDefectRow, ...]:
    """Total typed detector used to prove the post-normalization exact-zero.

    The detector deliberately reads no generated sentence as semantic input.
    Text inspection is limited to the registered terminal/whitespace contract.
    """

    defects: dict[CorrectableDefectKind, set[str]] = {
        kind: set() for kind in CorrectableDefectKind
    }
    duty_refs = tuple(row.duty_ref for row in duties)
    duty_by_ref = {row.duty_ref: row for row in duties}
    plan_by_duty = {row.duty_ref: row for row in clause_plans}
    plan_by_ref = {row.clause_plan_ref: row for row in clause_plans}
    expression_by_plan = {row.clause_plan_ref: row for row in expressions}
    unit_index_by_ref = {row.unit_ref: index for index, row in enumerate(units)}
    unit_index_by_duty = {
        duty_ref: index
        for index, unit in enumerate(units)
        for duty_ref in unit.duty_refs
    }
    visible_duty_refs = tuple(
        duty_ref for unit in units for duty_ref in unit.duty_refs
    )
    expected_required = tuple(
        row.duty_ref for row in duties if row.retention == "REQUIRED"
    )
    expected_suppressed = tuple(
        (row.duty_ref, DutySuppressionReason.NONMATERIAL_OPTIONAL, None)
        for row in duties
        if row.retention == "OPTIONAL"
    )
    if (
        len(duty_refs) != len(set(duty_refs))
        or required_duty_refs != expected_required
        or len(visible_duty_refs) != len(set(visible_duty_refs))
        or set(visible_duty_refs) != set(required_duty_refs)
        or suppressed_duty_rows != expected_suppressed
    ):
        defects[CorrectableDefectKind.NONMATERIAL_OR_DUPLICATE_DUTY].update(
            duty_refs
        )

    if (
        not 2 <= len(units) <= 9
        or any(
            not 1 <= len(unit.duty_refs) <= 2
            or any(ref not in duty_by_ref for ref in unit.duty_refs)
            or len({duty_by_ref[ref].layer for ref in unit.duty_refs}) != 1
            for unit in units
        )
    ):
        defects[CorrectableDefectKind.INCOMPATIBLE_SENTENCE_LOAD].update(
            ref for unit in units for ref in unit.duty_refs
        )

    owner_unit_indexes: dict[str, set[int]] = {}
    for duty_ref, unit_index in unit_index_by_duty.items():
        duty = duty_by_ref.get(duty_ref)
        if duty is None:
            continue
        for owner_ref in (
            *duty.basis_projection_refs,
            *duty.response_object_refs,
        ):
            owner_unit_indexes.setdefault(owner_ref, set()).add(unit_index)

    def dependency_valid(edge: ArcDependencyRow) -> bool:
        predecessors = owner_unit_indexes.get(edge.predecessor_owner_ref, set())
        successors = owner_unit_indexes.get(edge.successor_owner_ref, set())
        return bool(predecessors and successors) and min(predecessors) <= min(
            successors
        )

    invalid_dependencies = tuple(
        row.arc_dependency_ref
        for row in arc.dependency_rows
        if not dependency_valid(row)
    )
    if invalid_dependencies:
        defects[
            CorrectableDefectKind.DEPENDENCY_OR_INFORMATION_ORDER
        ].update(invalid_dependencies)

    expression_refs = tuple(row.response_object_expression_ref for row in expressions)
    if (
        len(expression_refs) != len(set(expression_refs))
        or len(expression_by_plan) != len(expressions)
        or set(expression_by_plan) != set(plan_by_ref)
    ):
        defects[
            CorrectableDefectKind.UNRESOLVED_OR_DISTANT_REFERENT
        ].update(expression_refs or tuple(plan_by_ref))
    for expression in expressions:
        own_index = unit_index_by_ref.get(expression.unit_ref)
        plan = plan_by_ref.get(expression.clause_plan_ref)
        if own_index is None or plan is None:
            defects[
                CorrectableDefectKind.UNRESOLVED_OR_DISTANT_REFERENT
            ].add(expression.response_object_expression_ref)
            continue
        if expression.expression_mode is ResponseObjectExpressionMode.ANAPHORIC:
            antecedent_index = unit_index_by_ref.get(
                expression.antecedent_unit_ref or ""
            )
            valid = antecedent_index is not None and antecedent_index < own_index
        else:
            valid = expression.antecedent_unit_ref is None and bool(
                expression.basis_semantic_refs
            )
        if not valid:
            defects[
                CorrectableDefectKind.UNRESOLVED_OR_DISTANT_REFERENT
            ].add(expression.response_object_expression_ref)

    invalid_scalar_plan_refs: list[str] = []
    for plan in clause_plans:
        try:
            scalar_rows_are_exact = (
                plan.scalar_surface_realization_rows
                == project_scalar_surface_realization_rows(
                    plan.clause_plan_ref,
                    plan.scalar_constraint_rows,
                )
            )
        except Stage1CompositionError:
            scalar_rows_are_exact = False
        if not scalar_rows_are_exact:
            invalid_scalar_plan_refs.append(plan.clause_plan_ref)
    if invalid_scalar_plan_refs:
        defects[CorrectableDefectKind.RELATION_OR_CONNECTIVE_FIT].update(
            invalid_scalar_plan_refs
        )

    first_l2 = next(
        (index for index, unit in enumerate(units) if unit.layer == "LAYER_2"),
        len(units),
    )
    topic_valid = (
        bool(units)
        and bool(units[0].duty_refs)
        and units[0].duty_refs[0] == seed.opening_duty_ref
        and not any(unit.layer == "LAYER_1" for unit in units[first_l2:])
        and all(
            (
                plan.speaker_requirement
                in {
                    SpeakerRequirement.EMLIS_ZERO_ALLOWED,
                    SpeakerRequirement.EMLIS_EXPLICIT_REQUIRED,
                }
            )
            == (duty_by_ref[plan.duty_ref].layer == "LAYER_2")
            for plan in clause_plans
        )
    )
    if not topic_valid:
        defects[CorrectableDefectKind.TOPIC_OR_SPEAKER_PLACEMENT].update(
            unit.unit_ref for unit in units
        )

    invalid_relations: list[str] = []
    for duty in duties:
        if not duty.relation_refs or duty.retention != "REQUIRED":
            continue
        plan = plan_by_duty.get(duty.duty_ref)
        expression = None if plan is None else expression_by_plan.get(
            plan.clause_plan_ref
        )
        specs = () if plan is None else tuple(
            row
            for row in CONSTRUCTION_REGISTRY
            if row.construction_id == plan.construction_id
        )
        if (
            len(duty.relation_refs) != 1
            or plan is None
            or plan.semantic_clause_kind is not SemanticClauseKind.ADMITTED_RELATION
            or expression is None
            or expression.expression_mode
            is not ResponseObjectExpressionMode.COMPOSITE
            or len(specs) != 1
            or not specs[0].relation_combinators
        ):
            invalid_relations.append(duty.duty_ref)
    if invalid_relations:
        defects[CorrectableDefectKind.RELATION_OR_CONNECTIVE_FIT].update(
            invalid_relations
        )

    invalid_subjective = tuple(
        row.arc_dependency_ref
        for row in arc.dependency_rows
        if row.dependency_kind
        in {
            ArcDependencyKind.SUBJECTIVE_CONTENT_DEPENDENCY,
            ArcDependencyKind.UNFINISHED_TERMINAL,
        }
        and not dependency_valid(row)
    )
    if invalid_subjective:
        defects[CorrectableDefectKind.SUBJECTIVE_SEQUENCE_FIT].update(
            invalid_subjective
        )

    terminal = _structural_lexeme("structural:sentence.v1")
    terminal_duties = tuple(
        row
        for row in duties
        if row.duty_ref == seed.terminal_duty_ref
        and set(row.basis_projection_refs).intersection(arc.terminal_owner_refs)
    )
    terminal_valid = (
        bool(units)
        and len(terminal_duties) == 1
        and seed.terminal_duty_ref in units[-1].duty_refs
        and all(
            type(unit.text) is str
            and type(unit.surface_text_sha256) is str
            and bool(unit.text)
            and unit.text.endswith(terminal)
            and "\n" not in unit.text
            and "\r" not in unit.text
            and unit.surface_text_sha256
            == hashlib.sha256(unit.text.encode("utf-8")).hexdigest()
            for unit in units
        )
    )
    if not terminal_valid:
        defects[CorrectableDefectKind.TERMINAL_FIT].update(
            (seed.terminal_duty_ref, *(unit.unit_ref for unit in units))
        )

    return tuple(
        CorrectableDefectRow(kind, tuple(sorted(owner_refs)))
        for kind in CorrectableDefectKind
        if (owner_refs := defects[kind])
    )


def normalize_to_normal_form(
    artifact: DraftArtifact | NormalizedDraftArtifact,
    seed: LayoutPreferenceSeed,
    phase_B_inputs: Stage1SurfaceCompositionInputs,
) -> NormalizedDraftArtifact:
    """Pure exact-six-phase normalizer; it never reads generated text as meaning."""

    if (
        type(artifact) not in {DraftArtifact, NormalizedDraftArtifact}
        or type(seed) is not LayoutPreferenceSeed
        or type(phase_B_inputs) is not Stage1SurfaceCompositionInputs
    ):
        raise Stage1CompositionError("RECOMPOSITION_NORMAL_FORM_INPUT_STOP")
    _validate_phase_B(phase_B_inputs)
    if artifact.projection_ref != _projection_ref(phase_B_inputs.projection) or artifact.layout_preference_seed != seed:
        raise Stage1CompositionError("RECOMPOSITION_NORMAL_FORM_INPUT_STOP")
    fresh = _fresh_draft(phase_B_inputs, seed)
    if type(artifact) is DraftArtifact and artifact != fresh:
        raise Stage1CompositionError("RECOMPOSITION_NORMAL_FORM_INPUT_STOP")
    duties = fresh.composition_duty_rows
    duty_by_ref = {row.duty_ref: row for row in duties}
    plan_by_duty = {row.duty_ref: row for row in fresh.clause_plan_rows}
    suppressed_duties, suppressed_claims = _normal_form_phase_suppression(duties)
    groups = _normal_form_phase_seed_constrained_merge_split(seed, duty_by_ref)
    groups = _normal_form_phase_dependency_information_order(
        groups, duties, fresh.discourse_arc
    )
    expressions, unit_skeletons = _normal_form_phase_reference_antecedent_recalculation(
        groups, duty_by_ref, plan_by_duty, fresh.discourse_arc
    )
    _normal_form_phase_topic_speaker_connective_terminal(groups, seed, duty_by_ref)
    sentence_units = _normal_form_phase_expression_selection_final_linearization(
        unit_skeletons,
        expressions,
        duty_by_ref,
        plan_by_duty,
        phase_B_inputs,
    )
    post_defect_rows = _project_post_normalization_defect_rows(
        arc=fresh.discourse_arc,
        seed=fresh.layout_preference_seed,
        duties=duties,
        required_duty_refs=fresh.required_duty_refs,
        suppressed_duty_rows=suppressed_duties,
        clause_plans=fresh.clause_plan_rows,
        expressions=expressions,
        units=sentence_units,
    )
    if post_defect_rows:
        raise Stage1CompositionError("RECOMPOSITION_NORMAL_FORM_UNPROVEN_STOP")
    normalized = NormalizedDraftArtifact(
        fresh.projection_ref,
        fresh.discourse_arc,
        fresh.layout_preference_seed,
        duties,
        fresh.full_duty_refs,
        fresh.required_duty_refs,
        suppressed_duties,
        suppressed_claims,
        fresh.clause_plan_rows,
        expressions,
        sentence_units,
        post_defect_rows,
        CMEE_STAGE1_NORMAL_FORM_VERSION,
        True,
        tuple(NormalFormPhase),
    )
    if type(artifact) is NormalizedDraftArtifact and artifact != normalized:
        raise Stage1CompositionError("RECOMPOSITION_NORMAL_FORM_UNPROVEN_STOP")
    return normalized


def canonical_normalized_bytes(artifact: NormalizedDraftArtifact) -> bytes:
    if (
        type(artifact) is not NormalizedDraftArtifact
        or artifact.projection_ref != artifact.discourse_arc.projection_ref
        or artifact.full_duty_refs
        != tuple(row.duty_ref for row in artifact.composition_duty_rows)
        or artifact.required_duty_refs
        != tuple(
            row.duty_ref
            for row in artifact.composition_duty_rows
            if row.retention == "REQUIRED"
        )
        or artifact.correctable_defect_rows
        or artifact.normal_form_version != CMEE_STAGE1_NORMAL_FORM_VERSION
        or artifact.normal_form_applied is not True
        or artifact.normalization_phase_trace != tuple(NormalFormPhase)
        or _project_post_normalization_defect_rows(
            arc=artifact.discourse_arc,
            seed=artifact.layout_preference_seed,
            duties=artifact.composition_duty_rows,
            required_duty_refs=artifact.required_duty_refs,
            suppressed_duty_rows=artifact.suppressed_duty_rows,
            clause_plans=artifact.clause_plan_rows,
            expressions=artifact.response_object_expression_rows,
            units=artifact.sentence_units,
        )
    ):
        raise Stage1CompositionError("RECOMPOSITION_NORMAL_FORM_UNPROVEN_STOP")
    return stage1_canonical_json_bytes(artifact)


def _derive_profile_applicability_mask(
    arc: Stage1DiscourseArcView,
    duties: Tuple[CompositionDutyView, ...],
) -> Tuple[bool, ...]:
    """Derive the pool-global exact-eight applicability mask from frozen rows."""

    if (
        type(arc) is not Stage1DiscourseArcView
        or type(duties) is not tuple
        or not duties
        or any(type(row) is not CompositionDutyView for row in duties)
        or any(row.projection_ref != arc.projection_ref for row in duties)
    ):
        raise Stage1CompositionError("STAGE1_PROFILE_APPLICABILITY_STOP")
    introduced_layer1_refs = {
        semantic_ref
        for row in duties
        if row.retention == "REQUIRED" and row.layer == "LAYER_1"
        for semantic_ref in row.response_object_refs
    }
    concrete_before_abstract_is_applicable = bool(
        introduced_layer1_refs.intersection(arc.layer2_response_target_refs)
    )
    return (
        True,
        concrete_before_abstract_is_applicable,
        True,
        True,
        True,
        True,
        True,
        True,
    )


def _derive_discourse_preference_profile_with_frozen_applicability(
    normalized_artifact: NormalizedDraftArtifact,
    *,
    applicability_mask: Tuple[bool, ...],
) -> DiscoursePreferenceProfile:
    """Project one member using the pool's already-frozen applicability."""

    if (
        type(normalized_artifact) is not NormalizedDraftArtifact
        or normalized_artifact.correctable_defect_rows
        or normalized_artifact.normalization_phase_trace
        != tuple(NormalFormPhase)
    ):
        raise Stage1CompositionError("STAGE1_PROFILE_INPUT_STOP")
    try:
        canonical_normalized_bytes(normalized_artifact)
    except Stage1CompositionError:
        raise Stage1CompositionError("STAGE1_PROFILE_INPUT_STOP") from None
    units = normalized_artifact.sentence_units
    arc = normalized_artifact.discourse_arc
    if not units:
        raise Stage1CompositionError("STAGE1_PROFILE_INPUT_STOP")
    unit_index_by_duty = {
        duty_ref: index
        for index, unit in enumerate(units)
        for duty_ref in unit.duty_refs
    }
    if len(unit_index_by_duty) != sum(len(unit.duty_refs) for unit in units):
        raise Stage1CompositionError("STAGE1_PROFILE_INPUT_STOP")
    duty_by_ref = {
        row.duty_ref: row for row in normalized_artifact.composition_duty_rows
    }
    plan_by_duty = {
        row.duty_ref: row for row in normalized_artifact.clause_plan_rows
    }
    owner_unit_indexes: dict[str, set[int]] = {}
    for duty_ref, unit_index in unit_index_by_duty.items():
        duty = duty_by_ref[duty_ref]
        for owner_ref in (
            *duty.basis_projection_refs,
            *duty.response_object_refs,
        ):
            owner_unit_indexes.setdefault(owner_ref, set()).add(unit_index)

    def dependency_is_aligned(row: ArcDependencyRow) -> bool:
        predecessor_indexes = owner_unit_indexes.get(row.predecessor_owner_ref, set())
        successor_indexes = owner_unit_indexes.get(row.successor_owner_ref, set())
        if not predecessor_indexes or not successor_indexes:
            return False
        if row.dependency_kind is ArcDependencyKind.ADMITTED_RELATION_DIRECTION:
            relation_duties = tuple(
                duty
                for duty in normalized_artifact.composition_duty_rows
                if row.source_relation_ref in duty.relation_refs
            )
            return (
                len(relation_duties) == 1
                and plan_by_duty[relation_duties[0].duty_ref].semantic_clause_kind
                is SemanticClauseKind.ADMITTED_RELATION
                and min(predecessor_indexes) <= min(successor_indexes)
            )
        return min(predecessor_indexes) <= min(successor_indexes)

    group_sizes = tuple(len(unit.duty_refs) for unit in units)
    available_relation_chains = {
        (first.duty_ref, second.duty_ref)
        for first in normalized_artifact.composition_duty_rows
        for second in normalized_artifact.composition_duty_rows
        if _shared_endpoint_relation_chain(
            (first.duty_ref, second.duty_ref),
            duty_by_ref,
            plan_by_duty,
        )
        is not None
    }
    grouped_relation_chains = {
        unit.duty_refs
        for unit in units
        if _shared_endpoint_relation_chain(
            unit.duty_refs,
            duty_by_ref,
            plan_by_duty,
        )
        is not None
    }
    sentence_load_aligned = (
        all(size == 1 for size in group_sizes)
        if not available_relation_chains
        else grouped_relation_chains == available_relation_chains
        and all(
            len(unit.duty_refs) == 1
            or unit.duty_refs in grouped_relation_chains
            for unit in units
        )
    )
    aligned_order = all(
        dependency_is_aligned(row) for row in arc.dependency_rows
    )
    first_l2 = next(
        (index for index, row in enumerate(units) if row.layer == "LAYER_2"),
        len(units),
    )
    l1_before_l2 = not any(
        unit.layer == "LAYER_1" for unit in units[first_l2:]
    )
    target_introductions = tuple(
        min(
            (
                index
                for index, unit in enumerate(units)
                if unit.layer == "LAYER_1"
                and target_ref in unit.basis_anchor_refs
            ),
            default=len(units),
        )
        for target_ref in arc.layer2_response_target_refs
    )
    target_responses = tuple(
        min(
            (
                index
                for index, unit in enumerate(units)
                if unit.layer == "LAYER_2"
                and target_ref in unit.basis_anchor_refs
            ),
            default=-1,
        )
        for target_ref in arc.layer2_response_target_refs
    )
    concrete_before_abstract = bool(target_introductions) and all(
        0 <= introduction < response < len(units)
        for introduction, response in zip(
            target_introductions, target_responses, strict=True
        )
    )
    expression_by_ref = {
        row.response_object_expression_ref: row
        for row in normalized_artifact.response_object_expression_rows
    }
    unit_index_by_ref = {row.unit_ref: index for index, row in enumerate(units)}
    referent_continuity = len(expression_by_ref) == len(
        normalized_artifact.response_object_expression_rows
    )
    for expression in normalized_artifact.response_object_expression_rows:
        own_index = unit_index_by_ref.get(expression.unit_ref)
        if own_index is None:
            referent_continuity = False
            break
        if expression.expression_mode is ResponseObjectExpressionMode.ANAPHORIC:
            antecedent_index = unit_index_by_ref.get(
                expression.antecedent_unit_ref or ""
            )
            if antecedent_index is None or antecedent_index >= own_index:
                referent_continuity = False
                break
        elif expression.antecedent_unit_ref is not None:
            referent_continuity = False
            break
    relation_duties = tuple(
        row.duty_ref
        for row in normalized_artifact.composition_duty_rows
        if row.relation_refs and row.retention == "REQUIRED"
    )
    expression_by_plan = {
        row.clause_plan_ref: row
        for row in normalized_artifact.response_object_expression_rows
    }
    relation_visible = all(
        ref in unit_index_by_duty
        and plan_by_duty[ref].semantic_clause_kind
        is SemanticClauseKind.ADMITTED_RELATION
        and expression_by_plan.get(plan_by_duty[ref].clause_plan_ref) is not None
        and expression_by_plan[plan_by_duty[ref].clause_plan_ref].expression_mode
        is ResponseObjectExpressionMode.COMPOSITE
        for ref in relation_duties
    )
    subjective_dependencies = tuple(
        row
        for row in arc.dependency_rows
        if row.dependency_kind
        in {
            ArcDependencyKind.SUBJECTIVE_CONTENT_DEPENDENCY,
            ArcDependencyKind.UNFINISHED_TERMINAL,
        }
    )
    subjective_sequence = all(
        dependency_is_aligned(row) for row in subjective_dependencies
    )
    terminal = (
        normalized_artifact.layout_preference_seed.terminal_duty_ref
        in units[-1].duty_refs
        and any(
            set(row.basis_projection_refs).intersection(arc.terminal_owner_refs)
            for row in normalized_artifact.composition_duty_rows
            if row.duty_ref
            == normalized_artifact.layout_preference_seed.terminal_duty_ref
        )
    )
    observed = (
        aligned_order,
        concrete_before_abstract,
        sentence_load_aligned,
        l1_before_l2
        and units[0].duty_refs[0]
        == normalized_artifact.layout_preference_seed.opening_duty_ref,
        referent_continuity,
        relation_visible,
        subjective_sequence,
        terminal,
    )
    if (
        type(applicability_mask) is not tuple
        or len(applicability_mask) != 8
        or any(type(value) is not bool for value in applicability_mask)
        or any(
            not is_applicable
            for index, is_applicable in enumerate(applicability_mask)
            if index != 1
        )
    ):
        raise Stage1CompositionError("STAGE1_PROFILE_APPLICABILITY_STOP")
    fits = tuple(
        ProfileFit.ARC_ALIGNED
        if is_applicable and is_aligned
        else ProfileFit.PERMITTED
        if is_applicable
        else ProfileFit.NOT_APPLICABLE
        for is_applicable, is_aligned in zip(
            applicability_mask, observed, strict=True
        )
    )
    evidence_fields = tuple(ProfileEvidenceField)
    rule_kinds = tuple(ProfileEvidenceRuleKind)
    owner_rows = (
        tuple(row.arc_dependency_ref for row in arc.dependency_rows),
        tuple(
            ref
            for unit in units
            if unit.layer == "LAYER_1"
            for ref in unit.duty_refs
        ),
        tuple(unit.unit_ref for unit in units),
        tuple(unit.unit_ref for unit in units),
        tuple(
            row.response_object_expression_ref
            for row in normalized_artifact.response_object_expression_rows
        ),
        relation_duties,
        tuple(
            row.arc_dependency_ref for row in subjective_dependencies
        ),
        (normalized_artifact.layout_preference_seed.terminal_duty_ref,),
    )
    not_applicable_evidence_owner_refs = (units[0].unit_ref,)
    not_applicable_form_ref = "profile-form:not-applicable.v1"
    evidence_rows: list[ProfileEvidenceRow] = []
    for field, rule, owners, fit in zip(
        evidence_fields, rule_kinds, owner_rows, fits, strict=True
    ):
        evidence_owner_refs = owners or not_applicable_evidence_owner_refs
        preferred_form_ref = (
            not_applicable_form_ref
            if fit is ProfileFit.NOT_APPLICABLE
            else f"profile-form:{field.value.lower()}:preferred.v1"
        )
        observed_form_ref = (
            not_applicable_form_ref
            if fit is ProfileFit.NOT_APPLICABLE
            else f"profile-form:{field.value.lower()}:{fit.value.lower()}.v1"
        )
        evidence_rows.append(
            ProfileEvidenceRow(
                _ref(
                    "profile-evidence",
                    (
                        normalized_artifact.projection_ref,
                        field,
                        rule,
                        evidence_owner_refs,
                        preferred_form_ref,
                        observed_form_ref,
                        fit,
                    ),
                ),
                field,
                rule,
                evidence_owner_refs,
                preferred_form_ref,
                observed_form_ref,
                fit,
            )
        )
    evidence = tuple(evidence_rows)
    return DiscoursePreferenceProfile(*fits, evidence)


def derive_discourse_preference_profile(
    normalized_artifact: NormalizedDraftArtifact,
) -> DiscoursePreferenceProfile:
    """Public exact-eight projector with no caller-owned result or mask input."""

    if type(normalized_artifact) is not NormalizedDraftArtifact:
        raise Stage1CompositionError("STAGE1_PROFILE_INPUT_STOP")
    applicability_mask = _derive_profile_applicability_mask(
        normalized_artifact.discourse_arc,
        normalized_artifact.composition_duty_rows,
    )
    return _derive_discourse_preference_profile_with_frozen_applicability(
        normalized_artifact,
        applicability_mask=applicability_mask,
    )


def _profile_key(profile: DiscoursePreferenceProfile) -> Tuple[int, ...]:
    order = {
        ProfileFit.ARC_ALIGNED: 0,
        ProfileFit.PERMITTED: 1,
    }
    values = tuple(
        getattr(profile, name)
        for name in (
            "information_flow_fit",
            "concrete_before_abstract_fit",
            "sentence_load_fit",
            "topic_transition_fit",
            "referent_continuity_fit",
            "relation_realization_fit",
            "subjective_sequence_fit",
            "terminal_fit",
        )
    )
    if (
        any(type(value) is not ProfileFit for value in values)
        or any(
            value is ProfileFit.NOT_APPLICABLE
            for index, value in enumerate(values)
            if index != 1
        )
    ):
        raise Stage1CompositionError("STAGE1_PROFILE_APPLICABILITY_STOP")
    return tuple(
        order[value]
        for index, value in enumerate(values)
        if not (index == 1 and value is ProfileFit.NOT_APPLICABLE)
    )


def _visible_key(artifact: NormalizedDraftArtifact) -> bytes:
    return stage1_canonical_json_bytes((artifact.projection_ref, tuple((unit.layer, unit.text, unit.duty_refs, unit.sentence_job_refs, unit.basis_anchor_refs) for unit in artifact.sentence_units)))


def _composition_signature(artifact: NormalizedDraftArtifact) -> str:
    duty_by_ref = {row.duty_ref: row for row in artifact.composition_duty_rows}
    structural_material = (
        tuple(
            tuple(duty_by_ref[ref].sentence_job for ref in group.ordered_duty_refs)
            for group in artifact.layout_preference_seed.layer1_group_rows
        ),
        tuple(
            tuple(duty_by_ref[ref].sentence_job for ref in group.ordered_duty_refs)
            for group in artifact.layout_preference_seed.layer2_group_rows
        ),
        tuple(
            (
                row.semantic_clause_kind,
                row.predicate_valency,
                row.grammatical_role_assignment_rule,
                row.syntactic_orientation,
                row.speaker_requirement,
                row.construction_id,
                tuple(
                    (
                        scalar.clause_argument_role,
                        scalar.polarity,
                        scalar.modality,
                        scalar.time_scope,
                    )
                    for scalar in row.scalar_constraint_rows
                ),
            )
            for row in artifact.clause_plan_rows
        ),
        tuple(
            row.expression_mode for row in artifact.response_object_expression_rows
        ),
        tuple(
            (unit.layer, unit.sentence_job_refs, len(unit.duty_refs))
            for unit in artifact.sentence_units
        ),
    )
    return hashlib.sha256(
        b"COCOLON_STAGE1_COMPOSITION_SIGNATURE_V1\0"
        + stage1_canonical_json_bytes(structural_material)
    ).hexdigest()


def _stage_a_exact_member_key_bytes(
    projection_ref: str,
    composition_signature: str,
    normalized_bytes: bytes,
) -> bytes:
    material = bytearray(b"COCOLON_STAGE1_EXACT_MEMBER_V1\0")
    for payload in (
        projection_ref.encode("utf-8"),
        composition_signature.encode("ascii"),
        normalized_bytes,
    ):
        material.extend(len(payload).to_bytes(8, "big"))
        material.extend(payload)
    return bytes(material)


def compose_stage1_from_projection(
    phase_B: Stage1SurfaceCompositionInputs,
) -> Stage1CompositionResult:
    """Sole Phase-B facade: draft, exact6 normalize, profile, reducers and rank."""

    arc = project_stage1_discourse_arc(phase_B)
    duties = _project_duties(phase_B, arc)
    seeds = _layout_seeds(duties, arc)
    applicability_mask = _derive_profile_applicability_mask(arc, duties)
    _validate_phase_B(phase_B)
    stage_a: dict[str, tuple[bytes, NormalizedDraftArtifact, str]] = {}
    for seed in seeds:
        draft = _fresh_draft(phase_B, seed)
        normalized = normalize_to_normal_form(draft, seed, phase_B)
        normalized_bytes = canonical_normalized_bytes(normalized)
        signature = _composition_signature(normalized)
        exact_member_key = _stage_a_exact_member_key_bytes(
            normalized.projection_ref, signature, normalized_bytes
        )
        digest = hashlib.sha256(exact_member_key).hexdigest()
        prior = stage_a.get(digest)
        if prior and prior[0] != exact_member_key:
            raise Stage1CompositionError("CANDIDATE_EXACT_KEY_COLLISION_STOP")
        stage_a[digest] = (exact_member_key, normalized, signature)
    profiled_members = tuple(
        (
            normalized,
            _derive_discourse_preference_profile_with_frozen_applicability(
                normalized,
                applicability_mask=applicability_mask,
            ),
            signature,
        )
        for _member_bytes, normalized, signature in stage_a.values()
    )
    projected_applicability_masks = tuple(
        tuple(
            getattr(profile, field) is not ProfileFit.NOT_APPLICABLE
            for field in PROFILE_RULE_REGISTRY
        )
        for _normalized, profile, _signature in profiled_members
    )
    if not projected_applicability_masks or any(
        mask != applicability_mask for mask in projected_applicability_masks
    ):
        raise Stage1CompositionError("STAGE1_PROFILE_APPLICABILITY_STOP")
    classes: dict[
        bytes,
        tuple[NormalizedDraftArtifact, DiscoursePreferenceProfile, str],
    ] = {}
    for normalized, profile, signature in profiled_members:
        key = _visible_key(normalized)
        member = (normalized, profile, signature)
        prior = classes.get(key)
        if prior is None or (_profile_key(profile), signature) < (_profile_key(prior[1]), prior[2]):
            classes[key] = member
        elif (_profile_key(profile), signature) == (_profile_key(prior[1]), prior[2]) and canonical_normalized_bytes(normalized) != canonical_normalized_bytes(prior[0]):
            raise Stage1CompositionError("DEDUPE_REPRESENTATIVE_NONUNIQUE_STOP")
    ordered = sorted(classes.values(), key=lambda row: (_profile_key(row[1]), row[2]))
    keys = tuple((_profile_key(profile), signature) for _normalized, profile, signature in ordered)
    if len(keys) != len(set(keys)):
        raise Stage1CompositionError("GLOBAL_RANK_NONUNIQUE_STOP")
    candidates = tuple(
        ArtifactCompositionCandidate(
            _ref("artifact-composition-candidate", (normalized.projection_ref, profile, signature)),
            signature,
            index + 1,
            "01-primary" if index == 0 else "02-alternate",
            normalized,
            profile,
            normalized.sentence_units,
        )
        for index, (normalized, profile, signature) in enumerate(ordered[:2])
    )
    if not candidates:
        raise Stage1CompositionError("NO_VALID_SURFACE")
    return Stage1CompositionResult(LANGUAGE_CORE_IDENTITY, arc, len(stage_a), candidates, candidates[0])


PROFILE_RULE_REGISTRY = (
    "information_flow_fit",
    "concrete_before_abstract_fit",
    "sentence_load_fit",
    "topic_transition_fit",
    "referent_continuity_fit",
    "relation_realization_fit",
    "subjective_sequence_fit",
    "terminal_fit",
)


def validate_language_core_registry_invariant() -> None:
    """Validate the frozen grammar/asset surface without request data.

    This is intentionally stricter than the construction-only Step 1 guard:
    every registry used by the final linearizer is checked here, before the
    language-core identity is frozen.  The validator accepts typed fragments
    and morphology only; a completed sentence, case identifier, raw-source
    selector, or duplicate typed rule is a fail-closed error.
    """

    validate_stage1_anti_template_registry_invariant(
        tuple(field.name for field in fields(ConstructionSpec)),
        (
            "grammatical_shape_key",
            "predicate_valency",
            "syntactic_orientation",
        ),
    )
    if (
        len(CONSTRUCTION_REGISTRY) != 8
        or len({row.construction_id for row in CONSTRUCTION_REGISTRY}) != 8
        or any(row.argument_slots != row.role_order for row in CONSTRUCTION_REGISTRY)
    ):
        raise Stage1CompositionError("LANGUAGE_CORE_CONSTRUCTION_REGISTRY_STOP")

    forbidden_fragments = (
        "case_id",
        "case_family",
        "fixture",
        "exact8",
        "raw_text",
        "raw_pattern",
        "source_regex",
        "semantic_keyword",
        "expected_text",
        "finished_surface",
        "finished_clause",
        "finished_sentence",
        "sentence_template",
        "clause_template",
    )
    registry_types = (
        ExpressionAssetSpec,
        RelationMorphologyAssetSpec,
        ScalarMorphologyAssetSpec,
        SourceScalarMorphologyAssetSpec,
        ParticipantLexemeAssetSpec,
        StructuralSurfaceAssetSpec,
    )
    if any(
        any(fragment in field.name.lower() for fragment in forbidden_fragments)
        for registry_type in registry_types
        for field in fields(registry_type)
    ):
        raise Stage1CompositionError("LANGUAGE_CORE_ANTI_TEMPLATE_REGISTRY_STOP")

    expression_ids = tuple(row.expression_asset_id for row in EXPRESSION_ASSET_REGISTRY)
    if (
        len(expression_ids) != len(set(expression_ids))
        or any(
            not row.predicate_lexemes
            or any(
                not token
                or any(mark in token for mark in ("。", "！", "？", "\n", "\r"))
                for token in row.predicate_lexemes
            )
            for row in EXPRESSION_ASSET_REGISTRY
        )
    ):
        raise Stage1CompositionError("LANGUAGE_CORE_EXPRESSION_ASSET_STOP")

    relation_operators = tuple(
        row.relation_operator for row in RELATION_MORPHOLOGY_ASSET_REGISTRY
    )
    if (
        len(relation_operators) != len(set(relation_operators))
        or set(relation_operators)
        != set(RelationOperator) - {RelationOperator.NO_RELATION_CLAIM}
        or any(
            not row.morphology_asset_id
            or any(
                mark in token
                for token in (row.left_particle, row.connective, row.right_particle)
                for mark in ("。", "！", "？", "\n", "\r")
            )
            for row in RELATION_MORPHOLOGY_ASSET_REGISTRY
        )
    ):
        raise Stage1CompositionError("LANGUAGE_CORE_RELATION_MORPHOLOGY_STOP")

    morphology_ids = tuple(
        row.morphology_asset_id for row in SCALAR_MORPHOLOGY_ASSET_REGISTRY
    )
    compatibility_keys = tuple(
        (row.scalar_axis, value, row.realization_mode)
        for row in SCALAR_MORPHOLOGY_ASSET_REGISTRY
        for value in row.compatible_values
    )
    if (
        len(morphology_ids) != len(set(morphology_ids))
        or len(compatibility_keys) != len(set(compatibility_keys))
        or {row.scalar_axis for row in SCALAR_MORPHOLOGY_ASSET_REGISTRY}
        != set(ClauseScalarAxis)
    ):
        raise Stage1CompositionError("LANGUAGE_CORE_SCALAR_MORPHOLOGY_STOP")
    for row in SCALAR_MORPHOLOGY_ASSET_REGISTRY:
        if row.realization_mode is ScalarSurfaceRealizationMode.FUSED_IN_REGISTERED_PART:
            expected_target = RegisteredFunctionalSlotRef.PREDICATE_HEAD.value
        elif row.realization_mode is ScalarSurfaceRealizationMode.OVERT_FUNCTIONAL_PART:
            expected_target = RegisteredFunctionalSlotRef.QUALIFIER.value
        elif row.realization_mode is ScalarSurfaceRealizationMode.UNMARKED_DEFAULT:
            expected_target = None
        else:
            raise Stage1CompositionError("LANGUAGE_CORE_SCALAR_MORPHOLOGY_STOP")
        if (
            row.realization_target_slot_ref != expected_target
            or not row.compatible_values
            or (
                row.realization_mode
                is ScalarSurfaceRealizationMode.UNMARKED_DEFAULT
            )
            != (row.morphemes == ())
            or any(
                not morpheme
                or any(mark in morpheme for mark in ("。", "！", "？", "\n", "\r"))
                for morpheme in row.morphemes
            )
        ):
            raise Stage1CompositionError("LANGUAGE_CORE_SCALAR_MORPHOLOGY_STOP")

    source_scalar_ids = tuple(
        row.morphology_asset_id
        for row in SOURCE_SCALAR_MORPHOLOGY_ASSET_REGISTRY
    )
    source_scalar_keys = tuple(
        (row.predicate_kind, row.required_attribute_codes)
        for row in SOURCE_SCALAR_MORPHOLOGY_ASSET_REGISTRY
    )
    if (
        len(source_scalar_ids) != len(set(source_scalar_ids))
        or len(source_scalar_keys) != len(set(source_scalar_keys))
        or {row.predicate_kind for row in SOURCE_SCALAR_MORPHOLOGY_ASSET_REGISTRY}
        != {"action", "change", "residue", "unfinished"}
        or any(
            not row.morphology_asset_id
            or not row.predicate_kind
            or not row.required_attribute_codes
            or len(row.required_attribute_codes)
            != len(set(row.required_attribute_codes))
            or not (row.terminal_rewrites or row.preserved_finite_terminals)
            or len(row.preserved_finite_terminals)
            != len(set(row.preserved_finite_terminals))
            or len(tuple(source for source, _target in row.terminal_rewrites))
            != len(set(source for source, _target in row.terminal_rewrites))
            or set(source for source, _target in row.terminal_rewrites)
            & set(row.preserved_finite_terminals)
            or any(
                not terminal
                or any(mark in terminal for mark in ("。", "！", "？", "\n", "\r"))
                for pair in row.terminal_rewrites
                for terminal in pair
            )
            or any(
                not terminal
                or any(mark in terminal for mark in ("。", "！", "？", "\n", "\r"))
                for terminal in row.preserved_finite_terminals
            )
            for row in SOURCE_SCALAR_MORPHOLOGY_ASSET_REGISTRY
        )
    ):
        raise Stage1CompositionError("LANGUAGE_CORE_SOURCE_SCALAR_MORPHOLOGY_STOP")

    participant_ids = tuple(row.participant_ref for row in PARTICIPANT_ASSET_REGISTRY)
    structural_ids = tuple(
        row.structural_asset_id for row in STRUCTURAL_ASSET_REGISTRY
    )
    if (
        len(participant_ids) != len(set(participant_ids))
        or len(structural_ids) != len(set(structural_ids))
        or any(
            not row.surface_lexeme or "。" in row.surface_lexeme
            for row in PARTICIPANT_ASSET_REGISTRY
        )
        or any(not row.surface_lexeme for row in STRUCTURAL_ASSET_REGISTRY)
        or FUNCTIONAL_ASSET_REGISTRY
        != (
            tuple(slot.value for slot in RegisteredFunctionalSlotRef),
            SCALAR_MORPHOLOGY_ASSET_REGISTRY,
            RELATION_MORPHOLOGY_ASSET_REGISTRY,
            SOURCE_SCALAR_MORPHOLOGY_ASSET_REGISTRY,
        )
        or tuple(PROFILE_RULE_REGISTRY)
        != tuple(f"{field.value.lower()}_fit" for field in ProfileEvidenceField)
    ):
        raise Stage1CompositionError("LANGUAGE_CORE_ASSET_REGISTRY_STOP")


LANGUAGE_CORE_EXTERNAL_PATHS = (
    "ai/services/ai_inference/cocolon_meaning_experience_engine/contracts.py",
    "ai/services/ai_inference/cocolon_meaning_experience_engine/emlis_stage1_response.py",
    "ai/services/ai_inference/cocolon_meaning_experience_engine/emlis_v1a.py",
    "ai/services/ai_inference/emlis_ai_grounded_observation_plan.py",
    "ai/services/ai_inference/cocolon_text_generation_core/composer.py",
    "ai/services/ai_inference/cocolon_text_generation_core/adapters/emlis_observation_composer.py",
)
_COMPOSITION_PATH = "ai/services/ai_inference/cocolon_meaning_experience_engine/emlis_stage1_composition.py"


_NO_IMPLICIT_DEFAULT = "NO_IMPLICIT_DEFAULT"
_CONTRACT_MANIFEST_SCHEMA_VERSION = (
    "cocolon.cmee.v1a.stage1_language_core_contract_manifest.v1"
)


def _logical_field_type(field_name: str) -> str:
    """Return a stable logical type tag without inspecting a runtime class."""

    if field_name.endswith(("_rows_by_unit", "_plan_rows_by_unit")):
        return "ORDERED_TUPLE_OF_ORDERED_TYPED_ROWS"
    if field_name.endswith(("_rows", "_refs", "_ids", "_bindings", "_ranges")):
        return "ORDERED_TUPLE"
    if field_name.endswith(("_ref", "_id", "_key", "_handle")):
        return "TYPED_IDENTITY"
    if field_name in {
        "normal_form_applied",
        "zero_subject_eligibility",
        "addressee_deictic_context",
    }:
        return "BOOLEAN"
    if field_name in {
        "part_index",
        "surface_scalar_start",
        "surface_scalar_end",
        "rank",
    }:
        return "INTEGER"
    if field_name in {
        "content",
        "asserted_subjective_proposition",
        "row_ref_free_proposition",
        "discourse_arc",
        "layout_preference_seed",
        "sealed_plan",
        "surface_derivation",
        "subject_binding",
        "unit_plan_row",
        "coverage_key",
    }:
        return "FROZEN_TYPED_OBJECT"
    return "CLOSED_SCALAR_OR_FROZEN_TYPED_OBJECT"


def _logical_contract_descriptor(
    type_name: str,
    version: str,
    field_spec: str,
    constraints: tuple[str, ...],
    derivation: str,
) -> tuple[Any, ...]:
    field_rows = []
    for token in field_spec.split():
        field_name, cardinality = token.split("=", 1)
        field_rows.append(
            (
                ("field_name", field_name),
                ("logical_type", _logical_field_type(field_name)),
                ("cardinality", cardinality),
                ("default", _NO_IMPLICIT_DEFAULT),
                (
                    "conditional_constraints",
                    (
                        "FIELD_INCLUDED_IN_CANONICAL_IDENTITY",
                        "TYPE_LEVEL_CONSTRAINTS_APPLY",
                    ),
                ),
                ("derivation", derivation),
            )
        )
    if not field_rows or len({row[0][1] for row in field_rows}) != len(field_rows):
        raise Stage1CompositionError("LANGUAGE_CORE_CONTRACT_DESCRIPTOR_STOP")
    return (
        ("type_name", type_name),
        ("logical_version", version),
        ("serialization_boundary", "REQUEST_LOCAL_PRIVATE_CANONICAL_VIEW"),
        ("fields", tuple(field_rows)),
        ("conditional_constraints", constraints),
        ("derivation", derivation),
    )


# This literal exact-59 inventory is deliberately independent of dataclass
# introspection.  Logical Step-4 types which are not runtime-active in Step 2
# are still frozen here with their complete approved field order/cardinality.
_LOGICAL_CONTRACT_FIELD_SPECS = (
    ("EmlisSubjectiveClaim", "response-v2", "schema_version=exact1 subjective_claim_id=exact1 parent_duty_ref=exact1 speaker_owner=exact1 claim_domain=exact1 subjective_mode=exact1 asserted_subjective_proposition=exact1 basis_observation_contribution_refs=1..N basis_semantic_refs=1..N source_reception_act_refs=1..N value_principle_refs=0..N user_fact_effect=exact0 forbidden_promotions=1..N subjective_responsibility_refs=1..N selected_subjective_opportunity_key=exact1", ("NESTED_V2_PROPOSITION", "LINEAGE_EXACT_COPY"), "FINAL_CLAIM_PROJECTOR"),
    ("SubjectiveBasisBinding", "basis-binding-v1", "projection_preimage_ref=exact1 binding_ref=exact1 contribution_ref=exact1 semantic_ref=exact1 role=exact1", ("UPSTREAM_ONLY_PREIMAGE",), "SUBJECTIVE_BASIS_PROJECTOR"),
    ("SourceQualifierBinding", "source-qualifier-v1", "projection_preimage_ref=exact1 source_qualifier_binding_ref=exact1 basis_binding_ref=exact1 source_candidate_ref=exact1 source_argument_role=0..1 canonical_qualifier_codes=exact3 polarity=exact1 modality=exact1 time_scope=exact1", ("ONE_ROW_PER_BASIS", "AXIS_EXACT3"), "SOURCE_QUALIFIER_PROJECTOR"),
    ("PolicyBasisBinding", "policy-basis-v1", "projection_preimage_ref=exact1 binding_ref=exact1 owner_kind=exact1 owner_ref=exact1 role=exact1", ("OWNER_KIND_DISCRIMINATED",), "POLICY_BASIS_PROJECTOR"),
    ("EmlisAffectContent", "proposition-v2", "category=exact1 intensity=exact1 elicitor_bindings=1..N", ("CONCRETE_ELICITOR_REQUIRED",), "AFFECT_OPPORTUNITY_PROJECTOR"),
    ("EmlisAppraisalContent", "proposition-v2", "dimension=exact1 operation=exact1 appraised_bindings=1..N focal_relation_ref=0..1 protected_bindings=0..N basis_contribution_refs=1..N", ("DIMENSION_OPERATION_CLOSED_PAIR",), "APPRAISAL_OPPORTUNITY_PROJECTOR"),
    ("EmlisRelationalPosition", "proposition-v2", "relational_position_kind=exact1 stance_operator=exact1 target_bindings=1..N boundary_bindings=0..N commitment=exact1 closure=exact1", ("COMMITMENT_DERIVES_POSITION_KIND",), "RELATIONAL_OPPORTUNITY_PROJECTOR"),
    ("RowRefFreeValueApplication", "policy-pre-id-v1", "principle_ref=exact1 material_risk=exact1 policy_basis_binding_refs=1..N protected_subjective_binding_refs=1..N", ("NO_POLICY_ROW_OR_CLAIM_REF",), "ROW_REF_FREE_VALUE_PROJECTOR"),
    ("RowRefFreeMaterialValueContent", "policy-pre-id-v1", "value_applications=1..N target_bindings=1..N boundary_bindings=exact0", ("PRINCIPLE_ORDER_UNIQUE", "TARGET_EQUALS_PROTECTED_UNION"), "ROW_REF_FREE_VALUE_PROJECTOR"),
    ("RowRefFreeSubjectivePropositionV2", "proposition-pre-id-v2", "schema_version=exact1 content_kind=exact1 subjective_mode=exact1 subjective_operator=exact1 target_contribution_refs=1..N primary_target_refs=1..N boundary_target_refs=0..N response_object_refs=1..N basis_binding_refs=1..N source_qualifier_binding_refs=1..N focal_relation_ref=0..1 affect_content=0..1 appraisal_content=0..1 material_value_content=0..1 relational_position=0..1 referenced_actor_refs=0..N referenced_experiencer_refs=0..N addressee_role=exact1 assertion_modality=exact1 epistemic_scope=exact1", ("CONTENT_DISCRIMINANT_EXACT1", "NO_POLICY_ROW_OR_CLAIM_REF"), "ROW_REF_FREE_PROPOSITION_PROJECTOR"),
    ("SubjectiveClaimDraft", "claim-draft-v1", "draft_handle=exact1 projection_preimage_ref=exact1 claim_schema_version=exact1 claim_domain=exact1 owner_ref=exact1 speaker_owner=exact1 parent_duty_ref=exact1 subjective_responsibility_refs=1..N selected_subjective_opportunity_key=exact1 basis_observation_contribution_refs=1..N basis_semantic_refs=1..N source_reception_act_refs=1..N value_principle_refs=0..N forbidden_promotions=1..N user_fact_effect=exact0 row_ref_free_proposition=exact1", ("IMMUTABLE_AFTER_FORBIDDEN_WRAPPER", "DRAFT_HANDLE_EXCLUDED_FROM_HASH"), "SUBJECTIVE_CLAIM_DRAFT_PROJECTOR"),
    ("MaterialValueContent", "proposition-v2", "value_applications=1..N target_bindings=1..N boundary_bindings=exact0", ("PRINCIPLE_ORDER_UNIQUE",), "FINAL_VALUE_PROJECTOR"),
    ("ValueApplication", "proposition-v2", "principle_ref=exact1 material_risk=exact1 policy_application_row_refs=1..N policy_basis_binding_refs=1..N protected_subjective_binding_refs=1..N", ("MATCHING_VISIBILITY_ROWS_EXACT_COVER",), "FINAL_VALUE_PROJECTOR"),
    ("Stage1PolicyFeatureVector", "policy-feature-v1", "PRESENT_BURDEN=boolean PRESENT_RESIDUE=boolean OBSERVE_BURDEN=boolean PRESERVE_RESIDUE=boolean PRESENT_DIRECTION=boolean PRESENT_CHANGE=boolean PRESENT_ACTUAL_OUTPUT=boolean COEXISTS_WITH=boolean TENSION_WITH=boolean PRESENT_UNFINISHED=boolean PRESERVE_UNFINISHED=boolean material_unknown=boolean actual_output_retention_required=boolean", ("EXACT13_INDEPENDENT_BOOLEAN_DOMAIN",), "VALIDATED_CONTRIBUTION_FEATURE_EXTRACTOR"),
    ("PolicyApplicationSeed", "policy-seed-v1", "affected_claim_draft_handle=exact1 application_kind=exact1 principle_ref=exact1 material_risk=exact1 policy_basis_binding_refs=1..N material_risk_evidence_refs=1..N protected_subjective_binding_refs=0..N source_reception_act_ref=0..1 act_basis_contribution_refs=0..N disposition=exact1", ("BODY_FREE_PRE_ID",), "POLICY_SEED_PROJECTOR"),
    ("PolicyApplicationRow", "policy-row-v1", "policy_application_row_ref=exact1 affected_claim_policy_target_key=exact1 application_kind=exact1 principle_ref=exact1 material_risk=exact1 policy_basis_binding_refs=1..N material_risk_evidence_refs=1..N protected_subjective_binding_refs=0..N affected_claim_ref=exact1 source_reception_act_ref=0..1 act_basis_contribution_refs=0..N disposition=exact1 visible_claim_ref=0..1", ("SUPPRESSION_OR_VISIBILITY_DISCRIMINATED", "POST_CLAIM_REFS_EXCLUDED_FROM_ROW_ID"), "POLICY_ROW_PROJECTOR"),
    ("SubjectivePropositionV2", "proposition-v2", "schema_version=exact1 content_kind=exact1 subjective_mode=exact1 subjective_operator=exact1 target_contribution_refs=1..N primary_target_refs=1..N boundary_target_refs=0..N response_object_refs=1..N basis_binding_refs=1..N source_qualifier_binding_refs=1..N focal_relation_ref=0..1 affect_content=0..1 appraisal_content=0..1 material_value_content=0..1 relational_position=0..1 referenced_actor_refs=0..N referenced_experiencer_refs=0..N addressee_role=exact1 assertion_modality=exact1 epistemic_scope=exact1", ("CONTENT_DISCRIMINANT_EXACT1", "MODE_OPERATOR_MODALITY_TOTAL_DERIVATION"), "FINAL_PROPOSITION_PROJECTOR"),
    ("EmlisStage1Projection", "response-v2", "schema_version=exact1 projection_id=exact1 projection_preimage_ref=exact1 grounded_graph_ref=exact1 parent_observation_duty_ref=exact1 parent_reception_duty_ref=exact1 interpretation_candidates=1..N meaning_field=exact1 observation_contributions=1..N subjective_claims=1..4 ordered_observation_refs=1..N ordered_subjective_refs=1..4 retained_reception_act_ids=1..N observation_depth_class=exact1 subjective_depth_class=exact1 temperature_class=exact1 reception_style_policy_ref=exact1 emlis_value_policy_ref=exact1 composition_policy_ref=exact1 low_level_grammar_policy_ref=exact1 subjective_responsibility_rows=1..N subjective_opportunity_rows=1..N subjective_facet_suppression_rows=0..N subjective_basis_binding_rows=1..N source_qualifier_binding_rows=1..N policy_basis_binding_rows=0..N policy_application_rows=0..N", ("FULL_ROW_TABLE_EXACT_COVER", "SUBJECTIVE_DEPTH_POST_CLAIM_ONLY"), "FINAL_PROJECTION_SEAL"),
    ("Stage1SubjectivePlanningInputs", "phase-a-v1", "admitted_source=exact1 grounded_graph=exact1 grounded_plan=exact1 parent_plan=exact1 projection_preimage_ref=exact1 interpretation_candidate_rows=1..N meaning_field=exact1 observation_contribution_rows=1..N retained_reception_act_rows=1..N material_unknown_refs=0..N observation_depth_class=exact1 temperature_class=exact1 reception_style_policy_ref=exact1 emlis_value_policy_ref=exact1 contribution_to_candidate_ref_map=1..N resolved_grounded_frame_by_candidate_ref=1..N relation_endpoint_grounded_candidate_ref_by_binding_key=0..N qualifier_value_by_candidate_scope_axis_key=1..N construction_registry_snapshot=exact1 expression_asset_registry_snapshot=exact1 response_object_registry_snapshot=exact1 functional_asset_registry_snapshot=exact1 participant_asset_registry_snapshot=exact1 structural_asset_registry_snapshot=exact1 profile_rule_registry_snapshot=exact1", ("FINAL_SUBJECTIVE_OUTPUT_EXACT0", "FULL_DOMAIN_FROZEN_MAPS"), "RESPONSE_PHASE_A_ADAPTER"),
    ("Stage1SurfaceCompositionInputs", "phase-b-v1", "admitted_source=exact1 grounded_graph=exact1 grounded_plan=exact1 parent_plan=exact1 projection=exact1 resolved_grounded_frame_by_candidate_ref=1..N relation_endpoint_grounded_candidate_ref_by_binding_key=0..N qualifier_value_by_candidate_scope_axis_key=1..N addressee_deictic_context=exact1 section_speaker_owner_ref=0..1 construction_registry_snapshot=exact1 expression_asset_registry_snapshot=exact1 response_object_registry_snapshot=exact1 functional_asset_registry_snapshot=exact1 participant_asset_registry_snapshot=exact1 structural_asset_registry_snapshot=exact1 profile_rule_registry_snapshot=exact1", ("PHASE_A_BYTES_EXACT_MATCH", "FINAL_PROJECTION_EXACT1"), "RESPONSE_PHASE_B_ADAPTER"),
    ("EmlisSubjectiveMeaningPlan", "meaning-plan-v1", "projection_preimage_ref=exact1 subjective_claim_rows=1..4 thought_support_status=exact1 content_bearing_thought_claim_refs=0..N retained_reception_act_refs=1..N subjective_responsibility_rows=1..N subjective_opportunity_rows=1..N responsibility_coverage_rows=1..N subjective_basis_binding_rows=1..N source_qualifier_binding_rows=1..N policy_basis_binding_rows=0..N policy_application_rows=0..N subjective_facet_suppression_rows=0..N", ("REQUEST_LOCAL_VIEW_NOT_ARTIFACT", "OPPORTUNITY_PARTITION_EXACT_COVER"), "SUBJECTIVE_MEANING_PROJECTOR"),
    ("SubjectiveResponsibilityRow", "responsibility-v1", "responsibility_ref=exact1 responsibility_kind=exact1 owner_component_refs=1..N retained_reception_act_refs=1..N", ("CLOSED_EXACT4_KIND",), "RESPONSIBILITY_PROJECTOR"),
    ("SubjectiveOpportunityRow", "opportunity-v1", "opportunity_key=exact1 responsibility_refs=1..N content_kind=exact1 content=exact1 specificity_key=exact1", ("ROW_REF_FREE_CONTENT",), "OPPORTUNITY_ENUMERATOR"),
    ("SubjectiveFacetSuppressionRow", "facet-suppression-v1", "suppressed_opportunity_key=exact1 reason=exact1 absorbed_by_selected_opportunity_key=0..1", ("NONMATERIAL_HAS_NO_ABSORBER",), "NONSELECTED_OPPORTUNITY_PARTITION"),
    ("Stage1DiscourseArcView", "arc-v1", "arc_ref=exact1 projection_ref=exact1 nucleus_owner_refs=1..N supporting_owner_refs=0..N admitted_relation_refs=0..N dependency_rows=1..N root_owner_refs=1..N unresolved_or_residue_refs=0..N terminal_owner_refs=1..N layer2_response_target_refs=1..N", ("FULL_ARC_TOTAL_PROJECTION",), "DISCOURSE_ARC_PROJECTOR"),
    ("ArcDependencyRow", "arc-dependency-v1", "arc_dependency_ref=exact1 predecessor_owner_ref=exact1 successor_owner_ref=exact1 dependency_kind=exact1 source_relation_ref=0..1", ("SOURCE_RELATION_IFF_ADMITTED_RELATION",), "ARC_DEPENDENCY_PROJECTOR"),
    ("CompositionDutyView", "duty-v1", "duty_ref=exact1 projection_ref=exact1 layer=exact1 sentence_job=exact1 basis_projection_refs=1..N relation_refs=0..1 response_object_refs=0..N retention=exact1", ("CLOSED_OWNER_TO_JOB_PRECEDENCE",), "COMPOSITION_DUTY_PROJECTOR"),
    ("DutySuppressionRow", "suppression-v1", "duty_ref=exact1 reason=exact1 absorbed_by_duty_ref=0..1", ("NONMATERIAL_HAS_NO_ABSORBER",), "VISIBILITY_PARTITION_PROJECTOR"),
    ("ClaimSuppressionRow", "suppression-v1", "subjective_claim_ref=exact1 reason=exact1 absorbed_by_subjective_claim_ref=0..1", ("FULLY_SUPPRESSED_CLAIMS_ONLY",), "VISIBILITY_PARTITION_PROJECTOR"),
    ("DiscourseReferenceStateRow", "reference-state-v1", "reference_state_ref=exact1 projection_ref=exact1 prior_clause_plan_ref=0..1 active_referent_refs=0..1 active_referent_establishment_kind=exact1 immediately_prior_subject_owner_ref=0..1 competing_subject_owner_refs=0..N addressee_deictic_context=exact1 active_speaker_kind=exact1 active_speaker_owner_ref=0..1 section_speaker_owner_ref=0..1 competing_speaker_owner_refs=0..N speaker_resolution_status=exact1 established_by_refs=1..N", ("FRESH_PRIOR_PLAN_TRANSITION", "ACTIVE_AND_COMPETING_DISJOINT"), "REFERENCE_STATE_PROJECTOR"),
    ("ClauseIntent", "clause-intent-v1", "clause_intent_ref=exact1 reference_state_ref=exact1 sentence_job_ref=exact1 semantic_clause_kind=exact1 grounded_candidate_ref=0..1 subjective_claim_ref=0..1 admitted_relation_candidate_ref=0..1 admitted_relation_basis_ref=0..1 grounded_predicate_kind=0..1 subjective_predication_kind=0..1 grammatical_role_assignment_rule=exact1 source_binding_coverage_rows=0..N scalar_constraint_rows=1..N subject_binding=0..1 clause_argument_slot_bindings=1..N required_clause_argument_roles_and_cardinalities=1..N relation_operator=exact1 predicate_valency=exact1 polarity_constraint=0..1 modality_constraint=0..1 time_scope_constraint=0..1 syntactic_orientation=exact1 speaker_requirement=exact1 zero_subject_eligibility=exact1", ("SEMANTIC_BRANCH_DISCRIMINATED", "CONSTRUCTION_LOOKUP_INPUT_ONLY"), "CLAUSE_INTENT_PROJECTOR"),
    ("ClauseSourceBindingCoverage", "source-coverage-v1", "qualifier_candidate_ref=exact1 grounded_frame_candidate_ref=exact1 source_argument_role=exact1 source_semantic_ref=exact1 disposition=exact1 clause_argument_role=0..1", ("SURFACE_ARGUMENT_IFF_CLAUSE_ROLE",), "DIRECT_OR_RELATION_BINDING_PROJECTOR"),
    ("ClauseScalarConstraintRow", "scalar-constraint-v1", "clause_scalar_constraint_ref=exact1 owner_kind=exact1 qualifier_candidate_ref=0..1 grounded_frame_candidate_ref=0..1 source_argument_role=0..1 source_semantic_ref=0..1 subjective_basis_binding_ref=0..1 clause_argument_role=0..1 qualifier_refs=0..N polarity=exact1 modality=exact1 time_scope=exact1", ("SOURCE_OR_SUBJECTIVE_OWNER_EXACT1",), "SCALAR_CONSTRAINT_PROJECTOR"),
    ("ScalarSurfaceCoverageKey", "scalar-surface-v1", "clause_plan_ref=exact1 clause_scalar_constraint_ref=exact1 scalar_axis=exact1", ("PLAN_ROW_AXIS_UNIQUE",), "SCALAR_SURFACE_PROJECTOR"),
    ("ScalarSurfaceRealizationRow", "scalar-surface-v1", "coverage_key=exact1 realization_mode=exact1 registered_realization_rule_ref=exact1 target_clause_slot_ref=0..1", ("OVERT_OR_FUSED_IFF_TARGET", "EXACT3_PER_SCALAR_ROW"), "SCALAR_SURFACE_PROJECTOR"),
    ("ClauseSubjectBinding", "subject-binding-v1", "origin_kind=exact1 source_argument_role=0..1 source_semantic_ref=0..1 grounded_actor_value=0..1 grounded_actor_owner_ref=0..1 participant_role_ref=0..1 emlis_owner_ref=0..1 explicit_expression_owner_ref=0..1 realization_mode=exact1", ("ORIGIN_KIND_DISCRIMINATED",), "SUBJECT_BINDING_PROJECTOR"),
    ("ClauseArgumentSlotBinding", "argument-slot-v1", "clause_argument_role=exact1 subject_owner_binding=0..1 semantic_refs=0..N", ("SUBJECT_XOR_SEMANTIC_REFS",), "GRAMMATICAL_ROLE_PROJECTOR"),
    ("ClausePlan", "clause-plan-v1", "clause_plan_ref=exact1 clause_intent_ref=exact1 covered_duty_refs=1..N sentence_job_ref=exact1 construction_id=exact1 syntactic_orientation=exact1 clause_argument_slot_bindings=1..N object_refs=0..N relation_refs=0..1 scalar_constraint_rows=1..N polarity_constraint=0..1 modality_constraint=0..1 time_scope_constraint=0..1 connective_requirement=exact1 terminal_duty_ref=0..1", ("INTENT_FIELDS_EXACT_COPY", "UNIQUE_CONSTRUCTION"), "CLAUSE_PLAN_PROJECTOR"),
    ("ResponseObjectExpression", "response-object-v1", "response_object_expression_ref=exact1 clause_plan_ref=exact1 unit_ref=exact1 basis_semantic_refs=1..N relation_refs=0..1 source_anchor_refs=1..N scalar_constraint_rows=1..N polarity_constraint=0..1 modality_constraint=0..1 time_scope_constraint=0..1 expression_mode=exact1 antecedent_unit_ref=0..1", ("ANAPHORIC_IFF_UNIQUE_PRIOR_CONCRETE",), "RESPONSE_OBJECT_PROJECTOR"),
    ("SurfacePartPlan", "surface-part-v1", "unit_ref=exact1 part_index=exact1 surface_text=1..N clause_plan_ref=exact1 binding_kind=exact1 source_semantic_refs=0..N subjective_claim_refs=0..N emlis_owner_ref=0..1 relation_or_clause_plan_refs=0..N qualifier_refs=0..N scalar_surface_coverage_keys=0..N response_object_expression_ref=0..1 participant_role_ref=0..1 structural_rule_ref=0..1 clause_slot_ref=exact1 surface_derivation=exact1", ("BINDING_KIND_OWNER_UNION_EXACT1", "CONTIGUOUS_PART_INDEX"), "SURFACE_PART_PROJECTOR"),
    ("SurfaceProjectionContext", "surface-context-v1", "unit_plan_row=exact1 ordered_clause_intent_rows=1..N ordered_clause_plan_rows=1..N ordered_response_object_rows=0..N ordered_clause_frame_rows=1..N ordered_surface_part_plan_rows=1..N", ("PRE_SEAL_DERIVED_CLOSURE",), "SURFACE_CONTEXT_PROJECTOR"),
    ("ClauseFrame", "response-v2", "move_ref=exact1 clause_plan_ref=exact1 discourse_relation=exact1 topic_refs=0..N predicate_operator=exact1 object_refs=0..N clause_argument_slot_bindings=1..N scalar_constraint_rows=1..N scalar_surface_realization_rows=3..N qualifier_refs=0..N relation_refs=0..1 polarity_constraint=0..1 modality_constraint=0..1 time_scope_constraint=0..1 subject_binding=0..1 actor_refs=0..N experiencer_refs=0..N addressee_role=exact1 epistemic_marker_refs=0..N speaker_marker=0..1 connective_requirement=exact1 reception_style_policy_ref=exact1 terminal_duty_ref=0..1", ("PLAN_FRAME_ONE_TO_ONE", "SCALAR_ROWS_EXACT3_MULTIPLIER"), "CLAUSE_FRAME_PROJECTOR"),
    ("RealizedSentenceUnit", "response-v2", "unit_id=exact1 projection_ref=exact1 layer=exact1 move_ref=exact1 clause_frames=1..N text=1..N basis_anchor_refs=1..N realized_surface_bindings=1..N discourse_link_to_prior_sentence=0..1 composition_variant_id=exact1", ("BINDINGS_EXACT_COVER_TEXT", "LAYER_TYPED_BASIS"), "REALIZED_UNIT_PROJECTOR"),
    ("LayoutPreferenceSeed", "layout-seed-v1", "opening_duty_ref=exact1 layer1_group_rows=1..N layer2_group_rows=1..N subjective_progression_duty_refs=1..N terminal_duty_ref=exact1", ("EXACT5_NO_HIDDEN_AXIS",), "LAYOUT_SEED_ENUMERATOR"),
    ("DutyGroupRow", "layout-seed-v1", "ordered_duty_refs=1..N", ("NO_DUPLICATE_DUTY",), "LAYOUT_SEED_ENUMERATOR"),
    ("EmlisCompositionLayout", "layout-v1", "discourse_arc_ref=exact1 layout_preference_seed=exact1 visible_duty_refs=1..N ordered_unit_group_rows=2..9", ("VISIBLE_EQUALS_REQUIRED",), "LAYOUT_PROJECTOR"),
    ("CorrectableDefectRow", "normal-form-v1", "defect_kind=exact1 defect_owner_refs=1..N", ("TYPED_OWNER_ONLY",), "NORMAL_FORM_DEFECT_CLASSIFIER"),
    ("DraftArtifact", "draft-v1", "projection_ref=exact1 discourse_arc=exact1 layout_preference_seed=exact1 composition_duty_rows=1..N full_duty_refs=1..N required_duty_refs=1..N suppressed_duty_rows=0..N suppressed_claim_rows=0..N reference_state_rows=1..N clause_intent_rows=1..N clause_plan_rows=1..N unit_plan_rows=2..9 response_object_expression_rows=0..N clause_frame_rows_by_unit=2..9 surface_part_plan_rows_by_unit=2..9 realized_surface_binding_rows_by_unit=2..9 correctable_defect_rows=0..N", ("PRE_NORMAL_FORM_TYPED_PLAN",), "DRAFT_LINEARIZER"),
    ("NormalizedDraftArtifact", "normal-form-v1", "projection_ref=exact1 discourse_arc=exact1 layout_preference_seed=exact1 composition_duty_rows=1..N full_duty_refs=1..N required_duty_refs=1..N suppressed_duty_rows=0..N suppressed_claim_rows=0..N reference_state_rows=1..N clause_intent_rows=1..N clause_plan_rows=1..N unit_plan_rows=2..9 response_object_expression_rows=0..N clause_frame_rows_by_unit=2..9 surface_part_plan_rows_by_unit=2..9 realized_surface_binding_rows_by_unit=2..9 correctable_defect_rows=exact0 normal_form_version=exact1 normal_form_applied=exact_true", ("DRAFT_FIELDS_SAME_ORDER", "EXACT6_IDEMPOTENT"), "WHOLE_ARTIFACT_NORMALIZER"),
    ("SealedCompositionPlan", "sealed-plan-v1", "projection_ref=exact1 composition_layout_id=exact1 discourse_arc=exact1 layout_preference_seed=exact1 composition_duty_rows=1..N full_duty_refs=1..N required_duty_refs=1..N suppressed_duty_rows=0..N suppressed_claim_rows=0..N clause_intent_rows=1..N clause_plan_rows=1..N reference_state_rows=1..N response_object_expression_rows=0..N unit_plan_rows=2..9 surface_part_plan_rows_by_unit=2..9", ("BOTTOM_UP_REPROJECTABLE",), "SEALED_PLAN_PROJECTOR"),
    ("SealedUnitPlanRow", "sealed-unit-v1", "unit_ref=exact1 covered_duty_refs=1..N sentence_job_refs=1..N clause_plan_refs=1..N", ("ORDERED_PLAN_CONCATENATION",), "SEALED_UNIT_PROJECTOR"),
    ("RankableNormalizedMember", "rank-member-v1", "candidate_id=exact1 projection_ref=exact1 composition_signature=exact1 sealed_plan=exact1 clause_frame_rows_by_unit=2..9 realized_surface_binding_rows_by_unit=2..9 normal_form_version=exact1 normal_form_applied=exact_true correctable_defect_rows=exact0 discourse_preference_profile=exact1 canonical_normalized_bytes_sha256=exact1", ("NO_SHARED_VARIANT_OR_REALIZED_UNIT",), "RANKABLE_MEMBER_PROJECTOR"),
    ("ArtifactCompositionCandidate", "candidate-v1", "candidate_id=exact1 projection_ref=exact1 composition_signature=exact1 shared_variant_id=exact1 sealed_plan=exact1 sentence_units=2..9 normal_form_version=exact1 normal_form_applied=exact_true correctable_defect_rows=exact0 discourse_preference_profile=exact1", ("EMITTED_EXACT1_TO_2",), "EMITTED_CANDIDATE_PROJECTOR"),
    ("DiscoursePreferenceProfile", "profile-v1", "information_flow_fit=exact1 concrete_before_abstract_fit=exact1 sentence_load_fit=exact1 topic_transition_fit=exact1 referent_continuity_fit=exact1 relation_realization_fit=exact1 subjective_sequence_fit=exact1 terminal_fit=exact1 profile_evidence_rows=8..N", ("EXACT8_TOTAL_REDUCER",), "PROFILE_PROJECTOR"),
    ("ProfileEvidenceRow", "profile-v1", "profile_evidence_ref=exact1 profile_field=exact1 rule_kind=exact1 evidence_owner_refs=1..N preferred_form_ref=exact1 observed_form_ref=exact1 result=exact1", ("FIELD_RULE_EXACT_PAIR",), "PROFILE_EVIDENCE_PROJECTOR"),
    ("GrammaticalShapeKey", "grammar-v1", "semantic_clause_kind=exact1 sentence_job=exact1 required_argument_roles=1..N grammatical_role_assignment_rule=exact1 predicate_valency=exact1 admitted_relation_operator=exact1 scalar_shape_rows=1..N syntactic_orientation=exact1", ("NO_RAW_TEXT_OR_CASE_ID",), "GRAMMATICAL_SHAPE_PROJECTOR"),
    ("SurfaceDerivation", "response-v2", "derivation_kind=exact1 source_or_claim_refs=0..N emlis_owner_ref=0..1 relation_or_clause_plan_refs=0..N qualifier_refs=0..N response_object_expression_ref=0..1 antecedent_unit_ref=0..1 participant_role_ref=0..1 evidence_refs=0..N rule_ref=exact1 input_scalar_ranges=0..N", ("EXACT8_KIND_OWNER_UNION",), "SURFACE_DERIVATION_PROJECTOR"),
    ("RealizedSurfaceBindingV2", "response-v2", "unit_ref=exact1 clause_plan_ref=exact1 binding_kind=exact1 source_semantic_refs=0..N subjective_claim_refs=0..N emlis_owner_ref=0..1 relation_or_clause_plan_refs=0..N qualifier_refs=0..N scalar_surface_coverage_keys=0..N response_object_expression_ref=0..1 participant_role_ref=0..1 structural_rule_ref=0..1 clause_slot_ref=exact1 surface_scalar_start=exact1 surface_scalar_end=exact1 surface_span_sha256=exact1 surface_derivation=exact1", ("EXACT8_BINDING_OWNER_UNION", "TEXT_SCALAR_EXACT_COVER"), "SURFACE_BINDING_PROJECTOR"),
    ("EmlisStage1PositiveTraceExtensionV2", "trace-v2", "schema_version=exact1 claim_domain=exact1 owner_ref=exact1 contribution_refs=0..N subjective_claim_refs=0..N basis_trace_refs=0..N interpretation_candidate_refs=0..N basis_observation_contribution_refs=0..N covered_duty_refs=1..N sentence_job_refs=1..N source_reception_act_refs=0..N value_principle_refs=0..N speaker_owner=0..1 user_fact_effect=exact0 composition_variant_id=exact1 composition_candidate_ref=exact1 composition_layout_ref=exact1 selected_stage1_artifact_ref=exact1", ("VISIBLE_UNIT_TRACE_EXACT_COPY",), "POSITIVE_TRACE_PROJECTOR"),
)

LANGUAGE_CORE_CONTENT_DERIVATION_ROWS = (
    ("AFFECT", "AFFECTIVE_RESPONSE", "FEEL_TOWARD", "EMLIS_FEELING"),
    ("APPRAISAL", "PERSONAL_APPRAISAL", "APPRAISE_AS_MATERIAL", "EMLIS_APPRAISAL"),
    ("MATERIAL_VALUE", "VALUE_POSITION", "PROTECT_VALUE_BOUNDARY", "EMLIS_VALUE_POSITION"),
    ("RELATIONAL_POSITION:STANCE", "RELATIONAL_STANCE", "TAKE_RELATIONAL_STANCE", "EMLIS_RELATIONAL_INTENTION"),
    ("RELATIONAL_POSITION:BOUNDED_COUNTERPOSITION", "BOUNDED_COUNTERPOSITION", "COUNTER_SPECIFIC_PROMOTION", "EMLIS_BOUNDED_REFUSAL"),
)

LANGUAGE_CORE_CONCRETE_BINDING_DESCRIPTORS = (
    ("ProjectedSubjectiveClaim", ("schema_version", "subjective_claim_id", "parent_duty_ref", "speaker_owner", "claim_domain", "subjective_responsibility_refs", "selected_subjective_opportunity_key", "asserted_subjective_proposition", "basis_observation_contribution_refs", "basis_semantic_refs", "source_reception_act_refs", "value_principle_refs", "user_fact_effect", "forbidden_promotions")),
    ("CandidateFrameRow", ("candidate_ref", "grounded_frame")),
    ("RelationEndpointCandidateRow", ("relation_candidate_ref", "source_argument_role", "source_semantic_ref", "endpoint_grounded_candidate_ref")),
    ("QualifierValueRow", ("candidate_ref", "qualifier_scope", "source_argument_role", "source_semantic_ref", "axis", "value")),
    ("RetainedReceptionActRow", ("act_ref", "reception_act", "basis_contribution_refs")),
    ("ComposedSentenceUnit", ("unit_ref", "layer", "duty_refs", "sentence_job_refs", "basis_anchor_refs", "clause_plan_refs", "text", "surface_text_sha256")),
    ("Stage1CompositionResult", ("language_core_identity", "discourse_arc", "internal_candidate_count", "ranked_candidates", "selected_candidate")),
    ("SourceScalarMorphologyAssetSpec", ("morphology_asset_id", "predicate_kind", "required_attribute_codes", "terminal_rewrites", "preserved_finite_terminals")),
)


def _validate_concrete_binding_descriptors() -> None:
    for type_name, expected_field_names in LANGUAGE_CORE_CONCRETE_BINDING_DESCRIPTORS:
        runtime_type = globals().get(type_name)
        if (
            not isinstance(runtime_type, type)
            or tuple(field.name for field in fields(runtime_type))
            != expected_field_names
        ):
            raise Stage1CompositionError("LANGUAGE_CORE_CONCRETE_DESCRIPTOR_STOP")


def _contract_manifest() -> tuple[Any, ...]:
    _validate_concrete_binding_descriptors()
    descriptors = tuple(
        _logical_contract_descriptor(*row)
        for row in _LOGICAL_CONTRACT_FIELD_SPECS
    )
    if len(descriptors) != 59 or len({row[0][1] for row in descriptors}) != 59:
        raise Stage1CompositionError("LANGUAGE_CORE_CONTRACT_DESCRIPTOR_STOP")
    return (
        ("schema_version", _CONTRACT_MANIFEST_SCHEMA_VERSION),
        ("logical_contract_count", 59),
        ("logical_contract_descriptors", descriptors),
        ("content_kind_derivation_rows", LANGUAGE_CORE_CONTENT_DERIVATION_ROWS),
        ("concrete_runtime_binding_descriptors", LANGUAGE_CORE_CONCRETE_BINDING_DESCRIPTORS),
        (
            "default_policy",
            (
                ("implicit_default", _NO_IMPLICIT_DEFAULT),
                ("optional_cardinality", "EXPLICIT_NONE_NOT_IMPLICIT_DEFAULT"),
                ("unknown_field", "REJECT"),
            ),
        ),
    )


LANGUAGE_CORE_CLOSED_ENUM_MANIFEST = (
    ("SubjectiveResponsibilityKind", ("AFFECTIVE_RESPONSE", "MATERIAL_APPRAISAL", "POLICY_VISIBLE_VALUE", "RELATIONAL_POSITION")),
    ("SubjectiveSpecificity", ("RELATION_BOUND_MULTI_ROLE", "MULTI_ROLE", "SINGLE_ROLE")),
    ("SubjectiveFacetSuppressionReason", ("NONMATERIAL", "DUPLICATE", "ABSORBED_ATTENTION")),
    ("ArcDependencyKind", ("ADMITTED_RELATION_DIRECTION", "SOURCE_DEPENDENCY_ORDER", "GROUNDED_BEFORE_SUBJECTIVE", "SUBJECTIVE_CONTENT_DEPENDENCY", "UNFINISHED_TERMINAL")),
    ("SentenceJob", ("OBSERVE_CENTER", "RELATE_COEXISTING_OR_TENSION", "TRACE_CHANGE_OR_SEQUENCE", "PRESERVE_RESIDUE_OR_UNFINISHED", "FEEL_TOWARD_OBJECT", "CONSIDER_MATERIAL_MEANING", "TAKE_MATERIAL_POSITION", "STAY_WITH_UNFINISHED")),
    ("DutySuppressionReason", ("NONMATERIAL_OPTIONAL", "DUPLICATE_SEMANTIC_COVERAGE", "ABSORBED_INTO_VISIBLE_OWNER")),
    ("ResponseObjectExpressionMode", ("EXPLICIT", "COMPOSITE", "ANAPHORIC")),
    ("GroundedPredicateKind", ("event", "state", "reaction", "wish", "constraint", "action", "change", "self_evaluation", "value", "uncertainty", "conclusion", "other_explicit", "refusal", "feeling")),
    ("RelationOperator", ("NO_RELATION_CLAIM", "COEXISTS_WITH", "TENSION_WITH", "TEMPORALLY_PRECEDES", "ACTION_PRECEDES_CHANGE", "SOURCE_EXPLICIT_CAUSE")),
    ("ArgumentRole", ("PRIMARY", "EXPERIENCER", "LEFT", "RIGHT", "BEFORE", "AFTER", "ACTION", "CHANGE", "CAUSE", "EFFECT")),
    ("ClauseArgumentRole", ("SUBJECT", "PRIMARY_OBJECT", "SECONDARY_OBJECT", "LEFT_ENDPOINT", "RIGHT_ENDPOINT", "BEFORE_EVENT", "AFTER_EVENT", "ACTION_EVENT", "CHANGE_EVENT", "CAUSE_EVENT", "EFFECT_EVENT")),
    ("QualifierLookupScope", ("DIRECT_UNQUALIFIED", "RELATION_SOURCE_BINDING")),
    ("SemanticClauseKind", ("GROUNDED_PREDICATE", "SUBJECTIVE_PREDICATE", "ADMITTED_RELATION")),
    ("SubjectivePredicationKind", ("AFFECT", "APPRAISAL", "MATERIAL_VALUE", "RELATIONAL_STANCE", "BOUNDED_COUNTERPOSITION")),
    ("PredicateValency", ("MONADIC_ARGUMENT", "DYADIC_ACTOR_TARGET", "TRIADIC_ACTOR_TARGET_BOUNDARY", "DYADIC_RELATION_ENDPOINTS")),
    ("ClauseScalarConstraintOwnerKind", ("SOURCE_BINDING", "SUBJECTIVE_BASIS")),
    ("ClauseScalarAxis", ("POLARITY", "MODALITY", "TIME_SCOPE")),
    ("ScalarSurfaceRealizationMode", ("OVERT_FUNCTIONAL_PART", "FUSED_IN_REGISTERED_PART", "UNMARKED_DEFAULT", "SEMANTIC_PROVENANCE_ONLY")),
    ("GrammaticalRoleAssignmentRule", ("DIRECT_REFERENT_SUBJECT", "GROUNDED_ACTOR_TARGET", "EMLIS_TARGET_OR_BOUNDARY", "ADMITTED_RELATION_ENDPOINT_PAIR")),
    ("SyntacticOrientation", ("REFERENT_FIRST", "GROUNDED_ACTOR_SUBJECT", "EMLIS_SUBJECT", "EVENT_FIRST", "RELATION_FIRST")),
    ("SpeakerRequirement", ("GROUNDED_NARRATION", "EMLIS_EXPLICIT_REQUIRED", "EMLIS_ZERO_ALLOWED")),
    ("SubjectOriginKind", ("SOURCE_ARGUMENT", "GROUNDED_ACTOR", "EMLIS_OWNER")),
    ("SubjectRealizationMode", ("EXPLICIT", "ZERO")),
    ("ActiveReferentEstablishmentKind", ("NONE", "ADMITTED_SOURCE", "IMMEDIATELY_PRIOR_VISIBLE_CLAUSE", "CARRIED_FORWARD")),
    ("SpeakerResolutionStatus", ("UNIQUE", "NONUNIQUE")),
    ("SurfaceDerivationKind", ("LITERAL_SUBSPAN", "NORMALIZED_INFLECTION", "COMPOSITIONAL_JOIN", "REGISTERED_EMLIS_LEXEME", "REGISTERED_PARTICIPANT_LEXEME", "REGISTERED_STRUCTURAL_ASSET", "PROJECTED_RESPONSE_OBJECT", "PROJECTED_FUNCTIONAL_ASSET")),
    ("SurfaceBindingKind", ("SOURCE_SEMANTIC", "SUBJECTIVE_CLAIM", "EMLIS_OWNER", "RELATION_FUNCTIONAL", "QUALIFIER_FUNCTIONAL", "RESPONSE_OBJECT_REFERENCE", "PARTICIPANT_ROLE", "PURE_STRUCTURAL")),
    ("CorrectableDefectKind", ("NONMATERIAL_OR_DUPLICATE_DUTY", "INCOMPATIBLE_SENTENCE_LOAD", "DEPENDENCY_OR_INFORMATION_ORDER", "UNRESOLVED_OR_DISTANT_REFERENT", "TOPIC_OR_SPEAKER_PLACEMENT", "RELATION_OR_CONNECTIVE_FIT", "SUBJECTIVE_SEQUENCE_FIT", "TERMINAL_FIT")),
    ("NormalFormPhase", ("SUPPRESSION", "SEED_CONSTRAINED_MERGE_SPLIT", "DEPENDENCY_INFORMATION_ORDER", "REFERENCE_ANTECEDENT_RECALCULATION", "TOPIC_SPEAKER_CONNECTIVE_TERMINAL", "EXPRESSION_SELECTION_FINAL_LINEARIZATION")),
    ("ProfileFit", ("ARC_ALIGNED", "PERMITTED", "NOT_APPLICABLE")),
    ("ProfileEvidenceField", ("INFORMATION_FLOW", "CONCRETE_BEFORE_ABSTRACT", "SENTENCE_LOAD", "TOPIC_TRANSITION", "REFERENT_CONTINUITY", "RELATION_REALIZATION", "SUBJECTIVE_SEQUENCE", "TERMINAL")),
    ("ProfileEvidenceRuleKind", ("ARC_DEPENDENCY", "CONCRETE_INTRODUCTION", "PREDICATION_LOAD", "TOPIC_STATE", "REFERENT_STATE", "RELATION_REALIZATION", "SUBJECTIVE_DEPENDENCY", "TERMINAL_DUTY")),
    ("RegisteredFunctionalSlotRef", ("functional-slot:predicate-head.v1", "functional-slot:qualifier.v1")),
    ("SubjectiveContentKind", ("AFFECT", "APPRAISAL", "MATERIAL_VALUE", "RELATIONAL_POSITION")),
    ("SubjectiveMode", ("ATTENTION", "AFFECTIVE_RESPONSE", "PERSONAL_APPRAISAL", "VALUE_POSITION", "RELATIONAL_STANCE", "BOUNDED_COUNTERPOSITION")),
    ("SubjectiveOperator", ("ATTEND_TO", "FEEL_TOWARD", "APPRAISE_AS_MATERIAL", "PROTECT_VALUE_BOUNDARY", "TAKE_RELATIONAL_STANCE", "COUNTER_SPECIFIC_PROMOTION")),
    ("SubjectiveAssertionModality", ("EMLIS_FEELING", "EMLIS_APPRAISAL", "EMLIS_VALUE_POSITION", "EMLIS_RELATIONAL_INTENTION", "EMLIS_BOUNDED_REFUSAL")),
    ("SubjectiveBasisRole", ("ELICITOR", "APPRAISED_OBJECT", "RELATION_LEFT", "RELATION_RIGHT", "ACTION", "CHANGE", "BEFORE", "AFTER", "RESIDUE", "UNFINISHED", "CHOICE_TARGET")),
    ("PolicyBasisOwnerKind", ("CONTRIBUTION", "MATERIAL_UNKNOWN")),
    ("PolicyBasisRole", ("BURDEN_OR_RESIDUE", "DIRECTION", "CHANGE_OR_ACTUAL_OUTPUT", "COEXISTENCE_OR_TENSION", "UNFINISHED", "VISIBILITY_ACT_BASIS", "MATERIAL_UNKNOWN")),
    ("MaterialRisk", ("MINIMIZATION", "WISH_TO_OBLIGATION", "NO_RESULT_TO_NO_VALUE", "SINGLE_EVENT_TO_IDENTITY", "BOUNDED_CHANGE_TO_UNIVERSAL_SOLUTION", "ONE_SIDE_TO_TRUE_SELF", "POSSIBILITY_TO_FACT", "REMOVE_USER_AGENCY", "UNKNOWN_TO_FALSE_UNDERSTANDING")),
    ("RelationalPositionKind", ("STANCE", "BOUNDED_COUNTERPOSITION")),
    ("RelationalCommitment", ("AFFIRM_SOURCE_BOUND_DIRECTION", "STAY_WITH", "HOLD_OPEN", "WELCOME_BOUNDED_CHANGE", "PROTECT_AGENCY", "DECLINE_PROMOTION")),
    ("RelationalClosure", ("NONE", "BOUNDED", "OPEN")),
)


def _validate_closed_enum_manifest() -> None:
    for enum_name, expected_values in LANGUAGE_CORE_CLOSED_ENUM_MANIFEST:
        enum_type = globals().get(enum_name)
        if isinstance(enum_type, type) and issubclass(enum_type, Enum):
            if tuple(row.value for row in enum_type) != expected_values:
                raise Stage1CompositionError("LANGUAGE_CORE_ENUM_MANIFEST_STOP")


LANGUAGE_CORE_POLICY_SUPPRESSION_FEATURE_FIELDS = (
    "PRESENT_BURDEN",
    "PRESENT_RESIDUE",
    "OBSERVE_BURDEN",
    "PRESERVE_RESIDUE",
    "PRESENT_DIRECTION",
    "PRESENT_CHANGE",
    "PRESENT_ACTUAL_OUTPUT",
    "COEXISTS_WITH",
    "TENSION_WITH",
    "PRESENT_UNFINISHED",
    "PRESERVE_UNFINISHED",
    "material_unknown",
    "actual_output_retention_required",
)
LANGUAGE_CORE_POLICY_VISIBILITY_FEATURE_FIELDS = (
    *LANGUAGE_CORE_POLICY_SUPPRESSION_FEATURE_FIELDS[:11],
    "actual_output_retention_required",
)
LANGUAGE_CORE_POLICY_RECEPTION_ACT_ORDER = tuple(
    row.reception_act for row in CMEE_STAGE1_RECEPTION_ACT_MAPPING_EXACT7
)

LANGUAGE_CORE_V1_TO_V9_POLICY_TABLE = (
    ("V1", ("PRESENT_BURDEN", "PRESENT_RESIDUE", "OBSERVE_BURDEN", "PRESERVE_RESIDUE"), "MINIMIZATION", ("bounded_counter_self_denial",)),
    ("V2", ("PRESENT_DIRECTION",), "WISH_TO_OBLIGATION", ("protect_retained_intention:DIRECTION_AND_BURDEN_OR_TENSION",)),
    ("V3", ("PRESENT_UNFINISHED", "PRESERVE_UNFINISHED"), "NO_RESULT_TO_NO_VALUE", ()),
    ("V4", ("PRESENT_CHANGE", "PRESENT_ACTUAL_OUTPUT"), "SINGLE_EVENT_TO_IDENTITY", ()),
    ("V5", ("PRESENT_CHANGE", "PRESENT_ACTUAL_OUTPUT"), "BOUNDED_CHANGE_TO_UNIVERSAL_SOLUTION", ()),
    ("V6", ("COEXISTS_WITH", "TENSION_WITH"), "ONE_SIDE_TO_TRUE_SELF", ()),
    ("V7", ("PRESENT_UNFINISHED", "PRESERVE_UNFINISHED"), "POSSIBILITY_TO_FACT", ()),
    ("V8", ("PRESENT_DIRECTION",), "REMOVE_USER_AGENCY", ("bounded_counter_self_denial", "protect_retained_intention:DIRECTION_AND_BURDEN_OR_TENSION", "hold_help_seeking:REQUIRED_PRESENT_ACTUAL_OUTPUT")),
    ("V9", ("PRESENT_UNFINISHED", "PRESERVE_UNFINISHED", "material_unknown"), "UNKNOWN_TO_FALSE_UNDERSTANDING", ()),
)

_POLICY_BEHAVIOR_MATRIX_SCHEMA = (
    ("schema_version", "cocolon.cmee.v1a.stage1_policy_behavior_matrix.v1"),
    ("suppression_feature_fields", LANGUAGE_CORE_POLICY_SUPPRESSION_FEATURE_FIELDS),
    ("visibility_feature_fields", LANGUAGE_CORE_POLICY_VISIBILITY_FEATURE_FIELDS),
    ("boolean_iteration_order", ("FALSE", "TRUE")),
    ("reception_act_order", LANGUAGE_CORE_POLICY_RECEPTION_ACT_ORDER),
)
POLICY_BEHAVIOR_DIGEST = "3cd429305e05f41e13fed60c14f24e7060c25c011da20dbf9ef159c05c751327"


def _boolean_vectors(width: int) -> Iterable[tuple[bool, ...]]:
    for integer in range(1 << width):
        yield tuple(
            bool((integer >> (width - position - 1)) & 1)
            for position in range(width)
        )


def _policy_suppression_codes_from_bits(bits: tuple[bool, ...]) -> tuple[str, ...]:
    selected = set()
    if any(bits[index] for index in (0, 1, 2, 3)):
        selected.add("V1")
    if bits[4]:
        selected.update(("V2", "V8"))
    if bits[5] or bits[6]:
        selected.update(("V4", "V5"))
    if bits[7] or bits[8]:
        selected.add("V6")
    if bits[9] or bits[10]:
        selected.update(("V3", "V7", "V9"))
    if bits[11]:
        selected.add("V9")
    return tuple(code for code, _ref in CMEE_STAGE1_VALUE_PRINCIPLE_REFS if code in selected)


def _policy_visible_refs_from_bits(
    bits: tuple[bool, ...], reception_act: str
) -> tuple[str, ...]:
    codes: tuple[str, ...]
    if reception_act == "bounded_counter_self_denial":
        codes = ("V1", "V8")
    elif reception_act == "protect_retained_intention" and bits[4] and (
        bits[0] or bits[7] or bits[8]
    ):
        codes = ("V2", "V8")
    elif reception_act == "hold_help_seeking" and bits[6] and bits[11]:
        codes = ("V8",)
    else:
        codes = ()
    selected = set(codes)
    return tuple(ref for code, ref in CMEE_STAGE1_VALUE_PRINCIPLE_REFS if code in selected)


def _policy_behavior_matrix_payload() -> tuple[Any, ...]:
    suppression_rows = tuple(
        (bits, _policy_suppression_codes_from_bits(bits))
        for bits in _boolean_vectors(13)
    )
    visibility_rows = tuple(
        (bits, reception_act, _policy_visible_refs_from_bits(bits, reception_act))
        for bits in _boolean_vectors(12)
        for reception_act in LANGUAGE_CORE_POLICY_RECEPTION_ACT_ORDER
    )
    if len(suppression_rows) != 8192 or len(visibility_rows) != 28672:
        raise Stage1CompositionError("LANGUAGE_CORE_POLICY_MATRIX_CARDINALITY_STOP")
    return (
        _POLICY_BEHAVIOR_MATRIX_SCHEMA,
        ("suppression_rows", suppression_rows),
        ("visibility_rows", visibility_rows),
    )


def recompute_policy_behavior_digest() -> str:
    return hashlib.sha256(
        stage1_canonical_json_bytes(_policy_behavior_matrix_payload())
    ).hexdigest()


LANGUAGE_CORE_REF_PREIMAGE_MANIFEST = (
    ("projection_preimage_ref", ("CMEE_STAGE1_PROJECTION_PREIMAGE_REF_VERSION", "grounded_graph_ref", "parent_observation_duty_ref", "parent_reception_duty_ref", "ordered_interpretation_candidate_ids", "meaning_field_id", "ordered_observation_contribution_ids", "ordered_retained_reception_act_ids", "observation_depth_class", "temperature_class", "reception_style_policy_ref", "emlis_value_policy_ref", "CMEE_STAGE1_RESPONSE_SCHEMA_VERSION", "CMEE_STAGE1_COMPOSITION_POLICY_VERSION")),
    ("subjective_basis_binding_ref", ("CMEE_STAGE1_SUBJECTIVE_BASIS_BINDING_REF_VERSION", "projection_preimage_ref", "contribution_ref", "semantic_ref", "role")),
    ("source_qualifier_binding_ref", ("CMEE_STAGE1_SOURCE_QUALIFIER_BINDING_REF_VERSION", "projection_preimage_ref", "basis_binding_ref", "source_candidate_ref", "source_argument_role", "canonical_qualifier_codes", "polarity", "modality", "time_scope")),
    ("policy_basis_binding_ref", ("CMEE_STAGE1_POLICY_BASIS_BINDING_REF_VERSION", "projection_preimage_ref", "owner_kind", "owner_ref", "role")),
    ("subjective_responsibility_ref", ("CMEE_STAGE1_SUBJECTIVE_RESPONSIBILITY_REF_VERSION", "projection_preimage_ref", "responsibility_kind", "canonical_owner_component_refs", "canonical_retained_reception_act_refs")),
    ("subjective_opportunity_key", ("CMEE_STAGE1_SUBJECTIVE_OPPORTUNITY_KEY_VERSION", "projection_preimage_ref", "canonical_responsibility_refs", "content_kind", "canonical_row_ref_free_discriminated_content", "typed_specificity_key")),
    ("arc_dependency_ref", ("CMEE_STAGE1_ARC_DEPENDENCY_REF_VERSION", "projection_ref", "predecessor_owner_ref", "successor_owner_ref", "dependency_kind", "source_relation_ref")),
    ("stage1_discourse_arc_ref", ("CMEE_STAGE1_DISCOURSE_ARC_REF_VERSION", "projection_ref", "canonical_nucleus_owner_refs", "canonical_supporting_owner_refs", "canonical_admitted_relation_refs", "canonical_full_arc_dependency_rows", "canonical_root_owner_refs", "canonical_unresolved_or_residue_refs", "canonical_terminal_owner_refs", "canonical_layer2_response_target_refs")),
    ("composition_duty_ref", ("CMEE_STAGE1_COMPOSITION_DUTY_REF_VERSION", "projection_ref", "layer", "sentence_job", "canonical_basis_projection_refs", "canonical_relation_refs", "canonical_response_object_refs", "retention")),
    ("reference_state_ref", ("CMEE_STAGE1_REFERENCE_STATE_REF_VERSION", "projection_ref", "prior_clause_plan_ref", "canonical_active_referent_refs", "active_referent_establishment_kind", "immediately_prior_subject_owner_ref", "canonical_competing_subject_owner_refs", "addressee_deictic_context", "active_speaker_kind", "active_speaker_owner_ref", "section_speaker_owner_ref", "canonical_competing_speaker_owner_refs", "speaker_resolution_status", "canonical_established_by_refs")),
    ("affected_claim_policy_target_key", ("CMEE_STAGE1_POLICY_TARGET_KEY_VERSION", "SubjectiveClaimDraft_declared_fields_except_draft_handle_and_row_ref_free_proposition", "canonical_RowRefFreeSubjectivePropositionV2_all_fields")),
    ("policy_application_row_ref", ("CMEE_STAGE1_POLICY_APPLICATION_ROW_ID_VERSION", "affected_claim_policy_target_key", "application_kind", "principle_ref", "material_risk", "canonical_policy_basis_binding_refs", "canonical_material_risk_evidence_refs", "canonical_protected_subjective_binding_refs", "source_reception_act_ref", "canonical_act_basis_contribution_refs", "disposition")),
    ("clause_scalar_constraint_ref", ("CMEE_STAGE1_CLAUSE_SCALAR_CONSTRAINT_REF_VERSION", "projection_ref", "owner_kind", "qualifier_candidate_ref", "grounded_frame_candidate_ref", "source_argument_role", "source_semantic_ref", "subjective_basis_binding_ref", "clause_argument_role", "canonical_qualifier_refs", "polarity", "modality", "time_scope")),
    ("clause_intent_ref", ("CMEE_STAGE1_CLAUSE_INTENT_ID_VERSION", "reference_state_ref", "sentence_job_ref", "semantic_clause_kind", "grounded_candidate_ref", "subjective_claim_ref", "admitted_relation_candidate_ref", "admitted_relation_basis_ref", "grounded_predicate_kind", "subjective_predication_kind", "grammatical_role_assignment_rule", "canonical_source_binding_coverage_rows", "canonical_scalar_constraint_rows", "canonical_subject_binding", "canonical_clause_argument_slot_bindings", "canonical_required_clause_argument_roles_and_cardinalities", "relation_operator", "predicate_valency", "polarity_constraint", "modality_constraint", "time_scope_constraint", "syntactic_orientation", "speaker_requirement", "zero_subject_eligibility")),
    ("clause_plan_ref", ("CMEE_STAGE1_CLAUSE_PLAN_ID_VERSION", "clause_intent_ref", "canonical_covered_duty_refs", "sentence_job_ref", "construction_id", "syntactic_orientation", "canonical_clause_argument_slot_bindings", "canonical_object_refs", "canonical_relation_refs", "canonical_scalar_constraint_rows", "polarity_constraint", "modality_constraint", "time_scope_constraint", "connective_requirement", "terminal_duty_ref")),
    ("response_object_expression_ref", ("CMEE_STAGE1_RESPONSE_OBJECT_EXPRESSION_ID_VERSION", "clause_plan_ref", "unit_ref", "canonical_basis_semantic_refs", "canonical_relation_refs", "canonical_source_anchor_refs", "canonical_scalar_constraint_rows", "polarity_constraint", "modality_constraint", "time_scope_constraint", "expression_mode", "antecedent_unit_ref")),
    ("profile_evidence_ref", ("CMEE_STAGE1_PROFILE_EVIDENCE_REF_VERSION", "profile_field", "rule_kind", "canonical_evidence_owner_refs", "preferred_form_ref", "observed_form_ref", "result")),
    ("unit_ref", ("CMEE_STAGE1_SEALED_UNIT_PLAN_ROW_ID_VERSION", "canonical_covered_duty_refs", "ordered_unique_sentence_job_refs", "ordered_clause_plan_refs")),
    ("composition_layout_id", ("CMEE_STAGE1_COMPOSITION_LAYOUT_ID_VERSION", "projection_ref", "ordered_subjective_claim_ids", "canonical_full_stage1_discourse_arc", "canonical_layout_preference_seed", "canonical_full_duty_refs", "canonical_required_duty_refs", "canonical_suppressed_duty_rows", "canonical_suppressed_claim_rows", "ordered_full_reference_state_rows", "ordered_sealed_unit_plan_rows", "ordered_full_response_object_expression_rows")),
    ("candidate_id", ("CMEE_STAGE1_ARTIFACT_COMPOSITION_CANDIDATE_ID_VERSION", "projection_ref", "composition_layout_id", "canonical_composition_signature", "CMEE_STAGE1_NORMAL_FORM_VERSION", "sha256_canonical_normalized_bytes", "canonical_discourse_preference_profile")),
    ("selected_stage1_artifact_ref", ("CMEE_STAGE1_SELECTED_ARTIFACT_ID_VERSION", "stage1_projection_artifact_ref", "candidate_id", "shared_variant_id", "ordered_realized_sentence_unit_ids", "CMEE_STAGE1_TRACE_EXTENSION_SCHEMA_VERSION")),
)

LANGUAGE_CORE_GENERATION_ORDER_RULES = (
    "PHASE_A_UPSTREAM_FREEZE",
    "CANDIDATE_FRAME_RELATION_ENDPOINT_AND_QUALIFIER_FREEZE",
    "PER_ACT_VISIBILITY",
    "RESPONSIBILITY_AND_ROW_REF_FREE_OPPORTUNITY",
    "UNIQUE_SUBSET_AND_FACET_SUPPRESSION",
    "SELECTED_BASIS_QUALIFIER_POLICY_ROWS_AND_CLAIM_SLOTS",
    "PER_SLOT_FORBIDDEN_OUTPUT_AND_IMMUTABLE_DRAFT",
    "POLICY_SEED_TARGET_KEY_ROW_FINAL_PROPOSITION_AND_CLAIM",
    "FINAL_PROJECTION",
    "ARC_DUTY_AND_LAYOUT_SEED",
    "REFERENCE_STATE_INTENT_PLAN_UNIT_RESPONSE_FRAME_PART_BINDING",
    "DRAFT_AND_EXACT6_NORMAL_FORM",
    "STAGE_A_EXACT_MEMBER_REDUCER",
    "PROFILE_AND_CANDIDATE_ID",
    "STAGE_B_VISIBLE_EQUIVALENCE_REDUCER",
    "GLOBAL_RANK_SHARED_VARIANT_REALIZED_UNIT_SELECTION",
)

LANGUAGE_CORE_LAYOUT_SEED_EXACT5_RULES = (
    ("opening_duty_ref", "exact1", "project_opening_duty_from_arc_roots"),
    ("layer1_group_rows", "1..N", "complete_layer1_partition_enumeration"),
    ("layer2_group_rows", "1..N", "complete_layer2_partition_enumeration"),
    ("subjective_progression_duty_refs", "1..N", "layer2_topological_order"),
    ("terminal_duty_ref", "exact1", "project_terminal_duty_from_arc_terminals"),
)
LANGUAGE_CORE_NORMAL_FORM_EXACT6_RULES = (
    ("SUPPRESSION", "_normal_form_phase_suppression", "NONMATERIAL_OR_DUPLICATE_DUTY"),
    ("SEED_CONSTRAINED_MERGE_SPLIT", "_normal_form_phase_seed_constrained_merge_split", "INCOMPATIBLE_SENTENCE_LOAD"),
    ("DEPENDENCY_INFORMATION_ORDER", "_normal_form_phase_dependency_information_order", "DEPENDENCY_OR_INFORMATION_ORDER"),
    ("REFERENCE_ANTECEDENT_RECALCULATION", "_normal_form_phase_reference_antecedent_recalculation", "UNRESOLVED_OR_DISTANT_REFERENT"),
    ("TOPIC_SPEAKER_CONNECTIVE_TERMINAL", "_normal_form_phase_topic_speaker_connective_terminal", "TOPIC_OR_SPEAKER_PLACEMENT|RELATION_OR_CONNECTIVE_FIT|SUBJECTIVE_SEQUENCE_FIT|TERMINAL_FIT"),
    ("EXPRESSION_SELECTION_FINAL_LINEARIZATION", "_normal_form_phase_expression_selection_final_linearization", "FINAL_DEFECT_RECOMPUTE_EXACT0"),
)
LANGUAGE_CORE_PROFILE_EXACT8_RULES = (
    ("INFORMATION_FLOW", "ARC_DEPENDENCY", "information_flow_fit", "REQUIRED_APPLICABLE", "ALL_ALIGNED_ELSE_ANY_PERMITTED"),
    ("CONCRETE_BEFORE_ABSTRACT", "CONCRETE_INTRODUCTION", "concrete_before_abstract_fit", "POOL_GLOBAL_OPTIONAL", "ALL_ALIGNED_ELSE_ANY_PERMITTED_ELSE_ALL_NOT_APPLICABLE"),
    ("SENTENCE_LOAD", "PREDICATION_LOAD", "sentence_load_fit", "REQUIRED_APPLICABLE", "ALL_ALIGNED_ELSE_ANY_PERMITTED"),
    ("TOPIC_TRANSITION", "TOPIC_STATE", "topic_transition_fit", "REQUIRED_APPLICABLE", "ALL_ALIGNED_ELSE_ANY_PERMITTED"),
    ("REFERENT_CONTINUITY", "REFERENT_STATE", "referent_continuity_fit", "REQUIRED_APPLICABLE", "ALL_ALIGNED_ELSE_ANY_PERMITTED"),
    ("RELATION_REALIZATION", "RELATION_REALIZATION", "relation_realization_fit", "REQUIRED_APPLICABLE", "ALL_ALIGNED_ELSE_ANY_PERMITTED"),
    ("SUBJECTIVE_SEQUENCE", "SUBJECTIVE_DEPENDENCY", "subjective_sequence_fit", "REQUIRED_APPLICABLE", "ALL_ALIGNED_ELSE_ANY_PERMITTED"),
    ("TERMINAL", "TERMINAL_DUTY", "terminal_fit", "REQUIRED_APPLICABLE", "ALL_ALIGNED_ELSE_ANY_PERMITTED"),
)
LANGUAGE_CORE_STAGE_A_B_RULES = (
    ("STAGE_A", "FULL_EXACT_MEMBER_CANONICAL_BYTES", "SHA256_BUCKET_WITH_FULL_BYTE_COLLISION_STOP", "PROFILE_AND_CANDIDATE_ID_EXCLUDED"),
    ("STAGE_B", "PROJECTION_AND_ORDERED_VISIBLE_LAYER_TEXT_DUTY_JOB_BASIS_KEY", "PROFILE_EXACT8_THEN_COMPOSITION_SIGNATURE", "WHOLE_OBJECT_REPRESENTATIVE_NO_FIELD_MERGE"),
    ("RESOURCE_ENVELOPE", "EXACT5_DIMENSIONS_EACH_1_TO_2", "INTERNAL_1_TO_32", "EMITTED_1_TO_2_MATERIAL_ALTERNATE_ONLY"),
)

LANGUAGE_CORE_PRODUCT_CAUSAL_OWNER_MANIFEST = (
    (_COMPOSITION_PATH, ("project_subjective_meaning_plan", "project_stage1_discourse_arc", "compose_stage1_from_projection", "normalize_to_normal_form", "derive_discourse_preference_profile", "_derive_discourse_preference_profile_with_frozen_applicability")),
    (LANGUAGE_CORE_EXTERNAL_PATHS[0], ("stage1_canonical_json_bytes", "stage1_subjective_forbidden_promotions", "_stage1_material_visible_value_refs", "project_stage1_projection_preimage_ref", "project_stage1_subjective_basis_binding_ref", "project_stage1_source_qualifier_binding_ref", "project_stage1_policy_basis_binding_ref", "validate_stage1_projection", "validate_stage1_sentence_unit")),
    (LANGUAGE_CORE_EXTERNAL_PATHS[1], ("project_direct_argument_bindings", "_candidate_from_direct", "_candidate_for_contribution", "resolve_candidate_for_contribution", "_qualifier_value", "resolve_qualifier_value", "build_subjective_planning_inputs", "seal_stage1_projection", "build_surface_composition_inputs")),
    (LANGUAGE_CORE_EXTERNAL_PATHS[2], ("_ordered", "_planned_visible_source_ids", "_build_graph", "_build_experience_plan")),
    (LANGUAGE_CORE_EXTERNAL_PATHS[3], ("build_grounded_observation_plan", "build_final_stage1_grounded_observation_plan", "validate_grounded_observation_plan")),
    (LANGUAGE_CORE_EXTERNAL_PATHS[4], ("generate_core_text",)),
    (LANGUAGE_CORE_EXTERNAL_PATHS[5], ("build_emlis_observation_core_payload", "evaluate_emlis_observation_candidate")),
)


def _validate_product_causal_owner_manifest(
    file_payloads: tuple[tuple[str, bytes], ...]
) -> None:
    expected_paths = (_COMPOSITION_PATH, *LANGUAGE_CORE_EXTERNAL_PATHS)
    if tuple(path for path, _names in LANGUAGE_CORE_PRODUCT_CAUSAL_OWNER_MANIFEST) != expected_paths:
        raise Stage1CompositionError("LANGUAGE_CORE_DEPENDENCY_SCOPE_STOP")
    payload_by_path = dict(file_payloads)
    if tuple(payload_by_path) != expected_paths:
        raise Stage1CompositionError("LANGUAGE_CORE_DEPENDENCY_SCOPE_STOP")
    for path, callable_names in LANGUAGE_CORE_PRODUCT_CAUSAL_OWNER_MANIFEST:
        if not callable_names or len(callable_names) != len(set(callable_names)):
            raise Stage1CompositionError("LANGUAGE_CORE_DEPENDENCY_SCOPE_STOP")
        payload = payload_by_path[path]
        for callable_name in callable_names:
            marker = f"def {callable_name}(".encode("utf-8")
            if payload.count(marker) != 1:
                raise Stage1CompositionError("LANGUAGE_CORE_DEPENDENCY_SCOPE_STOP")


def language_core_identity_payloads(repository_root: Optional[Path] = None) -> Tuple[Tuple[str, bytes], ...]:
    """Return the ordered exact-16 whole-file/manifest identity payloads."""

    root = repository_root or Path(__file__).resolve().parents[4]
    file_paths = (_COMPOSITION_PATH, *LANGUAGE_CORE_EXTERNAL_PATHS)
    file_payloads: list[tuple[str, bytes]] = []
    for relative in file_paths:
        path = root / relative
        if not path.is_file():
            raise Stage1CompositionError("LANGUAGE_CORE_DEPENDENCY_SCOPE_STOP")
        file_payloads.append((relative, path.read_bytes()))
    frozen_file_payloads = tuple(file_payloads)
    _validate_product_causal_owner_manifest(frozen_file_payloads)
    _validate_closed_enum_manifest()
    fresh_policy_digest = recompute_policy_behavior_digest()
    if fresh_policy_digest != POLICY_BEHAVIOR_DIGEST:
        raise Stage1CompositionError("LANGUAGE_CORE_POLICY_BEHAVIOR_DIGEST_STOP")
    policy_and_enum_manifest = (
        ("schema_version", "cocolon.cmee.v1a.stage1_policy_and_enum_manifest.v1"),
        ("final_logical_id_registry", CMEE_STAGE1_FINAL_LOGICAL_ID_REGISTRY),
        ("v1_to_v9_policy_table", LANGUAGE_CORE_V1_TO_V9_POLICY_TABLE),
        (
            "policy_behavior",
            (
                ("suppression_feature_fields", LANGUAGE_CORE_POLICY_SUPPRESSION_FEATURE_FIELDS),
                ("suppression_row_count", 8192),
                ("visibility_feature_fields", LANGUAGE_CORE_POLICY_VISIBILITY_FEATURE_FIELDS),
                ("visibility_reception_act_order", LANGUAGE_CORE_POLICY_RECEPTION_ACT_ORDER),
                ("visibility_row_count", 28672),
                ("boolean_iteration_order", ("FALSE", "TRUE")),
                ("expected_digest", POLICY_BEHAVIOR_DIGEST),
                ("fresh_recomputed_digest", fresh_policy_digest),
                ("extractor_rule", "VALIDATED_CONTRIBUTION_OPERATOR_KIND_RELATION_RETENTION_ONLY"),
                ("decision_owner", "CONTRACTS_SOLE_PURE_POLICY_DECISION_PATH"),
            ),
        ),
        ("closed_enum_manifest", LANGUAGE_CORE_CLOSED_ENUM_MANIFEST),
        ("ref_preimage_manifest", LANGUAGE_CORE_REF_PREIMAGE_MANIFEST),
        ("generation_order_rules", LANGUAGE_CORE_GENERATION_ORDER_RULES),
        ("product_causal_owner_manifest", LANGUAGE_CORE_PRODUCT_CAUSAL_OWNER_MANIFEST),
        (
            "direct_binding_rules",
            (
                "project_direct_argument_bindings_is_sole_direct_binding_table",
                "relation_qualifier_owner_is_R_with_source_argument_role",
                "relation_grounded_frame_owner_is_endpoint_D",
                "R_AND_D_ROLE_SEPARATION_REQUIRED",
            ),
        ),
        (
            "surface_owner_total_rules",
            (
                "project_predicate_head_owner_total_exact3_branch_table",
                "project_explicit_subject_surface_owner_total_exact4_branch_table",
                "zero_subject_removes_subject_part_only_and_retains_predicate_head",
                "reference_state_transition_and_terminal_duty_are_total_derived",
            ),
        ),
    )
    normal_form_and_profile_manifest = (
        ("schema_version", "cocolon.cmee.v1a.stage1_normal_form_and_profile_manifest.v1"),
        ("normal_form_version", CMEE_STAGE1_NORMAL_FORM_VERSION),
        ("normal_form_exact6", LANGUAGE_CORE_NORMAL_FORM_EXACT6_RULES),
        ("correctable_defect_exact8", tuple(row.value for row in CorrectableDefectKind)),
        ("layout_seed_exact5", LANGUAGE_CORE_LAYOUT_SEED_EXACT5_RULES),
        ("profile_exact8", LANGUAGE_CORE_PROFILE_EXACT8_RULES),
        (
            "profile_reducer",
            (
                "pool_global_applicability_before_candidate_observation",
                "exact7_required_applicable_and_concrete_before_abstract_pool_global_optional",
                "not_applicable_only_for_concrete_before_abstract_and_excluded_from_lexicographic_key",
                "profile_plus_signature_rank_key_must_be_globally_unique",
            ),
        ),
        ("stage_a_and_b", LANGUAGE_CORE_STAGE_A_B_RULES),
        (
            "idempotence_and_defect_proof",
            (
                "normalizer_called_exact1_per_internal_layout",
                "ordered_phase_trace_exact6",
                "normalize_normalized_artifact_returns_byte_equal_artifact",
                "correctable_defect_rows_exact0_after_normalization",
            ),
        ),
    )
    manifests = (
        ("language_core_contract_manifest", stage1_canonical_json_bytes(_contract_manifest())),
        ("construction_registry", stage1_canonical_json_bytes(CONSTRUCTION_REGISTRY)),
        ("emlis_expression_assets", stage1_canonical_json_bytes(EXPRESSION_ASSET_REGISTRY)),
        ("response_object_reference_assets", stage1_canonical_json_bytes(RESPONSE_OBJECT_ASSET_REGISTRY)),
        ("functional_surface_assets", stage1_canonical_json_bytes(FUNCTIONAL_ASSET_REGISTRY)),
        ("participant_lexeme_assets", stage1_canonical_json_bytes(PARTICIPANT_ASSET_REGISTRY)),
        ("structural_surface_assets", stage1_canonical_json_bytes(STRUCTURAL_ASSET_REGISTRY)),
        ("policy_and_enum_manifest", stage1_canonical_json_bytes(policy_and_enum_manifest)),
        ("normal_form_and_profile_manifest", stage1_canonical_json_bytes(normal_form_and_profile_manifest)),
    )
    result = (*frozen_file_payloads, *manifests)
    if len(result) != 16:
        raise Stage1CompositionError("LANGUAGE_CORE_IDENTITY_PAYLOAD_COUNT_STOP")
    return tuple(result)


def compute_language_core_identity(repository_root: Optional[Path] = None) -> str:
    material = bytearray(b"COCOLON_CMEE_STAGE1_LANGUAGE_CORE_IDENTITY_V1\x00")
    for name, payload in language_core_identity_payloads(repository_root):
        name_bytes = name.encode("utf-8")
        material.extend(len(name_bytes).to_bytes(8, "big"))
        material.extend(name_bytes)
        material.extend(len(payload).to_bytes(8, "big"))
        material.extend(payload)
    return hashlib.sha256(material).hexdigest()


validate_language_core_registry_invariant()
LANGUAGE_CORE_IDENTITY = compute_language_core_identity()


__all__ = (
    "ArtifactCompositionCandidate",
    "ClauseArgumentRole",
    "ClauseScalarAxis",
    "CONSTRUCTION_REGISTRY",
    "CorrectableDefectKind",
    "DiscoursePreferenceProfile",
    "EmlisSubjectiveMeaningPlan",
    "LANGUAGE_CORE_IDENTITY",
    "LayoutPreferenceSeed",
    "NormalFormPhase",
    "NormalizedDraftArtifact",
    "PredicateValency",
    "QualifierLookupScope",
    "QualifierValueRow",
    "RelationEndpointCandidateRow",
    "RetainedReceptionActRow",
    "SOURCE_SCALAR_MORPHOLOGY_ASSET_REGISTRY",
    "SentenceJob",
    "Stage1CompositionError",
    "Stage1CompositionResult",
    "Stage1SubjectivePlanningInputs",
    "Stage1SurfaceCompositionInputs",
    "canonical_normalized_bytes",
    "compose_stage1_from_projection",
    "compute_language_core_identity",
    "derive_discourse_preference_profile",
    "language_core_identity_payloads",
    "normalize_to_normal_form",
    "project_scalar_surface_realization_rows",
    "project_stage1_discourse_arc",
    "project_subjective_meaning_plan",
    "select_eligible_constructions",
    "validate_language_core_registry_invariant",
)
