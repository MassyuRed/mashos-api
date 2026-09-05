# -*- coding: utf-8 -*-
from __future__ import annotations

"""Deterministic Stage 1 interpretation and Layer 1 / Layer 2 planning.

This module is deliberately side-effect free.  It does not mutate an
:class:`ExperiencePlan` or create a second final-language owner.  The active
facade keeps CMEE's typed meaning selection, then delegates all final text to
the canonical grounded sentence/reception surface and its existing gates.

Semantic planning never branches on source text or ``MeaningNode.value``.
The boundary validator replays source admission from the frozen envelope, then
binds canonical-plan rows to the graph only by owner, kind, endpoint,
grounding and exact evidence identity.  The disabled Step 4 realizer reads a
bound node value only as that node's frozen lexical role surface; it never uses
the value to select a predicate, connective, variant, or semantic move.
"""

from dataclasses import dataclass, replace
from enum import Enum
import hashlib
import hmac
import json
import re
import unicodedata
from typing import TYPE_CHECKING, Any, Iterable, Mapping, Optional, Sequence, Tuple

from emlis_ai_current_input_bundle import build_emlis_current_input_bundle
from emlis_ai_evidence_ledger_service import build_evidence_span_resolver
from emlis_ai_grounded_observation_plan import (
    FINAL_STAGE1_GROUNDED_PROJECTION_VERSION,
    GroundedHumanReceptionPlan,
    GroundedObservationPlan,
    GroundedSemanticFrame,
    build_final_stage1_grounded_observation_plan,
    build_grounded_observation_plan,
    validate_grounded_observation_plan,
)
from emlis_ai_grounded_human_reception import (
    SOURCE_GROUNDED_RECEPTION_EXPRESSION_SCHEMA_VERSION,
    GroundedHumanReceptionSurface,
    GroundedHumanReceptionSurfaceError,
    ReceptionVisibleSegmentBindingV1,
    RealizableReceptionArgumentV1,
    SourceGroundedRealizableReceptionExpressionV1,
    _bounded_source_grounded_lexemes,
    _identify_visible_segment_binding,
    _source_grounded_direction_ref,
    _source_grounded_direction_side,
    _source_grounded_relation_endpoint_nucleus_roles,
    _source_grounded_relation_endpoint_ref,
    build_grounded_reception_clause_plans,
    derive_source_grounded_nominalization_plan,
    identify_source_grounded_reception_expression,
    realize_source_grounded_human_reception,
    reception_active_moves,
    reception_effective_move_reference_mode,
    source_grounded_case_marker_for_role,
    validate_source_grounded_reception_expressions,
)
from emlis_ai_grounded_observation_gate import (
    evaluate_grounded_observation_gate,
    evaluate_grounded_surface_body_inverse,
)
from emlis_ai_grounded_sentence_surface import (
    GROUND_RECOVERY_STAGES,
    RECEPTION_SECTION_LABEL,
    GroundedSentencePlan,
    GroundedSentenceSurfaceError,
    GroundedSurfaceResult,
    SentenceSurfacePlacement,
    build_grounded_sentence_plan,
    build_reception_recovery_sentence_plan,
    realize_grounded_sentence_plan,
    realize_grounded_sentence_plan_with_human_reception,
    validate_grounded_sentence_plan,
    validate_grounded_surface_result,
)
from emlis_ai_safety_triage import (
    TRIAGE_SAFE_OBSERVATION,
    TRIAGE_SELF_DENIAL_SAFE_STATE_ANSWER,
)

from .contracts import (
    AffectCategory,
    AffectIntensity,
    AllowedReceptionOpportunityEnvelope,
    ArgumentBinding,
    ArgumentRole,
    CMEE_GROUNDED_GRAPH_SCHEMA_VERSION,
    CMEE_STAGE1_MEANING_BOUND_SUBJECTIVE_PROJECTION_SCHEMA_VERSION,
    CMEE_STAGE1_MICROGRAMMAR_POLICY_REF,
    CMEE_STAGE1_RECEPTION_ACT_MAPPING_EXACT7,
    CMEE_STAGE1_RECEPTION_ACT_STANCE_EXACT7,
    CMEE_STAGE1_RECEPTION_DISTINCTNESS_FIELDS,
    CMEE_STAGE1_RECEPTION_FORBIDDEN_SURFACE_CODES_EXACT6,
    CMEE_STAGE1_RECEPTION_MOVE_ROLE_MAPPING,
    CMEE_STAGE1_RECEPTION_REFERENCE_MAPPING_EXACT3,
    CMEE_STAGE1_RECEPTION_SAFETY_CODE_MAPPING_EXACT3,
    CMEE_STAGE1_RECEPTION_SPEAKER_MAPPING_EXACT2,
    CMEE_STAGE1_RECEPTION_STANCE_MAPPING_EXACT5,
    CMEE_STAGE1_RECEPTION_SURFACE_STRATEGY_MAPPING_EXACT5,
    CMEE_STAGE1_FINAL_LOGICAL_ID_REGISTRY,
    CMEE_STAGE1_RESPONSE_SCHEMA_VERSION,
    CMEE_STAGE1_RESPONSE_SCHEMA_VERSION_V1,
    CMEE_STAGE1_RESPONSE_SCHEMA_VERSION_V2,
    CMEE_STAGE1_VALUE_POLICY_REF,
    CMEEStage1ContractError,
    BoundedLimitedReception,
    ClauseFrame,
    EmlisInterpretationCandidate,
    EmlisAppraisalContent,
    EmlisRelationalPosition,
    EmlisMeaningField,
    EmlisStage1Projection,
    EmlisSubjectiveClaim,
    EmlisTraceClaimDomain,
    EpistemicState,
    ExperiencePlan,
    GenerationRequest,
    GroundedMeaningGraph,
    InputSpecificMeaningStructure,
    INTERPRETATION_MATRIX_EXACT13,
    INTERPRETATION_MATRIX_EXACT16,
    LimitedMeaningVisibleCausalTraceRow,
    LimitedMeaningOutcome,
    MeaningBoundReceptionProposition,
    MeaningBoundReceptionSet,
    PreMeaningGroundedInputs,
    InterpretationEpistemicState,
    InterpretationKind,
    MeaningEdge,
    MeaningFieldEntry,
    MeaningFieldSlot,
    MeaningNode,
    ObservationContributionKind,
    ObservationDepthClass,
    PlannedObservationContribution,
    RealizationCandidateSet,
    RealizedSemanticBinding,
    RealizedSentenceUnit,
    RelationOperator,
    RelationalClosure,
    RelationalCommitment,
    RelationalPositionKind,
    SourceOwnerDisposition,
    SelectedEmlisProvisionalReading,
    SelectedMeaningVisibleCausalTraceRow,
    ReceptionVisibleCausalTraceRow,
    Stage1V2UnitSeal,
    SurfaceDerivationKind,
    SemanticOperator,
    StanceOperator,
    SubjectiveDepthClass,
    SubjectiveAssertionModality,
    SubjectiveContentKind,
    SubjectiveFacetSuppressionReason,
    SubjectiveMode,
    SubjectiveOperator,
    SubjectiveOpportunityRow,
    SubjectiveProposition,
    SubjectivePropositionV2,
    SubjectiveProjectionBranch,
    SubjectiveResponsibilityKind,
    SubjectiveResponsibilityRow,
    SubjectiveSpecificity,
    SubjectiveFacetSuppressionRow,
    PolicyApplicationRow,
    TemperatureClass,
    _im04_limited_appraisal_content,
    _im04_normal_reception_binding_key,
    _im04_normal_reception_mode_contract_satisfied,
    bounded_limited_reception_id,
    canonical_limited_retained_layer1_refs,
    limited_meaning_outcome_id,
    meaning_bound_reception_set_id,
    meaning_bound_reception_id,
    project_stage1_subjective_projection_seal_ref,
    project_stage1_tagged_projection_ref,
    project_stage1_projection_preimage_ref,
    project_premeaning_source_qualifier_rows,
    project_premeaning_source_relation_rows,
    project_stage1_relation_required_qualifiers,
    project_stage1_relation_shape,
    project_stage1_source_contract_qualifiers,
    project_stage1_source_explicit_shift_endpoint_node_ids,
    recompute_stage1_identity,
    resolve_limited_reception_aggregate,
    resolve_limited_subjective_binding_rows,
    stage1_projection_artifact_ref,
    stage1_canonical_json_bytes,
    stage1_candidate_selection_indices,
    stage1_candidate_uses_relation_qualifier_scope,
    stage1_foreground_coverage_required_flags,
    stage1_policy_application_order_key,
    stage1_source_explicit_target_topic_scope_refs,
    stage1_subjective_forbidden_promotions,
    stage1_subjective_semantic_key,
    stage1_value_principle_ref,
    subjective_proposition_v2_id,
    validate_stage1_post_selection_reception_records,
    validate_stage1_candidate_partition_bounds,
    validate_stage1_identity,
    validate_foreground_scope_derivation,
    validate_input_specific_meaning_structure,
    validate_premeaning_grounded_inputs,
    validate_stage1_projection,
    validate_stage1_interpretation_matrix,
    validate_stage1_sentence_unit,
    validate_surface_derivation,
)
from .source_kernel import (
    AdmittedTextSource,
    build_source_owner_universe,
    freeze_text_source,
    validate_evidence_refs,
)
from .emlis_input_specific_meaning import (
    ForegroundScopeDispositionCode,
    derive_foreground_scope_closed,
    derive_grounded_situation_view,
    derive_input_specific_meaning_structure,
    derive_reading_consequence,
    derive_sealed_emlis_provisional_reading,
    foreground_scope_disposition,
)

if TYPE_CHECKING:
    from .emlis_stage1_composition import (
        EmlisSubjectiveMeaningPlan,
        Stage1SubjectivePlanningInputs,
        Stage1SurfaceCompositionInputs,
    )


INTERPRETATION_CANDIDATE_POOL_CAP = 16
INTERPRETATION_CANDIDATE_KIND_CAP = 2
LAYER1_OBSERVATION_CONTRIBUTION_CAP = 5
OBSERVATION_SEMANTIC_KEY_VERSION = (
    "cocolon.cmee.v1a.emlis_stage1.observation_semantic_key.v1"
)

CMEE_STAGE1_MICROGRAMMAR_POLICY_VERSION = (
    "cocolon.emlis.stage1.microgrammar.v2"
)

# Sole finite Step 4 surface owner.  Every non-source Japanese token used by
# the disabled realizer is present in this immutable tuple.  These are lexical
# heads and typed slots, never completed sentence templates.
CMEE_STAGE1_MICROGRAMMAR_INVENTORY_TUPLE = (
    ("policy_id", CMEE_STAGE1_MICROGRAMMAR_POLICY_VERSION),
    ("policy_ref", CMEE_STAGE1_MICROGRAMMAR_POLICY_REF),
    (
        "predicate_families",
        (
            (
                "STATE_RECOGNITION_V1",
                (
                    "あります",
                    "続いています",
                    "残っています",
                    "まだ終わっていません",
                    "かかっています",
                    "起きています",
                    "記録されています",
                    "途中にあります",
                ),
            ),
            ("COEXISTENCE_V1", ("同時にあります", "重なっています")),
            ("ADMITTED_TENSION_V1", ("並んでいます", "せめぎ合っています")),
            ("ORDERED_CHANGE_V1", ("変化があります", "変わっています")),
            ("SOURCE_STATED_CAUSE_V1", ("明示されています",)),
            (
                "EMLIS_ATTENTION_APPRAISAL_V1",
                (
                    "目が向きます",
                    "心に残ります",
                    "意識を向けます",
                    "気に留めます",
                    "大切な動きだと考えます",
                    "見過ごせないことだと考えます",
                ),
            ),
            (
                "EMLIS_AFFECT_V1",
                (
                    ("CONCERN", "気がかりです"),
                    ("CONCERN", "気にかかります"),
                    ("RELIEF", "ほっとします"),
                    ("JOY", "うれしく思います"),
                    ("SADNESS", "悲しく感じます"),
                    ("RESPECT", "大切に受け取ります"),
                    ("DISCOMFORT", "違和感があります"),
                ),
            ),
            (
                "PROTECT_VALUE_BOUNDARY",
                ("大切にしたいと考えます", "守りたいと考えます"),
            ),
            (
                "TAKE_RELATIONAL_STANCE",
                (
                    "そばで受け止めます",
                    "そのまま受け取ります",
                    "開いたまま受け取ります",
                    "結論を急ぎません",
                    "選ぶ余地を残したいと考えます",
                    "急いで決めたくありません",
                    "うれしく受け取ります",
                    "大切に受け取ります",
                ),
            ),
            (
                "COUNTER_SPECIFIC_PROMOTION",
                ("急いで決めつけたくありません", "その決めつけには同意しません"),
            ),
        ),
    ),
    (
        "connective_families",
        (
            ("NONE", ("",)),
            ("ADDITIVE", ("そして", "そのうえで")),
            ("COADDITIVE", ("あわせて",)),
            ("SIMULTANEOUS", ("同時に",)),
            ("CONTRASTIVE", ("一方で", "それでも")),
            ("TEMPORAL", ("そのあと", "そこから")),
            ("CONTINUATIVE", ("また", "そのことに")),
            ("STANCE_TRANSITION", ("そのうえで", "あわせて")),
            ("BOUNDED_CONTRAST", ("ただ",)),
        ),
    ),
    (
        "operator_connective_rows",
        (
            ("LAYER_1", "NO_RELATION_CLAIM", "ADDITIVE"),
            ("LAYER_1", "COEXISTS_WITH", "SIMULTANEOUS"),
            ("LAYER_1", "TENSION_WITH", "CONTRASTIVE"),
            ("LAYER_1", "TEMPORALLY_PRECEDES", "TEMPORAL"),
            ("LAYER_1", "ACTION_PRECEDES_CHANGE", "TEMPORAL"),
            ("LAYER_1", "SOURCE_EXPLICIT_CAUSE", "ADDITIVE"),
            ("LAYER_2", "ATTEND_TO", "CONTINUATIVE"),
            ("LAYER_2", "FEEL_TOWARD", "CONTINUATIVE"),
            ("LAYER_2", "APPRAISE_AS_MATERIAL", "ADDITIVE"),
            ("LAYER_2", "PROTECT_VALUE_BOUNDARY", "ADDITIVE"),
            ("LAYER_2", "TAKE_RELATIONAL_STANCE", "STANCE_TRANSITION"),
            ("LAYER_2", "COUNTER_SPECIFIC_PROMOTION", "BOUNDED_CONTRAST"),
        ),
    ),
    (
        "modality_wrappers",
        (
            ("fact", "ということ"),
            ("feeling", "という気持ち"),
            ("wish", "という願い"),
            ("intention", "という方向"),
            ("possibility", "という可能性"),
            ("uncertain", "というまだ決まっていないこと"),
            ("refusal", "という境界"),
        ),
    ),
    (
        "time_wrappers",
        (
            ("current_input", ("今", "今の")),
            ("present", ("今", "今の")),
            ("past", ("その時", "その時の")),
            ("future", ("これから", "これからの")),
            ("continuing", ("今も", "今も続く")),
            ("past_to_present", ("その時から今も", "その時から今に残る")),
            ("present_to_future", ("今から先へ", "今から先へ向く")),
        ),
    ),
    (
        "observation_operator_rows",
        (
            ("PRESENT_STATE", "NO_RELATION_CLAIM", "STATE_RECOGNITION_V1", "あります", "続いています", "continuing_only"),
            ("PRESENT_DIRECTION", "NO_RELATION_CLAIM", "STATE_RECOGNITION_V1", "あります", "続いています", "continuing_only"),
            ("PRESENT_BURDEN", "NO_RELATION_CLAIM", "STATE_RECOGNITION_V1", "かかっています", "", "never"),
            ("PRESENT_CHANGE", "NO_RELATION_CLAIM", "STATE_RECOGNITION_V1", "あります", "起きています", "always"),
            ("PRESENT_ACTUAL_OUTPUT", "NO_RELATION_CLAIM", "STATE_RECOGNITION_V1", "起きています", "記録されています", "always"),
            ("PRESENT_RESIDUE", "NO_RELATION_CLAIM", "STATE_RECOGNITION_V1", "残っています", "続いています", "always"),
            ("PRESENT_UNFINISHED", "NO_RELATION_CLAIM", "STATE_RECOGNITION_V1", "まだ終わっていません", "途中にあります", "always"),
            ("SYNTHESIZE_RELATION", "COEXISTS_WITH", "COEXISTENCE_V1", "同時にあります", "重なっています", "always"),
            ("SYNTHESIZE_RELATION", "TENSION_WITH", "ADMITTED_TENSION_V1", "せめぎ合っています", "並んでいます", "always"),
            ("PRESENT_RESIDUE", "TEMPORALLY_PRECEDES", "STATE_RECOGNITION_V1", "残っています", "続いています", "always"),
            ("PRESENT_CHANGE", "ACTION_PRECEDES_CHANGE", "ORDERED_CHANGE_V1", "変化があります", "変わっています", "always"),
            ("SYNTHESIZE_RELATION", "SOURCE_EXPLICIT_CAUSE", "SOURCE_STATED_CAUSE_V1", "明示されています", "", "never"),
        ),
    ),
    (
        "subjective_operator_rows",
        (
            ("ATTEND_TO", "", "EMLIS_ATTENTION_APPRAISAL_V1", "目が向きます", "心に残ります"),
            ("FEEL_TOWARD", "CONCERN", "EMLIS_AFFECT_V1", "気がかりです", "気にかかります"),
            ("FEEL_TOWARD", "RELIEF", "EMLIS_AFFECT_V1", "ほっとします", ""),
            ("FEEL_TOWARD", "JOY", "EMLIS_AFFECT_V1", "うれしく思います", ""),
            ("FEEL_TOWARD", "SADNESS", "EMLIS_AFFECT_V1", "悲しく感じます", ""),
            ("FEEL_TOWARD", "RESPECT", "EMLIS_AFFECT_V1", "大切に受け取ります", ""),
            ("FEEL_TOWARD", "DISCOMFORT", "EMLIS_AFFECT_V1", "違和感があります", ""),
            ("APPRAISE_AS_MATERIAL", "", "EMLIS_ATTENTION_APPRAISAL_V1", "大切な動きだと考えます", "見過ごせないことだと考えます"),
            ("PROTECT_VALUE_BOUNDARY", "", "PROTECT_VALUE_BOUNDARY", "大切にしたいと考えます", "守りたいと考えます"),
            ("TAKE_RELATIONAL_STANCE", "STAY_WITH_SPECIFIC_OBJECT", "TAKE_RELATIONAL_STANCE", "そばで受け止めます", "そのまま受け取ります"),
            ("TAKE_RELATIONAL_STANCE", "HOLD_UNFINISHED_OPEN", "TAKE_RELATIONAL_STANCE", "開いたまま受け取ります", "結論を急ぎません"),
            ("TAKE_RELATIONAL_STANCE", "PROTECT_USER_AGENCY", "TAKE_RELATIONAL_STANCE", "選ぶ余地を残したいと考えます", "急いで決めたくありません"),
            ("TAKE_RELATIONAL_STANCE", "WELCOME_BOUNDED_CHANGE", "TAKE_RELATIONAL_STANCE", "うれしく受け取ります", "大切に受け取ります"),
            ("COUNTER_SPECIFIC_PROMOTION", "", "COUNTER_SPECIFIC_PROMOTION", "急いで決めつけたくありません", "その決めつけには同意しません"),
        ),
    ),
    (
        "attention_surface_rows",
        (
            (
                "PRESENT_DIRECTION:current_input",
                (("に", "目が向きます"), ("が", "心に残ります")),
            ),
            (
                "PRESENT_DIRECTION:present",
                (("が", "心に残ります"), ("に", "目が向きます")),
            ),
            (
                "PRESENT_DIRECTION:continuing",
                (("に", "意識を向けます"), ("が", "心に残ります")),
            ),
            (
                "PRESENT_BURDEN:current_input",
                (("に", "目が向きます"), ("に", "意識を向けます")),
            ),
            (
                "PRESENT_BURDEN:continuing",
                (("に", "意識を向けます"), ("に", "目が向きます")),
            ),
            (
                "*:*",
                (("に", "目が向きます"), ("が", "心に残ります")),
            ),
        ),
    ),
    (
        "layer1_direct_slots",
        (
            (
                "PRESENT_STATE",
                (
                    ("fact", "という状態が"),
                    ("feeling", "という気持ちが"),
                    ("wish", "という気持ちが"),
                    ("intention", "という気持ちが"),
                    ("possibility", "という可能性が"),
                    ("uncertain", "まだ決まっていないことが"),
                    ("refusal", "という状態が"),
                ),
            ),
            (
                "PRESENT_DIRECTION",
                (
                    ("fact", "という方向が"),
                    ("feeling", "という方向が"),
                    ("wish", "という気持ちが"),
                    ("intention", "という気持ちが"),
                    ("possibility", "という可能性が"),
                    ("uncertain", "まだ決まっていない方向が"),
                    ("refusal", "という境界が"),
                ),
            ),
            (
                "PRESENT_BURDEN",
                (
                    ("fact", "という負荷が"),
                    ("feeling", "という負荷が"),
                    ("wish", "という負荷が"),
                    ("intention", "という負荷が"),
                    ("possibility", "という負荷が"),
                    ("uncertain", "という負荷が"),
                    ("refusal", "という負荷が"),
                ),
            ),
            (
                "PRESENT_CHANGE",
                (
                    ("fact", "という変化が"),
                    ("feeling", "という変化が"),
                    ("wish", "という変化が"),
                    ("intention", "という変化が"),
                    ("possibility", "という変化が"),
                    ("uncertain", "という変化が"),
                    ("refusal", "という変化が"),
                ),
            ),
            (
                "PRESENT_ACTUAL_OUTPUT",
                (
                    ("fact", "という出来事が"),
                    ("feeling", "という出来事が"),
                    ("wish", "という出来事が"),
                    ("intention", "という出来事が"),
                    ("possibility", "という出来事が"),
                    ("uncertain", "という出来事が"),
                    ("refusal", "という出来事が"),
                ),
            ),
            (
                "PRESENT_UNFINISHED",
                (
                    ("fact", "ということが"),
                    ("feeling", "ということが"),
                    ("wish", "ということが"),
                    ("intention", "ということが"),
                    ("possibility", "ということが"),
                    ("uncertain", "ということが"),
                    ("refusal", "ということが"),
                ),
            ),
        ),
    ),
    (
        "layer2_anaphoric_surfaces",
        (
            ("PRESENT_STATE:*", "その状態"),
            ("PRESENT_STATE:feeling", "その気持ち"),
            ("PRESENT_STATE:refusal", "その境界"),
            ("PRESENT_DIRECTION:*", "その方向"),
            ("PRESENT_DIRECTION:wish", "その願い"),
            ("PRESENT_BURDEN:*", "その負荷"),
            ("PRESENT_CHANGE:*", "その変化"),
            ("PRESENT_ACTUAL_OUTPUT:*", "その出来事"),
            ("PRESENT_RESIDUE:*", "その残っていること"),
            ("PRESENT_UNFINISHED:*", "その途中にあること"),
            ("HEAD:QUESTION", "その問い"),
            ("HEAD:HESITATION", "そのためらい"),
        ),
    ),
    (
        "modality_anaphoric_surfaces",
        (
            ("fact", "そのこと"),
            ("feeling", "その気持ち"),
            ("wish", "その願い"),
            ("intention", "その方向"),
            ("possibility", "その可能性"),
            ("uncertain", "そのまだ決まっていないこと"),
            ("refusal", "その境界"),
        ),
    ),
    (
        "layer2_explicit_nominalizers",
        (
            ("PRESENT_STATE:*", "という状態"),
            ("PRESENT_STATE:feeling", "という気持ち"),
            ("PRESENT_STATE:refusal", "という境界"),
            ("PRESENT_DIRECTION:*", "という方向"),
            ("PRESENT_DIRECTION:wish", "という願い"),
            ("PRESENT_BURDEN:*", "という負荷"),
            ("PRESENT_CHANGE:*", "という変化"),
            ("PRESENT_ACTUAL_OUTPUT:*", "という出来事"),
            ("PRESENT_RESIDUE:*", "という残っていること"),
            ("PRESENT_UNFINISHED:*", "という途中にあること"),
            ("HEAD:QUESTION", "という問い"),
            ("HEAD:HESITATION", "というためらい"),
        ),
    ),
    (
        "direction_under_burden_surface",
        (
            ("predicate", "続いています"),
            ("burden_link", "がある中でも"),
            ("direction_topic", "は"),
        ),
    ),
    (
        "direct_contrast_surface",
        (
            ("direction_nominalizer", "という願い"),
            ("burden_nominalizer", "という負荷"),
            ("hesitation_nominalizer", "というためらい"),
            ("bridge", "がある一方で"),
            ("second_topic", "も"),
        ),
    ),
    (
        "context_residue_surface",
        (
            ("context_tail", "あとにも"),
            ("direction_nominalizer", "という願いがあり"),
            ("residue_topic", "も"),
            ("predicate", "残っています"),
        ),
    ),
    (
        "open_question_surface",
        (
            ("burden_link", "な中で"),
            ("question_case", "を"),
            ("predicate", "考えています"),
        ),
    ),
    (
        "compound_burden_surface",
        (
            ("context_link", "が続く中で"),
            ("fatigue_link", "いるうえに"),
        ),
    ),
    (
        "body_burden_surface",
        (
            ("topic_possessive", "の"),
            ("body_adjective_nominal", "だるさ"),
            ("topic_object", "を"),
        ),
    ),
    (
        "epistemic_burden_surface",
        (("question_link", "という"),),
    ),
    (
        "action_change_surface",
        (
            ("context_tail", "あと"),
            ("action_tail", "ことがあり"),
            ("sequence", "その後"),
        ),
    ),
    (
        "simple_change_surface",
        (
            ("te_context_tail", "たあと"),
            ("de_context_tail", "だあと"),
        ),
    ),
    (
        "bounded_self_denial_surface",
        (
            ("basis_nominalizer", "ということと"),
            ("boundary_nominalizer", "という境界が"),
        ),
    ),
    (
        "relation_time_precedence",
        (
            "past_to_present",
            "present_to_future",
            "continuing",
            "present",
            "current_input",
            "past",
            "future",
        ),
    ),
    (
        "layer1_optional_connective_rows",
        (
            ("PRESENT_DIRECTION", "COADDITIVE"),
            ("PRESENT_BURDEN", "CONTINUATIVE"),
            ("PRESENT_CHANGE", "ADDITIVE"),
            ("PRESENT_STATE", "ADDITIVE"),
            ("PRESENT_ACTUAL_OUTPUT", "ADDITIVE"),
            ("PRESENT_RESIDUE", "CONTINUATIVE"),
            ("PRESENT_UNFINISHED", "CONTINUATIVE"),
            ("SYNTHESIZE_RELATION", "ADDITIVE"),
        ),
    ),
    (
        "layer1_relation_slots",
        (
            ("COEXISTS_WITH", (("LEFT", "", "と"), ("RIGHT", "", "が"))),
            ("TENSION_WITH", (("LEFT", "", "と"), ("RIGHT", "", "が"))),
            ("TEMPORALLY_PRECEDES", (("BEFORE", "", "のあとに"), ("AFTER", "", "が"))),
            ("ACTION_PRECEDES_CHANGE", (("ACTION", "", "のあとに"), ("CHANGE", "", "という"))),
            ("SOURCE_EXPLICIT_CAUSE", (("CAUSE", "", "が"), ("EFFECT", "", "の理由だと"))),
        ),
    ),
    (
        "layer2_case_particles",
        (
            ("ATTEND_TO", "に"),
            ("FEEL_TOWARD:CONCERN", "が"),
            ("FEEL_TOWARD:RELIEF", "に"),
            ("FEEL_TOWARD:JOY", "を"),
            ("FEEL_TOWARD:SADNESS", "を"),
            ("FEEL_TOWARD:RESPECT", "を"),
            ("FEEL_TOWARD:DISCOMFORT", "に"),
            ("APPRAISE_AS_MATERIAL", "を"),
            ("PROTECT_VALUE_BOUNDARY", "を"),
            ("TAKE_RELATIONAL_STANCE:STAY_WITH_SPECIFIC_OBJECT", "を"),
            ("TAKE_RELATIONAL_STANCE:HOLD_UNFINISHED_OPEN", "を"),
            ("TAKE_RELATIONAL_STANCE:PROTECT_USER_AGENCY", "について"),
            ("TAKE_RELATIONAL_STANCE:WELCOME_BOUNDED_CHANGE", "を"),
            ("COUNTER_SPECIFIC_PROMOTION", "について"),
        ),
    ),
    (
        "subjective_semantic_predicate_rotation_rows",
        (
            (
                "FEEL_TOWARD",
                "CONCERN",
                "PRESENT_BURDEN",
                "current_input",
            ),
            (
                "TAKE_RELATIONAL_STANCE",
                "PROTECT_USER_AGENCY",
                "PRESENT_DIRECTION",
                "continuing",
            ),
        ),
    ),
    (
        "subjective_semantic_connective_rotation_rows",
        (
            (
                "TAKE_RELATIONAL_STANCE",
                "PROTECT_USER_AGENCY",
                "PRESENT_DIRECTION",
                "present",
            ),
        ),
    ),
    (
        "subjective_basis_connective_rows",
        (
            (
                "TAKE_RELATIONAL_STANCE",
                "PROTECT_USER_AGENCY",
                "TENSION_WITH",
                "ADDITIVE",
            ),
        ),
    ),
    (
        "structural_tokens",
        (
            ("speaker", "Emlis"),
            ("topic_particle", "は"),
            ("separator", "、"),
            ("quote_open", "「"),
            ("quote_close", "」"),
            ("terminal", "。"),
        ),
    ),
    (
        "topic_speaker_policy",
        (
            ("source_actor_experiencer", "explicit_only_when_ambiguous"),
            (
                "layer2_explicit_speaker_placement",
                "first_move_and_each_counterposition",
            ),
            ("later_zero_subject", "unique_resolution_only"),
            ("wrapper_placement", "nominalizer_then_time_adverb_then_predicate"),
            ("inflection_order", "polarity_then_modality_then_time_scope"),
        ),
    ),
    (
        "reference_mode_policy",
        (
            ("anaphoric_first", "unique_prior_object_required"),
            ("short_anchor_if_ambiguous", "source_bound_anchor_exact0_or1"),
            ("explicit_emlis_counterposition", "source_bound_target_exact1"),
        ),
    ),
    (
        "role_anchor_policy",
        (
            ("max_graphemes", 32),
            ("over_limit_selection", "semantic_boundary_or_stop"),
            ("inserted_token_count", 0),
            ("full_value_replay_over_limit", False),
        ),
    ),
    (
        "quote_policy",
        (
            ("l1_max_graphemes", 16),
            ("l1_max_per_sentence", 2),
            ("l2_max_graphemes", 16),
            ("l2_max_per_sentence", 1),
            ("full_replay", False),
        ),
    ),
    (
        "semantic_role_surface_policy",
        (
            ("per_required_argument_role", 1),
            ("binary_relation_role_surface", 2),
            ("actor_experiencer_addressee_separated", True),
            ("new_meaning_allowed", False),
        ),
    ),
    (
        "source_shape_recognizers",
        (
            (
                "direct_contrast",
                r"(?:けれども|けれど|けど|のに)[、,]?",
            ),
            (
                "context_direction_residue",
                r"(?P<context>.+?)あと[、,]"
                r"(?P<direction>[^、,。！？!?]{1,16}?たい)"
                r"(?:気持ち|願い)?(?:と|や)"
                r"(?P<residue>[^、,。！？!?]{1,16}?)(?:が|は)"
                r"残って(?:いる|います)",
            ),
            (
                "open_question",
                r"(?P<burden>.+?)で[、,]"
                r"(?P<question>どうしたら(?:いい|よい)のか)"
                r"(?:を)?考えて(?:いる|います)",
            ),
            (
                "compound_burden",
                r"(?P<context>.+?)が続いて(?P<fatigue>.+?て)いて[、,]"
                r"(?P<burden>.+)",
            ),
            (
                "action_change",
                r"(?P<context>.+?)(?:けれども|けれど|けど)[、,]?"
                r"(?P<action>.+?(?:たら|だら|なら))(?P<result>.+)",
            ),
            (
                "simple_positive_change",
                r"(?P<context>.+?)(?P<connector>て|で)"
                r"(?P<result>[^、,。！？!?]{1,16}?かった)",
            ),
            ("positive_desire", r"(?<!たくない)たい$"),
            (
                "hesitation",
                r"(?:かもしれない|かもしれません|かも)$",
            ),
            (
                "bounded_self_denial",
                r"(?P<basis>[^、,。！？!?]{1,16}?から)[、,]"
                r"(?P<boundary>[^、,。！？!?]{1,16}?てはいけない)",
            ),
            (
                "body_adjective",
                r"(?P<topic>.+?)が(?P<state>だるい)",
            ),
            (
                "body_weight",
                r"(?P<topic>.+?)が(?P<state>重く感じる)",
            ),
            (
                "context_de_epistemic_burden",
                r"(?P<context>[^、,。！？!?]{1,16}?)で"
                r"(?P<question>[^、,。！？!?]{1,16}?か)"
                r"(?P<affect>不安|心配)",
            ),
        ),
    ),
    (
        "source_shape_inflections",
        (
            ("conditional_tara", ("たら", "た")),
            ("conditional_dara", ("だら", "だ")),
            ("conditional_nara", ("なら", "")),
            ("simple_te", "て"),
            ("simple_de", "で"),
        ),
    ),
    (
        "clause_policy",
        (
            ("one_move_one_sentence", True),
            ("same_observation_argument_join", True),
            ("multiple_subjective_claim_join", False),
            ("unknown_join", False),
        ),
    ),
    (
        "move_ref_policy",
        (
            ("format", "move:{basis_anchor_ref}@cocolon.emlis.stage1.microgrammar.v2"),
            ("basis_anchor_count", 1),
            ("unit_frame_move_ref_exact", True),
        ),
    ),
    (
        "polarity_policy",
        (
            ("positive", "affirmative_polite_predicate"),
            ("negative", "source_anchor_preserved_no_predicate_inversion"),
            ("mixed", "argument_slots_preserved_separately"),
            ("neutral", "no_evaluative_morpheme_added"),
        ),
    ),
    (
        "variant_policy",
        (
            ("primary_variant_id", "01-primary.v2"),
            ("alternate_variant_id", "02-alternate.v2"),
            ("max_candidates", 2),
            ("first_predicate_alternate_only", True),
            ("connective_alternate_only_without_predicate_alternate", True),
            ("multiple_slot_replacement", False),
            ("predicate_case_pair_atomic", True),
            ("automatic_retry", 0),
            ("post_defect_generation", 0),
        ),
    ),
    (
        "s9_selection_policy",
        (
            ("hard_valid_only", True),
            ("required_full_coverage", True),
            ("normalized_exact_repetition", 0),
            ("unresolved_zero_subject", 0),
            ("connective_collision", 0),
            ("tie_break", "composition_variant_id_lexical_ascending"),
            ("new_recomposition", 0),
            ("new_generation", 0),
        ),
    ),
)
CMEE_STAGE1_MICROGRAMMAR_INVENTORY_DOCS_BYTES = stage1_canonical_json_bytes(
    CMEE_STAGE1_MICROGRAMMAR_INVENTORY_TUPLE
)
CMEE_STAGE1_MICROGRAMMAR_INVENTORY_DOCS_SHA256 = hashlib.sha256(
    CMEE_STAGE1_MICROGRAMMAR_INVENTORY_DOCS_BYTES
).hexdigest()

_MICROGRAMMAR_SECTIONS = dict(CMEE_STAGE1_MICROGRAMMAR_INVENTORY_TUPLE)

_OBSERVATION_PREDICATE_ROWS = {
    (operator, relation): (primary, alternate, condition)
    for operator, relation, _family, primary, alternate, condition
    in _MICROGRAMMAR_SECTIONS["observation_operator_rows"]
}
_OBSERVATION_PREDICATE_FAMILIES = {
    (operator, relation): family
    for operator, relation, family, _primary, _alternate, _condition
    in _MICROGRAMMAR_SECTIONS["observation_operator_rows"]
}
_SUBJECTIVE_PREDICATE_ROWS = {
    (operator, detail): (primary, alternate)
    for operator, detail, _family, primary, alternate
    in _MICROGRAMMAR_SECTIONS["subjective_operator_rows"]
}
_SUBJECTIVE_PREDICATE_FAMILIES = {
    (operator, detail): family
    for operator, detail, family, _primary, _alternate
    in _MICROGRAMMAR_SECTIONS["subjective_operator_rows"]
}
_ATTENTION_SURFACE_ROWS = dict(
    _MICROGRAMMAR_SECTIONS["attention_surface_rows"]
)
_CONNECTIVE_FAMILIES = dict(_MICROGRAMMAR_SECTIONS["connective_families"])
_OPERATOR_CONNECTIVES = {
    (layer, operator): family
    for layer, operator, family in _MICROGRAMMAR_SECTIONS[
        "operator_connective_rows"
    ]
}
_MODALITY_WRAPPERS = dict(_MICROGRAMMAR_SECTIONS["modality_wrappers"])
_TIME_WRAPPERS = dict(_MICROGRAMMAR_SECTIONS["time_wrappers"])
_LAYER1_DIRECT_SLOTS = {
    operator: dict(rows)
    for operator, rows in _MICROGRAMMAR_SECTIONS["layer1_direct_slots"]
}
_LAYER2_ANAPHORIC_SURFACES = dict(
    _MICROGRAMMAR_SECTIONS["layer2_anaphoric_surfaces"]
)
_MODALITY_ANAPHORIC_SURFACES = dict(
    _MICROGRAMMAR_SECTIONS["modality_anaphoric_surfaces"]
)
_LAYER2_EXPLICIT_NOMINALIZERS = dict(
    _MICROGRAMMAR_SECTIONS["layer2_explicit_nominalizers"]
)
_DIRECTION_UNDER_BURDEN_SURFACE = dict(
    _MICROGRAMMAR_SECTIONS["direction_under_burden_surface"]
)
_DIRECT_CONTRAST_SURFACE = dict(
    _MICROGRAMMAR_SECTIONS["direct_contrast_surface"]
)
_CONTEXT_RESIDUE_SURFACE = dict(
    _MICROGRAMMAR_SECTIONS["context_residue_surface"]
)
_OPEN_QUESTION_SURFACE = dict(
    _MICROGRAMMAR_SECTIONS["open_question_surface"]
)
_COMPOUND_BURDEN_SURFACE = dict(
    _MICROGRAMMAR_SECTIONS["compound_burden_surface"]
)
_BODY_BURDEN_SURFACE = dict(
    _MICROGRAMMAR_SECTIONS["body_burden_surface"]
)
_EPISTEMIC_BURDEN_SURFACE = dict(
    _MICROGRAMMAR_SECTIONS["epistemic_burden_surface"]
)
_ACTION_CHANGE_SURFACE = dict(
    _MICROGRAMMAR_SECTIONS["action_change_surface"]
)
_SIMPLE_CHANGE_SURFACE = dict(
    _MICROGRAMMAR_SECTIONS["simple_change_surface"]
)
_BOUNDED_SELF_DENIAL_SURFACE = dict(
    _MICROGRAMMAR_SECTIONS["bounded_self_denial_surface"]
)
_RELATION_TIME_PRECEDENCE = tuple(
    _MICROGRAMMAR_SECTIONS["relation_time_precedence"]
)
_LAYER1_OPTIONAL_CONNECTIVES = dict(
    _MICROGRAMMAR_SECTIONS["layer1_optional_connective_rows"]
)
_LAYER1_RELATION_SLOTS = dict(_MICROGRAMMAR_SECTIONS["layer1_relation_slots"])
_LAYER2_CASE_PARTICLES = dict(_MICROGRAMMAR_SECTIONS["layer2_case_particles"])
_SUBJECTIVE_SEMANTIC_PREDICATE_ROTATIONS = frozenset(
    tuple(row)
    for row in _MICROGRAMMAR_SECTIONS[
        "subjective_semantic_predicate_rotation_rows"
    ]
)
_SUBJECTIVE_SEMANTIC_CONNECTIVE_ROTATIONS = frozenset(
    tuple(row)
    for row in _MICROGRAMMAR_SECTIONS[
        "subjective_semantic_connective_rotation_rows"
    ]
)
_SUBJECTIVE_BASIS_CONNECTIVES = {
    (operator, detail, relation): family
    for operator, detail, relation, family
    in _MICROGRAMMAR_SECTIONS["subjective_basis_connective_rows"]
}
_STRUCTURAL_TOKENS = dict(_MICROGRAMMAR_SECTIONS["structural_tokens"])
_TOPIC_SPEAKER_POLICY = dict(_MICROGRAMMAR_SECTIONS["topic_speaker_policy"])
_REFERENCE_MODE_POLICY = dict(_MICROGRAMMAR_SECTIONS["reference_mode_policy"])
_QUOTE_POLICY = dict(_MICROGRAMMAR_SECTIONS["quote_policy"])
_ROLE_ANCHOR_POLICY = dict(_MICROGRAMMAR_SECTIONS["role_anchor_policy"])
_SOURCE_SHAPE_RECOGNIZERS = dict(
    _MICROGRAMMAR_SECTIONS["source_shape_recognizers"]
)
_SOURCE_SHAPE_INFLECTIONS = dict(
    _MICROGRAMMAR_SECTIONS["source_shape_inflections"]
)
_VARIANT_POLICY = dict(_MICROGRAMMAR_SECTIONS["variant_policy"])
_PRIMARY_VARIANT_ID = str(_VARIANT_POLICY["primary_variant_id"])
_ALTERNATE_VARIANT_ID = str(_VARIANT_POLICY["alternate_variant_id"])

_PROVISIONAL_QUALIFIER = "epistemic:provisional_interpretation"
_FORBIDDEN_PROMOTIONS = (
    "unsupported-cause",
    "personality-promotion",
    "hidden-intent-promotion",
    "diagnosis-promotion",
    "future-guarantee",
    "unknown-as-interpretation",
)
_FORBIDDEN_OBSERVATION_OPERATIONS = (
    "invent-cause",
    "invent-personality",
    "invent-hidden-intent",
    "invent-diagnosis",
    "promote-unknown",
    "complete-unfinished-meaning",
)
_ADMITTED_NUCLEUS_GROUNDING = frozenset({"explicit", "user_stated_relation"})
_ADMITTED_RELATION_GROUNDING = frozenset({"user_stated_relation"})
_CAUSE_RELATIONS = frozenset(
    {
        "cause",
        "causes",
        "caused_by",
        "because",
        "result_of",
        "user_stated_result",
    }
)
_DIRECTION_KINDS = frozenset(
    {"wish", "direction", "desire", "intention", "goal", "help_seeking"}
)
_BURDEN_KINDS = frozenset(
    {"constraint", "burden", "fatigue", "anxiety", "hesitation", "block"}
)
_ACTION_KINDS = frozenset({"action", "attempt"})
_CHANGE_KINDS = frozenset({"change", "bounded_change"})
_UNFINISHED_KINDS = frozenset({"uncertainty", "unfinished", "open_question"})

_SLOT_ORDER = (
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
_OPERATOR_PRIORITY = {
    RelationOperator.TENSION_WITH: 0,
    RelationOperator.COEXISTS_WITH: 1,
    RelationOperator.ACTION_PRECEDES_CHANGE: 2,
    RelationOperator.TEMPORALLY_PRECEDES: 3,
    RelationOperator.SOURCE_EXPLICIT_CAUSE: 4,
    RelationOperator.NO_RELATION_CLAIM: 5,
}
_RETENTION_PRIORITY = {"required": 0, "should": 1, "optional": 2}

_RECEPTION_ACT_ROWS = {
    row.reception_act: row for row in CMEE_STAGE1_RECEPTION_ACT_MAPPING_EXACT7
}
_RECEPTION_STANCE_ROWS = {
    row.stance: row for row in CMEE_STAGE1_RECEPTION_STANCE_MAPPING_EXACT5
}
_RECEPTION_STANCE_BY_ACT = dict(CMEE_STAGE1_RECEPTION_ACT_STANCE_EXACT7)
_RECEPTION_MOVE_ROLES_BY_ACT = dict(CMEE_STAGE1_RECEPTION_MOVE_ROLE_MAPPING)
_RECEPTION_SPEAKERS = frozenset(
    row[0] for row in CMEE_STAGE1_RECEPTION_SPEAKER_MAPPING_EXACT2
)
_RECEPTION_REFERENCE_MODES = frozenset(
    row[0] for row in CMEE_STAGE1_RECEPTION_REFERENCE_MAPPING_EXACT3
)
_RECEPTION_SURFACE_STRATEGIES = frozenset(
    row[0] for row in CMEE_STAGE1_RECEPTION_SURFACE_STRATEGY_MAPPING_EXACT5
)
_RECEPTION_SAFETY_CODES = tuple(
    row[0] for row in CMEE_STAGE1_RECEPTION_SAFETY_CODE_MAPPING_EXACT3
)

@dataclass(frozen=True, slots=True)
class _PlanBinding:
    node_meta: Mapping[str, object]
    edge_meta: Mapping[str, object]
    nucleus_to_node: Mapping[str, str]
    relation_to_edge: Mapping[str, str]
    required_node_ids: frozenset[str]
    required_edge_ids: frozenset[str]
    source_order: Mapping[str, int]


@dataclass(frozen=True, slots=True)
class _RequestLocalResponseState:
    """Exact request-local Layer 2 boundary; never persisted or carried over."""

    speaker_identity: str
    versioned_value_policy: str
    selected_observation_contribution_refs: tuple[str, ...]
    relationship_care_constraints: tuple[str, ...]


class UtterancePhase(str, Enum):
    L1_ACTIVE = "L1_ACTIVE"
    L1_COMPLETE = "L1_COMPLETE"
    L2_ACTIVE = "L2_ACTIVE"
    CANDIDATE_COMPLETE = "CANDIDATE_COMPLETE"
    READY_FOR_S9 = "READY_FOR_S9"
    NO_VALID_SURFACE = "NO_VALID_SURFACE"


@dataclass(slots=True)
class EmlisUtteranceState:
    """Request-local, noncanonical S8 state; never stored in an artifact."""

    phase: UtterancePhase
    realized_observation_contribution_refs: list[str]
    remaining_required_observation_refs: list[str]
    suppressed_observation_candidate_refs: list[str]
    realized_subjective_claim_refs: list[str]
    remaining_required_subjective_refs: list[str]
    suppressed_subjective_claim_refs: list[str]
    last_focus_refs: list[str]
    last_move_kind: Optional[str]
    realized_semantic_keys: list[str]
    normalized_surface_digests: list[str]
    layer_sentence_counts: dict[str, int]
    composition_variant_id: str
    stop_reason: Optional[str]


@dataclass(frozen=True, slots=True)
class _SurfacePart:
    text: str
    bindings: tuple[tuple[str, str], ...]


@dataclass(frozen=True, slots=True)
class _CandidateRow:
    candidate: EmlisInterpretationCandidate
    required: bool
    is_relation: bool
    obligation_kind: str
    retention_rank: int
    source_order: int


@dataclass(frozen=True, slots=True)
class _BoundReceptionMove:
    move: object
    basis_contributions: tuple[PlannedObservationContribution, ...]
    target_contributions: tuple[PlannedObservationContribution, ...]
    response_object_refs: tuple[str, ...]


def _ordered(values: Iterable[str]) -> tuple[str, ...]:
    return tuple(dict.fromkeys(value for value in values if value))


def _enum_or_text(value: object) -> str:
    raw = getattr(value, "value", value)
    return str(raw or "")


def _cause_like_relation(value: object) -> bool:
    relation = _enum_or_text(value).lower()
    return (
        relation in _CAUSE_RELATIONS
        or "cause" in relation
        or "reason" in relation
        or relation.endswith("_result")
    )


def _graph_ref(graph: GroundedMeaningGraph) -> str:
    return f"grounded:{graph.graph_id}@{CMEE_GROUNDED_GRAPH_SCHEMA_VERSION}"


def _node_ref(node_id: str) -> str:
    return f"node:{node_id}@{CMEE_GROUNDED_GRAPH_SCHEMA_VERSION}"


def _edge_ref(edge_id: str) -> str:
    return f"edge:{edge_id}@{CMEE_GROUNDED_GRAPH_SCHEMA_VERSION}"


def _evidence_ref(evidence_id: str, source_version: str) -> str:
    return f"evidence:{evidence_id}@{source_version}"


def _identified(value: object, field_name: str) -> object:
    return replace(value, **{field_name: recompute_stage1_identity(value)})


def _validate_graph_and_parent(
    graph: GroundedMeaningGraph,
    parent_plan: ExperiencePlan,
) -> None:
    if type(graph) is not GroundedMeaningGraph:
        raise CMEEStage1ContractError("stage1_grounded_graph_required")
    if type(parent_plan) is not ExperiencePlan:
        raise CMEEStage1ContractError("stage1_parent_plan_type_invalid")
    if (
        parent_plan.source_envelope_id != graph.source_envelope_id
        or parent_plan.source_version != graph.source_version
        or parent_plan.obligation_version != graph.obligation_version
        or parent_plan.owner_universe_digest != graph.owner_universe_digest
    ):
        raise CMEEStage1ContractError("stage1_parent_plan_lineage_mismatch")
    if (
        not parent_plan.observation_duty_id
        or not parent_plan.reception_duty_id
        or parent_plan.observation_duty_id == parent_plan.reception_duty_id
    ):
        raise CMEEStage1ContractError("stage1_parent_duty_ref_invalid")

    node_ids = tuple(row.node_id for row in graph.nodes)
    edge_ids = tuple(row.edge_id for row in graph.edges)
    if (
        any(type(row) is not MeaningNode for row in graph.nodes)
        or any(type(row) is not MeaningEdge for row in graph.edges)
        or any(not item for item in (*node_ids, *edge_ids))
        or len(node_ids) != len(set(node_ids))
        or len(edge_ids) != len(set(edge_ids))
        or set(node_ids) & set(edge_ids)
    ):
        raise CMEEStage1ContractError("stage1_grounded_graph_identity_invalid")
    if any(
        edge.source_node_id not in set(node_ids)
        or edge.target_node_id not in set(node_ids)
        for edge in graph.edges
    ):
        raise CMEEStage1ContractError("stage1_relation_endpoint_missing")

    visible = tuple(parent_plan.visible_owner_ids)
    required = tuple(parent_plan.required_observation_owner_ids)
    reception = tuple(parent_plan.reception_target_owner_ids)
    for refs, code in (
        (visible, "stage1_visible_owner_identity_invalid"),
        (required, "stage1_required_owner_identity_invalid"),
        (reception, "stage1_reception_owner_identity_invalid"),
    ):
        if (
            any(type(ref) is not str or not ref for ref in refs)
            or len(refs) != len(set(refs))
        ):
            raise CMEEStage1ContractError(code)
    if not set(required + reception).issubset(set(visible)):
        raise CMEEStage1ContractError("stage1_visible_owner_plan_mismatch")


def _visible_claim_ids(
    graph: GroundedMeaningGraph,
    parent_plan: ExperiencePlan,
) -> set[str]:
    visible_owners = set(parent_plan.visible_owner_ids)
    if not visible_owners:
        raise CMEEStage1ContractError("stage1_visible_source_empty")
    graph_node_ids = {row.node_id for row in graph.nodes}
    graph_edge_ids = {row.edge_id for row in graph.edges}
    graph_claim_ids = graph_node_ids | graph_edge_ids
    if not graph.owner_dispositions:
        return graph_claim_ids

    disposition_by_owner = {
        row.meaning_owner_id: row for row in graph.owner_dispositions
    }
    if len(disposition_by_owner) != len(graph.owner_dispositions):
        raise CMEEStage1ContractError("stage1_owner_disposition_duplicate")
    positive = {
        SourceOwnerDisposition.SOURCE_EXPLICIT_VISIBLE,
        SourceOwnerDisposition.SUPPLEMENTAL_USER_VISIBLE,
    }
    visible_claim_ids: set[str] = set()
    for owner_id in visible_owners:
        row = disposition_by_owner.get(owner_id)
        if row is None or row.source_owner_disposition not in positive:
            raise CMEEStage1ContractError("stage1_visible_owner_disposition_mismatch")
        if not set(row.visible_claim_refs).issubset(graph_claim_ids):
            raise CMEEStage1ContractError("stage1_visible_claim_ref_missing")
        visible_claim_ids.update(row.visible_claim_refs)
    if any(
        not set(row.visible_claim_refs).issubset(graph_claim_ids)
        for row in graph.owner_dispositions
    ):
        raise CMEEStage1ContractError("stage1_visible_claim_ref_missing")
    if not visible_claim_ids:
        raise CMEEStage1ContractError("stage1_visible_source_empty")
    return visible_claim_ids


_PREMEANING_PARENT_SEMANTIC_FIELDS = (
    "source_envelope_id",
    "source_version",
    "obligation_version",
    "owner_universe_digest",
    "observation_duty_id",
    "unknown_duty_id",
    "required_observation_owner_ids",
    "visible_owner_ids",
    "unresolved_owner_ids",
    "visible_unknown_owner_ids",
    "required_unknown_owner_ids",
)

_PREMEANING_GROUNDED_PLAN_SEMANTIC_FIELDS = (
    "schema_version",
    "adapter_version",
    "generation_path",
    "input_profile",
    "nuclei",
    "relations",
    "unknown_boundaries",
    "evidence_ledger_validation",
    "referenced_evidence_span_ids",
    "source_contracts",
)

_PREMEANING_COVERAGE_SEMANTIC_FIELDS = (
    "required_nucleus_ids",
    "required_relation_ids",
    "all_required_nuclei_must_be_covered",
    "all_required_relations_must_be_covered",
    "all_sentence_evidence_ids_must_resolve",
    "label_only_allowed_only_without_text_nuclei",
)


def _premeaning_grounded_plan_semantic_identity(
    grounded_plan: GroundedObservationPlan,
) -> tuple[object, ...]:
    """Project only source/meaning fields; Reception and surface stay absent."""

    if type(grounded_plan) is not GroundedObservationPlan:
        raise CMEEStage1ContractError(
            "stage1_grounded_observation_plan_required"
        )
    coverage = grounded_plan.coverage_requirements
    return (
        *(getattr(grounded_plan, name) for name in (
            _PREMEANING_GROUNDED_PLAN_SEMANTIC_FIELDS
        )),
        *(getattr(coverage, name) for name in (
            _PREMEANING_COVERAGE_SEMANTIC_FIELDS
        )),
    )


def _validate_canonical_semantic_inputs(
    source: AdmittedTextSource,
    grounded_plan: GroundedObservationPlan,
    graph: GroundedMeaningGraph,
    parent_plan: ExperiencePlan,
    *,
    delivery_blind_parent: bool = False,
) -> tuple[GroundedObservationPlan, ExperiencePlan]:
    """Require the exact frozen-source/canonical-plan path used by Step 1."""

    if type(source) is not AdmittedTextSource:
        raise CMEEStage1ContractError("stage1_admitted_text_source_required")
    if type(grounded_plan) is not GroundedObservationPlan:
        raise CMEEStage1ContractError("stage1_grounded_observation_plan_required")
    try:
        raw = source.envelope.raw_utf8
        prefix = f"{source.envelope.source_encoding}\n@raw_json:".encode("ascii")
        if not raw.startswith(prefix):
            raise ValueError("source_frame_prefix_invalid")
        length_end = raw.index(b"\n", len(prefix))
        raw_json_length = int(raw[len(prefix) : length_end].decode("ascii"))
        raw_json_start = length_end + 1
        raw_json_end = raw_json_start + raw_json_length
        if raw_json_length <= 0 or raw_json_end > len(raw):
            raise ValueError("source_frame_json_length_invalid")
        source_snapshot = json.loads(raw[raw_json_start:raw_json_end].decode("utf-8"))
        expected_source = freeze_text_source(
            GenerationRequest(
                request_id="stage1-source-revalidation",
                current_input_bundle=build_emlis_current_input_bundle(
                    source_snapshot
                ),
                expected_source_record_id=source.envelope.source_record_id,
            )
        )
        validate_evidence_refs(source.envelope, source.evidence_refs)
        expected_universe = build_source_owner_universe(
            source.envelope, source.evidence_refs
        )
        resolver = build_evidence_span_resolver(
            expected_source.evidence_spans,
            current_input=expected_source.normalized_current_input,
        )
        expected_active_plan = build_grounded_observation_plan(
            expected_source.normalized_current_input,
            evidence_spans=expected_source.evidence_spans,
        )
        if delivery_blind_parent:
            expected_final_plan = build_final_stage1_grounded_observation_plan(
                expected_source.normalized_current_input,
                evidence_spans=expected_source.evidence_spans,
            )
            actual_semantic_identity = (
                _premeaning_grounded_plan_semantic_identity(grounded_plan)
            )
            matching_plans = tuple(
                value
                for value in (expected_active_plan, expected_final_plan)
                if _premeaning_grounded_plan_semantic_identity(value)
                == actual_semantic_identity
            )
            if len(matching_plans) != 1:
                raise ValueError("semantic_grounded_plan_noncanonical")
            expected_plan = matching_plans[0]
            issues = validate_grounded_observation_plan(
                expected_plan,
                resolver,
            )
        else:
            if grounded_plan == expected_active_plan:
                expected_plan = expected_active_plan
            else:
                expected_plan = build_final_stage1_grounded_observation_plan(
                    expected_source.normalized_current_input,
                    evidence_spans=expected_source.evidence_spans,
                )
            issues = validate_grounded_observation_plan(
                grounded_plan,
                resolver,
            )
        # Local import avoids making the existing Step 1 implementation depend
        # on this disabled Step 2 module during module initialization.
        from .emlis_v1a import (
            _build_experience_plan,
            _build_graph,
            _ordered as _stage1_ordered,
            _planned_visible_source_ids,
        )

        required_nuclei, required_relations, reception_targets = (
            _planned_visible_source_ids(expected_plan)
        )
        expected_graph = _build_graph(
            expected_source,
            expected_plan,
            _stage1_ordered((*required_nuclei, *reception_targets)),
            required_relations,
        )
        expected_parent = _build_experience_plan(
            expected_source,
            expected_graph,
            expected_plan,
            required_nuclei,
            required_relations,
            reception_targets,
        )
    except Exception:
        raise CMEEStage1ContractError("stage1_source_evidence_unreachable") from None
    if source != expected_source or source.owner_universe != expected_universe:
        raise CMEEStage1ContractError("stage1_source_evidence_unreachable")
    grounded_plan_matches = (
        _premeaning_grounded_plan_semantic_identity(grounded_plan)
        == _premeaning_grounded_plan_semantic_identity(expected_plan)
        if delivery_blind_parent
        else grounded_plan == expected_plan
    )
    if issues or not grounded_plan_matches:
        raise CMEEStage1ContractError("stage1_grounded_observation_plan_noncanonical")
    if graph != expected_graph:
        raise CMEEStage1ContractError("stage1_grounded_graph_noncanonical")
    if delivery_blind_parent:
        parent_matches = type(parent_plan) is ExperiencePlan and all(
            getattr(parent_plan, field_name)
            == getattr(expected_parent, field_name)
            for field_name in _PREMEANING_PARENT_SEMANTIC_FIELDS
        )
    else:
        parent_matches = parent_plan == expected_parent
    if not parent_matches:
        raise CMEEStage1ContractError("stage1_parent_plan_noncanonical")
    return expected_plan, expected_parent


def _source_evidence_ids(
    source: AdmittedTextSource,
    span_ids: Sequence[str],
) -> tuple[str, ...]:
    try:
        refs = tuple(source.evidence_ref(span_id) for span_id in span_ids)
    except Exception:
        raise CMEEStage1ContractError("stage1_semantic_plan_evidence_unresolved") from None
    evidence = tuple(str(getattr(ref, "evidence_id", "") or "") for ref in refs)
    if not evidence or any(not row for row in evidence) or len(evidence) != len(set(evidence)):
        raise CMEEStage1ContractError("stage1_semantic_plan_evidence_invalid")
    return evidence


def _source_owner(source: AdmittedTextSource, span_ids: Sequence[str]) -> str:
    try:
        owners = _ordered(source.meaning_owner_for_span(span_id) for span_id in span_ids)
    except Exception:
        raise CMEEStage1ContractError("stage1_semantic_plan_owner_unresolved") from None
    if len(owners) != 1:
        raise CMEEStage1ContractError("stage1_semantic_plan_owner_ambiguous")
    return owners[0]


def _bind_grounded_plan(
    source: AdmittedTextSource,
    graph: GroundedMeaningGraph,
    grounded_plan: GroundedObservationPlan,
) -> _PlanBinding:
    envelope = getattr(source, "envelope", None)
    owner_universe = getattr(source, "owner_universe", None)
    if (
        envelope is None
        or owner_universe is None
        or getattr(envelope, "envelope_id", None) != graph.source_envelope_id
        or getattr(owner_universe, "source_version", None) != graph.source_version
        or getattr(owner_universe, "obligation_version", None)
        != graph.obligation_version
        or getattr(owner_universe, "owner_universe_digest", None)
        != graph.owner_universe_digest
    ):
        raise CMEEStage1ContractError("stage1_source_evidence_unreachable")
    nuclei = getattr(grounded_plan, "nuclei", None)
    relations = getattr(grounded_plan, "relations", None)
    coverage = getattr(grounded_plan, "coverage_requirements", None)
    if type(nuclei) is not tuple or type(relations) is not tuple or coverage is None:
        raise CMEEStage1ContractError("stage1_semantic_plan_shape_invalid")
    required_nucleus_refs = getattr(coverage, "required_nucleus_ids", None)
    required_relation_refs = getattr(coverage, "required_relation_ids", None)
    if type(required_nucleus_refs) is not tuple or type(required_relation_refs) is not tuple:
        raise CMEEStage1ContractError("stage1_semantic_plan_required_refs_invalid")

    node_meta: dict[str, object] = {}
    nucleus_to_node: dict[str, str] = {}
    source_order: dict[str, int] = {}
    used_nodes: set[str] = set()
    for index, nucleus in enumerate(nuclei):
        grounding = _enum_or_text(getattr(nucleus, "grounding_kind", ""))
        if grounding not in _ADMITTED_NUCLEUS_GROUNDING:
            continue
        nucleus_id = str(getattr(nucleus, "nucleus_id", "") or "")
        kind = _enum_or_text(getattr(nucleus, "kind", ""))
        span_ids = getattr(nucleus, "source_span_ids", None)
        if not nucleus_id or not kind or type(span_ids) is not tuple:
            raise CMEEStage1ContractError("stage1_semantic_plan_nucleus_invalid")
        evidence = _source_evidence_ids(source, span_ids)
        owner = _source_owner(source, span_ids)
        matches = tuple(
            row
            for row in graph.nodes
            if row.node_id not in used_nodes
            and row.owner_id == owner
            and _enum_or_text(row.node_kind) == kind
            and _enum_or_text(row.grounding_kind) == grounding
            and tuple(row.evidence_ids) == evidence
            and row.epistemic_state is EpistemicState.SOURCE_EXPLICIT
        )
        if len(matches) != 1:
            raise CMEEStage1ContractError("stage1_source_evidence_unreachable")
        node = matches[0]
        used_nodes.add(node.node_id)
        nucleus_to_node[nucleus_id] = node.node_id
        node_meta[node.node_id] = nucleus
        source_order[node.node_id] = index

    edge_meta: dict[str, object] = {}
    relation_to_edge: dict[str, str] = {}
    used_edges: set[str] = set()
    relation_offset = len(nuclei)
    for index, relation in enumerate(relations):
        grounding = _enum_or_text(getattr(relation, "grounding_kind", ""))
        if grounding not in _ADMITTED_RELATION_GROUNDING:
            continue
        relation_id = str(getattr(relation, "relation_id", "") or "")
        relation_kind = _enum_or_text(getattr(relation, "type", ""))
        from_id = str(getattr(relation, "from_nucleus_id", "") or "")
        to_id = str(getattr(relation, "to_nucleus_id", "") or "")
        span_ids = getattr(relation, "source_span_ids", None)
        if (
            not relation_id
            or not relation_kind
            or type(span_ids) is not tuple
            or from_id not in nucleus_to_node
            or to_id not in nucleus_to_node
        ):
            raise CMEEStage1ContractError("stage1_semantic_plan_relation_invalid")
        evidence = _source_evidence_ids(source, span_ids)
        owner = _source_owner(source, span_ids)
        matches = tuple(
            row
            for row in graph.edges
            if row.edge_id not in used_edges
            and row.owner_id == owner
            and _enum_or_text(row.relation) == relation_kind
            and row.source_node_id == nucleus_to_node[from_id]
            and row.target_node_id == nucleus_to_node[to_id]
            and _enum_or_text(row.grounding_kind) == grounding
            and tuple(row.evidence_ids) == evidence
            and row.epistemic_state is EpistemicState.SOURCE_EXPLICIT
        )
        if len(matches) != 1:
            raise CMEEStage1ContractError("stage1_source_evidence_unreachable")
        edge = matches[0]
        used_edges.add(edge.edge_id)
        relation_to_edge[relation_id] = edge.edge_id
        edge_meta[edge.edge_id] = relation
        source_order[edge.edge_id] = relation_offset + index

    if any(ref not in nucleus_to_node for ref in required_nucleus_refs):
        raise CMEEStage1ContractError("stage1_required_nucleus_unresolved")
    if any(ref not in relation_to_edge for ref in required_relation_refs):
        raise CMEEStage1ContractError("stage1_required_relation_unresolved")
    required_edges = frozenset(relation_to_edge[ref] for ref in required_relation_refs)
    covered_nodes = {
        endpoint
        for edge in graph.edges
        if edge.edge_id in required_edges
        for endpoint in (edge.source_node_id, edge.target_node_id)
    }
    required_nodes = frozenset(
        nucleus_to_node[ref]
        for ref in required_nucleus_refs
        if nucleus_to_node[ref] not in covered_nodes
    )
    return _PlanBinding(
        node_meta=node_meta,
        edge_meta=edge_meta,
        nucleus_to_node=nucleus_to_node,
        relation_to_edge=relation_to_edge,
        required_node_ids=required_nodes,
        required_edge_ids=required_edges,
        source_order=source_order,
    )


def _resolve_binding(
    graph: GroundedMeaningGraph,
    parent_plan: ExperiencePlan,
    *,
    source: AdmittedTextSource,
    grounded_plan: GroundedObservationPlan,
    visible_claim_ids: set[str],
) -> _PlanBinding:
    _validate_canonical_semantic_inputs(
        source,
        grounded_plan,
        graph,
        parent_plan,
    )
    binding = _bind_grounded_plan(source, graph, grounded_plan)
    node_by_id = {row.node_id: row for row in graph.nodes}
    edge_by_id = {row.edge_id: row for row in graph.edges}
    required_owners = set(parent_plan.required_observation_owner_ids)
    required_edge_ids = frozenset(
        binding.relation_to_edge[relation_id]
        for relation_id in grounded_plan.coverage_requirements.required_relation_ids
        if edge_by_id[binding.relation_to_edge[relation_id]].owner_id
        in required_owners
        and binding.relation_to_edge[relation_id] in visible_claim_ids
    )
    relation_covered_node_ids = {
        endpoint
        for edge_id in required_edge_ids
        for endpoint in (
            edge_by_id[edge_id].source_node_id,
            edge_by_id[edge_id].target_node_id,
        )
    }
    required_node_ids = frozenset(
        binding.nucleus_to_node[nucleus_id]
        for nucleus_id in grounded_plan.coverage_requirements.required_nucleus_ids
        if node_by_id[binding.nucleus_to_node[nucleus_id]].owner_id
        in required_owners
        and binding.nucleus_to_node[nucleus_id] in visible_claim_ids
        and binding.nucleus_to_node[nucleus_id]
        not in relation_covered_node_ids
    )
    binding = replace(
        binding,
        required_node_ids=required_node_ids,
        required_edge_ids=required_edge_ids,
    )
    admitted_nodes = {
        row.node_id
        for row in graph.nodes
        if row.epistemic_state is EpistemicState.SOURCE_EXPLICIT
        and _enum_or_text(row.grounding_kind) in _ADMITTED_NUCLEUS_GROUNDING
    }
    admitted_edges = {
        row.edge_id
        for row in graph.edges
        if row.epistemic_state is EpistemicState.SOURCE_EXPLICIT
        and _enum_or_text(row.grounding_kind) in _ADMITTED_RELATION_GROUNDING
    }
    if (
        admitted_nodes != set(binding.node_meta)
        or admitted_edges != set(binding.edge_meta)
    ):
        raise CMEEStage1ContractError("stage1_source_evidence_unreachable")
    visible_nodes = {
        row.node_id for row in graph.nodes if row.node_id in visible_claim_ids
    }
    visible_edges = {
        row.edge_id for row in graph.edges if row.edge_id in visible_claim_ids
    }
    if not binding.required_node_ids.issubset(visible_nodes) or not binding.required_edge_ids.issubset(visible_edges):
        raise CMEEStage1ContractError("stage1_required_semantic_not_visible")
    required_semantic_owners = {
        *(node_by_id[row].owner_id for row in binding.required_node_ids),
        *(edge_by_id[row].owner_id for row in binding.required_edge_ids),
    }
    if not required_owners.issubset(required_semantic_owners):
        raise CMEEStage1ContractError("stage1_required_owner_uncovered")
    return binding


def stage1_required_projection_nucleus_ids(
    *,
    source: AdmittedTextSource,
    grounded_graph: GroundedMeaningGraph,
    parent_plan: ExperiencePlan,
    grounded_plan: GroundedObservationPlan,
) -> tuple[str, ...]:
    """Return the exact canonical nucleus coverage owned by Stage 1.

    Required relations cover both endpoints. The ExperiencePlan's required
    owner duty is the exact Stage 1 denominator; active-optional source owners
    remain available for evidence but cannot silently become required output.
    """

    visible_claim_ids = _visible_claim_ids(grounded_graph, parent_plan)
    binding = _resolve_binding(
        grounded_graph,
        parent_plan,
        source=source,
        grounded_plan=grounded_plan,
        visible_claim_ids=visible_claim_ids,
    )
    edge_by_id = {row.edge_id: row for row in grounded_graph.edges}
    required_node_ids = set(binding.required_node_ids)
    for edge_id in binding.required_edge_ids:
        edge = edge_by_id.get(edge_id)
        if edge is None:
            raise CMEEStage1ContractError("stage1_required_relation_unresolved")
        required_node_ids.update((edge.source_node_id, edge.target_node_id))
    return tuple(
        nucleus.nucleus_id
        for nucleus in grounded_plan.nuclei
        if binding.nucleus_to_node.get(nucleus.nucleus_id) in required_node_ids
    )


def _qualifiers(
    meta: Optional[object],
    *,
    role: Optional[str] = None,
    source_explicit_shift_relation_endpoint: bool = False,
    include_relation_endpoint_source_contract: bool = False,
    stage1_response_schema_version: str = CMEE_STAGE1_RESPONSE_SCHEMA_VERSION,
) -> tuple[str, ...]:
    if meta is None:
        return (_PROVISIONAL_QUALIFIER,)
    frame = getattr(meta, "semantic_frame", None)
    if frame is None:
        return (_PROVISIONAL_QUALIFIER,)
    prefix = f"{role.lower()}_" if role else ""
    values = (
        ("actor", _enum_or_text(getattr(frame, "actor", ""))),
        ("polarity", _enum_or_text(getattr(frame, "polarity", ""))),
        ("modality", _enum_or_text(getattr(frame, "modality", ""))),
        ("time_scope", _enum_or_text(getattr(frame, "time_scope", ""))),
    )
    if stage1_response_schema_version == CMEE_STAGE1_RESPONSE_SCHEMA_VERSION_V2:
        aspects = tuple(
            code.split(":", 1)[1]
            for code in frame.attribute_codes if code.startswith("aspect:")
        )
        if len(aspects) > 1 or aspects and aspects[0] not in {
            "unknown", "source_bounded", "not_applicable", "completed",
            "perfective", "ongoing", "progressive",
        }:
            raise CMEEStage1ContractError("stage1_source_aspect_invalid")
        values = (values[0], ("aspect", aspects[0] if aspects else "unknown"), *values[1:])
    source_contract_qualifiers = project_stage1_source_contract_qualifiers(
        source_attribute_codes=tuple(
            getattr(frame, "attribute_codes", ())
        ),
        source_explicit_shift_relation_endpoint=(
            source_explicit_shift_relation_endpoint
        ),
        stage1_response_schema_version=stage1_response_schema_version,
    )
    if not role and not include_relation_endpoint_source_contract:
        source_contract_qualifiers = tuple(
            value
            for value in source_contract_qualifiers
            if not value.startswith(
                "qualifier:semantic_role:direction_under_burden_"
            )
        )
    return (
        _PROVISIONAL_QUALIFIER,
        *(f"{prefix}{name}:{value}" for name, value in values if value),
        *(f"{prefix}{value}" for value in source_contract_qualifiers),
    )


def _retention_rank(meta: object, *, required: bool) -> int:
    retention = _enum_or_text(getattr(meta, "retention", "")).lower()
    try:
        rank = _RETENTION_PRIORITY[retention]
    except KeyError:
        raise CMEEStage1ContractError("stage1_retention_invalid") from None
    if required and retention != "required":
        raise CMEEStage1ContractError("stage1_required_retention_mismatch")
    return rank


def _direct_shape(
    node: MeaningNode,
    meta: Optional[object],
) -> tuple[InterpretationKind, SemanticOperator]:
    kind = _enum_or_text(node.node_kind).lower()
    frame = getattr(meta, "semantic_frame", None)
    modality = _enum_or_text(getattr(frame, "modality", "")).lower()
    predicate = _enum_or_text(getattr(frame, "predicate_kind", "")).lower()
    attribute_codes = frozenset(
        _enum_or_text(row)
        for row in getattr(frame, "attribute_codes", ())
        if _enum_or_text(row)
    )
    if kind in _DIRECTION_KINDS or modality in {"wish", "intention"} or predicate == "wish":
        return InterpretationKind.DIRECT_DIRECTION, SemanticOperator.PRESENT_DIRECTION
    if (
        kind in _CHANGE_KINDS
        or predicate == "change"
        or "operator:change" in attribute_codes
        or "operator:positive_change" in attribute_codes
    ):
        return InterpretationKind.DIRECT_STATE, SemanticOperator.PRESENT_CHANGE
    if (
        kind in _UNFINISHED_KINDS
        or predicate == "unfinished"
        or "operator:unfinished" in attribute_codes
    ):
        return InterpretationKind.UNFINISHED, SemanticOperator.PRESENT_UNFINISHED
    if (
        kind in _BURDEN_KINDS
        or predicate == "constraint"
        or "operator:constraint" in attribute_codes
        or "detected_type:limit_signal" in attribute_codes
        or "detected_type:fear" in attribute_codes
        or any(row.startswith("source_claim:pressure.") for row in attribute_codes)
    ):
        return InterpretationKind.DIRECT_STATE, SemanticOperator.PRESENT_BURDEN
    if (
        kind in _ACTION_KINDS
        or predicate == "action"
        or "operator:action" in attribute_codes
    ):
        return InterpretationKind.DIRECT_STATE, SemanticOperator.PRESENT_ACTUAL_OUTPUT
    if modality == "uncertain" or "operator:uncertainty" in attribute_codes:
        return InterpretationKind.UNFINISHED, SemanticOperator.PRESENT_UNFINISHED
    return InterpretationKind.DIRECT_STATE, SemanticOperator.PRESENT_STATE


def _direct_shape_v2(
    node: MeaningNode,
    meta: Optional[object],
) -> tuple[InterpretationKind, SemanticOperator]:
    """Project the v2 node-kind-authoritative direct shape."""

    kind = _enum_or_text(node.node_kind).lower()
    frame = getattr(meta, "semantic_frame", None)
    predicate = _enum_or_text(getattr(frame, "predicate_kind", "")).lower()
    attribute_codes = frozenset(
        _enum_or_text(row)
        for row in getattr(frame, "attribute_codes", ())
        if _enum_or_text(row)
    )
    if kind in _DIRECTION_KINDS:
        return (
            InterpretationKind.DIRECT_DIRECTION,
            SemanticOperator.PRESENT_DIRECTION,
        )
    if kind in _CHANGE_KINDS:
        return InterpretationKind.DIRECT_STATE, SemanticOperator.PRESENT_CHANGE
    if kind in _UNFINISHED_KINDS:
        return InterpretationKind.UNFINISHED, SemanticOperator.PRESENT_UNFINISHED
    if kind in _BURDEN_KINDS:
        return InterpretationKind.DIRECT_STATE, SemanticOperator.PRESENT_BURDEN
    if kind in _ACTION_KINDS:
        return InterpretationKind.DIRECT_STATE, SemanticOperator.PRESENT_ACTUAL_OUTPUT
    metadata_burden = (
        predicate == "constraint"
        or "operator:constraint" in attribute_codes
        or "detected_type:limit_signal" in attribute_codes
        or "detected_type:fear" in attribute_codes
        or any(
            row.startswith("source_claim:pressure.")
            for row in attribute_codes
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
        return InterpretationKind.DIRECT_STATE, SemanticOperator.PRESENT_BURDEN
    return InterpretationKind.DIRECT_STATE, SemanticOperator.PRESENT_STATE


def _direct_shape_for_schema(
    node: MeaningNode,
    meta: Optional[object],
    *,
    stage1_response_schema_version: str,
) -> tuple[InterpretationKind, SemanticOperator]:
    if stage1_response_schema_version == CMEE_STAGE1_RESPONSE_SCHEMA_VERSION_V1:
        return _direct_shape(node, meta)
    if (
        stage1_response_schema_version
        == CMEE_STAGE1_RESPONSE_SCHEMA_VERSION_V2
    ):
        return _direct_shape_v2(node, meta)
    raise CMEEStage1ContractError("stage1_response_schema_version_invalid")


def project_direct_argument_bindings(
    source_semantic_ref: str,
    grounded_frame: Optional[GroundedSemanticFrame],
) -> tuple[ArgumentBinding, ...]:
    """Project the sole direct-candidate argument binding table.

    This pure upstream-only seam is shared by candidate construction and the
    additional-correction phase-A validator.  It deliberately accepts neither
    a contribution nor a projection, both of which are created later.
    """

    if not source_semantic_ref:
        raise CMEEStage1ContractError("stage1_semantic_ref_invalid")
    bindings = [ArgumentBinding(ArgumentRole.PRIMARY, source_semantic_ref)]
    modality = _enum_or_text(getattr(grounded_frame, "modality", "")).lower()
    actor = _enum_or_text(getattr(grounded_frame, "actor", "")).lower()
    if actor in {"current_user", "user"} and modality in {
        "feeling",
        "wish",
        "intention",
        "refusal",
        "uncertain",
    }:
        # The experiencer binding reuses the same canonical source proposition;
        # it never creates a person node or a free-form semantic ref.
        bindings.append(
            ArgumentBinding(ArgumentRole.EXPERIENCER, source_semantic_ref)
        )
    return tuple(bindings)


def _direct_argument_bindings(
    node: MeaningNode,
    meta: Optional[object],
) -> tuple[ArgumentBinding, ...]:
    return project_direct_argument_bindings(
        _node_ref(node.node_id),
        getattr(meta, "semantic_frame", None),
    )


def _validate_interpretation_matrix(
    candidate: EmlisInterpretationCandidate,
) -> None:
    validate_stage1_interpretation_matrix(candidate)


def _relation_shape(
    edge: MeaningEdge,
    node_by_id: Mapping[str, MeaningNode],
    binding: _PlanBinding,
    *,
    stage1_response_schema_version: str = CMEE_STAGE1_RESPONSE_SCHEMA_VERSION_V1,
) -> Optional[
    tuple[
        InterpretationKind,
        SemanticOperator,
        RelationOperator,
        tuple[ArgumentBinding, ...],
    ]
]:
    source = node_by_id[edge.source_node_id]
    target = node_by_id[edge.target_node_id]
    source_meta = binding.node_meta.get(source.node_id)
    target_meta = binding.node_meta.get(target.node_id)
    source_frame = getattr(source_meta, "semantic_frame", None)
    target_frame = getattr(target_meta, "semantic_frame", None)
    return project_stage1_relation_shape(
        relation_kind=_enum_or_text(edge.relation),
        source_ref=_node_ref(source.node_id),
        target_ref=_node_ref(target.node_id),
        source_node_kind=_enum_or_text(source.node_kind),
        target_node_kind=_enum_or_text(target.node_kind),
        source_direct_shape=_direct_shape_for_schema(
            source,
            source_meta,
            stage1_response_schema_version=stage1_response_schema_version,
        ),
        target_direct_shape=_direct_shape_for_schema(
            target,
            target_meta,
            stage1_response_schema_version=stage1_response_schema_version,
        ),
        source_time_scope=_enum_or_text(
            getattr(source_frame, "time_scope", "")
        ),
        target_time_scope=_enum_or_text(
            getattr(target_frame, "time_scope", "")
        ),
        source_attribute_codes=tuple(
            getattr(source_frame, "attribute_codes", ())
        ),
        target_attribute_codes=tuple(
            getattr(target_frame, "attribute_codes", ())
        ),
        source_order=binding.source_order.get(source.node_id),
        target_order=binding.source_order.get(target.node_id),
        edge_grounding_kind=edge.grounding_kind,
        edge_epistemic_state=edge.epistemic_state,
        edge_evidence_ids=edge.evidence_ids,
        stage1_response_schema_version=stage1_response_schema_version,
    )


def _candidate_from_direct(
    graph: GroundedMeaningGraph,
    node: MeaningNode,
    meta: Optional[object],
    *,
    include_relation_endpoint_source_contract: bool = False,
    stage1_response_schema_version: str = CMEE_STAGE1_RESPONSE_SCHEMA_VERSION,
) -> EmlisInterpretationCandidate:
    kind, semantic_operator = _direct_shape_for_schema(
        node,
        meta,
        stage1_response_schema_version=stage1_response_schema_version,
    )
    semantic_ref = _node_ref(node.node_id)
    shift_endpoint_node_ids = (
        project_stage1_source_explicit_shift_endpoint_node_ids(graph)
    )
    candidate = EmlisInterpretationCandidate(
        schema_version=stage1_response_schema_version,
        candidate_id="",
        candidate_kind=kind,
        claim_domain=EmlisTraceClaimDomain.INTERPRETIVE_OBSERVATION.value,
        semantic_operator=semantic_operator,
        argument_bindings=_direct_argument_bindings(node, meta),
        relation_operator=RelationOperator.NO_RELATION_CLAIM,
        relation_basis_refs=(),
        derivation_rule_id=(
            f"cocolon.cmee.v1a.stage1.direct.{kind.value.lower()}.v1"
        ),
        semantic_refs=(semantic_ref,),
        evidence_refs=tuple(
            _evidence_ref(row, graph.source_version) for row in node.evidence_ids
        ),
        basis_candidate_refs=(),
        epistemic_state=InterpretationEpistemicState.PROVISIONAL_INTERPRETATION,
        required_qualifiers=_qualifiers(
            meta,
            source_explicit_shift_relation_endpoint=(
                node.node_id in shift_endpoint_node_ids
            ),
            include_relation_endpoint_source_contract=(
                include_relation_endpoint_source_contract
            ),
            stage1_response_schema_version=(
                stage1_response_schema_version
            ),
        ),
        forbidden_promotions=_FORBIDDEN_PROMOTIONS,
    )
    _validate_interpretation_matrix(candidate)
    return _identified(candidate, "candidate_id")


def _candidate_from_relation(
    graph: GroundedMeaningGraph,
    edge: MeaningEdge,
    binding: _PlanBinding,
    shape: tuple[
        InterpretationKind,
        SemanticOperator,
        RelationOperator,
        tuple[ArgumentBinding, ...],
    ],
    *,
    stage1_response_schema_version: str = CMEE_STAGE1_RESPONSE_SCHEMA_VERSION,
) -> EmlisInterpretationCandidate:
    kind, semantic_operator, relation_operator, arguments = shape
    node_by_id = {row.node_id: row for row in graph.nodes}
    semantic_refs = tuple(row.semantic_ref for row in arguments)
    evidence_ids = _ordered(
        (
            *(item for ref in semantic_refs for item in node_by_id[_local_ref(ref)].evidence_ids),
            *edge.evidence_ids,
        )
    )
    qualifiers = [_PROVISIONAL_QUALIFIER]
    shift_endpoint_node_ids = (
        project_stage1_source_explicit_shift_endpoint_node_ids(graph)
    )
    for argument in arguments:
        argument_node_id = _local_ref(argument.semantic_ref)
        meta = binding.node_meta.get(argument_node_id)
        qualifiers.extend(
            _qualifiers(
                meta,
                role=argument.role.value,
                source_explicit_shift_relation_endpoint=(
                    argument_node_id in shift_endpoint_node_ids
                ),
                stage1_response_schema_version=(
                    stage1_response_schema_version
                ),
            )[1:]
        )
    source_frame = getattr(
        binding.node_meta.get(edge.source_node_id),
        "semantic_frame",
        None,
    )
    target_frame = getattr(
        binding.node_meta.get(edge.target_node_id),
        "semantic_frame",
        None,
    )
    qualifiers = list(
        project_stage1_relation_required_qualifiers(
            candidate_kind=kind,
            role_qualified_values=qualifiers,
            source_attribute_codes=tuple(
                getattr(source_frame, "attribute_codes", ())
            ),
            target_attribute_codes=tuple(
                getattr(target_frame, "attribute_codes", ())
            ),
            stage1_response_schema_version=(
                stage1_response_schema_version
            ),
        )
    )
    candidate = EmlisInterpretationCandidate(
        schema_version=stage1_response_schema_version,
        candidate_id="",
        candidate_kind=kind,
        claim_domain=EmlisTraceClaimDomain.INTERPRETIVE_OBSERVATION.value,
        semantic_operator=semantic_operator,
        argument_bindings=arguments,
        relation_operator=relation_operator,
        relation_basis_refs=(_edge_ref(edge.edge_id),),
        derivation_rule_id=(
            "cocolon.cmee.v1a.stage1.relation."
            f"{_enum_or_text(edge.relation).lower()}.v1"
        ),
        semantic_refs=semantic_refs,
        evidence_refs=tuple(
            _evidence_ref(row, graph.source_version) for row in evidence_ids
        ),
        basis_candidate_refs=(),
        epistemic_state=InterpretationEpistemicState.PROVISIONAL_INTERPRETATION,
        required_qualifiers=tuple(qualifiers),
        forbidden_promotions=_FORBIDDEN_PROMOTIONS,
    )
    _validate_interpretation_matrix(candidate)
    return _identified(candidate, "candidate_id")


def _local_ref(value: str) -> str:
    try:
        return value.split(":", 1)[1].rsplit("@", 1)[0]
    except (IndexError, AttributeError):
        raise CMEEStage1ContractError("stage1_semantic_ref_invalid") from None


def _candidate_rows(
    graph: GroundedMeaningGraph,
    parent_plan: ExperiencePlan,
    *,
    source: AdmittedTextSource,
    grounded_plan: GroundedObservationPlan,
    stage1_response_schema_version: str = CMEE_STAGE1_RESPONSE_SCHEMA_VERSION,
) -> tuple[_CandidateRow, ...]:
    _validate_graph_and_parent(graph, parent_plan)
    _validate_canonical_semantic_inputs(
        source,
        grounded_plan,
        graph,
        parent_plan,
    )
    visible_claim_ids = _visible_claim_ids(graph, parent_plan)
    binding = _resolve_binding(
        graph,
        parent_plan,
        source=source,
        grounded_plan=grounded_plan,
        visible_claim_ids=visible_claim_ids,
    )
    node_by_id = {row.node_id: row for row in graph.nodes}
    obligation_kind_by_owner = {
        row.meaning_owner_id: row.obligation_kind
        for row in source.owner_universe.obligations
    }
    rows: list[_CandidateRow] = []

    # Required relations own endpoint coverage before direct alternatives.
    for edge in graph.edges:
        if edge.edge_id not in visible_claim_ids:
            continue
        required = edge.edge_id in binding.required_edge_ids
        endpoints = (
            node_by_id[edge.source_node_id],
            node_by_id[edge.target_node_id],
        )
        if edge.source_node_id == edge.target_node_id:
            if required:
                raise CMEEStage1ContractError(
                    "stage1_relation_direction_invalid"
                )
            continue
        if (
            edge.epistemic_state is not EpistemicState.SOURCE_EXPLICIT
            or _enum_or_text(edge.grounding_kind)
            not in _ADMITTED_RELATION_GROUNDING
            or not edge.evidence_ids
            or len(edge.evidence_ids) != len(set(edge.evidence_ids))
            or any(
                node.epistemic_state is not EpistemicState.SOURCE_EXPLICIT
                or _enum_or_text(node.grounding_kind)
                not in _ADMITTED_NUCLEUS_GROUNDING
                or not node.evidence_ids
                or len(node.evidence_ids) != len(set(node.evidence_ids))
                for node in endpoints
            )
        ):
            if required:
                raise CMEEStage1ContractError("stage1_source_evidence_unreachable")
            continue
        shape = _relation_shape(
            edge,
            node_by_id,
            binding,
            stage1_response_schema_version=stage1_response_schema_version,
        )
        if shape is None:
            if required:
                relation_kind = _enum_or_text(edge.relation)
                if _cause_like_relation(relation_kind):
                    raise CMEEStage1ContractError("stage1_unsupported_cause")
                if relation_kind in {
                    "wish_and_constraint",
                    "preserves_despite",
                    "attempt_and_block",
                    "action_supports_change",
                    "temporal_before_after",
                    "shift_from_to",
                }:
                    raise CMEEStage1ContractError(
                        "stage1_relation_direction_invalid"
                    )
                raise CMEEStage1ContractError(
                    "stage1_interpretation_matrix_invalid"
                )
            continue
        candidate = _candidate_from_relation(
            graph,
            edge,
            binding,
            shape,
            stage1_response_schema_version=stage1_response_schema_version,
        )
        rows.append(
            _CandidateRow(
                candidate=candidate,
                required=required,
                is_relation=True,
                obligation_kind=obligation_kind_by_owner[edge.owner_id],
                retention_rank=_retention_rank(
                    binding.edge_meta[edge.edge_id], required=required
                ),
                source_order=binding.source_order.get(edge.edge_id, len(graph.nodes)),
            )
        )

    for node in graph.nodes:
        if node.node_id not in visible_claim_ids:
            continue
        required = node.node_id in binding.required_node_ids
        if (
            node.epistemic_state is not EpistemicState.SOURCE_EXPLICIT
            or _enum_or_text(node.grounding_kind)
            not in _ADMITTED_NUCLEUS_GROUNDING
            or not node.evidence_ids
            or len(node.evidence_ids) != len(set(node.evidence_ids))
        ):
            if required:
                raise CMEEStage1ContractError("stage1_source_evidence_unreachable")
            # UNKNOWN and source-explicit-not-realized rows never become an
            # InterpretationCandidate.
            continue
        candidate = _candidate_from_direct(
            graph,
            node,
            binding.node_meta.get(node.node_id),
            stage1_response_schema_version=stage1_response_schema_version,
        )
        rows.append(
            _CandidateRow(
                candidate=candidate,
                required=required,
                is_relation=False,
                obligation_kind=obligation_kind_by_owner[node.owner_id],
                retention_rank=_retention_rank(
                    binding.node_meta[node.node_id], required=required
                ),
                source_order=binding.source_order.get(node.node_id, 0),
            )
        )

    direct_semantic_refs = {
        argument.semantic_ref
        for row in rows
        if not row.is_relation
        for argument in row.candidate.argument_bindings
        if argument.role is ArgumentRole.PRIMARY
    }
    rows = [
        row
        for row in rows
        if not (
            row.is_relation
            and not row.required
            and any(
                argument.semantic_ref not in direct_semantic_refs
                for argument in row.candidate.argument_bindings
            )
        )
    ]
    if not rows:
        raise CMEEStage1ContractError("stage1_candidate_pool_empty")
    foreground_required_flags = stage1_foreground_coverage_required_flags(
        candidate_semantic_refs=tuple(
            row.candidate.semantic_refs for row in rows
        ),
        source_required_flags=tuple(row.required for row in rows),
        relation_flags=tuple(row.is_relation for row in rows),
        foreground_object_refs=(
            stage1_source_explicit_target_topic_scope_refs(graph)
        ),
    )
    rows = [
        replace(row, required=foreground_required_flags[index])
        for index, row in enumerate(rows)
    ]
    rows.sort(
        key=lambda row: (
            0 if row.required else 1,
            0 if row.is_relation else 1,
            row.retention_rank,
            row.source_order,
            _OPERATOR_PRIORITY[row.candidate.relation_operator],
            row.candidate.semantic_refs,
            row.candidate.candidate_id,
        )
    )

    selected = [
        rows[index]
        for index in stage1_candidate_selection_indices(
            tuple(row.candidate.candidate_kind for row in rows),
            tuple(row.required for row in rows),
        )
    ]
    if not selected or not any(row.required for row in selected):
        raise CMEEStage1ContractError("stage1_required_candidate_missing")
    return tuple(selected)


def _interpretation_candidates_from_rows(
    rows: Sequence[_CandidateRow],
) -> tuple[EmlisInterpretationCandidate, ...]:
    candidates = tuple(row.candidate for row in rows)
    if len(candidates) > INTERPRETATION_CANDIDATE_POOL_CAP:
        raise CMEEStage1ContractError("stage1_candidate_pool_cap_exceeded")
    for candidate in candidates:
        validate_stage1_identity(candidate)
    return candidates


def build_interpretation_candidate_pool(
    grounded_graph: GroundedMeaningGraph,
    parent_plan: ExperiencePlan,
    *,
    source: AdmittedTextSource,
    grounded_plan: GroundedObservationPlan,
    stage1_response_schema_version: str = CMEE_STAGE1_RESPONSE_SCHEMA_VERSION,
) -> tuple[EmlisInterpretationCandidate, ...]:
    """Build the canonical bounded provisional InterpretationCandidate pool."""

    rows = _candidate_rows(
        grounded_graph,
        parent_plan,
        source=source,
        grounded_plan=grounded_plan,
        stage1_response_schema_version=stage1_response_schema_version,
    )
    return _interpretation_candidates_from_rows(rows)


def validate_interpretation_candidate_pool(
    candidates: Sequence[EmlisInterpretationCandidate],
    *,
    grounded_graph: GroundedMeaningGraph,
    parent_plan: ExperiencePlan,
    source: AdmittedTextSource,
    grounded_plan: GroundedObservationPlan,
    stage1_response_schema_version: str = CMEE_STAGE1_RESPONSE_SCHEMA_VERSION,
) -> None:
    if type(candidates) is not tuple:
        raise CMEEStage1ContractError("stage1_candidate_pool_not_tuple")
    expected = build_interpretation_candidate_pool(
        grounded_graph,
        parent_plan,
        source=source,
        grounded_plan=grounded_plan,
        stage1_response_schema_version=stage1_response_schema_version,
    )
    if tuple(candidates) != expected:
        raise CMEEStage1ContractError("stage1_candidate_pool_noncanonical")


def _candidate_slot(candidate: EmlisInterpretationCandidate) -> MeaningFieldSlot:
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
    if candidate.candidate_kind in {
        InterpretationKind.ACTION_BEFORE_AFTER,
        InterpretationKind.BOUNDED_SOURCE_ORDER,
        InterpretationKind.SOURCE_STATED_TRANSITION,
    }:
        return MeaningFieldSlot.TIME_RELATION
    if candidate.candidate_kind is InterpretationKind.SOURCE_STATED_CAUSE:
        return MeaningFieldSlot.TIME_RELATION
    if candidate.semantic_operator is SemanticOperator.PRESENT_BURDEN:
        return MeaningFieldSlot.BURDEN
    if candidate.semantic_operator is SemanticOperator.PRESENT_CHANGE:
        return MeaningFieldSlot.CHANGE
    if candidate.semantic_operator is SemanticOperator.PRESENT_ACTUAL_OUTPUT:
        return MeaningFieldSlot.OUTPUT
    return MeaningFieldSlot.CENTER


def _entry(
    slot: MeaningFieldSlot,
    candidates: Sequence[EmlisInterpretationCandidate],
) -> MeaningFieldEntry:
    return MeaningFieldEntry(
        slot=slot,
        interpretation_candidate_refs=tuple(row.candidate_id for row in candidates),
        semantic_refs=_ordered(ref for row in candidates for ref in row.semantic_refs),
        evidence_refs=_ordered(ref for row in candidates for ref in row.evidence_refs),
    )


def _material_unknown_refs(
    graph: GroundedMeaningGraph,
    parent_plan: ExperiencePlan,
    source: AdmittedTextSource,
) -> tuple[str, ...]:
    unknown_owners = tuple(parent_plan.visible_unknown_owner_ids)
    if (
        any(type(row) is not str or not row for row in unknown_owners)
        or len(unknown_owners) != len(set(unknown_owners))
        or not set(parent_plan.required_unknown_owner_ids).issubset(
            set(unknown_owners)
        )
        or not set(unknown_owners).issubset(set(parent_plan.unresolved_owner_ids))
    ):
        raise CMEEStage1ContractError("stage1_material_unknown_owner_invalid")
    disposition = {row.meaning_owner_id: row for row in graph.owner_dispositions}
    if len(disposition) != len(graph.owner_dispositions):
        raise CMEEStage1ContractError("stage1_owner_disposition_duplicate")
    node_by_id = {row.node_id: row for row in graph.nodes}
    source_evidence_ids = {row.evidence_id for row in source.evidence_refs}
    refs: list[str] = []
    for owner_id in unknown_owners:
        row = disposition.get(owner_id)
        target = row.target_unknown_ref if row is not None else None
        node = node_by_id.get(str(target or ""))
        if (
            row is None
            or row.source_owner_disposition
            is not SourceOwnerDisposition.UNKNOWN_PRESERVED_LIMITED
            or type(target) is not str
            or not target
            or row.visible_claim_refs != (target,)
            or node is None
            or node.owner_id != owner_id
            or node.epistemic_state is not EpistemicState.UNKNOWN
            or not node.evidence_ids
            or len(node.evidence_ids) != len(set(node.evidence_ids))
            or tuple(node.evidence_ids) != tuple(row.evidence_refs)
            or not set(node.evidence_ids).issubset(source_evidence_ids)
        ):
            raise CMEEStage1ContractError("stage1_material_unknown_unreachable")
        refs.append(f"unknown:{target}@{graph.obligation_version}")
    return tuple(refs)


def _build_emlis_meaning_field_from_rows(
    grounded_graph: GroundedMeaningGraph,
    parent_plan: ExperiencePlan,
    rows: Sequence[_CandidateRow],
    *,
    source: AdmittedTextSource,
    stage1_response_schema_version: str = CMEE_STAGE1_RESPONSE_SCHEMA_VERSION,
) -> EmlisMeaningField:
    candidate_tuple = _interpretation_candidates_from_rows(rows)
    required = tuple(row.candidate.candidate_id for row in rows if row.required)
    required_set = set(required)
    center = next(
        (row for row in candidate_tuple if row.candidate_id in required_set),
        candidate_tuple[0],
    )
    grouped: dict[MeaningFieldSlot, list[EmlisInterpretationCandidate]] = {}
    for candidate in candidate_tuple:
        grouped.setdefault(_candidate_slot(candidate), []).append(candidate)
    # ``center_candidate_ref`` owns request-local product attention.  Entries
    # own semantic slot membership, so the center pointer is not duplicated
    # into CENTER when its candidate belongs to another material slot.
    entries = tuple(
        _entry(slot, grouped[slot]) for slot in _SLOT_ORDER if grouped.get(slot)
    )
    entry_refs = tuple(
        ref for entry in entries for ref in entry.interpretation_candidate_refs
    )
    if (
        len(entry_refs) != len(set(entry_refs))
        or set(entry_refs) != {row.candidate_id for row in candidate_tuple}
        or any(entry_refs.count(ref) != 1 for ref in required)
    ):
        raise CMEEStage1ContractError(
            "stage1_meaning_field_required_not_exact_cover"
        )
    meaning_field = EmlisMeaningField(
        schema_version=stage1_response_schema_version,
        meaning_field_id="",
        grounded_graph_ref=_graph_ref(grounded_graph),
        center_candidate_ref=center.candidate_id,
        entries=entries,
        required_candidate_refs=required,
        material_unknown_refs=_material_unknown_refs(
            grounded_graph, parent_plan, source
        ),
    )
    result = _identified(meaning_field, "meaning_field_id")
    validate_stage1_identity(result)
    return result


def build_emlis_meaning_field(
    grounded_graph: GroundedMeaningGraph,
    parent_plan: ExperiencePlan,
    candidates: Sequence[EmlisInterpretationCandidate],
    *,
    source: AdmittedTextSource,
    grounded_plan: GroundedObservationPlan,
    stage1_response_schema_version: str = CMEE_STAGE1_RESPONSE_SCHEMA_VERSION,
) -> EmlisMeaningField:
    """Project the canonical pool into Emlis request-local attention slots."""

    rows = _candidate_rows(
        grounded_graph,
        parent_plan,
        source=source,
        grounded_plan=grounded_plan,
        stage1_response_schema_version=stage1_response_schema_version,
    )
    expected_candidates = _interpretation_candidates_from_rows(rows)
    if tuple(candidates) != expected_candidates:
        raise CMEEStage1ContractError("stage1_candidate_pool_noncanonical")
    return _build_emlis_meaning_field_from_rows(
        grounded_graph,
        parent_plan,
        rows,
        source=source,
        stage1_response_schema_version=stage1_response_schema_version,
    )


def validate_emlis_meaning_field(
    meaning_field: EmlisMeaningField,
    *,
    candidates: Sequence[EmlisInterpretationCandidate],
    grounded_graph: GroundedMeaningGraph,
    parent_plan: ExperiencePlan,
    source: AdmittedTextSource,
    grounded_plan: GroundedObservationPlan,
    stage1_response_schema_version: str = CMEE_STAGE1_RESPONSE_SCHEMA_VERSION,
) -> None:
    candidate_ids = tuple(row.candidate_id for row in candidates)
    entry_refs = tuple(
        ref
        for entry in getattr(meaning_field, "entries", ())
        for ref in getattr(entry, "interpretation_candidate_refs", ())
    )
    if (
        type(meaning_field) is not EmlisMeaningField
        or meaning_field.center_candidate_ref not in set(candidate_ids)
        or len(entry_refs) != len(set(entry_refs))
        or set(entry_refs) != set(candidate_ids)
        or any(
            entry_refs.count(ref) != 1
            for ref in meaning_field.required_candidate_refs
        )
    ):
        raise CMEEStage1ContractError(
            "stage1_meaning_field_required_not_exact_cover"
        )
    expected = build_emlis_meaning_field(
        grounded_graph,
        parent_plan,
        tuple(candidates),
        source=source,
        grounded_plan=grounded_plan,
        stage1_response_schema_version=stage1_response_schema_version,
    )
    if meaning_field != expected:
        raise CMEEStage1ContractError("stage1_meaning_field_noncanonical")


def _contribution_kind(
    candidate: EmlisInterpretationCandidate,
) -> ObservationContributionKind:
    slot = _candidate_slot(candidate)
    mapping = {
        MeaningFieldSlot.CENTER: ObservationContributionKind.OBSERVE_CENTER,
        MeaningFieldSlot.COEXISTENCE: ObservationContributionKind.OBSERVE_COEXISTENCE,
        MeaningFieldSlot.TENSION: ObservationContributionKind.OBSERVE_TENSION,
        MeaningFieldSlot.DIRECTION: ObservationContributionKind.OBSERVE_DIRECTION,
        MeaningFieldSlot.BURDEN: ObservationContributionKind.OBSERVE_BURDEN,
        MeaningFieldSlot.CHANGE: (
            ObservationContributionKind.OBSERVE_ACTION_THEN_CHANGE
            if candidate.candidate_kind is InterpretationKind.ACTION_THEN_CHANGE_ONCE
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


def _semantic_key(candidate: EmlisInterpretationCandidate) -> str:
    material = {
        "semantic_key_version": OBSERVATION_SEMANTIC_KEY_VERSION,
        "claim_domain": candidate.claim_domain,
        "semantic_operator": candidate.semantic_operator,
        "argument_bindings": candidate.argument_bindings,
        "relation_operator": candidate.relation_operator,
        "relation_basis_refs": candidate.relation_basis_refs,
        "required_qualifiers": candidate.required_qualifiers,
    }
    digest = hashlib.sha256(stage1_canonical_json_bytes(material)).hexdigest()
    return f"observation-key-{digest}"


def _selected_contribution_candidates(
    rows: Sequence[_CandidateRow],
) -> tuple[_CandidateRow, ...]:
    required = [row for row in rows if row.required]
    if len(required) > LAYER1_OBSERVATION_CONTRIBUTION_CAP:
        raise CMEEStage1ContractError("stage1_required_observation_unrealizable")
    structured_context_kinds = {
        "EMOTION_CONTEXT",
        "CATEGORY_CONTEXT",
        "EMOTION_STRENGTH_CONTEXT",
        "STRUCTURED_CONTEXT_ATTACHMENT",
    }
    optional = [
        row
        for row in rows
        if not row.required
        and row.obligation_kind not in structured_context_kinds
    ]
    # Structured labels remain source-explicit candidate evidence, but cannot
    # manufacture an independently lived state/change sentence.  A genuinely
    # material optional meaning retains the prior bounded exact-one policy.
    selected_optional = optional[:1] if len(required) == 1 else []
    return tuple((*required, *selected_optional))


def _plan_layer1_observation_from_rows(
    parent_plan: ExperiencePlan,
    rows: Sequence[_CandidateRow],
    *,
    stage1_response_schema_version: str = CMEE_STAGE1_RESPONSE_SCHEMA_VERSION,
) -> tuple[PlannedObservationContribution, ...]:
    selected = _selected_contribution_candidates(rows)
    contributions: list[PlannedObservationContribution] = []
    for row in selected:
        candidate = row.candidate
        contribution = PlannedObservationContribution(
            schema_version=stage1_response_schema_version,
            contribution_id="",
            parent_duty_ref=parent_plan.observation_duty_id,
            contribution_kind=_contribution_kind(candidate),
            interpretation_candidate_refs=(candidate.candidate_id,),
            semantic_operator=candidate.semantic_operator,
            argument_bindings=candidate.argument_bindings,
            relation_operator=candidate.relation_operator,
            relation_basis_refs=candidate.relation_basis_refs,
            derivation_rule_id=(
                "cocolon.cmee.v1a.stage1.layer1."
                f"{_contribution_kind(candidate).value.lower()}.v1"
            ),
            semantic_refs=candidate.semantic_refs,
            evidence_refs=candidate.evidence_refs,
            retention="REQUIRED" if row.required else "OPTIONAL",
            semantic_key_version=OBSERVATION_SEMANTIC_KEY_VERSION,
            canonical_semantic_key=_semantic_key(candidate),
            prerequisite_contribution_refs=(),
            forbidden_operations=_FORBIDDEN_OBSERVATION_OPERATIONS,
        )
        identified = _identified(contribution, "contribution_id")
        validate_stage1_identity(identified)
        contributions.append(identified)
    if not contributions:
        raise CMEEStage1ContractError("stage1_observation_contribution_missing")
    return tuple(contributions)


def plan_layer1_observation(
    grounded_graph: GroundedMeaningGraph,
    parent_plan: ExperiencePlan,
    candidates: Sequence[EmlisInterpretationCandidate],
    meaning_field: EmlisMeaningField,
    *,
    source: AdmittedTextSource,
    grounded_plan: GroundedObservationPlan,
    stage1_response_schema_version: str = CMEE_STAGE1_RESPONSE_SCHEMA_VERSION,
) -> tuple[PlannedObservationContribution, ...]:
    """Select exact-cover Layer 1 contributions and suppress optional tail."""

    rows = _candidate_rows(
        grounded_graph,
        parent_plan,
        source=source,
        grounded_plan=grounded_plan,
        stage1_response_schema_version=stage1_response_schema_version,
    )
    expected_candidates = _interpretation_candidates_from_rows(rows)
    if tuple(candidates) != expected_candidates:
        raise CMEEStage1ContractError("stage1_candidate_pool_noncanonical")
    expected_meaning_field = _build_emlis_meaning_field_from_rows(
        grounded_graph,
        parent_plan,
        rows,
        source=source,
        stage1_response_schema_version=stage1_response_schema_version,
    )
    if meaning_field != expected_meaning_field:
        raise CMEEStage1ContractError("stage1_meaning_field_noncanonical")
    return _plan_layer1_observation_from_rows(
        parent_plan,
        rows,
        stage1_response_schema_version=stage1_response_schema_version,
    )


def classify_observation_depth(
    contributions: Sequence[PlannedObservationContribution],
) -> ObservationDepthClass:
    """Classify depth from selected distinct contribution count only."""

    rows = tuple(contributions)
    if any(type(row) is not PlannedObservationContribution for row in rows):
        raise CMEEStage1ContractError("stage1_contribution_type_invalid")
    keys = tuple(row.canonical_semantic_key for row in rows)
    if len(keys) != len(set(keys)):
        raise CMEEStage1ContractError("stage1_duplicate_observation_contribution")
    count = len(rows)
    if count == 1:
        return ObservationDepthClass.FOCUSED
    if 2 <= count <= 3:
        return ObservationDepthClass.LAYERED
    if 4 <= count <= LAYER1_OBSERVATION_CONTRIBUTION_CAP:
        return ObservationDepthClass.DENSE
    raise CMEEStage1ContractError("stage1_observation_depth_unrealizable")


# Compatibility with the terminology used by the Step 2 execution row.
observation_depth_class = classify_observation_depth


def validate_layer1_observation_plan(
    contributions: Sequence[PlannedObservationContribution],
    *,
    candidates: Sequence[EmlisInterpretationCandidate],
    meaning_field: EmlisMeaningField,
    grounded_graph: GroundedMeaningGraph,
    parent_plan: ExperiencePlan,
    source: AdmittedTextSource,
    grounded_plan: GroundedObservationPlan,
    stage1_response_schema_version: str = CMEE_STAGE1_RESPONSE_SCHEMA_VERSION,
) -> None:
    if type(contributions) is not tuple:
        raise CMEEStage1ContractError("stage1_contribution_array_not_tuple")
    candidate_by_id = {row.candidate_id: row for row in candidates}
    for contribution in contributions:
        if len(contribution.interpretation_candidate_refs) != 1:
            raise CMEEStage1ContractError(
                "stage1_observation_semantic_key_mismatch"
            )
        candidate = candidate_by_id.get(
            contribution.interpretation_candidate_refs[0]
        )
        if (
            candidate is None
            or contribution.semantic_key_version
            != OBSERVATION_SEMANTIC_KEY_VERSION
            or contribution.canonical_semantic_key != _semantic_key(candidate)
        ):
            raise CMEEStage1ContractError(
                "stage1_observation_semantic_key_mismatch"
            )
    expected = plan_layer1_observation(
        grounded_graph,
        parent_plan,
        tuple(candidates),
        meaning_field,
        source=source,
        grounded_plan=grounded_plan,
        stage1_response_schema_version=stage1_response_schema_version,
    )
    if tuple(contributions) != expected:
        raise CMEEStage1ContractError("stage1_observation_plan_noncanonical")
    classify_observation_depth(contributions)


def build_layer1_semantics(
    *,
    source: AdmittedTextSource,
    grounded_graph: GroundedMeaningGraph,
    parent_plan: ExperiencePlan,
    grounded_plan: GroundedObservationPlan,
    stage1_response_schema_version: str = CMEE_STAGE1_RESPONSE_SCHEMA_VERSION,
) -> tuple[
    tuple[EmlisInterpretationCandidate, ...],
    EmlisMeaningField,
    tuple[PlannedObservationContribution, ...],
    tuple[str, ...],
    ObservationDepthClass,
]:
    """Build the complete Step 2 Layer 1 semantic tuple.

    The returned tuple is not another plan contract.  Its elements are the
    registered Step 1 children, their exact contribution order, and depth
    derived from that selected contribution count.
    """

    rows = _candidate_rows(
        grounded_graph,
        parent_plan,
        source=source,
        grounded_plan=grounded_plan,
        stage1_response_schema_version=stage1_response_schema_version,
    )
    candidates = _interpretation_candidates_from_rows(rows)
    meaning_field = _build_emlis_meaning_field_from_rows(
        grounded_graph,
        parent_plan,
        rows,
        source=source,
        stage1_response_schema_version=stage1_response_schema_version,
    )
    contributions = _plan_layer1_observation_from_rows(
        parent_plan,
        rows,
        stage1_response_schema_version=stage1_response_schema_version,
    )
    ordered_refs = tuple(row.contribution_id for row in contributions)
    depth = classify_observation_depth(contributions)
    return candidates, meaning_field, contributions, ordered_refs, depth


def _style_policy_ref_for_stance(stance: str) -> str:
    try:
        return _RECEPTION_STANCE_ROWS[stance].distance_policy_ref
    except KeyError:
        raise CMEEStage1ContractError(
            "stage1_reception_stance_unregistered"
        ) from None


def validate_reception_asset_mapping(
    reception_plan: GroundedHumanReceptionPlan,
    *,
    grounded_plan: GroundedObservationPlan,
) -> None:
    """Close the current Reception asset to the registered §17.4 finite set."""

    if type(reception_plan) is not GroundedHumanReceptionPlan:
        raise CMEEStage1ContractError("stage1_reception_asset_type_invalid")
    if type(grounded_plan) is not GroundedObservationPlan:
        raise CMEEStage1ContractError(
            "stage1_grounded_observation_plan_required"
        )
    if (
        len(_RECEPTION_ACT_ROWS) != 7
        or len(_RECEPTION_STANCE_ROWS) != 5
        or len(_RECEPTION_STANCE_BY_ACT) != 7
        or len(_RECEPTION_MOVE_ROLES_BY_ACT) != 7
        or set(_RECEPTION_ACT_ROWS) != set(_RECEPTION_STANCE_BY_ACT)
        or set(_RECEPTION_ACT_ROWS) != set(_RECEPTION_MOVE_ROLES_BY_ACT)
    ):
        raise CMEEStage1ContractError("stage1_reception_mapping_shape_invalid")

    moves = reception_plan.moves
    opportunities = reception_plan.opportunities
    if type(moves) is not tuple or type(opportunities) is not tuple:
        raise CMEEStage1ContractError("stage1_reception_asset_array_not_tuple")
    if not 1 <= len(moves) <= 3:
        raise CMEEStage1ContractError("stage1_reception_move_count_invalid")
    act_ids = _ordered(str(move.reception_act) for move in moves)
    if any(act_id not in _RECEPTION_ACT_ROWS for act_id in act_ids):
        raise CMEEStage1ContractError("stage1_reception_act_unregistered")
    if reception_plan.primary_reception_act != moves[0].reception_act:
        raise CMEEStage1ContractError("stage1_reception_primary_act_mismatch")
    if (
        reception_plan.primary_reception_act not in _RECEPTION_ACT_ROWS
        or (
            reception_plan.secondary_reception_act is not None
            and reception_plan.secondary_reception_act not in _RECEPTION_ACT_ROWS
        )
    ):
        raise CMEEStage1ContractError("stage1_reception_act_unregistered")

    expected_stance = _RECEPTION_STANCE_BY_ACT[moves[0].reception_act]
    if reception_plan.stance != expected_stance:
        raise CMEEStage1ContractError("stage1_reception_stance_mismatch")
    if reception_plan.speaker_presence not in _RECEPTION_SPEAKERS:
        raise CMEEStage1ContractError("stage1_reception_speaker_unregistered")
    if reception_plan.reference_mode not in _RECEPTION_REFERENCE_MODES:
        raise CMEEStage1ContractError("stage1_reception_reference_unregistered")

    for move in moves:
        if move.reception_act not in _RECEPTION_ACT_ROWS:
            raise CMEEStage1ContractError("stage1_reception_act_unregistered")
        if move.move_role not in _RECEPTION_MOVE_ROLES_BY_ACT[move.reception_act]:
            raise CMEEStage1ContractError("stage1_reception_move_role_invalid")
        if move.speaker_presence not in _RECEPTION_SPEAKERS:
            raise CMEEStage1ContractError("stage1_reception_speaker_unregistered")
        if move.reference_mode not in _RECEPTION_REFERENCE_MODES:
            raise CMEEStage1ContractError("stage1_reception_reference_unregistered")
        if move.surface_strategy not in _RECEPTION_SURFACE_STRATEGIES:
            raise CMEEStage1ContractError("stage1_reception_strategy_unregistered")
        if (
            type(move.target_nucleus_ids) is not tuple
            or type(move.support_nucleus_ids) is not tuple
            or type(move.source_evidence_span_ids) is not tuple
            or not move.target_nucleus_ids
            or not move.source_evidence_span_ids
        ):
            raise CMEEStage1ContractError("stage1_reception_move_binding_invalid")

    quote_policy = reception_plan.quote_policy
    expected_anchor_count = int(
        any(move.reference_mode == "short_anchor_if_ambiguous" for move in moves)
    )
    if (
        quote_policy.mode != "no_full_quote_replay"
        or quote_policy.max_anchor_count != expected_anchor_count
        or quote_policy.max_anchor_visible_chars != 16
    ):
        raise CMEEStage1ContractError("stage1_reception_quote_policy_invalid")

    distinctness = reception_plan.distinctness_policy
    if tuple(
        bool(getattr(distinctness, field_name))
        for field_name in CMEE_STAGE1_RECEPTION_DISTINCTNESS_FIELDS
    ) != (False,) * 8:
        raise CMEEStage1ContractError("stage1_reception_distinctness_invalid")
    if (
        type(reception_plan.forbidden_surface_codes) is not tuple
        or reception_plan.forbidden_surface_codes
        != CMEE_STAGE1_RECEPTION_FORBIDDEN_SURFACE_CODES_EXACT6
    ):
        raise CMEEStage1ContractError("stage1_reception_forbidden_surface_invalid")

    bounded = "bounded_counter_self_denial" in set(act_ids)
    safety_kind = grounded_plan.safety_policy.safety_kind
    expected_safety_codes = (
        _RECEPTION_SAFETY_CODES
        if bounded
        else _RECEPTION_SAFETY_CODES[:2]
        if safety_kind == TRIAGE_SELF_DENIAL_SAFE_STATE_ANSWER
        else ()
    )
    if (
        type(reception_plan.safety_modifier_codes) is not tuple
        or reception_plan.safety_modifier_codes != expected_safety_codes
    ):
        raise CMEEStage1ContractError("stage1_reception_safety_mapping_invalid")
    if safety_kind not in {
        TRIAGE_SAFE_OBSERVATION,
        TRIAGE_SELF_DENIAL_SAFE_STATE_ANSWER,
    }:
        raise CMEEStage1ContractError("stage1_reception_safety_owner_invalid")
    if bounded and safety_kind != TRIAGE_SELF_DENIAL_SAFE_STATE_ANSWER:
        raise CMEEStage1ContractError("stage1_reception_safety_mapping_invalid")
    if reception_plan.depth_policy.level not in {"minimal", "focused", "layered"}:
        raise CMEEStage1ContractError("stage1_reception_depth_axis_unregistered")
    if reception_plan.depth_policy.raw_character_count_used is not False:
        raise CMEEStage1ContractError("stage1_reception_depth_raw_input_forbidden")


def _build_request_local_response_state(
    selected_contributions: Sequence[PlannedObservationContribution],
    *,
    relationship_care_constraints: tuple[str, ...],
) -> _RequestLocalResponseState:
    if type(selected_contributions) is not tuple or any(
        type(row) is not PlannedObservationContribution
        for row in selected_contributions
    ):
        raise CMEEStage1ContractError("stage1_self_state_selection_invalid")
    if (
        type(relationship_care_constraints) is not tuple
        or relationship_care_constraints
        not in {(), _RECEPTION_SAFETY_CODES[:2], _RECEPTION_SAFETY_CODES}
    ):
        raise CMEEStage1ContractError("stage1_self_state_constraint_invalid")
    refs = tuple(row.contribution_id for row in selected_contributions)
    if not refs or len(refs) != len(set(refs)):
        raise CMEEStage1ContractError("stage1_self_state_selection_invalid")
    return _RequestLocalResponseState(
        speaker_identity="EMLIS",
        versioned_value_policy=CMEE_STAGE1_VALUE_POLICY_REF,
        selected_observation_contribution_refs=refs,
        relationship_care_constraints=relationship_care_constraints,
    )


def classify_affect_intensity(
    affect_category: AffectCategory,
    target_contributions: Sequence[PlannedObservationContribution],
    *,
    reception_style_policy_ref: str,
    relationship_care_constraints: tuple[str, ...],
) -> AffectIntensity:
    """Classify intensity from four material inputs, never user strength/depth."""

    if type(affect_category) is not AffectCategory:
        raise CMEEStage1ContractError("stage1_affect_category_invalid")
    if type(target_contributions) is not tuple or not target_contributions:
        raise CMEEStage1ContractError("stage1_affect_target_invalid")
    if any(
        type(row) is not PlannedObservationContribution
        for row in target_contributions
    ):
        raise CMEEStage1ContractError("stage1_affect_target_invalid")
    if len({row.contribution_id for row in target_contributions}) != len(
        target_contributions
    ):
        raise CMEEStage1ContractError("stage1_affect_target_invalid")
    registered_styles = {
        row.distance_policy_ref for row in CMEE_STAGE1_RECEPTION_STANCE_MAPPING_EXACT5
    }
    if reception_style_policy_ref not in registered_styles:
        raise CMEEStage1ContractError("stage1_reception_style_policy_ref_invalid")
    if (
        type(relationship_care_constraints) is not tuple
        or relationship_care_constraints
        not in {(), _RECEPTION_SAFETY_CODES[:2], _RECEPTION_SAFETY_CODES}
    ):
        raise CMEEStage1ContractError("stage1_self_state_constraint_invalid")
    moderate_styles = {
        _style_policy_ref_for_stance("warm_recognition"),
        _style_policy_ref_for_stance("gentle_respect"),
    }
    if (
        affect_category
        in {AffectCategory.RELIEF, AffectCategory.JOY, AffectCategory.RESPECT}
        and all(
            row.retention == "REQUIRED" and bool(row.evidence_refs)
            for row in target_contributions
        )
        and reception_style_policy_ref in moderate_styles
        and relationship_care_constraints == ()
    ):
        return AffectIntensity.MODERATE
    return AffectIntensity.QUIET


def classify_subjective_depth(
    claims: Sequence[EmlisSubjectiveClaim],
) -> SubjectiveDepthClass:
    if type(claims) is not tuple or any(
        type(row) is not EmlisSubjectiveClaim for row in claims
    ):
        raise CMEEStage1ContractError("stage1_subjective_plan_type_invalid")
    distinct_count = len({stage1_subjective_semantic_key(row) for row in claims})
    if distinct_count != len(claims):
        raise CMEEStage1ContractError("stage1_duplicate_subjective_claim")
    if distinct_count == 1:
        return SubjectiveDepthClass.FOCUSED
    if 2 <= distinct_count <= 3:
        return SubjectiveDepthClass.LAYERED
    if distinct_count == 4:
        return SubjectiveDepthClass.DENSE
    raise CMEEStage1ContractError("stage1_subjective_depth_unrealizable")


def _temperature_for_reception_asset(
    reception_plan: GroundedHumanReceptionPlan,
    grounded_plan: GroundedObservationPlan,
) -> TemperatureClass:
    stance_row = _RECEPTION_STANCE_ROWS[reception_plan.stance]
    if stance_row.temperature_rule == "STANDARD":
        return TemperatureClass.STANDARD
    if (
        grounded_plan.safety_policy.safety_kind == TRIAGE_SAFE_OBSERVATION
        and reception_plan.safety_modifier_codes == ()
    ):
        return TemperatureClass.ELEVATED_NON_SAFETY
    return TemperatureClass.STANDARD


def _bind_reception_moves(
    reception_plan: GroundedHumanReceptionPlan,
    *,
    binding: _PlanBinding,
    contributions: tuple[PlannedObservationContribution, ...],
) -> tuple[_BoundReceptionMove, ...]:
    bound: list[_BoundReceptionMove] = []
    for move in reception_plan.moves:
        try:
            target_refs = tuple(
                _node_ref(binding.nucleus_to_node[nucleus_id])
                for nucleus_id in move.target_nucleus_ids
            )
            support_refs = tuple(
                _node_ref(binding.nucleus_to_node[nucleus_id])
                for nucleus_id in move.support_nucleus_ids
            )
        except KeyError:
            if move.required:
                raise CMEEStage1ContractError(
                    "stage1_reception_required_target_unbound"
                ) from None
            continue
        target_contributions = tuple(
            row
            for row in contributions
            if set(row.semantic_refs).intersection(target_refs)
        )
        support_contributions = tuple(
            row
            for row in contributions
            if set(row.semantic_refs).intersection(support_refs)
        )
        covered_target_refs = {
            ref for row in target_contributions for ref in row.semantic_refs
        }
        covered_support_refs = {
            ref for row in support_contributions for ref in row.semantic_refs
        }
        if (
            not target_contributions
            or not set(target_refs).issubset(covered_target_refs)
            or not set(support_refs).issubset(covered_support_refs)
        ):
            if move.required:
                raise CMEEStage1ContractError(
                    "stage1_reception_required_target_unbound"
                )
            continue
        selected_ids = {
            row.contribution_id
            for row in (*target_contributions, *support_contributions)
        }
        basis = tuple(
            row for row in contributions if row.contribution_id in selected_ids
        )
        bound.append(
            _BoundReceptionMove(
                move=move,
                basis_contributions=basis,
                target_contributions=target_contributions,
                response_object_refs=target_refs,
            )
        )
    if not bound:
        raise CMEEStage1ContractError("stage1_subjective_plan_empty")
    return tuple(bound)


def _claim_recipe(
    reception_act: str,
    bound_move: _BoundReceptionMove,
) -> tuple[tuple[SubjectiveMode, Optional[AffectCategory], Optional[StanceOperator], tuple[str, ...]], ...]:
    if bound_move.move.move_role not in _RECEPTION_MOVE_ROLES_BY_ACT.get(
        reception_act,
        (),
    ):
        raise CMEEStage1ContractError("stage1_reception_move_role_invalid")
    target_kinds = {
        row.contribution_kind for row in bound_move.target_contributions
    }
    basis_kinds = {
        row.contribution_kind for row in bound_move.basis_contributions
    }
    if reception_act == "stay_with_current_burden":
        category = (
            AffectCategory.SADNESS
            if ObservationContributionKind.PRESERVE_RESIDUE in target_kinds
            else AffectCategory.CONCERN
        )
        return (
            (SubjectiveMode.ATTENTION, None, None, ()),
            (SubjectiveMode.AFFECTIVE_RESPONSE, category, None, ()),
        )
    if reception_act == "honor_concrete_effort":
        return (
            (SubjectiveMode.AFFECTIVE_RESPONSE, AffectCategory.RESPECT, None, ()),
            (SubjectiveMode.PERSONAL_APPRAISAL, None, None, ()),
        )
    if reception_act == "protect_retained_intention":
        recipe = [
            (SubjectiveMode.ATTENTION, None, None, ()),
        ]
        has_direction = any(
            row.semantic_operator is SemanticOperator.PRESENT_DIRECTION
            for row in bound_move.basis_contributions
        )
        has_burden_or_tension = any(
            row.semantic_operator is SemanticOperator.PRESENT_BURDEN
            or row.relation_operator
            in {RelationOperator.COEXISTS_WITH, RelationOperator.TENSION_WITH}
            for row in bound_move.basis_contributions
        )
        if has_direction and has_burden_or_tension:
            recipe.append(
                (SubjectiveMode.VALUE_POSITION, None, None, ("V2", "V8"))
            )
        recipe.append(
            (
                SubjectiveMode.RELATIONAL_STANCE,
                None,
                StanceOperator.PROTECT_USER_AGENCY,
                (),
            )
        )
        return tuple(recipe)
    if reception_act == "recognize_lived_change":
        if ObservationContributionKind.OBSERVE_BURDEN in basis_kinds:
            category = AffectCategory.RELIEF
        elif ObservationContributionKind.OBSERVE_ACTION_THEN_CHANGE in target_kinds:
            category = AffectCategory.RESPECT
        else:
            category = AffectCategory.JOY
        return (
            (SubjectiveMode.AFFECTIVE_RESPONSE, category, None, ()),
            (SubjectiveMode.PERSONAL_APPRAISAL, None, None, ()),
        )
    if reception_act == "hold_help_seeking":
        return (
            (SubjectiveMode.AFFECTIVE_RESPONSE, AffectCategory.CONCERN, None, ()),
            (
                SubjectiveMode.RELATIONAL_STANCE,
                None,
                StanceOperator.STAY_WITH_SPECIFIC_OBJECT,
                (),
            ),
        )
    if reception_act == "bounded_counter_self_denial":
        return (
            (
                SubjectiveMode.BOUNDED_COUNTERPOSITION,
                None,
                StanceOperator.PROTECT_USER_AGENCY,
                ("V1", "V8"),
            ),
            (
                SubjectiveMode.RELATIONAL_STANCE,
                None,
                StanceOperator.PROTECT_USER_AGENCY,
                (),
            ),
        )
    if reception_act == "respect_words_placed":
        return (
            (SubjectiveMode.ATTENTION, None, None, ()),
            (SubjectiveMode.AFFECTIVE_RESPONSE, AffectCategory.RESPECT, None, ()),
        )
    raise CMEEStage1ContractError("stage1_reception_act_unregistered")


def _subjective_operator(mode: SubjectiveMode) -> SubjectiveOperator:
    return {
        SubjectiveMode.ATTENTION: SubjectiveOperator.ATTEND_TO,
        SubjectiveMode.AFFECTIVE_RESPONSE: SubjectiveOperator.FEEL_TOWARD,
        SubjectiveMode.PERSONAL_APPRAISAL: SubjectiveOperator.APPRAISE_AS_MATERIAL,
        SubjectiveMode.VALUE_POSITION: SubjectiveOperator.PROTECT_VALUE_BOUNDARY,
        SubjectiveMode.RELATIONAL_STANCE: SubjectiveOperator.TAKE_RELATIONAL_STANCE,
        SubjectiveMode.BOUNDED_COUNTERPOSITION: SubjectiveOperator.COUNTER_SPECIFIC_PROMOTION,
    }[mode]


def _build_subjective_claim(
    bound_move: _BoundReceptionMove,
    *,
    parent_plan: ExperiencePlan,
    mode: SubjectiveMode,
    affect_category: Optional[AffectCategory],
    stance_operator: Optional[StanceOperator],
    value_codes: tuple[str, ...],
    response_state: _RequestLocalResponseState,
    reception_style_policy_ref: str,
    material_unknown_refs: tuple[str, ...],
    stage1_response_schema_version: str,
) -> EmlisSubjectiveClaim:
    target_refs = tuple(
        row.contribution_id for row in bound_move.target_contributions
    )
    basis_refs = tuple(
        row.contribution_id for row in bound_move.basis_contributions
    )
    basis_semantic_refs = _ordered(
        ref
        for row in bound_move.basis_contributions
        for ref in (*row.semantic_refs, *row.relation_basis_refs)
    )
    intensity = None
    if affect_category is not None:
        intensity = classify_affect_intensity(
            affect_category,
            bound_move.target_contributions,
            reception_style_policy_ref=reception_style_policy_ref,
            relationship_care_constraints=(
                response_state.relationship_care_constraints
            ),
        )
    counterposition_ref = (
        bound_move.response_object_refs[0]
        if mode is SubjectiveMode.BOUNDED_COUNTERPOSITION
        else None
    )
    modality = (
        "feeling"
        if mode is SubjectiveMode.AFFECTIVE_RESPONSE
        else "refusal"
        if mode is SubjectiveMode.BOUNDED_COUNTERPOSITION
        else "intention"
        if mode in {SubjectiveMode.RELATIONAL_STANCE, SubjectiveMode.VALUE_POSITION}
        else "fact"
    )
    proposition = SubjectiveProposition(
        subjective_operator=_subjective_operator(mode),
        target_contribution_refs=target_refs,
        response_object_refs=bound_move.response_object_refs,
        affect_category=affect_category,
        affect_intensity=intensity,
        stance_operator=stance_operator,
        counterposition_target_ref=counterposition_ref,
        referenced_actor_refs=(),
        referenced_experiencer_refs=(),
        addressee_role="NONE",
        polarity="neutral",
        modality=modality,
    )
    claim = EmlisSubjectiveClaim(
        schema_version=stage1_response_schema_version,
        subjective_claim_id="",
        parent_duty_ref=parent_plan.reception_duty_id,
        speaker_owner=response_state.speaker_identity,
        claim_domain=EmlisTraceClaimDomain.SUBJECTIVE_RESPONSE.value,
        subjective_mode=mode,
        asserted_subjective_proposition=proposition,
        basis_observation_contribution_refs=basis_refs,
        basis_semantic_refs=basis_semantic_refs,
        source_reception_act_refs=(str(bound_move.move.reception_act),),
        value_principle_refs=tuple(
            stage1_value_principle_ref(code) for code in value_codes
        ),
        user_fact_effect=0,
        forbidden_promotions=stage1_subjective_forbidden_promotions(
            bound_move.basis_contributions,
            material_unknown_refs=material_unknown_refs,
        ),
    )
    return _identified(claim, "subjective_claim_id")


def _semantic_reception_asset(
    *,
    source: AdmittedTextSource,
    grounded_plan: GroundedObservationPlan,
) -> GroundedHumanReceptionPlan:
    resolver = build_evidence_span_resolver(
        source.evidence_spans,
        current_input=source.normalized_current_input,
    )
    try:
        from .emlis_v1a import _cmee_semantic_reception_plan

        plan = _cmee_semantic_reception_plan(grounded_plan, resolver)
    except CMEEStage1ContractError:
        raise
    except Exception:
        raise CMEEStage1ContractError(
            "stage1_reception_asset_noncanonical"
        ) from None
    validate_reception_asset_mapping(plan, grounded_plan=grounded_plan)
    return plan


def plan_layer2_subjectivity(
    *,
    source: AdmittedTextSource,
    grounded_graph: GroundedMeaningGraph,
    parent_plan: ExperiencePlan,
    grounded_plan: GroundedObservationPlan,
    observation_contributions: tuple[PlannedObservationContribution, ...],
    stage1_response_schema_version: str = (
        CMEE_STAGE1_RESPONSE_SCHEMA_VERSION_V1
    ),
) -> tuple[EmlisSubjectiveClaim, ...]:
    """Transform the current Reception asset into request-local Layer 2 claims."""

    _validate_canonical_semantic_inputs(
        source,
        grounded_plan,
        grounded_graph,
        parent_plan,
    )
    if type(observation_contributions) is not tuple or not observation_contributions:
        raise CMEEStage1ContractError("stage1_subjective_basis_missing")
    if any(
        type(row) is not PlannedObservationContribution
        for row in observation_contributions
    ):
        raise CMEEStage1ContractError("stage1_subjective_basis_invalid")
    reception_plan = _semantic_reception_asset(
        source=source,
        grounded_plan=grounded_plan,
    )
    retained_acts = _ordered(
        str(move.reception_act) for move in reception_plan.moves
    )
    if retained_acts != parent_plan.allowed_reception_act_ids:
        raise CMEEStage1ContractError("stage1_reception_parent_act_mismatch")
    binding = _bind_grounded_plan(source, grounded_graph, grounded_plan)
    bound_moves = _bind_reception_moves(
        reception_plan,
        binding=binding,
        contributions=observation_contributions,
    )
    selected_ids = {
        row.contribution_id
        for bound_move in bound_moves
        for row in bound_move.basis_contributions
    }
    selected_contributions = tuple(
        row
        for row in observation_contributions
        if row.contribution_id in selected_ids
    )
    response_state = _build_request_local_response_state(
        selected_contributions,
        relationship_care_constraints=reception_plan.safety_modifier_codes,
    )
    style_ref = _style_policy_ref_for_stance(str(reception_plan.stance))
    material_unknown_refs = _material_unknown_refs(
        grounded_graph,
        parent_plan,
        source,
    )

    candidate_specs: list[
        tuple[
            _BoundReceptionMove,
            SubjectiveMode,
            Optional[AffectCategory],
            Optional[StanceOperator],
            tuple[str, ...],
        ]
    ] = []
    recipes = tuple(
        (bound_move, _claim_recipe(str(bound_move.move.reception_act), bound_move))
        for bound_move in bound_moves
    )
    for bound_move, recipe in recipes:
        mode, category, stance, values = recipe[0]
        candidate_specs.append((bound_move, mode, category, stance, values))
    for bound_move, recipe in recipes:
        for mode, category, stance, values in recipe[1:]:
            if len(candidate_specs) >= 4:
                break
            candidate_specs.append((bound_move, mode, category, stance, values))
        if len(candidate_specs) >= 4:
            break

    claims: list[EmlisSubjectiveClaim] = []
    semantic_keys: set[str] = set()
    for bound_move, mode, category, stance, values in candidate_specs:
        claim = _build_subjective_claim(
            bound_move,
            parent_plan=parent_plan,
            mode=mode,
            affect_category=category,
            stance_operator=stance,
            value_codes=values,
            response_state=response_state,
            reception_style_policy_ref=style_ref,
            material_unknown_refs=material_unknown_refs,
            stage1_response_schema_version=(
                stage1_response_schema_version
            ),
        )
        semantic_key = stage1_subjective_semantic_key(claim)
        if semantic_key in semantic_keys:
            continue
        semantic_keys.add(semantic_key)
        claims.append(claim)
    result = tuple(claims)
    covered_acts = {
        claim.source_reception_act_refs[0] for claim in result
    }
    if covered_acts != set(retained_acts) or not 2 <= len(result) <= 4:
        raise CMEEStage1ContractError("stage1_subjective_plan_unrealizable")
    classify_subjective_depth(result)
    return result


def validate_layer2_subjective_plan(
    claims: tuple[EmlisSubjectiveClaim, ...],
    *,
    source: AdmittedTextSource,
    grounded_graph: GroundedMeaningGraph,
    parent_plan: ExperiencePlan,
    grounded_plan: GroundedObservationPlan,
    observation_contributions: tuple[PlannedObservationContribution, ...],
    stage1_response_schema_version: str = (
        CMEE_STAGE1_RESPONSE_SCHEMA_VERSION_V1
    ),
) -> None:
    if type(claims) is not tuple:
        raise CMEEStage1ContractError("stage1_subjective_plan_type_invalid")
    expected = plan_layer2_subjectivity(
        source=source,
        grounded_graph=grounded_graph,
        parent_plan=parent_plan,
        grounded_plan=grounded_plan,
        observation_contributions=observation_contributions,
        stage1_response_schema_version=stage1_response_schema_version,
    )
    if claims != expected:
        raise CMEEStage1ContractError("stage1_subjective_plan_noncanonical")


def _final_stage1_semantic_maps(
    *,
    source: AdmittedTextSource,
    grounded_graph: GroundedMeaningGraph,
    grounded_plan: GroundedObservationPlan,
    candidate_rows: tuple[EmlisInterpretationCandidate, ...],
    meaning_candidate_refs: Sequence[str],
) -> tuple[tuple[Any, ...], tuple[Any, ...], tuple[Any, ...]]:
    """Freeze the final Phase-A D-frame, R-to-D, and qualifier closures."""

    from . import emlis_stage1_composition as composition

    binding = _bind_grounded_plan(source, grounded_graph, grounded_plan)
    direct_rows = tuple(
        row
        for row in candidate_rows
        if not row.relation_basis_refs
    )
    meaning_candidate_set = set(meaning_candidate_refs)
    if not meaning_candidate_set.issubset(
        {row.candidate_id for row in candidate_rows}
    ):
        raise CMEEStage1ContractError(
            "stage1_final_meaning_candidate_ref_invalid"
        )
    direct_by_semantic_ref: dict[
        str, list[EmlisInterpretationCandidate]
    ] = {}
    frame_rows: list[Any] = []
    for candidate in direct_rows:
        primary = tuple(
            row
            for row in candidate.argument_bindings
            if row.role is ArgumentRole.PRIMARY
        )
        if len(primary) != 1:
            raise CMEEStage1ContractError(
                "stage1_final_direct_candidate_primary_invalid"
            )
        semantic_ref = primary[0].semantic_ref
        matching_node_ids = tuple(
            node_id
            for node_id in binding.node_meta
            if _node_ref(node_id) == semantic_ref
        )
        if len(matching_node_ids) != 1:
            raise CMEEStage1ContractError(
                "stage1_final_grounded_frame_unresolved"
            )
        nucleus = binding.node_meta[matching_node_ids[0]]
        frame = getattr(nucleus, "semantic_frame", None)
        if type(frame) is not GroundedSemanticFrame:
            raise CMEEStage1ContractError(
                "stage1_final_grounded_frame_unresolved"
            )
        direct_by_semantic_ref.setdefault(semantic_ref, []).append(candidate)
        frame_rows.append(
            composition.CandidateFrameRow(candidate.candidate_id, frame)
        )

    endpoint_rows: list[Any] = []
    for candidate in candidate_rows:
        if not candidate.relation_basis_refs:
            continue
        for argument in candidate.argument_bindings:
            direct_candidates = tuple(
                direct_by_semantic_ref.get(argument.semantic_ref, ())
            )
            role_prefix = f"{argument.role.value.lower()}_qualifier:"
            required_source_contract = tuple(
                f"qualifier:{value[len(role_prefix):]}"
                for value in candidate.required_qualifiers
                if value.startswith(role_prefix)
                and value[len(role_prefix):]
            )
            compatible_meaning = tuple(
                row
                for row in direct_candidates
                if row.candidate_id in meaning_candidate_set
                if set(required_source_contract).issubset(
                    {
                        value
                        for value in row.required_qualifiers
                        if value.startswith("qualifier:")
                    }
                )
            )
            compatible_support = tuple(
                row
                for row in direct_candidates
                if row.candidate_id not in meaning_candidate_set
                if set(required_source_contract).issubset(
                    {
                        value
                        for value in row.required_qualifiers
                        if value.startswith("qualifier:")
                    }
                )
            )
            compatible = compatible_meaning or compatible_support
            if len(compatible) != 1:
                raise CMEEStage1ContractError(
                    "stage1_final_relation_endpoint_unresolved"
                )
            endpoint = compatible[0]
            endpoint_rows.append(
                composition.RelationEndpointCandidateRow(
                    candidate.candidate_id,
                    argument.role,
                    argument.semantic_ref,
                    endpoint.candidate_id,
                )
            )

    qualifier_rows: list[Any] = []
    for candidate in candidate_rows:
        relation = stage1_candidate_uses_relation_qualifier_scope(candidate)
        arguments: tuple[Optional[ArgumentBinding], ...] = (
            tuple(candidate.argument_bindings) if relation else (None,)
        )
        for argument in arguments:
            role = argument.role if argument is not None else None
            semantic_ref = (
                argument.semantic_ref if argument is not None else None
            )
            for axis in composition.ClauseScalarAxis:
                qualifier_rows.append(
                    composition.QualifierValueRow(
                        candidate.candidate_id,
                        (
                            composition.QualifierLookupScope.RELATION_SOURCE_BINDING
                            if relation
                            else composition.QualifierLookupScope.DIRECT_UNQUALIFIED
                        ),
                        role,
                        semantic_ref,
                        axis,
                        resolve_qualifier_value(
                            candidate,
                            axis.value.lower(),
                            role=role,
                        ),
                    )
                )
    return tuple(frame_rows), tuple(endpoint_rows), tuple(qualifier_rows)


def _final_stage1_candidate_closure(
    *,
    source: AdmittedTextSource,
    grounded_graph: GroundedMeaningGraph,
    grounded_plan: GroundedObservationPlan,
    candidate_rows: tuple[EmlisInterpretationCandidate, ...],
    required_candidate_refs: Sequence[str],
    stage1_response_schema_version: str = CMEE_STAGE1_RESPONSE_SCHEMA_VERSION,
) -> tuple[EmlisInterpretationCandidate, ...]:
    """Add a separate exact support closure for required relation endpoints."""

    binding = _bind_grounded_plan(
        source,
        grounded_graph,
        grounded_plan,
    )
    candidate_ids = tuple(row.candidate_id for row in candidate_rows)
    required_candidate_set = set(required_candidate_refs)
    if (
        not required_candidate_set
        or not required_candidate_set.issubset(set(candidate_ids))
    ):
        raise CMEEStage1ContractError(
            "stage1_final_required_candidate_ref_invalid"
        )
    rows = list(candidate_rows)
    direct_semantic_refs = {
        argument.semantic_ref
        for candidate in rows
        if not candidate.relation_basis_refs
        for argument in candidate.argument_bindings
        if argument.role is ArgumentRole.PRIMARY
    }
    required_relation_candidates = tuple(
        candidate
        for candidate in candidate_rows
        if candidate.candidate_id in required_candidate_set
        and candidate.relation_basis_refs
    )
    required_endpoint_direct_rows: list[EmlisInterpretationCandidate] = []
    for relation_candidate in required_relation_candidates:
        for argument in relation_candidate.argument_bindings:
            matching_nodes = tuple(
                node
                for node in grounded_graph.nodes
                if _node_ref(node.node_id) == argument.semantic_ref
            )
            if len(matching_nodes) != 1:
                raise CMEEStage1ContractError(
                    "stage1_final_relation_endpoint_unresolved"
                )
            node = matching_nodes[0]
            nucleus = binding.node_meta.get(node.node_id)
            if nucleus is None:
                raise CMEEStage1ContractError(
                    "stage1_final_relation_endpoint_unresolved"
                )
            direct = _candidate_from_direct(
                grounded_graph,
                node,
                nucleus,
                include_relation_endpoint_source_contract=True,
                stage1_response_schema_version=(
                    stage1_response_schema_version
                ),
            )
            if direct.candidate_id not in {
                row.candidate_id for row in required_endpoint_direct_rows
            }:
                required_endpoint_direct_rows.append(direct)
            direct_semantic_refs.add(argument.semantic_ref)
    initial_candidate_ids = set(candidate_ids)
    expected_support_rows = tuple(
        direct
        for direct in required_endpoint_direct_rows
        if direct.candidate_id not in initial_candidate_ids
    )
    for direct in required_endpoint_direct_rows:
        existing = tuple(
            row for row in rows if row.candidate_id == direct.candidate_id
        )
        if len(existing) > 1 or (existing and existing[0] != direct):
            raise CMEEStage1ContractError(
                "stage1_final_candidate_identity_duplicate"
            )
        if not existing:
            rows.append(direct)
    if any(
        argument.semantic_ref not in direct_semantic_refs
        for candidate in candidate_rows
        if candidate.relation_operator
        is not RelationOperator.NO_RELATION_CLAIM
        for argument in candidate.argument_bindings
    ):
        raise CMEEStage1ContractError(
            "stage1_final_relation_endpoint_unresolved"
        )
    support_semantic_refs = tuple(
        candidate.semantic_refs[0]
        for candidate in rows[len(candidate_rows) :]
    )
    validate_stage1_candidate_partition_bounds(
        tuple(row.candidate_kind for row in candidate_rows),
        tuple(
            row.candidate_id in required_candidate_set
            for row in candidate_rows
        ),
        support_semantic_refs=support_semantic_refs,
        expected_support_semantic_refs=tuple(
            row.semantic_refs[0] for row in expected_support_rows
        ),
    )
    return tuple(rows)


def build_premeaning_grounded_inputs(
    *,
    source: AdmittedTextSource,
    grounded_graph: GroundedMeaningGraph,
    parent_plan: ExperiencePlan,
    grounded_plan: GroundedObservationPlan,
) -> PreMeaningGroundedInputs:
    """Build the sole Reception-free semantic closure used by IM01."""

    canonical_grounded_plan, canonical_parent_plan = (
        _validate_canonical_semantic_inputs(
            source,
            grounded_plan,
            grounded_graph,
            parent_plan,
            delivery_blind_parent=True,
        )
    )
    if FINAL_STAGE1_GROUNDED_PROJECTION_VERSION not in tuple(
        getattr(canonical_grounded_plan, "source_contracts", ())
    ):
        raise CMEEStage1ContractError(
            "stage1_final_grounded_observation_plan_required"
        )
    (
        candidates,
        meaning_field,
        contributions,
        ordered_observation_refs,
        observation_depth,
    ) = build_layer1_semantics(
        source=source,
        grounded_graph=grounded_graph,
        parent_plan=canonical_parent_plan,
        grounded_plan=canonical_grounded_plan,
        stage1_response_schema_version=CMEE_STAGE1_RESPONSE_SCHEMA_VERSION_V2,
    )
    premeaning_inputs = PreMeaningGroundedInputs(
        schema_version="1.0",
        stage1_response_schema_version=CMEE_STAGE1_RESPONSE_SCHEMA_VERSION_V2,
        grounded_graph=grounded_graph,
        grounded_graph_ref=_graph_ref(grounded_graph),
        parent_observation_duty_ref=(
            canonical_parent_plan.observation_duty_id
        ),
        interpretation_candidate_rows=candidates,
        meaning_field=meaning_field,
        observation_contribution_rows=contributions,
        ordered_observation_refs=ordered_observation_refs,
        material_unknown_refs=meaning_field.material_unknown_refs,
        observation_depth_class=observation_depth,
        source_qualifier_rows=project_premeaning_source_qualifier_rows(
            source=source,
            grounded_plan=canonical_grounded_plan,
            grounded_graph=grounded_graph,
            parent_plan=canonical_parent_plan,
            stage1_response_schema_version=(
                CMEE_STAGE1_RESPONSE_SCHEMA_VERSION_V2
            ),
        ),
        source_relation_rows=project_premeaning_source_relation_rows(
            source=source,
            grounded_plan=canonical_grounded_plan,
            grounded_graph=grounded_graph,
            parent_plan=canonical_parent_plan,
            stage1_response_schema_version=(
                CMEE_STAGE1_RESPONSE_SCHEMA_VERSION_V2
            ),
        ),
    )
    validate_premeaning_grounded_inputs(
        premeaning_inputs,
        source=source,
        grounded_plan=grounded_plan,
        grounded_graph=grounded_graph,
        parent_plan=parent_plan,
    )
    return premeaning_inputs


def build_allowed_reception_opportunity_envelope(
    *,
    source: AdmittedTextSource,
    grounded_graph: GroundedMeaningGraph,
    parent_plan: ExperiencePlan,
    grounded_plan: GroundedObservationPlan,
) -> AllowedReceptionOpportunityEnvelope:
    """Project only parent-allowed acts and grounded safety boundaries."""

    _validate_canonical_semantic_inputs(
        source,
        grounded_plan,
        grounded_graph,
        parent_plan,
    )
    retained_act_ids = tuple(parent_plan.allowed_reception_act_ids)
    safety_boundary_codes = tuple(
        grounded_plan.safety_policy.required_boundary_codes
    )
    envelope = AllowedReceptionOpportunityEnvelope(
        schema_version="1.0",
        source_envelope_id=source.envelope.envelope_id,
        parent_reception_duty_ref=parent_plan.reception_duty_id,
        allowed_reception_act_ids=retained_act_ids,
        safety_boundary_codes=safety_boundary_codes,
    )
    validate_allowed_reception_opportunity_envelope(
        envelope,
        source=source,
        grounded_graph=grounded_graph,
        parent_plan=parent_plan,
        grounded_plan=grounded_plan,
    )
    return envelope


def validate_allowed_reception_opportunity_envelope(
    envelope: AllowedReceptionOpportunityEnvelope,
    *,
    source: AdmittedTextSource,
    grounded_graph: GroundedMeaningGraph,
    parent_plan: ExperiencePlan,
    grounded_plan: GroundedObservationPlan,
) -> None:
    """Bind the opportunity-only envelope to its upstream owners."""

    _validate_canonical_semantic_inputs(
        source,
        grounded_plan,
        grounded_graph,
        parent_plan,
    )
    if (
        type(envelope) is not AllowedReceptionOpportunityEnvelope
        or envelope.schema_version != "1.0"
        or type(envelope.allowed_reception_act_ids) is not tuple
        or type(envelope.safety_boundary_codes) is not tuple
        or not envelope.allowed_reception_act_ids
        or len(envelope.allowed_reception_act_ids)
        != len(set(envelope.allowed_reception_act_ids))
        or len(envelope.safety_boundary_codes)
        != len(set(envelope.safety_boundary_codes))
        or any(
            type(value) is not str or not value
            for value in (
                *envelope.allowed_reception_act_ids,
                *envelope.safety_boundary_codes,
            )
        )
        or envelope.source_envelope_id != source.envelope.envelope_id
        or envelope.parent_reception_duty_ref
        != parent_plan.reception_duty_id
    ):
        raise CMEEStage1ContractError(
            "stage1_allowed_reception_envelope_invalid"
        )
    expected_act_ids = tuple(parent_plan.allowed_reception_act_ids)
    expected_safety_boundary_codes = tuple(
        grounded_plan.safety_policy.required_boundary_codes
    )
    if (
        envelope.allowed_reception_act_ids != expected_act_ids
        or envelope.safety_boundary_codes
        != expected_safety_boundary_codes
    ):
        raise CMEEStage1ContractError(
            "stage1_allowed_reception_envelope_noncanonical"
        )


_NORMAL_RECEPTION_ROLE_BY_MODE = {
    SubjectiveMode.ATTENTION: (
        SubjectiveResponsibilityKind.MATERIAL_APPRAISAL,
        SubjectiveAssertionModality.EMLIS_APPRAISAL,
    ),
    SubjectiveMode.PERSONAL_APPRAISAL: (
        SubjectiveResponsibilityKind.MATERIAL_APPRAISAL,
        SubjectiveAssertionModality.EMLIS_APPRAISAL,
    ),
    SubjectiveMode.VALUE_POSITION: (
        SubjectiveResponsibilityKind.POLICY_VISIBLE_VALUE,
        SubjectiveAssertionModality.EMLIS_VALUE_POSITION,
    ),
    SubjectiveMode.RELATIONAL_STANCE: (
        SubjectiveResponsibilityKind.RELATIONAL_POSITION,
        SubjectiveAssertionModality.EMLIS_RELATIONAL_INTENTION,
    ),
}


def _normal_reception_profiles(
    reception_act: str,
    contributions: Sequence[PlannedObservationContribution],
) -> tuple[
    tuple[
        SubjectiveMode,
        SubjectiveResponsibilityKind,
        SubjectiveAssertionModality,
    ],
    ...,
]:
    mapping_rows = tuple(
        row
        for row in CMEE_STAGE1_RECEPTION_ACT_MAPPING_EXACT7
        if row.reception_act == reception_act
    )
    if len(mapping_rows) != 1:
        raise CMEEStage1ContractError(
            "MEANING_RECEPTION_CAPABILITY_GAP"
        )
    profiles: list[
        tuple[
            SubjectiveMode,
            SubjectiveResponsibilityKind,
            SubjectiveAssertionModality,
        ]
    ] = []
    seen_responsibilities: set[SubjectiveResponsibilityKind] = set()
    for mode, _operator in mapping_rows[0].eligible_mode_operator_pairs:
        role = _NORMAL_RECEPTION_ROLE_BY_MODE.get(mode)
        if (
            role is None
            or role[0] in seen_responsibilities
            or not _im04_normal_reception_mode_contract_satisfied(
                reception_act,
                mode,
                contributions,
            )
        ):
            continue
        seen_responsibilities.add(role[0])
        profiles.append((mode, *role))
    return tuple(profiles)


def _assign_normal_reception_profiles(
    retained_rows: tuple[Any, ...],
    *,
    response_object_refs: tuple[str, ...],
    contribution_by_ref: Mapping[str, PlannedObservationContribution],
) -> tuple[
    tuple[
        SubjectiveMode,
        SubjectiveResponsibilityKind,
        SubjectiveAssertionModality,
    ],
    ...,
]:
    """Choose one complementary typed role per retained material act."""

    if len(retained_rows) > 4:
        raise CMEEStage1ContractError(
            "RECEPTION_BINDING_CONFLICT_STOP"
        )
    options = tuple(
        _normal_reception_profiles(
            row.reception_act,
            tuple(
                contribution_by_ref[ref]
                for ref in row.basis_contribution_refs
            ),
        )
        for row in retained_rows
    )
    act_response_object_refs = tuple(
        _ordered(
            response_object_ref
            for contribution_ref in row.basis_contribution_refs
            for response_object_ref in (
                *contribution_by_ref[contribution_ref].semantic_refs,
                *contribution_by_ref[
                    contribution_ref
                ].relation_basis_refs,
            )
        )
        for row in retained_rows
    )
    if any(
        not refs or not set(refs).issubset(response_object_refs)
        for refs in act_response_object_refs
    ):
        raise CMEEStage1ContractError(
            "RECEPTION_BINDING_CONFLICT_STOP"
        )

    def resolve(
        index: int,
        selected: tuple[
            tuple[
                SubjectiveMode,
                SubjectiveResponsibilityKind,
                SubjectiveAssertionModality,
            ],
            ...,
        ],
        occupied: frozenset[
            tuple[
                SubjectiveResponsibilityKind,
                tuple[str, ...],
            ]
        ],
    ) -> Optional[
        tuple[
            tuple[
                SubjectiveMode,
                SubjectiveResponsibilityKind,
                SubjectiveAssertionModality,
            ],
            ...,
        ]
    ]:
        if index == len(options):
            return selected
        retained_row = retained_rows[index]
        for profile in options[index]:
            conflict_key = _im04_normal_reception_binding_key(
                responsibility_kind=profile[1],
                response_object_refs=act_response_object_refs[index],
            )
            if conflict_key in occupied:
                continue
            result = resolve(
                index + 1,
                (*selected, profile),
                occupied | {conflict_key},
            )
            if result is not None:
                return result
        return None

    resolved = resolve(0, (), frozenset())
    if resolved is None:
        raise CMEEStage1ContractError(
            "RECEPTION_BINDING_CONFLICT_STOP"
        )
    return resolved


def build_stage1_post_selection_reception_records(
    *,
    input_specific_meaning_structure: InputSpecificMeaningStructure,
    projection_preimage_ref: str,
    retained_reception_act_rows: Sequence[Any],
    observation_contribution_rows: Sequence[PlannedObservationContribution],
    interpretation_candidate_rows: Sequence[EmlisInterpretationCandidate],
    contribution_to_candidate_ref_map: Sequence[tuple[str, str]],
    qualifier_value_rows: Sequence[Any],
    material_unknown_refs: Sequence[str],
    expected_act_refs: Sequence[str],
) -> tuple[
    Tuple[Any, ...],
    Tuple[Any, ...],
    Tuple[Any, ...],
    Tuple[Any, ...],
    Tuple[Any, ...],
    Tuple[Any, ...],
    str,
]:
    """Construct IM04 records exactly once after the IM03 outcome is sealed."""

    structure = input_specific_meaning_structure
    if type(structure) is not InputSpecificMeaningStructure:
        raise CMEEStage1ContractError(
            "stage1_post_selection_structure_type_invalid"
        )
    retained_rows = tuple(retained_reception_act_rows)
    contributions = tuple(observation_contribution_rows)
    interpretation_candidates = tuple(interpretation_candidate_rows)
    contribution_candidate_map = tuple(
        contribution_to_candidate_ref_map
    )
    qualifiers = tuple(qualifier_value_rows)
    material_unknowns = tuple(material_unknown_refs)
    expected_acts = tuple(expected_act_refs)
    allowed_acts = tuple(row.reception_act for row in retained_rows)
    contribution_refs = tuple(row.contribution_id for row in contributions)
    interpretation_candidate_refs = tuple(
        row.candidate_id for row in interpretation_candidates
    )
    if (
        not projection_preimage_ref
        or not retained_rows
        or not contributions
        or not interpretation_candidates
        or not qualifiers
        or any(
            type(row) is not EmlisInterpretationCandidate
            for row in interpretation_candidates
        )
        or type(contribution_candidate_map) is not tuple
        or any(
            type(row) is not tuple
            or len(row) != 2
            or any(type(value) is not str or not value for value in row)
            for row in contribution_candidate_map
        )
        or type(material_unknowns) is not tuple
        or type(expected_act_refs) is not tuple
        or not expected_acts
        or len(expected_acts) != len(set(expected_acts))
        or any(
            type(value) is not str or not value
            for value in expected_acts
        )
        or allowed_acts != expected_acts
        or any(type(value) is not str or not value for value in material_unknowns)
        or len(allowed_acts) != len(set(allowed_acts))
        or len(contribution_refs) != len(set(contribution_refs))
        or len(interpretation_candidate_refs)
        != len(set(interpretation_candidate_refs))
        or len(contribution_candidate_map)
        != len(set(contribution_candidate_map))
        or len(material_unknowns) != len(set(material_unknowns))
    ):
        raise CMEEStage1ContractError(
            "stage1_post_selection_authority_invalid"
        )
    outcome = structure.meaning_decision_outcome
    if type(outcome) is SelectedEmlisProvisionalReading:
        candidate_rows = tuple(
            row
            for row in structure.candidate_records
            if row.candidate_id == outcome.selected_candidate_ref
        )
        if len(candidate_rows) != 1:
            raise CMEEStage1ContractError(
                "stage1_post_selection_selected_candidate_missing"
            )
        candidate = candidate_rows[0]
        consequence = derive_reading_consequence(structure)
        sealed_reading = derive_sealed_emlis_provisional_reading(
            structure, consequence
        )
        response_object_refs = tuple(
            dict.fromkeys(
                (
                    outcome.primary_reading_focus_ref,
                    *outcome.supporting_facet_refs,
                    *outcome.reading_component_refs,
                    *outcome.reading_relation_refs,
                    *outcome.qualified_event_state_refs,
                )
            )
        )
        candidate_basis_refs = set(candidate.basis_contribution_refs)
        contribution_by_ref = {
            row.contribution_id: row for row in contributions
        }
        selected_response_object_refs = set(response_object_refs)
        bound_rows = tuple(
            sorted(
                (
                    row
                    for row in retained_rows
                    if row.reception_act != "bounded_counter_self_denial"
                    and bool(row.basis_contribution_refs)
                    and bool(
                        set(row.basis_contribution_refs).intersection(
                            candidate_basis_refs
                        )
                    )
                    and all(
                        ref in contribution_by_ref
                        for ref in row.basis_contribution_refs
                    )
                    and {
                        semantic_ref
                        for ref in row.basis_contribution_refs
                        for semantic_ref in contribution_by_ref[ref].semantic_refs
                    }.issubset(selected_response_object_refs)
                ),
                key=lambda row: (
                    row.reception_act,
                    row.act_ref,
                    row.basis_contribution_refs,
                ),
            )
        )
        if not bound_rows:
            raise CMEEStage1ContractError(
                "MEANING_RECEPTION_CAPABILITY_GAP"
            )
        profiles = _assign_normal_reception_profiles(
            bound_rows,
            response_object_refs=response_object_refs,
            contribution_by_ref=contribution_by_ref,
        )
        proposition_records: list[MeaningBoundReceptionProposition] = []
        for row, (
            subjective_mode,
            responsibility_kind,
            assertion_modality,
        ) in zip(bound_rows, profiles, strict=True):
            act_response_object_refs = _ordered(
                response_object_ref
                for contribution_ref in row.basis_contribution_refs
                for response_object_ref in (
                    *contribution_by_ref[
                        contribution_ref
                    ].semantic_refs,
                    *contribution_by_ref[
                        contribution_ref
                    ].relation_basis_refs,
                )
            )
            proposition = MeaningBoundReceptionProposition(
                schema_version="1.1",
                reception_id="",
                selected_reading_ref=outcome.reading_id,
                reception_function=row.reception_act,
                responsibility_kind=responsibility_kind,
                subjective_mode=subjective_mode,
                contribution_kind=(
                    "AFFIRMATIVE_RECEPTION_CONTRIBUTION"
                ),
                response_object_refs=act_response_object_refs,
                preserved_difference_refs=(
                    candidate.preserved_difference_refs
                ),
                optional_affect=None,
                optional_stance=None,
                reading_status="EMLIS_PROVISIONAL_READING",
                subjective_assertion_modality=assertion_modality,
            )
            proposition_records.append(
                replace(
                    proposition,
                    reception_id=meaning_bound_reception_id(proposition),
                )
            )
        propositions = tuple(proposition_records)
        proposition_refs = tuple(row.reception_id for row in propositions)
        count = len(propositions)
        depth = (
            SubjectiveDepthClass.FOCUSED
            if count == 1
            else SubjectiveDepthClass.LAYERED
            if count <= 3
            else SubjectiveDepthClass.DENSE
        )
        reception_set = MeaningBoundReceptionSet(
            schema_version="1.1",
            selected_reading_ref=outcome.reading_id,
            reading_consequence_ref=sealed_reading.reading_consequence_ref,
            subjective_depth=depth,
            proposition_refs=proposition_refs,
            affirmative_contribution_refs=proposition_refs,
            optional_counterposition_refs=(),
        )
        consequence_records: Tuple[Any, ...] = (consequence,)
        sealed_records: Tuple[Any, ...] = (sealed_reading,)
        proposition_tuple: Tuple[Any, ...] = propositions
        reception_set_records: Tuple[Any, ...] = (reception_set,)
        bounded_records: Tuple[Any, ...] = ()
        bounded_proposition_records: Tuple[Any, ...] = ()
    elif type(outcome) is LimitedMeaningOutcome:
        if (
            not outcome.retained_layer1_refs
            or not outcome.foreground_source_object_refs
            or not set(outcome.retained_layer1_refs).issubset(
                contribution_refs
            )
        ):
            raise CMEEStage1ContractError(
                "LIMITED_RECEPTION_CAPABILITY_GAP_STOP"
            )
        canonical_retained_refs = canonical_limited_retained_layer1_refs(
            outcome.retained_layer1_refs,
            contributions,
        )
        (
            limited_mode,
            limited_operator,
            _licensed_act_refs,
            licensed_contribution_refs,
            aggregate_attention,
        ) = resolve_limited_reception_aggregate(
            retained_rows,
            expected_act_refs=expected_acts,
            retained_layer1_refs=canonical_retained_refs,
            observation_contribution_rows=contributions,
        )
        try:
            resolved_basis_rows, resolved_qualifier_rows = (
                resolve_limited_subjective_binding_rows(
                    projection_preimage_ref=projection_preimage_ref,
                    limited_outcome=outcome,
                    observation_contribution_rows=contributions,
                    interpretation_candidate_rows=interpretation_candidates,
                    contribution_to_candidate_ref_map=(
                        contribution_candidate_map
                    ),
                    qualifier_value_rows=qualifiers,
                    licensed_contribution_refs=(
                        licensed_contribution_refs
                    ),
                )
            )
        except CMEEStage1ContractError as exc:
            raise CMEEStage1ContractError(
                "LIMITED_RECEPTION_CAPABILITY_GAP_STOP"
            ) from exc
        licensed_contribution_set = set(licensed_contribution_refs)
        limited_basis_rows = tuple(
            row
            for row in resolved_basis_rows
            if row.contribution_ref in licensed_contribution_set
        )
        limited_basis_ref_set = {
            row.binding_ref for row in limited_basis_rows
        }
        limited_qualifier_rows = tuple(
            row
            for row in resolved_qualifier_rows
            if row.basis_binding_ref in limited_basis_ref_set
        )
        basis_binding_refs = tuple(
            row.binding_ref for row in limited_basis_rows
        )
        qualifier_binding_refs = tuple(
            row.source_qualifier_binding_ref
            for row in limited_qualifier_rows
        )
        bound_contribution_refs = tuple(
            dict.fromkeys(
                row.contribution_ref for row in limited_basis_rows
            )
        )
        bound_semantic_refs = tuple(
            dict.fromkeys(row.semantic_ref for row in limited_basis_rows)
        )
        expected_bound_contribution_refs = tuple(
            ref
            for ref in canonical_retained_refs
            if ref in licensed_contribution_set
        )
        if (
            not basis_binding_refs
            or bound_contribution_refs != expected_bound_contribution_refs
            or not bound_semantic_refs
            or not set(bound_semantic_refs).issubset(
                outcome.foreground_source_object_refs
            )
            or len(qualifier_binding_refs) != len(basis_binding_refs)
        ):
            raise CMEEStage1ContractError(
                "LIMITED_RECEPTION_CAPABILITY_GAP_STOP"
            )

        content_kind: SubjectiveContentKind
        appraisal_content: Optional[EmlisAppraisalContent] = None
        relational_position: Optional[EmlisRelationalPosition] = None
        assertion_modality: SubjectiveAssertionModality
        if limited_mode in {
            SubjectiveMode.ATTENTION,
            SubjectiveMode.PERSONAL_APPRAISAL,
        }:
            content_kind = SubjectiveContentKind.APPRAISAL
            appraisal_content = _im04_limited_appraisal_content(
                basis_binding_refs=basis_binding_refs,
                contribution_rows=contributions,
                candidate_rows=interpretation_candidates,
                contribution_candidate_map=contribution_candidate_map,
                contribution_refs=bound_contribution_refs,
                semantic_refs=bound_semantic_refs,
                aggregate_attention=aggregate_attention,
            )
            if appraisal_content is None:
                raise CMEEStage1ContractError(
                    "LIMITED_RECEPTION_CAPABILITY_GAP_STOP"
                )
            assertion_modality = (
                SubjectiveAssertionModality.EMLIS_APPRAISAL
            )
        elif limited_mode is SubjectiveMode.RELATIONAL_STANCE:
            content_kind = SubjectiveContentKind.RELATIONAL_POSITION
            relational_position = EmlisRelationalPosition(
                RelationalPositionKind.STANCE,
                StanceOperator.STAY_WITH_SPECIFIC_OBJECT,
                basis_binding_refs,
                (),
                RelationalCommitment.STAY_WITH,
                RelationalClosure.NONE,
            )
            assertion_modality = (
                SubjectiveAssertionModality.EMLIS_RELATIONAL_INTENTION
            )
        else:
            raise CMEEStage1ContractError(
                "LIMITED_RECEPTION_CAPABILITY_GAP_STOP"
            )
        subjective_proposition = SubjectivePropositionV2(
            schema_version=(
                CMEE_STAGE1_MEANING_BOUND_SUBJECTIVE_PROJECTION_SCHEMA_VERSION
                if limited_mode is SubjectiveMode.ATTENTION
                else dict(CMEE_STAGE1_FINAL_LOGICAL_ID_REGISTRY)[
                    "CMEE_STAGE1_SUBJECTIVE_PROPOSITION_SCHEMA_VERSION"
                ]
            ),
            content_kind=content_kind,
            subjective_mode=limited_mode,
            subjective_operator=limited_operator,
            target_contribution_refs=bound_contribution_refs,
            primary_target_refs=bound_semantic_refs,
            boundary_target_refs=(),
            response_object_refs=bound_semantic_refs,
            basis_binding_refs=basis_binding_refs,
            source_qualifier_binding_refs=qualifier_binding_refs,
            focal_relation_ref=(
                appraisal_content.focal_relation_ref
                if appraisal_content is not None
                else None
            ),
            affect_content=None,
            appraisal_content=appraisal_content,
            material_value_content=None,
            relational_position=relational_position,
            referenced_actor_refs=(),
            referenced_experiencer_refs=(),
            addressee_role="USER",
            assertion_modality=assertion_modality,
            epistemic_scope="REQUEST_LOCAL_EMLIS_SUBJECTIVITY",
        )
        bounded = BoundedLimitedReception(
            schema_version="1.1",
            limited_outcome_ref=limited_meaning_outcome_id(outcome),
            # Aggregate reception owns a canonical union; the legacy exact-one
            # branch keeps the sealed IM03 order byte-for-byte.
            bound_layer1_contribution_refs=(
                canonical_retained_refs
                if aggregate_attention
                else outcome.retained_layer1_refs
            ),
            foreground_source_object_refs=(
                outcome.foreground_source_object_refs
            ),
            retained_qualifier_refs=outcome.retained_qualifier_refs,
            subjective_depth=SubjectiveDepthClass.FOCUSED,
            proposition_ref=subjective_proposition_v2_id(
                subjective_proposition
            ),
            contribution_kind="AFFIRMATIVE_RECEPTION_CONTRIBUTION",
        )
        bounded_limited_reception_id(
            bounded,
            limited_outcome=outcome,
            subjective_proposition=subjective_proposition,
        )
        consequence_records = ()
        sealed_records = ()
        proposition_tuple = ()
        reception_set_records = ()
        bounded_records = (bounded,)
        bounded_proposition_records = (subjective_proposition,)
    else:
        raise CMEEStage1ContractError(
            "stage1_post_selection_outcome_type_invalid"
        )
    projection_seal_ref = project_stage1_subjective_projection_seal_ref(
        projection_preimage_ref,
        meaning_decision_outcome=outcome,
        reading_consequence_records=consequence_records,
        sealed_emlis_provisional_reading_records=sealed_records,
        meaning_bound_reception_proposition_records=proposition_tuple,
        meaning_bound_reception_set_records=reception_set_records,
        bounded_limited_reception_records=bounded_records,
        bounded_limited_subjective_proposition_records=(
            bounded_proposition_records
        ),
        whole_reading_consequence_rows=structure.whole_reading_consequence_rows,
    )
    validate_stage1_post_selection_reception_records(
        input_specific_meaning_structure=structure,
        projection_preimage_ref=projection_preimage_ref,
        reading_consequence_records=consequence_records,
        sealed_emlis_provisional_reading_records=sealed_records,
        meaning_bound_reception_proposition_records=proposition_tuple,
        meaning_bound_reception_set_records=reception_set_records,
        bounded_limited_reception_records=bounded_records,
        bounded_limited_subjective_proposition_records=(
            bounded_proposition_records
        ),
        projection_seal_ref=projection_seal_ref,
        retained_reception_act_rows=retained_rows,
        observation_contribution_rows=contributions,
        interpretation_candidate_rows=interpretation_candidates,
        contribution_to_candidate_ref_map=contribution_candidate_map,
        qualifier_value_rows=qualifiers,
        material_unknown_refs=material_unknowns,
        expected_act_refs=expected_acts,
    )
    return (
        consequence_records,
        sealed_records,
        proposition_tuple,
        reception_set_records,
        bounded_records,
        bounded_proposition_records,
        projection_seal_ref,
    )


def build_subjective_planning_inputs(
    *,
    source: AdmittedTextSource,
    grounded_graph: GroundedMeaningGraph,
    parent_plan: ExperiencePlan,
    grounded_plan: GroundedObservationPlan,
) -> "Stage1SubjectivePlanningInputs":
    """Build the sole disabled final-composition Phase-A input closure."""

    from . import emlis_stage1_composition as composition

    premeaning_inputs = build_premeaning_grounded_inputs(
        source=source,
        grounded_graph=grounded_graph,
        parent_plan=parent_plan,
        grounded_plan=grounded_plan,
    )
    grounded_situation_view = derive_grounded_situation_view(
        premeaning_inputs
    )
    foreground_scope_derivation = derive_foreground_scope_closed(
        grounded_situation_view
    )
    validate_foreground_scope_derivation(
        foreground_scope_derivation,
        basis_rows=grounded_situation_view.basis_rows,
        premeaning_inputs=premeaning_inputs,
        source=source,
        grounded_plan=grounded_plan,
        grounded_graph=grounded_graph,
        parent_plan=parent_plan,
    )
    scope_disposition = foreground_scope_disposition(
        foreground_scope_derivation
    )
    if (
        scope_disposition.code
        is ForegroundScopeDispositionCode.STRUCTURE_INSUFFICIENT_STOP
    ):
        raise CMEEStage1ContractError(
            ForegroundScopeDispositionCode.STRUCTURE_INSUFFICIENT_STOP.value
        )

    # IM03 remains on the pre-Reception side of the type boundary.  Its
    # complete source-grounded structure is frozen before the allowed
    # opportunity envelope, concrete acts, style, or temperature are read.
    input_specific_meaning_structure: InputSpecificMeaningStructure = (
        derive_input_specific_meaning_structure(
            grounded_situation_view,
            foreground_scope_derivation,
        )
    )
    validate_input_specific_meaning_structure(
        input_specific_meaning_structure,
        grounded_view=grounded_situation_view,
        foreground_scope_derivation=foreground_scope_derivation,
    )

    candidates = _final_stage1_candidate_closure(
        source=source,
        grounded_graph=grounded_graph,
        grounded_plan=grounded_plan,
        candidate_rows=premeaning_inputs.interpretation_candidate_rows,
        required_candidate_refs=(
            premeaning_inputs.meaning_field.required_candidate_refs
        ),
        stage1_response_schema_version=(
            premeaning_inputs.stage1_response_schema_version
        ),
    )
    meaning_field = premeaning_inputs.meaning_field
    contributions = premeaning_inputs.observation_contribution_rows
    observation_depth = premeaning_inputs.observation_depth_class

    # Only the upstream opportunity envelope exists at the meaning boundary.
    # The concrete legacy Reception plan is bound after scope disposition.
    allowed_reception_envelope = (
        build_allowed_reception_opportunity_envelope(
            source=source,
            grounded_graph=grounded_graph,
            parent_plan=parent_plan,
            grounded_plan=grounded_plan,
        )
    )
    retained_act_ids = allowed_reception_envelope.allowed_reception_act_ids
    reception_plan = _semantic_reception_asset(
        source=source,
        grounded_plan=grounded_plan,
    )
    validate_reception_asset_mapping(
        reception_plan,
        grounded_plan=grounded_plan,
    )
    if _ordered(
        str(move.reception_act) for move in reception_plan.moves
    ) != retained_act_ids:
        raise CMEEStage1ContractError("stage1_reception_parent_act_mismatch")
    plan_binding = _bind_grounded_plan(
        source,
        grounded_graph,
        grounded_plan,
    )
    bound_moves = _bind_reception_moves(
        reception_plan,
        binding=plan_binding,
        contributions=premeaning_inputs.observation_contribution_rows,
    )
    retained_rows: list[Any] = []
    for act_ref in retained_act_ids:
        basis_refs = _ordered(
            row.contribution_id
            for bound_move in bound_moves
            if str(bound_move.move.reception_act) == act_ref
            for row in bound_move.basis_contributions
        )
        if not basis_refs:
            raise CMEEStage1ContractError(
                "stage1_final_reception_act_basis_missing"
            )
        retained_rows.append(
            composition.RetainedReceptionActRow(
                act_ref,
                act_ref,
                basis_refs,
            )
        )

    contribution_map = tuple(
        (
            contribution.contribution_id,
            resolve_candidate_for_contribution(
                candidates,
                contribution,
            ).candidate_id,
        )
        for contribution in contributions
    )
    frame_rows, endpoint_rows, qualifier_rows = _final_stage1_semantic_maps(
        source=source,
        grounded_graph=grounded_graph,
        grounded_plan=grounded_plan,
        candidate_rows=candidates,
        meaning_candidate_refs=tuple(
            ref
            for entry in meaning_field.entries
            for ref in entry.interpretation_candidate_refs
        ),
    )
    style_ref = _style_policy_ref_for_stance(str(reception_plan.stance))
    temperature = _temperature_for_reception_asset(
        reception_plan,
        grounded_plan,
    )
    projection_preimage_ref = project_stage1_projection_preimage_ref(
        grounded_graph_ref=_graph_ref(grounded_graph),
        parent_observation_duty_ref=parent_plan.observation_duty_id,
        parent_reception_duty_ref=parent_plan.reception_duty_id,
        interpretation_candidate_ids=tuple(
            row.candidate_id for row in candidates
        ),
        meaning_field_id=meaning_field.meaning_field_id,
        observation_contribution_ids=tuple(
            row.contribution_id for row in contributions
        ),
        retained_reception_act_ids=retained_act_ids,
        observation_depth_class=observation_depth,
        temperature_class=temperature,
        reception_style_policy_ref=style_ref,
        emlis_value_policy_ref=CMEE_STAGE1_VALUE_POLICY_REF,
    )
    (
        reading_consequence_records,
        sealed_emlis_provisional_reading_records,
        meaning_bound_reception_proposition_records,
        meaning_bound_reception_set_records,
        bounded_limited_reception_records,
        bounded_limited_subjective_proposition_records,
        projection_seal_ref,
    ) = build_stage1_post_selection_reception_records(
        input_specific_meaning_structure=input_specific_meaning_structure,
        projection_preimage_ref=projection_preimage_ref,
        retained_reception_act_rows=tuple(retained_rows),
        observation_contribution_rows=contributions,
        interpretation_candidate_rows=candidates,
        contribution_to_candidate_ref_map=contribution_map,
        qualifier_value_rows=qualifier_rows,
        material_unknown_refs=meaning_field.material_unknown_refs,
        expected_act_refs=(
            allowed_reception_envelope.allowed_reception_act_ids
        ),
    )
    return composition.Stage1SubjectivePlanningInputs(
        admitted_source=source,
        grounded_graph=grounded_graph,
        grounded_plan=grounded_plan,
        parent_plan=parent_plan,
        premeaning_inputs=premeaning_inputs,
        grounded_situation_view=grounded_situation_view,
        foreground_scope_derivation=foreground_scope_derivation,
        foreground_scope_disposition=scope_disposition,
        input_specific_meaning_structure=(
            input_specific_meaning_structure
        ),
        allowed_reception_opportunity_envelope=(
            allowed_reception_envelope
        ),
        projection_preimage_ref=projection_preimage_ref,
        reading_consequence_records=reading_consequence_records,
        sealed_emlis_provisional_reading_records=(
            sealed_emlis_provisional_reading_records
        ),
        meaning_bound_reception_proposition_records=(
            meaning_bound_reception_proposition_records
        ),
        meaning_bound_reception_set_records=(
            meaning_bound_reception_set_records
        ),
        bounded_limited_reception_records=(
            bounded_limited_reception_records
        ),
        bounded_limited_subjective_proposition_records=(
            bounded_limited_subjective_proposition_records
        ),
        projection_seal_ref=projection_seal_ref,
        interpretation_candidate_rows=candidates,
        meaning_field=meaning_field,
        observation_contribution_rows=contributions,
        retained_reception_act_rows=tuple(retained_rows),
        material_unknown_refs=meaning_field.material_unknown_refs,
        observation_depth_class=observation_depth,
        temperature_class=temperature,
        reception_style_policy_ref=style_ref,
        emlis_value_policy_ref=CMEE_STAGE1_VALUE_POLICY_REF,
        contribution_to_candidate_ref_map=contribution_map,
        resolved_grounded_frame_by_candidate_ref=frame_rows,
        relation_endpoint_grounded_candidate_ref_by_binding_key=endpoint_rows,
        qualifier_value_by_candidate_scope_axis_key=qualifier_rows,
        construction_registry_snapshot=composition.CONSTRUCTION_REGISTRY,
        expression_asset_registry_snapshot=composition.EXPRESSION_ASSET_REGISTRY,
        response_object_registry_snapshot=composition.RESPONSE_OBJECT_ASSET_REGISTRY,
        functional_asset_registry_snapshot=composition.FUNCTIONAL_ASSET_REGISTRY,
        participant_asset_registry_snapshot=composition.PARTICIPANT_ASSET_REGISTRY,
        structural_asset_registry_snapshot=composition.STRUCTURAL_ASSET_REGISTRY,
        profile_rule_registry_snapshot=composition.PROFILE_RULE_REGISTRY,
    )


def _final_subjective_depth(claim_count: int) -> SubjectiveDepthClass:
    if claim_count == 1:
        return SubjectiveDepthClass.FOCUSED
    if 2 <= claim_count <= 3:
        return SubjectiveDepthClass.LAYERED
    if claim_count == 4:
        return SubjectiveDepthClass.DENSE
    raise CMEEStage1ContractError("stage1_subjective_depth_unrealizable")


def _stage1_projected_claim_rows(value: object) -> tuple[object, ...]:
    """Read the one claim tuple shared by the plan and final projection."""

    rows = getattr(value, "subjective_claim_rows", None)
    if rows is None:
        rows = getattr(value, "subjective_claims", None)
    if type(rows) is not tuple or not 1 <= len(rows) <= 4:
        raise CMEEStage1ContractError(
            "stage1_final_meaning_plan_noncanonical"
        )
    return rows


def _stage1_projected_content(
    proposition: SubjectivePropositionV2,
) -> object:
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
    if content is None:
        raise CMEEStage1ContractError(
            "stage1_final_meaning_plan_noncanonical"
        )
    return content


def _validate_meaning_plan_vertical_binding(
    phase_A: "Stage1SubjectivePlanningInputs",
    meaning_plan: object,
) -> None:
    """Bind every projected claim to its exact sealed Phase-A source."""

    from . import emlis_stage1_composition as composition

    is_unsealed_plan = hasattr(meaning_plan, "subjective_claim_rows")
    claims = _stage1_projected_claim_rows(meaning_plan)
    claim_by_ref = {
        getattr(row, "subjective_claim_id", ""): row for row in claims
    }
    responsibilities = getattr(
        meaning_plan,
        "subjective_responsibility_rows",
        None,
    )
    opportunities = getattr(
        meaning_plan,
        "subjective_opportunity_rows",
        None,
    )
    basis_rows = getattr(
        meaning_plan,
        "subjective_basis_binding_rows",
        None,
    )
    qualifier_rows = getattr(
        meaning_plan,
        "source_qualifier_binding_rows",
        None,
    )
    policy_basis_rows = getattr(
        meaning_plan,
        "policy_basis_binding_rows",
        None,
    )
    policy_application_rows = getattr(
        meaning_plan,
        "policy_application_rows",
        None,
    )
    if (
        len(claim_by_ref) != len(claims)
        or "" in claim_by_ref
        or any(
            type(rows) is not tuple
            for rows in (
                responsibilities,
                opportunities,
                basis_rows,
                qualifier_rows,
                policy_basis_rows,
                policy_application_rows,
            )
        )
    ):
        raise CMEEStage1ContractError(
            "stage1_final_meaning_plan_noncanonical"
        )
    responsibility_by_ref = {
        row.responsibility_ref: row for row in responsibilities
    }
    opportunity_by_key = {
        row.opportunity_key: row for row in opportunities
    }
    if (
        len(responsibility_by_ref) != len(responsibilities)
        or len(opportunity_by_key) != len(opportunities)
    ):
        raise CMEEStage1ContractError(
            "stage1_final_meaning_plan_noncanonical"
        )

    try:
        expected_basis, expected_qualifiers, expected_policy_basis = (
            composition._projection_binding_rows(
                composition._projection_common_authority(phase_A)
            )
        )
    except composition.Stage1CompositionError:
        raise CMEEStage1ContractError(
            "stage1_final_meaning_plan_noncanonical"
        ) from None
    canonical_basis = tuple(
        sorted(expected_basis, key=lambda row: row.binding_ref)
    )
    canonical_qualifiers = tuple(
        sorted(
            expected_qualifiers,
            key=lambda row: row.source_qualifier_binding_ref,
        )
    )
    canonical_policy_basis = tuple(
        sorted(expected_policy_basis, key=lambda row: row.binding_ref)
    )
    if (
        basis_rows != canonical_basis
        or qualifier_rows != canonical_qualifiers
        or policy_basis_rows != canonical_policy_basis
    ):
        raise CMEEStage1ContractError(
            "stage1_final_meaning_plan_noncanonical"
        )

    contribution_by_ref = {
        row.contribution_id: row
        for row in phase_A.observation_contribution_rows
    }
    reception_rows = meaning_plan.reception_visible_causal_trace_rows
    if (
        type(reception_rows) is not tuple
        or tuple(
            dict.fromkeys(
                row.projected_claim_ref for row in reception_rows
            )
        )
        != tuple(claim_by_ref)
    ):
        raise CMEEStage1ContractError(
            "stage1_final_meaning_plan_noncanonical"
        )

    expected_policy_applications: list[object] = []

    def require_claim_spine(
        *,
        claim: object,
        proposition: SubjectivePropositionV2,
        responsibility_kind: SubjectiveResponsibilityKind,
        contribution_refs: tuple[str, ...],
        semantic_refs: tuple[str, ...],
        act_refs: tuple[str, ...],
        value_refs: tuple[str, ...],
        specificity: SubjectiveSpecificity,
        content: object,
    ) -> None:
        responsibility_ref = (
            composition.project_stage1_subjective_responsibility_ref(
                projection_preimage_ref=phase_A.projection_preimage_ref,
                responsibility_kind=responsibility_kind,
                owner_component_refs=contribution_refs,
                retained_reception_act_refs=act_refs,
            )
        )
        responsibility = responsibility_by_ref.get(responsibility_ref)
        opportunity_key = composition.project_stage1_subjective_opportunity_key(
            projection_preimage_ref=phase_A.projection_preimage_ref,
            responsibility_refs=(responsibility_ref,),
            content_kind=proposition.content_kind,
            row_ref_free_discriminated_content=content,
            specificity_key=specificity,
        )
        opportunity = opportunity_by_key.get(opportunity_key)
        contributions = tuple(
            contribution_by_ref[ref] for ref in contribution_refs
        )
        forbidden = stage1_subjective_forbidden_promotions(
            contributions,
            material_unknown_refs=phase_A.material_unknown_refs,
        )
        expected_claim_id = composition._projected_claim_identity(
            proposition=proposition,
            parent_duty_ref=phase_A.parent_plan.reception_duty_id,
            responsibility_refs=(responsibility_ref,),
            opportunity_key=opportunity_key,
            contribution_refs=contribution_refs,
            semantic_refs=semantic_refs,
            act_refs=act_refs,
            value_principle_refs=value_refs,
            forbidden_promotions=forbidden,
        )
        if (
            responsibility is None
            or responsibility.responsibility_kind
            is not responsibility_kind
            or responsibility.owner_component_refs != contribution_refs
            or responsibility.retained_reception_act_refs != act_refs
            or opportunity is None
            or opportunity.responsibility_refs != (responsibility_ref,)
            or opportunity.content_kind is not proposition.content_kind
            or opportunity.content != content
            or opportunity.specificity_key is not specificity
            or getattr(claim, "subjective_claim_id", None)
            != expected_claim_id
            or getattr(claim, "parent_duty_ref", None)
            != phase_A.parent_plan.reception_duty_id
            or getattr(claim, "speaker_owner", None)
            != (
                composition.CMEE_STAGE1_EMLIS_OWNER_REF
                if is_unsealed_plan
                else "EMLIS"
            )
            or getattr(claim, "claim_domain", None)
            != "EMLIS_SUBJECTIVE_RESPONSE"
            or getattr(claim, "subjective_responsibility_refs", None)
            != (responsibility_ref,)
            or getattr(
                claim,
                "selected_subjective_opportunity_key",
                None,
            )
            != opportunity_key
            or getattr(
                claim,
                "basis_observation_contribution_refs",
                None,
            )
            != contribution_refs
            or getattr(claim, "basis_semantic_refs", None) != semantic_refs
            or getattr(claim, "source_reception_act_refs", None) != act_refs
            or getattr(claim, "value_principle_refs", None) != value_refs
            or getattr(claim, "user_fact_effect", None) != 0
            or type(getattr(claim, "user_fact_effect", None)) is not int
            or getattr(claim, "forbidden_promotions", None) != forbidden
            or getattr(claim, "asserted_subjective_proposition", None)
            is not proposition
            or getattr(claim, "subjective_mode", proposition.subjective_mode)
            is not proposition.subjective_mode
        ):
            raise CMEEStage1ContractError(
                "stage1_final_meaning_plan_noncanonical"
            )

    outcome = (
        phase_A.input_specific_meaning_structure.meaning_decision_outcome
    )
    if type(outcome) is SelectedEmlisProvisionalReading:
        sources = phase_A.meaning_bound_reception_proposition_records
        selected_candidates = tuple(
            row
            for row in (
                phase_A.input_specific_meaning_structure.candidate_records
            )
            if row.candidate_id == outcome.selected_candidate_ref
        )
        if (
            len(sources) != len(reception_rows)
            or not 1 <= len(claims) <= len(sources)
            or len(selected_candidates) != 1
        ):
            raise CMEEStage1ContractError(
                "stage1_final_meaning_plan_noncanonical"
            )
        selected_candidate = selected_candidates[0]
        expected_local_claims: list[object] = []
        expected_local_responsibilities: list[object] = []
        expected_local_opportunities: list[object] = []
        expected_local_traces: list[object] = []
        for trace, source in zip(reception_rows, sources, strict=True):
            claim = claim_by_ref.get(trace.projected_claim_ref)
            retained = tuple(
                row
                for row in phase_A.retained_reception_act_rows
                if row.reception_act == source.reception_function
            )
            if claim is None or len(retained) != 1:
                raise CMEEStage1ContractError(
                    "stage1_final_meaning_plan_noncanonical"
                )
            projection_contribution_ref_set = set(
                retained[0].basis_contribution_refs
            )
            contribution_refs = tuple(
                row.contribution_id
                for row in phase_A.observation_contribution_rows
                if row.contribution_id in projection_contribution_ref_set
            )
            if (
                trace.layer1_contribution_refs != contribution_refs
                or any(
                    ref not in contribution_by_ref for ref in contribution_refs
                )
            ):
                raise CMEEStage1ContractError(
                    "stage1_final_meaning_plan_noncanonical"
                )
            contributions = tuple(
                contribution_by_ref[ref] for ref in contribution_refs
            )
            own_basis = tuple(
                row
                for row in expected_basis
                if row.contribution_ref in set(contribution_refs)
            )
            own_basis_refs = tuple(row.binding_ref for row in own_basis)
            own_basis_ref_set = set(own_basis_refs)
            own_qualifiers = tuple(
                row
                for row in expected_qualifiers
                if row.basis_binding_ref in own_basis_ref_set
            )
            own_semantic_refs = composition._unique(
                row.semantic_ref for row in own_basis
            )
            operator = composition._normal_reception_operator(source)
            value_refs: tuple[str, ...] = ()
            if source.subjective_mode in {
                SubjectiveMode.ATTENTION,
                SubjectiveMode.PERSONAL_APPRAISAL,
            }:
                content_kind = SubjectiveContentKind.APPRAISAL
                content = composition._normal_reception_appraisal(
                    proposition=source,
                    contributions=contributions,
                    basis_rows=own_basis,
                    semantic_contributions=tuple(
                        contribution_by_ref[ref]
                        for ref in selected_candidate.basis_contribution_refs
                        if ref in set(contribution_refs)
                    ),
                )
                focal_relation_ref = content.focal_relation_ref
                content_fields = (None, content, None, None)
            elif source.subjective_mode is SubjectiveMode.AFFECTIVE_RESPONSE:
                content_kind = SubjectiveContentKind.AFFECT
                content = source.optional_affect
                focal_relation_ref = None
                content_fields = (content, None, None, None)
            elif source.subjective_mode is SubjectiveMode.RELATIONAL_STANCE:
                content_kind = SubjectiveContentKind.RELATIONAL_POSITION
                content = composition._normal_reception_position(
                    proposition=source,
                    basis_rows=own_basis,
                )
                focal_relation_ref = None
                content_fields = (None, None, None, content)
            elif source.subjective_mode is SubjectiveMode.VALUE_POSITION:
                content_kind = SubjectiveContentKind.MATERIAL_VALUE
                value_refs = composition._stage1_material_visible_value_refs(
                    reception_act=source.reception_function,
                    contributions=contributions,
                )
                relevant_policy_refs = tuple(
                    row.binding_ref
                    for row in expected_policy_basis
                    if row.owner_kind
                    is composition.PolicyBasisOwnerKind.CONTRIBUTION
                    and row.owner_ref in set(contribution_refs)
                )
                applications = []
                for principle_ref in value_refs:
                    application_ref = composition._ref(
                        "policy-application",
                        (
                            phase_A.projection_seal_ref,
                            source.reception_id,
                            principle_ref,
                            relevant_policy_refs,
                            own_basis_refs,
                        ),
                    )
                    risk = composition._RISK_BY_PRINCIPLE[principle_ref]
                    applications.append(
                        composition.ValueApplication(
                            principle_ref,
                            risk,
                            (application_ref,),
                            relevant_policy_refs,
                            own_basis_refs,
                        )
                    )
                    expected_policy_applications.append(
                        PolicyApplicationRow(
                            application_ref,
                            "VISIBILITY",
                            principle_ref,
                            risk,
                            relevant_policy_refs,
                            trace.projected_claim_ref,
                            trace.projected_claim_ref,
                        )
                    )
                content = composition.MaterialValueContent(
                    tuple(applications),
                    own_basis_refs,
                    (),
                )
                focal_relation_ref = None
                content_fields = (None, None, content, None)
            else:
                raise CMEEStage1ContractError(
                    "stage1_final_meaning_plan_noncanonical"
                )
            expected_proposition = SubjectivePropositionV2(
                composition.CMEE_STAGE1_MEANING_BOUND_SUBJECTIVE_PROJECTION_SCHEMA_VERSION,
                content_kind,
                source.subjective_mode,
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
                *content_fields,
                (),
                (),
                "USER",
                source.subjective_assertion_modality,
                "REQUEST_LOCAL_EMLIS_SUBJECTIVITY",
            )
            if (
                trace.reception_record_ref
                != meaning_bound_reception_id(source)
                or trace.projected_response_object_refs
                != own_semantic_refs
            ):
                raise CMEEStage1ContractError(
                    "stage1_final_meaning_plan_noncanonical"
                )
            act_refs = (retained[0].act_ref,)
            specificity = (
                SubjectiveSpecificity.RELATION_BOUND_MULTI_ROLE
                if focal_relation_ref is not None
                else SubjectiveSpecificity.MULTI_ROLE
                if len(own_semantic_refs) > 1
                else SubjectiveSpecificity.SINGLE_ROLE
            )
            responsibility_ref = (
                composition.project_stage1_subjective_responsibility_ref(
                    projection_preimage_ref=phase_A.projection_preimage_ref,
                    responsibility_kind=source.responsibility_kind,
                    owner_component_refs=contribution_refs,
                    retained_reception_act_refs=act_refs,
                )
            )
            opportunity_key = (
                composition.project_stage1_subjective_opportunity_key(
                    projection_preimage_ref=phase_A.projection_preimage_ref,
                    responsibility_refs=(responsibility_ref,),
                    content_kind=content_kind,
                    row_ref_free_discriminated_content=content,
                    specificity_key=specificity,
                )
            )
            contributions = tuple(
                contribution_by_ref[ref] for ref in contribution_refs
            )
            forbidden = stage1_subjective_forbidden_promotions(
                contributions,
                material_unknown_refs=phase_A.material_unknown_refs,
            )
            local_claim_id = composition._projected_claim_identity(
                proposition=expected_proposition,
                parent_duty_ref=phase_A.parent_plan.reception_duty_id,
                responsibility_refs=(responsibility_ref,),
                opportunity_key=opportunity_key,
                contribution_refs=contribution_refs,
                semantic_refs=own_semantic_refs,
                act_refs=act_refs,
                value_principle_refs=value_refs,
                forbidden_promotions=forbidden,
            )
            expected_local_responsibilities.append(
                composition.SubjectiveResponsibilityRow(
                    responsibility_ref,
                    source.responsibility_kind,
                    contribution_refs,
                    act_refs,
                )
            )
            expected_local_opportunities.append(
                composition.SubjectiveOpportunityRow(
                    opportunity_key,
                    (responsibility_ref,),
                    content_kind,
                    content,
                    specificity,
                )
            )
            expected_local_claims.append(
                composition.ProjectedSubjectiveClaim(
                    composition.CMEE_STAGE1_RESPONSE_SCHEMA_VERSION,
                    local_claim_id,
                    phase_A.parent_plan.reception_duty_id,
                    composition.CMEE_STAGE1_EMLIS_OWNER_REF,
                    "EMLIS_SUBJECTIVE_RESPONSE",
                    (responsibility_ref,),
                    opportunity_key,
                    expected_proposition,
                    contribution_refs,
                    own_semantic_refs,
                    act_refs,
                    value_refs,
                    0,
                    forbidden,
                )
            )
            expected_local_traces.append(
                replace(trace, projected_claim_ref=local_claim_id)
            )
        (
            expected_claims,
            expected_opportunities,
            expected_traces,
        ) = composition._coalesce_normal_subjective_facets(
            authority=composition._projection_common_authority(phase_A),
            claims=expected_local_claims,
            responsibilities=expected_local_responsibilities,
            opportunities=expected_local_opportunities,
            basis_rows=expected_basis,
            qualifier_rows=expected_qualifiers,
            reception_traces=expected_local_traces,
            policy_applications=expected_policy_applications,
        )
        canonical_expected_responsibilities = tuple(
            sorted(
                expected_local_responsibilities,
                key=lambda row: row.responsibility_ref,
            )
        )
        canonical_expected_opportunities = tuple(
            sorted(
                expected_opportunities,
                key=lambda row: row.opportunity_key,
            )
        )
        if (
            len(claims) != len(expected_claims)
            or any(
                (
                    getattr(actual, "schema_version", None),
                    getattr(actual, "subjective_claim_id", None),
                    getattr(actual, "parent_duty_ref", None),
                    getattr(actual, "speaker_owner", None),
                    getattr(actual, "claim_domain", None),
                    getattr(actual, "asserted_subjective_proposition", None),
                    getattr(actual, "basis_observation_contribution_refs", None),
                    getattr(actual, "basis_semantic_refs", None),
                    getattr(actual, "source_reception_act_refs", None),
                    getattr(actual, "value_principle_refs", None),
                    getattr(actual, "user_fact_effect", None),
                    getattr(actual, "forbidden_promotions", None),
                    getattr(actual, "subjective_responsibility_refs", None),
                    getattr(actual, "selected_subjective_opportunity_key", None),
                )
                != (
                    expected.schema_version,
                    expected.subjective_claim_id,
                    expected.parent_duty_ref,
                    (
                        composition.CMEE_STAGE1_EMLIS_OWNER_REF
                        if is_unsealed_plan
                        else "EMLIS"
                    ),
                    expected.claim_domain,
                    expected.asserted_subjective_proposition,
                    expected.basis_observation_contribution_refs,
                    expected.basis_semantic_refs,
                    expected.source_reception_act_refs,
                    expected.value_principle_refs,
                    expected.user_fact_effect,
                    expected.forbidden_promotions,
                    expected.subjective_responsibility_refs,
                    expected.selected_subjective_opportunity_key,
                )
                for actual, expected in zip(claims, expected_claims)
            )
            or tuple(
                (
                    row.responsibility_ref,
                    row.responsibility_kind,
                    row.owner_component_refs,
                    row.retained_reception_act_refs,
                )
                for row in responsibilities
            )
            != tuple(
                (
                    row.responsibility_ref,
                    row.responsibility_kind,
                    row.owner_component_refs,
                    row.retained_reception_act_refs,
                )
                for row in canonical_expected_responsibilities
            )
            or tuple(
                (
                    row.opportunity_key,
                    row.responsibility_refs,
                    row.content_kind,
                    row.content,
                    row.specificity_key,
                )
                for row in opportunities
            )
            != tuple(
                (
                    row.opportunity_key,
                    row.responsibility_refs,
                    row.content_kind,
                    row.content,
                    row.specificity_key,
                )
                for row in canonical_expected_opportunities
            )
            or reception_rows != tuple(expected_traces)
        ):
            raise CMEEStage1ContractError(
                "stage1_final_meaning_plan_noncanonical"
            )
    elif type(outcome) is LimitedMeaningOutcome:
        sources = phase_A.bounded_limited_subjective_proposition_records
        bounded = phase_A.bounded_limited_reception_records
        if (
            len(sources) != 1
            or len(bounded) != 1
            or len(reception_rows) != 1
            or len(claims) != 1
        ):
            raise CMEEStage1ContractError(
                "stage1_final_meaning_plan_noncanonical"
            )
        source = sources[0]
        trace = reception_rows[0]
        claim = claim_by_ref.get(trace.projected_claim_ref)
        content = _stage1_projected_content(source)
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
        }.get(source.content_kind)
        contribution_refs = source.target_contribution_refs
        (
            licensed_mode,
            licensed_operator,
            licensed_act_refs,
            licensed_contribution_refs,
            aggregate_attention,
        ) = resolve_limited_reception_aggregate(
            phase_A.retained_reception_act_rows,
            expected_act_refs=(
                phase_A.allowed_reception_opportunity_envelope
                .allowed_reception_act_ids
            ),
            retained_layer1_refs=(
                canonical_limited_retained_layer1_refs(
                    outcome.retained_layer1_refs,
                    phase_A.observation_contribution_rows,
                )
            ),
            observation_contribution_rows=(
                phase_A.observation_contribution_rows
            ),
        )
        if (
            claim is None
            or responsibility_kind is None
            or getattr(claim, "asserted_subjective_proposition", None)
            is not source
            or source.subjective_mode is not licensed_mode
            or source.subjective_operator is not licensed_operator
            or contribution_refs != licensed_contribution_refs
            or trace.layer1_contribution_refs != contribution_refs
            or trace.projected_response_object_refs
            != source.response_object_refs
        ):
            raise CMEEStage1ContractError(
                "stage1_final_meaning_plan_noncanonical"
            )
        require_claim_spine(
            claim=claim,
            proposition=source,
            responsibility_kind=responsibility_kind,
            contribution_refs=contribution_refs,
            semantic_refs=source.response_object_refs,
            act_refs=licensed_act_refs,
            value_refs=(),
            specificity=(
                SubjectiveSpecificity.MULTI_ROLE
                if len(source.response_object_refs) > 1
                else SubjectiveSpecificity.SINGLE_ROLE
            ),
            content=content,
        )
    else:
        raise CMEEStage1ContractError(
            "stage1_final_meaning_plan_noncanonical"
        )

    application_key = lambda row: (
        row.policy_application_row_ref,
        row.application_kind,
        row.principle_ref,
        row.material_risk,
        row.policy_basis_binding_refs,
        row.affected_claim_ref,
        row.visible_claim_ref,
    )
    if tuple(map(application_key, policy_application_rows)) != tuple(
        map(
            application_key,
            sorted(
                expected_policy_applications,
                key=stage1_policy_application_order_key,
            ),
        )
    ):
        raise CMEEStage1ContractError(
            "stage1_final_meaning_plan_noncanonical"
        )


def _validate_meaning_plan_carrier_trace(
    phase_A: "Stage1SubjectivePlanningInputs",
    meaning_plan: "EmlisSubjectiveMeaningPlan",
) -> None:
    """Resolve plan trace rows to carried B/C records without reprojecting."""

    _validate_meaning_plan_vertical_binding(phase_A, meaning_plan)
    structure = phase_A.input_specific_meaning_structure
    outcome = structure.meaning_decision_outcome
    meaning_rows = meaning_plan.meaning_visible_causal_trace_rows
    reception_rows = meaning_plan.reception_visible_causal_trace_rows
    if type(outcome) is SelectedEmlisProvisionalReading:
        candidates = tuple(
            row
            for row in structure.candidate_records
            if row.candidate_id == outcome.selected_candidate_ref
        )
        evidence = tuple(
            row
            for row in structure.input_specificity_evidence_records
            if len(candidates) == 1
            and row.candidate_ref == candidates[0].candidate_id
        )
        required_by_ref = {
            row.difference_id: row for row in structure.required_difference_rows
        }
        observed_by_ref = {
            row.distinction_id: row
            for row in structure.observed_distinction_rows
        }
        propositions = phase_A.meaning_bound_reception_proposition_records
        sealed = phase_A.sealed_emlis_provisional_reading_records
        if (
            meaning_plan.projection_branch
            is not SubjectiveProjectionBranch.NORMAL
            or len(candidates) != 1
            or len(evidence) != 1
            or len(sealed) != 1
            or tuple(
                getattr(row, "required_difference_ref", "")
                for row in meaning_rows
            )
            != evidence[0].required_difference_refs
            or len(reception_rows) != len(propositions)
        ):
            raise CMEEStage1ContractError(
                "stage1_final_meaning_plan_noncanonical"
            )
        for row in meaning_rows:
            difference = required_by_ref.get(
                getattr(row, "required_difference_ref", "")
            )
            observed = (
                None
                if difference is None
                else observed_by_ref.get(difference.observed_distinction_ref)
            )
            if (
                type(row) is not SelectedMeaningVisibleCausalTraceRow
                or difference is None
                or observed is None
                or row.selected_reading_ref != outcome.reading_id
                or row.configuration_ref != observed.configuration_ref
                or row.configuration_component_refs
                != observed.contrasted_component_refs
                or row.source_qualifier_refs != observed.source_qualifier_refs
                or row.invariant_codes != difference.invariant_codes
            ):
                raise CMEEStage1ContractError(
                    "stage1_final_meaning_plan_noncanonical"
                )
        for row, proposition in zip(
            reception_rows, propositions, strict=True
        ):
            if (
                type(row) is not ReceptionVisibleCausalTraceRow
                or row.branch is not SubjectiveProjectionBranch.NORMAL
                or row.meaning_outcome_ref != outcome.reading_id
                or row.reading_consequence_ref
                != sealed[0].reading_consequence_ref
                or row.reception_record_ref
                != meaning_bound_reception_id(proposition)
                or row.response_object_refs
                != proposition.response_object_refs
                or row.preserved_difference_refs
                != proposition.preserved_difference_refs
            ):
                raise CMEEStage1ContractError(
                    "stage1_final_meaning_plan_noncanonical"
                )
        return

    if type(outcome) is LimitedMeaningOutcome:
        bounded = phase_A.bounded_limited_reception_records
        propositions = (
            phase_A.bounded_limited_subjective_proposition_records
        )
        if (
            meaning_plan.projection_branch
            is not SubjectiveProjectionBranch.LIMITED
            or len(bounded) != 1
            or len(propositions) != 1
            or len(reception_rows) != 1
            or tuple(
                getattr(row, "source_object_ref", "")
                for row in meaning_rows
            )
            != bounded[0].foreground_source_object_refs
        ):
            raise CMEEStage1ContractError(
                "stage1_final_meaning_plan_noncanonical"
            )
        outcome_ref = limited_meaning_outcome_id(outcome)
        contribution_by_ref = {
            row.contribution_id: row
            for row in phase_A.observation_contribution_rows
        }
        try:
            (
                _licensed_mode,
                _licensed_operator,
                _licensed_act_refs,
                _licensed_contribution_refs,
                aggregate_attention,
            ) = resolve_limited_reception_aggregate(
                phase_A.retained_reception_act_rows,
                expected_act_refs=(
                    phase_A.allowed_reception_opportunity_envelope
                    .allowed_reception_act_ids
                ),
                retained_layer1_refs=(
                    canonical_limited_retained_layer1_refs(
                        outcome.retained_layer1_refs,
                        phase_A.observation_contribution_rows,
                    )
                ),
                observation_contribution_rows=(
                    phase_A.observation_contribution_rows
                ),
            )
        except CMEEStage1ContractError:
            raise CMEEStage1ContractError(
                "stage1_final_meaning_plan_noncanonical"
            ) from None
        trace_contribution_refs = (
            bounded[0].bound_layer1_contribution_refs
            if aggregate_attention
            else tuple(contribution_by_ref)
        )
        for row in meaning_rows:
            expected_layer1_refs = tuple(
                contribution_ref
                for contribution_ref in trace_contribution_refs
                if contribution_ref in contribution_by_ref
                if getattr(row, "source_object_ref", "")
                in {
                    *contribution_by_ref[contribution_ref].semantic_refs,
                    *contribution_by_ref[
                        contribution_ref
                    ].relation_basis_refs,
                    *(
                        binding.semantic_ref
                        for binding in contribution_by_ref[
                            contribution_ref
                        ].argument_bindings
                    ),
                }
            )
            if (
                type(row) is not LimitedMeaningVisibleCausalTraceRow
                or row.limited_outcome_ref != outcome_ref
                or not expected_layer1_refs
                or row.layer1_contribution_refs != expected_layer1_refs
            ):
                raise CMEEStage1ContractError(
                    "stage1_final_meaning_plan_noncanonical"
                )
        reception = reception_rows[0]
        if (
            type(reception) is not ReceptionVisibleCausalTraceRow
            or reception.branch is not SubjectiveProjectionBranch.LIMITED
            or reception.meaning_outcome_ref != outcome_ref
            or reception.reading_consequence_ref is not None
            or reception.reception_record_ref
            != bounded_limited_reception_id(
                bounded[0],
                limited_outcome=outcome,
                subjective_proposition=propositions[0],
            )
            or reception.response_object_refs
            != bounded[0].foreground_source_object_refs
            or reception.preserved_difference_refs
        ):
            raise CMEEStage1ContractError(
                "stage1_final_meaning_plan_noncanonical"
            )
        return
    raise CMEEStage1ContractError("stage1_final_meaning_plan_noncanonical")


def _validate_meaning_plan_integrity(
    phase_A: "Stage1SubjectivePlanningInputs",
    meaning_plan: "EmlisSubjectiveMeaningPlan",
    *,
    composition: Any,
) -> None:
    """Reject every plan field that the final projection would normalize."""

    tuple_field_names = (
        "meaning_visible_causal_trace_rows",
        "reception_visible_causal_trace_rows",
        "subjective_claim_rows",
        "content_bearing_thought_claim_refs",
        "retained_reception_act_refs",
        "subjective_responsibility_rows",
        "subjective_opportunity_rows",
        "responsibility_coverage_rows",
        "subjective_basis_binding_rows",
        "source_qualifier_binding_rows",
        "policy_basis_binding_rows",
        "policy_application_rows",
        "subjective_facet_suppression_rows",
    )
    if any(
        type(getattr(meaning_plan, field_name, None)) is not tuple
        for field_name in tuple_field_names
    ):
        raise CMEEStage1ContractError(
            "stage1_final_meaning_plan_noncanonical"
        )
    claims = meaning_plan.subjective_claim_rows
    responsibilities = meaning_plan.subjective_responsibility_rows
    opportunities = meaning_plan.subjective_opportunity_rows
    coverage = meaning_plan.responsibility_coverage_rows
    suppressions = meaning_plan.subjective_facet_suppression_rows
    if (
        not 1 <= len(claims) <= 4
        or any(
            type(row) is not composition.ProjectedSubjectiveClaim
            for row in claims
        )
        or any(
            type(row) is not composition.SubjectiveResponsibilityRow
            for row in responsibilities
        )
        or any(
            type(row) is not composition.SubjectiveOpportunityRow
            for row in opportunities
        )
        or any(
            type(row) is not composition.ResponsibilityCoverageRow
            for row in coverage
        )
        or any(
            type(row) is not composition.SubjectiveFacetSuppressionRow
            for row in suppressions
        )
        or any(
            type(row) is not composition.SubjectiveBasisBinding
            for row in meaning_plan.subjective_basis_binding_rows
        )
        or any(
            type(row) is not composition.SourceQualifierBinding
            for row in meaning_plan.source_qualifier_binding_rows
        )
        or any(
            type(row) is not composition.PolicyBasisBinding
            for row in meaning_plan.policy_basis_binding_rows
        )
        or any(
            type(row) is not composition.PolicyApplicationRow
            for row in meaning_plan.policy_application_rows
        )
        or responsibilities
        != tuple(sorted(responsibilities, key=lambda row: row.responsibility_ref))
        or opportunities
        != tuple(sorted(opportunities, key=lambda row: row.opportunity_key))
        or coverage
        != tuple(sorted(coverage, key=lambda row: row.responsibility_ref))
        or suppressions
        != tuple(
            sorted(
                suppressions,
                key=lambda row: row.suppressed_opportunity_key,
            )
        )
        or meaning_plan.subjective_basis_binding_rows
        != tuple(
            sorted(
                meaning_plan.subjective_basis_binding_rows,
                key=lambda row: row.binding_ref,
            )
        )
        or meaning_plan.source_qualifier_binding_rows
        != tuple(
            sorted(
                meaning_plan.source_qualifier_binding_rows,
                key=lambda row: row.source_qualifier_binding_ref,
            )
        )
        or meaning_plan.policy_basis_binding_rows
        != tuple(
            sorted(
                meaning_plan.policy_basis_binding_rows,
                key=lambda row: row.binding_ref,
            )
        )
        or meaning_plan.policy_application_rows
        != tuple(
            sorted(
                meaning_plan.policy_application_rows,
                key=stage1_policy_application_order_key,
            )
        )
    ):
        raise CMEEStage1ContractError(
            "stage1_final_meaning_plan_noncanonical"
        )
    try:
        composition._validate_subjective_opportunity_partition(
            responsibilities=responsibilities,
            opportunities=opportunities,
            claims=claims,
            coverage=coverage,
            suppressions=suppressions,
        )
    except composition.Stage1CompositionError:
        raise CMEEStage1ContractError(
            "stage1_final_meaning_plan_noncanonical"
        ) from None

    expected_thought_refs = tuple(
        claim.subjective_claim_id
        for claim in claims
        if claim.asserted_subjective_proposition.content_kind
        is not SubjectiveContentKind.AFFECT
    )
    expected_retained_act_refs = tuple(
        row.act_ref for row in phase_A.retained_reception_act_rows
    )
    if (
        meaning_plan.thought_support_status
        != ("SUPPORTED" if expected_thought_refs else "NOT_SUPPORTED")
        or meaning_plan.content_bearing_thought_claim_refs
        != expected_thought_refs
        or meaning_plan.retained_reception_act_refs
        != expected_retained_act_refs
    ):
        raise CMEEStage1ContractError(
            "stage1_final_meaning_plan_noncanonical"
        )

    seen_claim_refs: set[str] = set()
    for claim in claims:
        proposition = claim.asserted_subjective_proposition
        if (
            claim.schema_version
            != composition.CMEE_STAGE1_RESPONSE_SCHEMA_VERSION
            or claim.parent_duty_ref
            != phase_A.parent_plan.reception_duty_id
            or claim.speaker_owner
            != composition.CMEE_STAGE1_EMLIS_OWNER_REF
            or claim.claim_domain != "EMLIS_SUBJECTIVE_RESPONSE"
            or type(proposition) is not SubjectivePropositionV2
            or type(claim.user_fact_effect) is not int
            or claim.user_fact_effect != 0
            or claim.subjective_claim_id in seen_claim_refs
        ):
            raise CMEEStage1ContractError(
                "stage1_final_meaning_plan_noncanonical"
            )
        final_claim = EmlisSubjectiveClaim(
            schema_version=claim.schema_version,
            subjective_claim_id=claim.subjective_claim_id,
            parent_duty_ref=claim.parent_duty_ref,
            speaker_owner="EMLIS",
            claim_domain=claim.claim_domain,
            subjective_mode=proposition.subjective_mode,
            asserted_subjective_proposition=proposition,
            basis_observation_contribution_refs=(
                claim.basis_observation_contribution_refs
            ),
            basis_semantic_refs=claim.basis_semantic_refs,
            source_reception_act_refs=claim.source_reception_act_refs,
            value_principle_refs=claim.value_principle_refs,
            user_fact_effect=claim.user_fact_effect,
            forbidden_promotions=claim.forbidden_promotions,
            subjective_responsibility_refs=(
                claim.subjective_responsibility_refs
            ),
            selected_subjective_opportunity_key=(
                claim.selected_subjective_opportunity_key
            ),
        )
        validate_stage1_identity(final_claim)
        seen_claim_refs.add(claim.subjective_claim_id)


def seal_stage1_projection(
    phase_A: "Stage1SubjectivePlanningInputs",
    meaning_plan: "EmlisSubjectiveMeaningPlan",
) -> EmlisStage1Projection:
    """Seal one final v2 projection without activating the current facade."""

    from . import emlis_stage1_composition as composition

    if type(phase_A) is not composition.Stage1SubjectivePlanningInputs:
        raise CMEEStage1ContractError("stage1_final_phase_a_type_invalid")
    if type(meaning_plan) is not composition.EmlisSubjectiveMeaningPlan:
        raise CMEEStage1ContractError("stage1_final_meaning_plan_type_invalid")
    try:
        composition._validate_phase_A(phase_A)
    except composition.Stage1CompositionError:
        raise CMEEStage1ContractError(
            "stage1_final_phase_a_noncanonical"
        ) from None
    _validate_meaning_plan_carrier_trace(phase_A, meaning_plan)
    _validate_meaning_plan_integrity(
        phase_A,
        meaning_plan,
        composition=composition,
    )
    if meaning_plan.projection_preimage_ref != phase_A.projection_preimage_ref:
        raise CMEEStage1ContractError("stage1_final_meaning_plan_noncanonical")
    if (
        meaning_plan.projection_seal_ref != phase_A.projection_seal_ref
        or type(meaning_plan.projection_branch)
        is not SubjectiveProjectionBranch
        or meaning_plan.tagged_projection_ref
        != project_stage1_tagged_projection_ref(
            projection_branch=meaning_plan.projection_branch,
            projection_seal_ref=meaning_plan.projection_seal_ref,
            meaning_visible_causal_trace_rows=(
                meaning_plan.meaning_visible_causal_trace_rows
            ),
            reception_visible_causal_trace_rows=(
                meaning_plan.reception_visible_causal_trace_rows
            ),
        )
    ):
        raise CMEEStage1ContractError("stage1_final_meaning_plan_noncanonical")
    projected_claims = tuple(meaning_plan.subjective_claim_rows)
    if (
        not 1 <= len(projected_claims) <= 4
        or any(
            type(claim.asserted_subjective_proposition)
            is not SubjectivePropositionV2
            for claim in projected_claims
        )
    ):
        raise CMEEStage1ContractError("stage1_final_meaning_plan_noncanonical")
    claim_pairs = tuple(
        (
            claim.subjective_claim_id,
            _identified(
                EmlisSubjectiveClaim(
                    schema_version=claim.schema_version,
                    subjective_claim_id="",
                    parent_duty_ref=claim.parent_duty_ref,
                    speaker_owner="EMLIS",
                    claim_domain=claim.claim_domain,
                    subjective_mode=(
                        claim.asserted_subjective_proposition.subjective_mode
                    ),
                    asserted_subjective_proposition=(
                        claim.asserted_subjective_proposition
                    ),
                    basis_observation_contribution_refs=(
                        claim.basis_observation_contribution_refs
                    ),
                    basis_semantic_refs=claim.basis_semantic_refs,
                    source_reception_act_refs=(
                        claim.source_reception_act_refs
                    ),
                    value_principle_refs=claim.value_principle_refs,
                    user_fact_effect=claim.user_fact_effect,
                    forbidden_promotions=claim.forbidden_promotions,
                    subjective_responsibility_refs=(
                        claim.subjective_responsibility_refs
                    ),
                    selected_subjective_opportunity_key=(
                        claim.selected_subjective_opportunity_key
                    ),
                ),
                "subjective_claim_id",
            ),
        )
        for claim in projected_claims
    )
    claims = tuple(row for _source_ref, row in claim_pairs)
    claim_id_by_projected_ref = {
        source_ref: row.subjective_claim_id for source_ref, row in claim_pairs
    }
    if len(claim_id_by_projected_ref) != len(claim_pairs):
        raise CMEEStage1ContractError("stage1_final_meaning_plan_noncanonical")
    for claim in claims:
        validate_stage1_identity(claim)
    grammar_version = composition.CMEE_STAGE1_CONSTRUCTION_GRAMMAR_POLICY_VERSION
    grammar_policy_id = grammar_version.rsplit(".", 1)[0]
    grammar_policy_ref = f"policy:{grammar_policy_id}@{grammar_version}"
    composition_version = composition.CMEE_STAGE1_COMPOSITION_POLICY_VERSION
    composition_policy_id = composition_version.rsplit(".", 1)[0]
    composition_policy_ref = (
        f"policy:{composition_policy_id}@{composition_version}"
    )
    responsibility_rows = tuple(
        sorted(
            (
                SubjectiveResponsibilityRow(
                    responsibility_ref=row.responsibility_ref,
                    responsibility_kind=SubjectiveResponsibilityKind(
                        row.responsibility_kind.value
                    ),
                    owner_component_refs=row.owner_component_refs,
                    retained_reception_act_refs=(
                        row.retained_reception_act_refs
                    ),
                )
                for row in meaning_plan.subjective_responsibility_rows
            ),
            key=lambda row: row.responsibility_ref,
        )
    )
    opportunity_rows = tuple(
        sorted(
            (
                SubjectiveOpportunityRow(
                    opportunity_key=row.opportunity_key,
                    responsibility_refs=row.responsibility_refs,
                    content_kind=row.content_kind,
                    content=row.content,
                    specificity_key=SubjectiveSpecificity(
                        row.specificity_key.value
                    ),
                )
                for row in meaning_plan.subjective_opportunity_rows
            ),
            key=lambda row: row.opportunity_key,
        )
    )
    suppression_rows = tuple(
        sorted(
            (
                SubjectiveFacetSuppressionRow(
                    suppressed_opportunity_key=(
                        row.suppressed_opportunity_key
                    ),
                    reason=SubjectiveFacetSuppressionReason(
                        row.reason.value
                    ),
                    absorbed_by_selected_opportunity_key=(
                        row.absorbed_by_selected_opportunity_key
                    ),
                )
                for row in meaning_plan.subjective_facet_suppression_rows
            ),
            key=lambda row: row.suppressed_opportunity_key,
        )
    )
    policy_application_rows = tuple(
        sorted(
            (
                PolicyApplicationRow(
                    policy_application_row_ref=(
                        row.policy_application_row_ref
                    ),
                    application_kind=row.application_kind,
                    principle_ref=row.principle_ref,
                    material_risk=row.material_risk,
                    policy_basis_binding_refs=(
                        row.policy_basis_binding_refs
                    ),
                    affected_claim_ref=claim_id_by_projected_ref.get(
                        row.affected_claim_ref,
                        "",
                    ),
                    visible_claim_ref=(
                        claim_id_by_projected_ref.get(
                            row.visible_claim_ref,
                            "",
                        )
                        if row.visible_claim_ref is not None
                        else None
                    ),
                )
                for row in meaning_plan.policy_application_rows
            ),
            key=stage1_policy_application_order_key,
        )
    )
    projection = EmlisStage1Projection(
        schema_version=composition.CMEE_STAGE1_RESPONSE_SCHEMA_VERSION,
        projection_id="",
        grounded_graph_ref=_graph_ref(phase_A.grounded_graph),
        parent_observation_duty_ref=phase_A.parent_plan.observation_duty_id,
        parent_reception_duty_ref=phase_A.parent_plan.reception_duty_id,
        interpretation_candidates=phase_A.interpretation_candidate_rows,
        meaning_field=phase_A.meaning_field,
        observation_contributions=phase_A.observation_contribution_rows,
        subjective_claims=claims,
        ordered_observation_refs=tuple(
            row.contribution_id
            for row in phase_A.observation_contribution_rows
        ),
        ordered_subjective_refs=tuple(
            row.subjective_claim_id for row in claims
        ),
        retained_reception_act_ids=tuple(
            row.act_ref for row in phase_A.retained_reception_act_rows
        ),
        observation_depth_class=phase_A.observation_depth_class,
        subjective_depth_class=_final_subjective_depth(len(claims)),
        temperature_class=phase_A.temperature_class,
        reception_style_policy_ref=phase_A.reception_style_policy_ref,
        emlis_value_policy_ref=phase_A.emlis_value_policy_ref,
        emlis_microgrammar_policy_ref="",
        projection_preimage_ref=phase_A.projection_preimage_ref,
        projection_seal_ref=meaning_plan.projection_seal_ref,
        projection_branch=meaning_plan.projection_branch,
        tagged_projection_ref=meaning_plan.tagged_projection_ref,
        meaning_visible_causal_trace_rows=(
            meaning_plan.meaning_visible_causal_trace_rows
        ),
        reception_visible_causal_trace_rows=(
            meaning_plan.reception_visible_causal_trace_rows
        ),
        composition_policy_ref=composition_policy_ref,
        low_level_grammar_policy_ref=grammar_policy_ref,
        subjective_responsibility_rows=responsibility_rows,
        subjective_opportunity_rows=opportunity_rows,
        subjective_facet_suppression_rows=suppression_rows,
        subjective_basis_binding_rows=tuple(
            sorted(
                meaning_plan.subjective_basis_binding_rows,
                key=lambda row: row.binding_ref,
            )
        ),
        source_qualifier_binding_rows=tuple(
            sorted(
                meaning_plan.source_qualifier_binding_rows,
                key=lambda row: row.source_qualifier_binding_ref,
            )
        ),
        policy_basis_binding_rows=tuple(
            sorted(
                meaning_plan.policy_basis_binding_rows,
                key=lambda row: row.binding_ref,
            )
        ),
        policy_application_rows=policy_application_rows,
    )
    identified = _identified(projection, "projection_id")
    validate_stage1_identity(identified)
    validate_stage1_projection(
        identified,
        grounded_graph=phase_A.grounded_graph,
        parent_plan=phase_A.parent_plan,
    )
    return identified


def build_surface_composition_inputs(
    phase_A: "Stage1SubjectivePlanningInputs",
    final_projection: EmlisStage1Projection,
) -> "Stage1SurfaceCompositionInputs":
    """Build Phase B from the exact Phase-A closure and its final seal."""

    from . import emlis_stage1_composition as composition

    if type(phase_A) is not composition.Stage1SubjectivePlanningInputs:
        raise CMEEStage1ContractError("stage1_final_phase_a_type_invalid")
    if type(final_projection) is not EmlisStage1Projection:
        raise CMEEStage1ContractError("stage1_final_projection_type_invalid")
    try:
        composition._validate_phase_A(phase_A)
    except composition.Stage1CompositionError:
        raise CMEEStage1ContractError(
            "stage1_final_phase_a_noncanonical"
        ) from None
    validate_stage1_identity(final_projection)
    validate_stage1_projection(
        final_projection,
        grounded_graph=phase_A.grounded_graph,
        parent_plan=phase_A.parent_plan,
    )
    _validate_meaning_plan_carrier_trace(phase_A, final_projection)
    expected_branch = (
        SubjectiveProjectionBranch.NORMAL
        if type(
            phase_A.input_specific_meaning_structure.meaning_decision_outcome
        )
        is SelectedEmlisProvisionalReading
        else SubjectiveProjectionBranch.LIMITED
    )
    if (
        final_projection.projection_preimage_ref
        != phase_A.projection_preimage_ref
        or final_projection.projection_seal_ref
        != phase_A.projection_seal_ref
        or final_projection.projection_branch is not expected_branch
        or final_projection.interpretation_candidates
        != phase_A.interpretation_candidate_rows
        or final_projection.meaning_field != phase_A.meaning_field
        or final_projection.observation_contributions
        != phase_A.observation_contribution_rows
        or final_projection.retained_reception_act_ids
        != tuple(row.act_ref for row in phase_A.retained_reception_act_rows)
        or final_projection.parent_observation_duty_ref
        != phase_A.parent_plan.observation_duty_id
        or final_projection.parent_reception_duty_ref
        != phase_A.parent_plan.reception_duty_id
    ):
        raise CMEEStage1ContractError("stage1_final_projection_noncanonical")
    participant_values = {
        _enum_or_text(getattr(row.grounded_frame, "actor", "")).lower()
        for row in phase_A.resolved_grounded_frame_by_candidate_ref
    }
    addressee_deictic_context = bool(
        participant_values.intersection({"current_user", "user"})
    )
    section_speaker_owner_ref = (
        composition.CMEE_STAGE1_EMLIS_OWNER_REF
        if final_projection.subjective_claims
        else None
    )
    return composition.Stage1SurfaceCompositionInputs(
        phase_A_authority=phase_A,
        admitted_source=phase_A.admitted_source,
        grounded_graph=phase_A.grounded_graph,
        grounded_plan=phase_A.grounded_plan,
        parent_plan=phase_A.parent_plan,
        projection=final_projection,
        resolved_grounded_frame_by_candidate_ref=(
            phase_A.resolved_grounded_frame_by_candidate_ref
        ),
        relation_endpoint_grounded_candidate_ref_by_binding_key=(
            phase_A.relation_endpoint_grounded_candidate_ref_by_binding_key
        ),
        qualifier_value_by_candidate_scope_axis_key=(
            phase_A.qualifier_value_by_candidate_scope_axis_key
        ),
        addressee_deictic_context=addressee_deictic_context,
        section_speaker_owner_ref=section_speaker_owner_ref,
        construction_registry_snapshot=phase_A.construction_registry_snapshot,
        expression_asset_registry_snapshot=phase_A.expression_asset_registry_snapshot,
        response_object_registry_snapshot=phase_A.response_object_registry_snapshot,
        functional_asset_registry_snapshot=phase_A.functional_asset_registry_snapshot,
        participant_asset_registry_snapshot=phase_A.participant_asset_registry_snapshot,
        structural_asset_registry_snapshot=phase_A.structural_asset_registry_snapshot,
        profile_rule_registry_snapshot=phase_A.profile_rule_registry_snapshot,
    )


def build_stage1_semantic_projection(
    *,
    source: AdmittedTextSource,
    grounded_graph: GroundedMeaningGraph,
    parent_plan: ExperiencePlan,
    grounded_plan: GroundedObservationPlan,
    stage1_response_schema_version: str = (
        CMEE_STAGE1_RESPONSE_SCHEMA_VERSION_V1
    ),
) -> EmlisStage1Projection:
    """Build and fully validate the disabled Step 3 semantic projection."""

    (
        candidates,
        meaning_field,
        contributions,
        ordered_observation_refs,
        observation_depth,
    ) = build_layer1_semantics(
        source=source,
        grounded_graph=grounded_graph,
        parent_plan=parent_plan,
        grounded_plan=grounded_plan,
        stage1_response_schema_version=stage1_response_schema_version,
    )
    claims = plan_layer2_subjectivity(
        source=source,
        grounded_graph=grounded_graph,
        parent_plan=parent_plan,
        grounded_plan=grounded_plan,
        observation_contributions=contributions,
        stage1_response_schema_version=stage1_response_schema_version,
    )
    reception_plan = _semantic_reception_asset(
        source=source,
        grounded_plan=grounded_plan,
    )
    projection = EmlisStage1Projection(
        schema_version=stage1_response_schema_version,
        projection_id="",
        grounded_graph_ref=_graph_ref(grounded_graph),
        parent_observation_duty_ref=parent_plan.observation_duty_id,
        parent_reception_duty_ref=parent_plan.reception_duty_id,
        interpretation_candidates=candidates,
        meaning_field=meaning_field,
        observation_contributions=contributions,
        subjective_claims=claims,
        ordered_observation_refs=ordered_observation_refs,
        ordered_subjective_refs=tuple(
            claim.subjective_claim_id for claim in claims
        ),
        retained_reception_act_ids=parent_plan.allowed_reception_act_ids,
        observation_depth_class=observation_depth,
        subjective_depth_class=classify_subjective_depth(claims),
        temperature_class=_temperature_for_reception_asset(
            reception_plan,
            grounded_plan,
        ),
        reception_style_policy_ref=_style_policy_ref_for_stance(
            str(reception_plan.stance)
        ),
        emlis_value_policy_ref=CMEE_STAGE1_VALUE_POLICY_REF,
        emlis_microgrammar_policy_ref=CMEE_STAGE1_MICROGRAMMAR_POLICY_REF,
    )
    identified = _identified(projection, "projection_id")
    validate_stage1_projection(
        identified,
        grounded_graph=grounded_graph,
        parent_plan=parent_plan,
    )
    return identified


def _validate_microgrammar_inventory() -> None:
    canonical_bytes = stage1_canonical_json_bytes(
        CMEE_STAGE1_MICROGRAMMAR_INVENTORY_TUPLE
    )
    canonical_sections = dict(CMEE_STAGE1_MICROGRAMMAR_INVENTORY_TUPLE)
    expected_observation_rows = {
        (operator, relation): (primary, alternate, condition)
        for operator, relation, _family, primary, alternate, condition
        in canonical_sections["observation_operator_rows"]
    }
    expected_observation_families = {
        (operator, relation): family
        for operator, relation, family, _primary, _alternate, _condition
        in canonical_sections["observation_operator_rows"]
    }
    expected_subjective_rows = {
        (operator, detail): (primary, alternate)
        for operator, detail, _family, primary, alternate
        in canonical_sections["subjective_operator_rows"]
    }
    expected_subjective_families = {
        (operator, detail): family
        for operator, detail, family, _primary, _alternate
        in canonical_sections["subjective_operator_rows"]
    }
    expected_operator_connectives = {
        (layer, operator): family
        for layer, operator, family
        in canonical_sections["operator_connective_rows"]
    }
    if (
        canonical_bytes != CMEE_STAGE1_MICROGRAMMAR_INVENTORY_DOCS_BYTES
        or hashlib.sha256(canonical_bytes).hexdigest()
        != CMEE_STAGE1_MICROGRAMMAR_INVENTORY_DOCS_SHA256
        or _MICROGRAMMAR_SECTIONS != canonical_sections
        or _OBSERVATION_PREDICATE_ROWS != expected_observation_rows
        or _OBSERVATION_PREDICATE_FAMILIES
        != expected_observation_families
        or _SUBJECTIVE_PREDICATE_ROWS != expected_subjective_rows
        or _SUBJECTIVE_PREDICATE_FAMILIES != expected_subjective_families
        or _ATTENTION_SURFACE_ROWS
        != dict(canonical_sections["attention_surface_rows"])
        or _CONNECTIVE_FAMILIES
        != dict(canonical_sections["connective_families"])
        or _OPERATOR_CONNECTIVES != expected_operator_connectives
        or _MODALITY_WRAPPERS
        != dict(canonical_sections["modality_wrappers"])
        or _TIME_WRAPPERS != dict(canonical_sections["time_wrappers"])
        or _LAYER1_DIRECT_SLOTS
        != {
            operator: dict(rows)
            for operator, rows in canonical_sections["layer1_direct_slots"]
        }
        or _LAYER2_ANAPHORIC_SURFACES
        != dict(canonical_sections["layer2_anaphoric_surfaces"])
        or _MODALITY_ANAPHORIC_SURFACES
        != dict(canonical_sections["modality_anaphoric_surfaces"])
        or _LAYER2_EXPLICIT_NOMINALIZERS
        != dict(canonical_sections["layer2_explicit_nominalizers"])
        or _DIRECTION_UNDER_BURDEN_SURFACE
        != dict(canonical_sections["direction_under_burden_surface"])
        or _DIRECT_CONTRAST_SURFACE
        != dict(canonical_sections["direct_contrast_surface"])
        or _CONTEXT_RESIDUE_SURFACE
        != dict(canonical_sections["context_residue_surface"])
        or _OPEN_QUESTION_SURFACE
        != dict(canonical_sections["open_question_surface"])
        or _COMPOUND_BURDEN_SURFACE
        != dict(canonical_sections["compound_burden_surface"])
        or _BODY_BURDEN_SURFACE
        != dict(canonical_sections["body_burden_surface"])
        or _EPISTEMIC_BURDEN_SURFACE
        != dict(canonical_sections["epistemic_burden_surface"])
        or _ACTION_CHANGE_SURFACE
        != dict(canonical_sections["action_change_surface"])
        or _SIMPLE_CHANGE_SURFACE
        != dict(canonical_sections["simple_change_surface"])
        or _BOUNDED_SELF_DENIAL_SURFACE
        != dict(canonical_sections["bounded_self_denial_surface"])
        or _RELATION_TIME_PRECEDENCE
        != tuple(canonical_sections["relation_time_precedence"])
        or _LAYER1_OPTIONAL_CONNECTIVES
        != dict(canonical_sections["layer1_optional_connective_rows"])
        or _LAYER1_RELATION_SLOTS
        != dict(canonical_sections["layer1_relation_slots"])
        or _LAYER2_CASE_PARTICLES
        != dict(canonical_sections["layer2_case_particles"])
        or _SUBJECTIVE_SEMANTIC_PREDICATE_ROTATIONS
        != frozenset(
            tuple(row)
            for row in canonical_sections[
                "subjective_semantic_predicate_rotation_rows"
            ]
        )
        or _SUBJECTIVE_SEMANTIC_CONNECTIVE_ROTATIONS
        != frozenset(
            tuple(row)
            for row in canonical_sections[
                "subjective_semantic_connective_rotation_rows"
            ]
        )
        or _SUBJECTIVE_BASIS_CONNECTIVES
        != {
            (operator, detail, relation): family
            for operator, detail, relation, family
            in canonical_sections["subjective_basis_connective_rows"]
        }
        or _STRUCTURAL_TOKENS
        != dict(canonical_sections["structural_tokens"])
        or _TOPIC_SPEAKER_POLICY
        != dict(canonical_sections["topic_speaker_policy"])
        or _REFERENCE_MODE_POLICY
        != dict(canonical_sections["reference_mode_policy"])
        or _QUOTE_POLICY != dict(canonical_sections["quote_policy"])
        or _ROLE_ANCHOR_POLICY
        != dict(canonical_sections["role_anchor_policy"])
        or _SOURCE_SHAPE_RECOGNIZERS
        != dict(canonical_sections["source_shape_recognizers"])
        or _SOURCE_SHAPE_INFLECTIONS
        != dict(canonical_sections["source_shape_inflections"])
        or _VARIANT_POLICY != dict(canonical_sections["variant_policy"])
        or _MICROGRAMMAR_SECTIONS.get("policy_id")
        != CMEE_STAGE1_MICROGRAMMAR_POLICY_VERSION
        or _MICROGRAMMAR_SECTIONS.get("policy_ref")
        != CMEE_STAGE1_MICROGRAMMAR_POLICY_REF
        or len(canonical_sections["observation_operator_rows"]) != 12
        or len(_OBSERVATION_PREDICATE_ROWS) != 12
        or len(_SUBJECTIVE_PREDICATE_ROWS) != 14
        or len(_CONNECTIVE_FAMILIES) != 9
        or len(_OPERATOR_CONNECTIVES) != 12
        or _VARIANT_POLICY.get("max_candidates") != 2
        or _VARIANT_POLICY.get("automatic_retry") != 0
        or _VARIANT_POLICY.get("post_defect_generation") != 0
        or _VARIANT_POLICY.get("predicate_case_pair_atomic") is not True
        or _ROLE_ANCHOR_POLICY.get("max_graphemes") != 32
        or _ROLE_ANCHOR_POLICY.get("inserted_token_count") != 0
        or _ROLE_ANCHOR_POLICY.get("full_value_replay_over_limit") is not False
        or _QUOTE_POLICY.get("l1_max_graphemes") != 16
        or _QUOTE_POLICY.get("l2_max_graphemes") != 16
        or _QUOTE_POLICY.get("full_replay") is not False
        or set(_REFERENCE_MODE_POLICY) != {
            "anaphoric_first",
            "short_anchor_if_ambiguous",
            "explicit_emlis_counterposition",
        }
    ):
        raise CMEEStage1ContractError("stage1_microgrammar_inventory_invalid")
    family_tokens: dict[str, set[str]] = {}
    family_names: set[str] = set()
    for family_name, entries in _MICROGRAMMAR_SECTIONS["predicate_families"]:
        if family_name in family_names or type(entries) is not tuple or not entries:
            raise CMEEStage1ContractError("stage1_microgrammar_inventory_invalid")
        family_names.add(family_name)
        if family_name == "EMLIS_AFFECT_V1":
            tokens = tuple(token for _category, token in entries)
        else:
            tokens = entries
        if any(type(token) is not str or not token for token in tokens):
            raise CMEEStage1ContractError("stage1_microgrammar_inventory_invalid")
        family_tokens[family_name] = set(tokens)
    for key, (primary, alternate, _condition) in _OBSERVATION_PREDICATE_ROWS.items():
        tokens = family_tokens.get(_OBSERVATION_PREDICATE_FAMILIES.get(key, ""), set())
        if primary not in tokens or (alternate and alternate not in tokens):
            raise CMEEStage1ContractError("stage1_microgrammar_inventory_invalid")
    for key, (primary, alternate) in _SUBJECTIVE_PREDICATE_ROWS.items():
        tokens = family_tokens.get(_SUBJECTIVE_PREDICATE_FAMILIES.get(key, ""), set())
        if primary not in tokens or (alternate and alternate not in tokens):
            raise CMEEStage1ContractError("stage1_microgrammar_inventory_invalid")
    attention_tokens = family_tokens.get(
        "EMLIS_ATTENTION_APPRAISAL_V1",
        set(),
    )
    admitted_particles = set(_LAYER2_CASE_PARTICLES.values())
    if (
        "*:*" not in _ATTENTION_SURFACE_ROWS
        or any(
            type(variants) is not tuple
            or len(variants) != 2
            or any(
                type(pair) is not tuple
                or len(pair) != 2
                or pair[0] not in admitted_particles
                or pair[1] not in attention_tokens
                for pair in variants
            )
            for variants in _ATTENTION_SURFACE_ROWS.values()
        )
    ):
        raise CMEEStage1ContractError("stage1_microgrammar_inventory_invalid")
    if any(
        family not in _CONNECTIVE_FAMILIES
        for family in _OPERATOR_CONNECTIVES.values()
    ):
        raise CMEEStage1ContractError("stage1_microgrammar_inventory_invalid")
    if (
        set(_MODALITY_ANAPHORIC_SURFACES) != set(_MODALITY_WRAPPERS)
        or any(
            family not in _CONNECTIVE_FAMILIES
            for family in _SUBJECTIVE_BASIS_CONNECTIVES.values()
        )
        or any(
            (operator, detail) not in _SUBJECTIVE_PREDICATE_ROWS
            or not _SUBJECTIVE_PREDICATE_ROWS[(operator, detail)][1]
            for operator, detail, _semantic_operator, _time_scope
            in _SUBJECTIVE_SEMANTIC_PREDICATE_ROTATIONS
        )
        or any(
            ("LAYER_2", operator) not in _OPERATOR_CONNECTIVES
            or len(
                _CONNECTIVE_FAMILIES[
                    _OPERATOR_CONNECTIVES[("LAYER_2", operator)]
                ]
            )
            != 2
            for operator, _detail, _semantic_operator, _time_scope
            in _SUBJECTIVE_SEMANTIC_CONNECTIVE_ROTATIONS
        )
    ):
        raise CMEEStage1ContractError("stage1_microgrammar_inventory_invalid")
    if tuple(sorted((_PRIMARY_VARIANT_ID, _ALTERNATE_VARIANT_ID))) != (
        _PRIMARY_VARIANT_ID,
        _ALTERNATE_VARIANT_ID,
    ):
        raise CMEEStage1ContractError("stage1_microgrammar_variant_order_invalid")


def _candidate_for_contribution(
    projection: EmlisStage1Projection,
    contribution: PlannedObservationContribution,
) -> EmlisInterpretationCandidate:
    return resolve_candidate_for_contribution(
        projection.interpretation_candidates,
        contribution,
    )


def resolve_candidate_for_contribution(
    candidate_rows: Sequence[EmlisInterpretationCandidate],
    contribution: PlannedObservationContribution,
) -> EmlisInterpretationCandidate:
    """Resolve one contribution without requiring a final projection."""

    rows = tuple(
        row
        for row in candidate_rows
        if row.candidate_id in set(contribution.interpretation_candidate_refs)
    )
    if len(rows) != 1:
        raise CMEEStage1ContractError("stage1_realization_candidate_binding_invalid")
    return rows[0]


def _qualifier_value(
    candidate: EmlisInterpretationCandidate,
    axis: str,
    *,
    role: Optional[ArgumentRole] = None,
) -> str:
    return resolve_qualifier_value(candidate, axis, role=role)


def resolve_qualifier_value(
    candidate: EmlisInterpretationCandidate,
    axis: str,
    *,
    role: Optional[ArgumentRole] = None,
) -> str:
    """Resolve one frozen scalar axis from its actual candidate owner."""

    prefix = f"{role.value.lower()}_" if role is not None else ""
    marker = f"{prefix}{axis}:"
    values = tuple(
        row[len(marker) :]
        for row in candidate.required_qualifiers
        if row.startswith(marker)
    )
    if len(values) != 1 or not values[0]:
        raise CMEEStage1ContractError("stage1_microgrammar_qualifier_missing")
    return values[0]


def _observation_predicate_spec(
    projection: EmlisStage1Projection,
    contribution: PlannedObservationContribution,
) -> tuple[str, str]:
    candidate = _candidate_for_contribution(projection, contribution)
    if (
        candidate.candidate_kind is InterpretationKind.DIRECTION_UNDER_BURDEN
        and contribution.relation_operator is RelationOperator.COEXISTS_WITH
    ):
        predicate = _DIRECTION_UNDER_BURDEN_SURFACE.get("predicate")
        if not predicate:
            raise CMEEStage1ContractError(
                "stage1_microgrammar_predicate_missing"
            )
        return predicate, ""
    key = (
        contribution.semantic_operator.value,
        contribution.relation_operator.value,
    )
    row = _OBSERVATION_PREDICATE_ROWS.get(key)
    if row is None:
        raise CMEEStage1ContractError("stage1_microgrammar_predicate_missing")
    primary, alternate, condition = row
    if not alternate:
        return primary, ""
    if condition == "always":
        return primary, alternate
    if condition == "continuing_only":
        times = tuple(
            _qualifier_value(candidate, "time_scope", role=binding.role)
            if contribution.relation_basis_refs
            else _qualifier_value(candidate, "time_scope")
            for binding in contribution.argument_bindings
            if binding.role is not ArgumentRole.EXPERIENCER
        )
        return (primary, alternate) if times and set(times) == {"continuing"} else (primary, "")
    if condition != "never":
        raise CMEEStage1ContractError("stage1_microgrammar_predicate_condition_invalid")
    return primary, ""


def _subjective_operator_detail(claim: EmlisSubjectiveClaim) -> str:
    proposition = claim.asserted_subjective_proposition
    operator = proposition.subjective_operator
    detail = ""
    if operator is SubjectiveOperator.FEEL_TOWARD:
        if proposition.affect_category is None:
            raise CMEEStage1ContractError("stage1_microgrammar_affect_missing")
        detail = proposition.affect_category.value
    elif operator is SubjectiveOperator.TAKE_RELATIONAL_STANCE:
        if proposition.stance_operator is None:
            raise CMEEStage1ContractError("stage1_microgrammar_stance_missing")
        detail = proposition.stance_operator.value
    return detail


def _subjective_predicate_spec(
    claim: EmlisSubjectiveClaim,
) -> tuple[str, str]:
    proposition = claim.asserted_subjective_proposition
    operator = proposition.subjective_operator
    detail = _subjective_operator_detail(claim)
    row = _SUBJECTIVE_PREDICATE_ROWS.get((operator.value, detail))
    if row is None:
        raise CMEEStage1ContractError("stage1_microgrammar_predicate_missing")
    return row


def _connective_family(
    *,
    layer: str,
    relation_or_operator: str,
    overall_index: int,
    layer_index: Optional[int] = None,
) -> str:
    if overall_index == 0 or (layer == "LAYER_2" and layer_index == 0):
        return "NONE"
    family = _OPERATOR_CONNECTIVES.get((layer, relation_or_operator))
    if family is None:
        raise CMEEStage1ContractError("stage1_microgrammar_connective_missing")
    return family


def _connective_token(family: str, *, alternate: bool) -> str:
    tokens = _CONNECTIVE_FAMILIES.get(family)
    if tokens is None or not tokens or len(tokens) > 2:
        raise CMEEStage1ContractError("stage1_microgrammar_connective_missing")
    if alternate:
        if len(tokens) != 2:
            raise CMEEStage1ContractError("stage1_microgrammar_alternate_missing")
        return tokens[1]
    return tokens[0]


def _subjective_connective_family(
    projection: EmlisStage1Projection,
    claim: EmlisSubjectiveClaim,
    *,
    overall_index: int,
    layer_index: int,
) -> str:
    proposition = claim.asserted_subjective_proposition
    base = _connective_family(
        layer="LAYER_2",
        relation_or_operator=proposition.subjective_operator.value,
        overall_index=overall_index,
        layer_index=layer_index,
    )
    if base == "NONE":
        return base
    contribution_by_id = {
        row.contribution_id: row
        for row in projection.observation_contributions
    }
    overrides = {
        _SUBJECTIVE_BASIS_CONNECTIVES[key]
        for ref in claim.basis_observation_contribution_refs
        if ref in contribution_by_id
        for key in (
            (
                proposition.subjective_operator.value,
                _subjective_operator_detail(claim),
                contribution_by_id[ref].relation_operator.value,
            ),
        )
        if key in _SUBJECTIVE_BASIS_CONNECTIVES
    }
    if len(overrides) > 1:
        raise CMEEStage1ContractError(
            "stage1_microgrammar_connective_ambiguous"
        )
    return next(iter(overrides), base)


def _subjective_semantic_predicate_alternate(
    projection: EmlisStage1Projection,
    claim: EmlisSubjectiveClaim,
    object_ref: str,
) -> bool:
    proposition = claim.asserted_subjective_proposition
    prefix = (
        proposition.subjective_operator.value,
        _subjective_operator_detail(claim),
    )
    if not any(
        row[:2] == prefix
        for row in _SUBJECTIVE_SEMANTIC_PREDICATE_ROTATIONS
    ):
        return False
    key = (
        *prefix,
        _semantic_operator_for_object(projection, object_ref),
        _time_scope_for_semantic_ref(projection, object_ref),
    )
    return key in _SUBJECTIVE_SEMANTIC_PREDICATE_ROTATIONS


def _subjective_semantic_connective_alternate(
    projection: EmlisStage1Projection,
    claim: EmlisSubjectiveClaim,
    object_ref: str,
) -> bool:
    proposition = claim.asserted_subjective_proposition
    prefix = (
        proposition.subjective_operator.value,
        _subjective_operator_detail(claim),
    )
    if not any(
        row[:2] == prefix
        for row in _SUBJECTIVE_SEMANTIC_CONNECTIVE_ROTATIONS
    ):
        return False
    key = (
        *prefix,
        _semantic_operator_for_object(projection, object_ref),
        _time_scope_for_semantic_ref(projection, object_ref),
    )
    return key in _SUBJECTIVE_SEMANTIC_CONNECTIVE_ROTATIONS


def _observation_connective_family(
    projection: EmlisStage1Projection,
    contribution: PlannedObservationContribution,
    *,
    overall_index: int,
) -> str:
    if overall_index == 0:
        return "NONE"
    candidate = _candidate_for_contribution(projection, contribution)
    if (
        candidate.candidate_kind is InterpretationKind.DIRECTION_UNDER_BURDEN
        and contribution.relation_operator is RelationOperator.COEXISTS_WITH
    ):
        return "COADDITIVE"
    if contribution.retention == "OPTIONAL":
        prior_ref = projection.ordered_observation_refs[overall_index - 1]
        prior = next(
            row
            for row in projection.observation_contributions
            if row.contribution_id == prior_ref
        )
        family = _LAYER1_OPTIONAL_CONNECTIVES.get(
            prior.semantic_operator.value
        )
        if family not in _CONNECTIVE_FAMILIES:
            raise CMEEStage1ContractError(
                "stage1_microgrammar_connective_missing"
            )
        return str(family)
    return _connective_family(
        layer="LAYER_1",
        relation_or_operator=contribution.relation_operator.value,
        overall_index=overall_index,
        layer_index=overall_index,
    )


def _variant_delta(
    projection: EmlisStage1Projection,
) -> Optional[tuple[str, str]]:
    for ref in projection.ordered_observation_refs:
        contribution = next(
            row
            for row in projection.observation_contributions
            if row.contribution_id == ref
        )
        _primary, alternate = _observation_predicate_spec(
            projection, contribution
        )
        if alternate:
            return "predicate", ref
    for ref in projection.ordered_subjective_refs:
        claim = next(
            row
            for row in projection.subjective_claims
            if row.subjective_claim_id == ref
        )
        _primary, alternate = _subjective_predicate_spec(claim)
        if alternate:
            return "predicate", ref
    contribution_by_id = {
        row.contribution_id: row for row in projection.observation_contributions
    }
    claim_by_id = {
        row.subjective_claim_id: row for row in projection.subjective_claims
    }
    for index, ref in enumerate(projection.ordered_observation_refs):
        contribution = contribution_by_id[ref]
        family = _observation_connective_family(
            projection,
            contribution,
            overall_index=index,
        )
        if len(_CONNECTIVE_FAMILIES[family]) == 2:
            return "connective", ref
    observation_count = len(projection.ordered_observation_refs)
    for layer_index, ref in enumerate(projection.ordered_subjective_refs):
        claim = claim_by_id[ref]
        family = _subjective_connective_family(
            projection,
            claim,
            overall_index=observation_count + layer_index,
            layer_index=layer_index,
        )
        if len(_CONNECTIVE_FAMILIES[family]) == 2:
            return "connective", ref
    return None


def _move_ref(anchor_ref: str) -> str:
    if type(anchor_ref) is not str or not anchor_ref or "@" in anchor_ref:
        raise CMEEStage1ContractError("stage1_realization_move_anchor_invalid")
    return f"move:{anchor_ref}@{CMEE_STAGE1_MICROGRAMMAR_POLICY_VERSION}"


def _grapheme_clusters(value: str) -> tuple[str, ...]:
    clusters: list[str] = []
    join_next = False
    for char in value:
        is_extension = bool(
            unicodedata.combining(char)
            or "\ufe00" <= char <= "\ufe0f"
            or "\U000e0100" <= char <= "\U000e01ef"
            or join_next
        )
        if is_extension and clusters:
            clusters[-1] += char
        else:
            clusters.append(char)
        join_next = char == "\u200d"
    return tuple(clusters)


def _source_bound_role_surface(
    semantic_ref: str,
    grounded_graph: GroundedMeaningGraph,
    *,
    layer: Optional[str] = None,
) -> str:
    if not semantic_ref.startswith("node:"):
        raise CMEEStage1ContractError("stage1_surface_binding_unavailable")
    node_id = _local_ref(semantic_ref)
    rows = tuple(row for row in grounded_graph.nodes if row.node_id == node_id)
    if len(rows) != 1 or type(rows[0].value) is not str:
        raise CMEEStage1ContractError("stage1_surface_binding_unavailable")
    value = rows[0].value
    if (
        not value
        or value != value.strip()
        or "\n" in value
        or "\r" in value
        or "\x00" in value
    ):
        raise CMEEStage1ContractError("stage1_surface_binding_unavailable")
    clusters = _grapheme_clusters(value)
    if layer not in {None, "LAYER_1", "LAYER_2"}:
        raise CMEEStage1ContractError("stage1_role_anchor_policy_invalid")
    quote_limit = (
        int(
            _QUOTE_POLICY[
                "l1_max_graphemes"
                if layer == "LAYER_1"
                else "l2_max_graphemes"
            ]
        )
        if layer is not None
        else int(_ROLE_ANCHOR_POLICY["max_graphemes"])
    )
    max_graphemes = min(
        int(_ROLE_ANCHOR_POLICY["max_graphemes"]),
        quote_limit,
    )
    if len(clusters) > max_graphemes:
        if (
            _ROLE_ANCHOR_POLICY.get("over_limit_selection")
            != "semantic_boundary_or_stop"
            or _ROLE_ANCHOR_POLICY.get("inserted_token_count") != 0
            or _ROLE_ANCHOR_POLICY.get("full_value_replay_over_limit") is not False
        ):
            raise CMEEStage1ContractError("stage1_role_anchor_policy_invalid")
        raise CMEEStage1ContractError("stage1_surface_binding_unavailable")
    return value


def _surface_parts(
    parts: Sequence[_SurfacePart],
) -> tuple[str, tuple[RealizedSemanticBinding, ...]]:
    text_parts: list[str] = []
    bindings: list[RealizedSemanticBinding] = []
    offset = 0
    for part in parts:
        if type(part) is not _SurfacePart or type(part.text) is not str or not part.text:
            raise CMEEStage1ContractError("stage1_microgrammar_surface_part_invalid")
        start = offset
        offset += len(part.text)
        text_parts.append(part.text)
        for semantic_ref, clause_slot in part.bindings:
            bindings.append(
                RealizedSemanticBinding(
                    semantic_ref=semantic_ref,
                    clause_slot=clause_slot,
                    surface_scalar_start=start,
                    surface_scalar_end=offset,
                    surface_span_sha256=hashlib.sha256(
                        part.text.encode("utf-8")
                    ).hexdigest(),
                )
            )
    return "".join(text_parts), tuple(bindings)


def _part(
    text: str,
    semantic_ref: str,
    clause_slot: str,
    *additional_bindings: tuple[str, str],
) -> _SurfacePart:
    return _SurfacePart(
        text=text,
        bindings=((semantic_ref, clause_slot), *additional_bindings),
    )


def _time_surface_tokens(time_scope: str) -> tuple[str, str]:
    row = _TIME_WRAPPERS.get(time_scope)
    if (
        type(row) is not tuple
        or len(row) != 2
        or any(type(token) is not str or not token for token in row)
    ):
        raise CMEEStage1ContractError("stage1_microgrammar_inflection_missing")
    return row


def _direct_nominalizer(semantic_operator: str, modality: str) -> str:
    rows = _LAYER1_DIRECT_SLOTS.get(semantic_operator)
    token = rows.get(modality) if rows is not None else None
    if type(token) is not str or not token:
        raise CMEEStage1ContractError("stage1_microgrammar_inflection_missing")
    return token


_DIRECT_CONTRAST_CONNECTOR_RE = re.compile(
    _SOURCE_SHAPE_RECOGNIZERS["direct_contrast"]
)
_CONTEXT_DIRECTION_RESIDUE_RE = re.compile(
    _SOURCE_SHAPE_RECOGNIZERS["context_direction_residue"]
)
_OPEN_QUESTION_IN_PROGRESS_RE = re.compile(
    _SOURCE_SHAPE_RECOGNIZERS["open_question"]
)
_COMPOUND_BURDEN_CONTEXT_RE = re.compile(
    _SOURCE_SHAPE_RECOGNIZERS["compound_burden"]
)
_ACTION_CHANGE_CONTEXT_RE = re.compile(
    _SOURCE_SHAPE_RECOGNIZERS["action_change"]
)
_SIMPLE_POSITIVE_CHANGE_RE = re.compile(
    _SOURCE_SHAPE_RECOGNIZERS["simple_positive_change"]
)
_POSITIVE_DESIRE_ROLE_RE = re.compile(
    _SOURCE_SHAPE_RECOGNIZERS["positive_desire"]
)
_HESITATION_ROLE_RE = re.compile(
    _SOURCE_SHAPE_RECOGNIZERS["hesitation"]
)
_BOUNDED_SELF_DENIAL_RE = re.compile(
    _SOURCE_SHAPE_RECOGNIZERS["bounded_self_denial"]
)
_BODY_ADJECTIVE_RE = re.compile(
    _SOURCE_SHAPE_RECOGNIZERS["body_adjective"]
)
_BODY_WEIGHT_RE = re.compile(
    _SOURCE_SHAPE_RECOGNIZERS["body_weight"]
)
_CONTEXT_DE_EPISTEMIC_BURDEN_RE = re.compile(
    _SOURCE_SHAPE_RECOGNIZERS["context_de_epistemic_burden"]
)


def _bounded_source_fragments(
    anchor: str,
    *fragments: str,
) -> Optional[tuple[str, ...]]:
    rows = tuple(fragments)
    if (
        not rows
        or any(
            type(row) is not str
            or not row
            or row not in anchor
            or len(_grapheme_clusters(row))
            > int(_QUOTE_POLICY["l1_max_graphemes"])
            for row in rows
        )
    ):
        return None
    return rows


def _source_direct_contrast_roles(
    anchor: str,
) -> Optional[tuple[tuple[str, str], tuple[str, str]]]:
    matches = tuple(_DIRECT_CONTRAST_CONNECTOR_RE.finditer(anchor))
    if len(matches) != 1:
        return None
    match = matches[0]
    left = anchor[: match.start()].rstrip("、,")
    right = anchor[match.end() :].lstrip("、,")
    if _bounded_source_fragments(anchor, left, right) is None:
        return None
    left_direction = bool(_POSITIVE_DESIRE_ROLE_RE.search(left))
    right_direction = bool(_POSITIVE_DESIRE_ROLE_RE.search(right))
    if left_direction == right_direction:
        return None
    other = right if left_direction else left
    other_kind = (
        "hesitation"
        if _HESITATION_ROLE_RE.search(other)
        else "burden"
    )
    return (
        (left, "direction" if left_direction else other_kind),
        (right, "direction" if right_direction else other_kind),
    )


def _source_context_direction_residue_parts(
    anchor: str,
) -> Optional[tuple[str, str, str]]:
    match = _CONTEXT_DIRECTION_RESIDUE_RE.fullmatch(anchor)
    if match is None:
        return None
    rows = tuple(match.group(name) for name in ("context", "direction", "residue"))
    bounded = _bounded_source_fragments(anchor, *rows)
    return None if bounded is None else (bounded[0], bounded[1], bounded[2])


def _source_open_question_parts(
    anchor: str,
) -> Optional[tuple[str, str]]:
    match = _OPEN_QUESTION_IN_PROGRESS_RE.fullmatch(anchor)
    if match is None:
        return None
    rows = tuple(match.group(name) for name in ("burden", "question"))
    bounded = _bounded_source_fragments(anchor, *rows)
    return None if bounded is None else (bounded[0], bounded[1])


def _source_compound_burden_parts(
    anchor: str,
) -> Optional[tuple[str, str, str]]:
    match = _COMPOUND_BURDEN_CONTEXT_RE.fullmatch(anchor)
    if match is None:
        return None
    rows = tuple(
        match.group(name) for name in ("context", "fatigue", "burden")
    )
    bounded = _bounded_source_fragments(anchor, *rows)
    return (
        None
        if bounded is None
        else (bounded[0], bounded[1], bounded[2])
    )


def _source_action_change_parts(
    anchor: str,
) -> Optional[tuple[str, str, str]]:
    match = _ACTION_CHANGE_CONTEXT_RE.fullmatch(anchor)
    if match is None:
        return None
    action = str(match.group("action") or "")
    for inflection_key in (
        "conditional_tara",
        "conditional_dara",
        "conditional_nara",
    ):
        suffix, replacement = _SOURCE_SHAPE_INFLECTIONS[inflection_key]
        if action.endswith(suffix):
            action = action[: -len(suffix)] + replacement
            break
    rows = (str(match.group("context") or ""), action, str(match.group("result") or ""))
    bounded = _bounded_source_fragments(anchor, *rows)
    return None if bounded is None else (bounded[0], bounded[1], bounded[2])


def _source_simple_change_parts(
    anchor: str,
) -> Optional[tuple[str, str, str]]:
    match = _SIMPLE_POSITIVE_CHANGE_RE.fullmatch(anchor)
    if match is None:
        return None
    context = str(match.group("context") or "")
    result = str(match.group("result") or "")
    bounded = _bounded_source_fragments(anchor, context, result)
    if bounded is None:
        return None
    tail_key = (
        "te_context_tail"
        if match.group("connector")
        == _SOURCE_SHAPE_INFLECTIONS["simple_te"]
        else "de_context_tail"
    )
    return bounded[0], tail_key, bounded[1]


def _source_bounded_self_denial_parts(
    anchor: str,
) -> Optional[tuple[str, str]]:
    match = _BOUNDED_SELF_DENIAL_RE.fullmatch(anchor)
    if match is None:
        return None
    rows = tuple(match.group(name) for name in ("basis", "boundary"))
    bounded = _bounded_source_fragments(anchor, *rows)
    return None if bounded is None else (bounded[0], bounded[1])


def _source_body_burden_parts(
    anchor: str,
) -> Optional[tuple[str, str, str]]:
    matches = tuple(
        (shape, pattern.fullmatch(anchor))
        for shape, pattern in (
            ("body_adjective", _BODY_ADJECTIVE_RE),
            ("body_weight", _BODY_WEIGHT_RE),
        )
    )
    matched = tuple((shape, match) for shape, match in matches if match is not None)
    if len(matched) != 1:
        return None
    shape, match = matched[0]
    rows = tuple(match.group(name) for name in ("topic", "state"))
    bounded = _bounded_source_fragments(anchor, *rows)
    return None if bounded is None else (shape, bounded[0], bounded[1])


def _source_context_de_epistemic_burden_parts(
    anchor: str,
) -> Optional[tuple[str, str]]:
    match = _CONTEXT_DE_EPISTEMIC_BURDEN_RE.fullmatch(anchor)
    if (
        match is None
        or len(_grapheme_clusters(anchor))
        > int(_QUOTE_POLICY["l1_max_graphemes"])
    ):
        return None
    affect = match.group("affect")
    question_span = anchor[: match.start("affect")]
    bounded = _bounded_source_fragments(anchor, question_span, affect)
    return None if bounded is None else (bounded[0], bounded[1])


def _quoted_role_parts(
    *,
    anchor: str,
    semantic_ref: str,
    clause_slot: str,
    anchor_bindings: tuple[tuple[str, str], ...] = (),
) -> tuple[_SurfacePart, ...]:
    return (
        _part(
            _STRUCTURAL_TOKENS["quote_open"],
            semantic_ref,
            f"{clause_slot}:quote_open",
        ),
        _SurfacePart(
            text=anchor,
            bindings=(
                anchor_bindings
                if anchor_bindings
                else ((semantic_ref, f"{clause_slot}:anchor"),)
            ),
        ),
        _part(
            _STRUCTURAL_TOKENS["quote_close"],
            semantic_ref,
            f"{clause_slot}:quote_close",
        ),
    )


def _direct_candidate_for_object(
    projection: EmlisStage1Projection,
    object_ref: str,
) -> EmlisInterpretationCandidate:
    direct = tuple(
        candidate
        for candidate in projection.interpretation_candidates
        if not candidate.relation_basis_refs
        and any(
            binding.semantic_ref == object_ref
            and binding.role is ArgumentRole.PRIMARY
            for binding in candidate.argument_bindings
        )
    )
    if len(direct) != 1:
        raise CMEEStage1ContractError("stage1_surface_binding_unavailable")
    return direct[0]


def _semantic_operator_for_object(
    projection: EmlisStage1Projection,
    object_ref: str,
) -> str:
    return _direct_candidate_for_object(
        projection,
        object_ref,
    ).semantic_operator.value


def _typed_reference_surface(
    rows: Mapping[str, str],
    *,
    operator: str,
    modality: str,
) -> str:
    token = rows.get(f"{operator}:{modality}") or rows.get(f"{operator}:*")
    if type(token) is not str or not token:
        raise CMEEStage1ContractError("stage1_surface_binding_unavailable")
    return token


def _shared_relation_surface_allocation(
    projection: EmlisStage1Projection,
    contribution: PlannedObservationContribution,
    *,
    overall_index: int,
) -> tuple[frozenset[str], frozenset[str]]:
    """Allocate exact endpoint anchors once across one adjacent relation pair.

    A source contrast can canonically own both a TENSION relation and a
    direction-under-burden COEXISTS relation over the same two endpoints.  The
    first move owns both exact endpoint anchors while deferring the direction
    endpoint's continuing qualifier.  The second move refers back to both
    endpoints and realizes that qualifier once.  This keeps both required
    relation moves visible without replaying either complete source
    proposition or its continuing qualifier.
    """

    if (
        not contribution.relation_basis_refs
        or overall_index < 0
        or overall_index >= len(projection.ordered_observation_refs)
        or projection.ordered_observation_refs[overall_index]
        != contribution.contribution_id
    ):
        return frozenset(), frozenset()
    endpoint_refs = frozenset(
        binding.semantic_ref
        for binding in contribution.argument_bindings
        if binding.role is not ArgumentRole.EXPERIENCER
    )
    if len(endpoint_refs) != 2:
        return frozenset(), frozenset()
    contribution_by_id = {
        row.contribution_id: row for row in projection.observation_contributions
    }
    matching = tuple(
        (index, contribution_by_id[ref])
        for index, ref in enumerate(projection.ordered_observation_refs)
        if contribution_by_id[ref].relation_basis_refs
        and frozenset(
            binding.semantic_ref
            for binding in contribution_by_id[ref].argument_bindings
            if binding.role is not ArgumentRole.EXPERIENCER
        )
        == endpoint_refs
    )
    if (
        len(matching) != 2
        or matching[1][0] != matching[0][0] + 1
        or matching[0][1].relation_operator is not RelationOperator.TENSION_WITH
        or matching[1][1].relation_operator is not RelationOperator.COEXISTS_WITH
        or _candidate_for_contribution(projection, matching[0][1]).candidate_kind
        is not InterpretationKind.TENSION
        or _candidate_for_contribution(projection, matching[1][1]).candidate_kind
        is not InterpretationKind.DIRECTION_UNDER_BURDEN
    ):
        return frozenset(), frozenset()
    direction_refs = tuple(
        ref
        for ref in endpoint_refs
        if _direct_candidate_for_object(projection, ref).semantic_operator
        is SemanticOperator.PRESENT_DIRECTION
    )
    burden_refs = tuple(
        ref
        for ref in endpoint_refs
        if _direct_candidate_for_object(projection, ref).semantic_operator
        is SemanticOperator.PRESENT_BURDEN
    )
    if len(direction_refs) != 1 or len(burden_refs) != 1:
        return frozenset(), frozenset()
    if overall_index == matching[0][0]:
        return frozenset(direction_refs), frozenset()
    if overall_index == matching[1][0]:
        return frozenset(), endpoint_refs
    return frozenset(), frozenset()


def _claim_uses_question_head(
    claim: Optional[EmlisSubjectiveClaim],
) -> bool:
    if claim is None:
        return True
    proposition = claim.asserted_subjective_proposition
    return bool(
        proposition.subjective_operator is SubjectiveOperator.ATTEND_TO
        or (
            proposition.subjective_operator
            is SubjectiveOperator.TAKE_RELATIONAL_STANCE
            and proposition.stance_operator
            is StanceOperator.HOLD_UNFINISHED_OPEN
        )
    )


def _anaphoric_surface(
    projection: EmlisStage1Projection,
    object_ref: str,
    grounded_graph: GroundedMeaningGraph,
    *,
    claim: Optional[EmlisSubjectiveClaim] = None,
) -> str:
    candidate = _direct_candidate_for_object(projection, object_ref)
    role_value = _source_bound_role_surface(
        object_ref,
        grounded_graph,
        layer=None,
    )
    override = None
    if (
        candidate.semantic_operator is SemanticOperator.PRESENT_DIRECTION
        and _source_open_question_parts(role_value) is not None
        and _claim_uses_question_head(claim)
    ):
        override = "HEAD:QUESTION"
    elif candidate.semantic_operator is SemanticOperator.PRESENT_DIRECTION:
        contrast = _source_direct_contrast_roles(role_value)
        claim_is_concern = bool(
            claim is not None
            and claim.asserted_subjective_proposition.subjective_operator
            is SubjectiveOperator.FEEL_TOWARD
            and claim.asserted_subjective_proposition.affect_category
            is AffectCategory.CONCERN
        )
        if (
            contrast is not None
            and contrast[1][1] == "hesitation"
            and (claim is None or claim_is_concern)
        ):
            override = "HEAD:HESITATION"
    if override is not None:
        token = _LAYER2_ANAPHORIC_SURFACES.get(override)
        if type(token) is not str or not token:
            raise CMEEStage1ContractError("stage1_surface_binding_unavailable")
        return token
    return _typed_reference_surface(
        _LAYER2_ANAPHORIC_SURFACES,
        operator=candidate.semantic_operator.value,
        modality=_qualifier_value(candidate, "modality"),
    )


def _prior_visible_anaphoric_surface(
    projection: EmlisStage1Projection,
    object_ref: str,
    prior_contributions: tuple[PlannedObservationContribution, ...],
    grounded_graph: GroundedMeaningGraph,
) -> str:
    matching = tuple(
        contribution
        for contribution in prior_contributions
        if any(
            binding.semantic_ref == object_ref
            and binding.role is not ArgumentRole.EXPERIENCER
            for binding in contribution.argument_bindings
        )
    )
    if not matching:
        raise CMEEStage1ContractError("stage1_surface_binding_unavailable")
    prior = matching[-1]
    if not prior.relation_basis_refs:
        return _anaphoric_surface(
            projection,
            object_ref,
            grounded_graph,
        )
    candidate = _candidate_for_contribution(projection, prior)
    binding = next(
        (
            row
            for row in prior.argument_bindings
            if row.semantic_ref == object_ref
            and row.role is not ArgumentRole.EXPERIENCER
        ),
        None,
    )
    if binding is None:
        raise CMEEStage1ContractError("stage1_surface_binding_unavailable")
    modality = _qualifier_value(candidate, "modality", role=binding.role)
    token = _MODALITY_ANAPHORIC_SURFACES.get(modality)
    if type(token) is not str or not token:
        raise CMEEStage1ContractError("stage1_surface_binding_unavailable")
    return token


def _explicit_object_nominalizer(
    projection: EmlisStage1Projection,
    object_ref: str,
    grounded_graph: GroundedMeaningGraph,
    *,
    claim: Optional[EmlisSubjectiveClaim] = None,
) -> str:
    candidate = _direct_candidate_for_object(projection, object_ref)
    role_value = _source_bound_role_surface(
        object_ref,
        grounded_graph,
        layer=None,
    )
    override = None
    if (
        candidate.semantic_operator is SemanticOperator.PRESENT_DIRECTION
        and _source_open_question_parts(role_value) is not None
        and _claim_uses_question_head(claim)
    ):
        override = "HEAD:QUESTION"
    elif candidate.semantic_operator is SemanticOperator.PRESENT_DIRECTION:
        contrast = _source_direct_contrast_roles(role_value)
        claim_is_concern = bool(
            claim is not None
            and claim.asserted_subjective_proposition.subjective_operator
            is SubjectiveOperator.FEEL_TOWARD
            and claim.asserted_subjective_proposition.affect_category
            is AffectCategory.CONCERN
        )
        if (
            contrast is not None
            and contrast[1][1] == "hesitation"
            and (claim is None or claim_is_concern)
        ):
            override = "HEAD:HESITATION"
    if override is not None:
        token = _LAYER2_EXPLICIT_NOMINALIZERS.get(override)
        if type(token) is not str or not token:
            raise CMEEStage1ContractError("stage1_surface_binding_unavailable")
        return token
    return _typed_reference_surface(
        _LAYER2_EXPLICIT_NOMINALIZERS,
        operator=candidate.semantic_operator.value,
        modality=_qualifier_value(candidate, "modality"),
    )


def _observation_surface_contract(
    projection: EmlisStage1Projection,
    contribution: PlannedObservationContribution,
    grounded_graph: GroundedMeaningGraph,
    *,
    overall_index: int,
    composition_variant_id: str,
    alternate_target: Optional[tuple[str, str]],
) -> tuple[
    str,
    tuple[ClauseFrame, ...],
    tuple[_SurfacePart, ...],
]:
    candidate = _candidate_for_contribution(projection, contribution)
    primary_predicate, alternate_predicate = _observation_predicate_spec(
        projection, contribution
    )
    use_alternate_predicate = bool(
        composition_variant_id == _ALTERNATE_VARIANT_ID
        and alternate_target == ("predicate", contribution.contribution_id)
    )
    if use_alternate_predicate and not alternate_predicate:
        raise CMEEStage1ContractError("stage1_microgrammar_alternate_missing")
    predicate = alternate_predicate if use_alternate_predicate else primary_predicate
    connective_family = _observation_connective_family(
        projection,
        contribution,
        overall_index=overall_index,
    )
    connective = _connective_token(
        connective_family,
        alternate=bool(
            composition_variant_id == _ALTERNATE_VARIANT_ID
            and alternate_target == ("connective", contribution.contribution_id)
        ),
    )
    move_ref = _move_ref(contribution.contribution_id)
    predicate_ref = (
        contribution.relation_basis_refs[0]
        if contribution.relation_basis_refs
        else contribution.argument_bindings[0].semantic_ref
    )
    parts: list[_SurfacePart] = []
    if connective:
        parts.append(_part(connective, predicate_ref, "frame:0:connective"))
        parts.append(
            _part(
                _STRUCTURAL_TOKENS["separator"],
                predicate_ref,
                "frame:0:connective_separator",
            )
        )
    frames: list[ClauseFrame] = []

    if not contribution.relation_basis_refs:
        primary_bindings = tuple(
            row
            for row in contribution.argument_bindings
            if row.role is ArgumentRole.PRIMARY
        )
        if len(primary_bindings) != 1:
            raise CMEEStage1ContractError("stage1_microgrammar_case_frame_invalid")
        primary_ref = primary_bindings[0].semantic_ref
        time_scope = _qualifier_value(candidate, "time_scope")
        modality = _qualifier_value(candidate, "modality")
        polarity = _qualifier_value(candidate, "polarity")
        time_adverb, _role_modifier = _time_surface_tokens(time_scope)
        direct_slot = _direct_nominalizer(
            contribution.semantic_operator.value,
            modality,
        )
        anchor_bindings = tuple(
            (
                row.semantic_ref,
                f"frame:0:argument:{row.role.value}",
            )
            for row in contribution.argument_bindings
        )
        role_value = _source_bound_role_surface(
            primary_ref,
            grounded_graph,
            layer=None,
        )
        context_residue = (
            _source_context_direction_residue_parts(role_value)
            if contribution.semantic_operator is SemanticOperator.PRESENT_DIRECTION
            else None
        )
        open_question = (
            _source_open_question_parts(role_value)
            if contribution.semantic_operator is SemanticOperator.PRESENT_DIRECTION
            else None
        )
        compound_burden = (
            _source_compound_burden_parts(role_value)
            if contribution.semantic_operator is SemanticOperator.PRESENT_BURDEN
            else None
        )
        action_change = (
            _source_action_change_parts(role_value)
            if contribution.semantic_operator is SemanticOperator.PRESENT_CHANGE
            else None
        )
        simple_change = (
            _source_simple_change_parts(role_value)
            if contribution.semantic_operator is SemanticOperator.PRESENT_CHANGE
            else None
        )
        bounded_self_denial = (
            _source_bounded_self_denial_parts(role_value)
            if contribution.semantic_operator is SemanticOperator.PRESENT_STATE
            else None
        )
        body_burden = (
            _source_body_burden_parts(role_value)
            if contribution.semantic_operator
            in {
                SemanticOperator.PRESENT_STATE,
                SemanticOperator.PRESENT_BURDEN,
            }
            else None
        )
        direct_contrast = (
            _source_direct_contrast_roles(role_value)
            if contribution.semantic_operator
            in {
                SemanticOperator.PRESENT_DIRECTION,
                SemanticOperator.PRESENT_BURDEN,
            }
            else None
        )
        if direct_contrast is not None:
            expected_second_kind = (
                "direction"
                if contribution.semantic_operator
                is SemanticOperator.PRESENT_DIRECTION
                else "burden"
            )
            if direct_contrast[1][1] not in {
                expected_second_kind,
                *(
                    ("hesitation",)
                    if contribution.semantic_operator
                    is SemanticOperator.PRESENT_DIRECTION
                    else ()
                ),
            }:
                direct_contrast = None

        if context_residue is not None:
            context, direction, residue = context_residue
            parts.append(
                _part(
                    context,
                    primary_ref,
                    "frame:0:argument:PRIMARY:context",
                )
            )
            parts.append(
                _part(
                    _CONTEXT_RESIDUE_SURFACE["context_tail"],
                    primary_ref,
                    "frame:0:context_tail",
                )
            )
            parts.append(
                _part(
                    _STRUCTURAL_TOKENS["separator"],
                    primary_ref,
                    "frame:0:context_separator",
                )
            )
            parts.extend(
                _quoted_role_parts(
                    anchor=direction,
                    semantic_ref=primary_ref,
                    clause_slot="frame:0:argument:PRIMARY:direction",
                    anchor_bindings=anchor_bindings,
                )
            )
            parts.append(
                _part(
                    _CONTEXT_RESIDUE_SURFACE["direction_nominalizer"],
                    primary_ref,
                    "frame:0:direction_case",
                )
            )
            parts.append(
                _part(
                    _STRUCTURAL_TOKENS["separator"],
                    primary_ref,
                    "frame:0:direction_separator",
                )
            )
            parts.append(
                _part(
                    residue,
                    primary_ref,
                    "frame:0:argument:PRIMARY:residue",
                )
            )
            parts.append(
                _part(
                    _CONTEXT_RESIDUE_SURFACE["residue_topic"],
                    primary_ref,
                    "frame:0:residue_topic",
                )
            )
            parts.append(
                _part(
                    _CONTEXT_RESIDUE_SURFACE["predicate"],
                    primary_ref,
                    "frame:0:predicate",
                )
            )
            parts.append(
                _part(
                    _STRUCTURAL_TOKENS["terminal"],
                    primary_ref,
                    "frame:0:terminal",
                )
            )
        elif open_question is not None:
            burden, question = open_question
            parts.append(_part(time_adverb, primary_ref, "frame:0:time"))
            parts.append(
                _part(
                    _STRUCTURAL_TOKENS["separator"],
                    primary_ref,
                    "frame:0:time_separator",
                )
            )
            parts.append(
                _part(
                    burden,
                    primary_ref,
                    "frame:0:argument:PRIMARY:burden",
                )
            )
            parts.append(
                _part(
                    _OPEN_QUESTION_SURFACE["burden_link"],
                    primary_ref,
                    "frame:0:burden_link",
                )
            )
            parts.append(
                _part(
                    _STRUCTURAL_TOKENS["separator"],
                    primary_ref,
                    "frame:0:burden_separator",
                )
            )
            parts.extend(
                _quoted_role_parts(
                    anchor=question,
                    semantic_ref=primary_ref,
                    clause_slot="frame:0:argument:PRIMARY:question",
                    anchor_bindings=anchor_bindings,
                )
            )
            parts.append(
                _part(
                    _OPEN_QUESTION_SURFACE["question_case"],
                    primary_ref,
                    "frame:0:question_case",
                )
            )
            parts.append(
                _part(
                    _OPEN_QUESTION_SURFACE["predicate"],
                    primary_ref,
                    "frame:0:predicate",
                )
            )
            parts.append(
                _part(
                    _STRUCTURAL_TOKENS["terminal"],
                    primary_ref,
                    "frame:0:terminal",
                )
            )
        elif body_burden is not None:
            shape, topic, state = body_burden
            body_direct_slot = (
                _direct_nominalizer(
                    SemanticOperator.PRESENT_STATE.value,
                    "fact",
                )
                if contribution.semantic_operator is SemanticOperator.PRESENT_STATE
                else direct_slot
            )
            parts.append(_part(time_adverb, primary_ref, "frame:0:time"))
            parts.append(
                _part(
                    _STRUCTURAL_TOKENS["separator"],
                    primary_ref,
                    "frame:0:time_separator",
                )
            )
            parts.extend(
                _quoted_role_parts(
                    anchor=topic,
                    semantic_ref=primary_ref,
                    clause_slot="frame:0:argument:PRIMARY:topic",
                    anchor_bindings=anchor_bindings,
                )
            )
            if shape == "body_adjective":
                parts.append(
                    _part(
                        _BODY_BURDEN_SURFACE["topic_possessive"],
                        primary_ref,
                        "frame:0:topic_possessive",
                    )
                )
                parts.append(
                    _part(
                        _BODY_BURDEN_SURFACE["body_adjective_nominal"],
                        primary_ref,
                        "frame:0:state_nominal",
                    )
                )
            elif shape == "body_weight":
                parts.append(
                    _part(
                        _BODY_BURDEN_SURFACE["topic_object"],
                        primary_ref,
                        "frame:0:topic_object",
                    )
                )
                parts.append(
                    _part(
                        state,
                        primary_ref,
                        "frame:0:argument:PRIMARY:state",
                    )
                )
            else:
                raise CMEEStage1ContractError(
                    "stage1_surface_binding_unavailable"
                )
            parts.append(_part(body_direct_slot, primary_ref, "frame:0:case"))
            parts.append(_part(predicate, primary_ref, "frame:0:predicate"))
            parts.append(
                _part(
                    _STRUCTURAL_TOKENS["terminal"],
                    primary_ref,
                    "frame:0:terminal",
                )
            )
        elif compound_burden is not None:
            context, fatigue, burden = compound_burden
            parts.append(
                _part(
                    context,
                    primary_ref,
                    "frame:0:argument:PRIMARY:context",
                )
            )
            parts.append(
                _part(
                    _COMPOUND_BURDEN_SURFACE["context_link"],
                    primary_ref,
                    "frame:0:context_link",
                )
            )
            parts.append(
                _part(
                    _STRUCTURAL_TOKENS["separator"],
                    primary_ref,
                    "frame:0:context_separator",
                )
            )
            parts.append(
                _part(
                    fatigue,
                    primary_ref,
                    "frame:0:argument:PRIMARY:fatigue",
                )
            )
            parts.append(
                _part(
                    _COMPOUND_BURDEN_SURFACE["fatigue_link"],
                    primary_ref,
                    "frame:0:fatigue_link",
                )
            )
            parts.append(
                _part(
                    _STRUCTURAL_TOKENS["separator"],
                    primary_ref,
                    "frame:0:fatigue_separator",
                )
            )
            parts.extend(
                _quoted_role_parts(
                    anchor=burden,
                    semantic_ref=primary_ref,
                    clause_slot="frame:0:argument:PRIMARY:burden",
                    anchor_bindings=anchor_bindings,
                )
            )
            parts.append(_part(direct_slot, primary_ref, "frame:0:case"))
            parts.append(_part(predicate, primary_ref, "frame:0:predicate"))
            parts.append(
                _part(
                    _STRUCTURAL_TOKENS["terminal"],
                    primary_ref,
                    "frame:0:terminal",
                )
            )
        elif action_change is not None:
            context, action, result = action_change
            parts.append(
                _part(
                    context,
                    primary_ref,
                    "frame:0:argument:PRIMARY:context",
                )
            )
            parts.append(
                _part(
                    _ACTION_CHANGE_SURFACE["context_tail"],
                    primary_ref,
                    "frame:0:context_tail",
                )
            )
            parts.append(
                _part(
                    _STRUCTURAL_TOKENS["separator"],
                    primary_ref,
                    "frame:0:context_separator",
                )
            )
            parts.append(
                _part(
                    action,
                    primary_ref,
                    "frame:0:argument:PRIMARY:action",
                )
            )
            parts.append(
                _part(
                    _ACTION_CHANGE_SURFACE["action_tail"],
                    primary_ref,
                    "frame:0:action_tail",
                )
            )
            parts.append(
                _part(
                    _STRUCTURAL_TOKENS["separator"],
                    primary_ref,
                    "frame:0:action_separator",
                )
            )
            parts.append(
                _part(
                    _ACTION_CHANGE_SURFACE["sequence"],
                    primary_ref,
                    "frame:0:sequence",
                )
            )
            parts.append(
                _part(
                    _STRUCTURAL_TOKENS["separator"],
                    primary_ref,
                    "frame:0:sequence_separator",
                )
            )
            parts.extend(
                _quoted_role_parts(
                    anchor=result,
                    semantic_ref=primary_ref,
                    clause_slot="frame:0:argument:PRIMARY:result",
                    anchor_bindings=anchor_bindings,
                )
            )
            parts.append(_part(direct_slot, primary_ref, "frame:0:case"))
            parts.append(_part(predicate, primary_ref, "frame:0:predicate"))
            parts.append(
                _part(
                    _STRUCTURAL_TOKENS["terminal"],
                    primary_ref,
                    "frame:0:terminal",
                )
            )
        elif simple_change is not None:
            context, context_tail_key, result = simple_change
            parts.append(
                _part(
                    context,
                    primary_ref,
                    "frame:0:argument:PRIMARY:context",
                )
            )
            parts.append(
                _part(
                    _SIMPLE_CHANGE_SURFACE[context_tail_key],
                    primary_ref,
                    "frame:0:context_tail",
                )
            )
            parts.append(
                _part(
                    _STRUCTURAL_TOKENS["separator"],
                    primary_ref,
                    "frame:0:context_separator",
                )
            )
            parts.extend(
                _quoted_role_parts(
                    anchor=result,
                    semantic_ref=primary_ref,
                    clause_slot="frame:0:argument:PRIMARY:result",
                    anchor_bindings=anchor_bindings,
                )
            )
            parts.append(_part(direct_slot, primary_ref, "frame:0:case"))
            parts.append(_part(predicate, primary_ref, "frame:0:predicate"))
            parts.append(
                _part(
                    _STRUCTURAL_TOKENS["terminal"],
                    primary_ref,
                    "frame:0:terminal",
                )
            )
        elif bounded_self_denial is not None:
            basis, boundary = bounded_self_denial
            parts.append(_part(time_adverb, primary_ref, "frame:0:time"))
            parts.append(
                _part(
                    _STRUCTURAL_TOKENS["separator"],
                    primary_ref,
                    "frame:0:time_separator",
                )
            )
            parts.extend(
                _quoted_role_parts(
                    anchor=basis,
                    semantic_ref=primary_ref,
                    clause_slot="frame:0:argument:PRIMARY:basis",
                )
            )
            parts.append(
                _part(
                    _BOUNDED_SELF_DENIAL_SURFACE["basis_nominalizer"],
                    primary_ref,
                    "frame:0:basis_nominalizer",
                )
            )
            parts.append(
                _part(
                    _STRUCTURAL_TOKENS["separator"],
                    primary_ref,
                    "frame:0:basis_separator",
                )
            )
            parts.extend(
                _quoted_role_parts(
                    anchor=boundary,
                    semantic_ref=primary_ref,
                    clause_slot="frame:0:argument:PRIMARY:boundary",
                    anchor_bindings=anchor_bindings,
                )
            )
            parts.append(
                _part(
                    _BOUNDED_SELF_DENIAL_SURFACE["boundary_nominalizer"],
                    primary_ref,
                    "frame:0:boundary_nominalizer",
                )
            )
            parts.append(_part(predicate, primary_ref, "frame:0:predicate"))
            parts.append(
                _part(
                    _STRUCTURAL_TOKENS["terminal"],
                    primary_ref,
                    "frame:0:terminal",
                )
            )
        elif direct_contrast is not None:
            parts.append(_part(time_adverb, primary_ref, "frame:0:time"))
            parts.append(
                _part(
                    _STRUCTURAL_TOKENS["separator"],
                    primary_ref,
                    "frame:0:time_separator",
                )
            )
            for role_index, (source_role, role_kind) in enumerate(
                direct_contrast
            ):
                role_bindings = anchor_bindings if role_index == 1 else ()
                parts.extend(
                    _quoted_role_parts(
                        anchor=source_role,
                        semantic_ref=primary_ref,
                        clause_slot=(
                            f"frame:0:argument:PRIMARY:contrast_{role_index}"
                        ),
                        anchor_bindings=role_bindings,
                    )
                )
                parts.append(
                    _part(
                        _DIRECT_CONTRAST_SURFACE[
                            f"{role_kind}_nominalizer"
                        ],
                        primary_ref,
                        f"frame:0:contrast_{role_index}_case",
                    )
                )
                if role_index == 0:
                    parts.append(
                        _part(
                            _DIRECT_CONTRAST_SURFACE["bridge"],
                            primary_ref,
                            "frame:0:contrast_bridge",
                        )
                    )
                    parts.append(
                        _part(
                            _STRUCTURAL_TOKENS["separator"],
                            primary_ref,
                            "frame:0:contrast_separator",
                        )
                    )
                else:
                    parts.append(
                        _part(
                            _DIRECT_CONTRAST_SURFACE["second_topic"],
                            primary_ref,
                            "frame:0:contrast_topic",
                        )
                    )
                    parts.append(
                        _part(
                            predicate,
                            primary_ref,
                            "frame:0:predicate",
                        )
                    )
                    parts.append(
                        _part(
                            _STRUCTURAL_TOKENS["terminal"],
                            primary_ref,
                            "frame:0:terminal",
                        )
                    )
        else:
            anchor = _source_bound_role_surface(
                primary_ref,
                grounded_graph,
                layer="LAYER_1",
            )
            parts.append(_part(time_adverb, primary_ref, "frame:0:time"))
            parts.append(
                _part(
                    _STRUCTURAL_TOKENS["separator"],
                    primary_ref,
                    "frame:0:time_separator",
                )
            )
            parts.extend(
                _quoted_role_parts(
                    anchor=anchor,
                    semantic_ref=primary_ref,
                    clause_slot="frame:0:argument:PRIMARY",
                    anchor_bindings=anchor_bindings,
                )
            )
            parts.append(_part(direct_slot, primary_ref, "frame:0:case"))
            parts.append(_part(predicate, primary_ref, "frame:0:predicate"))
            parts.append(
                _part(
                    _STRUCTURAL_TOKENS["terminal"],
                    primary_ref,
                    "frame:0:terminal",
                )
            )
        experiencers = _ordered(
            row.semantic_ref
            for row in contribution.argument_bindings
            if row.role is ArgumentRole.EXPERIENCER
        )
        frames.append(
            ClauseFrame(
                move_ref=move_ref,
                discourse_relation=connective_family,
                topic_ref=primary_ref,
                predicate_operator=contribution.semantic_operator.value,
                object_ref=primary_ref,
                argument_bindings=contribution.argument_bindings,
                qualifier_refs=candidate.required_qualifiers,
                polarity=polarity,
                modality=modality,
                time_scope=time_scope,
                actor_refs=(),
                experiencer_refs=experiencers,
                addressee_role="NONE",
                epistemic_marker="PROVISIONAL_INTERPRETATION",
                speaker_marker=None,
                connective_requirement=(
                    None if connective_family == "NONE" else connective_family
                ),
                reception_style_policy_ref=projection.reception_style_policy_ref,
                terminal_style="POLITE_DECLARATIVE",
            )
        )
    else:
        slot_rows = _LAYER1_RELATION_SLOTS.get(
            contribution.relation_operator.value
        )
        if slot_rows is None or tuple(row[0] for row in slot_rows) != tuple(
            binding.role.value for binding in contribution.argument_bindings
        ):
            raise CMEEStage1ContractError("stage1_microgrammar_case_frame_invalid")
        relation_rows: list[
            tuple[
                int,
                ArgumentBinding,
                tuple[str, str, str],
                str,
                str,
                str,
                str,
                str,
                str,
            ]
        ] = []
        for frame_index, (binding, slot_row) in enumerate(
            zip(contribution.argument_bindings, slot_rows)
        ):
            _role, prefix, suffix = slot_row
            time_scope = _qualifier_value(
                candidate, "time_scope", role=binding.role
            )
            modality = _qualifier_value(candidate, "modality", role=binding.role)
            polarity = _qualifier_value(candidate, "polarity", role=binding.role)
            modality_wrapper = _MODALITY_WRAPPERS.get(modality)
            time_adverb, role_modifier = _time_surface_tokens(time_scope)
            if type(modality_wrapper) is not str or not modality_wrapper:
                raise CMEEStage1ContractError("stage1_microgrammar_inflection_missing")
            relation_rows.append(
                (
                    frame_index,
                    binding,
                    slot_row,
                    time_scope,
                    modality,
                    polarity,
                    time_adverb,
                    role_modifier,
                    modality_wrapper,
                )
            )

        (
            deferred_qualifier_endpoint_refs,
            allocated_anaphoric_endpoint_refs,
        ) = _shared_relation_surface_allocation(
            projection,
            contribution,
            overall_index=overall_index,
        )

        direction_under_burden = bool(
            candidate.candidate_kind
            is InterpretationKind.DIRECTION_UNDER_BURDEN
            and contribution.relation_operator is RelationOperator.COEXISTS_WITH
        )
        if direction_under_burden:
            by_role = {row[1].role: row for row in relation_rows}
            if set(by_role) != {ArgumentRole.LEFT, ArgumentRole.RIGHT}:
                raise CMEEStage1ContractError(
                    "stage1_microgrammar_case_frame_invalid"
                )
            direction = by_role[ArgumentRole.LEFT]
            burden = by_role[ArgumentRole.RIGHT]
            burden_index, burden_binding = burden[0], burden[1]
            direction_index, direction_binding = direction[0], direction[1]
            contribution_by_id = {
                row.contribution_id: row
                for row in projection.observation_contributions
            }
            prior_contributions = tuple(
                contribution_by_id[ref]
                for ref in projection.ordered_observation_refs[:overall_index]
            )
            prior_semantic_refs = {
                binding.semantic_ref
                for prior_contribution in prior_contributions
                for binding in prior_contribution.argument_bindings
                if binding.role is not ArgumentRole.EXPERIENCER
            }
            use_endpoint_anaphora = {
                burden_binding.semantic_ref,
                direction_binding.semantic_ref,
            }.issubset(prior_semantic_refs)
            allocation_active = bool(
                deferred_qualifier_endpoint_refs
                or allocated_anaphoric_endpoint_refs
            )
            burden_uses_anaphora = bool(
                burden_binding.semantic_ref
                in allocated_anaphoric_endpoint_refs
                or (use_endpoint_anaphora and not allocation_active)
            )
            direction_uses_anaphora = bool(
                direction_binding.semantic_ref
                in allocated_anaphoric_endpoint_refs
                or (use_endpoint_anaphora and not allocation_active)
            )
            if burden_uses_anaphora:
                parts.append(
                    _part(
                        _prior_visible_anaphoric_surface(
                            projection,
                            burden_binding.semantic_ref,
                            prior_contributions,
                            grounded_graph,
                        ),
                        burden_binding.semantic_ref,
                        f"frame:{burden_index}:argument_anaphora",
                    )
                )
            else:
                parts.append(
                    _part(
                        burden[7],
                        burden_binding.semantic_ref,
                        f"frame:{burden_index}:time",
                    )
                )
                parts.extend(
                    _quoted_role_parts(
                        anchor=_source_bound_role_surface(
                            burden_binding.semantic_ref,
                            grounded_graph,
                            layer="LAYER_1",
                        ),
                        semantic_ref=burden_binding.semantic_ref,
                        clause_slot=(
                            f"frame:{burden_index}:argument:"
                            f"{burden_binding.role.value}"
                        ),
                    )
                )
                parts.append(
                    _part(
                        burden[8],
                        burden_binding.semantic_ref,
                        f"frame:{burden_index}:modality",
                    )
                )
            parts.append(
                _part(
                    _DIRECTION_UNDER_BURDEN_SURFACE["burden_link"],
                    burden_binding.semantic_ref,
                    f"frame:{burden_index}:case_suffix",
                )
            )
            parts.append(
                _part(
                    _STRUCTURAL_TOKENS["separator"],
                    burden_binding.semantic_ref,
                    f"frame:{burden_index}:separator",
                )
            )
            if direction_uses_anaphora:
                parts.append(
                    _part(
                        _prior_visible_anaphoric_surface(
                            projection,
                            direction_binding.semantic_ref,
                            prior_contributions,
                            grounded_graph,
                        ),
                        direction_binding.semantic_ref,
                        f"frame:{direction_index}:argument_anaphora",
                    )
                )
            else:
                parts.extend(
                    _quoted_role_parts(
                        anchor=_source_bound_role_surface(
                            direction_binding.semantic_ref,
                            grounded_graph,
                            layer="LAYER_1",
                        ),
                        semantic_ref=direction_binding.semantic_ref,
                        clause_slot=(
                            f"frame:{direction_index}:argument:"
                            f"{direction_binding.role.value}"
                        ),
                    )
                )
                parts.append(
                    _part(
                        direction[8],
                        direction_binding.semantic_ref,
                        f"frame:{direction_index}:modality",
                    )
                )
            parts.append(
                _part(
                    _DIRECTION_UNDER_BURDEN_SURFACE["direction_topic"],
                    direction_binding.semantic_ref,
                    f"frame:{direction_index}:case_suffix",
                )
            )
            parts.append(
                _part(
                    direction[6],
                    direction_binding.semantic_ref,
                    f"frame:{direction_index}:time",
                )
            )
        else:
            surface_relation_rows = relation_rows
            if candidate.candidate_kind in {
                InterpretationKind.COEXISTENCE,
                InterpretationKind.TENSION,
            }:
                node_source_order = {
                    node.node_id: index
                    for index, node in enumerate(grounded_graph.nodes)
                }
                surface_relation_rows = sorted(
                    relation_rows,
                    key=lambda row: node_source_order[
                        _local_ref(row[1].semantic_ref)
                    ],
                )
            for row_index, row in enumerate(surface_relation_rows):
                frame_index, binding, slot_row = row[0], row[1], row[2]
                _role, prefix, suffix = slot_row
                if prefix:
                    parts.append(
                        _part(
                            prefix,
                            binding.semantic_ref,
                            f"frame:{frame_index}:case_prefix",
                        )
                    )
                anchor = _source_bound_role_surface(
                    binding.semantic_ref,
                    grounded_graph,
                    layer="LAYER_1",
                )
                epistemic_burden = (
                    _source_context_de_epistemic_burden_parts(anchor)
                    if _semantic_operator_for_object(
                        projection,
                        binding.semantic_ref,
                    )
                    == SemanticOperator.PRESENT_BURDEN.value
                    else None
                )
                if binding.semantic_ref not in deferred_qualifier_endpoint_refs:
                    parts.append(
                        _part(
                            row[7],
                            binding.semantic_ref,
                            f"frame:{frame_index}:time",
                        )
                    )
                if epistemic_burden is not None:
                    question_span, affect = epistemic_burden
                    parts.extend(
                        _quoted_role_parts(
                            anchor=question_span,
                            semantic_ref=binding.semantic_ref,
                            clause_slot=(
                                f"frame:{frame_index}:argument:"
                                f"{binding.role.value}:"
                                "source_exact_epistemic_question"
                            ),
                        )
                    )
                    parts.append(
                        _part(
                            _EPISTEMIC_BURDEN_SURFACE["question_link"],
                            binding.semantic_ref,
                            f"frame:{frame_index}:question_link",
                        )
                    )
                    parts.append(
                        _part(
                            affect,
                            binding.semantic_ref,
                            f"frame:{frame_index}:argument:"
                            f"{binding.role.value}:affect",
                        )
                    )
                else:
                    parts.extend(
                        _quoted_role_parts(
                            anchor=anchor,
                            semantic_ref=binding.semantic_ref,
                            clause_slot=(
                                f"frame:{frame_index}:argument:"
                                f"{binding.role.value}"
                            ),
                        )
                    )
                    parts.append(
                        _part(
                            row[8],
                            binding.semantic_ref,
                            f"frame:{frame_index}:modality",
                        )
                    )
                if suffix:
                    parts.append(
                        _part(
                            suffix,
                            binding.semantic_ref,
                            f"frame:{frame_index}:case_suffix",
                        )
                    )
                if row_index < len(surface_relation_rows) - 1 and not suffix:
                    parts.append(
                        _part(
                            _STRUCTURAL_TOKENS["separator"],
                            binding.semantic_ref,
                            f"frame:{frame_index}:separator",
                        )
                    )

        for (
            frame_index,
            binding,
            _slot_row,
            time_scope,
            modality,
            polarity,
            _time_adverb,
            _role_modifier,
            _modality_wrapper,
        ) in relation_rows:
            role_prefix = f"{binding.role.value.lower()}_"
            frames.append(
                ClauseFrame(
                    move_ref=move_ref,
                    discourse_relation=connective_family,
                    topic_ref=binding.semantic_ref,
                    predicate_operator=contribution.semantic_operator.value,
                    object_ref=binding.semantic_ref,
                    argument_bindings=(binding,),
                    qualifier_refs=tuple(
                        row
                        for row in candidate.required_qualifiers
                        if row == _PROVISIONAL_QUALIFIER
                        or row.startswith(role_prefix)
                    ),
                    polarity=polarity,
                    modality=modality,
                    time_scope=time_scope,
                    actor_refs=(),
                    experiencer_refs=(),
                    addressee_role="NONE",
                    epistemic_marker="PROVISIONAL_INTERPRETATION",
                    speaker_marker=None,
                    connective_requirement=(
                        connective_family if frame_index == 0 and connective else None
                    ),
                    reception_style_policy_ref=projection.reception_style_policy_ref,
                    terminal_style="POLITE_DECLARATIVE",
                )
            )
        parts.append(
            _part(
                predicate,
                predicate_ref,
                f"frame:{len(frames) - 1}:predicate",
            )
        )
        parts.append(
            _part(
                _STRUCTURAL_TOKENS["terminal"],
                predicate_ref,
                f"frame:{len(frames) - 1}:terminal",
            )
        )
    return move_ref, tuple(frames), tuple(parts)


def _observation_surface_shape(
    projection: EmlisStage1Projection,
    contribution: PlannedObservationContribution,
    grounded_graph: GroundedMeaningGraph,
    *,
    overall_index: int,
    composition_variant_id: str,
    alternate_target: Optional[tuple[str, str]],
) -> tuple[
    str,
    tuple[ClauseFrame, ...],
    str,
    tuple[RealizedSemanticBinding, ...],
]:
    move_ref, frames, parts = _observation_surface_contract(
        projection,
        contribution,
        grounded_graph,
        overall_index=overall_index,
        composition_variant_id=composition_variant_id,
        alternate_target=alternate_target,
    )
    text, bindings = _surface_parts(parts)
    return move_ref, frames, text, bindings


def _subjective_object_ref(
    projection: EmlisStage1Projection,
    claim: EmlisSubjectiveClaim,
) -> str:
    proposition = claim.asserted_subjective_proposition
    source_refs = (
        (proposition.counterposition_target_ref,)
        if proposition.subjective_operator
        is SubjectiveOperator.COUNTER_SPECIFIC_PROMOTION
        else proposition.response_object_refs
    )
    if len(source_refs) != 1 or source_refs[0] is None:
        raise CMEEStage1ContractError("stage1_surface_binding_unavailable")
    ref = str(source_refs[0])
    if ref.startswith("node:"):
        return ref
    contribution = next(
        (
            row
            for row in projection.observation_contributions
            if row.contribution_id == ref
        ),
        None,
    )
    if contribution is None:
        raise CMEEStage1ContractError("stage1_surface_binding_unavailable")
    node_refs = tuple(
        row.semantic_ref
        for row in contribution.argument_bindings
        if row.semantic_ref.startswith("node:")
        and row.role is not ArgumentRole.EXPERIENCER
    )
    if len(node_refs) != 1:
        raise CMEEStage1ContractError("stage1_surface_binding_unavailable")
    return node_refs[0]


def _source_qualifier_for_semantic_ref(
    projection: EmlisStage1Projection,
    semantic_ref: str,
    axis: str,
) -> str:
    values: list[str] = []
    for contribution in projection.observation_contributions:
        candidate = _candidate_for_contribution(projection, contribution)
        for binding in contribution.argument_bindings:
            if binding.semantic_ref != semantic_ref:
                continue
            if not contribution.relation_basis_refs:
                value = _qualifier_value(candidate, axis)
            else:
                value = _qualifier_value(
                    candidate, axis, role=binding.role
                )
            if value not in values:
                values.append(value)
    if len(values) != 1:
        raise CMEEStage1ContractError(
            f"stage1_microgrammar_{axis}_ambiguous"
        )
    return values[0]


def _time_scope_for_semantic_ref(
    projection: EmlisStage1Projection,
    semantic_ref: str,
) -> str:
    return _source_qualifier_for_semantic_ref(
        projection,
        semantic_ref,
        "time_scope",
    )


def _reference_mode_for_claim(
    projection: EmlisStage1Projection,
    claim: EmlisSubjectiveClaim,
    object_ref: str,
    grounded_graph: GroundedMeaningGraph,
    *,
    layer2_index: int,
) -> str:
    proposition = claim.asserted_subjective_proposition
    if (
        proposition.subjective_operator
        is SubjectiveOperator.COUNTER_SPECIFIC_PROMOTION
    ):
        mode = "explicit_emlis_counterposition"
    else:
        prior_claim_refs = set(
            projection.ordered_subjective_refs[:layer2_index]
        )
        prior_same_object = any(
            prior.subjective_claim_id in prior_claim_refs
            and _subjective_object_ref(projection, prior) == object_ref
            for prior in projection.subjective_claims
        )
        contribution_by_id = {
            row.contribution_id: row
            for row in projection.observation_contributions
        }
        prior_layer1_rows = tuple(
            contribution_by_id[ref]
            for ref in projection.ordered_observation_refs
            if any(
                binding.semantic_ref == object_ref
                and binding.role is not ArgumentRole.EXPERIENCER
                for binding in contribution_by_id[ref].argument_bindings
            )
        )
        if not prior_layer1_rows:
            raise CMEEStage1ContractError("stage1_surface_binding_unavailable")
        last_layer1 = prior_layer1_rows[-1]
        selected_object_refs = tuple(
            dict.fromkeys(
                binding.semantic_ref
                for binding in last_layer1.argument_bindings
                if binding.role is not ArgumentRole.EXPERIENCER
                and binding.semantic_ref.startswith("node:")
            )
        )
        target_anaphora = _anaphoric_surface(
            projection,
            object_ref,
            grounded_graph,
            claim=claim,
        )
        ambiguous_anaphora = any(
            ref != object_ref
            and _anaphoric_surface(
                projection,
                ref,
                grounded_graph,
                claim=claim,
            )
            == target_anaphora
            for ref in selected_object_refs
        )
        mode = (
            "anaphoric_first"
            if prior_same_object or not ambiguous_anaphora
            else "short_anchor_if_ambiguous"
        )
    if mode not in _REFERENCE_MODE_POLICY:
        raise CMEEStage1ContractError("stage1_microgrammar_reference_mode_invalid")
    return mode


def _subjective_surface_contract(
    projection: EmlisStage1Projection,
    claim: EmlisSubjectiveClaim,
    grounded_graph: GroundedMeaningGraph,
    *,
    overall_index: int,
    layer2_index: int,
    composition_variant_id: str,
    alternate_target: Optional[tuple[str, str]],
) -> tuple[
    str,
    tuple[ClauseFrame, ...],
    tuple[_SurfacePart, ...],
]:
    proposition = claim.asserted_subjective_proposition
    primary_predicate, alternate_predicate = _subjective_predicate_spec(claim)
    variant_flips_predicate = bool(
        composition_variant_id == _ALTERNATE_VARIANT_ID
        and alternate_target == ("predicate", claim.subjective_claim_id)
    )
    object_ref = _subjective_object_ref(projection, claim)
    semantic_alternate_predicate = _subjective_semantic_predicate_alternate(
        projection,
        claim,
        object_ref,
    )
    use_alternate_predicate = bool(
        semantic_alternate_predicate != variant_flips_predicate
    )
    if use_alternate_predicate and not alternate_predicate:
        raise CMEEStage1ContractError("stage1_microgrammar_alternate_missing")
    predicate = alternate_predicate if use_alternate_predicate else primary_predicate
    connective_family = _subjective_connective_family(
        projection,
        claim,
        overall_index=overall_index,
        layer_index=layer2_index,
    )
    base_connective_family = _connective_family(
        layer="LAYER_2",
        relation_or_operator=proposition.subjective_operator.value,
        overall_index=overall_index,
        layer_index=layer2_index,
    )
    semantic_alternate_connective = bool(
        connective_family == base_connective_family
        and _subjective_semantic_connective_alternate(
            projection,
            claim,
            object_ref,
        )
    )
    variant_flips_connective = bool(
        composition_variant_id == _ALTERNATE_VARIANT_ID
        and alternate_target == ("connective", claim.subjective_claim_id)
    )
    connective = _connective_token(
        connective_family,
        alternate=bool(
            semantic_alternate_connective != variant_flips_connective
        ),
    )
    reference_mode = _reference_mode_for_claim(
        projection,
        claim,
        object_ref,
        grounded_graph,
        layer2_index=layer2_index,
    )
    source_modality = _source_qualifier_for_semantic_ref(
        projection,
        object_ref,
        "modality",
    )
    time_scope = _time_scope_for_semantic_ref(projection, object_ref)
    time_adverb, _role_modifier = _time_surface_tokens(time_scope)
    source_modality_wrapper = _MODALITY_WRAPPERS.get(source_modality)
    claim_modality_wrapper = _MODALITY_WRAPPERS.get(proposition.modality)
    explicit_object_nominalizer = _explicit_object_nominalizer(
        projection,
        object_ref,
        grounded_graph,
        claim=claim,
    )
    if (
        type(source_modality_wrapper) is not str
        or not source_modality_wrapper
        or type(claim_modality_wrapper) is not str
        or not claim_modality_wrapper
    ):
        raise CMEEStage1ContractError("stage1_microgrammar_inflection_missing")
    detail = ""
    if proposition.subjective_operator is SubjectiveOperator.FEEL_TOWARD:
        if proposition.affect_category is None:
            raise CMEEStage1ContractError("stage1_microgrammar_affect_missing")
        detail = f":{proposition.affect_category.value}"
    elif proposition.subjective_operator is SubjectiveOperator.TAKE_RELATIONAL_STANCE:
        if proposition.stance_operator is None:
            raise CMEEStage1ContractError("stage1_microgrammar_stance_missing")
        detail = f":{proposition.stance_operator.value}"
    particle = _LAYER2_CASE_PARTICLES.get(
        f"{proposition.subjective_operator.value}{detail}"
    )
    if particle is None:
        raise CMEEStage1ContractError("stage1_microgrammar_case_frame_invalid")
    if proposition.subjective_operator is SubjectiveOperator.ATTEND_TO:
        attention_key = (
            f"{_semantic_operator_for_object(projection, object_ref)}:"
            f"{time_scope}"
        )
        attention_variants = _ATTENTION_SURFACE_ROWS.get(
            attention_key,
            _ATTENTION_SURFACE_ROWS.get("*:*"),
        )
        if (
            type(attention_variants) is not tuple
            or len(attention_variants) != 2
        ):
            raise CMEEStage1ContractError(
                "stage1_microgrammar_case_frame_invalid"
            )
        particle, predicate = attention_variants[
            1 if use_alternate_predicate else 0
        ]
    if (
        _TOPIC_SPEAKER_POLICY.get("layer2_explicit_speaker_placement")
        != "first_move_and_each_counterposition"
    ):
        raise CMEEStage1ContractError("stage1_microgrammar_speaker_policy_invalid")
    explicit_speaker = bool(
        layer2_index == 0
        or proposition.subjective_operator
        is SubjectiveOperator.COUNTER_SPECIFIC_PROMOTION
    )
    move_ref = _move_ref(claim.subjective_claim_id)
    parts: list[_SurfacePart] = []
    if connective:
        parts.append(_part(connective, object_ref, "frame:0:connective"))
        parts.append(
            _part(
                _STRUCTURAL_TOKENS["separator"],
                object_ref,
                "frame:0:connective_separator",
            )
        )
    if explicit_speaker:
        parts.append(_part(_STRUCTURAL_TOKENS["speaker"], object_ref, "frame:0:speaker"))
        parts.append(
            _part(
                _STRUCTURAL_TOKENS["topic_particle"],
                object_ref,
                "frame:0:speaker_particle",
            )
        )
        parts.append(
            _part(
                _STRUCTURAL_TOKENS["separator"],
                object_ref,
                "frame:0:speaker_separator",
            )
        )
    if reference_mode == "anaphoric_first":
        parts.append(
            _part(
                _anaphoric_surface(
                    projection,
                    object_ref,
                    grounded_graph,
                    claim=claim,
                ),
                object_ref,
                "frame:0:object_anaphora",
            )
        )
    else:
        anchor = _source_bound_role_surface(
            object_ref,
            grounded_graph,
            layer=None,
        )
        reference_anchor = anchor
        if (
            reference_mode == "explicit_emlis_counterposition"
            and proposition.subjective_operator
            is SubjectiveOperator.COUNTER_SPECIFIC_PROMOTION
        ):
            bounded_self_denial = _source_bounded_self_denial_parts(anchor)
            if bounded_self_denial is not None:
                reference_anchor = bounded_self_denial[1]
        if (
            len(_grapheme_clusters(reference_anchor))
            > int(_QUOTE_POLICY["l2_max_graphemes"])
        ):
            raise CMEEStage1ContractError("stage1_surface_binding_unavailable")
        parts.append(_part(time_adverb, object_ref, "frame:0:time"))
        parts.append(
            _part(
                _STRUCTURAL_TOKENS["separator"],
                object_ref,
                "frame:0:time_separator",
            )
        )
        parts.extend(
            _quoted_role_parts(
                anchor=reference_anchor,
                semantic_ref=object_ref,
                clause_slot="frame:0:object",
            )
        )
        parts.append(
            _part(
                explicit_object_nominalizer,
                object_ref,
                "frame:0:object_modality",
            )
        )
    parts.append(_part(particle, object_ref, "frame:0:case"))
    parts.append(_part(predicate, object_ref, "frame:0:predicate"))
    parts.append(_part(_STRUCTURAL_TOKENS["terminal"], object_ref, "frame:0:terminal"))
    frame = ClauseFrame(
        move_ref=move_ref,
        discourse_relation=connective_family,
        topic_ref=object_ref,
        predicate_operator=proposition.subjective_operator.value,
        object_ref=object_ref,
        argument_bindings=(ArgumentBinding(ArgumentRole.PRIMARY, object_ref),),
        qualifier_refs=(
            *claim.value_principle_refs,
            f"reference_mode:{reference_mode}",
        ),
        polarity=proposition.polarity,
        modality=proposition.modality,
        time_scope=time_scope,
        actor_refs=proposition.referenced_actor_refs,
        experiencer_refs=proposition.referenced_experiencer_refs,
        addressee_role=proposition.addressee_role,
        epistemic_marker="REQUEST_LOCAL_SUBJECTIVE",
        speaker_marker="EMLIS" if explicit_speaker else None,
        connective_requirement=(
            None if connective_family == "NONE" else connective_family
        ),
        reception_style_policy_ref=projection.reception_style_policy_ref,
        terminal_style="POLITE_DECLARATIVE",
    )
    return move_ref, (frame,), tuple(parts)


def _subjective_surface_shape(
    projection: EmlisStage1Projection,
    claim: EmlisSubjectiveClaim,
    grounded_graph: GroundedMeaningGraph,
    *,
    overall_index: int,
    layer2_index: int,
    composition_variant_id: str,
    alternate_target: Optional[tuple[str, str]],
) -> tuple[
    str,
    tuple[ClauseFrame, ...],
    str,
    tuple[RealizedSemanticBinding, ...],
]:
    move_ref, frames, parts = _subjective_surface_contract(
        projection,
        claim,
        grounded_graph,
        overall_index=overall_index,
        layer2_index=layer2_index,
        composition_variant_id=composition_variant_id,
        alternate_target=alternate_target,
    )
    text, bindings = _surface_parts(parts)
    return move_ref, frames, text, bindings


def _normalized_surface_digest(text: str) -> str:
    if type(text) is not str or not text:
        raise CMEEStage1ContractError("stage1_realization_surface_empty")
    normalized = "".join(text.split())
    if not normalized:
        raise CMEEStage1ContractError("stage1_realization_surface_empty")
    return hashlib.sha256(normalized.encode("utf-8")).hexdigest()


def _clone_utterance_state(
    state: EmlisUtteranceState,
    **changes: object,
) -> EmlisUtteranceState:
    values: dict[str, object] = {
        "phase": state.phase,
        "realized_observation_contribution_refs": list(
            state.realized_observation_contribution_refs
        ),
        "remaining_required_observation_refs": list(
            state.remaining_required_observation_refs
        ),
        "suppressed_observation_candidate_refs": list(
            state.suppressed_observation_candidate_refs
        ),
        "realized_subjective_claim_refs": list(
            state.realized_subjective_claim_refs
        ),
        "remaining_required_subjective_refs": list(
            state.remaining_required_subjective_refs
        ),
        "suppressed_subjective_claim_refs": list(
            state.suppressed_subjective_claim_refs
        ),
        "last_focus_refs": list(state.last_focus_refs),
        "last_move_kind": state.last_move_kind,
        "realized_semantic_keys": list(state.realized_semantic_keys),
        "normalized_surface_digests": list(state.normalized_surface_digests),
        "layer_sentence_counts": dict(state.layer_sentence_counts),
        "composition_variant_id": state.composition_variant_id,
        "stop_reason": state.stop_reason,
    }
    values.update(changes)
    return EmlisUtteranceState(**values)  # type: ignore[arg-type]


def _validate_utterance_state(
    state: EmlisUtteranceState,
    projection: EmlisStage1Projection,
) -> None:
    if type(state) is not EmlisUtteranceState or type(state.phase) is not UtterancePhase:
        raise CMEEStage1ContractError("stage1_utterance_state_type_invalid")
    list_fields = (
        state.realized_observation_contribution_refs,
        state.remaining_required_observation_refs,
        state.suppressed_observation_candidate_refs,
        state.realized_subjective_claim_refs,
        state.remaining_required_subjective_refs,
        state.suppressed_subjective_claim_refs,
        state.last_focus_refs,
        state.realized_semantic_keys,
        state.normalized_surface_digests,
    )
    if any(type(rows) is not list for rows in list_fields):
        raise CMEEStage1ContractError("stage1_utterance_state_array_invalid")
    if any(
        any(type(ref) is not str or not ref for ref in rows)
        or len(rows) != len(set(rows))
        for rows in list_fields
    ):
        raise CMEEStage1ContractError("stage1_utterance_state_ref_invalid")
    if (
        state.composition_variant_id
        not in {_PRIMARY_VARIANT_ID, _ALTERNATE_VARIANT_ID}
        or type(state.layer_sentence_counts) is not dict
        or set(state.layer_sentence_counts) != {"LAYER_1", "LAYER_2"}
        or any(
            type(value) is not int or value < 0
            for value in state.layer_sentence_counts.values()
        )
    ):
        raise CMEEStage1ContractError("stage1_utterance_state_shape_invalid")
    observation_ids = set(projection.ordered_observation_refs)
    contribution_ids = {
        row.contribution_id for row in projection.observation_contributions
    }
    subjective_ids = set(projection.ordered_subjective_refs)
    candidate_ids = {
        row.candidate_id for row in projection.interpretation_candidates
    }
    realized_observation = set(
        state.realized_observation_contribution_refs
    )
    remaining_observation = set(state.remaining_required_observation_refs)
    realized_subjective = set(state.realized_subjective_claim_refs)
    remaining_subjective = set(state.remaining_required_subjective_refs)
    suppressed_subjective = set(state.suppressed_subjective_claim_refs)
    if (
        observation_ids != contribution_ids
        or not realized_observation.isdisjoint(remaining_observation)
        or realized_observation | remaining_observation != observation_ids
        or not set(state.suppressed_observation_candidate_refs).issubset(
            candidate_ids
        )
        or (realized_observation | remaining_observation)
        & set(state.suppressed_observation_candidate_refs)
        or not realized_subjective.isdisjoint(remaining_subjective)
        or not realized_subjective.isdisjoint(suppressed_subjective)
        or not remaining_subjective.isdisjoint(suppressed_subjective)
        or realized_subjective | remaining_subjective | suppressed_subjective
        != subjective_ids
    ):
        raise CMEEStage1ContractError("stage1_utterance_state_namespace_invalid")
    realized_count = (
        len(state.realized_observation_contribution_refs)
        + len(state.realized_subjective_claim_refs)
    )
    if (
        len(state.realized_semantic_keys) != realized_count
        or len(state.normalized_surface_digests) != realized_count
        or sum(state.layer_sentence_counts.values()) != realized_count
    ):
        raise CMEEStage1ContractError("stage1_utterance_state_count_invalid")
    observation_complete = not remaining_observation
    subjective_started = bool(realized_subjective or suppressed_subjective)
    subjective_complete = not remaining_subjective
    if state.phase is UtterancePhase.L1_ACTIVE:
        phase_valid = bool(
            remaining_observation
            and not subjective_started
            and state.layer_sentence_counts["LAYER_2"] == 0
        )
    elif state.phase is UtterancePhase.L1_COMPLETE:
        phase_valid = bool(
            observation_complete
            and not subjective_started
            and state.layer_sentence_counts["LAYER_2"] == 0
        )
    elif state.phase is UtterancePhase.L2_ACTIVE:
        phase_valid = bool(observation_complete and remaining_subjective)
    elif state.phase in {
        UtterancePhase.CANDIDATE_COMPLETE,
        UtterancePhase.READY_FOR_S9,
    }:
        phase_valid = bool(observation_complete and subjective_complete)
    else:
        phase_valid = state.phase is UtterancePhase.NO_VALID_SURFACE
    focus_universe = contribution_ids | subjective_ids
    if (
        not phase_valid
        or not set(state.last_focus_refs).issubset(focus_universe)
        or type(state.last_move_kind) not in {str, type(None)}
        or bool(state.last_focus_refs) != bool(state.last_move_kind)
    ):
        raise CMEEStage1ContractError("stage1_utterance_state_phase_invalid")
    if state.phase is UtterancePhase.NO_VALID_SURFACE:
        if type(state.stop_reason) is not str or not state.stop_reason:
            raise CMEEStage1ContractError("stage1_utterance_state_stop_reason_missing")
    elif state.stop_reason is not None:
        raise CMEEStage1ContractError("stage1_utterance_state_stop_reason_invalid")


def initialize_emlis_utterance_state(
    projection: EmlisStage1Projection,
    *,
    composition_variant_id: str,
) -> EmlisUtteranceState:
    state = EmlisUtteranceState(
        phase=UtterancePhase.L1_ACTIVE,
        realized_observation_contribution_refs=[],
        remaining_required_observation_refs=list(
            projection.ordered_observation_refs
        ),
        suppressed_observation_candidate_refs=[],
        realized_subjective_claim_refs=[],
        remaining_required_subjective_refs=list(
            projection.ordered_subjective_refs
        ),
        suppressed_subjective_claim_refs=[],
        last_focus_refs=[],
        last_move_kind=None,
        realized_semantic_keys=[],
        normalized_surface_digests=[],
        layer_sentence_counts={"LAYER_1": 0, "LAYER_2": 0},
        composition_variant_id=composition_variant_id,
        stop_reason=None,
    )
    _validate_utterance_state(state, projection)
    return state


def _accept_sentence(
    state: EmlisUtteranceState,
    unit: RealizedSentenceUnit,
    projection: EmlisStage1Projection,
) -> EmlisUtteranceState:
    """Return an atomically advanced state; never mutate ``state`` in place."""

    _validate_utterance_state(state, projection)
    if type(unit) is RealizedSentenceUnit:
        validate_stage1_identity(unit)
    if (
        type(unit) is not RealizedSentenceUnit
        or unit.projection_ref != projection.projection_id
        or unit.composition_variant_id != state.composition_variant_id
        or len(unit.basis_anchor_refs) != 1
        or not unit.clause_frames
    ):
        raise CMEEStage1ContractError("stage1_utterance_state_unit_invalid")
    anchor_ref = unit.basis_anchor_refs[0]
    expected_move_ref = _move_ref(anchor_ref)
    if (
        unit.move_ref != expected_move_ref
        or any(frame.move_ref != expected_move_ref for frame in unit.clause_frames)
    ):
        raise CMEEStage1ContractError("stage1_utterance_state_unit_invalid")
    digest = _normalized_surface_digest(unit.text)
    if digest in state.normalized_surface_digests:
        raise CMEEStage1ContractError("stage1_realization_surface_repetition")
    realized_keys = list(state.realized_semantic_keys)
    surface_digests = [*state.normalized_surface_digests, digest]
    layer_counts = dict(state.layer_sentence_counts)

    if unit.layer == "LAYER_1":
        if state.phase is not UtterancePhase.L1_ACTIVE:
            raise CMEEStage1ContractError("stage1_utterance_state_phase_invalid")
        contribution = next(
            (
                row
                for row in projection.observation_contributions
                if row.contribution_id == anchor_ref
            ),
            None,
        )
        if (
            contribution is None
            or anchor_ref not in state.remaining_required_observation_refs
        ):
            raise CMEEStage1ContractError("stage1_utterance_state_anchor_invalid")
        semantic_key = contribution.canonical_semantic_key
        if semantic_key in realized_keys:
            raise CMEEStage1ContractError("stage1_realization_semantic_repetition")
        selected_candidate_ids = set(contribution.interpretation_candidate_refs)
        suppressed_candidates = [
            *state.suppressed_observation_candidate_refs,
            *(
                row.candidate_id
                for row in projection.interpretation_candidates
                if row.candidate_id not in selected_candidate_ids
                and row.candidate_id
                not in state.suppressed_observation_candidate_refs
                and _semantic_key(row) == semantic_key
            ),
        ]
        realized = [
            *state.realized_observation_contribution_refs,
            anchor_ref,
        ]
        remaining = [
            ref
            for ref in state.remaining_required_observation_refs
            if ref != anchor_ref
        ]
        layer_counts["LAYER_1"] += 1
        advanced = _clone_utterance_state(
            state,
            phase=(
                UtterancePhase.L1_COMPLETE
                if not remaining
                else UtterancePhase.L1_ACTIVE
            ),
            realized_observation_contribution_refs=realized,
            remaining_required_observation_refs=remaining,
            suppressed_observation_candidate_refs=suppressed_candidates,
            last_focus_refs=[anchor_ref],
            last_move_kind=contribution.contribution_kind.value,
            realized_semantic_keys=[*realized_keys, semantic_key],
            normalized_surface_digests=surface_digests,
            layer_sentence_counts=layer_counts,
        )
    elif unit.layer == "LAYER_2":
        if state.phase is not UtterancePhase.L2_ACTIVE:
            raise CMEEStage1ContractError("stage1_utterance_state_phase_invalid")
        claim = next(
            (
                row
                for row in projection.subjective_claims
                if row.subjective_claim_id == anchor_ref
            ),
            None,
        )
        if claim is None or anchor_ref not in state.remaining_required_subjective_refs:
            raise CMEEStage1ContractError("stage1_utterance_state_anchor_invalid")
        semantic_key = stage1_subjective_semantic_key(claim)
        if semantic_key in realized_keys:
            raise CMEEStage1ContractError("stage1_realization_semantic_repetition")
        suppressed_claims = [
            *state.suppressed_subjective_claim_refs,
            *(
                row.subjective_claim_id
                for row in projection.subjective_claims
                if row.subjective_claim_id != anchor_ref
                and row.subjective_claim_id
                not in state.realized_subjective_claim_refs
                and row.subjective_claim_id
                not in state.suppressed_subjective_claim_refs
                and stage1_subjective_semantic_key(row) == semantic_key
            ),
        ]
        realized = [*state.realized_subjective_claim_refs, anchor_ref]
        remaining = [
            ref
            for ref in state.remaining_required_subjective_refs
            if ref != anchor_ref and ref not in set(suppressed_claims)
        ]
        layer_counts["LAYER_2"] += 1
        advanced = _clone_utterance_state(
            state,
            phase=(
                UtterancePhase.CANDIDATE_COMPLETE
                if not remaining
                else UtterancePhase.L2_ACTIVE
            ),
            realized_subjective_claim_refs=realized,
            remaining_required_subjective_refs=remaining,
            suppressed_subjective_claim_refs=suppressed_claims,
            last_focus_refs=[anchor_ref],
            last_move_kind=claim.subjective_mode.value,
            realized_semantic_keys=[*realized_keys, semantic_key],
            normalized_surface_digests=surface_digests,
            layer_sentence_counts=layer_counts,
        )
    else:
        raise CMEEStage1ContractError("stage1_utterance_state_layer_invalid")
    _validate_utterance_state(advanced, projection)
    return advanced


def _begin_layer2(
    state: EmlisUtteranceState,
    projection: EmlisStage1Projection,
) -> EmlisUtteranceState:
    _validate_utterance_state(state, projection)
    if (
        state.phase is not UtterancePhase.L1_COMPLETE
        or state.remaining_required_observation_refs
    ):
        raise CMEEStage1ContractError("stage1_utterance_state_phase_invalid")
    advanced = _clone_utterance_state(
        state,
        phase=UtterancePhase.L2_ACTIVE,
        last_focus_refs=[],
        last_move_kind=None,
    )
    _validate_utterance_state(advanced, projection)
    return advanced


def _ready_for_s9(
    state: EmlisUtteranceState,
    projection: EmlisStage1Projection,
) -> EmlisUtteranceState:
    _validate_utterance_state(state, projection)
    if (
        state.phase is not UtterancePhase.CANDIDATE_COMPLETE
        or state.remaining_required_observation_refs
        or state.remaining_required_subjective_refs
        or len(state.normalized_surface_digests)
        != len(set(state.normalized_surface_digests))
    ):
        raise CMEEStage1ContractError("stage1_realization_candidate_incomplete")
    advanced = _clone_utterance_state(
        state,
        phase=UtterancePhase.READY_FOR_S9,
    )
    _validate_utterance_state(advanced, projection)
    return advanced


def _mark_no_valid_surface(
    state: EmlisUtteranceState,
    projection: EmlisStage1Projection,
    *,
    reason: str,
) -> EmlisUtteranceState:
    _validate_utterance_state(state, projection)
    if type(reason) is not str or not reason:
        raise CMEEStage1ContractError("stage1_utterance_state_stop_reason_missing")
    stopped = _clone_utterance_state(
        state,
        phase=UtterancePhase.NO_VALID_SURFACE,
        stop_reason=reason,
    )
    _validate_utterance_state(stopped, projection)
    return stopped


def _realized_unit(
    *,
    projection: EmlisStage1Projection,
    layer: str,
    anchor_ref: str,
    move_ref: str,
    frames: tuple[ClauseFrame, ...],
    text: str,
    bindings: tuple[RealizedSemanticBinding, ...],
    prior_unit_id: Optional[str],
    composition_variant_id: str,
) -> RealizedSentenceUnit:
    unit = RealizedSentenceUnit(
        unit_id="",
        projection_ref=projection.projection_id,
        layer=layer,
        move_ref=move_ref,
        clause_frames=frames,
        text=text,
        basis_anchor_refs=(anchor_ref,),
        realized_semantic_bindings=bindings,
        discourse_link_to_prior_sentence=prior_unit_id,
        composition_variant_id=composition_variant_id,
    )
    return _identified(unit, "unit_id")


def _realize_stage1_variant(
    projection: EmlisStage1Projection,
    grounded_graph: GroundedMeaningGraph,
    parent_plan: ExperiencePlan,
    *,
    composition_variant_id: str,
    alternate_target: Optional[tuple[str, str]],
) -> tuple[RealizedSentenceUnit, ...]:
    state = initialize_emlis_utterance_state(
        projection,
        composition_variant_id=composition_variant_id,
    )
    units: list[RealizedSentenceUnit] = []
    contribution_by_id = {
        row.contribution_id: row for row in projection.observation_contributions
    }
    claim_by_id = {
        row.subjective_claim_id: row for row in projection.subjective_claims
    }
    for overall_index, anchor_ref in enumerate(
        projection.ordered_observation_refs
    ):
        contribution = contribution_by_id[anchor_ref]
        move_ref, frames, text, bindings = _observation_surface_shape(
            projection,
            contribution,
            grounded_graph,
            overall_index=overall_index,
            composition_variant_id=composition_variant_id,
            alternate_target=alternate_target,
        )
        unit = _realized_unit(
            projection=projection,
            layer="LAYER_1",
            anchor_ref=anchor_ref,
            move_ref=move_ref,
            frames=frames,
            text=text,
            bindings=bindings,
            prior_unit_id=units[-1].unit_id if units else None,
            composition_variant_id=composition_variant_id,
        )
        validate_stage1_sentence_unit(
            unit,
            projection,
            grounded_graph=grounded_graph,
            parent_plan=parent_plan,
            prior_unit_ids=tuple(row.unit_id for row in units),
        )
        state = _accept_sentence(state, unit, projection)
        units.append(unit)
    state = _begin_layer2(state, projection)
    observation_count = len(units)
    for layer2_index, anchor_ref in enumerate(projection.ordered_subjective_refs):
        overall_index = observation_count + layer2_index
        claim = claim_by_id[anchor_ref]
        move_ref, frames, text, bindings = _subjective_surface_shape(
            projection,
            claim,
            grounded_graph,
            overall_index=overall_index,
            layer2_index=layer2_index,
            composition_variant_id=composition_variant_id,
            alternate_target=alternate_target,
        )
        unit = _realized_unit(
            projection=projection,
            layer="LAYER_2",
            anchor_ref=anchor_ref,
            move_ref=move_ref,
            frames=frames,
            text=text,
            bindings=bindings,
            prior_unit_id=units[-1].unit_id if units else None,
            composition_variant_id=composition_variant_id,
        )
        validate_stage1_sentence_unit(
            unit,
            projection,
            grounded_graph=grounded_graph,
            parent_plan=parent_plan,
            prior_unit_ids=tuple(row.unit_id for row in units),
        )
        state = _accept_sentence(state, unit, projection)
        units.append(unit)
    state = _ready_for_s9(state, projection)
    if (
        state.layer_sentence_counts["LAYER_1"]
        != len(projection.ordered_observation_refs)
        or state.layer_sentence_counts["LAYER_2"]
        != len(projection.ordered_subjective_refs)
        or state.phase is not UtterancePhase.READY_FOR_S9
    ):
        raise CMEEStage1ContractError("stage1_realization_candidate_incomplete")
    return tuple(units)


def _validate_candidate_set_envelope(
    candidate_set: RealizationCandidateSet,
    projection: EmlisStage1Projection,
) -> None:
    expected_count = 2 if _variant_delta(projection) is not None else 1
    if (
        type(candidate_set) is not RealizationCandidateSet
        or type(candidate_set.candidates) is not tuple
        or candidate_set.projection_ref != projection.projection_id
        or len(candidate_set.candidates) != expected_count
        or expected_count > int(_VARIANT_POLICY["max_candidates"])
        or any(type(candidate) is not tuple for candidate in candidate_set.candidates)
        or any(
            type(unit) is not RealizedSentenceUnit
            for candidate in candidate_set.candidates
            for unit in candidate
        )
    ):
        raise CMEEStage1ContractError("stage1_realization_candidate_set_invalid")


def build_stage1_realization_candidate_set(
    *,
    projection: EmlisStage1Projection,
    grounded_graph: GroundedMeaningGraph,
    parent_plan: ExperiencePlan,
) -> RealizationCandidateSet:
    """S8: generate the complete bounded primary/alternate set exactly once."""

    _validate_microgrammar_inventory()
    validate_stage1_projection(
        projection,
        grounded_graph=grounded_graph,
        parent_plan=parent_plan,
    )
    if projection.emlis_microgrammar_policy_ref != CMEE_STAGE1_MICROGRAMMAR_POLICY_REF:
        raise CMEEStage1ContractError("stage1_microgrammar_policy_ref_invalid")
    alternate_target = _variant_delta(projection)
    variants = (
        (_PRIMARY_VARIANT_ID, None),
        *(((_ALTERNATE_VARIANT_ID, alternate_target),) if alternate_target else ()),
    )
    candidates: list[tuple[RealizedSentenceUnit, ...]] = []
    for composition_variant_id, target in variants:
        try:
            candidate = _realize_stage1_variant(
                projection,
                grounded_graph,
                parent_plan,
                composition_variant_id=composition_variant_id,
                alternate_target=target,
            )
        except CMEEStage1ContractError:
            _mark_no_valid_surface(
                initialize_emlis_utterance_state(
                    projection,
                    composition_variant_id=composition_variant_id,
                ),
                projection,
                reason="stage1_variant_generation_invalid",
            )
            candidate = ()
        candidates.append(candidate)
    result = RealizationCandidateSet(
        projection_ref=projection.projection_id,
        candidates=tuple(candidates),
    )
    _validate_candidate_set_envelope(result, projection)
    return result


def _candidate_variant_id(
    candidate: tuple[RealizedSentenceUnit, ...],
) -> str:
    if not candidate:
        raise CMEEStage1ContractError("stage1_realization_candidate_empty")
    variants = tuple(row.composition_variant_id for row in candidate)
    if len(set(variants)) != 1:
        raise CMEEStage1ContractError("stage1_realization_variant_mixed")
    return variants[0]


def _validate_surface_partition(unit: RealizedSentenceUnit) -> None:
    ranges = sorted(
        {
            (row.surface_scalar_start, row.surface_scalar_end)
            for row in unit.realized_semantic_bindings
        }
    )
    if not ranges or ranges[0][0] != 0 or ranges[-1][1] != len(unit.text):
        raise CMEEStage1ContractError("stage1_surface_binding_not_exact_cover")
    cursor = 0
    for start, end in ranges:
        if start != cursor or end <= start:
            raise CMEEStage1ContractError("stage1_surface_binding_not_exact_cover")
        cursor = end
    if cursor != len(unit.text):
        raise CMEEStage1ContractError("stage1_surface_binding_not_exact_cover")


def _validate_quote_policy(
    unit: RealizedSentenceUnit,
    grounded_graph: GroundedMeaningGraph,
) -> None:
    """Seal the registered per-sentence quote bounds against realized slots."""

    layer_key = {"LAYER_1": "l1", "LAYER_2": "l2"}.get(unit.layer)
    if layer_key is None:
        raise CMEEStage1ContractError("stage1_realization_quote_policy_invalid")
    quote_open = _STRUCTURAL_TOKENS["quote_open"]
    quote_close = _STRUCTURAL_TOKENS["quote_close"]
    openings = sorted(
        (
            row
            for row in unit.realized_semantic_bindings
            if row.clause_slot.endswith(":quote_open")
        ),
        key=lambda row: (row.surface_scalar_start, row.surface_scalar_end),
    )
    closings = sorted(
        (
            row
            for row in unit.realized_semantic_bindings
            if row.clause_slot.endswith(":quote_close")
        ),
        key=lambda row: (row.surface_scalar_start, row.surface_scalar_end),
    )
    max_count = int(_QUOTE_POLICY[f"{layer_key}_max_per_sentence"])
    max_graphemes = int(_QUOTE_POLICY[f"{layer_key}_max_graphemes"])
    if (
        len(openings) != len(closings)
        or len(openings) > max_count
        or unit.text.count(quote_open) != len(openings)
        or unit.text.count(quote_close) != len(closings)
    ):
        raise CMEEStage1ContractError("stage1_realization_quote_policy_invalid")
    node_values = {
        f"node:{row.node_id}@{CMEE_GROUNDED_GRAPH_SCHEMA_VERSION}": row.value
        for row in grounded_graph.nodes
    }
    previous_close_end = 0
    for opening, closing in zip(openings, closings, strict=True):
        anchor = unit.text[
            opening.surface_scalar_end : closing.surface_scalar_start
        ]
        source_value = node_values.get(opening.semantic_ref)
        anchor_bindings = tuple(
            row
            for row in unit.realized_semantic_bindings
            if row.surface_scalar_start == opening.surface_scalar_end
            and row.surface_scalar_end == closing.surface_scalar_start
        )
        if (
            opening.semantic_ref != closing.semantic_ref
            or opening.surface_scalar_start < previous_close_end
            or unit.text[
                opening.surface_scalar_start : opening.surface_scalar_end
            ]
            != quote_open
            or unit.text[
                closing.surface_scalar_start : closing.surface_scalar_end
            ]
            != quote_close
            or opening.surface_scalar_end > closing.surface_scalar_start
            or type(source_value) is not str
            or not anchor
            or not anchor_bindings
            or not any(
                row.semantic_ref == opening.semantic_ref
                for row in anchor_bindings
            )
            or len(_grapheme_clusters(anchor)) > max_graphemes
            or anchor not in source_value
        ):
            raise CMEEStage1ContractError(
                "stage1_realization_quote_policy_invalid"
            )
        previous_close_end = closing.surface_scalar_end


def _validate_existing_surface_contract(
    unit: RealizedSentenceUnit,
    parts: tuple[_SurfacePart, ...],
) -> None:
    """Validate existing S8 bytes by slot without composing a new surface."""

    if type(parts) is not tuple or not parts:
        raise CMEEStage1ContractError("stage1_realization_inventory_mismatch")
    first_slots = tuple(slot for _ref, slot in parts[0].bindings)
    if (
        any(slot.endswith(":connective") for slot in first_slots)
        and len(parts) > 1
        and parts[1].text.startswith(parts[0].text)
    ):
        raise CMEEStage1ContractError("stage1_realization_connective_collision")
    scalar_offset = 0
    binding_index = 0
    for part in parts:
        if type(part) is not _SurfacePart or type(part.text) is not str or not part.text:
            raise CMEEStage1ContractError("stage1_realization_inventory_mismatch")
        scalar_end = scalar_offset + len(part.text)
        if unit.text[scalar_offset:scalar_end] != part.text:
            raise CMEEStage1ContractError("stage1_realization_inventory_mismatch")
        expected_digest = hashlib.sha256(part.text.encode("utf-8")).hexdigest()
        for semantic_ref, clause_slot in part.bindings:
            if binding_index >= len(unit.realized_semantic_bindings):
                raise CMEEStage1ContractError(
                    "stage1_realization_inventory_mismatch"
                )
            binding = unit.realized_semantic_bindings[binding_index]
            if (
                binding.semantic_ref != semantic_ref
                or binding.clause_slot != clause_slot
                or binding.surface_scalar_start != scalar_offset
                or binding.surface_scalar_end != scalar_end
                or binding.surface_span_sha256 != expected_digest
            ):
                raise CMEEStage1ContractError(
                    "stage1_realization_inventory_mismatch"
                )
            binding_index += 1
        scalar_offset = scalar_end
    if (
        scalar_offset != len(unit.text)
        or binding_index != len(unit.realized_semantic_bindings)
    ):
        raise CMEEStage1ContractError("stage1_realization_inventory_mismatch")


def _validate_realization_candidate(
    candidate: tuple[RealizedSentenceUnit, ...],
    *,
    expected_variant_id: str,
    projection: EmlisStage1Projection,
    grounded_graph: GroundedMeaningGraph,
    parent_plan: ExperiencePlan,
    alternate_target: Optional[tuple[str, str]],
) -> None:
    if type(candidate) is not tuple or not candidate:
        raise CMEEStage1ContractError("stage1_realization_candidate_empty")
    if _candidate_variant_id(candidate) != expected_variant_id:
        raise CMEEStage1ContractError("stage1_realization_variant_invalid")
    if expected_variant_id == _ALTERNATE_VARIANT_ID and alternate_target is None:
        raise CMEEStage1ContractError("stage1_realization_alternate_unavailable")
    expected_anchors = (
        *projection.ordered_observation_refs,
        *projection.ordered_subjective_refs,
    )
    expected_layers = (
        *("LAYER_1" for _ref in projection.ordered_observation_refs),
        *("LAYER_2" for _ref in projection.ordered_subjective_refs),
    )
    actual_anchors = tuple(
        unit.basis_anchor_refs[0]
        if len(unit.basis_anchor_refs) == 1
        else ""
        for unit in candidate
    )
    if (
        len(candidate) != len(expected_anchors)
        or actual_anchors != expected_anchors
        or tuple(unit.layer for unit in candidate) != expected_layers
    ):
        raise CMEEStage1ContractError("stage1_realization_coverage_invalid")
    state = initialize_emlis_utterance_state(
        projection,
        composition_variant_id=expected_variant_id,
    )
    prior_ids: list[str] = []
    contribution_by_id = {
        row.contribution_id: row for row in projection.observation_contributions
    }
    claim_by_id = {
        row.subjective_claim_id: row for row in projection.subjective_claims
    }
    observation_count = len(projection.ordered_observation_refs)
    for index, unit in enumerate(candidate):
        validate_stage1_sentence_unit(
            unit,
            projection,
            grounded_graph=grounded_graph,
            parent_plan=parent_plan,
            prior_unit_ids=tuple(prior_ids),
        )
        anchor_ref = expected_anchors[index]
        if index < observation_count:
            expected_move, expected_frames, expected_parts = (
                _observation_surface_contract(
                    projection,
                    contribution_by_id[anchor_ref],
                    grounded_graph,
                    overall_index=index,
                    composition_variant_id=expected_variant_id,
                    alternate_target=alternate_target,
                )
            )
        else:
            expected_move, expected_frames, expected_parts = (
                _subjective_surface_contract(
                    projection,
                    claim_by_id[anchor_ref],
                    grounded_graph,
                    overall_index=index,
                    layer2_index=index - observation_count,
                    composition_variant_id=expected_variant_id,
                    alternate_target=alternate_target,
                )
            )
        expected_prior = prior_ids[-1] if prior_ids else None
        if (
            unit.projection_ref != projection.projection_id
            or unit.move_ref != expected_move
            or any(frame.move_ref != expected_move for frame in unit.clause_frames)
            or unit.clause_frames != expected_frames
            or unit.discourse_link_to_prior_sentence != expected_prior
        ):
            raise CMEEStage1ContractError("stage1_realization_inventory_mismatch")
        _validate_existing_surface_contract(unit, expected_parts)
        _validate_quote_policy(unit, grounded_graph)
        _validate_surface_partition(unit)
        if index == observation_count:
            state = _begin_layer2(state, projection)
        state = _accept_sentence(state, unit, projection)
        prior_ids.append(unit.unit_id)
    state = _ready_for_s9(state, projection)
    if state.phase is not UtterancePhase.READY_FOR_S9:
        raise CMEEStage1ContractError("stage1_realization_candidate_incomplete")


def select_stage1_realization_candidate(
    candidate_set: RealizationCandidateSet,
    *,
    projection: EmlisStage1Projection,
    grounded_graph: GroundedMeaningGraph,
    parent_plan: ExperiencePlan,
) -> tuple[RealizedSentenceUnit, ...]:
    """S9: reread and select only; this function has no realization call."""

    _validate_microgrammar_inventory()
    validate_stage1_projection(
        projection,
        grounded_graph=grounded_graph,
        parent_plan=parent_plan,
    )
    _validate_candidate_set_envelope(candidate_set, projection)
    alternate_target = _variant_delta(projection)
    valid: list[tuple[RealizedSentenceUnit, ...]] = []
    for index, candidate in enumerate(candidate_set.candidates):
        expected_variant_id = (
            _PRIMARY_VARIANT_ID if index == 0 else _ALTERNATE_VARIANT_ID
        )
        try:
            _validate_realization_candidate(
                candidate,
                expected_variant_id=expected_variant_id,
                projection=projection,
                grounded_graph=grounded_graph,
                parent_plan=parent_plan,
                alternate_target=alternate_target,
            )
        except CMEEStage1ContractError:
            continue
        valid.append(candidate)
    if not valid:
        raise CMEEStage1ContractError("stage1_no_hard_valid_realization")
    return min(valid, key=_candidate_variant_id)


def _validated_reception_adapter_rows(
    *,
    sentence_plan: GroundedSentencePlan,
    surface_result: GroundedSurfaceResult,
    human_reception_surface: GroundedHumanReceptionSurface,
    reception_placements: tuple[SentenceSurfacePlacement, ...],
) -> tuple[
    tuple[
        ReceptionVisibleSegmentBindingV1,
        SentenceSurfacePlacement,
        Mapping[str, Any],
    ],
    ...,
]:
    """Join the request-local Human Reception binding and placement once."""

    failure = "REALIZABLE_RECEPTION_EXPRESSION_VISIBLE_BINDING_GAP"
    if (
        type(human_reception_surface) is not GroundedHumanReceptionSurface
        or type(reception_placements) is not tuple
    ):
        raise CMEEStage1ContractError(failure)
    reception_lines = tuple(
        line
        for line in surface_result.lines
        if line.binding.line_role == "human_follow"
    )
    bindings = human_reception_surface.visible_segment_bindings
    if (
        type(bindings) is not tuple
        or len(reception_lines) != 1
        or not bindings
        or len(bindings) != len(reception_placements)
        or human_reception_surface.recovery_stage
        != sentence_plan.recovery_stage
        or human_reception_surface.text != reception_lines[0].text
        or type(human_reception_surface.expression_refs) is not tuple
        or not human_reception_surface.expression_refs
        or any(
            type(ref) is not str or not ref
            for ref in human_reception_surface.expression_refs
        )
        or len(human_reception_surface.expression_refs)
        != len(set(human_reception_surface.expression_refs))
        or type(human_reception_surface.realized_move_ids) is not tuple
        or not human_reception_surface.realized_move_ids
        or len(human_reception_surface.expression_refs)
        != len(human_reception_surface.realized_move_ids)
        or any(
            type(ref) is not str or not ref
            for ref in human_reception_surface.realized_move_ids
        )
        or len(human_reception_surface.realized_move_ids)
        != len(set(human_reception_surface.realized_move_ids))
        or type(human_reception_surface.realized_clause_move_ids) is not tuple
        or len(human_reception_surface.realized_clause_move_ids)
        != len(bindings)
    ):
        raise CMEEStage1ContractError(failure)

    reception_line = reception_lines[0]
    reception_prefix = f"{RECEPTION_SECTION_LABEL}\n"
    prefix_index = surface_result.text.find(reception_prefix)
    line_body_start = prefix_index + len(reception_prefix)
    if (
        prefix_index < 0
        or surface_result.text.find(reception_prefix, prefix_index + 1) >= 0
        or surface_result.text[
            line_body_start : line_body_start + len(reception_line.text)
        ]
        != reception_line.text
    ):
        raise CMEEStage1ContractError(failure)

    expected_field_order = (
        "semantic_refs",
        "source_evidence_refs",
        "predicate_operator",
        "lexical_heads",
        "topic_ref",
        "object_ref",
        "argument_bindings",
        "qualifier_refs",
        "relation_refs",
        "relation_endpoint_refs",
        "direction_refs",
        "polarity",
        "modality",
        "time_scope",
        "aspect",
        "degree",
        "quantity",
        "scope",
        "actor_refs",
        "subject_refs",
        "experiencer_refs",
        "reference_modes",
        "antecedent_refs",
        "antecedent_conditions",
        "particle_plans",
        "inflection_plans",
        "nominalization_plans",
        "clause_link_plans",
        "meaning_outcome_refs",
        "reception_binding_refs",
        "expression_frames",
    )
    rows: list[
        tuple[
            ReceptionVisibleSegmentBindingV1,
            SentenceSurfacePlacement,
            Mapping[str, Any],
        ]
    ] = []
    prior_local_end = 0
    prior_line_end = 0
    prior_body_end = line_body_start
    seen_binding_refs: set[str] = set()
    for binding, placement in zip(
        bindings,
        reception_placements,
        strict=True,
    ):
        if (
            type(binding) is not ReceptionVisibleSegmentBindingV1
            or type(placement) is not SentenceSurfacePlacement
            or type(binding.binding_ref) is not str
            or not binding.binding_ref
            or binding.binding_ref in seen_binding_refs
            or placement.binding_ref != binding.binding_ref
            or placement.sentence_id != reception_line.sentence_id
            or type(binding.expression_refs) is not tuple
            or not binding.expression_refs
            or any(
                type(ref) is not str or not ref
                for ref in binding.expression_refs
            )
            or len(binding.expression_refs) != len(set(binding.expression_refs))
            or type(binding.move_ids) is not tuple
            or not binding.move_ids
            or len(binding.expression_refs) != len(binding.move_ids)
            or any(type(ref) is not str or not ref for ref in binding.move_ids)
            or len(binding.move_ids) != len(set(binding.move_ids))
            or type(binding.surface_derivation_refs) is not tuple
            or not binding.surface_derivation_refs
            or any(
                type(ref) is not str or not ref
                for ref in binding.surface_derivation_refs
            )
            or len(binding.surface_derivation_refs)
            != len(set(binding.surface_derivation_refs))
            or type(binding.human_reception_local_scalar_start) is not int
            or type(binding.human_reception_local_scalar_end) is not int
            or binding.human_reception_local_scalar_start != prior_local_end
            or not (
                0
                <= binding.human_reception_local_scalar_start
                < binding.human_reception_local_scalar_end
                <= len(human_reception_surface.text)
            )
            or type(placement.line_scalar_start) is not int
            or type(placement.line_scalar_end) is not int
            or type(placement.body_scalar_start) is not int
            or type(placement.body_scalar_end) is not int
            or placement.line_scalar_start != prior_line_end
            or placement.body_scalar_start != prior_body_end
            or not (
                0
                <= placement.line_scalar_start
                < placement.line_scalar_end
                <= len(reception_line.text)
            )
            or not (
                line_body_start
                <= placement.body_scalar_start
                < placement.body_scalar_end
                <= line_body_start + len(reception_line.text)
            )
            or placement.body_scalar_start
            != line_body_start + placement.line_scalar_start
            or placement.body_scalar_end
            != line_body_start + placement.line_scalar_end
            or type(binding.surface_span_sha256) is not str
            or re.fullmatch(
                r"[0-9a-f]{64}",
                binding.surface_span_sha256,
            )
            is None
            or not isinstance(binding.clause_frame_fields, Mapping)
            or tuple(binding.clause_frame_fields) != expected_field_order
        ):
            raise CMEEStage1ContractError(failure)
        try:
            expected_binding_ref = _identify_visible_segment_binding(
                replace(binding, binding_ref="")
            ).binding_ref
        except (AttributeError, TypeError, ValueError):
            raise CMEEStage1ContractError(failure) from None
        if not hmac.compare_digest(
            binding.binding_ref,
            expected_binding_ref,
        ):
            raise CMEEStage1ContractError(failure)

        local_segment = human_reception_surface.text[
            binding.human_reception_local_scalar_start :
            binding.human_reception_local_scalar_end
        ]
        line_segment = reception_line.text[
            placement.line_scalar_start : placement.line_scalar_end
        ]
        body_segment = surface_result.text[
            placement.body_scalar_start : placement.body_scalar_end
        ]
        for segment in (local_segment, line_segment, body_segment):
            if not hmac.compare_digest(
                hashlib.sha256(segment.encode("utf-8")).hexdigest(),
                binding.surface_span_sha256,
            ):
                raise CMEEStage1ContractError(failure)
        fields = binding.clause_frame_fields
        seen_binding_refs.add(binding.binding_ref)
        prior_local_end = binding.human_reception_local_scalar_end
        prior_line_end = placement.line_scalar_end
        prior_body_end = placement.body_scalar_end
        rows.append((binding, placement, fields))

    if (
        prior_local_end != len(human_reception_surface.text)
        or prior_line_end != len(reception_line.text)
        or prior_body_end != line_body_start + len(reception_line.text)
        or tuple(
            expression_ref
            for binding in bindings
            for expression_ref in binding.expression_refs
        )
        != human_reception_surface.expression_refs
        or tuple(
            move_id for binding in bindings for move_id in binding.move_ids
        )
        != human_reception_surface.realized_move_ids
        or tuple(binding.move_ids for binding in bindings)
        != human_reception_surface.realized_clause_move_ids
        or tuple(
            pair
            for binding in bindings
            for pair in zip(
                binding.expression_refs,
                binding.move_ids,
                strict=True,
            )
        )
        != tuple(
            zip(
                human_reception_surface.expression_refs,
                human_reception_surface.realized_move_ids,
                strict=True,
            )
        )
    ):
        raise CMEEStage1ContractError(failure)
    return tuple(rows)


def _adapt_grounded_surface_to_v2_realized_units(
    *,
    source: AdmittedTextSource,
    projection: EmlisStage1Projection,
    grounded_plan: GroundedObservationPlan,
    sentence_plan: GroundedSentencePlan,
    surface_result: GroundedSurfaceResult,
    human_reception_surface: GroundedHumanReceptionSurface,
    reception_placements: tuple[SentenceSurfacePlacement, ...],
    selection_score: tuple[int, int, int, int, int],
    hard_valid_candidate_count: int,
    candidate_set_ref: str,
    grounded_graph: GroundedMeaningGraph,
    parent_plan: ExperiencePlan,
) -> tuple[RealizedSentenceUnit, ...]:
    """Adapt the canonical grounded surface into the CMEE trace envelope."""

    if (
        type(source) is not AdmittedTextSource
        or type(projection) is not EmlisStage1Projection
        or type(grounded_plan) is not GroundedObservationPlan
        or type(sentence_plan) is not GroundedSentencePlan
        or type(surface_result) is not GroundedSurfaceResult
        or type(grounded_graph) is not GroundedMeaningGraph
        or type(parent_plan) is not ExperiencePlan
        or projection.schema_version
        != CMEE_STAGE1_RESPONSE_SCHEMA_VERSION_V2
        or projection.grounded_graph_ref != _graph_ref(grounded_graph)
        or projection.parent_observation_duty_ref
        != parent_plan.observation_duty_id
        or projection.parent_reception_duty_ref
        != parent_plan.reception_duty_id
        or projection.ordered_observation_refs
        != tuple(
            row.contribution_id
            for row in projection.observation_contributions
        )
        or projection.ordered_subjective_refs
        != tuple(row.subjective_claim_id for row in projection.subjective_claims)
        or not projection.observation_contributions
        or not projection.subjective_claims
        or sentence_plan.status != "generated"
        or surface_result.status != "generated"
        or sentence_plan.recovery_stage != surface_result.recovery_stage
        or tuple(row.binding for row in sentence_plan.lines)
        != tuple(row.binding for row in surface_result.lines)
        or type(selection_score) is not tuple
        or len(selection_score) != 5
        or any(type(value) is not int for value in selection_score)
        or type(hard_valid_candidate_count) is not int
        or isinstance(hard_valid_candidate_count, bool)
        or hard_valid_candidate_count < 1
        or type(candidate_set_ref) is not str
        or not candidate_set_ref
    ):
        raise CMEEStage1ContractError(
            "stage1_v2_grounded_surface_adapter_input_invalid"
        )
    try:
        validate_stage1_identity(projection)
        validate_stage1_projection(
            projection,
            grounded_graph=grounded_graph,
            parent_plan=parent_plan,
        )
    except CMEEStage1ContractError:
        raise CMEEStage1ContractError(
            "stage1_v2_grounded_surface_adapter_projection_invalid"
        ) from None

    reception_adapter_rows = _validated_reception_adapter_rows(
        sentence_plan=sentence_plan,
        surface_result=surface_result,
        human_reception_surface=human_reception_surface,
        reception_placements=reception_placements,
    )

    plan_binding = _bind_grounded_plan(
        source,
        grounded_graph,
        grounded_plan,
    )
    node_ref_by_nucleus = {
        nucleus_id: _node_ref(node_id)
        for nucleus_id, node_id in plan_binding.nucleus_to_node.items()
    }
    edge_ref_by_relation = {
        relation_id: _edge_ref(edge_id)
        for relation_id, edge_id in plan_binding.relation_to_edge.items()
    }
    graph_refs = {
        *node_ref_by_nucleus.values(),
        *edge_ref_by_relation.values(),
    }
    contribution_by_ref = {
        row.contribution_id: row
        for row in projection.observation_contributions
    }
    claim_by_ref = {
        row.subjective_claim_id: row
        for row in projection.subjective_claims
    }
    remaining_observation_refs = set(projection.ordered_observation_refs)
    remaining_subjective_refs = set(projection.ordered_subjective_refs)
    base_units: list[RealizedSentenceUnit] = []
    unit_seal_rows: list[
        tuple[tuple[str, ...], tuple[str, ...], tuple[str, ...]]
    ] = []

    for ordinal, line in enumerate(surface_result.lines, start=1):
        layer = (
            "LAYER_2"
            if line.binding.line_role == "human_follow"
            else "LAYER_1"
        )
        line_refs = _ordered(
            (
                *(
                    node_ref_by_nucleus[nucleus_id]
                    for nucleus_id in line.binding.nucleus_ids
                    if nucleus_id in node_ref_by_nucleus
                ),
                *(
                    edge_ref_by_relation[relation_id]
                    for relation_id in line.binding.relation_ids
                    if relation_id in edge_ref_by_relation
                ),
            )
        )
        line_ref_set = set(line_refs)
        if layer == "LAYER_1":
            anchors = tuple(
                ref
                for ref in projection.ordered_observation_refs
                if ref in remaining_observation_refs
                and set(
                    (
                        *contribution_by_ref[ref].semantic_refs,
                        *contribution_by_ref[ref].relation_basis_refs,
                    )
                ) <= line_ref_set
                and bool(
                    set(
                        (
                            *contribution_by_ref[ref].semantic_refs,
                            *contribution_by_ref[ref].relation_basis_refs,
                        )
                    )
                    & line_ref_set
                )
            )
            reachable_refs = _ordered(
                ref
                for anchor in anchors
                for ref in (
                    *contribution_by_ref[anchor].semantic_refs,
                    *contribution_by_ref[anchor].relation_basis_refs,
                )
                if ref in graph_refs
            )
            remaining_observation_refs.difference_update(anchors)
        else:
            anchors = tuple(
                ref
                for ref in projection.ordered_subjective_refs
                if ref in remaining_subjective_refs
            )
            if not any(
                set(claim_by_ref[ref].basis_semantic_refs) & line_ref_set
                for ref in anchors
            ):
                anchors = ()
            reachable_refs = _ordered(
                ref
                for anchor in anchors
                for ref in claim_by_ref[anchor].basis_semantic_refs
                if ref in graph_refs
            )
            remaining_subjective_refs.difference_update(anchors)
        if (
            not anchors
            or not reachable_refs
            or not line_ref_set.issubset(set(reachable_refs))
        ):
            raise CMEEStage1ContractError(
                "stage1_v2_grounded_surface_trace_gap"
            )

        node_refs = tuple(
            ref for ref in reachable_refs if ref.startswith("node:")
        )
        relation_refs = tuple(
            ref for ref in reachable_refs if ref.startswith("edge:")
        )
        move_ref = _move_ref(anchors[0])
        if layer == "LAYER_1":
            argument_rows: list[ArgumentBinding] = []
            seen_argument_rows: set[tuple[ArgumentRole, str]] = set()
            for anchor in anchors:
                for row in contribution_by_ref[anchor].argument_bindings:
                    key = (row.role, row.semantic_ref)
                    if (
                        row.semantic_ref in set(reachable_refs)
                        and key not in seen_argument_rows
                    ):
                        seen_argument_rows.add(key)
                        argument_rows.append(row)
            if not argument_rows and node_refs:
                argument_rows.append(
                    ArgumentBinding(ArgumentRole.PRIMARY, node_refs[0])
                )
            visible_sentences = tuple(
                match.group(0).strip()
                for match in re.finditer(
                    r"[^。！？!?\r\n]+[。！？!?]*",
                    line.text,
                )
                if match.group(0).strip()
            ) or (line.text,)
            predicate_operator = _enum_or_text(
                contribution_by_ref[anchors[0]].semantic_operator
            )
            clause_frames = tuple(
                ClauseFrame(
                    move_ref=move_ref,
                    discourse_relation=(
                        relation_refs[index]
                        if index < len(relation_refs)
                        else f"relation:none:{line.binding.line_role}:{index}"
                    ),
                    topic_ref=node_refs[0] if node_refs else None,
                    predicate_operator=predicate_operator,
                    object_ref=node_refs[1] if len(node_refs) > 1 else None,
                    argument_bindings=tuple(argument_rows),
                    qualifier_refs=(),
                    polarity="source_bounded",
                    modality="source_bounded",
                    time_scope="current_input",
                    actor_refs=(),
                    experiencer_refs=(),
                    addressee_role="NONE",
                    epistemic_marker="source_bounded",
                    speaker_marker=None,
                    connective_requirement=None,
                    reception_style_policy_ref=(
                        projection.reception_style_policy_ref
                    ),
                    terminal_style="declarative",
                )
                for index, _sentence in enumerate(visible_sentences)
            )
            text_digest = hashlib.sha256(
                line.text.encode("utf-8")
            ).hexdigest()
            public_bindings = tuple(
                RealizedSemanticBinding(
                    semantic_ref=ref,
                    clause_slot=f"grounded_surface:{line.binding.line_role}",
                    surface_scalar_start=0,
                    surface_scalar_end=len(line.text),
                    surface_span_sha256=text_digest,
                )
                for ref in reachable_refs
            )
        else:
            failure = "REALIZABLE_RECEPTION_EXPRESSION_VISIBLE_BINDING_GAP"
            clause_frame_rows: list[ClauseFrame] = []
            semantic_binding_rows: list[RealizedSemanticBinding] = []
            bound_semantic_refs: list[str] = []
            for index, (binding, placement, fields) in enumerate(
                reception_adapter_rows
            ):
                semantic_refs = fields["semantic_refs"]
                source_evidence_refs = fields["source_evidence_refs"]
                raw_argument_bindings = fields["argument_bindings"]
                qualifier_refs = fields["qualifier_refs"]
                relation_refs = fields["relation_refs"]
                relation_endpoint_refs = fields["relation_endpoint_refs"]
                direction_refs = fields["direction_refs"]
                actor_refs = fields["actor_refs"]
                subject_refs = fields["subject_refs"]
                experiencer_refs = fields["experiencer_refs"]
                topic_ref = fields["topic_ref"]
                object_ref = fields["object_ref"]
                expression_frames = fields["expression_frames"]
                expression_count = len(binding.expression_refs)
                per_expression_fields = tuple(
                    fields[name]
                    for name in (
                        "predicate_operator",
                        "lexical_heads",
                        "polarity",
                        "modality",
                        "time_scope",
                        "aspect",
                        "degree",
                        "quantity",
                        "scope",
                        "reference_modes",
                        "antecedent_refs",
                        "antecedent_conditions",
                        "particle_plans",
                        "inflection_plans",
                        "nominalization_plans",
                        "clause_link_plans",
                        "meaning_outcome_refs",
                        "reception_binding_refs",
                    )
                )
                if (
                    type(semantic_refs) is not tuple
                    or not semantic_refs
                    or any(
                        type(ref) is not str
                        or not ref
                        or ref not in graph_refs
                        for ref in semantic_refs
                    )
                    or len(semantic_refs) != len(set(semantic_refs))
                    or type(source_evidence_refs) is not tuple
                    or not source_evidence_refs
                    or any(
                        type(ref) is not str or not ref
                        for ref in source_evidence_refs
                    )
                    or len(source_evidence_refs)
                    != len(set(source_evidence_refs))
                    or type(raw_argument_bindings) is not tuple
                    or not raw_argument_bindings
                    or type(qualifier_refs) is not tuple
                    or any(
                        type(ref) is not str or not ref
                        for ref in qualifier_refs
                    )
                    or len(qualifier_refs) != len(set(qualifier_refs))
                    or any(
                        type(values) is not tuple
                        or any(type(ref) is not str or not ref for ref in values)
                        or len(values) != len(set(values))
                        for values in (
                            relation_refs,
                            relation_endpoint_refs,
                            direction_refs,
                            actor_refs,
                            subject_refs,
                            experiencer_refs,
                        )
                    )
                    or not (actor_refs or subject_refs or experiencer_refs)
                    or any(
                        type(ref) is not str
                        or not ref.startswith("node:")
                        or ref not in set(reachable_refs)
                        or ref not in set(semantic_refs)
                        for ref in (
                            *actor_refs,
                            *subject_refs,
                            *experiencer_refs,
                        )
                    )
                    or any(
                        not ref.startswith("edge:")
                        or ref not in set(semantic_refs)
                        or ref not in graph_refs
                        for ref in relation_refs
                    )
                    or any(
                        not ref.startswith(
                            "source-grounded-relation-endpoint:"
                        )
                        or not ref.endswith(
                            "@"
                            + SOURCE_GROUNDED_RECEPTION_EXPRESSION_SCHEMA_VERSION
                        )
                        for ref in relation_endpoint_refs
                    )
                    or any(
                        not ref.startswith("source-grounded-direction:")
                        or not ref.endswith(
                            "@"
                            + SOURCE_GROUNDED_RECEPTION_EXPRESSION_SCHEMA_VERSION
                        )
                        for ref in direction_refs
                    )
                    or type(topic_ref) is not str
                    or topic_ref not in set(reachable_refs)
                    or topic_ref not in set(semantic_refs)
                    or (
                        object_ref is not None
                        and (
                            type(object_ref) is not str
                            or object_ref not in set(reachable_refs)
                            or object_ref not in set(semantic_refs)
                        )
                    )
                    or any(
                        type(values) is not tuple
                        or len(values) != expression_count
                        for values in per_expression_fields
                    )
                    or type(expression_frames) is not tuple
                    or len(expression_frames) != expression_count
                    or any(
                        not ref.endswith(
                            "@"
                            + SOURCE_GROUNDED_RECEPTION_EXPRESSION_SCHEMA_VERSION
                        )
                        for ref in binding.expression_refs
                    )
                ):
                    raise CMEEStage1ContractError(failure)

                argument_bindings: list[ArgumentBinding] = []
                argument_identity_keys: list[tuple[str, str, str | None]] = []
                argument_counts: list[int] = []
                argument_cursor = 0
                for raw_argument in raw_argument_bindings:
                    if type(raw_argument) is not tuple or len(raw_argument) != 12:
                        raise CMEEStage1ContractError(failure)
                    (
                        role_name,
                        semantic_ref,
                        lexical_form,
                        argument_evidence_refs,
                        requirement,
                        omission_permission,
                        zero_condition_refs,
                        omission_condition_refs,
                        case_marker,
                        direction_ref,
                        relation_endpoint_ref,
                        realization,
                    ) = raw_argument
                    if (
                        type(role_name) is not str
                        or role_name not in ArgumentRole.__members__
                        or type(semantic_ref) is not str
                        or semantic_ref not in set(semantic_refs)
                        or type(lexical_form) is not str
                        or not lexical_form
                        or type(argument_evidence_refs) is not tuple
                        or not argument_evidence_refs
                        or any(
                            type(ref) is not str or not ref
                            for ref in argument_evidence_refs
                        )
                        or requirement not in {"REQUIRED", "OPTIONAL"}
                        or omission_permission not in {"FORBIDDEN", "PERMITTED"}
                        or type(zero_condition_refs) is not tuple
                        or type(omission_condition_refs) is not tuple
                        or any(
                            type(ref) is not str or not ref
                            for ref in (
                                *zero_condition_refs,
                                *omission_condition_refs,
                            )
                        )
                        or (
                            case_marker is not None
                            and (type(case_marker) is not str or not case_marker)
                        )
                        or (
                            direction_ref is not None
                            and direction_ref not in set(direction_refs)
                        )
                        or (
                            relation_endpoint_ref is not None
                            and relation_endpoint_ref
                            not in set(relation_endpoint_refs)
                        )
                        or realization not in {"EXPLICIT", "ZERO", "OMITTED"}
                    ):
                        raise CMEEStage1ContractError(failure)
                    argument = ArgumentBinding(
                        ArgumentRole[role_name],
                        semantic_ref,
                    )
                    argument_bindings.append(argument)
                    argument_identity_keys.append(
                        (semantic_ref, role_name, relation_endpoint_ref)
                    )
                if not argument_bindings:
                    raise CMEEStage1ContractError(failure)

                for particle_plan in fields["particle_plans"]:
                    if (
                        type(particle_plan) is not tuple
                        or not particle_plan
                        or any(
                            type(row) is not str or not row
                            for row in particle_plan
                        )
                    ):
                        raise CMEEStage1ContractError(failure)
                    argument_counts.append(len(particle_plan))
                if sum(argument_counts) != len(raw_argument_bindings):
                    raise CMEEStage1ContractError(failure)
                validation_cursor = 0
                for count in argument_counts:
                    frame_arguments = tuple(
                        argument_bindings[
                            validation_cursor : validation_cursor + count
                        ]
                    )
                    validation_cursor += count
                    argument_keys = tuple(
                        argument_identity_keys[
                            validation_cursor - count : validation_cursor
                        ]
                    )
                    if len(argument_keys) != len(set(argument_keys)):
                        raise CMEEStage1ContractError(failure)

                expected_expression_frame_cores = tuple(
                    (
                        binding.expression_refs[frame_index],
                        fields["predicate_operator"][frame_index],
                        fields["lexical_heads"][frame_index],
                        fields["polarity"][frame_index],
                        fields["modality"][frame_index],
                        fields["time_scope"][frame_index],
                        fields["aspect"][frame_index],
                        fields["degree"][frame_index],
                        fields["quantity"][frame_index],
                        fields["scope"][frame_index],
                        fields["reference_modes"][frame_index],
                        fields["antecedent_refs"][frame_index],
                        fields["antecedent_conditions"][frame_index],
                    )
                    for frame_index in range(expression_count)
                )
                if (
                    tuple(
                        frame[:13]
                        if type(frame) is tuple and len(frame) == 14
                        else ()
                        for frame in expression_frames
                    )
                    != expected_expression_frame_cores
                    or any(
                        type(frame) is not tuple
                        or len(frame) != 14
                        or any(
                            type(value) is not str or not value
                            for value in frame[:11]
                        )
                        or type(frame[11]) is not tuple
                        or any(
                            type(ref) is not str or not ref
                            for ref in frame[11]
                        )
                        or (
                            frame[12] is not None
                            and (type(frame[12]) is not str or not frame[12])
                        )
                        or type(frame[13]) is not tuple
                        or len(frame[13]) != 9
                        or type(frame[13][0]) is not str
                        or not frame[13][0]
                        or any(
                            type(values) is not tuple
                            or any(
                                type(ref) is not str or not ref
                                for ref in values
                            )
                            or len(values) != len(set(values))
                            for values in frame[13][1:]
                        )
                        or not frame[13][1]
                        or not (
                            frame[13][6]
                            or frame[13][7]
                            or frame[13][8]
                        )
                        for frame in expression_frames
                    )
                    or tuple(frame[13][0] for frame in expression_frames)
                    != binding.move_ids
                    or _ordered(
                        ref
                        for frame in expression_frames
                        for ref in frame[13][1]
                    )
                    != semantic_refs
                    or _ordered(
                        ref
                        for frame in expression_frames
                        for ref in frame[13][2]
                    )
                    != qualifier_refs
                    or _ordered(
                        ref
                        for frame in expression_frames
                        for ref in frame[13][3]
                    )
                    != relation_refs
                    or _ordered(
                        ref
                        for frame in expression_frames
                        for ref in frame[13][4]
                    )
                    != relation_endpoint_refs
                    or _ordered(
                        ref
                        for frame in expression_frames
                        for ref in frame[13][5]
                    )
                    != direction_refs
                    or _ordered(
                        ref
                        for frame in expression_frames
                        for ref in frame[13][6]
                    )
                    != actor_refs
                    or _ordered(
                        ref
                        for frame in expression_frames
                        for ref in frame[13][7]
                    )
                    != subject_refs
                    or _ordered(
                        ref
                        for frame in expression_frames
                        for ref in frame[13][8]
                    )
                    != experiencer_refs
                    or any(
                        type(plan_rows) is not tuple
                        or not plan_rows
                        or any(
                            type(row) is not str or not row
                            for row in plan_rows
                        )
                        for plan_rows in (
                            *fields["inflection_plans"],
                            *fields["nominalization_plans"],
                            *fields["clause_link_plans"],
                        )
                    )
                ):
                    raise CMEEStage1ContractError(failure)

                for frame_index, expression_frame in enumerate(
                    expression_frames
                ):
                    count = argument_counts[frame_index]
                    frame_arguments = tuple(
                        argument_bindings[
                            argument_cursor : argument_cursor + count
                        ]
                    )
                    frame_raw_arguments = raw_argument_bindings[
                        argument_cursor : argument_cursor + count
                    ]
                    argument_cursor += count
                    local_projection = expression_frame[13]
                    local_move_id = local_projection[0]
                    local_semantic_refs = local_projection[1]
                    local_qualifier_refs = local_projection[2]
                    local_relation_refs = local_projection[3]
                    local_relation_endpoint_refs = local_projection[4]
                    local_direction_refs = local_projection[5]
                    local_actor_refs = local_projection[6]
                    local_subject_refs = local_projection[7]
                    local_experiencer_refs = local_projection[8]
                    frame_argument_semantic_ref_order = _ordered(
                        argument.semantic_ref
                        for argument in frame_arguments
                    )
                    frame_argument_semantic_refs = set(
                        frame_argument_semantic_ref_order
                    )
                    if (
                        _ordered(
                            (
                                *frame_argument_semantic_ref_order,
                                *local_relation_refs,
                            )
                        )
                        != local_semantic_refs
                        or _ordered(
                            raw_argument[10]
                            for raw_argument in frame_raw_arguments
                            if raw_argument[10] is not None
                        )
                        != local_relation_endpoint_refs
                        or _ordered(
                            raw_argument[9]
                            for raw_argument in frame_raw_arguments
                            if raw_argument[9] is not None
                        )
                        != local_direction_refs
                        or any(
                            ref not in frame_argument_semantic_refs
                            or not ref.startswith("node:")
                            or ref not in set(reachable_refs)
                            for ref in (
                                *local_actor_refs,
                                *local_subject_refs,
                                *local_experiencer_refs,
                            )
                        )
                        or any(
                            ref not in local_semantic_refs
                            or not ref.startswith("edge:")
                            or ref not in graph_refs
                            for ref in local_relation_refs
                        )
                        or any(
                            (
                                raw_argument[9] is not None
                                and raw_argument[9]
                                not in local_direction_refs
                            )
                            or (
                                raw_argument[10] is not None
                                and raw_argument[10]
                                not in local_relation_endpoint_refs
                            )
                            for raw_argument in frame_raw_arguments
                        )
                    ):
                        raise CMEEStage1ContractError(failure)
                    frame_topic_ref = next(
                        (
                            ref
                            for ref in local_subject_refs
                            if ref in frame_argument_semantic_refs
                        ),
                        frame_argument_semantic_ref_order[0],
                    )
                    frame_object_ref = next(
                        (
                            ref for ref in frame_argument_semantic_ref_order
                            if ref != frame_topic_ref
                        ),
                        None,
                    )
                    discourse_relation = next(
                        iter(local_relation_refs),
                        (
                            f"relation:none:{line.binding.line_role}:"
                            f"{index}:{frame_index}"
                        ),
                    )
                    clause_frame_rows.append(
                        ClauseFrame(
                            move_ref=move_ref,
                            discourse_relation=discourse_relation,
                            topic_ref=frame_topic_ref,
                            predicate_operator=expression_frame[1],
                            object_ref=frame_object_ref,
                            argument_bindings=frame_arguments,
                            qualifier_refs=_ordered(
                                (
                                    *local_qualifier_refs,
                                    expression_frame[0],
                                    binding.binding_ref,
                                )
                            ),
                            polarity=expression_frame[3],
                            modality=expression_frame[4],
                            time_scope=expression_frame[5],
                            actor_refs=local_actor_refs,
                            experiencer_refs=local_experiencer_refs,
                            addressee_role="USER",
                            epistemic_marker="source_bounded",
                            speaker_marker="EMLIS",
                            connective_requirement=None,
                            reception_style_policy_ref=(
                                projection.reception_style_policy_ref
                            ),
                            terminal_style="declarative",
                        )
                    )
                    publicly_reachable_semantic_refs = tuple(
                        semantic_ref
                        for semantic_ref in local_semantic_refs
                        if semantic_ref in set(reachable_refs)
                    )
                    if not publicly_reachable_semantic_refs:
                        raise CMEEStage1ContractError(failure)
                    bound_semantic_refs.extend(
                        publicly_reachable_semantic_refs
                    )
                    clause_slot = (
                        f"human_reception:{binding.binding_ref}:"
                        f"expression[{expression_frame[0]}]:"
                        f"move[{local_move_id}]"
                    )
                    semantic_binding_rows.extend(
                        RealizedSemanticBinding(
                            semantic_ref=semantic_ref,
                            clause_slot=clause_slot,
                            surface_scalar_start=placement.line_scalar_start,
                            surface_scalar_end=placement.line_scalar_end,
                            surface_span_sha256=binding.surface_span_sha256,
                        )
                        for semantic_ref in publicly_reachable_semantic_refs
                    )
                if argument_cursor != len(argument_bindings):
                    raise CMEEStage1ContractError(failure)
            if (
                not line_ref_set.issubset(set(bound_semantic_refs))
                or not set(bound_semantic_refs).issubset(set(reachable_refs))
            ):
                raise CMEEStage1ContractError(failure)
            clause_frames = tuple(clause_frame_rows)
            public_bindings = tuple(semantic_binding_rows)
        unit = _identified(
            RealizedSentenceUnit(
                unit_id="",
                projection_ref=projection.projection_id,
                layer=layer,
                move_ref=move_ref,
                clause_frames=clause_frames,
                text=line.text,
                basis_anchor_refs=anchors,
                realized_semantic_bindings=public_bindings,
                discourse_link_to_prior_sentence=(
                    base_units[-1].unit_id if base_units else None
                ),
                composition_variant_id=(
                    f"grounded-surface-{sentence_plan.recovery_stage}"
                ),
            ),
            "unit_id",
        )
        source_reception_act_refs = (
            _ordered(
                ref
                for anchor in anchors
                for ref in claim_by_ref[anchor].source_reception_act_refs
            )
            if layer == "LAYER_2"
            else ()
        )
        unit_seal_rows.append(
            (
                (f"duty:grounded-surface:{layer.lower()}:{ordinal}",),
                (
                    f"job:grounded-surface:{line.binding.line_role}",
                    f"hard-valid-candidate-count:{hard_valid_candidate_count}",
                    "selection-score:"
                    + ".".join(str(value) for value in selection_score),
                ),
                source_reception_act_refs,
            )
        )
        base_units.append(unit)

    if remaining_observation_refs or remaining_subjective_refs:
        raise CMEEStage1ContractError(
            "stage1_v2_grounded_surface_trace_incomplete"
        )
    selection_material = (
        stage1_projection_artifact_ref(projection),
        candidate_set_ref,
        hard_valid_candidate_count,
        selection_score,
        grounded_plan.schema_version,
        grounded_plan.generation_path,
        sentence_plan.schema_version,
        sentence_plan.generation_path,
        sentence_plan.recovery_stage,
        surface_result.schema_version,
        surface_result.generation_path,
        tuple(
            (
                unit.unit_id,
                unit.layer,
                unit.basis_anchor_refs,
                hashlib.sha256(unit.text.encode("utf-8")).hexdigest(),
            )
            for unit in base_units
        ),
    )
    selection_digest = hashlib.sha256(
        b"cocolon.emlis.grounded_surface.selection.v1\0"
        + stage1_canonical_json_bytes(selection_material)
    ).hexdigest()
    sealed_units = tuple(
        replace(
            unit,
            v2_trace_seal=Stage1V2UnitSeal(
                covered_duty_refs=duty_refs,
                sentence_job_refs=job_refs,
                source_reception_act_refs=source_act_refs,
                composition_candidate_ref=candidate_set_ref,
                composition_layout_ref=(
                    f"grounded-surface-selection-{selection_digest}"
                ),
                selected_stage1_artifact_ref=(
                    f"selected-grounded-surface-{selection_digest}"
                ),
            ),
        )
        for unit, (duty_refs, job_refs, source_act_refs) in zip(
            base_units,
            unit_seal_rows,
            strict=True,
        )
    )
    prior_unit_ids: list[str] = []
    for unit in sealed_units:
        validate_stage1_identity(unit)
        validate_stage1_sentence_unit(
            unit,
            projection,
            grounded_graph=grounded_graph,
            parent_plan=parent_plan,
            prior_unit_ids=tuple(prior_unit_ids),
        )
        prior_unit_ids.append(unit.unit_id)
    return sealed_units


def _inherit_projection_observation_coverage(
    *,
    source: AdmittedTextSource,
    grounded_graph: GroundedMeaningGraph,
    grounded_plan: GroundedObservationPlan,
    projection: EmlisStage1Projection,
) -> GroundedObservationPlan:
    """Bind selected Layer 1 meaning into the existing final-plan owner."""

    if (
        type(source) is not AdmittedTextSource
        or type(grounded_graph) is not GroundedMeaningGraph
        or type(grounded_plan) is not GroundedObservationPlan
        or type(projection) is not EmlisStage1Projection
        or projection.grounded_graph_ref != _graph_ref(grounded_graph)
        or not projection.observation_contributions
    ):
        raise CMEEStage1ContractError(
            "stage1_v2_grounded_surface_projection_coverage_invalid"
        )
    binding = _bind_grounded_plan(
        source,
        grounded_graph,
        grounded_plan,
    )
    nucleus_id_by_graph_ref = {
        _node_ref(node_id): nucleus_id
        for nucleus_id, node_id in binding.nucleus_to_node.items()
    }
    relation_id_by_graph_ref = {
        _edge_ref(edge_id): relation_id
        for relation_id, edge_id in binding.relation_to_edge.items()
    }
    selected_nucleus_ids: list[str] = []
    selected_relation_ids: list[str] = []
    for contribution in projection.observation_contributions:
        if (
            type(contribution) is not PlannedObservationContribution
            or type(contribution.semantic_refs) is not tuple
            or not contribution.semantic_refs
            or type(contribution.relation_basis_refs) is not tuple
        ):
            raise CMEEStage1ContractError(
                "stage1_v2_grounded_surface_projection_coverage_invalid"
            )
        for graph_ref in contribution.semantic_refs:
            if graph_ref in nucleus_id_by_graph_ref:
                selected_nucleus_ids.append(
                    nucleus_id_by_graph_ref[graph_ref]
                )
            elif graph_ref in relation_id_by_graph_ref:
                selected_relation_ids.append(
                    relation_id_by_graph_ref[graph_ref]
                )
            else:
                raise CMEEStage1ContractError(
                    "stage1_v2_grounded_surface_projection_coverage_unmapped"
                )
        for graph_ref in contribution.relation_basis_refs:
            if graph_ref not in relation_id_by_graph_ref:
                raise CMEEStage1ContractError(
                    "stage1_v2_grounded_surface_projection_coverage_unmapped"
                )
            selected_relation_ids.append(
                relation_id_by_graph_ref[graph_ref]
            )

    coverage = grounded_plan.coverage_requirements
    response_plan = grounded_plan.response_plan
    selected_nucleus_id_set = set(selected_nucleus_ids)
    selected_relation_id_set = set(selected_relation_ids)
    if (
        not set(coverage.required_nucleus_ids).issubset(
            selected_nucleus_id_set
        )
        or not set(coverage.required_relation_ids).issubset(
            selected_relation_id_set
        )
    ):
        raise CMEEStage1ContractError(
            "stage1_v2_grounded_surface_required_coverage_unselected"
        )
    required_nucleus_ids = _ordered(
        (*coverage.required_nucleus_ids, *selected_nucleus_ids)
    )
    required_relation_ids = _ordered(
        (*coverage.required_relation_ids, *selected_relation_ids)
    )
    response_required_nucleus_ids = _ordered(
        (*response_plan.required_nucleus_ids, *selected_nucleus_ids)
    )
    response_relation_ids = _ordered(
        (*response_plan.relation_ids, *selected_relation_ids)
    )
    promoted_nucleus_ids = set(response_required_nucleus_ids)
    return replace(
        grounded_plan,
        nuclei=tuple(
            replace(nucleus, retention="optional")
            if (
                nucleus.nucleus_id not in selected_nucleus_id_set
                and nucleus.retention == "should"
            )
            else nucleus
            for nucleus in grounded_plan.nuclei
        ),
        response_plan=replace(
            response_plan,
            required_nucleus_ids=response_required_nucleus_ids,
            optional_nucleus_ids=tuple(
                nucleus_id
                for nucleus_id in response_plan.optional_nucleus_ids
                if nucleus_id not in promoted_nucleus_ids
            ),
            relation_ids=response_relation_ids,
        ),
        coverage_requirements=replace(
            coverage,
            required_nucleus_ids=required_nucleus_ids,
            required_relation_ids=required_relation_ids,
        ),
    )


def _grounded_surface_projection_trace_closed(
    *,
    source: AdmittedTextSource,
    grounded_graph: GroundedMeaningGraph,
    grounded_plan: GroundedObservationPlan,
    projection: EmlisStage1Projection,
    surface_result: GroundedSurfaceResult,
) -> bool:
    """Admit only final-owner candidates whose line refs stay selected."""

    if type(surface_result) is not GroundedSurfaceResult:
        raise CMEEStage1ContractError(
            "stage1_v2_grounded_surface_projection_trace_invalid"
        )
    binding = _bind_grounded_plan(
        source,
        grounded_graph,
        grounded_plan,
    )
    node_ref_by_nucleus_id = {
        nucleus_id: _node_ref(node_id)
        for nucleus_id, node_id in binding.nucleus_to_node.items()
    }
    edge_ref_by_relation_id = {
        relation_id: _edge_ref(edge_id)
        for relation_id, edge_id in binding.relation_to_edge.items()
    }
    observation_refs = {
        ref
        for contribution in projection.observation_contributions
        for ref in (
            *contribution.semantic_refs,
            *contribution.relation_basis_refs,
        )
    }
    subjective_refs = {
        ref
        for claim in projection.subjective_claims
        for ref in claim.basis_semantic_refs
    }
    for line in surface_result.lines:
        try:
            line_refs = {
                *(
                    node_ref_by_nucleus_id[nucleus_id]
                    for nucleus_id in line.binding.nucleus_ids
                ),
                *(
                    edge_ref_by_relation_id[relation_id]
                    for relation_id in line.binding.relation_ids
                ),
            }
        except KeyError:
            return False
        allowed_refs = (
            subjective_refs
            if line.binding.line_role == "human_follow"
            else observation_refs
        )
        if not line_refs or not line_refs.issubset(allowed_refs):
            return False
    return True


_REALIZABLE_RECEPTION_ENDPOINT_ROLES = frozenset(
    {"LEFT", "RIGHT", "BEFORE", "AFTER", "ACTION", "CHANGE", "CAUSE", "EFFECT"}
)
_REALIZABLE_RECEPTION_NAMED_FAILURES = frozenset(
    {
        "MEANING_REALIZATION_CAPABILITY_GAP",
        "MEANING_REALIZATION_CAUSAL_TRACE_GAP",
        "REALIZABLE_RECEPTION_EXPRESSION_ARGUMENT_GAP",
        "REALIZABLE_RECEPTION_EXPRESSION_MORPHOLOGY_GAP",
        "REALIZABLE_RECEPTION_EXPRESSION_REFERENCE_GAP",
        "REALIZABLE_RECEPTION_EXPRESSION_VISIBLE_BINDING_GAP",
    }
)


def _raise_realizable_reception_failure(
    exc: GroundedHumanReceptionSurfaceError,
) -> None:
    failure = str(exc)
    if failure not in _REALIZABLE_RECEPTION_NAMED_FAILURES:
        failure = "MEANING_REALIZATION_CAPABILITY_GAP"
    raise CMEEStage1ContractError(failure) from None


def _realizable_reception_case_marker_for_role(
    role: str,
    relation_kind: str | None = None,
) -> str:
    try:
        return source_grounded_case_marker_for_role(role, relation_kind)
    except GroundedHumanReceptionSurfaceError:
        raise CMEEStage1ContractError(
            "REALIZABLE_RECEPTION_EXPRESSION_ARGUMENT_GAP"
        ) from None


def _one_realization_row(
    rows: Iterable[Any],
    *,
    failure: str = "MEANING_REALIZATION_CAUSAL_TRACE_GAP",
) -> Any:
    selected = tuple(rows)
    if len(selected) != 1:
        raise CMEEStage1ContractError(failure)
    return selected[0]


def _validate_selected_reception_expression_lineage(
    *,
    phase_A: "Stage1SubjectivePlanningInputs",
    projection: EmlisStage1Projection,
    reception_plan: GroundedHumanReceptionPlan,
    recovery_stage: str,
    expressions: tuple[SourceGroundedRealizableReceptionExpressionV1, ...],
    authority_expressions: tuple[
        SourceGroundedRealizableReceptionExpressionV1, ...
    ],
) -> None:
    """Rebind every sealed field to the typed selected branch authority."""

    failure = "MEANING_REALIZATION_CAUSAL_TRACE_GAP"
    if (
        type(expressions) is not tuple
        or type(authority_expressions) is not tuple
        or not expressions
        or not authority_expressions
        or any(
            type(expression)
            is not SourceGroundedRealizableReceptionExpressionV1
            for expression in (*expressions, *authority_expressions)
        )
        or any(
            (
                expression.meaning_outcome_ref,
                expression.reception_binding_ref,
                expression.source_evidence_refs,
                expression.arguments,
                expression.relation_refs,
                expression.relation_endpoint_refs,
                expression.direction_refs,
                expression.provenance_refs,
            )
            != (
                authority.meaning_outcome_ref,
                authority.reception_binding_ref,
                authority.source_evidence_refs,
                authority.arguments,
                authority.relation_refs,
                authority.relation_endpoint_refs,
                authority.direction_refs,
                authority.provenance_refs,
            )
            for expression, authority in zip(
                expressions,
                authority_expressions,
                strict=False,
            )
        )
        or expressions != authority_expressions
    ):
        raise CMEEStage1ContractError(failure)
    try:
        active_moves = reception_active_moves(reception_plan, recovery_stage)
    except GroundedHumanReceptionSurfaceError:
        raise CMEEStage1ContractError(failure) from None
    if tuple(expression.move_id for expression in expressions) != tuple(
        move.move_id for move in active_moves
    ):
        raise CMEEStage1ContractError(failure)

    outcome = (
        phase_A.input_specific_meaning_structure.meaning_decision_outcome
    )
    expected_rows: list[
        tuple[
            str,
            str,
            str,
            ReceptionVisibleCausalTraceRow,
            tuple[str, ...],
        ]
    ] = []
    if type(outcome) is SelectedEmlisProvisionalReading:
        if projection.projection_branch is not SubjectiveProjectionBranch.NORMAL:
            raise CMEEStage1ContractError(failure)
        reception_set = _one_realization_row(
            row
            for row in phase_A.meaning_bound_reception_set_records
            if row.selected_reading_ref == outcome.reading_id
        )
        try:
            reception_set_ref = meaning_bound_reception_set_id(
                reception_set,
                proposition_records=(
                    phase_A.meaning_bound_reception_proposition_records
                ),
            )
        except CMEEStage1ContractError:
            raise CMEEStage1ContractError(failure) from None
        for move in active_moves:
            proposition = _one_realization_row(
                row
                for row in phase_A.meaning_bound_reception_proposition_records
                if row.selected_reading_ref == outcome.reading_id
                and row.reception_function == move.reception_act
            )
            try:
                proposition_ref = meaning_bound_reception_id(proposition)
            except CMEEStage1ContractError:
                raise CMEEStage1ContractError(failure) from None
            if proposition.reception_id != proposition_ref:
                raise CMEEStage1ContractError(failure)
            trace = _one_realization_row(
                row
                for row in projection.reception_visible_causal_trace_rows
                if row.branch is SubjectiveProjectionBranch.NORMAL
                and row.meaning_outcome_ref == outcome.reading_id
                and row.reception_record_ref == proposition_ref
            )
            expected_rows.append(
                (
                    move.move_id,
                    outcome.reading_id,
                    proposition_ref,
                    trace,
                    (
                        outcome.reading_id,
                        outcome.selected_candidate_ref,
                        reception_set_ref,
                        proposition_ref,
                        trace.projected_claim_ref,
                        *(
                            (trace.reading_consequence_ref,)
                            if trace.reading_consequence_ref is not None
                            else ()
                        ),
                    ),
                )
            )
    elif type(outcome) is LimitedMeaningOutcome:
        if projection.projection_branch is not SubjectiveProjectionBranch.LIMITED:
            raise CMEEStage1ContractError(failure)
        bounded = _one_realization_row(
            phase_A.bounded_limited_reception_records
        )
        subjective_proposition = _one_realization_row(
            phase_A.bounded_limited_subjective_proposition_records
        )
        outcome_ref = limited_meaning_outcome_id(outcome)
        try:
            reception_binding_ref = bounded_limited_reception_id(
                bounded,
                limited_outcome=outcome,
                subjective_proposition=subjective_proposition,
            )
        except CMEEStage1ContractError:
            raise CMEEStage1ContractError(failure) from None
        trace = _one_realization_row(
            row
            for row in projection.reception_visible_causal_trace_rows
            if row.branch is SubjectiveProjectionBranch.LIMITED
            and row.meaning_outcome_ref == outcome_ref
            and row.reception_record_ref == reception_binding_ref
        )
        for move in active_moves:
            retained = _one_realization_row(
                row
                for row in phase_A.retained_reception_act_rows
                if row.act_ref == move.reception_act
                and row.reception_act == move.reception_act
            )
            expected_rows.append(
                (
                    move.move_id,
                    outcome_ref,
                    reception_binding_ref,
                    trace,
                    (
                        outcome_ref,
                        reception_binding_ref,
                        bounded.proposition_ref,
                        trace.projected_claim_ref,
                        retained.act_ref,
                    ),
                )
            )
    else:
        raise CMEEStage1ContractError(failure)

    if len(expected_rows) != len(expressions):
        raise CMEEStage1ContractError(failure)
    for expression, expected in zip(expressions, expected_rows, strict=True):
        (
            move_id,
            meaning_outcome_ref,
            reception_binding_ref,
            trace,
            required_provenance_refs,
        ) = expected
        if (
            expression.move_id != move_id
            or expression.meaning_outcome_ref != meaning_outcome_ref
            or expression.reception_binding_ref != reception_binding_ref
            or trace.branch is not projection.projection_branch
            or trace.meaning_outcome_ref != meaning_outcome_ref
            or trace.reception_record_ref != reception_binding_ref
            or not set(required_provenance_refs).issubset(
                expression.provenance_refs
            )
        ):
            raise CMEEStage1ContractError(failure)


def _realizable_reception_axis(
    values: Iterable[Any],
    *,
    prefix: str,
    empty: str,
) -> str:
    raw_values = tuple(values)
    if any(
        type(value) is not str
        or not value.startswith(prefix)
        or not value.removeprefix(prefix).strip()
        for value in raw_values
    ):
        raise CMEEStage1ContractError(
            "MEANING_REALIZATION_CAUSAL_TRACE_GAP"
        )
    normalized = _ordered(
        value.removeprefix(prefix).strip() for value in raw_values
    )
    if len(normalized) > 1:
        raise CMEEStage1ContractError(
            "MEANING_REALIZATION_CAUSAL_TRACE_GAP"
        )
    return normalized[0] if normalized else empty


def _derive_source_grounded_reception_expression_authority(
    *,
    source: AdmittedTextSource,
    phase_A: "Stage1SubjectivePlanningInputs",
    projection: EmlisStage1Projection,
    selected_grounded_plan: GroundedObservationPlan,
    reception_plan: GroundedHumanReceptionPlan,
    recovery_stage: str,
) -> tuple[SourceGroundedRealizableReceptionExpressionV1, ...]:
    """Join selected meaning to each active Move without selecting again."""

    outcome = (
        phase_A.input_specific_meaning_structure.meaning_decision_outcome
    )
    if projection.projection_branch not in {
        SubjectiveProjectionBranch.NORMAL,
        SubjectiveProjectionBranch.LIMITED,
    }:
        raise CMEEStage1ContractError("MEANING_REALIZATION_CAPABILITY_GAP")
    try:
        active_moves = reception_active_moves(reception_plan, recovery_stage)
        clause_plans = build_grounded_reception_clause_plans(
            reception_plan,
            recovery_stage,
        )
    except GroundedHumanReceptionSurfaceError as exc:
        _raise_realizable_reception_failure(exc)
    if not active_moves:
        raise CMEEStage1ContractError("MEANING_REALIZATION_CAPABILITY_GAP")

    clause_form_by_move_id: dict[str, str] = {}
    for clause_plan in clause_plans:
        if (
            type(clause_plan.move_ids) is not tuple
            or not clause_plan.move_ids
            or any(
                type(move_id) is not str or not move_id
                for move_id in clause_plan.move_ids
            )
        ):
            raise CMEEStage1ContractError(
                "MEANING_REALIZATION_CAUSAL_TRACE_GAP"
            )
        for index, move_id in enumerate(clause_plan.move_ids):
            if move_id in clause_form_by_move_id:
                raise CMEEStage1ContractError(
                    "MEANING_REALIZATION_CAUSAL_TRACE_GAP"
                )
            clause_form_by_move_id[move_id] = (
                "FINITE"
                if index == len(clause_plan.move_ids) - 1
                else "CONTINUATIVE"
            )
    if set(clause_form_by_move_id) != {
        move.move_id for move in active_moves
    }:
        raise CMEEStage1ContractError(
            "MEANING_REALIZATION_CAUSAL_TRACE_GAP"
        )

    if (
        selected_grounded_plan.response_plan.human_reception_plan
        != reception_plan
    ):
        raise CMEEStage1ContractError(
            "MEANING_REALIZATION_CAUSAL_TRACE_GAP"
        )
    plan_binding = _bind_grounded_plan(
        source,
        phase_A.grounded_graph,
        selected_grounded_plan,
    )
    semantic_ref_by_nucleus_id = {
        nucleus_id: _node_ref(node_id)
        for nucleus_id, node_id in plan_binding.nucleus_to_node.items()
    }
    nucleus_id_by_semantic_ref = {
        semantic_ref: nucleus_id
        for nucleus_id, semantic_ref in semantic_ref_by_nucleus_id.items()
    }
    nucleus_by_id = {
        nucleus.nucleus_id: nucleus
        for nucleus in selected_grounded_plan.nuclei
    }
    relation_by_edge_ref = {
        _edge_ref(edge_id): relation
        for edge_id, relation in plan_binding.edge_meta.items()
    }
    resolver = build_evidence_span_resolver(
        source.evidence_spans,
        current_input=source.normalized_current_input,
    )

    contribution_by_ref = {
        row.contribution_id: row
        for row in phase_A.observation_contribution_rows
    }
    candidate_ref_by_contribution = dict(
        phase_A.contribution_to_candidate_ref_map
    )
    semantic_projection_by_candidate = {
        row.interpretation_candidate_ref: row
        for row in (
            phase_A.grounded_situation_view.semantic_interpretation_projections
        )
    }
    node_by_ref = {
        _node_ref(node.node_id): node for node in phase_A.grounded_graph.nodes
    }
    edge_by_ref = {
        _edge_ref(edge.edge_id): edge for edge in phase_A.grounded_graph.edges
    }
    edge_refs = {
        _edge_ref(edge.edge_id) for edge in phase_A.grounded_graph.edges
    }
    evidence_rows = tuple(source.evidence_refs)
    canonical_evidence_rows = tuple(
        (
            _evidence_ref(
                row.evidence_id,
                phase_A.grounded_graph.source_version,
            ),
            row,
        )
        for row in evidence_rows
    )
    evidence_ref_by_canonical_ref = dict(canonical_evidence_rows)
    evidence_ref_by_source_span_id = {
        row.source_span_id: row for row in evidence_rows
    }
    if (
        len(evidence_ref_by_canonical_ref) != len(canonical_evidence_rows)
        or len(evidence_ref_by_source_span_id) != len(evidence_rows)
        or any(
            type(ref) is not str
            or not ref
            or type(row.source_span_id) is not str
            or not row.source_span_id
            for ref, row in canonical_evidence_rows
        )
    ):
        raise CMEEStage1ContractError(
            "MEANING_REALIZATION_CAUSAL_TRACE_GAP"
        )

    def _canonical_evidence_refs_for_span_ids(
        span_ids: Iterable[str],
    ) -> tuple[str, ...]:
        try:
            rows = tuple(
                evidence_ref_by_source_span_id[span_id]
                for span_id in span_ids
            )
        except KeyError:
            raise CMEEStage1ContractError(
                "MEANING_REALIZATION_CAUSAL_TRACE_GAP"
            ) from None
        refs = tuple(
            _evidence_ref(
                row.evidence_id,
                phase_A.grounded_graph.source_version,
            )
            for row in rows
        )
        if len(refs) != len(set(refs)):
            raise CMEEStage1ContractError(
                "MEANING_REALIZATION_CAUSAL_TRACE_GAP"
            )
        return refs
    claim_by_ref = {
        row.subjective_claim_id: row for row in projection.subjective_claims
    }

    normal_set_ref = ""
    normal_proposition_by_act: dict[str, MeaningBoundReceptionProposition] = {}
    limited_binding_ref = ""
    limited_trace: ReceptionVisibleCausalTraceRow | None = None
    limited_claim: EmlisSubjectiveClaim | None = None
    bounded: BoundedLimitedReception | None = None
    limited_subjective_proposition: SubjectivePropositionV2 | None = None
    selected_meaning_candidate: Any | None = None
    retained_by_act: dict[str, Any] = {}
    if type(outcome) is SelectedEmlisProvisionalReading:
        if projection.projection_branch is not SubjectiveProjectionBranch.NORMAL:
            raise CMEEStage1ContractError(
                "MEANING_REALIZATION_CAUSAL_TRACE_GAP"
            )
        reception_set = _one_realization_row(
            row
            for row in phase_A.meaning_bound_reception_set_records
            if row.selected_reading_ref == outcome.reading_id
        )
        normal_set_ref = meaning_bound_reception_set_id(
            reception_set,
            proposition_records=(
                phase_A.meaning_bound_reception_proposition_records
            ),
        )
        selected_meaning_candidate = _one_realization_row(
            row
            for row in (
                phase_A.input_specific_meaning_structure.candidate_records
            )
            if row.candidate_id == outcome.selected_candidate_ref
        )
        for move in active_moves:
            proposition = _one_realization_row(
                row
                for row in phase_A.meaning_bound_reception_proposition_records
                if row.selected_reading_ref == outcome.reading_id
                and row.reception_function == move.reception_act
            )
            normal_proposition_by_act[move.reception_act] = proposition
        meaning_outcome_ref = outcome.reading_id
    elif type(outcome) is LimitedMeaningOutcome:
        if projection.projection_branch is not SubjectiveProjectionBranch.LIMITED:
            raise CMEEStage1ContractError(
                "MEANING_REALIZATION_CAUSAL_TRACE_GAP"
            )
        meaning_outcome_ref = limited_meaning_outcome_id(outcome)
        bounded = _one_realization_row(
            phase_A.bounded_limited_reception_records
        )
        limited_subjective_proposition = _one_realization_row(
            phase_A.bounded_limited_subjective_proposition_records
        )
        limited_binding_ref = bounded_limited_reception_id(
            bounded,
            limited_outcome=outcome,
            subjective_proposition=limited_subjective_proposition,
        )
        limited_trace = _one_realization_row(
            row
            for row in projection.reception_visible_causal_trace_rows
            if row.branch is SubjectiveProjectionBranch.LIMITED
            and row.meaning_outcome_ref == meaning_outcome_ref
            and row.reception_record_ref == limited_binding_ref
        )
        limited_claim = claim_by_ref.get(limited_trace.projected_claim_ref)
        if limited_claim is None:
            raise CMEEStage1ContractError(
                "MEANING_REALIZATION_CAUSAL_TRACE_GAP"
            )
        if (
            not limited_subjective_proposition.target_contribution_refs
            or tuple(limited_subjective_proposition.target_contribution_refs)
            != tuple(limited_trace.layer1_contribution_refs)
            or not set(limited_subjective_proposition.target_contribution_refs)
            <= set(bounded.bound_layer1_contribution_refs)
            or tuple(limited_trace.projected_response_object_refs)
            != tuple(limited_subjective_proposition.response_object_refs)
            or tuple(limited_trace.response_object_refs)
            != tuple(bounded.foreground_source_object_refs)
        ):
            raise CMEEStage1ContractError(
                "MEANING_REALIZATION_CAUSAL_TRACE_GAP"
            )
        for move in active_moves:
            retained_by_act[move.reception_act] = _one_realization_row(
                row
                for row in phase_A.retained_reception_act_rows
                if row.act_ref == move.reception_act
                and row.reception_act == move.reception_act
            )
    else:
        raise CMEEStage1ContractError("MEANING_REALIZATION_CAPABILITY_GAP")

    expressions: list[SourceGroundedRealizableReceptionExpressionV1] = []
    for move in active_moves:
        if type(outcome) is SelectedEmlisProvisionalReading:
            proposition = normal_proposition_by_act[move.reception_act]
            trace = _one_realization_row(
                row
                for row in projection.reception_visible_causal_trace_rows
                if row.branch is SubjectiveProjectionBranch.NORMAL
                and row.meaning_outcome_ref == outcome.reading_id
                and row.reception_record_ref == proposition.reception_id
            )
            claim = claim_by_ref.get(trace.projected_claim_ref)
            if (
                claim is None
                or move.reception_act not in claim.source_reception_act_refs
                or trace.response_object_refs != proposition.response_object_refs
                or trace.preserved_difference_refs
                != proposition.preserved_difference_refs
            ):
                raise CMEEStage1ContractError(
                    "MEANING_REALIZATION_CAUSAL_TRACE_GAP"
                )
            assert selected_meaning_candidate is not None
            if (
                type(selected_meaning_candidate.basis_contribution_refs)
                is not tuple
            ):
                raise CMEEStage1ContractError(
                    "MEANING_REALIZATION_CAUSAL_TRACE_GAP"
                )
            contribution_refs = tuple(
                ref
                for ref in trace.layer1_contribution_refs
                if ref in set(
                    selected_meaning_candidate.basis_contribution_refs
                )
            )
            semantic_domain = set(trace.projected_response_object_refs)
            reception_binding_ref = proposition.reception_id
            branch_provenance = (
                outcome.reading_id,
                outcome.selected_candidate_ref,
                normal_set_ref,
                proposition.reception_id,
                trace.projected_claim_ref,
                *(ref for ref in (trace.reading_consequence_ref,) if ref),
            )
        else:
            assert bounded is not None
            assert limited_trace is not None
            assert limited_claim is not None
            assert limited_subjective_proposition is not None
            retained = retained_by_act[move.reception_act]
            if (
                move.reception_act
                not in limited_claim.source_reception_act_refs
                or retained.act_ref != move.reception_act
                or retained.reception_act != move.reception_act
                or type(retained.basis_contribution_refs) is not tuple
                or not retained.basis_contribution_refs
                or not set(retained.basis_contribution_refs).issubset(
                    limited_subjective_proposition.target_contribution_refs
                )
            ):
                raise CMEEStage1ContractError(
                    "MEANING_REALIZATION_CAUSAL_TRACE_GAP"
                )
            contribution_refs = tuple(retained.basis_contribution_refs)
            semantic_domain = set(
                limited_subjective_proposition.response_object_refs
            )
            reception_binding_ref = limited_binding_ref
            branch_provenance = (
                meaning_outcome_ref,
                limited_binding_ref,
                bounded.proposition_ref,
                limited_trace.projected_claim_ref,
                retained.act_ref,
            )

        if (
            type(move.target_nucleus_ids) is not tuple
            or not move.target_nucleus_ids
            or type(move.support_nucleus_ids) is not tuple
            or any(
                type(nucleus_id) is not str or not nucleus_id
                for nucleus_id in (
                    *move.target_nucleus_ids,
                    *move.support_nucleus_ids,
                )
            )
            or any(
                type(ref) is not str or not ref
                for ref in (*contribution_refs, *semantic_domain)
            )
        ):
            raise CMEEStage1ContractError(
                "MEANING_REALIZATION_CAUSAL_TRACE_GAP"
            )
        move_nucleus_ids = _ordered(
            (*move.target_nucleus_ids, *move.support_nucleus_ids)
        )
        try:
            target_semantic_refs = _ordered(
                semantic_ref_by_nucleus_id[nucleus_id]
                for nucleus_id in move.target_nucleus_ids
            )
            target_nuclei = tuple(
                nucleus_by_id[nucleus_id]
                for nucleus_id in move.target_nucleus_ids
            )
        except KeyError:
            raise CMEEStage1ContractError(
                "MEANING_REALIZATION_CAUSAL_TRACE_GAP"
            ) from None
        focus_kinds = _ordered(
            nucleus.kind
            for nucleus in target_nuclei
            if type(nucleus.kind) is str and nucleus.kind
        )
        if (
            not contribution_refs
            or not semantic_domain
            or not target_semantic_refs
            or not focus_kinds
            or any(
                type(nucleus.kind) is not str or not nucleus.kind
                for nucleus in target_nuclei
            )
            or not set(target_semantic_refs).issubset(semantic_domain)
        ):
            raise CMEEStage1ContractError(
                "MEANING_REALIZATION_CAUSAL_TRACE_GAP"
            )
        focus_kind = "+".join(focus_kinds)
        contribution_candidate_refs: list[str] = []
        for contribution_ref in contribution_refs:
            contribution = contribution_by_ref.get(contribution_ref)
            candidate_ref = candidate_ref_by_contribution.get(contribution_ref)
            semantic_projection = semantic_projection_by_candidate.get(
                candidate_ref
            )
            if (
                contribution is None
                or semantic_projection is None
                or contribution_ref
                not in semantic_projection.basis_contribution_refs
            ):
                raise CMEEStage1ContractError(
                    "MEANING_REALIZATION_CAUSAL_TRACE_GAP"
                )
            if candidate_ref not in contribution_candidate_refs:
                contribution_candidate_refs.append(candidate_ref)

        realization_candidate_refs = tuple(contribution_candidate_refs)
        realization_candidate_ref_set = set(realization_candidate_refs)
        selected_projection_rows = [
            semantic_projection
            for semantic_projection in (
                phase_A.grounded_situation_view
                .semantic_interpretation_projections
            )
            if semantic_projection.interpretation_candidate_ref
            in realization_candidate_ref_set
        ]
        if (
            len(selected_projection_rows) != len(realization_candidate_refs)
            or {
                semantic_projection.interpretation_candidate_ref
                for semantic_projection in selected_projection_rows
            }
            != realization_candidate_ref_set
            or any(
                not set(semantic_projection.basis_contribution_refs).issubset(
                    contribution_refs
                )
                for semantic_projection in selected_projection_rows
            )
        ):
            raise CMEEStage1ContractError(
                "MEANING_REALIZATION_CAUSAL_TRACE_GAP"
            )
        for semantic_projection in selected_projection_rows:
            try:
                expected_projection_evidence_refs = _ordered(
                    (
                        *(
                            ref
                            for component in semantic_projection.component_rows
                            for ref in component.source_evidence_refs
                        ),
                        *(
                            _evidence_ref(
                                evidence_id,
                                phase_A.grounded_graph.source_version,
                            )
                            for relation_ref in (
                                semantic_projection.relation_path_refs
                            )
                            for evidence_id in edge_by_ref[
                                relation_ref
                            ].evidence_ids
                        ),
                    )
                )
            except KeyError:
                raise CMEEStage1ContractError(
                    "MEANING_REALIZATION_CAUSAL_TRACE_GAP"
                ) from None
            if (
                tuple(semantic_projection.source_evidence_refs)
                != expected_projection_evidence_refs
                or any(
                    ref not in evidence_ref_by_canonical_ref
                    for ref in expected_projection_evidence_refs
                )
            ):
                raise CMEEStage1ContractError(
                    "MEANING_REALIZATION_CAUSAL_TRACE_GAP"
                )

        candidate_relation_refs = _ordered(
            (
                *(
                    ref
                    for semantic_projection in selected_projection_rows
                    for ref in semantic_projection.relation_path_refs
                ),
                *(
                    ref
                    for contribution_ref in contribution_refs
                    for ref in contribution_by_ref[
                        contribution_ref
                    ].relation_basis_refs
                ),
            )
        )
        if any(
            type(ref) is not str
            or not ref
            or ref not in edge_refs
            or ref not in relation_by_edge_ref
            for ref in candidate_relation_refs
        ):
            raise CMEEStage1ContractError(
                "MEANING_REALIZATION_CAUSAL_TRACE_GAP"
            )
        target_nucleus_id_set = set(move.target_nucleus_ids)
        required_relation_ids = set(
            selected_grounded_plan.coverage_requirements.required_relation_ids
        )
        candidate_relation_ref_set = set(candidate_relation_refs)
        applicable_relation_rows = tuple(
            relation
            for relation in selected_grounded_plan.relations
            if relation.relation_id in required_relation_ids
            and target_nucleus_id_set.intersection(
                (
                    relation.from_nucleus_id,
                    relation.to_nucleus_id,
                )
            )
        )
        try:
            plan_applicable_relation_refs = tuple(
                _edge_ref(plan_binding.relation_to_edge[relation.relation_id])
                for relation in applicable_relation_rows
            )
        except KeyError:
            raise CMEEStage1ContractError(
                "MEANING_REALIZATION_CAUSAL_TRACE_GAP"
            ) from None
        candidate_applicable_relation_refs = tuple(
            ref
            for ref in plan_applicable_relation_refs
            if ref in candidate_relation_ref_set
        )
        if candidate_applicable_relation_refs != plan_applicable_relation_refs:
            raise CMEEStage1ContractError(
                "MEANING_REALIZATION_CAUSAL_TRACE_GAP"
            )
        move_nucleus_ids = _ordered(
            (
                *move_nucleus_ids,
                *(
                    nucleus_id
                    for relation in applicable_relation_rows
                    for nucleus_id in (
                        relation.from_nucleus_id,
                        relation.to_nucleus_id,
                    )
                ),
            )
        )
        try:
            move_semantic_refs = _ordered(
                semantic_ref_by_nucleus_id[nucleus_id]
                for nucleus_id in move_nucleus_ids
            )
        except KeyError:
            raise CMEEStage1ContractError(
                "MEANING_REALIZATION_CAUSAL_TRACE_GAP"
            ) from None
        semantic_domain.intersection_update(move_semantic_refs)
        if (
            not semantic_domain
            or not set(target_semantic_refs).issubset(semantic_domain)
        ):
            raise CMEEStage1ContractError(
                "MEANING_REALIZATION_CAUSAL_TRACE_GAP"
            )

        move_semantic_rank = {
            semantic_ref: index
            for index, semantic_ref in enumerate(move_semantic_refs)
        }
        relation_refs = plan_applicable_relation_refs
        relation_kinds = tuple(
            relation.type for relation in applicable_relation_rows
        )
        if (
            candidate_applicable_relation_refs != relation_refs
            or len(relation_refs) != len(set(relation_refs))
            or any(
                type(relation_kind) is not str or not relation_kind
                for relation_kind in relation_kinds
            )
        ):
            raise CMEEStage1ContractError(
                "MEANING_REALIZATION_CAUSAL_TRACE_GAP"
            )
        applicable_relation_ref_set = set(relation_refs)
        relation_rank = {
            relation_ref: index
            for index, relation_ref in enumerate(relation_refs)
        }
        relation_by_ref = dict(zip(
            relation_refs,
            applicable_relation_rows,
            strict=True,
        ))
        selected_nucleus_rank = {
            nucleus.nucleus_id: index
            for index, nucleus in enumerate(selected_grounded_plan.nuclei)
        }

        # Keep the owning projection beside every component.  Dataclass
        # equality is payload equality, not provenance, and therefore cannot
        # be used to recover a component's relation path.
        component_entries: list[tuple[int, int, Any, Any]] = []
        for projection_rank, semantic_projection in enumerate(
            selected_projection_rows
        ):
            owned_applicable_refs = set(
                semantic_projection.relation_path_refs
            ).intersection(applicable_relation_ref_set)
            for component_rank, component in enumerate(
                semantic_projection.component_rows
            ):
                role_key = getattr(component, "role_key", "")
                if component.source_object_ref not in semantic_domain:
                    continue
                if (
                    role_key.removeprefix("role:").upper()
                    in _REALIZABLE_RECEPTION_ENDPOINT_ROLES
                    and not owned_applicable_refs
                ):
                    continue
                component_entries.append(
                    (
                        projection_rank,
                        component_rank,
                        semantic_projection,
                        component,
                    )
                )
        if not component_entries:
            raise CMEEStage1ContractError(
                "MEANING_REALIZATION_CAPABILITY_GAP"
            )
        if any(
            type(entry[3].source_object_ref) is not str
            or not entry[3].source_object_ref
            or entry[3].source_object_ref not in move_semantic_rank
            for entry in component_entries
        ):
            raise CMEEStage1ContractError(
                "MEANING_REALIZATION_CAUSAL_TRACE_GAP"
            )
        component_entries.sort(
            key=lambda entry: (
                move_semantic_rank[entry[3].source_object_ref],
                entry[0],
                entry[1],
            )
        )
        if (
            _ordered(
                entry[3].source_object_ref for entry in component_entries
            )
            != move_semantic_refs
        ):
            raise CMEEStage1ContractError(
                "REALIZABLE_RECEPTION_EXPRESSION_ARGUMENT_GAP"
            )
        try:
            lexical_rows = tuple(
                _bounded_source_grounded_lexemes(
                    nucleus_by_id[nucleus_id_by_semantic_ref[semantic_ref]],
                    resolver,
                )
                for semantic_ref in move_semantic_refs
            )
        except KeyError:
            raise CMEEStage1ContractError(
                "MEANING_REALIZATION_CAUSAL_TRACE_GAP"
            ) from None
        except GroundedHumanReceptionSurfaceError as exc:
            _raise_realizable_reception_failure(exc)
        if (
            len(lexical_rows) != len(move_semantic_refs)
            or any(
                type(argument) is not str
                or not argument.strip()
                or type(head) is not str
                or not head.strip()
                for argument, head in lexical_rows
            )
        ):
            raise CMEEStage1ContractError(
                "MEANING_REALIZATION_CAPABILITY_GAP"
            )
        lexical_form_by_semantic_ref = {
            semantic_ref: lexical_row[0]
            for semantic_ref, lexical_row in zip(
                move_semantic_refs,
                lexical_rows,
                strict=True,
            )
        }
        if any(
            entry[3].source_object_ref not in lexical_form_by_semantic_ref
            for entry in component_entries
        ):
            raise CMEEStage1ContractError(
                "REALIZABLE_RECEPTION_EXPRESSION_ARGUMENT_GAP"
            )

        def _component_relation_refs(
            entry: tuple[int, int, Any, Any],
        ) -> tuple[str, ...]:
            owner_relation_refs = set(entry[2].relation_path_refs)
            return tuple(
                relation_ref
                for relation_ref in relation_refs
                if relation_ref in owner_relation_refs
            )

        def _component_relation_matches(
            entry: tuple[int, int, Any, Any],
            relation_ref: str,
        ) -> bool:
            component = entry[3]
            role = component.role_key.removeprefix("role:").upper()
            relation = relation_by_ref[relation_ref]
            expected_endpoints = (
                _source_grounded_relation_endpoint_nucleus_roles(
                    relation,
                    nucleus_by_id,
                    selected_nucleus_rank,
                )
            )
            return any(
                expected_role == role
                and semantic_ref_by_nucleus_id.get(nucleus_id)
                == component.source_object_ref
                for nucleus_id, expected_role in expected_endpoints
            )

        argument_entries: list[
            tuple[tuple[int, int, Any, Any], str | None]
        ] = []
        for entry in component_entries:
            component = entry[3]
            role = component.role_key.removeprefix("role:").upper()
            if role in _REALIZABLE_RECEPTION_ENDPOINT_ROLES:
                matching_relation_refs = tuple(
                    relation_ref
                    for relation_ref in _component_relation_refs(entry)
                    if _component_relation_matches(entry, relation_ref)
                )
                if not matching_relation_refs:
                    raise CMEEStage1ContractError(
                        "REALIZABLE_RECEPTION_EXPRESSION_ARGUMENT_GAP"
                    )
                for relation_ref in matching_relation_refs:
                    _realizable_reception_case_marker_for_role(
                        role,
                        relation_by_ref[relation_ref].type,
                    )
                argument_entries.extend(
                    (entry, relation_ref)
                    for relation_ref in matching_relation_refs
                )
            else:
                _realizable_reception_case_marker_for_role(role)
                if _component_relation_refs(entry):
                    raise CMEEStage1ContractError(
                        "REALIZABLE_RECEPTION_EXPRESSION_ARGUMENT_GAP"
                    )
                argument_entries.append((entry, None))
        argument_entries.sort(
            key=lambda row: (
                move_semantic_rank[row[0][3].source_object_ref],
                -1 if row[1] is None else relation_rank[row[1]],
                row[0][0],
                row[0][1],
            )
        )
        direct_argument_role_keys = {
            (
                entry[3].source_object_ref,
                entry[3].role_key.removeprefix("role:").upper(),
            )
            for entry, relation_ref in argument_entries
            if relation_ref is None
        }

        arguments: list[RealizableReceptionArgumentV1] = []
        argument_by_key: dict[
            tuple[str, str, str | None], RealizableReceptionArgumentV1
        ] = {}
        for entry, relation_ref in argument_entries:
            semantic_projection = entry[2]
            component = entry[3]
            semantic_ref = component.source_object_ref
            node = node_by_ref.get(semantic_ref)
            lexical_form = lexical_form_by_semantic_ref[semantic_ref]
            role = (
                component.role_key.removeprefix("role:").upper()
                if (
                    type(component.role_key) is str
                    and component.role_key.startswith("role:")
                )
                else ""
            )
            relation_kind = (
                relation_by_ref[relation_ref].type
                if relation_ref is not None
                else None
            )
            case_marker = _realizable_reception_case_marker_for_role(
                role,
                relation_kind,
            )
            if (
                node is None
                or type(component.source_evidence_refs) is not tuple
                or not component.source_evidence_refs
                or any(
                    type(ref) is not str or not ref
                    for ref in component.source_evidence_refs
                )
                or set(
                    _evidence_ref(
                        evidence_id,
                        phase_A.grounded_graph.source_version,
                    )
                    for evidence_id in node.evidence_ids
                )
                != set(component.source_evidence_refs)
                or any(
                    evidence_ref not in evidence_ref_by_canonical_ref
                    for evidence_ref in component.source_evidence_refs
                )
                or not set(component.source_evidence_refs).issubset(
                    semantic_projection.source_evidence_refs
                )
            ):
                raise CMEEStage1ContractError(
                    "REALIZABLE_RECEPTION_EXPRESSION_ARGUMENT_GAP"
                )
            try:
                nucleus = nucleus_by_id[
                    nucleus_id_by_semantic_ref[semantic_ref]
                ]
            except KeyError:
                raise CMEEStage1ContractError(
                    "MEANING_REALIZATION_CAUSAL_TRACE_GAP"
                ) from None
            if set(component.source_evidence_refs) != set(
                _canonical_evidence_refs_for_span_ids(
                    nucleus.source_span_ids
                )
            ):
                raise CMEEStage1ContractError(
                    "MEANING_REALIZATION_CAUSAL_TRACE_GAP"
                )
            relation_evidence_refs: tuple[str, ...] = ()
            relation_endpoint_ref: str | None = None
            direction_ref: str | None = None
            if relation_ref is not None:
                relation = relation_by_ref[relation_ref]
                edge = edge_by_ref.get(relation_ref)
                relation_evidence_refs = (
                    _canonical_evidence_refs_for_span_ids(
                        relation.source_span_ids
                    )
                )
                if (
                    edge is None
                    or set(relation_evidence_refs)
                    != {
                        _evidence_ref(
                            evidence_id,
                            phase_A.grounded_graph.source_version,
                        )
                        for evidence_id in edge.evidence_ids
                    }
                    or not set(relation_evidence_refs).issubset(
                        semantic_projection.source_evidence_refs
                    )
                ):
                    raise CMEEStage1ContractError(
                        "MEANING_REALIZATION_CAUSAL_TRACE_GAP"
                    )
                relation_endpoint_ref = (
                    _source_grounded_relation_endpoint_ref(
                        relation_ref,
                        semantic_ref,
                        role,
                    )
                )
                direction_side = _source_grounded_direction_side(
                    relation.type,
                    role,
                )
                if direction_side is not None:
                    direction_ref = _source_grounded_direction_ref(
                        relation_ref,
                        semantic_ref,
                        role,
                        direction_side,
                    )
            argument_evidence_refs = _ordered(
                (
                    *component.source_evidence_refs,
                    *relation_evidence_refs,
                )
            )
            shared_current_user_subject = bool(
                relation_ref is None
                and role == "EXPERIENCER"
                and (semantic_ref, "PRIMARY") in direct_argument_role_keys
                and _enum_or_text(nucleus.semantic_frame.actor).lower()
                in {"current_user", "user"}
            )
            candidate_argument = RealizableReceptionArgumentV1(
                semantic_ref=semantic_ref,
                source_evidence_refs=argument_evidence_refs,
                semantic_role=role,
                lexical_form=lexical_form,
                requirement="REQUIRED",
                omission_permission="FORBIDDEN",
                zero_realization_condition_refs=(
                    ("shared-subject:current-user",)
                    if shared_current_user_subject
                    else ()
                ),
                omission_condition_refs=(),
                case_marker=case_marker,
                direction_ref=direction_ref,
                relation_endpoint_ref=relation_endpoint_ref,
                realization=(
                    "ZERO" if shared_current_user_subject else "EXPLICIT"
                ),
            )
            key = (semantic_ref, role, relation_endpoint_ref)
            prior = argument_by_key.get(key)
            if prior is not None:
                if prior != candidate_argument:
                    raise CMEEStage1ContractError(
                        "REALIZABLE_RECEPTION_EXPRESSION_ARGUMENT_GAP"
                    )
                continue
            argument_by_key[key] = candidate_argument
            arguments.append(candidate_argument)
        if not arguments:
            raise CMEEStage1ContractError(
                "REALIZABLE_RECEPTION_EXPRESSION_ARGUMENT_GAP"
            )

        source_evidence_refs = _ordered(
            ref
            for argument in arguments
            for ref in argument.source_evidence_refs
        )
        expected_move_evidence_refs = _ordered(
            (
                *(
                    ref
                    for semantic_ref in move_semantic_refs
                    for ref in _canonical_evidence_refs_for_span_ids(
                        nucleus_by_id[
                            nucleus_id_by_semantic_ref[semantic_ref]
                        ].source_span_ids
                    )
                ),
                *(
                    ref
                    for relation in applicable_relation_rows
                    for ref in _canonical_evidence_refs_for_span_ids(
                        relation.source_span_ids
                    )
                ),
            )
        )
        if (
            set(source_evidence_refs) != set(expected_move_evidence_refs)
            or not set(move.source_evidence_span_ids).issubset(
                evidence_ref_by_canonical_ref[ref].source_span_id
                for ref in source_evidence_refs
            )
        ):
            raise CMEEStage1ContractError(
                "MEANING_REALIZATION_CAUSAL_TRACE_GAP"
            )
        component_rows = [entry[3] for entry in component_entries]
        semantic_refs = _ordered(
            argument.semantic_ref for argument in arguments
        )
        subject_refs = _ordered(
            argument.semantic_ref
            for argument in arguments
            if argument.semantic_role
            in {"PRIMARY", "LEFT", "RIGHT", "BEFORE", "AFTER", "CHANGE", "EFFECT"}
        ) or semantic_refs[:1]
        actor_refs = _ordered(
            argument.semantic_ref
            for argument in arguments
            if argument.semantic_role in {"ACTION", "CAUSE"}
            or any(
                component.source_object_ref == argument.semantic_ref
                and component.semantic_kind_key == "semantic-kind:action"
                for component in component_rows
            )
        )
        experiencer_refs = _ordered(
            argument.semantic_ref
            for argument in arguments
            if argument.semantic_role == "EXPERIENCER"
        )
        qualifier_refs = _ordered(
            ref for component in component_rows for ref in component.qualifier_refs
        )
        if any(type(ref) is not str or not ref for ref in qualifier_refs):
            raise CMEEStage1ContractError(
                "MEANING_REALIZATION_CAUSAL_TRACE_GAP"
            )
        target_component_rows = tuple(
            component
            for component in component_rows
            if component.source_object_ref in set(target_semantic_refs)
        )
        # LEFT/RIGHT rows describe a target's participation in a relation;
        # they do not replace an available content-bearing predicate duty for
        # that same target.  Prefer the selected meaning's non-endpoint row
        # and use an endpoint row only when it is the sole target carrier.
        content_component_rows = tuple(
            component
            for component in target_component_rows
            if component.role_key not in {"role:left", "role:right"}
        )
        scalar_component_rows = (
            content_component_rows or target_component_rows
        )
        if not scalar_component_rows:
            raise CMEEStage1ContractError(
                "MEANING_REALIZATION_CAUSAL_TRACE_GAP"
            )
        scalar_qualifier_refs = _ordered(
            ref
            for component in scalar_component_rows
            for ref in component.qualifier_refs
        )
        predicate_kind = _realizable_reception_axis(
            (
                component.typed_predicate_key
                for component in scalar_component_rows
            ),
            prefix="predicate:",
            empty="source_bounded",
        )
        polarity = _realizable_reception_axis(
            (component.polarity_key for component in scalar_component_rows),
            prefix="polarity:",
            empty="source_bounded",
        )
        modality = _realizable_reception_axis(
            (component.modality_key for component in scalar_component_rows),
            prefix="modality:",
            empty="source_bounded",
        )
        time_scope = _realizable_reception_axis(
            (
                component.temporal_state_key
                for component in scalar_component_rows
            ),
            prefix="time:",
            empty="current_input",
        )
        scope = _realizable_reception_axis(
            (component.scope_key for component in scalar_component_rows),
            prefix="scope:",
            empty="source_bounded",
        )
        aspect = _realizable_reception_axis(
            (
                ref
                for ref in scalar_qualifier_refs
                if ref.startswith("aspect:")
            ),
            prefix="aspect:",
            empty="unknown",
        )
        degree = _realizable_reception_axis(
            (
                ref
                for ref in scalar_qualifier_refs
                if ref.startswith("degree:")
            ),
            prefix="degree:",
            empty="source_bounded",
        )
        quantity = _realizable_reception_axis(
            (
                ref
                for ref in scalar_qualifier_refs
                if ref.startswith("quantity:")
            ),
            prefix="quantity:",
            empty="not_applicable",
        )
        lexical_head = lexical_rows[0][1]
        effective_reference_mode = reception_effective_move_reference_mode(
            reception_plan,
            move,
            recovery_stage,
        )
        if effective_reference_mode == "anaphoric_first":
            reference_mode = "ANAPHORIC"
        elif effective_reference_mode == "short_anchor_if_ambiguous":
            reference_mode = (
                "COMPOSITE" if len(lexical_rows) > 1 else "EXPLICIT"
            )
        elif effective_reference_mode == "explicit_emlis_counterposition":
            reference_mode = "EXPLICIT"
        else:
            raise CMEEStage1ContractError(
                "REALIZABLE_RECEPTION_EXPRESSION_REFERENCE_GAP"
            )
        if reference_mode == "ANAPHORIC":
            antecedent_refs = semantic_refs
            antecedent_condition = "PRIOR_LAYER1_EXACT_SEMANTIC_COVER"
        elif reference_mode in {"COMPOSITE", "EXPLICIT"}:
            antecedent_refs = ()
            antecedent_condition = None
        else:
            raise CMEEStage1ContractError(
                "REALIZABLE_RECEPTION_EXPRESSION_REFERENCE_GAP"
            )
        direction_refs = _ordered(
            argument.direction_ref
            for argument in arguments
            if argument.direction_ref is not None
        )
        relation_endpoint_refs = _ordered(
            argument.relation_endpoint_ref
            for argument in arguments
            if argument.relation_endpoint_ref is not None
        )
        particle_plan = tuple(
            f"particle:{argument.semantic_role}:{argument.case_marker or 'ZERO'}"
            for argument in arguments
        )
        inflection_plan = (
            f"predicate:{predicate_kind}",
            f"polarity:{polarity}",
            f"modality:{modality}",
            f"time:{time_scope}",
            f"aspect:{aspect}",
            f"degree:{degree}",
            f"quantity:{quantity}",
            f"scope:{scope}",
            f"focus-kind:{focus_kind}",
            "head-class:source-grounded-proposition",
            "politeness:polite",
            f"reception-form:{recovery_stage}",
            f"clause-form:{clause_form_by_move_id[move.move_id]}",
        )
        nominalization_plan = derive_source_grounded_nominalization_plan(
            tuple(nucleus_by_id[nucleus_id_by_semantic_ref[semantic_ref]]
                  for semantic_ref in move_semantic_refs),
            tuple(argument for argument, _head in lexical_rows),
            reference_mode,
        )
        relation_kinds = tuple(relation_kinds)
        if any(
            type(relation_kind) is not str or not relation_kind
            for relation_kind in relation_kinds
        ):
            raise CMEEStage1ContractError(
                "MEANING_REALIZATION_CAUSAL_TRACE_GAP"
            )
        clause_link_plan = (
            tuple(
                f"relation-kind:{relation_kind}"
                for relation_kind in relation_kinds
            )
            or ("clause-link:none",)
        )
        provenance_refs = _ordered(
            (
                *branch_provenance,
                *contribution_refs,
                *(
                    semantic_projection.interpretation_candidate_ref
                    for semantic_projection in selected_projection_rows
                ),
                *source_evidence_refs,
                *relation_refs,
            )
        )
        draft = SourceGroundedRealizableReceptionExpressionV1(
            schema_version=(
                SOURCE_GROUNDED_RECEPTION_EXPRESSION_SCHEMA_VERSION
            ),
            expression_ref="",
            meaning_outcome_ref=meaning_outcome_ref,
            reception_binding_ref=reception_binding_ref,
            move_id=move.move_id,
            source_evidence_refs=source_evidence_refs,
            actor_refs=actor_refs,
            subject_refs=subject_refs,
            experiencer_refs=experiencer_refs,
            predicate_kind=predicate_kind,
            lexical_head=lexical_head,
            arguments=tuple(arguments),
            polarity=polarity,
            modality=modality,
            time_scope=time_scope,
            aspect=aspect,
            degree=degree,
            quantity=quantity,
            scope=scope,
            qualifier_refs=qualifier_refs,
            relation_refs=relation_refs,
            relation_endpoint_refs=relation_endpoint_refs,
            direction_refs=direction_refs,
            reference_mode=reference_mode,
            antecedent_refs=antecedent_refs,
            antecedent_condition=antecedent_condition,
            particle_plan=particle_plan,
            inflection_plan=inflection_plan,
            nominalization_plan=nominalization_plan,
            clause_link_plan=clause_link_plan,
            provenance_refs=provenance_refs,
        )
        try:
            expressions.append(
                identify_source_grounded_reception_expression(draft)
            )
        except GroundedHumanReceptionSurfaceError as exc:
            _raise_realizable_reception_failure(exc)

    if (
        tuple(expression.move_id for expression in expressions)
        != tuple(move.move_id for move in active_moves)
        or len({row.move_id for row in expressions}) != len(expressions)
        or len({row.expression_ref for row in expressions}) != len(expressions)
        or not {
            move.move_id for move in active_moves if move.required
        }.issubset(row.move_id for row in expressions)
    ):
        raise CMEEStage1ContractError(
            "MEANING_REALIZATION_CAUSAL_TRACE_GAP"
        )
    try:
        validated_rows = validate_source_grounded_reception_expressions(
            reception_plan,
            tuple(expressions),
            recovery_stage,
        )
    except GroundedHumanReceptionSurfaceError as exc:
        _raise_realizable_reception_failure(exc)
    if tuple(expression for _move, expression in validated_rows) != tuple(
        expressions
    ):
        raise CMEEStage1ContractError(
            "MEANING_REALIZATION_CAUSAL_TRACE_GAP"
        )
    return tuple(expressions)


def _build_source_grounded_reception_expressions(
    *,
    source: AdmittedTextSource,
    phase_A: "Stage1SubjectivePlanningInputs",
    projection: EmlisStage1Projection,
    selected_grounded_plan: GroundedObservationPlan,
    reception_plan: GroundedHumanReceptionPlan,
    recovery_stage: str,
    authority_expressions: (
        tuple[SourceGroundedRealizableReceptionExpressionV1, ...] | None
    ) = None,
) -> tuple[SourceGroundedRealizableReceptionExpressionV1, ...]:
    """Expose the derived rows without making them their own authority."""

    if authority_expressions is None:
        return _derive_source_grounded_reception_expression_authority(
            source=source,
            phase_A=phase_A,
            projection=projection,
            selected_grounded_plan=selected_grounded_plan,
            reception_plan=reception_plan,
            recovery_stage=recovery_stage,
        )
    if (
        type(authority_expressions) is not tuple
        or not authority_expressions
        or any(
            type(expression)
            is not SourceGroundedRealizableReceptionExpressionV1
            for expression in authority_expressions
        )
    ):
        raise CMEEStage1ContractError(
            "MEANING_REALIZATION_CAUSAL_TRACE_GAP"
        )
    return authority_expressions


def compile_stage1_response(
    *,
    source: AdmittedTextSource,
    grounded_graph: GroundedMeaningGraph,
    parent_plan: ExperiencePlan,
    grounded_plan: GroundedObservationPlan,
) -> tuple[EmlisStage1Projection, tuple[RealizedSentenceUnit, ...]]:
    """Run meaning selection, then the canonical grounded surface owner."""

    from . import emlis_stage1_composition as composition

    phase_A = build_subjective_planning_inputs(
        source=source,
        grounded_graph=grounded_graph,
        parent_plan=parent_plan,
        grounded_plan=grounded_plan,
    )
    meaning_plan = composition.project_subjective_meaning_plan(phase_A)
    projection = seal_stage1_projection(phase_A, meaning_plan)

    resolver = build_evidence_span_resolver(
        source.evidence_spans,
        current_input=source.normalized_current_input,
    )
    # Local import avoids the existing emlis_v1a -> response import cycle.
    from .emlis_v1a import _cmee_semantic_reception_plan

    grounded_material_selected = bool(
        projection.projection_branch is SubjectiveProjectionBranch.NORMAL
        and grounded_plan.input_profile.material_quality == "grounded"
        and grounded_plan.safety_policy.safety_kind
        == TRIAGE_SAFE_OBSERVATION
    )
    selected_material_quality = (
        "grounded" if grounded_material_selected else "limited_grounding"
    )
    reception_plan = _cmee_semantic_reception_plan(
        grounded_plan,
        resolver,
        material_quality=selected_material_quality,
    )
    selected_grounded_plan = replace(
        grounded_plan,
        input_profile=replace(
            grounded_plan.input_profile,
            material_quality=selected_material_quality,
        ),
        response_plan=replace(
            grounded_plan.response_plan,
            response_kind=(
                "normal_observation"
                if grounded_material_selected
                else "limited_grounding_observation"
            ),
            human_reception_plan=reception_plan,
        ),
        surface_policy=replace(
            grounded_plan.surface_policy,
            hedge_policy=(
                "single_input_scope"
                if grounded_material_selected
                else "limited_single_input_scope"
            ),
        ),
    )
    selected_grounded_plan = _inherit_projection_observation_coverage(
        source=source,
        grounded_graph=grounded_graph,
        grounded_plan=selected_grounded_plan,
        projection=projection,
    )
    selected_plan_issues = validate_grounded_observation_plan(
        selected_grounded_plan,
        resolver,
    )
    selected_reception_acts = _ordered(
        row.reception_act for row in reception_plan.moves
    )
    if (
        selected_plan_issues
        or selected_reception_acts
        != projection.retained_reception_act_ids
    ):
        raise CMEEStage1ContractError(
            "stage1_v2_grounded_surface_plan_invalid"
        )

    try:
        base_sentence_plan = build_grounded_sentence_plan(
            selected_grounded_plan,
            resolver,
            recovery_stage="full",
        )
    except GroundedSentenceSurfaceError:
        raise CMEEStage1ContractError(
            "stage1_no_hard_valid_realization"
        ) from None
    hard_valid_candidates: list[
        tuple[
            GroundedSentencePlan,
            GroundedSurfaceResult,
            GroundedHumanReceptionSurface,
            tuple[SentenceSurfacePlacement, ...],
            tuple[int, int, int, int],
            str,
        ]
    ] = []
    for recovery_stage in GROUND_RECOVERY_STAGES:
        try:
            sentence_plan = (
                base_sentence_plan
                if recovery_stage == "full"
                else build_reception_recovery_sentence_plan(
                    base_sentence_plan,
                    selected_grounded_plan,
                    resolver,
                    recovery_stage=recovery_stage,
                )
            )
        except GroundedSentenceSurfaceError:
            continue
        sentence_issues = validate_grounded_sentence_plan(
            sentence_plan,
            selected_grounded_plan,
            resolver,
        )
        if sentence_issues:
            continue
        authority_expressions = (
            _derive_source_grounded_reception_expression_authority(
                source=source,
                phase_A=phase_A,
                projection=projection,
                selected_grounded_plan=selected_grounded_plan,
                reception_plan=reception_plan,
                recovery_stage=recovery_stage,
            )
        )
        expressions = _build_source_grounded_reception_expressions(
            source=source,
            phase_A=phase_A,
            projection=projection,
            selected_grounded_plan=selected_grounded_plan,
            reception_plan=reception_plan,
            recovery_stage=recovery_stage,
            authority_expressions=authority_expressions,
        )
        _validate_selected_reception_expression_lineage(
            phase_A=phase_A,
            projection=projection,
            reception_plan=reception_plan,
            recovery_stage=recovery_stage,
            expressions=expressions,
            authority_expressions=authority_expressions,
        )
        reception_lines = tuple(
            line
            for line in sentence_plan.lines
            if line.binding.line_role == "human_follow"
        )
        if len(reception_lines) != 1:
            raise CMEEStage1ContractError(
                "REALIZABLE_RECEPTION_EXPRESSION_VISIBLE_BINDING_GAP"
            )
        try:
            human_reception_surface = (
                realize_source_grounded_human_reception(
                    reception_plan,
                    expressions,
                    {item.nucleus_id: item for item in selected_grounded_plan.nuclei},
                    resolver,
                    plan=selected_grounded_plan,
                    recovery_stage=recovery_stage,
                    clause_plans=(
                        reception_lines[0].reception_clause_plans
                    ),
                )
            )
            surface_result, reception_placements = (
                realize_grounded_sentence_plan_with_human_reception(
                    sentence_plan,
                    selected_grounded_plan,
                    resolver,
                    human_reception_surface=human_reception_surface,
                )
            )
        except GroundedHumanReceptionSurfaceError as exc:
            if str(exc) in _REALIZABLE_RECEPTION_NAMED_FAILURES:
                _raise_realizable_reception_failure(exc)
            continue
        except GroundedSentenceSurfaceError as exc:
            if "REALIZABLE_RECEPTION_EXPRESSION_VISIBLE_BINDING_GAP" in str(exc):
                raise CMEEStage1ContractError(
                    "REALIZABLE_RECEPTION_EXPRESSION_VISIBLE_BINDING_GAP"
                ) from None
            continue
        surface_issues = validate_grounded_surface_result(
            surface_result,
            sentence_plan,
            selected_grounded_plan,
            resolver,
        )
        if surface_issues:
            continue
        try:
            gate_report = evaluate_grounded_observation_gate(
                plan=selected_grounded_plan,
                sentence_plan=sentence_plan,
                surface_result=surface_result,
                resolver=resolver,
                product_readfeel_status="not_evaluated",
                require_body_inverse=True,
            )
            inverse_report = evaluate_grounded_surface_body_inverse(
                body=surface_result.text.encode("utf-8"),
                plan=selected_grounded_plan,
                sentence_plan=sentence_plan,
                resolver=resolver,
            )
        except (AttributeError, KeyError, TypeError, UnicodeError, ValueError):
            continue
        if not gate_report.passed or not inverse_report.passed:
            continue
        if not _grounded_surface_projection_trace_closed(
            source=source,
            grounded_graph=grounded_graph,
            grounded_plan=selected_grounded_plan,
            projection=projection,
            surface_result=surface_result,
        ):
            continue
        retention_score = (
            len(surface_result.covered_required_nucleus_ids) * 100
            + len(surface_result.covered_required_relation_ids) * 10
            + int(surface_result.human_follow_covered) * 2
            + int(surface_result.fact_boundary_covered)
        )
        specificity_score = (
            inverse_report.source_anchor_count * 100
            + sum(
                len(row.binding.evidence_span_ids)
                + len(row.binding.nucleus_ids)
                + len(row.binding.relation_ids)
                for row in surface_result.lines
            )
        )
        distinctness_score = (
            int(gate_report.all_reception_gates_passed) * 100
            - gate_report.repeated_long_anchor_count
            - int(gate_report.mechanical_restatement_detected)
        )
        naturalness_score = (
            len(GROUND_RECOVERY_STAGES)
            - GROUND_RECOVERY_STAGES.index(recovery_stage)
        )
        hard_valid_candidates.append(
            (
                sentence_plan,
                surface_result,
                human_reception_surface,
                reception_placements,
                (
                    retention_score,
                    specificity_score,
                    distinctness_score,
                    naturalness_score,
                ),
                hashlib.sha256(
                    surface_result.text.encode("utf-8")
                ).hexdigest(),
            )
        )
    if not hard_valid_candidates:
        raise CMEEStage1ContractError("stage1_no_hard_valid_realization")

    text_frequency = {
        text_hash: sum(
            candidate_hash == text_hash
            for *_head, candidate_hash in hard_valid_candidates
        )
        for *_head, text_hash in hard_valid_candidates
    }
    scored_candidates = tuple(
        (
            sentence_plan,
            surface_result,
            human_reception_surface,
            reception_placements,
            (*score, -text_frequency[text_hash]),
            text_hash,
        )
        for (
            sentence_plan,
            surface_result,
            human_reception_surface,
            reception_placements,
            score,
            text_hash,
        )
        in hard_valid_candidates
    )
    (
        selected_sentence_plan,
        selected_surface,
        selected_human_reception_surface,
        selected_reception_placements,
        selection_score,
        _text_hash,
    ) = (
        sorted(
            scored_candidates,
            key=lambda row: (
                *(-value for value in row[4]),
                row[0].recovery_stage,
            ),
        )[0]
    )
    candidate_set_material = (
        stage1_projection_artifact_ref(projection),
        tuple(
            (
                sentence_plan.recovery_stage,
                score,
                text_hash,
            )
            for (
                sentence_plan,
                _surface,
                _human_surface,
                _placements,
                score,
                text_hash,
            )
            in scored_candidates
        ),
    )
    candidate_set_ref = "grounded-surface-candidate-set-" + hashlib.sha256(
        b"cocolon.emlis.grounded_surface.candidate_set.v1\0"
        + stage1_canonical_json_bytes(candidate_set_material)
    ).hexdigest()
    selected_units = _adapt_grounded_surface_to_v2_realized_units(
        source=source,
        projection=projection,
        grounded_plan=selected_grounded_plan,
        sentence_plan=selected_sentence_plan,
        surface_result=selected_surface,
        human_reception_surface=selected_human_reception_surface,
        reception_placements=selected_reception_placements,
        selection_score=selection_score,
        hard_valid_candidate_count=len(scored_candidates),
        candidate_set_ref=candidate_set_ref,
        grounded_graph=grounded_graph,
        parent_plan=parent_plan,
    )
    return projection, selected_units


def _compile_stage1_response_v2_candidate(
    *,
    source: AdmittedTextSource,
    grounded_graph: GroundedMeaningGraph,
    parent_plan: ExperiencePlan,
    grounded_plan: GroundedObservationPlan,
) -> tuple[EmlisStage1Projection, tuple[RealizedSentenceUnit, ...]]:
    """Compatibility-only name for frozen private V2 replay callers."""

    return compile_stage1_response(
        source=source,
        grounded_graph=grounded_graph,
        parent_plan=parent_plan,
        grounded_plan=grounded_plan,
    )


def _compile_stage1_response_v1_legacy(
    *,
    source: AdmittedTextSource,
    grounded_graph: GroundedMeaningGraph,
    parent_plan: ExperiencePlan,
    grounded_plan: GroundedObservationPlan,
) -> tuple[EmlisStage1Projection, tuple[RealizedSentenceUnit, ...]]:
    """Retain the pre-cutover V1 compiler for isolated historical tests.

    The active facade and runner never call this function.
    """

    projection = build_stage1_semantic_projection(
        source=source,
        grounded_graph=grounded_graph,
        parent_plan=parent_plan,
        grounded_plan=grounded_plan,
    )
    candidate_set = build_stage1_realization_candidate_set(
        projection=projection,
        grounded_graph=grounded_graph,
        parent_plan=parent_plan,
    )
    selected = select_stage1_realization_candidate(
        candidate_set,
        projection=projection,
        grounded_graph=grounded_graph,
        parent_plan=parent_plan,
    )
    return projection, selected


__all__ = [
    "CMEE_STAGE1_MICROGRAMMAR_INVENTORY_DOCS_BYTES",
    "CMEE_STAGE1_MICROGRAMMAR_INVENTORY_DOCS_SHA256",
    "CMEE_STAGE1_MICROGRAMMAR_INVENTORY_TUPLE",
    "CMEE_STAGE1_MICROGRAMMAR_POLICY_VERSION",
    "EmlisUtteranceState",
    "INTERPRETATION_CANDIDATE_KIND_CAP",
    "INTERPRETATION_CANDIDATE_POOL_CAP",
    "INTERPRETATION_MATRIX_EXACT13",
    "INTERPRETATION_MATRIX_EXACT16",
    "LAYER1_OBSERVATION_CONTRIBUTION_CAP",
    "OBSERVATION_SEMANTIC_KEY_VERSION",
    "UtterancePhase",
    "build_emlis_meaning_field",
    "build_allowed_reception_opportunity_envelope",
    "build_interpretation_candidate_pool",
    "build_layer1_semantics",
    "build_premeaning_grounded_inputs",
    "build_subjective_planning_inputs",
    "build_surface_composition_inputs",
    "build_stage1_semantic_projection",
    "build_stage1_post_selection_reception_records",
    "build_stage1_realization_candidate_set",
    "compile_stage1_response",
    "classify_affect_intensity",
    "classify_observation_depth",
    "classify_subjective_depth",
    "observation_depth_class",
    "plan_layer1_observation",
    "plan_layer2_subjectivity",
    "project_direct_argument_bindings",
    "resolve_candidate_for_contribution",
    "resolve_qualifier_value",
    "seal_stage1_projection",
    "select_stage1_realization_candidate",
    "validate_emlis_meaning_field",
    "validate_interpretation_candidate_pool",
    "validate_layer1_observation_plan",
    "validate_layer2_subjective_plan",
    "validate_allowed_reception_opportunity_envelope",
    "validate_reception_asset_mapping",
]
