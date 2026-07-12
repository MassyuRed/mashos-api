# -*- coding: utf-8 -*-
from __future__ import annotations

"""Canonical GroundedObservationPlan contract (I1-I5).

The I1 adapter keeps the existing current-input Evidence Ledger authoritative.
I2 adds structure-first clause semantics and retention without depending on
fixture vocabulary. I3/I4 build SentencePlan/Surface from this plan, and I5
connects that same contract once from ``emlis_ai_reply_service``.
Grounded human reception RR2/RR3 adds a nested body-free opportunity/depth/move
contract while leaving SentencePlan, Surface, Gate, and the public response
shape unchanged.

Every source reference is an existing request-local ``sN`` id. No synthetic or
replacement Evidence id is created here.
"""

from collections.abc import Iterable, Mapping, Sequence
from dataclasses import asdict, dataclass, replace
import re
from typing import Any, Final, Literal

from emlis_ai_current_input_bundle import normalize_emlis_current_input
from emlis_ai_evidence_ledger_service import (
    EvidenceLedgerResolutionError,
    EvidenceLedgerValidationReport,
    EvidenceSpanResolver,
    build_evidence_ledger,
    build_evidence_span_resolver,
    validate_evidence_ledger,
)
from emlis_ai_observation_integrator_service import integrate_perspective_board
from emlis_ai_perspective_board import build_perspective_board
from emlis_ai_perspective_observers import run_perspective_observers
from emlis_ai_safety_triage import (
    TRIAGE_SAFE_OBSERVATION,
    TRIAGE_SAFETY_BLOCKED_EMERGENCY,
    TRIAGE_SAFETY_SUPPORT_REQUIRED,
    TRIAGE_SELF_DENIAL_SAFE_STATE_ANSWER,
    EmlisSafetyTriageDecision,
    build_emlis_safety_triage_decision,
)
from emlis_ai_types import (
    EvidenceRef,
    EvidenceSpan,
    InputMeaningBlock,
    MajorMeaningRetentionPlan,
    MeaningCoveragePlan,
    ObservationGraph,
    PerspectiveBoard,
    PerspectiveReport,
    RelationEdge,
    WholeInputMeaningArc,
)

GROUND_OBSERVATION_PLAN_SCHEMA_VERSION: Final = "cocolon.emlis.grounded_observation_plan.v1"
GROUND_OBSERVATION_PLAN_ADAPTER_VERSION: Final = "cocolon.emlis.grounded_observation_plan_adapter.i1.v1"
GROUND_OBSERVATION_PLAN_GENERATION_PATH: Final = "grounded_observation_plan_canonical_v1"
GROUND_OBSERVATION_PLAN_SEMANTIC_VERSION: Final = "cocolon.emlis.grounded_semantics.i2.v3"
GROUND_HUMAN_RECEPTION_PLAN_SCHEMA_VERSION: Final = "cocolon.emlis.grounded_human_reception_plan.v2"

EvidenceId = str
NucleusId = str
RelationId = str
NucleusKind = Literal[
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
]
RelationKind = Literal[
    "temporal_before_after",
    "shift_from_to",
    "contrast",
    "coexistence",
    "user_stated_cause",
    "user_stated_result",
    "attempt_and_block",
    "wish_and_constraint",
    "action_supports_change",
    "evaluation_about_event",
    "self_evaluation_about_state",
    "preserves_despite",
    "uncertain_connection",
    "continuation_or_refusal",
]
Retention = Literal["required", "should", "optional"]
GroundingKind = Literal["explicit", "user_stated_relation", "bounded_structural_inference"]
UnknownSurfacePolicy = Literal["do_not_claim", "hedge_only", "omit"]
GroundedHumanFollowRole = Literal[
    "integrated_current_state",
    "help_seeking_preserved",
    "protective_counterdirection",
    "retained_intention",
    "concrete_effort",
    "valued_change",
    "burden_expression",
]
GroundedHumanFollowDelivery = Literal[
    "separate_distinct_contribution",
    "not_required",
]
GroundedReceptionAct = Literal[
    "stay_with_current_burden",
    "honor_concrete_effort",
    "protect_retained_intention",
    "recognize_lived_change",
    "hold_help_seeking",
    "bounded_counter_self_denial",
    "respect_words_placed",
]
GroundedFollowElement = Literal[
    "intent_affirmation",
    "burden_understanding",
    "effort_receiving",
    "existence_respect",
]
GroundedReceptionStance = Literal[
    "quiet_presence",
    "warm_recognition",
    "gentle_respect",
    "protective_presence",
    "bounded_disagreement",
]
GroundedSpeakerPresence = Literal[
    "implicit_emlis",
    "explicit_emlis",
]
GroundedReferenceMode = Literal[
    "anaphoric_first",
    "short_anchor_if_ambiguous",
    "explicit_emlis_counterposition",
]
GroundedReceptionOpportunityFamily = Literal[
    "current_burden",
    "concrete_effort",
    "retained_intention",
    "lived_change",
    "help_seeking",
    "counterdirection",
    "words_placed",
]
GroundedReceptionDepthLevel = Literal[
    "minimal",
    "focused",
    "layered",
]
GroundedReceptionSafetyMode = Literal[
    "standard",
    "self_denial_bounded",
    "help_seeking_bounded",
]
GroundedReceptionMoveRole = Literal[
    "attention",
    "significance",
    "felt_response",
    "bounded_counterposition",
]
GroundedReceptionSurfaceStrategy = Literal[
    "quiet_referent_first",
    "emlis_attention_first",
    "referent_significance_first",
    "felt_response_first",
    "explicit_emlis_counterposition",
]

_TEXT_SOURCE_FIELDS: Final = frozenset({"memo", "memo_action"})
_LABEL_SOURCE_FIELDS: Final = frozenset({"emotion_details", "emotions", "category"})
_EVIDENCE_ID_RE: Final = re.compile(r"^s[1-9][0-9]*$")
_BODY_FREE_CODE_RE: Final = re.compile(r"^[A-Za-z0-9_.:-]+$")
_PUNCT_SPACE_RE: Final = re.compile(r"[\s\u3000、,。．.!！?？「」『』（）()]+")
_PURE_RELATION_MARKERS: Final = frozenset(
    {"でも", "だけど", "けど", "ただ", "とはいえ", "その中で", "一方", "同時に", "なのに", "からこそ", "だからこそ"}
)
_ALLOWED_RELATION_KINDS: Final = frozenset(
    {
        "temporal_before_after",
        "shift_from_to",
        "contrast",
        "coexistence",
        "user_stated_cause",
        "user_stated_result",
        "attempt_and_block",
        "wish_and_constraint",
        "action_supports_change",
        "evaluation_about_event",
        "self_evaluation_about_state",
        "preserves_despite",
        "uncertain_connection",
        "continuation_or_refusal",
    }
)
_RELATION_KIND_BY_EXISTING_TYPE: Final[dict[str, RelationKind]] = {
    "explicit_transition": "contrast",
    "coexistence": "coexistence",
    "tension": "wish_and_constraint",
    "limit_tension": "attempt_and_block",
}
_KIND_BY_DETECTED_TYPE: Final[dict[str, NucleusKind]] = {
    "event": "event",
    "emotion": "reaction",
    "wish": "wish",
    "constraint": "constraint",
    "fear": "reaction",
    "self_awareness": "self_evaluation",
    "limit_signal": "state",
    "value": "value",
    "relation_marker": "other_explicit",
    "safety_risk": "state",
}
_ROLE_KIND_HINTS: Final[tuple[tuple[frozenset[str], NucleusKind], ...]] = (
    (frozenset({"paced_progress"}), "change"),
    (frozenset({"self_view", "self_awareness", "self_suppression"}), "self_evaluation"),
    (frozenset({"wish", "wish_or_hope", "continuation_wish", "own_happiness_wish", "normal_life_wish"}), "wish"),
    (frozenset({"constraint", "restriction_pressure", "reality_gap_or_inconvenience", "collapse_anxiety"}), "constraint"),
    (frozenset({"fear_or_disappointment", "sadness_or_pain", "fatigue_or_limit", "limit_or_exhaustion"}), "reaction"),
    (frozenset({"value", "value_or_strength", "relief_source", "small_change_value"}), "value"),
)
_RETENTION_RANK: Final = {"optional": 0, "should": 1, "required": 2}


_NEGATION_RE: Final = re.compile(
    r"(?:ない|なかった|なく|ません|できず|出来ず|無理|だめ|ダメ)"
)
_NON_NEGATING_UNCERTAINTY_RE: Final = re.compile(r"(?:かも知れない|かもしれない)")
_NON_NEGATING_CONTRAST_RE: Final = re.compile(
    r"(?:だけでなく|わけではなく|のではなく|ではなく|じゃなく)(?:て|、|,)?"
)
_SIMILE_NOT_WISH_RE: Final = re.compile(r"(?<![てで])みたい")
_POSITIVE_CHANGE_RE: Final = re.compile(
    r"(?:できた|出来た|(?:ら|れ)れるようにな|ようになった|くなった|になった|"
    r"増えた|減った|戻った|進んだ|進めた|改善した|落ち着いた|楽になった|"
    r"嬉|うれ|喜び|安心|平穏|幸せ|達成)"
)
_FEELING_RE: Final = re.compile(
    r"(?:感じ|気持ち|悲し|不安|だる|しんど|つら|辛|焦|もやもや|怖|寂|苦し|嬉|うれ|落ち着|重い)"
)
_HELP_SEEKING_RE: Final = re.compile(
    r"(?:相談|面談|受診|診察|予約|窓口|連絡先|相談先|支援先|助けを求め|話を聞いてもら)"
)
_SOURCE_METAPHOR_RE: Final = re.compile(
    r"(?:鉛|石|重り|圧力|圧迫|締め付け|押し潰|沈む|霧|棘|刺さる|穴が空|空洞)"
)
_WISH_RE: Final = re.compile(
    r"(?:したい|なりたい|していきたい|過ごしていきたい|ほしい|欲しい|願|つもり|たい(?:って|と|気持ち|と思|[、,\s]|$)|たらいい)"
)
_REFUSAL_RE: Final = re.compile(
    r"(?:したくない|続けたくない|やめたい|終わらせたい|投げ出したい|"
    r"つもり(?:は|が)?ない|拒|嫌だ|このまま(?:では|じゃ)いけない)"
)
_UNCERTAIN_RE: Final = re.compile(
    r"(?:気がする|かもしれ|と思う|こうかな|かな(?=[、。,.!！?？\s]|$)|憶測|わからない|分からない|不明)"
)
_CONSTRAINT_RE: Final = re.compile(
    r"(?:なければ|ないと|できない|出来ない|難しい|無理|制約|限界|しかない|せざるを得|取れなく|作れない)"
)
_CHANGE_RE: Final = re.compile(
    r"(?:になった|なって|くなった|変わ|減った|増えた|戻った|進んだ|進めた|"
    r"できるよう|出来るよう|(?:ら|れ)れるよう|改善|進歩)"
)
_SELF_EVALUATION_RE: Final = re.compile(
    r"(?:自分|私).{0,24}(?:だ|と思|感じ|弱|悪|傷つ|遅|中途半端|だめ|ダメ|責任|比べ)"
)
_VALUE_RE: Final = re.compile(r"(?:大切|大事|価値|意味がある|守りたい|好まし|望まし|良(?:い|く)|いい)")
_ACTION_RE: Final = re.compile(r"(?:行動|記録|メモ|書き|書いた|見て|見た|作った|試した|調べた|残した)")
_CONTRAST_RE: Final = re.compile(r"(?:でも|だけど|けれど|けど|一方|なのに|ただ|とはいえ)")
_COEXISTENCE_RE: Final = re.compile(r"(?:同時に|両方|どっちも|抱えたまま)")
_CAUSE_RE: Final = re.compile(r"(?:ので|ため|ことで|からこそ|だからこそ)")
_RESULT_RE: Final = re.compile(r"(?:その結果|だから|になった|減った|増えた|できた|出来た|ようになった)")
_SHIFT_RE: Final = re.compile(
    r"(?:今までは|これまでは|以前は|前は|今は|現在は|昨日|今日|より|"
    r"になった|くなった|変わ|減った|増えた|戻った|ようになった|進歩)"
)
_CONTINUATION_RE: Final = re.compile(r"(?:続け|繰り返|ずっと)")
_LEADING_CONTRAST_RE: Final = re.compile(
    r"^(?:それでも|けれども?|でも|だけど|一方で|ただ|とはいえ|なのに)"
)
_BOUNDARY_CAUSE_RE: Final = re.compile(r"(?:ので|ため|ことで|からこそ|だからこそ)[、,]?$")
_BOUNDARY_RESULT_RE: Final = re.compile(r"^(?:その結果|結果として|そのため|だから)")
_ACHIEVEMENT_RE: Final = re.compile(
    r"(?:できた|出来た|書けた|作れた|見えた|行けた|進めた|伝えられた|残せた|"
    r"整えた|終えた|まとめた|片づけた|片付けた)"
)
_COMPLETED_ACTION_RE: Final = re.compile(
    r"(?:整理した|保存した|記録した|メモした|測定した|確認した|連絡した|相談した|"
    r"準備した|提出した|予約した|縮めて保存した|印を付けた|書き残した|残した|"
    r"書いた|調べた|試した|見た|作った|行った)"
)
_LIMITING_UNKNOWN_RE: Final = re.compile(
    r"(?:まだ(?:不明|分から|わから|遠い)|不明|分からない|わからない|"
    r"遠い(?:と思|気が)|かもしれない|確定できない)"
)
_PROVISIONAL_EVALUATION_RE: Final = re.compile(
    r"(?:失敗|無理|駄目|だめ|ダメ|終わり|価値がない).{0,18}(?:と思|と見|と感じ|"
    r"と片づけ|と片付け|そうにな|かけ)"
)
_EXPLICIT_EVALUATION_RE: Final = re.compile(
    r"(?:私|自分|本人).{0,12}(?:にとって|として).{0,12}(?:良い|いい|大切|大事|価値)|"
    r"(?:良い|いい|大切|大事|価値).{0,8}(?:変化|進歩|結果|部分)"
)
_EXPLICIT_SHIFT_FROM_RE: Final = re.compile(r"(?:今までは|これまでは|以前は|前は|昨日は)")
_EXPLICIT_SHIFT_TO_RE: Final = re.compile(
    r"(?:今は|現在は|これから|今後|次は|ようになった|くなった|になった|減った|増えた)"
)
_SELF_REFERENCE_RE: Final = re.compile(r"(?:自分|私|わたし|僕|ぼく|俺|おれ)")
_SELF_DENIAL_PREDICATE_RE: Final = re.compile(
    r"(?:嫌い|きらい|価値.{0,5}(?:ない|無い)|最低(?!でも|限)|クズ|駄目|だめ|ダメ(?!ージ)|"
    r"悪い|責め|追い込|傷つけ|許せない|好きになれない|役に立たない|"
    r"何もできない|なにもできない|できない(?:人間|奴|やつ)|失敗ばかり|"
    r"存在.{0,8}(?:意味|価値).{0,5}(?:ない|無い)|中途半端)"
)
_EXPRESSION_DIFFICULTY_RE: Final = re.compile(
    r"(?:上手く|うまく)?(?:表現|説明|整理|言葉に|話すことが|伝えることが)"
    r"(?:できない|出来ない|しにくい)|(?:上手く|うまく)言えない"
)
_PAST_RE: Final = re.compile(r"(?:昨日|以前|今まで|これまで|過去|先週|前は)")
_PRESENT_RE: Final = re.compile(r"(?:今日|今は|今の|現在|この記録|少しずつ)")
_FUTURE_RE: Final = re.compile(r"(?:これから|今後|次に|していきたい|過ごしていきたい)")
_TRULY_LIMITED_TEXT_RE: Final = re.compile(
    r"^(?:わからない|分からない|不明|特になし|なし|入力なし|未入力|うーん|えっと|それ|これ|あれ)$"
)
_SHORT_STATE_KINDS: Final = frozenset(
    {
        "state",
        "reaction",
        "wish",
        "constraint",
        "self_evaluation",
        "uncertainty",
        "conclusion",
    }
)


class GroundedObservationPlanError(ValueError):
    """Raised when the I1 shadow plan cannot satisfy its internal contract."""


@dataclass(frozen=True)
class GroundedSemanticFrame:
    actor: str
    predicate_kind: str
    polarity: Literal["positive", "negative", "mixed", "neutral"]
    modality: Literal["fact", "feeling", "wish", "possibility", "uncertain", "refusal", "intention"]
    target_anchor_ids: tuple[str, ...] = ()
    time_scope: str = "current_input"
    degree: str = "source_bounded"
    attribute_codes: tuple[str, ...] = ()


@dataclass(frozen=True)
class GroundedSemanticNucleus:
    nucleus_id: NucleusId
    kind: NucleusKind
    source_span_ids: tuple[EvidenceId, ...]
    source_fields: tuple[str, ...]
    surface_anchor_ids: tuple[str, ...]
    semantic_frame: GroundedSemanticFrame
    grounding_kind: GroundingKind
    certainty: float
    priority: float
    retention: Retention
    allowed_claim_scope: str
    forbidden_inference_codes: tuple[str, ...]
    source_claim_ids: tuple[str, ...] = ()
    source_meaning_block_keys: tuple[str, ...] = ()


@dataclass(frozen=True)
class GroundedSemanticRelation:
    relation_id: RelationId
    type: RelationKind
    from_nucleus_id: NucleusId
    to_nucleus_id: NucleusId
    source_span_ids: tuple[EvidenceId, ...]
    grounding_kind: GroundingKind
    certainty: float
    retention: Retention
    source_relation_ids: tuple[str, ...] = ()
    source_meaning_arc_keys: tuple[str, ...] = ()


@dataclass(frozen=True)
class GroundedUnknownBoundary:
    unknown_id: str
    dimension: str
    affected_nucleus_ids: tuple[NucleusId, ...] = ()
    evidence_span_ids: tuple[EvidenceId, ...] = ()
    surface_policy: UnknownSurfacePolicy = "do_not_claim"


@dataclass(frozen=True)
class GroundedInputProfile:
    text_presence: Literal["text_present", "labels_only", "empty"]
    material_quality: Literal[
        "grounded",
        "short_state_sufficient",
        "limited_grounding",
        "labels_only_limited",
        "empty",
        "safety_routed",
    ]
    semantic_complexity: Literal["minimal", "single", "multi", "long_arc"]
    nucleus_count: int
    relation_count: int
    safety_kind: str


@dataclass(frozen=True)
class GroundedQuestionPolicy:
    allowed: bool = False
    reason: str = "p7_base_observation_must_not_be_replaced_by_question"


@dataclass(frozen=True)
class GroundedReceptionQuotePolicy:
    mode: Literal["no_full_quote_replay"]
    max_anchor_count: int
    max_anchor_visible_chars: int


@dataclass(frozen=True)
class GroundedReceptionSentencePolicy:
    min_sentences: int
    max_sentences: int


@dataclass(frozen=True)
class GroundedReceptionDistinctnessPolicy:
    observation_summary_repetition_allowed: bool
    relation_reexplanation_allowed: bool
    all_input_enumeration_allowed: bool
    policy_explanation_allowed: bool
    new_cause_allowed: bool
    new_identity_claim_allowed: bool
    advice_allowed: bool
    question_allowed: bool


@dataclass(frozen=True)
class GroundedReceptionOpportunity:
    """Body-free chance to make one distinct human reception contribution."""

    opportunity_id: str
    family: GroundedReceptionOpportunityFamily
    reception_act: GroundedReceptionAct
    target_nucleus_ids: tuple[NucleusId, ...]
    support_nucleus_ids: tuple[NucleusId, ...]
    source_evidence_span_ids: tuple[EvidenceId, ...]
    retention: Retention
    priority: int
    source_field_count: int
    safety_required: bool


@dataclass(frozen=True)
class GroundedReceptionDepthPolicy:
    """Semantic response depth; raw input length is never an input."""

    level: GroundedReceptionDepthLevel
    safety_mode: GroundedReceptionSafetyMode
    opportunity_count: int
    selected_move_count: int
    selection_reason_codes: tuple[str, ...]
    raw_character_count_used: bool
    min_sentences: int
    max_sentences: int
    min_realized_moves: int
    max_moves_per_sentence: int


@dataclass(frozen=True)
class GroundedReceptionMovePlan:
    """One grounded human contribution for the later RR4/RR5 surface owner."""

    move_id: str
    move_role: GroundedReceptionMoveRole
    reception_act: GroundedReceptionAct
    target_nucleus_ids: tuple[NucleusId, ...]
    support_nucleus_ids: tuple[NucleusId, ...]
    source_evidence_span_ids: tuple[EvidenceId, ...]
    follow_elements: tuple[GroundedFollowElement, ...]
    speaker_presence: GroundedSpeakerPresence
    reference_mode: GroundedReferenceMode
    surface_strategy: GroundedReceptionSurfaceStrategy
    required: bool
    distinct_from_move_ids: tuple[str, ...]


@dataclass(frozen=True)
class GroundedHumanReceptionPlan:
    """Body-free contract for Emlis's distinct human reception contribution."""

    schema_version: str
    required: bool
    opportunities: tuple[GroundedReceptionOpportunity, ...]
    depth_policy: GroundedReceptionDepthPolicy
    moves: tuple[GroundedReceptionMovePlan, ...]
    primary_reception_act: GroundedReceptionAct | None
    secondary_reception_act: GroundedReceptionAct | None
    primary_follow_element: GroundedFollowElement | None
    secondary_follow_elements: tuple[GroundedFollowElement, ...]
    afterglow_follow_element: GroundedFollowElement | None
    target_nucleus_ids: tuple[NucleusId, ...]
    support_nucleus_ids: tuple[NucleusId, ...]
    source_evidence_span_ids: tuple[EvidenceId, ...]
    observation_owned_nucleus_ids: tuple[NucleusId, ...]
    stance: GroundedReceptionStance | None
    speaker_presence: GroundedSpeakerPresence | None
    reference_mode: GroundedReferenceMode | None
    quote_policy: GroundedReceptionQuotePolicy
    sentence_policy: GroundedReceptionSentencePolicy
    distinctness_policy: GroundedReceptionDistinctnessPolicy
    safety_modifier_codes: tuple[str, ...]
    forbidden_surface_codes: tuple[str, ...]


@dataclass(frozen=True)
class GroundedResponsePlan:
    response_kind: str
    primary_nucleus_ids: tuple[NucleusId, ...]
    supporting_nucleus_ids: tuple[NucleusId, ...]
    relation_ids: tuple[RelationId, ...]
    fact_boundary_nucleus_ids: tuple[NucleusId, ...]
    human_follow_target_ids: tuple[NucleusId, ...]
    human_reception_plan: GroundedHumanReceptionPlan | None
    required_nucleus_ids: tuple[NucleusId, ...]
    optional_nucleus_ids: tuple[NucleusId, ...]
    question_policy: GroundedQuestionPolicy
    surface_shape: Literal["plain", "two_stage", "multi_paragraph", "separate_safety_surface"]


