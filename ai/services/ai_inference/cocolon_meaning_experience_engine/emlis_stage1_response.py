# -*- coding: utf-8 -*-
from __future__ import annotations

"""Deterministic Stage 1 interpretation and Layer 1 / Layer 2 planning.

This module is deliberately private and side-effect free.  It does not call
the legacy realizer, mutate an :class:`ExperiencePlan`, or create a second plan
owner.  The complete builder consumes the already-frozen source, grounded
semantic plan, graph and parent plan.  The smaller builders also support a
single canonical path through that same frozen source and grounded plan.

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
import json
import unicodedata
from typing import Any, Iterable, Mapping, Optional, Sequence, Tuple

from emlis_ai_current_input_bundle import build_emlis_current_input_bundle
from emlis_ai_evidence_ledger_service import build_evidence_span_resolver
from emlis_ai_grounded_observation_plan import (
    GroundedHumanReceptionPlan,
    GroundedObservationPlan,
    build_grounded_observation_plan,
    validate_grounded_observation_plan,
)
from emlis_ai_safety_triage import (
    TRIAGE_SAFE_OBSERVATION,
    TRIAGE_SELF_DENIAL_SAFE_STATE_ANSWER,
)

from .contracts import (
    AffectCategory,
    AffectIntensity,
    ArgumentBinding,
    ArgumentRole,
    CMEE_GROUNDED_GRAPH_SCHEMA_VERSION,
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
    CMEE_STAGE1_RESPONSE_SCHEMA_VERSION,
    CMEE_STAGE1_VALUE_POLICY_REF,
    CMEEStage1ContractError,
    ClauseFrame,
    EmlisInterpretationCandidate,
    EmlisMeaningField,
    EmlisStage1Projection,
    EmlisSubjectiveClaim,
    EmlisTraceClaimDomain,
    EpistemicState,
    ExperiencePlan,
    GenerationRequest,
    GroundedMeaningGraph,
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
    RouteBDisposition,
    SemanticOperator,
    StanceOperator,
    SubjectiveDepthClass,
    SubjectiveMode,
    SubjectiveOperator,
    SubjectiveProposition,
    TemperatureClass,
    recompute_stage1_identity,
    stage1_canonical_json_bytes,
    stage1_subjective_forbidden_promotions,
    stage1_subjective_semantic_key,
    stage1_value_principle_ref,
    validate_stage1_identity,
    validate_stage1_projection,
    validate_stage1_sentence_unit,
)
from .source_kernel import (
    AdmittedTextSource,
    build_source_owner_universe,
    freeze_text_source,
    validate_evidence_refs,
)


INTERPRETATION_CANDIDATE_POOL_CAP = 16
INTERPRETATION_CANDIDATE_KIND_CAP = 2
LAYER1_OBSERVATION_CONTRIBUTION_CAP = 5
OBSERVATION_SEMANTIC_KEY_VERSION = (
    "cocolon.cmee.v1a.emlis_stage1.observation_semantic_key.v1"
)

CMEE_STAGE1_MICROGRAMMAR_POLICY_VERSION = (
    "cocolon.emlis.stage1.microgrammar.v1"
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
                    "大切な動きだと考えます",
                    "見過ごせないことだと考えます",
                ),
            ),
            (
                "EMLIS_AFFECT_V1",
                (
                    ("CONCERN", "気がかりです"),
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
            ("SIMULTANEOUS", ("同時に",)),
            ("CONTRASTIVE", ("一方で", "それでも")),
            ("TEMPORAL", ("そのあと", "そこから")),
            ("CONTINUATIVE", ("また", "そのことに")),
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
            ("LAYER_2", "APPRAISE_AS_MATERIAL", "CONTINUATIVE"),
            ("LAYER_2", "PROTECT_VALUE_BOUNDARY", "CONTINUATIVE"),
            ("LAYER_2", "TAKE_RELATIONAL_STANCE", "CONTINUATIVE"),
            ("LAYER_2", "COUNTER_SPECIFIC_PROMOTION", "BOUNDED_CONTRAST"),
        ),
    ),
    (
        "modality_wrappers",
        (
            ("fact", ""),
            ("feeling", "という気持ち"),
            ("wish", "という願い"),
            ("intention", "という方向"),
            ("possibility", "可能性として"),
            ("uncertain", "まだ決まっていないものとして"),
            ("refusal", "しない／したくないという境界"),
        ),
    ),
    (
        "time_wrappers",
        (
            ("current_input", "今ここにある"),
            ("present", "今ここにある"),
            ("past", "その時にあった"),
            ("future", "これからに向いた"),
            ("continuing", "今も続く"),
            ("past_to_present", "その時から今に残る"),
            ("present_to_future", "今から先へ向く"),
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
            ("FEEL_TOWARD", "CONCERN", "EMLIS_AFFECT_V1", "気がかりです", ""),
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
        "layer1_direct_slots",
        (
            ("PRESENT_STATE", "という状態が"),
            ("PRESENT_DIRECTION", "という方向が"),
            ("PRESENT_BURDEN", "という負荷が"),
            ("PRESENT_CHANGE", "という変化が"),
            ("PRESENT_ACTUAL_OUTPUT", "という出来事が"),
            ("PRESENT_UNFINISHED", "ということが"),
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
            ("FEEL_TOWARD", "について"),
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
        "structural_tokens",
        (
            ("speaker", "Emlis"),
            ("topic_particle", "は"),
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
            ("wrapper_placement", "time_after_topic_then_modality_before_predicate"),
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
            ("max_graphemes", 16),
            ("over_limit_selection", "semantic_boundary_or_stop"),
            ("inserted_token_count", 0),
            ("full_value_replay_over_limit", False),
        ),
    ),
    (
        "quote_policy",
        (
            ("l1_max_graphemes", 16),
            ("l1_max_per_sentence", 1),
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
            ("format", "move:{basis_anchor_ref}@cocolon.emlis.stage1.microgrammar.v1"),
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
            ("primary_variant_id", "01-primary.v1"),
            ("alternate_variant_id", "02-alternate.v1"),
            ("max_candidates", 2),
            ("first_predicate_alternate_only", True),
            ("connective_alternate_only_without_predicate_alternate", True),
            ("multiple_slot_replacement", False),
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
_CONNECTIVE_FAMILIES = dict(_MICROGRAMMAR_SECTIONS["connective_families"])
_OPERATOR_CONNECTIVES = {
    (layer, operator): family
    for layer, operator, family in _MICROGRAMMAR_SECTIONS[
        "operator_connective_rows"
    ]
}
_MODALITY_WRAPPERS = dict(_MICROGRAMMAR_SECTIONS["modality_wrappers"])
_TIME_WRAPPERS = dict(_MICROGRAMMAR_SECTIONS["time_wrappers"])
_LAYER1_DIRECT_SLOTS = dict(_MICROGRAMMAR_SECTIONS["layer1_direct_slots"])
_LAYER1_RELATION_SLOTS = dict(_MICROGRAMMAR_SECTIONS["layer1_relation_slots"])
_LAYER2_CASE_PARTICLES = dict(_MICROGRAMMAR_SECTIONS["layer2_case_particles"])
_STRUCTURAL_TOKENS = dict(_MICROGRAMMAR_SECTIONS["structural_tokens"])
_TOPIC_SPEAKER_POLICY = dict(_MICROGRAMMAR_SECTIONS["topic_speaker_policy"])
_REFERENCE_MODE_POLICY = dict(_MICROGRAMMAR_SECTIONS["reference_mode_policy"])
_QUOTE_POLICY = dict(_MICROGRAMMAR_SECTIONS["quote_policy"])
_ROLE_ANCHOR_POLICY = dict(_MICROGRAMMAR_SECTIONS["role_anchor_policy"])
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
_EVENT_KINDS = frozenset({"event", "action", "change"})
_RESIDUE_KINDS = frozenset(
    {"reaction", "residue", "lingering_state", "unfinished", "uncertainty"}
)
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

# Canonical §8.1.1 cross-field allowlist: nine kinds and exact thirteen
# kind/operator/relation combinations.  Optional EXPERIENCER is validated
# separately for the three NO_RELATION rows which permit it.
INTERPRETATION_MATRIX_EXACT13 = (
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
        RouteBDisposition.SOURCE_EXPLICIT_VISIBLE,
        RouteBDisposition.SUPPLEMENTAL_USER_VISIBLE,
    }
    visible_claim_ids: set[str] = set()
    for owner_id in visible_owners:
        row = disposition_by_owner.get(owner_id)
        if row is None or row.route_b_disposition not in positive:
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


def _validate_canonical_semantic_inputs(
    source: AdmittedTextSource,
    grounded_plan: GroundedObservationPlan,
    graph: GroundedMeaningGraph,
    parent_plan: ExperiencePlan,
) -> None:
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
        issues = validate_grounded_observation_plan(grounded_plan, resolver)
        expected_plan = build_grounded_observation_plan(
            expected_source.normalized_current_input,
            evidence_spans=expected_source.evidence_spans,
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
    if issues or grounded_plan != expected_plan:
        raise CMEEStage1ContractError("stage1_grounded_observation_plan_noncanonical")
    if graph != expected_graph:
        raise CMEEStage1ContractError("stage1_grounded_graph_noncanonical")
    if parent_plan != expected_parent:
        raise CMEEStage1ContractError("stage1_parent_plan_noncanonical")


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


def _qualifiers(meta: Optional[object], *, role: Optional[str] = None) -> tuple[str, ...]:
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
    return (
        _PROVISIONAL_QUALIFIER,
        *(f"{prefix}{name}:{value}" for name, value in values if value),
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
    if (
        kind in _UNFINISHED_KINDS
        or modality == "uncertain"
        or "operator:uncertainty" in attribute_codes
    ):
        return InterpretationKind.UNFINISHED, SemanticOperator.PRESENT_UNFINISHED
    return InterpretationKind.DIRECT_STATE, SemanticOperator.PRESENT_STATE


def _direct_argument_bindings(
    node: MeaningNode,
    meta: Optional[object],
) -> tuple[ArgumentBinding, ...]:
    semantic_ref = _node_ref(node.node_id)
    bindings = [ArgumentBinding(ArgumentRole.PRIMARY, semantic_ref)]
    frame = getattr(meta, "semantic_frame", None)
    modality = _enum_or_text(getattr(frame, "modality", "")).lower()
    actor = _enum_or_text(getattr(frame, "actor", "")).lower()
    if actor in {"current_user", "user"} and modality in {
        "feeling",
        "wish",
        "intention",
        "refusal",
        "uncertain",
    }:
        # The experiencer binding reuses the same canonical source proposition;
        # it never creates a person node or a free-form semantic ref.
        bindings.append(ArgumentBinding(ArgumentRole.EXPERIENCER, semantic_ref))
    return tuple(bindings)


def _validate_interpretation_matrix(
    candidate: EmlisInterpretationCandidate,
) -> None:
    matches = tuple(
        row
        for row in INTERPRETATION_MATRIX_EXACT13
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
    direct_optional_experiencer = (
        candidate.relation_operator is RelationOperator.NO_RELATION_CLAIM
        and actual_roles
        in {
            required_roles,
            (*required_roles, ArgumentRole.EXPERIENCER),
        }
    )
    if not direct_optional_experiencer and actual_roles != required_roles:
        raise CMEEStage1ContractError("stage1_interpretation_matrix_invalid")
    if candidate.relation_operator is RelationOperator.NO_RELATION_CLAIM:
        if candidate.relation_basis_refs:
            raise CMEEStage1ContractError("stage1_interpretation_matrix_invalid")
    elif len(candidate.relation_basis_refs) != 1:
        raise CMEEStage1ContractError("stage1_interpretation_matrix_invalid")


def _is_direction(node: MeaningNode, meta: Optional[object]) -> bool:
    return _direct_shape(node, meta)[0] is InterpretationKind.DIRECT_DIRECTION


def _is_burden(node: MeaningNode, meta: Optional[object]) -> bool:
    return _direct_shape(node, meta)[1] is SemanticOperator.PRESENT_BURDEN


def _relation_shape(
    edge: MeaningEdge,
    node_by_id: Mapping[str, MeaningNode],
    binding: _PlanBinding,
) -> Optional[
    tuple[
        InterpretationKind,
        SemanticOperator,
        RelationOperator,
        tuple[ArgumentBinding, ...],
    ]
]:
    relation = _enum_or_text(edge.relation)
    source = node_by_id[edge.source_node_id]
    target = node_by_id[edge.target_node_id]
    source_ref = _node_ref(source.node_id)
    target_ref = _node_ref(target.node_id)
    source_meta = binding.node_meta.get(source.node_id)
    target_meta = binding.node_meta.get(target.node_id)

    def symmetric(
        kind: InterpretationKind,
        operator: RelationOperator,
    ) -> tuple[
        InterpretationKind,
        SemanticOperator,
        RelationOperator,
        tuple[ArgumentBinding, ...],
    ]:
        left, right = sorted((source_ref, target_ref))
        return (
            kind,
            SemanticOperator.SYNTHESIZE_RELATION,
            operator,
            (
                ArgumentBinding(ArgumentRole.LEFT, left),
                ArgumentBinding(ArgumentRole.RIGHT, right),
            ),
        )

    if relation == "coexistence":
        return symmetric(InterpretationKind.COEXISTENCE, RelationOperator.COEXISTS_WITH)
    if relation == "contrast":
        return symmetric(InterpretationKind.TENSION, RelationOperator.TENSION_WITH)
    if relation in {"wish_and_constraint", "preserves_despite", "attempt_and_block"}:
        direction: Optional[MeaningNode] = None
        burden: Optional[MeaningNode] = None
        if _is_direction(source, source_meta) and _is_burden(target, target_meta):
            direction, burden = source, target
        elif _is_burden(source, source_meta) and _is_direction(target, target_meta):
            direction, burden = target, source
        if direction is not None and burden is not None:
            operator = (
                RelationOperator.COEXISTS_WITH
                if relation == "wish_and_constraint"
                else RelationOperator.TENSION_WITH
            )
            return (
                InterpretationKind.DIRECTION_UNDER_BURDEN,
                SemanticOperator.SYNTHESIZE_RELATION,
                operator,
                (
                    ArgumentBinding(
                        ArgumentRole.LEFT,
                        _node_ref(direction.node_id),
                    ),
                    ArgumentBinding(
                        ArgumentRole.RIGHT,
                        _node_ref(burden.node_id),
                    ),
                ),
            )
        return None
    if relation == "action_supports_change":
        if (
            _enum_or_text(source.node_kind).lower() not in _ACTION_KINDS
            or _enum_or_text(target.node_kind).lower() not in _CHANGE_KINDS
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
    if relation in {"temporal_before_after", "shift_from_to"}:
        if not (
            _enum_or_text(source.node_kind).lower() in _EVENT_KINDS
            and _enum_or_text(target.node_kind).lower() in _RESIDUE_KINDS
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
    if relation == "user_stated_cause":
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


def _candidate_from_direct(
    graph: GroundedMeaningGraph,
    node: MeaningNode,
    meta: Optional[object],
) -> EmlisInterpretationCandidate:
    kind, semantic_operator = _direct_shape(node, meta)
    semantic_ref = _node_ref(node.node_id)
    candidate = EmlisInterpretationCandidate(
        schema_version=CMEE_STAGE1_RESPONSE_SCHEMA_VERSION,
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
        required_qualifiers=_qualifiers(meta),
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
    for argument in arguments:
        meta = binding.node_meta.get(_local_ref(argument.semantic_ref))
        qualifiers.extend(_qualifiers(meta, role=argument.role.value)[1:])
    candidate = EmlisInterpretationCandidate(
        schema_version=CMEE_STAGE1_RESPONSE_SCHEMA_VERSION,
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
        shape = _relation_shape(edge, node_by_id, binding)
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
        candidate = _candidate_from_relation(graph, edge, binding, shape)
        rows.append(
            _CandidateRow(
                candidate=candidate,
                required=required,
                is_relation=True,
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
            graph, node, binding.node_meta.get(node.node_id)
        )
        rows.append(
            _CandidateRow(
                candidate=candidate,
                required=required,
                is_relation=False,
                retention_rank=_retention_rank(
                    binding.node_meta[node.node_id], required=required
                ),
                source_order=binding.source_order.get(node.node_id, 0),
            )
        )

    if not rows:
        raise CMEEStage1ContractError("stage1_candidate_pool_empty")
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

    selected: list[_CandidateRow] = []
    kind_counts: dict[InterpretationKind, int] = {}
    for row in rows:
        count = kind_counts.get(row.candidate.candidate_kind, 0)
        if count >= INTERPRETATION_CANDIDATE_KIND_CAP:
            if row.required:
                raise CMEEStage1ContractError("stage1_required_candidate_overflow")
            continue
        selected.append(row)
        kind_counts[row.candidate.candidate_kind] = count + 1

    if len(selected) > INTERPRETATION_CANDIDATE_POOL_CAP:
        if any(row.required for row in selected[INTERPRETATION_CANDIDATE_POOL_CAP:]):
            raise CMEEStage1ContractError("stage1_required_candidate_overflow")
        selected = selected[:INTERPRETATION_CANDIDATE_POOL_CAP]
    if not selected or not any(row.required for row in selected):
        raise CMEEStage1ContractError("stage1_required_candidate_missing")
    return tuple(selected)


def build_interpretation_candidate_pool(
    grounded_graph: GroundedMeaningGraph,
    parent_plan: ExperiencePlan,
    *,
    source: AdmittedTextSource,
    grounded_plan: GroundedObservationPlan,
) -> tuple[EmlisInterpretationCandidate, ...]:
    """Build the canonical bounded provisional InterpretationCandidate pool."""

    rows = _candidate_rows(
        grounded_graph,
        parent_plan,
        source=source,
        grounded_plan=grounded_plan,
    )
    candidates = tuple(row.candidate for row in rows)
    if len(candidates) > INTERPRETATION_CANDIDATE_POOL_CAP:
        raise CMEEStage1ContractError("stage1_candidate_pool_cap_exceeded")
    for candidate in candidates:
        validate_stage1_identity(candidate)
    return candidates


def validate_interpretation_candidate_pool(
    candidates: Sequence[EmlisInterpretationCandidate],
    *,
    grounded_graph: GroundedMeaningGraph,
    parent_plan: ExperiencePlan,
    source: AdmittedTextSource,
    grounded_plan: GroundedObservationPlan,
) -> None:
    if type(candidates) is not tuple:
        raise CMEEStage1ContractError("stage1_candidate_pool_not_tuple")
    expected = build_interpretation_candidate_pool(
        grounded_graph,
        parent_plan,
        source=source,
        grounded_plan=grounded_plan,
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
            or row.route_b_disposition
            is not RouteBDisposition.UNKNOWN_PRESERVED_LIMITED
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


def build_emlis_meaning_field(
    grounded_graph: GroundedMeaningGraph,
    parent_plan: ExperiencePlan,
    candidates: Sequence[EmlisInterpretationCandidate],
    *,
    source: AdmittedTextSource,
    grounded_plan: GroundedObservationPlan,
) -> EmlisMeaningField:
    """Project the canonical pool into Emlis request-local attention slots."""

    candidate_tuple = tuple(candidates)
    validate_interpretation_candidate_pool(
        candidate_tuple,
        grounded_graph=grounded_graph,
        parent_plan=parent_plan,
        source=source,
        grounded_plan=grounded_plan,
    )
    rows = _candidate_rows(
        grounded_graph,
        parent_plan,
        source=source,
        grounded_plan=grounded_plan,
    )
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
        schema_version=CMEE_STAGE1_RESPONSE_SCHEMA_VERSION,
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


def validate_emlis_meaning_field(
    meaning_field: EmlisMeaningField,
    *,
    candidates: Sequence[EmlisInterpretationCandidate],
    grounded_graph: GroundedMeaningGraph,
    parent_plan: ExperiencePlan,
    source: AdmittedTextSource,
    grounded_plan: GroundedObservationPlan,
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
    optional = [
        row
        for row in rows
        if not row.required
    ]
    # Optional meanings deepen a single required observation by exact1.  They
    # never inflate an already-layered/dense required set or manufacture depth
    # from sentence budget alone.
    selected_optional = optional[:1] if len(required) == 1 else []
    return tuple((*required, *selected_optional))


def plan_layer1_observation(
    grounded_graph: GroundedMeaningGraph,
    parent_plan: ExperiencePlan,
    candidates: Sequence[EmlisInterpretationCandidate],
    meaning_field: EmlisMeaningField,
    *,
    source: AdmittedTextSource,
    grounded_plan: GroundedObservationPlan,
) -> tuple[PlannedObservationContribution, ...]:
    """Select exact-cover Layer 1 contributions and suppress optional tail."""

    candidate_tuple = tuple(candidates)
    validate_emlis_meaning_field(
        meaning_field,
        candidates=candidate_tuple,
        grounded_graph=grounded_graph,
        parent_plan=parent_plan,
        source=source,
        grounded_plan=grounded_plan,
    )
    rows = _candidate_rows(
        grounded_graph,
        parent_plan,
        source=source,
        grounded_plan=grounded_plan,
    )
    selected = _selected_contribution_candidates(rows)
    contributions: list[PlannedObservationContribution] = []
    for row in selected:
        candidate = row.candidate
        contribution = PlannedObservationContribution(
            schema_version=CMEE_STAGE1_RESPONSE_SCHEMA_VERSION,
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

    candidates = build_interpretation_candidate_pool(
        grounded_graph,
        parent_plan,
        source=source,
        grounded_plan=grounded_plan,
    )
    meaning_field = build_emlis_meaning_field(
        grounded_graph,
        parent_plan,
        candidates,
        source=source,
        grounded_plan=grounded_plan,
    )
    contributions = plan_layer1_observation(
        grounded_graph,
        parent_plan,
        candidates,
        meaning_field,
        source=source,
        grounded_plan=grounded_plan,
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
        schema_version=CMEE_STAGE1_RESPONSE_SCHEMA_VERSION,
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
) -> None:
    if type(claims) is not tuple:
        raise CMEEStage1ContractError("stage1_subjective_plan_type_invalid")
    expected = plan_layer2_subjectivity(
        source=source,
        grounded_graph=grounded_graph,
        parent_plan=parent_plan,
        grounded_plan=grounded_plan,
        observation_contributions=observation_contributions,
    )
    if claims != expected:
        raise CMEEStage1ContractError("stage1_subjective_plan_noncanonical")


def build_stage1_semantic_projection(
    *,
    source: AdmittedTextSource,
    grounded_graph: GroundedMeaningGraph,
    parent_plan: ExperiencePlan,
    grounded_plan: GroundedObservationPlan,
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
    )
    claims = plan_layer2_subjectivity(
        source=source,
        grounded_graph=grounded_graph,
        parent_plan=parent_plan,
        grounded_plan=grounded_plan,
        observation_contributions=contributions,
    )
    reception_plan = _semantic_reception_asset(
        source=source,
        grounded_plan=grounded_plan,
    )
    projection = EmlisStage1Projection(
        schema_version=CMEE_STAGE1_RESPONSE_SCHEMA_VERSION,
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
        or _CONNECTIVE_FAMILIES
        != dict(canonical_sections["connective_families"])
        or _OPERATOR_CONNECTIVES != expected_operator_connectives
        or _MODALITY_WRAPPERS
        != dict(canonical_sections["modality_wrappers"])
        or _TIME_WRAPPERS != dict(canonical_sections["time_wrappers"])
        or _LAYER1_DIRECT_SLOTS
        != dict(canonical_sections["layer1_direct_slots"])
        or _LAYER1_RELATION_SLOTS
        != dict(canonical_sections["layer1_relation_slots"])
        or _LAYER2_CASE_PARTICLES
        != dict(canonical_sections["layer2_case_particles"])
        or _STRUCTURAL_TOKENS
        != dict(canonical_sections["structural_tokens"])
        or _TOPIC_SPEAKER_POLICY
        != dict(canonical_sections["topic_speaker_policy"])
        or _REFERENCE_MODE_POLICY
        != dict(canonical_sections["reference_mode_policy"])
        or _QUOTE_POLICY != dict(canonical_sections["quote_policy"])
        or _ROLE_ANCHOR_POLICY
        != dict(canonical_sections["role_anchor_policy"])
        or _VARIANT_POLICY != dict(canonical_sections["variant_policy"])
        or _MICROGRAMMAR_SECTIONS.get("policy_id")
        != CMEE_STAGE1_MICROGRAMMAR_POLICY_VERSION
        or _MICROGRAMMAR_SECTIONS.get("policy_ref")
        != CMEE_STAGE1_MICROGRAMMAR_POLICY_REF
        or len(_OBSERVATION_PREDICATE_ROWS) != 12
        or len(_SUBJECTIVE_PREDICATE_ROWS) != 14
        or len(_CONNECTIVE_FAMILIES) != 7
        or len(_OPERATOR_CONNECTIVES) != 12
        or _VARIANT_POLICY.get("max_candidates") != 2
        or _VARIANT_POLICY.get("automatic_retry") != 0
        or _VARIANT_POLICY.get("post_defect_generation") != 0
        or _ROLE_ANCHOR_POLICY.get("max_graphemes") != 16
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
    if any(
        family not in _CONNECTIVE_FAMILIES
        for family in _OPERATOR_CONNECTIVES.values()
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
    rows = tuple(
        row
        for row in projection.interpretation_candidates
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
        candidate = _candidate_for_contribution(projection, contribution)
        times = tuple(
            _qualifier_value(candidate, "time_scope", role=binding.role)
            if contribution.relation_operator is not RelationOperator.NO_RELATION_CLAIM
            else _qualifier_value(candidate, "time_scope")
            for binding in contribution.argument_bindings
            if binding.role is not ArgumentRole.EXPERIENCER
        )
        return (primary, alternate) if times and set(times) == {"continuing"} else (primary, "")
    if condition != "never":
        raise CMEEStage1ContractError("stage1_microgrammar_predicate_condition_invalid")
    return primary, ""


def _subjective_predicate_spec(
    claim: EmlisSubjectiveClaim,
) -> tuple[str, str]:
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
    row = _SUBJECTIVE_PREDICATE_ROWS.get((operator.value, detail))
    if row is None:
        raise CMEEStage1ContractError("stage1_microgrammar_predicate_missing")
    return row


def _connective_family(
    *,
    layer: str,
    relation_or_operator: str,
    overall_index: int,
) -> str:
    if overall_index == 0:
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
    ordered_moves: list[tuple[str, str, str]] = []
    for ref in projection.ordered_observation_refs:
        contribution = contribution_by_id[ref]
        ordered_moves.append(
            (
                "LAYER_1",
                contribution.contribution_id,
                contribution.relation_operator.value,
            )
        )
    for ref in projection.ordered_subjective_refs:
        claim = claim_by_id[ref]
        ordered_moves.append(
            (
                "LAYER_2",
                claim.subjective_claim_id,
                claim.asserted_subjective_proposition.subjective_operator.value,
            )
        )
    for index, (layer, ref, operator) in enumerate(ordered_moves):
        family = _connective_family(
            layer=layer,
            relation_or_operator=operator,
            overall_index=index,
        )
        if len(_CONNECTIVE_FAMILIES[family]) == 2:
            return "connective", ref
    return None


def _move_ref(anchor_ref: str) -> str:
    if type(anchor_ref) is not str or not anchor_ref or "@" in anchor_ref:
        raise CMEEStage1ContractError("stage1_realization_move_anchor_invalid")
    return f"move:{anchor_ref}@{CMEE_STAGE1_MICROGRAMMAR_POLICY_VERSION}"


def _source_bound_role_surface(
    semantic_ref: str,
    grounded_graph: GroundedMeaningGraph,
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
    max_graphemes = min(
        int(_ROLE_ANCHOR_POLICY["max_graphemes"]),
        int(_QUOTE_POLICY["l1_max_graphemes"]),
        int(_QUOTE_POLICY["l2_max_graphemes"]),
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
    connective_family = _connective_family(
        layer="LAYER_1",
        relation_or_operator=contribution.relation_operator.value,
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
    frames: list[ClauseFrame] = []

    if contribution.relation_operator is RelationOperator.NO_RELATION_CLAIM:
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
        time_wrapper = _TIME_WRAPPERS.get(time_scope)
        modality_wrapper = _MODALITY_WRAPPERS.get(modality)
        direct_slot = _LAYER1_DIRECT_SLOTS.get(contribution.semantic_operator.value)
        if time_wrapper is None or modality_wrapper is None or direct_slot is None:
            raise CMEEStage1ContractError("stage1_microgrammar_inflection_missing")
        anchor_bindings = tuple(
            (
                row.semantic_ref,
                f"frame:0:argument:{row.role.value}",
            )
            for row in contribution.argument_bindings
        )
        anchor = _source_bound_role_surface(primary_ref, grounded_graph)
        parts.append(
            _SurfacePart(text=anchor, bindings=anchor_bindings)
        )
        parts.append(_part(time_wrapper, primary_ref, "frame:0:time"))
        parts.append(_part(direct_slot, primary_ref, "frame:0:case"))
        if modality_wrapper:
            parts.append(
                _part(modality_wrapper, primary_ref, "frame:0:modality")
            )
        parts.append(_part(predicate, primary_ref, "frame:0:predicate"))
        parts.append(
            _part(_STRUCTURAL_TOKENS["terminal"], primary_ref, "frame:0:terminal")
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
        for frame_index, (binding, slot_row) in enumerate(
            zip(contribution.argument_bindings, slot_rows)
        ):
            _role, prefix, suffix = slot_row
            time_scope = _qualifier_value(
                candidate, "time_scope", role=binding.role
            )
            modality = _qualifier_value(candidate, "modality", role=binding.role)
            polarity = _qualifier_value(candidate, "polarity", role=binding.role)
            time_wrapper = _TIME_WRAPPERS.get(time_scope)
            modality_wrapper = _MODALITY_WRAPPERS.get(modality)
            if time_wrapper is None or modality_wrapper is None:
                raise CMEEStage1ContractError("stage1_microgrammar_inflection_missing")
            if prefix:
                parts.append(
                    _part(
                        prefix,
                        binding.semantic_ref,
                        f"frame:{frame_index}:case_prefix",
                    )
                )
            parts.append(
                _part(
                    _source_bound_role_surface(
                        binding.semantic_ref, grounded_graph
                    ),
                    binding.semantic_ref,
                    f"frame:{frame_index}:argument:{binding.role.value}",
                )
            )
            parts.append(
                _part(
                    time_wrapper,
                    binding.semantic_ref,
                    f"frame:{frame_index}:time",
                )
            )
            if modality_wrapper:
                parts.append(
                    _part(
                        modality_wrapper,
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
            if contribution.relation_operator is RelationOperator.NO_RELATION_CLAIM:
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
) -> str:
    proposition = claim.asserted_subjective_proposition
    if (
        proposition.subjective_operator
        is SubjectiveOperator.COUNTER_SPECIFIC_PROMOTION
    ):
        mode = "explicit_emlis_counterposition"
    else:
        prior_object_count = sum(
            1
            for contribution in projection.observation_contributions
            if any(
                binding.semantic_ref == object_ref
                and binding.role is not ArgumentRole.EXPERIENCER
                for binding in contribution.argument_bindings
            )
        )
        mode = (
            "anaphoric_first"
            if prior_object_count == 1
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
    use_alternate_predicate = bool(
        composition_variant_id == _ALTERNATE_VARIANT_ID
        and alternate_target == ("predicate", claim.subjective_claim_id)
    )
    if use_alternate_predicate and not alternate_predicate:
        raise CMEEStage1ContractError("stage1_microgrammar_alternate_missing")
    predicate = alternate_predicate if use_alternate_predicate else primary_predicate
    connective_family = _connective_family(
        layer="LAYER_2",
        relation_or_operator=proposition.subjective_operator.value,
        overall_index=overall_index,
    )
    connective = _connective_token(
        connective_family,
        alternate=bool(
            composition_variant_id == _ALTERNATE_VARIANT_ID
            and alternate_target == ("connective", claim.subjective_claim_id)
        ),
    )
    object_ref = _subjective_object_ref(projection, claim)
    reference_mode = _reference_mode_for_claim(projection, claim, object_ref)
    source_modality = _source_qualifier_for_semantic_ref(
        projection,
        object_ref,
        "modality",
    )
    anchor = _source_bound_role_surface(object_ref, grounded_graph)
    time_scope = _time_scope_for_semantic_ref(projection, object_ref)
    time_wrapper = _TIME_WRAPPERS.get(time_scope)
    source_modality_wrapper = _MODALITY_WRAPPERS.get(source_modality)
    claim_modality_wrapper = _MODALITY_WRAPPERS.get(proposition.modality)
    if (
        time_wrapper is None
        or source_modality_wrapper is None
        or claim_modality_wrapper is None
    ):
        raise CMEEStage1ContractError("stage1_microgrammar_inflection_missing")
    detail = ""
    if proposition.subjective_operator is SubjectiveOperator.TAKE_RELATIONAL_STANCE:
        if proposition.stance_operator is None:
            raise CMEEStage1ContractError("stage1_microgrammar_stance_missing")
        detail = f":{proposition.stance_operator.value}"
    particle = _LAYER2_CASE_PARTICLES.get(
        f"{proposition.subjective_operator.value}{detail}"
    )
    if particle is None:
        raise CMEEStage1ContractError("stage1_microgrammar_case_frame_invalid")
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
    if explicit_speaker:
        parts.append(_part(_STRUCTURAL_TOKENS["speaker"], object_ref, "frame:0:speaker"))
        parts.append(
            _part(
                _STRUCTURAL_TOKENS["topic_particle"],
                object_ref,
                "frame:0:speaker_particle",
            )
        )
    parts.append(_part(anchor, object_ref, "frame:0:object"))
    parts.append(_part(time_wrapper, object_ref, "frame:0:time"))
    parts.append(_part(particle, object_ref, "frame:0:case"))
    if source_modality_wrapper:
        parts.append(
            _part(
                source_modality_wrapper,
                object_ref,
                "frame:0:object_modality",
            )
        )
    if claim_modality_wrapper and claim_modality_wrapper != source_modality_wrapper:
        parts.append(
            _part(
                claim_modality_wrapper,
                object_ref,
                "frame:0:modality",
            )
        )
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


def compile_stage1_response(
    *,
    source: AdmittedTextSource,
    grounded_graph: GroundedMeaningGraph,
    parent_plan: ExperiencePlan,
    grounded_plan: GroundedObservationPlan,
) -> tuple[EmlisStage1Projection, tuple[RealizedSentenceUnit, ...]]:
    """Compile one immutable Stage 1 response through the sole S5--S9 path.

    The active orchestrator calls this facade exactly once.  Candidate
    generation and selection remain bounded inside that call, so callers
    cannot accidentally install a second planner, retry, or legacy fallback.
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
    "LAYER1_OBSERVATION_CONTRIBUTION_CAP",
    "OBSERVATION_SEMANTIC_KEY_VERSION",
    "UtterancePhase",
    "build_emlis_meaning_field",
    "build_interpretation_candidate_pool",
    "build_layer1_semantics",
    "build_stage1_semantic_projection",
    "build_stage1_realization_candidate_set",
    "compile_stage1_response",
    "classify_affect_intensity",
    "classify_observation_depth",
    "classify_subjective_depth",
    "observation_depth_class",
    "plan_layer1_observation",
    "plan_layer2_subjectivity",
    "select_stage1_realization_candidate",
    "validate_emlis_meaning_field",
    "validate_interpretation_candidate_pool",
    "validate_layer1_observation_plan",
    "validate_layer2_subjective_plan",
    "validate_reception_asset_mapping",
]
