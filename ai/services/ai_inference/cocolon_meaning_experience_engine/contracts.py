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
from dataclasses import (
    dataclass,
    field,
    fields as dataclass_fields,
    is_dataclass,
    replace,
)
from enum import Enum
from typing import Any, Mapping, Optional, Sequence, Tuple


CMEE_SCHEMA_VERSION = "cocolon.cmee.v1a.i1sx.material_unknown.v2"
CMEE_SOURCE_OWNER_POLICY_VERSION = "cocolon.cmee.v1a.source_owner_resolution.v2"
CMEE_SOURCE_CONTRACT_VERSION = "cocolon.cmee.emlis.current_input.text_grounded.v2"
CMEE_OBLIGATION_VERSION = "cocolon.cmee.emlis.i1sx.owner_obligation.v1"
CMEE_OWNER_UNIVERSE_SCHEMA_VERSION = "cocolon.cmee.v1a.owner_universe.v1"
CMEE_COMMON_GUARD_PROOF_VERSION = "cocolon.cmee.v1a.common_guard_proof.v1"
CMEE_GROUNDED_GRAPH_SCHEMA_VERSION = "cocolon.cmee.grounded_meaning_graph.v1alpha1"
CMEE_STAGE1_RESPONSE_SCHEMA_VERSION_V1 = (
    "cocolon.cmee.v1a.emlis_stage1_response.v1"
)
CMEE_STAGE1_RESPONSE_SCHEMA_VERSION_V2 = (
    "cocolon.cmee.v1a.emlis_stage1_response.v2"
)
CMEE_STAGE1_RESPONSE_SCHEMA_VERSION = CMEE_STAGE1_RESPONSE_SCHEMA_VERSION_V1
CMEE_STAGE1_TRACE_EXTENSION_SCHEMA_VERSION_V1 = (
    "cocolon.cmee.v1a.emlis_stage1_positive_trace_extension.v1"
)
CMEE_STAGE1_TRACE_EXTENSION_SCHEMA_VERSION_V2 = (
    "cocolon.cmee.v1a.emlis_stage1_positive_trace_extension.v2"
)
CMEE_STAGE1_TRACE_EXTENSION_SCHEMA_VERSION = (
    CMEE_STAGE1_TRACE_EXTENSION_SCHEMA_VERSION_V1
)
CMEE_STAGE1_IDENTITY_ALGORITHM = (
    "cocolon.cmee.identity.typed_canonical_json_sha256.v1"
)
CMEE_STAGE1_EMLIS_OWNER_REF_V1 = (
    "owner:emlis@cocolon.cmee.v1a.emlis_stage1_response.v1"
)
CMEE_STAGE1_EMLIS_OWNER_REF_V2 = (
    "owner:emlis@cocolon.cmee.v1a.emlis_stage1_response.v2"
)
CMEE_STAGE1_EMLIS_OWNER_REF = CMEE_STAGE1_EMLIS_OWNER_REF_V1
# Step 1 freezes the final v2 identity values without relabelling the callable
# v1 response route.  The active constants above, the v1 realizer registry and
# the runner move together only at the atomic cutover owned by Step 5.
CMEE_STAGE1_FINAL_LOGICAL_ID_REGISTRY = (
    (
        "CMEE_STAGE1_RESPONSE_SCHEMA_VERSION",
        "cocolon.cmee.v1a.emlis_stage1_response.v2",
    ),
    (
        "CMEE_STAGE1_SUBJECTIVE_PROPOSITION_SCHEMA_VERSION",
        "cocolon.cmee.v1a.emlis_subjective_proposition.v2",
    ),
    (
        "CMEE_STAGE1_COMPOSITION_POLICY_VERSION",
        "cocolon.emlis.stage1.discourse_composition.v2",
    ),
    (
        "CMEE_STAGE1_NORMAL_FORM_VERSION",
        "cocolon.cmee.v1a.emlis_stage1_normal_form.v2",
    ),
    (
        "CMEE_STAGE1_CONSTRUCTION_GRAMMAR_POLICY_VERSION",
        "cocolon.emlis.stage1.grounded_construction_grammar.v2",
    ),
    (
        "CMEE_STAGE1_PROJECTION_PREIMAGE_REF_VERSION",
        "cocolon.cmee.v1a.emlis_stage1_projection_preimage_ref.v1",
    ),
    (
        "CMEE_STAGE1_SUBJECTIVE_BASIS_BINDING_REF_VERSION",
        "cocolon.cmee.v1a.emlis_subjective_basis_binding_ref.v1",
    ),
    (
        "CMEE_STAGE1_SOURCE_QUALIFIER_BINDING_REF_VERSION",
        "cocolon.cmee.v1a.emlis_source_qualifier_binding_ref.v1",
    ),
    (
        "CMEE_STAGE1_POLICY_BASIS_BINDING_REF_VERSION",
        "cocolon.cmee.v1a.emlis_policy_basis_binding_ref.v1",
    ),
    (
        "CMEE_STAGE1_POLICY_TARGET_KEY_VERSION",
        "cocolon.cmee.v1a.emlis_policy_target_key.v1",
    ),
    (
        "CMEE_STAGE1_POLICY_APPLICATION_ROW_ID_VERSION",
        "cocolon.cmee.v1a.emlis_policy_application_row_id.v1",
    ),
    (
        "CMEE_STAGE1_SUBJECTIVE_RESPONSIBILITY_REF_VERSION",
        "cocolon.cmee.v1a.emlis_subjective_responsibility_ref.v1",
    ),
    (
        "CMEE_STAGE1_SUBJECTIVE_OPPORTUNITY_KEY_VERSION",
        "cocolon.cmee.v1a.emlis_subjective_opportunity_key.v1",
    ),
    (
        "CMEE_STAGE1_ARC_DEPENDENCY_REF_VERSION",
        "cocolon.cmee.v1a.emlis_arc_dependency_ref.v1",
    ),
    (
        "CMEE_STAGE1_DISCOURSE_ARC_REF_VERSION",
        "cocolon.cmee.v1a.emlis_stage1_discourse_arc_ref.v1",
    ),
    (
        "CMEE_STAGE1_COMPOSITION_DUTY_REF_VERSION",
        "cocolon.cmee.v1a.emlis_composition_duty_ref.v1",
    ),
    (
        "CMEE_STAGE1_REFERENCE_STATE_REF_VERSION",
        "cocolon.cmee.v1a.emlis_discourse_reference_state_ref.v2",
    ),
    (
        "CMEE_STAGE1_CLAUSE_SCALAR_CONSTRAINT_REF_VERSION",
        "cocolon.cmee.v1a.emlis_clause_scalar_constraint_ref.v1",
    ),
    (
        "CMEE_STAGE1_CLAUSE_INTENT_ID_VERSION",
        "cocolon.cmee.v1a.emlis_clause_intent_id.v1",
    ),
    (
        "CMEE_STAGE1_CLAUSE_PLAN_ID_VERSION",
        "cocolon.cmee.v1a.emlis_clause_plan_id.v1",
    ),
    (
        "CMEE_STAGE1_RESPONSE_OBJECT_EXPRESSION_ID_VERSION",
        "cocolon.cmee.v1a.emlis_response_object_expression_id.v1",
    ),
    (
        "CMEE_STAGE1_PROFILE_EVIDENCE_REF_VERSION",
        "cocolon.cmee.v1a.emlis_profile_evidence_ref.v1",
    ),
    (
        "CMEE_STAGE1_SEALED_UNIT_PLAN_ROW_ID_VERSION",
        "cocolon.cmee.v1a.emlis_sealed_unit_plan_row_id.v1",
    ),
    (
        "CMEE_STAGE1_COMPOSITION_LAYOUT_ID_VERSION",
        "cocolon.cmee.v1a.emlis_composition_layout_id.v1",
    ),
    (
        "CMEE_STAGE1_ARTIFACT_COMPOSITION_CANDIDATE_ID_VERSION",
        "cocolon.cmee.v1a.emlis_artifact_composition_candidate_id.v1",
    ),
    (
        "CMEE_STAGE1_SELECTED_ARTIFACT_ID_VERSION",
        "cocolon.cmee.v1a.emlis_selected_stage1_artifact_id.v1",
    ),
    (
        "CMEE_STAGE1_TRACE_EXTENSION_SCHEMA_VERSION",
        "cocolon.cmee.v1a.emlis_stage1_positive_trace_extension.v2",
    ),
    (
        "CMEE_STAGE1_EMLIS_OWNER_REF",
        "owner:emlis@cocolon.cmee.v1a.emlis_stage1_response.v2",
    ),
)
CMEE_STAGE1_ANTI_TEMPLATE_FORBIDDEN_REGISTRY_FIELDS = (
    "case_id",
    "case_family",
    "fixture_id",
    "exact8_id",
    "raw_text",
    "raw_pattern",
    "source_regex",
    "semantic_keyword",
    "expected_text",
    "finished_surface",
    "finished_clause",
    "finished_sentence",
)
CMEE_STAGE1_ANTI_TEMPLATE_FORBIDDEN_SELECTOR_INPUTS = (
    "raw_source",
    "raw_text",
    "normalized_input",
    "evidence_text",
    "resolver",
    "regex_result",
    "case_id",
    "fixture_id",
    "fixture",
    "exact8_id",
    "source_phrase_family",
    "semantic_domain_keyword",
    "input_hash",
)
_CMEE_STAGE1_ANTI_TEMPLATE_ALLOWED_REGISTRY_FIELDS_ORDERED = (
    "construction_id",
    "argument_slots",
    "role_order",
    "valency",
    "particle_rules",
    "auxiliary_rules",
    "relation_combinators",
    "inflection_order",
)
_CMEE_STAGE1_ANTI_TEMPLATE_ALLOWED_SELECTOR_INPUTS_ORDERED = (
    "grammatical_shape_key",
    "predicate_valency",
    "syntactic_orientation",
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


class SourceOwnerDisposition(str, Enum):
    """Exact source-owner disposition set from the CMEE V1 contract."""

    SOURCE_EXPLICIT_VISIBLE = "SOURCE_EXPLICIT_VISIBLE"
    SUPPLEMENTAL_USER_VISIBLE = "SUPPLEMENTAL_USER_VISIBLE"
    UNKNOWN_PRESERVED_LIMITED = "UNKNOWN_PRESERVED_LIMITED"
    CLARIFICATION_TARGET = "CLARIFICATION_TARGET"
    NOT_VISIBLE_UNRESOLVED = "NOT_VISIBLE_UNRESOLVED"
    SEPARATE_SAFETY = "SEPARATE_SAFETY"


class OwnerClass(str, Enum):
    REQUIRED = "REQUIRED"
    ACTIVE_OPTIONAL = "ACTIVE_OPTIONAL"


class ResolverResolution(str, Enum):
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


class ForegroundScopeBasisKind(str, Enum):
    SOURCE_EXPLICIT_TARGET_TOPIC_OR_SCOPE = (
        "SOURCE_EXPLICIT_TARGET_TOPIC_OR_SCOPE"
    )
    LAYER1_REQUIRED_OBSERVATION_OBJECT = (
        "LAYER1_REQUIRED_OBSERVATION_OBJECT"
    )
    EXISTING_REQUIRED_RETENTION_DUTY = (
        "EXISTING_REQUIRED_RETENTION_DUTY"
    )
    SOURCE_CONNECTED_RELATION = "SOURCE_CONNECTED_RELATION"
    MATERIAL_UNKNOWN_OR_REQUIRED_QUALIFIER = (
        "MATERIAL_UNKNOWN_OR_REQUIRED_QUALIFIER"
    )


class ForegroundScopeRelationKind(str, Enum):
    CONTRAST = "contrast"
    COEXISTENCE = "coexistence"
    CONTINUATION = "continuation"
    CORRECTION = "correction"


_FOREGROUND_SCOPE_RELATION_KIND_BY_SOURCE_RELATION = {
    "contrast": ForegroundScopeRelationKind.CONTRAST,
    "coexistence": ForegroundScopeRelationKind.COEXISTENCE,
    "continuation": ForegroundScopeRelationKind.CONTINUATION,
    "correction": ForegroundScopeRelationKind.CORRECTION,
}
_FOREGROUND_SCOPE_RELATION_KIND_BY_TYPED_SOURCE_RELATION = {
    (
        "wish_and_constraint",
        RelationOperator.COEXISTS_WITH,
    ): ForegroundScopeRelationKind.COEXISTENCE,
    (
        "continuation_or_refusal",
        RelationOperator.TENSION_WITH,
    ): ForegroundScopeRelationKind.CONTRAST,
    (
        "preserves_despite",
        RelationOperator.TENSION_WITH,
    ): ForegroundScopeRelationKind.CONTRAST,
    (
        "attempt_and_block",
        RelationOperator.TENSION_WITH,
    ): ForegroundScopeRelationKind.CONTRAST,
    (
        "action_supports_change",
        RelationOperator.ACTION_PRECEDES_CHANGE,
    ): ForegroundScopeRelationKind.CONTINUATION,
    (
        "temporal_before_after",
        RelationOperator.TEMPORALLY_PRECEDES,
    ): ForegroundScopeRelationKind.CONTINUATION,
    (
        "shift_from_to",
        RelationOperator.TEMPORALLY_PRECEDES,
    ): ForegroundScopeRelationKind.CONTINUATION,
}


def project_foreground_scope_relation_kind(
    source_relation: str,
    *,
    relation_operators: Sequence[RelationOperator] = (),
) -> Optional[ForegroundScopeRelationKind]:
    """Project a source relation into the closed exact4 scope vocabulary.

    Literal exact4 source relations are sufficient.  A legacy Stage-1
    relation is admitted only when its source-bound endpoint shape has a
    unique typed operator proving its exact4 role.  Cause/result,
    evaluation, uncertain connection, and other relations are deliberately
    not promoted into a scope-compatibility proof.
    """

    if type(source_relation) is not str:
        return None
    direct = _FOREGROUND_SCOPE_RELATION_KIND_BY_SOURCE_RELATION.get(
        source_relation
    )
    if direct is not None:
        return direct
    if type(relation_operators) is not tuple or any(
        type(value) is not RelationOperator for value in relation_operators
    ):
        return None
    projected = {
        value
        for relation_operator in relation_operators
        for value in (
            _FOREGROUND_SCOPE_RELATION_KIND_BY_TYPED_SOURCE_RELATION.get(
                (source_relation, relation_operator)
            ),
        )
        if value is not None
    }
    return next(iter(projected)) if len(projected) == 1 else None


class ForegroundScopeCompatibilityAxis(str, Enum):
    OWNER = "owner"
    WORLD = "world"
    EPISTEMIC = "epistemic"
    TIME = "time"
    ASPECT = "aspect"
    MODALITY = "modality"
    POLARITY = "polarity"
    SCOPE = "scope"
    REQUIRED_QUALIFIER = "required_qualifier"
    UNKNOWN = "unknown"


class ForegroundScopeDerivationState(str, Enum):
    FOREGROUND_SCOPE_AVAILABLE = "FOREGROUND_SCOPE_AVAILABLE"
    COMPETING_MATERIAL_SCOPES = "COMPETING_MATERIAL_SCOPES"
    FOREGROUND_SCOPE_STRUCTURE_INSUFFICIENT = (
        "FOREGROUND_SCOPE_STRUCTURE_INSUFFICIENT"
    )
    NO_SAFE_FOREGROUND_OBJECT = "NO_SAFE_FOREGROUND_OBJECT"


class WholeReadingConsequenceCode(str, Enum):
    INPUT_CENTER_CHANGED = "INPUT_CENTER_CHANGED"
    RELATION_STRUCTURE_CHANGED = "RELATION_STRUCTURE_CHANGED"
    TEMPORAL_FLOW_CHANGED = "TEMPORAL_FLOW_CHANGED"
    RESOLUTION_TREATMENT_CHANGED = "RESOLUTION_TREATMENT_CHANGED"
    WORLD_OR_OWNER_DISTINCTION_CHANGED = (
        "WORLD_OR_OWNER_DISTINCTION_CHANGED"
    )
    MODALITY_POLARITY_OR_LIMITATION_CHANGED = (
        "MODALITY_POLARITY_OR_LIMITATION_CHANGED"
    )
    EPISODICITY_BOUNDARY_CHANGED = "EPISODICITY_BOUNDARY_CHANGED"


class MeaningReadingOperation(str, Enum):
    KEEP_DISTINCT = "KEEP_DISTINCT"
    HOLD_RELATION = "HOLD_RELATION"
    TRACK_TRANSITION = "TRACK_TRANSITION"
    NOTICE_PERSISTENCE = "NOTICE_PERSISTENCE"
    RECOGNIZE_BOUNDED_ACTUALITY = "RECOGNIZE_BOUNDED_ACTUALITY"
    HOLD_UNRESOLVED = "HOLD_UNRESOLVED"
    HOLD_QUALIFIED_EVENT_STATE = "HOLD_QUALIFIED_EVENT_STATE"


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


class SubjectiveContentKind(str, Enum):
    AFFECT = "AFFECT"
    APPRAISAL = "APPRAISAL"
    MATERIAL_VALUE = "MATERIAL_VALUE"
    RELATIONAL_POSITION = "RELATIONAL_POSITION"


class SubjectiveAssertionModality(str, Enum):
    EMLIS_FEELING = "EMLIS_FEELING"
    EMLIS_APPRAISAL = "EMLIS_APPRAISAL"
    EMLIS_VALUE_POSITION = "EMLIS_VALUE_POSITION"
    EMLIS_RELATIONAL_INTENTION = "EMLIS_RELATIONAL_INTENTION"
    EMLIS_BOUNDED_REFUSAL = "EMLIS_BOUNDED_REFUSAL"


class SubjectiveBasisRole(str, Enum):
    ELICITOR = "ELICITOR"
    APPRAISED_OBJECT = "APPRAISED_OBJECT"
    RELATION_LEFT = "RELATION_LEFT"
    RELATION_RIGHT = "RELATION_RIGHT"
    ACTION = "ACTION"
    CHANGE = "CHANGE"
    BEFORE = "BEFORE"
    AFTER = "AFTER"
    RESIDUE = "RESIDUE"
    UNFINISHED = "UNFINISHED"
    CHOICE_TARGET = "CHOICE_TARGET"


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


class PolicyBasisOwnerKind(str, Enum):
    CONTRIBUTION = "CONTRIBUTION"
    MATERIAL_UNKNOWN = "MATERIAL_UNKNOWN"


class PolicyBasisRole(str, Enum):
    BURDEN_OR_RESIDUE = "BURDEN_OR_RESIDUE"
    DIRECTION = "DIRECTION"
    CHANGE_OR_ACTUAL_OUTPUT = "CHANGE_OR_ACTUAL_OUTPUT"
    COEXISTENCE_OR_TENSION = "COEXISTENCE_OR_TENSION"
    UNFINISHED = "UNFINISHED"
    VISIBILITY_ACT_BASIS = "VISIBILITY_ACT_BASIS"
    MATERIAL_UNKNOWN = "MATERIAL_UNKNOWN"


class AppraisalDimension(str, Enum):
    MATERIAL_WEIGHT = "MATERIAL_WEIGHT"
    RELATIONAL_NONCOLLAPSE = "RELATIONAL_NONCOLLAPSE"
    BOUNDED_CHANGE = "BOUNDED_CHANGE"
    UNFINISHED_OPENNESS = "UNFINISHED_OPENNESS"
    AGENCY_BOUNDARY = "AGENCY_BOUNDARY"


class AppraisalOperation(str, Enum):
    RECEIVE_AS_MATERIAL = "RECEIVE_AS_MATERIAL"
    PRESERVE_BOTH_ENDPOINTS = "PRESERVE_BOTH_ENDPOINTS"
    RECOGNIZE_AS_BOUNDED = "RECOGNIZE_AS_BOUNDED"
    LEAVE_UNFINISHED = "LEAVE_UNFINISHED"
    RESPECT_CHOICE = "RESPECT_CHOICE"


class MaterialRisk(str, Enum):
    MINIMIZATION = "MINIMIZATION"
    WISH_TO_OBLIGATION = "WISH_TO_OBLIGATION"
    NO_RESULT_TO_NO_VALUE = "NO_RESULT_TO_NO_VALUE"
    SINGLE_EVENT_TO_IDENTITY = "SINGLE_EVENT_TO_IDENTITY"
    BOUNDED_CHANGE_TO_UNIVERSAL_SOLUTION = (
        "BOUNDED_CHANGE_TO_UNIVERSAL_SOLUTION"
    )
    ONE_SIDE_TO_TRUE_SELF = "ONE_SIDE_TO_TRUE_SELF"
    POSSIBILITY_TO_FACT = "POSSIBILITY_TO_FACT"
    REMOVE_USER_AGENCY = "REMOVE_USER_AGENCY"
    UNKNOWN_TO_FALSE_UNDERSTANDING = "UNKNOWN_TO_FALSE_UNDERSTANDING"


class RelationalPositionKind(str, Enum):
    STANCE = "STANCE"
    BOUNDED_COUNTERPOSITION = "BOUNDED_COUNTERPOSITION"


class RelationalCommitment(str, Enum):
    AFFIRM_SOURCE_BOUND_DIRECTION = "AFFIRM_SOURCE_BOUND_DIRECTION"
    STAY_WITH = "STAY_WITH"
    HOLD_OPEN = "HOLD_OPEN"
    WELCOME_BOUNDED_CHANGE = "WELCOME_BOUNDED_CHANGE"
    PROTECT_AGENCY = "PROTECT_AGENCY"
    DECLINE_PROMOTION = "DECLINE_PROMOTION"


class RelationalClosure(str, Enum):
    NONE = "NONE"
    BOUNDED = "BOUNDED"
    OPEN = "OPEN"


class SurfaceDerivationKind(str, Enum):
    LITERAL_SUBSPAN = "LITERAL_SUBSPAN"
    NORMALIZED_INFLECTION = "NORMALIZED_INFLECTION"
    COMPOSITIONAL_JOIN = "COMPOSITIONAL_JOIN"
    REGISTERED_EMLIS_LEXEME = "REGISTERED_EMLIS_LEXEME"
    REGISTERED_PARTICIPANT_LEXEME = "REGISTERED_PARTICIPANT_LEXEME"
    REGISTERED_STRUCTURAL_ASSET = "REGISTERED_STRUCTURAL_ASSET"
    PROJECTED_RESPONSE_OBJECT = "PROJECTED_RESPONSE_OBJECT"
    PROJECTED_FUNCTIONAL_ASSET = "PROJECTED_FUNCTIONAL_ASSET"


class SourceLeafExtent(str, Enum):
    FULL_EVIDENCE_LITERAL = "FULL_EVIDENCE_LITERAL"
    CERTIFIED_LITERAL_SUBSPAN = "CERTIFIED_LITERAL_SUBSPAN"


class SourceLeafCardinality(str, Enum):
    EXACT1 = "EXACT1"
    ORDERED_EXACT2 = "ORDERED_EXACT2"


class SourceSentenceShape(str, Enum):
    ONE_SENTENCE = "ONE_SENTENCE"
    MULTI_SENTENCE = "MULTI_SENTENCE"


class SourceFinalTerminalClass(str, Enum):
    ABSENT = "ABSENT"
    PERIOD = "PERIOD"
    QUESTION = "QUESTION"
    EXCLAMATION = "EXCLAMATION"


class SourceQuoteTopology(str, Enum):
    NONE = "NONE"
    BALANCED_KAGI_ONLY = "BALANCED_KAGI_ONLY"
    BALANCED_NIJUKAGI_ONLY = "BALANCED_NIJUKAGI_ONLY"
    BALANCED_MIXED = "BALANCED_MIXED"


class SourceLineBreakShape(str, Enum):
    NONE = "NONE"
    LF_ONLY = "LF_ONLY"
    CRLF_ONLY = "CRLF_ONLY"


class SourceRealizationMode(str, Enum):
    QUOTE_COMPLEMENT = "QUOTE_COMPLEMENT"
    CONTENT_NOMINAL = "CONTENT_NOMINAL"
    CLASSIFIED_CONTENT = "CLASSIFIED_CONTENT"
    COORDINATED_EXACT2 = "COORDINATED_EXACT2"
    BOUNDARY_SPLIT_EXACT2 = "BOUNDARY_SPLIT_EXACT2"


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
    "@cocolon.emlis.stage1.microgrammar.v2"
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
class GroundedSourceQualifierRow:
    """Source-owned qualifier projection available before subjective planning."""

    node_ref: str
    qualifier_refs: Tuple[str, ...]


@dataclass(frozen=True, slots=True)
class GroundedSourceRelationRow:
    """Cap-free exact4 relation projection available before meaning selection."""

    relation_ref: str
    relation_kind: ForegroundScopeRelationKind


@dataclass(frozen=True, slots=True, repr=False)
class PreMeaningGroundedInputs:
    """Sanitized semantic closure; Reception-side data is intentionally absent."""

    schema_version: str
    stage1_response_schema_version: str
    grounded_graph: GroundedMeaningGraph
    grounded_graph_ref: str
    parent_observation_duty_ref: str
    interpretation_candidate_rows: Tuple[EmlisInterpretationCandidate, ...]
    meaning_field: EmlisMeaningField
    observation_contribution_rows: Tuple[PlannedObservationContribution, ...]
    ordered_observation_refs: Tuple[str, ...]
    material_unknown_refs: Tuple[str, ...]
    observation_depth_class: ObservationDepthClass
    source_qualifier_rows: Tuple[GroundedSourceQualifierRow, ...]
    source_relation_rows: Tuple[GroundedSourceRelationRow, ...]


@dataclass(frozen=True, slots=True)
class AllowedReceptionOpportunityEnvelope:
    """Post-scope Reception opportunity data; it cannot select meaning."""

    schema_version: str
    source_envelope_id: str
    parent_reception_duty_ref: str
    allowed_reception_act_ids: Tuple[str, ...]
    safety_boundary_codes: Tuple[str, ...]


@dataclass(frozen=True, slots=True)
class ForegroundScopeBasisRow:
    """One source-connected, non-ranking basis for Foreground Scope."""

    schema_version: str
    basis_kind: ForegroundScopeBasisKind
    scope_object_refs: Tuple[str, ...]
    source_object_refs: Tuple[str, ...]
    source_evidence_refs: Tuple[str, ...]
    layer1_required_object_refs: Tuple[str, ...]
    required_retention_duty_refs: Tuple[str, ...]
    source_connected_relation_refs: Tuple[str, ...]
    material_unknown_refs: Tuple[str, ...]
    required_qualifier_refs: Tuple[str, ...]
    owner_refs: Tuple[str, ...]
    world_refs: Tuple[str, ...]
    epistemic_state_refs: Tuple[str, ...]
    time_refs: Tuple[str, ...]
    aspect_refs: Tuple[str, ...]
    modality_refs: Tuple[str, ...]
    polarity_refs: Tuple[str, ...]
    scope_refs: Tuple[str, ...]


@dataclass(frozen=True, slots=True)
class ForegroundScopeObjectCompatibilityRow:
    """Per-object exact10 slots used before any canonical scope union."""

    schema_version: str
    scope_object_ref: str
    owner_refs: Tuple[str, ...]
    world_refs: Tuple[str, ...]
    epistemic_state_refs: Tuple[str, ...]
    time_refs: Tuple[str, ...]
    aspect_refs: Tuple[str, ...]
    modality_refs: Tuple[str, ...]
    polarity_refs: Tuple[str, ...]
    scope_refs: Tuple[str, ...]
    required_qualifier_refs: Tuple[str, ...]
    material_unknown_refs: Tuple[str, ...]


@dataclass(frozen=True, slots=True)
class ForegroundScope:
    schema_version: str
    scope_id: str
    integrated_scope_object_refs: Tuple[str, ...]
    basis_row_refs: Tuple[str, ...]
    source_connected_relation_refs: Tuple[str, ...]
    required_retention_duty_refs: Tuple[str, ...]
    material_unknown_refs: Tuple[str, ...]
    required_qualifier_refs: Tuple[str, ...]
    source_evidence_refs: Tuple[str, ...]


@dataclass(frozen=True, slots=True)
class ForegroundScopeDerivation:
    schema_version: str
    state: ForegroundScopeDerivationState
    foreground_scope: Optional[ForegroundScope]
    retained_foreground_source_object_refs: Tuple[str, ...]
    unresolved_scope_refs: Tuple[str, ...]
    missing_structure_refs: Tuple[str, ...]
    derivation_evidence_refs: Tuple[str, ...]


@dataclass(frozen=True, slots=True)
class MeaningComponentSemanticKey:
    typed_predicate_key: str
    semantic_kind_key: str
    owner_key: str
    scope_key: str
    role_key: str


@dataclass(frozen=True, slots=True)
class MeaningSemanticSignature:
    """Canonical, content-bearing structure; never raw text or local IDs."""

    schema_version: str
    reading_operation: MeaningReadingOperation
    input_center_keys: Tuple[str, ...]
    component_role_keys: Tuple[str, ...]
    relation_direction_keys: Tuple[str, ...]
    epistemic_state_keys: Tuple[str, ...]
    temporal_state_keys: Tuple[str, ...]
    resolution_treatment_keys: Tuple[str, ...]
    world_or_owner_distinction_keys: Tuple[str, ...]
    modality_polarity_or_limitation_keys: Tuple[str, ...]
    episodicity_boundary_keys: Tuple[str, ...]
    qualifier_keys: Tuple[str, ...]
    component_semantic_keys: Tuple[MeaningComponentSemanticKey, ...]


@dataclass(frozen=True, slots=True)
class WholeReadingConsequenceValidationContext:
    """IM00 binding seam; the actual difference issuer is implemented in IM02."""

    schema_version: str
    foreground_scope: ForegroundScope
    required_difference_ref: str
    source_evidence_refs: Tuple[str, ...]
    counterfactual_mutation_ref: str
    baseline_semantic_signature: MeaningSemanticSignature
    mutated_semantic_signature: MeaningSemanticSignature


@dataclass(frozen=True, slots=True)
class WholeReadingConsequenceRow:
    schema_version: str
    consequence_id: str
    consequence_code: WholeReadingConsequenceCode
    foreground_scope_ref: str
    required_difference_ref: str
    source_evidence_refs: Tuple[str, ...]
    counterfactual_mutation_ref: str
    baseline_semantic_signature: MeaningSemanticSignature
    mutated_semantic_signature: MeaningSemanticSignature


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
class SubjectiveBasisBinding:
    projection_preimage_ref: str
    binding_ref: str
    contribution_ref: str
    semantic_ref: str
    role: SubjectiveBasisRole


@dataclass(frozen=True, slots=True)
class SourceQualifierBinding:
    projection_preimage_ref: str
    source_qualifier_binding_ref: str
    basis_binding_ref: str
    source_candidate_ref: str
    source_argument_role: Optional[ArgumentRole]
    canonical_qualifier_codes: Tuple[str, str, str]
    polarity: str
    modality: str
    time_scope: str


@dataclass(frozen=True, slots=True)
class PolicyBasisBinding:
    projection_preimage_ref: str
    binding_ref: str
    owner_kind: PolicyBasisOwnerKind
    owner_ref: str
    role: PolicyBasisRole


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
class EmlisAffectContent:
    category: AffectCategory
    intensity: AffectIntensity
    elicitor_bindings: Tuple[str, ...]


@dataclass(frozen=True, slots=True)
class EmlisAppraisalContent:
    dimension: AppraisalDimension
    operation: AppraisalOperation
    appraised_bindings: Tuple[str, ...]
    focal_relation_ref: Optional[str]
    protected_bindings: Tuple[str, ...]
    basis_contribution_refs: Tuple[str, ...]


@dataclass(frozen=True, slots=True)
class ValueApplication:
    principle_ref: str
    material_risk: MaterialRisk
    policy_application_row_refs: Tuple[str, ...]
    policy_basis_binding_refs: Tuple[str, ...]
    protected_subjective_binding_refs: Tuple[str, ...]


@dataclass(frozen=True, slots=True)
class MaterialValueContent:
    value_applications: Tuple[ValueApplication, ...]
    target_bindings: Tuple[str, ...]
    boundary_bindings: Tuple[str, ...]


@dataclass(frozen=True, slots=True)
class EmlisRelationalPosition:
    relational_position_kind: RelationalPositionKind
    stance_operator: StanceOperator
    target_bindings: Tuple[str, ...]
    boundary_bindings: Tuple[str, ...]
    commitment: RelationalCommitment
    closure: RelationalClosure


@dataclass(frozen=True, slots=True)
class SubjectivePropositionV2:
    """Final request-local proposition contract, registered but not wired."""

    schema_version: str
    content_kind: SubjectiveContentKind
    subjective_mode: SubjectiveMode
    subjective_operator: SubjectiveOperator
    target_contribution_refs: Tuple[str, ...]
    primary_target_refs: Tuple[str, ...]
    boundary_target_refs: Tuple[str, ...]
    response_object_refs: Tuple[str, ...]
    basis_binding_refs: Tuple[str, ...]
    source_qualifier_binding_refs: Tuple[str, ...]
    focal_relation_ref: Optional[str]
    affect_content: Optional[EmlisAffectContent]
    appraisal_content: Optional[EmlisAppraisalContent]
    material_value_content: Optional[MaterialValueContent]
    relational_position: Optional[EmlisRelationalPosition]
    referenced_actor_refs: Tuple[str, ...]
    referenced_experiencer_refs: Tuple[str, ...]
    addressee_role: str
    assertion_modality: SubjectiveAssertionModality
    epistemic_scope: str


@dataclass(frozen=True, slots=True)
class SurfaceDerivation:
    derivation_kind: SurfaceDerivationKind
    source_or_claim_refs: Tuple[str, ...]
    emlis_owner_ref: Optional[str]
    relation_or_clause_plan_refs: Tuple[str, ...]
    qualifier_refs: Tuple[str, ...]
    response_object_expression_ref: Optional[str]
    antecedent_unit_ref: Optional[str]
    participant_role_ref: Optional[str]
    evidence_refs: Tuple[str, ...]
    rule_ref: str
    input_scalar_ranges: Tuple[Tuple[int, int], ...]


@dataclass(frozen=True, slots=True)
class GroundedExpressionPlan:
    plan_ref: str
    semantic_refs: Tuple[str, ...]
    predicate_kind: str
    source_scope_refs: Tuple[str, ...]
    matrix_scope_refs: Tuple[str, ...]


@dataclass(frozen=True, slots=True)
class PredicateSenseSpec:
    sense_id: str
    sentence_job: str
    semantic_clause_kind: str
    semantic_sense: str
    frame_license_refs: Tuple[str, ...]


@dataclass(frozen=True, slots=True)
class PredicateSenseFrameLicense:
    sense_ref: str
    frame_ref: str


@dataclass(frozen=True, slots=True)
class JapaneseCaseFrameSpec:
    frame_id: str
    sense_ref: str
    frame_kind: str
    slot_roles: Tuple[str, ...]
    slot_requirements: Tuple[str, ...]
    complement_rule_ref: str
    topic_policy: str
    zero_policy: str
    atomic_head_ref: str
    morphology_ref: str
    modifier_ref: Optional[str]


@dataclass(frozen=True, slots=True)
class SourceLeafToken:
    leaf_ref: str
    semantic_ref: str
    source_envelope_ref: str
    evidence_ref: str
    extent: SourceLeafExtent
    raw_utf8_start: int
    raw_utf8_end: int
    payload_utf8: bytes = field(repr=False)
    sentence_shape: SourceSentenceShape
    final_terminal_class: SourceFinalTerminalClass
    quote_topology: SourceQuoteTopology
    line_break_shape: SourceLineBreakShape
    derivation: SurfaceDerivation


@dataclass(frozen=True, slots=True)
class SourceLeafGroup:
    group_ref: str
    cardinality: SourceLeafCardinality
    ordered_leaf_refs: Tuple[str, ...]


@dataclass(frozen=True, slots=True)
class SourceComplementPlan:
    mode: SourceRealizationMode
    group_ref: str
    complement_rule_ref: str
    quote_delimiter_refs: Tuple[str, ...]
    classifier_ref: Optional[str]
    coordinator_ref: Optional[str]
    case_slot_ref: str


@dataclass(frozen=True, slots=True)
class ArgumentRealizationPlan:
    plan_ref: str
    frame_ref: str
    slot_role: str
    semantic_ref: str
    particle_rule_ref: str
    provenance_refs: Tuple[str, ...]


@dataclass(frozen=True, slots=True)
class DiscourseReferenceStateRow:
    state_ref: str
    antecedent_refs: Tuple[str, ...]
    competitor_refs: Tuple[str, ...]
    focus_ref: Optional[str]
    speaker_ref: Optional[str]
    establishment_proof_refs: Tuple[str, ...]


@dataclass(frozen=True, slots=True)
class ClauseLinkPlan:
    link_plan_ref: str
    admitted_relation_ref: str
    placement: str
    token_owner_ref: str


@dataclass(frozen=True, slots=True)
class PredicateMorphologyPlan:
    plan_ref: str
    head_ref: str
    aspect_time: str
    polarity: str
    modal: str
    politeness: str
    terminal_order: Tuple[str, ...]


@dataclass(frozen=True, slots=True)
class JapaneseClauseIR:
    clause_ir_ref: str
    argument_plans: Tuple[ArgumentRealizationPlan, ...]
    source_complement_plan_ref: Optional[str]
    reference_state_ref: Optional[str]
    link_plan_ref: Optional[str]
    morphology_plan_ref: str
    semantic_digest: str


@dataclass(frozen=True, slots=True)
class LinearizedJapaneseClause:
    clause_ref: str
    text: str = field(repr=False)
    clause_frames: Tuple["ClauseFrame", ...] = ()
    realized_semantic_bindings: Tuple["RealizedSemanticBinding", ...] = ()
    surface_derivations: Tuple[SurfaceDerivation, ...] = ()


@dataclass(frozen=True, slots=True)
class JapaneseLocalPreferenceProfile:
    profile_ref: str
    comparison_rows: Tuple[Tuple[str, int], ...]


@dataclass(frozen=True, slots=True)
class AtomicPredicateHeadSpec:
    head_id: str
    frame_ref: str
    atomic_parts: Tuple[str, ...]
    inflection_class_ref: str
    lexical_family_ref: str


@dataclass(frozen=True, slots=True)
class LexicalFamilySpec:
    lexical_family_id: str
    atomic_parts: Tuple[str, ...]


@dataclass(frozen=True, slots=True)
class ComplementRuleSpec:
    complement_rule_id: str
    mode: SourceRealizationMode
    cardinality: SourceLeafCardinality
    slot_roles: Tuple[str, ...]
    structural_asset_refs: Tuple[str, ...]


@dataclass(frozen=True, slots=True)
class SenseComplementLicense:
    license_id: str
    sense_ref: str
    frame_ref: str
    complement_rule_ref: str
    classifier_ref: Optional[str]


@dataclass(frozen=True, slots=True)
class SourceClassifierSpec:
    classifier_id: str
    classifier_kind: str
    atomic_surface: str


@dataclass(frozen=True, slots=True)
class SourceFunctionalTokenSpec:
    token_id: str
    token_kind: str
    atomic_surface: str


@dataclass(frozen=True, slots=True)
class SourceFunctionalModifierSpec:
    modifier_id: str
    frame_ref: str
    placement: str
    atomic_surface: str


@dataclass(frozen=True, slots=True)
class SourceQuoteDelimiterRule:
    delimiter_rule_id: str
    source_quote_topology: SourceQuoteTopology
    outer_delimiter_kind: str


@dataclass(frozen=True, slots=True)
class CaseParticleSurfaceVariant:
    variant_kind: str
    atomic_surface: str


@dataclass(frozen=True, slots=True)
class CaseParticleRule:
    particle_rule_id: str
    frame_ref: str
    slot_role: str
    surface_variants: Tuple[CaseParticleSurfaceVariant, ...]


@dataclass(frozen=True, slots=True)
class InflectionClassSpec:
    inflection_class_id: str
    inflection_class: str


@dataclass(frozen=True, slots=True)
class MatrixMorphologyParadigmSpec:
    morphology_id: str
    frame_ref: str
    aspect_time: str
    polarity: str
    modal: str
    politeness: str
    inflection_recipe: str
    terminal_class: str


@dataclass(frozen=True, slots=True)
class ClauseLinkRule:
    link_rule_id: str
    relation_kind: str
    placement: str
    token_ref: str
    internal_relation_policy: str


@dataclass(frozen=True, slots=True)
class ReferenceZeroTopicRule:
    reference_rule_id: str
    discourse_condition: str
    realization_kind: str


@dataclass(frozen=True, slots=True)
class JapaneseLocalPreferenceRule:
    preference_rule_id: str
    preference_kind: str


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
    subjective_responsibility_refs: Tuple[str, ...] = ()
    selected_subjective_opportunity_key: str = ""


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
    projection_preimage_ref: str = ""
    composition_policy_ref: str = ""
    low_level_grammar_policy_ref: str = ""
    subjective_responsibility_rows: Tuple[
        SubjectiveResponsibilityRow, ...
    ] = ()
    subjective_opportunity_rows: Tuple[SubjectiveOpportunityRow, ...] = ()
    subjective_facet_suppression_rows: Tuple[
        SubjectiveFacetSuppressionRow, ...
    ] = ()
    subjective_basis_binding_rows: Tuple[SubjectiveBasisBinding, ...] = ()
    source_qualifier_binding_rows: Tuple[SourceQualifierBinding, ...] = ()
    policy_basis_binding_rows: Tuple[PolicyBasisBinding, ...] = ()
    policy_application_rows: Tuple[PolicyApplicationRow, ...] = ()


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


@dataclass(frozen=True, slots=True)
class Stage1V2UnitSeal:
    """Private v2 provenance retained until positive trace validation."""

    covered_duty_refs: Tuple[str, ...]
    sentence_job_refs: Tuple[str, ...]
    source_reception_act_refs: Tuple[str, ...]
    composition_candidate_ref: str
    composition_layout_ref: str
    selected_stage1_artifact_ref: str


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
    v2_trace_seal: Optional[Stage1V2UnitSeal] = None


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
    subjective_claim_refs: Tuple[str, ...] = ()
    covered_duty_refs: Tuple[str, ...] = ()
    sentence_job_refs: Tuple[str, ...] = ()
    source_reception_act_refs: Tuple[str, ...] = ()
    composition_candidate_ref: str = ""
    composition_layout_ref: str = ""
    selected_stage1_artifact_ref: str = ""


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
    GroundedSourceQualifierRow: ("qualifier_refs",),
    PreMeaningGroundedInputs: (
        "interpretation_candidate_rows",
        "observation_contribution_rows",
        "ordered_observation_refs",
        "material_unknown_refs",
        "source_qualifier_rows",
        "source_relation_rows",
    ),
    AllowedReceptionOpportunityEnvelope: (
        "allowed_reception_act_ids",
        "safety_boundary_codes",
    ),
    ForegroundScopeBasisRow: (
        "scope_object_refs",
        "source_object_refs",
        "source_evidence_refs",
        "layer1_required_object_refs",
        "required_retention_duty_refs",
        "source_connected_relation_refs",
        "material_unknown_refs",
        "required_qualifier_refs",
        "owner_refs",
        "world_refs",
        "epistemic_state_refs",
        "time_refs",
        "aspect_refs",
        "modality_refs",
        "polarity_refs",
        "scope_refs",
    ),
    ForegroundScopeObjectCompatibilityRow: (
        "owner_refs",
        "world_refs",
        "epistemic_state_refs",
        "time_refs",
        "aspect_refs",
        "modality_refs",
        "polarity_refs",
        "scope_refs",
        "required_qualifier_refs",
        "material_unknown_refs",
    ),
    ForegroundScope: (
        "integrated_scope_object_refs",
        "basis_row_refs",
        "source_connected_relation_refs",
        "required_retention_duty_refs",
        "material_unknown_refs",
        "required_qualifier_refs",
        "source_evidence_refs",
    ),
    ForegroundScopeDerivation: (
        "retained_foreground_source_object_refs",
        "unresolved_scope_refs",
        "missing_structure_refs",
        "derivation_evidence_refs",
    ),
    MeaningComponentSemanticKey: (),
    MeaningSemanticSignature: (
        "input_center_keys",
        "component_role_keys",
        "relation_direction_keys",
        "epistemic_state_keys",
        "temporal_state_keys",
        "resolution_treatment_keys",
        "world_or_owner_distinction_keys",
        "modality_polarity_or_limitation_keys",
        "episodicity_boundary_keys",
        "qualifier_keys",
        "component_semantic_keys",
    ),
    WholeReadingConsequenceValidationContext: ("source_evidence_refs",),
    WholeReadingConsequenceRow: ("source_evidence_refs",),
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
    SubjectiveBasisBinding: (),
    SourceQualifierBinding: ("canonical_qualifier_codes",),
    PolicyBasisBinding: (),
    SubjectiveResponsibilityRow: (
        "owner_component_refs",
        "retained_reception_act_refs",
    ),
    SubjectiveOpportunityRow: ("responsibility_refs",),
    SubjectiveFacetSuppressionRow: (),
    PolicyApplicationRow: ("policy_basis_binding_refs",),
    EmlisAffectContent: ("elicitor_bindings",),
    EmlisAppraisalContent: (
        "appraised_bindings",
        "protected_bindings",
        "basis_contribution_refs",
    ),
    ValueApplication: (
        "policy_application_row_refs",
        "policy_basis_binding_refs",
        "protected_subjective_binding_refs",
    ),
    MaterialValueContent: (
        "value_applications",
        "target_bindings",
        "boundary_bindings",
    ),
    EmlisRelationalPosition: ("target_bindings", "boundary_bindings"),
    SubjectivePropositionV2: (
        "target_contribution_refs",
        "primary_target_refs",
        "boundary_target_refs",
        "response_object_refs",
        "basis_binding_refs",
        "source_qualifier_binding_refs",
        "referenced_actor_refs",
        "referenced_experiencer_refs",
    ),
    SurfaceDerivation: (
        "source_or_claim_refs",
        "relation_or_clause_plan_refs",
        "qualifier_refs",
        "evidence_refs",
        "input_scalar_ranges",
    ),
    EmlisSubjectiveClaim: (
        "basis_observation_contribution_refs",
        "basis_semantic_refs",
        "source_reception_act_refs",
        "value_principle_refs",
        "forbidden_promotions",
        "subjective_responsibility_refs",
    ),
    EmlisStage1Projection: (
        "interpretation_candidates",
        "observation_contributions",
        "subjective_claims",
        "ordered_observation_refs",
        "ordered_subjective_refs",
        "retained_reception_act_ids",
        "subjective_responsibility_rows",
        "subjective_opportunity_rows",
        "subjective_facet_suppression_rows",
        "subjective_basis_binding_rows",
        "source_qualifier_binding_rows",
        "policy_basis_binding_rows",
        "policy_application_rows",
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
    Stage1V2UnitSeal: (
        "covered_duty_refs",
        "sentence_job_refs",
        "source_reception_act_refs",
    ),
    RealizationCandidateSet: ("candidates",),
    EmlisStage1PositiveTraceExtension: (
        "contribution_refs",
        "basis_trace_refs",
        "interpretation_candidate_refs",
        "basis_observation_contribution_refs",
        "value_principle_refs",
        "subjective_claim_refs",
        "covered_duty_refs",
        "sentence_job_refs",
        "source_reception_act_refs",
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


def validate_stage1_final_logical_id_registry() -> None:
    """Validate the sole disabled registry frozen by correction Step 1."""

    rows = CMEE_STAGE1_FINAL_LOGICAL_ID_REGISTRY
    if (
        type(rows) is not tuple
        or len(rows) != 28
        or any(
            type(row) is not tuple
            or len(row) != 2
            or type(row[0]) is not str
            or not row[0]
            or type(row[1]) is not str
            or not row[1]
            for row in rows
        )
    ):
        raise CMEEStage1ContractError(
            "stage1_final_logical_id_registry_invalid"
        )
    names = tuple(row[0] for row in rows)
    values = tuple(row[1] for row in rows)
    if len(names) != len(set(names)) or len(values) != len(set(values)):
        raise CMEEStage1ContractError(
            "stage1_final_logical_id_registry_invalid"
        )
    response_version = _stage1_final_logical_identity(
        "CMEE_STAGE1_RESPONSE_SCHEMA_VERSION"
    )
    if _stage1_final_logical_identity("CMEE_STAGE1_EMLIS_OWNER_REF") != (
        f"owner:emlis@{response_version}"
    ):
        raise CMEEStage1ContractError(
            "stage1_final_logical_id_registry_invalid"
        )


def _stage1_final_logical_identity(name: str) -> str:
    matches = tuple(
        value
        for registered_name, value in CMEE_STAGE1_FINAL_LOGICAL_ID_REGISTRY
        if registered_name == name
    )
    if len(matches) != 1:
        raise CMEEStage1ContractError(
            "stage1_final_logical_id_registry_invalid"
        )
    return matches[0]


def _stage1_final_typed_identity(
    logical_version_name: str,
    identity_prefix: str,
    material: tuple[Any, ...],
) -> str:
    if (
        type(identity_prefix) is not str
        or not identity_prefix
        or type(material) is not tuple
    ):
        raise CMEEStage1ContractError("stage1_final_identity_input_invalid")
    version = _stage1_final_logical_identity(logical_version_name)
    digest = hashlib.sha256(
        version.encode("utf-8")
        + b"\0"
        + stage1_canonical_json_bytes(material)
    ).hexdigest()
    return f"{identity_prefix}-{digest}"


def _stage1_identity_string(value: object) -> bool:
    return type(value) is str and bool(value) and not any(
        char.isspace() for char in value
    )


def _stage1_exact_string_tuple(
    value: object,
    *,
    allow_empty: bool,
) -> tuple[str, ...]:
    if (
        type(value) is not tuple
        or (not allow_empty and not value)
        or any(not _stage1_identity_string(row) for row in value)
        or len(value) != len(set(value))
    ):
        raise CMEEStage1ContractError("stage1_subjective_v2_cross_owner_invalid")
    return value


def _stage1_first_occurrence_union(*rows: Sequence[str]) -> tuple[str, ...]:
    result: list[str] = []
    seen: set[str] = set()
    for group in rows:
        for value in group:
            if value not in seen:
                seen.add(value)
                result.append(value)
    return tuple(result)


def _stage1_subjective_content_binding_tuple(
    value: object,
    *,
    allow_empty: bool,
) -> tuple[str, ...]:
    try:
        return _stage1_exact_string_tuple(value, allow_empty=allow_empty)
    except CMEEStage1ContractError:
        raise CMEEStage1ContractError("GENERIC_SUBJECTIVE_CONTENT_STOP") from None


def project_stage1_projection_preimage_ref(
    *,
    grounded_graph_ref: str,
    parent_observation_duty_ref: str,
    parent_reception_duty_ref: str,
    interpretation_candidate_ids: Tuple[str, ...],
    meaning_field_id: str,
    observation_contribution_ids: Tuple[str, ...],
    retained_reception_act_ids: Tuple[str, ...],
    observation_depth_class: ObservationDepthClass,
    temperature_class: TemperatureClass,
    reception_style_policy_ref: str,
    emlis_value_policy_ref: str,
) -> str:
    scalar_values = (
        grounded_graph_ref,
        parent_observation_duty_ref,
        parent_reception_duty_ref,
        meaning_field_id,
        reception_style_policy_ref,
        emlis_value_policy_ref,
    )
    if any(not _stage1_identity_string(value) for value in scalar_values):
        raise CMEEStage1ContractError("stage1_projection_preimage_invalid")
    for values in (
        interpretation_candidate_ids,
        observation_contribution_ids,
        retained_reception_act_ids,
    ):
        try:
            _stage1_exact_string_tuple(values, allow_empty=False)
        except CMEEStage1ContractError:
            raise CMEEStage1ContractError(
                "stage1_projection_preimage_invalid"
            ) from None
    if (
        type(observation_depth_class) is not ObservationDepthClass
        or type(temperature_class) is not TemperatureClass
    ):
        raise CMEEStage1ContractError("stage1_projection_preimage_invalid")
    return _stage1_final_typed_identity(
        "CMEE_STAGE1_PROJECTION_PREIMAGE_REF_VERSION",
        "projection-preimage",
        (
            grounded_graph_ref,
            parent_observation_duty_ref,
            parent_reception_duty_ref,
            interpretation_candidate_ids,
            meaning_field_id,
            observation_contribution_ids,
            retained_reception_act_ids,
            observation_depth_class,
            temperature_class,
            reception_style_policy_ref,
            emlis_value_policy_ref,
            _stage1_final_logical_identity(
                "CMEE_STAGE1_RESPONSE_SCHEMA_VERSION"
            ),
            _stage1_final_logical_identity(
                "CMEE_STAGE1_COMPOSITION_POLICY_VERSION"
            ),
        ),
    )


def project_stage1_subjective_basis_binding_ref(
    *,
    projection_preimage_ref: str,
    contribution_ref: str,
    semantic_ref: str,
    role: SubjectiveBasisRole,
) -> str:
    if (
        any(
            not _stage1_identity_string(value)
            for value in (
                projection_preimage_ref,
                contribution_ref,
                semantic_ref,
            )
        )
        or type(role) is not SubjectiveBasisRole
    ):
        raise CMEEStage1ContractError("stage1_subjective_basis_binding_invalid")
    return _stage1_final_typed_identity(
        "CMEE_STAGE1_SUBJECTIVE_BASIS_BINDING_REF_VERSION",
        "subjective-basis-binding",
        (projection_preimage_ref, contribution_ref, semantic_ref, role),
    )


def project_stage1_source_qualifier_binding_ref(
    *,
    projection_preimage_ref: str,
    basis_binding_ref: str,
    source_candidate_ref: str,
    source_argument_role: Optional[ArgumentRole],
    canonical_qualifier_codes: Tuple[str, ...],
    polarity: str,
    modality: str,
    time_scope: str,
) -> str:
    scalar_values = (
        projection_preimage_ref,
        basis_binding_ref,
        source_candidate_ref,
        polarity,
        modality,
        time_scope,
    )
    if (
        any(not _stage1_identity_string(value) for value in scalar_values)
        or (
            source_argument_role is not None
            and type(source_argument_role) is not ArgumentRole
        )
        or type(canonical_qualifier_codes) is not tuple
        or len(canonical_qualifier_codes) != 3
        or any(
            not _stage1_identity_string(value)
            for value in canonical_qualifier_codes
        )
        or len(set(canonical_qualifier_codes)) != 3
    ):
        raise CMEEStage1ContractError("stage1_source_qualifier_binding_invalid")
    role_prefix = (
        ""
        if source_argument_role is None
        else f"{source_argument_role.value.lower()}_"
    )
    expected_qualifier_codes = (
        f"{role_prefix}polarity:{polarity}",
        f"{role_prefix}modality:{modality}",
        f"{role_prefix}time_scope:{time_scope}",
    )
    if canonical_qualifier_codes != expected_qualifier_codes:
        raise CMEEStage1ContractError("stage1_source_qualifier_binding_invalid")
    return _stage1_final_typed_identity(
        "CMEE_STAGE1_SOURCE_QUALIFIER_BINDING_REF_VERSION",
        "source-qualifier-binding",
        (
            projection_preimage_ref,
            basis_binding_ref,
            source_candidate_ref,
            source_argument_role,
            canonical_qualifier_codes,
            polarity,
            modality,
            time_scope,
        ),
    )


def project_stage1_policy_basis_binding_ref(
    *,
    projection_preimage_ref: str,
    owner_kind: PolicyBasisOwnerKind,
    owner_ref: str,
    role: PolicyBasisRole,
) -> str:
    if (
        not _stage1_identity_string(projection_preimage_ref)
        or type(owner_kind) is not PolicyBasisOwnerKind
        or not _stage1_identity_string(owner_ref)
        or type(role) is not PolicyBasisRole
    ):
        raise CMEEStage1ContractError("stage1_policy_basis_binding_invalid")
    return _stage1_final_typed_identity(
        "CMEE_STAGE1_POLICY_BASIS_BINDING_REF_VERSION",
        "policy-basis-binding",
        (projection_preimage_ref, owner_kind, owner_ref, role),
    )


def project_stage1_subjective_responsibility_ref(
    *,
    projection_preimage_ref: str,
    responsibility_kind: SubjectiveResponsibilityKind,
    owner_component_refs: Tuple[str, ...],
    retained_reception_act_refs: Tuple[str, ...],
) -> str:
    if (
        not _stage1_identity_string(projection_preimage_ref)
        or type(responsibility_kind) is not SubjectiveResponsibilityKind
    ):
        raise CMEEStage1ContractError(
            "stage1_subjective_responsibility_invalid"
        )
    try:
        _stage1_exact_string_tuple(owner_component_refs, allow_empty=False)
        _stage1_exact_string_tuple(
            retained_reception_act_refs,
            allow_empty=False,
        )
    except CMEEStage1ContractError:
        raise CMEEStage1ContractError(
            "stage1_subjective_responsibility_invalid"
        ) from None
    return _stage1_final_typed_identity(
        "CMEE_STAGE1_SUBJECTIVE_RESPONSIBILITY_REF_VERSION",
        "subjective-responsibility",
        (
            projection_preimage_ref,
            responsibility_kind,
            owner_component_refs,
            retained_reception_act_refs,
        ),
    )


def project_stage1_subjective_opportunity_key(
    *,
    projection_preimage_ref: str,
    responsibility_refs: Tuple[str, ...],
    content_kind: SubjectiveContentKind,
    row_ref_free_discriminated_content: object,
    specificity_key: SubjectiveSpecificity,
) -> str:
    if (
        not _stage1_identity_string(projection_preimage_ref)
        or type(content_kind) is not SubjectiveContentKind
        or type(specificity_key) is not SubjectiveSpecificity
        or not is_dataclass(row_ref_free_discriminated_content)
    ):
        raise CMEEStage1ContractError("stage1_subjective_opportunity_invalid")
    try:
        _stage1_exact_string_tuple(responsibility_refs, allow_empty=False)
        stage1_canonical_json_bytes(row_ref_free_discriminated_content)
    except CMEEStage1ContractError:
        raise CMEEStage1ContractError(
            "stage1_subjective_opportunity_invalid"
        ) from None
    return _stage1_final_typed_identity(
        "CMEE_STAGE1_SUBJECTIVE_OPPORTUNITY_KEY_VERSION",
        "subjective-opportunity",
        (
            projection_preimage_ref,
            responsibility_refs,
            content_kind,
            row_ref_free_discriminated_content,
            specificity_key,
        ),
    )


_STAGE1_APPRAISAL_DERIVATION_EXACT5 = (
    (AppraisalDimension.MATERIAL_WEIGHT, AppraisalOperation.RECEIVE_AS_MATERIAL),
    (
        AppraisalDimension.RELATIONAL_NONCOLLAPSE,
        AppraisalOperation.PRESERVE_BOTH_ENDPOINTS,
    ),
    (
        AppraisalDimension.BOUNDED_CHANGE,
        AppraisalOperation.RECOGNIZE_AS_BOUNDED,
    ),
    (
        AppraisalDimension.UNFINISHED_OPENNESS,
        AppraisalOperation.LEAVE_UNFINISHED,
    ),
    (AppraisalDimension.AGENCY_BOUNDARY, AppraisalOperation.RESPECT_CHOICE),
)
_STAGE1_VALUE_RISK_DERIVATION_EXACT9 = tuple(
    (principle_ref, risk)
    for (_code, principle_ref), risk in zip(
        CMEE_STAGE1_VALUE_PRINCIPLE_REFS,
        (
            MaterialRisk.MINIMIZATION,
            MaterialRisk.WISH_TO_OBLIGATION,
            MaterialRisk.NO_RESULT_TO_NO_VALUE,
            MaterialRisk.SINGLE_EVENT_TO_IDENTITY,
            MaterialRisk.BOUNDED_CHANGE_TO_UNIVERSAL_SOLUTION,
            MaterialRisk.ONE_SIDE_TO_TRUE_SELF,
            MaterialRisk.POSSIBILITY_TO_FACT,
            MaterialRisk.REMOVE_USER_AGENCY,
            MaterialRisk.UNKNOWN_TO_FALSE_UNDERSTANDING,
        ),
        strict=True,
    )
)
_STAGE1_VALUE_VISIBLE_PRINCIPLE_REFS = tuple(
    dict(CMEE_STAGE1_VALUE_PRINCIPLE_REFS)[code]
    for code in ("V1", "V2", "V8")
)


def _stage1_subjective_v2_content_bindings(
    proposition: SubjectivePropositionV2,
) -> tuple[tuple[str, ...], tuple[str, ...], Optional[str]]:
    if proposition.content_kind is SubjectiveContentKind.AFFECT:
        content = proposition.affect_content
        if (
            type(content) is not EmlisAffectContent
            or type(content.category) is not AffectCategory
            or type(content.intensity) is not AffectIntensity
        ):
            raise CMEEStage1ContractError(
                "stage1_subjective_v2_derived_field_invalid"
            )
        bindings = _stage1_subjective_content_binding_tuple(
            content.elicitor_bindings,
            allow_empty=False,
        )
        return bindings, (), None
    if proposition.content_kind is SubjectiveContentKind.APPRAISAL:
        content = proposition.appraisal_content
        if (
            type(content) is not EmlisAppraisalContent
            or type(content.dimension) is not AppraisalDimension
            or type(content.operation) is not AppraisalOperation
            or (content.dimension, content.operation)
            not in _STAGE1_APPRAISAL_DERIVATION_EXACT5
        ):
            raise CMEEStage1ContractError(
                "stage1_subjective_v2_derived_field_invalid"
            )
        if (
            content.dimension is AppraisalDimension.RELATIONAL_NONCOLLAPSE
            and content.focal_relation_ref is None
        ):
            raise CMEEStage1ContractError(
                "stage1_subjective_v2_focal_relation_invalid"
            )
        primary = _stage1_subjective_content_binding_tuple(
            content.appraised_bindings,
            allow_empty=False,
        )
        protected = _stage1_subjective_content_binding_tuple(
            content.protected_bindings,
            allow_empty=True,
        )
        _stage1_exact_string_tuple(
            content.basis_contribution_refs,
            allow_empty=False,
        )
        boundary = tuple(value for value in protected if value not in set(primary))
        return primary, boundary, content.focal_relation_ref
    if proposition.content_kind is SubjectiveContentKind.MATERIAL_VALUE:
        content = proposition.material_value_content
        if type(content) is not MaterialValueContent:
            raise CMEEStage1ContractError(
                "stage1_subjective_v2_content_discriminant_invalid"
            )
        if not content.value_applications:
            raise CMEEStage1ContractError("GENERIC_SUBJECTIVE_CONTENT_STOP")
        primary = _stage1_subjective_content_binding_tuple(
            content.target_bindings,
            allow_empty=False,
        )
        if type(content.boundary_bindings) is not tuple or content.boundary_bindings:
            raise CMEEStage1ContractError("stage1_subjective_v2_target_projection_invalid")
        principle_order = tuple(ref for _code, ref in CMEE_STAGE1_VALUE_PRINCIPLE_REFS)
        application_principles: list[str] = []
        protected_rows: list[tuple[str, ...]] = []
        if type(content.value_applications) is not tuple:
            raise CMEEStage1ContractError("stage1_subjective_v2_content_discriminant_invalid")
        for application in content.value_applications:
            if (
                type(application) is not ValueApplication
                or application.principle_ref not in principle_order
                or application.principle_ref
                not in _STAGE1_VALUE_VISIBLE_PRINCIPLE_REFS
                or type(application.material_risk) is not MaterialRisk
                or (application.principle_ref, application.material_risk)
                not in _STAGE1_VALUE_RISK_DERIVATION_EXACT9
            ):
                raise CMEEStage1ContractError(
                    "stage1_subjective_v2_cross_owner_invalid"
                )
            _stage1_exact_string_tuple(
                application.policy_application_row_refs,
                allow_empty=False,
            )
            _stage1_exact_string_tuple(
                application.policy_basis_binding_refs,
                allow_empty=False,
            )
            protected_rows.append(
                _stage1_exact_string_tuple(
                    application.protected_subjective_binding_refs,
                    allow_empty=False,
                )
            )
            application_principles.append(application.principle_ref)
        if (
            len(application_principles) != len(set(application_principles))
            or tuple(application_principles)
            != tuple(
                ref for ref in principle_order if ref in set(application_principles)
            )
            or _stage1_first_occurrence_union(*protected_rows) != primary
        ):
            raise CMEEStage1ContractError("stage1_subjective_v2_cross_owner_invalid")
        return primary, (), proposition.focal_relation_ref
    if proposition.content_kind is SubjectiveContentKind.RELATIONAL_POSITION:
        content = proposition.relational_position
        if (
            type(content) is not EmlisRelationalPosition
            or type(content.relational_position_kind) is not RelationalPositionKind
            or type(content.stance_operator) is not StanceOperator
            or type(content.commitment) is not RelationalCommitment
            or type(content.closure) is not RelationalClosure
        ):
            raise CMEEStage1ContractError(
                "stage1_subjective_v2_derived_field_invalid"
            )
        primary = _stage1_subjective_content_binding_tuple(
            content.target_bindings,
            allow_empty=False,
        )
        boundary = _stage1_subjective_content_binding_tuple(
            content.boundary_bindings,
            allow_empty=(
                content.relational_position_kind is RelationalPositionKind.STANCE
            ),
        )
        is_counter = (
            content.relational_position_kind
            is RelationalPositionKind.BOUNDED_COUNTERPOSITION
        )
        if (
            is_counter != (content.commitment is RelationalCommitment.DECLINE_PROMOTION)
            or (is_counter and not boundary)
            or (not is_counter and boundary)
        ):
            raise CMEEStage1ContractError("stage1_subjective_v2_derived_field_invalid")
        return primary, boundary, proposition.focal_relation_ref
    raise CMEEStage1ContractError("stage1_subjective_v2_content_discriminant_invalid")


def validate_subjective_proposition_v2(
    proposition: SubjectivePropositionV2,
    *,
    projection_preimage_ref: str,
    basis_rows: Tuple[SubjectiveBasisBinding, ...],
    qualifier_rows: Tuple[SourceQualifierBinding, ...],
    expected_basis_rows: Tuple[SubjectiveBasisBinding, ...],
    expected_qualifier_rows: Tuple[SourceQualifierBinding, ...],
    policy_basis_rows: Tuple[PolicyBasisBinding, ...],
    expected_policy_basis_rows: Tuple[PolicyBasisBinding, ...],
    allowed_contribution_refs: Tuple[str, ...],
    allowed_semantic_refs: Tuple[str, ...],
    allowed_source_candidate_refs: Tuple[str, ...],
    allowed_policy_application_row_refs: Tuple[str, ...],
    admitted_relation_refs: Tuple[str, ...],
    material_unknown_refs: Tuple[str, ...],
    expected_actor_refs: Tuple[str, ...],
    expected_experiencer_refs: Tuple[str, ...],
    expected_focal_relation_ref: Optional[str],
    owner_ref: str,
    speaker_owner: str,
    user_fact_effect: int,
    forbidden_promotions: Tuple[str, ...],
    expected_forbidden_promotions: Tuple[str, ...],
) -> None:
    """Validate the disabled final proposition and its minimum lineage spine.

    Every ``expected_*`` and ``allowed_*`` argument is a mandatory frozen
    phase-A authority output, never a caller-selected alternative.  Step 1
    registers this unwired seam; the Step 2 sole projector must supply all of
    these arguments from one phase-A snapshot before runtime use exists.
    """

    if type(proposition) is not SubjectivePropositionV2:
        raise CMEEStage1ContractError("stage1_subjective_v2_type_invalid")
    _validate_stage1_immutable_shape(proposition)
    final_schema = _stage1_final_logical_identity(
        "CMEE_STAGE1_SUBJECTIVE_PROPOSITION_SCHEMA_VERSION"
    )
    if proposition.schema_version != final_schema:
        raise CMEEStage1ContractError("stage1_subjective_v2_schema_invalid")
    contents = (
        proposition.affect_content,
        proposition.appraisal_content,
        proposition.material_value_content,
        proposition.relational_position,
    )
    content_types = (
        EmlisAffectContent,
        EmlisAppraisalContent,
        MaterialValueContent,
        EmlisRelationalPosition,
    )
    expected_content_index = tuple(SubjectiveContentKind).index(
        proposition.content_kind
    ) if type(proposition.content_kind) is SubjectiveContentKind else -1
    if (
        expected_content_index < 0
        or sum(value is not None for value in contents) != 1
        or type(contents[expected_content_index]) is not content_types[expected_content_index]
    ):
        raise CMEEStage1ContractError(
            "stage1_subjective_v2_content_discriminant_invalid"
        )

    relational_kind = (
        proposition.relational_position.relational_position_kind
        if proposition.relational_position is not None
        else None
    )
    derived = {
        SubjectiveContentKind.AFFECT: (
            SubjectiveMode.AFFECTIVE_RESPONSE,
            SubjectiveOperator.FEEL_TOWARD,
            SubjectiveAssertionModality.EMLIS_FEELING,
        ),
        SubjectiveContentKind.APPRAISAL: (
            SubjectiveMode.PERSONAL_APPRAISAL,
            SubjectiveOperator.APPRAISE_AS_MATERIAL,
            SubjectiveAssertionModality.EMLIS_APPRAISAL,
        ),
        SubjectiveContentKind.MATERIAL_VALUE: (
            SubjectiveMode.VALUE_POSITION,
            SubjectiveOperator.PROTECT_VALUE_BOUNDARY,
            SubjectiveAssertionModality.EMLIS_VALUE_POSITION,
        ),
    }.get(proposition.content_kind)
    if proposition.content_kind is SubjectiveContentKind.RELATIONAL_POSITION:
        derived = (
            (
                SubjectiveMode.BOUNDED_COUNTERPOSITION,
                SubjectiveOperator.COUNTER_SPECIFIC_PROMOTION,
                SubjectiveAssertionModality.EMLIS_BOUNDED_REFUSAL,
            )
            if relational_kind is RelationalPositionKind.BOUNDED_COUNTERPOSITION
            else (
                SubjectiveMode.RELATIONAL_STANCE,
                SubjectiveOperator.TAKE_RELATIONAL_STANCE,
                SubjectiveAssertionModality.EMLIS_RELATIONAL_INTENTION,
            )
        )
    if derived is None or (
        proposition.subjective_mode,
        proposition.subjective_operator,
        proposition.assertion_modality,
    ) != derived:
        raise CMEEStage1ContractError("stage1_subjective_v2_derived_field_invalid")
    if (
        proposition.addressee_role != "USER"
        or proposition.epistemic_scope != "REQUEST_LOCAL_EMLIS_SUBJECTIVITY"
        or owner_ref
        != _stage1_final_logical_identity("CMEE_STAGE1_EMLIS_OWNER_REF")
        or speaker_owner != "EMLIS"
        or type(user_fact_effect) is not int
        or user_fact_effect != 0
    ):
        raise CMEEStage1ContractError("stage1_subjective_v2_cross_owner_invalid")
    _stage1_exact_string_tuple(forbidden_promotions, allow_empty=False)
    _stage1_exact_string_tuple(expected_forbidden_promotions, allow_empty=False)
    generic_prefix_length = len(CMEE_STAGE1_SUBJECTIVE_FORBIDDEN_PROMOTIONS)
    suppression_suffix = forbidden_promotions[generic_prefix_length:]
    canonical_suppression_codes = tuple(
        f"value-policy-suppression:{code}"
        for code, _ref in CMEE_STAGE1_VALUE_PRINCIPLE_REFS
    )
    if (
        forbidden_promotions[:generic_prefix_length]
        != CMEE_STAGE1_SUBJECTIVE_FORBIDDEN_PROMOTIONS
        or forbidden_promotions != expected_forbidden_promotions
        or suppression_suffix
        != tuple(
            code
            for code in canonical_suppression_codes
            if code in set(suppression_suffix)
        )
    ):
        raise CMEEStage1ContractError("stage1_subjective_v2_cross_owner_invalid")

    for values, allow_empty in (
        (allowed_contribution_refs, False),
        (allowed_semantic_refs, False),
        (allowed_source_candidate_refs, False),
        (allowed_policy_application_row_refs, True),
        (admitted_relation_refs, True),
        (material_unknown_refs, True),
        (expected_actor_refs, True),
        (expected_experiencer_refs, True),
    ):
        _stage1_exact_string_tuple(values, allow_empty=allow_empty)
    if not _stage1_identity_string(projection_preimage_ref):
        raise CMEEStage1ContractError("stage1_subjective_v2_cross_owner_invalid")
    if (
        type(basis_rows) is not tuple
        or any(type(row) is not SubjectiveBasisBinding for row in basis_rows)
        or type(qualifier_rows) is not tuple
        or any(type(row) is not SourceQualifierBinding for row in qualifier_rows)
        or type(expected_basis_rows) is not tuple
        or any(type(row) is not SubjectiveBasisBinding for row in expected_basis_rows)
        or type(expected_qualifier_rows) is not tuple
        or any(
            type(row) is not SourceQualifierBinding
            for row in expected_qualifier_rows
        )
        or type(policy_basis_rows) is not tuple
        or any(type(row) is not PolicyBasisBinding for row in policy_basis_rows)
        or type(expected_policy_basis_rows) is not tuple
        or any(
            type(row) is not PolicyBasisBinding
            for row in expected_policy_basis_rows
        )
    ):
        raise CMEEStage1ContractError("stage1_subjective_v2_cross_owner_invalid")
    if not basis_rows or not expected_basis_rows:
        raise CMEEStage1ContractError(
            "stage1_subjective_v2_basis_exact_cover_invalid"
        )
    if not qualifier_rows or not expected_qualifier_rows:
        raise CMEEStage1ContractError(
            "stage1_subjective_v2_qualifier_exact_cover_invalid"
        )
    if basis_rows != expected_basis_rows:
        raise CMEEStage1ContractError(
            "stage1_subjective_v2_basis_exact_cover_invalid"
        )
    if qualifier_rows != expected_qualifier_rows:
        raise CMEEStage1ContractError(
            "stage1_subjective_v2_qualifier_exact_cover_invalid"
        )
    if policy_basis_rows != expected_policy_basis_rows:
        raise CMEEStage1ContractError("stage1_policy_basis_binding_invalid")

    basis_by_ref: dict[str, SubjectiveBasisBinding] = {}
    for row in basis_rows:
        if (
            row.projection_preimage_ref != projection_preimage_ref
            or row.contribution_ref not in set(allowed_contribution_refs)
            or row.semantic_ref not in set(allowed_semantic_refs)
            or row.binding_ref
            != project_stage1_subjective_basis_binding_ref(
                projection_preimage_ref=row.projection_preimage_ref,
                contribution_ref=row.contribution_ref,
                semantic_ref=row.semantic_ref,
                role=row.role,
            )
            or row.binding_ref in basis_by_ref
        ):
            raise CMEEStage1ContractError(
                "stage1_subjective_v2_basis_exact_cover_invalid"
            )
        if (
            row.contribution_ref in set(material_unknown_refs)
            or row.semantic_ref in set(material_unknown_refs)
        ):
            raise CMEEStage1ContractError(
                "stage1_material_unknown_promotion_invalid"
            )
        basis_by_ref[row.binding_ref] = row

    qualifier_by_basis: dict[str, SourceQualifierBinding] = {}
    qualifier_ref_seen: set[str] = set()
    for row in qualifier_rows:
        if (
            row.projection_preimage_ref != projection_preimage_ref
            or row.basis_binding_ref not in basis_by_ref
            or row.source_candidate_ref not in set(allowed_source_candidate_refs)
            or row.source_qualifier_binding_ref
            != project_stage1_source_qualifier_binding_ref(
                projection_preimage_ref=row.projection_preimage_ref,
                basis_binding_ref=row.basis_binding_ref,
                source_candidate_ref=row.source_candidate_ref,
                source_argument_role=row.source_argument_role,
                canonical_qualifier_codes=row.canonical_qualifier_codes,
                polarity=row.polarity,
                modality=row.modality,
                time_scope=row.time_scope,
            )
            or row.basis_binding_ref in qualifier_by_basis
            or row.source_qualifier_binding_ref in qualifier_ref_seen
        ):
            raise CMEEStage1ContractError(
                "stage1_subjective_v2_qualifier_exact_cover_invalid"
            )
        qualifier_by_basis[row.basis_binding_ref] = row
        qualifier_ref_seen.add(row.source_qualifier_binding_ref)

    material_unknown_owner_refs: list[str] = []
    policy_by_ref: dict[str, PolicyBasisBinding] = {}
    for row in policy_basis_rows:
        if (
            row.projection_preimage_ref != projection_preimage_ref
            or row.binding_ref
            != project_stage1_policy_basis_binding_ref(
                projection_preimage_ref=row.projection_preimage_ref,
                owner_kind=row.owner_kind,
                owner_ref=row.owner_ref,
                role=row.role,
            )
            or row.binding_ref in policy_by_ref
        ):
            raise CMEEStage1ContractError("stage1_policy_basis_binding_invalid")
        policy_by_ref[row.binding_ref] = row
        if row.owner_kind is PolicyBasisOwnerKind.MATERIAL_UNKNOWN:
            if (
                row.role is not PolicyBasisRole.MATERIAL_UNKNOWN
                or row.owner_ref not in set(material_unknown_refs)
            ):
                raise CMEEStage1ContractError(
                    "stage1_material_unknown_promotion_invalid"
                )
            material_unknown_owner_refs.append(row.owner_ref)
        elif (
            row.role is PolicyBasisRole.MATERIAL_UNKNOWN
            or row.owner_ref not in set(allowed_contribution_refs)
        ):
            raise CMEEStage1ContractError("stage1_policy_basis_binding_invalid")
    if len(material_unknown_owner_refs) != len(set(material_unknown_owner_refs)):
        raise CMEEStage1ContractError("stage1_material_unknown_promotion_invalid")

    primary_binding_refs, boundary_binding_refs, nested_focal_relation_ref = (
        _stage1_subjective_v2_content_bindings(proposition)
    )
    if proposition.material_value_content is not None:
        policy_application_ref_seen: set[str] = set()
        for application in proposition.material_value_content.value_applications:
            if (
                any(
                    ref not in policy_by_ref
                    or policy_by_ref[ref].owner_kind
                    is not PolicyBasisOwnerKind.CONTRIBUTION
                    for ref in application.policy_basis_binding_refs
                )
                or any(
                    ref not in set(allowed_policy_application_row_refs)
                    for ref in application.policy_application_row_refs
                )
                or any(
                    ref not in basis_by_ref
                    for ref in application.protected_subjective_binding_refs
                )
                or any(
                    ref in policy_application_ref_seen
                    for ref in application.policy_application_row_refs
                )
            ):
                raise CMEEStage1ContractError(
                    "stage1_subjective_v2_cross_owner_invalid"
                )
            policy_application_ref_seen.update(
                application.policy_application_row_refs
            )
    if (
        proposition.relational_position is not None
        and proposition.relational_position.relational_position_kind
        is RelationalPositionKind.BOUNDED_COUNTERPOSITION
        and proposition.focal_relation_ref is None
    ):
        raise CMEEStage1ContractError(
            "stage1_subjective_v2_focal_relation_invalid"
        )
    all_content_binding_refs = _stage1_first_occurrence_union(
        primary_binding_refs,
        boundary_binding_refs,
    )
    if (
        set(primary_binding_refs).intersection(boundary_binding_refs)
        or any(ref not in basis_by_ref for ref in all_content_binding_refs)
        or proposition.basis_binding_refs != all_content_binding_refs
        or tuple(row.binding_ref for row in basis_rows) != all_content_binding_refs
    ):
        raise CMEEStage1ContractError(
            "stage1_subjective_v2_basis_exact_cover_invalid"
        )
    expected_qualifier_refs = tuple(
        qualifier_by_basis[ref].source_qualifier_binding_ref
        for ref in all_content_binding_refs
        if ref in qualifier_by_basis
    )
    if (
        len(qualifier_by_basis) != len(all_content_binding_refs)
        or proposition.source_qualifier_binding_refs != expected_qualifier_refs
        or tuple(row.source_qualifier_binding_ref for row in qualifier_rows)
        != expected_qualifier_refs
    ):
        raise CMEEStage1ContractError(
            "stage1_subjective_v2_qualifier_exact_cover_invalid"
        )
    expected_primary_refs = _stage1_first_occurrence_union(
        tuple(basis_by_ref[ref].semantic_ref for ref in primary_binding_refs)
    )
    expected_boundary_refs = _stage1_first_occurrence_union(
        tuple(basis_by_ref[ref].semantic_ref for ref in boundary_binding_refs)
    )
    expected_contribution_refs = _stage1_first_occurrence_union(
        tuple(
            basis_by_ref[ref].contribution_ref
            for ref in all_content_binding_refs
        )
    )
    if (
        not set(expected_primary_refs).isdisjoint(expected_boundary_refs)
        or len(proposition.response_object_refs)
        != len(set(proposition.response_object_refs))
        or proposition.primary_target_refs != expected_primary_refs
        or proposition.boundary_target_refs != expected_boundary_refs
        or proposition.response_object_refs
        != (*expected_primary_refs, *expected_boundary_refs)
        or proposition.target_contribution_refs != expected_contribution_refs
    ):
        raise CMEEStage1ContractError(
            "stage1_subjective_v2_target_projection_invalid"
        )
    if proposition.content_kind is SubjectiveContentKind.APPRAISAL:
        content = proposition.appraisal_content
        if content is None or content.basis_contribution_refs != expected_contribution_refs:
            raise CMEEStage1ContractError(
                "stage1_subjective_v2_target_projection_invalid"
            )
    if (
        proposition.focal_relation_ref != nested_focal_relation_ref
        or proposition.focal_relation_ref != expected_focal_relation_ref
        or (
            proposition.focal_relation_ref is not None
            and proposition.focal_relation_ref not in set(admitted_relation_refs)
        )
    ):
        raise CMEEStage1ContractError(
            "stage1_subjective_v2_focal_relation_invalid"
        )
    if (
        proposition.referenced_actor_refs != expected_actor_refs
        or proposition.referenced_experiencer_refs != expected_experiencer_refs
    ):
        raise CMEEStage1ContractError("stage1_subjective_v2_cross_owner_invalid")


def validate_surface_derivation(
    derivation: SurfaceDerivation,
    *,
    registered_rule_refs_by_kind: Mapping[
        tuple[SurfaceDerivationKind, Optional[str]],
        Tuple[str, ...],
    ],
    response_object_mode: Optional[str] = None,
) -> None:
    """Validate the disabled exact8 derivation shape and frozen rule owner.

    The registered mapping is the request-local frozen rule snapshot.  Concrete
    source/evidence/span resolution belongs to the Step 2 projector and the
    Step 4 sealed-plan tamper gate; this Step 1 seam has no runtime caller.
    """

    if type(derivation) is not SurfaceDerivation:
        raise CMEEStage1ContractError("stage1_surface_derivation_type_invalid")
    _validate_stage1_immutable_shape(derivation)
    for values in (
        derivation.source_or_claim_refs,
        derivation.relation_or_clause_plan_refs,
        derivation.qualifier_refs,
        derivation.evidence_refs,
    ):
        _stage1_exact_string_tuple(values, allow_empty=True)
    expected_rule_keys = {
        *((kind, None) for kind in SurfaceDerivationKind if kind is not SurfaceDerivationKind.PROJECTED_RESPONSE_OBJECT),
        (SurfaceDerivationKind.PROJECTED_RESPONSE_OBJECT, "EXPLICIT"),
        (SurfaceDerivationKind.PROJECTED_RESPONSE_OBJECT, "COMPOSITE"),
        (SurfaceDerivationKind.PROJECTED_RESPONSE_OBJECT, "ANAPHORIC"),
    }
    if (
        not isinstance(registered_rule_refs_by_kind, Mapping)
        or set(registered_rule_refs_by_kind) != expected_rule_keys
    ):
        raise CMEEStage1ContractError("stage1_surface_derivation_rule_invalid")
    registered_rule_refs: list[str] = []
    for rule_refs in registered_rule_refs_by_kind.values():
        try:
            exact_rule_refs = _stage1_exact_string_tuple(
                rule_refs,
                allow_empty=False,
            )
            for rule_ref in exact_rule_refs:
                validate_version_qualified_ref(rule_ref, expected_types=("rule",))
        except CMEEStage1ContractError:
            raise CMEEStage1ContractError(
                "stage1_surface_derivation_rule_invalid"
            ) from None
        registered_rule_refs.extend(exact_rule_refs)
    if len(registered_rule_refs) != len(set(registered_rule_refs)):
        raise CMEEStage1ContractError("stage1_surface_derivation_rule_invalid")
    for value in (
        derivation.emlis_owner_ref,
        derivation.response_object_expression_ref,
        derivation.antecedent_unit_ref,
        derivation.participant_role_ref,
    ):
        if value is not None and not _stage1_identity_string(value):
            raise CMEEStage1ContractError(
                "stage1_surface_derivation_owner_invalid"
            )
    try:
        validate_version_qualified_ref(derivation.rule_ref, expected_types=("rule",))
    except CMEEStage1ContractError:
        raise CMEEStage1ContractError("stage1_surface_derivation_rule_invalid") from None
    rule_key = (
        derivation.derivation_kind,
        response_object_mode
        if derivation.derivation_kind
        is SurfaceDerivationKind.PROJECTED_RESPONSE_OBJECT
        else None,
    )
    if derivation.rule_ref not in set(
        registered_rule_refs_by_kind.get(rule_key, ())
    ):
        raise CMEEStage1ContractError("stage1_surface_derivation_rule_invalid")
    ranges = derivation.input_scalar_ranges
    if (
        type(ranges) is not tuple
        or any(
            type(row) is not tuple
            or len(row) != 2
            or type(row[0]) is not int
            or type(row[1]) is not int
            or isinstance(row[0], bool)
            or isinstance(row[1], bool)
            or row[0] < 0
            or row[1] <= row[0]
            for row in ranges
        )
        or tuple(sorted(ranges)) != ranges
        or len(ranges) != len(set(ranges))
        or any(
            left[1] > right[0]
            for left, right in zip(ranges, ranges[1:])
        )
    ):
        raise CMEEStage1ContractError("stage1_surface_derivation_range_invalid")

    source_count = len(derivation.source_or_claim_refs)
    relation_count = len(derivation.relation_or_clause_plan_refs)
    qualifier_count = len(derivation.qualifier_refs)
    evidence_count = len(derivation.evidence_refs)
    range_count = len(ranges)
    has_emlis = derivation.emlis_owner_ref is not None
    has_response = derivation.response_object_expression_ref is not None
    has_antecedent = derivation.antecedent_unit_ref is not None
    has_participant = derivation.participant_role_ref is not None
    kind = derivation.derivation_kind
    if type(kind) is not SurfaceDerivationKind:
        raise CMEEStage1ContractError("stage1_surface_derivation_type_invalid")
    common_other_owner = (
        relation_count
        or qualifier_count
        or has_emlis
        or has_response
        or has_antecedent
        or has_participant
    )
    if kind in {
        SurfaceDerivationKind.LITERAL_SUBSPAN,
        SurfaceDerivationKind.NORMALIZED_INFLECTION,
    }:
        valid = source_count >= 1 and not common_other_owner and evidence_count >= 1 and range_count >= 1
    elif kind is SurfaceDerivationKind.COMPOSITIONAL_JOIN:
        valid = source_count >= 2 and not common_other_owner and evidence_count >= 1 and range_count >= 2
    elif kind is SurfaceDerivationKind.REGISTERED_EMLIS_LEXEME:
        expected_owner = _stage1_final_logical_identity("CMEE_STAGE1_EMLIS_OWNER_REF")
        valid = (
            (has_emlis != bool(source_count))
            and (not has_emlis or derivation.emlis_owner_ref == expected_owner)
            and not relation_count
            and not qualifier_count
            and not has_response
            and not has_antecedent
            and not has_participant
            and evidence_count == 0
            and range_count == 0
        )
    elif kind is SurfaceDerivationKind.REGISTERED_PARTICIPANT_LEXEME:
        valid = (
            derivation.participant_role_ref == "CURRENT_USER_ADDRESSEE"
            and source_count == relation_count == qualifier_count == 0
            and not has_emlis
            and not has_response
            and not has_antecedent
            and evidence_count == range_count == 0
        )
    elif kind is SurfaceDerivationKind.REGISTERED_STRUCTURAL_ASSET:
        valid = (
            source_count == relation_count == qualifier_count == 0
            and not has_emlis
            and not has_response
            and not has_antecedent
            and not has_participant
            and evidence_count == range_count == 0
        )
    elif kind is SurfaceDerivationKind.PROJECTED_RESPONSE_OBJECT:
        valid = (
            source_count >= 1
            and relation_count <= 1
            and qualifier_count == 0
            and not has_emlis
            and has_response
            and not has_participant
        )
        if response_object_mode == "EXPLICIT":
            valid = valid and not has_antecedent and evidence_count >= 1 and range_count >= 1
        elif response_object_mode == "COMPOSITE":
            valid = valid and not has_antecedent and evidence_count >= 1 and range_count >= 2
        elif response_object_mode == "ANAPHORIC":
            valid = valid and has_antecedent and evidence_count == range_count == 0
        else:
            valid = False
    elif kind is SurfaceDerivationKind.PROJECTED_FUNCTIONAL_ASSET:
        valid = (
            bool(relation_count) != bool(qualifier_count)
            and source_count == 0
            and not has_emlis
            and not has_response
            and not has_antecedent
            and not has_participant
            and evidence_count == range_count == 0
        )
    else:
        valid = False
    if not valid:
        raise CMEEStage1ContractError("stage1_surface_derivation_owner_invalid")


def _stage1_normalized_contract_name(name: str) -> str:
    with_word_boundaries = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", name)
    return re.sub(r"[^a-z0-9]+", "_", with_word_boundaries.lower()).strip("_")


def validate_stage1_anti_template_registry_invariant(
    registry_field_names: Tuple[str, ...],
    selector_parameter_names: Tuple[str, ...] = (),
    registry_value_rows: Tuple[Tuple[str, ...], ...] = (),
) -> None:
    if (
        type(registry_field_names) is not tuple
        or type(selector_parameter_names) is not tuple
        or type(registry_value_rows) is not tuple
        or any(type(value) is not str or not value for value in registry_field_names)
        or any(type(value) is not str or not value for value in selector_parameter_names)
        or any(
            type(row) is not tuple
            or not row
            or any(type(value) is not str or not value for value in row)
            for row in registry_value_rows
        )
    ):
        raise CMEEStage1ContractError("stage1_anti_template_registry_invalid")
    forbidden_registry = set(CMEE_STAGE1_ANTI_TEMPLATE_FORBIDDEN_REGISTRY_FIELDS)
    forbidden_selector = set(CMEE_STAGE1_ANTI_TEMPLATE_FORBIDDEN_SELECTOR_INPUTS)

    def registry_forbidden(name: str) -> bool:
        normalized = _stage1_normalized_contract_name(name)
        forbidden_equivalent_names = {"opening", "terminal"}
        return (
            normalized in forbidden_registry
            or normalized in forbidden_equivalent_names
            or any(
                marker in normalized
                for marker in (
                    "case_family",
                    "case_specific",
                    "fixture",
                    "exact8",
                    "raw_text",
                    "raw_source",
                    "raw_pattern",
                    "source_regex",
                    "evidence_text",
                    "semantic_resolver",
                    "case_id",
                    "semantic_keyword",
                    "expected_text",
                    "normalized_source_input",
                    "finished_surface",
                    "finished_clause",
                    "finished_sentence",
                    "finished_connective",
                    "connective_chain",
                    "sentence_body",
                    "full_sentence",
                    "grounded_noun",
                    "source_domain_noun",
                    "sentence_template",
                    "clause_template",
                )
            )
        )

    def selector_forbidden(name: str) -> bool:
        normalized = _stage1_normalized_contract_name(name)
        forbidden_equivalent_names = {
            "content",
            "prompt",
            "utterance",
        }
        return (
            normalized in forbidden_selector
            or normalized in forbidden_equivalent_names
            or any(
                marker in normalized
                for marker in (
                    "raw_text",
                    "raw_source",
                    "raw_content",
                    "raw_pattern",
                    "source_regex",
                    "regex_result",
                    "evidence_text",
                    "resolver",
                    "semantic_resolver",
                    "semantic_keyword",
                    "case_id",
                    "case_family",
                    "fixture",
                    "exact8",
                    "input_hash",
                    "input_digest",
                    "expected_text",
                    "finished_",
                    "source_text",
                    "source_string",
                    "source_bytes",
                    "request_text",
                    "input_bytes",
                    "normalized_source_input",
                    "normalized_input",
                    "normalized_text",
                    "source_phrase_family",
                    "semantic_domain_keyword",
                )
            )
        )

    def registry_value_forbidden(value: str) -> bool:
        normalized = _stage1_normalized_contract_name(value)
        return (
            any(mark in value for mark in ("。", "！", "？", "\n", "\r"))
            or any(
                marker in normalized
                for marker in (
                    "raw_text",
                    "raw_source",
                    "suffix",
                    "substring",
                    "regex",
                    "source_suffix",
                    "source_substring",
                    "source_regex",
                    "regex_result",
                    "case_id",
                    "case_family",
                    "fixture_id",
                    "fixture_family",
                    "input_hash",
                    "input_digest",
                    "expected_text",
                    "finished_phrase",
                    "finished_clause",
                    "finished_sentence",
                    "finished_surface",
                    "prior_output",
                    "human_verdict",
                    "private_body_identity",
                )
            )
        )

    if (
        (
            not registry_value_rows
            and registry_field_names
            != _CMEE_STAGE1_ANTI_TEMPLATE_ALLOWED_REGISTRY_FIELDS_ORDERED
        )
        or (
            not registry_value_rows
            and selector_parameter_names
            != _CMEE_STAGE1_ANTI_TEMPLATE_ALLOWED_SELECTOR_INPUTS_ORDERED
        )
        or any(registry_forbidden(value) for value in registry_field_names)
        or any(selector_forbidden(value) for value in selector_parameter_names)
        or any(
            registry_value_forbidden(value)
            for row in registry_value_rows
            for value in row
        )
    ):
        raise CMEEStage1ContractError("stage1_anti_template_registry_invalid")


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
    if isinstance(value, EmlisSubjectiveClaim):
        material = {
            "schema_version": value.schema_version,
            "parent_duty_ref": value.parent_duty_ref,
            "speaker_owner": value.speaker_owner,
            "claim_domain": value.claim_domain,
            "subjective_mode": value.subjective_mode,
            "asserted_subjective_proposition": (
                value.asserted_subjective_proposition
            ),
            "basis_observation_contribution_refs": (
                value.basis_observation_contribution_refs
            ),
            "basis_semantic_refs": value.basis_semantic_refs,
            "source_reception_act_refs": value.source_reception_act_refs,
            "value_principle_refs": value.value_principle_refs,
            "user_fact_effect": value.user_fact_effect,
            "forbidden_promotions": value.forbidden_promotions,
        }
        if value.schema_version == CMEE_STAGE1_RESPONSE_SCHEMA_VERSION_V2:
            material = {
                **material,
                "subjective_responsibility_refs": (
                    value.subjective_responsibility_refs
                ),
                "selected_subjective_opportunity_key": (
                    value.selected_subjective_opportunity_key
                ),
            }
    elif isinstance(value, EmlisStage1Projection):
        material = {
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
        if value.schema_version == CMEE_STAGE1_RESPONSE_SCHEMA_VERSION_V2:
            material = {
                **material,
                "projection_preimage_ref": value.projection_preimage_ref,
                "subjective_claims": value.subjective_claims,
                "composition_policy_ref": value.composition_policy_ref,
                "low_level_grammar_policy_ref": (
                    value.low_level_grammar_policy_ref
                ),
                "subjective_responsibility_rows": (
                    value.subjective_responsibility_rows
                ),
                "subjective_opportunity_rows": (
                    value.subjective_opportunity_rows
                ),
                "subjective_facet_suppression_rows": (
                    value.subjective_facet_suppression_rows
                ),
                "subjective_basis_binding_rows": (
                    value.subjective_basis_binding_rows
                ),
                "source_qualifier_binding_rows": (
                    value.source_qualifier_binding_rows
                ),
                "policy_basis_binding_rows": value.policy_basis_binding_rows,
                "policy_application_rows": value.policy_application_rows,
            }
    elif isinstance(value, RealizedSentenceUnit):
        # The private v2 trace seal contains the selected artifact ref, which
        # is projected only after the ordered unit IDs are frozen.  It is
        # therefore intentionally outside both v1 and v2 unit identity
        # preimages; trace validation binds it back to the selected artifact.
        material = {
            row.name: getattr(value, row.name)
            for row in dataclass_fields(value)
            if row.name not in {identity_field, "v2_trace_seal"}
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
    if projection.schema_version not in {
        CMEE_STAGE1_RESPONSE_SCHEMA_VERSION_V1,
        CMEE_STAGE1_RESPONSE_SCHEMA_VERSION_V2,
    }:
        raise CMEEStage1ContractError("stage1_projection_schema_version_invalid")
    validate_stage1_identity(projection)
    return (
        f"projection:{projection.projection_id}"
        f"@{projection.schema_version}"
    )


def validate_stage1_projection_artifact_ref(
    value: str,
    *,
    expected_schema_version: Optional[str] = None,
) -> None:
    validate_version_qualified_ref(value, expected_types=("projection",))
    match = _VERSION_QUALIFIED_REF_RE.fullmatch(value)
    allowed_versions = {
        CMEE_STAGE1_RESPONSE_SCHEMA_VERSION_V1,
        CMEE_STAGE1_RESPONSE_SCHEMA_VERSION_V2,
    }
    if (
        expected_schema_version is not None
        and expected_schema_version not in allowed_versions
    ):
        raise CMEEStage1ContractError(
            "stage1_projection_artifact_ref_invalid"
        )
    if (
        match is None
        or match.group("version") not in allowed_versions
        or (
            expected_schema_version is not None
            and match.group("version") != expected_schema_version
        )
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
class SourceOwnerResolution:
    """Complete exact-one source-owner resolution for one meaning owner."""

    meaning_owner_id: str
    owner_class: OwnerClass
    resolver_resolution: ResolverResolution
    attachment_admission: AttachmentAdmission
    visible_authority: VisibleAuthority
    source_owner_disposition: SourceOwnerDisposition
    visible_claim_refs: Tuple[str, ...]
    evidence_refs: Tuple[str, ...]
    target_unknown_ref: Optional[str]
    reason_codes: Tuple[str, ...]

    # Compatibility accessors remain read-only while the disabled exact8
    # runner consumes the source-owner contract fields above.
    @property
    def owner_id(self) -> str:
        return self.meaning_owner_id

    @property
    def disposition(self) -> SourceOwnerDisposition:
        return self.source_owner_disposition

    @property
    def evidence_ids(self) -> Tuple[str, ...]:
        return self.evidence_refs


# Neutral read-only shorthand used by the disabled exact8 runner and the
# already-open PR's first vertical implementation.
OwnerDisposition = SourceOwnerResolution


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


def _stage1_positive_visible_claim_ids(
    grounded_graph: GroundedMeaningGraph,
    parent_plan: ExperiencePlan,
) -> set[str]:
    """Return claims with exact positive source-owner visible authority."""

    dispositions = tuple(grounded_graph.owner_dispositions)
    if not dispositions:
        # Small isolated contract fixtures predate source-owner rows. Runtime
        # projections always carry the complete owner denominator.
        return {row.node_id for row in grounded_graph.nodes} | {
            row.edge_id for row in grounded_graph.edges
        }
    owner_ids = tuple(row.meaning_owner_id for row in dispositions)
    if (
        len(owner_ids) != len(set(owner_ids))
        or owner_ids
        != (
            *grounded_graph.required_owner_refs,
            *grounded_graph.active_optional_owner_refs,
        )
    ):
        raise CMEEStage1ContractError("stage1_owner_disposition_partition_invalid")
    positive = {
        SourceOwnerDisposition.SOURCE_EXPLICIT_VISIBLE,
        SourceOwnerDisposition.SUPPLEMENTAL_USER_VISIBLE,
    }
    visible_owner_ids = tuple(
        row.meaning_owner_id
        for row in dispositions
        if row.source_owner_disposition in positive
    )
    unresolved_owner_ids = tuple(
        row.meaning_owner_id
        for row in dispositions
        if row.source_owner_disposition not in positive
    )
    if (
        tuple(parent_plan.visible_owner_ids) != visible_owner_ids
        or tuple(parent_plan.unresolved_owner_ids) != unresolved_owner_ids
    ):
        raise CMEEStage1ContractError("stage1_owner_disposition_partition_invalid")
    claim_by_id = {
        **{row.node_id: row for row in grounded_graph.nodes},
        **{row.edge_id: row for row in grounded_graph.edges},
    }
    visible_claim_ids: set[str] = set()
    for disposition in dispositions:
        refs = tuple(disposition.visible_claim_refs)
        if disposition.source_owner_disposition in positive:
            if not refs or len(refs) != len(set(refs)):
                raise CMEEStage1ContractError(
                    "stage1_candidate_visible_owner_disposition_mismatch"
                )
            for ref in refs:
                claim = claim_by_id.get(ref)
                if (
                    claim is None
                    or claim.owner_id != disposition.meaning_owner_id
                    or claim.epistemic_state is not EpistemicState.SOURCE_EXPLICIT
                ):
                    raise CMEEStage1ContractError(
                        "stage1_candidate_visible_owner_disposition_mismatch"
                    )
            visible_claim_ids.update(refs)
    return visible_claim_ids


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


_FOREGROUND_SCOPE_SCHEMA_VERSION = "1.0"
_FOREGROUND_SCOPE_BASIS_REF_VERSION = (
    "cocolon.cmee.emlis.foreground_scope_basis.v1"
)
_FOREGROUND_SCOPE_REF_VERSION = "cocolon.cmee.emlis.foreground_scope.v1"
_REQUIRED_DIFFERENCE_REF_VERSION = (
    "cocolon.cmee.emlis.required_difference.v1"
)
_COUNTERFACTUAL_MUTATION_REF_VERSION = (
    "cocolon.cmee.emlis.counterfactual_mutation.v1"
)
_WHOLE_READING_CONSEQUENCE_REF_VERSION = (
    "cocolon.cmee.emlis.whole_reading_consequence.v1"
)
_CANONICAL_TYPED_KEY_RE = re.compile(
    r"^[A-Za-z][A-Za-z0-9_-]*:[A-Za-z0-9][A-Za-z0-9._/@|=+\-]*$"
)
_FOREGROUND_SCOPE_TUPLE_FIELDS = (
    "scope_object_refs",
    "source_object_refs",
    "source_evidence_refs",
    "layer1_required_object_refs",
    "required_retention_duty_refs",
    "source_connected_relation_refs",
    "material_unknown_refs",
    "required_qualifier_refs",
    "owner_refs",
    "world_refs",
    "epistemic_state_refs",
    "time_refs",
    "aspect_refs",
    "modality_refs",
    "polarity_refs",
    "scope_refs",
)
_FOREGROUND_SCOPE_COMPATIBILITY_FIELD_PREFIXES = {
    "owner_refs": ("owner:",),
    "world_refs": ("world:",),
    "epistemic_state_refs": ("epistemic:", "epistemic-state:"),
    "time_refs": ("time:", "time_scope:"),
    "aspect_refs": ("aspect:",),
    "modality_refs": ("modality:",),
    "polarity_refs": ("polarity:",),
    "scope_refs": ("scope:",),
}
_QUALIFIER_PREFIXES = (
    "actor:",
    "aspect:",
    "epistemic:",
    "modality:",
    "polarity:",
    "qualifier:",
    "scope:",
    "time:",
    "time_scope:",
    "world:",
    *(
        f"{role.value.lower()}_{axis}:"
        for role in ArgumentRole
        for axis in (
            "actor",
            "world",
            "aspect",
            "polarity",
            "modality",
            "time_scope",
        )
    ),
)
_SEMANTIC_SIGNATURE_PREFIXES_BY_FIELD = {
    "input_center_keys": ("center:",),
    "component_role_keys": ("role:",),
    "relation_direction_keys": ("direction:", "relation:"),
    "epistemic_state_keys": ("epistemic:",),
    "temporal_state_keys": ("temporal:", "time:"),
    "resolution_treatment_keys": ("resolution:",),
    "world_or_owner_distinction_keys": ("owner:", "world:"),
    "modality_polarity_or_limitation_keys": (
        "limitation:",
        "modality:",
        "polarity:",
        "scope:",
    ),
    "episodicity_boundary_keys": ("episodicity:",),
    "qualifier_keys": ("qualifier:",),
}
_GROUNDED_MEANING_NODE_KIND_EXACT14 = frozenset(
    {
        "event",
        "state",
        "reaction",
        "wish",
        "constraint",
        "action",
        "change",
        "self_evaluation",
        "value",
        "uncertainty",
        "conclusion",
        "other_explicit",
        "STRUCTURED_EMOTION_STRENGTH",
        "STRUCTURED_CONTEXT_ATTACHMENT_RELATION",
    }
)
_WHOLE_READING_SIGNATURE_FIELDS_BY_CODE = {
    WholeReadingConsequenceCode.INPUT_CENTER_CHANGED: (
        "input_center_keys",
    ),
    WholeReadingConsequenceCode.RELATION_STRUCTURE_CHANGED: (
        "component_role_keys",
        "relation_direction_keys",
        "component_semantic_keys",
    ),
    WholeReadingConsequenceCode.TEMPORAL_FLOW_CHANGED: (
        "temporal_state_keys",
    ),
    WholeReadingConsequenceCode.RESOLUTION_TREATMENT_CHANGED: (
        "resolution_treatment_keys",
    ),
    WholeReadingConsequenceCode.WORLD_OR_OWNER_DISTINCTION_CHANGED: (
        "world_or_owner_distinction_keys",
        "component_semantic_keys",
    ),
    WholeReadingConsequenceCode.MODALITY_POLARITY_OR_LIMITATION_CHANGED: (
        "modality_polarity_or_limitation_keys",
        "qualifier_keys",
    ),
    WholeReadingConsequenceCode.EPISODICITY_BOUNDARY_CHANGED: (
        "episodicity_boundary_keys",
        "qualifier_keys",
    ),
}


def _require_canonical_string_set(
    values: Sequence[str],
    *,
    code: str,
    allow_empty: bool = True,
) -> Tuple[str, ...]:
    refs = tuple(values)
    if (
        (not allow_empty and not refs)
        or any(type(ref) is not str or not ref for ref in refs)
        or len(refs) != len(set(refs))
        or refs != tuple(sorted(refs))
    ):
        raise CMEEStage1ContractError(code)
    return refs


def _validate_typed_key(
    value: object,
    *,
    allowed_prefixes: Sequence[str],
    code: str,
) -> None:
    if (
        type(value) is not str
        or _CANONICAL_TYPED_KEY_RE.fullmatch(value) is None
        or not value.startswith(tuple(allowed_prefixes))
    ):
        raise CMEEStage1ContractError(code)


def _graph_object_ref(row: object) -> str:
    if type(row) is MeaningNode:
        return f"node:{row.node_id}@{CMEE_GROUNDED_GRAPH_SCHEMA_VERSION}"
    if type(row) is MeaningEdge:
        return f"edge:{row.edge_id}@{CMEE_GROUNDED_GRAPH_SCHEMA_VERSION}"
    raise CMEEStage1ContractError("foreground_scope_graph_object_type_invalid")


def _graph_evidence_refs(row: object, *, source_version: str) -> Tuple[str, ...]:
    values = tuple(
        sorted(f"evidence:{value}@{source_version}" for value in row.evidence_ids)
    )
    return values


_FOREGROUND_SOURCE_NUCLEUS_GROUNDING_EXACT2 = frozenset(
    {"explicit", "user_stated_relation"}
)
_FOREGROUND_SOURCE_OWNER_OBLIGATION_KINDS_EXACT5 = frozenset(
    {
        "THOUGHT_MEANING",
        "ACTION_MEANING",
        "EMOTION_CONTEXT",
        "CATEGORY_CONTEXT",
        "EMOTION_STRENGTH_CONTEXT",
    }
)
_FOREGROUND_SOURCE_ACTOR_VALUES = frozenset({"current_user"})
_FOREGROUND_SOURCE_POLARITY_VALUES = frozenset(
    {"positive", "negative", "mixed", "neutral"}
)
_FOREGROUND_SOURCE_MODALITY_VALUES = frozenset(
    {
        "fact",
        "feeling",
        "wish",
        "possibility",
        "uncertain",
        "refusal",
        "intention",
    }
)
_FOREGROUND_SOURCE_TIME_SCOPE_VALUES = frozenset(
    {
        "past",
        "present",
        "future",
        "past_to_present",
        "present_to_future",
        "continuing",
        "current_input",
    }
)


def _foreground_enum_text(value: object) -> str:
    return str(value.value) if isinstance(value, Enum) else str(value)


_FOREGROUND_ADMITTED_NUCLEUS_GROUNDING_EXACT2 = frozenset(
    {"explicit", "user_stated_relation"}
)
_FOREGROUND_ADMITTED_RELATION_GROUNDING_EXACT1 = frozenset(
    {"user_stated_relation"}
)
_FOREGROUND_OBSERVATION_DUTY_ID = (
    "OBSERVE_SOURCE_EXPLICIT_CURRENT_MEANING"
)
_FOREGROUND_UNKNOWN_DUTY_ID = "PRESERVE_EVIDENCE_BOUND_UNKNOWN"


def _foreground_stable_id(prefix: str, *values: str) -> str:
    digest = hashlib.sha256("|".join(values).encode("utf-8")).hexdigest()
    return f"{prefix}-{digest[:24]}"


def _foreground_graph_id(graph: GroundedMeaningGraph) -> str:
    """Recompute the existing graph identity without importing its owner."""

    node_parts = tuple(
        "\x1f".join(
            (
                row.node_id,
                row.owner_id,
                row.node_kind,
                row.grounding_kind,
                hashlib.sha256(row.value.encode("utf-8")).hexdigest(),
                row.epistemic_state.value,
                *row.evidence_ids,
            )
        )
        for row in graph.nodes
    )
    edge_parts = tuple(
        "\x1f".join(
            (
                row.edge_id,
                row.owner_id,
                row.relation,
                row.source_node_id,
                row.target_node_id,
                row.grounding_kind,
                row.epistemic_state.value,
                *row.evidence_ids,
            )
        )
        for row in graph.edges
    )
    disposition_parts = tuple(
        "\x1f".join(
            (
                row.meaning_owner_id,
                row.owner_class.value,
                row.resolver_resolution.value,
                row.attachment_admission.value,
                row.visible_authority.value,
                row.source_owner_disposition.value,
                "visible_claim_refs",
                *row.visible_claim_refs,
                "evidence_refs",
                *row.evidence_refs,
                "target_unknown_ref",
                row.target_unknown_ref or "",
                "reason_codes",
                *row.reason_codes,
            )
        )
        for row in graph.owner_dispositions
    )
    return _foreground_stable_id(
        "graph",
        graph.source_envelope_id,
        graph.owner_universe_digest,
        *node_parts,
        *edge_parts,
        *disposition_parts,
    )


def _foreground_external_type_is(value: object, name: str) -> bool:
    """Match one frozen upstream contract type without importing its module."""

    value_type = type(value)
    return (
        value_type.__module__ == "emlis_ai_grounded_observation_plan"
        and value_type.__name__ == name
    )


def _foreground_source_evidence_ids(
    source: object,
    source_span_ids: Sequence[str],
) -> Tuple[str, ...]:
    span_ids = tuple(source_span_ids)
    if (
        not span_ids
        or any(type(value) is not str or not value for value in span_ids)
        or len(span_ids) != len(set(span_ids))
    ):
        raise CMEEStage1ContractError(
            "foreground_scope_source_semantic_plan_binding_invalid"
        )
    try:
        refs = tuple(source.evidence_ref(value) for value in span_ids)
    except Exception:
        raise CMEEStage1ContractError(
            "foreground_scope_source_semantic_plan_binding_invalid"
        ) from None
    evidence_ids = tuple(getattr(value, "evidence_id", "") for value in refs)
    if any(type(value) is not str or not value for value in evidence_ids):
        raise CMEEStage1ContractError(
            "foreground_scope_source_semantic_plan_binding_invalid"
        )
    return evidence_ids


def _foreground_source_owner_id(
    source: object,
    source_span_ids: Sequence[str],
) -> str:
    try:
        owner_ids = tuple(
            dict.fromkeys(
                source.meaning_owner_for_span(value)
                for value in source_span_ids
            )
        )
    except Exception:
        raise CMEEStage1ContractError(
            "foreground_scope_source_semantic_plan_binding_invalid"
        ) from None
    if len(owner_ids) != 1 or type(owner_ids[0]) is not str:
        raise CMEEStage1ContractError(
            "foreground_scope_source_semantic_plan_binding_invalid"
        )
    return owner_ids[0]


def _foreground_plan_graph_binding(
    *,
    source: object,
    grounded_plan: object,
    grounded_graph: GroundedMeaningGraph,
    parent_plan: ExperiencePlan,
) -> Mapping[str, object]:
    """Validate and expose only the source/meaning projection of Step 1."""

    if not _foreground_external_type_is(
        grounded_plan, "GroundedObservationPlan"
    ):
        raise CMEEStage1ContractError(
            "foreground_scope_grounded_observation_plan_required"
        )
    if type(grounded_graph) is not GroundedMeaningGraph:
        raise CMEEStage1ContractError(
            "foreground_scope_grounded_graph_invalid"
        )
    if type(parent_plan) is not ExperiencePlan:
        raise CMEEStage1ContractError(
            "foreground_scope_parent_plan_type_invalid"
        )

    nuclei = getattr(grounded_plan, "nuclei", None)
    relations = getattr(grounded_plan, "relations", None)
    coverage = getattr(grounded_plan, "coverage_requirements", None)
    if (
        type(nuclei) is not tuple
        or type(relations) is not tuple
        or not _foreground_external_type_is(
            coverage, "GroundedCoverageRequirements"
        )
    ):
        raise CMEEStage1ContractError(
            "foreground_scope_grounded_observation_plan_noncanonical"
        )
    required_nucleus_ids = getattr(coverage, "required_nucleus_ids", None)
    required_relation_ids = getattr(coverage, "required_relation_ids", None)
    if (
        type(required_nucleus_ids) is not tuple
        or not required_nucleus_ids
        or type(required_relation_ids) is not tuple
        or len(required_nucleus_ids) != len(set(required_nucleus_ids))
        or len(required_relation_ids) != len(set(required_relation_ids))
    ):
        raise CMEEStage1ContractError(
            "foreground_scope_grounded_observation_plan_noncanonical"
        )
    evidence_ref_by_span = {
        getattr(value, "source_span_id", None): value
        for value in getattr(source, "evidence_refs", ())
    }
    if (
        None in evidence_ref_by_span
        or len(evidence_ref_by_span)
        != len(getattr(source, "evidence_refs", ()))
    ):
        raise CMEEStage1ContractError(
            "foreground_scope_source_semantic_plan_binding_invalid"
        )

    nucleus_by_id: dict[str, object] = {}
    node_meta_by_ref: dict[str, object] = {}
    node_id_by_nucleus_id: dict[str, str] = {}
    source_order_by_ref: dict[str, int] = {}
    expected_plan_nodes: list[MeaningNode] = []
    for index, nucleus in enumerate(nuclei):
        if not _foreground_external_type_is(
            nucleus, "GroundedSemanticNucleus"
        ):
            raise CMEEStage1ContractError(
                "foreground_scope_grounded_observation_plan_noncanonical"
            )
        nucleus_id = getattr(nucleus, "nucleus_id", None)
        node_kind = _foreground_enum_text(getattr(nucleus, "kind", ""))
        grounding = _foreground_enum_text(
            getattr(nucleus, "grounding_kind", "")
        )
        span_ids = getattr(nucleus, "source_span_ids", None)
        frame = getattr(nucleus, "semantic_frame", None)
        if (
            type(nucleus_id) is not str
            or not nucleus_id
            or nucleus_id in nucleus_by_id
            or node_kind not in _GROUNDED_MEANING_NODE_KIND_EXACT14
            or type(span_ids) is not tuple
            or not _foreground_external_type_is(frame, "GroundedSemanticFrame")
        ):
            raise CMEEStage1ContractError(
                "foreground_scope_grounded_observation_plan_noncanonical"
            )
        nucleus_by_id[nucleus_id] = nucleus
        if grounding not in _FOREGROUND_ADMITTED_NUCLEUS_GROUNDING_EXACT2:
            continue
        evidence_ids = _foreground_source_evidence_ids(source, span_ids)
        owner_id = _foreground_source_owner_id(source, span_ids)
        node_id = _foreground_stable_id(
            "mn", source.envelope.envelope_id, nucleus_id
        )
        matches = tuple(
            value
            for value in grounded_graph.nodes
            if value.node_id == node_id
        )
        if len(matches) != 1:
            raise CMEEStage1ContractError(
                "foreground_scope_grounded_graph_noncanonical"
            )
        node = matches[0]
        if (
            node.owner_id != owner_id
            or node.node_kind != node_kind
            or node.grounding_kind != grounding
            or type(node.value) is not str
            or not node.value
            or node.epistemic_state is not EpistemicState.SOURCE_EXPLICIT
            or node.evidence_ids != evidence_ids
        ):
            raise CMEEStage1ContractError(
                "foreground_scope_grounded_graph_noncanonical"
            )
        expected_plan_nodes.append(node)
        node_id_by_nucleus_id[nucleus_id] = node_id
        node_ref = _graph_object_ref(node)
        node_meta_by_ref[node_ref] = nucleus
        source_order_by_ref[node_ref] = index

    if any(
        value not in node_id_by_nucleus_id for value in required_nucleus_ids
    ):
        raise CMEEStage1ContractError(
            "foreground_scope_grounded_observation_plan_noncanonical"
        )

    relation_by_id: dict[str, object] = {}
    edge_meta_by_ref: dict[str, object] = {}
    edge_id_by_relation_id: dict[str, str] = {}
    expected_edges: list[MeaningEdge] = []
    for index, relation in enumerate(relations):
        if not _foreground_external_type_is(
            relation, "GroundedSemanticRelation"
        ):
            raise CMEEStage1ContractError(
                "foreground_scope_grounded_observation_plan_noncanonical"
            )
        relation_id = getattr(relation, "relation_id", None)
        relation_kind = _foreground_enum_text(getattr(relation, "type", ""))
        grounding = _foreground_enum_text(
            getattr(relation, "grounding_kind", "")
        )
        from_id = getattr(relation, "from_nucleus_id", None)
        to_id = getattr(relation, "to_nucleus_id", None)
        span_ids = getattr(relation, "source_span_ids", None)
        if (
            type(relation_id) is not str
            or not relation_id
            or relation_id in relation_by_id
            or type(relation_kind) is not str
            or not relation_kind
            or type(span_ids) is not tuple
        ):
            raise CMEEStage1ContractError(
                "foreground_scope_grounded_observation_plan_noncanonical"
            )
        relation_by_id[relation_id] = relation
        if grounding not in _FOREGROUND_ADMITTED_RELATION_GROUNDING_EXACT1:
            continue
        if (
            from_id not in node_id_by_nucleus_id
            or to_id not in node_id_by_nucleus_id
            or from_id == to_id
        ):
            raise CMEEStage1ContractError(
                "foreground_scope_grounded_observation_plan_noncanonical"
            )
        evidence_ids = _foreground_source_evidence_ids(source, span_ids)
        owner_id = _foreground_source_owner_id(source, span_ids)
        edge_id = _foreground_stable_id(
            "me", source.envelope.envelope_id, relation_id
        )
        expected = MeaningEdge(
            edge_id=edge_id,
            owner_id=owner_id,
            relation=relation_kind,
            source_node_id=node_id_by_nucleus_id[from_id],
            target_node_id=node_id_by_nucleus_id[to_id],
            grounding_kind=grounding,
            epistemic_state=EpistemicState.SOURCE_EXPLICIT,
            evidence_ids=evidence_ids,
        )
        matches = tuple(
            value
            for value in grounded_graph.edges
            if value.edge_id == edge_id
        )
        if matches != (expected,):
            raise CMEEStage1ContractError(
                "foreground_scope_grounded_graph_noncanonical"
            )
        expected_edges.append(expected)
        edge_id_by_relation_id[relation_id] = edge_id
        edge_ref = _graph_object_ref(expected)
        edge_meta_by_ref[edge_ref] = relation
        source_order_by_ref[edge_ref] = len(nuclei) + index

    if any(
        value not in edge_id_by_relation_id for value in required_relation_ids
    ):
        raise CMEEStage1ContractError(
            "foreground_scope_grounded_observation_plan_noncanonical"
        )

    required_nucleus_set = set(required_nucleus_ids)
    required_relation_set = set(required_relation_ids)
    selected_span_ids = {
        span_id
        for nucleus_id, nucleus in nucleus_by_id.items()
        if nucleus_id in required_nucleus_set
        for span_id in getattr(nucleus, "source_span_ids", ())
    }
    selected_span_ids.update(
        span_id
        for relation_id, relation in relation_by_id.items()
        if relation_id in required_relation_set
        for span_id in getattr(relation, "source_span_ids", ())
    )
    selected_field_paths = {
        getattr(evidence_ref_by_span[value], "field_path", "")
        for value in selected_span_ids
        if value in evidence_ref_by_span
    }
    attachment_is_material = bool(
        selected_field_paths.intersection({"memo", "memo_action"})
        and any(
            value not in {"memo", "memo_action"}
            for value in selected_field_paths
        )
    )

    try:
        strength_ref = source.evidence_ref("structured:emotion_strength")
        strength_owner = source.meaning_owner_for_span(
            "structured:emotion_strength"
        )
        attachment_obligation = source.attachment_unknown_obligation()
    except Exception:
        raise CMEEStage1ContractError(
            "foreground_scope_source_semantic_plan_binding_invalid"
        ) from None
    strength_node = MeaningNode(
        node_id=_foreground_stable_id(
            "mn", source.envelope.envelope_id, strength_owner
        ),
        owner_id=strength_owner,
        node_kind="STRUCTURED_EMOTION_STRENGTH",
        grounding_kind="source_explicit_not_realized",
        value=source.strength,
        epistemic_state=EpistemicState.SOURCE_EXPLICIT,
        evidence_ids=(strength_ref.evidence_id,),
    )
    unknown_node: Optional[MeaningNode] = None
    if attachment_is_material:
        unknown_node_id = _foreground_stable_id(
            "mn",
            source.envelope.envelope_id,
            attachment_obligation.meaning_owner_id,
            "structured_attachment_unknown",
        )
        unknown_node = MeaningNode(
            node_id=unknown_node_id,
            owner_id=attachment_obligation.meaning_owner_id,
            node_kind="STRUCTURED_CONTEXT_ATTACHMENT_RELATION",
            grounding_kind="unresolved_attachment_relation",
            value="",
            epistemic_state=EpistemicState.UNKNOWN,
            evidence_ids=attachment_obligation.evidence_refs,
        )

    visible_claims_by_owner: dict[str, list[str]] = {}
    for node in expected_plan_nodes:
        visible_claims_by_owner.setdefault(node.owner_id, []).append(
            node.node_id
        )
    for relation_id in required_relation_ids:
        edge_id = edge_id_by_relation_id[relation_id]
        edge = next(value for value in expected_edges if value.edge_id == edge_id)
        visible_claims_by_owner.setdefault(edge.owner_id, []).append(edge.edge_id)

    expected_dispositions: list[OwnerDisposition] = []
    for obligation in source.owner_universe.obligations:
        owner_id = obligation.meaning_owner_id
        visible_claim_refs = tuple(visible_claims_by_owner.get(owner_id, ()))
        if obligation.obligation_kind == "STRUCTURED_CONTEXT_ATTACHMENT":
            if unknown_node is not None:
                expected_dispositions.append(
                    OwnerDisposition(
                        meaning_owner_id=owner_id,
                        owner_class=obligation.owner_class,
                        resolver_resolution=ResolverResolution.UNRESOLVED,
                        attachment_admission=AttachmentAdmission.UNRESOLVED,
                        visible_authority=VisibleAuthority.NONE,
                        source_owner_disposition=(
                            SourceOwnerDisposition.UNKNOWN_PRESERVED_LIMITED
                        ),
                        visible_claim_refs=(unknown_node.node_id,),
                        evidence_refs=obligation.evidence_refs,
                        target_unknown_ref=unknown_node.node_id,
                        reason_codes=("ATTACHMENT_UNRESOLVED",),
                    )
                )
            else:
                expected_dispositions.append(
                    OwnerDisposition(
                        meaning_owner_id=owner_id,
                        owner_class=obligation.owner_class,
                        resolver_resolution=(
                            ResolverResolution.MISSING_OR_INVALID
                        ),
                        attachment_admission=AttachmentAdmission.UNAVAILABLE,
                        visible_authority=VisibleAuthority.NONE,
                        source_owner_disposition=(
                            SourceOwnerDisposition.NOT_VISIBLE_UNRESOLVED
                        ),
                        visible_claim_refs=(),
                        evidence_refs=obligation.evidence_refs,
                        target_unknown_ref=None,
                        reason_codes=("ATTACHMENT_UNRESOLVED",),
                    )
                )
        elif visible_claim_refs:
            expected_dispositions.append(
                OwnerDisposition(
                    meaning_owner_id=owner_id,
                    owner_class=obligation.owner_class,
                    resolver_resolution=ResolverResolution.MISSING_OR_INVALID,
                    attachment_admission=AttachmentAdmission.UNAVAILABLE,
                    visible_authority=VisibleAuthority.SOURCE_EXPLICIT,
                    source_owner_disposition=(
                        SourceOwnerDisposition.SOURCE_EXPLICIT_VISIBLE
                    ),
                    visible_claim_refs=visible_claim_refs,
                    evidence_refs=obligation.evidence_refs,
                    target_unknown_ref=None,
                    reason_codes=(),
                )
            )
        else:
            expected_dispositions.append(
                OwnerDisposition(
                    meaning_owner_id=owner_id,
                    owner_class=obligation.owner_class,
                    resolver_resolution=ResolverResolution.MISSING_OR_INVALID,
                    attachment_admission=AttachmentAdmission.UNAVAILABLE,
                    visible_authority=VisibleAuthority.NONE,
                    source_owner_disposition=(
                        SourceOwnerDisposition.NOT_VISIBLE_UNRESOLVED
                    ),
                    visible_claim_refs=(),
                    evidence_refs=obligation.evidence_refs,
                    target_unknown_ref=None,
                    reason_codes=("ATTACHMENT_UNRESOLVED",),
                )
            )

    expected_nodes = (
        *expected_plan_nodes,
        strength_node,
        *((unknown_node,) if unknown_node is not None else ()),
    )
    if (
        grounded_graph.nodes != expected_nodes
        or grounded_graph.edges != tuple(expected_edges)
        or grounded_graph.owner_dispositions
        != tuple(expected_dispositions)
        or grounded_graph.source_envelope_id != source.envelope.envelope_id
        or grounded_graph.required_owner_refs
        != source.owner_universe.required_owner_refs
        or grounded_graph.active_optional_owner_refs
        != source.owner_universe.active_optional_owner_refs
        or grounded_graph.source_version != source.owner_universe.source_version
        or grounded_graph.obligation_version
        != source.owner_universe.obligation_version
        or grounded_graph.owner_universe_digest
        != source.owner_universe.owner_universe_digest
        or grounded_graph.graph_id != _foreground_graph_id(grounded_graph)
    ):
        raise CMEEStage1ContractError(
            "foreground_scope_grounded_graph_noncanonical"
        )

    positive = {
        SourceOwnerDisposition.SOURCE_EXPLICIT_VISIBLE,
        SourceOwnerDisposition.SUPPLEMENTAL_USER_VISIBLE,
    }
    visible_owner_ids = tuple(
        value.meaning_owner_id
        for value in expected_dispositions
        if value.source_owner_disposition in positive
    )
    unresolved_owner_ids = tuple(
        value.meaning_owner_id
        for value in expected_dispositions
        if value.source_owner_disposition not in positive
    )
    unresolved_required = tuple(
        value
        for value in expected_dispositions
        if value.owner_class is OwnerClass.REQUIRED
        and value.source_owner_disposition not in positive
    )
    visible_unknown_owner_ids = tuple(
        value.meaning_owner_id
        for value in expected_dispositions
        if (
            value.meaning_owner_id
            == attachment_obligation.meaning_owner_id
            and (
                value.source_owner_disposition
                is SourceOwnerDisposition.UNKNOWN_PRESERVED_LIMITED
                or value in unresolved_required
            )
        )
    )
    required_unknown_owner_ids = tuple(
        value.meaning_owner_id for value in unresolved_required
    )
    required_observation_owner_ids = tuple(
        value.meaning_owner_id
        for value in expected_dispositions
        if value.meaning_owner_id in set(grounded_graph.required_owner_refs)
        and value.source_owner_disposition in positive
    )
    meaning_parent_fields = {
        "source_envelope_id": source.envelope.envelope_id,
        "source_version": grounded_graph.source_version,
        "obligation_version": grounded_graph.obligation_version,
        "owner_universe_digest": grounded_graph.owner_universe_digest,
        "observation_duty_id": _FOREGROUND_OBSERVATION_DUTY_ID,
        "unknown_duty_id": _FOREGROUND_UNKNOWN_DUTY_ID,
        "required_observation_owner_ids": required_observation_owner_ids,
        "visible_owner_ids": visible_owner_ids,
        "unresolved_owner_ids": unresolved_owner_ids,
        "visible_unknown_owner_ids": visible_unknown_owner_ids,
        "required_unknown_owner_ids": required_unknown_owner_ids,
    }
    if any(
        getattr(parent_plan, field_name) != expected
        for field_name, expected in meaning_parent_fields.items()
    ):
        raise CMEEStage1ContractError(
            "foreground_scope_parent_plan_noncanonical"
        )

    visible_object_ids = {
        claim_id
        for disposition in expected_dispositions
        if disposition.meaning_owner_id in set(visible_owner_ids)
        for claim_id in disposition.visible_claim_refs
    }
    visible_object_refs = {
        ref
        for ref in (*node_meta_by_ref, *edge_meta_by_ref)
        if ref.split(":", 1)[1].split("@", 1)[0] in visible_object_ids
    }
    edge_by_ref = {
        _graph_object_ref(value): value for value in expected_edges
    }
    node_by_ref = {
        _graph_object_ref(value): value for value in expected_plan_nodes
    }
    required_edge_refs = {
        _graph_object_ref(
            next(
                value
                for value in expected_edges
                if value.edge_id == edge_id_by_relation_id[relation_id]
            )
        )
        for relation_id in required_relation_ids
        if (
            next(
                value
                for value in expected_edges
                if value.edge_id == edge_id_by_relation_id[relation_id]
            ).owner_id
            in set(required_observation_owner_ids)
        )
    }
    relation_covered_node_ids = {
        endpoint
        for edge_ref in required_edge_refs
        for endpoint in (
            edge_by_ref[edge_ref].source_node_id,
            edge_by_ref[edge_ref].target_node_id,
        )
    }
    required_node_refs = {
        _graph_object_ref(
            next(
                value
                for value in expected_plan_nodes
                if value.node_id == node_id_by_nucleus_id[nucleus_id]
            )
        )
        for nucleus_id in required_nucleus_ids
        if (
            node_id_by_nucleus_id[nucleus_id]
            not in relation_covered_node_ids
            and next(
                value
                for value in expected_plan_nodes
                if value.node_id == node_id_by_nucleus_id[nucleus_id]
            ).owner_id
            in set(required_observation_owner_ids)
        )
    }
    if (
        not required_node_refs | required_edge_refs
        or not required_node_refs.issubset(visible_object_refs)
        or not required_edge_refs.issubset(visible_object_refs)
    ):
        raise CMEEStage1ContractError(
            "foreground_scope_grounded_observation_plan_noncanonical"
        )
    return {
        "node_meta_by_ref": node_meta_by_ref,
        "edge_meta_by_ref": edge_meta_by_ref,
        "node_by_ref": node_by_ref,
        "edge_by_ref": edge_by_ref,
        "source_order_by_ref": source_order_by_ref,
        "visible_object_refs": frozenset(visible_object_refs),
        "required_node_refs": frozenset(required_node_refs),
        "required_edge_refs": frozenset(required_edge_refs),
    }


def _validate_foreground_canonical_source_inputs(
    *,
    source: object,
    grounded_plan: object,
    grounded_graph: GroundedMeaningGraph,
    parent_plan: ExperiencePlan,
) -> Tuple[object, object, GroundedMeaningGraph, ExperiencePlan]:
    """Validate the frozen source and its delivery-blind meaning projection."""

    if type(parent_plan) is not ExperiencePlan:
        raise CMEEStage1ContractError(
            "foreground_scope_parent_plan_type_invalid"
        )

    from emlis_ai_current_input_bundle import build_emlis_current_input_bundle
    from .source_kernel import (
        AdmittedTextSource,
        build_source_owner_universe,
        freeze_text_source,
        validate_evidence_refs,
    )

    if type(source) is not AdmittedTextSource:
        raise CMEEStage1ContractError(
            "foreground_scope_admitted_text_source_required"
        )
    try:
        expected_source = freeze_text_source(
            GenerationRequest(
                request_id="im00-source-revalidation",
                current_input_bundle=build_emlis_current_input_bundle(
                    source.normalized_current_input
                ),
                expected_source_record_id=source.envelope.source_record_id,
            )
        )
        validate_evidence_refs(source.envelope, source.evidence_refs)
        expected_universe = build_source_owner_universe(
            source.envelope,
            source.evidence_refs,
        )
    except CMEEStage1ContractError:
        raise
    except Exception:
        raise CMEEStage1ContractError(
            "foreground_scope_source_evidence_unreachable"
        ) from None
    if source != expected_source or source.owner_universe != expected_universe:
        raise CMEEStage1ContractError(
            "foreground_scope_source_evidence_unreachable"
        )
    _foreground_plan_graph_binding(
        source=expected_source,
        grounded_plan=grounded_plan,
        grounded_graph=grounded_graph,
        parent_plan=parent_plan,
    )
    return expected_source, grounded_plan, grounded_graph, parent_plan


def _foreground_source_qualifiers_by_node_ref(
    *,
    source: object,
    grounded_plan: object,
    grounded_graph: GroundedMeaningGraph,
    parent_plan: ExperiencePlan,
) -> Mapping[str, Tuple[str, ...]]:
    """Bind source semantic frames to graph nodes without importing owners.

    ``source_kernel`` imports this module, so this core-private IM00 seam uses
    the frozen source/plan structural contract instead of importing that
    higher layer back into ``contracts.py``.  Every binding is still exact:
    envelope, owner universe, span evidence, owner, kind and grounding must
    reach one graph node.
    """

    _validate_foreground_canonical_source_inputs(
        source=source,
        grounded_plan=grounded_plan,
        grounded_graph=grounded_graph,
        parent_plan=parent_plan,
    )
    envelope = getattr(source, "envelope", None)
    owner_universe = getattr(source, "owner_universe", None)
    evidence_refs = getattr(source, "evidence_refs", None)
    nuclei = getattr(grounded_plan, "nuclei", None)
    obligations = getattr(owner_universe, "obligations", None)
    if (
        envelope is None
        or owner_universe is None
        or type(evidence_refs) is not tuple
        or type(nuclei) is not tuple
        or type(obligations) is not tuple
        or getattr(envelope, "envelope_id", None)
        != grounded_graph.source_envelope_id
        or getattr(owner_universe, "source_envelope_id", None)
        != grounded_graph.source_envelope_id
        or getattr(owner_universe, "source_version", None)
        != grounded_graph.source_version
        or getattr(owner_universe, "obligation_version", None)
        != grounded_graph.obligation_version
        or getattr(owner_universe, "owner_universe_digest", None)
        != grounded_graph.owner_universe_digest
    ):
        raise CMEEStage1ContractError(
            "foreground_scope_source_semantic_plan_binding_invalid"
        )
    evidence_by_span = {
        getattr(value, "source_span_id", None): getattr(
            value, "evidence_id", None
        )
        for value in evidence_refs
    }
    if (
        None in evidence_by_span
        or None in evidence_by_span.values()
        or len(evidence_by_span) != len(evidence_refs)
    ):
        raise CMEEStage1ContractError(
            "foreground_scope_source_semantic_plan_binding_invalid"
        )

    node_qualifiers: dict[str, Tuple[str, ...]] = {}
    used_node_ids: set[str] = set()
    for nucleus in nuclei:
        grounding = _foreground_enum_text(
            getattr(nucleus, "grounding_kind", "")
        )
        if grounding not in _FOREGROUND_SOURCE_NUCLEUS_GROUNDING_EXACT2:
            continue
        kind = _foreground_enum_text(getattr(nucleus, "kind", ""))
        span_ids = getattr(nucleus, "source_span_ids", None)
        frame = getattr(nucleus, "semantic_frame", None)
        if (
            not kind
            or type(span_ids) is not tuple
            or not span_ids
            or any(span_id not in evidence_by_span for span_id in span_ids)
            or frame is None
        ):
            raise CMEEStage1ContractError(
                "foreground_scope_source_semantic_plan_binding_invalid"
            )
        owner_matches = {
            getattr(value, "meaning_owner_id", None)
            for value in obligations
            if getattr(value, "obligation_kind", None)
            in _FOREGROUND_SOURCE_OWNER_OBLIGATION_KINDS_EXACT5
            and set(span_ids).issubset(
                set(getattr(value, "source_span_ids", ()))
            )
        }
        if len(owner_matches) != 1 or None in owner_matches:
            raise CMEEStage1ContractError(
                "foreground_scope_source_semantic_plan_binding_invalid"
            )
        owner_id = next(iter(owner_matches))
        expected_evidence_ids = tuple(
            evidence_by_span[span_id] for span_id in span_ids
        )
        matches = tuple(
            value
            for value in grounded_graph.nodes
            if value.node_id not in used_node_ids
            and value.owner_id == owner_id
            and _foreground_enum_text(value.node_kind) == kind
            and _foreground_enum_text(value.grounding_kind) == grounding
            and value.evidence_ids == expected_evidence_ids
            and value.epistemic_state is EpistemicState.SOURCE_EXPLICIT
        )
        if len(matches) != 1:
            raise CMEEStage1ContractError(
                "foreground_scope_source_semantic_plan_binding_invalid"
            )
        actor = _foreground_enum_text(getattr(frame, "actor", ""))
        polarity = _foreground_enum_text(getattr(frame, "polarity", ""))
        modality = _foreground_enum_text(getattr(frame, "modality", ""))
        time_scope = _foreground_enum_text(
            getattr(frame, "time_scope", "")
        )
        degree = _foreground_enum_text(getattr(frame, "degree", ""))
        if (
            actor not in _FOREGROUND_SOURCE_ACTOR_VALUES
            or polarity not in _FOREGROUND_SOURCE_POLARITY_VALUES
            or modality not in _FOREGROUND_SOURCE_MODALITY_VALUES
            or time_scope not in _FOREGROUND_SOURCE_TIME_SCOPE_VALUES
            or degree != "source_bounded"
        ):
            raise CMEEStage1ContractError(
                "foreground_scope_source_qualifier_value_invalid"
            )
        node = matches[0]
        used_node_ids.add(node.node_id)
        node_qualifiers[_graph_object_ref(node)] = (
            "epistemic:provisional_interpretation",
            f"actor:{actor}",
            "world:unknown",
            "aspect:unknown",
            f"polarity:{polarity}",
            f"modality:{modality}",
            f"time_scope:{time_scope}",
        )

    if not node_qualifiers:
        raise CMEEStage1ContractError(
            "foreground_scope_source_semantic_plan_binding_invalid"
        )
    return node_qualifiers


def _foreground_candidate_required_qualifiers(
    source_qualifiers: Sequence[str],
) -> Tuple[str, ...]:
    """Keep compatibility-only world/aspect out of Layer-1 identity."""

    return tuple(
        value
        for value in source_qualifiers
        if not value.startswith(("world:", "aspect:"))
    )


_FOREGROUND_CANDIDATE_FORBIDDEN_PROMOTIONS_EXACT6 = (
    "unsupported-cause",
    "personality-promotion",
    "hidden-intent-promotion",
    "diagnosis-promotion",
    "future-guarantee",
    "unknown-as-interpretation",
)
_FOREGROUND_OBSERVATION_FORBIDDEN_OPERATIONS_EXACT6 = (
    "invent-cause",
    "invent-personality",
    "invent-hidden-intent",
    "invent-diagnosis",
    "promote-unknown",
    "complete-unfinished-meaning",
)
_FOREGROUND_DIRECTION_KINDS = frozenset(
    {"wish", "direction", "desire", "intention", "goal", "help_seeking"}
)
_FOREGROUND_BURDEN_KINDS = frozenset(
    {"constraint", "burden", "fatigue", "anxiety", "hesitation", "block"}
)
_FOREGROUND_ACTION_KINDS = frozenset({"action", "attempt"})
_FOREGROUND_CHANGE_KINDS = frozenset({"change", "bounded_change"})
_FOREGROUND_EVENT_KINDS = frozenset({"event", "action", "change"})
_FOREGROUND_RESIDUE_KINDS = frozenset(
    {"reaction", "residue", "lingering_state", "unfinished", "uncertainty"}
)
_FOREGROUND_UNFINISHED_KINDS = frozenset(
    {"uncertainty", "unfinished", "open_question"}
)
_FOREGROUND_OPERATOR_PRIORITY = {
    RelationOperator.TENSION_WITH: 0,
    RelationOperator.COEXISTS_WITH: 1,
    RelationOperator.ACTION_PRECEDES_CHANGE: 2,
    RelationOperator.TEMPORALLY_PRECEDES: 3,
    RelationOperator.SOURCE_EXPLICIT_CAUSE: 4,
    RelationOperator.NO_RELATION_CLAIM: 5,
}
_FOREGROUND_RETENTION_PRIORITY = {"required": 0, "should": 1, "optional": 2}


def _foreground_direct_shape(
    node: MeaningNode,
    nucleus: object,
    *,
    stage1_response_schema_version: str,
) -> Tuple[InterpretationKind, SemanticOperator]:
    """Derive the exact current Layer-1 direct shape from source metadata."""

    kind = _foreground_enum_text(node.node_kind).lower()
    frame = getattr(nucleus, "semantic_frame", None)
    modality = _foreground_enum_text(getattr(frame, "modality", "")).lower()
    predicate = _foreground_enum_text(
        getattr(frame, "predicate_kind", "")
    ).lower()
    attribute_codes = frozenset(
        _foreground_enum_text(value)
        for value in getattr(frame, "attribute_codes", ())
        if _foreground_enum_text(value)
    )
    if stage1_response_schema_version == CMEE_STAGE1_RESPONSE_SCHEMA_VERSION_V2:
        if kind in _FOREGROUND_DIRECTION_KINDS:
            return (
                InterpretationKind.DIRECT_DIRECTION,
                SemanticOperator.PRESENT_DIRECTION,
            )
        if kind in _FOREGROUND_CHANGE_KINDS:
            return (
                InterpretationKind.DIRECT_STATE,
                SemanticOperator.PRESENT_CHANGE,
            )
        if kind in _FOREGROUND_UNFINISHED_KINDS:
            return (
                InterpretationKind.UNFINISHED,
                SemanticOperator.PRESENT_UNFINISHED,
            )
        if kind in _FOREGROUND_BURDEN_KINDS:
            return (
                InterpretationKind.DIRECT_STATE,
                SemanticOperator.PRESENT_BURDEN,
            )
        if kind in _FOREGROUND_ACTION_KINDS:
            return (
                InterpretationKind.DIRECT_STATE,
                SemanticOperator.PRESENT_ACTUAL_OUTPUT,
            )
        metadata_burden = (
            predicate == "constraint"
            or "operator:constraint" in attribute_codes
            or "detected_type:limit_signal" in attribute_codes
            or "detected_type:fear" in attribute_codes
            or any(
                value.startswith("source_claim:pressure.")
                for value in attribute_codes
            )
        )
        if kind == "reaction":
            if (
                predicate == "change"
                or "operator:change" in attribute_codes
                or "operator:positive_change" in attribute_codes
            ):
                return (
                    InterpretationKind.DIRECT_STATE,
                    SemanticOperator.PRESENT_CHANGE,
                )
            if metadata_burden:
                return (
                    InterpretationKind.DIRECT_STATE,
                    SemanticOperator.PRESENT_BURDEN,
                )
        elif kind == "state" and metadata_burden:
            return (
                InterpretationKind.DIRECT_STATE,
                SemanticOperator.PRESENT_BURDEN,
            )
        return InterpretationKind.DIRECT_STATE, SemanticOperator.PRESENT_STATE
    if stage1_response_schema_version != CMEE_STAGE1_RESPONSE_SCHEMA_VERSION_V1:
        raise CMEEStage1ContractError(
            "foreground_scope_meaning_projection_noncanonical"
        )
    if (
        kind in _FOREGROUND_DIRECTION_KINDS
        or modality in {"wish", "intention"}
        or predicate == "wish"
    ):
        return (
            InterpretationKind.DIRECT_DIRECTION,
            SemanticOperator.PRESENT_DIRECTION,
        )
    if (
        kind in _FOREGROUND_CHANGE_KINDS
        or predicate == "change"
        or "operator:change" in attribute_codes
        or "operator:positive_change" in attribute_codes
    ):
        return InterpretationKind.DIRECT_STATE, SemanticOperator.PRESENT_CHANGE
    if (
        kind in _FOREGROUND_UNFINISHED_KINDS
        or predicate == "unfinished"
        or "operator:unfinished" in attribute_codes
    ):
        return InterpretationKind.UNFINISHED, SemanticOperator.PRESENT_UNFINISHED
    if (
        kind in _FOREGROUND_BURDEN_KINDS
        or predicate == "constraint"
        or "operator:constraint" in attribute_codes
        or "detected_type:limit_signal" in attribute_codes
        or "detected_type:fear" in attribute_codes
        or any(
            value.startswith("source_claim:pressure.")
            for value in attribute_codes
        )
    ):
        return InterpretationKind.DIRECT_STATE, SemanticOperator.PRESENT_BURDEN
    if (
        kind in _FOREGROUND_ACTION_KINDS
        or predicate == "action"
        or "operator:action" in attribute_codes
    ):
        return (
            InterpretationKind.DIRECT_STATE,
            SemanticOperator.PRESENT_ACTUAL_OUTPUT,
        )
    if modality == "uncertain" or "operator:uncertainty" in attribute_codes:
        return InterpretationKind.UNFINISHED, SemanticOperator.PRESENT_UNFINISHED
    return InterpretationKind.DIRECT_STATE, SemanticOperator.PRESENT_STATE


def _foreground_direct_argument_bindings(
    semantic_ref: str,
    nucleus: object,
) -> Tuple[ArgumentBinding, ...]:
    frame = getattr(nucleus, "semantic_frame", None)
    actor = _foreground_enum_text(getattr(frame, "actor", "")).lower()
    modality = _foreground_enum_text(getattr(frame, "modality", "")).lower()
    values = [ArgumentBinding(ArgumentRole.PRIMARY, semantic_ref)]
    if actor in {"current_user", "user"} and modality in {
        "feeling",
        "wish",
        "intention",
        "refusal",
        "uncertain",
    }:
        values.append(ArgumentBinding(ArgumentRole.EXPERIENCER, semantic_ref))
    return tuple(values)


def _foreground_relation_shape(
    *,
    edge: MeaningEdge,
    relation: object,
    node_by_ref: Mapping[str, MeaningNode],
    node_meta_by_ref: Mapping[str, object],
    source_order_by_ref: Mapping[str, int],
    stage1_response_schema_version: str,
) -> Optional[
    Tuple[
        InterpretationKind,
        SemanticOperator,
        RelationOperator,
        Tuple[ArgumentBinding, ...],
    ]
]:
    source_ref = _stage1_node_ref(edge.source_node_id)
    target_ref = _stage1_node_ref(edge.target_node_id)
    source_node = node_by_ref[source_ref]
    target_node = node_by_ref[target_ref]
    source_shape = _foreground_direct_shape(
        source_node,
        node_meta_by_ref[source_ref],
        stage1_response_schema_version=stage1_response_schema_version,
    )
    target_shape = _foreground_direct_shape(
        target_node,
        node_meta_by_ref[target_ref],
        stage1_response_schema_version=stage1_response_schema_version,
    )
    relation_kind = _foreground_enum_text(getattr(relation, "type", ""))

    def symmetric(
        candidate_kind: InterpretationKind,
        relation_operator: RelationOperator,
    ) -> Tuple[
        InterpretationKind,
        SemanticOperator,
        RelationOperator,
        Tuple[ArgumentBinding, ...],
    ]:
        ordered_refs = tuple(
            sorted(
                (source_ref, target_ref),
                key=source_order_by_ref.__getitem__,
            )
        )
        if (
            len(ordered_refs) != 2
            or source_order_by_ref[source_ref]
            == source_order_by_ref[target_ref]
        ):
            raise CMEEStage1ContractError(
                "foreground_scope_meaning_projection_noncanonical"
            )
        return (
            candidate_kind,
            SemanticOperator.SYNTHESIZE_RELATION,
            relation_operator,
            (
                ArgumentBinding(ArgumentRole.LEFT, ordered_refs[0]),
                ArgumentBinding(ArgumentRole.RIGHT, ordered_refs[1]),
            ),
        )

    if relation_kind == "coexistence":
        return symmetric(
            InterpretationKind.COEXISTENCE,
            RelationOperator.COEXISTS_WITH,
        )
    if relation_kind == "contrast":
        return symmetric(
            InterpretationKind.TENSION,
            RelationOperator.TENSION_WITH,
        )
    if relation_kind in {
        "wish_and_constraint",
        "preserves_despite",
        "attempt_and_block",
        "continuation_or_refusal",
    }:
        direction_ref: Optional[str] = None
        burden_ref: Optional[str] = None
        if (
            source_shape[0] is InterpretationKind.DIRECT_DIRECTION
            and target_shape[1] is SemanticOperator.PRESENT_BURDEN
        ):
            direction_ref, burden_ref = source_ref, target_ref
        elif (
            source_shape[1] is SemanticOperator.PRESENT_BURDEN
            and target_shape[0] is InterpretationKind.DIRECT_DIRECTION
        ):
            direction_ref, burden_ref = target_ref, source_ref
        if direction_ref is None or burden_ref is None:
            return None
        operator = (
            RelationOperator.COEXISTS_WITH
            if relation_kind == "wish_and_constraint"
            else RelationOperator.TENSION_WITH
        )
        return (
            InterpretationKind.DIRECTION_UNDER_BURDEN,
            SemanticOperator.SYNTHESIZE_RELATION,
            operator,
            (
                ArgumentBinding(ArgumentRole.LEFT, direction_ref),
                ArgumentBinding(ArgumentRole.RIGHT, burden_ref),
            ),
        )
    if relation_kind == "action_supports_change":
        if (
            source_node.node_kind.lower() not in _FOREGROUND_ACTION_KINDS
            or target_node.node_kind.lower() not in _FOREGROUND_CHANGE_KINDS
        ):
            return None
        return (
            InterpretationKind.ACTION_THEN_CHANGE_ONCE,
            SemanticOperator.PRESENT_CHANGE,
            RelationOperator.ACTION_PRECEDES_CHANGE,
            (
                ArgumentBinding(ArgumentRole.ACTION, source_ref),
                ArgumentBinding(ArgumentRole.CHANGE, target_ref),
            ),
        )
    if relation_kind in {"temporal_before_after", "shift_from_to"}:
        if (
            source_node.node_kind.lower() not in _FOREGROUND_EVENT_KINDS
            or target_node.node_kind.lower() not in _FOREGROUND_RESIDUE_KINDS
        ):
            return None
        return (
            InterpretationKind.RESIDUE_AFTER_EVENT,
            SemanticOperator.PRESENT_RESIDUE,
            RelationOperator.TEMPORALLY_PRECEDES,
            (
                ArgumentBinding(ArgumentRole.BEFORE, source_ref),
                ArgumentBinding(ArgumentRole.AFTER, target_ref),
            ),
        )
    if relation_kind == "user_stated_cause":
        return (
            InterpretationKind.SOURCE_STATED_CAUSE,
            SemanticOperator.SYNTHESIZE_RELATION,
            RelationOperator.SOURCE_EXPLICIT_CAUSE,
            (
                ArgumentBinding(ArgumentRole.CAUSE, source_ref),
                ArgumentBinding(ArgumentRole.EFFECT, target_ref),
            ),
        )
    return None


def _foreground_identified(value: object, identity_field: str) -> object:
    return replace(
        value,
        **{identity_field: recompute_stage1_identity(value)},
    )


def _foreground_expected_layer1(
    *,
    source: object,
    grounded_plan: object,
    grounded_graph: GroundedMeaningGraph,
    parent_plan: ExperiencePlan,
    source_qualifiers_by_node_ref: Mapping[str, Tuple[str, ...]],
    stage1_response_schema_version: str = CMEE_STAGE1_RESPONSE_SCHEMA_VERSION,
) -> Tuple[
    Tuple[EmlisInterpretationCandidate, ...],
    EmlisMeaningField,
    Tuple[PlannedObservationContribution, ...],
    Tuple[str, ...],
    ObservationDepthClass,
]:
    binding = _foreground_plan_graph_binding(
        source=source,
        grounded_plan=grounded_plan,
        grounded_graph=grounded_graph,
        parent_plan=parent_plan,
    )
    node_meta_by_ref = binding["node_meta_by_ref"]
    edge_meta_by_ref = binding["edge_meta_by_ref"]
    node_by_ref = binding["node_by_ref"]
    edge_by_ref = binding["edge_by_ref"]
    source_order_by_ref = binding["source_order_by_ref"]
    visible_object_refs = binding["visible_object_refs"]
    required_node_refs = binding["required_node_refs"]
    required_edge_refs = binding["required_edge_refs"]
    obligation_kind_by_owner = {
        value.meaning_owner_id: value.obligation_kind
        for value in source.owner_universe.obligations
    }

    candidate_rows: list[tuple[object, ...]] = []
    for edge in grounded_graph.edges:
        edge_ref = _graph_object_ref(edge)
        if edge_ref not in visible_object_refs:
            continue
        required = edge_ref in required_edge_refs
        shape = _foreground_relation_shape(
            edge=edge,
            relation=edge_meta_by_ref[edge_ref],
            node_by_ref=node_by_ref,
            node_meta_by_ref=node_meta_by_ref,
            source_order_by_ref=source_order_by_ref,
            stage1_response_schema_version=(
                stage1_response_schema_version
            ),
        )
        if shape is None:
            if required:
                raise CMEEStage1ContractError(
                    "foreground_scope_meaning_projection_noncanonical"
                )
            continue
        candidate_kind, semantic_operator, relation_operator, arguments = shape
        semantic_refs = tuple(value.semantic_ref for value in arguments)
        evidence_ids = tuple(
            dict.fromkeys(
                (
                    *(
                        evidence_id
                        for semantic_ref in semantic_refs
                        for evidence_id in node_by_ref[
                            semantic_ref
                        ].evidence_ids
                    ),
                    *edge.evidence_ids,
                )
            )
        )
        qualifiers = ["epistemic:provisional_interpretation"]
        for argument in arguments:
            source_qualifiers = _foreground_candidate_required_qualifiers(
                source_qualifiers_by_node_ref[argument.semantic_ref]
            )
            role_prefix = f"{argument.role.value.lower()}_"
            qualifiers.extend(
                f"{role_prefix}{value}" for value in source_qualifiers[1:]
            )
        relation_meta = edge_meta_by_ref[edge_ref]
        candidate = EmlisInterpretationCandidate(
            schema_version=CMEE_STAGE1_RESPONSE_SCHEMA_VERSION,
            candidate_id="",
            candidate_kind=candidate_kind,
            claim_domain=EmlisTraceClaimDomain.INTERPRETIVE_OBSERVATION.value,
            semantic_operator=semantic_operator,
            argument_bindings=arguments,
            relation_operator=relation_operator,
            relation_basis_refs=(edge_ref,),
            derivation_rule_id=(
                "cocolon.cmee.v1a.stage1.relation."
                f"{_foreground_enum_text(getattr(relation_meta, 'type', '')).lower()}.v1"
            ),
            semantic_refs=semantic_refs,
            evidence_refs=tuple(
                f"evidence:{value}@{grounded_graph.source_version}"
                for value in evidence_ids
            ),
            basis_candidate_refs=(),
            epistemic_state=(
                InterpretationEpistemicState.PROVISIONAL_INTERPRETATION
            ),
            required_qualifiers=tuple(qualifiers),
            forbidden_promotions=(
                _FOREGROUND_CANDIDATE_FORBIDDEN_PROMOTIONS_EXACT6
            ),
        )
        candidate = _foreground_identified(candidate, "candidate_id")
        retention = _foreground_enum_text(
            getattr(relation_meta, "retention", "")
        ).lower()
        if retention not in _FOREGROUND_RETENTION_PRIORITY or (
            required and retention != "required"
        ):
            raise CMEEStage1ContractError(
                "foreground_scope_meaning_projection_noncanonical"
            )
        candidate_rows.append(
            (
                candidate,
                required,
                True,
                obligation_kind_by_owner[edge.owner_id],
                _FOREGROUND_RETENTION_PRIORITY[retention],
                source_order_by_ref[edge_ref],
            )
        )

    for node in grounded_graph.nodes:
        node_ref = _graph_object_ref(node)
        if node_ref not in visible_object_refs or node_ref not in node_meta_by_ref:
            continue
        required = node_ref in required_node_refs
        nucleus = node_meta_by_ref[node_ref]
        candidate_kind, semantic_operator = _foreground_direct_shape(
            node,
            nucleus,
            stage1_response_schema_version=(
                stage1_response_schema_version
            ),
        )
        candidate = EmlisInterpretationCandidate(
            schema_version=CMEE_STAGE1_RESPONSE_SCHEMA_VERSION,
            candidate_id="",
            candidate_kind=candidate_kind,
            claim_domain=EmlisTraceClaimDomain.INTERPRETIVE_OBSERVATION.value,
            semantic_operator=semantic_operator,
            argument_bindings=_foreground_direct_argument_bindings(
                node_ref, nucleus
            ),
            relation_operator=RelationOperator.NO_RELATION_CLAIM,
            relation_basis_refs=(),
            derivation_rule_id=(
                "cocolon.cmee.v1a.stage1.direct."
                f"{candidate_kind.value.lower()}.v1"
            ),
            semantic_refs=(node_ref,),
            evidence_refs=tuple(
                f"evidence:{value}@{grounded_graph.source_version}"
                for value in node.evidence_ids
            ),
            basis_candidate_refs=(),
            epistemic_state=(
                InterpretationEpistemicState.PROVISIONAL_INTERPRETATION
            ),
            required_qualifiers=(
                _foreground_candidate_required_qualifiers(
                    source_qualifiers_by_node_ref[node_ref]
                )
            ),
            forbidden_promotions=(
                _FOREGROUND_CANDIDATE_FORBIDDEN_PROMOTIONS_EXACT6
            ),
        )
        candidate = _foreground_identified(candidate, "candidate_id")
        retention = _foreground_enum_text(
            getattr(nucleus, "retention", "")
        ).lower()
        if retention not in _FOREGROUND_RETENTION_PRIORITY or (
            required and retention != "required"
        ):
            raise CMEEStage1ContractError(
                "foreground_scope_meaning_projection_noncanonical"
            )
        candidate_rows.append(
            (
                candidate,
                required,
                False,
                obligation_kind_by_owner[node.owner_id],
                _FOREGROUND_RETENTION_PRIORITY[retention],
                source_order_by_ref[node_ref],
            )
        )

    candidate_rows.sort(
        key=lambda value: (
            0 if value[1] else 1,
            0 if value[2] else 1,
            value[4],
            value[5],
            _FOREGROUND_OPERATOR_PRIORITY[value[0].relation_operator],
            value[0].semantic_refs,
            value[0].candidate_id,
        )
    )
    selected_rows: list[tuple[object, ...]] = []
    kind_counts: dict[InterpretationKind, int] = {}
    for value in candidate_rows:
        candidate = value[0]
        count = kind_counts.get(candidate.candidate_kind, 0)
        if count >= _STAGE1_INTERPRETATION_CANDIDATE_KIND_CAP:
            if value[1]:
                raise CMEEStage1ContractError(
                    "foreground_scope_meaning_projection_noncanonical"
                )
            continue
        selected_rows.append(value)
        kind_counts[candidate.candidate_kind] = count + 1
    if len(selected_rows) > 16:
        if any(value[1] for value in selected_rows[16:]):
            raise CMEEStage1ContractError(
                "foreground_scope_meaning_projection_noncanonical"
            )
        selected_rows = selected_rows[:16]
    if not selected_rows or not any(value[1] for value in selected_rows):
        raise CMEEStage1ContractError(
            "foreground_scope_meaning_projection_noncanonical"
        )
    candidates = tuple(value[0] for value in selected_rows)
    required_candidate_refs = tuple(
        value[0].candidate_id for value in selected_rows if value[1]
    )

    grouped: dict[MeaningFieldSlot, list[EmlisInterpretationCandidate]] = {}
    for candidate in candidates:
        grouped.setdefault(
            _stage1_meaning_field_slot_for_candidate(candidate), []
        ).append(candidate)
    entries = tuple(
        MeaningFieldEntry(
            slot=slot,
            interpretation_candidate_refs=tuple(
                value.candidate_id for value in grouped[slot]
            ),
            semantic_refs=_stage1_ordered_unique(
                tuple(
                    ref
                    for value in grouped[slot]
                    for ref in value.semantic_refs
                )
            ),
            evidence_refs=_stage1_ordered_unique(
                tuple(
                    ref
                    for value in grouped[slot]
                    for ref in value.evidence_refs
                )
            ),
        )
        for slot in _STAGE1_MEANING_SLOT_ORDER
        if grouped.get(slot)
    )
    disposition_by_owner = {
        value.meaning_owner_id: value
        for value in grounded_graph.owner_dispositions
    }
    material_unknown_refs = tuple(
        f"unknown:{disposition_by_owner[owner_id].target_unknown_ref}"
        f"@{grounded_graph.obligation_version}"
        for owner_id in parent_plan.visible_unknown_owner_ids
    )
    meaning_field = EmlisMeaningField(
        schema_version=CMEE_STAGE1_RESPONSE_SCHEMA_VERSION,
        meaning_field_id="",
        grounded_graph_ref=(
            f"grounded:{grounded_graph.graph_id}"
            f"@{CMEE_GROUNDED_GRAPH_SCHEMA_VERSION}"
        ),
        center_candidate_ref=required_candidate_refs[0],
        entries=entries,
        required_candidate_refs=required_candidate_refs,
        material_unknown_refs=material_unknown_refs,
    )
    meaning_field = _foreground_identified(
        meaning_field, "meaning_field_id"
    )

    required_rows = [value for value in selected_rows if value[1]]
    structured_context_kinds = {
        "EMOTION_CONTEXT",
        "CATEGORY_CONTEXT",
        "EMOTION_STRENGTH_CONTEXT",
        "STRUCTURED_CONTEXT_ATTACHMENT",
    }
    optional_rows = [
        value
        for value in selected_rows
        if not value[1] and value[3] not in structured_context_kinds
    ]
    contribution_rows = [
        *required_rows,
        *(optional_rows[:1] if len(required_rows) == 1 else []),
    ]
    contributions: list[PlannedObservationContribution] = []
    for value in contribution_rows:
        candidate = value[0]
        contribution_kind = _stage1_contribution_kind_for_candidate(candidate)
        contribution = PlannedObservationContribution(
            schema_version=CMEE_STAGE1_RESPONSE_SCHEMA_VERSION,
            contribution_id="",
            parent_duty_ref=parent_plan.observation_duty_id,
            contribution_kind=contribution_kind,
            interpretation_candidate_refs=(candidate.candidate_id,),
            semantic_operator=candidate.semantic_operator,
            argument_bindings=candidate.argument_bindings,
            relation_operator=candidate.relation_operator,
            relation_basis_refs=candidate.relation_basis_refs,
            derivation_rule_id=(
                "cocolon.cmee.v1a.stage1.layer1."
                f"{contribution_kind.value.lower()}.v1"
            ),
            semantic_refs=candidate.semantic_refs,
            evidence_refs=candidate.evidence_refs,
            retention="REQUIRED" if value[1] else "OPTIONAL",
            semantic_key_version=_STAGE2_OBSERVATION_SEMANTIC_KEY_VERSION,
            canonical_semantic_key=_stage2_observation_semantic_key(candidate),
            prerequisite_contribution_refs=(),
            forbidden_operations=(
                _FOREGROUND_OBSERVATION_FORBIDDEN_OPERATIONS_EXACT6
            ),
        )
        contributions.append(
            _foreground_identified(contribution, "contribution_id")
        )
    contribution_tuple = tuple(contributions)
    count = len(contribution_tuple)
    if count == 1:
        depth = ObservationDepthClass.FOCUSED
    elif 2 <= count <= 3:
        depth = ObservationDepthClass.LAYERED
    elif 4 <= count <= _STAGE1_LAYER1_OBSERVATION_CAP:
        depth = ObservationDepthClass.DENSE
    else:
        raise CMEEStage1ContractError(
            "foreground_scope_meaning_projection_noncanonical"
        )
    return (
        candidates,
        meaning_field,
        contribution_tuple,
        tuple(value.contribution_id for value in contribution_tuple),
        depth,
    )


def project_premeaning_source_qualifier_rows(
    *,
    source: object,
    grounded_plan: object,
    grounded_graph: GroundedMeaningGraph,
    parent_plan: ExperiencePlan,
) -> Tuple[GroundedSourceQualifierRow, ...]:
    """Project the canonical source-owned qualifier closure once."""

    qualifiers_by_node_ref = _foreground_source_qualifiers_by_node_ref(
        source=source,
        grounded_plan=grounded_plan,
        grounded_graph=grounded_graph,
        parent_plan=parent_plan,
    )
    return tuple(
        GroundedSourceQualifierRow(node_ref=ref, qualifier_refs=qualifiers)
        for ref, qualifiers in sorted(qualifiers_by_node_ref.items())
    )


def project_premeaning_source_relation_rows(
    *,
    source: object,
    grounded_plan: object,
    grounded_graph: GroundedMeaningGraph,
    parent_plan: ExperiencePlan,
    stage1_response_schema_version: str = CMEE_STAGE1_RESPONSE_SCHEMA_VERSION,
) -> Tuple[GroundedSourceRelationRow, ...]:
    """Project source relations before Layer-1 pool ordering or caps."""

    if stage1_response_schema_version not in {
        CMEE_STAGE1_RESPONSE_SCHEMA_VERSION_V1,
        CMEE_STAGE1_RESPONSE_SCHEMA_VERSION_V2,
    }:
        raise CMEEStage1ContractError(
            "premeaning_response_schema_invalid"
        )
    binding = _foreground_plan_graph_binding(
        source=source,
        grounded_plan=grounded_plan,
        grounded_graph=grounded_graph,
        parent_plan=parent_plan,
    )
    node_by_ref = binding["node_by_ref"]
    node_meta_by_ref = binding["node_meta_by_ref"]
    edge_meta_by_ref = binding["edge_meta_by_ref"]
    source_order_by_ref = binding["source_order_by_ref"]
    rows: list[GroundedSourceRelationRow] = []
    for edge in grounded_graph.edges:
        relation_ref = _graph_object_ref(edge)
        relation_meta = edge_meta_by_ref.get(relation_ref)
        if relation_meta is None:
            continue
        relation_kind = project_foreground_scope_relation_kind(
            edge.relation
        )
        if relation_kind is None:
            shape = _foreground_relation_shape(
                edge=edge,
                relation=relation_meta,
                node_by_ref=node_by_ref,
                node_meta_by_ref=node_meta_by_ref,
                source_order_by_ref=source_order_by_ref,
                stage1_response_schema_version=(
                    stage1_response_schema_version
                ),
            )
            if shape is None:
                continue
            relation_kind = project_foreground_scope_relation_kind(
                edge.relation,
                relation_operators=(shape[2],),
            )
        if relation_kind is None:
            continue
        rows.append(
            GroundedSourceRelationRow(
                relation_ref=relation_ref,
                relation_kind=relation_kind,
            )
        )
    return tuple(
        sorted(
            rows,
            key=lambda row: (row.relation_ref, row.relation_kind.value),
        )
    )


def validate_premeaning_grounded_inputs(
    premeaning_inputs: PreMeaningGroundedInputs,
    *,
    source: object,
    grounded_plan: object,
    grounded_graph: GroundedMeaningGraph,
    parent_plan: ExperiencePlan,
) -> None:
    """Bind a Reception-free semantic closure to the actual typed source."""

    if type(premeaning_inputs) is not PreMeaningGroundedInputs:
        raise CMEEStage1ContractError("premeaning_grounded_inputs_invalid")
    if premeaning_inputs.schema_version != "1.0":
        raise CMEEStage1ContractError("premeaning_schema_version_invalid")
    if premeaning_inputs.stage1_response_schema_version not in {
        CMEE_STAGE1_RESPONSE_SCHEMA_VERSION_V1,
        CMEE_STAGE1_RESPONSE_SCHEMA_VERSION_V2,
    }:
        raise CMEEStage1ContractError("premeaning_response_schema_invalid")
    if premeaning_inputs.grounded_graph is not grounded_graph:
        raise CMEEStage1ContractError("premeaning_grounded_graph_identity_mismatch")
    _validate_foreground_canonical_source_inputs(
        source=source,
        grounded_plan=grounded_plan,
        grounded_graph=grounded_graph,
        parent_plan=parent_plan,
    )
    source_qualifiers_by_node_ref = (
        _foreground_source_qualifiers_by_node_ref(
            source=source,
            grounded_plan=grounded_plan,
            grounded_graph=grounded_graph,
            parent_plan=parent_plan,
        )
    )
    (
        expected_candidates,
        expected_meaning_field,
        expected_contributions,
        expected_ordered_observation_refs,
        expected_observation_depth,
    ) = _foreground_expected_layer1(
        source=source,
        grounded_plan=grounded_plan,
        grounded_graph=grounded_graph,
        parent_plan=parent_plan,
        source_qualifiers_by_node_ref=source_qualifiers_by_node_ref,
        stage1_response_schema_version=(
            premeaning_inputs.stage1_response_schema_version
        ),
    )
    expected_graph_ref = (
        f"grounded:{grounded_graph.graph_id}"
        f"@{CMEE_GROUNDED_GRAPH_SCHEMA_VERSION}"
    )
    expected_qualifier_rows = project_premeaning_source_qualifier_rows(
        source=source,
        grounded_plan=grounded_plan,
        grounded_graph=grounded_graph,
        parent_plan=parent_plan,
    )
    expected_relation_rows = project_premeaning_source_relation_rows(
        source=source,
        grounded_plan=grounded_plan,
        grounded_graph=grounded_graph,
        parent_plan=parent_plan,
        stage1_response_schema_version=(
            premeaning_inputs.stage1_response_schema_version
        ),
    )
    meaning_projection_fields_match = (
        premeaning_inputs.grounded_graph_ref == expected_graph_ref
        and premeaning_inputs.parent_observation_duty_ref
        == parent_plan.observation_duty_id
        and premeaning_inputs.interpretation_candidate_rows
        == expected_candidates
        and premeaning_inputs.meaning_field == expected_meaning_field
        and premeaning_inputs.observation_contribution_rows
        == expected_contributions
        and premeaning_inputs.ordered_observation_refs
        == expected_ordered_observation_refs
        and premeaning_inputs.observation_depth_class
        is expected_observation_depth
        and premeaning_inputs.material_unknown_refs
        == expected_meaning_field.material_unknown_refs
        and premeaning_inputs.source_qualifier_rows == expected_qualifier_rows
        and premeaning_inputs.source_relation_rows == expected_relation_rows
    )
    if not meaning_projection_fields_match:
        raise CMEEStage1ContractError(
            "foreground_scope_meaning_projection_noncanonical"
        )


def _validate_premeaning_source_qualifiers(
    *,
    interpretation_candidate_rows: Sequence[EmlisInterpretationCandidate],
    source_qualifiers_by_node_ref: Mapping[str, Tuple[str, ...]],
) -> None:
    for candidate in interpretation_candidate_rows:
        if candidate.relation_operator is RelationOperator.NO_RELATION_CLAIM:
            semantic_refs = tuple(dict.fromkeys(candidate.semantic_refs))
            if (
                len(semantic_refs) != 1
                or semantic_refs[0] not in source_qualifiers_by_node_ref
            ):
                raise CMEEStage1ContractError(
                    "foreground_scope_projection_qualifier_source_mismatch"
                )
            expected = _foreground_candidate_required_qualifiers(
                source_qualifiers_by_node_ref[semantic_refs[0]]
            )
        else:
            expected_values = ["epistemic:provisional_interpretation"]
            for binding in candidate.argument_bindings:
                qualifiers = source_qualifiers_by_node_ref.get(
                    binding.semantic_ref
                )
                if qualifiers is None:
                    raise CMEEStage1ContractError(
                        "foreground_scope_projection_qualifier_source_mismatch"
                    )
                qualifiers = _foreground_candidate_required_qualifiers(
                    qualifiers
                )
                role_prefix = f"{binding.role.value.lower()}_"
                expected_values.extend(
                    f"{role_prefix}{value}" for value in qualifiers[1:]
                )
            expected = tuple(expected_values)
        if candidate.required_qualifiers != expected:
            raise CMEEStage1ContractError(
                "foreground_scope_projection_qualifier_source_mismatch"
            )


def _validate_foreground_scope_basis_shape(
    row: ForegroundScopeBasisRow,
) -> None:
    if type(row) is not ForegroundScopeBasisRow:
        raise CMEEStage1ContractError("foreground_scope_basis_row_type_invalid")
    _validate_stage1_immutable_shape(row)
    if row.schema_version != _FOREGROUND_SCOPE_SCHEMA_VERSION:
        raise CMEEStage1ContractError(
            "foreground_scope_basis_schema_version_invalid"
        )
    if type(row.basis_kind) is not ForegroundScopeBasisKind:
        raise CMEEStage1ContractError("foreground_scope_basis_kind_invalid")
    for field_name in _FOREGROUND_SCOPE_TUPLE_FIELDS:
        _require_canonical_string_set(
            getattr(row, field_name),
            code=f"foreground_scope_basis_{field_name}_noncanonical",
            allow_empty=field_name not in {
                "scope_object_refs",
                "source_object_refs",
                "source_evidence_refs",
            },
        )
    for field_name in ("scope_object_refs", "source_object_refs"):
        for ref in getattr(row, field_name):
            validate_version_qualified_ref(
                ref,
                expected_types=("node", "edge"),
            )
    for ref in row.source_evidence_refs:
        validate_version_qualified_ref(ref, expected_types=("evidence",))
    if any(
        not ref.startswith("contribution-")
        for ref in row.layer1_required_object_refs
    ):
        raise CMEEStage1ContractError(
            "foreground_scope_basis_layer1_ref_namespace_invalid"
        )
    for ref in row.source_connected_relation_refs:
        validate_version_qualified_ref(ref, expected_types=("edge",))
    for ref in row.material_unknown_refs:
        _validate_typed_key(
            ref,
            allowed_prefixes=("unknown:",),
            code="foreground_scope_basis_unknown_ref_namespace_invalid",
        )
    for ref in row.required_qualifier_refs:
        _validate_typed_key(
            ref,
            allowed_prefixes=_QUALIFIER_PREFIXES,
            code="foreground_scope_basis_qualifier_ref_namespace_invalid",
        )
    for field_name, prefixes in (
        _FOREGROUND_SCOPE_COMPATIBILITY_FIELD_PREFIXES.items()
    ):
        for ref in getattr(row, field_name):
            _validate_typed_key(
                ref,
                allowed_prefixes=prefixes,
                code=f"foreground_scope_basis_{field_name}_namespace_invalid",
            )


def foreground_scope_basis_row_ref(row: ForegroundScopeBasisRow) -> str:
    """Return a trace-only canonical ref; callers must never rank by it."""

    _validate_foreground_scope_basis_shape(row)
    digest = hashlib.sha256(stage1_canonical_json_bytes(row)).hexdigest()
    return (
        f"foreground-scope-basis:{digest}"
        f"@{_FOREGROUND_SCOPE_BASIS_REF_VERSION}"
    )


def validate_foreground_scope_basis_row(
    row: ForegroundScopeBasisRow,
    *,
    premeaning_inputs: PreMeaningGroundedInputs,
    source: object,
    grounded_plan: object,
    grounded_graph: GroundedMeaningGraph,
    parent_plan: ExperiencePlan,
) -> None:
    """Validate a basis by deriving provenance from actual typed owners."""

    _validate_foreground_scope_basis_shape(row)
    if type(grounded_graph) is not GroundedMeaningGraph:
        raise CMEEStage1ContractError("foreground_scope_grounded_graph_invalid")
    validate_premeaning_grounded_inputs(
        premeaning_inputs,
        source=source,
        grounded_plan=grounded_plan,
        grounded_graph=grounded_graph,
        parent_plan=parent_plan,
    )
    source_qualifiers_by_node_ref = (
        _foreground_source_qualifiers_by_node_ref(
            source=source,
            grounded_plan=grounded_plan,
            grounded_graph=grounded_graph,
            parent_plan=parent_plan,
        )
    )
    _validate_premeaning_source_qualifiers(
        interpretation_candidate_rows=(
            premeaning_inputs.interpretation_candidate_rows
        ),
        source_qualifiers_by_node_ref=source_qualifiers_by_node_ref,
    )
    expected_graph_ref = (
        f"grounded:{grounded_graph.graph_id}"
        f"@{CMEE_GROUNDED_GRAPH_SCHEMA_VERSION}"
    )
    if premeaning_inputs.grounded_graph_ref != expected_graph_ref:
        raise CMEEStage1ContractError(
            "foreground_scope_projection_graph_ref_mismatch"
        )

    graph_objects = {
        **{_graph_object_ref(value): value for value in grounded_graph.nodes},
        **{_graph_object_ref(value): value for value in grounded_graph.edges},
    }
    if any(ref not in graph_objects for ref in row.source_object_refs):
        raise CMEEStage1ContractError(
            "foreground_scope_basis_source_object_refs_unbound"
        )
    if not set(row.scope_object_refs).issubset(row.source_object_refs):
        raise CMEEStage1ContractError(
            "foreground_scope_basis_scope_object_refs_unbound"
        )
    expected_evidence = {
        evidence_ref
        for ref in row.source_object_refs
        for evidence_ref in _graph_evidence_refs(
            graph_objects[ref],
            source_version=grounded_graph.source_version,
        )
    }
    expected_source_objects: Optional[set[str]] = None
    contributions = {
        value.contribution_id: value
        for value in premeaning_inputs.observation_contribution_rows
    }
    dedicated_fields = {
        "layer1_required_object_refs": row.layer1_required_object_refs,
        "required_retention_duty_refs": row.required_retention_duty_refs,
        "source_connected_relation_refs": row.source_connected_relation_refs,
        "material_unknown_refs": row.material_unknown_refs,
        "required_qualifier_refs": row.required_qualifier_refs,
    }

    if row.basis_kind is ForegroundScopeBasisKind.SOURCE_EXPLICIT_TARGET_TOPIC_OR_SCOPE:
        if any(dedicated_fields.values()):
            raise CMEEStage1ContractError(
                "foreground_scope_basis_source_explicit_mixed_basis_invalid"
            )
        required_owner_ids = set(grounded_graph.required_owner_refs)
        required_visible_claim_ids = {
            claim_id
            for disposition in grounded_graph.owner_dispositions
            if disposition.meaning_owner_id in required_owner_ids
            and disposition.owner_class is OwnerClass.REQUIRED
            and disposition.visible_authority
            is VisibleAuthority.SOURCE_EXPLICIT
            and disposition.source_owner_disposition
            is SourceOwnerDisposition.SOURCE_EXPLICIT_VISIBLE
            for claim_id in disposition.visible_claim_refs
        }
        target_topic_scope_refs = {
            ref
            for ref, value in graph_objects.items()
            if type(value) is MeaningNode
            and value.owner_id in required_owner_ids
            and value.node_id in required_visible_claim_ids
        }
        expected_source_objects = target_topic_scope_refs
        if (
            not expected_source_objects
            or any(
                type(graph_objects.get(ref)) is not MeaningNode
                or graph_objects[ref].epistemic_state
                is not EpistemicState.SOURCE_EXPLICIT
                for ref in expected_source_objects
            )
        ):
            raise CMEEStage1ContractError(
                "foreground_scope_basis_source_explicit_target_role_unbound"
            )
    elif row.basis_kind is ForegroundScopeBasisKind.LAYER1_REQUIRED_OBSERVATION_OBJECT:
        if not row.layer1_required_object_refs:
            raise CMEEStage1ContractError(
                "foreground_scope_basis_layer1_required_object_missing"
            )
        if any(
            ref not in contributions or contributions[ref].retention != "REQUIRED"
            for ref in row.layer1_required_object_refs
        ):
            raise CMEEStage1ContractError(
                "foreground_scope_basis_layer1_required_object_unbound"
            )
        if any(
            values
            for name, values in dedicated_fields.items()
            if name != "layer1_required_object_refs"
        ):
            raise CMEEStage1ContractError(
                "foreground_scope_basis_layer1_mixed_basis_invalid"
            )
        selected = tuple(
            contributions[ref] for ref in row.layer1_required_object_refs
        )
        expected_source_objects = {
            source_ref for value in selected for source_ref in value.semantic_refs
        }
        expected_evidence = {
            evidence_ref for value in selected for evidence_ref in value.evidence_refs
        }
    elif row.basis_kind is ForegroundScopeBasisKind.EXISTING_REQUIRED_RETENTION_DUTY:
        if not row.required_retention_duty_refs:
            raise CMEEStage1ContractError(
                "foreground_scope_basis_retention_duty_missing"
            )
        selected = tuple(
            value
            for value in contributions.values()
            if value.retention == "REQUIRED"
            and value.parent_duty_ref in row.required_retention_duty_refs
        )
        if not selected or {
            value.parent_duty_ref for value in selected
        } != set(row.required_retention_duty_refs):
            raise CMEEStage1ContractError(
                "foreground_scope_basis_retention_duty_unbound"
            )
        if any(
            values
            for name, values in dedicated_fields.items()
            if name != "required_retention_duty_refs"
        ):
            raise CMEEStage1ContractError(
                "foreground_scope_basis_retention_mixed_basis_invalid"
            )
        expected_source_objects = {
            source_ref for value in selected for source_ref in value.semantic_refs
        }
        expected_evidence = {
            evidence_ref for value in selected for evidence_ref in value.evidence_refs
        }
    elif row.basis_kind is ForegroundScopeBasisKind.SOURCE_CONNECTED_RELATION:
        if not row.source_connected_relation_refs:
            raise CMEEStage1ContractError(
                "foreground_scope_basis_source_connected_relation_missing"
            )
        selected_edges = tuple(
            graph_objects.get(ref) for ref in row.source_connected_relation_refs
        )
        if any(type(value) is not MeaningEdge for value in selected_edges):
            raise CMEEStage1ContractError(
                "foreground_scope_basis_source_connected_relation_unbound"
            )
        if any(
            value.epistemic_state is not EpistemicState.SOURCE_EXPLICIT
            or _foreground_enum_text(value.grounding_kind)
            != "user_stated_relation"
            or not value.evidence_ids
            or not any(
                disposition.meaning_owner_id == value.owner_id
                and disposition.visible_authority
                is VisibleAuthority.SOURCE_EXPLICIT
                and disposition.source_owner_disposition
                is SourceOwnerDisposition.SOURCE_EXPLICIT_VISIBLE
                and value.edge_id in disposition.visible_claim_refs
                for disposition in grounded_graph.owner_dispositions
            )
            for value in selected_edges
        ):
            raise CMEEStage1ContractError(
                "foreground_scope_basis_source_connected_relation_not_source_explicit"
            )
        if any(
            _graph_object_ref(value)
            not in {
                relation_row.relation_ref
                for relation_row in premeaning_inputs.source_relation_rows
            }
            for value in selected_edges
        ):
            raise CMEEStage1ContractError(
                "foreground_scope_basis_source_connected_relation_kind_invalid"
            )
        if any(
            values
            for name, values in dedicated_fields.items()
            if name != "source_connected_relation_refs"
        ):
            raise CMEEStage1ContractError(
                "foreground_scope_basis_relation_mixed_basis_invalid"
            )
        expected_source_objects = {
            _graph_object_ref(node)
            for edge in selected_edges
            for node in grounded_graph.nodes
            if node.node_id in {edge.source_node_id, edge.target_node_id}
        }
        if len(expected_source_objects) < 2:
            raise CMEEStage1ContractError(
                "foreground_scope_basis_relation_endpoint_missing"
            )
        expected_evidence = {
            evidence_ref
            for value in (
                *selected_edges,
                *(graph_objects[ref] for ref in expected_source_objects),
            )
            for evidence_ref in _graph_evidence_refs(
                value,
                source_version=grounded_graph.source_version,
            )
        }
    else:
        material_unknown_arm = bool(row.material_unknown_refs)
        required_qualifier_arm = bool(row.required_qualifier_refs)
        if material_unknown_arm == required_qualifier_arm:
            raise CMEEStage1ContractError(
                "foreground_scope_basis_unknown_or_qualifier_missing"
            )
        if (
            row.layer1_required_object_refs
            or row.required_retention_duty_refs
            or row.source_connected_relation_refs
        ):
            raise CMEEStage1ContractError(
                "foreground_scope_basis_unknown_or_qualifier_mixed_basis_invalid"
            )
        if required_qualifier_arm:
            if any(
                type(graph_objects.get(ref)) is not MeaningNode
                or ref not in source_qualifiers_by_node_ref
                for ref in row.source_object_refs
            ):
                raise CMEEStage1ContractError(
                    "foreground_scope_basis_required_qualifier_source_missing"
                )
            qualifier_candidate_matches = tuple(
                candidate
                for candidate in premeaning_inputs.interpretation_candidate_rows
                if set(candidate.semantic_refs) == set(row.source_object_refs)
                and set(candidate.required_qualifiers)
                == set(row.required_qualifier_refs)
            )
            if not qualifier_candidate_matches:
                raise CMEEStage1ContractError(
                    "foreground_scope_basis_required_qualifier_source_mismatch"
                )
            expected_source_objects = set(row.source_object_refs)
            expected_evidence = {
                evidence_ref
                for ref in expected_source_objects
                for evidence_ref in _graph_evidence_refs(
                    graph_objects[ref],
                    source_version=grounded_graph.source_version,
                )
            }
        else:
            expected_material_unknown_refs = set(
                _stage1_expected_material_unknown_refs(
                    grounded_graph,
                    parent_plan,
                )
            )
            if not set(row.material_unknown_refs).issubset(
                expected_material_unknown_refs
            ):
                raise CMEEStage1ContractError(
                    "foreground_scope_basis_material_unknown_unbound"
                )
            unknown_source_objects = {
                (
                    f"node:{disposition.target_unknown_ref}"
                    f"@{CMEE_GROUNDED_GRAPH_SCHEMA_VERSION}"
                )
                for disposition in grounded_graph.owner_dispositions
                if (
                    disposition.target_unknown_ref is not None
                    and (
                        f"unknown:{disposition.target_unknown_ref}"
                        f"@{grounded_graph.obligation_version}"
                    )
                    in row.material_unknown_refs
                )
            }
            expected_source_objects = unknown_source_objects
            if not expected_source_objects:
                raise CMEEStage1ContractError(
                    "foreground_scope_basis_unknown_or_qualifier_source_missing"
                )
            expected_evidence = {
                evidence_ref
                for ref in expected_source_objects
                for evidence_ref in _graph_evidence_refs(
                    graph_objects[ref],
                    source_version=grounded_graph.source_version,
                )
            }

    if expected_source_objects is not None and set(row.source_object_refs) != expected_source_objects:
        raise CMEEStage1ContractError(
            "foreground_scope_basis_source_object_reachability_mismatch"
        )
    if expected_source_objects is not None and set(row.scope_object_refs) != expected_source_objects:
        raise CMEEStage1ContractError(
            "foreground_scope_basis_scope_object_reachability_mismatch"
        )
    if set(row.source_evidence_refs) != expected_evidence:
        raise CMEEStage1ContractError(
            "foreground_scope_basis_source_evidence_reachability_mismatch"
        )

    expected_owner_refs = tuple(
        sorted(
            {
                f"owner:{graph_objects[ref].owner_id}"
                f"@{grounded_graph.obligation_version}"
                for ref in row.source_object_refs
            }
        )
    )
    if row.owner_refs != expected_owner_refs:
        raise CMEEStage1ContractError(
            "foreground_scope_basis_owner_refs_unbound"
        )
    expected_epistemic_refs = tuple(
        sorted(
            {
                f"epistemic-state:{graph_objects[ref].epistemic_state.value.lower()}"
                f"@{_FOREGROUND_SCOPE_BASIS_REF_VERSION}"
                for ref in row.source_object_refs
            }
        )
    )
    if row.epistemic_state_refs != expected_epistemic_refs:
        raise CMEEStage1ContractError(
            "foreground_scope_basis_epistemic_state_refs_unbound"
        )
    source_qualifier_universe = {
        qualifier
        for ref in row.source_object_refs
        for qualifier in source_qualifiers_by_node_ref.get(ref, ())
    }
    compatibility_sources = {
        "world_refs": {
            value
            for value in source_qualifier_universe
            if value.startswith("world:")
        },
        "time_refs": {
            value
            for value in source_qualifier_universe
            if value.startswith(("time:", "time_scope:"))
        },
        "aspect_refs": {
            value
            for value in source_qualifier_universe
            if value.startswith("aspect:")
        },
        "modality_refs": {
            value
            for value in source_qualifier_universe
            if value.startswith("modality:")
        },
        "polarity_refs": {
            value
            for value in source_qualifier_universe
            if value.startswith("polarity:")
        },
        "scope_refs": (
            {"scope:source_bounded"}
            if any(
                ref in source_qualifiers_by_node_ref
                for ref in row.source_object_refs
            )
            else set()
        ),
    }
    for field_name, expected in compatibility_sources.items():
        if set(getattr(row, field_name)) != expected:
            raise CMEEStage1ContractError(
                f"foreground_scope_basis_{field_name}_unbound"
            )


def _foreground_scope_identity_payload(scope: ForegroundScope) -> Mapping[str, Any]:
    return {
        row.name: getattr(scope, row.name)
        for row in dataclass_fields(scope)
        if row.name != "scope_id"
    }


def foreground_scope_id(scope: ForegroundScope) -> str:
    if type(scope) is not ForegroundScope:
        raise CMEEStage1ContractError("foreground_scope_type_invalid")
    digest = hashlib.sha256(
        stage1_canonical_json_bytes(_foreground_scope_identity_payload(scope))
    ).hexdigest()
    return f"foreground-scope:{digest}@{_FOREGROUND_SCOPE_REF_VERSION}"


def validate_foreground_scope(
    scope: ForegroundScope,
    *,
    basis_rows: Sequence[ForegroundScopeBasisRow],
    premeaning_inputs: PreMeaningGroundedInputs,
    source: object,
    grounded_plan: object,
    grounded_graph: GroundedMeaningGraph,
    parent_plan: ExperiencePlan,
) -> None:
    if type(scope) is not ForegroundScope:
        raise CMEEStage1ContractError("foreground_scope_type_invalid")
    _validate_stage1_immutable_shape(scope)
    if scope.schema_version != _FOREGROUND_SCOPE_SCHEMA_VERSION:
        raise CMEEStage1ContractError("foreground_scope_schema_version_invalid")
    for field_name in _STAGE1_TUPLE_FIELDS[ForegroundScope]:
        _require_canonical_string_set(
            getattr(scope, field_name),
            code=f"foreground_scope_{field_name}_noncanonical",
            allow_empty=field_name not in {
                "integrated_scope_object_refs",
                "basis_row_refs",
                "source_evidence_refs",
            },
        )
    if type(basis_rows) is not tuple:
        raise CMEEStage1ContractError(
            "foreground_scope_basis_rows_tuple_required"
        )
    rows = basis_rows
    if not rows:
        raise CMEEStage1ContractError("foreground_scope_basis_rows_empty")
    row_refs = tuple(foreground_scope_basis_row_ref(row) for row in rows)
    if len(row_refs) != len(set(row_refs)):
        raise CMEEStage1ContractError("foreground_scope_basis_rows_duplicate")
    for row in rows:
        validate_foreground_scope_basis_row(
            row,
            premeaning_inputs=premeaning_inputs,
            source=source,
            grounded_plan=grounded_plan,
            grounded_graph=grounded_graph,
            parent_plan=parent_plan,
        )
    expected = {
        "integrated_scope_object_refs": tuple(
            sorted({ref for row in rows for ref in row.scope_object_refs})
        ),
        "basis_row_refs": tuple(sorted(foreground_scope_basis_row_ref(row) for row in rows)),
        "source_connected_relation_refs": tuple(
            sorted({ref for row in rows for ref in row.source_connected_relation_refs})
        ),
        "required_retention_duty_refs": tuple(
            sorted({ref for row in rows for ref in row.required_retention_duty_refs})
        ),
        "material_unknown_refs": tuple(
            sorted({ref for row in rows for ref in row.material_unknown_refs})
        ),
        "required_qualifier_refs": tuple(
            sorted({ref for row in rows for ref in row.required_qualifier_refs})
        ),
        "source_evidence_refs": tuple(
            sorted({ref for row in rows for ref in row.source_evidence_refs})
        ),
    }
    if any(getattr(scope, name) != values for name, values in expected.items()):
        raise CMEEStage1ContractError("foreground_scope_canonical_union_mismatch")
    if scope.scope_id != foreground_scope_id(scope):
        raise CMEEStage1ContractError("foreground_scope_id_mismatch")


def validate_foreground_scope_derivation(
    derivation: ForegroundScopeDerivation,
    *,
    basis_rows: Sequence[ForegroundScopeBasisRow],
    premeaning_inputs: PreMeaningGroundedInputs,
    source: object,
    grounded_plan: object,
    grounded_graph: GroundedMeaningGraph,
    parent_plan: ExperiencePlan,
) -> None:
    if type(derivation) is not ForegroundScopeDerivation:
        raise CMEEStage1ContractError("foreground_scope_derivation_type_invalid")
    _validate_stage1_immutable_shape(derivation)
    if derivation.schema_version != _FOREGROUND_SCOPE_SCHEMA_VERSION:
        raise CMEEStage1ContractError(
            "foreground_scope_derivation_schema_version_invalid"
        )
    if type(derivation.state) is not ForegroundScopeDerivationState:
        raise CMEEStage1ContractError("foreground_scope_derivation_state_invalid")
    for field_name in _STAGE1_TUPLE_FIELDS[ForegroundScopeDerivation]:
        _require_canonical_string_set(
            getattr(derivation, field_name),
            code=f"foreground_scope_derivation_{field_name}_noncanonical",
        )
    if type(basis_rows) is not tuple:
        raise CMEEStage1ContractError(
            "foreground_scope_basis_rows_tuple_required"
        )
    rows = basis_rows
    state = derivation.state
    for row in rows:
        validate_foreground_scope_basis_row(
            row,
            premeaning_inputs=premeaning_inputs,
            source=source,
            grounded_plan=grounded_plan,
            grounded_graph=grounded_graph,
            parent_plan=parent_plan,
        )
    if type(derivation.foreground_scope) is ForegroundScope:
        validate_foreground_scope(
            derivation.foreground_scope,
            basis_rows=rows,
            premeaning_inputs=premeaning_inputs,
            source=source,
            grounded_plan=grounded_plan,
            grounded_graph=grounded_graph,
            parent_plan=parent_plan,
        )
    retained = tuple(
        sorted({ref for row in rows for ref in row.scope_object_refs})
    )
    evidence = tuple(
        sorted({ref for row in rows for ref in row.source_evidence_refs})
    )
    if state is ForegroundScopeDerivationState.FOREGROUND_SCOPE_AVAILABLE:
        valid = (
            type(derivation.foreground_scope) is ForegroundScope
            and derivation.retained_foreground_source_object_refs == retained
            and derivation.retained_foreground_source_object_refs
            == derivation.foreground_scope.integrated_scope_object_refs
            and not derivation.unresolved_scope_refs
            and not derivation.missing_structure_refs
            and derivation.derivation_evidence_refs == evidence
            and derivation.derivation_evidence_refs
            == derivation.foreground_scope.source_evidence_refs
        )
    elif state is ForegroundScopeDerivationState.COMPETING_MATERIAL_SCOPES:
        valid = (
            derivation.foreground_scope is None
            and bool(retained)
            and derivation.retained_foreground_source_object_refs == retained
            and bool(derivation.unresolved_scope_refs)
            and not derivation.missing_structure_refs
            and derivation.derivation_evidence_refs == evidence
        )
    elif state is ForegroundScopeDerivationState.FOREGROUND_SCOPE_STRUCTURE_INSUFFICIENT:
        valid = (
            derivation.foreground_scope is None
            and bool(retained)
            and derivation.retained_foreground_source_object_refs == retained
            and not derivation.unresolved_scope_refs
            and bool(derivation.missing_structure_refs)
            and derivation.derivation_evidence_refs == evidence
        )
    else:
        valid = (
            derivation.foreground_scope is None
            and not rows
            and not derivation.retained_foreground_source_object_refs
            and not derivation.unresolved_scope_refs
            and not derivation.missing_structure_refs
            and not derivation.derivation_evidence_refs
        )
    if not valid:
        raise CMEEStage1ContractError(
            "foreground_scope_derivation_state_cardinality_mismatch"
        )


def _validate_meaning_component_semantic_key(
    value: MeaningComponentSemanticKey,
) -> None:
    if type(value) is not MeaningComponentSemanticKey:
        raise CMEEStage1ContractError(
            "meaning_component_semantic_key_type_invalid"
        )
    _validate_stage1_immutable_shape(value)
    for field_name, prefixes in (
        ("typed_predicate_key", ("predicate:",)),
        ("semantic_kind_key", ("semantic-kind:",)),
        ("owner_key", ("owner:",)),
        ("scope_key", ("scope:",)),
        ("role_key", ("role:",)),
    ):
        _validate_typed_key(
            getattr(value, field_name),
            allowed_prefixes=prefixes,
            code=f"meaning_component_semantic_key_{field_name}_invalid",
        )


_MEANING_SIGNATURE_FIXED_KEYS_BY_FIELD = {
    "relation_direction_keys": frozenset(
        f"relation:{value.value}" for value in ForegroundScopeRelationKind
    ),
    "temporal_state_keys": frozenset(
        f"time:{value}" for value in _FOREGROUND_SOURCE_TIME_SCOPE_VALUES
    ),
    "resolution_treatment_keys": frozenset(
        {"resolution:resolved", "resolution:unresolved"}
    ),
    "world_or_owner_distinction_keys": frozenset(
        {
            "owner:other_actor",
            "owner:unknown",
            "world:internal",
            "world:external",
            "world:relationship",
            "world:unknown",
        }
    ),
    "modality_polarity_or_limitation_keys": frozenset(
        {
            "limitation:not_generalized",
            *(f"modality:{value}" for value in _FOREGROUND_SOURCE_MODALITY_VALUES),
            *(f"polarity:{value}" for value in _FOREGROUND_SOURCE_POLARITY_VALUES),
            "scope:bounded",
        }
    ),
    "episodicity_boundary_keys": frozenset(
        {"episodicity:general_pattern", "episodicity:one_off"}
    ),
    "qualifier_keys": frozenset(
        {"qualifier:not_generalized", "qualifier:unknown_preserved"}
    ),
}
_MEANING_SIGNATURE_COUNTERFACTUAL_KEYS_BY_CODE = {
    WholeReadingConsequenceCode.INPUT_CENTER_CHANGED: {
        "input_center_keys": frozenset(),
    },
    WholeReadingConsequenceCode.RELATION_STRUCTURE_CHANGED: {
        "component_role_keys": frozenset(),
        "relation_direction_keys": (
            _MEANING_SIGNATURE_FIXED_KEYS_BY_FIELD[
                "relation_direction_keys"
            ]
        ),
    },
    WholeReadingConsequenceCode.TEMPORAL_FLOW_CHANGED: {
        "temporal_state_keys": (
            _MEANING_SIGNATURE_FIXED_KEYS_BY_FIELD["temporal_state_keys"]
        ),
    },
    WholeReadingConsequenceCode.RESOLUTION_TREATMENT_CHANGED: {
        "resolution_treatment_keys": (
            _MEANING_SIGNATURE_FIXED_KEYS_BY_FIELD[
                "resolution_treatment_keys"
            ]
        ),
    },
    WholeReadingConsequenceCode.WORLD_OR_OWNER_DISTINCTION_CHANGED: {
        "world_or_owner_distinction_keys": (
            _MEANING_SIGNATURE_FIXED_KEYS_BY_FIELD[
                "world_or_owner_distinction_keys"
            ]
        ),
    },
    WholeReadingConsequenceCode.MODALITY_POLARITY_OR_LIMITATION_CHANGED: {
        "modality_polarity_or_limitation_keys": (
            _MEANING_SIGNATURE_FIXED_KEYS_BY_FIELD[
                "modality_polarity_or_limitation_keys"
            ]
        ),
        "qualifier_keys": _MEANING_SIGNATURE_FIXED_KEYS_BY_FIELD[
            "qualifier_keys"
        ],
    },
    WholeReadingConsequenceCode.EPISODICITY_BOUNDARY_CHANGED: {
        "episodicity_boundary_keys": (
            _MEANING_SIGNATURE_FIXED_KEYS_BY_FIELD[
                "episodicity_boundary_keys"
            ]
        ),
    },
}


def _meaning_semantic_signature_profiles(
    *,
    foreground_scope: ForegroundScope,
    source: object,
    grounded_plan: object,
    grounded_graph: GroundedMeaningGraph,
    premeaning_inputs: PreMeaningGroundedInputs,
    parent_plan: ExperiencePlan,
) -> Tuple[
    Tuple[
        Mapping[str, Tuple[str, ...]],
        Tuple[MeaningComponentSemanticKey, ...],
    ],
    ...,
]:
    """Build candidate-exact semantic profiles from canonical source frames."""

    node_by_ref = {
        _graph_object_ref(value): value for value in grounded_graph.nodes
    }
    edge_by_ref = {
        _graph_object_ref(value): value for value in grounded_graph.edges
    }
    source_qualifiers_by_node_ref = (
        _foreground_source_qualifiers_by_node_ref(
            source=source,
            grounded_plan=grounded_plan,
            grounded_graph=grounded_graph,
            parent_plan=parent_plan,
        )
    )
    _validate_premeaning_source_qualifiers(
        interpretation_candidate_rows=(
            premeaning_inputs.interpretation_candidate_rows
        ),
        source_qualifiers_by_node_ref=source_qualifiers_by_node_ref,
    )
    scoped_node_refs = {
        ref
        for ref in foreground_scope.integrated_scope_object_refs
        if ref in node_by_ref
    }
    for ref in foreground_scope.source_connected_relation_refs:
        edge = next(
            (
                value
                for value in grounded_graph.edges
                if _graph_object_ref(value) == ref
            ),
            None,
        )
        if edge is not None:
            scoped_node_refs.update(
                candidate_ref
                for candidate_ref, node in node_by_ref.items()
                if node.node_id in {edge.source_node_id, edge.target_node_id}
            )
    if not scoped_node_refs:
        raise CMEEStage1ContractError(
            "meaning_semantic_signature_scope_node_missing"
        )
    if any(
        node_by_ref[ref].node_kind not in _GROUNDED_MEANING_NODE_KIND_EXACT14
        for ref in scoped_node_refs
    ):
        raise CMEEStage1ContractError(
            "meaning_semantic_signature_node_kind_invalid"
        )

    expected_relation_refs = set(
        foreground_scope.source_connected_relation_refs
    )
    connected_candidates = tuple(
        candidate
        for candidate in premeaning_inputs.interpretation_candidate_rows
        if candidate.semantic_refs
        and set(candidate.semantic_refs).issubset(scoped_node_refs)
        and set(candidate.relation_basis_refs).issubset(
            expected_relation_refs
        )
    )
    profiles: list[
        tuple[
            Mapping[str, Tuple[str, ...]],
            Tuple[MeaningComponentSemanticKey, ...],
        ]
    ] = []
    for candidate in connected_candidates:
        components: set[MeaningComponentSemanticKey] = set()
        temporal_keys: set[str] = set()
        modality_keys: set[str] = {"scope:bounded"}
        owner_keys: set[str] = set()
        for binding in candidate.argument_bindings:
            qualifiers = source_qualifiers_by_node_ref.get(
                binding.semantic_ref
            )
            if qualifiers is None:
                raise CMEEStage1ContractError(
                    "meaning_semantic_signature_source_qualifier_missing"
                )
            qualifier_values = dict(
                value.split(":", 1) for value in qualifiers[1:]
            )
            node = node_by_ref[binding.semantic_ref]
            role_key = f"role:{binding.role.value.lower()}"
            owner_key = f"owner:{qualifier_values['actor']}"
            owner_keys.add(owner_key)
            temporal_keys.add(f"time:{qualifier_values['time_scope']}")
            modality_keys.update(
                {
                    f"modality:{qualifier_values['modality']}",
                    f"polarity:{qualifier_values['polarity']}",
                }
            )
            components.add(
                MeaningComponentSemanticKey(
                    typed_predicate_key=(
                        "predicate:"
                        f"{candidate.semantic_operator.value.lower()}"
                    ),
                    semantic_kind_key=(
                        f"semantic-kind:{node.node_kind.lower()}"
                    ),
                    owner_key=owner_key,
                    scope_key="scope:source_bounded",
                    role_key=role_key,
                )
            )
        if not components:
            continue
        canonical_components = tuple(
            sorted(components, key=stage1_canonical_json_bytes)
        )
        material_unknown_present = bool(
            foreground_scope.material_unknown_refs
        )
        world_or_owner_keys = set(owner_keys)
        resolution_keys: set[str] = set()
        qualifier_keys = {
            "qualifier:not_generalized",
            *(
                f"qualifier:{value.replace(':', '=', 1)}"
                for value in candidate.required_qualifiers
            ),
        }
        if material_unknown_present:
            world_or_owner_keys.add("world:unknown")
            resolution_keys.add("resolution:unresolved")
            qualifier_keys.add("qualifier:unknown_preserved")
        relation_keys = {
            f"relation:{relation_kind.value}"
            for ref in candidate.relation_basis_refs
            if ref in edge_by_ref
            for relation_kind in (
                project_foreground_scope_relation_kind(
                    edge_by_ref[ref].relation,
                    relation_operators=(candidate.relation_operator,),
                ),
            )
            if relation_kind is not None
        }
        first_binding = candidate.argument_bindings[0]
        profile = {
            "input_center_keys": (
                f"center:{node_by_ref[first_binding.semantic_ref].node_kind.lower()}",
            ),
            "component_role_keys": tuple(
                sorted({value.role_key for value in canonical_components})
            ),
            "relation_direction_keys": tuple(sorted(relation_keys)),
            "epistemic_state_keys": tuple(
                sorted(
                    {
                        f"epistemic:{node_by_ref[ref].epistemic_state.value.lower()}"
                        for ref in candidate.semantic_refs
                    }
                )
            ),
            "temporal_state_keys": tuple(sorted(temporal_keys)),
            "resolution_treatment_keys": tuple(
                sorted(resolution_keys)
            ),
            "world_or_owner_distinction_keys": tuple(
                sorted(world_or_owner_keys)
            ),
            "modality_polarity_or_limitation_keys": tuple(
                sorted(modality_keys)
            ),
            "episodicity_boundary_keys": (),
            "qualifier_keys": tuple(sorted(qualifier_keys)),
        }
        candidate_profile = (
            profile,
            canonical_components,
        )
        if candidate_profile not in profiles:
            profiles.append(candidate_profile)
    if not profiles:
        raise CMEEStage1ContractError(
            "meaning_semantic_signature_source_component_missing"
        )
    return tuple(profiles)


def validate_meaning_semantic_signature(
    signature: MeaningSemanticSignature,
    *,
    foreground_scope: ForegroundScope,
    basis_rows: Sequence[ForegroundScopeBasisRow],
    source: object,
    grounded_plan: object,
    grounded_graph: GroundedMeaningGraph,
    premeaning_inputs: PreMeaningGroundedInputs,
    parent_plan: ExperiencePlan,
) -> None:
    if type(signature) is not MeaningSemanticSignature:
        raise CMEEStage1ContractError("meaning_semantic_signature_type_invalid")
    _validate_stage1_immutable_shape(signature)
    if signature.schema_version != _FOREGROUND_SCOPE_SCHEMA_VERSION:
        raise CMEEStage1ContractError(
            "meaning_semantic_signature_schema_version_invalid"
        )
    if type(signature.reading_operation) is not MeaningReadingOperation:
        raise CMEEStage1ContractError(
            "meaning_semantic_signature_reading_operation_invalid"
        )
    validate_foreground_scope(
        foreground_scope,
        basis_rows=basis_rows,
        source=source,
        grounded_plan=grounded_plan,
        grounded_graph=grounded_graph,
        premeaning_inputs=premeaning_inputs,
        parent_plan=parent_plan,
    )
    profiles = _meaning_semantic_signature_profiles(
        foreground_scope=foreground_scope,
        source=source,
        grounded_plan=grounded_plan,
        grounded_graph=grounded_graph,
        premeaning_inputs=premeaning_inputs,
        parent_plan=parent_plan,
    )
    for field_name, prefixes in _SEMANTIC_SIGNATURE_PREFIXES_BY_FIELD.items():
        values = _require_canonical_string_set(
            getattr(signature, field_name),
            code=f"meaning_semantic_signature_{field_name}_noncanonical",
        )
        for value in values:
            _validate_typed_key(
                value,
                allowed_prefixes=prefixes,
                code=f"meaning_semantic_signature_{field_name}_invalid",
            )
    components = signature.component_semantic_keys
    if (
        len(components) != len(set(components))
        or components
        != tuple(sorted(components, key=stage1_canonical_json_bytes))
    ):
        raise CMEEStage1ContractError(
            "meaning_semantic_signature_component_semantic_keys_noncanonical"
        )
    for value in components:
        _validate_meaning_component_semantic_key(value)
    matching_profiles = tuple(
        profile
        for profile in profiles
        if components == profile[1]
        and all(
            getattr(signature, field_name) == profile[0][field_name]
            for field_name in _SEMANTIC_SIGNATURE_PREFIXES_BY_FIELD
        )
    )
    if len(matching_profiles) != 1:
        raise CMEEStage1ContractError(
            "meaning_semantic_signature_source_exact_cover_mismatch"
        )
    expected_component_role_keys = tuple(
        sorted({value.role_key for value in components})
    )
    if signature.component_role_keys != expected_component_role_keys:
        raise CMEEStage1ContractError(
            "meaning_semantic_signature_component_role_unbound"
        )
    expected_component_owner_keys = tuple(
        sorted({value.owner_key for value in components})
    )
    signature_owner_keys = tuple(
        value
        for value in signature.world_or_owner_distinction_keys
        if value.startswith("owner:")
    )
    if signature_owner_keys != expected_component_owner_keys:
        raise CMEEStage1ContractError(
            "meaning_semantic_signature_component_owner_unbound"
        )
    if not signature.input_center_keys or not components:
        raise CMEEStage1ContractError(
            "meaning_semantic_signature_content_bearing_keys_missing"
        )


def _meaning_qualifier_parts(
    value: str,
) -> Optional[tuple[Optional[str], str, str]]:
    if not value.startswith("qualifier:") or "=" not in value:
        return None
    body, qualifier_value = value.removeprefix("qualifier:").split("=", 1)
    axes = {
        "actor",
        "world",
        "aspect",
        "modality",
        "polarity",
        "time_scope",
    }
    if body in axes:
        return None, body, qualifier_value
    for role in ArgumentRole:
        role_key = role.value.lower()
        prefix = f"{role_key}_"
        if body.startswith(prefix):
            axis = body.removeprefix(prefix)
            if axis in axes:
                return role_key, axis, qualifier_value
    return None


def _meaning_role_qualifier_parts(
    value: str,
) -> Optional[tuple[str, str, str]]:
    parts = _meaning_qualifier_parts(value)
    if parts is None or parts[0] is None:
        return None
    role, axis, qualifier_value = parts
    return role, axis, qualifier_value


def _meaning_relation_qualifiers_for_roles(
    qualifier_keys: Sequence[str],
    *,
    retained_roles: set[str],
) -> Tuple[str, ...]:
    return tuple(
        sorted(
            value
            for value in qualifier_keys
            if (
                (parts := _meaning_role_qualifier_parts(value)) is None
                or parts[0] in retained_roles
            )
        )
    )


def _meaning_relation_role_swapped_qualifiers(
    qualifier_keys: Sequence[str],
) -> Tuple[str, ...]:
    role_swap = {"left": "right", "right": "left"}
    swapped: list[str] = []
    for value in qualifier_keys:
        parts = _meaning_role_qualifier_parts(value)
        if parts is None or parts[0] not in role_swap:
            swapped.append(value)
            continue
        role, axis, qualifier_value = parts
        swapped.append(
            f"qualifier:{role_swap[role]}_{axis}={qualifier_value}"
        )
    return tuple(sorted(swapped))


def _meaning_endpoint_retained_summaries(
    baseline: MeaningSemanticSignature,
    retained_qualifiers: Sequence[str],
) -> tuple[Tuple[str, ...], Tuple[str, ...]]:
    baseline_parts = tuple(
        parts
        for value in baseline.qualifier_keys
        if (parts := _meaning_role_qualifier_parts(value)) is not None
    )
    retained_parts = tuple(
        parts
        for value in retained_qualifiers
        if (parts := _meaning_role_qualifier_parts(value)) is not None
    )
    temporal = set(baseline.temporal_state_keys)
    temporal.difference_update(
        f"time:{value}" for _role, axis, value in baseline_parts
        if axis == "time_scope"
    )
    temporal.update(
        f"time:{value}" for _role, axis, value in retained_parts
        if axis == "time_scope"
    )
    modality = set(baseline.modality_polarity_or_limitation_keys)
    modality.difference_update(
        f"{axis}:{value}" for _role, axis, value in baseline_parts
        if axis in {"modality", "polarity"}
    )
    modality.update(
        f"{axis}:{value}" for _role, axis, value in retained_parts
        if axis in {"modality", "polarity"}
    )
    return tuple(sorted(temporal)), tuple(sorted(modality))


def _meaning_owner_substituted_qualifiers(
    qualifier_keys: Sequence[str],
    *,
    baseline_components: Sequence[MeaningComponentSemanticKey],
    mutated_components: Sequence[MeaningComponentSemanticKey],
) -> Optional[Tuple[str, ...]]:
    def component_shape(
        value: MeaningComponentSemanticKey,
    ) -> tuple[str, str, str, str]:
        return (
            value.typed_predicate_key,
            value.semantic_kind_key,
            value.scope_key,
            value.role_key,
        )

    def semantic_group(
        shape: tuple[str, str, str, str],
    ) -> tuple[str, str, str]:
        return shape[:3]

    baseline_owner_by_shape = {
        component_shape(value): value.owner_key.removeprefix("owner:")
        for value in baseline_components
    }
    mutated_owner_by_shape = {
        component_shape(value): value.owner_key.removeprefix("owner:")
        for value in mutated_components
    }
    if set(mutated_owner_by_shape) != set(baseline_owner_by_shape):
        return None
    changed_shapes = {
        shape
        for shape, owner in baseline_owner_by_shape.items()
        if mutated_owner_by_shape[shape] != owner
    }
    changed_groups = {semantic_group(shape) for shape in changed_shapes}
    if len(changed_groups) != 1:
        return None
    has_unscoped_actor_qualifier = any(
        parts is not None and parts[:2] == (None, "actor")
        for value in qualifier_keys
        if (parts := _meaning_qualifier_parts(value)) is not None
    )
    if len(changed_shapes) != 1 and not has_unscoped_actor_qualifier:
        return None
    changed_group = next(iter(changed_groups))
    changed_roles = {
        shape[3].removeprefix("role:") for shape in changed_shapes
    }
    mutated_owner_by_role: dict[str, str] = {}
    for shape in changed_shapes:
        role = shape[3].removeprefix("role:")
        owner = mutated_owner_by_shape[shape]
        if (
            role in mutated_owner_by_role
            and mutated_owner_by_role[role] != owner
        ):
            return None
        mutated_owner_by_role[role] = owner
    group_shapes = {
        shape
        for shape in baseline_owner_by_shape
        if semantic_group(shape) == changed_group
    }
    group_new_owners = {
        mutated_owner_by_shape[shape] for shape in group_shapes
    }
    changed_qualifier_roles: set[str] = set()
    unscoped_actor_covered = False
    expected: list[str] = []
    for value in qualifier_keys:
        parts = _meaning_qualifier_parts(value)
        if (
            parts is not None
            and parts[0] is not None
            and parts[1] == "actor"
            and parts[0] in changed_roles
        ):
            role, axis, _owner = parts
            expected.append(
                f"qualifier:{role}_{axis}={mutated_owner_by_role[role]}"
            )
            changed_qualifier_roles.add(role)
        elif (
            parts is not None
            and parts[0] is None
            and parts[1] == "actor"
            and changed_shapes == group_shapes
            and len(group_new_owners) == 1
        ):
            expected.append(
                f"qualifier:actor={next(iter(group_new_owners))}"
            )
            unscoped_actor_covered = True
        else:
            expected.append(value)
    if not (
        changed_qualifier_roles == changed_roles
        or (unscoped_actor_covered and not changed_qualifier_roles)
    ):
        return None
    return tuple(sorted(expected))


def _meaning_modality_qualifier_mutation_is_coherent(
    baseline: MeaningSemanticSignature,
    mutated: MeaningSemanticSignature,
) -> bool:
    baseline_qualifiers = set(baseline.qualifier_keys)
    mutated_qualifiers = set(mutated.qualifier_keys)
    removed = baseline_qualifiers - mutated_qualifiers
    added = mutated_qualifiers - baseline_qualifiers
    if len(removed) == len(added) == 1:
        removed_parts = _meaning_qualifier_parts(next(iter(removed)))
        added_parts = _meaning_qualifier_parts(next(iter(added)))
        if (
            removed_parts is not None
            and added_parts is not None
            and removed_parts[:2] == added_parts[:2]
            and removed_parts[1] in {"modality", "polarity"}
        ):
            _role, axis, old_value = removed_parts
            _new_role, _new_axis, new_value = added_parts
            closed_values = (
                _FOREGROUND_SOURCE_MODALITY_VALUES
                if axis == "modality"
                else _FOREGROUND_SOURCE_POLARITY_VALUES
            )
            if new_value not in closed_values or new_value == old_value:
                return False
            expected_summary = set(
                baseline.modality_polarity_or_limitation_keys
            )
            old_key = f"{axis}:{old_value}"
            old_still_used = any(
                (parts := _meaning_qualifier_parts(value)) is not None
                and parts[1:] == (axis, old_value)
                for value in mutated_qualifiers
            )
            if not old_still_used:
                expected_summary.discard(old_key)
            expected_summary.add(f"{axis}:{new_value}")
            return mutated.modality_polarity_or_limitation_keys == tuple(
                sorted(expected_summary)
            )
    fixed_qualifiers = {"qualifier:not_generalized"}
    if (
        len(removed) + len(added) == 1
        and (removed | added).issubset(fixed_qualifiers)
    ):
        return (
            mutated.modality_polarity_or_limitation_keys
            == baseline.modality_polarity_or_limitation_keys
        )
    return False


def _meaning_temporal_qualifier_mutation_is_coherent(
    baseline: MeaningSemanticSignature,
    mutated: MeaningSemanticSignature,
) -> bool:
    baseline_qualifiers = set(baseline.qualifier_keys)
    mutated_qualifiers = set(mutated.qualifier_keys)
    removed = baseline_qualifiers - mutated_qualifiers
    added = mutated_qualifiers - baseline_qualifiers
    if len(removed) != 1 or len(added) != 1:
        return False
    removed_parts = _meaning_qualifier_parts(next(iter(removed)))
    added_parts = _meaning_qualifier_parts(next(iter(added)))
    if (
        removed_parts is None
        or added_parts is None
        or removed_parts[:2] != added_parts[:2]
        or removed_parts[1] != "time_scope"
    ):
        return False
    _role, _axis, old_value = removed_parts
    _new_role, _new_axis, new_value = added_parts
    if (
        new_value not in _FOREGROUND_SOURCE_TIME_SCOPE_VALUES
        or new_value == old_value
    ):
        return False
    expected_summary = set(baseline.temporal_state_keys)
    old_still_used = any(
        (parts := _meaning_qualifier_parts(value)) is not None
        and parts[1:] == ("time_scope", old_value)
        for value in mutated_qualifiers
    )
    if not old_still_used:
        expected_summary.discard(f"time:{old_value}")
    expected_summary.add(f"time:{new_value}")
    return mutated.temporal_state_keys == tuple(sorted(expected_summary))


def _validate_counterfactual_meaning_semantic_signature(
    signature: MeaningSemanticSignature,
    *,
    baseline_semantic_signature: MeaningSemanticSignature,
    consequence_code: WholeReadingConsequenceCode,
    foreground_scope: ForegroundScope,
    basis_rows: Sequence[ForegroundScopeBasisRow],
    source: object,
    grounded_plan: object,
    grounded_graph: GroundedMeaningGraph,
    premeaning_inputs: PreMeaningGroundedInputs,
    parent_plan: ExperiencePlan,
) -> None:
    """Validate one code-gated mutation without widening baseline meaning."""

    if type(consequence_code) is not WholeReadingConsequenceCode:
        raise CMEEStage1ContractError(
            "meaning_semantic_signature_counterfactual_code_invalid"
        )
    source_validation = {
        "foreground_scope": foreground_scope,
        "basis_rows": basis_rows,
        "source": source,
        "grounded_plan": grounded_plan,
        "grounded_graph": grounded_graph,
        "premeaning_inputs": premeaning_inputs,
        "parent_plan": parent_plan,
    }
    validate_meaning_semantic_signature(
        baseline_semantic_signature,
        **source_validation,
    )
    if type(signature) is not MeaningSemanticSignature:
        raise CMEEStage1ContractError("meaning_semantic_signature_type_invalid")
    _validate_stage1_immutable_shape(signature)
    if signature.schema_version != _FOREGROUND_SCOPE_SCHEMA_VERSION:
        raise CMEEStage1ContractError(
            "meaning_semantic_signature_schema_version_invalid"
        )
    if (
        type(signature.reading_operation) is not MeaningReadingOperation
        or signature.reading_operation
        is not baseline_semantic_signature.reading_operation
    ):
        raise CMEEStage1ContractError(
            "meaning_semantic_signature_counterfactual_axis_mismatch"
        )
    profiles = _meaning_semantic_signature_profiles(
        foreground_scope=foreground_scope,
        source=source,
        grounded_plan=grounded_plan,
        grounded_graph=grounded_graph,
        premeaning_inputs=premeaning_inputs,
        parent_plan=parent_plan,
    )
    registry = {
        field_name: frozenset(
            value
            for profile, _components in profiles
            for value in profile[field_name]
        )
        for field_name in _SEMANTIC_SIGNATURE_PREFIXES_BY_FIELD
    }
    scoped_node_by_ref = {
        _graph_object_ref(value): value for value in grounded_graph.nodes
    }
    registry["input_center_keys"] = frozenset(
        {
            *registry["input_center_keys"],
            *(
                f"center:{scoped_node_by_ref[ref].node_kind.lower()}"
                for ref in foreground_scope.integrated_scope_object_refs
                if ref in scoped_node_by_ref
            ),
        }
    )
    counterfactual_registry = (
        _MEANING_SIGNATURE_COUNTERFACTUAL_KEYS_BY_CODE[consequence_code]
    )
    correlated_delta_fields = {
        "qualifier_keys",
        *(
            {
                "temporal_state_keys",
                "modality_polarity_or_limitation_keys",
            }
            if consequence_code
            is WholeReadingConsequenceCode.RELATION_STRUCTURE_CHANGED
            else set()
        ),
    }
    qualifier_is_correlated_delta = consequence_code in {
        WholeReadingConsequenceCode.RELATION_STRUCTURE_CHANGED,
        WholeReadingConsequenceCode.TEMPORAL_FLOW_CHANGED,
        WholeReadingConsequenceCode.WORLD_OR_OWNER_DISTINCTION_CHANGED,
        WholeReadingConsequenceCode.MODALITY_POLARITY_OR_LIMITATION_CHANGED,
        WholeReadingConsequenceCode.EPISODICITY_BOUNDARY_CHANGED,
    }
    for field_name, prefixes in _SEMANTIC_SIGNATURE_PREFIXES_BY_FIELD.items():
        values = _require_canonical_string_set(
            getattr(signature, field_name),
            code=f"meaning_semantic_signature_{field_name}_noncanonical",
        )
        for value in values:
            _validate_typed_key(
                value,
                allowed_prefixes=prefixes,
                code=f"meaning_semantic_signature_{field_name}_invalid",
            )
        if (
            field_name not in counterfactual_registry
            and not (
                field_name in correlated_delta_fields
                and qualifier_is_correlated_delta
            )
            and values != getattr(baseline_semantic_signature, field_name)
        ):
            raise CMEEStage1ContractError(
                "meaning_semantic_signature_counterfactual_axis_mismatch"
            )
        allowed_values = set(registry[field_name]) | set(
            counterfactual_registry.get(field_name, ())
        )
        if (
            not (
                field_name in correlated_delta_fields
                and qualifier_is_correlated_delta
            )
            and not set(values).issubset(allowed_values)
        ):
            raise CMEEStage1ContractError(
                f"meaning_semantic_signature_{field_name}_counterfactual_unbound"
            )
    components = signature.component_semantic_keys
    if (
        len(components) != len(set(components))
        or components
        != tuple(sorted(components, key=stage1_canonical_json_bytes))
    ):
        raise CMEEStage1ContractError(
            "meaning_semantic_signature_component_semantic_keys_noncanonical"
        )
    for value in components:
        _validate_meaning_component_semantic_key(value)
    baseline_components = baseline_semantic_signature.component_semantic_keys
    component_mutation_valid = components == baseline_components
    if consequence_code is WholeReadingConsequenceCode.RELATION_STRUCTURE_CHANGED:
        role_swap = {"role:left": "role:right", "role:right": "role:left"}
        swapped_components = tuple(
            sorted(
                (
                    replace(
                        value,
                        role_key=role_swap.get(value.role_key, value.role_key),
                    )
                    for value in baseline_components
                ),
                key=stage1_canonical_json_bytes,
            )
        )
        relation_kind_only = (
            components == baseline_components
            and len(baseline_semantic_signature.relation_direction_keys) == 1
            and len(signature.relation_direction_keys) == 1
            and signature.component_role_keys
            == baseline_semantic_signature.component_role_keys
            and signature.qualifier_keys
            == baseline_semantic_signature.qualifier_keys
            and signature.temporal_state_keys
            == baseline_semantic_signature.temporal_state_keys
            and signature.modality_polarity_or_limitation_keys
            == baseline_semantic_signature.modality_polarity_or_limitation_keys
            and signature.relation_direction_keys
            != baseline_semantic_signature.relation_direction_keys
        )
        role_swap_only = (
            components == swapped_components
            and components != baseline_components
            and signature.relation_direction_keys
            == baseline_semantic_signature.relation_direction_keys
            and signature.qualifier_keys
            == _meaning_relation_role_swapped_qualifiers(
                baseline_semantic_signature.qualifier_keys
            )
            and signature.temporal_state_keys
            == baseline_semantic_signature.temporal_state_keys
            and signature.modality_polarity_or_limitation_keys
            == baseline_semantic_signature.modality_polarity_or_limitation_keys
        )
        removed_components = set(baseline_components) - set(components)
        retained_roles = {
            value.role_key.removeprefix("role:") for value in components
        }
        retained_qualifiers = _meaning_relation_qualifiers_for_roles(
            baseline_semantic_signature.qualifier_keys,
            retained_roles=retained_roles,
        )
        retained_temporal, retained_modality = (
            _meaning_endpoint_retained_summaries(
                baseline_semantic_signature,
                retained_qualifiers,
            )
        )
        endpoint_delete_only = (
            bool(components)
            and set(components).issubset(set(baseline_components))
            and len(removed_components) == 1
            and signature.qualifier_keys == retained_qualifiers
            and signature.temporal_state_keys == retained_temporal
            and signature.modality_polarity_or_limitation_keys
            == retained_modality
            and (
                signature.relation_direction_keys
                == baseline_semantic_signature.relation_direction_keys
                or (
                    len(components) < 2 or len(retained_roles) < 2
                )
                and signature.relation_direction_keys == ()
            )
        )
        component_mutation_valid = (
            relation_kind_only or role_swap_only or endpoint_delete_only
        )
    elif consequence_code is WholeReadingConsequenceCode.INPUT_CENTER_CHANGED:
        component_mutation_valid = (
            components == baseline_components
            and len(signature.input_center_keys) == 1
        )
    elif consequence_code is WholeReadingConsequenceCode.WORLD_OR_OWNER_DISTINCTION_CHANGED:
        def component_owner_shape(
            value: MeaningComponentSemanticKey,
        ) -> tuple[str, str, str, str]:
            return (
                value.typed_predicate_key,
                value.semantic_kind_key,
                value.scope_key,
                value.role_key,
            )

        baseline_by_shape = {
            component_owner_shape(value): value.owner_key
            for value in baseline_components
        }
        mutated_by_shape = {
            component_owner_shape(value): value.owner_key
            for value in components
        }
        closed_owner_keys = {
            *baseline_by_shape.values(),
            "owner:other_actor",
            "owner:unknown",
        }
        changed_owner_shapes = {
            shape
            for shape, owner in baseline_by_shape.items()
            if mutated_by_shape.get(shape) != owner
        }
        changed_owner_groups = {
            shape[:3] for shape in changed_owner_shapes
        }
        expected_owner_qualifiers = _meaning_owner_substituted_qualifiers(
            baseline_semantic_signature.qualifier_keys,
            baseline_components=baseline_components,
            mutated_components=components,
        )
        owner_substitution_only = (
            len(baseline_by_shape) == len(baseline_components)
            and len(mutated_by_shape) == len(components)
            and set(mutated_by_shape) == set(baseline_by_shape)
            and set(mutated_by_shape.values()).issubset(closed_owner_keys)
            and len(changed_owner_groups) == 1
            and expected_owner_qualifiers is not None
            and signature.qualifier_keys == expected_owner_qualifiers
            and tuple(
                value
                for value in signature.world_or_owner_distinction_keys
                if value.startswith("world:")
            )
            == tuple(
                value
                for value in baseline_semantic_signature.world_or_owner_distinction_keys
                if value.startswith("world:")
            )
        )
        world_substitution_only = (
            components == baseline_components
            and signature.qualifier_keys
            == baseline_semantic_signature.qualifier_keys
            and tuple(
                value
                for value in signature.world_or_owner_distinction_keys
                if value.startswith("owner:")
            )
            == tuple(
                value
                for value in baseline_semantic_signature.world_or_owner_distinction_keys
                if value.startswith("owner:")
            )
            and signature.world_or_owner_distinction_keys
            != baseline_semantic_signature.world_or_owner_distinction_keys
            and len(
                tuple(
                    value
                    for value in signature.world_or_owner_distinction_keys
                    if value.startswith("world:")
                )
            )
            <= 1
        )
        component_mutation_valid = owner_substitution_only or world_substitution_only
    elif consequence_code is WholeReadingConsequenceCode.TEMPORAL_FLOW_CHANGED:
        component_mutation_valid = (
            components == baseline_components
            and _meaning_temporal_qualifier_mutation_is_coherent(
                baseline_semantic_signature,
                signature,
            )
        )
    elif (
        consequence_code
        is WholeReadingConsequenceCode.MODALITY_POLARITY_OR_LIMITATION_CHANGED
    ):
        component_mutation_valid = (
            components == baseline_components
            and _meaning_modality_qualifier_mutation_is_coherent(
                baseline_semantic_signature,
                signature,
            )
        )
    elif consequence_code is WholeReadingConsequenceCode.RESOLUTION_TREATMENT_CHANGED:
        component_mutation_valid = (
            components == baseline_components
            and len(signature.resolution_treatment_keys) == 1
        )
    elif consequence_code is WholeReadingConsequenceCode.EPISODICITY_BOUNDARY_CHANGED:
        episodicity = signature.episodicity_boundary_keys
        expected_qualifiers = baseline_semantic_signature.qualifier_keys
        if episodicity == ("episodicity:general_pattern",):
            expected_qualifiers = tuple(
                value
                for value in expected_qualifiers
                if value != "qualifier:not_generalized"
            )
        component_mutation_valid = (
            components == baseline_components
            and len(episodicity) == 1
            and signature.qualifier_keys == expected_qualifiers
        )
    if not component_mutation_valid:
        raise CMEEStage1ContractError(
            "meaning_semantic_signature_counterfactual_axis_mismatch"
        )
    expected_component_role_keys = tuple(
        sorted({value.role_key for value in components})
    )
    if signature.component_role_keys != expected_component_role_keys:
        raise CMEEStage1ContractError(
            "meaning_semantic_signature_component_role_unbound"
        )
    expected_component_owner_keys = tuple(
        sorted({value.owner_key for value in components})
    )
    signature_owner_keys = tuple(
        value
        for value in signature.world_or_owner_distinction_keys
        if value.startswith("owner:")
    )
    if signature_owner_keys != expected_component_owner_keys:
        raise CMEEStage1ContractError(
            "meaning_semantic_signature_component_owner_unbound"
        )
    component_semantic_kinds = {
        value.semantic_kind_key.removeprefix("semantic-kind:")
        for value in components
    }
    center_semantic_kinds = {
        value.removeprefix("center:")
        for value in signature.input_center_keys
    }
    if not center_semantic_kinds.issubset(component_semantic_kinds):
        raise CMEEStage1ContractError(
            "meaning_semantic_signature_center_component_unbound"
        )
    if signature.relation_direction_keys and (
        len(components) < 2 or len(expected_component_role_keys) < 2
    ):
        raise CMEEStage1ContractError(
            "meaning_semantic_signature_relation_endpoint_cardinality_unbound"
        )
    if not signature.input_center_keys or not components:
        raise CMEEStage1ContractError(
            "meaning_semantic_signature_content_bearing_keys_missing"
        )


def _whole_reading_consequence_identity_payload(
    row: WholeReadingConsequenceRow,
) -> Mapping[str, Any]:
    return {
        value.name: getattr(row, value.name)
        for value in dataclass_fields(row)
        if value.name != "consequence_id"
    }


def whole_reading_consequence_id(row: WholeReadingConsequenceRow) -> str:
    if type(row) is not WholeReadingConsequenceRow:
        raise CMEEStage1ContractError(
            "whole_reading_consequence_row_type_invalid"
        )
    digest = hashlib.sha256(
        stage1_canonical_json_bytes(
            _whole_reading_consequence_identity_payload(row)
        )
    ).hexdigest()
    return (
        f"whole-reading-consequence:{digest}"
        f"@{_WHOLE_READING_CONSEQUENCE_REF_VERSION}"
    )


def _validate_whole_reading_context(
    context: WholeReadingConsequenceValidationContext,
    *,
    consequence_code: WholeReadingConsequenceCode,
    basis_rows: Sequence[ForegroundScopeBasisRow],
    source: object,
    grounded_plan: object,
    grounded_graph: GroundedMeaningGraph,
    premeaning_inputs: PreMeaningGroundedInputs,
    parent_plan: ExperiencePlan,
) -> None:
    if type(context) is not WholeReadingConsequenceValidationContext:
        raise CMEEStage1ContractError(
            "whole_reading_consequence_context_type_invalid"
        )
    _validate_stage1_immutable_shape(context)
    if context.schema_version != _FOREGROUND_SCOPE_SCHEMA_VERSION:
        raise CMEEStage1ContractError(
            "whole_reading_consequence_context_schema_version_invalid"
        )
    validate_foreground_scope(
        context.foreground_scope,
        basis_rows=basis_rows,
        source=source,
        grounded_plan=grounded_plan,
        grounded_graph=grounded_graph,
        premeaning_inputs=premeaning_inputs,
        parent_plan=parent_plan,
    )
    validate_version_qualified_ref(
        context.required_difference_ref,
        expected_types=("required-difference",),
    )
    validate_version_qualified_ref(
        context.counterfactual_mutation_ref,
        expected_types=("counterfactual-mutation",),
    )
    if not context.required_difference_ref.endswith(
        f"@{_REQUIRED_DIFFERENCE_REF_VERSION}"
    ):
        raise CMEEStage1ContractError(
            "whole_reading_consequence_required_difference_version_invalid"
        )
    if not context.counterfactual_mutation_ref.endswith(
        f"@{_COUNTERFACTUAL_MUTATION_REF_VERSION}"
    ):
        raise CMEEStage1ContractError(
            "whole_reading_consequence_mutation_version_invalid"
        )
    evidence = _require_canonical_string_set(
        context.source_evidence_refs,
        code="whole_reading_consequence_context_evidence_noncanonical",
        allow_empty=False,
    )
    graph_evidence = {
        ref
        for value in (*grounded_graph.nodes, *grounded_graph.edges)
        for ref in _graph_evidence_refs(
            value,
            source_version=grounded_graph.source_version,
        )
    }
    if not set(evidence).issubset(graph_evidence) or not set(evidence).issubset(
        context.foreground_scope.source_evidence_refs
    ):
        raise CMEEStage1ContractError(
            "whole_reading_consequence_context_evidence_unbound"
        )
    signature_validation = {
        "foreground_scope": context.foreground_scope,
        "basis_rows": basis_rows,
        "source": source,
        "grounded_plan": grounded_plan,
        "grounded_graph": grounded_graph,
        "premeaning_inputs": premeaning_inputs,
        "parent_plan": parent_plan,
    }
    validate_meaning_semantic_signature(
        context.baseline_semantic_signature,
        **signature_validation,
    )
    _validate_counterfactual_meaning_semantic_signature(
        context.mutated_semantic_signature,
        baseline_semantic_signature=context.baseline_semantic_signature,
        consequence_code=consequence_code,
        **signature_validation,
    )
    if context.baseline_semantic_signature == context.mutated_semantic_signature:
        raise CMEEStage1ContractError(
            "whole_reading_consequence_semantic_change_missing"
        )


def validate_whole_reading_consequence_row(
    row: WholeReadingConsequenceRow,
    *,
    binding_context: WholeReadingConsequenceValidationContext,
    foreground_scope_basis_rows: Sequence[ForegroundScopeBasisRow],
    source: object,
    grounded_plan: object,
    grounded_graph: GroundedMeaningGraph,
    premeaning_inputs: PreMeaningGroundedInputs,
    parent_plan: ExperiencePlan,
) -> None:
    """Bind a closed whole-reading delta to typed IM00 provenance owners."""

    if type(row) is not WholeReadingConsequenceRow:
        raise CMEEStage1ContractError(
            "whole_reading_consequence_row_type_invalid"
        )
    _validate_stage1_immutable_shape(row)
    if row.schema_version != _FOREGROUND_SCOPE_SCHEMA_VERSION:
        raise CMEEStage1ContractError(
            "whole_reading_consequence_schema_version_invalid"
        )
    if type(row.consequence_code) is not WholeReadingConsequenceCode:
        raise CMEEStage1ContractError(
            "whole_reading_consequence_code_invalid"
        )
    _require_canonical_string_set(
        row.source_evidence_refs,
        code="whole_reading_consequence_source_evidence_refs_noncanonical",
        allow_empty=False,
    )
    for ref, expected_type in (
        (row.consequence_id, "whole-reading-consequence"),
        (row.foreground_scope_ref, "foreground-scope"),
        (row.required_difference_ref, "required-difference"),
        (row.counterfactual_mutation_ref, "counterfactual-mutation"),
    ):
        validate_version_qualified_ref(ref, expected_types=(expected_type,))
    _validate_whole_reading_context(
        binding_context,
        consequence_code=row.consequence_code,
        basis_rows=foreground_scope_basis_rows,
        source=source,
        grounded_plan=grounded_plan,
        grounded_graph=grounded_graph,
        premeaning_inputs=premeaning_inputs,
        parent_plan=parent_plan,
    )
    if row.consequence_id != whole_reading_consequence_id(row):
        raise CMEEStage1ContractError(
            "whole_reading_consequence_id_mismatch"
        )
    if row.foreground_scope_ref != binding_context.foreground_scope.scope_id:
        raise CMEEStage1ContractError(
            "whole_reading_consequence_foreground_scope_ref_unbound"
        )
    if row.required_difference_ref != binding_context.required_difference_ref:
        raise CMEEStage1ContractError(
            "whole_reading_consequence_required_difference_ref_unbound"
        )
    if row.source_evidence_refs != binding_context.source_evidence_refs:
        raise CMEEStage1ContractError(
            "whole_reading_consequence_source_evidence_refs_unbound"
        )
    if (
        row.counterfactual_mutation_ref
        != binding_context.counterfactual_mutation_ref
    ):
        raise CMEEStage1ContractError(
            "whole_reading_consequence_mutation_ref_unbound"
        )
    if (
        row.baseline_semantic_signature
        != binding_context.baseline_semantic_signature
    ):
        raise CMEEStage1ContractError(
            "whole_reading_consequence_baseline_signature_unbound"
        )
    if (
        row.mutated_semantic_signature
        != binding_context.mutated_semantic_signature
    ):
        raise CMEEStage1ContractError(
            "whole_reading_consequence_mutated_signature_unbound"
        )
    changed_fields = _WHOLE_READING_SIGNATURE_FIELDS_BY_CODE[
        row.consequence_code
    ]
    if not any(
        getattr(row.baseline_semantic_signature, field_name)
        != getattr(row.mutated_semantic_signature, field_name)
        for field_name in changed_fields
    ):
        raise CMEEStage1ContractError(
            "whole_reading_consequence_code_change_mismatch"
        )


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


def stage1_policy_application_order_key(
    row: PolicyApplicationRow,
) -> tuple[int, str]:
    """Return the one canonical v2 policy-application row order key."""

    if (
        type(row) is not PolicyApplicationRow
        or not _stage1_identity_string(row.policy_application_row_ref)
    ):
        raise CMEEStage1ContractError(
            "stage1_projection_v2_policy_application_invalid"
        )
    for principle_position, (_code, principle_ref) in enumerate(
        CMEE_STAGE1_VALUE_PRINCIPLE_REFS
    ):
        if row.principle_ref == principle_ref:
            return principle_position, row.policy_application_row_ref
    raise CMEEStage1ContractError(
        "stage1_projection_v2_policy_application_invalid"
    )


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
    node_source_order: Mapping[str, int],
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
        left, right = tuple(
            _stage1_node_ref(node_id)
            for node_id in sorted(
                (edge.source_node_id, edge.target_node_id),
                key=node_source_order.__getitem__,
            )
        )
        expected_bindings = (
            ArgumentBinding(ArgumentRole.LEFT, left),
            ArgumentBinding(ArgumentRole.RIGHT, right),
        )
    elif candidate.candidate_kind is InterpretationKind.TENSION:
        expected_relation = {"contrast"}
        left, right = tuple(
            _stage1_node_ref(node_id)
            for node_id in sorted(
                (edge.source_node_id, edge.target_node_id),
                key=node_source_order.__getitem__,
            )
        )
        expected_bindings = (
            ArgumentBinding(ArgumentRole.LEFT, left),
            ArgumentBinding(ArgumentRole.RIGHT, right),
        )
    elif candidate.candidate_kind is InterpretationKind.DIRECTION_UNDER_BURDEN:
        source_direction_valid = (
            _STAGE1_DIRECTION_DIRECT_SHAPE in source_direct_shapes
            if source_direct_shapes
            else source_kind in _STAGE1_DIRECTION_NODE_KINDS
        )
        target_direction_valid = (
            _STAGE1_DIRECTION_DIRECT_SHAPE in target_direct_shapes
            if target_direct_shapes
            else target_kind in _STAGE1_DIRECTION_NODE_KINDS
        )
        source_burden_valid = (
            _STAGE1_BURDEN_DIRECT_SHAPE in source_direct_shapes
            if source_direct_shapes
            else source_kind in _STAGE1_BURDEN_NODE_KINDS
        )
        target_burden_valid = (
            _STAGE1_BURDEN_DIRECT_SHAPE in target_direct_shapes
            if target_direct_shapes
            else target_kind in _STAGE1_BURDEN_NODE_KINDS
        )
        source_is_direction = (
            source_kind in _STAGE1_DIRECTION_NODE_KINDS
            and source_direction_valid
        )
        target_is_direction = (
            target_kind in _STAGE1_DIRECTION_NODE_KINDS
            and target_direction_valid
        )
        source_is_burden = (
            source_kind in _STAGE1_BURDEN_NODE_KINDS
            and source_burden_valid
        )
        target_is_burden = (
            target_kind in _STAGE1_BURDEN_NODE_KINDS
            and target_burden_valid
        )
        if not (
            (source_is_direction and target_is_burden)
            or (source_is_burden and target_is_direction)
        ):
            raise CMEEStage1ContractError(
                "stage1_candidate_relation_binding_invalid"
            )
        direction_ref = source_ref if source_is_direction else target_ref
        burden_ref = source_ref if source_is_burden else target_ref
        expected_relation = (
            {"wish_and_constraint"}
            if candidate.relation_operator is RelationOperator.COEXISTS_WITH
            else {
                "preserves_despite",
                "attempt_and_block",
                "continuation_or_refusal",
            }
        )
        expected_bindings = (
            ArgumentBinding(ArgumentRole.LEFT, direction_ref),
            ArgumentBinding(ArgumentRole.RIGHT, burden_ref),
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
            or disposition.source_owner_disposition
            is not SourceOwnerDisposition.UNKNOWN_PRESERVED_LIMITED
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
            "continuation_or_refusal",
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


_STAGE1_V2_RELATION_BASIS_ROLE = {
    ArgumentRole.LEFT: SubjectiveBasisRole.RELATION_LEFT,
    ArgumentRole.RIGHT: SubjectiveBasisRole.RELATION_RIGHT,
    ArgumentRole.ACTION: SubjectiveBasisRole.ACTION,
    ArgumentRole.CHANGE: SubjectiveBasisRole.CHANGE,
    ArgumentRole.BEFORE: SubjectiveBasisRole.BEFORE,
    ArgumentRole.AFTER: SubjectiveBasisRole.AFTER,
    ArgumentRole.CAUSE: SubjectiveBasisRole.RELATION_LEFT,
    ArgumentRole.EFFECT: SubjectiveBasisRole.RELATION_RIGHT,
}


def _stage1_v2_basis_role(
    contribution: PlannedObservationContribution,
    argument_role: ArgumentRole,
) -> SubjectiveBasisRole:
    mapped = _STAGE1_V2_RELATION_BASIS_ROLE.get(argument_role)
    if mapped is not None:
        return mapped
    if contribution.semantic_operator is SemanticOperator.PRESENT_DIRECTION:
        return SubjectiveBasisRole.CHOICE_TARGET
    if contribution.semantic_operator is SemanticOperator.PRESENT_RESIDUE:
        return SubjectiveBasisRole.RESIDUE
    if contribution.semantic_operator is SemanticOperator.PRESENT_UNFINISHED:
        return SubjectiveBasisRole.UNFINISHED
    return SubjectiveBasisRole.APPRAISED_OBJECT


def _stage1_v2_content_binding_refs(content: object) -> tuple[str, ...]:
    if type(content) is EmlisAffectContent:
        return content.elicitor_bindings
    if type(content) is EmlisAppraisalContent:
        return _stage1_first_occurrence_union(
            content.appraised_bindings,
            content.protected_bindings,
        )
    if type(content) is MaterialValueContent:
        return _stage1_first_occurrence_union(
            content.target_bindings,
            content.boundary_bindings,
            tuple(
                ref
                for application in content.value_applications
                for ref in application.protected_subjective_binding_refs
            ),
        )
    if type(content) is EmlisRelationalPosition:
        return _stage1_first_occurrence_union(
            content.target_bindings,
            content.boundary_bindings,
        )
    raise CMEEStage1ContractError(
        "stage1_projection_v2_opportunity_invalid"
    )


def _validate_stage1_projection_v2_subjective_spine(
    projection: EmlisStage1Projection,
    *,
    grounded_graph: GroundedMeaningGraph,
    parent_plan: ExperiencePlan,
    contribution_by_id: Mapping[str, PlannedObservationContribution],
    candidate_by_id: Mapping[str, EmlisInterpretationCandidate],
    node_ids: set[str],
    edge_ids: set[str],
) -> set[str]:
    """Validate the self-contained response-v2 subjective lineage spine."""

    expected_preimage_ref = project_stage1_projection_preimage_ref(
        grounded_graph_ref=projection.grounded_graph_ref,
        parent_observation_duty_ref=projection.parent_observation_duty_ref,
        parent_reception_duty_ref=projection.parent_reception_duty_ref,
        interpretation_candidate_ids=tuple(
            row.candidate_id for row in projection.interpretation_candidates
        ),
        meaning_field_id=projection.meaning_field.meaning_field_id,
        observation_contribution_ids=tuple(contribution_by_id),
        retained_reception_act_ids=projection.retained_reception_act_ids,
        observation_depth_class=projection.observation_depth_class,
        temperature_class=projection.temperature_class,
        reception_style_policy_ref=projection.reception_style_policy_ref,
        emlis_value_policy_ref=projection.emlis_value_policy_ref,
    )
    if projection.projection_preimage_ref != expected_preimage_ref:
        raise CMEEStage1ContractError(
            "stage1_projection_v2_preimage_invalid"
        )

    responsibilities = projection.subjective_responsibility_rows
    opportunities = projection.subjective_opportunity_rows
    suppressions = projection.subjective_facet_suppression_rows
    basis_rows = projection.subjective_basis_binding_rows
    qualifier_rows = projection.source_qualifier_binding_rows
    policy_basis_rows = projection.policy_basis_binding_rows
    policy_application_rows = projection.policy_application_rows
    claims = projection.subjective_claims
    typed_rows = (
        (
            responsibilities,
            SubjectiveResponsibilityRow,
            False,
        ),
        (opportunities, SubjectiveOpportunityRow, False),
        (suppressions, SubjectiveFacetSuppressionRow, True),
        (basis_rows, SubjectiveBasisBinding, False),
        (qualifier_rows, SourceQualifierBinding, False),
        (policy_basis_rows, PolicyBasisBinding, True),
        (policy_application_rows, PolicyApplicationRow, True),
    )
    for rows, expected_type, allow_empty in typed_rows:
        if (
            type(rows) is not tuple
            or (not allow_empty and not rows)
            or any(type(row) is not expected_type for row in rows)
        ):
            raise CMEEStage1ContractError(
                "stage1_projection_v2_lineage_type_invalid"
            )
        for row in rows:
            _validate_stage1_immutable_shape(row)

    contribution_set = set(contribution_by_id)
    retained_act_set = set(projection.retained_reception_act_ids)
    responsibility_by_ref: dict[str, SubjectiveResponsibilityRow] = {}
    for row in responsibilities:
        try:
            _stage1_exact_string_tuple(row.owner_component_refs, allow_empty=False)
            _stage1_exact_string_tuple(
                row.retained_reception_act_refs,
                allow_empty=False,
            )
        except CMEEStage1ContractError:
            raise CMEEStage1ContractError(
                "stage1_subjective_responsibility_invalid"
            ) from None
        if (
            type(row.responsibility_kind)
            is not SubjectiveResponsibilityKind
            or not set(row.owner_component_refs).issubset(contribution_set)
            or not set(row.retained_reception_act_refs).issubset(
                retained_act_set
            )
            or row.responsibility_ref
            != project_stage1_subjective_responsibility_ref(
                projection_preimage_ref=projection.projection_preimage_ref,
                responsibility_kind=row.responsibility_kind,
                owner_component_refs=row.owner_component_refs,
                retained_reception_act_refs=row.retained_reception_act_refs,
            )
            or row.responsibility_ref in responsibility_by_ref
        ):
            raise CMEEStage1ContractError(
                "stage1_subjective_responsibility_invalid"
            )
        responsibility_by_ref[row.responsibility_ref] = row
    if tuple(responsibility_by_ref) != tuple(
        sorted(responsibility_by_ref)
    ):
        raise CMEEStage1ContractError(
            "stage1_subjective_responsibility_invalid"
        )

    content_type_by_kind = {
        SubjectiveContentKind.AFFECT: EmlisAffectContent,
        SubjectiveContentKind.APPRAISAL: EmlisAppraisalContent,
        SubjectiveContentKind.MATERIAL_VALUE: MaterialValueContent,
        SubjectiveContentKind.RELATIONAL_POSITION: EmlisRelationalPosition,
    }
    opportunity_by_key: dict[str, SubjectiveOpportunityRow] = {}
    opportunity_responsibility_refs: list[str] = []
    for row in opportunities:
        if (
            type(row.content_kind) is not SubjectiveContentKind
            or type(row.specificity_key) is not SubjectiveSpecificity
            or type(row.content) is not content_type_by_kind.get(row.content_kind)
        ):
            raise CMEEStage1ContractError(
                "stage1_projection_v2_opportunity_invalid"
            )
        try:
            _stage1_exact_string_tuple(row.responsibility_refs, allow_empty=False)
        except CMEEStage1ContractError:
            raise CMEEStage1ContractError(
                "stage1_projection_v2_opportunity_invalid"
            ) from None
        if (
            any(ref not in responsibility_by_ref for ref in row.responsibility_refs)
            or row.opportunity_key
            != project_stage1_subjective_opportunity_key(
                projection_preimage_ref=projection.projection_preimage_ref,
                responsibility_refs=row.responsibility_refs,
                content_kind=row.content_kind,
                row_ref_free_discriminated_content=row.content,
                specificity_key=row.specificity_key,
            )
            or row.opportunity_key in opportunity_by_key
        ):
            raise CMEEStage1ContractError(
                "stage1_projection_v2_opportunity_invalid"
            )
        _stage1_v2_content_binding_refs(row.content)
        opportunity_by_key[row.opportunity_key] = row
        opportunity_responsibility_refs.extend(row.responsibility_refs)
    if (
        tuple(opportunity_by_key) != tuple(sorted(opportunity_by_key))
        or len(opportunity_responsibility_refs)
        != len(set(opportunity_responsibility_refs))
        or set(opportunity_responsibility_refs) != set(responsibility_by_ref)
    ):
        raise CMEEStage1ContractError(
            "stage1_projection_v2_opportunity_invalid"
        )

    selected_keys = tuple(
        claim.selected_subjective_opportunity_key for claim in claims
    )
    suppressed_keys = tuple(
        row.suppressed_opportunity_key for row in suppressions
    )
    if (
        len(selected_keys) != len(set(selected_keys))
        or len(suppressed_keys) != len(set(suppressed_keys))
        or set(selected_keys).intersection(suppressed_keys)
        or set((*selected_keys, *suppressed_keys)) != set(opportunity_by_key)
        or tuple(suppressed_keys) != tuple(sorted(suppressed_keys))
    ):
        raise CMEEStage1ContractError(
            "stage1_projection_v2_opportunity_partition_invalid"
        )
    for row in suppressions:
        absorber = row.absorbed_by_selected_opportunity_key
        if (
            type(row.reason) is not SubjectiveFacetSuppressionReason
            or row.suppressed_opportunity_key not in opportunity_by_key
            or (
                row.reason is SubjectiveFacetSuppressionReason.NONMATERIAL
                and absorber is not None
            )
            or (
                row.reason is not SubjectiveFacetSuppressionReason.NONMATERIAL
                and absorber not in set(selected_keys)
            )
            or absorber == row.suppressed_opportunity_key
        ):
            raise CMEEStage1ContractError(
                "stage1_projection_v2_opportunity_partition_invalid"
            )

    basis_by_ref: dict[str, SubjectiveBasisBinding] = {}
    for row in basis_rows:
        contribution = contribution_by_id.get(row.contribution_ref)
        if contribution is None:
            raise CMEEStage1ContractError(
                "stage1_subjective_v2_basis_exact_cover_invalid"
            )
        candidate_rows = tuple(
            candidate_by_id[ref]
            for ref in contribution.interpretation_candidate_refs
            if ref in candidate_by_id
        )
        expected_roles = {
            _stage1_v2_basis_role(contribution, binding.role)
            for candidate in candidate_rows
            for binding in candidate.argument_bindings
            if binding.role is not ArgumentRole.EXPERIENCER
            and binding.semantic_ref == row.semantic_ref
        }
        if (
            row.projection_preimage_ref != projection.projection_preimage_ref
            or type(row.role) is not SubjectiveBasisRole
            or row.role not in expected_roles
            or row.semantic_ref not in set(contribution.semantic_refs)
            or row.binding_ref
            != project_stage1_subjective_basis_binding_ref(
                projection_preimage_ref=row.projection_preimage_ref,
                contribution_ref=row.contribution_ref,
                semantic_ref=row.semantic_ref,
                role=row.role,
            )
            or row.binding_ref in basis_by_ref
        ):
            raise CMEEStage1ContractError(
                "stage1_subjective_v2_basis_exact_cover_invalid"
            )
        basis_by_ref[row.binding_ref] = row
    expected_basis_descriptors = {
        (
            contribution.contribution_id,
            binding.semantic_ref,
            _stage1_v2_basis_role(contribution, binding.role),
        )
        for contribution in projection.observation_contributions
        for candidate_ref in contribution.interpretation_candidate_refs
        for binding in candidate_by_id[candidate_ref].argument_bindings
        if binding.role is not ArgumentRole.EXPERIENCER
    }
    actual_basis_descriptors = {
        (row.contribution_ref, row.semantic_ref, row.role) for row in basis_rows
    }
    if (
        tuple(basis_by_ref) != tuple(sorted(basis_by_ref))
        or actual_basis_descriptors != expected_basis_descriptors
    ):
        raise CMEEStage1ContractError(
            "stage1_subjective_v2_basis_exact_cover_invalid"
        )

    qualifier_by_basis: dict[str, SourceQualifierBinding] = {}
    qualifier_ref_seen: set[str] = set()
    for row in qualifier_rows:
        basis = basis_by_ref.get(row.basis_binding_ref)
        contribution = (
            contribution_by_id.get(basis.contribution_ref)
            if basis is not None
            else None
        )
        candidate = candidate_by_id.get(row.source_candidate_ref)
        relation_scoped = (
            candidate is not None
            and candidate.relation_operator is not RelationOperator.NO_RELATION_CLAIM
        )
        matching_binding = (
            candidate is not None
            and any(
                binding.semantic_ref == basis.semantic_ref
                and (
                    (relation_scoped and binding.role is row.source_argument_role)
                    or (not relation_scoped and row.source_argument_role is None)
                )
                for binding in candidate.argument_bindings
            )
        ) if basis is not None else False
        if (
            row.projection_preimage_ref != projection.projection_preimage_ref
            or basis is None
            or contribution is None
            or candidate is None
            or candidate.candidate_id
            not in set(contribution.interpretation_candidate_refs)
            or not matching_binding
            or row.source_qualifier_binding_ref
            != project_stage1_source_qualifier_binding_ref(
                projection_preimage_ref=row.projection_preimage_ref,
                basis_binding_ref=row.basis_binding_ref,
                source_candidate_ref=row.source_candidate_ref,
                source_argument_role=row.source_argument_role,
                canonical_qualifier_codes=row.canonical_qualifier_codes,
                polarity=row.polarity,
                modality=row.modality,
                time_scope=row.time_scope,
            )
            or row.basis_binding_ref in qualifier_by_basis
            or row.source_qualifier_binding_ref in qualifier_ref_seen
        ):
            raise CMEEStage1ContractError(
                "stage1_subjective_v2_qualifier_exact_cover_invalid"
            )
        qualifier_by_basis[row.basis_binding_ref] = row
        qualifier_ref_seen.add(row.source_qualifier_binding_ref)
    if (
        set(qualifier_by_basis) != set(basis_by_ref)
        or tuple(row.source_qualifier_binding_ref for row in qualifier_rows)
        != tuple(sorted(qualifier_ref_seen))
    ):
        raise CMEEStage1ContractError(
            "stage1_subjective_v2_qualifier_exact_cover_invalid"
        )

    policy_by_ref: dict[str, PolicyBasisBinding] = {}
    material_unknown_set = set(projection.meaning_field.material_unknown_refs)
    for row in policy_basis_rows:
        if (
            row.projection_preimage_ref != projection.projection_preimage_ref
            or type(row.owner_kind) is not PolicyBasisOwnerKind
            or type(row.role) is not PolicyBasisRole
            or row.binding_ref
            != project_stage1_policy_basis_binding_ref(
                projection_preimage_ref=row.projection_preimage_ref,
                owner_kind=row.owner_kind,
                owner_ref=row.owner_ref,
                role=row.role,
            )
            or row.binding_ref in policy_by_ref
            or (
                row.owner_kind is PolicyBasisOwnerKind.CONTRIBUTION
                and (
                    row.owner_ref not in contribution_set
                    or row.role is PolicyBasisRole.MATERIAL_UNKNOWN
                )
            )
            or (
                row.owner_kind is PolicyBasisOwnerKind.MATERIAL_UNKNOWN
                and (
                    row.owner_ref not in material_unknown_set
                    or row.role is not PolicyBasisRole.MATERIAL_UNKNOWN
                )
            )
        ):
            raise CMEEStage1ContractError("stage1_policy_basis_binding_invalid")
        policy_by_ref[row.binding_ref] = row
    if tuple(policy_by_ref) != tuple(sorted(policy_by_ref)):
        raise CMEEStage1ContractError("stage1_policy_basis_binding_invalid")

    application_by_ref: dict[str, PolicyApplicationRow] = {}
    risk_by_principle = dict(_STAGE1_VALUE_RISK_DERIVATION_EXACT9)
    claim_set = {row.subjective_claim_id for row in claims}
    for row in policy_application_rows:
        if (
            not _stage1_identity_string(row.policy_application_row_ref)
            or row.policy_application_row_ref in application_by_ref
            or row.application_kind not in {"SUPPRESSION", "VISIBILITY"}
            or row.principle_ref not in risk_by_principle
            or row.material_risk is not risk_by_principle.get(row.principle_ref)
            or row.affected_claim_ref not in claim_set
            or any(ref not in policy_by_ref for ref in row.policy_basis_binding_refs)
            or (
                row.application_kind == "VISIBILITY"
                and row.visible_claim_ref != row.affected_claim_ref
            )
            or (
                row.application_kind == "SUPPRESSION"
                and row.visible_claim_ref is not None
            )
        ):
            raise CMEEStage1ContractError(
                "stage1_projection_v2_policy_application_invalid"
            )
        application_by_ref[row.policy_application_row_ref] = row
    if policy_application_rows != tuple(
        sorted(
            policy_application_rows,
            key=stage1_policy_application_order_key,
        )
    ):
        raise CMEEStage1ContractError(
            "stage1_projection_v2_policy_application_invalid"
        )

    allowed_semantic_refs = _stage1_ordered_unique(
        tuple(
            ref
            for contribution in projection.observation_contributions
            for ref in contribution.semantic_refs
        )
    )
    admitted_relation_refs = _stage1_ordered_unique(
        tuple(
            ref
            for contribution in projection.observation_contributions
            for ref in contribution.relation_basis_refs
        )
    )
    referenced_acts: set[str] = set()
    referenced_basis_refs: set[str] = set()
    visible_principle_order = tuple(
        ref for _code, ref in CMEE_STAGE1_VALUE_PRINCIPLE_REFS
    )
    for claim in claims:
        proposition = claim.asserted_subjective_proposition
        opportunity = opportunity_by_key.get(
            claim.selected_subjective_opportunity_key
        )
        if type(proposition) is not SubjectivePropositionV2:
            raise CMEEStage1ContractError("stage1_subjective_v2_type_invalid")
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
        try:
            _stage1_exact_string_tuple(
                claim.subjective_responsibility_refs,
                allow_empty=False,
            )
            _stage1_exact_string_tuple(
                claim.basis_observation_contribution_refs,
                allow_empty=False,
            )
            _stage1_exact_string_tuple(
                claim.basis_semantic_refs,
                allow_empty=False,
            )
            _stage1_exact_string_tuple(
                claim.source_reception_act_refs,
                allow_empty=False,
            )
        except CMEEStage1ContractError:
            raise CMEEStage1ContractError(
                "stage1_projection_v2_claim_lineage_invalid"
            ) from None
        if (
            claim.schema_version != CMEE_STAGE1_RESPONSE_SCHEMA_VERSION_V2
            or claim.parent_duty_ref != projection.parent_reception_duty_ref
            or claim.speaker_owner != "EMLIS"
            or claim.claim_domain
            != EmlisTraceClaimDomain.SUBJECTIVE_RESPONSE.value
            or type(claim.subjective_mode) is not SubjectiveMode
            or claim.subjective_mode is not proposition.subjective_mode
            or claim.user_fact_effect != 0
            or type(claim.user_fact_effect) is not int
            or opportunity is None
            or claim.subjective_responsibility_refs
            != opportunity.responsibility_refs
            or opportunity.content_kind is not proposition.content_kind
            or opportunity.content != selected_content
            or set(claim.basis_observation_contribution_refs)
            - contribution_set
            or claim.basis_observation_contribution_refs
            != proposition.target_contribution_refs
            or claim.basis_semantic_refs != proposition.response_object_refs
            or not set(claim.source_reception_act_refs).issubset(retained_act_set)
        ):
            raise CMEEStage1ContractError(
                "stage1_projection_v2_claim_lineage_invalid"
            )
        selected_owner_refs = _stage1_first_occurrence_union(
            tuple(
                owner_ref
                for responsibility_ref in opportunity.responsibility_refs
                for owner_ref in responsibility_by_ref[
                    responsibility_ref
                ].owner_component_refs
            )
        )
        if selected_owner_refs != proposition.target_contribution_refs:
            raise CMEEStage1ContractError(
                "stage1_projection_v2_claim_lineage_invalid"
            )
        claim_basis_rows = tuple(
            basis_by_ref[ref]
            for ref in proposition.basis_binding_refs
            if ref in basis_by_ref
        )
        claim_qualifier_rows = tuple(
            qualifier_by_basis[row.binding_ref] for row in claim_basis_rows
        )
        if len(claim_basis_rows) != len(proposition.basis_binding_refs):
            raise CMEEStage1ContractError(
                "stage1_subjective_v2_basis_exact_cover_invalid"
            )
        expected_forbidden = stage1_subjective_forbidden_promotions(
            tuple(
                contribution_by_id[ref]
                for ref in claim.basis_observation_contribution_refs
            ),
            material_unknown_refs=projection.meaning_field.material_unknown_refs,
        )
        for actor_ref in (
            *proposition.referenced_actor_refs,
            *proposition.referenced_experiencer_refs,
        ):
            ref_type, ref_id = _stage1_ref_parts(
                actor_ref,
                expected_types=("node",),
                expected_version=CMEE_GROUNDED_GRAPH_SCHEMA_VERSION,
            )
            if ref_type != "node" or ref_id not in node_ids:
                raise CMEEStage1ContractError(
                    "stage1_subjective_v2_cross_owner_invalid"
                )
        validate_subjective_proposition_v2(
            proposition,
            projection_preimage_ref=projection.projection_preimage_ref,
            basis_rows=claim_basis_rows,
            qualifier_rows=claim_qualifier_rows,
            expected_basis_rows=claim_basis_rows,
            expected_qualifier_rows=claim_qualifier_rows,
            policy_basis_rows=policy_basis_rows,
            expected_policy_basis_rows=policy_basis_rows,
            allowed_contribution_refs=tuple(contribution_by_id),
            allowed_semantic_refs=allowed_semantic_refs,
            allowed_source_candidate_refs=tuple(candidate_by_id),
            allowed_policy_application_row_refs=tuple(application_by_ref),
            admitted_relation_refs=admitted_relation_refs,
            material_unknown_refs=projection.meaning_field.material_unknown_refs,
            expected_actor_refs=proposition.referenced_actor_refs,
            expected_experiencer_refs=proposition.referenced_experiencer_refs,
            expected_focal_relation_ref=proposition.focal_relation_ref,
            owner_ref=CMEE_STAGE1_EMLIS_OWNER_REF_V2,
            speaker_owner=claim.speaker_owner,
            user_fact_effect=claim.user_fact_effect,
            forbidden_promotions=claim.forbidden_promotions,
            expected_forbidden_promotions=expected_forbidden,
        )
        visible_rows = tuple(
            row
            for row in policy_application_rows
            if row.application_kind == "VISIBILITY"
            and row.visible_claim_ref == claim.subjective_claim_id
        )
        visible_refs = tuple(row.principle_ref for row in visible_rows)
        expected_visible_refs = tuple(
            ref for ref in visible_principle_order if ref in set(visible_refs)
        )
        nested_applications = (
            proposition.material_value_content.value_applications
            if proposition.material_value_content is not None
            else ()
        )
        if (
            visible_refs != expected_visible_refs
            or claim.value_principle_refs != expected_visible_refs
            or tuple(row.principle_ref for row in nested_applications)
            != expected_visible_refs
        ):
            raise CMEEStage1ContractError(
                "stage1_projection_v2_policy_application_invalid"
            )
        for application in nested_applications:
            matching_rows = tuple(
                row
                for row in visible_rows
                if row.principle_ref == application.principle_ref
            )
            if (
                application.policy_application_row_refs
                != tuple(row.policy_application_row_ref for row in matching_rows)
                or application.policy_basis_binding_refs
                != _stage1_first_occurrence_union(
                    tuple(
                        ref
                        for row in matching_rows
                        for ref in row.policy_basis_binding_refs
                    )
                )
            ):
                raise CMEEStage1ContractError(
                    "stage1_projection_v2_policy_application_invalid"
                )
        referenced_acts.update(claim.source_reception_act_refs)
        referenced_basis_refs.update(proposition.basis_binding_refs)

    referenced_basis_refs.update(
        ref
        for opportunity in opportunities
        for ref in _stage1_v2_content_binding_refs(opportunity.content)
    )
    if not referenced_basis_refs.issubset(set(basis_by_ref)):
        raise CMEEStage1ContractError(
            "stage1_subjective_v2_basis_exact_cover_invalid"
        )
    return referenced_acts


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
    if projection.schema_version not in {
        CMEE_STAGE1_RESPONSE_SCHEMA_VERSION_V1,
        CMEE_STAGE1_RESPONSE_SCHEMA_VERSION_V2,
    }:
        raise CMEEStage1ContractError("stage1_projection_schema_version_invalid")
    is_v2 = projection.schema_version == CMEE_STAGE1_RESPONSE_SCHEMA_VERSION_V2
    node_ids, edge_ids, evidence_ids = _stage1_graph_universe(
        projection, grounded_graph
    )
    positive_visible_claim_ids = _stage1_positive_visible_claim_ids(
        grounded_graph,
        parent_plan,
    )
    node_by_id = {row.node_id: row for row in grounded_graph.nodes}
    node_source_order = {
        row.node_id: index for index, row in enumerate(grounded_graph.nodes)
    }
    edge_by_id = {row.edge_id: row for row in grounded_graph.edges}
    policy_refs = (
        (
            projection.reception_style_policy_ref,
            projection.emlis_value_policy_ref,
            projection.composition_policy_ref,
            projection.low_level_grammar_policy_ref,
        )
        if is_v2
        else (
            projection.reception_style_policy_ref,
            projection.emlis_value_policy_ref,
            projection.emlis_microgrammar_policy_ref,
        )
    )
    for ref in policy_refs:
        validate_version_qualified_ref(ref, expected_types=("policy",))
    if projection.emlis_value_policy_ref != CMEE_STAGE1_VALUE_POLICY_REF:
        raise CMEEStage1ContractError("stage1_value_policy_ref_invalid")
    if is_v2:
        composition_version = _stage1_final_logical_identity(
            "CMEE_STAGE1_COMPOSITION_POLICY_VERSION"
        )
        grammar_version = _stage1_final_logical_identity(
            "CMEE_STAGE1_CONSTRUCTION_GRAMMAR_POLICY_VERSION"
        )
        expected_composition_ref = (
            f"policy:{composition_version.rsplit('.', 1)[0]}"
            f"@{composition_version}"
        )
        expected_grammar_ref = (
            f"policy:{grammar_version.rsplit('.', 1)[0]}@{grammar_version}"
        )
        if (
            projection.emlis_microgrammar_policy_ref != ""
            or projection.composition_policy_ref != expected_composition_ref
            or projection.low_level_grammar_policy_ref != expected_grammar_ref
        ):
            raise CMEEStage1ContractError(
                "stage1_projection_v2_policy_ref_invalid"
            )
    elif (
        projection.emlis_microgrammar_policy_ref
        != CMEE_STAGE1_MICROGRAMMAR_POLICY_REF
        or projection.projection_preimage_ref
        or projection.composition_policy_ref
        or projection.low_level_grammar_policy_ref
        or projection.subjective_responsibility_rows
        or projection.subjective_opportunity_rows
        or projection.subjective_facet_suppression_rows
        or projection.subjective_basis_binding_rows
        or projection.source_qualifier_binding_rows
        or projection.policy_basis_binding_rows
        or projection.policy_application_rows
    ):
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
    layer1_children = (*candidates, projection.meaning_field, *contributions)
    for child in layer1_children:
        _validate_stage1_immutable_shape(child)
        expected_layer1_schema = (
            CMEE_STAGE1_RESPONSE_SCHEMA_VERSION_V1
            if is_v2
            else projection.schema_version
        )
        if child.schema_version != expected_layer1_schema:
            raise CMEEStage1ContractError("stage1_child_schema_version_mismatch")
        validate_stage1_identity(child)
    for child in claims:
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
        or (
            not is_v2
            and set(meaning_field_candidate_refs) != candidate_set
        )
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
        referenced_claim_ids = {
            _stage1_ref_parts(
                ref,
                expected_types=("node", "edge"),
                expected_version=CMEE_GROUNDED_GRAPH_SCHEMA_VERSION,
            )[1]
            for ref in (*row.semantic_refs, *row.relation_basis_refs)
        }
        if not referenced_claim_ids.issubset(positive_visible_claim_ids):
            raise CMEEStage1ContractError(
                "stage1_candidate_visible_owner_disposition_mismatch"
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
            node_source_order=node_source_order,
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

    if is_v2:
        meaning_candidate_set = set(meaning_field_candidate_refs)
        support_candidate_set = candidate_set - meaning_candidate_set
        admitted_endpoint_refs = {
            binding.semantic_ref
            for candidate in candidates
            if candidate.relation_operator is not RelationOperator.NO_RELATION_CLAIM
            for binding in candidate.argument_bindings
        }
        contribution_candidate_refs = {
            ref
            for contribution in contributions
            for ref in contribution.interpretation_candidate_refs
        }
        if any(
            support.relation_operator is not RelationOperator.NO_RELATION_CLAIM
            or len(support.semantic_refs) != 1
            or support.semantic_refs[0] not in admitted_endpoint_refs
            or support.candidate_id in contribution_candidate_refs
            or support.candidate_id in set(meaning_field.required_candidate_refs)
            for support in (
                candidate_by_id[ref] for ref in support_candidate_set
            )
        ):
            raise CMEEStage1ContractError(
                "stage1_projection_v2_support_candidate_invalid"
            )

    kind_counts: dict[InterpretationKind, int] = {}
    required_candidate_set = set(meaning_field.required_candidate_refs)
    for row in candidates:
        if is_v2 and row.candidate_id in support_candidate_set:
            continue
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
        if is_v2:
            continue
        if (
            row.subjective_responsibility_refs
            or row.selected_subjective_opportunity_key
        ):
            raise CMEEStage1ContractError("stage1_subjective_type_invalid")
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
    if is_v2:
        referenced_acts = _validate_stage1_projection_v2_subjective_spine(
            projection,
            grounded_graph=grounded_graph,
            parent_plan=parent_plan,
            contribution_by_id=contribution_by_id,
            candidate_by_id=candidate_by_id,
            node_ids=node_ids,
            edge_ids=edge_ids,
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
    is_v2 = projection.schema_version == CMEE_STAGE1_RESPONSE_SCHEMA_VERSION_V2
    if not is_v2:
        if unit.v2_trace_seal is not None:
            raise CMEEStage1ContractError("stage1_unit_v2_seal_cross_version")
    else:
        seal = unit.v2_trace_seal
        if type(seal) is not Stage1V2UnitSeal:
            raise CMEEStage1ContractError("stage1_unit_v2_seal_missing")
        _validate_stage1_immutable_shape(seal)
        try:
            _stage1_exact_string_tuple(seal.covered_duty_refs, allow_empty=False)
            _stage1_exact_string_tuple(seal.sentence_job_refs, allow_empty=False)
            _stage1_exact_string_tuple(
                seal.source_reception_act_refs,
                allow_empty=True,
            )
        except CMEEStage1ContractError:
            raise CMEEStage1ContractError(
                "stage1_unit_v2_seal_invalid"
            ) from None
        if any(
            not _stage1_identity_string(ref)
            for ref in (
                seal.composition_candidate_ref,
                seal.composition_layout_ref,
                seal.selected_stage1_artifact_ref,
            )
        ):
            raise CMEEStage1ContractError("stage1_unit_v2_seal_invalid")
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
    if is_v2:
        seal = unit.v2_trace_seal
        assert seal is not None
        expected_source_reception_act_refs = (
            _stage1_first_occurrence_union(
                tuple(
                    ref
                    for anchor_ref in unit.basis_anchor_refs
                    for ref in claim_by_id[
                        anchor_ref
                    ].source_reception_act_refs
                )
            )
            if unit.layer == "LAYER_2"
            else ()
        )
        if (
            seal.source_reception_act_refs
            != expected_source_reception_act_refs
        ):
            raise CMEEStage1ContractError("stage1_unit_v2_seal_invalid")
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
    raw_passed: Optional[bool] = None
    disposition: str = "DIRECT"


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
    typed_admission_refs: Tuple[str, ...] = ()


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


def _validate_stage1_trace_spine_v2(
    trace_rows: Sequence[VisibleUnitTrace],
    projection: EmlisStage1Projection,
    *,
    grounded_graph: GroundedMeaningGraph,
) -> None:
    """Validate grouped v2 trace rows and their sealed provenance fields."""

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
        or roles
        != (
            *("OBSERVATION" for _ in range(observation_count)),
            *("UNKNOWN" for _ in range(unknown_count)),
            *("RECEPTION" for _ in range(reception_count)),
        )
    ):
        raise CMEEStage1ContractError("stage1_trace_role_order_invalid")
    visible_ids = tuple(row.visible_unit_id for row in rows)
    _require_unique_nonempty_refs(visible_ids, code="stage1_trace_identity_invalid")
    position = {visible_id: index for index, visible_id in enumerate(visible_ids)}
    candidate_by_id = {
        row.candidate_id: row for row in projection.interpretation_candidates
    }
    contribution_by_id = {
        row.contribution_id: row for row in projection.observation_contributions
    }
    claim_by_id = {
        row.subjective_claim_id: row for row in projection.subjective_claims
    }
    contribution_counts = {ref: 0 for ref in contribution_by_id}
    claim_counts = {ref: 0 for ref in claim_by_id}
    ordered_contribution_refs: list[str] = []
    ordered_claim_refs: list[str] = []
    covered_duty_seen: set[str] = set()
    variant_ids: set[str] = set()
    candidate_refs: set[str] = set()
    layout_refs: set[str] = set()
    selected_artifact_refs: set[str] = set()

    for index, row in enumerate(rows):
        if (
            row.source_envelope_id != grounded_graph.source_envelope_id
            or row.source_version != grounded_graph.source_version
            or row.obligation_version != grounded_graph.obligation_version
            or row.owner_universe_digest != grounded_graph.owner_universe_digest
        ):
            raise CMEEStage1ContractError(
                "stage1_trace_lineage_metadata_mismatch"
            )
        for field_name in (
            "meaning_node_ids",
            "meaning_edge_ids",
            "evidence_ids",
            "constrained_by_owner_ids",
        ):
            refs = getattr(row, field_name)
            if (
                type(refs) is not tuple
                or any(type(ref) is not str or not ref for ref in refs)
                or len(refs) != len(set(refs))
            ):
                raise CMEEStage1ContractError("stage1_trace_base_ref_invalid")
        extension = row.emlis_stage1_extension
        if row.role == "UNKNOWN":
            if extension is not None:
                raise CMEEStage1ContractError(
                    "stage1_unknown_trace_extension_present"
                )
            if (
                row.meaning_node_ids
                or row.meaning_edge_ids
                or not row.evidence_ids
                or not row.constrained_by_owner_ids
            ):
                raise CMEEStage1ContractError(
                    "stage1_unknown_trace_lineage_invalid"
                )
            continue
        if row.role not in {"OBSERVATION", "RECEPTION"}:
            raise CMEEStage1ContractError("stage1_trace_role_invalid")
        if type(extension) is not EmlisStage1PositiveTraceExtension:
            raise CMEEStage1ContractError("stage1_trace_extension_type_invalid")
        _validate_stage1_immutable_shape(extension)
        if (
            extension.schema_version
            != CMEE_STAGE1_TRACE_EXTENSION_SCHEMA_VERSION_V2
        ):
            raise CMEEStage1ContractError(
                "stage1_trace_extension_version_invalid"
            )
        if extension.owner_ref != CMEE_STAGE1_EMLIS_OWNER_REF_V2:
            raise CMEEStage1ContractError("stage1_trace_owner_invalid")
        if (
            extension.user_fact_effect != 0
            or type(extension.user_fact_effect) is not int
            or not _stage1_identity_string(extension.composition_variant_id)
        ):
            raise CMEEStage1ContractError("stage1_trace_variant_missing")
        try:
            _stage1_exact_string_tuple(
                extension.covered_duty_refs,
                allow_empty=False,
            )
            _stage1_exact_string_tuple(
                extension.sentence_job_refs,
                allow_empty=False,
            )
            _stage1_exact_string_tuple(
                extension.source_reception_act_refs,
                allow_empty=True,
            )
        except CMEEStage1ContractError:
            raise CMEEStage1ContractError(
                "stage1_trace_v2_seal_invalid"
            ) from None
        if (
            any(
                not _stage1_identity_string(ref)
                for ref in (
                    extension.composition_candidate_ref,
                    extension.composition_layout_ref,
                    extension.selected_stage1_artifact_ref,
                )
            )
            or covered_duty_seen.intersection(extension.covered_duty_refs)
        ):
            raise CMEEStage1ContractError("stage1_trace_v2_seal_invalid")
        covered_duty_seen.update(extension.covered_duty_refs)
        variant_ids.add(extension.composition_variant_id)
        candidate_refs.add(extension.composition_candidate_ref)
        layout_refs.add(extension.composition_layout_ref)
        selected_artifact_refs.add(extension.selected_stage1_artifact_ref)
        if not (row.meaning_node_ids or row.meaning_edge_ids) or not row.evidence_ids:
            raise CMEEStage1ContractError("stage1_trace_base_lineage_missing")

        if row.role == "OBSERVATION":
            if row.duty_id != projection.parent_observation_duty_ref:
                raise CMEEStage1ContractError(
                    "stage1_observation_trace_duty_mismatch"
                )
            if (
                extension.claim_domain
                is not EmlisTraceClaimDomain.INTERPRETIVE_OBSERVATION
                or extension.subjective_claim_ref is not None
                or extension.subjective_claim_refs
                or extension.basis_trace_refs
                or extension.basis_observation_contribution_refs
                or extension.source_reception_act_refs
                or extension.value_principle_refs
                or extension.speaker_owner is not None
            ):
                raise CMEEStage1ContractError(
                    "stage1_observation_trace_domain_invalid"
                )
            _require_local_subset(
                extension.contribution_refs,
                set(contribution_by_id),
                code="stage1_observation_trace_contribution_invalid",
                allow_empty=False,
            )
            _require_local_subset(
                extension.interpretation_candidate_refs,
                set(candidate_by_id),
                code="stage1_observation_trace_candidate_invalid",
                allow_empty=False,
            )
            reachable_candidates = {
                candidate_ref
                for contribution_ref in extension.contribution_refs
                for candidate_ref in contribution_by_id[
                    contribution_ref
                ].interpretation_candidate_refs
            }
            if not set(extension.interpretation_candidate_refs).issubset(
                reachable_candidates
            ):
                raise CMEEStage1ContractError(
                    "stage1_observation_trace_candidate_unreachable"
                )
            ordered_contribution_refs.extend(extension.contribution_refs)
            for ref in extension.contribution_refs:
                contribution_counts[ref] += 1
            reachable_semantic_refs = {
                ref
                for contribution_ref in extension.contribution_refs
                for ref in (
                    *contribution_by_id[contribution_ref].semantic_refs,
                    *contribution_by_id[contribution_ref].relation_basis_refs,
                )
            } | {
                ref
                for candidate_ref in extension.interpretation_candidate_refs
                for ref in candidate_by_id[candidate_ref].semantic_refs
            }
            reachable_evidence_ids = {
                _version_qualified_local_id(ref)
                for contribution_ref in extension.contribution_refs
                for ref in contribution_by_id[contribution_ref].evidence_refs
            } | {
                _version_qualified_local_id(ref)
                for candidate_ref in extension.interpretation_candidate_refs
                for ref in candidate_by_id[candidate_ref].evidence_refs
            }
        else:
            if row.duty_id != projection.parent_reception_duty_ref:
                raise CMEEStage1ContractError(
                    "stage1_reception_trace_duty_mismatch"
                )
            if (
                extension.claim_domain
                is not EmlisTraceClaimDomain.SUBJECTIVE_RESPONSE
                or extension.contribution_refs
                or extension.interpretation_candidate_refs
                or extension.subjective_claim_ref is not None
                or extension.speaker_owner != "EMLIS"
            ):
                raise CMEEStage1ContractError(
                    "stage1_reception_trace_domain_invalid"
                )
            _require_local_subset(
                extension.subjective_claim_refs,
                set(claim_by_id),
                code="stage1_reception_trace_claim_mismatch",
                allow_empty=False,
            )
            ordered_claim_refs.extend(extension.subjective_claim_refs)
            for ref in extension.subjective_claim_refs:
                claim_counts[ref] += 1
            expected_basis_contributions = _stage1_first_occurrence_union(
                tuple(
                    ref
                    for claim_ref in extension.subjective_claim_refs
                    for ref in claim_by_id[
                        claim_ref
                    ].basis_observation_contribution_refs
                )
            )
            expected_value_refs = _stage1_first_occurrence_union(
                tuple(
                    ref
                    for claim_ref in extension.subjective_claim_refs
                    for ref in claim_by_id[claim_ref].value_principle_refs
                )
            )
            expected_source_act_refs = _stage1_first_occurrence_union(
                tuple(
                    ref
                    for claim_ref in extension.subjective_claim_refs
                    for ref in claim_by_id[claim_ref].source_reception_act_refs
                )
            )
            if (
                extension.basis_observation_contribution_refs
                != expected_basis_contributions
                or extension.value_principle_refs != expected_value_refs
                or extension.source_reception_act_refs
                != expected_source_act_refs
            ):
                raise CMEEStage1ContractError(
                    "stage1_reception_trace_claim_mismatch"
                )
            _require_unique_nonempty_refs(
                extension.basis_trace_refs,
                code="stage1_reception_trace_ref_invalid",
            )
            expected_basis_contribution_set = set(
                expected_basis_contributions
            ).intersection(projection.ordered_observation_refs)
            reachable_basis_contributions: list[str] = []
            for basis_ref in extension.basis_trace_refs:
                basis_position = position.get(basis_ref)
                if basis_position is None:
                    raise CMEEStage1ContractError(
                        "stage1_reception_trace_ref_missing"
                    )
                if basis_position >= index:
                    raise CMEEStage1ContractError(
                        "stage1_reception_trace_ref_forward"
                    )
                basis_row = rows[basis_position]
                basis_extension = basis_row.emlis_stage1_extension
                if (
                    basis_row.role != "OBSERVATION"
                    or basis_extension is None
                ):
                    raise CMEEStage1ContractError(
                        "stage1_reception_trace_ref_foreign"
                    )
                basis_contribution_refs = basis_extension.contribution_refs
                if not expected_basis_contribution_set.intersection(
                    basis_contribution_refs
                ):
                    raise CMEEStage1ContractError(
                        "stage1_reception_trace_basis_unreachable"
                    )
                reachable_basis_contributions.extend(basis_contribution_refs)
            if not expected_basis_contribution_set.issubset(
                reachable_basis_contributions
            ):
                raise CMEEStage1ContractError(
                    "stage1_reception_trace_basis_unreachable"
                )
            reachable_semantic_refs = {
                ref
                for claim_ref in extension.subjective_claim_refs
                for ref in claim_by_id[claim_ref].basis_semantic_refs
            } | {
                ref
                for contribution_ref in expected_basis_contributions
                for ref in (
                    *contribution_by_id[contribution_ref].semantic_refs,
                    *contribution_by_id[contribution_ref].relation_basis_refs,
                )
            }
            reachable_evidence_ids = {
                _version_qualified_local_id(ref)
                for contribution_ref in expected_basis_contributions
                for ref in contribution_by_id[contribution_ref].evidence_refs
            }

        reachable_node_ids = {
            _version_qualified_local_id(ref)
            for ref in reachable_semantic_refs
            if ref.startswith("node:")
        }
        reachable_edge_ids = {
            _version_qualified_local_id(ref)
            for ref in reachable_semantic_refs
            if ref.startswith("edge:")
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
                "stage1_trace_lineage_unreachable"
            )

    flattened_contribution_refs = tuple(ordered_contribution_refs)
    if (
        len(flattened_contribution_refs)
        != len(set(flattened_contribution_refs))
        or set(flattened_contribution_refs)
        != set(projection.ordered_observation_refs)
        or any(count != 1 for count in contribution_counts.values())
    ):
        raise CMEEStage1ContractError(
            "stage1_observation_trace_coverage_invalid"
        )
    flattened_claim_refs = tuple(ordered_claim_refs)
    if (
        len(flattened_claim_refs) != len(set(flattened_claim_refs))
        or set(flattened_claim_refs)
        != set(projection.ordered_subjective_refs)
        or any(count != 1 for count in claim_counts.values())
    ):
        raise CMEEStage1ContractError(
            "stage1_reception_trace_coverage_invalid"
        )
    if not covered_duty_seen or any(
        len(refs) != 1
        for refs in (
            variant_ids,
            candidate_refs,
            layout_refs,
            selected_artifact_refs,
        )
    ):
        raise CMEEStage1ContractError("stage1_trace_v2_seal_invalid")


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
    if projection.schema_version == CMEE_STAGE1_RESPONSE_SCHEMA_VERSION_V2:
        _validate_stage1_trace_spine_v2(
            trace_rows,
            projection,
            grounded_graph=grounded_graph,
        )
        return
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
        if (
            extension.subjective_claim_refs
            or extension.covered_duty_refs
            or extension.sentence_job_refs
            or extension.source_reception_act_refs
            or extension.composition_candidate_ref
            or extension.composition_layout_ref
            or extension.selected_stage1_artifact_ref
        ):
            raise CMEEStage1ContractError(
                "stage1_trace_extension_cross_version"
            )
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
    source_owner_policy_version: str = CMEE_SOURCE_OWNER_POLICY_VERSION

    def as_body_free(self) -> Mapping[str, Any]:
        graph = self.meaning_graph
        artifact = self.artifact
        dispositions = tuple(graph.owner_dispositions) if graph else ()
        visible = {
            SourceOwnerDisposition.SOURCE_EXPLICIT_VISIBLE,
            SourceOwnerDisposition.SUPPLEMENTAL_USER_VISIBLE,
        }
        return {
            "schema_version": self.schema_version,
            "source_owner_policy_version": self.source_owner_policy_version,
            "core_id": CoreId.EMLIS_AI.value,
            "product_job": ProductJob.OBSERVE_AND_CLARIFY.value,
            "execution_mode": ExecutionMode.OFFLINE_CANDIDATE.value,
            "status": self.status.value,
            "reason_codes": list(self.reason_codes),
            "source_envelope_count": int(self.source_envelope is not None),
            "meaning_node_count": len(graph.nodes) if graph else 0,
            "meaning_edge_count": len(graph.edges) if graph else 0,
            "required_active_owner_count": len(dispositions),
            "visible_owner_count": sum(
                row.source_owner_disposition in visible for row in dispositions
            ),
            "unresolved_owner_count": sum(
                row.source_owner_disposition not in visible for row in dispositions
            ),
            "unresolved_required_owner_count": sum(
                row.owner_class is OwnerClass.REQUIRED
                and row.source_owner_disposition not in visible
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
            "source_owner_contract_complete": False,
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
    "ArgumentRealizationPlan",
    "AppraisalDimension",
    "AppraisalOperation",
    "ArgumentBinding",
    "ArgumentRole",
    "AllowedReceptionOpportunityEnvelope",
    "AttachmentAdmission",
    "AtomicPredicateHeadSpec",
    "CaseParticleRule",
    "CaseParticleSurfaceVariant",
    "CMEE_COMMON_GUARD_PROOF_VERSION",
    "CMEE_GROUNDED_GRAPH_SCHEMA_VERSION",
    "CMEE_OBLIGATION_VERSION",
    "CMEE_OWNER_UNIVERSE_SCHEMA_VERSION",
    "CMEE_SOURCE_OWNER_POLICY_VERSION",
    "CMEE_SCHEMA_VERSION",
    "CMEE_SOURCE_CONTRACT_VERSION",
    "CMEE_STAGE1_ANTI_TEMPLATE_FORBIDDEN_REGISTRY_FIELDS",
    "CMEE_STAGE1_ANTI_TEMPLATE_FORBIDDEN_SELECTOR_INPUTS",
    "CMEE_STAGE1_EMLIS_OWNER_REF",
    "CMEE_STAGE1_EMLIS_OWNER_REF_V1",
    "CMEE_STAGE1_EMLIS_OWNER_REF_V2",
    "CMEE_STAGE1_FINAL_LOGICAL_ID_REGISTRY",
    "CMEE_STAGE1_IDENTITY_ALGORITHM",
    "CMEE_STAGE1_RESPONSE_SCHEMA_VERSION",
    "CMEE_STAGE1_RESPONSE_SCHEMA_VERSION_V1",
    "CMEE_STAGE1_RESPONSE_SCHEMA_VERSION_V2",
    "CMEE_STAGE1_SUBJECTIVE_FORBIDDEN_PROMOTIONS",
    "CMEE_STAGE1_TRACE_EXTENSION_SCHEMA_VERSION",
    "CMEE_STAGE1_TRACE_EXTENSION_SCHEMA_VERSION_V1",
    "CMEE_STAGE1_TRACE_EXTENSION_SCHEMA_VERSION_V2",
    "CMEE_TERMINAL_GENERATED_DISABLED",
    "CMEEStage1ContractError",
    "ClauseFrame",
    "ClauseLinkPlan",
    "ClauseLinkRule",
    "ComplementRuleSpec",
    "CommonGuardProof",
    "CommonGuardResultProof",
    "CoreId",
    "EmlisInterpretationCandidate",
    "EmlisAffectContent",
    "EmlisAppraisalContent",
    "EmlisMeaningField",
    "EmlisRelationalPosition",
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
    "ForegroundScope",
    "ForegroundScopeBasisKind",
    "ForegroundScopeBasisRow",
    "ForegroundScopeCompatibilityAxis",
    "ForegroundScopeDerivation",
    "ForegroundScopeDerivationState",
    "ForegroundScopeObjectCompatibilityRow",
    "ForegroundScopeRelationKind",
    "GenerationArtifactBundle",
    "GenerationRequest",
    "GroundedExpressionPlan",
    "GroundedMeaningGraph",
    "GroundedSourceQualifierRow",
    "GroundedSourceRelationRow",
    "InflectionClassSpec",
    "InterpretationEpistemicState",
    "InterpretationKind",
    "JapaneseCaseFrameSpec",
    "JapaneseClauseIR",
    "JapaneseLocalPreferenceProfile",
    "JapaneseLocalPreferenceRule",
    "LexicalFamilySpec",
    "LinearizedJapaneseClause",
    "MatrixMorphologyParadigmSpec",
    "MeaningFieldEntry",
    "MeaningFieldSlot",
    "MeaningComponentSemanticKey",
    "MeaningReadingOperation",
    "MeaningSemanticSignature",
    "MeaningEdge",
    "MeaningNode",
    "MaterialRisk",
    "MaterialValueContent",
    "ObservationContributionKind",
    "ObservationDepthClass",
    "OwnerClass",
    "OwnerDisposition",
    "PolicyBasisBinding",
    "PolicyBasisOwnerKind",
    "PolicyBasisRole",
    "PolicyApplicationRow",
    "PlannedObservationContribution",
    "PreMeaningGroundedInputs",
    "PredicateMorphologyPlan",
    "PredicateSenseFrameLicense",
    "PredicateSenseSpec",
    "ProductJob",
    "ResolverResolution",
    "RealizedSemanticBinding",
    "RealizedSentenceUnit",
    "RealizationCandidateSet",
    "ReferenceZeroTopicRule",
    "RelationOperator",
    "RelationalClosure",
    "RelationalCommitment",
    "RelationalPositionKind",
    "SourceOwnerDisposition",
    "SourceOwnerResolution",
    "SemanticOperator",
    "SourceEnvelope",
    "SourceClassifierSpec",
    "SourceComplementPlan",
    "SourceFinalTerminalClass",
    "SourceFunctionalModifierSpec",
    "SourceFunctionalTokenSpec",
    "SourceLeafCardinality",
    "SourceLeafExtent",
    "SourceLeafGroup",
    "SourceLeafToken",
    "SourceLineBreakShape",
    "SourceQualifierBinding",
    "SourceQuoteDelimiterRule",
    "SourceQuoteTopology",
    "SourceRealizationMode",
    "SourceSentenceShape",
    "SenseComplementLicense",
    "DiscourseReferenceStateRow",
    "SourceOwnerObligation",
    "SourceOwnerUniverse",
    "StanceOperator",
    "SubjectiveAssertionModality",
    "SubjectiveBasisBinding",
    "SubjectiveBasisRole",
    "SubjectiveContentKind",
    "SubjectiveDepthClass",
    "SubjectiveFacetSuppressionReason",
    "SubjectiveFacetSuppressionRow",
    "SubjectiveMode",
    "SubjectiveOpportunityRow",
    "SubjectiveOperator",
    "SubjectiveProposition",
    "SubjectivePropositionV2",
    "SubjectiveResponsibilityKind",
    "SubjectiveResponsibilityRow",
    "SubjectiveSpecificity",
    "Stage1V2UnitSeal",
    "SurfaceDerivation",
    "SurfaceDerivationKind",
    "TemperatureClass",
    "VisibleAuthority",
    "VisibleUnknownUnit",
    "VisibleUnitTrace",
    "ValueApplication",
    "WholeReadingConsequenceCode",
    "WholeReadingConsequenceRow",
    "WholeReadingConsequenceValidationContext",
    "foreground_scope_basis_row_ref",
    "foreground_scope_id",
    "project_foreground_scope_relation_kind",
    "project_premeaning_source_qualifier_rows",
    "project_premeaning_source_relation_rows",
    "project_stage1_policy_basis_binding_ref",
    "project_stage1_projection_preimage_ref",
    "project_stage1_source_qualifier_binding_ref",
    "project_stage1_subjective_basis_binding_ref",
    "project_stage1_subjective_opportunity_key",
    "project_stage1_subjective_responsibility_ref",
    "recompute_stage1_identity",
    "stage1_policy_application_order_key",
    "stage1_projection_artifact_ref",
    "stage1_canonical_json_bytes",
    "validate_stage1_anti_template_registry_invariant",
    "validate_stage1_final_logical_id_registry",
    "validate_stage1_identity",
    "validate_stage1_local_ref_dag",
    "validate_stage1_projection",
    "validate_stage1_projection_artifact_ref",
    "validate_stage1_sentence_unit",
    "validate_stage1_trace_spine",
    "validate_foreground_scope",
    "validate_foreground_scope_basis_row",
    "validate_foreground_scope_derivation",
    "validate_premeaning_grounded_inputs",
    "validate_meaning_semantic_signature",
    "validate_subjective_proposition_v2",
    "validate_surface_derivation",
    "validate_version_qualified_ref",
    "validate_whole_reading_consequence_row",
    "whole_reading_consequence_id",
]