@dataclass(frozen=True)
class GroundedCoverageRequirements:
    required_nucleus_ids: tuple[NucleusId, ...]
    required_relation_ids: tuple[RelationId, ...]
    all_required_nuclei_must_be_covered: bool = True
    all_required_relations_must_be_covered: bool = True
    all_sentence_evidence_ids_must_resolve: bool = True
    label_only_allowed_only_without_text_nuclei: bool = True
    human_follow_required: bool = False
    fact_boundary_required: bool = False


@dataclass(frozen=True)
class GroundedSurfacePolicy:
    content_source: Literal["grounded_plan_only", "separate_safety_owner"]
    completed_semantic_template_allowed: bool = False
    example_cue_route_allowed: bool = False
    synthetic_evidence_id_allowed: bool = False
    unknown_word_policy: Literal["retain_as_source_anchor", "omit_without_inference"] = "retain_as_source_anchor"
    generic_observation_surface_allowed: bool = True
    tone_family: str = "current_input_bounded"
    hedge_policy: str = "single_input_scope"


@dataclass(frozen=True)
class GroundedSafetyPolicy:
    safety_kind: str
    identity_claim_must_not_be_accepted_as_fact: bool
    emergency_path_must_not_be_overridden: bool = True
    requires_separate_safety_surface: bool = False
    grounded_plan_overlay_allowed: bool = True
    required_boundary_codes: tuple[str, ...] = ()


@dataclass(frozen=True)
class GroundedObservationPlan:
    schema_version: str
    adapter_version: str
    generation_path: str
    input_profile: GroundedInputProfile
    nuclei: tuple[GroundedSemanticNucleus, ...]
    relations: tuple[GroundedSemanticRelation, ...]
    unknown_boundaries: tuple[GroundedUnknownBoundary, ...]
    response_plan: GroundedResponsePlan
    coverage_requirements: GroundedCoverageRequirements
    surface_policy: GroundedSurfacePolicy
    safety_policy: GroundedSafetyPolicy
    evidence_ledger_validation: EvidenceLedgerValidationReport
    referenced_evidence_span_ids: tuple[EvidenceId, ...]
    source_contracts: tuple[str, ...] = ()

    def as_body_free_meta(self) -> dict[str, Any]:
        """Return ids, codes, counts and policies only; never source/body text."""

        payload = asdict(self)
        payload.update(
            {
                "raw_input_included": False,
                "raw_text_included": False,
                "comment_text_included": False,
                "surface_text_included": False,
                "comment_text_generated": False,
                "surface_connected": True,
                "public_reply_path_connected": True,
                "human_reception_plan_included": self.response_plan.human_reception_plan is not None,
                "human_reception_plan_required": bool(
                    self.response_plan.human_reception_plan
                    and self.response_plan.human_reception_plan.required
                ),
                "public_contract_changed": False,
                "api_route_changed": False,
                "db_physical_name_changed": False,
                "rn_visible_contract_changed": False,
            }
        )
        return payload


@dataclass(frozen=True)
class _MeaningArtifacts:
    meaning_blocks: tuple[InputMeaningBlock, ...] = ()
    coverage_plan: MeaningCoveragePlan | None = None
    whole_input_meaning_arc: WholeInputMeaningArc | None = None
    retention_plan: MajorMeaningRetentionPlan | None = None


@dataclass(frozen=True)
class _RelationSeed:
    type: RelationKind
    from_nucleus_id: NucleusId
    to_nucleus_id: NucleusId
    source_span_ids: tuple[EvidenceId, ...]
    grounding_kind: GroundingKind
    certainty: float
    retention: Retention
    source_relation_ids: tuple[str, ...] = ()
    source_meaning_arc_keys: tuple[str, ...] = ()


@dataclass(frozen=True)
class _ClauseSignals:
    polarity: Literal["positive", "negative", "mixed", "neutral"]
    modality: Literal["fact", "feeling", "wish", "possibility", "uncertain", "refusal", "intention"]
    time_scope: str
    operator_codes: tuple[str, ...]


def _clean(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "").replace("\u3000", " ")).strip()


def _dedupe(values: Iterable[Any]) -> list[str]:
    out: list[str] = []
    for value in values or ():
        item = _clean(value)
        if item and item not in out:
            out.append(item)
    return out


def _span_number(span_id: str) -> tuple[int, str]:
    value = _clean(span_id)
    match = _EVIDENCE_ID_RE.fullmatch(value)
    return (int(value[1:]), value) if match else (10**9, value)


def _ordered_span_ids(values: Iterable[Any]) -> list[str]:
    return sorted(_dedupe(values), key=_span_number)


def _compact(value: Any) -> str:
    return _PUNCT_SPACE_RE.sub("", _clean(value)).lower()


def _is_body_free_code(value: Any) -> bool:
    return bool(_BODY_FREE_CODE_RE.fullmatch(_clean(value)))


def _clamp(value: Any, lower: float = 0.0, upper: float = 1.0) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError):
        number = lower
    return max(lower, min(upper, number))


def _retention_max(left: Retention, right: Retention) -> Retention:
    return left if _RETENTION_RANK[left] >= _RETENTION_RANK[right] else right


def _is_pure_relation_marker(span: EvidenceSpan) -> bool:
    return _clean(getattr(span, "raw_text", "")) in _PURE_RELATION_MARKERS


def _text_spans(spans: Sequence[EvidenceSpan]) -> list[EvidenceSpan]:
    return [span for span in spans if _clean(getattr(span, "source_field", "")) in _TEXT_SOURCE_FIELDS]


def _sort_spans(spans: Sequence[EvidenceSpan]) -> list[EvidenceSpan]:
    field_order = {"memo": 0, "memo_action": 1, "emotion_details": 2, "emotions": 3, "category": 4}
    return sorted(
        list(spans or ()),
        key=lambda span: (
            field_order.get(_clean(getattr(span, "source_field", "")), 9),
            int(getattr(span, "start_index", -1)) if int(getattr(span, "start_index", -1)) >= 0 else 10**9,
            _span_number(_clean(getattr(span, "span_id", ""))),
        ),
    )


def _time_scope_for_text(text: str) -> str:
    has_past = bool(_PAST_RE.search(text))
    has_present = bool(_PRESENT_RE.search(text))
    has_future = bool(_FUTURE_RE.search(text))
    if has_past and has_present:
        return "past_to_present"
    if has_present and has_future:
        return "present_to_future"
    if has_past:
        return "past"
    if has_future:
        return "future"
    if has_present:
        return "present"
    if _CONTINUATION_RE.search(text):
        return "continuing"
    return "current_input"


def _operator_codes_for_text(text: str, *, source_field: str = "") -> tuple[str, ...]:
    checks: tuple[tuple[str, re.Pattern[str]], ...] = (
        ("operator:positive_change", _POSITIVE_CHANGE_RE),
        ("operator:feeling", _FEELING_RE),
        ("operator:wish", _WISH_RE),
        ("operator:refusal", _REFUSAL_RE),
        ("operator:uncertainty", _UNCERTAIN_RE),
        ("operator:constraint", _CONSTRAINT_RE),
        ("operator:change", _CHANGE_RE),
        ("operator:self_evaluation", _SELF_EVALUATION_RE),
        ("operator:value", _VALUE_RE),
        ("operator:contrast", _CONTRAST_RE),
        ("operator:coexistence", _COEXISTENCE_RE),
        ("operator:cause", _CAUSE_RE),
        ("operator:result", _RESULT_RE),
        ("operator:shift", _SHIFT_RE),
        ("operator:continuation", _CONTINUATION_RE),
    )
    # ``かもしれない`` carries uncertainty, not negative polarity.  Remove
    # only that neutral uncertainty suffix before evaluating negation; an
    # explicit negative claim such as ``できないかもしれない`` still keeps
    # the preceding ``できない`` operator.
    negation_scope = _NON_NEGATING_UNCERTAINTY_RE.sub("", text)
    negation_scope = _NON_NEGATING_CONTRAST_RE.sub("", negation_scope)
    values = ["operator:negation"] if _NEGATION_RE.search(negation_scope) else []
    # The suffix in a simile such as ``鉛みたい`` is not the desiderative
    # ``たい``.  Let the wish detector see a scope with that exact hiragana
    # form removed; kanji forms such as ``見たい`` remain available.
    wish_scope = _SIMILE_NOT_WISH_RE.sub("", text)
    values.extend(
        code
        for code, pattern in checks
        if pattern.search(wish_scope if code == "operator:wish" else text)
    )
    if source_field == "memo_action" or _ACTION_RE.search(text):
        values.append("operator:action")
    if _HELP_SEEKING_RE.search(text):
        values.append("operator:help_seeking")
    return tuple(_dedupe(values))


def _clause_signals(span: EvidenceSpan, *, kind: NucleusKind) -> _ClauseSignals:
    text = _clean(getattr(span, "raw_text", ""))
    source_field = _clean(getattr(span, "source_field", ""))
    operators = _operator_codes_for_text(text, source_field=source_field)
    operator_set = set(operators)

    negative = "operator:negation" in operator_set or "operator:refusal" in operator_set
    positive = "operator:positive_change" in operator_set or "operator:value" in operator_set
    if negative and positive and "operator:contrast" in operator_set:
        polarity: Literal["positive", "negative", "mixed", "neutral"] = "mixed"
    elif negative:
        polarity = "negative"
    elif positive:
        polarity = "positive"
    elif kind in {"reaction", "constraint", "self_evaluation"}:
        polarity = "negative"
    elif kind in {"value", "wish"}:
        polarity = "positive"
    else:
        polarity = "neutral"

    if "operator:refusal" in operator_set:
        modality: Literal["fact", "feeling", "wish", "possibility", "uncertain", "refusal", "intention"] = "refusal"
    elif "operator:wish" in operator_set:
        modality = "wish"
    elif "operator:uncertainty" in operator_set:
        modality = "uncertain"
    elif kind in {"reaction", "self_evaluation"} or "operator:feeling" in operator_set:
        modality = "feeling"
    elif kind == "constraint" or "operator:constraint" in operator_set:
        modality = "possibility"
    elif source_field == "memo_action" and not re.search(r"(?:した|していった|見た|書いた|記録した|メモした|作った)", text):
        modality = "intention"
    else:
        modality = "fact"

    return _ClauseSignals(
        polarity=polarity,
        modality=modality,
        time_scope=_time_scope_for_text(text),
        operator_codes=operators,
    )


def _nearest_substantive_span(
    spans: Sequence[EvidenceSpan],
    start: int,
    step: int,
) -> EvidenceSpan | None:
    index = start
    while 0 <= index < len(spans):
        span = spans[index]
        if _is_substantive_text_span(span) and not _is_pure_relation_marker(span):
            return span
        index += step
    return None


def _arc_roles_by_span(spans: Sequence[EvidenceSpan]) -> dict[str, tuple[str, ...]]:
    """Classify major semantic turns without using event or fixture nouns.

    Roles are body-free codes attached to existing Evidence spans.  They
    decide which endpoints must survive compression; they do not prescribe a
    completed sentence or create a parallel Evidence system.
    """

    roles: dict[str, list[str]] = {}

    def add(span: EvidenceSpan | None, role: str) -> None:
        if span is None:
            return
        span_id = _clean(getattr(span, "span_id", ""))
        if span_id:
            roles.setdefault(span_id, []).append(role)

    ordered = _sort_spans(_text_spans(spans))
    by_field: dict[str, list[EvidenceSpan]] = {}
    for span in ordered:
        by_field.setdefault(_clean(getattr(span, "source_field", "")), []).append(span)

    for field_name, field_spans in by_field.items():
        substantive = [
            span
            for span in field_spans
            if _is_substantive_text_span(span) and not _is_pure_relation_marker(span)
        ]
        if not substantive:
            continue

        if field_name == "memo_action":
            scored: list[tuple[int, int, EvidenceSpan]] = []
            for order, span in enumerate(substantive):
                text = _clean(getattr(span, "raw_text", ""))
                operators = set(_operator_codes_for_text(text, source_field=field_name))
                score = 1
                if _COMPLETED_ACTION_RE.search(text):
                    score += 5
                if operators & {"operator:positive_change", "operator:change", "operator:result"}:
                    score += 6
                if "operator:action" in operators:
                    score += 3
                if "operator:uncertainty" in operators:
                    score -= 2
                scored.append((score, order, span))
            # A separate action field is supporting evidence, not a replacement
            # for the memo arc.  Select its strongest source-bound action once.
            representative = max(scored, key=lambda item: (item[0], -item[1]))[2]
            add(representative, "semantic_role:concrete_action_evidence")
            continue

        for index, span in enumerate(field_spans):
            text = _clean(getattr(span, "raw_text", ""))
            if _is_pure_relation_marker(span):
                previous = _nearest_substantive_span(field_spans, index - 1, -1)
                following = _nearest_substantive_span(field_spans, index + 1, 1)
                add(previous, "semantic_role:contrast_before")
                add(following, "semantic_role:contrast_after")
                continue
            if not _is_substantive_text_span(span):
                continue

            operators = set(_operator_codes_for_text(text, source_field=field_name))
            if _LEADING_CONTRAST_RE.search(text):
                add(_nearest_substantive_span(field_spans, index - 1, -1), "semantic_role:contrast_before")
                add(span, "semantic_role:contrast_after")
            elif "operator:contrast" in operators:
                # The ledger can keep both sides of a local turn in one span.
                # That source span is mandatory, but it is not split or
                # interpreted through fixture vocabulary.
                add(span, "semantic_role:embedded_turn")

            if operators & {"operator:positive_change", "operator:change"} or _ACHIEVEMENT_RE.search(text):
                add(span, "semantic_role:current_change")
            if "operator:result" in operators:
                add(span, "semantic_role:explicit_result")
            if _EXPLICIT_EVALUATION_RE.search(text):
                add(span, "semantic_role:explicit_evaluation")
            if "operator:wish" in operators:
                add(span, "semantic_role:retained_intention")
            if "operator:refusal" in operators:
                add(span, "semantic_role:protective_or_limiting_refusal")
            if _LIMITING_UNKNOWN_RE.search(text):
                add(span, "semantic_role:limiting_unknown")
            if _PROVISIONAL_EVALUATION_RE.search(text):
                add(span, "semantic_role:provisional_evaluation")
            if _COMPLETED_ACTION_RE.search(text):
                add(span, "semantic_role:concrete_action")

        major_ids = {
            span_id
            for span_id, span_roles in roles.items()
            if any(
                role
                in {
                    "semantic_role:contrast_before",
                    "semantic_role:contrast_after",
                    "semantic_role:embedded_turn",
                    "semantic_role:current_change",
                    "semantic_role:explicit_result",
                    "semantic_role:explicit_evaluation",
                    "semantic_role:retained_intention",
                    "semantic_role:protective_or_limiting_refusal",
                    "semantic_role:limiting_unknown",
                    "semantic_role:provisional_evaluation",
                    "semantic_role:concrete_action",
                }
                for role in span_roles
            )
        }
        if len(substantive) >= 4 and major_ids:
            first = substantive[0]
            add(first, "semantic_role:initial_condition")

    role_sets = {span_id: set(values) for span_id, values in roles.items()}
    for field_spans in by_field.values():
        for index, span in enumerate(field_spans):
            span_id = _clean(getattr(span, "span_id", ""))
            if "semantic_role:contrast_after" not in role_sets.get(span_id, set()):
                continue
            previous = _nearest_substantive_span(field_spans, index - 1, -1)
            previous_id = _clean(getattr(previous, "span_id", "")) if previous else ""
            if "semantic_role:provisional_evaluation" in role_sets.get(previous_id, set()):
                add(span, "semantic_role:counterevidence")

    return {span_id: tuple(_dedupe(values)) for span_id, values in roles.items()}


def _is_substantive_text_span(span: EvidenceSpan) -> bool:
    if _clean(getattr(span, "source_field", "")) not in _TEXT_SOURCE_FIELDS:
        return False
    if _is_pure_relation_marker(span):
        return False
    compact = _compact(getattr(span, "raw_text", ""))
    if not compact or _TRULY_LIMITED_TEXT_RE.fullmatch(compact):
        return False
    return len(compact) >= 4 or bool(
        _operator_codes_for_text(
            _clean(getattr(span, "raw_text", "")),
            source_field=_clean(getattr(span, "source_field", "")),
        )
    )


def _is_structural_self_denial_span(span: EvidenceSpan) -> bool:
    """Detect identity/self-worth denial without an exact fixture sentence."""

    if _clean(getattr(span, "source_field", "")) not in _TEXT_SOURCE_FIELDS:
        return False
    text = _clean(getattr(span, "raw_text", ""))
    if not _SELF_REFERENCE_RE.search(text):
        return False
    if _EXPRESSION_DIFFICULTY_RE.search(text) and not _SELF_DENIAL_PREDICATE_RE.search(text):
        return False
    return bool(_SELF_DENIAL_PREDICATE_RE.search(text))


def _is_input_grounded_refusal_span(span: EvidenceSpan) -> bool:
    if _clean(getattr(span, "source_field", "")) not in _TEXT_SOURCE_FIELDS:
        return False
    text = _clean(getattr(span, "raw_text", ""))
    operators = set(
        _operator_codes_for_text(
            text,
            source_field=_clean(getattr(span, "source_field", "")),
        )
    )
    return bool(
        "operator:refusal" in operators
        or ({"operator:continuation", "operator:negation"} <= operators)
    )


def _canonicalize_safety_decision(
    base_decision: EmlisSafetyTriageDecision,
    spans: Sequence[EvidenceSpan],
    *,
    authoritative_self_denial: bool,
) -> EmlisSafetyTriageDecision:
    """Keep emergency ownership and derive non-emergency self-denial structurally.

    The public triage remains a separate safety owner.  For this shadow plan,
    a triage hit is not enough by itself: the current Evidence spans must
    contain a self-referential negative evaluation.  This keeps fixture phrases
    and expression-difficulty false positives from deciding the canonical
    family while preserving emergency ownership.
    """

    if base_decision.safety_triage_kind in {
        TRIAGE_SAFETY_SUPPORT_REQUIRED,
        TRIAGE_SAFETY_BLOCKED_EMERGENCY,
    }:
        return base_decision

    ordered_text = _sort_spans(_text_spans(spans))
    self_denial_spans = [span for span in ordered_text if _is_structural_self_denial_span(span)]
    refusal_spans = [span for span in ordered_text if _is_input_grounded_refusal_span(span)]
    if not self_denial_spans and not (
        authoritative_self_denial
        and base_decision.safety_triage_kind == TRIAGE_SELF_DENIAL_SAFE_STATE_ANSWER
    ):
        return EmlisSafetyTriageDecision()

    evidence_ids = _ordered_span_ids(
        [
            *[_clean(getattr(span, "span_id", "")) for span in self_denial_spans],
            *[_clean(getattr(span, "span_id", "")) for span in refusal_spans],
            *(
                list(getattr(base_decision, "evidence_span_ids", ()) or ())
                if authoritative_self_denial
                else []
            ),
        ]
    )
    span_index = {
        _clean(getattr(span, "span_id", "")): span
        for span in spans
        if _clean(getattr(span, "span_id", ""))
    }
    source_fields = _dedupe(
        _clean(getattr(span_index[span_id], "source_field", ""))
        for span_id in evidence_ids
        if span_id in span_index
    )
    self_denial_ids = {
        _clean(getattr(span, "span_id", "")) for span in self_denial_spans
    }
    refusal_ids = {
        _clean(getattr(span, "span_id", "")) for span in refusal_spans
    }
    # A limited opposition is only grounded when a distinct source span adds a
    # continuation/refusal statement.  A single self-denial sentence may still
    # receive the fact boundary and evidence-bound follow, but no opposition is
    # invented from the same clause.
    continuation_refusal = bool(refusal_ids - self_denial_ids)
    reason_codes = ["self_denial_structure_non_emergency"]
    if continuation_refusal:
        reason_codes.append("input_grounded_continuation_refusal")
    return EmlisSafetyTriageDecision(
        safety_triage_kind=TRIAGE_SELF_DENIAL_SAFE_STATE_ANSWER,
        response_kind=TRIAGE_SELF_DENIAL_SAFE_STATE_ANSWER,
        normal_observation_allowed=False,
        safe_state_answer_allowed=True,
        public_emlis_observation_allowed=True,
        public_input_feedback_allowed=True,
        requires_separate_safety_surface=False,
        blocked_reason=None,
        must_not_accept_identity_claim_as_fact=True,
        continuation_refusal_detected=continuation_refusal,
        reason_codes=reason_codes,
        boundary_types=[],
        evidence_span_ids=evidence_ids,
        source_fields=source_fields,
        source="grounded_structural_overlay",
    )


def _relation_type_for_pair(
    left: GroundedSemanticNucleus,
    right: GroundedSemanticNucleus,
    *,
    source_text: str,
    explicit_marker_text: str = "",
) -> RelationKind:
    left_ops = set(left.semantic_frame.attribute_codes)
    right_ops = set(right.semantic_frame.attribute_codes)
    combined_ops = left_ops | right_ops
    marker_text = _clean(explicit_marker_text)
    marker_ops = set(_operator_codes_for_text(marker_text)) if marker_text else set()
    left_roles = {code for code in left_ops if code.startswith("semantic_role:")}
    right_roles = {code for code in right_ops if code.startswith("semantic_role:")}

    if (
        left.kind == "self_evaluation"
        and right.semantic_frame.modality == "refusal"
    ) or (
        right.kind == "self_evaluation"
        and left.semantic_frame.modality == "refusal"
    ):
        return "continuation_or_refusal"
    if "operator:continuation" in combined_ops and (
        right.semantic_frame.modality == "refusal"
        or right.semantic_frame.polarity == "negative"
    ):
        return "continuation_or_refusal"
    if (
        "semantic_role:provisional_evaluation" in left_roles
        and "semantic_role:counterevidence" in right_roles
        and "operator:contrast" in marker_ops
    ):
        return "preserves_despite"
    if right.semantic_frame.modality == "refusal":
        if left.kind in {"wish", "action"}:
            return "attempt_and_block"
        return "coexistence"
    if {left.kind, right.kind} == {"wish", "constraint"}:
        return "wish_and_constraint"
    if (
        "semantic_role:concrete_action_evidence" in right_roles
        and (
            "semantic_role:retained_intention" in left_roles
            or "semantic_role:current_change" in left_roles
        )
    ):
        return "action_supports_change"
    if "operator:cause" in marker_ops:
        return "user_stated_cause"
    if "operator:result" in marker_ops and "operator:shift" not in marker_ops:
        return "user_stated_result"
    if "operator:coexistence" in marker_ops:
        return "coexistence"
    if "operator:contrast" in marker_ops:
        if (
            left.semantic_frame.polarity == "negative"
            and right.semantic_frame.polarity in {"positive", "mixed"}
        ):
            return "preserves_despite"
        return "contrast"
    explicit_shift = bool(
        _EXPLICIT_SHIFT_FROM_RE.search(_clean(source_text))
        and (
            _EXPLICIT_SHIFT_TO_RE.search(_clean(source_text))
            or "semantic_role:current_change" in right_roles
        )
    )
    if explicit_shift or (
        left.semantic_frame.time_scope in {"past", "past_to_present"}
        and right.semantic_frame.time_scope in {"present", "future", "present_to_future"}
    ):
        return "shift_from_to"
    if {left.kind, right.kind} & {"action"} and {left.kind, right.kind} & {"change", "wish"}:
        return "action_supports_change"
    if left.kind == "self_evaluation" and right.kind in {"state", "conclusion", "change", "value"}:
        return "self_evaluation_about_state"
    return "uncertain_connection"


