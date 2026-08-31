# -*- coding: utf-8 -*-
from __future__ import annotations

"""Final, request-local CMEE Stage 1 composition core.

This module is deliberately not wired to the active v1 response facade.  It
contains the Step 2 language core which both early and final execution use.
It consumes frozen typed semantics, never reparses the request, and has no
alternate compatibility realizer.
"""

from dataclasses import dataclass, fields, replace
from enum import Enum
import ast
import hashlib
from pathlib import Path
from typing import Any, Iterable, Mapping, Optional, Sequence, Tuple

from .contracts import (
    AffectCategory,
    AffectIntensity,
    AllowedReceptionOpportunityEnvelope,
    BoundedLimitedReception,
    AppraisalDimension,
    AppraisalOperation,
    ArgumentBinding,
    ArgumentRealizationPlan,
    ArgumentRole,
    AtomicPredicateHeadSpec,
    CaseParticleRule,
    CaseParticleSurfaceVariant,
    ClauseFrame,
    ClauseLinkPlan,
    ClauseLinkRule,
    CMEE_GROUNDED_GRAPH_SCHEMA_VERSION,
    CMEE_OBLIGATION_VERSION,
    CMEE_STAGE1_FINAL_LOGICAL_ID_REGISTRY,
    CMEE_STAGE1_MEANING_BOUND_SUBJECTIVE_PROJECTION_SCHEMA_VERSION,
    CMEE_STAGE1_RECEPTION_ACT_MAPPING_EXACT7,
    CMEE_STAGE1_SUBJECTIVE_FORBIDDEN_PROMOTIONS,
    CMEE_STAGE1_VALUE_PRINCIPLE_REFS,
    CMEEStage1ContractError,
    ComplementRuleSpec,
    DiscourseReferenceStateRow,
    DifferenceInvariantCode,
    EmlisAffectContent,
    EmlisAppraisalContent,
    EmlisInterpretationCandidate,
    EmlisMeaningField,
    EmlisRelationalPosition,
    EmlisStage1Projection,
    EmlisSubjectiveClaim,
    EpistemicState,
    InflectionClassSpec,
    InputSpecificMeaningStructure,
    LimitedMeaningOutcome,
    LimitedMeaningVisibleCausalTraceRow,
    JapaneseClauseIR,
    JapaneseCaseFrameSpec,
    JapaneseLocalPreferenceProfile,
    JapaneseLocalPreferenceRule,
    LexicalFamilySpec,
    LinearizedJapaneseClause,
    MatrixMorphologyParadigmSpec,
    MaterialRisk,
    MaterialValueContent,
    MeaningBoundReceptionProposition,
    MeaningBoundReceptionSet,
    MeaningFieldEntry,
    ObservationContributionKind,
    OwnerClass,
    PlannedObservationContribution,
    PreMeaningGroundedInputs,
    QualifiedEventStateConfiguration,
    ReadingConsequence,
    ReceptionVisibleCausalTraceRow,
    RelationalConfiguration,
    ForegroundScopeDerivation,
    PolicyApplicationRow,
    PolicyBasisBinding,
    PolicyBasisOwnerKind,
    PolicyBasisRole,
    PredicateSenseFrameLicense,
    PredicateSenseSpec,
    PredicateMorphologyPlan,
    RelationOperator,
    ReferenceZeroTopicRule,
    RealizedSemanticBinding,
    RealizedSentenceUnit,
    RelationalClosure,
    RelationalCommitment,
    RelationalPositionKind,
    SemanticOperator,
    SenseComplementLicense,
    SourceClassifierSpec,
    SourceFinalTerminalClass,
    SourceOwnerDisposition,
    SourceFunctionalModifierSpec,
    SourceFunctionalTokenSpec,
    SourceLeafGroup,
    SourceLeafCardinality,
    SourceLeafExtent,
    SourceLeafToken,
    SourceLineBreakShape,
    SourceComplementPlan,
    SourceQualifierBinding,
    SourceQuoteDelimiterRule,
    SourceQuoteTopology,
    SourceRealizationMode,
    SourceSentenceShape,
    StanceOperator,
    SubjectiveAssertionModality,
    SubjectiveBasisBinding,
    SubjectiveBasisRole,
    SubjectiveContentKind,
    SubjectiveMode,
    SubjectiveOperator,
    SubjectivePropositionV2,
    SubjectiveProjectionBranch,
    SealedEmlisProvisionalReading,
    SelectedEmlisProvisionalReading,
    SelectedMeaningVisibleCausalTraceRow,
    SubjectiveResponsibilityKind,
    SubjectiveSpecificity,
    SurfaceDerivation,
    SurfaceDerivationKind,
    ValueApplication,
    VisibleAuthority,
    _stage1_material_visible_value_refs,
    project_stage1_policy_basis_binding_ref,
    project_stage1_projection_preimage_ref,
    project_stage1_subjective_opportunity_key,
    project_stage1_subjective_projection_seal_ref,
    project_stage1_subjective_responsibility_ref,
    recompute_stage1_identity,
    project_stage1_source_qualifier_binding_ref,
    project_stage1_subjective_basis_binding_ref,
    project_stage1_tagged_projection_ref,
    bounded_limited_reception_id,
    limited_meaning_outcome_id,
    meaning_bound_reception_id,
    subjective_proposition_v2_id,
    stage1_canonical_json_bytes,
    stage1_policy_application_order_key,
    stage1_subjective_forbidden_promotions,
    validate_stage1_anti_template_registry_invariant,
    validate_stage1_identity,
    validate_stage1_projection,
    validate_foreground_scope_derivation,
    validate_input_specific_meaning_structure,
    validate_stage1_post_selection_reception_records,
    validate_premeaning_grounded_inputs,
)
from .emlis_input_specific_meaning import (
    ForegroundScopeDisposition,
    ForegroundScopeDispositionCode,
    GroundedSituationView,
    validate_foreground_scope_disposition,
    validate_grounded_situation_view,
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
CMEE_STAGE1_COMPOSITION_LAYOUT_ID_VERSION = _FINAL_ID[
    "CMEE_STAGE1_COMPOSITION_LAYOUT_ID_VERSION"
]
CMEE_STAGE1_ARTIFACT_COMPOSITION_CANDIDATE_ID_VERSION = _FINAL_ID[
    "CMEE_STAGE1_ARTIFACT_COMPOSITION_CANDIDATE_ID_VERSION"
]


class Stage1CompositionError(ValueError):
    """Named fail-closed stop in the disabled final Stage 1 core."""


class ReferenceDecisionKind(str, Enum):
    """Closed typed reference dimensions consumed by the v2 projector."""

    REFERENT = "REFERENT"
    EMLIS_SUBJECT = "EMLIS_SUBJECT"
    REQUIRED_RELATION_ENDPOINT = "REQUIRED_RELATION_ENDPOINT"


@dataclass(frozen=True, slots=True)
class V2ReferenceSurfaceSpec:
    """Closed v2 anaphor surface; never sourced from the v1 asset seams."""

    surface_ref: str
    reference_rule_ref: str
    atomic_surface: str
    source_cardinality: SourceLeafCardinality
    licensed_frame_refs: Tuple[str, ...]


class ClauseLinkPlacement(str, Enum):
    """Closed placement input; rendered tokens remain registry-owned."""

    FRAME_INTERNAL = "FRAME_INTERNAL"
    SENTENCE_INITIAL = "SENTENCE_INITIAL"
    SENTENCE_INITIAL_ADDITIVE = "SENTENCE_INITIAL_ADDITIVE"
    ZERO = "ZERO"

# I01 registration only: no active facade reads this inventory and none of the
# rows contain request data or a completed user-visible phrase.
V2_GRAMMAR_INVENTORY_SHA256 = (
    "a669b33be64b067b6548da20390d7dbb8ffab0f8297d91736bf4363780d7c7b9"
)
V2_GRAMMAR_INVENTORY_BYTE_COUNT = 14_695
V2_GRAMMAR_INVENTORY_ROW_COUNT = 246
V2_GRAMMAR_INVENTORY = """SENSE|S01|OBSERVE_CENTER|GROUNDED_PREDICATE|center|F01
SENSE|S02|OBSERVE_CENTER|GROUNDED_PREDICATE|direction|F02
SENSE|S03|OBSERVE_CENTER|GROUNDED_PREDICATE|burden|F03
SENSE|S04|OBSERVE_CENTER|GROUNDED_PREDICATE|bounded-change|F04
SENSE|S05|RELATE_COEXISTING_OR_TENSION|ADMITTED_RELATION|coexistence|F05
SENSE|S06|RELATE_COEXISTING_OR_TENSION|ADMITTED_RELATION|tension|F06,F24
SENSE|S07|TRACE_CHANGE_OR_SEQUENCE|ADMITTED_RELATION|sequence|F07,F08,F09
SENSE|S08|PRESERVE_RESIDUE_OR_UNFINISHED|GROUNDED_PREDICATE|unfinished|F10
SENSE|S09|FEEL_TOWARD_OBJECT|SUBJECTIVE_PREDICATE|affect|F11
SENSE|S10|CONSIDER_MATERIAL_MEANING|SUBJECTIVE_PREDICATE|appraisal-material|F12
SENSE|S11|CONSIDER_MATERIAL_MEANING|SUBJECTIVE_PREDICATE|appraisal-noncollapse|F13
SENSE|S12|CONSIDER_MATERIAL_MEANING|SUBJECTIVE_PREDICATE|appraisal-change|F14
SENSE|S13|CONSIDER_MATERIAL_MEANING|SUBJECTIVE_PREDICATE|appraisal-unfinished|F15
SENSE|S14|CONSIDER_MATERIAL_MEANING|SUBJECTIVE_PREDICATE|appraisal-agency|F16
SENSE|S15|TAKE_MATERIAL_POSITION|SUBJECTIVE_PREDICATE|material-value|F17,F18
SENSE|S16|TAKE_MATERIAL_POSITION|SUBJECTIVE_PREDICATE|position|F19,F20,F23
SENSE|S17|STAY_WITH_UNFINISHED|SUBJECTIVE_PREDICATE|open-position|F21,F22
FRAME|F01|S01|GROUNDED_CENTER_MONADIC|SUBJECT|required|C03|TOPIC_CONDITIONAL|ZERO_FORBIDDEN|H01|MP01|NONE
FRAME|F02|S02|GROUNDED_DIRECTION_MONADIC|SUBJECT|required|C05|TOPIC_CONDITIONAL|ZERO_FORBIDDEN|H02|MP02|NONE
FRAME|F03|S03|GROUNDED_BURDEN_MONADIC|SUBJECT|required|C05|TOPIC_CONDITIONAL|ZERO_FORBIDDEN|H03|MP03|NONE
FRAME|F04|S04|GROUNDED_CHANGE_MONADIC|SUBJECT|required|C05|TOPIC_CONDITIONAL|ZERO_FORBIDDEN|H04|MP04|NONE
FRAME|F05|S05|RELATION_COEXISTENCE|LEFT_ENDPOINT,RIGHT_ENDPOINT|required|required|C07|TOPIC_FORBIDDEN|ZERO_FORBIDDEN|H05|MP05|NONE
FRAME|F06|S06|RELATION_TENSION|LEFT_ENDPOINT,RIGHT_ENDPOINT|required|required|C07|TOPIC_FORBIDDEN|ZERO_FORBIDDEN|H06|MP06|NONE
FRAME|F07|S07|RELATION_TEMPORAL|BEFORE_EVENT,AFTER_EVENT|required|required|C07|TOPIC_FORBIDDEN|ZERO_FORBIDDEN|H07|MP07|NONE
FRAME|F08|S07|RELATION_ACTION_CHANGE|ACTION_EVENT,CHANGE_EVENT|required|required|C07|TOPIC_FORBIDDEN|ZERO_FORBIDDEN|H08|MP08|NONE
FRAME|F09|S07|RELATION_EXPLICIT_CAUSE|CAUSE_EVENT,EFFECT_EVENT|required|required|C07|TOPIC_FORBIDDEN|ZERO_FORBIDDEN|H09|MP09|NONE
FRAME|F10|S08|GROUNDED_UNFINISHED_MONADIC|SUBJECT|required|C05|TOPIC_CONDITIONAL|ZERO_FORBIDDEN|H10|MP10|NONE
FRAME|F11|S09|SUBJECTIVE_AFFECT_DYADIC|SUBJECT,PRIMARY_OBJECT|required|required|C02|TOPIC_CONDITIONAL|EMLIS_ZERO_CONDITIONAL|H11|MP11|NONE
FRAME|F12|S10|SUBJECTIVE_APPRAISAL_MATERIAL_DYADIC|SUBJECT,PRIMARY_OBJECT|required|required|C04|TOPIC_CONDITIONAL|EMLIS_ZERO_CONDITIONAL|H12|MP12|NONE
FRAME|F13|S11|SUBJECTIVE_NONCOLLAPSE_DYADIC|SUBJECT,PRIMARY_OBJECT|required|required|C08|TOPIC_CONDITIONAL|EMLIS_ZERO_CONDITIONAL|H13|MP13|FM01
FRAME|F14|S12|SUBJECTIVE_CHANGE_DYADIC|SUBJECT,PRIMARY_OBJECT|required|required|C06|TOPIC_CONDITIONAL|EMLIS_ZERO_CONDITIONAL|H14|MP14|NONE
FRAME|F15|S13|SUBJECTIVE_UNFINISHED_DYADIC|SUBJECT,PRIMARY_OBJECT|required|required|C02|TOPIC_CONDITIONAL|EMLIS_ZERO_CONDITIONAL|H15|MP15|FM02
FRAME|F16|S14|SUBJECTIVE_AGENCY_DYADIC|SUBJECT,PRIMARY_OBJECT|required|required|C06|TOPIC_CONDITIONAL|EMLIS_ZERO_CONDITIONAL|H16|MP16|NONE
FRAME|F17|S15|SUBJECTIVE_VALUE_DYADIC|SUBJECT,PRIMARY_OBJECT|required|required|C04|TOPIC_CONDITIONAL|EMLIS_ZERO_CONDITIONAL|H17|MP17|NONE
FRAME|F18|S15|SUBJECTIVE_VALUE_BOUNDARY_TRIADIC|SUBJECT,PRIMARY_OBJECT,SECONDARY_OBJECT|required|required|required|C09|TOPIC_CONDITIONAL|EMLIS_ZERO_CONDITIONAL|H18|MP18|NONE
FRAME|F19|S16|SUBJECTIVE_POSITION_DYADIC|SUBJECT,PRIMARY_OBJECT|required|required|C06|TOPIC_CONDITIONAL|EMLIS_ZERO_CONDITIONAL|H19|MP19|NONE
FRAME|F20|S16|SUBJECTIVE_POSITION_BOUNDARY_TRIADIC|SUBJECT,PRIMARY_OBJECT,SECONDARY_OBJECT|required|required|required|C09|TOPIC_CONDITIONAL|EMLIS_ZERO_CONDITIONAL|H20|MP20|NONE
FRAME|F21|S17|SUBJECTIVE_OPEN_DYADIC|SUBJECT,PRIMARY_OBJECT|required|required|C02|TOPIC_CONDITIONAL|EMLIS_ZERO_CONDITIONAL|H21|MP21|FM03
FRAME|F22|S17|SUBJECTIVE_OPEN_BOUNDARY_TRIADIC|SUBJECT,PRIMARY_OBJECT,SECONDARY_OBJECT|required|required|required|C09|TOPIC_CONDITIONAL|EMLIS_ZERO_CONDITIONAL|H22|MP22|NONE
FRAME|F23|S16|SUBJECTIVE_POSITION_COORDINATED_DYADIC|SUBJECT,PRIMARY_OBJECT|required|required|C08|TOPIC_CONDITIONAL|EMLIS_ZERO_CONDITIONAL|H23|MP23|NONE
FRAME|F24|S06|RELATION_TENSION_STATIVE|LEFT_ENDPOINT,RIGHT_ENDPOINT|required|required|C07|TOPIC_FORBIDDEN|ZERO_FORBIDDEN|H24|MP24|NONE
HEAD|H01|F01|中心+LEXICALIZED_に+なる|IC03|LF01
HEAD|H02|F02|見える|IC01|LF02
HEAD|H03|F03|残る|IC03|LF03
HEAD|H04|F04|見+られる|IC01|LF21
HEAD|H05|F05|並ぶ|IC04|LF05
HEAD|H06|F06|せめぎ+合う|IC05|LF06
HEAD|H07|F07|続く|IC02|LF07
HEAD|H08|F08|起こる|IC03|LF04
HEAD|H09|F09|生じる|IC01|LF08
HEAD|H10|F10|ある|IC03|LF09
HEAD|H11|F11|気+LEXICALIZED_に+かける|IC01|LF10
HEAD|H12|F12|受け+止める|IC01|LF11
HEAD|H13|F13|抱える|IC01|LF12
HEAD|H14|F14|見+届ける|IC01|LF13
HEAD|H15|F15|結論づける|IC01|LF14
HEAD|H16|F16|尊重+する|IC06|LF15
HEAD|H17|F17|大切+LEXICALIZED_に+する|IC06|LF16
HEAD|H18|F18|守る|IC03|LF17
HEAD|H19|F19|見+守る|IC03|LF18
HEAD|H20|F20|固定+する|IC06|LF19
HEAD|H21|F21|断定+する|IC06|LF22
HEAD|H22|F22|限定+する|IC06|LF20
HEAD|H23|F23|守る|IC03|LF17
HEAD|H24|F24|緊張+関係+LEXICALIZED_に+ある|IC03|LF23
LEXICAL_FAMILY|LF01|中心+LEXICALIZED_に+なる
LEXICAL_FAMILY|LF02|見える
LEXICAL_FAMILY|LF03|残る
LEXICAL_FAMILY|LF04|起こる
LEXICAL_FAMILY|LF05|並ぶ
LEXICAL_FAMILY|LF06|せめぎ+合う
LEXICAL_FAMILY|LF07|続く
LEXICAL_FAMILY|LF08|生じる
LEXICAL_FAMILY|LF09|ある
LEXICAL_FAMILY|LF10|気+LEXICALIZED_に+かける
LEXICAL_FAMILY|LF11|受け+止める
LEXICAL_FAMILY|LF12|抱える
LEXICAL_FAMILY|LF13|見+届ける
LEXICAL_FAMILY|LF14|結論づける
LEXICAL_FAMILY|LF15|尊重+する
LEXICAL_FAMILY|LF16|大切+LEXICALIZED_に+する
LEXICAL_FAMILY|LF17|守る
LEXICAL_FAMILY|LF18|見+守る
LEXICAL_FAMILY|LF19|固定+する
LEXICAL_FAMILY|LF20|限定+する
LEXICAL_FAMILY|LF21|見+られる
LEXICAL_FAMILY|LF22|断定+する
LEXICAL_FAMILY|LF23|緊張+関係+LEXICALIZED_に+ある
COMPLEMENT|C02|QUOTE_COMPLEMENT|EXACT1|PRIMARY_OBJECT|OUTER_QUOTES,FRAME_MARKER
COMPLEMENT|C03|CONTENT_NOMINAL|EXACT1|MONADIC_SUBJECT|SF01,SF02
COMPLEMENT|C04|CONTENT_NOMINAL|EXACT1|PRIMARY_OBJECT|SF01,SF02
COMPLEMENT|C05|CLASSIFIED_CONTENT|EXACT1|MONADIC_SUBJECT|SF01,CLASSIFIER_EXACT1
COMPLEMENT|C06|CLASSIFIED_CONTENT|EXACT1|PRIMARY_OBJECT|SF01,CLASSIFIER_EXACT1
COMPLEMENT|C07|COORDINATED_EXACT2|ORDERED_EXACT2|PAIRED_ENDPOINTS|OUTER_QUOTES,FRAME_PARTICLES,COORDINATOR_ZERO
COMPLEMENT|C08|COORDINATED_EXACT2|ORDERED_EXACT2|PRIMARY_OBJECT|OUTER_QUOTES,SF03
COMPLEMENT|C09|BOUNDARY_SPLIT_EXACT2|ORDERED_EXACT2|PRIMARY_OBJECT,SECONDARY_OBJECT|OUTER_QUOTES,FRAME_PARTICLES,COORDINATOR_ZERO
SENSE_COMPLEMENT|SC01|S01|F01|C03|NONE
SENSE_COMPLEMENT|SC02|S02|F02|C05|CL01
SENSE_COMPLEMENT|SC03|S03|F03|C05|CL02
SENSE_COMPLEMENT|SC04|S04|F04|C05|CL03
SENSE_COMPLEMENT|SC05|S05|F05|C07|NONE
SENSE_COMPLEMENT|SC06|S06|F06|C07|NONE
SENSE_COMPLEMENT|SC07|S07|F07|C07|NONE
SENSE_COMPLEMENT|SC08|S07|F08|C07|NONE
SENSE_COMPLEMENT|SC09|S07|F09|C07|NONE
SENSE_COMPLEMENT|SC10|S08|F10|C05|CL05
SENSE_COMPLEMENT|SC11|S09|F11|C02|NONE
SENSE_COMPLEMENT|SC12|S10|F12|C04|NONE
SENSE_COMPLEMENT|SC13|S11|F13|C08|NONE
SENSE_COMPLEMENT|SC14|S12|F14|C06|CL03
SENSE_COMPLEMENT|SC15|S13|F15|C02|NONE
SENSE_COMPLEMENT|SC16|S14|F16|C06|CL04
SENSE_COMPLEMENT|SC17|S15|F17|C04|NONE
SENSE_COMPLEMENT|SC18|S15|F18|C09|NONE
SENSE_COMPLEMENT|SC19|S16|F19|C06|CL04
SENSE_COMPLEMENT|SC20|S16|F20|C09|NONE
SENSE_COMPLEMENT|SC21|S17|F21|C02|NONE
SENSE_COMPLEMENT|SC22|S17|F22|C09|NONE
SENSE_COMPLEMENT|SC23|S16|F23|C08|NONE
SENSE_COMPLEMENT|SC24|S06|F24|C07|NONE
SOURCE_MODE|SM01|QUOTE_COMPLEMENT
SOURCE_MODE|SM02|CONTENT_NOMINAL
SOURCE_MODE|SM03|CLASSIFIED_CONTENT
SOURCE_MODE|SM04|COORDINATED_EXACT2
SOURCE_MODE|SM05|BOUNDARY_SPLIT_EXACT2
CLASSIFIER|CL01|direction|方向性
CLASSIFIER|CL02|burden|負担
CLASSIFIER|CL03|bounded-change|変化
CLASSIFIER|CL04|agency-or-position|選択
CLASSIFIER|CL05|preserved-point|点
SOURCE_TOKEN|SF01|NOMINAL_ATTRIBUTIVE|という
SOURCE_TOKEN|SF02|CONTENT_HEAD|内容
SOURCE_TOKEN|SF03|PAIR_COORDINATOR|と
MODIFIER|FM01|F13|AFTER_PRIMARY_OBJECT_BEFORE_HEAD|どちらか一方だけにせず
MODIFIER|FM02|F15|AFTER_SUBJECT_BEFORE_PRIMARY_OBJECT|今すぐ
MODIFIER|FM03|F21|AFTER_SUBJECT_BEFORE_PRIMARY_OBJECT|ここで
QUOTE_DELIMITER|QD01|NONE|KAGI_OUTER
QUOTE_DELIMITER|QD02|BALANCED_KAGI_ONLY|NIJUKAGI_OUTER
QUOTE_DELIMITER|QD03|BALANCED_NIJUKAGI_ONLY|KAGI_OUTER
QUOTE_DELIMITER|QD04|BALANCED_MIXED|STOP
PARTICLE|P01|F01|SUBJECT|BASE_が|TOPIC_は
PARTICLE|P02|F02|SUBJECT|BASE_が|TOPIC_は
PARTICLE|P03|F03|SUBJECT|BASE_が|TOPIC_は
PARTICLE|P04|F04|SUBJECT|BASE_が|TOPIC_は
PARTICLE|P05|F10|SUBJECT|BASE_が|TOPIC_は
PARTICLE|P06|F05|LEFT_ENDPOINT|FIXED_と
PARTICLE|P07|F05|RIGHT_ENDPOINT|FIXED_が
PARTICLE|P08|F06|LEFT_ENDPOINT|FIXED_と
PARTICLE|P09|F06|RIGHT_ENDPOINT|FIXED_が
PARTICLE|P10|F07|BEFORE_EVENT|FIXED_のあとに
PARTICLE|P11|F07|AFTER_EVENT|FIXED_が
PARTICLE|P12|F08|ACTION_EVENT|FIXED_のあとに
PARTICLE|P13|F08|CHANGE_EVENT|FIXED_が
PARTICLE|P14|F09|CAUSE_EVENT|FIXED_によって
PARTICLE|P15|F09|EFFECT_EVENT|FIXED_が
PARTICLE|P16|F11|SUBJECT|BASE_が|TOPIC_は
PARTICLE|P17|F11|PRIMARY_OBJECT|FIXED_を
PARTICLE|P18|F12|SUBJECT|BASE_が|TOPIC_は
PARTICLE|P19|F12|PRIMARY_OBJECT|FIXED_を
PARTICLE|P20|F13|SUBJECT|BASE_が|TOPIC_は
PARTICLE|P21|F13|PRIMARY_OBJECT|FIXED_を
PARTICLE|P22|F14|SUBJECT|BASE_が|TOPIC_は
PARTICLE|P23|F14|PRIMARY_OBJECT|FIXED_を
PARTICLE|P24|F15|SUBJECT|BASE_が|TOPIC_は
PARTICLE|P25|F15|PRIMARY_OBJECT|FIXED_と
PARTICLE|P26|F16|SUBJECT|BASE_が|TOPIC_は
PARTICLE|P27|F16|PRIMARY_OBJECT|FIXED_を
PARTICLE|P28|F17|SUBJECT|BASE_が|TOPIC_は
PARTICLE|P29|F17|PRIMARY_OBJECT|FIXED_を
PARTICLE|P30|F19|SUBJECT|BASE_が|TOPIC_は
PARTICLE|P31|F19|PRIMARY_OBJECT|FIXED_を
PARTICLE|P32|F21|SUBJECT|BASE_が|TOPIC_は
PARTICLE|P33|F21|PRIMARY_OBJECT|FIXED_と
PARTICLE|P34|F18|SUBJECT|BASE_が|TOPIC_は
PARTICLE|P35|F18|PRIMARY_OBJECT|FIXED_を
PARTICLE|P36|F18|SECONDARY_OBJECT|FIXED_から
PARTICLE|P37|F20|SUBJECT|BASE_が|TOPIC_は
PARTICLE|P38|F20|PRIMARY_OBJECT|FIXED_を
PARTICLE|P39|F20|SECONDARY_OBJECT|FIXED_に
PARTICLE|P40|F22|SUBJECT|BASE_が|TOPIC_は
PARTICLE|P41|F22|PRIMARY_OBJECT|FIXED_を
PARTICLE|P42|F22|SECONDARY_OBJECT|FIXED_に
PARTICLE|P43|F23|SUBJECT|BASE_が|TOPIC_は
PARTICLE|P44|F23|PRIMARY_OBJECT|FIXED_を
PARTICLE|P45|F24|LEFT_ENDPOINT|FIXED_と
PARTICLE|P46|F24|RIGHT_ENDPOINT|FIXED_が
INFLECTION_CLASS|IC01|ICHIDAN_RU
INFLECTION_CLASS|IC02|GODAN_KU
INFLECTION_CLASS|IC03|GODAN_RU
INFLECTION_CLASS|IC04|GODAN_BU
INFLECTION_CLASS|IC05|GODAN_U
INFLECTION_CLASS|IC06|SAHEN_SURU
MORPHOLOGY|MP01|F01|RESULTATIVE_STATE|POSITIVE|GROUNDED_ASSERTION|POLITE|ONBIN_TE_IRU_MASU|PERIOD
MORPHOLOGY|MP02|F02|NONPAST_STATIVE|POSITIVE|GROUNDED_ASSERTION|POLITE|STEM_MASU|PERIOD
MORPHOLOGY|MP03|F03|RESULTATIVE_STATE|POSITIVE|GROUNDED_ASSERTION|POLITE|ONBIN_TE_IRU_MASU|PERIOD
MORPHOLOGY|MP04|F04|NONPAST_STATIVE|POSITIVE|GROUNDED_ASSERTION|POLITE|STEM_MASU|PERIOD
MORPHOLOGY|MP05|F05|PROGRESSIVE_STATE|POSITIVE|GROUNDED_ASSERTION|POLITE|ONBIN_DE_IRU_MASU|PERIOD
MORPHOLOGY|MP06|F06|PROGRESSIVE_STATE|POSITIVE|GROUNDED_ASSERTION|POLITE|ONBIN_TE_IRU_MASU|PERIOD
MORPHOLOGY|MP07|F07|PROGRESSIVE_STATE|POSITIVE|GROUNDED_ASSERTION|POLITE|ONBIN_ITE_IRU_MASU|PERIOD
MORPHOLOGY|MP08|F08|RESULTATIVE_STATE|POSITIVE|GROUNDED_ASSERTION|POLITE|ONBIN_TE_IRU_MASU|PERIOD
MORPHOLOGY|MP09|F09|RESULTATIVE_STATE|POSITIVE|GROUNDED_ASSERTION|POLITE|STEM_TE_IRU_MASU|PERIOD
MORPHOLOGY|MP10|F10|NONPAST_STATIVE|POSITIVE|GROUNDED_ASSERTION|POLITE|STEM_MASU|PERIOD
MORPHOLOGY|MP11|F11|PROGRESSIVE_STATE|POSITIVE|EMLIS_FEELING|POLITE|STEM_TE_IRU_MASU|PERIOD
MORPHOLOGY|MP12|F12|NONPAST|POSITIVE|EMLIS_VOLITIONAL|POLITE|STEM_TAI_DESU|PERIOD
MORPHOLOGY|MP13|F13|NONPAST|POSITIVE|EMLIS_VOLITIONAL|POLITE|STEM_TAI_DESU|PERIOD
MORPHOLOGY|MP14|F14|NONPAST|POSITIVE|EMLIS_VOLITIONAL|POLITE|STEM_TAI_DESU|PERIOD
MORPHOLOGY|MP15|F15|NONPAST|NEGATIVE|EMLIS_BOUNDED_REFUSAL|POLITE|STEM_TAKU_ARIMASEN|PERIOD
MORPHOLOGY|MP16|F16|NONPAST|POSITIVE|EMLIS_VOLITIONAL|POLITE|SAHEN_SHI_TAI_DESU|PERIOD
MORPHOLOGY|MP17|F17|NONPAST|POSITIVE|EMLIS_VOLITIONAL|POLITE|SAHEN_SHI_TAI_DESU|PERIOD
MORPHOLOGY|MP18|F18|NONPAST|POSITIVE|EMLIS_VOLITIONAL|POLITE|STEM_TAI_DESU|PERIOD
MORPHOLOGY|MP19|F19|NONPAST|POSITIVE|EMLIS_VOLITIONAL|POLITE|STEM_TAI_DESU|PERIOD
MORPHOLOGY|MP20|F20|NONPAST|NEGATIVE|EMLIS_BOUNDED_REFUSAL|POLITE|SAHEN_SHI_TAKU_ARIMASEN|PERIOD
MORPHOLOGY|MP21|F21|NONPAST|NEGATIVE|EMLIS_BOUNDED_REFUSAL|POLITE|SAHEN_SHI_TAKU_ARIMASEN|PERIOD
MORPHOLOGY|MP22|F22|NONPAST|NEGATIVE|EMLIS_BOUNDED_REFUSAL|POLITE|SAHEN_SHI_TAKU_ARIMASEN|PERIOD
MORPHOLOGY|MP23|F23|NONPAST|POSITIVE|EMLIS_VOLITIONAL|POLITE|STEM_TAI_DESU|PERIOD
MORPHOLOGY|MP24|F24|NONPAST_STATIVE|POSITIVE|GROUNDED_ASSERTION|POLITE|STEM_MASU|PERIOD
LINK|L01|COEXISTS_WITH|FRAME_INTERNAL|F05|ZERO_EXTERNAL
LINK|L02|TENSION_WITH|FRAME_INTERNAL|F06|ZERO_EXTERNAL
LINK|L03|TEMPORALLY_PRECEDES|FRAME_INTERNAL|F07|ZERO_EXTERNAL
LINK|L04|ACTION_PRECEDES_CHANGE|FRAME_INTERNAL|F08|ZERO_EXTERNAL
LINK|L05|SOURCE_EXPLICIT_CAUSE|FRAME_INTERNAL|F09|ZERO_EXTERNAL
LINK|L06|TEMPORALLY_PRECEDES|SENTENCE_INITIAL|registered:そのあと|INTERNAL_ZERO
LINK|L07|ACTION_PRECEDES_CHANGE|SENTENCE_INITIAL|registered:その後|INTERNAL_ZERO
LINK|L08|SOURCE_EXPLICIT_CAUSE|SENTENCE_INITIAL|registered:そのため|INTERNAL_ZERO
LINK|L09|NO_RELATION_CLAIM|SENTENCE_INITIAL_ADDITIVE|registered:また|INDEPENDENT_TOPIC_ONLY
LINK|L10|ANY_ADMITTED_RELATION|ZERO|registered:empty|RELATION_ALREADY_OWNED
LINK|L11|TENSION_WITH|FRAME_INTERNAL|F24|ZERO_EXTERNAL
REFERENCE|R01|FIRST_MENTION|FULL_EXPRESSION
REFERENCE|R02|AMBIGUOUS_ANTECEDENT|FULL_EXPRESSION
REFERENCE|R03|SINGULAR_ANTECEDENT_EXACT1|SINGULAR_ANAPHOR
REFERENCE|R04|ORDERED_PAIR_PREVIOUS_EXACT2|PAIR_ANAPHOR
REFERENCE|R05|EMLIS_FIRST_OR_RESTART|EXPLICIT_SUBJECT
REFERENCE|R06|EMLIS_SAME_SPEAKER_CHAIN|ZERO_SUBJECT
REFERENCE|R07|EMLIS_AFTER_COUNTERPOSITION|EXPLICIT_SUBJECT
REFERENCE|R08|INTRODUCED_TOPIC|TOPIC_HA
REFERENCE|R09|ADMITTED_CONTRAST|TOPIC_HA
REFERENCE|R10|FIRST_NONCONTRAST|BASE_CASE
REFERENCE|R11|REQUIRED_RELATION_ENDPOINT|EXPLICIT_ENDPOINT
REFERENCE|R12|REFERENCE_REPAIR|FULL_EXPRESSION_NO_FORK
PREFERENCE|J01|EXPLICIT_REFERENT_REPEAT
PREFERENCE|J02|TOPIC_STACK
PREFERENCE|J03|QUOTE_OR_NOMINALIZER_LOAD
PREFERENCE|J04|CONNECTIVE_REPEAT
PREFERENCE|J05|EXPLICIT_EMLIS_SUBJECT_REPEAT
PREFERENCE|J06|CLAUSE_LOAD
PREFERENCE|J07|REFERENCE_DISTANCE
"""
V2_GRAMMAR_INVENTORY_ROWS = tuple(
    tuple(line.split("|")) for line in V2_GRAMMAR_INVENTORY.splitlines()
)
V2_GRAMMAR_INVENTORY_EXACT_COUNTS = (
    ("SENSE", 17),
    ("FRAME", 24),
    ("HEAD", 24),
    ("LEXICAL_FAMILY", 23),
    ("COMPLEMENT", 8),
    ("SENSE_COMPLEMENT", 24),
    ("SOURCE_MODE", 5),
    ("CLASSIFIER", 5),
    ("SOURCE_TOKEN", 3),
    ("MODIFIER", 3),
    ("QUOTE_DELIMITER", 4),
    ("PARTICLE", 46),
    ("INFLECTION_CLASS", 6),
    ("MORPHOLOGY", 24),
    ("LINK", 11),
    ("REFERENCE", 12),
    ("PREFERENCE", 7),
)


def _validate_v2_grammar_inventory_literal() -> None:
    """Reject literal drift before any typed enum or row constructor runs."""

    payload = V2_GRAMMAR_INVENTORY.encode("utf-8")
    actual_counts = tuple(
        (kind, sum(row[0] == kind for row in V2_GRAMMAR_INVENTORY_ROWS))
        for kind, _count in V2_GRAMMAR_INVENTORY_EXACT_COUNTS
    )
    if (
        len(payload) != V2_GRAMMAR_INVENTORY_BYTE_COUNT
        or hashlib.sha256(payload).hexdigest() != V2_GRAMMAR_INVENTORY_SHA256
        or len(V2_GRAMMAR_INVENTORY_ROWS) != V2_GRAMMAR_INVENTORY_ROW_COUNT
        or not V2_GRAMMAR_INVENTORY.endswith("\n")
        or V2_GRAMMAR_INVENTORY.endswith("\n\n")
        or "\r" in V2_GRAMMAR_INVENTORY
        or actual_counts != V2_GRAMMAR_INVENTORY_EXACT_COUNTS
    ):
        raise Stage1CompositionError("GRAMMAR_INVENTORY_MANIFEST_DRIFT_STOP")


_validate_v2_grammar_inventory_literal()


def _v2_inventory_rows(kind: str) -> Tuple[Tuple[str, ...], ...]:
    return tuple(row for row in V2_GRAMMAR_INVENTORY_ROWS if row[0] == kind)


def _v2_optional_ref(value: str) -> Optional[str]:
    return None if value == "NONE" else value


def _v2_split_refs(value: str) -> Tuple[str, ...]:
    return tuple(value.split(","))


def _v2_case_frame(row: Tuple[str, ...]) -> JapaneseCaseFrameSpec:
    slot_roles = _v2_split_refs(row[4])
    tail = 5 + len(slot_roles)
    return JapaneseCaseFrameSpec(
        frame_id=row[1],
        sense_ref=row[2],
        frame_kind=row[3],
        slot_roles=slot_roles,
        slot_requirements=tuple(row[5:tail]),
        complement_rule_ref=row[tail],
        topic_policy=row[tail + 1],
        zero_policy=row[tail + 2],
        atomic_head_ref=row[tail + 3],
        morphology_ref=row[tail + 4],
        modifier_ref=_v2_optional_ref(row[tail + 5]),
    )


V2_PREDICATE_SENSE_REGISTRY = tuple(
    PredicateSenseSpec(
        sense_id=row[1],
        sentence_job=row[2],
        semantic_clause_kind=row[3],
        semantic_sense=row[4],
        frame_license_refs=_v2_split_refs(row[5]),
    )
    for row in _v2_inventory_rows("SENSE")
)
V2_PREDICATE_SENSE_FRAME_LICENSE_REGISTRY = tuple(
    PredicateSenseFrameLicense(sense_ref=row.sense_id, frame_ref=frame_ref)
    for row in V2_PREDICATE_SENSE_REGISTRY
    for frame_ref in row.frame_license_refs
)
V2_JAPANESE_CASE_FRAME_REGISTRY = tuple(
    _v2_case_frame(row) for row in _v2_inventory_rows("FRAME")
)
V2_ATOMIC_PREDICATE_HEAD_REGISTRY = tuple(
    AtomicPredicateHeadSpec(
        head_id=row[1],
        frame_ref=row[2],
        atomic_parts=tuple(row[3].split("+")),
        inflection_class_ref=row[4],
        lexical_family_ref=row[5],
    )
    for row in _v2_inventory_rows("HEAD")
)
V2_LEXICAL_FAMILY_REGISTRY = tuple(
    LexicalFamilySpec(
        lexical_family_id=row[1],
        atomic_parts=tuple(row[2].split("+")),
    )
    for row in _v2_inventory_rows("LEXICAL_FAMILY")
)
V2_COMPLEMENT_RULE_REGISTRY = tuple(
    ComplementRuleSpec(
        complement_rule_id=row[1],
        mode=SourceRealizationMode(row[2]),
        cardinality=SourceLeafCardinality(row[3]),
        slot_roles=_v2_split_refs(row[4]),
        structural_asset_refs=_v2_split_refs(row[5]),
    )
    for row in _v2_inventory_rows("COMPLEMENT")
)
V2_SENSE_COMPLEMENT_LICENSE_REGISTRY = tuple(
    SenseComplementLicense(
        license_id=row[1],
        sense_ref=row[2],
        frame_ref=row[3],
        complement_rule_ref=row[4],
        classifier_ref=_v2_optional_ref(row[5]),
    )
    for row in _v2_inventory_rows("SENSE_COMPLEMENT")
)
V2_SOURCE_REALIZATION_MODE_REGISTRY = tuple(
    SourceRealizationMode(row[2]) for row in _v2_inventory_rows("SOURCE_MODE")
)
V2_SOURCE_CLASSIFIER_REGISTRY = tuple(
    SourceClassifierSpec(
        classifier_id=row[1],
        classifier_kind=row[2],
        atomic_surface=row[3],
    )
    for row in _v2_inventory_rows("CLASSIFIER")
)
V2_SOURCE_FUNCTIONAL_TOKEN_REGISTRY = tuple(
    SourceFunctionalTokenSpec(
        token_id=row[1],
        token_kind=row[2],
        atomic_surface=row[3],
    )
    for row in _v2_inventory_rows("SOURCE_TOKEN")
)
V2_SOURCE_FUNCTIONAL_MODIFIER_REGISTRY = tuple(
    SourceFunctionalModifierSpec(
        modifier_id=row[1],
        frame_ref=row[2],
        placement=row[3],
        atomic_surface=row[4],
    )
    for row in _v2_inventory_rows("MODIFIER")
)
V2_SOURCE_QUOTE_DELIMITER_REGISTRY = tuple(
    SourceQuoteDelimiterRule(
        delimiter_rule_id=row[1],
        source_quote_topology=SourceQuoteTopology(row[2]),
        outer_delimiter_kind=row[3],
    )
    for row in _v2_inventory_rows("QUOTE_DELIMITER")
)
V2_CASE_PARTICLE_REGISTRY = tuple(
    CaseParticleRule(
        particle_rule_id=row[1],
        frame_ref=row[2],
        slot_role=row[3],
        surface_variants=tuple(
            CaseParticleSurfaceVariant(*variant.split("_", 1))
            for variant in row[4:]
        ),
    )
    for row in _v2_inventory_rows("PARTICLE")
)
V2_INFLECTION_CLASS_REGISTRY = tuple(
    InflectionClassSpec(
        inflection_class_id=row[1],
        inflection_class=row[2],
    )
    for row in _v2_inventory_rows("INFLECTION_CLASS")
)
V2_MATRIX_MORPHOLOGY_PARADIGM_REGISTRY = tuple(
    MatrixMorphologyParadigmSpec(
        morphology_id=row[1],
        frame_ref=row[2],
        aspect_time=row[3],
        polarity=row[4],
        modal=row[5],
        politeness=row[6],
        inflection_recipe=row[7],
        terminal_class=row[8],
    )
    for row in _v2_inventory_rows("MORPHOLOGY")
)
V2_CLAUSE_LINK_REGISTRY = tuple(
    ClauseLinkRule(
        link_rule_id=row[1],
        relation_kind=row[2],
        placement=row[3],
        token_ref=row[4],
        internal_relation_policy=row[5],
    )
    for row in _v2_inventory_rows("LINK")
)
V2_REFERENCE_ZERO_TOPIC_REGISTRY = tuple(
    ReferenceZeroTopicRule(
        reference_rule_id=row[1],
        discourse_condition=row[2],
        realization_kind=row[3],
    )
    for row in _v2_inventory_rows("REFERENCE")
)
V2_REFERENCE_SURFACE_REGISTRY_EXACT2 = (
    V2ReferenceSurfaceSpec(
        surface_ref="reference-surface:singular-anaphor.v2",
        reference_rule_ref="R03",
        atomic_surface="そのこと",
        source_cardinality=SourceLeafCardinality.EXACT1,
        licensed_frame_refs=(
            "F01",
            "F02",
            "F03",
            "F04",
            "F10",
            "F11",
            "F12",
            "F14",
            "F16",
            "F17",
            "F19",
        ),
    ),
    V2ReferenceSurfaceSpec(
        surface_ref="reference-surface:ordered-pair-anaphor.v2",
        reference_rule_ref="R04",
        atomic_surface="その両方",
        source_cardinality=SourceLeafCardinality.ORDERED_EXACT2,
        licensed_frame_refs=("F13", "F23"),
    ),
)
V2_JAPANESE_LOCAL_PREFERENCE_REGISTRY = tuple(
    JapaneseLocalPreferenceRule(
        preference_rule_id=row[1],
        preference_kind=row[2],
    )
    for row in _v2_inventory_rows("PREFERENCE")
)

V2_PARTICLE_WRONG_TARGET = (
    ("が", "を"),
    ("は", "を"),
    ("を", "が"),
    ("と", "を"),
    ("のあとに", "によって"),
    ("によって", "のあとに"),
    ("から", "に"),
    ("に", "から"),
)
V2_COMPLEMENT_WRONG_TARGET = (
    ("C02", "C03"),
    ("C03", "C04"),
    ("C04", "C05"),
    ("C05", "C06"),
    ("C06", "C07"),
    ("C07", "C08"),
    ("C08", "C09"),
    ("C09", "C02"),
)
V2_LINK_WRONG_TARGET = tuple(
    (
        f"L{index:02d}",
        f"L{index + 1:02d}" if index < 11 else "L01",
    )
    for index in range(1, 12)
)
V2_CONTINUATIVE_WRONG_TARGET = (
    ("ONBIN_TE_IRU_MASU", "ONBIN_TE"),
    ("STEM_MASU", "STEM_CONTINUATIVE"),
    ("ONBIN_DE_IRU_MASU", "ONBIN_DE"),
    ("ONBIN_ITE_IRU_MASU", "ONBIN_ITE"),
    ("STEM_TE_IRU_MASU", "STEM_TE"),
    ("STEM_TAI_DESU", "STEM_TAI"),
    ("STEM_TAKU_ARIMASEN", "STEM_TAKU"),
    ("SAHEN_SHI_TAI_DESU", "SAHEN_SHI_TAI"),
    ("SAHEN_SHI_TAKU_ARIMASEN", "SAHEN_SHI_TAKU"),
)


def _v2_mutation_case_registry() -> Tuple[Tuple[str, str, str], ...]:
    """Derive the closed applicable corpus from frozen typed owners."""

    particle_wrong_target = dict(V2_PARTICLE_WRONG_TARGET)
    complement_wrong_target = dict(V2_COMPLEMENT_WRONG_TARGET)
    continuative_wrong_target = dict(V2_CONTINUATIVE_WRONG_TARGET)
    link_wrong_target = dict(V2_LINK_WRONG_TARGET)
    cases: list[Tuple[str, str, str]] = []
    for rule in V2_CASE_PARTICLE_REGISTRY:
        for variant in rule.surface_variants:
            base_ref = (
                f"{rule.particle_rule_id}:"
                f"{variant.variant_kind}:{variant.atomic_surface}"
            )
            cases.extend(
                (
                    (base_ref, "PARTICLE_DROP", "DROP"),
                    (
                        base_ref,
                        "PARTICLE_DUPLICATE",
                        f"{variant.variant_kind}:{variant.atomic_surface}",
                    ),
                    (
                        base_ref,
                        "PARTICLE_WRONG_SWAP",
                        particle_wrong_target[variant.atomic_surface],
                    ),
                )
            )
    cases.extend(
        (f"{frame.frame_id}:{slot_role}", "REQUIRED_SLOT_DROP", "DROP")
        for frame in V2_JAPANESE_CASE_FRAME_REGISTRY
        for slot_role, requirement in zip(
            frame.slot_roles,
            frame.slot_requirements,
        )
        if requirement == "required"
    )
    cases.extend(
        (
            row.license_id,
            "COMPLEMENT_SWAP",
            complement_wrong_target[row.complement_rule_ref],
        )
        for row in V2_SENSE_COMPLEMENT_LICENSE_REGISTRY
    )
    cases.extend(
        (
            row.morphology_id,
            "FINITE_TO_CONTINUATIVE",
            continuative_wrong_target[row.inflection_recipe],
        )
        for row in V2_MATRIX_MORPHOLOGY_PARADIGM_REGISTRY
    )
    cases.extend(
        (
            row.link_rule_id,
            "ILLEGAL_CONNECTIVE",
            link_wrong_target[row.link_rule_id],
        )
        for row in V2_CLAUSE_LINK_REGISTRY
    )
    return tuple(sorted(cases))


V2_MUTATION_CASE_REGISTRY = _v2_mutation_case_registry()
V2_MUTATION_CASE_COUNT = 297

# The source boundary is a closed public-typed verification table.  Payload
# bytes are never stored here: the table enumerates only the shape predicate,
# group cardinality, mode/cardinality compatibility, and delimiter ownership.
V2_SOURCE_PRIMITIVE_BOUNDARY_ROWS = tuple(
    (
        extent,
        sentence_shape,
        terminal_class,
        quote_topology,
        line_break_shape,
    )
    for extent in SourceLeafExtent
    for sentence_shape in SourceSentenceShape
    for terminal_class in SourceFinalTerminalClass
    for quote_topology in SourceQuoteTopology
    for line_break_shape in SourceLineBreakShape
)
V2_SOURCE_GROUP_CARDINALITY_ROWS = tuple(SourceLeafCardinality)
V2_SOURCE_MODE_CARDINALITY_ROWS = tuple(
    (
        mode,
        cardinality,
        (
            cardinality is SourceLeafCardinality.EXACT1
            if mode
            in {
                SourceRealizationMode.QUOTE_COMPLEMENT,
                SourceRealizationMode.CONTENT_NOMINAL,
                SourceRealizationMode.CLASSIFIED_CONTENT,
            }
            else cardinality is SourceLeafCardinality.ORDERED_EXACT2
        ),
    )
    for mode in SourceRealizationMode
    for cardinality in SourceLeafCardinality
)
V2_SOURCE_QUOTE_DELIMITER_BOUNDARY_ROWS = tuple(
    (
        row.source_quote_topology,
        row.delimiter_rule_id,
        row.outer_delimiter_kind,
    )
    for row in V2_SOURCE_QUOTE_DELIMITER_REGISTRY
)
V2_SOURCE_BOUNDARY_ROWS = (
    *(
        ("PRIMITIVE", *row)
        for row in V2_SOURCE_PRIMITIVE_BOUNDARY_ROWS
    ),
    *(
        ("GROUP_CARDINALITY", row)
        for row in V2_SOURCE_GROUP_CARDINALITY_ROWS
    ),
    *(
        ("MODE_CARDINALITY", *row)
        for row in V2_SOURCE_MODE_CARDINALITY_ROWS
    ),
    *(
        ("QUOTE_DELIMITER", *row)
        for row in V2_SOURCE_QUOTE_DELIMITER_BOUNDARY_ROWS
    ),
)
V2_SOURCE_BOUNDARY_ROW_COUNT = 208


def _v2_typed_inventory_rows() -> Tuple[Tuple[str, ...], ...]:
    """Reverse-project every typed row to the canonical literal field order."""

    rows: list[Tuple[str, ...]] = []
    rows.extend(
        (
            "SENSE",
            row.sense_id,
            row.sentence_job,
            row.semantic_clause_kind,
            row.semantic_sense,
            ",".join(row.frame_license_refs),
        )
        for row in V2_PREDICATE_SENSE_REGISTRY
    )
    rows.extend(
        (
            "FRAME",
            row.frame_id,
            row.sense_ref,
            row.frame_kind,
            ",".join(row.slot_roles),
            *row.slot_requirements,
            row.complement_rule_ref,
            row.topic_policy,
            row.zero_policy,
            row.atomic_head_ref,
            row.morphology_ref,
            row.modifier_ref or "NONE",
        )
        for row in V2_JAPANESE_CASE_FRAME_REGISTRY
    )
    rows.extend(
        (
            "HEAD",
            row.head_id,
            row.frame_ref,
            "+".join(row.atomic_parts),
            row.inflection_class_ref,
            row.lexical_family_ref,
        )
        for row in V2_ATOMIC_PREDICATE_HEAD_REGISTRY
    )
    rows.extend(
        (
            "LEXICAL_FAMILY",
            row.lexical_family_id,
            "+".join(row.atomic_parts),
        )
        for row in V2_LEXICAL_FAMILY_REGISTRY
    )
    rows.extend(
        (
            "COMPLEMENT",
            row.complement_rule_id,
            row.mode.value,
            row.cardinality.value,
            ",".join(row.slot_roles),
            ",".join(row.structural_asset_refs),
        )
        for row in V2_COMPLEMENT_RULE_REGISTRY
    )
    rows.extend(
        (
            "SENSE_COMPLEMENT",
            row.license_id,
            row.sense_ref,
            row.frame_ref,
            row.complement_rule_ref,
            row.classifier_ref or "NONE",
        )
        for row in V2_SENSE_COMPLEMENT_LICENSE_REGISTRY
    )
    rows.extend(
        ("SOURCE_MODE", f"SM{index:02d}", mode.value)
        for index, mode in enumerate(
            V2_SOURCE_REALIZATION_MODE_REGISTRY,
            start=1,
        )
    )
    rows.extend(
        (
            "CLASSIFIER",
            row.classifier_id,
            row.classifier_kind,
            row.atomic_surface,
        )
        for row in V2_SOURCE_CLASSIFIER_REGISTRY
    )
    rows.extend(
        ("SOURCE_TOKEN", row.token_id, row.token_kind, row.atomic_surface)
        for row in V2_SOURCE_FUNCTIONAL_TOKEN_REGISTRY
    )
    rows.extend(
        (
            "MODIFIER",
            row.modifier_id,
            row.frame_ref,
            row.placement,
            row.atomic_surface,
        )
        for row in V2_SOURCE_FUNCTIONAL_MODIFIER_REGISTRY
    )
    rows.extend(
        (
            "QUOTE_DELIMITER",
            row.delimiter_rule_id,
            row.source_quote_topology.value,
            row.outer_delimiter_kind,
        )
        for row in V2_SOURCE_QUOTE_DELIMITER_REGISTRY
    )
    rows.extend(
        (
            "PARTICLE",
            row.particle_rule_id,
            row.frame_ref,
            row.slot_role,
            *(
                f"{variant.variant_kind}_{variant.atomic_surface}"
                for variant in row.surface_variants
            ),
        )
        for row in V2_CASE_PARTICLE_REGISTRY
    )
    rows.extend(
        (
            "INFLECTION_CLASS",
            row.inflection_class_id,
            row.inflection_class,
        )
        for row in V2_INFLECTION_CLASS_REGISTRY
    )
    rows.extend(
        (
            "MORPHOLOGY",
            row.morphology_id,
            row.frame_ref,
            row.aspect_time,
            row.polarity,
            row.modal,
            row.politeness,
            row.inflection_recipe,
            row.terminal_class,
        )
        for row in V2_MATRIX_MORPHOLOGY_PARADIGM_REGISTRY
    )
    rows.extend(
        (
            "LINK",
            row.link_rule_id,
            row.relation_kind,
            row.placement,
            row.token_ref,
            row.internal_relation_policy,
        )
        for row in V2_CLAUSE_LINK_REGISTRY
    )
    rows.extend(
        (
            "REFERENCE",
            row.reference_rule_id,
            row.discourse_condition,
            row.realization_kind,
        )
        for row in V2_REFERENCE_ZERO_TOPIC_REGISTRY
    )
    rows.extend(
        ("PREFERENCE", row.preference_rule_id, row.preference_kind)
        for row in V2_JAPANESE_LOCAL_PREFERENCE_REGISTRY
    )
    return tuple(rows)


_V2_REGISTRY_TYPES = (
    PredicateSenseSpec,
    PredicateSenseFrameLicense,
    JapaneseCaseFrameSpec,
    AtomicPredicateHeadSpec,
    LexicalFamilySpec,
    ComplementRuleSpec,
    SenseComplementLicense,
    SourceClassifierSpec,
    SourceFunctionalTokenSpec,
    SourceFunctionalModifierSpec,
    SourceQuoteDelimiterRule,
    CaseParticleRule,
    CaseParticleSurfaceVariant,
    InflectionClassSpec,
    MatrixMorphologyParadigmSpec,
    ClauseLinkRule,
    ReferenceZeroTopicRule,
    V2ReferenceSurfaceSpec,
    JapaneseLocalPreferenceRule,
)


def _v2_unique(values: Tuple[str, ...], stop: str) -> frozenset[str]:
    if len(values) != len(set(values)):
        raise Stage1CompositionError(stop)
    return frozenset(values)


def validate_v2_grammar_inventory() -> None:
    """Fail closed on any drift in the registered, disabled Route-A v2 surface."""

    _validate_v2_grammar_inventory_literal()
    if _v2_typed_inventory_rows() != V2_GRAMMAR_INVENTORY_ROWS:
        raise Stage1CompositionError(
            "GRAMMAR_INVENTORY_TYPED_PROJECTION_DRIFT_STOP"
        )

    closed_enum_values = (
        (
            SourceLeafExtent,
            ("FULL_EVIDENCE_LITERAL", "CERTIFIED_LITERAL_SUBSPAN"),
        ),
        (SourceLeafCardinality, ("EXACT1", "ORDERED_EXACT2")),
        (SourceSentenceShape, ("ONE_SENTENCE", "MULTI_SENTENCE")),
        (
            SourceFinalTerminalClass,
            ("ABSENT", "PERIOD", "QUESTION", "EXCLAMATION"),
        ),
        (
            SourceQuoteTopology,
            (
                "NONE",
                "BALANCED_KAGI_ONLY",
                "BALANCED_NIJUKAGI_ONLY",
                "BALANCED_MIXED",
            ),
        ),
        (SourceLineBreakShape, ("NONE", "LF_ONLY", "CRLF_ONLY")),
        (
            SourceRealizationMode,
            (
                "QUOTE_COMPLEMENT",
                "CONTENT_NOMINAL",
                "CLASSIFIED_CONTENT",
                "COORDINATED_EXACT2",
                "BOUNDARY_SPLIT_EXACT2",
            ),
        ),
    )
    if any(
        tuple(member.value for member in enum_type) != expected
        for enum_type, expected in closed_enum_values
    ):
        raise Stage1CompositionError("GRAMMAR_INVENTORY_CLOSED_ENUM_STOP")

    senses = _v2_unique(
        tuple(row.sense_id for row in V2_PREDICATE_SENSE_REGISTRY),
        "GRAMMAR_INVENTORY_SENSE_NONUNIQUE_STOP",
    )
    frames = _v2_unique(
        tuple(row.frame_id for row in V2_JAPANESE_CASE_FRAME_REGISTRY),
        "GRAMMAR_INVENTORY_FRAME_NONUNIQUE_STOP",
    )
    heads = _v2_unique(
        tuple(row.head_id for row in V2_ATOMIC_PREDICATE_HEAD_REGISTRY),
        "GRAMMAR_INVENTORY_HEAD_NONUNIQUE_STOP",
    )
    lexical_families = _v2_unique(
        tuple(row.lexical_family_id for row in V2_LEXICAL_FAMILY_REGISTRY),
        "GRAMMAR_INVENTORY_LEXICAL_FAMILY_NONUNIQUE_STOP",
    )
    complements = _v2_unique(
        tuple(row.complement_rule_id for row in V2_COMPLEMENT_RULE_REGISTRY),
        "GRAMMAR_INVENTORY_COMPLEMENT_NONUNIQUE_STOP",
    )
    classifiers = _v2_unique(
        tuple(row.classifier_id for row in V2_SOURCE_CLASSIFIER_REGISTRY),
        "GRAMMAR_INVENTORY_CLASSIFIER_NONUNIQUE_STOP",
    )
    functional_tokens = _v2_unique(
        tuple(row.token_id for row in V2_SOURCE_FUNCTIONAL_TOKEN_REGISTRY),
        "GRAMMAR_INVENTORY_SOURCE_TOKEN_NONUNIQUE_STOP",
    )
    modifiers = _v2_unique(
        tuple(row.modifier_id for row in V2_SOURCE_FUNCTIONAL_MODIFIER_REGISTRY),
        "GRAMMAR_INVENTORY_MODIFIER_NONUNIQUE_STOP",
    )
    inflection_classes = _v2_unique(
        tuple(row.inflection_class_id for row in V2_INFLECTION_CLASS_REGISTRY),
        "GRAMMAR_INVENTORY_INFLECTION_NONUNIQUE_STOP",
    )
    morphologies = _v2_unique(
        tuple(row.morphology_id for row in V2_MATRIX_MORPHOLOGY_PARADIGM_REGISTRY),
        "GRAMMAR_INVENTORY_MORPHOLOGY_NONUNIQUE_STOP",
    )
    _v2_unique(
        tuple(row.license_id for row in V2_SENSE_COMPLEMENT_LICENSE_REGISTRY),
        "GRAMMAR_INVENTORY_SENSE_COMPLEMENT_NONUNIQUE_STOP",
    )
    _v2_unique(
        tuple(row.delimiter_rule_id for row in V2_SOURCE_QUOTE_DELIMITER_REGISTRY),
        "GRAMMAR_INVENTORY_DELIMITER_NONUNIQUE_STOP",
    )
    _v2_unique(
        tuple(row.particle_rule_id for row in V2_CASE_PARTICLE_REGISTRY),
        "GRAMMAR_INVENTORY_PARTICLE_NONUNIQUE_STOP",
    )
    _v2_unique(
        tuple(row.link_rule_id for row in V2_CLAUSE_LINK_REGISTRY),
        "GRAMMAR_INVENTORY_LINK_NONUNIQUE_STOP",
    )
    _v2_unique(
        tuple(row.reference_rule_id for row in V2_REFERENCE_ZERO_TOPIC_REGISTRY),
        "GRAMMAR_INVENTORY_REFERENCE_NONUNIQUE_STOP",
    )
    reference_surfaces = V2_REFERENCE_SURFACE_REGISTRY_EXACT2
    if (
        len(reference_surfaces) != 2
        or tuple(row.reference_rule_ref for row in reference_surfaces)
        != ("R03", "R04")
        or tuple(row.source_cardinality for row in reference_surfaces)
        != (
            SourceLeafCardinality.EXACT1,
            SourceLeafCardinality.ORDERED_EXACT2,
        )
        or len({row.surface_ref for row in reference_surfaces}) != 2
        or len({row.atomic_surface for row in reference_surfaces}) != 2
        or any(
            not row.atomic_surface
            or any(mark in row.atomic_surface for mark in ("。", "！", "？", "「", "」"))
            or not row.licensed_frame_refs
            or len(row.licensed_frame_refs) != len(set(row.licensed_frame_refs))
            for row in reference_surfaces
        )
    ):
        raise Stage1CompositionError(
            "GRAMMAR_INVENTORY_REFERENCE_SURFACE_EXACT2_STOP"
        )
    _v2_unique(
        tuple(row.preference_rule_id for row in V2_JAPANESE_LOCAL_PREFERENCE_REGISTRY),
        "GRAMMAR_INVENTORY_PREFERENCE_NONUNIQUE_STOP",
    )

    licensed_pairs = tuple(
        (row.sense_ref, row.frame_ref)
        for row in V2_PREDICATE_SENSE_FRAME_LICENSE_REGISTRY
    )
    frame_pairs = tuple(
        (row.sense_ref, row.frame_id) for row in V2_JAPANESE_CASE_FRAME_REGISTRY
    )
    if (
        len(licensed_pairs) != 24
        or len(set(licensed_pairs)) != 24
        or frozenset(licensed_pairs) != frozenset(frame_pairs)
        or any(row.sense_ref not in senses for row in V2_JAPANESE_CASE_FRAME_REGISTRY)
    ):
        raise Stage1CompositionError("GRAMMAR_INVENTORY_SENSE_FRAME_COVER_STOP")

    head_by_frame = {
        row.frame_ref: row for row in V2_ATOMIC_PREDICATE_HEAD_REGISTRY
    }
    morphology_by_frame = {
        row.frame_ref: row for row in V2_MATRIX_MORPHOLOGY_PARADIGM_REGISTRY
    }
    complement_by_frame = {
        row.frame_ref: row for row in V2_SENSE_COMPLEMENT_LICENSE_REGISTRY
    }
    modifier_by_frame = {
        row.frame_ref: row for row in V2_SOURCE_FUNCTIONAL_MODIFIER_REGISTRY
    }
    particles_by_frame_slot = {
        (row.frame_ref, row.slot_role): row for row in V2_CASE_PARTICLE_REGISTRY
    }
    if (
        len(head_by_frame) != len(V2_ATOMIC_PREDICATE_HEAD_REGISTRY)
        or len(morphology_by_frame) != len(V2_MATRIX_MORPHOLOGY_PARADIGM_REGISTRY)
        or len(complement_by_frame) != len(V2_SENSE_COMPLEMENT_LICENSE_REGISTRY)
        or len(modifier_by_frame) != len(V2_SOURCE_FUNCTIONAL_MODIFIER_REGISTRY)
        or len(particles_by_frame_slot) != len(V2_CASE_PARTICLE_REGISTRY)
    ):
        raise Stage1CompositionError("GRAMMAR_INVENTORY_OWNER_NONUNIQUE_STOP")

    for frame in V2_JAPANESE_CASE_FRAME_REGISTRY:
        head = head_by_frame.get(frame.frame_id)
        morphology = morphology_by_frame.get(frame.frame_id)
        complement = complement_by_frame.get(frame.frame_id)
        frame_particle_slots = frozenset(
            slot
            for (frame_ref, slot), _row in particles_by_frame_slot.items()
            if frame_ref == frame.frame_id
        )
        if (
            len(frame.slot_roles) != len(frame.slot_requirements)
            or any(requirement != "required" for requirement in frame.slot_requirements)
            or frame_particle_slots != frozenset(frame.slot_roles)
            or head is None
            or head.head_id != frame.atomic_head_ref
            or head.lexical_family_ref not in lexical_families
            or head.inflection_class_ref not in inflection_classes
            or morphology is None
            or morphology.morphology_id != frame.morphology_ref
            or complement is None
            or complement.sense_ref != frame.sense_ref
            or complement.complement_rule_ref != frame.complement_rule_ref
            or frame.complement_rule_ref not in complements
            or (
                complement.classifier_ref is not None
                and complement.classifier_ref not in classifiers
            )
            or (
                frame.modifier_ref is None
                and frame.frame_id in modifier_by_frame
            )
            or (
                frame.modifier_ref is not None
                and (
                    frame.modifier_ref not in modifiers
                    or modifier_by_frame.get(frame.frame_id) is None
                    or modifier_by_frame[frame.frame_id].modifier_id
                    != frame.modifier_ref
                )
            )
        ):
            raise Stage1CompositionError("GRAMMAR_INVENTORY_FRAME_TOTALITY_STOP")

    referenced_assets = frozenset(
        asset_ref
        for row in V2_COMPLEMENT_RULE_REGISTRY
        for asset_ref in row.structural_asset_refs
        if asset_ref.startswith("SF")
    )
    if (
        {row.mode for row in V2_COMPLEMENT_RULE_REGISTRY}
        != set(SourceRealizationMode)
        or tuple(V2_SOURCE_REALIZATION_MODE_REGISTRY)
        != tuple(SourceRealizationMode)
        or set(row.source_quote_topology for row in V2_SOURCE_QUOTE_DELIMITER_REGISTRY)
        != set(SourceQuoteTopology)
        or set(row.complement_rule_ref for row in V2_JAPANESE_CASE_FRAME_REGISTRY)
        != complements
        or set(row.head_id for row in V2_ATOMIC_PREDICATE_HEAD_REGISTRY) != heads
        or set(row.lexical_family_ref for row in V2_ATOMIC_PREDICATE_HEAD_REGISTRY)
        != lexical_families
        or set(row.inflection_class_ref for row in V2_ATOMIC_PREDICATE_HEAD_REGISTRY)
        != inflection_classes
        or set(row.morphology_ref for row in V2_JAPANESE_CASE_FRAME_REGISTRY)
        != morphologies
        or any(
            frame_ref not in frames
            for row in V2_REFERENCE_SURFACE_REGISTRY_EXACT2
            for frame_ref in row.licensed_frame_refs
        )
        or set(
            row.modifier_ref
            for row in V2_JAPANESE_CASE_FRAME_REGISTRY
            if row.modifier_ref is not None
        )
        != modifiers
        or set(
            row.classifier_ref
            for row in V2_SENSE_COMPLEMENT_LICENSE_REGISTRY
            if row.classifier_ref is not None
        )
        != classifiers
        or referenced_assets != functional_tokens
        or sum(
            len(row.surface_variants) for row in V2_CASE_PARTICLE_REGISTRY
        )
        != 64
    ):
        raise Stage1CompositionError("GRAMMAR_INVENTORY_ORPHAN_STOP")

    expected_mode_cardinality = {
        SourceRealizationMode.QUOTE_COMPLEMENT:
            SourceLeafCardinality.EXACT1,
        SourceRealizationMode.CONTENT_NOMINAL:
            SourceLeafCardinality.EXACT1,
        SourceRealizationMode.CLASSIFIED_CONTENT:
            SourceLeafCardinality.EXACT1,
        SourceRealizationMode.COORDINATED_EXACT2:
            SourceLeafCardinality.ORDERED_EXACT2,
        SourceRealizationMode.BOUNDARY_SPLIT_EXACT2:
            SourceLeafCardinality.ORDERED_EXACT2,
    }
    if (
        len(V2_SOURCE_PRIMITIVE_BOUNDARY_ROWS) != 192
        or len(set(V2_SOURCE_PRIMITIVE_BOUNDARY_ROWS)) != 192
        or V2_SOURCE_GROUP_CARDINALITY_ROWS != tuple(SourceLeafCardinality)
        or len(V2_SOURCE_MODE_CARDINALITY_ROWS) != 10
        or len(set(V2_SOURCE_MODE_CARDINALITY_ROWS)) != 10
        or any(
            licensed
            is not (expected_mode_cardinality[mode] is cardinality)
            for mode, cardinality, licensed in V2_SOURCE_MODE_CARDINALITY_ROWS
        )
        or V2_SOURCE_QUOTE_DELIMITER_BOUNDARY_ROWS
        != tuple(
            (
                row.source_quote_topology,
                row.delimiter_rule_id,
                row.outer_delimiter_kind,
            )
            for row in V2_SOURCE_QUOTE_DELIMITER_REGISTRY
        )
        or len(V2_SOURCE_BOUNDARY_ROWS) != V2_SOURCE_BOUNDARY_ROW_COUNT
        or V2_SOURCE_BOUNDARY_ROW_COUNT != 208
    ):
        raise Stage1CompositionError("GRAMMAR_INVENTORY_SOURCE_BOUNDARY_STOP")

    mutation_registry = _v2_mutation_case_registry()
    mutation_operator_counts = tuple(
        (
            operator,
            sum(row[1] == operator for row in mutation_registry),
        )
        for operator in (
            "PARTICLE_DROP",
            "PARTICLE_DUPLICATE",
            "PARTICLE_WRONG_SWAP",
            "REQUIRED_SLOT_DROP",
            "COMPLEMENT_SWAP",
            "FINITE_TO_CONTINUATIVE",
            "ILLEGAL_CONNECTIVE",
        )
    )
    if (
        mutation_registry != V2_MUTATION_CASE_REGISTRY
        or tuple(sorted(mutation_registry)) != mutation_registry
        or len(mutation_registry) != len(set(mutation_registry))
        or len(mutation_registry) != V2_MUTATION_CASE_COUNT
        or V2_MUTATION_CASE_COUNT != 297
        or mutation_operator_counts
        != (
            ("PARTICLE_DROP", 64),
            ("PARTICLE_DUPLICATE", 64),
            ("PARTICLE_WRONG_SWAP", 64),
            ("REQUIRED_SLOT_DROP", 46),
            ("COMPLEMENT_SWAP", 24),
            ("FINITE_TO_CONTINUATIVE", 24),
            ("ILLEGAL_CONNECTIVE", 11),
        )
    ):
        raise Stage1CompositionError("GRAMMAR_INVENTORY_MUTATION_EXACT297_STOP")

    registry_field_names = tuple(
        field.name
        for registry_type in _V2_REGISTRY_TYPES
        for field in fields(registry_type)
    )
    validate_stage1_anti_template_registry_invariant(
        registry_field_names,
        (
            "typed_intent",
            "admitted_relation",
            "argument_roles",
            "typed_discourse_state",
        ),
        V2_GRAMMAR_INVENTORY_ROWS,
    )



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


@dataclass(frozen=True, slots=True)
class JapaneseCaseFrameKey:
    """Typed semantic key for the disabled Route-A v2 frame selector."""

    sentence_job: SentenceJob
    semantic_clause_kind: SemanticClauseKind
    subjective_content_kind: Optional[SubjectiveContentKind]
    subjective_predication_kind: Optional[SubjectivePredicationKind]
    subjective_semantic_sense: Optional[str]
    grounded_predicate_kind: Optional[str]
    required_argument_roles: Tuple[ClauseArgumentRole, ...]
    admitted_relation_operator: RelationOperator
    polarity: str
    modality: str
    time_scope: str
    speaker_requirement: SpeakerRequirement
    zero_subject_eligibility: str
    complement_requirement: str


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
    DEPENDENCY_PRESERVING_MERGE_SPLIT = (
        "DEPENDENCY_PRESERVING_MERGE_SPLIT"
    )
    INFORMATION_RELATION_ORDER = "INFORMATION_RELATION_ORDER"
    REFERENCE_SPEAKER_LINK_RECALCULATION = (
        "REFERENCE_SPEAKER_LINK_RECALCULATION"
    )
    GRAMMAR_BINDING_IR_LOCAL_REPAIR = "GRAMMAR_BINDING_IR_LOCAL_REPAIR"
    SOLE_LINEARIZATION_GRAMMAR_SEAL = "SOLE_LINEARIZATION_GRAMMAR_SEAL"


class NormalFormRepairKind(str, Enum):
    """The only four local repairs admitted by the Route-A v2 normal form."""

    AMBIGUOUS_ANAPHOR_TO_FULL_EXPRESSION = (
        "AMBIGUOUS_ANAPHOR_TO_FULL_EXPRESSION"
    )
    OVERLOADED_EXACT2_CLAUSE_UNIT_SPLIT = (
        "OVERLOADED_EXACT2_CLAUSE_UNIT_SPLIT"
    )
    REDUNDANT_CONNECTIVE_REMOVAL = "REDUNDANT_CONNECTIVE_REMOVAL"
    LICENSED_TOPIC_ALTERNANT_TO_BASE_CASE = (
        "LICENSED_TOPIC_ALTERNANT_TO_BASE_CASE"
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
    premeaning_inputs: PreMeaningGroundedInputs
    grounded_situation_view: GroundedSituationView
    foreground_scope_derivation: ForegroundScopeDerivation
    foreground_scope_disposition: ForegroundScopeDisposition
    input_specific_meaning_structure: InputSpecificMeaningStructure
    allowed_reception_opportunity_envelope: (
        AllowedReceptionOpportunityEnvelope
    )
    projection_preimage_ref: str
    reading_consequence_records: Tuple[ReadingConsequence, ...]
    sealed_emlis_provisional_reading_records: Tuple[
        SealedEmlisProvisionalReading, ...
    ]
    meaning_bound_reception_proposition_records: Tuple[
        MeaningBoundReceptionProposition, ...
    ]
    meaning_bound_reception_set_records: Tuple[
        MeaningBoundReceptionSet, ...
    ]
    bounded_limited_reception_records: Tuple[
        BoundedLimitedReception, ...
    ]
    bounded_limited_subjective_proposition_records: Tuple[
        SubjectivePropositionV2, ...
    ]
    projection_seal_ref: str
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
class _ProjectionCommonAuthority:
    """Branch-neutral, validation-only authority for tagged projection."""

    grounded_situation_view: GroundedSituationView
    foreground_scope_derivation: ForegroundScopeDerivation
    input_specific_meaning_structure: InputSpecificMeaningStructure
    admitted_source: Any
    grounded_graph: Any
    grounded_plan: Any
    grounded_graph_ref: str
    parent_plan: Any
    allowed_reception_opportunity_envelope: (
        AllowedReceptionOpportunityEnvelope
    )
    parent_observation_duty_ref: str
    projection_preimage_ref: str
    projection_seal_ref: str
    parent_reception_duty_ref: str
    meaning_field_id: str
    observation_depth_class: Any
    temperature_class: Any
    reception_style_policy_ref: str
    emlis_value_policy_ref: str
    interpretation_candidate_rows: Tuple[EmlisInterpretationCandidate, ...]
    observation_contribution_rows: Tuple[PlannedObservationContribution, ...]
    retained_reception_act_rows: Tuple[RetainedReceptionActRow, ...]
    material_unknown_refs: Tuple[str, ...]
    contribution_to_candidate_ref_map: Tuple[Tuple[str, str], ...]
    qualifier_value_by_candidate_scope_axis_key: Tuple[
        QualifierValueRow, ...
    ]


@dataclass(frozen=True, slots=True)
class SelectedReadingProjectionInputs:
    """NORMAL-only input; every post-selection record is the carried object."""

    common: _ProjectionCommonAuthority
    selected_reading: SelectedEmlisProvisionalReading
    reading_consequence_records: Tuple[ReadingConsequence, ...]
    sealed_reading_records: Tuple[SealedEmlisProvisionalReading, ...]
    reception_proposition_records: Tuple[
        MeaningBoundReceptionProposition, ...
    ]
    reception_set_records: Tuple[MeaningBoundReceptionSet, ...]


@dataclass(frozen=True, slots=True)
class LimitedProjectionInputs:
    """LIMITED-only input; deliberately has no selected-reading field."""

    common: _ProjectionCommonAuthority
    limited_outcome: LimitedMeaningOutcome
    bounded_reception_records: Tuple[BoundedLimitedReception, ...]
    subjective_proposition_records: Tuple[SubjectivePropositionV2, ...]


SubjectiveProjectionInputs = (
    SelectedReadingProjectionInputs | LimitedProjectionInputs
)


@dataclass(frozen=True, slots=True)
class Stage1SurfaceCompositionInputs:
    phase_A_authority: Stage1SubjectivePlanningInputs
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
    projection_seal_ref: str
    projection_branch: SubjectiveProjectionBranch
    tagged_projection_ref: str
    meaning_visible_causal_trace_rows: Tuple[
        SelectedMeaningVisibleCausalTraceRow
        | LimitedMeaningVisibleCausalTraceRow,
        ...,
    ]
    reception_visible_causal_trace_rows: Tuple[
        ReceptionVisibleCausalTraceRow, ...
    ]
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
    reception_projection_branch: Optional[SubjectiveProjectionBranch] = None
    reception_act_refs: Tuple[str, ...] = ()
    reception_content_kind: Optional[SubjectiveContentKind] = None
    reception_subjective_mode: Optional[SubjectiveMode] = None
    reception_subjective_operator: Optional[SubjectiveOperator] = None
    reception_semantic_operators: Tuple[SemanticOperator, ...] = ()
    reception_appraisal_dimension: Optional[AppraisalDimension] = None
    reception_appraisal_operation: Optional[AppraisalOperation] = None
    reception_relational_position_kind: Optional[
        RelationalPositionKind
    ] = None
    reception_stance_operator: Optional[StanceOperator] = None
    reception_relational_commitment: Optional[RelationalCommitment] = None
    reception_relational_closure: Optional[RelationalClosure] = None


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
class V2ClauseReferenceStateBundle:
    """Private dual state: Emlis subject and discourse object never alias."""

    state_ref: str
    subject_state: Optional[DiscourseReferenceStateRow]
    object_state: DiscourseReferenceStateRow
    response_object_expression: ResponseObjectExpression


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
class NormalFormRepairTraceRow:
    repair_kind: NormalFormRepairKind
    defect_tuple_before: Tuple[int, int, int, int]
    defect_tuple_after: Tuple[int, int, int, int]
    repaired_owner_refs: Tuple[str, ...]


@dataclass(frozen=True, slots=True)
class V2ClauseIRRow:
    """Private phase-5 closure before any visible text is produced."""

    duty_ref: str
    unit_ref: str
    source_leaves: Tuple[SourceLeafToken, ...]
    source_group: SourceLeafGroup
    frame: JapaneseCaseFrameSpec
    head: AtomicPredicateHeadSpec
    source_complement_plan: SourceComplementPlan
    argument_plans: Tuple[ArgumentRealizationPlan, ...]
    reference_state: V2ClauseReferenceStateBundle
    link_plan: ClauseLinkPlan
    morphology_plan: PredicateMorphologyPlan
    clause_ir: JapaneseClauseIR
    selected_expression_asset_ref: str
    clause_plan: Optional[ClausePlan] = None
    visible_meaning_trace_rows: Tuple[
        SelectedMeaningVisibleCausalTraceRow, ...
    ] = ()


@dataclass(frozen=True, slots=True)
class V2ClauseRealizationRow:
    """Private closure for one duty from opaque source leaves through seal."""

    duty_ref: str
    unit_ref: str
    source_leaves: Tuple[SourceLeafToken, ...]
    source_group: SourceLeafGroup
    frame: JapaneseCaseFrameSpec
    head: AtomicPredicateHeadSpec
    source_complement_plan: SourceComplementPlan
    argument_plans: Tuple[ArgumentRealizationPlan, ...]
    reference_state: V2ClauseReferenceStateBundle
    link_plan: ClauseLinkPlan
    morphology_plan: PredicateMorphologyPlan
    clause_ir: JapaneseClauseIR
    linearized_clause: LinearizedJapaneseClause
    selected_expression_asset_ref: str
    clause_plan: Optional[ClausePlan] = None
    visible_meaning_trace_rows: Tuple[
        SelectedMeaningVisibleCausalTraceRow, ...
    ] = ()


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
    clause_frames: Tuple[ClauseFrame, ...] = ()
    realized_semantic_bindings: Tuple[RealizedSemanticBinding, ...] = ()
    surface_derivations: Tuple[SurfaceDerivation, ...] = ()
    frame_refs: Tuple[str, ...] = ()
    atomic_head_refs: Tuple[str, ...] = ()
    lexical_family_refs: Tuple[str, ...] = ()
    source_group_refs: Tuple[str, ...] = ()
    reference_state_refs: Tuple[str, ...] = ()
    link_plan_refs: Tuple[str, ...] = ()
    morphology_plan_refs: Tuple[str, ...] = ()
    clause_ir_refs: Tuple[str, ...] = ()


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
    v2_clause_rows: Tuple[V2ClauseRealizationRow, ...] = ()
    repair_trace_rows: Tuple[NormalFormRepairTraceRow, ...] = ()
    repair_defect_tuple: Tuple[int, int, int, int] = (0, 0, 0, 0)


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
    japanese_local_preference_profile: JapaneseLocalPreferenceProfile


@dataclass(frozen=True, slots=True)
class Stage1CompositionResult:
    language_core_identity: str
    discourse_arc: Stage1DiscourseArcView
    internal_candidate_count: int
    ranked_candidates: Tuple[ArtifactCompositionCandidate, ...]
    selected_candidate: ArtifactCompositionCandidate
    validated_visible_causal_trace_seal_ref: str


def _ref(prefix: str, value: Any) -> str:
    return f"{prefix}-{hashlib.sha256(stage1_canonical_json_bytes(value)).hexdigest()}"


def _final_typed_ref(
    version: str,
    prefix: str,
    material: Tuple[Any, ...],
) -> str:
    if not version or not prefix or type(material) is not tuple:
        raise Stage1CompositionError("STAGE1_FINAL_IDENTITY_INPUT_STOP")
    return (
        f"{prefix}-"
        + hashlib.sha256(
            version.encode("utf-8")
            + b"\0"
            + stage1_canonical_json_bytes(material)
        ).hexdigest()
    )


def _unique(values: Iterable[str]) -> Tuple[str, ...]:
    return tuple(dict.fromkeys(values))


_V2_SOURCE_TERMINAL_CLASS_BY_CODEPOINT = (
    ("。", SourceFinalTerminalClass.PERIOD),
    ("．", SourceFinalTerminalClass.PERIOD),
    (".", SourceFinalTerminalClass.PERIOD),
    ("!", SourceFinalTerminalClass.EXCLAMATION),
    ("！", SourceFinalTerminalClass.EXCLAMATION),
    ("?", SourceFinalTerminalClass.QUESTION),
    ("？", SourceFinalTerminalClass.QUESTION),
)
_V2_RELATION_OPERATOR_BY_FRAME_REF = (
    ("F05", RelationOperator.COEXISTS_WITH),
    ("F06", RelationOperator.TENSION_WITH),
    ("F24", RelationOperator.TENSION_WITH),
    ("F07", RelationOperator.TEMPORALLY_PRECEDES),
    ("F08", RelationOperator.ACTION_PRECEDES_CHANGE),
    ("F09", RelationOperator.SOURCE_EXPLICIT_CAUSE),
)
_V2_SUBJECTIVE_KIND_BY_SENSE_REF = (
    (
        "S09",
        SubjectiveContentKind.AFFECT,
        SubjectivePredicationKind.AFFECT,
    ),
    *(
        (
            f"S{index:02d}",
            SubjectiveContentKind.APPRAISAL,
            SubjectivePredicationKind.APPRAISAL,
        )
        for index in range(10, 15)
    ),
    (
        "S15",
        SubjectiveContentKind.MATERIAL_VALUE,
        SubjectivePredicationKind.MATERIAL_VALUE,
    ),
    (
        "S16",
        SubjectiveContentKind.RELATIONAL_POSITION,
        SubjectivePredicationKind.RELATIONAL_STANCE,
    ),
    (
        "S17",
        SubjectiveContentKind.RELATIONAL_POSITION,
        SubjectivePredicationKind.BOUNDED_COUNTERPOSITION,
    ),
)


def _v2_exact1(rows: Sequence[Any], stop: str) -> Any:
    result = tuple(rows)
    if len(result) != 1:
        raise Stage1CompositionError(stop)
    return result[0]


def _v2_source_quote_witness(
    text: str,
) -> Tuple[SourceQuoteTopology, Tuple[int, ...]]:
    stack: list[str] = []
    seen_kagi = False
    seen_nijukagi = False
    outer_terminal_positions: list[int] = []
    open_to_close = {"「": "」", "『": "』"}
    for index, codepoint in enumerate(text):
        if codepoint in open_to_close:
            stack.append(open_to_close[codepoint])
            seen_kagi = seen_kagi or codepoint == "「"
            seen_nijukagi = seen_nijukagi or codepoint == "『"
            continue
        if codepoint in {"」", "』"}:
            if not stack or stack.pop() != codepoint:
                raise Stage1CompositionError(
                    "STAGE1_SOURCE_QUOTE_UNBALANCED_STOP"
                )
            continue
        if not stack and codepoint in dict(
            _V2_SOURCE_TERMINAL_CLASS_BY_CODEPOINT
        ):
            outer_terminal_positions.append(index)
    if stack:
        raise Stage1CompositionError("STAGE1_SOURCE_QUOTE_UNBALANCED_STOP")
    if seen_kagi and seen_nijukagi:
        topology = SourceQuoteTopology.BALANCED_MIXED
    elif seen_kagi:
        topology = SourceQuoteTopology.BALANCED_KAGI_ONLY
    elif seen_nijukagi:
        topology = SourceQuoteTopology.BALANCED_NIJUKAGI_ONLY
    else:
        topology = SourceQuoteTopology.NONE
    return topology, tuple(outer_terminal_positions)


def _v2_source_line_break_witness(text: str) -> SourceLineBreakShape:
    if "\r" not in text:
        return (
            SourceLineBreakShape.LF_ONLY
            if "\n" in text
            else SourceLineBreakShape.NONE
        )
    index = 0
    crlf_count = 0
    while index < len(text):
        if text[index] == "\r":
            if index + 1 >= len(text) or text[index + 1] != "\n":
                raise Stage1CompositionError(
                    "STAGE1_SOURCE_LINEBREAK_UNSUPPORTED_STOP"
                )
            crlf_count += 1
            index += 2
            continue
        if text[index] == "\n":
            raise Stage1CompositionError(
                "STAGE1_SOURCE_LINEBREAK_UNSUPPORTED_STOP"
            )
        index += 1
    if crlf_count == 0:
        raise Stage1CompositionError(
            "STAGE1_SOURCE_LINEBREAK_UNSUPPORTED_STOP"
        )
    return SourceLineBreakShape.CRLF_ONLY


def _validate_v2_source_leaf(
    leaf: SourceLeafToken,
    source_envelope_bindings: Sequence[Tuple[str, bytes]],
    evidence_literal_bindings: Sequence[Tuple[str, str, int, int]],
    certified_subspan_bindings: Sequence[Tuple[str, str, int, int]],
) -> None:
    if (
        type(leaf) is not SourceLeafToken
        or not leaf.leaf_ref
        or not leaf.semantic_ref
        or not leaf.source_envelope_ref
        or not leaf.evidence_ref
        or type(leaf.raw_utf8_start) is not int
        or type(leaf.raw_utf8_end) is not int
        or type(leaf.payload_utf8) is not bytes
    ):
        raise Stage1CompositionError(
            "STAGE1_SOURCE_LEAF_BINDING_NONUNIQUE_STOP"
        )
    if any(
        type(row) is not tuple or len(row) != 2
        for row in source_envelope_bindings
    ):
        raise Stage1CompositionError(
            "STAGE1_SOURCE_LEAF_BINDING_NONUNIQUE_STOP"
        )
    matching_raw_bindings = tuple(
        row
        for row in source_envelope_bindings
        if row[0] == leaf.source_envelope_ref
    )
    if any(type(row[1]) is not bytes for row in matching_raw_bindings):
        raise Stage1CompositionError(
            "STAGE1_SOURCE_LEAF_BINDING_NONUNIQUE_STOP"
        )
    raw_rows = tuple(row[1] for row in matching_raw_bindings)
    raw_utf8 = _v2_exact1(
        raw_rows,
        "STAGE1_SOURCE_LEAF_BINDING_NONUNIQUE_STOP",
    )
    if not (
        0 <= leaf.raw_utf8_start < leaf.raw_utf8_end <= len(raw_utf8)
    ):
        raise Stage1CompositionError("STAGE1_SOURCE_LEAF_UTF8_MISMATCH_STOP")
    if (
        raw_utf8[leaf.raw_utf8_start : leaf.raw_utf8_end]
        != leaf.payload_utf8
    ):
        raise Stage1CompositionError("STAGE1_SOURCE_LEAF_UTF8_MISMATCH_STOP")
    try:
        text = leaf.payload_utf8.decode("utf-8", errors="strict")
    except UnicodeDecodeError:
        raise Stage1CompositionError(
            "STAGE1_SOURCE_LEAF_UTF8_MISMATCH_STOP"
        ) from None
    if not text or text.encode("utf-8") != leaf.payload_utf8:
        raise Stage1CompositionError("STAGE1_SOURCE_LEAF_UTF8_MISMATCH_STOP")

    if any(
        type(row) is not tuple or len(row) != 4
        for row in evidence_literal_bindings
    ):
        raise Stage1CompositionError(
            "STAGE1_SOURCE_LEAF_BINDING_NONUNIQUE_STOP"
        )
    matching_evidence_bindings = tuple(
        row
        for row in evidence_literal_bindings
        if row[0] == leaf.evidence_ref
        and row[1] == leaf.source_envelope_ref
    )
    if any(
        type(row[2]) is not int or type(row[3]) is not int
        for row in matching_evidence_bindings
    ):
        raise Stage1CompositionError(
            "STAGE1_SOURCE_LEAF_BINDING_NONUNIQUE_STOP"
        )
    evidence_rows = tuple(
        (row[2], row[3]) for row in matching_evidence_bindings
    )
    evidence_start, evidence_end = _v2_exact1(
        evidence_rows,
        "STAGE1_SOURCE_LEAF_BINDING_NONUNIQUE_STOP",
    )
    if not (0 <= evidence_start < evidence_end <= len(raw_utf8)):
        raise Stage1CompositionError(
            "STAGE1_SOURCE_LEAF_BINDING_NONUNIQUE_STOP"
        )
    if leaf.extent is SourceLeafExtent.FULL_EVIDENCE_LITERAL:
        if (leaf.raw_utf8_start, leaf.raw_utf8_end) != (
            evidence_start,
            evidence_end,
        ):
            raise Stage1CompositionError(
                "STAGE1_SOURCE_LEAF_BINDING_NONUNIQUE_STOP"
            )
    elif leaf.extent is SourceLeafExtent.CERTIFIED_LITERAL_SUBSPAN:
        if any(
            type(row) is not tuple
            or len(row) != 4
            or type(row[2]) is not int
            or type(row[3]) is not int
            for row in certified_subspan_bindings
        ):
            raise Stage1CompositionError(
                "STAGE1_SOURCE_LITERAL_SUBSPAN_UNCERTIFIED_STOP"
            )
        certified_rows = tuple(
            (utf8_start, utf8_end)
            for evidence_ref, envelope_ref, utf8_start, utf8_end
            in certified_subspan_bindings
            if evidence_ref == leaf.evidence_ref
            and envelope_ref == leaf.source_envelope_ref
            and utf8_start == leaf.raw_utf8_start
            and utf8_end == leaf.raw_utf8_end
        )
        if (
            len(certified_rows) != 1
            or not (
                evidence_start
                <= leaf.raw_utf8_start
                < leaf.raw_utf8_end
                <= evidence_end
            )
        ):
            raise Stage1CompositionError(
                "STAGE1_SOURCE_LITERAL_SUBSPAN_UNCERTIFIED_STOP"
            )
    else:
        raise Stage1CompositionError(
            "STAGE1_SOURCE_LEAF_SHAPE_UNSUPPORTED_STOP"
        )

    quote_topology, outer_terminal_positions = _v2_source_quote_witness(text)
    line_break_shape = _v2_source_line_break_witness(text)
    terminal_class = dict(_V2_SOURCE_TERMINAL_CLASS_BY_CODEPOINT).get(
        text[-1],
        SourceFinalTerminalClass.ABSENT,
    )
    sentence_shape = (
        SourceSentenceShape.MULTI_SENTENCE
        if any(
            text[position + 1 :].strip()
            for position in outer_terminal_positions
            if position < len(text) - 1
        )
        else SourceSentenceShape.ONE_SENTENCE
    )
    if (
        quote_topology is not leaf.quote_topology
        or line_break_shape is not leaf.line_break_shape
        or terminal_class is not leaf.final_terminal_class
        or sentence_shape is not leaf.sentence_shape
    ):
        raise Stage1CompositionError(
            "STAGE1_SOURCE_LEAF_SHAPE_UNSUPPORTED_STOP"
        )
    if (
        type(leaf.derivation) is not SurfaceDerivation
        or leaf.derivation.derivation_kind
        is not SurfaceDerivationKind.LITERAL_SUBSPAN
        or leaf.derivation.source_or_claim_refs.count(leaf.semantic_ref) != 1
        or leaf.derivation.evidence_refs.count(leaf.evidence_ref) != 1
    ):
        raise Stage1CompositionError(
            "STAGE1_SOURCE_LEAF_BINDING_NONUNIQUE_STOP"
        )


def _validate_v2_source_group_cardinality(
    cardinality: SourceLeafCardinality,
    source_leaves: Sequence[SourceLeafToken],
) -> Tuple[str, ...]:
    leaves = tuple(source_leaves)
    expected_count = (
        1 if cardinality is SourceLeafCardinality.EXACT1 else 2
        if cardinality is SourceLeafCardinality.ORDERED_EXACT2 else 0
    )
    leaf_refs = tuple(
        leaf.leaf_ref if type(leaf) is SourceLeafToken else ""
        for leaf in leaves
    )
    if (
        type(cardinality) is not SourceLeafCardinality
        or expected_count == 0
        or len(leaves) != expected_count
        or not all(leaf_refs)
        or len(set(leaf_refs)) != len(leaf_refs)
    ):
        raise Stage1CompositionError("STAGE1_SOURCE_PAIR_CARDINALITY_STOP")
    return leaf_refs


def project_source_leaf_group(
    *,
    group_ref: str,
    cardinality: SourceLeafCardinality,
    source_leaves: Sequence[SourceLeafToken],
    source_envelope_bindings: Sequence[Tuple[str, bytes]],
    evidence_literal_bindings: Sequence[Tuple[str, str, int, int]],
    certified_subspan_bindings: Sequence[Tuple[str, str, int, int]] = (),
) -> SourceLeafGroup:
    """Validate opaque literal ownership and freeze ordered source refs."""

    validate_v2_grammar_inventory()
    if not group_ref:
        raise Stage1CompositionError(
            "STAGE1_SOURCE_LEAF_BINDING_NONUNIQUE_STOP"
        )
    leaves = tuple(source_leaves)
    leaf_refs = _validate_v2_source_group_cardinality(cardinality, leaves)
    for leaf in leaves:
        _validate_v2_source_leaf(
            leaf,
            source_envelope_bindings,
            evidence_literal_bindings,
            certified_subspan_bindings,
        )
    return SourceLeafGroup(
        group_ref=group_ref,
        cardinality=cardinality,
        ordered_leaf_refs=leaf_refs,
    )


def _validate_v2_projected_group_members(
    group: SourceLeafGroup,
    source_leaves: Sequence[SourceLeafToken],
) -> Tuple[SourceLeafToken, ...]:
    if type(group) is not SourceLeafGroup or not group.group_ref:
        raise Stage1CompositionError("STAGE1_SOURCE_PAIR_CARDINALITY_STOP")
    leaves = tuple(source_leaves)
    leaf_refs = _validate_v2_source_group_cardinality(
        group.cardinality,
        leaves,
    )
    if group.ordered_leaf_refs != leaf_refs:
        raise Stage1CompositionError("STAGE1_SOURCE_PAIR_CARDINALITY_STOP")
    return leaves


def _v2_complement_case_slots(
    rule: ComplementRuleSpec,
    frame: JapaneseCaseFrameSpec,
) -> Tuple[str, ...]:
    if rule.slot_roles == ("MONADIC_SUBJECT",):
        slots = ("SUBJECT",)
    elif rule.slot_roles == ("PAIRED_ENDPOINTS",):
        slots = frame.slot_roles
    else:
        slots = rule.slot_roles
    if (
        not slots
        or any(slot not in frame.slot_roles for slot in slots)
        or (
            rule.cardinality is SourceLeafCardinality.ORDERED_EXACT2
            and rule.complement_rule_id in {"C07", "C09"}
            and len(slots) != 2
        )
    ):
        raise Stage1CompositionError(
            "STAGE1_SOURCE_COMPLEMENT_NONUNIQUE_STOP"
        )
    return slots


def select_source_complement_plan(
    *,
    group: SourceLeafGroup,
    source_leaves: Sequence[SourceLeafToken],
    frame: JapaneseCaseFrameSpec,
) -> SourceComplementPlan:
    """Select the licensed complement without reading source payload text."""

    validate_v2_grammar_inventory()
    frame = _v2_exact1(
        tuple(
            row
            for row in V2_JAPANESE_CASE_FRAME_REGISTRY
            if row == frame
        ),
        "STAGE1_JAPANESE_CASE_FRAME_NONUNIQUE_STOP",
    )
    leaves = _validate_v2_projected_group_members(group, source_leaves)
    license_row = _v2_exact1(
        tuple(
            row
            for row in V2_SENSE_COMPLEMENT_LICENSE_REGISTRY
            if row.sense_ref == frame.sense_ref
            and row.frame_ref == frame.frame_id
            and row.complement_rule_ref == frame.complement_rule_ref
        ),
        "STAGE1_SOURCE_COMPLEMENT_NONUNIQUE_STOP",
    )
    rule = _v2_exact1(
        tuple(
            row
            for row in V2_COMPLEMENT_RULE_REGISTRY
            if row.complement_rule_id == license_row.complement_rule_ref
        ),
        "STAGE1_SOURCE_COMPLEMENT_NONUNIQUE_STOP",
    )
    compatibility = _v2_exact1(
        tuple(
            licensed
            for mode, cardinality, licensed
            in V2_SOURCE_MODE_CARDINALITY_ROWS
            if mode is rule.mode and cardinality is group.cardinality
        ),
        "STAGE1_SOURCE_COMPLEMENT_NONUNIQUE_STOP",
    )
    if not compatibility or rule.cardinality is not group.cardinality:
        raise Stage1CompositionError("STAGE1_SOURCE_PAIR_CARDINALITY_STOP")

    direct_source_safe = all(
        leaf.sentence_shape is SourceSentenceShape.ONE_SENTENCE
        and
        leaf.final_terminal_class
        is SourceFinalTerminalClass.ABSENT
        and leaf.line_break_shape is SourceLineBreakShape.NONE
        for leaf in leaves
    )
    delimiter_refs: list[str] = []
    if (
        "OUTER_QUOTES" in rule.structural_asset_refs
        or not direct_source_safe
    ):
        for leaf in leaves:
            delimiter = _v2_exact1(
                tuple(
                    row
                    for row in V2_SOURCE_QUOTE_DELIMITER_REGISTRY
                    if row.source_quote_topology is leaf.quote_topology
                ),
                "STAGE1_SOURCE_COMPLEMENT_NONUNIQUE_STOP",
            )
            if delimiter.outer_delimiter_kind == "STOP":
                raise Stage1CompositionError(
                    "SOURCE_OUTER_DELIMITER_UNAVAILABLE_STOP"
                )
            delimiter_refs.append(delimiter.delimiter_rule_id)

    classifier_ref: Optional[str] = None
    expects_classifier = "CLASSIFIER_EXACT1" in rule.structural_asset_refs
    if expects_classifier:
        classifier = _v2_exact1(
            tuple(
                row
                for row in V2_SOURCE_CLASSIFIER_REGISTRY
                if row.classifier_id == license_row.classifier_ref
            ),
            "STAGE1_SOURCE_CLASSIFIER_NONUNIQUE_STOP",
        )
        classifier_ref = classifier.classifier_id
    elif license_row.classifier_ref is not None:
        raise Stage1CompositionError(
            "STAGE1_SOURCE_CLASSIFIER_NONUNIQUE_STOP"
        )

    coordinator_ref: Optional[str] = None
    if "SF03" in rule.structural_asset_refs:
        coordinator = _v2_exact1(
            tuple(
                row
                for row in V2_SOURCE_FUNCTIONAL_TOKEN_REGISTRY
                if row.token_id == "SF03"
            ),
            "STAGE1_SOURCE_COMPLEMENT_NONUNIQUE_STOP",
        )
        coordinator_ref = coordinator.token_id
    case_slots = _v2_complement_case_slots(rule, frame)
    return SourceComplementPlan(
        mode=rule.mode,
        group_ref=group.group_ref,
        complement_rule_ref=rule.complement_rule_id,
        quote_delimiter_refs=tuple(delimiter_refs),
        classifier_ref=classifier_ref,
        coordinator_ref=coordinator_ref,
        case_slot_ref=",".join(case_slots),
    )


def _v2_relation_operator_for_frame(frame_ref: str) -> RelationOperator:
    return dict(_V2_RELATION_OPERATOR_BY_FRAME_REF).get(
        frame_ref,
        RelationOperator.NO_RELATION_CLAIM,
    )


def _v2_subjective_kind_for_sense(
    sense_ref: str,
) -> Tuple[Optional[SubjectiveContentKind], Optional[SubjectivePredicationKind]]:
    rows = tuple(
        (content_kind, predication_kind)
        for ref, content_kind, predication_kind
        in _V2_SUBJECTIVE_KIND_BY_SENSE_REF
        if ref == sense_ref
    )
    if not rows:
        return None, None
    return _v2_exact1(
        rows,
        "STAGE1_JAPANESE_CASE_FRAME_NONUNIQUE_STOP",
    )


def select_case_frame(intent: JapaneseCaseFrameKey) -> JapaneseCaseFrameSpec:
    """Return the sole licensed case frame for an existing typed intent."""

    validate_v2_grammar_inventory()
    if (
        type(intent) is not JapaneseCaseFrameKey
        or type(intent.sentence_job) is not SentenceJob
        or type(intent.semantic_clause_kind) is not SemanticClauseKind
        or (
            intent.subjective_content_kind is not None
            and type(intent.subjective_content_kind) is not SubjectiveContentKind
        )
        or (
            intent.subjective_predication_kind is not None
            and type(intent.subjective_predication_kind)
            is not SubjectivePredicationKind
        )
        or (
            intent.subjective_semantic_sense is not None
            and (
                type(intent.subjective_semantic_sense) is not str
                or not intent.subjective_semantic_sense
            )
        )
        or (
            intent.grounded_predicate_kind is not None
            and (
                type(intent.grounded_predicate_kind) is not str
                or not intent.grounded_predicate_kind
            )
        )
        or type(intent.required_argument_roles) is not tuple
        or not intent.required_argument_roles
        or any(
            type(role) is not ClauseArgumentRole
            for role in intent.required_argument_roles
        )
        or len(set(intent.required_argument_roles))
        != len(intent.required_argument_roles)
        or type(intent.admitted_relation_operator) is not RelationOperator
        or type(intent.polarity) is not str
        or not intent.polarity
        or type(intent.modality) is not str
        or not intent.modality
        or type(intent.time_scope) is not str
        or not intent.time_scope
        or type(intent.speaker_requirement) is not SpeakerRequirement
        or type(intent.zero_subject_eligibility) is not str
        or not intent.zero_subject_eligibility
        or type(intent.complement_requirement) is not str
        or not intent.complement_requirement
    ):
        raise Stage1CompositionError(
            "STAGE1_JAPANESE_CASE_FRAME_NONUNIQUE_STOP"
        )
    sense_rows: list[PredicateSenseSpec] = []
    for sense in V2_PREDICATE_SENSE_REGISTRY:
        if (
            sense.sentence_job != intent.sentence_job.value
            or sense.semantic_clause_kind != intent.semantic_clause_kind.value
        ):
            continue
        expected_content, expected_predication = (
            _v2_subjective_kind_for_sense(sense.sense_id)
        )
        if intent.semantic_clause_kind is SemanticClauseKind.SUBJECTIVE_PREDICATE:
            matches_kind = (
                intent.subjective_content_kind is expected_content
                and intent.subjective_predication_kind is expected_predication
                and intent.subjective_semantic_sense == sense.semantic_sense
                and intent.grounded_predicate_kind is None
            )
        elif intent.semantic_clause_kind is SemanticClauseKind.GROUNDED_PREDICATE:
            matches_kind = (
                intent.subjective_content_kind is None
                and intent.subjective_predication_kind is None
                and intent.subjective_semantic_sense is None
                and intent.grounded_predicate_kind == sense.semantic_sense
            )
        else:
            matches_kind = (
                intent.subjective_content_kind is None
                and intent.subjective_predication_kind is None
                and intent.subjective_semantic_sense is None
                and intent.grounded_predicate_kind is None
            )
        if matches_kind:
            sense_rows.append(sense)

    candidate_frames: list[JapaneseCaseFrameSpec] = []
    morphology_by_frame = {
        row.frame_ref: row for row in V2_MATRIX_MORPHOLOGY_PARADIGM_REGISTRY
    }
    for sense in sense_rows:
        for frame in V2_JAPANESE_CASE_FRAME_REGISTRY:
            morphology = morphology_by_frame.get(frame.frame_id)
            if (
                frame.sense_ref != sense.sense_id
                or frame.frame_id not in sense.frame_license_refs
                or tuple(
                    ClauseArgumentRole(slot) for slot in frame.slot_roles
                )
                != intent.required_argument_roles
                or _v2_relation_operator_for_frame(frame.frame_id)
                is not intent.admitted_relation_operator
                or morphology is None
                or morphology.polarity != intent.polarity
                or morphology.modal != intent.modality
                or morphology.aspect_time != intent.time_scope
                or frame.zero_policy != intent.zero_subject_eligibility
                or frame.complement_rule_ref != intent.complement_requirement
            ):
                continue
            if intent.semantic_clause_kind is SemanticClauseKind.SUBJECTIVE_PREDICATE:
                speaker_matches = intent.speaker_requirement in {
                    SpeakerRequirement.EMLIS_EXPLICIT_REQUIRED,
                    SpeakerRequirement.EMLIS_ZERO_ALLOWED,
                }
            else:
                speaker_matches = (
                    intent.speaker_requirement
                    is SpeakerRequirement.GROUNDED_NARRATION
                )
            if speaker_matches:
                candidate_frames.append(frame)
    return _v2_exact1(
        candidate_frames,
        "STAGE1_JAPANESE_CASE_FRAME_NONUNIQUE_STOP",
    )


def select_atomic_predicate_head(
    frame: JapaneseCaseFrameSpec,
) -> AtomicPredicateHeadSpec:
    """Select a head only after frame ownership has been fixed."""

    validate_v2_grammar_inventory()
    frame = _v2_exact1(
        tuple(
            row
            for row in V2_JAPANESE_CASE_FRAME_REGISTRY
            if row == frame
        ),
        "STAGE1_JAPANESE_CASE_FRAME_NONUNIQUE_STOP",
    )
    head = _v2_exact1(
        tuple(
            row
            for row in V2_ATOMIC_PREDICATE_HEAD_REGISTRY
            if row.frame_ref == frame.frame_id
            and row.head_id == frame.atomic_head_ref
        ),
        "STAGE1_ATOMIC_PREDICATE_HEAD_NONUNIQUE_STOP",
    )
    inflection_rows = tuple(
        row
        for row in V2_INFLECTION_CLASS_REGISTRY
        if row.inflection_class_id == head.inflection_class_ref
    )
    morphology_rows = tuple(
        row
        for row in V2_MATRIX_MORPHOLOGY_PARADIGM_REGISTRY
        if row.frame_ref == frame.frame_id
        and row.morphology_id == frame.morphology_ref
    )
    lexical_family_rows = tuple(
        row
        for row in V2_LEXICAL_FAMILY_REGISTRY
        if row.lexical_family_id == head.lexical_family_ref
        and row.atomic_parts == head.atomic_parts
    )
    if (
        len(inflection_rows) != 1
        or len(morphology_rows) != 1
        or len(lexical_family_rows) != 1
    ):
        raise Stage1CompositionError(
            "STAGE1_ATOMIC_HEAD_MORPHOLOGY_INCOMPATIBLE_STOP"
        )
    return head


def project_argument_realization_plan(
    *,
    frame: JapaneseCaseFrameSpec,
    slot_bindings: Sequence[
        Tuple[ClauseArgumentRole, str, Tuple[str, ...]]
    ],
) -> Tuple[ArgumentRealizationPlan, ...]:
    """Bind each required frame slot to one semantic and particle owner."""

    validate_v2_grammar_inventory()
    registered_frame = _v2_exact1(
        tuple(
            row
            for row in V2_JAPANESE_CASE_FRAME_REGISTRY
            if row == frame
        ),
        "STAGE1_JAPANESE_CASE_FRAME_NONUNIQUE_STOP",
    )
    expected_roles = tuple(
        ClauseArgumentRole(slot) for slot in registered_frame.slot_roles
    )
    bindings = tuple(slot_bindings)
    if any(
        type(binding) is not tuple
        or len(binding) != 3
        or type(binding[0]) is not ClauseArgumentRole
        or not binding[1]
        or type(binding[2]) is not tuple
        or not binding[2]
        or not all(binding[2])
        or len(set(binding[2])) != len(binding[2])
        for binding in bindings
    ):
        raise Stage1CompositionError(
            "STAGE1_REQUIRED_ARGUMENT_SLOT_NONUNIQUE_STOP"
        )
    bound_roles = tuple(binding[0] for binding in bindings)
    if (
        len(bound_roles) != len(set(bound_roles))
        or set(bound_roles) != set(expected_roles)
        or len(bound_roles) != len(expected_roles)
    ):
        raise Stage1CompositionError(
            "STAGE1_REQUIRED_ARGUMENT_SLOT_NONUNIQUE_STOP"
        )
    binding_by_role = {binding[0]: binding for binding in bindings}
    plans: list[ArgumentRealizationPlan] = []
    for role in expected_roles:
        _role, semantic_ref, provenance_refs = binding_by_role[role]
        particle = _v2_exact1(
            tuple(
                row
                for row in V2_CASE_PARTICLE_REGISTRY
                if row.frame_ref == registered_frame.frame_id
                and row.slot_role == role.value
            ),
            "STAGE1_CASE_PARTICLE_OWNER_NONUNIQUE_STOP",
        )
        if (
            not particle.surface_variants
            or len(particle.surface_variants)
            != len(set(particle.surface_variants))
        ):
            raise Stage1CompositionError(
                "STAGE1_CASE_PARTICLE_OWNER_NONUNIQUE_STOP"
            )
        plans.append(
            ArgumentRealizationPlan(
                plan_ref=_ref(
                    "argument-realization-plan-v2",
                    (
                        registered_frame.frame_id,
                        role.value,
                        semantic_ref,
                        particle.particle_rule_id,
                        provenance_refs,
                    ),
                ),
                frame_ref=registered_frame.frame_id,
                slot_role=role.value,
                semantic_ref=semantic_ref,
                particle_rule_ref=particle.particle_rule_id,
                provenance_refs=provenance_refs,
            )
        )
    return tuple(plans)


_V2_REFERENCE_PROOF_PREFIX = "reference-rule:"


def _v2_reference_rows_from_state(
    state: DiscourseReferenceStateRow,
) -> Tuple[ReferenceZeroTopicRule, ...]:
    if type(state) is not DiscourseReferenceStateRow or not state.state_ref:
        raise Stage1CompositionError(
            "STAGE1_REFERENCE_STATE_NONUNIQUE_STOP"
        )
    rule_refs = tuple(
        proof_ref.removeprefix(_V2_REFERENCE_PROOF_PREFIX)
        for proof_ref in state.establishment_proof_refs
        if proof_ref.startswith(_V2_REFERENCE_PROOF_PREFIX)
    )
    if not rule_refs or len(rule_refs) != len(set(rule_refs)):
        raise Stage1CompositionError(
            "STAGE1_REFERENCE_STATE_NONUNIQUE_STOP"
        )
    rows = tuple(
        row
        for rule_ref in rule_refs
        for row in V2_REFERENCE_ZERO_TOPIC_REGISTRY
        if row.reference_rule_id == rule_ref
    )
    if len(rows) != len(rule_refs):
        raise Stage1CompositionError(
            "STAGE1_REFERENCE_STATE_NONUNIQUE_STOP"
        )
    return rows


def _v2_reference_surface_for_frame(
    frame: JapaneseCaseFrameSpec,
    source_cardinality: SourceLeafCardinality,
) -> Optional[V2ReferenceSurfaceSpec]:
    rule_ref = (
        "R03"
        if source_cardinality is SourceLeafCardinality.EXACT1
        else "R04"
        if source_cardinality is SourceLeafCardinality.ORDERED_EXACT2
        else ""
    )
    matches = tuple(
        row
        for row in V2_REFERENCE_SURFACE_REGISTRY_EXACT2
        if row.reference_rule_ref == rule_ref
        and row.source_cardinality is source_cardinality
        and frame.frame_id in row.licensed_frame_refs
    )
    if len(matches) > 1:
        raise Stage1CompositionError(
            "GRAMMAR_INVENTORY_REFERENCE_SURFACE_EXACT2_STOP"
        )
    return matches[0] if matches else None


def _v2_reference_rows_from_bundle(
    bundle: V2ClauseReferenceStateBundle,
) -> Tuple[ReferenceZeroTopicRule, ...]:
    if type(bundle) is not V2ClauseReferenceStateBundle:
        raise Stage1CompositionError(
            "STAGE1_REFERENCE_STATE_NONUNIQUE_STOP"
        )
    subject_rows = (
        ()
        if bundle.subject_state is None
        else _v2_reference_rows_from_state(bundle.subject_state)
    )
    object_rows = _v2_reference_rows_from_state(bundle.object_state)
    return (*subject_rows, *object_rows)


def project_reference_state(
    *,
    state_ref: str,
    decision_kind: ReferenceDecisionKind,
    referent_refs: Tuple[str, ...],
    antecedent_refs: Tuple[str, ...] = (),
    competitor_refs: Tuple[str, ...] = (),
    focus_ref: Optional[str] = None,
    speaker_ref: Optional[str] = None,
    establishment_proof_refs: Tuple[str, ...] = (),
    previous_ordered_pair_refs: Tuple[str, ...] = (),
    same_speaker_chain: bool = False,
    first_or_restart: bool = False,
    after_counterposition: bool = False,
    introduced_topic: bool = False,
    admitted_contrast: bool = False,
    reference_repair: bool = False,
    distance_is_local: bool = True,
    full_expression_frame_compatible: bool = True,
) -> DiscourseReferenceStateRow:
    """Project registered mention, speaker, zero, and topic decisions."""

    validate_v2_grammar_inventory()
    exact_tuples = (
        referent_refs,
        antecedent_refs,
        competitor_refs,
        establishment_proof_refs,
        previous_ordered_pair_refs,
    )
    bool_values = (
        same_speaker_chain,
        first_or_restart,
        after_counterposition,
        introduced_topic,
        admitted_contrast,
        reference_repair,
        distance_is_local,
        full_expression_frame_compatible,
    )
    if (
        not state_ref
        or type(decision_kind) is not ReferenceDecisionKind
        or not referent_refs
        or any(
            type(values) is not tuple
            or any(type(value) is not str or not value for value in values)
            or len(values) != len(set(values))
            for values in exact_tuples
        )
        or any(type(value) is not bool for value in bool_values)
        or (focus_ref is not None and not focus_ref)
        or (speaker_ref is not None and not speaker_ref)
        or introduced_topic and admitted_contrast
        or any(
            proof.startswith(_V2_REFERENCE_PROOF_PREFIX)
            for proof in establishment_proof_refs
        )
    ):
        raise Stage1CompositionError(
            "STAGE1_REFERENCE_STATE_NONUNIQUE_STOP"
        )

    selected_rule_refs: list[str] = []
    if decision_kind is ReferenceDecisionKind.REQUIRED_RELATION_ENDPOINT:
        if (
            len(referent_refs) != 2
            or reference_repair
            or introduced_topic
            or admitted_contrast
            or same_speaker_chain
            or first_or_restart
            or after_counterposition
        ):
            raise Stage1CompositionError(
                "STAGE1_REFERENCE_STATE_NONUNIQUE_STOP"
            )
        selected_rule_refs.append("R11")
    elif decision_kind is ReferenceDecisionKind.EMLIS_SUBJECT:
        if speaker_ref != CMEE_STAGE1_EMLIS_OWNER_REF:
            raise Stage1CompositionError(
                "STAGE1_REFERENCE_STATE_NONUNIQUE_STOP"
            )
        speaker_condition_count = sum(
            (same_speaker_chain, first_or_restart, after_counterposition)
        )
        if speaker_condition_count != 1 or reference_repair:
            raise Stage1CompositionError(
                "STAGE1_REFERENCE_STATE_NONUNIQUE_STOP"
            )
        selected_rule_refs.append(
            "R07" if after_counterposition else
            "R05" if first_or_restart else
            "R06"
        )
        selected_rule_refs.append(
            "R08" if introduced_topic else
            "R09" if admitted_contrast else
            "R10"
        )
    else:
        if same_speaker_chain or first_or_restart or after_counterposition:
            raise Stage1CompositionError(
                "STAGE1_REFERENCE_STATE_NONUNIQUE_STOP"
            )
        if reference_repair:
            if not full_expression_frame_compatible:
                raise Stage1CompositionError(
                    "STAGE1_REFERENCE_REPAIR_UNAVAILABLE_STOP"
                )
            selected_rule_refs.append("R12")
        elif not antecedent_refs:
            if not full_expression_frame_compatible:
                raise Stage1CompositionError(
                    "STAGE1_REFERENCE_REPAIR_UNAVAILABLE_STOP"
                )
            selected_rule_refs.append("R01")
        elif competitor_refs:
            if not full_expression_frame_compatible:
                raise Stage1CompositionError(
                    "STAGE1_REFERENCE_REPAIR_UNAVAILABLE_STOP"
                )
            selected_rule_refs.append("R02")
        elif (
            len(referent_refs) == 1
            and antecedent_refs == referent_refs
            and focus_ref == referent_refs[0]
            and distance_is_local
        ):
            selected_rule_refs.append("R03")
        elif (
            len(referent_refs) == 2
            and antecedent_refs == referent_refs
            and previous_ordered_pair_refs == referent_refs
            and distance_is_local
        ):
            selected_rule_refs.append("R04")
        else:
            if not full_expression_frame_compatible:
                raise Stage1CompositionError(
                    "STAGE1_REFERENCE_REPAIR_UNAVAILABLE_STOP"
                )
            selected_rule_refs.append("R02")
        selected_rule_refs.append(
            "R08" if introduced_topic else
            "R09" if admitted_contrast else
            "R10"
        )

    registered_ids = {
        row.reference_rule_id for row in V2_REFERENCE_ZERO_TOPIC_REGISTRY
    }
    if (
        not selected_rule_refs
        or len(selected_rule_refs) != len(set(selected_rule_refs))
        or any(rule_ref not in registered_ids for rule_ref in selected_rule_refs)
    ):
        raise Stage1CompositionError(
            "STAGE1_REFERENCE_STATE_NONUNIQUE_STOP"
        )
    state = DiscourseReferenceStateRow(
        state_ref=state_ref,
        antecedent_refs=antecedent_refs,
        competitor_refs=competitor_refs,
        focus_ref=focus_ref,
        speaker_ref=speaker_ref,
        establishment_proof_refs=(
            *establishment_proof_refs,
            *tuple(
                f"{_V2_REFERENCE_PROOF_PREFIX}{rule_ref}"
                for rule_ref in selected_rule_refs
            ),
        ),
    )
    _v2_reference_rows_from_state(state)
    return state


def project_clause_link_plan(
    *,
    link_plan_ref: str,
    admitted_relation_ref: str,
    admitted_relation: RelationOperator,
    placement: ClauseLinkPlacement,
    frame: Optional[JapaneseCaseFrameSpec] = None,
    relation_already_owned: bool = False,
    independent_topic: bool = False,
    is_first_sentence: bool = False,
    previous_token_owner_ref: Optional[str] = None,
) -> ClauseLinkPlan:
    """Select the sole registered relation-display owner before rendering."""

    validate_v2_grammar_inventory()
    if (
        not link_plan_ref
        or not admitted_relation_ref
        or type(admitted_relation) is not RelationOperator
        or type(placement) is not ClauseLinkPlacement
        or type(relation_already_owned) is not bool
        or type(independent_topic) is not bool
        or type(is_first_sentence) is not bool
        or (
            previous_token_owner_ref is not None
            and not previous_token_owner_ref
        )
    ):
        raise Stage1CompositionError("STAGE1_CLAUSE_LINK_NONUNIQUE_STOP")
    registered_frame: Optional[JapaneseCaseFrameSpec] = None
    if frame is not None:
        registered_frame = _v2_exact1(
            tuple(
                row
                for row in V2_JAPANESE_CASE_FRAME_REGISTRY
                if row == frame
            ),
            "STAGE1_CLAUSE_LINK_NONUNIQUE_STOP",
        )
    relation_kind = admitted_relation.value
    candidates: Tuple[ClauseLinkRule, ...]
    if placement is ClauseLinkPlacement.FRAME_INTERNAL:
        if (
            registered_frame is None
            or relation_already_owned
            or independent_topic
            or _v2_relation_operator_for_frame(registered_frame.frame_id)
            is not admitted_relation
            or admitted_relation is RelationOperator.NO_RELATION_CLAIM
        ):
            raise Stage1CompositionError("STAGE1_CLAUSE_LINK_NONUNIQUE_STOP")
        candidates = tuple(
            row
            for row in V2_CLAUSE_LINK_REGISTRY
            if row.relation_kind == relation_kind
            and row.placement == placement.value
            and row.token_ref == registered_frame.frame_id
            and row.internal_relation_policy == "ZERO_EXTERNAL"
        )
    elif placement is ClauseLinkPlacement.SENTENCE_INITIAL:
        if (
            is_first_sentence
            or relation_already_owned
            or independent_topic
            or admitted_relation
            not in {
                RelationOperator.TEMPORALLY_PRECEDES,
                RelationOperator.ACTION_PRECEDES_CHANGE,
                RelationOperator.SOURCE_EXPLICIT_CAUSE,
            }
            or (
                registered_frame is not None
                and _v2_relation_operator_for_frame(registered_frame.frame_id)
                is not RelationOperator.NO_RELATION_CLAIM
            )
        ):
            raise Stage1CompositionError("STAGE1_CLAUSE_LINK_NONUNIQUE_STOP")
        candidates = tuple(
            row
            for row in V2_CLAUSE_LINK_REGISTRY
            if row.relation_kind == relation_kind
            and row.placement == placement.value
            and row.internal_relation_policy == "INTERNAL_ZERO"
        )
    elif placement is ClauseLinkPlacement.SENTENCE_INITIAL_ADDITIVE:
        if (
            is_first_sentence
            or relation_already_owned
            or not independent_topic
            or admitted_relation is not RelationOperator.NO_RELATION_CLAIM
        ):
            raise Stage1CompositionError("STAGE1_CLAUSE_LINK_NONUNIQUE_STOP")
        candidates = tuple(
            row
            for row in V2_CLAUSE_LINK_REGISTRY
            if row.relation_kind == relation_kind
            and row.placement == placement.value
            and row.internal_relation_policy == "INDEPENDENT_TOPIC_ONLY"
        )
    else:
        if independent_topic or not (
            relation_already_owned
            or admitted_relation is RelationOperator.NO_RELATION_CLAIM
        ):
            raise Stage1CompositionError("STAGE1_CLAUSE_LINK_NONUNIQUE_STOP")
        candidates = tuple(
            row
            for row in V2_CLAUSE_LINK_REGISTRY
            if row.link_rule_id == "L10"
            and row.placement == placement.value
            and row.internal_relation_policy == "RELATION_ALREADY_OWNED"
        )
    selected = _v2_exact1(
        candidates,
        "STAGE1_CLAUSE_LINK_NONUNIQUE_STOP",
    )
    if (
        previous_token_owner_ref is not None
        and selected.token_ref != "registered:empty"
        and selected.token_ref == previous_token_owner_ref
    ):
        raise Stage1CompositionError("STAGE1_CLAUSE_LINK_REPEAT_STOP")
    return ClauseLinkPlan(
        link_plan_ref=link_plan_ref,
        admitted_relation_ref=admitted_relation_ref,
        placement=ClauseLinkPlacement(selected.placement),
        token_owner_ref=selected.token_ref,
    )


def project_predicate_morphology_plan(
    *,
    frame: JapaneseCaseFrameSpec,
    head: AtomicPredicateHeadSpec,
) -> PredicateMorphologyPlan:
    """Close head, inflection class, finite chain, and terminal at exact1."""

    validate_v2_grammar_inventory()
    selected_frame = _v2_exact1(
        tuple(
            row
            for row in V2_JAPANESE_CASE_FRAME_REGISTRY
            if row == frame
        ),
        "STAGE1_MATRIX_MORPHOLOGY_NONUNIQUE_STOP",
    )
    selected_head = _v2_exact1(
        tuple(
            row
            for row in V2_ATOMIC_PREDICATE_HEAD_REGISTRY
            if row == head
            and row.frame_ref == selected_frame.frame_id
            and row.head_id == selected_frame.atomic_head_ref
        ),
        "STAGE1_MATRIX_MORPHOLOGY_NONUNIQUE_STOP",
    )
    _v2_exact1(
        tuple(
            row
            for row in V2_INFLECTION_CLASS_REGISTRY
            if row.inflection_class_id == selected_head.inflection_class_ref
        ),
        "STAGE1_MATRIX_MORPHOLOGY_NONUNIQUE_STOP",
    )
    morphology = _v2_exact1(
        tuple(
            row
            for row in V2_MATRIX_MORPHOLOGY_PARADIGM_REGISTRY
            if row.frame_ref == selected_frame.frame_id
            and row.morphology_id == selected_frame.morphology_ref
        ),
        "STAGE1_MATRIX_MORPHOLOGY_NONUNIQUE_STOP",
    )
    if morphology.terminal_class != "PERIOD":
        raise Stage1CompositionError(
            "STAGE1_MATRIX_MORPHOLOGY_NONUNIQUE_STOP"
        )
    return PredicateMorphologyPlan(
        plan_ref=_ref(
            "predicate-morphology-plan-v2",
            (
                selected_frame.frame_id,
                selected_head.head_id,
                selected_head.inflection_class_ref,
                morphology,
            ),
        ),
        head_ref=selected_head.head_id,
        aspect_time=morphology.aspect_time,
        polarity=morphology.polarity,
        modal=morphology.modal,
        politeness=morphology.politeness,
        terminal_order=(
            morphology.inflection_recipe,
            morphology.terminal_class,
        ),
    )


def _v2_source_complement_plan_ref(plan: SourceComplementPlan) -> str:
    return _ref(
        "source-complement-plan-v2",
        (
            plan.mode,
            plan.group_ref,
            plan.complement_rule_ref,
            plan.quote_delimiter_refs,
            plan.classifier_ref,
            plan.coordinator_ref,
            plan.case_slot_ref,
        ),
    )


def _v2_validate_argument_plans(
    frame: JapaneseCaseFrameSpec,
    argument_plans: Sequence[ArgumentRealizationPlan],
) -> Tuple[ArgumentRealizationPlan, ...]:
    plans = tuple(argument_plans)
    expected_roles = frame.slot_roles
    if (
        not plans
        or any(type(plan) is not ArgumentRealizationPlan for plan in plans)
        or tuple(plan.slot_role for plan in plans) != expected_roles
        or len({plan.slot_role for plan in plans}) != len(plans)
    ):
        raise Stage1CompositionError(
            "STAGE1_REQUIRED_ARGUMENT_SLOT_NONUNIQUE_STOP"
        )
    for plan in plans:
        particle = _v2_exact1(
            tuple(
                row
                for row in V2_CASE_PARTICLE_REGISTRY
                if row.frame_ref == frame.frame_id
                and row.slot_role == plan.slot_role
                and row.particle_rule_id == plan.particle_rule_ref
            ),
            "STAGE1_CASE_PARTICLE_OWNER_NONUNIQUE_STOP",
        )
        expected_ref = _ref(
            "argument-realization-plan-v2",
            (
                frame.frame_id,
                plan.slot_role,
                plan.semantic_ref,
                particle.particle_rule_id,
                plan.provenance_refs,
            ),
        )
        if (
            plan.frame_ref != frame.frame_id
            or not plan.semantic_ref
            or not plan.provenance_refs
            or expected_ref != plan.plan_ref
        ):
            raise Stage1CompositionError(
                "STAGE1_REQUIRED_ARGUMENT_SLOT_NONUNIQUE_STOP"
            )
    return plans


def _v2_validate_source_complement_plan(
    frame: JapaneseCaseFrameSpec,
    plan: SourceComplementPlan,
) -> None:
    if type(plan) is not SourceComplementPlan or not plan.group_ref:
        raise Stage1CompositionError(
            "STAGE1_SOURCE_COMPLEMENT_NONUNIQUE_STOP"
        )
    rule = _v2_exact1(
        tuple(
            row
            for row in V2_COMPLEMENT_RULE_REGISTRY
            if row.complement_rule_id == frame.complement_rule_ref
            and row.complement_rule_id == plan.complement_rule_ref
            and row.mode is plan.mode
        ),
        "STAGE1_SOURCE_COMPLEMENT_NONUNIQUE_STOP",
    )
    license_row = _v2_exact1(
        tuple(
            row
            for row in V2_SENSE_COMPLEMENT_LICENSE_REGISTRY
            if row.frame_ref == frame.frame_id
            and row.sense_ref == frame.sense_ref
            and row.complement_rule_ref == rule.complement_rule_id
        ),
        "STAGE1_SOURCE_COMPLEMENT_NONUNIQUE_STOP",
    )
    expected_slots = ",".join(_v2_complement_case_slots(rule, frame))
    source_cardinality = (
        1 if rule.cardinality is SourceLeafCardinality.EXACT1 else 2
    )
    allowed_delimiter_counts = (
        {source_cardinality}
        if "OUTER_QUOTES" in rule.structural_asset_refs
        else {0, source_cardinality}
    )
    if (
        plan.case_slot_ref != expected_slots
        or len(plan.quote_delimiter_refs) not in allowed_delimiter_counts
        or plan.classifier_ref != license_row.classifier_ref
        or ("CLASSIFIER_EXACT1" in rule.structural_asset_refs)
        != (plan.classifier_ref is not None)
        or ("SF03" in rule.structural_asset_refs)
        != (plan.coordinator_ref == "SF03")
    ):
        raise Stage1CompositionError(
            "STAGE1_SOURCE_COMPLEMENT_NONUNIQUE_STOP"
        )


def _v2_validate_reference_state_for_frame(
    frame: JapaneseCaseFrameSpec,
    state: DiscourseReferenceStateRow,
) -> Tuple[ReferenceZeroTopicRule, ...]:
    rows = _v2_reference_rows_from_state(state)
    rule_ids = {row.reference_rule_id for row in rows}
    speaker_rules = rule_ids & {"R05", "R06", "R07"}
    topic_rules = rule_ids & {"R08", "R09", "R10"}
    mention_rules = rule_ids & {"R01", "R02", "R03", "R04", "R11", "R12"}
    subjective = frame.zero_policy == "EMLIS_ZERO_CONDITIONAL"
    relation = _v2_relation_operator_for_frame(frame.frame_id)
    if subjective:
        valid = (
            len(speaker_rules) == 1
            and len(topic_rules) == 1
            and not mention_rules
            and state.speaker_ref == CMEE_STAGE1_EMLIS_OWNER_REF
        )
    elif relation is not RelationOperator.NO_RELATION_CLAIM:
        valid = (
            rule_ids == {"R11"}
            and len(state.antecedent_refs) <= 2
            and state.speaker_ref is None
        )
    else:
        valid = (
            len(mention_rules) == 1
            and len(topic_rules) == 1
            and not speaker_rules
            and state.speaker_ref is None
        )
    if not valid:
        raise Stage1CompositionError(
            "STAGE1_REFERENCE_STATE_NONUNIQUE_STOP"
        )
    return rows


def _v2_validate_reference_bundle_for_frame(
    frame: JapaneseCaseFrameSpec,
    bundle: V2ClauseReferenceStateBundle,
    argument_plans: Tuple[ArgumentRealizationPlan, ...],
) -> Tuple[ReferenceZeroTopicRule, ...]:
    """Validate independent subject/object state against one typed frame."""

    if (
        type(bundle) is not V2ClauseReferenceStateBundle
        or not bundle.state_ref
        or type(bundle.response_object_expression)
        is not ResponseObjectExpression
        or not bundle.response_object_expression.basis_semantic_refs
        or bundle.state_ref
        != _ref(
            "reference-state-bundle-v2",
            (
                bundle.subject_state,
                bundle.object_state,
                bundle.response_object_expression,
            ),
        )
    ):
        raise Stage1CompositionError(
            "STAGE1_REFERENCE_STATE_NONUNIQUE_STOP"
        )
    subjective = frame.zero_policy == "EMLIS_ZERO_CONDITIONAL"
    relation = _v2_relation_operator_for_frame(frame.frame_id)
    argument_source_refs = tuple(
        plan.semantic_ref
        for plan in argument_plans
        if not (subjective and plan.slot_role == "SUBJECT")
    )
    expression = bundle.response_object_expression
    expected_source_refs = (
        expression.basis_semantic_refs
        if frame.complement_rule_ref == "C08"
        and len(expression.basis_semantic_refs) == 2
        and argument_source_refs == (expression.basis_semantic_refs[0],)
        else argument_source_refs
    )
    if expression.basis_semantic_refs != expected_source_refs:
        raise Stage1CompositionError(
            "STAGE1_SOURCE_PAIR_CARDINALITY_STOP"
        )

    subject_rows: Tuple[ReferenceZeroTopicRule, ...] = ()
    if subjective:
        if bundle.subject_state is None:
            raise Stage1CompositionError(
                "STAGE1_REFERENCE_STATE_NONUNIQUE_STOP"
            )
        subject_rows = _v2_validate_reference_state_for_frame(
            frame, bundle.subject_state
        )
    elif bundle.subject_state is not None:
        raise Stage1CompositionError(
            "STAGE1_REFERENCE_STATE_NONUNIQUE_STOP"
        )

    object_rows = _v2_reference_rows_from_state(bundle.object_state)
    object_rule_ids = {row.reference_rule_id for row in object_rows}
    object_mention_rules = object_rule_ids & {
        "R01",
        "R02",
        "R03",
        "R04",
        "R11",
        "R12",
    }
    object_topic_rules = object_rule_ids & {"R08", "R09", "R10"}
    if relation is not RelationOperator.NO_RELATION_CLAIM:
        object_valid = (
            object_rule_ids == {"R11"}
            and expression.expression_mode
            is ResponseObjectExpressionMode.COMPOSITE
            and expression.relation_refs
        )
    else:
        object_valid = (
            len(object_mention_rules) == 1
            and len(object_topic_rules) == 1
            and not object_rule_ids.intersection({"R05", "R06", "R07"})
            and bundle.object_state.speaker_ref is None
        )
        if "R03" in object_rule_ids:
            object_valid = bool(
                object_valid
                and len(expected_source_refs) == 1
                and bundle.object_state.antecedent_refs == expected_source_refs
                and bundle.object_state.focus_ref == expected_source_refs[0]
                and expression.expression_mode
                is ResponseObjectExpressionMode.ANAPHORIC
                and _v2_reference_surface_for_frame(
                    frame, SourceLeafCardinality.EXACT1
                )
                is not None
            )
        elif "R04" in object_rule_ids:
            object_valid = bool(
                object_valid
                and len(expected_source_refs) == 2
                and bundle.object_state.antecedent_refs == expected_source_refs
                and expression.expression_mode
                is ResponseObjectExpressionMode.ANAPHORIC
                and _v2_reference_surface_for_frame(
                    frame, SourceLeafCardinality.ORDERED_EXACT2
                )
                is not None
            )
        elif "R12" in object_rule_ids:
            object_valid = bool(
                object_valid
                and bundle.object_state.antecedent_refs == expected_source_refs
                and expression.expression_mode
                is not ResponseObjectExpressionMode.ANAPHORIC
            )
        elif "R01" in object_rule_ids:
            object_valid = bool(
                object_valid and not bundle.object_state.antecedent_refs
            )
    if not object_valid:
        raise Stage1CompositionError(
            "STAGE1_REFERENCE_STATE_NONUNIQUE_STOP"
        )
    return (*subject_rows, *object_rows)


def _v2_validate_link_plan_for_frame(
    frame: JapaneseCaseFrameSpec,
    plan: ClauseLinkPlan,
) -> ClauseLinkRule:
    if (
        type(plan) is not ClauseLinkPlan
        or not plan.link_plan_ref
        or not plan.admitted_relation_ref
    ):
        raise Stage1CompositionError("STAGE1_CLAUSE_LINK_NONUNIQUE_STOP")
    rows = tuple(
        row
        for row in V2_CLAUSE_LINK_REGISTRY
        if row.placement == plan.placement
        and row.token_ref == plan.token_owner_ref
    )
    selected = _v2_exact1(rows, "STAGE1_CLAUSE_LINK_NONUNIQUE_STOP")
    frame_relation = _v2_relation_operator_for_frame(frame.frame_id)
    if (
        selected.placement == "FRAME_INTERNAL"
        and (
            selected.token_ref != frame.frame_id
            or selected.relation_kind != frame_relation.value
        )
    ):
        raise Stage1CompositionError("STAGE1_CLAUSE_LINK_NONUNIQUE_STOP")
    if (
        frame_relation is not RelationOperator.NO_RELATION_CLAIM
        and selected.placement not in {"FRAME_INTERNAL", "ZERO"}
    ):
        raise Stage1CompositionError("STAGE1_CLAUSE_LINK_DOUBLE_MARK_STOP")
    return selected


def _v2_validate_morphology_plan(
    frame: JapaneseCaseFrameSpec,
    head: AtomicPredicateHeadSpec,
    plan: PredicateMorphologyPlan,
) -> MatrixMorphologyParadigmSpec:
    expected = project_predicate_morphology_plan(frame=frame, head=head)
    if type(plan) is not PredicateMorphologyPlan or plan != expected:
        raise Stage1CompositionError(
            "STAGE1_MATRIX_MORPHOLOGY_NONUNIQUE_STOP"
        )
    return _v2_exact1(
        tuple(
            row
            for row in V2_MATRIX_MORPHOLOGY_PARADIGM_REGISTRY
            if row.frame_ref == frame.frame_id
            and row.morphology_id == frame.morphology_ref
        ),
        "STAGE1_MATRIX_MORPHOLOGY_NONUNIQUE_STOP",
    )


def build_japanese_clause_ir(
    *,
    frame: JapaneseCaseFrameSpec,
    head: AtomicPredicateHeadSpec,
    argument_plans: Sequence[ArgumentRealizationPlan],
    source_complement_plan: SourceComplementPlan,
    reference_state: V2ClauseReferenceStateBundle,
    link_plan: ClauseLinkPlan,
    morphology_plan: PredicateMorphologyPlan,
) -> JapaneseClauseIR:
    """Seal typed clause owners and their semantic digest before text exists."""

    validate_v2_grammar_inventory()
    registered_frame = _v2_exact1(
        tuple(
            row for row in V2_JAPANESE_CASE_FRAME_REGISTRY if row == frame
        ),
        "STAGE1_JAPANESE_CASE_FRAME_NONUNIQUE_STOP",
    )
    registered_head = select_atomic_predicate_head(registered_frame)
    if head != registered_head:
        raise Stage1CompositionError(
            "STAGE1_ATOMIC_PREDICATE_HEAD_NONUNIQUE_STOP"
        )
    plans = _v2_validate_argument_plans(registered_frame, argument_plans)
    _v2_validate_source_complement_plan(
        registered_frame,
        source_complement_plan,
    )
    _v2_validate_reference_bundle_for_frame(
        registered_frame, reference_state, plans
    )
    _v2_validate_link_plan_for_frame(registered_frame, link_plan)
    _v2_validate_morphology_plan(
        registered_frame,
        registered_head,
        morphology_plan,
    )
    semantic_material = (
        registered_frame.frame_id,
        registered_head.head_id,
        tuple(
            (
                plan.slot_role,
                plan.semantic_ref,
                plan.provenance_refs,
                plan.particle_rule_ref,
            )
            for plan in plans
        ),
        _v2_source_complement_plan_ref(source_complement_plan),
        reference_state,
        link_plan,
        morphology_plan,
    )
    semantic_digest = hashlib.sha256(
        stage1_canonical_json_bytes(semantic_material)
    ).hexdigest()
    return JapaneseClauseIR(
        clause_ir_ref=_ref("japanese-clause-ir-v2", semantic_material),
        argument_plans=plans,
        source_complement_plan_ref=_v2_source_complement_plan_ref(
            source_complement_plan
        ),
        reference_state_ref=reference_state.state_ref,
        link_plan_ref=link_plan.link_plan_ref,
        morphology_plan_ref=morphology_plan.plan_ref,
        semantic_digest=semantic_digest,
    )


_build_japanese_clause_ir_for_validation = build_japanese_clause_ir


def _v2_atomic_head_lemma(head: AtomicPredicateHeadSpec) -> str:
    parts = tuple(
        part.removeprefix("LEXICALIZED_") for part in head.atomic_parts
    )
    if not parts or any(not part for part in parts):
        raise Stage1CompositionError(
            "STAGE1_MATRIX_MORPHOLOGY_NONUNIQUE_STOP"
        )
    return "".join(parts)


def _v2_finite_predicate_surface(
    head: AtomicPredicateHeadSpec,
    morphology: MatrixMorphologyParadigmSpec,
) -> str:
    lemma = _v2_atomic_head_lemma(head)
    inflection_class = _v2_exact1(
        tuple(
            row
            for row in V2_INFLECTION_CLASS_REGISTRY
            if row.inflection_class_id == head.inflection_class_ref
        ),
        "STAGE1_MATRIX_MORPHOLOGY_NONUNIQUE_STOP",
    ).inflection_class
    recipe = morphology.inflection_recipe
    surface: Optional[str] = None
    if inflection_class == "ICHIDAN_RU" and lemma.endswith("る"):
        stem = lemma[:-1]
        suffix_by_recipe = {
            "STEM_MASU": "ます",
            "STEM_TE_IRU_MASU": "ています",
            "STEM_TAI_DESU": "たいです",
            "STEM_TAKU_ARIMASEN": "たくありません",
        }
        suffix = suffix_by_recipe.get(recipe)
        surface = None if suffix is None else stem + suffix
    elif inflection_class == "GODAN_KU" and lemma.endswith("く"):
        if recipe == "ONBIN_ITE_IRU_MASU":
            surface = lemma[:-1] + "いています"
    elif inflection_class == "GODAN_RU" and lemma.endswith("る"):
        suffix_by_recipe = {
            "ONBIN_TE_IRU_MASU": "っています",
            "STEM_MASU": "ります",
            "STEM_TAI_DESU": "りたいです",
        }
        suffix = suffix_by_recipe.get(recipe)
        surface = None if suffix is None else lemma[:-1] + suffix
    elif inflection_class == "GODAN_BU" and lemma.endswith("ぶ"):
        if recipe == "ONBIN_DE_IRU_MASU":
            surface = lemma[:-1] + "んでいます"
    elif inflection_class == "GODAN_U" and lemma.endswith("う"):
        if recipe == "ONBIN_TE_IRU_MASU":
            surface = lemma[:-1] + "っています"
    elif inflection_class == "SAHEN_SURU" and lemma.endswith("する"):
        suffix_by_recipe = {
            "SAHEN_SHI_TAI_DESU": "したいです",
            "SAHEN_SHI_TAKU_ARIMASEN": "したくありません",
        }
        suffix = suffix_by_recipe.get(recipe)
        surface = None if suffix is None else lemma[:-2] + suffix
    if not surface or any(mark in surface for mark in ("。", "！", "？")):
        raise Stage1CompositionError(
            "STAGE1_MATRIX_MORPHOLOGY_NONUNIQUE_STOP"
        )
    return surface


def _v2_surface_derivation(
    kind: SurfaceDerivationKind,
    *,
    owner_ref: Optional[str] = None,
    source_leaf: Optional[SourceLeafToken] = None,
    response_object_expression: Optional[ResponseObjectExpression] = None,
    qualifier_refs: Tuple[str, ...] = (),
) -> SurfaceDerivation:
    rule_suffix = kind.value.lower().replace("_", "-")
    common = {
        "source_or_claim_refs": (),
        "emlis_owner_ref": None,
        "relation_or_clause_plan_refs": (),
        "qualifier_refs": (),
        "response_object_expression_ref": None,
        "antecedent_unit_ref": None,
        "participant_role_ref": None,
        "evidence_refs": (),
        "rule_ref": f"rule:{rule_suffix}@cocolon.cmee.surface.v2",
        "input_scalar_ranges": (),
    }
    if kind is SurfaceDerivationKind.LITERAL_SUBSPAN:
        if source_leaf is None:
            raise Stage1CompositionError("STAGE1_DERIVATION_SEAL_STOP")
        try:
            payload_text = source_leaf.payload_utf8.decode("utf-8", "strict")
        except UnicodeDecodeError:
            raise Stage1CompositionError(
                "STAGE1_SOURCE_LEAF_UTF8_MISMATCH_STOP"
            ) from None
        input_ranges = source_leaf.derivation.input_scalar_ranges
        if (
            not payload_text
            or type(input_ranges) is not tuple
            or len(input_ranges) != 1
            or type(input_ranges[0]) is not tuple
            or len(input_ranges[0]) != 2
            or any(type(value) is not int for value in input_ranges[0])
            or input_ranges[0][0] < 0
            or input_ranges[0][1] <= input_ranges[0][0]
            or input_ranges[0][1] - input_ranges[0][0] != len(payload_text)
        ):
            raise Stage1CompositionError("STAGE1_DERIVATION_SEAL_STOP")
        common.update(
            source_or_claim_refs=(source_leaf.semantic_ref,),
            evidence_refs=(source_leaf.evidence_ref,),
            input_scalar_ranges=input_ranges,
        )
    elif kind is SurfaceDerivationKind.REGISTERED_EMLIS_LEXEME:
        if owner_ref != CMEE_STAGE1_EMLIS_OWNER_REF:
            raise Stage1CompositionError("STAGE1_DERIVATION_SEAL_STOP")
        common.update(emlis_owner_ref=owner_ref)
    elif kind is SurfaceDerivationKind.PROJECTED_FUNCTIONAL_ASSET:
        if (
            not owner_ref
            or len(qualifier_refs) != len(set(qualifier_refs))
            or any(not ref for ref in qualifier_refs)
        ):
            raise Stage1CompositionError("STAGE1_DERIVATION_SEAL_STOP")
        common.update(
            relation_or_clause_plan_refs=(
                () if qualifier_refs else (owner_ref,)
            ),
            qualifier_refs=qualifier_refs,
        )
    elif kind is SurfaceDerivationKind.PROJECTED_RESPONSE_OBJECT:
        expression = response_object_expression
        if (
            type(expression) is not ResponseObjectExpression
            or expression.expression_mode
            is not ResponseObjectExpressionMode.ANAPHORIC
            or not expression.basis_semantic_refs
            or expression.antecedent_unit_ref is None
            or len(expression.relation_refs) > 1
        ):
            raise Stage1CompositionError("STAGE1_DERIVATION_SEAL_STOP")
        common.update(
            source_or_claim_refs=expression.basis_semantic_refs,
            relation_or_clause_plan_refs=expression.relation_refs,
            response_object_expression_ref=(
                expression.response_object_expression_ref
            ),
            antecedent_unit_ref=expression.antecedent_unit_ref,
            rule_ref=(
                "rule:projected-response-object-anaphoric"
                "@cocolon.cmee.surface.v2"
            ),
        )
    elif kind is not SurfaceDerivationKind.REGISTERED_STRUCTURAL_ASSET:
        raise Stage1CompositionError("STAGE1_DERIVATION_SEAL_STOP")
    return SurfaceDerivation(derivation_kind=kind, **common)


def _v2_quote_delimiters(delimiter_ref: str) -> Tuple[str, str]:
    delimiter = _v2_exact1(
        tuple(
            row
            for row in V2_SOURCE_QUOTE_DELIMITER_REGISTRY
            if row.delimiter_rule_id == delimiter_ref
        ),
        "STAGE1_SOURCE_COMPLEMENT_NONUNIQUE_STOP",
    )
    if delimiter.outer_delimiter_kind == "KAGI_OUTER":
        return "「", "」"
    if delimiter.outer_delimiter_kind == "NIJUKAGI_OUTER":
        return "『", "』"
    raise Stage1CompositionError("SOURCE_OUTER_DELIMITER_UNAVAILABLE_STOP")


def _v2_clause_argument_role(
    frame: JapaneseCaseFrameSpec,
    slot_role: str,
) -> ArgumentRole:
    if slot_role == "SUBJECT":
        return (
            ArgumentRole.EXPERIENCER
            if frame.zero_policy == "EMLIS_ZERO_CONDITIONAL"
            else ArgumentRole.PRIMARY
        )
    return {
        "PRIMARY_OBJECT": ArgumentRole.PRIMARY,
        "SECONDARY_OBJECT": ArgumentRole.RIGHT,
        "LEFT_ENDPOINT": ArgumentRole.LEFT,
        "RIGHT_ENDPOINT": ArgumentRole.RIGHT,
        "BEFORE_EVENT": ArgumentRole.BEFORE,
        "AFTER_EVENT": ArgumentRole.AFTER,
        "ACTION_EVENT": ArgumentRole.ACTION,
        "CHANGE_EVENT": ArgumentRole.CHANGE,
        "CAUSE_EVENT": ArgumentRole.CAUSE,
        "EFFECT_EVENT": ArgumentRole.EFFECT,
    }.get(slot_role) or (_ for _ in ()).throw(
        Stage1CompositionError("STAGE1_REQUIRED_ARGUMENT_SLOT_NONUNIQUE_STOP")
    )


def _v2_visible_scalar_carrier_rows(
    clause_plan: Optional[ClausePlan],
    trace_rows: Tuple[SelectedMeaningVisibleCausalTraceRow, ...],
) -> Tuple[Tuple[str, str, Tuple[str, ...], Tuple[str, ...]], ...]:
    """Project selected scalar differences through registered carriers."""

    if clause_plan is None and not trace_rows:
        return ()
    if (
        type(clause_plan) is not ClausePlan
        or not trace_rows
        or any(
            type(row) is not SelectedMeaningVisibleCausalTraceRow
            for row in trace_rows
        )
        or clause_plan.semantic_clause_kind
        not in {
            SemanticClauseKind.GROUNDED_PREDICATE,
            SemanticClauseKind.ADMITTED_RELATION,
        }
        or clause_plan.scalar_surface_realization_rows
        != project_scalar_surface_realization_rows(
            clause_plan.clause_plan_ref,
            clause_plan.scalar_constraint_rows,
        )
    ):
        raise Stage1CompositionError("MEANING_REALIZATION_CAPABILITY_GAP")

    component_refs = _unique(
        ref
        for trace in trace_rows
        for ref in trace.configuration_component_refs
    )
    owner_refs = tuple(
        ref
        for ref in component_refs
        if ref.startswith("owner:") and ref.endswith(f"@{CMEE_OBLIGATION_VERSION}")
    )
    predicate_refs = tuple(ref for ref in component_refs if ref not in owner_refs)
    qualified_carrier = (
        clause_plan.semantic_clause_kind
        is SemanticClauseKind.GROUNDED_PREDICATE
    )
    if (
        qualified_carrier
        and (len(owner_refs) != 1 or not predicate_refs)
    ) or (
        not qualified_carrier
        and (owner_refs or len(predicate_refs) < 2)
    ):
        raise Stage1CompositionError("MEANING_REALIZATION_CAPABILITY_GAP")

    trace_qualifier_refs = _unique(
        ref for trace in trace_rows for ref in trace.source_qualifier_refs
    )
    trace_qualifier_ref_set = set(trace_qualifier_refs)
    invariant_codes = {
        code for trace in trace_rows for code in trace.invariant_codes
    }
    constraint_by_ref = {
        row.clause_scalar_constraint_ref: row
        for row in clause_plan.scalar_constraint_rows
    }
    asset_by_ref = {
        row.morphology_asset_id: row
        for row in SCALAR_MORPHOLOGY_ASSET_REGISTRY
    }
    carrier_rows: list[
        Tuple[str, str, Tuple[str, ...], Tuple[str, ...]]
    ] = []

    def add_asset(
        asset_ref: str,
        qualifier_refs: Tuple[str, ...],
        provenance_refs: Tuple[str, ...],
    ) -> None:
        asset = asset_by_ref.get(asset_ref)
        if (
            asset is None
            or asset.realization_mode
            not in {
                ScalarSurfaceRealizationMode.OVERT_FUNCTIONAL_PART,
                ScalarSurfaceRealizationMode.FUSED_IN_REGISTERED_PART,
            }
            or not asset.morphemes
            or not qualifier_refs
            or not set(qualifier_refs).issubset(trace_qualifier_ref_set)
            or (not provenance_refs and not qualified_carrier)
            or (
                provenance_refs
                and not set(provenance_refs).issubset(component_refs)
            )
            or (qualified_carrier and provenance_refs)
        ):
            raise Stage1CompositionError(
                "MEANING_REALIZATION_CAPABILITY_GAP"
            )
        for morpheme in asset.morphemes:
            row = (morpheme, asset_ref, provenance_refs, qualifier_refs)
            if row not in carrier_rows:
                carrier_rows.append(row)

    for realization in clause_plan.scalar_surface_realization_rows:
        if realization.realization_mode not in {
            ScalarSurfaceRealizationMode.OVERT_FUNCTIONAL_PART,
            ScalarSurfaceRealizationMode.FUSED_IN_REGISTERED_PART,
        }:
            continue
        constraint = constraint_by_ref.get(
            realization.clause_scalar_constraint_ref
        )
        if constraint is None or constraint.owner_ref not in predicate_refs:
            raise Stage1CompositionError(
                "MEANING_REALIZATION_CAPABILITY_GAP"
            )
        value = {
            ClauseScalarAxis.POLARITY: constraint.polarity,
            ClauseScalarAxis.MODALITY: constraint.modality,
            ClauseScalarAxis.TIME_SCOPE: constraint.time_scope,
        }[realization.scalar_axis]
        # Positive polarity is the source predicate's unmarked default.  Keep
        # it in the typed constraint/trace, but do not promote it into an
        # overt functional carrier.  Non-default polarity (for example,
        # NEGATIVE) remains tied to its role-local constraint owner below.
        if (
            realization.scalar_axis is ClauseScalarAxis.POLARITY
            and value == "positive"
        ):
            continue
        qualifier_ref = f"{realization.scalar_axis.value.lower()}:{value}"
        if qualifier_ref in trace_qualifier_ref_set:
            add_asset(
                realization.registered_realization_rule_ref,
                (qualifier_ref,),
                (
                    ()
                    if qualified_carrier
                    else (constraint.owner_ref,)
                ),
            )

    visible_qualifier_refs = {
        ref
        for _surface, _rule, _provenance, refs in carrier_rows
        for ref in refs
    }
    unmarked_qualifier_refs: set[str] = set()
    for realization in clause_plan.scalar_surface_realization_rows:
        if (
            realization.realization_mode
            is not ScalarSurfaceRealizationMode.UNMARKED_DEFAULT
        ):
            continue
        constraint = constraint_by_ref.get(
            realization.clause_scalar_constraint_ref
        )
        asset = asset_by_ref.get(realization.registered_realization_rule_ref)
        if constraint is None or constraint.owner_ref not in predicate_refs:
            raise Stage1CompositionError(
                "MEANING_REALIZATION_CAPABILITY_GAP"
            )
        value = {
            ClauseScalarAxis.POLARITY: constraint.polarity,
            ClauseScalarAxis.MODALITY: constraint.modality,
            ClauseScalarAxis.TIME_SCOPE: constraint.time_scope,
        }[realization.scalar_axis]
        if (
            asset is None
            or asset.scalar_axis is not realization.scalar_axis
            or value not in asset.compatible_values
            or asset.realization_mode
            is not ScalarSurfaceRealizationMode.UNMARKED_DEFAULT
            or asset.realization_target_slot_ref is not None
            or asset.morphemes
        ):
            raise Stage1CompositionError(
                "MEANING_REALIZATION_CAPABILITY_GAP"
            )
        qualifier_ref = f"{realization.scalar_axis.value.lower()}:{value}"
        if qualifier_ref in trace_qualifier_ref_set:
            unmarked_qualifier_refs.add(qualifier_ref)
    visible_qualifier_refs.update(unmarked_qualifier_refs)
    required_qualifier_prefixes = {
        DifferenceInvariantCode.WORLD_COLLAPSE: ("world:",),
        DifferenceInvariantCode.POLARITY_REVERSAL: ("polarity:",),
        DifferenceInvariantCode.MODALITY_PROMOTION: ("modality:",),
        DifferenceInvariantCode.TEMPORAL_COLLAPSE: (
            "time_scope:",
            "aspect:",
        ),
        DifferenceInvariantCode.UNKNOWN_ERASURE: ("unknown:", "world:"),
        DifferenceInvariantCode.EXPLICIT_LIMIT_ERASURE: (
            "scope:",
            "epistemic:",
            "limit:",
            "bounded:",
        ),
    }
    for invariant, prefixes in required_qualifier_prefixes.items():
        if invariant in invariant_codes and not any(
            ref.startswith(prefixes) for ref in visible_qualifier_refs
        ):
            raise Stage1CompositionError(
                "MEANING_REALIZATION_CAPABILITY_GAP"
            )
    if (
        not carrier_rows
        and not unmarked_qualifier_refs
        and set(required_qualifier_prefixes).intersection(invariant_codes)
    ):
        raise Stage1CompositionError("MEANING_REALIZATION_CAPABILITY_GAP")
    return tuple(carrier_rows)


def linearize_japanese_clause(
    *,
    clause_ir: JapaneseClauseIR,
    frame: JapaneseCaseFrameSpec,
    head: AtomicPredicateHeadSpec,
    group: SourceLeafGroup,
    source_leaves: Sequence[SourceLeafToken],
    source_complement_plan: SourceComplementPlan,
    reference_state: V2ClauseReferenceStateBundle,
    link_plan: ClauseLinkPlan,
    morphology_plan: PredicateMorphologyPlan,
    clause_plan: Optional[ClausePlan] = None,
    selected_expression_asset_ref: Optional[str] = None,
    suppress_grouped_sequence_asset_surface: bool = False,
    visible_meaning_trace_rows: Tuple[
        SelectedMeaningVisibleCausalTraceRow, ...
    ] = (),
) -> LinearizedJapaneseClause:
    """Sole v2 text owner; create surface, bindings, and seal together."""

    validate_v2_grammar_inventory()
    leaves = _validate_v2_projected_group_members(group, source_leaves)
    selected_source_plan = select_source_complement_plan(
        group=group,
        source_leaves=leaves,
        frame=frame,
    )
    if source_complement_plan != selected_source_plan:
        raise Stage1CompositionError(
            "STAGE1_SOURCE_COMPLEMENT_NONUNIQUE_STOP"
        )
    expected_ir = _build_japanese_clause_ir_for_validation(
        frame=frame,
        head=head,
        argument_plans=clause_ir.argument_plans
        if type(clause_ir) is JapaneseClauseIR else (),
        source_complement_plan=source_complement_plan,
        reference_state=reference_state,
        link_plan=link_plan,
        morphology_plan=morphology_plan,
    )
    if type(clause_ir) is not JapaneseClauseIR or clause_ir != expected_ir:
        raise Stage1CompositionError("STAGE1_JAPANESE_CLAUSE_IR_TAMPER_STOP")
    _v2_validate_reference_bundle_for_frame(
        frame,
        reference_state,
        clause_ir.argument_plans,
    )
    subject_reference_rule_ids = {
        row.reference_rule_id
        for row in (
            ()
            if reference_state.subject_state is None
            else _v2_reference_rows_from_state(reference_state.subject_state)
        )
    }
    object_reference_rule_ids = {
        row.reference_rule_id
        for row in _v2_reference_rows_from_state(reference_state.object_state)
    }
    link_rule = _v2_validate_link_plan_for_frame(frame, link_plan)
    morphology = _v2_validate_morphology_plan(frame, head, morphology_plan)
    finite_surface = _v2_finite_predicate_surface(head, morphology)
    if (
        type(suppress_grouped_sequence_asset_surface) is not bool
        or (
            suppress_grouped_sequence_asset_surface
            and clause_plan is None
        )
    ):
        raise Stage1CompositionError(
            "STAGE1_EXPRESSION_ASSET_NONUNIQUE_STOP"
        )
    if (clause_plan is None) != (selected_expression_asset_ref is None):
        raise Stage1CompositionError(
            "STAGE1_EXPRESSION_ASSET_NONUNIQUE_STOP"
        )
    expression_asset: Optional[ExpressionAssetSpec] = None
    expression_prefix: Optional[str] = None
    if clause_plan is not None:
        sense = _v2_exact1(
            tuple(
                row
                for row in V2_PREDICATE_SENSE_REGISTRY
                if row.sense_id == frame.sense_ref
            ),
            "STAGE1_EXPRESSION_ASSET_NONUNIQUE_STOP",
        )
        if (
            type(clause_plan) is not ClausePlan
            or clause_plan.semantic_clause_kind.value
            != sense.semantic_clause_kind
            or frame.frame_id not in sense.frame_license_refs
            or (
                suppress_grouped_sequence_asset_surface
                and (
                    sense.sense_id != "S07"
                    or sense.semantic_clause_kind
                    != SemanticClauseKind.ADMITTED_RELATION.value
                )
            )
        ):
            raise Stage1CompositionError(
                "STAGE1_EXPRESSION_ASSET_NONUNIQUE_STOP"
            )
        expression_asset = _v2_exact1(
            tuple(
                row
                for row in EXPRESSION_ASSET_REGISTRY
                if row.expression_asset_id
                == selected_expression_asset_ref
            ),
            "STAGE1_EXPRESSION_ASSET_NONUNIQUE_STOP",
        )
        if (
            expression_asset.sentence_job.value != sense.sentence_job
            or expression_asset.semantic_clause_kind.value
            != sense.semantic_clause_kind
            or expression_asset.predicate_key != sense.semantic_sense
            or clause_plan.predicate_valency
            not in expression_asset.compatible_valencies
            or (
                sense.semantic_clause_kind
                != SemanticClauseKind.SUBJECTIVE_PREDICATE.value
                and expression_asset.reception_projection_branch is not None
            )
            or (
                sense.semantic_clause_kind
                == SemanticClauseKind.SUBJECTIVE_PREDICATE.value
                and suppress_grouped_sequence_asset_surface
            )
            or len(expression_asset.predicate_lexemes) != 2
            or any(not value for value in expression_asset.predicate_lexemes)
        ):
            raise Stage1CompositionError(
                "STAGE1_EXPRESSION_ASSET_NONUNIQUE_STOP"
            )
        if (
            not suppress_grouped_sequence_asset_surface
            and frame.frame_id not in {"F10", "F24"}
        ):
            expression_prefix = expression_asset.predicate_lexemes[0]
    plan_by_role = {
        plan.slot_role: plan for plan in clause_ir.argument_plans
    }
    source_segment_by_slot: dict[
        str,
        list[Tuple[str, str, str, SurfaceDerivation]],
    ] = {slot: [] for slot in frame.slot_roles}

    def structural_segment(
        text: str,
        owner_ref: str,
        slot: str,
    ) -> Tuple[str, str, str, SurfaceDerivation]:
        return (
            text,
            owner_ref,
            slot,
            _v2_surface_derivation(
                SurfaceDerivationKind.REGISTERED_STRUCTURAL_ASSET
            ),
        )

    def functional_segment(
        text: str,
        owner_ref: str,
        slot: str,
        *,
        qualifier_refs: Tuple[str, ...] = (),
    ) -> Tuple[str, str, str, SurfaceDerivation]:
        return (
            text,
            owner_ref,
            slot,
            _v2_surface_derivation(
                SurfaceDerivationKind.PROJECTED_FUNCTIONAL_ASSET,
                owner_ref=owner_ref,
                qualifier_refs=qualifier_refs,
            ),
        )

    def quoted_leaf_segments(
        leaf: SourceLeafToken,
        delimiter_ref: str,
        slot: str,
    ) -> list[Tuple[str, str, str, SurfaceDerivation]]:
        opening, closing = _v2_quote_delimiters(delimiter_ref)
        payload_text = leaf.payload_utf8.decode("utf-8", "strict")
        return [
            structural_segment(opening, f"{delimiter_ref}:OPEN", slot),
            (
                payload_text,
                leaf.semantic_ref,
                slot,
                _v2_surface_derivation(
                    SurfaceDerivationKind.LITERAL_SUBSPAN,
                    source_leaf=leaf,
                ),
            ),
            structural_segment(closing, f"{delimiter_ref}:CLOSE", slot),
        ]

    def direct_leaf_segment(
        leaf: SourceLeafToken,
        slot: str,
    ) -> Tuple[str, str, str, SurfaceDerivation]:
        return (
            leaf.payload_utf8.decode("utf-8", "strict"),
            leaf.semantic_ref,
            slot,
            _v2_surface_derivation(
                SurfaceDerivationKind.LITERAL_SUBSPAN,
                source_leaf=leaf,
            ),
        )

    rule = _v2_exact1(
        tuple(
            row
            for row in V2_COMPLEMENT_RULE_REGISTRY
            if row.complement_rule_id
            == source_complement_plan.complement_rule_ref
        ),
        "STAGE1_SOURCE_COMPLEMENT_NONUNIQUE_STOP",
    )
    source_slots = _v2_complement_case_slots(rule, frame)
    anaphoric_rule_refs = object_reference_rule_ids.intersection({"R03", "R04"})
    if len(anaphoric_rule_refs) > 1:
        raise Stage1CompositionError("STAGE1_REFERENCE_STATE_NONUNIQUE_STOP")
    anaphoric_surface = (
        _v2_reference_surface_for_frame(
            frame,
            SourceLeafCardinality.EXACT1
            if len(leaves) == 1
            else SourceLeafCardinality.ORDERED_EXACT2,
        )
        if anaphoric_rule_refs
        else None
    )
    if anaphoric_rule_refs and (
        anaphoric_surface is None
        or anaphoric_surface.reference_rule_ref
        != next(iter(anaphoric_rule_refs))
    ):
        raise Stage1CompositionError(
            "STAGE1_REFERENCE_REPAIR_UNAVAILABLE_STOP"
        )
    leaf_slots: Tuple[str, ...] = ()
    if anaphoric_surface is not None:
        slot = source_slots[0]
        source_segment_by_slot[slot].append(
            (
                anaphoric_surface.atomic_surface,
                anaphoric_surface.surface_ref,
                slot,
                _v2_surface_derivation(
                    SurfaceDerivationKind.PROJECTED_RESPONSE_OBJECT,
                    response_object_expression=(
                        reference_state.response_object_expression
                    ),
                ),
            )
        )
        realized_leaves: Tuple[
            list[Tuple[str, str, str, SurfaceDerivation]], ...
        ] = ()
    else:
        leaf_slots = (
            source_slots
            if rule.complement_rule_id in {"C07", "C09"}
            else tuple(source_slots[0] for _leaf in leaves)
        )
        if len(leaf_slots) != len(leaves):
            raise Stage1CompositionError(
                "STAGE1_SOURCE_COMPLEMENT_NONUNIQUE_STOP"
            )
        direct_source_safe = all(
            leaf.sentence_shape is SourceSentenceShape.ONE_SENTENCE
            and
            leaf.final_terminal_class
            is SourceFinalTerminalClass.ABSENT
            and leaf.line_break_shape is SourceLineBreakShape.NONE
            for leaf in leaves
        )
        if (
            not source_complement_plan.quote_delimiter_refs
            and not direct_source_safe
        ):
            raise Stage1CompositionError(
                "STAGE1_SOURCE_COMPLEMENT_NONUNIQUE_STOP"
            )
        if source_complement_plan.quote_delimiter_refs:
            realized_leaves = tuple(
                quoted_leaf_segments(leaf, delimiter_ref, slot)
                for leaf, delimiter_ref, slot in zip(
                    leaves,
                    source_complement_plan.quote_delimiter_refs,
                    leaf_slots,
                    strict=True,
                )
            )
        else:
            realized_leaves = tuple(
                [direct_leaf_segment(leaf, slot)]
                for leaf, slot in zip(leaves, leaf_slots, strict=True)
            )
    if anaphoric_surface is not None:
        pass
    elif rule.complement_rule_id in {"C02", "C03", "C04", "C05", "C06"}:
        slot = source_slots[0]
        source_segment_by_slot[slot].extend(realized_leaves[0])
        if rule.complement_rule_id in {"C03", "C04", "C05", "C06"}:
            token = _v2_exact1(
                tuple(
                    row
                    for row in V2_SOURCE_FUNCTIONAL_TOKEN_REGISTRY
                    if row.token_id == "SF01"
                ),
                "STAGE1_SOURCE_COMPLEMENT_NONUNIQUE_STOP",
            )
            source_segment_by_slot[slot].append(
                functional_segment(token.atomic_surface, token.token_id, slot)
            )
        if rule.complement_rule_id in {"C03", "C04"}:
            token = _v2_exact1(
                tuple(
                    row
                    for row in V2_SOURCE_FUNCTIONAL_TOKEN_REGISTRY
                    if row.token_id == "SF02"
                ),
                "STAGE1_SOURCE_COMPLEMENT_NONUNIQUE_STOP",
            )
            source_segment_by_slot[slot].append(
                functional_segment(token.atomic_surface, token.token_id, slot)
            )
        elif rule.complement_rule_id in {"C05", "C06"}:
            classifier = _v2_exact1(
                tuple(
                    row
                    for row in V2_SOURCE_CLASSIFIER_REGISTRY
                    if row.classifier_id
                    == source_complement_plan.classifier_ref
                ),
                "STAGE1_SOURCE_CLASSIFIER_NONUNIQUE_STOP",
            )
            source_segment_by_slot[slot].append(
                functional_segment(
                    classifier.atomic_surface,
                    classifier.classifier_id,
                    slot,
                )
            )
    elif rule.complement_rule_id == "C07":
        for slot, leaf_segments in zip(source_slots, realized_leaves):
            source_segment_by_slot[slot].extend(leaf_segments)
    elif rule.complement_rule_id == "C08":
        slot = source_slots[0]
        source_segment_by_slot[slot].extend(realized_leaves[0])
        coordinator = _v2_exact1(
            tuple(
                row
                for row in V2_SOURCE_FUNCTIONAL_TOKEN_REGISTRY
                if row.token_id == source_complement_plan.coordinator_ref
            ),
            "STAGE1_SOURCE_COMPLEMENT_NONUNIQUE_STOP",
        )
        source_segment_by_slot[slot].append(
            functional_segment(
                coordinator.atomic_surface,
                coordinator.token_id,
                slot,
            )
        )
        source_segment_by_slot[slot].extend(realized_leaves[1])
    elif rule.complement_rule_id == "C09":
        for slot, leaf_segments in zip(source_slots, realized_leaves):
            source_segment_by_slot[slot].extend(leaf_segments)
    else:
        raise Stage1CompositionError(
            "STAGE1_SOURCE_COMPLEMENT_NONUNIQUE_STOP"
        )

    segments: list[Tuple[str, str, str, SurfaceDerivation]] = []
    if link_rule.placement in {
        "SENTENCE_INITIAL",
        "SENTENCE_INITIAL_ADDITIVE",
    }:
        token = link_rule.token_ref.removeprefix("registered:")
        if not token:
            raise Stage1CompositionError("STAGE1_CLAUSE_LINK_NONUNIQUE_STOP")
        segments.append(
            functional_segment(token, link_rule.link_rule_id, "CLAUSE_LINK")
        )
        segments.append(
            structural_segment("、", "CLAUSE_LINK_COMMA", "CLAUSE_LINK")
        )

    for surface, rule_ref, provenance_refs, qualifier_refs in (
        ()
        if not visible_meaning_trace_rows
        else _v2_visible_scalar_carrier_rows(
            clause_plan,
            visible_meaning_trace_rows,
        )
    ):
        if any(
            ref.startswith("owner:")
            and ref.endswith(f"@{CMEE_OBLIGATION_VERSION}")
            for ref in provenance_refs
        ):
            raise Stage1CompositionError(
                "MEANING_REALIZATION_CAPABILITY_GAP"
            )
        segments.append(
            functional_segment(
                surface,
                rule_ref,
                "QUALIFIER",
                qualifier_refs=_unique(
                    (*qualifier_refs, *provenance_refs)
                ),
            )
        )
        segments.append(
            structural_segment(
                "、",
                "QUALIFIER_COMMA",
                "QUALIFIER",
            )
        )

    if (
        expression_prefix is not None
        and clause_plan.semantic_clause_kind
        is SemanticClauseKind.ADMITTED_RELATION
    ):
        segments.append(
            functional_segment(
                expression_prefix,
                expression_asset.expression_asset_id,
                "PREDICATE_HEAD",
            )
        )
        segments.append(
            structural_segment(
                "、",
                "EXPRESSION_ASSET_COMMA",
                "PREDICATE_HEAD",
            )
        )

    topic_selected = bool(subject_reference_rule_ids & {"R08", "R09"})
    if frame.zero_policy != "EMLIS_ZERO_CONDITIONAL":
        topic_selected = bool(object_reference_rule_ids & {"R08", "R09"})
    zero_subject = "R06" in subject_reference_rule_ids
    modifier = None
    if frame.modifier_ref is not None:
        modifier = _v2_exact1(
            tuple(
                row
                for row in V2_SOURCE_FUNCTIONAL_MODIFIER_REGISTRY
                if row.modifier_id == frame.modifier_ref
                and row.frame_ref == frame.frame_id
            ),
            "STAGE1_SOURCE_COMPLEMENT_NONUNIQUE_STOP",
        )
    for slot in frame.slot_roles:
        plan = plan_by_role[slot]
        is_emlis_subject = (
            slot == "SUBJECT"
            and frame.zero_policy == "EMLIS_ZERO_CONDITIONAL"
        )
        if is_emlis_subject:
            if not zero_subject:
                segments.append(
                    (
                        "Emlis",
                        CMEE_STAGE1_EMLIS_OWNER_REF,
                        slot,
                        _v2_surface_derivation(
                            SurfaceDerivationKind.REGISTERED_EMLIS_LEXEME,
                            owner_ref=CMEE_STAGE1_EMLIS_OWNER_REF,
                        ),
                    )
                )
        else:
            segments.extend(source_segment_by_slot[slot])

        if not (is_emlis_subject and zero_subject):
            particle = _v2_exact1(
                tuple(
                    row
                    for row in V2_CASE_PARTICLE_REGISTRY
                    if row.particle_rule_id == plan.particle_rule_ref
                    and row.frame_ref == frame.frame_id
                    and row.slot_role == slot
                ),
                "STAGE1_CASE_PARTICLE_OWNER_NONUNIQUE_STOP",
            )
            requested_variant = (
                "TOPIC"
                if slot == "SUBJECT" and topic_selected
                else "BASE"
                if slot == "SUBJECT"
                else "FIXED"
            )
            variant = _v2_exact1(
                tuple(
                    row
                    for row in particle.surface_variants
                    if row.variant_kind == requested_variant
                ),
                "STAGE1_CASE_PARTICLE_OWNER_NONUNIQUE_STOP",
            )
            segments.append(
                functional_segment(
                    variant.atomic_surface,
                    particle.particle_rule_id,
                    slot,
                )
            )
        if (
            modifier is not None
            and modifier.placement == "AFTER_SUBJECT_BEFORE_PRIMARY_OBJECT"
            and slot == "SUBJECT"
        ):
            segments.append(
                functional_segment(
                    modifier.atomic_surface,
                    modifier.modifier_id,
                    "MODIFIER",
                )
            )
        if (
            modifier is not None
            and modifier.placement == "AFTER_PRIMARY_OBJECT_BEFORE_HEAD"
            and slot == "PRIMARY_OBJECT"
        ):
            segments.append(
                functional_segment(
                    modifier.atomic_surface,
                    modifier.modifier_id,
                    "MODIFIER",
                )
            )
        if (
            expression_prefix is not None
            and clause_plan.semantic_clause_kind
            is SemanticClauseKind.SUBJECTIVE_PREDICATE
            and slot == "SUBJECT"
            and (
                modifier is None
                or modifier.atomic_surface
                != expression_prefix
            )
        ):
            segments.append(
                functional_segment(
                    expression_prefix,
                    expression_asset.expression_asset_id,
                    "PREDICATE_HEAD",
                )
            )
            segments.append(
                structural_segment(
                    "、",
                    "EXPRESSION_ASSET_COMMA",
                    "PREDICATE_HEAD",
                )
            )

    segments.append(
        functional_segment(
            finite_surface,
            morphology_plan.plan_ref,
            "PREDICATE_HEAD",
        )
    )
    if morphology_plan.terminal_order[-1:] != ("PERIOD",):
        raise Stage1CompositionError(
            "STAGE1_SOURCE_TERMINAL_OWNERSHIP_STOP"
        )
    segments.append(
        structural_segment("。", "MATRIX_TERMINAL_PERIOD", "TERMINAL")
    )
    if any(not text for text, _owner, _slot, _derivation in segments):
        raise Stage1CompositionError("STAGE1_DERIVATION_SEAL_STOP")

    text = "".join(segment[0] for segment in segments)
    bindings: list[RealizedSemanticBinding] = []
    derivations: list[SurfaceDerivation] = []
    cursor = 0
    for surface, semantic_ref, clause_slot, derivation in segments:
        end = cursor + len(surface)
        bindings.append(
            RealizedSemanticBinding(
                semantic_ref=semantic_ref,
                clause_slot=clause_slot,
                surface_scalar_start=cursor,
                surface_scalar_end=end,
                surface_span_sha256=hashlib.sha256(
                    surface.encode("utf-8")
                ).hexdigest(),
            )
        )
        derivations.append(derivation)
        cursor = end
    if (
        cursor != len(text)
        or tuple(binding.surface_scalar_start for binding in bindings)
        != tuple(
            0 if index == 0 else bindings[index - 1].surface_scalar_end
            for index in range(len(bindings))
        )
        or len(bindings) != len(derivations)
    ):
        raise Stage1CompositionError("STAGE1_DERIVATION_SEAL_STOP")
    if anaphoric_surface is None:
        literal_slot_rows = tuple(
            (binding.semantic_ref, binding.clause_slot)
            for binding, derivation in zip(bindings, derivations, strict=True)
            if derivation.derivation_kind
            is SurfaceDerivationKind.LITERAL_SUBSPAN
        )
        expected_literal_slot_rows = tuple(
            (leaf.semantic_ref, slot)
            for leaf, slot in zip(leaves, leaf_slots, strict=True)
        )
        if literal_slot_rows != expected_literal_slot_rows:
            raise Stage1CompositionError("STAGE1_DERIVATION_SEAL_STOP")

    argument_bindings = tuple(
        ArgumentBinding(
            role=_v2_clause_argument_role(frame, plan.slot_role),
            semantic_ref=plan.semantic_ref,
        )
        for plan in clause_ir.argument_plans
    )
    primary_object = next(
        (
            plan.semantic_ref
            for plan in clause_ir.argument_plans
            if plan.slot_role == "PRIMARY_OBJECT"
        ),
        None,
    )
    subjective = frame.zero_policy == "EMLIS_ZERO_CONDITIONAL"
    clause_frame = ClauseFrame(
        move_ref=clause_ir.clause_ir_ref,
        discourse_relation=link_plan.admitted_relation_ref,
        topic_ref=(
            (
                reference_state.subject_state.focus_ref
                if reference_state.subject_state is not None
                else reference_state.object_state.focus_ref
            )
            if topic_selected
            else None
        ),
        predicate_operator=head.head_id,
        object_ref=primary_object,
        argument_bindings=argument_bindings,
        qualifier_refs=(() if modifier is None else (modifier.modifier_id,)),
        polarity=morphology_plan.polarity,
        modality=morphology_plan.modal,
        time_scope=morphology_plan.aspect_time,
        actor_refs=(
            (CMEE_STAGE1_EMLIS_OWNER_REF,) if subjective else ()
        ),
        experiencer_refs=(
            (CMEE_STAGE1_EMLIS_OWNER_REF,) if subjective else ()
        ),
        addressee_role="CURRENT_USER_ADDRESSEE",
        epistemic_marker=None,
        speaker_marker=(
            CMEE_STAGE1_EMLIS_OWNER_REF if subjective else None
        ),
        connective_requirement=(
            link_plan.link_plan_ref
            if link_rule.placement
            in {"SENTENCE_INITIAL", "SENTENCE_INITIAL_ADDITIVE"}
            else None
        ),
        reception_style_policy_ref=CMEE_STAGE1_COMPOSITION_POLICY_VERSION,
        terminal_style=morphology.terminal_class,
    )
    return LinearizedJapaneseClause(
        clause_ref=_ref(
            "linearized-japanese-clause-v2",
            (
                clause_ir.clause_ir_ref,
                text,
                tuple(bindings),
                tuple(derivations),
            ),
        ),
        text=text,
        clause_frames=(clause_frame,),
        realized_semantic_bindings=tuple(bindings),
        surface_derivations=tuple(derivations),
    )


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
    premeaning_inputs = phase_A.premeaning_inputs
    envelope = phase_A.allowed_reception_opportunity_envelope
    if (
        type(premeaning_inputs) is not PreMeaningGroundedInputs
        or type(envelope) is not AllowedReceptionOpportunityEnvelope
    ):
        raise Stage1CompositionError(
            "STAGE1_PREMEANING_RECEPTION_SPLIT_STOP"
        )
    try:
        validate_premeaning_grounded_inputs(
            premeaning_inputs,
            source=phase_A.admitted_source,
            grounded_plan=phase_A.grounded_plan,
            grounded_graph=phase_A.grounded_graph,
            parent_plan=phase_A.parent_plan,
        )
        from .emlis_stage1_response import (
            _bind_grounded_plan,
            _bind_reception_moves,
            _ordered,
            _semantic_reception_asset,
            validate_allowed_reception_opportunity_envelope,
            validate_reception_asset_mapping,
        )

        validate_allowed_reception_opportunity_envelope(
            envelope,
            source=phase_A.admitted_source,
            grounded_graph=phase_A.grounded_graph,
            parent_plan=phase_A.parent_plan,
            grounded_plan=phase_A.grounded_plan,
        )
        reception_plan = _semantic_reception_asset(
            source=phase_A.admitted_source,
            grounded_plan=phase_A.grounded_plan,
        )
        validate_reception_asset_mapping(
            reception_plan,
            grounded_plan=phase_A.grounded_plan,
        )
        retained_act_ids = envelope.allowed_reception_act_ids
        if _ordered(
            str(move.reception_act) for move in reception_plan.moves
        ) != retained_act_ids:
            raise CMEEStage1ContractError(
                "stage1_reception_parent_act_mismatch"
            )
        plan_binding = _bind_grounded_plan(
            phase_A.admitted_source,
            phase_A.grounded_graph,
            phase_A.grounded_plan,
        )
        bound_moves = _bind_reception_moves(
            reception_plan,
            binding=plan_binding,
            contributions=phase_A.observation_contribution_rows,
        )
        expected_retained_reception_act_rows = tuple(
            RetainedReceptionActRow(
                act_ref,
                act_ref,
                _ordered(
                    row.contribution_id
                    for bound_move in bound_moves
                    if str(bound_move.move.reception_act) == act_ref
                    for row in bound_move.basis_contributions
                ),
            )
            for act_ref in retained_act_ids
        )
        if any(
            not row.basis_contribution_refs
            for row in expected_retained_reception_act_rows
        ):
            raise CMEEStage1ContractError(
                "stage1_final_reception_act_basis_missing"
            )
        validate_grounded_situation_view(
            phase_A.grounded_situation_view,
            premeaning_inputs,
            phase_A.grounded_graph,
        )
        validate_foreground_scope_derivation(
            phase_A.foreground_scope_derivation,
            basis_rows=phase_A.grounded_situation_view.basis_rows,
            premeaning_inputs=premeaning_inputs,
            source=phase_A.admitted_source,
            grounded_plan=phase_A.grounded_plan,
            grounded_graph=phase_A.grounded_graph,
            parent_plan=phase_A.parent_plan,
        )
        validate_foreground_scope_disposition(
            phase_A.foreground_scope_disposition,
            phase_A.foreground_scope_derivation,
        )
    except CMEEStage1ContractError:
        raise Stage1CompositionError(
            "STAGE1_PREMEANING_RECEPTION_SPLIT_STOP"
        ) from None
    if (
        phase_A.retained_reception_act_rows
        != expected_retained_reception_act_rows
    ):
        raise Stage1CompositionError(
            "STAGE1_RECEPTION_ACT_BASIS_CLOSURE_STOP"
        )
    try:
        validate_input_specific_meaning_structure(
            phase_A.input_specific_meaning_structure,
            grounded_view=phase_A.grounded_situation_view,
            foreground_scope_derivation=(
                phase_A.foreground_scope_derivation
            ),
        )
    except CMEEStage1ContractError:
        raise Stage1CompositionError(
            "STAGE1_INPUT_SPECIFIC_MEANING_STRUCTURE_STOP"
        ) from None
    try:
        expected_projection_preimage_ref = (
            project_stage1_projection_preimage_ref(
                grounded_graph_ref=(
                    f"grounded:{getattr(phase_A.grounded_graph, 'graph_id', '')}"
                    f"@{CMEE_GROUNDED_GRAPH_SCHEMA_VERSION}"
                ),
                parent_observation_duty_ref=(
                    phase_A.parent_plan.observation_duty_id
                ),
                parent_reception_duty_ref=(
                    phase_A.parent_plan.reception_duty_id
                ),
                interpretation_candidate_ids=tuple(
                    row.candidate_id
                    for row in phase_A.interpretation_candidate_rows
                ),
                meaning_field_id=phase_A.meaning_field.meaning_field_id,
                observation_contribution_ids=tuple(
                    row.contribution_id
                    for row in phase_A.observation_contribution_rows
                ),
                retained_reception_act_ids=tuple(
                    row.act_ref for row in phase_A.retained_reception_act_rows
                ),
                observation_depth_class=phase_A.observation_depth_class,
                temperature_class=phase_A.temperature_class,
                reception_style_policy_ref=(
                    phase_A.reception_style_policy_ref
                ),
                emlis_value_policy_ref=phase_A.emlis_value_policy_ref,
            )
        )
    except (AttributeError, TypeError, CMEEStage1ContractError):
        raise Stage1CompositionError(
            "STAGE1_PROJECTION_PREIMAGE_CLOSURE_STOP"
        ) from None
    if phase_A.projection_preimage_ref != expected_projection_preimage_ref:
        raise Stage1CompositionError(
            "STAGE1_PROJECTION_PREIMAGE_CLOSURE_STOP"
        )
    try:
        validate_stage1_post_selection_reception_records(
            input_specific_meaning_structure=(
                phase_A.input_specific_meaning_structure
            ),
            projection_preimage_ref=phase_A.projection_preimage_ref,
            reading_consequence_records=(
                phase_A.reading_consequence_records
            ),
            sealed_emlis_provisional_reading_records=(
                phase_A.sealed_emlis_provisional_reading_records
            ),
            meaning_bound_reception_proposition_records=(
                phase_A.meaning_bound_reception_proposition_records
            ),
            meaning_bound_reception_set_records=(
                phase_A.meaning_bound_reception_set_records
            ),
            bounded_limited_reception_records=(
                phase_A.bounded_limited_reception_records
            ),
            bounded_limited_subjective_proposition_records=(
                phase_A.bounded_limited_subjective_proposition_records
            ),
            projection_seal_ref=phase_A.projection_seal_ref,
            retained_reception_act_rows=(
                phase_A.retained_reception_act_rows
            ),
            observation_contribution_rows=(
                phase_A.observation_contribution_rows
            ),
            interpretation_candidate_rows=(
                phase_A.interpretation_candidate_rows
            ),
            contribution_to_candidate_ref_map=(
                phase_A.contribution_to_candidate_ref_map
            ),
            qualifier_value_rows=(
                phase_A.qualifier_value_by_candidate_scope_axis_key
            ),
            material_unknown_refs=phase_A.material_unknown_refs,
        )
    except CMEEStage1ContractError:
        raise Stage1CompositionError(
            "STAGE1_INPUT_SPECIFIC_MEANING_STRUCTURE_STOP"
        ) from None
    if (
        premeaning_inputs.grounded_graph is not phase_A.grounded_graph
        or premeaning_inputs.meaning_field != phase_A.meaning_field
        or premeaning_inputs.observation_contribution_rows
        != phase_A.observation_contribution_rows
        or premeaning_inputs.material_unknown_refs
        != phase_A.material_unknown_refs
        or premeaning_inputs.observation_depth_class
        is not phase_A.observation_depth_class
        or type(phase_A.grounded_situation_view)
        is not GroundedSituationView
        or type(phase_A.foreground_scope_derivation)
        is not ForegroundScopeDerivation
        or type(phase_A.foreground_scope_disposition)
        is not ForegroundScopeDisposition
        or type(phase_A.input_specific_meaning_structure)
        is not InputSpecificMeaningStructure
        or envelope.source_envelope_id
        != phase_A.parent_plan.source_envelope_id
        or envelope.parent_reception_duty_ref
        != phase_A.parent_plan.reception_duty_id
    ):
        raise Stage1CompositionError(
            "STAGE1_PREMEANING_RECEPTION_SPLIT_STOP"
        )
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
    premeaning_candidate_ids = {
        row.candidate_id
        for row in premeaning_inputs.interpretation_candidate_rows
    }
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
        or retained_act_refs != envelope.allowed_reception_act_ids
        or not premeaning_candidate_ids.issubset(candidate_ids)
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
    authority = getattr(phase_B, "phase_A_authority", None)
    if type(authority) is not Stage1SubjectivePlanningInputs:
        raise Stage1CompositionError(
            "STAGE1_FINAL_PROJECTION_CLOSURE_STOP"
        )
    _validate_phase_A(authority)
    _validate_registry_snapshots(phase_B)
    _validate_phase_lineage(phase_B, projection=phase_B.projection)
    _projection_ref(phase_B.projection)
    try:
        validate_stage1_projection(
            phase_B.projection,
            grounded_graph=phase_B.grounded_graph,
            parent_plan=phase_B.parent_plan,
        )
    except CMEEStage1ContractError:
        raise Stage1CompositionError(
            "STAGE1_FINAL_PROJECTION_CLOSURE_STOP"
        ) from None
    try:
        from . import emlis_stage1_response as response

        response._validate_meaning_plan_carrier_trace(
            authority,
            phase_B.projection,
        )
    except CMEEStage1ContractError:
        raise Stage1CompositionError(
            "STAGE1_FINAL_PROJECTION_CLOSURE_STOP"
        ) from None
    expected_addressee_deictic_context = bool(
        {
            str(getattr(row.grounded_frame, "actor", "")).lower()
            for row in authority.resolved_grounded_frame_by_candidate_ref
        }.intersection({"current_user", "user"})
    )
    if (
        phase_B.admitted_source is not authority.admitted_source
        or phase_B.grounded_graph is not authority.grounded_graph
        or phase_B.grounded_plan is not authority.grounded_plan
        or phase_B.parent_plan is not authority.parent_plan
        or phase_B.resolved_grounded_frame_by_candidate_ref
        is not authority.resolved_grounded_frame_by_candidate_ref
        or phase_B.relation_endpoint_grounded_candidate_ref_by_binding_key
        is not authority.relation_endpoint_grounded_candidate_ref_by_binding_key
        or phase_B.qualifier_value_by_candidate_scope_axis_key
        is not authority.qualifier_value_by_candidate_scope_axis_key
        or phase_B.construction_registry_snapshot
        is not authority.construction_registry_snapshot
        or phase_B.expression_asset_registry_snapshot
        is not authority.expression_asset_registry_snapshot
        or phase_B.response_object_registry_snapshot
        is not authority.response_object_registry_snapshot
        or phase_B.functional_asset_registry_snapshot
        is not authority.functional_asset_registry_snapshot
        or phase_B.participant_asset_registry_snapshot
        is not authority.participant_asset_registry_snapshot
        or phase_B.structural_asset_registry_snapshot
        is not authority.structural_asset_registry_snapshot
        or phase_B.profile_rule_registry_snapshot
        is not authority.profile_rule_registry_snapshot
        or phase_B.addressee_deictic_context
        is not expected_addressee_deictic_context
    ):
        raise Stage1CompositionError(
            "STAGE1_FINAL_PROJECTION_CLOSURE_STOP"
        )
    if type(phase_B.addressee_deictic_context) is not bool:
        raise Stage1CompositionError("STAGE1_COMPOSITION_DEICTIC_CONTEXT_STOP")
    claims = _claims(phase_B.projection)
    if (
        not 1 <= len(claims) <= 4
        or any(
            type(claim) is not EmlisSubjectiveClaim
            or claim.schema_version != CMEE_STAGE1_RESPONSE_SCHEMA_VERSION
            or claim.speaker_owner != "EMLIS"
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
    authority: _ProjectionCommonAuthority,
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
            for row in authority.qualifier_value_by_candidate_scope_axis_key
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
        or suppressions
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
        or len(flattened_responsibility_refs)
        != len(set(flattened_responsibility_refs))
        or set(flattened_responsibility_refs) != set(responsibility_by_ref)
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


def _projection_binding_rows(
    authority: _ProjectionCommonAuthority,
) -> tuple[
    tuple[SubjectiveBasisBinding, ...],
    tuple[SourceQualifierBinding, ...],
    tuple[PolicyBasisBinding, ...],
]:
    """Project only base-bound rows; never derive or select meaning."""

    contributions = authority.observation_contribution_rows
    candidates = {
        row.candidate_id: row
        for row in authority.interpretation_candidate_rows
    }
    contribution_candidate = dict(
        authority.contribution_to_candidate_ref_map
    )
    if set(contribution_candidate) != {
        row.contribution_id for row in contributions
    }:
        raise Stage1CompositionError(
            "STAGE1_CONTRIBUTION_CANDIDATE_CLOSURE_STOP"
        )

    basis_rows: list[SubjectiveBasisBinding] = []
    qualifier_rows: list[SourceQualifierBinding] = []
    for contribution in contributions:
        candidate = candidates.get(
            contribution_candidate[contribution.contribution_id]
        )
        if candidate is None:
            raise Stage1CompositionError(
                "STAGE1_CONTRIBUTION_CANDIDATE_CLOSURE_STOP"
            )
        for binding in candidate.argument_bindings:
            if binding.role is ArgumentRole.EXPERIENCER:
                continue
            role = _basis_role(contribution, binding.role)
            basis_ref = project_stage1_subjective_basis_binding_ref(
                projection_preimage_ref=authority.projection_preimage_ref,
                contribution_ref=contribution.contribution_id,
                semantic_ref=binding.semantic_ref,
                role=role,
            )
            basis = SubjectiveBasisBinding(
                authority.projection_preimage_ref,
                basis_ref,
                contribution.contribution_id,
                binding.semantic_ref,
                role,
            )
            polarity, modality, time_scope, qualifier_role = (
                _qualifier_lookup(authority, candidate, binding)
            )
            prefix = (
                ""
                if qualifier_role is None
                else f"{qualifier_role.value.lower()}_"
            )
            qualifier_codes = (
                f"{prefix}polarity:{polarity}",
                f"{prefix}modality:{modality}",
                f"{prefix}time_scope:{time_scope}",
            )
            qualifier_ref = project_stage1_source_qualifier_binding_ref(
                projection_preimage_ref=authority.projection_preimage_ref,
                basis_binding_ref=basis_ref,
                source_candidate_ref=candidate.candidate_id,
                source_argument_role=qualifier_role,
                canonical_qualifier_codes=qualifier_codes,
                polarity=polarity,
                modality=modality,
                time_scope=time_scope,
            )
            basis_rows.append(basis)
            qualifier_rows.append(
                SourceQualifierBinding(
                    authority.projection_preimage_ref,
                    qualifier_ref,
                    basis_ref,
                    candidate.candidate_id,
                    qualifier_role,
                    qualifier_codes,
                    polarity,
                    modality,
                    time_scope,
                )
            )
    if not basis_rows or len(basis_rows) != len(qualifier_rows):
        raise Stage1CompositionError(
            "MEANING_REALIZATION_CAPABILITY_GAP"
        )

    policy_basis_rows: list[PolicyBasisBinding] = []
    for contribution in contributions:
        if contribution.semantic_operator in {
            SemanticOperator.PRESENT_BURDEN,
            SemanticOperator.PRESENT_RESIDUE,
        }:
            role = PolicyBasisRole.BURDEN_OR_RESIDUE
        elif contribution.semantic_operator is SemanticOperator.PRESENT_DIRECTION:
            role = PolicyBasisRole.DIRECTION
        elif contribution.semantic_operator in {
            SemanticOperator.PRESENT_CHANGE,
            SemanticOperator.PRESENT_ACTUAL_OUTPUT,
        }:
            role = PolicyBasisRole.CHANGE_OR_ACTUAL_OUTPUT
        elif (
            contribution.semantic_operator
            is SemanticOperator.PRESENT_UNFINISHED
        ):
            role = PolicyBasisRole.UNFINISHED
        else:
            role = PolicyBasisRole.COEXISTENCE_OR_TENSION
        binding_ref = project_stage1_policy_basis_binding_ref(
            projection_preimage_ref=authority.projection_preimage_ref,
            owner_kind=PolicyBasisOwnerKind.CONTRIBUTION,
            owner_ref=contribution.contribution_id,
            role=role,
        )
        policy_basis_rows.append(
            PolicyBasisBinding(
                authority.projection_preimage_ref,
                binding_ref,
                PolicyBasisOwnerKind.CONTRIBUTION,
                contribution.contribution_id,
                role,
            )
        )
    for unknown_ref in authority.material_unknown_refs:
        binding_ref = project_stage1_policy_basis_binding_ref(
            projection_preimage_ref=authority.projection_preimage_ref,
            owner_kind=PolicyBasisOwnerKind.MATERIAL_UNKNOWN,
            owner_ref=unknown_ref,
            role=PolicyBasisRole.MATERIAL_UNKNOWN,
        )
        policy_basis_rows.append(
            PolicyBasisBinding(
                authority.projection_preimage_ref,
                binding_ref,
                PolicyBasisOwnerKind.MATERIAL_UNKNOWN,
                unknown_ref,
                PolicyBasisRole.MATERIAL_UNKNOWN,
            )
        )
    return tuple(basis_rows), tuple(qualifier_rows), tuple(policy_basis_rows)


def _normal_reception_operator(
    proposition: MeaningBoundReceptionProposition,
) -> SubjectiveOperator:
    rows = tuple(
        operator
        for mapping in CMEE_STAGE1_RECEPTION_ACT_MAPPING_EXACT7
        if mapping.reception_act == proposition.reception_function
        for mode, operator in mapping.eligible_mode_operator_pairs
        if mode is proposition.subjective_mode
    )
    if len(rows) != 1:
        raise Stage1CompositionError(
            "MEANING_REALIZATION_CAPABILITY_GAP"
        )
    return rows[0]


def _normal_reception_appraisal(
    *,
    proposition: MeaningBoundReceptionProposition,
    contributions: tuple[PlannedObservationContribution, ...],
    basis_rows: tuple[SubjectiveBasisBinding, ...],
    semantic_contributions: Optional[
        tuple[PlannedObservationContribution, ...]
    ] = None,
) -> EmlisAppraisalContent:
    """Derive one act-local appraisal without whole-input focus priority."""

    semantic_rows = (
        contributions
        if semantic_contributions is None
        else semantic_contributions
    )
    relation_rows = tuple(
        row
        for row in semantic_rows
        if row.relation_operator
        in {
            RelationOperator.COEXISTS_WITH,
            RelationOperator.TENSION_WITH,
        }
    )
    unfinished = any(
        row.semantic_operator
        in {
            SemanticOperator.PRESENT_RESIDUE,
            SemanticOperator.PRESENT_UNFINISHED,
        }
        or row.contribution_kind
        in {
            ObservationContributionKind.PRESERVE_RESIDUE,
            ObservationContributionKind.PRESERVE_UNFINISHED,
        }
        for row in semantic_rows
    )
    bounded_change = (
        proposition.reception_function == "recognize_lived_change"
        and any(
            row.semantic_operator is SemanticOperator.PRESENT_CHANGE
            for row in semantic_rows
        )
    )
    agency = (
        proposition.reception_function == "protect_retained_intention"
        and not relation_rows
        and any(
            row.semantic_operator is SemanticOperator.PRESENT_DIRECTION
            for row in semantic_rows
        )
    )
    material = proposition.reception_function in {
        "stay_with_current_burden",
        "honor_concrete_effort",
        "respect_words_placed",
    } and not (relation_rows or unfinished or bounded_change or agency)
    matched = sum(
        (
            bool(relation_rows),
            unfinished,
            bounded_change,
            agency,
            material,
        )
    )
    if matched != 1:
        raise Stage1CompositionError(
            "MEANING_REALIZATION_CAPABILITY_GAP"
        )

    focal_relation_ref: Optional[str] = None
    if relation_rows:
        reciprocal_pair = _reciprocal_tension_relation_pair(
            relation_rows
        )
        appraised_semantic_refs = _unique(
            row.semantic_ref for row in basis_rows
        )
        focal_relation_rows = (
            relation_rows
            if len(relation_rows) == 1
            else tuple(
                row
                for row in reciprocal_pair
                if _ordered_relation_endpoint_refs(row)
                == appraised_semantic_refs
            )
        )
        if len(focal_relation_rows) != 1:
            raise Stage1CompositionError(
                "MEANING_REALIZATION_CAPABILITY_GAP"
            )
        dimension = AppraisalDimension.RELATIONAL_NONCOLLAPSE
        operation = AppraisalOperation.PRESERVE_BOTH_ENDPOINTS
        focal_relation_ref = _relation_refs(focal_relation_rows[0])[0]
    elif unfinished:
        dimension = AppraisalDimension.UNFINISHED_OPENNESS
        operation = AppraisalOperation.LEAVE_UNFINISHED
    elif bounded_change:
        dimension = AppraisalDimension.BOUNDED_CHANGE
        operation = AppraisalOperation.RECOGNIZE_AS_BOUNDED
    elif agency:
        dimension = AppraisalDimension.AGENCY_BOUNDARY
        operation = AppraisalOperation.RESPECT_CHOICE
    else:
        dimension = AppraisalDimension.MATERIAL_WEIGHT
        operation = AppraisalOperation.RECEIVE_AS_MATERIAL
    return EmlisAppraisalContent(
        dimension,
        operation,
        tuple(row.binding_ref for row in basis_rows),
        focal_relation_ref,
        (),
        tuple(row.contribution_id for row in contributions),
    )


def _normal_reception_position(
    *,
    proposition: MeaningBoundReceptionProposition,
    basis_rows: tuple[SubjectiveBasisBinding, ...],
) -> EmlisRelationalPosition:
    if proposition.optional_stance is not None:
        return proposition.optional_stance
    if proposition.reception_function == "protect_retained_intention":
        operator = StanceOperator.PROTECT_USER_AGENCY
        commitment = RelationalCommitment.PROTECT_AGENCY
        closure = RelationalClosure.BOUNDED
    elif proposition.reception_function == "hold_help_seeking":
        operator = StanceOperator.STAY_WITH_SPECIFIC_OBJECT
        commitment = RelationalCommitment.STAY_WITH
        closure = RelationalClosure.NONE
    else:
        raise Stage1CompositionError(
            "MEANING_REALIZATION_CAPABILITY_GAP"
        )
    return EmlisRelationalPosition(
        RelationalPositionKind.STANCE,
        operator,
        tuple(row.binding_ref for row in basis_rows),
        (),
        commitment,
        closure,
    )


def _projected_claim_identity(
    *,
    proposition: SubjectivePropositionV2,
    parent_duty_ref: str,
    responsibility_refs: tuple[str, ...],
    opportunity_key: str,
    contribution_refs: tuple[str, ...],
    semantic_refs: tuple[str, ...],
    act_refs: tuple[str, ...],
    value_principle_refs: tuple[str, ...],
    forbidden_promotions: tuple[str, ...],
) -> str:
    return recompute_stage1_identity(
        EmlisSubjectiveClaim(
            schema_version=CMEE_STAGE1_RESPONSE_SCHEMA_VERSION,
            subjective_claim_id="",
            parent_duty_ref=parent_duty_ref,
            speaker_owner="EMLIS",
            claim_domain="EMLIS_SUBJECTIVE_RESPONSE",
            subjective_mode=proposition.subjective_mode,
            asserted_subjective_proposition=proposition,
            basis_observation_contribution_refs=contribution_refs,
            basis_semantic_refs=semantic_refs,
            source_reception_act_refs=act_refs,
            value_principle_refs=value_principle_refs,
            user_fact_effect=0,
            forbidden_promotions=forbidden_promotions,
            subjective_responsibility_refs=responsibility_refs,
            selected_subjective_opportunity_key=opportunity_key,
        )
    )


def _normal_subjective_coalescence_key(
    claim: ProjectedSubjectiveClaim,
    *,
    responsibility_by_ref: Mapping[str, SubjectiveResponsibilityRow],
    basis_by_ref: Mapping[str, SubjectiveBasisBinding],
    qualifier_by_ref: Mapping[str, SourceQualifierBinding],
) -> Optional[tuple[Any, ...]]:
    """Match typed proposition semantics while excluding provenance rows."""

    if len(claim.subjective_responsibility_refs) != 1:
        return None
    responsibility = responsibility_by_ref.get(
        claim.subjective_responsibility_refs[0]
    )
    proposition = claim.asserted_subjective_proposition

    def binding_semantics(
        refs: tuple[str, ...],
    ) -> Optional[tuple[str, ...]]:
        rows = tuple(basis_by_ref.get(ref) for ref in refs)
        if any(row is None for row in rows):
            return None
        return tuple(
            dict.fromkeys(
                row.semantic_ref
                for row in rows
                if row is not None
            )
        )

    content: Any
    if type(proposition.appraisal_content) is EmlisAppraisalContent:
        appraisal = proposition.appraisal_content
        appraised_semantics = binding_semantics(
            appraisal.appraised_bindings
        )
        protected_semantics = binding_semantics(
            appraisal.protected_bindings
        )
        if appraised_semantics is None or protected_semantics is None:
            return None
        content = (
            "APPRAISAL",
            appraisal.dimension,
            appraisal.operation,
            appraisal.focal_relation_ref,
            appraised_semantics,
            protected_semantics,
        )
    elif type(proposition.affect_content) is EmlisAffectContent:
        affect = proposition.affect_content
        elicitor_semantics = binding_semantics(affect.elicitor_bindings)
        if elicitor_semantics is None:
            return None
        content = (
            "AFFECT",
            affect.category,
            affect.intensity,
            elicitor_semantics,
        )
    elif type(proposition.relational_position) is EmlisRelationalPosition:
        position = proposition.relational_position
        target_semantics = binding_semantics(position.target_bindings)
        boundary_semantics = binding_semantics(
            position.boundary_bindings
        )
        if target_semantics is None or boundary_semantics is None:
            return None
        content = (
            "RELATIONAL_POSITION",
            position.relational_position_kind,
            position.stance_operator,
            position.commitment,
            position.closure,
            target_semantics,
            boundary_semantics,
        )
    else:
        # Policy-visible value content owns claim-specific application rows;
        # it cannot be coalesced without re-projecting that policy ledger.
        return None
    if responsibility is None or claim.value_principle_refs:
        return None
    qualifier_semantics = tuple(
        sorted(
            {
                (
                    basis_by_ref[row.basis_binding_ref].semantic_ref,
                    row.polarity,
                    row.modality,
                    row.time_scope,
                )
                for ref in proposition.source_qualifier_binding_refs
                for row in (qualifier_by_ref.get(ref),)
                if row is not None
                and row.basis_binding_ref in basis_by_ref
            }
        )
    )
    return (
        responsibility.responsibility_kind,
        proposition.content_kind,
        proposition.subjective_mode,
        proposition.subjective_operator,
        proposition.primary_target_refs,
        proposition.boundary_target_refs,
        proposition.response_object_refs,
        proposition.focal_relation_ref,
        content,
        qualifier_semantics,
        proposition.referenced_actor_refs,
        proposition.referenced_experiencer_refs,
        proposition.addressee_role,
        proposition.assertion_modality,
        proposition.epistemic_scope,
    )


def _coalesce_normal_subjective_facets(
    *,
    authority: _ProjectionCommonAuthority,
    claims: list[ProjectedSubjectiveClaim],
    responsibilities: list[SubjectiveResponsibilityRow],
    opportunities: list[SubjectiveOpportunityRow],
    basis_rows: tuple[SubjectiveBasisBinding, ...],
    qualifier_rows: tuple[SourceQualifierBinding, ...],
    reception_traces: list[ReceptionVisibleCausalTraceRow],
    policy_applications: list[PolicyApplicationRow],
) -> tuple[
    list[ProjectedSubjectiveClaim],
    list[SubjectiveOpportunityRow],
    list[ReceptionVisibleCausalTraceRow],
]:
    """Coalesce provenance variants into one typed NORMAL proposition."""

    responsibility_by_ref = {
        row.responsibility_ref: row for row in responsibilities
    }
    opportunity_by_key = {
        row.opportunity_key: row for row in opportunities
    }
    basis_by_ref = {row.binding_ref: row for row in basis_rows}
    qualifier_by_ref = {
        row.source_qualifier_binding_ref: row for row in qualifier_rows
    }
    grouped: dict[tuple[Any, ...], list[ProjectedSubjectiveClaim]] = {}
    for claim in claims:
        key = _normal_subjective_coalescence_key(
            claim,
            responsibility_by_ref=responsibility_by_ref,
            basis_by_ref=basis_by_ref,
            qualifier_by_ref=qualifier_by_ref,
        )
        stable_key = (
            ("NONCOALESCIBLE", claim.subjective_claim_id)
            if key is None
            else ("COALESCIBLE", *key)
        )
        grouped.setdefault(stable_key, []).append(claim)

    merged_claims: list[ProjectedSubjectiveClaim] = []
    merged_opportunities: list[SubjectiveOpportunityRow] = []
    projected_claim_ref_map: dict[str, str] = {}
    for group in grouped.values():
        if len(group) == 1:
            claim = group[0]
            merged_claims.append(claim)
            merged_opportunities.append(
                opportunity_by_key[claim.selected_subjective_opportunity_key]
            )
            projected_claim_ref_map[claim.subjective_claim_id] = (
                claim.subjective_claim_id
            )
            continue

        group_claim_refs = {
            claim.subjective_claim_id for claim in group
        }
        if any(
            row.affected_claim_ref in group_claim_refs
            or row.visible_claim_ref in group_claim_refs
            for row in policy_applications
        ):
            raise Stage1CompositionError(
                "MEANING_REALIZATION_CAPABILITY_GAP"
            )
        responsibility_refs = tuple(
            sorted(
                {
                    ref
                    for claim in group
                    for ref in claim.subjective_responsibility_refs
                }
            )
        )
        contribution_ref_set = {
            ref
            for responsibility_ref in responsibility_refs
            for ref in responsibility_by_ref[
                responsibility_ref
            ].owner_component_refs
        }
        contribution_refs = tuple(
            row.contribution_id
            for row in authority.observation_contribution_rows
            if row.contribution_id in contribution_ref_set
        )
        merged_basis = _selected_basis(basis_rows, contribution_refs)
        merged_basis_refs = tuple(row.binding_ref for row in merged_basis)
        merged_basis_ref_set = set(merged_basis_refs)
        semantic_refs = _unique(row.semantic_ref for row in merged_basis)
        source_qualifier_refs = tuple(
            row.source_qualifier_binding_ref
            for row in qualifier_rows
            if row.basis_binding_ref in merged_basis_ref_set
        )

        def canonical_binding_union(
            *groups: tuple[str, ...],
        ) -> tuple[str, ...]:
            selected = {ref for refs in groups for ref in refs}
            result = tuple(
                row.binding_ref
                for row in merged_basis
                if row.binding_ref in selected
            )
            if set(result) != selected:
                raise Stage1CompositionError(
                    "MEANING_REALIZATION_CAUSAL_TRACE_GAP"
                )
            return result

        template = group[0]
        template_proposition = template.asserted_subjective_proposition
        if (
            set(semantic_refs)
            != set(template_proposition.response_object_refs)
            or any(
                claim.asserted_subjective_proposition.response_object_refs
                != template_proposition.response_object_refs
                for claim in group
            )
        ):
            raise Stage1CompositionError(
                "MEANING_REALIZATION_CAUSAL_TRACE_GAP"
            )
        appraisal_content = template_proposition.appraisal_content
        affect_content = template_proposition.affect_content
        relational_position = template_proposition.relational_position
        if appraisal_content is not None:
            appraisal_content = replace(
                appraisal_content,
                appraised_bindings=canonical_binding_union(
                    *tuple(
                        claim.asserted_subjective_proposition
                        .appraisal_content.appraised_bindings
                        for claim in group
                    )
                ),
                protected_bindings=canonical_binding_union(
                    *tuple(
                        claim.asserted_subjective_proposition
                        .appraisal_content.protected_bindings
                        for claim in group
                    )
                ),
                basis_contribution_refs=contribution_refs,
            )
        elif affect_content is not None:
            affect_content = replace(
                affect_content,
                elicitor_bindings=canonical_binding_union(
                    *tuple(
                        claim.asserted_subjective_proposition
                        .affect_content.elicitor_bindings
                        for claim in group
                    )
                ),
            )
        elif relational_position is not None:
            relational_position = replace(
                relational_position,
                target_bindings=canonical_binding_union(
                    *tuple(
                        claim.asserted_subjective_proposition
                        .relational_position.target_bindings
                        for claim in group
                    )
                ),
                boundary_bindings=canonical_binding_union(
                    *tuple(
                        claim.asserted_subjective_proposition
                        .relational_position.boundary_bindings
                        for claim in group
                    )
                ),
            )
        else:
            raise Stage1CompositionError(
                "MEANING_REALIZATION_CAPABILITY_GAP"
            )
        proposition = replace(
            template_proposition,
            target_contribution_refs=contribution_refs,
            primary_target_refs=template_proposition.primary_target_refs,
            boundary_target_refs=template_proposition.boundary_target_refs,
            response_object_refs=template_proposition.response_object_refs,
            basis_binding_refs=merged_basis_refs,
            source_qualifier_binding_refs=source_qualifier_refs,
            appraisal_content=appraisal_content,
            affect_content=affect_content,
            relational_position=relational_position,
        )
        content = (
            proposition.affect_content
            or proposition.appraisal_content
            or proposition.material_value_content
            or proposition.relational_position
        )
        specificity = (
            SubjectiveSpecificity.RELATION_BOUND_MULTI_ROLE
            if proposition.focal_relation_ref is not None
            else SubjectiveSpecificity.MULTI_ROLE
            if len(semantic_refs) > 1
            else SubjectiveSpecificity.SINGLE_ROLE
        )
        opportunity_key = project_stage1_subjective_opportunity_key(
            projection_preimage_ref=authority.projection_preimage_ref,
            responsibility_refs=responsibility_refs,
            content_kind=proposition.content_kind,
            row_ref_free_discriminated_content=content,
            specificity_key=specificity,
        )
        act_ref_set = {
            ref
            for claim in group
            for ref in claim.source_reception_act_refs
        }
        act_refs = tuple(
            row.act_ref
            for row in authority.retained_reception_act_rows
            if row.act_ref in act_ref_set
        )
        if set(act_refs) != act_ref_set:
            raise Stage1CompositionError(
                "MEANING_REALIZATION_CAUSAL_TRACE_GAP"
            )
        contributions = tuple(
            row
            for row in authority.observation_contribution_rows
            if row.contribution_id in contribution_ref_set
        )
        forbidden = stage1_subjective_forbidden_promotions(
            contributions,
            material_unknown_refs=authority.material_unknown_refs,
        )
        claim_id = _projected_claim_identity(
            proposition=proposition,
            parent_duty_ref=authority.parent_reception_duty_ref,
            responsibility_refs=responsibility_refs,
            opportunity_key=opportunity_key,
            contribution_refs=contribution_refs,
            semantic_refs=semantic_refs,
            act_refs=act_refs,
            value_principle_refs=(),
            forbidden_promotions=forbidden,
        )
        merged_claim = ProjectedSubjectiveClaim(
            CMEE_STAGE1_RESPONSE_SCHEMA_VERSION,
            claim_id,
            authority.parent_reception_duty_ref,
            CMEE_STAGE1_EMLIS_OWNER_REF,
            "EMLIS_SUBJECTIVE_RESPONSE",
            responsibility_refs,
            opportunity_key,
            proposition,
            contribution_refs,
            semantic_refs,
            act_refs,
            (),
            0,
            forbidden,
        )
        merged_claims.append(merged_claim)
        merged_opportunities.append(
            SubjectiveOpportunityRow(
                opportunity_key,
                responsibility_refs,
                proposition.content_kind,
                content,
                specificity,
            )
        )
        for claim in group:
            projected_claim_ref_map[claim.subjective_claim_id] = claim_id

    merged_traces = [
        replace(
            trace,
            projected_claim_ref=projected_claim_ref_map[
                trace.projected_claim_ref
            ],
        )
        for trace in reception_traces
    ]
    return merged_claims, merged_opportunities, merged_traces


def _finalize_subjective_meaning_plan(
    *,
    authority: _ProjectionCommonAuthority,
    branch: SubjectiveProjectionBranch,
    claims: list[ProjectedSubjectiveClaim],
    responsibilities: list[SubjectiveResponsibilityRow],
    opportunities: list[SubjectiveOpportunityRow],
    basis_rows: tuple[SubjectiveBasisBinding, ...],
    qualifier_rows: tuple[SourceQualifierBinding, ...],
    policy_basis_rows: tuple[PolicyBasisBinding, ...],
    policy_application_rows: list[PolicyApplicationRow],
    meaning_trace_rows: tuple[
        SelectedMeaningVisibleCausalTraceRow
        | LimitedMeaningVisibleCausalTraceRow,
        ...,
    ],
    reception_trace_rows: tuple[ReceptionVisibleCausalTraceRow, ...],
) -> EmlisSubjectiveMeaningPlan:
    canonical_responsibilities = tuple(
        sorted(responsibilities, key=lambda row: row.responsibility_ref)
    )
    canonical_opportunities = tuple(
        sorted(opportunities, key=lambda row: row.opportunity_key)
    )
    canonical_basis_rows = tuple(
        sorted(basis_rows, key=lambda row: row.binding_ref)
    )
    canonical_qualifier_rows = tuple(
        sorted(
            qualifier_rows,
            key=lambda row: row.source_qualifier_binding_ref,
        )
    )
    canonical_policy_basis_rows = tuple(
        sorted(policy_basis_rows, key=lambda row: row.binding_ref)
    )
    canonical_policy_application_rows = tuple(
        sorted(
            policy_application_rows,
            key=stage1_policy_application_order_key,
        )
    )
    coverage = tuple(
        ResponsibilityCoverageRow(
            row.responsibility_ref,
            row.retained_reception_act_refs,
            tuple(
                claim.subjective_claim_id
                for claim in claims
                if row.responsibility_ref
                in claim.subjective_responsibility_refs
            ),
        )
        for row in canonical_responsibilities
    )
    suppressions: tuple[SubjectiveFacetSuppressionRow, ...] = ()
    _validate_subjective_opportunity_partition(
        responsibilities=canonical_responsibilities,
        opportunities=canonical_opportunities,
        claims=claims,
        coverage=coverage,
        suppressions=suppressions,
    )
    thought_refs = tuple(
        claim.subjective_claim_id
        for claim in claims
        if claim.asserted_subjective_proposition.content_kind
        is not SubjectiveContentKind.AFFECT
    )
    tagged_ref = project_stage1_tagged_projection_ref(
        projection_branch=branch,
        projection_seal_ref=authority.projection_seal_ref,
        meaning_visible_causal_trace_rows=meaning_trace_rows,
        reception_visible_causal_trace_rows=reception_trace_rows,
    )
    return EmlisSubjectiveMeaningPlan(
        projection_preimage_ref=authority.projection_preimage_ref,
        projection_seal_ref=authority.projection_seal_ref,
        projection_branch=branch,
        tagged_projection_ref=tagged_ref,
        meaning_visible_causal_trace_rows=meaning_trace_rows,
        reception_visible_causal_trace_rows=reception_trace_rows,
        subjective_claim_rows=tuple(claims),
        thought_support_status=(
            "SUPPORTED" if thought_refs else "NOT_SUPPORTED"
        ),
        content_bearing_thought_claim_refs=thought_refs,
        retained_reception_act_refs=tuple(
            row.act_ref for row in authority.retained_reception_act_rows
        ),
        subjective_responsibility_rows=canonical_responsibilities,
        subjective_opportunity_rows=canonical_opportunities,
        responsibility_coverage_rows=coverage,
        subjective_basis_binding_rows=canonical_basis_rows,
        source_qualifier_binding_rows=canonical_qualifier_rows,
        policy_basis_binding_rows=canonical_policy_basis_rows,
        policy_application_rows=canonical_policy_application_rows,
        subjective_facet_suppression_rows=suppressions,
    )


def _validate_tagged_projection_inputs(
    inputs: SubjectiveProjectionInputs,
) -> _ProjectionCommonAuthority:
    """Close a direct branch call against the sealed post-selection carrier."""

    if type(inputs) not in {
        SelectedReadingProjectionInputs,
        LimitedProjectionInputs,
    } or type(inputs.common) is not _ProjectionCommonAuthority:
        raise Stage1CompositionError(
            "STAGE1_TAGGED_PROJECTION_INPUT_TYPE_STOP"
        )
    authority = inputs.common
    try:
        from .emlis_stage1_response import (
            validate_allowed_reception_opportunity_envelope,
        )

        validate_allowed_reception_opportunity_envelope(
            authority.allowed_reception_opportunity_envelope,
            source=authority.admitted_source,
            grounded_graph=authority.grounded_graph,
            parent_plan=authority.parent_plan,
            grounded_plan=authority.grounded_plan,
        )
    except CMEEStage1ContractError:
        raise Stage1CompositionError(
            "STAGE1_PROJECTION_PREIMAGE_CLOSURE_STOP"
        ) from None
    if (
        authority.grounded_graph_ref
        != (
            f"grounded:{getattr(authority.grounded_graph, 'graph_id', '')}"
            f"@{CMEE_GROUNDED_GRAPH_SCHEMA_VERSION}"
        )
        or authority.parent_observation_duty_ref
        != getattr(authority.parent_plan, "observation_duty_id", None)
        or authority.parent_reception_duty_ref
        != getattr(authority.parent_plan, "reception_duty_id", None)
        or tuple(
            row.act_ref for row in authority.retained_reception_act_rows
        )
        != tuple(
            getattr(authority.parent_plan, "allowed_reception_act_ids", ())
        )
    ):
        raise Stage1CompositionError(
            "STAGE1_PROJECTION_PREIMAGE_CLOSURE_STOP"
        )
    outcome = (
        authority.input_specific_meaning_structure.meaning_decision_outcome
    )
    if type(inputs) is SelectedReadingProjectionInputs:
        if (
            type(outcome) is not SelectedEmlisProvisionalReading
            or inputs.selected_reading is not outcome
            or type(inputs.reading_consequence_records) is not tuple
            or len(inputs.reading_consequence_records) != 1
            or type(inputs.reading_consequence_records[0])
            is not ReadingConsequence
            or type(inputs.sealed_reading_records) is not tuple
            or len(inputs.sealed_reading_records) != 1
            or type(inputs.sealed_reading_records[0])
            is not SealedEmlisProvisionalReading
            or type(inputs.reception_proposition_records) is not tuple
            or not 1 <= len(inputs.reception_proposition_records) <= 4
            or any(
                type(row) is not MeaningBoundReceptionProposition
                for row in inputs.reception_proposition_records
            )
            or type(inputs.reception_set_records) is not tuple
            or len(inputs.reception_set_records) != 1
            or type(inputs.reception_set_records[0])
            is not MeaningBoundReceptionSet
        ):
            raise Stage1CompositionError(
                "STAGE1_SELECTED_PROJECTION_INPUT_CLOSURE_STOP"
            )
        records = (
            inputs.reading_consequence_records,
            inputs.sealed_reading_records,
            inputs.reception_proposition_records,
            inputs.reception_set_records,
            (),
            (),
        )
    else:
        if (
            type(outcome) is not LimitedMeaningOutcome
            or inputs.limited_outcome is not outcome
            or type(inputs.bounded_reception_records) is not tuple
            or len(inputs.bounded_reception_records) != 1
            or type(inputs.bounded_reception_records[0])
            is not BoundedLimitedReception
            or type(inputs.subjective_proposition_records) is not tuple
            or len(inputs.subjective_proposition_records) != 1
            or type(inputs.subjective_proposition_records[0])
            is not SubjectivePropositionV2
        ):
            raise Stage1CompositionError(
                "STAGE1_LIMITED_PROJECTION_INPUT_CLOSURE_STOP"
            )
        records = (
            (),
            (),
            (),
            (),
            inputs.bounded_reception_records,
            inputs.subjective_proposition_records,
        )
    try:
        validate_input_specific_meaning_structure(
            authority.input_specific_meaning_structure,
            grounded_view=authority.grounded_situation_view,
            foreground_scope_derivation=(
                authority.foreground_scope_derivation
            ),
        )
        validate_stage1_post_selection_reception_records(
            input_specific_meaning_structure=(
                authority.input_specific_meaning_structure
            ),
            projection_preimage_ref=authority.projection_preimage_ref,
            reading_consequence_records=records[0],
            sealed_emlis_provisional_reading_records=records[1],
            meaning_bound_reception_proposition_records=records[2],
            meaning_bound_reception_set_records=records[3],
            bounded_limited_reception_records=records[4],
            bounded_limited_subjective_proposition_records=records[5],
            projection_seal_ref=authority.projection_seal_ref,
            retained_reception_act_rows=(
                authority.retained_reception_act_rows
            ),
            observation_contribution_rows=(
                authority.observation_contribution_rows
            ),
            interpretation_candidate_rows=(
                authority.interpretation_candidate_rows
            ),
            contribution_to_candidate_ref_map=(
                authority.contribution_to_candidate_ref_map
            ),
            qualifier_value_rows=(
                authority.qualifier_value_by_candidate_scope_axis_key
            ),
            material_unknown_refs=authority.material_unknown_refs,
        )
        expected_seal_ref = project_stage1_subjective_projection_seal_ref(
            authority.projection_preimage_ref,
            meaning_decision_outcome=outcome,
            reading_consequence_records=records[0],
            sealed_emlis_provisional_reading_records=records[1],
            meaning_bound_reception_proposition_records=records[2],
            meaning_bound_reception_set_records=records[3],
            bounded_limited_reception_records=records[4],
            bounded_limited_subjective_proposition_records=records[5],
            whole_reading_consequence_rows=(
                authority.input_specific_meaning_structure
                .whole_reading_consequence_rows
            ),
        )
        expected_preimage_ref = project_stage1_projection_preimage_ref(
            grounded_graph_ref=authority.grounded_graph_ref,
            parent_observation_duty_ref=(
                authority.parent_observation_duty_ref
            ),
            parent_reception_duty_ref=(
                authority.parent_reception_duty_ref
            ),
            interpretation_candidate_ids=tuple(
                row.candidate_id
                for row in authority.interpretation_candidate_rows
            ),
            meaning_field_id=authority.meaning_field_id,
            observation_contribution_ids=tuple(
                row.contribution_id
                for row in authority.observation_contribution_rows
            ),
            retained_reception_act_ids=tuple(
                row.act_ref for row in authority.retained_reception_act_rows
            ),
            observation_depth_class=authority.observation_depth_class,
            temperature_class=authority.temperature_class,
            reception_style_policy_ref=(
                authority.reception_style_policy_ref
            ),
            emlis_value_policy_ref=authority.emlis_value_policy_ref,
        )
    except (AttributeError, TypeError, CMEEStage1ContractError):
        raise Stage1CompositionError(
            "STAGE1_INPUT_SPECIFIC_MEANING_STRUCTURE_STOP"
        ) from None
    if expected_preimage_ref != authority.projection_preimage_ref:
        raise Stage1CompositionError(
            "STAGE1_PROJECTION_PREIMAGE_CLOSURE_STOP"
        )
    if expected_seal_ref != authority.projection_seal_ref:
        raise Stage1CompositionError(
            "STAGE1_TAGGED_PROJECTION_SEAL_CLOSURE_STOP"
        )
    return authority


def project_selected_reading_plan_candidate(
    inputs: SelectedReadingProjectionInputs,
) -> EmlisSubjectiveMeaningPlan:
    """Project the carried NORMAL reading and Reception without reselection."""

    if type(inputs) is not SelectedReadingProjectionInputs:
        raise Stage1CompositionError(
            "STAGE1_SELECTED_PROJECTION_INPUT_TYPE_STOP"
        )
    authority = _validate_tagged_projection_inputs(inputs)
    sealed_reading = inputs.sealed_reading_records[0]
    basis_rows, qualifier_rows, policy_basis_rows = (
        _projection_binding_rows(authority)
    )
    candidate_rows = tuple(
        row
        for row in authority.input_specific_meaning_structure.candidate_records
        if row.candidate_id == inputs.selected_reading.selected_candidate_ref
    )
    evidence_rows = (
        ()
        if len(candidate_rows) != 1
        else tuple(
            row
            for row in (
                authority.input_specific_meaning_structure
                .input_specificity_evidence_records
            )
            if row.candidate_ref == candidate_rows[0].candidate_id
        )
    )
    required_difference_by_ref = {
        row.difference_id: row
        for row in (
            authority.input_specific_meaning_structure.required_difference_rows
        )
    }
    evidence_difference_refs = (
        ()
        if len(evidence_rows) != 1
        else evidence_rows[0].required_difference_refs
    )
    if (
        len(candidate_rows) != 1
        or len(evidence_rows) != 1
        or len(required_difference_by_ref)
        != len(
            authority.input_specific_meaning_structure.required_difference_rows
        )
        or len(evidence_difference_refs) != len(set(evidence_difference_refs))
        or set(evidence_difference_refs) != set(required_difference_by_ref)
    ):
        raise Stage1CompositionError(
            "MEANING_REALIZATION_CAUSAL_TRACE_GAP"
        )
    candidate = candidate_rows[0]
    contribution_by_id = {
        row.contribution_id: row
        for row in authority.observation_contribution_rows
    }
    retained_by_act = {
        row.reception_act: row
        for row in authority.retained_reception_act_rows
    }
    if len(retained_by_act) != len(authority.retained_reception_act_rows):
        raise Stage1CompositionError(
            "STAGE1_RECEPTION_ACT_CLOSURE_STOP"
        )

    responsibilities: list[SubjectiveResponsibilityRow] = []
    opportunities: list[SubjectiveOpportunityRow] = []
    claims: list[ProjectedSubjectiveClaim] = []
    policy_applications: list[PolicyApplicationRow] = []
    reception_traces: list[ReceptionVisibleCausalTraceRow] = []
    for source_reception in inputs.reception_proposition_records:
        retained = retained_by_act.get(source_reception.reception_function)
        retained_contribution_refs = (
            ()
            if retained is None
            else retained.basis_contribution_refs
        )
        projection_contribution_ref_set = {
            *retained_contribution_refs,
            *candidate.basis_contribution_refs,
        }
        contribution_refs = tuple(
            row.contribution_id
            for row in authority.observation_contribution_rows
            if row.contribution_id in projection_contribution_ref_set
        )
        if (
            retained is None
            or not contribution_refs
            or not set(retained_contribution_refs).intersection(
                candidate.basis_contribution_refs
            )
            or any(ref not in contribution_by_id for ref in contribution_refs)
            or not {
                semantic_ref
                for ref in contribution_refs
                for semantic_ref in contribution_by_id[ref].semantic_refs
            }.issubset(source_reception.response_object_refs)
        ):
            raise Stage1CompositionError(
                "MEANING_REALIZATION_CAPABILITY_GAP"
            )
        contributions = tuple(
            contribution_by_id[ref] for ref in contribution_refs
        )
        own_basis = _selected_basis(basis_rows, contribution_refs)
        own_basis_refs = tuple(row.binding_ref for row in own_basis)
        own_basis_ref_set = set(own_basis_refs)
        own_qualifiers = tuple(
            row
            for row in qualifier_rows
            if row.basis_binding_ref in own_basis_ref_set
        )
        own_semantic_refs = _unique(
            row.semantic_ref for row in own_basis
        )
        operator = _normal_reception_operator(source_reception)
        value_refs: tuple[str, ...] = ()
        pending_policy_rows: tuple[
            tuple[str, str, MaterialRisk, tuple[str, ...]], ...
        ] = ()

        if source_reception.subjective_mode in {
            SubjectiveMode.ATTENTION,
            SubjectiveMode.PERSONAL_APPRAISAL,
        }:
            content_kind = SubjectiveContentKind.APPRAISAL
            content = _normal_reception_appraisal(
                proposition=source_reception,
                contributions=contributions,
                basis_rows=own_basis,
                semantic_contributions=tuple(
                    contribution_by_id[ref]
                    for ref in candidate.basis_contribution_refs
                    if ref in set(contribution_refs)
                ),
            )
            affect_content = None
            appraisal_content = content
            material_value_content = None
            relational_position = None
            focal_relation_ref = content.focal_relation_ref
        elif (
            source_reception.subjective_mode
            is SubjectiveMode.AFFECTIVE_RESPONSE
        ):
            content_kind = SubjectiveContentKind.AFFECT
            content = source_reception.optional_affect
            if (
                type(content) is not EmlisAffectContent
                or content.elicitor_bindings != own_basis_refs
            ):
                raise Stage1CompositionError(
                    "MEANING_REALIZATION_CAPABILITY_GAP"
                )
            affect_content = content
            appraisal_content = None
            material_value_content = None
            relational_position = None
            focal_relation_ref = None
        elif (
            source_reception.subjective_mode
            is SubjectiveMode.RELATIONAL_STANCE
        ):
            content_kind = SubjectiveContentKind.RELATIONAL_POSITION
            content = _normal_reception_position(
                proposition=source_reception,
                basis_rows=own_basis,
            )
            affect_content = None
            appraisal_content = None
            material_value_content = None
            relational_position = content
            focal_relation_ref = None
        elif (
            source_reception.subjective_mode
            is SubjectiveMode.VALUE_POSITION
        ):
            content_kind = SubjectiveContentKind.MATERIAL_VALUE
            value_refs = _stage1_material_visible_value_refs(
                reception_act=source_reception.reception_function,
                contributions=contributions,
            )
            relevant_policy_refs = tuple(
                row.binding_ref
                for row in policy_basis_rows
                if row.owner_kind is PolicyBasisOwnerKind.CONTRIBUTION
                and row.owner_ref in set(contribution_refs)
            )
            if not value_refs or not relevant_policy_refs:
                raise Stage1CompositionError(
                    "MEANING_REALIZATION_CAPABILITY_GAP"
                )
            pending = []
            applications = []
            for principle_ref in value_refs:
                application_ref = _ref(
                    "policy-application",
                    (
                        authority.projection_seal_ref,
                        source_reception.reception_id,
                        principle_ref,
                        relevant_policy_refs,
                        own_basis_refs,
                    ),
                )
                risk = _RISK_BY_PRINCIPLE[principle_ref]
                pending.append(
                    (
                        application_ref,
                        principle_ref,
                        risk,
                        relevant_policy_refs,
                    )
                )
                applications.append(
                    ValueApplication(
                        principle_ref,
                        risk,
                        (application_ref,),
                        relevant_policy_refs,
                        own_basis_refs,
                    )
                )
            pending_policy_rows = tuple(pending)
            content = MaterialValueContent(
                tuple(applications), own_basis_refs, ()
            )
            affect_content = None
            appraisal_content = None
            material_value_content = content
            relational_position = None
            focal_relation_ref = None
        else:
            raise Stage1CompositionError(
                "MEANING_REALIZATION_CAPABILITY_GAP"
            )

        proposition = SubjectivePropositionV2(
            CMEE_STAGE1_MEANING_BOUND_SUBJECTIVE_PROJECTION_SCHEMA_VERSION,
            content_kind,
            source_reception.subjective_mode,
            operator,
            contribution_refs,
            own_semantic_refs,
            (),
            own_semantic_refs,
            own_basis_refs,
            tuple(
                row.source_qualifier_binding_ref
                for row in own_qualifiers
            ),
            focal_relation_ref,
            affect_content,
            appraisal_content,
            material_value_content,
            relational_position,
            (),
            (),
            "USER",
            source_reception.subjective_assertion_modality,
            "REQUEST_LOCAL_EMLIS_SUBJECTIVITY",
        )
        act_refs = (retained.act_ref,)
        responsibility_ref = project_stage1_subjective_responsibility_ref(
            projection_preimage_ref=authority.projection_preimage_ref,
            responsibility_kind=source_reception.responsibility_kind,
            owner_component_refs=contribution_refs,
            retained_reception_act_refs=act_refs,
        )
        specificity = (
            SubjectiveSpecificity.RELATION_BOUND_MULTI_ROLE
            if focal_relation_ref is not None
            else SubjectiveSpecificity.MULTI_ROLE
            if len(own_semantic_refs) > 1
            else SubjectiveSpecificity.SINGLE_ROLE
        )
        opportunity_key = project_stage1_subjective_opportunity_key(
            projection_preimage_ref=authority.projection_preimage_ref,
            responsibility_refs=(responsibility_ref,),
            content_kind=content_kind,
            row_ref_free_discriminated_content=content,
            specificity_key=specificity,
        )
        forbidden = stage1_subjective_forbidden_promotions(
            contributions,
            material_unknown_refs=authority.material_unknown_refs,
        )
        claim_id = _projected_claim_identity(
            proposition=proposition,
            parent_duty_ref=authority.parent_reception_duty_ref,
            responsibility_refs=(responsibility_ref,),
            opportunity_key=opportunity_key,
            contribution_refs=contribution_refs,
            semantic_refs=own_semantic_refs,
            act_refs=act_refs,
            value_principle_refs=value_refs,
            forbidden_promotions=forbidden,
        )
        responsibilities.append(
            SubjectiveResponsibilityRow(
                responsibility_ref,
                source_reception.responsibility_kind,
                contribution_refs,
                act_refs,
            )
        )
        opportunities.append(
            SubjectiveOpportunityRow(
                opportunity_key,
                (responsibility_ref,),
                content_kind,
                content,
                specificity,
            )
        )
        claims.append(
            ProjectedSubjectiveClaim(
                CMEE_STAGE1_RESPONSE_SCHEMA_VERSION,
                claim_id,
                authority.parent_reception_duty_ref,
                CMEE_STAGE1_EMLIS_OWNER_REF,
                "EMLIS_SUBJECTIVE_RESPONSE",
                (responsibility_ref,),
                opportunity_key,
                proposition,
                contribution_refs,
                own_semantic_refs,
                act_refs,
                value_refs,
                0,
                forbidden,
            )
        )
        for (
            application_ref,
            principle_ref,
            risk,
            relevant_policy_refs,
        ) in pending_policy_rows:
            policy_applications.append(
                PolicyApplicationRow(
                    application_ref,
                    "VISIBILITY",
                    principle_ref,
                    risk,
                    relevant_policy_refs,
                    claim_id,
                    claim_id,
                )
            )
        trace_response_refs = set(source_reception.response_object_refs)
        trace_relation_refs = {
            ref
            for contribution in contributions
            for ref in contribution.relation_basis_refs
        }
        if trace_response_refs != (
            set(own_semantic_refs)
            | trace_relation_refs
            | trace_response_refs.intersection(
                candidate.basis_configuration_refs
            )
        ):
            raise Stage1CompositionError(
                "MEANING_REALIZATION_CAUSAL_TRACE_GAP"
            )
        reception_traces.append(
            ReceptionVisibleCausalTraceRow(
                branch=SubjectiveProjectionBranch.NORMAL,
                meaning_outcome_ref=inputs.selected_reading.reading_id,
                reading_consequence_ref=(
                    sealed_reading.reading_consequence_ref
                ),
                reception_record_ref=source_reception.reception_id,
                projected_claim_ref=claim_id,
                layer1_contribution_refs=contribution_refs,
                response_object_refs=source_reception.response_object_refs,
                projected_response_object_refs=own_semantic_refs,
                preserved_difference_refs=(
                    source_reception.preserved_difference_refs
                ),
            )
        )

    claims, opportunities, reception_traces = (
        _coalesce_normal_subjective_facets(
            authority=authority,
            claims=claims,
            responsibilities=responsibilities,
            opportunities=opportunities,
            basis_rows=basis_rows,
            qualifier_rows=qualifier_rows,
            reception_traces=reception_traces,
            policy_applications=policy_applications,
        )
    )

    observed_by_ref = {
        row.distinction_id: row
        for row in (
            authority.input_specific_meaning_structure.observed_distinction_rows
        )
    }
    if len(observed_by_ref) != len(
        authority.input_specific_meaning_structure.observed_distinction_rows
    ):
        raise Stage1CompositionError(
            "MEANING_REALIZATION_CAUSAL_TRACE_GAP"
        )
    meaning_trace_values: list[SelectedMeaningVisibleCausalTraceRow] = []
    for difference_ref in evidence_difference_refs:
        difference = required_difference_by_ref[difference_ref]
        observed = observed_by_ref.get(difference.observed_distinction_ref)
        if (
            observed is None
            or observed.configuration_ref
            not in set(candidate.basis_configuration_refs)
        ):
            raise Stage1CompositionError(
                "MEANING_REALIZATION_CAUSAL_TRACE_GAP"
            )
        direct_refs = tuple(
            ref
            for ref in candidate.basis_contribution_refs
            if ref in set(difference.retention_duty_refs)
        )
        component_refs = set(observed.contrasted_component_refs)
        semantic_match_refs = tuple(
            ref
            for ref in candidate.basis_contribution_refs
            if ref in contribution_by_id
            and component_refs.intersection(
                {
                    *contribution_by_id[ref].semantic_refs,
                    *contribution_by_id[ref].relation_basis_refs,
                    *(
                        binding.semantic_ref
                        for binding in contribution_by_id[ref].argument_bindings
                    ),
                }
            )
        )
        configuration_cover_refs = tuple(
            ref
            for ref in candidate.basis_contribution_refs
            if ref in contribution_by_id
            and component_refs.issubset(
                {
                    *contribution_by_id[ref].semantic_refs,
                    *(
                        binding.semantic_ref
                        for binding in contribution_by_id[ref].argument_bindings
                    ),
                }
            )
        )
        direct_cover_refs = tuple(
            ref for ref in direct_refs if ref in set(configuration_cover_refs)
        )
        layer1_refs = (
            direct_cover_refs
            if direct_cover_refs
            else configuration_cover_refs
            if configuration_cover_refs
            else direct_refs
            if direct_refs
            else semantic_match_refs
            if semantic_match_refs
            else candidate.basis_contribution_refs
            if len(candidate.basis_contribution_refs) == 1
            else ()
        )
        if not layer1_refs:
            raise Stage1CompositionError(
                "MEANING_REALIZATION_CAUSAL_TRACE_GAP"
            )
        meaning_trace_values.append(
            SelectedMeaningVisibleCausalTraceRow(
                required_difference_ref=difference_ref,
                selected_reading_ref=inputs.selected_reading.reading_id,
                configuration_ref=observed.configuration_ref,
                configuration_component_refs=(
                    observed.contrasted_component_refs
                ),
                source_qualifier_refs=observed.source_qualifier_refs,
                invariant_codes=difference.invariant_codes,
                layer1_contribution_refs=layer1_refs,
            )
        )
    meaning_traces = tuple(meaning_trace_values)
    return _finalize_subjective_meaning_plan(
        authority=authority,
        branch=SubjectiveProjectionBranch.NORMAL,
        claims=claims,
        responsibilities=responsibilities,
        opportunities=opportunities,
        basis_rows=basis_rows,
        qualifier_rows=qualifier_rows,
        policy_basis_rows=policy_basis_rows,
        policy_application_rows=policy_applications,
        meaning_trace_rows=meaning_traces,
        reception_trace_rows=tuple(reception_traces),
    )


def project_limited_subjective_plan_candidate(
    inputs: LimitedProjectionInputs,
) -> EmlisSubjectiveMeaningPlan:
    """Project the carried LIMITED proposition without a selected reading."""

    if type(inputs) is not LimitedProjectionInputs:
        raise Stage1CompositionError(
            "STAGE1_LIMITED_PROJECTION_INPUT_TYPE_STOP"
        )
    authority = _validate_tagged_projection_inputs(inputs)
    basis_rows, qualifier_rows, policy_basis_rows = (
        _projection_binding_rows(authority)
    )
    bounded_reception = inputs.bounded_reception_records[0]
    proposition = inputs.subjective_proposition_records[0]
    contribution_refs = proposition.target_contribution_refs
    contribution_by_id = {
        row.contribution_id: row
        for row in authority.observation_contribution_rows
    }
    if (
        not contribution_refs
        or any(ref not in contribution_by_id for ref in contribution_refs)
    ):
        raise Stage1CompositionError(
            "LIMITED_RECEPTION_CAPABILITY_GAP_STOP"
        )
    contributions = tuple(
        contribution_by_id[ref] for ref in contribution_refs
    )
    content = {
        SubjectiveContentKind.AFFECT: proposition.affect_content,
        SubjectiveContentKind.APPRAISAL: proposition.appraisal_content,
        SubjectiveContentKind.MATERIAL_VALUE: (
            proposition.material_value_content
        ),
        SubjectiveContentKind.RELATIONAL_POSITION: (
            proposition.relational_position
        ),
    }.get(proposition.content_kind)
    responsibility_kind = {
        SubjectiveContentKind.AFFECT: (
            SubjectiveResponsibilityKind.AFFECTIVE_RESPONSE
        ),
        SubjectiveContentKind.APPRAISAL: (
            SubjectiveResponsibilityKind.MATERIAL_APPRAISAL
        ),
        SubjectiveContentKind.MATERIAL_VALUE: (
            SubjectiveResponsibilityKind.POLICY_VISIBLE_VALUE
        ),
        SubjectiveContentKind.RELATIONAL_POSITION: (
            SubjectiveResponsibilityKind.RELATIONAL_POSITION
        ),
    }.get(proposition.content_kind)
    if content is None or responsibility_kind is None:
        raise Stage1CompositionError(
            "LIMITED_RECEPTION_CAPABILITY_GAP_STOP"
        )

    matching_act_rows = tuple(
        row
        for row in authority.retained_reception_act_rows
        for mapping in CMEE_STAGE1_RECEPTION_ACT_MAPPING_EXACT7
        if mapping.reception_act == row.reception_act
        and (
            proposition.subjective_mode,
            proposition.subjective_operator,
        )
        in mapping.eligible_mode_operator_pairs
        and len(row.basis_contribution_refs) == len(contribution_refs)
        and set(row.basis_contribution_refs) == set(contribution_refs)
        and set(row.basis_contribution_refs).issubset(
            set(bounded_reception.bound_layer1_contribution_refs)
        )
    )
    if len(matching_act_rows) != 1:
        raise Stage1CompositionError(
            "LIMITED_RECEPTION_CAPABILITY_GAP_STOP"
        )
    act_refs = (matching_act_rows[0].act_ref,)
    responsibility_ref = project_stage1_subjective_responsibility_ref(
        projection_preimage_ref=authority.projection_preimage_ref,
        responsibility_kind=responsibility_kind,
        owner_component_refs=contribution_refs,
        retained_reception_act_refs=act_refs,
    )
    specificity = (
        SubjectiveSpecificity.MULTI_ROLE
        if len(proposition.response_object_refs) > 1
        else SubjectiveSpecificity.SINGLE_ROLE
    )
    opportunity_key = project_stage1_subjective_opportunity_key(
        projection_preimage_ref=authority.projection_preimage_ref,
        responsibility_refs=(responsibility_ref,),
        content_kind=proposition.content_kind,
        row_ref_free_discriminated_content=content,
        specificity_key=specificity,
    )
    forbidden = stage1_subjective_forbidden_promotions(
        contributions,
        material_unknown_refs=authority.material_unknown_refs,
    )
    claim_id = _projected_claim_identity(
        proposition=proposition,
        parent_duty_ref=authority.parent_reception_duty_ref,
        responsibility_refs=(responsibility_ref,),
        opportunity_key=opportunity_key,
        contribution_refs=contribution_refs,
        semantic_refs=proposition.response_object_refs,
        act_refs=act_refs,
        value_principle_refs=(),
        forbidden_promotions=forbidden,
    )
    responsibilities = [
        SubjectiveResponsibilityRow(
            responsibility_ref,
            responsibility_kind,
            contribution_refs,
            act_refs,
        )
    ]
    opportunities = [
        SubjectiveOpportunityRow(
            opportunity_key,
            (responsibility_ref,),
            proposition.content_kind,
            content,
            specificity,
        )
    ]
    claims = [
        ProjectedSubjectiveClaim(
            CMEE_STAGE1_RESPONSE_SCHEMA_VERSION,
            claim_id,
            authority.parent_reception_duty_ref,
            CMEE_STAGE1_EMLIS_OWNER_REF,
            "EMLIS_SUBJECTIVE_RESPONSE",
            (responsibility_ref,),
            opportunity_key,
            proposition,
            contribution_refs,
            proposition.response_object_refs,
            act_refs,
            (),
            0,
            forbidden,
        )
    ]
    outcome_ref = limited_meaning_outcome_id(inputs.limited_outcome)
    bounded_ref = bounded_limited_reception_id(
        bounded_reception,
        limited_outcome=inputs.limited_outcome,
        subjective_proposition=proposition,
    )
    meaning_traces = tuple(
        LimitedMeaningVisibleCausalTraceRow(
            limited_outcome_ref=outcome_ref,
            source_object_ref=source_object_ref,
            layer1_contribution_refs=tuple(
                contribution_ref
                for contribution_ref in (
                    bounded_reception.bound_layer1_contribution_refs
                )
                if source_object_ref
                in {
                    *contribution_by_id[
                        contribution_ref
                    ].semantic_refs,
                    *contribution_by_id[
                        contribution_ref
                    ].relation_basis_refs,
                    *(
                        binding.semantic_ref
                        for binding in contribution_by_id[
                            contribution_ref
                        ].argument_bindings
                    ),
                }
            ),
        )
        for source_object_ref in (
            bounded_reception.foreground_source_object_refs
        )
    )
    if any(not row.layer1_contribution_refs for row in meaning_traces):
        raise Stage1CompositionError(
            "LIMITED_RECEPTION_CAPABILITY_GAP_STOP"
        )
    reception_traces = (
        ReceptionVisibleCausalTraceRow(
            branch=SubjectiveProjectionBranch.LIMITED,
            meaning_outcome_ref=outcome_ref,
            reading_consequence_ref=None,
            reception_record_ref=bounded_ref,
            projected_claim_ref=claim_id,
            layer1_contribution_refs=contribution_refs,
            response_object_refs=(
                bounded_reception.foreground_source_object_refs
            ),
            projected_response_object_refs=proposition.response_object_refs,
            preserved_difference_refs=(),
        ),
    )
    return _finalize_subjective_meaning_plan(
        authority=authority,
        branch=SubjectiveProjectionBranch.LIMITED,
        claims=claims,
        responsibilities=responsibilities,
        opportunities=opportunities,
        basis_rows=basis_rows,
        qualifier_rows=qualifier_rows,
        policy_basis_rows=policy_basis_rows,
        policy_application_rows=[],
        meaning_trace_rows=meaning_traces,
        reception_trace_rows=reception_traces,
    )


def _projection_common_authority(
    phase_A: Stage1SubjectivePlanningInputs,
) -> _ProjectionCommonAuthority:
    """Remove branch-specific records before invoking a dedicated projector."""

    return _ProjectionCommonAuthority(
        grounded_situation_view=phase_A.grounded_situation_view,
        foreground_scope_derivation=phase_A.foreground_scope_derivation,
        input_specific_meaning_structure=(
            phase_A.input_specific_meaning_structure
        ),
        admitted_source=phase_A.admitted_source,
        grounded_graph=phase_A.grounded_graph,
        grounded_plan=phase_A.grounded_plan,
        grounded_graph_ref=(
            f"grounded:{getattr(phase_A.grounded_graph, 'graph_id', '')}"
            f"@{CMEE_GROUNDED_GRAPH_SCHEMA_VERSION}"
        ),
        parent_plan=phase_A.parent_plan,
        allowed_reception_opportunity_envelope=(
            phase_A.allowed_reception_opportunity_envelope
        ),
        parent_observation_duty_ref=(
            phase_A.parent_plan.observation_duty_id
        ),
        projection_preimage_ref=phase_A.projection_preimage_ref,
        projection_seal_ref=phase_A.projection_seal_ref,
        parent_reception_duty_ref=phase_A.parent_plan.reception_duty_id,
        meaning_field_id=phase_A.meaning_field.meaning_field_id,
        observation_depth_class=phase_A.observation_depth_class,
        temperature_class=phase_A.temperature_class,
        reception_style_policy_ref=phase_A.reception_style_policy_ref,
        emlis_value_policy_ref=phase_A.emlis_value_policy_ref,
        interpretation_candidate_rows=phase_A.interpretation_candidate_rows,
        observation_contribution_rows=phase_A.observation_contribution_rows,
        retained_reception_act_rows=phase_A.retained_reception_act_rows,
        material_unknown_refs=phase_A.material_unknown_refs,
        contribution_to_candidate_ref_map=(
            phase_A.contribution_to_candidate_ref_map
        ),
        qualifier_value_by_candidate_scope_axis_key=(
            phase_A.qualifier_value_by_candidate_scope_axis_key
        ),
    )


def project_subjective_meaning_plan(
    phase_A: Stage1SubjectivePlanningInputs,
) -> EmlisSubjectiveMeaningPlan:
    """Exhaustively dispatch an already sealed NORMAL or LIMITED outcome."""

    if type(phase_A) is not Stage1SubjectivePlanningInputs:
        raise Stage1CompositionError(
            "STAGE1_COMPOSITION_PHASE_A_TYPE_STOP"
        )
    _validate_phase_A(phase_A)
    outcome = (
        phase_A.input_specific_meaning_structure.meaning_decision_outcome
    )
    common = _projection_common_authority(phase_A)
    if type(outcome) is SelectedEmlisProvisionalReading:
        return project_selected_reading_plan_candidate(
            SelectedReadingProjectionInputs(
                common=common,
                selected_reading=outcome,
                reading_consequence_records=(
                    phase_A.reading_consequence_records
                ),
                sealed_reading_records=(
                    phase_A.sealed_emlis_provisional_reading_records
                ),
                reception_proposition_records=(
                    phase_A.meaning_bound_reception_proposition_records
                ),
                reception_set_records=(
                    phase_A.meaning_bound_reception_set_records
                ),
            )
        )
    if type(outcome) is LimitedMeaningOutcome:
        return project_limited_subjective_plan_candidate(
            LimitedProjectionInputs(
                common=common,
                limited_outcome=outcome,
                bounded_reception_records=(
                    phase_A.bounded_limited_reception_records
                ),
                subjective_proposition_records=(
                    phase_A
                    .bounded_limited_subjective_proposition_records
                ),
            )
        )
    raise Stage1CompositionError(
        "STAGE1_PROJECTION_BRANCH_NOT_EXHAUSTIVE_STOP"
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


def _reciprocal_tension_relation_pair(
    contributions: tuple[PlannedObservationContribution, ...],
) -> tuple[
    PlannedObservationContribution,
    PlannedObservationContribution,
] | tuple[()]:
    """Return the sole reciprocal TENSION exact2 without collapsing it."""

    relation_rows = tuple(
        row
        for row in contributions
        if row.relation_operator is not RelationOperator.NO_RELATION_CLAIM
    )
    if (
        len(relation_rows) != 2
        or any(
            row.relation_operator is not RelationOperator.TENSION_WITH
            for row in relation_rows
        )
    ):
        return ()
    first, second = relation_rows
    first_endpoints = _ordered_relation_endpoint_refs(first)
    second_endpoints = _ordered_relation_endpoint_refs(second)
    if (
        first.contribution_id == second.contribution_id
        or first_endpoints != tuple(reversed(second_endpoints))
        or _relation_refs(first) == _relation_refs(second)
        or first.retention != second.retention
    ):
        return ()
    return first, second


def _reciprocal_tension_scalar_axes_match(
    pair: tuple[
        PlannedObservationContribution,
        PlannedObservationContribution,
    ],
    phase_B: Stage1SurfaceCompositionInputs,
) -> bool:
    """Require identical carried endpoint qualifiers across both directions."""

    if len(pair) != 2:
        return False
    axes_by_contribution: list[
        tuple[tuple[str, tuple[str, str, str]], ...]
    ] = []
    for contribution in pair:
        if len(contribution.interpretation_candidate_refs) != 1:
            return False
        candidate_ref = contribution.interpretation_candidate_refs[0]
        endpoint_axes: list[tuple[str, tuple[str, str, str]]] = []
        for binding in contribution.argument_bindings:
            rows = tuple(
                row
                for row in phase_B.qualifier_value_by_candidate_scope_axis_key
                if row.candidate_ref == candidate_ref
                and row.qualifier_scope
                is QualifierLookupScope.RELATION_SOURCE_BINDING
                and row.source_argument_role is binding.role
                and row.source_semantic_ref == binding.semantic_ref
            )
            values = tuple(
                _v2_exact1(
                    tuple(row.value for row in rows if row.axis is axis),
                    "STAGE1_QUALIFIER_CLOSURE_STOP",
                )
                for axis in ClauseScalarAxis
            )
            if len(rows) != len(ClauseScalarAxis):
                return False
            endpoint_axes.append((binding.semantic_ref, values))
        if len(endpoint_axes) != 2:
            return False
        axes_by_contribution.append(tuple(endpoint_axes))
    first_axes, second_axes = axes_by_contribution
    second_by_ref = dict(second_axes)
    return (
        len(second_by_ref) == 2
        and tuple(ref for ref, _values in first_axes)
        == tuple(reversed(tuple(ref for ref, _values in second_axes)))
        and all(second_by_ref.get(ref) == values for ref, values in first_axes)
    )


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
    reciprocal_pair = _reciprocal_tension_relation_pair(contributions)
    nonprecedence_relation_refs = {
        ref for row in reciprocal_pair for ref in _relation_refs(row)
    }
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
        if (
            projection.projection_branch
            is SubjectiveProjectionBranch.LIMITED
        ):
            # LIMITED preserves the unresolved Layer-1 object without
            # inventing a NORMAL open-position claim.  Its exact-one bounded
            # claim is therefore the only licensed subjective terminal.
            limited_terminal_claim = _v2_exact1(
                claims,
                "STAGE1_UNFINISHED_TERMINAL_CLOSURE_STOP",
            )
            terminal = (limited_terminal_claim.subjective_claim_id,)
        else:
            closure_claims: list[str] = []
            claim_owned_unresolved = tuple(
                unresolved_ref
                for unresolved_ref in unresolved
                if any(
                    unresolved_ref in _prop(claim).target_contribution_refs
                    and (
                        (
                            _prop(claim).appraisal_content is not None
                            and (
                                _prop(claim).appraisal_content.dimension
                                is AppraisalDimension.UNFINISHED_OPENNESS
                            )
                            and unresolved_ref
                            in (
                                _prop(claim).appraisal_content
                                .basis_contribution_refs
                            )
                        )
                        or (
                            _prop(claim).relational_position is not None
                            and (
                                _prop(claim).relational_position.closure
                                is RelationalClosure.OPEN
                                or (
                                    _prop(claim).relational_position
                                    .commitment
                                    is RelationalCommitment.HOLD_OPEN
                                )
                            )
                        )
                    )
                    for claim in claims
                )
            )
            for unresolved_ref in claim_owned_unresolved:
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
                        claim.subjective_claim_id
                        != closure.subjective_claim_id
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
            terminal = (
                _unique(closure_claims)
                if closure_claims
                else tuple(
                    claim.subjective_claim_id
                    for claim in claims
                    if claim.subjective_claim_id
                    not in {
                        row.predecessor_owner_ref
                        for row in dependencies
                    }
                )
            )

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
    precedence_dependencies = tuple(
        row
        for row in dependencies
        if not (
            row.dependency_kind
            is ArcDependencyKind.ADMITTED_RELATION_DIRECTION
            and row.source_relation_ref in nonprecedence_relation_refs
        )
    )
    incoming = {
        row.successor_owner_ref for row in precedence_dependencies
    }
    outgoing = {
        row.predecessor_owner_ref for row in precedence_dependencies
    }
    roots = tuple(ref for ref in all_owners if ref not in incoming)
    if not terminal:
        terminal = tuple(ref for ref in all_owners if ref not in outgoing)
    if not roots or not terminal:
        raise Stage1CompositionError("STAGE1_DISCOURSE_ARC_BOUNDARY_STOP")
    if any(
        row.predecessor_owner_ref in set(terminal)
        for row in precedence_dependencies
    ):
        raise Stage1CompositionError("STAGE1_UNFINISHED_TERMINAL_CLOSURE_STOP")

    adjacency: dict[str, set[str]] = {ref: set() for ref in all_owners}
    for row in precedence_dependencies:
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
    reciprocal_pair = _reciprocal_tension_relation_pair(contributions)
    if reciprocal_pair and not _reciprocal_tension_scalar_axes_match(
        reciprocal_pair,
        phase_B,
    ):
        raise Stage1CompositionError("STAGE1_QUALIFIER_CLOSURE_STOP")
    reciprocal_first = reciprocal_pair[0] if reciprocal_pair else None
    reciprocal_second = reciprocal_pair[1] if reciprocal_pair else None
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
        if reciprocal_second is not None and row == reciprocal_second:
            # A reciprocal TENSION pair is one symmetric visible fact.  The
            # reverse source edge remains in the frozen arc and trace, while
            # this canonical surface owner carries both contribution refs.
            continue
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
            (
                row.contribution_id,
                *(
                    (reciprocal_second.contribution_id,)
                    if reciprocal_first is not None
                    and reciprocal_second is not None
                    and row == reciprocal_first
                    else ()
                ),
                *absorbed_endpoint_owners,
            )
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
    ExpressionAssetSpec("expression:emlis-appraisal-noncollapse.v1", SentenceJob.CONSIDER_MATERIAL_MEANING, SemanticClauseKind.SUBJECTIVE_PREDICATE, "appraisal-noncollapse", ("どちらか一方だけにせず", "抱えたいです"), (PredicateValency.DYADIC_ACTOR_TARGET,)),
    ExpressionAssetSpec("expression:emlis-appraisal-change.v1", SentenceJob.CONSIDER_MATERIAL_MEANING, SemanticClauseKind.SUBJECTIVE_PREDICATE, "appraisal-change", ("今回起きた変化として", "大切に受け止めたいです"), (PredicateValency.DYADIC_ACTOR_TARGET,)),
    ExpressionAssetSpec("expression:emlis-appraisal-unfinished.v1", SentenceJob.CONSIDER_MATERIAL_MEANING, SemanticClauseKind.SUBJECTIVE_PREDICATE, "appraisal-unfinished", ("まだ結論にしなくてよいものとして", "受け止めたいです"), (PredicateValency.DYADIC_ACTOR_TARGET,)),
    ExpressionAssetSpec("expression:emlis-appraisal-agency.v1", SentenceJob.CONSIDER_MATERIAL_MEANING, SemanticClauseKind.SUBJECTIVE_PREDICATE, "appraisal-agency", ("本人が選べる向きとして", "大切に受け止めたいです"), (PredicateValency.DYADIC_ACTOR_TARGET,)),
    ExpressionAssetSpec("expression:emlis-value.v1", SentenceJob.TAKE_MATERIAL_POSITION, SemanticClauseKind.SUBJECTIVE_PREDICATE, "material-value", ("決めつけに変えず", "大切にしたいです"), (PredicateValency.DYADIC_ACTOR_TARGET, PredicateValency.TRIADIC_ACTOR_TARGET_BOUNDARY)),
    ExpressionAssetSpec("expression:emlis-position.v1", SentenceJob.TAKE_MATERIAL_POSITION, SemanticClauseKind.SUBJECTIVE_PREDICATE, "position", ("選べる向きとして", "尊重したいです"), (PredicateValency.DYADIC_ACTOR_TARGET, PredicateValency.TRIADIC_ACTOR_TARGET_BOUNDARY)),
    ExpressionAssetSpec("expression:emlis-open-position.v1", SentenceJob.STAY_WITH_UNFINISHED, SemanticClauseKind.SUBJECTIVE_PREDICATE, "open-position", ("急いで閉じず", "一緒に置いていたいです"), (PredicateValency.DYADIC_ACTOR_TARGET, PredicateValency.TRIADIC_ACTOR_TARGET_BOUNDARY)),
    ExpressionAssetSpec(
        "expression:emlis-appraisal-material-current-burden.v1",
        SentenceJob.CONSIDER_MATERIAL_MEANING,
        SemanticClauseKind.SUBJECTIVE_PREDICATE,
        "appraisal-material",
        ("具体的な負担の重みを軽く扱わずに", "受け止めたいです"),
        (PredicateValency.DYADIC_ACTOR_TARGET,),
        reception_projection_branch=SubjectiveProjectionBranch.NORMAL,
        reception_act_refs=("stay_with_current_burden",),
        reception_content_kind=SubjectiveContentKind.APPRAISAL,
        reception_subjective_mode=SubjectiveMode.ATTENTION,
        reception_subjective_operator=SubjectiveOperator.ATTEND_TO,
        reception_semantic_operators=(SemanticOperator.PRESENT_BURDEN,),
        reception_appraisal_dimension=AppraisalDimension.MATERIAL_WEIGHT,
        reception_appraisal_operation=AppraisalOperation.RECEIVE_AS_MATERIAL,
    ),
    ExpressionAssetSpec(
        "expression:emlis-appraisal-bounded-change.v1",
        SentenceJob.CONSIDER_MATERIAL_MEANING,
        SemanticClauseKind.SUBJECTIVE_PREDICATE,
        "appraisal-change",
        ("ここで示された変化をほかの場面まで広げずに", "見届けたいです"),
        (PredicateValency.DYADIC_ACTOR_TARGET,),
        reception_projection_branch=SubjectiveProjectionBranch.NORMAL,
        reception_act_refs=("recognize_lived_change",),
        reception_content_kind=SubjectiveContentKind.APPRAISAL,
        reception_subjective_mode=SubjectiveMode.ATTENTION,
        reception_subjective_operator=SubjectiveOperator.ATTEND_TO,
        reception_semantic_operators=(SemanticOperator.PRESENT_CHANGE,),
        reception_appraisal_dimension=AppraisalDimension.BOUNDED_CHANGE,
        reception_appraisal_operation=AppraisalOperation.RECOGNIZE_AS_BOUNDED,
    ),
    ExpressionAssetSpec(
        "expression:emlis-appraisal-retained-direction.v1",
        SentenceJob.CONSIDER_MATERIAL_MEANING,
        SemanticClauseKind.SUBJECTIVE_PREDICATE,
        "appraisal-agency",
        ("選べる向きを固定せずに", "尊重したいです"),
        (PredicateValency.DYADIC_ACTOR_TARGET,),
        reception_projection_branch=SubjectiveProjectionBranch.NORMAL,
        reception_act_refs=("protect_retained_intention",),
        reception_content_kind=SubjectiveContentKind.APPRAISAL,
        reception_subjective_mode=SubjectiveMode.ATTENTION,
        reception_subjective_operator=SubjectiveOperator.ATTEND_TO,
        reception_semantic_operators=(SemanticOperator.PRESENT_DIRECTION,),
        reception_appraisal_dimension=AppraisalDimension.AGENCY_BOUNDARY,
        reception_appraisal_operation=AppraisalOperation.RESPECT_CHOICE,
    ),
    ExpressionAssetSpec(
        "expression:emlis-position-help-seeking.v1",
        SentenceJob.TAKE_MATERIAL_POSITION,
        SemanticClauseKind.SUBJECTIVE_PREDICATE,
        "position",
        ("助けを求める向きから離れずに", "見守りたいです"),
        (PredicateValency.DYADIC_ACTOR_TARGET,),
        reception_projection_branch=SubjectiveProjectionBranch.LIMITED,
        reception_act_refs=("hold_help_seeking",),
        reception_content_kind=SubjectiveContentKind.RELATIONAL_POSITION,
        reception_subjective_mode=SubjectiveMode.RELATIONAL_STANCE,
        reception_subjective_operator=SubjectiveOperator.TAKE_RELATIONAL_STANCE,
        reception_semantic_operators=(SemanticOperator.PRESENT_DIRECTION,),
        reception_relational_position_kind=RelationalPositionKind.STANCE,
        reception_stance_operator=StanceOperator.STAY_WITH_SPECIFIC_OBJECT,
        reception_relational_commitment=RelationalCommitment.STAY_WITH,
        reception_relational_closure=RelationalClosure.NONE,
    ),
    ExpressionAssetSpec(
        "expression:emlis-position-burden-direction-pair.v1",
        SentenceJob.TAKE_MATERIAL_POSITION,
        SemanticClauseKind.SUBJECTIVE_PREDICATE,
        "position",
        ("負担と残る向きのどちらか一方だけに縮めずに", "守りたいです"),
        (PredicateValency.DYADIC_ACTOR_TARGET,),
        reception_projection_branch=SubjectiveProjectionBranch.LIMITED,
        reception_act_refs=("protect_retained_intention",),
        reception_content_kind=SubjectiveContentKind.RELATIONAL_POSITION,
        reception_subjective_mode=SubjectiveMode.RELATIONAL_STANCE,
        reception_subjective_operator=SubjectiveOperator.TAKE_RELATIONAL_STANCE,
        reception_semantic_operators=(
            SemanticOperator.PRESENT_BURDEN,
            SemanticOperator.PRESENT_DIRECTION,
        ),
        reception_relational_position_kind=RelationalPositionKind.STANCE,
        reception_stance_operator=StanceOperator.STAY_WITH_SPECIFIC_OBJECT,
        reception_relational_commitment=RelationalCommitment.STAY_WITH,
        reception_relational_closure=RelationalClosure.NONE,
    ),
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
    ScalarMorphologyAssetSpec("scalar:polarity:positive:unmarked.v1", ClauseScalarAxis.POLARITY, ("positive",), ScalarSurfaceRealizationMode.UNMARKED_DEFAULT, None, ()),
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
    surface_range_rows = tuple(
        code
        for code in getattr(frame, "attribute_codes", ())
        if isinstance(code, str) and code.startswith("surface_scalar_range:")
    )
    surface_source_rows = tuple(
        code
        for code in getattr(frame, "attribute_codes", ())
        if isinstance(code, str) and code.startswith("surface_scalar_source:")
    )
    fragment_range_rows = tuple(
        code
        for code in getattr(frame, "attribute_codes", ())
        if isinstance(code, str)
        and code.startswith("source_fragment_scalar_range:")
    )
    fragment_source_rows = tuple(
        code
        for code in getattr(frame, "attribute_codes", ())
        if isinstance(code, str)
        and code.startswith("source_fragment_scalar_source:")
    )
    if not surface_range_rows and not fragment_range_rows:
        if surface_source_rows or fragment_source_rows:
            raise Stage1CompositionError("STAGE1_SOURCE_SCALAR_RANGE_STOP")
        return None
    if surface_range_rows:
        range_rows = surface_range_rows
        source_rows = surface_source_rows
        expected_source_row = "surface_scalar_source:normalized_raw_text"
        foreign_rows = (*fragment_range_rows, *fragment_source_rows)
    else:
        range_rows = fragment_range_rows
        source_rows = fragment_source_rows
        expected_source_row = (
            "source_fragment_scalar_source:normalized_raw_text"
        )
        foreign_rows = (*surface_range_rows, *surface_source_rows)
    if len(range_rows) != 1 or source_rows != (expected_source_row,) or foreign_rows:
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
        isinstance(code, str)
        and code.startswith(
            ("surface_scalar_range:", "source_fragment_scalar_range:")
        )
        for code in getattr(frame, "attribute_codes", ())
    )
    is_source_fragment = any(
        isinstance(code, str)
        and code.startswith("source_fragment_scalar_range:")
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
        if not is_source_fragment:
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
    phase_B: Stage1SurfaceCompositionInputs | None = None,
) -> ExpressionAssetSpec:
    """Select a broad sense asset, then refine only from typed Reception."""

    key = _predicate_key(duty, owner)
    base_asset = _v2_exact1(
        tuple(
            row
            for row in EXPRESSION_ASSET_REGISTRY
            if row.sentence_job is duty.sentence_job
            and row.semantic_clause_kind is plan.semantic_clause_kind
            and row.predicate_key == key
            and plan.predicate_valency in row.compatible_valencies
            and row.reception_projection_branch is None
        ),
        "STAGE1_EXPRESSION_ASSET_NONUNIQUE_STOP",
    )
    if duty.layer != "LAYER_2":
        return base_asset
    if phase_B is None:
        raise Stage1CompositionError("MEANING_REALIZATION_CAUSAL_TRACE_GAP")
    proposition = _prop(owner)
    branch = phase_B.projection.projection_branch
    trace_stop = (
        "LIMITED_RECEPTION_CAPABILITY_GAP_STOP"
        if branch is SubjectiveProjectionBranch.LIMITED
        else "MEANING_REALIZATION_CAUSAL_TRACE_GAP"
    )
    if (
        type(owner) not in {ProjectedSubjectiveClaim, EmlisSubjectiveClaim}
        or type(proposition) is not SubjectivePropositionV2
        or branch
        not in {
            SubjectiveProjectionBranch.NORMAL,
            SubjectiveProjectionBranch.LIMITED,
        }
        or tuple(owner.basis_observation_contribution_refs)
        != tuple(proposition.target_contribution_refs)
        or tuple(duty.response_object_refs)
        != tuple(proposition.response_object_refs)
    ):
        raise Stage1CompositionError(trace_stop)
    contribution_by_ref = {
        row.contribution_id: row
        for row in phase_B.projection.observation_contributions
    }
    if (
        len(contribution_by_ref)
        != len(phase_B.projection.observation_contributions)
        or any(
            ref not in contribution_by_ref
            for ref in owner.basis_observation_contribution_refs
        )
    ):
        raise Stage1CompositionError(trace_stop)
    semantic_operators = tuple(
        sorted(
            {
                contribution_by_ref[ref].semantic_operator
                for ref in owner.basis_observation_contribution_refs
            },
            key=lambda value: value.value,
        )
    )
    reception_traces = tuple(
        row
        for row in phase_B.projection.reception_visible_causal_trace_rows
        if type(row) is ReceptionVisibleCausalTraceRow
        and row.projected_claim_ref == owner.subjective_claim_id
    )
    trace_layer1_cover = _unique(
        ref
        for row in reception_traces
        for ref in row.layer1_contribution_refs
    )
    if (
        not reception_traces
        or len(reception_traces) != len(owner.source_reception_act_refs)
        or any(row.branch is not branch for row in reception_traces)
        or any(
            tuple(row.projected_response_object_refs)
            != tuple(duty.response_object_refs)
            or not row.layer1_contribution_refs
            or not set(row.layer1_contribution_refs).issubset(
                owner.basis_observation_contribution_refs
            )
            for row in reception_traces
        )
        or set(trace_layer1_cover)
        != set(owner.basis_observation_contribution_refs)
    ):
        raise Stage1CompositionError(trace_stop)
    if branch is SubjectiveProjectionBranch.NORMAL:
        reading_consequence_refs = {
            row.reading_consequence_ref for row in reception_traces
        }
        sealed_consequence_refs = {
            row.reading_consequence_ref
            for row in (
                phase_B.phase_A_authority
                .sealed_emlis_provisional_reading_records
            )
        }
        difference_refs = {
            row.required_difference_ref
            for row in (
                phase_B.phase_A_authority.input_specific_meaning_structure
                .whole_reading_consequence_rows
            )
        }
        if (
            len(reading_consequence_refs) != 1
            or None in reading_consequence_refs
            or not reading_consequence_refs.issubset(
                sealed_consequence_refs
            )
            or any(
                not row.preserved_difference_refs
                or not set(row.preserved_difference_refs).issubset(
                    difference_refs
                )
                for row in reception_traces
            )
        ):
            raise Stage1CompositionError(trace_stop)
    elif any(
        row.reading_consequence_ref is not None
        or row.preserved_difference_refs
        for row in reception_traces
    ):
        raise Stage1CompositionError(trace_stop)

    appraisal = proposition.appraisal_content
    position = proposition.relational_position
    profile_rows = tuple(
        row
        for row in EXPRESSION_ASSET_REGISTRY
        if row.sentence_job is duty.sentence_job
        and row.semantic_clause_kind is plan.semantic_clause_kind
        and row.predicate_key == key
        and plan.predicate_valency in row.compatible_valencies
        and row.reception_projection_branch is branch
        and row.reception_act_refs == owner.source_reception_act_refs
        and row.reception_content_kind is proposition.content_kind
        and row.reception_subjective_mode is proposition.subjective_mode
        and row.reception_subjective_operator
        is proposition.subjective_operator
        and row.reception_semantic_operators == semantic_operators
        and row.reception_appraisal_dimension
        is getattr(appraisal, "dimension", None)
        and row.reception_appraisal_operation
        is getattr(appraisal, "operation", None)
        and row.reception_relational_position_kind
        is getattr(position, "relational_position_kind", None)
        and row.reception_stance_operator
        is getattr(position, "stance_operator", None)
        and row.reception_relational_commitment
        is getattr(position, "commitment", None)
        and row.reception_relational_closure
        is getattr(position, "closure", None)
    )
    if len(profile_rows) > 1:
        raise Stage1CompositionError(
            "STAGE1_EXPRESSION_ASSET_NONUNIQUE_STOP"
        )
    return profile_rows[0] if profile_rows else base_asset


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


def _generic_relation_fragment_clause(
    endpoint_object: str,
    carrier: str,
    frame: Any,
) -> Optional[str]:
    """Join a typed source fragment to its role-local scalar carrier.

    The final grounding projection marks only exact source slices admitted as
    local relation endpoints.  This branch may adjust their nominalizer and
    particle, but it never chooses a relation, endpoint, or semantic scalar.
    """

    attributes = tuple(getattr(frame, "attribute_codes", ()))
    if "semantic_role:generic_relation_fragment" not in attributes:
        return None
    quoted = _quoted_source_object(endpoint_object)
    modality = str(getattr(frame, "modality", ""))
    polarity = str(getattr(frame, "polarity", ""))
    if modality == "wish" and polarity == "positive":
        continuing = carrier.endswith("今も残り")
        if quoted.endswith(("気持ち」", "願い」")):
            return "".join(
                (quoted, "が今も残り" if continuing else "があり")
            )
        return "".join(
            (
                quoted,
                "という願いが今も残り" if continuing else "という願いがあり",
            )
        )
    if (
        str(getattr(frame, "predicate_kind", "")) == "state"
        and modality == "fact"
        and polarity == "neutral"
    ):
        return "".join(
            (
                quoted,
                "があり"
                if quoted.endswith(("気持ち」", "願い」"))
                else "ということがあり",
            )
        )
    if modality == "uncertain" and carrier:
        # ``carrier`` is already the unique role-local serialization of the
        # registered modality/time/polarity axes.  Join every registered
        # combination uniformly instead of re-enumerating particular input
        # or time-scope cases here.
        if carrier == "不確かさも残り":
            # The fused carrier's ``も`` is role-local before attachment.
            # Once the source endpoint supplies ``には``, realize the
            # carrier's grammatical subject with ``が`` rather than stacking
            # two topic particles.
            return "".join((endpoint_object, "には不確かさが残り"))
        return "".join(
            (
                endpoint_object,
                "は" if carrier.startswith("今も不確かなまま") else "には",
                carrier,
            )
        )
    if (
        str(getattr(frame, "predicate_kind", "")) == "constraint"
        and modality == "possibility"
    ):
        return "".join((quoted, "という制約があり"))
    if (
        polarity in {"neutral", "positive"}
        and str(getattr(frame, "predicate_kind", ""))
        in {"action", "change", "value"}
    ):
        return (
            "".join(
                (
                    endpoint_object,
                    _relation_endpoint_particle(carrier),
                    carrier,
                )
            )
            if carrier
            else "".join((endpoint_object, "があり"))
        )
    if carrier and (
        polarity == "negative" or modality == "possibility"
    ):
        return "".join((endpoint_object, "には", carrier))
    return None


def _generic_relation_fragment_response_object(
    expression: ResponseObjectExpression,
    object_surface: str,
    owner: Any,
    phase_B: Stage1SurfaceCompositionInputs,
) -> Optional[str]:
    """Drop only a redundant nominalizer from an admitted nominal wish.

    The response-object identity, its scalar axes and its source slice are
    already fixed upstream.  This is therefore a grammatical join over the
    generic relation-fragment marker, not a lexical or case-family choice.
    """

    if (
        expression.expression_mode is not ResponseObjectExpressionMode.EXPLICIT
        or len(expression.basis_semantic_refs) != 1
    ):
        return None
    semantic_ref = expression.basis_semantic_refs[0]
    frame = _frame_for_semantic_ref(owner, semantic_ref, phase_B)
    if (
        "semantic_role:generic_relation_fragment"
        not in tuple(getattr(frame, "attribute_codes", ()))
        or str(getattr(frame, "modality", "")) != "wish"
        or str(getattr(frame, "polarity", "")) != "positive"
    ):
        return None
    quoted = _quoted_source_object(object_surface)
    return quoted if quoted.endswith(("気持ち」", "願い」")) else None


def _subjective_noncollapse_relation_owner(
    proposition: SubjectivePropositionV2,
    phase_B: Stage1SurfaceCompositionInputs,
) -> Optional[PlannedObservationContribution]:
    """Resolve one typed noncollapse owner for the proposition's exact2 refs."""

    response_refs = tuple(proposition.response_object_refs)
    if len(response_refs) != 2 or len(set(response_refs)) != 2:
        return None
    rows = tuple(
        row
        for row in phase_B.projection.observation_contributions
        if row.contribution_id in set(proposition.target_contribution_refs)
        and row.relation_operator
        in {RelationOperator.COEXISTS_WITH, RelationOperator.TENSION_WITH}
        and _ordered_relation_endpoint_refs(row) == response_refs
        and (
            proposition.content_kind
            is not SubjectiveContentKind.APPRAISAL
            or row.relation_basis_refs
            == (proposition.focal_relation_ref,)
        )
    )
    return rows[0] if len(rows) == 1 else None


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
    expression_asset = _expression_asset(duty, plan, owner, phase_B)
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
        endpoint_frames = tuple(
            _frame_for_semantic_ref(owner, ref, phase_B)
            for ref in expression.basis_semantic_refs
        )
        endpoint_objects = tuple(
            _source_expression(ref, phase_B, frame)
            for ref, frame in zip(
                expression.basis_semantic_refs,
                endpoint_frames,
                strict=True,
            )
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
            right_attributes = tuple(
                getattr(endpoint_frames[1], "attribute_codes", ())
            )
            source_visible_action_residue = bool(
                owner.semantic_operator is SemanticOperator.PRESENT_RESIDUE
                and "operator:residue" in right_attributes
                and any(
                    code.startswith("surface_scalar_range:")
                    for code in right_attributes
                )
            )
            if source_visible_action_residue:
                return "".join(
                    (
                        endpoint_objects[0],
                        "のあとにも",
                        comma,
                        _quoted_source_object(endpoint_objects[1]),
                        "という状態があります",
                        terminal,
                    )
                )
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
            generic_endpoint_flags = tuple(
                "semantic_role:generic_relation_fragment"
                in tuple(getattr(frame, "attribute_codes", ()))
                for frame in endpoint_frames
            )
            if any(generic_endpoint_flags) and not all(generic_endpoint_flags):
                raise Stage1CompositionError(
                    "STAGE1_GENERIC_RELATION_FRAGMENT_CARDINALITY_STOP"
                )

            def endpoint_clause(index: int, carrier: str) -> str:
                generic = _generic_relation_fragment_clause(
                    endpoint_objects[index],
                    carrier,
                    endpoint_frames[index],
                )
                if generic is not None:
                    return generic
                if all(generic_endpoint_flags):
                    raise Stage1CompositionError(
                        "STAGE1_GENERIC_RELATION_FRAGMENT_SCALAR_STOP"
                    )
                return "".join(
                    (
                        endpoint_objects[index],
                        (
                            "には"
                            if "が" in carrier
                            else "は"
                            if carrier
                            else "が"
                        ),
                        carrier or "あり",
                    )
                )

            endpoint_clauses = (
                endpoint_clause(0, left_carrier),
                endpoint_clause(1, right_carrier),
            )
            relation_predicate_lexemes = tuple(
                value
                for value in expression_asset.predicate_lexemes
                if not (
                    all(generic_endpoint_flags)
                    and value == "今もあり"
                    and any(
                        clause.endswith(("があり", "が残り"))
                        for clause in endpoint_clauses
                    )
                )
            )
            return "".join(
                (
                    comma.join(
                        (
                            *endpoint_clauses,
                            *relation_predicate_lexemes,
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
        proposition = _prop(owner)
        expected_response_refs = _unique(
            (
                *proposition.response_object_refs,
                *proposition.boundary_target_refs,
            )
        )
        if (
            duty.response_object_refs != expected_response_refs
            or expression.basis_semantic_refs != expected_response_refs
            or expression.relation_refs != duty.relation_refs
        ):
            raise Stage1CompositionError(
                "STAGE1_SUBJECTIVE_RESPONSE_OBJECT_CLOSURE_STOP"
            )
        generic_object_surface = _generic_relation_fragment_response_object(
            expression,
            object_surface,
            owner,
            phase_B,
        )
        if generic_object_surface is not None:
            object_surface = generic_object_surface
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
        relation_endpoint_frames = tuple(
            _frame_for_semantic_ref(owner, ref, phase_B)
            for ref in expression.basis_semantic_refs
        )
        relation_endpoint_exact2 = bool(
            len(expression.basis_semantic_refs) == 2
            and len(set(expression.basis_semantic_refs)) == 2
            and len(relation_endpoint_frames) == 2
        )
        generic_relation_exact2 = bool(
            relation_endpoint_exact2
            and all(
                "semantic_role:generic_relation_fragment"
                in tuple(getattr(frame, "attribute_codes", ()))
                for frame in relation_endpoint_frames
            )
        )
        noncollapse_relation_owner = (
            _subjective_noncollapse_relation_owner(proposition, phase_B)
            if relation_endpoint_exact2
            else None
        )
        if (
            relation_endpoint_exact2
            and proposition.content_kind is SubjectiveContentKind.APPRAISAL
            and proposition.appraisal_content is not None
            and proposition.appraisal_content.dimension
            is AppraisalDimension.RELATIONAL_NONCOLLAPSE
            and proposition.appraisal_content.operation
            is AppraisalOperation.PRESERVE_BOTH_ENDPOINTS
        ):
            if noncollapse_relation_owner is None:
                raise Stage1CompositionError(
                    "STAGE1_SUBJECTIVE_RELATION_OBJECT_CLOSURE_STOP"
                )
            left_object, right_object = tuple(
                _source_expression(ref, phase_B, frame)
                for ref, frame in zip(
                    expression.basis_semantic_refs,
                    relation_endpoint_frames,
                    strict=True,
                )
            )
            return "".join(
                (
                    emlis_subject,
                    comma if emlis_subject else "",
                    left_object,
                    "と",
                    right_object,
                    "を",
                    "どちらか一方だけにせず受け止めたいです",
                    terminal,
                )
            )
        if (
            relation_endpoint_exact2
            and proposition.content_kind
            is SubjectiveContentKind.MATERIAL_VALUE
            and proposition.material_value_content is not None
            and noncollapse_relation_owner is not None
            and {
                MaterialRisk.WISH_TO_OBLIGATION,
                MaterialRisk.REMOVE_USER_AGENCY,
            }.issubset(
                {
                    application.material_risk
                    for application in proposition.material_value_content.value_applications
                }
            )
        ):
            # The appraisal immediately before this value claim names the
            # same exact2 source endpoints.  Reuse the already-proven
            # anaphoric object when available so the policy boundary remains
            # visible without repeating both source fragments verbatim.
            value_object = object_surface
            if (
                expression.expression_mode
                is not ResponseObjectExpressionMode.ANAPHORIC
            ):
                left_object, right_object = tuple(
                    _source_expression(ref, phase_B, frame)
                    for ref, frame in zip(
                        expression.basis_semantic_refs,
                        relation_endpoint_frames,
                        strict=True,
                    )
                )
                value_object = "".join((left_object, "と", right_object))
            return "".join(
                (
                    emlis_subject,
                    comma if emlis_subject else "",
                    value_object,
                    "を",
                    "義務や決めつけに変えず",
                    comma,
                    "そのまま大切にしたいです",
                    terminal,
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
    if (
        duty.sentence_job is SentenceJob.PRESERVE_RESIDUE_OR_UNFINISHED
        and len(expression.basis_semantic_refs) == 1
    ):
        source_frame = _frame_for_semantic_ref(
            owner,
            expression.basis_semantic_refs[0],
            phase_B,
        )
        source_attributes = tuple(
            getattr(source_frame, "attribute_codes", ())
        )
        if (
            "operator:uncertainty" in source_attributes
            and "operator:unfinished" in source_attributes
            and str(getattr(source_frame, "modality", "")) == "uncertain"
            and any(
                code.startswith("surface_scalar_range:")
                for code in source_attributes
            )
        ):
            return "".join(
                (
                    object_surface,
                    particles[ClauseArgumentRole.SUBJECT],
                    comma,
                    "".join(expression_asset.predicate_lexemes),
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
    if len(unique) > 4:
        raise Stage1CompositionError("CANDIDATE_BOUND_STOP")
    return tuple(unique)


def _local_reciprocal_tension_dependencies(
    duties: Tuple[CompositionDutyView, ...],
    arc: Stage1DiscourseArcView,
) -> tuple[ArcDependencyRow, ArcDependencyRow] | tuple[()]:
    """Resolve the carried reciprocal TENSION orientation rows exact2."""

    relation_duties_by_ref: dict[str, list[CompositionDutyView]] = {}
    for duty in duties:
        if duty.sentence_job is not SentenceJob.RELATE_COEXISTING_OR_TENSION:
            continue
        for relation_ref in duty.relation_refs:
            relation_duties_by_ref.setdefault(relation_ref, []).append(duty)
    dependencies = tuple(
        row
        for row in arc.dependency_rows
        if row.dependency_kind
        is ArcDependencyKind.ADMITTED_RELATION_DIRECTION
    )
    if len(dependencies) != 2:
        return ()
    first, second = dependencies
    dependency_relation_refs = tuple(
        row.source_relation_ref for row in dependencies
    )
    matched_duties = tuple(
        tuple(relation_duties_by_ref.get(relation_ref or "", ()))
        for relation_ref in dependency_relation_refs
    )
    endpoint_refs = {
        first.predecessor_owner_ref,
        first.successor_owner_ref,
    }
    if (
        arc.admitted_relation_refs != dependency_relation_refs
        or first.source_relation_ref == second.source_relation_ref
        or (
            first.predecessor_owner_ref,
            first.successor_owner_ref,
        )
        != (
            second.successor_owner_ref,
            second.predecessor_owner_ref,
        )
        or not endpoint_refs.issubset(arc.root_owner_refs)
        or not endpoint_refs.issubset(arc.terminal_owner_refs)
    ):
        return ()
    exact2_duty_shape = bool(
        all(len(rows) == 1 for rows in matched_duties)
        and len({rows[0].duty_ref for rows in matched_duties}) == 2
        and all(
            rows[0].relation_refs == (dependency.source_relation_ref,)
            and rows[0].response_object_refs
            == (
                dependency.predecessor_owner_ref,
                dependency.successor_owner_ref,
            )
            for dependency, rows in zip(
                dependencies, matched_duties, strict=True
            )
        )
    )
    canonical_exact1_shape = bool(
        len(matched_duties[0]) == 1
        and not matched_duties[1]
        and matched_duties[0][0].relation_refs
        == (first.source_relation_ref,)
        and matched_duties[0][0].response_object_refs
        == (
            first.predecessor_owner_ref,
            first.successor_owner_ref,
        )
        and len(matched_duties[0][0].basis_projection_refs) == 2
    )
    if not (exact2_duty_shape or canonical_exact1_shape):
        return ()
    return first, second


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
    nonprecedence_dependency_refs = {
        row.arc_dependency_ref
        for row in _local_reciprocal_tension_dependencies(required, arc)
    }
    for dependency in arc.dependency_rows:
        if dependency.arc_dependency_ref in nonprecedence_dependency_refs:
            continue
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
    """Return the sole canonical topological order.

    Visible alternates may regroup this order, but never reverse independent
    source owners merely to manufacture a candidate.
    """

    duty_ref_set = set(duty_refs)
    source_index = {ref: index for index, ref in enumerate(duty_refs)}

    def project() -> Tuple[str, ...]:
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
            )[0]
            remaining.remove(selected)
            ordered.append(selected)
        return tuple(ordered)

    canonical = project()
    return _bounded_layout_dimension((canonical,))


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
    terminal_candidates = _bounded_layout_dimension(
        row.duty_ref
        for row in required
        if row.layer == "LAYER_2"
        and terminal_owner_refs.intersection(row.basis_projection_refs)
        and not successor_by_duty[row.duty_ref]
    )
    # Multiple terminal-capable claims do not form a naturalness axis.  The
    # final projection-ordered owner is the single semantic terminal; choosing
    # another solely to create a visible alternate is forbidden.
    terminal_choices = (terminal_candidates[-1],)
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


V2_CANDIDATE_AXIS_MAXIMA = (
    ("LAYOUT_GROUPING", 4),
    ("MENTION_POLICY", 2),
    ("LINK_PLACEMENT", 2),
    ("PREDICATE_HEAD", 1),
)
V2_INTERNAL_CANDIDATE_LIMIT = 16
V2_EMITTED_CANDIDATE_LIMIT = 2
LEGACY_COMPOSITION_SEAM_SYMBOL_SET_EXACT18 = (
    "_source_expression",
    "_source_scalar_finite_form",
    "_normalize_source_scalar_text",
    "_source_scalar_text",
    "_functional_surface_lexemes_by_role",
    "_functional_surface_lexemes",
    "_finite_relation_carrier",
    "_relation_endpoint_particle",
    "_generic_relation_fragment_clause",
    "_generic_relation_fragment_response_object",
    "_quoted_source_object",
    "_shared_endpoint_conjunct",
    "_new_endpoint_followup",
    "_shared_endpoint_relation_chain",
    "_shared_endpoint_relation_chain_surface",
    "_surface_for_plan",
    "_normal_form_phase_topic_speaker_connective_terminal",
    "_normal_form_phase_expression_selection_final_linearization",
)


def _v2_reverse_normalized_scalar_spans(
    raw_text: str,
) -> Tuple[str, Tuple[Tuple[int, int], ...]]:
    """Map each normalized scalar to its unique contiguous raw scalar span."""

    if type(raw_text) is not str or not raw_text:
        raise Stage1CompositionError(
            "STAGE1_SOURCE_LITERAL_SUBSPAN_UNCERTIFIED_STOP"
        )
    spans: list[Tuple[int, int]] = []
    normalized: list[str] = []
    index = 0
    saw_nonspace = False
    while index < len(raw_text):
        if raw_text[index].isspace():
            start = index
            while index < len(raw_text) and raw_text[index].isspace():
                index += 1
            if saw_nonspace and index < len(raw_text):
                normalized.append(" ")
                spans.append((start, index))
            continue
        normalized.append(raw_text[index])
        spans.append((index, index + 1))
        saw_nonspace = True
        index += 1
    normalized_text = "".join(normalized)
    if (
        not normalized_text
        or len(normalized_text) != len(spans)
    ):
        raise Stage1CompositionError(
            "STAGE1_SOURCE_LITERAL_SUBSPAN_UNCERTIFIED_STOP"
        )
    return normalized_text, tuple(spans)


def _v2_source_leaf_for_semantic_ref(
    *,
    semantic_ref: str,
    owner: Any,
    case_frame: JapaneseCaseFrameSpec,
    phase_B: Stage1SurfaceCompositionInputs,
) -> Tuple[SourceLeafToken, Optional[Tuple[str, str, int, int]]]:
    """Project one EvidenceRef-bound leaf without searching source text."""

    frame = _frame_for_semantic_ref(owner, semantic_ref, phase_B)
    anchor_ids = tuple(getattr(frame, "target_anchor_ids", ()))
    if len(anchor_ids) != 1:
        raise Stage1CompositionError(
            "STAGE1_SOURCE_LEAF_BINDING_NONUNIQUE_STOP"
        )
    evidence = _v2_exact1(
        tuple(
            row
            for row in getattr(phase_B.admitted_source, "evidence_refs", ())
            if getattr(row, "source_span_id", None) == anchor_ids[0]
        ),
        "STAGE1_SOURCE_LEAF_BINDING_NONUNIQUE_STOP",
    )
    graph_node = _v2_exact1(
        tuple(
            node
            for node in getattr(phase_B.grounded_graph, "nodes", ())
            if getattr(node, "node_id", None)
            == _semantic_ref_node_id(semantic_ref)
        ),
        "STAGE1_SOURCE_LEAF_BINDING_NONUNIQUE_STOP",
    )
    if tuple(getattr(graph_node, "evidence_ids", ())).count(
        evidence.evidence_id
    ) != 1:
        raise Stage1CompositionError(
            "STAGE1_SOURCE_LEAF_BINDING_NONUNIQUE_STOP"
        )
    envelope = getattr(phase_B.admitted_source, "envelope", None)
    raw_utf8 = getattr(envelope, "raw_utf8", None)
    envelope_ref = getattr(envelope, "envelope_id", None)
    if (
        type(raw_utf8) is not bytes
        or not envelope_ref
        or evidence.source_envelope_id != envelope_ref
        or not (
            0 <= evidence.utf8_start < evidence.utf8_end <= len(raw_utf8)
        )
    ):
        raise Stage1CompositionError(
            "STAGE1_SOURCE_LEAF_BINDING_NONUNIQUE_STOP"
        )
    evidence_literal = raw_utf8[evidence.utf8_start : evidence.utf8_end]
    try:
        evidence_text = evidence_literal.decode("utf-8", "strict")
    except UnicodeDecodeError:
        raise Stage1CompositionError(
            "STAGE1_SOURCE_LEAF_UTF8_MISMATCH_STOP"
        ) from None
    if (
        evidence.scalar_end - evidence.scalar_start != len(evidence_text)
        or evidence.scalar_start < 0
        or evidence.scalar_end <= evidence.scalar_start
    ):
        raise Stage1CompositionError(
            "STAGE1_SOURCE_LEAF_BINDING_NONUNIQUE_STOP"
        )
    normalized_text, normalized_spans = _v2_reverse_normalized_scalar_spans(
        evidence_text
    )
    scalar_range = _surface_scalar_range(frame, len(normalized_text))
    raw_graph_value = getattr(graph_node, "value", "")
    try:
        graph_value, _graph_value_spans = (
            _v2_reverse_normalized_scalar_spans(raw_graph_value)
        )
    except Stage1CompositionError:
        graph_value = ""
    if (
        scalar_range is None
        and case_frame.complement_rule_ref in {"C03", "C04", "C05", "C06"}
    ):
        matching_starts = tuple(
            index
            for index in range(
                0,
                len(normalized_text) - len(graph_value) + 1,
            )
            if graph_value
            and normalized_text.startswith(graph_value, index)
        )
        if len(matching_starts) == 1:
            graph_start = matching_starts[0]
            graph_end = graph_start + len(graph_value)
            if (graph_start, graph_end) != (0, len(normalized_text)):
                scalar_range = (graph_start, graph_end)
    certified_binding: Optional[Tuple[str, str, int, int]] = None
    if scalar_range is None:
        extent = SourceLeafExtent.FULL_EVIDENCE_LITERAL
        raw_scalar_start, raw_scalar_end = 0, len(evidence_text)
        utf8_start, utf8_end = evidence.utf8_start, evidence.utf8_end
    else:
        normalized_start, normalized_end = scalar_range
        if not (0 <= normalized_start < normalized_end <= len(normalized_spans)):
            raise Stage1CompositionError(
                "STAGE1_SOURCE_LITERAL_SUBSPAN_UNCERTIFIED_STOP"
            )
        raw_scalar_start = normalized_spans[normalized_start][0]
        raw_scalar_end = normalized_spans[normalized_end - 1][1]
        prefix_bytes = evidence_text[:raw_scalar_start].encode("utf-8")
        payload_bytes = evidence_text[
            raw_scalar_start:raw_scalar_end
        ].encode("utf-8")
        utf8_start = evidence.utf8_start + len(prefix_bytes)
        utf8_end = utf8_start + len(payload_bytes)
        if (
            raw_utf8[utf8_start:utf8_end] != payload_bytes
            or _v2_reverse_normalized_scalar_spans(
                evidence_text[raw_scalar_start:raw_scalar_end]
            )[0]
            != normalized_text[normalized_start:normalized_end]
        ):
            raise Stage1CompositionError(
                "STAGE1_SOURCE_LITERAL_SUBSPAN_UNCERTIFIED_STOP"
            )
        extent = SourceLeafExtent.CERTIFIED_LITERAL_SUBSPAN
        certified_binding = (
            evidence.evidence_id,
            envelope_ref,
            utf8_start,
            utf8_end,
        )
    payload_utf8 = raw_utf8[utf8_start:utf8_end]
    payload_text = payload_utf8.decode("utf-8", "strict")
    quote_topology, outer_terminal_positions = _v2_source_quote_witness(
        payload_text
    )
    line_break_shape = _v2_source_line_break_witness(payload_text)
    terminal_class = dict(_V2_SOURCE_TERMINAL_CLASS_BY_CODEPOINT).get(
        payload_text[-1], SourceFinalTerminalClass.ABSENT
    )
    sentence_shape = (
        SourceSentenceShape.MULTI_SENTENCE
        if any(
            payload_text[position + 1 :].strip()
            for position in outer_terminal_positions
            if position < len(payload_text) - 1
        )
        else SourceSentenceShape.ONE_SENTENCE
    )
    input_start = evidence.scalar_start + raw_scalar_start
    input_end = evidence.scalar_start + raw_scalar_end
    if (
        input_end - input_start != len(payload_text)
        or (
            extent is SourceLeafExtent.FULL_EVIDENCE_LITERAL
            and (input_start, input_end)
            != (evidence.scalar_start, evidence.scalar_end)
        )
    ):
        raise Stage1CompositionError(
            "STAGE1_SOURCE_LEAF_BINDING_NONUNIQUE_STOP"
        )
    derivation = SurfaceDerivation(
        derivation_kind=SurfaceDerivationKind.LITERAL_SUBSPAN,
        source_or_claim_refs=(semantic_ref,),
        emlis_owner_ref=None,
        relation_or_clause_plan_refs=(),
        qualifier_refs=(),
        response_object_expression_ref=None,
        antecedent_unit_ref=None,
        participant_role_ref=None,
        evidence_refs=(evidence.evidence_id,),
        rule_ref="rule:literal-subspan@cocolon.cmee.surface.v2",
        input_scalar_ranges=((input_start, input_end),),
    )
    leaf = SourceLeafToken(
        leaf_ref=_ref(
            "source-leaf-v2",
            (
                semantic_ref,
                envelope_ref,
                evidence.evidence_id,
                extent,
                utf8_start,
                utf8_end,
            ),
        ),
        semantic_ref=semantic_ref,
        source_envelope_ref=envelope_ref,
        evidence_ref=evidence.evidence_id,
        extent=extent,
        raw_utf8_start=utf8_start,
        raw_utf8_end=utf8_end,
        payload_utf8=payload_utf8,
        sentence_shape=sentence_shape,
        final_terminal_class=terminal_class,
        quote_topology=quote_topology,
        line_break_shape=line_break_shape,
        derivation=derivation,
    )
    return leaf, certified_binding


def _v2_frame_for_duty(
    duty: CompositionDutyView,
    owner: Any,
    source_refs: Tuple[str, ...],
    phase_B: Stage1SurfaceCompositionInputs,
) -> JapaneseCaseFrameSpec:
    semantic_kind = (
        SemanticClauseKind.SUBJECTIVE_PREDICATE
        if duty.layer == "LAYER_2"
        else SemanticClauseKind.ADMITTED_RELATION
        if duty.relation_refs
        else SemanticClauseKind.GROUNDED_PREDICATE
    )
    semantic_sense = _predicate_key(duty, owner)
    sense = _v2_exact1(
        tuple(
            row
            for row in V2_PREDICATE_SENSE_REGISTRY
            if row.sentence_job == duty.sentence_job.value
            and row.semantic_clause_kind == semantic_kind.value
            and row.semantic_sense == semantic_sense
        ),
        "STAGE1_JAPANESE_CASE_FRAME_NONUNIQUE_STOP",
    )
    licensed_frames = tuple(
        row
        for row in V2_JAPANESE_CASE_FRAME_REGISTRY
        if row.sense_ref == sense.sense_id
        and row.frame_id in sense.frame_license_refs
    )
    if semantic_kind is SemanticClauseKind.ADMITTED_RELATION:
        relation = getattr(owner, "relation_operator", None)
        reciprocal_pair = _reciprocal_tension_relation_pair(
            _contributions(phase_B.projection)
        )
        preferred_frame_ref: Optional[str] = None
        if relation is RelationOperator.TENSION_WITH:
            if reciprocal_pair:
                if not _reciprocal_tension_scalar_axes_match(
                    reciprocal_pair, phase_B
                ):
                    raise Stage1CompositionError(
                        "STAGE1_QUALIFIER_CLOSURE_STOP"
                    )
                owner_positions = tuple(
                    index
                    for index, row in enumerate(reciprocal_pair)
                    if row == owner
                )
                if len(owner_positions) != 1:
                    raise Stage1CompositionError(
                        "STAGE1_JAPANESE_CASE_FRAME_NONUNIQUE_STOP"
                    )
                preferred_frame_ref = (
                    "F06" if owner_positions[0] == 0 else "F24"
                )
            else:
                preferred_frame_ref = "F06"
        frame = _v2_exact1(
            tuple(
                row
                for row in licensed_frames
                if _v2_relation_operator_for_frame(row.frame_id) is relation
                and (
                    preferred_frame_ref is None
                    or row.frame_id == preferred_frame_ref
                )
            ),
            "STAGE1_JAPANESE_CASE_FRAME_NONUNIQUE_STOP",
        )
    elif len(licensed_frames) == 1:
        frame = licensed_frames[0]
    else:
        boundary_refs = tuple(
            getattr(_prop(owner), "boundary_target_refs", ())
        )
        if sense.sense_id == "S16" and not boundary_refs:
            complement_ref = "C08" if len(source_refs) == 2 else "C06"
            frame = _v2_exact1(
                tuple(
                    row
                    for row in licensed_frames
                    if row.complement_rule_ref == complement_ref
                ),
                "STAGE1_JAPANESE_CASE_FRAME_NONUNIQUE_STOP",
            )
        else:
            required_slot_count = 3 if boundary_refs else 2
            frame = _v2_exact1(
                tuple(
                    row
                    for row in licensed_frames
                    if len(row.slot_roles) == required_slot_count
                ),
                "STAGE1_JAPANESE_CASE_FRAME_NONUNIQUE_STOP",
            )
    morphology = _v2_exact1(
        tuple(
            row
            for row in V2_MATRIX_MORPHOLOGY_PARADIGM_REGISTRY
            if row.frame_ref == frame.frame_id
            and row.morphology_id == frame.morphology_ref
        ),
        "STAGE1_MATRIX_MORPHOLOGY_NONUNIQUE_STOP",
    )
    content_kind, predication_kind = _v2_subjective_kind_for_sense(
        sense.sense_id
    )
    speaker_requirement = (
        SpeakerRequirement.EMLIS_ZERO_ALLOWED
        if semantic_kind is SemanticClauseKind.SUBJECTIVE_PREDICATE
        and phase_B.section_speaker_owner_ref == CMEE_STAGE1_EMLIS_OWNER_REF
        else SpeakerRequirement.EMLIS_EXPLICIT_REQUIRED
        if semantic_kind is SemanticClauseKind.SUBJECTIVE_PREDICATE
        else SpeakerRequirement.GROUNDED_NARRATION
    )
    intent = JapaneseCaseFrameKey(
        sentence_job=duty.sentence_job,
        semantic_clause_kind=semantic_kind,
        subjective_content_kind=content_kind,
        subjective_predication_kind=predication_kind,
        subjective_semantic_sense=(
            semantic_sense
            if semantic_kind is SemanticClauseKind.SUBJECTIVE_PREDICATE
            else None
        ),
        grounded_predicate_kind=(
            semantic_sense
            if semantic_kind is SemanticClauseKind.GROUNDED_PREDICATE
            else None
        ),
        required_argument_roles=tuple(
            ClauseArgumentRole(role) for role in frame.slot_roles
        ),
        admitted_relation_operator=_v2_relation_operator_for_frame(
            frame.frame_id
        ),
        polarity=morphology.polarity,
        modality=morphology.modal,
        time_scope=morphology.aspect_time,
        speaker_requirement=speaker_requirement,
        zero_subject_eligibility=frame.zero_policy,
        complement_requirement=frame.complement_rule_ref,
    )
    selected = select_case_frame(intent)
    if selected != frame or not source_refs:
        raise Stage1CompositionError(
            "STAGE1_JAPANESE_CASE_FRAME_NONUNIQUE_STOP"
        )
    return selected


def _v2_c08_claim_configuration_pair(
    owner: Any,
    proposition: SubjectivePropositionV2,
    phase_B: Stage1SurfaceCompositionInputs,
) -> Tuple[str, str]:
    """Resolve C08's local ordered pair from the claim's causal lineage."""

    stop = "STAGE1_SOURCE_PAIR_CARDINALITY_STOP"
    claim_ref = getattr(owner, "subjective_claim_id", None)
    claim_basis_refs = tuple(
        getattr(owner, "basis_observation_contribution_refs", ())
    )
    source_reception_act_refs = tuple(
        getattr(owner, "source_reception_act_refs", ())
    )
    projected_response_refs = tuple(proposition.response_object_refs)
    if (
        not claim_ref
        or not claim_basis_refs
        or len(claim_basis_refs) != len(set(claim_basis_refs))
        or not source_reception_act_refs
        or len(source_reception_act_refs)
        != len(set(source_reception_act_refs))
        or len(projected_response_refs) <= 2
        or len(projected_response_refs) != len(set(projected_response_refs))
    ):
        raise Stage1CompositionError(stop)

    reception_traces = tuple(
        row
        for row in phase_B.projection.reception_visible_causal_trace_rows
        if type(row) is ReceptionVisibleCausalTraceRow
        and row.projected_claim_ref == claim_ref
    )
    trace_layer1_cover = (
        reception_traces[0].layer1_contribution_refs
        if len(reception_traces) == 1
        else _unique(
            ref
            for row in reception_traces
            for ref in row.layer1_contribution_refs
        )
    )
    if (
        len(reception_traces) != len(source_reception_act_refs)
        or len(
            {row.reception_record_ref for row in reception_traces}
        )
        != len(reception_traces)
        or trace_layer1_cover != claim_basis_refs
        or any(
            not row.layer1_contribution_refs
            or len(row.layer1_contribution_refs)
            != len(set(row.layer1_contribution_refs))
            or not set(row.layer1_contribution_refs).issubset(
                claim_basis_refs
            )
            or tuple(row.projected_response_object_refs)
            != projected_response_refs
            or not row.preserved_difference_refs
            for row in reception_traces
        )
    ):
        raise Stage1CompositionError(stop)

    reception_records: list[MeaningBoundReceptionProposition] = []
    retained_rows = []
    matching_configuration_rows: list[
        SelectedMeaningVisibleCausalTraceRow
    ] = []
    relational_configuration_by_ref = {
        row.configuration_id: row
        for row in (
            phase_B.phase_A_authority.input_specific_meaning_structure
            .configurations
        )
        if type(row) is RelationalConfiguration
        and len(row.endpoint_component_refs) == 2
        and len(row.endpoint_component_refs)
        == len(set(row.endpoint_component_refs))
    }
    if not relational_configuration_by_ref:
        raise Stage1CompositionError(stop)

    for source_reception_act_ref, reception_trace in zip(
        source_reception_act_refs,
        reception_traces,
        strict=True,
    ):
        reception_record = _v2_exact1(
            tuple(
                row
                for row in (
                    phase_B.phase_A_authority
                    .meaning_bound_reception_proposition_records
                )
                if type(row) is MeaningBoundReceptionProposition
                and row.reception_id
                == reception_trace.reception_record_ref
                and row.reception_function
                == source_reception_act_ref
            ),
            stop,
        )
        if (
            tuple(reception_record.preserved_difference_refs)
            != tuple(reception_trace.preserved_difference_refs)
            or not set(projected_response_refs).issubset(
                reception_record.response_object_refs
            )
        ):
            raise Stage1CompositionError(stop)
        reception_records.append(reception_record)

        retained = _v2_exact1(
            tuple(
                row
                for row in (
                    phase_B.phase_A_authority.retained_reception_act_rows
                )
                if row.act_ref == source_reception_act_ref
            ),
            stop,
        )
        retained_basis_refs = tuple(retained.basis_contribution_refs)
        if (
            retained.reception_act != reception_record.reception_function
            or not retained_basis_refs
            or len(retained_basis_refs) != len(set(retained_basis_refs))
            or not set(retained_basis_refs).issubset(
                reception_trace.layer1_contribution_refs
            )
        ):
            raise Stage1CompositionError(stop)
        retained_rows.append(retained)

        preserved_difference_refs = set(
            reception_trace.preserved_difference_refs
        )
        local_matching_rows = tuple(
            row
            for row in phase_B.projection.meaning_visible_causal_trace_rows
            if type(row) is SelectedMeaningVisibleCausalTraceRow
            and row.required_difference_ref in preserved_difference_refs
            and row.configuration_ref in relational_configuration_by_ref
            and tuple(row.configuration_component_refs)
            == tuple(
                relational_configuration_by_ref[
                    row.configuration_ref
                ].endpoint_component_refs
            )
            and set(row.configuration_component_refs).issubset(
                projected_response_refs
            )
            and row.layer1_contribution_refs
            and len(row.layer1_contribution_refs)
            == len(set(row.layer1_contribution_refs))
            and set(row.layer1_contribution_refs).issubset(
                retained_basis_refs
            )
        )
        if not local_matching_rows:
            raise Stage1CompositionError(stop)
        matching_configuration_rows.extend(local_matching_rows)

    if (
        tuple(row.reception_function for row in reception_records)
        != source_reception_act_refs
        or len(retained_rows) != len(source_reception_act_refs)
    ):
        raise Stage1CompositionError(stop)

    configuration_signatures = tuple(
        dict.fromkeys(
            (
                row.configuration_ref,
                tuple(row.configuration_component_refs),
            )
            for row in matching_configuration_rows
        )
    )
    configuration_ref, component_refs = _v2_exact1(
        configuration_signatures,
        stop,
    )
    if (
        len(component_refs) != 2
        or len(component_refs) != len(set(component_refs))
        or not set(component_refs).issubset(projected_response_refs)
    ):
        raise Stage1CompositionError(stop)

    configuration = relational_configuration_by_ref.get(configuration_ref)
    if tuple(configuration.endpoint_component_refs) != component_refs:
        raise Stage1CompositionError(stop)

    contributions = _contributions(phase_B.projection)
    contribution_by_ref = {
        row.contribution_id: row
        for row in contributions
    }
    if (
        len(contribution_by_ref) != len(contributions)
        or any(
            ref not in contribution_by_ref
            for row in matching_configuration_rows
            for ref in row.layer1_contribution_refs
        )
    ):
        raise Stage1CompositionError(stop)
    matched_contribution_refs = _unique(
        ref
        for row in matching_configuration_rows
        if row.configuration_ref == configuration_ref
        and tuple(row.configuration_component_refs) == component_refs
        for ref in row.layer1_contribution_refs
    )
    local_contributions = tuple(
        contribution_by_ref[ref] for ref in matched_contribution_refs
    )
    local_semantic_refs = {
        semantic_ref
        for contribution in local_contributions
        for semantic_ref in (
            *contribution.semantic_refs,
            *(
                binding.semantic_ref
                for binding in contribution.argument_bindings
            ),
        )
    }
    if not set(component_refs).issubset(local_semantic_refs):
        raise Stage1CompositionError(stop)
    return component_refs


def _v2_source_refs_for_frame(
    source_refs: Tuple[str, ...],
    owner: Any,
    frame: JapaneseCaseFrameSpec,
    phase_B: Stage1SurfaceCompositionInputs,
) -> Tuple[str, ...]:
    rule = _v2_exact1(
        tuple(
            row
            for row in V2_COMPLEMENT_RULE_REGISTRY
            if row.complement_rule_id == frame.complement_rule_ref
        ),
        "STAGE1_SOURCE_COMPLEMENT_NONUNIQUE_STOP",
    )
    expected = (
        1
        if rule.cardinality is SourceLeafCardinality.EXACT1
        else 2
        if rule.cardinality is SourceLeafCardinality.ORDERED_EXACT2
        else 0
    )
    if frame.zero_policy == "EMLIS_ZERO_CONDITIONAL":
        proposition = _prop(owner)
        if frame.complement_rule_ref == "C09":
            primary_refs = tuple(proposition.primary_target_refs)
            boundary_refs = tuple(proposition.boundary_target_refs)
            if len(primary_refs) != 1 or len(boundary_refs) != 1:
                raise Stage1CompositionError(
                    "STAGE1_SOURCE_PAIR_CARDINALITY_STOP"
                )
            typed_source_refs = (primary_refs[0], boundary_refs[0])
        elif frame.complement_rule_ref == "C08":
            typed_source_refs = tuple(proposition.response_object_refs)
            if len(typed_source_refs) > 2:
                typed_source_refs = _v2_c08_claim_configuration_pair(
                    owner,
                    proposition,
                    phase_B,
                )
        else:
            typed_source_refs = tuple(proposition.primary_target_refs)
    elif _v2_relation_operator_for_frame(
        frame.frame_id
    ) is not RelationOperator.NO_RELATION_CLAIM:
        typed_source_refs = _ordered_relation_endpoint_refs(owner)
        if typed_source_refs != source_refs:
            raise Stage1CompositionError("STAGE1_RELATION_DIRECTION_STOP")
    else:
        typed_source_refs = source_refs
    if expected == 2:
        if len(typed_source_refs) != 2:
            raise Stage1CompositionError("STAGE1_SOURCE_PAIR_CARDINALITY_STOP")
        return typed_source_refs
    if expected != 1 or not typed_source_refs:
        raise Stage1CompositionError("STAGE1_SOURCE_PAIR_CARDINALITY_STOP")
    if len(typed_source_refs) != 1:
        branch = phase_B.projection.projection_branch
        if branch is SubjectiveProjectionBranch.LIMITED:
            raise Stage1CompositionError(
                "LIMITED_RECEPTION_CAPABILITY_GAP_STOP"
            )
        if branch is SubjectiveProjectionBranch.NORMAL:
            raise Stage1CompositionError(
                "MEANING_REALIZATION_CAPABILITY_GAP"
            )
        raise Stage1CompositionError("MEANING_REALIZATION_CAPABILITY_GAP")
    return typed_source_refs


def _v2_source_binding_for_duty(
    duty: CompositionDutyView,
    phase_B: Stage1SurfaceCompositionInputs,
) -> Tuple[
    Any,
    Tuple[str, ...],
    JapaneseCaseFrameSpec,
    Tuple[str, ...],
]:
    """Resolve one frame and its exact visible source cardinality once."""

    owner, projected_source_refs = _duty_semantics(duty, phase_B)
    if duty.relation_refs:
        all_source_refs = _ordered_relation_endpoint_refs(owner)
        if all_source_refs != projected_source_refs:
            raise Stage1CompositionError("STAGE1_RELATION_DIRECTION_STOP")
    elif duty.layer == "LAYER_2":
        proposition = _prop(owner)
        all_source_refs = _unique(
            (
                *tuple(proposition.primary_target_refs),
                *tuple(proposition.boundary_target_refs),
            )
        )
        if not all_source_refs or not set(projected_source_refs).issubset(
            set(all_source_refs)
        ):
            raise Stage1CompositionError(
                "STAGE1_SOURCE_BINDING_CLOSURE_STOP"
            )
    else:
        all_source_refs = projected_source_refs
    frame = _v2_frame_for_duty(duty, owner, all_source_refs, phase_B)
    source_refs = _v2_source_refs_for_frame(
        all_source_refs, owner, frame, phase_B
    )
    expected_cardinality = (
        2
        if frame.complement_rule_ref in {"C07", "C08", "C09"}
        else 1
    )
    if len(source_refs) != expected_cardinality:
        raise Stage1CompositionError("STAGE1_SOURCE_PAIR_CARDINALITY_STOP")
    return owner, all_source_refs, frame, source_refs


def _v2_reception_contribution_kinds_for_claim(
    claim_ref: str,
    phase_B: Stage1SurfaceCompositionInputs,
) -> Tuple[str, ...]:
    """Resolve the carried Reception kind without adding a parallel carrier."""

    projection = phase_B.projection
    phase_A = phase_B.phase_A_authority
    traces = tuple(
        row
        for row in projection.reception_visible_causal_trace_rows
        if row.projected_claim_ref == claim_ref
    )
    if (
        not claim_ref
        or not traces
        or any(row.branch is not projection.projection_branch for row in traces)
    ):
        raise Stage1CompositionError("MEANING_REALIZATION_CAPABILITY_GAP")
    if projection.projection_branch is SubjectiveProjectionBranch.NORMAL:
        records = tuple(
            _v2_exact1(
                tuple(
                    record
                    for record in (
                        phase_A.meaning_bound_reception_proposition_records
                    )
                    if type(record) is MeaningBoundReceptionProposition
                    and record.reception_id == trace.reception_record_ref
                ),
                "MEANING_REALIZATION_CAPABILITY_GAP",
            )
            for trace in traces
        )
    elif projection.projection_branch is SubjectiveProjectionBranch.LIMITED:
        outcome = phase_A.input_specific_meaning_structure.meaning_decision_outcome
        bounded = _v2_exact1(
            tuple(phase_A.bounded_limited_reception_records),
            "LIMITED_RECEPTION_CAPABILITY_GAP_STOP",
        )
        proposition = _v2_exact1(
            tuple(phase_A.bounded_limited_subjective_proposition_records),
            "LIMITED_RECEPTION_CAPABILITY_GAP_STOP",
        )
        if (
            len(traces) != 1
            or type(outcome) is not LimitedMeaningOutcome
            or type(bounded) is not BoundedLimitedReception
            or type(proposition) is not SubjectivePropositionV2
            or traces[0].reception_record_ref
            != bounded_limited_reception_id(
                bounded,
                limited_outcome=outcome,
                subjective_proposition=proposition,
            )
        ):
            raise Stage1CompositionError(
                "LIMITED_RECEPTION_CAPABILITY_GAP_STOP"
            )
        records = (bounded,)
    else:
        raise Stage1CompositionError("MEANING_REALIZATION_CAPABILITY_GAP")
    kinds = tuple(record.contribution_kind for record in records)
    if (
        not kinds
        or any(
            kind
            not in {
                "AFFIRMATIVE_RECEPTION_CONTRIBUTION",
                "BOUNDED_COUNTERPOSITION",
            }
            for kind in kinds
        )
    ):
        raise Stage1CompositionError("MEANING_REALIZATION_CAPABILITY_GAP")
    return kinds


def _v2_validate_layer2_reception_morphology(
    duty: CompositionDutyView,
    phase_B: Stage1SurfaceCompositionInputs,
    morphology: PredicateMorphologyPlan,
) -> None:
    """Keep carried affirmative/counterposition type and morphology aligned."""

    if duty.layer != "LAYER_2":
        return
    if (
        type(morphology) is not PredicateMorphologyPlan
        or len(duty.basis_projection_refs) != 1
    ):
        raise Stage1CompositionError("MEANING_REALIZATION_CAPABILITY_GAP")
    kinds = _v2_reception_contribution_kinds_for_claim(
        duty.basis_projection_refs[0],
        phase_B,
    )
    kind_set = set(kinds)
    if kind_set == {"AFFIRMATIVE_RECEPTION_CONTRIBUTION"}:
        if (
            morphology.polarity != "POSITIVE"
            or morphology.modal == "EMLIS_BOUNDED_REFUSAL"
        ):
            raise Stage1CompositionError(
                "MEANING_REALIZATION_CAPABILITY_GAP"
            )
        return
    if kind_set == {"BOUNDED_COUNTERPOSITION"}:
        if (
            morphology.polarity != "NEGATIVE"
            or morphology.modal != "EMLIS_BOUNDED_REFUSAL"
        ):
            raise Stage1CompositionError(
                "MEANING_REALIZATION_CAPABILITY_GAP"
            )
        return
    raise Stage1CompositionError("MEANING_REALIZATION_CAPABILITY_GAP")


def _normal_form_repair_defect_tuple_strictly_decreases(
    before: Tuple[int, int, int, int],
    after: Tuple[int, int, int, int],
) -> bool:
    return (
        type(before) is tuple
        and type(after) is tuple
        and len(before) == len(after) == 4
        and all(type(value) is int and value >= 0 for value in (*before, *after))
        and all(later <= earlier for earlier, later in zip(before, after, strict=True))
        and after < before
    )


def _v2_normal_form_phase_dependency_preserving_merge_split(
    seed: LayoutPreferenceSeed,
    duty_by_ref: dict[str, CompositionDutyView],
) -> Tuple[
    Tuple[DutyGroupRow, ...],
    Tuple[NormalFormRepairTraceRow, ...],
    Tuple[int, int, int, int],
]:
    groups = _normal_form_phase_seed_constrained_merge_split(
        seed, duty_by_ref
    )
    def licensed_shared_relation_merge(group: DutyGroupRow) -> bool:
        if len(group.ordered_duty_refs) != 2:
            return False
        first, second = tuple(
            duty_by_ref[ref] for ref in group.ordered_duty_refs
        )
        return (
            first.layer == second.layer == "LAYER_1"
            and len(first.relation_refs) == len(second.relation_refs) == 1
            and len(
                set(first.response_object_refs).intersection(
                    second.response_object_refs
                )
            )
            == 1
        )

    def ordered_response_target_merge(
        group: DutyGroupRow,
    ) -> Optional[DutyGroupRow]:
        if len(group.ordered_duty_refs) != 2:
            return None
        first, second = tuple(
            duty_by_ref[ref] for ref in group.ordered_duty_refs
        )
        paired_refs = (*first.response_object_refs, *second.response_object_refs)
        consumers = tuple(
            duty
            for duty in duty_by_ref.values()
            if duty.layer == "LAYER_2"
            and duty.retention == "REQUIRED"
            and not duty.relation_refs
            and len(duty.response_object_refs) == 2
            and len(set(duty.response_object_refs)) == 2
            and set(duty.response_object_refs) == set(paired_refs)
        )
        if not (
            first.layer == second.layer == "LAYER_1"
            and not first.relation_refs
            and not second.relation_refs
            and len(first.response_object_refs)
            == len(second.response_object_refs)
            == 1
            and len(set(paired_refs)) == 2
            and len(consumers) == 1
        ):
            return None
        duty_ref_by_response_ref = {
            first.response_object_refs[0]: first.duty_ref,
            second.response_object_refs[0]: second.duty_ref,
        }
        return DutyGroupRow(
            tuple(
                duty_ref_by_response_ref[response_ref]
                for response_ref in consumers[0].response_object_refs
            )
        )

    ordered_response_target_groups = {
        group: ordered
        for group in groups
        if (ordered := ordered_response_target_merge(group)) is not None
    }
    normalized_groups = tuple(
        ordered_response_target_groups.get(group, group)
        for group in groups
    )

    overloaded = tuple(
        group
        for group in groups
        if len(group.ordered_duty_refs) == 2
        and not licensed_shared_relation_merge(group)
        and group not in ordered_response_target_groups
    )
    before = (0, len(overloaded), 0, 0)
    if not overloaded:
        return normalized_groups, (), before
    repaired = tuple(
        repaired_group
        for group in normalized_groups
        for repaired_group in (
            tuple(
                DutyGroupRow((duty_ref,))
                for duty_ref in group.ordered_duty_refs
            )
            if group in overloaded
            else (group,)
        )
    )
    after = (0, 0, 0, 0)
    if not _normal_form_repair_defect_tuple_strictly_decreases(before, after):
        raise Stage1CompositionError("RECOMPOSITION_REPAIR_NONMONOTONE_STOP")
    trace = NormalFormRepairTraceRow(
        repair_kind=NormalFormRepairKind.OVERLOADED_EXACT2_CLAUSE_UNIT_SPLIT,
        defect_tuple_before=before,
        defect_tuple_after=after,
        repaired_owner_refs=tuple(
            ref for group in overloaded for ref in group.ordered_duty_refs
        ),
    )
    return repaired, (trace,), after


def _fresh_draft(phase_B: Stage1SurfaceCompositionInputs, seed: LayoutPreferenceSeed) -> DraftArtifact:
    _validate_phase_B(phase_B)
    arc = project_stage1_discourse_arc(phase_B)
    projected_duties = _project_duties(phase_B, arc)
    projected_duty_by_ref = {
        row.duty_ref: row for row in projected_duties
    }
    projected_required = tuple(
        row.duty_ref
        for row in projected_duties
        if row.retention == "REQUIRED"
    )
    seed_refs = tuple(ref for group in (*seed.layer1_group_rows, *seed.layer2_group_rows) for ref in group.ordered_duty_refs)
    layer2_seed_refs = _ordered_partition_refs(seed.layer2_group_rows)
    if (
        seed not in _layout_seeds(projected_duties, arc)
        or len(seed_refs) != len(set(seed_refs))
        or set(seed_refs) != set(projected_required)
        or seed.subjective_progression_duty_refs != layer2_seed_refs
    ):
        raise Stage1CompositionError("STAGE1_LAYOUT_SEED_COVERAGE_STOP")
    # Once the sole semantic topology has been selected, every downstream
    # duty-indexed row follows that visible trace order.  Optional suppressed
    # rows retain projection order after the complete required trace.
    duties = (
        *tuple(projected_duty_by_ref[ref] for ref in seed_refs),
        *tuple(
            row for row in projected_duties if row.retention == "OPTIONAL"
        ),
    )
    duty_by_ref = {row.duty_ref: row for row in duties}
    required = seed_refs
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
    required = tuple(row for row in duties if row.duty_ref in set(input_refs))
    predecessor_by_duty, _successor_by_duty = _duty_dependency_maps(
        required, arc
    )
    # Preserve projection-owned information order for otherwise-independent
    # roots.  A typed terminal owner is nevertheless selected only after all
    # other eligible duties in its layer.
    source_order = {
        row.duty_ref: index
        for index, row in enumerate(duties)
        if row.duty_ref in set(input_refs)
    }
    terminal_owner_refs = set(arc.terminal_owner_refs)
    licensed_pair_target_refs = {
        response_ref
        for layer2_duty in required
        if layer2_duty.layer == "LAYER_2"
        and not layer2_duty.relation_refs
        and len(layer2_duty.response_object_refs) == 2
        and len(
            tuple(
                layer1_duty
                for layer1_duty in required
                if layer1_duty.layer == "LAYER_1"
                and not layer1_duty.relation_refs
                and len(layer1_duty.response_object_refs) == 1
                and layer1_duty.response_object_refs[0]
                in set(layer2_duty.response_object_refs)
            )
        )
        == 2
        for response_ref in layer2_duty.response_object_refs
    }
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
                1
                if duty_by_ref[ref].layer == "LAYER_1"
                and licensed_pair_target_refs.intersection(
                    duty_by_ref[ref].response_object_refs
                )
                else 0,
                1
                if terminal_owner_refs.intersection(
                    duty_by_ref[ref].basis_projection_refs
                )
                else 0,
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
    phase_B: Stage1SurfaceCompositionInputs,
) -> Tuple[Tuple[ResponseObjectExpression, ...], Tuple[ComposedSentenceUnit, ...]]:
    expressions: list[ResponseObjectExpression] = []
    units: list[ComposedSentenceUnit] = []
    antecedent_by_refs: dict[
        Tuple[str, ...], Tuple[str, str, int, Tuple[str, ...]]
    ] = {}
    antecedent_by_ref: dict[
        str, Tuple[str, str, int, Tuple[str, ...]]
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
                _unique(row.sentence_job.value for row in duties),
                unit_anchor_refs,
                tuple(plan_by_duty[ref].clause_plan_ref for ref in group.ordered_duty_refs),
                "",
                "",
            )
        )
        for duty in duties:
            _owner, _all_source_refs, frame, refs = (
                _v2_source_binding_for_duty(duty, phase_B)
            )
            prior = antecedent_by_refs.get(refs)
            if prior is None and len(refs) == 2 and not duty.relation_refs:
                prior_rows = tuple(
                    antecedent_by_ref.get(ref) for ref in refs
                )
                if (
                    all(row is not None for row in prior_rows)
                    and all(row[1] == "LAYER_1" for row in prior_rows if row)
                    and len({row[0] for row in prior_rows if row}) == 1
                    and all(row[3] == refs for row in prior_rows if row)
                ):
                    latest_prior = max(
                        (row for row in prior_rows if row),
                        key=lambda row: row[2],
                    )
                    if latest_prior[2] == index - 1:
                        prior = latest_prior
            plan = plan_by_duty[duty.duty_ref]
            exact_immediately_prior = (
                prior is not None
                and prior[2] == index - 1
                and prior[3] == refs
            )
            source_cardinality = (
                SourceLeafCardinality.EXACT1
                if len(refs) == 1
                else SourceLeafCardinality.ORDERED_EXACT2
                if len(refs) == 2
                else (_ for _ in ()).throw(
                    Stage1CompositionError(
                        "STAGE1_SOURCE_PAIR_CARDINALITY_STOP"
                    )
                )
            )
            reference_surface = _v2_reference_surface_for_frame(
                frame, source_cardinality
            )
            if (
                exact_immediately_prior
                and not duty.relation_refs
                and plan.predicate_valency
                is not PredicateValency.TRIADIC_ACTOR_TARGET_BOUNDARY
                and reference_surface is not None
            ):
                mode = ResponseObjectExpressionMode.ANAPHORIC
                if prior is None:
                    raise Stage1CompositionError(
                        "STAGE1_REFERENCE_STATE_NONUNIQUE_STOP"
                    )
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
            for ref in refs:
                antecedent_by_ref[ref] = (
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
        or duty_by_ref[ordered_refs[0]].layer != "LAYER_1"
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


def _v2_normal_form_phase_reference_speaker_link_recalculation(
    groups: Tuple[DutyGroupRow, ...],
    seed: LayoutPreferenceSeed,
    duty_by_ref: dict[str, CompositionDutyView],
    plan_by_duty: dict[str, ClausePlan],
    arc: Stage1DiscourseArcView,
    phase_B: Stage1SurfaceCompositionInputs,
) -> Tuple[Tuple[ResponseObjectExpression, ...], Tuple[ComposedSentenceUnit, ...]]:
    """Phase 4: recalculate typed mention/speaker state after grouping."""

    expressions, unit_skeletons = (
        _normal_form_phase_reference_antecedent_recalculation(
            groups, duty_by_ref, plan_by_duty, arc, phase_B
        )
    )
    ordered_refs = tuple(
        duty_ref for group in groups for duty_ref in group.ordered_duty_refs
    )
    first_layer2_index = next(
        (
            index
            for index, duty_ref in enumerate(ordered_refs)
            if duty_by_ref[duty_ref].layer == "LAYER_2"
        ),
        len(ordered_refs),
    )
    if (
        not ordered_refs
        or duty_by_ref[ordered_refs[0]].layer != "LAYER_1"
        or seed.terminal_duty_ref not in groups[-1].ordered_duty_refs
        or any(
            duty_by_ref[duty_ref].layer == "LAYER_1"
            for duty_ref in ordered_refs[first_layer2_index:]
        )
    ):
        raise Stage1CompositionError("RECOMPOSITION_TERMINAL_OR_TOPIC_STOP")
    return expressions, unit_skeletons


def _typed_shared_endpoint_relation_chain(
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


def _shared_endpoint_relation_chain(
    duty_refs: Tuple[str, ...],
    duty_by_ref: dict[str, CompositionDutyView],
    plan_by_duty: dict[str, ClausePlan],
) -> Optional[Tuple[CompositionDutyView, CompositionDutyView]]:
    """Historical Step-1 seam retained for migration-ledger closure only."""

    return _typed_shared_endpoint_relation_chain(
        duty_refs, duty_by_ref, plan_by_duty
    )


def _v2_shared_endpoint_relation_chain(
    duty_refs: Tuple[str, ...],
    duty_by_ref: dict[str, CompositionDutyView],
    plan_by_duty: dict[str, ClausePlan],
) -> Optional[Tuple[CompositionDutyView, CompositionDutyView]]:
    """Typed v2 owner for the licensed exact2 relation grouping."""

    return _typed_shared_endpoint_relation_chain(
        duty_refs, duty_by_ref, plan_by_duty
    )


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


def _v2_normal_form_phase_grammar_binding_ir_local_repair(
    units: Tuple[ComposedSentenceUnit, ...],
    expressions: Tuple[ResponseObjectExpression, ...],
    duty_by_ref: dict[str, CompositionDutyView],
    plan_by_duty: dict[str, ClausePlan],
    phase_B: Stage1SurfaceCompositionInputs,
    arc: Stage1DiscourseArcView,
) -> Tuple[V2ClauseIRRow, ...]:
    """Phase 5: bind the typed grammar and build IR without visible text."""

    expression_by_plan = {row.clause_plan_ref: row for row in expressions}
    if set(expression_by_plan) != {
        plan.clause_plan_ref for plan in plan_by_duty.values()
    } or arc.projection_ref != _projection_ref(phase_B.projection):
        raise Stage1CompositionError("RECOMPOSITION_NORMAL_FORM_INPUT_STOP")
    predecessor_by_duty, _successor_by_duty = _duty_dependency_maps(
        tuple(duty_by_ref.values()), arc
    )
    root_owner_refs = set(arc.root_owner_refs)
    envelope = getattr(phase_B.admitted_source, "envelope", None)
    envelope_ref = getattr(envelope, "envelope_id", None)
    raw_utf8 = getattr(envelope, "raw_utf8", None)
    if not envelope_ref or type(raw_utf8) is not bytes:
        raise Stage1CompositionError(
            "STAGE1_SOURCE_LEAF_BINDING_NONUNIQUE_STOP"
        )
    source_envelope_bindings = ((envelope_ref, raw_utf8),)
    evidence_literal_bindings = tuple(
        (
            evidence.evidence_id,
            evidence.source_envelope_id,
            evidence.utf8_start,
            evidence.utf8_end,
        )
        for evidence in getattr(phase_B.admitted_source, "evidence_refs", ())
    )
    if not evidence_literal_bindings:
        raise Stage1CompositionError(
            "STAGE1_SOURCE_LEAF_BINDING_NONUNIQUE_STOP"
        )
    qualified_configuration_by_ref = {
        row.configuration_id: row
        for row in (
            phase_B.phase_A_authority.input_specific_meaning_structure.configurations
        )
        if type(row) is QualifiedEventStateConfiguration
    }

    clause_rows: list[V2ClauseIRRow] = []
    emlis_subject_established = False
    previous_subjective_was_counterposition = False
    previous_token_owner_ref: Optional[str] = None
    prior_object_by_refs: dict[Tuple[str, ...], Tuple[str, int]] = {}
    prior_object_by_ref: dict[str, Tuple[str, int]] = {}
    unit_anchor_refs_by_ref = {
        unit.unit_ref: unit.basis_anchor_refs for unit in units
    }
    for unit_index, unit in enumerate(units):
        for duty_ref in unit.duty_refs:
            duty = duty_by_ref[duty_ref]
            owner, _all_source_refs, frame, source_refs = (
                _v2_source_binding_for_duty(duty, phase_B)
            )
            plan = plan_by_duty[duty_ref]
            expression = expression_by_plan[plan.clause_plan_ref]
            visible_meaning_trace_rows = tuple(
                trace
                for trace in phase_B.projection.meaning_visible_causal_trace_rows
                if type(trace) is SelectedMeaningVisibleCausalTraceRow
                and set(trace.layer1_contribution_refs).intersection(
                    duty.basis_projection_refs
                )
                and (
                    trace.configuration_ref
                    in qualified_configuration_by_ref
                    or plan.semantic_clause_kind
                    is SemanticClauseKind.ADMITTED_RELATION
                )
            )
            for trace in visible_meaning_trace_rows:
                configuration = qualified_configuration_by_ref.get(
                    trace.configuration_ref
                )
                qualified_trace_valid = bool(
                    configuration is not None
                    and configuration.predicate_ref
                    in set(trace.configuration_component_refs)
                    and set(trace.configuration_component_refs).issubset(
                        {configuration.predicate_ref, configuration.owner_ref}
                    )
                )
                relation_trace_valid = bool(
                    configuration is None
                    and plan.semantic_clause_kind
                    is SemanticClauseKind.ADMITTED_RELATION
                    and len(trace.configuration_component_refs) == 2
                    and set(trace.configuration_component_refs)
                    == set(source_refs)
                )
                if not (qualified_trace_valid or relation_trace_valid):
                    raise Stage1CompositionError(
                        "MEANING_REALIZATION_CAPABILITY_GAP"
                    )
            if (
                expression.unit_ref != unit.unit_ref
                or expression.basis_semantic_refs != source_refs
                or expression.relation_refs != duty.relation_refs
            ):
                raise Stage1CompositionError(
                    "STAGE1_SOURCE_PAIR_CARDINALITY_STOP"
                )
            selected_expression_asset = _expression_asset(
                duty,
                plan,
                owner,
                phase_B,
            )
            projected_leaf_rows = tuple(
                _v2_source_leaf_for_semantic_ref(
                    semantic_ref=semantic_ref,
                    owner=owner,
                    case_frame=frame,
                    phase_B=phase_B,
                )
                for semantic_ref in source_refs
            )
            source_leaves = tuple(row[0] for row in projected_leaf_rows)
            certified_subspan_bindings = tuple(
                row[1] for row in projected_leaf_rows if row[1] is not None
            )
            cardinality = (
                SourceLeafCardinality.EXACT1
                if len(source_leaves) == 1
                else SourceLeafCardinality.ORDERED_EXACT2
                if len(source_leaves) == 2
                else (_ for _ in ()).throw(
                    Stage1CompositionError(
                        "STAGE1_SOURCE_PAIR_CARDINALITY_STOP"
                    )
                )
            )
            source_group = project_source_leaf_group(
                group_ref=_ref(
                    "source-leaf-group-v2",
                    (duty_ref, tuple(leaf.leaf_ref for leaf in source_leaves)),
                ),
                cardinality=cardinality,
                source_leaves=source_leaves,
                source_envelope_bindings=source_envelope_bindings,
                evidence_literal_bindings=evidence_literal_bindings,
                certified_subspan_bindings=certified_subspan_bindings,
            )
            source_complement_plan = select_source_complement_plan(
                group=source_group,
                source_leaves=source_leaves,
                frame=frame,
            )
            head = select_atomic_predicate_head(frame)

            if duty.layer == "LAYER_2":
                slot_semantic_refs = {
                    "SUBJECT": CMEE_STAGE1_EMLIS_OWNER_REF,
                    "PRIMARY_OBJECT": source_refs[0],
                    **(
                        {"SECONDARY_OBJECT": source_refs[1]}
                        if "SECONDARY_OBJECT" in frame.slot_roles
                        else {}
                    ),
                }
            else:
                slot_semantic_refs = dict(
                    zip(frame.slot_roles, source_refs, strict=True)
                )
            argument_plans = project_argument_realization_plan(
                frame=frame,
                slot_bindings=tuple(
                    (
                        ClauseArgumentRole(slot_role),
                        slot_semantic_refs[slot_role],
                        _unique(
                            (
                                duty.basis_projection_refs[0],
                                slot_semantic_refs[slot_role],
                            )
                        ),
                    )
                    for slot_role in frame.slot_roles
                ),
            )

            frame_relation = _v2_relation_operator_for_frame(frame.frame_id)
            subject_state: Optional[DiscourseReferenceStateRow] = None
            if frame_relation is not RelationOperator.NO_RELATION_CLAIM:
                object_state = project_reference_state(
                    state_ref=_ref(
                        "reference-state-v2", (unit.unit_ref, duty_ref, "relation")
                    ),
                    decision_kind=ReferenceDecisionKind.REQUIRED_RELATION_ENDPOINT,
                    referent_refs=source_refs,
                    focus_ref=source_refs[0],
                    establishment_proof_refs=(duty_ref,),
                )
                if len(duty.relation_refs) != 1:
                    raise Stage1CompositionError(
                        "STAGE1_CLAUSE_LINK_NONUNIQUE_STOP"
                    )
                link_plan = project_clause_link_plan(
                    link_plan_ref=_ref(
                        "clause-link-plan-v2", (unit.unit_ref, duty_ref)
                    ),
                    admitted_relation_ref=duty.relation_refs[0],
                    admitted_relation=frame_relation,
                    placement=ClauseLinkPlacement.FRAME_INTERNAL,
                    frame=frame,
                    previous_token_owner_ref=previous_token_owner_ref,
                )
            elif duty.layer == "LAYER_2":
                proposition = _prop(owner)
                relational_position = proposition.relational_position
                is_counterposition = (
                    proposition.subjective_mode
                    is SubjectiveMode.BOUNDED_COUNTERPOSITION
                    and proposition.subjective_operator
                    is SubjectiveOperator.COUNTER_SPECIFIC_PROMOTION
                    and relational_position is not None
                    and relational_position.relational_position_kind
                    is RelationalPositionKind.BOUNDED_COUNTERPOSITION
                    and relational_position.commitment
                    is RelationalCommitment.DECLINE_PROMOTION
                    and relational_position.closure is RelationalClosure.BOUNDED
                )
                after_counterposition = (
                    previous_subjective_was_counterposition
                )
                subject_state = project_reference_state(
                    state_ref=_ref(
                        "reference-state-v2", (unit.unit_ref, duty_ref, "speaker")
                    ),
                    decision_kind=ReferenceDecisionKind.EMLIS_SUBJECT,
                    referent_refs=(CMEE_STAGE1_EMLIS_OWNER_REF,),
                    speaker_ref=CMEE_STAGE1_EMLIS_OWNER_REF,
                    establishment_proof_refs=(duty_ref,),
                    same_speaker_chain=(
                        emlis_subject_established
                        and not is_counterposition
                        and not after_counterposition
                    ),
                    first_or_restart=(
                        (not emlis_subject_established or is_counterposition)
                        and not after_counterposition
                    ),
                    after_counterposition=after_counterposition,
                    introduced_topic=(
                        not emlis_subject_established
                        and not is_counterposition
                    ),
                    admitted_contrast=is_counterposition,
                )
                emlis_subject_established = True
                previous_subjective_was_counterposition = is_counterposition
                link_plan = project_clause_link_plan(
                    link_plan_ref=_ref(
                        "clause-link-plan-v2", (unit.unit_ref, duty_ref)
                    ),
                    admitted_relation_ref=f"relation:none:{duty_ref}",
                    admitted_relation=RelationOperator.NO_RELATION_CLAIM,
                    placement=ClauseLinkPlacement.ZERO,
                    frame=frame,
                    relation_already_owned=True,
                    previous_token_owner_ref=previous_token_owner_ref,
                )
            else:
                independent_topic = (
                    previous_token_owner_ref is not None
                    and not predecessor_by_duty[duty_ref]
                    and bool(
                        root_owner_refs.intersection(
                            duty.basis_projection_refs
                        )
                    )
                )
                link_plan = project_clause_link_plan(
                    link_plan_ref=_ref(
                        "clause-link-plan-v2", (unit.unit_ref, duty_ref)
                    ),
                    admitted_relation_ref=f"relation:none:{duty_ref}",
                    admitted_relation=RelationOperator.NO_RELATION_CLAIM,
                    placement=(
                        ClauseLinkPlacement.SENTENCE_INITIAL_ADDITIVE
                        if independent_topic
                        else ClauseLinkPlacement.ZERO
                    ),
                    frame=frame,
                    relation_already_owned=not independent_topic,
                    independent_topic=independent_topic,
                    is_first_sentence=not independent_topic,
                    previous_token_owner_ref=previous_token_owner_ref,
                )
            if frame_relation is RelationOperator.NO_RELATION_CLAIM:
                prior_object = prior_object_by_refs.get(source_refs)
                if (
                    prior_object is None
                    and len(source_refs) == 2
                    and expression.expression_mode
                    is ResponseObjectExpressionMode.ANAPHORIC
                ):
                    prior_rows = tuple(
                        prior_object_by_ref.get(ref) for ref in source_refs
                    )
                    if (
                        all(row is not None for row in prior_rows)
                        and len({row[0] for row in prior_rows if row}) == 1
                        and unit_anchor_refs_by_ref.get(
                            next(row[0] for row in prior_rows if row)
                        )
                        == source_refs
                    ):
                        latest_prior = max(
                            (row for row in prior_rows if row),
                            key=lambda row: row[1],
                        )
                        if latest_prior[1] == unit_index - 1:
                            prior_object = latest_prior
                exact_immediately_prior = bool(
                    prior_object is not None
                    and prior_object[1] == unit_index - 1
                )
                proof_refs = (
                    duty_ref,
                    expression.response_object_expression_ref,
                    *(
                        (f"antecedent-unit:{prior_object[0]}",)
                        if prior_object is not None
                        else ()
                    ),
                )
                if expression.expression_mode is ResponseObjectExpressionMode.ANAPHORIC:
                    if (
                        not exact_immediately_prior
                        or prior_object is None
                        or expression.antecedent_unit_ref != prior_object[0]
                        or _v2_reference_surface_for_frame(frame, cardinality)
                        is None
                    ):
                        raise Stage1CompositionError(
                            "STAGE1_REFERENCE_STATE_NONUNIQUE_STOP"
                        )
                    object_state = project_reference_state(
                        state_ref=_ref(
                            "reference-state-v2",
                            (unit.unit_ref, duty_ref, "object-anaphor"),
                        ),
                        decision_kind=ReferenceDecisionKind.REFERENT,
                        referent_refs=source_refs,
                        antecedent_refs=source_refs,
                        focus_ref=(
                            source_refs[0] if len(source_refs) == 1 else None
                        ),
                        establishment_proof_refs=proof_refs,
                        previous_ordered_pair_refs=(
                            source_refs if len(source_refs) == 2 else ()
                        ),
                        distance_is_local=True,
                    )
                elif prior_object is not None:
                    object_state = project_reference_state(
                        state_ref=_ref(
                            "reference-state-v2",
                            (unit.unit_ref, duty_ref, "object-repair"),
                        ),
                        decision_kind=ReferenceDecisionKind.REFERENT,
                        referent_refs=source_refs,
                        antecedent_refs=source_refs,
                        focus_ref=source_refs[0],
                        establishment_proof_refs=proof_refs,
                        reference_repair=True,
                        distance_is_local=exact_immediately_prior,
                        full_expression_frame_compatible=True,
                    )
                else:
                    object_state = project_reference_state(
                        state_ref=_ref(
                            "reference-state-v2",
                            (unit.unit_ref, duty_ref, "object-first"),
                        ),
                        decision_kind=ReferenceDecisionKind.REFERENT,
                        referent_refs=source_refs,
                        focus_ref=source_refs[0],
                        establishment_proof_refs=proof_refs,
                    )
            reference_state = V2ClauseReferenceStateBundle(
                state_ref=_ref(
                    "reference-state-bundle-v2",
                    (subject_state, object_state, expression),
                ),
                subject_state=subject_state,
                object_state=object_state,
                response_object_expression=expression,
            )
            prior_object_by_refs[source_refs] = (unit.unit_ref, unit_index)
            for source_ref in source_refs:
                prior_object_by_ref[source_ref] = (
                    unit.unit_ref,
                    unit_index,
                )
            previous_token_owner_ref = link_plan.token_owner_ref
            morphology_plan = project_predicate_morphology_plan(
                frame=frame, head=head
            )
            _v2_validate_layer2_reception_morphology(
                duty,
                phase_B,
                morphology_plan,
            )
            clause_ir = build_japanese_clause_ir(
                frame=frame,
                head=head,
                argument_plans=argument_plans,
                source_complement_plan=source_complement_plan,
                reference_state=reference_state,
                link_plan=link_plan,
                morphology_plan=morphology_plan,
            )
            clause_rows.append(
                V2ClauseIRRow(
                    duty_ref=duty_ref,
                    unit_ref=unit.unit_ref,
                    source_leaves=source_leaves,
                    source_group=source_group,
                    frame=frame,
                    head=head,
                    source_complement_plan=source_complement_plan,
                    argument_plans=argument_plans,
                    reference_state=reference_state,
                    link_plan=link_plan,
                    morphology_plan=morphology_plan,
                    clause_ir=clause_ir,
                    selected_expression_asset_ref=(
                        selected_expression_asset.expression_asset_id
                    ),
                    clause_plan=plan,
                    visible_meaning_trace_rows=(
                        visible_meaning_trace_rows
                    ),
                )
            )

    return tuple(clause_rows)


def _v2_normal_form_phase_sole_linearization_grammar_seal(
    units: Tuple[ComposedSentenceUnit, ...],
    clause_ir_rows: Tuple[V2ClauseIRRow, ...],
    duty_by_ref: dict[str, CompositionDutyView],
    plan_by_duty: dict[str, ClausePlan],
) -> Tuple[Tuple[ComposedSentenceUnit, ...], Tuple[V2ClauseRealizationRow, ...]]:
    """Phase 6: invoke the sole linearizer and seal exact visible cover."""

    row_by_duty = {row.duty_ref: row for row in clause_ir_rows}
    if (
        len(row_by_duty) != len(clause_ir_rows)
        or set(row_by_duty) != set(duty_by_ref)
        or set(row_by_duty) != set(plan_by_duty)
        or any(
            duty_ref not in row_by_duty
            for unit in units
            for duty_ref in unit.duty_refs
        )
    ):
        raise Stage1CompositionError("STAGE1_DERIVATION_SEAL_STOP")
    grouped_sequence_duty_refs = frozenset(
        duty_ref
        for unit in units
        if _v2_shared_endpoint_relation_chain(
            unit.duty_refs,
            duty_by_ref,
            plan_by_duty,
        )
        is not None
        for duty_ref in unit.duty_refs
        if row_by_duty[duty_ref].frame.sense_ref == "S07"
    )
    clause_rows = tuple(
        V2ClauseRealizationRow(
            duty_ref=row.duty_ref,
            unit_ref=row.unit_ref,
            source_leaves=row.source_leaves,
            source_group=row.source_group,
            frame=row.frame,
            head=row.head,
            source_complement_plan=row.source_complement_plan,
            argument_plans=row.argument_plans,
            reference_state=row.reference_state,
            link_plan=row.link_plan,
            morphology_plan=row.morphology_plan,
            clause_ir=row.clause_ir,
            linearized_clause=linearize_japanese_clause(
                clause_ir=row.clause_ir,
                frame=row.frame,
                head=row.head,
                group=row.source_group,
                source_leaves=row.source_leaves,
                source_complement_plan=row.source_complement_plan,
                reference_state=row.reference_state,
                link_plan=row.link_plan,
                morphology_plan=row.morphology_plan,
                clause_plan=row.clause_plan,
                selected_expression_asset_ref=(
                    row.selected_expression_asset_ref
                ),
                suppress_grouped_sequence_asset_surface=(
                    row.duty_ref in grouped_sequence_duty_refs
                ),
                visible_meaning_trace_rows=(
                    row.visible_meaning_trace_rows
                ),
            ),
            selected_expression_asset_ref=(
                row.selected_expression_asset_ref
            ),
            clause_plan=row.clause_plan,
            visible_meaning_trace_rows=row.visible_meaning_trace_rows,
        )
        for row in clause_ir_rows
    )
    if (
        not clause_rows
        or len(clause_rows) != len(clause_ir_rows)
        or tuple(row.duty_ref for row in clause_rows)
        != tuple(row.duty_ref for row in clause_ir_rows)
    ):
        raise Stage1CompositionError("STAGE1_DERIVATION_SEAL_STOP")

    output: list[ComposedSentenceUnit] = []
    for unit in units:
        rows = tuple(
            row for row in clause_rows if row.unit_ref == unit.unit_ref
        )
        if tuple(row.duty_ref for row in rows) != unit.duty_refs:
            raise Stage1CompositionError("STAGE1_DERIVATION_SEAL_STOP")
        text = "".join(row.linearized_clause.text for row in rows)
        bindings: list[RealizedSemanticBinding] = []
        derivations: list[SurfaceDerivation] = []
        cursor = 0
        for row in rows:
            if len(row.linearized_clause.realized_semantic_bindings) != len(
                row.linearized_clause.surface_derivations
            ):
                raise Stage1CompositionError("STAGE1_DERIVATION_SEAL_STOP")
            for binding in row.linearized_clause.realized_semantic_bindings:
                bindings.append(
                    RealizedSemanticBinding(
                        semantic_ref=binding.semantic_ref,
                        clause_slot=binding.clause_slot,
                        surface_scalar_start=(
                            cursor + binding.surface_scalar_start
                        ),
                        surface_scalar_end=cursor + binding.surface_scalar_end,
                        surface_span_sha256=binding.surface_span_sha256,
                    )
                )
            derivations.extend(row.linearized_clause.surface_derivations)
            cursor += len(row.linearized_clause.text)
        if (
            not text
            or cursor != len(text)
            or len(bindings) != len(derivations)
            or tuple(binding.surface_scalar_start for binding in bindings)
            != tuple(
                0 if index == 0 else bindings[index - 1].surface_scalar_end
                for index in range(len(bindings))
            )
            or any(
                binding.surface_span_sha256
                != hashlib.sha256(
                    text[
                        binding.surface_scalar_start : binding.surface_scalar_end
                    ].encode("utf-8")
                ).hexdigest()
                for binding in bindings
            )
        ):
            raise Stage1CompositionError("STAGE1_DERIVATION_SEAL_STOP")
        output.append(
            ComposedSentenceUnit(
                unit_ref=unit.unit_ref,
                layer=unit.layer,
                duty_refs=unit.duty_refs,
                sentence_job_refs=unit.sentence_job_refs,
                basis_anchor_refs=unit.basis_anchor_refs,
                clause_plan_refs=unit.clause_plan_refs,
                text=text,
                surface_text_sha256=hashlib.sha256(
                    text.encode("utf-8")
                ).hexdigest(),
                clause_frames=tuple(
                    frame
                    for row in rows
                    for frame in row.linearized_clause.clause_frames
                ),
                realized_semantic_bindings=tuple(bindings),
                surface_derivations=tuple(derivations),
                frame_refs=tuple(row.frame.frame_id for row in rows),
                atomic_head_refs=tuple(row.head.head_id for row in rows),
                lexical_family_refs=tuple(
                    row.head.lexical_family_ref for row in rows
                ),
                source_group_refs=tuple(
                    row.source_group.group_ref for row in rows
                ),
                reference_state_refs=tuple(
                    row.reference_state.state_ref for row in rows
                ),
                link_plan_refs=tuple(
                    row.link_plan.link_plan_ref for row in rows
                ),
                morphology_plan_refs=tuple(
                    row.morphology_plan.plan_ref for row in rows
                ),
                clause_ir_refs=tuple(
                    row.clause_ir.clause_ir_ref for row in rows
                ),
            )
        )
    return tuple(output), tuple(clause_rows)


def _normal_form_phase_expression_selection_final_linearization(
    units: Tuple[ComposedSentenceUnit, ...],
    expressions: Tuple[ResponseObjectExpression, ...],
    duty_by_ref: dict[str, CompositionDutyView],
    plan_by_duty: dict[str, ClausePlan],
    phase_B: Stage1SurfaceCompositionInputs,
) -> Tuple[Tuple[ComposedSentenceUnit, ...], Tuple[V2ClauseRealizationRow, ...]]:
    """Historical Step-1 seam retained outside the active v2 call graph."""

    clause_ir_rows = _v2_normal_form_phase_grammar_binding_ir_local_repair(
        units,
        expressions,
        duty_by_ref,
        plan_by_duty,
        phase_B,
        project_stage1_discourse_arc(phase_B),
    )
    return _v2_normal_form_phase_sole_linearization_grammar_seal(
        units,
        clause_ir_rows,
        duty_by_ref,
        plan_by_duty,
    )


def _validate_v2_normalized_grammar_seal(
    artifact: NormalizedDraftArtifact,
) -> None:
    rows = artifact.v2_clause_rows
    units = artifact.sentence_units
    visible_duty_refs = tuple(
        duty_ref for unit in units for duty_ref in unit.duty_refs
    )
    if (
        not rows
        or tuple(row.duty_ref for row in rows) != artifact.required_duty_refs
        or set(visible_duty_refs) != set(artifact.required_duty_refs)
        or len({row.duty_ref for row in rows}) != len(rows)
    ):
        raise Stage1CompositionError("STAGE1_DERIVATION_SEAL_STOP")
    prior_lexical_family_ref: Optional[str] = None
    row_by_duty = {row.duty_ref: row for row in rows}
    duty_by_ref = {
        row.duty_ref: row for row in artifact.composition_duty_rows
    }
    plan_by_duty = {
        row.duty_ref: row for row in artifact.clause_plan_rows
    }
    if set(row_by_duty) != set(duty_by_ref) or set(row_by_duty) != set(
        plan_by_duty
    ):
        raise Stage1CompositionError("STAGE1_DERIVATION_SEAL_STOP")
    for unit in units:
        unit_rows = tuple(row_by_duty[duty_ref] for duty_ref in unit.duty_refs)
        exact_count = len(unit_rows)
        if (
            tuple(row.duty_ref for row in unit_rows) != unit.duty_refs
            or any(row.unit_ref != unit.unit_ref for row in unit_rows)
            or not exact_count
            or len(unit.clause_plan_refs) != exact_count
            or len(unit.clause_frames) != exact_count
            or len(unit.frame_refs) != exact_count
            or len(unit.atomic_head_refs) != exact_count
            or len(unit.lexical_family_refs) != exact_count
            or len(unit.source_group_refs) != exact_count
            or len(unit.reference_state_refs) != exact_count
            or len(unit.link_plan_refs) != exact_count
            or len(unit.morphology_plan_refs) != exact_count
            or len(unit.clause_ir_refs) != exact_count
            or len(unit.realized_semantic_bindings)
            != len(unit.surface_derivations)
        ):
            raise Stage1CompositionError("STAGE1_DERIVATION_SEAL_STOP")
        grouped_sequence_chain = _v2_shared_endpoint_relation_chain(
            unit.duty_refs,
            duty_by_ref,
            plan_by_duty,
        )
        for row in unit_rows:
            repeated = linearize_japanese_clause(
                clause_ir=row.clause_ir,
                frame=row.frame,
                head=row.head,
                group=row.source_group,
                source_leaves=row.source_leaves,
                source_complement_plan=row.source_complement_plan,
                reference_state=row.reference_state,
                link_plan=row.link_plan,
                morphology_plan=row.morphology_plan,
                clause_plan=row.clause_plan,
                selected_expression_asset_ref=(
                    row.selected_expression_asset_ref
                ),
                suppress_grouped_sequence_asset_surface=(
                    grouped_sequence_chain is not None
                    and row.frame.sense_ref == "S07"
                ),
                visible_meaning_trace_rows=(
                    row.visible_meaning_trace_rows
                ),
            )
            if repeated != row.linearized_clause:
                raise Stage1CompositionError(
                    "STAGE1_JAPANESE_CLAUSE_IR_TAMPER_STOP"
                )
            if (
                prior_lexical_family_ref is not None
                and prior_lexical_family_ref == row.head.lexical_family_ref
            ):
                raise Stage1CompositionError(
                    "ADJACENT_ATOMIC_HEAD_REPEAT_STOP"
                )
            prior_lexical_family_ref = row.head.lexical_family_ref
        if (
            unit.frame_refs != tuple(row.frame.frame_id for row in unit_rows)
            or unit.atomic_head_refs
            != tuple(row.head.head_id for row in unit_rows)
            or unit.lexical_family_refs
            != tuple(row.head.lexical_family_ref for row in unit_rows)
            or unit.source_group_refs
            != tuple(row.source_group.group_ref for row in unit_rows)
            or unit.reference_state_refs
            != tuple(row.reference_state.state_ref for row in unit_rows)
            or unit.link_plan_refs
            != tuple(row.link_plan.link_plan_ref for row in unit_rows)
            or unit.morphology_plan_refs
            != tuple(row.morphology_plan.plan_ref for row in unit_rows)
            or unit.clause_ir_refs
            != tuple(row.clause_ir.clause_ir_ref for row in unit_rows)
            or unit.clause_frames
            != tuple(
                frame
                for row in unit_rows
                for frame in row.linearized_clause.clause_frames
            )
        ):
            raise Stage1CompositionError("STAGE1_DERIVATION_SEAL_STOP")
        cursor = 0
        for binding in unit.realized_semantic_bindings:
            if (
                binding.surface_scalar_start != cursor
                or not (
                    cursor
                    < binding.surface_scalar_end
                    <= len(unit.text)
                )
                or binding.surface_span_sha256
                != hashlib.sha256(
                    unit.text[cursor : binding.surface_scalar_end].encode(
                        "utf-8"
                    )
                ).hexdigest()
            ):
                raise Stage1CompositionError("STAGE1_DERIVATION_SEAL_STOP")
            cursor = binding.surface_scalar_end
        if cursor != len(unit.text):
            raise Stage1CompositionError("STAGE1_DERIVATION_SEAL_STOP")

    repair_kinds = tuple(row.repair_kind for row in artifact.repair_trace_rows)
    if len(repair_kinds) != len(set(repair_kinds)) or any(
        not _normal_form_repair_defect_tuple_strictly_decreases(
            row.defect_tuple_before, row.defect_tuple_after
        )
        for row in artifact.repair_trace_rows
    ):
        raise Stage1CompositionError("RECOMPOSITION_REPAIR_NONMONOTONE_STOP")
    expected_final_defect_tuple = (
        artifact.repair_trace_rows[-1].defect_tuple_after
        if artifact.repair_trace_rows
        else (0, 0, 0, 0)
    )
    if artifact.repair_defect_tuple != expected_final_defect_tuple:
        raise Stage1CompositionError("RECOMPOSITION_REPAIR_NONMONOTONE_STOP")


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
    unit_by_ref = {row.unit_ref: row for row in units}
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

    reciprocal_nonprecedence_refs = {
        row.arc_dependency_ref
        for row in _local_reciprocal_tension_dependencies(duties, arc)
    }

    def dependency_valid(edge: ArcDependencyRow) -> bool:
        if edge.arc_dependency_ref in reciprocal_nonprecedence_refs:
            return True
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
    prior_expression_by_refs: dict[Tuple[str, ...], Tuple[str, int]] = {}
    prior_expression_by_ref: dict[str, Tuple[str, int]] = {}
    for expression in expressions:
        own_index = unit_index_by_ref.get(expression.unit_ref)
        plan = plan_by_ref.get(expression.clause_plan_ref)
        if own_index is None or plan is None:
            defects[
                CorrectableDefectKind.UNRESOLVED_OR_DISTANT_REFERENT
            ].add(expression.response_object_expression_ref)
            continue
        duty = duty_by_ref.get(plan.duty_ref)
        unit = unit_by_ref.get(expression.unit_ref)
        ordered_duty_projection = (
            tuple(
                ref
                for ref in duty.response_object_refs
                if ref in set(expression.basis_semantic_refs)
            )
            if duty is not None
            else ()
        )
        direct_literal_projection = (
            ()
            if unit is None
            else _unique(
                ref
                for derivation in unit.surface_derivations
                if derivation.derivation_kind
                is SurfaceDerivationKind.LITERAL_SUBSPAN
                for ref in derivation.source_or_claim_refs
                if ref in set(expression.basis_semantic_refs)
            )
        )
        response_domain_is_typed = bool(
            duty is not None
            and expression.basis_semantic_refs
            and len(expression.basis_semantic_refs)
            == len(set(expression.basis_semantic_refs))
            and set(expression.basis_semantic_refs).issubset(
                duty.response_object_refs
            )
        )
        binding_is_exact = bool(
            response_domain_is_typed
            and duty is not None
            and expression.relation_refs == duty.relation_refs
            and (
                ordered_duty_projection == expression.basis_semantic_refs
                if expression.expression_mode
                is ResponseObjectExpressionMode.ANAPHORIC
                else direct_literal_projection
                == expression.basis_semantic_refs
            )
        )
        prior_expression = prior_expression_by_refs.get(
            expression.basis_semantic_refs
        )
        if (
            prior_expression is None
            and expression.expression_mode
            is ResponseObjectExpressionMode.ANAPHORIC
            and len(expression.basis_semantic_refs) == 2
        ):
            prior_rows = tuple(
                prior_expression_by_ref.get(ref)
                for ref in expression.basis_semantic_refs
            )
            if (
                all(row is not None for row in prior_rows)
                and len({row[0] for row in prior_rows if row}) == 1
                and unit_by_ref[
                    next(row[0] for row in prior_rows if row)
                ].basis_anchor_refs
                == expression.basis_semantic_refs
            ):
                prior_expression = max(
                    (row for row in prior_rows if row),
                    key=lambda row: row[1],
                )
        if expression.expression_mode is ResponseObjectExpressionMode.ANAPHORIC:
            antecedent_index = unit_index_by_ref.get(
                expression.antecedent_unit_ref or ""
            )
            valid = bool(
                binding_is_exact
                and antecedent_index is not None
                and antecedent_index == own_index - 1
                and prior_expression
                == (expression.antecedent_unit_ref, antecedent_index)
                and len(expression.basis_semantic_refs) in {1, 2}
                and plan.predicate_valency
                is not PredicateValency.TRIADIC_ACTOR_TARGET_BOUNDARY
            )
        else:
            valid = bool(
                binding_is_exact
                and expression.antecedent_unit_ref is None
                and expression.basis_semantic_refs
            )
        if not valid:
            defects[
                CorrectableDefectKind.UNRESOLVED_OR_DISTANT_REFERENT
            ].add(expression.response_object_expression_ref)
        prior_expression_by_refs[expression.basis_semantic_refs] = (
            expression.unit_ref,
            own_index,
        )
        for semantic_ref in expression.basis_semantic_refs:
            prior_expression_by_ref[semantic_ref] = (
                expression.unit_ref,
                own_index,
            )

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
        and duty_by_ref[units[0].duty_refs[0]].layer == "LAYER_1"
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
    groups, repair_trace_rows, repair_defect_tuple = (
        _v2_normal_form_phase_dependency_preserving_merge_split(
            seed, duty_by_ref
        )
    )
    groups = _normal_form_phase_dependency_information_order(
        groups, duties, fresh.discourse_arc
    )
    expressions, unit_skeletons = (
        _v2_normal_form_phase_reference_speaker_link_recalculation(
            groups,
            seed,
            duty_by_ref,
            plan_by_duty,
            fresh.discourse_arc,
            phase_B_inputs,
        )
    )
    clause_ir_rows = _v2_normal_form_phase_grammar_binding_ir_local_repair(
        unit_skeletons,
        expressions,
        duty_by_ref,
        plan_by_duty,
        phase_B_inputs,
        fresh.discourse_arc,
    )
    sentence_units, v2_clause_rows = (
        _v2_normal_form_phase_sole_linearization_grammar_seal(
            unit_skeletons,
            clause_ir_rows,
            duty_by_ref,
            plan_by_duty,
        )
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
    clause_row_by_duty = {row.duty_ref: row for row in v2_clause_rows}
    if set(clause_row_by_duty) != set(fresh.required_duty_refs):
        raise Stage1CompositionError("STAGE1_DERIVATION_SEAL_STOP")
    v2_clause_rows = tuple(
        clause_row_by_duty[duty_ref] for duty_ref in fresh.required_duty_refs
    )
    normalized = NormalizedDraftArtifact(
        projection_ref=fresh.projection_ref,
        discourse_arc=fresh.discourse_arc,
        layout_preference_seed=fresh.layout_preference_seed,
        composition_duty_rows=duties,
        full_duty_refs=fresh.full_duty_refs,
        required_duty_refs=fresh.required_duty_refs,
        suppressed_duty_rows=suppressed_duties,
        suppressed_claim_rows=suppressed_claims,
        clause_plan_rows=fresh.clause_plan_rows,
        response_object_expression_rows=expressions,
        sentence_units=sentence_units,
        correctable_defect_rows=post_defect_rows,
        normal_form_version=CMEE_STAGE1_NORMAL_FORM_VERSION,
        normal_form_applied=True,
        normalization_phase_trace=tuple(NormalFormPhase),
        v2_clause_rows=v2_clause_rows,
        repair_trace_rows=repair_trace_rows,
        repair_defect_tuple=repair_defect_tuple,
    )
    _validate_v2_normalized_grammar_seal(normalized)
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
    _validate_v2_normalized_grammar_seal(artifact)
    v2_clause_material = tuple(
        (
            row.duty_ref,
            row.unit_ref,
            tuple(
                (
                    leaf.leaf_ref,
                    leaf.semantic_ref,
                    leaf.source_envelope_ref,
                    leaf.evidence_ref,
                    leaf.extent,
                    leaf.raw_utf8_start,
                    leaf.raw_utf8_end,
                    hashlib.sha256(leaf.payload_utf8).hexdigest(),
                    len(leaf.payload_utf8),
                    leaf.sentence_shape,
                    leaf.final_terminal_class,
                    leaf.quote_topology,
                    leaf.line_break_shape,
                    leaf.derivation,
                )
                for leaf in row.source_leaves
            ),
            row.source_group,
            row.frame,
            row.head,
            row.source_complement_plan,
            row.argument_plans,
            row.reference_state,
            row.link_plan,
            row.morphology_plan,
            row.clause_ir,
            row.selected_expression_asset_ref,
            row.linearized_clause,
        )
        for row in artifact.v2_clause_rows
    )
    return stage1_canonical_json_bytes(
        (
            artifact.projection_ref,
            artifact.discourse_arc,
            artifact.layout_preference_seed,
            artifact.composition_duty_rows,
            artifact.full_duty_refs,
            artifact.required_duty_refs,
            artifact.suppressed_duty_rows,
            artifact.suppressed_claim_rows,
            artifact.clause_plan_rows,
            artifact.response_object_expression_rows,
            artifact.sentence_units,
            artifact.correctable_defect_rows,
            artifact.normal_form_version,
            artifact.normal_form_applied,
            artifact.normalization_phase_trace,
            v2_clause_material,
            artifact.repair_trace_rows,
            artifact.repair_defect_tuple,
        )
    )


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

    reciprocal_nonprecedence_rows = (
        _local_reciprocal_tension_dependencies(
            normalized_artifact.composition_duty_rows,
            arc,
        )
    )

    def dependency_is_aligned(row: ArcDependencyRow) -> bool:
        predecessor_indexes = owner_unit_indexes.get(row.predecessor_owner_ref, set())
        successor_indexes = owner_unit_indexes.get(row.successor_owner_ref, set())
        if not predecessor_indexes or not successor_indexes:
            return False
        if row.dependency_kind is ArcDependencyKind.ADMITTED_RELATION_DIRECTION:
            if row in reciprocal_nonprecedence_rows:
                return True
            relation_duties = tuple(
                duty
                for duty in normalized_artifact.composition_duty_rows
                if row.source_relation_ref in duty.relation_refs
            )
            directly_aligned = (
                len(relation_duties) == 1
                and plan_by_duty[relation_duties[0].duty_ref].semantic_clause_kind
                is SemanticClauseKind.ADMITTED_RELATION
                and min(predecessor_indexes) <= min(successor_indexes)
            )
            if directly_aligned:
                return True
            return False
        return min(predecessor_indexes) <= min(successor_indexes)

    group_sizes = tuple(len(unit.duty_refs) for unit in units)
    available_relation_chains = {
        (first.duty_ref, second.duty_ref)
        for first in normalized_artifact.composition_duty_rows
        for second in normalized_artifact.composition_duty_rows
        if _v2_shared_endpoint_relation_chain(
            (first.duty_ref, second.duty_ref),
            duty_by_ref,
            plan_by_duty,
        )
        is not None
    }
    grouped_relation_chains = {
        unit.duty_refs
        for unit in units
        if _v2_shared_endpoint_relation_chain(
            unit.duty_refs,
            duty_by_ref,
            plan_by_duty,
        )
        is not None
    }
    available_response_target_pairs = {
        (first.duty_ref, second.duty_ref)
        for consumer in normalized_artifact.composition_duty_rows
        for first in normalized_artifact.composition_duty_rows
        for second in normalized_artifact.composition_duty_rows
        if consumer.layer == "LAYER_2"
        and consumer.retention == "REQUIRED"
        and not consumer.relation_refs
        and len(consumer.response_object_refs) == 2
        and len(set(consumer.response_object_refs)) == 2
        and first.layer == second.layer == "LAYER_1"
        and first.retention == second.retention == "REQUIRED"
        and not first.relation_refs
        and not second.relation_refs
        and len(first.response_object_refs)
        == len(second.response_object_refs)
        == 1
        and consumer.response_object_refs
        == (
            first.response_object_refs[0],
            second.response_object_refs[0],
        )
        and len(
            tuple(
                duty
                for duty in normalized_artifact.composition_duty_rows
                if duty.layer == "LAYER_1"
                and duty.retention == "REQUIRED"
                and not duty.relation_refs
                and len(duty.response_object_refs) == 1
                and duty.response_object_refs[0]
                in set(consumer.response_object_refs)
            )
        )
        == 2
        and len(
            tuple(
                duty
                for duty in normalized_artifact.composition_duty_rows
                if duty.layer == "LAYER_2"
                and duty.retention == "REQUIRED"
                and not duty.relation_refs
                and len(duty.response_object_refs) == 2
                and set(duty.response_object_refs)
                == set(consumer.response_object_refs)
            )
        )
        == 1
    }
    grouped_response_target_pairs = {
        unit.duty_refs
        for unit in units
        if unit.duty_refs in available_response_target_pairs
    }
    available_exact2_groups = (
        available_relation_chains | available_response_target_pairs
    )
    grouped_exact2_groups = (
        grouped_relation_chains | grouped_response_target_pairs
    )
    # Exact2 grouping is preferred for a typed relation chain or for the two
    # concrete Layer-1 objects jointly received by one Layer-2 proposition.
    sentence_load_aligned = (
        all(size == 1 for size in group_sizes)
        if not available_exact2_groups
        else grouped_exact2_groups == available_exact2_groups
        and all(
            len(unit.duty_refs) == 1
            or unit.duty_refs in grouped_exact2_groups
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


def derive_japanese_local_preference_profile(
    normalized_artifact: NormalizedDraftArtifact,
) -> JapaneseLocalPreferenceProfile:
    """Derive J01--J07 from typed plans only; lower is preferable."""

    if type(normalized_artifact) is not NormalizedDraftArtifact:
        raise Stage1CompositionError("STAGE1_LOCAL_PROFILE_INPUT_STOP")
    _validate_v2_normalized_grammar_seal(normalized_artifact)
    units = normalized_artifact.sentence_units
    row_by_duty = {
        row.duty_ref: row for row in normalized_artifact.v2_clause_rows
    }
    rows = tuple(
        row_by_duty[duty_ref]
        for unit in units
        for duty_ref in unit.duty_refs
    )
    reference_rule_ids = tuple(
        frozenset(
            rule.reference_rule_id
            for rule in _v2_reference_rows_from_bundle(row.reference_state)
        )
        for row in rows
    )

    explicit_referent_repeat = sum(
        bool(rule_ids.intersection({"R02", "R12"}))
        for rule_ids in reference_rule_ids
    )
    topic_selected = tuple(
        bool(rule_ids.intersection({"R08", "R09"}))
        for rule_ids in reference_rule_ids
    )
    topic_stack = sum(
        previous and current
        for previous, current in zip(
            topic_selected, topic_selected[1:]
        )
    )
    quote_or_nominalizer_load = sum(
        0
        if row.reference_state.response_object_expression.expression_mode
        is ResponseObjectExpressionMode.ANAPHORIC
        else max(0, len(row.source_complement_plan.quote_delimiter_refs) - 1)
        + (
            1
            if row.source_complement_plan.complement_rule_ref
            in {"C03", "C04", "C05", "C06"}
            else 0
        )
        for row in rows
    )
    visible_link_tokens = tuple(
        None
        if row.link_plan.token_owner_ref == "registered:empty"
        else row.link_plan.token_owner_ref
        for row in rows
    )
    connective_repeat = sum(
        previous is not None and previous == current
        for previous, current in zip(
            visible_link_tokens, visible_link_tokens[1:]
        )
    )
    subjective_rule_rows = tuple(
        rule_ids
        for row, rule_ids in zip(rows, reference_rule_ids, strict=True)
        if row.frame.zero_policy == "EMLIS_ZERO_CONDITIONAL"
    )
    explicit_emlis_subject_repeat = sum(
        bool(rule_ids.intersection({"R05", "R07"}))
        for rule_ids in subjective_rule_rows[1:]
    )
    clause_load = sum(max(0, len(unit.clause_frames) - 1) for unit in units)
    unit_index_by_ref = {
        unit.unit_ref: index for index, unit in enumerate(units)
    }
    reference_distance = sum(
        max(
            0,
            unit_index_by_ref[expression.unit_ref]
            - unit_index_by_ref[expression.antecedent_unit_ref or ""]
            - 1,
        )
        for expression in normalized_artifact.response_object_expression_rows
        if expression.expression_mode is ResponseObjectExpressionMode.ANAPHORIC
        and expression.unit_ref in unit_index_by_ref
        and (expression.antecedent_unit_ref or "") in unit_index_by_ref
    )
    values = (
        explicit_referent_repeat,
        topic_stack,
        quote_or_nominalizer_load,
        connective_repeat,
        explicit_emlis_subject_repeat,
        clause_load,
        reference_distance,
    )
    rule_ids = tuple(
        row.preference_rule_id
        for row in V2_JAPANESE_LOCAL_PREFERENCE_REGISTRY
    )
    if (
        rule_ids != tuple(f"J{index:02d}" for index in range(1, 8))
        or len(values) != 7
        or any(type(value) is not int or value < 0 for value in values)
    ):
        raise Stage1CompositionError("STAGE1_LOCAL_PROFILE_INPUT_STOP")
    comparison_rows = tuple(zip(rule_ids, values, strict=True))
    return JapaneseLocalPreferenceProfile(
        profile_ref=_ref(
            "japanese-local-preference-profile-v2",
            (normalized_artifact.projection_ref, comparison_rows),
        ),
        comparison_rows=comparison_rows,
    )


def _japanese_local_profile_key(
    profile: JapaneseLocalPreferenceProfile,
) -> Tuple[int, ...]:
    expected_rule_ids = tuple(
        row.preference_rule_id
        for row in V2_JAPANESE_LOCAL_PREFERENCE_REGISTRY
    )
    if (
        type(profile) is not JapaneseLocalPreferenceProfile
        or not profile.profile_ref
        or tuple(row[0] for row in profile.comparison_rows)
        != expected_rule_ids
        or any(
            type(row) is not tuple
            or len(row) != 2
            or type(row[1]) is not int
            or row[1] < 0
            for row in profile.comparison_rows
        )
    ):
        raise Stage1CompositionError("STAGE1_LOCAL_PROFILE_INPUT_STOP")
    return tuple(row[1] for row in profile.comparison_rows)


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


def _composition_layout_ref(artifact: NormalizedDraftArtifact) -> str:
    """Project the final-registry composition-layout identity preimage."""

    if (
        type(artifact) is not NormalizedDraftArtifact
        or artifact.projection_ref != artifact.discourse_arc.projection_ref
        or artifact.full_duty_refs
        != tuple(row.duty_ref for row in artifact.composition_duty_rows)
    ):
        raise Stage1CompositionError("STAGE1_COMPOSITION_LAYOUT_ID_STOP")
    row_by_duty = {row.duty_ref: row for row in artifact.v2_clause_rows}
    ordered_clause_rows = tuple(
        row_by_duty[duty_ref]
        for unit in artifact.sentence_units
        for duty_ref in unit.duty_refs
        if duty_ref in row_by_duty
    )
    if (
        len(row_by_duty) != len(artifact.v2_clause_rows)
        or tuple(row.duty_ref for row in ordered_clause_rows)
        != tuple(
            duty_ref
            for unit in artifact.sentence_units
            for duty_ref in unit.duty_refs
        )
    ):
        raise Stage1CompositionError("STAGE1_COMPOSITION_LAYOUT_ID_STOP")
    ordered_subjective_claim_ids = _unique(
        owner_ref
        for duty in artifact.composition_duty_rows
        if duty.layer == "LAYER_2"
        for owner_ref in duty.basis_projection_refs
    )
    sealed_unit_plan_rows = tuple(
        (
            unit.unit_ref,
            unit.layer,
            unit.duty_refs,
            unit.sentence_job_refs,
            unit.basis_anchor_refs,
            unit.clause_plan_refs,
            unit.frame_refs,
            unit.atomic_head_refs,
            unit.lexical_family_refs,
            unit.source_group_refs,
            unit.reference_state_refs,
            unit.link_plan_refs,
            unit.morphology_plan_refs,
            unit.clause_ir_refs,
        )
        for unit in artifact.sentence_units
    )
    return _final_typed_ref(
        CMEE_STAGE1_COMPOSITION_LAYOUT_ID_VERSION,
        "composition-layout",
        (
            artifact.projection_ref,
            ordered_subjective_claim_ids,
            artifact.discourse_arc,
            artifact.layout_preference_seed,
            artifact.full_duty_refs,
            artifact.required_duty_refs,
            artifact.suppressed_duty_rows,
            artifact.suppressed_claim_rows,
            tuple(row.reference_state for row in ordered_clause_rows),
            sealed_unit_plan_rows,
            artifact.response_object_expression_rows,
        ),
    )


def _artifact_composition_candidate_ref(
    artifact: NormalizedDraftArtifact,
    profile: DiscoursePreferenceProfile,
    signature: str,
) -> str:
    """Project the canonical final-registry candidate identity."""

    if (
        type(artifact) is not NormalizedDraftArtifact
        or type(profile) is not DiscoursePreferenceProfile
        or type(signature) is not str
        or not signature
        or signature != _composition_signature(artifact)
    ):
        raise Stage1CompositionError("STAGE1_COMPOSITION_CANDIDATE_ID_STOP")
    _profile_key(profile)
    normalized_sha256 = hashlib.sha256(
        canonical_normalized_bytes(artifact)
    ).hexdigest()
    return _final_typed_ref(
        CMEE_STAGE1_ARTIFACT_COMPOSITION_CANDIDATE_ID_VERSION,
        "artifact-composition-candidate",
        (
            artifact.projection_ref,
            _composition_layout_ref(artifact),
            signature,
            CMEE_STAGE1_NORMAL_FORM_VERSION,
            normalized_sha256,
            profile,
        ),
    )


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


def _normal_form_visible_equivalence_representative_key(
    artifact: NormalizedDraftArtifact,
) -> Tuple[Any, ...]:
    """Choose one typed normal-form witness without enumeration-order state.

    A material grouping seed may normalize to the same visible units as the
    canonical singleton seed.  Prefer the witness that needed no repair, then
    the seed's typed group-cardinality shape.  Duty and candidate identifiers
    are deliberately excluded from this key.
    """

    if type(artifact) is not NormalizedDraftArtifact:
        raise Stage1CompositionError("STAGE1_PROFILE_INPUT_STOP")
    return (
        len(artifact.repair_trace_rows),
        sum(
            len(row.repaired_owner_refs)
            for row in artifact.repair_trace_rows
        ),
        tuple(
            len(group.ordered_duty_refs)
            for group in artifact.layout_preference_seed.layer1_group_rows
        ),
        tuple(
            len(group.ordered_duty_refs)
            for group in artifact.layout_preference_seed.layer2_group_rows
        ),
    )


def _rank_v2_profiled_members(
    profiled_members: Sequence[
        Tuple[
            NormalizedDraftArtifact,
            DiscoursePreferenceProfile,
            JapaneseLocalPreferenceProfile,
            str,
        ]
    ],
) -> Tuple[
    Tuple[
        NormalizedDraftArtifact,
        DiscoursePreferenceProfile,
        JapaneseLocalPreferenceProfile,
        str,
    ],
    ...,
]:
    """Rank typed profiles, dedupe visible equivalence, never ID-tiebreak."""

    members = tuple(profiled_members)
    if not members:
        raise Stage1CompositionError("NO_VALID_SURFACE")
    classes: dict[
        bytes,
        Tuple[
            NormalizedDraftArtifact,
            DiscoursePreferenceProfile,
            JapaneseLocalPreferenceProfile,
            str,
        ],
    ] = {}
    for member in members:
        if (
            type(member) is not tuple
            or len(member) != 4
            or type(member[0]) is not NormalizedDraftArtifact
            or type(member[1]) is not DiscoursePreferenceProfile
            or type(member[2]) is not JapaneseLocalPreferenceProfile
            or type(member[3]) is not str
            or not member[3]
        ):
            raise Stage1CompositionError("STAGE1_LOCAL_PROFILE_INPUT_STOP")
        visible_key = _visible_key(member[0])
        prior = classes.get(visible_key)
        member_key = (
            _profile_key(member[1]),
            _japanese_local_profile_key(member[2]),
        )
        if prior is None:
            classes[visible_key] = member
            continue
        prior_key = (
            _profile_key(prior[1]),
            _japanese_local_profile_key(prior[2]),
        )
        if member_key < prior_key:
            classes[visible_key] = member
        elif member_key == prior_key:
            member_representative_key = (
                _normal_form_visible_equivalence_representative_key(
                    member[0]
                )
            )
            prior_representative_key = (
                _normal_form_visible_equivalence_representative_key(
                    prior[0]
                )
            )
            if member_representative_key < prior_representative_key:
                classes[visible_key] = member
            elif (
                member_representative_key == prior_representative_key
                and canonical_normalized_bytes(member[0])
                != canonical_normalized_bytes(prior[0])
            ):
                raise Stage1CompositionError(
                    "IDIOMATIC_PREFERENCE_NONUNIQUE_STOP"
                )

    unique_members = tuple(classes.values())
    typed_key_to_visible: dict[Tuple[Tuple[int, ...], Tuple[int, ...]], bytes] = {}
    for member in unique_members:
        typed_key = (
            _profile_key(member[1]),
            _japanese_local_profile_key(member[2]),
        )
        visible_key = _visible_key(member[0])
        prior_visible = typed_key_to_visible.get(typed_key)
        if prior_visible is not None and prior_visible != visible_key:
            raise Stage1CompositionError(
                "IDIOMATIC_PREFERENCE_NONUNIQUE_STOP"
            )
        typed_key_to_visible[typed_key] = visible_key
    return tuple(
        sorted(
            unique_members,
            key=lambda member: (
                _profile_key(member[1]),
                _japanese_local_profile_key(member[2]),
            ),
        )
    )


def _v2_qualified_owner_has_certified_source_argument(
    *,
    phase_B: Stage1SurfaceCompositionInputs,
    unit: ComposedSentenceUnit,
    clause_row: V2ClauseRealizationRow,
    frame: ClauseFrame,
    configuration: QualifiedEventStateConfiguration,
) -> bool:
    """Bind a qualified owner to the visible, source-certified predicate."""

    owner_prefix = "owner:"
    owner_suffix = f"@{CMEE_OBLIGATION_VERSION}"
    if (
        not configuration.owner_ref.startswith(owner_prefix)
        or not configuration.owner_ref.endswith(owner_suffix)
    ):
        return False
    meaning_owner_id = configuration.owner_ref[
        len(owner_prefix) : -len(owner_suffix)
    ]
    if (
        not meaning_owner_id
        or configuration.owner_ref
        != f"{owner_prefix}{meaning_owner_id}{owner_suffix}"
    ):
        return False

    source = phase_B.admitted_source
    graph = phase_B.grounded_graph
    owner_universe = getattr(source, "owner_universe", None)
    obligations = tuple(
        row
        for row in getattr(owner_universe, "obligations", ())
        if row.meaning_owner_id == meaning_owner_id
    )
    dispositions = tuple(
        row
        for row in getattr(graph, "owner_dispositions", ())
        if row.meaning_owner_id == meaning_owner_id
    )
    nodes = tuple(
        row
        for row in getattr(graph, "nodes", ())
        if (
            f"node:{row.node_id}@{CMEE_GROUNDED_GRAPH_SCHEMA_VERSION}"
            == configuration.predicate_ref
        )
    )
    if len(obligations) != 1 or len(dispositions) != 1 or len(nodes) != 1:
        return False
    obligation = obligations[0]
    disposition = dispositions[0]
    node = nodes[0]
    owner_pool_name = (
        "required_owner_refs"
        if obligation.owner_class is OwnerClass.REQUIRED
        else "active_optional_owner_refs"
    )
    if (
        disposition.owner_class is not obligation.owner_class
        or disposition.visible_authority is not VisibleAuthority.SOURCE_EXPLICIT
        or disposition.source_owner_disposition
        is not SourceOwnerDisposition.SOURCE_EXPLICIT_VISIBLE
        or node.owner_id != meaning_owner_id
        or node.node_id not in disposition.visible_claim_refs
        or node.epistemic_state is not EpistemicState.SOURCE_EXPLICIT
        or meaning_owner_id
        not in getattr(owner_universe, owner_pool_name, ())
        or meaning_owner_id not in getattr(graph, owner_pool_name, ())
        or tuple(disposition.evidence_refs) != tuple(obligation.evidence_refs)
        or tuple(node.evidence_ids) != tuple(obligation.evidence_refs)
    ):
        return False

    source_version = getattr(owner_universe, "source_version", "")
    versioned_evidence_refs = tuple(
        f"evidence:{ref}@{source_version}"
        for ref in obligation.evidence_refs
    )
    evidence_by_ref = {
        row.evidence_id: row
        for row in getattr(source, "evidence_refs", ())
    }
    if (
        not source_version
        or configuration.source_evidence_refs != versioned_evidence_refs
        or any(ref not in evidence_by_ref for ref in obligation.evidence_refs)
        or tuple(
            dict.fromkeys(
                evidence_by_ref[ref].source_span_id
                for ref in obligation.evidence_refs
            )
        )
        != obligation.source_span_ids
    ):
        return False

    source_arguments = tuple(
        binding
        for binding in frame.argument_bindings
        if binding.semantic_ref == configuration.predicate_ref
    )
    source_leaves = tuple(
        leaf
        for leaf in clause_row.source_leaves
        if leaf.semantic_ref == configuration.predicate_ref
    )
    literal_bindings = tuple(
        (binding, derivation)
        for binding, derivation in zip(
            unit.realized_semantic_bindings,
            unit.surface_derivations,
            strict=True,
        )
        if binding.semantic_ref == configuration.predicate_ref
        and derivation.derivation_kind
        is SurfaceDerivationKind.LITERAL_SUBSPAN
    )
    if (
        len(source_arguments) != 1
        or source_arguments[0].role is not ArgumentRole.PRIMARY
        or len(source_leaves) != 1
        or len(literal_bindings) != 1
    ):
        return False
    leaf = source_leaves[0]
    literal_derivation = literal_bindings[0][1]
    try:
        visible_literal = leaf.payload_utf8.decode("utf-8", "strict")
    except UnicodeDecodeError:
        return False
    return bool(
        visible_literal
        and visible_literal in unit.text
        and leaf.leaf_ref in clause_row.source_group.ordered_leaf_refs
        and leaf.source_envelope_ref == source.envelope.envelope_id
        and leaf.evidence_ref in obligation.evidence_refs
        and literal_derivation.source_or_claim_refs
        == (configuration.predicate_ref,)
        and literal_derivation.evidence_refs == (leaf.evidence_ref,)
    )


def validate_postrealizer_visible_causal_trace(
    phase_B: Stage1SurfaceCompositionInputs,
    candidate: ArtifactCompositionCandidate,
) -> str:
    """Resolve projection requirements to actual case-frame surface units."""

    if (
        type(phase_B) is not Stage1SurfaceCompositionInputs
        or type(candidate) is not ArtifactCompositionCandidate
        or candidate.sentence_units
        != candidate.normalized_artifact.sentence_units
    ):
        raise Stage1CompositionError(
            "MEANING_REALIZATION_CAUSAL_TRACE_GAP"
        )
    projection = phase_B.projection
    artifact = candidate.normalized_artifact
    try:
        _validate_phase_B(phase_B)
        expected_projection_ref = _projection_ref(projection)
        _validate_v2_normalized_grammar_seal(artifact)
        expected_candidate_ref = _artifact_composition_candidate_ref(
            artifact,
            candidate.discourse_preference_profile,
            candidate.composition_signature,
        )
        expected_discourse_profile = derive_discourse_preference_profile(
            artifact
        )
        expected_local_profile = derive_japanese_local_preference_profile(
            artifact
        )
    except Stage1CompositionError as exc:
        raise Stage1CompositionError(
            "MEANING_REALIZATION_CAUSAL_TRACE_GAP"
        ) from exc
    if (
        candidate.artifact_composition_candidate_id != expected_candidate_ref
        or type(candidate.rank) is not int
        or isinstance(candidate.rank, bool)
        or candidate.rank != 1
        or candidate.shared_variant_id != "01-primary"
        or candidate.discourse_preference_profile
        != expected_discourse_profile
        or candidate.japanese_local_preference_profile
        != expected_local_profile
    ):
        raise Stage1CompositionError(
            "MEANING_REALIZATION_CAUSAL_TRACE_GAP"
        )
    duties = artifact.composition_duty_rows
    units = candidate.sentence_units
    duty_by_ref = {row.duty_ref: row for row in duties}
    contribution_by_ref = {
        row.contribution_id: row
        for row in projection.observation_contributions
    }
    qualified_configuration_by_ref = {
        row.configuration_id: row
        for row in (
            phase_B.phase_A_authority.input_specific_meaning_structure.configurations
        )
        if type(row) is QualifiedEventStateConfiguration
    }
    clause_rows_by_duty = {
        row.duty_ref: row for row in artifact.v2_clause_rows
    }
    clause_plan_by_duty = {
        row.duty_ref: row for row in artifact.clause_plan_rows
    }
    if (
        artifact.projection_ref != expected_projection_ref
        or artifact.discourse_arc.projection_ref != expected_projection_ref
        or any(
            duty.projection_ref != expected_projection_ref
            for duty in duties
        )
        or len(duty_by_ref) != len(duties)
        or set(duty_by_ref) != set(artifact.full_duty_refs)
        or len(clause_rows_by_duty) != len(artifact.v2_clause_rows)
        or set(clause_rows_by_duty) != set(artifact.required_duty_refs)
        or len(clause_plan_by_duty) != len(artifact.clause_plan_rows)
        or set(clause_plan_by_duty) != set(artifact.required_duty_refs)
    ):
        raise Stage1CompositionError(
            "MEANING_REALIZATION_CAUSAL_TRACE_GAP"
        )

    def typed_unit_for_duty(
        duty_ref: str,
    ) -> tuple[ComposedSentenceUnit, V2ClauseRealizationRow, ClauseFrame]:
        matches = tuple(
            unit for unit in units if duty_ref in set(unit.duty_refs)
        )
        clause_row = clause_rows_by_duty.get(duty_ref)
        if len(matches) != 1 or clause_row is None:
            raise Stage1CompositionError(
                "MEANING_REALIZATION_CAUSAL_TRACE_GAP"
            )
        unit = matches[0]
        frame_matches = tuple(
            frame
            for frame in unit.clause_frames
            if frame.move_ref == clause_row.clause_ir.clause_ir_ref
            and frame.predicate_operator == clause_row.head.head_id
        )
        functional_rows = tuple(
            row
            for row in unit.surface_derivations
            if row.derivation_kind
            is SurfaceDerivationKind.PROJECTED_FUNCTIONAL_ASSET
            and row.relation_or_clause_plan_refs
        )
        if (
            clause_row.unit_ref != unit.unit_ref
            or len(frame_matches) != 1
            or not unit.clause_frames
            or clause_row.frame.frame_id not in set(unit.frame_refs)
            or clause_row.head.head_id not in set(unit.atomic_head_refs)
            or clause_row.source_group.group_ref
            not in set(unit.source_group_refs)
            or clause_row.clause_ir.clause_ir_ref
            not in set(unit.clause_ir_refs)
            or not unit.surface_derivations
            or not functional_rows
        ):
            raise Stage1CompositionError(
                "MEANING_REALIZATION_CAUSAL_TRACE_GAP"
            )
        return unit, clause_row, frame_matches[0]

    layer1_units_by_contribution: dict[str, ComposedSentenceUnit] = {}
    for trace in projection.meaning_visible_causal_trace_rows:
        if type(trace) is SelectedMeaningVisibleCausalTraceRow:
            configuration_component_refs = set(
                trace.configuration_component_refs
            )
        elif type(trace) is LimitedMeaningVisibleCausalTraceRow:
            configuration_component_refs = {trace.source_object_ref}
        else:
            raise Stage1CompositionError(
                "MEANING_REALIZATION_CAUSAL_TRACE_GAP"
            )
        for contribution_ref in trace.layer1_contribution_refs:
            contribution = contribution_by_ref.get(contribution_ref)
            matching_duties = tuple(
                duty
                for duty in duties
                if duty.layer == "LAYER_1"
                and contribution_ref in set(duty.basis_projection_refs)
            )
            if contribution is None or len(matching_duties) != 1:
                raise Stage1CompositionError(
                    "MEANING_REALIZATION_CAUSAL_TRACE_GAP"
                )
            duty = matching_duties[0]
            unit, clause_row, frame = typed_unit_for_duty(
                duty.duty_ref
            )
            try:
                (
                    expected_owner,
                    _expected_all_source_refs,
                    expected_case_frame,
                    expected_source_refs,
                ) = _v2_source_binding_for_duty(duty, phase_B)
                expected_head = select_atomic_predicate_head(
                    expected_case_frame
                )
            except Stage1CompositionError as exc:
                raise Stage1CompositionError(
                    "MEANING_REALIZATION_CAUSAL_TRACE_GAP"
                ) from exc
            frame_semantic_refs = {
                binding.semantic_ref for binding in frame.argument_bindings
            }
            ordered_frame_semantic_refs = tuple(
                binding.semantic_ref for binding in frame.argument_bindings
            )
            reciprocal_pair = _reciprocal_tension_relation_pair(
                _contributions(projection)
            )
            absorbed_reciprocal = bool(
                reciprocal_pair
                and expected_owner == reciprocal_pair[0]
                and contribution == reciprocal_pair[1]
                and set(duty.basis_projection_refs).issuperset(
                    {
                        reciprocal_pair[0].contribution_id,
                        reciprocal_pair[1].contribution_id,
                    }
                )
                and duty.relation_refs
                == _relation_refs(reciprocal_pair[0])
                and _reciprocal_tension_scalar_axes_match(
                    reciprocal_pair,
                    phase_B,
                )
                and set(artifact.discourse_arc.admitted_relation_refs)
                == {
                    *_relation_refs(reciprocal_pair[0]),
                    *_relation_refs(reciprocal_pair[1]),
                }
            )
            relation_is_typed = (
                contribution.relation_operator
                is not RelationOperator.NO_RELATION_CLAIM
                and _v2_relation_operator_for_frame(
                    clause_row.frame.frame_id
                )
                is contribution.relation_operator
                and (
                    ordered_frame_semantic_refs == expected_source_refs
                    or (
                        absorbed_reciprocal
                        and tuple(reversed(ordered_frame_semantic_refs))
                        == tuple(
                            binding.semantic_ref
                            for binding in contribution.argument_bindings
                        )
                    )
                )
            )
            predicate_is_typed = (
                (expected_owner is contribution or absorbed_reciprocal)
                and clause_row.frame == expected_case_frame
                and clause_row.head == expected_head
                and clause_row.head.frame_ref == clause_row.frame.frame_id
                and clause_row.frame.atomic_head_ref
                == clause_row.head.head_id
                and frame.predicate_operator == clause_row.head.head_id
                and set(expected_source_refs).issubset(
                    frame_semantic_refs
                )
            )
            plan = clause_plan_by_duty[duty.duty_ref]
            if type(trace) is SelectedMeaningVisibleCausalTraceRow:
                qualified_configuration = qualified_configuration_by_ref.get(
                    trace.configuration_ref
                )
                direct_visible_qualifier_refs = {
                    *frame.qualifier_refs,
                    *(
                        ref
                        for derivation in unit.surface_derivations
                        for ref in derivation.qualifier_refs
                    ),
                }
                visible_functional_asset_refs = {
                    binding.semantic_ref
                    for binding, derivation in zip(
                        unit.realized_semantic_bindings,
                        unit.surface_derivations,
                        strict=True,
                    )
                    if derivation.derivation_kind
                    is SurfaceDerivationKind.PROJECTED_FUNCTIONAL_ASSET
                }
                derivation_owner_refs = {
                    *direct_visible_qualifier_refs,
                    *visible_functional_asset_refs,
                    *(
                        ref
                        for derivation in unit.surface_derivations
                        for ref in derivation.relation_or_clause_plan_refs
                    ),
                }
                visible_qualifier_refs = set(
                    direct_visible_qualifier_refs
                )
                scalar_owner_refs: set[str] = set()
                for constraint in plan.scalar_constraint_rows:
                    if constraint.owner_ref not in configuration_component_refs:
                        continue
                    scalar_rows = tuple(
                        row
                        for row in plan.scalar_surface_realization_rows
                        if row.clause_scalar_constraint_ref
                        == constraint.clause_scalar_constraint_ref
                    )
                    if {
                        row.scalar_axis for row in scalar_rows
                    } != set(ClauseScalarAxis):
                        raise Stage1CompositionError(
                            "MEANING_REALIZATION_CAUSAL_TRACE_GAP"
                        )
                    scalar_value_by_axis = {
                        ClauseScalarAxis.POLARITY: constraint.polarity,
                        ClauseScalarAxis.MODALITY: constraint.modality,
                        ClauseScalarAxis.TIME_SCOPE: constraint.time_scope,
                    }
                    visible_scalar_rows = tuple(
                        row
                        for row in scalar_rows
                        if row.realization_mode
                        in {
                            ScalarSurfaceRealizationMode.OVERT_FUNCTIONAL_PART,
                            ScalarSurfaceRealizationMode.FUSED_IN_REGISTERED_PART,
                        }
                        and row.registered_realization_rule_ref
                        in derivation_owner_refs
                        and (
                            plan.semantic_clause_kind
                            is not SemanticClauseKind.ADMITTED_RELATION
                            or constraint.owner_ref
                            in direct_visible_qualifier_refs
                        )
                    )
                    unmarked_scalar_rows: list[
                        ScalarSurfaceRealizationRow
                    ] = []
                    for row in scalar_rows:
                        if (
                            row.realization_mode
                            is not ScalarSurfaceRealizationMode.UNMARKED_DEFAULT
                        ):
                            continue
                        value = scalar_value_by_axis[row.scalar_axis]
                        matching_assets = tuple(
                            asset
                            for asset in SCALAR_MORPHOLOGY_ASSET_REGISTRY
                            if asset.morphology_asset_id
                            == row.registered_realization_rule_ref
                            and asset.scalar_axis is row.scalar_axis
                            and value in asset.compatible_values
                            and asset.realization_mode
                            is ScalarSurfaceRealizationMode.UNMARKED_DEFAULT
                            and asset.realization_target_slot_ref is None
                            and not asset.morphemes
                        )
                        if (
                            len(matching_assets) != 1
                            or constraint.owner_ref not in frame_semantic_refs
                        ):
                            raise Stage1CompositionError(
                                "MEANING_REALIZATION_CAUSAL_TRACE_GAP"
                            )
                        unmarked_scalar_rows.append(row)
                    certified_scalar_rows = (
                        *visible_scalar_rows,
                        *unmarked_scalar_rows,
                    )
                    if certified_scalar_rows:
                        scalar_owner_refs.add(constraint.owner_ref)
                    visible_qualifier_refs.update(
                        f"{row.scalar_axis.value.lower()}:"
                        f"{scalar_value_by_axis[row.scalar_axis]}"
                        for row in certified_scalar_rows
                    )
                qualified_owner_is_certified = bool(
                    qualified_configuration is not None
                    and _v2_qualified_owner_has_certified_source_argument(
                        phase_B=phase_B,
                        unit=unit,
                        clause_row=clause_row,
                        frame=frame,
                        configuration=qualified_configuration,
                    )
                )
                certified_owner_refs = (
                    {qualified_configuration.owner_ref}
                    if qualified_configuration is not None
                    and qualified_owner_is_certified
                    else set()
                )
                typed_component_refs = {
                    *frame_semantic_refs,
                    *scalar_owner_refs,
                    *certified_owner_refs,
                }
                component_exact_cover = configuration_component_refs.issubset(
                    typed_component_refs
                )
                trace_qualifier_refs = set(trace.source_qualifier_refs)

                def visible_qualifier(prefix: str) -> bool:
                    return any(
                        ref.startswith(prefix)
                        and ref in visible_qualifier_refs
                        for ref in trace_qualifier_refs
                    )

                ordered_relation_refs = tuple(
                    binding.semantic_ref
                    for binding in contribution.argument_bindings
                )
                relation_topology_exact = (
                    relation_is_typed
                    and len(ordered_relation_refs) == 2
                    and (
                        ordered_relation_refs == expected_source_refs
                        or (
                            absorbed_reciprocal
                            and ordered_relation_refs
                            == tuple(reversed(expected_source_refs))
                        )
                    )
                    and len(set(ordered_frame_semantic_refs)) == 2
                )
                role_topology_exact = (
                    len(ordered_relation_refs) == 2
                    and len(
                        {
                            binding.role
                            for binding in contribution.argument_bindings
                        }
                    )
                    == 2
                    and (
                        ordered_relation_refs == ordered_frame_semantic_refs
                        or (
                            absorbed_reciprocal
                            and ordered_relation_refs
                            == tuple(reversed(ordered_frame_semantic_refs))
                        )
                    )
                )
                direction_exact = relation_topology_exact
                qualified_semantics_exact = bool(
                    qualified_configuration is not None
                    and qualified_configuration.predicate_ref
                    in frame_semantic_refs
                    and qualified_owner_is_certified
                    and set(trace.source_qualifier_refs).intersection(
                        direct_visible_qualifier_refs
                    )
                )
                unknown_visible = any(
                    ref.startswith("unknown:")
                    and ref in typed_component_refs
                    for ref in configuration_component_refs
                ) or any(
                    ref.endswith(":unknown")
                    and ref in direct_visible_qualifier_refs
                    for ref in trace_qualifier_refs
                )
                explicit_limit_visible = any(
                    ref.startswith(
                        ("scope:", "epistemic:", "limit:", "bounded:")
                    )
                    and ref in direct_visible_qualifier_refs
                    for ref in trace_qualifier_refs
                )
                invariant_witness = {
                    DifferenceInvariantCode.ENDPOINT_COLLAPSE: (
                        qualified_semantics_exact
                        if qualified_configuration is not None
                        else (
                            relation_topology_exact
                            and configuration_component_refs.issubset(
                                frame_semantic_refs
                            )
                        )
                    ),
                    DifferenceInvariantCode.DIRECTION_REVERSAL: (
                        direction_exact
                    ),
                    DifferenceInvariantCode.WORLD_COLLAPSE: (
                        visible_qualifier("world:")
                    ),
                    DifferenceInvariantCode.ROLE_COLLAPSE: (
                        qualified_semantics_exact
                        if qualified_configuration is not None
                        else role_topology_exact
                    ),
                    DifferenceInvariantCode.TEMPORAL_COLLAPSE: (
                        visible_qualifier("time_scope:")
                    ),
                    DifferenceInvariantCode.POLARITY_REVERSAL: (
                        visible_qualifier("polarity:")
                    ),
                    DifferenceInvariantCode.MODALITY_PROMOTION: (
                        visible_qualifier("modality:")
                    ),
                    DifferenceInvariantCode.UNKNOWN_ERASURE: (
                        unknown_visible
                    ),
                    DifferenceInvariantCode.EXPLICIT_LIMIT_ERASURE: (
                        explicit_limit_visible
                    ),
                    DifferenceInvariantCode.REQUIRED_RETENTION_ERASURE: (
                        getattr(
                            contribution.retention,
                            "value",
                            contribution.retention,
                        )
                        == "REQUIRED"
                        and getattr(duty.retention, "value", duty.retention)
                        == "REQUIRED"
                        and component_exact_cover
                    ),
                }
                meaning_is_typed = (
                    set(invariant_witness) == set(DifferenceInvariantCode)
                    and bool(trace.invariant_codes)
                    and all(
                        invariant_witness[code]
                        for code in trace.invariant_codes
                    )
                )
            else:
                meaning_is_typed = (
                    relation_is_typed
                    or configuration_component_refs.issubset(
                        frame_semantic_refs
                    )
                )
            if (
                unit.layer != "LAYER_1"
                or not predicate_is_typed
                or not meaning_is_typed
            ):
                raise Stage1CompositionError(
                    "MEANING_REALIZATION_CAUSAL_TRACE_GAP"
                )
            for carried_contribution_ref in duty.basis_projection_refs:
                carried_contribution = contribution_by_ref.get(
                    carried_contribution_ref
                )
                if carried_contribution is None:
                    raise Stage1CompositionError(
                        "MEANING_REALIZATION_CAUSAL_TRACE_GAP"
                    )
                carried_is_absorbed_reciprocal = bool(
                    reciprocal_pair
                    and carried_contribution == reciprocal_pair[1]
                    and expected_owner == reciprocal_pair[0]
                    and duty.relation_refs
                    == _relation_refs(reciprocal_pair[0])
                    and {
                        reciprocal_pair[0].contribution_id,
                        reciprocal_pair[1].contribution_id,
                    }.issubset(duty.basis_projection_refs)
                    and _reciprocal_tension_scalar_axes_match(
                        reciprocal_pair,
                        phase_B,
                    )
                    and set(artifact.discourse_arc.admitted_relation_refs)
                    == {
                        *_relation_refs(reciprocal_pair[0]),
                        *_relation_refs(reciprocal_pair[1]),
                    }
                )
                if not set(carried_contribution.semantic_refs).issubset(
                    frame_semantic_refs
                ) or not (
                    set(carried_contribution.relation_basis_refs).issubset(
                        duty.relation_refs
                    )
                    or carried_is_absorbed_reciprocal
                ):
                    continue
                prior = layer1_units_by_contribution.get(
                    carried_contribution_ref
                )
                if prior is not None and prior.unit_ref != unit.unit_ref:
                    raise Stage1CompositionError(
                        "MEANING_REALIZATION_CAUSAL_TRACE_GAP"
                    )
                layer1_units_by_contribution[carried_contribution_ref] = unit

    claims = {
        row.subjective_claim_id: row for row in projection.subjective_claims
    }
    unit_by_ref = {row.unit_ref: row for row in units}
    expression_rows_by_unit: dict[str, tuple[ResponseObjectExpression, ...]] = {
        unit.unit_ref: tuple(
            row
            for row in artifact.response_object_expression_rows
            if row.unit_ref == unit.unit_ref
        )
        for unit in units
    }

    def antecedent_reaches_layer1(
        unit_ref: str,
        allowed_layer1_refs: set[str],
        seen: set[str],
    ) -> bool:
        if unit_ref in allowed_layer1_refs:
            return True
        unit = unit_by_ref.get(unit_ref)
        if unit is None or unit_ref in seen or unit.layer != "LAYER_2":
            return False
        next_seen = {*seen, unit_ref}
        return any(
            row.antecedent_unit_ref is not None
            and antecedent_reaches_layer1(
                row.antecedent_unit_ref,
                allowed_layer1_refs,
                next_seen,
            )
            for row in expression_rows_by_unit.get(unit_ref, ())
        )

    def antecedent_visible_semantic_refs(
        unit_ref: str,
        allowed_layer1_refs: set[str],
        seen: set[str],
    ) -> set[str]:
        unit = unit_by_ref.get(unit_ref)
        if unit is None or unit_ref in seen:
            return set()
        if unit_ref in allowed_layer1_refs and unit.layer == "LAYER_1":
            return {
                *(
                    binding.semantic_ref
                    for frame in unit.clause_frames
                    for binding in frame.argument_bindings
                ),
                *(
                    ref
                    for row in unit.surface_derivations
                    if row.derivation_kind
                    is SurfaceDerivationKind.LITERAL_SUBSPAN
                    for ref in row.source_or_claim_refs
                ),
            }
        if unit.layer != "LAYER_2":
            return set()
        next_seen = {*seen, unit_ref}
        return {
            ref
            for row in expression_rows_by_unit.get(unit_ref, ())
            if row.antecedent_unit_ref is not None
            for ref in antecedent_visible_semantic_refs(
                row.antecedent_unit_ref,
                allowed_layer1_refs,
                next_seen,
            )
        }

    layer2_witness_rows: list[
        tuple[str, str, str, str, tuple[str, ...]]
    ] = []
    for claim in claims.values():
        claim_traces = tuple(
            trace
            for trace in projection.reception_visible_causal_trace_rows
            if trace.projected_claim_ref == claim.subjective_claim_id
        )
        exact_trace_cover = (
            claim_traces[0].layer1_contribution_refs
            if len(claim_traces) == 1
            else _unique(
                ref
                for trace in claim_traces
                for ref in trace.layer1_contribution_refs
            )
        )
        if (
            not claim_traces
            or exact_trace_cover
            != claim.basis_observation_contribution_refs
        ):
            raise Stage1CompositionError(
                "MEANING_REALIZATION_CAUSAL_TRACE_GAP"
            )
    for trace in projection.reception_visible_causal_trace_rows:
        claim = claims.get(trace.projected_claim_ref)
        matching_duties = tuple(
            duty
            for duty in duties
            if duty.layer == "LAYER_2"
            and duty.basis_projection_refs == (trace.projected_claim_ref,)
        )
        if (
            claim is None
            or len(matching_duties) != 1
            or not set(trace.layer1_contribution_refs).issubset(
                claim.basis_observation_contribution_refs
            )
            or not matching_duties[0].response_object_refs
            or matching_duties[0].response_object_refs
            != trace.projected_response_object_refs
            or any(
                ref not in layer1_units_by_contribution
                for ref in trace.layer1_contribution_refs
            )
        ):
            raise Stage1CompositionError(
                "MEANING_REALIZATION_CAUSAL_TRACE_GAP"
            )
        duty = matching_duties[0]
        unit, clause_row, frame = typed_unit_for_duty(duty.duty_ref)
        _v2_validate_layer2_reception_morphology(
            duty,
            phase_B,
            clause_row.morphology_plan,
        )
        try:
            (
                expected_owner,
                _expected_all_source_refs,
                expected_case_frame,
                expected_source_refs,
            ) = _v2_source_binding_for_duty(duty, phase_B)
            expected_head = select_atomic_predicate_head(
                expected_case_frame
            )
        except Stage1CompositionError as exc:
            raise Stage1CompositionError(
                "LIMITED_RECEPTION_CAPABILITY_GAP_STOP"
                if projection.projection_branch
                is SubjectiveProjectionBranch.LIMITED
                else "MEANING_REALIZATION_CAUSAL_TRACE_GAP"
            ) from exc
        plan = clause_plan_by_duty[duty.duty_ref]
        expressions = tuple(
            row
            for row in expression_rows_by_unit.get(unit.unit_ref, ())
            if row.clause_plan_ref == plan.clause_plan_ref
        )
        emlis_rows = tuple(
            row
            for row in unit.surface_derivations
            if row.derivation_kind
            is SurfaceDerivationKind.REGISTERED_EMLIS_LEXEME
            and row.emlis_owner_ref == CMEE_STAGE1_EMLIS_OWNER_REF
        )
        if (
            unit.layer != "LAYER_2"
            or expected_owner is not claim
            or clause_row.frame != expected_case_frame
            or clause_row.head != expected_head
            or len(expressions) != 1
            or not set(expected_source_refs).issubset(
                {
                    binding.semantic_ref
                    for binding in frame.argument_bindings
                }
                | set(expressions[0].basis_semantic_refs)
            )
            or not set(expressions[0].basis_semantic_refs).issubset(
                set(trace.projected_response_object_refs)
            )
            or not expressions[0].basis_semantic_refs
            or not emlis_rows
            or frame.predicate_operator != clause_row.head.head_id
        ):
            raise Stage1CompositionError(
                "LIMITED_RECEPTION_CAPABILITY_GAP_STOP"
                if projection.projection_branch
                is SubjectiveProjectionBranch.LIMITED
                else "MEANING_REALIZATION_CAUSAL_TRACE_GAP"
            )
        expression = expressions[0]
        try:
            expected_expression_asset = _expression_asset(
                duty,
                plan,
                expected_owner,
                phase_B,
            )
        except Stage1CompositionError as exc:
            raise Stage1CompositionError(
                "LIMITED_RECEPTION_CAPABILITY_GAP_STOP"
                if projection.projection_branch
                is SubjectiveProjectionBranch.LIMITED
                else "MEANING_REALIZATION_CAUSAL_TRACE_GAP"
            ) from exc
        expression_asset_segments = tuple(
            (
                clause_row.linearized_clause.text[
                    binding.surface_scalar_start : binding.surface_scalar_end
                ],
                binding,
                derivation,
            )
            for binding, derivation in zip(
                clause_row.linearized_clause.realized_semantic_bindings,
                clause_row.linearized_clause.surface_derivations,
                strict=True,
            )
            if binding.semantic_ref
            == expected_expression_asset.expression_asset_id
            and derivation.derivation_kind
            is SurfaceDerivationKind.PROJECTED_FUNCTIONAL_ASSET
        )
        matching_registered_modifier_rows = tuple(
            row
            for row in V2_SOURCE_FUNCTIONAL_MODIFIER_REGISTRY
            if row.frame_ref == clause_row.frame.frame_id
            and row.atomic_surface
            == expected_expression_asset.predicate_lexemes[0]
        )
        modifier_expression_segments = tuple(
            (
                clause_row.linearized_clause.text[
                    binding.surface_scalar_start : binding.surface_scalar_end
                ],
                binding,
                derivation,
            )
            for binding, derivation in zip(
                clause_row.linearized_clause.realized_semantic_bindings,
                clause_row.linearized_clause.surface_derivations,
                strict=True,
            )
            if len(matching_registered_modifier_rows) == 1
            and binding.semantic_ref
            == matching_registered_modifier_rows[0].modifier_id
            and derivation.derivation_kind
            is SurfaceDerivationKind.PROJECTED_FUNCTIONAL_ASSET
        )
        base_modifier_surface_is_exact = bool(
            expected_expression_asset.reception_projection_branch is None
            and not expression_asset_segments
            and len(matching_registered_modifier_rows) == 1
            and len(modifier_expression_segments) == 1
            and modifier_expression_segments[0][0]
            == expected_expression_asset.predicate_lexemes[0]
        )
        if (
            clause_row.selected_expression_asset_ref
            != expected_expression_asset.expression_asset_id
            or (
                not base_modifier_surface_is_exact
                and (
                    len(expression_asset_segments) != 1
                    or expression_asset_segments[0][0]
                    != expected_expression_asset.predicate_lexemes[0]
                )
            )
        ):
            raise Stage1CompositionError(
                "LIMITED_RECEPTION_CAPABILITY_GAP_STOP"
                if projection.projection_branch
                is SubjectiveProjectionBranch.LIMITED
                else "MEANING_REALIZATION_CAUSAL_TRACE_GAP"
            )
        projected_objects = tuple(
            row
            for row in unit.surface_derivations
            if row.derivation_kind
            is SurfaceDerivationKind.PROJECTED_RESPONSE_OBJECT
        )
        allowed_layer1_refs = {
            layer1_units_by_contribution[ref].unit_ref
            for ref in trace.layer1_contribution_refs
        }
        layer1_visible_refs = {
            semantic_ref
            for unit_ref in allowed_layer1_refs
            for semantic_ref in antecedent_visible_semantic_refs(
                unit_ref,
                allowed_layer1_refs,
                set(),
            )
        }
        if expression.expression_mode is ResponseObjectExpressionMode.ANAPHORIC:
            matching_projected = tuple(
                row
                for row in projected_objects
                if row.response_object_expression_ref
                == expression.response_object_expression_ref
                and row.antecedent_unit_ref
                == expression.antecedent_unit_ref
            )
            antecedent_visible_refs = (
                set()
                if expression.antecedent_unit_ref is None
                else antecedent_visible_semantic_refs(
                    expression.antecedent_unit_ref,
                    allowed_layer1_refs,
                    set(),
                )
            )
            response_visible = bool(
                len(matching_projected) == 1
                and expression.antecedent_unit_ref is not None
                and matching_projected[0].source_or_claim_refs
                == expression.basis_semantic_refs
                and antecedent_reaches_layer1(
                    expression.antecedent_unit_ref,
                    allowed_layer1_refs,
                    set(),
                )
                and set(expression.basis_semantic_refs).issubset(
                    antecedent_visible_refs
                )
                and set(trace.projected_response_object_refs).issubset(
                    antecedent_visible_refs | layer1_visible_refs
                )
            )
            visible_response_refs = (
                antecedent_visible_refs | layer1_visible_refs
            ).intersection(trace.projected_response_object_refs)
        else:
            matching_projected = tuple(
                row
                for row in projected_objects
                if row.response_object_expression_ref
                == expression.response_object_expression_ref
                and row.antecedent_unit_ref is None
            )
            literal_refs = {
                ref
                for row in unit.surface_derivations
                if row.derivation_kind
                is SurfaceDerivationKind.LITERAL_SUBSPAN
                for ref in row.source_or_claim_refs
            }
            response_visible = (
                expression.antecedent_unit_ref is None
                and set(expression.basis_semantic_refs).issubset(literal_refs)
                and set(trace.projected_response_object_refs).issubset(
                    literal_refs | layer1_visible_refs
                )
            )
            visible_response_refs = (
                literal_refs | layer1_visible_refs
            ).intersection(trace.projected_response_object_refs)
        direct_response_refs = {
            *expression.basis_semantic_refs,
            *(
                ref
                for row in matching_projected
                for ref in row.source_or_claim_refs
            ),
        }
        if projection.projection_branch is SubjectiveProjectionBranch.LIMITED:
            projected_response_refs = trace.projected_response_object_refs
            projected_response_ref_set = set(projected_response_refs)
            is_anaphoric = (
                expression.expression_mode
                is ResponseObjectExpressionMode.ANAPHORIC
            )
            direct_exact_cover = (
                direct_response_refs == projected_response_ref_set
            )
            if is_anaphoric:
                expected_cardinality = (
                    SourceLeafCardinality.EXACT1
                    if len(projected_response_refs) == 1
                    else SourceLeafCardinality.ORDERED_EXACT2
                    if len(projected_response_refs) == 2
                    else None
                )
                single_antecedent_refs = (
                    set()
                    if expression.antecedent_unit_ref is None
                    else antecedent_visible_semantic_refs(
                        expression.antecedent_unit_ref,
                        allowed_layer1_refs,
                        set(),
                    )
                )
                response_visible = bool(
                    len(matching_projected) == 1
                    and expression.antecedent_unit_ref
                    in allowed_layer1_refs
                    and matching_projected[0].antecedent_unit_ref
                    == expression.antecedent_unit_ref
                    and expression.basis_semantic_refs
                    == projected_response_refs
                    and matching_projected[0].source_or_claim_refs
                    == projected_response_refs
                    and expected_cardinality is not None
                    and clause_row.source_group.cardinality
                    is expected_cardinality
                    and single_antecedent_refs
                    == projected_response_ref_set
                    and antecedent_reaches_layer1(
                        expression.antecedent_unit_ref,
                        allowed_layer1_refs,
                        set(),
                    )
                    and direct_exact_cover
                )
            else:
                response_visible = bool(
                    expression.expression_mode
                    in {
                        ResponseObjectExpressionMode.EXPLICIT,
                        ResponseObjectExpressionMode.COMPOSITE,
                    }
                    and expression.antecedent_unit_ref is None
                    and not matching_projected
                    and expression.basis_semantic_refs
                    == projected_response_refs
                    and literal_refs == projected_response_ref_set
                    and direct_exact_cover
                )
            visible_response_refs = (
                projected_response_ref_set if response_visible else set()
            )
        if not response_visible:
            raise Stage1CompositionError(
                "LIMITED_RECEPTION_CAPABILITY_GAP_STOP"
                if projection.projection_branch
                is SubjectiveProjectionBranch.LIMITED
                else "MEANING_REALIZATION_CAUSAL_TRACE_GAP"
            )
        layer2_witness_rows.append(
            (
                trace.projected_claim_ref,
                trace.reception_record_ref,
                unit.unit_ref,
                expression.response_object_expression_ref,
                expected_expression_asset.expression_asset_id,
                tuple(
                    ref
                    for ref in trace.projected_response_object_refs
                    if ref in visible_response_refs
                ),
            )
        )

    if not layer2_witness_rows:
        raise Stage1CompositionError(
            "MEANING_REALIZATION_CAUSAL_TRACE_GAP"
        )
    return _ref(
        "postrealizer-visible-causal-trace-seal",
        (
            projection.tagged_projection_ref,
            projection.projection_seal_ref,
            candidate.artifact_composition_candidate_id,
            tuple(
                sorted(
                    (
                        ref,
                        unit.unit_ref,
                    )
                    for ref, unit in (
                        layer1_units_by_contribution.items()
                    )
                )
            ),
            tuple(layer2_witness_rows),
        ),
    )


def compose_stage1_from_projection(
    phase_B: Stage1SurfaceCompositionInputs,
) -> Stage1CompositionResult:
    """Sole Phase-B facade: draft, exact6 normalize, profile, reducers and rank."""

    arc = project_stage1_discourse_arc(phase_B)
    duties = _project_duties(phase_B, arc)
    seeds = _layout_seeds(duties, arc)
    axis_cardinalities = (len(seeds), 1, 1, 1)
    if (
        any(
            cardinality < 1 or cardinality > maximum
            for cardinality, (_axis, maximum) in zip(
                axis_cardinalities, V2_CANDIDATE_AXIS_MAXIMA, strict=True
            )
        )
        or len(seeds) > V2_INTERNAL_CANDIDATE_LIMIT
    ):
        raise Stage1CompositionError("CANDIDATE_BOUND_STOP")
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
            derive_japanese_local_preference_profile(normalized),
            signature,
        )
        for _member_bytes, normalized, signature in stage_a.values()
    )
    projected_applicability_masks = tuple(
        tuple(
            getattr(profile, field) is not ProfileFit.NOT_APPLICABLE
            for field in PROFILE_RULE_REGISTRY
        )
        for _normalized, profile, _local_profile, _signature in profiled_members
    )
    if not projected_applicability_masks or any(
        mask != applicability_mask for mask in projected_applicability_masks
    ):
        raise Stage1CompositionError("STAGE1_PROFILE_APPLICABILITY_STOP")
    ordered = _rank_v2_profiled_members(profiled_members)
    candidates = tuple(
        ArtifactCompositionCandidate(
            artifact_composition_candidate_id=(
                _artifact_composition_candidate_ref(
                    normalized,
                    profile,
                    signature,
                )
            ),
            composition_signature=signature,
            rank=index + 1,
            shared_variant_id=(
                "01-primary" if index == 0 else "02-alternate"
            ),
            normalized_artifact=normalized,
            discourse_preference_profile=profile,
            sentence_units=normalized.sentence_units,
            japanese_local_preference_profile=local_profile,
        )
        for index, (normalized, profile, local_profile, signature) in enumerate(
            ordered[:V2_EMITTED_CANDIDATE_LIMIT]
        )
    )
    if not candidates:
        raise Stage1CompositionError("NO_VALID_SURFACE")
    if len(candidates) > V2_EMITTED_CANDIDATE_LIMIT:
        raise Stage1CompositionError("CANDIDATE_BOUND_STOP")
    visible_trace_seal_ref = validate_postrealizer_visible_causal_trace(
        phase_B, candidates[0]
    )
    return Stage1CompositionResult(
        LANGUAGE_CORE_IDENTITY,
        arc,
        len(stage_a),
        candidates,
        candidates[0],
        visible_trace_seal_ref,
    )


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
    reception_profile_rows = tuple(
        row
        for row in EXPRESSION_ASSET_REGISTRY
        if row.reception_projection_branch is not None
    )
    reception_profile_keys = tuple(
        (
            row.reception_projection_branch,
            row.reception_act_refs,
            row.reception_content_kind,
            row.reception_subjective_mode,
            row.reception_subjective_operator,
            row.reception_semantic_operators,
            row.reception_appraisal_dimension,
            row.reception_appraisal_operation,
            row.reception_relational_position_kind,
            row.reception_stance_operator,
            row.reception_relational_commitment,
            row.reception_relational_closure,
        )
        for row in reception_profile_rows
    )
    if (
        len(expression_ids) != len(set(expression_ids))
        or len(reception_profile_rows) != 5
        or len(reception_profile_keys) != len(set(reception_profile_keys))
        or any(
            not row.predicate_lexemes
            or any(
                not token
                or any(mark in token for mark in ("。", "！", "？", "\n", "\r"))
                for token in row.predicate_lexemes
            )
            for row in EXPRESSION_ASSET_REGISTRY
        )
        or any(
            row.semantic_clause_kind
            is not SemanticClauseKind.SUBJECTIVE_PREDICATE
            or len(row.reception_act_refs) != 1
            or row.reception_content_kind is None
            or row.reception_subjective_mode is None
            or row.reception_subjective_operator is None
            or not row.reception_semantic_operators
            or row.reception_semantic_operators
            != tuple(
                sorted(
                    set(row.reception_semantic_operators),
                    key=lambda value: value.value,
                )
            )
            or "、" in row.predicate_lexemes[0]
            or not any(
                marker in row.predicate_lexemes[0]
                for marker in ("ず", "ではなく")
            )
            or (
                row.reception_content_kind
                is SubjectiveContentKind.APPRAISAL
                and (
                    row.reception_appraisal_dimension is None
                    or row.reception_appraisal_operation is None
                    or any(
                        value is not None
                        for value in (
                            row.reception_relational_position_kind,
                            row.reception_stance_operator,
                            row.reception_relational_commitment,
                            row.reception_relational_closure,
                        )
                    )
                )
            )
            or (
                row.reception_content_kind
                is SubjectiveContentKind.RELATIONAL_POSITION
                and (
                    row.reception_appraisal_dimension is not None
                    or row.reception_appraisal_operation is not None
                    or row.reception_relational_position_kind is None
                    or row.reception_stance_operator is None
                    or row.reception_relational_commitment is None
                    or row.reception_relational_closure is None
                )
            )
            for row in reception_profile_rows
        )
        or any(
            row.reception_projection_branch is None
            and any(
                value
                for value in (
                    row.reception_act_refs,
                    row.reception_content_kind,
                    row.reception_subjective_mode,
                    row.reception_subjective_operator,
                    row.reception_semantic_operators,
                    row.reception_appraisal_dimension,
                    row.reception_appraisal_operation,
                    row.reception_relational_position_kind,
                    row.reception_stance_operator,
                    row.reception_relational_commitment,
                    row.reception_relational_closure,
                )
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
    "ai/services/ai_inference/cocolon_meaning_experience_engine/emlis_input_specific_meaning.py",
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


# This literal exact-69 inventory is deliberately independent of dataclass
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
    ("EmlisStage1Projection", "response-v2", "schema_version=exact1 projection_id=exact1 projection_preimage_ref=exact1 projection_seal_ref=exact1 projection_branch=exact1 tagged_projection_ref=exact1 meaning_visible_causal_trace_rows=1..N reception_visible_causal_trace_rows=1..4 grounded_graph_ref=exact1 parent_observation_duty_ref=exact1 parent_reception_duty_ref=exact1 interpretation_candidates=1..N meaning_field=exact1 observation_contributions=1..N subjective_claims=1..4 ordered_observation_refs=1..N ordered_subjective_refs=1..4 retained_reception_act_ids=1..N observation_depth_class=exact1 subjective_depth_class=exact1 temperature_class=exact1 reception_style_policy_ref=exact1 emlis_value_policy_ref=exact1 composition_policy_ref=exact1 low_level_grammar_policy_ref=exact1 subjective_responsibility_rows=1..N subjective_opportunity_rows=1..N subjective_facet_suppression_rows=exact0 subjective_basis_binding_rows=1..N source_qualifier_binding_rows=1..N policy_basis_binding_rows=0..N policy_application_rows=0..N", ("FULL_ROW_TABLE_EXACT_COVER", "SUBJECTIVE_DEPTH_POST_CLAIM_ONLY", "FINAL_POST_SELECTION_SEAL_BOUND"), "FINAL_PROJECTION_SEAL"),
    ("ReadingConsequence", "meaning-consequence-v1", "selected_reading_ref=exact1 input_specificity_evidence_ref=exact1 whole_reading_consequence_refs=1..N changed_whole_reading_codes=1..N response_consequence_requirement_codes=exact4 source_constraint_refs=1..N", ("POST_SELECTION_ONLY", "NO_RECEPTION_FIELDS"), "INPUT_SPECIFIC_MEANING_OWNER"),
    ("SealedEmlisProvisionalReading", "sealed-reading-v1", "selected_reading_ref=exact1 reading_consequence_ref=exact1", ("FULL_RECORD_REF_CLOSURE",), "POST_SELECTION_RESPONSE_ADAPTER"),
    ("MeaningBoundReceptionProposition", "meaning-reception-v1", "schema_version=exact1 reception_id=exact1 selected_reading_ref=exact1 reception_function=exact1 responsibility_kind=exact1 subjective_mode=exact1 contribution_kind=exact1 response_object_refs=1..N preserved_difference_refs=1..N optional_affect=0..1 optional_stance=0..1 reading_status=exact1 subjective_assertion_modality=exact1", ("AFFIRMATIVE_OR_COUNTERPOSITION", "SELECTED_READING_EXACT_BIND"), "POST_SELECTION_RESPONSE_ADAPTER"),
    ("MeaningBoundReceptionSet", "meaning-reception-set-v1", "schema_version=exact1 selected_reading_ref=exact1 reading_consequence_ref=exact1 subjective_depth=exact1 proposition_refs=1..4 affirmative_contribution_refs=1..4 optional_counterposition_refs=0..3", ("DISJOINT_UNION_EXACT_COVER", "SUBJECTIVE_DEPTH_CARDINALITY"), "POST_SELECTION_RESPONSE_ADAPTER"),
    ("BoundedLimitedReception", "bounded-limited-reception-v1", "schema_version=exact1 limited_outcome_ref=exact1 bound_layer1_contribution_refs=1..N foreground_source_object_refs=1..N retained_qualifier_refs=0..N subjective_depth=FOCUSED proposition_ref=exact1 contribution_kind=AFFIRMATIVE_RECEPTION_CONTRIBUTION", ("NO_FAKE_SELECTED_READING", "SOURCE_BOUND_EXACT1"), "POST_SELECTION_RESPONSE_ADAPTER"),
    ("Stage1SubjectivePlanningInputs", "phase-a-v2", "admitted_source=exact1 grounded_graph=exact1 grounded_plan=exact1 parent_plan=exact1 premeaning_inputs=exact1 grounded_situation_view=exact1 foreground_scope_derivation=exact1 foreground_scope_disposition=exact1 input_specific_meaning_structure=exact1 allowed_reception_opportunity_envelope=exact1 projection_preimage_ref=exact1 reading_consequence_records=0..1 sealed_emlis_provisional_reading_records=0..1 meaning_bound_reception_proposition_records=0..4 meaning_bound_reception_set_records=0..1 bounded_limited_reception_records=0..1 bounded_limited_subjective_proposition_records=0..1 projection_seal_ref=exact1 interpretation_candidate_rows=1..N meaning_field=exact1 observation_contribution_rows=1..N retained_reception_act_rows=1..N material_unknown_refs=0..N observation_depth_class=exact1 temperature_class=exact1 reception_style_policy_ref=exact1 emlis_value_policy_ref=exact1 contribution_to_candidate_ref_map=1..N resolved_grounded_frame_by_candidate_ref=1..N relation_endpoint_grounded_candidate_ref_by_binding_key=0..N qualifier_value_by_candidate_scope_axis_key=1..N construction_registry_snapshot=exact1 expression_asset_registry_snapshot=exact1 response_object_registry_snapshot=exact1 functional_asset_registry_snapshot=exact1 participant_asset_registry_snapshot=exact1 structural_asset_registry_snapshot=exact1 profile_rule_registry_snapshot=exact1", ("PREMEANING_RECEPTION_TYPE_SPLIT", "FOREGROUND_SCOPE_DERIVED_BEFORE_RECEPTION", "IM02_STRUCTURE_DERIVED_BEFORE_RECEPTION", "IM04_BRANCH_CARDINALITY_EXACT", "FULL_DOMAIN_FROZEN_MAPS"), "RESPONSE_PHASE_A_ADAPTER"),
    ("Stage1SurfaceCompositionInputs", "phase-b-v1", "phase_A_authority=exact1 admitted_source=exact1 grounded_graph=exact1 grounded_plan=exact1 parent_plan=exact1 projection=exact1 resolved_grounded_frame_by_candidate_ref=1..N relation_endpoint_grounded_candidate_ref_by_binding_key=0..N qualifier_value_by_candidate_scope_axis_key=1..N addressee_deictic_context=exact1 section_speaker_owner_ref=0..1 construction_registry_snapshot=exact1 expression_asset_registry_snapshot=exact1 response_object_registry_snapshot=exact1 functional_asset_registry_snapshot=exact1 participant_asset_registry_snapshot=exact1 structural_asset_registry_snapshot=exact1 profile_rule_registry_snapshot=exact1", ("PHASE_A_BYTES_EXACT_MATCH", "FINAL_PROJECTION_EXACT1", "PHASE_A_EXACT38_AUTHORITY"), "RESPONSE_PHASE_B_ADAPTER"),
    ("EmlisSubjectiveMeaningPlan", "meaning-plan-v1", "projection_preimage_ref=exact1 projection_seal_ref=exact1 projection_branch=exact1 tagged_projection_ref=exact1 meaning_visible_causal_trace_rows=1..N reception_visible_causal_trace_rows=1..4 subjective_claim_rows=1..4 thought_support_status=exact1 content_bearing_thought_claim_refs=0..N retained_reception_act_refs=1..N subjective_responsibility_rows=1..N subjective_opportunity_rows=1..N responsibility_coverage_rows=1..N subjective_basis_binding_rows=1..N source_qualifier_binding_rows=1..N policy_basis_binding_rows=0..N policy_application_rows=0..N subjective_facet_suppression_rows=exact0", ("REQUEST_LOCAL_VIEW_NOT_ARTIFACT", "OPPORTUNITY_PARTITION_EXACT_COVER", "NORMAL_LIMITED_EXHAUSTIVE_TAG"), "SUBJECTIVE_MEANING_PROJECTOR"),
    ("SubjectiveResponsibilityRow", "responsibility-v1", "responsibility_ref=exact1 responsibility_kind=exact1 owner_component_refs=1..N retained_reception_act_refs=1..N", ("CLOSED_EXACT4_KIND",), "RESPONSIBILITY_PROJECTOR"),
    ("SubjectiveOpportunityRow", "opportunity-v1", "opportunity_key=exact1 responsibility_refs=1..N content_kind=exact1 content=exact1 specificity_key=exact1", ("ROW_REF_FREE_CONTENT",), "OPPORTUNITY_ENUMERATOR"),
    ("SubjectiveFacetSuppressionRow", "facet-suppression-v1", "suppressed_opportunity_key=exact1 reason=exact1 absorbed_by_selected_opportunity_key=0..1", ("NONMATERIAL_HAS_NO_ABSORBER",), "NONSELECTED_OPPORTUNITY_PARTITION"),
    ("Stage1DiscourseArcView", "arc-v1", "arc_ref=exact1 projection_ref=exact1 nucleus_owner_refs=1..N supporting_owner_refs=0..N admitted_relation_refs=0..N dependency_rows=1..N root_owner_refs=1..N unresolved_or_residue_refs=0..N terminal_owner_refs=1..N layer2_response_target_refs=1..N", ("FULL_ARC_TOTAL_PROJECTION",), "DISCOURSE_ARC_PROJECTOR"),
    ("ArcDependencyRow", "arc-dependency-v1", "arc_dependency_ref=exact1 predecessor_owner_ref=exact1 successor_owner_ref=exact1 dependency_kind=exact1 source_relation_ref=0..1", ("SOURCE_RELATION_IFF_ADMITTED_RELATION",), "ARC_DEPENDENCY_PROJECTOR"),
    ("CompositionDutyView", "duty-v1", "duty_ref=exact1 projection_ref=exact1 layer=exact1 sentence_job=exact1 basis_projection_refs=1..N relation_refs=0..1 response_object_refs=0..N retention=exact1", ("CLOSED_OWNER_TO_JOB_PRECEDENCE",), "COMPOSITION_DUTY_PROJECTOR"),
    ("DutySuppressionRow", "suppression-v1", "duty_ref=exact1 reason=exact1 absorbed_by_duty_ref=0..1", ("NONMATERIAL_HAS_NO_ABSORBER",), "VISIBILITY_PARTITION_PROJECTOR"),
    ("ClaimSuppressionRow", "suppression-v1", "subjective_claim_ref=exact1 reason=exact1 absorbed_by_subjective_claim_ref=0..1", ("FULLY_SUPPRESSED_CLAIMS_ONLY",), "VISIBILITY_PARTITION_PROJECTOR"),
    ("V2ClauseReferenceStateBundle", "reference-bundle-v2", "state_ref=exact1 subject_state=0..1 object_state=exact1 response_object_expression=exact1", ("SUBJECT_AND_OBJECT_STATE_INDEPENDENT", "R03_EXACT1_R04_IMMEDIATE_ORDERED_EXACT2"), "REFERENCE_BUNDLE_PROJECTOR"),
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
    ("ArtifactCompositionCandidate", "candidate-v1", "candidate_id=exact1 projection_ref=exact1 composition_signature=exact1 rank=exact1 shared_variant_id=exact1 sealed_plan=exact1 sentence_units=2..9 normal_form_version=exact1 normal_form_applied=exact_true correctable_defect_rows=exact0 discourse_preference_profile=exact1 japanese_local_preference_profile=exact1", ("EMITTED_EXACT1_TO_2", "SELECTED_RANK1_PRIMARY_VARIANT"), "EMITTED_CANDIDATE_PROJECTOR"),
    ("DiscoursePreferenceProfile", "profile-v1", "information_flow_fit=exact1 concrete_before_abstract_fit=exact1 sentence_load_fit=exact1 topic_transition_fit=exact1 referent_continuity_fit=exact1 relation_realization_fit=exact1 subjective_sequence_fit=exact1 terminal_fit=exact1 profile_evidence_rows=8..N", ("EXACT8_TOTAL_REDUCER",), "PROFILE_PROJECTOR"),
    ("ProfileEvidenceRow", "profile-v1", "profile_evidence_ref=exact1 profile_field=exact1 rule_kind=exact1 evidence_owner_refs=1..N preferred_form_ref=exact1 observed_form_ref=exact1 result=exact1", ("FIELD_RULE_EXACT_PAIR",), "PROFILE_EVIDENCE_PROJECTOR"),
    ("GrammaticalShapeKey", "grammar-v1", "semantic_clause_kind=exact1 sentence_job=exact1 required_argument_roles=1..N grammatical_role_assignment_rule=exact1 predicate_valency=exact1 admitted_relation_operator=exact1 scalar_shape_rows=1..N syntactic_orientation=exact1", ("NO_RAW_TEXT_OR_CASE_ID",), "GRAMMATICAL_SHAPE_PROJECTOR"),
    ("SurfaceDerivation", "response-v2", "derivation_kind=exact1 source_or_claim_refs=0..N emlis_owner_ref=0..1 relation_or_clause_plan_refs=0..N qualifier_refs=0..N response_object_expression_ref=0..1 antecedent_unit_ref=0..1 participant_role_ref=0..1 evidence_refs=0..N rule_ref=exact1 input_scalar_ranges=0..N", ("EXACT8_KIND_OWNER_UNION",), "SURFACE_DERIVATION_PROJECTOR"),
    ("RealizedSurfaceBindingV2", "response-v2", "unit_ref=exact1 clause_plan_ref=exact1 binding_kind=exact1 source_semantic_refs=0..N subjective_claim_refs=0..N emlis_owner_ref=0..1 relation_or_clause_plan_refs=0..N qualifier_refs=0..N scalar_surface_coverage_keys=0..N response_object_expression_ref=0..1 participant_role_ref=0..1 structural_rule_ref=0..1 clause_slot_ref=exact1 surface_scalar_start=exact1 surface_scalar_end=exact1 surface_span_sha256=exact1 surface_derivation=exact1", ("EXACT8_BINDING_OWNER_UNION", "TEXT_SCALAR_EXACT_COVER"), "SURFACE_BINDING_PROJECTOR"),
    ("EmlisStage1PositiveTraceExtensionV2", "trace-v2", "schema_version=exact1 claim_domain=exact1 owner_ref=exact1 contribution_refs=0..N subjective_claim_refs=0..N basis_trace_refs=0..N interpretation_candidate_refs=0..N basis_observation_contribution_refs=0..N covered_duty_refs=1..N sentence_job_refs=1..N source_reception_act_refs=0..N value_principle_refs=0..N speaker_owner=0..1 user_fact_effect=exact0 composition_variant_id=exact1 composition_candidate_ref=exact1 composition_layout_ref=exact1 selected_stage1_artifact_ref=exact1", ("VISIBLE_UNIT_TRACE_EXACT_COPY",), "POSITIVE_TRACE_PROJECTOR"),
    ("SelectedMeaningVisibleCausalTraceRow", "visible-causal-trace-v1", "required_difference_ref=exact1 selected_reading_ref=exact1 configuration_ref=exact1 configuration_component_refs=1..N source_qualifier_refs=1..N invariant_codes=1..N layer1_contribution_refs=1..N", ("REQUIRED_DIFFERENCE_TO_ACTUAL_LAYER1",), "TAGGED_PROJECTION_TRACE_PROJECTOR"),
    ("LimitedMeaningVisibleCausalTraceRow", "visible-causal-trace-v1", "limited_outcome_ref=exact1 source_object_ref=exact1 layer1_contribution_refs=1..N", ("NO_FAKE_SELECTED_READING",), "TAGGED_PROJECTION_TRACE_PROJECTOR"),
    ("ReceptionVisibleCausalTraceRow", "visible-causal-trace-v1", "branch=exact1 meaning_outcome_ref=exact1 reading_consequence_ref=0..1 reception_record_ref=exact1 projected_claim_ref=exact1 layer1_contribution_refs=1..N response_object_refs=1..N projected_response_object_refs=1..N preserved_difference_refs=0..N", ("MEANING_AND_RECEPTION_TO_ACTUAL_LAYER2",), "TAGGED_PROJECTION_TRACE_PROJECTOR"),
    ("SelectedReadingProjectionInputs", "tagged-projection-input-v1", "common=exact1 selected_reading=exact1 reading_consequence_records=exact1 sealed_reading_records=exact1 reception_proposition_records=1..4 reception_set_records=exact1", ("NORMAL_BRANCH_ONLY", "CARRIED_RECORD_OBJECTS_ONLY"), "TAGGED_PROJECTION_DISPATCH"),
    ("LimitedProjectionInputs", "tagged-projection-input-v1", "common=exact1 limited_outcome=exact1 bounded_reception_records=exact1 subjective_proposition_records=exact1", ("LIMITED_BRANCH_ONLY", "SELECTED_READING_FIELDS_EXACT0"), "TAGGED_PROJECTION_DISPATCH"),
)

LANGUAGE_CORE_CONTENT_DERIVATION_ROWS = (
    ("AFFECT", "AFFECTIVE_RESPONSE", "FEEL_TOWARD", "EMLIS_FEELING"),
    ("APPRAISAL:ATTENTION", "ATTENTION", "ATTEND_TO", "EMLIS_APPRAISAL"),
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
    ("ComposedSentenceUnit", ("unit_ref", "layer", "duty_refs", "sentence_job_refs", "basis_anchor_refs", "clause_plan_refs", "text", "surface_text_sha256", "clause_frames", "realized_semantic_bindings", "surface_derivations", "frame_refs", "atomic_head_refs", "lexical_family_refs", "source_group_refs", "reference_state_refs", "link_plan_refs", "morphology_plan_refs", "clause_ir_refs")),
    ("V2ClauseReferenceStateBundle", ("state_ref", "subject_state", "object_state", "response_object_expression")),
    ("V2ReferenceSurfaceSpec", ("surface_ref", "reference_rule_ref", "atomic_surface", "source_cardinality", "licensed_frame_refs")),
    ("Stage1CompositionResult", ("language_core_identity", "discourse_arc", "internal_candidate_count", "ranked_candidates", "selected_candidate", "validated_visible_causal_trace_seal_ref")),
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
    if len(descriptors) != 69 or len({row[0][1] for row in descriptors}) != 69:
        raise Stage1CompositionError("LANGUAGE_CORE_CONTRACT_DESCRIPTOR_STOP")
    return (
        ("schema_version", _CONTRACT_MANIFEST_SCHEMA_VERSION),
        ("logical_contract_count", 69),
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
    ("NormalFormPhase", ("SUPPRESSION", "DEPENDENCY_PRESERVING_MERGE_SPLIT", "INFORMATION_RELATION_ORDER", "REFERENCE_SPEAKER_LINK_RECALCULATION", "GRAMMAR_BINDING_IR_LOCAL_REPAIR", "SOLE_LINEARIZATION_GRAMMAR_SEAL")),
    ("NormalFormRepairKind", ("AMBIGUOUS_ANAPHOR_TO_FULL_EXPRESSION", "OVERLOADED_EXACT2_CLAUSE_UNIT_SPLIT", "REDUNDANT_CONNECTIVE_REMOVAL", "LICENSED_TOPIC_ALTERNANT_TO_BASE_CASE")),
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
    ("SubjectiveProjectionBranch", ("NORMAL", "LIMITED")),
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
    ("selected_stage1_artifact_ref", ("CMEE_STAGE1_SELECTED_ARTIFACT_ID_VERSION", "stage1_projection_artifact_ref", "projection_seal_ref", "candidate_id", "shared_variant_id", "ordered_realized_sentence_unit_ids", "validated_visible_causal_trace_seal_ref", "CMEE_STAGE1_TRACE_EXTENSION_SCHEMA_VERSION")),
    ("tagged_projection_ref", ("CMEE_STAGE1_TAGGED_SUBJECTIVE_PROJECTION_REF_VERSION", "projection_branch", "projection_seal_ref", "canonical_full_meaning_visible_causal_trace_rows", "canonical_full_reception_visible_causal_trace_rows")),
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
    ("DEPENDENCY_PRESERVING_MERGE_SPLIT", "_v2_normal_form_phase_dependency_preserving_merge_split", "OVERLOADED_EXACT2_SPLIT_ONLY"),
    ("INFORMATION_RELATION_ORDER", "_normal_form_phase_dependency_information_order", "DEPENDENCY_AND_RELATION_DIRECTION_IMMUTABLE"),
    ("REFERENCE_SPEAKER_LINK_RECALCULATION", "_v2_normal_form_phase_reference_speaker_link_recalculation", "GROUPING_POSTSTATE_RECALCULATION"),
    ("GRAMMAR_BINDING_IR_LOCAL_REPAIR", "_v2_normal_form_phase_grammar_binding_ir_local_repair", "FRAME_COMPLEMENT_TOPIC_MORPHOLOGY_AND_EXACT4_MONOTONE_REPAIR"),
    ("SOLE_LINEARIZATION_GRAMMAR_SEAL", "_v2_normal_form_phase_sole_linearization_grammar_seal", "FINAL_TYPED_GRAMMAR_AND_DERIVATION_EXACT_COVER"),
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
    ("STAGE_B", "PROJECTION_AND_ORDERED_VISIBLE_LAYER_TEXT_DUTY_JOB_BASIS_KEY", "PROFILE_EXACT8_THEN_JAPANESE_LOCAL_EXACT7", "VISIBLE_EQUIVALENCE_DEDUPE_AND_TYPED_TIE_STOP"),
    ("RESOURCE_ENVELOPE", "LAYOUT4_X_MENTION2_X_LINK2_X_HEAD1", "INTERNAL_1_TO_16_NO_TRUNCATION", "EMITTED_1_TO_2"),
)

N2_BEHAVIOR_ROOT_SYMBOL_SET_EXACT34 = (
    (LANGUAGE_CORE_EXTERNAL_PATHS[0], (
        "CMEE_STAGE1_FINAL_LOGICAL_ID_REGISTRY",
        "validate_stage1_anti_template_registry_invariant",
    )),
    (_COMPOSITION_PATH, (
        "V2_GRAMMAR_INVENTORY",
        "validate_v2_grammar_inventory",
        "project_source_leaf_group",
        "select_source_complement_plan",
        "select_case_frame",
        "select_atomic_predicate_head",
        "project_argument_realization_plan",
        "project_reference_state",
        "project_clause_link_plan",
        "project_predicate_morphology_plan",
        "build_japanese_clause_ir",
        "linearize_japanese_clause",
        "normalize_to_normal_form",
        "derive_discourse_preference_profile",
        "compose_stage1_from_projection",
    )),
    (LANGUAGE_CORE_EXTERNAL_PATHS[1], (
        "build_subjective_planning_inputs",
        "seal_stage1_projection",
        "build_surface_composition_inputs",
        "_adapt_v2_composed_units_to_realized_units",
        "_compile_stage1_response_v2_candidate",
    )),
    (LANGUAGE_CORE_EXTERNAL_PATHS[2], (
        "_stage1_runtime_contract",
        "_build_stage1_grounded_observation_plan_for_schema",
        "_realize_cmee_experience",
        "_trace_for_lines",
        "validate_positive_realization_trace",
        "_build_text_grounded_limited_artifact_for_schema",
    )),
    (LANGUAGE_CORE_EXTERNAL_PATHS[6], (
        "derive_grounded_situation_view",
        "derive_foreground_scope_closed",
        "foreground_scope_disposition",
        "derive_difference_configuration_set",
        "derive_requirement_bundle_set",
        "issue_whole_reading_consequence_row",
    )),
)
IM03_BEHAVIOR_ROOT_SYMBOL_SET_EXACT35 = (
    *N2_BEHAVIOR_ROOT_SYMBOL_SET_EXACT34[:-1],
    (
        LANGUAGE_CORE_EXTERNAL_PATHS[6],
        (
            *N2_BEHAVIOR_ROOT_SYMBOL_SET_EXACT34[-1][1],
            "derive_input_specific_meaning_structure",
        ),
    ),
)
# The disabled historical N3 runner still reads the frozen exact28 symbol to
# prove its own immutable terminal identity before it reports the expected
# source drift.  Keep that tuple as a compatibility view; the IM01 roots and
# IM02's new exact3 meaning-owner roots live only in the exact34 identity.
N2_BEHAVIOR_ROOT_SYMBOL_SET_EXACT28 = (
    N2_BEHAVIOR_ROOT_SYMBOL_SET_EXACT34[:-1]
)
N2_IDENTITY_INFRASTRUCTURE_CHANGED_SYMBOL_SET_EXACT5 = (
    "LANGUAGE_CORE_PRODUCT_CAUSAL_OWNER_MANIFEST",
    "_validate_product_causal_owner_manifest",
    "stage1_runtime_integration_identity_payloads",
    "_language_core_source_owner_payloads",
    "language_core_identity_payloads",
)

LANGUAGE_CORE_PRODUCT_CAUSAL_OWNER_MANIFEST = (
    (_COMPOSITION_PATH, (
        "project_subjective_meaning_plan",
        "project_stage1_discourse_arc",
        "compose_stage1_from_projection",
        "normalize_to_normal_form",
        "derive_discourse_preference_profile",
        "_derive_discourse_preference_profile_with_frozen_applicability",
        "V2_GRAMMAR_INVENTORY",
        "validate_v2_grammar_inventory",
        "project_source_leaf_group",
        "select_source_complement_plan",
        "select_case_frame",
        "select_atomic_predicate_head",
        "project_argument_realization_plan",
        "project_reference_state",
        "project_clause_link_plan",
        "project_predicate_morphology_plan",
        "build_japanese_clause_ir",
        "linearize_japanese_clause",
    )),
    (LANGUAGE_CORE_EXTERNAL_PATHS[0], ("stage1_canonical_json_bytes", "stage1_subjective_forbidden_promotions", "_stage1_material_visible_value_refs", "project_stage1_projection_preimage_ref", "project_stage1_subjective_basis_binding_ref", "project_stage1_source_qualifier_binding_ref", "project_stage1_policy_basis_binding_ref", "validate_stage1_projection", "validate_stage1_sentence_unit", "validate_stage1_anti_template_registry_invariant")),
    (LANGUAGE_CORE_EXTERNAL_PATHS[1], ("project_direct_argument_bindings", "_candidate_from_direct", "_candidate_for_contribution", "resolve_candidate_for_contribution", "_qualifier_value", "resolve_qualifier_value", "build_subjective_planning_inputs", "seal_stage1_projection", "build_surface_composition_inputs", "_adapt_v2_composed_units_to_realized_units", "_compile_stage1_response_v2_candidate")),
    (LANGUAGE_CORE_EXTERNAL_PATHS[2], (
        "_ordered",
        "_planned_visible_source_ids",
        "_build_graph",
        "_build_experience_plan",
        "_stage1_runtime_contract",
        "_build_stage1_grounded_observation_plan_for_schema",
        "_realize_cmee_experience",
        "_trace_for_lines",
        "validate_positive_realization_trace",
        "_build_text_grounded_limited_artifact_for_schema",
    )),
    (LANGUAGE_CORE_EXTERNAL_PATHS[3], ("build_grounded_observation_plan", "build_final_stage1_grounded_observation_plan", "validate_grounded_observation_plan")),
    (LANGUAGE_CORE_EXTERNAL_PATHS[4], ("generate_core_text",)),
    (LANGUAGE_CORE_EXTERNAL_PATHS[5], ("build_emlis_observation_core_payload", "evaluate_emlis_observation_candidate")),
    (LANGUAGE_CORE_EXTERNAL_PATHS[6], (
        "derive_grounded_situation_view",
        "derive_foreground_scope_closed",
        "foreground_scope_disposition",
        "derive_difference_configuration_set",
        "derive_requirement_bundle_set",
        "issue_whole_reading_consequence_row",
        "derive_input_specific_meaning_structure",
    )),
)


def _validate_product_causal_owner_manifest(
    file_payloads: tuple[tuple[str, bytes], ...]
) -> None:
    expected_paths = (_COMPOSITION_PATH, *LANGUAGE_CORE_EXTERNAL_PATHS)
    expected_seed_cardinalities = (18, 10, 11, 10, 3, 1, 2, 7)
    if (
        tuple(
            path for path, _names in LANGUAGE_CORE_PRODUCT_CAUSAL_OWNER_MANIFEST
        )
        != expected_paths
        or tuple(
            len(names)
            for _path, names in LANGUAGE_CORE_PRODUCT_CAUSAL_OWNER_MANIFEST
        )
        != expected_seed_cardinalities
        or tuple(path for path, _names in IM03_BEHAVIOR_ROOT_SYMBOL_SET_EXACT35)
        != (
            LANGUAGE_CORE_EXTERNAL_PATHS[0],
            _COMPOSITION_PATH,
            LANGUAGE_CORE_EXTERNAL_PATHS[1],
            LANGUAGE_CORE_EXTERNAL_PATHS[2],
            LANGUAGE_CORE_EXTERNAL_PATHS[6],
        )
        or tuple(
            len(names)
            for _path, names in IM03_BEHAVIOR_ROOT_SYMBOL_SET_EXACT35
        )
        != (2, 15, 5, 6, 7)
        or sum(
            len(names)
            for _path, names in IM03_BEHAVIOR_ROOT_SYMBOL_SET_EXACT35
        )
        != 35
        or len(N2_IDENTITY_INFRASTRUCTURE_CHANGED_SYMBOL_SET_EXACT5) != 5
        or len(set(N2_IDENTITY_INFRASTRUCTURE_CHANGED_SYMBOL_SET_EXACT5))
        != 5
        or len(LEGACY_COMPOSITION_SEAM_SYMBOL_SET_EXACT18) != 18
        or len(set(LEGACY_COMPOSITION_SEAM_SYMBOL_SET_EXACT18)) != 18
    ):
        raise Stage1CompositionError("LANGUAGE_CORE_DEPENDENCY_SCOPE_STOP")
    payload_by_path = dict(file_payloads)
    if tuple(payload_by_path) != expected_paths:
        raise Stage1CompositionError("LANGUAGE_CORE_DEPENDENCY_SCOPE_STOP")
    for path, callable_names in LANGUAGE_CORE_PRODUCT_CAUSAL_OWNER_MANIFEST:
        if not callable_names or len(callable_names) != len(set(callable_names)):
            raise Stage1CompositionError("LANGUAGE_CORE_DEPENDENCY_SCOPE_STOP")
        try:
            tree = ast.parse(payload_by_path[path], filename=path)
        except (SyntaxError, ValueError):
            raise Stage1CompositionError(
                "LANGUAGE_CORE_DEPENDENCY_SCOPE_STOP"
            ) from None
        bound_names: list[str] = []
        for node in tree.body:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                bound_names.append(node.name)
            elif isinstance(node, ast.Assign):
                bound_names.extend(
                    target.id
                    for target in node.targets
                    if isinstance(target, ast.Name)
                )
            elif isinstance(node, ast.AnnAssign) and isinstance(
                node.target, ast.Name
            ):
                bound_names.append(node.target.id)
        for callable_name in callable_names:
            if bound_names.count(callable_name) != 1:
                raise Stage1CompositionError("LANGUAGE_CORE_DEPENDENCY_SCOPE_STOP")


def stage1_runtime_integration_identity_payloads(
    repository_root: Optional[Path] = None,
) -> Tuple[Tuple[str, bytes], ...]:
    """Return the broad exact-17 whole-file/manifest integration payloads."""

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
        (
            "normal_form_allowed_repair_exact4",
            tuple(row.value for row in NormalFormRepairKind),
        ),
        ("correctable_defect_exact8", tuple(row.value for row in CorrectableDefectKind)),
        ("layout_seed_exact5", LANGUAGE_CORE_LAYOUT_SEED_EXACT5_RULES),
        ("profile_exact8", LANGUAGE_CORE_PROFILE_EXACT8_RULES),
        (
            "japanese_local_preference_exact7",
            tuple(
                (row.preference_rule_id, row.preference_kind)
                for row in V2_JAPANESE_LOCAL_PREFERENCE_REGISTRY
            ),
        ),
        (
            "profile_reducer",
            (
                "pool_global_applicability_before_candidate_observation",
                "exact7_required_applicable_and_concrete_before_abstract_pool_global_optional",
                "not_applicable_only_for_concrete_before_abstract_and_excluded_from_lexicographic_key",
                "profile_exact8_then_local_exact7_lexicographic",
                "distinct_visible_typed_profile_tie_is_named_stop",
                "hash_id_signature_tiebreak_zero",
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
    case_frame_and_particle_manifest = (
        (
            "schema_version",
            "cocolon.cmee.v1a.stage1_case_frame_and_particle_manifest.v2",
        ),
        ("japanese_case_frames", V2_JAPANESE_CASE_FRAME_REGISTRY),
        ("case_particles", V2_CASE_PARTICLE_REGISTRY),
    )
    predicate_sense_and_atomic_head_manifest = (
        (
            "schema_version",
            "cocolon.cmee.v1a.stage1_predicate_sense_and_atomic_head_manifest.v2",
        ),
        ("predicate_senses", V2_PREDICATE_SENSE_REGISTRY),
        ("predicate_sense_frame_licenses", V2_PREDICATE_SENSE_FRAME_LICENSE_REGISTRY),
        ("atomic_predicate_heads", V2_ATOMIC_PREDICATE_HEAD_REGISTRY),
        ("lexical_families", V2_LEXICAL_FAMILY_REGISTRY),
    )
    source_complement_reference_manifest = (
        (
            "schema_version",
            "cocolon.cmee.v1a.stage1_source_complement_reference_manifest.v2",
        ),
        ("source_realization_modes", V2_SOURCE_REALIZATION_MODE_REGISTRY),
        ("complement_rules", V2_COMPLEMENT_RULE_REGISTRY),
        ("sense_complement_licenses", V2_SENSE_COMPLEMENT_LICENSE_REGISTRY),
        ("source_classifiers", V2_SOURCE_CLASSIFIER_REGISTRY),
        ("source_quote_delimiters", V2_SOURCE_QUOTE_DELIMITER_REGISTRY),
        ("reference_zero_topic_rules", V2_REFERENCE_ZERO_TOPIC_REGISTRY),
        ("reference_surfaces_exact2", V2_REFERENCE_SURFACE_REGISTRY_EXACT2),
        ("source_boundary_rows", V2_SOURCE_BOUNDARY_ROWS),
    )
    morphology_link_functional_manifest = (
        (
            "schema_version",
            "cocolon.cmee.v1a.stage1_morphology_link_functional_manifest.v2",
        ),
        ("inflection_classes", V2_INFLECTION_CLASS_REGISTRY),
        ("matrix_morphology", V2_MATRIX_MORPHOLOGY_PARADIGM_REGISTRY),
        ("clause_links", V2_CLAUSE_LINK_REGISTRY),
        ("source_functional_tokens", V2_SOURCE_FUNCTIONAL_TOKEN_REGISTRY),
        ("source_functional_modifiers", V2_SOURCE_FUNCTIONAL_MODIFIER_REGISTRY),
    )
    participant_structural_manifest = (
        (
            "schema_version",
            "cocolon.cmee.v1a.stage1_participant_structural_manifest.v2",
        ),
        ("participant_lexemes", PARTICIPANT_ASSET_REGISTRY),
        ("structural_assets", STRUCTURAL_ASSET_REGISTRY),
    )
    product_causal_owner_and_registry_digests_manifest = (
        (
            "schema_version",
            "cocolon.cmee.v1a.stage1_product_causal_owner_and_registry_digests.v3",
        ),
        ("product_causal_owner_manifest", LANGUAGE_CORE_PRODUCT_CAUSAL_OWNER_MANIFEST),
        ("im03_behavior_root_exact35", IM03_BEHAVIOR_ROOT_SYMBOL_SET_EXACT35),
        (
            "n2_identity_infrastructure_exact5",
            N2_IDENTITY_INFRASTRUCTURE_CHANGED_SYMBOL_SET_EXACT5,
        ),
        (
            "legacy_composition_seam_exact18",
            LEGACY_COMPOSITION_SEAM_SYMBOL_SET_EXACT18,
        ),
        (
            "v2_grammar_inventory_identity",
            (
                ("sha256", V2_GRAMMAR_INVENTORY_SHA256),
                ("byte_count", V2_GRAMMAR_INVENTORY_BYTE_COUNT),
                ("row_count", V2_GRAMMAR_INVENTORY_ROW_COUNT),
                ("exact_counts", V2_GRAMMAR_INVENTORY_EXACT_COUNTS),
                ("mutation_count", V2_MUTATION_CASE_COUNT),
                ("source_boundary_count", V2_SOURCE_BOUNDARY_ROW_COUNT),
            ),
        ),
        (
            "registry_manifest_sha256",
            tuple(
                (
                    name,
                    hashlib.sha256(
                        stage1_canonical_json_bytes(value)
                    ).hexdigest(),
                )
                for name, value in (
                    ("case_frame_and_particle", case_frame_and_particle_manifest),
                    (
                        "predicate_sense_and_atomic_head",
                        predicate_sense_and_atomic_head_manifest,
                    ),
                    (
                        "source_complement_reference",
                        source_complement_reference_manifest,
                    ),
                    (
                        "morphology_link_functional",
                        morphology_link_functional_manifest,
                    ),
                    ("participant_structural", participant_structural_manifest),
                    ("policy_and_closed_enum", policy_and_enum_manifest),
                    ("normal_form_and_profile", normal_form_and_profile_manifest),
                )
            ),
        ),
    )
    manifests = (
        ("language_core_contract_manifest", stage1_canonical_json_bytes(_contract_manifest())),
        ("case_frame_and_particle_manifest", stage1_canonical_json_bytes(case_frame_and_particle_manifest)),
        ("predicate_sense_and_atomic_head_manifest", stage1_canonical_json_bytes(predicate_sense_and_atomic_head_manifest)),
        ("source_complement_reference_manifest", stage1_canonical_json_bytes(source_complement_reference_manifest)),
        ("morphology_link_functional_manifest", stage1_canonical_json_bytes(morphology_link_functional_manifest)),
        ("participant_structural_manifest", stage1_canonical_json_bytes(participant_structural_manifest)),
        ("policy_and_closed_enum_manifest", stage1_canonical_json_bytes(policy_and_enum_manifest)),
        ("normal_form_and_profile_manifest", stage1_canonical_json_bytes(normal_form_and_profile_manifest)),
        ("product_causal_owner_and_registry_digests_manifest", stage1_canonical_json_bytes(product_causal_owner_and_registry_digests_manifest)),
    )
    result = (*frozen_file_payloads, *manifests)
    if len(result) != 17:
        raise Stage1CompositionError(
            "STAGE1_RUNTIME_INTEGRATION_IDENTITY_PAYLOAD_COUNT_STOP"
        )
    return tuple(result)


_LANGUAGE_CORE_NONBEHAVIOR_IDENTITY_BINDINGS = frozenset(
    {"LANGUAGE_CORE_IDENTITY", "STAGE1_RUNTIME_INTEGRATION_IDENTITY"}
)
_LANGUAGE_CORE_SOURCE_OWNER_SCHEMA_VERSION = (
    "cocolon.cmee.v1a.stage1_language_core_source_owner_ast.v1"
)


def _module_name_from_language_core_path(relative_path: str) -> str:
    prefix = "ai/services/ai_inference/"
    if not relative_path.startswith(prefix) or not relative_path.endswith(".py"):
        raise Stage1CompositionError("LANGUAGE_CORE_DEPENDENCY_SCOPE_STOP")
    return relative_path[len(prefix) : -3].replace("/", ".")


def _language_core_source_owner_payloads(
    repository_root: Optional[Path] = None,
) -> Tuple[Tuple[str, bytes], ...]:
    """Project the transitive AST closure of the declared Step-2 owners.

    The closure includes only declarations and import bindings reached from
    the explicit planner/composer/normalizer/ranker owner seeds.  Formatting,
    comments and unrelated later-step declarations are excluded, while every
    referenced same-module declaration and every referenced declaration in
    the other admitted owner modules is included fail closed.
    """

    root = repository_root or Path(__file__).resolve().parents[4]
    owner_seed_by_path = dict(LANGUAGE_CORE_PRODUCT_CAUSAL_OWNER_MANIFEST)
    expected_paths = (_COMPOSITION_PATH, *LANGUAGE_CORE_EXTERNAL_PATHS)
    activation_owner_exclusions = frozenset(
        {
            (
                LANGUAGE_CORE_EXTERNAL_PATHS[1],
                "compile_stage1_response",
            ),
            (
                LANGUAGE_CORE_EXTERNAL_PATHS[2],
                "build_text_grounded_limited_artifact",
            ),
        }
    )
    if tuple(owner_seed_by_path) != expected_paths:
        raise Stage1CompositionError("LANGUAGE_CORE_DEPENDENCY_SCOPE_STOP")
    if any(
        (relative_path, owner_name) in activation_owner_exclusions
        for relative_path, owner_names in LANGUAGE_CORE_PRODUCT_CAUSAL_OWNER_MANIFEST
        for owner_name in owner_names
    ):
        raise Stage1CompositionError("LANGUAGE_CORE_DEPENDENCY_SCOPE_STOP")

    module_name_by_path = {
        path: _module_name_from_language_core_path(path)
        for path in expected_paths
    }
    path_by_module_name = {
        module_name: path for path, module_name in module_name_by_path.items()
    }
    trees: dict[str, ast.Module] = {}
    declarations: dict[str, dict[str, ast.AST]] = {}
    bound_names_by_node: dict[str, dict[ast.AST, tuple[str, ...]]] = {}
    imports: dict[str, dict[str, tuple[Any, ...]]] = {}

    def target_names(target: ast.AST) -> tuple[str, ...]:
        if isinstance(target, ast.Name):
            return (target.id,)
        if isinstance(target, (ast.Tuple, ast.List)):
            return tuple(
                name
                for child in target.elts
                for name in target_names(child)
            )
        return ()

    for relative_path in expected_paths:
        path = root / relative_path
        if not path.is_file():
            raise Stage1CompositionError("LANGUAGE_CORE_DEPENDENCY_SCOPE_STOP")
        try:
            tree = ast.parse(path.read_bytes(), filename=relative_path)
        except (OSError, SyntaxError, ValueError):
            raise Stage1CompositionError(
                "LANGUAGE_CORE_SOURCE_OWNER_PARSE_STOP"
            ) from None
        trees[relative_path] = tree
        declaration_by_name: dict[str, ast.AST] = {}
        names_by_node: dict[ast.AST, tuple[str, ...]] = {}
        import_by_name: dict[str, tuple[Any, ...]] = {}
        for node in tree.body:
            names: tuple[str, ...] = ()
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                names = (node.name,)
            elif isinstance(node, ast.Assign):
                names = tuple(
                    name
                    for target in node.targets
                    for name in target_names(target)
                )
            elif isinstance(node, ast.AnnAssign):
                names = target_names(node.target)
            elif isinstance(node, ast.Import):
                for alias in node.names:
                    bound_name = alias.asname or alias.name.split(".", 1)[0]
                    if bound_name in import_by_name or bound_name in declaration_by_name:
                        raise Stage1CompositionError(
                            "LANGUAGE_CORE_SOURCE_OWNER_BINDING_STOP"
                        )
                    import_by_name[bound_name] = (
                        "IMPORT",
                        alias.name,
                        alias.asname or "",
                    )
            elif isinstance(node, ast.ImportFrom):
                for alias in node.names:
                    bound_name = alias.asname or alias.name
                    if bound_name in import_by_name or bound_name in declaration_by_name:
                        raise Stage1CompositionError(
                            "LANGUAGE_CORE_SOURCE_OWNER_BINDING_STOP"
                        )
                    import_by_name[bound_name] = (
                        "IMPORT_FROM",
                        node.level,
                        node.module or "",
                        alias.name,
                        alias.asname or "",
                    )
            if names:
                if len(names) != len(set(names)):
                    raise Stage1CompositionError(
                        "LANGUAGE_CORE_SOURCE_OWNER_BINDING_STOP"
                    )
                for name in names:
                    if name in declaration_by_name or name in import_by_name:
                        raise Stage1CompositionError(
                            "LANGUAGE_CORE_SOURCE_OWNER_BINDING_STOP"
                        )
                    declaration_by_name[name] = node
                names_by_node[node] = tuple(sorted(names))
        declarations[relative_path] = declaration_by_name
        bound_names_by_node[relative_path] = names_by_node
        imports[relative_path] = import_by_name

    selected_nodes = {path: set() for path in expected_paths}
    selected_imports = {path: set() for path in expected_paths}
    queue = [
        (path, owner_name, True)
        for path, owner_names in LANGUAGE_CORE_PRODUCT_CAUSAL_OWNER_MANIFEST
        for owner_name in owner_names
    ]
    seen: set[tuple[str, str]] = set()

    def resolve_import_target(
        current_path: str,
        descriptor: tuple[Any, ...],
    ) -> tuple[Optional[str], Optional[str]]:
        current_module = module_name_by_path[current_path]
        if descriptor[0] == "IMPORT":
            target_path = path_by_module_name.get(str(descriptor[1]))
            return target_path, None
        _kind, level, module, imported_name, _asname = descriptor
        if level:
            current_parts = current_module.split(".")
            if level > len(current_parts):
                return None, None
            base_parts = current_parts[:-level]
            module_parts = str(module).split(".") if module else []
            target_module = ".".join((*base_parts, *module_parts))
        else:
            target_module = str(module)
        target_path = path_by_module_name.get(target_module)
        if target_path is not None:
            return target_path, str(imported_name)
        if not module:
            submodule = ".".join(
                (*current_module.split(".")[:-1], str(imported_name))
            )
            target_path = path_by_module_name.get(submodule)
            if target_path is not None:
                return target_path, None
        return None, None

    while queue:
        relative_path, name, required_seed = queue.pop()
        key = (relative_path, name)
        if (
            key in seen
            or name in _LANGUAGE_CORE_NONBEHAVIOR_IDENTITY_BINDINGS
            or key in activation_owner_exclusions
        ):
            continue
        seen.add(key)
        node = declarations[relative_path].get(name)
        if node is not None:
            selected_nodes[relative_path].add(node)
            for referenced in {
                child.id
                for child in ast.walk(node)
                if isinstance(child, ast.Name)
                and isinstance(child.ctx, ast.Load)
            }:
                if (
                    referenced in declarations[relative_path]
                    or referenced in imports[relative_path]
                ):
                    queue.append((relative_path, referenced, False))
            for child in ast.walk(node):
                if not (
                    isinstance(child, ast.Attribute)
                    and isinstance(child.value, ast.Name)
                ):
                    continue
                descriptor = imports[relative_path].get(child.value.id)
                if descriptor is None or descriptor[0] != "IMPORT":
                    continue
                target_path, _target_name = resolve_import_target(
                    relative_path, descriptor
                )
                if target_path is not None:
                    queue.append((target_path, child.attr, False))
            continue
        descriptor = imports[relative_path].get(name)
        if descriptor is not None:
            selected_imports[relative_path].add(name)
            target_path, target_name = resolve_import_target(
                relative_path, descriptor
            )
            if target_path is not None and target_name is not None:
                queue.append((target_path, target_name, False))
            continue
        if required_seed:
            raise Stage1CompositionError("LANGUAGE_CORE_SOURCE_OWNER_SEED_STOP")

    payloads: list[tuple[str, bytes]] = []
    for relative_path in expected_paths:
        selected_node_rows = tuple(
            (
                ("bound_names", bound_names_by_node[relative_path][node]),
                (
                    "canonical_ast",
                    ast.dump(node, annotate_fields=True, include_attributes=False),
                ),
            )
            for node in sorted(
                selected_nodes[relative_path],
                key=lambda item: bound_names_by_node[relative_path][item],
            )
        )
        if not selected_node_rows:
            raise Stage1CompositionError("LANGUAGE_CORE_SOURCE_OWNER_SEED_STOP")
        selected_import_rows = tuple(
            (("bound_name", name), ("binding", imports[relative_path][name]))
            for name in sorted(selected_imports[relative_path])
        )
        owner_payload = (
            ("schema_version", _LANGUAGE_CORE_SOURCE_OWNER_SCHEMA_VERSION),
            ("relative_path", relative_path),
            ("seed_owner_names", owner_seed_by_path[relative_path]),
            ("selected_import_bindings", selected_import_rows),
            ("selected_declarations", selected_node_rows),
        )
        payloads.append(
            (
                f"language_core_source_owner_ast:{relative_path}",
                stage1_canonical_json_bytes(owner_payload),
            )
        )
    return tuple(payloads)


def language_core_identity_payloads(
    repository_root: Optional[Path] = None,
) -> Tuple[Tuple[str, bytes], ...]:
    """Return Step-2 behavior owners plus their closed manifest payloads."""

    integration_payloads = stage1_runtime_integration_identity_payloads(
        repository_root
    )
    source_owner_payloads = _language_core_source_owner_payloads(repository_root)
    result = (*source_owner_payloads, *integration_payloads[8:])
    if len(result) != 17:
        raise Stage1CompositionError("LANGUAGE_CORE_IDENTITY_PAYLOAD_COUNT_STOP")
    return tuple(result)


def _compute_framed_identity(
    domain: bytes,
    payloads: Tuple[Tuple[str, bytes], ...],
) -> str:
    material = bytearray(domain)
    for name, payload in payloads:
        name_bytes = name.encode("utf-8")
        material.extend(len(name_bytes).to_bytes(8, "big"))
        material.extend(name_bytes)
        material.extend(len(payload).to_bytes(8, "big"))
        material.extend(payload)
    return hashlib.sha256(material).hexdigest()


def compute_stage1_runtime_integration_identity(
    repository_root: Optional[Path] = None,
) -> str:
    return _compute_framed_identity(
        b"COCOLON_CMEE_STAGE1_LANGUAGE_CORE_IDENTITY_V1\x00",
        stage1_runtime_integration_identity_payloads(repository_root),
    )


def compute_language_core_identity(repository_root: Optional[Path] = None) -> str:
    return _compute_framed_identity(
        b"COCOLON_CMEE_STAGE1_LANGUAGE_CORE_IDENTITY_V2\x00",
        language_core_identity_payloads(repository_root),
    )


validate_v2_grammar_inventory()
validate_language_core_registry_invariant()
STAGE1_RUNTIME_INTEGRATION_IDENTITY = (
    compute_stage1_runtime_integration_identity()
)
LANGUAGE_CORE_IDENTITY = compute_language_core_identity()


__all__ = (
    "ArtifactCompositionCandidate",
    "ClauseArgumentRole",
    "ClauseLinkPlacement",
    "ClauseScalarAxis",
    "CONSTRUCTION_REGISTRY",
    "CorrectableDefectKind",
    "DiscoursePreferenceProfile",
    "EmlisSubjectiveMeaningPlan",
    "JapaneseCaseFrameKey",
    "IM03_BEHAVIOR_ROOT_SYMBOL_SET_EXACT35",
    "LANGUAGE_CORE_IDENTITY",
    "STAGE1_RUNTIME_INTEGRATION_IDENTITY",
    "LayoutPreferenceSeed",
    "NormalFormPhase",
    "NormalFormRepairKind",
    "NormalFormRepairTraceRow",
    "NormalizedDraftArtifact",
    "PredicateValency",
    "QualifierLookupScope",
    "QualifierValueRow",
    "ReferenceDecisionKind",
    "RelationEndpointCandidateRow",
    "RetainedReceptionActRow",
    "SOURCE_SCALAR_MORPHOLOGY_ASSET_REGISTRY",
    "SentenceJob",
    "Stage1CompositionError",
    "Stage1CompositionResult",
    "Stage1SubjectivePlanningInputs",
    "Stage1SurfaceCompositionInputs",
    "V2_ATOMIC_PREDICATE_HEAD_REGISTRY",
    "V2_CANDIDATE_AXIS_MAXIMA",
    "V2_CASE_PARTICLE_REGISTRY",
    "V2_CLAUSE_LINK_REGISTRY",
    "V2_COMPLEMENT_RULE_REGISTRY",
    "V2_GRAMMAR_INVENTORY",
    "V2_GRAMMAR_INVENTORY_BYTE_COUNT",
    "V2_GRAMMAR_INVENTORY_EXACT_COUNTS",
    "V2_GRAMMAR_INVENTORY_ROW_COUNT",
    "V2_GRAMMAR_INVENTORY_ROWS",
    "V2_GRAMMAR_INVENTORY_SHA256",
    "V2_INFLECTION_CLASS_REGISTRY",
    "V2_JAPANESE_CASE_FRAME_REGISTRY",
    "V2_JAPANESE_LOCAL_PREFERENCE_REGISTRY",
    "V2_LEXICAL_FAMILY_REGISTRY",
    "V2_MATRIX_MORPHOLOGY_PARADIGM_REGISTRY",
    "V2_MUTATION_CASE_COUNT",
    "V2_MUTATION_CASE_REGISTRY",
    "V2_PREDICATE_SENSE_FRAME_LICENSE_REGISTRY",
    "V2_PREDICATE_SENSE_REGISTRY",
    "V2_REFERENCE_ZERO_TOPIC_REGISTRY",
    "V2_REFERENCE_SURFACE_REGISTRY_EXACT2",
    "V2_SENSE_COMPLEMENT_LICENSE_REGISTRY",
    "V2_SOURCE_CLASSIFIER_REGISTRY",
    "V2_SOURCE_FUNCTIONAL_MODIFIER_REGISTRY",
    "V2_SOURCE_FUNCTIONAL_TOKEN_REGISTRY",
    "V2_SOURCE_QUOTE_DELIMITER_REGISTRY",
    "V2_SOURCE_REALIZATION_MODE_REGISTRY",
    "V2_SOURCE_BOUNDARY_ROW_COUNT",
    "V2_SOURCE_BOUNDARY_ROWS",
    "V2_SOURCE_GROUP_CARDINALITY_ROWS",
    "V2_SOURCE_MODE_CARDINALITY_ROWS",
    "V2_SOURCE_PRIMITIVE_BOUNDARY_ROWS",
    "V2_SOURCE_QUOTE_DELIMITER_BOUNDARY_ROWS",
    "V2ClauseRealizationRow",
    "V2ClauseReferenceStateBundle",
    "_artifact_composition_candidate_ref",
    "_composition_layout_ref",
    "canonical_normalized_bytes",
    "build_japanese_clause_ir",
    "compose_stage1_from_projection",
    "compute_language_core_identity",
    "compute_stage1_runtime_integration_identity",
    "derive_discourse_preference_profile",
    "derive_japanese_local_preference_profile",
    "language_core_identity_payloads",
    "normalize_to_normal_form",
    "project_scalar_surface_realization_rows",
    "project_argument_realization_plan",
    "project_clause_link_plan",
    "project_predicate_morphology_plan",
    "project_reference_state",
    "project_source_leaf_group",
    "project_stage1_discourse_arc",
    "project_subjective_meaning_plan",
    "select_eligible_constructions",
    "select_atomic_predicate_head",
    "select_case_frame",
    "select_source_complement_plan",
    "linearize_japanese_clause",
    "stage1_runtime_integration_identity_payloads",
    "validate_language_core_registry_invariant",
    "validate_v2_grammar_inventory",
)