def _relation_grounding_kind_for_pair(
    left: GroundedSemanticNucleus,
    right: GroundedSemanticNucleus,
    *,
    relation_type: RelationKind,
    source_text: str,
    explicit_marker_text: str = "",
) -> GroundingKind:
    """Separate source-stated relations from adjacency-only inference.

    The canonical plan may use source order to retain a bounded connection, but
    that alone must not make the relation required.  A relation is promoted to
    ``user_stated_relation`` only when the current clauses contain the matching
    structural operator or endpoint modalities.  No event noun or fixture text
    participates in this decision.
    """

    endpoint_operators = set(left.semantic_frame.attribute_codes) | set(right.semantic_frame.attribute_codes)
    marker_text = _clean(explicit_marker_text)
    marker_operators = set(_operator_codes_for_text(marker_text)) if marker_text else set()
    if relation_type == "continuation_or_refusal" and (
        "operator:continuation" in endpoint_operators
        or (
            "operator:refusal" in endpoint_operators
            and {left.kind, right.kind} & {"self_evaluation", "state", "conclusion"}
        )
    ):
        return "user_stated_relation"
    if relation_type in {"contrast", "preserves_despite"} and "operator:contrast" in marker_operators:
        return "user_stated_relation"
    if relation_type == "coexistence" and "operator:coexistence" in marker_operators:
        return "user_stated_relation"
    if relation_type == "user_stated_cause" and "operator:cause" in marker_operators:
        return "user_stated_relation"
    if relation_type == "user_stated_result" and "operator:result" in marker_operators:
        return "user_stated_relation"
    if relation_type == "shift_from_to" and (
        _EXPLICIT_SHIFT_FROM_RE.search(_clean(source_text))
        or "operator:shift" in marker_operators
    ):
        return "user_stated_relation"
    if relation_type == "wish_and_constraint" and {
        "operator:wish",
        "operator:constraint",
    } <= endpoint_operators:
        return "user_stated_relation"
    if relation_type == "attempt_and_block" and "operator:refusal" in endpoint_operators:
        return "user_stated_relation"
    return "bounded_structural_inference"


def _structural_role_for_span(span: EvidenceSpan) -> str:
    """Return a source-bound role from operators, never from example nouns."""

    text = _clean(getattr(span, "raw_text", ""))
    source_field = _clean(getattr(span, "source_field", ""))
    operators = set(_operator_codes_for_text(text, source_field=source_field))
    if source_field == "memo_action" or "operator:action" in operators:
        return "action"
    if "operator:self_evaluation" in operators:
        return "self_evaluation"
    if {"operator:wish", "operator:constraint"} <= operators:
        return "wish_constraint"
    if "operator:wish" in operators:
        return "wish"
    if "operator:constraint" in operators:
        return "constraint"
    if "operator:change" in operators or "operator:positive_change" in operators:
        return "change"
    if "operator:feeling" in operators:
        return "state"
    if _clean(getattr(span, "detected_type", "")) == "relation_marker":
        return "relation"
    return "current_expression"


def _build_meaning_artifacts(
    normalized_input: Mapping[str, Any],
    spans: Sequence[EvidenceSpan],
) -> _MeaningArtifacts:
    """Build structure/operator based MeaningBlock provenance for the shadow plan.

    The production ``emlis_ai_input_meaning_block_service`` still owns the
    pre-I5 public path.  The canonical shadow path builds directly from the
    authoritative Evidence Ledger so source offsets, real Evidence IDs, and
    relation endpoints remain the single provenance truth without another
    adapter boundary.
    """

    evidence_ref = EvidenceRef(
        kind="current_input",
        ref_id=_clean(normalized_input.get("id")) or "request_local_current_input",
        weight=1.0,
        note="i2_structural_meaning_adapter",
    )
    text_spans = [
        span
        for span in _sort_spans(_text_spans(spans))
        if _is_substantive_text_span(span)
    ]
    blocks: list[InputMeaningBlock] = []
    must_keep_keys: list[str] = []
    should_keep_keys: list[str] = []
    optional_keys: list[str] = []
    arc_roles_by_span = _arc_roles_by_span(spans)

    for order, span in enumerate(text_spans):
        span_id = _clean(getattr(span, "span_id", ""))
        role = _structural_role_for_span(span)
        arc_roles = set(arc_roles_by_span.get(span_id, ()))
        block_key = f"meaning:{order}:{role}"
        priority = 0.92 if arc_roles else 0.72
        blocks.append(
            InputMeaningBlock(
                block_key=block_key,
                role=role,
                title=f"source_bound:{role}",
                summary=_clean(getattr(span, "raw_text", "")),
                user_phrases=[],
                evidence=[evidence_ref],
                priority=priority,
                clarity=_clamp(getattr(span, "confidence", 0.0)),
                include_in_emlis_reply=True,
                include_in_piece_core=False,
            )
        )
        if arc_roles:
            must_keep_keys.append(block_key)
        elif role in {"action", "change", "wish", "constraint", "self_evaluation"}:
            should_keep_keys.append(block_key)
        else:
            optional_keys.append(block_key)

    text_length = sum(len(_compact(getattr(span, "raw_text", ""))) for span in text_spans)
    clear_long_input = text_length >= 180 or len(blocks) >= 6
    input_level = "long" if clear_long_input else "short" if len(blocks) <= 2 else "medium"
    if blocks and not must_keep_keys:
        must_keep_keys.append(blocks[0].block_key)
    selected_keys = [block.block_key for block in blocks]
    required_roles = _dedupe(
        block.role
        for block in blocks
        if block.block_key in set(must_keep_keys)
    )
    coverage = MeaningCoveragePlan(
        input_level=input_level,
        clear_long_input=clear_long_input,
        meaning_block_count=len(blocks),
        required_roles=list(required_roles),
        selected_block_keys=selected_keys,
        min_blocks_to_cover=len(must_keep_keys),
        max_blocks_to_cover=len(blocks),
        coverage_ratio_target=1.0 if clear_long_input else 0.8,
        reason="structure_operator_and_source_anchor_coverage",
    )
    arc = WholeInputMeaningArc(
        arc_key="whole_input:source_order",
        title="source_order_arc",
        summary="",
        ordered_block_keys=selected_keys,
        tension_pairs=[],
        core_wish_keys=[block.block_key for block in blocks if block.role == "wish"],
        fear_keys=[block.block_key for block in blocks if block.role in {"constraint", "state"}],
        present_action_keys=[block.block_key for block in blocks if block.role == "action"],
        clarity=0.86 if blocks else 0.0,
        evidence=[evidence_ref],
    )
    retention = MajorMeaningRetentionPlan(
        clear_long_input=clear_long_input,
        total_block_count=len(blocks),
        must_keep_block_keys=_dedupe(must_keep_keys),
        should_keep_block_keys=_dedupe(should_keep_keys),
        optional_block_keys=_dedupe(optional_keys),
        forbidden_overcompression_targets=_dedupe(must_keep_keys),
        min_must_keep_coverage_ratio=1.0 if must_keep_keys else 0.0,
        reason="structural_retention_without_example_roles",
    )
    return _MeaningArtifacts(tuple(blocks), coverage, arc, retention)


def _block_index(block_key: Any) -> int | None:
    parts = _clean(block_key).split(":")
    return int(parts[1]) if len(parts) >= 2 and parts[1].isdigit() else None


def _meaning_block_span_ids(
    blocks: Sequence[InputMeaningBlock],
    spans: Sequence[EvidenceSpan],
) -> dict[str, tuple[str, ...]]:
    """Map existing MeaningBlocks back to the current request ledger."""

    ordered_text = _sort_spans(_text_spans(spans))
    result: dict[str, tuple[str, ...]] = {}
    for block in blocks or ():
        key = _clean(getattr(block, "block_key", ""))
        summary = _compact(getattr(block, "summary", ""))
        matched: list[str] = []
        if len(summary) >= 2:
            for span in ordered_text:
                candidate = _compact(getattr(span, "raw_text", ""))
                if candidate and (
                    candidate == summary
                    or (len(candidate) >= 4 and candidate in summary)
                    or (len(summary) >= 4 and summary in candidate)
                ):
                    matched.append(_clean(getattr(span, "span_id", "")))
        if not matched:
            index = _block_index(key)
            if index is not None and 0 <= index < len(ordered_text):
                matched.append(_clean(getattr(ordered_text[index], "span_id", "")))
        result[key] = tuple(_ordered_span_ids(matched))
    return result


def _claim_ids_by_span(board: PerspectiveBoard) -> dict[str, tuple[str, ...]]:
    index: dict[str, list[str]] = {}
    claims = dict(getattr(board, "claim_index", {}) or getattr(board, "claims_by_id", {}) or {})
    for claim in claims.values():
        for span_id in list(getattr(claim, "evidence_span_ids", ()) or ()):
            index.setdefault(_clean(span_id), []).append(_clean(getattr(claim, "claim_id", "")))
    return {key: tuple(_dedupe(values)) for key, values in index.items()}


def _roles_and_block_keys_by_span(
    blocks: Sequence[InputMeaningBlock],
    block_span_ids: Mapping[str, Sequence[str]],
) -> tuple[dict[str, tuple[str, ...]], dict[str, tuple[str, ...]]]:
    roles: dict[str, list[str]] = {}
    keys: dict[str, list[str]] = {}
    for block in blocks or ():
        block_key = _clean(getattr(block, "block_key", ""))
        role = _clean(getattr(block, "role", ""))
        for span_id in block_span_ids.get(block_key, ()):
            if role:
                roles.setdefault(span_id, []).append(role)
            if block_key:
                keys.setdefault(span_id, []).append(block_key)
    return (
        {span_id: tuple(_dedupe(values)) for span_id, values in roles.items()},
        {span_id: tuple(_dedupe(values)) for span_id, values in keys.items()},
    )


def _retention_by_span(
    spans: Sequence[EvidenceSpan],
    *,
    block_span_ids: Mapping[str, Sequence[str]],
    meaning_artifacts: _MeaningArtifacts,
    safety_decision: EmlisSafetyTriageDecision,
) -> dict[str, Retention]:
    ordered_text = _sort_spans(_text_spans(spans))
    substantive_text = [span for span in ordered_text if _is_substantive_text_span(span)]
    # The ledger intentionally keeps punctuation-delimited source spans.  A
    # quoted question or quotation suffix can therefore leave a syntactically
    # dependent fragment.  Keep those spans resolvable in the plan, but do not
    # promote them to public-surface mandatory material on their own.
    fragment_ids: set[str] = set()
    for index, span in enumerate(substantive_text):
        text = _clean(getattr(span, "raw_text", "")).strip("「」『』 、,。．.!！?？")
        next_text = ""
        if index + 1 < len(substantive_text):
            next_text = _clean(getattr(substantive_text[index + 1], "raw_text", "")).lstrip()
        if (
            re.search(r"(?:何故|なぜ|どうして)$", text)
            or re.match(r"^(?:何故|なぜ|どうして|とか|という|と考えて(?:いた|しまって))", text)
            or (
                re.match(r"^という", next_text)
                and index + 1 < len(substantive_text)
                and _clean(getattr(span, "source_field", ""))
                == _clean(getattr(substantive_text[index + 1], "source_field", ""))
            )
        ):
            fragment_ids.add(_clean(span.span_id))
    surface_substantive_text = [
        span for span in substantive_text if _clean(span.span_id) not in fragment_ids
    ] or substantive_text
    text_count = len(surface_substantive_text)
    result: dict[str, Retention] = {}
    arc_roles_by_span = _arc_roles_by_span(spans)

    for span in spans:
        span_id = _clean(getattr(span, "span_id", ""))
        field_name = _clean(getattr(span, "source_field", ""))
        if field_name in _TEXT_SOURCE_FIELDS:
            if span_id in fragment_ids:
                result[span_id] = (
                    "required" if arc_roles_by_span.get(span_id) else "optional"
                )
                continue
            if _is_pure_relation_marker(span):
                result[span_id] = "optional"
                continue
            result[span_id] = "required" if text_count <= 3 else "should"
            if arc_roles_by_span.get(span_id):
                result[span_id] = "required"
        else:
            result[span_id] = "required" if text_count == 0 else "optional"

    coverage = meaning_artifacts.coverage_plan
    if coverage is not None:
        for block_key in tuple(getattr(coverage, "selected_block_keys", ()) or ()):
            for span_id in block_span_ids.get(_clean(block_key), ()):
                result[span_id] = _retention_max(result.get(span_id, "optional"), "should")

    retention = meaning_artifacts.retention_plan
    if retention is not None:
        for block_key in tuple(getattr(retention, "must_keep_block_keys", ()) or ()):
            for span_id in block_span_ids.get(_clean(block_key), ()):
                result[span_id] = "required"
        for block_key in tuple(getattr(retention, "should_keep_block_keys", ()) or ()):
            for span_id in block_span_ids.get(_clean(block_key), ()):
                result[span_id] = _retention_max(result.get(span_id, "optional"), "should")

    # Upstream coverage/retention is allowed to keep a dependent fragment in
    # the semantic plan, but it must not reverse the public-surface boundary.
    # A fragment that also owns a major turn is not merely syntactic residue;
    # its arc obligation remains required and is integrated downstream.
    for span_id in fragment_ids:
        if not arc_roles_by_span.get(span_id):
            result[span_id] = "optional"

    for span_id in tuple(getattr(safety_decision, "evidence_span_ids", ()) or ()):
        if span_id in result:
            result[span_id] = "required"

    # Required is a semantic obligation, not a sentence-count budget.  Surface
    # integration may combine endpoints, but it must never demote an arc role
    # merely because more than four required spans exist.
    if surface_substantive_text and not any(result.get(_clean(span.span_id)) == "required" for span in surface_substantive_text):
        result[_clean(surface_substantive_text[0].span_id)] = "required"
    return result


def _kind_for_span(
    span: EvidenceSpan,
    *,
    roles: Sequence[str],
    safety_decision: EmlisSafetyTriageDecision,
    safety_span_order: Mapping[str, int],
) -> NucleusKind:
    field_name = _clean(getattr(span, "source_field", ""))
    span_id = _clean(getattr(span, "span_id", ""))
    text = _clean(getattr(span, "raw_text", ""))
    if field_name == "memo_action":
        return "action"
    if safety_decision.safety_triage_kind == TRIAGE_SELF_DENIAL_SAFE_STATE_ANSWER and span_id in safety_span_order:
        return "self_evaluation" if safety_span_order[span_id] == 0 else "conclusion"
    if _clean(getattr(span, "detected_type", "")) == "relation_marker":
        return "other_explicit"
    if _SELF_EVALUATION_RE.search(text):
        return "self_evaluation"
    if _REFUSAL_RE.search(text):
        return "state"
    if _SIMILE_NOT_WISH_RE.search(text):
        return "reaction"
    if _WISH_RE.search(_SIMILE_NOT_WISH_RE.sub("", text)):
        return "wish"
    if _CHANGE_RE.search(text):
        return "change"
    if _CONSTRAINT_RE.search(text):
        return "constraint"
    if _FEELING_RE.search(text):
        return "reaction"
    if _VALUE_RE.search(text):
        return "value"
    if _ACTION_RE.search(text):
        return "action"

    # Upstream roles remain provenance/fallback only. Canonical semantics above
    # are driven by structural operators and source anchors, not fixture nouns.
    role_set = frozenset(_dedupe(roles))
    if "effort_direction" in role_set:
        return "change" if safety_decision.safety_triage_kind == TRIAGE_SAFE_OBSERVATION else "conclusion"
    for candidates, kind in _ROLE_KIND_HINTS:
        if role_set & candidates:
            return kind
    return _KIND_BY_DETECTED_TYPE.get(_clean(getattr(span, "detected_type", "")), "other_explicit")


def _semantic_frame_for_span(
    span: EvidenceSpan,
    *,
    kind: NucleusKind,
    roles: Sequence[str],
    claim_ids: Sequence[str],
    arc_role_codes: Sequence[str] = (),
) -> GroundedSemanticFrame:
    signals = _clause_signals(span, kind=kind)
    detected_type = _clean(getattr(span, "detected_type", "")) or "unknown"
    span_id = _clean(getattr(span, "span_id", ""))
    predicate_kind = next(
        (
            code.split(":", 1)[1]
            for code in signals.operator_codes
            if code
            in {
                "operator:refusal",
                "operator:wish",
                "operator:constraint",
                "operator:change",
                "operator:self_evaluation",
                "operator:feeling",
                "operator:action",
            }
        ),
        kind,
    )
    return GroundedSemanticFrame(
        actor="current_user",
        predicate_kind=predicate_kind,
        polarity=signals.polarity,
        modality=signals.modality,
        target_anchor_ids=(span_id,),
        time_scope=signals.time_scope,
        attribute_codes=tuple(
            _dedupe(
                [
                    f"semantic_analyzer:{GROUND_OBSERVATION_PLAN_SEMANTIC_VERSION}",
                    f"detected_type:{detected_type}",
                    *signals.operator_codes,
                    *arc_role_codes,
                    f"time_scope:{signals.time_scope}",
                    *[f"source_claim:{claim_id}" for claim_id in claim_ids],
                ]
            )
        ),
    )


def _priority_for_nucleus(span: EvidenceSpan, retention: Retention, kind: NucleusKind) -> float:
    base = {"required": 0.92, "should": 0.72, "optional": 0.42}[retention]
    if _clean(getattr(span, "source_field", "")) in _TEXT_SOURCE_FIELDS:
        base += 0.03
    if kind in {"change", "wish", "constraint", "self_evaluation", "action", "value"}:
        base += 0.02
    return _clamp(max(base, float(getattr(span, "confidence", 0.0) or 0.0) * 0.85))


def _build_nuclei(
    *,
    spans: Sequence[EvidenceSpan],
    board: PerspectiveBoard,
    meaning_artifacts: _MeaningArtifacts,
    safety_decision: EmlisSafetyTriageDecision,
) -> tuple[GroundedSemanticNucleus, ...]:
    block_span_ids = _meaning_block_span_ids(meaning_artifacts.meaning_blocks, spans)
    roles_by_span, block_keys_by_span = _roles_and_block_keys_by_span(
        meaning_artifacts.meaning_blocks,
        block_span_ids,
    )
    retention_by_span = _retention_by_span(
        spans,
        block_span_ids=block_span_ids,
        meaning_artifacts=meaning_artifacts,
        safety_decision=safety_decision,
    )
    claim_ids_by_span = _claim_ids_by_span(board)
    safety_ids = _ordered_span_ids(getattr(safety_decision, "evidence_span_ids", ()) or ())
    safety_span_order = {span_id: index for index, span_id in enumerate(safety_ids)}
    arc_roles_by_span = _arc_roles_by_span(spans)

    nuclei: list[GroundedSemanticNucleus] = []
    for span in _sort_spans(spans):
        span_id = _clean(getattr(span, "span_id", ""))
        if not span_id:
            continue
        roles = roles_by_span.get(span_id, ())
        claim_ids = claim_ids_by_span.get(span_id, ())
        retention = retention_by_span.get(span_id, "optional")
        kind = _kind_for_span(
            span,
            roles=roles,
            safety_decision=safety_decision,
            safety_span_order=safety_span_order,
        )
        field_name = _clean(getattr(span, "source_field", ""))
        grounding_kind: GroundingKind = (
            "user_stated_relation"
            if _clean(getattr(span, "detected_type", "")) == "relation_marker"
            else "explicit"
        )
        nuclei.append(
            GroundedSemanticNucleus(
                nucleus_id=f"nucleus:{span_id}",
                kind=kind,
                source_span_ids=(span_id,),
                source_fields=(field_name,),
                surface_anchor_ids=(span_id,),
                semantic_frame=_semantic_frame_for_span(
                    span,
                    kind=kind,
                    roles=roles,
                    claim_ids=claim_ids,
                    arc_role_codes=arc_roles_by_span.get(span_id, ()),
                ),
                grounding_kind=grounding_kind,
                certainty=_clamp(getattr(span, "confidence", 0.0)),
                priority=_priority_for_nucleus(span, retention, kind),
                retention=retention,
                allowed_claim_scope=(
                    "selected_label_only"
                    if field_name in _LABEL_SOURCE_FIELDS
                    else "source_bounded_relation"
                    if grounding_kind == "user_stated_relation"
                    else "explicit_current_input"
                ),
                forbidden_inference_codes=(
                    "unsupported_cause",
                    "unsupported_personality",
                    "diagnosis",
                    "period_tendency_from_single_record",
                    "input_external_fact",
                ),
                source_claim_ids=tuple(claim_ids),
                source_meaning_block_keys=tuple(block_keys_by_span.get(span_id, ())),
            )
        )
    return tuple(nuclei)


def _apply_short_state_lexical_policy(
    nuclei: Sequence[GroundedSemanticNucleus],
    spans: Sequence[EvidenceSpan],
    *,
    material_quality: str,
    relations: Sequence[GroundedSemanticRelation],
) -> tuple[GroundedSemanticNucleus, ...]:
    """Attach source-bound lexical constraints to a true single short state.

    These codes are policy facts, not a completed response.  They tell the
    realizer and Gate that the user's predicate family must remain visible and
    that an unrelated sensation metaphor must not be introduced.
    """

    if material_quality != "short_state_sufficient" or relations:
        return tuple(nuclei)
    candidates = tuple(
        item
        for item in nuclei
        if item.retention == "required"
        and item.kind != "other_explicit"
        and any(field in _TEXT_SOURCE_FIELDS for field in item.source_fields)
    )
    if len(candidates) != 1:
        return tuple(nuclei)
    target_id = candidates[0].nucleus_id
    span_index = {
        _clean(getattr(span, "span_id", "")): span
        for span in spans
        if _clean(getattr(span, "span_id", ""))
    }
    source_text = " ".join(
        _clean(getattr(span_index.get(span_id), "raw_text", ""))
        for span_id in candidates[0].source_span_ids
    )
    policy_codes = [
        "lexical:preserve_source_predicate",
        "lexical:no_new_sensation_family",
    ]
    if _SOURCE_METAPHOR_RE.search(source_text):
        policy_codes.append("lexical:source_metaphor_present")
    output: list[GroundedSemanticNucleus] = []
    for item in nuclei:
        if item.nucleus_id != target_id:
            output.append(item)
            continue
        output.append(
            replace(
                item,
                semantic_frame=replace(
                    item.semantic_frame,
                    attribute_codes=tuple(
                        _dedupe([*item.semantic_frame.attribute_codes, *policy_codes])
                    ),
                ),
            )
        )
    return tuple(output)


def _claim_to_nucleus_id(
    board: PerspectiveBoard,
    claim_id: Any,
    nucleus_by_span: Mapping[str, str],
) -> str | None:
    claims = dict(getattr(board, "claim_index", {}) or getattr(board, "claims_by_id", {}) or {})
    claim = claims.get(_clean(claim_id))
    if claim is None:
        return None
    for span_id in _ordered_span_ids(getattr(claim, "evidence_span_ids", ()) or ()):
        if span_id in nucleus_by_span:
            return nucleus_by_span[span_id]
    return None


def _relation_retention(
    from_id: str,
    to_id: str,
    nucleus_index: Mapping[str, GroundedSemanticNucleus],
    *,
    relation_type: RelationKind,
    grounding_kind: GroundingKind,
) -> Retention:
    left = nucleus_index[from_id].retention
    right = nucleus_index[to_id].retention
    if "optional" in {left, right}:
        return "optional"
    # Adjacency-only inference is context, not a required claim.  A relation
    # becomes required only after structural operators promote it to a
    # source-stated relation (for example a continuation/refusal sentence).
    if grounding_kind == "bounded_structural_inference":
        left_roles = set(nucleus_index[from_id].semantic_frame.attribute_codes)
        right_roles = set(nucleus_index[to_id].semantic_frame.attribute_codes)
        if (
            relation_type == "action_supports_change"
            and left == right == "required"
            and "semantic_role:concrete_action_evidence" in right_roles
            and bool(
                left_roles
                & {
                    "semantic_role:retained_intention",
                    "semantic_role:current_change",
                }
            )
        ):
            return "required"
        return "should"
    if relation_type == "uncertain_connection":
        return "should"
    if left == right == "required":
        return "required"
    return "should"


def _append_relation_seed(seeds: list[_RelationSeed], seed: _RelationSeed) -> None:
    if not seed.from_nucleus_id or not seed.to_nucleus_id or seed.from_nucleus_id == seed.to_nucleus_id:
        return
    canonical_key = (seed.from_nucleus_id, seed.to_nucleus_id)
    grounding_rank = {
        "bounded_structural_inference": 0,
        "user_stated_relation": 1,
        "explicit": 2,
    }
    type_rank = {
        "uncertain_connection": 0,
        "coexistence": 1,
        "contrast": 2,
        "shift_from_to": 3,
        "evaluation_about_event": 3,
        "self_evaluation_about_state": 3,
        "temporal_before_after": 3,
        "user_stated_cause": 4,
        "user_stated_result": 4,
        "wish_and_constraint": 4,
        "attempt_and_block": 4,
        "action_supports_change": 4,
        "continuation_or_refusal": 5,
        "preserves_despite": 5,
    }

    def candidate_rank(item: _RelationSeed) -> tuple[int, int, int, float]:
        source_rank = 1
        if any(ref.startswith("evidence_relation_marker:") for ref in item.source_relation_ids):
            source_rank = 3
        elif "whole_input_source_order" in item.source_relation_ids:
            source_rank = 2
        elif "source_field_transition:memo_to_memo_action" in item.source_relation_ids:
            source_rank = 2
        elif item.source_relation_ids:
            source_rank = 4
        return (
            grounding_rank.get(item.grounding_kind, -1),
            source_rank,
            type_rank.get(item.type, 0),
            item.certainty,
        )
    for index, item in enumerate(seeds):
        item_key = (item.from_nucleus_id, item.to_nucleus_id)
        if item_key != canonical_key:
            continue
        # Existing graph edges, relation-marker evidence, and source-order
        # analysis can describe the same directed pair with different type
        # guesses.  Keep the strongest/first source-grounded interpretation so
        # the public surface does not repeat one pair under multiple labels.
        item_rank = candidate_rank(item)
        seed_rank = candidate_rank(seed)
        winner = seed if seed_rank > item_rank else item
        stronger_grounding = winner.grounding_kind
        # The strongest/first semantic owner keeps its binding evidence.  This
        # preserves an upstream relation edge's exact provenance instead of
        # silently adding a nearby marker that a later adapter happened to see.
        stronger_source_span_ids = (
            winner.source_span_ids or item.source_span_ids or seed.source_span_ids
        )
        seeds[index] = _RelationSeed(
            type=winner.type,
            from_nucleus_id=item.from_nucleus_id,
            to_nucleus_id=item.to_nucleus_id,
            source_span_ids=stronger_source_span_ids,
            grounding_kind=stronger_grounding,
            certainty=max(item.certainty, seed.certainty),
            retention=_retention_max(item.retention, seed.retention),
            source_relation_ids=tuple(
                _dedupe([*item.source_relation_ids, *seed.source_relation_ids])
            ),
            source_meaning_arc_keys=tuple(
                _dedupe([*item.source_meaning_arc_keys, *seed.source_meaning_arc_keys])
            ),
        )
        return
    seeds.append(seed)


def _build_relations(
    *,
    spans: Sequence[EvidenceSpan],
    board: PerspectiveBoard,
    nuclei: Sequence[GroundedSemanticNucleus],
    meaning_artifacts: _MeaningArtifacts,
) -> tuple[GroundedSemanticRelation, ...]:
    nucleus_index = {item.nucleus_id: item for item in nuclei}
    nucleus_by_span = {
        span_id: item.nucleus_id
        for item in nuclei
        for span_id in item.source_span_ids
    }
    span_index = {
        _clean(getattr(span, "span_id", "")): span
        for span in spans
        if _clean(getattr(span, "span_id", ""))
    }
    seeds: list[_RelationSeed] = []

    def source_text_for_ids(span_ids: Sequence[str]) -> str:
        return " ".join(
            _clean(getattr(span_index.get(span_id), "raw_text", ""))
            for span_id in span_ids
            if span_id in span_index
        )

    def boundary_marker_text(left_id: str, right_id: str) -> str:
        left_text = source_text_for_ids(nucleus_index[left_id].source_span_ids)
        right_text = source_text_for_ids(nucleus_index[right_id].source_span_ids)
        if _LEADING_CONTRAST_RE.search(right_text):
            return right_text
        if _BOUNDARY_RESULT_RE.search(right_text):
            return right_text
        if _BOUNDARY_CAUSE_RE.search(left_text):
            return left_text
        return ""

    def syntactically_dependent_pair(left_id: str, right_id: str) -> bool:
        left_text = source_text_for_ids(nucleus_index[left_id].source_span_ids)
        right_text = source_text_for_ids(nucleus_index[right_id].source_span_ids)
        return bool(
            re.search(r"(?:何故|なぜ|どうして)$", left_text)
            or re.match(r"^(?:と考えて(?:いた|しまって)|とか|という)", right_text)
        )

    existing_relations: Sequence[RelationEdge] = tuple(
        dict(getattr(board, "relation_index", {}) or getattr(board, "relations_by_id", {}) or {}).values()
    )
    for edge in existing_relations:
        from_id = _claim_to_nucleus_id(board, getattr(edge, "from_claim_id", ""), nucleus_by_span)
        to_id = _claim_to_nucleus_id(board, getattr(edge, "to_claim_id", ""), nucleus_by_span)
        if not from_id or not to_id:
            continue
        source_ids = tuple(_ordered_span_ids(getattr(edge, "evidence_span_ids", ()) or ()))
        relation_type = _RELATION_KIND_BY_EXISTING_TYPE.get(_clean(getattr(edge, "relation_type", "")))
        if relation_type is None:
            relation_type = _relation_type_for_pair(
                nucleus_index[from_id],
                nucleus_index[to_id],
                source_text=source_text_for_ids(source_ids),
            )
        _append_relation_seed(
            seeds,
            _RelationSeed(
                type=relation_type,
                from_nucleus_id=from_id,
                to_nucleus_id=to_id,
                source_span_ids=source_ids,
                grounding_kind="user_stated_relation",
                certainty=_clamp(getattr(edge, "confidence", 0.0)),
                retention=_relation_retention(
                    from_id,
                    to_id,
                    nucleus_index,
                    relation_type=relation_type,
                    grounding_kind="user_stated_relation",
                ),
                source_relation_ids=(_clean(getattr(edge, "edge_id", "")),),
            ),
        )

    text_spans = _sort_spans(_text_spans(spans))
    by_field: dict[str, list[EvidenceSpan]] = {}
    for span in text_spans:
        by_field.setdefault(_clean(getattr(span, "source_field", "")), []).append(span)
    for field_spans in by_field.values():
        for index, span in enumerate(field_spans):
            if _clean(getattr(span, "detected_type", "")) != "relation_marker":
                continue
            marker_id = _clean(getattr(span, "span_id", ""))
            marker_nucleus = nucleus_by_span.get(marker_id)
            previous = _nearest_substantive_span(field_spans, index - 1, -1)
            following = _nearest_substantive_span(field_spans, index + 1, 1)
            if _is_pure_relation_marker(span):
                left = nucleus_by_span.get(_clean(getattr(previous, "span_id", ""))) if previous else None
                right = nucleus_by_span.get(_clean(getattr(following, "span_id", ""))) if following else None
            else:
                marker_text = _clean(getattr(span, "raw_text", ""))
                # When both sides of an embedded marker remain in one ledger
                # span, the plan cannot truthfully invent an endpoint in the
                # preceding span.  Keep that span as an embedded major turn;
                # only a leading boundary marker may connect it locally to the
                # nearest previous substantive nucleus.
                if not (
                    _LEADING_CONTRAST_RE.search(marker_text)
                    or _BOUNDARY_RESULT_RE.search(marker_text)
                ):
                    continue
                left = nucleus_by_span.get(_clean(getattr(previous, "span_id", ""))) if previous else marker_nucleus
                right = marker_nucleus if previous else (
                    nucleus_by_span.get(_clean(getattr(following, "span_id", ""))) if following else None
                )
            if not left or not right:
                continue
            source_ids = tuple(
                _ordered_span_ids(
                    [marker_id, *nucleus_index[left].source_span_ids, *nucleus_index[right].source_span_ids]
                )
            )
            relation_type = _relation_type_for_pair(
                nucleus_index[left],
                nucleus_index[right],
                source_text=source_text_for_ids(source_ids),
                explicit_marker_text=_clean(getattr(span, "raw_text", "")),
            )
            _append_relation_seed(
                seeds,
                _RelationSeed(
                    type=relation_type,
                    from_nucleus_id=left,
                    to_nucleus_id=right,
                    source_span_ids=source_ids,
                    grounding_kind="user_stated_relation",
                    certainty=_clamp(getattr(span, "confidence", 0.0)),
                    retention=_relation_retention(
                        left,
                        right,
                        nucleus_index,
                        relation_type=relation_type,
                        grounding_kind="user_stated_relation",
                    ),
                    source_relation_ids=(f"evidence_relation_marker:{marker_id}",),
                ),
            )

    block_span_ids = _meaning_block_span_ids(meaning_artifacts.meaning_blocks, spans)
    arc = meaning_artifacts.whole_input_meaning_arc
    if arc is not None:
        representatives: list[str] = []
        for block_key in tuple(getattr(arc, "ordered_block_keys", ()) or ()):
            nucleus_id = next(
                (nucleus_by_span[span_id] for span_id in block_span_ids.get(_clean(block_key), ()) if span_id in nucleus_by_span),
                None,
            )
            if nucleus_id and (not representatives or representatives[-1] != nucleus_id):
                representatives.append(nucleus_id)
        for left, right in zip(representatives, representatives[1:]):
            if syntactically_dependent_pair(left, right):
                # Both fragments belong to one source clause.  They remain
                # required nuclei and are recombined by SentencePlan; treating
                # their punctuation split as a semantic edge would expose a
                # false from/to direction.
                continue
            source_ids = tuple(
                _ordered_span_ids([*nucleus_index[left].source_span_ids, *nucleus_index[right].source_span_ids])
            )
            source_text = source_text_for_ids(source_ids)
            marker_text = boundary_marker_text(left, right)
            relation_type = _relation_type_for_pair(
                nucleus_index[left],
                nucleus_index[right],
                source_text=source_text,
                explicit_marker_text=marker_text,
            )
            grounding_kind = _relation_grounding_kind_for_pair(
                nucleus_index[left],
                nucleus_index[right],
                relation_type=relation_type,
                source_text=source_text,
                explicit_marker_text=marker_text,
            )
            # Source-order arcs may bridge ``memo`` and ``memo_action``.  The
            # field boundary alone does not state a semantic relation, so it
            # must not become a required public claim.  The dedicated bounded
            # action-support edge below remains available as context.
            if set(nucleus_index[left].source_fields) != set(nucleus_index[right].source_fields):
                grounding_kind = "bounded_structural_inference"
            _append_relation_seed(
                seeds,
                _RelationSeed(
                    type=relation_type,
                    from_nucleus_id=left,
                    to_nucleus_id=right,
                    source_span_ids=source_ids,
                    grounding_kind=grounding_kind,
                    certainty=_clamp(getattr(arc, "clarity", 0.0) * 0.72),
                    retention=_relation_retention(
                        left,
                        right,
                        nucleus_index,
                        relation_type=relation_type,
                        grounding_kind=grounding_kind,
                    ),
                    source_relation_ids=("whole_input_source_order",),
                    source_meaning_arc_keys=(_clean(getattr(arc, "arc_key", "")),),
                ),
            )

    memo_ids = [
        nucleus_by_span[span.span_id]
        for span in text_spans
        if span.source_field == "memo" and span.span_id in nucleus_by_span
    ]
    action_ids = [
        nucleus_by_span[span.span_id]
        for span in text_spans
        if span.source_field == "memo_action" and span.span_id in nucleus_by_span
    ]
    action_evidence_ids = [
        nucleus_id
        for nucleus_id in action_ids
        if "semantic_role:concrete_action_evidence"
        in nucleus_index[nucleus_id].semantic_frame.attribute_codes
    ]
    intention_or_change_ids = [
        nucleus_id
        for nucleus_id in memo_ids
        if nucleus_index[nucleus_id].retention == "required"
        and bool(
            set(nucleus_index[nucleus_id].semantic_frame.attribute_codes)
            & {
                "semantic_role:retained_intention",
                "semantic_role:current_change",
            }
        )
    ]
    if intention_or_change_ids and action_evidence_ids:
        left, right = intention_or_change_ids[-1], action_evidence_ids[0]
        source_ids = tuple(
            _ordered_span_ids([*nucleus_index[left].source_span_ids, *nucleus_index[right].source_span_ids])
        )
        _append_relation_seed(
            seeds,
            _RelationSeed(
                type="action_supports_change",
                from_nucleus_id=left,
                to_nucleus_id=right,
                source_span_ids=source_ids,
                grounding_kind="bounded_structural_inference",
                certainty=0.64,
                retention=_relation_retention(
                    left,
                    right,
                    nucleus_index,
                    relation_type="action_supports_change",
                    grounding_kind="bounded_structural_inference",
                ),
                source_relation_ids=("source_field_transition:memo_to_memo_action",),
                source_meaning_arc_keys=(
                    _clean(getattr(arc, "arc_key", "")) if arc is not None else "current_input_source_order",
                ),
            ),
        )

    return tuple(
        GroundedSemanticRelation(
            relation_id=f"relation:r{index}",
            type=seed.type,
            from_nucleus_id=seed.from_nucleus_id,
            to_nucleus_id=seed.to_nucleus_id,
            source_span_ids=seed.source_span_ids,
            grounding_kind=seed.grounding_kind,
            certainty=seed.certainty,
            retention=seed.retention,
            source_relation_ids=tuple(_dedupe(seed.source_relation_ids)),
            source_meaning_arc_keys=tuple(_dedupe(seed.source_meaning_arc_keys)),
        )
        for index, seed in enumerate(seeds, start=1)
    )


def _build_unknown_boundaries(
    *,
    board: PerspectiveBoard,
    graph: ObservationGraph,
    nuclei: Sequence[GroundedSemanticNucleus],
) -> tuple[GroundedUnknownBoundary, ...]:
    dimensions = _dedupe(
        [
            *list(getattr(graph, "missing_information", ()) or ()),
            *list(getattr(board, "uncertainty", ()) or ()),
        ]
    )
    affected = tuple(item.nucleus_id for item in nuclei if item.retention == "required")[:4]
    return tuple(
        GroundedUnknownBoundary(
            unknown_id=f"unknown:u{index}",
            dimension=dimension,
            affected_nucleus_ids=affected,
        )
        for index, dimension in enumerate(dimensions, start=1)
    )


def _text_presence(spans: Sequence[EvidenceSpan]) -> Literal["text_present", "labels_only", "empty"]:
    if any(_clean(getattr(span, "source_field", "")) in _TEXT_SOURCE_FIELDS for span in spans):
        return "text_present"
    if spans:
        return "labels_only"
    return "empty"


def _material_quality(
    *,
    text_presence: str,
    safety_kind: str,
    spans: Sequence[EvidenceSpan],
    nuclei: Sequence[GroundedSemanticNucleus],
) -> Literal[
    "grounded",
    "short_state_sufficient",
    "limited_grounding",
    "labels_only_limited",
    "empty",
    "safety_routed",
]:
    if safety_kind in {TRIAGE_SAFETY_SUPPORT_REQUIRED, TRIAGE_SAFETY_BLOCKED_EMERGENCY}:
        return "safety_routed"
    if text_presence == "empty":
        return "empty"
    if text_presence == "labels_only":
        return "labels_only_limited"

    substantive = [span for span in _text_spans(spans) if _is_substantive_text_span(span)]
    if not substantive:
        return "limited_grounding"
    total_chars = sum(len(_compact(getattr(span, "raw_text", ""))) for span in substantive)
    text_nuclei = [
        nucleus
        for nucleus in nuclei
        if any(field in _TEXT_SOURCE_FIELDS for field in nucleus.source_fields)
        and nucleus.kind != "other_explicit"
    ]
    if not text_nuclei:
        return "limited_grounding"
    state_like = all(
        nucleus.kind in _SHORT_STATE_KINDS
        or nucleus.semantic_frame.modality in {"feeling", "refusal", "uncertain"}
        for nucleus in text_nuclei
    )
    contains_action_field = any("memo_action" in nucleus.source_fields for nucleus in text_nuclei)
    if total_chars <= 80 and len(substantive) <= 3 and state_like and not contains_action_field:
        return "short_state_sufficient"
    return "grounded"


def _semantic_complexity(
    *,
    nuclei: Sequence[GroundedSemanticNucleus],
    relations: Sequence[GroundedSemanticRelation],
    meaning_artifacts: _MeaningArtifacts,
) -> Literal["minimal", "single", "multi", "long_arc"]:
    if meaning_artifacts.coverage_plan is not None and bool(
        getattr(meaning_artifacts.coverage_plan, "clear_long_input", False)
    ):
        return "long_arc"
    text_count = sum(1 for item in nuclei if any(field in _TEXT_SOURCE_FIELDS for field in item.source_fields))
    if text_count == 0:
        return "minimal"
    if text_count == 1 and not relations:
        return "single"
    return "multi"


_NORMAL_HUMAN_FOLLOW_ROLE_PRIORITY: Final[tuple[GroundedHumanFollowRole, ...]] = (
    "help_seeking_preserved",
    "retained_intention",
    "concrete_effort",
    "valued_change",
    "burden_expression",
    "integrated_current_state",
)
_SELF_DENIAL_HUMAN_FOLLOW_ROLE_PRIORITY: Final[tuple[GroundedHumanFollowRole, ...]] = (
    "help_seeking_preserved",
    "protective_counterdirection",
    "concrete_effort",
    "retained_intention",
    "burden_expression",
    "integrated_current_state",
)
_RECEPTION_ACT_BY_FOLLOW_ROLE: Final[dict[GroundedHumanFollowRole, GroundedReceptionAct]] = {
    "integrated_current_state": "stay_with_current_burden",
    "burden_expression": "stay_with_current_burden",
    "concrete_effort": "honor_concrete_effort",
    "retained_intention": "protect_retained_intention",
    "valued_change": "recognize_lived_change",
    "help_seeking_preserved": "hold_help_seeking",
    "protective_counterdirection": "bounded_counter_self_denial",
}
_FOLLOW_PROFILE_BY_RECEPTION_ACT: Final[
    dict[
        GroundedReceptionAct,
        tuple[GroundedFollowElement, tuple[GroundedFollowElement, ...], GroundedFollowElement | None],
    ]
] = {
    "stay_with_current_burden": (
        "burden_understanding",
        ("existence_respect",),
        None,
    ),
    "honor_concrete_effort": (
        "effort_receiving",
        ("intent_affirmation",),
        None,
    ),
    "protect_retained_intention": (
        "intent_affirmation",
        ("existence_respect",),
        None,
    ),
    "recognize_lived_change": (
        "effort_receiving",
        ("intent_affirmation",),
        None,
    ),
    "hold_help_seeking": (
        "effort_receiving",
        ("existence_respect",),
        "intent_affirmation",
    ),
    "bounded_counter_self_denial": (
        "existence_respect",
        ("effort_receiving",),
        None,
    ),
    "respect_words_placed": (
        "existence_respect",
        (),
        None,
    ),
}
_STANCE_BY_RECEPTION_ACT: Final[dict[GroundedReceptionAct, GroundedReceptionStance]] = {
    "stay_with_current_burden": "quiet_presence",
    "honor_concrete_effort": "warm_recognition",
    "protect_retained_intention": "gentle_respect",
    "recognize_lived_change": "warm_recognition",
    "hold_help_seeking": "protective_presence",
    "bounded_counter_self_denial": "bounded_disagreement",
    "respect_words_placed": "gentle_respect",
}
_RECEPTION_FORBIDDEN_SURFACE_CODES: Final[tuple[str, ...]] = (
    "generic_empathy_suffix",
    "second_observation_summary",
    "internal_policy_explanation",
    "full_source_quote_replay",
    "all_input_enumeration",
    "duplicate_reception_move",
)
_RECEPTION_ACT_BY_OPPORTUNITY_FAMILY: Final[
    dict[GroundedReceptionOpportunityFamily, GroundedReceptionAct]
] = {
    "current_burden": "stay_with_current_burden",
    "concrete_effort": "honor_concrete_effort",
    "retained_intention": "protect_retained_intention",
    "lived_change": "recognize_lived_change",
    "help_seeking": "hold_help_seeking",
    "counterdirection": "bounded_counter_self_denial",
    "words_placed": "respect_words_placed",
}
_OPPORTUNITY_FAMILY_BY_RECEPTION_ACT: Final[
    dict[GroundedReceptionAct, GroundedReceptionOpportunityFamily]
] = {
    reception_act: family
    for family, reception_act in _RECEPTION_ACT_BY_OPPORTUNITY_FAMILY.items()
}
_OPPORTUNITY_FAMILY_ORDER: Final[tuple[GroundedReceptionOpportunityFamily, ...]] = (
    "help_seeking",
    "counterdirection",
    "concrete_effort",
    "lived_change",
    "retained_intention",
    "current_burden",
    "words_placed",
)
_OPPORTUNITY_ID_RE: Final = re.compile(r"^ro[1-9][0-9]*$")
_MOVE_ID_RE: Final = re.compile(r"^rm[1-9][0-9]*$")


def _grounded_human_follow_role_for_nucleus(
    nucleus: GroundedSemanticNucleus,
    *,
    safety_kind: str,
) -> GroundedHumanFollowRole:
    attributes = set(nucleus.semantic_frame.attribute_codes)
    if "operator:help_seeking" in attributes:
        return "help_seeking_preserved"
    if safety_kind == TRIAGE_SELF_DENIAL_SAFE_STATE_ANSWER and (
        "semantic_role:protective_or_limiting_refusal" in attributes
        or nucleus.semantic_frame.modality == "refusal"
        or (
            "operator:continuation" in attributes
            and nucleus.semantic_frame.polarity == "negative"
        )
    ):
        return "protective_counterdirection"

    # Performed action evidence wins over a wider-arc intention label.  A
    # merely unperformed negative action (for example an inability to move)
    # must remain an intention/burden rather than becoming "effort".
    if _is_explicit_action_nucleus(nucleus):
        return "concrete_effort"

    retained_intention = bool(
        nucleus.kind == "wish"
        or nucleus.semantic_frame.modality == "wish"
        or {
            "semantic_role:retained_intention",
            "semantic_role:next_intention",
        }
        & attributes
    )
    if retained_intention:
        return "retained_intention"
    if _is_reception_performed_action_nucleus(nucleus):
        return "concrete_effort"
    if nucleus.kind in {"change", "value"} or {
        "semantic_role:current_change",
        "semantic_role:explicit_evaluation",
        "semantic_role:positive_evaluation",
    } & attributes:
        return "valued_change"
    return "burden_expression"


def classify_grounded_human_follow_role(
    *,
    safety_kind: str,
    material_quality: str,
    required_nucleus_count: int,
    nuclei: Sequence[GroundedSemanticNucleus],
) -> GroundedHumanFollowRole:
    """Classify a body-free follow role from semantic nuclei.

    The classifier deliberately does not inspect case ids, source text, or a
    completed sentence.  Plan target selection and SentencePlan validation can
    therefore share one semantic decision without copying fixture cues.
    """

    candidates = tuple(nuclei)
    if (
        safety_kind != TRIAGE_SELF_DENIAL_SAFE_STATE_ANSWER
        and material_quality == "short_state_sufficient"
        and required_nucleus_count == 1
    ):
        return "integrated_current_state"
    if not candidates:
        return "burden_expression"

    roles = {
        _grounded_human_follow_role_for_nucleus(
            nucleus,
            safety_kind=safety_kind,
        )
        for nucleus in candidates
    }
    priority = (
        _SELF_DENIAL_HUMAN_FOLLOW_ROLE_PRIORITY
        if safety_kind == TRIAGE_SELF_DENIAL_SAFE_STATE_ANSWER
        else _NORMAL_HUMAN_FOLLOW_ROLE_PRIORITY
    )
    return next((role for role in priority if role in roles), "burden_expression")


def map_grounded_human_follow_role_to_reception_act(
    role: GroundedHumanFollowRole,
) -> GroundedReceptionAct:
    """Map the existing target classification to a distinct reception act."""

    try:
        return _RECEPTION_ACT_BY_FOLLOW_ROLE[role]
    except KeyError as exc:
        raise GroundedObservationPlanError(f"unsupported_grounded_human_follow_role:{role}") from exc


def _is_explicit_action_nucleus(nucleus: GroundedSemanticNucleus) -> bool:
    attributes = set(nucleus.semantic_frame.attribute_codes)
    if (
        "operator:help_seeking" in attributes
        and "operator:action" in attributes
    ):
        return True
    if "operator:wish" in attributes:
        return False
    result_evidence = bool(
        {
            "operator:result",
            "operator:positive_change",
            "operator:shift",
        }
        & attributes
    )
    unperformed_negative_intention = bool(
        nucleus.semantic_frame.modality == "intention"
        and nucleus.semantic_frame.polarity == "negative"
        and "operator:negation" in attributes
        and not result_evidence
    )
    if unperformed_negative_intention:
        return False
    if "semantic_role:concrete_action_evidence" in attributes:
        return True
    return bool(
        nucleus.kind == "action"
        and nucleus.semantic_frame.modality == "fact"
    )


def _is_reception_performed_action_nucleus(
    nucleus: GroundedSemanticNucleus,
) -> bool:
    """Accept performed action semantics without treating plans as actions."""

    attributes = set(nucleus.semantic_frame.attribute_codes)
    return bool(
        _is_explicit_action_nucleus(nucleus)
        or (
            nucleus.semantic_frame.modality == "fact"
            and "operator:action" in attributes
            and {
                "semantic_role:concrete_action",
                "semantic_role:concrete_action_evidence",
            }
            & attributes
        )
    )


def _is_valued_change_nucleus(nucleus: GroundedSemanticNucleus) -> bool:
    attributes = set(nucleus.semantic_frame.attribute_codes)
    return bool(
        nucleus.kind in {"change", "value"}
        or {
            "semantic_role:current_change",
            "semantic_role:explicit_evaluation",
            "semantic_role:positive_evaluation",
        }
        & attributes
    )


def _is_input_grounded_counterposition_nucleus(nucleus: GroundedSemanticNucleus) -> bool:
    attributes = set(nucleus.semantic_frame.attribute_codes)
    return bool(
        _is_explicit_action_nucleus(nucleus)
        or nucleus.semantic_frame.modality == "refusal"
        or (
            nucleus.kind == "wish"
            and nucleus.semantic_frame.modality in {"intention", "wish"}
        )
        or "operator:help_seeking" in attributes
        or "operator:continuation" in attributes
        or "operator:refusal" in attributes
        or "semantic_role:protective_or_limiting_refusal" in attributes
    )


def _is_reception_grounded_counterposition_nucleus(
    nucleus: GroundedSemanticNucleus,
) -> bool:
    """Recognize grounded action for RR2 without advancing the legacy Surface."""

    attributes = set(nucleus.semantic_frame.attribute_codes)
    return bool(
        _is_input_grounded_counterposition_nucleus(nucleus)
        or _is_reception_performed_action_nucleus(nucleus)
    )


def select_grounded_reception_act(
    *,
    human_follow_role: GroundedHumanFollowRole,
    safety_kind: str,
    material_quality: str,
    semantic_complexity: str,
    target_nuclei: Sequence[GroundedSemanticNucleus],
    available_nuclei: Sequence[GroundedSemanticNucleus],
) -> GroundedReceptionAct:
    """Select an act from body-free semantic structure, never fixture identity."""

    candidates = tuple(available_nuclei)
    target_ids = {item.nucleus_id for item in target_nuclei}
    if safety_kind == TRIAGE_SELF_DENIAL_SAFE_STATE_ANSWER:
        if any(
            _grounded_human_follow_role_for_nucleus(item, safety_kind=safety_kind)
            == "help_seeking_preserved"
            for item in candidates
        ):
            return "hold_help_seeking"
        if any(_is_input_grounded_counterposition_nucleus(item) for item in candidates):
            return "bounded_counter_self_denial"
        # The observation fact boundary still rejects the identity claim.  The
        # reception layer must not manufacture a counterposition without input
        # action, refusal, or intention evidence.
        return "stay_with_current_burden"

    if material_quality == "short_state_sufficient":
        return "stay_with_current_burden"
    if material_quality in {"limited_grounding", "labels_only_limited"} and not any(
        any(field in _TEXT_SOURCE_FIELDS for field in item.source_fields)
        for item in target_nuclei
    ):
        return "respect_words_placed"

    non_target_candidates = tuple(item for item in candidates if item.nucleus_id not in target_ids)
    if human_follow_role == "retained_intention" and any(
        _is_reception_performed_action_nucleus(item)
        for item in non_target_candidates
    ):
        return "honor_concrete_effort"
    if (
        human_follow_role == "concrete_effort"
        and semantic_complexity == "long_arc"
        and any(_is_valued_change_nucleus(item) for item in non_target_candidates)
    ):
        return "recognize_lived_change"
    return map_grounded_human_follow_role_to_reception_act(human_follow_role)


def _select_reception_support_nucleus_ids(
    *,
    primary_act: GroundedReceptionAct,
    human_follow_role: GroundedHumanFollowRole,
    target_nucleus_ids: Sequence[str],
    fact_boundary_nucleus_ids: Sequence[str],
    observation_owned_nucleus_ids: Sequence[str],
    nuclei: Sequence[GroundedSemanticNucleus],
) -> tuple[str, ...]:
    target_ids = set(target_nucleus_ids)
    observation_owned = set(observation_owned_nucleus_ids)
    candidates = tuple(
        item
        for item in nuclei
        if item.nucleus_id not in target_ids and item.nucleus_id in observation_owned
    )

    def first(predicate) -> tuple[str, ...]:
        selected = next((item for item in candidates if predicate(item)), None)
        return (selected.nucleus_id,) if selected is not None else ()

    if primary_act in {"hold_help_seeking", "bounded_counter_self_denial"}:
        fact_boundary = next(
            (
                nucleus_id
                for nucleus_id in fact_boundary_nucleus_ids
                if nucleus_id not in target_ids and nucleus_id in observation_owned
            ),
            None,
        )
        if fact_boundary:
            return (fact_boundary,)
        return first(_is_input_grounded_counterposition_nucleus)
    if primary_act == "honor_concrete_effort" and human_follow_role == "retained_intention":
        return first(_is_explicit_action_nucleus)
    if primary_act == "recognize_lived_change" and human_follow_role == "concrete_effort":
        return first(_is_valued_change_nucleus)
    if primary_act == "recognize_lived_change":
        return first(_is_explicit_action_nucleus)
    return ()


def _is_reception_lived_change_nucleus(
    nucleus: GroundedSemanticNucleus,
) -> bool:
    """Require an input-grounded positive/valued change, not a provisional miss."""

    attributes = set(nucleus.semantic_frame.attribute_codes)
    if "semantic_role:provisional_evaluation" in attributes:
        return False
    explicit_positive_evidence = bool(
        {
            "operator:positive_change",
            "semantic_role:explicit_result",
            "semantic_role:explicit_evaluation",
            "semantic_role:positive_evaluation",
        }
        & attributes
    )
    adverse_source_claim_without_positive_evidence = bool(
        any(
            code.startswith(
                (
                    "source_claim:pressure.",
                    "source_claim:conflict.",
                    "source_claim:limit.",
                )
            )
            for code in attributes
        )
        and not explicit_positive_evidence
    )
    if adverse_source_claim_without_positive_evidence:
        # A generic change/feeling parse is not evidence that a repeated
        # burden is a welcome lived change.  Keep adverse-only text in the
        # current-burden reception family unless the semantic layer recorded
        # an explicit positive change/result/evaluation.
        return False
    return bool(
        nucleus.semantic_frame.polarity == "positive"
        and explicit_positive_evidence
    )


def _reception_opportunity_families_for_nucleus(
    nucleus: GroundedSemanticNucleus,
    *,
    safety_kind: str,
) -> tuple[GroundedReceptionOpportunityFamily, ...]:
    """Map body-free nucleus semantics to distinct human contribution families."""

    attributes = set(nucleus.semantic_frame.attribute_codes)
    has_text_source = any(field in _TEXT_SOURCE_FIELDS for field in nucleus.source_fields)
    if "operator:help_seeking" in attributes:
        return (
            "help_seeking",
            *(
                ("counterdirection",)
                if safety_kind == TRIAGE_SELF_DENIAL_SAFE_STATE_ANSWER
                else ()
            ),
        )
    if (
        safety_kind == TRIAGE_SELF_DENIAL_SAFE_STATE_ANSWER
        and _is_reception_grounded_counterposition_nucleus(nucleus)
        and nucleus.kind != "self_evaluation"
    ):
        return ("counterdirection",)
    if _is_reception_performed_action_nucleus(nucleus):
        return ("concrete_effort",)
    if (
        nucleus.kind == "wish"
        or nucleus.semantic_frame.modality == "wish"
        or {
            "semantic_role:retained_intention",
            "semantic_role:next_intention",
        }
        & attributes
    ):
        return ("retained_intention",)
    if _is_reception_lived_change_nucleus(nucleus):
        return ("lived_change",)
    if has_text_source and (
        nucleus.semantic_frame.polarity == "negative"
        or nucleus.semantic_frame.modality in {"feeling", "refusal", "uncertain"}
        or nucleus.kind
        in {
            "state",
            "reaction",
            "constraint",
            "self_evaluation",
            "uncertainty",
        }
    ):
        return ("current_burden",)
    # A text-grounded but otherwise neutral nucleus still gives us something
    # present-tense to stay with.  ``words_placed`` is the deliberately narrow
    # fallback for labels-only / limited material.
    return ("current_burden",) if has_text_source else ("words_placed",)


def _opportunity_nucleus_rank(
    nucleus: GroundedSemanticNucleus,
    *,
    human_follow_target_ids: set[str],
    legacy_support_ids: set[str],
    relation_connected_ids: set[str],
) -> tuple[Any, ...]:
    return (
        0 if nucleus.nucleus_id in human_follow_target_ids else 1,
        0 if nucleus.nucleus_id in legacy_support_ids else 1,
        -_RETENTION_RANK[nucleus.retention],
        0 if nucleus.nucleus_id in relation_connected_ids else 1,
        0 if nucleus.grounding_kind in {"explicit", "user_stated_relation"} else 1,
        -float(nucleus.certainty),
        -float(nucleus.priority),
        _span_number(nucleus.source_span_ids[0] if nucleus.source_span_ids else ""),
    )


def _opportunity_priority(
    nucleus: GroundedSemanticNucleus,
    *,
    family: GroundedReceptionOpportunityFamily,
    human_follow_target_ids: set[str],
    relation_connected_ids: set[str],
    safety_required: bool,
) -> int:
    family_rank = len(_OPPORTUNITY_FAMILY_ORDER) - _OPPORTUNITY_FAMILY_ORDER.index(
        family
    )
    return int(
        _RETENTION_RANK[nucleus.retention] * 100
        + family_rank * 10
        + (40 if nucleus.nucleus_id in human_follow_target_ids else 0)
        + (20 if nucleus.nucleus_id in relation_connected_ids else 0)
        + (200 if safety_required else 0)
        + round(float(nucleus.priority) * 5)
    )


def build_grounded_reception_opportunities(
    *,
    human_follow_target_ids: Sequence[str],
    primary_nucleus_ids: Sequence[str],
    supporting_nucleus_ids: Sequence[str],
    fact_boundary_nucleus_ids: Sequence[str],
    nuclei: Sequence[GroundedSemanticNucleus],
    relations: Sequence[GroundedSemanticRelation],
    primary_reception_act: GroundedReceptionAct,
    safety_kind: str,
    material_quality: str,
) -> tuple[GroundedReceptionOpportunity, ...]:
    """Build a deterministic body-free RR2 opportunity inventory.

    The selector reads only semantic fields, ids, retention, relation
    membership, and Safety.  It never receives a case id, source body,
    expected hash, completed sentence, or raw character count.
    """

    nucleus_index = {item.nucleus_id: item for item in nuclei}
    observation_owned_ids = tuple(
        _dedupe(
            [
                *primary_nucleus_ids,
                *supporting_nucleus_ids,
                *fact_boundary_nucleus_ids,
            ]
        )
    )
    owned_nuclei = tuple(
        nucleus_index[nucleus_id]
        for nucleus_id in observation_owned_ids
        if nucleus_id in nucleus_index
    )
    text_nucleus_present = any(
        any(field in _TEXT_SOURCE_FIELDS for field in item.source_fields)
        for item in owned_nuclei
    )
    relation_connected_ids = {
        nucleus_id
        for relation in relations
        if relation.retention in {"required", "should"}
        for nucleus_id in (relation.from_nucleus_id, relation.to_nucleus_id)
    }
    follow_ids = set(human_follow_target_ids)
    legacy_support_ids = set(supporting_nucleus_ids)
    candidates_by_family: dict[
        GroundedReceptionOpportunityFamily,
        list[GroundedSemanticNucleus],
    ] = {}
    for nucleus in owned_nuclei:
        has_text_source = any(
            field in _TEXT_SOURCE_FIELDS for field in nucleus.source_fields
        )
        if text_nucleus_present and not has_text_source:
            continue
        for family in _reception_opportunity_families_for_nucleus(
            nucleus,
            safety_kind=safety_kind,
        ):
            candidates_by_family.setdefault(family, []).append(nucleus)

    # The established short-state contract is deliberately one quiet burden
    # move.  A terse wish/action must not be inflated merely because its lone
    # nucleus has a richer semantic label; Safety remains the only exception.
    if (
        material_quality == "short_state_sufficient"
        and safety_kind != TRIAGE_SELF_DENIAL_SAFE_STATE_ANSWER
        and owned_nuclei
    ):
        candidates_by_family = {"current_burden": list(owned_nuclei)}

    # Preserve the established body-free primary selector as the compatibility
    # anchor.  Its classification can be more specific than the nucleus-kind
    # mapper (for example, an event carrying a valued-change role).  This does
    # not invent a contribution: it binds that already-selected act to the
    # same request-local human-follow target and evidence.
    compatibility_family = _OPPORTUNITY_FAMILY_BY_RECEPTION_ACT[
        primary_reception_act
    ]
    if compatibility_family not in candidates_by_family:
        compatibility_nuclei = [
            nucleus_index[nucleus_id]
            for nucleus_id in human_follow_target_ids
            if nucleus_id in nucleus_index
        ]
        if not compatibility_nuclei:
            compatibility_nuclei = list(owned_nuclei[:1])
        compatibility_family_is_grounded = bool(
            compatibility_family != "lived_change"
            or any(
                _is_reception_lived_change_nucleus(nucleus)
                for nucleus in compatibility_nuclei
            )
        )
        if compatibility_nuclei and compatibility_family_is_grounded:
            candidates_by_family[compatibility_family] = compatibility_nuclei

    concrete_families = set(candidates_by_family) - {"words_placed"}
    if concrete_families and compatibility_family != "words_placed":
        candidates_by_family.pop("words_placed", None)
    richer_families = concrete_families - {"current_burden"}
    if (
        richer_families
        and safety_kind != TRIAGE_SELF_DENIAL_SAFE_STATE_ANSWER
        and material_quality != "short_state_sufficient"
        and compatibility_family != "current_burden"
    ):
        candidates_by_family.pop("current_burden", None)

    rows: list[GroundedReceptionOpportunity] = []
    for family in _OPPORTUNITY_FAMILY_ORDER:
        family_candidates = tuple(candidates_by_family.get(family, ()))
        if not family_candidates:
            continue
        representative = min(
            family_candidates,
            key=lambda item: (
                0
                if family == "lived_change"
                and {
                    "semantic_role:explicit_evaluation",
                    "semantic_role:positive_evaluation",
                }
                & set(item.semantic_frame.attribute_codes)
                else 1,
                *_opportunity_nucleus_rank(
                    item,
                    human_follow_target_ids=follow_ids,
                    legacy_support_ids=legacy_support_ids,
                    relation_connected_ids=relation_connected_ids,
                ),
            ),
        )
        target_ids: tuple[str, ...] = (representative.nucleus_id,)
        support_ids: tuple[str, ...] = ()
        if family == "counterdirection" and fact_boundary_nucleus_ids:
            fact_id = next(
                (
                    nucleus_id
                    for nucleus_id in fact_boundary_nucleus_ids
                    if nucleus_id in nucleus_index
                ),
                None,
            )
            if fact_id is not None and fact_id != representative.nucleus_id:
                target_ids = (fact_id,)
                support_ids = (representative.nucleus_id,)
        selected_nuclei = tuple(
            nucleus_index[nucleus_id]
            for nucleus_id in (*target_ids, *support_ids)
            if nucleus_id in nucleus_index
        )
        evidence_ids = tuple(
            _ordered_span_ids(
                span_id
                for item in selected_nuclei
                for span_id in item.source_span_ids
            )
        )
        safety_required = bool(
            safety_kind == TRIAGE_SELF_DENIAL_SAFE_STATE_ANSWER
            and family in {"help_seeking", "counterdirection"}
        )
        retention = max(
            (item.retention for item in selected_nuclei),
            key=lambda value: _RETENTION_RANK[value],
        )
        rows.append(
            GroundedReceptionOpportunity(
                opportunity_id="",
                family=family,
                reception_act=_RECEPTION_ACT_BY_OPPORTUNITY_FAMILY[family],
                target_nucleus_ids=target_ids,
                support_nucleus_ids=support_ids,
                source_evidence_span_ids=evidence_ids,
                retention=retention,
                priority=_opportunity_priority(
                    representative,
                    family=family,
                    human_follow_target_ids=follow_ids,
                    relation_connected_ids=relation_connected_ids,
                    safety_required=safety_required,
                ),
                source_field_count=len(
                    {
                        field
                        for item in selected_nuclei
                        for field in item.source_fields
                    }
                ),
                safety_required=safety_required,
            )
        )

    rows.sort(
        key=lambda item: (
            -item.priority,
            _OPPORTUNITY_FAMILY_ORDER.index(item.family),
            _span_number(
                item.source_evidence_span_ids[0]
                if item.source_evidence_span_ids
                else ""
            ),
        )
    )
    return tuple(
        replace(item, opportunity_id=f"ro{index}")
        for index, item in enumerate(rows, start=1)
    )


def _opportunities_are_distinct(
    left: GroundedReceptionOpportunity,
    right: GroundedReceptionOpportunity,
) -> bool:
    return bool(
        left.family != right.family
        or left.reception_act != right.reception_act
        or set(left.target_nucleus_ids) != set(right.target_nucleus_ids)
    )


def _select_reception_opportunities(
    opportunities: Sequence[GroundedReceptionOpportunity],
    *,
    legacy_primary_act: GroundedReceptionAct,
    safety_kind: str,
    semantic_complexity: str,
) -> tuple[GroundedReceptionOpportunity, ...]:
    inventory = tuple(opportunities)
    if not inventory:
        raise GroundedObservationPlanError("human_reception_opportunity_missing")
    primary = next(
        (
            item
            for item in inventory
            if item.reception_act == legacy_primary_act
        ),
        inventory[0],
    )
    selected: list[GroundedReceptionOpportunity] = [primary]
    by_family = {item.family: item for item in inventory}

    if safety_kind == TRIAGE_SELF_DENIAL_SAFE_STATE_ANSWER:
        if primary.family == "help_seeking":
            support_order = ("counterdirection",)
        elif primary.family == "counterdirection":
            support_order = ("current_burden",)
        else:
            support_order = ("counterdirection",)
    else:
        support_order_by_primary = {
            "concrete_effort": ("lived_change", "retained_intention"),
            "lived_change": ("concrete_effort", "retained_intention"),
            "retained_intention": ("lived_change", "concrete_effort"),
            "current_burden": (
                "concrete_effort",
                "retained_intention",
                "lived_change",
            ),
            "help_seeking": (
                "lived_change",
                "concrete_effort",
                "retained_intention",
            ),
            "counterdirection": ("current_burden",),
            "words_placed": (),
        }
        support_order = support_order_by_primary[primary.family]

    support_limit = 2 if semantic_complexity == "long_arc" else 1
    selected_support_count = 0
    for family in support_order:
        candidate = by_family.get(family)
        if candidate is None or candidate.retention not in {"required", "should"}:
            continue
        if all(_opportunities_are_distinct(candidate, item) for item in selected):
            selected.append(candidate)
            selected_support_count += 1
            if selected_support_count >= support_limit:
                break

    required_safety = tuple(
        item
        for item in inventory
        if item.safety_required and item not in selected
    )
    for item in required_safety:
        if len(selected) >= 3:
            raise GroundedObservationPlanError(
                "human_reception_required_safety_move_exceeds_limit"
            )
        if all(_opportunities_are_distinct(item, other) for other in selected):
            selected.append(item)
    return tuple(selected)


def _move_roles_by_opportunity_family(
    selected: Sequence[GroundedReceptionOpportunity],
) -> dict[str, GroundedReceptionMoveRole]:
    families = {item.family for item in selected}
    result: dict[str, GroundedReceptionMoveRole] = {}
    for item in selected:
        if item.family == "counterdirection":
            role: GroundedReceptionMoveRole = "bounded_counterposition"
        elif item.family in {"current_burden", "help_seeking", "words_placed"}:
            role = "felt_response"
        elif {"concrete_effort", "lived_change"} <= families:
            role = "attention" if item.family == "concrete_effort" else "felt_response"
        elif {"lived_change", "retained_intention"} <= families:
            role = "attention" if item.family == "lived_change" else "felt_response"
        elif {"concrete_effort", "retained_intention"} <= families:
            role = "attention" if item.family == "retained_intention" else "felt_response"
        elif item.family == "concrete_effort":
            role = "attention"
        elif item.family == "retained_intention":
            role = "significance"
        else:
            role = "felt_response"
        result[item.opportunity_id] = role
    return result


def _surface_strategy_for_move(
    opportunity: GroundedReceptionOpportunity,
    role: GroundedReceptionMoveRole,
) -> GroundedReceptionSurfaceStrategy:
    if role == "bounded_counterposition":
        return "explicit_emlis_counterposition"
    if opportunity.family == "current_burden":
        return "quiet_referent_first"
    if role == "attention":
        return "emlis_attention_first"
    if role == "significance":
        return "referent_significance_first"
    return "felt_response_first"


def _build_reception_depth_policy_and_moves(
    opportunities: Sequence[GroundedReceptionOpportunity],
    *,
    legacy_primary_act: GroundedReceptionAct,
    legacy_reference_mode: GroundedReferenceMode,
    safety_kind: str,
    semantic_complexity: str,
) -> tuple[GroundedReceptionDepthPolicy, tuple[GroundedReceptionMovePlan, ...]]:
    selected = _select_reception_opportunities(
        opportunities,
        legacy_primary_act=legacy_primary_act,
        safety_kind=safety_kind,
        semantic_complexity=semantic_complexity,
    )
    if safety_kind == TRIAGE_SELF_DENIAL_SAFE_STATE_ANSWER:
        safety_mode: GroundedReceptionSafetyMode = (
            "help_seeking_bounded"
            if any(item.family == "help_seeking" for item in selected)
            else "self_denial_bounded"
        )
        level: GroundedReceptionDepthLevel = "focused"
        min_sentences = 2 if len(selected) >= 2 else 1
        max_sentences = 2
    else:
        safety_mode = "standard"
        if len(selected) >= 2:
            level = "layered"
            min_sentences = 2
            max_sentences = min(3, len(selected))
        elif selected[0].family in {"current_burden", "words_placed"}:
            level = "minimal"
            min_sentences = max_sentences = 1
        else:
            level = "focused"
            min_sentences = max_sentences = 1

    roles = _move_roles_by_opportunity_family(selected)
    moves: list[GroundedReceptionMovePlan] = []
    for index, opportunity in enumerate(selected, start=1):
        role = roles[opportunity.opportunity_id]
        primary_element, secondary_elements, afterglow_element = (
            _FOLLOW_PROFILE_BY_RECEPTION_ACT[opportunity.reception_act]
        )
        follow_elements = tuple(
            _dedupe(
                [
                    primary_element,
                    *secondary_elements,
                    *(
                        (afterglow_element,)
                        if afterglow_element is not None
                        else ()
                    ),
                ]
            )
        )[:3]
        explicit = role == "bounded_counterposition"
        moves.append(
            GroundedReceptionMovePlan(
                move_id=f"rm{index}",
                move_role=role,
                reception_act=opportunity.reception_act,
                target_nucleus_ids=opportunity.target_nucleus_ids,
                support_nucleus_ids=opportunity.support_nucleus_ids,
                source_evidence_span_ids=opportunity.source_evidence_span_ids,
                follow_elements=follow_elements,
                speaker_presence="explicit_emlis" if explicit else "implicit_emlis",
                reference_mode=(
                    "explicit_emlis_counterposition"
                    if explicit
                    else legacy_reference_mode
                    if index == 1
                    else "anaphoric_first"
                ),
                surface_strategy=_surface_strategy_for_move(opportunity, role),
                required=(
                    opportunity.safety_required
                    or opportunity.retention in {"required", "should"}
                ),
                distinct_from_move_ids=tuple(item.move_id for item in moves),
            )
        )

    min_realized_moves = sum(1 for item in moves if item.required)
    policy = GroundedReceptionDepthPolicy(
        level=level,
        safety_mode=safety_mode,
        opportunity_count=len(tuple(opportunities)),
        selected_move_count=len(moves),
        selection_reason_codes=(
            "selection:semantic_opportunity_inventory",
            "selection:distinct_human_contributions",
            "selection:raw_character_count_unused",
            f"depth:{level}",
            f"safety:{safety_mode}",
        ),
        raw_character_count_used=False,
        min_sentences=min_sentences,
        max_sentences=max_sentences,
        min_realized_moves=max(1, min_realized_moves),
        # RR7 may safely integrate one pair only when three selected Moves
        # can still satisfy the layered two-sentence lower bound. Full
        # realization remains one Move per sentence.
        max_moves_per_sentence=2 if len(moves) == 3 else 1,
    )
    return policy, tuple(moves)


def build_grounded_human_reception_plan(
    *,
    required: bool,
    human_follow_target_ids: Sequence[str],
    primary_nucleus_ids: Sequence[str],
    supporting_nucleus_ids: Sequence[str],
    required_nucleus_ids: Sequence[str],
    fact_boundary_nucleus_ids: Sequence[str],
    nuclei: Sequence[GroundedSemanticNucleus],
    relations: Sequence[GroundedSemanticRelation],
    safety_kind: str,
    material_quality: str,
    semantic_complexity: str,
) -> GroundedHumanReceptionPlan | None:
    """Build the request-local body-free RR2/RR3 reception plan."""

    if not required:
        return None
    nucleus_index = {item.nucleus_id: item for item in nuclei}
    target_ids = tuple(_dedupe(human_follow_target_ids))
    target_nuclei = tuple(nucleus_index[item] for item in target_ids if item in nucleus_index)
    if not target_nuclei:
        raise GroundedObservationPlanError("human_reception_target_missing")

    human_follow_role = classify_grounded_human_follow_role(
        safety_kind=safety_kind,
        material_quality=material_quality,
        required_nucleus_count=len(tuple(required_nucleus_ids)),
        nuclei=target_nuclei,
    )
    observation_owned_ids = tuple(
        _dedupe(
            [
                *primary_nucleus_ids,
                *supporting_nucleus_ids,
                *fact_boundary_nucleus_ids,
            ]
        )
    )
    observation_owned_set = set(observation_owned_ids)
    available_nuclei = tuple(
        item for item in nuclei if item.nucleus_id in observation_owned_set
    )
    primary_act = select_grounded_reception_act(
        human_follow_role=human_follow_role,
        safety_kind=safety_kind,
        material_quality=material_quality,
        semantic_complexity=semantic_complexity,
        target_nuclei=target_nuclei,
        available_nuclei=available_nuclei,
    )
    support_ids = _select_reception_support_nucleus_ids(
        primary_act=primary_act,
        human_follow_role=human_follow_role,
        target_nucleus_ids=target_ids,
        fact_boundary_nucleus_ids=fact_boundary_nucleus_ids,
        observation_owned_nucleus_ids=observation_owned_ids,
        nuclei=nuclei,
    )
    selected_nuclei = tuple(
        nucleus_index[item]
        for item in (*target_ids, *support_ids)
        if item in nucleus_index
    )
    grounded_counterposition = any(
        _is_input_grounded_counterposition_nucleus(item) for item in selected_nuclei
    )
    secondary_act: GroundedReceptionAct | None = None
    if (
        safety_kind == TRIAGE_SELF_DENIAL_SAFE_STATE_ANSWER
        and primary_act == "hold_help_seeking"
        and grounded_counterposition
    ):
        secondary_act = "bounded_counter_self_denial"

    primary_element, secondary_elements, afterglow_element = _FOLLOW_PROFILE_BY_RECEPTION_ACT[
        primary_act
    ]
    bounded_counterposition = (
        primary_act == "bounded_counter_self_denial"
        or secondary_act == "bounded_counter_self_denial"
    )
    speaker_presence: GroundedSpeakerPresence = (
        "explicit_emlis" if bounded_counterposition else "implicit_emlis"
    )
    reference_mode: GroundedReferenceMode
    if bounded_counterposition:
        reference_mode = "explicit_emlis_counterposition"
    elif material_quality == "short_state_sufficient":
        reference_mode = "anaphoric_first"
    elif semantic_complexity in {"multi", "long_arc"}:
        reference_mode = "short_anchor_if_ambiguous"
    else:
        reference_mode = "anaphoric_first"

    opportunities = build_grounded_reception_opportunities(
        human_follow_target_ids=target_ids,
        primary_nucleus_ids=primary_nucleus_ids,
        supporting_nucleus_ids=supporting_nucleus_ids,
        fact_boundary_nucleus_ids=fact_boundary_nucleus_ids,
        nuclei=nuclei,
        relations=relations,
        primary_reception_act=primary_act,
        safety_kind=safety_kind,
        material_quality=material_quality,
    )
    depth_policy, moves = _build_reception_depth_policy_and_moves(
        opportunities,
        legacy_primary_act=primary_act,
        legacy_reference_mode=reference_mode,
        safety_kind=safety_kind,
        semantic_complexity=semantic_complexity,
    )
    # RR4 keeps the public follow target stable while expanding the aggregate
    # compatibility grounding to every selected Move.  ClausePlan remains the
    # owner of each individual Move binding; the aggregate fields keep the
    # existing Gate and recovery perimeter evidence-complete.
    move_nucleus_ids = tuple(
        _dedupe(
            nucleus_id
            for move in moves
            for nucleus_id in (
                *move.target_nucleus_ids,
                *move.support_nucleus_ids,
            )
        )
    )
    support_ids = tuple(
        nucleus_id
        for nucleus_id in move_nucleus_ids
        if nucleus_id not in set(target_ids)
    )
    selected_nuclei = tuple(
        nucleus_index[nucleus_id]
        for nucleus_id in (*target_ids, *support_ids)
        if nucleus_id in nucleus_index
    )
    # The compatibility primary remains aligned with the first planned Move.
    primary_act = moves[0].reception_act
    primary_element, secondary_elements, afterglow_element = (
        _FOLLOW_PROFILE_BY_RECEPTION_ACT[primary_act]
    )
    max_sentences = (
        1
        if material_quality == "short_state_sufficient"
        and safety_kind != TRIAGE_SELF_DENIAL_SAFE_STATE_ANSWER
        and secondary_act is None
        else 2
    )
    safety_modifier_codes: list[str] = []
    if safety_kind == TRIAGE_SELF_DENIAL_SAFE_STATE_ANSWER:
        safety_modifier_codes.extend(
            (
                "felt_state_is_real",
                "identity_claim_is_not_accepted",
            )
        )
        if bounded_counterposition or any(
            move.move_role == "bounded_counterposition" for move in moves
        ):
            safety_modifier_codes.append("counterposition_requires_input_evidence")

    source_evidence_ids = tuple(
        _ordered_span_ids(
            span_id
            for item in selected_nuclei
            for span_id in item.source_span_ids
        )
    )
    return GroundedHumanReceptionPlan(
        schema_version=GROUND_HUMAN_RECEPTION_PLAN_SCHEMA_VERSION,
        required=True,
        opportunities=opportunities,
        depth_policy=depth_policy,
        moves=moves,
        primary_reception_act=primary_act,
        secondary_reception_act=secondary_act,
        primary_follow_element=primary_element,
        secondary_follow_elements=secondary_elements,
        afterglow_follow_element=afterglow_element,
        target_nucleus_ids=target_ids,
        support_nucleus_ids=support_ids,
        source_evidence_span_ids=source_evidence_ids,
        observation_owned_nucleus_ids=observation_owned_ids,
        stance=_STANCE_BY_RECEPTION_ACT[primary_act],
        speaker_presence=speaker_presence,
        reference_mode=reference_mode,
        quote_policy=GroundedReceptionQuotePolicy(
            mode="no_full_quote_replay",
            max_anchor_count=1 if reference_mode == "short_anchor_if_ambiguous" else 0,
            max_anchor_visible_chars=16,
        ),
        sentence_policy=GroundedReceptionSentencePolicy(
            min_sentences=1,
            max_sentences=max_sentences,
        ),
        distinctness_policy=GroundedReceptionDistinctnessPolicy(
            observation_summary_repetition_allowed=False,
            relation_reexplanation_allowed=False,
            all_input_enumeration_allowed=False,
            policy_explanation_allowed=False,
            new_cause_allowed=False,
            new_identity_claim_allowed=False,
            advice_allowed=False,
            question_allowed=False,
        ),
        safety_modifier_codes=tuple(safety_modifier_codes),
        forbidden_surface_codes=_RECEPTION_FORBIDDEN_SURFACE_CODES,
    )


def classify_grounded_human_follow_delivery(
    *,
    safety_kind: str,
    material_quality: str,
    required_nucleus_count: int,
    target_nuclei: Sequence[GroundedSemanticNucleus],
    relations: Sequence[GroundedSemanticRelation],
    required_relation_ids: Sequence[str],
    fact_boundary_nucleus_ids: Sequence[str] = (),
) -> GroundedHumanFollowDelivery:
    """Keep the human reception contribution structurally separate.

    ``見えたこと：`` and ``Emlisから：`` are a mandatory public-body
    contract for every generated Emlis observation, including short-state and
    limited-input observations.  A semantic observation line may cover the
    same nucleus, but it must not absorb the human reception contribution.
    Keeping the delivery separate prevents an internal ``human_follow`` atom
    from being mistaken for a visible second section.
    """

    targets = tuple(target_nuclei)
    if not targets:
        return "not_required"

    # Retain the arguments in the contract because callers and tests use this
    # classifier as the single body-free decision point.  They no longer alter
    # the visible section layout.
    _ = (
        safety_kind,
        material_quality,
        required_nucleus_count,
        relations,
        required_relation_ids,
        fact_boundary_nucleus_ids,
    )
    return "separate_distinct_contribution"


def _is_grounded_human_follow_candidate(nucleus: GroundedSemanticNucleus) -> bool:
    if not any(field in _TEXT_SOURCE_FIELDS for field in nucleus.source_fields):
        return False
    attributes = set(nucleus.semantic_frame.attribute_codes)
    if nucleus.kind != "other_explicit":
        return True
    return bool(
        "operator:help_seeking" in attributes
        or "operator:action" in attributes
        or "operator:wish" in attributes
        or any(code.startswith("semantic_role:") for code in attributes)
    )


def _build_response_and_policies(
    *,
    nuclei: Sequence[GroundedSemanticNucleus],
    relations: Sequence[GroundedSemanticRelation],
    safety_decision: EmlisSafetyTriageDecision,
    complexity: str,
    material_quality: str,
) -> tuple[GroundedResponsePlan, GroundedCoverageRequirements, GroundedSurfacePolicy, GroundedSafetyPolicy]:
    ordered = sorted(
        nuclei,
        key=lambda item: (-_RETENTION_RANK[item.retention], -item.priority, _span_number(item.source_span_ids[0])),
    )
    required_ids = tuple(item.nucleus_id for item in ordered if item.retention == "required")
    optional_ids = tuple(item.nucleus_id for item in ordered if item.retention == "optional")
    required_relation_ids = tuple(item.relation_id for item in relations if item.retention == "required")
    planned_relation_ids = tuple(item.relation_id for item in relations if item.retention in {"required", "should"})

    relation_weight = {
        "preserves_despite": 6,
        "continuation_or_refusal": 6,
        "shift_from_to": 5,
        "user_stated_cause": 5,
        "user_stated_result": 5,
        "wish_and_constraint": 4,
        "action_supports_change": 3,
        "contrast": 3,
    }
    endpoint_weight: dict[str, int] = {}
    for relation in relations:
        if relation.relation_id not in required_relation_ids:
            continue
        weight = relation_weight.get(relation.type, 2)
        endpoint_weight[relation.from_nucleus_id] = max(
            endpoint_weight.get(relation.from_nucleus_id, 0), weight
        )
        endpoint_weight[relation.to_nucleus_id] = max(
            endpoint_weight.get(relation.to_nucleus_id, 0), weight
        )

    def primary_score(item: GroundedSemanticNucleus) -> int:
        roles = set(item.semantic_frame.attribute_codes)
        semantic_weight = 0
        for role, weight in (
            ("semantic_role:counterevidence", 10),
            ("semantic_role:provisional_evaluation", 10),
            ("semantic_role:explicit_evaluation", 9),
            ("semantic_role:embedded_turn", 8),
            ("semantic_role:current_change", 7),
            ("semantic_role:contrast_after", 7),
            ("semantic_role:contrast_before", 6),
            ("semantic_role:initial_condition", 5),
            ("semantic_role:retained_intention", 5),
            ("semantic_role:concrete_action_evidence", 4),
        ):
            if role in roles:
                semantic_weight = max(semantic_weight, weight)
        return semantic_weight + endpoint_weight.get(item.nucleus_id, 0)

    text_required = [
        item
        for item in ordered
        if item.retention == "required"
        and any(field in _TEXT_SOURCE_FIELDS for field in item.source_fields)
    ]
    if text_required:
        highest_primary_score = max(primary_score(item) for item in text_required)
        selected_primary_ids = tuple(
            item.nucleus_id
            for item in sorted(text_required, key=lambda item: _span_number(item.source_span_ids[0]))
            if primary_score(item) >= max(1, highest_primary_score - 2)
        )
        primary_ids = selected_primary_ids or (text_required[0].nucleus_id,)
    else:
        primary_ids = tuple(required_ids or tuple(item.nucleus_id for item in ordered[:1]))
    supporting_ids = tuple(
        item.nucleus_id
        for item in ordered
        if item.nucleus_id not in primary_ids and item.retention in {"required", "should"}
    )

    safety_evidence_ids = set(getattr(safety_decision, "evidence_span_ids", ()) or ())
    safety_nuclei = tuple(item for item in nuclei if set(item.source_span_ids) & safety_evidence_ids)
    separate_safety = safety_decision.safety_triage_kind in {
        TRIAGE_SAFETY_SUPPORT_REQUIRED,
        TRIAGE_SAFETY_BLOCKED_EMERGENCY,
    }
    fact_boundary_required = safety_decision.safety_triage_kind in {
        TRIAGE_SELF_DENIAL_SAFE_STATE_ANSWER,
        TRIAGE_SAFETY_SUPPORT_REQUIRED,
        TRIAGE_SAFETY_BLOCKED_EMERGENCY,
    }
    if safety_decision.safety_triage_kind == TRIAGE_SELF_DENIAL_SAFE_STATE_ANSWER:
        self_evaluation_ids = tuple(
            item.nucleus_id
            for item in ordered
            if item.kind == "self_evaluation"
            and item.retention in {"required", "should"}
        )
        safety_self_evaluation_ids = tuple(
            item.nucleus_id for item in safety_nuclei if item.kind == "self_evaluation"
        )
        fact_boundary_ids = (
            safety_self_evaluation_ids
            or self_evaluation_ids[:1]
            or tuple(item.nucleus_id for item in safety_nuclei[:1])
            or primary_ids[:1]
        )
    else:
        fact_boundary_ids = tuple(item.nucleus_id for item in safety_nuclei) if fact_boundary_required else ()

    candidate_ids = tuple(_dedupe([*primary_ids, *supporting_ids, *required_ids]))
    candidate_index = {item.nucleus_id: item for item in nuclei}
    follow_candidates = tuple(
        candidate_index[nucleus_id]
        for nucleus_id in candidate_ids
        if nucleus_id in candidate_index
        and candidate_index[nucleus_id].retention in {"required", "should"}
        and _is_grounded_human_follow_candidate(candidate_index[nucleus_id])
    )
    follow_role_priority = (
        _SELF_DENIAL_HUMAN_FOLLOW_ROLE_PRIORITY
        if safety_decision.safety_triage_kind == TRIAGE_SELF_DENIAL_SAFE_STATE_ANSWER
        else _NORMAL_HUMAN_FOLLOW_ROLE_PRIORITY
    )
    follow_role_rank = {role: index for index, role in enumerate(follow_role_priority)}
    primary_set = set(primary_ids)
    supporting_set = set(supporting_ids)
    relation_connected_ids = {
        endpoint
        for relation in relations
        if relation.relation_id in required_relation_ids
        or relation.type == "action_supports_change"
        for endpoint in (relation.from_nucleus_id, relation.to_nucleus_id)
    }

    def follow_rank(item: GroundedSemanticNucleus) -> tuple[Any, ...]:
        role = classify_grounded_human_follow_role(
            safety_kind=safety_decision.safety_triage_kind,
            material_quality=material_quality,
            required_nucleus_count=len(required_ids),
            nuclei=(item,),
        )
        attributes = set(item.semantic_frame.attribute_codes)
        role_explicit = bool(
            (role == "retained_intention" and (
                item.semantic_frame.modality in {"wish", "intention"}
                or {
                    "semantic_role:retained_intention",
                    "semantic_role:next_intention",
                } & attributes
            ))
            or (role == "concrete_effort" and {
                "semantic_role:concrete_action",
                "semantic_role:concrete_action_evidence",
            } & attributes)
            or (role == "valued_change" and {
                "semantic_role:current_change",
                "semantic_role:explicit_evaluation",
                "semantic_role:positive_evaluation",
            } & attributes)
            or (role == "help_seeking_preserved" and "operator:help_seeking" in attributes)
            or (
                role == "protective_counterdirection"
                and "semantic_role:protective_or_limiting_refusal" in attributes
            )
        )
        response_membership_rank = (
            0 if item.nucleus_id in primary_set else 1 if item.nucleus_id in supporting_set else 2
        )
        return (
            follow_role_rank.get(role, len(follow_role_rank)),
            -_RETENTION_RANK[item.retention],
            0 if role_explicit else 1,
            response_membership_rank,
            0 if item.nucleus_id in relation_connected_ids else 1,
            0 if item.grounding_kind in {"explicit", "user_stated_relation"} else 1,
            -float(item.certainty),
            -float(item.priority),
            _span_number(item.source_span_ids[0] if item.source_span_ids else ""),
        )

    selected_follow = min(follow_candidates, key=follow_rank) if follow_candidates else None
    follow_ids = (selected_follow.nucleus_id,) if selected_follow is not None else primary_ids[:1]

    observable_nucleus_present = bool(nuclei)
    human_follow_required = bool(observable_nucleus_present) and not separate_safety and material_quality != "empty"
    if not human_follow_required:
        follow_ids = ()

    if separate_safety:
        surface_shape: Literal["plain", "two_stage", "multi_paragraph", "separate_safety_surface"] = "separate_safety_surface"
    elif material_quality == "empty":
        surface_shape = "plain"
    else:
        # Long inputs may use multiple paragraphs *inside* the two labelled
        # sections.  They do not change the public body contract.
        surface_shape = "two_stage"

    if safety_decision.safety_triage_kind == TRIAGE_SELF_DENIAL_SAFE_STATE_ANSWER:
        response_kind = TRIAGE_SELF_DENIAL_SAFE_STATE_ANSWER
    elif separate_safety:
        response_kind = _clean(getattr(safety_decision, "response_kind", "")) or safety_decision.safety_triage_kind
    else:
        response_kind = {
            "short_state_sufficient": "short_state_observation",
            "limited_grounding": "limited_grounding_observation",
            "labels_only_limited": "labels_only_limited_observation",
            "empty": "unavailable",
        }.get(material_quality, "normal_observation")

    human_reception_plan = build_grounded_human_reception_plan(
        required=human_follow_required,
        human_follow_target_ids=follow_ids,
        primary_nucleus_ids=primary_ids,
        supporting_nucleus_ids=supporting_ids,
        required_nucleus_ids=required_ids,
        fact_boundary_nucleus_ids=fact_boundary_ids,
        nuclei=nuclei,
        relations=relations,
        safety_kind=safety_decision.safety_triage_kind,
        material_quality=material_quality,
        semantic_complexity=complexity,
    )
    response = GroundedResponsePlan(
        response_kind=response_kind,
        primary_nucleus_ids=primary_ids,
        supporting_nucleus_ids=supporting_ids,
        relation_ids=planned_relation_ids,
        fact_boundary_nucleus_ids=tuple(fact_boundary_ids),
        human_follow_target_ids=tuple(follow_ids),
        human_reception_plan=human_reception_plan,
        required_nucleus_ids=required_ids,
        optional_nucleus_ids=optional_ids,
        question_policy=GroundedQuestionPolicy(),
        surface_shape=surface_shape,
    )
    coverage = GroundedCoverageRequirements(
        required_nucleus_ids=required_ids,
        required_relation_ids=required_relation_ids,
        human_follow_required=human_follow_required,
        fact_boundary_required=fact_boundary_required,
    )
    surface = GroundedSurfacePolicy(
        content_source="separate_safety_owner" if separate_safety else "grounded_plan_only",
        generic_observation_surface_allowed=not separate_safety,
        hedge_policy=(
            "limited_single_input_scope"
            if material_quality in {"limited_grounding", "labels_only_limited"}
            else "single_input_scope"
        ),
    )
    safety = GroundedSafetyPolicy(
        safety_kind=_clean(getattr(safety_decision, "safety_triage_kind", "")) or TRIAGE_SAFE_OBSERVATION,
        identity_claim_must_not_be_accepted_as_fact=bool(
            getattr(safety_decision, "must_not_accept_identity_claim_as_fact", False)
        ),
        requires_separate_safety_surface=bool(
            getattr(safety_decision, "requires_separate_safety_surface", False)
        ),
        grounded_plan_overlay_allowed=not separate_safety,
        required_boundary_codes=tuple(
            _dedupe(
                [
                    *list(getattr(safety_decision, "reason_codes", ()) or ()),
                    *list(getattr(safety_decision, "boundary_types", ()) or ()),
                ]
            )
        ),
    )
    return response, coverage, surface, safety


def _all_plan_evidence_ids(
    nuclei: Sequence[GroundedSemanticNucleus],
    relations: Sequence[GroundedSemanticRelation],
    unknowns: Sequence[GroundedUnknownBoundary],
) -> tuple[str, ...]:
    return tuple(
        _ordered_span_ids(
            [
                *[span_id for item in nuclei for span_id in item.source_span_ids],
                *[span_id for item in relations for span_id in item.source_span_ids],
                *[span_id for item in unknowns for span_id in item.evidence_span_ids],
            ]
        )
    )


def validate_grounded_human_reception_plan(
    reception_plan: GroundedHumanReceptionPlan,
    *,
    expected_target_ids: Sequence[str],
    nucleus_index: Mapping[str, GroundedSemanticNucleus],
    resolver: EvidenceSpanResolver,
    safety_kind: str,
    material_quality: str,
) -> tuple[str, ...]:
    """Validate the nested plan without inspecting source text or a surface."""

    issues: list[str] = []
    if reception_plan.schema_version != GROUND_HUMAN_RECEPTION_PLAN_SCHEMA_VERSION:
        issues.append("human_reception_plan_schema_version_mismatch")
    if not reception_plan.required:
        issues.append("human_reception_plan_present_but_not_required")

    allowed_acts = set(_FOLLOW_PROFILE_BY_RECEPTION_ACT)
    allowed_follow_elements = {
        element
        for primary, secondary, afterglow in _FOLLOW_PROFILE_BY_RECEPTION_ACT.values()
        for element in (primary, *secondary, afterglow)
        if element is not None
    }
    allowed_families = set(_RECEPTION_ACT_BY_OPPORTUNITY_FAMILY)
    observation_owned_set = set(reception_plan.observation_owned_nucleus_ids)
    opportunities = tuple(reception_plan.opportunities)
    if not opportunities:
        issues.append("human_reception_opportunity_missing")
    opportunity_index: dict[str, GroundedReceptionOpportunity] = {}
    opportunity_signatures: set[tuple[Any, ...]] = set()
    for index, opportunity in enumerate(opportunities, start=1):
        expected_id = f"ro{index}"
        if not _OPPORTUNITY_ID_RE.fullmatch(opportunity.opportunity_id):
            issues.append("human_reception_opportunity_id_invalid")
        if opportunity.opportunity_id != expected_id:
            issues.append("human_reception_opportunity_order_invalid")
        if opportunity.opportunity_id in opportunity_index:
            issues.append("human_reception_opportunity_id_duplicate")
        opportunity_index[opportunity.opportunity_id] = opportunity
        if opportunity.family not in allowed_families:
            issues.append("human_reception_opportunity_family_invalid")
        elif (
            opportunity.reception_act
            != _RECEPTION_ACT_BY_OPPORTUNITY_FAMILY[opportunity.family]
        ):
            issues.append("human_reception_opportunity_act_mismatch")

        opportunity_target_ids = tuple(opportunity.target_nucleus_ids)
        opportunity_support_ids = tuple(opportunity.support_nucleus_ids)
        if not opportunity_target_ids:
            issues.append("human_reception_opportunity_target_missing")
        if len(opportunity_target_ids) != len(set(opportunity_target_ids)):
            issues.append("human_reception_opportunity_target_duplicate")
        if len(opportunity_support_ids) != len(set(opportunity_support_ids)):
            issues.append("human_reception_opportunity_support_duplicate")
        if set(opportunity_target_ids) & set(opportunity_support_ids):
            issues.append("human_reception_opportunity_target_support_overlap")
        for nucleus_id in (*opportunity_target_ids, *opportunity_support_ids):
            if nucleus_id not in nucleus_index:
                issues.append(
                    f"human_reception_opportunity_unknown_nucleus:{nucleus_id}"
                )
            elif nucleus_id not in observation_owned_set:
                issues.append(
                    f"human_reception_opportunity_not_observation_owned:{nucleus_id}"
                )

        opportunity_nuclei = tuple(
            nucleus_index[nucleus_id]
            for nucleus_id in (*opportunity_target_ids, *opportunity_support_ids)
            if nucleus_id in nucleus_index
        )
        expected_opportunity_evidence = tuple(
            _ordered_span_ids(
                span_id
                for nucleus in opportunity_nuclei
                for span_id in nucleus.source_span_ids
            )
        )
        opportunity_evidence = tuple(opportunity.source_evidence_span_ids)
        if not opportunity_evidence:
            issues.append("human_reception_opportunity_evidence_missing")
        if opportunity_evidence != expected_opportunity_evidence:
            issues.append("human_reception_opportunity_evidence_mismatch")
        for span_id in opportunity_evidence:
            if not _EVIDENCE_ID_RE.fullmatch(span_id):
                issues.append(
                    f"human_reception_opportunity_invalid_evidence:{span_id}"
                )
        for span_id in resolver.unresolved_ids(opportunity_evidence):
            issues.append(
                f"human_reception_opportunity_unresolved_evidence:{span_id}"
            )

        if opportunity.retention not in _RETENTION_RANK:
            issues.append("human_reception_opportunity_retention_invalid")
        elif opportunity_nuclei:
            expected_retention = max(
                (nucleus.retention for nucleus in opportunity_nuclei),
                key=lambda value: _RETENTION_RANK[value],
            )
            if opportunity.retention != expected_retention:
                issues.append("human_reception_opportunity_retention_mismatch")
        if (
            not isinstance(opportunity.priority, int)
            or isinstance(opportunity.priority, bool)
            or opportunity.priority <= 0
        ):
            issues.append("human_reception_opportunity_priority_invalid")
        expected_source_field_count = len(
            {
                field
                for nucleus in opportunity_nuclei
                for field in nucleus.source_fields
            }
        )
        if opportunity.source_field_count != expected_source_field_count:
            issues.append("human_reception_opportunity_source_field_count_mismatch")
        if not isinstance(opportunity.safety_required, bool):
            issues.append("human_reception_opportunity_safety_required_invalid")
        expected_safety_required = bool(
            safety_kind == TRIAGE_SELF_DENIAL_SAFE_STATE_ANSWER
            and opportunity.family in {"help_seeking", "counterdirection"}
        )
        if opportunity.safety_required is not expected_safety_required:
            issues.append("human_reception_opportunity_safety_required_mismatch")
        signature = (
            opportunity.family,
            opportunity.reception_act,
            opportunity_target_ids,
            opportunity_support_ids,
        )
        if signature in opportunity_signatures:
            issues.append("human_reception_opportunity_duplicate")
        opportunity_signatures.add(signature)
        if opportunity.family == "counterdirection" and not any(
            _is_reception_grounded_counterposition_nucleus(nucleus)
            for nucleus in opportunity_nuclei
        ):
            issues.append("human_reception_opportunity_ungrounded_counterposition")

    depth_policy = reception_plan.depth_policy
    moves = tuple(reception_plan.moves)
    if depth_policy.level not in {"minimal", "focused", "layered"}:
        issues.append("human_reception_depth_level_invalid")
    if depth_policy.safety_mode not in {
        "standard",
        "self_denial_bounded",
        "help_seeking_bounded",
    }:
        issues.append("human_reception_depth_safety_mode_invalid")
    if depth_policy.opportunity_count != len(opportunities):
        issues.append("human_reception_depth_opportunity_count_mismatch")
    if depth_policy.selected_move_count != len(moves):
        issues.append("human_reception_depth_selected_move_count_mismatch")
    if depth_policy.raw_character_count_used is not False:
        issues.append("human_reception_depth_raw_character_count_forbidden")
    if not depth_policy.selection_reason_codes:
        issues.append("human_reception_depth_selection_reason_missing")
    if len(depth_policy.selection_reason_codes) != len(
        set(depth_policy.selection_reason_codes)
    ):
        issues.append("human_reception_depth_selection_reason_duplicate")
    if any(
        not _is_body_free_code(code)
        for code in depth_policy.selection_reason_codes
    ):
        issues.append("human_reception_depth_selection_reason_non_body_free_code")
    if not 1 <= depth_policy.min_sentences <= depth_policy.max_sentences <= 3:
        issues.append("human_reception_depth_sentence_budget_invalid")
    if not 1 <= depth_policy.max_moves_per_sentence <= 2:
        issues.append("human_reception_depth_moves_per_sentence_invalid")
    if not 1 <= len(moves) <= 3:
        issues.append("human_reception_move_count_invalid")
    if not 1 <= depth_policy.min_realized_moves <= max(1, len(moves)):
        issues.append("human_reception_depth_min_realized_moves_invalid")
    required_move_count = sum(1 for move in moves if move.required)
    if depth_policy.min_realized_moves != max(1, required_move_count):
        issues.append("human_reception_depth_min_realized_moves_mismatch")
    if depth_policy.level == "minimal" and (
        len(moves) != 1
        or depth_policy.min_sentences != 1
        or depth_policy.max_sentences != 1
    ):
        issues.append("human_reception_depth_minimal_contract_invalid")
    if depth_policy.level == "focused":
        if len(moves) not in {1, 2}:
            issues.append("human_reception_depth_focused_contract_invalid")
        if depth_policy.max_sentences > 2:
            issues.append(
                "human_reception_depth_focused_sentence_budget_invalid"
            )
    if depth_policy.level == "layered" and (
        len(moves) < 2 or depth_policy.min_sentences < 2
    ):
        issues.append("human_reception_depth_layered_contract_invalid")

    allowed_move_roles = {
        "attention",
        "significance",
        "felt_response",
        "bounded_counterposition",
    }
    allowed_surface_strategies = {
        "quiet_referent_first",
        "emlis_attention_first",
        "referent_significance_first",
        "felt_response_first",
        "explicit_emlis_counterposition",
    }
    move_index: dict[str, GroundedReceptionMovePlan] = {}
    selected_opportunity_ids: set[str] = set()
    move_signatures: set[tuple[Any, ...]] = set()
    for index, move in enumerate(moves, start=1):
        expected_id = f"rm{index}"
        if not _MOVE_ID_RE.fullmatch(move.move_id):
            issues.append("human_reception_move_id_invalid")
        if move.move_id != expected_id:
            issues.append("human_reception_move_order_invalid")
        if move.move_id in move_index:
            issues.append("human_reception_move_id_duplicate")
        move_index[move.move_id] = move
        if move.move_role not in allowed_move_roles:
            issues.append("human_reception_move_role_invalid")
        if move.reception_act not in allowed_acts:
            issues.append("human_reception_move_act_invalid")
        move_target_ids = tuple(move.target_nucleus_ids)
        move_support_ids = tuple(move.support_nucleus_ids)
        if not move_target_ids:
            issues.append("human_reception_move_target_missing")
        if len(move_target_ids) != len(set(move_target_ids)):
            issues.append("human_reception_move_target_duplicate")
        if len(move_support_ids) != len(set(move_support_ids)):
            issues.append("human_reception_move_support_duplicate")
        if set(move_target_ids) & set(move_support_ids):
            issues.append("human_reception_move_target_support_overlap")
        for nucleus_id in (*move_target_ids, *move_support_ids):
            if nucleus_id not in nucleus_index:
                issues.append(f"human_reception_move_unknown_nucleus:{nucleus_id}")
            elif nucleus_id not in observation_owned_set:
                issues.append(
                    f"human_reception_move_not_observation_owned:{nucleus_id}"
                )
        move_nuclei = tuple(
            nucleus_index[nucleus_id]
            for nucleus_id in (*move_target_ids, *move_support_ids)
            if nucleus_id in nucleus_index
        )
        expected_move_evidence = tuple(
            _ordered_span_ids(
                span_id
                for nucleus in move_nuclei
                for span_id in nucleus.source_span_ids
            )
        )
        move_evidence = tuple(move.source_evidence_span_ids)
        if not move_evidence:
            issues.append("human_reception_move_evidence_missing")
        if move_evidence != expected_move_evidence:
            issues.append("human_reception_move_evidence_mismatch")
        for span_id in move_evidence:
            if not _EVIDENCE_ID_RE.fullmatch(span_id):
                issues.append(f"human_reception_move_invalid_evidence:{span_id}")
        for span_id in resolver.unresolved_ids(move_evidence):
            issues.append(f"human_reception_move_unresolved_evidence:{span_id}")

        matching_opportunities = tuple(
            opportunity
            for opportunity in opportunities
            if (
                opportunity.reception_act == move.reception_act
                and opportunity.target_nucleus_ids == move_target_ids
                and opportunity.support_nucleus_ids == move_support_ids
                and opportunity.source_evidence_span_ids == move_evidence
            )
        )
        if not matching_opportunities:
            issues.append("human_reception_move_without_opportunity")
        else:
            opportunity = matching_opportunities[0]
            if opportunity.opportunity_id in selected_opportunity_ids:
                issues.append("human_reception_move_opportunity_duplicate")
            selected_opportunity_ids.add(opportunity.opportunity_id)
            expected_move_required = bool(
                opportunity.safety_required
                or opportunity.retention in {"required", "should"}
            )
            if move.required is not expected_move_required:
                issues.append("human_reception_move_required_mismatch")
            if move.surface_strategy != _surface_strategy_for_move(
                opportunity,
                move.move_role,
            ):
                issues.append("human_reception_move_surface_strategy_mismatch")
        if not 1 <= len(move.follow_elements) <= 3:
            issues.append("human_reception_move_follow_element_count_invalid")
        if len(move.follow_elements) != len(set(move.follow_elements)):
            issues.append("human_reception_move_follow_element_duplicate")
        if any(
            element not in allowed_follow_elements
            for element in move.follow_elements
        ):
            issues.append("human_reception_move_follow_element_invalid")
        if move.speaker_presence not in {"implicit_emlis", "explicit_emlis"}:
            issues.append("human_reception_move_speaker_presence_invalid")
        if move.reference_mode not in {
            "anaphoric_first",
            "short_anchor_if_ambiguous",
            "explicit_emlis_counterposition",
        }:
            issues.append("human_reception_move_reference_mode_invalid")
        if move.surface_strategy not in allowed_surface_strategies:
            issues.append("human_reception_move_surface_strategy_invalid")
        if not isinstance(move.required, bool):
            issues.append("human_reception_move_required_invalid")
        expected_distinct_ids = tuple(f"rm{item}" for item in range(1, index))
        if tuple(move.distinct_from_move_ids) != expected_distinct_ids:
            issues.append("human_reception_move_distinct_reference_invalid")
        move_signature = (
            move.reception_act,
            move_target_ids,
            move.move_role,
        )
        if move_signature in move_signatures:
            issues.append("human_reception_move_duplicate")
        move_signatures.add(move_signature)
        if move.move_role == "bounded_counterposition":
            if move.reception_act != "bounded_counter_self_denial":
                issues.append("human_reception_counterposition_move_act_invalid")
            if move.speaker_presence != "explicit_emlis":
                issues.append("human_reception_counterposition_move_speaker_invalid")
            if move.reference_mode != "explicit_emlis_counterposition":
                issues.append("human_reception_counterposition_move_reference_invalid")
            if move.surface_strategy != "explicit_emlis_counterposition":
                issues.append("human_reception_counterposition_move_strategy_invalid")
            if not any(
                _is_reception_grounded_counterposition_nucleus(nucleus)
                for nucleus in move_nuclei
            ):
                issues.append("human_reception_move_ungrounded_counterposition")

    if moves and reception_plan.primary_reception_act != moves[0].reception_act:
        issues.append("human_reception_primary_act_move_mismatch")
    # RR4 still owns the compatibility-field cutover.  Until then an internal
    # caller may set the legacy secondary act for the existing renderer; new
    # production plans keep standard-mode secondary acts empty.
    for opportunity in opportunities:
        if (
            opportunity.safety_required
            and opportunity.opportunity_id not in selected_opportunity_ids
        ):
            issues.append("human_reception_required_safety_opportunity_unselected")

    counter_moves = tuple(
        move for move in moves if move.move_role == "bounded_counterposition"
    )
    help_moves = tuple(
        move for move in moves if move.reception_act == "hold_help_seeking"
    )
    if safety_kind == TRIAGE_SELF_DENIAL_SAFE_STATE_ANSWER:
        expected_safety_mode = (
            "help_seeking_bounded" if help_moves else "self_denial_bounded"
        )
        if depth_policy.safety_mode != expected_safety_mode:
            issues.append("human_reception_depth_safety_mode_mismatch")
        grounded_counter_opportunity = any(
            opportunity.family == "counterdirection"
            for opportunity in opportunities
        )
        if grounded_counter_opportunity and not counter_moves:
            issues.append("human_reception_required_counterposition_move_missing")
    elif depth_policy.safety_mode != "standard":
        issues.append("human_reception_depth_standard_safety_mode_required")

    if reception_plan.primary_reception_act not in allowed_acts:
        issues.append("human_reception_primary_act_missing_or_invalid")
    if (
        reception_plan.secondary_reception_act is not None
        and reception_plan.secondary_reception_act not in allowed_acts
    ):
        issues.append("human_reception_secondary_act_invalid")
    if reception_plan.secondary_reception_act == reception_plan.primary_reception_act:
        issues.append("human_reception_secondary_act_not_distinct")
    if reception_plan.primary_follow_element not in allowed_follow_elements:
        issues.append("human_reception_primary_follow_element_missing_or_invalid")
    if len(reception_plan.secondary_follow_elements) > 2:
        issues.append("human_reception_secondary_follow_element_limit_exceeded")
    if len(set(reception_plan.secondary_follow_elements)) != len(
        reception_plan.secondary_follow_elements
    ):
        issues.append("human_reception_secondary_follow_element_duplicate")
    if any(
        element not in allowed_follow_elements
        for element in reception_plan.secondary_follow_elements
    ):
        issues.append("human_reception_secondary_follow_element_invalid")
    if reception_plan.primary_follow_element in reception_plan.secondary_follow_elements:
        issues.append("human_reception_primary_follow_element_repeated")
    if (
        reception_plan.afterglow_follow_element is not None
        and reception_plan.afterglow_follow_element not in allowed_follow_elements
    ):
        issues.append("human_reception_afterglow_follow_element_invalid")
    if reception_plan.afterglow_follow_element in {
        reception_plan.primary_follow_element,
        *reception_plan.secondary_follow_elements,
    }:
        issues.append("human_reception_afterglow_follow_element_repeated")
    if reception_plan.primary_reception_act in allowed_acts:
        expected_follow_profile = _FOLLOW_PROFILE_BY_RECEPTION_ACT[
            reception_plan.primary_reception_act
        ]
        if (
            reception_plan.primary_follow_element,
            reception_plan.secondary_follow_elements,
            reception_plan.afterglow_follow_element,
        ) != expected_follow_profile:
            issues.append("human_reception_follow_profile_act_mismatch")

    target_ids = tuple(reception_plan.target_nucleus_ids)
    support_ids = tuple(reception_plan.support_nucleus_ids)
    observation_owned_ids = tuple(reception_plan.observation_owned_nucleus_ids)
    if target_ids != tuple(expected_target_ids):
        issues.append("human_reception_target_mismatch")
    if not target_ids:
        issues.append("human_reception_target_missing")
    for label, ids in (
        ("target", target_ids),
        ("support", support_ids),
        ("observation_owned", observation_owned_ids),
    ):
        if len(ids) != len(set(ids)):
            issues.append(f"human_reception_{label}_duplicate")
        for nucleus_id in ids:
            if nucleus_id not in nucleus_index:
                issues.append(f"human_reception_{label}_unknown_nucleus:{nucleus_id}")
    if set(target_ids) & set(support_ids):
        issues.append("human_reception_target_support_overlap")
    if not observation_owned_ids:
        issues.append("human_reception_observation_owned_missing")
    if not set(target_ids).issubset(observation_owned_ids):
        issues.append("human_reception_target_not_observation_owned")

    selected_nuclei = tuple(
        nucleus_index[nucleus_id]
        for nucleus_id in (*target_ids, *support_ids)
        if nucleus_id in nucleus_index
    )
    expected_evidence_ids = tuple(
        _ordered_span_ids(
            span_id
            for nucleus in selected_nuclei
            for span_id in nucleus.source_span_ids
        )
    )
    if tuple(reception_plan.source_evidence_span_ids) != expected_evidence_ids:
        issues.append("human_reception_source_evidence_mismatch")
    if not reception_plan.source_evidence_span_ids:
        issues.append("human_reception_source_evidence_missing")
    for span_id in reception_plan.source_evidence_span_ids:
        if not _EVIDENCE_ID_RE.fullmatch(span_id):
            issues.append(f"human_reception_invalid_evidence_id:{span_id}")
    for span_id in resolver.unresolved_ids(reception_plan.source_evidence_span_ids):
        issues.append(f"human_reception_unresolved_evidence:{span_id}")

    if reception_plan.stance not in set(_STANCE_BY_RECEPTION_ACT.values()):
        issues.append("human_reception_stance_missing_or_invalid")
    elif (
        reception_plan.primary_reception_act in allowed_acts
        and reception_plan.stance
        != _STANCE_BY_RECEPTION_ACT[reception_plan.primary_reception_act]
    ):
        issues.append("human_reception_stance_act_mismatch")
    if reception_plan.speaker_presence not in {"implicit_emlis", "explicit_emlis"}:
        issues.append("human_reception_speaker_presence_missing_or_invalid")
    if reception_plan.reference_mode not in {
        "anaphoric_first",
        "short_anchor_if_ambiguous",
        "explicit_emlis_counterposition",
    }:
        issues.append("human_reception_reference_mode_missing_or_invalid")

    quote_policy = reception_plan.quote_policy
    if quote_policy.mode != "no_full_quote_replay":
        issues.append("human_reception_quote_policy_mode_invalid")
    if not 0 <= quote_policy.max_anchor_count <= 1:
        issues.append("human_reception_quote_anchor_count_invalid")
    if not 0 <= quote_policy.max_anchor_visible_chars <= 20:
        issues.append("human_reception_quote_anchor_length_invalid")
    sentence_policy = reception_plan.sentence_policy
    if sentence_policy.min_sentences != 1:
        issues.append("human_reception_sentence_min_invalid")
    if not 1 <= sentence_policy.max_sentences <= 2:
        issues.append("human_reception_sentence_max_invalid")
    if sentence_policy.min_sentences > sentence_policy.max_sentences:
        issues.append("human_reception_sentence_budget_invalid")

    distinctness = reception_plan.distinctness_policy
    if any(
        (
            distinctness.observation_summary_repetition_allowed,
            distinctness.relation_reexplanation_allowed,
            distinctness.all_input_enumeration_allowed,
            distinctness.policy_explanation_allowed,
            distinctness.new_cause_allowed,
            distinctness.new_identity_claim_allowed,
            distinctness.advice_allowed,
            distinctness.question_allowed,
        )
    ):
        issues.append("human_reception_distinctness_policy_relaxed")

    for prefix, codes in (
        ("safety_modifier", reception_plan.safety_modifier_codes),
        ("forbidden_surface", reception_plan.forbidden_surface_codes),
    ):
        if len(codes) != len(set(codes)):
            issues.append(f"human_reception_{prefix}_duplicate")
        for code in codes:
            if not _is_body_free_code(code):
                issues.append(f"human_reception_{prefix}_non_body_free_code")
    if not set(_RECEPTION_FORBIDDEN_SURFACE_CODES).issubset(
        reception_plan.forbidden_surface_codes
    ):
        issues.append("human_reception_forbidden_surface_contract_missing")

    bounded_counterposition = (
        reception_plan.primary_reception_act == "bounded_counter_self_denial"
        or reception_plan.secondary_reception_act == "bounded_counter_self_denial"
    )
    if safety_kind == TRIAGE_SELF_DENIAL_SAFE_STATE_ANSWER:
        if not {
            "felt_state_is_real",
            "identity_claim_is_not_accepted",
        }.issubset(reception_plan.safety_modifier_codes):
            issues.append("human_reception_self_denial_safety_modifier_missing")
    if bounded_counterposition:
        if reception_plan.speaker_presence != "explicit_emlis":
            issues.append("human_reception_self_denial_explicit_stance_missing")
        if reception_plan.reference_mode != "explicit_emlis_counterposition":
            issues.append("human_reception_counterposition_reference_invalid")
        if "counterposition_requires_input_evidence" not in reception_plan.safety_modifier_codes:
            issues.append("human_reception_counterposition_evidence_policy_missing")
        if not any(
            _is_reception_grounded_counterposition_nucleus(item)
            for item in selected_nuclei
        ):
            issues.append("human_reception_ungrounded_self_denial_counterposition")
    if (
        material_quality == "short_state_sufficient"
        and safety_kind != TRIAGE_SELF_DENIAL_SAFE_STATE_ANSWER
    ):
        if reception_plan.primary_reception_act != "stay_with_current_burden":
            issues.append("human_reception_short_state_act_invalid")
        if reception_plan.sentence_policy.max_sentences != 1:
            issues.append("human_reception_short_state_sentence_budget_invalid")
        if reception_plan.distinctness_policy.policy_explanation_allowed:
            issues.append("human_reception_short_state_policy_explanation_allowed")
    return tuple(_dedupe(issues))


def validate_grounded_observation_plan(
    plan: GroundedObservationPlan,
    resolver: EvidenceSpanResolver,
) -> tuple[str, ...]:
    """Validate references and Safety/Surface perimeter without rendering text."""

    issues: list[str] = []
    if plan.schema_version != GROUND_OBSERVATION_PLAN_SCHEMA_VERSION:
        issues.append("plan_schema_version_mismatch")
    if plan.adapter_version != GROUND_OBSERVATION_PLAN_ADAPTER_VERSION:
        issues.append("plan_adapter_version_mismatch")
    if plan.generation_path != GROUND_OBSERVATION_PLAN_GENERATION_PATH:
        issues.append("plan_generation_path_mismatch")

    def append_code_issues(prefix: str, values: Sequence[Any]) -> None:
        for value in values or ():
            cleaned = _clean(value)
            if not cleaned or not _is_body_free_code(cleaned):
                issues.append(f"{prefix}_non_body_free_code")

    def append_evidence_issues(prefix: str, span_ids: Sequence[str]) -> tuple[str, ...]:
        requested = tuple(_dedupe(span_ids))
        for span_id in requested:
            if not _EVIDENCE_ID_RE.fullmatch(span_id):
                issues.append(f"{prefix}_invalid_evidence_id:{span_id}")
        unresolved = resolver.unresolved_ids(requested)
        for span_id in unresolved:
            issues.append(f"{prefix}_unresolved_evidence:{span_id}")
        return unresolved

    nucleus_index: dict[str, GroundedSemanticNucleus] = {}
    for item in plan.nuclei:
        if not item.nucleus_id:
            issues.append("nucleus_without_id")
            continue
        if item.nucleus_id in nucleus_index:
            issues.append(f"duplicate_nucleus_id:{item.nucleus_id}")
        nucleus_index[item.nucleus_id] = item
        append_code_issues(
            f"nucleus:{item.nucleus_id}",
            (
                item.nucleus_id,
                *item.surface_anchor_ids,
                *item.semantic_frame.target_anchor_ids,
                *item.semantic_frame.attribute_codes,
                *item.forbidden_inference_codes,
                *item.source_claim_ids,
                *item.source_meaning_block_keys,
            ),
        )
        if not item.source_span_ids:
            issues.append(f"nucleus_without_evidence:{item.nucleus_id}")
        unresolved = append_evidence_issues(f"nucleus:{item.nucleus_id}", item.source_span_ids)
        if not unresolved and tuple(item.source_fields) != resolver.source_fields_for(item.source_span_ids):
            issues.append(f"nucleus_source_field_mismatch:{item.nucleus_id}")

    relation_index: dict[str, GroundedSemanticRelation] = {}
    for item in plan.relations:
        if not item.relation_id:
            issues.append("relation_without_id")
            continue
        if item.relation_id in relation_index:
            issues.append(f"duplicate_relation_id:{item.relation_id}")
        relation_index[item.relation_id] = item
        append_code_issues(
            f"relation:{item.relation_id}",
            (
                item.relation_id,
                item.type,
                item.from_nucleus_id,
                item.to_nucleus_id,
                *item.source_relation_ids,
                *item.source_meaning_arc_keys,
            ),
        )
        if item.type not in _ALLOWED_RELATION_KINDS:
            issues.append(f"unsupported_relation_type:{item.relation_id}:{item.type}")
        if item.from_nucleus_id not in nucleus_index:
            issues.append(f"relation_unknown_from_nucleus:{item.relation_id}:{item.from_nucleus_id}")
        if item.to_nucleus_id not in nucleus_index:
            issues.append(f"relation_unknown_to_nucleus:{item.relation_id}:{item.to_nucleus_id}")
        if item.from_nucleus_id == item.to_nucleus_id:
            issues.append(f"relation_self_loop:{item.relation_id}")
        if not item.source_span_ids:
            issues.append(f"relation_without_evidence:{item.relation_id}")
        append_evidence_issues(f"relation:{item.relation_id}", item.source_span_ids)

    for item in plan.unknown_boundaries:
        append_code_issues(
            f"unknown_boundary:{item.unknown_id}",
            (item.unknown_id, item.dimension, *item.affected_nucleus_ids),
        )
        for nucleus_id in item.affected_nucleus_ids:
            if nucleus_id not in nucleus_index:
                issues.append(f"unknown_boundary_unknown_nucleus:{item.unknown_id}:{nucleus_id}")
        append_evidence_issues(f"unknown_boundary:{item.unknown_id}", item.evidence_span_ids)

    for nucleus_id in (
        *plan.response_plan.primary_nucleus_ids,
        *plan.response_plan.supporting_nucleus_ids,
        *plan.response_plan.fact_boundary_nucleus_ids,
        *plan.response_plan.human_follow_target_ids,
        *plan.response_plan.required_nucleus_ids,
        *plan.response_plan.optional_nucleus_ids,
        *plan.coverage_requirements.required_nucleus_ids,
    ):
        if nucleus_id not in nucleus_index:
            issues.append(f"response_or_coverage_unknown_nucleus:{nucleus_id}")
    for relation_id in (*plan.response_plan.relation_ids, *plan.coverage_requirements.required_relation_ids):
        if relation_id not in relation_index:
            issues.append(f"response_or_coverage_unknown_relation:{relation_id}")

    reception_plan = plan.response_plan.human_reception_plan
    if plan.coverage_requirements.human_follow_required:
        if reception_plan is None:
            issues.append("human_reception_plan_missing")
        else:
            issues.extend(
                validate_grounded_human_reception_plan(
                    reception_plan,
                    expected_target_ids=plan.response_plan.human_follow_target_ids,
                    nucleus_index=nucleus_index,
                    resolver=resolver,
                    safety_kind=plan.safety_policy.safety_kind,
                    material_quality=plan.input_profile.material_quality,
                )
            )
    elif reception_plan is not None:
        issues.append("human_reception_plan_forbidden_when_not_required")

    append_code_issues("source_contract", plan.source_contracts)
    append_code_issues("safety_boundary", plan.safety_policy.required_boundary_codes)
    if plan.response_plan.question_policy.allowed:
        issues.append("p7_question_policy_must_be_false")
    if plan.surface_policy.completed_semantic_template_allowed:
        issues.append("completed_semantic_template_must_be_false")
    if plan.surface_policy.example_cue_route_allowed:
        issues.append("example_cue_route_must_be_false")
    if plan.surface_policy.synthetic_evidence_id_allowed:
        issues.append("synthetic_evidence_id_must_be_false")
    if plan.input_profile.text_presence == "text_present" and not plan.response_plan.required_nucleus_ids:
        issues.append("text_present_without_required_nucleus")

    safety_kind = plan.safety_policy.safety_kind
    separate_expected = safety_kind in {TRIAGE_SAFETY_SUPPORT_REQUIRED, TRIAGE_SAFETY_BLOCKED_EMERGENCY}
    if separate_expected:
        if plan.response_plan.surface_shape != "separate_safety_surface":
            issues.append("separate_safety_surface_shape_missing")
        if plan.surface_policy.content_source != "separate_safety_owner":
            issues.append("separate_safety_owner_not_preserved")
        if plan.surface_policy.generic_observation_surface_allowed:
            issues.append("generic_surface_allowed_for_separate_safety")
        if plan.safety_policy.grounded_plan_overlay_allowed:
            issues.append("grounded_overlay_allowed_for_separate_safety")
    else:
        if plan.surface_policy.content_source != "grounded_plan_only":
            issues.append("grounded_content_source_missing")
        if plan.input_profile.material_quality == "empty":
            if plan.response_plan.surface_shape != "plain":
                issues.append("empty_input_surface_shape_must_be_plain")
        else:
            # Public Emlis observations always use the same two labelled
            # sections.  Input length controls the number of paragraphs inside
            # a section; it cannot switch the public body back to a plain or
            # observation-only surface.
            if plan.response_plan.surface_shape != "two_stage":
                issues.append("mandatory_two_stage_surface_shape_missing")
            if not plan.coverage_requirements.human_follow_required:
                issues.append("mandatory_two_stage_human_follow_requirement_missing")
            if not plan.response_plan.human_follow_target_ids:
                issues.append("mandatory_two_stage_human_follow_target_missing")
    if safety_kind == TRIAGE_SELF_DENIAL_SAFE_STATE_ANSWER:
        if not plan.safety_policy.identity_claim_must_not_be_accepted_as_fact:
            issues.append("self_denial_identity_fact_boundary_missing")
        if not plan.coverage_requirements.fact_boundary_required:
            issues.append("self_denial_fact_boundary_requirement_missing")
    if safety_kind == TRIAGE_SAFETY_BLOCKED_EMERGENCY and not plan.safety_policy.emergency_path_must_not_be_overridden:
        issues.append("emergency_override_protection_missing")

    expected_response_kind = {
        "short_state_sufficient": "short_state_observation",
        "limited_grounding": "limited_grounding_observation",
        "labels_only_limited": "labels_only_limited_observation",
        "empty": "unavailable",
    }.get(plan.input_profile.material_quality)
    if (
        expected_response_kind
        and safety_kind == TRIAGE_SAFE_OBSERVATION
        and plan.response_plan.response_kind != expected_response_kind
    ):
        issues.append("material_quality_response_kind_mismatch")
    if plan.input_profile.material_quality == "short_state_sufficient" and plan.response_plan.question_policy.allowed:
        issues.append("short_state_question_escape_forbidden")
    if safety_kind == TRIAGE_SELF_DENIAL_SAFE_STATE_ANSWER:
        if not plan.response_plan.fact_boundary_nucleus_ids:
            issues.append("self_denial_fact_boundary_target_missing")
        if not plan.response_plan.human_follow_target_ids:
            issues.append("self_denial_human_follow_target_missing")
        opposition_required = (
            "input_grounded_continuation_refusal"
            in plan.safety_policy.required_boundary_codes
        )
        if opposition_required and not any(
            item.type == "continuation_or_refusal"
            and item.relation_id in plan.coverage_requirements.required_relation_ids
            for item in plan.relations
        ):
            issues.append("self_denial_limited_opposition_relation_missing")

    computed_references = _all_plan_evidence_ids(plan.nuclei, plan.relations, plan.unknown_boundaries)
    if tuple(plan.referenced_evidence_span_ids) != computed_references:
        issues.append("referenced_evidence_span_ids_mismatch")
    append_evidence_issues("plan", plan.referenced_evidence_span_ids)
    if not plan.evidence_ledger_validation.valid:
        issues.extend(
            f"evidence_ledger_contract:{code}"
            for code in plan.evidence_ledger_validation.issue_codes
        )
    return tuple(_dedupe(issues))


def build_grounded_observation_plan(
    current_input: Mapping[str, Any] | None,
    *,
    evidence_spans: Sequence[EvidenceSpan] | None = None,
    reports: Sequence[PerspectiveReport] | None = None,
    board: PerspectiveBoard | None = None,
    graph: ObservationGraph | None = None,
    meaning_blocks: Sequence[InputMeaningBlock] | None = None,
    coverage_plan: MeaningCoveragePlan | None = None,
    whole_input_meaning_arc: WholeInputMeaningArc | None = None,
    retention_plan: MajorMeaningRetentionPlan | None = None,
    safety_decision: EmlisSafetyTriageDecision | None = None,
) -> GroundedObservationPlan:
    """Build the canonical plan used by the public grounded reply path."""

    normalized = normalize_emlis_current_input(current_input or {})
    span_list = tuple(evidence_spans if evidence_spans is not None else build_evidence_ledger(normalized))
    ledger_validation = validate_evidence_ledger(span_list, current_input=normalized)
    try:
        resolver = build_evidence_span_resolver(span_list, current_input=normalized)
    except EvidenceLedgerResolutionError as exc:
        raise GroundedObservationPlanError(str(exc)) from exc

    report_list = tuple(reports if reports is not None else run_perspective_observers(span_list))
    perspective_board = board or build_perspective_board(evidence_spans=span_list, reports=report_list)
    observation_graph = graph or integrate_perspective_board(board=perspective_board)

    structural_artifacts = _build_meaning_artifacts(normalized, span_list)
    if any(value is not None for value in (meaning_blocks, coverage_plan, whole_input_meaning_arc, retention_plan)):
        blocks = tuple(meaning_blocks) if meaning_blocks is not None else structural_artifacts.meaning_blocks
        block_keys = [_clean(getattr(block, "block_key", "")) for block in blocks]
        coverage = coverage_plan or MeaningCoveragePlan(
            input_level="long" if len(blocks) >= 6 else "short" if len(blocks) <= 2 else "medium",
            clear_long_input=len(blocks) >= 6,
            meaning_block_count=len(blocks),
            required_roles=_dedupe(getattr(block, "role", "") for block in blocks),
            selected_block_keys=block_keys,
            min_blocks_to_cover=len(blocks),
            max_blocks_to_cover=len(blocks),
            coverage_ratio_target=1.0 if blocks else 0.0,
            reason="explicit_upstream_meaning_blocks_adapted_without_role_reclassification",
        )
        arc = whole_input_meaning_arc or WholeInputMeaningArc(
            arc_key="whole_input:provided_source_order",
            title="provided_source_order_arc",
            summary="",
            ordered_block_keys=block_keys,
            clarity=0.8 if blocks else 0.0,
            evidence=[],
        )
        retention = retention_plan or MajorMeaningRetentionPlan(
            clear_long_input=bool(getattr(coverage, "clear_long_input", False)),
            total_block_count=len(blocks),
            must_keep_block_keys=block_keys,
            should_keep_block_keys=[],
            optional_block_keys=[],
            forbidden_overcompression_targets=block_keys,
            min_must_keep_coverage_ratio=1.0 if blocks else 0.0,
            reason="provided_meaning_blocks_are_source_contract",
        )
        meaning_artifacts = _MeaningArtifacts(blocks, coverage, arc, retention)
    else:
        meaning_artifacts = structural_artifacts

    base_triage = safety_decision or build_emlis_safety_triage_decision(
        current_input=normalized,
        graph=observation_graph,
        evidence_spans=span_list,
    )
    triage = _canonicalize_safety_decision(
        base_triage,
        span_list,
        authoritative_self_denial=safety_decision is not None,
    )
    nuclei = _build_nuclei(
        spans=span_list,
        board=perspective_board,
        meaning_artifacts=meaning_artifacts,
        safety_decision=triage,
    )
    relations = _build_relations(
        spans=span_list,
        board=perspective_board,
        nuclei=nuclei,
        meaning_artifacts=meaning_artifacts,
    )
    unknowns = _build_unknown_boundaries(board=perspective_board, graph=observation_graph, nuclei=nuclei)
    presence = _text_presence(span_list)
    material_quality = _material_quality(
        text_presence=presence,
        safety_kind=triage.safety_triage_kind,
        spans=span_list,
        nuclei=nuclei,
    )
    nuclei = _apply_short_state_lexical_policy(
        nuclei,
        span_list,
        material_quality=material_quality,
        relations=relations,
    )
    complexity = _semantic_complexity(nuclei=nuclei, relations=relations, meaning_artifacts=meaning_artifacts)
    response_plan, coverage_requirements, surface_policy, safety_policy = _build_response_and_policies(
        nuclei=nuclei,
        relations=relations,
        safety_decision=triage,
        complexity=complexity,
        material_quality=material_quality,
    )
    referenced_ids = _all_plan_evidence_ids(nuclei, relations, unknowns)
    plan = GroundedObservationPlan(
        schema_version=GROUND_OBSERVATION_PLAN_SCHEMA_VERSION,
        adapter_version=GROUND_OBSERVATION_PLAN_ADAPTER_VERSION,
        generation_path=GROUND_OBSERVATION_PLAN_GENERATION_PATH,
        input_profile=GroundedInputProfile(
            text_presence=presence,
            material_quality=material_quality,
            semantic_complexity=complexity,
            nucleus_count=len(nuclei),
            relation_count=len(relations),
            safety_kind=triage.safety_triage_kind,
        ),
        nuclei=nuclei,
        relations=relations,
        unknown_boundaries=unknowns,
        response_plan=response_plan,
        coverage_requirements=coverage_requirements,
        surface_policy=surface_policy,
        safety_policy=safety_policy,
        evidence_ledger_validation=ledger_validation,
        referenced_evidence_span_ids=referenced_ids,
        source_contracts=(
            "EmlisCurrentInputBundle",
            "EvidenceSpan:sN",
            "PerspectiveReport",
            "PerspectiveBoard",
            "ObservationGraph",
            "InputMeaningBlock",
            "MeaningCoveragePlan",
            "WholeInputMeaningArc",
            "MajorMeaningRetentionPlan",
            "EmlisSafetyTriageDecision",
        ),
    )
    issues = validate_grounded_observation_plan(plan, resolver)
    if issues:
        raise GroundedObservationPlanError("invalid_grounded_observation_plan:" + ",".join(issues))
    return plan


# Transitional import compatibility for I1-I4 structural tests and internal
# callers.  Both names resolve to the same canonical builder; there is no
# second generation path or shadow implementation after I5.
build_grounded_observation_plan_shadow = build_grounded_observation_plan


__all__ = [
    "GROUND_OBSERVATION_PLAN_SCHEMA_VERSION",
    "GROUND_OBSERVATION_PLAN_ADAPTER_VERSION",
    "GROUND_OBSERVATION_PLAN_GENERATION_PATH",
    "GROUND_OBSERVATION_PLAN_SEMANTIC_VERSION",
    "GROUND_HUMAN_RECEPTION_PLAN_SCHEMA_VERSION",
    "GroundedReceptionAct",
    "GroundedFollowElement",
    "GroundedReceptionStance",
    "GroundedSpeakerPresence",
    "GroundedReferenceMode",
    "GroundedReceptionOpportunityFamily",
    "GroundedReceptionDepthLevel",
    "GroundedReceptionSafetyMode",
    "GroundedReceptionMoveRole",
    "GroundedReceptionSurfaceStrategy",
    "GroundedObservationPlanError",
    "GroundedSemanticFrame",
    "GroundedSemanticNucleus",
    "GroundedSemanticRelation",
    "GroundedUnknownBoundary",
    "GroundedInputProfile",
    "GroundedQuestionPolicy",
    "GroundedReceptionQuotePolicy",
    "GroundedReceptionSentencePolicy",
    "GroundedReceptionDistinctnessPolicy",
    "GroundedReceptionOpportunity",
    "GroundedReceptionDepthPolicy",
    "GroundedReceptionMovePlan",
    "GroundedHumanReceptionPlan",
    "GroundedResponsePlan",
    "GroundedCoverageRequirements",
    "GroundedSurfacePolicy",
    "GroundedSafetyPolicy",
    "GroundedObservationPlan",
    "classify_grounded_human_follow_role",
    "map_grounded_human_follow_role_to_reception_act",
    "select_grounded_reception_act",
    "classify_grounded_human_follow_delivery",
    "build_grounded_reception_opportunities",
    "build_grounded_human_reception_plan",
    "build_grounded_observation_plan",
    "build_grounded_observation_plan_shadow",
    "validate_grounded_human_reception_plan",
    "validate_grounded_observation_plan",
]
